"""Validity tests for the auditor's statistical backbone.

The critical property is *time-uniform* coverage: the probability that the CS
ever excludes the true mean along the whole trajectory must be <= alpha. We
check it by Monte Carlo, and we check the fail-closed decision semantics.
"""

import numpy as np
import pytest

from qevc.auditing.claims import Claim, Verdict, resolve_claim
from qevc.statistics.confidence_sequences import (
    clopper_pearson,
    empirical_bernstein_cs,
    hoeffding_cs,
)

RNG = np.random.default_rng(20260810)


@pytest.mark.parametrize("cs_fn", [hoeffding_cs, empirical_bernstein_cs])
@pytest.mark.parametrize("mu", [0.1, 0.5, 0.72, 0.9])
def test_time_uniform_coverage(cs_fn, mu):
    """P(exists t: mu outside CS_t) must be <= alpha (with MC slack)."""
    alpha, n_stream, n_rep = 0.05, 400, 400
    violations = 0
    for _ in range(n_rep):
        x = (RNG.random(n_stream) < mu).astype(float)
        cs = cs_fn(x, alpha=alpha).running_intersection()
        if np.any(cs.lower > mu) or np.any(cs.upper < mu):
            violations += 1
    rate = violations / n_rep
    # Binomial 3-sigma slack above alpha.
    assert rate <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep), rate


def test_eb_tighter_than_hoeffding_low_variance():
    """Variance adaptivity: EB should beat Hoeffding on low-variance streams."""
    x = (RNG.random(2000) < 0.95).astype(float)
    eb = empirical_bernstein_cs(x).running_intersection()
    hf = hoeffding_cs(x).running_intersection()
    width_eb = eb.upper[-1] - eb.lower[-1]
    width_hf = hf.upper[-1] - hf.lower[-1]
    assert width_eb < width_hf


def test_running_intersection_monotone():
    x = (RNG.random(500) < 0.6).astype(float)
    cs = empirical_bernstein_cs(x).running_intersection()
    assert np.all(np.diff(cs.lower) >= -1e-12)
    assert np.all(np.diff(cs.upper) <= 1e-12)


def test_resolve_supported_and_nstar():
    """A clearly-true claim resolves SUPPORTED with finite n*."""
    x = (RNG.random(3000) < 0.9).astype(float)
    cs = empirical_bernstein_cs(x)
    res = resolve_claim(Claim("acc", 0.8), cs)
    assert res.verdict is Verdict.SUPPORTED
    assert res.n_star is not None and res.n_star < 3000
    assert res.lower >= 0.8


def test_resolve_refuted():
    x = (RNG.random(3000) < 0.55).astype(float)
    res = resolve_claim(Claim("acc", 0.8), empirical_bernstein_cs(x))
    assert res.verdict is Verdict.REFUTED


def test_resolve_unresolved_when_ambiguous():
    """Tiny evidence near the threshold must abstain (fail-closed)."""
    x = (RNG.random(8) < 0.8).astype(float)
    res = resolve_claim(Claim("acc", 0.8), empirical_bernstein_cs(x))
    assert res.verdict is Verdict.UNRESOLVED
    assert res.n_star is None


def test_heuristic_alarm_only_demotes():
    x_good = (RNG.random(3000) < 0.9).astype(float)
    res = resolve_claim(Claim("acc", 0.8), empirical_bernstein_cs(x_good), heuristic_alarm=True)
    assert res.verdict is Verdict.UNRESOLVED and res.vetoed

    x_bad = (RNG.random(3000) < 0.55).astype(float)
    res = resolve_claim(Claim("acc", 0.8), empirical_bernstein_cs(x_bad), heuristic_alarm=True)
    assert res.verdict is Verdict.REFUTED and not res.vetoed


def test_false_certification_rate_controlled():
    """Empirical Type-I: claim 'mu >= 0.8' when truth is 0.78 (claim false).

    SUPPORTED verdicts anywhere along the stream count as false certification;
    rate must stay <= alpha (+MC slack).
    """
    alpha, n_rep = 0.05, 300
    false_cert = 0
    for _ in range(n_rep):
        x = (RNG.random(1500) < 0.78).astype(float)
        res = resolve_claim(Claim("acc", 0.8), empirical_bernstein_cs(x, alpha=alpha))
        # n_star with SUPPORTED-at-any-time counts: check via intersection scan
        inter = empirical_bernstein_cs(x, alpha=alpha).running_intersection()
        if np.any(inter.lower >= 0.8):
            false_cert += 1
    rate = false_cert / n_rep
    assert rate <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_rep), rate


def test_clopper_pearson_basics():
    lo, hi = clopper_pearson(90, 100)
    assert 0.8 < lo < 0.9 < hi <= 1.0
    assert clopper_pearson(0, 10)[0] == 0.0
    assert clopper_pearson(10, 10)[1] == 1.0
