import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()

SCRIPTS = {
    "Restaurant Crawler": Path("code/hung/src/ingestion/foody-shoppefood/foody_restaurant_crawler.py"),
    "Review Crawler": Path("code/hung/src/ingestion/foody-shoppefood/foody_review_crawler.py"),
    "MinIO Uploader": Path("code/hung/src/storage/minio_uploader.py"),
}


def ask_positive_int(message):
    while True:
        try:
            value = int(input(message).strip())
            if value > 0:
                return value
        except ValueError:
            pass
        print("Vui lòng nhập số nguyên > 0.")


def choose_crawl_mode():
    print("\nChọn phương pháp crawl:")
    print("1. Vét cạn toàn bộ restaurant và toàn bộ review")
    print("2. Giới hạn số restaurant và số review")

    while True:
        choice = input("Lựa chọn [1/2]: ").strip()

        if choice == "1":
            return None, None

        if choice == "2":
            max_restaurants = ask_positive_int(
                "Số restaurant tối đa cho mỗi tỉnh/endpoint: "
            )
            max_reviews = ask_positive_int(
                "Số review tối đa cho mỗi restaurant: "
            )
            return max_restaurants, max_reviews

        print("Chỉ nhập 1 hoặc 2.")


def run(name, path, args=None):
    full_path = ROOT / path

    if not full_path.exists():
        raise FileNotFoundError(f"Không tìm thấy {full_path}")

    command = [sys.executable, str(path)]
    if args:
        command.extend(args)

    print(f"\nSTART: {name}")
    result = subprocess.run(command, cwd=ROOT)

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit code {result.returncode}"
        )

    print(f"DONE: {name}")


def main():
    print("FOODY DATA INGESTION PIPELINE")

    max_restaurants, max_reviews = choose_crawl_mode()

    if max_restaurants is None:
        print("\nMODE: VÉT CẠN")
    else:
        print(
            f"\nMODE: GIỚI HẠN | "
            f"{max_restaurants} restaurant/tỉnh | "
            f"{max_reviews} review/restaurant"
        )

    commands = {
        "Restaurant Crawler": (
            ["--max-restaurants", str(max_restaurants)]
            if max_restaurants is not None else []
        ),
        "Review Crawler": (
            ["--max-reviews", str(max_reviews)]
            if max_reviews is not None else []
        ),
        "MinIO Uploader": [],
    }

    try:
        for i, (name, path) in enumerate(SCRIPTS.items(), start=1):
            run(f"{i}. {name}", path, commands[name])
    except Exception as e:
        print(f"\nPIPELINE FAILED: {e}")
        sys.exit(1)

    print("\nPIPELINE RUN SUCCESSFULLY")


if __name__ == "__main__":
    main()
