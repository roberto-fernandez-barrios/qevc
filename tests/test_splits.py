import numpy as np
import pytest

from qevc.data.splits import ROLES, SplitSpec, load_splits, make_splits, save_splits

FRAC = {
    "train": 0.4,
    "source_val": 0.15,
    "nominal_test": 0.15,
    "auditor_dev": 0.15,
    "final_eval": 0.15,
}
RNG = np.random.default_rng(1)


def test_partition_disjoint_and_complete():
    y = (RNG.random(1000) < 0.3).astype(int)
    splits = make_splits(1000, SplitSpec(FRAC, seed=0), y=y)
    all_idx = np.concatenate(list(splits.values()))
    assert len(all_idx) == 1000
    assert len(np.unique(all_idx)) == 1000
    assert set(splits) == set(ROLES)


def test_stratification_preserves_class_ratio():
    y = (RNG.random(10000) < 0.25).astype(int)
    splits = make_splits(10000, SplitSpec(FRAC, seed=1), y=y)
    for idx in splits.values():
        assert abs(y[idx].mean() - y.mean()) < 0.02


def test_deterministic_given_seed():
    y = (RNG.random(500) < 0.5).astype(int)
    a = make_splits(500, SplitSpec(FRAC, seed=42), y=y)
    b = make_splits(500, SplitSpec(FRAC, seed=42), y=y)
    c = make_splits(500, SplitSpec(FRAC, seed=43), y=y)
    for r in ROLES:
        assert np.array_equal(a[r], b[r])
    assert any(not np.array_equal(a[r], c[r]) for r in ROLES)


def test_save_load_roundtrip_and_quarantine(tmp_path):
    y = (RNG.random(300) < 0.5).astype(int)
    spec = SplitSpec(FRAC, seed=7)
    splits = make_splits(300, spec, y=y)
    p = save_splits(splits, spec, tmp_path / "splits_seed7.json")
    loaded = load_splits(p)
    assert "final_eval" not in loaded  # sealed by default
    for r in loaded:
        assert np.array_equal(loaded[r], splits[r])
    unsealed = load_splits(p, touch_final_eval=True)
    assert np.array_equal(unsealed["final_eval"], splits["final_eval"])
    with pytest.raises(FileExistsError):
        save_splits(splits, spec, p)


def test_spec_validation():
    with pytest.raises(ValueError):
        SplitSpec({**FRAC, "train": 0.5}, seed=0)  # doesn't sum to 1
    bad = dict(FRAC)
    bad.pop("auditor_dev")
    with pytest.raises(ValueError):
        SplitSpec(bad, seed=0)
    with pytest.raises(ValueError):
        make_splits(100, SplitSpec(FRAC, seed=0))  # stratify without labels
