"""Shared model utilities: training weights, calibration, thresholds (D-012).

All models expose a uniform contract:
- ``fit(X, y, sample_weight)`` — sample_weight is the TRAINING weight
  (class-balanced physical weights, D-012);
- ``scores(X)`` — monotone signal-likeness scores (higher = more signal).

Evaluation always uses raw physical weights, never the training weights.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


def class_balanced_weights(y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Physical weights rescaled so both classes carry equal total mass and the
    overall mean weight is 1 (sum = n).

    Mean-1 normalization matters: gradient-boosting split criteria
    (min_child_weight) and SVM regularization (C · w_i) are NOT scale-invariant
    in the weights — weights summing to O(1) silently cripple both.
    """
    y = np.asarray(y)
    w = np.asarray(w, dtype=float)
    out = w.copy()
    for cls in (0, 1):
        mask = y == cls
        total = w[mask].sum()
        if total <= 0:
            raise ValueError(f"class {cls} has no weight mass")
        out[mask] *= 0.5 / total
    return out * len(y)


def weighted_resample_indices(w: np.ndarray, n: int, seed: int) -> np.ndarray:
    """Weight-proportional resampling (for estimators without sample_weight)."""
    w = np.asarray(w, dtype=float)
    rng = np.random.default_rng(seed)
    return rng.choice(len(w), size=n, replace=True, p=w / w.sum())


class PlattCalibrator:
    """Weighted sigmoid calibration: P(y=1|s) = σ(a·s + b).

    Fitted on source-validation data only (never test); turns arbitrary
    monotone scores into probabilities so calibration metrics (ECE, Brier)
    are comparable across model families.
    """

    def __init__(self) -> None:
        self._lr: LogisticRegression | None = None

    def fit(self, scores, y, sample_weight=None) -> "PlattCalibrator":
        s = np.asarray(scores, dtype=float).reshape(-1, 1)
        self._lr = LogisticRegression(C=1e6, max_iter=1000)
        self._lr.fit(s, np.asarray(y), sample_weight=sample_weight)
        return self

    def predict_proba(self, scores) -> np.ndarray:
        if self._lr is None:
            raise RuntimeError("calibrator used before fit")
        s = np.asarray(scores, dtype=float).reshape(-1, 1)
        return self._lr.predict_proba(s)[:, 1]


def ba_optimal_threshold(y, prob, sample_weight, n_grid: int = 200) -> float:
    """Threshold maximizing weighted balanced accuracy on validation data."""
    from qevc.metrics.classifier import weighted_balanced_accuracy

    prob = np.asarray(prob, dtype=float)
    cand = np.unique(np.quantile(prob, np.linspace(0.01, 0.99, n_grid)))
    best_t, best_ba = 0.5, -np.inf
    for t in cand:
        pred = (prob >= t).astype(float)
        if pred.min() == pred.max():
            continue
        ba = weighted_balanced_accuracy(y, pred, sample_weight)
        if ba > best_ba:
            best_ba, best_t = ba, float(t)
    return best_t
