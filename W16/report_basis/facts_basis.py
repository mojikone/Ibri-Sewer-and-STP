"""Facts for the Design Basis Report (W16), on top of the concept report's facts_w14.

Everything the basis report quotes that the concept report did not already compute
is derived here, once, from the same W14 outputs: the flows without the overflow, the
plant flows by year, the process loads, the free meters, the self-cleansing curve.
Nothing is typed in by hand except the guideline constants, each cited.
"""
import math
import os
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(os.path.dirname(HERE), "report")
sys.path.insert(0, REPORT)
import facts_w14 as F  # noqa: E402

fmt = F.fmt

# ------------------------------------------------------------- constants, cited
OPEN_YEAR = 2030            # TOR: the construction year or 2030
CONNECT_2030 = 0.61         # Inception Report R0 connection ratio, reached by 2028
INFIL_LD_KM = 720.0         # G201 p72 §7.4.3, new networks
MARGIN = 0.10               # G201 p73 §7.4.5, new STPs
MERRIMACK_PROPS = 100       # G201 p71 §7.4.2, "over 100 properties"
PF_CAP = 5.0                # G201 p72, a recommendation
TAU_PA = 1.0                # concept-stage tractive tension, engineer 2026-09-11; not in G203
K_MARA = 2.33e-4            # G203 p27, Q in m3/s
Q_FLOOR_LS = 1.5            # the design floor for the tractive check, engineer 2026-09-12, for NWS
V_MIN, V_PREF, V_MAX = 0.75, 0.90, 3.0         # G203 p26, p27
TABLE11 = {200: 5.00, 250: 3.75, 315: 2.70, 400: 2.05, 500: 1.55, 600: 1.25, 700: 1.00, 800: 0.85, 900: 0.75}  # G203 p29, mm/m
STEP_SECONDARY, STEP_TRUNK = 0.05, 0.025       # per cent; engineer 2026-09-11
DEPTH_MAX = 12.0            # m of cover, project rule 2026-09-07 (G203 p33 recommends 10 to 12)
COVER_MIN = 1.3             # m, G203 (1.5 m in a wadi)
RM_V_MIN, RM_V_INT, RM_V_MAX = 0.75, 1.0, 2.5  # rising main, G203 p50 §8.1
BOD_GPCD, TSS_GPCD = 60.0, 80.0                # G203 p74 §10.3.1, "at least"
TABLE30 = {"BOD5": (350, 400), "COD": (700, 900), "TSS": (400, 500), "Ammonia as N": (40, 50),
           "TKN": (60, 80), "Fat, oil and grease": (50, 100), "Total phosphorus": (10, 15)}   # G203 p67, mg/l
TABLE31 = {"BOD5": (350, 1050), "COD": (1350, 5000), "TKN": (115, 265), "TSS": (900, 4300)}  # G203 p68, tankers
PF_BOD_LARGE, PF_TKN_LARGE = 1.2, 1.5          # G203 p74, medium and large STPs
TSE_RATIO, TSE_LOSS = 0.95, 0.10               # G201 p73 §7.4.6.1; p76 §7.4.6.3 b
Q_PER_CAP_LD = 164.0 * (0.85 + 0.22 * 0.54 + 0.14 * 0.54)   # 171.3 l/d per person on a future plot
LS = 86.4                   # m3/d per l/s


# ------------------------------------------------------------------ formulae
def merrimack(q_m3d):
    """Peak flow, m3/d, G201 p71: Qpdf = 2.65 Qadf^0.879, both in Ml/d."""
    return 2.65 * (q_m3d / 1000.0) ** 0.879 * 1000.0


def peltier_pf(q_m3d):
    """Peak factor, G201 p72: 1.5 + 1/sqrt(Qm), Qm in l/s."""
    qm = q_m3d / LS
    return 1.5 + 1.0 / math.sqrt(qm) if qm > 0 else float("inf")


def mara_smin_pct(q_ls, tau=TAU_PA):
    """Minimum gradient by tractive force, per cent: Smin = K tau^1.23 Q^-0.461, Q in m3/s (G203 p27)."""
    q = q_ls / 1000.0
    return K_MARA * tau ** 1.23 * q ** -0.461 * 100.0


def flow_at_gradient(s_pct, tau=TAU_PA):
    """The flow, l/s, at which the tractive minimum equals a gradient (the inverse of mara_smin_pct)."""
    return (K_MARA * tau ** 1.23 / (s_pct / 100.0)) ** (1 / 0.461) * 1000.0


# ------------------------------------------------------------- the years
@lru_cache(None)
def years():
    t = F.totals()
    return (F.BASE_YEAR, OPEN_YEAR, 2055, t["ultimate"])


@lru_cache(None)
def plant_flows():
    """The flows at one works for the whole area, by year: average from the plots, the
    Merrimack peak, both with the margin; infiltration stated per km (T04 chapter 9.11 and 18)."""
    t = F.totals()
    out = {}
    for y in years():
        q = float(t["q"][y]); pk = merrimack(q)
        out[y] = dict(people=float(t["pop"][y]), qadf=q, pf=pk / q, qpdf=pk,
                      aaf=q * (1 + MARGIN), phf=pk * (1 + MARGIN),
                      peltier_pf=peltier_pf(q), low=q * CONNECT_2030 if y == OPEN_YEAR else None)
    out["infil_per_km"] = INFIL_LD_KM / 1000.0 * (1 + MARGIN)     # m3/d per km, with the margin
    return out


@lru_cache(None)
def process_loads():
    """Organic loads at the works by year from the per-capita minima of G203 p74, with
    the concentration they imply at the flow of the same year, against Table 30."""
    t = F.totals(); out = {}
    for y in years():
        people = float(t["pop"][y]); q = float(t["q"][y])
        bod = people * BOD_GPCD / 1000.0; tss = people * TSS_GPCD / 1000.0
        out[y] = dict(people=people, q=q, bod_kgd=bod, tss_kgd=tss,
                      bod_mgl=bod / q * 1000.0, tss_mgl=tss / q * 1000.0,
                      bod_peak_kgd=bod * PF_BOD_LARGE)
    return out


@lru_cache(None)
def tse():
    """Treated effluent produced and delivered by year: 95 % of the inflow, less 10 % in the network."""
    pf = plant_flows(); out = {}
    for y in years():
        inflow = pf[y]["aaf"]
        prod = inflow * TSE_RATIO
        out[y] = dict(inflow=inflow, produced=prod, delivered=prod * (1 - TSE_LOSS))
    return out


# ------------------------------------------------------- with and without overflow
@lru_cache(None)
def own_series():
    """The Inception Report growth series per settlement, as a factor on 2024."""
    import openpyxl
    st = F.settlements()
    wb = openpyxl.load_workbook(os.path.join(F.REPO, "_CLIENT", "Ibri Sewer Demand R0 2026 08 03.xlsx"),
                                read_only=True, data_only=True)
    ws = wb["Project Pop Settlements"]; rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]
    yc = {int(h.split()[1]): i for i, h in enumerate(hdr) if h.startswith("Pop ")}
    P = {}
    for r in rows[1:]:
        key = str(r[1]).strip().upper() if r[1] else None
        if key in st.index:
            base = float(r[yc[F.BASE_YEAR]])
            P[key] = {y: float(r[i]) / base for y, i in yc.items()}
    return P


@lru_cache(None)
def no_overflow():
    """Every settlement on its own growth alone, capped at its capacity: people and average
    flow in the design years, beside the same with the overflow. The flow of the new people is
    171.3 l/d each, as in the plot layer."""
    st = F.settlements(); P = own_series(); g = F.growth()
    pop_w = g["Population by year"]; q_w = g["Qadf by year m3d"]
    yrs = years(); rows = []
    tot = {y: dict(pop_own=0.0, q_own=0.0, pop_with=0.0, q_with=0.0) for y in yrs}
    for s in st.sort_values("POP_TODAY", ascending=False).index:
        pop0 = float(st.at[s, "POP_TODAY"]); cap = float(st.at[s, "FUT_CAP_POP"]); q0 = float(st.at[s, "Q_2024"])
        row = dict(key=s, name=F.NAME.get(s, s.title()), capacity=cap, pop0=pop0)
        for y in yrs:
            own = min(pop0 * P[s][y], pop0 + cap)
            q_own = q0 + (own - pop0) * Q_PER_CAP_LD / 1000.0
            withp = float(pop_w.at[s, str(y)]) if str(y) in pop_w.columns else float(pop_w.at[s, y])
            withq = float(q_w.at[s, str(y)]) if str(y) in q_w.columns else float(q_w.at[s, y])
            row[y] = dict(pop_own=own, q_own=q_own, pop_with=withp, q_with=withq)
            for k in ("pop_own", "q_own", "pop_with", "q_with"):
                tot[y][k] += row[y][k]
        full_own = next((yy for yy in range(F.BASE_YEAR, 2101) if pop0 * (P[s][yy] - 1) >= cap), None)
        row["full_own"] = full_own
        sat = g["Settlements"].at[s, "saturation_year"]
        row["full_with"] = int(sat) if sat == sat else None
        rows.append(row)
    return dict(rows=rows, totals=tot, never=[r["name"] for r in rows if r["full_own"] is None])


def series_totals(to_year=None):
    """Study-area people by year, with the overflow and without, for the chart."""
    st = F.settlements(); P = own_series(); g = F.growth(); pop_w = g["Population by year"]
    ult = F.totals()["ultimate"]; to_year = to_year or ult
    out = []
    for y in range(F.BASE_YEAR, to_year + 1):
        own = sum(min(float(st.at[s, "POP_TODAY"]) * P[s][y], float(st.at[s, "POP_TODAY"]) + float(st.at[s, "FUT_CAP_POP"])) for s in st.index)
        col = str(y) if str(y) in pop_w.columns else y
        withp = float(pop_w[col].sum())
        out.append((y, own, withp))
    return out


# ------------------------------------------------------------- the free meters
@lru_cache(None)
def free_meters():
    """The meters more than 15 m from any plot: where they are, what they are."""
    m = F.meters()
    free = m[m.PLACE == "free"].copy()
    free["x"] = free.geometry.x; free["y"] = free.geometry.y
    by_settle = free.SETTLE.value_counts().to_dict()
    by_tariff = free.TARIFF.value_counts().to_dict()
    dom = int((free.PROPERTY == 1).sum())
    # people they would carry at their settlement's occupancy
    oc = F.settlements()["OR_S"]
    people = float(sum(oc.get(s, 4.0) for s in free.loc[free.PROPERTY == 1, "SETTLE"]))
    return dict(count=len(free), domestic=dom, people=people, by_settle=by_settle, by_tariff=by_tariff,
                rows=[dict(settle=F.NAME.get(r.SETTLE, str(r.SETTLE).title()), tariff=r.TARIFF, gud=r.GUD,
                           domestic=int(r.PROPERTY == 1), x=float(r.x), y=float(r.y)) for r in free.itertuples()])


# ------------------------------------------------------------- the pipe rules
def table11_points(tau=TAU_PA):
    """Where each size's Table 11 minimum meets the tractive curve: the flow, l/s, at which a
    pipe laid at Table 11 passes the tractive test."""
    return {dn: flow_at_gradient(s / 10.0, tau) for dn, s in TABLE11.items()}


if __name__ == "__main__":
    pf = plant_flows()
    for y in years():
        print(y, {k: round(v, 3) if isinstance(v, float) else v for k, v in pf[y].items()})
    print("infiltration with margin, m3/d per km:", round(pf["infil_per_km"], 3))
    pl = process_loads()
    for y in years():
        print(y, "BOD kg/d", round(pl[y]["bod_kgd"]), "TSS", round(pl[y]["tss_kgd"]), "mg/l", round(pl[y]["bod_mgl"]), round(pl[y]["tss_mgl"]))
    no = no_overflow()
    for y in years():
        print(y, {k: round(v) for k, v in no["totals"][y].items()})
    print("never fill on own growth:", no["never"])
    fm = free_meters(); print("free", fm["count"], "domestic", fm["domestic"], "people", round(fm["people"]), fm["by_settle"])
    print("floor 1.5 l/s ->", round(mara_smin_pct(Q_FLOOR_LS), 3), "% ; table 11 meets:", {k: round(v, 2) for k, v in table11_points().items()})


# ------------------------------------------------------------- the map data boxes
def boxes():
    """The data-box rows of every basis map, written to img/basis_boxes.json for the
    QGIS side (no pandas there). The concept maps' boxes are refreshed too."""
    import json
    F.map_boxes()                     # W16/report/img/map_boxes.json and routes.json
    ps = F.plot_summary(); t = F.totals(); pf = plant_flows(); fm = free_meters()
    cls = ps["classes"]
    out = {
        "B01_boundaries": [["Settlements", "25"], ["Boundaries received", "drawn round the built cores"],
                           ["Redrawn", "as a partition, no gaps"], ["Plots assigned", fmt(ps["total"])],
                           ["Corrected", "Tanam, Satwah, Al Makhtibyah, Bat"]],
        "B02_landuse": [["Built plots with meters", fmt(ps["metered"])], ["Homes", fmt(cls.get("Residential", 0))],
                        ["Shops", fmt(cls.get("Commercial", 0))], ["Home and shop", fmt(cls.get("Residential-Commercial", 0))],
                        ["Government", fmt(cls.get("Government", 0))], ["Farms", fmt(cls.get("Agricultural", 0))],
                        ["Industrial", fmt(cls.get("Industrial", 0))], ["Heritage", fmt(ps["heritage"])],
                        ["Empty", fmt(ps["empty"])]],
        "B03_saturation": [["1  Add the settlements in the catchment", "m³/d"],
                           ["2  Add infiltration", f"{INFIL_LD_KM / 1000:.2f} m³/d per km of sewer"],
                           ["3  Add the plant margin", f"× {1 + MARGIN:.2f}  (the design average)"],
                           ["4  Peak hour", "2.65 × (average in Ml/d)^0.879, Ml/d"],
                           [f"Whole area, {t['ultimate']}: average", f"{fmt(t['q_ult'])} → {fmt(pf[t['ultimate']]['aaf'])} m³/d"],
                           [f"Whole area, {t['ultimate']}: peak hour", f"{fmt(pf[t['ultimate']]['phf'])} m³/d"]],
        "B05_free_meters": [["Meters more than 15 m from any plot", fmt(fm["count"])], ["of which dwelling meters", fmt(fm["domestic"])],
                            ["People they would carry", fmt(fm["people"])],
                            ["Government and commercial meters", fmt(fm["by_tariff"].get("Government", 0) + fm["by_tariff"].get("Commercial", 0))],
                            ["Zoom panels", "68, in the appendix"]],
    }
    path = os.path.join(HERE, "img", "basis_boxes.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return path
