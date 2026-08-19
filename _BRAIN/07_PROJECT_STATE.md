# PROJECT-STATE — single-file orientation for any new session
**Companion page: `_BRAIN/00_CURRENT.md` lists which files are live and which are superseded. LIVE DOCUMENT (user-mandated): update with every substantive commit, alongside README.md — see CLAUDE.md rule 12. Last updated 2026-08-15. Read this FIRST, then 02_DESIGN_CRITERIA before writing any number.**

## 1. Project in three lines
Concept→detailed design + supervision of sewer network, TE network and STP capacity for Ibri Wilayat, Oman (Client NWS, Tender T/2719110/2025, Renardet job 2621). Horizons: start / 2030 / 2055 / ultimate-saturated; ≥3 options each for sewer, TE, STP. Existing STP at E444387 N2563352 (ground ≈327.5 m); ultimate flows ≫ 20,000 m³/d ⇒ STP phasing is the pivotal decision.

## 2. Settled engineering doctrine (user-agreed, binding for design work)
1. **Load allocation** (agreed 2026-08-15): *plots at saturation size the pipes; capped-and-spilled zone totals at dated years size the STP phases; the two meet only at trunk nodes.*
   - Pipes/civil: EVERY plot (built + future + unparceled buildings) at full saturation load (properties × OR × 171 l/c/d), accumulated with PF. No timing.
   - Dated years: zone totals only — R0 projection capped at zone ceiling (plots × OR); surplus spills to adjacent zones proportional to vacancy (A2 model). Never per-plot-per-year.
   - Phased elements: STP trains, pumps, force-main duty equipment (M&E ~20 yr life). Buried civil = saturation.
   - Early-years check: self-cleansing (0.75 m/s / tractive force, G203-p26-27) verified at start-year flows.
   - Farms: **the agricultural USE carries no sewage load (they are TE customers), but DWELLINGS on a farm plot do** (narrowed 2026-08-19 — 1,947 CLASS=A plots carry 3,366 domestic electricity accounts, so there are houses on them).
2. **Saturation** = no more developable plots. Zone-level ceilings bite inside the design horizon (IBRI ≈2038); whole boundary saturates ≈2062–2070 at OR 6.0; beyond that R0 projections are physically unhousable (407k surplus by 2100) — pending NCSI/MoHUP resolution.
3. **Maximum depth is 12 m, with no exceptions** (G203-p33; settled 2026-08-19 after the user
   found 21.3 m chambers passing the audit). The limit applies to every chamber AND to the trench
   between chambers. It may never be relaxed by calling an area an "SLS pocket" — that exemption
   caused the failure and has been deleted from the audit. Where a gravity sewer would pass 12 m,
   a **pumping station goes in before that point**: the sewage is lifted and the pipe restarts at
   normal cover, so the next stretch runs by gravity. Pumps are not to be removed by digging
   deeper; the route is re-searched first, and whatever pumping is left is real.
   - The rising main from each station is sized on the **pump duty** (wet well emptied faster than
     it fills), keeping 0.75-3.0 m/s (G203-p50 8.1) — not on the arriving gravity flow.
   - Stations within 1.5 km of one another are cascade candidates (rule 9); land acquisition makes
     the station COUNT the thing to minimise.
4. **Inlet angle** (G203-p30, "shall"): no pipe may arrive at a chamber pointing against the flow.
   Where a street meets at a bad angle a **bend chamber** goes a few metres short of the junction
   so the turn is made in two halves. Where there is no room (2 m plot clearance, 3 m chamber
   clearance) the junction is flagged for a purpose-made chamber with a curved channel.
5. **Stub-outs**: capped connections at future-plot frontage, sized for that area's saturation flow; usually DN200 minimum governs.
6. Flow chain per **TUTORIALS/T01** (Rev 2, 47 pp, docx/pdf) — the teaching reference with every value page-cited; reconciliation register vs Inception R0 inside.

## 3. Data available (detail: 03_DATA_INVENTORY)
| Data | State |
|---|---|
| Standards | G203 (wastewater), G201 (general), G202 (water/TSE, in `_STANDARDS/`) — criteria extracted to 02 with page refs |
| Client R0 package | Inception Report R0 + demand workbook (NCSI pop to 2100, criteria tabs decoded in T01 Appendix B) — `_CLIENT/` on repo for remote access |
| Cadastre | MoH_Plots 61,272 (65 % LANDUSE empty — characterized by imagery, A6); **2,799 buildings have NO plot** (A5a `Unparceled_Buildings.shp`) |
| Plot status layers (W3/shp) | `MoH_Plots_class_v4.shp` = CLASS B/P/A (built 17,961 / planned 36,945 / agri 6,366) + BUILT_FIN, VEGFRAC, PROB18; QML styles included (black/white/green) |
| Settlement zones | 26 polygons from R0 kmz; TANAM/SATWAH/AL MAKHTIBYAH/BAT boundaries WRONG (miss their plots); 24 of 50 workbook settlements have no polygon |
| Terrain | **`Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt` 0.5 m blend = authoritative (user 2026-08-18)**; DTM_terrain_mask.tif 5 m superseded (was W1–W3 source); NSA_DEM 4 m screening only; NO buildings in any DEM; "Sat_" folder name misleading — it is terrain |
| Imagery (LOCAL ONLY, not in repo) | `Hydraulic/Imagery/`: esri_z17_mosaic_3857.tif (80 MB, full boundary, 1.19 m) + z17/z18 tile stores (6,550 + ~12,400 tiles). Esri XYZ streaming for remote QGIS |
| Existing system | F2 PDF read-off only: NE district (Al Araqi) served, existing trunk to STP — as-builts still missing (GAP-6) |

## 4. Progress stages
| Stage | State |
|---|---|
| W1 (superseded) | First pass: trunk + 20 zones, 125 SLS candidates |
| W2 (delivered) | 36 zones, trunk 22+172 km, 18 SLS, 134 wadi crossings, report R1 (Sample.docx style), QGIS layouts M1–M6, DXF |
| T01 tutorial | Rev 2: full flow/load chain, native equations, R0 workbook decoded (incl. its +20 % weekly peak baked into WWG series) |
| W3 (analysis, current) | A1 capacity (IBRI ceiling crossed ≈2038) · A2 spillover (−43k IBRI → +27k AT TAYYIB @2055; totals conserved) · A3–A5 built classification v3 (z17+z18, 95.9 % train acc) · A5a unparceled buildings · A6 3-class layer v4 + empty-LANDUSE characterization · **A7** load allocation per town + data-request note (key: request *persons per built plot* ≈ 6.0–6.96 as a product, not OR alone; non-dom/gov % ratios are a FALLBACK — land-use unit rates are the method, 02 amended) · **A8** `A8_load_calc.xlsx` transparent formula-driven load workbook (12 named inputs) · **A9** criteria audit vs all three guidelines (145 issues: 83 missing rules, 59 incomplete, 3 misread — incl. tractive-force τ^1.23 term; fixes folded into 02, remainder recorded for detail design) |
| Towns layer | 26 settlement polygons (from R0 kmz) as QGIS layer with population series to 2100 attached from the demand workbook |
| W5 (superseded by W6, 2026-08-19) | **The agreed rules are implemented and the design runs end to end.** Inputs: new road layer `SHP/Road centerline 2` (the `dual` column decides exclusions, NOT road class — 95 National and 55 Arterial roads are single carriageway), 50-year flood grid `Data/04 Lekhuwair/Hazard_T50y.tif` (classes 4/5/6 = wadi, no value = dry), and **33,970 electricity accounts** as counted properties. Rules: no pipe on a dual carriageway (trunk included, crossings perpendicular only), roundabouts and turning links removed, straight street = one line, chamber at a corner with a 2 m plot clearance CHECK (flag, not redesign), max 3 chambers per bend. House connections rebuilt around the plot frontage with separate output layers. OR = 5. Farm plots with houses now load (doctrine narrowed). Result: 1,744 chambers / 78.4 km / Qadf 3,620 m³/d / peak 96 L/s / 5 SLS spots / 3 checks failing. See `W5/docs/WHAT_CHANGED.md` and `W5/docs/CRITERIA_UPDATE_R1.md`. |
| **W6 (CURRENT, 2026-08-19)** | **User-placed trunk + the 12 m depth limit enforced for real.** The main pipe follows the western edge then the southern side beside the dual carriageway (2.1 km, 44 joining points, median 76.7 m off the wanted line); every street drains to its nearest point on it (multi-source Dijkstra), so nothing crosses the area to reach one outfall. **The bug the user caught:** `audit._max_depth` skipped chambers flagged `sls_pocket`, so 71 chambers reached 12-21.3 m with no pump. Exemption deleted; depth now checked at every chamber and mid-trench. Solver rewritten to **lift-and-reset**: when the next chamber would pass 12 m, a station is placed and the pipe restarts at cover. Rising mains sized on pump duty. Routing searched with two cost models (uphill-expensive and depth-gain-expensive) plus an avoid-list built from the best design so far: **6 stations -> 3**. New **SweepEntry** stage adds 172 bend chambers so branches meet the flow at >=90 deg. Also fixed: the re-route loop was leaving the house-connection check with stale pipe references (it silently checked nothing). Result: **1,925 chambers / 78.7 km / Qadf 3,619 m3/d / peak 96 L/s / deepest 11.88 m / 3 stations (855 properties, 31.4 m lift) / 3 checks failing.** Why any pumping at all: the 4.6 km spine dips ~5 m then climbs back over a ridge before falling to the outfall — the sewer cannot climb, so it goes deep under the ridge. Overall fall is adequate (~14 m); it is the ridge that costs. |
| _W4 spec (now built in W5)_ | **`W4/docs/CRITERIA_UPDATE_R1.md` = the single pending change register** — road layer swap to `SHP/Road centerline 2` (StrCls/TYPE hierarchy), roundabouts + dual carriageways excluded as corridors (crossings still allowed), head chambers at the house gate, bend bands with chord control, and the tertiary rewrite (frontage projection, perpendicular spurs, rider ≤3 HCC, stub-outs, separate output layers). **Working rule 7 (collapse duals) is superseded for sewer corridors — exclude, do not collapse.** Nothing implemented yet; awaiting confirmation of StrCls vs TYPE as the exclusion field. |
| **W4 (DELIVERED 2026-08-18, restructured same day)** | **Code is now an object model**: `sewnet/model.py` (Chamber/Reach/Network owning the no-loops + one-outlet invariants), frozen `Criteria` object (tau sensitivity = config, not code), one class per stage in `sewnet/stages/`, audit as a check REGISTRY generating the compliance table. Refactor verified by an equality gate. **RoadTreatment stage** (new): raw centrelines → reviewable `W4_corridors.shp`; 27% of chambers were artefacts of road-data breaks → **1,655 chambers (−23%)**, 89.5 km. Two adversarial reviews (21 + 33 agents): 28 confirmed findings, all fixed — see `W4/docs/REVIEW_FINDINGS.md`. Audit: 2 failures left (inlet angle 263/1654; 152 house connections >50 m). |
| _W4 original delivery_ | **Test-boundary sewer design pipeline — end to end, audit-clean, adversarially reviewed.** `W4/py/sewnet/`: criteria (all values page-cited + tagged assumptions) · CW hydraulics on TRUE bore (Table-11 gate ±5%, tractive floored at Mara 1.5 L/s) · prep (boundary repair, dual collapse) · climb-weighted tree + cross-street summit-split augmentation · manholes (≤100 m, bends, <2 m contraction) · saturation loads per doctrine §2 · sizing⇄inverts solver (drops to outgoing-invert datum, 12 m→SLS pockets) · house-connectability check with MH deepening (user mandate: elevated roads) · independent audit. Test area: 2,359 MH / 95.3 km / 83 L/s peak / 0 violations / 12 residual low plots / 1 absorb pocket. Review: 11 confirmed findings fixed (`docs/REVIEW_FINDINGS.md`). **Self-cleansing rests on τ=1 Pa [GAP-9]: 1,626 pipes exposed if τ=2 — top kickoff item.** Outfall auto-pick (450614, 2567397) is 733 m from user's expected west-edge point — config swap + 13 s re-run if user relocates. SewerGEMS package + referee CSV await user's ModelBuilder run. T01 Rev 3 (CW §14). **Next (W5): user-finalized trunk + multi-connection subnetworks; then three concept options, F2 georeferencing, capacity rerun with A6 farm correction** |

## 5. Key numbers (screening grade; **W1–W3 numbers below were built at OR 6.0 — the design basis is now OR 5.0 with properties COUNTED from electricity accounts, so they need rescaling before reuse**)
| Quantity | Value |
|---|---|
| Ultimate Qadf / +10 % | ≈49,700 / 54,700 m³/d (W2 chain) — R0 model 2055 WWG 46.5k (÷1.2 weekly peak ≈ 38.7k avg) |
| Cadastre status | 61,272 plots: 33 % built, 10 % agri, 57 % planned; +2,799 unparceled buildings |
| IBRI settlement | 57 % built; ceiling 94k pop, crossed ≈2038; 2055 spillover −43k |
| AT TAYYIB | 87 % vacant, ceiling 47k — primary growth sink (+27k by 2055) |
| Boundary saturation | ≈326k pop ≈ 2062–2070 |
| **Properties per plot (measured 2026-08-19)** | **1.4 average** from 33,970 electricity accounts; 1.46 domestic → 7.28 people/plot at OR 5, matching A7's independent 6.96 |
| W5 test area (551 ha, superseded) | 1,744 chambers · 78.4 km · Qadf 3,620 m³/d · peak 96 L/s |
| **W6 test area (551 ha, CURRENT)** | 1,925 chambers · 78.7 km · 4,226 properties on 3,017 plots · Qadf 3,619 m³/d · peak 96 L/s · **deepest chamber 11.88 m (limit 12.00)** · **3 pumping stations**, 855 properties, 31.4 m lift, 162 m rising main |

## 6. Open gaps (detail: 05_GAPS)
GAP-5 occupancy (NCSI housing units — NOT in R0 package) · GAP-6 as-builts/F2 GIS · GAP-7 existing STP capacity/invert · NEW: MoHUP cadastre completion (unparceled buildings, empty LANDUSE) · settlement boundary fixes (BAT etc.) · NWS confirmations: infiltration basis (720 L/d/km vs R0 10 %), peaking formula per element, tanker catchment (25 km vs observed 150 km), model start year.

## 7. Where things live
Repo root = `Hydraulic/Claude/` (github.com/mojikone/Ibri-Sewer-and-STP, public — user-accepted; remote user downloads via repo, warn-once-then-push policy). `_BRAIN/` truth · `_STANDARDS/` G202 pdf · `_CLIENT/` R0 package · `TUTORIALS/` T01 · `W#/` iterations (py re-runnable, shp/img/analysis outputs) · `_SETUP/` bootstrap for fresh machines. Client data outside repo: `Data/`, `Hydraulic/Terrain/`, `Hydraulic/SHP/`, `Hydraulic/Imagery/`, QGIS project `Hydraulic/QGIS/*.qgz` (open it for qgis MCP).
