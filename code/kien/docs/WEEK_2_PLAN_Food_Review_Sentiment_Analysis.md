# WEEK 2 PLAN — Food Review Sentiment Analysis

## 1. Week 2 Goal

Hoàn thiện **Project Planning / Report 1** để sẵn sàng bước sang Week 3 — Data Engineering.

### Expected outcome at the end of Week 2

Nhóm cần trả lời rõ được 6 câu hỏi:

- [ ] Project đang giải quyết vấn đề gì?
- [ ] Research Questions là gì?
- [ ] Hypotheses \(H_0, H_1\) cho từng câu hỏi là gì?
- [ ] Cần thu thập những field dữ liệu nào?
- [ ] Nguồn nào có khả năng cung cấp các field đó?
- [ ] Data sẽ đi từ source → MinIO → Database → Analysis như thế nào?

> **Không phải mục tiêu tuần 2:** crawl dataset lớn, EDA hoàn chỉnh, train model hoặc làm sentiment model.

---

# 2. Project Scope

## Project Name

**Food Review Sentiment Analysis on E-commerce / Food Platforms**

## Candidate Data Sources

Hiện tại nhóm dự kiến khảo sát:

1. ShopeeFood
2. Foody
3. Tripadvisor
4. GrabFood

### Source status

| Source | Status | Need to Validate |
|---|---|---|
| ShopeeFood | Candidate | Review text, rating, date, restaurant metadata, pagination/API accessibility |
| Foody | Candidate | Review text, rating, date, restaurant metadata, pagination/API accessibility |
| Tripadvisor | Candidate | Review text, rating, date, location, restaurant metadata, pagination/API accessibility |
| GrabFood | Candidate | Review text, rating, restaurant metadata, accessibility/API availability |

> Chưa chọn source chính thức cho đến khi hoàn thành **Source Feasibility Check**.

---

# 3. Research Questions

## RQ1 — Review Volume vs Rating

**Question**

> Is higher review volume associated with lower customer ratings?

### Mục đích

Kiểm tra liệu các quán có lượng review lớn có xu hướng nhận rating thấp hơn hay không.

### Hypothesis

**H0**

> Review volume không có mối liên hệ đáng kể với customer rating.

**H1**

> Review volume có mối liên hệ đáng kể với customer rating.

### Important note

Không được mặc định:

> nhiều review = đông khách

Review volume chỉ được xem là **proxy variable** cho mức độ phổ biến / lượng tương tác, không phải số khách thực tế.

---

## RQ2 — Fatal Keywords in 1-Star Reviews

**Question**

> Which words or phrases are strongly associated with 1-star reviews?

### Hypothesis

**H0**

> Không có từ hoặc cụm từ nào có mối liên hệ đáng kể với đánh giá 1 sao.

**H1**

> Một số từ hoặc cụm từ có mối liên hệ đáng kể với đánh giá 1 sao.

### Possible future approaches

Week 2 chỉ xác định hướng phân tích, chưa triển khai:

- Word frequency
- N-gram
- TF-IDF
- Chi-square
- Odds ratio
- Logistic Regression
- Sentiment classification

---

## RQ3 — Comment Length vs Rating

**Question**

> Is review length associated with star rating?

### Status

- [ ] Keep
- [ ] Remove

Chỉ giữ nếu dữ liệu crawl được có đủ review text và rating.

---

# 4. Data Requirements

## Unit of Analysis

Primary unit:

> **One restaurant review = one record**

Secondary aggregation:

> **One restaurant = one aggregated entity**

## Required Raw Fields

| Field | Description | Required For |
|---|---|---|
| `source` | Platform name | Traceability |
| `restaurant_id` | Unique restaurant ID | Grouping / Join |
| `restaurant_name` | Restaurant name | Identification |
| `restaurant_url` | Original source URL | Traceability |
| `city` | City / location | Regional analysis |
| `category` | Restaurant / cuisine category | Control variable |
| `review_id` | Review identifier | Deduplication |
| `review_text` | Review content | RQ2 |
| `rating` | Star rating | RQ1, RQ2 |
| `review_date` | Review date | Time analysis |
| `reviewer_id` | Reviewer identifier if available | Duplicate / behavior check |
| `total_reviews` | Review count of restaurant | RQ1 |
| `restaurant_rating` | Overall restaurant rating | RQ1 |
| `crawl_timestamp` | Time data was collected | Reproducibility |

## Derived Fields Later

Các field này chưa cần crawl trực tiếp:

```text
comment_length
is_1_star
region
review_month
review_year
review_volume_bucket
cleaned_text
tokens
keywords
sentiment_score
```

---

# 5. Source Feasibility Check

## Objective

Trước khi chọn nguồn dữ liệu chính thức, kiểm tra từng platform có cung cấp đủ dữ liệu cho Research Questions hay không.

## Checklist per source

### ShopeeFood

- [ ] Tìm restaurant listing endpoint / public API / request được browser gọi
- [ ] Tìm review endpoint
- [ ] Kiểm tra pagination
- [ ] Có `review_text`
- [ ] Có `rating`
- [ ] Có `review_date`
- [ ] Có `restaurant_id`
- [ ] Có `total_reviews`
- [ ] Có city/location
- [ ] Test 1–3 restaurants
- [ ] Lưu 20–100 sample reviews

### Foody

- [ ] Tìm review request/API
- [ ] Kiểm tra pagination
- [ ] Có `review_text`
- [ ] Có `rating`
- [ ] Có `review_date`
- [ ] Có `restaurant_id`
- [ ] Có `total_reviews`
- [ ] Có city/location
- [ ] Test 1–3 restaurants
- [ ] Lưu 20–100 sample reviews

### Tripadvisor

- [ ] Xác định khả năng lấy restaurant reviews
- [ ] Kiểm tra pagination
- [ ] Có `review_text`
- [ ] Có `rating`
- [ ] Có `review_date`
- [ ] Có restaurant metadata
- [ ] Có location
- [ ] Test 1–3 restaurants
- [ ] Lưu 20–100 sample reviews

### GrabFood

- [ ] Xác định review data có public / accessible hay không
- [ ] Kiểm tra restaurant metadata
- [ ] Kiểm tra rating data
- [ ] Kiểm tra review text có tồn tại hay không
- [ ] Kiểm tra pagination nếu có
- [ ] Test sample request
- [ ] Decide KEEP / DROP

---

# 6. Source Selection Criteria

Không chọn nguồn chỉ vì crawl được.

Chấm từng source theo:

| Criterion | Weight |
|---|---:|
| Có review text | High |
| Có star rating | High |
| Có review date | High |
| Có total review count | High |
| Có restaurant metadata | Medium |
| Có city/location | Medium |
| Pagination rõ ràng | High |
| Có thể crawl reproducibly | High |
| Ít phụ thuộc browser automation | Medium |
| Data format ổn định | Medium |

## Decision

Cuối tuần cần quyết định:

```text
Primary source:
Secondary source:
Sources dropped:
Reason:
```

---

# 7. Planned Data Flow

```text
ShopeeFood / Foody / Tripadvisor / GrabFood
                     │
                     ▼
              Python Ingestion
                     │
                     ▼
             Raw JSON Response
                     │
                     ▼
              MinIO Data Lake
                  raw/
                     │
                     ▼
            Python Processing
                     │
                     ▼
                PostgreSQL
                     │
             ┌───────┴───────┐
             ▼               ▼
          RStudio         Jupyter
             │               │
            EDA           Modeling
```

---

# 8. MinIO Storage Design

Proposed bucket:

```text
food-review-data
```

Proposed object structure:

```text
raw/
├── shopeefood/
│   └── YYYY-MM-DD/
│       └── restaurant_<id>.json
│
├── foody/
│   └── YYYY-MM-DD/
│       └── restaurant_<id>.json
│
├── tripadvisor/
│   └── YYYY-MM-DD/
│       └── restaurant_<id>.json
│
└── grabfood/
    └── YYYY-MM-DD/
        └── restaurant_<id>.json
```

Rule:

> Raw data phải được giữ nguyên trước khi cleaning.

---

# 9. Docker Architecture

Week 2 chỉ cần hoàn thành infrastructure skeleton.

## Required services

### 1. MinIO

Purpose:

> Raw Data Lake

### 2. PostgreSQL

Purpose:

> Structured / cleaned analytical data

### 3. Python App

Purpose:

- ingestion
- processing
- connection to MinIO
- connection to PostgreSQL

### Future integration

RStudio có thể:

- chạy như container riêng, hoặc
- chạy local và connect PostgreSQL

Quyết định cách nào sẽ được chốt trước Report 3.

---

# 10. Repository Checklist

Expected structure:

```text
Food-Review-Sentiment-Analysis/
│
├── .gitignore
├── README.md
├── AI_Log.md
├── docker-compose.yml
├── requirements.txt
│
├── configs/
│
├── docker/
│   └── app/
│       └── Dockerfile
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│   ├── data_requirements.md
│   └── architecture.md
│
├── src/
│   ├── ingestion/
│   │   └── crawler.py
│   ├── processing/
│   │   └── cleaner.py
│   ├── modeling/
│   └── utils/
│
├── notebooks/
│
└── reports/
    └── Report_1_Proposal.*
```

## Repo tasks

- [ ] Check `.gitignore`
- [ ] Ignore `.env`
- [ ] Ignore `__pycache__`
- [ ] Ignore large raw data
- [ ] Update README
- [ ] Create `AI_Log.md`
- [ ] Create initial `docker-compose.yml`
- [ ] Verify folder structure
- [ ] Make at least 2 meaningful commits this week

Suggested commits:

```bash
git commit -m "docs: define research questions and hypotheses"

git commit -m "docs: add data requirements and source feasibility plan"

git commit -m "feat: add docker architecture skeleton"

git commit -m "chore: organize repository structure for data pipeline"
```

---

# 11. Report 1 Outline

## 1. Project Overview

- Project name
- Background
- Problem statement
- Project objective

## 2. Business Understanding

Explain:

- Why food reviews matter
- Why rating alone may not explain customer dissatisfaction
- Why text reviews provide additional information

## 3. Research Questions

Include:

- RQ1
- RQ2
- Optional RQ3

## 4. Research Hypotheses

For every RQ:

- H0
- H1

## 5. Analytic Approach

Example mapping:

| Research Question | Planned Approach |
|---|---|
| RQ1 | descriptive statistics, correlation, regression |
| RQ2 | NLP, keyword analysis, classification |
| RQ3 | correlation / regression / group comparison |

## 6. Data Requirements

Include:

- raw fields
- unit of analysis
- expected derived fields

## 7. Data Collection Strategy

Candidate sources:

- ShopeeFood
- Foody
- Tripadvisor
- GrabFood

Explain:

- source validation process
- sample crawl
- source selection criteria

## 8. System Architecture

Include diagram:

```text
Source
  ↓
Python
  ↓
MinIO
  ↓
Processing
  ↓
PostgreSQL
  ↓
RStudio / Jupyter
```

## 9. Technology Stack

- Python
- SQL / PostgreSQL
- MinIO
- Docker
- RStudio
- Jupyter
- Git / GitHub

## 10. Risks and Limitations

Potential risks:

- API / endpoint changes
- anti-bot mechanisms
- missing review dates
- missing review text
- inconsistent rating scales
- duplicated reviews
- different platform schemas
- regional sampling bias

---

# 12. Week 2 Execution Plan

## Day 1 — Research Definition

### Tasks

- [ ] Finalize RQ1
- [ ] Finalize RQ2
- [ ] Decide whether to keep RQ3
- [ ] Write H0 / H1
- [ ] Define unit of analysis

### Deliverable

```text
Research Questions + Hypotheses v1
```

---

## Day 2 — Data Requirements

### Tasks

- [ ] Create data field table
- [ ] Map fields to each RQ
- [ ] Identify mandatory vs optional fields
- [ ] Define expected raw JSON structure

### Deliverable

```text
docs/data_requirements.md
```

---

## Day 3 — Source Investigation

### Tasks

Inspect:

- [ ] ShopeeFood
- [ ] Foody
- [ ] Tripadvisor
- [ ] GrabFood

For each source:

- Inspect browser Network tab
- Identify request URLs
- Inspect request parameters
- Inspect response schema
- Check pagination
- Check whether authentication/token is required

### Deliverable

```text
Source feasibility table
```

---

## Day 4 — Small Data Collection Test

### Tasks

For sources that appear feasible:

- [ ] Collect 1–3 restaurants
- [ ] Collect 20–100 reviews
- [ ] Save original JSON
- [ ] Compare fields between platforms
- [ ] Check null/missing data

### Important

This is only a **proof-of-concept crawl**.

Do not start full-scale collection yet.

### Deliverable

```text
data/raw/sample/
```

---

## Day 5 — Architecture + Docker

### Tasks

- [ ] Finalize architecture diagram
- [ ] Start MinIO
- [ ] Start PostgreSQL
- [ ] Start Python app container
- [ ] Verify connectivity
- [ ] Create MinIO bucket

### Deliverable

```text
docker-compose.yml
architecture diagram
```

---

## Day 6 — Report 1

### Tasks

- [ ] Write Business Understanding
- [ ] Add Research Questions
- [ ] Add Hypotheses
- [ ] Add Data Requirements
- [ ] Add Collection Strategy
- [ ] Add Architecture
- [ ] Add Risks

### Deliverable

```text
Report 1 Draft
```

---

## Day 7 — Review & Freeze Week 2

### Final review

- [ ] Source selected
- [ ] RQs frozen
- [ ] H0/H1 frozen
- [ ] Required fields frozen
- [ ] Architecture frozen
- [ ] Docker services start successfully
- [ ] README updated
- [ ] AI_Log updated
- [ ] ≥ 2 meaningful commits
- [ ] Report 1 ready for submission/review

---

# 13. Definition of Done — Week 2

Week 2 được xem là hoàn thành khi:

```text
[ ] Research Questions are finalized
[ ] H0/H1 are defined
[ ] Data requirements are documented
[ ] Candidate platforms are investigated
[ ] At least one feasible source is identified
[ ] Small sample data has been collected
[ ] Raw sample schema is understood
[ ] Docker architecture is documented
[ ] MinIO + PostgreSQL + Python skeleton works
[ ] Repository follows required structure
[ ] README.md is updated
[ ] AI_Log.md is updated
[ ] Report 1 draft is complete
[ ] At least 2 meaningful Git commits exist
```

---

# 14. Not Doing Yet

Các phần sau để Week 3+:

- Full-scale crawling
- Production ingestion pipeline
- Complete MinIO → PostgreSQL ETL
- Data cleaning at scale
- EDA
- RStudio visualization
- NLP training
- Machine Learning
- Model evaluation
- Dashboard
- Deployment

---

# 15. Week 3 Entry Criteria

Chỉ chuyển sang Data Engineering khi có:

```text
Research Question
        ↓
Hypothesis
        ↓
Required Fields
        ↓
Validated Source
        ↓
Known Response Schema
        ↓
Docker Architecture
        ↓
READY FOR INGESTION
```

Week 3 focus:

```text
Source
   ↓
Crawler / API Client
   ↓
Raw JSON
   ↓
MinIO
   ↓
Processing
   ↓
PostgreSQL
```
