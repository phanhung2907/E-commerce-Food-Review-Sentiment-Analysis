import os
import json

def check_duplicate_reviews():
    output_dir = "code/kien/data/raw/enterprise_100k"
    
    if not os.path.exists(output_dir):
        print("Thư mục chứa dữ liệu không tồn tại!")
        return

    all_review_ids = set()
    total_records = 0
    duplicate_count = 0

    print("--- ĐANG KIỂM TRA TRÙNG LẶP DỮ LIỆU ---")
    
    for filename in sorted(os.listdir(output_dir)):
        if filename.startswith("tripadvisor_part_") and filename.endswith(".json"):
            file_path = os.path.join(output_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    file_records = len(data)
                    total_records += file_records
                    
                    for item in data:
                        # Giả sử trường định danh của review là 'review_id' hoặc 'id'
                        # Bạn có thể thay đổi key cho khớp với schema thực tế trong json của bạn
                        review_id = item.get("review_id") or item.get("id")
                        
                        if review_id:
                            if review_id in all_review_ids:
                                duplicate_count += 1
                            else:
                                all_review_ids.add(review_id)
            except Exception as e:
                print(f"Lỗi khi đọc file {filename}: {e}")

    print("---------------------------------------")
    print(f"Tổng số bản ghi đã quét: {total_records:,}")
    print(f"Số lượng bản ghi độc lập (Unique): {len(all_review_ids):,}")
    print(f"Số lượng bản ghi bị trùng lặp: {duplicate_count:,}")
    
    if duplicate_count == 0:
        print("Tuyệt vời! Không có bất kỳ bản ghi nào bị trùng lặp giữa các file.")
    else:
        print(f"Phát hiện có {duplicate_count} bản ghi bị trùng.")

if __name__ == "__main__":
    check_duplicate_reviews()