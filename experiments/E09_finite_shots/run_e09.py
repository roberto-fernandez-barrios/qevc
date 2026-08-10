"""E09 — Finite-shot kernel study (spec §18, §28; H6).

The SAME exact fidelity Grams drive every shot budget: per (shots, seed) each
Gram entry is resampled from Binomial(shots, K_exact)/shots — exactly the
compute–uncompute sampling law (decision D-007) — so shot noise is isolated
from every other effect. Per configuration we measure:

- kernel estimation error (relative Frobenius), PSD violation, effective-rank
  distortion of the training Gram;
- classifier AUC across the predeclared environment subset (deployment
  protocol: calibration + threshold frozen on that configuration's own
  source_val scores — a finite-shot deployment owns its whole pipeline);
- certification stability: the E05-style auditor re-run per configuration;
  verdict flips vs the exact-kernel model's verdicts;
- H6 interaction: deviation of each configuration's TES response from the
  exact kernel's TES response.

Outputs: results/tables/E09_shots.json (Fig. 8 data).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from sklearn.svm import SVC  # noqa: E402

from qevc.auditing.claims import Claim, resolve_claim  # noqa: E402
from qevc.geometry.descriptors import effective_rank, psd_violation  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.metrics.classifier import weighted_auc  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E09 = yaml.safe_load((REPO / "configs/experiments/E09.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import parse_params  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sample_gram(K: np.ndarray, shots: int, rng: np.random.Generator,
                symmetric: bool) -> np.ndarray:
    """Binomial(shots, K)/shots per entry — the D-007 sampling law."""
    Kc = np.clip(K, 0.0, 1.0)
    if not symmetric:
        return rng.binomial(shots, Kc) / shots
    n = K.shape[0]
    iu = np.triu_indices(n, k=1)
    est = np.zeros_like(K)
    est[iu] = rng.binomial(shots, Kc[iu]) / shots
    est = est + est.T
    np.fill_diagonal(est, 1.0)
    return est


def stream_seed(tag: str, s: int) -> int:
    digest = hashlib.sha256(f"{E09['audit']['seed_salt']}|{tag}|{s}".encode()).digest()
    return int.from_bytes(digest[:8], "little")


def audit_cell(correct: np.ndarray, m_s: float) -> dict[str, str]:
    """Majority verdict per delta over the audit replications."""
    a = E09["audit"]
    out = {}
    for d in a["deltas"]:
        tau = m_s - d
        counts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
        for s in range(a["audit_seeds"]):
            rng = np.random.default_rng(stream_seed(f"{tau:.5f}|{len(correct)}", s))
            x = correct[rng.integers(0, len(correct), size=a["n_max"])]
            cs = empirical_bernstein_cs(x, alpha=a["alpha"])
            counts[resolve_claim(Claim("acc", tau), cs).verdict.value] += 1
        out[str(d)] = max(counts, key=counts.get)
    return out


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    df_a = tier_a_frame(frames["train"], E01["tier_a"]["n_train"],
                        E01["tier_a"]["seed"])
    sv_df = frames["source_val"]

    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    q_cols = E01["features"]["quantum"]
    ang = AngleScaler().fit(df_a[q_cols].to_numpy(float))
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    Z_tr = ang.transform(df_a[q_cols].to_numpy(float))
    y_tr = df_a["labels"].to_numpy()
    wb_tr = class_balanced_weights(y_tr, df_a["weights"].to_numpy())

    # Exact Grams, computed once (D-007: shots only resample these).
    K_tr = kernel_exact(Z_tr, fm)
    K_sv = kernel_exact(ang.transform(sv_df[q_cols].to_numpy(float)), fm, Z_tr)
    envs = {name: Environment(**cfg) for name, cfg in E09["environments"].items()}
    env_data = {}
    for name, env in envs.items():
        te = build_environment_dataset(raw, env, row_ids=raw_splits["nominal_test"])
        env_data[name] = {
            "K": kernel_exact(ang.transform(te[q_cols].to_numpy(float)), fm, Z_tr),
            "y": te["labels"].to_numpy(),
            "w": te["weights"].to_numpy(),
        }
        log(f"exact cross-Gram ready: {name} ({len(te):,} events)")

    y_sv, w_sv = sv_df["labels"].to_numpy(), sv_df["weights"].to_numpy()
    erank_exact = effective_rank(K_tr)

    def deploy_and_measure(K_train, K_source_val, K_envs, tag) -> dict:
        svc = SVC(kernel="precomputed", C=qp["C"])
        svc.fit(K_train, y_tr, sample_weight=wb_tr)
        s_sv = svc.decision_function(K_source_val)
        cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
        p_sv = cal.predict_proba(s_sv)
        thr = ba_optimal_threshold(y_sv, p_sv, w_sv)
        m_s = float(np.mean((p_sv >= thr).astype(int) == y_sv))
        entry: dict = {"m_source": round(m_s, 5), "envs": {}}
        for name, K_env in K_envs.items():
            p = cal.predict_proba(svc.decision_function(K_env))
            y, w = env_data[name]["y"], env_data[name]["w"]
            correct = ((p >= thr).astype(int) == y).astype(float)
            entry["envs"][name] = {
                "auc": round(float(weighted_auc(y, p, w)), 5),
                "m_target": round(float(correct.mean()), 5),
                "verdicts": audit_cell(correct, m_s),
            }
        return entry

    out: dict = {"experiment": "E09", "exact": {}, "configs": {}}
    out["exact"] = deploy_and_measure(
        K_tr, K_sv, {n: d["K"] for n, d in env_data.items()}, "exact")
    out["exact"]["kernel"] = {"eff_rank": round(erank_exact, 2),
                              "psd_violation": 0.0, "frob_rel_err": 0.0}
    log("exact baseline done")

    for shots in E09["shots_grid"]:
        for ks in E09["kernel_seeds"]:
            rng = np.random.default_rng(stream_seed(f"gram|{shots}", ks))
            Kt = sample_gram(K_tr, shots, rng, symmetric=True)
            Ks = sample_gram(K_sv, shots, rng, symmetric=False)
            Ke = {n: sample_gram(d["K"], shots, rng, symmetric=False)
                  for n, d in env_data.items()}
            entry = deploy_and_measure(Kt, Ks, Ke, f"{shots}|{ks}")
            entry["kernel"] = {
                "frob_rel_err": round(float(
                    np.linalg.norm(Kt - K_tr) / np.linalg.norm(K_tr)), 5),
                "psd_violation": round(float(psd_violation(Kt)), 6),
                "eff_rank": round(float(effective_rank(Kt)), 2),
            }
            out["configs"][f"shots{shots}_seed{ks}"] = entry
            log(f"shots={shots} kseed={ks}: "
                f"frob={entry['kernel']['frob_rel_err']:.4f} "
                f"auc_nom={entry['envs']['nominal']['auc']:.4f}")

    # ---- Synthesis: flips and H6 interaction ------------------------------
    exact_verdicts = {
        (n, d): v for n, e in out["exact"]["envs"].items()
        for d, v in e["verdicts"].items()
    }
    for cfg, entry in out["configs"].items():
        flips = sum(
            1 for n, e in entry["envs"].items()
            for d, v in e["verdicts"].items()
            if v != exact_verdicts[(n, d)]
        )
        entry["verdict_flips_vs_exact"] = flips
    exact_tes = {n: out["exact"]["envs"]["nominal"]["auc"] - e["auc"]
                 for n, e in out["exact"]["envs"].items() if n.startswith("tes")}
    for cfg, entry in out["configs"].items():
        entry["tes_response_deviation"] = {
            n: round((entry["envs"]["nominal"]["auc"] - entry["envs"][n]["auc"])
                     - exact_tes[n], 5)
            for n in exact_tes
        }

    out["wall_seconds"] = round(time.time() - t0, 1)
    out_path = REPO / "results/tables/E09_shots.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E09", config={"E01": E01, "E09": E09}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E09 complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
