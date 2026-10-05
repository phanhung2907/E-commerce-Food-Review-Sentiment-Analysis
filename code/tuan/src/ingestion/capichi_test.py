import requests
import time
import json
from datetime import datetime
from pathlib import Path

def get_all_restaurants():
    """HÀM MASTER: Khởi chạy quét 10 quán"""
    print("\n[MASTER] Đang khởi chạy hệ thống (CHẾ ĐỘ TEST: 10 quán, CỐ TÌNH LÀM BỂ CHỮ)...")
    restaurants_dict = {}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/json"
    }
    
    provinces = {
        1: "Khu vực 1", 2: "Đà Nẵng", 3: "Hà Nội", 4: "Khu vực 4",
        5: "Khu vực 5", 6: "Khu vực 6", 7: "Khu vực 7", 8: "Khu vực 8",
        9: "Khu vực 9", 10: "Khu vực 10"
    }
    
    for province_id, city_name in provinces.items():
        page = 1
        while True:
            api_url = f"https://store.capichiapp.com/api/v107/food_booking/restaurants?province_id={province_id}&store_type=restaurant&page={page}&limit=50"
            try:
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code != 200: break
                    
                json_data = response.json()
                data = json_data.get('data', [])
                if not data: break 
                    
                new_ids = False
                for item in data:
                    store_id = item.get('id')
                    
                    if store_id and store_id not in restaurants_dict:
                        cats = item.get('categories', [])
                        restaurants_dict[store_id] = {
                            "name": item.get('name', 'Unknown'),
                            "city": city_name,
                            "category": cats[0].get('name', 'Không xác định') if cats else 'Không xác định',
                            "url": f"https://order.capichiapp.com/vi/restaurant/{store_id}"
                        }
                        new_ids = True
                        
                        # Chặn đúng 10 quán là ngắt ngay Master
                        if len(restaurants_dict) == 10:
                            print(f"\n[TEST MODE] Đã gom đủ 10 quán. Ngắt Master chuyển sang Worker.")
                            return restaurants_dict
                        
                if not new_ids: break
                page += 1
                time.sleep(1)
            except Exception:
                break
    return restaurants_dict

def crawl_capichi_reviews(store_id, store_info):
    """HÀM WORKER: Chuẩn 14 trường (Không Langdetect)"""
    all_reviews = []
    seen_review_ids = set()
    limit = 10
    page = 1 
    
    while True:
        api_url = f"https://store.capichiapp.com/api/v106/food_booking/restaurants/{store_id}/review_list?page={page}&limit={limit}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://order.capichiapp.com"
        }
        
        try:
            response = requests.post(api_url, headers=headers, timeout=10)
            if response.status_code != 200: break
                
            json_data = response.json()
            total_reviews = json_data.get('total_review', 0)
            avg_review = json_data.get('avg_review', 0.0)
            reviews = json_data.get('data', [])
            
            if not reviews: break
                
            new_items = False
            for item in reviews:
                review_id = item.get('id')
                
                if review_id in seen_review_ids: continue
                seen_review_ids.add(review_id)
                new_items = True 
                
                text = item.get('feedback', '')
                if not text or text.strip() == '': continue
                    
                all_reviews.append({
                    "source": "Capichi",
                    "restaurant_id": store_id,
                    "restaurant_name": store_info["name"], 
                    "restaurant_url": store_info["url"],
                    "city": store_info["city"],
                    "category": store_info["category"], 
                    "total_reviews": total_reviews,
                    "restaurant_rating": avg_review,
                    "review_id": review_id,
                    "reviewer_id": item.get('user_id'),
                    "review_text": text.strip(),
                    "rating": item.get('review_score'), 
                    "review_date": item.get('created_at'),
                    "crawl_timestamp": datetime.now().isoformat()
                })
                
            if not new_items: break
            page += 1 
            time.sleep(1) 
        except Exception:
            break
    return all_reviews

def main_spider():
    restaurants_dict = get_all_restaurants()
    total_stores = len(restaurants_dict)
    
    final_dataset = []
    for index, (store_id, store_info) in enumerate(restaurants_dict.items(), 1):
        print(f"\n[WORKER] Đang cào quán {index}/{total_stores}: {store_info['name']}...")
        reviews = crawl_capichi_reviews(store_id, store_info)
        final_dataset.extend(reviews)
        print(f" -> Thu thập được {len(reviews)} bình luận. (Tổng data hiện tại: {len(final_dataset)} records).")
        
    save_data(final_dataset, f"capichi_test_10_quan_be_chu.json")

def save_data(data, filename):
    if not data: return
    output_dir = Path("code/tuan/data/capichi/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    
    # [ĐÃ SỬA CỐ Ý LÀM LỖI]: Xóa encoding='utf-8' ở dòng open và xóa ensure_ascii=False ở dòng json.dump
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"\n[BACKUP] Đã ghi {len(data)} records vào {file_path} (Lưu ý: File này sẽ bị bể chữ vì không có UTF-8)")

if __name__ == "__main__":
    main_spider()