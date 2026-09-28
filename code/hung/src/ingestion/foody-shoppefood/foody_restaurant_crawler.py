import argparse
import csv
import random
import threading
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter


# =========================================================
# CONFIG
# =========================================================

PLATFORM_NAME = "foody_shoppefood"

LOCATIONS_FILE = Path(
    "code/hung/configs/foody_locations.txt"
)

DATA_ROOT = Path(
    "code/hung/data"
) / PLATFORM_NAME / "raw"

BASE_URL = "https://www.foody.vn"

HOME_LIST_API = (
    f"{BASE_URL}/__get/Place/HomeListPlace"
)

COUNT_PER_PAGE = 12

DEFAULT_WORKERS = 50
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 0.15
MAX_RETRIES = 5


# =========================================================
# HEADERS / THREADING
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With": "XMLHttpRequest",
}

_thread_local = threading.local()
_print_lock = threading.Lock()


def log(*args):
    with _print_lock:
        print(*args, flush=True)


def get_session():
    session = getattr(
        _thread_local,
        "session",
        None,
    )

    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)

        adapter = HTTPAdapter(
            pool_connections=4,
            pool_maxsize=4,
            max_retries=0,
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        _thread_local.session = session

    return session


# =========================================================
# URL HELPERS
# =========================================================

def normalize_target_url(url):
    parsed = urlparse(url)

    if not parsed.scheme:
        raise ValueError(
            f"URL thiếu http/https: {url}"
        )

    if not parsed.netloc:
        raise ValueError(
            f"URL không hợp lệ: {url}"
        )

    if "foody.vn" not in parsed.netloc.lower():
        raise ValueError(
            f"Không phải Foody URL: {url}"
        )

    if parsed.path in ("", "/"):
        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/"
        )

    return url.rstrip("/")


def get_location_slug(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        return "ho-chi-minh"

    return path.split("/")[0]


# =========================================================
# READ LOCATIONS
# =========================================================

def read_locations():
    if not LOCATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy config: {LOCATIONS_FILE}"
        )

    locations = []

    with open(
        LOCATIONS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            url = line.strip()

            if not url or url.startswith("#"):
                continue

            try:
                locations.append(
                    normalize_target_url(url)
                )
            except ValueError as e:
                log(
                    f"Skip line {line_number}: {e}"
                )

    return locations


# =========================================================
# HTTP
# =========================================================

def get_with_retry(
    session,
    url,
    *,
    params=None,
    headers=None,
):
    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):
        try:
            response = session.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                return response

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
                        wait = float(retry_after)
                    except ValueError:
                        wait = None
                else:
                    wait = None

                if wait is None:
                    wait = min(
                        30,
                        (2 ** (attempt - 1))
                        + random.uniform(0.2, 1.0),
                    )

                last_error = RuntimeError(
                    f"HTTP {response.status_code}"
                )

                log(
                    f"HTTP {response.status_code}; "
                    f"retry {attempt}/{MAX_RETRIES} "
                    f"sau {wait:.1f}s"
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

        except requests.RequestException as e:
            last_error = e

            if attempt >= MAX_RETRIES:
                break

            wait = min(
                30,
                (2 ** (attempt - 1))
                + random.uniform(0.2, 1.0),
            )

            time.sleep(wait)

    if last_error:
        raise last_error

    raise RuntimeError(
        f"Không lấy được response: {url}"
    )


def open_location_page(
    session,
    url,
):
    response = get_with_retry(
        session,
        url,
    )

    return response.status_code


def fetch_restaurant_page(
    session,
    referer,
    page,
):
    params = {
        "t": int(time.time() * 1000),
        "page": page,
        "count": COUNT_PER_PAGE,
        "districtId": "",
        "cateId": "",
        "cuisineId": "",
        "isReputation": "",
        "type": 1,
    }

    headers = HEADERS.copy()
    headers["Referer"] = referer

    response = get_with_retry(
        session,
        HOME_LIST_API,
        params=params,
        headers=headers,
    )

    return response.json()


# =========================================================
# FIND RESTAURANTS
# =========================================================

def looks_like_restaurant(item):
    if not isinstance(item, dict):
        return False

    keys = {
        str(key).lower()
        for key in item.keys()
    }

    indicators = {
        "id",
        "resid",
        "name",
        "address",
        "url",
    }

    return len(keys & indicators) >= 2


def find_restaurant_list(data):
    if isinstance(data, list):
        if (
            data
            and isinstance(data[0], dict)
            and looks_like_restaurant(data[0])
        ):
            return data

        for item in data:
            result = find_restaurant_list(item)

            if result:
                return result

        return []

    if not isinstance(data, dict):
        return []

    preferred_keys = [
        "Items",
        "items",
        "Places",
        "places",
        "Restaurants",
        "restaurants",
    ]

    for key in preferred_keys:
        value = data.get(key)

        if (
            isinstance(value, list)
            and value
            and looks_like_restaurant(value[0])
        ):
            return value

    for value in data.values():
        if isinstance(value, (dict, list)):
            result = find_restaurant_list(
                value
            )

            if result:
                return result

    return []


# =========================================================
# NORMALIZE
# =========================================================

def get_first_value(
    item,
    *keys,
):
    for key in keys:
        value = item.get(key)

        if value is not None:
            return value

    return None


def normalize_restaurant(
    item,
    city,
):
    return {
        "restaurant_id":
            get_first_value(
                item,
                "Id",
                "ResId",
                "RestaurantId",
                "restaurant_id",
            ),
        "name":
            get_first_value(
                item,
                "Name",
                "name",
            ),
        "address":
            get_first_value(
                item,
                "Address",
                "address",
            ),
        "url":
            get_first_value(
                item,
                "Url",
                "url",
            ),
        "city":
            city,
    }


# =========================================================
# SAVE CSV
# =========================================================

def save_restaurants_csv(
    restaurants,
    city,
):
    city_dir = DATA_ROOT / city

    city_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        city_dir
        / "restaurants.csv"
    )

    fieldnames = [
        "restaurant_id",
        "name",
        "address",
        "url",
        "city",
    ]

    temp_path = output_path.with_suffix(
        ".csv.tmp"
    )

    with open(
        temp_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(restaurants)

    temp_path.replace(output_path)

    return output_path


# =========================================================
# CRAWL ONE LOCATION
# =========================================================

def crawl_location(
    target_url,
    max_restaurants=None,
):
    session = get_session()

    city = get_location_slug(
        target_url
    )

    log(
        f"[{city}] START {target_url}"
    )

    open_location_page(
        session,
        target_url,
    )

    restaurants = []
    seen = set()
    page = 1

    while True:
        data = fetch_restaurant_page(
            session=session,
            referer=target_url,
            page=page,
        )

        items = find_restaurant_list(data)

        if not items:
            break

        new_count = 0

        for item in items:
            restaurant = normalize_restaurant(
                item,
                city,
            )

            restaurant_id = (
                restaurant["restaurant_id"]
            )

            restaurant_url = (
                restaurant["url"]
            )

            if restaurant_id is not None:
                key = f"id:{restaurant_id}"
            elif restaurant_url:
                key = f"url:{restaurant_url}"
            else:
                continue

            if key in seen:
                continue

            seen.add(key)
            restaurants.append(restaurant)
            new_count += 1

            if (
                max_restaurants is not None
                and len(restaurants)
                >= max_restaurants
            ):
                break

        log(
            f"[{city}] page={page} "
            f"new={new_count} "
            f"total={len(restaurants)}"
        )

        if new_count == 0:
            break

        if (
            max_restaurants is not None
            and len(restaurants)
            >= max_restaurants
        ):
            break

        page += 1

        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

    output_path = None

    if restaurants:
        output_path = save_restaurants_csv(
            restaurants,
            city,
        )

    log(
        f"[{city}] DONE "
        f"{len(restaurants)} restaurants"
    )

    return {
        "city": city,
        "count": len(restaurants),
        "output_path": output_path,
    }


# =========================================================
# MAIN
# =========================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Foody restaurant crawler "
            "đa luồng theo tỉnh/thành"
        )
    )

    parser.add_argument(
        "--max-restaurants",
        type=int,
        default=None,
        help=(
            "Số restaurant tối đa cho mỗi "
            "endpoint/tỉnh. Bỏ trống = vét cạn."
        ),
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            f"Số worker chạy song song. "
            f"Mặc định={DEFAULT_WORKERS}."
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

    return parser.parse_args()


def main():
    args = parse_args()

    if (
        args.max_restaurants is not None
        and args.max_restaurants <= 0
    ):
        raise ValueError(
            "--max-restaurants phải > 0"
        )

    if args.workers < 1:
        raise ValueError(
            "--workers phải >= 1"
        )

    locations = read_locations()

    if args.city:
        locations = [
            url
            for url in locations
            if get_location_slug(url)
            == args.city
        ]

    if not locations:
        print(
            "Không có location nào để crawl."
        )
        return

    worker_count = min(
        args.workers,
        len(locations),
    )

    print(
        "\nFOODY RESTAURANT CRAWLER"
    )
    print(
        "Locations:",
        len(locations),
    )
    print(
        "Workers:",
        worker_count,
    )

    success = 0
    failed = 0
    total = 0

    with ThreadPoolExecutor(
        max_workers=worker_count
    ) as executor:
        futures = {
            executor.submit(
                crawl_location,
                url,
                args.max_restaurants,
            ): url
            for url in locations
        }

        for future in as_completed(futures):
            url = futures[future]

            try:
                result = future.result()
                success += 1
                total += result["count"]

            except Exception as e:
                failed += 1
                log(
                    f"FAILED: {url} | {e}"
                )

    print(
        "\n=============================="
    )
    print("DONE")
    print(
        "Success locations:",
        success,
    )
    print(
        "Failed locations:",
        failed,
    )
    print(
        "Restaurants:",
        total,
    )


if __name__ == "__main__":
    main()
