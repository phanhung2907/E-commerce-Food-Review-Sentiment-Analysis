# Raw data TripAdvisor — Food Review Sentiment Analysis

Gói này chứa dữ liệu crawl TripAdvisor của cá nhân. Thành viên trong nhóm có thể giải nén và dùng pipeline hiện tại để nạp dữ liệu vào PostgreSQL Docker trên máy mình theo mô hình chuẩn 3NF.

## Cấu trúc thư mục

```text
tripadvisor_copy/
├── README_RAW_DATA.md
└── raw/
    └── single_restaurants/
        ├── crawled_restaurants.json
        ├── restaurant_431863_Versailles.json
        ├── restaurant_809040_NA.json
        └── ...
```

| Đường dẫn | Nội dung |
|---|---|
| `raw/single_restaurants/restaurant_<restaurant_id>_<name>.json` | File JSON chứa toàn bộ dữ liệu thô của từng nhà hàng TripAdvisor riêng lẻ. Đây là đầu vào chính cho các script xử lý. |
| `raw/single_restaurants/crawled_restaurants.json` | File tổng hợp danh sách các nhà hàng đã được crawl. |

Quy tắc đặt tên file: `restaurant_<restaurant_id>_<name>.json`. Ví dụ: `restaurant_431863_Versailles.json`, trong đó `431863` là ID gốc của quán trên TripAdvisor. Tham số nguồn của pipeline đối với gói này là `tripadvisor`.

## Nạp vào PostgreSQL Docker

Chạy từ thư mục gốc repo có `docker-compose.yml` và `pyproject.toml`. Giải nén ZIP vào một thư mục trên máy, ví dụ `code/kien/data/tripadvisor_copy/`, sao cho thư mục `raw/` nằm ngay bên trong. Đặt `$rawRoot` theo vị trí giải nén thực tế của bạn.

1. Kiểm tra `.env` đang trỏ tới MinIO và PostgreSQL của máy mình. Nếu chạy lệnh từ Windows host, dùng cổng được publish bởi Docker. Các biến liên quan là `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` và `POSTGRES_PASSWORD`. Nếu các service trong Compose của repo chưa chạy, dùng `docker compose up -d minio postgres`. Nếu chưa có bucket, chạy **uv run python code/kien/src/storage/setup_minio.py**. Schema cần cả migration phiên bản dữ liệu, gồm bảng **data_ingestion_versions**. Với DB mới hoặc DB chưa có migration này, chạy **uv run python code/kien/src/storage/init_postgres.py** sau khi kiểm tra cấu hình kết nối.
2. Upload dữ liệu thô lên MinIO. Lệnh dưới đây trỏ trực tiếp đến thư mục chứa các file JSON nhà hàng TripAdvisor của bạn.
3. Chạy ETL với manifest mới do uploader tạo trên máy bạn tại `$manifest`. Script đọc các object trong manifest, chuyển đổi và ghi vào các bảng chuẩn theo schema 3NF trong PostgreSQL.

```powershell
$rawRoot = 'code/kien/data/tripadvisor_copy/raw/single_restaurants'
$manifest = Join-Path (Split-Path (Split-Path $rawRoot -Parent) -Parent) ('import-' + [guid]::NewGuid() + '.json')

uv run python code/kien/src/storage/minio_uploader.py --source tripadvisor --local-root "$rawRoot" --manifest-path "$manifest"
if ($LASTEXITCODE -ne 0) { throw 'Upload failed. Check the log before running ETL.' }

uv run python code/kien/src/processing/minio_to_postgres.py --source tripadvisor --manifest "$manifest" --workers 4
if ($LASTEXITCODE -ne 0) { throw 'ETL failed. Check failed_objects and the log.' }
```

4. Kiểm tra log ETL có `"failed_objects": 0` rồi chạy truy vấn sau trong PostgreSQL để xác thực dữ liệu đã vào bảng `reviews` thành công:

```sql
SELECT COUNT(*) AS tripadvisor_reviews
FROM reviews
WHERE source_code = 'tripadvisor';
```