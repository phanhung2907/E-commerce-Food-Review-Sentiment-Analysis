import pandas as pd

# Đường dẫn đến file CSV tổng của em
csv_path = "code/kien/data/processed/all_reviews_final_report.csv" 
# Hoặc file cũ nếu cần check: "code/kien/data/processed/data_clean.csv"

try:
    print("Đang đọc file CSV, vui lòng đợi một chút...")
    df = pd.read_csv(csv_path)
    
    # Tổng số dòng (tương ứng với tổng số review)
    total_reviews = len(df)
    
    print(f"\n==================================================")
    print(f" KẾT QUẢ KIỂM TRA TỔNG REVIEW TRONG CSV")
    print(f"==================================================\n")
    print(f"📁 Tên file: {csv_path}")
    print(f"📊 Tổng số lượng review: {total_reviews:,} bài")
    
    # Kiểm tra thêm số lượng cột và tên các cột chính
    print(f"📌 Số lượng cột dữ liệu: {len(df.columns)}")
    print(f"📋 Các cột có trong file: {list(df.columns)}")
    
    print(f"==================================================\n")

except Exception as e:
    print(f"[ERROR] Không thể đọc file: {e}")