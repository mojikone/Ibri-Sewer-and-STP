---
name: concept-saturation-population-and-load
description: "The agreed method for saturation population and load per plot (class v7 with unit-rate loads, 2026-09-10) — the engineer said \"I like it, remember this\""
metadata: 
  node_type: memory
  type: project
  originSessionId: 4c6c2c7b-00c3-4e9a-b8fc-2e647a78c88a
  modified: 2026-09-10T22:00:00.000Z
---

**The concept saturation population and load calculation, settled 2026-09-10 (class v7, live in W14).**
Full write-up: `W14/docs/W14_LOAD_AND_GROWTH.md` and the report note `W14/docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md`; scripts `W14/py/plots_meters_load.py` → `plot_class_v2_apply.py` → `growth_by_settlement.py`; the decision trail in `W14/analysis/REFINEMENTS_PENDING.md`. W13 stays the pipe-laying folder.

1. Every dwelling meter (primary, subsidised, additional tariff) is a property; meters snap to the nearest plot within 15 m. Base year 2024.
2. Built plot class: farm meter → farm (never overridden); Sentinel-2 NDVI grove (≥ 1,000 m² at NDVI ≥ 0.30, mean ≥ 0.20) → farm unless ≥ ⅔ shop or a simple government majority; then proportion: > ⅔ home → Residential, ≥ ⅔ government → Government, ≥ ⅔ shop → Commercial, between → mixed. MoH "Tourism" = the heritage old quarter, takes nothing. The RGB excess-green test is NOT used (it put farms on bare land).
3. Ratio = properties per pure home plot (Residential, < 15 meters), per settlement.
4. **Occupancy per settlement** = workbook population 2024 ÷ DOMESTIC meters, floor 4.0, cap 6.12 (Bat's, the highest among settlements ≥ 2,000 people). **Under 1,000 people in 2024: occupancy 4.0, ratio 1, home share 0.9 outright** (13 settlements; At Tayyib's 4.02 at 3,300 people is the reference). The single 5.32 is superseded.
5. Capacity per settlement = home-shaped empty plots (200–1,000 m², compact ≥ 0.6, aspect ≤ 3; not grove/industrial/heritage/estate) × home share (pure homes among built, metered, home-shaped plots) × ratio × occupancy.
6. Growth at the inception workbook's RATE only (census to 2040, extrapolation to 2050, 2.40 %/yr beyond; its 2100 total is NOT saturation), on the metered population; fill to capacity; overflow **Ibri → Al Araqi 70 % / Al Qurayn 20 % / Shalashil 10 % in parallel, then Ad Dariz, then nearest with room; At Tayyib → Miayrid first; every settlement receives**; saturation year per settlement; ultimate = the year the last one fills.
7. Spread the housed people over ALL empty plots ≤ 2,000 m² (not grove/industrial/heritage/estate) by area capped at 1,000 m² — every plot the network passes carries load; totals stay consistent.
8. Per person 164 L/d domestic, 0.22×164 non-domestic, 0.14×164 governmental (never compounded); sewage 85 % / 54 %; the two industrial estates additive (4,500 + 1,800 workers × 93 L/d) and **their meters out of the pool**; farm meters no load. **Per existing plot (2026-09-10): Q = 0.85·164·OR·N_dom + 0.54·(U_nd·N_nd + U_gov·N_gov + 93·workers)**, where U_nd / U_gov are the settlement's 22 % / 14 % pools divided by its shop / government meters outside the estates (Ibri 510 and 3,342 L/d per meter) — on every plot as `U_NDOM`, `U_GOV`; a settlement with no such meter keeps the share on its dwellings. Future plot: people × 171.3 L/d. Peaking per pipe in the engine, never per plot. Network sized on saturation. The delivered plot layer keeps only what the report or the network reads (56 fields; audit fields in `plot_class_audit.csv`); the settlement layer carries everything the report says about a settlement (69 fields); the plots sum to the settlement to the m³/d.

Result v7 (unit-rate loads, four-decimal storage): today 119,893 people / 20,852 m³/d; capacity 229,136; ultimate **2070, 349,029 people, 60,099 m³/d**; Ibri full 2056. People, occupancy and workers are stored to four decimals: at two, thousands of equal per-plot values rounded the same way and lost 13 people in Ibri.

**Why:** six earlier versions were rejected or refined in turn (one shop meter made a plot mixed; a house on a farm made it residential; the RGB green test; meter-only missed the groves; a single 5.32; a cap from Tanam that could not work). The engineer wants this exact chain reused, not re-derived.

**How to apply:** treat this as the load basis for W14 onward; change a number only at the top of the two scripts and record it in the refinements file; the report reads every number from `W14/report/facts_w14.py`. Related: [[load-basis-locked-tier-a-volume]], [[list-tasks-before-multistep-work]].
