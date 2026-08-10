"""E00 — Dataset validation (spec §28, registry E00).

Validates the local FAIR Universe release against its own metadata, the
benchmark paper's documented per-process statistics, and the systematics
semantics pinned in tests/test_fair_universe_systematics.py — on the real
file, not the bundled sample.

Run:  .venv/Scripts/python experiments/E00_dataset_validation/run_e00.py
Outputs: results/tables/E00_validation.json + immutable manifest.
Exit code 0 only if every check passes (gate semantics).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
    apply_environment,
    split_columns,
)
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

PARQUET = REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet"
METAJSON = REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data_metadata.json"
CHECKSUMS = REPO / "data/raw/fair_universe/CHECKSUMS.txt"

CONFIG = {
    "experiment": "E00",
    "dataset": "fair_universe_zenodo_15131565",
    # Documented values (docs/dataset_audit.md §1.1; arXiv:2410.02867):
    "expected_rows": 220_099_101,
    "expected_counts": {
        "htautau": 52_040_227,
        "ztautau": 160_383_358,
        "ttbar": 7_070_398,
        "diboson": 605_118,
    },
    "expected_sum_weights_total": 1_051_433.0,
    "expected_sum_weights_by_process": {
        "htautau": 1_015.0,
        "ztautau": 1_002_395.0,
        "ttbar": 44_192.0,
        "diboson": 3_783.0,
    },
    "weight_sum_rtol": 5e-3,  # documented values are rounded
    "subsample_rows": 200_000,
    "subsample_seed": 20260810,
    "tes_check": 1.02,
}


def check(name: str, ok: bool, detail: str, results: list) -> None:
    results.append({"check": name, "pass": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def main() -> int:
    t0 = time.time()
    results: list[dict] = []
    pf = pq.ParquetFile(PARQUET)
    meta = json.loads(METAJSON.read_text())

    # -- 1. Schema ----------------------------------------------------------
    cols = [pf.schema_arrow.field(i).name for i in range(len(pf.schema_arrow))]
    expected_cols = PRI_COLUMNS + ["weights", "detailed_labels", "labels"] + DER_COLUMNS
    check("schema_columns", set(cols) == set(expected_cols) and len(cols) == 31,
          f"{len(cols)} columns, sets equal={set(cols) == set(expected_cols)}", results)

    # -- 2. Row count vs paper and vs bundled metadata ----------------------
    n = pf.metadata.num_rows
    check("row_count", n == CONFIG["expected_rows"] == meta["total_rows"],
          f"{n:,} rows (paper {CONFIG['expected_rows']:,}, metadata {meta['total_rows']:,})",
          results)

    # -- 3. Full streaming pass: counts and weighted yields per process -----
    counts: dict[str, int] = {}
    wsums: dict[str, float] = {}
    label_mismatch = 0
    for batch in pf.iter_batches(columns=["weights", "labels", "detailed_labels"],
                                 batch_size=2_000_000):
        df = batch.to_pandas()
        for proc, cnt in df["detailed_labels"].value_counts().items():
            counts[proc] = counts.get(proc, 0) + int(cnt)
        for proc, ws in df.groupby("detailed_labels", observed=True)["weights"].sum().items():
            wsums[proc] = wsums.get(proc, 0.0) + float(ws)
        # labels must be exactly 1[detailed_labels == htautau]
        label_mismatch += int(
            ((df["detailed_labels"] == "htautau") != (df["labels"] == 1)).sum()
        )

    check("unweighted_counts_per_process", counts == CONFIG["expected_counts"],
          f"{counts}", results)
    total_w = sum(wsums.values())
    ok_total = np.isclose(total_w, CONFIG["expected_sum_weights_total"], rtol=1e-3) \
        and np.isclose(total_w, meta["sum_weights"], rtol=1e-6)
    check("sum_weights_total", ok_total,
          f"{total_w:,.1f} (metadata {meta['sum_weights']:,.1f})", results)
    ok_proc = all(
        np.isclose(wsums[p], v, rtol=CONFIG["weight_sum_rtol"])
        for p, v in CONFIG["expected_sum_weights_by_process"].items()
    )
    check("sum_weights_per_process", ok_proc,
          {k: round(v, 1) for k, v in wsums.items()}.__repr__(), results)
    check("labels_consistent_with_detailed", label_mismatch == 0,
          f"{label_mismatch} mismatches", results)

    # -- 4. Subsample: value sanity + systematics round-trip ----------------
    rng = np.random.default_rng(CONFIG["subsample_seed"])
    groups = rng.choice(pf.metadata.num_row_groups, size=4, replace=False)
    sub = pd.concat([pf.read_row_group(int(g)).to_pandas() for g in sorted(groups)])
    sub = sub.sample(n=CONFIG["subsample_rows"], random_state=CONFIG["subsample_seed"])

    finite = all(np.isfinite(sub[c].to_numpy(dtype=float)).all()
                 for c in PRI_COLUMNS + DER_COLUMNS + ["weights"])
    check("subsample_all_finite", finite, f"{len(sub):,} rows scanned", results)
    sentinel_ok = (
        ((sub["PRI_jet_leading_pt"] > 0) | (sub["PRI_jet_leading_pt"] == -25)).all()
        and (sub.loc[sub["PRI_n_jets"] == 0, "PRI_jet_leading_pt"] == -25).all()
        and sub["PRI_n_jets"].between(0, 20).all()
        and (sub["weights"] > 0).all()
        and sub["PRI_met_phi"].between(-3.15, 3.15).all()
    )
    check("subsample_value_ranges", bool(sentinel_ok), "sentinels/ranges/weights>0", results)

    dset = split_columns(sub.reset_index(drop=True))
    base = apply_environment(dset, Environment())
    frac_kept = len(base["data"]) / len(sub)
    check("nominal_selection_fraction", 0.80 <= frac_kept <= 1.0,
          f"{frac_kept:.4f} of raw rows survive nominal selection", results)

    tes = CONFIG["tes_check"]
    up = apply_environment(dset, Environment(tes=tes))
    # mean had_pt on selected events rises by ~tes (selection composition shifts slightly)
    ratio = up["data"]["PRI_had_pt"].mean() / base["data"]["PRI_had_pt"].mean()
    check("tes_direction_and_magnitude", 1.0 < ratio < tes + 0.01,
          f"mean PRI_had_pt ratio {ratio:.4f} for TES={tes}", results)
    check("tes_up_gains_events", len(up["data"]) >= len(base["data"]),
          f"{len(up['data']):,} vs {len(base['data']):,} (upward migration)", results)

    # -- 5. Persist ---------------------------------------------------------
    if not CHECKSUMS.exists():
        CHECKSUMS.write_text(f"{file_sha256(PARQUET)}  {PARQUET.name}\n", encoding="utf-8")
    parquet_sha = CHECKSUMS.read_text().split()[0]

    all_pass = all(r["pass"] for r in results)
    out = {
        "experiment": "E00",
        "all_pass": all_pass,
        "checks": results,
        "wall_seconds": round(time.time() - t0, 1),
        "parquet_sha256": parquet_sha,
    }
    out_path = REPO / "results/tables/E00_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    manifest = RunManifest(
        experiment_id="E00",
        config=CONFIG,
        seed=CONFIG["subsample_seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": parquet_sha},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")

    print(f"\nE00 {'ALL PASS' if all_pass else 'FAILURES PRESENT'} "
          f"({out['wall_seconds']} s)")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
