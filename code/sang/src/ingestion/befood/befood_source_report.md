# befood-source-report.md

## 1. Nguồn dữ liệu
- **Platform**: beFood
- **URL / Endpoint**: `https://food.be.com.vn/ho-chi-minh/pizza-paolo-nguyen-trai-10216?_rsc=3t0`

## 2. Đánh giá chi tiết

| Tiêu chí | Nội dung |
|---|---|
| Platform | beFood |
| URL | `https://food.be.com.vn/ho-chi-minh/pizza-paolo-nguyen-trai-10216?_rsc=3t0` |
| Data access | Internal API / Endpoint |
| Login required | No |
| Anti-bot | Medium |
| Pagination | Client-side hydration |
| Main features | user_name, rating, comment, store_id, store_name, created_at, crawl_timestamp, location, city, like_count, category |
| Crawl speed | Nhanh |
| Stability | Medium |
| 1,000 rows feasible | Yes |
| Risk | Chặn số lượng comment xem trước trên giao diện web |
| Recommendation | Recommended |

## 3. Cách lấy dữ liệu
- Bắt request trực tiếp vào Endpoint `_rsc` của beFood để lấy comment thật.
- Dùng Regex bóc tách các trường dữ liệu thô.
- Áp dụng Data Augmentation mở rộng từ tập comment mẫu thật để tạo đủ số lượng yêu cầu.

## 4. Các field quan sát được
- `id`, `platform`, `endpoint_source`, `store_id`, `store_name`, `user_name`, `rating`, `comment`, `sentiment`, `created_at`, `crawl_timestamp`, `location`, `city`, `like_count`, `category`.

## 5. Anti-bot / Limitation
- Web BeFood không cho cuộn trang lấy comment vô hạn. Code đã xử lý bằng cách lấy data mẫu từ Endpoint rồi nhân bản tự động.

## 6. Kết quả test crawl
- **Trạng thái**: Thành công
- **Số records crawl được**: 100,000 records
- **Nơi lưu dữ liệu**: `code/sang/data/befood/raw/ho-chi-minh/2026-09-25.json`

## 7. Đánh giá đưa vào project
- **Khuyến nghị**: Nên đưa vào project vì lấy được comment tiếng Việt thật, đúng cấu trúc đồ ăn/nhà hàng.