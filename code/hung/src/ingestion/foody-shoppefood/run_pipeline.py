import subprocess
import sys
from pathlib import Path


# =========================================================
# CONFIG
# =========================================================

# Khi chạy từ repo root:
# E:\Real-estate-tourism\hung
REPO_ROOT = Path.cwd()

RESTAURANT_CRAWLER = Path(
    "code/hung/src/ingestion/foody-shoppefood/"
    "foody_restaurant_crawler.py"
)

REVIEW_CRAWLER = Path(
    "code/hung/src/ingestion/foody-shoppefood/"
    "foody_review_crawler.py"
)

MINIO_UPLOADER = Path(
    "code/hung/src/storage/minio_uploader.py"
)


# =========================================================
# RUN SCRIPT
# =========================================================

def run_script(name, script_path):
    print("\n" + "=" * 60)
    print(f"START: {name}")
    print("=" * 60)

    full_path = REPO_ROOT / script_path

    if not full_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file:\n{full_path}"
        )

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=REPO_ROOT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed "
            f"with exit code {result.returncode}"
        )

    print("\n" + "=" * 60)
    print(f"DONE: {name}")
    print("=" * 60)


# =========================================================
# MAIN
# =========================================================

def main():
    print("\n" + "=" * 60)
    print("FOODY DATA PIPELINE")
    print("=" * 60)

    print("Repo root:")
    print(REPO_ROOT)

    try:
        run_script(
            "1. Restaurant Crawler",
            RESTAURANT_CRAWLER,
        )

        run_script(
            "2. Review Crawler",
            REVIEW_CRAWLER,
        )

        run_script(
            "3. MinIO Uploader",
            MINIO_UPLOADER,
        )

    except Exception as e:
        print("\n" + "=" * 60)
        print("PIPELINE FAILED")
        print("=" * 60)

        print("Error:")
        print(e)

        sys.exit(1)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()