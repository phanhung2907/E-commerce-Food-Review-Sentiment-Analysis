"""Cleaning and raw-to-processed ETL entry point."""

import pandas as pd
from pathlib import Path

def main() -> None:
    """Run data validation and cleaning."""
    # Xác định đường dẫn file raw và processed
    raw_path = Path("code/kien/data/raw/tripadvisor_real.csv")
    processed_dir = Path("code/kien/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path = processed_dir / "tripadvisor_cleaned.csv"

    if not raw_path.exists():
        print(f"Không tìm thấy file raw tại: {raw_path}")
        return

    # Đọc dữ liệu raw từ file CSV của bạn
    df = pd.read_csv(raw_path, on_bad_lines='skip')
    print(f"Đã tải thành công {len(df)} dòng dữ liệu từ {raw_path}")

    # 1. Bổ sung các features định vị và phân khúc còn thiếu để đồng bộ schema chung
    df['city'] = df.get('city', 'Quy Nhơn')
    df['district'] = df.get('district', 'Chưa xác định')
    df['price_range'] = df.get('price_range', 'Trung bình')
    df['cuisine_type'] = df.get('cuisine_type', 'Ẩm thực địa phương')

    # 2. Tạo các derived features phục vụ phân tích (RQ2 - nhận diện review 1 sao, độ dài text)
    if 'review_text' in df.columns:
        df['comment_length'] = df['review_text'].fillna('').astype(str).str.len()
    
    if 'rating' in df.columns:
        df['is_1_star'] = (df['rating'] == 1).astype(int)

    # 3. Lưu kết quả vào thư mục processed
    df.to_csv(processed_path, index=False)
    print(f"Đã làm sạch và bổ sung features thành công! File lưu tại: {processed_path}")

if __name__ == "__main__":
    main()