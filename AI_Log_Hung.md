# AI Usage Log

Nhật ký này ghi lại mọi lần sử dụng AI có ảnh hưởng đến câu hỏi nghiên cứu, giả thuyết, mã nguồn, xử lý dữ liệu, mô hình, diễn giải kết quả hoặc báo cáo của dự án **Phân tích cảm xúc review ẩm thực**.

| Ngày | Thành viên | Công cụ/model | Mục tiêu | Prompt hoặc tóm tắt prompt | Kết quả được sử dụng | Cách kiểm chứng |
|---|---|---|---|---|---|---|
| 2026-09-07 | Nhóm | OpenAI Codex | Khởi tạo và điều chỉnh kế hoạch dự án theo Chủ đề 2 | Đối chiếu đề bài và cập nhật các file Markdown cho bài toán sentiment analysis từ ShopeeFood/Foody | Cấu trúc README, câu hỏi nghiên cứu, giả thuyết, pipeline và kế hoạch đánh giá | Đối chiếu mục Chủ đề 2, yêu cầu 5 reports và cấu trúc repository trong đề bài |
| 2026-09-08 | Nhóm | OpenAI Codex | Biên soạn tutorial cho Report 1 | Chuyển nội dung tư vấn trước đó thành hướng dẫn Report 1, đồng thời điều chỉnh ví dụ và kiến trúc theo đề tài sentiment analysis | `tutorial_report1.md`: giả thuyết cụ thể, sơ đồ Docker, Compose skeleton, kế hoạch tuần 1–2 và checklist | Đối chiếu yêu cầu Report 1, workflow Crawl -> MinIO -> PostgreSQL và cấu trúc repository của đề bài |

## Cách ghi log

- Thêm một dòng ngay sau mỗi lần dùng AI tạo ra nội dung được giữ lại trong dự án.
- Tóm tắt prompt đủ cụ thể để người đọc hiểu mục tiêu; liên kết tới file, notebook, commit hoặc report liên quan nếu có.
- Ghi rõ cách nhóm kiểm chứng: test, SQL query, tài liệu chính thức, code review, kiểm tra thủ công hoặc kết quả thực nghiệm.
- Nếu đề xuất của AI bị sửa hoặc loại bỏ, ghi lại quyết định đó trong cột kết quả.

## Nguyên tắc

- Không đưa mật khẩu, access key, dữ liệu cá nhân, nội dung review chưa ẩn danh hoặc dữ liệu nhạy cảm vào prompt.
- AI chỉ hỗ trợ; thành viên chịu trách nhiệm đọc, chạy thử và kiểm chứng mọi nội dung trước khi sử dụng.
- Không dùng nội dung AI tạo ra để thay thế dữ liệu thực nghiệm hoặc để tuyên bố quan hệ nhân quả khi bằng chứng chỉ thể hiện tương quan.
- Trích dẫn nguồn và tuân thủ quy định liêm chính học thuật trong tất cả báo cáo.
