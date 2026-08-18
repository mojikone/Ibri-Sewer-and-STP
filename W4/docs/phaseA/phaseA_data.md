# Input Data Inspection — W4 Test-Boundary Network Design (Ibri)

All paths verified present. Python env used: system 3.12.10 with geopandas 1.1.4 / pyogrio 0.13.0 / rasterio 1.5.0 / shapely 2.1.2 (osgeo bindings absent — not needed). All scratch scripts written to the session scratchpad only; no project file touched.

## 0. CRS consistency

| Layer | CRS | Matches EPSG:32640 |
|---|---|---|
| roads_study.shp | EPSG:32640 | yes |
| MoH_Plots.shp (raw) | EPSG:32640 | yes |
| MoH_Plots_class_v4.shp | EPSG:32640 | yes |
| Netwrok desing test boudary.shp | EPSG:32640 | yes |
| IBRI_0p5_VRT2.vrt | EPSG:32640 | yes |

No CRS mismatch anywhere.

## A. Roads — `D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W1/shp/roads_study.shp`

| Property | Value |
|---|---|
| Features | 17,959 |
| Geometry | LineString — 100% single-part, 0 empty/null |
| Extent | 432863.1, 2556789.0 → 478392.0, 2583027.4 |
| Sidecars | .cpg (1252), .dbf, .prj, .shx |

Fields (type, 3 samples, null count of 17,959):

| Field | Type | Samples | Nulls |
|---|---|---|---|
| OBJECTID | int64 | 358089, 358090, 358092 | 0 |
| Id | int64 | 526625, 526626, 526628 | 0 |
| StrID | int64 | 177392, 177333, 177492 | 0 |
| DataQlt / DataPvd / DtPvdCls / Dir / OSStr | object | (all null) | 17,959 each |
| DtPvdPid | int64 | 0 | 0 (constant 0) |
| Created / Updated | datetime | 2019-08-09, 2019-08-13, 2019-08-20 | 0 |
| Deleted | datetime | 1899-12-30 (sentinel) | 0 |
| OldstNm | str | 'Tanam-Qarat Al Milh Road', 'Tanam-Kabshat  Road', 'Ayyash  Road' | 16,563 |
| Lenght | float64 | 0.0 | 0 — **all zeros, unusable; recompute from geometry** |

## B1. Plots raw — `D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/SHP/MoHUP_DATA/MoH_Plots.shp`

| Property | Value |
|---|---|
| Features | 61,272 |
| Geometry | 61,270 Polygon + **2 MultiPolygon**; 0 invalid, 0 empty |
| Extent | 433153.0, 2558276.7 → 476938.0, 2581494.8 |
| Sidecars | .cpg (UTF-8), .dbf, .prj, .sbn, .sbx, .shx, .xml |

~80 fields, the majority entirely null. Populated/relevant ones:

| Field | Type | Samples | Nulls |
|---|---|---|---|
| OBJECTID | int64 | 1104405, 1104406, 1104407 | 0 |
| LANDUSE | str (Arabic) | 'زراعى', 'حكومي', 'سكني/تجاري' | 39,838 |
| VILLAGE_EN | str | 'AL SULAIF', 'ALQURAIN (P.A)', 'AL JUBAYYAH' | 43,557 |
| WILAYAT_EN | str | 'WILAYAT IBRI' | 369 |
| PLOT_NO | str | '105', '115', '116' | 18,192 |
| PAIN | str | '5-13-104-03-224', … | 43,556 |
| SB_FRONT / SB_BACK / SB_SIDE | str | '8 م', '5 م', '3 - 3 م' | ~50,000 each |
| BLDG_HT / BT_AREA | str | '2 م', '30%', '40%' | ~50,000 each |
| SHAPE_Leng / SHAPE_Area | float64 | 901.86 / 46544.86 … | 0 |
| BUILTTYPE | int32 | 2, 1, 0 | 0 |
| COMMENTS | str | 'OPEN AREA, FARM', 'OPEN AREA', 'FARM' | 44,351 |
| FILE_NAME | str | 'ARAQI.dwg', 'IBRI-NORTH.dwg', 'IBRI-SOUTH.dwg' | 369 |

Data-quality note: some Arabic values in the *source data itself* are double-encoded mojibake (e.g. NOTES sample 3 'ÇáÈÇáæÚÉ ÏÇÎá ÍÏæÏ ÇáÞØÚÉ' = cp1256 bytes mis-decoded upstream; same in BT_AREA_IW, HT_BLDG_IW). Not a read-encoding issue on our side — it is baked into the DBF.

## B2. Plots classified — `D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W3/shp/MoH_Plots_class_v4.shp`

| Property | Value |
|---|---|
| Features | 61,272 (1:1 with raw) |
| Geometry | 61,270 Polygon + 2 MultiPolygon; 0 invalid |
| Extent | identical to raw |
| Sidecars | .dbf, .prj, .qml, .shx — **no .cpg** |

| Field | Type | Samples | Nulls |
|---|---|---|---|
| OBJECTID | int64 | 1104405, 1104406, 1104407 | 0 |
| LANDUSE | str | mojibake on default read; correct Arabic ('زراعى', 'حكومي', 'سكني/تجاري') when read with `encoding='utf-8'` | 39,838 |
| VILLAGE_EN | str | 'AL SULAIF', 'ALQURAIN (P.A)', 'AL JUBAYYAH' | 43,557 |
| CLASS | str | 'A', 'P', 'B' — whole-layer counts: P 36,945 / B 17,961 / A 6,366; no nulls, no other values | 0 |
| BUILT_FIN | int32 | 0, 1 — whole-layer: 0→40,873, 1→20,399 | 0 |
| VEGFRAC | float64 | 0.201, 0.507, 0.638 | 0 |
| PROB18 | float64 | 0.05, 0.01, 0.006 | 0 |
| AREA_M2 | float64 | 46544.9, 811.1, 829.2 | 0 |

**Missing .cpg**: the DBF is UTF-8 but has no codepage sidecar, so default reads decode LANDUSE as latin-1 mojibake. Fix in the design pipeline: pass `encoding='utf-8'` (or add a .cpg saying UTF-8 — not done here, task is read-only). CLASS/BUILT_FIN/numerics are ASCII and unaffected.

## C. Test boundary — `D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/SHP/temp/Netwrok desing test boudary.shp`

| Property | Value |
|---|---|
| Features | 1 Polygon (single-part, explode → still 1) |
| CRS | EPSG:32640 |
| Fields | `id` (float64) — null |
| Extent | 449901.0, 2566736.6 → 451984.3, 2570846.0 (~2.08 × 4.11 km) |
| Area | **551.45 ha** |
| Centroid | **E 450836.6, N 2569013.8** |
| Validity | **INVALID — ring self-intersection at (450430.591, 2567539.561)** |

`make_valid` returns GeometryCollection(Polygon + MultiLineString) with **zero area change** — the defect is a degenerate pinch/spike, not a bowtie splitting the area. All analyses below used the repaired polygon part.

## Clip analysis inside boundary

### Roads
| Metric | Value |
|---|---|
| Original road features intersecting boundary | 1,383 |
| Clipped line parts | 2,047 |
| **Total road length inside boundary** | **98,045 m (98.04 km)** |
| Clipped segment length | min 0.0 / median 26.7 / mean 47.9 / max 1082.8 m |

Nodedness (checked on the 1,383 original intersecting features, endpoints rounded to mm):

| Check | Result |
|---|---|
| Unique endpoints | 1,012 — 917 shared by ≥2 segments, 95 degree-1 |
| Endpoint degree histogram | {1: 95, 2: 199, 3: 600, 4: 117, 5: 1} |
| Collinear overlapping pairs (duplicate lines) | **0** |
| Crossings/touches NOT at shared endpoints (un-noded) | **0** |
| Connected components (endpoint graph, originals) | **1** — fully connected |
| Connected components (clipped lines) | 1 |

The road network in the test area is properly noded, has no duplicate/overlapping geometry, and is a single connected component. The 95 degree-1 nodes are culs-de-sac and boundary exits — normal. Caveat: dual carriageways drawn as *parallel offset* lines (project rule 7) would not be caught by the overlap test; the 117 degree-4 junctions suggest a grid, not necessarily duals — visual/corridor check still required per doctrine.

### Plots (class_v4)
| Metric | Value |
|---|---|
| Plots with representative point inside | **2,825** (2,830 intersect at all) |
| CLASS = B (built) | **2,217** |
| CLASS = P (planned) | **522** |
| CLASS = A (agricultural) | **86** |
| Empty/null LANDUSE inside | **2,417 of 2,825 (85.6%)** |
| BUILT_FIN inside | 1 → 2,276; 0 → 549 |
| Plot area (m²) inside | min **1** / median 600 / mean 830 / max 44,997 |
| MultiPolygon plots inside | 0 (both layer MultiPolygons are elsewhere) |

## D. Terrain — `D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt`

| Property | Value |
|---|---|
| Driver | VRT, 1 band, Float32 |
| CRS | EPSG:32640 |
| Size | 151,370 × 148,490 px |
| Pixel size | 0.5 × 0.5 m |
| NoData | -9999 |
| Full extent | 417800, 2534825 → 493485, 2609070 |
| Covers test boundary | **Yes, fully** |

Referenced sources (relative to VRT, layered in order — later wins where valid):

| Source | Exists | Size | Role |
|---|---|---|---|
| `ibri_blend.tif` | yes | 230 MB | 15,137×14,849 px = 5 m grid, upsampled 10× bilinear as base fill |
| `ibri_0p5_blend.tif` | yes | 7,399 MB | 151,353×148,487 px native 0.5 m overlay (offset 9,2 px) |

### Elevation sampled inside boundary (22,058,157 px)
| Metric | Value |
|---|---|
| NoData pixels inside | **0 (0.000%)** — no holes |
| Min / Max | 351.18 / 405.91 m |
| Mean ± std | 364.20 ± 7.00 m |
| Percentiles | p1 352.5, p5 353.9, p25 359.3, p50 363.9, p75 367.6, p95 377.1, p99 385.7 |

~55 m total relief over 551 ha, falling terrain — gravity-friendly.

### Slope sanity check (gradient magnitude, %)
| Scale | Median | p95 | Mean | Max |
|---|---|---|---|---|
| Native 0.5 m | 2.46 | 16.30 | 4.82 | 590.0 |
| 5 m block-averaged | 2.37 | 16.08 | 4.66 | 134.2 |

Median/p95 stable across scales → the 16% p95 is real local terrain (wadi banks/edges), not pixel noise; the 590% native max is isolated edge artifacts (expected in a satellite-derived 0.5 m surface — walls/buildings/vegetation edges may persist locally). Median ~2.4% is comfortable for gravity sewer design.

## Flags for automated network design

| # | Severity | Issue | Consequence / required handling |
|---|---|---|---|
| 1 | **Blocker until handled** | Test boundary polygon is INVALID (ring self-intersection at 450430.59, 2567539.56); `make_valid` yields a GeometryCollection | Any clip/overlay/mask without repair can fail or silently drop area. Pipeline must `make_valid` + extract the Polygon part (area unchanged, 551.45 ha) as step zero |
| 2 | High | `MoH_Plots_class_v4.shp` has **no .cpg** — LANDUSE reads as mojibake by default | Force `encoding='utf-8'` on every read (or add a .cpg outside this read-only task). CLASS/BUILT_FIN unaffected |
| 3 | Medium | Roads `Lenght` field is all zeros | Never use the attribute; compute lengths from geometry |
| 4 | Medium | Clipping roads to boundary produces degenerate slivers (min part length 0.0 m) | Filter parts below a tolerance (e.g. <0.5 m) after clip |
| 5 | Medium | 85.6% of plots inside boundary have empty LANDUSE | Load allocation must key on CLASS/BUILT_FIN (per settled doctrine), not LANDUSE |
| 6 | Low | 1 m² sliver plots exist inside boundary (min area 1 m²) | Guard per-plot flow allocation against zero/sliver areas |
| 7 | Low | 2 MultiPolygon plots in the full 61,272-plot layer (none inside the test boundary) | Irrelevant for W4 test area; explode if the pipeline later runs study-wide |
| 8 | Low | Raw MoH_Plots has source-side double-encoded Arabic in NOTES/BT_AREA_IW/HT_BLDG_IW | Cosmetic; do not attempt auto-repair |
| 9 | Info | Dual-carriageway detection: 0 coincident overlaps found, but parallel-offset duals are not detectable by overlap tests | Apply the existing W1 dual-detection (s1_roads_graph.py) corridor logic before trunk routing |
| 10 | Info | Terrain is a 0.5 m satellite-derived surface (Sat_0p5m), not the doctrine-authoritative `DTM_terrain_mask.tif` 5 m DTM; isolated slope spikes to 590% at native res | Confirm which surface is authoritative for invert design in this W4 test, or smooth/aggregate before profiling |

**Clean bill**: CRS uniform EPSG:32640 across all five inputs; roads single-part, fully noded, one connected component, no overlaps; plots 1:1 raw↔classified with valid geometries; terrain has zero nodata inside the boundary and fully covers it.

Scratch scripts (read-only analysis, reproducible): `C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\c2458709-6ed2-41d1-83f3-e515ea91aff4\scratchpad\inspect_vectors.py`, `...\clip_analysis.py`, `...\terrain_analysis.py`.