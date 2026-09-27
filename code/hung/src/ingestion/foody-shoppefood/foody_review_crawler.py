import argparse
import csv
import json
import time

from pathlib import Path
from datetime import datetime

import requests


# =========================================================
# CONFIG
# =========================================================

PLATFORM_NAME = "foody_shoppefood"

DATA_ROOT = Path(
    "code/hung/data"
) / PLATFORM_NAME / "raw"

FOODY_REVIEW_API = (
    "https://www.foody.vn/"
    "__get/Review/ResLoadMore"
)

REVIEWS_PER_REQUEST = 10

REQUEST_DELAY = 1.0
RESTAURANT_DELAY = 1.5

REQUEST_TIMEOUT = 20
MAX_RETRIES = 3


# =========================================================
# HEADERS
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


# =========================================================
# SESSION
# =========================================================

def create_session():
    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    return session


# =========================================================
# FIND RESTAURANT FILES
# =========================================================

def find_restaurant_files():
    """
    Tìm:

    code/hung/data/foody_shoppefood/raw/
        gia-lai/restaurants.csv
        binh-dinh/restaurants.csv
        ...
    """

    if not DATA_ROOT.exists():

        raise FileNotFoundError(
            f"Không tồn tại: "
            f"{DATA_ROOT}"
        )

    return sorted(
        DATA_ROOT.glob(
            "*/restaurants.csv"
        )
    )


# =========================================================
# CITY
# =========================================================

def get_city_from_path(
    csv_path
):
    return (
        csv_path.parent.name
    )


# =========================================================
# READ RESTAURANTS
# =========================================================

def read_restaurants(
    csv_path
):
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

            restaurant_id = (
                row
                .get(
                    "restaurant_id",
                    "",
                )
                .strip()
            )

            if not restaurant_id:
                continue

            try:

                restaurant_id = int(
                    restaurant_id
                )

            except ValueError:

                print(
                    "Invalid ID:",
                    restaurant_id
                )

                continue

            restaurants.append({
                "restaurant_id":
                    restaurant_id,

                "name":
                    row.get(
                        "name",
                        ""
                    ),

                "address":
                    row.get(
                        "address",
                        ""
                    ),

                "url":
                    row.get(
                        "url",
                        ""
                    ),

                "city":
                    row.get(
                        "city",
                        ""
                    ),
            })

    return restaurants


# =========================================================
# REQUEST REVIEW PAGE
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
            str(exclude_ids or ""),

        "LastId":
            str(
                last_id
            ),
    }

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

            print(
                f"HTTP "
                f"{response.status_code}"
            )

        except (
            requests.RequestException,
            ValueError,
        ) as e:

            print(
                f"Attempt "
                f"{attempt}/"
                f"{MAX_RETRIES}:",
                e
            )

        if attempt < MAX_RETRIES:

            time.sleep(
                attempt * 2
            )

    return None


# =========================================================
# CRAWL RESTAURANT
# =========================================================

def crawl_restaurant_reviews(
    session,
    restaurant,
    max_reviews=None,
):
    restaurant_id = (
        restaurant[
            "restaurant_id"
        ]
    )

    name = (
        restaurant[
            "name"
        ]
    )

    print(
        f"\nCrawling: "
        f"{name} "
        f"(ResId={restaurant_id})"
    )

    reviews = []

    seen_review_ids = set()

    last_id = ""
    exclude_ids = ""

    total_api = None

    page = 1
    seen_cursor_states = set()

    while True:

        data = (
            request_review_page(
                session,
                restaurant_id,
                last_id,
                exclude_ids,
            )
        )

        if data is None:

            print(
                "Request failed."
            )

            break

        if total_api is None:

            total_api = (
                data.get(
                    "Total"
                )
                or data.get(
                    "Summary",
                    {}
                ).get(
                    "Total"
                )
            )

            print(
                "Total API (có thể bị Foody cap):",
                total_api
            )

        items = (
            data.get(
                "Items"
            )
            or []
        )

        print(
            f"Page {page}: "
            f"{len(items)}"
        )

        if not items:
            print("STOP: API không còn trả review.")
            break

        new_reviews = 0

        for item in items:

            review_id = (
                item.get(
                    "Id"
                )
            )

            if (
                review_id
                is not None
                and review_id
                in seen_review_ids
            ):
                continue

            if review_id is not None:

                seen_review_ids.add(
                    review_id
                )

            review = (
                item.copy()
            )

            # crawler metadata
            review[
                "source"
            ] = "foody"

            review[
                "restaurant_id_query"
            ] = restaurant_id

            review[
                "restaurant_name"
            ] = name

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

            reviews.append(
                review
            )

            new_reviews += 1

            if (
                max_reviews is not None
                and len(reviews) >= max_reviews
            ):
                break

        if (
            max_reviews is not None
            and len(reviews) >= max_reviews
        ):
            print(
                f"Đã đạt giới hạn {max_reviews} review."
            )
            break

        if new_reviews == 0:
            print("STOP: trang mới không có review mới.")
            break

        new_last_id = data.get("LastId")

        if not new_last_id:
            new_last_id = items[-1].get("Id")

        if not new_last_id:
            print("STOP: không còn LastId để phân trang.")
            break

        new_exclude_ids = data.get("ExcludeIds")
        if new_exclude_ids is None:
            new_exclude_ids = exclude_ids

        cursor_state = (
            str(new_last_id),
            str(new_exclude_ids or ""),
        )

        if cursor_state in seen_cursor_states:
            print("STOP: cursor bị lặp.")
            break

        seen_cursor_states.add(cursor_state)

        last_id = new_last_id
        exclude_ids = new_exclude_ids or ""

        # Không dừng theo data["Total"].
        # Foody có thể trả Total=100 dù trang web có >100 review.
        # Chỉ dừng khi API thực sự hết Items/cursor hoặc đạt max_reviews.

        page += 1

        time.sleep(
            REQUEST_DELAY
        )

    print(
        "Reviews crawled:",
        len(reviews)
    )

    return {
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
            "total_reviews_api":
                total_api,

            "total_reviews_crawled":
                len(reviews),
        },

        "reviews":
            reviews,
    }


# =========================================================
# SAVE REVIEW JSON
# =========================================================

def save_city_reviews(
    city,
    csv_path,
    results,
):
    crawl_day = (
        datetime.now()
        .strftime(
            "%Y-%m-%d"
        )
    )

    output_path = (
        csv_path.parent
        / (
            f"reviews_"
            f"{crawl_day}.json"
        )
    )

    total_reviews = sum(
        result[
            "review_summary"
        ][
            "total_reviews_crawled"
        ]
        for result
        in results
    )

    output = {
        "source":
            "foody",

        "platform":
            PLATFORM_NAME,

        "city":
            city,

        "crawl_date":
            crawl_day,

        "crawl_timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "total_restaurants":
            len(results),

        "total_reviews":
            total_reviews,

        "restaurants":
            results,
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "\nSaved:",
        output_path
    )


# =========================================================
# CRAWL CITY
# =========================================================

def crawl_city(
    session,
    csv_path,
    max_reviews=None,
):
    city = (
        get_city_from_path(
            csv_path
        )
    )

    print(
        "\n========================================"
    )

    print(
        f"CITY: {city}"
    )

    print(
        "========================================"
    )

    restaurants = (
        read_restaurants(
            csv_path
        )
    )

    print(
        "Restaurants:",
        len(restaurants)
    )

    results = []

    for index, restaurant in enumerate(
        restaurants,
        start=1,
    ):

        print(
            f"\n[{index}/"
            f"{len(restaurants)}]"
        )

        result = (
            crawl_restaurant_reviews(
                session,
                restaurant,
                max_reviews=max_reviews,
            )
        )

        results.append(
            result
        )

        time.sleep(
            RESTAURANT_DELAY
        )

    save_city_reviews(
        city,
        csv_path,
        results,
    )


# =========================================================
# MAIN
# =========================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Foody review crawler"
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=None,
        help="Số review tối đa cho mỗi restaurant. Bỏ trống = vét cạn.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.max_reviews is not None and args.max_reviews <= 0:
        raise ValueError("--max-reviews phải > 0")

    print(
        "\n=============================="
    )

    print(
        "FOODY REVIEW CRAWLER"
    )

    print(
        "=============================="
    )

    files = (
        find_restaurant_files()
    )

    if not files:

        print(
            "Không tìm thấy "
            "restaurants.csv"
        )

        return

    print(
        "Files:",
        len(files)
    )

    session = (
        create_session()
    )

    for csv_path in files:

        try:

            crawl_city(
                session,
                csv_path,
                max_reviews=args.max_reviews,
            )

        except Exception as e:

            print(
                f"ERROR: "
                f"{csv_path}"
            )

            print(
                e
            )

    print(
        "\n=============================="
    )

    print(
        "ALL DONE"
    )

    print(
        "=============================="
    )


if __name__ == "__main__":
    main()