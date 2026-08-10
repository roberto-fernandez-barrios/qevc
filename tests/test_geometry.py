import numpy as np
import pytest

from qevc.geometry.descriptors import (
    cka,
    class_geometry,
    describe_environment,
    effective_rank,
    eigenspectrum,
    kernel_target_alignment,
    mean_similarity_shift,
    psd_violation,
)

RNG = np.random.default_rng(7)


def _rbf(X, Y, gamma=0.5):
    d2 = ((X[:, None, :] - Y[None, :, :]) ** 2).sum(-1)
    return np.exp(-gamma * d2)


def test_effective_rank_bounds():
    n = 30
    assert effective_rank(np.eye(n)) == pytest.approx(n)
    assert effective_rank(np.ones((n, n))) == pytest.approx(1.0)


def test_eigenspectrum_descending_nonnegative():
    X = RNG.normal(size=(40, 3))
    w = eigenspectrum(_rbf(X, X))
    assert np.all(np.diff(w) <= 1e-10)
    assert np.all(w >= 0)


def test_psd_violation():
    assert psd_violation(np.eye(5)) == 0.0
    K = np.eye(5)
    K[0, 0] = -1.0  # forces a negative eigenvalue
    assert psd_violation(K) > 0


def test_cka_self_and_symmetry():
    X = RNG.normal(size=(50, 4))
    K1, K2 = _rbf(X, X, 0.5), _rbf(X, X, 0.05)
    assert cka(K1, K1) == pytest.approx(1.0)
    assert cka(K1, K2) == pytest.approx(cka(K2, K1))
    assert 0.0 < cka(K1, K2) < 1.0


def test_kta_separable_beats_random():
    y = np.array([1] * 25 + [-1] * 25)
    X = RNG.normal(size=(50, 2)) + 3.0 * y[:, None]
    kta_good = kernel_target_alignment(_rbf(X, X, 0.1), y)
    kta_rand = kernel_target_alignment(_rbf(RNG.normal(size=(50, 2)), RNG.normal(size=(50, 2)) * 0 + RNG.normal(size=(50, 2)), 0.1), y)
    assert kta_good > kta_rand


def test_mmd_zero_same_distribution_positive_under_shift():
    X = RNG.normal(size=(100, 3))
    T_same = RNG.normal(size=(100, 3))
    T_shift = RNG.normal(size=(100, 3)) + 2.0
    d_same = mean_similarity_shift(_rbf(X, X), _rbf(X, T_same), _rbf(T_same, T_same))
    d_shift = mean_similarity_shift(_rbf(X, X), _rbf(X, T_shift), _rbf(T_shift, T_shift))
    assert d_shift["mmd2"] > d_same["mmd2"]
    assert d_shift["mmd2"] > 0.1


def test_class_geometry_separation():
    y = np.array([1] * 30 + [-1] * 30)
    X = RNG.normal(size=(60, 2)) + 2.5 * y[:, None]
    g = class_geometry(_rbf(X, X, 0.2), y)
    assert g["rkhs_centroid_sep2"] > 0.5
    assert g["between"] < min(g["within_pos"], g["within_neg"])


def test_describe_environment_keys_and_i1_discipline():
    X = RNG.normal(size=(40, 3))
    T = RNG.normal(size=(35, 3)) + 1.0
    y = np.array([1] * 20 + [-1] * 20)
    g = describe_environment(_rbf(X, X), _rbf(T, T), _rbf(X, T), y_source=y)
    for key in ("eff_rank_ratio", "mmd2", "kta_source", "class_rkhs_centroid_sep2"):
        assert key in g
    # Without source labels, no label-aware keys may appear (I1 discipline).
    g_unlabeled = describe_environment(_rbf(X, X), _rbf(T, T), _rbf(X, T))
    assert not any(k.startswith(("kta", "class_")) for k in g_unlabeled)
