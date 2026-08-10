"""E02R — Multi-seed replication of the nominal baselines and the landscape.

Per replication seed s: fresh five-role RAW-row partition (final_eval sealed),
fresh tier-A subsample, fresh model initialization — hyperparameters frozen
from E01 (declared: replication measures partition/init variance). Each seed's
models are evaluated over the full E02 environment grid at deployment
conditions (thresholds frozen on that seed's source_val).

Outputs: results/tables/E02R_multiseed.json — per-seed nominal AUCs, per-env
per-model AUC/ΔAUC, across-seed means/stds, and the TES sign-pattern
replication check for the quantum model.
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

from qevc.data.splits import SplitSpec, make_splits  # noqa: E402
from qevc.metrics.classifier import weighted_auc, weighted_balanced_accuracy  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    load_raw_subset,
    tier_a_frame,
)
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E02R = yaml.safe_load((REPO / "configs/experiments/E02R.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, parse_params  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    q_cols = E01["features"]["quantum"]
    env_list = [("nominal", Environment())] + environments()

    per_seed: dict = {}
    for s in E02R["replication_seeds"]:
        ts = time.time()
        spec = SplitSpec(E01["splits"]["fractions"], seed=s)
        splits = make_splits(len(raw), spec, y=raw["labels"].to_numpy())
        splits.pop("final_eval")  # sealed, untouched in replication
        d0 = build_environment_dataset(raw, Environment())
        frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
                  for r, ids in splits.items()}
        df_a = tier_a_frame(frames["train"], E01["tier_a"]["n_train"], seed=s)
        sv_df = frames["source_val"]
        y_sv, w_sv = sv_df["labels"].to_numpy(), sv_df["weights"].to_numpy()

        fitted: dict[str, tuple] = {}
        from qevc.pipeline.common import features_for  # noqa: PLC0415

        for key in E02R["models"]:
            tier, name = key.split(":")
            params = parse_params(E01_RESULTS["tiers"][tier][name]["best_params"])
            train_df = df_a if tier == "A" else frames["train"]
            cols = features_for(name, q_cols, FEATURES_ALL)
            X = train_df[cols].to_numpy(float)
            y, w = train_df["labels"].to_numpy(), train_df["weights"].to_numpy()
            model = (qksvc_builder(params, s) if name == "qksvc"
                     else build(name, params, s))
            model.fit(X, y, sample_weight=class_balanced_weights(y, w))
            s_sv = model.scores(sv_df[cols].to_numpy(float))
            cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
            thr = ba_optimal_threshold(y_sv, cal.predict_proba(s_sv), w_sv)
            fitted[key] = (model, cal, thr, cols)

        seed_out: dict = {"environments": {}}
        for env_name, env in env_list:
            te = build_environment_dataset(raw, env,
                                           row_ids=splits["nominal_test"])
            y_te, w_te = te["labels"].to_numpy(), te["weights"].to_numpy()
            env_out = {}
            for key, (model, cal, thr, cols) in fitted.items():
                p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
                env_out[key] = {
                    "auc": round(float(weighted_auc(y_te, p, w_te)), 5),
                    "ba": round(float(weighted_balanced_accuracy(
                        y_te, (p >= thr).astype(float), w_te)), 5),
                }
            seed_out["environments"][env_name] = env_out
        per_seed[str(s)] = seed_out
        log(f"seed {s}: done in {time.time() - ts:.0f} s")

    # ---- Across-seed synthesis -------------------------------------------
    seeds = [str(s) for s in E02R["replication_seeds"]]
    env_names = [e for e, _ in env_list]
    summary: dict = {}
    for key in E02R["models"]:
        nom = np.array([per_seed[s]["environments"]["nominal"][key]["auc"]
                        for s in seeds])
        summary[key] = {
            "nominal_auc_mean": round(float(nom.mean()), 5),
            "nominal_auc_std": round(float(nom.std(ddof=1)), 5),
            "delta_auc": {},
        }
        for env_name in env_names:
            if env_name == "nominal":
                continue
            d = np.array([
                per_seed[s]["environments"]["nominal"][key]["auc"]
                - per_seed[s]["environments"][env_name][key]["auc"]
                for s in seeds
            ])
            summary[key]["delta_auc"][env_name] = {
                "mean": round(float(d.mean()), 5),
                "std": round(float(d.std(ddof=1)), 5),
                "sign_consistent": bool(np.all(d > 0) or np.all(d < 0)),
            }

    # Nominal paired contrast QK − A:xgboost across seeds
    qk_minus_xgb = np.array([
        per_seed[s]["environments"]["nominal"]["A:qksvc"]["auc"]
        - per_seed[s]["environments"]["nominal"]["A:xgboost"]["auc"]
        for s in seeds
    ])
    # TES sign-pattern replication for the quantum model
    tes_check_model = E02R["checks"]["tes_sign_pattern"]
    tes_pattern = {}
    for env_name in ("tes=0.98", "tes=0.99", "tes=1.01", "tes=1.02"):
        d = summary[tes_check_model]["delta_auc"][env_name]
        tes_pattern[env_name] = d
    monotone_frac = float(np.mean([
        all(
            (per_seed[s]["environments"]["tes=0.98"][tes_check_model]["auc"]
             < per_seed[s]["environments"]["tes=0.99"][tes_check_model]["auc"]
             < per_seed[s]["environments"]["tes=1.01"][tes_check_model]["auc"]
             < per_seed[s]["environments"]["tes=1.02"][tes_check_model]["auc"],)
        )
        for s in seeds
    ]))

    out = {
        "experiment": "E02R",
        "hyperparams": "frozen from E01 (partition/init variance only)",
        "summary": summary,
        "nominal_qk_minus_xgbA": {
            "per_seed": [round(float(v), 5) for v in qk_minus_xgb],
            "mean": round(float(qk_minus_xgb.mean()), 5),
            "std": round(float(qk_minus_xgb.std(ddof=1)), 5),
        },
        "tes_sign_pattern_qk": tes_pattern,
        "tes_monotone_fraction_of_seeds": monotone_frac,
        "per_seed": per_seed,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E02R_multiseed.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E02R", config={"E01": E01, "E02R": E02R},
        seed=E02R["replication_seeds"][0],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E02R complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
