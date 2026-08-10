"""E01 — Nominal baselines (spec §28, registry E01; config configs/experiments/E01.yaml).

Tier A: matched comparison — all six models (incl. QK-SVC) trained on the SAME
2000 nominal events with identical tuning budgets. Tier B: classical models on
the full training split for scale context. Thresholds and calibration frozen
on source_val; all reported metrics are physics-weighted on nominal_test.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.data.splits import SplitSpec, load_splits, make_splits, save_splits  # noqa: E402
from qevc.metrics.classifier import metric_suite, weighted_auc  # noqa: E402
from qevc.models.classical.suite import build, tune  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.models.quantum.qksvc import QKSVC_SPACE, qksvc_builder  # noqa: E402
from qevc.statistics.bootstrap import bootstrap_metric, paired_bootstrap_diff  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
    apply_environment,
    split_columns,
)
from qevc.utils.repro import RunManifest  # noqa: E402

CONFIG = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
PARQUET = REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet"
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build_nominal_dataset() -> pd.DataFrame:
    loader = FairUniverseLoader(PARQUET, REPO / "data/interim/fair_universe")
    raw = loader.load_subset(CONFIG["subset"]["n_total"], CONFIG["subset"]["seed"])
    log(f"raw subset: {len(raw):,} rows")
    d0 = apply_environment(split_columns(raw), Environment())
    df = d0["data"].copy()
    df["weights"] = d0["weights"]
    df["labels"] = d0["labels"].astype(int)
    df["detailed_labels"] = d0["detailed_labels"]
    log(f"nominal D0: {len(df):,} rows after selection")
    return df.reset_index(drop=True)


def get_splits(df: pd.DataFrame) -> dict[str, np.ndarray]:
    spec = SplitSpec(CONFIG["splits"]["fractions"], seed=CONFIG["splits"]["seed"])
    path = REPO / "data/processed/splits" / f"E01_seed{spec.seed}_n{len(df)}.json"
    if path.exists():
        return load_splits(path)
    splits = make_splits(len(df), spec, y=df["labels"].to_numpy())
    save_splits(splits, spec, path)
    return load_splits(path)  # final_eval stays sealed


def tier_a_indices(train_idx: np.ndarray, y: np.ndarray) -> np.ndarray:
    n, seed = CONFIG["tier_a"]["n_train"], CONFIG["tier_a"]["seed"]
    rng = np.random.default_rng(seed)
    pools = [train_idx[y[train_idx] == c] for c in (0, 1)]
    fracs = [len(p) / len(train_idx) for p in pools]
    picks = [rng.choice(p, size=round(n * f), replace=False)
             for p, f in zip(pools, fracs)]
    return np.sort(np.concatenate(picks))


def evaluate_model(name, model, df, splits, X_cols, results, bs_seed):
    """Calibrate on source_val, freeze threshold, evaluate on nominal_test."""
    sv, te = splits["source_val"], splits["nominal_test"]
    X_sv = df.loc[sv, X_cols].to_numpy(float)
    X_te = df.loc[te, X_cols].to_numpy(float)
    y_sv, w_sv = df.loc[sv, "labels"].to_numpy(), df.loc[sv, "weights"].to_numpy()
    y_te, w_te = df.loc[te, "labels"].to_numpy(), df.loc[te, "weights"].to_numpy()

    s_sv = model.scores(X_sv)
    cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
    p_sv, p_te = cal.predict_proba(s_sv), cal.predict_proba(model.scores(X_te))
    thr = ba_optimal_threshold(y_sv, p_sv, w_sv)

    test = metric_suite(y_te, p_te, thr, w_te)
    ci = bootstrap_metric(weighted_auc, y_te, p_te, w_te,
                          n_resamples=CONFIG["bootstrap"]["n_resamples"], seed=bs_seed)
    results["test"] = test
    results["auc_ci95"] = [round(ci.lower, 5), round(ci.upper, 5)]
    results["source_val_auc"] = round(float(weighted_auc(y_sv, p_sv, w_sv)), 5)
    results["threshold"] = round(thr, 5)
    log(f"  {name}: test AUC {test['auc']:.4f} "
        f"[{ci.lower:.4f}, {ci.upper:.4f}], BA {test['balanced_accuracy']:.4f}")
    return p_te


def main() -> int:
    t0 = time.time()
    df = build_nominal_dataset()
    splits = get_splits(df)
    y_all = df["labels"].to_numpy()
    w_all = df["weights"].to_numpy()
    out: dict = {"experiment": "E01", "tiers": {"A": {}, "B": {}}, "sizes": {}}
    tuning = CONFIG["tuning"]

    # ---- Tier A: matched 2000-event comparison ----------------------------
    idx_a = tier_a_indices(splits["train"], y_all)
    out["sizes"] = {r: int(len(v)) for r, v in splits.items()} | {"tier_a": len(idx_a)}
    log(f"tier A: {len(idx_a)} matched events; models {CONFIG['tier_a']['models']}")
    q_cols = CONFIG["features"]["quantum"]
    test_probs: dict[str, np.ndarray] = {}

    for name in CONFIG["tier_a"]["models"]:
        cols = q_cols if name == "qksvc" else FEATURES_ALL
        X = df.loc[idx_a, cols].to_numpy(float)
        y = y_all[idx_a]
        wb = class_balanced_weights(y, w_all[idx_a])
        n_cfg = tuning["n_configs_overrides"].get(name, tuning["n_configs"])
        kwargs = ({"builder_override": qksvc_builder, "space_override": QKSVC_SPACE}
                  if name == "qksvc" else {})
        res = tune(name, X, y, wb, w_all[idx_a], n_configs=n_cfg,
                   cv_folds=tuning["cv_folds"], seed=tuning["seed"], **kwargs)
        model = (qksvc_builder(res.best_params, tuning["seed"]) if name == "qksvc"
                 else build(name, res.best_params, tuning["seed"]))
        model.fit(X, y, sample_weight=wb)
        entry = {"best_params": {k: str(v) for k, v in res.best_params.items()},
                 "cv_auc": round(res.best_cv_auc, 5), "features": len(cols)}
        test_probs[name] = evaluate_model(
            name, model, df, splits, cols, entry, CONFIG["bootstrap"]["seed"])
        out["tiers"]["A"][name] = entry

    # Paired contrasts vs QK-SVC on shared test events
    te = splits["nominal_test"]
    y_te, w_te = y_all[te], w_all[te]
    out["paired_auc_diff_qksvc_minus"] = {}
    for name in CONFIG["tier_a"]["models"]:
        if name == "qksvc":
            continue
        ci = paired_bootstrap_diff(
            weighted_auc, y_te, test_probs["qksvc"], test_probs[name], w_te,
            n_resamples=CONFIG["bootstrap"]["n_resamples"],
            seed=CONFIG["bootstrap"]["seed"])
        out["paired_auc_diff_qksvc_minus"][name] = {
            "point": round(ci.point, 5), "ci95": [round(ci.lower, 5), round(ci.upper, 5)]}

    # ---- Tier B: classical at scale ---------------------------------------
    tr = splits["train"]
    log(f"tier B: {len(tr):,} training events; models {CONFIG['tier_b']['models']}")
    for name in CONFIG["tier_b"]["models"]:
        X = df.loc[tr, FEATURES_ALL].to_numpy(float)
        y = y_all[tr]
        wb = class_balanced_weights(y, w_all[tr])
        n_cfg = tuning["n_configs_overrides"].get(name, tuning["n_configs"])
        res = tune(name, X, y, wb, w_all[tr], n_configs=n_cfg,
                   cv_folds=tuning["cv_folds"], seed=tuning["seed"])
        model = build(name, res.best_params, tuning["seed"])
        model.fit(X, y, sample_weight=wb)
        entry = {"best_params": {k: str(v) for k, v in res.best_params.items()},
                 "cv_auc": round(res.best_cv_auc, 5), "features": len(FEATURES_ALL)}
        evaluate_model(name, model, df, splits, FEATURES_ALL, entry,
                       CONFIG["bootstrap"]["seed"] + 1)
        out["tiers"]["B"][name] = entry

    # ---- Persist ----------------------------------------------------------
    out["wall_seconds"] = round(time.time() - t0, 1)
    out_path = REPO / "results/tables/E01_nominal.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E01", config=CONFIG, seed=CONFIG["subset"]["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E01 complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
