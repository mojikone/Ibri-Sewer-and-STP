# SewerGEMS ModelBuilder shapefile schema — research findings (raw data for synthesis)

Confidence legend: [Certain] = read verbatim from Bentley doc/KB; [Likely] = strong inference from Bentley sources; [Guessing] = flagged explicitly. Field widths/names in the schema tables are my recommendations (shapefile-legal, <=10 chars); the "Maps to" property names are verbatim Bentley property names.

---

## 1. Layer split (recommended)

[Certain — from Bentley's main ModelBuilder TechNote, which builds from one shapefile per element type]
- **Manhole point shapefile** — table type `Manhole` (physical data).
- **Conduit polyline shapefile** — table type `Conduit` (single-part polylines).
- **Outfall point shapefile** — table type `Outfall`.
- **Sanitary load table** — a separate NON-spatial table (Excel/CSV-as-XLSX/DBase) keyed on manhole Label, imported in a **second ModelBuilder run** with table type **`Manhole, Sanitary Loads`** (a "collection" table). [Certain for Excel; see §4]. Wet-weather inflows use table type **`Manhole, Inflow (Wet) Collection`**. [Certain]
- ModelBuilder can take several shapefiles in one connection (Ctrl-click multi-select); each layer is mapped to its own table type in the Field Mapping step. [Certain]
- LoadBuilder (not ModelBuilder) is the tool for **spatial** load allocation from polygon/point layers (parcels, billing meters); Bentley's KB explicitly says: loading contained "within shapefiles" spatially → LoadBuilder; loading in a label-keyed table → ModelBuilder. [Certain]

## 2. Schema tables

### 2a. Manholes — `MANHOLES.shp` (Point)

| Field | Type (DBF) | Width | Unit | Maps to (SewerGEMS property) | Notes |
|---|---|---|---|---|---|
| LABEL | C | 16 | — | Label — used as **Key/Label field** | Must be unique; duplicates silently collapse (only first creates, rest update) [Certain] |
| GRD_EL | N | 10.3 | m | `Elevation (Ground)` | [Certain property name] |
| RIM_EL | N | 10.3 | m | `Elevation (Rim)` | Optional — omit and leave `Set Rim to Ground Elevation?` = True (default) [Certain] |
| INV_EL | N | 10.3 | m | `Elevation (Invert)` | Structure bottom. If supplied here, conduit inverts can be auto-derived (see §2b) [Certain] |
| MH_DIA | N | 6.2 | m | `Diameter` | Only if `Structure Shape Type` = Circular Structure [Certain]; optional at concept stage |
| X / Y | — | — | — | not needed | Geometry supplies coordinates for shapefiles; X/Y fields only required for Excel sources [Certain] |

### 2b. Conduits — `CONDUITS.shp` (PolylineZ not needed; plain Polyline)

| Field | Type | Width | Unit | Maps to | Notes |
|---|---|---|---|---|---|
| LABEL | C | 16 | — | Label — **Key field** | Unique |
| START_ND | C | 16 | — | `Start Node` | Manhole/outfall LABEL. Optional if spatial connectivity used, but explicit is preferred (see §3) |
| STOP_ND | C | 16 | — | `Stop Node` | idem |
| DIA_MM | N | 6.0 | mm | `Diameter` | Numeric field for **user-defined** conduits; in mapping, set the field's unit to mm — ModelBuilder converts per-field units [Certain]. Catalog conduits instead need a text GUID mapped to `Size` (see pitfalls) [Certain] |
| MATERIAL | C | 16 | — | `Material` | Text label only; it does NOT auto-populate Manning's n — map n separately [Likely, inferred from property list where Material and Manning's n are independent] |
| MANNING_N | N | 6.4 | — | `Manning's n` | Roughness used by the GVF solvers; `Roughness Type` = single Manning's n [Certain property exists] |
| INV_UP | N | 10.3 | m | `Invert (Start)` / `Elevation (Start Invert)` | See invert logic below |
| INV_DN | N | 10.3 | m | `Invert (Stop)` / `Elevation (Stop Invert)` | idem |
| LEN_M | N | 10.2 | m | `Length (User Defined)` | Optional; if omitted, scaled (geometric) length from geometry is used [Certain that mapping user-defined length is optional] |

**Invert logic** [Certain, Bentley KB]: `Invert (Start)`/`Invert (Stop)` are read-only while `Set Invert to Start Node?` / `Set Invert to Stop Node?` = True (the default) — conduit inverts then inherit the connected node inverts. Two clean strategies:
- **Strategy A (node-driven, simplest):** put inverts only in the manhole layer (`INV_EL`); don't map conduit inverts at all. Conduit ends take manhole inverts automatically. No drop across a manhole possible.
- **Strategy B (conduit-driven, needed for drop manholes / per-pipe inverts):** put INV_UP/INV_DN on conduits AND also map two boolean fields (or global-edit after import) to set `Set Invert to Start Node?` = False and `Set Invert to Stop Node?` = False, otherwise the mapped invert values are ignored (read-only). [Certain that the booleans must be False for conduit inverts to be writable]
- Bentley KB0016772 documents a full workaround sequence when ONLY conduits carry elevations (FlexTable export → re-import keyed on Start Node to push values to manholes/outfalls).

### 2c. Outfall — `OUTFALL.shp` (Point)

| Field | Type | Width | Unit | Maps to | Notes |
|---|---|---|---|---|---|
| LABEL | C | 16 | — | Label — Key field | |
| GRD_EL | N | 10.3 | m | `Elevation (Ground)` | [Certain — KB0016772 maps to outfall `Elevation (Ground)`] |
| INV_EL | N | 10.3 | m | `Elevation (Invert)` | [Likely — outfall carries an invert like other nodes; not read verbatim in fetched docs] |
| BC_TYPE | C | 24 | — | `Boundary Condition Type` | Enumerated: `Free Outfall`, `Normal`, `Elevation (User Defined Tailwater)`, `Time-Elevation Curve`, `Elevation-Flow Curve`, `Tidal`, `Boundary Element` [Certain list]. Enumerations must match model strings **exactly, case-sensitive** [Certain] — safer to leave unmapped and set in the model (1 outfall). |
| TW_EL | N | 10.3 | m | `Elevation (User Defined Tailwater)` | Only if BC_TYPE demands it |

### 2d. Sanitary loads — `LOADS` table (DBF/XLSX; one row per load, composite rows allowed)

Table type **`Manhole, Sanitary Loads`**; Key/Label field = manhole label. [Certain — KB0014854, quoted structure]

| Field | Type | Width | Unit | Maps to | Notes |
|---|---|---|---|---|---|
| MH_LABEL | C | 16 | — | Key/Label field | Must exactly match model manhole labels or NEW elements get created [Certain] |
| LOADTYPE | C | 24 | — | `Load Definition (Label)` | Must be exactly (spelling+capitalization): `Sanitary Unit Load`, `Sanitary Pattern Load`, or `Sanitary Hydrograph` [Certain verbatim]. Without it, loads import as default Sanitary Hydrograph and base flow/count are ignored [Certain] |
| BASEFLOW | N | 10.4 | L/s (unit chosen in mapping) | `Base Flow` | For pattern-based loads; "Make sure you check your units!" [Certain verbatim] |
| PATTERN | C | 16 | — | `Pattern (Label)` | Pattern must pre-exist under Components > Patterns; ModelBuilder will NOT create it [Certain]. `Fixed` pattern works but throws an ignorable warning [Certain] |
| UNITLOAD | C | 24 | — | `Unit Sanitary Load (Label)` | Unit load definition must pre-exist under Components > Unit Sanitary Loads [Certain] |
| UNITCOUNT | N | 10.2 | count | `Loading Unit Count` | For unit-based loads [Certain] |

Other mappable fields that exist but are normally skipped: `Load Definition (ID)`, `Pattern (ID)`, `Unit Sanitary Load (ID)`, `Index` (hydrograph). [Certain]

Manhole **Inflow** (wet) collection load-type strings: `Pattern`, `Fixed Load`, `Hydrograph Load`. A `Fixed Load` inflow needs only flow + load-type columns — Bentley suggests it over "Fixed"-pattern sanitary loads for steady-state runs with many fixed loads. [Certain]

**Import semantics (critical):** a ModelBuilder load import **replaces the whole sanitary-load collection** of every manhole present in the table — it cannot update one load among several; all loads for a manhole must be in the same run (multiple rows per manhole = composite loads OK). Loads land in the Sanitary Loading alternative of the scenario active when ModelBuilder opens. [Certain]

**Practical best route for plot-aggregated loads per manhole (Ibri case):** aggregate plots → flow per manhole in GIS, write a per-manhole table with LOADTYPE=`Sanitary Pattern Load`, BASEFLOW in L/s, PATTERN=`Fixed` (or a diurnal pattern defined first), run as an update-only ModelBuilder connection (all spatial/create/delete options unchecked). [Certain procedure for Excel; [Likely] a DBF/shapefile attribute table works identically since DBase is a listed source type — not verified verbatim.] Alternative: unit-load route (UNITLOAD=e.g. `Residential`, UNITCOUNT=plot or capita count) keeps per-capita rates editable inside SewerGEMS.

## 3. Connectivity

[Certain — Bentley docs "Specifying Network Connectivity in ModelBuilder"]
- Two methods: **explicit** (map `Start Node`/`Stop Node` fields on the conduit table) and **implicit** ("Establish connectivity using spatial data" + Tolerance, optional "Create nodes if none found at pipe endpoint").
- Bentley's decision rule, verbatim structure: complete start/stop data → explicit (**preferred**); partial → both; none but good geometry → implicit; no nodes at all → implicit + create-nodes.
- "If pipes do not have explicit Start/Stop nodes and 'Establish connectivity using spatial data' is not checked, the pipes will not be connected to the nodes and a valid model will not be produced." [Certain verbatim]
- Tolerance: unit = the Coordinate Unit chosen in Step 2; guidance is "set as low as possible" to avoid wrong connections; no documented default value found for the connectivity tolerance ([Guessing] on any specific number — the only default I saw documented is 100 units for the separate *spatial-join key-matching* feature, which is a different thing).
- Implicit method: polyline **first vertex = Start node, last vertex = Stop node** — start/stop assignment follows digitized direction. [Certain per Bentley forum/KB summary]
- Nodes auto-created at unmatched pipe ends come in as the default node type; end-node type corrections are manual afterwards. [Certain]
- Also general TechNote guidance: check BOTH connectivity boxes as good practice; a pipe end with no node in tolerance and create-nodes off → **pipe not imported at all**. [Certain verbatim]

**What the GIS export should guarantee** (synthesis of the above, all grounded):
- Exact vertex coincidence of conduit endpoints and node points (snap in GIS; Bentley: "turn on all of your snapping options... so there aren't connectivity gaps") [Certain verbatim advice].
- Single-part polylines, one pipe per manhole-to-manhole reach; every pipe end lands on a node.
- Digitize upstream→downstream so Start = upstream (matters for invert inheritance, design, profile conventions; solvers tolerate reversed flow but the schema shouldn't rely on it) [Likely — direction→start/stop is Certain; "solvers tolerate reversal" is my inference, and there is a documented "reverse start/stop" tool implying it matters].
- Belt-and-braces: provide BOTH explicit START_ND/STOP_ND fields AND clean snapped geometry; enable spatial connectivity with a small tolerance as backup. Explicit fields make the import independent of tolerance tuning. [Certain that explicit is Bentley-preferred]

## 4. Units, CRS, import procedure

- **Before importing anything**: set the model's unit system (SI) via Tools > More > Options — Bentley warns this avoids "spatial disconnection". [Certain verbatim]
- Step 2 of the wizard: choose **Coordinate Unit = m** for metric data. [Certain]
- Per-field units are set in the Field Mapping step (e.g., DIA_MM mapped to Diameter with unit mm; BASEFLOW with unit L/s). [Certain]
- **CRS:** ModelBuilder ≤ v2024 is CRS-blind — it reads raw coordinates and requires a **projected** CRS (linear units); geographic (lat/lon) shapefiles import as a point pile. Version **2026 (26.00.00.xxx)+** recognizes external CRSs and reprojects to the model's declared CS. For EPSG:32640 (projected, metres) either way is fine — just keep ALL layers in the same projected CRS. [Certain]
- Key field choice: `Label` (or GIS-ID for long-term GIS sync). ModelBuilder's auto `<label>` field exists as fallback but blocks sync-out. [Certain]
- Wizard order: Data source → layer/worksheet selection (+optional WHERE clause) → Spatial/connectivity options → Create/Remove/Update options → Additional options (target scenario, key field) → Field mappings per table → (Snapshots) → Build. [Certain]
- For the loads run specifically: **uncheck all spatial/create/delete options** (update-only). [Certain verbatim]

## 5. Pitfalls (all sourced)

| Pitfall | Effect | Source-grounded fix |
|---|---|---|
| Duplicate values in Key field | "An item with the same key has already been added" error, or only first element created and the rest merely re-update it | Make labels unique before export [Certain] |
| Zero-length pipes in source | Import errors / model won't compute | Clean in GIS first; check via source-file audit [Certain] |
| Corrupt/odd shapefile geometry | "Unable to open table" | ArcGIS Repair Geometry or re-export a fresh copy [Certain] |
| Enumerated fields (Structure Type, Section Type, Boundary Condition Type, load-type strings) | Value silently rejected: "enumeration value ... is not valid" | Strings must match model options exactly, case-sensitive. Bentley's discovery trick (KB0071914): build 3 dummy elements, Sync Out to Excel, read the exact strings/data types [Certain] |
| Mapping conduit inverts while `Set Invert to Start/Stop Node?` = True | Mapped inverts ignored (fields read-only) | Map/global-edit the booleans to False, or use manhole-driven inverts [Certain] |
| Catalog conduits | Mapping a text size to `Diameter` fails; catalog sizes are assigned by GUID mapped to `Size` (text), obtained via Sync Out | Use numeric `Diameter` (user-defined conduits) at concept stage [Certain] |
| Elevation vs depth | SewerGEMS manhole/conduit import wants **elevations** (Ground/Rim/Invert); no depth-based import fields appeared in any property list I retrieved | Convert depths to elevations in GIS [Likely — absence of depth fields is negative evidence, not a verbatim statement] |
| mm vs m diameter | Wrong by 1000x if field unit left at model default | Explicitly set the unit dropdown per mapped field [Certain mechanism] |
| Loads import replaces whole load collection per manhole | Partial updates impossible | Regenerate the full loads table every time [Certain] |
| Patterns / unit-load definitions not pre-defined | Loads fall back to Sanitary Hydrograph type, base flow ignored | Define Components > Patterns and > Unit Sanitary Loads before the loads run [Certain] |
| Shapefile DBF 10-char field-name truncation producing duplicate names | Can trigger the "same key" open-table error | Keep names ≤10 chars and unique by construction (as in schema above) [Likely — duplicate-name link to this error is my inference; duplicate *labels* cause is Certain] |
| Node in model but removed pipe (or vice versa) after re-runs | Orphans remain — ModelBuilder "Remove" option only deletes per-table matches | Review summary Messages tab; manual cleanup expected [Certain] |

## 6. Uncertain / not established

- Exact default value of the **connectivity tolerance** field — not found in fetched docs (only "as low as possible"; spatial-join default 100 units is a different feature).
- Whether a **shapefile DBF** can be the source for the `Manhole, Sanitary Loads` collection table type (Bentley's worked example uses Excel; DBase is a supported source type generally) — [Likely], verify with a 3-manhole pilot.
- Outfall `Elevation (Invert)` property name — [Likely], not read verbatim.
- Property-name spelling drift between versions: `Invert (Start)` (FlexTable/KB usage) vs `Elevation (Start Invert)` (SS5 help page) refer to the same attribute; current CONNECT/2024+ UI strings may differ slightly.
- No Bentley-published "canonical shapefile schema" exists; the schema above is assembled from the property lists + TechNotes, not copied from a single Bentley table.

## 7. Sources

- Using ModelBuilder to Import External Data [TN] (main, full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0057220
- Importing Sanitary Loading Information Using ModelBuilder (full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0014854
- How to apply conduit start/stop elevations to adjacent nodes (full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0016772
- Using ModelBuilder to add catalog conduits (full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0058552
- Discovering field types/enum values via Sync Out (full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0071914
- Error "Unable to open table / item with the same key" (full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0015158
- Geographic vs projected CRS in ModelBuilder/LoadBuilder (full text captured): https://bentleysystems.service-now.com/community?id=kb_article_view&sysparm_article=KB0014824
- Specifying Network Connectivity in ModelBuilder (docs): https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-A603FA94CF344544BD620DA406698BF5.html
- Step 2 — Specify Spatial Options (docs): https://docs.bentley.com/LiveContent/web/Bentley%20CivilStorm%20SS5-v1/en/40012.html
- Preparing to Use ModelBuilder (docs): https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-657AD64DDC7C4BDC952F46D4A9CF7A28.html
- Conduit-Physical attribute list (docs): https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-726D7C08DDC6412A82B6F284EBC13B0D.html
- Manhole-Physical attribute list (docs): https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-27522ED11541493288027666FF589A78.html
- Outfall-Boundary Condition (docs): https://docs.bentley.com/LiveContent/web/Bentley%20StormCAD%20SS5-v1/en/GUID-17DD1FC21DB84A11BA14FE4182CD1E1F.html
- Methods for Entering Loads, SewerGEMS (docs): https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-A83024F97D8346308F5CD8CCD4D5DD0E.html