from minio import Minio
from minio.error import S3Error
import os

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

    # 3. Đường dẫn file local (tự động lấy chính xác tuyệt đối theo vị trí file hiện tại)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_file_path = os.path.join(base_dir, "foody_sample_data.json")
    
    # Đặt tên object trên MinIO theo cấu trúc thư mục quy ước: source/date/filename
    object_name = "foody/2026-07-20/foody_sample_data.json"

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