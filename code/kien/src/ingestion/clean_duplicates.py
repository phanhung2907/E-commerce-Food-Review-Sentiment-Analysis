import json
import os


def clean_duplicate_restaurants():
  local_dir = "code/kien/data/raw/single_restaurants"
  if not os.path.exists(local_dir):
    print(f"Thư mục {local_dir} không tồn tại.")
    return

  files = [f for f in os.listdir(local_dir) if f.endswith(".json")]
  restaurant_dict = {}

  # Gom nhóm các file theo restaurant_id
  for file_name in files:
    file_path = os.path.join(local_dir, file_name)
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        r_id = data.get("restaurant_id")
        if not r_id:
          continue

        if r_id not in restaurant_dict:
          restaurant_dict[r_id] = []
        restaurant_dict[r_id].append(
            {"file_path": file_path, "file_name": file_name}
        )
    except Exception as e:
      print(f"Lỗi đọc file {file_name}: {e}")

  deleted_count = 0

  # Xử lý từng nhóm trùng lặp
  for r_id, items in restaurant_dict.items():
    if len(items) > 1:
      # Ưu tiên giữ lại file không có chữ '_NA' trong tên (tên nhà hàng đầy đủ hơn)
      items.sort(
          key=lambda x: (
              0 if "_NA" not in x["file_name"] else 1,
              len(x["file_name"]),
          ),
          reverse=True,
      )

      keep_item = items[0]  # Giữ file tốt nhất
      print(f"\n[Giữ lại] {keep_item['file_name']} (ID: {r_id})")

      # Xóa các file thừa còn lại trong nhóm
      for duplicate in items[1:]:
        print(f"  -> [Xóa trùng] {duplicate['file_name']}")
        os.remove(duplicate["file_path"])
        deleted_count += 1

  print(f"\n[XONG] Đã dọn dẹp sạch sẽ! Đã xóa thành công {deleted_count} file thừa.")


if __name__ == "__main__":
  clean_duplicate_restaurants()