# Hướng dẫn ETL từ Local JSON vào PostgreSQL (Theo Schema chung)

## 1. Cấu trúc Database Schema (7 bảng)
- `sources`: Quản lý nguồn dữ liệu (foody, tripadvisor, eatigo, capichi).
- `restaurants`: Thông tin chi tiết nhà hàng.
- `restaurant_opening_hours`: Giờ mở cửa theo tuần.
- `restaurant_cuisines`: Loại hình ẩm thực.
- `reviewers`: Thông tin người đánh giá.
- `reviews`: Bảng trung tâm chứa 20 cột đánh giá (hợp nhất chuẩn Union).
- `review_tags`: Các thẻ tag của review.

## 2. Cách thức chạy ETL trên máy cá nhân
1. Tải bộ data JSON thô của nhóm về máy và đặt vào thư mục local (ví dụ: `code/sang/data/raw/...`).
2. Cấu hình file kết nối PostgreSQL (Host: `localhost`, Port: `5432`, User: `postgres`, Pass: `postgres`, DB: `food_review`).
3. Chạy script Python để đọc file JSON từ local và insert trực tiếp vào PostgreSQL.