"""Stratified subset loader for the FAIR Universe parquet (D-010, E00 findings).

The parquet's leading row group(s) are process-blocked (E00: group 0 is 100%
ztautau), so subsets are sampled by GLOBAL row index, stratified per process,
never by row-group clusters. Subset weights are renormalized per process to the
full-file weight sums (decision D-010), so weighted yields on subsets estimate
full-dataset quantities.

Caches (under a cache dir, typically ``data/interim``):
- ``label_codes.npy``  — int8 process code per row (one full-file scan);
- ``process_stats.json`` — per-process counts and full-file weight sums;
- subsets under ``subsets/`` as parquet + provenance JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

PROCESS_CODES = {"htautau": 0, "ztautau": 1, "ttbar": 2, "diboson": 3}
CODE_TO_PROCESS = {v: k for k, v in PROCESS_CODES.items()}


class FairUniverseLoader:
    def __init__(self, parquet_path: str | Path, cache_dir: str | Path):
        self.parquet_path = Path(parquet_path)
        self.cache_dir = Path(cache_dir)
        if not self.parquet_path.is_file():
            raise FileNotFoundError(self.parquet_path)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._pf = pq.ParquetFile(self.parquet_path)

    # -- full-file index ----------------------------------------------------

    def label_codes(self) -> np.ndarray:
        """int8 process code per global row index (cached, one streaming scan)."""
        cache = self.cache_dir / "label_codes.npy"
        if cache.exists():
            return np.load(cache)
        codes = np.empty(self._pf.metadata.num_rows, dtype=np.int8)
        pos = 0
        for batch in self._pf.iter_batches(columns=["detailed_labels"],
                                           batch_size=4_000_000):
            dl = batch.column(0).to_pandas()
            codes[pos : pos + len(dl)] = dl.map(PROCESS_CODES).to_numpy(dtype=np.int8)
            pos += len(dl)
        assert pos == len(codes)
        np.save(cache, codes)
        return codes

    def process_stats(self) -> dict:
        """Per-process row counts and full-file weight sums (cached)."""
        cache = self.cache_dir / "process_stats.json"
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        counts: dict[str, int] = {p: 0 for p in PROCESS_CODES}
        wsums: dict[str, float] = {p: 0.0 for p in PROCESS_CODES}
        for batch in self._pf.iter_batches(columns=["detailed_labels", "weights"],
                                           batch_size=4_000_000):
            df = batch.to_pandas()
            g = df.groupby("detailed_labels", observed=True)["weights"]
            for proc, cnt in g.count().items():
                counts[proc] += int(cnt)
            for proc, ws in g.sum().items():
                wsums[proc] += float(ws)
        stats = {"counts": counts, "weight_sums": wsums}
        cache.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        return stats

    # -- sampling -----------------------------------------------------------

    def stratified_indices(self, n_total: int, seed: int,
                           exclude: np.ndarray | None = None) -> np.ndarray:
        """Sorted global row indices, stratified at the file's process mix.

        ``exclude`` (D-020): optional array of global row indices removed from
        every per-process pool BEFORE sampling, so the draw is provably
        disjoint from previously used rows. Allocation proportions are always
        computed on the full file, so the subset keeps the file's process mix.
        With ``exclude=None`` the code path (and hence any historical draw's
        reproduction) is byte-identical to the original implementation.
        """
        codes = self.label_codes()
        if not 0 < n_total <= len(codes):
            raise ValueError("n_total out of range")
        rng = np.random.default_rng(seed)
        picks: list[np.ndarray] = []
        # Largest-remainder allocation keeps the exact total.
        props = {c: (codes == c).mean() for c in CODE_TO_PROCESS}
        alloc = {c: int(np.floor(n_total * p)) for c, p in props.items()}
        remainder = n_total - sum(alloc.values())
        for c in sorted(props, key=lambda c: -(n_total * props[c]) % 1)[:remainder]:
            alloc[c] += 1
        excl = None
        if exclude is not None:
            excl = np.unique(np.asarray(exclude, dtype=np.int64))
        for c, k in alloc.items():
            if k == 0:
                continue
            pool = np.flatnonzero(codes == c)
            if excl is not None:
                pool = pool[~np.isin(pool, excl, assume_unique=True)]
                if k > len(pool):
                    raise ValueError(
                        f"process {CODE_TO_PROCESS[c]}: pool exhausted after "
                        f"exclusion ({len(pool)} < {k})")
            picks.append(rng.choice(pool, size=k, replace=False))
        out = np.sort(np.concatenate(picks))
        if excl is not None:
            assert not np.any(np.isin(out, excl, assume_unique=True))
        return out

    def load_rows(self, indices: np.ndarray) -> pd.DataFrame:
        """Gather rows by sorted global indices (reads only needed row groups)."""
        indices = np.asarray(indices, dtype=np.int64)
        if len(indices) == 0 or np.any(np.diff(indices) <= 0):
            raise ValueError("indices must be non-empty, sorted, unique")
        boundaries = np.cumsum(
            [0] + [self._pf.metadata.row_group(g).num_rows
                   for g in range(self._pf.metadata.num_row_groups)]
        )
        frames = []
        group_of = np.searchsorted(boundaries, indices, side="right") - 1
        for g in np.unique(group_of):
            local = indices[group_of == g] - boundaries[g]
            tbl = self._pf.read_row_group(int(g))
            frames.append(tbl.take(local).to_pandas())
        return pd.concat(frames, ignore_index=True)

    # -- public API ---------------------------------------------------------

    def load_subset(self, n_total: int, seed: int, renormalize: bool = True,
                    exclude: np.ndarray | None = None,
                    tag: str | None = None) -> pd.DataFrame:
        """Stratified subset with per-process weight renormalization (D-010).

        Cached: repeated calls with the same (n_total, seed, renormalize)
        return the cached parquet, with provenance JSON alongside.

        D-020 extension: with ``exclude`` the draw avoids the given global
        indices and a distinguishing ``tag`` is REQUIRED (the cache key must
        not collide with unexcluded draws). Fresh draws (cache misses) also
        persist their global indices as ``<cache>.indices.npy`` so
        disjointness is a stored, checkable artifact.
        """
        if exclude is not None and not tag:
            raise ValueError("an exclusion draw requires an explicit tag (D-020)")
        stem = f"subset_n{n_total}_seed{seed}{'_renorm' if renormalize else ''}"
        if tag:
            stem += f"_{tag}"
        cache = self.cache_dir / "subsets" / f"{stem}.parquet"
        if cache.exists():
            return pd.read_parquet(cache)
        idx = self.stratified_indices(n_total, seed, exclude=exclude)
        df = self.load_rows(idx)
        factors: dict[str, float] = {}
        if renormalize:
            full = self.process_stats()["weight_sums"]
            for proc, sub_sum in df.groupby("detailed_labels", observed=True)["weights"].sum().items():
                factors[proc] = full[proc] / float(sub_sum)
                df.loc[df["detailed_labels"] == proc, "weights"] *= factors[proc]
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache, index=False)
        idx_path = cache.with_suffix(".indices.npy")
        np.save(idx_path, idx.astype(np.int64))
        prov = {
            "source": str(self.parquet_path),
            "n_total": n_total,
            "seed": seed,
            "renormalize": renormalize,
            "renorm_factors": factors,
            "indices_sha_input": (
                f"stratified_indices(n={n_total}, seed={seed}"
                f"{', exclude=<archived>' if exclude is not None else ''})"),
            "indices_file": idx_path.name,
            "n_excluded": 0 if exclude is None else int(np.unique(np.asarray(exclude)).size),
        }
        cache.with_suffix(".json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
        return df
