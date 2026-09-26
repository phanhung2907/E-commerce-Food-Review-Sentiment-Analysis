import requests
import json
import time
import random
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# ---------------------------------------------------------
# TÍNH NĂNG 4: GHOST MODE - DANH SÁCH NGỤY TRANG (USER-AGENTS)
# ---------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
]

# ---------------------------------------------------------
# TÍNH NĂNG 3: SMART RESUME - ĐỌC FILE BACKUP TỰ ĐỘNG
# ---------------------------------------------------------
def load_backup_data(backup_file):
    scraped_ids = set()
    existing_data = []
    if backup_file.exists():
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                for item in existing_data:
                    # Lưu lại ID quán đã cào để không cào lại
                    if item.get("restaurant_id"):
                        scraped_ids.add(str(item["restaurant_id"]))
            print(f"[SMART RESUME] Đã load thành công {len(existing_data)} records từ file backup!")
            print(f"[SMART RESUME] Nhận diện được {len(scraped_ids)} quán đã cào. Sẽ bỏ qua các quán này.")
        except Exception as e:
            print(f"[LỖI] Không thể đọc file backup: {e}")
    else:
        print("[SMART RESUME] Không tìm thấy file backup. Sẽ cào mới từ đầu.")
    return existing_data, scraped_ids

# ---------------------------------------------------------
# TÍNH NĂNG 2: AUTO-HUNTER - TRÌNH ĐÀO BỚI JSON ĐỆ QUY
# ---------------------------------------------------------
def find_reviews_in_json(node, results):
    """
    Thuật toán đệ quy đào bới mọi ngóc ngách của JSON để tìm cấu trúc bình luận.
    Giúp code không bị gãy ngay cả khi BeFood thay đổi giao diện.
    """
    if isinstance(node, dict):
        # Đặc điểm nhận dạng bình luận của BeFood thường có các key này
        if ("comment" in node or "content" in node) and ("rating" in node or "score" in node):
            results.append(node)
        for key, value in node.items():
            find_reviews_in_json(value, results)
    elif isinstance(node, list):
        for item in node:
            find_reviews_in_json(item, results)

# ---------------------------------------------------------
# TÍNH NĂNG 1 & 5: SSR EXTRACTOR & CHECKPOINT
# ---------------------------------------------------------
def save_data(data, filename):
    output_dir = Path("code/tuan/data/befood/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[CHECKPOINT] Đã bảo vệ an toàn {len(data)} records chuẩn NLP vào {file_path}")

def crawl_befood_restaurant(restaurant_id):
    # BeFood thường chấp nhận cấu trúc URL có ID ở cuối dù tên slug (phần chữ) không chính xác
    url = f"https://food.be.com.vn/ho-chi-minh/quan-an-{restaurant_id}"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
            
        # TÍNH NĂNG 1: Dùng BeautifulSoup Nội soi HTML tìm Next.js Data
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return []
            
        # Giải mã JSON ẩn
        raw_json = json.loads(next_data_script.string)
        
        # Gọi trình đào bới đệ quy
        raw_reviews = []
        find_reviews_in_json(raw_json, raw_reviews)
        
        # Chuyển đổi sang chuẩn 15 trường NLP của dự án
        nlp_records = []
        for rv in raw_reviews:
            text = rv.get('comment') or rv.get('content') or ""
            if not text.strip(): # Bỏ qua nếu không có chữ (chỉ chấm điểm)
                continue
                
            record = {
                "source": "beFood",
                "restaurant_id": restaurant_id,
                "restaurant_name": f"BeFood Restaurant {restaurant_id}", # Next.js giấu tên quán ở chỗ khác, dùng tạm ID
                "restaurant_url": url,
                "city": "ho-chi-minh",
                "category": None,
                "total_reviews": None,
                "reviewer_id": rv.get('user_id') or rv.get('id'),
                "review_text": text,
                "language": "vi",
                "rating": rv.get('rating') or rv.get('score'),
                "review_date": rv.get('created_at') or rv.get('date'),
                "crawl_timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            nlp_records.append(record)
            
        return nlp_records
        
    except Exception as e:
        print(f"[LỖI] Dò ID {restaurant_id} thất bại: {e}")
        return []

def main_spider():
    print("[SYSTEM] Khởi động Siêu Robot cào BeFood (Phiên bản Next.js SSR)...")
    
    # 1. Khôi phục vốn cũ từ file backup
    backup_path = Path("code/tuan/data/befood/raw/befood_backup_3k.json")
    final_dataset, scraped_ids = load_backup_data(backup_path)
    
    # 2. Cấu hình dải ID dò tìm (BeFood thường có mã từ 110.000 đến 130.000)
    start_id = 116000
    end_id = 130000
    
    checkpoint_name = "befood_checkpoint.json"
    valid_restaurant_count = 0
    
    print(f"\n[RADAR] Bắt đầu rà quét dải ID từ {start_id} đến {end_id}...")
    
    for current_id in range(start_id, end_id):
        # Bỏ qua nếu quán này đã nằm trong file backup 3k
        if str(current_id) in scraped_ids:
            continue
            
        print(f"[RADAR] Đang nội soi ID quán: {current_id}...", end='\r')
        
        reviews = crawl_befood_restaurant(current_id)
        
        if reviews:
            valid_restaurant_count += 1
            final_dataset.extend(reviews)
            scraped_ids.add(str(current_id))
            
            print(f"\n[WORKER] TÌM THẤY Quán {current_id}! -> Lấy được {len(reviews)} bình luận. (Tổng kho: {len(final_dataset)})")
            
            # TÍNH NĂNG 5: Checkpoint - Cứ 10 quán thật là lưu 1 lần
            if valid_restaurant_count % 10 == 0:
                save_data(final_dataset, checkpoint_name)
                
        # TÍNH NĂNG 4: Ngủ đông ngẫu nhiên 1 - 2 giây để chống Block IP
        time.sleep(random.uniform(1.0, 2.0))

    # Khi quét xong toàn bộ, lưu thành file chung cuộc
    final_filename = f"befood_final_{datetime.now().strftime('%Y%m%d')}.json"
    save_data(final_dataset, final_filename)
    print(f"\n[HOÀN THÀNH] Đã thu hoạch xong {len(final_dataset)} records THẬT từ BeFood!")

if __name__ == "__main__":
    main_spider()