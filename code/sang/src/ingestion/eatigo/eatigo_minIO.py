import json
import ijson
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import datetime


def upload_restaurant(client, bucket_name, product_id, records):

    first_record = records[0]

    restaurant_data = {
        "source": "eatigo",
        "platform": "eatigo",
        "crawl_timestamp": datetime.now().isoformat(),

        "restaurant": {
            "restaurant_id": product_id
        },

        "restaurant_tags_raw":
            first_record.get("restaurant_tags_raw", {}),

        "comment_container_raw":
            first_record.get("comment_container_raw", {}),

        "reviews": []
    }

    # Giữ nguyên review thật
    for record in records:

        review = record.get("review_item_raw")

        if review is not None:
            restaurant_data["reviews"].append(review)

    # Đúng cấu trúc MinIO của nhóm
    object_name = (
        f"eatigo/raw/"
        f"ho-chi-minh/"
        f"{product_id}/"
        f"restaurant.json"
    )

    # default=str để xử lý Decimal
    json_data = json.dumps(
        restaurant_data,
        ensure_ascii=False,
        indent=4,
        default=str
    ).encode("utf-8")

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


def upload_to_minio():

    # ============================================================
    # Kết nối MinIO
    # ============================================================

    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )

    bucket_name = "raw-data"

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Đã tạo bucket: {bucket_name}")

    # ============================================================
    # File JSON đã crawl trước đó
    # ============================================================

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

    print("📖 Bắt đầu đọc JSON từng record...")
    print("📂 File:", local_file_path)

    # ============================================================
    # Đọc JSON streaming - không load toàn bộ file vào RAM
    # ============================================================

    current_product_id = None
    current_records = []

    restaurant_count = 0
    review_count = 0

    try:

        with open(local_file_path, "rb") as f:

            records = ijson.items(f, "item")

            for record in records:

                product_id = str(
                    record.get("product_id") or ""
                ).strip()

                if not product_id:
                    continue

                # Nếu chuyển sang restaurant mới
                if (
                    current_product_id is not None
                    and product_id != current_product_id
                ):

                    upload_restaurant(
                        client,
                        bucket_name,
                        current_product_id,
                        current_records
                    )

                    restaurant_count += 1
                    review_count += len(current_records)

                    current_records = []

                current_product_id = product_id

                current_records.append(record)

        # Upload restaurant cuối cùng
        if current_product_id and current_records:

            upload_restaurant(
                client,
                bucket_name,
                current_product_id,
                current_records
            )

            restaurant_count += 1
            review_count += len(current_records)

    except Exception as e:

        print("❌ Có lỗi khi xử lý file:")
        print(e)

        return

    # ============================================================
    # Kết quả
    # ============================================================

    print("\n========================================")
    print("✨ HOÀN TẤT UPLOAD MINIO")
    print("========================================")
    print(f"🏪 Số restaurant: {restaurant_count}")
    print(f"📝 Số review: {review_count}")
    print("📂 Cấu trúc:")
    print(
        "eatigo/raw/ho-chi-minh/"
        "<restaurant_id>/restaurant.json"
    )
    print("========================================")


if __name__ == "__main__":
    upload_to_minio()