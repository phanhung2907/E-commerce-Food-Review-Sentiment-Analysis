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
    client.f_object("raw-data", "foody/2026-07-20/foody_sample_data.json", "temp.json")
    
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
    cursor = conn.cursor()
    
    # Lọc và insert dữ liệu
    for item in data:
        # Thực hiện câu lệnh insert vào bảng food_reviews
        cursor.execute(
            """
            INSERT INTO food_reviews (source, restaurant_id, restaurant_name, city, total_reviews, review_id, review_text, rating, review_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                item.get("source"),
                item.get("restaurant_id"),
                item.get("restaurant_name"),
                item.get("city"),
                item.get("total_reviews"),
                item.get("review_id"),
                item.get("review_text"),
                item.get("rating"),
                item.get("review_date")
            )
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Đã nạp dữ liệu thành công!")

if __name__ == "__main__":
    main()

