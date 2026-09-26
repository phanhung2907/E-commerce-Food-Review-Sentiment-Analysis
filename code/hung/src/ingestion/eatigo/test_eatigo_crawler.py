import json
import time
from datetime import datetime
from pathlib import Path

import requests


BASE_URL = "https://eatigo.com/v2/eatigo/product"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_json(url: str, params: dict | None = None) -> dict:
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def fetch_review_tags(product_id: str) -> dict:
    url = f"{BASE_URL}/{product_id}/review-tags-count"

    try:
        return fetch_json(url)
    except requests.RequestException as e:
        print(f"   ⚠️ Không lấy được review-tags-count: {e}")
        return {}


def crawl_product(product_id: str, page_size: int = 50) -> dict:
    comments_url = f"{BASE_URL}/{product_id}/comments"

    start = 0
    all_comments = []
    response_metadata = {}

    print(f"\n📍 Crawling product_id: {product_id}")

    while True:
        params = {
            "start": start,
            "size": page_size,
            "sortby": "default",
        }

        try:
            raw_response = fetch_json(comments_url, params=params)

        except requests.RequestException as e:
            print(f"   ❌ Request error: {e}")
            break

        data = raw_response.get("data", {})
        comments = data.get("comments", [])

        # Giữ TẤT CẢ field backend trả về ngoài comments
        # Không cần biết trước Eatigo có những field nào.
        response_metadata.update({
            key: value
            for key, value in data.items()
            if key != "comments"
        })

        # Giữ nguyên từng review object
        all_comments.extend(comments)

        print(
            f"   📥 start={start:<6} "
            f"received={len(comments):<3} "
            f"total_collected={len(all_comments)}"
        )

        if not comments:
            break

        start += len(comments)

        total_count = data.get("total_count")

        if total_count is not None and len(all_comments) >= total_count:
            break

        if len(comments) < page_size:
            break

        time.sleep(0.5)

    tags_response = fetch_review_tags(product_id)

    return {
        "product_id": product_id,
        "crawl_metadata": {
            "crawled_at": datetime.now().isoformat(),
            "comments_endpoint": comments_url,
            "records_collected": len(all_comments),
        },

        # Mọi field nằm trong data ngoại trừ comments
        "api_metadata": response_metadata,

        # Toàn bộ comments nguyên bản, KHÔNG chọn feature
        "comments": all_comments,

        # Giữ nguyên response endpoint tags
        "review_tags_count_response": tags_response,
    }


def crawl_eatigo(product_ids: list[str]):
    output_dir = Path("code/hung/data/raw/eatigo")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "eatigo_raw.json"

    result = {
        "source": "eatigo",
        "crawl_started_at": datetime.now().isoformat(),
        "products": [],
    }

    print("🚀 Eatigo Raw Crawler")
    print(f"📂 Products: {len(product_ids)}")

    for index, product_id in enumerate(product_ids, start=1):
        print(f"\n[{index}/{len(product_ids)}]")

        product_data = crawl_product(product_id)
        result["products"].append(product_data)

        # checkpoint sau mỗi restaurant
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                result,
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(
            f"   💾 Checkpoint saved "
            f"({len(product_data['comments'])} reviews)"
        )

    result["crawl_finished_at"] = datetime.now().isoformat()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )

    total_reviews = sum(
        len(product["comments"])
        for product in result["products"]
    )

    print("\n✅ Crawl completed")
    print(f"📊 Total reviews: {total_reviews}")
    print(f"📁 Output: {output_file}")


if __name__ == "__main__":
    product_ids = [
        "3644620907182",
        # "product_id_2",
        # "product_id_3",
    ]

    crawl_eatigo(product_ids)