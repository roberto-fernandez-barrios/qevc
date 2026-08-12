"""E08v3 — Multi-draw independent-MC beliefs (registry E08v3; D-031).

Disposition of the E08v2 falsifier firings. E08v2 evaluated coverage
CONDITIONAL on a single belief half-split draw, which is degenerate when
belief-side MC-stat dominates the interval; this run measures the
MARGINAL coverage over K independent draws and adds the
emulation-symmetric accounting independent_bb_sym (truth-half sum(w^2)
term added; in the field, where nature is exact, bb_sym == bb).

Arms (registry entry, falsifier frozen before execution):
  - Counting, nominal env, K=400 draws, 4 audit models, frozen mu/PE
    grids, four accountings; per-draw variance components stored for
    both halves so the bb model prediction is computable from the table.
  - Profile L2, K=10 draws, cells {tes=0.98 x A:xgboost (flagship),
    nominal x A:xgboost (shift-free control)}, 200 PEs, D-023 frozen.

Outputs: results/tables/E08v3_multidraw.json + manifest.
Smoke mode (--smoke): tiny K/PE counts, output to a scratch path, no
manifest — end-to-end plumbing check only.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from math import erf, sqrt
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
sys.path.insert(0, str(REPO / "experiments/E15_realistic_inference"))
sys.path.insert(0, str(REPO / "experiments/E08_physics_inference"))

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

from run_e02 import environments, train_frozen_models  # noqa: E402
from run_e08v2 import (  # noqa: E402
    env_filename,
    lumi_factors_for,
    rescaled,
)
from run_e15 import (  # noqa: E402
    PROCESSES,
    make_templates,
    run_cell,
    score_bin_edges,
    stable_seed,
)
import run_e15  # noqa: E402

E08V3 = yaml.safe_load((REPO / "configs/experiments/E08v3.yaml").read_text())
E08V2 = yaml.safe_load((REPO / E08V3["base"]).read_text())
E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E08 = yaml.safe_load((REPO / E08V2["base_counting"]).read_text())
E15 = run_e15.E15


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def half_split(test_df, salt: str) -> tuple[np.ndarray, np.ndarray]:
    """Stratified-by-process half split, parameterized salt (E08v2 logic)."""
    digest = hashlib.sha256(salt.encode()).digest()
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


def draw_salt(k: int) -> str:
    return f"{E08V3['split']['salt_prefix']}:{k:03d}"


def main() -> int:  # noqa: PLR0915
    smoke = "--smoke" in sys.argv
    k_count = 3 if smoke else E08V3["counting"]["n_draws"]
    k_prof = 1 if smoke else E08V3["profile_spotcheck"]["n_draws"]
    n_pe_prof = 10 if smoke else E08V3["profile_spotcheck"]["n_pe"]
    n_pe_count = 50 if smoke else E08["pseudo_experiments"]

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
    test_frame = frames["nominal_test"]
    test_rid = test_frame["row_id"].to_numpy()

    models = train_frozen_models(frames)
    sv_df = frames["source_val"]
    y_sv = sv_df["labels"].to_numpy()
    w_sv_full = rescaled(sv_df, lumi_factors_for(frames["nominal_test"],
                                                 loader))

    # frozen SR thresholds — identical procedure/inputs to E08/E08v2
    qs = np.linspace(0.5, 0.999,
                     E08["signal_region"]["threshold_grid_quantiles"])
    sr: dict[str, float] = {}
    for key in E08V3["counting"]["models"]:
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

    # ---- counting arm: nominal env, K draws ------------------------------
    te = build_environment_dataset(raw, Environment(), row_ids=test_ids)
    npz = np.load(env_filename("nominal"))
    if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
        raise RuntimeError("row alignment mismatch in nominal")
    rid = te["row_id"].to_numpy()
    y = labels_raw[rid]
    w_raw_te = te["weights"].to_numpy()
    dl_te = te["detailed_labels"].to_numpy()
    sel_by_key = {key: npz[key] >= sr[key]
                  for key in E08V3["counting"]["models"]}

    z = 1.0
    mu_grid = E08["mu_true_grid"]
    accs = E08V3["counting"]["accountings"]
    count_draws: list[dict] = []
    for k in range(1, k_count + 1):
        belief_ids, truth_ids = half_split(test_frame, draw_salt(k))
        m_bel_t = np.isin(test_rid, belief_ids)
        bel_nom = test_frame[m_bel_t]
        tru_nom = test_frame[~m_bel_t]
        f_bel = lumi_factors_for(bel_nom, loader)
        f_tru = lumi_factors_for(tru_nom, loader)
        fac_b = np.ones_like(w_raw_te)
        fac_t = np.ones_like(w_raw_te)
        for proc, f in f_bel.items():
            fac_b[dl_te == proc] = f
        for proc, f in f_tru.items():
            fac_t[dl_te == proc] = f
        w_b = w_raw_te * fac_b
        w_t = w_raw_te * fac_t
        m_bel = np.isin(rid, belief_ids)
        m_tru = np.isin(rid, truth_ids)
        rng = np.random.default_rng(stable_seed("E08V3", "count", k))
        draw_out: dict = {"draw": k}
        for key in E08V3["counting"]["models"]:
            sel = sel_by_key[key]
            sb_t = sel & (y == 1) & m_tru
            bb_t = sel & (y == 0) & m_tru
            sb_b = sel & (y == 1) & m_bel
            bb_b = sel & (y == 0) & m_bel
            s0_t = float(w_t[sb_t].sum())
            b0_t = float(w_t[bb_t].sum())
            s0_b = float(w_b[sb_b].sum())
            b0_b = float(w_b[bb_b].sum())
            var_s0_b = float((w_b[sb_b] ** 2).sum())
            var_b0_b = float((w_b[bb_b] ** 2).sum())
            var_s0_t = float((w_t[sb_t] ** 2).sum())
            var_b0_t = float((w_t[bb_t] ** 2).sum())
            cov = {a: [] for a in accs}
            for mu in mu_grid:
                N = rng.poisson(mu * s0_t + b0_t, size=n_pe_count)
                # (i) shared: beliefs from the truth half itself
                mu_hat = (N - b0_t) / s0_t
                sig = np.sqrt(np.maximum(N, 1.0)) / s0_t
                cov["shared_truth_half"].append(float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig)))
                # (ii) independent naive
                mu_hat = (N - b0_b) / s0_b
                sig = np.sqrt(np.maximum(N, 1.0)) / s0_b
                cov["independent_naive"].append(float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig)))
                # (iii) belief-side BB-lite (field estimator)
                sig_bb = np.sqrt(np.maximum(N, 1.0) + var_b0_b
                                 + (mu_hat ** 2) * var_s0_b) / s0_b
                cov["independent_bb"].append(float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig_bb)))
                # (iv) + truth-half term (emulation-honest)
                sig_sym = np.sqrt(np.maximum(N, 1.0)
                                  + var_b0_b + var_b0_t
                                  + (mu_hat ** 2) * (var_s0_b + var_s0_t)
                                  ) / s0_b
                cov["independent_bb_sym"].append(float(
                    np.mean(np.abs(mu_hat - mu) <= z * sig_sym)))
            draw_out[key] = {
                "s0_t": round(s0_t, 2), "b0_t": round(b0_t, 2),
                "s0_b": round(s0_b, 2), "b0_b": round(b0_b, 2),
                "var_s0_b": round(var_s0_b, 2),
                "var_b0_b": round(var_b0_b, 2),
                "var_s0_t": round(var_s0_t, 2),
                "var_b0_t": round(var_b0_t, 2),
                "coverage": {a: round(float(np.mean(cov[a])), 4)
                             for a in accs},
            }
        count_draws.append(draw_out)
        if k % 25 == 0 or k == k_count:
            log(f"counting draw {k}/{k_count}")

    marginal = {}
    for key in E08V3["counting"]["models"]:
        marginal[key] = {a: round(float(np.mean(
            [d[key]["coverage"][a] for d in count_draws])), 4) for a in accs}
        # model prediction for the belief-only bb accounting, from the
        # stored per-draw components (documents hypothesis (ii))
        ratios = []
        for d in count_draws:
            c = d[key]
            nbar = c["s0_t"] + c["b0_t"]
            v_b = c["var_b0_b"] + c["var_s0_b"]
            v_t = c["var_b0_t"] + c["var_s0_t"]
            ratios.append(sqrt((nbar + v_b) / (nbar + v_b + v_t)))
        r = float(np.mean(ratios))
        marginal[key]["bb_predicted"] = round(erf(r / sqrt(2.0)), 4)

    # falsifier (a): marginal bb_sym within 0.6827 +- band, gated models
    band = E08V3["acceptance"]["bb_sym_band"]
    gated = ["A:qksvc", "A:rbf_svc", "A:xgboost"]
    arm_a = {}
    n_fail = 0
    for key in gated:
        covm = marginal[key]["independent_bb_sym"]
        ok = abs(covm - 0.6827) <= band
        arm_a[key] = {"marginal_coverage_bb_sym": covm, "pass": bool(ok)}
        n_fail += (not ok)
    arm_a["pass"] = bool(n_fail < 2)
    log("counting arm done: " + json.dumps(
        {k: marginal[k]["independent_bb_sym"] for k in gated}))

    # ---- profile arm: K draws x 2 cells ----------------------------------
    key_prof = "A:xgboost"
    log("profile arm: frozen bin edges")
    model, cal, _thr, cols = models[key_prof]
    p_sv = cal.predict_proba(model.scores(sv_df[cols].to_numpy(float)))
    edges = {key_prof: score_bin_edges(p_sv, w_sv_full, y_sv,
                                       E15["binning"]["n_bins"],
                                       E15["binning"]["b_floor"])}

    anchor_envs = (["nominal"]
                   + [f"tes={v}" for v in E15["anchors"]["tes"]]
                   + [f"jes={v}" for v in E15["anchors"]["jes"]]
                   + [f"soft_met={g}/seed{s}" for g in
                      E15["anchors"]["soft_met"] for s in (11, 12, 13)])
    cell_envs = sorted({c["env"]
                        for c in E08V3["profile_spotcheck"]["cells"]})
    need = sorted(set(anchor_envs) | set(cell_envs))
    env_map = dict([("nominal", Environment())] + environments())
    env_cache: dict = {}
    for env_name in need:
        te_e = build_environment_dataset(raw, env_map[env_name],
                                         row_ids=test_ids)
        npz_e = np.load(env_filename(env_name))
        if not np.array_equal(npz_e["row_id"], te_e["row_id"].to_numpy()):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        env_cache[env_name] = {
            "rid": te_e["row_id"].to_numpy(),
            "dl": te_e["detailed_labels"].to_numpy(),
            "w_raw": te_e["weights"].to_numpy(),
            "p": np.clip(npz_e[key_prof], 0.0, 1.0),
        }
        log(f"env cache {env_name}: done")

    def true_theta_of(env: Environment) -> dict:
        return {"tes": (env.tes - 1.0) / 0.01, "jes": (env.jes - 1.0) / 0.01,
                "soft_met": env.soft_met, "ttbar_scale": env.ttbar_scale,
                "diboson_scale": env.diboson_scale,
                "bkg_scale": env.bkg_scale}

    profile_draws: list[dict] = []
    for k in range(1, k_prof + 1):
        belief_ids, truth_ids = half_split(test_frame, draw_salt(k))
        m_bel_t = np.isin(test_rid, belief_ids)
        f_bel = lumi_factors_for(test_frame[m_bel_t], loader)
        f_tru = lumi_factors_for(test_frame[~m_bel_t], loader)
        hists_bel: dict = {}
        hists_tru: dict = {}
        for env_name in need:
            c = env_cache[env_name]
            fac_b = np.ones_like(c["w_raw"])
            fac_t = np.ones_like(c["w_raw"])
            for proc, f in f_bel.items():
                fac_b[c["dl"] == proc] = f
            for proc, f in f_tru.items():
                fac_t[c["dl"] == proc] = f
            w_b = c["w_raw"] * fac_b
            w_t = c["w_raw"] * fac_t
            m_bel = np.isin(c["rid"], belief_ids)
            m_tru = np.isin(c["rid"], truth_ids)
            hists_bel[env_name] = {key_prof: {}}
            hists_tru[env_name] = {key_prof: {}}
            for proc in PROCESSES:
                mp = c["dl"] == proc
                hists_bel[env_name][key_prof][proc], _ = np.histogram(
                    c["p"][mp & m_bel], bins=edges[key_prof],
                    weights=w_b[mp & m_bel])
                hists_tru[env_name][key_prof][proc], _ = np.histogram(
                    c["p"][mp & m_tru], bins=edges[key_prof],
                    weights=w_t[mp & m_tru])
        templates_bel = make_templates(hists_bel, edges, key_prof)
        draw_out = {"draw": k}
        for cell in E08V3["profile_spotcheck"]["cells"]:
            env_name = cell["env"]
            env = env_map[env_name]
            s_true = hists_tru[env_name][key_prof]["htautau"].astype(float)
            b_true = sum(hists_tru[env_name][key_prof][p].astype(float)
                         for p in PROCESSES if p != "htautau")
            per_mu = {}
            for mu in E15["mu_true_grid"]:
                r = run_cell(templates_bel, E15["profile"]["l2_shapes"],
                             E15["profile"]["l2_norms"],
                             s_true, b_true, mu, n_pe_prof,
                             stable_seed("E08V3", "L2", k, env_name,
                                         key_prof, mu),
                             E15["ci_z"], true_theta_of(env))
                per_mu[str(mu)] = r
            cov_mean = float(np.mean([v["coverage"]
                                      for v in per_mu.values()]))
            bias_mean = float(np.mean([v["bias"] for v in per_mu.values()]))
            draw_out[f"{env_name}|{key_prof}"] = {
                "per_mu": per_mu,
                "coverage_mean": round(cov_mean, 4),
                "bias_mean": round(bias_mean, 4)}
            log(f"profile draw {k}/{k_prof} {env_name}: "
                f"coverage {cov_mean:.4f} bias {bias_mean:+.2f}")
        profile_draws.append(draw_out)

    flag_cell = "tes=0.98|A:xgboost"
    nom_cell = "nominal|A:xgboost"
    flag_covs = [d[flag_cell]["coverage_mean"] for d in profile_draws]
    nom_covs = [d[nom_cell]["coverage_mean"] for d in profile_draws]
    n_below = int(sum(c < 0.633 for c in flag_covs))
    if n_below >= E08V3["acceptance"]["flagship_generic_ge"]:
        strength = "generic"
    elif n_below <= E08V3["acceptance"]["flagship_atypical_le"]:
        strength = "v2_draw_atypical"
    else:
        strength = "draw_dependent"
    arm_b = {
        "flagship_coverage_per_draw": [round(c, 4) for c in flag_covs],
        "nominal_coverage_per_draw": [round(c, 4) for c in nom_covs],
        "n_draws_below_0633": n_below,
        "strength_of_statement": strength,
        "e08v2_single_draw": {"flagship": 0.0, "e15_shared": 0.7188},
    }

    out = {
        "experiment": "E08v3",
        "declared_status": "multi-draw marginal evaluation of the "
                           "independent-MC belief estimators (D-031 "
                           "disposition of the E08v2 falsifier firings)",
        "smoke": smoke,
        "n_draws": {"counting": k_count, "profile": k_prof},
        "signal_regions": {kk: round(v, 5) for kk, v in sr.items()},
        "counting_marginal": marginal,
        "counting_draws": count_draws,
        "profile_draws": profile_draws,
        "acceptance": {"a_marginal_bb_sym": arm_a,
                       "b_flagship_strength": arm_b,
                       "all_pass": bool(arm_a["pass"])},
        "wall_seconds": round(time.time() - t0, 1),
    }
    if smoke:
        out_path = Path(sys.argv[sys.argv.index("--smoke") + 1]) \
            if len(sys.argv) > sys.argv.index("--smoke") + 1 \
            else REPO / "results/tables/E08v3_smoke_DELETEME.json"
        out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
        log(f"SMOKE ok in {out['wall_seconds']} s -> {out_path}")
        return 0

    out_path = REPO / "results/tables/E08v3_multidraw.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E08v3", config={"E08v3": E08V3},
        seed=stable_seed("E08V3", "count", 1),
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet":
                        checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E08v3 complete in {out['wall_seconds']} s -> {out_path}")
    log("ACCEPTANCE: " + json.dumps(
        {"a_pass": arm_a["pass"], "b_strength": strength}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
