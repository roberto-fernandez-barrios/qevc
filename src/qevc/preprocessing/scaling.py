"""Feature scaling for quantum angle encoding (spec §8).

``AngleScaler`` maps features to [-scale·π, scale·π] via per-feature robust
quantile ranges. Discipline enforced by construction:

- fitted ONLY on training data (transform refuses before fit);
- jet sentinel values (-25 for absent jets) are excluded from quantile fitting
  and mapped to a fixed encodable constant, not treated as numeric outliers;
- values beyond the fitted quantiles are clipped — deployment data cannot
  stretch the encoding range chosen at training time.

The bandwidth prefactor lives in the feature map (`build_feature_map(scale=…)`),
not here: this class fixes the data window, the kernel fixes the bandwidth.
"""

from __future__ import annotations

import numpy as np

SENTINEL = -25.0


class AngleScaler:
    """Robust per-feature map to [-π, π] with sentinel handling."""

    def __init__(self, q_low: float = 0.005, q_high: float = 0.995,
                 sentinel_angle: float = -np.pi):
        if not 0.0 <= q_low < q_high <= 1.0:
            raise ValueError("need 0 <= q_low < q_high <= 1")
        self.q_low = q_low
        self.q_high = q_high
        self.sentinel_angle = float(sentinel_angle)
        self.lo_: np.ndarray | None = None
        self.hi_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "AngleScaler":
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or len(X) == 0:
            raise ValueError("X must be 2-D and non-empty")
        n_feat = X.shape[1]
        lo = np.empty(n_feat)
        hi = np.empty(n_feat)
        for j in range(n_feat):
            col = X[:, j]
            col = col[col != SENTINEL]
            if len(col) < 10:
                raise ValueError(f"feature {j}: not enough non-sentinel values to fit")
            lo[j], hi[j] = np.quantile(col, [self.q_low, self.q_high])
            if hi[j] <= lo[j]:
                raise ValueError(f"feature {j}: degenerate quantile range")
        self.lo_, self.hi_ = lo, hi
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.lo_ is None:
            raise RuntimeError("AngleScaler used before fit (leakage guard)")
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != len(self.lo_):
            raise ValueError("feature-count mismatch with fitted scaler")
        sent = X == SENTINEL
        Xc = np.clip(X, self.lo_, self.hi_)
        out = (2.0 * (Xc - self.lo_) / (self.hi_ - self.lo_) - 1.0) * np.pi
        out[sent] = self.sentinel_angle
        return out

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)
