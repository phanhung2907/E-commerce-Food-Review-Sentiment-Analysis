import requests
import pandas as pd
import time
import os
from datetime import datetime

# Cấu hình Headers chuẩn giống trình duyệt thật để tránh bị chặn
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.foody.vn/"
}

def fetch_reviews_for_restaurant(restaurant_id, max_reviews=35):
    reviews_data = []
    last_id = ""
    
    print(f"\n⏳ Đang cào dữ liệu THẬT cho Restaurant ID: {restaurant_id}...")
    api_url = "https://www.foody.vn/__get/Review/ResLoadMore"
    
    total_reviews_count = "N/A"
    
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
            response = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
            
            if response.status_code != 200:
                print(f"  -> Lỗi kết nối HTTP: {response.status_code}")
                break
                
            try:
                data = response.json()
            except Exception:
                print("  -> Phản hồi từ server không phải dạng JSON hợp lệ.")
                break
                
            # Lấy tổng số review thật từ API trả về
            if "TotalReview" in data:
                total_reviews_count = data.get("TotalReview")
            elif "totalReview" in data:
                total_reviews_count = data.get("totalReview")

            items = data.get("Items", []) or data.get("itm", [])
            
            if not items:
                print("  -> Đã cào hết toàn bộ review có sẵn của quán này.")
                break
                
            for item in items:
                if len(reviews_data) >= max_reviews:
                    break
                    
                # 1. BÊ NGUYÊN TOÀN BỘ FEATURES THẬT 100% CỦA API
                review_data = item.copy() 
                
                # 2. Chỉ đính kèm ID query và thời gian quét thực tế để không bị lẫn lộn giữa các quán
                review_data["source_system"] = "ShopeeFood/Foody"
                review_data["restaurant_id_query"] = str(restaurant_id)
                review_data["total_reviews_api"] = total_reviews_count
                review_data["crawl_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                reviews_data.append(review_data)
                
                last_id = item.get("Id", "")
                
            time.sleep(1) # Nghỉ 1 giây để không làm sập server ShopeeFood
            
        except Exception as e:
            print(f"  -> Gặp ngoại lệ: {e}")
            break
            
    print(f"✅ Hoàn tất! Lấy thành công {len(reviews_data)} reviews THẬT cho quán {restaurant_id}.")
    return reviews_data

def main():
    # Danh sách ID quán ăn THẬT mà bạn cần crawl
    target_restaurant_ids = [272138, 272139, 272140] 
    
    all_reviews = []
    for res_id in target_restaurant_ids:
        reviews = fetch_reviews_for_restaurant(res_id, max_reviews=35)
        all_reviews.extend(reviews)
        
    # Lưu kết quả
    if all_reviews:
        df = pd.DataFrame(all_reviews)
        
        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/raw_reviews.csv"
        
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Xuất file thành công! Đã lưu tổng cộng {len(df)} dòng dữ liệu THẬT vào '{output_path}'.")
    else:
        # Nếu cào thất bại, script báo lỗi chứ KHÔNG tạo dữ liệu ảo
        print("⚠️ CẢNH BÁO: Không thu thập được dữ liệu nào. Vui lòng kiểm tra lại kết nối mạng hoặc ID nhà hàng.")

if __name__ == "__main__":
    main()