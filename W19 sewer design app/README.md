# W19 — sewer design app

A local application for sewer and stormwater network modelling and design: our own engines, an interface over them and
an AI assistant. **W18 stays the live Ibri design; W19 is a tool folder.** Spec:
`docs/2026-11-20-sewer-design-app-design.md`; plan: `docs/2026-11-20-plan-phase0-1.md`; every script and its place in
the UI: `docs/SCRIPT_REGISTER.md`; what the gates found: `docs/FINDINGS.md`.

**Clean-room:** the engines come from published methods only (PAM-GUD-201/202/203, Colebrook-White, Peltier,
Merrimack, EPA SWMM 5, public domain). Bentley's binaries are never decompiled and SewerGEMS's file formats are never
read. SewerGEMS is the referee, driven through its documented API in the offline VM, and its saved exports are what
the engine is checked against. Full statement: `docs/CLEAN_ROOM.md`.

## Start it

    cd "W19 sewer design app"
    python -m sewerapp.api            # then open http://127.0.0.1:8765 (this PC only)

Needs Python 3.12 with numpy, pandas, geopandas, shapely, pyogrio, ezdxf, fastapi, uvicorn, anthropic and swmm-toolkit
(`pip install -e ".[app]"`). The map loads MapLibre and the OpenStreetMap tiles from the internet.

**The assistant** needs `ANTHROPIC_API_KEY` as a user environment variable (set it yourself; it is never written to a
file). Without it the Assistant tab says so and everything else works. A design question with several tool calls costs about $0.30-0.45 on Opus 5.5 (2026-11-21: 5.4k output, 38k cache-write, 119k cache-read tokens); `claude-sonnet-5-5` costs about half. Model `claude-opus-5-5` (effort high), with a
`claude-sonnet-5-5` option; billed per token.

## The general app (home page, since 2026-11-22)

A network editor that works the way SewerGEMS does, on any project, sewer and stormwater (plan:
`docs/2026-11-21-general-app-plan.md`):

- **Projects:** a new project (a projected CRS with a basemap, or local metres), open or save a GeoPackage project
  file (QGIS opens it), open an Ibri sample, import an EPA SWMM `.inp`, or import GIS layers (GeoPackage, GeoJSON,
  zipped shapefile) with a field mapping.
- **Draw and edit:** manholes, outfalls, wet wells, pipes, pumps and catchments on the map; move, split, delete; a
  property grid with bulk edit; Nodes, Links and Results tables; undo and redo; scenarios copied and edited separately.
- **Instant re-run:** every edit re-solves the steady sanitary hydraulics (peaked unit loads, infiltration, Colebrook-
  White or Manning, normal depth, the d/D, velocity, cover and gradient checks): a small network at once; Ibri's 19,083 pipes solve in 0.35 s, an edit round trip about 1 s.
- **Design:** sizes every conduit by the d/D limit at its size's minimum gradient and lays it with crowns matched and
  minimum cover (equal to W18's design at every node); undoable.
- **Stormwater:** catchments, rain as a time series or a design storm from an IDF table, run on EPA SWMM 5, peaks and
  flooding on the map, hydrographs.
- **Export:** GeoPackage, SWMM `.inp`, DXF, CSV.
- **Assistant:** answers about any open project from its solved results, explains each check with its guideline page,
  and tries fixes, designs and storm runs in new scenarios.

| Gate | What it proved (2026-11-22) |
|---|---|
| G1 | Ibri's 12 designs as general projects: every pipe flow equals W18's within 0.1 %, velocities within 0.003 m/s, the file round-trips |
| G2 | the editor end to end in Chrome (12 Playwright tests): draw from blank, solve, edit, undo, save and reopen, sample, design, storm, import/export |
| G3 | the general design gives W18's gradient table, W18's depth at every node of SC1-2056 (0.6 mm) and W18's sizes |
| G4 | 15 EPA SWMM models round-trip through the app with zero difference; an edited size is written; a drawn storm network runs |
| G5 | GIS layers with foreign field names import back exactly (mapping, snapping); DXF and CSV open |
| G6 | the assistant's nine tools on any project, new scenarios only; one live run on Sonnet 5.5 |

The Ibri W18 viewer of phase 1B (the 12 frozen designs with their W18 tools) is at `http://127.0.0.1:8765/w18`.

**Findings for the engineer** (`docs/FINDINGS.md`):
- the O3 → O2-M696 gravity join is over its d/D limit in SC1 and SC2 (0.55 / 0.59 / 0.63);
- W18 took each outfall station's flow from SewerGEMS's run before the lift cuts, so stations below a lift miss the
  lifts' extra peak (P4 / O9 in SC1-2056: 10,970 against 9,835 m³/d).

## The W18 viewer (`/w18`)

- **Map** of the 12 W18 designs (SC1-SC4 × 2051/2056/2061), coloured by size, velocity, velocity at 2031, d/D,
  needs-re-lay or failing; click or shift-select pipes.
- **What-if scenarios:** copy a case, edit pipe size or gradient (one or many pipes), and the whole network re-solves
  in under 0.1 s. Inverts are held and the laid gradient kept; the edited pipe and everything downstream are flagged
  "needs re-lay". The design chain runs on the base cases only, so a what-if's re-lay is not done in the app yet. Undo,
  redo, compare two scenarios.
- **Profile** from any manhole to the outfall: ground, invert, crown, water surface at the peak.
- **Tools menu** (each a tested script): failing pipes, self-cleansing list, design-year check, stations, quantities,
  the whole W18 design chain on a base case (about 60 s, checked against W18), comparison with SewerGEMS, EPA SWMM stormwater examples.
- **Export** GeoPackage (opens in QGIS), DXF, CSV.
- **Assistant:** answers questions on a design from the solved results, explains every check with its guideline page,
  and tests a fix as a new what-if (never edits an existing scenario).

## Phase status

| Phase | State | Gate |
|---|---|---|
| 0 Foundations | **passed** 2026-11-21 | `python -m pytest -m gate_p0` |
| 1A Sanitary engine | **passed** 2026-11-21 | `python -m pytest -m gate_p1a` |
| 1B App and assistant | **passed** 2026-11-21 (live assistant test passed with the key) | `python -m pytest tests/api tests/e2e`; `-m live` with the key |
| Stormwater (SWMM) | 12 of 15 EPA models equal at every step of every period; extran8a and extran9 equal on their common periods (this build writes one more final period); Example1 up to 0.68 % off. Inputs identical to EPA's, so the cause is the engine build | `python -m pytest -m gate_swmm` |
| G1-G6 the general app | **passed** 2026-11-22 (see the table above) | `python -m pytest tests/general tests/e2e` |
| G7 SewerGEMS models with all scenarios | **passed** 2026-11-22: the SC1-2056 referee model's 23 scenarios exported by bridge job 101 (490 s) and opened in the app with SewerGEMS's stored results; with its loads exported (jobs 102-103) the app's engine re-solves SewerGEMS's own model, every pipe within 0.1 % of SewerGEMS's flows | `python -m pytest -m gate_g7` |

**Not done yet** (approved, open):
- SewerGEMS models: infiltration is not exported yet (the app uses 720 L/day per km, the Ibri model's value); to export
  another model set `$src` and `$tag` in `referee/jobs/100_w19_export_scenarios.ps1` and `103_w19_export_loads.ps1` and drop
  both into `D:\VBOXridge\jobs` with the watcher running; on DN200 at very low flows SewerGEMS's GVF velocities read up to
  0.04 m/s below the app's normal-depth velocities (GVF backwater not built);
- EPANET `.inp` (water distribution): not started;
- the hydraulics of pumps, wet wells and force mains (a pump passes its flow on; no pump curve or head is solved);
  GVF backwater; rational-method storm design and inlet capture;
- a dynamic SWMM run of a sewer from its sanitary loads (no dry-weather flow is written yet; a SWMM run needs rain);
- Babbitt and Harmon peaking; the catalogue, minimum-gradient, d/D and peaking tables are not editable in the UI
  (only through the Settings JSON paths);
- a saved project file holds one scenario (Save writes the chosen scenario flattened);
- imported US-unit SWMM models show feet and acres under the m and ha labels, and Design is not meant for them;
- the W18 viewer (`/w18`): the design chain does not take a what-if's edits; BOQ, costs, station flows, DWG and
  schematics are still to be placed (`docs/SCRIPT_REGISTER.md`, "Planned").

All tests, one pass (2026-11-22): `python -m pytest` - 207 passed, 1 skipped (a live assistant test), 2 expected failures
(EPA Example1, a SWMM build difference), 6 min; the editor suite has since grown to 16 tests, and all 31 end-to-end tests pass.

## Reproduction and speed (2026-11-21)

| Check | Result |
|---|---|
| All 12 W18 cases, whole chain | identical sizes, depths within 1 mm, flows within 0.1 %, same stations, same km under 0.75 m/s, same deepest manhole |
| SC1-2056 against SewerGEMS's saved export | 19,078 pipes, 100 % within 0.1 % (largest 0.0036 %), 0 over d/D, velocity 5-95 % -0.0008 to +0.0006 m/s, 9.01 km under 0.75 m/s in both |
| In-process engine, every pipe of all 12 cases | flows and velocities to 1e-9, identical sizes |
| Design-year check | equal to W18 on all 8 cases |
| EPA SWMM examples (Example1-5, extran1-10) against EPA's benchmark | 12 of 15 equal at every step (worst 0.0); 2 equal on the common periods; Example1 up to 0.68 % on 13 of 468 values. The inputs are the same git blobs as EPA's at the benchmark tag |
| Speed | re-solve of 19,083 pipes 0.03-0.09 s; design chain one case 38 s, 12 cases 67 s in parallel; SWMM 15 models 1.4 s (SewerGEMS: about 44 min per design) |

Saved comparisons: `docs/GATE_P1A.json`, `docs/GATE_SWMM.json`.

**Finding:** the gravity join O3 → O2-M696 (P1-P151, DN1000) runs over its d/D limit of 0.50 (G203 p27) in SC1 and SC2:
0.553 in 2051, 0.591 in 2056, 0.630 in 2061. It is the only one of the 60 joins in the 12 cases that does; SC3 and SC4
pass. DN1200 passes. Likely cause: SewerGEMS carried joins as transfers, so the join pipe was never analysed there.
Decision for the engineer.

**Self-cleansing length:** the app reports 9.01 km above DN200 under 0.75 m/s at 2031 for SC1-2056, judging velocity
at two decimals (the definition of W18's SewerGEMS comparison, which gives 9.01 km in both). W18's quantities and R12
say 9.29 km. W18 used the unrounded steepened gradients; the published files round them to three decimals of a
percent, so pipes laid to exactly 0.75 m/s read 0.749 in the app.

## Data

`tests/fixtures/` holds frozen copies of W18's inputs and outputs and SewerGEMS's SC1-2056 export (37 MB, manifest
with SHA-256), and EPA's public SWMM example inputs. EPA's reference results stay in `work/swmm_ref/`, not in git.
To rebuild them, download `benchmark-win64.zip` (21.9 MB) from github.com/USEPA/swmm-nrtestsuite, release
v2.5.0-dev, and extract the `Example_*` and `extran_*` folders' `.out` and `.rpt` files into `work/swmm_ref/`. Without
them the SWMM gate is skipped, not passed.
