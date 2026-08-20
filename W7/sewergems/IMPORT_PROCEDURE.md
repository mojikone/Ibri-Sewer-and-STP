# SewerGEMS import — W4 test boundary package

Two ModelBuilder runs (New model, unit system SI set FIRST via Tools > More > Options;
wizard Step 2 Coordinate Unit = m).

## Run 1 — elements
1. ModelBuilder > New > Shapefiles: select MANHOLES.shp, CONDUITS.shp, OUTFALL.shp (Ctrl-click).
2. Spatial options: check "Establish connectivity using spatial data", tolerance 0.05 m
   (belt and braces — explicit Start/Stop labels are also mapped and take precedence).
3. Table types: MANHOLES -> Manhole; CONDUITS -> Conduit; OUTFALL -> Outfall. Key field = LABEL.
4. Field mappings:
   - MANHOLES: GRD_EL -> Elevation (Ground) [m]; INV_EL -> Elevation (Invert) [m];
     MH_DIA -> Diameter [m] (leave Set Rim to Ground = True).
   - CONDUITS: START_ND -> Start Node; STOP_ND -> Stop Node; DIA_MM -> Diameter [mm!];
     MANNING_N -> Manning's n; INV_UP -> Invert (Start) [m]; INV_DN -> Invert (Stop) [m];
     MATERIAL -> Material. IMPORTANT: after build, global-edit conduits
     "Set Invert to Start Node?" = False and "Set Invert to Stop Node?" = False,
     otherwise the mapped inverts are ignored and DROP MANHOLES ARE LOST.
   - OUTFALL: GRD_EL -> Elevation (Ground); INV_EL -> Elevation (Invert).
     Boundary condition: set Free Outfall in the model (not mapped — enum trap).
5. Build. Check the Messages tab: zero errors expected. 1841 conduits / 1841 manholes / 1 outfall.

## Run 2 — sanitary loads (update-only)
1. Components > Patterns: confirm pattern "Fixed" exists (or define the diurnal pattern first).
2. ModelBuilder > New > Excel: LOADS.xlsx, table type "Manhole, Sanitary Loads",
   Key field MH_LABEL. UNCHECK all spatial/create/delete options (update-only run).
3. Map: LOADTYPE -> Load Definition (Label); BASEFLOW -> Base Flow [L/s!]; PATTERN -> Pattern (Label).
4. Build. A "Fixed pattern" warning per row is ignorable (Bentley KB0014854).
5. NOTE: a loads import REPLACES each listed manhole's whole load collection — always
   re-import the full table, never a partial one.

## Referee comparison (PLAN §3b.4)
Run a steady-state (or EPS peak) analysis, export the conduit FlexTable, paste
Discharge / Velocity / d-D into REFEREE_pipes.csv columns SG_Q_LS / SG_V_MS / SG_DOD.
Any pipe off by more than 5% from OUR_* columns needs investigation before the design
is called verified. Expect small differences from junction losses (we ignore minor
losses at concept stage) and from the GVF engine vs our normal-depth assumption.
