"""W18 final design: the bill of quantities of the sewer network for the four scenarios and three design years, and the
network capital cost at the rates of the team's options cost estimate (October 2026), in one workbook:
  Read me, Summary, A Gravity sewers, B Manholes, C Pumping stations and lifts, D Force mains, E Treatment plants,
  F Network cost (amounts as formulas, so a rate can be changed in the sheet).
Quantities from results/final_0.75pc_SC1-SC4/<case>/named and /products. Current names only. Excluded until the survey
(as the earlier bill): house connections, crossings, excavation and backfill volumes, reinstatement. Not priced here:
the treatment plants, the treated effluent network and the operating cost (the team's estimate).
Usage: python final_boq.py    Writes report_final/deliverables/Ibri_Sewer_BOQ_and_Network_Cost_SC1-SC4.xlsx"""
import os, sys, json, collections
import numpy as np, pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
OUT = os.path.join(W18, "report_final", "deliverables", "Ibri_Sewer_BOQ_and_Network_Cost_SC1-SC4.xlsx")
RATES = os.path.join(r"W:\2621 Design and Supervision for STP, Sewer & TE Networks System in Ibri_NAMA\06-WORKING\04-Hydraulic\11_Finacial",
                     "2621 - Options Cost Estimation-MH 14-10-2026.xlsx")
SCEN = {"SC1": "STP 1 only", "SC2": "STP 16 only", "SC3": "STP 1 and STP 5", "SC4": "STP 16 and STP 5"}
CASES = [f"{s}-{y}" for s in SCEN for y in ("2051", "2056", "2061")]
NAVY = "1F3B63"; HEAD = PatternFill("solid", fgColor="DCE6F1"); BASE = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="999999"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
BANDS = ["Up to 1.5"] + [f"{a / 2:.1f} - {a / 2 + 0.5:.1f}" for a in range(3, 30)] + ["Over 15.0"]


def band(d):
    if d <= 1.5: return "Up to 1.5"
    if d > 15: return "Over 15.0"
    a = math.floor(d * 2) / 2 if (d * 2) % 1 else d - 0.5
    return f"{a:.1f} - {a + 0.5:.1f}"


import math
mh_type = lambda dn: "Type 1 - 1200 mm" if dn <= 355 else "Type 2 - 1500 mm" if dn <= 560 else "Type 3 - 1800 mm"

# ------------------------------------------------------------------ the team's rates
wb_r = load_workbook(RATES, data_only=True)
ws = wb_r["Pipe Rate"]; hdr = [c for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
pipe_rate, fm_rate, sec = {}, {}, "sewer"
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == "Force/TSE Pipes": sec = "force"; continue
    if isinstance(row[0], (int, float)):
        if sec == "sewer": pipe_rate[int(row[0])] = {hdr[i]: row[i] for i in range(1, len(hdr)) if hdr[i] and isinstance(row[i], (int, float))}
        else: fm_rate[int(row[0])] = row[1]
growth = 1.11                                                        # the sheet's rise from one 0.5 m band to the next
ws = wb_r["Manhole Rate"]; mh_hdr = [c for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
mh_rate = {}
for row in ws.iter_rows(min_row=2, max_row=4, values_only=True):
    mh_rate[row[0]] = {mh_hdr[i]: row[i] for i in range(1, len(mh_hdr)) if mh_hdr[i] and isinstance(row[i], (int, float))}
ST_RATE = {"lift or pump up to 10 kW": 25000.0, "lift or pump over 10 kW": 5000.0, "plant inlet pumping station": 5000.0}   # OMR/kW


def rate_pipe(dn, b):
    r = pipe_rate[dn]
    return r[b] if b in r else r["14.5 - 15.0"] * growth                # over 15 m: one more band's rise
def rate_mh(t, b):
    r = mh_rate[t]
    return r[b] if b in r else r["14.5 - 15.0"] * growth
def rate_fm(dn):
    for d in sorted(fm_rate):
        if d >= max(dn, 100): return fm_rate[d], d
    return fm_rate[max(fm_rate)], max(fm_rate)


# ------------------------------------------------------------------ quantities
A, B, C, D, E, Q = {}, {}, [], {}, [], {}
for c in CASES:
    K = pd.read_csv(os.path.join(R, c, "named", "links.csv")); N = pd.read_csv(os.path.join(R, c, "named", "nodes.csv"))
    S = pd.read_csv(os.path.join(R, c, "products", "stations.csv")); P = pd.read_csv(os.path.join(R, c, "products", "plants.csv"))
    Q[c] = json.load(open(os.path.join(R, c, "products", "quantities.json")))
    K["b"] = ((K.depth_up_m + K.depth_dn_m) / 2).map(band)              # depth to invert, average of the two ends
    A[c] = K.groupby(["dn_mm", "b"]).length_m.sum()
    big = pd.concat([K[["from_mh", "dn_mm"]].rename(columns={"from_mh": "mh"}), K[["to_mh", "dn_mm"]].rename(columns={"to_mh": "mh"})]).groupby("mh").dn_mm.max()
    mh = N[N.kind == "manhole"].copy(); mh["t"] = mh.new.map(big).fillna(200).map(mh_type); mh["b"] = mh.depth.map(band)
    B[c] = mh.groupby(["t", "b"]).size()
    D[c] = S[S.force_main_m > 0].groupby("force_main_dn").force_main_m.sum()
    for r in S.itertuples(): C.append(dict(case=c, **r._asdict()))
    for r in P.itertuples(): E.append(dict(case=c, **r._asdict()))

# ------------------------------------------------------------------ workbook
wb = Workbook()


def title(ws, text, note):
    ws["A1"] = text; ws["A1"].font = Font(size=13, bold=True, color=NAVY); ws["A2"] = note; ws["A2"].alignment = Alignment(wrap_text=False)


def header(ws, row, titles, widths=None):
    for i, t in enumerate(titles, 1):
        x = ws.cell(row=row, column=i, value=t); x.font = Font(bold=True, color=NAVY); x.fill = HEAD; x.border = BOX
        x.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        if widths: ws.column_dimensions[get_column_letter(i)].width = widths[i - 1] if i <= len(widths) else widths[-1]
    ws.row_dimensions[row].height = 32


def put(ws, row, vals, fmt=None, bold=False, base_cols=()):
    for i, v in enumerate(vals, 1):
        x = ws.cell(row=row, column=i, value=v); x.border = BOX; x.font = Font(bold=bold)
        if fmt and i > 2 and isinstance(v, (int, float)) or (fmt and isinstance(v, str) and v.startswith("=")): x.number_format = fmt
        if i in base_cols: x.fill = BASE


case_head = [f"{c.split('-')[0]} {SCEN[c.split('-')[0]]}\ndesigned for {c.split('-')[1]}" for c in CASES]
base_cols = [i + 3 for i, c in enumerate(CASES) if c.endswith("2056")]
ws = wb.active; ws.title = "Read me"
lines = [("Ibri sewer network, scenarios SC1 to SC4: bill of quantities and network capital cost", "t"), ("", ""),
         ("Scenarios", "h"), ("SC1: one treatment plant, STP 1. SC2: one treatment plant, STP 16. SC3: STP 1 and STP 5. SC4: STP 16 and STP 5.", ""),
         ("Each scenario is designed for 2051, 2056 and 2061; 2056 (2031 plus 25 years) is the base design and is shaded.", ""), ("", ""),
         ("Basis", "h"),
         ("Gravity sewers: PAM-GUD-203 Table 11 minimum gradients, steepened where needed (up to 0.75 %) so that sewers above DN200 reach 0.75 m/s at the 2031 peak flow.", ""),
         ("Depth to invert: limited to about 12 m; where a slightly deeper sewer saves a pumping station or a lift, up to about 15 m at a station and 16.5 m at a manhole.", ""),
         ("Pumping station: pumps through a force main to another location. Lift station: pumps to a nearby manhole within one standard manhole spacing. PAM-GUD-203 calls both pumping stations, Type 1 to 3 by design flow.", ""),
         ("Sewer length by nominal diameter and by depth to invert (average of the two ends), in the 0.5 m bands of the rate tables.", ""),
         ("Manholes by type (the largest pipe: up to DN355 Type 1, 1200 mm; DN400 to DN560 Type 2, 1500 mm; DN630 and larger Type 3, 1800 mm) and by depth to invert.", ""),
         ("Stations: duty, head and power at the design-year peak; force mains sized for 1.0 to 2.5 m/s.", ""), ("", ""),
         ("Rates (sheet F)", "h"),
         ("The rates of the options cost estimate of October 2026: sewers and manholes by size and 0.5 m depth band, force mains by diameter, stations by installed power (up to 10 kW 25,000 OMR/kW; over 10 kW and plant inlet stations 5,000 OMR/kW).", ""),
         ("Depths beyond the last band of a rate table (over 15 m) take the last rate raised by the table's step of 11 %. Force mains below 100 mm take the 100 mm rate; a diameter without a rate takes the next larger one.", ""),
         ("Amounts are formulas: a rate changed in sheet F changes the totals.", ""), ("", ""),
         ("Not included", "h"), ("House connections, road and wadi crossings, excavation and backfill volumes, reinstatement (to follow the survey).", ""),
         ("Treatment plants, the treated effluent network and operating cost are priced in the options cost estimate.", "")]
for i, (t, k) in enumerate(lines, 1):
    x = ws.cell(row=i, column=1, value=t); x.font = Font(size=13 if k == "t" else 10, bold=k in ("t", "h"), color=NAVY if k else "000000")
ws.column_dimensions["A"].width = 150

ws = wb.create_sheet("Summary"); title(ws, "Summary by scenario and design year", "Base design (2056) shaded.")
header(ws, 4, ["Item", "Unit"] + case_head, [44, 10] + [17] * len(CASES))
rows = [("Gravity sewers", "km", lambda q: q["sewer_km"]), ("   of which above DN200", "km", lambda q: q["km_big"]),
        ("Manholes", "nr", lambda q: q["manholes"]), ("Pumping stations", "nr", lambda q: q["pumps"]), ("Lift stations", "nr", lambda q: q["lifts"]),
        ("Plant inlet pumping stations", "nr", lambda q: q["plant_inlets"]), ("Force mains", "km", lambda q: q["force_main_km"]),
        ("Network pumping duty", "kW", lambda q: q["kw_network"]), ("Plant inlet pumping duty", "kW", lambda q: q["kw_plant_inlets"]),
        ("Pumping energy, 2031", "MWh/yr", lambda q: q["mwh_2031"]), ("Pumping energy, design year", "MWh/yr", lambda q: q["mwh_design"]),
        ("Sewers above DN200 under 0.75 m/s at the 2031 peak", "km", lambda q: q["km_big_under075_2031"]),
        ("   of which still under 0.75 m/s at the 2036 peak", "km", lambda q: q["km_big_under075_2036"]),
        ("Deepest manhole", "m", lambda q: q["deepest"]["depth"])]
for i, (a, u, f) in enumerate(rows, 5): put(ws, i, [a, u] + [f(Q[c]) for c in CASES], "#,##0.0", base_cols=base_cols)

ws = wb.create_sheet("A Gravity sewers"); title(ws, "Bill A: gravity sewers", "Length in metres by nominal diameter and depth to invert (average of the two ends).")
header(ws, 4, ["Diameter, mm", "Depth band, m"] + case_head, [14, 14] + [17] * len(CASES))
keys = sorted(set().union(*[set(A[c].index) for c in CASES]), key=lambda k: (k[0], BANDS.index(k[1])))
r = 5
for k in keys:
    put(ws, r, [int(k[0]), k[1]] + [round(float(A[c].get(k, 0)), 1) for c in CASES], "#,##0", base_cols=base_cols); r += 1
put(ws, r, ["Total", ""] + [round(float(A[c].sum()), 1) for c in CASES], "#,##0", bold=True, base_cols=base_cols)

ws = wb.create_sheet("B Manholes"); title(ws, "Bill B: manholes", "Number by type (largest pipe at the manhole) and depth to invert.")
header(ws, 4, ["Type", "Depth band, m"] + case_head, [20, 14] + [17] * len(CASES))
keys = sorted(set().union(*[set(B[c].index) for c in CASES]), key=lambda k: (k[0], BANDS.index(k[1])))
r = 5
for k in keys:
    put(ws, r, [k[0], k[1]] + [int(B[c].get(k, 0)) for c in CASES], "#,##0", base_cols=base_cols); r += 1
put(ws, r, ["Total", ""] + [int(B[c].sum()) for c in CASES], "#,##0", bold=True, base_cols=base_cols)

ws = wb.create_sheet("C Pumping stations"); title(ws, "Bill C: pumping stations and lift stations", "One row per station; duty and head at the design-year peak. Type by PAM-GUD-203 (design flow).")
cols = ["case", "name", "kind", "g203_type", "outfall_depth_m", "wet_well_depth_m", "q_design_ls", "duty_ls", "head_m", "kw", "pumps_to",
        "force_main_dn", "force_main_m", "fm_velocity_ms", "avg_design_m3d", "mwh_design"]
heads = ["Scenario, design year", "Station", "Kind", "Type", "Incoming sewer depth, m", "Wet well depth, m", "Design peak, L/s", "Duty, L/s",
         "Head, m", "Power, kW", "Discharges to", "Force main, mm", "Force main, m", "Velocity, m/s", "Average flow, m³/d", "Energy, MWh/yr"]
header(ws, 4, heads, [16, 9, 13, 7, 11, 11, 11, 10, 9, 10, 16, 11, 11, 10, 13, 12])
for i, x in enumerate(C, 5):
    put(ws, i, [x["case"].replace("-", " "), x["name"], x["kind"], x["g203_type"], x["outfall_depth_m"], x["wet_well_depth_m"], x["q_design_ls"], x["duty_ls"],
                x["head_m"], x["kw"], x["pumps_to"] if str(x["pumps_to"]) != "nan" else "", x["force_main_dn"] if x["force_main_dn"] == x["force_main_dn"] else "",
                x["force_main_m"], x["fm_velocity_ms"] if x["fm_velocity_ms"] == x["fm_velocity_ms"] else "", x["avg_design_m3d"], x["mwh_design"]], "#,##0.0")

ws = wb.create_sheet("D Force mains"); title(ws, "Bill D: force mains", "Length in metres by nominal diameter; the material is chosen at the preliminary design.")
header(ws, 4, ["Diameter, mm", ""] + case_head, [14, 4] + [17] * len(CASES))
keys = sorted(set().union(*[set(D[c].index) for c in CASES]))
for i, k in enumerate(keys, 5): put(ws, i, [int(k), ""] + [round(float(D[c].get(k, 0)), 1) for c in CASES], "#,##0", base_cols=base_cols)
put(ws, 5 + len(keys), ["Total", ""] + [round(float(D[c].sum()), 1) for c in CASES], "#,##0", bold=True, base_cols=base_cols)

ws = wb.create_sheet("E Treatment plants"); title(ws, "Bill E: treatment plants", "Average flow arriving at each plant by year (the plots served and the infiltration of their sewers), the inlet depth and the design peak.")
yc = [c for c in pd.DataFrame(E).columns if c.startswith("avg_")]
header(ws, 4, ["Scenario, design year", "Plant inlet", "Inlet depth, m"] + [c[4:8] + ", m³/d" for c in yc] + ["Design peak, L/s"], [18, 11, 11] + [12] * len(yc) + [13])
for i, x in enumerate(E, 5): put(ws, i, [x["case"].replace("-", " "), x["plant"], x["inlet_depth_m"]] + [x[c] for c in yc] + [x["peak_design_ls"]], "#,##0")

# ------------------------------------------------------------------ F: network cost at the team's rates (formulas)
ws = wb.create_sheet("F Network cost"); title(ws, "Network capital cost at the rates of the options cost estimate (October 2026), OMR",
                                               "Amount = rate x quantity (formulas). Treatment plants, treated effluent network and operating cost: see the options cost estimate.")
n = len(CASES); hdr_ = ["Item", "Detail", "Rate, OMR"] + [h.replace("\n", " ") + " qty" for h in case_head] + [h.replace("\n", " ") + " OMR" for h in case_head]
header(ws, 4, hdr_, [30, 18, 12] + [12] * n + [15] * n)
r = 5; sect_rows = {}


def line(item, detail, rate, qtys):
    global r
    vals = [item, detail, round(rate, 2)] + [q for q in qtys]
    put(ws, r, vals, "#,##0.0")
    for j in range(n):
        qc = get_column_letter(4 + j); ac = 4 + n + j
        x = ws.cell(row=r, column=ac, value=f"=C{r}*{qc}{r}"); x.number_format = "#,##0"; x.border = BOX
    r += 1


for name, fn in (("Gravity sewers", None),):
    start = r
    keys = sorted(set().union(*[set(A[c].index) for c in CASES]), key=lambda k: (k[0], BANDS.index(k[1])))
    for k in keys: line("Gravity sewer", f"DN{int(k[0])}, {k[1]} m", rate_pipe(int(k[0]), k[1]), [round(float(A[c].get(k, 0)), 1) for c in CASES])
    sect_rows["Gravity sewers"] = (start, r - 1)
start = r
for k in sorted(set().union(*[set(B[c].index) for c in CASES]), key=lambda k: (k[0], BANDS.index(k[1]))):
    line("Manhole", f"{k[0]}, {k[1]} m", rate_mh(k[0], k[1]), [int(B[c].get(k, 0)) for c in CASES])
sect_rows["Manholes"] = (start, r - 1)
start = r
for k in sorted(set().union(*[set(D[c].index) for c in CASES])):
    rt, used = rate_fm(int(k)); line("Force main", f"DN{int(k)}" + (f" (rate of DN{used})" if used != k else ""), rt, [round(float(D[c].get(k, 0)), 1) for c in CASES])
sect_rows["Force mains"] = (start, r - 1)
start = r
Cdf = pd.DataFrame(C)
cat = lambda x: "plant inlet pumping station" if x.kind == "plant inlet" else "lift or pump up to 10 kW" if x.kw <= 10 else "lift or pump over 10 kW"
Cdf["cat"] = [cat(x) for x in Cdf.itertuples()]
for k in ST_RATE:
    line("Pumping and lift stations", f"{k}, installed power kW", ST_RATE[k], [round(float(Cdf[(Cdf.case == c) & (Cdf.cat == k)].kw.sum()), 1) for c in CASES])
sect_rows["Pumping and lift stations"] = (start, r - 1)
r += 1
for name, (a, b) in sect_rows.items():
    vals = [f"Total: {name.lower()}", "", ""] + [""] * n
    put(ws, r, vals, bold=True)
    for j in range(n):
        ac = get_column_letter(4 + n + j); x = ws.cell(row=r, column=4 + n + j, value=f"=SUM({ac}{a}:{ac}{b})"); x.number_format = "#,##0"; x.font = Font(bold=True); x.border = BOX
    r += 1
put(ws, r, ["Total: sewer network", "", ""] + [""] * n, bold=True)
for j in range(n):
    ac = get_column_letter(4 + n + j); x = ws.cell(row=r, column=4 + n + j, value=f"=SUM({ac}{r - len(sect_rows)}:{ac}{r - 1})")
    x.number_format = "#,##0"; x.font = Font(bold=True, color=NAVY); x.border = BOX
for w in wb.worksheets:
    w.sheet_view.zoomScale = 90
    if w.title != "Read me": w.freeze_panes = "C5"
os.makedirs(os.path.dirname(OUT), exist_ok=True); wb.save(OUT)

# the totals, computed here as well (the workbook keeps formulas)
tot = {}
for c in CASES:
    sew = sum(rate_pipe(int(k[0]), k[1]) * v for k, v in A[c].items()); man = sum(rate_mh(k[0], k[1]) * v for k, v in B[c].items())
    fm = sum(rate_fm(int(k))[0] * v for k, v in D[c].items())
    st = sum(ST_RATE[cat(x)] * x.kw for x in Cdf[Cdf.case == c].itertuples())
    tot[c] = dict(sewers=round(sew), manholes=round(man), force_mains=round(fm), stations=round(st), total=round(sew + man + fm + st))
json.dump(tot, open(os.path.join(R, "network_cost.json"), "w"), indent=1)
print("wrote", OUT)
for c in CASES: print(c, {k: f"{v / 1e6:,.2f} M" for k, v in tot[c].items()})
