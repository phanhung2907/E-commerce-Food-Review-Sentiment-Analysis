import subprocess
from pathlib import Path

# Xác định thư mục gốc của project
ROOT = Path.cwd()

# Khai báo các bước trong Pipeline (Trỏ đúng đường dẫn thực tế của nhóm)
SCRIPTS = {
    "Foody Crawler": Path("code/sang/src/ingestion/crawler.py"),
    "MinIO Uploader": Path("code/sang/src/ingestion/MinIO.py")
}

def run(name, path):
    print(f"START : {name}")
    script_path = ROOT / path
    if not script_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file script tại đường dẫn: {script_path}")
    
    # Thực thi file script python con
    subprocess.run(["python", str(script_path)], check=True)
    print(f"DONE : {name}\n")

if __name__ == "__main__":
    try:
        for name, path in SCRIPTS.items():
            run(name, path)
        print("PIPELINE RUN SUCCESSFULLY")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi chạy pipeline tại tiến trình: {e}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")