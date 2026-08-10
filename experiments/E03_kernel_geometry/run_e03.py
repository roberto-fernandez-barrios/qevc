"""E03 — Kernel geometry observatory (spec §12, §28; H2 descriptive half).

For each E02 environment θ and each kernel (quantum from E01's frozen QK-SVC;
RBF comparator from E01's frozen RBF-SVC), computes the I1-level descriptor
vector G_θ from: source tier-A training events, an UNLABELED target sample of
D_θ (test role rows), and source labels only. No target labels are touched —
geometry is a risk sensor, never a certificate (D-006).

Outputs: results/tables/E03_geometry.json (G_θ per env × kernel).
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

from qevc.geometry.descriptors import describe_environment  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E02 = yaml.safe_load((REPO / "configs/experiments/E02.yaml").read_text())
E03 = yaml.safe_load((REPO / "configs/experiments/E03.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, parse_params  # noqa: E402  (same env list as E02)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def rbf_gram(A: np.ndarray, B: np.ndarray, gamma: float) -> np.ndarray:
    aa = (A * A).sum(1)[:, None]
    bb = (B * B).sum(1)[None, :]
    return np.exp(-gamma * np.clip(aa + bb - 2.0 * A @ B.T, 0.0, None))


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    d0 = build_environment_dataset(raw, Environment())
    train_df = d0[np.isin(d0["row_id"].to_numpy(), raw_splits["train"])]
    df_a = tier_a_frame(train_df, E01["tier_a"]["n_train"], E01["tier_a"]["seed"])
    y_src = np.where(df_a["labels"].to_numpy() == 1, 1, -1)

    # -- Quantum kernel anchor (identical to frozen QK-SVC preprocessing) ----
    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    q_cols = E01["features"]["quantum"]
    Xq_src_raw = df_a[q_cols].to_numpy(float)
    ang = AngleScaler().fit(Xq_src_raw)
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    Zq_src = ang.transform(Xq_src_raw)

    # -- RBF comparator anchor ----------------------------------------------
    Xc_src_raw = df_a[FEATURES_ALL].to_numpy(float)
    std = StandardScaler().fit(Xc_src_raw)
    Zc_src = std.transform(Xc_src_raw)
    rp = parse_params(E01_RESULTS["tiers"]["A"]["rbf_svc"]["best_params"])
    gamma = (1.0 / (Zc_src.shape[1] * Zc_src.var())
             if rp["gamma"] == "scale" else float(rp["gamma"]))

    K_ss_q = kernel_exact(Zq_src, fm)
    K_ss_c = rbf_gram(Zc_src, Zc_src, gamma)
    log(f"source anchors ready (n={len(df_a)}); gamma_rbf={gamma:.5f}")

    rng = np.random.default_rng(E03["samples"]["target_seed"])
    test_ids = raw_splits["nominal_test"]
    out: dict = {"experiment": "E03", "environments": {}}

    envs = [("nominal", Environment())] + environments()
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        n_t = min(E03["samples"]["n_target_per_env"], len(te))
        sub = te.iloc[np.sort(rng.choice(len(te), size=n_t, replace=False))]
        entry: dict = {"theta": env.to_dict(), "n_target": int(n_t), "kernels": {}}

        Zq_t = ang.transform(sub[q_cols].to_numpy(float))
        entry["kernels"]["quantum"] = describe_environment(
            K_ss_q, kernel_exact(Zq_t, fm), kernel_exact(Zq_src, fm, Zq_t),
            y_source=y_src, top_eigs=E03["top_eigs"])

        Zc_t = std.transform(sub[FEATURES_ALL].to_numpy(float))
        entry["kernels"]["rbf"] = describe_environment(
            K_ss_c, rbf_gram(Zc_t, Zc_t, gamma), rbf_gram(Zc_src, Zc_t, gamma),
            y_source=y_src, top_eigs=E03["top_eigs"])

        out["environments"][env_name] = entry
        log(f"{env_name}: mmd2 q={entry['kernels']['quantum']['mmd2']:.5f} "
            f"rbf={entry['kernels']['rbf']['mmd2']:.5f}")

    out["wall_seconds"] = round(time.time() - t0, 1)
    out_path = REPO / "results/tables/E03_geometry.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E03", config={"E01": E01, "E02": E02, "E03": E03},
        seed=E03["samples"]["target_seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E03 complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
