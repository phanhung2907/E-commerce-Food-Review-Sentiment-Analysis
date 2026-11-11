import argparse
import io
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from storage.data_versioning import (MANIFEST_SCHEMA_VERSION, archive_local_bytes,
    json_bytes, local_version_root, new_run_id, safe_component, sha256_bytes,
    snapshot_key, validate_identity, write_immutable)
from storage.minio_client import MINIO_BUCKET, create_minio_client, get_thread_minio_client, require_bucket
from storage.raw_snapshots import ensure_snapshot, optional_bytes
from utils.source_codes import validate_source_code

DEFAULT_WORKERS = 50
DEFAULT_LOCAL_ROOT = Path("code/hung/data/foody_shoppefood/raw")


def find_restaurant_files(local_root, city=None):
    local_root = Path(local_root)
    if not local_root.exists():
        raise FileNotFoundError(local_root)
    search_root = local_root / safe_component(city) if city else local_root
    return sorted(search_root.glob("*/restaurant.json" if city else "*/*/restaurant.json"))


def validate_local_file(file_path, local_root):
    parts = Path(file_path).relative_to(local_root).parts
    if len(parts) != 3 or parts[-1] != "restaurant.json":
        raise ValueError("Expected <city>/<restaurant_id>/restaurant.json")
    return safe_component(parts[0]), safe_component(parts[1])


def build_object_name(source_code, file_path, local_root):
    city, restaurant_id = validate_local_file(file_path, local_root)
    return f"{source_code}/raw/{city}/{restaurant_id}/restaurant.json"


def upload_one(source_code, file_path, local_root, overwrite=False):
    client = get_thread_minio_client()
    city, restaurant_id = validate_local_file(file_path, local_root)
    current_key = build_object_name(source_code, file_path, local_root)
    local_data = Path(file_path).read_bytes()
    validate_identity(json.loads(local_data), source_code, city, restaurant_id)
    archive_local_bytes(local_root, city, restaurant_id, local_data)

    # Backfill local history, including the pre-upgrade current file.
    version_dir = local_version_root(local_root) / city / restaurant_id
    for path in sorted(version_dir.glob("*/restaurant.json")):
        data = path.read_bytes()
        digest = sha256_bytes(data)
        if path.parent.name != digest:
            raise ValueError(f"Corrupt local snapshot: {path}")
        ensure_snapshot(client, snapshot_key(source_code, city, restaurant_id, digest), data)

    previous = optional_bytes(client, current_key)
    if previous is not None:
        # Protect remote-only legacy data before replacing the current alias.
        ensure_snapshot(client, snapshot_key(source_code, city, restaurant_id, sha256_bytes(previous)), previous)
    selected = local_data if previous is None or overwrite else previous
    raw = json.loads(selected)
    validate_identity(raw, source_code, city, restaurant_id)
    digest = sha256_bytes(selected)
    immutable_key = snapshot_key(source_code, city, restaurant_id, digest)
    ensure_snapshot(client, immutable_key, selected)
    updated = previous != selected
    version_id = None
    if updated:
        result = client.put_object(MINIO_BUCKET, current_key, io.BytesIO(selected), len(selected),
                                   content_type="application/json", metadata={"sha256": digest})
        version_id = getattr(result, "version_id", None)
    return {"object_name": immutable_key, "current_object_key": current_key,
            "sha256": digest, "size_bytes": len(selected), "city": city,
            "restaurant_id": restaurant_id, "crawl_timestamp": raw.get("crawl_timestamp"),
            "crawl_run_id": raw.get("crawl_run_id"), "current_updated": updated,
            "minio_version_id": version_id}


def parse_args():
    parser = argparse.ArgumentParser(description="Upload raw snapshots, then update current aliases")
    parser.add_argument("--source", default="foody")
    parser.add_argument("--local-root", type=Path, default=DEFAULT_LOCAL_ROOT)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--city")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--overwrite", action="store_true", help="Update current alias; retain history")
    parser.add_argument("--run-id")
    parser.add_argument("--manifest-path", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    source = validate_source_code(args.source)
    if args.workers < 1 or (args.limit is not None and args.limit < 1):
        raise ValueError("workers/limit must be positive")
    run_id = safe_component(args.run_id or new_run_id())
    manifest_path = args.manifest_path or args.local_root.parent / "manifests" / f"{run_id}.json"
    if manifest_path.exists():
        raise FileExistsError(f"Manifest already exists; use a new run ID: {manifest_path}")
    files = find_restaurant_files(args.local_root, args.city)
    if args.limit:
        files = files[:args.limit]
    if not files:
        raise RuntimeError("No matching local restaurant files")
    identities = set()
    for path in files:
        _, restaurant_id = validate_local_file(path, args.local_root)
        if restaurant_id in identities:
            raise ValueError(f"Multiple city paths have restaurant ID {restaurant_id}; resolve before upload")
        identities.add(restaurant_id)
    require_bucket(create_minio_client())
    entries, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(upload_one, source, path, args.local_root, args.overwrite): path for path in files}
        for future in as_completed(futures):
            try:
                entries.append(future.result())
            except Exception as exc:
                failures.append({"local_file": str(futures[future]), "error": f"{type(exc).__name__}: {exc}"})
                print(f"FAILED {futures[future]}: {type(exc).__name__}: {exc}", flush=True)
    manifest = {"schema_version": MANIFEST_SCHEMA_VERSION, "run_id": run_id,
                "source": source, "bucket": MINIO_BUCKET,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "failed" if failures else "complete", "selected_files": len(files),
                "entries": sorted(entries, key=lambda entry: entry["object_name"]), "failures": failures}
    write_immutable(manifest_path, json_bytes(manifest))
    ensure_snapshot(get_thread_minio_client(), f"{source}/manifests/{run_id}.json", json_bytes(manifest))
    print(f"Uploaded/selected={len(entries)} failed={len(failures)} manifest={manifest_path}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
