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
                pure_home_plots=int((built & (p.DERIVED == "Residential") & (p.HIGH == 0) & (p.G_DOM > 0)).sum()))


# ------------------------------------------------------------ settlements
@lru_cache(None)
def settlement_table():
    """One row per settlement, largest first: the numbers the report tables use."""
    st = settlements(); oc = occupancy(); g = growth()["Settlements"]
    rows = []
    for s in oc.sort_values("workbook_2024", ascending=False).index:
        sat = g.at[s, "saturation_year"] if s in g.index else None
        rows.append(dict(
            key=s, name=NAME.get(s, s.title()),
            properties=int(oc.at[s, "properties"]), workbook_2024=float(oc.at[s, "workbook_2024"]),
            or_raw=float(oc.at[s, "OR_raw"]), or_used=float(st.at[s, "OR_S"]),
            people_today=float(st.at[s, "POP_TODAY"]),
            ratio=float(st.at[s, "PROPS_PER_BUILT_PLOT"]), home_share=float(st.at[s, "HOME_SHARE"]),
            home_plots=int(st.at[s, "DOM_PLOTS_BUILT"]),
            cap_plots=int(st.at[s, "FUT_CAP_PLOTS"]), cap_people=float(st.at[s, "FUT_CAP_POP"]),
            sat_year=int(sat) if sat == sat and sat else None,
            pop_2030=float(g.at[s, "pop_2030"]), pop_2055=float(g.at[s, "pop_2055"]),
            q_2030=float(g.at[s, "Qadf_2030"]), q_2055=float(g.at[s, "Qadf_2055"]),
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
        for v in r.iloc[1:-1]:
            cells.append("" if v != v or v is None else (f"{v:,.0f}"))
        sat = r.iloc[-1]
        out.append([name] + cells + ["" if sat != sat else f"{int(sat)}"])
    return list(df.columns), out


def map_boxes():
    """The data-box rows of every map figure, written to img/map_boxes.json for
    the QGIS side, which has no pandas. Numbers come from the same functions
    the text uses."""
    import json
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
                        ["Sewage from the estates", f"{ps['s_spec']:,.0f} m3/d"]],
        "M09_saturation": [["Saturation year", str(t["ultimate"])], ["People at saturation", fmt(t["pop_ult"])],
                           ["Sewage at saturation", f"{t['q_ult']:,.0f} m3/d"], [f"People, {BASE_YEAR}", fmt(t["pop_today"])],
                           ["Capacity of the empty plots", fmt(t["capacity"])], ["Ibri full", str(ib["sat_year"])]],
    }
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
