# SewerGEMS inventory and the app's coverage (2026-11-23, v3)

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
- `v3`: built and tested in this pass (2026-11-23).
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
| Pressure Pipe | v3 | Bore, Hazen-Williams C / Darcy-Weisbach e (Colebrook-White) / Manning n per pipe or per project, minor loss K, check-valve flag. |
| Pressure Junction | v3 | Elevation and ground; pressure head at the junctions in the results. |
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
| GVF-Convex steady sanitary | part | The app's steady engine accumulates flow (unit loads peaked on their combined load or population, sanitary loads unpeaked, infiltration, transfers) and solves normal depth per conduit. Matched SewerGEMS's flows within 0.1 % on SC1-2056. No backwater (GVF) profile, HGL or structure losses. |
| Pressure engine (steady) | v3 | Force-main friction and minor losses; the pump's head at the flow; the operating point on its curve (from the stop and the start levels); the system curve; the discharge level is the higher of the main's crown and the water in the receiving structure; shutoff below the static lift gives Q = 0, flagged; negative pressure flagged. |
| GVF-Rational | part | Block 04 sections matched at SewerGEMS's flows. The rational method itself: gap. |
| Implicit / Explicit (SWMM) dynamic | have | EPA SWMM 5. Storm runs, plus v3: force mains (FORCE_MAIN, H-W or D-W), pump curves (Type 3), constant pumps (Type 2), storage tables, orifices, weirs, fixed tailwater, dry-weather flow with hourly patterns. |
| Pond routing (PondPack) | part | Through SWMM storage. |
| Energy cost | gap | |
| Gravity friction (Manning, Colebrook-White) | have | |
| Pressure friction method (H-W, D-W, Manning) | v3 | |
| Extreme flow setup | v3 | Settings > Peaking. |
| Pattern setup, EPS | v3 | Dry-weather EPS on SWMM with an hourly pattern. |
| Use pumped flows, wet well fixed level in steady state, controls in steady state | gap | The app passes the inflow (SewerGEMS's default with "use pumped flows" off). |
| Several named calculation options; structure loss mode | gap | |

## 3. Loading

| SewerGEMS | App | Notes |
|---|---|---|
| Unit sanitary loads (population, area, discharge, count; population equivalent) | v3 | Library (Components > Unit loads); rows of unit load and count per structure (Properties). |
| Extreme flow methods | v3 | Table (flow), Peltier and Merrimack (G201), Federov (flow), Harmon, Ten States, Babbitt (population, on the population upstream), constant, cutoff. SewerGEMS's generic equation form: gap. |
| Sanitary load (fixed, unpeaked) | have | |
| Pattern loads (dry weather) | v3 | SWMM DWF with hourly patterns. Hydrograph loads: gap. |
| Conduit infiltration (length, length x diameter, surface, count) | have | |
| RDII / RTK, LoadBuilder, Thiessen | gap | |
| Sanitary Load Control Center | part | The Nodes table with bulk edit and paste. |

## 4. Pumps and force mains

| SewerGEMS | App | Notes |
|---|---|---|
| Pump definition: design point, standard 3-point, multiple point, constant flow | v3 | EPANET's single-point convention; H = A - B Q^C through three points; straight lines through a table. |
| Pump definition: constant power, standard/custom extended, depth-flow, volume-flow | gap | |
| Efficiency, motor, VSD | gap | |
| On/off levels | have | As depths at the inlet, shown with their elevations. |
| Controls, logical controls | gap | |
| Minor losses, check valve | v3 | K per pipe; the check valve is recorded (no reverse flow in the steady run). |
| System head curves | v3 | Drawn with the pump curve and the steady duty in Pump definitions. |

## 5. Hydrology

| SewerGEMS | App | Notes |
|---|---|---|
| EPA SWMM runoff | have | |
| Rational, modified rational, SCS UH, generic UH, RTK, time-area, ILSAX; Tc methods | gap | |
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
| Scenarios | have | Edit lists with inheritance; compare. Batch run: gap. |
| Alternatives (19 types) | part | Scenarios carry all edits; separate alternatives: gap. |
| FlexTables | v3 | Sort, filter, global edit, paste and CSV, plus v3: choose columns, and a statistics row (mean, range, sum). |
| Element Symbology, Background layers, Network Navigator, Prototypes, Profiles, Time Browser | have | |
| Selection sets | v3 | Named, kept with the project (Home > Sets, Ctrl+3). |
| Queries | v3 | Field, operator, value; a new selection, added to it, or within it (Ctrl+5). |
| Engineering libraries | v3 | Pipe catalogue, sections, pump definitions, unit loads, patterns. |
| User Notifications | v3 | Validate (F8). Errors: tree, missing nodes, inverts above ground, no outfall, zero length, no size, a pump that cannot lift. Warnings: isolated, ends that are not outfalls, flat or adverse, a short pump, negative pressure, two links into an outfall, coincident structures. Each takes you to its element. |
| Graphs | part | Hydrographs per element; pump and system curves. |
| Calculation summaries | part | Summary tab. |
| ModelBuilder | have | |
| TRex, LoadBuilder, user data extensions, hyperlinks, active topology | gap | |
| Batch morph, batch split | part | Morph a selection; layout runs split at the spacing. |
| Energy and capital cost, H2S, water quality | gap / out | |

## 8. Interface

| SewerGEMS | App | Notes |
|---|---|---|
| Ribbon (File, Home, Layout, Components, Analysis, Report, View, Tools, Help), minimised ribbon, quick access | have | /v2 |
| Manager shortcuts | v3 | Ctrl+1 symbology, Ctrl+3 selection sets, Ctrl+4 navigator, Ctrl+5 query, Ctrl+6 prototypes, Ctrl+7 tables, Ctrl+9 profile, F8 notifications. |
| Drawing | have | Layout tool, morph, reconnect, split, reverse, box/polygon select, context menus. Tools for force mains, pressure junctions, orifices and weirs: v3. |
| Docking managers | part | Properties and tables dock; floating managers: gap. |

## 9. Next, in the reviewer's order of value for a sewer designer

1. Use pumped flows and a fixed wet-well level in the steady run; pump controls.
2. A backwater (GVF) profile with structure losses, for the steady HGL.
3. LoadBuilder (points or polygons to manholes); TRex from a GeoTIFF.
4. Rational and SCS hydrology on catchments; outfall tailwater curves.
5. Named calculation options; batch runs; energy cost.
