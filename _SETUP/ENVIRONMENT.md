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
- `anthropic-skills:docx` — Word document work (read its guidance before editing Sample-derived files).
- `anthropic-skills:pdf` / pymupdf scripts — reading client PDFs (scope, guidelines).
- Standard tools: Bash (Git Bash), PowerShell (Word COM), qgis MCP.

## 5. Reference repo
`https://github.com/mojikone/SWNETWROK.git` — user's stormwater network pipeline; architecture reference for gravity routing (territory assignment, invert routing, fan-out). Assessment in `_BRAIN/04_TOOLS.md`.

## 6. Memory
`memory-snapshot/` in this folder is a copy of the Claude auto-memory for this project (machine-local at `~/.claude/projects/<slug>/memory/`). On a new machine, read it once — or copy it to the new machine's corresponding auto-memory path — so past feedback and project facts carry over. The durable engineering knowledge is all in `_BRAIN/`; the memory files are behavioural (how the user wants work done).

## 7. User's global preferences
The user keeps private global instructions in `~/.claude/CLAUDE.md` (challenge-first tone, confidence tags, [PRESERVE-CHECK] protocol for code edits, no-push-without-instruction rule, Arabic→Persian training format). That file is per-machine: transfer it manually to the new machine — it is deliberately NOT committed to this public repo.

## 8. Client data (NOT in repo)
`D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\` — scope.pdf, PAM-GUD-203, PAM-GUD-201, Sample.docx, figures F1–F3, MoHUP shapefiles; `Hydraulic\Terrain\` — NSA_DEM.tif (DSM), DTM_terrain_mask.tif (DTM, authoritative); `Hydraulic\SHP\` — roads, streams, landuse, plots. These stay on the project drive; the new instance must have the same drive/paths or update path constants at the top of the py scripts.
