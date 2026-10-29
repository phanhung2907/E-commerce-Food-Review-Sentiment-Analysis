import os
import json
from collections import Counter

local_dir = "code/kien/data/raw/single_restaurants"
rating_counter = Counter()
total_files = 0
total_reviews = 0

if not os.path.exists(local_dir):
    print(f"Không tìm thấy thư mục: {local_dir}")
else:
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            total_files += 1
            file_path = os.path.join(local_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    reviews = data.get("reviews", [])
                    for r in reviews:
                        rating = r.get("rating")
                        rating_counter[rating] += 1
                        total_reviews += 1
            except Exception as e:
                continue

    print(f"Đã quét qua {total_files} file nhà hàng (Tổng số review: {total_reviews})")
    print("--- KẾT QUẢ PHÂN PHỐI RATING ---")
    for score in sorted(rating_counter.keys(), reverse=True):
        count = rating_counter[score]
        percent = (count / total_reviews * 100) if total_reviews > 0 else 0
        print(f" - {score} sao: {count} bài review ({percent:.2f}%)")