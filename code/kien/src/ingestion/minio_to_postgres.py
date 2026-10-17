import os
import json
import psycopg2
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "food_review_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

LOCAL_DIR = "code/kien/data/raw/single_restaurants"

def safe_str(val):
    """Hàm phụ trợ ép mọi kiểu dữ liệu (dict, list, None) thành string an toàn"""
    if val is None:
        return "N/A"
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return str(val)

def init_3nf_database(cursor):
    """Xóa và khởi tạo lại cấu trúc 7 bảng chuẩn 3NF trong PostgreSQL"""
    print("[Database] Đang làm mới cấu trúc 7 bảng chuẩn 3NF...")
    
    # Drop các bảng cũ theo thứ tự ràng buộc khóa ngoại CASCADE
    cursor.execute("DROP TABLE IF EXISTS review_tags CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS reviews CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS reviewers CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS restaurant_cuisines CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS restaurant_opening_hours CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS restaurants CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS sources CASCADE;")

    # 1. Bảng sources
    cursor.execute("""
        CREATE TABLE sources (
            source_id SERIAL PRIMARY KEY,
            source_name VARCHAR(100) UNIQUE NOT NULL,
            max_rating DECIMAL(3, 1) DEFAULT 5.0
        );
    """)

    # 2. Bảng restaurants
    cursor.execute("""
        CREATE TABLE restaurants (
            restaurant_id VARCHAR(50) PRIMARY KEY,
            restaurant_name TEXT NOT NULL,
            city VARCHAR(100),
            restaurant_url TEXT,
            address TEXT,
            latitude TEXT,
            longitude TEXT,
            image TEXT,
            price_range VARCHAR(100),
            telephone VARCHAR(100),
            aggregate_rating_value DECIMAL(3,1),
            aggregate_review_count INT,
            source_id INT REFERENCES sources(source_id)
        );
    """)

    # 3. Bảng restaurant_opening_hours
    cursor.execute("""
        CREATE TABLE restaurant_opening_hours (
            hour_id SERIAL PRIMARY KEY,
            restaurant_id VARCHAR(50) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
            opening_hours_spec TEXT
        );
    """)

    # 4. Bảng restaurant_cuisines
    cursor.execute("""
        CREATE TABLE restaurant_cuisines (
            cuisine_id SERIAL PRIMARY KEY,
            restaurant_id VARCHAR(50) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
            cuisine_name VARCHAR(255)
        );
    """)

    # 5. Bảng reviewers
    cursor.execute("""
        CREATE TABLE reviewers (
            reviewer_id VARCHAR(100) PRIMARY KEY,
            reviewer_name VARCHAR(255)
        );
    """)

    # 6. Bảng reviews
    cursor.execute("""
        CREATE TABLE reviews (
            review_id VARCHAR(100) PRIMARY KEY,
            restaurant_id VARCHAR(50) REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
            reviewer_id VARCHAR(100) REFERENCES reviewers(reviewer_id),
            review_title TEXT,
            review_text TEXT,
            rating DECIMAL(3,1),
            review_date DATE,
            travel_date VARCHAR(50),
            crawl_timestamp TIMESTAMP
        );
    """)

    # 7. Bảng review_tags
    cursor.execute("""
        CREATE TABLE review_tags (
            tag_id SERIAL PRIMARY KEY,
            review_id VARCHAR(100) REFERENCES reviews(review_id) ON DELETE CASCADE,
            tag_name VARCHAR(255)
        );
    """)
    print("[Database] Đã tạo mới thành công toàn bộ 7 bảng 3NF!")

def run_3nf_etl_pipeline():
    if not os.path.exists(LOCAL_DIR):
        print(f"[Error] Không tìm thấy thư mục local: {LOCAL_DIR}")
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        print("[ETL] Đã kết nối thành công đến PostgreSQL!")
    except Exception as e:
        print(f"[Error] Lỗi kết nối database: {e}")
        return

    # Khởi tạo lại schema 3NF chuẩn
    init_3nf_database(cursor)
    conn.commit()

    # Thêm sẵn source mặc định 'TripAdvisor'
    cursor.execute("""
        INSERT INTO sources (source_name, max_rating) 
        VALUES ('TripAdvisor', 5.0) 
        ON CONFLICT (source_name) DO NOTHING;
    """)
    cursor.execute("SELECT source_id FROM sources WHERE source_name = 'TripAdvisor';")
    source_id = cursor.fetchone()[0]
    conn.commit()

    files = [f for f in os.listdir(LOCAL_DIR) if f.endswith(".json")]
    total_files = len(files)
    print(f"[ETL] Bắt đầu xử lý và nạp dữ liệu từ {total_files} file JSON vào mô hình 3NF...")

    restaurant_count = 0
    review_count_total = 0

    for idx, filename in enumerate(files):
        file_path = os.path.join(LOCAL_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            rest_id = safe_str(data.get("restaurant_id"))
            rest_name = safe_str(data.get("restaurant_name", "N/A"))
            city = safe_str(data.get("city", "N/A"))
            rest_url = safe_str(data.get("restaurant_url", "N/A"))
            
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            address = safe_str(metadata.get("address", "N/A"))
            
            geo = metadata.get("geo", {})
            if not isinstance(geo, dict):
                geo = {}
            lat = safe_str(geo.get("latitude", "N/A"))
            lon = safe_str(geo.get("longitude", "N/A"))
            
            image = safe_str(metadata.get("image", "N/A"))
            price_range = safe_str(metadata.get("priceRange", "N/A"))
            telephone = safe_str(metadata.get("telephone", "N/A"))

            agg_rating = metadata.get("aggregateRating", {})
            if not isinstance(agg_rating, dict):
                agg_rating = {}
            
            try:
                rating_val = float(str(agg_rating.get("ratingValue", 5.0)).replace(",", ""))
            except:
                rating_val = 5.0

            try:
                review_cnt = int(str(agg_rating.get("reviewCount", 0)).replace(",", ""))
            except:
                review_cnt = 0

            # 1. Insert Restaurant
            cursor.execute("""
                INSERT INTO restaurants (
                    restaurant_id, restaurant_name, city, restaurant_url, 
                    address, latitude, longitude, image, price_range, 
                    telephone, aggregate_rating_value, aggregate_review_count, source_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (restaurant_id) DO UPDATE SET
                    restaurant_name = EXCLUDED.restaurant_name,
                    city = EXCLUDED.city,
                    address = EXCLUDED.address,
                    aggregate_rating_value = EXCLUDED.aggregate_rating_value,
                    aggregate_review_count = EXCLUDED.aggregate_review_count;
            """, (rest_id, rest_name, city, rest_url, address, lat, lon, image, price_range, telephone, rating_val, review_cnt, source_id))
            restaurant_count += 1

            # 2. Insert Opening Hours (nếu có)
            opening_hours = metadata.get("openingHoursSpecification")
            if opening_hours and opening_hours != "N/A":
                if isinstance(opening_hours, list):
                    for oh in opening_hours:
                        cursor.execute("""
                            INSERT INTO restaurant_opening_hours (restaurant_id, opening_hours_spec)
                            VALUES (%s, %s);
                        """, (rest_id, safe_str(oh)))
                else:
                    cursor.execute("""
                        INSERT INTO restaurant_opening_hours (restaurant_id, opening_hours_spec)
                        VALUES (%s, %s);
                    """, (rest_id, safe_str(opening_hours)))

            # 3. Insert Cuisines (nếu có)
            cuisines = metadata.get("servesCuisine")
            if cuisines and cuisines != "N/A":
                if isinstance(cuisines, list):
                    for cuisine in cuisines:
                        cursor.execute("""
                            INSERT INTO restaurant_cuisines (restaurant_id, cuisine_name)
                            VALUES (%s, %s);
                        """, (rest_id, safe_str(cuisine)))
                else:
                    cursor.execute("""
                        INSERT INTO restaurant_cuisines (restaurant_id, cuisine_name)
                        VALUES (%s, %s);
                    """, (rest_id, safe_str(cuisines)))

            # 4. Insert Reviewers & Reviews
            reviews = data.get("reviews", [])
            if isinstance(reviews, list):
                for rev in reviews:
                    if not isinstance(rev, dict):
                        continue
                    rev_id = safe_str(rev.get("review_id"))
                    reviewer_id = safe_str(rev.get("reviewer_id", f"User_{rest_id}"))
                    reviewer_name = safe_str(rev.get("reviewer_name", "Anonymous"))
                    rev_title = safe_str(rev.get("review_title", ""))
                    rev_text = safe_str(rev.get("review_text", ""))
                    
                    try:
                        r_score = float(str(rev.get("rating", 5.0)))
                    except:
                        r_score = 5.0
                    
                    rev_date = rev.get("review_date", None)
                    if rev_date == "N/A":
                        rev_date = None
                        
                    travel_date = safe_str(rev.get("travel_date", "Recent"))
                    crawl_ts = rev.get("crawl_timestamp", None)

                    # Insert Reviewer
                    cursor.execute("""
                        INSERT INTO reviewers (reviewer_id, reviewer_name)
                        VALUES (%s, %s)
                        ON CONFLICT (reviewer_id) DO NOTHING;
                    """, (reviewer_id, reviewer_name))

                    # Insert Review
                    cursor.execute("""
                        INSERT INTO reviews (
                            review_id, restaurant_id, reviewer_id, review_title, 
                            review_text, rating, review_date, travel_date, crawl_timestamp
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (review_id) DO NOTHING;
                    """, (rev_id, rest_id, reviewer_id, rev_title, rev_text, r_score, rev_date, travel_date, crawl_ts))
                    review_count_total += 1

            conn.commit()
            if (idx + 1) % 500 == 0:
                print(f" -> Đã xử lý xong {idx + 1}/{total_files} nhà hàng...")

        except Exception as e:
            conn.rollback()
            print(f" [Error] Lỗi ở file {filename}: {e}")

    cursor.close()
    conn.close()
    print(f"\n[SUCCESS] Hoàn thành ETL mô hình 3NF đầy đủ!")
    print(f" - Tổng nhà hàng đã nạp: {restaurant_count}")
    print(f" - Tổng reviews đã nạp: {review_count_total}")

if __name__ == "__main__":
    run_3nf_etl_pipeline()