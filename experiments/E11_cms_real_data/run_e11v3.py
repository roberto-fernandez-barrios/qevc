"""E11v3 — CMS ledger statistical hardening (registry E11v3; D-028).

Re-analysis of the archived E11v2 inputs only (frozen skims, frozen sensor
definition, frozen SR/CR rules). Two hardenings, both registered with a
BIDIRECTIONAL falsifier before this run:

  (i)  C2/C4 with MC-side statistics: per-process sqrt(sum w^2) propagated
       into the C2 ratio interval (log-delta method combined with the data
       Poisson term) and into the C4 z-score denominator.
  (ii) C3 as calibrated evidence instead of a 20-draw max-floor on a single
       observation draw: (a) null-calibrated p-value from 200 MC-vs-MC
       draws; (b) permutation test (999 permutations) on the pooled
       MC/data sample, per observation draw; 20 MC-vs-data observation
       draws. Decision rule (fixed here, before results): the claim-level
       p per calibration is the MEDIAN over the 20 observation draws;
       C3 stays REFUTED iff median p <= alpha under BOTH calibrations,
       otherwise the verdict is corrected to UNRESOLVED and published.

Integrity anchor: the exact v2 sensor draw (seed 1112) is replayed and its
MMD2 must reproduce the archived evidence value before anything new runs.

The sensor estimand is unchanged from v1/v2 (unweighted row samples); the
weighting caveat remains disclosed in the manuscript.

Outputs: results/tables/E11v3_cms_stats.json + manifest.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from scipy import stats  # noqa: E402

from qevc.data.cms_htautau import FEATURES, SAMPLES  # noqa: E402
from qevc.kernels.quantum import (  # noqa: E402
    _statevectors_fast,
    build_feature_map,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import parse_params  # noqa: E402

E11V3 = yaml.safe_load((REPO / "configs/experiments/E11v3.yaml").read_text())
V2 = yaml.safe_load((REPO / E11V3["base_config"]).read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
V2_RESULTS = json.loads(
    (REPO / "results/tables/E11v2_cms_full.json").read_text())
V1_RESULTS = json.loads((REPO / V2["compare_to_v1"]).read_text())
CMS = REPO / V2["cms_interim"]
ALPHA = E11V3["alpha"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    mc, data = [], []
    for stem, (_proc, _sig, xsec) in SAMPLES.items():
        df = pd.read_parquet(CMS / f"{stem}.parquet")
        (data if xsec is None else mc).append(df)
    return (pd.concat(mc, ignore_index=True),
            pd.concat(data, ignore_index=True))


def gram(Sa: np.ndarray, Sb: np.ndarray) -> np.ndarray:
    return np.abs(Sa @ Sb.conj().T) ** 2


def mmd2_from_blocks(Kaa, Kbb, Kab) -> float:
    return float(Kaa.mean() + Kbb.mean() - 2.0 * Kab.mean())


def mmd2_perm(K: np.ndarray, g: np.ndarray, n: int) -> float:
    """MMD2 for a permutation split given the pooled Gram K; g is the 0/1
    indicator of group A (|A| = n = |B|)."""
    h = 1.0 - g
    Kg = K @ g
    a = g @ Kg
    b = h @ (K @ h)
    ab = g @ (K @ h)
    return float(a / n**2 + b / n**2 - 2.0 * ab / n**2)


def main() -> int:
    t0 = time.time()
    mc, data = load_all()
    mc_sr, mc_ss = mc[mc["os"]], mc[~mc["os"]]
    data_sr, data_ss = data[data["os"]], data[~data["os"]]
    log(f"pools: mc_sr {len(mc_sr):,}  data_sr {len(data_sr):,}  "
        f"mc_ss {len(mc_ss):,}  data_ss {len(data_ss):,}")

    # ---- replicate the frozen sensor pieces deterministically (no training)
    rng = np.random.default_rng(V2["train"]["seed"])
    idx = rng.permutation(len(mc_sr))
    n_val = int(V2["train"]["val_fraction"] * len(mc_sr))
    tr_df = mc_sr.iloc[idx[n_val:]]
    y_tr = tr_df["labels"].to_numpy()
    n_q = V2["train"]["qksvc_n_train"]
    pools = [np.flatnonzero(y_tr == c) for c in (0, 1)]
    fr = [len(p) / len(y_tr) for p in pools]
    q_idx = np.sort(np.concatenate([
        rng.choice(p, size=round(n_q * f), replace=False)
        for p, f in zip(pools, fr)]))
    Xq = tr_df.iloc[q_idx][FEATURES].to_numpy(float)
    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    ang = AngleScaler().fit(Xq)
    fm = build_feature_map(len(FEATURES), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    log("frozen sensor pieces replicated (AngleScaler + feature map)")

    mc_pool = mc_sr[FEATURES].to_numpy(float)
    data_pool = data_sr[FEATURES].to_numpy(float)
    n_s = V2["sensor"]["n_sample"]

    # statevector cache for the full MC pool (draw Grams become matmuls)
    S_mc = _statevectors_fast(ang.transform(mc_pool), fm)
    log(f"MC statevectors cached: {S_mc.shape}")

    # ---- integrity anchor: replay the exact v2 draw (seed 1112)
    srng = np.random.default_rng(V2["sensor"]["seed"])
    v2_floor = []
    for _ in range(V2["sensor"]["n_noise_draws"]):
        pick = srng.choice(len(mc_pool), size=2 * n_s, replace=False)
        Ka = gram(S_mc[pick[:n_s]], S_mc[pick[:n_s]])
        Kb = gram(S_mc[pick[n_s:]], S_mc[pick[n_s:]])
        Kab = gram(S_mc[pick[:n_s]], S_mc[pick[n_s:]])
        v2_floor.append(mmd2_from_blocks(Ka, Kb, Kab))
    mc_pick = srng.choice(len(mc_pool), n_s, replace=False)
    data_pick = srng.choice(len(data_pool), n_s, replace=False)
    S_d0 = _statevectors_fast(ang.transform(data_pool[data_pick]), fm)
    obs_v2 = mmd2_from_blocks(gram(S_mc[mc_pick], S_mc[mc_pick]),
                              gram(S_d0, S_d0), gram(S_mc[mc_pick], S_d0))
    archived = V2_RESULTS["claims_ledger"]["C3_no_shift"]["evidence"][
        "mmd2_mc_vs_data"]
    if not np.isclose(obs_v2, archived, atol=5e-7):
        raise RuntimeError(f"v2 sensor replay mismatch: {obs_v2} vs {archived}")
    log(f"v2 observation draw reproduced: {obs_v2:.6f} (archived {archived})")

    # ---- new calibration (seed 1911)
    cal = E11V3["sensor_calibration"]
    crng = np.random.default_rng(cal["seed"])

    null_mmd2 = []
    for _ in range(cal["n_null_draws"]):
        pick = crng.choice(len(mc_pool), size=2 * n_s, replace=False)
        Ka = gram(S_mc[pick[:n_s]], S_mc[pick[:n_s]])
        Kb = gram(S_mc[pick[n_s:]], S_mc[pick[n_s:]])
        Kab = gram(S_mc[pick[:n_s]], S_mc[pick[n_s:]])
        null_mmd2.append(mmd2_from_blocks(Ka, Kb, Kab))
    null_mmd2 = np.array(null_mmd2)
    log(f"null calibrated: {len(null_mmd2)} MC-vs-MC draws "
        f"(mean {null_mmd2.mean():.7f}, max {null_mmd2.max():.7f})")

    obs_rows = []
    for d in range(cal["n_obs_draws"]):
        mpick = crng.choice(len(mc_pool), n_s, replace=False)
        dpick = crng.choice(len(data_pool), n_s, replace=False)
        S_a = S_mc[mpick]
        S_b = _statevectors_fast(ang.transform(data_pool[dpick]), fm)
        obs = mmd2_from_blocks(gram(S_a, S_a), gram(S_b, S_b), gram(S_a, S_b))
        p_null = float((1 + np.sum(null_mmd2 >= obs)) / (len(null_mmd2) + 1))

        S_pool = np.vstack([S_a, S_b])
        K = gram(S_pool, S_pool)
        count = 0
        for _b in range(cal["n_permutations"]):
            g = np.zeros(2 * n_s)
            g[crng.choice(2 * n_s, n_s, replace=False)] = 1.0
            if mmd2_perm(K, g, n_s) >= obs:
                count += 1
        p_perm = float((1 + count) / (cal["n_permutations"] + 1))
        obs_rows.append({"mmd2": round(obs, 7), "p_null": round(p_null, 5),
                         "p_perm": round(p_perm, 5)})
        log(f"obs draw {d}: mmd2 {obs:.7f}  p_null {p_null:.4f}  "
            f"p_perm {p_perm:.4f}")

    p_null_med = float(np.median([r["p_null"] for r in obs_rows]))
    p_perm_med = float(np.median([r["p_perm"] for r in obs_rows]))
    c3_refuted = p_null_med <= ALPHA and p_perm_med <= ALPHA
    c3_verdict = "REFUTED" if c3_refuted else "UNRESOLVED"

    # ---- C2 with MC-side statistics
    mt_cut = V2["claims"]["C2_w_norm"]["mt_cut"]
    tol = V2["claims"]["C2_w_norm"]["tolerance"]
    cr_mask = mc_sr["mass_transverse_met_lep"] > mt_cut
    d_wcr = int((data_sr["mass_transverse_met_lep"] > mt_cut).sum())
    w_cr = mc_sr.loc[cr_mask, "weights"].to_numpy()
    m_wcr = float(w_cr.sum())
    mc_relerr = float(np.sqrt(np.sum(w_cr**2)) / m_wcr)
    r = d_wcr / m_wcr
    # v2 data-only Garwood interval (for comparison)
    r_lo_d = stats.chi2.ppf(0.025, 2 * d_wcr) / 2 / m_wcr
    r_hi_d = stats.chi2.ppf(0.975, 2 * (d_wcr + 1)) / 2 / m_wcr
    # combined interval: log-delta with data Poisson + MC template terms
    sig_log = float(np.sqrt(1.0 / d_wcr + mc_relerr**2))
    r_lo_c = r * np.exp(-1.96 * sig_log)
    r_hi_c = r * np.exp(+1.96 * sig_log)
    c2_in = r_lo_c >= 1 - tol and r_hi_c <= 1 + tol
    c2_out = r_hi_c < 1 - tol or r_lo_c > 1 + tol
    c2_verdict = "SUPPORTED" if c2_in else "REFUTED" if c2_out else "UNRESOLVED"

    # ---- C4 with MC-side statistics
    d_ss = int(len(data_ss))
    w_ss = mc_ss["weights"].to_numpy()
    m_ss = float(w_ss.sum())
    excess = d_ss - m_ss
    z_v2 = excess / np.sqrt(max(d_ss, 1.0))
    z_corr = excess / np.sqrt(max(d_ss, 1.0) + float(np.sum(w_ss**2)))
    c4_verdict = "SUPPORTED" if z_corr > 3 else "UNRESOLVED"

    ledger = {
        "C1_event_accuracy": {
            "verdict": "UNRESOLVED",
            "reason": "fail-closed by construction (unchanged)",
        },
        "C2_w_norm": {
            "evidence": {
                "data_yield": d_wcr, "mc_yield": round(m_wcr, 1),
                "ratio": round(r, 4),
                "ratio_ci95_data_only": [round(r_lo_d, 4), round(r_hi_d, 4)],
                "mc_relerr": round(mc_relerr, 5),
                "ratio_ci95_with_mc_stat": [round(float(r_lo_c), 4),
                                            round(float(r_hi_c), 4)],
            },
            "verdict": c2_verdict,
        },
        "C3_no_shift": {
            "evidence": {
                "v2_replayed_mmd2": round(obs_v2, 7),
                "null_mean": round(float(null_mmd2.mean()), 7),
                "null_q95": round(float(np.quantile(null_mmd2, 0.95)), 7),
                "null_max": round(float(null_mmd2.max()), 7),
                "obs_draws": obs_rows,
                "p_null_median": round(p_null_med, 5),
                "p_perm_median": round(p_perm_med, 5),
            },
            "decision_rule": "REFUTED iff median p <= alpha under BOTH "
                             "calibrations (fixed pre-run)",
            "verdict": c3_verdict,
        },
        "C4_ss_qcd": {
            "evidence": {"data_ss": d_ss, "mc_ss": round(m_ss, 1),
                         "excess": round(excess, 1),
                         "z_data_only": round(float(z_v2), 2),
                         "z_with_mc_stat": round(float(z_corr), 2)},
            "verdict": c4_verdict,
        },
    }

    comparison = {}
    for cid in ledger:
        comparison[cid] = {
            "v1": V1_RESULTS["claims_ledger"][cid]["verdict"],
            "v2": V2_RESULTS["claims_ledger"][cid]["verdict"],
            "v3": ledger[cid]["verdict"],
            "verdict_stable": (V2_RESULTS["claims_ledger"][cid]["verdict"]
                               == ledger[cid]["verdict"]),
        }

    falsifier = {
        "c3_direction": ("refuted_stands_on_calibrated_grounds" if c3_refuted
                         else "corrected_to_unresolved_published"),
        "c2_verdict_changed": comparison["C2_w_norm"]["v3"]
        != comparison["C2_w_norm"]["v2"],
        "c4_z_below_5": bool(z_corr < 5),
    }

    out = {
        "experiment": "E11v3",
        "declared_status": "re-analysis of archived E11v2 inputs "
                           "(bidirectional falsifier frozen; D-028)",
        "claims_ledger": ledger,
        "v1_v2_v3_comparison": comparison,
        "falsifier": falsifier,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E11v3_cms_stats.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")

    manifest = RunManifest(
        experiment_id="E11v3",
        config={"E11v3": E11V3, "base": V2},
        seed=cal["seed"],
        dataset_hashes={p.name: file_sha256(p)
                        for p in sorted(CMS.glob("*.parquet"))},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E11v3 complete in {out['wall_seconds']} s -> {out_path}")
    print(json.dumps({k: v["verdict"] for k, v in ledger.items()}, indent=1))
    print(json.dumps(comparison, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
