"""Tests for the I3 rate/control-region machinery (E14; D-024)."""

import numpy as np
import pytest

from qevc.auditing.claims import Verdict
from qevc.auditing.rates import (
    fit_norm_scales,
    garwood_poisson_ci,
    resolve_rate_claim,
    worst_case_weighted_verdict,
)

RNG = np.random.default_rng(20260813)


def test_garwood_basics_and_coverage():
    lo, hi = garwood_poisson_ci(0)
    assert lo == 0.0 and hi > 0
    lo, hi = garwood_poisson_ci(100)
    assert lo < 100 < hi
    # MC coverage at lambda = 50
    miss = 0
    for r in range(400):
        n = np.random.default_rng(r).poisson(50)
        lo, hi = garwood_poisson_ci(int(n), alpha=0.05)
        if not (lo <= 50 <= hi):
            miss += 1
    assert miss / 400 <= 0.05 + 3 * np.sqrt(0.05 * 0.95 / 400)


def _cr_setup():
    """Two CRs: ttbar-enriched and everything-else."""
    lam_sig = np.array([2.0, 40.0])
    lam_ttbar = np.array([900.0, 400.0])
    lam_diboson = np.array([5.0, 60.0])
    lam_other = np.array([300.0, 30000.0])
    return lam_sig, lam_ttbar, lam_diboson, lam_other


def test_fit_norm_scales_recovers_truth():
    lam_sig, lam_tt, lam_db, lam_oth = _cr_setup()
    s_tt_true, s_bkg_true = 1.04, 1.002
    lam = lam_sig + s_bkg_true * (s_tt_true * lam_tt + 1.0 * lam_db + lam_oth)
    hits_tt = hits_bkg = 0
    n_rep = 60
    for r in range(n_rep):
        counts = np.random.default_rng(100 + r).poisson(lam)
        fit = fit_norm_scales(counts, lam_sig, lam_tt, lam_db, lam_oth,
                              alpha=0.05)
        if fit["ci_tt"][0] <= s_tt_true <= fit["ci_tt"][1]:
            hits_tt += 1
        if fit["ci_bkg"][0] <= s_bkg_true <= fit["ci_bkg"][1]:
            hits_bkg += 1
    # PLR CIs should cover at roughly >= 1 - alpha (diboson profiling makes
    # them conservative); allow MC slack downward
    assert hits_tt / n_rep >= 0.85, hits_tt / n_rep
    assert hits_bkg / n_rep >= 0.85, hits_bkg / n_rep


def test_resolve_rate_claim_verdicts():
    assert resolve_rate_claim((0.97, 1.03), (0.9, 1.1)) is Verdict.SUPPORTED
    assert resolve_rate_claim((1.2, 1.4), (0.9, 1.1)) is Verdict.REFUTED
    assert resolve_rate_claim((1.05, 1.15), (0.9, 1.1)) is Verdict.UNRESOLVED


def _stream(n=6000):
    w0 = RNG.choice([0.05, 1.0, 4.0], size=n, p=[0.3, 0.4, 0.3])
    is_tt = RNG.random(n) < 0.1
    is_db = (~is_tt) & (RNG.random(n) < 0.05)
    is_bkg = RNG.random(n) < 0.7          # bkg_scale applies to background
    c = (RNG.random(n) < 0.85).astype(float)
    return c, w0, is_tt, is_db, is_bkg


def test_worst_case_point_box_matches_plain_weighted():
    c, w0, is_tt, is_db, is_bkg = _stream()
    boxes = {"ttbar": (1.0, 1.0), "diboson": (1.0, 1.0), "bkg": (1.0, 1.0)}
    res = worst_case_weighted_verdict(c, w0, is_tt, is_db, is_bkg,
                                      tau=0.7, w_max=10.0, s_boxes=boxes)
    assert res["verdict"] is Verdict.SUPPORTED
    assert len(set(res["corner_verdicts"])) == 1


def test_worst_case_wide_box_abstains_near_boundary():
    c, w0, is_tt, is_db, is_bkg = _stream()
    a_w = float((w0 * c).sum() / w0.sum())
    boxes = {"ttbar": (0.8, 1.2), "diboson": (0.0, 2.0), "bkg": (0.99, 1.01)}
    res = worst_case_weighted_verdict(c, w0, is_tt, is_db, is_bkg,
                                      tau=round(a_w, 3), w_max=10.0,
                                      s_boxes=boxes)
    assert res["verdict"] is Verdict.UNRESOLVED


def test_worst_case_comfortable_margin_supported():
    c, w0, is_tt, is_db, is_bkg = _stream(n=12000)
    boxes = {"ttbar": (0.96, 1.04), "diboson": (0.5, 1.5), "bkg": (0.998, 1.002)}
    res = worst_case_weighted_verdict(c, w0, is_tt, is_db, is_bkg,
                                      tau=0.6, w_max=10.0, s_boxes=boxes)
    assert res["verdict"] is Verdict.SUPPORTED
