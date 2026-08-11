# Ibri Sewer, TE Networks & STP — Concept Engineering Workspace

Working repository of the Claude-assisted concept engineering for **Renardet Project 2621** — Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri, Oman (Client: Nama Water Services, Tender T/2719110/2025).

> **AI agents:** start at [`CLAUDE.md`](CLAUDE.md) → `_BRAIN/` → `_SETUP/`. Humans: this README is the summary; the report under `W2/report/` is the deliverable.

## Current state — latest first

| Date | Update |
|---|---|
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
| `W1/`, `W2/` | Iteration outputs: `py/` pipelines (re-runnable), `shp/`, `dwg/` (DXF), `img/maps/`, `report/` |
| `W2/report/Ibri_Concept_Screening_R1.docx/.pdf` | **Latest deliverable report** |

Client source data (`Data/`, `Hydraulic/Terrain/`, `Hydraulic/SHP/`, QGIS project) lives outside the repo on the project drive.

## Maintenance rule
This README is updated with every substantive commit — "Current state" table gets a new top row; key-numbers table is corrected whenever results change. Enforced via `CLAUDE.md` working rules.
