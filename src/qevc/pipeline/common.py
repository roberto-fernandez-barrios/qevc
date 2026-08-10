"""Shared experiment-pipeline helpers (raw-row partitioning scheme, D-013).

Used by E02+ runners; E01's runner predates this module and carries local
copies with identical semantics (kept in sync by the E01/E02 consistency
assertions in run_e02.py).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from qevc.data.fair_universe_loader import FairUniverseLoader
from qevc.data.splits import SplitSpec, load_splits, make_splits, save_splits
from qevc.systematics.fair_universe import Environment, apply_environment, split_columns


def load_raw_subset(repo: Path, subset_cfg: dict) -> pd.DataFrame:
    loader = FairUniverseLoader(
        repo / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        repo / "data/interim/fair_universe",
    )
    return loader.load_subset(subset_cfg["n_total"], subset_cfg["seed"])


def get_raw_splits(repo: Path, raw: pd.DataFrame, splits_cfg: dict,
                   experiment_tag: str = "E01") -> dict[str, np.ndarray]:
    """Load (or create) the five-role RAW-row partition shared across
    experiments. E02+ reuse E01's stored split file for identical roles."""
    spec = SplitSpec(splits_cfg["fractions"], seed=splits_cfg["seed"])
    path = (repo / "data/processed/splits" /
            f"{experiment_tag}_{splits_cfg['scheme']}_seed{spec.seed}_n{len(raw)}.json")
    if path.exists():
        return load_splits(path)
    splits = make_splits(len(raw), spec, y=raw["labels"].to_numpy())
    save_splits(splits, spec, path)
    return load_splits(path)


def build_environment_dataset(
    raw: pd.DataFrame, env: Environment, row_ids: np.ndarray | None = None
) -> pd.DataFrame:
    """D_θ for (a subset of) raw rows, with raw-row provenance ids.

    ``row_ids`` restricts to those raw rows (e.g. the test role) — the ids are
    global raw-subset row indices and survive the selection (D-013).
    """
    if row_ids is None:
        sub, ids = raw, np.arange(len(raw))
    else:
        ids = np.asarray(row_ids, dtype=int)
        sub = raw.iloc[ids]
    dset = split_columns(sub.reset_index(drop=True))
    dset["row_id"] = ids
    d = apply_environment(dset, env)
    df = d["data"].copy()
    df["weights"] = d["weights"]
    df["labels"] = np.asarray(d["labels"]).astype(int)
    df["detailed_labels"] = d["detailed_labels"]
    df["row_id"] = np.asarray(d["row_id"]).astype(int)
    return df.reset_index(drop=True)


QUANTUM_FEATURE_MODELS = {"qksvc", "rbf_svc_8f"}


def features_for(model_name: str, q_cols: list[str], all_cols: list[str]) -> list[str]:
    """Which feature set a model consumes (matched-kernel control uses the
    quantum 8-feature set; everything else the full 28)."""
    return q_cols if model_name in QUANTUM_FEATURE_MODELS else all_cols


def tier_a_frame(train_df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Label-stratified matched-comparison subset of the training role."""
    rng = np.random.default_rng(seed)
    y = train_df["labels"].to_numpy()
    idx = np.arange(len(train_df))
    pools = [idx[y == c] for c in (0, 1)]
    fracs = [len(p) / len(idx) for p in pools]
    picks = [rng.choice(p, size=round(n * f), replace=False)
             for p, f in zip(pools, fracs)]
    return train_df.iloc[np.sort(np.concatenate(picks))]
