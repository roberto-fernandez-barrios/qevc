"""Tests for the E15 profile-likelihood machinery (D-023).

Validity properties: morphing reproduces its anchors exactly and is the
identity at alpha = 0; normalization nuisances act exactly (no interpolation
error); the fit recovers mu on well-specified synthetic data with ~nominal
interval coverage; profiling a real shape nuisance restores an unbiased fit
where the mis-specified model is biased.
"""

import numpy as np
import pytest

from qevc.inference.profile_likelihood import (
    ProfileLikelihood,
    TemplateSet,
    score_bin_edges,
)

RNG = np.random.default_rng(20260812)


def make_templates(n_bins=8, s_tot=60.0, b_tot=3000.0, with_tes=False):
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    t = TemplateSet(edges=edges, processes=["htautau", "ztautau"],
                    signal_processes=("htautau",))
    x = np.linspace(0.05, 0.95, n_bins)
    sig = x**2
    bkg = (1.0 - x) ** 1.5
    t.nominal["htautau"] = s_tot * sig / sig.sum()
    t.nominal["ztautau"] = b_tot * bkg / bkg.sum()
    if with_tes:
        # a +-1/-+2 sigma family: background shape tilts with alpha
        t.shape_anchors["tes"] = {}
        for a in (-2.0, -1.0, 1.0, 2.0):
            tilt = 1.0 + 0.06 * a * (x - x.mean())
            b = b_tot * (bkg * tilt) / (bkg * tilt).sum()
            s = t.nominal["htautau"] * (1.0 + 0.01 * a)
            t.shape_anchors["tes"][a] = {"htautau": s, "ztautau": b}
    return t


def test_morphing_identity_and_anchors():
    t = make_templates(with_tes=True)
    lam0 = t.expected(1.0, {"tes": 0.0}, {})
    np.testing.assert_allclose(
        lam0, t.nominal["htautau"] + t.nominal["ztautau"], rtol=1e-9)
    for a in (-2.0, -1.0, 1.0, 2.0):
        lam = t.expected(1.0, {"tes": a}, {})
        expect = (t.shape_anchors["tes"][a]["htautau"]
                  + t.shape_anchors["tes"][a]["ztautau"])
        np.testing.assert_allclose(lam, expect, rtol=1e-9)


def test_norm_nuisances_exact():
    edges = np.linspace(0, 1, 5)
    t = TemplateSet(edges=edges, processes=["htautau", "ttbar", "diboson"])
    t.nominal["htautau"] = np.array([1.0, 2, 3, 4])
    t.nominal["ttbar"] = np.array([10.0, 10, 10, 10])
    t.nominal["diboson"] = np.array([2.0, 2, 2, 2])
    lam = t.expected(1.0, {}, {"ttbar_scale": 1.1, "diboson_scale": 0.5,
                               "bkg_scale": 1.002})
    expect = (t.nominal["htautau"] + 1.1 * 1.002 * t.nominal["ttbar"]
              + 0.5 * 1.002 * t.nominal["diboson"])
    np.testing.assert_allclose(lam, expect, rtol=1e-12)


def test_fit_recovers_mu_and_coverage():
    t = make_templates()
    pl = ProfileLikelihood(t, profile_shapes=[], profile_norms=["bkg_scale"])
    lam_true = t.expected(1.0, {}, {})
    mu_hats, cover = [], 0
    n_pe = 120
    for r in range(n_pe):
        n_obs = RNG.poisson(lam_true)
        res = pl.fit(n_obs)
        mu_hats.append(res.mu_hat)
        lo, hi = res.interval
        if lo <= 1.0 <= hi:
            cover += 1
    bias = float(np.mean(mu_hats)) - 1.0
    assert abs(bias) < 0.15, bias
    assert 0.53 <= cover / n_pe <= 0.83, cover / n_pe  # ~0.6827 +- MC slack


def test_profiling_restores_validity_under_shape_shift():
    """Truth at tes = +1.5 sigma: the no-tes model is biased; profiling tes
    removes most of the bias."""
    t = make_templates(with_tes=True)
    lam_true = t.expected(1.0, {"tes": 1.5}, {})
    fits_none, fits_tes = [], []
    for r in range(60):
        n_obs = RNG.poisson(lam_true)
        pl0 = ProfileLikelihood(t, profile_shapes=[], profile_norms=[])
        pl1 = ProfileLikelihood(t, profile_shapes=["tes"], profile_norms=[])
        fits_none.append(pl0.fit(n_obs).mu_hat)
        fits_tes.append(pl1.fit(n_obs).mu_hat)
    bias_none = abs(np.mean(fits_none) - 1.0)
    bias_tes = abs(np.mean(fits_tes) - 1.0)
    assert bias_tes < bias_none, (bias_none, bias_tes)
    assert bias_tes < 0.35


def test_score_bin_edges_floor():
    p = RNG.random(20000)
    w = np.full(20000, 0.5)
    y = (RNG.random(20000) < 0.1).astype(int)
    edges = score_bin_edges(p, w, y, n_bins=10, b_floor=100.0)
    b_yield, _ = np.histogram(p[y == 0], bins=edges, weights=w[y == 0])
    assert np.all(b_yield >= 100.0)
    assert edges[0] == 0.0 and edges[-1] == 1.0
