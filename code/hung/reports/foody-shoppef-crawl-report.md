# Foody–ShopeeFood Crawl Report

## 1. Mục tiêu

Thu thập dữ liệu nhà hàng và review phục vụ project **Food Review Sentiment Analysis**, ưu tiên dữ liệu tự crawl thay vì public dataset.

## 2. Các hướng đã thử

### ShopeeFood API trực tiếp
- Lấy request từ DevTools và thử gọi lại bằng `requests`.
- Gặp HTTP `403`, phụ thuộc token/session/browser fingerprint.
- Khó tái sử dụng ổn định và tốn thời gian reverse-engineer.

**Đánh giá:** dữ liệu tốt nhưng anti-bot mạnh, không phù hợp làm pipeline chính.

### Playwright / browser automation
- Thử mở Foody/ShopeeFood bằng browser thật.
- Có thể quan sát network/DOM nhưng load chậm, đôi lúc treo và khó scale.

**Đánh giá:** phù hợp để khám phá request, không phù hợp làm crawler chính.

### Foody internal API
Phát hiện hai endpoint ổn định hơn:

- `HomeListPlace`: lấy danh sách nhà hàng.
- `ResLoadMore`: lấy review theo `ResId`, phân trang bằng `LastId`.

Dùng Python `requests` cho tốc độ và độ ổn định tốt hơn.

## 3. Pipeline cuối cùng

```text
foody_locations.txt
        ↓
foody_restaurant_crawler.py
        ↓
restaurants.csv
        ↓
foody_review_crawler.py
        ↓
reviews_YYYY-MM-DD.json
        ↓
minio_uploader.py
        ↓
MinIO
```

Cấu trúc dữ liệu:

```text
code/hung/data/
└── foody_shoppefood/
    └── raw/
        └── <city>/
            ├── restaurants.csv
            └── reviews_YYYY-MM-DD.json
```

## 4. Đánh giá tổng quan

### Ưu điểm
- Không phụ thuộc public dataset.
- Không cần browser automation khi crawl chính.
- Dễ mở rộng nhiều thành phố.
- Có phân trang, retry và deduplicate.
- Raw review được giữ gần nguyên response API để phục vụ ETL.
- Dễ tích hợp MinIO và PostgreSQL.

### Hạn chế
- Endpoint nội bộ có thể thay đổi.
- Coverage phụ thuộc Foody.
- Cần phân biệt field gốc API và metadata do crawler thêm.
- Cần rate limit để tránh gửi request quá nhanh.

## 5. Kết luận

Phương án phù hợp nhất hiện tại là:

> **Foody internal API + Python requests + CSV/JSON raw + MinIO**

ShopeeFood direct API và Playwright hữu ích trong giai đoạn khảo sát, nhưng pipeline Foody đơn giản hơn, dễ debug, dễ tái chạy và phù hợp hơn với workflow Data Science.
