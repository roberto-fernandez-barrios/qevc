"""E16 hardware arm (analyze) — C_ideal vs C_shots vs C_hw at micro-scale.

Consumes the completed QPU job (raw counts), assembles the 100%-hardware
train and cross Grams, builds the micro-deployment in three kernel regimes
(ideal / finite-shot at the same budget / hardware), and runs the auditor
end-to-end on each: per-environment accuracy claims resolved from label
streams drawn from the micro test populations (paired across regimes).

The honest scale statement: claims resolvable at n~10 events are the
very-wide-margin ones; the sim arm predicts those are noise-stable, and
this is the direct hardware test of that prediction. Near-margin claims
abstain at micro-scale — fail-closed on a real device.

Outputs: results/tables/E16_hw.json (+ K_hw blocks archived).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from sklearn.svm import SVC  # noqa: E402

from qevc.auditing.claims import Claim, resolve_claim  # noqa: E402
from qevc.geometry.descriptors import (  # noqa: E402
    effective_rank,
    psd_violation,
)
from qevc.models.common import class_balanced_weights  # noqa: E402
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

RAW_DIR = REPO / "results/raw/E16_hw"
TAUS = [0.55, 0.65, 0.75]
N_MAX = 2000
AUDIT_SEEDS = 10
ALPHA = 0.05
SHOT_SEEDS = [1, 2, 3]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_token() -> str:
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("IBM_QUANTUM_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no token in .env")


def stable_rng(*parts) -> np.random.Generator:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def main() -> int:
    t0 = time.time()
    prov = json.loads((RAW_DIR / "job_provenance.json").read_text())
    pairs = json.loads((RAW_DIR / "pair_order.json").read_text())
    K_ideal_tr = np.load(RAW_DIR / "K_ideal_train.npy")
    K_ideal_cx = np.load(RAW_DIR / "K_ideal_cross.npy")
    y_tr = np.load(RAW_DIR / "train_labels.npy")
    w_tr = np.load(RAW_DIR / "train_weights.npy")
    y_te = np.load(RAW_DIR / "test_labels.npy")
    te_env = json.loads((RAW_DIR / "test_envs.json").read_text())
    n_tr, n_te = len(y_tr), len(y_te)
    shots = prov["shots"]

    # -- fetch counts ---------------------------------------------------------
    from qiskit_ibm_runtime import QiskitRuntimeService  # noqa: PLC0415
    svc = QiskitRuntimeService(channel="ibm_quantum_platform",
                               token=get_token())
    job = svc.job(prov["job_id"])
    status = str(job.status())
    log(f"job {prov['job_id']} status: {status}")
    if "DONE" not in status.upper():
        log("job not complete — aborting analysis (rerun later)")
        return 1
    result = job.result()
    fidelities = []
    raw_counts = []
    for res in result:
        counts = res.data.meas.get_counts()
        zeros = "0" * len(next(iter(counts)))
        f = counts.get(zeros, 0) / sum(counts.values())
        fidelities.append(f)
        raw_counts.append(counts)
    (RAW_DIR / "raw_counts.json").write_text(json.dumps(raw_counts),
                                             encoding="utf-8")
    fidelities = np.array(fidelities)

    n_train_pairs = len(pairs["train_pairs"])
    K_hw_tr = np.eye(n_tr)
    for (i, j), f in zip(pairs["train_pairs"], fidelities[:n_train_pairs]):
        K_hw_tr[i, j] = K_hw_tr[j, i] = f
    K_hw_cx = np.zeros((n_tr, n_te))
    for (i, j), f in zip(pairs["cross_pairs"], fidelities[n_train_pairs:]):
        K_hw_cx[i, j] = f
    np.save(RAW_DIR / "K_hw_train.npy", K_hw_tr)
    np.save(RAW_DIR / "K_hw_cross.npy", K_hw_cx)

    # -- kernel diagnostics ---------------------------------------------------
    def frob(a, b):
        return float(np.linalg.norm(a - b) / np.linalg.norm(b))

    diag = {
        "train_frob_rel_err": round(frob(K_hw_tr, K_ideal_tr), 5),
        "cross_frob_rel_err": round(frob(K_hw_cx, K_ideal_cx), 5),
        "train_mean_bias": round(float(np.mean(
            (K_hw_tr - K_ideal_tr)[np.triu_indices(n_tr, 1)])), 5),
        "psd_violation": round(float(psd_violation(K_hw_tr)), 6),
        "eff_rank_hw": round(float(effective_rank(K_hw_tr)), 2),
        "eff_rank_ideal": round(float(effective_rank(K_ideal_tr)), 2),
    }
    # shot-only comparators at the same budget (D-007 law)
    shot_frobs = []
    for s in SHOT_SEEDS:
        rng = stable_rng("hwshots", s)
        est = rng.binomial(shots, np.clip(K_ideal_tr, 0, 1)) / shots
        iu = np.triu_indices(n_tr, 1)
        sym = np.eye(n_tr)
        sym[iu] = est[iu]
        sym.T[iu] = est[iu]
        shot_frobs.append(frob(sym, K_ideal_tr))
    diag["shot_only_frob_mean"] = round(float(np.mean(shot_frobs)), 5)
    diag["device_excess_frob"] = round(
        diag["train_frob_rel_err"] - diag["shot_only_frob_mean"], 5)

    # -- micro-deployments in three regimes ----------------------------------
    def deploy(K_train, K_cross) -> np.ndarray:
        svc_m = SVC(kernel="precomputed", C=1.0)
        svc_m.fit(K_train, y_tr,
                  sample_weight=class_balanced_weights(y_tr, w_tr))
        pred = (svc_m.decision_function(K_cross.T) >= 0).astype(int)
        return (pred == y_te).astype(float)

    regimes = {"ideal": deploy(K_ideal_tr, K_ideal_cx),
               "hardware": deploy(K_hw_tr, K_hw_cx)}
    for s in SHOT_SEEDS:
        rng = stable_rng("deployshots", s)
        est_tr = rng.binomial(shots, np.clip(K_ideal_tr, 0, 1)) / shots
        iu = np.triu_indices(n_tr, 1)
        sym = np.eye(n_tr)
        sym[iu] = est_tr[iu]
        sym.T[iu] = est_tr[iu]
        est_cx = rng.binomial(shots, np.clip(K_ideal_cx, 0, 1)) / shots
        regimes[f"shots_s{s}"] = deploy(sym, est_cx)

    # -- auditor at micro-scale (paired streams across regimes) --------------
    envs = sorted(set(te_env))
    te_env = np.array(te_env)
    verdicts: dict = {}
    for regime, correct in regimes.items():
        verdicts[regime] = {}
        for env in envs:
            mask = te_env == env
            pop = correct[mask]
            m_t = float(pop.mean())
            for tau in TAUS:
                counts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                for s in range(AUDIT_SEEDS):
                    rng = stable_rng("E16hw", env, tau, s)   # paired via key
                    idx = rng.integers(0, len(pop), size=N_MAX)
                    cs = empirical_bernstein_cs(pop[idx], alpha=ALPHA)
                    res = resolve_claim(Claim("acc", tau), cs)
                    counts[res.verdict.value] += 1
                verdicts[regime][f"{env}|tau{tau}"] = {
                    "m_target": round(m_t, 4), "verdicts": counts}

    flips = {}
    for regime in [r for r in regimes if r != "ideal"]:
        n_diff = 0
        cells = 0
        for cell, v in verdicts[regime].items():
            ideal_top = max(verdicts["ideal"][cell]["verdicts"],
                            key=verdicts["ideal"][cell]["verdicts"].get)
            top = max(v["verdicts"], key=v["verdicts"].get)
            cells += 1
            n_diff += top != ideal_top
        flips[regime] = {"cells": cells, "majority_verdict_flips": n_diff}

    out = {
        "experiment": "E16_hw",
        "job_id": prov["job_id"], "backend": prov["backend"],
        "shots": shots, "n_train": n_tr, "n_test": n_te,
        "kernel_diagnostics": diag,
        "auditor_verdicts": verdicts,
        "verdict_flips_vs_ideal": flips,
        "scale_statement": "claims resolvable at micro-scale are wide-margin "
                           "by construction; near-margin claims abstain "
                           "(fail-closed on hardware)",
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E16_hw.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    manifest = RunManifest(
        experiment_id="E16hw", config={"provenance": prov}, seed=1616,
        dataset_hashes={},
        backend={"name": prov["backend"], "job_id": prov["job_id"]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E16 hw analysis complete in {out['wall_seconds']} s")
    log(json.dumps(diag, indent=1))
    log(json.dumps(flips, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
