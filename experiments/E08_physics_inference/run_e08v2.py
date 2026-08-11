"""E08v2 — Independent-MC beliefs for physics inference (registry E08v2).

Closes the D-015 deferral and the shared-simulation caveat. Verified fact
motivating this run: E08 computes (s0, b0) and the PE truth from the SAME
nominal_test rows (run_e08.py:114-136), and E15 builds its templates from
those same rows (run_e15.py:83,107) — literal row-level sharing.

Design (registry entry, falsifier frozen):
  - Seeded stratified half-split of nominal_test (salt "E08V2"):
    B_belief (analyst MC) vs B_truth (pseudo-experiment truth).
  - Counting arm, full frozen 41-env grid x 4 audit models x mu grid,
    three accountings: (i) shared_truth_half baseline, (ii) independent
    naive (pure-Poisson interval), (iii) independent + delta-method
    MC-stat term from per-process sqrt(sum w^2) of the belief half.
  - Profile arm (bounded): E15-L2 spot-check cells with templates rebuilt
    from B_belief while truth yields come from B_truth; 500 PEs; D-023
    protocol otherwise frozen.

Outputs: results/tables/E08v2_independent_mc.json + manifest.
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
sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
sys.path.insert(0, str(REPO / "experiments/E15_realistic_inference"))

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

from run_e02 import environments, train_frozen_models  # noqa: E402
from run_e15 import (  # noqa: E402
    PROCESSES,
    make_templates,
    run_cell,
    score_bin_edges,
    stable_seed,
)
import run_e15  # noqa: E402

E08V2 = yaml.safe_load((REPO / "configs/experiments/E08v2.yaml").read_text())
E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E08 = yaml.safe_load((REPO / E08V2["base_counting"]).read_text())
E15 = run_e15.E15
FROZEN = yaml.safe_load((REPO / E08V2["frozen_source"]).read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def half_split(test_df) -> tuple[np.ndarray, np.ndarray]:
    """Stratified-by-process half split of the nominal_test role row_ids."""
    digest = hashlib.sha256(E08V2["split"]["seed_salt"].encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
    row_id = test_df["row_id"].to_numpy()
    dl = test_df["detailed_labels"].to_numpy()
    belief, truth = [], []
    for proc in np.unique(dl):
        ids = row_id[dl == proc]
        perm = rng.permutation(len(ids))
        half = len(ids) // 2
        belief.append(ids[perm[:half]])
        truth.append(ids[perm[half:]])
    return np.sort(np.concatenate(belief)), np.sort(np.concatenate(truth))


def lumi_factors_for(df, loader) -> dict[str, float]:
    full = loader.process_stats()["weight_sums"]
    got = df.groupby("detailed_labels", observed=True)["weights"].sum()
    return {proc: full[proc] / float(got[proc]) for proc in got.index}


def rescaled(df, factors) -> np.ndarray:
    w = df["weights"].to_numpy(copy=True)
    dl = df["detailed_labels"].to_numpy()
    for proc, f in factors.items():
        w[dl == proc] *= f
    return w


def main() -> int:  # noqa: PLR0915
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    labels_raw = raw["labels"].to_numpy().astype(int)
    test_ids = raw_splits["nominal_test"]

    belief_ids, truth_ids = half_split(frames["nominal_test"])
    log(f"half split: belief {len(belief_ids):,}  truth {len(truth_ids):,}")
    bel_nom = frames["nominal_test"][np.isin(
        frames["nominal_test"]["row_id"].to_numpy(), belief_ids)]
    tru_nom = frames["nominal_test"][np.isin(
        frames["nominal_test"]["row_id"].to_numpy(), truth_ids)]
    f_bel = lumi_factors_for(bel_nom, loader)
    f_tru = lumi_factors_for(tru_nom, loader)

    models = train_frozen_models(frames)
    sv_df = frames["source_val"]
    y_sv = sv_df["labels"].to_numpy()
    w_sv_full = rescaled(sv_df, lumi_factors_for(frames["nominal_test"],
                                                 loader))

    # frozen SR thresholds (identical procedure/inputs to E08)
    qs = np.linspace(0.5, 0.999,
                     E08["signal_region"]["threshold_grid_quantiles"])
    sr: dict[str, float] = {}
    for key in E08V2["counting"]["models"]:
        model, cal, _thr, cols = models[key]
        p_sv = cal.predict_proba(model.scores(sv_df[cols].to_numpy(float)))
        best_t, best_obj = None, -np.inf
        for t in np.unique(np.quantile(p_sv, qs)):
            sel = p_sv >= t
            s = w_sv_full[sel & (y_sv == 1)].sum()
            b = w_sv_full[sel & (y_sv == 0)].sum()
            if b < E08["signal_region"]["b_floor"]:
                continue
            if s / np.sqrt(b) > best_obj:
                best_obj, best_t = s / np.sqrt(b), float(t)
        sr[key] = best_t
        log(f"SR({key}): t={best_t:.5f}")

    # ---- counting arm ------------------------------------------------------
    rng = np.random.default_rng(E08V2["counting"]["seed"])
    z = 1.0
    env_list = [("nominal", Environment())] + environments()
    beliefs: dict[str, dict[str, tuple]] = {"belief": {}, "truth": {}}
    out_envs: dict = {}
    for env_name, env in env_list:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(env_filename(env_name))
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        rid = te["row_id"].to_numpy()
        m_bel = np.isin(rid, belief_ids)
        m_tru = np.isin(rid, truth_ids)
        y = labels_raw[rid]
        w_b = rescaled(te, f_bel)
        w_t = rescaled(te, f_tru)
        out_envs[env_name] = {}
        for key in E08V2["counting"]["models"]:
            p = npz[key]
            sel = p >= sr[key]
            # truth-half env yields (the PE truth in every accounting)
            s_th = float(w_t[sel & (y == 1) & m_tru].sum())
            b_th = float(w_t[sel & (y == 0) & m_tru].sum())
            if env_name == "nominal":
                s0_t, b0_t = s_th, b_th
                sb = sel & (y == 1) & m_bel
                bb = sel & (y == 0) & m_bel
                s0_b = float(w_b[sb].sum())
                b0_b = float(w_b[bb].sum())
                var_s0 = float((w_b[sb] ** 2).sum())
                var_b0 = float((w_b[bb] ** 2).sum())
                beliefs["truth"][key] = (s0_t, b0_t)
                beliefs["belief"][key] = (s0_b, b0_b, var_s0, var_b0)
            s0_t, b0_t = beliefs["truth"][key]
            s0_b, b0_b, var_s0, var_b0 = beliefs["belief"][key]
            entry: dict = {"s_theta": round(s_th, 2),
                           "b_theta": round(b_th, 2), "accountings": {}}
            for mu in E08["mu_true_grid"]:
                N = rng.poisson(mu * s_th + b_th,
                                size=E08["pseudo_experiments"])
                per_acc = {}
                # (i) shared: beliefs from the truth half itself
                mu_hat = (N - b0_t) / s0_t
                sig = np.sqrt(np.maximum(N, 1.0)) / s0_t
                per_acc["shared_truth_half"] = float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig))
                # (ii) independent naive
                mu_hat = (N - b0_b) / s0_b
                sig = np.sqrt(np.maximum(N, 1.0)) / s0_b
                per_acc["independent_naive"] = float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig))
                # (iii) independent + BB-lite MC-stat term (delta method)
                sig_bb = np.sqrt(np.maximum(N, 1.0) + var_b0
                                 + (mu_hat ** 2) * var_s0) / s0_b
                per_acc["independent_bb"] = float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig_bb))
                entry["accountings"][str(mu)] = {
                    k: round(v, 4) for k, v in per_acc.items()}
            for acc in ("shared_truth_half", "independent_naive",
                        "independent_bb"):
                entry[f"coverage_mean_{acc}"] = round(float(np.mean(
                    [entry["accountings"][str(mu)][acc]
                     for mu in E08["mu_true_grid"]])), 4)
            out_envs[env_name][key] = entry
        log(f"counting {env_name}: done")

    belief_summary = {
        key: {"s0_truth": round(beliefs["truth"][key][0], 2),
              "b0_truth": round(beliefs["truth"][key][1], 2),
              "s0_belief": round(beliefs["belief"][key][0], 2),
              "b0_belief": round(beliefs["belief"][key][1], 2),
              "s0_relerr": round(np.sqrt(beliefs["belief"][key][2])
                                 / beliefs["belief"][key][0], 5),
              "b0_relerr": round(np.sqrt(beliefs["belief"][key][3])
                                 / beliefs["belief"][key][1], 5)}
        for key in E08V2["counting"]["models"]}

    # falsifier arm (a): accounting (iii) nominal coverage within the band
    gate_band = E08V2["acceptance"]["gate_band"]
    gated = ["A:qksvc", "A:rbf_svc", "A:xgboost"]  # E15 gate-passing models
    arm_a = {}
    n_fail = 0
    for key in gated:
        cov = out_envs["nominal"][key]["coverage_mean_independent_bb"]
        ok = abs(cov - 0.6827) <= gate_band
        arm_a[key] = {"nominal_coverage_bb": cov, "pass": bool(ok)}
        n_fail += (not ok)
    arm_a["pass"] = bool(n_fail < 2)

    # ---- profile arm: independent templates spot-check ---------------------
    log("profile arm: building split histogram stores")
    edges = {}
    for key in E15["models"]:
        model, cal, _thr, cols = models[key]
        p_sv = cal.predict_proba(model.scores(sv_df[cols].to_numpy(float)))
        edges[key] = score_bin_edges(p_sv, w_sv_full, y_sv,
                                     E15["binning"]["n_bins"],
                                     E15["binning"]["b_floor"])

    anchor_envs = (["nominal"]
                   + [f"tes={v}" for v in E15["anchors"]["tes"]]
                   + [f"jes={v}" for v in E15["anchors"]["jes"]]
                   + [f"soft_met={g}/seed{s}" for g in
                      E15["anchors"]["soft_met"] for s in (11, 12, 13)])
    cell_envs = sorted({c["env"] for c in E08V2["profile_spotcheck"]["cells"]})
    need = sorted(set(anchor_envs) | set(cell_envs))
    env_map = dict(env_list)
    hists_bel: dict = {}
    hists_tru: dict = {}
    for env_name in need:
        env = env_map[env_name]
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(env_filename(env_name))
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        rid = te["row_id"].to_numpy()
        dl = te["detailed_labels"].to_numpy()
        w_b = rescaled(te, f_bel)
        w_t = rescaled(te, f_tru)
        m_bel = np.isin(rid, belief_ids)
        m_tru = np.isin(rid, truth_ids)
        hists_bel[env_name] = {}
        hists_tru[env_name] = {}
        for key in E15["models"]:
            p = np.clip(npz[key], 0.0, 1.0)
            hists_bel[env_name][key] = {}
            hists_tru[env_name][key] = {}
            for proc in PROCESSES:
                mp = dl == proc
                hists_bel[env_name][key][proc], _ = np.histogram(
                    p[mp & m_bel], bins=edges[key],
                    weights=w_b[mp & m_bel])
                hists_tru[env_name][key][proc], _ = np.histogram(
                    p[mp & m_tru], bins=edges[key],
                    weights=w_t[mp & m_tru])
        log(f"hists {env_name}: done")

    templates_bel = {key: make_templates(hists_bel, edges, key)
                     for key in E15["models"]}
    l2_shapes = E15["profile"]["l2_shapes"]
    l2_norms = E15["profile"]["l2_norms"]
    zci = E15["ci_z"]

    def true_theta_of(env: Environment) -> dict:
        return {"tes": (env.tes - 1.0) / 0.01, "jes": (env.jes - 1.0) / 0.01,
                "soft_met": env.soft_met, "ttbar_scale": env.ttbar_scale,
                "diboson_scale": env.diboson_scale,
                "bkg_scale": env.bkg_scale}

    profile_out: dict = {}
    for cell in E08V2["profile_spotcheck"]["cells"]:
        env_name = cell["env"]
        key = f"A:{cell['model']}"
        env = env_map[env_name]
        s_true = hists_tru[env_name][key]["htautau"].astype(float)
        b_true = sum(hists_tru[env_name][key][p].astype(float)
                     for p in PROCESSES if p != "htautau")
        per_mu = {}
        for mu in E15["mu_true_grid"]:
            r = run_cell(templates_bel[key], l2_shapes, l2_norms,
                         s_true, b_true, mu,
                         E08V2["profile_spotcheck"]["n_pe"],
                         stable_seed("E08V2", "L2ind", env_name, key, mu),
                         zci, true_theta_of(env))
            per_mu[str(mu)] = r
        cov_mean = float(np.mean([v["coverage"] for v in per_mu.values()]))
        profile_out[f"{env_name}|{key}"] = {
            "per_mu": per_mu, "coverage_mean": round(cov_mean, 4)}
        log(f"profile L2(independent templates) {env_name}|{key}: "
            f"coverage {cov_mean:.4f}")

    flag = profile_out.get("tes=0.98|A:xgboost", {})
    arm_b = {
        "flagship_coverage": flag.get("coverage_mean"),
        "e15_shared_reference": 0.7188,
        "pass": bool(flag.get("coverage_mean", 0.0)
                     >= E08V2["acceptance"]["flagship_coverage_below"]),
    }

    out = {
        "experiment": "E08v2",
        "declared_status": "independent-MC beliefs/templates for the frozen "
                           "physics estimators (D-015 deferral closure; "
                           "D-028)",
        "split": {"belief_n": int(len(belief_ids)),
                  "truth_n": int(len(truth_ids)),
                  "seed_salt": E08V2["split"]["seed_salt"]},
        "belief_summary": belief_summary,
        "signal_regions": {k: round(v, 5) for k, v in sr.items()},
        "counting": out_envs,
        "profile_spotcheck": profile_out,
        "acceptance": {"a_nominal_bb_coverage": arm_a,
                       "b_flagship_independent_templates": arm_b,
                       "all_pass": bool(arm_a["pass"] and arm_b["pass"])},
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E08v2_independent_mc.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E08v2", config={"E08v2": E08V2},
        seed=E08V2["counting"]["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet":
                        checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E08v2 complete in {out['wall_seconds']} s -> {out_path}")
    log("ACCEPTANCE: " + json.dumps(
        {"a": arm_a["pass"], "b": arm_b["pass"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
