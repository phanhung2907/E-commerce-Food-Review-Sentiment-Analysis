# Report 4 · Đề xuất tìm từ khóa đặc trưng theo mức đánh giá

**ADY201m · Chủ đề 2 · Phân tích cảm xúc Food Review · Tuần 7–8**

## 1. Câu hỏi và giả thuyết

Lộ trình ADY201m yêu cầu Report 4 xây dựng hai mô hình ML khác nhau, đánh giá, so sánh và biện luận giả thuyết. RQ2 trong kế hoạch tuần 2 hỏi cụm từ nào liên hệ mạnh với đánh giá 1 sao. Kế hoạch tuần 5–6 đã định hướng đếm theo review, đọc ngữ cảnh và tách tập kiểm tra theo quán. Đề xuất này nối các bước đó với thiết kế xác nhận trên dữ liệu độc lập.

- **Câu hỏi chính.** Trong review tiếng Việt có điểm sao gốc, cụm từ nào xuất hiện đặc trưng ở 1 sao, và cụm nào vẫn phân biệt được 1 sao với 2 sao?
- **Mở rộng.** Ở từng mức 0, 1, 2, 3, 4 và 5 trên thang phân tích, cụm nào xuất hiện nhiều hơn tương đối so với phần còn lại, và cụm nào phân biệt được mức điểm với các mức liền kề?
- **Giả thuyết từ khóa.** Với một cụm và một đối chiếu đã chốt, H₀ là hệ số của biến có mặt cụm bằng 0 trong mô hình liên hệ. H₁ là hệ số dương. Báo cáo kiểm định hai phía và chỉ giữ phát hiện có chiều dương.
- **Giả thuyết dự báo.** Cụm từ cung cấp tín hiệu cho bài toán 1 sao trên quán chưa thấy. Đo phần cải thiện Average Precision (AP) của mô hình dùng văn bản so với baseline chỉ dùng độ dài, với ngưỡng cải thiện thực tiễn đề xuất là 0,02 AP tuyệt đối.

“Fatal keyword” chỉ từ hoặc cụm từ gắn với mức 1 sao trong dữ liệu quan sát. Với các mức khác, dùng “từ khóa đặc trưng”. Khách có thể vừa chấm sao vừa mô tả cùng một trải nghiệm. Vì vậy, dữ liệu đo mối liên hệ giữa lời mô tả và điểm, còn tác động của việc thay đổi trải nghiệm cần một thiết kế nhân quả riêng. [Hernán & Robins](https://miguelhernan.org/whatifbook)

## 2. Kiểm tra dữ liệu hiện có

Kiểm tra trực tiếp hai CSV trong `code/hung/data/database-merge-data` bằng trình đọc CSV có xử lý trường nhiều dòng. Snapshot có **400.067 review**, không có khóa `(source_code, source_review_id)` lặp, không có rating thiếu hoặc nằm ngoài khoảng từ 0 tới max cấu hình. Độ phủ ngôn ngữ và tính hợp lệ về nghiệp vụ cần audit riêng. Các số dưới đây là số record quan sát được trong bản xuất, trước khi lọc ngôn ngữ, kiểm tra nội dung và nguồn gốc nhãn.

| Nguồn | Tổng review | Khoảng gốc quan sát | Có nội dung | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Foody | 262.874 | 0–10 | 262.854 | 119 | 11.856 | 12.827 | 53.580 | 129.250 | 55.222 |
| Eatigo | 28.955 | 0–5 | 12.967 | 17 | 628 | 606 | 1.499 | 2.741 | 7.476 |
| Capichi | 38.706 | 1–5 | 38.706 | 0 | 979 | 848 | 1.957 | 3.060 | 31.862 |
| BeFood | 18.061 | 1–5 | 18.061 | 0 | 5.222 | 1.937 | 2.746 | 2.464 | 5.692 |
| Tripadvisor | 51.471 | 1–5 | 51.471 | 0 | 5.731 | 2.561 | 1.292 | 829 | 41.058 |

Các cột 0–5 tính trên review có `review_text` khác rỗng, với quy tắc quy đổi tại mục 3. Cột 0 thể hiện số ứng viên theo giá trị CSV trước bước xác minh nhãn. Khoảng quan sát trong CSV và `rating_scale_max` phản ánh dữ liệu dự án, còn thang điểm công khai và ý nghĩa trường phải đối chiếu với dữ liệu thô.

**BeFood phù hợp để bắt đầu câu hỏi 1 sao.** Có 17.959 review mang nhãn ngôn ngữ `vi`, gồm 5.187 review 1 sao từ 1.140 ID quán, trước khi kiểm tra chất lượng text. Mã crawler hiện có trích `rating` cùng `feedback` và khử trùng theo cặp giá trị trong từng trang đã tải. Khi chốt dữ liệu, đối chiếu mẫu JSON/HTML hoặc trang với bản ghi nhập DB, kiểm tra chuỗi tiếng Việt lỗi mã hóa và kiểm tra các mẫu feedback lặp giữa các quán. Phân bố thu được mô tả review mà quy trình crawl giữ lại.

**Hai điểm cần xác minh trước khi chốt nhãn.** Foody có 127 điểm 0 gốc, 119 có nội dung và 99 trong số đó thuộc 2017. Eatigo có 81 điểm 0 gốc, 17 có nội dung từ 6 ID quán. Kiểm tra cách API trả điểm 0, trường vắng mặt, các giá trị mặc định trong ETL và mẫu hiển thị. Tại Foody, trong review có nội dung, tỷ lệ điểm 10/10 là 794/986 (80,5%) năm 2025 và 393/486 (80,9%) năm 2026. Đối chiếu raw với trường điểm gốc và các thành phần điểm nếu có, kiểm tra cả các năm trước và audit riêng trước khi kết luận nhãn bị lỗi. Cột `language` hiện trống cho toàn bộ review có nội dung của Foody, Eatigo và Tripadvisor, nên cần bộ nhận diện ngôn ngữ và đọc tay mẫu văn bản ngắn.

## 3. Định nghĩa các mức rating

| Câu hỏi | Dữ liệu và nhãn | Cách trình bày |
|---|---|---|
| Đúng 1 sao | BeFood sau audit, `rating = 1`, so với 2–5 sao. Đối chiếu sát 1 với 2 sao. Kiểm tra lặp trên nguồn sao gốc khác nếu có đủ review tiếng Việt. | “Từ khóa gắn với đánh giá 1 sao trên BeFood”. |
| Sáu mức 0–5 | Phân tích trong từng nguồn trước. Nguồn sao gốc giữ số sao. Foody dùng mức quy đổi để lập hồ sơ điểm. | Ghi nguồn, thang gốc và khoảng của từng nhóm. |
| Đúng 0 điểm | Mỗi nguồn chỉ đưa các giá trị 0 gốc đã xác minh vào phân tích. | Nếu nhãn chưa rõ hoặc hỗ trợ thấp, ghi “chưa đủ bằng chứng” và trình bày số lượng. |

Với Foody, đặt `r5 = rating * 5 / rating_scale_max` và `bucket = floor(r5 + 0.5)` trong miền hợp lệ. Trên thang 0–5, sáu khoảng lần lượt là **[0, 0,5), [0,5, 1,5), [1,5, 2,5), [2,5, 3,5), [3,5, 4,5), [4,5, 5]**. Chẳng hạn Foody từ 1 đến dưới 3 trên thang 10 thuộc mức quy đổi 1. Mức này giữ tên “Foody mức 1/5 quy đổi”. Phân tích độ nhạy dùng rating Foody gốc qua các khoảng điểm hoặc đối chiếu điểm nguyên khi đủ mẫu. So sánh các danh sách theo nguồn bằng chiều liên hệ và độ lớn. Nếu cần một kết quả chung, chỉ tổng hợp những nguồn có lớp và nhóm đối chứng tương ứng, đồng thời công bố bất đồng giữa các nguồn. Thứ tự lớp và khoảng cách giữa mức kề nhau là thông tin quan trọng trong bài toán suy rating từ văn bản. [Pang & Lee, 2005](https://aclanthology.org/P05-1015/)

## 4. Quy trình tìm và xác nhận từ khóa

### 4.1. Chuẩn bị từ PostgreSQL

Kết nối PostgreSQL gộp, xác minh schema thực tế và số dòng theo nguồn trước khi chạy. Dùng bảng `reviews` nối `sources` qua `source_code`, nối `restaurants` qua `(source_code, source_restaurant_id)` khi cần metadata đã kiểm tra. DDL gốc trong `schema_3nf.sql` liệt kê bốn nguồn trong CHECK, còn CSV gộp có thêm BeFood. Kiểm tra constraint và sự hiện diện của BeFood trên DB đích trước khi dùng nguồn này. Xuất snapshot có rating gốc, source, review ID, restaurant ID, review date, language và review text. Dùng ngày đăng có nguồn gốc xác minh được để phân tầng thời gian. Nếu chỉ có thời điểm crawl, báo cáo độ phủ thời gian và bỏ biến ngày đăng khỏi mô hình điều chỉnh của nguồn đó.

Chuẩn hóa Unicode NFC, HTML, khoảng trắng, chữ thường và các biến thể viết tắt đã kiểm tra. Giữ dấu tiếng Việt, từ phủ định như “không”, “chưa”, “chẳng” và ranh giới câu. Lấy cụm 1–3 đơn vị từ, thử tách từ tiếng Việt hoặc n-gram theo âm tiết trên development. Chuẩn hóa đường dẫn, thông tin cá nhân, tên quán nhận diện được và câu tiết lộ nhãn như “cho 1 sao”, “2/10”. Dùng thân bài cho kết quả chính và kiểm tra riêng ảnh hưởng của tiêu đề. Loại boilerplate hoặc nhóm văn bản trùng/gần trùng trước khi chia dữ liệu. Kiểm tra riêng lời ngắn có thể là review thật, vì văn bản giống nhau như “ngon” chưa đủ để kết luận là bản sao của cùng một quan sát. [Vu et al., 2018](https://aclanthology.org/N18-5012/)

### 4.2. Chia tập trước khi xem từ khóa

Tái sử dụng manifest khóa từ Report 3 nếu có thể đối chiếu đúng snapshot và phạm vi. Nếu chưa có, đề xuất khoảng 80% development và 20% test theo nhóm quán, giữ nhóm trùng văn bản dài trong cùng split. Với phân tích liên nguồn, nối ID những quán đã xác minh trùng trước khi chia nhóm. Bên trong development dùng 5 fold theo nhóm và cố gắng giữ phân bố lớp. Kiểm tra số quán có lớp đích ở từng fold, giao nhau giữa các tập và số lượng mẫu bị loại. Với lớp hiếm, giảm số fold khi có căn cứ hoặc báo cáo mô tả nếu thiếu nhóm độc lập. Mọi lựa chọn từ vựng, IDF, siêu tham số và danh sách cụm cần hoàn tất trên development. [StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html) · [Scikit-learn, Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)

### 4.3. Sàng lọc bằng tỷ lệ review có chứa cụm

Đếm một cụm tối đa một lần trong mỗi review. Với lớp đích, gọi `a` và `b` lần lượt là số review có và không có cụm. Với nhóm so sánh, dùng `c` và `d`. Tính tỷ lệ `p1 = a/(a+b)`, `p0 = c/(c+d)`, chênh lệch `p1 - p0` và OR làm trơn `[(a+0,5)(d+0,5)]/[(b+0,5)(c+0,5)]`. Có thể xếp hạng theo log-OR chia cho sai số chuẩn xấp xỉ tính từ bốn ô đã làm trơn. Đây là điểm sàng lọc nhị phân theo review, phát triển từ ý tưởng so sánh từ vựng bằng log-odds có làm trơn. Phương pháp gốc của Monroe et al. dùng tần suất token và prior Dirichlet. Hai cách dùng đơn vị đếm khác nhau. [Monroe et al., 2008](https://doi.org/10.1093/PAN/MPN018)

Chạy với `k` so với các mức còn lại để tìm tín hiệu nhận diện lớp. Chạy thêm `k` so với từng mức kề có đủ hỗ trợ. Cụm mạnh khi so với toàn bộ nhưng yếu ở cặp 1–2 có thể đại diện cho điểm thấp nói chung. Với mức giữa, so riêng hai phía để tránh hiệu ứng trung bình che khuất sự khác biệt. Ví dụ giả định, nếu một cụm có mặt trong 40/1.000 review 1 sao, 20/5.000 review còn lại và 35/1.000 review 2 sao, tỷ lệ lần lượt là 4%, 0,4% và 3,5%. Cụm có chênh lệch lớn khi so với toàn bộ, nhưng chênh lệch với 2 sao chỉ là 0,5 điểm phần trăm.

### 4.4. Chốt danh sách rồi xác nhận trên test

1. Trên development, giữ ứng viên có ít nhất 20 review lớp đích từ ít nhất 5 quán. Ưu tiên cụm có chiều dương ổn định qua tối thiểu 4/5 fold khi đủ fold, đồng thời ghi hệ số Logistic Regression, số fold cụm có mặt và số quán hỗ trợ. Chốt tối đa 20 cụm mỗi mức, cùng nhóm đối chiếu và các cụm đồng nghĩa đã rà soát. Các ngưỡng là đề xuất phải khóa trước khi mở test.
2. Trên test, ghi lại tỷ lệ hai nhóm, hỗ trợ theo review/quán và khoảng tin cậy. Với từng cụm đã chốt, ước lượng Logistic Regression nhị phân dùng biến có/không có cụm và log độ dài review, cùng năm/vùng nếu metadata đủ tin cậy và nhóm có hỗ trợ. Chạy riêng theo nguồn. Dùng sai số chuẩn theo cụm quán khi đủ cụm độc lập, đồng thời kiểm tra độ nhạy với reviewer lặp nếu có định danh. Trường hợp phân tách hoàn toàn, ít cụm hoặc độ phủ quá thấp thì trình bày mô tả và ghi chưa đủ bằng chứng xác nhận. Hệ số sau điều chỉnh và OR thô trả lời hai câu hỏi khác nhau, nên hiển thị cả hai.
3. Dùng Holm ở mức 5% cho toàn bộ kiểm định xác nhận đã đăng ký, gồm các cặp mức kề cần công bố. Giữ kiểm định không ước lượng được trong mẫu số hiệu chỉnh, tương đương gán p = 1 cho mục đích Holm. Công bố OR, CI 95% theo cụm và p đã điều chỉnh. Ngưỡng công bố đề xuất gồm OR điều chỉnh ≥ 1,5, CI dưới > 1, p đã điều chỉnh < 0,05 và tối thiểu 10 review chứa cụm thuộc ít nhất 5 quán ở lớp đích trên test. Ghi rõ số kết quả đủ điều kiện, kể cả khi bằng 0. Gắn nhãn “đặc trưng riêng cho mức k” khi các đối chiếu kề đã đăng ký cùng hỗ trợ kết luận.
4. Kiểm tra độ nhạy với Foody trước 2025, toàn kỳ và tập chỉ gồm nhãn đã xác minh nếu phát hiện bất thường. Kiểm tra quán có ảnh hưởng lớn, mẫu ngôn ngữ không chắc chắn và cách gom điểm. Một cụm xác nhận ở một nguồn giữ phạm vi nguồn đó. Chỉ ghi “lặp lại liên nguồn” khi nguồn độc lập đủ mẫu và cho cùng chiều ở đối chiếu tương ứng.
5. Đọc ngữ cảnh mẫu từ nhiều quán trong lớp đích và lớp đối chứng, ẩn sao ở lượt mã hóa đầu. Gắn khía cạnh như món ăn, vệ sinh, phục vụ, giao hàng, đóng gói hoặc giá. Ghi phủ định, mỉa mai và câu vừa khen vừa chê. Hai người có thể mã hóa độc lập 20–30 ngữ cảnh cho nhóm cụm ưu tiên rồi đối chiếu bất đồng. Trích dẫn ngắn đã ẩn danh trong báo cáo. VLSP 2018 có khung phân tích cảm xúc theo khía cạnh cho nhà hàng để tham khảo cách xây nhãn. Dữ liệu thực nghiệm của môn dùng review nhóm tự crawl. [VLSP 2018](https://vlsp.org.vn/index.php/vlsp2018/eval) · [Holm, 1979](https://www.jstor.org/stable/4615733)

## 5. Hai mô hình và cách kiểm tra giá trị dự báo

| Thành phần | Cấu hình đề xuất | Câu hỏi trả lời |
|---|---|---|
| Baseline | Dummy theo tỷ lệ lớp và Logistic Regression chỉ có độ dài review | Mô hình văn bản thêm bao nhiêu tín hiệu so với phân bố lớp và độ dài? |
| Mô hình 1 | TF-IDF cụm từ 1–3 + Logistic Regression L2 | Những cụm nào có hệ số dương ổn định khi xét đồng thời các cụm khác? |
| Mô hình 2 | Cùng đặc trưng TF-IDF không âm + Complement Naive Bayes | Tín hiệu có tái hiện với một thuật toán ước lượng khác? |
| Ablation | Huấn luyện lại sau khi bỏ các cột đặc trưng thuộc danh sách cụm đã chốt, cùng split và quy tắc tuning | Cả nhóm cụm đóng góp bao nhiêu vào khả năng dự báo của mô hình? |

Huấn luyện bài toán nhị phân 1 sao trước, rồi phân loại đa lớp cho từng nguồn có đủ support. Dùng cùng split, quy trình làm sạch và ngân sách tuning tương đương. Trong Logistic Regression đa lớp, kiểm tra trọng số lớp đích so với từng lớp kề vì điểm dự báo phụ thuộc cả hai lớp. Với ablation, giữ các n-gram đồng nghĩa có chủ đích hoặc loại cùng nhóm theo quy tắc đã chốt và ghi rõ lựa chọn. Mức giảm dự báo đo thông tin mất đi khi bỏ nhóm đặc trưng trong pipeline. Cụm tương quan có thể thay thế cho nhau. [Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) · [ComplementNB](https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.ComplementNB.html)

- **1 sao.** Dùng AP và đường precision–recall, kèm tỷ lệ lớp 1 sao trên test, F1, precision, recall và ngưỡng đã chọn trên development. Ước lượng CI 95% của chênh lệch AP bằng bootstrap theo quán, ghép cặp cùng mẫu bootstrap giữa các mô hình. Nếu CI dưới > 0, có bằng chứng về cải thiện dự báo. Nếu mức tăng quan sát ≥ 0,02, đạt ngưỡng thực tiễn đề xuất. [Saito & Rehmsmeier, 2015](https://pubmed.ncbi.nlm.nih.gov/25738806/)
- **0–5.** Dùng Macro-F1, AP/F1 và số mẫu từng mức, ma trận nhầm lẫn, MAE trên nhãn thứ bậc. Ghi rõ lớp nào được đánh giá và báo riêng trường hợp mức 0 chưa đủ support. Bản đồ nhiệt theo mức cho các cụm đã xác nhận có thể hiển thị tỷ lệ review chứa cụm, kèm số mẫu từng cột.
- **Diễn giải.** Kết quả mô hình đánh giá sức dự báo của văn bản. Kiểm định theo cụm mới là cơ sở công bố danh sách từ khóa. Nếu hai mô hình dự báo tốt nhưng cụm riêng lẻ chưa qua xác nhận, kết luận ở cấp độ văn bản và báo số cụm được xác nhận.

## 6. Đầu ra đề xuất

| Bảng | Cột cần có |
|---|---|
| Chất lượng dữ liệu và phân bố nhãn | nguồn, rating gốc, mức quy đổi, số review, số quán, thiếu text, ngôn ngữ, trạng thái xác minh |
| Từ khóa theo mức | nguồn, mức, đối chiếu, cụm, tỷ lệ hai nhóm, số review/quán hỗ trợ, OR điều chỉnh, CI, p đã điều chỉnh, số fold cùng chiều, khía cạnh, trạng thái |
| So sánh mô hình | split, nguồn, bài toán, mô hình, AP, Macro-F1, MAE khi phù hợp, hỗ trợ theo lớp, CI của chênh lệch AP |
| Phân tích sai lệch | quán hoặc giai đoạn có ảnh hưởng, ngữ cảnh phủ định/mỉa mai, kết quả đổi ngưỡng rating, khả năng lặp lại theo nguồn |

**Tuần 7** hoàn thành audit nhãn, manifest, tiền xử lý, danh sách ứng viên và chọn cấu hình hai mô hình. **Tuần 8** mở test, xác nhận cụm, so sánh mô hình, đọc ngữ cảnh và viết kết luận. Lưu seed, truy vấn SQL, ID hoặc hash snapshot, cấu hình mô hình và bảng kết quả để tái lập. Lộ trình môn yêu cầu nộp nhật ký sử dụng AI cùng sản phẩm dự án.

**Trạng thái hiện tại.** Số liệu ở mục 2 đã kiểm tra trên CSV. Quy tắc ngưỡng, nguồn ưu tiên và thiết kế phân tích là đề xuất. Danh sách từ khóa thực tế và điểm số mô hình được xác định sau khi chạy quy trình trên tập đã khóa.

### Tài liệu nội bộ đã đối chiếu

- `plans/260109-ADY201m_ AI, DATA SCIENCE WITH PYTHON & SQL.md` và bản hướng dẫn môn đã cập nhật.
- `plans/WEEK_2_PLAN_Food_Review_Sentiment_Analysis.md` và `plans/WEEK_5-6_PLAN_EDA_CHI_TIET.md`.
- `code/hung/src/storage/schema_3nf.sql`, `code/hung/src/processing/foody_transform.py`, `code/tuan/src/ingestion/befood/befood_crawler.py` và hai CSV đã nêu tại mục 2.
