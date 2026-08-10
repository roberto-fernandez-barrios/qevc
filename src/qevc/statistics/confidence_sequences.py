"""Anytime-valid confidence sequences for bounded means.

Statistical backbone of the conditional auditor (SAP §3, decision D-005).

A confidence sequence (CS) is a sequence of intervals [L_t, U_t] such that

    P( ∃ t ≥ 1 : mu ∉ [L_t, U_t] ) ≤ alpha,

i.e. coverage holds *uniformly over time*. This makes inference valid at any
data-dependent stopping time — in particular at n*, the first label count at
which an audit claim resolves.

Implemented:

- ``hoeffding_cs``      : time-uniform Hoeffding CS (loose, variance-agnostic).
- ``empirical_bernstein_cs`` : predictable plug-in empirical-Bernstein CS of
  Waudby-Smith & Ramdas (JRSS-B 2023), Theorem 2 — variance-adaptive, the
  auditor's default.
- ``clopper_pearson``   : fixed-n exact binomial interval (NOT anytime-valid);
  used only for comparison tables, never for sequential decisions.

All observations must lie in [0, 1]; rescale metrics before calling.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as _sps


@dataclass(frozen=True)
class ConfidenceSequence:
    """Lower/upper bounds after each observation (index t = 1..n)."""

    lower: np.ndarray
    upper: np.ndarray
    alpha: float
    method: str

    def __post_init__(self) -> None:
        if self.lower.shape != self.upper.shape:
            raise ValueError("lower/upper shape mismatch")

    @property
    def n(self) -> int:
        return len(self.lower)

    def running_intersection(self) -> "ConfidenceSequence":
        """Intersect intervals over time.

        Valid because the mean is fixed: if every interval contains mu with
        probability 1-alpha simultaneously, so does their running intersection.
        Yields monotone (tightening) bounds.
        """
        return ConfidenceSequence(
            lower=np.maximum.accumulate(self.lower),
            upper=np.minimum.accumulate(self.upper),
            alpha=self.alpha,
            method=self.method + "+intersection",
        )


def _validate(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or len(x) == 0:
        raise ValueError("x must be a non-empty 1-D array")
    if np.any(~np.isfinite(x)) or np.any(x < 0.0) or np.any(x > 1.0):
        raise ValueError("observations must be finite and in [0, 1]")
    return x


def hoeffding_cs(x: np.ndarray, alpha: float = 0.05) -> ConfidenceSequence:
    """Time-uniform Hoeffding CS via stitched boundary.

    Uses the polynomial stitching bound of Howard et al. (2021) with default
    stitching parameters (eta = 2, s = 1.4), giving a boundary

        u(t) = 1.7 * sqrt( (log log(2t) + 0.72 * log(5.2/alpha)) / t ).

    Loose but assumption-light; serves as a sanity ceiling for the EB CS.
    """
    x = _validate(x)
    t = np.arange(1, len(x) + 1, dtype=float)
    mean = np.cumsum(x) / t
    radius = 1.7 * np.sqrt((np.log(np.log(2.0 * t)) + 0.72 * np.log(5.2 / alpha)) / t)
    return ConfidenceSequence(
        lower=np.clip(mean - radius, 0.0, 1.0),
        upper=np.clip(mean + radius, 0.0, 1.0),
        alpha=alpha,
        method="hoeffding-stitched",
    )


def empirical_bernstein_cs(
    x: np.ndarray,
    alpha: float = 0.05,
    lambda_max: float = 0.5,
) -> ConfidenceSequence:
    """Predictable plug-in empirical-Bernstein CS (Waudby-Smith & Ramdas 2023).

    For X_t in [0,1] with mean mu, define predictable estimates

        muhat_t = (1/2 + sum_{i<=t} X_i) / (t + 1)
        sighat_t^2 = (1/4 + sum_{i<=t} (X_i - muhat_i)^2) / (t + 1)
        lambda_t = min( sqrt( 2 log(2/alpha) / (sighat_{t-1}^2 t log(1+t)) ),
                        lambda_max )
        v_t = 4 (X_t - muhat_{t-1})^2
        psi_E(lam) = (-log(1 - lam) - lam) / 4

    Then with S_t = sum lambda_i X_i, W_t = sum lambda_i,
    V_t = log(2/alpha) + sum v_i psi_E(lambda_i):

        [ S_t/W_t - V_t/W_t ,  S_t/W_t + V_t/W_t ]

    is a (1-alpha) CS for mu (their Theorem 2). Variance-adaptive: shrinks at
    the Bernstein rate when the stream has low variance, which is exactly the
    regime of accuracy-type audit metrics.
    """
    x = _validate(x)
    if not (0.0 < lambda_max < 1.0):
        raise ValueError("lambda_max must be in (0, 1)")
    n = len(x)
    t = np.arange(1, n + 1, dtype=float)

    muhat = (0.5 + np.cumsum(x)) / (t + 1.0)  # muhat_t, t = 1..n
    # Predictable lag: muhat_{t-1} with muhat_0 = 1/2.
    muhat_prev = np.concatenate(([0.5], muhat[:-1]))
    dev2 = (x - muhat_prev) ** 2  # actually (X_t - muhat_{t-1})^2 used in v_t
    # sighat_t^2 uses (X_i - muhat_i)^2 per the paper's display.
    sighat2 = (0.25 + np.cumsum((x - muhat) ** 2)) / (t + 1.0)
    sighat2_prev = np.concatenate(([0.25], sighat2[:-1]))

    lam = np.sqrt(2.0 * np.log(2.0 / alpha) / (sighat2_prev * t * np.log1p(t)))
    lam = np.minimum(lam, lambda_max)

    v = 4.0 * dev2
    psi = (-np.log1p(-lam) - lam) / 4.0

    weight = np.cumsum(lam)
    center = np.cumsum(lam * x) / weight
    margin = (np.log(2.0 / alpha) + np.cumsum(v * psi)) / weight

    return ConfidenceSequence(
        lower=np.clip(center - margin, 0.0, 1.0),
        upper=np.clip(center + margin, 0.0, 1.0),
        alpha=alpha,
        method="empirical-bernstein-wsr",
    )


def clopper_pearson(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact fixed-n binomial CI. NOT valid under optional stopping.

    Kept for comparison tables only (SAP §3.1); the auditor never uses it to
    resolve sequentially-inspected claims.
    """
    if not 0 <= successes <= n or n <= 0:
        raise ValueError("need 0 <= successes <= n, n > 0")
    lo = 0.0 if successes == 0 else _sps.beta.ppf(alpha / 2, successes, n - successes + 1)
    hi = 1.0 if successes == n else _sps.beta.ppf(1 - alpha / 2, successes + 1, n - successes)
    return float(lo), float(hi)
