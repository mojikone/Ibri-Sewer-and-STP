# W1–W3 Pipeline Code Inventory — Reusable Building Blocks for W4

Scope: all 23 Python scripts under `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\{W1,W2,W3}` were read in full. Every claim below is [Certain] (read from source) unless tagged otherwise.

## 0. Library stack (common to everything)

- **pyshp (`shapefile`)** — primary vector I/O (read AND write). geopandas appears only in the three newest scripts (`W3/py/a7_load_alloc.py`, `a8_load_calc_xlsx.py`, `towns_from_kmz.py`).
- **shapely** (2.x — `STRtree.query(..., predicate=...)` API), **networkx** (graphs/Dijkstra), **rasterio** (raster sampling, windows, `geometry_mask`, warp transform used as the universal CRS reprojector — pyproj is never imported directly), **scipy** (`cKDTree`, `Voronoi`), **numpy**, **matplotlib Agg** (charts, profiles, PNG maps), **openpyxl** (live-formula workbook), **python-docx** (report), **PIL** (tile mosaics), **urllib + ThreadPoolExecutor** (tile download).
- Documented install line (`_SETUP/ENVIRONMENT.md` §2): `pip install networkx shapely pyshp rasterio numpy scipy matplotlib pymupdf pdfplumber pypdf python-docx` — geopandas/openpyxl were added later and are NOT in that line (stale doc, minor).
- Style: flat imperative scripts, absolute Windows path constants at top, `log()` with elapsed seconds, no functions/CLI/config separation. Nothing is packaged as an importable module — "reuse" today means copy-paste.

---

## 1. Road network graph building / cleaning

### `W1/py/s1_roads_graph.py` (118 lines)
Builds the noded road graph from raw road centerlines and **detects** dual carriageways.
- **Does**: reads `W1/shp/roads_study.shp` → explodes parts → `unary_union` to node all intersections → graph with 0.5 m node snap (`nkey` rounding) → largest connected component → k-sampled edge betweenness (k=600, seed 42) → dual-carriageway detection → writes `W1/shp/roads_graph.shp` with fields `LEN, BTW, DUAL, ARTERIAL` + hand-written `.prj` (EPSG:32640 WKT literal).
- **Reusable blocks**:
  - Noding pattern: `unary_union(lines)` → filter `length > 0.1` (lines 33–38).
  - `nkey()` snap-to-grid node keying (lines 40–41).
  - **Dual-carriageway detector** (lines 64–97): for edges ≥40 m, STRtree query on 45 m buffer, bearing difference ≤12°, midpoint-to-candidate distance 6–45 m → flag both edges `DUAL`. This is the working-rule-7 primitive.
  - Arterial classification: top-10% betweenness OR dual (lines 99–111).
- **Hardcoded**: SNAP=0.5 m; dual thresholds (40 m min length, 12°, 6–45 m offset); betweenness quantile 0.90; input path `W1/shp/roads_study.shp` (itself a study-area clip whose creation script is not in the repo — [Likely] made ad hoc in QGIS/session).

### `W2/py/s3_w2_pipeline.py` lines 37–83 — **dual-carriageway COLLAPSE** (the working-rule-7 implementation to reuse)
- Reads W1's `roads_graph.shp` (keeps DUAL/ARTERIAL flags), then: collect all nodes touched by DUAL edges → `cKDTree.query_pairs(35.0)` → union-find merge of node clusters within 35 m → remap each cluster to its centroid → rebuild graph; twin cross-links vanish (`a2 == b2`), parallel twins collapse via keep-shortest-duplicate-edge rule. Result: one routing corridor per dual road.
- **Caveat for W4**: edge geometry keeps the ORIGINAL carriageway polyline while endpoints are remapped, so collapsed-edge geometry does not exactly touch the merged node coordinates — fine for screening maps, not fine for a real pipe layout with manholes. W4 needs a geometry re-anchoring step that W2 never built.

## 2. Terrain / raster sampling

- **Point sampling** (`s3_w2_pipeline.py` lines 85–100, near-identical in `s2_trunk_zones.py` 56–75): open raster once, `ds.read(1)` whole band into memory, `zval(x,y)` via `ds.index()` array lookup with nodata guard, then fill missing node elevations with neighbor mean (graph-aware gap fill). Simple and fast; whole-band read was fine for the 5 m DTM but **will not scale to the 0.5 m VRT** (study-area at 0.5 m is tens of GB) — W4 must switch to windowed reads (`rasterio.windows.from_bounds`, pattern already exists in `W3/py/classify_built.py::feats()` and `vegfrac.py`).
- **Polygon-masked window stats** (`W3/py/classify_built.py` lines 34–60 `feats()`, `W3/py/vegfrac.py` lines 26–43): window read around geometry bounds + `rasterio.features.geometry_mask` + per-plot statistics. This is the reusable "sample raster under geometry" primitive.
- **No along-line sampling at fixed step exists** — elevation is only ever sampled at graph nodes. A profile-along-polyline sampler (every 5–10 m for invert design) must be written.
- **STALE PATHS — elevation**: `W2/py/s3_w2_pipeline.py` line 16 hardcodes `Hydraulic\Terrain\DTM_terrain_mask.tif` (5 m); `W1/py/s2_trunk_zones.py` line 57 uses `W1/temp/DEM_study.tif` (NSA DSM clip). Both superseded 2026-08-18 by **`D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt`** (0.5 m; confirmed present on disk alongside `ibri_blend.tif`, `ibri_0p5_blend.tif`). Any W4 script must take the VRT; note also `_BRAIN` docs and CLAUDE.md still name the 5 m DTM as "elevation source" (rule 6) — the doctrine files lag the change.

## 3. Trunk routing and flow accumulation

`W2/py/s3_w2_pipeline.py` (lines 133–173) — the mature version; `W1/py/s2_trunk_zones.py` (lines 114–163) is the superseded draft.
- **Two-tree design worth keeping**: (a) *aesthetic tree* — undirected Dijkstra from STP with weight `len * rf` where rf = 0.55 dual / 0.70 arterial / 1.0 minor (prefers wide corridors); (b) *hydraulic tree* — DiGraph with directional climb penalty `w = len + 300·max(0, Z[u]−Z[v])` (KCLIMB=300) used for gravity screening. W1 line 115–121 documents WHY undirected Dijkstra can't orient adverse grade — the DiGraph fix in W2 is the answer.
- **STP connector**: KD-tree nearest node, add synthetic edge STP→network (lines 124–131). STP coords hardcoded `(444387.0, 2563352.5)`.
- **Flow accumulation**: plot weights routed down shortest-path trees; `acc[m] += w` for every node m on `hpaths[n]` (lines 182–185); trunk edges accumulate `CUMPLOTS` the same way (164–168). It is plot-count accumulation, not flow accumulation — flows are computed only per zone, never per pipe. **W4 needs per-pipe design flow (population→Qpeak per link), which does not exist.**
- **Seed/outlet selection**: 1 km-cell plot-weight aggregation, threshold ≥60 plots, ≥2500 m mutual separation (lines 143–156). Seeds double as zone outlets — outlets are demand hotspots, NOT hydraulic low points; acceptable for screening, wrong primitive for W4 network design.

## 4. Zone / outlet handling

`W2/py/s3_w2_pipeline.py`:
- Territories: `multi_source_dijkstra` from all seeds, `owner = first node of path` (lines 176–179) — network-distance Voronoi, exactly working rule 8.
- Zone polygons: scipy `Voronoi` over graph nodes with 4 far-corner dummy points, cells <4 km² kept, dissolved by owner, clipped to built envelope (`unary_union` of every 3rd plot-centroid buffered 200 m, then +120/−120 smoothing), parts >5 ha kept (lines 233–261). Replaces W1's cruder buffer-hull approach (`s2_trunk_zones.py` 238–259).
- Zone stats/flows per zone: GUD-201 chain + `zone_flows.csv` (lines 263–293).

## 5. SLS placement logic

`W2/py/s3_w2_pipeline.py` lines 181–231 — implements working rule 9 end-to-end:
- Invert-accumulation gravity screen per node route: start invert = ground − 1.9 m (`MIN_COVER_INV`, = 1.3 cover + 0.6 pipe/bed, G203-p33); descend at Table-11 minimum gradient chosen by accumulated upstream plots (`smin_for()`: 0.0050/0.0027/0.00155/0.0010/0.00075 for <150/<400/<1500/<5000/≥5000 plots — a plots→DN class proxy, G203-p29); invert rides no shallower than min cover when ground falls faster (`inv = min(inv − L·s, Z[b] − 1.9)`); node fails when depth > `MAX_COVER` 12 m.
- Failed nodes → connected components → drop pockets <50 plots (`SLS_MIN_PLOTS`) → one SLS at lowest node of each component → per-SLS Qpeak (Peltier) → cascade consolidation: absorb any station within 1500 m of a larger kept one.
- Note: the per-SLS wastewater formula (line 213) algebraically equals the zone formula but skips infiltration — consistent enough for screening.

## 6. Design-criteria constants (repeated verbatim in W1 s2, W2 s3, W3 a7, W3 a8 — four copies, no shared module)

`LPCD=164` (G1-p60), `ND_RATIO=0.22`, `GOV_RATIO=0.14` (G1-p60), `RET_DOM=0.85`, `RET_ND=0.54` (G1-p71), `INFIL_L_D_KM=720` (G1-p72), `PF_CAP=5.0` + Peltier `1.5+1/√Qm` (G1-p72), `MAX_COVER=12`, `MIN_COVER_INV=1.9` (G203-p33), Table-11 `smin_for()`, `OR_ASSUMED=6.0`, `PROP_PER_PLOT=1.0` ([GAP-5], unconfirmed). W4 should hoist these into one criteria module; also note A7 superseded the flat per-capita ND+Gov uplift — **the current load-allocation doctrine is A7's** (ND+Gov placed on non-residential plot area), and W2's `s3` still contains the old method.

## 7. Load allocation / calculation (current doctrine)

- **`W3/py/a7_load_alloc.py`** (135 lines, geopandas): corrected allocation — domestic per residential plots, project-wide ND+Gov volume distributed over non-residential plot area per zone; Arabic-LANDUSE handling incl. the `fix()` latin-1/utf-8 mojibake repair (needed for every read of `MoH_Plots.dbf` LANDUSE); `peaking()` helper. Reads `W2/shp/zones.shp`, `W3/shp/MoH_Plots_class_v4.shp`, `W2/report/zone_flows.csv` → `W3/analysis/A7_load_alloc.csv`. Directly reusable for W4 node-load assignment.
- **`W3/py/a8_load_calc_xlsx.py`** (284 lines, openpyxl): the live-formula workbook generator — defined names from an Inputs sheet, full GUD-201 chain as Excel formulas, By-Town-2055 A7 allocation, Saturation sheet. The styling/`header`/`widths`/defined-name pattern is the house template for any W4 calculation deliverable. Depends on `Hydraulic/SHP/Towns/Towns.shp` and `W3/analysis/_nonres_area_by_town.csv`.
- **`W3/py/towns_from_kmz.py`** (239 lines, geopandas): KMZ→Towns.shp with population series 2023–2100, cross-checked against the R0 workbook; robust KML popup-table parser, dissolve, UTF-8 DBF + .cpg. The reusable piece is the pattern of hard cross-checks (`raise SystemExit` on mismatch).
- Settlement/ceiling/spillover analytics: `W3/py/zone_capacity.py`, `a2_spillover.py`, `finalize_w3.py`, `a3_built_stats.py` — inputs to W4 phasing, not network-design code. Note they parse the KMZ zones inline (4 copies of the same KML parsing block).

## 8. Plot classification stack (inputs W4 will consume, not re-run)

- `W3/py/intersect_fp.py` — MS building footprints × plots → `BUILT_MS` (`W3/shp/MoH_Plots_built.shp`); STRtree bulk `query(predicate="intersects")` + overlap-area pattern.
- `W3/py/classify_built.py` — imagery texture features + hand-rolled logistic regression → `MoH_Plots_built_v2.shp`.
- `W3/py/z18_fetch.py` / `z18_recheck.py` / `a5b_finalize_v3.py` — z18 recheck at 0.6 m/px, per-landuse flip thresholds → `MoH_Plots_built_v3.shp` (+ tile-cache `crop()` mosaic-on-the-fly reader worth reusing).
- `W3/py/vegfrac.py` + `a6_landuse_class.py` — excess-green vegetation fraction → 3-class **`W3/shp/MoH_Plots_class_v4.shp`** (`CLASS` A/B/P + `BUILT_FIN`, `VEGFRAC`, `PROB18`, `AREA_M2`) — **the authoritative plot layer for W4 loads**.
- `W3/py/a5_unparceled.py` — footprints with no plot → `W3/shp/Unparceled_Buildings.shp`.
- **Fragility**: this chain passes state via `.npy`/`.json` files in a session-specific scratchpad path (`...\413b098f-...\scratchpad`) that is hardcoded in 10+ scripts and belongs to a PREVIOUS session — those intermediate files may no longer exist; only the shapefile outputs in `W3/shp/` are durable. Do not plan to re-run the classification chain as-is.

## 9. Imagery / basemap

- `W3/py/esri_tiles.py` + `esri_mosaic.py` — Esri World Imagery z17 tile fetch (resumable, threaded) → JPEG-in-GTiff mosaic `Hydraulic\Imagery\esri_z17_mosaic_3857.tif` (EPSG:3857, 1.19 m/px). Licensing: never push imagery to repo.
- `W3/py/a4_overlay_maps.py` — the only pure-Python PNG map renderer: windowed mosaic read + matplotlib imshow + vector overlays, view-window list in EPSG:32640. No opacity blending, no scalebar, no legend box — it does NOT meet the working-rule-4 map spec.
- **The deliverable maps (W2 M1–M6) and DXF were NOT made in Python.** No `.py` mentions dxf/ezdxf anywhere; `W1/dwg/W1_concept_screening.dxf` and `W2/dwg/W2_concept_screening.dxf` exist, and `_BRAIN/07_PROJECT_STATE.md` line 34 credits "QGIS layouts M1–M6, DXF" — i.e. produced via the qgis MCP (layouts saved in `Hydraulic/QGIS/QGIS 2621 ibri sewer stp.qgz`, template `Hydraulic/QGIS/Layout template.qpt`, Google hybrid at 30% opacity per `_BRAIN/06_W2_FEEDBACK.md`). [Likely] DXF came from QGIS export of the shapefiles. For W4 this workflow is repeatable only with QGIS open + qgis MCP; there is no scripted, re-runnable map/DXF pipeline in the repo.

## 10. Report generation

`W2/report/make_report_r1.py` (298 lines, python-docx): opens `Data/sample report/Sample.docx`, wipes body keeping final `sectPr`, patches headers, then helper kit — `para/H/bullet/caption/pic/shade/table/pagebreak/toc` (TOC via `fldSimple` needing manual refresh; PDF export via Word COM per ENVIRONMENT.md). All content is hardcoded prose with numbers typed inline (only the zone table reads `zone_flows.csv`) — the helper kit is fully reusable; the content layer is not parameterized. Output `W2/report/Ibri_Concept_Screening_R1.docx`.

## 11. Shapefile writing pattern (house style)

pyshp `shapefile.Writer` + explicit `w.field(...)` defs + `wprj()` writing a copied/literal EPSG:32640 WKT (no .cpg except Towns). Polygons written exterior-only in W1/W2 zones (interiors handled only in `s3` zones write, line 313); `towns_from_kmz.py` shows the geopandas `to_file(..., encoding="utf-8")` + `.cpg` alternative — prefer that for W4 (handles holes, multiparts, encoding, and CRS properly).

---

## 12. Hardcoded assumptions & stale-path register (things W4 must not inherit blindly)

| Item | Where | Status |
|---|---|---|
| Elevation raster `Hydraulic\Terrain\DTM_terrain_mask.tif` (5 m) | `W2/py/s3_w2_pipeline.py:16` | **STALE** → use `Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt` (0.5 m); whole-band read must become windowed |
| `W1/temp/DEM_study.tif` (NSA DSM clip) | `W1/py/s2_trunk_zones.py:57` | STALE, screening-only source, superseded twice |
| STP coordinates `(444387.0, 2563352.5)` | s2:17, s3:18 | still valid ([Certain] per CLAUDE.md) but should live in a criteria module |
| OR=6.0, 1 dwelling/plot | s2, s3, a7, a8 | [GAP-5] unconfirmed; A8 shows measured ~7.0 persons/built plot; colleague suggests 4.9 |
| Landuse source `Hydraulic\SHP\Landuse\Landuse.shp` field `NewLUClass` | s2:78–81, s3:103–106 | superseded for load purposes by `W3/shp/MoH_Plots_class_v4.shp` + A7 doctrine |
| Plot→node assignment: nearest node ≤400 m, else plot silently dropped | s2:91, s3:114 | screening shortcut; W4 must account for every serviceable plot |
| Session-specific scratchpad absolute paths | 10+ W3 scripts | dead paths for any new session |
| rf weights 0.55/0.70/1.0, KCLIMB=300, seed thresholds (≥60 plots, 2500 m), SLS cluster 1500 m, dual-merge 35 m | s3 throughout | tuning constants with no criteria citation — fine to reuse but tag as method choices, not standards |
| Infiltration NET_KM=194 km (trunk only, no laterals) | a8 Inputs | provisional; also INFIL 720 L/d/km conflicts with R0's 10%-of-flow (flagged CONFLICT in A8) |

## 13. What does NOT exist in-house (explicit gap list for W4)

1. **Invert/profile solver** — no hydraulic grade computation, no pipe-by-pipe invert design, no drop-manhole logic, no cover optimization. The only invert logic is the screening accumulator (min-gradient descent + 12 m fail flag).
2. **Manhole placement** — nothing places manholes (max spacing 100/120/150/200 m per G203-p30, junctions, bends). No manhole layer exists anywhere.
3. **Pipe sizing** — no Colebrook-White/Manning capacity calc, no d/D check (0.65/0.50 limit), no velocity check (0.75–3.0 m/s), no DN selection. `smin_for()` is a plots→class proxy, not sizing.
4. **Per-pipe design flow** — flow is computed per zone only; no link-level Qpeak accumulation down a tree.
5. **Directed sewer network datamodel** — graphs are undirected screening graphs; no from-node/to-node, no upstream/downstream topology export.
6. **Along-line raster profile sampler** at fixed chainage step (needed for 0.5 m terrain).
7. **Geometry re-anchoring after dual collapse** — collapsed edges keep original carriageway geometry; a corridor centerline builder does not exist.
8. **Force-main / rising-main design** (G203 p50-51 velocity/gradient rules) — SLS records carry only a straight-line `FM_LEN_M` to nearest gravity node.
9. **Scripted DXF export** — no ezdxf anywhere; DXFs were QGIS-side. A re-runnable DXF writer is missing.
10. **Scripted deliverable-grade map rendering** — `a4_overlay_maps.py` is a QA renderer; the rule-4 map spec (hybrid 30% background, MoH_Plots layer, scalebar, data-table box) exists only as QGIS layouts in the .qgz, driven manually/via qgis MCP.
11. **SewerGEMS seed/export** (planned next task in PROJECT-STATE) — nothing exists.
12. **Shared criteria/constants module** — four divergent copies of the GUD numbers; W2's copy still embodies the superseded pre-A7 allocation.
13. **Test harness / validation** — no tests anywhere; the only self-checks are the assert-style cross-checks in `towns_from_kmz.py`.

## 14. Shortest reuse path for W4 (raw pointers)

- Graph + dual collapse: `W1/py/s1_roads_graph.py` (noding, DUAL detect) → `W2/py/s3_w2_pipeline.py:37-83` (collapse) — port, then fix geometry anchoring.
- Routing/screening: `s3_w2_pipeline.py:133-231` (two-tree Dijkstra, accumulation, SLS consolidation).
- Terrain: windowed-read pattern from `classify_built.py::feats()` applied to `IBRI_0p5_VRT2.vrt`; graph-neighbor gap-fill from s3.
- Loads: `a7_load_alloc.py` (doctrine + mojibake fix + peaking) on `MoH_Plots_class_v4.shp`.
- Deliverables: `make_report_r1.py` helper kit; `a8_load_calc_xlsx.py` workbook pattern; QGIS MCP for maps/DXF (external dependency: QGIS open with the project loaded).
- External architecture reference (per `_SETUP/ENVIRONMENT.md` §5): user's stormwater repo `github.com/mojikone/SWNETWROK` for gravity routing/invert fan-out patterns — not vendored locally.
