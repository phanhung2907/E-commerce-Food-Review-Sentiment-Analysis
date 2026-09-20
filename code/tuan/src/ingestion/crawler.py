import requests
import time
import csv
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

    print(f"⏳ Đang cào tối đa {target_count} lượt review thực tế cho Restaurant ID: {restaurant_id}...")
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
            
            # Trích xuất tổng số lượng review của quán từ JSON trả về
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
                    
                # Bóc tách đầy đủ các trường thông tin theo đúng yêu cầu
                review_text = item.get("Description", "") or item.get("Title", "")
                rating = item.get("Rating", "")
                review_date = item.get("CreatedOn", "") or item.get("CreatedDate", "")
                reviewer_id = item.get("Owner", {}).get("Id", "") if isinstance(item.get("Owner"), dict) else ""
                res_name = item.get("ResName", f"Restaurant {restaurant_id}")
                restaurant_rating = item.get("AvgRating", "")

                review = {
                    "source": "Foody",
                    "restaurant_id": str(restaurant_id),
                    "restaurant_name": res_name,
                    "restaurant_url": f"https://www.foody.vn/binh-dinh/restaurant-{restaurant_id}",
                    "city": city_val,
                    "category": "Food/Drink",
                    "review_id": item.get("Id", ""),
                    "review_text": review_text,
                    "rating": rating,
                    "review_date": review_date,
                    "reviewer_id": str(reviewer_id),
                    "total_reviews": total_reviews_val,
                    "restaurant_rating": restaurant_rating,
                    "crawl_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
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
    # Sử dụng ID chính xác của quán trên Foody (Ví dụ: 272138) với mục tiêu lấy đủ 100 lượt
    target_restaurant_ids = [272138] 
    all_reviews = []
    
    print("🚀 Bắt đầu khởi động bot cào dữ liệu thực tế từ ShopeeFood/Foody...")
    
    for res_id in target_restaurant_ids:
        reviews = fetch_reviews_for_restaurant(res_id, target_count=100)
        all_reviews.extend(reviews)

    # Khai báo chuẩn hóa đúng 14 trường dữ liệu theo sơ đồ thiết kế đồ án
    fields = [
        "source", "restaurant_id", "restaurant_name", "restaurant_url", 
        "city", "category", "review_id", "review_text", "rating", 
        "review_date", "reviewer_id", "total_reviews", "restaurant_rating", "crawl_timestamp"
    ]
    
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/raw_reviews.csv"
    
    with open(output_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_reviews)
        
    print(f"\n🎉 Hoàn thành xuất sắc! Đã lưu tổng cộng {len(all_reviews)} dòng dữ liệu thực tế đủ các trường tại '{output_path}'.")

if __name__ == "__main__":
    main()