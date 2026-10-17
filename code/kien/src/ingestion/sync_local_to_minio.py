import os
from minio import Minio
from minio.error import S3Error

def sync_clean_data_to_minio():
    # 1. Khởi tạo kết nối MinIO Client
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

    bucket_name = "tripadvisor-raw-data"
    
    # 2. Kiểm tra và tạo Bucket nếu chưa tồn tại
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"[MinIO] Đã tạo bucket mới thành công: {bucket_name}")
        else:
            print(f"[MinIO] Bucket {bucket_name} đã sẵn sàng.")
    except S3Error as e:
        print(f"[MinIO Error] Lỗi kiểm tra bucket: {e}")
        return

    # 3. Trỏ đến thư mục local chứa dữ liệu chuẩn đã lọc sạch 0 review
    local_dir = "code/kien/data/raw/single_restaurants"
    
    if not os.path.exists(local_dir):
        print(f"[Error] Không tìm thấy thư mục local: {local_dir}")
        return

    # 4. Lọc ra các file JSON và đẩy lên thư mục individual_restaurants trên MinIO
    files = [f for f in os.listdir(local_dir) if f.endswith(".json")]
    total_files = len(files)
    print(f"[Sync Start] Bắt đầu đồng bộ {total_files} file chuẩn lên MinIO...")

    success_count = 0
    for idx, filename in enumerate(files):
        local_path = os.path.join(local_dir, filename)
        # Đẩy đúng vào cấu trúc thư mục individual_restaurants trên MinIO
        object_name = f"individual_restaurants/{filename}"
        
        try:
            client.fput_object(bucket_name, object_name, local_path)
            success_count += 1
            print(f" [{success_count}/{total_files}] Đã đồng bộ thành công: {filename}")
        except S3Error as e:
            print(f" [Error] Lỗi khi đẩy file {filename}: {e}")

    print(f"\n[SUCCESS] Hoàn tất đồng bộ! Tổng số file đã đưa lên MinIO: {success_count}/{total_files}")

if __name__ == "__main__":
    sync_clean_data_to_minio()