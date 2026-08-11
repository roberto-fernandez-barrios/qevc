"""E16 hardware arm (submit) — full-pipeline micro-demonstration (D-027).

Priority (a) of the registry entry: a QK-SVC trained AND deployed on
100%-hardware kernels, with the auditor run end-to-end at micro-scale.
Sized to the live Open-plan budget via a PREDECLARED ladder (largest config
whose conservative estimate fits 90% of the remaining window); raw counts,
no mitigation (priority (b) does not fit the Open window and is reported as
not-run). Test events: half nominal, half tes=0.98 — the collider-shift x
quantum-noise double uncertainty on a real device.

Outputs: results/raw/E16_hw/{K blocks, provenance}; analysis in
run_e16_hw_analyze.py once the job completes. Failed jobs are reported.
"""

from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from qiskit import QuantumCircuit, transpile  # noqa: E402
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2  # noqa: E402

from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.systematics.fair_universe import Environment  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
FROZEN = yaml.safe_load((REPO / "configs/frozen/frozen_deployment_v1.yaml").read_text())
RAW_DIR = REPO / "results/raw/E16_hw"
SHOTS = 1024
SEED = 1616
SEC_PER_CIRCUIT = 0.35        # conservative from E10 v1 (0.556 s @ 2048 shots)
LADDER = [                     # predeclared; largest fitting 0.9 * remaining
    {"n_train": 36, "n_test": 20},
    {"n_train": 32, "n_test": 16},
    {"n_train": 28, "n_test": 12},
    {"n_train": 24, "n_test": 8},
]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_token() -> str:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("IBM_QUANTUM_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no token in .env")


def parse_params(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        try:
            out[k] = eval(v, {"__builtins__": {}})
        except Exception:
            out[k] = v
    return out


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=get_token())
    usage = svc.usage()
    remaining = usage.get("usage_remaining_seconds", 0)
    log(f"open-plan remaining: {remaining} s (period ends "
        f"{usage.get('usage_period', {}).get('end_time')})")
    chosen = None
    for cfg in LADDER:
        n_circ = (cfg["n_train"] * (cfg["n_train"] - 1)) // 2 \
            + cfg["n_train"] * cfg["n_test"]
        est = n_circ * SEC_PER_CIRCUIT
        if est <= 0.9 * remaining:
            chosen = {**cfg, "n_circuits": n_circ, "est_seconds": round(est, 1)}
            break
    if chosen is None:
        log("no ladder config fits the remaining budget — NOT submitting")
        (RAW_DIR / "submit_skipped.json").write_text(json.dumps(
            {"reason": "insufficient open-plan budget", "usage": usage},
            indent=2, default=str), encoding="utf-8")
        return 1
    log(f"ladder pick: {chosen}")

    # -- events: train (tier-A stratified) + test (nominal & tes=0.98) -------
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    d0 = build_environment_dataset(raw, Environment())
    train_df = d0[np.isin(d0["row_id"].to_numpy(), raw_splits["train"])]
    df_a = tier_a_frame(train_df, E01["tier_a"]["n_train"], E01["tier_a"]["seed"])
    rng = np.random.default_rng(SEED)
    y_a = df_a["labels"].to_numpy()
    n_half = chosen["n_train"] // 2
    tr_idx = np.sort(np.concatenate([
        rng.choice(np.flatnonzero(y_a == 1), size=n_half, replace=False),
        rng.choice(np.flatnonzero(y_a == 0),
                   size=chosen["n_train"] - n_half, replace=False)]))
    sub_tr = df_a.iloc[tr_idx]

    # test rows: distinct stratified draws from the nominal_test role,
    # half evaluated at nominal, half under tes=0.98 features
    te_nom_all = build_environment_dataset(raw, Environment(),
                                           row_ids=raw_splits["nominal_test"])
    te_tes_all = build_environment_dataset(raw, Environment(tes=0.98),
                                           row_ids=raw_splits["nominal_test"])
    n_te_half = chosen["n_test"] // 2

    def strat_pick(df, n):
        y = df["labels"].to_numpy()
        k = n // 2
        return np.sort(np.concatenate([
            rng.choice(np.flatnonzero(y == 1), size=k, replace=False),
            rng.choice(np.flatnonzero(y == 0), size=n - k, replace=False)]))

    i_nom = strat_pick(te_nom_all, n_te_half)
    i_tes = strat_pick(te_tes_all, chosen["n_test"] - n_te_half)
    sub_te = {
        "nominal": te_nom_all.iloc[i_nom],
        "tes=0.98": te_tes_all.iloc[i_tes],
    }

    qp = parse_params(FROZEN["hyperparameters"]["tier_a"]["qksvc"])
    q_cols = FROZEN["features"]["quantum"]
    ang = AngleScaler().fit(df_a[q_cols].to_numpy(float))
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    Z_tr = ang.transform(sub_tr[q_cols].to_numpy(float))
    Z_te = np.vstack([ang.transform(sub_te[e][q_cols].to_numpy(float))
                      for e in ("nominal", "tes=0.98")])
    te_env = (["nominal"] * n_te_half
              + ["tes=0.98"] * (chosen["n_test"] - n_te_half))

    np.save(RAW_DIR / "Z_train.npy", Z_tr)
    np.save(RAW_DIR / "Z_test.npy", Z_te)
    np.save(RAW_DIR / "train_labels.npy", sub_tr["labels"].to_numpy())
    np.save(RAW_DIR / "train_weights.npy", sub_tr["weights"].to_numpy())
    np.save(RAW_DIR / "train_row_ids.npy", sub_tr["row_id"].to_numpy())
    te_labels = np.concatenate([sub_te[e]["labels"].to_numpy()
                                for e in ("nominal", "tes=0.98")])
    te_rows = np.concatenate([sub_te[e]["row_id"].to_numpy()
                              for e in ("nominal", "tes=0.98")])
    np.save(RAW_DIR / "test_labels.npy", te_labels)
    np.save(RAW_DIR / "test_row_ids.npy", te_rows)
    (RAW_DIR / "test_envs.json").write_text(json.dumps(te_env), encoding="utf-8")

    K_ideal_tr = kernel_exact(Z_tr, fm)
    K_ideal_cross = kernel_exact(Z_tr, fm, Z_te)
    np.save(RAW_DIR / "K_ideal_train.npy", K_ideal_tr)
    np.save(RAW_DIR / "K_ideal_cross.npy", K_ideal_cross)

    # -- circuits: train pairs then cross pairs (order recorded) -------------
    train_pairs = list(combinations(range(len(Z_tr)), 2))
    cross_pairs = [(i, j) for i in range(len(Z_tr)) for j in range(len(Z_te))]
    circuits = []
    for i, j in train_pairs:
        qc = QuantumCircuit(len(q_cols))
        qc.compose(fm(Z_tr[i]), inplace=True)
        qc.compose(fm(Z_tr[j]).inverse(), inplace=True)
        qc.measure_all()
        circuits.append(qc)
    for i, j in cross_pairs:
        qc = QuantumCircuit(len(q_cols))
        qc.compose(fm(Z_tr[i]), inplace=True)
        qc.compose(fm(Z_te[j]).inverse(), inplace=True)
        qc.measure_all()
        circuits.append(qc)
    assert len(circuits) == chosen["n_circuits"]
    (RAW_DIR / "pair_order.json").write_text(json.dumps(
        {"train_pairs": train_pairs, "cross_pairs": cross_pairs}),
        encoding="utf-8")

    backends = [b for b in svc.backends()
                if b.status().operational and b.num_qubits >= 100]
    backend = min(backends, key=lambda b: b.status().pending_jobs)
    log(f"backend: {backend.name} (pending {backend.status().pending_jobs})")
    tqc = transpile(circuits, backend=backend, optimization_level=1,
                    seed_transpiler=SEED)
    depths = [c.depth() for c in tqc]
    twoq = [sum(1 for inst in c.data if inst.operation.num_qubits == 2)
            for c in tqc]
    log(f"transpiled: depth med {int(np.median(depths))}, "
        f"2q med {int(np.median(twoq))}")

    calib = {"backend": backend.name, "num_qubits": backend.num_qubits}
    try:
        props = backend.properties()
        calib["last_update_date"] = str(props.last_update_date)
    except Exception as e:
        calib["properties_note"] = f"unavailable: {e}"

    sampler = SamplerV2(mode=backend)
    job = sampler.run(tqc, shots=SHOTS)
    provenance = {
        "experiment": "E16_hw", "job_id": job.job_id(),
        "backend": backend.name, "shots": SHOTS,
        "ladder_choice": chosen, "usage_at_submit": usage,
        "n_train": chosen["n_train"], "n_test": chosen["n_test"],
        "test_env_split": te_env,
        "transpile": {"optimization_level": 1,
                      "depth_median": int(np.median(depths)),
                      "twoq_median": int(np.median(twoq))},
        "calibration": calib,
        "submitted_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qksvc_params": {k: str(v) for k, v in qp.items()},
        "mitigation": "none (raw counts); DD/twirling split does not fit the "
                      "Open window — reported as not-run (D-027 priority b)",
    }
    (RAW_DIR / "job_provenance.json").write_text(
        json.dumps(provenance, indent=2, default=str), encoding="utf-8")
    log(f"SUBMITTED job {job.job_id()} to {backend.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
