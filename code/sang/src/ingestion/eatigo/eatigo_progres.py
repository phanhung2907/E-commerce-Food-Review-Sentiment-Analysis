import ijson
from minio import Minio
import psycopg2

def etl_eatigo_minio_to_postgres():
    # 1. Kết nối MinIO
    minio_client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )
    
    bucket_name = "raw-data"
    object_name = "eatigo/2026-09-28/eatigo_raw_objects_final.json"

    # 2. Kết nối PostgreSQL (Nhớ thay user/password khớp với file .env của nhóm nếu cần)
    print("🔌 Đang kết nối tới PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="food_review", 
            user="postgres",           
            password="postgres123",       
            port=5433                  
        )
        cur = conn.cursor()
        print("✅ Kết nối PostgreSQL thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối PostgreSQL: {e}")
        return

    # 3. TỰ ĐỘNG TẠO BẢNG NẾU CHƯA CÓ (Tránh lỗi relation does not exist)
    print("🛠️ Đang kiểm tra và khởi tạo các bảng chuẩn 3NF...")
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS sources (
        source_code VARCHAR(30) PRIMARY KEY,
        rating_scale_max NUMERIC(4,2)
    );

    CREATE TABLE IF NOT EXISTS restaurants (
        source_code VARCHAR(30),
        source_restaurant_id TEXT,
        name TEXT,
        url TEXT,
        city TEXT,
        address TEXT,
        category TEXT,
        location TEXT,
        avg_rating NUMERIC(4,2),
        total_reviews INTEGER,
        latitude NUMERIC(9,6),
        longitude NUMERIC(9,6),
        price_range TEXT,
        telephone TEXT,
        crawl_timestamp TIMESTAMPTZ,
        raw_object_key TEXT,
        PRIMARY KEY (source_code, source_restaurant_id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
        source_code VARCHAR(30),
        source_review_id TEXT,
        source_restaurant_id TEXT,
        reviewer_id TEXT,
        reviewer_name_raw TEXT,
        review_title TEXT,
        review_text TEXT,
        rating NUMERIC(4,2),
        review_date TIMESTAMPTZ,
        travel_date DATE,
        language VARCHAR(10),
        device_name TEXT,
        total_views INTEGER,
        total_pictures INTEGER,
        total_likes INTEGER,
        total_comments INTEGER,
        guest_count TEXT,
        visit_again TEXT,
        money_spend TEXT,
        feature_depth_status TEXT,
        PRIMARY KEY (source_code, source_review_id)
    );

    INSERT INTO sources (source_code, rating_scale_max) 
    VALUES ('eatigo', 5.0) 
    ON CONFLICT (source_code) DO NOTHING;
    """
    try:
        cur.execute(create_tables_sql)
        conn.commit()
        print("✅ Khởi tạo cấu trúc bảng thành công!")
    except Exception as e:
        print(f"❌ Lỗi tạo bảng: {e}")
        return

    # 4. Đọc streaming từ MinIO và Insert vào PostgreSQL
    print("📥 Đang stream và xử lý dữ liệu từ MinIO vào PostgreSQL...")
    try:
        response = minio_client.get_object(bucket_name, object_name)
        parser = ijson.items(response, 'item')
        
        count = 0
        for record in parser:
            product_id = str(record.get("product_id"))
            container = record.get("comment_container_raw", {})
            review = record.get("review_item_raw", {})
            
            restaurant_name = container.get("restaurant_name")
            city = container.get("city")
            
            # 4.1. Insert vào bảng restaurants
            sql_restaurant = """
                INSERT INTO restaurants (source_code, source_restaurant_id, name, city, crawl_timestamp, raw_object_key)
                VALUES ('eatigo', %s, %s, %s, NOW(), %s)
                ON CONFLICT (source_code, source_restaurant_id) DO NOTHING;
            """
            cur.execute(sql_restaurant, (product_id, restaurant_name, city, object_name))

            # 4.2. Insert vào bảng reviews
            if review and review.get("id"):
                review_id = str(review.get("id"))
                comment = review.get("comment")
                rating = review.get("rating")
                
                sql_review = """
                    INSERT INTO reviews (source_code, source_review_id, source_restaurant_id, review_text, rating)
                    VALUES ('eatigo', %s, %s, %s, %s)
                    ON CONFLICT (source_code, source_review_id) DO NOTHING;
                """
                cur.execute(sql_review, (review_id, product_id, comment, rating))
            
            count += 1
            if count % 1000 == 0:
                print(f"Đã xử lý và insert {count} records...")
                conn.commit()

        conn.commit()
        response.close()
        print(f"✨ Hoàn tất ETL từ MinIO sang PostgreSQL thành công! Tổng số records: {count}")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình ETL: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    etl_eatigo_minio_to_postgres()