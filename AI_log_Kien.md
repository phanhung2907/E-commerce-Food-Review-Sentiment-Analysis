NHẬT KÝ TƯƠNG TÁC TRỢ LÝ AI VÀ BÁO CÁO KỸ THUẬT (AI_LOG.MD)

Dự án: E-commerce & Food Review Sentiment Analysis

Thành viên thực hiện: Kiên

Mục đích: Ghi nhận minh bạch quá trình tương tác AI, đồng thời cung cấp phần giải thích chuyên sâu về mặt kỹ thuật (cơ chế chống bot, giải pháp cào 10.000+ records và phương pháp trích xuất dữ liệu gốc Schema.org) phục vụ bảo vệ đồ án.

PHẦN I: NHẬT KÝ TIẾN TRÌNH TƯƠNG TÁC VÀ PROMPT (CHRONOLOGICAL LOG)

1. Giai đoạn 1: Khởi tạo ý tưởng & Xây dựng Crawler thu thập dữ liệu

Nội dung Prompt/Yêu cầu của người dùng:

Xây dựng hệ thống cào dữ liệu tự động (mass-scale crawler) trên TripAdvisor nhắm tới mục tiêu tối thiểu 10.000 bản ghi phục vụ phân tích cảm xúc.

Tích hợp công nghệ chống chặn bot (undetected-chromedriver) và chuẩn Schema.org (JSON-LD) để trích xuất metadata và review.

Thiết lập cơ chế lưu cuốn chiếu (Incremental Saving) sau mỗi nhà hàng để tránh mất mát dữ liệu.

Đóng góp của AI: Cung cấp mã nguồn Python chuẩn, xây dựng hàm extract_json_ld_features để bóc tách metadata và vòng lặp phân trang cào review chi tiết.

2. Giai đoạn 2: Báo cáo kỹ thuật & Quản lý phiên bản GitHub

Nội dung Prompt/Yêu cầu của người dùng:

Yêu cầu viết file báo cáo report.md phân định rõ tính năng cấp nhà hàng và cấp review để nộp cho nhóm trưởng trước 20:00.

Hướng dẫn thực hiện các câu lệnh Git để tạo nhánh mới và mở Pull Request trên GitHub.

Đóng góp của AI: Biên soạn nội dung báo cáo chi tiết theo cấu trúc Markdown và cung cấp các câu lệnh Git chuẩn (git checkout -b, git add, git commit, git push) để hoàn tất Pull Request #24.

3. Giai đoạn 3: Khắc phục sự cố Anti-Bot & Tràn bộ nhớ RAM (OOM)

Nội dung Prompt/Yêu cầu của người dùng:

Gặp lỗi chặn IP "Access is temporarily restricted" do TripAdvisor phát hiện tần suất request.

Gặp lỗi sập cửa sổ VS Code do tràn bộ nhớ RAM (Lỗi OOM - Out of Memory với mã code: '-53687094') khi treo máy cào số lượng lớn.

Thắc mắc tại sao script dừng ở các mốc ~4.600, ~8.142, ~8.800 và làm sao để cào đạt mốc 10.000+ mà không mất dữ liệu cũ.

Đóng góp của AI:

Hướng dẫn học viên chuyển sang phát Wi-Fi 4G từ điện thoại để thay đổi địa chỉ IP ngay lập tức.

Khuyên chạy lệnh qua Terminal độc lập bên ngoài (CMD/PowerShell) thay vì bên trong VS Code để tiết kiệm RAM.

Nâng cấp code tích hợp Chế độ khôi phục (Resume Mode) giúp tự động đọc file JSON cũ, nạp sẵn hàng nghìn bản ghi đã cào trước đó và tiếp tục chạy nối tiếp.

Mở rộng danh sách các thành phố du lịch/ẩm thực trọng điểm (Hà Nội, TP.HCM, Đà Nẵng, Nha Trang, Đà Lạt, Vũng Tàu, Phú Quốc, Huế, Cần Thơ, Quy Nhơn,...) để đảm bảo nguồn dữ liệu đầu vào dồi dào.

4. Giai đoạn 4: Kiểm định dữ liệu & Hoàn thành mục tiêu 10.000 records

Nội dung Prompt/Yêu cầu của người dùng:

Xác thực ý nghĩa trường giá trị mặc định rating: 5.0 và kiểm tra cấu trúc file JSON khi đạt mốc chính xác 10.000 records.

Thắc mắc tại sao file JSON dung lượng lớn không hiển thị màu sắc rực rỡ như các file nhỏ.

Đóng góp của AI: Giải thích rõ bản chất giá trị mặc định placeholder và cách trích xuất song song giữa đánh giá chi tiết của người dùng (review_text) và điểm tổng quan chuẩn Schema (aggregateRating), đồng thời xác nhận file dữ liệu hoàn tất tại code/kien/data/raw/tripadvisor_mass_schema_features_2026-09-27.json.

PHẦN II: PHÂN TÍCH CHUYÊN SÂU KỸ THUẬT (DÙNG ĐỂ BÁO CÁO & PHẢN BIỆN)

1. Tại sao TripAdvisor lại có cơ chế chống bot nghiêm ngặt?

TripAdvisor là nền tảng đánh giá du lịch hàng đầu thế giới với tài sản dữ liệu khổng lồ về hành vi người dùng và metadata thương mại. Họ áp dụng các hệ thống phòng thủ đa lớp (như Cloudflare và WAF) vì các lý do cốt lõi:

Ngăn chặn cạnh tranh thương mại: Chặn các bên thứ ba quét dữ liệu giá cả, thông tin và insight kinh doanh hàng loạt.

Bảo vệ quyền riêng tư: Tránh việc bot khai thác thông tin cá nhân của người dùng đánh giá (reviewer).

Bảo vệ hạ tầng máy chủ (Anti-DDoS / Rate Limiting): Giới hạn tần suất request tự động để tránh làm quá tải hoặc sập hệ thống.

2. Tại sao các biện pháp cào dữ liệu truyền thống lại thất bại?

Khi cào bằng các phương pháp thông thường, hệ thống lập tức trả về lỗi "Access is temporarily restricted" do:

Lộ dấu vết tự động hóa (WebDriver Fingerprinting): Trình duyệt Selenium tiêu chuẩn bật sẵn cờ navigator.webdriver = true và thiếu các tham số phần cứng giả lập, giúp hệ thống bảo mật dễ dàng nhận diện bot.

Tần suất bất thường (Rate Limit & Rapid Taps): Bot gửi request liên tục không có độ trễ sinh học, không có thao tác cuộn trang hay di chuyển chuột tự nhiên, dẫn đến việc IP bị đưa vào danh sách đen (Blacklist).

3. Giải pháp kỹ thuật nào giúp cào thành công 10.000+ records?

Để đạt mục tiêu an toàn tuyệt đối mà không dùng dataset có sẵn, chúng ta đã kết hợp các giải pháp:

Sử dụng undetected-chromedriver: Vá các lỗ hổng định danh của Selenium, che giấu hoàn toàn cờ tự động hóa để đánh lừa hệ thống phát hiện bot.

Chiến lược phân tán diện rộng (Multi-City Scaling): Quét dàn trải qua hơn 10 thành phố lớn để chia nhỏ tải trọng request thay vì dồn dập vào một điểm.

Mô phỏng hành vi người dùng (Human-like Delays): Thêm thời gian chờ ngẫu nhiên (random.uniform) kết hợp cuộn trang (window.scrollBy) để kích hoạt nội dung tải bất đồng bộ (Lazy Loading) tự nhiên.

Cơ chế khôi phục thông minh (Resume Mode & Incremental Saving): Ghi cuốn chiếu dữ liệu liên tục xuống file JSON sau mỗi nhà hàng và tự động nạp lại tiến trình cũ khi khởi động lại, giải quyết triệt để vấn đề mất dữ liệu do sập mạng hoặc tràn RAM.

4. Phương pháp lấy các Features gốc của trang web (Schema.org / JSON-LD)

Thay vì bóc tách thủ công các thẻ HTML dễ bị lỗi khi giao diện thay đổi, chúng ta áp dụng chiến lược trích xuất cấu trúc kép:

Metadata chuẩn Schema.org (JSON-LD): Quét các thẻ ẩn <script type="application/ld+json"> để lấy chính xác định danh nhà hàng (@id), tọa độ (geo), khoảng giá (priceRange), ẩm thực (servesCuisine) và đánh giá tổng quan (aggregateRating).

Dữ liệu bình luận thô (review_text): Trích xuất trực tiếp nội dung đánh giá từ các vùng văn bản người dùng để phục vụ bài toán phân tích cảm xúc một cách chuẩn xác nhất.