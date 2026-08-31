"""Declared PSD diagnostics and repair for finite-shot training Grams.

The finite-shot estimators in :mod:`qevc.kernels.quantum` deliberately retain
entry-wise sampling noise.  A realized symmetric training Gram can therefore
be indefinite even though the ideal fidelity kernel is PSD.  This module
contains the post-campaign, deterministic sensitivity operation used to ask
whether E16's deployment conclusions depend on passing that indefinite matrix
directly to LIBSVM.

Only the training diagonal is loaded.  Off-diagonal training estimates and all
calibration/target cross-Grams remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


DEFAULT_EPSILON_REL = 1e-10
DEFAULT_NEGATIVE_TOL_REL = 1e-10


@dataclass(frozen=True)
class MinimumDiagonalLoading:
    """Result of the declared minimum-diagonal-loading repair."""

    matrix: np.ndarray
    loading: float
    epsilon: float
    lambda_min_before: float
    lambda_min_after: float


def symmetric_eigenvalues(K: np.ndarray) -> np.ndarray:
    """Return the ascending eigenvalues of a finite square symmetric matrix."""
    matrix = np.asarray(K, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("expected a square matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("matrix contains non-finite values")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError("matrix must be symmetric")
    return np.linalg.eigvalsh(0.5 * (matrix + matrix.T))


def spectral_audit(
    K: np.ndarray,
    *,
    negative_tolerance_relative: float = DEFAULT_NEGATIVE_TOL_REL,
) -> dict[str, float | int | None]:
    """Compute the declared spectrum diagnostics for one realized Gram.

    Negative modes are counted below ``-tol``, where
    ``tol = negative_tolerance_relative * max(1, |lambda_max|)``.  Both a
    worst-mode ratio and an aggregate negative-mass fraction are reported.
    The positive-spectrum condition number is descriptive only because the
    unrepaired matrix is indefinite.
    """
    eigenvalues = symmetric_eigenvalues(K)
    lambda_min = float(eigenvalues[0])
    lambda_max = float(eigenvalues[-1])
    scale = max(1.0, abs(lambda_max))
    tolerance = float(negative_tolerance_relative * scale)
    negative = eigenvalues[eigenvalues < -tolerance]
    positive = eigenvalues[eigenvalues > tolerance]
    negative_mass = float(-negative.sum())
    abs_mass = float(np.abs(eigenvalues).sum())
    trace = float(eigenvalues.sum())
    positive_condition = (
        float(lambda_max / positive[0]) if len(positive) and lambda_max > 0 else None
    )
    return {
        "lambda_min": lambda_min,
        "lambda_max": lambda_max,
        "negative_modes": int(len(negative)),
        "negative_mass": negative_mass,
        "negative_mass_fraction": negative_mass / abs_mass if abs_mass else 0.0,
        "negative_mass_trace_ratio": negative_mass / abs(trace) if trace else None,
        "relative_indefiniteness": max(0.0, -lambda_min) / max(abs(lambda_max), 1e-300),
        "positive_spectrum_condition": positive_condition,
        "near_zero_modes": int(np.count_nonzero(np.abs(eigenvalues) <= tolerance)),
        "spectral_tolerance": tolerance,
        "trace": trace,
    }


def minimum_diagonal_loading(
    K: np.ndarray,
    *,
    epsilon_relative: float = DEFAULT_EPSILON_REL,
) -> MinimumDiagonalLoading:
    """Restore positive definiteness with the smallest declared diagonal load.

    For ``epsilon = epsilon_relative * max(1, |lambda_max|)``, apply

    ``K_psd = K + max(0, -lambda_min + epsilon) I``.

    The float64 copy leaves the input untouched and preserves every
    off-diagonal element exactly.  With a strictly positive epsilon, the
    repaired training block is full rank; unchanged cross-kernel columns have
    a coherent out-of-sample linear extension through that training span.
    """
    matrix = np.asarray(K, dtype=np.float64)
    eigenvalues = symmetric_eigenvalues(matrix)
    lambda_min = float(eigenvalues[0])
    lambda_max = float(eigenvalues[-1])
    epsilon = float(epsilon_relative * max(1.0, abs(lambda_max)))
    loading = float(max(0.0, -lambda_min + epsilon))
    repaired = matrix.copy()
    repaired.flat[:: repaired.shape[0] + 1] += loading
    lambda_min_after = float(np.linalg.eigvalsh(repaired)[0])
    return MinimumDiagonalLoading(
        matrix=repaired,
        loading=loading,
        epsilon=epsilon,
        lambda_min_before=lambda_min,
        lambda_min_after=lambda_min_after,
    )
