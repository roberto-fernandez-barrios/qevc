"""E15 — Realistic physics inference (registry E15; D-023 + amendments).

Does the classifier-vs-physics decoupling survive a physically defensible
inference chain — and which information restores validity where it does not?

Levels: L1 = deployment-blind counting (E08's table, reused as baseline);
L2 = binned Poisson profile likelihood over the frozen classifier score with
all six benchmark nuisances profiled; L3 = the same machinery with the
actually-shifted family OMITTED from the profile (predeclared realistic
misspecification).

Calibration gate (falsifier): L2 at the nominal environment must cover at
0.6827 within tolerance before any shifted-environment number is
interpreted.

Outputs: results/tables/E15_inference.json.
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

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.inference.profile_likelihood import (  # noqa: E402
    NORM_SIGMA,
    ProfileLikelihood,
    TemplateSet,
    score_bin_edges,
)
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E15 = yaml.safe_load((REPO / "configs/experiments/E15.yaml").read_text())
E08_RESULTS = json.loads((REPO / "results/tables/E08_physics.json").read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"
PROCESSES = ["htautau", "ztautau", "ttbar", "diboson"]

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, train_frozen_models  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stable_seed(*parts) -> int:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(digest[:8], "little")


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def env_family(env_name: str) -> str:
    for fam in ("tes", "jes", "soft_met", "ttbar_scale", "diboson_scale",
                "bkg_scale", "combo"):
        if env_name.startswith(fam):
            return fam
    return "nominal"


def build_histogram_store(raw, raw_splits, models, factors) -> tuple:
    """One pass over all environments: per (env, model, process) binned
    yields (lumi-rescaled), plus frozen bin edges per model."""
    test_ids = raw_splits["nominal_test"]
    labels_raw = raw["labels"].to_numpy().astype(int)

    # frozen bin edges on source_val (per model)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    sv = frames["source_val"]
    y_sv = sv["labels"].to_numpy()
    w_sv = sv["weights"].to_numpy(copy=True)
    dl_sv = sv["detailed_labels"].to_numpy()
    for proc, f in factors.items():
        w_sv[dl_sv == proc] *= f
    edges = {}
    for key in E15["models"]:
        model, cal, _thr, cols = models[key]
        p_sv = cal.predict_proba(model.scores(sv[cols].to_numpy(float)))
        edges[key] = score_bin_edges(p_sv, w_sv, y_sv, E15["binning"]["n_bins"],
                                     E15["binning"]["b_floor"])
        log(f"bin edges {key}: {len(edges[key]) - 1} bins")

    hists: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    env_list = [("nominal", Environment())] + environments()
    for env_name, env in env_list:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(env_filename(env_name))
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        w = te["weights"].to_numpy(copy=True)
        dl = te["detailed_labels"].to_numpy()
        for proc, f in factors.items():
            w[dl == proc] *= f
        hists[env_name] = {}
        for key in E15["models"]:
            p = npz[key]
            hists[env_name][key] = {}
            for proc in PROCESSES:
                m = dl == proc
                h, _ = np.histogram(np.clip(p[m], 0.0, 1.0),
                                    bins=edges[key], weights=w[m])
                hists[env_name][key][proc] = h
        log(f"hists {env_name}: done")
    _ = labels_raw
    return hists, edges


def make_templates(hists, edges, key) -> TemplateSet:
    """Analyst templates: nominal + official-grid anchors (shared-simulation
    caveat declared as in D-015)."""
    t = TemplateSet(edges=edges[key], processes=PROCESSES,
                    signal_processes=("htautau",))
    t.nominal = {p: hists["nominal"][key][p].astype(float) for p in PROCESSES}
    t.shape_anchors = {"tes": {}, "jes": {}, "soft_met": {}}
    for env_val, alpha in E15["anchors"]["tes"].items():
        t.shape_anchors["tes"][float(alpha)] = {
            p: hists[f"tes={env_val}"][key][p].astype(float) for p in PROCESSES}
    for env_val, alpha in E15["anchors"]["jes"].items():
        t.shape_anchors["jes"][float(alpha)] = {
            p: hists[f"jes={env_val}"][key][p].astype(float) for p in PROCESSES}
    for gev in E15["anchors"]["soft_met"]:
        reps = [hists[f"soft_met={gev}/seed{s}"][key] for s in (11, 12, 13)]
        t.shape_anchors["soft_met"][float(gev)] = {
            p: np.mean([r[p] for r in reps], axis=0).astype(float)
            for p in PROCESSES}
    return t


def run_cell(templates: TemplateSet, profile_shapes, profile_norms,
             s_true: np.ndarray, b_true: np.ndarray, mu_true: float,
             n_pe: int, seed: int, z: float,
             true_theta: dict | None = None) -> dict:
    """One (env, model, mu, level) cell. D-023 amendment 2: each PE draws
    the auxiliary constraint centers around the environment's TRUE nuisance
    values (unconditional ensemble)."""
    pl = ProfileLikelihood(templates, profile_shapes, profile_norms)
    rng = np.random.default_rng(seed)
    lam = mu_true * s_true + b_true
    true_theta = true_theta or {}
    mu_hats, widths, cover, pulls, n_conv = [], [], 0, [], 0
    for _ in range(n_pe):
        n_obs = rng.poisson(lam)
        aux = {}
        for s in profile_shapes:
            if s in ("tes", "jes"):
                aux[s] = float(rng.normal(true_theta.get(s, 0.0), 1.0))
        for nrm in profile_norms:
            aux[nrm] = float(rng.normal(true_theta.get(nrm, 1.0),
                                        NORM_SIGMA[nrm]))
        res = pl.fit(n_obs, z=z, aux=aux)
        mu_hats.append(res.mu_hat)
        lo, hi = res.interval
        widths.append(hi - lo)
        if lo <= mu_true <= hi:
            cover += 1
        pulls.append(res.nuisance_hat)
        n_conv += res.converged
    mu_hats = np.array(mu_hats)
    pull_summary = {k: round(float(np.mean([p[k] for p in pulls])), 4)
                    for k in pulls[0]} if pulls else {}
    return {"bias": round(float(mu_hats.mean() - mu_true), 4),
            "rmse": round(float(np.sqrt(((mu_hats - mu_true) ** 2).mean())), 4),
            "width_mean": round(float(np.mean(widths)), 4),
            "coverage": round(cover / n_pe, 4),
            "nuisance_hat_mean": pull_summary,
            "converged_frac": round(n_conv / n_pe, 3)}


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    full = loader.process_stats()["weight_sums"]
    got = frames["nominal_test"].groupby("detailed_labels", observed=True)["weights"].sum()
    factors = {proc: full[proc] / float(got[proc]) for proc in got.index}

    models = train_frozen_models(frames)
    hists, edges = build_histogram_store(raw, raw_splits, models, factors)

    templates = {key: make_templates(hists, edges, key) for key in E15["models"]}
    env_list = [("nominal", Environment())] + environments()

    def true_theta_of(env: Environment) -> dict:
        return {"tes": (env.tes - 1.0) / 0.01, "jes": (env.jes - 1.0) / 0.01,
                "soft_met": env.soft_met, "ttbar_scale": env.ttbar_scale,
                "diboson_scale": env.diboson_scale,
                "bkg_scale": env.bkg_scale}
    z = E15["ci_z"]
    l2_shapes = E15["profile"]["l2_shapes"]
    l2_norms = E15["profile"]["l2_norms"]

    # ---- calibration gate: L2 at nominal, 2000 PEs --------------------------
    gate = {}
    gate_jobs = []
    for key in E15["models"]:
        s_true = hists["nominal"][key]["htautau"].astype(float)
        b_true = sum(hists["nominal"][key][p].astype(float)
                     for p in PROCESSES if p != "htautau")
        for mu in E15["mu_true_grid"]:
            gate_jobs.append((key, mu, delayed(run_cell)(
                templates[key], l2_shapes, l2_norms, s_true, b_true, mu,
                E15["pseudo_experiments"]["calibration_gate"],
                stable_seed(E15["seed_salt"], "gate", key, mu), z,
                true_theta_of(Environment()))))
    log(f"calibration gate: {len(gate_jobs)} cells x "
        f"{E15['pseudo_experiments']['calibration_gate']} PEs")
    gate_res = Parallel(n_jobs=-1)(j for _, _, j in gate_jobs)
    tol = E15["calibration_gate"]["tolerance"]
    target = E15["calibration_gate"]["target"]
    n_g = E15["pseudo_experiments"]["calibration_gate"] * len(E15["mu_true_grid"])
    mc_term = 3 * np.sqrt(target * (1 - target) / n_g)
    for key in E15["models"]:
        covs = [r["coverage"] for (k, _mu, _j), r in zip(gate_jobs, gate_res)
                if k == key]
        cov_mean = float(np.mean(covs))
        gate[key] = {"coverage_mean": round(cov_mean, 4),
                     "per_mu": [round(c, 4) for c in covs],
                     "pass": bool(abs(cov_mean - target) <= tol + mc_term)}
        log(f"GATE {key}: coverage {cov_mean:.4f} pass={gate[key]['pass']}")
    if not all(g["pass"] for g in gate.values()):
        log("CALIBRATION GATE FAILED — shifted environments not interpreted")

    # ---- L2 / L3 over the full grid ----------------------------------------
    if not all(g["pass"] for g in gate.values()):
        # M5 audit fix: the gate GATES — no shifted-environment table is
        # produced on a failed calibration.
        out = {"experiment": "E15", "calibration_gate": gate,
               "gate_all_pass": False,
               "note": "gate failed; grid not run (registry falsifier)"}
        out_path = REPO / "results/tables/E15_inference.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        log("gate failed -> wrote gate-only table and stopped")
        return 1

    jobs, meta = [], []
    for env_name, env in env_list:
        fam = env_family(env_name)
        omit = E15["profile"]["l3_omit_by_family"][fam]
        if fam == "combo" and env.soft_met == 0.0:
            # M3 audit fix (registered): combo0/combo1 shift tes+jes only —
            # omitting the inactive soft_met would not be a misspecification
            # stress. Omit tes (shifted in every combo) instead.
            omit = "tes"
        l3_shapes = [s for s in l2_shapes if s != omit]
        l3_norms = [n for n in l2_norms if n != omit]
        tt = true_theta_of(env)
        for key in E15["models"]:
            s_true = hists[env_name][key]["htautau"].astype(float)
            b_true = sum(hists[env_name][key][p].astype(float)
                         for p in PROCESSES if p != "htautau")
            for mu in E15["mu_true_grid"]:
                for level, shp, nrm in (("L2", l2_shapes, l2_norms),
                                        ("L3", l3_shapes, l3_norms)):
                    meta.append((env_name, key, mu, level, omit))
                    jobs.append(delayed(run_cell)(
                        templates[key], shp, nrm, s_true, b_true, mu,
                        E15["pseudo_experiments"]["l2_l3"],
                        stable_seed(E15["seed_salt"], level, env_name, key, mu),
                        z, tt))
    log(f"L2/L3 grid: {len(jobs)} cells x {E15['pseudo_experiments']['l2_l3']} PEs")
    results = Parallel(n_jobs=-1, verbose=1)(jobs)

    out_envs: dict = {}
    for (env_name, key, mu, level, omit), r in zip(meta, results):
        env_e = out_envs.setdefault(env_name, {"l3_omitted": omit, "models": {}})
        mdl = env_e["models"].setdefault(key, {})
        mdl.setdefault(level, {})[str(mu)] = r
    # coverage_mean per (env, model, level) + L1 copy from E08
    summary_cells = []
    for env_name, env_e in out_envs.items():
        for key, mdl in env_e["models"].items():
            for level in ("L2", "L3"):
                covs = [v["coverage"] for v in mdl[level].values()]
                mdl[level + "_coverage_mean"] = round(float(np.mean(covs)), 4)
            e08_env = E08_RESULTS["environments"].get(env_name, {}).get(
                "models", {}).get(key, {})
            mdl["L1_coverage_mean"] = e08_env.get("coverage_mean")
            mdl["delta_auc_e02"] = e08_env.get("delta_auc")
            summary_cells.append({
                "env": env_name, "model": key,
                "L1": mdl["L1_coverage_mean"],
                "L2": mdl["L2_coverage_mean"], "L3": mdl["L3_coverage_mean"],
                "l3_omitted": env_e["l3_omitted"]})

    out = {
        "experiment": "E15",
        "levels": {"L1": "E08 counting (reused)", "L2": "full profile",
                   "L3": "profile minus shifted family (predeclared; "
                         "combo0/1 omit tes — M3 audit fix)"},
        "interpretation_notes": [
            "single-family environments: the fit's anchors coincide with the "
            "truth histograms (shared-simulation), so L2 coverage there does "
            "not test morphing error — combos are the real morphing test",
            "the morphing model is additive across nuisances; combo truth "
            "applies them jointly (cross-terms real) — combo L2 "
            "undercoverage, if any, is morphing misspecification, not "
            "statistics",
        ],
        "calibration_gate": gate,
        "gate_all_pass": bool(all(g["pass"] for g in gate.values())),
        "bin_edges": {k: [round(float(e), 5) for e in v]
                      for k, v in edges.items()},
        "coverage_summary": summary_cells,
        "environments": out_envs,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E15_inference.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E15", config={"E01": E01, "E15": E15}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E15 complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
