# W11b stage 8 - export, and the levels stage that does not exist

*W11b-s8_export-1.0, built 2026-09-03 13:33. Nothing imported from `W8/py/sewnet`, `W10/py` or `W11a/py`.*

## The uncomfortable answer first

**There is no stage 6 in W11b, so this stage had to build one.** Every invert, diameter, gradient, velocity, depth of flow, cover and drop in this export came out of a levels-and-sizes pass written inside `s8_export.py`, tagged `STAGE = 's8_export/levels-standin'` on every published row. It is a single strict pass; philosophy sec 7 asks for two and then an audit.

**And what it measures is not a tree problem. It is flatness.** **4,903 of 56,935 chambers (8.6 %) pass the 12 m cover cap** (G203-p33), covering **131.7 km** of the 1,491.9 km network, and **4,448 of them have no exit** under philosophy sec 5 - neither a recovery within 500 m nor an outfall within 1,000 m, or the excursion forces a drop past 20 m and the exit is withdrawn. The deepest chamber carries **85.7 m of cover**. That is not a levelling error and it is not the tree: **92.5 % of the length is DN200**, whose Table 11 minimum is 5.00 mm/m (G203-p29), and **84.7 % of the length is laid at its governing MINIMUM gradient rather than at the ground's own fall** - which is what it means to say the ground is flatter than the pipe may be laid. There the pipe sinks whichever way it points.

**The 85 stations s7 located are worth 753 chambers.** Run the same levels with each station resetting the depth at its anchor chamber and the breach count falls 4,903 -> 4,150 and the no-exit count 4,448 -> 3,507. **The published layers are the GRAVITY-ONLY arm**, because the stations are not in the written topology (H16) and their rising mains discharge to nodes this graph does not contain. Putting them in the levels but not in the graph would publish a network that carries its own flow twice.

**And the first long section this stage drew found something no table had shown: some outfalls are near the TOP of their own catchment.** Over the 15.4 km of package P003 the invert falls in a straight line while the ground RISES. Measured over all 195 components: **55 discharge at their own lowest chamber**, and **42 components of 20 chambers or more (389.5 km, 26.1 % of the network) discharge with MORE THAN HALF their catchment below the outlet**; the worst outfall sits **22.8 m above the lowest chamber it serves**. That is a stage-2 / stage-3 orientation result, not a levelling one - no invert arithmetic recovers a terminal placed uphill of its own catchment. The table is `outfall_check` in the GeoPackage and in `W11b_outfall_check.csv`.

**Which of the two costs more depth, measured rather than asserted.** Over the 125 components of 20 chambers or more, Spearman rank correlation against the deepest chamber in the component: **flow-path scale (component length) +0.810**, **outfall height above its own lowest chamber +0.765**, share of the catchment below the outlet +0.352. So length dominates - which is flatness, because the length is being laid at the minimum gradient - and outfall placement is a close second. It is not one or the other, and the ranking is the useful part: fixing the tree helps most where the run is longest.

## What was built

| Path | What |
|---|---|
| `W11b/shp/W11b_export.gpkg` | 9 contract layers + the check table, the manifest and the assumptions |
| `W11b/shp/kmz/*.kmz` | **22 styled Google Earth files**, each with subfolders and a legend overlay |
| `W11b/export/shp/` | 13 shapefiles + tables, every one proven to round-trip without losing a field name |
| `W11b/export/dxf/` | 2 drawings - geometry, and geometry with every chamber and pipe labelled |
| `W11b/export/schedules/` | 10 workbooks - chambers, pipes, stations, rising mains, connections, crossings, packages, quantities, not-served, data dictionary |
| `W11b/export/profiles/` | 7 long sections |
| `W11b/export/sewergems/` | the model package, the field map, the read-me and a runnable EPA SWMM 5 `.inp` |
| `W11b/export/qgis_load_W11b.py` | the PyQGIS loader, generated from the SAME View objects the KMZ used |

## The design, measured

| | | Source |
|---|---|---|
| Gravity sewer | **1,491.9 km** | s4's chamber-to-chamber segments |
| Chambers | **56,935** (38.2 per km) | s4; built network 34.2/km |
| Components, each ending at exactly one outfall | **195** | H15 |
| Diameters | **DN200-900** | H8, sized on flow alone |
| Laid gradient | 0.10 - 46.45 %, median 0.50 % | 0.05 % steps, P1 |
| Peak flow, largest reach | **225.6 L/s** | s5 published 234.7 |
| Velocity at peak | 0.09 - 1.80 m/s, **0 over the 3.0 m/s maximum** | G203-p27 |
| d/D at peak | max 0.650, **0 reaches over the Table 10 limit** | G203-p27 Tab 10 |
| Cover | median 2.02 m, deepest **85.71 m** | G203-p33 |
| Below the 1.30 m minimum cover | **0.00 km** | G203-p33 |
| Backdrops (0.60-2.00 m) | 1,096 | G203-p30 |
| **Vortex drop shafts (> 2.00 m)** | **1,775** | G203-p30. NAMA's built network has 37 |
| Inlets under 90 deg | 2,797 | G203-p30, H10 |
| Draining against the ground | **26.4 %** of length (393.2 km) | philosophy sec 4; NAMA's own built network runs uphill on 34 % |
| Load connected | **70,406.2 m3/d** over 53,018 plots | s4; s5 published 70,405.5 |
| Properties | 93,320 | s4 |

### Self-cleansing, and the size of the tau exposure

**1,369.0 km (91.8 %) is self-cleansed by the TRACTIVE route**, 123.0 km (8.2 %) by velocity, and 0.00 km by neither. G203-p27 4.2.2.1 offers the two as alternatives and requires the steeper, so the tractive share is legal - and it is also the exact extent of the scheme resting on tau = 1 Pa, which the guideline never gives (GAP-9). At 2.0 Pa every one of those gradients rises 2.346x.

### What set each diameter, and what set each gradient

| Diameter set by | Reaches | km | | Gradient set by | Reaches | km |
|---|---|---|---|---|---|---|
| capacity | 1141 | 29.9 | | cover_min | 8789 | 227.9 |
| dod | 3156 | 82.2 | | ground | 11 | 0.3 |
| minimum | 52443 | 1,379.8 | | table11 | 8817 | 226.9 |
|  |  |  | | uniform | 39123 | 1,036.9 |

`depth` and `cover` are not in the SIZED_BY vocabulary and cannot be: oversizing a pipe to lay it flatter is prohibited by G203-p29 and by Ten States sec 33.43 independently, so the prohibited move is not expressible on the layer.

### The wadi and dual-carriageway register, MEASURED

**845 registered contacts** - 826 wadi, 19 dual carriageway - over **81.24 km** of wadi ground and **0.592 km** of dual carriageway. The angle is measured against the nearest stream line's own direction, sampled every 3 m off the 50-year hazard grid: **median 36.5 deg, minimum 0.0 deg, and only 206 of 845 sit within 25 deg of square.** The rest run ALONG the channel rather than across it, which H1 forbids and H1a does not excuse. `APPROVED = 0` on every row: MoAFWR consent (G201-p85) and the roads authority's are open items, not silent ones.

*W11a published `ANGLE_DEG = 90` on 3,290 crossings. It was fabricated and the measured minimum was 0.00 deg. This register measures every one.*

### CAN_DRAIN, answered for the first time

s4 published `CAN_DRAIN cannot run - no designed invert exists at stage 4`. There is one now. **47,497 of 53,018 connected plots can reach their chamber on gravity**; **5,521 cannot** - the sewer invert sits above the property outlet at the G203-p19 3.4 minimum HCC depth of 1.2 m, with the 3 % minimum gradient of G203-p18 Table 5 over the connection's own length. They are in `W11b_schedule_not_served.xlsx`, sheet 2, each named.

## What does NOT validate, and why each one is real

`contract.validate()` was run over every published layer before a single schedule, drawing or model file was written. Nothing was silenced. The full text of every objection is in the `contract_check` layer of the GeoPackage and on the last sheet of the data dictionary.

| Layer | Result |
|---|---|
| `nodes` | **CONTRACT VIOLATION** |
| `reaches` | **CONTRACT VIOLATION** |
| `connections` | **CONTRACT VIOLATION** |
| `stations` | **CONTRACT VIOLATION** |
| `rising_mains` | **CONTRACT VIOLATION** |
| `crossings` | PASSES |
| `packages` | PASSES |
| `crossings <-> reaches` | **REGISTER DOES NOT RESOLVE** |

| What fails | Extent | Whose it is |
|---|---|---|
| Depth / cover / drop past the contract's 40 m and 20 m range guards | 906 chambers, 257 drops, worst 83.1 m | **the design.** Flatness, not arithmetic |
| Past the 12 m cap with no sec 5 exit | 4,448 chambers, 4,519 reaches | **stage 7's**: every one is a station demand |
| `SLOPE_LAID` over the contract's 25 % bound | 11 reaches, worst 46.45 % | **the ground.** Capping them put the pipe above the surface, which is not a conservative answer but an impossible one |
| `LEN_M` under the 0.5 m floor | 1 reach (0.464 m) | s4's chamber spacing |
| `connections` geometry invalid | 2,279 zero-length connections | s4: the chamber stands on the property's own connection point. Shapely calls a zero-length LineString invalid |
| `FLOOD_LV` null on all 85 stations | 85 | **NWS.** `hazard.flood_level_m_aod()` raises by design - the grids carry an AR&R hazard CLASS and no water level, and G203-p38 7.2 needs the 1:50 water surface for the 300 mm freeboard. Filling it with ground level (which this stage did on its first build) manufactured a freeboard failure on all 85 that says nothing about any |
| Rising mains under 0.75 m/s at design MINIMUM flow | 85 | **s7's**, inherited unchanged |
| `WELL_M3` disagrees with 0.25 Q T | 1 station | **s7's**, inherited unchanged |
| 2 reaches touch BOTH a wadi and a dual carriageway | 2 | **the contract's**: a reach carries one `CROSS_ID` and cannot be registered against two obstacles |

## What this export could NOT do

1. **Design the trunk.** `W11b_hier.gpkg|trunk` is 85.49 km of the client's own Main Pipe in 54 pieces, with no chambers and no topology. Nothing here drains into it. The 195 outfalls are subnetwork outlets, each an independent discharge, and the biggest reach in the design therefore carries a fraction of what a joined network would - s5 measured the like-for-like figure at 1,362 L/s and tagged it a hypothetical. It is still one.
2. **Resolve the station ids.** s7 minted `NODE_UID` N0000001-N0000085; those strings also exist in the chamber layer on different chambers, and none of the 85 agree on ground level. Re-anchored by proximity - median 0.00 m, max 65.9 m, 75 of 85 within 1 m - and published as `ANCHOR_ND` with `ST_SNAP_M` beside it. A recovered anchor is not written topology (H16).
3. **Phase anything.** `PHASE = 0` on every row: the contract's own words are "0 = not yet assigned". Packages are one per subnetwork - which satisfies "one tree, one outlet" by construction and the 3.5-40 km size band only where it happens to: 31 of 195 do, largest 206.8 km, median 0.82 km.
4. **Run the second pass.** Philosophy sec 7 wants a strict pass, a review pass and then the audit. This is one strict pass. Nothing here absorbs a finger, moves a sub main onto a through-street or puts a station on a package seam.
5. **Referee its own hydraulics.** The SewerGEMS package and the SWMM `.inp` are written but not run. A solver will not object to a chamber 85 m deep - it deepens forever - so the referee checks the hydraulics and never the routing.

## Every number this stage used that is not already in `criteria`

| Name | Value | Source | Why |
|---|---|---|---|
| `MIN_COVER_CROWN` | 1.3 | G203-p33 4.6.3 | minimum cover to crown; sets the shallowest invert a reach may be laid at |
| `MAX_COVER` | 12.0 | G203-p33 | the cover cap; past it philosophy sec 5's ladder starts |
| `EXIT_RECOVER_M` | 500.0 | philosophy sec 5 | cover must come back under the cap within this distance for the first exit |
| `EXIT_OUTFALL_M` | 1000.0 | philosophy sec 5 | the run must reach its outfall within this distance for the second exit |
| `DROP_TRIGGER` | 0.6 | G203-p30 | invert difference above which an external ramped backdrop is required |
| `BACKDROP_MAX` | 2.0 | G203-p30 | backdrop maximum height; beyond it a vortex drop shaft |
| `DROP_CEILING_M` | 20.0 | PROJECT ASSUMPTION (criteria) | the drop a vortex shaft is assumed buildable to. G203 gives no maximum |
| `SLOPE_STEP` | 0.0005 | PROJECT RULE (user 2026-08-23) | gradients are laid on round 0.05 % steps so the drawing matches the levels |
| `V_MAX` | 3.0 | G203-p27 4.2.2.2 | gravity maximum velocity |
| `TAU_PA` | 1.0 | ASSUMPTION GAP-9 (G203-p27 gives no numeric tau) | the tractive stress every tractive-governed gradient rests on |
| `MANNING_N_EXPORT` | 0.013 | ASSUMPTION (G203-p27 derivation n=0.013) | Manning n written into the SewerGEMS/SWMM package; a MODEL parameter, never a design value on the pipe |
| `INFILT_L_D_KM` | 720.0 | G201-p72 7.4.3 | infiltration for a NEW network, unpeaked |
| `PF_HOLD_PROPERTIES` | 100 | G201-p71 7.4.2 | below this many properties G201 prescribes no peak-factor formula, so PF is HELD at 1.0 and said so |
| `MH_DIA_STD_M` | 1.2 | PROJECT ASSUMPTION - G203 gives no table of chamber size against depth (searched: p29-30 sec 4.4) | standard chamber internal diameter used for the take-off. G203-p30 requires at least 1.5 m wherever an internal backdrop is unavoidable, so a chamber carrying a backdrop is written up to that |
| `SLOPE_MAX_LAID_PCT` | 25.0 | PROJECT BOUND - declared in contract.REACHES.SLOPE_LAID (hi=25.0) | the steepest gradient a gravity sewer is laid at. G203 gives NO maximum gradient - it caps VELOCITY at 3.0 m/s (p27 4.2.2.2), and on this network the velocity cap never binds because the flows are tiny, so a DN200 carrying 0.5 L/s solved to a 46.45 % laid gradient down a cliff. Past this bound the fall is taken at a drop chamber (philosophy sec 5) instead of by the pipe |
| `TRENCH_SIDE_M` | 0.3 | PROJECT ASSUMPTION - no guideline trench width was found | working space each side of the barrel in the excavation take-off. The take-off is declared indicative and is NOT a bill of quantities |

*TRACTIVE STRESS tau = 1 Pa - AN ASSUMPTION, NOT A GUIDELINE VALUE. PAM-GUD-203 sec 4.2.2.1 (p27) gives the equation Smin = K tau^1.23 Q^-0.461 and no numeric design tau (GAP-9). At tau = 1.0 Pa the required gradients are the shallowest the method allows, so the pipes are shallower and the stations fewer. If NWS return tau = 2.0 Pa every tractive-governed gradient rises by 2.346x and every level downstream of it changes.*

## The KMZ set

| File | The question it answers |
|---|---|
| `W11b_constraint.kmz` | Show me only the breaches, ranked, with everything compliant greyed out. |
| `W11b_pumping_demand.kmz` | Which chambers pass the 12 m cover cap with no way back out? |
| `W11b_tier.kmz` | Is this a hierarchy, or a flat mat of pipe? How many things touch the trunk? |
| `W11b_crossings.kmz` | Does the design CROSS these things, or does it run ALONG them? |
| `W11b_ground_fall.kmz` | THE W11b QUESTION. How much of this network carries flow UPHILL? |
| `W11b_drops.kmz` | How many vortex drop shafts does this layout demand? NAMA built 37. |
| `W11b_depth.kmz` | Where does this design get expensive, and where does it pass the 12 m cap? |
| `W11b_stations.kmz` | How many stations, how big, and how hard are they working? |
| `W11b_subnet.kmz` | How many separate systems is this really, and does each end at one outfall? |
| `W11b_chambers.kmz` | Where are the deep chambers, and are they clustered or scattered? |
| `W11b_diameter.kmz` | Where are the big pipes, and how much of the scheme depends on DN above 1200? |
| `W11b_sized_by.kmz` | Did anything on this network get its size from depth rather than flow? |
| `W11b_grad_by.kmz` | Where is the design fighting the ground, and where is it just obeying Table 11? |
| `W11b_flow.kmz` | Does the flow grow the way a tree should — small at the tips, large at the trunk? |
| `W11b_velocity.kmz` | Which pipes will silt up? Not the same question as: which pipes are legal? |
| `W11b_clean_by.kmz` | How much of this scheme rests on an assumed tractive stress? |
| `W11b_capacity.kmz` | What is surcharged, or close to it? |
| `W11b_rising_mains.kmz` | Where does the scheme pump, how far, and how long does sewage sit in the main? |
| `W11b_package.kmz` | What does one contract actually contain, and can it be commissioned alone? |
| `W11b_material.kmz` | Is the material consistent with the diameter and the laying method? |
| `W11b_packages_area.kmz` | What ground does each contract cover, and do the areas nest sensibly? |
| `W11b_can_drain.kmz` | Which plots sit BELOW the sewer that is supposed to serve them? |

## Run log

```
[    0.0s] assembling from the published stage layers
[    0.9s]    read chambers        56,935  W11b_chambers.gpkg
[    0.9s]    read segments        56,740  W11b_chambers.gpkg
[    0.9s]    read connections     53,018  W11b_chambers.gpkg
[    0.9s]    read unserved         3,396  W11b_chambers.gpkg
[    0.9s]    read hier reaches    12,566  W11b_hier.gpkg
[    0.9s]    read trunk               54  W11b_hier.gpkg
[    0.9s]    read corridors       12,665  W11b_roads.gpkg
[    0.9s]    read flow arcs       12,816  W11b_flows.gpkg
[    0.9s]    read stations            85  W11b_pumps.gpkg
[    0.9s]    read rising mains        85  W11b_pumps.gpkg
[    0.9s]    note: 90 segments (1.76 km) carry an ARC_CID stage 3 never tiered; written as 'lateral', the lowest tier, so the diameter floor is the weakest and nothing is flattered
[    1.1s]    note: vocabulary: SRC 'draft_base'/'draft_propo' -> 'dwg_road' (both are road centrelines from the one clean DXF); CONFIDENCE 'corroborated' -> 'drafted'. 26,268 segments on the PROPOSED road layer were floored to 'provisional' (philosophy sec 4: a platted reserve is never reported as existing)
[    1.3s]    note: STATION IDS DO NOT RESOLVE: 65 of 85 station NODE_UIDs also exist in the chamber layer on a DIFFERENT chamber (zero agree on ground level). Re-anchored by proximity: median 0.00 m, max 65.9 m, 75 within 1 m. Published as ANCHOR_ND with ST_SNAP_M beside it, and the station's own id is now PS#####
[    1.4s] levels [gravity only - PUBLISHED]: sizing 56,740 reaches on flow
[    1.8s] levels [gravity only - PUBLISHED]: walking 56,935 chambers in topological order
[    2.6s] levels [gravity only - PUBLISHED]: solving depth of flow and velocity at the laid gradient
[    3.0s] levels [with the 85 s7 stations - measured, NOT published]: sizing 56,740 reaches on flow
[    3.2s] levels [with the 85 s7 stations - measured, NOT published]: walking 56,935 chambers in topological order
[    4.5s] levels [with the 85 s7 stations - measured, NOT published]: solving depth of flow and velocity at the laid gradient
[    4.8s] measuring the wadi contact off the 50-year hazard grid
[    8.9s]    580,313 sample points at 3 m along 56,740 reaches
[   12.7s]    crossings register: 845 rows (826 wadi, 19 dual), 81.24 km on wadi ground, 0.59 km on a dual carriageway; 206 within 25 deg of square
[   12.9s]    195 packages (one per subnetwork). 31 sit inside the contract's 3.5-40 km band; largest 206.8 km, median 0.82 km
[   13.9s]    connections: CAN_DRAIN answered for the first time - 47,497 of 53,018 plots can reach their chamber on gravity at the 3 % minimum (G203-p18 Tab 5); 5,521 cannot
[   16.9s]    folded the graduated views on their own class labels: depth (5), ground_fall (5), capacity (3), velocity (3), flow (5), chambers (5)
[   16.9s]    outfall check: 55 of 195 components discharge at their OWN lowest chamber; 42 components of 20+ chambers (389.5 km) discharge with more than half their catchment BELOW the outlet; worst 22.8 m above its own low point
[   17.2s] contract check: nodes=FAIL, reaches=FAIL, connections=FAIL, stations=FAIL, rising_mains=FAIL, crossings=pass, packages=pass, crossings <-> reaches=FAIL
[   18.0s]    wrote nodes           56,935  -> W11b_export.gpkg
[   19.2s]    wrote reaches         56,740  -> W11b_export.gpkg
[   19.6s]    wrote connections     53,018  -> W11b_export.gpkg
[   19.6s]    wrote stations            85  -> W11b_export.gpkg
[   19.6s]    wrote rising_mains        85  -> W11b_export.gpkg
[   19.6s]    wrote crossings          845  -> W11b_export.gpkg
[   19.7s]    wrote packages           195  -> W11b_export.gpkg
[   19.7s]    wrote trunk               54  -> W11b_export.gpkg
[   19.7s]    wrote package_areas      195  -> W11b_export.gpkg
[   19.7s]    wrote contract_check       8  -> W11b_export.gpkg
[   19.7s]    wrote manifest            33  -> W11b_export.gpkg
[   19.7s]    wrote assumptions         22  -> W11b_export.gpkg
[   19.7s]    wrote levels_arms         12  -> W11b_export.gpkg
[   19.8s]    wrote outfall_check      195  -> W11b_export.gpkg
[   22.0s]    W11b_nodes.shp                56,935 features, 41 fields, round trip clean
[   24.9s]    W11b_reaches.shp              56,740 features, 51 fields, round trip clean
[   26.6s]    W11b_connections.shp          53,018 features, 22 fields, round trip clean
[   26.6s]    W11b_stations.shp                 85 features, 27 fields, round trip clean
[   26.6s]    W11b_rising_mains.shp             85 features, 23 fields, round trip clean
[   26.7s]    W11b_crossings.shp               845 features, 15 fields, round trip clean
[   26.7s]    W11b_trunk.shp                    54 features, 7 fields, round trip clean
[   26.7s]    W11b_package_areas.shp           195 features, 13 fields, round trip clean
[   34.5s]    W11b_network.dxf             32.5 MB
[   52.8s]    W11b_annotated.dxf           74.2 MB
[   60.7s]    W11b_schedule_chambers.xlsx             56,935 rows
[   74.5s]    W11b_schedule_pipes.xlsx                56,740 rows
[   74.5s]    W11b_schedule_stations.xlsx                 85 rows
[   74.5s]    W11b_schedule_rising_mains.xlsx             85 rows
[   80.5s]    W11b_schedule_connections.xlsx          53,018 rows
[   80.5s]    W11b_schedule_crossings.xlsx               845 rows
[   80.5s]    W11b_schedule_packages.xlsx                195 rows
[   80.6s]    W11b_quantities.xlsx                        51 rows
[   81.1s]    W11b_schedule_not_served.xlsx            8,917 rows
[   81.2s]    W11b_data_dictionary.xlsx                  178 rows
[   91.0s]    24 long sections -> W11b_long_sections.pdf (0.6 MB) + 6 PNG
[   93.4s]    W11b.inp                     17.1 MB  (EPA SWMM 5, average DWF only)
[   93.5s]    SewerGEMS package: 56,740 manholes, 195 outfalls, 56,740 conduits, LOADS.csv carries AVERAGE flow with our peak beside it
[   93.5s] rendering 22 KMZ views through w11b.present, off W11b_export.gpkg
[  288.1s]    qgis_load_W11b.py             119 kB  22 styled layers, 6 layouts
```