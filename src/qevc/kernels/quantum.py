"""Quantum fidelity kernels: exact, finite-shot, and (later) hardware.

Kernel definition (spec §9):

    K_Q(x, y) = |<phi(x)|phi(y)>|^2,   |phi(x)> = U(x)|0>

The SAME parameterized circuit U(x) drives all three estimation regimes
(statevector-exact, Aer shot-based via compute–uncompute, QPU), so spec §18–19
comparisons isolate *estimation* effects from *model* effects.

Feature map: Havlicek-style ZZ map (single-qubit RZ data rotations inside
Hadamard layers + pairwise ZZ entanglers), with

- ``reps``: encoding repetitions (depth control);
- ``entanglement``: 'linear' | 'full' | 'none';
- ``scale``: global bandwidth prefactor on the encoded angles. This is the
  kernel-bandwidth knob (Canatar et al.): without it, fidelity kernels
  concentrate as dimension grows and the Gram matrix degenerates.

One qubit per feature; inputs are expected standardized (approx. in [-π, π]
after scaling — the preprocessing pipeline enforces this and it is checked).
"""

from __future__ import annotations

import itertools

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def build_feature_map(
    n_features: int,
    reps: int = 2,
    entanglement: str = "linear",
    scale: float = 1.0,
) -> "callable":
    """Return circuit_fn(x) -> QuantumCircuit encoding one sample."""
    if n_features < 1:
        raise ValueError("n_features must be >= 1")
    if entanglement not in ("linear", "full", "none"):
        raise ValueError(f"unknown entanglement: {entanglement}")

    if entanglement == "linear":
        pairs = [(i, i + 1) for i in range(n_features - 1)]
    elif entanglement == "full":
        pairs = list(itertools.combinations(range(n_features), 2))
    else:
        pairs = []

    def circuit_fn(x: np.ndarray) -> QuantumCircuit:
        x = np.asarray(x, dtype=float)
        if x.shape != (n_features,):
            raise ValueError(f"expected shape ({n_features},), got {x.shape}")
        z = scale * x
        qc = QuantumCircuit(n_features)
        for _ in range(reps):
            for q in range(n_features):
                qc.h(q)
                qc.rz(2.0 * z[q], q)
            for i, j in pairs:
                qc.cx(i, j)
                qc.rz(2.0 * z[i] * z[j], j)
                qc.cx(i, j)
        return qc

    circuit_fn.n_features = n_features
    circuit_fn.config = {
        "reps": reps, "entanglement": entanglement, "scale": scale,
        "n_qubits": n_features,
    }
    return circuit_fn


def _statevectors(X: np.ndarray, circuit_fn) -> np.ndarray:
    X = np.atleast_2d(np.asarray(X, dtype=float))
    dim = 2 ** circuit_fn.n_features
    V = np.empty((len(X), dim), dtype=complex)
    for i, x in enumerate(X):
        V[i] = Statevector(circuit_fn(x)).data
    return V


def kernel_exact(X1: np.ndarray, circuit_fn, X2: np.ndarray | None = None) -> np.ndarray:
    """Exact fidelity Gram matrix via statevectors.

    K[i, j] = |<phi(x1_i)|phi(x2_j)>|^2. Symmetric case (X2 None) reuses the
    statevector block. Memory: O(n · 2^q) — fine for the ≤ ~12-qubit regime
    declared feasible in the spec.
    """
    V1 = _statevectors(X1, circuit_fn)
    V2 = V1 if X2 is None else _statevectors(X2, circuit_fn)
    G = V1 @ V2.conj().T
    K = np.abs(G) ** 2
    if X2 is None:
        K = 0.5 * (K + K.T)
        np.fill_diagonal(K, 1.0)
    return K


def kernel_shots(
    X1: np.ndarray,
    circuit_fn,
    shots: int,
    seed: int,
    X2: np.ndarray | None = None,
) -> np.ndarray:
    """Finite-shot estimate of the fidelity kernel (compute–uncompute).

    Each entry is estimated as the empirical frequency of the all-zeros outcome
    of U†(y)U(x)|0>, i.e. Binomial(shots, K_exact)/shots — the exact sampling
    law of the compute–uncompute protocol on a noiseless device. We therefore
    sample directly from that law using the exact fidelity, which is
    numerically identical to simulating the measurement, at a fraction of the
    cost. (Hardware runs in E10 use real executions instead; device noise is
    NOT modeled here — this function isolates pure shot noise, per H6.)

    Estimated Grams are generally NOT PSD: PSD violation is itself a measured
    quantity (spec §18), so no clipping/projection happens here. Projection, if
    used by a model, is a separate declared step.
    """
    if shots < 1:
        raise ValueError("shots must be >= 1")
    rng = np.random.default_rng(seed)
    K = kernel_exact(X1, circuit_fn, X2)
    symmetric = X2 is None
    if not symmetric:
        return rng.binomial(shots, np.clip(K, 0.0, 1.0)) / shots
    n = K.shape[0]
    iu = np.triu_indices(n, k=1)
    est = np.zeros_like(K)
    est[iu] = rng.binomial(shots, np.clip(K[iu], 0.0, 1.0)) / shots
    est = est + est.T
    np.fill_diagonal(est, 1.0)  # K(x,x)=1 exactly; not estimated on hardware either
    return est
