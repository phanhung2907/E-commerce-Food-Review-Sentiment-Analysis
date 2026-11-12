import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = os.getenv('POSTGRES_DB', 'food_review')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres123')

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def run_detailed_eda():
    print("\n" + "="*75)
    print("EDA MỞ RỘNG 1: KIỂM TOÁN CHẤT LƯỢNG & TỶ LỆ MISSING/NULL THEO NGUỒN")
    print("="*75)
    sql_quality = """
        SELECT 
            source_code,
            COUNT(*) AS total_rows,
            COUNT(review_text) FILTER (WHERE TRIM(review_text) <> '') AS valid_text_count,
            ROUND(100.0 * (COUNT(*) - COUNT(review_text) FILTER (WHERE TRIM(review_text) <> '')) / COUNT(*), 2) AS missing_text_pct,
            COUNT(rating) AS valid_rating_count,
            ROUND(100.0 * (COUNT(*) - COUNT(rating)) / COUNT(*), 2) AS missing_rating_pct,
            COUNT(review_date) AS valid_date_count,
            ROUND(100.0 * (COUNT(*) - COUNT(review_date)) / COUNT(*), 2) AS null_date_pct,
            COUNT(language) AS valid_lang_count,
            ROUND(100.0 * (COUNT(*) - COUNT(language)) / COUNT(*), 2) AS null_lang_pct
        FROM reviews
        GROUP BY source_code;
    """
    df_quality = pd.read_sql_query(sql_quality, engine)
    print(df_quality.to_string(index=False))

    print("\n" + "="*75)
    print("EDA MỞ RỘNG 2: PHÂN PHỐI CHI TIẾT ĐIỂM RATING (CHUẨN HÓA THANG 10) THEO NGUỒN")
    print("="*75)
    sql_rating_dist = """
        SELECT 
            source_code,
            ROUND(rating * 2.0, 1) AS rating_scale_10,
            COUNT(*) AS review_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY source_code), 2) AS percentage
        FROM reviews
        WHERE rating IS NOT NULL
        GROUP BY source_code, ROUND(rating * 2.0, 1)
        ORDER BY source_code, rating_scale_10;
    """
    df_dist = pd.read_sql_query(sql_rating_dist, engine)
    print(df_dist.to_string(index=False))

    print("\n" + "="*75)
    print("EDA MỞ RỘNG 3: THỐNG KÊ MÔ TẢ (MEAN, STD, MEDIAN, IQR) TRÊN THANG ĐIỂM 10")
    print("="*75)
    sql_stats = """
        WITH rest_summary AS (
            SELECT 
                rest.source_code,
                rest.source_restaurant_id,
                COUNT(rev.source_review_id) AS rev_cnt,
                AVG(rev.rating * 2.0) AS avg_rat_scale10
            FROM restaurants rest
            JOIN reviews rev 
                ON rest.source_code = rev.source_code 
                AND rest.source_restaurant_id = rev.source_restaurant_id
            WHERE rev.rating IS NOT NULL
            GROUP BY rest.source_code, rest.source_restaurant_id
        )
        SELECT 
            source_code,
            COUNT(*) AS total_active_restaurants,
            ROUND(AVG(rev_cnt), 2) AS mean_reviews_per_rest,
            ROUND(STDDEV(rev_cnt), 2) AS std_reviews_per_rest,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rev_cnt) AS q25_reviews,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rev_cnt) AS median_reviews,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rev_cnt) AS q75_reviews,
            MAX(rev_cnt) AS max_reviews_rest,
            ROUND(AVG(avg_rat_scale10)::numeric, 2) AS mean_rest_rating_scale10,
            ROUND(STDDEV(avg_rat_scale10)::numeric, 2) AS std_rest_rating_scale10
        FROM rest_summary
        GROUP BY source_code;
    """
    df_stats = pd.read_sql_query(sql_stats, engine)
    print(df_stats.to_string(index=False))

    print("\n" + "="*75)
    print("EDA MỞ RỘNG 4: PHÂN TÍCH ĐỘ DÀI VĂN BẢN THEO MỨC ĐỘ HÀI LÒNG (THANG 10)")
    print("="*75)
    sql_text_len = """
        SELECT 
            source_code,
            CASE 
                WHEN (rating * 2.0) <= 4.0 THEN '1. Tiêu cực (2.0-4.0 điểm)'
                WHEN (rating * 2.0) = 6.0 THEN '2. Trung lập (6.0 điểm)'
                ELSE '3. Tích cực (8.0-10.0 điểm)'
            END AS sentiment_group_scale10,
            COUNT(*) AS total_reviews,
            ROUND(AVG(LENGTH(TRIM(review_text))), 1) AS avg_char_length,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY LENGTH(TRIM(review_text))) AS median_char_length,
            ROUND(AVG(ARRAY_LENGTH(REGEXP_SPLIT_TO_ARRAY(TRIM(review_text), '\\s+'), 1)), 1) AS avg_word_count
        FROM reviews
        WHERE review_text IS NOT NULL AND TRIM(review_text) <> '' AND rating IS NOT NULL
        GROUP BY source_code, sentiment_group_scale10
        ORDER BY source_code, sentiment_group_scale10;
    """
    df_len = pd.read_sql_query(sql_text_len, engine)
    print(df_len.to_string(index=False))

if __name__ == "__main__":
    run_detailed_eda()