import os
import json

def clean_and_deduplicate_data():
    output_dir = "code/kien/data/raw/enterprise_100k"
    
    if not os.path.exists(output_dir):
        print("Thư mục chứa dữ liệu không tồn tại!")
        return

    seen_review_ids = set()
    all_unique_records = []
    total_raw_count = 0

    print("--- ĐANG TIẾN HÀNH LỌC VÀ GỘP DỮ LIỆU SẠCH ---")
    
    # 1. Đọc toàn bộ các file part hiện có
    for filename in sorted(os.listdir(output_dir)):
        if filename.startswith("tripadvisor_part_") and filename.endswith(".json"):
            file_path = os.path.join(output_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_raw_count += len(data)
                    
                    for item in data:
                        review_id = item.get("review_id") or item.get("id")
                        
                        # Nếu tìm thấy review_id và chưa từng xuất hiện -> Lưu lại
                        if review_id:
                            if review_id not in seen_review_ids:
                                seen_review_ids.add(review_id)
                                all_unique_records.append(item)
                        else:
                            # Phòng hờ trường hợp không có ID thì cứ giữ lại để tránh mất mát
                            all_unique_records.append(item)
            except Exception as e:
                print(f"Lỗi khi đọc file {filename}: {e}")

    print(f"Tổng số bản ghi ban đầu (gồm trùng): {total_raw_count:,}")
    print(f"Số lượng bản ghi độc lập sau khi lọc trùng: {len(all_unique_records):,}")
    print(f"Đã loại bỏ thành công: {total_raw_count - len(all_unique_records):,} bản ghi trùng lặp.")

    # 2. Ghi lại dữ liệu sạch theo cơ chế chia phần (mỗi file tối đa 10,000 bản ghi chuẩn chỉnh)
    chunk_size = 10000
    for i in range(0, len(all_unique_records), chunk_size):
        chunk_data = all_unique_records[i:i + chunk_size]
        part_num = (i // chunk_size) + 1
        new_filename = f"tripadvisor_part_{part_num}.json"
        new_file_path = os.path.join(output_dir, new_filename)
        
        with open(new_file_path, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=4)
        print(f"Đã ghi lại file sạch: {new_filename} ({len(chunk_data):,} bản ghi)")

    print("---------------------------------------")
    print("🎉 Hoàn tất dọn dẹp! Dữ liệu của bạn giờ đây hoàn toàn sạch và không bị trùng lặp.")

if __name__ == "__main__":
    clean_and_deduplicate_data()