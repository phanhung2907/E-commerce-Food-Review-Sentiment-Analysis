import os
import json

# Đường dẫn đến thư mục chứa các file JSON nhà hàng
local_dir = "code/kien/data/raw/single_restaurants"

deleted_count = 0

if os.path.exists(local_dir):
    print("Đang quét và xóa các file rác chứa 'Vietnam_Subregion'...")
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                raw_city = str(data.get("city", ""))
                
                # Nếu phát hiện chứa "Vietnam_Subregion", tiến hành xóa file
                if "Vietnam_Subregion" in raw_city:
                    os.remove(file_path)
                    deleted_count += 1
            except Exception as e:
                print(f"Lỗi khi đọc file {file_name}: {e}")

    print(f"\n[SUCCESS] Đã xóa thành công {deleted_count} file JSON chứa 'Vietnam_Subregion' khỏi thư mục!")
else:
    print(f"[Error] Không tìm thấy thư mục: {local_dir}")