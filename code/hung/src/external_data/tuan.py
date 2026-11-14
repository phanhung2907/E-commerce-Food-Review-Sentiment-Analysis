"""Transform Capichi and BeFood review exports and register BeFood in 3NF."""
import hashlib
import json
from datetime import datetime

from transforms import identifier, number, text, timestamp


def record_crawl_time(row):
    return timestamp(row.get("crawl_timestamp") or row.get("crawled_at"))


def transform_tuan(data, key, file_modified_at):
    restaurants = {}
    reviewers = {}
    reviews = []
    for raw in data:
        source = identifier(raw["source"]).lower()
        if source not in {"capichi", "befood"}:
            raise ValueError(f"Unexpected Tuấn source: {source}")
        restaurant_id = identifier(raw["restaurant_id"])
        parent = dict(source_code=source, source_restaurant_id=restaurant_id)
        crawl = record_crawl_time(raw) or file_modified_at
        restaurant_key = (source, restaurant_id)
        current = restaurants.get(restaurant_key)
        if current is None or datetime.fromisoformat(crawl) > datetime.fromisoformat(current["crawl_timestamp"]):
            restaurants[restaurant_key] = dict(
                parent, name=text(raw.get("restaurant_name")), url=text(raw.get("restaurant_url")),
                city=text(raw.get("city")), category=text(raw.get("category")),
                avg_rating=number(raw.get("restaurant_rating")), total_reviews=number(raw.get("total_reviews")),
                crawl_timestamp=crawl, raw_object_key=key,
            )
        review_text = text(raw.get("review_text"))
        rating = number(raw.get("rating"))
        review_id = text(raw.get("review_id"))
        if source == "befood" and review_id is None:
            identity = json.dumps([restaurant_id, review_text, rating], ensure_ascii=False)
            review_id = "legacy-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
        reviewer_id = text(raw.get("reviewer_id"))
        if reviewer_id and reviewer_id.casefold() in {"ẩn danh", "anonymous"}:
            reviewer_id = None
        if reviewer_id:
            reviewers[(source, reviewer_id)] = dict(source_code=source, reviewer_id=reviewer_id)
        reviews.append(dict(
            parent, source_review_id=identifier(review_id), reviewer_id=reviewer_id,
            reviewer_name_raw=text(raw.get("reviewer_id")) if reviewer_id is None else None,
            review_text=review_text, rating=rating, language=text(raw.get("language")),
            review_date=timestamp(raw.get("review_date")),
        ))
    return {"restaurants": list(restaurants.values()), "reviewers": list(reviewers.values()),
            "reviews": reviews}


def ensure_tuan_sources(conn):
    from psycopg import sql

    conn.execute(
        "INSERT INTO sources (source_code, rating_scale_max) VALUES ('capichi', 5) "
        "ON CONFLICT DO NOTHING"
    )
    if conn.execute("SELECT 1 FROM sources WHERE source_code = 'befood'").fetchone():
        return
    conn.execute("LOCK TABLE sources IN ACCESS EXCLUSIVE MODE")
    if conn.execute("SELECT 1 FROM sources WHERE source_code = 'befood'").fetchone():
        return
    constraint = conn.execute("""
        SELECT pg_get_expr(conbin, conrelid)
        FROM pg_constraint
        WHERE conrelid = 'sources'::regclass AND conname = 'chk_source_code' AND contype = 'c'
    """).fetchone()
    if constraint:
        conn.execute(sql.SQL(
            "ALTER TABLE sources DROP CONSTRAINT chk_source_code, "
            "ADD CONSTRAINT chk_source_code CHECK (({}) OR source_code = 'befood')"
        ).format(sql.SQL(constraint[0])))
    conn.execute("INSERT INTO sources (source_code, rating_scale_max) VALUES ('befood', 5)")
