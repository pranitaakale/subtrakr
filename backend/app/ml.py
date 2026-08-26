"""Trainable recurring-payment classifier with explainable feature engineering."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "recurring_classifier.joblib"
FEATURE_NAMES = (
    "transaction_count",
    "mean_interval_days",
    "interval_regularness",
    "amount_coefficient_of_variation",
    "cadence_alignment",
    "history_days",
)
CADENCES = np.array([7, 14, 30, 90, 365])


def transaction_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["normalized"]].append(row)
    return groups


def features_for_entries(entries: list[dict[str, Any]]) -> dict[str, float]:
    ordered = sorted(entries, key=lambda item: item["date"])
    amounts = np.array([float(item["amount"]) for item in ordered])
    intervals = np.array([(ordered[i]["date"] - ordered[i - 1]["date"]).days for i in range(1, len(ordered))], dtype=float)
    mean_interval = float(intervals.mean()) if len(intervals) else 365.0
    interval_std = float(intervals.std()) if len(intervals) else 365.0
    nearest_cadence = float(np.min(np.abs(CADENCES - mean_interval)))
    return {
        "transaction_count": float(len(ordered)),
        "mean_interval_days": mean_interval,
        "interval_regularness": float(max(0.0, 1 - interval_std / max(mean_interval, 1))),
        "amount_coefficient_of_variation": float(amounts.std() / max(amounts.mean(), 0.01)),
        "cadence_alignment": float(max(0.0, 1 - nearest_cadence / max(mean_interval, 1))),
        "history_days": float((ordered[-1]["date"] - ordered[0]["date"]).days) if len(ordered) > 1 else 0.0,
    }


def vector(features: dict[str, float]) -> list[float]:
    return [features[name] for name in FEATURE_NAMES]


def weak_label(features: dict[str, float]) -> int:
    """Bootstrap labels from conservative domain rules until human reviews accumulate."""
    return int(
        features["transaction_count"] >= 2
        and features["cadence_alignment"] >= 0.72
        and features["interval_regularness"] >= 0.55
        and features["amount_coefficient_of_variation"] <= 0.25
    )


def _metrics(y_true: list[int], probability: np.ndarray) -> dict[str, float | None]:
    predicted = (probability >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, predicted, average="binary", zero_division=0)
    auc = roc_auc_score(y_true, probability) if len(set(y_true)) == 2 else None
    return {"precision": round(float(precision), 3), "recall": round(float(recall), 3), "f1": round(float(f1), 3), "roc_auc": round(float(auc), 3) if auc is not None else None}


def train(rows: list[dict[str, Any]], reviewed_labels: dict[str, int] | None = None) -> dict[str, Any]:
    reviewed_labels = reviewed_labels or {}
    samples: list[tuple[str, dict[str, float], int, str]] = []
    for merchant, entries in transaction_groups(rows).items():
        if len(entries) < 2:
            continue
        features = features_for_entries(entries)
        label_source = "human" if merchant in reviewed_labels else "weak_supervision"
        samples.append((merchant, features, reviewed_labels.get(merchant, weak_label(features)), label_source))
    if len(samples) < 4 or len({sample[2] for sample in samples}) < 2:
        return {"trained": False, "reason": "Need at least four merchant groups spanning both classes."}
    x = np.array([vector(sample[1]) for sample in samples])
    y = np.array([sample[2] for sample in samples])
    indices = np.arange(len(samples))
    stratify = y if min(np.bincount(y)) >= 2 else None
    train_idx, test_idx = train_test_split(indices, test_size=max(1, round(len(samples) * 0.25)), random_state=42, stratify=stratify)
    pipeline = Pipeline([("scale", StandardScaler()), ("classifier", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))])
    pipeline.fit(x[train_idx], y[train_idx])
    test_probability = pipeline.predict_proba(x[test_idx])[:, 1]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pipeline": pipeline, "feature_names": FEATURE_NAMES, "trained_on": str(date.today()), "sample_count": len(samples), "human_label_count": sum(item[3] == "human" for item in samples), "metrics": _metrics(y[test_idx].tolist(), test_probability)}
    joblib.dump(payload, MODEL_PATH)
    return {"trained": True, **{key: payload[key] for key in ("sample_count", "human_label_count", "metrics")}}


def predict(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not MODEL_PATH.exists() or len(entries) < 2:
        return None
    payload = joblib.load(MODEL_PATH)
    features = features_for_entries(entries)
    probability = float(payload["pipeline"].predict_proba([vector(features)])[0][1])
    return {"probability": round(probability, 3), "features": features, "explanation": explain(features, probability)}


def explain(features: dict[str, float], probability: float) -> list[str]:
    evidence = []
    if features["transaction_count"] >= 3:
        evidence.append(f"{int(features['transaction_count'])} transactions create a reliable history")
    if features["cadence_alignment"] >= 0.75:
        evidence.append("intervals align with a common billing cadence")
    if features["interval_regularness"] >= 0.7:
        evidence.append("payment timing is highly regular")
    if features["amount_coefficient_of_variation"] <= 0.15:
        evidence.append("charge amounts are stable")
    if not evidence:
        evidence.append("timing or amounts are too variable for a strong recurring-payment signal")
    evidence.append(f"classifier probability: {probability:.0%}")
    return evidence[:4]


def model_status() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return {"available": False, "message": "Model will train after enough merchant histories are available."}
    payload = joblib.load(MODEL_PATH)
    return {"available": True, "feature_names": list(payload["feature_names"]), "trained_on": payload["trained_on"], "sample_count": payload["sample_count"], "human_label_count": payload["human_label_count"], "metrics": payload["metrics"]}
