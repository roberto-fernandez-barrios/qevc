"""Sharp-nominal-bound sensitivity of the weighted certification (E13 / E19).

DERIVED / NO NEW RANDOMNESS.  The registered analyses use the predeclared bound

    w_max = (max nominal per-event weight of the frozen population) x 2.05,

where the factor kappa_norm = 2.05 covers compound nuisance weight scalings.
After the D-032 estimand correction, every executed I2 weighted claim in E13
Part B and E19 audits a NOMINAL-weight estimand: the revealed increment is
u_i = w_i^(0) (or w_i^(0) 1[y_i = c]), which never exceeds the nominal maximum.
The factor 2.05 is therefore not required for the validity of those executed
claims; it is deliberate conservatism carried over from the theta-weight
estimand.  This script quantifies its stopping-time price WITHOUT touching the
registered primary analysis:

  1. replay E13 Part B with kappa_norm = 2.05 through the frozen runner and
     require an exact match with the archived ``E13_weighted_cs.json``
     (falsifier F6: no sensitivity is computed unless the replay is exact);
  2. replay E13 Part B with kappa_norm = 1.0 on EXACTLY the same populations,
     audit draws, order, labels, thresholds, alpha and confidence-sequence
     implementation (the streams are seeded by fixed salts and do not depend
     on w_max);
  3. do the same for the E19 weighted arm using the frozen E19 reconstruction
     and the archived verdict counts;
  4. report the changes in n*, resolution fractions, verdict compositions,
     the weighted/unweighted stopping-time ratio and the error rates.

The primary registered results are not modified.  Outputs:
  results/tables/E13_wmax_nominal_bound_sensitivity.json
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "E12_confirmatory"))

from qevc.auditing.claims import Verdict  # noqa: E402
from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.pipeline.common import build_environment_dataset  # noqa: E402
from qevc.statistics.weighted import resolve_weighted_claim  # noqa: E402
from qevc.systematics.fair_universe import Environment  # noqa: E402

E13_RUNNER = ROOT / "experiments" / "E13_weighted_certification" / "run_e13.py"
E19_RUNNER = ROOT / "experiments" / "E19_fresh_world_validity" / "run_e19.py"
E13_ARCHIVE = ROOT / "results" / "tables" / "E13_weighted_cs.json"
E19_ARCHIVE = ROOT / "results" / "tables" / "E19_fresh_world_validity.json"
E13_CONFIG = ROOT / "configs" / "experiments" / "E13.yaml"
E19_CONFIG = ROOT / "configs" / "experiments" / "E19.yaml"
OUTPUT = ROOT / "results" / "tables" / "E13_wmax_nominal_bound_sensitivity.json"
HISTORICAL_KAPPA = 2.05
SHARP_KAPPA = 1.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def normalize(value):
    """Round-trip through JSON so tuples/ints compare like the archive."""
    return json.loads(json.dumps(value))


def summarize(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return {"n": 0}
    return {
        "n": int(array.size),
        "median": round(float(np.median(array)), 4),
        "q25": round(float(np.percentile(array, 25)), 4),
        "q75": round(float(np.percentile(array, 75)), 4),
        "min": round(float(array.min()), 4),
        "max": round(float(array.max()), 4),
    }


# ---------------------------------------------------------------------------
# E13 Part B
# ---------------------------------------------------------------------------

def e13_part_b_comparison(hist: dict, sharp: dict) -> dict:
    """Compare two E13 Part-B tables claim by claim."""
    n_star_w_hist, n_star_w_sharp = [], []
    ratios_hist, ratios_sharp = [], []
    resolved_hist = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
    resolved_sharp = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
    cc_hist = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
    cc_sharp = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
    per_claim_ratio = []
    for env_name, env in hist["environments"].items():
        for model, entry in env["models"].items():
            sharp_entry = sharp["environments"][env_name]["models"][model]
            for claim, cell in entry["claims"].items():
                sharp_cell = sharp_entry["claims"][claim]
                if "verdicts_w" in cell:
                    for verdict, count in cell["verdicts_w"].items():
                        resolved_hist[verdict] += count
                    for verdict, count in sharp_cell["verdicts_w"].items():
                        resolved_sharp[verdict] += count
                    if cell["n_star_w_median"] is not None:
                        n_star_w_hist.append(cell["n_star_w_median"])
                    if sharp_cell["n_star_w_median"] is not None:
                        n_star_w_sharp.append(sharp_cell["n_star_w_median"])
                    if cell["n_star_w_median"] and sharp_cell["n_star_w_median"]:
                        per_claim_ratio.append(sharp_cell["n_star_w_median"] / cell["n_star_w_median"])
                    if cell["n_star_w_median"] and cell["n_star_unw_median"]:
                        ratios_hist.append(cell["n_star_w_median"] / cell["n_star_unw_median"])
                    if sharp_cell["n_star_w_median"] and sharp_cell["n_star_unw_median"]:
                        ratios_sharp.append(sharp_cell["n_star_w_median"] / sharp_cell["n_star_unw_median"])
                else:
                    for verdict, count in cell["verdicts"].items():
                        cc_hist[verdict] += count
                    for verdict, count in sharp_cell["verdicts"].items():
                        cc_sharp[verdict] += count
    total_w = sum(resolved_hist.values())
    total_cc = sum(cc_hist.values())
    # cell-level transitions: where does resolution move when the bound is sharpened?
    per_claim = []
    cells_more_resolved = cells_less_resolved = cells_same = 0
    for env_name, env in hist["environments"].items():
        for model, entry in env["models"].items():
            sharp_entry = sharp["environments"][env_name]["models"][model]
            for claim, cell in entry["claims"].items():
                if "verdicts_w" not in cell:
                    continue
                sharp_cell = sharp_entry["claims"][claim]
                res_h = cell["verdicts_w"]["SUPPORTED"] + cell["verdicts_w"]["REFUTED"]
                res_s = sharp_cell["verdicts_w"]["SUPPORTED"] + sharp_cell["verdicts_w"]["REFUTED"]
                cells_more_resolved += res_s > res_h
                cells_less_resolved += res_s < res_h
                cells_same += res_s == res_h
                per_claim.append({
                    "environment": env_name,
                    "model": model,
                    "delta": claim,
                    "margin_w": cell["margin_w"],
                    "truth_w": cell["truth_w"],
                    "verdicts_w_historical": cell["verdicts_w"],
                    "verdicts_w_sharp": sharp_cell["verdicts_w"],
                    "n_star_w_median_historical": cell["n_star_w_median"],
                    "n_star_w_median_sharp": sharp_cell["n_star_w_median"],
                    "n_star_unw_median": cell["n_star_unw_median"],
                })
    small = [row for row in per_claim if abs(row["margin_w"]) < 0.01]
    large = [row for row in per_claim if abs(row["margin_w"]) >= 0.04]

    def resolved_streams(rows, key):
        return int(sum(r[key]["SUPPORTED"] + r[key]["REFUTED"] for r in rows))

    return {
        "per_claim_cells": per_claim,
        "cell_transitions": {
            "cells": len(per_claim),
            "more_resolved_under_sharp_bound": cells_more_resolved,
            "less_resolved_under_sharp_bound": cells_less_resolved,
            "unchanged_resolution_count": cells_same,
            "near_margin_cells_abs_margin_below_0_01": {
                "cells": len(small),
                "resolved_streams_historical": resolved_streams(small, "verdicts_w_historical"),
                "resolved_streams_sharp": resolved_streams(small, "verdicts_w_sharp"),
            },
            "far_margin_cells_abs_margin_at_least_0_04": {
                "cells": len(large),
                "resolved_streams_historical": resolved_streams(large, "verdicts_w_historical"),
                "resolved_streams_sharp": resolved_streams(large, "verdicts_w_sharp"),
            },
        },
        "weighted_accuracy_claims": {
            "stream_verdicts_historical": resolved_hist,
            "stream_verdicts_sharp": resolved_sharp,
            "fraction_resolved_historical": round((total_w - resolved_hist["UNRESOLVED"]) / total_w, 5),
            "fraction_resolved_sharp": round((total_w - resolved_sharp["UNRESOLVED"]) / total_w, 5),
            "cells_with_median_n_star_historical": len(n_star_w_hist),
            "cells_with_median_n_star_sharp": len(n_star_w_sharp),
            "median_n_star_w_historical": summarize(n_star_w_hist),
            "median_n_star_w_sharp": summarize(n_star_w_sharp),
            "per_claim_n_star_ratio_sharp_over_historical": summarize(per_claim_ratio),
        },
        "class_conditional_claims": {
            "stream_verdicts_historical": cc_hist,
            "stream_verdicts_sharp": cc_sharp,
            "fraction_resolved_historical": round((total_cc - cc_hist["UNRESOLVED"]) / total_cc, 5),
            "fraction_resolved_sharp": round((total_cc - cc_sharp["UNRESOLVED"]) / total_cc, 5),
        },
        "n_star_ratio_w_over_unw": {
            "historical_archived": hist["n_star_ratio_w_over_unw"],
            "historical_recomputed_from_cell_medians": summarize(ratios_hist),
            "sharp_archived_style": sharp["n_star_ratio_w_over_unw"],
            "sharp_recomputed_from_cell_medians": summarize(ratios_sharp),
        },
        "error_rates": {
            "historical": hist["error_rates"],
            "sharp": sharp["error_rates"],
        },
        "verdict_pairs_unw_to_w": {
            "historical": hist["verdict_pairs_unw_to_w"],
            "sharp": sharp["verdict_pairs_unw_to_w"],
        },
    }


def run_e13(kappa: float, run_e13_module) -> dict:
    run_e13_module.E13["w_max"]["kappa_norm"] = kappa
    table = run_e13_module.part_b()
    return normalize(table)


# ---------------------------------------------------------------------------
# E19 weighted arm (exact re-implementation of the frozen loop, no output write)
# ---------------------------------------------------------------------------

def run_e19_weighted(kappa: float, ctx: dict) -> dict:
    """Replay the E19 weighted arm for one kappa on the frozen streams."""
    run_e19 = ctx["module"]
    E19 = run_e19.E19
    ALPHA = run_e19.ALPHA
    w_max = ctx["base_wmax"] * float(kappa)
    if float(np.max(ctx["w0_all"])) > w_max:
        raise RuntimeError("w_max violated on nominal weights")
    deltas = run_e19.FROZEN["claims"]["deltas"]
    n_max = E19["auditor"]["n_max"]
    n_seeds = E19["auditor"]["audit_seeds"]
    fc = fr = n_false = n_true = 0
    n_stars = []
    per_env = {}
    for env_name, env in ctx["envs"]:
        te = build_environment_dataset(ctx["raw"], env, row_ids=ctx["test_ids"])
        npz = np.load(run_e19.SCORES_DIR / run_e19.npz_name(env_name))
        rid = te["row_id"].to_numpy()
        if not np.array_equal(npz["row_id"], rid):
            raise RuntimeError(f"row_id mismatch in {env_name}")
        y = ctx["labels_raw"][rid]
        w = ctx["w0_all"][rid]
        per_env[env_name] = {}
        for key in E19["auditor"]["models"]:
            _m, _c, thr, _cols, _ms = ctx["models"][key]
            p = npz[key]
            correct = ((p >= thr).astype(int) == y).astype(float)
            m_t_w = float(np.sum(w * correct) / np.sum(w))
            cell = {}
            for d in deltas:
                tau_w = ctx["refs"][key]["m_s_w"] - d
                truth_w = m_t_w >= tau_w
                v_w = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                for s in range(n_seeds):
                    rng = run_e19.stream_rng(E19["auditor"]["seed_salt"], env_name, key, s)
                    ix = rng.integers(0, len(correct), size=n_max)
                    r_w = resolve_weighted_claim(
                        correct[ix], w[ix], min(max(tau_w, 0), 1), w_max, alpha=ALPHA,
                        heuristic_alarm=False,
                    )
                    v_w[r_w.verdict.value] += 1
                    if r_w.n_star is not None:
                        n_stars.append(int(r_w.n_star))
                    if not truth_w:
                        n_false += 1
                        if r_w.verdict is Verdict.SUPPORTED:
                            fc += 1
                    else:
                        n_true += 1
                        if r_w.verdict is Verdict.REFUTED:
                            fr += 1
                cell[str(d)] = {"truth_w": bool(truth_w), "verdicts_w": v_w}
            per_env[env_name][key] = cell
        log(f"E19 weighted arm kappa={kappa}: audited {env_name}")
    total = n_false + n_true
    return {
        "w_max": round(w_max, 5),
        "false_cert_counts": [fc, n_false],
        "false_refutation_counts": [fr, n_true],
        "n_streams": total,
        "n_stars": n_stars,
        "per_env": per_env,
    }


def prepare_e19_context() -> dict:
    run_e19 = load_module("frozen_e19_runner", E19_RUNNER)
    run_e12 = run_e19.run_e12
    loader = FairUniverseLoader(
        ROOT / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        ROOT / "data/interim/fair_universe",
    )
    raw, raw_splits = run_e19.reconstruct_world(loader)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)] for r, ids in raw_splits.items()}
    labels_raw = raw["labels"].to_numpy().astype(int)
    test_ids = raw_splits["nominal_test"]
    models, _ = run_e12.train_frozen(frames)
    cert = run_e19.certify_archives(raw, test_ids, labels_raw, models)
    sv = frames["source_val"]
    y_sv, w_sv = sv["labels"].to_numpy(), sv["weights"].to_numpy()
    refs = {}
    for key, (model, cal, thr, cols, m_s_unw) in models.items():
        p_sv = cal.predict_proba(model.scores(sv[cols].to_numpy(float)))
        c_sv = ((p_sv >= thr).astype(int) == y_sv).astype(float)
        refs[key] = {"m_s_unw": m_s_unw, "m_s_w": float(np.sum(w_sv * c_sv) / np.sum(w_sv))}
    return {
        "module": run_e19,
        "raw": raw,
        "labels_raw": labels_raw,
        "test_ids": test_ids,
        "models": models,
        "refs": refs,
        "base_wmax": float(np.max(d0["weights"].to_numpy())),
        "w0_all": raw["weights"].to_numpy(),
        "envs": [("nominal", Environment())] + run_e12.environments(),
        "archive_certification": cert,
    }


def main() -> int:
    start = time.time()
    protected = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in (E13_ARCHIVE, E19_ARCHIVE, E13_CONFIG, E19_CONFIG, E13_RUNNER, E19_RUNNER)
    }
    e13_archive = json.loads(E13_ARCHIVE.read_text(encoding="utf-8"))
    e19_archive = json.loads(E19_ARCHIVE.read_text(encoding="utf-8"))
    archived_b = normalize(e13_archive["part_b_benchmark"])

    # --- mathematical necessity audit ------------------------------------
    necessity = {
        "estimand": "nominal-weight ratio R = E[u c]/E[u] with u = w^(0) or w^(0) 1[y=c] (D-032)",
        "bound_required_for_validity": "any scalar w_max >= max_i u_i fixed before the audit order",
        "max_u_never_exceeds": "max_i w_i^(0) (the nominal maximum) for every executed E13 Part-B and E19 claim",
        "kappa_2_05_required_for_executed_nominal_claims": False,
        "kappa_2_05_role": (
            "deliberate conservatism covering compound nuisance weight scalings of the "
            "theta-weight estimand (spec 3.4); it does not affect validity of nominal-weight "
            "claims and costs only stopping time"
        ),
    }

    # --- E13 Part B: exact historical replay, then sharp bound ---------------
    run_e13_module = load_module("frozen_e13_runner", E13_RUNNER)
    assert float(run_e13_module.E13["w_max"]["kappa_norm"]) == HISTORICAL_KAPPA
    log("E13 Part B: historical replay (kappa 2.05)")
    hist_b = run_e13(HISTORICAL_KAPPA, run_e13_module)
    e13_exact = hist_b == archived_b
    mismatch_detail = None
    if not e13_exact:
        for field in archived_b:
            if hist_b.get(field) != archived_b[field]:
                mismatch_detail = field
                break
        log(f"E13 historical replay MISMATCH at field {mismatch_detail}")
    else:
        log("E13 historical replay reproduces the archived Part-B table exactly")
    e13_result = {
        "historical_replay_exact": e13_exact,
        "first_mismatching_field": mismatch_detail,
        "w_max_historical": archived_b["w_max"],
    }
    if e13_exact:
        log("E13 Part B: sharp nominal bound (kappa 1.0) on identical streams")
        sharp_b = run_e13(SHARP_KAPPA, run_e13_module)
        e13_result["w_max_sharp"] = sharp_b["w_max"]
        e13_result["comparison"] = e13_part_b_comparison(hist_b, sharp_b)
        e13_result["frozen_refs_identical"] = sharp_b["frozen_refs"] == hist_b["frozen_refs"]

    # --- E19 weighted arm ---------------------------------------------------
    e19_result = {"attempted": True}
    try:
        ctx = prepare_e19_context()
        e19_result["archive_certification"] = ctx["archive_certification"]
        hist19 = run_e19_weighted(HISTORICAL_KAPPA, ctx)
        archived_counts = e19_archive["error_rates"]["weighted"]["counts"]
        archived_fr = e19_archive["error_rates"]["weighted"]["false_refutation"]
        exact_counts = hist19["false_cert_counts"] == archived_counts
        exact_cells = True
        for env_name, env in e19_archive["environments"].items():
            for key, cell in env["models"].items():
                for d, claim in cell["claims"].items():
                    if hist19["per_env"][env_name][key][d]["verdicts_w"] != claim["verdicts_w"]:
                        exact_cells = False
        e19_exact = (
            exact_counts and exact_cells
            and round(hist19["w_max"], 5) == e19_archive["w_max"]["w_max"]
            and round(hist19["false_refutation_counts"][0] / hist19["false_refutation_counts"][1], 5) == archived_fr
        )
        e19_result.update({
            "historical_replay_exact": e19_exact,
            "w_max_historical": hist19["w_max"],
            "historical_false_cert_counts": hist19["false_cert_counts"],
        })
        if e19_exact:
            log("E19 weighted arm: historical replay reproduces the archived verdict counts exactly")
            sharp19 = run_e19_weighted(SHARP_KAPPA, ctx)
            def composition(res):
                comp = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                for env in res["per_env"].values():
                    for cell in env.values():
                        for claim in cell.values():
                            for verdict, count in claim["verdicts_w"].items():
                                comp[verdict] += count
                return comp
            comp_h, comp_s = composition(hist19), composition(sharp19)
            total = sum(comp_h.values())
            e19_result.update({
                "w_max_sharp": sharp19["w_max"],
                "sharp_false_cert_counts": sharp19["false_cert_counts"],
                "historical_false_refutation_counts": hist19["false_refutation_counts"],
                "sharp_false_refutation_counts": sharp19["false_refutation_counts"],
                "stream_verdicts_historical": comp_h,
                "stream_verdicts_sharp": comp_s,
                "fraction_resolved_historical": round((total - comp_h["UNRESOLVED"]) / total, 5),
                "fraction_resolved_sharp": round((total - comp_s["UNRESOLVED"]) / total, 5),
                "n_star_historical": summarize(hist19["n_stars"]),
                "n_star_sharp": summarize(sharp19["n_stars"]),
            })
        else:
            log("E19 weighted arm: historical replay did NOT reproduce the archive; no sensitivity computed")
    except Exception as exc:  # noqa: BLE001 - reported, never hidden
        e19_result["error"] = f"{type(exc).__name__}: {exc}"
        log(f"E19 arm not reconstructed: {e19_result['error']}")

    protected_after = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in (E13_ARCHIVE, E19_ARCHIVE, E13_CONFIG, E19_CONFIG, E13_RUNNER, E19_RUNNER)
    }
    if protected != protected_after:
        raise RuntimeError("a protected artifact changed during the derived analysis")

    output = {
        "analysis": "Sharp-nominal-bound sensitivity of the weighted anytime-valid certification",
        "status": "DERIVED / NO NEW RANDOMNESS / POST-HOC SENSITIVITY (the registered kappa_norm = 2.05 analysis remains primary)",
        "unit_of_analysis": "claim cell and paired audit stream on the frozen populations; streams are identical between the historical and sharp bounds by construction",
        "method": (
            "replay the frozen E13 Part-B runner and the frozen E19 weighted-arm loop with the "
            "historical kappa_norm = 2.05, require exact reproduction of the archived tables, then "
            "repeat with kappa_norm = 1.0 (w_max = max nominal weight) on the same salts, draws, "
            "order, labels, thresholds, alpha and confidence-sequence implementation"
        ),
        "dependencies": [
            "experiments/E13_weighted_certification/run_e13.py",
            "experiments/E19_fresh_world_validity/run_e19.py",
            "results/tables/E13_weighted_cs.json",
            "results/tables/E19_fresh_world_validity.json",
            "results/raw/E02_scores, results/raw/E12_scores (archived deployment scores)",
        ],
        "limitations": [
            "post-hoc sensitivity; the registered 2.05 analysis is unchanged and remains primary",
            "the sharp bound is the nominal maximum of the frozen population, still a scalar fixed before the audit order",
            "stream-level counts are correlated across the delta grid and models",
        ],
        "provenance": {
            "protected_sha256": protected,
            "protected_unchanged_after_analysis": protected == protected_after,
            "no_new_randomness": True,
            "no_new_seeds_samples_models_or_thresholds": True,
            "script_sha256": sha256(Path(__file__).resolve()),
        },
        "mathematical_necessity_audit": necessity,
        "kappa": {"historical": HISTORICAL_KAPPA, "sharp": SHARP_KAPPA},
        "E13_part_b": e13_result,
        "E19_weighted_arm": e19_result,
        "wall_seconds": round(time.time() - start, 1),
    }
    OUTPUT.write_text(json.dumps(output, indent=1) + "\n", encoding="utf-8")
    log(f"wrote {OUTPUT.relative_to(ROOT)} ({output['wall_seconds']:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
