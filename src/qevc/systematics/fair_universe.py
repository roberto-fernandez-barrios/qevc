"""FAIR Universe systematic environments D_θ (spec §6, audit §1.4).

Wraps the official `systematics()` from the vendored HEP-Challenge repo
(commit pinned in docs/dataset_audit.md) for feature-level nuisances
(TES / JES / soft MET + official post-selection + DER recompute), and applies
the three normalization nuisances directly on event weights.

The normalization path in the official function is a silent no-op (its guard
tests the misspelled column name `detailedlabel`; audit §1.3, decision D-008),
so this module NEVER passes norm scales to `systematics()` — semantics are
pinned by tests/test_fair_universe_systematics.py either way.

Environment identity: `soft_met > 0` injects seeded Gaussian noise, so the
environment is (θ, seed), not θ alone (audit §4). `Environment.name` encodes
both.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_INGESTION_DIR = _REPO_ROOT / "external" / "HEP-Challenge" / "ingestion_program"

PRI_COLUMNS = [
    "PRI_lep_pt", "PRI_lep_eta", "PRI_lep_phi",
    "PRI_had_pt", "PRI_had_eta", "PRI_had_phi",
    "PRI_jet_leading_pt", "PRI_jet_leading_eta", "PRI_jet_leading_phi",
    "PRI_jet_subleading_pt", "PRI_jet_subleading_eta", "PRI_jet_subleading_phi",
    "PRI_n_jets", "PRI_jet_all_pt", "PRI_met", "PRI_met_phi",
]
DER_COLUMNS = [
    "DER_mass_transverse_met_lep", "DER_mass_vis", "DER_pt_h",
    "DER_deltaeta_jet_jet", "DER_mass_jet_jet", "DER_prodeta_jet_jet",
    "DER_deltar_had_lep", "DER_pt_tot", "DER_sum_pt",
    "DER_pt_ratio_lep_had", "DER_met_phi_centrality", "DER_lep_eta_centrality",
]
PROCESSES = ("htautau", "ztautau", "ttbar", "diboson")

# Official priors (audit §1.2): (nominal, sigma). soft_met has no Gaussian
# sigma (LogNormal prior in the official evaluation); grid values are set
# explicitly in configs instead of via sigma multiples.
NUISANCE_PRIORS = {
    "tes": (1.0, 0.01),
    "jes": (1.0, 0.01),
    "ttbar_scale": (1.0, 0.02),
    "diboson_scale": (1.0, 0.25),
    "bkg_scale": (1.0, 0.001),
}


def _official_systematics():
    if not OFFICIAL_INGESTION_DIR.is_dir():
        raise RuntimeError(
            f"vendored HEP-Challenge repo not found at {OFFICIAL_INGESTION_DIR}; "
            "clone it per docs/dataset_audit.md §1.1"
        )
    path = str(OFFICIAL_INGESTION_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)
    from systematics import systematics  # noqa: PLC0415 (official flat module)

    return systematics


@dataclass(frozen=True)
class Environment:
    """One systematic environment θ (plus seed where θ is stochastic)."""

    tes: float = 1.0
    jes: float = 1.0
    soft_met: float = 0.0
    ttbar_scale: float = 1.0
    diboson_scale: float = 1.0
    bkg_scale: float = 1.0
    seed: int = 31415

    def __post_init__(self) -> None:
        if not (0.9 <= self.tes <= 1.1 and 0.9 <= self.jes <= 1.1):
            raise ValueError("tes/jes outside official clip range [0.9, 1.1]")
        if not (0.0 <= self.soft_met <= 5.0):
            raise ValueError("soft_met outside official clip range [0, 5]")
        if not (0.8 <= self.ttbar_scale <= 1.2):
            raise ValueError("ttbar_scale outside official clip range [0.8, 1.2]")
        if not (0.0 <= self.diboson_scale <= 2.0):
            raise ValueError("diboson_scale outside official clip range [0, 2]")
        if not (0.99 <= self.bkg_scale <= 1.01):
            raise ValueError("bkg_scale outside official clip range [0.99, 1.01]")

    @property
    def is_nominal(self) -> bool:
        return self == Environment(seed=self.seed)

    @property
    def name(self) -> str:
        parts = [
            f"tes{self.tes:g}", f"jes{self.jes:g}", f"soft{self.soft_met:g}",
            f"ttb{self.ttbar_scale:g}", f"dib{self.diboson_scale:g}",
            f"bkg{self.bkg_scale:g}",
        ]
        if self.soft_met > 0:  # stochastic θ ⇒ seed is part of identity
            parts.append(f"seed{self.seed}")
        return "_".join(parts)

    def with_seed(self, seed: int) -> "Environment":
        return replace(self, seed=seed)

    def to_dict(self) -> dict[str, float | int]:
        return {
            "tes": self.tes, "jes": self.jes, "soft_met": self.soft_met,
            "ttbar_scale": self.ttbar_scale, "diboson_scale": self.diboson_scale,
            "bkg_scale": self.bkg_scale, "seed": self.seed,
        }


NOMINAL = Environment()


def split_columns(df: pd.DataFrame) -> dict:
    """Full 31-column frame → official dict structure (PRI-only data).

    DER columns are dropped: they are recomputed from shifted primaries by the
    official pipeline, and keeping stale ones would be a leakage/consistency
    hazard.
    """
    missing = [c for c in PRI_COLUMNS + ["weights", "labels", "detailed_labels"] if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    return {
        "data": df[PRI_COLUMNS].copy(),
        "weights": df["weights"].to_numpy(copy=True),
        "labels": df["labels"].to_numpy(copy=True),
        "detailed_labels": df["detailed_labels"].to_numpy(copy=True),
    }


def _norm_weight_scale(weights, labels, detailed_labels, env: Environment):
    """Normalization nuisances applied directly on weights (audit §1.3)."""
    w = np.asarray(weights, dtype=float).copy()
    dl = np.asarray(detailed_labels)
    y = np.asarray(labels)
    if env.ttbar_scale != 1.0:
        w[dl == "ttbar"] *= env.ttbar_scale
    if env.diboson_scale != 1.0:
        w[dl == "diboson"] *= env.diboson_scale
    if env.bkg_scale != 1.0:
        w[y == 0] *= env.bkg_scale
    return w


def apply_environment(dset: dict, env: Environment) -> dict:
    """Produce D_θ from a nominal dataset dict.

    ``dset`` = {"data": PRI DataFrame, "weights", "labels", "detailed_labels"}.
    Returns the same structure with shifted primaries, recomputed DER features,
    official post-selection applied (rows may drop), and norm-scaled weights.
    """
    for key in ("data", "weights", "labels", "detailed_labels"):
        if key not in dset:
            raise ValueError(f"dset missing key '{key}'")
    official = _official_systematics()
    shifted = official(
        data_set={k: dset[k] for k in ("data", "weights", "labels", "detailed_labels")},
        tes=env.tes,
        jes=env.jes,
        soft_met=env.soft_met,
        seed=env.seed,
        dopostprocess=True,
    )
    shifted["weights"] = _norm_weight_scale(
        shifted["weights"], shifted["labels"], shifted["detailed_labels"], env
    )
    return shifted
