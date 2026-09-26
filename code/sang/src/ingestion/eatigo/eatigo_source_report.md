# Source Report: Eatigo Data Ingestion & Schema Architecture

## 1. Overview & Metadata
* **Platform:** Eatigo.
* **Target Endpoint:** `https://eatigo.com/v2/eatigo/product/{product_id}/comments`[cite: 5]
* **Data Access Mechanism:** Sử dụng script Python gọi trực tiếp vào API ngầm của hệ thống để thu thập dữ liệu thô (Raw Data Ingestion)[cite: 1, 5].
* **Authentication / Login:** Không yêu cầu tài khoản đăng nhập (truy cập qua endpoint công khai).
* **Anti-bot Protection:** Tối thiểu; cấu hình các HTTP Headers tiêu chuẩn để giả lập trình duyệt và kết nối ổn định.

---

## 2. Source Discovery & Schema Mapping
Dữ liệu được thu thập và lưu trữ dưới dạng **Python Dictionary Object nguyên bản (Raw Objects)** từ API của Eatigo mà không qua các bước bóc tách làm biến dạng cấu trúc gốc. Dưới đây là kiến trúc các khối object và danh sách các trường (features) chi tiết:

| Khối dữ liệu chính (Raw Object Keys) | Tên trường cụ thể (Nested Fields) | Ý nghĩa và Mô tả chi tiết |
| :--- | :--- | :--- |
| **`product_id`** | `product_id` | Mã định danh duy nhất của nhà hàng trên hệ thống Eatigo[cite: 6]. |
| **`restaurant_tags_raw`** | `tags` (Array of objects) | Khối object chứa toàn bộ dữ liệu thống kê số lượng các thẻ đánh giá chung của nhà hàng (ví dụ: *Great food, Good service, Reasonable price*,...)[cite: 3, 6]. |
| **`comment_container_raw`** | `location`, `cuisine`, `avg_rating`, `total_count`, `comments` | Khối object chứa toàn bộ cấu trúc phản hồi gốc của trang bình luận, bao gồm thông tin khu vực, loại ẩm thực, điểm trung bình và tổng số lượng review[cite: 6]. |
| **`review_item_raw`** | `id` | Mã định danh duy nhất (ID) của từng bài đánh giá/bình luận. |
| | `description` | Nội dung văn bản review thực tế của khách hàng (Feature cốt lõi phục vụ bài toán *NLP / Sentiment Analysis*). |
| | `rating` | Điểm số đánh giá sao của khách hàng (thang điểm từ 1 đến 5 sao). |
| | `comment_time` | Mốc thời gian chính xác khi khách hàng gửi bài đánh giá. |
| | `rated_by` | Thông tin metadata về người viết review (đã được che bớt ký tự tên để bảo mật). |
| | `is_like`, `like_count` | Trạng thái tương tác và tổng số lượt thích (likes) của bình luận. |
| | `tags`, `images` | Các nhãn đánh giá nhanh và danh sách đường dẫn hình ảnh thực tế do khách hàng đính kèm. |

---

## 3. Execution & Methodology Results
* **Methodology:** Sử dụng phương pháp **Seed List / Pre-collected Target IDs** kết hợp với kiến trúc phân tầng Ingestion. Do API danh sách tổng quát của Eatigo áp dụng cơ chế phân quyền và ẩn dữ liệu động (on-the-fly) trả về mảng rỗng (`[]`), việc sử dụng tập hợp mã `product_id` mục tiêu đã được xác thực giúp hệ thống gom về dữ liệu thực tế thành công 100% mà không bị gián đoạn[cite: 5].
* **Execution Results:** 
  * Chạy thực nghiệm thu thập thành công trên các mã nhà hàng mẫu, tích lũy hàng trăm dòng dữ liệu thô thực tế vào file JSON chuẩn cấu trúc (`eatigo_raw_objects_final.json`).
  * Script tích hợp cơ chế checkpoint lưu dữ liệu tự động sau mỗi nhà hàng, đảm bảo an toàn tuyệt đối khi treo máy xuyên đêm thu thập số lượng lớn.

---

## 4. Limitations & Next Steps
* **Limitations:** Mỗi nhà hàng trên Eatigo có giới hạn số lượng bài đánh giá hiển thị công khai cố định (thường dưới 300 reviews cho mỗi quán).
* **Next Steps:** Mở rộng danh sách các `product_id` hoạt động tích cực (active reviews) trên diện rộng để tự động hóa hoàn toàn quy trình thu thập dữ liệu quy mô lớn (Scale-up) phục vụ các giai đoạn xử lý và mô hình hóa.