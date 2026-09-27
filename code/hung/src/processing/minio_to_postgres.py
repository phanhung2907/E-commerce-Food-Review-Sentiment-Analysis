import argparse
import sys
import threading

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from pathlib import Path


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


DEFAULT_WORKERS = 8

TRANSFORMERS = {
    "foody":
        transform_foody_object,
}

_print_lock = threading.Lock()


def log(*args):
    with _print_lock:
        print(*args, flush=True)


def find_restaurant_objects(
    source_code: str,
    city: str | None = None,
):
    client = create_minio_client()

    prefix = (
        f"{source_code}/raw/"
    )

    if city:
        prefix += f"{city}/"

    objects = []

    for object_name in (
        list_object_names(
            prefix=prefix,
            client=client,
        )
    ):
        if object_name.endswith(
            "/restaurant.json"
        ):
            objects.append(
                object_name
            )

    return sorted(objects)


def process_one_object(
    source_code: str,
    object_name: str,
    dry_run: bool,
):
    raw = read_json_object(
        object_name
    )

    transformer = (
        TRANSFORMERS[
            source_code
        ]
    )

    transformed = transformer(
        raw,
        object_name,
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
                len(
                    transformed[
                        "reviews"
                    ]
                ),
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
            len(
                transformed[
                    "reviews"
                ]
            ),
        **stats,
        "dry_run":
            False,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "ETL: MinIO raw -> "
            "PostgreSQL 3NF"
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


def main():
    args = parse_args()

    source_code = validate_source_code(
        args.source
    )

    if (
        source_code
        not in TRANSFORMERS
    ):
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

    require_bucket()

    if args.object_key:
        objects = [
            args.object_key
        ]
    else:
        objects = (
            find_restaurant_objects(
                source_code,
                args.city,
            )
        )

    if args.limit is not None:
        objects = objects[
            :args.limit
        ]

    print(
        "Source:",
        source_code,
    )
    print(
        "Objects:",
        len(objects),
    )
    print(
        "Workers:",
        args.workers,
    )
    print(
        "Dry run:",
        args.dry_run,
    )

    inserted_reviews = 0
    existing_reviews = 0
    failed = 0

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
            for object_name in objects
        }

        for index, future in enumerate(
            as_completed(futures),
            start=1,
        ):
            object_name = futures[
                future
            ]

            try:
                stats = future.result()

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
                        f"{stats['reviews_found']}"
                    )
                else:
                    log(
                        f"[{index}/"
                        f"{len(objects)}] "
                        f"LOADED "
                        f"{object_name} "
                        f"| new="
                        f"{stats['inserted_reviews']} "
                        f"| existed="
                        f"{stats['existing_reviews']}"
                    )

            except Exception as e:
                failed += 1

                log(
                    f"[{index}/"
                    f"{len(objects)}] "
                    f"FAILED "
                    f"{object_name} | {e}"
                )

    print(
        "\nIMPORT SUMMARY"
    )
    print(
        "New reviews:",
        inserted_reviews,
    )
    print(
        "Existing reviews skipped:",
        existing_reviews,
    )
    print(
        "Failed objects:",
        failed,
    )


if __name__ == "__main__":
    main()
