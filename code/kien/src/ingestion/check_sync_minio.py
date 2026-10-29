import os
from minio import Minio

# Cấu hình kết nối MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "tripadvisor-raw-data"

LOCAL_DIR = "code/kien/data/raw/single_restaurants"

def verify_sync():
    # 1. Lấy danh sách tên file trong thư mục local
    if not os.path.exists(LOCAL_DIR):
        print(f"[Error] Thư mục local không tồn tại: {LOCAL_DIR}")
        return
    
    local_files = {f for f in os.listdir(LOCAL_DIR) if f.endswith(".json")}
    print(f"[Local] Tổng số file JSON local: {len(local_files)}")

    # 2. Kết nối MinIO và lấy danh sách file trên server
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    
    try:
        # Lấy tất cả objects có trong bucket (đệ quy)
        objects = client.list_objects(MINIO_BUCKET, recursive=True)
        minio_files = set()
        for obj in objects:
            # Lấy tên file cuối cùng từ đường dẫn object (vd: individual_restaurants/file.json -> file.json)
            file_name = os.path.basename(obj.object_name)
            if file_name.endswith(".json"):
                minio_files.add(file_name)
        
        print(f"[MinIO] Tổng số file JSON trên MinIO: {len(minio_files)}")

        # 3. So sánh
        missing_on_minio = local_files - minio_files
        extra_on_minio = minio_files - local_files

        print("\n--- KẾT QUẢ ĐỐI SOÁT ---")
        if not missing_on_minio:
            print("[SUCCESS] Tuyệt vời! Tất cả các file trong local đều đã có mặt trên MinIO.")
        else:
            print(f"[WARNING] Có {len(missing_on_minio)} file có ở local nhưng CHƯA có trên MinIO:")
            for f in list(missing_on_minio)[:10]: # In tối đa 10 file đầu
                print(f"   - {f}")

        if extra_on_minio:
            print(f"[INFO] Có {len(extra_on_minio)} file trên MinIO (có thể từ các lần cào trước hoặc khu vực khác).")

    except Exception as e:
        print(f"[Error] Lỗi kết nối MinIO: {e}")

if __name__ == "__main__":
    verify_sync()