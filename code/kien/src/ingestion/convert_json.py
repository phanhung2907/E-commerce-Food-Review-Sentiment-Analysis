import pandas as pd
from pathlib import Path

# Xác định đường dẫn file CSV đã làm sạch và file JSON đầu ra
csv_path = Path("code/kien/data/processed/tripadvisor_cleaned.csv")
json_path = Path("code/kien/data/processed/tripadvisor_cleaned.json")

# Đọc file CSV
df = pd.read_csv(csv_path)

# Xuất ra định dạng JSON
df.to_json(json_path, orient='records', force_ascii=False, indent=4)

print(f"Đã tạo file JSON thành công tại: {json_path}")