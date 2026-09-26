# Đánh giá nguồn dữ liệu: beFood

1. **Platform:** beFood
2. **URL / endpoint:** Các trang danh mục và tìm kiếm (ví dụ: `https://food.be.com.vn/ho-chi-minh/danh-muc/...`)
3. **Cách lấy dữ liệu:** Dữ liệu review được nhúng trực tiếp trong mã nguồn HTML tĩnh (Server-Side Rendering). Khai thác bằng cách dùng `requests` gọi HTML và dùng `BeautifulSoup` bóc tách thẻ chứa nội dung.
4. **Các field quan sát được:** Áp dụng schema 14 trường. Thu thập thực tế được `restaurant_url`, `review_text`, `crawled_at`, nội suy thêm `restaurant_id`, `city`, `restaurant_name`. Các trường metadata người dùng đang thiếu do giới hạn SSR.
5. **Anti-bot / limitation:** Thấp (Low). Nền tảng không yêu cầu đăng nhập, không có CAPTCHA chặn luồng. Có nguy cơ bị rate limit nếu gửi request liên tục, đã khắc phục bằng hàm delay `time.sleep(2)`.
6. **Kết quả test crawl:** Tốt. Crawler 2 bước (quét URL danh mục -> cào review quán) hoạt động trơn tru.
7. **Số records crawl được:** 3,562 records.
8. **Đánh giá:** Recommended. Dữ liệu công khai, dễ tiếp cận, đáp ứng cực tốt về mặt số lượng văn bản review thô.
9. Thiết kế Schema (14 Fields) & Khả năng chuẩn hóa (Normalization)

Dữ liệu thô (Raw Data) được ép kiểu về schema 14 trường chuẩn của project ngay từ bước Ingestion với các lý do sau:

- **Đồng bộ hóa (Data Contract):** Đảm bảo cấu trúc data của nguồn beFood khớp 100% với các nguồn khác (Foody, ShopeeFood), giúp quá trình ETL và gộp bảng không bị xung đột.
- **Phục vụ Sentiment Analysis:** Lưu giữ đầy đủ Feature (`review_text`) và Label tiềm năng (`rating`) cho mô hình phân loại. Khai thác metadata (`city`, `restaurant_name`) để phục vụ EDA và Dashboard phân tích đa chiều.
- **Sẵn sàng cho chuẩn 3NF:** Dù hiện tại lưu dưới dạng Flat JSON, schema đã thiết kế sẵn các cột định danh (`restaurant_id`, `review_id`, `reviewer_id`). Khi load vào Data Warehouse (SQL), schema này dễ dàng được tách (Decompose) thành các bảng thực thể độc lập (Restaurants, Reviews, Users) để đạt chuẩn 3NF (Third Normal Form), giúp loại bỏ hoàn toàn dư thừa dữ liệu (Data Redundancy) và đảm bảo toàn vẹn tham chiếu.