import os

# Đường dẫn đến thư mục chứa các file JSON nhà hàng mới
folder_path = "code/kien/data/raw/single_restaurants"

if os.path.exists(folder_path):
    # Lọc ra tất cả các file có đuôi .json
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    
    print(f"==================================================")
    print(f" KẾT QUẢ KIỂM TRA SỐ LƯỢNG FILE JSON MỚI")
    print(f"==================================================\n")
    print(f"📁 Thư mục: {folder_path}")
    print(f"📊 Tổng số file JSON (nhà hàng): {len(json_files):,} file")
    print(f"==================================================\n")
    
    # In thử 5 tên file đầu tiên để kiểm chứng
    if json_files:
        print("💡 Mẫu vài file JSON đầu tiên trong thư mục:")
        for fname in json_files[:5]:
            print(f" - {fname}")
else:
    print(f"[ERROR] Không tìm thấy thư mục: {folder_path}")