import polars as pl
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from pathlib import Path

# Đường dẫn file dữ liệu Parquet bạn đã xử lý ở bước trước
DATA_PATH = Path("code/tuan/data/processed/merged_dataset_for_pearson.parquet")

def solve_core_question_with_decision_tree():
    print("\n" + "="*80)
    print("GIẢI QUYẾT VẤN ĐỀ CỐT LÕI (SỬ DỤNG DECISION TREE)")
    print("Câu hỏi: Chất lượng dịch vụ có xu hướng đi xuống khi quán quá đông khách không?")
    print("="*80)

    # 1. Đọc dữ liệu bằng Polars
    df = pl.read_parquet(DATA_PATH)
    
    # 2. Gom nhóm theo nhà hàng để tính: Số lượng Review (độ đông) và Điểm trung bình (chất lượng)
    rest_df = (
        df.group_by(["source_code", "source_restaurant_id", "name"])
        .agg([
            pl.len().alias("review_count"),
            pl.col("rating_level_5").mean().alias("avg_rating")
        ])
        # Lọc các quán có từ 5 review trở lên để loại bỏ nhiễu (quán quá mới)
        .filter(pl.col("review_count") >= 5) 
    ).to_pandas()

    print(f"[*] Đã tổng hợp dữ liệu của {len(rest_df):,} nhà hàng hợp lệ.")

    # 3. Chuẩn bị dữ liệu cho Decision Tree
    X = rest_df[['review_count']] # Biến độc lập: Số lượng khách
    y = rest_df['avg_rating']     # Biến phụ thuộc: Điểm chất lượng

    # 4. Huấn luyện Cây quyết định (Decision Tree)
    # Giới hạn max_depth=1 hoặc 2 để tìm ra "Ngưỡng gãy" (Threshold) rõ ràng nhất
    tree_model = DecisionTreeRegressor(max_depth=2, min_samples_leaf=10, random_state=42)
    tree_model.fit(X, y)

    # 5. Bóc tách logic của Cây quyết định để xuất ra báo cáo
    # Lấy ngưỡng chia cắt đầu tiên (Root node threshold)
    root_threshold = tree_model.tree_.threshold[0]
    
    # Tính điểm trung bình của 2 nhánh
    left_branch = rest_df[rest_df['review_count'] <= root_threshold]
    right_branch = rest_df[rest_df['review_count'] > root_threshold]
    
    avg_rating_left = left_branch['avg_rating'].mean()
    avg_rating_right = right_branch['avg_rating'].mean()

    print("\n[*] KẾT QUẢ TỪ MÔ HÌNH DECISION TREE:")
    print(f"  -> Mô hình đã tự động dò tìm và phát hiện NGƯỠNG QUÁ TẢI là: {int(root_threshold)} lượt review.")
    print(f"  -> Nhóm 1 (Chưa quá tải - Dưới {int(root_threshold)} review): Điểm trung bình = {avg_rating_left:.2f} sao.")
    print(f"  -> Nhóm 2 (Đã quá tải - Trên {int(root_threshold)} review): Điểm trung bình = {avg_rating_right:.2f} sao.")
    
    print("\n[*] KẾT LUẬN BÁO CÁO NGHIỆP VỤ:")
    if avg_rating_right < avg_rating_left:
        drop_pct = (avg_rating_left - avg_rating_right) / avg_rating_left * 100
        print(f"  => CÓ XU HƯỚNG ĐI XUỐNG. Trực giác của bạn hoàn toàn chính xác!")
        print(f"  => Khi nhà hàng vượt ngưỡng {int(root_threshold)} lượt đánh giá, chất lượng dịch vụ có dấu hiệu đi xuống, kéo rating giảm khoảng {drop_pct:.1f}%.")
        print("  => Điều này chứng tỏ khi lượng khách quá đông, quy trình phục vụ hoặc chất lượng món ăn của các quán không còn giữ được sự đồng đều như lúc ban đầu.")
    else:
        print("  => KHÔNG CÓ XU HƯỚNG ĐI XUỐNG. Các quán đông khách vẫn giữ vững được phong độ dịch vụ.")

if __name__ == "__main__":
    solve_core_question_with_decision_tree()