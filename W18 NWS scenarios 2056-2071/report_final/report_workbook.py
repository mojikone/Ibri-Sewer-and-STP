"""The workbook that goes with the concept design report: the tables behind its charts and the people and flow at every
station, laid out as a person would (one table a sheet, live formulas for every derived value), with the charts built in
Excel itself. The report's chart images are exported from these charts, so the two cannot disagree.
Step 1 writes the sheets with openpyxl; step 2 opens the file in a separate hidden Excel (never the user's own), adds and
formats the charts, saves, and exports each chart to img/chart_*.png.
Usage: python report_workbook.py      Writes deliverables/Ibri_Concept_Design_Tables_and_Charts.xlsx and img/chart_*.png"""
import os, sys, json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import facts_final as F
R = F.R; IMG = os.path.join(HERE, "img"); XLSX = os.path.join(HERE, "deliverables", "Ibri_Concept_Design_Tables_and_Charts.xlsx")
FIN = json.load(open(os.path.join(R, "financial.json"))); DYC = json.load(open(os.path.join(R, "design_year_check_2056.json")))
SF = pd.read_csv(os.path.join(R, "station_flows.csv"))
SC = list(F.SCEN); YEARS = ["2051", "2056", "2061"]; Y5 = [2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061]
CASE = {(sc, y): F.case(sc, y) for sc in SC for y in YEARS}

NAVY = "1B2A4A"; HEAD = PatternFill("solid", fgColor=NAVY); BAND = PatternFill("solid", fgColor="F2F5FA")
thin = Side(style="thin", color="C9D3E0"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
wb = Workbook(); wb.remove(wb.active)


def sheet(name, title, note, head, rows, widths=None, fmt=None):
    """A clean table: title, one note line, header, rows (values or '=' formulas with {r} for the row)."""
    ws = wb.create_sheet(name); ws.sheet_view.showGridLines = False
    ws["A1"] = title; ws["A1"].font = Font(bold=True, size=13, color=NAVY)
    ws["A2"] = note; ws["A2"].font = Font(italic=True, size=9, color="6B7A90")
    for j, h in enumerate(head, 1):
        c = ws.cell(row=4, column=j, value=h); c.fill = HEAD; c.font = Font(bold=True, color="FFFFFF", size=10)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX
    for i, r in enumerate(rows):
        for j, v in enumerate(r, 1):
            c = ws.cell(row=5 + i, column=j, value=v.format(r=5 + i) if isinstance(v, str) and v.startswith("=") else v)
            c.border = BOX; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.font = Font(size=10)
            if i % 2: c.fill = BAND
            if fmt and j - 1 < len(fmt) and fmt[j - 1]: c.number_format = fmt[j - 1]
    ws.row_dimensions[4].height = 42
    for j, w in enumerate(widths or [14] * len(head), 1): ws.column_dimensions[CL(j)].width = w
    ws.freeze_panes = "A5"
    return ws


# ------------------------------------------------------------------ 1 flows from the population to the plant(s)
POP = {2031: 133121, 2036: 148512, 2041: 165698, 2046: 183599, 2051: 203866, 2056: 226301, 2061: 251204}
T413 = {2031: 23867, 2036: 26499, 2041: 29438, 2046: 32500, 2051: 35966, 2056: 39803, 2061: 44062}
inflow = {int(y): v for y, v in FIN["SC1"]["inflow"].items()}
rows = [[y, POP[y], T413[y], 316, 1099, round(T413[y] + 316 - 1099 + 1079 - inflow[y]), 1079, "=C{r}+D{r}-E{r}-F{r}+G{r}", "=H{r}*1.1"] for y in sorted(POP)]
sheet("Flows to the plants", "Average flow from the population to the treatment plant(s)",
      "Chapter 4 flow, with the industrial estates, less the plots not yet conveyed, with the infiltration of the modelled sewers in place of the whole-network allowance.",
      ["Year", "People", "Average flow, Chapter 4 (m³/d)", "Industrial estates (m³/d)", "Infiltration allowance, whole network (m³/d)",
       "Plots not yet conveyed (m³/d)", "Infiltration, modelled sewers (m³/d)", "Average inflow, plant(s) (m³/d)", "Design average +10 % (m³/d)"],
      rows, [9, 11, 15, 13, 17, 15, 15, 15, 15], [None, "#,##0", "#,##0", "#,##0", "#,##0", "#,##0", "#,##0", "#,##0", "#,##0"])

# ------------------------------------------------------------------ 2 gradient limit (SC1, 2056)
rows = [[x["limit"], x["stations"], x["added"], x["km_big"], x["km_under"], "=D{r}-E{r}", "=F{r}/D{r}"] for x in F.LIMITS]
sheet("Gradient limit", "Gradient limit for self-cleansing, Scenario SC1 designed for 2056",
      "Each limit with the station arrangement that keeps the network within the depth criteria with the fewest stations.",
      ["Gradient limit", "Pumping and lift stations", "Lift stations added by steepening", "Sewers above 200 mm (km)",
       "Below 0.75 m/s at the 2031 peak (km)", "Reaching 0.75 m/s (km)", "Reaching 0.75 m/s (%)"], rows, [12, 13, 14, 13, 15, 13, 13],
      [None, "0", "0", "0.0", "0.0", "0.0", "0.0%"])

# ------------------------------------------------------------------ 3 design years, all twelve designs
rows = []
for sc in SC:
    for y in YEARS:
        c = CASE[(sc, y)]; k = DYC.get(f"{sc}-{y}", {"pipes_over": 0, "km_over": 0.0})
        rows.append([sc, int(y), round(c["km_big"], 1), round(c["km_under31"], 1), round(c["km_under36"], 1), "=1-D{r}/C{r}",
                     f"{c['pumps']} / {c['lifts']}", int(c["mh_over12"]), k["pipes_over"], k["km_over"], round(c["cost"]["total"] / 1e6, 1)])
sheet("Design year", "The three design years compared, every scenario",
      "Self-cleansing checked at the 2031 and 2036 peaks; 'over the limit by 2056' = pipes of that design whose depth of flow at the 2056 peak exceeds 0.65 (to DN355) or 0.50 of the diameter.",
      ["Scenario", "Design year", "Sewers above 200 mm (km)", "Below 0.75 m/s, 2031 peak (km)", "Below 0.75 m/s, 2036 peak (km)",
       "Reaching 0.75 m/s at 2031 (%)", "Pumping / lift stations", "Manholes deeper than 12 m", "Pipes over the depth limit by 2056",
       "Length over the limit by 2056 (km)", "Sewer network cost (M OMR)"], rows, [10, 9, 12, 13, 13, 13, 11, 12, 13, 13, 12],
      [None, "0", "0.0", "0.0", "0.0", "0.0%", None, "#,##0", "#,##0", "0.0", "0.0"])

# ------------------------------------------------------------------ 4 people and flow at every station (own catchment; same in every scenario)
own = SF[SF.scenario == "SC1"]
order = sorted(own.station.unique(), key=lambda s: (int(s[1:].split("L")[0]), 0 if "L" not in s else int(s.split("L")[1])))
kind = own.drop_duplicates("station").set_index("station").kind.map({"plant inlet": "plant inlet / pumping", "pump": "pumping station", "lift": "lift station"})
P = own.pivot_table(index="station", columns="year", values="people_own"); Qo = own.pivot_table(index="station", columns="year", values="flow_own_m3d")
rows = [[s, kind[s]] + [int(P.at[s, y]) for y in Y5] + [round(float(Qo.at[s, y])) for y in Y5] for s in order]
n = len(rows); rows.append(["Total", ""] + [f"=SUM({CL(3 + j)}5:{CL(3 + j)}{4 + n})" for j in range(16)])
ws = sheet("Station catchments", "People and average flow generated in each station's own catchment",
           "The sewers that drain by gravity to the station; the same in all four scenarios. Flow includes shops, offices, the estates and infiltration (0.72 m³/d per km).",
           ["Station", "Kind"] + [f"People {y}" for y in Y5] + [f"Flow {y} (m³/d)" for y in Y5], rows, [9, 18] + [10] * 16,
           [None, None] + ["#,##0"] * 16)
for j in range(18): ws.cell(row=5 + n, column=1 + j).font = Font(bold=True, size=10)
rows = []
for sc in SC:
    t = SF[SF.scenario == sc]
    Ft = t.pivot_table(index="station", columns="year", values="flow_through_m3d"); Pt = t.pivot_table(index="station", columns="year", values="people_through")
    for s in order:
        if abs(Ft.at[s, 2056] - Qo.at[s, 2056]) < 0.5 and SF[(SF.station == s) & (SF.year == 2056)].flow_through_m3d.nunique() == 1 and sc != "SC1": continue
        rows.append([sc, s] + [int(Pt.at[s, y]) for y in Y5] + [round(float(Ft.at[s, y])) for y in Y5])
sheet("Station throughflow", "People served and average flow through each station, by scenario",
      "Its own catchment and everything pumped into it. Stations whose flow is the same in every scenario are listed under SC1 only.",
      ["Scenario", "Station"] + [f"People {y}" for y in Y5] + [f"Flow {y} (m³/d)" for y in Y5], rows, [10, 9] + [10] * 16,
      [None, None] + ["#,##0"] * 16)

# ------------------------------------------------------------------ 5 treatment capacity and phasing
rows = []
for cfg, (sc, stp) in {"Single plant (SC1, SC2)": ("SC1", "STP-1"), "Main plant with STP-5 (SC3, SC4)": ("SC3", "STP-1"), "STP-5 (SC3, SC4)": ("SC3", "STP-5")}.items():
    p = FIN[sc]["plants"][stp]; inst = 0
    for y in [2031, 2036, 2041, 2046, 2051, 2056]:
        inst += p["plan"].get(str(y), 0)
        rows.append([cfg, y, p["q"][str(y)], "=C{r}*1.1", inst * p["size"]])
sheet("Plant capacity", "Plant inflow, requirement with the 10 % margin, and installed capacity",
      "Four equal modules a plant; a module is commissioned in the first five-year year whose inflow +10 % exceeds the installed capacity.",
      ["Plant", "Year", "Average inflow (m³/d)", "Inflow +10 % (m³/d)", "Installed capacity (m³/d)"], rows, [30, 9, 14, 14, 15],
      [None, "0", "#,##0", "#,##0", "#,##0"])

# ------------------------------------------------------------------ 6 the scenarios compared
C = {sc: CASE[(sc, "2056")] for sc in SC}
M = [("Gravity sewers (km)", [round(C[s]["sewer_km"]) for s in SC], "#,##0"), ("Pumping stations", [C[s]["pumps"] for s in SC], "0"),
     ("Lift stations", [C[s]["lifts"] for s in SC], "0"), ("Force mains (km)", [round(C[s]["force_main_km"], 1) for s in SC], "0.0"),
     ("Network pumping duty (kW)", [round(C[s]["kw_network"]) for s in SC], "#,##0"), ("Plant inlet pumping duty (kW)", [round(C[s]["kw_plant_inlets"]) for s in SC], "#,##0"),
     ("Sewage pumping duty (kW)", ["={c}9+{c}10"] * 4, "#,##0"), ("TE booster duty (kW)", [round(FIN[s]["te"]["kw"]) for s in SC], "#,##0"),
     ("Combined duty (kW)", ["={c}11+{c}12"] * 4, "#,##0"), ("TE network (km)", [round(FIN[s]["te"]["km"], 1) for s in SC], "0.0"),
     ("Sewer network cost (M OMR)", [round(C[s]["cost"]["total"] / 1e6, 1) for s in SC], "0.0"), ("Capital cost (M OMR, 2031 prices)", [round(FIN[s]["capex_base"] / 1e6, 1) for s in SC], "0.0"),
     ("Operating cost, first year (M OMR)", [round(FIN[s]["opex_first"]["total"] / 1e6, 2) for s in SC], "0.00"),
     ("Whole-life cost, constant prices (M OMR)", [round(FIN[s]["pv_total"] / 1e6, 1) for s in SC], "0.0"),
     ("Cumulative cost, escalated, 25 years (M OMR)", [round(FIN[s]["total_2055"] / 1e6, 1) for s in SC], "0.0")]
ws = wb.create_sheet("Scenarios compared"); ws.sheet_view.showGridLines = False
ws["A1"] = "The four scenarios compared, 2056 design"; ws["A1"].font = Font(bold=True, size=13, color=NAVY)
ws["A2"] = "Duty power is installed duty, not annual energy; treatment process power is excluded."; ws["A2"].font = Font(italic=True, size=9, color="6B7A90")
for j, h in enumerate(["Item"] + SC, 1):
    c = ws.cell(row=4, column=j, value=h); c.fill = HEAD; c.font = Font(bold=True, color="FFFFFF"); c.alignment = Alignment(horizontal="center"); c.border = BOX
for i, (lab, vals, nf) in enumerate(M):
    r = 5 + i; c = ws.cell(row=r, column=1, value=lab); c.border = BOX; c.font = Font(size=10)
    for j, v in enumerate(vals):
        col = CL(2 + j); x = ws.cell(row=r, column=2 + j, value=v.format(c=col) if isinstance(v, str) else v)
        x.number_format = nf; x.border = BOX; x.alignment = Alignment(horizontal="center"); x.font = Font(size=10, bold=lab.startswith(("Combined", "Whole-life", "Cumulative")))
        if i % 2: x.fill = BAND
    if i % 2: c.fill = BAND
ws.column_dimensions["A"].width = 42
for j in range(4): ws.column_dimensions[CL(2 + j)].width = 12
ws.freeze_panes = "B5"

# ------------------------------------------------------------------ 7 cumulative cost by year, and 8 whole-life cost
YC = ["2031", "2036", "2041", "2046", "2051", "2055"]
rows = [[int(y)] + [round((FIN[s]["capex_nominal_by"][y] + FIN[s]["opex_cum"]["opex_nominal"][y]) / 1e6, 1) for s in SC] for y in YC]
sheet("Cost by year", "Cumulative CAPEX and OPEX, escalated at 5 % a year, M OMR", "From 2031 to the end of each year shown; 2055 completes 25 years of operation.",
      ["Year"] + SC, rows, [9, 12, 12, 12, 12], ["0"] + ["0.0"] * 4)
rows = [[s, round(FIN[s]["pv_capex"] / 1e6, 1), round(FIN[s]["pv_opex"] / 1e6, 1), "=B{r}+C{r}", "=MIN($D$5:$D$8)*1.1", "=D{r}/MIN($D$5:$D$8)-1"] for s in SC]
sheet("Whole-life cost", "Whole-life cost over 25 years at 5 %, constant prices, M OMR", "PAM-GUD-201 pp. 95-96; within 10 % of the lowest, the more sustainable scenario is preferred (p. 106).",
      ["Scenario", "Present value of capital", "Present value of operation", "Whole-life cost", "Lowest +10 %", "Above the lowest"], rows, [10, 14, 14, 13, 13, 12],
      [None, "0.0", "0.0", "0.0", "0.0", "0.0%"])

# ------------------------------------------------------------------ contents
ws = wb.create_sheet("Contents", 0); ws.sheet_view.showGridLines = False
ws["A1"] = "Ibri Sewer, TE Networks and STP - Concept Design: tables and charts"; ws["A1"].font = Font(bold=True, size=14, color=NAVY)
for i, (s, d) in enumerate([("Flows to the plants", "Population and flow, Chapter 4 to the plant inflow"), ("Gradient limit", "The 0.50, 0.75 and 1.00 % limits compared"),
                            ("Design year", "The twelve designs: four scenarios in three design years"), ("Station catchments", "People and flow generated at every station, 2026-2061"),
                            ("Station throughflow", "People served and flow through every station, by scenario"), ("Plant capacity", "Inflow and installed capacity of the plants"),
                            ("Scenarios compared", "Quantities, duty power, TE and costs of the four scenarios"), ("Cost by year", "Cumulative CAPEX and OPEX by year"),
                            ("Whole-life cost", "Present value over 25 years")]):
    a = ws.cell(row=3 + i, column=1, value=s); a.hyperlink = f"#'{s}'!A1"; a.font = Font(color="1F6FB2", underline="single")
    ws.cell(row=3 + i, column=2, value=d)
ws.column_dimensions["A"].width = 24; ws.column_dimensions["B"].width = 64
os.makedirs(os.path.dirname(XLSX), exist_ok=True); wb.save(XLSX); print("sheets written")

# ------------------------------------------------------------------ step 2: the charts, in Excel itself
import win32com.client as W
rgb = lambda h: int(h[0:2], 16) + 256 * int(h[2:4], 16) + 65536 * int(h[4:6], 16)
PAL = {"navy": "1B2A4A", "blue": "1F6FB2", "orange": "D9730D", "green": "2E8B57", "red": "D7301F", "purple": "7B4FB0", "grey": "8C99AD", "light": "9DC3E6"}
app = W.DispatchEx("Excel.Application"); app.Visible = False; app.DisplayAlerts = False
try:
    book = app.Workbooks.Open(XLSX)

    def new_chart(ws, kind, left, top, w=960, h=520, title=None):
        sh = ws.Shapes.AddChart2(-1, kind, left, top, w, h); ch = sh.Chart
        ch.HasTitle = bool(title)
        if title: ch.ChartTitle.Text = title; ch.ChartTitle.Format.TextFrame2.TextRange.Font.Size = 17; ch.ChartTitle.Format.TextFrame2.TextRange.Font.Bold = True
        ch.ChartArea.Format.TextFrame2.TextRange.Font.Name = "Calibri"; ch.ChartArea.Format.TextFrame2.TextRange.Font.Size = 13; ch.ChartArea.Format.Line.Visible = False
        while ch.SeriesCollection().Count: ch.SeriesCollection(1).Delete()
        return ch

    def series(ch, name, vals, cats, colour, kind=None, axis=1, labels=False, fmt="#,##0", dash=False, width=3.0, white=False):
        s = ch.SeriesCollection().NewSeries(); s.Name = name; s.Values = vals; s.XValues = cats
        if kind: s.ChartType = kind
        s.AxisGroup = axis
        if kind in (4, 65):                                                   # lines
            s.Format.Line.ForeColor.RGB = rgb(colour); s.Format.Line.Weight = width
            if dash: s.Format.Line.DashStyle = 4
            s.MarkerStyle = 8 if kind == 65 else -4142; s.MarkerSize = 6
            try: s.MarkerBackgroundColor = rgb(colour); s.MarkerForegroundColor = rgb(colour)
            except Exception: pass
        else:
            s.Format.Fill.ForeColor.RGB = rgb(colour); s.Format.Line.Visible = False
        if labels:
            s.HasDataLabels = True; s.DataLabels().NumberFormat = fmt; s.DataLabels().Format.TextFrame2.TextRange.Font.Size = 12
            if kind in (4, 65):
                try: s.DataLabels().Position = 0; s.DataLabels().Format.TextFrame2.TextRange.Font.Bold = True   # above the marker, clear of any bar
                except Exception: pass
            if white:
                s.DataLabels().Format.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = rgb('FFFFFF'); s.DataLabels().Format.TextFrame2.TextRange.Font.Bold = True
                if ch.ChartType in (51, 57) or kind in (51, 57):                  # clustered columns or bars: label inside the end of the bar
                    try: s.DataLabels().Position = 3
                    except Exception: pass
        return s

    def axis_title(ch, which, text, group=1):
        a = ch.Axes(which, group); a.HasTitle = True; a.AxisTitle.Text = text; a.AxisTitle.Format.TextFrame2.TextRange.Font.Size = 13

    def tidy(ch, legend=True):
        ch.HasLegend = legend
        if legend: ch.Legend.Position = -4107; ch.Legend.Format.TextFrame2.TextRange.Font.Size = 13
        try:
            ch.Axes(2).MajorGridlines.Format.Line.ForeColor.RGB = rgb("E3E8EF")
        except Exception: pass

    out = {}
    # gradient limit: km below 0.75 (columns) and stations (line, right axis)
    ws = book.Worksheets("Gradient limit")
    ch = new_chart(ws, 51, 20, 140, title="Gradient limit: early-year self-cleansing against stations")
    series(ch, "Sewers above 200 mm below 0.75 m/s at the 2031 peak (km)", ws.Range("E5:E7"), ws.Range("A5:A7"), PAL["blue"], labels=True, fmt="0.0", white=True)
    series(ch, "Pumping and lift stations", ws.Range("B5:B7"), ws.Range("A5:A7"), PAL["red"], kind=65, axis=2, labels=True, fmt="0")
    axis_title(ch, 2, "km below 0.75 m/s"); axis_title(ch, 2, "stations", 2); ch.Axes(2, 2).MinimumScale = 15; ch.Axes(2, 2).MaximumScale = 27
    tidy(ch); out["chart_gradient_limit"] = ch
    # design year: km below 0.75 at 2031 by scenario and year
    ws = book.Worksheets("Design year")
    ch = new_chart(ws, 51, 20, 260, w=960, h=470, title="Design year, Scenario SC1: what each design year leaves short (km)")
    series(ch, "Sewers above 200 mm below 0.75 m/s at the 2031 peak", ws.Range("D5:D7"), ws.Range("B5:B7"), PAL["blue"], labels=True, fmt="0.0")
    series(ch, "Sewers over their depth limit by 2056", ws.Range("J5:J7"), ws.Range("B5:B7"), PAL["red"], labels=True, fmt="0.0")
    ch.ChartGroups(1).GapWidth = 80; ch.ChartGroups(1).Overlap = -10
    axis_title(ch, 1, "Designed for"); axis_title(ch, 2, "km"); tidy(ch); out["chart_design_year"] = ch
    # plant capacity: requirement (solid) and installed (dashed) for the three plant configurations
    ws = book.Worksheets("Plant capacity")
    ch = new_chart(ws, 51, 20, 160, w=960, h=560, title="Treatment capacity: installed modules and inflow +10 % (m³/d)")
    CFG = [("Single plant (SC1, SC2)", PAL["blue"], "BDD7EE"), ("Main plant with STP-5 (SC3, SC4)", PAL["orange"], "F8CBAD"), ("STP-5 (SC3, SC4)", PAL["green"], "C6E0B4")]
    for k, (cfg, colr, tint) in enumerate(CFG):
        r0 = 5 + 6 * k; series(ch, f"{cfg}: installed", ws.Range(f"E{r0}:E{r0 + 5}"), ws.Range(f"B{r0}:B{r0 + 5}"), tint)
    for k, (cfg, colr, tint) in enumerate(CFG):
        r0 = 5 + 6 * k; series(ch, f"{cfg}: inflow +10 %", ws.Range(f"D{r0}:D{r0 + 5}"), ws.Range(f"B{r0}:B{r0 + 5}"), colr, kind=65)
    ch.ChartGroups(1).GapWidth = 40; ch.ChartGroups(1).Overlap = 0
    axis_title(ch, 2, "m³/d"); tidy(ch); out["chart_plant_capacity"] = ch
    # duty power: sewage and TE stacked bars by scenario
    ws = book.Worksheets("Scenarios compared")
    ch = new_chart(ws, 58, 20, 360, w=960, h=430, title="Duty pump power by scenario (kW)")
    series(ch, "Sewage pumping (network and plant inlets)", ws.Range("B11:E11"), ws.Range("B4:E4"), PAL["blue"], labels=True, white=True)
    series(ch, "Treated effluent boosters", ws.Range("B12:E12"), ws.Range("B4:E4"), PAL["purple"], labels=True, white=True)
    ch.Axes(1).ReversePlotOrder = True; ch.ChartGroups(1).GapWidth = 60; tidy(ch); out["chart_duty_power"] = ch
    # cumulative cost by year
    ws = book.Worksheets("Cost by year")
    ch = new_chart(ws, 65, 20, 150, title="Cumulative CAPEX and OPEX, escalated (M OMR)")
    for s_, colr in zip(SC, [PAL["blue"], PAL["orange"], PAL["green"], PAL["purple"]]):
        j = 2 + SC.index(s_); series(ch, s_, ws.Range(f"{CL(j)}5:{CL(j)}10"), ws.Range("A5:A10"), colr, kind=65)
    axis_title(ch, 2, "M OMR"); tidy(ch); out["chart_cost_by_year"] = ch
    # whole-life cost: stacked PV of capital and operation, with the 10 % line
    ws = book.Worksheets("Whole-life cost")
    ch = new_chart(ws, 52, 20, 150, title="Whole-life cost over 25 years, constant prices (M OMR)")
    series(ch, "Present value of capital", ws.Range("B5:B8"), ws.Range("A5:A8"), PAL["blue"], labels=True, fmt="0.0", white=True)
    series(ch, "Present value of operation", ws.Range("C5:C8"), ws.Range("A5:A8"), PAL["light"], labels=True, fmt="0.0")
    series(ch, "Lowest +10 %", ws.Range("E5:E8"), ws.Range("A5:A8"), PAL["red"], kind=4, dash=True, width=2.0)
    ch.ChartGroups(1).GapWidth = 70; axis_title(ch, 2, "M OMR"); tidy(ch); out["chart_whole_life_cost"] = ch
    book.Save()
    for ch in out.values():
        for ax_ in (1, 2):
            try: ch.Axes(ax_).TickLabels.Font.Size = 12
            except Exception: pass
    for name, ch in out.items():
        p = os.path.join(IMG, name + ".png"); ch.Export(p); print("exported", name)
    book.Close(False)
finally:
    app.Quit()
print("wrote", XLSX)
