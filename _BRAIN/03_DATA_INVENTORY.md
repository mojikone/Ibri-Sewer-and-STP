# DATA INVENTORY & QUALITY FLAGS
Project CRS: **EPSG:32640** (WGS84 / UTM 40N). QGIS project: `Hydraulic/QGIS/QGIS 2621 ibri sewer stp.qgz` (open, MCP-connected).

| Layer | Source | Features | Key facts | Flags |
|---|---|---|---|---|
| NSA_DEM | Hydraulic/Terrain/NSA_DEM.tif | 44567×44172 @ 4 m | z −41.7…3029.4 m; covers 178×177 km | **DTM (user-corrected 2026-08-14; earlier noted as DSM — wrong). Rough, survey ongoing → screening only, never invert design. Contains NO buildings → cannot derive built/vacant status. Clip before processing (2G px).** |
| Project_boundary | SHP/MoHUP_DATA | 1 poly | 439.8 km² single part | — |
| IBRI STP | SHP/IBRI STP | 1 point | E444387 N2563352, ground ≈327.6 m | **EXISTING STP** (user-confirmed). New STP siting = consultant scope |
| Landuse | SHP/Landuse | 76,146 poly | inside boundary: Res 43,722 (32.2 km²), Agri 4,310 (36.8), NotClass 3,991 (7.5), Comm 3,057 (2.4), Gov 2,976 (16.3), Ind 466 (0.9) | class field `NewLUClass` |
| MoH_Plots | SHP/MoHUP_DATA | 61,272 poly | Arabic LANDUSE field, BUILTTYPE, SHAPE_Area | overlaps Landuse; use as secondary/occupancy evidence |
| Road_Centercline | SHP/Road centerline | **57,584** lines, 10,894 km | regional 137×104 km extent; only `OldstNm` populated | **.shx stale → provider reports 0 features — repair (ogr2ogr rewrite). No hierarchy attributes. Dual carriageways = two parallel polylines (user) → detect arterials geometrically (parallel pair + betweenness), then merge** |
| Streams NSA 2m | SHP/Streams | 20,318 lines | `STRM_VAL` threshold value; regional extent | derived from DEM (DSM!) — wadi lines indicative |
| Layout template | Hydraulic/QGIS/Layout template.qpt | — | report map template (from previous project) | use for all report maps |
| Sample report | Data/sample report/Sample.docx | 1 docx | styling shell for R1+ reports | GAP-4 CLOSED — used by `W2/report/make_report_r1.py` |
| Figures F1–F3 | Data/Drawing & Figures | 3 PDFs | project location, existing sewer, design-stage boundaries | F2/F3 define As-built vs new-design areas — read before zoning finalisation |
| **PAM-GUD-202** Water & TSE v1.0 | `_STANDARDS/` (in repo) + Data/ | 177 pp | water/TSE networks: velocities, head loss, pressures, PS, reservoirs, tankers | criteria extracted → 02 §12b (`G2-p##`) |
| Inception R0 package | Data/Received/2621/inception report - R0/ | docx+pdf+xlsx+kmz+dwg | **`Ibri Sewer Demand R0 2026 08 03.xlsx` = NCSI pop (Ibri 183,564 @2024) + full demand chain**; boundary kmz/dwg | R0 adopted values → 02 §12c; reconcile any new calc against it |
| Kick-off presentation + as-built jpgs | Data/Received/2621/ | pptx/pdf + 2 jpg | kickoff slides; `STP_As_Built.jpg`, `Sewerage Network.jpg` | jpgs = leads for GAP-6/GAP-7 (existing STP + network) — not yet read |
| Terrain 0.5 m blend | Data/Terrain/Sat_0p5m/ibri_0p5_blend.tif (+5 m ibri_blend.tif, VRT) | 151k×148k @ 0.5 m, float32, EPSG:32640 | **terrain (user-confirmed 2026-08-14), NOT imagery** — bare-earth blend covering full boundary | no buildings; folder name "Sat_" is misleading |
| Settlement boundaries (26) | Data/Received/2621/inception report - R0/Final_Boundary_IBRI.kmz | 26 town polygons + labels | R0 settlement zones incl. IBRI, AD DARIZ, AL ARAQI | TANAM/SATWAH/AL MAKHTIBYAH polygons mismatch their plot areas; 24 of 50 workbook settlements missing |
| **Built/vacant status** | — | — | **NO source on disk**: cadastre status fields empty, both DEMs are DTMs (no buildings), no imagery file | options: MoHUP records (kickoff), MS Building Footprints download, imagery digitization |

## F2 read-off (user screenshot 2026-07-20 — verify against GIS when provided)
- Existing sewer system serves the **NE district** (Al Araqi area, ~466–471E / 2574–2581N approx) — yellow network inside blue boundary.
- An **existing trunk/TE corridor runs from that district SW to the existing STP** (long blue-outlined strip through town center ~449E,2567N). New trunk concept must assess its route, capacity and condition (TOR: integration + hydraulic assessment of existing systems).
- Existing STP sits inside its own blue boundary at SW. Titleblock: Nama WS, "Figure No. 2 Existing Sewer and TE Systems", DRWG GEN-AM-F2-002-0.
- W2+ implication: NE zones overlap the already-served area → those zones' flows partly existing customers, not new connections; trunk options should evaluate reuse/paralleling of the existing corridor.

## Terrain intelligence (computed 2026-07-20, DSM-grade)
- STP ground ≈ **327.6 m**; main Ibri cluster (47,520 plots, 40.5 km²) median ≈ 374.3 m → median available straight-line grade to STP ≈ **3.6 m/km**; p25 ≈ 3.2.
- Gravity viable for ~95% of plots (Smin trunk ≥900 mm = 0.75 m/m‰, Tab 11). Low-grade (<1 m/km): ~2.8% of plots; below STP+5 m: ~5.4% → SLS candidate pockets.
- Profile STP→cluster centroid monotonic rise, no adverse grade over first ~9 km.
- Settlement clusters: #1 main town 47.5k plots; #2 east 1,144 plots @31.7 km, +164 m (satellite solution question); #3 565 @21 km; #4 487 @10 km NW (+14 m); #6 52 plots **−9.7 m below STP** (pumping or deferred).
