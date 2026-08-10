"""Console summary of E09 (dev aid): shots vs kernel error, AUC, flips."""

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E09_shots.json").read_text())

ex = d["exact"]
print(f"exact: eff_rank={ex['kernel']['eff_rank']} "
      f"auc_nom={ex['envs']['nominal']['auc']:.4f} M_S={ex['m_source']:.4f}")
print("exact verdicts:", {n: e["verdicts"] for n, e in ex["envs"].items()})

shots_vals = sorted({int(c.split("_")[0][5:]) for c in d["configs"]})
print(f"\n{'shots':>6s} {'frob_err':>9s} {'psd_viol':>9s} {'eff_rank':>9s} "
      f"{'auc_nom':>16s} {'flips':>6s} {'tes_dev_max':>11s}")
for sh in shots_vals:
    cfgs = [v for k, v in d["configs"].items() if k.startswith(f"shots{sh}_")]
    frob = np.mean([c["kernel"]["frob_rel_err"] for c in cfgs])
    psd = np.mean([c["kernel"]["psd_violation"] for c in cfgs])
    er = np.mean([c["kernel"]["eff_rank"] for c in cfgs])
    aucs = [c["envs"]["nominal"]["auc"] for c in cfgs]
    flips = [c["verdict_flips_vs_exact"] for c in cfgs]
    tes_dev = max(abs(v) for c in cfgs for v in c["tes_response_deviation"].values())
    print(f"{sh:6d} {frob:9.4f} {psd:9.5f} {er:9.1f} "
          f"{np.mean(aucs):8.4f}±{np.std(aucs):.4f} {np.mean(flips):6.1f} "
          f"{tes_dev:11.4f}")

print("\nper-config verdict flips (20 cells each: 5 envs x 4 deltas):")
for k, v in sorted(d["configs"].items()):
    if v["verdict_flips_vs_exact"] > 0:
        flipped = [
            (n, dd) for n, e in v["envs"].items() for dd, verd in e["verdicts"].items()
            if verd != ex["envs"][n]["verdicts"][dd]
        ]
        print(f"  {k}: {v['verdict_flips_vs_exact']} flips -> {flipped}")
