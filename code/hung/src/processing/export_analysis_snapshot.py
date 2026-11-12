"""Freeze consistent PostgreSQL analysis tables into a new, checksummed directory."""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from storage.data_versioning import TRANSFORM_VERSION, json_bytes, new_run_id, safe_component, transform_fingerprint, write_immutable
from storage.postgres_client import create_postgres_connection

QUERIES = {
    'reviews.csv': '''
        SELECT r.source_code, r.source_review_id, r.source_restaurant_id,
               r.review_title, r.review_text, r.rating, s.rating_scale_max,
               r.review_date, r.language, r.observed_at, r.raw_object_key,
               q.city, q.category, q.price_range,
               char_length(r.review_text) AS comment_length_chars
        FROM reviews r
        JOIN restaurants q USING (source_code, source_restaurant_id)
        JOIN sources s USING (source_code)
        ORDER BY r.source_code, r.source_review_id
    ''',
    'restaurants.csv': '''
        SELECT q.source_code, q.source_restaurant_id, q.city, q.category, q.price_range,
               q.avg_rating AS platform_avg_rating, q.total_reviews AS platform_total_reviews,
               s.rating_scale_max, q.crawl_timestamp, q.raw_object_key,
               COALESCE(a.n_reviews_crawled, 0) AS n_reviews_crawled,
               a.mean_rating_crawled, a.n_nonmissing_ratings,
               COALESCE(c.cuisines, '') AS cuisines
        FROM restaurants q
        JOIN sources s USING (source_code)
        LEFT JOIN (
            SELECT source_code, source_restaurant_id, count(*) AS n_reviews_crawled,
                   avg(rating) AS mean_rating_crawled, count(rating) AS n_nonmissing_ratings
            FROM reviews GROUP BY source_code, source_restaurant_id
        ) a USING (source_code, source_restaurant_id)
        LEFT JOIN (
            SELECT source_code, source_restaurant_id, string_agg(cuisine, ' | ' ORDER BY cuisine) AS cuisines
            FROM restaurant_cuisines GROUP BY source_code, source_restaurant_id
        ) c USING (source_code, source_restaurant_id)
        ORDER BY q.source_code, q.source_restaurant_id
    ''',
    'raw_lineage.csv': '''
        SELECT v.* FROM data_ingestion_versions v
        WHERE v.raw_object_key IN (
            SELECT raw_object_key FROM reviews UNION SELECT raw_object_key FROM restaurants
        )
        ORDER BY v.source_code, v.source_restaurant_id, v.raw_sha256, v.transform_version
    ''',
}


def export_query(conn, sql, destination):
    count = 0
    with conn.cursor(name='analysis_export') as cursor:
        cursor.execute(sql)
        with destination.open('w', encoding='utf-8', newline='') as output:
            writer = csv.writer(output)
            writer.writerow(column.name for column in cursor.description)
            while rows := cursor.fetchmany(2000):
                writer.writerows(rows)
                count += len(rows)
    digest = hashlib.sha256()
    with destination.open('rb') as saved:
        for chunk in iter(lambda: saved.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'rows': count, 'bytes': destination.stat().st_size, 'sha256': digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-id', help='New identifier, e.g. eda-v1-20261019')
    parser.add_argument('--output-root', type=Path, default=Path('code/hung/data/processed'))
    args = parser.parse_args()
    dataset_id = safe_component(args.dataset_id or 'eda-' + new_run_id())
    final = args.output_root / dataset_id
    if final.exists():
        raise FileExistsError(f'Dataset already exists: {final}')
    partial = args.output_root / f'.partial-{dataset_id}-{new_run_id()}'
    partial.mkdir(parents=True, exist_ok=False)
    files = {}
    with create_postgres_connection() as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        unversioned = conn.execute(
            'SELECT count(*) FROM reviews WHERE observed_at IS NULL OR raw_object_key IS NULL'
        ).fetchone()[0]
        if unversioned:
            raise ValueError(f'{unversioned} reviews have no version lineage; reconcile/reimport before export')
        missing_lineage = conn.execute('''
            SELECT count(*) FROM (
                SELECT raw_object_key FROM reviews UNION SELECT raw_object_key FROM restaurants
            ) keys WHERE NOT EXISTS (
                SELECT 1 FROM data_ingestion_versions v WHERE v.raw_object_key = keys.raw_object_key
            )
        ''').fetchone()[0]
        if missing_lineage:
            raise ValueError(f'{missing_lineage} raw references have no committed version ledger')
        transaction_time = conn.execute('SELECT transaction_timestamp()').fetchone()[0].isoformat()
        for filename, query in QUERIES.items():
            files[filename] = export_query(conn, query, partial / filename)
    if not files['reviews.csv']['rows']:
        raise ValueError('No reviews to export')
    manifest = {'schema_version': 1, 'dataset_id': dataset_id, 'status': 'complete',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'db_transaction_timestamp': transaction_time,
                'transform_version': TRANSFORM_VERSION, 'export_code_transform_fingerprint': transform_fingerprint(),
                'files': files,
                'query_sha256': {name: hashlib.sha256(sql.encode()).hexdigest() for name, sql in QUERIES.items()},
                'null_policy': 'CSV empty field means SQL NULL; read strings as UTF-8 and IDs as character',
                'notes': ['This is a frozen extract, before analysis eligibility filters.',
                          'Platform metadata and metrics computed from crawled reviews are separate columns.',
                          'An unfinished .partial directory is not an approved dataset.']}
    write_immutable(partial / 'manifest.json', json_bytes(manifest))
    partial.rename(final)
    print(json.dumps({'dataset_id': dataset_id, 'path': str(final), 'files': files}, ensure_ascii=False))


if __name__ == '__main__':
    main()
