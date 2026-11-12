# Rà soát Data Cleaning & Preprocessing trên nguồn Capichi và BeFood (Tuấn)

**Phạm vi:** `code/tuan/src/` (`ingestion/`, `processing/cleaner.py`, `processing/raw_to_minio.py`, `processing/minio_to_postgres.py`, `storage/init_schema.sql`, `modeling/model.py`, `modeling/eda_detailed.py`), đối chiếu với `WEEK_3_database_design.md` và `WEEK_3_minio_schema_design.md`.

**Trạng thái dữ liệu thực tế:** Đã chạy toàn bộ pipeline thực tế từ Raw JSON -> MinIO -> PostgreSQL (`food_review`) với tổng cộng **2.126 nhà hàng đang hoạt động** (**1.822 nhà hàng** có >= 3 đánh giá), **56.665 bản ghi đánh giá gốc** trên bảng `reviews` và **56.708 bản ghi** sau khi nối bảng đa trị `restaurant_cuisines` (38.749 từ Capichi và 17.959 từ BeFood).

---

## 1. Kết luận chính

1. **Đã hoàn thiện pipeline làm sạch kỹ thuật (ETL Cleaning & Validation):** Quá trình đẩy dữ liệu từ Raw -> MinIO (`raw_to_minio.py`) -> PostgreSQL (`cleaner.py`, `minio_to_postgres.py`) đã xử lý chuẩn hóa định danh (`source_code`, `source_restaurant_id`, `source_review_id`), loại bỏ bản ghi trùng lặp, chuẩn hóa chuỗi rỗng về `NULL`, ép kiểu số cho `rating` và tách bảng chuẩn 3NF (`restaurants`, `reviews`, `reviewers`, `restaurant_cuisines`, `restaurant_opening_hours`).
2. **Chuẩn hóa đồng bộ Thang điểm 10 (Scale-10 Normalization) cho Report 3:** Giữ nguyên giá trị điểm gốc (thang 1–5) trong cơ sở dữ liệu PostgreSQL để bảo toàn tính nguyên bản của nguồn Capichi và BeFood (`rating_scale_max = 5`), đồng thời thực hiện quy đổi tuyến tính lên **thang điểm 10 (`rating_scale_10 = rating * 2.0`, miền giá trị 2.0–10.0)** tại tầng truy vấn phân tích (`eda_detailed.py`, `model.py`) nhằm đồng bộ hoàn toàn với nguồn Foody của nhóm.
3. **Đã triển khai bước phân loại danh mục tự động (Rule-based Categorization) và tiền xử lý NLP:** Khắc phục tình trạng thiếu nhãn ẩm thực (`Unknown` / `Chưa phân loại`) bằng đối sánh từ khóa để gán nhãn `cuisine` (Món Nhật Bản, Thức Ăn Nhanh, Món Hàn Quốc, Cà phê / Trà sữa...), đồng thời làm sạch văn bản đầu vào (lọc `NULL`/chuỗi khoảng trắng, chuẩn hóa chữ thường `LOWER()`, tách token đa ngôn ngữ bằng Regex) trước khi đưa vào `TfidfVectorizer`.
4. **Bảo toàn tính trung thực của dữ liệu (Data Integrity):** Tuân thủ đúng thiết kế 3NF: các trường không được API của BeFood và Capichi cung cấp (như `travel_date`, `device_name`, `total_views`, `total_pictures`, `money_spend`) được giữ nguyên là `NULL` trong bảng `reviews`, tuyệt đối không sinh dữ liệu giả (fake data).

---

## 2. Phân loại các bước xử lý đã triển khai

| Nhóm xử lý | Thực hiện trong code của Tuấn | Mức độ hoàn thành |
|---|---|---|
| **Cleaning giá trị (Value Cleaning)** | Trim khoảng trắng đầu/cuối, chuyển chuỗi rỗng `""` thành `NULL` ở bảng 3NF, lọc bỏ review thiếu ID hoặc thiếu `rating` | Đã chạy thực tế trên DB |
| **Chuẩn hóa & Ánh xạ (Schema Mapping)** | Đồng nhất cấu trúc JSON khác biệt giữa Capichi và BeFood về chung schema chuẩn (`source_code`, `review_text`, `rating`...) | Đã chạy thực tế trên DB |
| **Chuẩn hóa Thang điểm 10 (Scale Normalization)** | Giữ nguyên data gốc 1–5 trong DB; quy đổi tuyến tính `rating * 2.0` lên thang điểm 10 (2.0–10.0) trong toàn bộ truy vấn EDA, RQ1, RQ2 và Root Cause của Report 3 | Đã áp dụng trong Report 3 |
| **Bổ sung đặc trưng (Feature Enrichment)** | Tự động phân loại `cuisine` cho nhà hàng từ tên quán/thông tin mô tả thay vì để `Unknown` | Đã chạy thực tế trên DB |
| **Chuẩn hóa cấu trúc 3NF & Ràng buộc DB** | Tách bảng `restaurants`, `restaurant_cuisines`, `reviews`, `reviewers`; khóa chính kép `(source_code, id)` chống trùng lặp | Đã chạy thực tế trên DB |
| **Tiền xử lý phục vụ EDA & NLP** | Lọc `TRIM(review_text) <> ''`, chuẩn hóa `lower()`, Regex phân nhóm lỗi vận hành và trích xuất N-grams (1,2) với `min_df=5` | Đã chạy thực tế (`model.py`) |

---

## 3. Chi tiết quy trình xử lý qua từng giai đoạn

### 3.1. Tầng Ingestion & Lưu trữ MinIO (`raw_to_minio.py`)
- **Kiểm soát nguồn (`source_code`):** Gán nhãn chuẩn `'capichi'` và `'befood'`, định tuyến lưu trữ object trên MinIO theo đúng cấu trúc phân cấp của thiết kế.
- **Loại trùng & Kiểm tra định danh:** Đảm bảo mỗi nhà hàng (`source_restaurant_id`) và mỗi đánh giá (`source_review_id`) có định danh hợp lệ trước khi đóng gói đẩy lên MinIO.

### 3.2. Tầng Cleaning & Transform (`cleaner.py` & `minio_to_postgres.py`)
- **Xử lý chuỗi văn bản (`review_text`, `name`, `city`):**
  - Thực hiện `.strip()` để cắt khoảng trắng thừa ở hai đầu.
  - Chuỗi rỗng hoặc chỉ chứa khoảng trắng được chuyển về `None` (tương ứng `NULL` trong PostgreSQL).
  - Giữ nguyên các ký tự đa ngôn ngữ (tiếng Việt có dấu, tiếng Nhật Kanji/Hiragana/Katakana, tiếng Hàn Hangul, tiếng Anh) và các ký hiệu phân dòng `\n` hoặc nhãn đánh giá nhanh của BeFood (như `"Đáng đồng tiền, Đóng gói tốt"`).
- **Xử lý kiểu số, Thang điểm & Thời gian:**
  - Tại tầng lưu trữ Database (`reviews`): Bảo toàn điểm `rating` gốc trên thang 1.0–5.0 theo đúng thiết kế bảng `sources` (`rating_scale_max = 5`).
  - Tại tầng phân tích & báo cáo (Report 3): Thực hiện chuẩn hóa tuyến tính lên **thang điểm 10 (`rating * 2.0`)**, giúp các mức điểm 1–5 sao chuyển thành `2.0, 4.0, 6.0, 8.0, 10.0` (điểm trung bình quán của BeFood đạt **6,18/10**, Capichi đạt **8,88/10**; ngưỡng đánh giá thấp `Rating <= 3` trên thang 5 tương ứng với `Rating <= 6.0` trên thang 10).
  - Các trường thiếu ở nguồn gốc (như `total_reviews` của reviewer trên một số luồng raw bị nhận diện là `nan` ở bảng `raw_reviews`) được tách biệt hoàn toàn khỏi bảng phân tích chính `reviews`.
- **Chuẩn hóa địa danh (`city`) & Phong cách ẩm thực (`cuisine`):**
  - Chuẩn hóa slug thành phố (`ho-chi-minh`, `ha-noi`, `khu-vuc-5`...). Nếu thiếu trong truy vấn phân tích sẽ được xử lý qua `COALESCE(rest.city, 'Chưa rõ')`.
  - Ánh xạ các nhà hàng vào bảng `restaurant_cuisines` theo nhóm chuẩn: `Thức Ăn Nhanh`, `Món Nhật Bản`, `Món Hàn Quốc`, `Cà phê / Trà sữa`, `Món Ấn Độ`, `Món Thái Lan`, `Món Việt Nam / Khác`.

### 3.3. Tầng Nạp PostgreSQL (`init_schema.sql` & `load_to_db_minio.py`)
- **Khóa chính ghép (Composite Primary Key):** Sử dụng cặp `(source_code, source_restaurant_id)` cho bảng `restaurants` và `(source_code, source_review_id)` cho bảng `reviews`, đảm bảo ID giữa Capichi và BeFood không bao giờ bị xung đột và chống chèn trùng dữ liệu khi chạy lại pipeline.
- **Xử lý `NULL` đúng chuẩn 3NF:** Các cột nâng cao (`reviewer_id`, `reviewer_name_raw`, `review_title`, `travel_date`, `device_name`, `total_views`, `total_pictures`, `total_likes`, `total_comments`, `guest_count`, `visit_again`, `money_spend`) được giữ trạng thái `[NULL]` khi nguồn không có dữ liệu.

### 3.4. Tầng Tiền xử lý cho Phân tích EDA & Mô hình NLP (`eda_detailed.py` & `model.py`)
- **Lọc nhiễu trước khi đưa vào mô hình:**
  - Tại câu truy vấn SQL đầu vào cho mô hình: áp dụng điều kiện lọc cứng `WHERE rev.review_text IS NOT NULL AND TRIM(rev.review_text) <> '' AND rev.rating IS NOT NULL` (tỷ lệ thiếu Text và thiếu Rating trên 56.665 bản ghi đều bằng **0,0%**).
  - Tại bài toán tương quan quy mô (RQ1): lọc bỏ các quán có quá ít đánh giá (`HAVING COUNT(rev.source_review_id) >= 3`) để giữ lại **1.822 nhà hàng** đủ độ tin cậy thống kê (điểm trung bình nhóm `>100 reviews` đạt **9,30/10**).
- **Tiền xử lý văn bản đa ngôn ngữ & Trọng số hồi quy Thang 10:**
  - Chuyển toàn bộ văn bản về chữ thường (`sub_df['review_text'].str.lower()`).
  - Sử dụng biểu thức chính quy Unicode `token_pattern=r'(?u)\b\w+\b'` kết hợp `ngram_range=(1, 2)` và ngưỡng tần suất `min_df=5` trong `TfidfVectorizer` kết hợp `Ridge Regression` trên biến mục tiêu đã chuẩn hóa thang 10 (`rating * 2.0`), giúp trích xuất chính xác trọng số tác động trên thang điểm 10 của từng từ khóa (ví dụ trên BeFood: `'hơi'` +4,622, `'5 sao'` +4,568, `'làm đúng'` +4,196, `'not delicious'` -5,774, `'không hợp'` -5,040; trên Capichi: `'change'` +3,018, `'terrible'` -6,244, `'tệ'` -6,214, `'美味しくない'` -5,652).

---

## 4. Bảng đối chiếu kết quả xử lý trên dữ liệu thật

| Trường hợp dữ liệu thực tế | Cách xử lý trong Pipeline | Kết quả trong PostgreSQL / Report 3 (Thang 10) |
|---|---|---|
| Nguồn BeFood không trả về `total_views`, `device_name`, `travel_date` | Không tự gán giá trị 0 hay chuỗi giả; ánh xạ thành `None` khi nạp bảng 3NF | Hiển thị `[NULL]` chuẩn xác trên bảng `reviews` |
| Đồng bộ thang điểm giữa Capichi/BeFood (thang 5) và Foody (thang 10) | Giữ nguyên điểm gốc 1–5 trong DB; nhân hệ số `2.0` (`rating * 2.0`) khi chạy truy vấn EDA & Modeling | Điểm chuẩn hóa về thang `2.0 – 10.0` (TB quán BeFood: **6,18/10**, Capichi: **8,88/10**) |
| Review có `review_text` bị trống hoặc chỉ có khoảng trắng | Lọc bằng `WHERE rev.review_text IS NOT NULL AND TRIM(rev.review_text) <> ''` | **56.665** bản ghi gốc trên bảng `reviews` (**56.708** dòng sau khi `LEFT JOIN restaurant_cuisines`) |
| Nhà hàng chỉ có 1–2 đánh giá làm lệch điểm trung bình | Lọc ở bước tổng hợp bằng `HAVING COUNT(rev.source_review_id) >= 3` | Giữ lại **1.822** nhà hàng đủ độ tin cậy thống kê |
| Văn bản chứa nhiều ngôn ngữ (Việt, Nhật, Anh, Hàn) và từ viết tắt (`"ko"`, `"sốp"`) | Tách phân tích theo từng `source_code`, dùng `TfidfVectorizer(ngram_range=(1,2), min_df=5)` | Trích xuất chính xác trọng số từ khóa trên thang 10 của từng nền tảng mà không làm mất nghĩa gốc |