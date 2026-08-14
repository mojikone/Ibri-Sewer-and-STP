# Ibri Sewer, TE Networks & STP — Concept Engineering Workspace

Working repository of the Claude-assisted concept engineering for **Renardet Project 2621** — Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri, Oman (Client: Nama Water Services, Tender T/2719110/2025).

> **AI agents:** start at [`CLAUDE.md`](CLAUDE.md) → `_BRAIN/` → `_SETUP/`. Humans: this README is the summary; the report under `W2/report/` is the deliverable.

## Current state — latest first

| Date | Update |
|---|---|
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
