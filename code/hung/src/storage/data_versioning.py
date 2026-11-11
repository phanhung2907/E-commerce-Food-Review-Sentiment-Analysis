"""Byte-preserving raw snapshots. No infrastructure or network side effects here."""

import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_SCHEMA_VERSION = 1
TRANSFORM_VERSION = "foody-etl-v2"
_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def safe_component(value):
    value = str(value)
    if not _COMPONENT.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"Invalid path component: {value!r}")
    return value


def new_run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ-") + uuid.uuid4().hex[:12]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def snapshot_key(source, city, restaurant_id, digest):
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid SHA-256")
    return "/".join((safe_component(source), "raw_versions", safe_component(city),
                     safe_component(restaurant_id), digest, "restaurant.json"))


def parse_raw_key(key, source):
    parts = key.split("/")
    if len(parts) not in (5, 6) or parts[0] != source or parts[-1] != "restaurant.json":
        raise ValueError(f"Invalid restaurant object key: {key}")
    if (len(parts) == 5 and parts[1] != "raw") or (len(parts) == 6 and parts[1] != "raw_versions"):
        raise ValueError(f"Invalid raw prefix: {key}")
    city, restaurant_id = map(safe_component, parts[2:4])
    digest = parts[4] if len(parts) == 6 else None
    if digest and not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid SHA-256 in object key")
    return city, restaurant_id, digest


def validate_identity(raw, source, city, restaurant_id):
    if not isinstance(raw, dict):
        raise ValueError("Raw object must be a JSON object")
    if raw.get("source", source) != source:
        raise ValueError("Raw source does not match object path")
    restaurant = raw.get("restaurant") or {}
    raw_id = next((restaurant.get(k) for k in ("restaurant_id", "ResId", "Id")
                   if restaurant.get(k) is not None), None)
    if str(raw_id).strip() != str(restaurant_id):
        raise ValueError("Raw restaurant ID does not match object path")
    if restaurant.get("city") and restaurant["city"] != city:
        raise ValueError("Raw city does not match object path")


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_immutable(path, data):
    """Atomic publication; an existing different value is always an error."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Immutable file has different content: {path}")
        return
    fd, temporary = tempfile.mkstemp(prefix="snapshot-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        try:
            # Windows rename refuses an existing destination; POSIX rename replaces it.
            if os.name == "nt":
                os.rename(temporary, path)
            else:
                os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError(f"Immutable file conflict: {path}")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def local_version_root(local_root):
    return Path(local_root).parent / (Path(local_root).name + "_versions")


def archive_local_bytes(local_root, city, restaurant_id, data):
    digest = sha256_bytes(data)
    path = local_version_root(local_root) / safe_component(city) / safe_component(restaurant_id) / digest / "restaurant.json"
    write_immutable(path, data)
    return path


def save_local_snapshot(output_path, raw, local_root):
    output_path, local_root = Path(output_path), Path(local_root)
    relative = output_path.relative_to(local_root)
    if len(relative.parts) != 3 or relative.name != "restaurant.json":
        raise ValueError("Expected <city>/<restaurant_id>/restaurant.json")
    city, restaurant_id = relative.parts[:2]
    validate_identity(raw, "foody", city, restaurant_id)
    data = json_bytes(raw)
    # Protect both the pre-upgrade current file and the new snapshot BEFORE replacement.
    if output_path.exists():
        archive_local_bytes(local_root, city, restaurant_id, output_path.read_bytes())
    archive_local_bytes(local_root, city, restaurant_id, data)
    atomic_write(output_path, data)
    return output_path


def transform_fingerprint():
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for relative in ("processing/foody_transform.py", "storage/postgres_repository.py"):
        digest.update(relative.encode("utf-8"))
        digest.update((root / relative).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()
