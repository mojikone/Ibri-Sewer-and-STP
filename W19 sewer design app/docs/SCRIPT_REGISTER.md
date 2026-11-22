# Script register: every tested script and its place in the UI

Rule (engineer, 2026-11-21): a script that is built and tested gets a named place in the UI in the same change; a
script with no UI place is not done. Status: `tested` (gate or unit test green) · `in UI` (reachable from the app) ·
`planned`.

| Script | What it does | UI place | Status |
|---|---|---|---|
| `w18port/final_design.py` | flows (unit loads, peaking, infiltration, transfers, lifts) and pass-by-pass sizing of one case | Tools "Design → Re-run the W18 design chain" (base cases; a what-if's edits are not carried yet) | tested (gate P0) |
| `w18port/split_deep_subnetworks.py` | steepen to 0.75 m/s up to 0.75 %, re-lay (crowns matched, 1.3 m cover), cut, gravity joins, fixed stations | Design menu → "Run design chain"; results view "Cuts and joins" | tested (gate P0) |
| `w18port/final_selfcleansing.py` | self-cleansing above DN200 at the 2031 peak, rechecked at 2036 | results view "Self-cleansing" check | tested (gate P0) |
| `w18port/final_naming.py` | names pumps P#, lifts P#L#, manholes and pipes; lift or pump by Table 12 spacing | applied on every chain run; map labels | tested (gate P0) |
| `w18port/final_products.py` | stations sized (duty, force main, head, wet well, kW, MWh), plant flows, quantities | Stations panel; Quantities panel | tested (gate P0) |
| `w18port/final_sg_compare.py` | a case against SewerGEMS's run of it, pipe by pipe | Referee panel "Compare with SewerGEMS" | ported, not yet run in W19 |
| `w18port/run.py` | builds a work root from the fixtures and runs the chain until the lift stations stop changing | the engine behind "Run design chain" | tested (gate P0) |
| `engine/flows.py` | design flow in every pipe: peaked unit loads, infiltration, transfers, lifts | instant re-run on every edit (task 4); Results table "flow" | tested on all 12 cases (1e-9) |
| `engine/hydraulics.py`, `engine/analysis.py` | normal depth, velocity, d/D against Table 10, 3 m/s check | instant re-run; map colour by v / d/D; failing pipes flagged | tested on all 12 cases (1e-9) |
| `engine/design.py` | pass-by-pass sizing at the current size's Table 11 gradient | Design menu "Size pipes (keep layout)" | tested on all 12 cases (identical sizes) |
| `engine/peaking.py` | Extreme Flow Setup table, Peltier, Merrimack | Settings "Peaking table" | tested (G201 p71-72) |
| `referee/golden.py`, `referee/sewergems.py` | a case against W18 at the spec's tolerances; against SewerGEMS's saved export | Referee panel "Compare with W18 / SewerGEMS" (task 5) | tested (gate P1A) |
| `model/project.py` | scenarios = a W18 case + edits; instant re-run (laid gradient, inverts held, needs-relay flag downstream); undo/redo; copy; compare; profile | the whole UI: Scenarios bar, property grid edits, Undo/Redo, Compare, Profile | tested (API tests) |
| `api/exports.py` | GeoPackage (pipes + manholes with results, EPSG:32640) and DXF (one layer per size) | File menu "Export GPKG / DXF / CSV" | tested (API tests) |
| `api/tools.py` | the tools menu: checks, self-cleansing list, stations, quantities, design chain, SewerGEMS comparison | Tools menu (one entry each) | tested (API tests; design chain via gate P0) |
| `assistant/runner.py`, `assistant/tools.py` | the AI assistant: Claude API (claude-opus-5-5, sonnet-5-5 switch) with tools list/summary/query/get/explain (checks with guideline pages)/make_whatif (new scenario only)/compare/run_tool/lookup_criterion | Assistant tab | tested with a stand-in client; live test waits for ANTHROPIC_API_KEY |
| `engine/swmm.py` | stormwater and dynamic routing on EPA SWMM 5.2.4 (swmm-toolkit); run a model, compare every time step with a reference | Tools menu "Stormwater → Run EPA's SWMM examples and compare" | tested (gate SWMM: 12 of 15 EPA models equal at every step, 2 on their common periods, Example1 up to 0.68 % off) |
| `engine/design_year.py` | the 2051 and 2061 designs of a scenario at the 2056 peak: pipes and km over the d/D limit, surcharged | Tools menu "Checks → Design-year check" | tested (equal to W18 on all 8 cases) |

## Planned: W18 tools not yet in the app (each with what it needs; source list `_SETUP/TOOLKIT_W18_deliverables.md`)

| W18 script | What it does | Planned UI place | Needs |
|---|---|---|---|
| `final_boq.py` | bill of quantities and network capital cost of the 12 designs | Tools "Quantities → BOQ and network cost (Excel)" | the team's rates workbook on W: (team data: read in place at run time, never copied into the repo) |
| `final_financial.py` | CAPEX/OPEX, STP modules, TE supply of the 12 designs | Tools "Costs → Financial summary" | the same rates, `te_customers.csv`, `SC4_TE_lengths.csv` |
| `final_station_flows.py` | people and flow at every station 2026-2061 | Stations panel "Flows by year" | W18's plot layer `W18_plots_2026_2100.shp` (local, not in git) |
| `final_dwg.py` | DWG/DXF drawings of a scenario | File "Export drawing (DWG)" | `financial.json`; the app's DXF export covers pipes and manholes today |
| `diagram_layout.py`, `diagram_png.py` | flow schematics in the R7 form | Tools "Schematic of the stations" | the station flows above |
| `nws_loads.py`, `map_not_carried.py` | loads on plots and manholes; the flow the network does not carry | Loads menu | the plot layer and the bridge's W17 inventory (local) |
| `te_sc4_network.py` | treated effluent network of SC4 | Tools "TE network" | the S2/S3 TE shapefiles (local) |
| `reduce_stations.py` | fewer stations by the engineer's caps | Design "Fewer stations…" | runs on the port's split; next after the UI |

## The interface (web/)

| Part | What it does | Tested by |
|---|---|---|
| `web/index.html`, `web/app.js`, `web/style.css` | map (MapLibre, OSM basemap toggle), colour by size / velocity / v2031 / d/D / re-lay / failing, click and shift-select, property grid with bulk edit in what-ifs, scenarios bar, copy, undo/redo, compare, export menu, tools menu from `/api/tools`, results table, profile (ground, invert, crown, water; re-lay in orange), assistant pane | `tests/e2e/test_e2e.py` (Playwright, 15 tests) |

## The general app (G1-G6, plan `docs/2026-11-21-general-app-plan.md`)

| Script | What it does | UI place | Status |
|---|---|---|---|
| `model/general.py` | the general project: nodes, links (conduit, pump, transfer), catchments, settings, load sets, fixed flows | File menu New / Open / Save; element tables | tested (gate G1) |
| `engine/steady.py` | steady sanitary solve of any project: flows (W18 rule, station = sum of arriving peaked flows), peaking table / Peltier / Merrimack / constant, Colebrook-White or Manning, normal depth, checks | Run (instant re-run on every edit) | tested (gate G1: 12 Ibri cases) |
| `io/gpkg_project.py` | the project file (GeoPackage, opens in QGIS) | File menu Open / Save | tested (round trip) |
| `io/ibri_sample.py` | Ibri's 12 W18 designs as sample projects | File menu "Open sample: Ibri SC#-year" | tested (gate G1) |
| `model/workspace.py`, `api/general_api.py`, `api/coords.py` | open projects, scenarios as edit lists by element id (set / bulk set, add node / link / catchment, delete, move, split, set load, set setting), undo/redo, instant re-solve, model and results for the map, profile, save/open GeoPackage, project CRS or local metres | the editor (G2): toolbar, property grid, File menu, scenarios bar | tested (`tests/general/test_general_api.py`, hand calculation on a drawn network) |
| `engine/design_general.py` | automated design of any project: pass-by-pass sizing at the size's minimum gradient (Table 11 rule), re-lay with crowns matched and minimum cover; an undoable edit | Tools "Design → Design: size and lay"; Tools "Checks → Failing links" | tested (gate G3: W18 depths at every node, W18 sizes; drawn network) |
| `io/swmm_inp.py` | EPA SWMM 5 `.inp` to and from the general project (modelled elements editable, SWMM's other fields and sections kept verbatim); design storm by the alternating-block method from an IDF table | File "Import SWMM .inp" / "Export .inp"; Settings "Rain" | tested (gate G4: 15 EPA models round-trip with zero difference; edited size written) |
| `engine/storm.py` | run a project on EPA SWMM 5: peaks per link, node, catchment, flooding, continuity; time series | Tools "Stormwater → Run on EPA SWMM"; hydrograph panel | tested (gate G4: drawn storm network, continuity < 1 %) |
| `io/gis_import.py` | a network from GIS layers (GeoPackage, GeoJSON, zipped shapefile) with a field mapping; ends snapped to nodes; DXF export of any project | File "Import from GIS layers…" (field-mapping dialog from `/api/g/gis/fields`); File "Export DXF" / "Export CSV" | tested (gate G5) |
| `web/editor/` | the general editor (home page `/`): File (new, sample, open, save, import/export .inp), toolbar (select, manhole, outfall, wet well, pipe, pump, catchment, move, delete; split by clicking a pipe), map coloured by result, property grid with bulk edit, Nodes / Links / Results tables, Profile, Settings with Rain, Hydrograph, Tools menu from `/api/g/tools`, undo/redo, scenarios | the app | tested (`tests/e2e/test_editor.py`, 12 tests) |
| `assistant/gtools.py` (+ `runner.ask` general) | the assistant on ANY open project: list, summary, query links, get element, explain a link (checks with guideline pages), make_scenario / design_scenario (always a new scenario), storm_scenario, lookup_criterion | editor Assistant tab; Tools "Assistant" | tested (gate G6, stand-in + one live run on Sonnet 5.5) |
| `referee/jobs/100_w19_export_scenarios.ps1` (bridge job) | exports EVERY scenario of a SewerGEMS model (a copy) through the documented OpenFlows API: conduits, manholes and outfalls with each scenario's results, geometry, the scenario list | File "Open SewerGEMS model…" lists the exports; the job is dropped into `D:\VBOX\bridge\jobs` | ran 2026-11-22 as job 101: 23 scenarios in 490 s |
| `io/sewergems_export.py` | opens such an export as a project: every scenario an app scenario (its differences as edits) holding SewerGEMS's own results | File "Open SewerGEMS model…"; results source switch (W19 engine / SewerGEMS stored); "Compare with SewerGEMS" | tested (gate G7 on the frozen referee export of SC1-2056) |
| `web/editor/` (G7, G5 additions) | File "Open SewerGEMS…" (lists bridge exports), Results source "W19 engine / SewerGEMS (stored)", Tools "Compare with SewerGEMS (stored)"; More → "Import from GIS…" (field-mapping dialog), "Export DXF", "Export CSV" | the editor | tested (`tests/e2e/test_editor.py`, 16 tests) |
