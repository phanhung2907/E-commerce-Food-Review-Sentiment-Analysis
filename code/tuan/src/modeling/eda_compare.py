import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

# Cấu hình đường dẫn
DATA_PATH = Path("code/tuan/data/processed/merged_dataset_for_pearson.parquet")
OUTPUT_DIR = Path("code/tuan/reports") # Lưu ảnh vào thư mục reports của bạn
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_eda_comparison():
    print("[*] Đang đọc dữ liệu để vẽ biểu đồ EDA so sánh...")
    df = pl.read_parquet(DATA_PATH)
    
    # 1. Dữ liệu gốc (Chưa lọc Outliers)
    rest_df_raw = (
        df.group_by(["source_code", "source_restaurant_id", "name"])
        .agg([pl.len().alias("review_count")])
        .filter(pl.col("review_count") >= 5) 
    ).to_pandas()

    # 2. Dữ liệu V2 (Đã lọc 5% Outliers)
    threshold_95 = rest_df_raw['review_count'].quantile(0.95)
    rest_df_cleaned = rest_df_raw[rest_df_raw['review_count'] <= threshold_95]

    print(f"[*] Dữ liệu gốc: {len(rest_df_raw):,} quán.")
    print(f"[*] Dữ liệu sau khi gọt Outliers (<= {int(threshold_95)} review): {len(rest_df_cleaned):,} quán.")

    sns.set_theme(style="whitegrid")

    # --- BIỂU ĐỒ 1: SO SÁNH BOXPLOT (Sự khác biệt về nhiễu) ---
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    sns.boxplot(y=rest_df_raw['review_count'], color='salmon')
    plt.title("Model Cũ: CHƯA lọc Outliers\n(Dữ liệu bị kéo giãn bởi các quán khổng lồ)")
    plt.ylabel("Số lượng Review")

    plt.subplot(1, 2, 2)
    sns.boxplot(y=rest_df_cleaned['review_count'], color='lightgreen')
    plt.title(f"Model V2: ĐÃ lọc 5% Outliers\n(Tập trung vào các quán <= {int(threshold_95)} review)")
    plt.ylabel("Số lượng Review")

    plt.tight_layout()
    boxplot_path = OUTPUT_DIR / "eda_boxplot_comparison.png"
    plt.savefig(boxplot_path, dpi=300)
    
    # --- BIỂU ĐỒ 2: SO SÁNH HISTOGRAM (Phân bố dữ liệu) ---
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    sns.histplot(rest_df_raw['review_count'], bins=50, color='salmon', kde=True)
    plt.title("Phân bố Model Cũ")
    plt.xlabel("Số lượng Review")
    plt.ylabel("Số lượng Nhà hàng")

    plt.subplot(1, 2, 2)
    sns.histplot(rest_df_cleaned['review_count'], bins=50, color='lightgreen', kde=True)
    plt.title("Phân bố Model V2 (Sát thực tế hơn)")
    plt.xlabel("Số lượng Review")
    plt.ylabel("Số lượng Nhà hàng")

    plt.tight_layout()
    hist_path = OUTPUT_DIR / "eda_histogram_comparison.png"
    plt.savefig(hist_path, dpi=300)

    print(f"[+] Đã lưu thành công 2 biểu đồ so sánh vào thư mục: {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_eda_comparison()