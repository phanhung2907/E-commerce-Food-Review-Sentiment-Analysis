import requests
import time
import json
import random
from datetime import datetime
from pathlib import Path

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.foody.vn/"
    }

def fetch_foody_reviews_for_restaurant(restaurant_id, max_reviews_per_res=200):
    api_url = "https://www.foody.vn/__get/Review/ResLoadMore"
    restaurant_reviews = []
    last_id = ""
    total_reviews_val = "N/A"
    
    while len(restaurant_reviews) < max_reviews_per_res:
        params = {
            "t": str(int(time.time() * 1000)),
            "ResId": str(restaurant_id),
            "Count": "10",
            "Type": "1",
            "isLatest": "true",
            "ExcludeIds": "",
            "LastId": str(last_id)
        }
        
        try:
            response = requests.get(api_url, params=params, headers=get_random_headers(), timeout=10)
            if response.status_code in [403, 503]:
                return "BLOCKED"
            if response.status_code != 200:
                break
                
            data = response.json()
            if "TotalReview" in data:
                total_reviews_val = str(data.get("TotalReview"))
            elif "totalReview" in data:
                total_reviews_val = str(data.get("totalReview"))

            items = data.get("Items", []) or data.get("itm", [])
            if not items:
                break
                
            for item in items:
                if len(restaurant_reviews) >= max_reviews_per_res:
                    break
                
                raw_desc = item.get("Description")
                text = raw_desc.strip() if isinstance(raw_desc, str) else ""
                if not text:
                    continue

                review = item.copy()
                review["source_system"] = "Foody"
                review["restaurant_id_query"] = str(restaurant_id)
                review["city_query"] = "Bình Định"
                review["total_reviews_api"] = total_reviews_val
                review["crawl_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                restaurant_reviews.append(review)
                last_id = item.get("Id", "")
                
            time.sleep(random.uniform(0.3, 0.8))
        except requests.exceptions.RequestException:
            break
            
    return restaurant_reviews

def save_checkpoint(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    print("[SYSTEM] Bắt đầu tiến trình cào Foody tự động hướng tới mục tiêu 10.000 records...")
    
    start_id = 301000
    end_id = 400000
    target_total_goal = 100000
    
    final_dataset = []
    scraped_ids = set()
    
    output_dir = Path("code/sang/data/raw")
    checkpoint_file = output_dir / "foody_checkpoint.json"
    
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                final_dataset = json.load(f)
                for item in final_dataset:
                    scraped_ids.add(int(item.get('restaurant_id_query', 0)))
            print(f"[RESUME] Khôi phục thành công {len(final_dataset)} records từ lần chạy trước.")
        except Exception as e:
            print(f"[LỖI RESUME] Khởi động lại từ đầu: {e}")

    current_id = start_id
    valid_shops = 0
    
    while current_id <= end_id and len(final_dataset) < target_total_goal:
        if current_id in scraped_ids:
            current_id += 1
            continue
            
        print(f"[RADAR] Đang quét ID quán: {current_id} | Tổng tích lũy: {len(final_dataset)}/{target_total_goal}...", end="\r")
        
        reviews = fetch_foody_reviews_for_restaurant(current_id, max_reviews_per_res=200)
        
        if reviews == "BLOCKED":
            print(f"\n[CẢNH BÁO] Bị chặn tạm thời bởi Foody! Nghỉ ngơi 90 giây...")
            time.sleep(90)
            continue
            
        if reviews:
            valid_shops += 1
            final_dataset.extend(reviews)
            scraped_ids.add(current_id)
            print(f"\n[WORKER] TÌM THẤY Quán ID {current_id} -> Thu được {len(reviews)} review. (Tổng: {len(final_dataset)})")
            
            if valid_shops % 5 == 0:
                save_checkpoint(final_dataset, checkpoint_file)
                
        time.sleep(random.uniform(0.5, 1.2))
        current_id += 1

    if final_dataset:
        final_output_path = output_dir / "foody_raw_reviews.json"
        save_checkpoint(final_dataset, final_output_path)
        print(f"\n🎉 HOÀN THÀNH XUẤT SẮC! Đã gom đủ {len(final_dataset)} dòng tại '{final_output_path}'.")
    else:
        print("\n⚠️ Không thu thập được dữ liệu.")

if __name__ == "__main__":
    main()