"""Fit the two classifiers and verify serialized pipelines in a fresh process."""

import argparse
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import warnings

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from text_features import clean_text, terms

GRID = {"logistic": (0.5, 2.0), "bayes": (0.25, 1.0)}


def text_vectorizer(language):
    return TfidfVectorizer(analyzer=partial(analyze, language=language),
                           min_df=2, max_features=150_000, sublinear_tf=True, dtype=np.float64)


def pretokenized(document):
    return document


def analyze(text, language):
    return terms(clean_text(text), language)


def classifier(model, param):
    if model == "logistic":
        return LogisticRegression(solver="liblinear", C=param, max_iter=500, random_state=0)
    return ComplementNB(alpha=param)


def fit_classifier(model, param, matrix, y):
    with warnings.catch_warnings(), threadpool_limits(limits=2):
        warnings.simplefilter("error", ConvergenceWarning)
        return classifier(model, param).fit(matrix, y)


def best_threshold(y, probabilities):
    precision, recall, thresholds = precision_recall_curve(y, probabilities)
    score = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
    return float(thresholds[np.argmax(score)])


def train_models(texts, ratings, folds, levels, language, progress):
    """Reuse each fold's TF-IDF across all one-vs-rest models."""
    progress(f"{language}: tokenize {len(texts):,} train reviews")
    documents = np.empty(len(texts), dtype=object)
    for index, text in enumerate(texts):
        documents[index] = tuple(analyze(text, language))
    scores = {
        (level, model, param): np.full(len(ratings), np.nan)
        for level in levels for model in GRID for param in GRID[model]
    }
    for fold, (train, validation) in enumerate(folds, 1):
        progress(f"{language}: CV {fold}/{len(folds)}")
        tfidf = text_vectorizer(language)
        tfidf.analyzer = pretokenized
        x_train = tfidf.fit_transform(documents[train])
        x_validation = tfidf.transform(documents[validation])
        for level in levels:
            y = ratings == level
            if len(np.unique(y[train])) != 2 or len(np.unique(y[validation])) != 2:
                continue
            for model, parameters in GRID.items():
                for param in parameters:
                    estimator = fit_classifier(model, param, x_train, y[train])
                    scores[level, model, param][validation] = estimator.predict_proba(x_validation)[:, 1]

    tfidf = text_vectorizer(language)
    tfidf.analyzer = pretokenized
    matrix = tfidf.fit_transform(documents)
    tfidf.analyzer = partial(analyze, language=language)
    fitted = {}
    for level in levels:
        y = ratings == level
        fitted[level] = {}
        for model, parameters in GRID.items():
            def ap(param):
                prediction = scores[level, model, param]
                keep = np.isfinite(prediction)
                return float(average_precision_score(y[keep], prediction[keep])) if len(np.unique(y[keep])) == 2 else -1.0

            param = max(parameters, key=ap)
            prediction = scores[level, model, param]
            keep = np.isfinite(prediction)
            threshold = best_threshold(y[keep], prediction[keep]) if ap(param) >= 0 else 0.5
            estimator = fit_classifier(model, param, matrix, y)
            pipeline = Pipeline([("tfidf", tfidf), ("classifier", estimator)])
            fitted[level][model] = (pipeline, {
                "parameter": param, "threshold": threshold, "cv_ap": max(-1.0, ap(param)),
                "cv_rows": int(keep.sum()),
            })
    return tfidf, matrix, fitted


def feature_digest(pipeline):
    names = pipeline.named_steps["tfidf"].get_feature_names_out()
    return hashlib.sha256("\0".join(names).encode()).hexdigest()


def save_model(path, pipeline, metadata):
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        **metadata, "sklearn_version": sklearn.__version__,
        "python_version": sys.version.split()[0], "classes": [0, 1],
        "feature_sha256": feature_digest(pipeline),
    }
    temporary = path.with_suffix(".tmp")
    joblib.dump({"pipeline": pipeline, "metadata": metadata}, temporary, compress=3)
    temporary.replace(path)


def verify_models(paths_and_samples):
    payload = []
    for path, pipeline, threshold, sample in paths_and_samples:
        probabilities = pipeline.predict_proba(sample)
        payload.append({
            "path": str(path), "text": list(sample), "probabilities": probabilities.tolist(),
            "classes": pipeline.classes_.astype(int).tolist(),
            "prediction": (probabilities[:, 1] >= threshold).astype(int).tolist(),
            "feature_sha256": feature_digest(pipeline),
        })
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "verification.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), str(path)],
            check=True, env={**os.environ, "PYTHONUTF8": "1"},
        )


def verify_saved(payload):
    for expected in payload:
        bundle = joblib.load(expected["path"])
        pipeline, metadata = bundle["pipeline"], bundle["metadata"]
        probabilities = pipeline.predict_proba(expected["text"])
        np.testing.assert_allclose(probabilities, expected["probabilities"], atol=1e-12, rtol=1e-12)
        np.testing.assert_array_equal(pipeline.classes_.astype(int), expected["classes"])
        np.testing.assert_array_equal(probabilities[:, 1] >= metadata["threshold"], expected["prediction"])
        assert feature_digest(pipeline) == expected["feature_sha256"] == metadata["feature_sha256"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("verification", type=Path)
    args = parser.parse_args()
    verify_saved(json.loads(args.verification.read_text(encoding="utf-8")))
