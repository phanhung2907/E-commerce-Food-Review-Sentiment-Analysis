# `src` — Pipeline Foody Incremental

Copy toàn bộ folder `src` này vào:

```text
code/hung/src/
```

## Cấu trúc

```text
src/
├── ingestion/
│   └── foody-shoppefood/
│       ├── foody_restaurant_crawler.py
│       └── foody_review_crawler.py
│
├── processing/
│   ├── __init__.py
│   ├── foody_transform.py
│   └── minio_to_postgres.py
│
├── storage/
│   ├── __init__.py
│   ├── check_infrastructure.py
│   ├── init_postgres.py
│   ├── minio_client.py
│   ├── minio_uploader.py
│   ├── postgres_client.py
│   ├── postgres_repository.py
│   ├── schema_3nf.sql
│   └── setup_minio.py
│
├── utils/
│   ├── __init__.py
│   └── source_codes.py
│
├── README.md
└── run_pipeline.py
```

---

# 1. Flow mới

Luồng chạy bình thường:

```text
PostgreSQL
    ↓
lấy review_id đã có
    ↓
Foody Web/API
    ↓
chỉ crawl từ review mới nhất
    ↓
chạm page toàn review cũ
    ↓
DỪNG
    ↓
merge review mới + raw cũ
    ↓
Local
    ↓
MinIO
    ↓
PostgreSQL
```

Nhờ vậy lần crawl thứ 2, thứ 3... không cần vét lại toàn bộ lịch sử review.

---

# 2. Ví dụ incremental

Database đã có:

```text
100
99
98
97
...
```

Foody có thêm:

```text
105
104
103
102
101
100
99
...
```

Crawler request từ newest:

```text
105 -> mới
104 -> mới
103 -> mới
102 -> mới
101 -> mới
100 -> cũ
99  -> cũ
```

Khi gặp một page không còn review mới:

```text
page_new_count = 0
```

crawler dừng.

Kết quả:

```text
chỉ crawl 5 review mới
```

thay vì vét lại toàn bộ review cũ.

---

# 3. Vì sao vẫn giữ raw đầy đủ?

Raw object không chỉ chứa review mới.

Crawler merge:

```text
review vừa crawl
+
restaurant.json cũ
```

theo `review_id`.

Kết quả vẫn là:

```json
{
  "reviews": [
    105,
    104,
    103,
    102,
    101,
    100,
    99,
    98
  ]
}
```

Nếu local raw bị xóa nhưng MinIO còn dữ liệu, crawler sẽ lấy raw cũ từ MinIO để merge.

---

# 4. `crawl_complete`

Mỗi `restaurant.json` có metadata:

```json
{
  "review_summary": {
    "crawl_complete": true,
    "new_reviews_crawled": 5,
    "pages_scanned": 2,
    "stop_reason": "da_cham_vung_review_cu"
  }
}
```

Incremental early-stop chỉ được bật khi:

```text
crawl_complete = true
```

ở lần crawl trước.

Điều này tránh trường hợp dữ liệu từng bị crawl limit nhưng crawler tưởng đã vét cạn.

Raw cũ từ phiên bản crawler trước chưa có `crawl_complete` sẽ được crawl sâu lại một lần để thiết lập checkpoint an toàn.

---

# 5. Setup thư viện

```bash
uv add requests minio python-dotenv "psycopg[binary]"
```

---

# 6. `.env`

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=food-review-data
MINIO_SECURE=false

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=food_review
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

Nếu PostgreSQL expose `5433`:

```env
POSTGRES_PORT=5433
```

---

# 7. Setup hạ tầng — chỉ một lần

Khởi động Docker:

```bash
docker compose up -d
```

Tạo MinIO bucket:

```bash
uv run python code/hung/src/storage/setup_minio.py
```

Tạo PostgreSQL schema:

```bash
uv run python code/hung/src/storage/init_postgres.py
```

Kiểm tra:

```bash
uv run python code/hung/src/storage/check_infrastructure.py
```

`run_pipeline.py` không tạo bucket/database/schema.

Nếu thiếu hạ tầng, pipeline báo lỗi và dừng.

---

# 8. Chạy bình thường — incremental

```bash
uv run python code/hung/src/run_pipeline.py
```

Hoặc 50 worker toàn pipeline:

```bash
uv run python code/hung/src/run_pipeline.py --workers 50
```

Đây là command nên dùng cho các lần crawl định kỳ.

Ví dụ:

```text
01/10 crawl
15/10 crawl lại
01/11 crawl lại
```

Mỗi lần đều dùng:

```bash
uv run python code/hung/src/run_pipeline.py --workers 50
```

Không cần tạo bucket/database mới.

---

# 9. Worker

Dùng cùng một số worker:

```bash
uv run python code/hung/src/run_pipeline.py \
  --workers 50
```

Khi đó:

```text
crawl workers    = 50
upload workers   = 50
database workers = 50
```

Khuyến nghị thực tế:

```bash
uv run python code/hung/src/run_pipeline.py \
  --workers 50 \
  --db-workers 8
```

Tức:

```text
crawl    = 50
MinIO    = 50
Postgres = 8
```

Có thể cấu hình riêng:

```bash
uv run python code/hung/src/run_pipeline.py \
  --crawl-workers 50 \
  --upload-workers 30 \
  --db-workers 8
```

---

# 10. Crawl giới hạn để test

Ví dụ:

```bash
uv run python code/hung/src/run_pipeline.py \
  --mode limit \
  --max-restaurants-per-city 5 \
  --max-reviews 20 \
  --workers 20
```

`--max-reviews` giới hạn số review item đọc từ API trong lần chạy đó.

Nếu lần test bị giới hạn:

```text
crawl_complete = false
```

Lần sau chạy production không limit:

```bash
uv run python code/hung/src/run_pipeline.py --workers 50
```

crawler sẽ không dùng early-stop cho restaurant đó cho tới khi crawl vét cạn an toàn.

---

# 11. Chỉ một thành phố

```bash
uv run python code/hung/src/run_pipeline.py \
  --city dien-bien \
  --workers 50
```

---

# 12. Full refresh

Thông thường không cần.

Nếu muốn cố ý bỏ incremental và vét lại toàn bộ:

```bash
uv run python code/hung/src/run_pipeline.py \
  --full-refresh \
  --workers 50
```

Full refresh:

```text
không dùng review_id trong PostgreSQL để early-stop
→ crawl tới khi API hết review
→ rebuild restaurant.json
```

---

# 13. Resume khi pipeline crash

Nếu cùng một lần crawl bị crash giữa chừng:

```bash
uv run python code/hung/src/run_pipeline.py \
  --resume \
  --workers 50
```

`--resume` làm review crawler skip các `restaurant.json` local đã có.

## Quan trọng

Không dùng:

```bash
--resume
```

cho lần crawl định kỳ sau 1–2 tuần.

Vì khi đó bạn muốn crawler kiểm tra review mới.

---

# 14. Chạy riêng review crawler

Incremental:

```bash
uv run python code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py \
  --workers 50
```

Một city:

```bash
uv run python code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py \
  --city dien-bien \
  --workers 50
```

Full refresh:

```bash
uv run python code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py \
  --full-refresh \
  --workers 50
```

Resume:

```bash
uv run python code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py \
  --resume \
  --workers 50
```

---

# 15. Local raw

```text
code/hung/data/foody_shoppefood/raw/
└── <city>/
    └── <restaurant_id>/
        └── restaurant.json
```

Ví dụ:

```text
code/hung/data/foody_shoppefood/raw/
└── dien-bien/
    └── 646075/
        └── restaurant.json
```

---

# 16. MinIO

```text
food-review-data/
└── foody/
    └── raw/
        └── <city>/
            └── <restaurant_id>/
                └── restaurant.json
```

Pipeline luôn đồng bộ raw local mới nhất lên cùng object key.

Không tạo bucket theo từng lần crawl.

---

# 17. PostgreSQL

Review có:

```sql
PRIMARY KEY (
    source_code,
    source_review_id
)
```

Importer:

```sql
ON CONFLICT (
    source_code,
    source_review_id
)
DO NOTHING
```

Do đó:

```text
foody + review_id
```

đã tồn tại sẽ không bị insert lần thứ hai.

---

# 18. Vai trò của PostgreSQL trong incremental crawl

PostgreSQL vừa là nơi lưu dữ liệu phân tích, vừa là checkpoint review ID.

Crawler chạy query:

```sql
SELECT source_review_id
FROM reviews
WHERE source_code = 'foody'
  AND source_restaurant_id = ?;
```

Sau đó so sánh review Foody mới trả về với tập ID này.

---

# 19. Flow lần đầu

```text
Database chưa có review
        ↓
existing_review_ids = {}
        ↓
crawler không thể early-stop
        ↓
vét cạn Foody
        ↓
crawl_complete = true
        ↓
Local -> MinIO -> PostgreSQL
```

---

# 20. Flow những lần sau

```text
Database đã có review IDs
        +
raw trước crawl_complete=true
        ↓
request page mới nhất
        ↓
lưu review mới
        ↓
page toàn review cũ
        ↓
STOP
        ↓
merge raw
        ↓
MinIO
        ↓
PostgreSQL chỉ insert review mới
```

---

# 21. Nếu local raw bị mất

Crawler tìm:

```text
local restaurant.json
```

Nếu không có:

```text
MinIO
foody/raw/<city>/<restaurant_id>/restaurant.json
```

Nếu tìm thấy thì dùng MinIO raw để merge.

Nếu cả local và MinIO đều không có nhưng PostgreSQL đã có review ID:

```text
prior_complete = false
```

crawler sẽ crawl sâu lại thay vì early-stop để tránh tạo raw thiếu dữ liệu.

---

# 22. Các option chính `run_pipeline.py`

| Option | Chức năng |
|---|---|
| `--workers N` | N worker chung cho pipeline |
| `--crawl-workers N` | Worker crawler |
| `--upload-workers N` | Worker MinIO |
| `--db-workers N` | Worker PostgreSQL |
| `--mode full` | Không giới hạn số lượng |
| `--mode limit` | Chạy giới hạn để test |
| `--max-restaurants-per-city N` | Giới hạn nhà hàng mỗi city |
| `--max-reviews N` | Giới hạn review item đọc từ API |
| `--city SLUG` | Một city |
| `--page-delay X` | Delay giữa page |
| `--full-refresh` | Vét lại toàn bộ review |
| `--resume` | Tiếp tục lần chạy bị crash |
| `--db-dry-run` | Không ghi PostgreSQL |
| `--skip-restaurant-crawl` | Bỏ bước crawl restaurant |
| `--skip-review-crawl` | Bỏ bước crawl review |
| `--skip-minio-upload` | Bỏ upload MinIO |
| `--skip-db-load` | Bỏ import PostgreSQL |

Xem trực tiếp:

```bash
uv run python code/hung/src/run_pipeline.py --help
```

---

# 23. Cách dùng lâu dài khuyến nghị

## Lần đầu

```bash
docker compose up -d

uv run python code/hung/src/storage/setup_minio.py

uv run python code/hung/src/storage/init_postgres.py

uv run python code/hung/src/storage/check_infrastructure.py

uv run python code/hung/src/run_pipeline.py `
  --workers 50 `
  --db-workers 8

uv run python code/hung/src/run_pipeline.py --workers 50 --db-workers 8
```

## Hai tuần sau

```bash
uv run python code/hung/src/run_pipeline.py \
  --workers 50 \
  --db-workers 8
```

## Những lần tiếp theo

Vẫn chính command đó.

Crawler sẽ chỉ request đủ sâu để tìm review mới rồi dừng khi chạm vùng review cũ.
