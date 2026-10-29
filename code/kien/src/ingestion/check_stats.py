import os
import json
import re
import pandas as pd

# Đường dẫn đến thư mục chứa các file JSON nhà hàng
local_dir = "code/kien/data/raw/single_restaurants"
restaurant_list = []

print("Đang quét dữ liệu từ thư mục local để thống kê...")

if os.path.exists(local_dir):
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # --- LÀM SẠCH TÊN THÀNH PHỐ BẰNG REGEX ---
                    raw_city = data.get("city", "Unknown")
                    first_line = str(raw_city).split("\n")[0].strip()
                    
                    # Bỏ qua các bản ghi thuộc vùng rác hệ thống nếu còn sót
                    if "Vietnam_Subregion" in first_line:
                        continue
                        
                    cleaned = re.sub(r'^\d+\.\s*', '', first_line)
                    city = re.sub(r'\s+Restaurants.*$', '', cleaned, flags=re.IGNORECASE).strip()
                    if not city:
                        city = "Unknown"
                    # ------------------------------------------
                    
                    reviews_count = len(data.get("reviews", []))
                    rest_name = data.get("restaurant_name", "N/A")
                    
                    restaurant_list.append({
                        "restaurant_name": rest_name,
                        "city": city,
                        "reviews_count": reviews_count
                    })
            except Exception as e:
                continue

df = pd.DataFrame(restaurant_list)

if not df.empty:
    print("\n================ THỐNG KÊ TỔNG HỢP THEO KHU VỰC (ĐÃ LÀM SẠCH) ================")
    summary = df.groupby('city').agg(
        total_restaurants=('restaurant_name', 'count'),
        total_reviews=('reviews_count', 'sum')
    ).reset_index().sort_values(by='total_restaurants', ascending=False)
    
    # Hiển thị toàn bộ bảng kết quả rõ ràng
    print(summary.to_string(index=False))
else:
    print("Không tìm thấy dữ liệu hoặc thư mục trống!")