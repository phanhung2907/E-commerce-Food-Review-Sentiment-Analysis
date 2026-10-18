import json
import ijson
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import datetime


def upload_restaurant(client, bucket_name, country, city, product_id, records):
    if not records:
        return

    first_record = records[0]

    # Chuẩn hóa tên quốc gia và thành phố thành slug
    country_slug = country.lower().replace(" ", "-") if country else "unknown-country"
    city_slug = city.lower().replace(" ", "-") if city else "unknown-city"

    restaurant_data = {
        "source": "eatigo",
        "platform": "eatigo",
        "crawl_timestamp": datetime.now().isoformat(),
        "country": country,
        "city": city,
        "restaurant": {
            "restaurant_id": product_id
        },
        "restaurant_tags_raw": first_record.get("restaurant_tags_raw", {}),
        "comment_container_raw": first_record.get("comment_container_raw", {}),
        "reviews": []
    }

    # Giữ nguyên review thật, không fake dữ liệu
    for record in records:
        review = record.get("review_item_raw")
        if review is not None:
            restaurant_data["reviews"].append(review)

    # Cấu trúc MinIO phân cấp: eatigo/raw/<country>/<city>/<restaurant_id>/restaurant.json
    object_name = (
        f"eatigo/raw/"
        f"{country_slug}/"
        f"{city_slug}/"
        f"{product_id}/"
        f"restaurant.json"
    )

    # default=str để xử lý kiểu dữ liệu Decimal
    json_data = json.dumps(
        restaurant_data,
        ensure_ascii=False,
        indent=4,
        default=str
    ).encode("utf-8")

    try:
        client.put_object(
            bucket_name,
            object_name,
            BytesIO(json_data),
            length=len(json_data),
            content_type="application/json"
        )
        print(
            f"✅ Đã upload: {object_name} "
            f"({len(restaurant_data['reviews'])} reviews)"
        )
    except S3Error as err:
        print(f"❌ Lỗi S3 khi upload {object_name}: {err}")


def upload_to_minio():
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )

    bucket_name = "raw-data"

    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Đã tạo bucket: {bucket_name}")
    except S3Error as err:
        print(f"❌ Lỗi kết nối MinIO bucket: {err}")
        return

    local_file_path = Path(
        r"C:\Users\LENOVO\Documents\GitHub"
        r"\E-commerce-Food-Review-Sentiment-Analysis"
        r"\code\sang\data\raw\eatigo"
        r"\eatigo_raw_objects_final.json"
    )

    if not local_file_path.exists():
        print("❌ Không tìm thấy file:")
        print(local_file_path)
        return

    print("📖 Bắt đầu đọc JSON streaming với ijson và gom nhóm theo restaurant_id...")
    print("📂 File:", local_file_path)

    restaurants_dict = {}
    restaurant_count = 0
    review_count = 0

    try:
        with open(local_file_path, "rb") as f:
            # Dùng ijson đọc từng item tuần tự, tiết kiệm tối đa RAM
            records = ijson.items(f, "item")

            for record in records:
                product_id = str(
                    record.get("product_id") or ""
                ).strip()

                if not product_id:
                    continue

                # Gom tất cả các record có chung product_id vào từ điển
                if product_id not in restaurants_dict:
                    restaurants_dict[product_id] = []
                restaurants_dict[product_id].append(record)

        print(f"🎯 Đã gom nhóm thành công {len(restaurants_dict)} nhà hàng. Bắt đầu đẩy lên MinIO...")

        # Tiến hành upload từng nhà hàng lên MinIO
        for product_id, records in restaurants_dict.items():
            first_record = records[0]
            container = first_record.get("comment_container_raw", {})
            country = container.get("country") or first_record.get("country") or None
            city = container.get("city") or first_record.get("city") or None

            upload_restaurant(
                client,
                bucket_name,
                country,
                city,
                product_id,
                records
            )

            restaurant_count += 1
            reviews_in_rest = [r.get("review_item_raw") for r in records if r.get("review_item_raw") is not None]
            review_count += len(reviews_in_rest)

    except Exception as e:
        print("❌ Có lỗi khi xử lý file:")
        print(e)
        return

    print("\n========================================")
    print("✨ HOÀN TẤT UPLOAD MINIO (STREAMING)")
    print("========================================")
    print(f"🏪 Số restaurant: {restaurant_count}")
    print(f"📝 Số review: {review_count}")
    print("📂 Cấu trúc: eatigo/raw/<country>/<city>/<restaurant_id>/restaurant.json")
    print("========================================")


if __name__ == "__main__":
    upload_to_minio()