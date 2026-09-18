# Báo cáo: Thiết kế Schema PostgreSQL và Đối chiếu Dữ liệu

## 1. Schema Database (PostgreSQL)
Cấu trúc cơ sở dữ liệu được chia làm 2 bảng chính (`restaurants` và `reviews`) nhằm đảm bảo chuẩn hóa dữ liệu (Normalization). Chi tiết mã nguồn SQL được đặt tại thư mục `src/storage/init_schema.sql`.

## 2. Chứng minh sự phù hợp (Data Mapping)
Dữ liệu thô thu thập được (file `raw_reviews.csv`) hoàn toàn tương thích và đổ vừa vặn vào Schema này mà không bị suy hao thông tin:

*   **restaurant_id:** Khớp trực tiếp với Khóa chính (PK) của bảng `restaurants` và Khóa ngoại (FK) của bảng `reviews`.
*   **review_text (Comment):** Map vào trường `review_text` (kiểu TEXT, cho phép lưu chuỗi ký tự dài).
*   **rating (Điểm số):** Map vào trường `rating` (kiểu FLOAT).
*   **review_date:** Map vào trường `review_date` (kiểu TIMESTAMP).
*   **city/location & total_reviews:** Map trực tiếp vào bảng `restaurants`.

**Kết luận:** Schema hoàn toàn đáp ứng được cấu trúc của tập dữ liệu đã crawl.