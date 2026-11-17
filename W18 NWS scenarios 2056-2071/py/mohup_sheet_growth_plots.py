"""The team's sheet 'MOHUP DATA - NA' rebuilt on the engineer's capacity rule (2026-11-17), every cell a live formula
except the inputs:
  existing population  = the team's average population of 2026 (NCSI, meters x 4.8, APSR), linked to sheet 'Average'
  future plots         = OUR growth plots per settlement in gis/W18_plots_2026_2100.shp (future, inside the settlement
                         boundary, 200-3,000 m2, not odd-shaped, any zoning but agricultural / heritage / industrial,
                         no grove or estate)
  properties per plot  = the team's calculation: existing residential properties / existing residential and
                         residential-commercial plots (their 'Base MOHUP Data - NA'), not below 1 as they set it
  future population    = future plots x properties per plot x persons per new property (4.8, one input cell)
  capacity             = existing population + future population
  saturation year      = first year the team's average population reaches the capacity
Sheets: 'MOHUP DATA - NA' (this), 'Team original' (their sheet, live), 'Average' (their population as values), 'Notes'.
Excel recalculates and saves once, so the file opens with values on a phone.
Writes results/W18_MOHUP_DATA_NA_growth_plots.xlsx.  Usage: python mohup_sheet_growth_plots.py"""
import os, subprocess
import openpyxl, pyogrio
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.comments import Comment

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
WB = os.path.join(W18, "..", "..", "temp", "recent updates by the team", "New Calculation MH.xlsx")
PLOTS = os.path.join(W18, "gis", "W18_plots_2026_2100.shp")
OUT = os.path.join(W18, "results", "W18_MOHUP_DATA_NA_growth_plots.xlsx")
SHEET = "MOHUP DATA - NA"; N0, N1 = 2, 26; TOT = 27; PAR = 29

p = pyogrio.read_dataframe(PLOTS, columns=["SETTLE", "GROWTH"], read_geometry=False)
ours = p.groupby(p.SETTLE.str.strip().str.upper()).GROWTH.sum().astype(int).to_dict()

vals = openpyxl.load_workbook(WB, data_only=True)
base = vals["Base MOHUP Data - NA"]; exres = {}
for r in range(3, 30):                               # existing Residential (F) + Residential-Commercial (G) plots
    n = base.cell(r, 1).value
    if n and n.strip() != "Total" and n.strip().upper() not in exres:
        exres[n.strip().upper()] = (base.cell(r, 6).value or 0) + (base.cell(r, 7).value or 0)

wb = openpyxl.load_workbook(WB)
for name in list(wb.sheetnames):                      # keep only the sheet and the population it reads
    if name not in (SHEET, "Average"): del wb[name]
av, avv = wb["Average"], vals["Average"]              # Average as values: its sources are not carried
for row in av.iter_rows():
    for c in row: c.value = avv[c.coordinate].value
team = wb[SHEET]; team.title = "Team original"
ws = wb.create_sheet(SHEET)

H = ["Settlements", "Existing Residential Properties", "Existing Population 2026 (average)", "Existing Residential Plots",
     "Residential Properties per Plot", "Future Plots (our growth plots)", "Future Residential Properties",
     "Total Residential Properties", "Future Population", "Total Population Capacity", "Saturation Year", None,
     "Team's Future Residential Plots", "Team's Total Population Capacity", "Team's Saturation Year"]
WID = [17, 13, 14, 12, 12, 13, 13, 13, 13, 14, 13, 3, 14, 15, 13]
blue, grey = PatternFill("solid", fgColor="DDEBF7"), PatternFill("solid", fgColor="F2F2F2")
thin = Border(bottom=Side(style="thin"))
for j, (h, w) in enumerate(zip(H, WID), 1):
    c = ws.cell(1, j, h); c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    c.border = thin; ws.column_dimensions[c.column_letter].width = w
    if j >= 13: c.fill = grey
ws.row_dimensions[1].height = 45; ws["F1"].fill = blue
ws["F1"].comment = Comment("Growth plots of the plot layer: future, inside the settlement boundary, 200-3,000 m2, "
                           "not odd-shaped, any zoning except agricultural, tourism (heritage) and industrial, "
                           "no grove or estate.", "W18")
INT, DEC = "#,##0", "0.00"
names = []
for r in range(N0, N1 + 1):
    n = team.cell(r, 1).value; k = n.strip().upper(); names.append(k)
    assert av.cell(r, 1).value.strip().upper() == k, ("Average row order", r, k)
    assert k in ours and k in exres, k
    row = {"A": n, "B": f"='Team original'!B{r}", "C": f"=Average!B{r}", "D": exres[k],
           "E": f"=MAX(1,B{r}/D{r})", "F": ours[k], "G": f"=F{r}*E{r}", "H": f"=B{r}+G{r}",
           "I": f"=G{r}*$B${PAR}", "J": f"=C{r}+I{r}",
           "K": f'=IFERROR(INDEX(Average!$B$1:$BX$1,MATCH(TRUE,INDEX(Average!$B{r}:$BX{r}>=$J{r},0),0)),"Not Fully Occupied")',
           "M": f"='Team original'!C{r}", "N": f"='Team original'!G{r}", "O": f"='Team original'!H{r}"}
    for col, v in row.items():
        c = ws[f"{col}{r}"]; c.value = v
        c.number_format = DEC if col == "E" else INT
        if col in "KO": c.alignment = Alignment(horizontal="center")
    ws[f"F{r}"].fill = blue
assert set(names) == set(ours) and sum(ours.values()) == int(p.GROWTH.sum())
ws[f"A{TOT}"] = "Total"
for col in "BCDFGHIJMN":
    c = ws[f"{col}{TOT}"]; c.value = f"=SUM({col}{N0}:{col}{N1})"; c.number_format = INT
for col in "ABCDEFGHIJKMNO": ws[f"{col}{TOT}"].font = Font(bold=True); ws[f"{col}{TOT}"].border = Border(top=Side(style="thin"))
ws[f"A{PAR}"] = "Persons per new property"; ws[f"B{PAR}"] = 4.8; ws[f"B{PAR}"].fill = blue; ws[f"A{PAR}"].font = Font(bold=True)
ws.freeze_panes = "B2"

nt = wb.create_sheet("Notes")
notes = ["How sheet 'MOHUP DATA - NA' is calculated (inputs shaded blue; every other cell is a formula)",
         "",
         "B  Existing Residential Properties: the team's figure (domestic electricity accounts).",
         "C  Existing Population 2026: the team's average population of 2026 (NCSI, meters x 4.8 and APSR), from sheet 'Average'.",
         "D  Existing Residential Plots: the team's count of existing plots zoned Residential and Residential-Commercial.",
         "E  Residential Properties per Plot = B / D, not below 1 (the team set Miayrid to 1).",
         "F  Future Plots: the growth plots of each settlement in our plot layer: future, inside the settlement boundary, 200-3,000 m2,",
         "   not odd-shaped (compactness >= 0.6, length <= 3 x width), any zoning except agricultural, tourism (heritage) and industrial,",
         "   and not a grove on the satellite check or an estate plot.",
         "G  Future Residential Properties = F x E.      H  Total Residential Properties = B + G.",
         "I  Future Population = G x persons per new property (cell B29, 4.8).",
         "J  Total Population Capacity = C + I: the existing properties keep the people they have in 2026, the new ones take 4.8 each.",
         "K  Saturation Year: the first year the team's average population reaches J ('Not Fully Occupied' if not by 2100).",
         "M-O  The team's own plot count, capacity and saturation year; sheet 'Team original' is their sheet unchanged.",
         "",
         "The team's capacity is (B + G) x 4.8, which counts the existing properties at 4.8 people while the 2026 population",
         "puts more on them in most settlements (Ibri 5.98 per property)."]
for i, t in enumerate(notes, 1): nt.cell(i, 1, t)
nt["A1"].font = Font(bold=True); nt.column_dimensions["A"].width = 140
wb._sheets = [wb[SHEET], wb["Team original"], wb["Average"], wb["Notes"]]
wb.active = 0
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)

# Excel recalculates and saves once (openpyxl writes formulas without values)
ps = (f"$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false; "
      f"$w = $x.Workbooks.Open('{OUT}'); $x.CalculateFull(); $w.Save(); $w.Close($false); $x.Quit(); "
      f"[void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($x)")
subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)

chk = openpyxl.load_workbook(OUT, data_only=True)
s, t = chk[SHEET], chk["Team original"]
for r in range(N0, N1 + 1):                          # the team's ratio reproduced, the capacity adds up
    assert abs(s[f"E{r}"].value - t[f"D{r}"].value) < 1e-9, (r, s[f"E{r}"].value, t[f"D{r}"].value)
    assert abs(s[f"J{r}"].value - (s[f"C{r}"].value + s[f"F{r}"].value * s[f"E{r}"].value * 4.8)) < 1e-6
print(f"{'settlement':17}{'exist pop':>10}{'plots':>7}{'prop/plot':>10}{'fut pop':>9}{'capacity':>10}{'full':>8}{'team cap':>10}{'team':>8}")
for r in range(N0, TOT + 1):
    g = [s[f"{c}{r}"].value for c in "ACFEIJKNO"]
    print(f"{g[0]:17}{g[1]:>10,.0f}{g[2]:>7,}{(g[3] or 0):>10.4f}{g[4]:>9,.0f}{g[5]:>10,.0f}{str(g[6] or ''):>8}{g[7]:>10,.0f}{str(g[8] or ''):>8}")
print(OUT)
