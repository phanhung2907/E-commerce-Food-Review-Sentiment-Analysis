# Foody Data Crawl Report

## 1. Luồng crawl dữ liệu

Pipeline sử dụng **Foody internal API + Python `requests`** để thu thập danh sách nhà hàng và review, sau đó lưu raw data và upload lên MinIO.

```text
foody_locations.txt
        ↓
foody_restaurant_crawler.py
        ↓
HomeListPlace
        ↓
restaurants.csv
        ↓
foody_review_crawler.py
        ↓
ResLoadMore
        ↓
reviews_YYYY-MM-DD.json
        ↓
minio_uploader.py
        ↓
MinIO
```

### Restaurant crawler

- Đọc các endpoint tỉnh/thành từ `foody_locations.txt`.
- Gọi endpoint:

```text
/__get/Place/HomeListPlace
```

- Crawl tuần tự từng page.
- Deduplicate restaurant theo `restaurant_id` hoặc URL.
- Dừng khi API không còn trả restaurant mới.
- Output:

```text
restaurants.csv
```

Các field chính:

```text
restaurant_id
name
address
url
city
```

### Review crawler

- Đọc từng `restaurant_id` từ `restaurants.csv`.
- Gọi endpoint:

```text
/__get/Review/ResLoadMore
```

- Mỗi request lấy một batch review.
- Pagination tiếp tục bằng `LastId` và `ExcludeIds`.
- Không dùng `Total` làm điều kiện dừng vì Foody có thể cap giá trị này ở `100`.
- Dừng khi:
  - API trả `Items` rỗng;
  - không còn review mới;
  - không còn cursor;
  - cursor bị lặp;
  - hoặc đạt giới hạn do người dùng nhập ở chế độ crawl giới hạn.

Pipeline hỗ trợ 2 mode:

```text
1. Vét cạn
   → toàn bộ restaurant
   → toàn bộ review

2. Giới hạn
   → N restaurant / tỉnh
   → M review / restaurant
```

---

## 2. Cấu trúc dữ liệu

Local raw data:

```text
code/hung/data/
└── foody_shoppefood/
    └── raw/
        └── <city>/
            ├── restaurants.csv
            └── reviews_YYYY-MM-DD.json
```

### `restaurants.csv`

```text
restaurant_id
name
address
url
city
```

File này đóng vai trò index nhà hàng để review crawler sử dụng `restaurant_id` làm `ResId`.

### `reviews_YYYY-MM-DD.json`

Cấu trúc tổng quát:

```text
root
├── source
├── platform
├── city
├── crawl_date
├── crawl_timestamp
├── total_restaurants
├── total_reviews
└── restaurants[]
    ├── restaurant
    │   ├── restaurant_id
    │   ├── name
    │   ├── address
    │   ├── url
    │   └── city
    │
    ├── review_summary
    │   ├── total_reviews_api
    │   └── total_reviews_crawled
    │
    └── reviews[]
        ├── Id
        ├── Title
        ├── Description
        ├── AvgRating
        ├── CreatedDate
        ├── DeviceName
        ├── TotalViews
        ├── TotalPictures
        ├── Pictures
        ├── Owner
        ├── Options
        ├── TotalLike
        ├── TotalComment
        ├── Comments
        ├── ResId
        └── crawler metadata
```

Crawler bổ sung một số metadata vào mỗi review:

```text
source
restaurant_id_query
restaurant_name
restaurant_city
crawl_timestamp
```

Raw layer giữ gần nguyên response của Foody để tránh mất feature trước bước ETL.

---

## 3. Tổng kết

Pipeline hiện tại:

```text
Foody internal API
→ Restaurant discovery
→ Review pagination
→ Raw CSV/JSON
→ MinIO
```

Ưu điểm chính:

- không phụ thuộc public dataset;
- không cần browser automation trong luồng crawl chính;
- hỗ trợ nhiều tỉnh/thành;
- hỗ trợ vét cạn hoặc crawl theo giới hạn;
- có pagination, deduplicate, retry và rate delay;
- giữ raw data đầy đủ để phục vụ ETL, EDA và sentiment analysis.

Lưu ý chính: endpoint của Foody là internal API nên có thể thay đổi; cần giữ delay giữa request và không dùng riêng field `Total` để xác định đã crawl hết review.
