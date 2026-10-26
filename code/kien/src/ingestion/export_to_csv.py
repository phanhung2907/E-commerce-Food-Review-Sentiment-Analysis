import os
import json
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(current_dir, "../../data/raw/single_restaurants")

if os.path.exists(json_dir):
    files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
    print(f"Đang quét toàn bộ {len(files)} file JSON để xuất CSV đầy đủ thông tin...")
    
    restaurant_list = []
    for filename in files:
        file_path = os.path.join(json_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Lấy thông tin chung của nhà hàng
            city = data.get("city", "N/A")
            restaurant_id = data.get("restaurant_id", "N/A")
            
            reviews = data.get("reviews", [])
            for rev in reviews:
                restaurant_list.append({
                    "source_restaurant_id": restaurant_id,
                    "city": city,  # Đã bổ sung thành công cột city
                    "rating": rev.get("rating", 5.0),
                    "review_text": rev.get("review_text", "")
                })
        except Exception as e:
            print(f"Lỗi đọc file {filename}: {e}")
            
    df = pd.DataFrame(restaurant_list)
    
    if not df.empty:
        processed_dir = os.path.join(current_dir, "../../data/processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        output_path = os.path.join(processed_dir, "data_clean.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Thành công! Đã xuất {len(df)} dòng dữ liệu (bao gồm cả cột city) vào: {output_path}")
    else:
        print("Không tìm thấy dữ liệu review!")
else:
    print(f"Không tìm thấy thư mục: {json_dir}")