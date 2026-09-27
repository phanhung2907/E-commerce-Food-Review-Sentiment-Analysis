import json
import os
import threading

from dotenv import load_dotenv
from minio import Minio


load_dotenv()

MINIO_ENDPOINT = os.getenv(
    "MINIO_ENDPOINT",
    "localhost:9000",
)

MINIO_ACCESS_KEY = os.getenv(
    "MINIO_ACCESS_KEY",
    "minioadmin",
)

MINIO_SECRET_KEY = os.getenv(
    "MINIO_SECRET_KEY",
    "minioadmin",
)

MINIO_BUCKET = os.getenv(
    "MINIO_BUCKET",
    "food-review-data",
)

MINIO_SECURE = (
    os.getenv(
        "MINIO_SECURE",
        "false",
    ).lower()
    == "true"
)

_thread_local = threading.local()


def create_minio_client() -> Minio:
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def get_thread_minio_client() -> Minio:
    client = getattr(
        _thread_local,
        "client",
        None,
    )

    if client is None:
        client = create_minio_client()
        _thread_local.client = client

    return client


def require_bucket(
    client: Minio | None = None,
) -> None:
    """
    Runtime check only.
    NEVER creates infrastructure.
    """
    client = client or create_minio_client()

    if not client.bucket_exists(
        MINIO_BUCKET
    ):
        raise RuntimeError(
            "MinIO bucket chưa tồn tại: "
            f"{MINIO_BUCKET}. "
            "Hãy chạy setup_minio.py một lần "
            "trước khi chạy pipeline."
        )


def create_bucket_if_missing(
    client: Minio | None = None,
) -> bool:
    """
    Setup-only helper.
    Returns True if a bucket was created.
    """
    client = client or create_minio_client()

    if client.bucket_exists(
        MINIO_BUCKET
    ):
        return False

    client.make_bucket(
        MINIO_BUCKET
    )
    return True


def read_json_object(
    object_name: str,
    client: Minio | None = None,
) -> dict:
    client = (
        client
        or get_thread_minio_client()
    )

    response = client.get_object(
        MINIO_BUCKET,
        object_name,
    )

    try:
        raw = response.read()
        return json.loads(
            raw.decode("utf-8")
        )
    finally:
        response.close()
        response.release_conn()


def list_object_names(
    prefix: str,
    client: Minio | None = None,
):
    client = client or create_minio_client()

    for obj in client.list_objects(
        MINIO_BUCKET,
        prefix=prefix,
        recursive=True,
    ):
        if not obj.is_dir:
            yield obj.object_name



def object_exists(
    object_name: str,
    client: Minio | None = None,
) -> bool:
    """
    Kiểm tra object có tồn tại hay không.
    Không tạo object/bucket.
    """
    client = client or create_minio_client()

    try:
        client.stat_object(
            MINIO_BUCKET,
            object_name,
        )
        return True

    except Exception as exc:
        code = getattr(
            exc,
            "code",
            None,
        )

        if code in {
            "NoSuchKey",
            "NoSuchObject",
            "NoSuchBucket",
        }:
            return False

        raise
