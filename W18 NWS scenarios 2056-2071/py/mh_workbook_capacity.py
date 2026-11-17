"""The team's workbook 'New Calculation MH.xlsx' copied EXACTLY (every sheet, the chart, their formulas) and edited in
Excel itself (COM: openpyxl would drop the chart sheet), engineer 2026-11-17:
  'MOHUP DATA - NA': columns inserted - Existing Population 2026 (= Average 2026), Existing Residential Plots (their
     'Base MOHUP Data - NA', Residential + Residential-Commercial), Future Plots (our growth plots, typed, shaded blue)
     and Future Population; their Future Residential Plots (MoHUP zoning) KEPT in grey font, no longer used;
     Residential Properties per Plot = MAX(1, existing properties / existing residential plots) (their value, now a
     formula); Future Residential Properties = growth plots x properties per plot; Future Population = x 4.8;
     Total Population Capacity = Existing Population 2026 + Future Population; Saturation Year by COUNTIF.
  'WW Generation': each year = MIN(average population, capacity) x 171.03 L/d + their infiltration; a row for the two
     industrial estates (6,300 workers x 93 L/d x 0.54 = 316.4 m3/d); the total includes it.
  'Notes (W18)': what changed. Their file is not touched; the copy is saved once.
Writes results/New Calculation MH - capacity.xlsx.  Usage: python mh_workbook_capacity.py"""
import os, shutil
import openpyxl, pyogrio
import tempfile, win32com
# pywin32's shared type cache on this machine is corrupt (Excel's gen_py module has no CLSIDToClassMap); use a private,
# empty one instead of touching it, so every Excel object is late-bound
_gp = os.path.join(tempfile.gettempdir(), "gen_py_w18"); os.makedirs(_gp, exist_ok=True)
win32com.__gen_path__ = _gp
import win32com.gen_py; win32com.gen_py.__path__ = [_gp]
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
SRC = os.path.abspath(os.path.join(W18, "..", "..", "temp", "recent updates by the team", "New Calculation MH.xlsx"))
DST = os.path.abspath(os.path.join(W18, "results", "New Calculation MH - capacity.xlsx"))
PLOTS = os.path.join(W18, "gis", "W18_plots_2026_2100.shp")
N0, N1 = 2, 26

p = pyogrio.read_dataframe(PLOTS, columns=["SETTLE", "GROWTH"], read_geometry=False)
ours = p.groupby(p.SETTLE.str.strip().str.upper()).GROWTH.sum().astype(int).to_dict()
v = openpyxl.load_workbook(SRC, data_only=True)
md, av, bs = v["MOHUP DATA - NA"], v["Average"], v["Base MOHUP Data - NA"]
names = [md.cell(r, 1).value.strip().upper() for r in range(N0, N1 + 1)]
assert [av.cell(r, 1).value.strip().upper() for r in range(N0, N1 + 1)] == names, "Average rows are not in the sheet's order"
brow = {}
for r in range(3, 30):
    n = bs.cell(r, 1).value
    if n and n.strip() not in ("Total", "Grand Total") and n.strip().upper() not in brow: brow[n.strip().upper()] = r
assert set(names) == set(ours) == set(brow)
assert [c.value for c in md[1]][:8] == ["Settlements", "Existing Residential Properties", "Future Residential Plots",
        "Residential Properties per Plot", "Future Residential Properties", "Total Residential Properties",
        "Total Population Capacity", "Saturation Year"], "the team's sheet layout changed"

os.makedirs(os.path.dirname(DST), exist_ok=True)
shutil.copy2(SRC, DST)
xl = win32.DispatchEx("Excel.Application")   # a NEW Excel process, never the engineer's open one
xl.Visible = False; xl.DisplayAlerts = False
try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("MOHUP DATA - NA")
    # their layout A..H -> A Settlements, B Existing Res. Properties, C Existing Population 2026 (new), D Existing Res.
    # Plots (new), E their Future Residential Plots (grey), F Future Plots (ours, new), G Properties per Plot, H Future
    # Properties, I Total Properties, J Future Population (new), K Total Population Capacity, L Saturation Year
    ws.Columns("C:D").Insert()
    ws.Columns("F").Insert()
    ws.Columns("J").Insert()
    GREY, BLUE = 0x808080, 0xF7EBDD          # Excel colours are BGR: grey 128,128,128; light blue DDEBF7
    head = {"C": "Existing Population 2026 (average)", "D": "Existing Residential Plots",
            "E": "Future Residential Plots (MoHUP zoning, not used)", "F": "Future Plots (growth plots)", "J": "Future Population"}
    for c, h in head.items(): ws.Range(f"{c}1").Value = h
    for r in range(N0, N1 + 1):
        k = names[r - N0]; b = brow[k]
        ws.Range(f"C{r}").Formula = f"=Average!B{r}"
        ws.Range(f"D{r}").Formula = f"='Base MOHUP Data - NA'!F{b}+'Base MOHUP Data - NA'!G{b}"
        ws.Range(f"F{r}").Value = ours[k]
        ws.Range(f"G{r}").Formula = f"=MAX(1,B{r}/D{r})"
        ws.Range(f"H{r}").Formula = f"=F{r}*G{r}"
        ws.Range(f"I{r}").Formula = f"=H{r}+B{r}"
        ws.Range(f"J{r}").Formula = f"=H{r}*4.8"
        ws.Range(f"K{r}").Formula = f"=C{r}+J{r}"
        ws.Range(f"L{r}").ClearContents()
        ws.Range(f"L{r}").Formula = (f'=IF(COUNTIF(Average!$B{r}:$BX{r},"<"&$K{r})>=COLUMNS(Average!$B{r}:$BX{r}),"Not Fully Occupied",'
                                     f'INDEX(Average!$B$1:$BX$1,COUNTIF(Average!$B{r}:$BX{r},"<"&$K{r})+1))')
    for c in "CDFJ": ws.Range(f"{c}27").Formula = f"=SUM({c}2:{c}26)"
    for c in "CDFHIJK": ws.Range(f"{c}2:{c}27").NumberFormat = "#,##0"
    ws.Range("G2:G26").NumberFormat = "0.00"
    ws.Range("E1:E27").Font.Color = GREY
    ws.Range("F1:F26").Interior.Color = BLUE
    for c in "CDEFJ": ws.Columns(c).ColumnWidth = ws.Columns("B").ColumnWidth
    ws.Rows(1).WrapText = True

    ww = wb.Worksheets("WW Generation")
    assert ww.Range("A27").Value == "Total" and ww.Range("BX1").Value == 2100
    ww.Range("B2:BX26").Formula = "=MIN(Average!B2,'MOHUP DATA - NA'!$K2)*'Base Demand'!$H$4/1000+'Base Demand'!$C7"
    ww.Rows(27).Insert()
    ww.Range("A27").Value = "INDUSTRIAL ESTATES (6,300 workers x 93 L/d x 0.54)"
    ww.Range("B27:BX27").Formula = "=0.54*93*(4500+1800)/1000"
    ww.Range("B28:BX28").Formula = "=SUM(B2:B27)"
    ww.Range("B27:BX27").NumberFormat = ww.Range("B26").NumberFormat

    nt = wb.Worksheets.Add(); nt.Name = "Notes (W18)"
    nt.Move(None, wb.Sheets(wb.Sheets.Count))        # to the end (late binding drops Add's After= keyword)
    notes = ["Changes to the team's workbook (2026-11-17); every other sheet is as received.",
             "",
             "MOHUP DATA - NA",
             "C  Existing Population 2026: the 2026 average population (sheet Average).",
             "D  Existing Residential Plots: existing Residential + Residential-Commercial plots (sheet Base MOHUP Data - NA, F + G).",
             "E  Future Residential Plots (MoHUP zoning): the team's count, in grey: no longer used.",
             "F  Future Plots (growth plots), shaded blue: future plots inside the settlement boundary, 200-3,000 m2, not odd-shaped",
             "   (compactness >= 0.6, length <= 3 x width), any zoning except agricultural, tourism (heritage) and industrial,",
             "   not a grove on the satellite check and not an estate plot. Counted on the plot layer; typed values.",
             "G  Residential Properties per Plot = MAX(1, B / D): the team's figure, now a formula.",
             "H  Future Residential Properties = F x G.      I  Total Residential Properties = B + H.",
             "J  Future Population = H x 4.8.",
             "K  Total Population Capacity = C + J: the existing properties keep the people they have in 2026, the new ones 4.8 each",
             "   (before: (existing + future properties) x 4.8, which counted the existing properties at 4.8 people).",
             "L  Saturation Year: the first year the average population reaches K (COUNTIF, so it computes in any spreadsheet app).",
             "",
             "WW Generation",
             "Each settlement and year: MIN(average population, capacity K) x 171.03 L/person/day + the settlement's infiltration",
             "(Base Demand, column C): a settlement stops growing when its empty plots are full (before: no cap).",
             "Row 27: the two industrial estates, 6,300 workers x 93 L/d x 0.54 = 316.4 m3/d (Al Tayyeb 4,500, Tanam 1,800).",
             "Not subtracted: the flow of plots the network does not reach (inactive manholes, over 200 m from a sewer):",
             "it is generated, but not carried."]
    for i, t in enumerate(notes, 1): nt.Range(f"A{i}").Value = t
    nt.Range("A1").Font.Bold = True; nt.Columns("A").ColumnWidth = 130
    ws.Activate()
    xl.CalculateFull()
    wb.Save()
    wb.Close(False)
finally:
    xl.Quit()

# checks on the saved copy
c = openpyxl.load_workbook(DST, data_only=True); f = openpyxl.load_workbook(DST)
s, w, a = c["MOHUP DATA - NA"], c["WW Generation"], c["Average"]
rate = c["Base Demand"]["H4"].value / 1000.0
infil = sum(c["Base Demand"].cell(r, 3).value or 0 for r in range(7, 32))
assert [x.title for x in f.worksheets] == [x for x in openpyxl.load_workbook(SRC).sheetnames if x != "Chart1"] + ["Notes (W18)"], [x.title for x in f.worksheets]
import zipfile; assert any(n.startswith("xl/charts/chart") for n in zipfile.ZipFile(DST).namelist()), "the chart is gone"
for r in range(N0, N1 + 1):
    assert abs(s[f"G{r}"].value - md.cell(r, 4).value) < 1e-9, ("properties per plot", r)
    assert s[f"E{r}"].value == md.cell(r, 3).value and s[f"F{r}"].value == ours[names[r - N0]]
    assert abs(s[f"K{r}"].value - (a[f"B{r}"].value + s[f"F{r}"].value * s[f"G{r}"].value * 4.8)) < 1e-6
print(f"capacity {s['K27'].value:,.0f}; Ibri {s['K18'].value:,.0f}, full {s['L18'].value}")
for y in (2031, 2056, 2071, 2091):
    col = next(cc for cc in range(2, 77) if w.cell(1, cc).value == y)
    tot = w.cell(28, col).value
    want = sum(min(a.cell(r, col).value, s[f"K{r}"].value) for r in range(N0, N1 + 1)) * rate + infil + 316.386
    assert abs(tot - want) < 0.01, (y, tot, want)
    print(f"WW Generation {y}: {tot:,.1f} m3/d (estates {w.cell(27, col).value:.1f}, infiltration {infil:,.1f})")
print(DST)
