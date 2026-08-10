"""Weighted bootstrap confidence intervals (SAP §5).

Descriptive uncertainty for reported metrics and paired model contrasts.
These are fixed-n, exchangeability-based intervals for *reporting*; they are
never used by the auditor to resolve claims (that is the CS machinery).

Resampling unit: the event. Event weights ride along with resampled indices,
which preserves the weighted-metric estimand under the empirical distribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

MetricFn = Callable[..., float]  # metric(y_true, y_score, sample_weight) -> float


@dataclass(frozen=True)
class BootstrapCI:
    point: float
    lower: float
    upper: float
    alpha: float
    n_resamples: int

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper


def bootstrap_metric(
    metric: MetricFn,
    y_true: np.ndarray,
    y_score: np.ndarray,
    sample_weight: np.ndarray | None = None,
    alpha: float = 0.05,
    n_resamples: int = 10_000,
    seed: int = 0,
) -> BootstrapCI:
    """Percentile bootstrap CI for one metric on one model."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    w = None if sample_weight is None else np.asarray(sample_weight, dtype=float)
    n = len(y_true)
    rng = np.random.default_rng(seed)
    point = metric(y_true, y_score, w)

    stats = np.empty(n_resamples)
    for b in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        try:
            stats[b] = metric(y_true[idx], y_score[idx], None if w is None else w[idx])
        except ValueError:  # degenerate resample (single class)
            stats[b] = np.nan
    stats = stats[~np.isnan(stats)]
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(float(point), float(lo), float(hi), alpha, len(stats))


def paired_bootstrap_diff(
    metric: MetricFn,
    y_true: np.ndarray,
    score_a: np.ndarray,
    score_b: np.ndarray,
    sample_weight: np.ndarray | None = None,
    alpha: float = 0.05,
    n_resamples: int = 10_000,
    seed: int = 0,
) -> BootstrapCI:
    """CI for metric(A) − metric(B) with both models resampled on the SAME
    events — the correct design for two models scored on a shared test set
    (SAP §5: paired contrasts, full CI of the difference, never bare p-values).
    """
    y_true = np.asarray(y_true)
    a = np.asarray(score_a, dtype=float)
    b = np.asarray(score_b, dtype=float)
    w = None if sample_weight is None else np.asarray(sample_weight, dtype=float)
    n = len(y_true)
    rng = np.random.default_rng(seed)
    point = metric(y_true, a, w) - metric(y_true, b, w)

    diffs = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        wi = None if w is None else w[idx]
        try:
            diffs[i] = metric(y_true[idx], a[idx], wi) - metric(y_true[idx], b[idx], wi)
        except ValueError:
            diffs[i] = np.nan
    diffs = diffs[~np.isnan(diffs)]
    lo, hi = np.quantile(diffs, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(float(point), float(lo), float(hi), alpha, len(diffs))
