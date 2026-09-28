import io
import json
import psycopg2
from minio import Minio

def transfer_minio_to_postgres():
    # 1. Kết nối MinIO client
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    bucket_name = "tripadvisor-raw-data"

    # 2. Kết nối PostgreSQL (Cấu hình thông tin database của nhóm)
    conn = psycopg2.connect(
        dbname="tripadvisor_db",       # Tên database của nhóm
        user="postgres",               # User đăng nhập postgres
        password="your_password",      # Mật khẩu database của bạn
        host="localhost",              # Host (hoặc IP container)
        port="5432"                    # Port postgres mặc định
    )
    cursor = conn.cursor()

    # 3. Tạo bảng trong PostgreSQL nếu chưa có (theo đúng cấu trúc schema chuẩn)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurant_reviews (
            review_id VARCHAR(100) PRIMARY KEY,
            restaurant_id VARCHAR(50),
            restaurant_name TEXT,
            city VARCHAR(100),
            review_text TEXT,
            rating NUMERIC(3,1),
            crawl_timestamp TIMESTAMP
        );
    """)
    conn.commit()

    try:
        # Lấy danh sách các file trong bucket của MinIO
        objects = client.list_objects(bucket_name, recursive=True)
        
        for obj in objects:
            object_name = obj.object_name
            if object_name.endswith(".json"):
                print(f"Đang xử lý và đồng bộ file từ MinIO: {object_name}")
                
                # Tải file từ MinIO vào bộ nhớ đệm
                response = client.get_object(bucket_name, object_name)
                data = json.loads(response.read().decode('utf-8'))
                response.close()
                response.release_connection()

                # 4. Insert dữ liệu vào PostgreSQL
                count_inserted = 0
                for item in data:
                    insert_query = """
                        INSERT INTO restaurant_reviews (
                            review_id, restaurant_id, restaurant_name, city, review_text, rating, crawl_timestamp
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (review_id) DO NOTHING;
                    """
                    cursor.execute(insert_query, (
                        item.get("review_id"),
                        item.get("restaurant_id"),
                        item.get("restaurant_name"),
                        item.get("city"),
                        item.get("review_text"),
                        float(item.get("rating", 5.0)),
                        item.get("crawl_timestamp")
                    ))
                    count_inserted += 1
                
                conn.commit()
                print(f"Đã đưa thành công {count_inserted} bản ghi từ file {object_name} vào PostgreSQL!")

    except Exception as e:
        conn.rollback()
        print(f"Lỗi tiến trình MinIO -> Postgres: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    transfer_minio_to_postgres()