"""Independent audit of the W18 deliverables (engineer, 2026-11-17: "review all the excel and plot data"). Recomputes
every rule from the RAW sources - the team's workbook, the W14 plot layer, the model's plot layer and the W14
settlement boundaries - without importing the scripts under test, then compares:
  A  the capacity workbook (results/W18_MOHUP_DATA_NA_growth_plots.xlsx), cell by cell
  B  the plot layer 2026-2100 (gis/W18_plots_2026_2100.shp)
  C  the settlement layer 2026-2100 (gis/W18_settlements_2026_2100.shp)
  D  the model loads (results/loads/*.csv)
  E  the QGIS zip (gis/W18_plot_flows_QGIS.zip)
Writes results/loads/audit.md; exits non-zero if any check fails.  Usage: python audit_w18.py"""
import os, sys, io, zipfile, hashlib
import numpy as np, pandas as pd, pyogrio, openpyxl, shapely

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE); ROOT = os.path.dirname(W18)
TEAMWB = os.path.join(ROOT, "..", "temp", "recent updates by the team", "New Calculation MH.xlsx")
W14P = os.path.join(ROOT, "W14", "shp", "PLOTS_load.shp")
SB = os.path.join(ROOT, "W14", "shp", "Settlements_merged.shp")
MODEL = r"C:\Users\mojtaba\Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\SHP\Plots\Plots.shp"
PL = os.path.join(W18, "gis", "W18_plots_2026_2100.shp")
ST = os.path.join(W18, "gis", "W18_settlements_2026_2100.shp")
XL = os.path.join(W18, "results", "W18_MOHUP_DATA_NA_growth_plots.xlsx")
LD = os.path.join(W18, "results", "loads")
ZP = os.path.join(W18, "gis", "W18_plot_flows_QGIS.zip")
YEARS = list(range(2026, 2101)); MY = list(range(2026, 2092, 5)); OCC = 4.8
R = []                                                     # (section, check, ok, detail)
def chk(sec, name, ok, detail=""): R.append((sec, name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + sec, name, detail)

# ---------------------------------------------------------------- raw sources
tv = openpyxl.load_workbook(TEAMWB, data_only=True)
rate = tv["Base Demand"]["H4"].value / 1000.0
tav, tmd, tbs = tv["Average"], tv["MOHUP DATA - NA"], tv["Base MOHUP Data - NA"]
yc = {tav.cell(1, c).value: c for c in range(2, tav.max_column + 1)}
avg = {tav.cell(r, 1).value.strip().upper(): np.array([tav.cell(r, yc[y]).value for y in YEARS], float) for r in range(2, 27)}
team = {tmd.cell(r, 1).value.strip().upper(): dict(row=r, B=tmd.cell(r, 2).value, C=tmd.cell(r, 3).value, D=tmd.cell(r, 4).value,
        G=tmd.cell(r, 7).value, H=tmd.cell(r, 8).value) for r in range(2, 27)}
base = {}
for r in range(3, 30):
    n = tbs.cell(r, 1).value
    if n and n.strip() != "Total" and n.strip().upper() not in base:
        base[n.strip().upper()] = (tbs.cell(r, 6).value or 0) + (tbs.cell(r, 7).value or 0)
S25 = sorted(team)
w14 = pyogrio.read_dataframe(W14P, columns=["SETTLE", "AREA_M2", "Classes", "DERIVED", "ESTATE", "COMPACT", "ASPECT", "POP",
                                            "G_DOM", "G_NDOM", "G_GOV", "G_SPEC", "G_AGR", "S_SPEC"], read_geometry=False)
mod = pyogrio.read_dataframe(MODEL, columns=["PLOT_NO", "SETTLE", "CADASTRE", "STATUS", "AREA_M2", "USE", "Q_2024", "HMINNODE"])
sb = pyogrio.read_dataframe(SB, columns=["SETTLE"]); sb["S"] = sb.SETTLE.str.strip().str.upper(); poly = dict(zip(sb.S, sb.geometry.values))

cols = ["PLOT_NO", "CADASTRE", "SETTLE", "AREA_M2", "STATUS", "LANDUSE", "MOH_USE", "M_DOM", "M_COM", "M_GOV", "M_SPEC", "M_AGR",
        "PROP_EX", "PROP_FUT", "PROPS", "IN_BOUND", "GROWTH", "NETWORK", "MH_W18"] + [f"POP_{y}" for y in YEARS] + [f"Q_{y}" for y in YEARS]
p = pyogrio.read_dataframe(PL, columns=cols, read_geometry=False)
p["S"] = p.SETTLE.str.strip().str.upper()
POP = p[[f"POP_{y}" for y in YEARS]].values; Q = p[[f"Q_{y}" for y in YEARS]].values

# independent recomputation of the rules
inside = np.array([bool(shapely.contains(poly[s], c)) for s, c in zip(mod.SETTLE.str.strip().str.upper(), mod.geometry.centroid.values)])
fut = (mod.STATUS == "Future").values
growth = (fut & inside & (w14.AREA_M2 >= 200).values & (w14.AREA_M2 <= 3000).values & (w14.COMPACT >= 0.6).values
          & (w14.ASPECT <= 3).values & ~w14.Classes.isin(["Agricultural", "Tourism", "Industrial"]).values
          & ~w14.DERIVED.isin(["Agricultural", "Industrial", "Heritage"]).values & w14.ESTATE.isna().values)
ngrow = {s: int((growth & (p.S == s).values).sum()) for s in S25}
cap = {s: avg[s][0] + ngrow[s] * max(1.0, team[s]["B"] / base[s]) * OCC for s in S25}
used = {s: np.minimum(avg[s], cap[s]) for s in S25}
def full(series, c): return next((y for y, v in zip(YEARS, series) if v >= c), None)

# ---------------------------------------------------------------- A  workbook
xf = openpyxl.load_workbook(XL); xv = openpyxl.load_workbook(XL, data_only=True)
chk("A", "sheets", xv.sheetnames == ["MOHUP DATA - NA", "Team original", "Average", "Notes"], str(xv.sheetnames))
a_diff = max(abs((xv["Average"].cell(r, c).value or 0) - (tav.cell(r, c).value or 0)) if isinstance(tav.cell(r, c).value, (int, float))
             else (0 if xv["Average"].cell(r, c).value == tav.cell(r, c).value else 1e9) for r in range(1, 28) for c in range(1, 77))
chk("A", "Average sheet = the team's Average, rows 1-27 x 2026-2100", a_diff < 1e-9, f"max difference {a_diff:.2e}")
def same(a, b):                                            # Excel stores 15 significant figures
    return abs(a - b) <= 1e-12 * max(1.0, abs(b)) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else a == b
t_bad = [(r, c) for r in range(1, 28) for c in range(1, 9) if not same(xv["Team original"].cell(r, c).value, tmd.cell(r, c).value)]
chk("A", "Team original = the team's MOHUP DATA - NA (values, to Excel's 15 figures)", not t_bad, f"{len(t_bad)} cells differ {t_bad[:5]}")
s, sf_ = xv["MOHUP DATA - NA"], xf["MOHUP DATA - NA"]
chk("A", "persons per new property B29 = 4.8", s["B29"].value == 4.8)
bad = []
for r in range(2, 27):
    k = s[f"A{r}"].value.strip().upper(); t = team[k]; v = {c: s[f"{c}{r}"].value for c in "BCDEFGHIJKMNO"}
    E = max(1.0, t["B"] / base[k]); G = ngrow[k] * E; I = G * OCC; J = avg[k][0] + I
    fy = full(avg[k], J) or "Not Fully Occupied"; fyt = full(avg[k], t["G"]) or "Not Fully Occupied"
    exp = dict(B=t["B"], C=avg[k][0], D=base[k], E=E, F=ngrow[k], G=G, H=t["B"] + G, I=I, J=J, K=fy, M=t["C"], N=t["G"], O=fyt)
    for c, e in exp.items():
        ok = (v[c] == e) if isinstance(e, str) or c in "BDFMK O" and not isinstance(e, float) else abs(v[c] - e) < 1e-6 * max(1, abs(e))
        if not ok: bad.append((k, c, v[c], e))
    if abs(E - t["D"]) > 1e-9: bad.append((k, "E vs team D", E, t["D"]))
    if fyt != t["H"]: bad.append((k, "O vs team H", fyt, t["H"]))
chk("A", "every row recomputed from the raw sources (B-O, 25 settlements)", not bad, f"{len(bad)} mismatches {bad[:4]}")
tot = {c: s[f"{c}27"].value for c in "BCDFGHIJMN"}
exp_t = {c: sum(s[f"{c}{r}"].value for r in range(2, 27)) for c in tot}
chk("A", "total row = sum of the rows", all(abs(tot[c] - exp_t[c]) < 1e-6 for c in tot), f"capacity {tot['J']:,.0f}, team {tot['N']:,.0f}")
nf = [f"{c}{r}" for r in range(2, 28) for c in "BCEGHIJKMNO" if (r < 27 or c in "BCGHIJMN") and not str(sf_[f"{c}{r}"].value).startswith("=")]
chk("A", "formula cells hold formulas (not typed values)", not nf, f"{len(nf)} typed: {nf[:5]}")
errs = [f"{c}{r}" for r in range(2, 28) for c in "ABCDEFGHIJKMNO" if isinstance(s[f"{c}{r}"].value, str) and s[f"{c}{r}"].value.startswith("#")]
chk("A", "no error values", not errs, str(errs[:5]))
mono = all((np.diff(avg[k]) >= 0).all() for k in S25)
chk("A", "population never falls (the COUNTIF saturation year relies on it)", mono)

# ---------------------------------------------------------------- B  plot layer
chk("B", "77,265 plots, row for row with W14 and the model", len(p) == len(w14) == len(mod) and np.allclose(p.AREA_M2, w14.AREA_M2, atol=0.01)
    and (p.PLOT_NO.values == mod.PLOT_NO.values).all() and (p.SETTLE.values == mod.SETTLE.values).all())
chk("B", "PLOT_NO unique", p.PLOT_NO.is_unique)
chk("B", "STATUS and LANDUSE = the model's", (p.STATUS.values == mod.STATUS.values).all() and (p.LANDUSE.values == mod.USE.values).all())
chk("B", "MOH_USE = W14 Classes (MoH file)", (p.MOH_USE.values == w14.Classes.values).all())
cad_same = (p.CADASTRE.fillna("").values == p.MOH_USE.fillna("").values).mean()
fd = open(os.path.join(W18, "gis", "W18_plots_2026_2100_fields.md"), encoding="utf-8").read()
chk("B", "CADASTRE = MOH_USE, and the field list says so (the model's name; no cadastre number in the source)",
    cad_same == 1.0 and "identical to MOH_USE" in fd, f"equal on {cad_same:.1%} of plots")
meters = all((p[m].values == w14[g].values).all() for m, g in (("M_DOM", "G_DOM"), ("M_COM", "G_NDOM"), ("M_GOV", "G_GOV"), ("M_SPEC", "G_SPEC"), ("M_AGR", "G_AGR")))
chk("B", "meters = W14 meters by category; PROP_EX = M_DOM", meters and (p.PROP_EX.values == p.M_DOM.values).all())
chk("B", "IN_BOUND recomputed (centroid in own settlement)", (p.IN_BOUND.values == inside.astype(int)).all(), f"{int((~inside).sum()):,} outside")
gd = int((p.GROWTH.values.astype(bool) != growth).sum())
chk("B", "GROWTH recomputed from the rule", gd == 0, f"{int(growth.sum()):,} growth plots recomputed, {gd} differ")
chk("B", "no NaN or negative people or flow", np.isfinite(POP).all() and np.isfinite(Q).all() and (POP >= -1e-9).all() and (Q >= -1e-9).all())
out = ~inside
chk("B", "plots outside their boundary: no people, no flow, every year", np.abs(POP[out]).max() == 0 and np.abs(Q[out]).max() == 0)
ex = (p.STATUS == "Existing").values
chk("B", "existing plots: people and flow fixed at 2026 every year", np.abs(POP[ex] - POP[ex][:, [0]]).max() < 1e-9 and np.abs(Q[ex] - Q[ex][:, [0]]).max() < 1e-9)
fng = fut & inside & ~growth
spec = w14.S_SPEC.fillna(0).values
q_fng = np.abs(Q[fng] - spec[fng][:, None]).max()
chk("B", "future plots that do not take growth: no people; flow only the estates' own (constant)", np.abs(POP[fng]).max() == 0 and q_fng < 1e-4,
    f"{int(fng.sum()):,} plots, {int((spec[fng] > 0).sum())} estate plots among them, max deviation {q_fng:.1e}")
qb = (mod.Q_2024.values - spec)
chk("B", "no future plot carries a 2024 flow (the 2026 pattern stays on existing plots)", (np.abs(qb[fut]) < 1e-9).all(), f"max {np.abs(qb[fut]).max():.2e}")
e_pat, e_pop, e_sum, g_eq, g_val, g_q, s_pop, s_q, s_cap = [], [], [], [], [], [], [], [], []
for k in S25:
    m = (p.S == k).values & inside; me = m & ex; mg = m & growth
    # existing pattern: 2026 people in proportion to W14 residents, 2026 flow (less estates) in proportion to the model's 2024 flow
    rp = POP[me, 0][w14.POP.values[me] > 0] / w14.POP.values[me][w14.POP.values[me] > 0]
    if len(rp): e_pop.append(np.ptp(rp) / rp.mean())
    rq = (Q[me, 0] - spec[me])[qb[me] > 1e-9] / qb[me][qb[me] > 1e-9]
    if len(rq): e_pat.append(np.ptp(rq) / rq.mean())
    e_sum.append(abs(POP[me, 0].sum() - avg[k][0]))
    want = used[k] - avg[k][0]
    g_eq.append(np.ptp(POP[mg], axis=0).max() if mg.sum() else 0)
    g_val.append(np.abs(POP[mg] - want / mg.sum()).max() if mg.sum() else 0)
    g_q.append(np.abs(Q[mg] - POP[mg] * rate).max() if mg.sum() else 0)
    s_pop.append(np.abs(POP[m].sum(axis=0) - used[k]).max())
    s_q.append(np.abs(Q[m].sum(axis=0) - (used[k] * rate + spec[m].sum())).max())
    s_cap.append(POP[m].sum(axis=0).max() - cap[k])
chk("B", "existing plots, 2026 people in the W14 resident pattern", max(e_pop) < 1e-3, f"max spread of people/W14 resident within a settlement {max(e_pop):.1e}")
chk("B", "existing plots, 2026 flow in the 2024 pattern of the model", max(e_pat) < 1e-3, f"max spread {max(e_pat):.1e}")
chk("B", "existing plots hold the team's 2026 population", max(e_sum) < 0.5, f"max difference {max(e_sum):.3f} people")
chk("B", "growth plots: one equal share per settlement and year", max(g_eq) < 1e-4, f"max spread {max(g_eq):.1e} people")
chk("B", "growth share = (min(team average, capacity) - 2026 population) / growth plots", max(g_val) < 1e-3, f"max error {max(g_val):.1e} people")
chk("B", "growth plots: flow = people x 171.03 L/d", max(g_q) < 1e-4, f"rate {rate*1000:.3f} L/d, max error {max(g_q):.1e} m3/d")
chk("B", "settlement people = min(team average, capacity), every year", max(s_pop) < 0.5, f"max error {max(s_pop):.3f} people")
chk("B", "settlement flow = people x rate + estates, every year", max(s_q) < 0.1, f"max error {max(s_q):.4f} m3/d")
chk("B", "no settlement above its capacity", max(s_cap) < 0.5, f"max excess {max(s_cap):.3f}")
pf = np.where(growth, (POP[:, -1] - POP[:, 0]) / OCC, 0.0)
chk("B", "PROP_FUT = people added by 2100 / 4.8; PROPS = PROP_EX + PROP_FUT", np.abs(p.PROP_FUT.values - pf).max() < 0.006
    and np.abs(p.PROPS.values - p.PROP_EX.values - p.PROP_FUT.values).max() < 0.006)
chk("B", "growth plots never lose people from one year to the next", (np.diff(POP[growth], axis=1) >= -1e-6).all())
i64 = int(np.argmax(p.PROP_EX.values))
chk("B", f"largest existing plot ({p.PROP_EX.values[i64]} properties, {p.SETTLE.values[i64]}) fixed", np.ptp(POP[i64]) == 0 and np.ptp(Q[i64]) == 0,
    f"{POP[i64, 0]:.1f} people, {Q[i64, 0]:.1f} m3/d every year")

# ---------------------------------------------------------------- C  settlement layer
st = pyogrio.read_dataframe(ST); st["S"] = st.SETTLE.str.strip().str.upper(); st = st.set_index("S")
chk("C", "25 settlements, the W14 boundaries", len(st) == 25 and set(st.index) == set(S25) and
    max(abs(st.loc[k, "AREA_KM2"] - poly[k].area / 1e6) for k in S25) < 0.001)
cp = max(abs(st.loc[k, f"P_{y}"] - POP[(p.S == k).values, i].sum()) for k in S25 for i, y in enumerate(YEARS))
cq = max(abs(st.loc[k, f"Q_{y}"] - Q[(p.S == k).values, i].sum()) for k in S25 for i, y in enumerate(YEARS))
chk("C", "P_yyyy and Q_yyyy = sums of the plot layer, 2026-2100", cp < 0.1 and cq < 0.01, f"max {cp:.3f} people, {cq:.4f} m3/d")
xs = {s[f"A{r}"].value.strip().upper(): r for r in range(2, 27)}
cc = []
for k in S25:
    r = xs[k]; m = (p.S == k).values; mi = m & inside
    fy = full(avg[k], cap[k]) or 0
    tests = dict(CAPACITY=(st.loc[k, "CAPACITY"], cap[k], 0.06), CAP_TEAM=(st.loc[k, "CAP_TEAM"], team[k]["G"], 0.06),
                 FULL_YEAR=(st.loc[k, "FULL_YEAR"], fy, 0), FULL_TEAM=(st.loc[k, "FULL_TEAM"], str(team[k]["H"]), None),
                 N_GROWTH=(st.loc[k, "N_GROWTH"], ngrow[k], 0), TEAM_PLOTS=(st.loc[k, "TEAM_PLOTS"], team[k]["C"], 0),
                 PPP_TEAM=(st.loc[k, "PPP_TEAM"], team[k]["D"], 0.0006), PPP_SAT=(st.loc[k, "PPP_SAT"], max(1.0, team[k]["B"] / base[k]), 0.0006),
                 N_PLOTS=(st.loc[k, "N_PLOTS"], int(mi.sum()), 0), N_EXIST=(st.loc[k, "N_EXIST"], int((mi & ex).sum()), 0),
                 N_EMPTY=(st.loc[k, "N_EMPTY"], int((mi & fut).sum()), 0), N_OUTSIDE=(st.loc[k, "N_OUTSIDE"], int((m & ~inside).sum()), 0),
                 PROP_2026=(st.loc[k, "PROP_2026"], int(p.PROP_EX.values[m].sum()), 0), PROP_2100=(st.loc[k, "PROP_2100"], p.PROPS.values[m].sum(), 0.06),
                 OR_2026=(st.loc[k, "OR_2026"], avg[k][0] / max(p.PROP_EX.values[m].sum(), 1), 0.0006),
                 QNC_2071=(st.loc[k, "QNC_2071"], Q[m & (p.NETWORK != "connected").values, YEARS.index(2071)].sum(), 0.006),
                 EX_RES=(st.loc[k, "EX_RES"], int((mi & ex & (p.LANDUSE == "Residential").values).sum()), 0),
                 NA_DOM=(st.loc[k, "NA_DOM"], int((mi & ex & (p.M_DOM > 0).values).sum()), 0),
                 CAP_XL=(s[f"J{r}"].value, st.loc[k, "CAPACITY"], 0.06), N_XL=(s[f"F{r}"].value, st.loc[k, "N_GROWTH"], 0))
    for f, (got, e, tol) in tests.items():
        ok = (str(got) == e) if tol is None else abs(got - e) <= tol
        if not ok: cc.append((k, f, got, e))
chk("C", "settlement fields recomputed (capacity, years, counts, properties, OR, not carried) and = workbook", not cc, f"{len(cc)} mismatches {cc[:4]}")

# ---------------------------------------------------------------- D  loads (the model's input)
pl = pd.read_csv(os.path.join(LD, "plot_loads.csv"), index_col="FID")
dq = max(np.abs(pl[f"Q_{y}"].values - Q[:, YEARS.index(y)]).max() for y in MY)
chk("D", f"plot_loads.csv = plot layer in the model years {MY[0]}-{MY[-1]}", dq < 1e-4, f"max {dq:.1e} m3/d")
chk("D", "plot_loads.csv growth flag = recomputed rule", (pl.GROWTH.values.astype(bool) == growth).all())
car = (p.NETWORK == "connected").values
chk("D", "not carried = inactive manhole or over 200 m (and nothing else)", set(p.NETWORK) == {"connected", "inactive manhole", "over 200 m from a sewer"}
    and ((pl.WHY_OUT.fillna("") == "").values == car).all())
mh = pd.read_csv(os.path.join(LD, "manhole_loads.csv"), index_col="manhole_id")
g = pd.DataFrame({f"Q_{y}": Q[car, YEARS.index(y)] for y in MY}, index=p.MH_W18.values[car]).groupby(level=0).sum()
dm = max(np.abs(mh.loc[g.index, c].values - g[c].values).max() for c in g.columns)
chk("D", "manhole_loads.csv = carried plot flow summed per manhole", set(g.index) <= set(mh.index) and dm < 1e-3,
    f"{len(g):,} manholes, max {dm:.1e} m3/d; carried 2056 {mh['Q_2056'].sum():,.1f}, 2071 {mh['Q_2071'].sum():,.1f}")
sfl = pd.read_csv(os.path.join(LD, "settlement_flows.csv"))
ds = max(abs(r.capacity - cap[r.settlement]) for r in sfl.itertuples())
chk("D", "settlement_flows.csv capacity = recomputed capacity", ds < 1e-3, f"max {ds:.1e}")

# ---------------------------------------------------------------- E  QGIS zip
z = zipfile.ZipFile(ZP); names = set(z.namelist())
want = {"W18_plot_flows/layers/" + os.path.basename(f): f for b in ("W18_plots_2026_2100", "W18_settlements_2026_2100")
        for f in [os.path.join(W18, "gis", b + e) for e in (".shp", ".shx", ".dbf", ".prj", ".cpg")] if os.path.exists(f)}
want["W18_plot_flows/W18_MOHUP_DATA_NA_growth_plots.xlsx"] = XL
h = lambda b: hashlib.md5(b).hexdigest()
stale = [n for n, f in want.items() if n not in names or h(z.read(n)) != h(open(f, "rb").read())]
chk("E", "zip layers and workbook = the files on disk", not stale, f"stale or missing: {stale}")
qgz = zipfile.ZipFile(io.BytesIO(z.read("W18_plot_flows/W18_plot_flows.qgz")))
qs = qgz.read(next(n for n in qgz.namelist() if n.endswith(".qgs"))).decode("utf-8")
chk("E", "project inside the zip reads ./layers only", "./layers/W18_plots_2026_2100.shp" in qs and "../" not in qs)

# ---------------------------------------------------------------- report
fails = [r for r in R if not r[2]]
L = ["# W18 audit", "", f"{len(R)} checks, {len(R) - len(fails)} pass, {len(fails)} fail. Built by `py/audit_w18.py` from the raw sources "
     "(team workbook, W14 plots, model plots, W14 boundaries); nothing imported from the scripts it checks.", "",
     "| | check | result | detail |", "|---|---|---|---|"] + [f"| {a} | {b} | {'pass' if c else '**FAIL**'} | {d} |" for a, b, c, d in R]
open(os.path.join(LD, "audit.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"\n{len(R)} checks, {len(fails)} fail")
sys.exit(1 if fails else 0)
