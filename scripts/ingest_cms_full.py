"""Ingest the E11v2 working set (D-026): MC from the verified mirror files
re-weighted to the FULL Run2012B+C luminosity, collision data from the full
opendata.cern.ch files. Output: data/interim/cms_full/*.parquet."""

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from qevc.data.cms_htautau import LUMI_PB, SAMPLES, ingest_sample  # noqa: E402

MIRROR = REPO / "data/raw/cms_htautau_mirror"
FULL = REPO / "data/raw/cms_htautau_full"
OUT = REPO / "data/interim/cms_full"
OUT.mkdir(parents=True, exist_ok=True)

for stem, (_proc, _sig, xsec) in SAMPLES.items():
    dst = OUT / f"{stem}.parquet"
    if dst.exists():
        print(f"[{time.strftime('%H:%M:%S')}] {stem}: cached", flush=True)
        continue
    src = (FULL if xsec is None else MIRROR) / f"{stem}.root"
    t0 = time.time()
    df = ingest_sample(src, stem, lumi_pb=LUMI_PB)
    df.to_parquet(dst, index=False)
    print(f"[{time.strftime('%H:%M:%S')}] {stem}: {len(df):,} selected of "
          f"{df.attrs['n_generated']:,} ({time.time()-t0:.0f} s) "
          f"[{'FULL data' if xsec is None else 'mirror MC @ full lumi'}]",
          flush=True)
print("E11v2 INGESTION COMPLETE", flush=True)
