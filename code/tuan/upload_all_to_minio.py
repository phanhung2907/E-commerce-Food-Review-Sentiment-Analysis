import os
from minio import Minio
from minio.error import S3Error

# Cấu hình kết nối MinIO chuẩn từ .env
client = Minio(
    "localhost:9000",
    access_key="minioadmin", 
    secret_key="minioadmin123",
    secure=False
)

bucket_name = "food-review-data" # Đã cập nhật theo chuẩn của nhóm

def upload_to_minio():
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Đã tạo bucket: {bucket_name}")
        else:
            print(f"Bucket '{bucket_name}' đã tồn tại.")

        base_dir = r"D:\E-commerce-Food-Review-Sentiment-Analysis\code\tuan\data\raw"
        folders_to_upload = ["DL_of_Hung", "DL_of_Kien", "DL_of_Sang", "DL_of_Tuan"]

        for folder in folders_to_upload:
            folder_path = os.path.join(base_dir, folder)
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.json', '.csv')):
                        file_path = os.path.join(root, file)
                        object_name = f"{folder}/{file}"
                        
                        client.fput_object(bucket_name, object_name, file_path)
                        print(f"Đã up thành công: {object_name}")

    except S3Error as exc:
        print("Lỗi MinIO: ", exc)

if __name__ == "__main__":
    upload_to_minio()