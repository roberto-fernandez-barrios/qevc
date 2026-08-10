"""Event-weight-aware classifier metrics (SAP §1.1).

HEP events carry physical weights (cross-section × luminosity / N_generated);
every metric here accepts ``sample_weight`` and treats it as mandatory in
pipeline code (None is allowed only for unit tests / toy data).

All probability inputs are P(signal); labels are {0, 1} with signal = 1.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def _check(y_true, y_score, sample_weight):
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    if y_true.shape != y_score.shape or y_true.ndim != 1:
        raise ValueError("y_true and y_score must be 1-D and same length")
    if set(np.unique(y_true)) - {0, 1}:
        raise ValueError("labels must be in {0, 1}")
    if sample_weight is None:
        w = np.ones_like(y_score)
    else:
        w = np.asarray(sample_weight, dtype=float)
        if w.shape != y_score.shape or np.any(w < 0) or not np.any(w > 0):
            raise ValueError("weights must be non-negative, not all zero, same length")
    return y_true, y_score, w


def weighted_auc(y_true, y_score, sample_weight=None) -> float:
    y, s, w = _check(y_true, y_score, sample_weight)
    return float(roc_auc_score(y, s, sample_weight=w))


def weighted_pr_auc(y_true, y_score, sample_weight=None) -> float:
    y, s, w = _check(y_true, y_score, sample_weight)
    return float(average_precision_score(y, s, sample_weight=w))


def weighted_balanced_accuracy(y_true, y_pred, sample_weight=None) -> float:
    """Mean of weighted TPR and TNR at a fixed operating point."""
    y, p, w = _check(y_true, y_pred, sample_weight)
    if set(np.unique(p)) - {0.0, 1.0}:
        raise ValueError("y_pred must be hard {0,1} decisions at a frozen threshold")
    pos, neg = y == 1, y == 0
    if w[pos].sum() == 0 or w[neg].sum() == 0:
        raise ValueError("both classes need positive weight mass")
    tpr = w[pos & (p == 1)].sum() / w[pos].sum()
    tnr = w[neg & (p == 0)].sum() / w[neg].sum()
    return float(0.5 * (tpr + tnr))


def expected_calibration_error(
    y_true, y_prob, sample_weight=None, n_bins: int = 15
) -> float:
    """Weight-aware ECE with equal-mass bins (SAP §1.1).

    Bins are equal *weight* mass (quantiles of the weighted score
    distribution), which keeps the estimate stable under the long weight tails
    typical of HEP samples.
    """
    y, s, w = _check(y_true, y_prob, sample_weight)
    if np.any((s < 0) | (s > 1)):
        raise ValueError("y_prob must be in [0, 1]")
    order = np.argsort(s)
    y, s, w = y[order], s[order], w[order]
    cw = np.cumsum(w) / w.sum()
    edges = np.searchsorted(cw, np.linspace(0, 1, n_bins + 1)[1:-1], side="left")
    ece = 0.0
    for idx in np.split(np.arange(len(s)), edges):
        if len(idx) == 0 or w[idx].sum() == 0:
            continue
        wb = w[idx].sum()
        conf = np.average(s[idx], weights=w[idx])
        acc = np.average(y[idx], weights=w[idx])
        ece += (wb / w.sum()) * abs(acc - conf)
    return float(ece)


def weighted_brier(y_true, y_prob, sample_weight=None) -> float:
    y, s, w = _check(y_true, y_prob, sample_weight)
    return float(np.average((s - y) ** 2, weights=w))


def metric_suite(y_true, y_prob, threshold: float, sample_weight=None) -> dict[str, float]:
    """Full SAP §1.1 suite at a frozen operating point."""
    y_pred = (np.asarray(y_prob) >= threshold).astype(float)
    return {
        "auc": weighted_auc(y_true, y_prob, sample_weight),
        "pr_auc": weighted_pr_auc(y_true, y_prob, sample_weight),
        "balanced_accuracy": weighted_balanced_accuracy(y_true, y_pred, sample_weight),
        "ece": expected_calibration_error(y_true, y_prob, sample_weight),
        "brier": weighted_brier(y_true, y_prob, sample_weight),
        "threshold": float(threshold),
    }
