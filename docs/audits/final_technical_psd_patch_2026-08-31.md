# Final technical PSD patch audit — 2026-08-31

## Scope and frozen provenance

This is a post-hoc robustness analysis prompted by the final technical audit,
not a new experiment. It uses the six E16 shot budgets and five kernel seeds
already frozen in `configs/experiments/E16.yaml`. The original runner did not
persist the large Gram arrays, so the stable RNG and frozen inputs were
deterministically replayed. All 30 historical per-configuration summaries
matched `results/tables/E16_quantum_uncertainty.json` before repair.

- Primary E16 SHA-256:
  `3208814B4A66609A6C9436D2E232A8BD93204F36F6E2E5431D9FECA5DED981FE`.
- E16 deployment summary SHA-256:
  `1E593F7BFBC8D1C974A0391042851D8F4E962DD90B7C997BD486D4A42D2FEDAC`.
- E16 config SHA-256:
  `AE6B41936C03F60F18540B98395AEA9BF88F37D348B89DFC51FEE97EB070946C`.
- Frozen deployment SHA-256:
  `93E47A093C6481F0232DBD9E288CF35032DAF8AC364E1ACA39E04BC66142CD1F`.
- Derived PSD analysis SHA-256:
  `31D13A9D2EA739284DD739C1523120B349787D45C9062B9B21C5527CADE7ED7D`.

The derived JSON records the before/after hashes of every E16 hardware raw
file. They are unchanged. E20 remains `offline_gate_only` with
`qpu_jobs_submitted = 0`.

## Declared spectrum and repair conventions

Negative modes are eigenvalues below
`-1e-10 * max(1, abs(lambda_max))`. Reported negative mass is the magnitude of
their sum; relative indefiniteness is `max(0,-lambda_min)/abs(lambda_max)`;
negative-mass fraction divides by total absolute spectral mass. The
positive-spectrum condition number is descriptive only for an indefinite
matrix.

The single repair is minimum diagonal loading:

`K_psd = K_raw + max(0, -lambda_min + epsilon) I`,

where `epsilon = 1e-10 * max(1, abs(lambda_max))`. It preserves every
off-diagonal finite-shot estimate and every source/target cross-Gram. The same
SVC is refitted and the same calibration, threshold-freezing, roles, claims
and paired audit streams are rerun without new randomness.

## Spectral and far-margin result

| Shots | n | Median lambda_min | Worst lambda_min | Median negative modes | Worst negative modes | Raw far C_dep flips | PSD far C_dep flips | Raw far C_ideal flips | PSD far C_ideal flips |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 5 | -1.930 | -1.939 | 580 | 580 | 0.0% | 0.0% | 20.8% | 31.5% |
| 256 | 5 | -1.325 | -1.333 | 531 | 532 | 0.0% | 0.0% | 17.7% | 40.7% |
| 512 | 5 | -0.936 | -0.966 | 489 | 490 | 0.0% | 0.0% | 0.9% | 25.1% |
| 1024 | 5 | -0.655 | -0.657 | 449 | 450 | 0.0% | 0.0% | 11.9% | 3.0% |
| 2048 | 5 | -0.448 | -0.457 | 412 | 413 | 0.0% | 0.0% | 5.8% | 6.9% |
| 4096 | 5 | -0.313 | -0.319 | 379 | 380 | 0.0% | 0.0% | 0.4% | 0.3% |

All 30 raw Grams are indefinite. Median negative spectral-mass fraction falls
from 13.59% at 128 shots to 2.14% at 4096 shots. Mean PSD-repaired nominal AUC
differs from raw by +0.0051 to +0.0137 across budgets. Deployment-relative
raw-versus-repaired verdict-change rates are zero for far, at most 19.9% for
moderate and 7.6% for near. Full deployment metrics, target metrics,
thresholds, abstention, verdict composition and transitions are stored in
`results/tables/E16_psd_sensitivity.json`.

## Scientific disposition

**PSD-SENSITIVE-BUT-SCOPED.** The zero far-margin deployment-relative flip
finding survives exactly. The qualitative ideal-anchored finding also
survives: rates remain heterogeneous, non-monotonic across the observed budget
sequence and much smaller at the 4096-shot endpoint. Several ideal-anchored
magnitudes change materially, however, so the historical raw percentages are
not repair-invariant and are not presented as such.

No other manuscript or repository was modified. In particular, *Sharp
Target-Domain Certificates for Quantum-Kernel Advantage under Distribution
Shift* was not cited, edited or added to the present paper.
