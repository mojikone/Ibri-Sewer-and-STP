"""W18 settlement layer 2026-2100 (engineer, 2026-11-17): the 25 settlement boundaries (W14 Settlements_merged, its
geometry only; the W14 attributes are superseded) with the W18 numbers, summed from the plot layer
gis/W18_plots_2026_2100.shp and the team's sheet 'MOHUP DATA - NA'.
Plot counts are over the plots INSIDE the settlement boundary (those outside take no flow; counted in N_OUTSIDE).
Asked for: population and average flow every year, occupancy, properties per growth plot at saturation and in 2100,
area, plot counts, existing plots by land use and by Nama meter category, empty plots and their share.
Added: growth plots, empty share by area, capacity and full years (ours and the team's), the team's properties per
plot, properties 2026 and 2100, flow not carried by the network in 2031 / 2056 / 2071.
Writes gis/W18_settlements_2026_2100.shp and gis/W18_settlements_2026_2100_fields.md.
Usage: python settlements_2100.py"""
import os
import numpy as np, pandas as pd, pyogrio, openpyxl, fiona
from fiona.crs import CRS

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
PLOTS = os.path.join(W18, "gis", "W18_plots_2026_2100.shp")
SB = os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp")
W14P = os.path.join(W18, "..", "W14", "shp", "PLOTS_load.shp")
WB = os.path.join(W18, "..", "..", "temp", "recent updates by the team", "New Calculation MH.xlsx")
SETS = os.path.join(W18, "results", "loads", "plot_layer_settlements.csv")
OUT = os.path.join(W18, "gis", "W18_settlements_2026_2100.shp")
YEARS = list(range(2026, 2101)); OCC = 4.8

sb = pyogrio.read_dataframe(SB, columns=["SETTLE"]); sb["S"] = sb.SETTLE.str.strip().str.upper()
cols = ["SETTLE", "STATUS", "AREA_M2", "LANDUSE", "M_DOM", "M_COM", "M_GOV", "M_SPEC", "M_AGR", "PROP_EX", "PROPS",
        "IN_BOUND", "GROWTH", "NETWORK"] + [f"POP_{y}" for y in YEARS] + [f"Q_{y}" for y in YEARS]
p = pyogrio.read_dataframe(PLOTS, columns=cols, read_geometry=False); p["S"] = p.SETTLE.str.strip().str.upper()
w14 = pyogrio.read_dataframe(W14P, columns=["SETTLE", "OR_S"], read_geometry=False)
orr = w14.groupby(w14.SETTLE.str.strip().str.upper()).OR_S.first()
st = pd.read_csv(SETS).set_index("settlement")
md = openpyxl.load_workbook(WB, data_only=True)["MOHUP DATA - NA"]
team = {md.cell(r, 1).value.strip().upper(): dict(C=md.cell(r, 3).value, D=md.cell(r, 4).value)
        for r in range(2, md.max_row + 1) if md.cell(r, 1).value and md.cell(r, 1).value != "Total"}
assert set(sb.S) == set(st.index) == set(team), "settlement names differ between the layer, the loads and the team's sheet"

LU = [("Residential", "EX_RES"), ("Residential-Commercial", "EX_RESCOM"), ("Commercial", "EX_COM"),
      ("Government", "EX_GOV"), ("Industrial", "EX_IND"), ("Agricultural", "EX_AGR")]
NA = [("M_DOM", "NA_DOM"), ("M_COM", "NA_COM"), ("M_GOV", "NA_GOV"), ("M_SPEC", "NA_SPEC"), ("M_AGR", "NA_AGR")]
rows = []
for _, r in sb.iterrows():
    s = r.S; a = p[p.S == s]; d = a[a.IN_BOUND == 1]; ex = d[d.STATUS == "Existing"]; em = d[d.STATUS == "Future"]
    full = st.loc[s, "full_year"]
    row = dict(SETTLE=r.SETTLE.strip(), AREA_KM2=round(r.geometry.area / 1e6, 3),
               OR=round(float(orr[s]), 3), OR_2026=round(a.POP_2026.sum() / max(a.PROP_EX.sum(), 1), 3),
               PPP_SAT=round(st.loc[s, "properties_per_growth_plot_when_full"], 3),
               PPP_2100=round(st.loc[s, "properties_added_per_growth_plot_2100"], 3),
               PPP_TEAM=round(team[s]["D"], 3),
               CAPACITY=round(st.loc[s, "capacity"], 1), CAP_TEAM=round(st.loc[s, "capacity_team"], 1),
               FULL_YEAR=0 if str(full).startswith("not") else int(full),
               FULL_TEAM=str(st.loc[s, "team_full_year"]),
               N_PLOTS=len(d), N_EXIST=len(ex), N_EMPTY=len(em),
               EMPTY_PCT=round(100 * len(em) / max(len(d), 1), 1),
               EMPTY_APCT=round(100 * em.AREA_M2.sum() / max(d.AREA_M2.sum(), 1), 1),
               N_GROWTH=int(d.GROWTH.sum()), N_OUTSIDE=int((a.IN_BOUND == 0).sum()), TEAM_PLOTS=int(team[s]["C"]),
               PROP_2026=int(a.PROP_EX.sum()), PROP_2100=round(a.PROPS.sum(), 1))
    for v, f in LU: row[f] = int((ex.LANDUSE == v).sum())
    for m, f in NA: row[f] = int((ex[m] > 0).sum())
    nc = a.NETWORK != "connected"
    for y in (2031, 2056, 2071): row[f"QNC_{y}"] = round(a.loc[nc, f"Q_{y}"].sum(), 2)
    for y in YEARS: row[f"P_{y}"] = round(a[f"POP_{y}"].sum(), 1)
    for y in YEARS: row[f"Q_{y}"] = round(a[f"Q_{y}"].sum(), 2)
    rows.append(row)
t = pd.DataFrame(rows)

# checks: the settlements add up to the plot layer, and no settlement passes its capacity
for y in YEARS:
    assert abs(t[f"P_{y}"].sum() - p[f"POP_{y}"].sum()) < 2, y
    assert abs(t[f"Q_{y}"].sum() - p[f"Q_{y}"].sum()) < 0.5, y
assert (t[[f"P_{y}" for y in YEARS]].max(axis=1) <= t.CAPACITY + 0.5).all()
assert (t.N_EXIST + t.N_EMPTY == t.N_PLOTS).all()
assert t.N_PLOTS.sum() + t.N_OUTSIDE.sum() == len(p)

schema = {"geometry": "MultiPolygon", "properties": {}}
for c in t.columns:
    if c in ("SETTLE", "FULL_TEAM"): schema["properties"][c] = "str:24"
    elif t[c].dtype.kind in "iu": schema["properties"][c] = "int:8"
    elif c.startswith("P_") or c in ("CAPACITY", "CAP_TEAM", "PROP_2100"): schema["properties"][c] = "float:11.1"
    else: schema["properties"][c] = "float:11.3"
from shapely.geometry import MultiPolygon, mapping
geoms = [g if g.geom_type == "MultiPolygon" else MultiPolygon([g]) for g in sb.geometry.values]
with fiona.open(OUT, "w", driver="ESRI Shapefile", schema=schema, crs=CRS.from_epsg(32640), encoding="utf-8") as f:
    for g, (_, r) in zip(geoms, t.iterrows()):
        f.write({"geometry": mapping(g), "properties": {c: (r[c].item() if hasattr(r[c], "item") else r[c]) for c in t.columns}})

D = [("SETTLE", "settlement name", ""),
     ("AREA_KM2", "area of the settlement boundary", "km²"),
     ("OR", "occupancy measured in 2024 (W14, persons per domestic meter; floor 4.0, cap 6.12)", "persons/property"),
     ("OR_2026", "the team's 2026 population / existing properties (domestic meters)", "persons/property"),
     ("PPP_SAT", "properties added per growth plot when the settlement is full (saturation)", "properties/plot"),
     ("PPP_2100", "properties added per growth plot by 2100 (= PPP_SAT where full by 2100)", "properties/plot"),
     ("PPP_TEAM", "the team's residential properties per future plot (MOHUP DATA - NA, column D)", "properties/plot"),
     ("CAPACITY", "population capacity: 2026 population + growth plots x the team's properties per plot x 4.8 (the population stops here)", "people"),
     ("CAP_TEAM", "the team's capacity (sheet column G: (existing + future residential properties) x 4.8), for comparison", "people"),
     ("FULL_YEAR", "year the settlement is full on the team's series (0 = not by 2100)", "year"),
     ("FULL_TEAM", "the team's saturation year (column H)", ""),
     ("N_PLOTS", "plots inside the settlement boundary", "plots"),
     ("N_EXIST", "existing plots inside the boundary", "plots"),
     ("N_EMPTY", "empty (future) plots inside the boundary", "plots"),
     ("EMPTY_PCT", "empty plots / all plots, by count", "%"),
     ("EMPTY_APCT", "empty plots / all plots, by area", "%"),
     ("N_GROWTH", "growth plots: take the growth flow (future, 200-3,000 m², not odd-shaped, not agricultural, heritage or industrial)", "plots"),
     ("N_OUTSIDE", "plots of the settlement outside its boundary (no flow)", "plots"),
     ("TEAM_PLOTS", "the team's future residential plots (column C)", "plots"),
     ("PROP_2026", "existing properties (domestic meters 2024)", "properties"),
     ("PROP_2100", "properties in 2100: existing + added on growth plots", "properties"),
     ("EX_RES ... EX_AGR", "existing plots by land use: residential, residential-commercial, commercial, government, industrial, agricultural", "plots"),
     ("NA_DOM ... NA_AGR", "existing plots with at least one Nama meter of the category: domestic, commercial, government, special, agricultural (a plot can count in more than one)", "plots"),
     ("QNC_2031, _2056, _2071", "flow not carried by the network (inactive manhole or over 200 m from a sewer)", "m³/d"),
     ("P_2026 ... P_2100", "population (team's series, capped at the capacity)", "people"),
     ("Q_2026 ... Q_2100", "average sewage flow, all plots of the settlement (estates included, infiltration not)", "m³/d")]
md_ = ["# W18_settlements_2026_2100 - fields", "", f"{len(t)} settlements, {len(t.columns)} fields, EPSG:32640. Built by `py/settlements_2100.py`.", "",
       "| Field | Meaning | Unit |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in D]
open(OUT.replace(".shp", "_fields.md"), "w", encoding="utf-8").write("\n".join(md_) + "\n")
print(OUT, len(t), "settlements,", len(t.columns), "fields")
print(t[["SETTLE", "AREA_KM2", "N_PLOTS", "N_EXIST", "N_EMPTY", "EMPTY_PCT", "N_GROWTH", "OR", "PPP_SAT", "FULL_YEAR", "P_2056", "Q_2056"]].to_string(index=False))
