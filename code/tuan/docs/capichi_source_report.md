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