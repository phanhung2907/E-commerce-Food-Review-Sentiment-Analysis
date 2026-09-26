import requests
import time
import json
from datetime import datetime
from pathlib import Path

def crawl_capichi_api():
    all_reviews = []
    seen_review_ids = set() # Bộ nhớ lưu trữ ID chống trùng lặp
    limit = 10
    page = 1 
    
    print("Bắt đầu khởi chạy cào API Capichi (Tonkatsu FUJIRO)...")
    
    while True:
        print(f"Đang tải dữ liệu trang {page}...")
        api_url = f"https://store.capichiapp.com/api/v106/food_booking/restaurants/capichistore00a344/review_list?page={page}&limit={limit}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://order.capichiapp.com",
            "Referer": "https://order.capichiapp.com/"
        }
        
        try:
            response = requests.post(api_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Bị chặn ở trang {page}! Mã lỗi: {response.status_code}")
                break
                
            json_data = response.json()
            reviews = json_data.get('data', [])
            
            if not reviews:
                break
                
            new_items_found = False # Cờ hiệu kiểm tra trang này có dữ liệu mới không

            print(reviews)
            break
            
            # for item in reviews:
            #     review_id = item.get('id')
                
            #     # Bắt quả tang API lặp lại dữ liệu cũ -> Bỏ qua
            #     if review_id in seen_review_ids:
            #         continue
                    
            #     seen_review_ids.add(review_id)
            #     new_items_found = True
                
            #     text = item.get('feedback', '')
            #     if not text or text.strip() == '':
            #         continue
                    
            #     all_reviews.append({
            #         "source": "Capichi",
            #         "restaurant_id": "capichistore00a344",
            #         "restaurant_name": "Tonkatsu FUJIRO Phan Ke Binh", 
            #         "restaurant_url": "https://order.capichiapp.com/vi/ha-noi/phuong-ba-dinh/restaurant/capichistore00a344",
            #         "city": "Hà Nội",
            #         "category": "Món Nhật", 
            #         "total_reviews": 6017,
            #         "restaurant_rating": 4.9,
            #         "review_id": review_id,
            #         "reviewer_id": item.get('user_id'),
            #         "review_text": text.strip(),
            #         "rating": item.get('review_score'), 
            #         "review_date": item.get('created_at'),
            #         "crawl_timestamp": datetime.now().isoformat()
            #     })
            break
                
            # Nếu quét cả trang mà không có ID nào mới, ngắt toàn bộ vòng lặp
            if not new_items_found:
                print(f"\nPhát hiện API bẫy lặp dữ liệu ở trang {page}! Đã đụng đáy thực sự.")
                break
                
            print(f" -> Cào thành công trang {page}. Tổng thu: {len(all_reviews)} records chuẩn.")
            
            page += 1 
            time.sleep(1.5) 
            
        except Exception as e:
            print(f"Lỗi hệ thống ở trang {page}: {e}")
            break
            
    return all_reviews

def save_data(data):
    if not data:
        print("Không có dữ liệu để lưu.")
        return
        
    output_dir = Path("code/tuan/data/capichi/raw/ha-noi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = output_dir / f"{date_str}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"\n CHỐT SỔ: Đã lưu thành công {len(data)} records chuẩn 14 trường tại: {file_path}")

if __name__ == "__main__":
    scraped_data = crawl_capichi_api()
    save_data(scraped_data)