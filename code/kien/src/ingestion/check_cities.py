import pandas as pd

# Đường dẫn đến file CSV tổng đã gộp an toàn
csv_path = "code/kien/data/processed/all_reviews_merged_safe.csv"

try:
    df = pd.read_csv(csv_path)
    
    # Kiểm tra xem cột 'city' có tồn tại không
    if "city" in df.columns:
        # Đếm số lượng thành phố duy nhất
        unique_cities = df["city"].dropna().unique()
        print(f"==================================================")
        print(f" TỔNG SỐ THÀNH PHỐ ĐÃ CÀO ĐƯỢC: {len(unique_cities)}")
        print(f"==================================================\n")
        
        # Thống kê chi tiết số lượng review và số nhà hàng theo từng thành phố
        city_stats = df.groupby("city").agg(
            total_reviews=("review_text", "count"),
            total_restaurants=("restaurant_id", "nunique")
        ).reset_index()
        
        # Sắp xếp theo số lượng review giảm dần
        city_stats = city_stats.sort_values(by="total_reviews", ascending=False)
        
        print(city_stats.to_string(index=False))
    else:
        print("[WARNING] Không tìm thấy cột 'city' trong file CSV.")

except Exception as e:
    print(f"[ERROR] Lỗi khi đọc file: {e}")