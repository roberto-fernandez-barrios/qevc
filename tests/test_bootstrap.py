import numpy as np

from qevc.metrics.classifier import weighted_auc
from qevc.statistics.bootstrap import bootstrap_metric, paired_bootstrap_diff

RNG = np.random.default_rng(5)


def _toy(n=1500, sep=1.2):
    y = (RNG.random(n) < 0.5).astype(int)
    s = 1 / (1 + np.exp(-(sep * (2 * y - 1) + RNG.normal(size=n))))
    w = RNG.exponential(1.0, size=n)
    return y, s, w


def test_bootstrap_ci_contains_point_and_is_ordered():
    y, s, w = _toy()
    ci = bootstrap_metric(weighted_auc, y, s, w, n_resamples=500, seed=1)
    assert ci.lower <= ci.point <= ci.upper
    assert 0.5 < ci.lower < ci.upper < 1.0


def test_bootstrap_coverage_sanity():
    """CI should usually contain the large-sample truth."""
    y_big, s_big, w_big = _toy(n=200_000)
    truth = weighted_auc(y_big, s_big, w_big)
    hits = 0
    for k in range(30):
        y, s, w = _toy(n=800)
        ci = bootstrap_metric(weighted_auc, y, s, w, n_resamples=400, seed=k)
        hits += ci.contains(truth)
    assert hits >= 24  # ~95% nominal, generous MC slack


def test_paired_diff_detects_better_model():
    y, s, w = _toy(n=3000, sep=1.5)
    noisy = np.clip(s + RNG.normal(0, 0.35, size=len(s)), 0, 1)
    ci = paired_bootstrap_diff(weighted_auc, y, s, noisy, w, n_resamples=500, seed=2)
    assert ci.point > 0
    assert ci.lower > 0  # significantly better, CI excludes 0


def test_paired_diff_null_covers_zero():
    y, s, w = _toy(n=3000)
    perturbed = np.clip(s + RNG.normal(0, 1e-3, size=len(s)), 0, 1)
    ci = paired_bootstrap_diff(weighted_auc, y, s, perturbed, w, n_resamples=500, seed=3)
    assert ci.contains(0.0)
