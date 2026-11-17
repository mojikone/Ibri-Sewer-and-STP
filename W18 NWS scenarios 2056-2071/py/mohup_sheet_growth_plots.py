"""The team's sheet 'MOHUP DATA - NA' with OUR growth plots in place of their future residential plots (engineer,
2026-11-17): column C = the growth plots of each settlement in gis/W18_plots_2026_2100.shp (future, inside the
settlement boundary, 200-3,000 m2, not odd-shaped, any zoning but agricultural / heritage / industrial, no grove or
estate); columns E-H keep the team's formulas, so properties, capacity and saturation year follow.
Sheets written:
  'MOHUP DATA - NA'   the updated copy (C changed, team's C, G and H alongside for comparison)
  'Team original'     the team's sheet untouched (live formulas)
  'Average'           the team's average population 2026-2100 as values (the saturation-year formula reads it)
  'Notes'             what changed
Then Excel recalculates and saves once, so the file opens with values on a phone.
Writes results/W18_MOHUP_DATA_NA_growth_plots.xlsx.  Usage: python mohup_sheet_growth_plots.py"""
import os, subprocess
import openpyxl, pyogrio
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.comments import Comment

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
WB = os.path.join(W18, "..", "..", "temp", "recent updates by the team", "New Calculation MH.xlsx")
PLOTS = os.path.join(W18, "gis", "W18_plots_2026_2100.shp")
OUT = os.path.join(W18, "results", "W18_MOHUP_DATA_NA_growth_plots.xlsx")
SHEET = "MOHUP DATA - NA"

p = pyogrio.read_dataframe(PLOTS, columns=["SETTLE", "GROWTH"], read_geometry=False)
ours = p.groupby(p.SETTLE.str.strip().str.upper()).GROWTH.sum().astype(int).to_dict()

vals = openpyxl.load_workbook(WB, data_only=True)
wb = openpyxl.load_workbook(WB)
for name in list(wb.sheetnames):                      # keep only the sheet and the population it reads
    if name not in (SHEET, "Average"): del wb[name]
av, avv = wb["Average"], vals["Average"]              # Average as values: its sources are not carried
for row in av.iter_rows():
    for c in row: c.value = avv[c.coordinate].value
ws = wb[SHEET]
team = wb.copy_worksheet(ws); team.title = "Team original"
for col, d in ws.column_dimensions.items(): team.column_dimensions[col].width = d.width

fill = PatternFill("solid", fgColor="DDEBF7")
names = {}
for r in range(2, 27):
    s = ws.cell(r, 1).value.strip().upper(); names[s] = r
    assert s in ours, s
    ws.cell(r, 3).value = ours[s]; ws.cell(r, 3).fill = fill
assert set(names) == set(ours), "settlement names differ between the sheet and the plot layer"
assert sum(ours.values()) == int(p.GROWTH.sum())
ws["C1"] = "Future Plots (our growth plots)"; ws["C1"].fill = fill
ws["C1"].comment = Comment("Growth plots of the plot layer: future, inside the settlement boundary, 200-3,000 m2, "
                           "not odd-shaped, any zoning except agricultural, tourism (heritage) and industrial, "
                           "no grove or estate. The team's count is in column J and on sheet 'Team original'.", "W18")
for c, h in zip("JKL", ["Team's Future Residential Plots", "Team's Total Population Capacity", "Team's Saturation Year"]):
    ws[f"{c}1"] = h; ws[f"{c}1"].font = Font(bold=True); ws[f"{c}1"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.column_dimensions[c].width = 16
ws["I1"] = None
for r in range(2, 27):
    ws[f"J{r}"] = f"='Team original'!C{r}"; ws[f"J{r}"].number_format = "#,##0"
    ws[f"K{r}"] = f"='Team original'!G{r}"; ws[f"K{r}"].number_format = "#,##0"
    ws[f"L{r}"] = f"='Team original'!H{r}"
ws["J27"] = "=SUM(J2:J26)"; ws["K27"] = "=SUM(K2:K26)"
for c in ("J27", "K27"): ws[c].number_format = "#,##0"; ws[c].font = Font(bold=True)

nt = wb.create_sheet("Notes")
notes = ["What changed against the team's sheet 'MOHUP DATA - NA'",
         "",
         "Column C: the growth plots of each settlement in our plot layer, in place of the future plots zoned Residential and Residential-Commercial.",
         "A growth plot is future, inside its settlement boundary, 200-3,000 m2, not odd-shaped (compactness >= 0.6, length <= 3 x width),",
         "of any zoning except agricultural, tourism (heritage) and industrial, and not a grove on the satellite check or an estate plot.",
         "Columns B and D are the team's (existing properties, properties per plot); E, F, G and H keep the team's formulas.",
         "Columns J-L repeat the team's own plot count, capacity and saturation year; sheet 'Team original' is their sheet unchanged.",
         "Sheet 'Average' is the team's average population (NCSI, meters x 4.8, APSR) 2026-2100, copied as values.",
         "",
         "Note: the capacity G still counts existing properties at 4.8 people, while the 2026 population puts more on them in most settlements",
         "(Ibri 5.99 per property)."]
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

chk = openpyxl.load_workbook(OUT, data_only=True)[SHEET]
print(f"{'settlement':18}{'ours':>7}{'team':>7}{'capacity':>10}{'team cap':>10}{'full':>8}{'team':>8}")
for r in range(2, 28):
    g = [chk.cell(r, c).value for c in (1, 3, 10, 7, 11, 8, 12)]
    print(f"{g[0]:18}{g[1]:>7,}{g[2]:>7,}{g[3]:>10,.0f}{g[4]:>10,.0f}{str(g[5] or ''):>8}{str(g[6] or ''):>8}")
print(OUT)
