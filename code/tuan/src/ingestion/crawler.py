import requests
import time
import pandas as pd
from datetime import datetime
import os

def fetch_reviews_for_restaurant(restaurant_id, target_count=100):
    api_url = "https://www.foody.vn/__get/Review/ResLoadMore"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.foody.vn/"
    }
    
    params = {
        "t": str(int(time.time() * 1000)),
        "ResId": str(restaurant_id),
        "Count": "10",
        "Type": "1",
        "isLatest": "true",
        "ExcludeIds": "",
        "LastId": ""
    }

    print(f"⏳ Đang cào tối đa {target_count} lượt review THỰC TẾ (Toàn bộ Features) cho Restaurant ID: {restaurant_id}...")
    collected_for_res = 0
    restaurant_reviews = []
    total_reviews_val = "N/A"
    city_val = "Bình Định"

    while collected_for_res < target_count:
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"  -> Lỗi kết nối API: {response.status_code}")
                break
                
            data = response.json()
            
            # Trích xuất tổng số lượng review
            if "TotalReview" in data:
                total_reviews_val = str(data.get("TotalReview"))
            elif "totalReview" in data:
                total_reviews_val = str(data.get("totalReview"))

            items = data.get('Items', []) or data.get('itm', [])
            
            if not items:
                print("  -> Đã cào hết toàn bộ review có sẵn trên hệ thống của quán này.")
                break
                
            for item in items:
                if collected_for_res >= target_count:
                    break
                    
                # 1. THÁO KHUÔN: Không giới hạn 14 trường nữa, lấy NGUYÊN BẢN toàn bộ features của API
                review = item.copy()
                
                # 2. Đính kèm thêm các thông tin quản lý chung (Metadata)
                review["source_system"] = "Foody"
                review["restaurant_id_query"] = str(restaurant_id)
                review["city_query"] = city_val
                review["total_reviews_api"] = total_reviews_val
                review["crawl_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                restaurant_reviews.append(review)
                collected_for_res += 1
                
                params["LastId"] = item.get("Id", "")
                
            time.sleep(0.5)
        except Exception as e:
            print(f"  -> Gặp ngoại lệ: {e}")
            break
            
    print(f"✅ Hoàn tất! Lấy thành công {len(restaurant_reviews)} reviews cho quán {restaurant_id}.")
    return restaurant_reviews

def main():
    # Sử dụng ID chính xác của quán trên Foody (Ví dụ: 272138)
    target_restaurant_ids = [272138] 
    all_reviews = []
    
    print("🚀 Bắt đầu khởi động bot cào dữ liệu thực tế (RAW DATA)...")
    
    for res_id in target_restaurant_ids:
        reviews = fetch_reviews_for_restaurant(res_id, target_count=100)
        all_reviews.extend(reviews)

    if all_reviews:
        # THÁO KHUÔN LÚC LƯU: Dùng Pandas để tự động bung TẤT CẢ các keys trong dict thành các cột CSV
        df = pd.DataFrame(all_reviews)
        
        os.makedirs("code/tuan/data/raw", exist_ok=True)
        output_path = "code/tuan/data/raw/raw_reviews.csv"
        
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Hoàn thành xuất sắc! Đã lưu tổng cộng {len(df)} dòng dữ liệu thô với TOÀN BỘ FEATURES tại '{output_path}'.")
    else:
        print("⚠️ CẢNH BÁO: Không thu thập được dữ liệu nào.")

if __name__ == "__main__":
    main()