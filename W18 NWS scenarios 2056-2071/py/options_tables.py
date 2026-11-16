"""The STP options side by side: one workbook for the deliverable folder and one markdown for the repository.

    python options_tables.py
Reads results/S#/S#_summary.json, S#_pipes.csv and S#_pumps.csv (scenario_results.py) for every option that has them.
Writes  W17/Options 2026-10/Tables/W17_network_options_tables.xlsx   (not in git: the deliverable folder)
        W17/results/options_comparison.md                              (in git)
Quantities are the 2070 design of model IBRI_W17_R9; pipe depth is the mean of the depths to invert at the two ends.
"""
import csv, json, os, collections
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from routing import SCENARIOS, YEARS, OLD, option_label

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
RES = os.path.join(W17, "results")
XLSX = os.path.join(W17, "Options 2026-10", "Tables", "W17_network_options_tables.xlsx")
MD = os.path.join(RES, "options_comparison.md")
BANDS = [(0, 1.5), (1.5, 3), (3, 4.5), (4.5, 6), (6, 9), (9, 12), (12, 99)]
band = lambda d: next(f"{a:g}-{b:g} m" if b < 99 else f">{a:g} m" for a, b in BANDS if a <= d < b)
BAND_NAMES = [band((a + min(b, a + 1)) / 2) for a, b in BANDS]
name = lambda s: s          # current names only: the tables go to the client with the report (engineer, 2026-10-01)

opts = [o for o in SCENARIOS if os.path.exists(os.path.join(RES, o, f"{o}_summary.json"))]
S = {o: json.load(open(os.path.join(RES, o, f"{o}_summary.json"), encoding="utf-8")) for o in opts}
P = {o: list(csv.DictReader(open(os.path.join(RES, o, f"{o}_pipes.csv"), encoding="utf-8"))) for o in opts}
PS = {o: list(csv.DictReader(open(os.path.join(RES, o, f"{o}_pumps.csv"), encoding="utf-8"))) for o in opts}

HEAD = Font(bold=True, color="FFFFFF"); FILL = PatternFill("solid", fgColor="1F3B63")
wb = Workbook(); wb.remove(wb.active)


def sheet(title, header, rows, note=None, widths=None):
    ws = wb.create_sheet(title)
    r0 = 1
    if note:
        ws.cell(1, 1, note).font = Font(italic=True, color="5A5A5A"); r0 = 3
    for j, h in enumerate(header, 1):
        c = ws.cell(r0, j, h); c.font = HEAD; c.fill = FILL; c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, row in enumerate(rows, r0 + 1):
        for j, v in enumerate(row, 1):
            ws.cell(i, j, v)
    for j in range(1, len(header) + 1):
        ws.column_dimensions[get_column_letter(j)].width = (widths[j - 1] if widths else 14)
    ws.freeze_panes = ws.cell(r0 + 1, 2)
    return ws


md = [f"# STP options compared — W17, model IBRI_W17_R9 (Colebrook-White, ks 1.5 mm)\n",
      f"Options with results: {', '.join(opts)}. Source: `results/S#/S#_summary.json`, written by `py/scenario_results.py`.\n"]

# ---- summary
hdr = ["Option", "Arrangement", "Plants", "Sewer km", "Pipes", "Manholes", "Manholes 9-12 m", "Manholes > 12 m",
       "Deepest manhole m", "Deepest at", "Sewer > 12 m deep, km", "Pumping stations", "PS type 1/2/3",
       "Pumps in duty kW", "Energy 2030 MWh/yr", "Energy 2070 MWh/yr", "Rising mains km"]
rows = []
for o in opts:
    s = S[o]
    rows.append([o, option_label(o), ", ".join(name(z) for z in s["stp"]), s["pipe_km"], s["pipes"], s["manholes"],
                 s["manholes_by_band"].get("9-12 m", 0), s["manholes_over_12"], s["deepest"]["depth"], s["deepest"]["label"],
                 s["pipe_km_deeper_12"], s["pumping_stations"], "/".join(str(s["ps_by_type"].get(str(t), 0)) for t in (1, 2, 3)),
                 s["kw"], s["mwh_2030"], s["mwh_2070"], round(s["rising_main_m"] / 1000, 2)])
sheet("Summary", hdr, rows, widths=[8, 34, 30] + [12] * (len(hdr) - 3))
md += ["## Summary\n", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
md += ["| " + " | ".join(f"{v:,}" if isinstance(v, (int, float)) else str(v) for v in r) + " |" for r in rows]

# ---- plants by year
hdr = ["Option", "Plant"] + [f"Average {y} m3/d" for y in YEARS] + [f"Peak {y} L/s" for y in YEARS]
rows = []
for o in opts:
    for z in S[o]["stp"]:
        v = S[o]["plants"][z]
        rows.append([o, name(z)] + [v["avg_m3d"][y] for y in YEARS] + [v["peak_ls"][y] for y in YEARS])
sheet("Plant flows", hdr, rows, note="Average = plot flow of the subnetworks served + infiltration 720 L/day/km; peak = sum "
      "of the outfall peaks reaching the plant. The 10 % margin for a new STP (G201 p73) is not included.",
      widths=[8, 16] + [13] * (len(hdr) - 2))
md += ["\n## Average flow arriving at each plant, m³/d (peak 2070, L/s)\n", "| Option | Plant | " + " | ".join(YEARS) + " | peak 2070 |",
       "|" + "---|" * (len(YEARS) + 3)]
md += [f"| {r[0]} | {r[1]} | " + " | ".join(f"{x:,.0f}" for x in r[2:2 + len(YEARS)]) + f" | {r[-1]:,.0f} |" for r in rows]

# ---- pipe length by OD, and by OD x depth band (BOQ)
ods = sorted({int(p["od"]) for o in opts for p in P[o]})
by_od = {o: collections.Counter() for o in opts}
boq = {o: collections.defaultdict(float) for o in opts}
for o in opts:
    for p in P[o]:
        L = float(p["length"]); od = int(p["od"])
        by_od[o][od] += L; boq[o][(od, band(float(p["depth_avg"])))] += L
rows = [[od] + [round(by_od[o][od]) for o in opts] for od in ods] + [["Total"] + [round(sum(by_od[o].values())) for o in opts]]
sheet("Pipes by size", ["OD mm"] + opts, rows, note="Length of sewer, metres, by outside diameter (catalogue size of the 2070 design).",
      widths=[10] + [12] * len(opts))
md += ["\n## Length of sewer by outside diameter, m\n", "| OD mm | " + " | ".join(opts) + " |", "|" + "---|" * (len(opts) + 1)]
md += ["| " + " | ".join(f"{v:,}" if isinstance(v, (int, float)) else str(v) for v in r) + " |" for r in rows]
for o in opts:
    rows = [[od] + [round(boq[o][(od, b)]) or None for b in BAND_NAMES] + [round(by_od[o][od])] for od in ods if by_od[o][od]]
    rows.append(["Total"] + [round(sum(boq[o][(od, b)] for od in ods)) for b in BAND_NAMES] + [round(sum(by_od[o].values()))])
    sheet(f"{o} pipes BOQ", ["OD mm"] + [f"depth {b}" for b in BAND_NAMES] + ["total"], rows,
          note=f"Option {o}: length of sewer, metres, by outside diameter and depth to invert (mean of the two ends).",
          widths=[10] + [12] * (len(BAND_NAMES) + 1))

# ---- manholes by depth band
rows = [[b] + [S[o]["manholes_by_band"].get(b, 0) for o in opts] for b in BAND_NAMES] + [["Total"] + [S[o]["manholes"] for o in opts]]
sheet("Manholes by depth", ["Depth to invert"] + opts, rows, note="Manholes of the 2070 design by depth from the rim to the invert.",
      widths=[16] + [12] * len(opts))
md += ["\n## Manholes by depth to invert\n", "| Depth | " + " | ".join(opts) + " |", "|" + "---|" * (len(opts) + 1)]
md += ["| " + " | ".join(f"{v:,}" if isinstance(v, (int, float)) else str(v) for v in r) + " |" for r in rows]

# ---- pumping stations
hdr = ["Option", "Station", "Discharges to", "Kind", "Type (G203 Tab 17)", "Outfall depth m", "Wet well depth m",
       "Average flow 2070 m3/d", "Q 2070 L/s", "Duty L/s", "Rising main DN", "Velocity m/s", "Rising main m", "Static head m",
       "Total head m", "kW", "MWh/yr 2030", "MWh/yr 2070", "Retention 2030 min", "Live volume m3", "Route"]
rows = []
for o in opts:
    for r in PS[o]:
        f = lambda k, n=1: round(float(r[k]), n)
        rows.append([o, r["ps"], f"STP {r['to']}" if r["kind"] == "plant" else r["to"], r["kind"], int(r["type"]),
                     f("outfall_depth", 2), f("wet_well_depth"), f("avg2070_m3d", 0), f("q70"), f("duty"), int(r["dn"]),
                     f("v", 2), f("L", 0), f("static"), f("H"), f("kw"), round(float(r["kwh2030"]) / 1000, 1),
                     round(float(r["kwh2070"]) / 1000, 1), f("ret2030", 0), f("live_m3"), r["route"]])
sheet("Pumping stations", hdr, rows, note="ASSUMED for the concept: rising mains along roads and streets (cross-country x 1.1 where the "
      "street route is over 1.6 x the straight line); Hazen-Williams C 120 (G202 p104); minor losses +10 %; wet well 1.5 m below "
      "the outfall invert; discharge 0.3 m above the receiving invert (G203 p55) or 3 m above ground at a plant; efficiency 0.65; "
      "duty raised to keep 1.0 m/s in a main of at least 75 mm (G203 p50).", widths=[8, 9, 12, 9, 9] + [11] * 15 + [30])
md += ["\n## Pumping stations (largest duty first)\n", "| Option | Station | to | duty L/s | DN | main m | head m | kW | retention 2030 min |",
       "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[9]:,.1f} | {r[10]} | {r[12]:,.0f} | {r[14]:,.1f} | {r[15]:,.0f} | {r[18]:,.0f} |")

os.makedirs(os.path.dirname(XLSX), exist_ok=True)
wb.save(XLSX)
open(MD, "w", encoding="utf-8").write("\n".join(md) + "\n")
print("wrote", XLSX); print("wrote", MD)
