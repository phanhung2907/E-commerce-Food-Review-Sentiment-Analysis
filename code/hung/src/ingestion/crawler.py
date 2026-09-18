import requests
import time
import csv

def main() -> None:
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

    print("Đang khởi động bot... Mục tiêu: 100 bình luận!")
    
    total_collected = 0
    target = 100
    
    # Tạo một danh sách rỗng để gom dữ liệu
    all_reviews = []
    
    while total_collected < target:
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("Items", [])
            
            if not items:
                break
                
            for item in items:
                total_collected += 1
                rating = item.get("AvgRating")
                comment = item.get("Description", item.get("Title"))
                
                # Cất từng bình luận vào danh sách thay vì chỉ in ra
                all_reviews.append({
                    "STT": total_collected,
                    "Rating": rating,
                    "Comment": comment
                })
                
                print(f"Đang tải: [{total_collected}/100]...")
                
                if total_collected >= target:
                    break
            
            last_item = items[-1]
            params["LastId"] = str(last_item.get("Id", ""))
            
            time.sleep(1)
        else:
            print(f"Lỗi kết nối! Mã lỗi: {response.status_code}")
            break

    # --- PHẦN MỚI: LƯU DỮ LIỆU RA FILE CSV ---
    print("\nĐã tải xong! Đang tiến hành lưu file...")
    
    # Đường dẫn lưu file vào thư mục data
    file_path = "data/raw_reviews.csv"
    
    # Ghi dữ liệu vào file
    with open(file_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["STT", "Rating", "Comment"])
        writer.writeheader()
        writer.writerows(all_reviews)
        
    print(f"🎉 Tuyệt vời! Bạn đã lưu thành công 100 bình luận vào file: {file_path}")

if __name__ == "__main__":
    main()