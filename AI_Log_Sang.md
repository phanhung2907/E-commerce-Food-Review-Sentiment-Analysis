## Nhật ký làm việc với AI - Cào dữ liệu Foody

**Mục tiêu:** 
Hoàn thành Source Feasibility Check cho nguồn Foody: Tìm API, kiểm tra phân trang và viết script lấy hơn 100 sample reviews.

**Quá trình thực hiện:**
1. Mở Developer Tools (F12) > Tab Network > Fetch/XHR.
2. Tìm được request API: `[https://www.foody.vn/__get/Review/ResLoadMore](https://www.foody.vn/__get/Review/ResLoadMore)`.
3. Xác định được cơ chế phân trang (pagination) thông qua tham số `LastId` trong Payload.
4. Trích xuất thành công các field bắt buộc: `review_text`, `rating`, `review_date`, `restaurant_id`, `total_reviews`, `city`.


