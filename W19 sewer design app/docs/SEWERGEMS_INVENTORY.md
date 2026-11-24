# SewerGEMS inventory and the app's coverage (2026-11-23, v4)

Built clean-room from two sources only:

1. **Bentley's public help.** SewerGEMS CONNECT (SS5) and OpenFlows SewerCAD 2026 topics on docs.bentley.com; 19 pages read, feature names only.
2. **The installed SewerGEMS 10.4 data model, read through its documented API in the offline VM.**
   - Bridge job 113 with `referee/lib/DomainCatalogue.cs`; output in `D:\VBOX\bridge\out\w19\catalogue\`.
   - 31 element types.
   - 19 alternative types, holding 1,160 input fields.
   - 10 numerical engines with 266 calculation-option fields. 212 of them belong to the GVF/implicit product engine; the others carry 6 generic fields each.
   - 50 support types (libraries and definitions), holding 1,144 fields.
   - 2,349 result fields.

No SewerGEMS file was read. A Fable 5.2 review of the first draft found that it overstated the steady engine and listed planned items as built. This version corrects both.

**Status:**
- `have`: in the app and tested.
- `v3`, `v4`: built and tested in the passes of 2026-11-23 (v4: GVF profile, pumped flows, controls, LoadBuilder, TRex, rational method, curve number, batch runs, named calculation options).
- `part`: some of it.
- `gap`: not yet.
- `out`: outside a sewer design app's scope (2D surface flow, live SCADA, snow, pollutants).

## 1. Element types (31 in SewerGEMS)

| SewerGEMS element | App | Notes |
|---|---|---|
| Manhole | have | Ground, invert, unit loads (peaked) and sanitary load (not peaked). Structure headloss: gap. |
| Outfall | v3 | Free, or a fixed tailwater level (SWMM FIXED). Time-elevation and elevation-flow tailwater: gap. |
| Wet Well | part | Invert, start/stop depths (shown as elevations too), plan area or depth-area table for the storm run. Alarms and the steady fixed level: gap. |
| Pump | v3 | A link from the wet well (SWMM's convention; SewerGEMS draws a node with a downstream link). Definition, start/stop, and identical pumps in parallel (count). |
| Pressure Pipe | v3 | Bore, Hazen-Williams C / Darcy-Weisbach e (Colebrook-White) / Manning n per pipe or per project, minor loss K. Splitting one keeps both halves' values and inserts a pressure junction. |
| Pressure Junction | v3 | Elevation and ground (a prototype of its own). Pressure head is given at the force main's pipe ends, not per junction. |
| Conduit | have | Circular (catalogue), box, open rectangle, trapezoid, barrels, n; infiltration per conduit. |
| Channel | part | As open-rectangle and trapezoid conduits. |
| Catchment | have | SWMM runoff (area, imperviousness, width, slope, n). Rational, SCS UH and RTK: gap. |
| Pond | v3 | A storage node with a constant area or a depth-area table. |
| Pond Outlet Structure | v3 | Orifice (circular or rectangular, Cd, offset, flap gate) and weir (rectangular or V-notch, crest, Cd) links, written to SWMM. Composite outlet and rating curve: gap. |
| Catch Basin, inlets | gap | |
| Transition, Cross Section node, Headwall, Property Connection, Tap, Lateral, Gutter | gap | |
| Air Valve, Pump Station, VSP battery | gap | |
| LID | gap | |
| SCADA, Grid2D, Boundary, Surface polygon, line, point, Profile path | out | |

## 2. Solvers and calculation options

| SewerGEMS | App | Notes |
|---|---|---|
| GVF-Convex steady sanitary | v4 | The steady engine accumulates flow (unit loads peaked on their combined load or population, sanitary loads unpeaked, infiltration, transfers), matched SewerGEMS's flows within 0.1 % on SC1-2056, and (v4, Settings > Water profile) carries a gradually varied water profile up from the outfalls: direct step M1/M2, steep (entrance control), full pipes by their friction slope, a structure loss K v^2/2g; water level per structure, surcharge and flooding flagged; the long section draws it. Checked against an independent fine integration within 2 mm. Circular pipes; boxes and channels keep normal depth. |
| Pressure engine (steady) | v3 | Force-main friction and minor losses; the pump's head at the flow; the operating point on its curve (from the stop and the start levels); the system curve; the discharge level is the higher of the main's crown and the water in the receiving structure; shutoff below the static lift gives Q = 0, flagged; negative pressure flagged. |
| GVF-Rational | part | Block 04 sections matched at SewerGEMS's flows. The rational method itself: gap. |
| Implicit / Explicit (SWMM) dynamic | have | EPA SWMM 5. Storm runs, plus v3: force mains (FORCE_MAIN, H-W or D-W; a Manning main as a full circular conduit), pump curves (Type 3, strictly falling, n pumps in parallel), constant pumps (Type 2), storage tables, orifices, weirs, fixed tailwater, dry-weather flow with hourly patterns. The dry-weather switch applies to projects made in the app; an imported .inp keeps its own [DWF]. |
| Pond routing (PondPack) | part | Through SWMM storage. |
| Energy cost | gap | |
| Gravity friction (Manning, Colebrook-White) | have | |
| Pressure friction method (H-W, D-W, Manning) | v3 | |
| Extreme flow setup | v3 | Settings > Peaking. |
| Pattern setup, EPS | v3 | Dry-weather EPS on SWMM with an hourly pattern. |
| Use pumped flows | v4 | Settings > Force mains: downstream of a pump, its inflow (default) or what it pumps on its curve. Wet-well level fixed in steady state: the lift is from the stop or start level. Controls in the steady run: gap. |
| Several named calculation options | v4 | Named sets of options saved with the project and applied to a scenario (Analysis > Calculation options). Structure loss methods beyond K v^2/2g (HEC-22, AASHTO): gap. |

## 3. Loading

| SewerGEMS | App | Notes |
|---|---|---|
| Unit sanitary loads (population, area, discharge, count; population equivalent) | v3 | Library (Components > Unit loads); rows of unit load and count per structure (Properties), for every load set or for one. |
| Extreme flow methods | v3 | Table (flow), Peltier and Merrimack (G201), Federov (flow), Harmon, Ten States, Babbitt (population, on the population upstream), constant; a cutoff capping any of them. A population method with no population is a notification. SewerGEMS's generic equation form: gap. |
| Sanitary load (fixed, unpeaked) | have | |
| Pattern loads (dry weather) | v3 | SWMM DWF with hourly patterns. Hydrograph loads: gap. |
| Conduit infiltration (length, length x diameter, surface, count) | have | |
| LoadBuilder | v4 | Points or polygons (by their centre) to the nearest manhole, wet well or storage, summed, as loads or unit-load counts; preview, then one undo step. |
| Sanitary Load Control Center | part | The Nodes table with bulk edit and paste. |

## 4. Pumps and force mains

| SewerGEMS | App | Notes |
|---|---|---|
| Pump definition: design point, standard 3-point, multiple point, constant flow | v3 | EPANET's single-point convention; H = A - B Q^C through three points; straight lines through a table. |
| Pump definition: constant power, standard/custom extended, depth-flow, volume-flow | gap | |
| Efficiency, motor, VSD | gap | |
| On/off levels | have | As depths at the inlet, shown with their elevations. |
| Controls | v4 | Rules for the storm run (SWMM [CONTROLS]): a structure's depth or the time against a value switches a pump or sets an orifice or weir, with an else. Logical controls with several conditions: gap. |
| Minor losses | v3 | K per pipe. Check valves: gap (the steady run has no reverse flow; SWMM pumps do not run backwards). |
| System head curves | v3 | Drawn with the pump curve and the steady duty in Pump definitions. |

## 5. Hydrology

| SewerGEMS | App | Notes |
|---|---|---|
| EPA SWMM runoff | have | |
| Rational method | v4 | A steady storm run: Q = C i A / 360 with each catchment's C and Tc, the travel time down the pipes and the IDF table. |
| Storm data: IDF tables, time series | part | IDF table (alternating block) and time series. |

## 6. Gravity structures and design

| SewerGEMS | App | Notes |
|---|---|---|
| Junction headloss methods | gap | |
| Constrained design | have | d/D at the minimum gradient, crowns matched, cover. |
| Tractive force design, inlet capacity | gap | |

## 7. Managers and tools

| SewerGEMS | App | Notes |
|---|---|---|
| Scenarios | have | Edit lists with inheritance; compare; batch run of several scenarios side by side (v4). |
| Alternatives (19 types) | v5 | Seven kinds (physical, sanitary loading, infiltration, hydrology and rain, boundary conditions, operational, calculation options) with parents, taken per scenario and inherited by its children; an edit of a kind goes into the alternative the scenario takes (Home > Alternatives). SewerGEMS splits physical and the rest further: 7 of 19. |
| FlexTables | v3 | Sort, filter, global edit, paste and CSV, plus v3: choose columns, and a statistics row (mean, range, sum). |
| Element Symbology, Background layers, Network Navigator, Prototypes, Profiles, Time Browser | have | |
| Opening a SewerGEMS model | v6 | Read directly from its .stsw.sqlite, every scenario, without SewerGEMS (equal to SewerGEMS's own export on the Ibri final model), pumps, wet wells and force mains with their pump curves, and variable-speed pump batteries (run at full speed, 1 + lag pumps) included; box or channel dimensions not read yet. A large model is sent in compressed pieces. Through SewerGEMS in the VM when every scenario is to be computed. |
| Background layers | v6 | The basemap and GIS layers (shapefile with sidecars, zip, GeoPackage, GeoJSON, KML, DXF) under the network: visibility, colour, opacity, order, zoom, kept with the project. Raster images: gap. |
| Bends (vertices) | v6 | Add, remove and drag a pipe's bends; the layout tool draws through bends (right-click > Bend); moves and splits keep them. |
| Selection sets | v5 | Named, any element types together, kept with the project; design, check or select just a set (Home > Sets, Ctrl+3). |
| Queries | v3 | Field, operator, value; a new selection, added to it, or within it (Ctrl+5). |
| Engineering libraries | v3 | Pipe catalogue, sections, pump definitions, unit loads, patterns. |
| User Notifications | v3 | Validate (F8). Errors: tree, missing nodes, inverts above ground, no outfall, zero length, no size, a pump that cannot lift. Warnings: isolated, ends that are not outfalls, flat or adverse, a short pump, negative pressure, two links into an outfall, coincident structures. Each takes you to its element. |
| Graphs | part | Hydrographs per element; pump and system curves. |
| Calculation summaries | part | Summary tab. |
| ModelBuilder | have | |
| TRex | v5 | Ground levels from a terrain GeoTIFF or VRT read in the browser (no upload, any size), a path on this computer, or Copernicus 30 m fetched on request; reprojected; the inverts moved with the ground when asked; each level keeps its source. Contours and spot levels (SHP, GPKG, GeoJSON, DXF; DWG through the ODA File Converter) by a TIN. |
| Batch morph, batch split | part | Morph a selection; layout runs split at the spacing. |
| Energy and capital cost, H2S, water quality | gap / out | |

## 8. Interface

| SewerGEMS | App | Notes |
|---|---|---|
| Ribbon (File, Home, Layout, Components, Analysis, Report, View, Tools, Help), minimised ribbon, quick access | have | /v2 |
| Manager shortcuts | v3 | Ctrl+1 symbology, Ctrl+3 selection sets, Ctrl+4 navigator, Ctrl+5 query, Ctrl+6 prototypes, Ctrl+7 tables, Ctrl+9 profile, F8 notifications. |
| Drawing | have | Layout tool, morph, reconnect, split, reverse, box/polygon select, context menus. Tools for force mains, pressure junctions, orifices and weirs: v3. |
| Docking managers | part | Properties and tables dock; floating managers: gap. |

## 9. Next

v5 built the engineer's F13-F21 (`docs/USER_TRIAL_FEEDBACK.md`). Then: structure loss methods (HEC-22, AASHTO), logical controls, SCS unit hydrographs and Tc methods, RDII, energy cost.
