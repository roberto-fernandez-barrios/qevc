"""Predeclared data partitions with stored indices (spec §10).

Partition roles are fixed by the spec: train / source-val / nominal-test /
auditor-dev / final-eval. Splits are produced once per seed from a declared
fraction spec, saved as JSON (indices + provenance), and reloaded everywhere —
no experiment ever re-splits ad hoc. The final-eval partition is quarantined:
loading it requires an explicit acknowledgement flag so accidental use fails.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROLES = ("train", "source_val", "nominal_test", "auditor_dev", "final_eval")


@dataclass(frozen=True)
class SplitSpec:
    fractions: dict[str, float]
    seed: int
    stratify: bool = True

    def __post_init__(self) -> None:
        if set(self.fractions) != set(ROLES):
            raise ValueError(f"fractions must cover exactly {ROLES}")
        if any(f <= 0 for f in self.fractions.values()):
            raise ValueError("all fractions must be positive")
        if abs(sum(self.fractions.values()) - 1.0) > 1e-9:
            raise ValueError("fractions must sum to 1")


def make_splits(n: int, spec: SplitSpec, y: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Deterministic (seeded), optionally label-stratified partition of range(n)."""
    if spec.stratify and y is None:
        raise ValueError("stratified split requires labels")
    rng = np.random.default_rng(spec.seed)

    def _partition(idx: np.ndarray) -> dict[str, np.ndarray]:
        idx = rng.permutation(idx)
        out: dict[str, np.ndarray] = {}
        start = 0
        for i, role in enumerate(ROLES):
            if i == len(ROLES) - 1:
                out[role] = idx[start:]
            else:
                k = int(round(spec.fractions[role] * len(idx)))
                out[role] = idx[start : start + k]
                start += k
        return out

    if not spec.stratify:
        return _partition(np.arange(n))

    y = np.asarray(y)
    if len(y) != n:
        raise ValueError("labels length mismatch")
    parts: dict[str, list[np.ndarray]] = {r: [] for r in ROLES}
    for cls in np.unique(y):
        for role, idx in _partition(np.flatnonzero(y == cls)).items():
            parts[role].append(idx)
    return {r: np.sort(np.concatenate(v)) for r, v in parts.items()}


def save_splits(splits: dict[str, np.ndarray], spec: SplitSpec, path: str | Path) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists — splits are immutable once written")
    payload = {
        "spec": {"fractions": spec.fractions, "seed": spec.seed, "stratify": spec.stratify},
        "indices": {r: np.asarray(v).tolist() for r, v in splits.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def load_splits(path: str | Path, touch_final_eval: bool = False) -> dict[str, np.ndarray]:
    """Load stored splits. ``final_eval`` stays sealed unless explicitly requested.

    The quarantine (spec §10: "final untouched evaluation environments") makes
    accidental use of the final partition a hard error rather than a silent
    leak; passing ``touch_final_eval=True`` is a logged, greppable act.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {r: np.asarray(v, dtype=int) for r, v in data["indices"].items()}
    if not touch_final_eval:
        out.pop("final_eval")
    disjoint = [set(v.tolist()) for v in out.values()]
    if sum(len(s) for s in disjoint) != len(set().union(*disjoint)):
        raise ValueError("stored splits overlap — file corrupted")
    return out
