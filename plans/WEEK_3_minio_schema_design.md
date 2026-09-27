# MinIO Storage Schema Design

## 1. Cấu trúc lưu trữ

Mỗi **restaurant = 1 MinIO object**.

```text
food-review-data/
└── <source>/
    └── raw/
        └── <city>/
            └── <restaurant_id>/
                └── restaurant.json
```

Ví dụ:

```text
food-review-data/
└── foody/
    └── raw/
        └── dien-bien/
            ├── 646075/
            │   └── restaurant.json
            ├── 896238/
            │   └── restaurant.json
            └── 1025860/
                └── restaurant.json
```

Object key dùng để lưu trong PostgreSQL:

```text
foody/raw/dien-bien/646075/restaurant.json
```

---

## 2. Cấu trúc `restaurant.json`

Mỗi object chứa metadata nhà hàng và toàn bộ review của nhà hàng đó.

```json
{
  "source": "foody",
  "platform": "foody_shoppefood",
  "crawl_timestamp": "2026-09-27T14:00:00",

  "restaurant": {
    "restaurant_id": "646075",
    "name": "Phở Vược",
    "address": "...",
    "url": "...",
    "city": "dien-bien"
  },

  "review_summary": {
    "total_reviews_api": 188,
    "total_reviews_crawled": 188
  },

  "reviews": [
    {
      "Id": 17706333,
      "Title": "Phở Vược",
      "Description": "...",
      "AvgRating": 8.0,
      "CreatedDate": "...",
      "...": "giữ nguyên các field raw từ source"
    }
  ]
}
```

### Quy ước

- Giữ raw data gần nguyên cấu trúc source.
- Không ép các source khác nhau phải có cùng feature trong MinIO.
- `restaurant_id` dùng đúng ID gốc của source.
- Tên folder thành phố dùng dạng slug thống nhất, ví dụ:
  - `ho-chi-minh`
  - `ha-noi`
  - `dien-bien`
- Mỗi folder restaurant chỉ chứa object raw của chính restaurant đó.
- Khi crawl lại cùng restaurant, ghi đè `restaurant.json` bằng dữ liệu mới nhất.

---

## 3. Mapping PostgreSQL ↔ MinIO

PostgreSQL lưu:

```text
source_restaurant_id = 646075

raw_object_key =
foody/raw/dien-bien/646075/restaurant.json
```

Mapping:

```text
restaurants.id
      ↓
restaurants.raw_object_key
      ↓
MinIO object
      ↓
restaurant.json
      ↓
restaurant metadata + toàn bộ raw reviews
```

Review không cần lưu `raw_object_key` riêng vì đã liên kết tới restaurant qua:

```text
reviews.restaurant_id
        ↓
restaurants.id
        ↓
restaurants.raw_object_key
```

Nhờ đó mỗi restaurant chỉ có một đường dẫn raw duy nhất trong hệ thống.
