import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

# Cấu hình đường dẫn
DATA_PATH = Path("code/tuan/data/processed/merged_dataset_for_pearson.parquet")
OUTPUT_DIR = Path("code/tuan/reports") 
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_rating_vs_review():
    print("[*] Đang đọc dữ liệu để vẽ biểu đồ Tương quan Rating...")
    df = pl.read_parquet(DATA_PATH)
    
    # 1. Gom nhóm và tính toán y hệt Model V2
    rest_df_raw = (
        df.group_by(["source_code", "source_restaurant_id", "name"])
        .agg([
            pl.len().alias("review_count"),
            pl.col("rating_level_5").mean().alias("avg_rating")
        ])
        .filter(pl.col("review_count") >= 5) 
    ).to_pandas()

    # Lọc bỏ 5% Outliers (Chỉ lấy quán <= 100 review)
    threshold_95 = rest_df_raw['review_count'].quantile(0.95)
    rest_df = rest_df_raw[rest_df_raw['review_count'] <= threshold_95]

    # --- VẼ BIỂU ĐỒ SCATTER PLOT ---
    plt.figure(figsize=(12, 6))
    
    # Vẽ các điểm dữ liệu (mỗi dấu chấm là 1 nhà hàng)
    sns.scatterplot(
        data=rest_df, 
        x='review_count', 
        y='avg_rating', 
        alpha=0.4,          # Làm mờ dấu chấm để thấy chỗ nào tập trung đông
        color='dodgerblue',
        edgecolor=None
    )

    # Vẽ ĐƯỜNG NGƯỠNG GÃY (Threshold = 20) bằng vạch đỏ đứt nét
    plt.axvline(x=20, color='red', linestyle='--', linewidth=2.5, label='Ngưỡng gãy Decision Tree (20 review)')

    # Thêm chú thích điểm số trung bình vào 2 bên của biểu đồ
    plt.text(10, 1.5, 'NHÓM 1 (< 20 Review)\nTrung bình: 3.71 sao', 
             color='darkred', fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.7))
    plt.text(60, 1.5, 'NHÓM 2 (> 20 Review)\nTrung bình: 3.82 sao', 
             color='darkgreen', fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.7))

    # Trang trí biểu đồ
    plt.title('TƯƠNG QUAN GIỮA SỐ LƯỢNG REVIEW VÀ ĐIỂM ĐÁNH GIÁ\n(Dữ liệu tập trung vào phân khúc SME - Đã lọc 5% Outliers)', fontsize=14, pad=15)
    plt.xlabel('Số lượng Review (Khách hàng)', fontsize=12)
    plt.ylabel('Điểm Đánh giá Trung bình (Sao)', fontsize=12)
    plt.legend(loc='lower right')
    
    # Giới hạn trục Y từ 1 đến 5 sao cho chuẩn thực tế
    plt.ylim(1, 5.2)

    plt.tight_layout()
    plot_path = OUTPUT_DIR / "eda_rating_scatter.png"
    plt.savefig(plot_path, dpi=300)
    print(f"[+] Đã lưu biểu đồ Scatter Plot tại: {plot_path}")

if __name__ == "__main__":
    visualize_rating_vs_review()