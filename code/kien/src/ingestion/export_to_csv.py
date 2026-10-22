import os
import json
import pandas as pd

# Tự động định vị đường dẫn tuyệt đối
current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(current_dir, "../../data/raw/single_restaurants")

restaurant_list = []

print("Đang quét và trích xuất dữ liệu từ các file JSON...")
if os.path.exists(json_dir):
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Lấy danh sách reviews từ file JSON
                    reviews = data.get("reviews", [])
                    
                    for rev in reviews:
                        if isinstance(rev, dict):
                            # Lấy đúng tên key đã hiện ra trên Terminal
                            rest_id = rev.get("restaurant_id") or data.get("restaurant_id", filename)
                            text = rev.get("review_text", "")
                            rating = rev.get("rating", 0)
                            
                            if str(text).strip() != "":
                                restaurant_list.append({
                                "source_restaurant_id": str(rest_id),
                                "review_text": str(text).strip(),
                                "rating": float(rating)
                            })
            except Exception as e:
                print(f"Lỗi đọc file {filename}: {e}")

# Chuyển đổi thành Pandas DataFrame
df = pd.DataFrame(restaurant_list)

if not df.empty:
    processed_dir = os.path.join(current_dir, "../../data/processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    output_path = os.path.join(processed_dir, "data_clean.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f" Thành công tuyệt đối! Đã xuất {len(df)} dòng dữ liệu vào: {output_path}")
else:
    print(" Không tìm thấy dữ liệu review!")