# Ibri Sewer, TE Networks & STP — Concept Engineering Workspace

Working repository of the Claude-assisted concept engineering for **Renardet Project 2621** — Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri, Oman (Client: Nama Water Services, Tender T/2719110/2025).

> **AI agents:** start at [`CLAUDE.md`](CLAUDE.md) → `_BRAIN/` → `_SETUP/`. Humans: this README is the summary; the report under `W2/report/` is the deliverable.

## Current state — latest first

| Date | Update |
|---|---|
| 2026-08-16 | **W3 A8 — transparent load-calc workbook**: `A8_load_calc.xlsx` — Inputs (12 yellow named cells, GUD-201 refs), Population (25 towns, NCSI series; 239 wilayat settlements, all grow at the same wilayat rate), Load chain per model year (2055 Qadf 40,885 m³/d, STP +10% = 44,974), By-Town 2055 with A7 area-based ND+Gov allocation, Saturation (OR 4.9→full by 2054). Load uses NCSI population directly — OR only drives the ceiling. |
| 2026-08-16 | **W3 A7 — data-request note + load-allocation correction**: GUD-201 Tab 11 calls the 22 %/14 % non-domestic and governmental figures the "**Distributed**" ratios (governorate volumes ÷ population), and §7.3.2–7.3.3 say Table 12 land-use rates **shall** be used where land use exists — so the ratios are a **fallback, not the method**. `_BRAIN/02` §11 rewritten to record this, plus the double-count warning and the rule that Tab 12 is keyed to floor area/headcounts, never plot area (mosque plot area × 185 l/m²/d = 224,143 m³/d ≈ 4× the STP). New `py/a7_load_alloc.py`: keeps the ratio-derived total but places the non-domestic + governmental volume on non-residential plots by area — **project Qadf unchanged at 53,339 m³/d, zones shift −16.8 % to +127.2 %** (21 down, 13 up; Ibri core +12.6 %). Residential-only branches drop 171.3 → 139.4 l/c/d, ~19 %. Note also carries the ranked data-request list and the OR 4.9-vs-6.0 sensitivity (saturation 2054 vs 2062) |
| 2026-08-16 | **Towns polygon layer + population series**: `Final_Boundary_IBRI.kmz` parsed → `Hydraulic/SHP/Towns/Towns.shp` (25 towns, EPSG:32640, UTF-8 DBF, 84 fields) — `NAME_EN`/`NAME_AR`/`CODE` (NCSI national code, from the KMZ points), `TOWN` census code, and **`Pop_2023…Pop_2100`** from `Ibri Sewer Demand R0 2026 08 03.xlsx`; the KMZ's own Pop_2023–2050 verified == `ROUND(xlsx)` on all 25×28 cells (script aborts if that ever breaks). Project totals **2025 119,243 · 2030 135,532 · 2055 237,885 · 2100 691,264** (IBRI town 68,713 → 137,081 → 398,339). **The series compounds at ~2.2–2.4 %/yr to 2100 and never saturates — there is no ultimate/saturation case in the workbook**, to be reconciled against the 49,700 m³/d ultimate Qadf. AL MUQAYDIH has a KMZ point but no polygon and is absent from the client's 25-town project list. Boundary polygon exported separately (521.1 km² computed vs 507.49 in attribute) |
| 2026-08-15 | **W3 A6 — 3-class layer v4 (built/planned/agriculture)**: per-plot vegetation fraction from imagery → AGRI class (100% capture of known farms, 2.2% false rate); **empty-LANDUSE plots (39,838) characterized**: 36% built, 6% farms, 58% vacant; `MoH_Plots_class_v4.shp` (black/white/green QML); AGRI feeds TE demand mapping |
| 2026-08-15 | **W3 A5b — z18 re-check → built v3**: 12,237 z18 tiles, retrained classifier (95.9% acc), 2,736 planned→built flips (agri plots gated at 0.8 to kill palm-row false positives) → `MoH_Plots_built_v3.shp` (+`PROB18`, `SRC`); IBRI 57.2% built (b/impl 0.87), AL WAHRAH undercount fixed (0.99); **IBRI's remaining ~44k capacity < 2055 spillover demand** |
| 2026-08-15 | **W3 A5a — unparceled buildings layer**: 2,799 MS-footprint buildings (380k m² roof; IBRI 1,325) intersect NO cadastral plot → `Unparceled_Buildings.shp` (red style) — confirms user-reported MoH_Plots gaps; MoHUP cadastre completion added to data requests |
| 2026-08-14 | **W3 A4 — overlay style delivered**: `MoH_Plots_built_v2.qml` (auto-style: no fill, black outline = built, white = planned) + 3 rendered imagery-overlay verification maps (IBRI core, AD DARIZ, AT TAYYIB edge) |
| 2026-08-14 | **W3 A3 — built/planned classification finalized**: Esri z17 imagery (6,550 tiles, full boundary, mosaic kept off-repo) + texture classifier (88.8% train acc, validated 0.91–0.98 built/implied-dwellings in former no-coverage zones) → `MoH_Plots_built_v2.shp` with `BUILT_FIN` for all 61,272 plots; **IBRI 52.4% built**, AT TAYYIB 89% vacant; BAT boundary anomaly flagged |
| 2026-08-14 | **W3 A2 — spillover growth model** (user intent: growth continues past IBRI's fill, relocating to adjacent zones): 2055 allocation shifts −43k IBRI → +27k AT TAYYIB (+AD DIBAYSHI, AL QURAYN, AL JIBAYYAH, AL JAHLI); totals conserved; **whole boundary saturates ≈2062–2070** — 407k of R0's 2100 projection unhousable at OR 6.0 → NCSI/MoHUP data gates model validity beyond ~2060 |
| 2026-08-14 | **W3 A1 — settlement capacity & built/vacant analysis**: IBRI land ceiling (94k @ OR 6.0) crossed by R0 projection ≈ **2038** (146% utilized @2055) → growth must reallocate to AT TAYYIB (99% vacant, 47k capacity) etc.; area-wide saturation ≈ 2070; `BUILT_MS` field added to plots via MS Building Footprints (34% IBRI built; 7 settlements = footprint coverage gaps); shp+csv+charts in `W3/` |
| 2026-08-14 | **T01 Rev 2** (47 pp, 13 figures): Rev-1 comments addressed — R0 workbook decoded (master WWG equation traced from cell formulas, +20% weekly peak found baked into WWG series), Appendix B documents 5 tabs with equations + 4 charts, settlement populations to 2100 charted, future-plots/stub-out section, horizon logic corrected (saturation likely beyond 2055 — projections cross provisional ceiling mid-century), Peltier-vs-Merrimack element allocation, demand/return charts |
| 2026-08-14 | **`_CLIENT/` added**: Inception Report R0 (pdf+docx) + demand workbook pushed for remote access — user explicitly accepted public-repo exposure of these client documents |
| 2026-08-14 | **T01 Rev 1** (37 pp): all 28 review comments addressed — abbreviations, extensive exec summary, lists of figures/tables, teaching-level explanations, native OMML equations, 6 figures (chain, diurnal, 2 route flowcharts, NCSI population, Peltier-vs-Merrimack), electricity-accounts route (G1-p58), saturation-vs-dated-horizons section, conclusions/recommendations/references/appendix; 150-km tanker risk flagged |
| 2026-08-14 | **T01 as styled Word report** (`TUTORIALS/T01_*.docx/.pdf`, 9 pp): Sample.docx shell via `make_tutorial_t01_docx.py`, chain diagram, TOC + PDF via Word COM |
| 2026-08-14 | **Tutorial T01 — Sewage Flow & Load Calculation** (`TUTORIALS/`): full chain population→flows→loads with worked example + standard-vs-R0 reconciliation register |
| 2026-08-14 | **PAM-GUD-202 Water & TSE Guidelines** filed (`_STANDARDS/` + `Data/`), criteria extracted to `_BRAIN/02` §12b (`G2-p##` refs); Inception R0 package registered — NCSI population (Ibri 183,564 @2024) partly closes GAP-5, R0 adopted values in `_BRAIN/02` §12c |
| 2026-07-20 | **Global operating instructions committed** (`_SETUP/global-CLAUDE.md`): advisor tone, confidence tags, PRESERVE-CHECK protocol, no-push rule — restored automatically by bootstrap, drift-checked without overwriting |
| 2026-07-20 | **Migration automation**: root-CLAUDE.md bootstrap chain, project `.mcp.json`, `_SETUP/bootstrap.ps1` self-check (tested all-PASS) — a fresh Claude Code instance continues with zero manual setup |
| 2026-07-20 | **F2 existing-system findings** folded in: NE served district (Al Araqi) + existing trunk to STP; report data register extended (as-built DWG/SHP, design reports, trunk details — items 19–21) |
| 2026-07-20 | **W2 rework (current)**: DTM elevations, dual-carriageway collapse, full-coverage trunk (22 km main + 172 km branches), 36 structured zones, **18 consolidated SLS**, 134 wadi crossings, saved QGIS layouts M1–M6 (satellite bg 30%, info tables), **report R1** styled on client sample (23 pp, docx+pdf), DXF |
| 2026-07-20 | W1 first pass: road hierarchy (betweenness + dual detection), trunk + 20 zones, 125 SLS candidates (superseded by W2), report R0 |
| 2026-07-20 | `_BRAIN` knowledge base: scope register, design criteria from PAM-GUD-203 + PAM-GUD-201 (all values page-cited), data inventory, gaps |

## Key engineering numbers (W2, screening grade)

| Quantity | Value | Basis |
|---|---|---|
| Serviceable plots | 53,503 (43,722 residential) | MoHUP cadastre |
| Ultimate Qadf / +10% STP margin | ≈ 49,700 / 54,700 m³/d | PAM-GUD-201: 164 l/c/d, ratios, return rates, infiltration |
| Peak flow (Peltier per zone) | ≈ 86,400 m³/d | G1-p72 |
| Gravity coverage | ≈ 84% of plots to existing STP | Table 11 gradients + 12 m max cover (GUD-203 p29, p33) |
| Sewer zones | 36, one outlet each, road+density territories | — |
| Lifting stations (candidates) | 18 after consolidation | wadi-floor pockets below STP level |
| Trunk wadi crossings | 134 (12 on main trunk) | DI +15 m, 2 m cover, MoAFWR (G1-p85-86) |
| STP implication | Ultimate ≫ 20,000 m³/d TOR threshold → phasing is the pivotal decision | TOR p3 |

## Repository layout

| Path | Content |
|---|---|
| `CLAUDE.md` | Agent working rules + reading order (mandatory) |
| `_BRAIN/` | Source of truth: scope register, page-cited design criteria, data inventory, tools, gaps, W2 feedback constraints |
| `_SETUP/` | Migration/bootstrap: environment guide, MCP config, memory snapshot, `bootstrap.ps1` |
| `_STANDARDS/` | Standards PDFs kept in-repo for remote access (PAM-GUD-202; 201/203 remain in `Data/`) |
| `TUTORIALS/` | Method tutorials (T01: sewage flow & load calculation) |
| `W1/`, `W2/` | Iteration outputs: `py/` pipelines (re-runnable), `shp/`, `dwg/` (DXF), `img/maps/`, `report/` |
| `W2/report/Ibri_Concept_Screening_R1.docx/.pdf` | **Latest deliverable report** |

Client source data (`Data/`, `Hydraulic/Terrain/`, `Hydraulic/SHP/`, QGIS project) lives outside the repo on the project drive.

## Maintenance rule
This README is updated with every substantive commit — "Current state" table gets a new top row; key-numbers table is corrected whenever results change. Enforced via `CLAUDE.md` working rules.
