# Báo Cáo Thu Thập Dữ Liệu - Nguồn: BeFood
**Dự án:** E-commerce Food Review Sentiment Analysis
**Người thực hiện:** Võ Quốc Tuấn
**Thời gian:** 27/09/2026

---

## 1. Luồng Crawl & Phương Pháp Kỹ Thuật

Quá trình cào dữ liệu từ nền tảng BeFood gặp phải 2 lớp phòng thủ từ hệ thống, và đã được giải quyết triệt để trong bản source code chính thức:

*   **Vượt rào kiến trúc Next.js (RSC Payload):** BeFood không render dữ liệu vào các thẻ HTML tĩnh (`__NEXT_DATA__`) hay gọi API JSON thông thường. Dữ liệu bị giấu trong luồng payload mã hóa chằng chịt của React Server Components. 
    *   *Phương pháp giải quyết:* Bỏ qua thư viện parse HTML truyền thống (BeautifulSoup). Trực tiếp dùng **Regex (Biểu thức chính quy)** quét toàn bộ văn bản phản hồi thô để "móc" chính xác cấu trúc `r'"rating":([0-9.]+),"feedback":"(.*?)"'`[cite: 26].
*   **Xử lý lỗi Font chữ (Mojibake Double-Encoding):** Máy chủ BeFood trả về tiếng Việt bị lỗi font nặng (ví dụ: `"nhiá» u Ä‘á»“ Äƒn"`). Ép kiểu UTF-8 thông thường không tác dụng.
    *   *Phương pháp giải quyết:* Sử dụng kỹ thuật **Ép kiểu ngược (Double-decoding)**: Ép chuỗi rác về byte gốc bằng chuẩn `latin-1`, sau đó mới decode bung ra lại bằng `utf-8` kết hợp `unicode_escape`[cite: 26]. Kết quả: Tiếng Việt hiển thị chuẩn 100%[cite: 27].
*   **Chống Ban IP:** Tích hợp `time.sleep(2)` giữa các lần chuyển quán để mô phỏng người dùng thật[cite: 26], đảm bảo an toàn khi treo máy crawl số lượng lớn qua đêm.

---

## 2. Cấu Trúc Dữ Liệu & Ý Nghĩa Các Features Đã Thiết Lập

File JSON xuất ra không chỉ chứa dữ liệu thô mà đã được thực hiện **Feature Engineering** ngay từ lúc cào[cite: 26]. Các trường này sinh ra để phục vụ trực tiếp cho model AI sau này.

### Nhóm thông tin định danh (Cơ bản)
*   `source`, `restaurant_id`, `restaurant_name`, `restaurant_url`, `crawled_at`: Lưu lại nguồn gốc xuất xứ của từng câu review để sau này trace bug hoặc làm Dashboard lọc theo quán.

### Nhóm Feature Cảm xúc & Hành vi (Khai thác từ Text)
Thay vì để model AI tự học một cách khó nhọc từ chữ, code đã tự động bóc tách các hành vi của khách hàng thành các cột số liệu cụ thể:

*   `sentiment_label` (Positive/Negative/Neutral): Quy đổi thẳng từ số sao rating. Khách chấm 1-2 sao tự động dán nhãn Negative[cite: 26]. **Thực tế:** Giúp chúng ta có sẵn cột Target (Label) để train mô hình phân loại cảm xúc mà không cần gán nhãn bằng tay.
*   `text_length` & `word_count`: Đếm số ký tự và số từ[cite: 26]. **Thực tế:** Khách hàng khi chê bai hoặc bóc phốt thường viết một đoạn văn rất dài và chi tiết. Khách khen đôi khi chỉ lười biếng thả 1 chữ "ngon"[cite: 27]. Chiều dài câu là một tín hiệu cực mạnh để AI đoán biết mức độ cảm xúc.
*   `exclamation_count` & `question_count`: Đếm dấu chấm than (!) và dấu hỏi (?)[cite: 26]. **Thực tế:** Chả ai bình thường lại xài nhiều dấu chấm than. Khi khách hàng bực tức tột độ ("Tệ quá!!!") hoặc quá phấn khích, họ mới gõ dấu này. Đếm dấu câu giúp model đo lường được "thái độ" cường điệu của người viết.
*   `contains_emoji`: Trả về True/False nếu câu có chứa icon[cite: 26]. **Thực tế:** Dùng icon mặt phẫn nộ hay icon trái tim thường đi kèm liền với trạng thái tiêu cực hay tích cực.

### Nhóm Feature Phân loại Chủ đề (Topic Extraction bằng Regex)
Khi khách chửi (Negative), chúng ta cần biết họ chửi cái gì. Code đã dùng Regex bắt từ khóa để tạo ra 3 cột True/False[cite: 26]:
*   `mention_delivery`: Bắt các chữ *shipper, giao, trễ, đợi...* **Thực tế:** Giúp model phân biệt được khách cho 1 sao là do Shipper giao chậm (lỗi khách quan) hay do đồ ăn dở thật[cite: 27].
*   `mention_price`: Bắt các chữ *mắc, đắt, rẻ, tiền...* **Thực tế:** Lọc ra những review nhạy cảm về giá[cite: 27].
*   `mention_packaging`: Bắt các chữ *hộp, đổ, tràn, bao bì...* **Thực tế:** Tách biệt lỗi đóng gói móp méo đổ tháo ra khỏi lỗi khẩu vị của đầu bếp[cite: 27].

-----
# Báo Cáo Thu Thập Dữ Liệu Nguồn Capichi

## 1. Báo cáo Dữ liệu (Data Structure)
Dữ liệu được thu thập và lưu trữ dưới định dạng `JSON`. Mỗi bản ghi (record) đại diện cho một bài đánh giá của khách hàng, bao gồm 15 trường dữ liệu (features) đã được chuẩn hóa để phục vụ cho bài toán Sentiment Analysis:

*   **Thông tin hệ thống:**
    *   `source`: Nguồn dữ liệu (Mặc định: "Capichi").
    *   `crawl_timestamp`: Dấu thời gian lúc hệ thống cào dữ liệu (ISO 8601).
*   **Thông tin Nhà hàng:**
    *   `restaurant_id`: Mã ID định danh của nhà hàng trên hệ thống Capichi.
    *   `restaurant_name`: Tên nhà hàng.
    *   `restaurant_url`: Đường link dẫn đến trang của nhà hàng.
    *   `city`: Khu vực tỉnh/thành phố (Ví dụ: Hà Nội, Đà Nẵng).
    *   `category`: Phân loại ẩm thực của quán (Hiện tại đa số API trả về "Không xác định").
    *   `total_reviews`: Tổng số lượng bình luận của quán trên nền tảng.
    *   `restaurant_rating`: Điểm đánh giá trung bình của toàn bộ quán.
*   **Thông tin Đánh giá (Review):**
    *   `review_id`: Mã định danh duy nhất của từng bài bình luận.
    *   `reviewer_id`: Mã định danh người dùng (thường trả về `null` do bảo mật của API).
    *   `rating`: Điểm số khách hàng chấm cho bữa ăn (từ 1 đến 5).
    *   `review_date`: Thời gian khách hàng đăng bình luận.
    *   `review_text`: Nội dung văn bản bình luận chi tiết.
    *   `language`: **(Feature xử lý NLP)** Mã ngôn ngữ của bình luận (`vi`, `en`, `ja`, `ko`...) được tự động nhận diện bằng thư viện `langdetect`.

## 2. Luồng Crawl và Phương pháp (Crawling Flow & Methodology)
Source code sử dụng phương pháp gọi trực tiếp API của Capichi thông qua thư viện `requests` (không dùng Selenium để tối ưu tốc độ và tài nguyên). 

**Kiến trúc hệ thống chia làm 2 tầng (Master - Worker):**
1.  **Tầng Master (`get_all_restaurants`):** 
    *   Nhiệm vụ: Quét mảng khu vực (Province ID từ 1 đến 10) để vét sạch toàn bộ ID nhà hàng trên hệ thống. 
    *   Kỹ thuật: Xử lý phân trang (pagination) tự động qua endpoint `/api/v107/food_booking/restaurants`. Nếu trang rỗng, tự động ngắt và chuyển khu vực.
2.  **Tầng Worker (`crawl_capichi_reviews`):**
    *   Nhiệm vụ: Nhận ID từ Master, truy cập vào endpoint `/api/v106/food_booking/restaurants/{store_id}/review_list` để rút trích bình luận.
    *   Kỹ thuật: Sử dụng `Set` để kiểm tra trùng lặp `review_id`. Tích hợp thư viện `langdetect` để bắt ngôn ngữ ngay tại thời điểm cào (tránh việc phải tiền xử lý ngôn ngữ sau này). Bỏ qua các bình luận rỗng (chỉ có sao, không có text).

**Cơ chế an toàn (Safe-guards):**
*   **Anti-block:** Fake `User-Agent` và thiết lập `time.sleep(1)` sau mỗi lượt request để tránh bị máy chủ Capichi chặn IP.
*   **Checkpoint Guardian:** Cứ sau khi cào xong 10 nhà hàng, hệ thống tự động ghi đè dữ liệu tạm thời ra file `capichi_checkpoint.json` để phòng hờ cúp điện hoặc crash chương trình.

## 3. Source Code Chính Thức
File source code hoàn chỉnh để treo máy đêm nay nằm tại: `code/tuan/src/ingestion/capichi/capichi_crawler.py`.

**Hướng dẫn sử dụng cho team:**
1. Cài đặt thư viện cần thiết: `pip install requests langdetect`
2. Chạy lệnh khởi động: `python capichi_crawler.py`
3. Quá trình cào hoàn toàn tự động, file dữ liệu cuối cùng sẽ được lưu tại `code/tuan/data/capichi/raw/` với định dạng `capichi_final_YYYYMMDD.json`.