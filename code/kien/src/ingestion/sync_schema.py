import pandas as pd
import numpy as np

# 1. Đọc file CSV dữ liệu của bạn từ thư mục processed
df = pd.read_csv('code/kien/data/processed/all_reviews_final_report.csv')

# 2. Đổi tên các cột hiện có cho khớp với Schema chuẩn của nhóm
df = df.rename(columns={
    'restaurant_id': 'source_restaurant_id',
    'review_id': 'source_review_id'
})

# 3. Tạo danh sách 19 cột chuẩn theo yêu cầu của nhóm trưởng
schema_columns = [
    'source_code', 'source_review_id', 'source_restaurant_id', 'reviewer_id',
    'reviewer_name_raw', 'review_title', 'review_text', 'rating', 'review_date',
    'language', 'device_name', 'total_views', 'total_pictures', 'total_likes',
    'total_comments', 'guest_count', 'visit_again', 'money_spend', 'feature_depth_status'
]

# 4. Thêm các cột bị thiếu và gán giá trị NaN (tương đương giá trị NULL)
for col in schema_columns:
    if col not in df.columns:
        df[col] = np.nan

# 5. Gán giá trị mặc định cho cột nguồn (source_code)
df['source_code'] = 'tripadvisor'

# 6. Lọc và sắp xếp lại đúng 19 cột theo thứ tự chuẩn, loại bỏ các cột thừa ngoài schema
df_final = df[schema_columns]

# 7. Lưu lại thành file CSV mới đã được chuẩn hóa
df_final.to_csv('code/kien/data/processed/data_da_chuan_hoa.csv', index=False)
print("Đã chuẩn hóa xong! File mới được lưu tại: code/kien/data/processed/data_da_chuan_hoa.csv")