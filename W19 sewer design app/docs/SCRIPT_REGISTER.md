# Script register: every tested script and its place in the UI

Rule (engineer, 2026-11-21): a script that is built and tested gets a named place in the UI in the same change; a
script with no UI place is not done. Status: `tested` (gate or unit test green) · `in UI` (reachable from the app) ·
`planned`.

| Script | What it does | UI place | Status |
|---|---|---|---|
| `w18port/final_design.py` | flows (unit loads, peaking, infiltration, transfers, lifts) and pass-by-pass sizing of one case | Design menu → "Run design chain" (task 4) | tested (gate P0) |
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
| `engine/swmm.py` | stormwater and dynamic routing on EPA SWMM 5.2.4 (swmm-toolkit); run a model, compare every time step with a reference | Tools menu "Stormwater → Run EPA's SWMM examples and compare" | tested (gate SWMM: 14 of 15 EPA models equal at every step; Example1 a build difference) |
