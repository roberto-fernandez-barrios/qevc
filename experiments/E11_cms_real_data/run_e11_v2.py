"""E11v2 — Strengthened CMS real-data demonstration (registry E11v2; D-026).

Same frozen pipeline and claims ledger as E11, with the collision-data side
on the FULL Run2012B+C TauPlusX files (~10x the mirror statistics) and MC
re-weighted to the full luminosity. The mirror-based E11 v1 ledger is kept
and compared claim-by-claim (registered falsifier: full-data CR ratios
moving outside the mirror intervals beyond combined uncertainties would
flag sample fragility — reported either way).

Outputs: results/tables/E11v2_cms_full.json.
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

from qevc.data.cms_htautau import FEATURES, LUMI_PB, SAMPLES  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.metrics.classifier import weighted_auc  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
V2 = yaml.safe_load((REPO / "configs/experiments/E11v2.yaml").read_text())
V1_RESULTS = json.loads((REPO / V2["compare_to_v1"]).read_text())
CMS = REPO / V2["cms_interim"]

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import parse_params  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    mc, data = [], []
    for stem, (_proc, _sig, xsec) in SAMPLES.items():
        df = pd.read_parquet(CMS / f"{stem}.parquet")
        (data if xsec is None else mc).append(df)
    return (pd.concat(mc, ignore_index=True),
            pd.concat(data, ignore_index=True))


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(V2["train"]["seed"])
    mc, data = load_all()
    log(f"MC: {len(mc):,} selected; data: {len(data):,} selected (FULL runs)")

    mc_sr, mc_ss = mc[mc["os"]], mc[~mc["os"]]
    data_sr, data_ss = data[data["os"]], data[~data["os"]]

    idx = rng.permutation(len(mc_sr))
    n_val = int(V2["train"]["val_fraction"] * len(mc_sr))
    val_df = mc_sr.iloc[idx[:n_val]]
    tr_df = mc_sr.iloc[idx[n_val:]]
    y_tr, w_tr = tr_df["labels"].to_numpy(), tr_df["weights"].to_numpy()
    y_val, w_val = val_df["labels"].to_numpy(), val_df["weights"].to_numpy()

    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    xp = parse_params(E01_RESULTS["tiers"]["A"]["xgboost"]["best_params"])

    n_q = V2["train"]["qksvc_n_train"]
    pools = [np.flatnonzero(y_tr == c) for c in (0, 1)]
    fr = [len(p) / len(y_tr) for p in pools]
    q_idx = np.sort(np.concatenate([
        rng.choice(p, size=round(n_q * f), replace=False)
        for p, f in zip(pools, fr)]))
    Xq = tr_df.iloc[q_idx][FEATURES].to_numpy(float)
    yq, wq = y_tr[q_idx], w_tr[q_idx]

    models = {}
    qk = qksvc_builder(qp, V2["train"]["seed"])
    qk.fit(Xq, yq, sample_weight=class_balanced_weights(yq, wq))
    models["qksvc"] = qk
    xgb = build("xgboost", xp, V2["train"]["seed"])
    xgb.fit(tr_df[FEATURES].to_numpy(float), y_tr,
            sample_weight=class_balanced_weights(y_tr, w_tr))
    models["xgboost"] = xgb

    frozen = {}
    for name, model in models.items():
        s_val = model.scores(val_df[FEATURES].to_numpy(float))
        cal = PlattCalibrator().fit(s_val, y_val, w_val)
        p_val = cal.predict_proba(s_val)
        thr = ba_optimal_threshold(y_val, p_val, w_val)
        frozen[name] = {
            "cal": cal, "thr": thr,
            "m_source": float(np.mean((p_val >= thr).astype(int) == y_val)),
            "auc_mc_val": float(weighted_auc(y_val, p_val, w_val)),
        }
        log(f"{name}: MC-val AUC {frozen[name]['auc_mc_val']:.4f}  "
            f"M_S {frozen[name]['m_source']:.4f}")

    # -- I1 sensor: QK MMD2 MC vs FULL data ---------------------------------
    cfg = V2["sensor"]
    srng = np.random.default_rng(cfg["seed"])
    ang = AngleScaler().fit(Xq)
    fm = build_feature_map(len(FEATURES), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])

    def mmd2(A: np.ndarray, B: np.ndarray) -> float:
        Za, Zb = ang.transform(A), ang.transform(B)
        Kaa, Kbb = kernel_exact(Za, fm), kernel_exact(Zb, fm)
        Kab = kernel_exact(Za, fm, Zb)
        return float(Kaa.mean() + Kbb.mean() - 2.0 * Kab.mean())

    mc_pool = mc_sr[FEATURES].to_numpy(float)
    data_pool = data_sr[FEATURES].to_numpy(float)
    n_s = cfg["n_sample"]
    floor_draws = []
    for _ in range(cfg["n_noise_draws"]):
        pick = srng.choice(len(mc_pool), size=2 * n_s, replace=False)
        floor_draws.append(mmd2(mc_pool[pick[:n_s]], mc_pool[pick[n_s:]]))
    obs_draw = mmd2(mc_pool[srng.choice(len(mc_pool), n_s, replace=False)],
                    data_pool[srng.choice(len(data_pool), n_s, replace=False)])
    noise_floor = float(np.max(floor_draws))
    alarm = obs_draw > noise_floor
    log(f"sensor: MC-vs-data MMD2 {obs_draw:.6f} vs floor {noise_floor:.6f} "
        f"-> alarm={alarm}")

    # -- Control regions -----------------------------------------------------
    mt_cut = V2["claims"]["C2_w_norm"]["mt_cut"]
    tol = V2["claims"]["C2_w_norm"]["tolerance"]
    d_wcr = int((data_sr["mass_transverse_met_lep"] > mt_cut).sum())
    m_wcr = float(mc_sr.loc[mc_sr["mass_transverse_met_lep"] > mt_cut,
                            "weights"].sum())
    r = d_wcr / m_wcr
    r_lo = stats.chi2.ppf(0.025, 2 * d_wcr) / 2 / m_wcr
    r_hi = stats.chi2.ppf(0.975, 2 * (d_wcr + 1)) / 2 / m_wcr

    d_ss = int(len(data_ss))
    m_ss = float(mc_ss["weights"].sum())
    ss_excess = d_ss - m_ss
    ss_z = ss_excess / np.sqrt(max(d_ss, 1.0))

    ledger = {}
    ledger["C1_event_accuracy"] = {
        "text": V2["claims"]["C1_event_accuracy"]["text"],
        "requires": V2["claims"]["C1_event_accuracy"]["requires"],
        "verdict": "UNRESOLVED",
        "reason": "no event-level truth exists on collision data — "
                  "fail-closed by construction (unchanged from v1; more "
                  "data cannot change this, which is the point)",
    }
    c2_in = r_lo >= 1 - tol and r_hi <= 1 + tol
    c2_out = r_hi < 1 - tol or r_lo > 1 + tol
    ledger["C2_w_norm"] = {
        "text": V2["claims"]["C2_w_norm"]["text"],
        "requires": V2["claims"]["C2_w_norm"]["requires"],
        "evidence": {"data_yield": d_wcr, "mc_yield": round(m_wcr, 1),
                     "ratio": round(r, 4),
                     "ratio_ci95": [round(r_lo, 4), round(r_hi, 4)]},
        "verdict": ("SUPPORTED" if c2_in else "REFUTED" if c2_out
                    else "UNRESOLVED"),
    }
    ledger["C3_no_shift"] = {
        "text": V2["claims"]["C3_no_shift"]["text"],
        "requires": V2["claims"]["C3_no_shift"]["requires"],
        "evidence": {"mmd2_mc_vs_data": round(obs_draw, 6),
                     "noise_floor_max": round(noise_floor, 6),
                     "noise_floor_median": round(float(np.median(floor_draws)), 6)},
        "verdict": "REFUTED" if alarm else "SUPPORTED",
    }
    ledger["C4_ss_qcd"] = {
        "text": V2["claims"]["C4_ss_qcd"]["text"],
        "requires": V2["claims"]["C4_ss_qcd"]["requires"],
        "evidence": {"data_ss": d_ss, "mc_ss": round(m_ss, 1),
                     "excess": round(ss_excess, 1), "z": round(float(ss_z), 2)},
        "verdict": "SUPPORTED" if ss_z > 3 else "UNRESOLVED",
    }

    # -- mirror-vs-full comparison (registered falsifier) --------------------
    v1 = V1_RESULTS["claims_ledger"]
    comparison = {}
    for cid in ledger:
        row = {"v1_verdict": v1[cid]["verdict"],
               "v2_verdict": ledger[cid]["verdict"],
               "verdict_stable": v1[cid]["verdict"] == ledger[cid]["verdict"]}
        if cid == "C2_w_norm":
            r1 = v1[cid]["evidence"]["ratio"]
            ci1 = v1[cid]["evidence"]["ratio_ci95"]
            row["v1_ratio"] = r1
            row["v2_ratio"] = round(r, 4)
            # combined-uncertainty consistency: v2 ratio inside v1 CI widened
            # by the (small) v2 CI half-width
            half2 = (r_hi - r_lo) / 2
            row["consistent"] = bool(ci1[0] - half2 <= r <= ci1[1] + half2)
        if cid == "C4_ss_qcd":
            row["v1_z"] = v1[cid]["evidence"]["z"]
            row["v2_z"] = round(float(ss_z), 2)
        if cid == "C3_no_shift":
            row["v1_mmd2"] = v1[cid]["evidence"]["mmd2_mc_vs_data"]
            row["v2_mmd2"] = round(obs_draw, 6)
        comparison[cid] = row

    diagnostics = {}
    for name, model in models.items():
        p_data = frozen[name]["cal"].predict_proba(model.scores(data_pool))
        p_mcval = frozen[name]["cal"].predict_proba(
            model.scores(val_df[FEATURES].to_numpy(float)))
        ks = stats.ks_2samp(p_data, p_mcval)
        diagnostics[name] = {
            "auc_mc_val": round(frozen[name]["auc_mc_val"], 4),
            "m_source": round(frozen[name]["m_source"], 4),
            "score_ks_data_vs_mcval": {"stat": round(float(ks.statistic), 4),
                                       "p": float(ks.pvalue)},
        }

    out = {
        "experiment": "E11v2",
        "lumi_pb": LUMI_PB,
        "samples": {"mc_selected": int(len(mc)), "data_selected": int(len(data)),
                    "mc_sr": int(len(mc_sr)), "data_sr": int(len(data_sr)),
                    "mc_ss": int(len(mc_ss)), "data_ss": int(len(data_ss))},
        "claims_ledger": ledger,
        "mirror_vs_full_comparison": comparison,
        "deployment_diagnostics": diagnostics,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E11v2_cms_full.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    manifest = RunManifest(
        experiment_id="E11v2",
        config={"E11v2": V2, "lumi_pb": LUMI_PB},
        seed=V2["train"]["seed"],
        dataset_hashes={p.name: file_sha256(p)
                        for p in sorted(CMS.glob("*.parquet"))},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E11v2 complete in {out['wall_seconds']} s -> {out_path}")
    print(json.dumps({k: v["verdict"] for k, v in ledger.items()}, indent=1))
    print(json.dumps(comparison, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
