import pandas as pd
from collections import Counter
import re

# 1. Đọc file dữ liệu đã chuẩn hóa schema
df = pd.read_csv('code/kien/data/processed/data_da_chuan_hoa.csv')

# Đảm bảo cột rating và review_text đúng định dạng
df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df['review_text'] = df['review_text'].fillna('').astype(str)

# 2. Lọc ra các review có rating = 1.0 (Đánh giá 1 sao)
df_1_star = df[df['rating'] == 1.0]
print(f"Tổng số lượng review 1 sao: {len(df_1_star)}")

# 3. Hàm làm sạch và tách từ cơ bản
def extract_words(text):
    text = text.lower()
    # Lấy các từ tiếng Việt và tiếng Anh (bao gồm có dấu)
    words = re.findall(r'\b[a-zA-Zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+\b', text)
    return words

# Gom toàn bộ text của 1 sao lại
all_words_1_star = []
for text in df_1_star['review_text']:
    all_words_1_star.extend(extract_words(text))

# 4. Loại bỏ các từ dừng tiếng Việt cơ bản (stopwords) thường gặp không mang nhiều ý nghĩa phản ánh lỗi
stopwords = {
    và, là, của, có, cho, các, nhưng, không, bị, một,được, thì, mà, đã, lại, với, về, trong, quá, rất, thì, là, mà, những, này, đó,đến, đi, ăn, quán, nhà, hàng
} # Bạn có thể bổ sung thêm tùy ý
filtered_words = [word for word in all_words_1_star if word not in stopwords and len(word) > 1]

# 5. Thống kê Top các từ khóa xuất hiện nhiều nhất trong nhóm 1 sao
word_counts = Counter(filtered_words)
print("\n--- TOP 20 FATAL KEYWORDS (Từ khóa xuất hiện nhiều nhất ở review 1 sao) ---")
for word, freq in word_counts.most_common(20):
    print(f"- Từ: '{word}' | Tần suất xuất hiện: {freq} lần")