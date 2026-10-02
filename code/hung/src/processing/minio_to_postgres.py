import argparse
import sys
import threading

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from pathlib import Path


# =========================================================
# IMPORT PATH
# =========================================================

SRC_ROOT = Path(__file__).resolve().parents[1]

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_ROOT),
    )


from processing.foody_transform import (  # noqa: E402
    transform_foody_object,
)

from storage.minio_client import (  # noqa: E402
    create_minio_client,
    require_bucket,
    list_object_names,
    read_json_object,
)

from storage.postgres_client import (  # noqa: E402
    get_thread_postgres_connection,
)

from storage.postgres_repository import (  # noqa: E402
    load_transformed_object,
)

from utils.source_codes import (  # noqa: E402
    validate_source_code,
)


# =========================================================
# CONFIG
# =========================================================

DEFAULT_WORKERS = 8

TRANSFORMERS = {
    "foody": transform_foody_object,
}

_print_lock = threading.Lock()


# =========================================================
# LOGGING
# =========================================================

def log(*args):
    with _print_lock:
        print(
            *args,
            flush=True,
        )


# =========================================================
# MINIO OBJECT DISCOVERY
# =========================================================

def find_restaurant_objects(
    source_code: str,
    city: str | None = None,
    limit: int | None = None,
):
    """
    Tìm restaurant.json trong MinIO.

    Điểm khác bản cũ:
    - log ngay khi bắt đầu
    - limit được áp dụng ngay trong lúc list
    - không cần list toàn bucket rồi mới cắt
    - có progress log
    """

    client = create_minio_client()

    prefix = f"{source_code}/raw/"

    if city:
        prefix += f"{city}/"

    log(
        f"[MINIO] Listing objects "
        f"| prefix={prefix}"
    )

    objects = []
    scanned = 0

    for object_name in list_object_names(
        prefix=prefix,
        client=client,
    ):
        scanned += 1

        if scanned % 500 == 0:
            log(
                f"[MINIO] scanned={scanned} "
                f"| matched={len(objects)}"
            )

        if not object_name.endswith(
            "/restaurant.json"
        ):
            continue

        objects.append(
            object_name
        )

        if (
            limit is not None
            and len(objects) >= limit
        ):
            log(
                f"[MINIO] Limit reached "
                f"| limit={limit}"
            )
            break

    log(
        f"[MINIO] Listing done "
        f"| scanned={scanned} "
        f"| objects={len(objects)}"
    )

    return objects


# =========================================================
# PROCESS ONE OBJECT
# =========================================================

def process_one_object(
    source_code: str,
    object_name: str,
    dry_run: bool,
):
    """
    1 object MinIO:
        read raw
        -> transform
        -> PostgreSQL
    """

    raw = read_json_object(
        object_name
    )

    transformer = TRANSFORMERS[
        source_code
    ]

    transformed = transformer(
        raw,
        object_name,
    )

    reviews_found = len(
        transformed.get(
            "reviews",
            [],
        )
    )

    if dry_run:
        return {
            "object_name":
                object_name,
            "inserted_reviews":
                0,
            "existing_reviews":
                0,
            "reviews_found":
                reviews_found,
            "dry_run":
                True,
        }

    conn = (
        get_thread_postgres_connection()
    )

    try:
        stats = (
            load_transformed_object(
                conn,
                transformed,
            )
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    return {
        "object_name":
            object_name,
        "reviews_found":
            reviews_found,
        **stats,
        "dry_run":
            False,
    }


# =========================================================
# CLI
# =========================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "ETL: MinIO raw -> PostgreSQL 3NF"
        )
    )

    parser.add_argument(
        "--source",
        default="foody",
        help=(
            "Canonical source label. "
            "Default=foody."
        ),
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            "Số restaurant objects "
            "process song song. "
            f"Default={DEFAULT_WORKERS}."
        ),
    )

    parser.add_argument(
        "--city",
        default=None,
        help=(
            "Chỉ import một city slug."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Giới hạn số MinIO objects "
            "để test."
        ),
    )

    parser.add_argument(
        "--object-key",
        default=None,
        help=(
            "Chỉ process đúng một "
            "MinIO object key."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Đọc + transform nhưng "
            "không ghi PostgreSQL."
        ),
    )

    return parser.parse_args()


# =========================================================
# MAIN
# =========================================================

def main():
    args = parse_args()

    source_code = validate_source_code(
        args.source
    )

    if source_code not in TRANSFORMERS:
        raise NotImplementedError(
            "Chưa có transformer cho "
            f"source={source_code}"
        )

    if args.workers < 1:
        raise ValueError(
            "--workers phải >= 1"
        )

    if (
        args.limit is not None
        and args.limit <= 0
    ):
        raise ValueError(
            "--limit phải > 0"
        )

    log(
        "\n================================"
    )
    log(
        "MINIO -> POSTGRESQL"
    )
    log(
        "================================"
    )

    log(
        f"Source: {source_code}"
    )
    log(
        f"Workers: {args.workers}"
    )
    log(
        f"Dry run: {args.dry_run}"
    )

    if args.city:
        log(
            f"City: {args.city}"
        )

    if args.limit:
        log(
            f"Limit: {args.limit}"
        )

    # -----------------------------------------------------
    # STEP 1: CHECK MINIO
    # -----------------------------------------------------

    log(
        "\n[1/3] Checking MinIO bucket..."
    )

    require_bucket()

    log(
        "[1/3] MinIO bucket OK"
    )

    # -----------------------------------------------------
    # STEP 2: DISCOVER OBJECTS
    # -----------------------------------------------------

    if args.object_key:
        objects = [
            args.object_key
        ]

        log(
            "\n[2/3] Using single object:"
        )
        log(
            args.object_key
        )

    else:
        log(
            "\n[2/3] Finding restaurant objects..."
        )

        objects = (
            find_restaurant_objects(
                source_code=source_code,
                city=args.city,
                limit=args.limit,
            )
        )

    if not objects:
        log(
            "\nKhông tìm thấy restaurant.json "
            "phù hợp trong MinIO."
        )
        return

    log(
        f"\n[2/3] Found {len(objects)} objects"
    )

    # -----------------------------------------------------
    # STEP 3: PROCESS OBJECTS
    # -----------------------------------------------------

    log(
        "\n[3/3] Starting processing..."
    )

    inserted_reviews = 0
    existing_reviews = 0
    failed = 0
    total_reviews_found = 0

    with ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:

        futures = {
            executor.submit(
                process_one_object,
                source_code,
                object_name,
                args.dry_run,
            ): object_name

            for object_name
            in objects
        }

        for index, future in enumerate(
            as_completed(
                futures
            ),
            start=1,
        ):
            object_name = (
                futures[
                    future
                ]
            )

            try:
                stats = (
                    future.result()
                )

                reviews_found = (
                    stats.get(
                        "reviews_found",
                        0,
                    )
                )

                total_reviews_found += (
                    reviews_found
                )

                inserted_reviews += (
                    stats.get(
                        "inserted_reviews",
                        0,
                    )
                )

                existing_reviews += (
                    stats.get(
                        "existing_reviews",
                        0,
                    )
                )

                if args.dry_run:
                    log(
                        f"[{index}/"
                        f"{len(objects)}] "
                        f"VALID "
                        f"{object_name} "
                        f"| reviews="
                        f"{reviews_found}"
                    )

                else:
                    log(
                        f"[{index}/"
                        f"{len(objects)}] "
                        f"LOADED "
                        f"{object_name} "
                        f"| reviews="
                        f"{reviews_found} "
                        f"| new="
                        f"{stats.get('inserted_reviews', 0)} "
                        f"| existed="
                        f"{stats.get('existing_reviews', 0)}"
                    )

            except Exception as exc:
                failed += 1

                log(
                    f"[{index}/"
                    f"{len(objects)}] "
                    f"FAILED "
                    f"{object_name} "
                    f"| {type(exc).__name__}: "
                    f"{exc}"
                )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    log(
        "\n================================"
    )
    log(
        "IMPORT SUMMARY"
    )
    log(
        "================================"
    )

    log(
        "Objects processed:",
        len(objects),
    )

    log(
        "Reviews found:",
        total_reviews_found,
    )

    log(
        "New reviews:",
        inserted_reviews,
    )

    log(
        "Existing reviews skipped:",
        existing_reviews,
    )

    log(
        "Failed objects:",
        failed,
    )


if __name__ == "__main__":
    main()
