"""Read-only local audit; aggregate counts only, without exposing review text/users."""

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from processing.foody_transform import transform_foody_object
from storage.data_versioning import atomic_write, json_bytes, sha256_bytes, validate_identity


def audit(local_root):
    started = datetime.now(timezone.utc)
    counts, cities, ratings, stop_reasons = Counter(), Counter(), Counter(), Counter()
    metadata_missing = Counter()
    restaurant_ids, review_ids, long_text_counts = Counter(), Counter(), Counter()
    long_text_first_restaurant, cross_restaurant_texts = {}, set()
    errors, timestamps = [], []
    inventory_digest = hashlib.sha256()
    for index, path in enumerate(sorted(local_root.glob('*/*/restaurant.json')), 1):
        data = path.read_bytes()
        counts['files'] += 1
        counts['bytes'] += len(data)
        relative = path.relative_to(local_root).as_posix()
        inventory_digest.update(relative.encode('utf-8') + b'\0' + sha256_bytes(data).encode() + b'\n')
        city, restaurant_id = path.parent.parent.name, path.parent.name
        cities[city] += 1
        restaurant_ids[restaurant_id] += 1
        try:
            raw = json.loads(data)
            validate_identity(raw, 'foody', city, restaurant_id)
            counts['json_identity_ok'] += 1
            summary = raw.get('review_summary') or {}
            counts['crawl_complete_true'] += summary.get('crawl_complete') is True
            stop_reasons[str(summary.get('stop_reason'))] += 1
            stamp = raw.get('crawl_timestamp')
            if stamp:
                timestamps.append(stamp)
                counts['naive_object_timestamps'] += not bool(re.search(r'(Z|[+-]\d\d:\d\d)$', stamp))
            reviews = raw.get('reviews') or []
            counts['raw_reviews'] += len(reviews)
            transformed = transform_foody_object(raw, f'foody/raw/{relative}')
            counts['transform_ok_files'] += 1
            rows = transformed['reviews']
            counts['transformed_reviews'] += len(rows)
            counts['raw_reviews_not_transformed'] += len(reviews) - len(rows)
            restaurant = transformed['restaurant']
            for field in ('avg_rating', 'total_reviews', 'category', 'price_range', 'latitude', 'longitude'):
                metadata_missing[field] += restaurant[field] is None
            counts['restaurant_rq1_complete'] += restaurant['avg_rating'] is not None and restaurant['total_reviews'] is not None
            for review in rows:
                review_ids[review['source_review_id']] += 1
                text, rating = review['review_text'], review['rating']
                counts['text_missing'] += text is None
                counts['rating_missing'] += rating is None
                counts['review_date_missing'] += review['review_date'] is None
                finite_rating = rating is not None and math.isfinite(rating)
                counts['rating_nonfinite'] += rating is not None and not math.isfinite(rating)
                counts['rating_outside_0_10'] += finite_rating and not 0 <= rating <= 10
                counts['rating_zero'] += finite_rating and rating == 0
                if finite_rating:
                    ratings[f'{rating:g}'] += 1
                counts['text_and_positive_rating_0_10'] += bool(text) and finite_rating and 0 < rating <= 10
                if text:
                    counts['text_with_html_pattern'] += bool(re.search(r'<[^>]+>|&(?:[A-Za-z]+|#\d+);', text))
                    counts['text_not_nfc'] += text != unicodedata.normalize('NFC', text)
                    counts['text_with_repeated_whitespace'] += bool(re.search(r'\s{2,}', text))
                    normalized = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()
                    if len(normalized) >= 20:
                        digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
                        long_text_counts[digest] += 1
                        first_restaurant = long_text_first_restaurant.setdefault(digest, restaurant_id)
                        if first_restaurant != restaurant_id:
                            cross_restaurant_texts.add(digest)
        except Exception as exc:
            counts['failed_files'] += 1
            if len(errors) < 20:
                errors.append({'file': relative, 'error_type': type(exc).__name__})
        if index % 5000 == 0:
            print(f'Audited {index} files; transformed reviews={counts["transformed_reviews"]}', flush=True)
    return {
        'scope': 'Current local Foody raw files; read-only scan, not a database audit or a frozen experiment snapshot',
        'started_at': started.isoformat(), 'completed_at': datetime.now(timezone.utc).isoformat(),
        'inventory_sha256': inventory_digest.hexdigest(), 'counts': dict(counts),
        'unique_restaurant_ids': len(restaurant_ids),
        'restaurant_id_duplicate_excess': sum(count - 1 for count in restaurant_ids.values()),
        'unique_review_ids': len(review_ids),
        'review_id_duplicate_excess': sum(count - 1 for count in review_ids.values()),
        'normalized_text_ge20_duplicate_groups': sum(count > 1 for count in long_text_counts.values()),
        'normalized_text_ge20_duplicate_excess': sum(count - 1 for count in long_text_counts.values()),
        'normalized_text_ge20_cross_restaurant_groups': len(cross_restaurant_texts),
        'restaurant_metadata_missing_files': dict(metadata_missing),
        'rating_distribution': dict(sorted(ratings.items(), key=lambda item: float(item[0]))),
        'cities': dict(sorted(cities.items())), 'stop_reasons': dict(stop_reasons),
        'object_timestamp_lexical_min': min(timestamps, default=None),
        'object_timestamp_lexical_max': max(timestamps, default=None),
        'error_examples': errors,
        'notes': [
            'Duplicate text candidates use NFC plus whitespace normalization, case-sensitive, at least 20 characters; they are not automatically spam.',
            '0 < rating <= 10 is only an audit screen, not an approved sentiment label or confirmation of the scale semantics.',
            'No concurrent-write lock was taken for this scan; use immutable snapshot manifests for experiments.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-root', type=Path, default=Path('code/hung/data/foody_shoppefood/raw'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.local_root.exists():
        raise FileNotFoundError(args.local_root)
    result = audit(args.local_root)
    atomic_write(args.output, json_bytes(result))
    print(json.dumps(result['counts'], ensure_ascii=False))
    print(f'Audit saved: {args.output}')


if __name__ == '__main__':
    main()
