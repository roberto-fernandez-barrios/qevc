"""E13 — Weighted anytime-valid certification (registry E13; D-019).

Part A: Monte Carlo validation battery per docs/weighted_certification_spec.md
§5 — time-uniform coverage, false certification/refutation at margins,
adversarial optional stopping, BA_w conservatism — on synthetic populations
(uniform / benchmark-derived / adversarial heavy-tail weights).

Part B: benchmark study on the seed-101 archives — weighted vs unweighted
verdicts and n* on IDENTICAL label draws over the 41 environments × models ×
frozen claim grid, plus weighted class-conditional (TPR_w/TNR_w) claims.
Every environment is audited with NOMINAL per-event weights (the oracle
cannot know theta_norm); the true-weight gap for weight-only nuisances is
E14's demonstration.

Campaign quarantine: this experiment never touches E12 rows.

Outputs: results/tables/E13_weighted_cs.json.
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
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.statistics.weighted import (  # noqa: E402
    effective_sample_size_ratio,
    resolve_ba_claim,
    resolve_weighted_claim,
    weighted_claim_stream,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E13 = yaml.safe_load((REPO / "configs/experiments/E13.yaml").read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, train_frozen_models  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stream_rng(*parts) -> np.random.Generator:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def stable_seed(*parts) -> int:
    """Stable across processes — python hash() is salted (E05 lesson)."""
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(digest[:4], "little")


# ---------------------------------------------------------------------------
# Part A — Monte Carlo battery
# ---------------------------------------------------------------------------

def make_population(profile: str, a_w_target: float, n: int, seed: int,
                    bench_weights: np.ndarray | None):
    """Finite population with prescribed weight profile and approximate
    weighted accuracy; the EXACT A_w of the realized population is measured
    and used as truth."""
    rng = np.random.default_rng(seed)
    if profile == "uniform":
        w = np.ones(n)
    elif profile == "benchmark":
        w = rng.choice(bench_weights, size=n)
    elif profile == "heavy":
        w = rng.choice([0.05, 5.0], size=n, p=[0.96, 0.04])
    else:
        raise ValueError(profile)
    # Correctness correlated with weight (high-weight events worse by 0.15),
    # solved so the weighted mean lands near the target.
    hi = w >= np.median(w)
    frac_hi_w = w[hi].sum() / w.sum()
    acc_hi_w = a_w_target - 0.15 * (1.0 - frac_hi_w)
    acc_lo_w = a_w_target + 0.15 * frac_hi_w
    p = np.where(hi, np.clip(acc_hi_w, 0.02, 0.98), np.clip(acc_lo_w, 0.02, 0.98))
    c = (rng.random(n) < p).astype(float)
    a_w = float((w * c).sum() / w.sum())
    return c, w, a_w


def part_a(bench_weights: np.ndarray) -> dict:
    mc = E13["monte_carlo"]
    alpha = E13["benchmark"]["alpha"]
    out: dict = {"margins": {}, "coverage": {}, "adversarial_stopping": {},
                 "ba_conservatism": {}}

    # (1) false cert / refutation / abstention at margins
    for profile in mc["profiles"]:
        for a_lvl in mc["a_w_levels"]:
            c_pop, w_pop, a_w = make_population(
                profile, a_lvl, mc["population_n"],
                seed=stable_seed("pop", profile, a_lvl), bench_weights=bench_weights)
            w_max = float(w_pop.max()) * 1.001
            for m in mc["margins"]:
                tau = float(np.clip(a_w + m, 0.0, 1.0))
                truth = a_w >= tau
                counts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                n_stars = []
                for r in range(mc["n_rep"]):
                    rng = stream_rng(mc["seed_salt"], profile, a_lvl, m, r)
                    idx = rng.integers(0, len(c_pop), size=mc["n_max"])
                    res = resolve_weighted_claim(c_pop[idx], w_pop[idx], tau,
                                                 w_max, alpha=alpha)
                    counts[res.verdict.value] += 1
                    if res.n_star is not None:
                        n_stars.append(res.n_star)
                key = f"{profile}|a{a_lvl}|m{m:+}"
                out["margins"][key] = {
                    "a_w_exact": round(a_w, 5), "tau": round(tau, 5),
                    "truth": bool(truth), "verdicts": counts,
                    "false_cert_rate": (counts["SUPPORTED"] / mc["n_rep"]
                                        if not truth else None),
                    "false_refute_rate": (counts["REFUTED"] / mc["n_rep"]
                                          if truth else None),
                    "n_star_median": (int(np.median(n_stars)) if n_stars else None),
                    "ess_ratio": round(effective_sample_size_ratio(w_pop), 4),
                }
            log(f"Part A margins: {profile} a={a_lvl} done")

    # (2) time-uniform miscoverage of E[Z(tau)] at fixed tau
    for profile in mc["profiles"]:
        for a_lvl in mc["coverage_a_w"]:
            c_pop, w_pop, a_w = make_population(
                profile, a_lvl, mc["population_n"],
                seed=stable_seed("cov", profile, a_lvl),
                bench_weights=bench_weights)
            w_max = float(w_pop.max()) * 1.001
            tau = float(np.clip(a_w, 0.0, 1.0))
            z_pop_mean = float(np.mean(
                weighted_claim_stream(c_pop, w_pop, tau, w_max)))
            viol = 0
            for r in range(mc["coverage_n_rep"]):
                rng = stream_rng(mc["seed_salt"], "cov", profile, a_lvl, r)
                idx = rng.integers(0, len(c_pop), size=mc["n_max"])
                z = weighted_claim_stream(c_pop[idx], w_pop[idx], tau, w_max)
                cs = empirical_bernstein_cs(z, alpha=alpha).running_intersection()
                if np.any(cs.lower > z_pop_mean) or np.any(cs.upper < z_pop_mean):
                    viol += 1
            out["coverage"][f"{profile}|a{a_lvl}"] = {
                "miscoverage": viol / mc["coverage_n_rep"], "alpha": alpha,
                "pass": bool(viol / mc["coverage_n_rep"]
                             <= alpha + 3 * np.sqrt(alpha * (1 - alpha)
                                                    / mc["coverage_n_rep"]))}
        log(f"Part A coverage: {profile} done")

    # (3) adversarial stopping: naive fixed-n Wald vs CS on a false claim
    c_pop, w_pop, a_w = make_population("benchmark", 0.72, mc["population_n"],
                                        seed=1234, bench_weights=bench_weights)
    w_max = float(w_pop.max()) * 1.001
    tau = min(a_w + 0.01, 1.0)
    naive = cs_cert = 0
    z_crit = 1.6449
    for r in range(mc["n_rep"]):
        rng = stream_rng(mc["seed_salt"], "adv", r)
        idx = rng.integers(0, len(c_pop), size=mc["n_max"])
        z = weighted_claim_stream(c_pop[idx], w_pop[idx], tau, w_max)
        t = np.arange(1, len(z) + 1)
        mean = np.cumsum(z) / t
        var = np.cumsum(z * z) / t - mean**2
        se = np.sqrt(np.maximum(var, 1e-12) / t)
        if np.any((mean - z_crit * se >= tau) & (t >= 30)):
            naive += 1
        cs = empirical_bernstein_cs(z, alpha=alpha).running_intersection()
        if np.any(cs.lower >= tau):
            cs_cert += 1
    out["adversarial_stopping"] = {
        "claim_margin": -0.01, "naive_wald_false_cert": naive / mc["n_rep"],
        "cs_false_cert": cs_cert / mc["n_rep"], "alpha": alpha}

    # (4) BA_w conservatism: false-cert at small negative margin + verdict
    # rate on a TRUE claim (measures the conservatism cost)
    rng0 = np.random.default_rng(77)
    n = mc["population_n"]
    y = (rng0.random(n) < 0.3).astype(int)
    w = rng0.choice(bench_weights, size=n)
    c = (rng0.random(n) < np.where(y == 1, 0.75, 0.85)).astype(float)
    tpr = (w * c * (y == 1)).sum() / (w * (y == 1)).sum()
    tnr = (w * c * (y == 0)).sum() / (w * (y == 0)).sum()
    ba_w = float((tpr + tnr) / 2)
    w_max = float(w.max()) * 1.001
    res_counts = {}
    for m, label in ((+0.02, "false_claim"), (-0.05, "true_claim")):
        tau = float(np.clip(ba_w + m, 0.0, 1.0))
        counts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
        for r in range(mc["n_rep"] // 2):
            rng = stream_rng(mc["seed_salt"], "ba", m, r)
            idx = rng.integers(0, n, size=mc["n_max"])
            res = resolve_ba_claim(c[idx], y[idx], w[idx], tau, w_max, alpha=alpha)
            counts[res.verdict.value] += 1
        res_counts[label] = {"tau": round(tau, 5), "verdicts": counts}
    out["ba_conservatism"] = {"ba_w_exact": round(ba_w, 5), **res_counts}
    log("Part A complete")
    return out


# ---------------------------------------------------------------------------
# Part B — benchmark study (seed-101 archives)
# ---------------------------------------------------------------------------

def part_b() -> dict:
    bm = E13["benchmark"]
    alpha, n_max, n_seeds = bm["alpha"], bm["n_max"], bm["audit_seeds"]
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    labels_raw = raw["labels"].to_numpy().astype(int)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    models = train_frozen_models(frames)

    # w_max: per-process weight constancy check + predeclared bound
    sub_w = raw["weights"].to_numpy()
    sub_dl = raw["detailed_labels"].to_numpy()
    proc_w = {}
    for proc in np.unique(sub_dl):
        vals = sub_w[sub_dl == proc]
        proc_w[str(proc)] = {"min": float(vals.min()), "max": float(vals.max()),
                             "constant": bool(np.allclose(vals.min(), vals.max()))}
    w_base = float(sub_w.max())
    w_max = w_base * E13["w_max"]["kappa_norm"]
    log(f"w_max = {w_base:.4f} * {E13['w_max']['kappa_norm']} = {w_max:.4f}")

    # frozen source references (weighted + unweighted, on source_val)
    sv = frames["source_val"]
    y_sv, w_sv = sv["labels"].to_numpy(), sv["weights"].to_numpy()
    refs: dict[str, dict] = {}
    for key in bm["models"]:
        model, cal, thr, cols = models[key]
        p_sv = cal.predict_proba(model.scores(sv[cols].to_numpy(float)))
        pred = (p_sv >= thr).astype(int)
        corr = (pred == y_sv).astype(float)
        m_s_unw = float(corr.mean())
        m_s_w = float((w_sv * corr).sum() / w_sv.sum())
        tpr_w = float((w_sv * corr * (y_sv == 1)).sum() / (w_sv * (y_sv == 1)).sum())
        tnr_w = float((w_sv * corr * (y_sv == 0)).sum() / (w_sv * (y_sv == 0)).sum())
        refs[key] = {"thr": thr, "m_s_unw": m_s_unw, "m_s_w": m_s_w,
                     "tpr_w": tpr_w, "tnr_w": tnr_w}
        log(f"{key}: M_S unw={m_s_unw:.4f} w={m_s_w:.4f} "
            f"TPRw={tpr_w:.4f} TNRw={tnr_w:.4f}")

    test_ids = raw_splits["nominal_test"]
    env_list = [("nominal", Environment())] + environments()
    err = {"w": {"false_cert": 0, "false_refute": 0, "n_false": 0, "n_true": 0},
           "unw": {"false_cert": 0, "false_refute": 0, "n_false": 0, "n_true": 0},
           "cc": {"false_cert": 0, "false_refute": 0, "n_false": 0, "n_true": 0}}
    flips = {"verdict_pairs": {}, "n_star_ratios": []}
    per_env: dict = {}

    w0_all = raw["weights"].to_numpy()
    for env_name, env in env_list:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz")
        rid = te["row_id"].to_numpy()
        if not np.array_equal(npz["row_id"], rid):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        # NOMINAL weights of the surviving rows (audit C1 fix, 2026-08-11):
        # build_environment_dataset applies norm scalings to te["weights"],
        # so the environment frame's weights are w(theta), NOT the nominal
        # weights the oracle reveals. Index the raw subset instead (as E14
        # does). First-run table preserved as *_v1_theta_weights.json.
        w_env = w0_all[rid]
        y_env = labels_raw[rid]
        ess = effective_sample_size_ratio(w_env)
        per_env[env_name] = {"ess_ratio": round(ess, 4), "models": {}}
        for key in bm["models"]:
            p = npz[key]
            corr = ((p >= refs[key]["thr"]).astype(int) == y_env).astype(float)
            m_t_unw = float(corr.mean())
            m_t_w = float((w_env * corr).sum() / w_env.sum())
            entry: dict = {"m_t_unw": round(m_t_unw, 5), "m_t_w": round(m_t_w, 5),
                           "claims": {}}
            for d in bm["deltas"]:
                tau_w = float(np.clip(refs[key]["m_s_w"] - d, 0.0, 1.0))
                tau_u = float(np.clip(refs[key]["m_s_unw"] - d, 0.0, 1.0))
                truth_w = m_t_w >= tau_w
                truth_u = m_t_unw >= tau_u
                vw = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                vu = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                ns_w, ns_u = [], []
                for s in range(n_seeds):
                    rng = stream_rng(bm["seed_salt"], env_name, key, s)
                    idx = rng.integers(0, len(corr), size=n_max)
                    res_w = resolve_weighted_claim(corr[idx], w_env[idx],
                                                   tau_w, w_max, alpha=alpha)
                    cs_u = empirical_bernstein_cs(corr[idx], alpha=alpha)
                    res_u = resolve_claim(Claim("acc", tau_u), cs_u)
                    vw[res_w.verdict.value] += 1
                    vu[res_u.verdict.value] += 1
                    if res_w.n_star is not None:
                        ns_w.append(res_w.n_star)
                    if res_u.n_star is not None:
                        ns_u.append(res_u.n_star)
                    pair = f"{res_u.verdict.value}->{res_w.verdict.value}"
                    flips["verdict_pairs"][pair] = flips["verdict_pairs"].get(pair, 0) + 1
                    if res_w.n_star is not None and res_u.n_star is not None:
                        flips["n_star_ratios"].append(res_w.n_star / res_u.n_star)
                    for tag, res, truth in (("w", res_w, truth_w),
                                            ("unw", res_u, truth_u)):
                        if truth:
                            err[tag]["n_true"] += 1
                            if res.verdict is Verdict.REFUTED:
                                err[tag]["false_refute"] += 1
                        else:
                            err[tag]["n_false"] += 1
                            if res.verdict is Verdict.SUPPORTED:
                                err[tag]["false_cert"] += 1
                entry["claims"][str(d)] = {
                    "tau_w": round(tau_w, 5), "truth_w": bool(truth_w),
                    "margin_w": round(m_t_w - tau_w, 5),
                    "truth_unw": bool(truth_u),
                    "margin_unw": round(m_t_unw - tau_u, 5),
                    "verdicts_w": vw, "verdicts_unw": vu,
                    "n_star_w_median": (int(np.median(ns_w)) if ns_w else None),
                    "n_star_unw_median": (int(np.median(ns_u)) if ns_u else None),
                }
            # class-conditional weighted claims (TPR_w / TNR_w)
            for d in bm["class_conditional_deltas"]:
                for comp, ref_key in (("tpr_w", "tpr_w"), ("tnr_w", "tnr_w")):
                    mask = (y_env == 1) if comp == "tpr_w" else (y_env == 0)
                    u_env = w_env * mask
                    m_t_c = float((u_env * corr).sum() / u_env.sum())
                    tau_c = float(np.clip(refs[key][ref_key] - d, 0.0, 1.0))
                    truth_c = m_t_c >= tau_c
                    vc = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                    ns_c = []
                    for s in range(n_seeds):
                        rng = stream_rng(bm["seed_salt"], "cc", env_name, key,
                                         comp, d, s)
                        idx = rng.integers(0, len(corr), size=n_max)
                        res = resolve_weighted_claim(corr[idx], u_env[idx],
                                                     tau_c, w_max, alpha=alpha)
                        vc[res.verdict.value] += 1
                        if res.n_star is not None:
                            ns_c.append(res.n_star)
                        if truth_c:
                            err["cc"]["n_true"] += 1
                            if res.verdict is Verdict.REFUTED:
                                err["cc"]["false_refute"] += 1
                        else:
                            err["cc"]["n_false"] += 1
                            if res.verdict is Verdict.SUPPORTED:
                                err["cc"]["false_cert"] += 1
                    entry["claims"][f"{comp}|{d}"] = {
                        "tau": round(tau_c, 5), "truth": bool(truth_c),
                        "margin": round(m_t_c - tau_c, 5), "verdicts": vc,
                        "n_star_median": (int(np.median(ns_c)) if ns_c else None)}
            per_env[env_name]["models"][key] = entry
        log(f"Part B {env_name}: done")

    rates = {}
    for tag, e in err.items():
        rates[tag] = {
            "false_certification": (e["false_cert"] / e["n_false"]
                                    if e["n_false"] else None),
            "false_refutation": (e["false_refute"] / e["n_true"]
                                 if e["n_true"] else None), **e}
    ratios = np.array(flips["n_star_ratios"])
    return {"w_max": {"base": w_base, "kappa_norm": E13["w_max"]["kappa_norm"],
                      "value": w_max, "per_process_weights": proc_w},
            "frozen_refs": {k: {kk: round(vv, 5) for kk, vv in v.items()}
                            for k, v in refs.items()},
            "error_rates": rates,
            "verdict_pairs_unw_to_w": flips["verdict_pairs"],
            "n_star_ratio_w_over_unw": {
                "median": (round(float(np.median(ratios)), 3) if len(ratios) else None),
                "iqr": ([round(float(np.percentile(ratios, q)), 3)
                         for q in (25, 75)] if len(ratios) else None),
                "n_pairs": int(len(ratios))},
            "environments": per_env}


def main() -> int:
    t0 = time.time()
    # benchmark weight profile for Part A: the actual per-process weight
    # constants of the seed-101 subset (D-010-rescaled)
    raw = load_raw_subset(REPO, E01["subset"])
    bench_weights = raw.groupby("detailed_labels", observed=True)["weights"].mean().to_numpy()
    log(f"benchmark weight constants: {np.round(bench_weights, 4)}")

    a = part_a(bench_weights)
    b = part_b()

    # falsifier evaluation (registry E13)
    cov_pass = all(v["pass"] for v in a["coverage"].values())
    fc_cells = [v["false_cert_rate"] for v in a["margins"].values()
                if v["false_cert_rate"] is not None]
    alpha = E13["benchmark"]["alpha"]
    n_rep = E13["monte_carlo"]["n_rep"]
    slack = alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep)
    fc_pass = all(r <= slack for r in fc_cells)
    out = {
        "experiment": "E13",
        "spec": "docs/weighted_certification_spec.md (D-019)",
        "part_a_monte_carlo": a,
        "part_b_benchmark": b,
        "falsifier": {
            "coverage_all_pass": bool(cov_pass),
            "false_cert_all_within_slack": bool(fc_pass),
            "slack_alpha_plus_3sigma": round(slack, 5),
            "worst_false_cert_cell": (round(max(fc_cells), 5) if fc_cells else None),
            "implementation_valid": bool(cov_pass and fc_pass),
        },
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E13_weighted_cs.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E13", config={"E01": E01, "E13": E13}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E13 complete in {out['wall_seconds']} s -> {out_path}")
    log(f"falsifier: {json.dumps(out['falsifier'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
