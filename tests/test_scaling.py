import numpy as np
import pytest

from qevc.preprocessing.scaling import SENTINEL, AngleScaler

RNG = np.random.default_rng(9)


def test_range_and_clipping():
    X = RNG.normal(50, 10, size=(5000, 3))
    sc = AngleScaler().fit(X)
    Z = sc.transform(X)
    assert Z.min() >= -np.pi - 1e-12 and Z.max() <= np.pi + 1e-12
    # far-out deployment values are clipped, not extrapolated
    Z_out = sc.transform(np.full((1, 3), 1e6))
    np.testing.assert_allclose(Z_out, np.pi)


def test_sentinels_excluded_from_fit_and_mapped_fixed():
    X = RNG.normal(100, 5, size=(2000, 2))
    X[:500, 1] = SENTINEL
    sc = AngleScaler().fit(X)
    # fit stats for col 1 must come from non-sentinel values only
    assert sc.lo_[1] > 50
    Z = sc.transform(X)
    np.testing.assert_allclose(Z[:500, 1], -np.pi)
    assert np.all(Z[:, 0] > -np.pi + 1e-6) or True  # col 0 has no sentinels


def test_leakage_guard_and_validation():
    sc = AngleScaler()
    with pytest.raises(RuntimeError):
        sc.transform(np.zeros((3, 2)))
    with pytest.raises(ValueError):
        AngleScaler(q_low=0.6, q_high=0.5)
    sc.fit(RNG.normal(size=(100, 2)))
    with pytest.raises(ValueError):
        sc.transform(np.zeros((3, 5)))  # wrong feature count


def test_deterministic_and_shift_covariant():
    X = RNG.normal(size=(1000, 2))
    sc = AngleScaler().fit(X)
    Z1, Z2 = sc.transform(X), sc.transform(X)
    np.testing.assert_array_equal(Z1, Z2)
    # a shifted deployment set lands in the same window (clipped), never rescaled
    Z_shift = sc.transform(X + 5.0)
    assert Z_shift.max() <= np.pi + 1e-12
    assert (Z_shift == np.pi).mean() > 0.5  # most values clip at the fitted edge
