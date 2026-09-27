import os
import json
import psycopg2
import uuid
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

# Thông số MinIO
MINIO_URL = f"localhost:{os.getenv('MINIO_API_PORT', '9000')}"
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
BUCKET_NAME = "food-review-data"

# Thông số PostgreSQL
DB_HOST = "localhost"
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'food_sentiment_db')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres')

def process_and_insert(minio_object_path):
    print(f"[*] Đang tải {minio_object_path} từ MinIO...")
    client = Minio(MINIO_URL, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
    response = client.get_object(BUCKET_NAME, minio_object_path)
    raw_data = json.loads(response.read().decode('utf-8'))
    response.close()
    response.release_conn()
    
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
    cursor = conn.cursor()
    
    # 1. Khởi tạo bảng từ file init_schema.sql
    print("[*] Đang kiểm tra và khởi tạo bảng từ init_schema.sql...")
    try:
        with open("code/tuan/src/storage/init_schema.sql", "r", encoding="utf-8") as f:
            schema_sql = f.read()
            cursor.execute(schema_sql)
            conn.commit()
    except Exception as e:
        print(f"[CẢNH BÁO] Không thể chạy file schema: {e}")
        conn.rollback()

    # 2. KHAI BÁO CÂU LỆNH SQL (Phần bạn bị xóa mất)
    insert_restaurant = """
        INSERT INTO restaurants (restaurant_id, restaurant_name, restaurant_url)
        VALUES (%s, %s, %s)
        ON CONFLICT (restaurant_id) DO NOTHING;
    """
    
    insert_review = """
        INSERT INTO reviews (review_id, restaurant_id, source, review_text, rating, crawl_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (review_id) DO NOTHING;
    """
    
    # 3. Lặp và chèn dữ liệu
    count = 0
    for item in raw_data:
        try:
            cursor.execute(insert_restaurant, (
                item.get('restaurant_id'),
                item.get('restaurant_name'),
                item.get('restaurant_url')
            ))
            
            rev_id = str(uuid.uuid4())
            cursor.execute(insert_review, (
                rev_id,
                item.get('restaurant_id'),
                item.get('source'),
                item.get('review_text'),
                item.get('rating'),
                item.get('crawled_at')
            ))
            count += 1
        except Exception as e:
            conn.rollback() # Tránh lỗi "current transaction is aborted" hàng loạt
            print(f"Lỗi dòng dữ liệu: {e}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print(f"🏆 [THÀNH CÔNG] Đã lưu {count} reviews từ MinIO vào bảng PostgreSQL chuẩn 3NF.")

if __name__ == "__main__":
    import datetime
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    # Lưu ý: Cần chạy file raw_to_minio.py trước để file này có sẵn trên MinIO
    process_and_insert(f"raw/befood/{date_str}/restaurant_9965.json")