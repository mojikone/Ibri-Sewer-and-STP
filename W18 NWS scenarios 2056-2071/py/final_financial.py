"""W18 final design: treatment capacity and phasing, treated effluent supply, and the CAPEX / OPEX of the four scenarios by
the method of the team's options cost estimate (October 2026, sheets 'STP - CAPEX', 'OPEX', 'Capex/Opex Per Years'),
on the flows of the final design (each plant's average inflow with infiltration, 2056 design).

  Treatment: design capacity = 2056 average inflow + 10 %; four equal modules per plant, rounded up to 500 m3/d (250 below
             5,000); the modules installed in 2031 cover the 2031 inflow + 10 %, a further module enters service in the first
             five-year year whose inflow + 10 % exceeds the installed capacity. Rate per m3/d by the plant's design capacity:
             <=1,000 1,000; <=5,000 900; <=10,000 800; <=20,000 700; <=50,000 600; <=100,000 500 OMR. Power 0.025 kW per m3/d of
             capacity; land 8/6/4/3/2/1 m2 per m3/d in the same bands.
  Network:   sewers, manholes, force mains and the pumping and lift stations from network_cost.json (the BOQ at the team's
             rates); the stations' land 5 m2/kW up to 10 kW and 3 m2/kW above, as the team's sheet.
  TE:        SC1-SC3 the team's TE networks and booster power (TE Pipes - CAPEX, BPS 750 / 850 / 497 kW); SC4 the STP-5 network
             of SC3 with the SC2 network from STP-2 reduced to the customers STP-2 supplies (te/SC4_TE_network.gpkg), at the
             team's TE pipe rates; its booster power pro rata to the flow each plant supplies in the SC2 and SC3 models.
             Boosters 5,000 OMR/kW and 3 m2/kW.
  OPEX (team's sheet): maintenance and operation 1 % of the capital in service a year; power = installed kW (boosters,
             sewage stations, plant) x 24 h x 365 x 0.020 OMR/kWh x the year's flow as a share of the design flow; land
             1 OMR/m2 a month; staff (ROUNDUP(stations / 5) x 2 + 20 for one plant, 28 for two) x 2,500 OMR x 13; chemicals
             chlorine 8 g and NaHCO3 20 g per m3 of capacity at 0.3 OMR/kg, polymer as the sheet at 1 OMR/kg, x the flow share.
  Prices: base 2031; capital and operating costs escalated at 5 % a year from 2031 (team's inflation rate). The present
             value at 5 % over 25 years (2031-2055) is given at constant prices.
  TE supply: production 95 % of the plant inflow, 10 % network loss (PAM-GUD-201 7.4.6); customers' demands of the team's
             register (2030 and 2070, linear between), each customer supplied by the plant of the team's TE model.
Usage: python final_financial.py    Writes results/final_0.75pc_SC1-SC4/financial.json and
       report_final/deliverables/Ibri_Treatment_TE_and_Financial_SC1-SC4.xlsx"""
import os, json, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); TE = os.path.join(R, "te")
XLSX = os.path.join(W18, "report_final", "deliverables", "Ibri_Treatment_TE_and_Financial_SC1-SC4.xlsx")
SC = ["SC1", "SC2", "SC3", "SC4"]; Y5 = [2031, 2036, 2041, 2046, 2051, 2056]; YEARS = list(range(2031, 2056))   # 25 years
BASE, INFL, DISC = 2031, 0.05, 0.05
NET = json.load(open(os.path.join(R, "network_cost.json")))
BANDS = [(1000, 1000, 8), (5000, 900, 6), (10000, 800, 4), (20000, 700, 3), (50000, 600, 2), (100000, 500, 1)]
band = lambda cap: next(b for b in BANDS if cap <= b[0])
TE_RATE = {100: 10.2, 150: 14.0, 200: 32.1, 250: 40.7, 300: 49.2, 350: 53.0, 400: 56.8, 500: 73.2, 600: 98.1, 700: 113.3, 800: 128.4, 900: 157.8}
TE_TEAM = {"SC1": dict(cost=4923902.3, km=95.869, kw=750.0, by={100: 6103, 150: 15961, 200: 1586, 250: 28808, 300: 13006, 400: 9455, 500: 6477, 600: 4451, 800: 8652, 900: 1370}),
           "SC2": dict(cost=4609221.5, km=96.051, kw=850.0),
           "SC3": dict(cost=4397593.1, km=92.868, kw=497.0)}
Q_MODEL = dict(S2_stp2=769.72, S3_stp1=717.64, S3_stp5=52.08)       # L/s each plant supplies in the team's TE models


def plants(sc):
    p = pd.read_csv(os.path.join(R, f"{sc}-2056", "products", "plants.csv"))
    return {r.stp: {int(c[4:8]): getattr(r, c) for c in p.columns if c.startswith("avg_")} for r in p.itertuples()}


def at(series, y):
    ys = sorted(series); return float(np.interp(y, ys, [series[k] for k in ys]))


def modules(q):
    cap = q[2056] * 1.1; size = math.ceil(cap / 4 / (500 if cap / 4 >= 5000 else 250)) * (500 if cap / 4 >= 5000 else 250)
    n0 = math.ceil(q[2031] * 1.1 / size); plan = {2031: n0}; n = n0
    for y in Y5[1:]:
        need = math.ceil(q[y] * 1.1 / size)
        if need > n: plan[y] = need - n; n = need
    return dict(design=cap, size=size, n=n, total=n * size, plan=plan, rate=band(n * size)[1], land_per=band(n * size)[2])


out = {}
C = pd.read_csv(os.path.join(TE, "te_customers.csv"))
C["src_sc3"] = C.sc3_source.str.replace(" (no location)", "", regex=False)
dem = lambda df, y: float((df.d2030 + (df.d2070 - df.d2030) * (y - 2030) / 40).sum())
for sc in SC:
    q = plants(sc); stp = {k: modules(v) for k, v in q.items()}
    tot = {y: sum(v[y] for v in q.values()) for y in q[next(iter(q))]}
    st = pd.read_csv(os.path.join(R, f"{sc}-2056", "products", "stations.csv"))
    n_st = int((st.kind != "plant inlet").sum() + (st.kind == "plant inlet").sum())   # every pumping and lift station
    kw_sew = float(st.kw.sum()); small = st[st.kw <= 10].kw.sum(); large = st[st.kw > 10].kw.sum()
    land_st = math.ceil(small * 5 / 100) * 100 + math.ceil(large * 3 / 100) * 100
    # treated effluent network
    if sc in TE_TEAM: te = dict(TE_TEAM[sc])
    else:
        L = pd.read_csv(os.path.join(TE, "SC4_TE_lengths.csv"))
        te = dict(by={int(d): float(l) for d, l in zip(L.D, L.L)}, km=L.L.sum() / 1000, cost=float(sum(TE_RATE[int(d)] * l for d, l in zip(L.D, L.L))),
                  kw=round(TE_TEAM["SC2"]["kw"] * Q_MODEL["S3_stp1"] / Q_MODEL["S2_stp2"] + TE_TEAM["SC3"]["kw"] * Q_MODEL["S3_stp5"] / (Q_MODEL["S3_stp1"] + Q_MODEL["S3_stp5"]), 0))
    land_te = math.ceil(te["kw"] * 3 / 100) * 100
    # supply: which plant supplies each customer
    src = {"SC1": lambda s: "STP-1", "SC2": lambda s: "STP-2", "SC3": lambda s: s, "SC4": lambda s: "STP-2" if s == "STP-1" else s}[sc]
    C["src"] = C.src_sc3.map(src)
    supply = {}
    for p in q:
        cu = C[C.src == p]
        supply[p] = {y: dict(produced=0.95 * at(q[p], y), delivered=0.95 * 0.9 * at(q[p], y), demand=dem(cu, y)) for y in (2031, 2036, 2046, 2056)}
        supply[p]["customers"] = int(len(cu)); supply[p]["demand_2070"] = float(cu.d2070.sum())
    # capital, base prices, by year of expenditure
    capex = {2031: dict(sewers=NET[f"{sc}-2056"]["sewers"], manholes=NET[f"{sc}-2056"]["manholes"], force_mains=NET[f"{sc}-2056"]["force_mains"],
                        stations=NET[f"{sc}-2056"]["stations"], te_mains=te["cost"], te_boosters=te["kw"] * 5000.0, stp=0.0)}
    for p, m in stp.items():
        for y, k in m["plan"].items():
            capex.setdefault(y, dict(stp=0.0))["stp"] = capex.get(y, {}).get("stp", 0.0) + k * m["size"] * m["rate"]
    cap_total = sum(m["total"] for m in stp.values()); kw_stp = 0.025 * cap_total
    land = sum(m["total"] * m["land_per"] for m in stp.values()) + land_st + land_te
    staff = math.ceil(n_st / 5) * 2 + (20 if len(stp) == 1 else 28)
    chem_kgd = dict(chlorine=cap_total * 8 / 1000, nahco3=cap_total * 20 / 1000,
                    polymer=((cap_total * 0.01 * 0.01 * 1005) * 8 + (cap_total * 0.01 * 0.01 * 1005) * 0.95 * 10) / 1000)
    chem = (chem_kgd["chlorine"] * 0.3 + chem_kgd["nahco3"] * 0.3 + chem_kgd["polymer"] * 1.0) * 365
    kw_all = te["kw"] + kw_sew + kw_stp; power_full = kw_all * 24 * 365 * 0.02
    rows = []; in_service = 0.0
    for y in YEARS:
        in_service += sum(capex.get(y, {}).values())
        f = at(tot, y) / tot[2056]; e = (1 + INFL) ** (y - BASE)
        rows.append(dict(year=y, flow_share=f, capex_base=sum(capex.get(y, {}).values()), capex_nominal=sum(capex.get(y, {}).values()) * e,
                         mo=0.01 * in_service * e, power=power_full * f * e, land=land * 12 * e, staff=staff * 2500 * 13 * e, chemicals=chem * f * e,
                         opex_base=0.01 * in_service + power_full * f + land * 12 + staff * 2500 * 13 + chem * f))
    D = pd.DataFrame(rows); D["opex_nominal"] = D[["mo", "power", "land", "staff", "chemicals"]].sum(axis=1)
    disc = (1 + DISC) ** -(D.year - BASE)
    out[sc] = dict(plants={p: dict(q={y: round(at(q[p], y)) for y in Y5 + [2061]}, **{k: v for k, v in m.items()}) for p, m in stp.items()},
                   inflow={y: round(at(tot, y)) for y in Y5 + [2061]}, te=te, supply=supply,
                   capex_by_year={y: {k: round(v) for k, v in c.items()} for y, c in capex.items()},
                   capex_base=float(D.capex_base.sum()), capex_nominal=float(D.capex_nominal.sum()),
                   capex_nominal_by={y: float(D[D.year <= y].capex_nominal.sum()) for y in [2031, 2036, 2041, 2046, 2051, 2055]},
                   opex_first=dict(mo=float(D.mo[0]), power=float(D.power[0]), land=float(D.land[0]), staff=float(D.staff[0]), chemicals=float(D.chemicals[0]), total=float(D.opex_nominal[0])),
                   opex_cum={k: {y: float(D[D.year <= y][k].sum()) for y in [2031, 2036, 2041, 2046, 2051, 2055]} for k in ["mo", "power", "land", "staff", "chemicals", "opex_nominal"]},
                   pv_capex=float((D.capex_base * disc).sum()), pv_opex=float((D.opex_base * disc).sum()),
                   requirements=dict(te_kw=te["kw"], sewage_kw=round(kw_sew, 1), stp_kw=kw_stp, land_m2=land, stations=n_st, plants=len(stp), staff=staff, **{k: round(v, 1) for k, v in chem_kgd.items()}),
                   annual=D.round(2).to_dict(orient="list"))
    out[sc]["pv_total"] = out[sc]["pv_capex"] + out[sc]["pv_opex"]
    out[sc]["total_2055"] = out[sc]["capex_nominal_by"][2055] + out[sc]["opex_cum"]["opex_nominal"][2055]
json.dump(out, open(os.path.join(R, "financial.json"), "w"), indent=1, default=float)

# ------------------------------------------------------------------ the workbook
with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
    pd.DataFrame([("Basis", "")] + [(l.strip(), "") for l in __doc__.split("Usage:")[0].splitlines()[1:] if l.strip()]).to_excel(xw, sheet_name="A Read me", index=False, header=False)
    rows = []
    for sc in SC:
        for p, m in out[sc]["plants"].items():
            rows.append(dict(scenario=sc, plant=p, **{f"inflow {y}": m["q"][y] for y in Y5 + [2061]}, design_capacity_2056=round(m["design"]), module=m["size"],
                             modules=m["n"], capacity=m["total"], phasing="; ".join(f"{y}: {k}" for y, k in m["plan"].items()), rate_OMR_per_m3d=m["rate"], land_m2_per_m3d=m["land_per"]))
    pd.DataFrame(rows).to_excel(xw, sheet_name="B Treatment", index=False)
    rows = []
    for sc in SC:
        for p, s in out[sc]["supply"].items():
            for y in (2031, 2036, 2046, 2056):
                rows.append(dict(scenario=sc, plant=p, customers=s["customers"], year=y, **{k: round(v) for k, v in s[y].items()}, surplus=round(s[y]["delivered"] - s[y]["demand"])))
    pd.DataFrame(rows).to_excel(xw, sheet_name="C TE supply", index=False)
    C.drop(columns=["src"]).to_excel(xw, sheet_name="D TE customers", index=False)
    pd.DataFrame([dict(scenario=sc, length_km=round(out[sc]["te"]["km"], 2), cost_OMR=round(out[sc]["te"]["cost"]), booster_kW=out[sc]["te"]["kw"]) for sc in SC]).to_excel(xw, sheet_name="E TE network", index=False)
    pd.DataFrame([dict(scenario=sc, year=y, **c) for sc in SC for y, c in out[sc]["capex_by_year"].items()]).to_excel(xw, sheet_name="F CAPEX base prices", index=False)
    pd.DataFrame([dict(scenario=sc, **out[sc]["requirements"]) for sc in SC]).to_excel(xw, sheet_name="G Operation", index=False)
    pd.concat([pd.DataFrame(out[sc]["annual"]).assign(scenario=sc) for sc in SC]).to_excel(xw, sheet_name="H Annual", index=False)
    pd.DataFrame([dict(scenario=sc, capex_base=round(out[sc]["capex_base"]), capex_escalated=round(out[sc]["capex_nominal"]),
                       opex_25yr_escalated=round(out[sc]["opex_cum"]["opex_nominal"][2055]), total_escalated=round(out[sc]["total_2055"]),
                       pv_capex=round(out[sc]["pv_capex"]), pv_opex=round(out[sc]["pv_opex"]), pv_total=round(out[sc]["pv_total"])) for sc in SC]).to_excel(xw, sheet_name="I Summary", index=False)
for sc in SC:
    o = out[sc]
    print(sc, {p: (m["size"], m["n"], m["plan"]) for p, m in o["plants"].items()}, f"capex {o['capex_base'] / 1e6:.1f} M base, {o['capex_nominal'] / 1e6:.1f} M esc;",
          f"opex y1 {o['opex_first']['total'] / 1e6:.2f} M; 25y esc total {o['total_2055'] / 1e6:.1f} M; PV {o['pv_total'] / 1e6:.1f} M; TE {o['te']['km']:.1f} km {o['te']['kw']:.0f} kW;",
          "supply 2056:", {p: (round(s[2056]['delivered']), round(s[2056]['demand'])) for p, s in o["supply"].items()})
print("wrote", XLSX)
