import pandas as pd
import os
from collections import Counter
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "../../data/processed/data_clean.csv")

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    text_data = " ".join(df['review_text'].dropna().astype(str).str.lower())
    words = re.findall(r'\b[a-z]{3,}\b', text_data)
    
    # Loại bỏ các từ dừng tiếng Anh thông dụng
    stopwords = set(['the', 'and', 'was', 'for', 'with', 'that', 'this', 'you', 'not', 'but', 'are', 'from', 'they', 'have', 'all', 'had', 'were', 'his', 'her', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'its', 'food', 'restaurant', 'good', 'place', 'very'])
    filtered_words = [w for w in words if w not in stopwords]
    
    top_words = Counter(filtered_words).most_common(10)
    print("Top 10 từ khóa phổ biến:", top_words)