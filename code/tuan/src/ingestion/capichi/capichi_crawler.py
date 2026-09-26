import requests
import time
import json
from datetime import datetime
from pathlib import Path
from langdetect import detect, LangDetectException

def get_all_restaurants():
    """HÀM MASTER: Tự động lùng sục ID và các trường thông tin cơ bản của quán ăn"""
    print("\n[MASTER] Đang khởi chạy hệ thống quyét ID quán ăn toàn quốc...")
    restaurants_dict = {}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/json"
    }
    
    # SỬA LẠI: Ánh xạ chính xác ID khu vực theo dữ liệu thực tế của máy chủ Capichi
    # SỬA LẠI: Quét diện rộng từ mã 1 đến 10 để vét sạch mọi khu vực của Capichi
    provinces = {
        1: "Khu vực 1",
        2: "Đà Nẵng",
        3: "Hà Nội",
        4: "Khu vực 4",
        5: "Khu vực 5",
        6: "Khu vực 6",
        7: "Khu vực 7",
        8: "Khu vực 8",
        9: "Khu vực 9",
        10: "Khu vực 10"
    }
    
    for province_id, city_name in provinces.items():
        page = 1
        print(f"\n[MASTER] Đang quét khu vực {city_name} (Mã ID: {province_id})...")
        
        while True:
            api_url = f"https://store.capichiapp.com/api/v107/food_booking/restaurants?province_id={province_id}&store_type=restaurant&page={page}&limit=50"
            
            try:
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    break
                    
                json_data = response.json()
                data = json_data.get('data', [])
                
                # Nếu API trả về rỗng (như mã 1 hôm trước), lập tức ngắt vòng lặp khu vực này
                if not data:
                    break 
                    
                new_ids = False
                for item in data:
                    store_id = item.get('id')
                    store_name = item.get('name', 'Unknown')
                    
                    cats = item.get('categories', [])
                    category_name = cats[0].get('name', 'Không xác định') if cats else 'Không xác định'
                    store_url = f"https://order.capichiapp.com/vi/restaurant/{store_id}"
                    
                    if store_id and store_id not in restaurants_dict:
                        restaurants_dict[store_id] = {
                            "name": store_name,
                            "city": city_name,
                            "category": category_name,
                            "url": store_url
                        }
                        new_ids = True
                        
                if not new_ids:
                    break
                    
                print(f" -> {city_name} - Quét xong trang {page}. Tổng ID gom được: {len(restaurants_dict)}")
                page += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"Lỗi Master tại {city_name} trang {page}: {e}")
                break
                
    return restaurants_dict

def crawl_capichi_reviews(store_id, store_info):
    """HÀM WORKER: Cào review của 1 quán, lọc NLP và ráp đủ 14 trường"""
    all_reviews = []
    seen_review_ids = set()
    limit = 10
    page = 1 
    
    while True:
        api_url = f"https://store.capichiapp.com/api/v106/food_booking/restaurants/{store_id}/review_list?page={page}&limit={limit}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Accept": "application/json",
            "Origin": "https://order.capichiapp.com",
            "Referer": "https://order.capichiapp.com/"
        }
        
        try:
            response = requests.post(api_url, headers=headers, timeout=10)
            if response.status_code != 200:
                break
                
            json_data = response.json()
            
            # Đã Bổ Sung: Trích xuất tổng review và rating tổng của quán từ API
            total_reviews = json_data.get('total_review', 0)
            avg_review = json_data.get('avg_review', 0.0)
            
            reviews = json_data.get('data', [])
            
            if not reviews:
                break
                
            new_items = False
            for item in reviews:
                review_id = item.get('id')
                if review_id in seen_review_ids:
                    continue
                    
                seen_review_ids.add(review_id)
                new_items = True
                
                text = item.get('feedback', '')
                if not text or text.strip() == '':
                    continue
                    
                # ---------------------------------------------------------
                # BỘ LỌC NLP MỚI: GIỮ LẠI TẤT CẢ VÀ DÁN NHÃN NGÔN NGỮ
                # ---------------------------------------------------------
                try:
                    # Detect sẽ trả về 'vi', 'ja', 'en', 'ko'...
                    language = detect(text)
                except LangDetectException:
                    language = 'unknown' # Nếu text toàn icon hoặc ký tự lạ
                    
                # Bổ sung trường "language" vào từ điển dữ liệu (Nâng cấp thành 15 trường)
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
                    "language": language, # Trợ thủ đắc lực cho khâu Tiền xử lý
                    "rating": item.get('review_score'), 
                    "review_date": item.get('created_at'),
                    "crawl_timestamp": datetime.now().isoformat()
                })
                
            if not new_items:
                break
                
            page += 1 
            time.sleep(1) 
            
        except Exception:
            break
            
    return all_reviews

def main_spider():
    restaurants_dict = get_all_restaurants()
    total_stores = len(restaurants_dict)
    print(f"\n[SYSTEM] Master đã chốt danh sách {total_stores} quán ăn mục tiêu.")
    
    final_dataset = []
    
    for index, (store_id, store_info) in enumerate(restaurants_dict.items(), 1):
        print(f"\n[WORKER] Đang cào quán {index}/{total_stores}: {store_info['name']}...")
        
        reviews = crawl_capichi_reviews(store_id, store_info)
        final_dataset.extend(reviews)
        
        print(f" -> Thu thập được {len(reviews)} bình luận đa ngôn ngữ. (Tổng data hiện tại: {len(final_dataset)} records).")
        if index % 10 == 0:
            save_data(final_dataset, f"capichi_checkpoint.json")
            
    save_data(final_dataset, f"capichi_final_{datetime.now().strftime('%Y%m%d')}.json")

def save_data(data, filename):
    if not data:
        return
    output_dir = Path("code/tuan/data/capichi/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[BACKUP] Đã ghi đè an toàn {len(data)} records chuẩn 14 trường vào {file_path}")

if __name__ == "__main__":
    main_spider()