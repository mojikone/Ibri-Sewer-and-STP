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
- **Kept open:** a page reload reopens the project, its scenario and the view; the app keeps a snapshot of each open
  project in `work/sessions/` (not in git; the newest 12, at most 7 days old), so a restart of the app finds it too
  (SC1-2056's 23 scenarios: 32 MB, back in 9 s). Save still writes the GeoPackage you keep.
- **Tables like a spreadsheet:** double-click a cell to edit it (Enter moves down); click a cell and paste a column, or
  several, copied from Excel: one undoable edit, with the same rules as a single edit (a manhole's invert carries the
  pipe ends that sat at it). Editable: node kind, ground, invert, inflow, load; link kind, length, size, inverts, transfer.
- **Trace:** upstream or downstream from a manhole or pipe (Properties, or U / D): the pipes are selected and summed
  (length, nodes, load, flow leaving, the farthest manhole, failing pipes), with a profile from the farthest one.
- **Box select:** Shift+drag selects the pipes whose middle is in the box, Ctrl+drag the nodes; then edit them together.
- **Reference layers:** a GeoPackage, GeoJSON, zipped shapefile or DXF drawn under the network (Display card), with
  hover attributes; display only, kept with the open project. A layer with no CRS is read in the project's coordinates.
- **Any SewerGEMS model:** File > Open SewerGEMS model lists the exports ready to open and every SewerGEMS model (.stsw)
  in the shared folders (the VM's model share and `bridge/models`). Export writes the bridge job itself: the VM copies
  the model and SewerGEMS's own API reads the copy (every scenario, its results and loads); the dialog follows the job
  and opens the export when it is ready (Majlas: seconds; Block 04, 8 scenarios: under a minute). "Run every scenario
  first" computes each scenario on the copy before exporting, for a model saved without results (Block 04's storms take
  about 13 min each; a scenario whose calculation type is Design is re-sized by that run, as SewerGEMS's Compute would,
  and the job log says so). Box and open-channel conduits come with their shape, dimensions, barrels and n, and are solved;
  other non-circular shapes are drawn, labelled and marked not analysed. The VM watcher must be running; the dialog says
  whether it is.
- **Box and channel sections:** Properties > Cross-section turns conduits into a box (closed rectangle), an open
  rectangle or an open trapezoid, with its own n and a number of barrels, or back to a catalogue circle (one undoable
  edit). The steady engine solves them by Manning at normal depth per barrel and reports the depth, depth over rise, the
  critical depth and the full capacity; the sewer d/D limit and v max do not apply; the design leaves them as they are.
  A box beyond its free-surface maximum (above full bore, the open perimeter being shorter: 1.31 x for 3 x 1.5 m, 1.41 x
  for 10 x 2.5 m) flows full and is marked surcharged, an open section over its bank too. The status line says when the
  load set puts no load on the network (a storm model: only infiltration flows). The profile draws the rise as the crown or bank. SWMM files read and write
  RECT_CLOSED, RECT_OPEN and TRAPEZOIDAL with their barrels and n. For an export run in SewerGEMS,
  `GET .../section_check` compares the app's normal and critical depth at SewerGEMS's own flow with SewerGEMS's.
- **v5 (2026-11-23): the engineer's trial items F13-F21.**
  - **Mixed selection** (F13): a box or a click takes every element type by default; Ctrl or Shift adds and removes any
    element; the bar above Properties names each type ("2 pipes 3 structures") and switches the one being edited;
    Delete removes them all in one undo step.
  - **Alternatives** (F14, Home > Alternatives): seven kinds of data under a name and a parent, taken by scenarios and
    inherited by their children; what you change of that kind goes into the alternative, shared by every scenario that
    takes it; undo takes it back out.
  - The tool hint is a tooltip by the cursor that fades (F15); **selection sets** hold any types and are the scope of a
    design, a check or a selection (F16); profile labels stay inside the drawing (F17); the **Element Symbology pane docks
    on the left** (F18, View); **Settings by group** with paste from Excel into any table and named pipe catalogues (F19);
    **Design constraints** as their own group (F20).
  - **The assistant as an agent** (F21): it reads the folders the engineer registers (Assistant > Folders, this computer
    only, never over the shared link), inspects layers and tables, builds a project from GIS layers or a SWMM file,
    loads it with LoadBuilder, sets levels from a terrain file, edits, validates and runs it, and offers the project it
    built. It changes only what it made; each change is one undo step. It reads the open QGIS project (layers,
    fields, attribute rows, the selection) through the QGIS MCP plugin, read only, and adds a layer to a "W19"
    group when asked; it never sends QGIS code to run.
  - **A daily spending limit for the assistant** (Assistant > Limits, set on this computer only): this computer, each
    shared-link visitor and all visitors together, estimated from each answer's tokens at list prices; an answer stops
    between steps at the limit; the spend shows in the assistant pane.
  - **Phones and tablets:** below 900 px wide or 520 px high the map keeps the screen, Properties opens over it as a
    drawer when one element is chosen, the ribbon starts folded on phones, Find shrinks to its lens, dialogs fit the
    screen, touch targets grow.
  - **Flow arrows run with the flow** (F23): 46 % of the Ibri sample's pipe lines were digitised from the downstream
    end, so their arrows pointed upstream; lines are now turned on entry, and Validate names a line that misses one
    of its structures (6 in the sample, in swapped pairs, carrying the wrong length).
  - **The tables' pane by finger** (F24): a tap on the splitter opens or closes it, a finger drag resizes it, the
    arrow stays in view.
  - **On a phone** (F25-F27): only Select opens Properties; tools morph onto what they tap (24 px on touch), a structure
    tool or a layout run on a pipe splits it; Design now is the main button and a preview says it changed nothing; a
    scenario the assistant makes is offered with Open it.
  - **Terrain without uploading it** (F28, Tools > TRex): a GeoTIFF, or a VRT with its GeoTIFFs, is read in the browser
    where it is, only the blocks under the structures (Ibri's 19,112 structures through the 0.5 m VRT: 67 s); a path on
    this computer still works; Copernicus 30 m is fetched on request (a surface model: screening only, flagged by
    Validate); contours or spot levels (SHP, GPKG, GeoJSON, DXF; DWG when the free ODA File Converter is installed) by a
    TIN; each structure keeps the source of its ground level. The map box has a north arrow and Fit all (F29).
- **v6 (2026-11-24): the engineer's trial items F30-F42.**
  - **Selection:** Shift adds, Ctrl removes, with a click, a box or a polygon; a New / Add / Remove switch on a phone;
    no 3D tilt (the compass puts north up); the middle button pans in every tool.
  - **Editing as in SewerGEMS:** drag a selected structure to move it (or Move... then a tap), its lines follow; a
    pipe's right-click adds, removes or straightens bends, and a selected pipe's bends are dragged; the layout tool's
    right-click ends the run or sets the next point (a structure type, or a bend); a long press is the right-click on
    a phone.
  - **Panes:** the left dock holds Element Symbology and Background Layers as tabs, widened by its edge; closing the
    last gives the map back. Background Layers: the basemap and GIS layers with colour, opacity and order.
  - **Colour by subnetwork:** by outfall, pumping station (lifts merged), lift, or every wet well; a wet well is
    marked a lift in Properties.
  - **Made for other users:** every model has its link in the address bar (File > Copy link, File > Recent); Find
    finds tools too; a SewerGEMS model is picked from any device; tools that read the server's files show only on it.
  - **The assistant** shows each step live in plain words and answers without code; Sonnet runs at medium effort.
  - **SewerGEMS models without SewerGEMS** (F46, the clean-room rule lifted by the engineer): the .stsw.sqlite is read
    directly, every scenario, equal to SewerGEMS's own export of the Ibri final model, pumps and force mains with their
    curves included (F47); the app runs every scenario itself, SewerGEMS in the VM only for its own results.
  - Fixed after a Fable 5.2 review: an uploaded file's name could choose where the server wrote it (any folder, from
    the shared link); alternatives now replay in the order things were done (a session-wide edit clock), undo removes
    exactly its own edit from a shared alternative, a mixed batch is one undo step, a child can take its own edits,
    alternative ids are never reused, the agent's copies get private alternatives; the long section drew nothing
    (a comment swallowed two variables); a stale mixed selection could delete hidden elements; the app no longer
    locks during an assistant answer; a foreign Host header counts as remote; at most 20 strict tools (the API's
    limit, found by the live test).
- **v4 (2026-11-23): the rest of the SewerGEMS list.**
  - **GVF water profile** (Settings > Water profile, `engine/gvf.py`): from the outfalls up, direct step M1/M2 (checked on
    10 m and 5 m pipes against an independent fine integration within 2 mm), steep pipes under entrance control,
    overloaded and drowned pipes by the full-pipe friction slope, flat and adverse pipes, a structure loss K v^2/2g;
    a water level per structure, surcharge and flooding in Properties and Notifications; the long section draws it.
  - **Use pumped flows** (Settings > Force mains): downstream of a pump, what it pumps on its curve; a short pump stays
    flagged on its inflow.
  - **Controls** for the storm run (Components > Controls): a structure's depth or the time switches a pump or sets an
    orifice or weir, with an else (SWMM [CONTROLS]).
  - **LoadBuilder** (Tools): points or polygons to the nearest structures, as loads or unit-load counts, preview first.
  - **TRex** (Tools): ground levels from a terrain GeoTIFF or a VRT path (the project's 0.5 m VRT), inverts moved with
    the ground; structures off the terrain kept and reported.
  - **Rational method** (Analysis): Q = C i A / 360 with each catchment's C and Tc, the travel time and the IDF table.
  - **SCS curve number** for the storm run's infiltration (Settings > Storm run, each catchment's CN).
  - **Batch run** of several scenarios and **named calculation options** applied per scenario (Analysis).
- **v3 (2026-11-23): closer to SewerGEMS, from an inventory of its help and of its data model read through the API**
  (`docs/SEWERGEMS_INVENTORY.md`, reviewed by Fable 5.2; each item marked have / v3 / part / gap):
  - **pump stations and force mains:** pressure pipes and junctions (Layout tools), pump definitions (design point,
    three points, table, constant flow; Components > Pump definitions, with the pump curve drawn against the selected
    pump's force-main system curve and its steady duty), identical pumps in parallel, the steady pressure solve
    (`engine/pressure.py`: H-W, D-W by Colebrook-White, Manning, minor losses, discharge at the higher of the main's crown
    and the receiving structure's water, operating points from the stop and start levels, a pump that cannot lift
    flagged, negative pressure flagged), shown in Properties in plain words (short / delivers, the head needed and given);
    written to SWMM as FORCE_MAIN conduits and Type 3 pump curves;
  - **loads:** unit sanitary loads by type (population, area, discharge, count, population equivalent) as a library and
    rows per structure; extreme-flow methods Harmon, Ten States, Babbitt (on the population upstream), Federov, the
    project's table, Peltier, Merrimack, constant, a cutoff; hourly patterns and the dry-weather flow on SWMM (an EPS run);
  - **ponds:** orifice and weir outlets (Layout tools), a fixed tailwater at outfalls, all on SWMM; the steady run leaves
    pond outlets out;
  - **managers:** user notifications (Validate, F8; each note takes you to its element), selection sets, queries,
    FlexTable columns and a statistics row, SewerGEMS's manager shortcuts (Ctrl+1/3/4/5/6/7/9).
- **The ribbon interface (v2, 2026-11-23), at `http://127.0.0.1:8765/v2`:** the same editor with every tool in ribbon tabs as
  SewerGEMS's (File, Home, Layout, Components, Analysis, Report, View, Tools, Help), a quick-access bar (save, undo,
  redo), collapsible to the tab row (double-click a tab, the arrow, or Ctrl+F1; a click on a tab then shows it over the
  map). The legend is its own panel (fold, hide from View > Legend); the basemap and display controls are in View. The
  classic toolbar stays at `/` (Help > Classic toolbar). Both have, from the engineer's trial of 2026-11-23
  (`docs/USER_TRIAL_FEEDBACK.md`):
  - **Layout tool** (L): each click places the structure prototype and a pipe from the last click, until Esc,
    right-click or double-click; manholes go in between at the engineer's rounded spacing (W13's rule of 2026-08-18,
    ported with its tests to `engine/spacing.py`: 230 m at 100 m gives 80 + 80 + 70) at G203 Table 12's maximum for
    the pipe's size or at a typed maximum; a run from a manhole that already drains becomes a branch into it; one
    undo step per click;
  - **morph:** a structure tool clicked on a structure changes it to that kind (id, place, levels and pipes kept); also
    right-click > Morph to;
  - **right-click menu** on structures, pipes, catchments and the map: properties, zoom, trace, long section from here,
    reconnect start or stop to another node, reverse, split here, start a layout run, delete;
  - **units** (Components > Units, or Settings): flows, loads and infiltration in the unit chosen (L/s, m3/s, m3/h,
    m3/d, ML/d...); the model keeps its own units;
  - **the two load kinds** as SewerGEMS's, in Properties and the Nodes table: the unit load (peaked with the load upstream)
    and the sanitary load (added unpeaked);
  - **infiltration** by length (the project's 0.72 m3/d/km, G201 p72), by length x diameter, by inside surface or per
    conduit, and a conduit's own rate in its Properties;
  - **prototypes** (what a new manhole, outfall, wet well, conduit or catchment gets) and **engineering libraries** (named
    box and channel sections, applied to a selection or made the conduit prototype; the pipe catalogue);
  - **ponds and pumps for the storm run:** a storage node's area or depth-area table and a pump's capacity with its
    start and stop depths, written to SWMM; the sample "Pond and pump" is laid out on the engineer's Pond_Mouj model;
  - a server that cannot be reached (the tunnel's 502 page) is retried with a banner instead of showing an HTML page;
  - **selection:** box and polygon tools (pipes, structures or catchments; Shift adds), select by type, invert, clear;
  - **network navigator:** find connected, upstream, downstream, the path between two structures, and finds for isolated
    structures, two leaving pipes, ends that are not outfalls, pipes that reach no outfall, failing pipes, coincident
    structures.
- **Symbology (colour coding and labels), as in SewerGEMS's Element Symbology:** Display card > Symbology > Edit...
  opens a panel beside the map (the map stays live). For pipes, structures and catchments:
  - colour coding by any field: inputs (size or section, DN, length, gradient, inverts, depth at either end, ground,
    load, area, imperviousness...) and results (flow, velocity, d/D, normal and critical depth, failed checks, storm flow,
    fullness, head and flooding); calculated range, steps, equal widths or equal counts, five colour ramps, reverse,
    editable classes, an above-range class; shown as colour, line width / symbol size, or both; all elements or a kept
    selection; text fields get one class per value. The pipes' coding is picked in Colour by, the structures' and
    catchments' in their own selects (shown once a coding exists); the legend shows each class's count and a click
    selects its elements; storm fields follow the time slider;
  - labels: any number per element type, each a field with prefix, suffix (%u = its unit) and decimals, or free text
    with fields in braces ({id} L={length_m:1:u}); on the same line or the next; text size, the zoom they show from and
    whether they may overlap. Pipe labels sit at the pipe's middle along its direction;
  - named symbologies ("Default" reproduces the map as it was), switched on the Display card, kept with the project
    (its file and its session snapshot). File > Export KMZ takes the map's colouring and labels.
- **Failing pipes:** the red overlay can be switched off (Display card, or click its legend line); it stays off over a
  comparison or a storm colouring, where steady-state failures would mislead.
- **Settings tables:** the pipe catalogue, minimum gradient by size, d/D limit by size and the peaking table are edited
  in Settings and applied as one undoable edit; the self-cleansing size threshold too.
- **Keyboard and mouse:** the ? button (or the ? key) lists every shortcut.
- **Scenarios:** a manager (Scenarios...) as a tree: open, copy, rename, delete (with the scenarios copied from it), and
  compare: the open scenario coloured by what changed against another (size, levels, flow only, new pipes) with the
  differences in Tool output. Save keeps every scenario inside the GeoPackage (its layers stay the scenario on screen,
  for QGIS); Open brings them all back with their undo history and saved routes.
- **Summary tab:** pipes, km and failures as tiles (a failure tile steps through them), and length by size, by velocity
  and by d/D as bars; a bar selects its pipes.
- **Design control:** Tools > Design asks the scope (the whole network or the selected pipes), the load set, and offers
  a preview (what would change, nothing recorded) before applying; pipes locked in Properties keep their size and levels.
- **Quantities** in the team's BOQ structure (W18 `final_boq.py`): pipes by size and by size and depth band (up to
  1.5 m, every 0.5 m to 15 m, over 15 m), manholes by type (Type 1/2/3 by the largest pipe) and depth band; CSV of any
  Tool output. Rates are not read. **KMZ** for Google Earth (File menu).
- **Storm:** a time slider and play button colour the map at any reporting period of the last run; the profile shows
  the storm's peak water level at the manholes.
- **Assistant:** it is told what is selected and which profile is on screen, and can select and zoom to pipes or draw a
  profile in the editor (show_on_map, show_profile; they change nothing in the model).
- **Profile along any route:** from a manhole or pipe down to the outfall, or to any other manhole or pipe through
  via points, along the shortest path through the network in either direction (pipes walked against the flow are
  marked); pick the route by clicking on the map; the route is lit on the map and one cursor follows both ways (map
  and profile) with a readout of levels, depth, cover, flow and d/D; data bands, the minimum-cover line, flow arrows,
  CSV, PNG and SVG export. Manholes are drawn as shafts, and every pipe that joins a manhole off the route as a circle
  of its own diameter at its own invert, with a dashed line for the drop to the outgoing invert (the readout lists them).
  Routes are saved by name with the project. Long sections: zoom buttons, a scrollbar, wheel zoom at the cursor, Shift+wheel or drag to scroll, Ctrl+wheel to
  zoom the levels, double-click for the whole route.
- **Interface:** panels that drag to any size and collapse (F2 properties, F3 tables, F4 map only), remembered between
  sessions; a Display card on the map with the colour, the results source, the basemap (streets, satellite with labels,
  topographic, light or dark grey, none), its opacity, a hillshade and flow arrows; pipes drawn by size with DN and
  gradient labels close in; find by ID (Ctrl+F); E/N coordinates under the cursor; hover tooltips; failure counts that
  step through the failing pipes; a measure tool; a dark theme. Satellite and map tiles are for the screen only.
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
| Box and channel sections | **passed** 2026-11-22: Block 04's 212 open channels, its 2-year storm run by SewerGEMS (GVF-Rational) in the VM and exported with sections (bridge job 108): at SewerGEMS's flow the app's normal depth is within 0.025 % of SewerGEMS's on all 185 flowing channels (largest 0.07 mm), critical depth within 0.19 mm | `python -m pytest -m gate_sections` |
| G7 SewerGEMS models with all scenarios | **passed** 2026-11-22: the SC1-2056 referee model's 23 scenarios exported by bridge job 101 (490 s) and opened in the app with SewerGEMS's stored results; with its loads exported (jobs 102-103) the app's engine re-solves SewerGEMS's own model, every pipe within 0.1 % of SewerGEMS's flows | `python -m pytest -m gate_g7` |

**Not done yet** (approved, open):
- SewerGEMS models: infiltration is not exported yet (the app uses 720 L/day per km, the Ibri model's value); of the
  catalogue's shape codes only 3 (open rectangle) is measured, so a SewerGEMS box or trapezoid class keeps the conduit's
  typed shape until one is checked; arches, ellipses and irregular channels are not analysed; on DN200 at very low flows
  SewerGEMS's GVF velocities read up to 0.04 m/s below the app's normal-depth velocities (GVF backwater not built);
- box and channel sections are solved at normal depth (no backwater), and the design does not size them; only the open
  rectangle is checked against SewerGEMS (Block 04), the closed box and trapezoid against hand calculations only;
  whether SewerGEMS closes its shape-3 rectangle at the rise is not settled: its Design runs hold every Block 04 channel
  at 0.75 of the rise (2- and 200-year storms), so it needs an Analysis run with the sizes held;
- EPANET `.inp` (water distribution): not started;
- the hydraulics of pumps, wet wells and force mains (a pump passes its flow on; no pump curve or head is solved);
  GVF backwater; rational-method storm design and inlet capture;
- a dynamic SWMM run of a sewer from its sanitary loads (no dry-weather flow is written yet; a SWMM run needs rain);
- Babbitt and Harmon peaking;
- imported US-unit SWMM models show feet and acres under the m and ha labels, and Design is not meant for them;
- the W18 viewer (`/w18`): the design chain does not take a what-if's edits; BOQ, costs, station flows, DWG and
  schematics are still to be placed (`docs/SCRIPT_REGISTER.md`, "Planned").

All tests (2026-11-23, after v4 and its review fixes): 330 passed, 1 skipped, 2 expected failures. After v3 and its review fixes: 303 passed, 1 skipped, 2 expected failures. After v2: 277 passed, 1 skipped, 2 expected failures (the full suite, then the browser tests again after the selection tools: 68 passed). Before: (2026-11-22, after the symbology): `python -m pytest` - 252 passed, 1 skipped (a live assistant test), 2 expected
failures (EPA Example1, a SWMM build difference), 11 min, 43 end-to-end tests among them.

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
