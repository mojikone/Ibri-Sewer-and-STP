"""W18 plot layer 2026-2100 (engineer, 2026-11-16): every plot with its electricity meters by category, land use,
status, properties, residents and average sewage flow for every year of the team's series (2026-2100), on the W18
load basis. The placement is py/nws_loads.py's, repeated for every year; the flows of its ten years are checked
against results/loads/plot_loads.csv to 1e-6 m3/d.

People are RESIDENTS. The settlement's people (team series, capped at its capacity) sit on the existing plots in the
pattern of the W14 residents (POP: dwelling meters x the settlement's occupancy) up to the 2026 figure, and every person
above 2026 sits on the growth plots in equal shares - the same plots and shares that take the growth flow. So on a
growth plot Q = people x 171.03 L/d exactly; on an existing plot the flow also carries the plot's shops, offices and
the estates' workers, which are not residents.

Properties: existing = dwelling meters 2024 (W14 G_DOM); future = the people added on the plot by 2100 / 4.8, the
team's persons per dwelling (sheet 'MOHUP DATA - NA', column G = total properties x 4.8).

Writes gis/W18_plots_2026_2100.shp (+ .zip of it), gis/W18_plots_2026_2100_fields.md, results/loads/plot_layer_check.md
Usage: python plot_layer_2100.py
"""
import os, zipfile
import numpy as np, pandas as pd, openpyxl, pyogrio, shapely

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
TEAM = os.path.join(W18, "..", "..", "temp", "recent updates by the team")
WB = os.path.join(TEAM, "New Calculation MH.xlsx")
PLOTS = r"C:\Users\mojtaba\Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\SHP\Plots\Plots.shp"
W14P = os.path.join(W18, "..", "W14", "shp", "PLOTS_load.shp")
SETTLE_SHP = os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp")
LOADS = os.path.join(W18, "results", "loads")
NAME = "W18_plots_2026_2100"
GIS = os.path.join(W18, "gis")
YEARS = list(range(2026, 2101)); BASE = 2026
OCC = 4.8

wb = openpyxl.load_workbook(WB, data_only=True)
rate = wb["Base Demand"]["H4"].value / 1000.0
av = wb["Average"]
col = {av.cell(1, c).value: c for c in range(2, av.max_column + 1)}
assert all(y in col for y in YEARS), "the team's series does not cover 2026-2100"
pop = {av.cell(r, 1).value.strip().upper(): {y: av.cell(r, col[y]).value for y in YEARS}
       for r in range(2, av.max_row + 1) if av.cell(r, 1).value and av.cell(r, 1).value != "Total"}
md = wb["MOHUP DATA - NA"]
cap = {md.cell(r, 1).value.strip().upper(): md.cell(r, 7).value for r in range(2, md.max_row + 1)
       if md.cell(r, 1).value and md.cell(r, 1).value != "Total"}
team_full = {md.cell(r, 1).value.strip().upper(): md.cell(r, 8).value for r in range(2, md.max_row + 1)
             if md.cell(r, 1).value and md.cell(r, 1).value != "Total"}
g2 = openpyxl.load_workbook(WB, data_only=False)["MOHUP DATA - NA"]["G2"].value
assert str(g2).replace(" ", "") == "=F2*4.8", f"the team's persons per dwelling is no longer 4.8: {g2}"
assert set(pop) == set(cap) and len(pop) == 25

g = pyogrio.read_dataframe(PLOTS, columns=["PLOT_NO", "SETTLE", "STATUS", "CADASTRE", "USE", "AREA_M2", "Q_2024"])
g["S"] = g.SETTLE.str.strip().str.upper()
w14 = pyogrio.read_dataframe(W14P, columns=["AREA_M2", "Classes", "G_DOM", "G_NDOM", "G_GOV", "G_SPEC", "G_AGR", "POP",
                                            "S_SPEC", "SPREAD_W", "HOMESHAPE"], read_geometry=False)
assert len(w14) == len(g) and np.allclose(w14.AREA_M2.values, g.AREA_M2.values, atol=0.01)
sb = pyogrio.read_dataframe(SETTLE_SHP, columns=["SETTLE"]); sb["S"] = sb.SETTLE.str.strip().str.upper()
poly = dict(zip(sb.S, sb.geometry.values))
cent = g.geometry.centroid.values
inside = np.array([bool(shapely.contains(poly[s], c)) for s, c in zip(g.S, cent)])
spec_all = w14.S_SPEC.values
spread = (w14.SPREAD_W.values > 0) & (w14.HOMESHAPE.values == 1)
pl = pd.read_csv(os.path.join(LOADS, "plot_loads.csv"), index_col="FID")
assert len(pl) == len(g) and (pl.SETTLE.values == g.SETTLE.values).all()

Q = {y: np.zeros(len(g)) for y in YEARS}; P = {y: np.zeros(len(g)) for y in YEARS}
growth = np.zeros(len(g), bool); rows = []
for s in sorted(pop):
    m = ((g.S == s).values & inside)
    base_w = (g.Q_2024.values - spec_all) * m
    res_w = w14.POP.values * m
    tgt = m & (g.STATUS == "Future").values & spread
    growth |= tgt
    n_t = int(tgt.sum()); spec = spec_all * m
    p26 = pop[s][BASE]; f_base = p26 * rate
    full = next((y for y in YEARS if pop[s][y] >= cap[s]), None)
    for y in YEARS:
        Py = min(pop[s][y], cap[s]); G = Py * rate - f_base
        assert Py >= p26 - 1e-9, (s, y)
        if n_t:
            Q[y] += base_w / base_w.sum() * f_base + tgt * (G / n_t) + spec
            P[y] += res_w / res_w.sum() * p26 + tgt * ((Py - p26) / n_t)
        else:
            Q[y] += base_w / base_w.sum() * Py * rate + spec
            P[y] += res_w / res_w.sum() * Py
    rows.append(dict(settlement=s, growth_plots=n_t, people_2026=p26, people_2100=min(pop[s][2100], cap[s]),
                     capacity=cap[s], full_year=full or "not by 2100", team_full_year=team_full[s],
                     dwellings_added_per_growth_plot_2100=(min(pop[s][2100], cap[s]) - p26) / n_t / OCC if n_t else np.nan,
                     dwellings_per_growth_plot_when_full=(cap[s] - p26) / n_t / OCC if n_t else np.nan))
st = pd.DataFrame(rows).set_index("settlement")

# --- checks: the ten model years are nws_loads.py's flows; residents and flow sum to the settlements
d_max = max(np.abs(Q[y] - pl[f"Q_{y}"].values).max() for y in range(2026, 2072, 5))
assert d_max < 1e-6, d_max
gs = g.S.values
for y in YEARS:
    want_p = {s: min(pop[s][y], cap[s]) for s in pop}
    got_p = pd.Series(P[y]).groupby(gs).sum()
    assert max(abs(got_p[s] - want_p[s]) for s in pop) < 1e-6, y
    got_q = pd.Series(Q[y]).groupby(gs).sum()
    spec_s = pd.Series(spec_all * inside).groupby(gs).sum()
    assert max(abs(got_q[s] - want_p[s] * rate - spec_s[s]) for s in pop) < 1e-6, y
fut_only = growth & (g.Q_2024.values == 0) & (spec_all == 0)
assert np.allclose(Q[2100][fut_only], P[2100][fut_only] * rate, atol=1e-9)

# --- the layer
why = pl.WHY_OUT.fillna("").values
out = g[["PLOT_NO", "CADASTRE", "SETTLE", "AREA_M2", "STATUS", "USE"]].rename(columns={"USE": "LANDUSE"}).copy()
out["MOH_USE"] = w14.Classes.values
for f, c in (("M_DOM", "G_DOM"), ("M_COM", "G_NDOM"), ("M_GOV", "G_GOV"), ("M_SPEC", "G_SPEC"), ("M_AGR", "G_AGR")):
    out[f] = w14[c].values.astype(int)
out["PROP_EX"] = w14.G_DOM.values.astype(int)
out["PROP_FUT"] = np.round(np.where(growth, (P[2100] - P[BASE]) / OCC, 0.0), 2)
out["PROPS"] = np.round(out.PROP_EX + out.PROP_FUT, 2)
out["IN_BOUND"] = inside.astype(int)
out["GROWTH"] = growth.astype(int)
out["NETWORK"] = np.where(why == "", "connected", why)
out["MH_W18"] = pl.MH_W18.values.astype(int)
# five decimals: every growth plot of a settlement carries the same share, so its rounding error repeats 10,000 times
# instead of cancelling (2 decimals put the file 100 people off the total, 4 decimals 1.3; W14 stored four for the same reason)
yr = pd.DataFrame({**{f"POP_{y}": np.round(P[y], 5) for y in YEARS}, **{f"Q_{y}": np.round(Q[y], 5) for y in YEARS}}, index=out.index)
out = pd.concat([out, yr], axis=1).set_geometry(g.geometry.values, crs=g.crs)

schema = {"geometry": "Polygon", "properties": {
    "PLOT_NO": "int:10", "CADASTRE": "str:40", "SETTLE": "str:20", "AREA_M2": "float:12.2", "STATUS": "str:8",
    "LANDUSE": "str:24", "MOH_USE": "str:24", "M_DOM": "int:5", "M_COM": "int:5", "M_GOV": "int:5", "M_SPEC": "int:5",
    "M_AGR": "int:5", "PROP_EX": "int:5", "PROP_FUT": "float:8.2", "PROPS": "float:8.2", "IN_BOUND": "int:1",
    "GROWTH": "int:1", "NETWORK": "str:24", "MH_W18": "int:10",
    **{f"POP_{y}": "float:11.5" for y in YEARS}, **{f"Q_{y}": "float:11.5" for y in YEARS}}}
assert out.CADASTRE.fillna("").str.len().max() <= 40 and out.NETWORK.str.len().max() <= 24
os.makedirs(GIS, exist_ok=True)
shp = os.path.join(GIS, NAME + ".shp")
out.to_file(shp, engine="fiona", schema=schema, encoding="utf-8")
with zipfile.ZipFile(os.path.join(GIS, NAME + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
        z.write(os.path.join(GIS, NAME + ext), NAME + ext)

# --- read it back: the rounded values still sum to the settlements
back = pyogrio.read_dataframe(shp, read_geometry=False)
assert len(back) == len(g) and list(back.columns) == list(schema["properties"])
rb = max(abs(back[f"POP_{y}"].sum() - sum(min(pop[s][y], cap[s]) for s in pop)) for y in YEARS)
qb = max(abs(back[f"Q_{y}"].sum() - Q[y].sum()) for y in YEARS)
assert rb < 0.5 and qb < 0.5, (rb, qb)

ex_out = (~inside) & (w14.G_DOM.values > 0)
L = [f"# W18 plot layer 2026-2100, check", "",
     f"{len(g):,} plots, {len(schema['properties'])} fields; residents and flow for {len(YEARS)} years ({YEARS[0]}-{YEARS[-1]}).",
     f"Flows of the model years 2026-2071 against results/loads/plot_loads.csv: largest difference {d_max:.2e} m3/d.",
     f"Residents and flow sum to the settlements every year (to 1e-6); after rounding in the file (5 decimals), residents within {rb:.2f} people and flow within {qb:.3f} m3/d of the totals.",
     f"Growth plots: {int(growth.sum()):,}. Existing plots outside their settlement boundary with dwelling meters (no people, no flow): "
     f"{int(ex_out.sum()):,} plots, {int(w14.G_DOM.values[ex_out].sum()):,} dwellings.", "",
     "| year | residents | flow m3/d | carried by the network m3/d |", "|---|---|---|---|"]
car = out.NETWORK.values == "connected"
for y in (2026, 2031, 2041, 2051, 2056, 2061, 2066, 2071, 2081, 2091, 2100):
    L.append(f"| {y} | {P[y].sum():,.0f} | {Q[y].sum():,.1f} | {Q[y][car].sum():,.1f} |")
L += ["", "| settlement | growth plots | people 2026 | people 2100 | capacity | full (ours) | full (team sheet) | dwellings added per growth plot by 2100 | per growth plot when full |",
      "|---|---|---|---|---|---|---|---|---|"]
for s, r in st.iterrows():
    L.append(f"| {s} | {r.growth_plots:,} | {r.people_2026:,.0f} | {r.people_2100:,.0f} | {r.capacity:,.0f} | {r.full_year} | {r.team_full_year} | "
             f"{r.dwellings_added_per_growth_plot_2100:.2f} | {r.dwellings_per_growth_plot_when_full:.2f} |")
open(os.path.join(LOADS, "plot_layer_check.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
st.to_csv(os.path.join(LOADS, "plot_layer_settlements.csv"), float_format="%.4f")

F = [f"# {NAME} - field dictionary", "",
     "Plots of the model (the W14 plot set, 77,265, row for row with the model's plot layer), EPSG:32640.",
     "Load basis: the team's settlement population (mean of NCSI, meters x 4.8 and APSR), each settlement capped at the",
     "capacity of its empty plots; 171.03 L/person/day; no infiltration (the model adds 720 L/day/km). The 2026 flow sits",
     "on the existing plots in their 2024 pattern (homes, shops and government on their own plots); everything above 2026",
     "is shared equally by the growth plots. The two industrial estates (316.4 m3/d) are added on their plots every year.", "",
     "| field | meaning | unit |", "|---|---|---|",
     "| PLOT_NO | plot number of the model's plot layer | |",
     "| CADASTRE | MoH cadastre number | |",
     "| SETTLE | settlement the plot belongs to | |",
     "| AREA_M2 | plot area | m2 |",
     "| STATUS | Existing (built or metered in 2024) or Future (empty) | |",
     "| LANDUSE | plot use: Residential, Residential-Commercial, Commercial, Government, Industrial, Agricultural, Heritage, Empty (unmetered) - from the meters on the plot, farms by meter or satellite grove test | |",
     "| MOH_USE | MoH planned use of the plot | |",
     "| M_DOM | dwelling meters (primary, subsidised and additional tariffs) | meters |",
     "| M_COM | commercial meters (shops, offices; large users identified as commercial) | meters |",
     "| M_GOV | government meters (including large users identified as government) | meters |",
     "| M_SPEC | special meters (the two industrial estates) | meters |",
     "| M_AGR | farm meters (no sewage load) | meters |",
     "| PROP_EX | existing dwellings, 2024 (= M_DOM) | properties |",
     "| PROP_FUT | dwellings added on the plot by 2100: people added / 4.8 | properties |",
     "| PROPS | PROP_EX + PROP_FUT | properties |",
     "| IN_BOUND | 1 = centroid inside its own settlement's boundary; 0 = outside, takes no people and no flow | |",
     "| GROWTH | 1 = growth plot: empty, home-shaped (200-1,000 m2, compact, not a strip), not grove, industrial, heritage or estate, inside its boundary | |",
     "| NETWORK | connected; inactive manhole (planted areas, outlying catchments); over 200 m from a sewer - the last two are not carried by the network | |",
     "| MH_W18 | manhole the plot loads in the model | |",
     "| POP_yyyy | residents on the plot, every year 2026-2100 | people |",
     "| Q_yyyy | average dry-weather sewage, every year 2026-2100 (unpeaked, no infiltration) | m3/d |", "",
     "Residents and flow differ on purpose: on a growth plot Q = POP x 171.03 L/d; on an existing plot Q also carries the",
     "plot's shops, offices and estate workers, who are not residents, so a shop has flow and no residents.",
     f"A settlement stops growing the year its people reach its capacity; Ibri is full in {st.loc['IBRI', 'full_year']}."]
open(os.path.join(GIS, NAME + "_fields.md"), "w", encoding="utf-8").write("\n".join(F) + "\n")
print("\n".join(L))
for ext in (".dbf", ".shp", ".zip"):
    print(ext, f"{os.path.getsize(os.path.join(GIS, NAME + ext))/1e6:.1f} MB")
