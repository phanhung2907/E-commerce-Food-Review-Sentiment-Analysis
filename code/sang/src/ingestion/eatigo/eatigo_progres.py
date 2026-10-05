import json
from minio import Minio
import psycopg2


def etl_eatigo_minio_to_postgres():

    # =========================================================
    # 1. KẾT NỐI MINIO
    # =========================================================

    minio_client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False
    )

    bucket_name = "raw-data"

    # Cấu trúc mới
    prefix = "eatigo/raw/ho-chi-minh/"

    # =========================================================
    # 2. KẾT NỐI POSTGRESQL
    # =========================================================

    print("🔌 Đang kết nối tới PostgreSQL...")

    try:
        conn = psycopg2.connect(
            host="localhost",
            database="food_review",
            user="postgres",
            password="postgres123",
            port=5432
        )

        cur = conn.cursor()

        print("✅ Kết nối PostgreSQL thành công!")

    except Exception as e:
        print(f"❌ Lỗi kết nối PostgreSQL: {e}")
        return

    # =========================================================
    # 3. TẠO BẢNG
    # =========================================================

    print("🛠️ Đang kiểm tra bảng...")

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
        print("✅ Khởi tạo bảng thành công!")

    except Exception as e:
        print(f"❌ Lỗi tạo bảng: {e}")
        cur.close()
        conn.close()
        return

    # =========================================================
    # 4. LẤY DANH SÁCH restaurant.json TRONG MINIO
    # =========================================================

    print("\n📥 Đang tìm các restaurant.json trong MinIO...")

    try:

        objects = minio_client.list_objects(
            bucket_name,
            prefix=prefix,
            recursive=True
        )

        restaurant_objects = [
            obj.object_name
            for obj in objects
            if obj.object_name.endswith("/restaurant.json")
        ]

        print(
            f"🏪 Tìm thấy {len(restaurant_objects)} restaurant.json"
        )

    except Exception as e:
        print(f"❌ Lỗi đọc danh sách MinIO: {e}")
        cur.close()
        conn.close()
        return

    # =========================================================
    # 5. ĐỌC TỪNG RESTAURANT.JSON
    # =========================================================

    restaurant_count = 0
    review_count = 0

    try:

        for object_name in restaurant_objects:

            print(f"\n📂 Đang xử lý: {object_name}")

            response = None

            try:

                response = minio_client.get_object(
                    bucket_name,
                    object_name
                )

                restaurant_data = json.loads(
                    response.read().decode("utf-8")
                )

            finally:

                if response:
                    response.close()
                    response.release_conn()

            # =================================================
            # RESTAURANT ID
            # =================================================

            restaurant_info = restaurant_data.get(
                "restaurant",
                {}
            )

            if not isinstance(restaurant_info, dict):
                restaurant_info = {}

            product_id = str(
                restaurant_info.get("restaurant_id") or ""
            ).strip()

            if not product_id:
                print("⚠️ Không có restaurant_id → bỏ qua")
                continue

            # =================================================
            # RAW CONTAINER
            # =================================================

            container = restaurant_data.get(
                "comment_container_raw",
                {}
            )

            if not isinstance(container, dict):
                container = {}

            # =================================================
            # RESTAURANT DATA
            # =================================================

            restaurant_name = (
                container.get("restaurant_name")
                or container.get("name")
            )

            city = container.get("city")
            address = container.get("address")
            category = container.get("category")
            url = container.get("url")
            location = container.get("location")

            avg_rating = container.get("avg_rating")

            # =================================================
            # TOTAL REVIEWS
            # =================================================

            restaurant_tags = restaurant_data.get(
                "restaurant_tags_raw",
                {}
            )

            if not isinstance(restaurant_tags, dict):
                restaurant_tags = {}

            total_reviews = restaurant_tags.get(
                "total_reviews_count"
            )

            # =================================================
            # CRAWL TIMESTAMP
            # =================================================

            crawl_timestamp = restaurant_data.get(
                "crawl_timestamp"
            )

            # =================================================
            # INSERT / UPDATE RESTAURANT
            # =================================================

            sql_restaurant = """
                INSERT INTO restaurants (
                    source_code,
                    source_restaurant_id,
                    name,
                    url,
                    city,
                    address,
                    category,
                    location,
                    avg_rating,
                    total_reviews,
                    crawl_timestamp,
                    raw_object_key
                )
                VALUES (
                    'eatigo',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )

                ON CONFLICT (
                    source_code,
                    source_restaurant_id
                )

                DO UPDATE SET
                    name = EXCLUDED.name,
                    url = EXCLUDED.url,
                    city = EXCLUDED.city,
                    address = EXCLUDED.address,
                    category = EXCLUDED.category,
                    location = EXCLUDED.location,
                    avg_rating = EXCLUDED.avg_rating,
                    total_reviews = EXCLUDED.total_reviews,
                    crawl_timestamp = EXCLUDED.crawl_timestamp,
                    raw_object_key = EXCLUDED.raw_object_key;
            """

            cur.execute(
                sql_restaurant,
                (
                    product_id,
                    restaurant_name,
                    url,
                    city,
                    address,
                    category,
                    location,
                    avg_rating,
                    total_reviews,
                    crawl_timestamp,
                    object_name
                )
            )

            # =================================================
            # REVIEWS
            # =================================================

            reviews = restaurant_data.get(
                "reviews",
                []
            )

            if not isinstance(reviews, list):
                reviews = []

            for review in reviews:

                if not isinstance(review, dict):
                    continue

                review_id = str(
                    review.get("id") or ""
                ).strip()

                if not review_id:
                    continue

                review_text = review.get(
                    "description"
                )

                rating = review.get(
                    "rating"
                )

                reviewer_name = review.get(
                    "rated_by"
                )

                review_date = review.get(
                    "comment_time"
                )

                like_count = review.get(
                    "like_count"
                )

                # =============================================
                # INSERT REVIEW
                # =============================================

                sql_review = """
                    INSERT INTO reviews (
                        source_code,
                        source_review_id,
                        source_restaurant_id,
                        reviewer_name_raw,
                        review_text,
                        rating,
                        review_date,
                        total_likes
                    )

                    VALUES (
                        'eatigo',
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )

                    ON CONFLICT (
                        source_code,
                        source_review_id
                    )

                    DO NOTHING;
                """

                cur.execute(
                    sql_review,
                    (
                        review_id,
                        product_id,
                        reviewer_name,
                        review_text,
                        rating,
                        review_date,
                        like_count
                    )
                )

                review_count += 1

            restaurant_count += 1

            # Commit sau mỗi restaurant
            conn.commit()

            print(
                f"   ✅ Restaurant {product_id}: "
                f"{len(reviews)} reviews"
            )

        # =====================================================
        # HOÀN TẤT
        # =====================================================

        conn.commit()

        print("\n========================================")
        print("✨ ETL EATIGO HOÀN TẤT")
        print("========================================")
        print(f"🏪 Restaurants xử lý: {restaurant_count}")
        print(f"📝 Reviews xử lý: {review_count}")
        print("📦 Raw object key đã lưu theo từng restaurant")
        print("========================================")

    except Exception as e:

        conn.rollback()

        print("\n❌ LỖI TRONG QUÁ TRÌNH ETL:")
        print(e)

    finally:

        cur.close()
        conn.close()


if __name__ == "__main__":
    etl_eatigo_minio_to_postgres()