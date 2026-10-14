import os
import json
import psycopg2
from psycopg2.extras import execute_values

# Cấu hình kết nối PostgreSQL chuẩn theo file .env của nhóm
DB_CONFIG = {
    "dbname": "food_review_db",
    "user": "postgres",
    "password": "postgres",
    "host": "127.0.0.1",
    "port": "5432"
}

def create_tables(cursor):
    # 1. Tạo bảng restaurants
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            restaurant_id VARCHAR(50) PRIMARY KEY,
            restaurant_name TEXT,
            city VARCHAR(100),
            restaurant_url TEXT,
            rating_value NUMERIC(3,2),
            review_count_web INT,
            latitude NUMERIC(10, 6),
            longitude NUMERIC(10, 6),
            price_range VARCHAR(50),
            serves_cuisine TEXT,
            telephone VARCHAR(50)
        );
    """)

    # 2. Tạo bảng reviews (Liên kết khóa ngoại với restaurants)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id VARCHAR(100) PRIMARY KEY,
            restaurant_id VARCHAR(50) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
            reviewer_id VARCHAR(50),
            review_title TEXT,
            review_text TEXT,
            rating NUMERIC(3,2),
            review_date DATE,
            crawl_timestamp TIMESTAMP
        );
    """)
    print("[Database] Đã tạo thành công cấu trúc bảng trong PostgreSQL.")

def run_etl_pipeline():
    local_dir = "code/kien/data/raw/single_restaurants"
    
    if not os.path.exists(local_dir):
        print(f"[Error] Không tìm thấy thư mục chứa dữ liệu: {local_dir}")
        return

    print("[ETL] Đang kết nối đến PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"[Connection Error] Không thể kết nối tới PostgreSQL: {e}")
        print("-> Hãy chắc chắn rằng container PostgreSQL trong Docker đang chạy.")
        return

    cursor = conn.cursor()

    # Tạo bảng nếu chưa tồn tại
    create_tables(cursor)
    conn.commit()

    restaurant_records = []
    review_records = []

    print("[ETL] Đang đọc và chuyển đổi dữ liệu từ các file JSON...")
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    r_id = data.get("restaurant_id")
                    r_name = data.get("restaurant_name", "N/A")
                    
                    # Làm sạch tên thành phố
                    raw_city = data.get("city", "Unknown")
                    clean_city = raw_city.split("\n")[0].replace("1. ", "").replace(" Restaurants", "").strip()
                    
                    r_url = data.get("restaurant_url", "N/A")
                    
                    metadata = data.get("metadata", {})
                    agg_rating = metadata.get("aggregateRating", {})
                    geo = metadata.get("geo", {})
                    
                    # Xử lý giá trị 'N/A' thành kiểu số hoặc None cho Database
                    rating_val = agg_rating.get("ratingValue")
                    rating_val = float(rating_val) if rating_val not in ["N/A", None, ""] else None

                    review_cnt = agg_rating.get("reviewCount")
                    review_cnt = int(review_cnt) if str(review_cnt).isdigit() else None

                    lat = geo.get("latitude")
                    lat = float(lat) if lat not in ["N/A", None, ""] else None

                    lon = geo.get("longitude")
                    lon = float(lon) if lon not in ["N/A", None, ""] else None

                    price_range = metadata.get("priceRange", "N/A")
                    cuisines = ", ".join(metadata.get("servesCuisine", [])) if isinstance(metadata.get("servesCuisine"), list) else "N/A"
                    telephone = metadata.get("telephone", "N/A")

                    # Thêm vào danh sách nhà hàng
                    restaurant_records.append((
                        r_id, r_name, clean_city, r_url, rating_val, review_cnt, lat, lon, price_range, cuisines, telephone
                    ))

                    # Thêm vào danh sách reviews thuộc nhà hàng này
                    for rev in data.get("reviews", []):
                        rev_id = rev.get("review_id")
                        rev_user = rev.get("reviewer_id", "Unknown")
                        rev_title = rev.get("review_title", "")
                        rev_text = rev.get("review_text", "")
                        
                        rev_rating = rev.get("rating")
                        rev_rating = float(rev_rating) if rev_rating not in ["N/A", None, ""] else 5.0
                        
                        rev_date = rev.get("review_date")
                        crawl_ts = rev.get("crawl_timestamp")

                        review_records.append((
                            rev_id, r_id, rev_user, rev_title, rev_text, rev_rating, rev_date, crawl_ts
                        ))
            except Exception as e:
                print(f"Lỗi xử lý file {file_name}: {e}")

    # Thực hiện Bulk Insert vào PostgreSQL bằng execute_values để tối ưu tốc độ
    print(f"[ETL] Đang ghi {len(restaurant_records)} nhà hàng và {len(review_records)} reviews vào PostgreSQL...")

    try:
        # Insert restaurants
        rest_query = """
            INSERT INTO restaurants (restaurant_id, restaurant_name, city, restaurant_url, rating_value, review_count_web, latitude, longitude, price_range, serves_cuisine, telephone)
            VALUES %s
            ON CONFLICT (restaurant_id) DO NOTHING;
        """
        execute_values(cursor, rest_query, restaurant_records)

        # Insert reviews
        rev_query = """
            INSERT INTO reviews (review_id, restaurant_id, reviewer_id, review_title, review_text, rating, review_date, crawl_timestamp)
            VALUES %s
            ON CONFLICT (review_id) DO NOTHING;
        """
        execute_values(cursor, rev_query, review_records)

        conn.commit()
        print("[SUCCESS] Hoàn thành quá trình ETL dữ liệu lên PostgreSQL thành công!")
    except Exception as e:
        conn.rollback()
        print(f"[Error] Lỗi khi ghi vào Database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_etl_pipeline()