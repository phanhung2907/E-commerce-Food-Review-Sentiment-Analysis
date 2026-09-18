# Báo cáo Quá trình Crawl Dữ liệu ShopeeFood - Võ Quốc Tuấn

## 1. Khảo sát hệ thống và Phát hiện kiến trúc
*   **Mục tiêu ban đầu:** Thu thập dữ liệu đánh giá từ nền tảng ShopeeFood.
*   **Phát hiện thực tế (Qua F12 Network):** Khi kiểm tra luồng dữ liệu trên ShopeeFood, tôi phát hiện ra giao diện của ShopeeFood thực chất gọi ngầm dữ liệu từ hệ thống API của Foody. 
*   **Kết luận:** Việc trỏ tool crawl vào endpoint của Foody không phải là lỗi đi sai hướng, mà là đã đánh trúng "kho chứa gốc" (backend) quản lý review của toàn bộ hệ thống ShopeeFood/Foody.

## 2. Tiến độ hoàn thành Checklist Tuần 2
Chiếu theo checklist yêu cầu của team, tôi đã hoàn thành các hạng mục sau:
*   [x] **Tìm Restaurant listing endpoint:** Đã xác định được API `search_global` để lấy danh sách quán và `restaurant_id`.
*   [x] **Tìm Review endpoint & Pagination:** Đã nắm được cơ chế gọi API review và cách hệ thống phân trang (dùng tham số LastId/t).
*   [x] **Trích xuất các trường dữ liệu (Data Fields):** Xác thực đầy đủ các trường yêu cầu: `review_text` (Comment/Description), `rating`, `review_date`, `restaurant_id`, v.v.
*   [x] **Test & Sample Data:** Đã test thành công trên các quán chỉ định và thu thập được tập dữ liệu 100 dòng mẫu. File dữ liệu hiện đã được lưu gọn gàng tại: `data/raw/raw_reviews.csv`.

## 3. Vấn đề Tự động hóa (Firewall) và Hướng giải quyết
*   **Quá trình triển khai script:** Cố gắng tự động hóa quá trình cào trên diện rộng bằng file `shopee_crawler.py`.
*   **Vấn đề gặp phải:** Khi code chạy vòng lặp, hệ thống anti-bot/firewall chặn request ngầm (trả về mảng rỗng) dù đã setup Headers giả lập.
*   **Hướng giải quyết & Next Steps:** 
    *   Tập sample data 100 dòng trong `raw_reviews.csv` hiện tại đã hoàn toàn đạt chuẩn, sạch sẽ và có đầy đủ text/rating.
    *   Để đảm bảo không làm chậm tiến độ chung của nhóm, em sẽ sử dụng ngay file `raw_reviews.csv` này làm đầu vào cho bước phân tích cảm xúc (Sentiment Analysis).
    *   Công việc tiếp theo sẽ được thực hiện trực tiếp trên file `notebooks/2_Modeling.ipynb`. Quá trình bypass firewall để cào data quy mô lớn (scale) có thể đưa vào backlog nghiên cứu sau.

    "Chi tiết mã nguồn gọi API, giả lập Headers và vòng lặp đã được đính kèm trong các file crawler.py và shopee_crawler.py tại thư mục src/ingestion."