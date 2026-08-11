"""E12 diagnostic — factorize the nominal-level shift (registry E12 addendum).

E12's fresh draw reproduced every paired/relative headline but sits ~0.06-0.09
BELOW the seed-101 world in absolute weighted AUC for every model — far beyond
E02R's partition variance (which re-partitions the SAME 300k rows). This
script factorizes the shift without touching any protocol:

  (1) cross-evaluation: seed-101-trained models on the E12 test set and
      E12-trained models on the seed-101 test set (models x data grid);
  (2) weighted vs unweighted AUC in all four combinations (is the shift
      weight-driven?);
  (3) weight-distribution anatomy per process (within-process dispersion,
      effective sample size) in both subsets;
  (4) feature-distribution distances between the two subsets (per-process
      KS on the 8 quantum features).

Pure post-hoc analysis of a completed confirmatory run: nothing is tuned,
no protocol changes, no E13-E16 development uses E12 rows.

Outputs: results/tables/E12_diagnostic.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from scipy import stats  # noqa: E402

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.metrics.classifier import weighted_auc  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import PlattCalibrator, class_balanced_weights  # noqa: E402
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    features_for,
    get_raw_splits,
    tier_a_frame,
)
from qevc.statistics.bootstrap import bootstrap_metric  # noqa: E402
from qevc.statistics.weighted import effective_sample_size_ratio  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E12 = yaml.safe_load((REPO / "configs/experiments/E12.yaml").read_text())
FROZEN = yaml.safe_load((REPO / E12["frozen_source"]).read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS
MODELS = [("A", "qksvc"), ("A", "rbf_svc_8f"), ("A", "xgboost"), ("B", "xgboost")]
Q_COLS = FROZEN["features"]["quantum"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_params(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        try:
            out[k] = eval(v, {"__builtins__": {}})
        except Exception:
            out[k] = v
    return out


def load_world(tag: str, loader: FairUniverseLoader):
    """(raw, frames, tier_a_seed) for the seed-101 or E12 world."""
    if tag == "s101":
        raw = loader.load_subset(E01["subset"]["n_total"], E01["subset"]["seed"])
        splits_cfg, exp_tag, ta_seed = E01["splits"], "E01", E01["tier_a"]["seed"]
    else:
        exclusion = np.union1d(
            np.load(REPO / "data/processed/used_rows/seed101_subset_n300000_indices.npy"),
            np.load(REPO / "data/processed/used_rows/e00_validation_rowgroup_indices.npy"))
        raw = loader.load_subset(E12["subset"]["n_total"], E12["subset"]["seed"],
                                 exclude=exclusion, tag=E12["subset"]["tag"])
        splits_cfg, exp_tag, ta_seed = E12["splits"], "E12", E12["tier_a_seed"]
    splits = get_raw_splits(REPO, raw, splits_cfg, experiment_tag=exp_tag)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in splits.items()}
    return raw, frames, ta_seed


def train_world_models(frames, ta_seed):
    df_a = tier_a_frame(frames["train"],
                        FROZEN["training_protocol"]["tier_a_budget"]["n_train"],
                        ta_seed)
    seed = FROZEN["training_protocol"]["init_seed"]
    sv = frames["source_val"]
    out = {}
    for tier, name in MODELS:
        params = parse_params(
            FROZEN["hyperparameters"]["tier_a" if tier == "A" else "tier_b"][name])
        train_df = df_a if tier == "A" else frames["train"]
        cols = features_for(name, Q_COLS, FEATURES_ALL)
        X = train_df[cols].to_numpy(float)
        y, w = train_df["labels"].to_numpy(), train_df["weights"].to_numpy()
        model = (qksvc_builder(params, seed) if name == "qksvc"
                 else build(name, params, seed))
        model.fit(X, y, sample_weight=class_balanced_weights(y, w))
        s_sv = model.scores(sv[cols].to_numpy(float))
        cal = PlattCalibrator().fit(s_sv, sv["labels"].to_numpy(),
                                    sv["weights"].to_numpy())
        out[f"{tier}:{name}"] = (model, cal, cols)
        log(f"trained {tier}:{name}")
    return out


def weight_anatomy(raw) -> dict:
    w = raw["weights"].to_numpy()
    dl = raw["detailed_labels"].to_numpy()
    out = {"overall": {
        "ess_ratio": round(effective_sample_size_ratio(w), 6),
        "max_over_mean": round(float(w.max() / w.mean()), 2)}}
    for proc in np.unique(dl):
        v = w[dl == proc]
        out[str(proc)] = {
            "n": int(len(v)), "sum": round(float(v.sum()), 2),
            "mean": round(float(v.mean()), 6), "min": round(float(v.min()), 8),
            "max": round(float(v.max()), 4),
            "max_over_mean": round(float(v.max() / v.mean()), 2),
            "ess_ratio": round(effective_sample_size_ratio(v), 6),
            "constant_within_process": bool(np.allclose(v.min(), v.max(), rtol=1e-6)),
        }
    return out


def main() -> int:
    t0 = time.time()
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")
    worlds = {}
    for tag in ("s101", "e12"):
        raw, frames, ta_seed = load_world(tag, loader)
        worlds[tag] = {"raw": raw, "frames": frames, "ta_seed": ta_seed}
        log(f"world {tag}: test n={len(frames['nominal_test'])}")

    models = {tag: train_world_models(w["frames"], w["ta_seed"])
              for tag, w in worlds.items()}

    # (1)+(2) models x data grid, weighted + unweighted AUC (+ bootstrap CI)
    grid: dict = {}
    for mtag, mset in models.items():
        for dtag, w in worlds.items():
            te = w["frames"]["nominal_test"]
            y = te["labels"].to_numpy()
            wt = te["weights"].to_numpy()
            for key, (model, cal, cols) in mset.items():
                p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
                auc_w = weighted_auc(y, p, sample_weight=wt)
                auc_u = weighted_auc(y, p, sample_weight=np.ones_like(wt))
                ci = bootstrap_metric(weighted_auc, y, p, wt,
                                      n_resamples=500, seed=99)
                grid[f"models[{mtag}]-data[{dtag}]|{key}"] = {
                    "auc_weighted": round(float(auc_w), 5),
                    "auc_weighted_ci95": [round(ci.lower, 5), round(ci.upper, 5)],
                    "auc_unweighted": round(float(auc_u), 5),
                }
            log(f"scored models[{mtag}] on data[{dtag}]")

    # (3) weight anatomy per world
    anatomy = {tag: weight_anatomy(w["raw"]) for tag, w in worlds.items()}

    # ESS of the nominal_test role specifically (drives the AUC variance)
    for tag, w in worlds.items():
        wt = w["frames"]["nominal_test"]["weights"].to_numpy()
        anatomy[tag]["nominal_test_ess_ratio"] = round(
            effective_sample_size_ratio(wt), 6)
        anatomy[tag]["nominal_test_n"] = int(len(wt))

    # (4) per-process KS distances on the 8 quantum features between subsets
    ks: dict = {}
    for proc in ("htautau", "ztautau", "ttbar", "diboson"):
        a = worlds["s101"]["raw"]
        b = worlds["e12"]["raw"]
        ma = a["detailed_labels"].to_numpy() == proc
        mb = b["detailed_labels"].to_numpy() == proc
        ks[proc] = {}
        for col in Q_COLS:
            va = a[col].to_numpy()[ma]
            vb = b[col].to_numpy()[mb]
            va, vb = va[va > -20], vb[vb > -20]  # drop sentinels
            if len(va) > 50 and len(vb) > 50:
                st = stats.ks_2samp(va, vb)
                ks[proc][col] = {"ks": round(float(st.statistic), 5),
                                 "p": round(float(st.pvalue), 5)}

    out = {
        "experiment": "E12_diagnostic",
        "purpose": "factorize the E12 nominal-level shift (models x data)",
        "grid": grid,
        "weight_anatomy": anatomy,
        "feature_ks_between_subsets": ks,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E12_diagnostic.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E12d", config={"E12": E12}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"diagnostic complete in {out['wall_seconds']} s")
    # concise console summary
    for k in sorted(grid):
        if "A:xgboost" in k or "B:xgboost" in k:
            g = grid[k]
            log(f"{k}: w={g['auc_weighted']} u={g['auc_unweighted']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
