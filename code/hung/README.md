# Food Review Sentiment Analysis — `code/hung`

## 1. Mục tiêu

Module này chứa pipeline chính để thu thập và lưu trữ dữ liệu Foody/ShopeeFood phục vụ project **Food Review Sentiment Analysis**.

```text
Foody endpoints
    ↓
Restaurant crawler
    ↓
Review crawler
    ↓
Raw data
    ↓
MinIO
    ↓
ETL / SQL / Python / Visualization / Modeling
```

## 2. Cấu trúc chính

```text
code/hung/
├── configs/
│   └── foody_locations.txt
├── data/
│   └── foody_shoppefood/
│       └── raw/
│           └── <city>/
│               ├── restaurants.csv
│               └── reviews_YYYY-MM-DD.json
└── src/
    ├── ingestion/
    │   └── foody-shoppefood/
    │       ├── foody_restaurant_crawler.py
    │       ├── foody_review_crawler.py
    │       └── run_pipeline.py
    ├── storage/
    │   └── minio_uploader.py
    ├── processing/
    ├── modeling/
    └── utils/
```

## 3. Setup môi trường

Project dùng `uv`.

```bash
uv --version
uv sync
```

Nếu thiếu dependency:

```bash
uv add requests minio python-dotenv
```

Nếu terminal đang active virtual environment cũ và xuất hiện warning `VIRTUAL_ENV ... does not match ...`:

```bash
deactivate
uv sync
```

Sau đó tiếp tục dùng `uv run`.

## 4. Cấu hình location Foody

File:

```text
code/hung/configs/foody_locations.txt
```

Ví dụ:

```text
https://www.foody.vn/gia-lai
https://www.foody.vn/binh-dinh
https://www.foody.vn/
```

- Mỗi dòng là một location URL.
- Dòng trống được bỏ qua.
- Dòng bắt đầu bằng `#` là comment.
- Root `https://www.foody.vn/` được hiểu là TP.HCM.
- Không cần cấu hình `lat/lon`.

## 5. Crawl restaurant

Script:

```text
code/hung/src/ingestion/foody-shoppefood/foody_restaurant_crawler.py
```

Chạy từ repo root:

```bash
uv run python code\hung\src\ingestion\foody-shoppefood\foody_restaurant_crawler.py
```

Output:

```text
code/hung/data/foody_shoppefood/raw/<city>/restaurants.csv
```

CSV gồm 5 field:

```text
restaurant_id
name
address
url
city
```

`restaurant_id` chính là `ResId` dùng cho bước crawl review.

## 6. Crawl review

Script:

```text
code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py
```

Chạy:

```bash
uv run python code\hung\src\ingestion\foody-shoppefood\foody_review_crawler.py
```

Script sẽ:

1. quét tất cả `restaurants.csv`;
2. lấy từng `ResId`;
3. gọi Foody `ResLoadMore`;
4. phân trang bằng `LastId`;
5. lưu review theo city.

Output:

```text
code/hung/data/foody_shoppefood/raw/<city>/reviews_YYYY-MM-DD.json
```

Crawler giữ các field review từ Foody và thêm metadata:

```text
source
restaurant_id_query
restaurant_name
restaurant_city
crawl_timestamp
```

## 7. MinIO

Ví dụ `.env`:

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=food-review-data
MINIO_SECURE=false
```

Thay credential theo Docker Compose thực tế.

Chạy uploader:

```bash
uv run python code\hung\src\storage\minio_uploader.py
```

Local:

```text
code/hung/data/foody_shoppefood/raw/gia-lai/
```

được mirror lên MinIO:

```text
food-review-data/
└── foody_shoppefood/
    └── raw/
        └── gia-lai/
```

## 8. Chạy toàn bộ pipeline

Script:

```text
code/hung/src/ingestion/foody-shoppefood/run_pipeline.py
```

Chạy từ **repo root**:

```bash
uv run python code\hung\src\ingestion\foody-shoppefood\run_pipeline.py
```

Thứ tự:

```text
1. foody_restaurant_crawler.py
2. foody_review_crawler.py
3. minio_uploader.py
```

Nếu một bước lỗi, pipeline dừng để tránh chạy tiếp với dữ liệu chưa hoàn chỉnh.

## 9. Docker services

Các service chính:

```text
MinIO        : object storage
PostgreSQL   : structured / analytical data
CloudBeaver  : database UI
```

Khởi động:

```bash
docker compose up -d
docker compose ps
```

Thông thường:

```text
MinIO API     : localhost:9000
MinIO Console : localhost:9001
CloudBeaver   : localhost:8978
```

Port thực tế phụ thuộc `.env` và `docker-compose.yml`.

## 10. Data flow tiếp theo

Crawler hiện tập trung vào **raw layer**.

```text
raw
 ↓
processing / cleaning
 ↓
processed
 ↓
curated / analytics
```

Các bước tiếp theo nên đặt trong `src/processing/`:

- normalize date;
- xử lý HTML entity;
- remove duplicate;
- xử lý missing value;
- chuẩn hóa rating;
- clean/tokenize Vietnamese text;
- tạo dataset sentiment analysis.

## 11. Scripts quan trọng

| Script | Chức năng |
|---|---|
| `foody_restaurant_crawler.py` | Crawl restaurant metadata |
| `foody_review_crawler.py` | Crawl review theo `ResId` |
| `minio_uploader.py` | Upload raw data lên MinIO |
| `run_pipeline.py` | Chạy toàn bộ pipeline |

## 12. Workflow khuyến nghị

Thông thường chỉ cần:

```bash
docker compose up -d
uv run python code\hung\src\ingestion\foody-shoppefood\run_pipeline.py
```

Sau đó kiểm tra:

```text
code/hung/data/foody_shoppefood/raw/
```

và MinIO:

```text
food-review-data/foody_shoppefood/raw/
```

Từ đây dữ liệu được chuyển sang ETL, PostgreSQL, EDA, sentiment analysis, visualization và modeling.
