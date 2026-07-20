# TOOLS & ENVIRONMENT

## SWNETWROK repo (github.com/mojikone/SWNETWROK, cloned in scratchpad/swnet)
Stormwater gravity-network pipeline: roads+DEM+outfalls → noded directed graph → Dijkstra territory assignment per outfall → top-down invert routing (MIN_SLOPE / MIN_COVER / MAX_COVER, pruning, re-pooling) → one-out fan-out resolution → dendritic naming → attributed shapefiles (nodes, channels, catchments).
**Reuse verdict:** architecture directly reusable for sewer trunk/zone screening. Required adaptations:
- MIN_SLOPE → diameter-dependent Table 11 (BRAIN 02 §2), not single value.
- MAX_COVER = 10–12 m (p33) → its pruning naturally flags SLS locations (pruned branches = pump candidates). MIN_COVER = 1.3 m.
- Outfall = existing STP inlet; zone outlets = trunk connection nodes.
- Territory cost function: add road-class/centrality weighting (user wants near-straight trunk, minimal bends).
- Modules: `py/dem.py, roads.py, graph.py, hydraulics.py, outputs.py, swnetwork.py` (+tests). Keep W1 scripts standalone but lift functions from here.

## Environment
| Tool | State |
|---|---|
| QGIS 3.44.8 (open project) via **qgis MCP** | execute_code(PyQGIS), processing, layouts, styling, render/export — primary GIS engine (has GDAL/SAGA/GRASS providers) |
| System Python 3.12 | pymupdf/pdfplumber/pypdf ok; **no osgeo/geopandas** → do geoprocessing inside QGIS MCP or install libs into venv if needed |
| AutoCAD + civil3d MCPs | available for DWG outputs (alignments, polylines) |
| Scratchpad | extracted `scope.txt`, `guidelines.txt`, `gl_toc.txt`, repo clone |

## Conventions (user-mandated)
- Work folders: `Hydraulic/Claude/W1`, `W2`… (new W = rewrite iteration). Outputs: shp, dwg, img, report under the active W.
- QGIS: load outputs into a **group** with proper styling.
- Report: evolving document, revised as work proceeds; styles per `Data/sample report` (**empty — GAP-4**); maps from `Layout template.qpt`.
- Responses to user: concise, bullets, tables.
- DWG deliverables so user can inspect in CAD.
