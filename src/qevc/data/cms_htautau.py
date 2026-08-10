"""CMS Open Data H→ττ (μτ_h, 2012) ingestion — Level II (audit §2).

Reads the 69-branch reduced-NanoAOD files (records 12351–12359 / root.cern
mirror), applies a documented HIG-13-004-inspired selection, and computes
high-level features PARALLEL to the FAIR Universe quantum feature set
(D-011), so Level-I-trained pipelines and sensors apply unchanged.

Selection (simplified from the reference skim; deviations documented here):
- trigger  ``HLT_IsoMu17_eta2p1_LooseIsoPFTau20``;
- muon: pt > 20 GeV, |η| < 2.1, tightId, pfRelIso03 < 0.1;
- tau:  pt > 25 GeV, |η| < 2.3, decay-mode finding, Tight isolation,
  Tight anti-e, Tight anti-μ, charge ≠ 0;
- pair: leading passing muon × leading passing tau (pt-ordered collections),
  ΔR(μ,τ) > 0.5;
- the OS/SS charge product is KEPT as a column: OS = signal region,
  SS = QCD control region (the reference analysis' data-driven QCD method).

Weights: MC only, w = σ·L / N_generated with N_generated = total entries of
the ingested file (the mirror files are unbiased ~10% subsets, so this keeps
absolute yields at the mirror's effective luminosity share; all Level-II
claims use data/MC ratios or shapes, never absolute-yield precision).
Cross sections (pb, 8 TeV) and lumi follow the reference outreach analysis.
Real data carries weight 1 and label −1 (NO event-level truth, ever).
"""

from __future__ import annotations

from pathlib import Path

import awkward as ak
import numpy as np
import pandas as pd
import uproot

LUMI_PB = 11467.0  # Run2012B+C TauPlusX (≈11.5 fb⁻¹, FULL datasets)

# The root.cern mirror's DATA files are ~10% subsets of the full runs
# (mirror 3,564,750 + 5,130,317 vs full 35.6M + 51.3M ⇒ fraction 0.1001),
# so the collision data corresponds to an effective luminosity of
# LUMI_PB × DATA_LUMI_FRACTION. MC weights must target THAT luminosity or
# every data/MC comparison is off by ~10× (bug caught by the E11 control
# regions on first run; absolute-yield precision beyond the ~1% rounding of
# the full-run counts is never claimed).
DATA_LUMI_FRACTION = 0.1001
EFFECTIVE_LUMI_PB = LUMI_PB * DATA_LUMI_FRACTION

SAMPLES = {
    # file stem: (process, is_signal, xsec_pb)  — xsecs per reference analysis
    "GluGluToHToTauTau": ("ggH", 1, 19.6),
    "VBF_HToTauTau": ("VBF", 1, 1.55),
    "DYJetsToLL": ("DY", 0, 3503.7),
    "TTbar": ("TT", 0, 225.2),
    "W1JetsToLNu": ("W1J", 0, 6381.2),
    "W2JetsToLNu": ("W2J", 0, 2039.8),
    "W3JetsToLNu": ("W3J", 0, 612.5),
    "Run2012B_TauPlusX": ("data", -1, None),
    "Run2012C_TauPlusX": ("data", -1, None),
}

BRANCHES = [
    "HLT_IsoMu17_eta2p1_LooseIsoPFTau20",
    "nMuon", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass", "Muon_charge",
    "Muon_pfRelIso03_all", "Muon_tightId",
    "nTau", "Tau_pt", "Tau_eta", "Tau_phi", "Tau_mass", "Tau_charge",
    "Tau_idDecayMode", "Tau_idIsoTight", "Tau_idAntiEleTight",
    "Tau_idAntiMuTight",
    "MET_pt", "MET_phi",
    "nJet", "Jet_pt", "Jet_eta",
]

# Feature names parallel to the FAIR Universe quantum set (D-011 order).
FEATURES = [
    "mass_transverse_met_lep", "mass_vis", "pt_ratio_lep_had",
    "met_phi_centrality", "deltar_had_lep", "pt_h", "sum_pt", "met",
]


def _wrap_phi(dphi: np.ndarray) -> np.ndarray:
    return (dphi + np.pi) % (2.0 * np.pi) - np.pi


def _process_chunk(a: ak.Array) -> pd.DataFrame:
    mu = ak.zip({k: a[f"Muon_{k}"] for k in
                 ("pt", "eta", "phi", "mass", "charge")}
                | {"iso": a["Muon_pfRelIso03_all"], "tightId": a["Muon_tightId"]})
    tau = ak.zip({k: a[f"Tau_{k}"] for k in
                  ("pt", "eta", "phi", "mass", "charge")}
                 | {"dm": a["Tau_idDecayMode"], "iso": a["Tau_idIsoTight"],
                    "antie": a["Tau_idAntiEleTight"], "antimu": a["Tau_idAntiMuTight"]})

    mu_ok = ((mu.pt > 20) & (abs(mu.eta) < 2.1)
             & mu.tightId & (mu.iso < 0.1))
    tau_ok = ((tau.pt > 25) & (abs(tau.eta) < 2.3) & (tau.charge != 0)
              & tau.dm & tau.iso & tau.antie & tau.antimu)

    good_mu, good_tau = mu[mu_ok], tau[tau_ok]
    evt = (ak.to_numpy(a["HLT_IsoMu17_eta2p1_LooseIsoPFTau20"]).astype(bool)
           & (ak.to_numpy(ak.num(good_mu)) > 0)
           & (ak.to_numpy(ak.num(good_tau)) > 0))

    m = ak.firsts(good_mu[evt])
    t = ak.firsts(good_tau[evt])
    met = ak.to_numpy(a["MET_pt"][evt])
    met_phi = ak.to_numpy(a["MET_phi"][evt])
    jets_pt = a["Jet_pt"][evt]
    jets_sel = jets_pt[(jets_pt > 30) & (abs(a["Jet_eta"][evt]) < 4.7)]
    jet_sum = ak.to_numpy(ak.sum(jets_sel, axis=1))

    mpt, meta, mphi = (ak.to_numpy(m.pt), ak.to_numpy(m.eta), ak.to_numpy(m.phi))
    tpt, teta, tphi = (ak.to_numpy(t.pt), ak.to_numpy(t.eta), ak.to_numpy(t.phi))
    mmass, tmass = ak.to_numpy(m.mass), ak.to_numpy(t.mass)

    dphi_mt = _wrap_phi(mphi - tphi)
    dr = np.sqrt((meta - teta) ** 2 + dphi_mt ** 2)
    keep = dr > 0.5

    # Visible mass from the μτ four-vectors
    def p4(pt, eta, phi, mass):
        px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
        e = np.sqrt(px**2 + py**2 + pz**2 + mass**2)
        return px, py, pz, e

    mpx, mpy, mpz, me = p4(mpt, meta, mphi, mmass)
    tpx, tpy, tpz, te = p4(tpt, teta, tphi, tmass)
    mass_vis = np.sqrt(np.maximum(
        (me + te) ** 2 - (mpx + tpx) ** 2 - (mpy + tpy) ** 2 - (mpz + tpz) ** 2,
        0.0))

    mt = np.sqrt(np.maximum(
        2.0 * mpt * met * (1.0 - np.cos(_wrap_phi(mphi - met_phi))), 0.0))
    metx, mety = met * np.cos(met_phi), met * np.sin(met_phi)
    pt_h = np.sqrt((mpx + tpx + metx) ** 2 + (mpy + tpy + mety) ** 2)

    # MET φ-centrality (HiggsML definition, ε-regularized at collinearity)
    eps = 1e-6
    a_c = np.sin(_wrap_phi(met_phi - mphi)) * np.sign(np.sin(_wrap_phi(tphi - mphi)))
    b_c = np.sin(_wrap_phi(tphi - met_phi)) * np.sign(np.sin(_wrap_phi(tphi - mphi)))
    denom = np.sqrt(a_c**2 + b_c**2) + eps
    centrality = (a_c + b_c) / denom

    df = pd.DataFrame({
        "mass_transverse_met_lep": mt,
        "mass_vis": mass_vis,
        "pt_ratio_lep_had": mpt / tpt,
        "met_phi_centrality": centrality,
        "deltar_had_lep": dr,
        "pt_h": pt_h,
        "sum_pt": mpt + tpt + jet_sum,
        "met": met,
        "os": (ak.to_numpy(m.charge) * ak.to_numpy(t.charge)) < 0,
    })
    return df[keep].reset_index(drop=True)


def ingest_sample(root_path: str | Path, stem: str) -> pd.DataFrame:
    """One ROOT file → selected feature DataFrame with process metadata."""
    process, is_signal, xsec = SAMPLES[stem]
    total = 0
    chunks = []
    for arrays in uproot.iterate(f"{root_path}:Events", BRANCHES,
                                 step_size="200 MB", library="ak"):
        total += len(arrays)
        chunks.append(_process_chunk(arrays))
    df = pd.concat(chunks, ignore_index=True)
    df["process"] = process
    df["labels"] = is_signal
    df["weights"] = 1.0 if xsec is None else xsec * EFFECTIVE_LUMI_PB / total
    df.attrs["n_generated"] = total
    return df
