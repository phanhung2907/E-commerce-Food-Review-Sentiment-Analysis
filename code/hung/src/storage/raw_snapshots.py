"""MinIO snapshots; content addressing works even when bucket versioning is off."""

import io
import json

from storage.data_versioning import parse_raw_key, sha256_bytes, snapshot_key, validate_identity
from storage.minio_client import MINIO_BUCKET, get_thread_minio_client


def read_bytes(client, key):
    response = client.get_object(MINIO_BUCKET, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def optional_bytes(client, key):
    try:
        return read_bytes(client, key)
    except Exception as exc:
        if getattr(exc, "code", None) in {"NoSuchKey", "NoSuchObject"}:
            return None
        raise


def ensure_snapshot(client, key, data):
    digest = sha256_bytes(data)
    try:
        stat = client.stat_object(MINIO_BUCKET, key)
    except Exception as exc:
        if getattr(exc, "code", None) not in {"NoSuchKey", "NoSuchObject"}:
            raise
    else:
        # Verify existing bytes too: a snapshot edited outside this application must fail.
        if stat.size != len(data) or sha256_bytes(read_bytes(client, key)) != digest:
            raise ValueError(f"Snapshot checksum mismatch: {key}")
        return
    client.put_object(MINIO_BUCKET, key, io.BytesIO(data), len(data),
                      content_type="application/json", metadata={"sha256": digest})


def freeze_object(source, key, expected_sha256=None, *, client=None, persist=True):
    client = client or get_thread_minio_client()
    city, restaurant_id, key_digest = parse_raw_key(key, source)
    data = read_bytes(client, key)
    digest = sha256_bytes(data)
    if (key_digest and key_digest != digest) or (expected_sha256 and expected_sha256 != digest):
        raise ValueError(f"SHA-256 mismatch: {key}")
    raw = json.loads(data.decode("utf-8"))
    validate_identity(raw, source, city, restaurant_id)
    immutable_key = snapshot_key(source, city, restaurant_id, digest)
    if persist and key != immutable_key:
        ensure_snapshot(client, immutable_key, data)
    return raw, {"object_name": immutable_key, "sha256": digest, "size_bytes": len(data)}
