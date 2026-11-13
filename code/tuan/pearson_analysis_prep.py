import polars as pl
from scipy.stats import pearsonr
import numpy as np
from pathlib import Path

# Thư mục chứa các file CSV do nhóm xuất ra từ PostgreSQL
DATA_DIR = Path("preprocess_merged_data")

def main():
    print("1. ĐANG ĐỌC DỮ LIỆU TỪ CÁC FILE CSV...")
    
    # 1.1 Đọc bảng Reviews (dùng schema_overrides để tránh lỗi chuỗi Hash)
    reviews_df = pl.read_csv(
        DATA_DIR / "reviews_preprocessed.csv",
        schema_overrides={
            "source_review_id": pl.String,
            "source_restaurant_id": pl.String,
            "reviewer_id": pl.String
        }
    )
    print(f" - Đã đọc bảng Reviews: {reviews_df.height:,} dòng.")

    # Lọc bỏ các dòng lỗi (điểm = 0) theo đúng báo cáo
    reviews_df = reviews_df.filter(pl.col("rating_level_5") > 0)
    print(f" - Số dòng Reviews hợp lệ (sau khi loại điểm 0): {reviews_df.height:,} dòng.")

    # 1.2 Đọc bảng Restaurants
    restaurants_df = pl.read_csv(
        DATA_DIR / "restaurants.csv",
        schema_overrides={
            "source_restaurant_id": pl.String
        }
    ).select(["source_code", "source_restaurant_id", "name", "city"])
    
    print(f" - Đã đọc bảng Restaurants: {restaurants_df.height:,} dòng.")

    # 1.3 Đọc bảng Reviewers (để tính số lượng hình ảnh/tương tác)
    reviewers_df = pl.read_csv(
        DATA_DIR / "reviewers.csv",
        schema_overrides={
            "reviewer_id": pl.String
        }
    ).select(["source_code", "reviewer_id", "total_reviews", "total_pictures"])
    
    print(f" - Đã đọc bảng Reviewers: {reviewers_df.height:,} dòng.\n")

    print("2. CHUẨN BỊ DỮ LIỆU CHO KIỂM ĐỊNH PEARSON...")
    
    # Kết nối dữ liệu: Đưa thông tin nhà hàng và người dùng vào bảng Review
    merged_df = (
        reviews_df
        .join(
            restaurants_df,
            on=["source_code", "source_restaurant_id"],
            how="left"
        )
        .join(
            reviewers_df,
            on=["source_code", "reviewer_id"],
            how="left"
        )
    )

    # Tính toán các độ dài để kiểm định tương quan (Pearson)
    # Ví dụ: Độ dài của review_text
    final_df = merged_df.with_columns(
        pl.col("review_text").str.len_chars().fill_null(0).alias("review_length")
    )
    
    print(f" - Bộ dữ liệu phân tích đã sẵn sàng với {final_df.height:,} dòng.")

    print("\n3. THỰC HIỆN KIỂM ĐỊNH PEARSON (Theo phương pháp học trên MAS)...")
    
    # Yêu cầu kiểm định: Tương quan giữa Độ dài bình luận và Điểm đánh giá (rating_level_5)
    # Lọc ra các dòng có dữ liệu số hợp lệ để tránh lỗi tính toán
    valid_data = final_df.filter(
        pl.col("review_length").is_not_null() & 
        pl.col("rating_level_5").is_not_null()
    )

    x = valid_data["review_length"].to_numpy()
    y = valid_data["rating_level_5"].to_numpy()
    
    # Tính hệ số Pearson
    correlation, p_value = pearsonr(x, y)
    
    print(f" - Hệ số tương quan Pearson (r) giữa [Độ dài bình luận] và [Điểm đánh giá]: {correlation:.4f}")
    print(f" - Giá trị P-value: {p_value:.4e}")
    
    if p_value < 0.05:
        print(" => Kết luận: Có mối tương quan có ý nghĩa thống kê (P-value < 0.05) giữa độ dài bình luận và điểm số.")
    else:
        print(" => Kết luận: Không có mối tương quan rõ ràng (P-value >= 0.05).")

    # Tương tự, kiểm tra tương quan giữa Điểm đánh giá và Số lượng ảnh của người dùng (từ bảng reviewers)
    # Foody và TripAdvisor có dữ liệu về ảnh
    valid_pic_data = final_df.filter(
        pl.col("total_pictures").is_not_null() & 
        pl.col("rating_level_5").is_not_null()
    )
    
    if valid_pic_data.height > 0:
        x2 = valid_pic_data["total_pictures"].to_numpy()
        y2 = valid_pic_data["rating_level_5"].to_numpy()
        corr_pic, p_val_pic = pearsonr(x2, y2)
        print(f"\n - Hệ số Pearson (r) giữa [Tổng số ảnh của Reviewer] và [Điểm đánh giá]: {corr_pic:.4f}")
        print(f" - Giá trị P-value: {p_val_pic:.4e}")

    # Xuất ra file để lưu lại kết quả đã gộp
    out_file = Path("code/tuan/data/processed/merged_dataset_for_pearson.parquet")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    final_df.write_parquet(out_file)
    print(f"\n4. Đã lưu bộ dữ liệu gộp thành công tại: {out_file}")

if __name__ == "__main__":
    main()