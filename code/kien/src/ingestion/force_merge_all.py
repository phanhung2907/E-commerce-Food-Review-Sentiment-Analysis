import os
import json
import pandas as pd
import re

all_records = []

# 1. Nạp trọn vẹn file CSV cũ (data_clean.csv) và map đúng cột source_restaurant_id
old_csv_path = "code/kien/data/processed/data_clean.csv"
if os.path.exists(old_csv_path):
    print(f"Đang nạp file CSV cũ: {old_csv_path}...")
    df_old = pd.read_csv(old_csv_path)
    for _, row in df_old.iterrows():
        # Lấy ID từ cột 'source_restaurant_id' hoặc 'restaurant_id' của file cũ
        res_id = row.get("source_restaurant_id", "N/A")
        if pd.isna(res_id) or str(res_id).strip() == "" or str(res_id).lower() == "nan":
            res_id = row.get("restaurant_id", "N/A")
            
        all_records.append({
            "restaurant_id": str(res_id),
            "restaurant_name": str(row.get("restaurant_name", "N/A")),
            "city": str(row.get("city", "N/A")),
            "review_id": str(row.get("review_id", "N/A")),
            "rating": float(row.get("rating", 5.0)),
            "review_text": str(row.get("review_text", "")),
            "review_date": str(row.get("review_date", "")),
            "priceRange": str(row.get("priceRange", "N/A"))
        })
    print(f" -> Đã nạp xong {len(df_old)} dòng từ file cũ.")

# 2. Nạp toàn bộ các file JSON mới trong thư mục single_restaurants (Lấy priceRange ở cấp độ gốc của JSON)
local_dir = "code/kien/data/raw/single_restaurants"
if os.path.exists(local_dir):
    print("Đang nạp các file JSON mới...")
    new_count = 0
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    restaurant_name = data.get("restaurant_name", "N/A")
                    city = data.get("city", "N/A")
                    
                    # Lấy priceRange trực tiếp ở cấp độ gốc của file JSON nhà hàng (VD: "$$$$")
                    price_range = data.get("priceRange", "N/A")
                    
                    for r in data.get("reviews", []):
                        all_records.append({
                            "restaurant_id": str(data.get("restaurant_id", "N/A")),
                            "restaurant_name": restaurant_name,
                            "city": city,
                            "review_id": str(r.get("review_id", "N/A")),
                            "rating": float(r.get("rating", 5.0)),
                            "review_text": str(r.get("review_text", "")),
                            "review_date": str(r.get("review_date", "")),
                            "priceRange": str(price_range)
                        })
                        new_count += 1
            except Exception as e:
                continue
    print(f" -> Đã nạp thêm {new_count} review từ file JSON mới.")

# 3. Tạo DataFrame tổng hợp và loại bỏ trùng lặp nội dung review
df_final = pd.DataFrame(all_records)
print(f"Tổng số record trước khi lọc trùng: {len(df_final)}")

if not df_final.empty:
    df_final.drop_duplicates(subset=["review_text"], keep="first", inplace=True)
    
    # Lưu ra file CSV cuối cùng chính thức cho đồ án
    output_path = "code/kien/data/processed/all_reviews_final_report.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] Đã lưu file tổng cuối cùng tại: {output_path}")
    print(f"Tổng số review thực tế sau khi gộp chuẩn: {len(df_final)}")
    
    # 4. Thống kê nhanh theo thành phố chuẩn hóa ngay lập tức
    def clean_city_name(val):
        if pd.isna(val):
            return "Unknown"
        s = str(val)
        s = re.sub(r'^\d+\.\s*', '', s)
        s = re.split(r'Restaurants|\\n|See all', s)[0].strip()
        return s if s else "Unknown"

    df_final["city_clean"] = df_final["city"].apply(clean_city_name)
    df_final["restaurant_name_clean"] = df_final["restaurant_name"].fillna("Unknown").astype(str)
    
    city_stats = df_final.groupby("city_clean").agg(
        total_reviews=("review_text", "count"),
        total_restaurants=("restaurant_name_clean", "nunique")
    ).reset_index().sort_values(by="total_reviews", ascending=False)
    
    print("\n================ BẢNG THỐNG KÊ TỔNG HỢP CUỐI CÙNG ================")
    print(city_stats.to_string(index=False))
    print("=================================================================")
else:
    print("[WARNING] Không có dữ liệu.")