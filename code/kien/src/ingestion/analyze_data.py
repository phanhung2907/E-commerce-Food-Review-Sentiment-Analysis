import os
import json
import re
import pandas as pd

# Đường dẫn đến thư mục chứa các file JSON nhà hàng đã cào
local_dir = "code/kien/data/raw/single_restaurants"

restaurant_list = []
all_reviews = []

print("Đang quét và nạp dữ liệu từ các file JSON...")

if os.path.exists(local_dir):
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # 1. Trích xuất thông tin tổng quan của nhà hàng
                    metadata = data.get("metadata", {})
                    aggregate_rating = metadata.get("aggregateRating", {})
                    
                    # --- LÀM SẠCH TÊN THÀNH PHỐ BẰNG REGEX ---
                    raw_city = data.get("city", "Unknown")
                    first_line = raw_city.split("\n")[0].strip()
                    
                    # Nếu phát hiện chứa "Vietnam_Subregion", ta bỏ qua hoặc đánh dấu để loại bỏ
                    if "Vietnam_Subregion" in first_line or "Vietnam_Subregion" in str(raw_city):
                        continue  # Bỏ qua các file bị lỗi gán nhãn vùng hệ thống này
                    
                    # Loại bỏ số thứ tự ở đầu và chữ "Restaurants" phía sau
                    cleaned = re.sub(r'^\d+\.\s*', '', first_line)
                    clean_city = re.sub(r'\s+Restaurants.*$', '', cleaned, flags=re.IGNORECASE).strip()

                    restaurant_list.append({
                        "restaurant_id": data.get("restaurant_id"),
                        "restaurant_name": data.get("restaurant_name"),
                        "city": clean_city,
                        "reviews_count_scraped": data.get("reviews_count", 0),
                        "rating_value": aggregate_rating.get("ratingValue", "N/A"),
                        "total_reviews_web": aggregate_rating.get("reviewCount", "N/A"),
                        "price_range": metadata.get("priceRange", "N/A"),
                        "serves_cuisine": ", ".join(metadata.get("servesCuisine", [])) if isinstance(metadata.get("servesCuisine"), list) else "N/A"
                    })
                    
                    # 2. Trích xuất danh sách reviews chi tiết
                    for rev in data.get("reviews", []):
                        all_reviews.append({
                            "restaurant_id": data.get("restaurant_id"),
                            "restaurant_name": data.get("restaurant_name"),
                            "city": clean_city,
                            "review_id": rev.get("review_id"),
                            "review_text": rev.get("review_text"),
                            "review_date": rev.get("review_date")
                        })
            except Exception as e:
                print(f"Lỗi đọc file {file_name}: {e}")

# Chuyển đổi thành Pandas DataFrame
df_restaurants = pd.DataFrame(restaurant_list)
df_reviews = pd.DataFrame(all_reviews)

print("\n================ TỔNG KẾT DỮ LIỆU BAN ĐẦU ================")
print(f"Tổng số nhà hàng đã nạp (đã lọc Subregion): {len(df_restaurants)}")
print(f"Tổng số bài review đã nạp: {len(df_reviews)}")

if not df_restaurants.empty:
    print("\nVí dụ 5 nhà hàng đầu tiên:")
    print(df_restaurants[["restaurant_name", "city", "rating_value", "price_range"]].head())


# ==========================================
# PHẦN 2: THỐNG KÊ CHI TIẾT CHO BÁO CÁO NHÓM TRƯỞNG
# ==========================================

print("\n================ THỐNG KÊ CHI TIẾT CHO BÁO CÁO ================")

# 1. Thống kê Top 5 thành phố có số lượng nhà hàng nhiều nhất
print("\n--- 1. TOP 5 KHU VỰC/THÀNH PHỐ CÓ NHIỀU NHÀ HÀNG NHẤT ---")
top_cities = df_restaurants['city'].value_counts().head(5)
print(top_cities)

# 2. Thống kê phân khúc giá (Price Range) của nhà hàng
print("\n--- 2. PHÂN BỔ PHÂN KHÚC GIÁ (PRICE RANGE) ---")
price_distribution = df_restaurants['price_range'].value_counts()
print(price_distribution)

# 3. Thống kê điểm số đánh giá trung bình (Rating Value)
df_valid_rating = df_restaurants[df_restaurants['rating_value'] != 'N/A'].copy()
df_valid_rating['rating_value'] = df_valid_rating['rating_value'].astype(float)

print("\n--- 3. THỐNG KÊ ĐIỂM SỐ RATING ---")
print(f"Điểm rating trung bình toàn hệ thống: {df_valid_rating['rating_value'].mean():.2f} / 5.0")
print(f"Điểm rating cao nhất: {df_valid_rating['rating_value'].max()}")
print(f"Điểm rating thấp nhất: {df_valid_rating['rating_value'].min()}")

# 4. Top 5 nhà hàng có số lượng review được cào nhiều nhất
print("\n--- 4. TOP 5 NHÀ HÀNG CÓ SỐ LƯỢNG REVIEW NHIỀU NHẤT TRONG DATA ---")
top_reviewed = df_restaurants.sort_values(by='reviews_count_scraped', ascending=False).head(5)
for idx, row in top_reviewed.iterrows():
    print(f" - {row['restaurant_name']} ({row['city']}): {row['reviews_count_scraped']} reviews")