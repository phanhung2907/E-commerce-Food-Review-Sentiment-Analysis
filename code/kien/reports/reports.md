# BÁO CÁO KỸ THUẬT: THU THẬP & KHAI THÁC DỮ LIỆU TRIPADVISOR (MASS-SCALE CRAWLING)
**Thành viên thực hiện:** Kiên  
**Mục tiêu:** Thu thập dữ liệu quy mô lớn (Mass-scale) phục vụ mô hình Phân tích Cảm xúc (Sentiment Analysis).

---

## 1. Cấu Trúc Dữ Liệu & Ý Nghĩa Các Features
Dữ liệu thu thập được thiết kế theo mô hình kết hợp giữa thông tin cấp độ nhà hàng (Restaurant-Level) dựa trên chuẩn **Schema.org (`application/ld+json`)** và cấp độ đánh giá chi tiết (Review-Level) nhằm đảm bảo tính toàn diện cho bài toán Data Science.

### A. Restaurant-Level Features (Thuộc tính định danh & metadata nhà hàng)
* **`restaurant_id`**: Mã định danh duy nhất của nhà hàng được bóc tách tự động từ URL (ví dụ: `-d10721705-`). Giúp phân biệt các nhà hàng trên hệ thống.
* **`restaurant_name`**: Tên chính thức của nhà hàng hiển thị trên giao diện TripAdvisor.
* **`restaurant_url`**: Đường dẫn URL gốc của trang chi tiết nhà hàng trên TripAdvisor.
* **`city`**: Thành phố chứa nhà hàng (Quy Nhơn, TP. Hồ Chí Minh, Hà Nội), phục vụ việc phân loại dữ liệu theo vùng miền.
* **`@id`**: Đường dẫn URL chuẩn tắc (Canonical URL) định danh nhà hàng theo chuẩn Schema.org.
* **`address`**: Đối tượng/chuỗi chứa địa chỉ chi tiết (số nhà, tên đường, phường, thành phố, mã bưu chính).
* **`aggregateRating`**: Chứa thông tin tổng quan gồm `ratingValue` (Điểm đánh giá trung bình, ví dụ: 4.6) và `reviewCount` (Tổng số lượng đánh giá trên nền tảng).
* **`geo`**: Tọa độ địa lý gồm `latitude` (vĩ độ) và `longitude` (kinh độ), phục vụ cho việc định vị bản đồ và không gian.
* **`image`**: Đường dẫn URL hình ảnh chất lượng cao đại diện cho nhà hàng.
* **`openingHoursSpecification`**: Khung thời gian mở cửa chi tiết theo các ngày trong tuần.
* **`priceRange`**: Khoảng giá dịch vụ của nhà hàng (ký hiệu theo mức độ từ `$` đến `$$$$`).
* **`servesCuisine`**: Danh sách các thể loại ẩm thực mà nhà hàng phục vụ (ví dụ: *Asian, Vietnamese, Healthy, Street Food*).
* **`telephone`**: Số điện thoại liên hệ chính thức của nhà hàng.

### B. Review-Level Features (Thuộc tính nội dung đánh giá)
* **`review_id`**: Mã định danh duy nhất cho từng bản đánh giá (được cấu trúc bằng ID nhà hàng kết hợp số trang và thứ tự thẻ).
* **`reviewer_id`**: Mã định danh tương đối của người viết đánh giá trong phiên cào.
* **`review_title`**: Tiêu đề ngắn gọn của bài đánh giá do người dùng đặt.
* **`review_text`**: Nội dung chi tiết của bình luận/đánh giá (Đây là feature cốt lõi nhất dùng để đưa vào mô hình NLP/Sentiment Analysis).
* **`rating`**: Điểm số sao cá nhân mà người dùng chấm cho trải nghiệm của họ.
* **`review_date`**: Ngày tháng bài đánh giá được đăng tải lên hệ thống.
* **`travel_date`**: Thời gian thực tế mà người dùng thực hiện chuyến đi/trải nghiệm.
* **`feature_depth_status`**: Nhãn trạng thái đánh giá mức độ hoàn thiện dữ liệu (*Schema-Full-Features-Validated*).

---

## 2. Luồng Crawl & Phương Pháp Kỹ Thuật

Hệ thống crawl được xây dựng theo mô hình **Pipeline 2 Giai Đoạn** nhằm tối ưu hóa hiệu suất và tránh tình trạng sót dữ liệu:

1. **Giai đoạn 1 (Discovery & URL Harvesting):** 
   * Truy cập vào các trang danh mục thành phố (`City Listing Pages`) trên TripAdvisor.
   * Thực thi hành vi cuộn trang tự động (Auto-scrolling) kết hợp thời gian nghỉ ngẫu nhiên (`random.uniform`) để ép tải toàn bộ danh sách nhà hàng.
   * Trích xuất và lọc ra danh sách toàn bộ các URL chi tiết của nhà hàng (`Restaurant_Review`).

2. **Giai đoạn 2 (Deep Extraction & Incremental Parsing):**
   * Duyệt qua từng URL nhà hàng đã thu thập được ở giai đoạn 1.
   * Trích xuất trực tiếp các thẻ dữ liệu ẩn cấu trúc **`application/ld+json`** để lấy trọn vẹn thông tin metadata chuẩn Schema.org của nhà hàng.
   * Tiếp tục chuyển xuống khu vực các thẻ review, thực hiện cuộn trang qua các trang phân trang (pagination) để vét cạn nội dung bình luận của khách hàng.

3. **Cơ chế chống quét & An toàn hệ thống (Anti-Blocking & Resilience):**
   * **Undetected ChromeDriver (`uc`):** Giúp ẩn danh tính trình duyệt tự động, vượt qua các lớp kiểm duyệt bot nâng cao (như Cloudflare / DataDome) của TripAdvisor.
   * **Random Delays (`time.sleep(random.uniform(...))):** Giả lập hoàn hảo hành vi duyệt web ngẫu nhiên của con người, giảm thiểu tối đa rủi ro bị khóa địa chỉ IP (`Access is restricted`).
   * **Incremental JSON Saving:** Ghi dữ liệu dạng cuốn chiếu xuống ổ cứng ngay sau khi hoàn thành mỗi nhà hàng, đảm bảo không bị mất mát dữ liệu nếu xảy ra sự cố sập nguồn hoặc mất kết nối giữa chừng.