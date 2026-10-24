import os
import json
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(current_dir, "../../data/raw/single_restaurants")

restaurant_list = []
all_ratings_counter = {}

print("Đang quét toàn bộ file JSON để thống kê phân phối điểm số...")
if os.path.exists(json_dir):
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    reviews = data.get("reviews", [])
                    
                    for rev in reviews:
                        if isinstance(rev, dict):
                            rest_id = rev.get("restaurant_id") or data.get("restaurant_id", filename)
                            text = rev.get("review_text", "")
                            
                            rating_val = rev.get("rating", 5.0)
                            try:
                                rating_float = float(str(rating_val).replace("of 5 bubbles", "").strip())
                            except:
                                rating_float = 5.0
                                
                            # Đếm tần suất xuất hiện của từng mức rating
                            all_ratings_counter[rating_float] = all_ratings_counter.get(rating_float, 0) + 1
                            
                            if str(text).strip() != "":
                                restaurant_list.append({
                                    "source_restaurant_id": str(rest_id),
                                    "review_text": str(text).strip(),
                                    "rating": rating_float
                                })
            except Exception as e:
                print(f"Lỗi đọc file {filename}: {e}")

    print("\n================ STATS ================")
    print("Thống kê số lượng theo từng mức rating trong toàn bộ dữ liệu:")
    for score, count in sorted(all_ratings_counter.items()):
        print(f" - {score} sao: {count} review")
    print("=======================================\n")

    df = pd.DataFrame(restaurant_list)

    if not df.empty:
        processed_dir = os.path.join(current_dir, "../../data/processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        output_path = os.path.join(processed_dir, "data_clean.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f" Thành công! Đã xuất {len(df)} dòng dữ liệu vào: {output_path}")
    else:
        print(" Không tìm thấy dữ liệu review!")
else:
    print(f" Không tìm thấy thư mục: {json_dir}")