# Food Review Sentiment Analysis

Project môn **ADY201m – AI, Data Science with Python & SQL**.

Mục tiêu của project là xây dựng pipeline dữ liệu end-to-end để tự thu thập review nhà hàng/quán ăn, lưu dữ liệu gốc, chuẩn hóa dữ liệu và phục vụ EDA / SQL / Machine Learning.

## 1. Architecture

```text
Foody / ShopeeFood / other sources
                │
                ▼
          Python Crawler
                │
                ▼
        MinIO — Raw Data
                │
                ▼
       Python ETL / Cleaning
                │
                ▼
   PostgreSQL — Processed Data
                │
        ┌───────┴────────┐
        ▼                ▼
   CloudBeaver      Jupyter / RStudio
   SQL / Inspect      EDA / Modeling
```

### Vai trò từng service

| Service | Vai trò | Truy cập |
|---|---|---|
| **MinIO** | Lưu raw JSON/HTML nguyên bản sau khi crawl | `http://localhost:9001` |
| **PostgreSQL** | Lưu dữ liệu đã clean / normalize theo relational schema | Host port trong `.env` |
| **CloudBeaver** | GUI để xem table, PK/FK và chạy SQL trên PostgreSQL | `http://localhost:8978` |
| **Python + uv** | Crawler, ETL, validation, EDA/modeling code | chạy local |

> MinIO giữ **raw data**. PostgreSQL giữ **processed relational data**. Không dùng Git để đồng bộ database/runtime data.

---

## 2. Repository Structure

Repo hiện tại tổ chức code theo từng thành viên:

```text
.
├── code/
│   ├── hung/
│   ├── kien/
│   ├── sang/
│   └── tuan/
│       ├── configs/
│       ├── data/
│       │   ├── raw/
│       │   └── processed/
│       ├── notebooks/
│       ├── reports/
│       └── src/
│           ├── ingestion/
│           ├── processing/
│           ├── modeling/
│           └── utils/
│
├── docker/
│   ├── minio/              # runtime local
│   ├── postgres/data/      # runtime local
│   └── cloudbeaver/        # runtime local
│
├── plans/
│   ├── WEEK_2_PLAN_Food_Review_Sentiment_Analysis.md
│   └── tutorial_report1.md
│
├── AI_Log_Hung.md
├── AI_Log_Sang.md
├── AI_Log_Tuan.md
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

`docker/` chứa dữ liệu runtime local được tạo bởi container. **Không commit nội dung runtime này lên GitHub.**

---

## 3. Requirements

Cài trước:

- **Git**
- **Docker Desktop**
- **uv**
- Python theo project: **>= 3.12**

Kiểm tra:

```bash
docker --version
docker compose version
uv --version
```

---

## 4. Setup Project

### 4.1 Clone repo

```bash
git clone <repository-url>
cd <repository-folder>
```

### 4.2 Setup Python environment

Project sử dụng `uv`:

```bash
uv sync
```

Chạy Python bằng:

```bash
uv run python <script.py>
```

---

## 5. Environment Variables

Tạo file `.env` tại root project.

Ví dụ:

```env
# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change_me
MINIO_BUCKET=food-review-data

# PostgreSQL
POSTGRES_DB=food_review
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# CloudBeaver
CLOUDBEAVER_PORT=8978
CLOUDBEAVER_SERVER_NAME=Food Review CloudBeaver
CLOUDBEAVER_ADMIN_NAME=cbadmin
CLOUDBEAVER_ADMIN_PASSWORD=change_me
```

> `.env` chứa credential local và **không được commit**.

---

## 6. Start Docker Services

Chạy:

```bash
docker compose up -d
```

Kiểm tra:

```bash
docker compose ps
```

Các container chính:

```text
food-review-minio
food-review-postgres
food-review-cloudbeaver
```

Dừng hệ thống:

```bash
docker compose down
```

---

## 7. MinIO Setup

Mở:

```text
http://localhost:9001
```

Đăng nhập bằng:

```text
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
```

Tạo bucket:

```text
food-review-data
```

Raw data nên được lưu theo convention:

```text
raw/<source>/<entity>/<crawl_date>/<run_id>/...
```

Ví dụ:

```text
raw/foody/reviews/2026-09-18/run_001/272138/page_001.json
```

### Nguyên tắc

Raw response phải được giữ nguyên để:

- audit dữ liệu nguồn;
- chạy lại ETL khi cleaning thay đổi;
- merge dữ liệu giữa các thành viên;
- tránh phải crawl lại khi processing code lỗi.

---

## 8. PostgreSQL + CloudBeaver Setup

### PostgreSQL

PostgreSQL chạy bên trong Docker ở:

```text
postgres:5432
```

Port expose ra máy host được lấy từ:

```env
POSTGRES_PORT
```

Ví dụ nếu:

```env
POSTGRES_PORT=5433
```

thì Python chạy trên máy local kết nối:

```text
localhost:5433
```

> PostgreSQL không phải web server, vì vậy không mở `localhost:5433` bằng browser.

### CloudBeaver

Mở:

```text
http://localhost:8978
```

Tạo PostgreSQL connection với:

```text
Host: postgres
Port: 5432
Database: food_review
Username: postgres
Password: giá trị POSTGRES_PASSWORD trong .env
Connection name: Food Review PostgreSQL
```

Quan trọng:

```text
CloudBeaver → PostgreSQL: postgres:5432
Python local → PostgreSQL: localhost:<POSTGRES_PORT>
```

Sau khi nhập, bấm:

```text
TEST → CREATE
```

---

## 9. Data Storage Workflow

### Raw Layer

```text
Crawler
   ↓
MinIO
   ↓
raw JSON / HTML
```

Không clean hoặc đổi schema ở bước này.

### Processed Layer

```text
MinIO Raw
   ↓
Python ETL
   ↓
validate / normalize / deduplicate
   ↓
PostgreSQL
```

PostgreSQL sẽ chứa relational tables phục vụ SQL, EDA và modeling.

Schema chính thức cần được thống nhất trước khi ingestion production bắt đầu.

---

## 10. Team Workflow

Mỗi thành viên có thể chạy Docker và dữ liệu local riêng:

```text
Member A                    Member B
MinIO A                     MinIO B
PostgreSQL A                PostgreSQL B
```

### GitHub dùng để share

- source code;
- schema / SQL scripts;
- notebooks;
- config mẫu;
- Docker Compose;
- reports;
- AI logs.

### GitHub không dùng để share

- MinIO runtime data;
- PostgreSQL data directory;
- CloudBeaver workspace;
- `.env`;
- dataset crawl lớn.

### Khi cần hợp nhất dữ liệu

Không merge trực tiếp PostgreSQL folder giữa các máy.

Flow chuẩn:

```text
Raw data Member A ─┐
                   ├──> Central MinIO
Raw data Member B ─┘
                         │
                         ▼
                    One ETL Pipeline
                         │
                         ▼
                  Central PostgreSQL
```

**Rule:** merge raw data trước, sau đó chạy cùng một ETL để tạo database cuối.

---

## 11. Current Status

Đã setup và test:

- [x] Docker Compose
- [x] MinIO
- [x] PostgreSQL
- [x] CloudBeaver
- [x] Python environment bằng `uv`
- [x] Repository chia workspace theo thành viên

Đang thực hiện:

- [ ] Chốt raw schema
- [ ] Chốt PostgreSQL relational schema
- [ ] Khảo sát endpoint/API nguồn dữ liệu
- [ ] Crawl raw JSON vào MinIO
- [ ] Xây ETL MinIO → PostgreSQL

Chi tiết kế hoạch nằm trong:

```text
plans/
```

---

## 12. Useful Commands

```bash
# Python dependencies
uv sync

# Start services
docker compose up -d

# Check services
docker compose ps

# View logs
docker compose logs

# PostgreSQL logs
docker logs food-review-postgres

# Test PostgreSQL inside container
docker exec -it food-review-postgres \
  psql -U postgres -d food_review

# Stop services
docker compose down
```

---

## 13. Working Rules

- Không commit `.env` hoặc credential.
- Không commit runtime data trong `docker/minio`, `docker/postgres/data`, `docker/cloudbeaver`.
- Không sửa raw data sau khi crawl.
- Các thành viên phải dùng cùng canonical schema.
- Commit message phải mô tả rõ thay đổi.
- Ghi lại việc sử dụng AI trong `AI_Log_<member>.md`.

---

## Project Pipeline

```text
Crawl
  ↓
MinIO / Raw
  ↓
ETL
  ↓
PostgreSQL / Processed
  ↓
SQL + EDA
  ↓
Modeling
  ↓
Evaluation
```
