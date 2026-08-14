# -*- coding: utf-8 -*-
"""Tutorial T01 — Sewage Flow & Load Calculation, styled on Data/sample report/Sample.docx.
Same style pattern as W2/report/make_report_r1.py. Refs: p## = PAM-GUD-203, G1-p## = PAM-GUD-201,
G2-p## = PAM-GUD-202, R0 = Ibri Inception Report R0 demand workbook (Aug 2026)."""
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SAMPLE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\sample report\Sample.docx"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "T01_Sewage_Flow_and_Load_Calculation.docx")
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
PROJ = "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri"
SUB = "Tutorial T01 — Sewage Flow and Pollution Load Calculation"

# ---------- flow-chain diagram (matplotlib) ----------
CHAIN = os.path.join(IMG, "t01_chain.png")
def make_chain():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    steps = [
        ("1  Population", "NCSI census / plots x occupancy"),
        ("2  Water demand", "domestic 164 + 22% + 14% l/c/d"),
        ("3  Wastewater return", "85% domestic / 54% non-dom & gov"),
        ("4  Additions", "infiltration + tankers"),
        ("5  Average flow Qadf", "annual average (AAF)"),
        ("6  Peak flows", "Peltier / Merrimack, PF <= 5"),
        ("7  Organic loads", "60 g BOD5 / 80 g TSS per cap/d"),
        ("8  STP sizing", "AAF + loads (biology), PHF (hydraulics), +10%"),
        ("9  TSE output", "95% of STP inlet -> TE network"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 8.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, len(steps) * 1.15); ax.axis("off")
    boxes = []
    for i, (t, s) in enumerate(steps):
        y = (len(steps) - 1 - i) * 1.15
        b = FancyBboxPatch((1.2, y + 0.08), 7.6, 0.86, boxstyle="round,pad=0.06",
                           fc="#EAF1FB", ec="#2E5C9E", lw=1.4)
        ax.add_patch(b)
        ax.text(5.0, y + 0.62, t, ha="center", va="center", fontsize=12, fontweight="bold", color="#1F3A64")
        ax.text(5.0, y + 0.28, s, ha="center", va="center", fontsize=9.5, color="#444444")
        boxes.append(y)
    for i in range(len(steps) - 1):
        ax.add_patch(FancyArrowPatch((5.0, boxes[i] + 0.06), (5.0, boxes[i + 1] + 0.96),
                                     arrowstyle="-|>", mutation_scale=16, color="#2E5C9E", lw=1.4))
    fig.savefig(CHAIN, dpi=200, bbox_inches="tight")
    plt.close(fig)
make_chain()

# ---------- document shell ----------
doc = Document(SAMPLE)
body = doc.element.body
sect = body.find(qn("w:sectPr"))
for el in list(body):
    if el is not sect:
        body.remove(el)

def patch_part(part):
    xml = part._element
    first = True
    for t in xml.iter(qn("w:t")):
        if first:
            t.text = PROJ + " — " + SUB
            first = False
        else:
            t.text = ""
for s in doc.sections:
    for hd in (s.header, s.first_page_header, s.even_page_header):
        if hd is not None: patch_part(hd)

def para(text, style=None, align=None, bold=None, size=None, color=None, space_after=6):
    p = doc.add_paragraph(style=style)
    r = p.add_run(text)
    if bold is not None: r.bold = bold
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if align is not None: p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p
def H(level, text):
    return doc.add_paragraph(text, style=f"Heading {level}")
_styles = {s_.name for s_ in doc.styles}
def bullet(text):
    if "List Bullet" in _styles:
        return doc.add_paragraph(text, style="List Bullet")
    p = doc.add_paragraph("• " + text)
    p.paragraph_format.left_indent = Inches(0.3)
    return p
def caption(text):
    try:
        p = doc.add_paragraph(text, style="Caption")
    except KeyError:
        p = para(text, bold=True, size=10)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p
def pic(path, w=6.0):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(w))
def shade(cell, hexc):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), hexc)
    tcPr.append(sh)
def table(headers, rows, widths=None, font=9):
    t = doc.add_table(rows=1, cols=len(headers))
    try: t.style = "Table Grid"
    except KeyError: pass
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(font)
        shade(c, "D9E2F3")
    for row in rows:
        cs = t.add_row().cells
        for i, v in enumerate(row):
            cs[i].text = ""
            r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(font)
    if widths:
        for i, w in enumerate(widths):
            for r_ in t.rows:
                r_.cells[i].width = Inches(w)
    return t
def pagebreak():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
def toc():
    p = doc.add_paragraph()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), r'TOC \o "1-2" \h \z \u')
    r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = "Right-click and Update Field to refresh the Table of Contents."
    r.append(t); fld.append(r); p._p.append(fld)

# ================= COVER =================
para("", space_after=60)
para("Sultanate of Oman", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)
para("Nama Water Services Company SAOC (NWS / OWWSC)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
para("", space_after=40)
try:
    para(PROJ, style="Title", align=WD_ALIGN_PARAGRAPH.CENTER)
except KeyError:
    para(PROJ, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=24)
para("Tender No. T/2719110/2025", align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
para("", space_after=40)
para(SUB, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=20, color="0000CC")
para("Revision 0 — August 2026", align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
para("", space_after=80)
para("Renardet S.A. & Partners Consulting Engineers", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
para("Project No. 2621", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
pagebreak()
para("Table of Contents", bold=True, size=16, color="0000CC")
toc()
pagebreak()

# ================= 1 PURPOSE =================
H(1, "Purpose and Design Basis")
para("This tutorial sets out, step by step, how sewage flows and pollution loads are calculated for the Ibri project, from population through to the flows and loads that size the collection network and the sewage treatment plant. It is intended as a compact, self-contained method statement: every numerical value is taken from the NWS design guidelines or from the project Inception Report R0 demand model, and each is cited at the point of use.")
H(2, "Reference documents and citation convention")
table(["Abbreviation", "Document"], [
 ["p##", "PAM-GUD-203 — Wastewater Design Guidelines v1.0 (Rev 01), page ##"],
 ["G1-p##", "PAM-GUD-201 — General Design Guidelines v1.0 (Rev 01), page ##"],
 ["G2-p##", "PAM-GUD-202 — Potable Water & TSE Design Guidelines v1.0 (Rev 01), page ##"],
 ["R0", "Inception Report R0 demand workbook (Ibri Sewer Demand R0, August 2026)"],
], widths=[1.1, 5.4])
para("Where the guidelines and the R0 model differ, both values are stated and the difference is flagged for confirmation with NWS (Section 4).")

# ================= 2 CHAIN =================
H(1, "The Calculation Chain")
para("The calculation proceeds in nine steps. Steps 1-5 build the average flow; Step 6 converts it to peak flows for hydraulic sizing; Step 7 establishes the pollution loads independently of the flows; Steps 8-9 combine them at the treatment plant.")
pic(CHAIN, w=5.6)
caption("Figure 1 — Sewage flow and load calculation chain")
pagebreak()

H(2, "Step 1 — Population")
para("Two routes are used together (G1-p58). The census route projects the NCSI wilayat population and disaggregates it to settlements; it governs the dated model years (2030, 2055). The plot route multiplies the number of plots by the average properties per plot and the occupancy rate; it governs the ultimate (saturated) horizon, because saturation no longer depends on the growth rate.")
table(["Route", "Formula / source", "Governs"], [
 ["Census (top-down)", "NCSI wilayat series, settlement disaggregation. Ibri: 183,564 (2024), growth 2.4-3.0 %/yr (R0)", "Model years 2030 / 2055"],
 ["Plots (bottom-up)", "Population = plots x properties per plot x occupancy rate (G1-p58)", "Ultimate / saturation"],
], widths=[1.5, 3.5, 1.5])
para("The scope horizons are the start year, 2030, 2055 and ultimate, at 5-year projection intervals; the design horizon is completion + 25 years or saturation, whichever governs (TOR p3, p14-15). The occupancy rate per settlement is to be confirmed from NCSI housing statistics.")

H(2, "Step 2 — Water demand")
para("Water demand is built from the domestic per-capita consumption, increased by fixed governorate ratios for non-domestic and governmental use (G1-p60-61). For Adh Dhahirah:")
table(["Component", "Value (l/c/d)", "Reference"], [
 ["Domestic", "164 (R0 computes 163.5 from 2021-24 billing — equivalent)", "G1-p60, R0"],
 ["Non-domestic (+22% of domestic)", "36.1", "G1-p60-61"],
 ["Governmental (+14% of domestic)", "23.0", "G1-p60"],
 ["Total water demand", "223", "—"],
], widths=[2.6, 2.4, 1.4])
para("For large individual facilities (schools, hospitals, malls) the unit rates of G1-p61 Table 12 may replace the percentage approach (e.g. 130 l/pupil/d for schools, 650 l/bed/d for hospitals).")

H(2, "Step 3 — Wastewater return")
para("Only part of the supplied water returns to the sewer. The return rates of G1-p71 (Table 19) are 85% for domestic and tankered consumption and 54% for non-domestic and governmental consumption:")
table(["Stream", "Return", "Per-capita wastewater (l/c/d)"], [
 ["Domestic", "85%", "164 x 0.85 = 139.4"],
 ["Non-domestic + governmental", "54%", "(36.1 + 23.0) x 0.54 = 31.9"],
 ["Total wastewater generation", "—", "≈ 171"],
], widths=[2.6, 1.2, 2.6])

H(2, "Step 4 — Additions: infiltration and tankers")
bullet("Infiltration, new networks: 720 L/d per km of sewer (G1-p72). For existing inland networks: 10% of the wastewater flow; up to 40% for coastal/high-groundwater systems. No stormwater allowance — the system is strictly separate.")
bullet("Yellow tankers: currently about 17% of STP inflow nationally; design coverage reaches 100% by the end of the planning period (G1-p73). The R0 model collects tankered flows from settlements within 25 km of the STP.")
para("Note: the R0 model currently applies 10% infiltration to selected settlements, whereas the guideline value for new networks is the linear 720 L/d/km — roughly an order of magnitude smaller for this network. Both are carried until NWS confirms the basis (Section 4).")

H(2, "Step 5 — Average flow")
para("The average daily flow (Qadf, equal to the annual average flow AAF of GUD-203) is:")
para("Qadf [m3/d] = Population x 171 l/c/d / 1000 + Infiltration + Tanker deliveries", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=10)
para("GUD-203 (p65-66) distinguishes AAF (annual average), MDF (maximum day) and PHF (peak hour); each has a distinct use in Step 8.")

H(2, "Step 6 — Peak flows")
para("Peaking applies to the sewage component only; infiltration is not peaked. Two formulas are permitted (G1-p71-72):")
table(["Method", "Expression", "Result"], [
 ["Peltier (IMP 2024)", "PF = 1.5 + 1/√Qm, Qm in L/s", "Peak factor on average flow"],
 ["Merrimack", "Qpdf = 2.65 x Qadf^0.879 (both Ml/d, >100 properties)", "Peak daily flow directly"],
 ["Cap", "Hourly PF ≤ 5.0", "—"],
], widths=[1.7, 3.1, 1.7])
para("The two methods do not agree (the worked example gives PF 1.72 vs 2.48). Peltier is the current IMP 2024 method; the binding choice is to be confirmed with NWS. The R0 model additionally applies a +20% weekly peak, which has no guideline source and is likewise flagged.")

H(2, "Step 7 — Organic loads")
para("Per-capita loads are fixed minimums (p74) and do not scale with water consumption:")
table(["Parameter", "Value", "Reference"], [
 ["BOD5", "≥ 60 g/cap/d", "p74"],
 ["TSS", "80 g/cap/d", "p74"],
 ["COD (domestic)", "1.8 - 2.2 x BOD", "p74"],
], widths=[2.0, 2.4, 1.4])
para("Concentration is always derived, never assumed: C [mg/l] = Load [kg/d] x 1000 / Q [m3/d]. Low per-capita water use produces concentrated sewage: expect BOD around 300-400 mg/l here. A result near 200 mg/l (European dilution) indicates an error.")

H(2, "Step 8 — What each flow is used for")
table(["Use", "Governing flow", "Additional rules"], [
 ["Gravity pipe sizing", "Peak (hourly) flow", "d/D ≤ 0.65 (D ≤ 350) / 0.50 (D > 350); v = 0.75-3.0 m/s; Table 11 minimum gradients (p26-29)"],
 ["Pumping stations / force mains", "Peak flow with any one pump out", "v = 1.0 (intermittent) - 2.5 m/s (p39, p50)"],
 ["STP hydraulic pass-through", "PHF", "p65-66"],
 ["STP biology", "AAF + organic loads", "p65-66"],
 ["TE / TSE pipelines", "TSE = 95% of STP inlet", "Roughness penalty for TE: ε +30%, C −10% (G2-p104)"],
], widths=[1.9, 1.8, 2.8], font=8)

H(2, "Step 9 — STP incoming flow and outputs")
para("STP incoming flow = network Qadf (including infiltration) + tankered flows + 10% operational allowance (p65 Table 29, G1-p73). A plant at or above 20,000 m3/d falls in the Large category (p65); per the TOR, the Phase I capacity relative to this threshold determines whether the new STP preliminary design remains in the consultancy scope.")
bullet("TSE production = 95% of STP inlet (G1-p73) — this feeds the TE network design.")
bullet("Sludge ≈ 0.25 kg per m3 treated (R0 planning rate; to be refined at process design).")
pagebreak()

# ================= 3 WORKED EXAMPLE =================
H(1, "Worked Example")
para("A settlement of 10,000 persons served by 25 km of new sewers, all values rounded:")
table(["#", "Step", "Calculation", "Result"], [
 ["1", "Population", "given", "10,000 cap"],
 ["2", "Water demand", "164 x 1.36", "223 l/c/d → 2,230 m3/d"],
 ["3", "Wastewater return", "164 x 0.85 + 59.1 x 0.54", "171.3 l/c/d → 1,713 m3/d"],
 ["4", "Infiltration (new network)", "720 L/d/km x 25 km", "+18 m3/d (≈ 1%)"],
 ["5", "Average flow Qadf", "1,713 + 18", "1,731 m3/d = 20.0 L/s"],
 ["6a", "Peltier peak", "PF = 1.5 + 1/√20.0 = 1.72", "peak 34.5 L/s"],
 ["6b", "Merrimack peak", "2.65 x 1.731^0.879", "4.29 Ml/d = 49.7 L/s (PF 2.48)"],
 ["7", "Loads BOD / TSS / COD", "10,000 x 60 / 80 / 120 g/d", "600 / 800 / 1,200 kg/d"],
 ["7b", "Concentrations", "load / Qadf", "BOD 347, TSS 462, COD 693 mg/l"],
 ["8", "STP incoming flow", "1,731 x 1.10", "1,904 m3/d"],
 ["9", "TSE production", "1,904 x 0.95", "1,809 m3/d"],
], widths=[0.45, 1.9, 2.5, 1.9], font=9)
caption("Table — Worked example, 10,000-person settlement")
para("Sanity checks that should always hold: BOD concentration between 300 and 400 mg/l; peak factor between 1.5 and 5.0; infiltration far smaller than sewage flow for a new inland network.")

# ================= 4 RECONCILIATION =================
H(1, "Guideline vs Inception R0 — Reconciliation Register")
para("The R0 demand model and the guidelines agree on the core parameters; the differences below are carried openly until confirmed with NWS at the kick-off stage:")
table(["Item", "Guideline (binding)", "R0 adopted", "Status"], [
 ["Domestic per-capita demand", "164 l/c/d (G1-p60)", "163.5 computed from billing", "Consistent"],
 ["Return ratios", "85% / 54% (G1-p71)", "Same", "Consistent"],
 ["Infiltration", "720 L/d/km, new networks (G1-p72)", "10% of wastewater flow", "To reconcile"],
 ["Peaking", "Peltier / Merrimack, PF ≤ 5 (G1-p71-72)", "+20% weekly peak added", "Confirm basis"],
 ["Tanker catchment", "Not specified", "25 km radius", "NWS to confirm"],
 ["STP margin / TSE ratio", "+10% / 95% (G1-p73)", "Same", "Consistent"],
 ["Sludge rate", "Not specified", "0.25 kg/m3", "R0 planning value"],
], widths=[1.7, 2.1, 1.8, 1.0], font=8)
H(2, "Open inputs")
bullet("Occupancy rate per settlement — NCSI housing statistics (partly available in the R0 workbook; value per settlement to be confirmed).")
bullet("Existing Ibri STP capacity, headworks invert and spare capacity.")
bullet("Model start year and confirmation of the 2030 / 2055 / ultimate horizons.")

doc.save(OUT)
print("saved", OUT)
