"""E07 — Active auditing (spec §15, §28).

Compares label-acquisition strategies for claim resolution:

- ``uniform``: IID uniform draws (E06 semantics, independent seeds).
- ``uncertainty_mix``: importance sampling from a mixture proposal
  q = mix·uniform + (1−mix)·closeness-to-threshold. Each draw contributes
  X_t = iw·1[correct] with iw = (1/N)/q_i ≤ 1/mix, so X/(1/mix) ∈ [0, 1] and
  the EB confidence sequence applies exactly to the rescaled stream
  (E_q[X] = M_T; claims resolved at τ·mix on the rescaled scale). Validity is
  preserved BY CONSTRUCTION — the question is purely whether variance drops
  enough to shrink n*.

If active acquisition does not beat uniform, that is the reported result
(spec §15). Outputs: results/tables/E07_active.json.
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
from qevc.pipeline.common import load_raw_subset  # noqa: E402
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E07 = yaml.safe_load((REPO / "configs/experiments/E07.yaml").read_text())
E05_RESULTS = json.loads((REPO / "results/tables/E05_auditor.json").read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def stream_seed(strategy: str, env: str, model: str, s: int) -> int:
    digest = hashlib.sha256(
        f"{E07['seed_salt']}|{strategy}|{env}|{model}|{s}".encode()).digest()
    return int.from_bytes(digest[:8], "little")


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    labels_raw = raw["labels"].to_numpy().astype(int)
    frozen = E05_RESULTS["frozen"]
    from qevc.systematics.fair_universe import Environment  # noqa: PLC0415

    deltas, budgets = E07["deltas"], E07["budgets"]
    alpha, n_max, n_seeds = E07["alpha"], E07["n_max"], E07["audit_seeds"]
    mix = E07["strategies"]["uncertainty_mix"]["mix"]
    eps_frac = E07["strategies"]["uncertainty_mix"]["eps_frac_of_median"]
    env_list = [("nominal", Environment())] + environments()

    err = {st: {"false_cert": 0, "claim_false": 0} for st in E07["strategies"]}
    out_envs: dict = {}
    for env_name, env in env_list:
        npz = np.load(env_filename(env_name))
        y_env = labels_raw[npz["row_id"]]
        out_envs[env_name] = {"models": {}}
        for key in E07["models"]:
            thr, m_s = frozen[key]["thr"], frozen[key]["m_source"]
            p = npz[key]
            correct = ((p >= thr).astype(int) == y_env).astype(float)
            m_t = float(correct.mean())
            n = len(correct)

            # Uncertainty-mixture proposal (predeclared rule).
            dist = np.abs(p - thr)
            eps = eps_frac * max(float(np.median(dist)), 1e-12)
            u = 1.0 / (dist + eps)
            q = mix / n + (1.0 - mix) * (u / u.sum())
            q /= q.sum()
            iw = (1.0 / n) / q          # importance weights, <= 1/mix
            iw_max = 1.0 / mix

            entry: dict = {"m_target": round(m_t, 5), "strategies": {}}
            for strategy in E07["strategies"]:
                claim_stats = {
                    str(d): {"n_stars": [], "verdicts":
                             {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}}
                    for d in deltas
                }
                for s in range(n_seeds):
                    rng = np.random.default_rng(stream_seed(strategy, env_name, key, s))
                    if strategy == "uniform":
                        x = correct[rng.integers(0, n, size=n_max)]
                        scale = 1.0
                    else:
                        idx = rng.choice(n, size=n_max, replace=True, p=q)
                        x = (iw[idx] * correct[idx]) / iw_max  # in [0, 1]
                        scale = 1.0 / iw_max                   # claims at tau*scale
                    cs = empirical_bernstein_cs(x, alpha=alpha)
                    for d in deltas:
                        tau = m_s - d
                        truth = m_t >= tau
                        res = resolve_claim(Claim("acc", tau * scale), cs)
                        st = claim_stats[str(d)]
                        st["verdicts"][res.verdict.value] += 1
                        st["n_stars"].append(
                            res.n_star if res.n_star is not None else np.inf)
                        if not truth:
                            err[strategy]["claim_false"] += 1
                            if res.verdict is Verdict.SUPPORTED:
                                err[strategy]["false_cert"] += 1
                entry["strategies"][strategy] = {
                    str(d): {
                        "verdicts": v["verdicts"],
                        "resolved_frac_at_budget": {
                            str(b): round(float(
                                (np.array(v["n_stars"]) <= b).mean()), 3)
                            for b in budgets
                        },
                        "n_star_q50": (
                            None if not np.isfinite(
                                med := np.sort(np.array(v["n_stars"]))[
                                    (len(v["n_stars"]) - 1) // 2])
                            else int(med)),
                    }
                    for d, v in claim_stats.items()
                }
            out_envs[env_name]["models"][key] = entry
        log(f"{env_name}: done")

    out = {
        "experiment": "E07",
        "alpha": alpha, "n_max": n_max, "audit_seeds": n_seeds,
        "error_rates": {
            st: {
                **c,
                "false_cert_rate": (round(c["false_cert"] / c["claim_false"], 5)
                                    if c["claim_false"] else None),
            }
            for st, c in err.items()
        },
        "environments": out_envs,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E07_active.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E07", config={"E01": E01, "E07": E07}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E07 complete in {out['wall_seconds']} s -> {out_path}")
    print(json.dumps(out["error_rates"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
