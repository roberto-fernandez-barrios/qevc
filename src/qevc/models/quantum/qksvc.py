"""Quantum-kernel SVC (spec §9) on precomputed fidelity Grams.

Same fit/scores contract as the classical suite. The AngleScaler is fitted
inside ``fit`` on the training rows only (leakage discipline); the kernel is
the exact statevector fidelity kernel by default, with the estimation regime
(exact / finite-shot) selectable so E09 can reuse this class unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.svm import SVC

from qevc.kernels.quantum import build_feature_map, kernel_exact, kernel_shots
from qevc.preprocessing.scaling import AngleScaler


class QKSVC:
    def __init__(
        self,
        C: float = 1.0,
        reps: int = 2,
        entanglement: str = "linear",
        scale: float = 1.0,
        shots: int | None = None,  # None = exact kernel
        seed: int = 0,
    ):
        self.C = C
        self.reps = reps
        self.entanglement = entanglement
        self.scale = scale
        self.shots = shots
        self.seed = seed
        self._scaler: AngleScaler | None = None
        self._fm = None
        self._svc: SVC | None = None
        self._X_train: np.ndarray | None = None
        # D-022: each Gram evaluation draws an INDEPENDENT substream, as a
        # physical device would; deterministic given (seed, call order).
        self._shot_seq = np.random.SeedSequence(seed)

    def _gram(self, A: np.ndarray, B: np.ndarray | None = None) -> np.ndarray:
        if self.shots is None:
            return kernel_exact(A, self._fm, B)
        call_seed = int(self._shot_seq.spawn(1)[0].generate_state(1)[0])
        return kernel_shots(A, self._fm, shots=self.shots, seed=call_seed, X2=B)

    def fit(self, X, y, sample_weight=None) -> "QKSVC":
        X = np.asarray(X, dtype=float)
        self._scaler = AngleScaler().fit(X)
        self._fm = build_feature_map(
            X.shape[1], reps=self.reps, entanglement=self.entanglement,
            scale=self.scale,
        )
        self._X_train = self._scaler.transform(X)
        K = self._gram(self._X_train)
        self._svc = SVC(kernel="precomputed", C=self.C)
        self._svc.fit(K, np.asarray(y), sample_weight=sample_weight)
        return self

    def scores(self, X) -> np.ndarray:
        if self._svc is None:
            raise RuntimeError("model used before fit")
        Z = self._scaler.transform(np.asarray(X, dtype=float))
        K = self._gram(Z, self._X_train)
        return self._svc.decision_function(K)

    @property
    def config(self) -> dict:
        return {
            "C": self.C, "reps": self.reps, "entanglement": self.entanglement,
            "scale": self.scale, "shots": self.shots,
            "n_qubits": None if self._fm is None else self._fm.config["n_qubits"],
        }


QKSVC_SPACE = {
    "C": [0.1, 0.3, 1.0, 3.0, 10.0],
    "reps": [1, 2],
    "scale": [0.25, 0.5, 0.75, 1.0],
    "entanglement": ["linear", "full"],
}


def qksvc_builder(params: dict, seed: int) -> QKSVC:
    return QKSVC(
        C=params["C"], reps=params["reps"], scale=params["scale"],
        entanglement=params["entanglement"], seed=seed,
    )
