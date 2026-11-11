# KẾ HOẠCH EDA CHI TIẾT TUẦN 5–6 — FOOD REVIEW SENTIMENT ANALYSIS

**Ngày lập:** 19/10/2026. **Workspace:** `E:\Real-estate-tourism\hung`.

**Đầu ra môn học:** Report 3 (10%) gồm notebook cleaning, EDA thực hiện bằng RStudio và Data Dictionary. Kế hoạch này coi phần cleaning hiện có là đầu vào đã được nhóm thực hiện; không phân bổ lại hai tuần để viết lại cleaner. Phần đầu chỉ nghiệm thu dữ liệu, bổ sung versioning và chốt tập phân tích. Những lỗi còn lại được ghi nhận theo bằng chứng, không ngầm coi tất cả giá trị đã đúng.

**Trạng thái:** đây là kế hoạch thực hiện, chưa phải báo cáo kết quả EDA. Số liệu kiểm kê local và phạm vi kiểm chứng xem `BAO_CAO_CLEANING_VA_DATA_VERSIONING.md` và `CLEANING_LOCAL_AUDIT_METRICS.json`. MinIO/PostgreSQL chưa kết nối được trong phiên kiểm tra; chưa xác nhận số dòng hay chất lượng DB thật. Không đưa trước “insight”, p-value hoặc kết quả mô hình.

**Căn cứ cập nhật sau audit toàn bộ raw local:** 34.492 file với 34.492 restaurant ID và 265.804 review ID duy nhất; không có ID lặp trong cây dữ liệu được quét. Có 20 review thiếu text, 128 rating bằng 0; 6.050 text chưa NFC và 231 text có mẫu HTML/entity cần đọc kiểm tra. Có 2.323 nhóm text dài ít nhất 20 ký tự giống nhau sau NFC/chuẩn hóa whitespace, trong đó 882 nhóm trải qua nhiều quán; đây là ứng viên kiểm tra trùng, chưa phải danh sách spam. Cả `avg_rating`, `total_reviews`, `category`, `price_range`, latitude và longitude đều thiếu trong 34.492/34.492 object sau transform. Vì vậy, nhánh mặc định của kế hoạch là ưu tiên EDA review/text; chưa thực hiện RQ1 platform và chưa dùng category/price làm baseline. Những số liệu này là kiểm tra kỹ thuật toàn cây raw, không phải EDA nội dung trên tập test.

## 1. Kết quả cần đạt cuối tuần 6

1. Có một dataset cố định, có `dataset_id`, danh sách snapshot raw, hash, phiên bản transform và bảng chia tập; mọi biểu đồ đều truy về dataset này.
2. Có hai bảng đúng grain: một dòng/review và một dòng/quán/nguồn. Không nhân dòng khi nối cuisines/tags.
3. Có Data Dictionary cho toàn bộ biến dùng trong phân tích, kèm quy tắc NULL, miền hợp lệ và vai trò của biến.
4. Có khoảng 10–12 biểu đồ chính trong báo cáo, biểu đồ chẩn đoán bổ sung ở phụ lục, tất cả tạo bằng R trong RStudio.
5. Có 3–5 phát hiện thực tế, mỗi phát hiện có số liệu, mẫu số, mức hỗ trợ theo quán và giới hạn diễn giải.
6. Có quyết định rõ về phạm vi dữ liệu, nhãn mục tiêu và thiết kế đánh giá để bàn giao sang tuần 7–8. Chưa huấn luyện hay chọn mô hình trong kế hoạch này.

**Phân biệt yêu cầu và đề xuất:** RStudio, notebook cleaning, Data Dictionary, Report 3 và nhịp commit là yêu cầu từ tài liệu môn học. Số biểu đồ, thời lượng, cỡ mẫu đọc tay, bootstrap và các ngưỡng cảnh báo dưới đây là đề xuất chuyên môn; có thể điều chỉnh có ghi lý do.

## 2. Chốt câu hỏi nghiên cứu và điều kiện khả thi

### 2.1. RQ chính — ngôn ngữ trong các đánh giá điểm thấp

**Câu hỏi EDA:** review điểm thấp khác các review còn lại về độ dài, từ/cụm từ và chủ đề phàn nàn như thế nào? Dữ liệu có đủ để sang tuần 7 kiểm tra giá trị bổ sung của nội dung văn bản không?

Đơn vị quan sát là một review, định danh bằng `(source_code, source_review_id)`. Thang điểm được lấy từ `sources.rating_scale_max` rồi kiểm chứng bằng phân bố và đối chiếu mẫu raw/giao diện nguồn.

| Trường hợp xác minh | Quyết định nhãn | Điều phải ghi trong báo cáo |
|---|---|---|
| Nguồn có sao 1–5 đúng nghĩa | Có thể dùng `is_one_star = rating == 1` | Chỉ dùng rating hợp lệ, không điền rating thiếu thành 0 |
| Foody có điểm tổng hợp 0–10/1–10 | Dùng tên `is_low_rating`, ngưỡng cần chốt trước phân tích từ khóa | Không gọi điểm Foody là “1 sao”; không chia 2 rồi coi hai khái niệm tương đương |
| Có giá trị 0 | Xác minh đó là điểm hợp lệ hay chưa đánh giá | Giữ cờ riêng; chưa đưa vào lớp bình thường hoặc lớp thấp khi chưa rõ ý nghĩa |
| Trộn nguồn/thang khác nhau | Phân tích riêng theo nguồn trước | Không gộp bằng một ngưỡng chung khi chưa có căn cứ tương thích |

Ví dụ `rating <= 4/10` chỉ là một **phương án nghiên cứu**, chưa phải nhãn được duyệt. Chốt ngưỡng theo ý nghĩa nguồn và yêu cầu proposal; không chọn ngưỡng vì nó tạo biểu đồ đẹp hoặc cải thiện mô hình. Nếu cần, kiểm tra độ nhạy bằng một hoặc hai ngưỡng lân cận trên tập phát triển, công bố mọi kết quả thay vì chỉ kết quả thuận lợi.

Rating là nhãn đại diện do người dùng chấm; chưa đồng nghĩa cảm xúc của riêng câu chữ. Một review có thể vừa khen vừa chê, mỉa mai, có phủ định hoặc lệch giữa text và điểm.

### 2.2. RQ phụ — số review và rating ở cấp quán

**RQ1 nguyên bản:** số review platform công bố có liên hệ âm với rating trung bình platform của quán không?

**Quyết định theo dữ liệu hiện có:** tạm ghi RQ1 nguyên bản **chưa khả thi**, vì audit local cho thấy hai field cần thiết đều thiếu 100%. Nếu DB có metadata được bổ sung từ luồng khác, phải chứng minh nguồn gốc/độ phủ trước khi thay quyết định này. Không dành phần lớn tuần 5–6 mở rộng crawler để cứu một câu hỏi phụ; ưu tiên hoàn thành EDA chính và nêu giới hạn trong Report 3.

- `X = log1p(platform_total_reviews)`, `Y = platform_avg_rating`.
- Một quán/nguồn xuất hiện một lần trong snapshot; tách theo nguồn và thời điểm thu thập phù hợp.
- Chỉ thực hiện đúng RQ1 nếu hai biến platform được thu thập và có độ phủ đủ để phân tích có ý nghĩa.
- Crawler hiện chủ yếu chuyển tiếp ID, tên, địa chỉ, URL, city; việc có cột trong DB không bảo đảm đã có metadata cần cho RQ1.

**Nhánh thay thế nếu thiếu metadata:** khảo sát `n_reviews_crawled` với `mean_rating_crawled`, đổi tên thành “mối liên hệ trong mẫu đã crawl”. Đây là một câu hỏi khác, chịu ảnh hưởng giới hạn crawler; không dùng để trả lời thay cho số review/rating thật trên platform. Quán có 0 rating hợp lệ phải có `mean_rating_crawled = NA`.

Với một snapshot, chỉ kết luận liên hệ giữa các quán. Snapshot lịch sử mới giúp bảo toàn dữ liệu cho nghiên cứu sau này; nó không tự tạo đủ chuỗi thời gian hoặc chứng minh “quán đông lên làm chất lượng giảm”.

### 2.3. Câu hỏi hỗ trợ

- Dữ liệu tập trung vào địa phương, thời gian, nhóm quán và người viết nào?
- Review thiếu text hoặc rating có khác nhóm đủ dữ liệu không?
- Một số ít quán có chi phối thống kê tính theo review không?
- Có trùng nội dung hoặc nhóm review gần trùng gây rò rỉ giữa các tập không?
- Kết luận có thay đổi khi tính mỗi quán cùng trọng số, loại nhóm nghi trùng hoặc đổi ngưỡng nhãn không?

## 3. Hợp đồng dữ liệu cho EDA

### 3.1. Đóng băng đầu vào

Sau khi hạ tầng hoạt động và migration được áp dụng:

1. Nạp các snapshot raw qua manifest hoàn chỉnh. Mỗi quán trong manifest chỉ có một snapshot được chọn; lưu bản manifest cùng báo cáo.
2. Đối chiếu số object chọn, object thành công/thất bại, số review raw, transformed và đã nạp. Không ghi “ETL thành công toàn bộ” nếu còn object lỗi.
3. Xuất dữ liệu bằng `export_analysis_snapshot.py`, trong một giao dịch PostgreSQL `REPEATABLE READ READ ONLY`, để các bảng cùng nhìn một trạng thái nhất quán.
4. Lưu `reviews.csv`, `restaurants.csv`, `raw_lineage.csv` và `manifest.json` vào thư mục dataset mới. Script từ chối ghi đè một `dataset_id` đã có và từ chối xuất khi còn review không có lineage.
5. Thêm quyết định phạm vi, nhãn, split và hash file phân tích vào manifest phân tích riêng. Thay đổi quy tắc có ảnh hưởng dữ liệu phải tăng phiên bản.

Ví dụ lệnh từ thư mục gốc workspace:

```powershell
uv run python code/hung/src/storage/init_postgres.py
uv run python code/hung/src/processing/minio_to_postgres.py --source foody --manifest code/hung/data/foody_shoppefood/manifests/<upload_run_id>.json --workers 4
uv run python code/hung/src/processing/export_analysis_snapshot.py --dataset-id eda-v1-20261019
```

Các lệnh là hướng dẫn cho lần chạy tiếp theo; chưa được chạy với DB thật trong phiên này. Chạy kiểm tra một object trước, xem log và đối chiếu raw–DB rồi mới nạp diện rộng.

### 3.2. Hai bảng phân tích

| Bảng | Grain và khóa | Nội dung chính | Kiểm tra bắt buộc |
|---|---|---|---|
| `reviews.csv` | Một review; source + review ID | Text, rating, scale, ngày đăng, quán, city, category, price, observed_at, raw key | Khóa không trùng; một review liên kết đúng một quán; số dòng không tăng sau join |
| `restaurants.csv` | Một quán/nguồn; source + restaurant ID | Metadata platform, số review crawl, trung bình rating crawl, số rating không thiếu, cuisines đã aggregate | Khóa không trùng; các biến platform và crawl khác tên; nêu rõ quán có 0 review |
| `raw_lineage.csv` | Các phiên bản raw/transform có liên quan đầu ra | SHA raw, key, thời điểm, version và hash code | Mọi raw key dùng trong hai bảng có ledger tương ứng |

Không nối `review_tags` và `restaurant_cuisines` ở dạng nhiều dòng vào bảng review rồi mới đếm. Aggregate chúng theo đúng khóa trước khi join. Không dùng `COUNT(*)` sau join bảng con làm số review.

### 3.3. Tập hợp và mẫu số phải có tên riêng

| Tập | Điều kiện | Dùng cho |
|---|---|---|
| `D_inventory` | Tất cả bản ghi kiểm kê | Funnel và chất lượng dữ liệu |
| `D_scope` | Đúng nguồn, địa lý, ngôn ngữ/phạm vi đã chốt | Mô tả phạm vi nghiên cứu |
| `D_text` | Trong phạm vi, text có nội dung sau quy tắc cleaning | EDA văn bản không cần nhãn |
| `D_labeled` | Trong phạm vi, text có nội dung, rating hợp lệ và định nghĩa được nhãn | EDA có nhãn, split cho modeling |
| `D_restaurant_rq1` | Quán có đủ biến đúng định nghĩa RQ1 | Phân tích cấp quán |

Một dòng có thể vi phạm nhiều quy tắc. Báo cáo đồng thời **số vi phạm từng cờ** và **funnel loại tuần tự với thứ tự cố định**; không cộng các cờ chồng lấp rồi gọi là số review bị loại. Ví dụ tỷ lệ thiếu text có mẫu số toàn bộ review, trong khi tỷ lệ lớp thấp có mẫu số review đủ điều kiện nhãn.

## 4. Kế hoạch 14 ngày

Đề xuất khoảng 32–40 giờ làm việc chủ động cho một người trong hai tuần; thời gian chờ quét/nạp dữ liệu tính riêng. Nếu hai người, chia phần dữ liệu–SQL và RStudio–báo cáo, nhưng dùng chung snapshot và review chéo.

| Ngày | Việc cụ thể | Thời lượng gợi ý | Đầu ra và điều kiện kết thúc |
|---|---|---:|---|
| T5–N1 | Đọc cleaning audit, chạy kiểm thử versioning, bật hạ tầng theo quy trình hiện có, áp dụng migration; chọn một quán kiểm tra hai lần nạp | 3h | Bằng chứng snapshot cũ còn, hash khớp, nạp lặp không tăng review, lỗi không commit nửa chừng |
| T5–N2 | Chốt manifest; đối chiếu raw–transform–DB; xuất dataset nhất quán; kiểm tra grain và khóa | 3h | Dataset v1 + manifest + bảng funnel, mọi chênh lệch có giải thích |
| T5–N3 | Kiểm tra thang điểm/giá trị 0; lập mapping địa lý; xác minh language; đánh giá metadata RQ1 | 3h | `scope_decisions.md`, `label_definition.md`, quyết định giữ/đổi RQ1 có lý do |
| T5–N4 | Lập Data Dictionary v1; thống kê missing, rating, coverage; tạo khung R Markdown | 2.5h | Dictionary đủ biến dùng; bảng quality; 3 biểu đồ đầu chạy từ snapshot |
| T5–N5 | Audit trùng chính xác/gần trùng; tạo nhóm quán và duplicate; chia development/test; lưu manifest | 3h | Không có quán/nhóm trùng qua hai tập; bảng hỗ trợ lớp/quán; seed cố định |
| T5–N6 | EDA một biến trên development: rating, text length, số review/quán; chốt mẫu đọc tay | 2.5h | Biểu đồ A01–A06, bảng median/IQR/quantile; danh sách ID mẫu đọc tay |
| T5–N7 | Review tuần 5, sửa báo cáo/chú thích, xác nhận các cổng chất lượng; commit có ý nghĩa | 1.5h | Dataset v1 được nghiệm thu hoặc danh sách blocker cụ thể, không tự thay dataset sau nghiệm thu |
| T6–N1 | EDA thiếu dữ liệu và bias theo city, thời gian, mức độ đầy đủ crawl; hoàn thiện địa lý/ngôn ngữ | 2.5h | Biểu đồ A02/A04/A07/A08 và diễn giải phạm vi đại diện |
| T6–N2 | So sánh độ dài theo rating/nhãn; mức tập trung và kết quả theo trọng số quán | 3h | A06/A09, effect size/CI phù hợp; biết kết luận có bị quán lớn chi phối không |
| T6–N3 | Từ/cụm từ theo lớp trên development; đọc ngữ cảnh, chuẩn hóa theo số document; audit cụm phủ định | 3h | A10–A11, bảng hỗ trợ review/quán, không gọi từ khóa là nguyên nhân |
| T6–N4 | RQ1 hoặc nhánh thay thế; kiểm tra độ nhạy; đọc tay đánh giá text–rating; ghi giới hạn | 3h | A12–A14, quyết định đủ/chưa đủ bằng chứng; kết quả đọc tay có mẫu số |
| T6–N5 | Tổng hợp 3–5 phát hiện; hoàn thiện dictionary, nhãn/feature allowed-list và thiết kế đánh giá tuần 7 | 2.5h | Bảng câu hỏi → bằng chứng → kết luận → giới hạn; handoff modeling |
| T6–N6 | Viết Report 3, render R Markdown/Quarto từ đầu; kiểm tra mọi con số và caption | 3h | HTML/PDF cuối, source R, file figures và session information |
| T6–N7 | Chạy lại từ session sạch, review checklist, chuẩn bị giải thích miệng và commit | 1.5h | Report 3 hoàn chỉnh, AI log, README, tối thiểu 2 commit/tuần theo yêu cầu môn |

Lịch là ngày tương đối trong tuần học, không giả định tuần 5 bắt đầu ngày 19/10. Nếu cần rút ngắn: giữ A01–A06, A09–A10 và phân tích RQ chính; chuyển biểu đồ bổ trợ/phân tích vùng miền sang phụ lục. Không bỏ version, grain, split hoặc kiểm tra nhãn để tiết kiệm thời gian.

## 5. Danh mục phân tích EDA

### A01 — Funnel, quy mô và độ phủ

**Mục tiêu:** biết chính xác bao nhiêu dữ liệu được dùng và phần nào bị mất qua từng bước.

- Đếm số object, quán, review theo source/city; raw → transform → DB → scope → đủ text/rating → development/test.
- Ghi số quán không có review, số review/quán, thời điểm crawl và khoảng thời gian đăng bài.
- Vẽ funnel và biểu đồ cột số review/quán theo nguồn; bảng đếm là bằng chứng chính.
- Điều kiện đạt: số dòng có thể đối soát, không dùng số quán thay số review hoặc ngược lại.

### A02 — Missing và cơ chế chọn mẫu

**Biến:** text, rating, review_date, language, city, category, price, platform_total_reviews, platform_avg_rating.

- Tính `n_missing`, `%missing` theo đúng grain; metadata quán thống kê cả theo quán và theo review để thấy khác biệt trọng số.
- Vẽ cột tỷ lệ thiếu, ma trận đồng thiếu; so sánh thiếu text theo rating, city, số review/quán và completeness.
- Tách “nguồn không cung cấp”, “parse lỗi”, “chưa crawl”, “không biết” khi có bằng chứng; không suy ra nguyên nhân từ NULL đơn thuần.
- Nếu thiếu liên hệ với nhóm rating/city, mô tả nguy cơ tập đủ dữ liệu không đại diện. EDA không tự chứng minh missing hoàn toàn ngẫu nhiên.
- Đầu ra: bảng missing theo biến và nhóm; quyết định không sử dụng biến thiếu/tin cậy kém trong baseline.

### A03 — Phân bố rating và lớp mục tiêu

- Dùng tần suất các mức rating thực tế; Foody có thể có số thập phân nên không ép thành số nguyên hoặc 5 mức sao.
- Vẽ histogram/mức điểm theo nguồn, cột tỷ lệ lớp có cả số mẫu và tỷ lệ; dùng bins cố định có giải thích khi quá nhiều mức.
- Tách NULL, 0, ngoài miền và giá trị chưa xác minh. Kiểm tra tích tụ tại 0/5/10, điểm làm tròn, khác biệt giữa nguồn.
- Báo cáo số review và số quán chứa lớp thấp. Một nghìn review thấp từ một quán không tương đương hỗ trợ từ một nghìn quán.
- Đầu ra: quyết định nhãn, prevalence development và giới hạn mất cân bằng lớp; chưa suy từ accuracy giả định.

### A04 — Địa lý, quốc gia và ngôn ngữ

- Giữ `city_raw`; tạo `country_scope`, `city_canonical`, `region_analysis`, `mapping_version` riêng.
- Dữ liệu local có slug ngoài Việt Nam như Bangkok, Singapore, Tokyo. Không tự gán mọi dòng vào Bắc/Trung/Nam.
- Giữ địa danh tại nguồn/thời điểm thu thập; nếu quy đổi địa giới, công bố bảng mapping và phiên bản, không áp nhãn hành chính mới một cách ngầm định.
- Language thiếu phải là `unknown`; không coi language NULL là tiếng Việt. Nếu dùng nhận diện tự động, lưu công cụ/phiên bản và đọc kiểm tra mẫu, đặc biệt review ngắn/mixed-language.
- Vẽ top địa phương theo review **và theo quán**; tách nhóm “khác”; báo cáo phần ngoài phạm vi thay vì xóa khỏi kiểm kê.
- So sánh vùng chỉ là phân tích phụ khi mapping rõ, nguồn tương thích và hỗ trợ đủ quán; ưu tiên mô tả nếu nhóm quá nhỏ.

### A05 — Mức tập trung review theo quán

- Đếm `n_reviews_crawled` theo source + restaurant ID; tính median, IQR, P90/P95/P99, min/max.
- Vẽ histogram với trục `log1p(n)` và đường tỷ trọng tích lũy review do các quán đóng góp; thêm tỷ trọng top 1%, 5%, 10% quán.
- Phân biệt số review crawl và tổng review platform. Nếu có tỷ lệ coverage, chỉ tính khi mẫu số platform xác minh được và >0.
- Không xóa quán nhiều review chỉ vì là outlier. Kiểm tra log/crawl limit rồi làm phân tích độ nhạy.
- Đầu ra: quyết định báo cáo song song kết quả trọng số review và trọng số quán.

### A06 — Cấu trúc và độ dài văn bản

- Tạo `n_chars`, `n_whitespace_tokens`, cờ URL/HTML/emoji/phủ định/repeated characters khi quy tắc rõ; dùng cùng một phiên bản text.
- `n_whitespace_tokens` là số token tách khoảng trắng, **không gọi là số từ tiếng Việt** nếu chưa có tách từ phù hợp.
- Báo cáo median/IQR/P95/P99; vẽ histogram trục log hoặc ECDF. Giữ bảng phân phối đầy đủ ngay cả khi trục hình cắt tại P99 để dễ đọc.
- Gắn cờ text cực ngắn, cực dài, HTML sót lại; kiểm tra mẫu. Không cắt bỏ tự động, không xóa dấu/emoji/từ phủ định.
- Đầu ra: mô tả độ nhiễu và nhóm review khó; các thay đổi cleaning nếu phát sinh cần dataset version mới, không sửa âm thầm giữa EDA.

### A07 — Thời gian và mức cập nhật

- Phân biệt `review_date` (ngày đăng), `observed_at` (lần quan sát review), `crawl_timestamp` (snapshot quán), `loaded_at` (nạp DB).
- Thống kê độ phủ ngày đăng, ngày bất hợp lý, tỷ lệ thiếu và độ trễ từ đăng đến crawl. Kiểm tra timezone trước khi phân ngày/tháng.
- Vẽ số review theo tháng đăng, tỷ lệ lớp thấp theo tháng kèm số review/quán hỗ trợ. Không dùng các tháng quá nhỏ để kể câu chuyện xu hướng.
- Ngày crawl không thay thế ngày khách đăng. Một đợt crawl không chứng minh thay đổi chất lượng theo thời gian; số review theo tháng còn chịu thiên lệch hồi cứu/xóa bài/giới hạn API.

### A08 — Completeness và sampling bias

- Đọc `crawl_complete`, `stop_reason`, pages/items scanned, full-refresh/incremental và giới hạn crawler từ raw qua lineage khi cần.
- So sánh quán complete/không complete theo quy mô và rating; ghi số quán đạt gần giới hạn lấy listing như một dấu hiệu cần điều tra, không tự kết luận API bị cap.
- `crawl_complete=True` là trạng thái theo logic crawler, không phải bằng chứng độc lập đã có mọi review trên platform.
- Đầu ra: bảng giới hạn lấy mẫu, vùng/loại quán thiếu, khoảng thời gian quan sát và phần dữ liệu chưa thể coi đại diện.

### A09 — Độ dài bình luận theo rating/nhãn

- Vẽ boxplot/violin hoặc ECDF trên development, kèm median/IQR và số review/quán mỗi nhóm.
- So sánh độ lớn khác biệt, ví dụ chênh median số ký tự hoặc tỷ số median; dùng cluster bootstrap theo quán nếu báo khoảng tin cậy trên dữ liệu review.
- Không coi hàng nghìn review cùng quán là các quan sát độc lập để tạo p-value quá lạc quan. Kiểm tra thêm tóm tắt ở cấp quán.
- Kruskal–Wallis chỉ là lựa chọn thăm dò khi giả định độc lập phù hợp; không mặc định kiểm định này giải quyết phụ thuộc trong quán.
- Diễn giải quan hệ hai chiều: review dài có thể khen hoặc chê; độ dài không phải cảm xúc.

### A10 — Từ/cụm từ liên quan đến lớp thấp

- Chỉ dùng development. Chọn trước cách lowercase, Unicode, loại URL và tokenization; lưu cả text gốc và text cho đếm từ.
- Giữ phủ định (`không`, `chưa`, `chẳng`), dấu tiếng Việt và cụm từ; unigram có thể đảo nghĩa khi đứng một mình.
- Ưu tiên **document frequency**: số review chứa term / số review của lớp, thay vì tổng số lần term xuất hiện. So sánh hai lớp trên cùng mẫu số đã chuẩn hóa.
- Vẽ top terms theo tỷ lệ document và chênh tỷ lệ, kèm n review và n quán hỗ trợ. Một lựa chọn cảnh báo để đọc tay là <20 review hoặc <5 quán; đây là ngưỡng trình bày đề xuất, không phải ranh giới thống kê.
- Nếu dùng log-odds/lift, công bố smoothing và độ hỗ trợ; hạn chế suy diễn term hiếm. Không gọi TF-IDF hoặc word cloud là kiểm định từ khóa quyết định.
- Đầu ra: 15–30 term/cụm ứng viên cùng ngữ cảnh đã ẩn định danh; chốt danh sách cần kiểm tra ở modeling, chưa tuyên bố “fatal keywords” cuối cùng.

### A11 — Chủ đề phàn nàn và đọc ngữ cảnh

- Lấy mẫu phân tầng trên development theo rating/nhãn, độ dài, city và nhóm nghi trùng; khoảng 150–200 review là cỡ mẫu khả thi đề xuất.
- Ẩn rating khi người đọc gán cảm xúc text nếu có thể; hai người đọc độc lập một phần/toàn bộ mẫu, ghi bất đồng và cách phân xử.
- Lưu bảng gồm ID đã mã hóa, cảm xúc text, chủ đề (chất lượng món/giao hàng/phục vụ/giá/vệ sinh/khác), cờ mỉa mai/phủ định/khen-chê lẫn, quyết định và lý do.
- Báo tỷ lệ đồng thuận, confusion table text–rating; nếu dùng Cohen's kappa phải kèm tỷ lệ lớp và giới hạn khi lệch lớp. Mẫu này không tạo “ground truth” cho toàn dataset.
- Nếu lấy mẫu không tỷ lệ để xem nhiều review hiếm/khó, không lấy tỷ lệ thô của mẫu đọc tay làm tỷ lệ toàn bộ dataset; dùng trọng số lấy mẫu khi ước lượng hoặc chỉ báo kết quả theo tầng.

### A12 — RQ1 cấp quán hoặc câu hỏi thay thế

- Kiểm tra đủ cặp biến, cùng nguồn/thời điểm, review_count không âm. Một quán là một quan sát.
- Vẽ scatter có transparency/hexbin khi dày, `log1p(review_count)` trên trục x; tránh tính tương quan của dữ liệu đã bin.
- Bắt đầu bằng Spearman rho trên cặp đầy đủ. Khi có ties, cấu hình và ghi rõ cách tính; `cor.test(..., method='spearman', exact=FALSE)` cung cấp p-value xấp xỉ. Khoảng tin cậy Spearman cần phương pháp riêng, chẳng hạn bootstrap ở cấp quán; không lấy nhầm CI Pearson.
- Nếu biến kiểm soát tin cậy và đủ độ phủ, bổ sung hồi quy với sai số chuẩn phù hợp; kiểm tra phi tuyến và điểm ảnh hưởng. Không ép điền category/price thiếu bằng giá trị cố định để đủ chạy hồi quy.
- Nếu metadata thiếu hoặc cỡ mẫu độc lập quá nhỏ, ghi RQ1 chưa khả thi. Với nhánh crawl-only, ghi rõ đây là trung bình không trọng số của rating trong mẫu crawl, chưa đại diện rating platform.
- Tài liệu hàm kiểm định: [R stats — cor.test](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/cor.test.html).

### A13 — Trùng và gần trùng

- Phân biệt trùng khóa (lỗi grain), cùng text khác ID, cùng bài có format khác và review ngắn phổ biến.
- Dùng NFC + chuẩn hóa khoảng trắng để tạo hash chẩn đoán; không mặc định mọi “ngon”, “ok” giống nhau là một bài trùng.
- Đọc mẫu các nhóm text dài giống nhau, xem hỗ trợ quán/ngày/ID; nếu làm gần trùng, nêu representation, ngưỡng và tỷ lệ kiểm tra tay. Ngưỡng chỉ fit/tinh chỉnh trên development.
- Tạo `duplicate_group_id` cho những nhóm có lý do xác thực. Chính sách có thể giữ mọi raw nhưng chọn một đại diện cho phân tích có trọng số; mọi loại trừ phải log.
- Đầu ra: số nhóm, số dòng ảnh hưởng, lý do xử lý và kiểm tra các nhóm đó không đi qua development/test.

### A14 — Kiểm tra độ bền của các phát hiện

Chọn 2–3 thay đổi có lý do, không chạy hàng chục lựa chọn rồi chỉ báo lựa chọn thuận lợi:

1. Toàn bộ development so với phần quán có completeness tốt hơn.
2. Trọng số theo review so với mỗi quán cùng trọng số.
3. Giữ so với xử lý nhóm trùng đã xác minh; hoặc ngưỡng nhãn lân cận nếu bài toán cho phép.

Báo chiều, độ lớn và mức thay đổi kết luận. Nếu kết quả phụ thuộc mạnh vào một lựa chọn, đó là một phát hiện về giới hạn dữ liệu. Với nhiều kiểm định thăm dò, ghi rõ tính thăm dò; xác định trước phân tích chính và cân nhắc điều chỉnh đa kiểm định khi có nhiều so sánh xác nhận.

## 6. Chia tập trước EDA chi tiết để bảo vệ tuần 7–8

1. Hoàn tất kiểm tra kỹ thuật toàn dataset (schema, ID, lỗi miền, trùng); chốt phạm vi và định nghĩa nhãn dựa trên ý nghĩa nguồn.
2. Nhóm theo `source_code + restaurant_id`. Nếu xác định được cùng quán vật lý qua nguồn, liên kết cùng nhóm; không đoán bằng tên đơn thuần.
3. Nếu một duplicate group trải qua nhiều quán, xây nhóm liên thông chứa cả các quán và duplicate group trước khi chia. Việc này có thể làm nhóm rất lớn; nếu vậy báo ảnh hưởng và chọn chính sách trùng có giải trình, không tách nhóm chỉ để đạt đúng 80/20.
4. Chia development/test theo nhóm, mục tiêu xấp xỉ 80/20; seed đề xuất `20261019`. Tỷ lệ review thực tế có thể khác tỷ lệ quán. Không thử nhiều seed để chọn kết quả dễ hơn.
5. Lưu `split_manifest.csv` với source, review ID, restaurant ID, split group, duplicate group, split, seed, dataset_id và hash quy tắc.
6. Kiểm tra không trùng ID/quán/nhóm trùng qua hai tập. Mỗi tập cần có đủ quán chứa lớp thấp; nếu không đủ, điều chỉnh phạm vi hoặc thiết kế nghiên cứu và ghi lý do.
7. EDA nội dung, từ khóa, lựa chọn feature và giả thuyết chi tiết chỉ trên development. Test chỉ kiểm tra cấu trúc và hỗ trợ lớp, sau đó giữ riêng đến khi chốt mô hình ở tuần 8.

Đây là thiết kế đánh giá trên **quán chưa thấy**. Nếu câu hỏi chuyển sang dự đoán tương lai tại quán đã biết, phải lập split theo thời gian và kiểm soát trùng bằng một thiết kế khác. Hướng dẫn nhóm quan sát cùng tập xem [rsample group splitting](https://rsample.tidymodels.org/reference/initial_split.html); phòng rò rỉ preprocessing xem [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).

## 7. Data Dictionary cần bàn giao

Mỗi biến có: tên, bảng/grain, định nghĩa, kiểu, đơn vị/thang, nguồn raw/SQL, quy tắc missing, miền hợp lệ, công thức, thời điểm sẵn có, vai trò, xử lý cleaning và ví dụ đã ẩn định danh.

| Biến/nhóm | Định nghĩa và lưu ý quan trọng | Vai trò |
|---|---|---|
| `source_code`, review/restaurant ID | ID là chuỗi; khóa ghép có source | Join/split/audit; không làm feature |
| `review_text`, `review_title` | Text nguồn và phiên bản text phân tích cần phân biệt | Nội dung để phân tích; công bố có dùng title hay không |
| `rating`, `rating_scale_max` | Giá trị gốc/thang nguồn đã xác minh | Rating tạo nhãn; không làm feature cho chính nhãn đó |
| `is_low_rating`/`is_one_star` | Hàm và ngưỡng theo nguồn, giữ NA nếu chưa đủ điều kiện | Nhãn, có version |
| `city_raw`, `country_scope`, `region_analysis` | Mapping địa lý có version, giữ nhóm unknown | Mô tả/phân tầng; feature chỉ khi tin cậy |
| `language`, `language_detected` | Nguồn cung cấp và nhận diện tự động khác nhau | Phạm vi/quality; không lấp NULL bằng `vi` |
| `category`, `price_range`, cuisines | Độ phủ và mức tin cậy riêng; cuisines aggregate | Metadata ứng viên có điều kiện |
| `platform_total_reviews`, `platform_avg_rating` | Số liệu platform nếu thực sự đã thu thập | RQ1; có nguy cơ hậu nghiệm khi modeling |
| `n_reviews_crawled`, `mean_rating_crawled` | Đếm/trung bình trong snapshot mẫu crawl; trung bình chỉ trên rating không thiếu | EDA mẫu; không đánh tráo metadata platform |
| `n_chars`, `n_whitespace_tokens` | Công thức, text version và quy tắc đếm rõ | EDA, feature cấu trúc ứng viên |
| `review_date`, `observed_at`, `crawl_timestamp`, `loaded_at` | Bốn thời điểm khác nhau; timestamp UTC, hiển thị +07 khi cần | EDA thời gian/provenance |
| `raw_object_key`, `raw_sha256`, code/transform version | Snapshot và mã xử lý đã dùng | Tái lập; không làm feature |
| Cờ chất lượng và eligibility | Tên cờ, điều kiện, thứ tự funnel | Chọn tập/công khai loại trừ |
| `duplicate_group_id`, `split_group_id`, `split` | Quy tắc tạo nhóm và seed | Chống leakage, kiểm thử split |

Không tự nhận giá trị mẫu là giá trị quan sát thật. Không đưa tên người dùng, số điện thoại, URL cá nhân hoặc nội dung định danh vào biểu đồ/báo cáo.

## 8. Cách tổ chức báo cáo trong RStudio

Đề xuất `notebooks/WEEK_5_6_EDA.Rmd` hoặc `.qmd`, nhận tham số đường dẫn dataset cố định. Nội dung:

1. Mục tiêu, dataset_id, nguồn và thời điểm.
2. Xác minh manifest/hash và đọc CSV UTF-8; ép ID thành character, rating numeric, timestamp đúng timezone.
3. Kiểm tra grain/join và quality funnel.
4. Áp phạm vi và tạo biến dẫn xuất theo quyết định đã lưu.
5. Đọc split manifest và chỉ mở development cho EDA chi tiết.
6. Các phân tích A01–A14 với caption nêu n review, n quán, subset và cách xử lý missing.
7. Kết quả đọc tay và nhạy cảm với lựa chọn phân tích.
8. Bảng phát hiện, giới hạn và bàn giao modeling.
9. `sessionInfo()`, seed, phiên bản package, code/dataset hash.

Các package R phù hợp: `readr`, `dplyr`, `tidyr`, `ggplot2`, `stringr`, `jsonlite`, `digest`, và `rsample` nếu dùng split trong R. Khóa môi trường bằng `renv` nếu nhóm đã dùng; chỉ cài thứ cần thiết. Tạo `figures/` và `tables/` theo dataset_id, không sửa tay con số trong báo cáo. RStudio hỗ trợ render báo cáo có code và kết quả cùng tài liệu; xem [Quarto computations in RStudio](https://quarto.org/docs/get-started/computations/rstudio).

**Mẫu câu diễn giải:** “Trong [subset, dataset_id], [kết quả và đơn vị] với [n review, n quán]; so với [nhóm], chênh lệch [effect size/CI nếu có]. Kết quả gợi ý [liên hệ], nhưng bị giới hạn bởi [sampling/missing/phụ thuộc/nhãn đại diện].” Chỉ điền sau khi chạy.

## 9. Bố cục Report 3

| Phần | Nội dung phải có | Bằng chứng |
|---|---|---|
| Bối cảnh và câu hỏi | RQ chính/phụ, grain, scope, nhãn | Quyết định được chốt, không thay khái niệm sao/điểm |
| Dữ liệu và cleaning | Luồng, quy tắc đã làm, missing/duplicate, funnel | Notebook/script cleaning, audit, bảng trước–sau |
| Versioning và tái lập | Snapshot, manifest, code version, split | Raw keys/hash, dataset manifest, hướng dẫn chạy |
| EDA bằng RStudio | Phân bố, quan hệ, text, sampling bias | Source R + report render + biểu đồ có caption |
| Phát hiện và bàn luận | 3–5 phát hiện có số liệu, độ lớn và hỗ trợ | Bảng/biểu đồ tạo tự động, giới hạn rõ |
| Data Dictionary | Đầy đủ biến dùng trong phân tích | Bảng/file dictionary có version |
| Handoff tuần 7–8 | Nhãn, feature allowed-list, split và metric dự kiến | Cấu hình đóng băng; test chưa dùng để chọn feature |

Không yêu cầu số trang cụ thể từ tài liệu được cung cấp; ưu tiên đầy đủ bằng chứng. Số biểu đồ là đề xuất, không phải tiêu chí chấm cứng.

## 10. Cổng nghiệm thu và xử lý khi chưa đạt

| Cổng | Điều kiện | Nếu chưa đạt |
|---|---|---|
| G1 — version | Snapshot/hash/manifest đủ; không ghi đè lịch sử; mọi raw key xuất có ledger | Chưa đóng băng dataset; sửa lineage hoặc đối soát lại |
| G2 — grain | Không trùng khóa phân tích; join không nhân dòng; FK đúng | Sửa query/grain, xuất dataset mới |
| G3 — nhãn | Ý nghĩa rating/0 đã xác minh; nhãn thiếu vẫn NA; scope có văn bản | Tạm chỉ EDA mô tả không nhãn, chưa làm term theo lớp |
| G4 — dữ liệu dùng | Text/rating hợp lệ với từng tập; lỗi/loại trừ có log; hỗ trợ lớp theo quán đủ cho thiết kế | Thu hẹp câu hỏi hoặc đổi thiết kế; không bịa label/impute để đủ mẫu |
| G5 — split | Không giao nhóm quán/duplicate; manifest cố định; test được giữ riêng | Sửa split trước EDA chi tiết, ghi version mới |
| G6 — báo cáo | Rerun từ session sạch; cùng dataset/hash; biểu đồ có n/đơn vị/caption; dictionary đủ | Sửa source phân tích và render lại |

Không đặt một tỷ lệ NULL chung để tuyên bố toàn dataset “sạch”. ID/text/nhãn cho modeling cần điều kiện chặt; metadata phụ có thể thiếu và phải được mô tả đúng.

## 11. Hồ sơ bàn giao cuối tuần 6

```text
code/hung/data/processed/<dataset_id>/
  reviews.csv
  restaurants.csv
  raw_lineage.csv
  manifest.json
  scope_decisions.md            # cần bổ sung khi thực hiện EDA
  label_definition.json         # cần bổ sung khi chốt nhãn
  split_manifest.csv            # cần tạo trước EDA nội dung

code/hung/notebooks/
  WEEK_5_6_EDA.Rmd              # hoặc .qmd; cần triển khai/chạy trong RStudio

code/hung/reports/report_3/<dataset_id>/
  Report_3.html hoặc .pdf
  data_dictionary.csv
  figures/
  tables/
  findings_and_limitations.md
```

Những file có ghi “cần” là đầu ra của kế hoạch, chưa được tạo hoặc chưa có kết quả trong phiên này. Script export mới là công cụ hỗ trợ, chưa chạy với PostgreSQL thật.

Handoff modeling ghi rõ: rating và biến suy từ rating không được làm feature; không dùng ID/tên quán/người viết/URL; chỉ fit vectorizer, encoder và bước chọn feature trong train của mỗi fold. Metric dự kiến chính là Average Precision kèm prevalence lớp thấp; tuần 7 mới so sánh baseline và ít nhất hai thuật toán theo yêu cầu Report 4.

Theo audit hiện tại, baseline ngoài ngữ nghĩa chỉ nên bắt đầu từ city đã xác minh và độ dài text; category/price chưa có dữ liệu để sử dụng. Độ dài vẫn là đặc trưng cấu trúc của văn bản, nên phải đặt tên baseline và giải thích phép so sánh chính xác. Nếu có metadata đáng tin được bổ sung sau này, xuất dataset version mới và chốt lại thiết kế trước thực nghiệm.

## 12. Tài liệu cơ sở

- Kế hoạch môn ADY201m 10 tuần: yêu cầu Report 3, Report 4, RStudio, dictionary, GitHub và AI log.
- `PLAN_TUAN_5_6_7_8_Food_Review_Sentiment_Analysis.md`: câu hỏi nghiên cứu, rating khác thang, tránh leakage và timeline.
- `code/hung/docs/HUNG_DATA_CLEANING_AUDIT.md`: mô tả cleaning/ETL trước lần sửa này; giữ nguyên làm tài liệu lịch sử.
- Mã nguồn thực tế trong `code/hung/src`, kiểm kê raw local ngày 19/10/2026 và báo cáo versioning đi kèm.

Các tài liệu đính kèm được dùng làm căn cứ yêu cầu và bối cảnh dự án. Lịch cũ, ví dụ và đề xuất trong tài liệu không được coi là lệnh tự động chạy crawler, huấn luyện mô hình hoặc thay đổi dữ liệu thật.
