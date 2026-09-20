import json
from minio import Minio
import psycopg2

def main():
    print("🚀 Đang tải file JSON từ MinIO...")
    
    # 1. Kết nối MinIO trực tiếp
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )
    
    bucket_name = "raw-data"
    object_name = "foody/2026-07-20/foody_sample_data.json"
    temp_file = "temp_foody.json"
    
    # Sử dụng đúng hàm fget_object của MinIO
    client.fget_object(bucket_name, object_name, temp_file)
    print("✅ Đã tải file tạm thành công từ MinIO.")
    
    # 2. Đọc dữ liệu từ file tạm
    with open(temp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not data:
        print("⚠️ File JSON trống!")
        return
        
    print(f"🧹 Đang xử lý và nạp động {len(data)} dòng dữ liệu với tất cả features mới vào PostgreSQL...")
    
    # 3. Kết nối PostgreSQL chính xác với thông tin từ file .env
    conn = psycopg2.connect(
        host="localhost",
        port=5433,                # Cổng Docker map ra ngoài
        database="food_review",   # Lấy từ POSTGRES_DB
        user="postgres",          # Lấy từ POSTGRES_USER
        password="postgres123"    # Lấy từ POSTGRES_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # 4. Tự động lấy tất cả các keys từ file JSON để làm tên cột INSERT động
    sample_item = data[0]
    columns = list(sample_item.keys())
    
    col_names = ", ".join([f'"{col}"' for col in columns])
    placeholders = ", ".join(["%s"] * len(columns))
    
    insert_query = f"""
        INSERT INTO food_reviews ({col_names})
        VALUES ({placeholders})
    """
    
    # Duyệt và insert từng dòng dữ liệu đầy đủ features
    for item in data:
        values = [item.get(col) for col in columns]
        cursor.execute(insert_query, values)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Đã nạp toàn bộ dữ liệu đầy đủ features mới vào PostgreSQL thành công!")

if __name__ == "__main__":
    main()