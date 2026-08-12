"""Weighted anytime-valid certification (E13; D-019).

Implements ``docs/weighted_certification_spec.md`` exactly. Estimands are
ratios R = E[u·c] / E[u] over uniform-with-replacement draws from a finite
audited population, where c ∈ {0,1} is per-event correctness and u ≥ 0 is a
bounded "mask-weight" (u = w for weighted accuracy; u = w·1[y=1] for TPR_w;
u = w·1[y=0] for TNR_w). Per-event weights are revealed only at labeling
time (they are label-equivalent in this benchmark — see spec §2).

Primary machinery — the one-sample reduction (spec §3.1): for a claim
R ≥ τ, the transformed increment

    Z_i(τ) = ( u_i (c_i − τ) + τ · w_max ) / w_max  ∈ [0, 1]

satisfies  R ≥ τ  ⟺  E[Z(τ)] ≥ τ,  so the existing empirical-Bernstein CS
applies verbatim and the D-006 decision rule is inherited unchanged. With
u ≡ 1, w_max = 1 the stream is *identically* the unweighted correctness
stream — the weighted machinery strictly generalizes D-014.

Secondary machinery — the simultaneous-in-τ ratio CS (spec §3.2) via α/2
CSs on numerator and denominator means, and the conservative BA_w component
bound (spec §3.3).

w_max must be a NONRANDOM, predeclared upper bound on u (spec §3.4);
looseness costs efficiency, never validity.
"""

from __future__ import annotations

import numpy as np

from qevc.auditing.claims import Claim, Resolution, Verdict, resolve_claim
from qevc.statistics.confidence_sequences import (
    ConfidenceSequence,
    empirical_bernstein_cs,
)


def _validate_inputs(correct: np.ndarray, u: np.ndarray, tau: float,
                     w_max: float) -> tuple[np.ndarray, np.ndarray]:
    correct = np.asarray(correct, dtype=float)
    u = np.asarray(u, dtype=float)
    if correct.ndim != 1 or len(correct) == 0 or correct.shape != u.shape:
        raise ValueError("correct/u must be equal-length non-empty 1-D arrays")
    if not np.all(np.isin(correct, (0.0, 1.0))):
        raise ValueError("correct must be binary {0,1}")
    if np.any(~np.isfinite(u)) or np.any(u < 0.0):
        raise ValueError("u must be finite and non-negative")
    if not np.isfinite(w_max) or w_max <= 0.0:
        raise ValueError("w_max must be a positive finite predeclared bound")
    if np.any(u > w_max * (1.0 + 1e-12)):
        raise ValueError("observed u exceeds the predeclared bound w_max — "
                         "the guarantee would be void (spec §3.4)")
    if not 0.0 <= tau <= 1.0:
        raise ValueError("tau must be in [0, 1]")
    return correct, u


def weighted_claim_stream(correct: np.ndarray, u: np.ndarray, tau: float,
                          w_max: float) -> np.ndarray:
    """Z_i(τ) = (u_i(c_i − τ) + τ·w_max) / w_max ∈ [0,1] (spec §3.1).

    Draws with u_i = 0 (events outside the component mask) contribute exactly
    τ — neutral by construction.
    """
    correct, u = _validate_inputs(correct, u, tau, w_max)
    z = (u * (correct - tau) + tau * w_max) / w_max
    # Numerical guard only; the transform is in [0,1] by algebra.
    return np.clip(z, 0.0, 1.0)


def resolve_weighted_claim(correct: np.ndarray, u: np.ndarray, tau: float,
                           w_max: float, alpha: float = 0.05,
                           heuristic_alarm: bool = False) -> Resolution:
    """Fail-closed verdict for the ratio claim R ≥ τ (primary path).

    Exactly the D-006 rule on the Z-stream: SUPPORTED ⟺ lower CS bound on
    E[Z(τ)] ≥ τ; REFUTED ⟺ upper < τ; else UNRESOLVED. Time-uniform, so n*
    is a legitimate stopping time; the heuristic alarm can only demote
    SUPPORTED → UNRESOLVED.
    """
    z = weighted_claim_stream(correct, u, tau, w_max)
    cs = empirical_bernstein_cs(z, alpha=alpha)
    return resolve_claim(Claim("weighted_ratio", tau), cs,
                         heuristic_alarm=heuristic_alarm)


def weighted_ratio_cs(correct: np.ndarray, u: np.ndarray, w_max: float,
                      alpha: float = 0.05) -> ConfidenceSequence:
    """Simultaneous-in-τ CS for R = E[u·c]/E[u] (secondary, spec §3.2).

    α/2 empirical-Bernstein CSs on the numerator mean E[u·c]/w_max and the
    denominator mean E[u]/w_max, combined by union bound:

        [ L_N / U_D , U_N / L_D ]  (clipped to [0,1]; upper = 1 while the
        denominator lower bound is still 0)

    Strictly more conservative than the one-sample reduction per claim; used
    descriptively (landscapes), never preferred for verdicts.
    """
    correct, u = _validate_inputs(correct, u, 0.0, w_max)
    num = empirical_bernstein_cs(u * correct / w_max, alpha=alpha / 2.0)
    den = empirical_bernstein_cs(u / w_max, alpha=alpha / 2.0)
    n_i, d_i = num.running_intersection(), den.running_intersection()
    with np.errstate(divide="ignore", invalid="ignore"):
        lower = np.where(d_i.upper > 0.0, n_i.lower / d_i.upper, 0.0)
        upper = np.where(d_i.lower > 0.0, n_i.upper / d_i.lower, 1.0)
    return ConfidenceSequence(
        lower=np.clip(lower, 0.0, 1.0),
        upper=np.clip(upper, 0.0, 1.0),
        alpha=alpha,
        method="weighted-ratio-eb(union)",
    )


def resolve_ba_claim(correct: np.ndarray, y: np.ndarray, w: np.ndarray,
                     tau: float, w_max: float, alpha: float = 0.05,
                     heuristic_alarm: bool = False) -> Resolution:
    """Conservative verdict for BA_w ≥ τ via component bounds (spec §3.3).

    TPR_w and TNR_w each get a simultaneous ratio CS at α/2; the BA_w bound
    is the average of the component bounds (valid uniformly in t by union).
    Registered as strictly conservative — its measured cost is an E13 output.
    """
    y = np.asarray(y)
    if not np.all(np.isin(y, (0, 1))):
        raise ValueError("y must be binary {0,1}")
    w = np.asarray(w, dtype=float)
    u_pos = w * (y == 1)
    u_neg = w * (y == 0)
    cs_pos = weighted_ratio_cs(correct, u_pos, w_max, alpha=alpha / 2.0)
    cs_neg = weighted_ratio_cs(correct, u_neg, w_max, alpha=alpha / 2.0)
    ba = ConfidenceSequence(
        lower=(cs_pos.lower + cs_neg.lower) / 2.0,
        upper=(cs_pos.upper + cs_neg.upper) / 2.0,
        alpha=alpha,
        method="ba-weighted-component(union)",
    )
    return resolve_claim(Claim("ba_weighted", tau), ba,
                         heuristic_alarm=heuristic_alarm)


def resolve_ba_presplit(correct: np.ndarray, y: np.ndarray, w: np.ndarray,
                        tau_pos: float, tau_neg: float,
                        w_max_pos: float, w_max_neg: float,
                        alpha: float = 0.05,
                        heuristic_alarm: bool = False
                        ) -> tuple[Resolution, Resolution, Resolution]:
    """Pre-split component allocation for BA_w (spec §4c; E13v2).

    Predeclared component thresholds (τ₁, τ₂) with (τ₁+τ₂)/2 = τ_BA, α/2
    per component, each component certified through the sharp §3.1
    one-sample reduction with its own predeclared per-class bound
    (w_max_pos for u = w·1[y=1]; w_max_neg for u = w·1[y=0]).

    Verdict rule (spec §4c): SUPPORTED iff both components certify;
    REFUTED iff both refute; UNRESOLVED otherwise. False certification
    and false refutation are each ≤ α by Theorem 1 per component plus
    the union bound (validity proposition, spec §4c).

    Returns (ba_resolution, tpr_resolution, tnr_resolution); the BA
    resolution's n* is the first draw at which BOTH components had
    resolved (running intersections are monotone, so component verdicts
    never un-resolve).
    """
    y = np.asarray(y)
    if not np.all(np.isin(y, (0, 1))):
        raise ValueError("y must be binary {0,1}")
    w = np.asarray(w, dtype=float)
    u_pos = w * (y == 1)
    u_neg = w * (y == 0)
    r_pos = resolve_weighted_claim(correct, u_pos, tau_pos, w_max_pos,
                                   alpha=alpha / 2.0,
                                   heuristic_alarm=heuristic_alarm)
    r_neg = resolve_weighted_claim(correct, u_neg, tau_neg, w_max_neg,
                                   alpha=alpha / 2.0,
                                   heuristic_alarm=heuristic_alarm)
    tau_ba = (tau_pos + tau_neg) / 2.0
    if (r_pos.verdict is r_neg.verdict
            and r_pos.verdict is not Verdict.UNRESOLVED):
        verdict = r_pos.verdict
        n_star = max(r_pos.n_star, r_neg.n_star)
    else:
        verdict, n_star = Verdict.UNRESOLVED, None
    # The BA verdict is threshold-wise (spec §4c); the component Z-scale
    # bounds live on different w_max scales and average to no valid BA_w
    # interval, so the combined resolution carries the vacuous [0, 1] —
    # interval information lives in the component resolutions.
    ba = Resolution(
        claim=Claim("ba_weighted_presplit", tau_ba),
        verdict=verdict,
        n_used=r_pos.n_used,
        lower=0.0,
        upper=1.0,
        n_star=n_star,
        vetoed=r_pos.vetoed or r_neg.vetoed,
    )
    return ba, r_pos, r_neg


def effective_sample_size_ratio(u: np.ndarray) -> float:
    """ESS/n = (Σu)² / (n·Σu²) — the weight-dispersion diagnostic the n*
    inflation is expected to track (spec §5.4)."""
    u = np.asarray(u, dtype=float)
    s1, s2 = u.sum(), (u * u).sum()
    if s2 == 0.0:
        return 0.0
    return float(s1 * s1 / (len(u) * s2))
