import argparse
import mimetypes
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

from storage.minio_client import (  # noqa: E402
    MINIO_BUCKET,
    create_minio_client,
    require_bucket,
    get_thread_minio_client,
    list_object_names,
)
from utils.source_codes import (  # noqa: E402
    validate_source_code,
)


DEFAULT_WORKERS = 50
DEFAULT_LOCAL_ROOT = Path(
    "code/hung/data/"
    "foody_shoppefood/raw"
)

_print_lock = threading.Lock()


def log(*args):
    with _print_lock:
        print(*args, flush=True)


def find_restaurant_files(
    local_root: Path,
    city: str | None = None,
):
    """
    Expected local schema:

    <local_root>/
        <city>/
            <restaurant_id>/
                restaurant.json
    """
    if not local_root.exists():
        raise FileNotFoundError(
            f"Không tồn tại: {local_root}"
        )

    if city:
        search_root = (
            local_root
            / city
        )
        pattern = (
            "*/restaurant.json"
        )
    else:
        search_root = local_root
        pattern = (
            "*/*/restaurant.json"
        )

    if not search_root.exists():
        return []

    return sorted(
        path
        for path
        in search_root.glob(pattern)
        if path.is_file()
    )


def validate_local_file(
    file_path: Path,
    local_root: Path,
) -> tuple[str, str]:
    relative = (
        file_path
        .relative_to(local_root)
    )

    parts = relative.parts

    if (
        len(parts) != 3
        or parts[2]
        != "restaurant.json"
    ):
        raise ValueError(
            "Sai MinIO local schema: "
            f"{relative}. "
            "Expected "
            "<city>/<restaurant_id>/"
            "restaurant.json"
        )

    city = parts[0]
    restaurant_id = parts[1]

    return city, restaurant_id


def build_object_name(
    source_code: str,
    file_path: Path,
    local_root: Path,
) -> str:
    city, restaurant_id = (
        validate_local_file(
            file_path,
            local_root,
        )
    )

    return (
        f"{source_code}/raw/"
        f"{city}/"
        f"{restaurant_id}/"
        "restaurant.json"
    )


def get_content_type(
    file_path: Path,
) -> str:
    content_type, _ = (
        mimetypes.guess_type(
            str(file_path)
        )
    )

    return (
        content_type
        or "application/json"
    )


def upload_one(
    source_code: str,
    file_path: Path,
    local_root: Path,
):
    client = (
        get_thread_minio_client()
    )

    object_name = build_object_name(
        source_code,
        file_path,
        local_root,
    )

    client.fput_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_name,
        file_path=str(file_path),
        content_type=(
            get_content_type(
                file_path
            )
        ),
    )

    return object_name


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Upload raw restaurant objects "
            "theo MinIO schema chuẩn"
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
        "--local-root",
        type=Path,
        default=DEFAULT_LOCAL_ROOT,
        help=(
            "Folder raw local chứa "
            "<city>/<restaurant_id>/"
            "restaurant.json"
        ),
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            f"Số upload song song. "
            f"Default={DEFAULT_WORKERS}."
        ),
    )

    parser.add_argument(
        "--city",
        default=None,
        help=(
            "Chỉ upload một city slug."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Giới hạn số object để test."
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Upload đè object đã có trên "
            "MinIO. Mặc định sẽ skip."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    source_code = validate_source_code(
        args.source
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

    files = find_restaurant_files(
        args.local_root,
        args.city,
    )

    if args.limit is not None:
        files = files[
            :args.limit
        ]

    client = create_minio_client()
    require_bucket(client)

    existing = set()

    if not args.overwrite:
        prefix = (
            f"{source_code}/raw/"
        )

        if args.city:
            prefix += (
                f"{args.city}/"
            )

        existing = set(
            list_object_names(
                prefix=prefix,
                client=client,
            )
        )

    jobs = []

    for file_path in files:
        object_name = (
            build_object_name(
                source_code,
                file_path,
                args.local_root,
            )
        )

        if (
            not args.overwrite
            and object_name
            in existing
        ):
            continue

        jobs.append(file_path)

    skipped = (
        len(files)
        - len(jobs)
    )

    print(
        "Source:",
        source_code,
    )
    print(
        "Local files:",
        len(files),
    )
    print(
        "Need upload:",
        len(jobs),
    )
    print(
        "Skip existing:",
        skipped,
    )
    print(
        "Workers:",
        args.workers,
    )

    uploaded = 0
    failed = 0

    with ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:
        futures = {
            executor.submit(
                upload_one,
                source_code,
                file_path,
                args.local_root,
            ): file_path
            for file_path in jobs
        }

        for index, future in enumerate(
            as_completed(futures),
            start=1,
        ):
            file_path = futures[future]

            try:
                object_name = (
                    future.result()
                )
                uploaded += 1

                log(
                    f"[{index}/{len(jobs)}] "
                    f"Uploaded: "
                    f"{object_name}"
                )

            except Exception as e:
                failed += 1

                log(
                    f"[{index}/{len(jobs)}] "
                    f"FAILED: "
                    f"{file_path} | {e}"
                )

    print(
        "\nUPLOAD SUMMARY"
    )
    print(
        "Uploaded:",
        uploaded,
    )
    print(
        "Skipped:",
        skipped,
    )
    print(
        "Failed:",
        failed,
    )


if __name__ == "__main__":
    main()
