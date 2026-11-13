Vấn đề Cốt lõi 1 cần giải quyết được phát biểu như sau:

"Xu hướng: 'Chất lượng dịch vụ (qua rating) có xu hướng đi xuống khi quán trở nên quá đông khách (nhiều review) không?'"

Biến đầu vào (X): Quy mô lượt đánh giá của quán (review_count - đại diện cho mức độ đông khách).

Biến đầu ra (y): Điểm đánh giá trung bình (avg_rating hoặc rating_level_5 - đại diện cho chất lượng dịch vụ).

2. Ý TƯỞNG & TRỰC GIÁC:
Bài toán về "sự quá tải" của một quán ăn mang bản chất của sự phân chia khoảng (ngưỡng giới hạn) thay vì một xu hướng tăng/giảm đều đặn. Do đó, thuật toán Decision Tree (Cây quyết định) được đề xuất dựa trên trực giác ban đầu.
Mục tiêu kỳ vọng: Cần một mô hình có khả năng tự động dò tìm ra "Điểm gãy quá tải" (Break-even / Threshold Point) — ví dụ: khi quán vượt mốc N lượt reviews thì điểm đánh giá bắt đầu giảm rõ rệt.

3. PHÂN TÍCH SO SÁNH GIỮA LINEAR REGRESSION VÀ DECISION TREE

a: LINEAR REGRESSION
lỗ hổng khi áp dụng vào bài toán:

- Thực tế trải nghiệm khách hàng không biến thiên theo đường thẳng tắp. Quán mới mở có thể điểm bấp bênh, quán đông vừa phải có quy trình chuẩn nên điểm rất cao, nhưng khi vượt ngưỡng chịu đựng (quá tải) thì điểm mới sụt giảm. Linear Regression bắt ép toàn bộ dữ liệu phải nằm trên một đường thẳng, dẫn đến việc bị "mù" trước các biến động dạng uốn cong (Non-linear).

- Vì bị ép phải vẽ một đường thẳng, Linear Regression sẽ tính trung bình bù trừ cho tất cả các khúc trên. Kết quả là nó sẽ cho ra một hệ số góc gần bằng 0 (như bạn thấy ở lần chạy trước là -0.0062), và kết luận ngô nghê rằng: "Độ đông khách không ảnh hưởng gì đến điểm số". Nó hoàn toàn bỏ lỡ cái "điểm gãy" khi quán bắt đầu quá tải.

b: Decision Tree:
- Khả năng tự động phát hiện Ngưỡng quá tải (Threshold Detection):
Decision Tree tự động chia dữ liệu thành các câu hỏi If/Else (ví dụ: If review_count <= T). Giá trị T chính là ngưỡng giới hạn sức chứa của nhà hàng.

- Không bắt ép dữ liệu đi theo đường thẳng, chấp nhận sự tăng giảm theo dạng bậc thang (Step-function) phản ánh đúng thực tế kinh doanh.

4: Chốt lại mô hình:
 - Chọn thuật toán Decision Tree phân tich cho vấn đề 1:

 - Lí do chọn: Decision Tree phản ánh chính xác trực giác ban đầu của người dùng, loại bỏ các lỗ hổng của Linear Regression, đồng thời mang lại câu trả lời định lượng trực tiếp về "ngưỡng quá tải" cho bài toán phân tích chất lượng dịch vụ nhà hàng.