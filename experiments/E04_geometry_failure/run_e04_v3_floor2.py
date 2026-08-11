"""E04v3 floor addendum (registered amendment, 2026-08-11).

Finding from the main E04v3 run: under common random numbers the weight-only
environments produce MMD^2 IDENTICAL to nominal (their features are the
nominal features and CRN uses the same rows), so the frozen
max-over-weight-only floor degenerates to the nominal point value and
almost every out-of-grid shift "alarms". The blindness statement gets
STRONGER (computational identity), but the veto floor must be built from
INDEPENDENT nominal draws — the sampling-noise null the rule was always
meant to capture (E11's MC-vs-MC floor already does this).

This addendum computes, per world: 20 independent auditor_dev nominal draw
pairs -> MMD^2 null distribution; floor = max (frozen rule's analogue) and
q95; alarm counts for the 48 out-of-grid shift environments under both.
Appends a `floor_v2` section to E04v3_out_of_grid.json (original content
untouched).
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

from sklearn.preprocessing import StandardScaler  # noqa: E402

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.geometry.descriptors import mean_similarity_shift  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.systematics.fair_universe import Environment  # noqa: E402

sys.path.insert(0, str(REPO / "experiments/E04_geometry_failure"))
from run_e04_v3 import (  # noqa: E402
    FROZEN,
    Q_COLS,
    load_world,
    new_environments,
    parse_params,
    rbf_gram,
)

N_NULL_DRAWS = 20
NULL_SEED_BASE = 8100
N_ROWS = 2500


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    t0 = time.time()
    out_path = REPO / "results/tables/E04v3_out_of_grid.json"
    table = json.loads(out_path.read_text())
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")

    qp = parse_params(FROZEN["hyperparameters"]["tier_a"]["qksvc"])
    r8 = parse_params(FROZEN["hyperparameters"]["tier_a"]["rbf_svc_8f"])
    gamma8 = float(r8["gamma"])

    for world in ("s101", "e12"):
        raw, splits, ta_seed = load_world(world, loader)
        d0 = build_environment_dataset(raw, Environment())
        train_df = d0[np.isin(d0["row_id"].to_numpy(), splits["train"])]
        df_a = tier_a_frame(
            train_df, FROZEN["training_protocol"]["tier_a_budget"]["n_train"],
            ta_seed)
        ang = AngleScaler().fit(df_a[Q_COLS].to_numpy(float))
        fm = build_feature_map(len(Q_COLS), reps=qp["reps"],
                               entanglement=qp["entanglement"],
                               scale=qp["scale"])
        std8 = StandardScaler().fit(df_a[Q_COLS].to_numpy(float))
        Zq_src = ang.transform(df_a[Q_COLS].to_numpy(float))
        Z8_src = std8.transform(df_a[Q_COLS].to_numpy(float))
        K_ss = {"quantum": kernel_exact(Zq_src, fm),
                "rbf8": rbf_gram(Z8_src, Z8_src, gamma8)}

        # independent nominal draws from auditor_dev (label-free, D-021)
        ad_ids = splits["auditor_dev"]
        te_nom = build_environment_dataset(raw, Environment(), row_ids=ad_ids)
        rid = te_nom["row_id"].to_numpy()
        null_vals = {"quantum": [], "rbf8": []}
        for k in range(N_NULL_DRAWS):
            rng = np.random.default_rng(NULL_SEED_BASE + k)
            ids = rng.choice(ad_ids, size=N_ROWS, replace=False)
            sub = te_nom[np.isin(rid, ids)]
            Zq_t = ang.transform(sub[Q_COLS].to_numpy(float))
            Z8_t = std8.transform(sub[Q_COLS].to_numpy(float))
            null_vals["quantum"].append(mean_similarity_shift(
                K_ss["quantum"], kernel_exact(Zq_src, fm, Zq_t),
                kernel_exact(Zq_t, fm))["mmd2"])
            null_vals["rbf8"].append(mean_similarity_shift(
                K_ss["rbf8"], rbf_gram(Z8_src, Z8_t, gamma8),
                rbf_gram(Z8_t, Z8_t, gamma8))["mmd2"])
        log(f"[{world}] null draws done")

        envs = new_environments()
        shift = [n for n, f, _ in envs if f != "weight_only"]
        mmd_mean = table["worlds"][world]["mmd2_mean"]
        floor_v2 = {}
        for kern in ("quantum", "rbf8"):
            null = np.array(null_vals[kern])
            fl_max = float(null.max())
            fl_q95 = float(np.percentile(null, 95))
            alarms_max = sorted(e for e in shift
                                if mmd_mean[e][kern] > fl_max)
            alarms_q95 = sorted(e for e in shift
                                if mmd_mean[e][kern] > fl_q95)
            floor_v2[kern] = {
                "null_mean": round(float(null.mean()), 7),
                "null_std": round(float(null.std()), 7),
                "floor_max_of_20": round(fl_max, 7),
                "floor_q95": round(fl_q95, 7),
                "n_alarms_floor_max": len(alarms_max),
                "n_alarms_floor_q95": len(alarms_q95),
                "n_shift_envs": len(shift),
                "alarmed_families_max": sorted({e.split("=")[0].replace("og_", "")
                                                if not e.startswith("prior")
                                                else "prior"
                                                for e in alarms_max}),
            }
        table["worlds"][world]["floor_v2"] = floor_v2
        table["worlds"][world]["floor_v2_note"] = (
            "CRN makes weight-only envs IDENTICAL to nominal (blindness in "
            "exact form); the operative veto floor is the independent-"
            "nominal-draw null computed here (registered amendment)")
        log(f"[{world}] floor_v2: {json.dumps(floor_v2)}")

    table["floor2_wall_seconds"] = round(time.time() - t0, 1)
    out_path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    log("floor_v2 appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
