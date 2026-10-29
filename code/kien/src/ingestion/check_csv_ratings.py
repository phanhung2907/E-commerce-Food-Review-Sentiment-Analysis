import pandas as pd

# Đường dẫn đến file CSV tổng của em
csv_path = "code/kien/data/processed/all_reviews_final_report.csv" 
# Nếu em muốn check file cũ thì đổi thành: "code/kien/data/processed/data_clean.csv"

try:
    df = pd.read_csv(csv_path)
    
    if "rating" in df.columns:
        # Ép kiểu rating sang float để chắc chắn không bị lỗi định dạng
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        
        print(f"==================================================")
        print(f" THỐNG KÊ PHÂN PHỐI SAO TRONG FILE CSV")
        print(f"==================================================\n")
        
        # Đếm số lượng review theo từng mức sao (sắp xếp từ cao xuống thấp)
        rating_counts = df["rating"].value_counts().sort_index(ascending=False)
        print(rating_counts)
        
        # Lọc ra các review dưới 5 sao (1.0, 2.0, 3.0, 4.0)
        below_5_stars = df[df["rating"] < 5.0]
        print(f"\n--------------------------------------------------")
        print(f" Tổng số lượng review dưới 5 sao: {len(below_5_stars)}")
        print(f" Chiếm tỷ lệ: {(len(below_5_stars) / len(df)) * 100:.2f}% tổng số review")
        print(f"--------------------------------------------------\n")
        
        # In thử 3 nội dung review dưới 5 sao bất kỳ để kiểm chứng thực tế
        if not below_5_stars.empty:
            print("💡 Mẫu một vài review dưới 5 sao thực tế trong file:")
            sample_reviews = below_5_stars.sample(min(3, len(below_5_stars)))
            for idx, row in sample_reviews.iterrows():
                print(f" - [{row['rating']} sao] Quán: {row.get('restaurant_name', 'N/A')} | Nội dung: {str(row['review_text'])[:100]}...")
    else:
        print("[WARNING] Không tìm thấy cột 'rating' trong file CSV.")

except Exception as e:
    print(f"[ERROR] Lỗi khi đọc file: {e}")