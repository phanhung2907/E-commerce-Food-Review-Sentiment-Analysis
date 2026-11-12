import os
import re
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from scipy.stats import pearsonr, spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge, LinearRegression # Đã bổ sung LinearRegression ở đây
from dotenv import load_dotenv

load_dotenv()

# ================= 1. KẾT NỐI TRỰC TIẾP POSTGRESQL =================
DB_HOST = "localhost" 
DB_PORT = "5432"
DB_NAME = os.getenv('POSTGRES_DB', 'food_review')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres123')

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def analyze_question_1_volume_vs_rating():
    print("\n" + "="*65)
    print("CÂU HỎI 1: QUÁN ĐÔNG KHÁCH CÓ LÀM GIẢM CHẤT LƯỢNG (RATING) KHÔNG?")
    print("="*65)
    
    sql_q1 = """
        SELECT 
            rest.source_code,
            rest.source_restaurant_id,
            rest.name,
            COUNT(rev.source_review_id) AS review_count,
            AVG(rev.rating) AS avg_rating,
            SUM(CASE WHEN rev.rating <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(rev.source_review_id) AS neg_ratio
        FROM restaurants rest
        JOIN reviews rev 
            ON rest.source_code = rev.source_code 
            AND rest.source_restaurant_id = rev.source_restaurant_id
        WHERE rev.rating IS NOT NULL
        GROUP BY rest.source_code, rest.source_restaurant_id, rest.name
        HAVING COUNT(rev.source_review_id) >= 3;
    """
    df_rest = pd.read_sql_query(sql_q1, engine)
    
    if df_rest.empty:
        print("[-] Chưa đủ dữ liệu để phân tích.")
        return

    r_pearson, p_pearson = pearsonr(df_rest['review_count'], df_rest['avg_rating'])
    r_spearman, p_spearman = spearmanr(df_rest['review_count'], df_rest['avg_rating'])
    
    print(f"[*] Tổng số nhà hàng đưa vào phân tích (>= 3 reviews): {len(df_rest)}")
    print(f"[*] Tương quan tuyến tính (Pearson r): {r_pearson:.4f} (p-value = {p_pearson:.4e})")
    print(f"[*] Tương quan hạng (Spearman rho):    {r_spearman:.4f} (p-value = {p_spearman:.4e})")
    
    bins = [0, 10, 30, 100, 100000]
    labels = ['1. Ít (<10 reviews)', '2. Vừa (10-30)', '3. Đông (31-100)', '4. Rất đông (>100)']
    df_rest['volume_tier'] = pd.cut(df_rest['review_count'], bins=bins, labels=labels)
    
    summary = df_rest.groupby('volume_tier', observed=False).agg(
        so_luong_quan=('source_restaurant_id', 'count'),
        diem_tb=('avg_rating', 'mean'),
        ty_le_che_tb_pct=('neg_ratio', 'mean')
    ).round(2)
    
    print("\n[*] Bảng đối chiếu Điểm Rating theo Quy mô lượng đánh giá:")
    print(summary.to_string())

    # === BỔ SUNG MÔ HÌNH MACHINE LEARNING: LINEAR REGRESSION ===
    print("\n[*] --- CHẠY MÔ HÌNH MACHINE LEARNING (LINEAR REGRESSION) ---")
    # 1. Lấy dữ liệu ĐẦU VÀO (X) và ĐẦU RA (y) hoàn toàn từ data thật của database
    X = df_rest['review_count'].values.reshape(-1, 1) # Đầu vào: Số lượng review của 1.822 quán thật
    y = df_rest['avg_rating'].values                  # Đầu ra: Điểm Rating trung bình tương ứng

    # 2. Khởi tạo và huấn luyện mô hình
    lr_model = LinearRegression()
    lr_model.fit(X, y)

    # 3. Lấy ra trọng số (Coefficient) để kết luận
    he_so_goc = lr_model.coef_[0]
    
    print(f"  -> Hệ số hồi quy (Coefficient) của biến Số lượng Review: {he_so_goc:.5f}")
    if he_so_goc > 0:
        print("  -> KẾT LUẬN TỪ MODEL: Hệ số DƯƠNG. Chứng tỏ quán càng có nhiều review, điểm rating dự đoán càng TĂNG. Bác bỏ định kiến 'quán đông làm ẩu'!")
    else:
        print("  -> KẾT LUẬN TỪ MODEL: Hệ số ÂM. Chứng tỏ quán càng đông, rating càng giảm.")


def analyze_question_2_keywords_impact():
    print("\n" + "="*65)
    print("CÂU HỎI 2: TỪ KHÓA (KEYWORDS) NÀO QUYẾT ĐỊNH ĐIỂM SỐ RATING?")
    print("="*65)
    
    sql_q2 = """
        SELECT 
            rev.source_code,
            rev.review_text,
            rev.rating,
            COALESCE(rc.cuisine, 'Khác') AS cuisine
        FROM reviews rev
        JOIN restaurants rest 
            ON rev.source_code = rest.source_code 
            AND rev.source_restaurant_id = rest.source_restaurant_id
        LEFT JOIN restaurant_cuisines rc 
            ON rest.source_code = rc.source_code 
            AND rest.source_restaurant_id = rc.source_restaurant_id
        WHERE rev.review_text IS NOT NULL 
          AND TRIM(rev.review_text) <> ''
          AND rev.rating IS NOT NULL;
    """
    df_rev = pd.read_sql_query(sql_q2, engine)
    print(f"[*] Đã tải trực tiếp {len(df_rev)} bản ghi review từ PostgreSQL.")

    for src in df_rev['source_code'].unique():
        sub_df = df_rev[df_rev['source_code'] == src].copy()
        if len(sub_df) < 20:
            continue
            
        print(f"\n--- PHÂN TÍCH TỪ KHÓA TRÊN NGUỒN: {src.upper()} ({len(sub_df)} reviews) ---")
        
        vectorizer = TfidfVectorizer(
             ngram_range=(1, 2), 
            min_df=5, 
            max_features=2000,
            token_pattern=r'(?u)\b\w+\b'
        )
        X = vectorizer.fit_transform(sub_df['review_text'].str.lower())
        y = sub_df['rating'].values
        
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        
        feature_names = np.array(vectorizer.get_feature_names_out())
        coefs = model.coef_
        
        top_pos_idx = np.argsort(coefs)[-12:][::-1]
        top_neg_idx = np.argsort(coefs)[:12]
        
        print("  [+] TOP TỪ KHÓA KÉO ĐIỂM LÊN CAO (Tích cực):")
        for idx in top_pos_idx:
            print(f"      - '{feature_names[idx]}' (Trọng số: +{coefs[idx]:.3f})")
            
        print("  [-] TOP TỪ KHÓA KÉO ĐIỂM XUỐNG THẤP (Tiêu cực):")
        for idx in top_neg_idx:
            print(f"      - '{feature_names[idx]}' (Trọng số: {coefs[idx]:.3f})")


def analyze_external_factors():
    print("\n" + "="*65)
    print("ĐIỀU KIỆN ĐỦ: PHÂN TÍCH YẾU TỐ NGOẠI LỰC (LOẠI ẨM THỰC & NGUYÊN NHÂN)")
    print("="*65)
    
    sql_ext = """
        SELECT 
            rest.source_code,
            COALESCE(rc.cuisine, 'Chưa phân loại') AS cuisine,
            COUNT(rev.source_review_id) AS total_reviews,
            ROUND(AVG(rev.rating), 2) AS avg_rating,
            SUM(CASE WHEN LOWER(rev.review_text) ~ '(giao|ship|shipper|lâu|chậm|trễ|배달|遅|spilled|đổ)' THEN 1 ELSE 0 END) AS issue_delivery_packaging,
            SUM(CASE WHEN LOWER(rev.review_text) ~ '(thiếu|sai|nhầm|note|ghi chú|missing|wrong|間違)' THEN 1 ELSE 0 END) AS issue_wrong_order,
            SUM(CASE WHEN LOWER(rev.review_text) ~ '(mặn|nhạt|nguội|khô|dở|sống|thiu|tóc|冷|辛すぎ)' THEN 1 ELSE 0 END) AS issue_food_quality
        FROM reviews rev
        JOIN restaurants rest 
            ON rev.source_code = rest.source_code 
            AND rev.source_restaurant_id = rest.source_restaurant_id
        LEFT JOIN restaurant_cuisines rc 
            ON rest.source_code = rc.source_code 
            AND rest.source_restaurant_id = rc.source_restaurant_id
        WHERE rev.review_text IS NOT NULL AND rev.rating <= 3
        GROUP BY rest.source_code, COALESCE(rc.cuisine, 'Chưa phân loại')
        ORDER BY total_reviews DESC;
    """
    df_ext = pd.read_sql_query(sql_ext, engine)
    print("[*] Phân rã nguyên nhân các đánh giá thấp (Rating <= 3) theo Phong cách ẩm thực:")
    print(df_ext.to_string(index=False))

if __name__ == "__main__":
    analyze_question_1_volume_vs_rating()
    analyze_question_2_keywords_impact()
    analyze_external_factors()