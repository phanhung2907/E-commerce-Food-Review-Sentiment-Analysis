# Chạy Report 4

Từ thư mục gốc của dự án, dùng môi trường `.venv` đã có:

```powershell
.\.venv\Scripts\python.exe -u code/hung/src/model/report-4/run_report4.py
```

Mặc định script đọc `code/hung/data/preprocess_merged_data/reviews_preprocessed.csv` và ghi kết quả vào `code/hung/docs/report-4/`. Chạy lại có thể ghi đè các file kết quả và model trong thư mục này. Dùng `--output <đường-dẫn>` để ghi sang thư mục khác, `--help` để xem các tham số còn lại.

Đọc `REPORT_4_RESULTS.md` trước. `keyword_results.csv` chứa bảng đếm và kết quả đầy đủ; `split_manifest.csv` lưu cách chia. Các model nằm trong `model/<ngôn-ngữ>/rating-<mức>/`, với `vn` tương ứng mã `vi` trong dữ liệu.

Để nạp model, thêm thư mục chứa script này vào Python module path, sau đó dùng `joblib.load(path)`. File lưu một dictionary có khóa `pipeline` và `metadata`. Chỉ nạp file joblib từ nguồn đáng tin cậy.

Trạng thái xác nhận trong báo cáo chỉ phản ánh các ngưỡng thống kê và hỗ trợ của kế hoạch; cần đọc ngữ cảnh để kiểm tra cụm có ý nghĩa trước khi diễn giải. Đây là liên hệ quan sát, không chứng minh quan hệ nhân quả. Sai số chuẩn theo nhóm dùng xấp xỉ chuẩn, có thể kém tin cậy khi số nhóm hỗ trợ ít; p-value và Holm không tự khắc phục vấn đề này. Việc dò review trùng gần đúng chỉ phát hiện những cặp thỏa điều kiện tìm kiếm trong code.
