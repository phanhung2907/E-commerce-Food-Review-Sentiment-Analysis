import os
import json
import unicodedata
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from minio import Minio
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

# Tự động lấy thông số từ file .env khớp với docker-compose
MINIO_URL = f"localhost:{os.getenv('MINIO_API_PORT', '9000')}"
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
BUCKET_NAME = "food-review-data"

def make_slug(text):
    """Hàm chuẩn hóa chuỗi thành dạng slug (VD: 'Đà Nẵng' -> 'da-nang')"""
    if not text:
        return "unknown-city"
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[-\s]+', '-', text.lower().strip())

def group_reviews_by_restaurant(file_paths):
    """Đọc các file JSON raw và gom nhóm review theo nhà hàng"""
    grouped_data = defaultdict(lambda: defaultdict(list))
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
                for record in records:
                    # Chuẩn hóa tên source về viết thường (befood, capichi)
                    source_name = str(record.get("source", "unknown")).lower()
                    restaurant_id = str(record.get("restaurant_id", ""))
                    
                    if restaurant_id:
                        grouped_data[source_name][restaurant_id].append(record)
        except Exception as e:
            print(f"[-] Lỗi khi đọc file {file_path}: {e}")
            
    return grouped_data

def upload_restaurant_to_minio(client, source, restaurant_id, reviews):
    """Định dạng cấu trúc chuẩn và đẩy lên MinIO"""
    if not reviews:
        return
    
    # Rút trích thông tin nhà hàng từ record đầu tiên
    first_record = reviews[0]
    raw_city = first_record.get("city", "Ho Chi Minh") # Mặc định HCM nếu không có
    city_slug = make_slug(raw_city)
    
    # Xây dựng cấu trúc chuẩn theo yêu cầu của hệ thống
    restaurant_data = {
        "source": source,
        "platform": f"{source}_app",
        "crawl_timestamp": datetime.now().isoformat(),
        "restaurant": {
            "restaurant_id": restaurant_id,
            "name": first_record.get("restaurant_name", ""),
            "address": first_record.get("address", ""),
            "url": first_record.get("restaurant_url", ""),
            "city": city_slug
        },
        "review_summary": {
            "total_reviews_api": first_record.get("total_reviews", len(reviews)),
            "total_reviews_crawled": len(reviews)
        },
        "reviews": reviews
    }
    
    # Định nghĩa Object Key theo chuẩn: <source>/raw/<city>/<restaurant_id>/restaurant.json
    minio_path = f"{source}/raw/{city_slug}/{restaurant_id}/restaurant.json"
    
    # Lưu tạm file JSON đã chuẩn hóa để đẩy lên MinIO
    temp_file_path = f"temp_{restaurant_id}.json"
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(restaurant_data, f, ensure_ascii=False, indent=4)
            
        # Upload lên MinIO
        client.fput_object(BUCKET_NAME, minio_path, temp_file_path)
        print(f"   [+] Upload thành công: {minio_path} ({len(reviews)} reviews)")
    except Exception as e:
        print(f"   [-] Lỗi upload {minio_path}: {e}")
    finally:
        # Xóa file tạm sau khi upload xong
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def main():
    # Khởi tạo kết nối MinIO
    client = Minio(MINIO_URL, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)

    # Đảm bảo bucket đã tồn tại
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        print(f"[*] Đã tạo bucket mới: {BUCKET_NAME}")

    # Tìm tất cả file JSON dữ liệu thô
    base_dir = Path("code/tuan/data")
    all_json_files = list(base_dir.rglob("*.json"))
    raw_files = [f for f in all_json_files if 'raw' in str(f)]
    
    print(f"[*] Tìm thấy {len(raw_files)} file JSON dữ liệu thô hợp lệ.")
    
    if not raw_files:
        print("[-] Không có dữ liệu để xử lý. Vui lòng kiểm tra lại thư mục data.")
        return

    # Gom nhóm dữ liệu theo từng nhà hàng
    print("[*] Đang gom nhóm dữ liệu theo từng nhà hàng...")
    grouped_data = group_reviews_by_restaurant(raw_files)

    # Đẩy dữ liệu lên MinIO
    print("[*] Bắt đầu đẩy dữ liệu chuẩn hóa lên MinIO Data Lake...")
    for source, restaurants in grouped_data.items():
        print(f"\n=> Xử lý Source: {source.upper()} ({len(restaurants)} nhà hàng)")
        for rest_id, reviews in restaurants.items():
            upload_restaurant_to_minio(client, source, rest_id, reviews)
            
    print("\n🏆 Hoàn tất quy trình phân tách và đẩy dữ liệu lên MinIO!")

if __name__ == "__main__":
    main()