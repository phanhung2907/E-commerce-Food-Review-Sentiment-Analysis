import argparse
import csv
import json
import random
import sys
import threading
import time

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter


# Cho phép ingestion import các module dùng chung trong src/
SRC_ROOT = Path(__file__).resolve().parents[2]

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_ROOT),
    )

from storage.minio_client import (  # noqa: E402
    object_exists,
    read_json_object,
)
from storage.postgres_client import (  # noqa: E402
    get_thread_postgres_connection,
)


# =========================================================
# CẤU HÌNH
# =========================================================

PLATFORM_NAME = "foody_shoppefood"
SOURCE_CODE = "foody"

DATA_ROOT = (
    Path("code/hung/data")
    / PLATFORM_NAME
    / "raw"
)

FOODY_REVIEW_API = (
    "https://www.foody.vn/"
    "__get/Review/ResLoadMore"
)

REVIEWS_PER_REQUEST = 10

DEFAULT_WORKERS = 50
DEFAULT_PAGE_DELAY = 0.15

REQUEST_TIMEOUT = 20
MAX_RETRIES = 5


# =========================================================
# HTTP / THREAD
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept":
        "application/json, text/plain, */*",
    "Accept-Language":
        "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With":
        "XMLHttpRequest",
    "Referer":
        "https://www.foody.vn/",
}

_thread_local = threading.local()
_print_lock = threading.Lock()


def log(*args):
    with _print_lock:
        print(
            *args,
            flush=True,
        )


def get_session():
    """
    Mỗi worker dùng một requests.Session riêng
    để tái sử dụng TCP connection.
    """
    session = getattr(
        _thread_local,
        "session",
        None,
    )

    if session is None:
        session = requests.Session()
        session.headers.update(
            HEADERS
        )

        adapter = HTTPAdapter(
            pool_connections=4,
            pool_maxsize=4,
            max_retries=0,
        )

        session.mount(
            "https://",
            adapter,
        )
        session.mount(
            "http://",
            adapter,
        )

        _thread_local.session = session

    return session


# =========================================================
# ĐỌC DANH SÁCH NHÀ HÀNG
# =========================================================

def find_restaurant_files():
    if not DATA_ROOT.exists():
        raise FileNotFoundError(
            f"Không tồn tại: {DATA_ROOT}"
        )

    return sorted(
        DATA_ROOT.glob(
            "*/restaurants.csv"
        )
    )


def get_city_from_path(
    csv_path,
):
    return csv_path.parent.name


def read_restaurants(
    csv_path,
):
    city = get_city_from_path(
        csv_path
    )

    restaurants = []

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            raw_id = (
                row
                .get(
                    "restaurant_id",
                    "",
                )
                .strip()
            )

            if not raw_id:
                continue

            try:
                restaurant_id = int(
                    raw_id
                )
            except ValueError:
                log(
                    "ID nhà hàng không hợp lệ:",
                    raw_id,
                )
                continue

            restaurants.append({
                "restaurant_id":
                    restaurant_id,
                "name":
                    row.get(
                        "name",
                        "",
                    ),
                "address":
                    row.get(
                        "address",
                        "",
                    ),
                "url":
                    row.get(
                        "url",
                        "",
                    ),
                "city":
                    row.get(
                        "city",
                        "",
                    ) or city,
            })

    return restaurants


def load_all_restaurants(
    city=None,
    max_restaurants_per_city=None,
):
    tasks = []
    seen = set()

    for csv_path in (
        find_restaurant_files()
    ):
        csv_city = (
            get_city_from_path(
                csv_path
            )
        )

        if (
            city is not None
            and csv_city != city
        ):
            continue

        city_count = 0

        for restaurant in (
            read_restaurants(
                csv_path
            )
        ):
            key = (
                restaurant["city"],
                restaurant[
                    "restaurant_id"
                ],
            )

            if key in seen:
                continue

            seen.add(key)
            tasks.append(
                restaurant
            )
            city_count += 1

            if (
                max_restaurants_per_city
                is not None
                and city_count
                >= max_restaurants_per_city
            ):
                break

    return tasks


# =========================================================
# ĐƯỜNG DẪN RAW
# =========================================================

def restaurant_output_path(
    restaurant,
):
    city = (
        restaurant["city"]
        or "unknown"
    )

    return (
        DATA_ROOT
        / city
        / str(
            restaurant[
                "restaurant_id"
            ]
        )
        / "restaurant.json"
    )


def restaurant_object_key(
    restaurant,
):
    city = (
        restaurant["city"]
        or "unknown"
    )

    return (
        f"{SOURCE_CODE}/raw/"
        f"{city}/"
        f"{restaurant['restaurant_id']}/"
        "restaurant.json"
    )


# =========================================================
# STATE: POSTGRESQL + RAW CŨ
# =========================================================

def get_existing_review_ids(
    restaurant_id,
):
    """
    PostgreSQL là checkpoint lâu dài.

    Trả về toàn bộ source_review_id đã có
    của nhà hàng trên source=foody.
    """
    conn = (
        get_thread_postgres_connection()
    )

    rows = conn.execute(
        """
        SELECT source_review_id
        FROM reviews
        WHERE source_code = %s
          AND source_restaurant_id = %s
        """,
        (
            SOURCE_CODE,
            str(restaurant_id),
        ),
    ).fetchall()

    return {
        str(row[0])
        for row in rows
    }


def load_json_file(
    path,
):
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(
                file
            )

        if isinstance(
            data,
            dict,
        ):
            return data

    except (
        OSError,
        json.JSONDecodeError,
    ):
        pass

    return None


def load_previous_raw(
    restaurant,
):
    """
    Ưu tiên local để nhanh.

    Nếu local bị xóa nhưng MinIO vẫn còn,
    lấy raw cũ từ MinIO để merge.

    Trả về:
        (raw_dict | None, nguồn)
    """
    local_path = (
        restaurant_output_path(
            restaurant
        )
    )

    if local_path.exists():
        raw = load_json_file(
            local_path
        )

        if raw is not None:
            return raw, "local"

    object_key = (
        restaurant_object_key(
            restaurant
        )
    )

    if object_exists(
        object_key
    ):
        try:
            raw = read_json_object(
                object_key
            )

            if isinstance(
                raw,
                dict,
            ):
                return raw, "minio"

        except Exception as exc:
            log(
                "[CẢNH BÁO] Không đọc được "
                f"raw cũ từ MinIO "
                f"{object_key}: {exc}"
            )

    return None, "none"


def previous_crawl_complete(
    previous_raw,
):
    """
    Chỉ cho phép incremental early-stop
    nếu raw trước đó xác nhận đã crawl vét cạn.

    Raw phiên bản cũ chưa có field crawl_complete
    sẽ được xem là chưa xác nhận -> crawl sâu lại
    một lần để thiết lập checkpoint an toàn.
    """
    if not previous_raw:
        return False

    summary = (
        previous_raw.get(
            "review_summary"
        )
        or {}
    )

    return (
        summary.get(
            "crawl_complete"
        )
        is True
    )


# =========================================================
# REQUEST REVIEW
# =========================================================

def request_review_page(
    session,
    restaurant_id,
    last_id="",
    exclude_ids="",
):
    params = {
        "ResId":
            str(
                restaurant_id
            ),
        "Count":
            str(
                REVIEWS_PER_REQUEST
            ),
        "Type":
            "1",
        "isLatest":
            "true",
        "ExcludeIds":
            str(
                exclude_ids
                or ""
            ),
        "LastId":
            str(
                last_id
                or ""
            ),
    }

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):
        try:
            response = session.get(
                FOODY_REVIEW_API,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if (
                response.status_code
                == 200
            ):
                return (
                    response.json()
                )

            if response.status_code in {
                403,
                429,
                500,
                502,
                503,
                504,
            }:
                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                if retry_after:
                    try:
                        wait = float(
                            retry_after
                        )
                    except ValueError:
                        wait = None
                else:
                    wait = None

                if wait is None:
                    wait = min(
                        30,
                        (
                            2
                            ** (
                                attempt
                                - 1
                            )
                        )
                        + random.uniform(
                            0.2,
                            1.0,
                        ),
                    )

                last_error = (
                    RuntimeError(
                        "HTTP "
                        f"{response.status_code}"
                    )
                )

                time.sleep(
                    wait
                )
                continue

            response.raise_for_status()

        except (
            requests.RequestException,
            ValueError,
        ) as exc:
            last_error = exc

            if (
                attempt
                >= MAX_RETRIES
            ):
                break

            wait = min(
                30,
                (
                    2
                    ** (
                        attempt
                        - 1
                    )
                )
                + random.uniform(
                    0.2,
                    1.0,
                ),
            )

            time.sleep(
                wait
            )

    if last_error:
        raise last_error

    raise RuntimeError(
        "Không lấy được review response."
    )


# =========================================================
# REVIEW HELPERS
# =========================================================

def review_id_of(
    review,
):
    if not isinstance(
        review,
        dict,
    ):
        return None

    value = review.get(
        "Id"
    )

    if value is None:
        value = review.get(
            "id"
        )

    if value is None:
        return None

    return str(
        value
    ).strip()


def decorate_review(
    item,
    restaurant,
):
    review = item.copy()

    review["source"] = (
        SOURCE_CODE
    )

    review[
        "restaurant_id_query"
    ] = restaurant[
        "restaurant_id"
    ]

    review[
        "restaurant_name"
    ] = restaurant[
        "name"
    ]

    review[
        "restaurant_city"
    ] = restaurant[
        "city"
    ]

    review[
        "crawl_timestamp"
    ] = (
        datetime.now()
        .isoformat(
            timespec="seconds"
        )
    )

    return review


def merge_reviews(
    fetched_reviews,
    previous_raw,
    full_refresh=False,
):
    """
    Review vừa fetch được đứng trước và thắng
    nếu trùng ID, giúp refresh metadata gần nhất.

    Incremental:
        fetched mới/recent + raw cũ.

    Full refresh:
        chỉ dùng dữ liệu vừa crawl từ web.
    """
    previous_reviews = []

    if (
        not full_refresh
        and previous_raw
    ):
        previous_reviews = (
            previous_raw.get(
                "reviews"
            )
            or []
        )

    merged = []
    seen = set()

    for review in [
        *fetched_reviews,
        *previous_reviews,
    ]:
        review_id = (
            review_id_of(
                review
            )
        )

        if not review_id:
            continue

        if review_id in seen:
            continue

        seen.add(
            review_id
        )
        merged.append(
            review
        )

    return merged


# =========================================================
# CRAWL INCREMENTAL
# =========================================================

def crawl_restaurant_reviews(
    restaurant,
    existing_review_ids,
    prior_complete,
    max_reviews=None,
    page_delay=DEFAULT_PAGE_DELAY,
    full_refresh=False,
):
    """
    Mặc định: incremental.

    Nếu raw trước đã crawl_complete=True:
    - request từ review mới nhất.
    - page nào không còn review mới so với PostgreSQL
      -> đã chạm vùng dữ liệu cũ -> dừng.

    Nếu chưa từng crawl vét cạn:
    - không dùng early-stop trên review cũ.
    - tiếp tục đến khi API hết dữ liệu.

    full_refresh=True:
    - bỏ checkpoint PostgreSQL.
    - vét lại toàn bộ dữ liệu.
    """
    session = get_session()

    restaurant_id = (
        restaurant[
            "restaurant_id"
        ]
    )

    checkpoint_ids = (
        set()
        if full_refresh
        else {
            str(value)
            for value
            in existing_review_ids
        }
    )

    can_incremental_stop = (
        not full_refresh
        and prior_complete
        and bool(
            checkpoint_ids
        )
    )

    fetched_reviews = []
    seen_this_run = set()

    last_id = ""
    exclude_ids = ""

    total_api = None
    page = 1
    pages_scanned = 0
    items_scanned = 0
    new_reviews_crawled = 0

    seen_cursor_states = set()

    crawl_complete = False
    stop_reason = None

    while True:
        data = request_review_page(
            session=session,
            restaurant_id=(
                restaurant_id
            ),
            last_id=last_id,
            exclude_ids=(
                exclude_ids
            ),
        )

        pages_scanned += 1

        if total_api is None:
            total_api = (
                data.get(
                    "Total"
                )
                or data.get(
                    "Summary",
                    {},
                ).get(
                    "Total"
                )
            )

        items = (
            data.get(
                "Items"
            )
            or []
        )

        if not items:
            crawl_complete = True
            stop_reason = (
                "api_het_review"
            )
            break

        page_new_count = 0
        hit_limit = False

        for item in items:
            review_id = (
                review_id_of(
                    item
                )
            )

            if not review_id:
                continue

            if (
                review_id
                in seen_this_run
            ):
                continue

            seen_this_run.add(
                review_id
            )

            fetched_reviews.append(
                decorate_review(
                    item,
                    restaurant,
                )
            )

            items_scanned += 1

            if (
                review_id
                not in checkpoint_ids
            ):
                page_new_count += 1
                new_reviews_crawled += 1

            if (
                max_reviews
                is not None
                and items_scanned
                >= max_reviews
            ):
                hit_limit = True
                break

        if hit_limit:
            crawl_complete = False
            stop_reason = (
                "dat_gioi_han_max_reviews"
            )
            break

        # Chỉ early-stop khi lần crawl trước đã được
        # xác nhận là vét cạn. Nhờ đó dữ liệu test/limit
        # không làm mất các review cũ chưa từng thu thập.
        if (
            can_incremental_stop
            and page_new_count == 0
        ):
            crawl_complete = True
            stop_reason = (
                "da_cham_vung_review_cu"
            )
            break

        new_last_id = (
            data.get(
                "LastId"
            )
        )

        if not new_last_id:
            new_last_id = (
                items[-1]
                .get(
                    "Id"
                )
            )

        if not new_last_id:
            crawl_complete = False
            stop_reason = (
                "khong_con_cursor"
            )
            break

        new_exclude_ids = (
            data.get(
                "ExcludeIds"
            )
        )

        if (
            new_exclude_ids
            is None
        ):
            new_exclude_ids = (
                exclude_ids
            )

        cursor_state = (
            str(
                new_last_id
            ),
            str(
                new_exclude_ids
                or ""
            ),
        )

        if (
            cursor_state
            in seen_cursor_states
        ):
            crawl_complete = False
            stop_reason = (
                "cursor_bi_lap"
            )
            break

        seen_cursor_states.add(
            cursor_state
        )

        last_id = (
            new_last_id
        )

        exclude_ids = (
            new_exclude_ids
            or ""
        )

        page += 1

        if page_delay > 0:
            time.sleep(
                page_delay
            )

    return {
        "total_reviews_api":
            total_api,
        "fetched_reviews":
            fetched_reviews,
        "new_reviews_crawled":
            new_reviews_crawled,
        "pages_scanned":
            pages_scanned,
        "items_scanned":
            items_scanned,
        "crawl_complete":
            crawl_complete,
        "stop_reason":
            stop_reason,
        "incremental_early_stop_enabled":
            can_incremental_stop,
    }


# =========================================================
# BUILD / SAVE RAW OBJECT
# =========================================================

def build_result(
    restaurant,
    crawl_result,
    merged_reviews,
    previous_raw_source,
    existing_review_count,
    full_refresh,
):
    return {
        "source":
            SOURCE_CODE,
        "platform":
            PLATFORM_NAME,
        "crawl_timestamp":
            datetime.now()
            .isoformat(
                timespec="seconds"
            ),
        "restaurant": {
            "restaurant_id":
                restaurant[
                    "restaurant_id"
                ],
            "name":
                restaurant[
                    "name"
                ],
            "address":
                restaurant[
                    "address"
                ],
            "url":
                restaurant[
                    "url"
                ],
            "city":
                restaurant[
                    "city"
                ],
        },
        "review_summary": {
            # Có thể bị Foody cap ở 100.
            "total_reviews_api":
                crawl_result[
                    "total_reviews_api"
                ],

            # Tổng review hiện có trong raw object sau merge.
            "total_reviews_crawled":
                len(
                    merged_reviews
                ),
            "total_reviews_in_object":
                len(
                    merged_reviews
                ),

            # Thống kê riêng cho lần chạy hiện tại.
            "new_reviews_crawled":
                crawl_result[
                    "new_reviews_crawled"
                ],
            "existing_review_ids_in_db":
                existing_review_count,
            "pages_scanned":
                crawl_result[
                    "pages_scanned"
                ],
            "items_scanned":
                crawl_result[
                    "items_scanned"
                ],

            # Chỉ True khi crawler biết chắc đã chạm hết
            # dữ liệu cũ hoặc API thực sự hết review.
            "crawl_complete":
                crawl_result[
                    "crawl_complete"
                ],
            "stop_reason":
                crawl_result[
                    "stop_reason"
                ],
            "incremental_early_stop_enabled":
                crawl_result[
                    "incremental_early_stop_enabled"
                ],
            "full_refresh":
                full_refresh,
            "previous_raw_source":
                previous_raw_source,
        },
        "reviews":
            merged_reviews,
    }


def save_restaurant_json(
    restaurant,
    result,
):
    output_path = (
        restaurant_output_path(
            restaurant
        )
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = (
        output_path
        .with_suffix(
            ".json.tmp"
        )
    )

    with open(
        temp_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temp_path.replace(
        output_path
    )

    return output_path


# =========================================================
# WORKER
# =========================================================

def crawl_and_save(
    restaurant,
    *,
    max_reviews,
    page_delay,
    resume,
    full_refresh,
):
    output_path = (
        restaurant_output_path(
            restaurant
        )
    )

    # Resume chỉ dành cho cùng một lần chạy bị gián đoạn.
    if (
        resume
        and output_path.exists()
    ):
        return {
            "status":
                "skipped_resume",
            "restaurant_id":
                restaurant[
                    "restaurant_id"
                ],
            "new_reviews":
                0,
            "total_reviews":
                None,
            "pages_scanned":
                0,
            "path":
                output_path,
        }

    existing_ids = (
        get_existing_review_ids(
            restaurant[
                "restaurant_id"
            ]
        )
    )

    previous_raw, previous_source = (
        load_previous_raw(
            restaurant
        )
    )

    prior_complete = (
        previous_crawl_complete(
            previous_raw
        )
    )

    crawl_result = (
        crawl_restaurant_reviews(
            restaurant=restaurant,
            existing_review_ids=(
                existing_ids
            ),
            prior_complete=(
                prior_complete
            ),
            max_reviews=(
                max_reviews
            ),
            page_delay=(
                page_delay
            ),
            full_refresh=(
                full_refresh
            ),
        )
    )

    merged_reviews = merge_reviews(
        fetched_reviews=(
            crawl_result[
                "fetched_reviews"
            ]
        ),
        previous_raw=(
            previous_raw
        ),
        full_refresh=(
            full_refresh
        ),
    )

    result = build_result(
        restaurant=restaurant,
        crawl_result=(
            crawl_result
        ),
        merged_reviews=(
            merged_reviews
        ),
        previous_raw_source=(
            previous_source
        ),
        existing_review_count=(
            len(existing_ids)
        ),
        full_refresh=(
            full_refresh
        ),
    )

    save_restaurant_json(
        restaurant,
        result,
    )

    return {
        "status":
            "done",
        "restaurant_id":
            restaurant[
                "restaurant_id"
            ],
        "new_reviews":
            crawl_result[
                "new_reviews_crawled"
            ],
        "total_reviews":
            len(
                merged_reviews
            ),
        "pages_scanned":
            crawl_result[
                "pages_scanned"
            ],
        "stop_reason":
            crawl_result[
                "stop_reason"
            ],
        "crawl_complete":
            crawl_result[
                "crawl_complete"
            ],
        "path":
            output_path,
    }


# =========================================================
# CLI
# =========================================================

def parse_args():
    parser = (
        argparse.ArgumentParser(
            description=(
                "Foody review crawler "
                "đa luồng + incremental crawl"
            )
        )
    )

    parser.add_argument(
        "--max-reviews",
        type=int,
        default=None,
        help=(
            "Giới hạn số review item đọc từ API "
            "mỗi nhà hàng trong lần chạy này. "
            "Bỏ trống = không giới hạn."
        ),
    )

    parser.add_argument(
        "--max-restaurants-per-city",
        type=int,
        default=None,
        help=(
            "Giới hạn số nhà hàng mỗi city. "
            "Bỏ trống = toàn bộ restaurants.csv."
        ),
    )

    parser.add_argument(
        "--city",
        default=None,
        help=(
            "Chỉ crawl một city slug, "
            "ví dụ dien-bien."
        ),
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            "Số nhà hàng crawl song song. "
            f"Mặc định={DEFAULT_WORKERS}."
        ),
    )

    parser.add_argument(
        "--page-delay",
        type=float,
        default=DEFAULT_PAGE_DELAY,
        help=(
            "Delay giữa các page của cùng "
            "nhà hàng. Mặc định=0.15 giây."
        ),
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Tiếp tục cùng một lần chạy bị gián đoạn: "
            "nếu restaurant.json local đã tồn tại thì skip."
        ),
    )

    parser.add_argument(
        "--full-refresh",
        "--overwrite",
        dest="full_refresh",
        action="store_true",
        help=(
            "Bỏ incremental checkpoint và vét lại "
            "toàn bộ review của mỗi nhà hàng. "
            "--overwrite được giữ làm alias tương thích."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if (
        args.max_reviews
        is not None
        and args.max_reviews <= 0
    ):
        raise ValueError(
            "--max-reviews phải > 0"
        )

    if (
        args.max_restaurants_per_city
        is not None
        and args.max_restaurants_per_city
        <= 0
    ):
        raise ValueError(
            "--max-restaurants-per-city phải > 0"
        )

    if args.workers < 1:
        raise ValueError(
            "--workers phải >= 1"
        )

    if args.page_delay < 0:
        raise ValueError(
            "--page-delay phải >= 0"
        )

    if (
        args.resume
        and args.full_refresh
    ):
        raise ValueError(
            "Không dùng --resume và "
            "--full-refresh cùng lúc."
        )

    restaurants = (
        load_all_restaurants(
            city=args.city,
            max_restaurants_per_city=(
                args.max_restaurants_per_city
            ),
        )
    )

    if not restaurants:
        print(
            "Không có nhà hàng để crawl."
        )
        return

    print(
        "\nFOODY REVIEW CRAWLER"
    )
    print(
        "Chế độ:",
        (
            "FULL REFRESH"
            if args.full_refresh
            else (
                "RESUME"
                if args.resume
                else "INCREMENTAL"
            )
        ),
    )
    print(
        "Nhà hàng:",
        len(restaurants),
    )
    print(
        "Workers:",
        args.workers,
    )
    print(
        "Page delay:",
        args.page_delay,
    )

    done = 0
    skipped = 0
    failed = 0

    total_new_reviews = 0
    total_reviews_in_raw = 0
    total_pages = 0

    with ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:
        futures = {
            executor.submit(
                crawl_and_save,
                restaurant,
                max_reviews=(
                    args.max_reviews
                ),
                page_delay=(
                    args.page_delay
                ),
                resume=(
                    args.resume
                ),
                full_refresh=(
                    args.full_refresh
                ),
            ): restaurant
            for restaurant
            in restaurants
        }

        for index, future in enumerate(
            as_completed(
                futures
            ),
            start=1,
        ):
            restaurant = (
                futures[
                    future
                ]
            )

            try:
                result = (
                    future.result()
                )

                if (
                    result["status"]
                    == "skipped_resume"
                ):
                    skipped += 1

                    log(
                        f"[{index}/"
                        f"{len(restaurants)}] "
                        "RESUME-SKIP "
                        f"{restaurant['restaurant_id']} "
                        f"| {restaurant['name']}"
                    )
                    continue

                done += 1

                total_new_reviews += (
                    result[
                        "new_reviews"
                    ]
                )

                total_reviews_in_raw += (
                    result[
                        "total_reviews"
                    ]
                    or 0
                )

                total_pages += (
                    result[
                        "pages_scanned"
                    ]
                )

                log(
                    f"[{index}/"
                    f"{len(restaurants)}] "
                    "XONG "
                    f"{restaurant['restaurant_id']} "
                    f"| mới="
                    f"{result['new_reviews']} "
                    f"| raw="
                    f"{result['total_reviews']} "
                    f"| pages="
                    f"{result['pages_scanned']} "
                    f"| stop="
                    f"{result['stop_reason']} "
                    f"| {restaurant['name']}"
                )

            except Exception as exc:
                failed += 1

                log(
                    f"[{index}/"
                    f"{len(restaurants)}] "
                    "LỖI "
                    f"{restaurant['restaurant_id']} "
                    f"| {restaurant['name']} "
                    f"| {exc}"
                )

    print(
        "\n=============================="
    )
    print(
        "HOÀN TẤT CRAWL REVIEW"
    )
    print(
        "Nhà hàng xử lý:",
        done,
    )
    print(
        "Nhà hàng resume-skip:",
        skipped,
    )
    print(
        "Nhà hàng lỗi:",
        failed,
    )
    print(
        "Review mới:",
        total_new_reviews,
    )
    print(
        "Tổng page đã request:",
        total_pages,
    )
    print(
        "Tổng review trong raw objects:",
        total_reviews_in_raw,
    )


if __name__ == "__main__":
    main()
