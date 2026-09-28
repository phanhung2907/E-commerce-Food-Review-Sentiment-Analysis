import os
import json

output_dir = "code/kien/data/raw/enterprise_100k"

if not os.path.exists(output_dir):
    print("Thư mục chứa dữ liệu chưa tồn tại!")
else:
    total_records = 0
    print("--- THỐNG KÊ TIẾN ĐỘ CÀO DỮ LIỆU ---")
    for filename in sorted(os.listdir(output_dir)):
        if filename.startswith("tripadvisor_part_") and filename.endswith(".json"):
            file_path = os.path.join(output_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = len(data)
                    total_records += count
                    print(f"File {filename}: {count:,} bản ghi")
            except Exception as e:
                print(f"Lỗi đọc file {filename}: {e}")
                
    print("---------------------------------------")
    print(f"TỔNG CỘNG TÍCH LŨY: {total_records:,} bản ghi")