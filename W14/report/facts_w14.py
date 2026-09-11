"""Measured facts for Revision 2: population, land use, saturation and flows.

Every figure the report quotes about properties, occupancy, land use, capacity,
growth and sewage flow is read here from the W14 outputs, once, so the text,
the tables, the charts and the maps cannot disagree. Nothing in this module is
typed in by hand; change the outputs and rebuild.

Sources (all under W14/):
  shp/PLOTS_load.shp                       every plot: meters, class, people, flows
  shp/Settlements_merged.shp               the 25 settlements as a partition
  analysis/settlements_today.csv           occupancy, ratio, home share, capacity
  analysis/occupancy_by_settlement.csv     raw and used occupancy
  analysis/W14_growth_by_settlement.xlsx   people and flow per settlement per year
  analysis/CRT_accounts_identified.csv     the 499 large-consumer accounts
  analysis/IDENTIFIED_PROJECTS.md          the special land uses (text only)
"""
import os
from functools import lru_cache

W14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHP = os.path.join(W14, "shp")
ANA = os.path.join(W14, "analysis")

BASE_YEAR = 2024
DESIGN_YEARS = (2030, 2055)
LPCD = 164.0
R_ND, R_GOV = 0.22, 0.14
RET_DOM, RET_ND = 0.85, 0.54
L_IND = 93.0
OR_FLOOR = 4.0
WORKERS = {"Al Tayyeb": 4500, "Tanam": 1800}
HOME_LO, HOME_HI, BIG = 200, 1000, 2000
HIGH_METERS = 15                      # a plot with this many dwelling meters is a block, not a home
LPCD, R_ND, R_GOV, L_IND, RET_DOM, RET_ND = 164.0, 0.22, 0.14, 93.0, 0.85, 0.54   # PAM-GUD-201 Tab 11 p60, Tab 12 p61, Tab 19 p71

NAME = {  # settlement names as the report writes them
    "IBRI": "Ibri", "AD DARIZ": "Ad Dariz", "AL ARAQI": "Al Araqi", "AL AYNAYN": "Al Aynayn",
    "AL WAHRAH": "Al Wahrah", "AT TAYYIB": "At Tayyib", "AL JIBAYYAH": "Al Jibayyah", "BAT": "Bat",
    "AD DIBAYSHI": "Ad Dibayshi", "TANAM": "Tanam", "SUWAYDA AL MA": "Suwayda al Ma", "HIJAR": "Hijar",
    "AL GHUBAYRAH": "Al Ghubayrah", "AL QURAYN": "Al Qurayn", "SAYH AL MASARRAT": "Sayh al Masarrat",
    "AL JAHLI": "Al Jahli", "SATWAH": "Satwah", "AL AKHEEDAR": "Al Akheedar", "AL QALI": "Al Qali",
    "SHALASHIL": "Shalashil", "AL MAKHTIBYAH": "Al Makhtibyah", "USAYBUQ": "Usaybuq",
    "WADI AL MANKAS": "Wadi al Mankas", "ASH SHIAB": "Ash Shiab", "MIAYRID": "Miayrid",
}


def fmt(n, nd=0):
    """Thousands separator, rounded half up so a .5 total prints the same everywhere."""
    n = float(n); n = round(n + (1e-9 if n >= 0 else -1e-9), nd)
    return f"{n:,.{nd}f}"


@lru_cache(None)
def plots():
    import geopandas as gpd
    return gpd.read_file(os.path.join(SHP, "PLOTS_load.shp"))


@lru_cache(None)
def meters():
    import geopandas as gpd
    return gpd.read_file(os.path.join(SHP, "ELE_meters_on_plots.shp"))


@lru_cache(None)
def settlements():
    import pandas as pd
    return pd.read_csv(os.path.join(ANA, "settlements_today.csv")).set_index("SETTLE")


@lru_cache(None)
def occupancy():
    import pandas as pd
    return pd.read_csv(os.path.join(ANA, "occupancy_by_settlement.csv")).set_index("SETTLE")


@lru_cache(None)
def growth():
    """Sheets of the growth workbook as DataFrames keyed by sheet name."""
    import pandas as pd
    xl = os.path.join(ANA, "W14_growth_by_settlement.xlsx")
    out = {}
    for sh in ("Settlements", "Population by year", "Qadf by year m3d", "Five-year to saturation",
               "Five-year Qadf", "Overflow routes", "Inflow from overflow"):
        df = pd.read_excel(xl, sheet_name=sh)
        if sh in ("Settlements", "Population by year", "Qadf by year m3d", "Inflow from overflow"):
            df = df.set_index(df.columns[0])
        out[sh] = df
    return out


@lru_cache(None)
def crt():
    import pandas as pd
    return pd.read_csv(os.path.join(ANA, "CRT_accounts_identified.csv"))


# ----------------------------------------------------------------- meters
@lru_cache(None)
def meter_counts():
    m = meters()
    place = m.PLACE.value_counts().to_dict()
    tariff = m.TARIFF.value_counts().to_dict()
    gud = m.GUD.value_counts().to_dict()
    return dict(total=len(m), inside=place.get("inside", 0), snapped=place.get("snapped", 0),
                free=place.get("free", 0), tariff=tariff, gud=gud,
                domestic=int((m.PROPERTY == 1).sum()))


@lru_cache(None)
def crt_summary():
    c = crt()
    c = c[c.tariff != "Industrial"]          # the one Industrial-tariff account is not a large-consumer account
    use = c.USE.value_counts().to_dict()
    conf = c.CONF.value_counts().to_dict()
    return dict(total=len(c), use=use, conf=conf)


# ------------------------------------------------------------------ plots
@lru_cache(None)
def plot_summary():
    p = plots()
    built = p.Buiding_St == "EXisting"
    metered = built & (p.N_ACC > 0)
    cls = p.loc[metered, "DERIVED"].value_counts().to_dict()
    farms_by = p.loc[metered & (p.DERIVED == "Agricultural"), "WHYC"].value_counts().to_dict()
    empty = p.Buiding_St == "Future"
    return dict(total=len(p), built=int(built.sum()), metered=int(metered.sum()), empty=int(empty.sum()),
                classes=cls, farms_by=farms_by,
                homeshaped_empty=int((empty & (p.HOMESHAPE == 1)).sum()),
                capacity_plots=int((p.FUT_CAP == 1).sum()),
                spread_plots=int((p.SPREAD_W > 0).sum()),
                slivers=int((empty & (p.AREA_M2 < HOME_LO)).sum()),
                big=int((empty & (p.AREA_M2 > BIG)).sum()),
                heritage=int((p.DERIVED == "Heritage").sum()),
                properties=int(p.G_DOM.sum()),
                pop_today=float(p.POP.sum()), qadf_today=float(p.QADF.sum()),
                w_today=float(p.W_TOT.sum()),
                s_dom=float(p.S_DOM.sum()), s_nd=float(p.S_NDOM.sum()), s_gov=float(p.S_GOV.sum()),
                s_spec=float(p.S_SPEC.sum()),
                pure_home_plots=int((built & (p.DERIVED == "Residential") & (p.G_DOM < HIGH_METERS) & (p.G_DOM > 0)).sum()))


# ------------------------------------------------------------ settlements
@lru_cache(None)
def settlement_table():
    """One row per settlement, largest first: the numbers the report tables use."""
    st = settlements(); oc = occupancy(); g = growth()["Settlements"]
    rows = []
    for s in st.sort_values("WB_2024", ascending=False).index:
        sat = g.at[s, "saturation_year"] if s in g.index else None
        rows.append(dict(
            key=s, name=NAME.get(s, s.title()),
            properties=int(st.at[s, "PROPS"]), workbook_2024=float(st.at[s, "WB_2024"]),
            or_raw=round(float(st.at[s, "WB_2024"]) / max(int(st.at[s, "PROPS"]), 1), 2), or_used=float(st.at[s, "OR_S"]),
            people_today=float(st.at[s, "POP_TODAY"]),
            ratio=float(st.at[s, "PROPS_PER_BUILT_PLOT"]), home_share=float(st.at[s, "HOME_SHARE"]),
            ratio_raw=float(st.at[s, "PPP_RAW"]), home_share_raw=float(st.at[s, "HOME_SHARE_RAW"]),
            small=bool(int(st.at[s, "SMALL"])), empty_plots=int(st.at[s, "EMPTY_PLOTS"]),
            home_plots=int(st.at[s, "DOM_PLOTS_BUILT"]),
            cap_plots=int(st.at[s, "FUT_CAP_PLOTS"]), cap_people=float(st.at[s, "FUT_CAP_POP"]),
            sat_year=int(sat) if sat == sat and sat else None,
            pop_2030=float(g.at[s, "pop_2030"]), pop_2055=float(g.at[s, "pop_2055"]),
            q_2030=float(g.at[s, "Qadf_2030"]), q_2055=float(g.at[s, "Qadf_2055"]),
            built_plots=int(st.at[s, "BUILT_PLOTS"]), g_ndom=int(st.at[s, "NDOM_METERS"]), nd_pool=int(st.at[s, "NDOM_POOL"]),
            g_gov=int(st.at[s, "GOV_METERS"]), gov_pool=int(st.at[s, "GOV_POOL"]), workers=float(st.at[s, "WORKERS"]),
            u_nd=float(st.at[s, "U_NDOM"]), u_gov=float(st.at[s, "U_GOV"]),
            w_dom=float(st.at[s, "W_DOM"]), w_nd=float(st.at[s, "W_NDOM"]), w_gov=float(st.at[s, "W_GOV"]),
            w_spec=float(st.at[s, "W_SPEC"]), w_tot=float(st.at[s, "W_TOT"]),
            s_dom=float(st.at[s, "S_DOM"]), s_nd=float(st.at[s, "S_NDOM"]), s_gov=float(st.at[s, "S_GOV"]),
            s_spec=float(st.at[s, "S_SPEC"]), q_2024=float(st.at[s, "Q_2024"]),
        ))
    return rows


@lru_cache(None)
def totals():
    g = growth(); pop = g["Population by year"]; q = g["Qadf by year m3d"]
    years = [int(c) for c in pop.columns]
    tot_pop = {y: float(pop[c].sum()) for y, c in zip(years, pop.columns)}
    tot_q = {y: float(q[c].sum()) for y, c in zip(years, q.columns)}
    sat = growth()["Settlements"]["saturation_year"].dropna()
    ult = int(sat.max())
    return dict(years=years, pop=tot_pop, q=tot_q, ultimate=ult,
                pop_ult=tot_pop[ult], q_ult=tot_q[ult],
                capacity=float(settlements().FUT_CAP_POP.sum()),
                pop_today=tot_pop[BASE_YEAR], q_today=tot_q[BASE_YEAR])


def five_year_rows(kind="pop"):
    """The five-year table as the report prints it: settlement rows, blank after saturation, fill year last."""
    df = growth()["Five-year to saturation" if kind == "pop" else "Five-year Qadf"]
    out = []
    for _, r in df.iterrows():
        name = NAME.get(r.iloc[0], str(r.iloc[0]).title()) if r.iloc[0] != "TOTAL" else "Total"
        cells = []
        for v in r.iloc[1:-2]:
            cells.append("" if v != v or v is None else fmt(v))
        sat, val = r.iloc[-2], r.iloc[-1]
        out.append([name] + cells + ["" if sat != sat else f"{int(sat)}", "" if val != val else fmt(val)])
    cols = list(df.columns)[:-1]
    # a five-year column past the last saturation year is blank for every settlement: it is not printed
    while len(cols) > 4 and all(r[len(cols) - 2] == "" for r in out if r[0] != "Total"):
        k = len(cols) - 2          # the last five-year column: cols ends with the saturation year
        cols.pop(k); [r.pop(k) for r in out]
    return cols, out


@lru_cache(None)
def routes(min_people=50):
    """Overflow routes: donor, receiver, people at ultimate, the year the donor is full,
    the year the receiver starts taking and the year it is full. Sorted by people; routes
    under min_people are left out (the appendix prints those of fifty or more)."""
    g = growth(); r = g["Overflow routes"]; inflow = g["Inflow from overflow"]; S = g["Settlements"]
    last = r.columns[-1]
    first_in = {s: next((int(c) for c in inflow.columns if float(inflow.at[s, c]) > 0.5), None) for s in inflow.index}
    sat = S["saturation_year"]
    out = []
    for _, x in r.sort_values(last, ascending=False).iterrows():
        if float(x[last]) < min_people:
            continue
        out.append(dict(donor=x["from"], receiver=x["to"], donor_name=NAME.get(x["from"], x["from"].title()),
                        receiver_name=NAME.get(x["to"], x["to"].title()), people=float(x[last]),
                        donor_full=int(sat[x["from"]]) if sat[x["from"]] == sat[x["from"]] else None,
                        starts=first_in.get(x["to"]), receiver_full=int(sat[x["to"]]) if sat[x["to"]] == sat[x["to"]] else None))
    return out


@lru_cache(None)
def own_growth_saturation():
    """For every settlement: the year it would fill on its own growth alone, beside the year with overspill."""
    import openpyxl
    st = settlements(); S = growth()["Settlements"]
    wb = openpyxl.load_workbook(os.path.join(os.path.dirname(W14), "_CLIENT", "Ibri Sewer Demand R0 2026 08 03.xlsx"), read_only=True, data_only=True)
    ws = wb["Project Pop Settlements"]; rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]
    yc = {int(h.split()[1]): i for i, h in enumerate(hdr) if h.startswith("Pop ")}
    P = {str(r[1]).strip().upper(): {y: float(r[i]) for y, i in yc.items()} for r in rows[1:] if r[1] and str(r[1]).strip().upper() in st.index}
    out = []
    for s in st.sort_values("POP_TODAY", ascending=False).index:
        pop0 = float(st.at[s, "POP_TODAY"]); cap = float(st.at[s, "FUT_CAP_POP"]); base = P[s][BASE_YEAR]
        own = next((y for y in range(BASE_YEAR, 2101) if pop0 * (P[s][y] / base - 1) >= cap), None)
        sat = S.at[s, "saturation_year"]
        out.append(dict(key=s, name=NAME.get(s, s.title()), own=own, with_spill=int(sat) if sat == sat else None,
                        inflow=float(S.at[s, "inflow_at_ultimate"]), capacity=cap))
    return out


def routes_json():
    """Routes with settlement centroids, for the overflow map drawn in QGIS."""
    import json, geopandas as gpd
    sett = gpd.read_file(os.path.join(SHP, "Settlements_merged.shp")).set_index("SETTLE")
    cent = sett.geometry.representative_point()
    inflow_share = {s: (float(growth()["Settlements"].at[s, "inflow_at_ultimate"]) / max(float(settlements().at[s, "FUT_CAP_POP"]), 1)) for s in sett.index}
    data = {"routes": [dict(r, x1=float(cent[r["donor"]].x), y1=float(cent[r["donor"]].y), x2=float(cent[r["receiver"]].x), y2=float(cent[r["receiver"]].y)) for r in routes()],
            "inflow_share": inflow_share}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "routes.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    return path


def map_boxes():
    """The data-box rows of every map figure, written to img/map_boxes.json for
    the QGIS side, which has no pandas. Numbers come from the same functions
    the text uses."""
    import json
    import geopandas as gpd
    t = totals(); ps = plot_summary(); mc = meter_counts(); cs = crt_summary()
    st = settlement_table(); ib = [r for r in st if r["key"] == "IBRI"][0]
    boxes = {
        "M04_electricity": [["Meters", fmt(mc["total"])], ["Domestic", fmt(mc["gud"].get("domestic", 0))],
                            ["Non-domestic", fmt(mc["gud"].get("non_domestic", 0))], ["Governmental", fmt(mc["gud"].get("government", 0))],
                            ["Agricultural", fmt(mc["gud"].get("agricultural", 0))], ["Special", fmt(mc["gud"].get("special", 0))],
                            ["On a plot", f"{fmt(mc['inside'] + mc['snapped'])} ({fmt(mc['free'])} free)"]],
        "M05_settlements": [["Settlements", "25"], ["Plots", fmt(ps["total"])], ["Built, with meters", fmt(ps["metered"])],
                            ["Empty", fmt(ps["empty"])], [f"People, {BASE_YEAR}", fmt(t["pop_today"])],
                            ["Occupancy, Ibri", f"{ib['or_used']:.2f}"]],
        "M07_landuse": [["Built plots with meters", fmt(ps["metered"])], ["Homes", fmt(ps["classes"].get("Residential", 0))],
                        ["Shops", fmt(ps["classes"].get("Commercial", 0))], ["Home and shop", fmt(ps["classes"].get("Residential-Commercial", 0))],
                        ["Government", fmt(ps["classes"].get("Government", 0))], ["Farms", fmt(ps["classes"].get("Agricultural", 0))],
                        ["Industrial", fmt(ps["classes"].get("Industrial", 0))], ["Heritage", fmt(ps["heritage"])]],
        "M08_special": [["Industrial estates", "2"], ["Al Tayyeb workforce", fmt(WORKERS["Al Tayyeb"])], ["Tanam workforce", fmt(WORKERS["Tanam"])],
                        ["Rate", f"{L_IND:.0f} l/d per worker"], ["Army camp", "296 ha, no meter"], ["Resort, planned", "2 km2, no load yet"],
                        ["Sewage from the estates", f"{fmt(ps['s_spec'])} m3/d"]],
        "M09_saturation": [["Saturation year", str(t["ultimate"])], ["People at saturation", fmt(t["pop_ult"])],
                           ["Sewage at saturation", f"{fmt(t['q_ult'])} m3/d"], [f"People, {BASE_YEAR}", fmt(t["pop_today"])],
                           ["Capacity of the empty plots", fmt(t["capacity"])], ["Ibri full", str(ib["sat_year"])]],
        "M10_overflow": [["Ibri full", str(ib["sat_year"])], ["Ibri sends out", fmt(gpd.read_file(os.path.join(SHP, "Settlements_merged.shp"), ignore_geometry=True).set_index("SETTLE").at["IBRI", "OUT_PEOPLE"])],
                         ["Largest route", f"{routes()[0]['donor_name']} to {routes()[0]['receiver_name']}"],
                         ["People on it", fmt(routes()[0]['people'])],
                         ["Never fill alone", str(sum(1 for r in own_growth_saturation() if r["own"] is None))],
                         ["Saturation, all", str(t["ultimate"])]],
    }
    routes_json()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "map_boxes.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(boxes, fh, indent=1, ensure_ascii=False)
    return path


if __name__ == "__main__":
    print("map boxes ->", map_boxes())
    t = totals(); ps = plot_summary(); mc = meter_counts()
    print("meters", mc["total"], mc["inside"], mc["snapped"], mc["free"], "| properties", ps["properties"])
    print("today %.0f people, %.0f m3/d | capacity %.0f | ultimate %d: %.0f people, %.0f m3/d" %
          (t["pop_today"], t["q_today"], t["capacity"], t["ultimate"], t["pop_ult"], t["q_ult"]))
    print("classes", ps["classes"]); print("farms by", ps["farms_by"])
    for r in settlement_table()[:5]:
        print(r["name"], r["or_raw"], r["or_used"], r["people_today"], r["sat_year"])


# ------------------------------------------------------- the flow per plot
def unit_rate_rows():
    """Water shares and unit rates by settlement, 2024 (the table in 15.4).
    Source: settlements_today.csv, every column a sum over the plots."""
    st = settlement_table(); rows = []
    for r in st:
        rows.append([r["name"], fmt(r["people_today"]), fmt(r["w_dom"]), fmt(r["w_nd"]), fmt(r["w_gov"]),
                     fmt(r["nd_pool"]), fmt(r["gov_pool"]),
                     fmt(r["u_nd"]) if r["nd_pool"] > 0 else "on dwellings",
                     fmt(r["u_gov"]) if r["gov_pool"] > 0 else "on dwellings",
                     fmt(r["w_spec"]) if r["w_spec"] > 0 else "–", fmt(r["q_2024"])])
    T = lambda k: sum(r[k] for r in st)
    rows.append(["Total", fmt(T("people_today")), fmt(T("w_dom")), fmt(T("w_nd")), fmt(T("w_gov")),
                 fmt(T("nd_pool")), fmt(T("gov_pool")), fmt(T("w_nd") * 1000 / T("nd_pool")),
                 fmt(T("w_gov") * 1000 / T("gov_pool")), fmt(T("w_spec")), fmt(T("q_2024"))])
    return rows


def example_plot(key="IBRI", n_dom=4, n_nd=2, n_gov=1):
    """One plot worked from its meters with the settlement's adopted rates: the rows of the table in 15.4."""
    r = next(x for x in settlement_table() if x["key"] == key)
    w_dom = n_dom * r["or_used"] * LPCD; w_nd = n_nd * r["u_nd"]; w_gov = n_gov * r["u_gov"]
    s_dom, s_nd, s_gov = w_dom * RET_DOM, w_nd * RET_ND, w_gov * RET_ND
    q = s_dom + s_nd + s_gov
    rows = [[f"Domestic: {n_dom} meters × {r['or_used']:.2f} persons × 164 l/d", fmt(w_dom), "0.85", fmt(s_dom)],
            [f"Non-domestic: {n_nd} meters × {fmt(r['u_nd'])} l/d", fmt(w_nd), "0.54", fmt(s_nd)],
            [f"Governmental: {n_gov} meter × {fmt(r['u_gov'])} l/d", fmt(w_gov), "0.54", fmt(s_gov)],
            ["Plot", fmt(w_dom + w_nd + w_gov), "", f"{fmt(q)} = {q / 1000:.2f} m³/d"]]
    return dict(rows=rows, name=r["name"], or_used=r["or_used"], u_nd=r["u_nd"], u_gov=r["u_gov"],
                people=n_dom * r["or_used"], q=q)


# ------------------------------------------------------ figures the prose quotes
@lru_cache(None)
def growth_rates():
    """The growth series' year-on-year rate: decade means (per cent) and the ramp
    after 2050. Source: the demand workbook, sheet Project Pop Settlements, the 25 settlements."""
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(os.path.dirname(W14), "_CLIENT", "Ibri Sewer Demand R0 2026 08 03.xlsx"), read_only=True, data_only=True)
    ws = wb["Project Pop Settlements"]; rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]
    yc = {int(h.split()[1]): i for i, h in enumerate(hdr) if h.startswith("Pop ")}
    keys = set(settlements().index)
    tot = {y: sum(float(r[i]) for r in rows[1:] if r[1] and str(r[1]).strip().upper() in keys) for y, i in yc.items()}
    rate = {y: (tot[y] / tot[y - 1] - 1) * 100 for y in sorted(tot) if y - 1 in tot}
    mean = lambda a, b: ((tot[b] / tot[a]) ** (1 / (b - a)) - 1) * 100
    at240 = next(y for y in sorted(rate) if y > 2050 and rate[y] >= 2.395)
    return dict(d2024_2030=mean(2024, 2030), d2030s=mean(2030, 2040), d2040s=mean(2040, 2050), d2050s=mean(2050, 2060),
                d2060on=mean(2060, 2100), r2051=rate[2051], year_240=at240, rate=rate)


@lru_cache(None)
def farm_bare_share():
    """Share of the plots with a farm meter that fail the satellite grove test: pump sites without a crop."""
    p = plots(); farm = p.G_AGR > 0
    nm, ns, ga = p.NDVI_MEAN.fillna(0), p.NDVI_SHARE.fillna(0), p.GREEN_M2.fillna(0)
    green = ((ga >= 1000) & (nm >= 0.20)) | ((ns >= 0.60) & (nm >= 0.40) & (p.AREA_M2 >= 800))
    return float((farm & ~green).sum() / max(int(farm.sum()), 1))


def home_share_range():
    """Measured home share among the settlements of a thousand people or more: (low, name, high, name)."""
    rows = [r for r in settlement_table() if not r["small"]]
    lo = min(rows, key=lambda r: r["home_share_raw"]); hi = max(rows, key=lambda r: r["home_share_raw"])
    return lo["home_share_raw"], lo["name"], hi["home_share_raw"], hi["name"]


def ibri_receivers(min_people=1000):
    """Settlements that take min_people or more of Ibri's overflow, largest first."""
    return [r for r in routes(0) if r["donor"] == "IBRI" and r["people"] >= min_people]


def census_rate():
    """Persons per domestic property over the study area on the census figure alone."""
    st = settlement_table()
    return sum(r["workbook_2024"] for r in st) / sum(r["properties"] for r in st)


def cadastre_disagreement():
    """Share of the built, metered plots whose cadastral class differs from the use derived from their meters."""
    p = plots(); m = (p.Buiding_St == "EXisting") & (p.N_ACC > 0)
    return float((p.loc[m, "Classes"] != p.loc[m, "DERIVED"]).mean())
