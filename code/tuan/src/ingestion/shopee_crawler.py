import requests
import time
import json
import random
from datetime import datetime
from pathlib import Path
from langdetect import detect, LangDetectException

# 1. KHO USER-AGENT: Ngụy trang thành nhiều loại thiết bị và trình duyệt khác nhau
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.foody.vn/"
    }

def fetch_shopee_reviews(restaurant_id, max_reviews=500):
    reviews_data = []
    last_id = ""
    api_url = "https://www.foody.vn/__get/Review/ResLoadMore"
    total_reviews_count = None
    
    while len(reviews_data) < max_reviews:
        params = {
            "ResId": str(restaurant_id),
            "Count": "10",
            "Type": "1",
            "isLatest": "true",
            "ExcludeIds": "",
            "LastId": str(last_id)
        }
        
        try:
            # Gắn headers với User-Agent đã được xoay vòng ngẫu nhiên
            response = requests.get(api_url, params=params, headers=get_random_headers(), timeout=10)
            
            # XỬ LÝ KHI BỊ CHẶN: Trả về cờ hiệu "BLOCKED" để Master biết đường tạm nghỉ
            if response.status_code in [403, 503]:
                return "BLOCKED"
                
            if response.status_code != 200:
                break
                
            data = response.json()
            
            if "TotalReview" in data:
                total_reviews_count = data.get("TotalReview")
            elif "totalReview" in data:
                total_reviews_count = data.get("totalReview")

            items = data.get("Items", []) or data.get("itm", [])
            
            if not items:
                break
                
            for item in items:
                if len(reviews_data) >= max_reviews:
                    break
                    
                text = item.get("Description", "").strip()
                if not text:
                    continue 
                
                try:
                    language = detect(text)
                except LangDetectException:
                    language = 'unknown'

                reviews_data.append({
                    "source": "ShopeeFood",
                    "restaurant_id": restaurant_id,
                    "restaurant_name": None, 
                    "restaurant_url": f"https://www.foody.vn/ho-chi-minh/quan-{restaurant_id}",
                    "city": "Unknown",
                    "category": None, 
                    "total_reviews": total_reviews_count,
                    "restaurant_rating": None,
                    "review_id": item.get("Id"),
                    "reviewer_id": item.get("Owner", {}).get("Id") if isinstance(item.get("Owner"), dict) else None,
                    "review_text": text,
                    "language": language, 
                    "rating": item.get("AvgRating"), 
                    "review_date": item.get("CreatedOn"),
                    "crawl_timestamp": datetime.now().isoformat()
                })
                
                last_id = item.get("Id", "")
                
            # Nghỉ ngẫu nhiên khi đang lật trang bên trong 1 quán (từ 0.3s đến 1s)
            time.sleep(random.uniform(0.3, 1.0)) 
            
        except requests.exceptions.RequestException:
            break
            
    return reviews_data

def save_data(data, filename):
    if not data:
        return
        
    output_dir = Path("code/tuan/data/shopee/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"[BACKUP] Đã ghi đè an toàn {len(data)} records chuẩn 15 trường vào {file_path}")

def main_spider():
    print("[SYSTEM] Bắt đầu tiến trình cào ShopeeFood Tàng Hình (Anti-ban)...")
    
    start_id = 272000 
    end_id = 300000
    
    final_dataset = []
    scraped_ids = set()
    checkpoint_name = "shopee_checkpoint.json"
    checkpoint_file = Path("code/tuan/data/shopee/raw") / checkpoint_name
    
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                final_dataset = json.load(f)
                for item in final_dataset:
                    scraped_ids.add(item['restaurant_id'])
            print(f"[RESUME] Phục hồi thành công {len(final_dataset)} records từ ca chạy trước.")
        except Exception as e:
            print(f"[LỖI RESUME] Bắt đầu lại từ số 0: {e}")

    valid_restaurant_count = 0
    current_id = start_id
    
    while current_id <= end_id:
        if current_id in scraped_ids:
            current_id += 1
            continue
            
        # 1. GẮN RADAR: In đè lên cùng 1 dòng (dùng end='\r') để màn hình không bị trôi
        print(f"[RADAR] Đang dò tìm ID quán: {current_id}...", end="\r")
        
        reviews = fetch_shopee_reviews(current_id)
        
        if reviews == "BLOCKED":
            print(f"\n[CẢNH BÁO] Phát hiện tường lửa Foody! Tạm dừng hệ thống 2 phút để gỡ IP...")
            time.sleep(120)
            continue 
            
        if reviews:
            valid_restaurant_count += 1
            final_dataset.extend(reviews)
            scraped_ids.add(current_id)
            
            # 2. XÓA DÒNG RADAR CŨ VÀ IN KẾT QUẢ KHI TÌM THẤY QUÁN THẬT
            print(f"\n[WORKER] TÌM THẤY Quán ID {current_id}! -> Thu thập {len(reviews)} bình luận. (Tổng: {len(final_dataset)})")
            
            if valid_restaurant_count % 10 == 0:
                save_data(final_dataset, checkpoint_name)
                
        time.sleep(random.uniform(0.5, 1.5))
        current_id += 1
            
    final_filename = f"shopee_final_{datetime.now().strftime('%Y%m%d')}.json"
    save_data(final_dataset, final_filename)
    print(f"\n[HOÀN THÀNH] Đã thu hoạch xong {len(final_dataset)} records THẬT từ ShopeeFood!")

if __name__ == "__main__":
    main_spider()
    