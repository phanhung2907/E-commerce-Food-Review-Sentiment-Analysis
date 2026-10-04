import os
from minio import Minio
from minio.error import S3Error

def upload_raw_to_minio():
    # 1. Khởi tạo MinIO client (Kết nối tới MinIO local qua Docker)
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",     # Thay đổi access key nếu cấu hình nhóm bạn khác
        secret_key="minioadmin",     # Thay đổi secret key nếu cấu hình nhóm bạn khác
        secure=False                 # False nếu chạy HTTP local
    )

    bucket_name = "tripadvisor-raw-data"
    
    # 2. Tạo bucket trên MinIO nếu chưa tồn tại
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Đã tạo bucket thành công trên MinIO: {bucket_name}")
        else:
            print(f"Bucket {bucket_name} đã tồn tại trên MinIO.")
    except S3Error as e:
        print(f"Lỗi khởi tạo bucket MinIO: {e}")
        return

    # 3. Đường dẫn thư mục chứa dữ liệu raw hiện tại của bạn (nơi có các file part_x.json)
    local_dir = "code/kien/data/raw/enterprise_100k"
    
    if not os.path.exists(local_dir):
        print(f"Thư mục local không tồn tại: {local_dir}")
        return

    # 4. Duyệt qua tất cả các file JSON và đẩy lên MinIO
    for filename in os.listdir(local_dir):
        if filename.endswith(".json"):
            local_path = os.path.join(local_dir, filename)
            object_name = f"raw_chunks/{filename}"
            
            try:
                client.fput_object(bucket_name, object_name, local_path)
                print(f"Đã tải lên MinIO thành công: {filename} -> {bucket_name}/{object_name}")
            except S3Error as e:
                print(f"Lỗi khi tải file {filename} lên MinIO: {e}")

if __name__ == "__main__":
    upload_raw_to_minio()