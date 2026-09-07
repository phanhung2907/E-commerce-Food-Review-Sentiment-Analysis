# Real Estate & Tourism Data Science

Dự án nhóm cho môn **ADY201m – AI, Data Science with Python & SQL**, theo **Chủ đề 1: Bất động sản & Du lịch**.

> Trạng thái: đang lập kế hoạch (Report 1). Phạm vi, địa bàn và nguồn dữ liệu cuối cùng cần được cả nhóm xác nhận trước khi viết crawler.

## 1. Mục tiêu dự án

Xây dựng một pipeline dữ liệu end-to-end để tự thu thập, lưu trữ, xử lý và phân tích dữ liệu bất động sản hoặc lưu trú du lịch:

```text
Nguồn web/API -> Python ingestion -> MinIO (raw) -> Python ETL -> PostgreSQL
               -> Jupyter/RStudio EDA -> Machine Learning -> Demo
```

Nguồn được gợi ý trong đề bài: Booking, Agoda và Batdongsan. Dữ liệu dùng cho dự án phải do nhóm tự thu thập; không dùng dataset có sẵn.

## 2. Câu hỏi nghiên cứu ban đầu

Nhóm có thể chốt một trong hai hướng sau thay vì dàn trải cả bất động sản và du lịch:

1. **Du lịch/lưu trú:** Tiện ích nào (hồ bơi, view biển, gần trung tâm...) ảnh hưởng mạnh nhất đến giá phòng?
2. **Bất động sản:** Quan hệ giữa diện tích và giá có tuyến tính không, và có xuất hiện điểm bão hòa không?

Khung giả thuyết đề xuất cho hướng du lịch:

- **H0:** Sau khi kiểm soát vị trí và loại hình lưu trú, các tiện ích không làm thay đổi đáng kể giá phòng.
- **H1:** Ít nhất một tiện ích làm thay đổi đáng kể giá phòng sau khi đã kiểm soát các yếu tố còn lại.

Đây mới là giả thuyết khởi đầu. Trước Report 1, nhóm cần xác định rõ biến mục tiêu, địa bàn, thời gian thu thập, đơn vị quan sát và tiêu chí kiểm định.

## 3. Kiến trúc dự kiến

- **MinIO:** Data Lake tương thích S3, lưu JSON/HTML thô và dữ liệu theo từng lần crawl.
- **PostgreSQL:** lưu dữ liệu đã làm sạch, chuẩn hóa và sẵn sàng truy vấn SQL.
- **Python app:** ingestion, validation, cleaning, ETL và modeling.
- **Jupyter/RStudio:** EDA, trực quan hóa, kiểm định giả thuyết và so sánh mô hình.
- **Docker Compose:** khởi chạy đồng bộ các service phục vụ demo.

## 4. Cấu trúc repository

```text
.
├── .gitignore
├── README.md
├── AI_Log.md
├── docker-compose.yml
├── requirements.txt
├── configs/
│   └── db_config.json
├── docker/
│   ├── app/
│   │   └── Dockerfile
│   └── db/
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── ingestion/
│   │   └── crawler.py
│   ├── processing/
│   │   └── cleaner.py
│   ├── modeling/
│   │   └── model.py
│   └── utils/
├── notebooks/
└── reports/
```

Các thư mục dữ liệu chỉ giữ `.gitkeep` hoặc sample nhỏ có tiền tố `sample_`. Dữ liệu crawl đầy đủ, volume Docker, secrets và model sinh ra trong quá trình chạy không được commit.

## 5. Khởi động dự án (dự kiến)

Yêu cầu: Git, Docker Desktop có Docker Compose, Python 3.11+ và R/RStudio nếu chạy EDA bằng R.

```bash
cp .env.example .env
docker compose up --build
```

Sau khi các service và pipeline được triển khai, phần này cần bổ sung lệnh crawl, ETL, test, notebook/RMarkdown và địa chỉ truy cập MinIO. Hiện tại `docker-compose.yml` và mã nguồn chỉ là scaffold, chưa phải bản demo hoàn chỉnh.

## 6. Kế hoạch 10 tuần

| Tuần | Mục tiêu | Sản phẩm chính |
|---|---|---|
| 1–2 | Planning | Giả thuyết, phạm vi dữ liệu, sơ đồ Docker, Report 1 |
| 3–4 | Data Engineering | Crawler, raw data trên MinIO, ETL vào PostgreSQL, Report 2 |
| 5–6 | Cleaning & EDA | Quy tắc làm sạch, Data Dictionary, EDA bằng RStudio/Jupyter, Report 3 |
| 7–8 | Modeling | Ít nhất 2 mô hình, validation và so sánh, Report 4 |
| 9–10 | Deployment | Docker Compose hoàn chỉnh, demo, slide và Report 5 |

## 7. Việc nhóm cần chốt trước khi code

- Chọn **một hướng chính**: bất động sản hoặc lưu trú du lịch.
- Chọn địa bàn nghiên cứu và nguồn dữ liệu được phép thu thập.
- Chốt biến mục tiêu, biến giải thích và cách đo khoảng cách/vị trí/tiện ích.
- Kiểm tra `robots.txt`, điều khoản sử dụng, giới hạn tốc độ và dữ liệu cá nhân của nguồn.
- Phân công owner cho ingestion, data/SQL, EDA/modeling, infrastructure và reports.
- Định nghĩa schema raw, schema processed và Data Dictionary phiên bản đầu.

## 8. Quy ước làm việc

- Mỗi thành viên commit tối thiểu **2 lần/tuần**.
- Dùng commit message rõ nghĩa, ví dụ: `feat: add booking ingestion prototype` hoặc `fix: handle missing room price`.
- Không commit `.env`, mật khẩu, access key, dữ liệu lớn hoặc volume cục bộ.
- Mọi lần dùng AI cho dự án phải được ghi trong [`AI_Log.md`](AI_Log.md).
- Tạo branch theo dạng `feat/<ten-tinh-nang>`, mở pull request và có ít nhất một thành viên review trước khi merge.

## 9. Tiêu chí hoàn thành tối thiểu

- `docker compose up --build` khởi động được hệ thống demo.
- Dữ liệu tự crawl đi qua đủ luồng Raw (MinIO) -> Processed (PostgreSQL).
- Có truy vấn SQL kiểm tra chất lượng dữ liệu và Data Dictionary.
- Có EDA bằng RStudio hoặc Jupyter theo yêu cầu môn học.
- Có ít nhất 2 mô hình ML, metric phù hợp và kết luận chấp nhận/bác bỏ giả thuyết.
- Có đủ 5 reports, nhật ký AI và lịch sử commit đều đặn.

