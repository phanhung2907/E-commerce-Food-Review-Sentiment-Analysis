import csv
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


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

MAX_PAGES = 3
COUNT_PER_PAGE = 12

REQUEST_TIMEOUT = 20
REQUEST_DELAY = 1.0
LOCATION_DELAY = 2.0


# =========================================================
# HEADERS
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": (
        "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


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

    # root Foody = TP.HCM
    if parsed.path in ("", "/"):
        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/"
        )

    return url.rstrip("/")


def get_location_slug(url):
    """
    https://www.foody.vn/
        -> ho-chi-minh

    https://www.foody.vn/gia-lai
        -> gia-lai
    """

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
            f"Không tìm thấy config: "
            f"{LOCATIONS_FILE}"
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

            if not url:
                continue

            if url.startswith("#"):
                continue

            try:
                url = normalize_target_url(
                    url
                )

            except ValueError as e:

                print(
                    f"Skip line "
                    f"{line_number}: {e}"
                )

                continue

            locations.append(
                url
            )

    return locations


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
# OPEN LOCATION
# =========================================================

def open_location_page(
    session,
    url,
):
    print(
        f"Opening: {url}"
    )

    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT,
    )

    print(
        "Location HTTP:",
        response.status_code
    )

    response.raise_for_status()


# =========================================================
# FETCH RESTAURANT PAGE
# =========================================================

def fetch_restaurant_page(
    session,
    referer,
    page,
):
    params = {
        "t": int(
            time.time() * 1000
        ),

        "page": page,

        "count":
            COUNT_PER_PAGE,

        "districtId": "",
        "cateId": "",
        "cuisineId": "",
        "isReputation": "",

        "type": 1,
    }

    headers = (
        HEADERS.copy()
    )

    headers[
        "Referer"
    ] = referer

    response = session.get(
        HOME_LIST_API,
        params=params,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    print(
        f"Page {page} | "
        f"HTTP {response.status_code}"
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# FIND RESTAURANTS
# =========================================================

def looks_like_restaurant(
    item
):
    if not isinstance(
        item,
        dict
    ):
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

    return (
        len(
            keys & indicators
        )
        >= 2
    )


def find_restaurant_list(
    data
):
    if isinstance(
        data,
        list
    ):

        if (
            data
            and isinstance(
                data[0],
                dict
            )
            and looks_like_restaurant(
                data[0]
            )
        ):
            return data

        for item in data:

            result = (
                find_restaurant_list(
                    item
                )
            )

            if result:
                return result

        return []

    if not isinstance(
        data,
        dict
    ):
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

        value = data.get(
            key
        )

        if (
            isinstance(
                value,
                list
            )
            and value
            and looks_like_restaurant(
                value[0]
            )
        ):
            return value

    for value in data.values():

        if isinstance(
            value,
            (dict, list)
        ):

            result = (
                find_restaurant_list(
                    value
                )
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

        value = item.get(
            key
        )

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
    """
    code/hung/data/foody_shoppefood/raw/<city>/restaurants.csv
    """

    city_dir = (
        DATA_ROOT
        / city
    )

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

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            restaurants
        )

    print(
        "\nSaved:",
        output_path
    )


# =========================================================
# CRAWL ONE LOCATION
# =========================================================

def crawl_location(
    session,
    target_url,
):
    city = get_location_slug(
        target_url
    )

    print(
        "\n========================================"
    )

    print(
        f"CITY: {city}"
    )

    print(
        f"URL : {target_url}"
    )

    print(
        "========================================"
    )

    open_location_page(
        session,
        target_url
    )

    restaurants = []

    seen = set()

    for page in range(
        1,
        MAX_PAGES + 1,
    ):

        print(
            f"\n--- PAGE {page} ---"
        )

        data = (
            fetch_restaurant_page(
                session=session,
                referer=target_url,
                page=page,
            )
        )

        items = (
            find_restaurant_list(
                data
            )
        )

        if not items:

            print(
                "Không tìm thấy restaurant."
            )

            break

        new_count = 0

        for item in items:

            restaurant = (
                normalize_restaurant(
                    item,
                    city,
                )
            )

            restaurant_id = (
                restaurant[
                    "restaurant_id"
                ]
            )

            restaurant_url = (
                restaurant[
                    "url"
                ]
            )

            if restaurant_id is not None:

                key = (
                    f"id:"
                    f"{restaurant_id}"
                )

            elif restaurant_url:

                key = (
                    f"url:"
                    f"{restaurant_url}"
                )

            else:
                continue

            if key in seen:
                continue

            seen.add(
                key
            )

            restaurants.append(
                restaurant
            )

            new_count += 1

            print(
                restaurant[
                    "restaurant_id"
                ],
                "|",
                restaurant[
                    "name"
                ],
            )

        print(
            "New:",
            new_count
        )

        print(
            "Total:",
            len(restaurants)
        )

        if new_count == 0:
            break

        if len(items) < COUNT_PER_PAGE:
            break

        time.sleep(
            REQUEST_DELAY
        )

    if restaurants:

        save_restaurants_csv(
            restaurants,
            city,
        )

    return len(
        restaurants
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "\n=============================="
    )

    print(
        "FOODY RESTAURANT CRAWLER"
    )

    print(
        "=============================="
    )

    locations = (
        read_locations()
    )

    print(
        "Locations:",
        len(locations)
    )

    session = (
        create_session()
    )

    success = 0
    failed = 0
    total = 0

    for index, url in enumerate(
        locations,
        start=1,
    ):

        print(
            f"\n[{index}/{len(locations)}]"
        )

        try:

            count = crawl_location(
                session,
                url,
            )

            total += count
            success += 1

        except Exception as e:

            failed += 1

            print(
                f"FAILED: {url}"
            )

            print(
                e
            )

        time.sleep(
            LOCATION_DELAY
        )

    print(
        "\n=============================="
    )

    print(
        "DONE"
    )

    print(
        "=============================="
    )

    print(
        "Success:",
        success
    )

    print(
        "Failed:",
        failed
    )

    print(
        "Restaurants:",
        total
    )


if __name__ == "__main__":
    main()