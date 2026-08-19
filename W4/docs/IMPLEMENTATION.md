# W4 Implementation Plan (condensed — executed in-session)

> **SUPERSEDED — kept as the record of W4.** The live design is **W5**; see `_BRAIN/00_CURRENT.md` for what is current. Numbers here use one property per plot and 6.0 people per property, both replaced on 2026-08-19.

> Spec: `W4/docs/PLAN.md` (incl. §3b hydraulics-first regime and §7 decisions). This file tracks the build order and test gates; PLAN.md holds the reasoning. Executed by the session directly (user: "go ahead and do not stop until finish"), with the adversarial hydraulic review workflow as the independent check.

**Stack:** python 3.12 · geopandas/pyogrio/shapely 2 · rasterio (windowed VRT reads) · networkx · ezdxf · pytest. Package `W4/py/sewnet/`, tests `W4/py/tests/`, one runner `W4/py/run_test_boundary.py` + `config_test.py`.

| # | Module | Gate before moving on |
|---|---|---|
| 1 | `criteria.py` — every number, page-cited; tagged assumptions | review by eye; imported by everything |
| 2 | `hydra.py` — CW full/partial flow, Merrimack+Peltier PF, tractive Smin | **pytest: reproduce all 9 Table-11 gradients ±5%**; hand-calc fixtures match |
| 3 | `prep.py` — boundary repair, clip, node, dual collapse + re-anchor | pytest on synthetic road grid; test-area run: 1 component, no slivers |
| 4 | `topo.py` — weighted directed tree to auto-picked outfall | pytest: synthetic grid orients to outlet, loops broken; outfall report vs user point (no stop) |
| 5 | `manholes.py` — placement + ≤100 m splits, labels | pytest: spacing never exceeded, junction/bend/head coverage |
| 6 | `loads.py` — per-plot saturation loads, zero silent drops, accumulation + infiltration | pytest: mass balance to outfall exact |
| 7 | `solver.py` — sizing ⇄ inverts, drops/backdrops, Smax @ v=3, 12 m SLS pockets, node min-depth constraints | pytest: synthetic profiles incl. drop case + steep case + deep case |
| 8 | `tertiary.py` — riders/PCS schematic + **plot connectability elevation check** + manhole deepening pass | pytest: synthetic low-plot case gets flagged, deepening resolves it |
| 9 | `audit.py` — every rule re-checked independently, saturation + start-year (CLASS=B) runs | end-to-end: zero violations on test boundary |
| 10 | exports — `export_shp.py`, `export_gems.py`, `export_dxf.py`, `maps.py` | ogrinfo-clean files; GEMS package schema per phaseA_sewergems.md; DXF opens; PNGs render |
| 11 | Adversarial review workflow on hydra+solver; fix confirmed findings | all confirmed findings closed |
| 12 | `METHODOLOGY.md` (exec summary last-written, first-placed) + Figma diagrams; README/PROJECT-STATE; push | rule 12 satisfied |

Parallel track: T01 Rev 3 Colebrook-White chapter (background workflow, author+verify) — merged on completion.

Commit per module. Push at milestones.
