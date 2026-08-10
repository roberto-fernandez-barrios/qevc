import numpy as np
import pytest

from qevc.metrics.classifier import (
    expected_calibration_error,
    metric_suite,
    weighted_auc,
    weighted_balanced_accuracy,
    weighted_brier,
    weighted_pr_auc,
)

RNG = np.random.default_rng(3)


def _toy(n=2000, sep=1.5):
    y = (RNG.random(n) < 0.4).astype(int)
    score = 1 / (1 + np.exp(-(sep * (2 * y - 1) + RNG.normal(size=n))))
    w = RNG.exponential(1.0, size=n)
    return y, score, w


def test_auc_perfect_and_random():
    y = np.array([0, 0, 1, 1])
    assert weighted_auc(y, [0.1, 0.2, 0.8, 0.9]) == 1.0
    y, s, w = _toy(sep=0.0)
    assert abs(weighted_auc(y, s, w) - 0.5) < 0.05


def test_weights_matter():
    y = np.array([0, 0, 1, 1])
    s = np.array([0.1, 0.9, 0.2, 0.8])
    w_a = np.array([1.0, 0.01, 0.01, 1.0])  # upweights correct pairs
    w_b = np.array([0.01, 1.0, 1.0, 0.01])  # upweights incorrect pairs
    assert weighted_auc(y, s, w_a) > 0.9 > 0.1 > weighted_auc(y, s, w_b)


def test_balanced_accuracy_frozen_threshold():
    y, s, w = _toy()
    ba = weighted_balanced_accuracy(y, (s >= 0.5).astype(float), w)
    assert 0.6 < ba < 1.0
    with pytest.raises(ValueError):
        weighted_balanced_accuracy(y, s, w)  # soft scores rejected


def test_ece_calibrated_vs_miscalibrated():
    n = 20000
    p = RNG.random(n)
    y_cal = (RNG.random(n) < p).astype(int)
    ece_cal = expected_calibration_error(y_cal, p)
    ece_bad = expected_calibration_error(y_cal, np.clip(p**3, 0, 1))
    assert ece_cal < 0.02
    assert ece_bad > 5 * ece_cal


def test_brier_bounds():
    y, s, w = _toy()
    assert 0.0 < weighted_brier(y, s, w) < 0.25
    assert weighted_brier([1, 0], [1.0, 0.0]) == 0.0


def test_metric_suite_keys():
    y, s, w = _toy()
    out = metric_suite(y, s, threshold=0.5, sample_weight=w)
    assert set(out) == {"auc", "pr_auc", "balanced_accuracy", "ece", "brier", "threshold"}
    assert all(np.isfinite(v) for v in out.values())
    assert weighted_pr_auc(y, s, w) > 0.4


def test_validation_errors():
    with pytest.raises(ValueError):
        weighted_auc([0, 2], [0.5, 0.5])
    with pytest.raises(ValueError):
        weighted_auc([0, 1], [0.5, 0.5], [-1.0, 1.0])
    with pytest.raises(ValueError):
        expected_calibration_error([0, 1], [0.5, 1.5])
