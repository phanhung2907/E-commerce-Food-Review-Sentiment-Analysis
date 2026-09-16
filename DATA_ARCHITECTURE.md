# Data Storage & Team Workflow Architecture

## 1. Purpose

Tài liệu này mô tả kiến trúc lưu trữ dữ liệu của project từ **raw data → processed data**, cách các service được chạy bằng **Docker Compose**, vai trò của từng thành viên trong nhóm, và quy trình hợp nhất dữ liệu khi mỗi thành viên đều chạy MinIO/PostgreSQL/CloudBeaver trên máy local riêng.

Mục tiêu chính:

- Giữ dữ liệu gốc an toàn và có thể trace lại.
- Chuẩn hóa dữ liệu trước khi phân tích.
- Cho phép các thành viên làm việc độc lập trên máy riêng.
- Hợp nhất dữ liệu cuối cùng mà không cần merge trực tiếp thư mục runtime của Docker.
- Giữ repo GitHub sạch, chỉ chứa code/config/schema chứ không chứa database runtime data.

---

## 2. High-Level Architecture

```text
ShopeeFood / Foody / Tripadvisor / GrabFood
                     |
                     v
               Python Crawler
                     |
                     v
               MinIO - RAW
                     |
                     v
          Python ETL / Processing
                     |
                     v
               PostgreSQL
                     |
             +-------+--------+
             v                v
         CloudBeaver       RStudio/Jupyter
             |                |
          Inspect DB      EDA / Modeling
```

### Data Flow

```text
Source
  ↓
Crawl
  ↓
Raw JSON
  ↓
MinIO
  ↓
Clean / Normalize / Validate
  ↓
PostgreSQL
  ↓
EDA / Statistics / NLP / Modeling
```

---

## 3. Docker Compose Architecture

Project sử dụng một `docker-compose.yml` để khởi chạy các service chính.

```text
Docker Compose
|
+-- MinIO
|   +-- API: 9000
|   +-- Console: 9001
|
+-- PostgreSQL
|   +-- Port: 5432
|
+-- CloudBeaver
    +-- Web UI: 8978
```

Các service cùng nằm trong một Docker network nên có thể gọi nhau bằng **service name**.

Ví dụ:

```text
CloudBeaver
    ↓
postgres:5432
    ↓
PostgreSQL
```

Trong khi Python chạy trực tiếp trên máy local sẽ kết nối:

```text
localhost:5432
localhost:9000
```

---

## 4. Responsibility of Each Service

### 4.1 MinIO

**Nhiệm vụ:** giữ **raw data gốc** sau khi crawl.

Ví dụ:

```text
food-review-data/
└── raw/
    ├── shopeefood/
    ├── foody/
    ├── tripadvisor/
    └── grabfood/
```

Quy tắc:

- Raw data không chỉnh sửa thủ công.
- Không clean trực tiếp trong MinIO.
- Nếu ETL lỗi thì có thể chạy lại từ raw data.
- MinIO là Data Lake, không dùng thay PostgreSQL.

Ví dụ object key:

```text
raw/shopeefood/reviews/2026-09-16/run_001/restaurant_123/page_001.json
```

---

### 4.2 PostgreSQL

**Nhiệm vụ:** giữ **processed / normalized relational data**.

Ví dụ:

```text
sources
restaurants
reviews
restaurant_snapshots
crawl_runs
```

PostgreSQL dùng để:

- JOIN
- GROUP BY
- filter
- aggregate
- SQL analysis
- connect với RStudio/Jupyter
- chuẩn bị dữ liệu cho modeling

Phân vai:

```text
MinIO      = raw / original source data
PostgreSQL = clean / normalized / relational data
```

Không cần tạo `processed/` trong MinIO nếu PostgreSQL đã đảm nhận processed layer.

---

### 4.3 CloudBeaver

**Nhiệm vụ:** GUI để:

- xem database/schema/table
- inspect columns
- kiểm tra PK/FK
- chạy SQL
- xem sample data
- debug PostgreSQL

CloudBeaver **không phải nơi lưu dữ liệu chính**.

---

## 5. Local Storage Layout

Mỗi thành viên có runtime storage riêng:

```text
storage/
├── minio/
├── postgres/
└── cloudbeaver/
```

Các folder này là dữ liệu runtime của container.

### Không commit các folder này lên GitHub

`.gitignore`:

```gitignore
.env

storage/minio/*
!storage/minio/.gitkeep

storage/postgres/*
!storage/postgres/.gitkeep

storage/cloudbeaver/*
!storage/cloudbeaver/.gitkeep
```

GitHub chỉ nên lưu:

```text
docker-compose.yml
pyproject.toml
uv.lock
.env.example
README.md
docs/
src/
notebooks/
reports/
sql/
```

---

## 6. Why Runtime Storage Is Not Shared Through Git

Không merge trực tiếp:

```text
storage/postgres/
storage/minio/
storage/cloudbeaver/
```

qua Git vì:

- PostgreSQL chứa binary/internal files.
- MinIO chứa object metadata/runtime state.
- CloudBeaver chứa workspace/config local.
- Git không phải database synchronization system.
- Rất dễ conflict/corruption.
- Repo sẽ tăng kích thước nhanh.
- Có nguy cơ commit credential hoặc dữ liệu thật.

---

## 7. Team Working Model

Giả sử nhóm có 2 thành viên.

```text
Member A
├── Docker
│   ├── MinIO A
│   ├── PostgreSQL A
│   └── CloudBeaver A
└── Local data A

Member B
├── Docker
│   ├── MinIO B
│   ├── PostgreSQL B
│   └── CloudBeaver B
└── Local data B
```

Mỗi người có:

- cùng source code
- cùng schema
- cùng Docker Compose
- cùng ETL logic
- nhưng runtime data riêng

---

## 8. Team Responsibilities

### Member A — Ingestion / Source 1

Ví dụ:

```text
ShopeeFood
Foody
```

Nhiệm vụ:

- inspect Network/API
- crawl raw data
- lưu raw JSON vào MinIO local
- ghi crawl manifest
- kiểm tra field mapping
- commit crawler code

### Member B — Ingestion / Source 2

Ví dụ:

```text
Tripadvisor
GrabFood
```

Nhiệm vụ:

- inspect Network/API
- crawl raw data
- lưu raw JSON vào MinIO local
- ghi crawl manifest
- kiểm tra field mapping
- commit crawler code

### Shared Responsibilities

Cả nhóm cùng chịu trách nhiệm:

```text
canonical schema
PostgreSQL DDL
ETL rules
validation rules
naming convention
deduplication
Report documentation
AI_Log
```

---

## 9. Rule: Same Schema, Different Local Data

Mỗi máy có thể có dữ liệu khác nhau, nhưng phải dùng cùng schema.

Ví dụ canonical review schema:

```text
source
source_review_id
source_restaurant_id
rating
review_text
review_date
crawl_timestamp
```

Không được để:

```text
Member A: comment
Member B: review_text
Member C: text
```

Nếu source field khác nhau thì map về canonical field chung trong ETL.

---

## 10. How to Split Work Safely

Có thể chia theo:

### Option A — By Platform

```text
Member A:
ShopeeFood + Foody

Member B:
Tripadvisor + GrabFood
```

### Option B — By Region

```text
Member A:
Da Nang

Member B:
Quy Nhon / Nha Trang
```

### Option C — By Restaurant Range

```text
Member A:
restaurant IDs 1–500

Member B:
restaurant IDs 501–1000
```

Cách chia phải tránh overlap không cần thiết.

---

## 11. Recommended Raw Naming Convention

Dùng naming convention thống nhất:

```text
raw/<source>/<entity>/<crawl_date>/<run_id>/<restaurant_id>/<file>.json
```

Ví dụ:

```text
raw/shopeefood/reviews/2026-09-16/run_A_001/123/page_001.json
raw/tripadvisor/reviews/2026-09-16/run_B_001/456/page_001.json
```

Nhờ vậy khi merge raw data sẽ ít bị ghi đè.

---

## 12. Crawl Run Identification

Mỗi thành viên nên có `run_id`.

Ví dụ:

```text
run_hung_20260916_001
run_member2_20260916_001
```

Manifest:

```json
{
  "run_id": "run_hung_20260916_001",
  "source": "shopeefood",
  "collector": "member_a",
  "started_at": "2026-09-16T10:00:00+07:00",
  "status": "completed"
}
```

---

## 13. Merge Strategy

Không merge PostgreSQL data directory.

Không merge MinIO internal metadata directory.

Merge theo luồng:

```text
Member A Raw
      |
      +------+
             |
Member B Raw |
      |      |
      +------+
             v
       Central MinIO
             |
             v
        One ETL Pipeline
             |
             v
      Central PostgreSQL
```

### Correct Merge Order

```text
1. Export/copy raw data
2. Merge raw objects
3. Validate duplicates
4. Run one canonical ETL
5. Load final PostgreSQL
6. Run validation SQL
```

---

## 14. Why Merge Raw First

Nếu merge trực tiếp DB từ nhiều máy:

```text
PostgreSQL A
+
PostgreSQL B
```

sẽ dễ gặp:

- ID conflict
- duplicate
- schema mismatch
- different constraints
- different cleaning versions
- different normalization logic

Cách an toàn hơn:

```text
Raw A + Raw B
      ↓
One ETL
      ↓
One PostgreSQL
```

---

## 15. Central Merge Workflow

### Step 1 — Export raw objects

Mỗi thành viên export phần raw data đã crawl.

Ví dụ:

```text
exports/
├── member_a/
└── member_b/
```

### Step 2 — Copy into central MinIO

Central MinIO:

```text
food-review-data/
└── raw/
    ├── shopeefood/
    ├── foody/
    ├── tripadvisor/
    └── grabfood/
```

### Step 3 — Deduplication

PostgreSQL nên có:

```sql
UNIQUE (source_id, source_restaurant_id)
```

và:

```sql
UNIQUE (source_id, source_review_id)
```

nếu source cung cấp stable ID.

Nếu không có review ID thì dùng fingerprint/hash.

### Step 4 — Run canonical ETL

```text
Central MinIO
    ↓
ETL
    ↓
Validation
    ↓
Central PostgreSQL
```

---

## 16. Shared Schema Files

Repo nên có:

```text
docs/
└── data_schema.md

sql/
├── schema.sql
└── seed_sources.sql
```

Mọi thành viên dùng cùng file.

Không tự tạo schema khác nhau trên từng máy.

---

## 17. Database Initialization

Mỗi thành viên clone repo:

```bash
git clone <repo>
```

sau đó:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Chạy:

```bash
docker compose up -d
```

Sau đó chạy schema:

```text
sql/schema.sql
```

Mỗi máy sẽ có cùng cấu trúc database nhưng dữ liệu riêng.

---

## 18. `.env` Strategy

Không commit `.env`.

Commit:

```text
.env.example
```

Ví dụ:

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change_me
MINIO_BUCKET=food-review-data

POSTGRES_DB=food_review
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

CLOUDBEAVER_ADMIN_NAME=cbadmin
CLOUDBEAVER_ADMIN_PASSWORD=change_me
```

---

## 19. Local vs Docker Hostnames

### Python chạy ngoài Docker

```text
MinIO:
localhost:9000

PostgreSQL:
localhost:5432
```

### Container gọi container

CloudBeaver → PostgreSQL:

```text
Host: postgres
Port: 5432
```

Không dùng `localhost` giữa 2 container.

---

## 20. Git Responsibility

### Commit

Nên commit:

```text
crawler code
ETL code
schema.sql
docs
README
docker-compose.yml
pyproject.toml
uv.lock
.env.example
```

### Do Not Commit

Không commit:

```text
.env
storage/
raw datasets lớn
PostgreSQL runtime files
MinIO runtime files
CloudBeaver workspace
```

---

## 21. Example Team Workflow

```text
Day 1
Member A → crawl ShopeeFood
Member B → crawl Tripadvisor

Day 2
A → validate raw schema
B → validate raw schema

Day 3
Both → update canonical mapping

Day 4
A + B → merge raw data to central MinIO

Day 5
Run canonical ETL

Day 6
Validate PostgreSQL

Day 7
EDA / Report
```

---

## 22. Definition of Done for Local Team Architecture

Setup được coi là đúng khi:

```text
[ ] Each member can run docker compose up -d
[ ] Each member has local MinIO
[ ] Each member has local PostgreSQL
[ ] Each member can inspect PostgreSQL through CloudBeaver
[ ] All members use the same schema
[ ] Raw naming convention is shared
[ ] Crawl runs are traceable
[ ] storage/ is ignored by Git
[ ] .env is ignored by Git
[ ] .env.example is committed
[ ] Raw data can be exported from each member
[ ] Raw data can be merged to a central MinIO
[ ] One canonical ETL can rebuild final PostgreSQL
```

---

## 23. Final Recommended Architecture

```text
                   GitHub
                     |
       +-------------+-------------+
       v             v             v
    Member A      Member B      Member C
       |             |             |
       v             v             v
   Local Docker   Local Docker   Local Docker
       |             |             |
   +---+---+     +---+---+     +---+---+
   v       v     v       v     v       v
 MinIO  Postgres MinIO  Postgres MinIO Postgres
   |       |     |       |     |       |
   +-------+-----+-------+-----+-------+
                   |
                   v
             Merge Raw Data
                   |
                   v
              Central MinIO
                   |
                   v
              Canonical ETL
                   |
                   v
           Central PostgreSQL
                   |
            +------+------+
            v             v
         RStudio        Jupyter
```

---

## 24. Key Rule

> **Share code through GitHub. Share final data through MinIO/PostgreSQL. Do not share Docker runtime storage through Git.**

Với mô hình local theo từng thành viên:

> **Merge raw data first, then rebuild one final PostgreSQL using one canonical ETL pipeline.**

Đây là cách an toàn và dễ kiểm soát nhất cho project hiện tại.
