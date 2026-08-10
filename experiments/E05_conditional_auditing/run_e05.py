"""E05 — Information-set conditional auditor (spec §13, §28; H3, H4).

For every (environment, model) pair and the predeclared degradation claims
C_δ: M_T ≥ M_S − δ (D-014, unweighted event correctness at the frozen
threshold), the auditor resolves claims under explicit information sets:

- I0 (source only): certification is impossible without target evidence
  (unsupervised-accuracy impossibility) → UNRESOLVED by construction.
- I1 (+ unlabeled target): geometry alarm (E03 quantum-kernel MMD² above the
  weight-only noise floor) may VETO a SUPPORTED verdict — it can never create
  one (D-006). Structurally blind to weight-only nuisances (E03 finding).
- I2(n): sequential labeled draws (uniform with replacement → exact IID
  Bernoulli(M_T)) through an empirical-Bernstein confidence sequence at
  α = 0.05; fail-closed decision rule; n* = first resolution budget.

Simulation truth (M_T on the full archived environment scores) is used ONLY
to score the auditor's decisions — never given to the auditor.

Outputs: results/tables/E05_auditor.json.
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

from qevc.auditing.claims import Claim, Verdict, resolve_claim  # noqa: E402
from qevc.metrics.classifier import weighted_auc  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E05 = yaml.safe_load((REPO / "configs/experiments/E05.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
E03_RESULTS = json.loads((REPO / "results/tables/E03_geometry.json").read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS
SCORES_DIR = REPO / "results/raw/E02_scores"

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, parse_params  # noqa: E402

WEIGHT_ONLY = ("ttbar_scale", "diboson_scale", "bkg_scale")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def frozen_thresholds_and_source_acc(raw, raw_splits) -> dict[str, dict]:
    """Re-derive frozen thresholds + unweighted source accuracy M_S for the
    focus models (deterministic retrain, identical to E02's procedure)."""
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    sv_df = frames["source_val"]
    df_a = tier_a_frame(frames["train"], E01["tier_a"]["n_train"],
                        E01["tier_a"]["seed"])
    seed = E01["tuning"]["seed"]
    q_cols = E01["features"]["quantum"]
    out: dict[str, dict] = {}
    from qevc.pipeline.common import features_for  # noqa: PLC0415

    for key in E05["models"]:
        tier, name = key.split(":")
        params = parse_params(E01_RESULTS["tiers"][tier][name]["best_params"])
        train_df = df_a if tier == "A" else frames["train"]
        cols = features_for(name, q_cols, FEATURES_ALL)
        X = train_df[cols].to_numpy(float)
        y, w = train_df["labels"].to_numpy(), train_df["weights"].to_numpy()
        model = (qksvc_builder(params, seed) if name == "qksvc"
                 else build(name, params, seed))
        model.fit(X, y, sample_weight=class_balanced_weights(y, w))
        s_sv = model.scores(sv_df[cols].to_numpy(float))
        y_sv, w_sv = sv_df["labels"].to_numpy(), sv_df["weights"].to_numpy()
        cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
        p_sv = cal.predict_proba(s_sv)
        thr = ba_optimal_threshold(y_sv, p_sv, w_sv)
        m_s = float(np.mean((p_sv >= thr).astype(int) == y_sv))  # unweighted, D-014
        out[key] = {"thr": thr, "m_source": m_s}
        log(f"{key}: thr={thr:.5f}  M_S={m_s:.4f}")
    return out


def i1_alarm_envs() -> set[str]:
    """Envs whose quantum-kernel MMD² exceeds the weight-only noise floor."""
    envs_g = E03_RESULTS["environments"]
    kern = E05["i1_alarm"]["kernel"]
    desc = E05["i1_alarm"]["descriptor"]
    floor = max(v["kernels"][kern][desc] for e, v in envs_g.items()
                if any(e.startswith(p) for p in WEIGHT_ONLY))
    return {e for e, v in envs_g.items()
            if e != "nominal" and v["kernels"][kern][desc] > floor}


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    frozen = frozen_thresholds_and_source_acc(raw, raw_splits)
    labels_raw = raw["labels"].to_numpy().astype(int)
    alarms = i1_alarm_envs()
    log(f"I1 alarm envs ({len(alarms)}): {sorted(alarms)}")

    deltas = E05["claims"]["deltas"]
    alpha, n_max, n_seeds = E05["alpha"], E05["n_max"], E05["audit_seeds"]
    env_list = [("nominal", Environment())] + environments()

    results: dict = {}
    err_counts = {"false_cert": 0, "false_refute": 0,
                  "streams_claim_false": 0, "streams_claim_true": 0}
    for env_name, _env in env_list:
        npz = np.load(env_filename(env_name))
        row_id = npz["row_id"]
        y_env = labels_raw[row_id]
        alarm = env_name in alarms
        results[env_name] = {"i1_alarm": bool(alarm), "models": {}}
        for key in E05["models"]:
            p = npz[key]
            correct = ((p >= frozen[key]["thr"]).astype(int) == y_env).astype(float)
            m_t = float(correct.mean())
            m_s = frozen[key]["m_source"]
            model_entry: dict = {"m_target": round(m_t, 5), "m_source": round(m_s, 5),
                                 "claims": {}}
            for d in deltas:
                tau = m_s - d
                truth = m_t >= tau
                verdicts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                vetoed = 0
                n_stars = []
                for s in range(n_seeds):
                    # Stable stream seed (python hash() is per-process salted)
                    digest = hashlib.sha256(
                        f"{env_name}|{key}|{s}".encode()).digest()
                    rng = np.random.default_rng(
                        int.from_bytes(digest[:8], "little"))
                    x = correct[rng.integers(0, len(correct), size=n_max)]
                    cs = empirical_bernstein_cs(x, alpha=alpha)
                    res = resolve_claim(Claim("acc", tau), cs,
                                        heuristic_alarm=alarm)
                    verdicts[res.verdict.value] += 1
                    vetoed += res.vetoed
                    if res.n_star is not None:
                        n_stars.append(res.n_star)
                    if not truth:
                        err_counts["streams_claim_false"] += 1
                        if res.verdict is Verdict.SUPPORTED:
                            err_counts["false_cert"] += 1
                    else:
                        err_counts["streams_claim_true"] += 1
                        if res.verdict is Verdict.REFUTED:
                            err_counts["false_refute"] += 1
                model_entry["claims"][str(d)] = {
                    "tau": round(tau, 5), "truth": bool(truth),
                    "margin": round(m_t - tau, 5),
                    "verdicts": verdicts, "vetoed": vetoed,
                    "n_star_median": (int(np.median(n_stars)) if n_stars else None),
                    "n_star_iqr": ([int(np.percentile(n_stars, q)) for q in (25, 75)]
                                   if n_stars else None),
                }
            results[env_name]["models"][key] = model_entry
        log(f"{env_name}: audited")

    fc_rate = (err_counts["false_cert"] / err_counts["streams_claim_false"]
               if err_counts["streams_claim_false"] else None)
    fr_rate = (err_counts["false_refute"] / err_counts["streams_claim_true"]
               if err_counts["streams_claim_true"] else None)
    out = {
        "experiment": "E05",
        "estimand": "unweighted_event_correctness_at_frozen_threshold (D-014)",
        "information_sets": {
            "I0": "source only -> UNRESOLVED by construction (impossibility)",
            "I1": "unlabeled target -> geometry alarm can only veto SUPPORTED",
            "I2": f"sequential labels, EB-CS, alpha={alpha}, n_max={n_max}",
        },
        "frozen": {k: {kk: round(vv, 5) for kk, vv in v.items()}
                   for k, v in frozen.items()},
        "i1_alarm_envs": sorted(alarms),
        "error_rates": {
            "false_certification": (round(fc_rate, 5) if fc_rate is not None else None),
            "false_refutation": (round(fr_rate, 5) if fr_rate is not None else None),
            **err_counts,
            "alpha": alpha,
        },
        "environments": results,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E05_auditor.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E05", config={"E01": E01, "E05": E05}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E05 complete in {out['wall_seconds']} s -> {out_path}")
    log(f"false certification rate: {fc_rate}  (alpha={alpha})")
    log(f"false refutation rate: {fr_rate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
