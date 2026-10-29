import pandas as pd
import re

csv_path = "code/kien/data/processed/all_reviews_final_report.csv"

try:
    df = pd.read_csv(csv_path)
    
    # 1. Làm sạch tên thành phố
    def clean_city_name(val):
        if pd.isna(val):
            return "Unknown"
        s = str(val)
        s = re.sub(r'^\d+\.\s*', '', s)
        s = re.split(r'Restaurants|\\n|See all', s)[0].strip()
        return s if s else "Unknown"

    df["city_clean"] = df["city"].apply(clean_city_name)
    
    # 2. Xử lý cột tên nhà hàng: nếu bị trống/N/A thì lấy restaurant_id hoặc gán nhãn thay thế để không bị tính là 0
    if "restaurant_name" in df.columns:
        df["restaurant_name_clean"] = df["restaurant_name"].fillna("Unknown").astype(str)
        # Nếu là N/A hoặc nan thì thay bằng ID hoặc định danh khác
        mask = df["restaurant_name_clean"].isin(["N/A", "nan", "", "Unknown"])
        if "restaurant_id" in df.columns:
            df.loc[mask, "restaurant_name_clean"] = df.loc[mask, "restaurant_id"].astype(str)
        else:
            df.loc[mask, "restaurant_name_clean"] = "Restaurant_" + df.index.astype(str)
    else:
        df["restaurant_name_clean"] = "Restaurant_" + df.index.astype(str)

    # 3. Gom nhóm và đếm tổng số review và tổng số nhà hàng
    city_stats = df.groupby("city_clean").agg(
        total_reviews=("review_text", "count"),
        total_restaurants=("restaurant_name_clean", "nunique")
    ).reset_index()
    
    # 4. Sắp xếp từ cao xuống thấp theo số lượng review
    city_stats = city_stats.sort_values(by="total_reviews", ascending=False)
    
    print(f"==================================================")
    print(f" THỐNG KÊ THÀNH PHỐ TỪ CAO ĐẾN THẤP (CHUẨN XÁC)")
    print(f"==================================================\n")
    
    print(city_stats.to_string(index=False))
    
except Exception as e:
    print(f"[ERROR]: {e}")