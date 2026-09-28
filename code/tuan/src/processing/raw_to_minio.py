import os
from minio import Minio
from datetime import datetime
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

# Tự động lấy thông số từ file .env khớp với docker-compose
MINIO_URL = f"localhost:{os.getenv('MINIO_API_PORT', '9000')}"
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
BUCKET_NAME = "food-review-data"

def upload_to_minio(local_file_path, source_name, restaurant_id):
    client = Minio(MINIO_URL, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
    
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        print(f"[*] Đã tạo bucket mới: {BUCKET_NAME}")

    # Đường dẫn chuẩn lưu trên MinIO (Data Lake)
    date_str = datetime.now().strftime('%Y-%m-%d')
    minio_path = f"raw/{source_name}/{date_str}/restaurant_{restaurant_id}.json"
    
    try:
        client.fput_object(BUCKET_NAME, minio_path, local_file_path)
        print(f"[THÀNH CÔNG] Đã đẩy file {local_file_path} lên MinIO tại: {minio_path}")
    except Exception as e:
        print(f"[LỖI] Không thể upload: {e}")

if __name__ == "__main__":
    # Thay đường dẫn này bằng đường dẫn file JSON thật của bạn trong thư mục data/raw
    local_path = "code/tuan/data/befood/raw/befood_final_100_20260927.json"
    upload_to_minio(local_path, "befood", "9965")