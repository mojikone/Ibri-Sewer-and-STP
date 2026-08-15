# A5 — Cadastre Gaps and z18 Re-check (Built Classification v3)
**W3 analysis · 2026-08-15 · executes the user-confirmed order: (a) unparceled buildings, (b) z18 re-check**

## A5a — Buildings without any cadastral plot
User-reported (QGIS review): constructed buildings with no MoH plot polygon. Confirmed and quantified:
- **2,799 buildings** (MS footprints ≥25 m² with <15 % overlap on any plot), total roof area 380,381 m².
- Distribution: IBRI 1,325 · TANAM 341 · AL JIBAYYAH 323 · AL MAKHTIBYAH 156 · SUWAYDA AL MA 119 · AD DIBAYSHI 102 · rest smaller.
- Layer: [`Unparceled_Buildings.shp`](../shp/) (red auto-style, `AREA_M2`, `SETTLEMENT`).
- Implication: the plot-based ceilings slightly *understate* current occupation; these structures carry demand but no parcel. **MoHUP cadastre completion added to the kickoff data register.** Only exists where MS coverage exists — the imagery route (A5b) does not fill this layer.

## A5b — z18 re-check of planned-classified plots
User-reported: built houses classified as planned (sparse desert-edge areas). Fixed by a second pass at 0.6 m/px:
- 12,237 z18 tiles fetched for all 43,609 `BUILT_FIN = 0` plots; classifier retrained at z18 scale — **train accuracy 95.9 %** (vs 88.8 % at z17).
- Flip rule: planned→built at probability ≥ 0.6; **agricultural plots require ≥ 0.8** (palm-row texture is the main false-positive mode, caught in visual QA); 198 agri flips blocked.
- **2,736 plots flipped** planned→built. New layer: [`MoH_Plots_built_v3.shp`](../shp/) with `PROB18` (recheck probability, filterable), `SRC` (1=MS footprint, 2=z17 imagery, 3=z18 recheck), same black/white QML.

## Result v3 (key settlements — full table [`A5_built_v3.csv`](A5_built_v3.csv))
| Settlement | % built v2 → v3 | built/implied dwellings |
|---|---|---|
| IBRI | 52.4 → **57.2 %** | 0.87 |
| AL ARAQI | 45.0 → 51.8 % | 1.11 |
| AL WAHRAH | 15.6 → 23.1 % | **0.99** (undercount fixed) |
| AD DARIZ | 32.6 → 40.7 % | 1.14 |
| AT TAYYIB | 10.8 → 12.6 % | still ~87 % vacant |
| Whole cadastre | 28.8 → **33.3 %** (20,399 plots) | — |

## Standing caveats
- Screening grade; ratios >1 in low-density zones = multi-structure plots and/or R0 under-allocation — calibrate against billing data.
- Step (c) (compound-wall tracing) held back per the agreed order — only worth running where (a)+(b) leave holes the user's review flags.
- Capacity effect: IBRI at 57 % built leaves ~7,300 vacant plots ≈ 44k persons at OR 6.0 — now *below* the ~43k spillover demand by 2055 (A2): IBRI effectively fills within the design horizon.
