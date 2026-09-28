import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()

SCRIPTS = {
    "kiem_tra_ha_tang": Path(
        "code/hung/src/storage/"
        "check_infrastructure.py"
    ),
    "crawl_nha_hang": Path(
        "code/hung/src/ingestion/"
        "foody-shoppefood/"
        "foody_restaurant_crawler.py"
    ),
    "crawl_review": Path(
        "code/hung/src/ingestion/"
        "foody-shoppefood/"
        "foody_review_crawler.py"
    ),
    "upload_minio": Path(
        "code/hung/src/storage/"
        "minio_uploader.py"
    ),
    "minio_sang_postgres": Path(
        "code/hung/src/processing/"
        "minio_to_postgres.py"
    ),
}


def chay_script(
    ten_buoc,
    script_path,
    tham_so,
):
    full_path = (
        ROOT
        / script_path
    )

    if not full_path.exists():
        raise FileNotFoundError(
            "Không tìm thấy script: "
            f"{full_path}"
        )

    command = [
        sys.executable,
        str(script_path),
        *tham_so,
    ]

    print(
        "\n"
        + "=" * 70
    )
    print(
        f"BẮT ĐẦU: {ten_buoc}"
    )
    print(
        "LỆNH:",
        " ".join(
            command
        ),
    )
    print(
        "=" * 70
    )

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{ten_buoc} thất bại "
            f"với mã thoát "
            f"{result.returncode}"
        )

    print(
        f"HOÀN THÀNH: {ten_buoc}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline Foody: "
            "Web -> Local -> MinIO -> PostgreSQL. "
            "Mặc định crawl incremental."
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "full",
            "limit",
        ],
        default="full",
        help=(
            "full = không giới hạn số lượng; "
            "limit = giới hạn để test. "
            "Cả hai đều incremental mặc định."
        ),
    )

    parser.add_argument(
        "--max-restaurants-per-city",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--max-reviews",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--city",
        default=None,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=(
            "Đặt cùng số worker cho "
            "crawl/upload/database."
        ),
    )

    parser.add_argument(
        "--crawl-workers",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--upload-workers",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--db-workers",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--page-delay",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Tiếp tục cùng một lần chạy "
            "bị gián đoạn. Không dùng cho "
            "lần crawl định kỳ mới."
        ),
    )

    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help=(
            "Bỏ incremental checkpoint và "
            "vét lại toàn bộ review từ Foody."
        ),
    )

    parser.add_argument(
        "--db-dry-run",
        action="store_true",
    )

    parser.add_argument(
        "--skip-restaurant-crawl",
        action="store_true",
    )

    parser.add_argument(
        "--skip-review-crawl",
        action="store_true",
    )

    parser.add_argument(
        "--skip-minio-upload",
        action="store_true",
    )

    parser.add_argument(
        "--skip-db-load",
        action="store_true",
    )

    return parser.parse_args()


def resolve_workers(
    args,
):
    common = args.workers

    crawl = (
        args.crawl_workers
        if args.crawl_workers
        is not None
        else (
            common
            if common is not None
            else 50
        )
    )

    upload = (
        args.upload_workers
        if args.upload_workers
        is not None
        else (
            common
            if common is not None
            else 50
        )
    )

    db = (
        args.db_workers
        if args.db_workers
        is not None
        else (
            common
            if common is not None
            else 8
        )
    )

    return (
        crawl,
        upload,
        db,
    )


def validate_args(
    args,
    crawl_workers,
    upload_workers,
    db_workers,
):
    for name, value in (
        (
            "crawl-workers",
            crawl_workers,
        ),
        (
            "upload-workers",
            upload_workers,
        ),
        (
            "db-workers",
            db_workers,
        ),
    ):
        if value < 1:
            raise ValueError(
                f"--{name} phải >= 1"
            )

    if (
        args.workers is not None
        and args.workers < 1
    ):
        raise ValueError(
            "--workers phải >= 1"
        )

    if args.page_delay < 0:
        raise ValueError(
            "--page-delay phải >= 0"
        )

    if (
        args.resume
        and args.full_refresh
    ):
        raise ValueError(
            "Không dùng --resume và "
            "--full-refresh cùng lúc."
        )

    if args.mode == "limit":
        if (
            args.max_restaurants_per_city
            is None
            or args.max_restaurants_per_city
            <= 0
        ):
            raise ValueError(
                "--mode limit cần "
                "--max-restaurants-per-city > 0"
            )

        if (
            args.max_reviews
            is None
            or args.max_reviews <= 0
        ):
            raise ValueError(
                "--mode limit cần "
                "--max-reviews > 0"
            )


def main():
    args = parse_args()

    (
        crawl_workers,
        upload_workers,
        db_workers,
    ) = resolve_workers(
        args
    )

    validate_args(
        args,
        crawl_workers,
        upload_workers,
        db_workers,
    )

    if args.full_refresh:
        crawl_mode = (
            "FULL REFRESH"
        )
    elif args.resume:
        crawl_mode = (
            "RESUME"
        )
    else:
        crawl_mode = (
            "INCREMENTAL"
        )

    print(
        "PIPELINE FOODY"
    )
    print(
        "Luồng: Web -> Local "
        "-> MinIO -> PostgreSQL"
    )
    print(
        "Crawl mode:",
        crawl_mode,
    )
    print(
        "Giới hạn:",
        args.mode,
    )
    print(
        "Thành phố:",
        args.city
        or "TẤT CẢ",
    )
    print(
        "Worker crawl:",
        crawl_workers,
    )
    print(
        "Worker upload:",
        upload_workers,
    )
    print(
        "Worker database:",
        db_workers,
    )

    try:
        # Runtime pipeline chỉ kiểm tra.
        # Không tạo bucket/database/schema.
        chay_script(
            "0. Kiểm tra hạ tầng",
            SCRIPTS[
                "kiem_tra_ha_tang"
            ],
            [],
        )

        if (
            not args
            .skip_restaurant_crawl
        ):
            restaurant_args = [
                "--workers",
                str(
                    crawl_workers
                ),
            ]

            if args.city:
                restaurant_args.extend([
                    "--city",
                    args.city,
                ])

            if args.mode == "limit":
                restaurant_args.extend([
                    "--max-restaurants",
                    str(
                        args
                        .max_restaurants_per_city
                    ),
                ])

            chay_script(
                "1. Web -> Local: "
                "crawl nhà hàng",
                SCRIPTS[
                    "crawl_nha_hang"
                ],
                restaurant_args,
            )

        if (
            not args
            .skip_review_crawl
        ):
            review_args = [
                "--workers",
                str(
                    crawl_workers
                ),
                "--page-delay",
                str(
                    args.page_delay
                ),
            ]

            if args.city:
                review_args.extend([
                    "--city",
                    args.city,
                ])

            if args.mode == "limit":
                review_args.extend([
                    "--max-restaurants-per-city",
                    str(
                        args
                        .max_restaurants_per_city
                    ),
                    "--max-reviews",
                    str(
                        args.max_reviews
                    ),
                ])

            if args.resume:
                review_args.append(
                    "--resume"
                )

            if args.full_refresh:
                review_args.append(
                    "--full-refresh"
                )

            chay_script(
                "2. Web -> Local: "
                "crawl review incremental",
                SCRIPTS[
                    "crawl_review"
                ],
                review_args,
            )

        if (
            not args
            .skip_minio_upload
        ):
            upload_args = [
                "--source",
                "foody",
                "--workers",
                str(
                    upload_workers
                ),

                # Luôn đồng bộ raw local mới nhất
                # lên đúng object key.
                "--overwrite",
            ]

            if args.city:
                upload_args.extend([
                    "--city",
                    args.city,
                ])

            chay_script(
                "3. Local -> MinIO",
                SCRIPTS[
                    "upload_minio"
                ],
                upload_args,
            )

        if (
            not args
            .skip_db_load
        ):
            db_args = [
                "--source",
                "foody",
                "--workers",
                str(
                    db_workers
                ),
            ]

            if args.city:
                db_args.extend([
                    "--city",
                    args.city,
                ])

            if args.db_dry_run:
                db_args.append(
                    "--dry-run"
                )

            chay_script(
                "4. MinIO -> PostgreSQL",
                SCRIPTS[
                    "minio_sang_postgres"
                ],
                db_args,
            )

    except Exception as exc:
        print(
            "\nPIPELINE THẤT BẠI:",
            exc,
        )
        sys.exit(1)

    print(
        "\n"
        + "=" * 70
    )
    print(
        "PIPELINE HOÀN THÀNH"
    )
    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()
