"""E02 — Systematic landscape (spec §28, registry E02; H1).

Retrains the E01 models with their FROZEN best_params (no re-tuning), freezes
calibration + thresholds on the nominal source_val role, then maps the full
predeclared nuisance grid: for each environment θ, the test population is
D_θ over the SAME raw test rows (selection migration included, D-013), and
every model is scored under deployment conditions (nothing re-fitted).

Outputs: results/tables/E02_landscape.json (+ per-env score arrays under
results/raw/E02_scores/ for E03–E05 reuse).
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

from qevc.metrics.classifier import metric_suite, weighted_auc  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.statistics.bootstrap import bootstrap_metric  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E02 = yaml.safe_load((REPO / "configs/experiments/E02.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS
SCORES_DIR = REPO / "results/raw/E02_scores"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_params(raw: dict) -> dict:
    """E01 stored params stringified; recover python types."""
    out = {}
    for k, v in raw.items():
        try:
            out[k] = eval(v, {"__builtins__": {}})  # literals only: numbers/tuples/strings
        except Exception:
            out[k] = v
    return out


def environments() -> list[tuple[str, Environment]]:
    envs: list[tuple[str, Environment]] = []
    for nuisance, values in E02["grid"].items():
        for v in values:
            if nuisance == "soft_met":
                for s in E02["env_seeds"]:
                    envs.append((f"soft_met={v}/seed{s}",
                                 Environment(soft_met=v, seed=s)))
            else:
                envs.append((f"{nuisance}={v}", Environment(**{nuisance: v})))
    for i, combo in enumerate(E02["combos"]):
        if "soft_met" in combo:
            for s in E02["env_seeds"]:
                envs.append((f"combo{i}/seed{s}", Environment(**combo, seed=s)))
        else:
            envs.append((f"combo{i}", Environment(**combo)))
    return envs


def train_frozen_models(frames: dict) -> dict[str, tuple]:
    """Retrain E01 models from frozen params; freeze calibration + threshold."""
    sv_df = frames["source_val"]
    tuning_seed = E01["tuning"]["seed"]
    q_cols = E01["features"]["quantum"]
    models: dict[str, tuple] = {}

    jobs = [("A", n) for n in E01["tier_a"]["models"]] + \
           [("B", n) for n in E01["tier_b"]["models"]]
    df_a = tier_a_frame(frames["train"], E01["tier_a"]["n_train"],
                        E01["tier_a"]["seed"])
    from qevc.pipeline.common import features_for  # noqa: PLC0415

    for tier, name in jobs:
        params = parse_params(E01_RESULTS["tiers"][tier][name]["best_params"])
        train_df = df_a if tier == "A" else frames["train"]
        cols = features_for(name, q_cols, FEATURES_ALL)
        X = train_df[cols].to_numpy(float)
        y, w = train_df["labels"].to_numpy(), train_df["weights"].to_numpy()
        wb = class_balanced_weights(y, w)
        model = (qksvc_builder(params, tuning_seed) if name == "qksvc"
                 else build(name, params, tuning_seed))
        model.fit(X, y, sample_weight=wb)
        s_sv = model.scores(sv_df[cols].to_numpy(float))
        y_sv, w_sv = sv_df["labels"].to_numpy(), sv_df["weights"].to_numpy()
        cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
        thr = ba_optimal_threshold(y_sv, cal.predict_proba(s_sv), w_sv)
        key = f"{tier}:{name}"
        models[key] = (model, cal, thr, cols)
        log(f"trained+froze {key} (thr {thr:.4f})")
    return models


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    models = train_frozen_models(frames)
    test_ids = raw_splits["nominal_test"]
    SCORES_DIR.mkdir(parents=True, exist_ok=True)

    out: dict = {"experiment": "E02", "environments": {}, "nominal": {}}
    envs = [("nominal", Environment())] + environments()
    log(f"{len(envs)} environments × {len(models)} models")

    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        y, w = te["labels"].to_numpy(), te["weights"].to_numpy()
        entry: dict = {"theta": env.to_dict(), "n_events": int(len(te)),
                       "sum_weights": float(w.sum()), "models": {}}
        score_store: dict[str, np.ndarray] = {"row_id": te["row_id"].to_numpy()}
        for key, (model, cal, thr, cols) in models.items():
            p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
            suite = metric_suite(y, p, thr, w)
            ci = bootstrap_metric(weighted_auc, y, p, w,
                                  n_resamples=E02["bootstrap"]["n_resamples"],
                                  seed=E02["bootstrap"]["seed"])
            entry["models"][key] = {
                "auc": round(suite["auc"], 5),
                "auc_ci95": [round(ci.lower, 5), round(ci.upper, 5)],
                "balanced_accuracy": round(suite["balanced_accuracy"], 5),
                "pr_auc": round(suite["pr_auc"], 5),
                "ece": round(suite["ece"], 6),
                "brier": round(suite["brier"], 6),
            }
            if E02["save_scores"]:
                score_store[key] = p.astype(np.float32)
        if E02["save_scores"]:
            np.savez_compressed(
                SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz",
                **score_store)
        bucket = "nominal" if env_name == "nominal" else "environments"
        if bucket == "nominal":
            out["nominal"] = entry
        else:
            out["environments"][env_name] = entry
        auc_span = [m["auc"] for m in entry["models"].values()]
        log(f"{env_name}: n={len(te):,} auc[{min(auc_span):.4f},{max(auc_span):.4f}]")

    # Degradation deltas vs nominal
    for env_name, entry in out["environments"].items():
        entry["delta_auc"] = {
            k: round(out["nominal"]["models"][k]["auc"] - m["auc"], 5)
            for k, m in entry["models"].items()
        }

    out["wall_seconds"] = round(time.time() - t0, 1)
    out_path = REPO / "results/tables/E02_landscape.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E02", config={"E01": E01, "E02": E02},
        seed=E01["subset"]["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E02 complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
