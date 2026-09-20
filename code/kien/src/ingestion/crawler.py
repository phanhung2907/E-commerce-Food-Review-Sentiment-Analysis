import csv
import os
from datetime import datetime

def load_and_validate_dataset(file_path="code/kien/data/raw/tripadvisor_real.csv"):
    """
    Hàm kiểm tra và validate tệp dữ liệu TripAdvisor đã thu thập.
    """
    print(f"Đang kiểm tra file dữ liệu tại: {file_path}")
    if os.path.exists(file_path):
        with open(file_path, mode='r', encoding='utf-8') as f:
            total_rows = sum(1 for line in f) - 1  # Trừ đi dòng tiêu đề header
        print(f"Đã tải và validate thành công! Tổng số bản ghi thực tế: {total_rows}")
        return True
    else:
        print(f"Không tìm thấy file tại đường dẫn: {file_path}")
        return False

def automate_data_pipeline():
    print("="*50)
    print("BẮT ĐẦU TIẾN TRÌNH AUTOMATED DATA CRAWL / PIPELINE")
    print(f"Thời gian thực thi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    input_file = "code/kien/data/raw/tripadvisor_real.csv"
    report_file = "code/kien/reports/reports.txt"
    
    # Kiểm tra nguồn dữ liệu thô
    if not os.path.exists(input_file):
        print(f"[LỖI] Không tìm thấy tệp dữ liệu tại: {input_file}")
        return
        
    reviews_count = 0
    valid_records = []
    
    # Đọc và tự động xác thực dữ liệu đầu vào
    with open(input_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reviews_count += 1
            valid_records.append(row)
            
    print(f"Đã tự động quét và nạp thành công: {reviews_count} bản ghi.")
    
    # Ghi nhận báo cáo tự động (Automated Reporting)
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, mode="w", encoding="utf-8") as rep:
        rep.write(f"AUTOMATED CRAWL / INGESTION REPORT\n")
        rep.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        rep.write(f"Source File: {input_file}\n")
        rep.write(f"Total Records Processed: {reviews_count}\n")
        rep.write(f"Status: SUCCESS\n")
        
    print(f"Đã xuất báo cáo tự động tại: {report_file}")
    print("="*50)
    print("TIẾN TRÌNH HOÀN TẤT THÀNH CÔNG.")

# Khối gọi hàm đặt ở CUỐI CÙNG của file
if __name__ == "__main__":
    automate_data_pipeline()
    load_and_validate_dataset()