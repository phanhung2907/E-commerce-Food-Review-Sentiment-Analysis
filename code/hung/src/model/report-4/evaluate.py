"""Held-out keyword tests, Holm correction and classifier metrics."""

import math

import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_fscore_support

from text_features import context_tokens


def divide(numerator, denominator):
    return numerator / denominator if denominator else None


def phrase_counts(candidate, matrix, ratings, groups, shops, rows):
    level = candidate["rating"]
    column = candidate["column"]
    indices = matrix.indices[matrix.indptr[column]:matrix.indptr[column + 1]]
    has_phrase = np.zeros(len(ratings), dtype=bool)
    has_phrase[indices] = True
    positive = ratings == level
    cells = np.bincount(2 * (~has_phrase) + (~positive), minlength=4)
    a, b, c, d = map(int, cells)
    supported = np.flatnonzero(has_phrase & positive)
    target_shops = len(np.unique(shops[supported]))
    target_groups = len(np.unique(groups[supported]))
    p1, p2 = divide(a, a + b), divide(c, c + d)
    result = {
        **candidate, "tp": a, "fp": b, "fn": c, "tn": d,
        "precision": p1, "recall": divide(a, a + c),
        "f1": divide(2 * a, 2 * a + b + c),
        "accuracy": divide(a + d, a + b + c + d),
        "majority_accuracy": max(a + c, b + d) / len(ratings),
        "p1": p1, "p2": p2, "delta_pp": (p1 - p2) * 100 if p1 is not None and p2 is not None else None,
        "target_reviews": a, "target_shops": target_shops, "target_groups": target_groups,
        "test_groups": int(groups.max()) + 1,
        "or": None, "ci_low": None, "ci_high": None, "se": None, "z": None,
        "p_raw": None, "p_holm": None, "holm_rank": None,
        "length_sensitivity": None, "context": "",
    }
    if min(cells) > 0:
        result["or"] = a * d / (b * c)
    if min(cells) <= 0:
        result["reason"] = "Ô đếm bằng 0"
    elif a < 10 or target_shops < 5 or target_groups < 5:
        result["reason"] = "Thiếu review hoặc nhóm quán hỗ trợ"
    else:
        group_count = result["test_groups"]
        group_cells = np.bincount(
            groups * 4 + 2 * (~has_phrase) + (~positive), minlength=group_count * 4,
        ).reshape(-1, 4)
        influence = (group_cells / cells) @ np.array([1, -1, -1, 1])
        se = math.sqrt(group_count / (group_count - 1) * float(influence @ influence))
        if not math.isfinite(se) or se <= np.finfo(float).eps:
            result["reason"] = "Sai số chuẩn suy biến"
        else:
            theta = math.log(result["or"])
            z = theta / se
            low, high = theta - 1.96 * se, theta + 1.96 * se
            result.update(se=se, z=z, p_raw=float(norm.sf(z)), ci_low=math.exp(low),
                          ci_high=math.exp(high), reason="")
    return result, has_phrase


def length_sensitivity(has_phrase, labels, lengths, cutoffs):
    strata = np.digitize(lengths, cutoffs)
    values = []
    for index in np.unique(strata):
        a, b, c, d = np.bincount(2 * (~has_phrase[strata == index]) + (~labels[strata == index]), minlength=4)
        p1, p2 = divide(a, a + b), divide(c, c + d)
        if p1 is not None and p2 is not None:
            values.append(f"nhóm {index + 1}: {(p1 - p2) * 100:+.1f} đpt ({a+b+c+d} review, {a+b} có cụm)")
    return "; ".join(values)


def evaluate_candidates(candidates, matrix, ratings, groups, shops, rows, cutoffs):
    matrix = matrix.tocsc()
    groups = np.unique(groups, return_inverse=True)[1]
    lengths = np.array([len(row["text"]) for row in rows])
    results = []
    for candidate in candidates:
        result, flags = phrase_counts(candidate, matrix, ratings, groups, shops, rows)
        level = candidate["rating"]
        result["length_sensitivity"] = length_sensitivity(flags, ratings == level, lengths, cutoffs)
        contexts = []
        used_shops = set()
        if result["p_raw"] is not None and result["p_raw"] < 0.05 and result["or"] >= 1.5:
            for index in np.flatnonzero(flags & (ratings == level)):
                row = rows[index]
                if row["shop"] in used_shops:
                    continue
                context = context_tokens(row["text"], candidate["language"], candidate["phrase"], row["shop_name"])
                if context and context not in contexts:
                    contexts.append(context)
                    used_shops.add(row["shop"])
                if len(contexts) == 2:
                    break
        result["context"] = " / ".join(contexts)
        results.append(result)
    return results


def apply_holm(results):
    ordered = sorted(results, key=lambda row: (row["p_raw"] is None, row["p_raw"] if row["p_raw"] is not None else 1.0,
                                               row["language"], row["rating"], row["phrase"]))
    running = 0.0
    for index, row in enumerate(ordered):
        row["holm_rank"] = index + 1
        raw = row["p_raw"] if row["p_raw"] is not None else 1.0
        running = max(running, min(1.0, (len(ordered) - index) * raw))
        row["holm_input"] = raw
        if row["p_raw"] is None:
            row["status"] = "Chưa đủ bằng chứng"
            continue
        row["p_holm"] = running
        failures = []
        if row["p1"] <= row["p2"]:
            failures.append("Sai chiều")
        if row["or"] < 1.5:
            failures.append("OR < 1.5")
        if row["ci_low"] <= 1:
            failures.append("CI chứa 1 hoặc thấp hơn")
        if running >= 0.05:
            failures.append("p Holm ≥ 0.05")
        row["status"] = "Không đạt" if failures else "Xác nhận"
        row["reason"] = "; ".join(failures)


def model_metrics(language, level, models, test_matrix, train_lengths, test_lengths, y_train, y_test):
    length_model = LogisticRegression(solver="lbfgs").fit(train_lengths, y_train)
    length_ap = float(average_precision_score(y_test, length_model.predict_proba(test_lengths)[:, 1]))
    baseline_ap = float(np.mean(y_test))
    result = []
    for model, (pipeline, config) in models.items():
        probabilities = pipeline.named_steps["classifier"].predict_proba(test_matrix)[:, 1]
        predictions = probabilities >= config["threshold"]
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, predictions, average="binary", zero_division=0,
        )
        ap = float(average_precision_score(y_test, probabilities))
        result.append({
            "language": language, "rating": level, "model": model, "ap": ap,
            "precision": float(precision), "recall": float(recall), "f1": float(f1),
            "class_prior_ap": baseline_ap, "length_baseline_ap": length_ap,
            "delta_ap_vs_length": ap - length_ap, **config,
        })
    return result
