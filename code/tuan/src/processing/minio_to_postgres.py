import os
import json
import psycopg2
from datetime import datetime
from minio import Minio
from dotenv import load_dotenv

load_dotenv()
def auto_detect_category(restaurant_name):
    """Tự động phân loại ẩm thực dựa vào từ khóa trong tên nhà hàng"""
    if not restaurant_name:
        return "Khác"
        
    name_lower = restaurant_name.lower()
    
    if any(kw in name_lower for kw in ['sushi', 'ramen', 'udon', 'don', 'izakaya', 'teppan', 'onigiri', 'tonkatsu', 'tempura', 'sashimi', 'tokyo', 'akataiyo', 'kagura']):
        return "Món Nhật Bản"
    if any(kw in name_lower for kw in ['pizza', 'burger', 'gà rán', 'fried chicken', 'fastfood', 'kfc', 'lotteria', 'popeyes', 'hot diggity dog', 'bbq chicken']):
        return "Thức Ăn Nhanh"
    if any(kw in name_lower for kw in ['thai', 'thái']):
        return "Món Thái Lan"
    if any(kw in name_lower for kw in ['ấn độ', 'maazi', 'indian']):
        return "Món Ấn Độ"
    if any(kw in name_lower for kw in ['kimbap', 'tokbokki', 'han quoc', 'hàn quốc', 'samgyetang', 'bbq', 'xoxo']):
        return "Món Hàn Quốc"
    if any(kw in name_lower for kw in ['coffee', 'cafe', 'trà sữa', 'tea', 'cha', 'jardin']):
        return "Cà phê / Trà sữa"
    if any(kw in name_lower for kw in ['bánh tráng', 'ăn vặt']):
        return "Ăn vặt"
        
    return "Món Việt Nam / Khác"
MINIO_URL = f"localhost:{os.getenv('MINIO_API_PORT', '9000')}"
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
BUCKET_NAME = "food-review-data"

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = os.getenv('POSTGRES_DB', 'food_review')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres123')

def process_and_insert(cursor, client, minio_path):
    try:
        response = client.get_object(BUCKET_NAME, minio_path)
        data = json.loads(response.read().decode('utf-8'))
        
        # Chuyển source_code thành chữ thường (BeFood -> befood) để khớp khóa ngoại
        source_code = data.get('source', 'unknown').lower() 
        restaurant = data.get('restaurant', {})
        reviews = data.get('reviews', [])
        crawl_ts = data.get('crawl_timestamp', datetime.now().isoformat())
        
        rest_id = restaurant.get('restaurant_id')
        if not rest_id:
            return

        # 1. BẢNG RESTAURANTS
        insert_rest_sql = """
            INSERT INTO restaurants (
                source_code, source_restaurant_id, name, city, address, url, crawl_timestamp, raw_object_key
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_code, source_restaurant_id) DO NOTHING;
        """
        cursor.execute(insert_rest_sql, (
            source_code, rest_id, restaurant.get('name'), restaurant.get('city'), 
            restaurant.get('address'), restaurant.get('url'), crawl_ts, minio_path
        ))

        # ================= 2. BẢNG RESTAURANT_CUISINES =================
        category_str = ""
        if len(reviews) > 0:
            category_str = reviews[0].get('category') or restaurant.get('category') or ""
            
        # Áp dụng AI phân loại tự động nếu Capichi để là "Không xác định"
        if category_str.strip().lower() == "không xác định":
            category_str = auto_detect_category(restaurant.get('name'))
            
        cuisines = [c.strip() for c in str(category_str).split(',')] if category_str else []
        
        insert_cuisine_sql = """
            INSERT INTO restaurant_cuisines (source_code, source_restaurant_id, cuisine)
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
        """
        for c in cuisines:
            if c and c.lower() != "không xác định":
                cursor.execute(insert_cuisine_sql, (source_code, rest_id, c))

        # ================= 3 & 4. BẢNG REVIEWERS VÀ REVIEWS =================
        insert_reviewer_sql = """
            INSERT INTO reviewers (source_code, reviewer_id, reviewer_name)
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
        """
        
        insert_review_sql = """
            INSERT INTO reviews (
                source_code, source_review_id, source_restaurant_id, 
                reviewer_id, reviewer_name_raw, review_title, review_text, rating, review_date, language
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_code, source_review_id) 
            DO UPDATE SET 
                review_text = EXCLUDED.review_text,
                review_date = EXCLUDED.review_date;
        """
        
        for r in reviews:
            # Bắt đa dạng các Key ID
            review_id = str(r.get('review_id') or r.get('Id') or r.get('id') or "")
            if not review_id or review_id == 'None':
                continue

            reviewer_id = r.get('reviewer_id') or r.get('UserId')
            reviewer_name = r.get('reviewer_name') or r.get('UserName') or r.get('author')

            db_reviewer_id = None
            if reviewer_id and str(reviewer_id).lower() != "null" and str(reviewer_id).strip() != "":
                db_reviewer_id = str(reviewer_id)
                cursor.execute(insert_reviewer_sql, (source_code, db_reviewer_id, str(reviewer_name)))
            else:
                reviewer_name = "Ẩn danh" 

            # Bắt đa dạng các Key Nội dung, Rating và Ngày tháng
            r_text = r.get('review_text') or r.get('Description') or r.get('text') or r.get('content') or ''
            r_rating = r.get('rating') or r.get('AvgRating') or r.get('score')
            r_date = r.get('review_date') or r.get('CreatedDate') or r.get('created_at')
            r_lang = r.get('language') or r.get('lang')

            cursor.execute(insert_review_sql, (
                source_code,
                review_id,
                rest_id,
                db_reviewer_id,
                reviewer_name if not db_reviewer_id else None,
                r.get('Title') or r.get('title'),
                r_text,
                r_rating,
                r_date,
                r_lang
            ))

        print(f"   [+] Đã cập nhật xong: {minio_path}")

    except Exception as e:
        print(f"   [-] Lỗi khi xử lý file {minio_path}: {e}")
        raise e
    finally:
        response.close()
        response.release_conn()
def main():
    print("[*] Đang khởi tạo kết nối...")
    minio_client = Minio(MINIO_URL, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        print("[+] Đã kết nối PostgreSQL thành công!")
    except Exception as e:
        print(f"[-] Không thể kết nối PostgreSQL: {e}")
        return

    print("[*] Đang quét Data Lake để lấp đầy dữ liệu còn thiếu...")
    objects = minio_client.list_objects(BUCKET_NAME, recursive=True)
    
    file_count = 0
    for obj in objects:
        minio_path = obj.object_name
        if not minio_path.endswith('.json'):
            continue
            
        file_count += 1
        try:
            process_and_insert(cursor, minio_client, minio_path)
            conn.commit() 
        except Exception:
            conn.rollback()

    cursor.close()
    conn.close()
    print(f"\n🏆 Hoàn tất! Đã cập nhật toàn diện cấu trúc 3NF cho {file_count} file JSON.")

if __name__ == "__main__":
    main()