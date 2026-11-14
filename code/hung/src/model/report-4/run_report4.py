"""Run Report 4 from the prepared snapshot through the Markdown conclusion."""

import argparse
from collections import defaultdict
from pathlib import Path
import numpy as np
from discover import discover
from evaluate import apply_holm, evaluate_candidates, model_metrics
from prepare import (
    LANGUAGES, file_hash, foody_restaurant_paths, load_shop_names,
    prepare_language, read_snapshot, split_reviews,
)
from report import write_csv, write_report
from train import save_model, train_models, verify_models


HUNG = Path(__file__).resolve().parents[3]
DATA_ROOT = HUNG / "data"
DEFAULT_INPUT = DATA_ROOT / "preprocess_merged_data/reviews_preprocessed.csv"
DEFAULT_OUTPUT = HUNG / "docs/report-4"


def progress(message):
    print(message, flush=True)


def coverage_rows(language, ratings, shops, train, test):
    result = []
    for level in range(6):
        row = {"language": language, "rating": level}
        for name, indices in (("train", train), ("test", test)):
            subset = indices[ratings[indices] == level]
            row[f"{name}_reviews"] = len(subset)
            row[f"{name}_shops"] = len(np.unique(shops[subset]))
        result.append(row)
    return result


def audit_samples(rows, seed):
    rng = np.random.default_rng(seed)
    strata = defaultdict(list)
    for row in rows:
        key = (row["source_code"], row["rating"], "short" if len(row["text"].split()) <= 5 else "long")
        strata[key].append(row)
    result = []
    for key, group in sorted(strata.items()):
        for index in sorted(rng.choice(len(group), min(3, len(group)), replace=False)):
            row = group[index]
            result.append({
                "language": row["language"], "source_code": key[0], "rating": key[1],
                "length_group": key[2], "source_review_id": row["source_review_id"],
                "source_restaurant_id": row["source_restaurant_id"],
                "review_status": row["language_status"], "detected_language": row["detected_language"],
            })
    return result


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    input_sha = file_hash(args.input)
    progress(f"Reading {args.input.name}")
    reviews, datasets = read_snapshot(args.input)
    selected = sum(frame.height for frame in datasets.values())
    foody_paths = foody_restaurant_paths(reviews, args.data_root)
    shop_names = load_shop_names(args.data_root)
    audit, zero_audit, samples, manifest, coverage, locked = [], [], [], [], [], []
    skipped = {}
    prepared = {}

    for language, frame in datasets.items():
        progress(f"{language}: audit {frame.height:,} reviews and split by shop")
        rows, zeros, drops = prepare_language(frame, args.data_root, foody_paths, shop_names)
        zero_audit.extend(zeros)
        samples.extend(audit_samples(rows, args.seed))
        train, test, groups, folds, links = split_reviews(rows, args.seed)
        ratings = np.array([row["rating"] for row in rows], dtype=np.int8)
        shop_codes = {shop: index for index, shop in enumerate(sorted({row["shop"] for row in rows}))}
        shops = np.array([shop_codes[row["shop"]] for row in rows], dtype=int)
        texts = np.array([row["text"] for row in rows], dtype=object)
        split = np.full(len(rows), "train", dtype=object)
        split[test] = "test"
        fold_assignment = np.full(len(rows), -1)
        for fold, (_, validation) in enumerate(folds, 1):
            fold_assignment[train[validation]] = fold
        for index, row in enumerate(rows):
            manifest.append({
                "language": language, "source_code": row["source_code"],
                "source_review_id": row["source_review_id"], "source_restaurant_id": row["source_restaurant_id"],
                "group": int(groups[index]), "split": split[index],
                "fold": int(fold_assignment[index]) if fold_assignment[index] > 0 else None,
                "rating": int(ratings[index]), "seed": args.seed, "snapshot_sha256": input_sha,
            })
        language_coverage = coverage_rows(language, ratings, shops, train, test)
        coverage.extend(language_coverage)
        levels = []
        for row in language_coverage:
            level = row["rating"]
            if row["train_reviews"] < 20 or row["train_shops"] < 5:
                skipped[language, level] = "Thiếu review hoặc quán lớp đích trên train"
            elif row["test_reviews"] == 0 or row["test_reviews"] == len(test) or row["train_reviews"] == len(train):
                skipped[language, level] = "Train hoặc test thiếu một lớp"
            else:
                levels.append(level)
        audit.append({
            "language": language, "input_rows": frame.height, "train_rows": len(train),
            "test_rows": len(test), "train_shops": len(np.unique(shops[train])),
            "test_shops": len(np.unique(shops[test])), "zero_kept": int(np.count_nonzero(ratings == 0)),
            "zero_dropped": drops["unverified_zero"], "language_drops": drops["language_mismatch"],
            "other_drops": sum(drops.values()) - drops["unverified_zero"] - drops["language_mismatch"],
            "exact_group_links": links["exact"], "near_group_links": links["near"],
        })
        progress(f"{language}: train={len(train):,}, test={len(test):,}, levels={levels}")
        prepared[language] = (rows, texts, ratings, shops, groups, train, test, folds, levels)

    manifest_path = args.output / "split_manifest.csv"
    write_csv(manifest_path, manifest)
    metadata = {
        "input_name": args.input.name, "input_rows": reviews.height, "selected_rows": selected,
        "input_sha256": input_sha, "manifest_sha256": file_hash(manifest_path),
        "seed": args.seed, "top_n": args.top_n,
    }
    del manifest, reviews, datasets
    write_csv(args.output / "rating_coverage.csv", coverage)
    write_csv(args.output / "rating_zero_audit.csv", zero_audit)
    write_csv(args.output / "language_audit_sample.csv", samples)

    trained = {}
    verification = []
    for language, data in prepared.items():
        _, texts, ratings, shops, _, train, _, folds, levels = data
        if not levels:
            continue
        tfidf, matrix, models = train_models(texts[train], ratings[train], folds, levels, language, progress)
        names = tfidf.get_feature_names_out()
        candidates = []
        for level, estimators in models.items():
            candidates.extend(discover(matrix, names, ratings[train], shops[train], estimators,
                                       language, level, args.top_n))
            model_folder = args.output / "model" / LANGUAGES[language] / f"rating-{level}"
            for model, (pipeline, config) in estimators.items():
                path = model_folder / f"{model}.joblib"
                save_model(path, pipeline, {**metadata, **config, "language": language, "rating": level, "model": model})
                verification.append((path, pipeline, config["threshold"], texts[train[:3]]))
        locked.extend(candidates)
        trained[language] = (tfidf, models, candidates)
        progress(f"{language}: saved {2 * len(models)} models, locked {len(candidates)} candidates")

    write_csv(args.output / "locked_candidates.csv", locked)
    progress(f"Reload check for {len(verification)} models")
    verify_models(verification)

    results, metrics = [], []
    for language, (tfidf, models, candidates) in trained.items():
        rows, texts, ratings, shops, groups, train, test, _, _ = prepared[language]
        progress(f"{language}: evaluate {len(candidates)} locked candidates")
        test_matrix = tfidf.transform(texts[test])
        test_rows = [rows[index] for index in test]
        train_lengths = np.array([len(text) for text in texts[train]]).reshape(-1, 1)
        test_lengths = np.array([len(text) for text in texts[test]]).reshape(-1, 1)
        cutoffs = np.unique(np.quantile(train_lengths, [1 / 3, 2 / 3]))
        results.extend(evaluate_candidates(candidates, test_matrix, ratings[test], groups[test],
                                           shops[test], test_rows, cutoffs))
        for level, estimators in models.items():
            metrics.extend(model_metrics(language, level, estimators, test_matrix, np.log1p(train_lengths),
                                         np.log1p(test_lengths), ratings[train] == level, ratings[test] == level))
    apply_holm(results)

    by_level = defaultdict(list)
    for row in results:
        by_level[row["language"], row["rating"]].append(row)
    summary = []
    for language in LANGUAGES:
        for level in range(6):
            subset = sorted(by_level[language, level], key=lambda row: row["holm_rank"])
            confirmed = [row["phrase"] for row in subset if row["status"] == "Xác nhận"]
            summary.append({
                "language": language, "rating": level,
                "logistic_candidates": sum(row["logistic_rank"] is not None for row in subset),
                "bayes_candidates": sum(row["bayes_rank"] is not None for row in subset),
                "candidates": len(subset), "confirmed": len(confirmed),
                "confirmed_phrases": ", ".join(confirmed),
                "status": skipped.get((language, level), "Có cụm xác nhận" if confirmed else
                                      "Chưa có cụm được xác nhận" if subset else "Không có ứng viên đủ hỗ trợ"),
            })
    assert len(locked) == len(results)
    assert len({(row["language"], row["rating"], row["phrase"]) for row in locked}) == len(locked)
    assert len(summary) == len(LANGUAGES) * 6
    assert len(metrics) == len(verification)
    for row in results:
        if row["status"] == "Xác nhận":
            assert row["p_holm"] < 0.05 and row["or"] >= 1.5 and row["ci_low"] > 1 and row["p1"] > row["p2"]
    write_csv(args.output / "keyword_results.csv", sorted(results, key=lambda row: row["holm_rank"]))
    write_csv(args.output / "test_metrics.csv", metrics)
    write_csv(args.output / "keywords_by_language_rating.csv", summary)
    write_report(args.output / "REPORT_4_RESULTS.md", audit, coverage, summary, results, metrics, metadata)
    progress(f"Done: {len(metrics)} models, {len(results)} candidates, "
             f"{sum(row['confirmed'] for row in summary)} confirmed")
    progress(str(args.output / "REPORT_4_RESULTS.md"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=20261114)
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()
    if args.top_n < 1:
        parser.error("--top-n must be positive")
    run(args)


if __name__ == "__main__":
    main()
