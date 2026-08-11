"""E15 gate diagnosis (dev aid, not a results run): isolate the source of
the residual overcoverage on the REAL A:xgboost templates by comparing
profile configurations at nominal truth, mu_true = 1.

  (i)   full L2 (tes, jes, soft_met flat)  -> expect ~0.95 (reproduces gate)
  (ii)  L2 minus soft_met                  -> if ~0.68, soft_met profiling
                                              is the cause
  (iii) L2 with soft_met KEPT but at a fixed Gaussian aux sigma_sm = 1 GeV
        (boundary-truncated)               -> candidate registered fix
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import json  # noqa: E402

import yaml  # noqa: E402

from qevc.inference import profile_likelihood as plmod  # noqa: E402
from qevc.inference.profile_likelihood import (  # noqa: E402
    NORM_SIGMA,
    ProfileLikelihood,
)
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402

sys.path.insert(0, str(REPO / "experiments/E15_realistic_inference"))
from run_e15 import build_histogram_store, make_templates  # noqa: E402

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import train_frozen_models  # noqa: E402

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
KEY = "A:xgboost"
N_PE = 300
MU = 1.0


def one_pe(templates, shapes, norms, s_true, b_true, seed, sm_sigma):
    rng = np.random.default_rng(seed)
    n_obs = rng.poisson(MU * s_true + b_true)
    aux = {}
    for s in shapes:
        if s in ("tes", "jes"):
            aux[s] = float(rng.normal(0.0, 1.0))
    for nrm in norms:
        aux[nrm] = float(rng.normal(1.0, NORM_SIGMA[nrm]))
    if sm_sigma is not None and "soft_met" in shapes:
        aux["soft_met"] = max(0.0, float(rng.normal(0.0, sm_sigma)))
    pl = ProfileLikelihood(templates, shapes, norms)
    if sm_sigma is not None:
        # patch: add Gaussian soft_met constraint through a wrapper
        base_nll = pl.nll

        def nll_sm(x, n, a=None):
            val = base_nll(x, n, a)
            mu_, sh, _ = pl._unpack(x)
            a0 = 0.0 if a is None else float(a.get("soft_met", 0.0))
            val += 0.5 * ((sh.get("soft_met", 0.0) - a0) / sm_sigma) ** 2
            return val
        pl.nll = nll_sm
    res = pl.fit(n_obs, aux=aux)
    lo, hi = res.interval
    return (lo <= MU <= hi, hi - lo)


def main() -> int:
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
    t = make_templates(hists, edges, KEY)
    s_true = hists["nominal"][KEY]["htautau"].astype(float)
    b_true = sum(hists["nominal"][KEY][p].astype(float)
                 for p in ("ztautau", "ttbar", "diboson"))

    norms = ["ttbar_scale", "diboson_scale", "bkg_scale"]
    configs = {
        "i_full_L2": (["tes", "jes", "soft_met"], norms, None),
        "ii_no_softmet": (["tes", "jes"], norms, None),
        "iii_softmet_gauss1": (["tes", "jes", "soft_met"], norms, 1.0),
    }
    out = {}
    for name, (shapes, nrms, sm_sigma) in configs.items():
        res = Parallel(n_jobs=-1)(
            delayed(one_pe)(t, shapes, nrms, s_true, b_true, 5000 + r, sm_sigma)
            for r in range(N_PE))
        cov = float(np.mean([c for c, _ in res]))
        wid = float(np.mean([w for _, w in res]))
        out[name] = {"coverage": round(cov, 4), "width_mean": round(wid, 4)}
        print(name, out[name], flush=True)
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
