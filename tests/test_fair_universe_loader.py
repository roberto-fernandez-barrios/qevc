"""Loader tests on a synthetic parquet that reproduces the process-blocked
head found in E00 (row group 0 single-process), so stratification correctness
is exercised where naive row-group sampling would fail."""

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from qevc.data.fair_universe_loader import PROCESS_CODES, FairUniverseLoader

RNG = np.random.default_rng(17)


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    root = tmp_path_factory.mktemp("fu")
    # Block 1: pure ztautau (mimics the process-blocked head); blocks 2-3 mixed.
    def block(procs, n):
        return pd.DataFrame({
            "PRI_had_pt": RNG.uniform(20, 100, n),
            "weights": RNG.uniform(0.001, 0.01, n),
            "labels": [1.0 if p == "htautau" else 0.0 for p in procs],
            "detailed_labels": procs,
        })
    b1 = block(["ztautau"] * 4000, 4000)
    mix = list(RNG.choice(["htautau", "ztautau", "ttbar", "diboson"],
                          size=8000, p=[0.33, 0.61, 0.05, 0.01]))
    b2 = block(mix[:4000], 4000)
    b3 = block(mix[4000:], 4000)
    df = pd.concat([b1, b2, b3], ignore_index=True)
    path = root / "synthetic.parquet"
    pq.write_table(pa.Table.from_pandas(df), path, row_group_size=4000)
    return path, df, root


def test_label_codes_full_scan(synthetic):
    path, df, root = synthetic
    loader = FairUniverseLoader(path, root / "cache")
    codes = loader.label_codes()
    assert len(codes) == 12000
    expected = df["detailed_labels"].map(PROCESS_CODES).to_numpy(dtype=np.int8)
    np.testing.assert_array_equal(codes, expected)
    # cached second call identical
    np.testing.assert_array_equal(loader.label_codes(), expected)


def test_stratified_indices_match_global_mix(synthetic):
    path, df, root = synthetic
    loader = FairUniverseLoader(path, root / "cache")
    idx = loader.stratified_indices(3000, seed=5)
    assert len(idx) == 3000 and np.all(np.diff(idx) > 0)
    sub = df.iloc[idx]["detailed_labels"].value_counts(normalize=True)
    full = df["detailed_labels"].value_counts(normalize=True)
    for proc in full.index:
        assert abs(sub.get(proc, 0) - full[proc]) < 0.01  # exact up to rounding
    # determinism
    np.testing.assert_array_equal(idx, loader.stratified_indices(3000, seed=5))
    assert not np.array_equal(idx, loader.stratified_indices(3000, seed=6))


def test_load_rows_returns_exact_rows(synthetic):
    path, df, root = synthetic
    loader = FairUniverseLoader(path, root / "cache")
    idx = np.array([0, 3999, 4000, 7500, 11999])  # spans all three row groups
    out = loader.load_rows(idx)
    np.testing.assert_allclose(out["PRI_had_pt"].to_numpy(),
                               df.iloc[idx]["PRI_had_pt"].to_numpy())
    assert list(out["detailed_labels"]) == list(df.iloc[idx]["detailed_labels"])


def test_subset_weight_renormalization_per_process(synthetic):
    path, df, root = synthetic
    loader = FairUniverseLoader(path, root / "cache")
    sub = loader.load_subset(2000, seed=3, renormalize=True)
    full_sums = df.groupby("detailed_labels")["weights"].sum()
    sub_sums = sub.groupby("detailed_labels", observed=True)["weights"].sum()
    for proc in sub_sums.index:
        np.testing.assert_allclose(sub_sums[proc], full_sums[proc], rtol=1e-10)
    # cache hit returns identical frame
    again = loader.load_subset(2000, seed=3, renormalize=True)
    pd.testing.assert_frame_equal(sub, again)


def test_load_rows_validation(synthetic):
    path, _, root = synthetic
    loader = FairUniverseLoader(path, root / "cache")
    with pytest.raises(ValueError):
        loader.load_rows(np.array([5, 5, 6]))  # duplicates
    with pytest.raises(ValueError):
        loader.load_rows(np.array([], dtype=int))
