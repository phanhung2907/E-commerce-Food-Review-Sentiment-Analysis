from pathlib import Path
import polars as pl

# Trỏ đúng vào thư mục chứa dữ liệu đã được Hùng pull về
DATA_DIR = Path("preprocess_merged_data")

def main():
    print("=== 1. ĐỌC DỮ LIỆU ĐÁNH GIÁ BẰNG POLARS VỚI SCHEMA OVERRIDES ===")
    
    # Ép kiểu String cho các cột ID để tránh lỗi khi gặp chuỗi Hash
    reviews_lazy = pl.scan_csv(
        DATA_DIR / "reviews_preprocessed.csv", 
        infer_schema_length=10000,
        schema_overrides={
            "source_review_id": pl.String,
            "source_restaurant_id": pl.String,
            "reviewer_id": pl.String
        }
    )
    
    total_rows = reviews_lazy.select(pl.len()).collect().item()
    print(f"Đã đọc file reviews_preprocessed.csv thành công. Tổng số dòng: {total_rows:,}\n")

    print("=== 2. KẾT NỐI VỚI BẢNG NHÀ HÀNG (RESTAURANTS) ===")
    restaurants_lazy = (
        pl.scan_csv(
            DATA_DIR / "restaurants.csv", 
            infer_schema_length=10000,
            schema_overrides={
                "source_restaurant_id": pl.String
            }
        )
        .select(["source_code", "source_restaurant_id", "name", "city", "avg_rating", "latitude", "longitude"])
    )

    print("=== 3. LỌC ĐIỂM SỐ VÀ GÁN NHÃN CẢM XÚC (SENTIMENT) ===")
    # Nối 2 bảng dựa trên KHÓA GHÉP của Hùng
    final_dataset_lazy = (
        reviews_lazy
        .filter(pl.col("rating_level_5") > 0)
        .join(
            restaurants_lazy,
            on=["source_code", "source_restaurant_id"], # Khóa ghép theo file CSV mới
            how="left"
        )
        .with_columns(
            pl.when(pl.col("rating_level_5") <= 2).then(pl.lit("negative"))
            .when(pl.col("rating_level_5") == 3).then(pl.lit("neutral"))
            .otherwise(pl.lit("positive"))
            .alias("sentiment_label")
        )
    )

    sentiment_counts = (
        final_dataset_lazy
        .group_by(["source_code", "sentiment_label"])
        .len()
        .sort(["source_code", "sentiment_label"])
        .collect()
    )
    print("Phân bố nhãn Sentiment theo từng nguồn dữ liệu:")
    print(sentiment_counts)

    output_path = Path("code/tuan/data/processed/reviews_ready_for_model.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("\nĐang lưu dữ liệu...")
    final_dataset_lazy.collect().write_parquet(output_path)
    print(f"Đã lưu thành công bộ dữ liệu sạch tại: {output_path}")

if __name__ == "__main__":
    main()