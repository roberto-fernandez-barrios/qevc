"""E14 — Information set I3 (registry E14; D-024; spec §4b).

Demonstrates, formally and experimentally, the identifiability boundary:
weight-only (normalization) nuisances are invisible to I0/I1/I2-with-
nominal-weights (proposition, spec §4b) but become resolvable when the
information set contains rate/control-region evidence (I3):

  A. Rate claims |s_p - 1| <= x: Monte-Carlo-validated profile-likelihood
     CIs from two control regions (ttbar-enriched DER_sum_pt tail + rest),
     with empirical CI coverage checked BEFORE any verdict is trusted
     (registry falsifier); diboson expected UNRESOLVED (no viable CR).
  B. True-weighted claims A_w^theta >= tau: the I2-nominal auditor
     estimates the WRONG estimand under theta_norm (its false-certification
     against the true estimand is measured); the I3 worst-case-over-s-box
     auditor restores fail-closed control (alpha split per spec §4b).
  C. combo3 contamination stress: CR-based s-hat under simultaneous
     feature shifts is biased by selection migration — measured and
     reported (the principled joint treatment is E15's profiling).

Development world: seed-101 archives only (campaign quarantine).
Outputs: results/tables/E14_i3.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from joblib import Parallel, delayed

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from qevc.auditing.claims import Verdict  # noqa: E402
from qevc.auditing.rates import (  # noqa: E402
    fit_norm_scales,
    resolve_rate_claim,
    worst_case_weighted_verdict,
)
from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.statistics.weighted import resolve_weighted_claim  # noqa: E402
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E14 = yaml.safe_load((REPO / "configs/experiments/E14.yaml").read_text())
E13_RESULTS = json.loads((REPO / "results/tables/E13_weighted_cs.json").read_text())
E03_RESULTS = json.loads((REPO / "results/tables/E03_geometry.json").read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"
WEIGHT_ONLY = ("ttbar_scale", "diboson_scale", "bkg_scale")

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stable_rng(*parts) -> np.random.Generator:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def true_scales(env: Environment) -> dict[str, float]:
    return {"s_tt": env.ttbar_scale, "s_db": env.diboson_scale,
            "s_bkg": env.bkg_scale}


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")
    labels_raw = raw["labels"].to_numpy().astype(int)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    full = loader.process_stats()["weight_sums"]

    def role_factors(df):
        got = df.groupby("detailed_labels", observed=True)["weights"].sum()
        return {proc: full[proc] / float(got[proc]) for proc in got.index}

    # ---- CR design + analyst templates on auditor_dev (D-021) --------------
    ad = frames["auditor_dev"]
    f_ad = role_factors(ad)
    feat = E14["control_regions"]["cr_ttbar"]["feature"]
    thr_cr = float(np.quantile(ad[feat].to_numpy(),
                               E14["control_regions"]["cr_ttbar"]["quantile"]))
    log(f"CR_ttbar: {feat} > {thr_cr:.2f} (q90 on auditor_dev)")

    def cr_yields(df, factors, with_var: bool = False):
        """Per-CR (cr_tt, cr_rest) yields for sig / ttbar / diboson / other.
        ``with_var`` also returns the per-CR template-MC-stat variance
        Σ_g Σ_i w_i² (D-024 amendment; Barlow–Beeston-lite)."""
        w = df["weights"].to_numpy(copy=True)
        dl = df["detailed_labels"].to_numpy()
        for proc, f in factors.items():
            w[dl == proc] *= f
        in_tt = df[feat].to_numpy() > thr_cr
        out = {}
        var = np.zeros(2)
        for grp, mask_p in (("sig", dl == "htautau"), ("ttbar", dl == "ttbar"),
                            ("diboson", dl == "diboson"),
                            ("other", dl == "ztautau")):
            out[grp] = np.array([float(w[in_tt & mask_p].sum()),
                                 float(w[~in_tt & mask_p].sum())])
            var += np.array([float((w[in_tt & mask_p] ** 2).sum()),
                             float((w[~in_tt & mask_p] ** 2).sum())])
        if with_var:
            return out, var
        return out

    tmpl, tmpl_var = cr_yields(ad, f_ad, with_var=True)  # analyst belief
    purity_tt = tmpl["ttbar"][0] / sum(v[0] for v in tmpl.values())
    log(f"CR_ttbar purity (ttbar fraction): {purity_tt:.3f}; "
        f"yields sig={tmpl['sig']}, tt={tmpl['ttbar']}, db={tmpl['diboson']}, "
        f"other={tmpl['other']}")

    # ---- environments -------------------------------------------------------
    env_map = dict([("nominal", Environment())] + environments())
    env_names = (["nominal"]
                 + [e for e in env_map
                    if any(e.startswith(p) for p in WEIGHT_ONLY)]
                 + E14["environments"]["combos"])

    te_nom = build_environment_dataset(raw, Environment(),
                                       row_ids=raw_splits["nominal_test"])
    f_te = role_factors(te_nom)

    # ---- A. rate claims with MC-validated CIs ------------------------------
    mc = E14["rate_mc"]
    rate_out: dict = {}

    def rate_env(env_name: str) -> tuple[str, dict]:
        env = env_map[env_name]
        te = build_environment_dataset(raw, env,
                                       row_ids=raw_splits["nominal_test"])
        lam_true_by_grp = cr_yields(te, f_te)
        lam_true = sum(lam_true_by_grp.values())
        s_true = true_scales(env)
        cover = {"s_tt": 0, "s_bkg": 0}
        verdict_counts = {f"{c['param']}|{c['band']}":
                          {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                          for c in E14["rate_claims"]}
        bias_tt, bias_bkg = [], []
        for r in range(mc["n_rep"]):
            rng = stable_rng(mc["seed_salt"], env_name, r)
            counts = rng.poisson(lam_true)
            fit = fit_norm_scales(counts, tmpl["sig"], tmpl["ttbar"],
                                  tmpl["diboson"], tmpl["other"],
                                  alpha=mc["alpha"], template_var=tmpl_var)
            bias_tt.append(fit["s_tt_hat"] - s_true["s_tt"])
            bias_bkg.append(fit["s_bkg_hat"] - s_true["s_bkg"])
            if fit["ci_tt"][0] <= s_true["s_tt"] <= fit["ci_tt"][1]:
                cover["s_tt"] += 1
            if fit["ci_bkg"][0] <= s_true["s_bkg"] <= fit["ci_bkg"][1]:
                cover["s_bkg"] += 1
            for c in E14["rate_claims"]:
                band = (1.0 - c["band"], 1.0 + c["band"])
                if c["param"] == "s_tt":
                    v = resolve_rate_claim(fit["ci_tt"], band)
                elif c["param"] == "s_bkg":
                    v = resolve_rate_claim(fit["ci_bkg"], band)
                else:   # s_db: unidentified -> clip-range "CI"
                    v = resolve_rate_claim((0.0, 2.0), band)
                verdict_counts[f"{c['param']}|{c['band']}"][v.value] += 1
        # error accounting vs truth
        errors = {}
        for c in E14["rate_claims"]:
            key = f"{c['param']}|{c['band']}"
            s_val = {"s_tt": s_true["s_tt"], "s_bkg": s_true["s_bkg"],
                     "s_db": s_true["s_db"]}[c["param"]]
            truth = abs(s_val - 1.0) <= c["band"]
            vc = verdict_counts[key]
            errors[key] = {
                "truth": bool(truth),
                "false_cert_rate": (vc["SUPPORTED"] / mc["n_rep"]
                                    if not truth else None),
                "false_refute_rate": (vc["REFUTED"] / mc["n_rep"]
                                      if truth else None),
                "verdicts": vc}
        return env_name, {
            "s_true": s_true,
            "ci_coverage": {k: v / mc["n_rep"] for k, v in cover.items()},
            "s_hat_bias": {"s_tt": round(float(np.mean(bias_tt)), 5),
                           "s_bkg": round(float(np.mean(bias_bkg)), 6)},
            "claims": errors}

    log(f"rate MC: {len(env_names)} envs x {mc['n_rep']} reps")
    results = Parallel(n_jobs=-1)(delayed(rate_env)(e) for e in env_names)
    rate_out = dict(results)

    # falsifier: CI coverage on weight-only + nominal envs (no contamination)
    wo_names = [e for e in env_names if e == "nominal"
                or any(e.startswith(p) for p in WEIGHT_ONLY)]
    slack = 3 * np.sqrt(0.05 * 0.95 / mc["n_rep"])
    cov_ok = all(rate_out[e]["ci_coverage"][p] >= 1 - mc["alpha"] - slack
                 for e in wo_names for p in ("s_tt", "s_bkg"))
    log(f"rate CI coverage falsifier: {'PASS' if cov_ok else 'FAIL'}")

    # ---- I1 blindness (computational fact + archived sensor values) --------
    floor = max(v["kernels"]["quantum"]["mmd2"]
                for e, v in E03_RESULTS["environments"].items()
                if any(e.startswith(p) for p in WEIGHT_ONLY))
    i1_blind = {e: {"mmd2": E03_RESULTS["environments"][e]["kernels"]["quantum"]["mmd2"],
                    "above_floor": bool(
                        E03_RESULTS["environments"][e]["kernels"]["quantum"]["mmd2"]
                        > floor)}
                for e in env_names if e in E03_RESULTS["environments"]
                and any(e.startswith(p) for p in WEIGHT_ONLY)}

    # ---- B. true-weighted chain --------------------------------------------
    wc = E14["weighted_chain"]
    refs = E13_RESULTS["part_b_benchmark"]["frozen_refs"]
    w_max = E13_RESULTS["part_b_benchmark"]["w_max"]["value"]
    a_cs = wc["alpha_total"] / 2.0
    a_par = wc["alpha_total"] / 4.0
    chain_out: dict = {}
    chain_envs = [e for e in env_names if e != "nominal"]
    for env_name in chain_envs:
        env = env_map[env_name]
        te = build_environment_dataset(raw, env,
                                       row_ids=raw_splits["nominal_test"])
        w_true = te["weights"].to_numpy()
        rid = te["row_id"].to_numpy()
        dl = te["detailed_labels"].to_numpy()
        y_env = labels_raw[rid]
        npz = np.load(env_filename(env_name))
        if not np.array_equal(npz["row_id"], rid):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        # nominal weights of the SAME surviving rows
        w0_all = raw["weights"].to_numpy()
        w_nom = w0_all[rid]
        is_tt = dl == "ttbar"
        is_db = dl == "diboson"
        is_bkg = y_env == 0
        lam_true_by_grp = cr_yields(te, f_te)
        lam_true = sum(lam_true_by_grp.values())
        chain_out[env_name] = {"models": {}}
        for key in E14["models"]:
            thr = refs[key]["thr"]
            m_s_w = refs[key]["m_s_w"]
            corr = ((npz[key] >= thr).astype(int) == y_env).astype(float)
            a_w_theta = float((w_true * corr).sum() / w_true.sum())
            a_w_nom = float((w_nom * corr).sum() / w_nom.sum())
            entry = {"a_w_theta": round(a_w_theta, 5),
                     "a_w_nominal_est": round(a_w_nom, 5), "claims": {}}
            for d in wc["deltas"]:
                tau = float(np.clip(m_s_w - d, 0.0, 1.0))
                truth_theta = a_w_theta >= tau
                i2 = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                i3 = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                i2_false_cert = i3_false_cert = 0
                for s in range(wc["audit_seeds"]):
                    rng = stable_rng(wc["seed_salt"], env_name, key, d, s)
                    idx = rng.integers(0, len(corr), size=wc["n_max"])
                    # I2-nominal: audits the WRONG estimand under theta_norm
                    r2 = resolve_weighted_claim(corr[idx], w_nom[idx], tau,
                                                w_max, alpha=wc["alpha_total"])
                    i2[r2.verdict.value] += 1
                    if not truth_theta and r2.verdict is Verdict.SUPPORTED:
                        i2_false_cert += 1
                    # I3: CR counts -> s-box -> worst-case corners
                    counts = rng.poisson(lam_true)
                    fit = fit_norm_scales(counts, tmpl["sig"], tmpl["ttbar"],
                                          tmpl["diboson"], tmpl["other"],
                                          alpha=a_par, template_var=tmpl_var)
                    boxes = {"ttbar": fit["ci_tt"], "diboson": (0.0, 2.0),
                             "bkg": fit["ci_bkg"]}
                    r3 = worst_case_weighted_verdict(
                        corr[idx], w_nom[idx], is_tt[idx], is_db[idx],
                        is_bkg[idx], tau, w_max, boxes, alpha_cs=a_cs)
                    i3[r3["verdict"].value] += 1
                    if not truth_theta and r3["verdict"] is Verdict.SUPPORTED:
                        i3_false_cert += 1
                entry["claims"][str(d)] = {
                    "tau": round(tau, 5), "truth_theta": bool(truth_theta),
                    "margin_theta": round(a_w_theta - tau, 5),
                    "margin_nominal": round(a_w_nom - tau, 5),
                    "i2_nominal_verdicts": i2, "i3_verdicts": i3,
                    "i2_false_cert": i2_false_cert,
                    "i3_false_cert": i3_false_cert}
            chain_out[env_name]["models"][key] = entry
        log(f"weighted chain {env_name}: done")

    # ---- claim x information-set table -------------------------------------
    i3_fc_total = sum(
        m["claims"][d]["i3_false_cert"]
        for env_e in chain_out.values() for m in env_e["models"].values()
        for d in m["claims"])
    i2_fc_total = sum(
        m["claims"][d]["i2_false_cert"]
        for env_e in chain_out.values() for m in env_e["models"].values()
        for d in m["claims"])
    n_false_streams = sum(
        wc["audit_seeds"]
        for env_e in chain_out.values() for m in env_e["models"].values()
        for d in m["claims"] if not m["claims"][d]["truth_theta"])
    table = {
        "classifier_performance_unweighted": {
            "I0": "UNRESOLVED (impossibility)", "I1": "veto only",
            "I2": "resolvable (E05: fc 0.61%)", "I3": "resolvable"},
        "classifier_performance_weighted_nominal_estimand": {
            "I0": "UNRESOLVED", "I1": "veto only",
            "I2": "resolvable (E13: fc 0.02%)", "I3": "resolvable"},
        "true_weighted_performance_under_theta_norm": {
            "I0": "UNRESOLVED", "I1": "UNRESOLVED (proposition 4b)",
            "I2": f"WRONG ESTIMAND (measured fc {i2_fc_total}/{n_false_streams})",
            "I3": f"resolvable worst-case (fc {i3_fc_total}/{n_false_streams})"},
        "normalization_rate_claims": {
            "I0": "UNRESOLVED", "I1": "UNRESOLVED (proposition 4b)",
            "I2": "UNRESOLVED (nominal-weight stream theta-invariant)",
            "I3": "resolvable for s_tt/s_bkg (MC-validated CIs); s_db "
                  "UNIDENTIFIED (no CR) -> UNRESOLVED"},
        "physics_level_validity": {
            "I0": "UNRESOLVED", "I1": "UNRESOLVED",
            "I2": "insufficient (E08/E12: decoupling)",
            "I3": "requires inference procedure consuming theta-hat (E15)"},
    }

    out = {
        "experiment": "E14",
        "proposition": "docs/weighted_certification_spec.md §4b",
        "control_region": {"feature": feat, "threshold": round(thr_cr, 3),
                           "purity_ttbar": round(float(purity_tt), 4),
                           "templates": {k: [round(x, 2) for x in v]
                                         for k, v in tmpl.items()}},
        "rate_claims": rate_out,
        "rate_ci_coverage_falsifier_pass": bool(cov_ok),
        "i1_blindness_weight_only": i1_blind,
        "weighted_chain": chain_out,
        "claim_information_table": table,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E14_i3.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E14", config={"E01": E01, "E14": E14}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E14 complete in {out['wall_seconds']} s -> {out_path}")
    log(f"I2-nominal false certs: {i2_fc_total}/{n_false_streams}; "
        f"I3 false certs: {i3_fc_total}/{n_false_streams}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
