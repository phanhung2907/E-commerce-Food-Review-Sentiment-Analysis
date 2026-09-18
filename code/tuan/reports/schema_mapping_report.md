# Báo cáo: Thiết kế Schema PostgreSQL Chuẩn 3NF và Đối chiếu Dữ liệu

## 1. Cấu trúc Schema Database & Chuẩn hóa (3NF)
Cơ sở dữ liệu được thiết kế gồm 2 bảng chính nhằm tuân thủ tuyệt đối các nguyên tắc chuẩn hóa dữ liệu (Normalization) đến dạng chuẩn 3NF, bám sát thực tế các trường dữ liệu thu thập được từ dự án:
*   **Bảng `restaurants` (Thông tin quán ăn):** Lưu trữ các thuộc tính định danh và mô tả chung của quán. Khóa chính là `restaurant_id`. Các trường dữ liệu phụ thuộc hoàn toàn vào khóa chính (đạt chuẩn 2NF và 3NF).
*   **Bảng `reviews` (Dữ liệu đánh giá chi tiết):** Lưu trữ nội dung từng lượt review. Sử dụng `restaurant_id` làm khóa ngoại (Foreign Key) liên kết sang bảng `restaurants`. Việc tách bảng này giúp tuyệt đối không lưu lặp lại thông tin tên quán hay thành phố ở từng dòng đánh giá, qua đó triệt tiêu sự phụ thuộc bắc cầu và đạt chuẩn 3NF.

Chi tiết mã nguồn SQL được lưu tại thư mục: code/tuan/src/storage/init_schema.sql

## 2. Chứng minh sự phù hợp (Data Mapping - Phân bổ 14 Fields)
Dữ liệu thô thu thập được (file `raw_reviews.csv`) tương thích và ánh xạ hoàn toàn 100% vào Schema cơ sở dữ liệu mà không bị dư thừa hay suy hao thông tin:

*   **Nhóm thuộc tính quán ăn (Bảng `restaurants`):**
    *   `restaurant_id`: Khớp trực tiếp với Khóa chính (Primary Key).
    *   `restaurant_name`: Map vào trường `restaurant_name`.
    *   `restaurant_url`: Map vào trường `restaurant_url`.
    *   `city`: Map vào trường `city` (Phục vụ phân tích theo vùng/khu vực).
    *   `category`: Map vào trường `category` (Phân loại ẩm thực).
    *   `total_reviews`: Map vào trường `total_reviews` (Số lượng tổng review của quán).
    *   `restaurant_rating`: Bổ sung trường điểm đánh giá tổng quan của quán.

*   **Nhóm thuộc tính đánh giá (Bảng `reviews`):**
    *   `review_id`: Khớp trực tiếp với Khóa chính (Primary Key).
    *   `restaurant_id`: Khớp với Khóa ngoại (Foreign Key) để đồng bộ quan hệ với bảng quán.
    *   `source`: Map vào trường `source` (Nguồn nền tảng crawl, ví dụ: "Foody").
    *   `review_text`: Map vào trường `review_text` (kiểu dữ liệu TEXT phục vụ bài toán Sentiment Analysis).
    *   `rating`: Map vào trường `rating` (kiểu FLOAT chứa điểm số sao).
    *   `review_date`: Map vào trường `review_date` (kiểu TIMESTAMP phục vụ phân tích thời gian).
    *   `reviewer_id`: Map vào trường `reviewer_id` (Mã định danh người đánh giá để kiểm tra hành vi trùng lặp).
    *   `crawl_timestamp`: Trường hệ thống tự động ghi nhận mốc thời gian crawl dữ liệu thực tế.

**Kết luận:** Mô hình cơ sở dữ liệu được thiết kế đạt chuẩn 3NF, vừa tối ưu hóa hiệu năng lưu trữ, vừa phản ánh chính xác, đầy đủ cấu trúc thực tế của tập dữ liệu phân tích cảm xúc.