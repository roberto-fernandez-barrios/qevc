"""Kernel-geometry observatory (spec §12).

Label-free and label-aware descriptors of kernel matrices, used as *risk
sensors* (never certificates) in information sets I0/I1. All functions take
dense Gram matrices; quantum and classical kernels are treated identically.

Conventions:
- ``K_ss``: source-source Gram (n_s × n_s), symmetric PSD up to estimation noise.
- ``K_tt``: target-target Gram (n_t × n_t).
- ``K_st``: source-target cross Gram (n_s × n_t).
- ``y``: ±1 labels where a label-aware descriptor applies (source labels only —
  target labels are never available at I0/I1).
"""

from __future__ import annotations

import numpy as np


def _sym(K: np.ndarray) -> np.ndarray:
    K = np.asarray(K, dtype=float)
    if K.ndim != 2 or K.shape[0] != K.shape[1]:
        raise ValueError("expected a square Gram matrix")
    return 0.5 * (K + K.T)


def _center(K: np.ndarray) -> np.ndarray:
    n = K.shape[0]
    H = np.eye(n) - np.full((n, n), 1.0 / n)
    return H @ K @ H


def eigenspectrum(K: np.ndarray) -> np.ndarray:
    """Descending eigenvalues, clipped at 0 (estimation noise can break PSD)."""
    w = np.linalg.eigvalsh(_sym(K))[::-1]
    return np.clip(w, 0.0, None)


def effective_rank(K: np.ndarray) -> float:
    """exp(spectral entropy) of the normalized eigenvalue distribution."""
    w = eigenspectrum(K)
    s = w.sum()
    if s <= 0:
        return 0.0
    p = w / s
    p = p[p > 0]
    return float(np.exp(-(p * np.log(p)).sum()))


def spectral_entropy(K: np.ndarray) -> float:
    w = eigenspectrum(K)
    s = w.sum()
    if s <= 0:
        return 0.0
    p = w / s
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def psd_violation(K: np.ndarray) -> float:
    """Magnitude of most-negative eigenvalue relative to largest (0 if PSD)."""
    w = np.linalg.eigvalsh(_sym(K))
    top = max(abs(w[-1]), 1e-300)
    return float(max(0.0, -w[0]) / top)


def cka(K1: np.ndarray, K2: np.ndarray) -> float:
    """Centered kernel alignment between two Grams on the SAME points."""
    K1c, K2c = _center(_sym(K1)), _center(_sym(K2))
    num = float((K1c * K2c).sum())
    den = float(np.linalg.norm(K1c) * np.linalg.norm(K2c))
    return num / den if den > 0 else 0.0


def kernel_target_alignment(K: np.ndarray, y: np.ndarray) -> float:
    """Centered alignment between K and the ideal label kernel yyᵀ."""
    y = np.asarray(y, dtype=float)
    if set(np.unique(y)) - {-1.0, 1.0}:
        raise ValueError("labels must be ±1")
    return cka(K, np.outer(y, y))


def mean_similarity_shift(K_ss: np.ndarray, K_st: np.ndarray, K_tt: np.ndarray) -> dict[str, float]:
    """First-order shift diagnostics between source and target similarity mass.

    ``mmd2`` is the (biased, V-statistic) squared Maximum Mean Discrepancy in
    the kernel's RKHS — the canonical label-free two-sample shift measure.
    """
    m_ss = float(np.mean(K_ss))
    m_tt = float(np.mean(K_tt))
    m_st = float(np.mean(K_st))
    return {
        "mean_kss": m_ss,
        "mean_ktt": m_tt,
        "mean_kst": m_st,
        "mmd2": m_ss + m_tt - 2.0 * m_st,
    }


def class_geometry(K_ss: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """Within/between-class similarity and RKHS centroid separation (source)."""
    y = np.asarray(y)
    pos, neg = y == 1, y == -1
    if pos.sum() == 0 or neg.sum() == 0:
        raise ValueError("need both classes present")
    K = _sym(K_ss)
    k_pp = float(np.mean(K[np.ix_(pos, pos)]))
    k_nn = float(np.mean(K[np.ix_(neg, neg)]))
    k_pn = float(np.mean(K[np.ix_(pos, neg)]))
    # ||mu_+ - mu_-||^2 in RKHS
    centroid_sep2 = k_pp + k_nn - 2.0 * k_pn
    return {
        "within_pos": k_pp,
        "within_neg": k_nn,
        "between": k_pn,
        "rkhs_centroid_sep2": centroid_sep2,
    }


def describe_environment(
    K_ss: np.ndarray,
    K_tt: np.ndarray,
    K_st: np.ndarray,
    y_source: np.ndarray | None = None,
    top_eigs: int = 10,
) -> dict[str, float]:
    """Full I1-level descriptor vector G_θ for one (kernel, environment) pair.

    Uses only: source data, unlabeled target data, and source labels if given.
    """
    g: dict[str, float] = {}
    w_ss, w_tt = eigenspectrum(K_ss), eigenspectrum(K_tt)
    g["eff_rank_ss"] = effective_rank(K_ss)
    g["eff_rank_tt"] = effective_rank(K_tt)
    g["eff_rank_ratio"] = g["eff_rank_tt"] / max(g["eff_rank_ss"], 1e-12)
    g["spec_entropy_ss"] = spectral_entropy(K_ss)
    g["spec_entropy_tt"] = spectral_entropy(K_tt)
    g["psd_violation_tt"] = psd_violation(K_tt)
    s_ss, s_tt = max(w_ss.sum(), 1e-300), max(w_tt.sum(), 1e-300)
    for i in range(min(top_eigs, len(w_ss))):
        g[f"eig{i}_frac_ss"] = float(w_ss[i] / s_ss)
        g[f"eig{i}_frac_tt"] = float(w_tt[i] / s_tt)
    g.update(mean_similarity_shift(K_ss, K_st, K_tt))
    if y_source is not None:
        g["kta_source"] = kernel_target_alignment(K_ss, np.asarray(y_source))
        g.update({f"class_{k}": v for k, v in class_geometry(K_ss, y_source).items()})
    return g
