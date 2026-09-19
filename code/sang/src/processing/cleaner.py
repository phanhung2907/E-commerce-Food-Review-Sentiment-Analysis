import json
from minio import Minio
import psycopg2

def main():
    print("🚀 Đang tải dữ liệu từ MinIO...")
    
    # 1. Kết nối MinIO trực tiếp
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )
    
    # Tải file JSON từ MinIO về máy làm file tạm
    client.fget_object("raw-data", "foody/2026-07-20/foody_sample_data.json", "temp.json")

    # 2. Đọc dữ liệu từ file tạm
    with open("temp.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"🧹 Đang nạp {len(data)} dòng vào PostgreSQL...")

    # 3. Kết nối PostgreSQL trực tiếp
    conn = psycopg2.connect(
        host="localhost",
        database="food_review", # Tên database của nhóm
        user="postgres",
        password="your_password" # Thay mật khẩu của bạn vào đây
    )
    cur = conn.cursor()

    # 4. Đẩy từng dòng dữ liệu vào bảng
    for item in data:
        cur.execute(
            """
            INSERT INTO food_reviews (restaurant_name, review_text, rating) 
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (
                item.get('restaurant_name'), 
                item.get('review_text'), 
                item.get('rating')
            )
        )
    
    # Lưu thay đổi và đóng kết nối
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Hoàn tất! Dữ liệu đã được nạp thẳng vào PostgreSQL.")

if __name__ == "__main__":
    main()