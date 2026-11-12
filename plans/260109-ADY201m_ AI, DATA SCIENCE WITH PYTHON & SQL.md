# **ADY201m: AI, DATA SCIENCE WITH PYTHON & SQL**

## **HƯỚNG DẪN HỌC TẬP: ADVANCED DATA ENGINEERING & SCIENCE BOOTCAMP**

### **1\. GIỚI THIỆU CHUNG**

Chào mừng các bạn đến với ADY201m. Học kỳ này được thiết kế như một **"Trại huấn luyện" (Bootcamp)** cường độ cao, mô phỏng quy trình làm việc tại các công ty công nghệ lớn.

* **Triết lý RBL (Research-Based Learning):** Chúng ta không học để trả bài. Chúng ta học để chứng minh hoặc bác bỏ các **giả thuyết khoa học**. Bạn phải đặt câu hỏi *trước*, sau đó mới đi tìm dữ liệu để trả lời.  
* **Mục tiêu:** Xây dựng một hệ thống dữ liệu tự động (End-to-End Pipeline) từ Data Lake đến Machine Learning Model.  
* **Tech Stack (Bắt buộc):** Python, SQL, **RStudio**, **Docker (Micro-architecture)**, **MinIO (Data Lake)**, GitHub.

### **2\. CẤU TRÚC LỚP HỌC & ĐÁNH GIÁ (80/20)**

#### **2.1. Đội ngũ dự án**

* **Số lượng:** **1 \- 2 sinh viên / nhóm.**  
* **Yêu cầu:** Khả năng tự học (Self-research) và chịu áp lực cao.

#### **2.2. Phương thức đánh giá (Assessment)**

Điểm số môn học bao gồm **80% Dự án Thực tế** (thông qua 5 Reports) và **20% Thi cuối kỳ**.

**QUAN TRỌNG:** Môn học này **KHÔNG CÓ BÀI KIỂM TRA TRẮC NGHIỆM GIỮA KỲ (NO PROGRESS TESTS)**. Toàn bộ điểm số của Progress Test trong Syllabus đã được chuyển sang đánh giá chất lượng sản phẩm trong Report 2 và Report 4\.

| Report | Quy đổi điểm | Trọng số | Nội dung & Yêu cầu Kỹ thuật (Advanced) |
| :---- | :---- | :---- | :---- |
| **Report 1** | *Project Planning* | **10%** | **Research Proposal & Architecture:** \- Xác định bài toán & **Đặt giả thuyết nghiên cứu (Hypotheses)**. \- Thiết kế kiến trúc hệ thống (Docker Diagram). |
| **Report 2** | *On-going 1 (10%)* \+ *Progress Test 1 (10%)* | **20%** | **Data Lake & Engineering (Heavy Workload):** \- Setup **MinIO** trên Docker. \- Code Pipeline: Crawl \-\> MinIO (Raw) \-\> Dgma. |
| **Report 3** | *On-going 2* | **10%** | **EDA & RStudio Integration:** \- Sử dụng **RStudio** để thực hiện phân tích khám phá (EDA). \- Data Dictionary (Từ điển dữ liệu). |
| **Report 4** | *On-going 3 (10%)* \+ *Progress Test 2 (10%)* | **20%** | **Modeling & Validation (Heavy Workload):** \- Xây dựng 2 mô hình ML khác nhau để kiểm định giả thuyết. \- Đánh giá độ chính xác (Model Evaluation) và so sánh hiệu quả. |
| **Report 5** | *Final Project Eval* | **20%** | **Deployment & Defense:** \- Đóng gói sản phẩm bằng **Docker Compose**. \- Demo & Bảo vệ kết quả nghiên cứu. |
| **Final Exam** | *Final Exam* | **20%** | Thi cuối kỳ (Trắc nghiệm tổng hợp). Điều kiện: Hoàn thành đủ 5 Reports. |

#### **2.3. QUY ĐỊNH VỀ GITHUB & CẤU TRÚC DỰ ÁN (BẮT BUỘC)**

Sinh viên phải tuân thủ nghiêm ngặt quy trình quản lý mã nguồn. **Vi phạm cấu trúc hoặc không commit thường xuyên sẽ bị 0 điểm Report.**

**A. Quy tắc Commit:**

1. **Tần suất:** Phải có commit ít nhất **2 lần/tuần**.  
2. **Message:** Commit message phải rõ ràng (VD: feat: add crawling script for shopee, fix: handle null values in cleaning). Không chấp nhận message kiểu update, final, code.  
3. **Cấm:** Chỉ upload code 1 lần duy nhất vào cuối kỳ \-\> **0 điểm toàn bộ quá trình.**

B. Cấu trúc Thư mục Chuẩn (Project Structure):  
Tất cả các nhóm phải tổ chức GitHub Repo theo cấu trúc cây thư mục sau:  
Student\_ID\_Project\_Name/  
│  
├── .gitignore               \# Loại bỏ file rác, file .env, \_\_pycache\_\_  
├── README.md                \# Hướng dẫn setup và chạy dự án (BẮT BUỘC)  
├── AI\_Log.md                \# Nhật ký sử dụng AI (Prompt engineering log)  
├── docker-compose.yml       \# File khởi chạy toàn bộ hệ thống (MinIO, DB, App)  
├── requirements.txt         \# Các thư viện Python cần thiết  
│  
├── configs/                 \# Chứa file cấu hình (nếu có)  
│   └── db\_config.json  
│  
├── docker/                  \# Các file Dockerfile cho từng service  
│   ├── app/  
│   │   └── Dockerfile  
│   └── db/                  \# (Optional nếu dùng image gốc)  
│  
├── data/                    \# Dữ liệu mẫu (Sample only \- KHÔNG UP DỮ LIỆU LỚN LÊN GITHUB)  
│   ├── raw/  
│   └── processed/  
│  
├── src/                     \# Source code chính  
│   ├── ingestion/           \# Code Crawl/API  
│   │   └── crawler.py  
│   ├── processing/          \# Code làm sạch & ETL  
│   │   └── cleaner.py  
│   ├── modeling/            \# Code Machine Learning  
│   │   └── model.py  
│   └── utils/               \# Các hàm tiện ích dùng chung  
│  
├── notebooks/               \# Jupyter Notebooks & RMarkdown (Dùng để phân tích/EDA)  
│   ├── 1\_Exploration.ipynb  
│   └── 2\_Modeling.ipynb  
│  
└── reports/                 \# Các file báo cáo PDF nộp định kỳ  
    ├── Report\_1\_Proposal.pdf  
    └── Report\_2\_DataEngineering.pdf

### **3\. QUY TRÌNH KỸ THUẬT (TECHNICAL WORKFLOW)**

Sinh viên phải thiết lập môi trường Local mô phỏng hệ thống Enterprise:

1. **Infrastructure (Docker Compose):**  
   * Container 1: **MinIO** (Data Lake \- S3 Compatible).  
   * Container 2: **Database** (PostgreSQL hoặc SQLite mount volume).  
   * Container 3: **App/Workstation** (Python/RStudio environment).  
2. **Data Pipeline:**  
   * **Ingestion:** Python Crawl \-\> Lưu file JSON/HTML thô vào MinIO.  
   * **Processing:** Đọc từ MinIO \-\> Làm sạch \-\> Lưu vào Database.  
   * **Analysis:** RStudio/Jupyter kết nối DB \-\> Visualize \-\> Modeling.

### **4\. CHỦ ĐỀ NGHIÊN CỨU & ĐỊNH HƯỚNG GIẢ THUYẾT**

*Lưu ý: Sinh viên cần chuyển hóa các vấn đề cốt lõi thành Giả thuyết khoa học (*\$H\_0, H\_1\$*) trong Report 1\.*

#### **CHỦ ĐỀ 1: BẤT ĐỘNG SẢN & DU LỊCH (Real Estate/Tourism)**

* **Nguồn:** Booking, Agoda, Batdongsan.  
* **Vấn đề Cốt lõi:**  
  1. *Vị trí:* "Liệu có phải cứ gần trung tâm/biển là giá cao, hay còn phụ thuộc vào yếu tố khác (an ninh, tiện ích)?"  
  2. *Quy luật giá:* "Diện tích và Giá tiền có thực sự tuyến tính? Có điểm bão hòa nào không?"  
* Câu hỏi MỞ (Gợi ý): Tiện ích nào (Hồ bơi, view biển, gần trung tâm) làm tăng giá phòng nhiều nhất?

#### **CHỦ ĐỀ 2: PHÂN TÍCH CẢM XÚC (Sentiment Analysis)**

* **Nguồn:** ShopeeFood, Foody.  
* **Vấn đề Cốt lõi:**  
  1. *Xu hướng:* "Chất lượng dịch vụ (qua rating) có xu hướng đi xuống khi quán trở nên quá đông khách (nhiều review) không?"  
  2. *Ngôn ngữ:* "Các từ khóa nào mang tính quyết định đến việc khách hàng đánh giá 1 sao (Fatal keywords)?"  
* Câu hỏi MỞ (Gợi ý): Có sự khác biệt vùng miền (Bắc/Nam) trong cách đánh giá không? Hay độ dài comment có liên quan đến số sao không?

#### **CHỦ ĐỀ 3: GAME ANALYTICS (Dota 2 / LoL)**

* **Nguồn:** API Dota/LoL.  
* **Vấn đề Cốt lõi:**  
  1. *Thời lượng:* "Các trận đấu kéo dài (\>40p) có làm thay đổi tỷ lệ thắng của các nhóm tướng (Late game carry) không?"  
  2. *Meta Game:* "Tướng có tỷ lệ chọn (Pick rate) cao liệu có đồng nghĩa với tỷ lệ thắng (Win rate) cao?"  
* Câu hỏi MỞ (Gợi ý): Phân tích sự độc hại (Toxic): Tần suất chat trong game có tương quan với việc thua trận không?

#### **CHỦ ĐỀ 4: TRENDING CONTENT (YouTube/Spotify)**

* **Nguồn:** YouTube/Spotify API.  
* **Vấn đề Cốt lõi:**  
  1. *Thời điểm vàng:* "Upload video vào khung giờ hành chính hay khung giờ nghỉ ngơi sẽ dễ lọt Top Trending hơn?"  
  2. *Tương tác:* "Lượng Dislike (hoặc Comment tiêu cực) có ảnh hưởng đến khả năng viral của video không?"  
* Câu hỏi MỞ (Gợi ý): Phân tích tiêu đề (Title): Các video có từ khóa "giật gân" (SỐC, LỘ, REVIEW) có thực sự nhiều view hơn trung bình không?

#### **CHỦ ĐỀ 5: THỊ TRƯỜNG TUYỂN DỤNG IT**

* **Nguồn:** ITViec, TopDev.  
* **Vấn đề Cốt lõi:**  
  1. *Giá trị bằng cấp:* "Mức lương của các công việc yêu cầu 'University Degree' có cao hơn đáng kể so với các công việc không yêu cầu không?"  
  2. *Kỹ năng:* "Python hay Java đang là ngôn ngữ có 'Median Salary' cao nhất tại thị trường Việt Nam?"  
* Câu hỏi MỞ (Gợi ý): So sánh chế độ đãi ngộ giữa công ty Product và công ty Outsourcing?

### **5\. LỘ TRÌNH TRIỂN KHAI (TIMELINE 10 TUẦN)**

| Tuần | Hoạt động (Tasks) | Deadline & Yêu cầu Báo cáo |
| :---- | :---- | :---- |
| **1 \- 2** | **Project Planning** | **REPORT 1 (10%): Proposal & Architecture** \- Trình bày Giả thuyết nghiên cứu. \- Setup GitHub Repo theo cấu trúc chuẩn. \- Sơ đồ kiến trúc Docker. |
| **3 \- 4** | **Data Engineering** | **REPORT 2 (20%): Data Pipeline** \- Code Crawl \-\> MinIO \-\> DB. \- Chứng minh dữ liệu đã về Data Lake. \- SQL Queries kiểm tra dữ liệu thô. |
| **5 \- 6** | **Cleaning & EDA** | **REPORT 3 (10%): Data Cleaning & RStudio** \- Notebook làm sạch. \- Sử dụng RStudio vẽ biểu đồ phân bố. \- Data Dictionary. |
| **7 \- 8** | **Modeling** | **REPORT 4 (20%): Modeling & Evaluation** \- Chạy mô hình (Regression/Classification). \- Biện luận kết quả: Chấp nhận hay bác bỏ giả thuyết? |
| **9 \- 10** | **Deployment** | **REPORT 5 (20%): Final Defense** \- docker-compose up để demo sản phẩm. \- Slide báo cáo & Trả lời phản biện. |

### **6\. QUY ĐỊNH CHUNG (AI & INTEGRITY)**

1. **AI Policy:** Được dùng AI, nhưng phải nộp AI\_Log.md chứng minh quá trình prompt.  
2. **GitHub:**  
   * Tạo Private Repo, invite giảng viên.  
   * **Bắt buộc:** Phải có file .gitignore để tránh upload file rác (\_\_pycache\_\_, .DS\_Store, file dữ liệu quá nặng).  
3. **Data:** Phải tự crawl. Cấm dùng dataset có sẵn.