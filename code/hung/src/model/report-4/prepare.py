"""Read the immutable review snapshot and prepare restaurant-disjoint splits."""

from collections import Counter, defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import polars as pl
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold

from language_audit import audit_language, review_body
from text_features import WORD

LANGUAGES = {"vi": "vn", "en": "en", "ja": "ja", "fr": "fr"}
COLUMNS = (
    "source_code", "source_review_id", "source_restaurant_id", "language",
    "review_text", "rating", "rating_level_5", "raw_object_key",
)


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_snapshot(path):
    reviews = pl.read_csv(path, columns=COLUMNS, schema_overrides={column: pl.String for column in COLUMNS})
    reviews = reviews.with_columns(
        pl.col("language").str.strip_chars().str.to_lowercase().fill_null("unknown"),
        pl.col("rating_level_5").cast(pl.Int8, strict=False),
    )
    return reviews, {
        language: reviews.filter(pl.col("language") == language)
        for language in LANGUAGES
    }


@lru_cache(maxsize=128)
def raw_reviews(path):
    try:
        document = json.loads(path.read_bytes())
    except (FileNotFoundError, OSError, ValueError):
        return {}
    return {
        str(review.get("Id", review.get("id"))): review
        for review in document.get("reviews", [])
        if isinstance(review, dict)
    }


def audit_zero(row, data_root, foody_paths):
    source, shop = row["source_code"], row["source_restaurant_id"]
    paths = []
    if source == "foody":
        if row["raw_object_key"]:
            key = Path(row["raw_object_key"])
            if key.parts and key.parts[0] == "foody" and ".." not in key.parts:
                paths.append(data_root / "foody_shoppefood" / Path(*key.parts[1:]))
        paths.extend(foody_paths.get(shop, ()))
    elif source == "eatigo":
        paths.append(data_root / "data-sang/data/raw/eatigo_copy/raw/single_restaurants" / f"restaurant_{shop}_eatigo.json")

    for path in dict.fromkeys(paths):
        review = raw_reviews(path).get(row["source_review_id"])
        if review is None:
            continue
        for field in ("AvgRating", "rating", "Rating"):
            value = review.get(field)
            if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                try:
                    status = "explicit_zero" if float(value) == 0.0 else "raw_rating_disagrees"
                except ValueError:
                    continue
                return status, field, str(value), str(path.relative_to(data_root))
        return "raw_rating_missing", "", "", str(path.relative_to(data_root))
    return "raw_review_unmatched", "", "", ""


def foody_restaurant_paths(reviews, data_root):
    shops = set(reviews.filter(
        (pl.col("source_code") == "foody") & (pl.col("rating_level_5") == 0)
    ).get_column("source_restaurant_id"))
    root = data_root / "foody_shoppefood/raw"
    paths = defaultdict(list)
    for city in sorted(root.glob("*")):
        for shop in sorted(shops - {None}):
            candidate = city / shop / "restaurant.json"
            if candidate.is_file():
                paths[shop].append(candidate)
    return paths


def load_shop_names(data_root):
    path = data_root / "preprocess_merged_data/restaurants.csv"
    if not path.is_file():
        return {}
    names = pl.read_csv(path, columns=["source_code", "source_restaurant_id", "name"],
                        schema_overrides={"source_restaurant_id": pl.String, "name": pl.String})
    return {(source, shop): name for source, shop, name in names.iter_rows() if name}


def prepare_language(frame, data_root, foody_paths, shop_names):
    rows, zero_audit, drops = [], [], Counter()
    keys = set()
    for row in frame.sort("source_code", "source_review_id").iter_rows(named=True):
        source, review_id, shop = (row[column] for column in COLUMNS[:3])
        key = (source, review_id)
        if not all((source, review_id, shop)):
            drops["missing_key"] += 1
            continue
        if key in keys:
            raise ValueError(f"Duplicate review key in the snapshot: {key}")
        keys.add(key)
        rating = row["rating_level_5"]
        if rating not in range(6):
            drops["invalid_rating"] += 1
            continue
        if rating == 0:
            status, field, raw_rating, path = audit_zero(row, data_root, foody_paths)
            zero_audit.append({
                "language": row["language"], "source_code": source, "source_review_id": review_id,
                "source_restaurant_id": shop, "csv_rating": row["rating"], "status": status,
                "raw_field": field, "raw_rating": raw_rating, "raw_path": path,
            })
            if status != "explicit_zero":
                drops["unverified_zero"] += 1
                continue
        cleaned = review_body(row["review_text"] or "", source)
        if not any(character.isalpha() for character in cleaned):
            drops["empty_after_cleaning"] += 1
            continue
        rows.append({
            "source_code": source, "source_review_id": review_id, "source_restaurant_id": shop,
            "language": row["language"], "rating": rating, "text": cleaned,
            "shop": (source, shop), "shop_name": shop_names.get((source, shop), ""),
        })
    if rows:
        audit_language(rows, rows[0]["language"])
    retained = [row for row in rows if row["language_status"] != "language_mismatch"]
    drops["language_mismatch"] = len(rows) - len(retained)
    return retained, zero_audit, drops


def restaurant_groups(rows):
    """Join shops sharing long exact or anchored near-duplicate text."""
    shops = {shop: index for index, shop in enumerate(sorted({row["shop"] for row in rows}))}
    parents = list(range(len(shops)))

    def root(index):
        while index != parents[index]:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def join(left, right):
        left, right = root(left), root(right)
        if left != right:
            parents[max(left, right)] = min(left, right)

    exact = {}
    anchors = defaultdict(list)
    links = Counter()
    for row in rows:
        text = " ".join(WORD.findall(row["text"].lower()))
        if len(text) < 120:
            continue
        shop = shops[row["shop"]]
        digest = hashlib.blake2b(text.encode(), digest_size=16).digest()
        previous = exact.setdefault(digest, shop)
        if previous != shop:
            if root(shop) != root(previous):
                links["exact"] += 1
                join(shop, previous)
            continue
        for anchor in (("head", text[:48]), ("tail", text[-48:])):
            representatives = anchors[anchor]
            matched = False
            for other, reference in representatives:
                if root(shop) == root(other):
                    continue
                if min(len(text), len(reference)) < 0.90 * max(len(text), len(reference)):
                    continue
                if SequenceMatcher(None, text, reference).ratio() >= 0.90:
                    join(shop, other)
                    links["near"] += 1
                    matched = True
                    break
            if not matched and len(representatives) < 12:
                representatives.append((shop, text))
    return np.array([root(shops[row["shop"]]) for row in rows]), links


def split_reviews(rows, seed):
    labels = np.array([row["rating"] for row in rows], dtype=np.int8)
    groups, links = restaurant_groups(rows)
    if len(np.unique(groups)) < 2:
        return np.arange(len(rows)), np.array([], dtype=int), groups, [], links
    total = np.bincount(labels, minlength=6)
    levels = total > 0
    best = None
    splitter = GroupShuffleSplit(n_splits=96, test_size=0.20, random_state=seed)
    for train, test in splitter.split(labels, groups=groups):
        test_counts = np.bincount(labels[test], minlength=6)
        fractions = test_counts[levels] / total[levels]
        missing = np.count_nonzero((fractions == 0) | (fractions == 1))
        score = missing * 10 + abs(len(test) / len(labels) - 0.20) + np.mean(abs(fractions - 0.20))
        if best is None or score < best[0]:
            best = (score, train, test)
    _, train, test = best
    assert not (set(groups[train]) & set(groups[test]))
    folds = []
    fold_count = min(5, len(np.unique(groups[train])))
    if fold_count >= 2:
        splitter = StratifiedGroupKFold(n_splits=fold_count, shuffle=True, random_state=seed)
        folds = list(splitter.split(labels[train], labels[train], groups[train]))
        for fit, validation in folds:
            assert not (set(groups[train[fit]]) & set(groups[train[validation]]))
    return train, test, groups, folds, links
