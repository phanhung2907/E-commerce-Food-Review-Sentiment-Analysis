import os
import pandas as pd
import psycopg2
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# --- CẤU HÌNH POSTGRESQL ---
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "food_review")
db_user = os.getenv("DB_USER", "postgres")
db_pass = "postgres123"  # Mật khẩu PostgreSQL của bạn
db_port = os.getenv("DB_PORT", "5432")

# --- CẤU HÌNH MINIO ---
minio_endpoint = "http://localhost:9000"
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
bucket_name = "raw-data"  # Tên bucket chứa dữ liệu thô trên MinIO

def upload_to_minio(file_path):
    try:
        # Khởi tạo S3 client kết nối với MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=minio_endpoint,
            aws_access_key_id=minio_access_key,
            aws_secret_access_key=minio_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )

        # Kiểm tra và tạo bucket nếu chưa tồn tại
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"📦 Đã tạo mới MinIO bucket: '{bucket_name}'")

        # Upload file CSV lên MinIO
        object_name = "raw_reviews.csv"
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"☁️ Đã upload thành công file lên MinIO bucket '{bucket_name}/{object_name}'")

    except Exception as e:
        print(f"⚠️ Lỗi kết nối hoặc upload lên MinIO: {e}")

def main():
    file_path = "data/raw/raw_reviews.csv"
    if not os.path.exists(file_path):
        print("❌ Không tìm thấy file dữ liệu thô tại data/raw/raw_reviews.csv!")
        return

    df = pd.read_csv(file_path)
    print(f"📊 Đã đọc thành công {len(df)} dòng dữ liệu từ file CSV.")

    # 1. Xử lý lưu vào PostgreSQL
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port=db_port
        )
        cursor = conn.cursor()
        print("✅ Kết nối PostgreSQL thành công!")

        # Tự động tạo bảng nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_reviews (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50),
                restaurant_id VARCHAR(50),
                restaurant_name VARCHAR(255),
                restaurant_url TEXT,
                city VARCHAR(100),
                category VARCHAR(100),
                review_id VARCHAR(50),
                review_text TEXT,
                rating NUMERIC,
                review_date VARCHAR(50),
                reviewer_id VARCHAR(50),
                total_reviews VARCHAR(50),
                restaurant_rating VARCHAR(50),
                crawl_timestamp VARCHAR(50)
            );
        """)
        conn.commit()

        # Insert dữ liệu
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO raw_reviews (
                    source, restaurant_id, restaurant_name, restaurant_url, 
                    city, category, review_id, review_text, rating, 
                    review_date, reviewer_id, total_reviews, restaurant_rating, crawl_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                str(row.get("source", "")), str(row.get("restaurant_id", "")), 
                str(row.get("restaurant_name", "")), str(row.get("restaurant_url", "")),
                str(row.get("city", "")), str(row.get("category", "")), 
                str(row.get("review_id", "")), str(row.get("review_text", "")), 
                float(row["rating"]) if pd.notnull(row.get("rating")) else 0.0,
                str(row.get("review_date", "")), str(row.get("reviewer_id", "")), 
                str(row.get("total_reviews", "")), str(row.get("restaurant_rating", "")), 
                str(row.get("crawl_timestamp", ""))
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("🎉 Đã đẩy toàn bộ 100 dòng dữ liệu thành công vào PostgreSQL!")

    except Exception as e:
        print(f"⚠️ Lỗi PostgreSQL: {e}")

    # 2. Xử lý đẩy file lên MinIO
    upload_to_minio(file_path)

if __name__ == "__main__":
    main()