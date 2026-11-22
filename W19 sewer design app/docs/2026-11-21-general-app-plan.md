# The general app — plan (approved 2026-11-21)

Engineer, 2026-11-21: *"this app you created only runs for this project! i want to be able to use it as sewergems,
create and run end to end for both sewer and stormwater"*, then *"do it as complete and close to SewerGEMS, ensure all
scripts have a tool in UI, wire or keep in memory as you go and test to ensure it works fine, as SewerGEMS does."*
Defaults approved: GeoPackage project file; any projected CRS or local metres; EPA SWMM 5 for stormwater; the steady
engine designs sewers, with SWMM as a second (dynamic) analysis; small SewerGEMS checks through the bridge.

## Standing rules

- Every script gets its tool in the UI in the same change (`docs/SCRIPT_REGISTER.md`).
- Every stage ends with its tests green (unit, API, Playwright), committed and pushed.
- Clean room (`docs/CLEAN_ROOM.md`); numeric values trace to a guideline page or to a project setting the user enters.

## The general model (`sewerapp/model/general.py`)

| Table | Fields |
|---|---|
| nodes | `id` (stable string id; every edit, result and test addresses elements by id, never by row), `kind` (manhole, outfall, storage, junction), `x`, `y`, `ground`, `invert`, `inflow_m3d` (added unpeaked); loads live only in the load sets |
| links | `id`, `kind` (conduit, pump), `from_node`, `to_node`, `length_m`, `dn_mm`, `inside_mm`, `up_inv`, `dn_inv`, `transfer` (a conduit that carries its upstream flow as a transfer, unpeaked: W18 gravity joins) |
| catchments | `id`, `outlet`, `area_ha`, `imperv_pc`, `width_m`, `slope_pc`, `n_imperv`, `n_perv`, `gauge`, polygon |
| load sets | name → load per node (m³/d), e.g. "2056", "2031" |
| settings | friction (Colebrook-White ks or Manning n), peaking (table, Peltier, Merrimack, constant, none), infiltration per km, design constraints (velocity min/max, cover min/max, d/D by size, minimum slope by size, crowns matched), catalogue, design and check load sets, self-cleansing rule |
| rain | gauges and time series (SWMM) or a design storm from an IDF table |
| swmm passthrough | raw `.inp` sections the model does not edit, so an imported model writes back unchanged |

**Flows:** the W18 rule on any tree. A pump link (or a transfer conduit) passes the peaked flow at its upstream node
downstream as an unpeaked inflow, which is how W18 and SewerGEMS carry lifts and joins.

**Project file:** a GeoPackage with layers `nodes`, `links`, `catchments`, and a table `project` holding the settings,
load sets, rain, scenarios and passthrough as JSON. The CRS is the project's, or undefined for local metres.

**Scenarios:** base plus a list of edits (set a field, add an element, delete one, move a node), with undo and redo,
copy and compare: the pattern already tested in phase 1B, generalised.

## Stages and gates

| # | Stage | Gate |
|---|---|---|
| G1 | the general model, the GeoPackage file, one coordinate boundary at the API (project CRS or local metres ↔ the map's lon/lat), Ibri as a sample project built from the named W18 outputs; built beside phase 1B, which stays green until the switch | Ibri through the general path: pipe flows within 0.1 % of W18 on every pipe of the 12 cases, station flows equal to W18's transfers within 0.1 %, velocities within 0.003 m/s; save → open → save identical |
| G2 | the editor in the SewerGEMS manner: element toolbar (manhole, outfall, conduit, pump, catchment), draw, move, delete, split, connect, one table per element type with bulk edit, undo/redo, new blank project (CRS or local) | Playwright draws a network from a blank project, saves it and reopens it |
| G3 | the general sewer engine: loads, peaking choices, infiltration, Colebrook-White or Manning, analysis, automated design under the constraints (pass-by-pass sizing, re-lay with crowns matched and minimum cover), profile | the general re-lay equal to W18's `depth_design` on every node of SC1-2056; one Ibri subnetwork cut out as a standalone project equal to W18; Ibri's sizes from the general design equal W18's |
| G4 | stormwater: catchments, gauges, time series and IDF design storms, SWMM build, run and read-back, hydrographs, dynamic analysis of a sewer | EPA's examples imported, run and exported equal EPA's reference; an edited conduit size is carried into the written `.inp` and moves the result; a drawn storm network runs end to end |
| G5 | import and export: SWMM `.inp`, GeoPackage and SHP with field mapping, CSV, DXF | each format round-trips |
| G6 | the assistant on any project (build, edit, size, explain), always into a new scenario | stand-in tests and one live question |
