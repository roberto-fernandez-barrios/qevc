"""Ingest all CMS mirror samples to cached parquet (E11 input)."""

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from qevc.data.cms_htautau import SAMPLES, ingest_sample  # noqa: E402

RAW = REPO / "data/raw/cms_htautau_mirror"
OUT = REPO / "data/interim/cms"
OUT.mkdir(parents=True, exist_ok=True)

for stem in SAMPLES:
    dst = OUT / f"{stem}.parquet"
    if dst.exists():
        print(f"[{time.strftime('%H:%M:%S')}] {stem}: cached", flush=True)
        continue
    t0 = time.time()
    df = ingest_sample(RAW / f"{stem}.root", stem)
    df.to_parquet(dst, index=False)
    print(f"[{time.strftime('%H:%M:%S')}] {stem}: {len(df):,} selected "
          f"of {df.attrs['n_generated']:,} ({time.time()-t0:.0f} s)", flush=True)
print("INGESTION COMPLETE", flush=True)
