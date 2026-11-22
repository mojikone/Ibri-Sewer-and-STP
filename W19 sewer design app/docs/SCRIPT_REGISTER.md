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
