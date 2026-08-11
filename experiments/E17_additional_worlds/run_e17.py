"""E17 — Additional confirmatory worlds (registry E17; D-028).

Two fresh 300k subsets (seeds 131, 141) from the verified complement of ALL
archived index sets, evaluated with the frozen deployment on the registered
compute-bounded environment subset (17 evaluations/world). Targets: (i) the
between-world variance of absolute physics-weighted metrics (E12 diagnostic's
±0.05 inference), (ii) the missing between-subset variance component of E12
arm (a) (post-audit M6), (iii) SR-composition dependence of norm-nuisance
coverage damage (E12 arm-(e) corrected reading).

Nothing is tuned, selected, or thresholded on E17 data. Falsifier arms are
evaluated in-run and written into the table (registry entry E17).

Outputs: results/tables/E17_worlds.json (+ index archives under
data/processed/used_rows/, split files, manifest).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments/E12_confirmatory"))

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
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
    features_for,
    get_raw_splits,
    tier_a_frame,
)
from qevc.statistics.bootstrap import bootstrap_metric  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

from run_e12 import environments as frozen_environments  # noqa: E402
from run_e12 import parse_params  # noqa: E402

E17 = yaml.safe_load((REPO / "configs/experiments/E17.yaml").read_text())
FROZEN = yaml.safe_load((REPO / E17["frozen_source"]).read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS
USED_ROWS = REPO / "data/processed/used_rows"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_subset() -> list[tuple[str, Environment]]:
    """The registered 17-evaluation subset, resolved from the frozen grid."""
    include = set(E17["environments"]["include"])
    full = dict(frozen_environments())
    out: list[tuple[str, Environment]] = []
    for name in E17["environments"]["include"]:
        if name == "nominal":
            out.append(("nominal", Environment()))
        elif name in full:
            out.append((name, full[name]))
        else:
            raise KeyError(f"registered env {name!r} not in the frozen grid")
    missing = include - {n for n, _ in out}
    if missing:
        raise KeyError(f"unresolved registered envs: {missing}")
    return out


# ---------------------------------------------------------------------------
# Phase 1 — provably disjoint draws (D-028 rule 2)
# ---------------------------------------------------------------------------

def load_archived(name: str) -> np.ndarray:
    path = USED_ROWS / name
    if not path.exists():
        raise RuntimeError(f"required index archive missing: {path}")
    return np.load(path)


def draw_world(loader: FairUniverseLoader, seed: int, tag: str,
               extra: dict[str, np.ndarray]) -> tuple:
    """Draw one fresh world from the complement of all archived index sets."""
    parts = {
        "seed101_subset": load_archived("seed101_subset_n300000_indices.npy"),
        "e00_rowgroups": load_archived("e00_validation_rowgroup_indices.npy"),
        "e12_subset": load_archived("e12_subset_n300000_seed121_indices.npy"),
        **extra,
    }
    exclusion = np.unique(np.concatenate(list(parts.values())))
    n = E17["subset"]["n_total"]
    sub = loader.load_subset(n, seed, renormalize=True, exclude=exclusion,
                             tag=tag)
    idx = np.load(loader.cache_dir / "subsets" /
                  f"subset_n{n}_seed{seed}_renorm_{tag}.indices.npy")
    archive = USED_ROWS / f"e17_{tag}_subset_n{n}_seed{seed}_indices.npy"
    np.save(archive, idx)

    overlaps = {k: int(np.intersect1d(idx, v).size) for k, v in parts.items()}
    if any(overlaps.values()):
        raise RuntimeError(f"E17 draw {tag} NOT disjoint: {overlaps} — abort")
    proof = {
        "indices_sha256": file_sha256(archive),
        "n_excluded": int(exclusion.size),
        "overlaps": overlaps,
    }
    log(f"world {tag} drawn: n={len(sub)}, excluded {exclusion.size:,}, "
        f"all overlaps 0")
    return sub, idx, proof


# ---------------------------------------------------------------------------
# Phase 2 — frozen deployment (verbatim from run_e12.train_frozen, with the
# tier-A seed and model lists passed explicitly per world)
# ---------------------------------------------------------------------------

def train_frozen_world(frames: dict, tier_a_seed: int) -> tuple[dict, object]:
    sv_df = frames["source_val"]
    seed = FROZEN["training_protocol"]["init_seed"]
    q_cols = FROZEN["features"]["quantum"]
    df_a = tier_a_frame(frames["train"],
                        FROZEN["training_protocol"]["tier_a_budget"]["n_train"],
                        tier_a_seed)
    jobs = ([("A", n) for n in E17["models"]["tier_a"]] +
            [("B", n) for n in E17["models"]["tier_b"]])
    models: dict[str, tuple] = {}
    for tier, name in jobs:
        params = parse_params(
            FROZEN["hyperparameters"]["tier_a" if tier == "A" else "tier_b"][name])
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
        m_s_unw = float(np.mean((p_sv >= thr).astype(int) == y_sv))
        models[f"{tier}:{name}"] = (model, cal, thr, cols, m_s_unw)
        log(f"trained+froze {tier}:{name} (thr {thr:.4f}, M_S {m_s_unw:.4f})")
    return models, df_a


# ---------------------------------------------------------------------------
# Phase 3 — one pass per world: landscape metrics + D-015 physics
# ---------------------------------------------------------------------------

def run_world(raw, raw_splits, frames, models, loader,
              world_seed: int) -> dict:
    labels_raw = raw["labels"].to_numpy().astype(int)
    test_ids = raw_splits["nominal_test"]

    # physics: per-process lumi rescale + frozen SR procedure (D-015)
    pe = FROZEN["physics_estimator"]
    full = loader.process_stats()["weight_sums"]
    got = frames["nominal_test"].groupby(
        "detailed_labels", observed=True)["weights"].sum()
    factors = {proc: full[proc] / float(got[proc]) for proc in got.index}

    def rescaled(df):
        w = df["weights"].to_numpy(copy=True)
        dl = df["detailed_labels"].to_numpy()
        for proc, f in factors.items():
            w[dl == proc] *= f
        return w

    sv_df = frames["source_val"]
    w_sv = rescaled(sv_df)
    y_sv = sv_df["labels"].to_numpy()
    qs = np.linspace(0.5, 0.999, pe["signal_region"]["threshold_grid_quantiles"])
    sr: dict[str, float] = {}
    for key in E17["physics"]["models"]:
        model, cal, _t, cols, _m = models[key]
        p_sv = cal.predict_proba(model.scores(sv_df[cols].to_numpy(float)))
        best_t, best_obj = None, -np.inf
        for t in np.unique(np.quantile(p_sv, qs)):
            sel = p_sv >= t
            s = w_sv[sel & (y_sv == 1)].sum()
            b = w_sv[sel & (y_sv == 0)].sum()
            if b < pe["signal_region"]["b_floor"]:
                continue
            if s / np.sqrt(b) > best_obj:
                best_obj, best_t = s / np.sqrt(b), float(t)
        sr[key] = best_t
        log(f"SR({key}): t={best_t:.5f}")

    rng = np.random.default_rng([E17["physics"]["seed"], world_seed])
    bs = E17["nominal_diagnostic"]
    envs = env_subset()
    nominal_exp: dict[str, tuple[float, float]] = {}
    out: dict = {"environments": {}, "signal_regions":
                 {k: round(v, 5) for k, v in sr.items()}}
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        y = labels_raw[te["row_id"].to_numpy()]
        w = te["weights"].to_numpy()
        w_resc = rescaled(te)
        ones = np.ones_like(w)
        entry: dict = {"n_events": int(len(te)), "models": {}}
        for key, (model, cal, thr, cols, _ms) in models.items():
            p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
            m: dict = {
                "auc_w": round(float(weighted_auc(y, p, w)), 5),
                "auc_unw": round(float(weighted_auc(y, p, ones)), 5),
            }
            if env_name == "nominal":
                ci_w = bootstrap_metric(weighted_auc, y, p, w,
                                        n_resamples=bs["n_resamples"],
                                        seed=bs["seed"])
                m["auc_w_ci95"] = [round(ci_w.lower, 5), round(ci_w.upper, 5)]
            if key in E17["physics"]["models"]:
                sel = p >= sr[key]
                s_th = float(w_resc[sel & (y == 1)].sum())
                b_th = float(w_resc[sel & (y == 0)].sum())
                if env_name == "nominal":
                    nominal_exp[key] = (s_th, b_th)
                s0, b0 = nominal_exp[key]
                covs = []
                for mu in pe["mu_true_grid"]:
                    N = rng.poisson(mu * s_th + b_th,
                                    size=pe["pseudo_experiments"])
                    mu_hat = (N - b0) / s0
                    sigma = np.sqrt(np.maximum(N, 1.0)) / s0
                    covs.append(float(np.mean(np.abs(mu_hat - mu) <= sigma)))
                m.update({"s_theta": round(s_th, 2), "b_theta": round(b_th, 2),
                          "coverage_mean": round(float(np.mean(covs)), 4)})
            entry["models"][key] = m
        out["environments"][env_name] = entry
        log(f"world eval {env_name}: n={len(te):,}")
    nom = out["environments"]["nominal"]["models"]
    for env_name, entry in out["environments"].items():
        if env_name == "nominal":
            continue
        entry["delta_auc_w"] = {
            k: round(nom[k]["auc_w"] - m["auc_w"], 5)
            for k, m in entry["models"].items()}
    out["nominal_expectations"] = {k: {"s0": round(v[0], 2),
                                       "b0": round(v[1], 2)}
                                   for k, v in nominal_exp.items()}
    out["partition_sizes"] = {r: int(len(v)) for r, v in frames.items()}
    return out


# ---------------------------------------------------------------------------
# Phase 4 — between-world analysis + registered falsifier arms
# ---------------------------------------------------------------------------

NORM_ENVS = [f"ttbar_scale={v}" for v in (0.96, 0.98, 1.02, 1.04)] + \
            [f"diboson_scale={v}" for v in (0.5, 0.75, 1.25, 1.5)] + \
            [f"bkg_scale={v}" for v in (0.998, 0.999, 1.001, 1.002)]


def prior_world_values() -> dict:
    """Absolute nominal weighted AUCs, contrasts, norm-env coverage and SR
    composition for the two prior worlds, read from their archived tables."""
    e01 = json.loads((REPO / E17["between_world"]["prior_worlds"]["seed101"]
                      ).read_text())
    e12 = json.loads((REPO / E17["between_world"]["prior_worlds"]["seed121"]
                      ).read_text())
    e08 = json.loads((REPO / "results/tables/E08_physics.json").read_text())

    def e01_auc(name: str) -> float:
        node = e01["tiers"]["A"][name]["test"]
        return float(node["auc"] if isinstance(node, dict) else node)

    s101 = {
        "auc_w": {f"A:{m}": e01_auc(m)
                  for m in ("qksvc", "rbf_svc_8f", "rbf_svc", "xgboost",
                            "lightgbm")},
        "coverage": {env: {k: e08["environments"][env]["models"][k]
                           ["coverage_mean"]
                           for k in e08["environments"][env]["models"]}
                     for env in NORM_ENVS},
        "sr_composition": {k: dict(v) for k, v in
                           e08["nominal_expectations"].items()},
    }
    s101["auc_w"]["B:xgboost"] = float(
        e01["tiers"]["B"]["xgboost"]["test"]["auc"]
        if isinstance(e01["tiers"]["B"]["xgboost"]["test"], dict)
        else e01["tiers"]["B"]["xgboost"]["test"])

    e12_nom = e12["landscape"]["nominal"]["models"]
    s121 = {
        "auc_w": {k: float(v["auc"]) for k, v in e12_nom.items()},
        "coverage": {env: {k: e12["physics"]["environments"][env][k]
                           ["coverage_mean"]
                           for k in e12["physics"]["environments"][env]}
                     for env in NORM_ENVS},
        "sr_composition": {k: {"s0": e12["physics"]["environments"]["nominal"]
                               [k]["s_theta"],
                               "b0": e12["physics"]["environments"]["nominal"]
                               [k]["b_theta"]}
                           for k in e12["physics"]["environments"]["nominal"]},
    }
    return {"seed101": s101, "seed121": s121}


def between_world_analysis(worlds: dict, prior: dict) -> dict:
    order = ["seed101", "seed121"] + list(worlds.keys())
    model_keys = sorted(worlds[next(iter(worlds))]["environments"]["nominal"]
                        ["models"].keys())

    def auc_of(wname: str, key: str) -> float | None:
        if wname in worlds:
            return worlds[wname]["environments"]["nominal"]["models"][key][
                "auc_w"]
        return prior[wname]["auc_w"].get(key)

    abs_levels = {}
    for key in model_keys:
        vals = [auc_of(w, key) for w in order]
        known = [v for v in vals if v is not None]
        abs_levels[key] = {
            "per_world": {w: (round(v, 5) if v is not None else None)
                          for w, v in zip(order, vals)},
            "between_world_std": round(float(np.std(known, ddof=1)), 5),
            "range": round(float(np.max(known) - np.min(known)), 5),
        }

    contrasts = {}
    for label, (a, b) in {"qk_minus_xgb": ("A:qksvc", "A:xgboost"),
                          "qk_minus_rbf8": ("A:qksvc", "A:rbf_svc_8f")}.items():
        vals = {w: (auc_of(w, a) - auc_of(w, b)) for w in order
                if auc_of(w, a) is not None and auc_of(w, b) is not None}
        arr = np.array(list(vals.values()))
        contrasts[label] = {
            "per_world": {w: round(v, 5) for w, v in vals.items()},
            "between_world_std_dof3": round(float(np.std(arr, ddof=1)), 5),
            "sign_consistent": bool(np.all(arr < 0)),
        }

    coverage = {}
    for env in NORM_ENVS:
        coverage[env] = {}
        keys = set()
        for w in order:
            src = (worlds[w]["environments"].get(env, {}).get("models", {})
                   if w in worlds else prior[w]["coverage"].get(env, {}))
            keys |= set(k for k in src if k in
                        ("A:qksvc", "A:rbf_svc", "A:xgboost", "B:xgboost"))
        for k in sorted(keys):
            per_w = {}
            for w in order:
                if w in worlds:
                    cell = worlds[w]["environments"].get(env, {}).get(
                        "models", {}).get(k, {})
                    per_w[w] = cell.get("coverage_mean")
                else:
                    per_w[w] = prior[w]["coverage"].get(env, {}).get(k)
            coverage[env][k] = per_w

    sr_comp = {}
    for w in order:
        if w in worlds:
            sr_comp[w] = worlds[w]["nominal_expectations"]
        else:
            sr_comp[w] = prior[w]["sr_composition"]

    return {"world_order": order, "absolute_weighted_auc": abs_levels,
            "paired_contrasts": contrasts,
            "norm_env_coverage_by_world": coverage,
            "sr_composition_by_world": sr_comp}


def evaluate_falsifiers(worlds: dict, between: dict) -> dict:
    arms: dict = {}
    # (a) paired QK−XGB > 0 in any world
    per_w = between["paired_contrasts"]["qk_minus_xgb"]["per_world"]
    arms["a_ordering"] = {
        "qk_minus_xgb_per_world": per_w,
        "pass": bool(all(v <= 0 for v in per_w.values())),
    }
    # (b) degradation signs in the new worlds
    degr = {}
    ok = True
    for wname, wr in worlds.items():
        tes = wr["environments"]["tes=0.98"]["delta_auc_w"]["A:qksvc"]
        combo3 = float(np.mean(
            [wr["environments"][f"combo3/seed{s}"]["delta_auc_w"]["A:qksvc"]
             for s in (11, 12, 13)]))
        degr[wname] = {"tes098_delta_qk": tes,
                       "combo3_mean_delta_qk": round(combo3, 5)}
        ok = ok and tes >= 0 and combo3 >= 0
    arms["b_degradation"] = {**degr, "pass": bool(ok)}
    # (c) between-world std of absolute weighted AUC > 0.10 escalation
    worst = max(v["between_world_std"]
                for v in between["absolute_weighted_auc"].values())
    arms["c_variance_scale"] = {"worst_between_world_std": round(worst, 5),
                                "pass": bool(worst <= 0.10)}
    # predeclared reporting rule (not a falsifier)
    arms["reporting_rule"] = {
        "threshold": 0.02,
        "verdict": ("caveat_replaced_by_measured_bound" if worst <= 0.02
                    else "caveat_confirmed_as_quantified_finding"),
    }
    arms["all_pass"] = bool(all(v["pass"] for v in arms.values()
                                if isinstance(v, dict) and "pass" in v))
    return arms


def main() -> int:
    t0 = time.time()
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")

    worlds_out: dict = {}
    proofs: dict = {}
    extra: dict[str, np.ndarray] = {}
    for wcfg in E17["worlds"]:
        seed, tag = wcfg["seed"], wcfg["tag"]
        raw, idx, proof = draw_world(loader, seed, tag, extra)
        extra[f"e17_{tag}"] = idx
        splits_cfg = dict(E17["splits"], seed=seed)
        raw_splits = get_raw_splits(REPO, raw, splits_cfg,
                                    experiment_tag=f"E17{tag}")
        d0 = build_environment_dataset(raw, Environment())
        frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
                  for r, ids in raw_splits.items()}
        log(f"partition sizes: { {r: len(v) for r, v in frames.items()} }")
        models, _df_a = train_frozen_world(frames, tier_a_seed=seed)
        worlds_out[tag] = run_world(raw, raw_splits, frames, models, loader,
                                    seed)
        proofs[tag] = proof
        log(f"world {tag} complete")

    prior = prior_world_values()
    between = between_world_analysis(worlds_out, prior)
    acceptance = evaluate_falsifiers(worlds_out, between)

    out = {
        "experiment": "E17",
        "declared_status": "post-development confirmatory evidence "
                           "(protocol frozen before draws; D-028)",
        "disjointness_proofs": proofs,
        "frozen_source": E17["frozen_source"],
        "worlds": worlds_out,
        "between_world": between,
        "acceptance": acceptance,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E17_worlds.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E17", config={"E17": E17, "frozen": FROZEN},
        seed=E17["worlds"][0]["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet":
                        checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E17 complete in {out['wall_seconds']} s -> {out_path}")
    log("ACCEPTANCE: " + json.dumps(
        {k: v.get("pass", v.get("verdict")) if isinstance(v, dict) else v
         for k, v in acceptance.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
