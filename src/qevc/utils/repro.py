"""Reproducibility primitives (spec §25).

Every experiment run produces an immutable JSON manifest under
``results/manifests/`` recording: git commit, config hash, dataset hashes,
seed, package versions, platform, timing, and declared output artifacts.
Manifests are append-only: writing over an existing manifest path raises.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from dataclasses import dataclass, field
from importlib import metadata as _im
from pathlib import Path
from typing import Any

_TRACKED_PACKAGES = (
    "numpy", "scipy", "pandas", "scikit-learn", "xgboost", "lightgbm",
    "qiskit", "qiskit-machine-learning", "qiskit-aer", "qiskit-ibm-runtime",
)


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no whitespace variance."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def config_hash(config: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(config).encode()).hexdigest()


def file_sha256(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def git_commit(repo_root: str | Path | None = None) -> str:
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def git_is_dirty(repo_root: str | Path | None = None) -> bool:
    """Dirtiness of the CODE state (code/configs/docs), excluding run outputs.

    A run writing its own outputs under ``results/`` must not make the
    recorded commit ambiguous about the code that produced them (D-016);
    everything else counting as dirty is exactly the point.
    """
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", ".", ":(exclude)results"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return bool(out.stdout.strip())


def package_versions() -> dict[str, str]:
    versions: dict[str, str] = {"python": platform.python_version()}
    for pkg in _TRACKED_PACKAGES:
        try:
            versions[pkg] = _im.version(pkg)
        except _im.PackageNotFoundError:
            pass
    return versions


@dataclass
class RunManifest:
    """Immutable record of one experiment run."""

    experiment_id: str
    config: dict[str, Any]
    seed: int
    dataset_hashes: dict[str, str] = field(default_factory=dict)
    backend: dict[str, Any] = field(default_factory=dict)  # QPU/simulator metadata
    outputs: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def finalize(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.finished_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        dirty = git_is_dirty()
        return {
            "experiment_id": self.experiment_id,
            "git_commit": git_commit(),
            "git_dirty": dirty,
            "config": self.config,
            "config_hash": config_hash(self.config),
            "seed": self.seed,
            "dataset_hashes": self.dataset_hashes,
            "backend": self.backend,
            "package_versions": package_versions(),
            "platform": platform.platform(),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "wall_seconds": (
                None if self.finished_at is None else self.finished_at - self.started_at
            ),
            "outputs": self.outputs,
        }

    def write(self, manifests_dir: str | Path) -> Path:
        d = self.to_dict()
        if d["git_dirty"]:
            # Allowed during development; final paper runs must be clean.
            d["warning"] = "git working tree dirty at run time"
        name = (f"{self.experiment_id}_{d['config_hash'][:12]}_seed{self.seed}"
                f"_{int(self.started_at)}.json")  # re-runs get their own manifest
        path = Path(manifests_dir) / name
        if path.exists():
            raise FileExistsError(
                f"manifest {path} already exists — manifests are immutable; "
                "change the config or seed instead of overwriting"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")
        return path
