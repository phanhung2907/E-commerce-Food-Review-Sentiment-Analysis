# Food Review Sentiment Analysis

Dự án nhóm cho môn **ADY201m – AI, Data Science with Python & SQL**, theo **Chủ đề 2: Phân tích cảm xúc (Sentiment Analysis)**.

> Trạng thái: lập kế hoạch cho Report 1. Phạm vi địa lý, nguồn dữ liệu và khoảng thời gian thu thập cần được nhóm xác nhận trước khi triển khai crawler.

## 1. Bài toán nghiên cứu

Dự án xây dựng một pipeline dữ liệu end-to-end để tự thu thập và phân tích đánh giá nhà hàng/quán ăn từ **ShopeeFood hoặc Foody**. Kết quả hướng đến việc:

- kiểm tra mối liên hệ giữa mức độ phổ biến của quán (đại diện bằng số lượng review) và chất lượng dịch vụ (đại diện bằng rating);
- nhận diện từ khóa hoặc cụm từ có khả năng dự báo đánh giá 1 sao (`fatal keywords`);
- khảo sát sự khác biệt trong cách đánh giá giữa các vùng và mối liên hệ giữa độ dài bình luận với số sao.

```text
ShopeeFood/Foody -> Python crawler -> MinIO (raw JSON/HTML)
                  -> Python ETL -> PostgreSQL
                  -> RStudio/Jupyter EDA -> 2 mô hình ML -> Demo
```

Dữ liệu của dự án phải do nhóm tự thu thập, không sử dụng dataset có sẵn. Việc thu thập chỉ được thực hiện sau khi kiểm tra điều khoản sử dụng, `robots.txt`, giới hạn truy cập và yêu cầu bảo vệ dữ liệu cá nhân của nguồn.

## 2. Câu hỏi và giả thuyết nghiên cứu

### 2.1. Câu hỏi nghiên cứu

- **RQ1:** Rating có xu hướng giảm khi số lượng review của quán tăng không?
- **RQ2:** Những từ khóa/cụm từ nào có ảnh hưởng mạnh nhất đến khả năng một review được đánh giá 1 sao?
- **RQ3:** Cách đánh giá có khác biệt giữa các vùng địa lý không? Độ dài bình luận có liên quan đến số sao không?

### 2.2. Giả thuyết đề xuất

**Giả thuyết A – mức độ phổ biến và rating**

- **H0A:** Sau khi kiểm soát các yếu tố như khu vực, loại món và phân khúc giá, số lượng review không có mối liên hệ có ý nghĩa thống kê với rating của quán.
- **H1A:** Sau khi kiểm soát các yếu tố trên, số lượng review có mối liên hệ âm có ý nghĩa thống kê với rating của quán.

**Giả thuyết B – nội dung bình luận và đánh giá 1 sao**

- **H0B:** Đặc trưng văn bản của bình luận không cải thiện đáng kể khả năng nhận diện review 1 sao so với mô hình baseline không dùng nội dung văn bản.
- **H1B:** Đặc trưng văn bản cải thiện đáng kể khả năng nhận diện review 1 sao; một số từ/cụm từ có sức dự báo nổi bật và ổn định.

Số lượng review chỉ là **biến đại diện cho mức độ phổ biến**, không phải phép đo trực tiếp mức độ đông khách. Vì vậy, kết quả của RQ1 chỉ cho phép kết luận về mối liên hệ, không tự động chứng minh quan hệ nhân quả “quán đông làm chất lượng giảm”.

Trước Report 1, nhóm cần chốt rõ một giả thuyết chính, biến mục tiêu, đơn vị quan sát, địa bàn, thời gian crawl, ngưỡng xác định review tiêu cực và tiêu chí kiểm định.

## 3. Dữ liệu dự kiến

Đơn vị dữ liệu chính là **một review**. Tùy khả năng thu thập hợp lệ của nguồn, schema dự kiến gồm:

| Nhóm trường | Ví dụ |
|---|---|
| Review | `review_id`, nội dung, rating, thời điểm đăng, thời điểm crawl |
| Quán | `restaurant_id`, tên quán, địa chỉ, khu vực, loại món, phân khúc giá |
| Tương tác | số lượt thích/phản hồi nếu nguồn công khai và cho phép thu thập |
| Trường dẫn xuất | độ dài bình luận, nhãn 1 sao, token/từ khóa, vùng địa lý |

Không thu thập hoặc công khai thông tin nhận dạng người dùng nếu không cần thiết cho giả thuyết. Mọi định danh phục vụ chống trùng lặp cần được loại bỏ hoặc băm trước khi đưa vào tập processed.

## 4. Kiến trúc dự kiến

- **MinIO:** Data Lake tương thích S3, lưu nguyên trạng JSON/HTML theo nguồn và từng lần crawl.
- **PostgreSQL:** lưu các bảng đã chuẩn hóa, dự kiến gồm `restaurants`, `reviews` và `crawl_runs`.
- **Python app:** ingestion, kiểm tra schema, loại trùng, làm sạch văn bản tiếng Việt, ETL và modeling.
- **RStudio/Jupyter:** EDA, kiểm định giả thuyết, trực quan hóa và so sánh mô hình.
- **Docker Compose:** khởi chạy MinIO, PostgreSQL và môi trường ứng dụng để demo toàn bộ pipeline.

Luồng dữ liệu bắt buộc:

```text
Crawl -> MinIO/Raw -> Cleaning & Validation -> PostgreSQL/Processed
      -> SQL quality checks -> EDA -> Modeling -> Evaluation
```

## 5. Cấu trúc repository

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
│   ├── 1_Exploration.ipynb
│   └── 2_Modeling.ipynb
└── reports/
    └── README.md
```

Các thư mục dữ liệu chỉ giữ `.gitkeep` hoặc sample nhỏ có tiền tố `sample_`. Không commit toàn bộ dữ liệu crawl, volume Docker, secrets, thông tin người dùng hoặc model artifacts.

## 6. Khởi động dự án (dự kiến)

Yêu cầu: Git, Docker Desktop có Docker Compose, Python 3.11+ và R/RStudio.

```bash
cp .env.example .env
docker compose up --build
```

Hiện tại `docker-compose.yml` và mã nguồn mới là scaffold. Khi pipeline được triển khai, phần này phải bổ sung lệnh crawl, ETL, kiểm tra chất lượng dữ liệu, huấn luyện mô hình và địa chỉ truy cập MinIO.

## 7. Kế hoạch theo 5 reports

| Tuần | Report | Nội dung phải hoàn thành |
|---|---|---|
| 1–2 | Report 1 – Project Planning | Bài toán, H0/H1, phạm vi crawl, sơ đồ kiến trúc Docker và repository chuẩn |
| 3–4 | Report 2 – Data Engineering | MinIO trên Docker; pipeline Crawl -> Raw -> PostgreSQL; SQL kiểm tra dữ liệu thô |
| 5–6 | Report 3 – EDA | Quy tắc làm sạch tiếng Việt, Data Dictionary, EDA và biểu đồ bằng RStudio |
| 7–8 | Report 4 – Modeling | Hai mô hình ML khác nhau, validation, metric, so sánh và kết luận giả thuyết |
| 9–10 | Report 5 – Deployment | `docker compose up`, demo end-to-end, báo cáo cuối và bảo vệ kết quả |

## 8. Kế hoạch phân tích và modeling

### Làm sạch và EDA

- Chuẩn hóa Unicode tiếng Việt nhưng giữ dấu để tránh mất nghĩa.
- Loại review trùng, HTML thừa, bản ghi thiếu rating và dữ liệu ngoài phạm vi.
- Xử lý emoji, tiếng lóng và từ viết tắt có quy tắc; không tùy tiện loại các từ phủ định như “không”, “chưa”.
- Kiểm tra phân phối rating, tỷ lệ review 1 sao, số review theo quán/khu vực và dữ liệu mất cân bằng.
- Dùng SQL để kiểm tra khóa trùng, giá trị thiếu, miền rating và tính toàn vẹn giữa bảng quán với bảng review.

### Mô hình dự kiến

- **Baseline:** mô hình chỉ dùng metadata như độ dài bình luận, khu vực và phân khúc giá.
- **Model 1:** Logistic Regression với TF-IDF, thuận tiện để giải thích từ/cụm từ quan trọng.
- **Model 2:** Linear SVM hoặc mô hình phân loại văn bản khác do nhóm lựa chọn và giải thích.

Với bài toán review 1 sao có thể mất cân bằng, không chỉ báo cáo accuracy. Cần ưu tiên Precision, Recall, F1-score, PR-AUC, confusion matrix và khoảng tin cậy hoặc cross-validation phù hợp.

Để hạn chế rò rỉ dữ liệu, các review trùng hoặc gần trùng phải ở cùng một tập; ưu tiên chia train/test theo quán hoặc theo thời gian thay vì chia ngẫu nhiên từng dòng mà không kiểm soát.

`Fatal keywords` được hiểu là các từ/cụm từ có sức dự báo mạnh và ổn định trong mô hình, không mặc nhiên là nguyên nhân khiến khách hàng chấm 1 sao.

## 9. Việc nhóm cần chốt trước khi code

- Chọn **một nguồn chính**: ShopeeFood hoặc Foody; nguồn còn lại chỉ dùng khi phạm vi và thời gian cho phép.
- Chọn địa bàn nghiên cứu và quy tắc ánh xạ vùng Bắc/Nam nếu dùng RQ3.
- Chọn RQ/giả thuyết chính để tránh triển khai dàn trải.
- Xác định quy mô mẫu tối thiểu, lịch crawl, giới hạn tốc độ và cơ chế tiếp tục khi crawl lỗi.
- Chốt schema raw, schema processed, Data Dictionary và quy tắc khử trùng lặp.
- Phân công owner cho ingestion, MinIO/SQL, cleaning/EDA, modeling và reports.
- Định nghĩa trước metric thành công và cách so sánh hai mô hình.

## 10. Quy ước làm việc

- Mỗi thành viên commit tối thiểu **2 lần/tuần**.
- Commit message phải rõ nghĩa, ví dụ: `feat: add foody review ingestion` hoặc `fix: preserve vietnamese negation tokens`.
- Không dùng các message chung chung như `update`, `final` hoặc `code`.
- Không commit `.env`, mật khẩu, access key, dữ liệu lớn, dữ liệu cá nhân hoặc volume cục bộ.
- Mọi lần dùng AI có ảnh hưởng đến dự án phải được ghi trong [`AI_Log.md`](AI_Log.md).
- Tạo branch theo dạng `feat/<ten-tinh-nang>`, mở pull request và review trước khi merge.

## 11. Tiêu chí hoàn thành tối thiểu

- `docker compose up --build` khởi động được hệ thống demo gồm MinIO, database và app/workstation.
- Dữ liệu tự crawl đi qua đủ luồng Raw (MinIO) -> Processed (PostgreSQL).
- Có SQL queries kiểm tra dữ liệu và Data Dictionary.
- Có EDA bằng RStudio theo yêu cầu Report 3; Jupyter có thể dùng bổ sung.
- Có ít nhất hai mô hình ML khác nhau, validation phù hợp và kết luận chấp nhận hoặc bác bỏ giả thuyết.
- Có đủ 5 reports, nhật ký AI và lịch sử commit đều đặn trong suốt học kỳ.

