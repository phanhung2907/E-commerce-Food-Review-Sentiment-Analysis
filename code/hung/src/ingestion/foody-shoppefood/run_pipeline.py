import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
SCRIPTS = {
    "Restaurant Crawler" : Path("code/hung/src/ingestion/foody-shoppefood/foody_restaurant_crawler.py"),
    "Review Crawler" : Path("code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py"),
    "MinIO Uploader" : Path("code/hung/src/storage/minio_uploader.py")
}

def run(name, path):
    full_path = ROOT / path

    if not full_path.exists():
        raise FileNotFoundError(f"Không tìm thấy {full_path}")
    print(f"\n START : {name}")
    result = subprocess.run([sys.executable, str(path)], cwd= ROOT)
    print(f"DONE : {name}")

def main():
    print("Foody DATA INGESTION PIPELINE")
    try:
        for i, (name,path) in enumerate(SCRIPTS.items(), start= 1):
            run(f"{i} . {name}", path)
    except Exception as e:
        print(f"\n PIPELINE FAILED")
        sys.exit(1)
    print("\n PIPELINE RUN SUCCESFULLY")

if __name__ == "__main__":
    main()