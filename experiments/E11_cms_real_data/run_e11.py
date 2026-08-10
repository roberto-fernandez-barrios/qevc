"""E11 — Simulation-to-real fail-closed case study (spec §20, §28; H4 deployed).

Pipeline: MC-trained classifiers (E01-frozen hyperparameters, Level-II
features parallel to D-011) → REAL CMS collision data (Run2012B+C μτ_h,
NO event-level truth) → information-set-conditional claims ledger:

- C1 (event accuracy on data): requires I2 target labels, which DO NOT EXIST
  on collision data → UNRESOLVED by construction. The framework's flagship
  fail-closed behavior: it refuses to invent real-data accuracy (spec §20).
- C2 (W normalization in the high-mT control region): resolvable from
  aggregate CR yields — data/MC ratio with Poisson uncertainty.
- C3 (no MC→data shift at sensor sensitivity): I1 geometry — QK-MMD² between
  MC and data vs an MC-vs-MC bootstrap noise floor.
- C4 (SS-region QCD excess): resolvable from CR aggregates — the documented
  data-driven QCD method's premise, checked.

Outputs: results/tables/E11_cms_case_study.json (Fig. 9 data).
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

from qevc.data.cms_htautau import (  # noqa: E402
    EFFECTIVE_LUMI_PB,
    FEATURES,
    SAMPLES,
)
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
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E11 = yaml.safe_load((REPO / "configs/experiments/E11.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
CMS = REPO / "data/interim/cms"

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import parse_params  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    mc, data = [], []
    for stem, (proc, is_sig, xsec) in SAMPLES.items():
        df = pd.read_parquet(CMS / f"{stem}.parquet")
        (data if xsec is None else mc).append(df)
    return (pd.concat(mc, ignore_index=True),
            pd.concat(data, ignore_index=True))


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(E11["train"]["seed"])
    mc, data = load_all()
    log(f"MC: {len(mc):,} selected ({mc['labels'].sum():,} signal); "
        f"data: {len(data):,} selected")

    mc_sr, mc_ss = mc[mc["os"]], mc[~mc["os"]]
    data_sr, data_ss = data[data["os"]], data[~data["os"]]

    # -- Train on MC SR (train/val split) -----------------------------------
    idx = rng.permutation(len(mc_sr))
    n_val = int(E11["train"]["val_fraction"] * len(mc_sr))
    val_df = mc_sr.iloc[idx[:n_val]]
    tr_df = mc_sr.iloc[idx[n_val:]]
    y_tr, w_tr = tr_df["labels"].to_numpy(), tr_df["weights"].to_numpy()
    y_val, w_val = val_df["labels"].to_numpy(), val_df["weights"].to_numpy()

    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    xp = parse_params(E01_RESULTS["tiers"]["A"]["xgboost"]["best_params"])

    # QKSVC on a tier-A-scale stratified subsample (frozen hyperparams)
    n_q = E11["train"]["qksvc_n_train"]
    pools = [np.flatnonzero(y_tr == c) for c in (0, 1)]
    fr = [len(p) / len(y_tr) for p in pools]
    q_idx = np.sort(np.concatenate([
        rng.choice(p, size=round(n_q * f), replace=False)
        for p, f in zip(pools, fr)]))
    Xq = tr_df.iloc[q_idx][FEATURES].to_numpy(float)
    yq, wq = y_tr[q_idx], w_tr[q_idx]

    models = {}
    qk = qksvc_builder(qp, E11["train"]["seed"])
    qk.fit(Xq, yq, sample_weight=class_balanced_weights(yq, wq))
    models["qksvc"] = qk
    xgb = build("xgboost", xp, E11["train"]["seed"])
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

    # -- I1 geometry sensor: QK MMD² MC vs data, with MC-vs-MC noise floor --
    cfg = E11["sensor"]
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
        f"(median MC-vs-MC {np.median(floor_draws):.6f}) -> alarm={alarm}")

    # -- Control-region aggregates ------------------------------------------
    mt_cut = E11["claims"]["C2_w_norm"]["mt_cut"]
    tol = E11["claims"]["C2_w_norm"]["tolerance"]
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

    # -- Claims ledger -------------------------------------------------------
    ledger = {}
    ledger["C1_event_accuracy"] = {
        "text": E11["claims"]["C1_event_accuracy"]["text"],
        "requires": E11["claims"]["C1_event_accuracy"]["requires"],
        "verdict": "UNRESOLVED",
        "reason": "no event-level truth exists on collision data; certification "
                  "requires I2 evidence the deployment does not possess "
                  "(fail-closed by construction, spec §20)",
    }
    c2_in = r_lo >= 1 - tol and r_hi <= 1 + tol
    c2_out = r_hi < 1 - tol or r_lo > 1 + tol
    ledger["C2_w_norm"] = {
        "text": E11["claims"]["C2_w_norm"]["text"],
        "requires": E11["claims"]["C2_w_norm"]["requires"],
        "evidence": {"data_yield": d_wcr, "mc_yield": round(m_wcr, 1),
                     "ratio": round(r, 4),
                     "ratio_ci95": [round(r_lo, 4), round(r_hi, 4)]},
        "verdict": ("SUPPORTED" if c2_in else "REFUTED" if c2_out else "UNRESOLVED"),
        "note": "MC lacks QCD; high-mT region is W-dominated (documented)",
    }
    ledger["C3_no_shift"] = {
        "text": E11["claims"]["C3_no_shift"]["text"],
        "requires": E11["claims"]["C3_no_shift"]["requires"],
        "evidence": {"mmd2_mc_vs_data": round(obs_draw, 6),
                     "noise_floor_max": round(noise_floor, 6),
                     "noise_floor_median": round(float(np.median(floor_draws)), 6)},
        "verdict": "REFUTED" if alarm else "SUPPORTED",
        "note": "REFUTED = shift detected -> geometry alarm active; the alarm "
                "can only veto, never certify (D-006)",
    }
    ledger["C4_ss_qcd"] = {
        "text": E11["claims"]["C4_ss_qcd"]["text"],
        "requires": E11["claims"]["C4_ss_qcd"]["requires"],
        "evidence": {"data_ss": d_ss, "mc_ss": round(m_ss, 1),
                     "excess": round(ss_excess, 1), "z": round(float(ss_z), 2)},
        "verdict": "SUPPORTED" if ss_z > 3 else "UNRESOLVED",
    }

    # Deployment score diagnostics (descriptive, never 'real-data accuracy')
    diagnostics = {}
    for name, model in models.items():
        p_data = frozen[name]["cal"].predict_proba(
            model.scores(data_pool))
        p_mcval = frozen[name]["cal"].predict_proba(
            model.scores(val_df[FEATURES].to_numpy(float)))
        ks = stats.ks_2samp(p_data, p_mcval)
        diagnostics[name] = {
            "auc_mc_val": round(frozen[name]["auc_mc_val"], 4),
            "m_source": round(frozen[name]["m_source"], 4),
            "threshold": round(frozen[name]["thr"], 6),
            "score_ks_data_vs_mcval": {"stat": round(float(ks.statistic), 4),
                                       "p": float(ks.pvalue)},
            "frac_above_thr_data": round(float((p_data >= frozen[name]["thr"]).mean()), 4),
            "frac_above_thr_mcval": round(float((p_mcval >= frozen[name]["thr"]).mean()), 4),
        }

    out = {
        "experiment": "E11",
        "samples": {"mc_selected": int(len(mc)), "data_selected": int(len(data)),
                    "mc_sr": int(len(mc_sr)), "data_sr": int(len(data_sr)),
                    "mc_ss": int(len(mc_ss)), "data_ss": int(len(data_ss))},
        "claims_ledger": ledger,
        "deployment_diagnostics": diagnostics,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E11_cms_case_study.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    from qevc.utils.repro import file_sha256  # noqa: PLC0415

    manifest = RunManifest(
        experiment_id="E11",
        config={"E11": E11, "effective_lumi_pb": EFFECTIVE_LUMI_PB},
        seed=E11["train"]["seed"],
        dataset_hashes={p.name: file_sha256(p)
                        for p in sorted(CMS.glob("*.parquet"))},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E11 complete in {out['wall_seconds']} s -> {out_path}")
    print(json.dumps(ledger, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
