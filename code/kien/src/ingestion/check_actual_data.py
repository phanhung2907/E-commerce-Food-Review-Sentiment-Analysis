import json
import os


def check_local_restaurants():
  local_dir = "code/kien/data/raw/single_restaurants"

  if not os.path.exists(local_dir):
    print(f"Thư mục {local_dir} chưa tồn tại hoặc chưa có dữ liệu.")
    return

  files = [f for f in os.listdir(local_dir) if f.endswith(".json")]
  print(f"Tổng số file JSON hiện có trong thư mục local: {len(files)}")

  restaurant_ids = set()
  duplicates = []

  for file_name in files:
    file_path = os.path.join(local_dir, file_name)
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        r_id = data.get("restaurant_id")

        if r_id in restaurant_ids:
          duplicates.append((r_id, file_name))
        else:
          restaurant_ids.add(r_id)
    except Exception as e:
      print(f"Lỗi khi đọc file {file_name}: {e}")

  print(f"Số lượng restaurant_id duy nhất: {len(restaurant_ids)}")

  if duplicates:
    print(
        f"[CẢNH BÁO] Phát hiện {len(duplicates)} trường hợp bị trùng lặp ID:"
    )
    for dup in duplicates:
      print(dup)
  else:
    print("[TUYỆT VỜI] Không có bất kỳ dữ liệu nào bị trùng lặp ID cả!")


if __name__ == "__main__":
  check_local_restaurants()