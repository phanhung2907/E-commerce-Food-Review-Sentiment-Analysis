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

# None = toàn bộ
MAX_REVIEWS_PER_RESTAURANT = None

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
            "",

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

    total_api = None

    page = 1

    while True:

        data = (
            request_review_page(
                session,
                restaurant_id,
                last_id,
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
                "Total API:",
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
                MAX_REVIEWS_PER_RESTAURANT
                is not None
                and len(reviews)
                >= MAX_REVIEWS_PER_RESTAURANT
            ):
                break

        if (
            MAX_REVIEWS_PER_RESTAURANT
            is not None
            and len(reviews)
            >= MAX_REVIEWS_PER_RESTAURANT
        ):
            break

        if new_reviews == 0:
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
            break

        if (
            str(new_last_id)
            == str(last_id)
        ):
            break

        last_id = (
            new_last_id
        )

        if (
            isinstance(
                total_api,
                int
            )
            and len(reviews)
            >= total_api
        ):
            break

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

def main():

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