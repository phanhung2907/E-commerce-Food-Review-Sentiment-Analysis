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

