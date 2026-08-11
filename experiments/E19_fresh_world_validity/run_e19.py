"""E19 — Fresh-world validity replication on archived E12 scores (registry E19).

Reconstructs the E12 world deterministically (cached subset + persisted split,
indices verified against the D-020 archives), re-derives the frozen deployment
with E12's own training protocol, CERTIFIES the archived score files by exact
float32 comparison on two environments, then replicates:

  (i)  the E05 v1.1 unweighted auditor protocol      (salt "E19",  n_max 3000)
  (ii) the E13 Part-B weighted benchmark, identical draws (same streams)
  (iii) an E06-style n* landscape                    (salt "E19L", n_max 20000)

over the 41 archived environments × 4 audit models. Scores come from
results/raw/E12_scores/ (archived outputs of the frozen deployment — reuse
declared in D-028 rule 5). I1 veto accounting follows E12's corrected arm-(d)
pattern: primary rate on non-vetoed false-claim streams, all-streams reported.

Falsifier (frozen in the registry): false certification > alpha + 3*sigma
binomial in either estimand family (non-vetoed denominators).

Outputs: results/tables/E19_fresh_world_validity.json + manifest.
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
sys.path.insert(0, str(REPO / "experiments/E12_confirmatory"))

from qevc.auditing.claims import Claim, Verdict, resolve_claim  # noqa: E402
from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
)
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.statistics.weighted import (  # noqa: E402
    resolve_weighted_claim,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

import run_e12  # noqa: E402  (E12 config, frozen grid, training protocol)

E19 = yaml.safe_load((REPO / "configs/experiments/E19.yaml").read_text())
E13 = yaml.safe_load((REPO / E19["weighted"]["source_config"]).read_text())
E12CFG = run_e12.E12
FROZEN = run_e12.FROZEN
SCORES_DIR = REPO / E19["scores_dir"]
USED_ROWS = REPO / "data/processed/used_rows"
ALPHA = E19["alpha"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def npz_name(env_name: str) -> str:
    return env_name.replace("/", "_").replace("=", "_") + ".npz"


def stream_rng(salt: str, env: str, model: str, seed: int):
    digest = hashlib.sha256(f"{salt}|{env}|{model}|{seed}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def reconstruct_world(loader: FairUniverseLoader):
    """E12 subset + persisted split, verified against the D-020 archives."""
    idx101 = np.load(USED_ROWS / "seed101_subset_n300000_indices.npy")
    e00 = np.load(USED_ROWS / "e00_validation_rowgroup_indices.npy")
    exclusion = np.union1d(idx101, e00)
    sub = loader.load_subset(E12CFG["subset"]["n_total"],
                             E12CFG["subset"]["seed"],
                             renormalize=True, exclude=exclusion,
                             tag=E12CFG["subset"]["tag"])
    n, s = E12CFG["subset"]["n_total"], E12CFG["subset"]["seed"]
    idx = np.load(loader.cache_dir / "subsets" /
                  f"subset_n{n}_seed{s}_renorm_{E12CFG['subset']['tag']}"
                  ".indices.npy")
    archived = np.load(USED_ROWS / "e12_subset_n300000_seed121_indices.npy")
    if not np.array_equal(np.sort(idx), np.sort(archived)):
        raise RuntimeError("E12 subset reconstruction != archived indices")
    log("E12 world reconstructed; indices match the D-020 archive")
    splits = get_raw_splits(REPO, sub, E12CFG["splits"], experiment_tag="E12")
    return sub, splits


def certify_archives(raw, test_ids, labels_raw, models) -> dict:
    """Exact float32 re-scoring check on two environments; abort on mismatch."""
    check_envs = [("nominal", Environment()),
                  ("tes=0.98", Environment(tes=0.98))]
    report = {}
    for env_name, env in check_envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(SCORES_DIR / npz_name(env_name))
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row_id mismatch in {env_name}")
        for key, (model, cal, _thr, cols, _ms) in models.items():
            if key not in npz:
                continue
            p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
            same = np.array_equal(p.astype(np.float32), npz[key])
            report[f"{env_name}|{key}"] = bool(same)
            if not same:
                raise RuntimeError(
                    f"archived scores NOT reproduced: {env_name}/{key}")
        log(f"archive certified byte-identical: {env_name}")
    return report


def main() -> int:
    t0 = time.time()
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")
    raw, raw_splits = reconstruct_world(loader)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    labels_raw = raw["labels"].to_numpy().astype(int)
    test_ids = raw_splits["nominal_test"]

    models, _df_a = run_e12.train_frozen(frames)  # E12's own protocol/config
    cert = certify_archives(raw, test_ids, labels_raw, models)

    # references and w_max (E13 rule applied to this world, recorded)
    sv = frames["source_val"]
    y_sv, w_sv = sv["labels"].to_numpy(), sv["weights"].to_numpy()
    base_wmax = float(np.max(d0["weights"].to_numpy()))
    w_max = base_wmax * float(E13["w_max"]["kappa_norm"])
    refs = {}
    for key, (model, cal, thr, cols, m_s_unw) in models.items():
        p_sv = cal.predict_proba(model.scores(sv[cols].to_numpy(float)))
        c_sv = ((p_sv >= thr).astype(int) == y_sv).astype(float)
        refs[key] = {"m_s_unw": m_s_unw,
                     "m_s_w": float(np.sum(w_sv * c_sv) / np.sum(w_sv))}
        log(f"refs {key}: M_S_unw {m_s_unw:.5f}  M_S_w {refs[key]['m_s_w']:.5f}")

    e12_table = json.loads(
        (REPO / "results/tables/E12_confirmatory.json").read_text())
    alarms = set(e12_table["geometry"]["i1_alarm_envs"]["quantum"])

    deltas = FROZEN["claims"]["deltas"]
    n_max_aud = E19["auditor"]["n_max"]
    n_seeds = E19["auditor"]["audit_seeds"]
    audit_models = E19["auditor"]["models"]

    err = {
        "unw": {"fc": 0, "fr": 0, "false_all": 0, "true_all": 0,
                "fc_nonveto": 0, "false_nonveto": 0},
        "w": {"fc": 0, "fr": 0, "false_all": 0, "true_all": 0},
    }
    landscape_cells = []
    per_env: dict = {}
    envs = [("nominal", Environment())] + run_e12.environments()
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(SCORES_DIR / npz_name(env_name))
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row_id mismatch in {env_name}")
        y = labels_raw[te["row_id"].to_numpy()]
        w = te["weights"].to_numpy()
        if float(np.max(w)) > w_max:
            raise RuntimeError(f"w_max violated in {env_name}")
        alarm = env_name in alarms
        per_env[env_name] = {"i1_alarm": bool(alarm), "models": {}}
        for key in audit_models:
            _m, _c, thr, _cols, _ms = models[key]
            p = npz[key]
            correct = ((p >= thr).astype(int) == y).astype(float)
            m_t_unw = float(correct.mean())
            m_t_w = float(np.sum(w * correct) / np.sum(w))
            cell: dict = {"m_t_unw": round(m_t_unw, 5),
                          "m_t_w": round(m_t_w, 5), "claims": {}}
            for d in deltas:
                tau_u = refs[key]["m_s_unw"] - d
                tau_w = refs[key]["m_s_w"] - d
                truth_u = m_t_unw >= tau_u
                truth_w = m_t_w >= tau_w
                v_u = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                v_w = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                for s in range(n_seeds):
                    rng = stream_rng(E19["auditor"]["seed_salt"],
                                     env_name, key, s)
                    ix = rng.integers(0, len(correct), size=n_max_aud)
                    c_s, w_s = correct[ix], w[ix]
                    cs = empirical_bernstein_cs(c_s, alpha=ALPHA)
                    r_u = resolve_claim(Claim("acc", min(max(tau_u, 0), 1)),
                                        cs, heuristic_alarm=alarm)
                    v_u[r_u.verdict.value] += 1
                    r_w = resolve_weighted_claim(
                        c_s, w_s, min(max(tau_w, 0), 1), w_max, alpha=ALPHA,
                        heuristic_alarm=False)
                    v_w[r_w.verdict.value] += 1
                    if not truth_u:
                        err["unw"]["false_all"] += 1
                        if r_u.verdict is Verdict.SUPPORTED:
                            err["unw"]["fc"] += 1
                        if not alarm:
                            err["unw"]["false_nonveto"] += 1
                            if r_u.verdict is Verdict.SUPPORTED:
                                err["unw"]["fc_nonveto"] += 1
                    else:
                        err["unw"]["true_all"] += 1
                        if r_u.verdict is Verdict.REFUTED:
                            err["unw"]["fr"] += 1
                    if not truth_w:
                        err["w"]["false_all"] += 1
                        if r_w.verdict is Verdict.SUPPORTED:
                            err["w"]["fc"] += 1
                    else:
                        err["w"]["true_all"] += 1
                        if r_w.verdict is Verdict.REFUTED:
                            err["w"]["fr"] += 1
                cell["claims"][str(d)] = {
                    "truth_unw": bool(truth_u), "truth_w": bool(truth_w),
                    "margin_unw": round(m_t_unw - tau_u, 5),
                    "margin_w": round(m_t_w - tau_w, 5),
                    "verdicts_unw": v_u, "verdicts_w": v_w,
                }
            per_env[env_name]["models"][key] = cell

            # landscape arm (n* at 20k, unweighted, salt E19L)
            for d in deltas:
                tau_u = refs[key]["m_s_unw"] - d
                n_stars = []
                for s in range(E19["landscape"]["audit_seeds"]):
                    rng = stream_rng(E19["landscape"]["seed_salt"],
                                     env_name, key, s)
                    ix = rng.integers(0, len(correct),
                                      size=E19["landscape"]["n_max"])
                    cs = empirical_bernstein_cs(correct[ix], alpha=ALPHA)
                    res = resolve_claim(Claim("acc", min(max(tau_u, 0), 1)),
                                        cs, heuristic_alarm=False)
                    if res.n_star is not None:
                        n_stars.append(res.n_star)
                landscape_cells.append({
                    "env": env_name, "model": key, "delta": d,
                    "margin": round(m_t_unw - tau_u, 5),
                    "resolved_frac": round(
                        len(n_stars) / E19["landscape"]["audit_seeds"], 3),
                    "n_star_q50": (int(np.median(n_stars))
                                   if n_stars else None),
                })
        log(f"audited {env_name}")

    def rate(num, den):
        return round(num / den, 5) if den else None

    n_false_nv = err["unw"]["false_nonveto"]
    n_false_w = err["w"]["false_all"]
    slack_u = (ALPHA + 3 * np.sqrt(ALPHA * (1 - ALPHA) / n_false_nv)
               if n_false_nv else None)
    slack_w = (ALPHA + 3 * np.sqrt(ALPHA * (1 - ALPHA) / n_false_w)
               if n_false_w else None)
    fc_u = rate(err["unw"]["fc_nonveto"], n_false_nv)
    fc_w = rate(err["w"]["fc"], n_false_w)

    error_rates = {
        "alpha": ALPHA,
        "unweighted": {
            "false_cert_nonvetoed": fc_u,
            "counts_nonvetoed": [err["unw"]["fc_nonveto"], n_false_nv],
            "false_cert_all_streams": rate(err["unw"]["fc"],
                                           err["unw"]["false_all"]),
            "counts_all": [err["unw"]["fc"], err["unw"]["false_all"]],
            "false_refutation": rate(err["unw"]["fr"], err["unw"]["true_all"]),
            "threshold_alpha_plus_3sigma": (round(slack_u, 5)
                                            if slack_u else None),
        },
        "weighted": {
            "false_cert": fc_w,
            "counts": [err["w"]["fc"], n_false_w],
            "false_refutation": rate(err["w"]["fr"], err["w"]["true_all"]),
            "threshold_alpha_plus_3sigma": (round(slack_w, 5)
                                            if slack_w else None),
        },
    }
    falsifier = {
        "unweighted_pass": bool(fc_u is not None and slack_u is not None
                                and fc_u <= slack_u),
        "weighted_pass": bool(fc_w is not None and slack_w is not None
                              and fc_w <= slack_w),
    }
    falsifier["pass"] = falsifier["unweighted_pass"] and falsifier[
        "weighted_pass"]

    comparison = {
        "E05_false_cert": "48/7820 = 0.61%",
        "E12_false_cert_nonvetoed": "21/3060 = 0.69%",
        "E13_weighted_false_cert": "2/8580 = 0.02%",
        "E19_unweighted_nonvetoed": f"{err['unw']['fc_nonveto']}/{n_false_nv}",
        "E19_weighted": f"{err['w']['fc']}/{n_false_w}",
    }

    out = {
        "experiment": "E19",
        "declared_status": "validity replication on archived fresh-world "
                           "scores (D-028 rule 5)",
        "archive_certification": cert,
        "w_max": {"base_max_weight": round(base_wmax, 5),
                  "kappa_norm": E13["w_max"]["kappa_norm"],
                  "w_max": round(w_max, 5)},
        "references": {k: {kk: round(vv, 6) for kk, vv in v.items()}
                       for k, v in refs.items()},
        "error_rates": error_rates,
        "falsifier": falsifier,
        "comparison_rows": comparison,
        "landscape_cells": landscape_cells,
        "environments": per_env,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E19_fresh_world_validity.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E19", config={"E19": E19, "E13_wmax": E13["w_max"]},
        seed=E12CFG["subset"]["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet":
                        checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E19 complete in {out['wall_seconds']} s -> {out_path}")
    log(f"FALSIFIER: {json.dumps(falsifier)}  "
        f"unw {comparison['E19_unweighted_nonvetoed']}  "
        f"w {comparison['E19_weighted']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
