# One-Day Data Source Expansion Plan

## 1. Mục tiêu trong ngày

Mở rộng nguồn dữ liệu cho project **Food Review Sentiment Analysis** ngoài:

- ShopeeFood
- Foody
- TripAdvisor

Yêu cầu:
- Tìm thêm **ít nhất 2 nguồn food review data**.
- Đánh giá khả năng tiếp cận và thu thập dữ liệu của từng nguồn.
- Crawl thử **ít nhất 1,000 records / nguồn** nếu khả thi.
- **Không giới hạn features** ở raw layer: ưu tiên lưu đầy đủ field có thể thu thập được.

## 2. Source Discovery

Ưu tiên nguồn có:
- review text
- rating/star
- restaurant information
- timestamp
- reviewer metadata
- location
- reaction / like / helpful count
- category / cuisine
- image metadata

Không dùng public dataset có sẵn nếu có thể tự crawl từ nguồn gốc.

## 3. Đánh giá từng nguồn

| Tiêu chí | Nội dung |
|---|---|
| Platform | Tên nền tảng |
| URL | Trang / endpoint chính |
| Data access | API / internal API / HTML / browser automation |
| Login required | Yes / No |
| Anti-bot | Low / Medium / High |
| Pagination | Cách phân trang |
| Main features | Các field quan trọng |
| Crawl speed | Ước lượng |
| Stability | Low / Medium / High |
| 1,000 rows feasible | Yes / No |
| Risk | Rate limit, CAPTCHA, token, session, blocking... |
| Recommendation | Recommended / Possible / Not Recommended |

## 4. Crawl thử

Với mỗi nguồn khả thi:

```text
Target: >= 1,000 records
```

Raw data:
> Không chủ động loại bỏ feature ở bước crawl.

Nếu API trả 40 fields thì ưu tiên lưu cả 40 fields.

Chỉ bỏ field khi:
- dữ liệu nhị phân quá lớn;
- chắc chắn không liên quan;
- có vấn đề privacy / security;
- không thể serialize hợp lý.

Output đề xuất:

```text
code/<member>/data/<platform>/raw/
└── <city-or-category>/
    └── <crawl-date>.json
```

Hoặc CSV nếu response phù hợp dạng bảng.

## 5. Yêu cầu crawler

Crawler thử nghiệm nên có:
- pagination
- retry khi request lỗi
- request timeout
- delay giữa request
- deduplicate
- logging số records
- checkpoint / lưu định kỳ nếu crawl lâu

Không cần ETL hoặc cleaning trong task này.

## 6. Deliverables cuối ngày

Mỗi thành viên bàn giao:

### A. Source report

```text
<platform>-source-report.md
```

Gồm:
1. Platform
2. URL / endpoint
3. Cách lấy dữ liệu
4. Các field quan sát được
5. Anti-bot / limitation
6. Kết quả test crawl
7. Số records crawl được
8. Đánh giá có nên đưa vào project

### B. Crawler code

```text
code/<member>/src/ingestion/<platform>/
```

Code phải chạy độc lập.

### C. Sample raw data

```text
>= 1,000 records / source
```

nếu nguồn cho phép.

### D. README chạy code

Ví dụ:

```bash
uv sync
uv run python <crawler.py>
```

và mô tả output được lưu ở đâu.

## 7. Phân chia công việc gợi ý

Chia theo **platform**, không chia theo công đoạn.

| Member | Responsibility |
|---|---|
| Member 1 | Source A: research + crawler + report |
| Member 2 | Source B: research + crawler + report |
| Member 3 | Source C: research + crawler + report |
| Leader | Review quality, merge code, compare sources |

## 8. Definition of Done

- [ ] Tìm được ít nhất **2 nguồn mới** ngoài ShopeeFood, Foody, TripAdvisor.
- [ ] Có đánh giá khả năng crawl cho từng nguồn.
- [ ] Xác định endpoint / request / HTML structure.
- [ ] Crawl thử ít nhất **1,000 records** với mỗi nguồn khả thi.
- [ ] Raw data giữ tối đa features có thể thu thập.
- [ ] Có crawler code chạy lại được.
- [ ] Có report ngắn cho từng nguồn.
- [ ] Có sample raw data.
- [ ] Code và tài liệu được commit đúng branch/member folder.

## 9. Thứ tự thực hiện trong ngày

```text
1. Tìm source
2. Inspect Network / HTML
3. Test request nhỏ
4. Xác định pagination
5. Crawl 1,000+ records
6. Save raw
7. Viết report
8. Commit
```

Nếu một nguồn gặp CAPTCHA, browser fingerprint, token động hoặc anti-bot phức tạp:

> Ghi lại kết quả thử nghiệm, đánh giá limitation và chuyển sang nguồn khác.
