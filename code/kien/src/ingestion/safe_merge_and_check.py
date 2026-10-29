import os
import json
import pandas as pd

old_csv_path = "code/kien/data/processed/data_clean.csv"
local_dir = "code/kien/data/raw/single_restaurants" # Hoặc thư mục backup của em
all_records = []

# 1. Đọc data cũ
if os.path.exists(old_csv_path):
    df_old = pd.read_csv(old_csv_path)
    for _, row in df_old.iterrows():
        all_records.append({
            "restaurant_id": str(row.get("restaurant_id", "N/A")),
            "restaurant_name": str(row.get("restaurant_name", "N/A")),
            "city": str(row.get("city", "N/A")),
            "review_id": str(row.get("review_id", "N/A")),
            "rating": float(row.get("rating", 5.0)),
            "review_text": str(row.get("review_text", "")),
            "review_date": str(row.get("review_date", ""))
        })

# 2. Đọc data JSON mới
if os.path.exists(local_dir):
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    restaurant_name = data.get("restaurant_name", "N/A")
                    city = data.get("city", "N/A")
                    for r in data.get("reviews", []):
                        all_records.append({
                            "restaurant_id": str(data.get("restaurant_id", "N/A")),
                            "restaurant_name": restaurant_name,
                            "city": city,
                            "review_id": str(r.get("review_id", "N/A")),
                            "rating": float(r.get("rating", 5.0)),
                            "review_text": str(r.get("review_text", "")),
                            "review_date": str(r.get("review_date", ""))
                        })
            except:
                continue

# 3. Tạo DataFrame và lọc trùng
df_final = pd.DataFrame(all_records)
if not df_final.empty:
    df_final.drop_duplicates(subset=["review_text"], keep="first", inplace=True)
    
    # 🔍 KIỂM TRA ĐỘ CHUYÊN SÂU: ĐẾM SỐ LƯỢNG THEO TỪNG MỨC SAO NGAY TRONG TERMINAL
    print("\n================ THỐNG KÊ SAU KHI GỘP ================")
    print(df_final["rating"].value_counts().sort_index(ascending=False))
    print("=====================================================\n")

    output_path = "code/kien/data/processed/all_reviews_merged_safe.csv"
    df_final.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] Đã lưu file an toàn tại: {output_path}")
else:
    print("[WARNING] Không có dữ liệu.")