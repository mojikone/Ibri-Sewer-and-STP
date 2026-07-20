# DATA INVENTORY & QUALITY FLAGS
Project CRS: **EPSG:32640** (WGS84 / UTM 40N). QGIS project: `Hydraulic/QGIS/QGIS 2621 ibri sewer stp.qgz` (open, MCP-connected).

| Layer | Source | Features | Key facts | Flags |
|---|---|---|---|---|
| NSA_DEM | Hydraulic/Terrain/NSA_DEM.tif | 44567×44172 @ 4 m | z −41.7…3029.4 m; covers 178×177 km | **Rough DSM (user-confirmed), survey ongoing → screening only, never invert design. Clip before processing (2G px).** |
| Project_boundary | SHP/MoHUP_DATA | 1 poly | 439.8 km² single part | — |
| IBRI STP | SHP/IBRI STP | 1 point | E444387 N2563352, ground ≈327.6 m | **EXISTING STP** (user-confirmed). New STP siting = consultant scope |
| Landuse | SHP/Landuse | 76,146 poly | inside boundary: Res 43,722 (32.2 km²), Agri 4,310 (36.8), NotClass 3,991 (7.5), Comm 3,057 (2.4), Gov 2,976 (16.3), Ind 466 (0.9) | class field `NewLUClass` |
| MoH_Plots | SHP/MoHUP_DATA | 61,272 poly | Arabic LANDUSE field, BUILTTYPE, SHAPE_Area | overlaps Landuse; use as secondary/occupancy evidence |
| Road_Centercline | SHP/Road centerline | **57,584** lines, 10,894 km | regional 137×104 km extent; only `OldstNm` populated | **.shx stale → provider reports 0 features — repair (ogr2ogr rewrite). No hierarchy attributes. Dual carriageways = two parallel polylines (user) → detect arterials geometrically (parallel pair + betweenness), then merge** |
| Streams NSA 2m | SHP/Streams | 20,318 lines | `STRM_VAL` threshold value; regional extent | derived from DEM (DSM!) — wadi lines indicative |
| Layout template | Hydraulic/QGIS/Layout template.qpt | — | report map template (from previous project) | use for all report maps |
| Sample report | Data/sample report/ | **EMPTY** | — | **GAP-4: no styling source; ask user** |
| Figures F1–F3 | Data/Drawing & Figures | 3 PDFs | project location, existing sewer, design-stage boundaries | F2/F3 define As-built vs new-design areas — read before zoning finalisation |

## Terrain intelligence (computed 2026-07-20, DSM-grade)
- STP ground ≈ **327.6 m**; main Ibri cluster (47,520 plots, 40.5 km²) median ≈ 374.3 m → median available straight-line grade to STP ≈ **3.6 m/km**; p25 ≈ 3.2.
- Gravity viable for ~95% of plots (Smin trunk ≥900 mm = 0.75 m/m‰, Tab 11). Low-grade (<1 m/km): ~2.8% of plots; below STP+5 m: ~5.4% → SLS candidate pockets.
- Profile STP→cluster centroid monotonic rise, no adverse grade over first ~9 km.
- Settlement clusters: #1 main town 47.5k plots; #2 east 1,144 plots @31.7 km, +164 m (satellite solution question); #3 565 @21 km; #4 487 @10 km NW (+14 m); #6 52 plots **−9.7 m below STP** (pumping or deferred).
