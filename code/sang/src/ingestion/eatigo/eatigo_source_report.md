# Source Report: Eatigo Data Ingestion

## 1. Overview & Metadata
* **Platform:** Eatigo (Trang đặt bàn và đánh giá quán ăn)
* **Target Endpoint:** `https://eatigo.com/v2/eatigo/product/{product_id}/comments`
* **Data Access Method:** Dùng code gọi trực tiếp vào hệ thống dữ liệu ngầm của trang web[cite: 1, 5]
* **Authentication / Login:** Không cần tài khoản đăng nhập
* **Anti-bot Protection:** Thấp / Chỉ cần cấu hình các thẻ thông tin cơ bản (`User-Agent`, `X-Requested-With`)

---

## 2. Source Discovery & Schema Mapping
Dữ liệu thô thu về đáp ứng đầy đủ các yêu cầu cần thiết theo kế hoạch mở rộng của nhóm:

| Feature Category | Mapped Field in JSON Output | Description |
|---|---|---|
| **Review Text** | `review_text` | Nội dung bình luận thực tế của khách hàng[cite: 2] |
| **Rating** | `rating_star` | Mức đánh giá số sao (từ 1 đến 5 sao)[cite: 2] |
| **Timestamp** | `timestamp` | Ngày và giờ gửi đánh giá[cite: 2] |
| **Reviewer Metadata** | `reviewer_metadata` | Tên hiển thị được ẩn bớt của người viết[cite: 2] |
| **Interactions** | `reaction_likes` | Số lượt tương tác, thích bài viết (`is_like`, `like_count`)[cite: 2] |
| **Tags & Media** | `tags`, `image_metadata` | Các nhãn đánh giá nhanh và hình ảnh khách đính kèm[cite: 2] |
| **Restaurant Info** | `restaurant_info` | Thông tin mã quán, điểm trung bình và tóm tắt thẻ đánh giá[cite: 2] |

---

## 3. Execution & Testing Results
* **Sample Target:** Chạy thử nghiệm trên một quán mẫu (`product_id: 3644620907182`)[cite: 5].
* **Yield:** Đã lấy thành công **240 dòng dữ liệu**, đúng bằng giới hạn số lượng bài viết thực tế của quán đó trên hệ thống[cite: 5].
* **Data Integrity:** Không bị mất mát dữ liệu; giữ lại trọn vẹn cả các trường đã chuẩn hóa và dữ liệu gốc ban đầu[cite: 2].

---

## 4. Limitations & Next Steps
* **Limitation:** Mỗi chi nhánh quán ăn trên Eatigo chỉ có sẵn một số lượng đánh giá có hạn (thường dưới 300 bài cho mỗi quán).
* **Scaling Strategy:** Viết thêm phần code chạy tự động quét qua danh sách nhiều mã quán khác nhau (`product_ids`) để gom chung lại và đạt được số lượng lớn dữ liệu theo đúng tiến độ[cite: 2].