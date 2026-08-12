"""Validity tests for the weighted certification machinery (E13, D-019).

The load-bearing properties: (1) the one-sample reduction is EXACTLY the
unweighted stream when u ≡ 1 (strict generalization of D-014); (2) claim
equivalence R ≥ τ ⟺ E[Z(τ)] ≥ τ holds by arithmetic; (3) time-uniform
false-certification control on weighted claims, including heavy-tailed
weights; (4) the ratio CS covers the true ratio time-uniformly; (5) the CS
survives an adversarial stopping rule that breaks fixed-n intervals;
(6) the BA component bound is conservative, never anti-conservative.
"""

import numpy as np
import pytest

from qevc.auditing.claims import Verdict
from qevc.statistics.confidence_sequences import empirical_bernstein_cs
from qevc.statistics.weighted import (
    resolve_ba_presplit,
    effective_sample_size_ratio,
    resolve_ba_claim,
    resolve_weighted_claim,
    weighted_claim_stream,
    weighted_ratio_cs,
)

RNG = np.random.default_rng(20260811)


def _population(n=20000, profile="benchmark", acc_hi=0.9, acc_lo=0.6, seed=7):
    """Finite population with weights and correctness correlated with weight
    class, so A_w != unweighted accuracy and the weighted estimand is
    genuinely different."""
    rng = np.random.default_rng(seed)
    if profile == "uniform":
        w = np.ones(n)
    elif profile == "benchmark":  # few weight classes, ~30x spread
        w = rng.choice([0.03, 0.4, 1.0], size=n, p=[0.34, 0.03, 0.63])
    elif profile == "heavy":      # w_max / mean >= 20
        w = rng.choice([0.05, 5.0], size=n, p=[0.96, 0.04])
    else:
        raise ValueError(profile)
    # high-weight events are LESS often correct -> weighted acc < unweighted
    p_correct = np.where(w >= np.median(w), acc_lo, acc_hi)
    c = (rng.random(n) < p_correct).astype(float)
    a_w = float((w * c).sum() / w.sum())
    return c, w, a_w


def test_reduces_exactly_to_unweighted_stream():
    c = (RNG.random(500) < 0.8).astype(float)
    z = weighted_claim_stream(c, np.ones_like(c), tau=0.75, w_max=1.0)
    np.testing.assert_array_equal(z, c)
    cs_w = empirical_bernstein_cs(z)
    cs_u = empirical_bernstein_cs(c)
    np.testing.assert_array_equal(cs_w.lower, cs_u.lower)
    np.testing.assert_array_equal(cs_w.upper, cs_u.upper)


def test_claim_equivalence_arithmetic():
    c, w, a_w = _population(profile="benchmark")
    w_max = float(w.max())
    for tau in (a_w - 0.05, a_w, a_w + 0.05):
        z = weighted_claim_stream(c, w, tau=np.clip(tau, 0, 1), w_max=w_max)
        # population identity: mean Z >= tau  <=>  A_w >= tau
        assert (z.mean() >= tau) == (a_w >= tau - 1e-12)
        assert z.min() >= 0.0 and z.max() <= 1.0


def test_masked_draws_are_neutral():
    c = (RNG.random(300) < 0.7).astype(float)
    u = np.zeros(300)  # fully masked
    z = weighted_claim_stream(c, u, tau=0.4, w_max=2.0)
    np.testing.assert_allclose(z, 0.4)


def test_wmax_violation_raises():
    c = np.ones(10)
    u = np.full(10, 3.0)
    with pytest.raises(ValueError, match="w_max"):
        weighted_claim_stream(c, u, tau=0.5, w_max=2.0)


@pytest.mark.parametrize("profile", ["uniform", "benchmark", "heavy"])
def test_false_certification_controlled_weighted(profile):
    """Claims with margin -0.02 (genuinely false): SUPPORTED-at-any-time rate
    must stay <= alpha (+3-sigma MC slack)."""
    alpha, n_rep, n_stream = 0.05, 250, 1500
    c_pop, w_pop, a_w = _population(profile=profile)
    w_max = float(w_pop.max()) * 1.05
    tau = min(a_w + 0.02, 1.0)  # claim false by 0.02
    false_cert = 0
    for r in range(n_rep):
        rng = np.random.default_rng(1000 + r)
        idx = rng.integers(0, len(c_pop), size=n_stream)
        res = resolve_weighted_claim(c_pop[idx], w_pop[idx], tau, w_max,
                                     alpha=alpha)
        if res.verdict is Verdict.SUPPORTED:
            false_cert += 1
    rate = false_cert / n_rep
    assert rate <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep), rate


def test_true_claim_resolves_supported():
    c_pop, w_pop, a_w = _population(profile="benchmark")
    w_max = float(w_pop.max()) * 1.05
    tau = a_w - 0.08  # comfortably true
    rng = np.random.default_rng(3)
    idx = rng.integers(0, len(c_pop), size=8000)
    res = resolve_weighted_claim(c_pop[idx], w_pop[idx], tau, w_max)
    assert res.verdict is Verdict.SUPPORTED
    assert res.n_star is not None


def test_ratio_cs_time_uniform_coverage():
    alpha, n_rep, n_stream = 0.05, 200, 1000
    c_pop, w_pop, a_w = _population(profile="benchmark")
    w_max = float(w_pop.max()) * 1.05
    violations = 0
    for r in range(n_rep):
        rng = np.random.default_rng(5000 + r)
        idx = rng.integers(0, len(c_pop), size=n_stream)
        cs = weighted_ratio_cs(c_pop[idx], w_pop[idx], w_max, alpha=alpha)
        if np.any(cs.lower > a_w) or np.any(cs.upper < a_w):
            violations += 1
    rate = violations / n_rep
    assert rate <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep), rate


def test_adversarial_stopping_breaks_fixed_n_not_cs():
    """Stop the first time a naive fixed-n Wald interval would certify: the
    naive rule inflates false certification well above alpha; the CS holds."""
    alpha, n_rep, n_stream = 0.05, 300, 2000
    z_crit = 1.6449  # one-sided 95%
    c_pop, w_pop, a_w = _population(profile="benchmark")
    w_max = float(w_pop.max()) * 1.05
    tau = min(a_w + 0.01, 1.0)  # false claim, near boundary
    naive_cert = cs_cert = 0
    for r in range(n_rep):
        rng = np.random.default_rng(9000 + r)
        idx = rng.integers(0, len(c_pop), size=n_stream)
        z = weighted_claim_stream(c_pop[idx], w_pop[idx], tau, w_max)
        t = np.arange(1, n_stream + 1)
        mean = np.cumsum(z) / t
        var = np.cumsum(z * z) / t - mean**2
        se = np.sqrt(np.maximum(var, 1e-12) / t)
        if np.any((mean - z_crit * se >= tau) & (t >= 30)):
            naive_cert += 1
        cs = empirical_bernstein_cs(z, alpha=alpha).running_intersection()
        if np.any(cs.lower >= tau):
            cs_cert += 1
    assert naive_cert / n_rep > 2 * alpha   # naive rule is broken by stopping
    assert cs_cert / n_rep <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep)


def test_ba_component_bound_conservative():
    """BA_w claims: false-cert rate under the component bound must be <=
    alpha (it should be far below — conservatism is the registered cost)."""
    alpha, n_rep, n_stream = 0.05, 150, 2000
    rng0 = np.random.default_rng(42)
    n = 20000
    y = (rng0.random(n) < 0.3).astype(int)
    w = rng0.choice([0.05, 1.0], size=n, p=[0.4, 0.6])
    p_correct = np.where(y == 1, 0.75, 0.85)
    c = (rng0.random(n) < p_correct).astype(float)
    tpr = (w * c * (y == 1)).sum() / (w * (y == 1)).sum()
    tnr = (w * c * (y == 0)).sum() / (w * (y == 0)).sum()
    ba_w = (tpr + tnr) / 2
    w_max = float(w.max()) * 1.05
    tau = min(ba_w + 0.02, 1.0)  # false claim
    false_cert = 0
    for r in range(n_rep):
        rng = np.random.default_rng(7000 + r)
        idx = rng.integers(0, n, size=n_stream)
        res = resolve_ba_claim(c[idx], y[idx], w[idx], tau, w_max, alpha=alpha)
        if res.verdict is Verdict.SUPPORTED:
            false_cert += 1
    assert false_cert / n_rep <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep)


def test_ess_ratio():
    assert effective_sample_size_ratio(np.ones(100)) == pytest.approx(1.0)
    u = np.zeros(100); u[0] = 5.0
    assert effective_sample_size_ratio(u) == pytest.approx(0.01)


# ---- E13v2: pre-split BA_w allocation (spec 4c) ---------------------------

def _presplit_population(seed=42, n=20000):
    rng0 = np.random.default_rng(seed)
    y = (rng0.random(n) < 0.3).astype(int)
    w = rng0.choice([0.05, 1.0], size=n, p=[0.4, 0.6])
    c = (rng0.random(n) < np.where(y == 1, 0.75, 0.85)).astype(float)
    tpr = (w * c * (y == 1)).sum() / (w * (y == 1)).sum()
    tnr = (w * c * (y == 0)).sum() / (w * (y == 0)).sum()
    return y, w, c, float(tpr), float(tnr)


def test_presplit_false_cert_controlled():
    """Spec 4c validity (i): false certification <= alpha on a false BA
    claim decomposed with per-component margins."""
    alpha, n_rep, n_stream = 0.05, 150, 2000
    y, w, c, tpr, tnr = _presplit_population()
    w_max_pos = float(w[y == 1].max()) * 1.05
    w_max_neg = float(w[y == 0].max()) * 1.05
    m = 0.02  # false claim: both components above truth
    false_cert = 0
    for r in range(n_rep):
        rng = np.random.default_rng(9000 + r)
        idx = rng.integers(0, len(y), size=n_stream)
        ba, _rp, _rn = resolve_ba_presplit(
            c[idx], y[idx], w[idx], min(tpr + m, 1.0), min(tnr + m, 1.0),
            w_max_pos, w_max_neg, alpha=alpha)
        if ba.verdict is Verdict.SUPPORTED:
            false_cert += 1
    assert false_cert / n_rep <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep)


def test_presplit_true_claim_resolves_when_feasible():
    """With mild dispersion and balanced classes the pre-split rule must
    certify a comfortably true BA claim (the sharpening exists)."""
    y, w, c, tpr, tnr = _presplit_population()
    w_max_pos = float(w[y == 1].max()) * 1.05
    w_max_neg = float(w[y == 0].max()) * 1.05
    rng = np.random.default_rng(123)
    idx = rng.integers(0, len(y), size=20000)
    ba, rp, rn = resolve_ba_presplit(
        c[idx], y[idx], w[idx], tpr - 0.10, tnr - 0.10,
        w_max_pos, w_max_neg, alpha=0.05)
    assert ba.verdict is Verdict.SUPPORTED
    assert ba.n_star == max(rp.n_star, rn.n_star)


def test_presplit_disagreement_is_unresolved():
    """One component certifying and the other refuting must yield
    UNRESOLVED (fail-closed, spec 4c verdict rule)."""
    y, w, c, tpr, tnr = _presplit_population()
    w_max_pos = float(w[y == 1].max()) * 1.05
    w_max_neg = float(w[y == 0].max()) * 1.05
    rng = np.random.default_rng(321)
    idx = rng.integers(0, len(y), size=5000)
    # TPR claim far below truth (certifies); TNR claim far above (refutes)
    ba, rp, rn = resolve_ba_presplit(
        c[idx], y[idx], w[idx], max(tpr - 0.10, 0.0), min(tnr + 0.10, 1.0),
        w_max_pos, w_max_neg, alpha=0.05)
    assert rp.verdict is Verdict.SUPPORTED
    assert rn.verdict is Verdict.REFUTED
    assert ba.verdict is Verdict.UNRESOLVED
    assert ba.n_star is None


def test_presplit_class_bound_violation_raises():
    """A signal-class weight above the predeclared per-class bound must
    void loudly (spec 3.4 discipline applied per class)."""
    y, w, c, tpr, tnr = _presplit_population()
    bad_wmax_pos = float(w[y == 1].max()) * 0.5
    w_max_neg = float(w[y == 0].max()) * 1.05
    with pytest.raises(ValueError):
        resolve_ba_presplit(c[:100], y[:100], w[:100], 0.5, 0.5,
                            bad_wmax_pos, w_max_neg)
