"""Rank candidates on train and take the union of the two rankings."""

import numpy as np

from text_features import candidate_text


def model_weights(pipeline, model):
    estimator = pipeline.named_steps["classifier"]
    positive = int(np.flatnonzero(estimator.classes_ == 1)[0])
    if model == "logistic":
        return estimator.coef_[0] if positive == 1 else -estimator.coef_[0]
    return estimator.feature_log_prob_[positive] - estimator.feature_log_prob_[1 - positive]


def discover(matrix, names, labels, shops, models, language, level, top_n):
    positive = labels == level
    positive_matrix = matrix[positive].tocsc()
    support = np.diff(positive_matrix.indptr)
    positive_shops = shops[positive]
    eligible = {}
    weights = {model: model_weights(pipeline, model) for model, (pipeline, _) in models.items()}
    full_support = np.bincount(matrix.indices, minlength=matrix.shape[1])
    proposals = {}
    for model, scores in weights.items():
        ordered = np.argsort(-scores, kind="stable")
        rank = 0
        for column in ordered:
            if scores[column] <= 0:
                break
            if support[column] < 20 or not candidate_text(names[column], language):
                continue
            if column not in eligible:
                indices = positive_matrix.indices[positive_matrix.indptr[column]:positive_matrix.indptr[column + 1]]
                _, counts = np.unique(positive_shops[indices], return_counts=True)
                eligible[column] = (len(counts), float(counts.max() / len(indices)))
            shop_count, concentration = eligible[column]
            if shop_count < 5:
                continue
            rank += 1
            if column not in proposals:
                a = int(support[column])
                b = int(full_support[column]) - a
                c = int(positive.sum()) - a
                d = len(labels) - a - b - c
                proposals[column] = {
                    "language": language, "rating": level, "phrase": str(names[column]),
                    "column": int(column), "train_target_with_phrase": a,
                    "train_target_shops_with_phrase": shop_count,
                    "train_top_shop_share": concentration,
                    "train_p1": a / (a + b), "train_p2": c / (c + d),
                    "train_smoothed_log_or": float(np.log((a + 0.5) * (d + 0.5) / ((b + 0.5) * (c + 0.5)))),
                    "logistic_weight": float(weights["logistic"][column]),
                    "bayes_score": float(weights["bayes"][column]),
                    "logistic_rank": None, "bayes_rank": None,
                }
            proposals[column][f"{model}_rank"] = rank
            if rank == top_n:
                break
    return sorted(proposals.values(), key=lambda row: row["phrase"])
