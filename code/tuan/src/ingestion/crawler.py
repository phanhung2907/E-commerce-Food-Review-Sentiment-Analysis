import requests
import time
import csv
from datetime import datetime

def main():
    api_url = "https://www.foody.vn/__get/Review/ResLoadMore"
    params = {
        "t": "1789607109005",
        "ResId": "272138",
        "Count": "10",
        "Type": "1",
        "isLatest": "true",
        "ExcludeIds": "",
        "LastId": ""
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    print("Đang khởi động bot... Mục tiêu: 100 bình luận")
    total_collected = 0
    target = 100
    all_reviews = []

    while total_collected < target:
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # API Foody thường trả về danh sách review trong key 'Items'
            items = data.get('Items', [])
            
            if not items:
                print("Không còn dữ liệu để lấy.")
                break
                
            for item in items:
                if total_collected >= target:
                    break
                    
                # Mapping chuẩn xác theo 14 fields trong WEEK_2_PLAN_Food_Review_Sentiment_Analysis.md
                review = {
                    "source": "Foody",
                    "restaurant_id": params["ResId"],
                    "restaurant_name": "N/A", # Có thể bổ sung nếu lấy được thêm từ API chi tiết quán
                    "restaurant_url": "N/A",
                    "city": "N/A",
                    "category": "N/A",
                    "review_id": item.get("Id", ""),
                    "review_text": item.get("Description", ""),
                    "rating": item.get("Rating", ""),
                    "review_date": item.get("CreatedOn", ""),
                    "reviewer_id": item.get("Owner", {}).get("Id", "") if isinstance(item.get("Owner"), dict) else "",
                    "total_reviews": "",
                    "restaurant_rating": "",
                    "crawl_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                all_reviews.append(review)
                total_collected += 1
                
                # Lưu LastId để API trả về các review tiếp theo ở request sau
                params["LastId"] = item.get("Id", "")
            
            print(f"Đã lấy được {total_collected}/{target} reviews...")
            time.sleep(2) # Tránh bị block do gửi request quá nhanh
        else:
            print(f"Lỗi kết nối API: {response.status_code}")
            break

    # Ghi dữ liệu ra file CSV theo đúng thứ tự các trường yêu cầu
    fields = [
        "source", "restaurant_id", "restaurant_name", "restaurant_url", 
        "city", "category", "review_id", "review_text", "rating", 
        "review_date", "reviewer_id", "total_reviews", "restaurant_rating", "crawl_timestamp"
    ]
    
    # Lưu file ra thư mục data/raw/
    output_path = "../../data/raw/raw_reviews.csv"
    with open(output_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_reviews)
        
    print(f"Đã hoàn thành! Lưu dữ liệu tại {output_path}")

if __name__ == "__main__":
    main()