"""Three sheets, each with the simple conversion on top and the same table with the values
below it: the electricity tariffs to the NAMA demand categories, the plot uses to the meters
that infer them, the NAMA categories to the tariffs and plot uses that carry them. Counts read
from the frozen W14 layers (the meters, the plots with the report's one override).

    python meter_tariff_table.py   ->  meter_tariff_to_nama_category.xlsx
"""
import collections
import os
import sys

import geopandas as gpd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "W16", "report"))
import facts_w14 as F  # noqa: E402

m = gpd.read_file(os.path.join(REPO, "W14", "shp", "ELE_meters_on_plots.shp"))
p = F.plots()
n = collections.Counter(m["TARIFF"])
crt = m[m["GROUP"] == "crt"]
u = collections.Counter(crt["USE"].fillna("Unresolved"))
gud = collections.Counter(m["GUD"])
der = collections.Counter(p["DERIVED"])
met = collections.Counter(p.loc[p["Buiding_St"] == "EXisting", "DERIVED"])
free = int((m["PLACE"] == "free").sum())
water = {k: float(p[c].sum()) for k, c in (("dom", "W_DOM"), ("ndom", "W_NDOM"), ("gov", "W_GOV"), ("spec", "W_SPEC"))}
sew = {k: float(p[c].sum()) for k, c in (("dom", "S_DOM"), ("ndom", "S_NDOM"), ("gov", "S_GOV"), ("spec", "S_SPEC"))}
fut_status = int((p["Buiding_St"] == "Future").sum())

DOM_T = "Primary Account Tariff; Primary Account Tariff (with National Subsidy); Additional Account Tariff"
COM_T = "Commercial; Fisheries; Tourism; CRT accounts found to be shops, malls, fuel, banks, telecom or unresolved"
GOV_T = "Government; MOD; CRT accounts found to be government, education, health or religious"
AGR_T = "Agricultural; CRT accounts found to be farm pumps"
SPEC_T = "Industrial; CRT accounts found to be industrial (Tanam estate)"

# ------------------------------------------------------------ sheet 1: tariff -> category -> use
CRT_N = n["CRT Seasonal"] + n["CRT Time of Use"] + n["CRT Fixed Rate"]
S1 = [  # tariff, meters, NAMA category, water rate, return, plot use, rule
    ("Primary Account Tariff", n["Primary Account Tariff"], "Domestic", "164 l/person/d x the settlement's persons per property (G201 Table 11, Adh Dhahirah)", "85 % (Table 19)", "Residential", "one property per meter"),
    ("Primary Account Tariff (with National Subsidy)", n["Primary Account Tariff (with National Subsidy)"], "Domestic", "same", "85 %", "Residential", "one property per meter"),
    ("Additional Account Tariff", n["Additional Account Tariff"], "Domestic", "same", "85 %", "Residential", "a further property on the same plot"),
    ("Commercial", n["Commercial"], "Non-domestic", "share of the 22 % of domestic (G201 Table 11, distributed ratio)", "54 % (Table 19)", "Commercial; Residential-Commercial when the plot also carries domestic meters", "placed on the shop meters in proportion"),
    ("Fisheries", n["Fisheries"], "Non-domestic", "22 % share", "54 %", "Commercial", ""),
    ("Tourism", n["Tourism"], "Non-domestic", "22 % share", "54 %", "Commercial", ""),
    ("Government", n["Government"], "Governmental", "share of the 14 % of domestic (G201 Table 11, distributed ratio)", "54 %", "Government", "placed on the government meters in proportion"),
    ("MOD", n["MOD"], "Governmental", "14 % share", "54 %", "Government", ""),
    ("Agricultural", n["Agricultural"], "Agricultural (irrigation pump)", "none: no sewage", "-", "Agricultural; Residential when a house is metered on the farm", "the farm carries no load, the house on it does"),
    ("Industrial", n["Industrial"], "Special consumption", "93 l/worker/d, dry industry (G201 Table 12)", "54 %", "Industrial", ""),
    ("CRT Seasonal; CRT Time of Use; CRT Fixed Rate", CRT_N, "a consumption class (over 150 MWh/yr), not a use: each account resolved from public data, split below", "", "", "", "OpenStreetMap, reverse geocoding, satellite by eye, the identified-projects search"),
    ("   CRT found: shops, malls, fuel, banks, telecom, unresolved", u["Commercial"] + u["Telecom/Utility"] + u["Unresolved"], "Non-domestic", "22 % share", "54 %", "Commercial / Residential-Commercial", f"{u['Unresolved']} unresolved accounts kept as non-domestic, flagged"),
    ("   CRT found: government, education, health, religious", u["Government"] + u["Education"] + u["Health"] + u["Religious"], "Governmental", "14 % share", "54 %", "Government", ""),
    ("   CRT found: industrial (Tanam estate)", u["Industrial"], "Special consumption", "93 l/worker/d", "54 %", "Industrial", ""),
    ("   CRT found: farm pumps (Al Aynayn)", u["Agricultural"], "Agricultural", "none", "-", "Agricultural", ""),
]
assert sum(r[1] for r in S1[:11]) == len(m), (sum(r[1] for r in S1[:11]), len(m))
assert sum(r[1] for r in S1[11:]) == CRT_N, (sum(r[1] for r in S1[11:]), CRT_N)

# ------------------------------------------------------------ sheet 2: plot use <- meters and evidence
S2 = [  # use, plots, metered plots, meter types inferred as this use, other evidence, rule (in the order applied), load it carries
    ("Residential", der["Residential"], met["Residential"], DOM_T, "none",
     "domestic meters are more than two-thirds of the plot's meters", "domestic: persons per property x 164 l/d; the minority shop or government meters keep their share"),
    ("Residential-Commercial", der["Residential-Commercial"], met["Residential-Commercial"], "domestic tariffs with shop tariffs (Commercial, Fisheries, Tourism, CRT shops) on one plot", "none",
     "no category reaches two-thirds and shop meters are at least as many as government meters", "domestic and non-domestic, each on its own meters"),
    ("Commercial", der["Commercial"], met["Commercial"], COM_T, "none",
     "shop meters are two-thirds or more of the plot's meters", "non-domestic: its share of the 22 %; any domestic meters on it keep theirs"),
    ("Government", der["Government"], met["Government"], GOV_T, "the treatment plant's compound (farm meters for its pumps), set by hand",
     "government meters are two-thirds or more; or a mix where government meters outnumber shop meters", "governmental: its share of the 14 %; any domestic meters on it keep theirs"),
    ("Agricultural", der["Agricultural"], met["Agricultural"], AGR_T, "planted, by satellite: green area of 1,000 m2 or more at NDVI 0.20, or 60 % green at NDVI 0.40 on a plot of 800 m2 or more",
     "a farm meter on the plot; or planted, unless the plot's meters are two-thirds shops or over half government", "none for the farm; a house metered on it carries its domestic load"),
    ("Industrial", der["Industrial"], met["Industrial"], SPEC_T + "; the estates' Commercial-tariff meters sit on these plots but do not decide the use", "inside the Al Tayyeb or Tanam estate footprint (identified projects)",
     "inside an estate footprint; or special-consumption meters at least as many as domestic", "special consumption: the estate's assumed workforce (4,500 and 1,800) spread by plot area at 93 l/worker/d"),
    ("Heritage", der["Heritage"], met["Heritage"], "none: no meter on these plots", "the cadastre's Tourism class (the old quarters)",
     "the cadastre class is Tourism", "none"),
    ("Empty (unmetered)", der["Unmetered"], met["Unmetered"], "none: no meter of any tariff", "not planted, not heritage, not in an estate; the cadastre's Proposed plots fall here when unmetered",
     "no meter and no other evidence", "future people: home-shaped plots at 171.3 l/d per person as the settlement fills"),
]
assert sum(r[1] for r in S2) == len(p), (sum(r[1] for r in S2), len(p))

# ------------------------------------------------------------ sheet 3: NAMA category <- tariffs and uses
S3 = [  # category, meters, tariffs folded in, plot uses that carry its load, rate, return, water 2024, sewage 2024
    ("Domestic", gud["domestic"], DOM_T, "Residential; Residential-Commercial; the dwelling meters on farm, shop and government plots",
     "164 l/person/d x persons per property", "85 %", water["dom"], sew["dom"]),
    ("Non-domestic", gud["non_domestic"], COM_T, "Commercial; Residential-Commercial; the shop meters on other plots",
     "22 % of the settlement's domestic water, placed on its shop meters", "54 %", water["ndom"], sew["ndom"]),
    ("Governmental", gud["government"], GOV_T, "Government; the government meters on other plots",
     "14 % of the settlement's domestic water, placed on its government meters", "54 %", water["gov"], sew["gov"]),
    ("Agricultural", gud["agricultural"], AGR_T, "Agricultural (farm meters and planted plots)",
     "none: irrigation, no sewage", "-", 0.0, 0.0),
    ("Special consumption", gud["special"], SPEC_T, "Industrial (the two estates' plots, by area)",
     "93 l/worker/d on the assumed workforce (4,500 Al Tayyeb, 1,800 Tanam)", "54 %", water["spec"], sew["spec"]),
]
assert sum(r[1] for r in S3) == len(m)

NOTES = [
    ("Empty and Proposed", f"Empty is a plot with no meter and no other evidence: {der['Unmetered']:,} plots. The cadastre's Proposed class (49 plots) is not a use of its own: 38 are unmetered and count as empty, 11 carry meters and take their use from them. The report's figure of {fut_status:,} empty plots is the cadastre's Future status, which also holds {der['Agricultural'] - met['Agricultural']:,} planted plots, {der['Heritage']} heritage plots and {der['Industrial'] - met['Industrial']} unbuilt estate plots; none of those carries future people."),
    ("Industrial estates", "Al Tayyeb and Tanam are metered as Commercial (1,035 and 409 meters). The estate footprint decides the use; the plots carry the assumed workforce, not the shop share."),
    ("Heritage", "The old quarters (177 plots) come from the cadastre's Tourism class, carry no meter and no load."),
    ("Meters on no plot", f"{free} meters lie more than 15 m from any plot and carry nothing until NWS says whether to assign or leave them (Design Basis Report, Section 3.3)."),
    ("Water and sewage 2024", "The sums of the plot layer's 2024 water and sewage by category, m3/d, after the return ratios; the same figures the report's Table 6 builds on."),
    ("Source", "W14/shp/ELE_meters_on_plots.shp (33,971 accounts, 2024) and W14/shp/PLOTS_load.shp (77,265 plots) with the report's one override (the treatment plant's compound as Government); rules in W14/py/plot_class_v2_apply.py; categories per PAM-GUD-201 section 7.3; rates Table 11 (p60) and Table 19 (p71)."),
]

# ------------------------------------------------------------ the workbook
NAVY = PatternFill("solid", fgColor="1F497D"); LIGHT = PatternFill("solid", fgColor="F3F6FA")
RULE = Border(bottom=Side(style="thin", color="D9D9D9"))


def block(ws, row, title, headers, rows, widths=None, numeric=(), bold_rows=()):
    """A titled table starting at row; returns the next free row."""
    ws.cell(row, 1, title).font = Font(bold=True, size=12, color="1F497D"); row += 1
    for j, h in enumerate(headers, 1):
        c = ws.cell(row, j, h); c.fill = NAVY; c.font = Font(bold=True, color="FFFFFF"); c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 30; row += 1
    for i, r in enumerate(rows):
        for j, v in enumerate(r, 1):
            c = ws.cell(row, j, v); c.border = RULE; c.font = Font(bold=i in bold_rows)
            c.alignment = Alignment(vertical="center", wrap_text=True, horizontal="right" if j in numeric else "left")
            if j in numeric:
                c.number_format = "#,##0"
            if i % 2 == 0:
                c.fill = LIGHT
        row += 1
    if widths:
        for j, w in enumerate(widths, 1):
            cur = ws.column_dimensions[get_column_letter(j)].width or 0
            ws.column_dimensions[get_column_letter(j)].width = max(cur, w)
    return row + 2


wb = Workbook()
ws = wb.active; ws.title = "1 Tariff"
r = block(ws, 1, "Electricity tariff  >  NAMA demand category  >  plot use", ["Electricity tariff (as received)", "NAMA water demand category", "Plot use it gives"],
          [(a, c, f) for a, b, c, d, e, f, g in S1], widths=(50, 14, 46), bold_rows=(10,))
block(ws, r, "The same, with the values", ["Electricity tariff (as received)", "Meters", "NAMA water demand category (PAM-GUD-201 s7.3)", "Water rate applied", "Return to sewer", "Plot use it gives", "Rule"],
      S1, widths=(50, 14, 46, 46, 16, 46, 46), numeric=(2,), bold_rows=(10,))
ws.cell(r + 2 + len(S1) + 1, 1, "The four CRT lines split the CRT line above them; the tariff lines sum to every meter.").font = Font(italic=True, color="808080")

ws = wb.create_sheet("2 Plot use")
r = block(ws, 1, "Plot use  <  the meter types read as that use, and the other evidence", ["Plot use", "Meter types inferred as this use", "Other evidence (not a meter)"],
          [(a, d, e) for a, b, c, d, e, f, g in S2], widths=(26, 60, 60))
block(ws, r, "The same, with the values", ["Plot use", "Plots", "of which with meters", "Meter types inferred as this use", "Other evidence (not a meter)", "Rule, in the order applied", "Load it carries"],
      S2, widths=(26, 10, 12, 60, 60, 60, 60), numeric=(2, 3))

ws = wb.create_sheet("3 NAMA category")
r = block(ws, 1, "NAMA demand category  <  the tariffs folded into it, and the plot uses that carry it", ["NAMA water demand category", "Electricity tariffs folded in", "Plot uses that carry its load"],
          [(a, c, d) for a, b, c, d, e, f, g, h in S3], widths=(26, 70, 60))
rows3 = [(a, b, c, d, e, f, round(g), round(h)) for a, b, c, d, e, f, g, h in S3]
block(ws, r, "The same, with the values", ["NAMA water demand category", "Meters", "Electricity tariffs folded in", "Plot uses that carry its load", "Water rate", "Return to sewer", "Water 2024, m3/d", "Sewage 2024, m3/d"],
      rows3, widths=(26, 10, 70, 60, 50, 14, 16, 16), numeric=(2, 7, 8))

ws = wb.create_sheet("Notes")
block(ws, 1, "Notes", ["Item", "Note"], NOTES, widths=(24, 130))
for w in wb.worksheets:
    w.sheet_view.showGridLines = False

out = os.path.join(HERE, "meter_tariff_to_nama_category.xlsx"); wb.save(out)
print("wrote", out, "|", len(m), "meters |", len(p), "plots | water 2024", round(sum(water.values())), "m3/d")
