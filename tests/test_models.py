import numpy as np
import pytest

from qevc.models.classical.suite import REGISTRY, build, tune
from qevc.models.common import (
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
    weighted_resample_indices,
)
from qevc.models.quantum.qksvc import QKSVC, QKSVC_SPACE, qksvc_builder

RNG = np.random.default_rng(23)


def _toy(n=600, d=4, sep=1.6):
    y = (RNG.random(n) < 0.4).astype(int)
    X = RNG.normal(size=(n, d)) + sep * y[:, None]
    w = RNG.exponential(1.0, size=n) * np.where(y == 1, 0.05, 1.0)  # imbalanced
    return X, y, w


def test_class_balanced_weights():
    _, y, w = _toy()
    wb = class_balanced_weights(y, w)
    assert np.isclose(wb[y == 1].sum(), wb[y == 0].sum())  # balanced classes
    assert np.isclose(wb.mean(), 1.0)  # mean-1 (split criteria / C scaling)
    # within-class structure preserved
    r = wb[y == 1] / w[y == 1]
    assert np.allclose(r, r[0])


def test_weighted_resample_prefers_heavy():
    w = np.array([1.0, 1.0, 100.0, 1.0])
    idx = weighted_resample_indices(w, 2000, seed=1)
    assert (idx == 2).mean() > 0.9


def test_platt_and_threshold():
    X, y, w = _toy(2000)
    s = X.sum(axis=1) + RNG.normal(0, 0.5, len(y))
    cal = PlattCalibrator().fit(s, y, w)
    p = cal.predict_proba(s)
    assert p.min() >= 0 and p.max() <= 1
    assert np.all(np.diff(p[np.argsort(s)]) >= -1e-12)  # strictly monotone map
    t = ba_optimal_threshold(y, p, w)
    assert 0.0 < t < 1.0


@pytest.mark.parametrize("name", list(REGISTRY))
def test_each_classical_model_learns(name):
    X, y, w = _toy()
    wb = class_balanced_weights(y, w)
    model = build(name, {k: v[0] for k, v in REGISTRY[name][1].items()}, seed=0)
    model.fit(X, y, sample_weight=wb)
    from qevc.metrics.classifier import weighted_auc

    assert weighted_auc(y, model.scores(X), w) > 0.8


def test_tune_returns_budgeted_trials():
    X, y, w = _toy(400)
    wb = class_balanced_weights(y, w)
    res = tune("xgboost", X, y, wb, w, n_configs=3, cv_folds=2, seed=7)
    assert len(res.trials) == 3
    assert res.best_cv_auc > 0.7
    assert res.best_params in [t["params"] for t in res.trials]


def test_qksvc_learns_and_is_deterministic():
    X, y, w = _toy(n=160, d=3)
    wb = class_balanced_weights(y, w)
    m1 = QKSVC(C=1.0, reps=1, scale=0.5).fit(X, y, sample_weight=wb)
    m2 = QKSVC(C=1.0, reps=1, scale=0.5).fit(X, y, sample_weight=wb)
    from qevc.metrics.classifier import weighted_auc

    s1, s2 = m1.scores(X), m2.scores(X)
    np.testing.assert_allclose(s1, s2)
    assert weighted_auc(y, s1, w) > 0.8


def test_qksvc_tunes_through_generic_tuner():
    X, y, w = _toy(n=120, d=3)
    wb = class_balanced_weights(y, w)
    res = tune("qksvc", X, y, wb, w, n_configs=2, cv_folds=2, seed=3,
               builder_override=qksvc_builder, space_override=QKSVC_SPACE)
    assert len(res.trials) == 2
    assert np.isfinite(res.best_cv_auc)
