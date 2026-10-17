import os
import json

LOCAL_RESTAURANTS_DIR = "code/kien/data/raw/single_restaurants"

def clean_zero_review_files():
    if not os.path.exists(LOCAL_RESTAURANTS_DIR):
        print(f"[Error] Không tìm thấy thư mục: {LOCAL_RESTAURANTS_DIR}")
        return

    files = [f for f in os.listdir(LOCAL_RESTAURANTS_DIR) if f.endswith(".json")]
    print(f"[Start] Tổng số file quét thấy: {len(files)}")
    
    deleted_count = 0
    kept_count = 0
    locked_count = 0

    for file_name in files:
        file_path = os.path.join(LOCAL_RESTAURANTS_DIR, file_name)
        try:
            # Mở file đọc an toàn
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            reviews = data.get("reviews", [])
            reviews_count = int(data.get("reviews_count", len(reviews)))
            
            # Nếu nhà hàng không có review nào -> Xóa file
            if reviews_count == 0 or len(reviews) == 0:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except PermissionError:
                    # File đang bị tiến trình khác chiếm quyền
                    locked_count += 1
            else:
                kept_count += 1
                
        except PermissionError:
            locked_count += 1
        except Exception as e:
            # Bỏ qua lỗi JSON không hợp lệ hoặc file đang bị khóa
            pass

    print("\n--- KẾT QUẢ DỌN DẸP ---")
    print(f"🗑️ Đã xóa: {deleted_count} nhà hàng không có review.")
    print(f"✅ Đã giữ lại: {kept_count} nhà hàng có review.")
    print(f"🔒 Bỏ qua (đang bị tiến trình khác sử dụng/khóa): {locked_count} file.")

if __name__ == "__main__":
    clean_zero_review_files()