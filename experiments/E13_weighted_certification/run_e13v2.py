"""E13v2 — BA_w pre-split component allocation (registry E13v2; spec §4c).

Re-runs ONLY the BA_w block of the E13 validation battery with the
pre-split allocation frozen in docs/weighted_certification_spec.md §4c
(derived before this file was written): predeclared component thresholds
(τ₁+τ₂)/2 = τ_BA, α/2 per component, sharp §3.1 one-sample reduction per
component, per-class predeclared bounds (κ_sig = 1.0, κ_norm = 2.05).

Populations (frozen): P1 synthetic_v1 (v1 BA-block construction — the
attribution control: weights class-independent) and P2 benchmark_class
(seed-101 subset (y, w) rows — physics class-weight correlation).
Claims: τ_BA = BA_w ± m, m ∈ {0.02, 0.05}; n_max = 5,000; n_rep = 200;
salt "E13V2". Comparison arm: v1 resolve_ba_claim on identical draws.

Falsifiers (frozen, D-028): (a) any cell false-cert > α + 3σ → the
allocation is invalid and blocked; (b) ALL true BA_w claims UNRESOLVED
on the physics population → measured impossibility, published as such.

Outputs: results/tables/E13v2_baw_allocation.json + manifest.
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

from qevc.pipeline.common import load_raw_subset  # noqa: E402
from qevc.statistics.weighted import (  # noqa: E402
    effective_sample_size_ratio,
    resolve_ba_claim,
    resolve_ba_presplit,
    weighted_claim_stream,
)
from qevc.statistics.confidence_sequences import (  # noqa: E402
    empirical_bernstein_cs,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E13V2 = yaml.safe_load((REPO / "configs/experiments/E13v2.yaml").read_text())
E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stream_rng(*parts) -> np.random.Generator:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def make_populations(raw) -> dict:
    """The two frozen populations with exact component truths."""
    rates = E13V2["component_rates"]
    pops = {}

    # P1 — the v1 BA-block construction (run_e13.py part_a step 4):
    # y ~ Bern(0.3), weights drawn class-independently from the per-process
    # mean-weight constants, correctness class-conditional at the targets.
    bench_weights = raw.groupby("detailed_labels", observed=True)[
        "weights"].mean().to_numpy()
    rng0 = np.random.default_rng(77)
    n = 50000
    y1 = (rng0.random(n) < 0.3).astype(int)
    w1 = rng0.choice(bench_weights, size=n)
    c1 = (rng0.random(n) < np.where(y1 == 1, rates["tpr"],
                                    rates["tnr"])).astype(float)
    pops["synthetic_v1"] = (y1, w1, c1)

    # P2 — benchmark-faithful: the subset's actual (y, w) rows; correctness
    # synthesized class-conditionally at the same targets.
    y2 = raw["labels"].to_numpy().astype(int)
    w2 = raw["weights"].to_numpy().astype(float)
    rng2 = stream_rng(E13V2["seed_salt"], "P2-correctness")
    c2 = (rng2.random(len(y2)) < np.where(y2 == 1, rates["tpr"],
                                          rates["tnr"])).astype(float)
    pops["benchmark_class"] = (y2, w2, c2)
    return pops


def main() -> int:
    t0 = time.time()
    alpha = E13V2["alpha"]
    n_max = E13V2["n_max"]
    n_rep = E13V2["n_rep"]
    raw = load_raw_subset(REPO, E01["subset"])
    pops = make_populations(raw)

    out: dict = {
        "experiment": "E13v2",
        "declared_status": "BA_w pre-split component allocation battery "
                           "(spec 4c frozen before implementation; D-028 "
                           "falsifiers)",
        "config": {"alpha": alpha, "n_max": n_max, "n_rep": n_rep,
                   "margins": E13V2["margins"],
                   "kappa_sig": E13V2["kappa_sig"],
                   "kappa_norm": E13V2["kappa_norm"]},
        "populations": {},
    }

    slack = alpha + 3 * float(np.sqrt(alpha * (1 - alpha) / n_rep))
    any_validity_fail = False
    physics_true_resolved = 0

    for pop_name in E13V2["populations"]:
        y, w, c = pops[pop_name]
        tpr = float((w * c * (y == 1)).sum() / (w * (y == 1)).sum())
        tnr = float((w * c * (y == 0)).sum() / (w * (y == 0)).sum())
        ba = (tpr + tnr) / 2.0
        w_max_pos = float(w[y == 1].max()) * E13V2["kappa_sig"]
        w_max_neg = float(w[y == 0].max()) * E13V2["kappa_norm"]
        w_max_v1 = float(w.max()) * 1.001   # v1 battery convention
        u_pos = w * (y == 1)
        u_neg = w * (y == 0)
        pop_out = {
            "truth": {"tpr_w": round(tpr, 5), "tnr_w": round(tnr, 5),
                      "ba_w": round(ba, 5)},
            "bounds": {"w_max_pos": round(w_max_pos, 5),
                       "w_max_neg": round(w_max_neg, 5),
                       "w_max_v1_global": round(w_max_v1, 5),
                       "sharpening_factor_pos":
                           round(w_max_v1 / w_max_pos, 4)},
            "class_structure": {
                "weighted_signal_fraction":
                    round(float(u_pos.sum() / w.sum()), 6),
                "ess_ratio_pos":
                    round(effective_sample_size_ratio(u_pos), 6),
                "ess_ratio_neg":
                    round(effective_sample_size_ratio(u_neg), 6)},
            "z_margin_diagnostics": {},
            "cells": {},
        }
        # exact Z-scale margins per component and margin (spec 4c limit)
        eu_pos = float(u_pos.mean())
        eu_neg = float(u_neg.mean())
        for m in E13V2["margins"]:
            pop_out["z_margin_diagnostics"][str(m)] = {
                "tpr_z_margin": round(eu_pos * m / w_max_pos, 8),
                "tnr_z_margin": round(eu_neg * m / w_max_neg, 8)}

        for m in E13V2["margins"]:
            for sign, label in ((-1, "true"), (+1, "false")):
                tau1 = float(np.clip(tpr + sign * m, 0.0, 1.0))
                tau2 = float(np.clip(tnr + sign * m, 0.0, 1.0))
                tau_ba = (tau1 + tau2) / 2.0
                truth = ba >= tau_ba
                v2_counts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                comp_counts = {"tpr": dict(v2_counts), "tnr": dict(v2_counts)}
                v1_counts = dict(v2_counts)
                n_stars = []
                for r in range(n_rep):
                    rng = stream_rng(E13V2["seed_salt"], pop_name, m,
                                     sign, r)
                    idx = rng.integers(0, len(y), size=n_max)
                    res, rp, rn = resolve_ba_presplit(
                        c[idx], y[idx], w[idx], tau1, tau2,
                        w_max_pos, w_max_neg, alpha=alpha)
                    v2_counts[res.verdict.value] += 1
                    comp_counts["tpr"][rp.verdict.value] += 1
                    comp_counts["tnr"][rn.verdict.value] += 1
                    if res.n_star is not None:
                        n_stars.append(res.n_star)
                    r1 = resolve_ba_claim(c[idx], y[idx], w[idx], tau_ba,
                                          w_max_v1, alpha=alpha)
                    v1_counts[r1.verdict.value] += 1
                cell = {
                    "tau_ba": round(tau_ba, 5), "truth": bool(truth),
                    "presplit_verdicts": v2_counts,
                    "component_verdicts": comp_counts,
                    "v1_component_bound_verdicts": v1_counts,
                    "n_star_median": (int(np.median(n_stars))
                                      if n_stars else None),
                }
                if not truth:
                    fc = v2_counts["SUPPORTED"] / n_rep
                    cell["false_cert_rate"] = fc
                    cell["validity_pass"] = bool(fc <= slack)
                    any_validity_fail |= not cell["validity_pass"]
                else:
                    cell["resolution_rate"] = (
                        v2_counts["SUPPORTED"] + v2_counts["REFUTED"]
                    ) / n_rep
                    if pop_name == "benchmark_class":
                        physics_true_resolved += (v2_counts["SUPPORTED"]
                                                  + v2_counts["REFUTED"])
                pop_out["cells"][f"m{m:+}|{label}"] = cell
                log(f"{pop_name} m={m} {label}: v2 {v2_counts}  "
                    f"v1 {v1_counts}")

        # radius diagnostic on one representative stream (rep 0, true, m=.02)
        rng = stream_rng(E13V2["seed_salt"], pop_name, 0.02, -1, 0)
        idx = rng.integers(0, len(y), size=n_max)
        z1 = weighted_claim_stream(c[idx], u_pos[idx],
                                   float(np.clip(tpr - 0.02, 0, 1)),
                                   w_max_pos)
        z0 = weighted_claim_stream(c[idx], u_neg[idx],
                                   float(np.clip(tnr - 0.02, 0, 1)),
                                   w_max_neg)
        rad = {}
        for name, z in (("tpr", z1), ("tnr", z0)):
            cs = empirical_bernstein_cs(z, alpha=alpha / 2)
            ri = cs.running_intersection()
            rad[name] = round(float((ri.upper[-1] - ri.lower[-1]) / 2), 6)
        r1 = resolve_ba_claim(c[idx], y[idx], w[idx],
                              float(np.clip(ba - 0.02, 0, 1)),
                              float(w.max()) * 1.001, alpha=alpha)
        rad["v1_ba_radius_ba_units"] = round((r1.upper - r1.lower) / 2, 6)
        pop_out["radius_at_nmax"] = rad
        out["populations"][pop_name] = pop_out

    n_true_cells_physics = len(E13V2["margins"])  # true cells on P2
    out["acceptance"] = {
        "a_validity": {"pass": bool(not any_validity_fail),
                       "slack": round(slack, 5)},
        "b_physics_resolution": {
            "true_claim_resolutions_benchmark_class": physics_true_resolved,
            "impossibility_branch": bool(physics_true_resolved == 0),
            "n_true_cells": n_true_cells_physics},
        "all_pass": bool(not any_validity_fail),
    }
    out["wall_seconds"] = round(time.time() - t0, 1)

    out_path = REPO / "results/tables/E13v2_baw_allocation.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E13v2", config={"E13v2": E13V2},
        seed=int.from_bytes(
            hashlib.sha256(E13V2["seed_salt"].encode()).digest()[:4],
            "little"),
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet":
                        checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E13v2 complete in {out['wall_seconds']} s -> {out_path}")
    log("ACCEPTANCE: " + json.dumps(out["acceptance"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
