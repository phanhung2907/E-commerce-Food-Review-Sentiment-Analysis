from minio import Minio
from minio.error import S3Error
import os
from datetime import datetime  # <-- Nhớ có dòng này để lấy ngày tháng

def upload_to_minio():
    # 1. Khởi tạo MinIO client
    client = Minio(
        "localhost:9000",                    # Cổng API S3 chuẩn của MinIO
        access_key="minioadmin",            # Access key
        secret_key="minioadmin123",         # Secret key
        secure=False                        # Không dùng https cho môi trường local
    )

    # 2. Tên bucket quy ước chung của team
    bucket_name = "raw-data"

    # Tạo bucket nếu chưa tồn tại
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Đã tạo bucket: {bucket_name}")

    # 3. Đường dẫn file local (Dùng đường dẫn tuyệt đối cho an toàn tuyệt đối)
    local_file_path = r"C:\Users\LENOVO\Documents\GitHub\E-commerce-Food-Review-Sentiment-Analysis\code\sang\data\raw\eatigo\eatigo_raw_objects_final.json"
    
    # Lấy ngày hiện tại tự động
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Đặt tên object trên MinIO theo cấu trúc thư mục quy ước của nhóm
    object_name = f"eatigo/{current_date}/eatigo_raw_objects_final.json"

    try:
        # 4. Thực hiện upload
        client.fput_object(
            bucket_name, object_name, local_file_path,
        )
        print(f"✅ Thành công! Đã đẩy file lên MinIO tại: s3://{bucket_name}/{object_name}")
        
    except S3Error as e:
        print(f"❌ Lỗi khi upload lên MinIO: {e}")

if __name__ == "__main__":
    upload_to_minio()