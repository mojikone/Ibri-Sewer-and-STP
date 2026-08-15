# A3 — Built / Planned Plot Classification, Finalized (Screening Grade)
**W3 analysis · 2026-08-14 · completes A1's built-status gap per user instruction**

## What was produced
`W3/shp/MoH_Plots_built_v2.shp` — all 61,272 MoH plots with:
| Field | Meaning |
|---|---|
| `BUILT_MS` | Microsoft ML footprint intersect (1/0; trusted only in covered zones — A1) |
| `BUILT_IMG` | Esri World Imagery texture classifier (1/0; −1 = no features) |
| `BUILT_FIN` | **Final: BUILT_MS=1 wins, else BUILT_IMG** |
| `SRC` | 1 = MS footprint, 2 = imagery classifier, 0 = unclassified |

Imagery: Esri World Imagery z17 (1.19 m/px), 6,550 tiles, full boundary, mosaicked to
`Hydraulic/Imagery/esri_z17_mosaic_3857.tif` (80 MB, **outside the repo** — imagery is not committed).

## Method & validation
- Classifier: logistic regression on 5 texture features per plot (intensity std, edge energy, shadow/bright fractions, strong-edge density), trained on 5,803 confirmed-built (IBRI, MS footprints) vs 8,616 confirmed-vacant (AT TAYYIB) plots; training accuracy 88.8 %.
- Independent check: agreement with MS labels in four uninvolved settlements 66–81 % (MS itself under-detects, so true accuracy lies above the agreement figure).
- Visual QA: random imagery crops in AD DARIZ (an MS-gap zone) — all BUILT=1 samples show buildings; BUILT=0 samples dominantly vacant.
- Strongest validation: in the former NO-COVERAGE settlements, detected built plots ≈ census-implied dwellings (built/implied = 0.91 AD DARIZ, 0.96 AL ARAQI, 0.98 AL AYNAYN).

## Results (key settlements)
| Settlement | Plots | Built (final) | % built | Built / implied dwellings 2024 |
|---|---|---|---|---|
| IBRI | 17,032 | 8,924 | **52.4 %** | 0.80 |
| AD DARIZ | 5,526 | 1,799 | 32.6 % | 0.91 |
| AL ARAQI | 3,806 | 1,714 | 45.0 % | 0.96 |
| AL AYNAYN | 1,823 | 747 | 41.0 % | 0.98 |
| AT TAYYIB | 8,755 | 945 | 10.8 % | 1.69 |
| Whole cadastre | 61,272 | 17,663 | 28.8 % | — |

Full table: [`A3_built_final.csv`](A3_built_final.csv).

## Implications
- **A1/A2 conclusions harden**: IBRI is half built already; with 52 % of plots consumed, its remaining capacity (~8,100 plots ≈ 48k persons at OR 6.0) is materially less than its projected 2038–2055 growth — the spillover reallocation (A2) is not optional.
- AT TAYYIB confirmed ~89 % vacant → the primary growth sink, now with a defensible number.
- Stub-out planning can now be plot-specific: `BUILT_FIN = 0` plots are the future-connection inventory per zone.

## Caveats & anomalies
- Screening grade (~80 % per-plot confidence): use for zone aggregates and planning, not per-plot legal status. MoHUP building records remain the authoritative close-out (data register).
- **BAT anomaly**: 2.4 % built vs 426 implied dwellings — village likely outside the kmz polygon (and UNESCO archaeological area); resolve with corrected boundaries.
- Small low-density zones show built/implied > 1.5 (AL JAHLI, SAYH AL MASARRAT, AL QURAYN, AT TAYYIB): either mild over-detection (walls/farm structures) or R0 under-allocates their current population — flag for the model calibration against water billing.
- Esri imagery date is not uniform across the mosaic; treat "built" as "built as of latest available imagery".
