"""Import member datasets through MinIO into the shared 3NF schema."""
import argparse
import hashlib
import io
import json
import os
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

repo_root = os.environ.get("FOOD_REVIEW_REPO_ROOT")
SRC = Path(repo_root) / "code/hung/src" if repo_root else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))

KEYS = {
    "restaurants": ("source_code", "source_restaurant_id"),
    "reviewers": ("source_code", "reviewer_id"),
    "restaurant_opening_hours": ("source_code", "source_restaurant_id", "day_of_week"),
    "restaurant_cuisines": ("source_code", "source_restaurant_id", "cuisine"),
    "reviews": ("source_code", "source_review_id"),
    "review_tags": ("source_code", "source_review_id", "tag"),
}
SOURCES = {"kien": "tripadvisor", "sang": "eatigo"}


def put(client, bucket, key, content):
    client.put_object(bucket, key, io.BytesIO(content), len(content),
                      content_type="application/json")


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")


def raw_objects(owner, root):
    if owner == "kien":
        paths = sorted((root / "data/raw/single_restaurants").glob("restaurant_*.json"))
    elif owner == "sang":
        raw = root / "data/raw"
        paths = sorted((raw / "eatigo_copy/raw/single_restaurants").glob("restaurant_*.json"))
        paths += sorted((raw / "eatigo_split").rglob("restaurant.json"))
    else:
        raw = root / "data/raw"
        paths = sorted((raw / "capichi/raw").glob("capichi_final_*.json"))
        paths += sorted((raw / "befood/raw").glob("befood_final_*.json"))
    if not paths:
        raise ValueError(f"No restaurant JSON files found under {root}")
    for path in paths:
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        yield path.relative_to(root).as_posix(), path.read_bytes(), modified


def upload(owner):
    parser = argparse.ArgumentParser(description=f"Upload {owner} data to MinIO")
    parser.add_argument("--raw-root", type=Path, default=SRC.parent / "data" / f"data-{owner}")
    parser.add_argument("--manifest", type=Path, default=Path(f"import-{owner}.json"))
    args = parser.parse_args()

    from storage.minio_client import MINIO_BUCKET, create_minio_client, require_bucket
    from transforms import crawl_time

    client = create_minio_client()
    require_bucket(client)
    prefix = f"external_data/{owner}/{uuid.uuid4().hex}/"
    objects = raw_objects(owner, args.raw_root)
    ranked_entries = []
    for relative_key, content, modified in objects:
        data = json.loads(content.decode("utf-8-sig"))
        observed = crawl_time(owner, data)
        date_rank = datetime.fromisoformat(observed or modified)
        review_count = len(data) if owner == "tuan" else len(data["reviews"])
        priority = (bool(observed), date_rank, review_count)
        key = prefix + relative_key
        put(client, MINIO_BUCKET, key, content)
        entry = {"key": key, "sha256": hashlib.sha256(content).hexdigest(),
                 "file_modified_at": modified}
        ranked_entries.append((priority, entry))
        if len(ranked_entries) % 50 == 0:
            print(f"Uploaded {len(ranked_entries)} objects", flush=True)
    ranked_entries.sort(key=lambda item: item[0], reverse=True)
    entries = [entry for _, entry in ranked_entries]
    manifest = {"owner": owner, "bucket": MINIO_BUCKET, "prefix": prefix, "objects": entries}
    put(client, MINIO_BUCKET, prefix + "manifest.json", encode(manifest))
    temp = args.manifest.with_name(f".{args.manifest.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp.write_bytes(encode(manifest))
        temp.replace(args.manifest)
    finally:
        temp.unlink(missing_ok=True)
    print(f"Uploaded {len(entries)} objects. Manifest: {args.manifest}")


def read_object(client, bucket, entry):
    response = client.get_object(bucket, entry["key"])
    try:
        content = response.read()
    finally:
        response.close()
        response.release_conn()
    if hashlib.sha256(content).hexdigest() != entry["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {entry['key']}")
    return json.loads(content.decode("utf-8-sig"))


def insert_rows(conn, table, rows):
    from psycopg import sql
    from psycopg.types.json import Jsonb

    if not rows:
        return 0
    columns = tuple(rows[0])
    if not set(KEYS[table]).issubset(columns):
        raise ValueError(f"Missing key columns for {table}")
    if any(set(row) != set(columns) for row in rows):
        raise ValueError(f"Mixed column sets for {table}")
    statement = sql.SQL(
        "INSERT INTO {table} ({columns}) SELECT {columns} "
        "FROM jsonb_populate_recordset(NULL::{table}, %s) "
        "ON CONFLICT ({keys}) DO NOTHING"
    ).format(
        table=sql.Identifier(table),
        columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
        keys=sql.SQL(", ").join(map(sql.Identifier, KEYS[table])),
    )
    return conn.execute(statement, (Jsonb(rows),)).rowcount


def load(owner):
    parser = argparse.ArgumentParser(description=f"Load {owner} data from MinIO")
    parser.add_argument("--manifest", type=Path, default=Path(f"import-{owner}.json"))
    parser.add_argument("--dry-run", action="store_true", help="Validate SQL and roll back")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    prefix = manifest["prefix"]
    if manifest["owner"] != owner or not prefix.startswith(f"external_data/{owner}/"):
        raise ValueError("Manifest belongs to a different member")
    entries = manifest["objects"]
    if not entries or any(not entry["key"].startswith(prefix) for entry in entries):
        raise ValueError("Empty manifest or object outside the run prefix")
    from storage.minio_client import MINIO_BUCKET, create_minio_client, require_bucket
    from storage.postgres_client import create_postgres_connection
    from storage.postgres_repository import ensure_source_exists
    from transforms import transform

    if manifest["bucket"] != MINIO_BUCKET:
        raise ValueError("Manifest bucket differs from MINIO_BUCKET")
    client = create_minio_client()
    require_bucket(client)
    seen, inserted = Counter(), Counter()
    with create_postgres_connection() as conn:
        if owner == "tuan":
            from tuan import ensure_tuan_sources

            ensure_tuan_sources(conn)
        else:
            ensure_source_exists(conn, SOURCES[owner])
        for index, entry in enumerate(entries, 1):
            key = entry["key"]
            try:
                payload = read_object(client, MINIO_BUCKET, entry)
                batches = transform(owner, payload, key, entry["file_modified_at"])
                for table in KEYS:
                    rows = batches.get(table, [])
                    seen[table] += len(rows)
                    inserted[table] += insert_rows(conn, table, rows)
                if index % 50 == 0:
                    print(f"Processed {index}/{len(entries)} objects", flush=True)
            except Exception as exc:
                raise RuntimeError(f"Failed object {key}: {exc}") from exc
        if args.dry_run:
            conn.rollback()
    print(json.dumps({"dry_run": args.dry_run, "rows_read": seen,
                      "rows_inserted": inserted}, ensure_ascii=False, indent=2))

