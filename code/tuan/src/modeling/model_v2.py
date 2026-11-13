import polars as pl
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from pathlib import Path

DATA_PATH = Path("code/tuan/data/processed/merged_dataset_for_pearson.parquet")

def solve_core_question_with_decision_tree_v2():
    print("\n" + "="*80)
    print("MÔ HÌNH V2: SỬ DỤNG DECISION TREE & LỌC TOP 5% OUTLIERS")
    print("="*80)

    df = pl.read_parquet(DATA_PATH)
    
    # Gom nhóm theo nhà hàng (chỉ lấy quán >= 5 review)
    rest_df_raw = (
        df.group_by(["source_code", "source_restaurant_id", "name"])
        .agg([
            pl.len().alias("review_count"),
            pl.col("rating_level_5").mean().alias("avg_rating")
        ])
        .filter(pl.col("review_count") >= 5) 
    )

    # Lọc bỏ 5% Outliers
    threshold_95 = rest_df_raw.select(pl.col("review_count").quantile(0.95)).item()
    rest_df = rest_df_raw.filter(pl.col("review_count") <= threshold_95).to_pandas()

    print(f"[*] Ngưỡng loại bỏ Outliers (95%): {int(threshold_95)} lượt review.")
    print(f"[*] Số nhà hàng sau khi lọc (đưa vào model): {len(rest_df):,} quán.")

    # Huấn luyện
    X = rest_df[['review_count']]
    y = rest_df['avg_rating']
    
    tree_model = DecisionTreeRegressor(max_depth=2, min_samples_leaf=10, random_state=42)
    tree_model.fit(X, y)
    root_threshold = tree_model.tree_.threshold[0]
    
    # Tính điểm
    left_branch = rest_df[rest_df['review_count'] <= root_threshold]
    right_branch = rest_df[rest_df['review_count'] > root_threshold]
    
    avg_rating_left = left_branch['avg_rating'].mean()
    avg_rating_right = right_branch['avg_rating'].mean()

    print("\n[*] KẾT QUẢ TỪ MÔ HÌNH (V2):")
    print(f"  -> NGƯỠNG QUÁ TẢI MỚI là: {int(root_threshold)} lượt review.")
    print(f"  -> Dưới {int(root_threshold)} review: {avg_rating_left:.2f} sao.")
    print(f"  -> Trên {int(root_threshold)} review: {avg_rating_right:.2f} sao.")

    # === THÊM PHẦN KẾT LUẬN ===
    print("\n[*] KẾT LUẬN BÁO CÁO NGHIỆP VỤ (SAU KHI LỌC OUTLIERS):")
    if avg_rating_right < avg_rating_left:
        drop_pct = (avg_rating_left - avg_rating_right) / avg_rating_left * 100
        print("  => CÓ XU HƯỚNG ĐI XUỐNG. Trực giác của bạn hoàn toàn chính xác!")
        print(f"  => Đối với tập khách hàng cốt lõi (các quán vừa và nhỏ), khi nhà hàng vượt ngưỡng {int(root_threshold)} lượt đánh giá,")
        print(f"     chất lượng dịch vụ bắt đầu có dấu hiệu đi xuống, kéo rating giảm khoảng {drop_pct:.1f}%.")
        print("  => Điều này chứng tỏ khi lượng khách tăng lên đột ngột, quy trình phục vụ của các quán nhỏ không kịp thích ứng.")
    else:
        increase_pct = (avg_rating_right - avg_rating_left) / avg_rating_left * 100
        print("  => KHÔNG CÓ XU HƯỚNG ĐI XUỐNG. Thậm chí chất lượng còn tăng lên!")
        print(f"  => Đối với nhóm quán vừa và nhỏ, khi họ đạt qua ngưỡng {int(root_threshold)} review, điểm đánh giá của họ tăng thêm {increase_pct:.1f}%.")
        print("  => Phân tích nghiệp vụ: Những quán vượt qua được mốc 20 review thường là những quán đã 'sống sót' qua giai đoạn mở bán ban đầu,")
        print("     bắt đầu có lượng khách quen và quy trình ổn định hơn, từ đó nhận được đánh giá tích cực hơn.")

if __name__ == "__main__":
    solve_core_question_with_decision_tree_v2()