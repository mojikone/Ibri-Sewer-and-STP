"""W18 plot loads on the NWS basis of November 2026.

Volume: the team's settlement population (mean of the NCSI, meters x 4.8 and APSR series, sheet 'Average'
of 'New Calculation MH.xlsx'), capped at the settlement's capacity of its empty plots (sheet 'MOHUP DATA - NA',
column G; engineer 2026-11-16: each settlement grows only until its empty plots are full, no overflow),
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
YEARS = [2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061, 2066, 2071]
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

rows, out = [], {f"Q_{y}": np.zeros(len(p)) for y in YEARS}
for s in sorted(pop):
    assert pop[s][BASE] < cap[s], f"{s} already over capacity in {BASE}"
    m = (p.S == s).values
    base_w = p.Q_2024.values * m
    tgt = m & (p.STATUS == "Future").values & p.CADASTRE.isin(TARGET_USES).values
    n_t = int(tgt.sum())
    f_base = pop[s][BASE] * rate
    for y in YEARS:
        P = min(pop[s][y], cap[s]); F = P * rate; G = F - f_base
        q = base_w / base_w.sum() * f_base
        if n_t: q = q + tgt * (G / n_t)
        else:   q = base_w / base_w.sum() * F                       # no future home plot: existing plots take the growth
        out[f"Q_{y}"] += q
        rows.append(dict(settlement=s, year=y, pop_team=pop[s][y], capacity=cap[s], pop_used=P,
                         capped=pop[s][y] > cap[s], flow_m3d=F, future_home_plots=n_t))
sf = pd.DataFrame(rows)
for y in YEARS:
    p[f"Q_{y}"] = out[f"Q_{y}"]
    got = p.groupby("S")[f"Q_{y}"].sum()
    want = sf[sf.year == y].set_index("settlement").flow_m3d
    assert (got - want).abs().max() < 1e-6, y

# the team's scenario sheet carries infiltration per settlement; take it off to compare
sc = openpyxl.load_workbook(SCEN, data_only=True).active
team = {sc.cell(1, c).value: sum(sc.cell(r, c).value for r in range(2, 27)) for c in range(2, 7)}
infil = sum(wb["Base Demand"].cell(r, 3).value for r in range(7, 32))

qcols = [f"Q_{y}" for y in YEARS]
p[["SETTLE", "STATUS", "CADASTRE", "USE", "HMINNODE"] + qcols].to_csv(os.path.join(OUT, "plot_loads.csv"), index_label="FID", float_format="%.6f")
mh = p.dropna(subset=["HMINNODE"]).groupby(p.HMINNODE.dropna().astype(int))[qcols].sum()
mh.to_csv(os.path.join(OUT, "manhole_loads.csv"), index_label="manhole_id", float_format="%.6f")
sf.to_csv(os.path.join(OUT, "settlement_flows.csv"), index=False, float_format="%.4f")

L = ["# W18 loads, check", "", f"Rate {rate*1000:.3f} L/person/day; plots {len(p):,}; manholes loaded {len(mh):,}; "
     f"plots without a manhole {int(p.HMINNODE.isna().sum())} carrying {p.loc[p.HMINNODE.isna(), qcols[-1]].sum():.1f} m3/d in {YEARS[-1]}", "",
     "| year | people used | plot flow m3/d | team sheet less infiltration ({:,.1f}) | difference | settlements capped |".format(infil),
     "|---|---|---|---|---|---|"]
for y in YEARS:
    t = sf[sf.year == y]; fl = p[f"Q_{y}"].sum()
    tm = team.get(y); d = "" if tm is None else f"{fl - (tm - infil):,.1f}"
    L.append(f"| {y} | {t.pop_used.sum():,.0f} | {fl:,.1f} | {'' if tm is None else f'{tm - infil:,.1f}'} | {d} | {', '.join(t[t.capped].settlement) or '-'} |")
open(os.path.join(OUT, "check.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
