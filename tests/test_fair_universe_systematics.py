"""Semantics-pinning tests for the FAIR Universe systematics wrapper.

Run on the 1000-row sample bundled with the vendored official repo. Findings
pinned here (also recorded in docs/dataset_audit.md):

- the raw parquet carries a LOOSER preselection than the analysis selection:
  the official pipeline applies `postprocess()` (PRI_had_pt >= 26, jet
  demotion below 26) even at nominal θ, so the *nominal analysis dataset* is
  `apply_environment(raw, NOMINAL)`, not the raw file;
- TES/JES act multiplicatively on the documented primaries;
- soft MET is stochastic but seed-deterministic;
- norm nuisances scale exactly their weight groups (our workaround), while the
  official norm path remains a silent no-op (audit §1.3).
"""

import numpy as np
import pandas as pd
import pytest

from qevc.systematics.fair_universe import (
    DER_COLUMNS,
    OFFICIAL_INGESTION_DIR,
    PRI_COLUMNS,
    Environment,
    apply_environment,
    split_columns,
    _official_systematics,
)

pytestmark = pytest.mark.skipif(
    not OFFICIAL_INGESTION_DIR.is_dir(), reason="vendored HEP-Challenge repo absent"
)

SAMPLE = OFFICIAL_INGESTION_DIR.parent / "input_data" / "FAIR_Universe_HiggsML_data.parquet"


@pytest.fixture(scope="module")
def raw_df() -> pd.DataFrame:
    return pd.read_parquet(SAMPLE)


@pytest.fixture()
def dset_raw(raw_df):
    return split_columns(raw_df)


@pytest.fixture(scope="module")
def safe_df(raw_df) -> pd.DataFrame:
    """Rows comfortably away from every selection threshold, so ±5% shifts
    neither drop events nor demote jets — row-stable by construction."""
    ok_had = raw_df["PRI_had_pt"] >= 30
    ok_lead = (raw_df["PRI_jet_leading_pt"] >= 30) | (raw_df["PRI_jet_leading_pt"] == -25)
    ok_sub = (raw_df["PRI_jet_subleading_pt"] >= 30) | (raw_df["PRI_jet_subleading_pt"] == -25)
    out = raw_df[ok_had & ok_lead & ok_sub].reset_index(drop=True)
    assert len(out) > 300  # keep the fixture meaningful
    return out


@pytest.fixture()
def dset_safe(safe_df):
    return split_columns(safe_df)


def test_split_columns_structure(dset_raw):
    assert list(dset_raw["data"].columns) == PRI_COLUMNS
    assert len(dset_raw["weights"]) == len(dset_raw["data"]) == 1000
    assert set(np.unique(dset_raw["labels"])) == {0, 1}


def test_nominal_applies_analysis_selection(raw_df, dset_raw):
    """Raw parquet is pre-selection: nominal θ still drops sub-threshold events."""
    out = apply_environment(dset_raw, Environment())
    expected = raw_df[raw_df["PRI_had_pt"] >= 26]
    assert len(out["data"]) == len(expected) < 1000
    assert out["data"]["PRI_had_pt"].min() >= 26.0
    np.testing.assert_allclose(out["weights"], expected["weights"].to_numpy())


def test_nominal_is_identity_on_safe_rows(safe_df, dset_safe):
    out = apply_environment(dset_safe, Environment())
    assert len(out["data"]) == len(safe_df)
    for col in PRI_COLUMNS:
        np.testing.assert_allclose(
            out["data"][col].to_numpy(), safe_df[col].to_numpy(),
            rtol=0, atol=1e-3,  # official pipeline rounds primaries to 3 decimals
        )
    np.testing.assert_allclose(out["weights"], safe_df["weights"].to_numpy())
    # DER recomputed nominally ≈ shipped DER (float32 + rounding tolerance).
    for col in DER_COLUMNS:
        np.testing.assert_allclose(
            out["data"][col].to_numpy(dtype=float),
            safe_df[col].to_numpy(dtype=float),
            rtol=2e-2, atol=2e-2,
        )


def test_tes_scales_had_pt(dset_safe, safe_df):
    for tes in (0.97, 1.03):
        out = apply_environment(dset_safe, Environment(tes=tes))
        assert len(out["data"]) == len(safe_df)  # row-stable on safe rows
        np.testing.assert_allclose(
            out["data"]["PRI_had_pt"].to_numpy(),
            tes * safe_df["PRI_had_pt"].to_numpy(),
            atol=1e-3,
        )


def test_tes_down_drops_boundary_events(dset_raw):
    base = apply_environment(dset_raw, Environment())
    down = apply_environment(dset_raw, Environment(tes=0.97))
    assert len(down["data"]) < len(base["data"])  # 26–26.8 GeV events migrate out


def test_jes_scales_jets_only_where_present(dset_safe, safe_df):
    out = apply_environment(dset_safe, Environment(jes=1.05))
    assert len(out["data"]) == len(safe_df)
    has_jet = safe_df["PRI_n_jets"].to_numpy() > 0
    lead_before = safe_df["PRI_jet_leading_pt"].to_numpy()
    lead_after = out["data"]["PRI_jet_leading_pt"].to_numpy()
    np.testing.assert_allclose(lead_after[has_jet], 1.05 * lead_before[has_jet], atol=1e-3)
    assert np.all(lead_after[~has_jet] == lead_before[~has_jet])  # -25 sentinels untouched


def test_soft_met_is_stochastic_but_seeded(dset_safe, safe_df):
    a = apply_environment(dset_safe, Environment(soft_met=3.0, seed=1))
    b = apply_environment(dset_safe, Environment(soft_met=3.0, seed=1))
    c = apply_environment(dset_safe, Environment(soft_met=3.0, seed=2))
    np.testing.assert_allclose(a["data"]["PRI_met"], b["data"]["PRI_met"])
    assert not np.allclose(a["data"]["PRI_met"], c["data"]["PRI_met"])
    # MET changes; hadronic tau untouched; selection untouched by MET → row-stable
    assert len(a["data"]) == len(safe_df)
    assert not np.allclose(a["data"]["PRI_met"], safe_df["PRI_met"], atol=1e-3)
    np.testing.assert_allclose(a["data"]["PRI_had_pt"], safe_df["PRI_had_pt"], atol=1e-3)


def test_norm_scales_hit_exactly_their_groups(dset_raw):
    env = Environment(ttbar_scale=1.2, diboson_scale=0.5, bkg_scale=1.01)
    out = apply_environment(dset_raw, env)
    base = apply_environment(dset_raw, Environment())
    dl, y, w = out["detailed_labels"], out["labels"], out["weights"]
    bw = base["weights"]
    np.testing.assert_allclose(w[dl == "ttbar"], bw[dl == "ttbar"] * 1.2 * 1.01)
    np.testing.assert_allclose(w[dl == "diboson"], bw[dl == "diboson"] * 0.5 * 1.01)
    np.testing.assert_allclose(w[dl == "ztautau"], bw[dl == "ztautau"] * 1.01)
    np.testing.assert_allclose(w[y == 1], bw[y == 1])  # signal never norm-scaled


def test_upstream_norm_path_is_still_a_noop(dset_raw):
    """Documents the official bug (audit §1.3). If this fails, upstream fixed
    it and D-008's workaround must be re-examined for double-scaling."""
    official = _official_systematics()
    kwargs = dict(
        data_set={k: dset_raw[k] for k in ("data", "weights", "labels", "detailed_labels")},
        tes=1.0, jes=1.0, soft_met=0.0, dopostprocess=True,
    )
    out = official(**kwargs, ttbar_scale=2.0)
    base = official(**kwargs)
    ttbar = out["detailed_labels"] == "ttbar"
    np.testing.assert_allclose(out["weights"][ttbar], base["weights"][ttbar])


def test_row_id_passthrough_survives_selection(dset_raw, raw_df):
    """D-013: provenance ids ride through shifting + row-dropping selection."""
    dset = dict(dset_raw)
    dset["row_id"] = np.arange(len(raw_df))
    out = apply_environment(dset, Environment(tes=0.97))
    assert "row_id" in out
    assert len(out["row_id"]) == len(out["data"]) < 1000
    # surviving ids reference rows that indeed pass the shifted selection
    survivors = out["row_id"]
    np.testing.assert_allclose(
        np.sort(0.97 * raw_df["PRI_had_pt"].to_numpy()[survivors])[:1].min(),
        out["data"]["PRI_had_pt"].min(), atol=1e-3)
    assert (0.97 * raw_df["PRI_had_pt"].to_numpy()[survivors] >= 26 - 1e-3).all()


def test_environment_validation_and_identity():
    with pytest.raises(ValueError):
        Environment(tes=1.2)
    with pytest.raises(ValueError):
        Environment(bkg_scale=0.9)
    assert Environment().is_nominal
    assert not Environment(jes=1.01).is_nominal
    assert "seed" in Environment(soft_met=1.0).name
    assert "seed" not in Environment(tes=1.02).name
