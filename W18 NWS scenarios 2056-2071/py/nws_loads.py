"""W18 plot loads on the NWS basis of November 2026.

Volume: the team's settlement population (mean of the NCSI, meters x 4.8 and APSR series, sheet 'Average'
of 'New Calculation MH.xlsx'), capped at the settlement's capacity (engineer 2026-11-16: each settlement grows only
until its empty plots are full, no overflow; 2026-11-17: capacity = 2026 population + growth plots x the team's
properties per plot (sheet 'MOHUP DATA - NA', column D) x 4.8, in place of the team's column G),
times the per-capita rate of sheet 'Base Demand' H4 (171.03 L/person/day). No infiltration: the model adds
720 L/day/km itself.

Placement (engineer 2026-11-16): the settlement's 2026 flow on its existing plots in the pattern of the plot
layer's 2024 flow (homes, commercial and government plots on their own plots); everything above 2026 shared
equally by the settlement's future residential and residential-commercial plots (the plots the capacity counts).

Plots: the model's plot layer (the W14 plots, row for row), HMINNODE = the manhole each plot loads.
Writes results/loads/: plot_loads.csv, manhole_loads.csv, settlement_flows.csv, check.md
"""
import os, sys
import numpy as np, pandas as pd, openpyxl, pyogrio

HERE = os.path.dirname(os.path.abspath(__file__))
W18 = os.path.dirname(HERE)
TEAM = os.path.join(W18, "..", "..", "temp", "recent updates by the team")
WB = os.path.join(TEAM, "New Calculation MH.xlsx")
SCEN = os.path.join(TEAM, "WW Generation - Network Scenarios.xlsx")
PLOTS = r"C:\Users\mojtaba\Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\SHP\Plots\Plots.shp"
OUT = os.path.join(W18, "results", "loads"); os.makedirs(OUT, exist_ok=True)
YEARS = list(range(2026, 2092, 5))   # 2026-2091 every 5 years (engineer 2026-11-17: model years every 5 from 2031 to 2091)
BASE = 2026
TARGET_USES = ("Residential", "Residential-Commercial")

wb = openpyxl.load_workbook(WB, data_only=True)
rate = wb["Base Demand"]["H4"].value / 1000.0                       # m3 per person per day
av = wb["Average"]
col = {av.cell(1, c).value: c for c in range(2, av.max_column + 1)}
pop = {av.cell(r, 1).value.strip().upper(): {y: av.cell(r, col[y]).value for y in YEARS}
       for r in range(2, av.max_row + 1) if av.cell(r, 1).value and av.cell(r, 1).value != "Total"}
md = wb["MOHUP DATA - NA"]
cap = {md.cell(r, 1).value.strip().upper(): md.cell(r, 7).value for r in range(2, md.max_row + 1)
       if md.cell(r, 1).value and md.cell(r, 1).value != "Total"}
assert set(pop) == set(cap) and len(pop) == 25, (set(pop) ^ set(cap))

p = pyogrio.read_dataframe(PLOTS, columns=["SETTLE", "STATUS", "CADASTRE", "USE", "Q_2024", "HMINNODE"], read_geometry=False)
p["S"] = p.SETTLE.str.strip().str.upper()
assert set(p.S) == set(pop), set(p.S) ^ set(pop)

# A plot takes flow only inside its own settlement's boundary (engineer, 2026-11-16: the redrawn settlement boundaries
# lie inside the project boundary and a settlement's flow cannot leave them). Centroid in the plot's own polygon.
import shapely
SETTLE_SHP = os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp")
sb = pyogrio.read_dataframe(SETTLE_SHP, columns=["SETTLE"])
sb["S"] = sb.SETTLE.str.strip().str.upper()
assert set(sb.S) == set(pop)
geo = pyogrio.read_dataframe(PLOTS, columns=[])
cent = geo.geometry.centroid.values
poly = dict(zip(sb.S, sb.geometry.values))
p["INSIDE"] = [bool(shapely.contains(poly[s], c)) for s, c in zip(p.S, cent)]

# Earlier decisions kept (W14 rules, W14/docs/W14_LOAD_AND_GROWTH.md; checked 2026-11-16 at the engineer's request):
#  rule 4  - the two industrial estates (4,500 + 1,800 workers x 93 L/d, S_SPEC, 316.4 m3/d) are ADDITIVE, outside the
#            per-capita volume (doctrine 1b): taken out of the existing pattern and added on their plots every year;
#  rule 9d - growth lands only on W14's spread set: empty plots up to 2,000 m2, not grove, industrial, heritage or
#            estate (SPREAD_W > 0); 9e heritage takes nothing. The weighting is now equal per plot (8 Nov, NWS), no
#            longer W14's area capped at 1,000 m2.
w14 = pyogrio.read_dataframe(os.path.join(W18, "..", "W14", "shp", "PLOTS_load.shp"), columns=["AREA_M2", "SPREAD_W", "S_SPEC", "HOMESHAPE", "COMPACT", "ASPECT", "Classes", "DERIVED", "ESTATE"], read_geometry=False)
assert len(w14) == len(p) and np.allclose(w14.AREA_M2.values, pyogrio.read_dataframe(PLOTS, columns=["AREA_M2"], read_geometry=False).AREA_M2.values, atol=0.01)
p["SPEC"] = w14.S_SPEC.values
# Growth only on HOME-SHAPED empty plots (engineer, 2026-11-16: large or non-square plots take no growth): W14 rule 9,
# 200-1,000 m2, compact >= 0.6, aspect <= 3, not grove, industrial, heritage or estate - the plots its capacity counted.
# Under an equal share per plot, slivers and strips of W14's spread set would take as much as a house plot.
# Upper limit raised from 1,000 to 2,000 m2 (engineer, 2026-11-16, after the plot-flow check maps; 2,000 m2 is also the
# ceiling of W14's spread set). The test is W14's (plot_class_v2_apply.py), rebuilt here from its COMPACT and ASPECT
# fields; with 1,000 m2 it reproduces W14's HOMESHAPE plot for plot.
# THE RULE NOW (engineer, 2026-11-17: "the limit is 200 to 3000 m2; proposed agriculture lands out; all odd shape plots
# out"): a growth plot is a future plot ZONED residential by MoHUP (Residential or Residential-Commercial, the plots the
# team's capacity counts), 200-3,000 m2, not odd-shaped (W14's test: compact >= 0.6, aspect <= 3), not agricultural
# (zoned so, or a grove on W14's satellite test), not heritage, industrial or an estate. It replaces W14's spread set,
# which stopped at 2,000 m2 and put growth on 1,197 plots zoned commercial or agricultural.
# Zoning ignored (engineer, 2026-11-17: "I am not sure the proposed plot use are correct ... treat all receiving plots
# the same"): any future zoning qualifies - residential, commercial, proposed - except agricultural (the engineer's rule),
# Tourism (MoHUP's class for the heritage plots, W14 rule 9e) and Industrial (the estates carry their own load).
HOME_LO, HOME_HI = 200.0, 3000.0
home = lambda w, hi: (w.AREA_M2 >= HOME_LO) & (w.AREA_M2 <= hi) & (w.COMPACT >= 0.6) & (w.ASPECT <= 3)
assert (home(w14, 1000.0).astype(int) == w14.HOMESHAPE).all()
zoned_ok = ~w14.Classes.isin(["Agricultural", "Tourism", "Industrial"])
excluded = w14.DERIVED.isin(["Agricultural", "Industrial", "Heritage"]) | w14.ESTATE.notna()
p["SPREAD"] = (zoned_ok & home(w14, HOME_HI) & ~excluded).values

# CAPACITY (engineer, 2026-11-17): the 2026 population stays on the existing plots and each growth plot takes the team's
# properties per plot (sheet 'MOHUP DATA - NA', column D) x 4.8 people: capacity = P_2026 + growth plots x D x 4.8.
# It replaces the team's column G, (existing + future residential properties) x 4.8, which counted the existing
# properties at 4.8 people (Ibri holds 5.98 per property in 2026) and the team's own count of future plots. The team's
# average population is unchanged: the capacity only sets the year a settlement stops growing.
# Same as results/W18_MOHUP_DATA_NA_growth_plots.xlsx, column J (py/mohup_sheet_growth_plots.py).
OCC = 4.8
ppp = {md.cell(r, 1).value.strip().upper(): md.cell(r, 4).value for r in range(2, md.max_row + 1)
       if md.cell(r, 1).value and md.cell(r, 1).value != "Total"}
n_growth = {s: int(((p.S == s) & p.INSIDE & (p.STATUS == "Future") & p.SPREAD).sum()) for s in pop}
cap_team = cap
cap = {s: pop[s][BASE] + n_growth[s] * ppp[s] * OCC for s in pop}

rows, out = [], {f"Q_{y}": np.zeros(len(p)) for y in YEARS}
for s in sorted(pop):
    assert pop[s][BASE] < cap[s], f"{s} already over capacity in {BASE}"
    m = ((p.S == s) & p.INSIDE).values
    base_w = (p.Q_2024.values - p.SPEC.values) * m
    tgt = m & (p.STATUS == "Future").values & p.SPREAD.values
    n_t = int(tgt.sum()); assert n_t == n_growth[s], s
    spec = p.SPEC.values * m
    f_base = pop[s][BASE] * rate
    for y in YEARS:
        P = min(pop[s][y], cap[s]); F = P * rate; G = F - f_base
        q = base_w / base_w.sum() * f_base
        if n_t: q = q + tgt * (G / n_t)
        else:   q = base_w / base_w.sum() * F                       # no future plot to spread on: existing plots take the growth
        out[f"Q_{y}"] += q + spec
        rows.append(dict(settlement=s, year=y, pop_team=pop[s][y], capacity=cap[s], capacity_team=cap_team[s], pop_used=P,
                         capped=pop[s][y] > cap[s], flow_m3d=F, special_m3d=spec.sum(), future_spread_plots=n_t,
                         plots_outside_boundary=int(((p.S == s) & ~p.INSIDE).sum())))
sf = pd.DataFrame(rows)
for y in YEARS:
    p[f"Q_{y}"] = out[f"Q_{y}"]
    got = p.groupby("S")[f"Q_{y}"].sum()
    want = sf[sf.year == y].set_index("settlement").eval("flow_m3d + special_m3d")
    assert (got - want).abs().max() < 1e-6, y

# the team's scenario sheet carries infiltration per settlement; take it off to compare
sc = openpyxl.load_workbook(SCEN, data_only=True).active
team = {sc.cell(1, c).value: sum(sc.cell(r, c).value for r in range(2, 27)) for c in range(2, 7)}
infil = sum(wb["Base Demand"].cell(r, 3).value for r in range(7, 32))

qcols = [f"Q_{y}" for y in YEARS]

# The manhole each plot loads. HMINNODE is 0 on 6,499 plots (6,246 future) that carried no flow in W14, so the load
# builder never linked them; under the equal share they now carry flow. SewerGEMS cannot take a load on a manhole that
# has no load row (jobs 060-066), so every plot goes to a manhole that carries a row in all six year alternatives:
# its own HMINNODE where that holds, otherwise the nearest such manhole (the load builder's nearest-node rule).
from scipy.spatial import cKDTree
ROWS = r"D:\VBOX\bridge\out\r4\diag\rows_{}.csv"
rowed = set.intersection(*[set(pd.read_csv(ROWS.format(y)).mh_id) for y in ("2030", "2040", "2050", "2055", "2060", "2070")])
nodes = pd.read_csv(r"D:\VBOX\bridge\out\inv_w17\nodes.csv")
nodes = nodes[nodes.id.isin(rowed)]
g = pyogrio.read_dataframe(PLOTS, columns=[])
cen = np.column_stack([g.geometry.centroid.x.values, g.geometry.centroid.y.values])
own = p.HMINNODE.fillna(0).astype(int).values
need = ~np.isin(own, list(rowed))
dist, idx = cKDTree(nodes[["x", "y"]].values).query(cen[need])
p["MH_W18"] = own
p.loc[need, "MH_W18"] = nodes.id.values[idx]
p["MH_DIST"] = 0.0
p.loc[need, "MH_DIST"] = dist
moved = need & (p[qcols[-1]].values > 0)

# What the network carries (engineer, 2026-11-16): a plot whose manhole is inactive (the deactivated areas, as in W17)
# is not carried, and neither is a plot whose edge lies more than 200 m from the nearest active sewer (land left
# without a network: steep ground, vegetation). Their flow stays in the settlement totals, reported as not carried.
from shapely import STRtree, linestrings
allnodes = pd.read_csv(r"D:\VBOX\bridge\out\inv_w17\nodes.csv").set_index("id")
cd = pd.read_csv(r"D:\VBOX\bridge\out\scen\S1\conduits_S1-2070.csv")
cd = cd[cd.active == True]
seg = linestrings(np.stack([allnodes.loc[cd.start, ["x", "y"]].values, allnodes.loc[cd.stop, ["x", "y"]].values], axis=1))
_, dpipe = STRtree(seg).query_nearest(g.geometry.values, return_distance=True, all_matches=False)
NO_NETWORK_M = 200.0
p["D_PIPE"] = dpipe
p["MH_ACTIVE"] = allnodes.loc[p.MH_W18, "active"].values.astype(bool)
p["WHY_OUT"] = np.where(~p.MH_ACTIVE, "inactive manhole", np.where(p.D_PIPE > NO_NETWORK_M, "over 200 m from a sewer", ""))
p["CARRIED"] = p.WHY_OUT == ""

p["GROWTH"] = ((p.STATUS == "Future") & p.INSIDE & p.SPREAD).astype(int)   # the growth plots, read by plot_layer_2100.py
p[["SETTLE", "STATUS", "CADASTRE", "USE", "HMINNODE", "MH_W18", "MH_DIST", "D_PIPE", "WHY_OUT", "GROWTH"] + qcols].to_csv(os.path.join(OUT, "plot_loads.csv"), index_label="FID", float_format="%.6f")
mh = p[p.CARRIED].groupby("MH_W18")[qcols].sum()
assert set(mh.index) <= rowed
out_tab = p[~p.CARRIED].groupby("WHY_OUT")[qcols].sum()
out_tab.loc["total not carried"] = out_tab.sum()
out_tab.to_csv(os.path.join(OUT, "not_carried.csv"), float_format="%.2f")
mh.to_csv(os.path.join(OUT, "manhole_loads.csv"), index_label="manhole_id", float_format="%.6f")
sf.to_csv(os.path.join(OUT, "settlement_flows.csv"), index=False, float_format="%.4f")

L = ["# W18 loads, check", "", f"Rate {rate*1000:.3f} L/person/day; plots {len(p):,}; manholes loaded {len(mh):,}, every one carrying a row in all six year alternatives.",
     f"Plots linked to a manhole here (no HMINNODE, or one without a row): {int(need.sum()):,}; carrying flow in {YEARS[-1]}: {int(moved.sum()):,} "
     f"({p.loc[moved, qcols[-1]].sum():,.1f} m3/d), distance to the manhole median {np.median(dist):,.0f} m, 95th percentile {np.percentile(dist, 95):,.0f} m, max {dist.max():,.0f} m", "",
     f"Not carried by the network, m3/d (plots: inactive manhole {int((p.WHY_OUT == 'inactive manhole').sum()):,}, over 200 m from a sewer {int((p.WHY_OUT == 'over 200 m from a sewer').sum()):,}):", "",
     "| | " + " | ".join(qcols) + " |", "|---|" + "---|" * len(qcols)]
L += [f"| {k} | " + " | ".join(f"{v:,.1f}" for v in r) + " |" for k, r in out_tab.iterrows()]
L += ["", f"Carried by the network (the model's loads): " + ", ".join(f"{c} {mh[c].sum():,.1f}" for c in qcols), "",
     "| year | people used | plot flow m3/d | team sheet less infiltration ({:,.1f}) | difference | settlements capped |".format(infil),
     "|---|---|---|---|---|---|"]
for y in YEARS:
    t = sf[sf.year == y]; fl = p[f"Q_{y}"].sum()
    tm = team.get(y); d = "" if tm is None else f"{fl - (tm - infil):,.1f}"
    L.append(f"| {y} | {t.pop_used.sum():,.0f} | {fl:,.1f} | {'' if tm is None else f'{tm - infil:,.1f}'} | {d} | {', '.join(t[t.capped].settlement) or '-'} |")
open(os.path.join(OUT, "check.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
