"""E10 (analysis phase) — K_ideal vs K_shots vs K_hw (spec §19).

Fetches the completed SamplerV2 job, reconstructs K_hw from raw all-zeros
frequencies, saves raw counts, and compares the three kernel regimes:
Frobenius distance, PSD violation, effective rank, per-entry residual
statistics, and a leave-one-out SVC agreement check on the 32-event subset
(qualitative — hardware is never the statistical backbone).

Outputs: results/tables/E10_hardware.json + raw artifacts under
results/raw/E10_hw/.
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

from qiskit_ibm_runtime import QiskitRuntimeService  # noqa: E402
from sklearn.svm import SVC  # noqa: E402

from qevc.geometry.descriptors import effective_rank, psd_violation  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E10 = yaml.safe_load((REPO / "configs/experiments/E10.yaml").read_text())
RAW_DIR = REPO / E10["outputs_raw"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_token() -> str:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("IBM_QUANTUM_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no token in .env")


def gram_stats(K: np.ndarray, K_ref: np.ndarray) -> dict:
    diff = K - K_ref
    iu = np.triu_indices(len(K), k=1)
    return {
        "frob_rel_err": round(float(np.linalg.norm(diff) / np.linalg.norm(K_ref)), 5),
        "mean_abs_entry_err": round(float(np.abs(diff[iu]).mean()), 5),
        "max_abs_entry_err": round(float(np.abs(diff[iu]).max()), 5),
        "mean_bias": round(float(diff[iu].mean()), 5),
        "psd_violation": round(float(psd_violation(K)), 6),
        "eff_rank": round(float(effective_rank(K)), 2),
    }


def loo_accuracy(K: np.ndarray, y: np.ndarray, C: float) -> float:
    n = len(y)
    hits = 0
    for i in range(n):
        keep = np.arange(n) != i
        svc = SVC(kernel="precomputed", C=C)
        svc.fit(K[np.ix_(keep, keep)], y[keep])
        hits += int(svc.predict(K[i][keep][None, :])[0] == y[i])
    return hits / n


def main() -> int:
    prov = json.loads((RAW_DIR / "job_provenance.json").read_text())
    K_ideal = np.load(RAW_DIR / "K_ideal.npy")
    y = np.load(RAW_DIR / "subset_labels.npy")
    n = len(y)
    pairs = list(combinations(range(n), 2))

    svc_conn = QiskitRuntimeService(channel="ibm_quantum_platform", token=get_token())
    job = svc_conn.job(prov["job_id"])
    status = str(job.status())
    log(f"job {prov['job_id']}: {status}")
    if "DONE" not in status:
        # Failed hardware runs are REPORTED, never hidden (spec §19).
        out = {"experiment": "E10", "job_id": prov["job_id"],
               "status": status, "note": "terminal non-DONE status — reported"}
        (REPO / "results/tables/E10_hardware.json").write_text(
            json.dumps(out, indent=2), encoding="utf-8")
        return 1

    result = job.result()
    K_hw = np.eye(n)
    counts_dump = {}
    for (i, j), pub in zip(pairs, result):
        counts = pub.data.meas.get_counts()
        shots = sum(counts.values())
        zeros_key = "0" * len(next(iter(counts)))  # width from the data itself
        k = counts.get(zeros_key, 0) / shots
        K_hw[i, j] = K_hw[j, i] = k
        counts_dump[f"{i}-{j}"] = counts
    np.save(RAW_DIR / "K_hw.npy", K_hw)
    (RAW_DIR / "raw_counts.json").write_text(
        json.dumps(counts_dump), encoding="utf-8")
    log("K_hw reconstructed and raw counts saved")

    # Local finite-shot replicas at the same budget (D-007 law).
    rngs = [np.random.default_rng(s) for s in E10["comparison"]["kernel_seeds_local"]]
    iu = np.triu_indices(n, k=1)
    k_shots_list = []
    for rng in rngs:
        Ks = np.eye(n)
        vals = rng.binomial(E10["shots"], np.clip(K_ideal[iu], 0, 1)) / E10["shots"]
        Ks[iu] = vals
        Ks = np.triu(Ks, 1) + np.triu(Ks, 1).T + np.eye(n)
        k_shots_list.append(Ks)

    C = float(json.loads((REPO / "results/tables/E01_nominal.json").read_text())
              ["tiers"]["A"]["qksvc"]["best_params"]["C"])
    out = {
        "experiment": "E10",
        "job_id": prov["job_id"],
        "backend": prov["backend"],
        "shots": prov["shots"],
        "n_events": n,
        "provenance": prov,
        "kernels": {
            "ideal": {"eff_rank": round(float(effective_rank(K_ideal)), 2),
                      "loo_acc": round(loo_accuracy(K_ideal, y, C), 4)},
            "shots_local": {
                "stats_vs_ideal": [gram_stats(Ks, K_ideal) for Ks in k_shots_list],
                "loo_acc": [round(loo_accuracy(Ks, y, C), 4) for Ks in k_shots_list],
            },
            "hardware": {
                "stats_vs_ideal": gram_stats(K_hw, K_ideal),
                "loo_acc": round(loo_accuracy(K_hw, y, C), 4),
            },
        },
    }
    # Device-noise excess: hardware error beyond pure shot noise
    shot_frob = np.mean([s["frob_rel_err"]
                         for s in out["kernels"]["shots_local"]["stats_vs_ideal"]])
    out["device_noise_excess_frob"] = round(
        out["kernels"]["hardware"]["stats_vs_ideal"]["frob_rel_err"] - shot_frob, 5)

    out_path = REPO / "results/tables/E10_hardware.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E10", config={"E10": E10}, seed=E10["subset"]["seed"],
        backend={"name": prov["backend"], "job_id": prov["job_id"]},
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E10 analysis complete -> {out_path}")
    print(json.dumps(out["kernels"]["hardware"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
