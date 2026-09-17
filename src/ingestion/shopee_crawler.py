import requests
import pandas as pd
import time
import os

# Cấu hình Headers đầy đủ như một trình duyệt Chrome thật đang truy cập
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.foody.vn/binh-dinh/pho-ga-chi-chi-dau-93",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_reviews_for_restaurant(restaurant_id, max_reviews=40):
    reviews_data = []
    last_id = ""
    
    print(f"Đang cào review cho Restaurant ID: {restaurant_id}...")
    
    while len(reviews_data) < max_reviews:
        url = f"https://www.foody.vn/__get/Review/ResLoadMore?idRes={restaurant_id}&lastId={last_id}&count=10"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code != 200:
                print(f"  -> Lỗi kết nối HTTP: {response.status_code}")
                break
                
            # Đọc trực tiếp dữ liệu dạng JSON từ phản hồi
            data = response.json()
            items = data.get("itm", [])
            
            if not items:
                print("  -> Đã cào hết toàn bộ review có sẵn.")
                break
                
            for item in items:
                review_text = item.get("Description") or item.get("Title", "")
                rating = item.get("Rating", 0.0)
                review_date = item.get("CreatedDate", "")
                
                reviews_data.append({
                    "restaurant_id": restaurant_id,
                    "review_text": review_text,
                    "rating": rating,
                    "review_date": review_date,
                    "city_id": 231 
                })
                
                last_id = item.get("Id", "")
                
            time.sleep(0.5) # Tạm dừng nửa giây giữa các lần gọi trang để an toàn
            
        except Exception as e:
            print(f"  -> Gặp ngoại lệ: {e}")
            break
        
    print(f"✅ Đã lấy thành công {len(reviews_data)} reviews cho quán {restaurant_id}.")
    return reviews_data

def main():
    # Sử dụng ID chuẩn của quán Phở Gà Chị Dậu
    target_restaurant_ids = [272138] 
    
    all_reviews = []
    for res_id in target_restaurant_ids:
        reviews = fetch_reviews_for_restaurant(res_id, max_reviews=50)
        all_reviews.extend(reviews)
        
    # Lưu kết quả ra file CSV chuẩn trong thư mục data/raw
    if all_reviews:
        df = pd.DataFrame(all_reviews)
        
        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/shopeefood_sample_reviews.csv"
        
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Hoàn thành xuất sắc! Đã lưu tổng cộng {len(df)} dòng dữ liệu vào '{output_path}'.")
    else:
        print("Không thu thập được dữ liệu nào.")

if __name__ == "__main__":
    main()