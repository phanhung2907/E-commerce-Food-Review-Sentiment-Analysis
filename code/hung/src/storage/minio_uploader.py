import os
import mimetypes

from pathlib import Path

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

PLATFORM_NAME = (
    "foody_shoppefood"
)

LOCAL_DATA_ROOT = Path(
    "code/hung/data"
) / PLATFORM_NAME

MINIO_ENDPOINT = (
    os.getenv(
        "MINIO_ENDPOINT",
        "localhost:9000",
    )
)

MINIO_ACCESS_KEY = (
    os.getenv(
        "MINIO_ACCESS_KEY",
        "minioadmin",
    )
)

MINIO_SECRET_KEY = (
    os.getenv(
        "MINIO_SECRET_KEY",
        "minioadmin",
    )
)

MINIO_BUCKET = (
    os.getenv(
        "MINIO_BUCKET",
        "food-review-data",
    )
)

MINIO_SECURE = (
    os.getenv(
        "MINIO_SECURE",
        "false",
    )
    .lower()
    == "true"
)


# =========================================================
# CLIENT
# =========================================================

def create_client():

    return Minio(
        endpoint=(
            MINIO_ENDPOINT
        ),

        access_key=(
            MINIO_ACCESS_KEY
        ),

        secret_key=(
            MINIO_SECRET_KEY
        ),

        secure=(
            MINIO_SECURE
        ),
    )


# =========================================================
# BUCKET
# =========================================================

def ensure_bucket(
    client
):
    if client.bucket_exists(
        MINIO_BUCKET
    ):

        print(
            "Bucket exists:",
            MINIO_BUCKET
        )

        return

    client.make_bucket(
        MINIO_BUCKET
    )

    print(
        "Created bucket:",
        MINIO_BUCKET
    )


# =========================================================
# FIND FILES
# =========================================================

def find_files():
    """
    Upload tất cả file trong:

    code/hung/data/
        foody_shoppefood/
    """

    if not LOCAL_DATA_ROOT.exists():

        raise FileNotFoundError(
            f"Không tồn tại: "
            f"{LOCAL_DATA_ROOT}"
        )

    return sorted(
        path
        for path
        in LOCAL_DATA_ROOT.rglob(
            "*"
        )
        if path.is_file()
    )


# =========================================================
# OBJECT NAME
# =========================================================

def build_object_name(
    file_path
):
    """
    Local:

    code/hung/data/
        foody_shoppefood/
        raw/
        gia-lai/
        restaurants.csv

    MinIO:

    foody_shoppefood/
        raw/
        gia-lai/
        restaurants.csv
    """

    relative_path = (
        file_path
        .relative_to(
            LOCAL_DATA_ROOT
        )
    )

    object_path = (
        Path(
            PLATFORM_NAME
        )
        / relative_path
    )

    return (
        object_path
        .as_posix()
    )


# =========================================================
# CONTENT TYPE
# =========================================================

def get_content_type(
    file_path
):
    content_type, _ = (
        mimetypes.guess_type(
            str(file_path)
        )
    )

    return (
        content_type
        or "application/octet-stream"
    )


# =========================================================
# OBJECT EXISTS
# =========================================================

def object_exists(
    client,
    object_name,
):
    try:

        client.stat_object(
            MINIO_BUCKET,
            object_name,
        )

        return True

    except S3Error as e:

        if e.code in (
            "NoSuchKey",
            "NoSuchObject",
        ):

            return False

        raise


# =========================================================
# UPLOAD FILE
# =========================================================

def upload_file(
    client,
    file_path,
):
    object_name = (
        build_object_name(
            file_path
        )
    )

    content_type = (
        get_content_type(
            file_path
        )
    )

    client.fput_object(
        bucket_name=(
            MINIO_BUCKET
        ),

        object_name=(
            object_name
        ),

        file_path=str(
            file_path
        ),

        content_type=(
            content_type
        ),
    )

    print(
        "Uploaded:",
        object_name
    )


# =========================================================
# UPLOAD ALL
# =========================================================

def upload_all(
    client
):
    files = (
        find_files()
    )

    print(
        "Files found:",
        len(files)
    )

    uploaded = 0
    skipped = 0
    failed = 0

    for file_path in files:

        object_name = (
            build_object_name(
                file_path
            )
        )

        try:

            if object_exists(
                client,
                object_name,
            ):

                print(
                    "Skip existing:",
                    object_name
                )

                skipped += 1

                continue

            upload_file(
                client,
                file_path,
            )

            uploaded += 1

        except Exception as e:

            print(
                "FAILED:",
                file_path
            )

            print(
                e
            )

            failed += 1

    print(
        "\n=============================="
    )

    print(
        "UPLOAD SUMMARY"
    )

    print(
        "=============================="
    )

    print(
        "Uploaded:",
        uploaded
    )

    print(
        "Skipped:",
        skipped
    )

    print(
        "Failed:",
        failed
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "\n=============================="
    )

    print(
        "MINIO UPLOADER"
    )

    print(
        "=============================="
    )

    print(
        "Endpoint:",
        MINIO_ENDPOINT
    )

    print(
        "Bucket:",
        MINIO_BUCKET
    )

    client = (
        create_client()
    )

    ensure_bucket(
        client
    )

    upload_all(
        client
    )


if __name__ == "__main__":
    main()