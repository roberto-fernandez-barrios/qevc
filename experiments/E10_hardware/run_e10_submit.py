"""E10 (submit phase) — Quantum hardware validation (spec §19, §28).

Builds the 32-event stratified subset, constructs the 496 compute–uncompute
circuits of the E01-frozen feature map, transpiles them for the least-pending
open-instance backend, submits ONE SamplerV2 job at 2048 shots, and records
full provenance (backend, calibration snapshot, transpiled depths/gate
counts, timestamps, job id). Analysis happens in run_e10_analyze.py once the
job completes — failed runs are reported, never hidden.

Token is read from the gitignored .env and never printed or stored in
results.
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
E10 = yaml.safe_load((REPO / "configs/experiments/E10.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
RAW_DIR = REPO / E10["outputs_raw"]

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import parse_params  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_token() -> str:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("IBM_QUANTUM_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no token in .env")


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # -- Subset (deterministic, stratified from tier-A train) ---------------
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    d0 = build_environment_dataset(raw, Environment())
    train_df = d0[np.isin(d0["row_id"].to_numpy(), raw_splits["train"])]
    df_a = tier_a_frame(train_df, E01["tier_a"]["n_train"], E01["tier_a"]["seed"])
    rng = np.random.default_rng(E10["subset"]["seed"])
    y_a = df_a["labels"].to_numpy()
    n_half = E10["subset"]["n_events"] // 2
    idx = np.sort(np.concatenate([
        rng.choice(np.flatnonzero(y_a == 1), size=n_half, replace=False),
        rng.choice(np.flatnonzero(y_a == 0),
                   size=E10["subset"]["n_events"] - n_half, replace=False),
    ]))
    sub = df_a.iloc[idx]

    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    q_cols = E01["features"]["quantum"]
    ang = AngleScaler().fit(df_a[q_cols].to_numpy(float))  # scaler = deployment's
    Z = ang.transform(sub[q_cols].to_numpy(float))
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])

    K_ideal = kernel_exact(Z, fm)
    np.save(RAW_DIR / "K_ideal.npy", K_ideal)
    np.save(RAW_DIR / "subset_row_ids.npy", sub["row_id"].to_numpy())
    np.save(RAW_DIR / "subset_labels.npy", sub["labels"].to_numpy())
    pairs = list(combinations(range(len(Z)), 2))
    log(f"subset ready: {len(Z)} events, {len(pairs)} pairs; K_ideal saved")

    # -- Circuits (compute–uncompute) ---------------------------------------
    circuits = []
    for i, j in pairs:
        qc = QuantumCircuit(len(q_cols))
        qc.compose(fm(Z[i]), inplace=True)
        qc.compose(fm(Z[j]).inverse(), inplace=True)
        qc.measure_all()
        circuits.append(qc)

    # -- Backend + transpile + submit ---------------------------------------
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=get_token())
    backends = [b for b in svc.backends() if b.status().operational]
    backend = min(backends, key=lambda b: b.status().pending_jobs)
    log(f"backend: {backend.name} (pending {backend.status().pending_jobs})")

    tqc = transpile(circuits, backend=backend,
                    optimization_level=E10["transpile"]["optimization_level"],
                    seed_transpiler=E10["subset"]["seed"])
    depths = [c.depth() for c in tqc]
    twoq = [sum(1 for inst in c.data if inst.operation.num_qubits == 2)
            for c in tqc]
    log(f"transpiled: depth med {int(np.median(depths))} "
        f"[{min(depths)}, {max(depths)}], 2q-gates med {int(np.median(twoq))}")

    # Calibration snapshot (best-effort; formats vary by backend generation)
    calib = {"backend": backend.name, "num_qubits": backend.num_qubits}
    try:
        props = backend.properties()
        calib["last_update_date"] = str(props.last_update_date)
    except Exception as e:
        calib["properties_note"] = f"unavailable: {e}"

    sampler = SamplerV2(mode=backend)
    job = sampler.run(tqc, shots=E10["shots"])
    provenance = {
        "experiment": "E10",
        "job_id": job.job_id(),
        "backend": backend.name,
        "shots": E10["shots"],
        "n_events": len(Z),
        "n_circuits": len(tqc),
        "transpile": {"optimization_level": E10["transpile"]["optimization_level"],
                      "depth_median": int(np.median(depths)),
                      "depth_min": int(min(depths)), "depth_max": int(max(depths)),
                      "twoq_median": int(np.median(twoq))},
        "calibration": calib,
        "submitted_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qksvc_params": {k: str(v) for k, v in qp.items()},
        "mitigation": "none (raw counts; any mitigation would be reported)",
    }
    (RAW_DIR / "job_provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8")
    log(f"SUBMITTED job {job.job_id()} to {backend.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
