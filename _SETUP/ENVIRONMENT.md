# _SETUP — Environment for a fresh Claude Code instance

What a new Claude Code session needs beyond `CLAUDE.md` + `_BRAIN/`. Read this once at first session on a new machine/subscription.

## 1. MCP servers (as configured on the original machine)
Copy `mcp.json` from this folder into the project as `.mcp.json` (project scope) or merge into `~/.claude.json` (user scope):

| Server | Purpose | Config |
|---|---|---|
| `qgis` | Primary GIS engine — PyQGIS execute_code, processing, styling, layouts, exports. Requires QGIS open with the qgis_mcp plugin | `uvx --from git+https://github.com/nkarasiak/qgis-mcp.git qgis-mcp-server` |
| `civil3d-mcp` | Civil 3D automation (alignments, pipe networks, surfaces) — for later design stages | `node C:\Civil3D-mcp\build\index.js` (install path machine-specific) |
| `autocad-mcp` | Plain AutoCAD drawing automation (was available; reinstall if needed) | — |

QGIS project to open before starting the qgis MCP: `Hydraulic/QGIS/QGIS 2621 ibri sewer stp.qgz` (QGIS 3.44.x). Layouts "W2 M1..M6" are saved inside it.

## 2. Python (system 3.12, NOT QGIS python)
```
pip install networkx shapely pyshp rasterio numpy scipy matplotlib pymupdf pdfplumber pypdf python-docx
```
Pipelines: `W1/py/s1_roads_graph.py` (road graph + dual detection) → `W2/py/s3_w2_pipeline.py` (trunk/zones/flows/SLS/crossings). Both standalone, re-runnable, ~20 s each.

## 3. Node / report toolchain
- `docx` npm package used only for W1 R0 (superseded). R1+ uses **python-docx** with `Data/sample report/Sample.docx` as the style shell: `W2/report/make_report_r1.py`.
- PDF export + TOC refresh via Word COM (PowerShell): see the one-liner in `make_report_r1.py` history — LibreOffice is NOT installed on the original machine.

## 4. Skills used (Claude Code built-ins/plugins)
- **`report-writing`** — the project's own skill, in `_SETUP/skills/report-writing/SKILL.md`. Copy it to `~/.claude/skills/report-writing/SKILL.md` on a fresh machine (`bootstrap.ps1` does this). It carries the whole deliverable-report method: OMML equations, real footnotes, versioned revisions, flowcharts, data charts, QGIS map figures, and the writing rules that keep the prose human.
- `anthropic-skills:docx` — Word document work (read its guidance before editing Sample-derived files).
- `anthropic-skills:pdf` / pymupdf scripts — reading client PDFs (scope, guidelines).
- Standard tools: Bash (Git Bash), PowerShell (Word COM), qgis MCP.

## 5. Reference repo
`https://github.com/mojikone/SWNETWROK.git` — user's stormwater network pipeline; architecture reference for gravity routing (territory assignment, invert routing, fan-out). Assessment in `_BRAIN/04_TOOLS.md`.

## 6. Memory
`memory-snapshot/` mirrors the Claude auto-memory (`~/.claude/projects/D--Mojtaba-Renardet-2621-Ibri-Sewer-STP/memory/`). Migration is same-machine/same-folder, so the live memory persists across subscriptions; `bootstrap.ps1` restores it from this snapshot automatically if it is ever missing. Durable engineering knowledge is in `_BRAIN/`; memory files are behavioural.

## 7. User's global operating instructions — IN THE REPO
`global-CLAUDE.md` (this folder) is a verbatim copy of the user's `~/.claude/CLAUDE.md`. It defines *how the user wants to be worked with*, and applies to every reply — it is not project documentation:
- advisor-not-assistant tone: challenge first, no agreement openers, uncomfortable answer first, hold position under pushback;
- **confidence tags** [Certain] / [Likely] / [Guessing] before claims;
- **[PRESERVE-CHECK] protocol** for any modification of existing code: KEEP / CHANGE / FILES declared before editing, `[BROAD]` gate for anything removed, replaced or uncertain;
- one logical change per commit; **never `git push` without explicit instruction**;
- Arabic→Persian interlinear HTML training format spec.

`bootstrap.ps1` restores it to `~/.claude/CLAUDE.md` if that file is missing, and reports drift without overwriting when both exist (the live file always wins). If the user edits the live file, refresh the repo copy so the next instance inherits it.

## 8b. Fully automated first run
`bootstrap.ps1` (this folder): restores root `CLAUDE.md` + `.mcp.json` from `_SETUP` copies, restores auto-memory, installs missing python deps, verifies all data paths, git remote and Word COM. The root `CLAUDE.md` instructs the new instance to run it once.

## 8. Client data (NOT in repo)
`D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\` — scope.pdf, PAM-GUD-203, PAM-GUD-201, Sample.docx, figures F1–F3, MoHUP shapefiles; `Hydraulic\Terrain\` — NSA_DEM.tif (DSM), DTM_terrain_mask.tif (DTM, authoritative); `Hydraulic\SHP\` — roads, streams, landuse, plots. These stay on the project drive; the new instance must have the same drive/paths or update path constants at the top of the py scripts.
