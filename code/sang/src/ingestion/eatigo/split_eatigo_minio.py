import ijson
import io
import json
from minio import Minio

def split_and_upload_streaming():
    # 1. Kết nối MinIO (Đảm bảo Docker MinIO đã được bật ở cổng 9000)
    minio_client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )
    
    bucket_name = "food-review-data"
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    input_file = "code/sang/data/raw/eatigo/eatigo_raw_objects_final.json"
    print("📥 Đang stream file raw lớn để phân vùng và đẩy lên MinIO...")

    # 2. Dùng ijson đọc stream từ file cục bộ (tránh tuyệt đối lỗi MemoryError)
    restaurants_dict = {}
    
    with open(input_file, "rb") as f:
        # Giả sử file JSON là một mảng lớn các item từ crawler
        parser = ijson.items(f, 'item')
        
        count = 0
        for record in parser:
            product_id = str(record.get("product_id"))
            container = record.get("comment_container_raw", {})
            
            # Nếu nhà hàng chưa có trong dict tạm, khởi tạo khung cấu trúc chuẩn
            if product_id not in restaurants_dict:
                city_raw = container.get("city", "ho-chi-minh")
                if not city_raw:
                    city_raw = "ho-chi-minh"
                city_slug = str(city_raw).lower().strip().replace(" ", "-")
                
                restaurants_dict[product_id] = {
                    "city": city_slug,
                    "container": container,
                    "tags": record.get("restaurant_tags_raw", {}),
                    "reviews": []
                }
            
            # Gom review vào đúng nhà hàng tương ứng
            review_item = record.get("review_item_raw")
            if review_item:
                restaurants_dict[product_id]["reviews"].append(review_item)
            
            count += 1
            if count % 5000 == 0:
                print(f"Đã gom được {count} records...")

    print(f"🔄 Đang đẩy {len(restaurants_dict)} nhà hàng đã phân vùng lên MinIO...")

    # 3. Đẩy từng nhà hàng lên MinIO theo chuẩn <city>/<restaurant_id>/restaurant.json
    uploaded_count = 0
    for product_id, data in restaurants_dict.items():
        city_slug = data["city"]
        container = data["container"]
        
        object_key = f"eatigo/raw/{city_slug}/{product_id}/restaurant.json"
        
        restaurant_object = {
            "source": "eatigo",
            "crawl_timestamp": "2026-09-28T00:00:00",
            "restaurant": {
                "restaurant_id": product_id,
                "name": container.get("restaurant_name") or "Chưa cập nhật tên",
                "city": city_slug,
                "address": container.get("address"),
            },
            "review_summary": {
                "total_reviews_crawled": len(data["reviews"])
            },
            "restaurant_tags_raw": data["tags"],
            "reviews": data["reviews"]
        }
        
        json_bytes = json.dumps(restaurant_object, ensure_ascii=False, indent=4).encode('utf-8')
        data_stream = io.BytesIO(json_bytes)
        
        minio_client.put_object(
            bucket_name,
            object_key,
            data_stream,
            len(json_bytes),
            content_type="application/json"
        )
        
        uploaded_count += 1
        if uploaded_count % 50 == 0:
            print(f"Đã upload {uploaded_count} nhà hàng lên MinIO...")

    print(f"✨ Hoàn tất toàn bộ quá trình phân vùng và đẩy lên MinIO thành công!")

if __name__ == "__main__":
    split_and_upload_streaming()