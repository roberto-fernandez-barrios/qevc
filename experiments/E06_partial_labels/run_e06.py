"""E06 — Partial-label certification landscape (spec §14, §28; H3).

Estimates n*(θ, C) — the label budget at which each claim leaves UNRESOLVED —
across the full environment grid and predeclared claim family, with streams
extended to n_max = 20,000. A claim resolved at n* stays resolved (running-
intersection CS bounds are monotone), so the landscape over budgets is the
survival curve of n*.

Inputs are all archived artifacts: E02 per-env scores, E05 frozen thresholds
and source accuracies. Outputs: results/tables/E06_nstar.json (Fig. 5 data).
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
E06 = yaml.safe_load((REPO / "configs/experiments/E06.yaml").read_text())
E05_RESULTS = json.loads((REPO / "results/tables/E05_auditor.json").read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def stream_seed(env: str, model: str, s: int) -> int:
    digest = hashlib.sha256(f"{E06['seed_salt']}|{env}|{model}|{s}".encode()).digest()
    return int.from_bytes(digest[:8], "little")


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    labels_raw = raw["labels"].to_numpy().astype(int)
    frozen = E05_RESULTS["frozen"]
    from qevc.systematics.fair_universe import Environment  # noqa: PLC0415

    deltas, budgets = E06["deltas"], E06["budgets"]
    alpha, n_max, n_seeds = E06["alpha"], E06["n_max"], E06["audit_seeds"]
    env_list = [("nominal", Environment())] + environments()

    out_envs: dict = {}
    for env_name, env in env_list:
        npz = np.load(env_filename(env_name))
        y_env = labels_raw[npz["row_id"]]
        out_envs[env_name] = {"theta": env.to_dict(), "models": {}}
        for key in E06["models"]:
            thr, m_s = frozen[key]["thr"], frozen[key]["m_source"]
            correct = ((npz[key] >= thr).astype(int) == y_env).astype(float)
            m_t = float(correct.mean())
            claims_out: dict = {}
            # One CS per seed resolves every delta simultaneously.
            per_seed_cs = []
            for s in range(n_seeds):
                rng = np.random.default_rng(stream_seed(env_name, key, s))
                x = correct[rng.integers(0, len(correct), size=n_max)]
                per_seed_cs.append(empirical_bernstein_cs(x, alpha=alpha))
            for d in deltas:
                tau = m_s - d
                n_stars, final_verdicts = [], {"SUPPORTED": 0, "REFUTED": 0,
                                               "UNRESOLVED": 0}
                for cs in per_seed_cs:
                    res = resolve_claim(Claim("acc", tau), cs)
                    final_verdicts[res.verdict.value] += 1
                    n_stars.append(res.n_star if res.n_star is not None else np.inf)
                n_stars = np.array(n_stars, dtype=float)
                claims_out[str(d)] = {
                    "tau": round(tau, 5),
                    "truth": bool(m_t >= tau),
                    "margin": round(m_t - tau, 5),
                    "final_verdicts": final_verdicts,
                    "resolved_frac_at_budget": {
                        str(b): round(float((n_stars <= b).mean()), 3)
                        for b in budgets
                    },
                    # Nearest-rank quantiles: interpolation between finite and
                    # inf (unresolved) values would produce NaN.
                    "n_star_quantiles": {
                        name: (None if not np.isfinite(v) else int(v))
                        for name, v in zip(
                            ("q25", "q50", "q75"),
                            np.sort(n_stars)[
                                [int(q * (len(n_stars) - 1)) for q in (0.25, 0.5, 0.75)]
                            ],
                        )
                    },
                }
            out_envs[env_name]["models"][key] = {
                "m_target": round(m_t, 5), "claims": claims_out}
        log(f"{env_name}: done")

    out = {
        "experiment": "E06",
        "alpha": alpha, "n_max": n_max, "audit_seeds": n_seeds,
        "frozen": frozen,
        "environments": out_envs,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E06_nstar.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E06", config={"E01": E01, "E06": E06}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E06 complete in {out['wall_seconds']} s -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
