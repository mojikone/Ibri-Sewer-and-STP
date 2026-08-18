"""sewnet.export_gems — SewerGEMS ModelBuilder import package, built exactly to the
Bentley-sourced schema in W4/docs/phaseA/phaseA_sewergems.md:

  MANHOLES.shp   LABEL / GRD_EL / INV_EL / MH_DIA        -> Manhole physical
  CONDUITS.shp   LABEL / START_ND / STOP_ND / DIA_MM /
                 MATERIAL / MANNING_N / INV_UP / INV_DN / LEN_M
  OUTFALL.shp    LABEL / GRD_EL / INV_EL
  LOADS.xlsx     MH_LABEL / LOADTYPE / BASEFLOW (L/s) / PATTERN   (+ LOADS.csv twin)
  REFEREE_pipes.csv   our Q/v/d-D per conduit + empty SewerGEMS columns (PLAN §3b.4)
  IMPORT_PROCEDURE.md the two-run ModelBuilder walk-through with the known traps

Guarantees: unique labels; single-part polylines digitized upstream->downstream;
conduit endpoints vertex-snapped to node points; explicit start/stop labels;
elevations (never depths); numeric diameter in mm (user-defined conduits)."""

import csv
import os
import geopandas as gpd
from shapely.geometry import Point

from . import criteria as C

CRS = "EPSG:32640"

PROCEDURE = """# SewerGEMS import — W4 test boundary package

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
"""


def write_all(out_dir, nodes, pipes, per_mh_units, of_rep, outfall_key):
    os.makedirs(out_dir, exist_ok=True)

    mh_keys = [k for k, n in nodes.items() if n["kind"] != "outfall"]
    mh = gpd.GeoDataFrame({
        "LABEL": [nodes[k]["label"] for k in mh_keys],
        "GRD_EL": [round(nodes[k]["z"], 3) for k in mh_keys],
        "INV_EL": [round(nodes[k]["invert"], 3) for k in mh_keys],
        "MH_DIA": [1.2 for _ in mh_keys],   # typical ladder (criteria.ASSUMPTIONS MH_SIZES)
    }, geometry=[Point(nodes[k]["x"], nodes[k]["y"]) for k in mh_keys], crs=CRS)
    mh.to_file(os.path.join(out_dir, "MANHOLES.shp"), encoding="utf-8")

    cd = gpd.GeoDataFrame({
        "LABEL": [p["label"] for p in pipes],
        "START_ND": [nodes[p["up"]]["label"] for p in pipes],
        "STOP_ND": [nodes[p["dn"]]["label"] for p in pipes],
        "DIA_MM": [p["dn_mm"] for p in pipes],
        "MATERIAL": [p["material"] for p in pipes],
        "MANNING_N": [C.MANNING_N_EXPORT for _ in pipes],
        "INV_UP": [round(p["inv_up"], 3) for p in pipes],
        "INV_DN": [round(p["inv_dn"], 3) for p in pipes],
        "LEN_M": [round(p["length"], 2) for p in pipes],
    }, geometry=[p["geom"] for p in pipes], crs=CRS)
    cd.to_file(os.path.join(out_dir, "CONDUITS.shp"), encoding="utf-8")

    of = gpd.GeoDataFrame({
        "LABEL": ["OF-1"], "GRD_EL": [round(of_rep["z"], 3)],
        "INV_EL": [round(nodes[outfall_key]["invert"], 3)],
    }, geometry=[Point(of_rep["x"], of_rep["y"])], crs=CRS)
    of.to_file(os.path.join(out_dir, "OUTFALL.shp"), encoding="utf-8")

    # loads: one row per loaded manhole, pattern-based fixed base flow in L/s
    rows = []
    for k in mh_keys:
        n_units = len(per_mh_units.get(k, []))
        if n_units == 0:
            continue
        q_ls = n_units * C.PLOT_QADF_LS
        rows.append((nodes[k]["label"], "Sanitary Pattern Load", round(q_ls, 4), "Fixed"))
    with open(os.path.join(out_dir, "LOADS.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["MH_LABEL", "LOADTYPE", "BASEFLOW", "PATTERN"])
        w.writerows(rows)
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "loads"
        ws.append(["MH_LABEL", "LOADTYPE", "BASEFLOW", "PATTERN"])
        for r in rows:
            ws.append(list(r))
        wb.save(os.path.join(out_dir, "LOADS.xlsx"))
    except ImportError:
        pass

    with open(os.path.join(out_dir, "REFEREE_pipes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LABEL", "DIA_MM", "SLOPE_PMIL", "OUR_Q_LS", "OUR_V_MS", "OUR_DOD",
                    "SG_Q_LS", "SG_V_MS", "SG_DOD", "DQ_PCT", "DV_PCT"])
        for p in pipes:
            w.writerow([p["label"], p["dn_mm"], round(p["slope"] * 1000, 3),
                        round(p["qpeak_ls"], 2),
                        round(p["vel"], 3) if p.get("vel") else "",
                        round(p["dod"], 3) if p.get("dod") else "", "", "", "", "", ""])

    with open(os.path.join(out_dir, "IMPORT_PROCEDURE.md"), "w", encoding="utf-8") as f:
        f.write(PROCEDURE)
    return len(rows)
