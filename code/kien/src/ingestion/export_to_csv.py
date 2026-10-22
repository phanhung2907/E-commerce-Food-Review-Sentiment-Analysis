import os
import json
import pandas as pd

# Lùi 2 cấp từ src/ingestion để vào kien/, sau đó trỏ vào data/raw/single_restaurants
current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(current_dir, "../../data/raw/single_restaurants")

restaurant_list = []

print("Đang đọc các file JSON...")
if os.path.exists(json_dir):
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rest_id = data.get("restaurant_id", filename)
                    reviews = data.get("reviews", [])
                    
                    for rev in reviews:
                        restaurant_list.append({
                            "source_restaurant_id": rest_id,
                            "review_text": str(rev.get("text", "")).strip(), # Làm sạch khoảng trắng (.strip())
                            "rating": rev.get("rating", 0)
                        })
            except Exception as e:
                print(f"Lỗi đọc file {filename}: {e}")

    # Chuyển đổi thành Pandas DataFrame
    df = pd.DataFrame(restaurant_list)

    if not df.empty:
        # Làm sạch cơ bản: loại bỏ dòng review trống
        df = df[df["review_text"] != ""]
        
        # Tạo thư mục data/processed nếu chưa có
        os.makedirs("../../data/processed", exist_ok=True)
        
        # Xuất ra file data_clean.csv
        output_path = "../../data/processed/data_clean.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f" Thành công! File CSV đã lưu tại: {output_path}")
    else:
        print(" Không tìm thấy dữ liệu review trong các file JSON!")
else:
    print(f" Không tìm thấy thư mục: {json_dir}")