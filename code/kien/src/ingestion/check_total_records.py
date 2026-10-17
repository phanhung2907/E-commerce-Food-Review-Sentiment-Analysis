import json
import os


def count_total_records():
  local_dir = "code/kien/data/raw/single_restaurants"
  if not os.path.exists(local_dir):
    print(f"Thư mục {local_dir} chưa tồn tại.")
    return

  files = [f for f in os.listdir(local_dir) if f.endswith(".json")]
  total_restaurants = len(files)
  total_reviews = 0

  for file_name in files:
    file_path = os.path.join(local_dir, file_name)
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Đếm số lượng review trong mỗi file nhà hàng
        reviews = data.get("reviews", [])
        total_reviews += len(reviews)
    except Exception as e:
      print(f"Lỗi khi đọc file {file_name}: {e}")

  print(f"--- THỐNG KÊ TỔNG DỮ LIỆU ---")
  print(f"Tổng số nhà hàng (Files): {total_restaurants}")
  print(f"Tổng số lượng review (Records): {total_reviews}")


if __name__ == "__main__":
  count_total_records()