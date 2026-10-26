import os
import re
import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ================= 1. KẾT NỐI TRỰC TIẾP POSTGRESQL =================
DB_HOST = "localhost" 
DB_PORT = "5432"
DB_NAME = os.getenv('POSTGRES_DB', 'food_review')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres123')

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    print("[+] Kết nối PostgreSQL thành công!")
except Exception as e:
    print(f"[-] Lỗi kết nối PostgreSQL: {e}")
    print("[-] Hãy đảm bảo dịch vụ PostgreSQL trên máy tính của bạn đã được khởi động.")
    exit(1)

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
            SUM(CASE WHEN rev.rating <= 2 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(rev.source_review_id), 0) AS neg_ratio
        FROM restaurants rest
        LEFT JOIN reviews rev 
            ON rest.source_code = rev.source_code 
            AND rest.source_restaurant_id = rev.source_restaurant_id
        WHERE rev.rating IS NOT NULL
        GROUP BY rest.source_code, rest.source_restaurant_id, rest.name
        HAVING COUNT(rev.source_review_id) >= 1;
    """
    df_rest = pd.read_sql(sql_q1, conn)
    
    if df_rest.empty:
        print("[-] Chưa đủ dữ liệu trong Database để phân tích.")
        return

    r_pearson = np.corrcoef(df_rest['review_count'], df_rest['avg_rating'])[0, 1]
    
    print(f"[*] Tổng số nhà hàng đưa vào phân tích: {len(df_rest)}")
    print(f"[*] Tương quan tuyến tính (Pearson r): {r_pearson:.4f}")
    
    # Phân loại quy mô quán rõ ràng hơn
    bins = [-1, 5, 20, 50, 100000]
    labels = ['1. Rất ít (<5 reviews)', '2. Ít (5-20)', '3. Vừa (21-50)', '4. Đông (>50 reviews)']
    df_rest['volume_tier'] = pd.cut(df_rest['review_count'], bins=bins, labels=labels)
    
    summary = df_rest.groupby('volume_tier', observed=False).agg(
        so_luong_quan=('source_restaurant_id', 'count'),
        diem_tb=('avg_rating', 'mean'),
        ty_le_che_tb_pct=('neg_ratio', 'mean')
    ).round(2)
    
    print("\n[*] Bảng đối chiếu Điểm Rating theo Quy mô lượng đánh giá:")
    print(summary.to_string())


def analyze_question_2_keywords_impact():
    print("\n" + "="*65)
    print("CÂU HỎI 2: TỪ KHÓA (KEYWORDS) NÀO QUYẾT ĐỊNH ĐIỂM SỐ RATING?")
    print("="*65)
    
    sql_q2 = """
        SELECT 
            rev.source_code,
            rev.review_text,
            rev.rating
        FROM reviews rev
        WHERE rev.review_text IS NOT NULL 
          AND TRIM(rev.review_text) <> ''
          AND rev.rating IS NOT NULL;
    """
    df_rev = pd.read_sql(sql_q2, conn)
    
    if df_rev.empty:
        print("[-] Không tìm thấy dữ liệu review trong PostgreSQL.")
        return
        
    print(f"[*] Đã tải trực tiếp {len(df_rev)} bản ghi review từ PostgreSQL.")

    for src in df_rev['source_code'].unique():
        sub_df = df_rev[df_rev['source_code'] == src].copy()
        if len(sub_df) < 10:
            continue
            
        print(f"\n--- PHÂN TÍCH TỪ KHÓA TRÊN NGUỒN: {src.upper()} ({len(sub_df)} reviews) ---")
        
        all_words = []
        # Các từ dừng tiếng Anh phổ biến cần loại bỏ để kết quả sạch hơn
        stopwords = {"the", "and", "a", "to", "of", "in", "for", "is", "on", "that", "by", "this", "with", "i", "it", "not", "as", "you", "was", "but", "be", "they", "at", "one", "have", "from", "or", "had", "an", "so", "all", "we", "when", "there", "can", "are"}

        for _, row in sub_df.iterrows():
            text = str(row['review_text']).lower()
            rating = row['rating']
            # Chỉ lấy các từ thuần chữ cái tiếng Anh từ 3 ký tự trở lên, loại bỏ ký tự đặc biệt/dấu câu
            words = re.findall(r'\b[a-z]{3,}\b', text)
            
            for w in set(words): # Dùng set để mỗi từ chỉ tính 1 lần trong 1 review
                if w not in stopwords:
                    all_words.append({'word': w, 'rating': rating})
        
        if not all_words:
            continue
            
        df_words = pd.DataFrame(all_words)
        word_stats = df_words.groupby('word').agg(
            avg_rating=('rating', 'mean'),
            count=('rating', 'count')
        ).reset_index()
        
        # Bắt buộc từ khóa phải xuất hiện ít nhất 10 lần mới đưa vào thống kê để đảm bảo độ tin cậy
        word_stats = word_stats[word_stats['count'] >= 10]
        
        top_pos = word_stats.sort_values(by='avg_rating', ascending=False).head(10)
        top_neg = word_stats.sort_values(by='avg_rating', ascending=True).head(10)
        
        print("  [+] TOP TỪ KHÓA TÍCH CỰC (Kéo điểm rating cao):")
        for _, r in top_pos.iterrows():
            print(f"      - '{r['word']}' (Rating TB: {r['avg_rating']:.2f} | Tần suất: {r['count']} lần)")
              
        print("\n  [-] TOP TỪ KHÓA TIÊU CỰC (Kéo điểm rating thấp):")
        for _, r in top_neg.iterrows():
            print(f"      - '{r['word']}' (Rating TB: {r['avg_rating']:.2f} | Tần suất: {r['count']} lần)")


if __name__ == "__main__":
    try:
        analyze_question_1_volume_vs_rating()
        analyze_question_2_keywords_impact()
    finally:
        conn.close()