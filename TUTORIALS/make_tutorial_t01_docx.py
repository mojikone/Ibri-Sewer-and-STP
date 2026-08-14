# -*- coding: utf-8 -*-
"""Tutorial T01 Rev 1 — Sewage Flow & Load Calculation, styled on Data/sample report/Sample.docx.
Rev 1 addresses the review comments of T01_..._commented.docx (2026-08-14).
Refs: G203-p## = PAM-GUD-203, G201-p## = PAM-GUD-201, G202-p## = PAM-GUD-202,
R0 = Ibri Inception Report R0 demand workbook (Aug 2026)."""
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement, parse_xml

SAMPLE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\sample report\Sample.docx"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "T01_Sewage_Flow_and_Load_Calculation.docx")
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
PROJ = "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri"
SUB = "Tutorial T01 — Sewage Flow and Pollution Load Calculation"

BLUE = "#0072B2"; ORANGE = "#E69F00"; INK = "#333333"; GRID = "#DDDDDD"

# ================================================================= CHARTS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def style_ax(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#999999")
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.tick_params(colors="#555555", labelsize=9)

CHAIN = os.path.join(IMG, "t01_chain.png")
def make_chain():
    steps = [
        ("1  Population", "NCSI census route / plot route / electricity pro-rata"),
        ("2  Water demand", "domestic 164 l/c/d + non-domestic 22% + governmental 14%"),
        ("3  Wastewater return", "85% of domestic & tanker / 54% of non-domestic & governmental"),
        ("4  Additions", "infiltration + tankered sewage"),
        ("5  Average flow Qadf", "the annual-average flow (AAF)"),
        ("6  Peak flows", "Peltier / Merrimack peak factors, PF <= 5"),
        ("7  Organic loads", "60 g BOD5, 80 g TSS per capita per day"),
        ("8  STP sizing", "biology on AAF + loads; hydraulics on PHF; +10% margin"),
        ("9  TSE output", "95% of STP inlet, feeds the TE network"),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 8.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, len(steps) * 1.15); ax.axis("off")
    ys = []
    for i, (t, s) in enumerate(steps):
        y = (len(steps) - 1 - i) * 1.15
        ax.add_patch(FancyBboxPatch((0.9, y + 0.08), 8.2, 0.86, boxstyle="round,pad=0.06",
                                    fc="#EAF1FB", ec="#2E5C9E", lw=1.4))
        ax.text(5.0, y + 0.63, t, ha="center", va="center", fontsize=12.5, fontweight="bold", color="#1F3A64")
        ax.text(5.0, y + 0.28, s, ha="center", va="center", fontsize=9.5, color="#444444")
        ys.append(y)
    for i in range(len(steps) - 1):
        ax.add_patch(FancyArrowPatch((5.0, ys[i] + 0.06), (5.0, ys[i + 1] + 0.96),
                                     arrowstyle="-|>", mutation_scale=16, color="#2E5C9E", lw=1.4))
    fig.savefig(CHAIN, dpi=200, bbox_inches="tight"); plt.close(fig)

DIURNAL = os.path.join(IMG, "t01_diurnal.png")
def make_diurnal():
    h = np.linspace(0, 24, 241)
    f = (1.0 + 0.55 * np.sin((h - 9.5) * np.pi / 12) + 0.28 * np.sin((h - 20.0) * np.pi / 6.0)
         - 0.18 * np.cos((h - 3) * np.pi / 12))
    f = np.clip(f, 0.25, None)
    f = f / f.mean()
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.plot(h, f, color=BLUE, lw=2.2, zorder=3)
    ax.axhline(1.0, color="#777777", lw=1.2, ls="--", zorder=2)
    pk = h[np.argmax(f)]
    ax.annotate("peak hour  (PHF = peak-hour flow)", xy=(pk, f.max()), xytext=(pk + 2.2, f.max() + 0.06),
                fontsize=9, color=INK, arrowprops=dict(arrowstyle="->", color="#777777"))
    ax.annotate("daily average = 1.0  (AAF when averaged over the year)", xy=(2.8, 1.0),
                xytext=(0.4, 1.62), fontsize=9, color=INK, arrowprops=dict(arrowstyle="->", color="#777777"))
    ax.annotate("night minimum\n(mostly infiltration)", xy=(h[np.argmin(f)], f.min()),
                xytext=(6.5, 0.32), fontsize=9, color=INK, arrowprops=dict(arrowstyle="->", color="#777777"))
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 4))
    ax.set_xlabel("hour of day", fontsize=9, color=INK)
    ax.set_ylabel("flow / daily average", fontsize=9, color=INK)
    style_ax(ax)
    fig.savefig(DIURNAL, dpi=200, bbox_inches="tight"); plt.close(fig)

ROUTE_CENSUS = os.path.join(IMG, "t01_route_census.png")
ROUTE_PLOTS = os.path.join(IMG, "t01_route_plots.png")
def route_chart(path, title, steps, color="#2E5C9E", fill="#EAF1FB"):
    fig, ax = plt.subplots(figsize=(7.2, 1.1 + 1.12 * len(steps)))
    ax.set_xlim(0, 10); ax.set_ylim(0, len(steps) * 1.12 + 0.5); ax.axis("off")
    ax.text(5, len(steps) * 1.12 + 0.25, title, ha="center", fontsize=12.5, fontweight="bold", color="#1F3A64")
    ys = []
    for i, (t, s) in enumerate(steps):
        y = (len(steps) - 1 - i) * 1.12
        ax.add_patch(FancyBboxPatch((0.7, y + 0.10), 8.6, 0.84, boxstyle="round,pad=0.05",
                                    fc=fill, ec=color, lw=1.3))
        ax.text(5.0, y + 0.62, t, ha="center", va="center", fontsize=10.5, fontweight="bold", color="#1F3A64")
        ax.text(5.0, y + 0.29, s, ha="center", va="center", fontsize=8.8, color="#444444")
        ys.append(y)
    for i in range(len(steps) - 1):
        ax.add_patch(FancyArrowPatch((5.0, ys[i] + 0.08), (5.0, ys[i + 1] + 0.95),
                                     arrowstyle="-|>", mutation_scale=14, color=color, lw=1.3))
    fig.savefig(path, dpi=200, bbox_inches="tight"); plt.close(fig)

POPCHART = os.path.join(IMG, "t01_population.png")
NCSI = {2021: 168409, 2022: 173418, 2023: 178477, 2024: 183564, 2025: 187962, 2026: 193116,
        2027: 198344, 2028: 203659, 2029: 209063, 2030: 213637, 2031: 219186, 2032: 224840, 2033: 227736}
def make_pop():
    yrs = sorted(NCSI); pop = [NCSI[y] / 1000 for y in yrs]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ax.plot(yrs, pop, color=BLUE, lw=2.2, marker="o", ms=4.5, zorder=3)
    ax.annotate("183.6k (2024)", xy=(2024, 183.564), xytext=(2024.2, 172), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="->", color="#777777"))
    ax.annotate("227.7k (2033)", xy=(2033, 227.736), xytext=(2030.4, 231), fontsize=9, color=INK)
    ax.text(2021.2, 224, "growth rate declines 3.0% -> 1.3%/yr", fontsize=9, color="#555555")
    ax.set_xlabel("year", fontsize=9, color=INK); ax.set_ylabel("population (thousands)", fontsize=9, color=INK)
    ax.set_xticks(yrs[::2])
    style_ax(ax)
    fig.savefig(POPCHART, dpi=200, bbox_inches="tight"); plt.close(fig)

PFCHART = os.path.join(IMG, "t01_pf.png")
def make_pf():
    q = np.logspace(0, 3, 200)              # L/s
    pf_pel = np.clip(1.5 + 1 / np.sqrt(q), None, 5.0)
    q_mld = q * 0.0864
    pf_mer = 2.65 * q_mld ** (-0.121)
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.semilogx(q, pf_pel, color=BLUE, lw=2.2, zorder=3)
    ax.semilogx(q, pf_mer, color=ORANGE, lw=2.2, zorder=3)
    ax.axhline(5.0, color="#999999", lw=1.1, ls=":")
    ax.text(1.15, 5.08, "cap PF = 5.0 (G201-p72)", fontsize=8.5, color="#777777")
    ax.text(300, 1.62, "Peltier (peak hour)", fontsize=9.5, color=BLUE, fontweight="bold")
    ax.text(300, 2.35, "Merrimack (peak day)", fontsize=9.5, color=ORANGE, fontweight="bold")
    ax.plot([20], [1.72], "o", color=BLUE, ms=6)
    ax.plot([20], [2.48], "o", color=ORANGE, ms=6)
    ax.annotate("worked example\nQadf = 20 L/s", xy=(20, 1.72), xytext=(33, 1.1), fontsize=8.8, color=INK,
                arrowprops=dict(arrowstyle="->", color="#777777"))
    ax.set_xlabel("average flow Qadf (L/s, log scale)", fontsize=9, color=INK)
    ax.set_ylabel("peak factor PF", fontsize=9, color=INK)
    ax.set_ylim(0.8, 5.6)
    style_ax(ax)
    fig.savefig(PFCHART, dpi=200, bbox_inches="tight"); plt.close(fig)

make_chain(); make_diurnal(); make_pop(); make_pf()
route_chart(ROUTE_CENSUS, "Route A — Census projection (dated horizons 2030 / 2055)", [
    ("NCSI wilayat population series", "official census + forecast, Ibri wilayat, from 2020 onward (G201-p58-59)"),
    ("Project the growth", "apply the NCSI forecast (or fitted growth rate) at 5-year intervals to each model year"),
    ("Disaggregate to settlements", "split the wilayat total using the settlement shares of the latest census (G201-p58)"),
    ("Sub-settlement split where needed", "pro-rata by electricity account counts within the area, provided by NWS (G201-p58)"),
    ("Population per zone and model year", "input to water demand (Step 2) for 2030 / 2055 horizons"),
])
route_chart(ROUTE_PLOTS, "Route B — Plot count x occupancy (ultimate / saturated horizon)", [
    ("Cadastral plots (MoHUP)", "count plots by land-use typology inside each zone (G201-p58)"),
    ("x average properties per plot", "how many dwellings a developed plot carries at build-out (subdivision checked)"),
    ("x occupancy rate", "persons per housing unit = NCSI population / NCSI housing units (G201-p58-59)"),
    ("Saturation population per zone", "the ceiling when every plot is developed - independent of growth rate"),
], color="#8A5A00", fill="#FBF3E2")

# ================================================================= DOCUMENT
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

def para(text, style=None, align=None, bold=None, size=None, color=None, space_after=6, italic=None):
    p = doc.add_paragraph(style=style)
    r = p.add_run(text)
    if bold is not None: r.bold = bold
    if italic is not None: r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if align is not None: p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p
def H(level, text):
    return doc.add_paragraph(text, style=f"Heading {level}")
_styles = {s_.name for s_ in doc.styles}
def bullet(text, bold_lead=None):
    if "List Bullet" in _styles:
        p = doc.add_paragraph(style="List Bullet")
    else:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.add_run("• ")
    if bold_lead:
        r = p.add_run(bold_lead); r.bold = True
    p.add_run(text)
    return p

FIGS, TABS = [], []
def fig_caption(text):
    n = len(FIGS) + 1
    label = f"Figure {n} — {text}"
    FIGS.append(label)
    try: p = doc.add_paragraph(label, style="Caption")
    except KeyError: p = para(label, bold=True, size=10)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p
def tab_caption(text):
    n = len(TABS) + 1
    label = f"Table {n} — {text}"
    TABS.append(label)
    try: p = doc.add_paragraph(label, style="Caption")
    except KeyError: p = para(label, bold=True, size=10)
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
    r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = "Right-click and Update Field to refresh."
    r.append(t); fld.append(r); p._p.append(fld)

# ---------- OMML native equations ----------
NSDECL = ('xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
          'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')
def mr(t, sty=None):
    rpr = '<m:rPr><m:sty m:val="%s"/></m:rPr>' % sty if sty else ""
    return f'<m:r>{rpr}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{t}</m:t></m:r>'
def frac(num, den):
    return f'<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>'
def sqrt(e):
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>'
def ssub(base, sub):
    return f'<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>'
def ssup(base, sup):
    return f'<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>'
def equation(inner):
    xml = f'<w:p {NSDECL}><w:pPr><w:jc w:val="center"/><w:spacing w:after="120"/></w:pPr><m:oMathPara><m:oMath>{inner}</m:oMath></m:oMathPara></w:p>'
    sect.addprevious(parse_xml(xml))

Q = lambda s: ssub(mr("Q"), mr(s))
q_ = lambda s: ssub(mr("q"), mr(s))

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
para("Revision 1 — August 2026 (addresses review comments on Rev 0)", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
para("", space_after=80)
para("Renardet S.A. & Partners Consulting Engineers", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
para("Project No. 2621", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
pagebreak()

# ================= ABBREVIATIONS =================
para("Abbreviations and Symbols", bold=True, size=16, color="0000CC")
table(["Abbreviation", "Meaning"], [
 ["AAF", "Annual Average Flow — the sewage flow averaged over a full year (= Qadf in this tutorial)"],
 ["ADF / Qadf", "Average Daily Flow — daily flow averaged over the year; the basic planning flow"],
 ["MDF", "Maximum Day Flow — the flow of the highest-flow day of the year"],
 ["PHF", "Peak Hour Flow — the flow of the highest hour; sizes all hydraulic pass-through elements"],
 ["PF", "Peak Factor — ratio converting an average flow into a peak flow"],
 ["BOD5", "Biochemical Oxygen Demand (5-day) — oxygen consumed by bacteria degrading the organic matter"],
 ["COD", "Chemical Oxygen Demand — oxygen equivalent of ALL oxidisable matter (chemical test)"],
 ["TSS", "Total Suspended Solids — particulate matter carried by the sewage"],
 ["LPCD", "Litres Per Capita per Day"],
 ["NCSI", "National Centre for Statistics and Information (Oman census authority)"],
 ["IMP", "Integrated Master Plan — NWS's national water/wastewater master plan (IMP 2024 edition)"],
 ["NWS", "Nama Water Services (the Client; also OWWSC)"],
 ["MoHUP", "Ministry of Housing and Urban Planning (cadastral plot data)"],
 ["STP", "Sewage Treatment Plant"],
 ["TSE / TE", "Treated Sewage Effluent / Treated Effluent — the reclaimed water product of the STP"],
 ["SLS", "Sewage Lifting Station"],
 ["OR", "Occupancy Rate — persons per housing unit"],
 ["G201 / G202 / G203", "NWS guidelines PAM-GUD-201 (General), -202 (Water & TSE), -203 (Wastewater)"],
], widths=[1.2, 5.3], font=9)
pagebreak()

# ================= EXECUTIVE SUMMARY =================
H(1, "Executive Summary")
para("This tutorial teaches, from first principles, how the sewage flows and pollution loads of the Ibri project are calculated: what each parameter means, where its value comes from, why the calculation is structured the way it is, and how the results are used to size the collection network and the sewage treatment plant (STP). It is written for a reader new to wastewater flow estimation; every value is cited to the NWS guidelines (G203, G201, G202, by page) or to the project Inception Report R0 demand model, and every equation is explained before it is used.")
para("The calculation is a nine-step chain. It is summarised here in full; each step has a dedicated section in the body of the report.")
bullet("Population is estimated by two complementary routes. ", bold_lead="Step 1 — Population (Section 5). ")
para("Route A projects the official NCSI census series for Ibri wilayat (183,564 inhabitants in 2024, growth declining from about 3.0 to 1.3 percent per year in the NCSI forecast to 2033) and disaggregates it to settlements using census shares — and below settlement level, pro-rata by electricity account counts, as the guideline directs. Route A produces the populations of the dated model years (2030, 2055). Route B multiplies the count of cadastral plots by the average number of properties per plot and by the occupancy rate (persons per housing unit, from NCSI housing statistics). Route B produces the saturation (ultimate) population — the ceiling reached when every plot is developed, which is independent of how fast growth occurs. The network pipes, which live 50 years and cannot be economically re-laid, are sized for the Route B ceiling; the STP, which is built in phases, is sized for the Route A dated horizons. This is how the two routes are reconciled.")
bullet("Total water demand is built from the measured domestic consumption of Adh Dhahirah Governorate — 164 litres per capita per day (l/c/d) — plus governorate-average allowances of 22 percent for non-domestic (commercial) and 14 percent for governmental consumption, giving 223 l/c/d. These percentage allowances are a planning-level bookkeeping device: they distribute the governorate's measured non-domestic water use over the resident population so that totals are correct even before land-use-specific data exist. In the hydraulic model, large individual facilities are instead loaded at their own nodes using per-facility unit rates (litres per pupil, per bed, per m2).", bold_lead="Step 2 — Water demand (Section 6). ")
bullet("Only part of the supplied water reaches the sewer: 85 percent of domestic (and tankered) consumption and 54 percent of non-domestic and governmental consumption; the remainder is lost to irrigation, evaporative cooling and other consumptive uses. The result for Ibri is a wastewater generation of about 171 l/c/d.", bold_lead="Step 3 — Wastewater return (Section 7). ")
bullet("Two flows join the sewage: infiltration of groundwater and soil moisture through pipe joints and manholes (720 litres per day per kilometre of new sewer per the guideline; the R0 model provisionally uses the more conservative 10 percent of wastewater flow), and tankered sewage from properties not yet connected to the network (about 17 percent of STP inflow nationally today, to be phased out as coverage reaches 100 percent). A recent site visit found tankers arriving from camps up to 150 km away — beyond any assumption in the scope — which is flagged as a project risk.", bold_lead="Step 4 — Additions (Section 8). ")
bullet("The average daily flow Qadf is the population times the per-capita wastewater generation, plus infiltration and tanker deliveries. Qadf is the backbone quantity of the whole design: the STP biology, the annual loads and the phasing analysis all rest on it.", bold_lead="Step 5 — Average flow (Section 9). ")
bullet("Sewage flow varies strongly over the day, so pipes must carry the peak, not the average. The peak factor (PF) converts average to peak flow; it decreases as catchments grow because many households' peaks do not coincide. Two empirical formulas are permitted — Peltier (a peak-hour factor, the current IMP 2024 method) and Merrimack (a peak-day regression). They answer slightly different questions and were fitted to different data, so they disagree (1.72 vs 2.48 at the worked-example flow); the binding choice is to be confirmed with NWS at kickoff.", bold_lead="Step 6 — Peak flows (Section 10). ")
bullet("Pollution is quantified independently of water use: each person contributes a fixed daily mass of organic matter (at least 60 g of BOD5 and 80 g of TSS per day) regardless of how much water dilutes it. Loads (kg/d) size the biological treatment; concentrations (mg/l) are always derived as load divided by flow — Oman's low water use makes the sewage concentrated, around 300-400 mg/l BOD5.", bold_lead="Step 7 — Organic loads (Section 11). ")
bullet("Each design element is sized by a specific flow: gravity pipes and pumping stations by the peak-hour flow, the STP hydraulic pass-through by PHF, the biological process by AAF plus loads. The STP incoming flow adds a 10 percent operational allowance; the plant category (above/below 20,000 m3/d) determines the STP scope route per the Terms of Reference.", bold_lead="Steps 8-9 — Design flows and STP (Sections 12-13). ")
bullet("The STP returns 95 percent of its inflow as treated sewage effluent (TSE), which feeds the TE network design, and produces sludge (about 0.25 kg per m3 treated) which is thickened, dewatered and directed to reuse or disposal under the sludge management strategy required by the scope.", bold_lead="Outputs (Section 13). ")
para("A fully worked numerical example (Section 14) carries a hypothetical settlement of 10,000 persons through all nine steps, and a reconciliation register (Section 15) lists the four points where the R0 model and the guidelines differ (infiltration basis, weekly peak, tanker catchment radius, sludge rate) — all flagged for confirmation with NWS at the kickoff stage. Conclusions and recommendations close the report.")
pagebreak()

# ================= TOC / LOF / LOT =================
para("Table of Contents", bold=True, size=16, color="0000CC")
toc()
para("", space_after=10)
para("List of Figures", bold=True, size=14, color="0000CC")
LOF_MARK = doc.add_paragraph()
para("List of Tables", bold=True, size=14, color="0000CC")
LOT_MARK = doc.add_paragraph()
pagebreak()

# ================= 1 INTRODUCTION =================
H(1, "Introduction")
H(2, "Purpose and how to read this tutorial")
para("This document is a teaching text, not a design report: its goal is that the reader can afterwards perform and check every calculation independently. Each section first explains the concept in plain terms — what the quantity is, why it exists, what would go wrong without it — then gives the governing values and equations with their sources, and finally shows the numbers at work in the worked example of Section 14. No parameter is used without being defined, and no equation appears without its purpose stated.")
H(2, "Reference documents and citation convention")
table(["Citation", "Document"], [
 ["G203-p##", "PAM-GUD-203 — Wastewater Design Guidelines v1.0 (Rev 01), page ##"],
 ["G201-p##", "PAM-GUD-201 — General Design Guidelines v1.0 (Rev 01), page ##"],
 ["G202-p##", "PAM-GUD-202 — Potable Water & TSE Design Guidelines v1.0 (Rev 01), page ##"],
 ["TOR", "Terms of Reference, Section 03, Tender T/2719110/2025"],
 ["R0", "Inception Report R0 demand workbook (Ibri Sewer Demand R0, August 2026)"],
], widths=[1.1, 5.4])
tab_caption("Reference documents and citation convention")
para("Where the guidelines and the R0 model differ, both values are given and the difference is flagged for confirmation with NWS (Section 15).")

# ================= 2 KEY CONCEPTS =================
H(1, "Key Concepts: How Sewage Flow Behaves")
para("Before any calculation, three facts about sewage flow must be understood, because the whole structure of the method follows from them.")
bullet("Sewage flow follows human activity over the day. It is lowest in the small hours of the night (when what remains in the pipe is mostly infiltration), rises steeply with the morning routine, and shows a second evening peak. Figure 1 shows a typical (illustrative) diurnal pattern.", bold_lead="It varies over the day. ")
bullet("Weekends, holidays and seasons shift water use; over a year, the highest-flow day can be well above the average day.", bold_lead="It varies over the year. ")
bullet("A single house may momentarily discharge many times its average; a city of 100,000 never does, because individual peaks do not coincide. This damping with size is why peak factors decrease as flow accumulates downstream, and why small upstream sewers need proportionally more capacity headroom than large trunk mains.", bold_lead="The bigger the catchment, the smoother the flow. ")
pic(DIURNAL, w=5.9)
fig_caption("Typical diurnal sewage flow pattern (illustrative), with the average and peak-hour levels marked")
para("From this behaviour the guidelines define three reference flows (G203-p65-66), each with a distinct design role:")
table(["Flow", "Definition", "What it is used for"], [
 ["AAF (= Qadf)", "Annual Average Flow: total annual volume / 365 days. In this tutorial written Qadf (average daily flow).", "The planning backbone: STP biological sizing, annual loads, phasing, energy and cost estimates"],
 ["MDF", "Maximum Day Flow: the highest single-day volume of the year.", "Storage, emergency lagoons, day-scale process checks"],
 ["PHF", "Peak Hour Flow: the highest hourly flow of the year.", "Everything sewage physically passes through: pipes, pumps, screens, channels, STP headworks"],
], widths=[1.1, 2.7, 2.7], font=9)
tab_caption("The three reference flows of G203-p65-66 and their design roles")
para("The relationship is always AAF < MDF < PHF. The calculation chain of this tutorial first establishes Qadf (Steps 1-5), then converts it to the peaks (Step 6).")

# ================= 3 CHAIN =================
H(1, "The Calculation Chain at a Glance")
para("The nine steps of Figure 2 form a strict chain: each step consumes the previous step's output. Steps 1-5 build the average flow; Step 6 converts it to peak flows; Step 7 establishes the pollution loads on a parallel track (they depend on population, not on water); Steps 8-9 combine flows and loads at the treatment plant.")
pic(CHAIN, w=5.6)
fig_caption("The sewage flow and load calculation chain (Steps 1-9)")
pagebreak()

# ================= 4 STEP 1 POPULATION =================
H(1, "Step 1 — Population")
H(2, "Why population comes first")
para("Every quantity in this tutorial — water, sewage, BOD, sludge — is generated by people. Population is therefore the root input, and any error in it propagates proportionally through the entire chain: a 10 percent error in population is a 10 percent error in STP capacity. The guidelines (G201-p57) recognise three approaches: figures provided directly by a developer (for defined developments), calculation from NCSI forecast data, and calculation from plots, property types and occupancy rates. For a whole-town project like Ibri the last two are used together, as Routes A and B below; developer figures apply only to specific master-planned schemes if NWS provides them.")
H(2, "Route A — census projection (for the dated model years)")
para("Route A answers: how many people will actually live here in 2030, in 2055? It starts from the official NCSI population series and works downward in scale:")
bullet("The NCSI series for Ibri wilayat is the authoritative starting point (G201-p58-59). The current figures, taken from the R0 workbook, are shown in Table 4 and Figure 3.", bold_lead="Start from the wilayat series. ")
bullet("NCSI publishes forecasts; where projection beyond them is needed, a growth rate fitted to the series is applied at the 5-year intervals required by the TOR (start year, 2030, 2055).", bold_lead="Project the growth. ")
bullet("The wilayat total is split over settlements in proportion to their shares in the latest census (G201-p58) — a settlement holding 4 percent of the census population receives 4 percent of every projected total.", bold_lead="Disaggregate to settlements. ")
bullet("Where a project zone covers only part of a settlement, the guideline directs a pro-rata split by the number of electricity accounts in the area, obtained from NWS (G201-p58). Electricity accounts are a reliable proxy for occupied dwellings because effectively every occupied dwelling has a metered connection — this is also why the TOR (p12) lists electricity data among the required flow-assessment inputs.", bold_lead="Split below settlement level by electricity accounts. ")
pic(ROUTE_CENSUS, w=5.9)
fig_caption("Route A — from NCSI wilayat series to zone populations for the dated horizons")
table(["Year", "2021", "2022", "2023", "2024", "2026", "2028", "2030", "2032", "2033"], [
 ["Population", "168,409", "173,418", "178,477", "183,564", "193,116", "203,659", "213,637", "224,840", "227,736"],
 ["Growth (%/yr)", "—", "2.97", "2.92", "2.85", "2.74", "2.68", "2.19", "2.58", "1.29"],
], widths=[1.05, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62], font=8)
tab_caption("NCSI population series for Ibri wilayat (from the R0 workbook; selected years)")
pic(POPCHART, w=5.9)
fig_caption("NCSI population series and forecast for Ibri wilayat, 2021-2033")
H(2, "Route B — plots x occupancy (for the ultimate horizon)")
para("Route B answers a different question: how many people can this area hold when it is fully built? It works upward from the cadastre:")
equation(mr("Population") + mr(" = ") + ssub(mr("N"), mr("plots")) + mr(" × ") + ssub(mr("n"), mr("prop")) + mr(" × ") + mr("OR"))
para("where N(plots) is the number of plots of a given typology inside the zone, n(prop) is the average number of properties (dwellings) each such plot carries at build-out, and OR is the occupancy rate (G201-p58):")
equation(mr("OR") + mr(" = ") + frac(mr("Population"), mr("Housing units")))
para("Both OR inputs come from the NCSI data portal, which publishes population and housing-unit counts from 2020 at governorate and wilayat level (G201-p59). The guideline adds two cautions: plot subdivision must be checked so that the effective number of housing units is not understated, and development speed must temper the assumption that all plots fill up (G201-p59).")
pic(ROUTE_PLOTS, w=5.9)
fig_caption("Route B — from cadastral plots to the saturation population")
H(2, "How the two routes fit together — saturation vs dated horizons")
para("The two routes serve different design decisions, and understanding their relationship is essential:")
bullet("The master-plan plots define the maximum development the planning framework allows. Multiplying all plots by properties-per-plot and occupancy gives the saturation population — a ceiling, not a forecast. It says nothing about when that ceiling is reached.")
bullet("The census projection gives the population trajectory in time — but knows nothing about the physical ceiling; extrapolated far enough it would eventually exceed what the plots can hold.")
bullet("The two are reconciled by using each where it is authoritative: buried pipes have a 50-year design life (G201-p57) and cannot economically be re-laid, so the network is sized once, for the Route B saturation flow. The STP is modular and is expanded in phases, so each phase is sized for a Route A dated horizon (2030, 2055). The TOR's design horizon rule — completion + 25 years or ultimate, whichever governs — expresses exactly this: if the Route A projection at completion + 25 years exceeds saturation, saturation caps it.")
bullet("Consistency check: zone-by-zone, the Route A population at any horizon must remain below the Route B ceiling. Where a projection exceeds the ceiling, either the growth allocation to that zone is too high or the plot data is stale (new subdivisions) — the discrepancy must be resolved, not ignored.")
H(2, "Is the available plot data ready for this?")
para("Partly. The MoHUP cadastral layer for Ibri contains 61,272 plot polygons with land-use classification and a built-type attribute, which is sufficient for counting and classifying plots per zone (Route B's first input). Two of the three factors are, however, not yet supported by data: the average properties per plot (requires the subdivision check of G201-p59) and the occupancy rate (requires NCSI housing-unit counts, which are not included in the R0 package — its workbook carries population only). Both are on the kickoff data request; until they arrive, screening uses a tagged assumption (OR = 6.0) and results are reported as scaling linearly with it.")

# ================= 5 STEP 2 WATER =================
H(1, "Step 2 — Water Demand")
H(2, "The concept: sewage begins as drinking water")
para("Nearly all sewage is water that was first supplied through the potable network (or by water tanker), used, and discharged to the drain. Wastewater estimation therefore starts by establishing how much water each person's presence causes to be consumed — not only at home (domestic), but also in the shops, offices, schools and government buildings that exist because the population exists.")
H(2, "The per-capita method and why the components are added")
para("The domestic consumption of Adh Dhahirah Governorate is 164 l/c/d — a measured value from the IMP 2024 baseline (G201-p60), which the R0 model independently reproduces (163.5 l/c/d) from 2021-24 billing records. Non-domestic and governmental consumption are then expressed as governorate-average ratios of the domestic figure: +22 percent and +14 percent respectively (G201-p60-61).")
para("A reader may reasonably object: commercial and governmental demand belongs to specific land-use plots, not to residents — why add it per capita? The answer is that the ratios are an aggregate bookkeeping device, and it is worth being precise about what they do and do not claim:")
bullet("At governorate scale, the total non-domestic and governmental water use is measured (it is in the billing data). Dividing it by the resident population and expressing it as a percentage of domestic use distributes that measured total over the people it ultimately serves. The town-wide totals are then correct by construction — even before any land-use analysis exists. This is the appropriate method at the planning stage, when the question is 'how much sewage will Ibri produce'.")
bullet("At model scale, the same consumption is instead assigned spatially: each commercial or institutional plot is loaded at its own network node, using the unit rates of G201-p61 Table 12 (130 l/pupil/d for schools, 650 l/bed/d for hospitals, 12.2 l/m2/d for shopping floor area, 93 l/employee/d for offices, etc.), with the occupancy of each facility taken from the GIS land-use data. This is the appropriate method when the question is 'which pipe must carry the hospital's discharge'.")
bullet("The two views must reconcile: the sum of the spatially-assigned non-domestic loads over the whole town should approximate the percentage allowance times the population. A large discrepancy signals either unrealistic facility occupancies or a non-domestic sector unlike the governorate average — and is investigated, not averaged away.")
table(["Component", "Basis", "Value (l/c/d)", "Source"], [
 ["Domestic", "measured, Adh Dhahirah", "164", "G201-p60; R0: 163.5 from billing"],
 ["Non-domestic", "+22% of domestic (governorate ratio)", "36.1", "G201-p60-61"],
 ["Governmental", "+14% of domestic (governorate ratio)", "23.0", "G201-p60"],
 ["Total water demand", "sum (aggregate planning view)", "223", "—"],
], widths=[1.7, 2.4, 1.2, 1.9], font=9)
tab_caption("Water demand build-up for Ibri (aggregate per-capita view)")

# ================= 6 STEP 3 RETURN =================
H(1, "Step 3 — Wastewater Return")
H(2, "The concept: not all water comes back")
para("Part of the supplied water never reaches the sewer: garden and farm irrigation percolates or evaporates, evaporative (desert) coolers and cooling towers evaporate their feed, washing water is thrown on yards, mosques' ablution water often irrigates landscaping. The return rate is the measured fraction that does come back, and it differs by consumer type (G201-p71, Table 19):")
table(["Stream", "Return rate", "Why this value"], [
 ["Domestic (and tankered)", "85%", "most indoor use returns; ~15% lost to gardens, coolers, outdoor cleaning"],
 ["Non-domestic + governmental", "54%", "large landscaped compounds, cooling and process losses make commercial/institutional use far more consumptive"],
], widths=[2.2, 1.2, 3.6], font=9)
tab_caption("Return rates to the sewer by consumer stream (G201-p71 Table 19)")
para("The per-capita wastewater generation follows by applying each return rate to its own stream and summing the results. As in Step 2, the summation is the aggregate planning view — each stream keeps its own rate, and only the resulting sewage quantities (which do all end up in the same pipe) are added:")
equation(q_("ww") + mr(" = ") + q_("dom") + mr(" × 0.85 + (") + q_("nd") + mr(" + ") + q_("gov") + mr(") × 0.54"))
para("For Ibri: 164 × 0.85 + (36.1 + 23.0) × 0.54 = 139.4 + 31.9 ≈ 171 l/c/d of sewage per person. This single number now carries the whole demand side of the calculation.")

# ================= 7 STEP 4 ADDITIONS =================
H(1, "Step 4 — Additions: Infiltration and Tankered Sewage")
H(2, "Infiltration — what it is and how it is estimated")
para("Sewers are not watertight. Groundwater and soil moisture enter through pipe joints, manhole walls, and — in older systems — cracks and illegal connections. This infiltration flows continuously, day and night (it is what remains in the pipe at 4 a.m., Figure 1), consumes pipe and treatment capacity, and dilutes the sewage. It cannot be zero, so it is budgeted explicitly (G201-p72):")
bullet("720 litres per day per kilometre of sewer — a linear allowance reflecting tight modern joints and (in Ibri's inland setting) deep groundwater.", bold_lead="New networks: ")
bullet("10% of the wastewater flow; up to 40% for coastal or high-groundwater systems.", bold_lead="Existing inland networks: ")
bullet("None. The system is strictly separate; rainfall does not enter the design flows (G201-p72).", bold_lead="Stormwater allowance: ")
para("The R0 model provisionally applies the 10 percent rule to selected settlements. For the new Ibri network this is roughly ten times the guideline's linear allowance — a conservative choice that is safe for STP capacity but not free: carried through to ultimate flows it adds several thousand m3/d of phantom flow to the STP sizing and dilutes the design concentrations. The recommended treatment (Section 15) is to carry the guideline value as the design basis, keep 10 percent as an upper sensitivity bound, and have NWS confirm the basis at kickoff.")
H(2, "Tankered sewage")
para("Properties not yet connected to a network discharge to holding tanks emptied by vacuum tankers ('yellow tankers'), which discharge at the STP's tanker reception facility. Tanker sewage is therefore part of the STP inflow from day one, while network flows ramp up as connections are made. Nationally, tankers deliver about 17 percent of STP inflow today; design coverage reaches 100 percent by the end of the planning period, phasing tanker deliveries out (G201-p73). Two project-specific points:")
bullet("The R0 model collects tankered flows from settlements within 25 km of the STP. This radius is an R0 assumption with no guideline source — it must not be mixed into design calculations until NWS confirms it (Section 15).")
bullet("A recent site visit found tankers delivering sewage from camps up to 150 km away. This is outside any assumption in the scope and materially affects the tanker reception sizing, the early-years flow balance and possibly the STP odour/septicity design (long-haul sewage arrives septic). It is flagged as a project risk requiring an NWS policy decision: which catchment is the Ibri STP obliged to accept?")

# ================= 8 STEP 5 AVERAGE =================
H(1, "Step 5 — Average Daily Flow")
para("The average daily flow assembles everything so far: people times per-capita sewage, plus the two additions of Step 4:")
equation(Q("adf") + mr(" = ") + frac(mr("P × ") + q_("ww"), mr("1000")) + mr(" + ") + Q("inf") + mr(" + ") + Q("tank"))
para("where P is the population served (capita), q(ww) the per-capita wastewater generation (l/c/d, = 171 for Ibri), Q(inf) the infiltration allowance and Q(tank) the tankered deliveries, all in m3/d. The division by 1000 converts litres to cubic metres.")
para("Qadf equals the AAF of Section 3 and is the backbone quantity of the design: every later flow is derived from it, the biological STP sizing rests on it, and the phasing analysis compares it across model years. In the worked example (Section 14) it evaluates to 1,731 m3/d, i.e. 20.0 L/s.")

# ================= 9 STEP 6 PEAKS =================
H(1, "Step 6 — Peak Flows")
H(2, "What a peak factor is and why it shrinks with catchment size")
para("Pipes and pumps must carry the worst hour, not the average day — a sewer sized for Qadf would surcharge every morning (Figure 2). The peak factor is the multiplier that converts the average flow into that governing peak. Because individual households' peaks do not coincide, the aggregate flow smooths out as the catchment grows: PF is large for a street (approaching the cap of 5), small for a city trunk (approaching about 1.6). All peak-factor formulas are therefore decreasing functions of flow. Peaking applies to the sewage component only — infiltration is a steady base flow and is added after peaking.")
H(2, "The two permitted formulas — and why they differ")
para("The guidelines permit two empirical formulas (G201-p71-72). They are not two estimates of the same number; they answer different questions:")
bullet("gives the ratio of the peak-hour flow to the average flow. Developed for the Oman IMP 2024, it is the current national method. Qm is the mean flow in L/s:", bold_lead="Peltier (peak-hour factor) ")
equation(mr("PF") + mr(" = 1.5 + ") + frac(mr("1"), sqrt(Q("m"))))
bullet("is a regression fitted to observed maximum-day flows (US practice, valid above ~100 connected properties); it returns the peak-day flow directly, both flows in Ml/d:", bold_lead="Merrimack (peak-day flow) ")
equation(Q("pdf") + mr(" = 2.65 × ") + ssup(mr("(") + Q("adf") + mr(")"), mr("0.879")))
para("Both are capped by the absolute limit PF ≤ 5.0 on the hourly factor (G201-p72). Figure 6 plots the two over the practically relevant flow range.")
pic(PFCHART, w=5.9)
fig_caption("Peltier and Merrimack peak factors versus average flow, with the PF = 5.0 cap and the worked example marked")
para("Why do they disagree (1.72 vs 2.48 at 20 L/s)? Three reasons, all visible in Figure 6:")
bullet("Peltier's 1.5 asymptote is a peak-hour ratio for large flows; Merrimack tracks the maximum day, and its implied factor (2.65 × Qadf to the power −0.121) stays higher across the range. A peak day and a peak hour are different events.", bold_lead="Different peak definitions. ")
bullet("Peltier was fitted to Omani IMP data; Merrimack to New England systems with different habits, appliances and infiltration behaviour. Empirical regressions carry their calibration data with them.", bold_lead="Different source data. ")
bullet("Merrimack's exponent makes its factor fall very slowly with size, so the divergence grows for large flows.", bold_lead="Different damping. ")
para("Practical guidance: use Peltier for hydraulic (peak-hour) sizing as the current IMP method, use Merrimack as a peak-day cross-check for storage and process buffering, and obtain NWS's confirmation of the binding choice at kickoff — the difference is roughly 40 percent of pipe capacity, which is not a rounding issue. The R0 model additionally applies a +20 percent weekly peak with no guideline source; it is flagged in Section 15.")

# ================= 10 STEP 7 LOADS =================
H(1, "Step 7 — Organic (Pollution) Loads")
H(2, "What the loads are")
para("Flow says how much liquid arrives; loads say how much pollution it carries. The STP's biological reactors, aeration system, clarifiers and sludge line are sized by the daily mass of pollutants, in kilograms per day — not by concentration. Three parameters characterise domestic sewage:")
bullet("the mass of oxygen that bacteria consume in five days while degrading the biodegradable organic matter in the sample. It is the standard measure of 'how much food for bacteria' the sewage carries, and it directly sets the biological reactor volume and the oxygen (aeration energy) demand.", bold_lead="BOD5 (biochemical oxygen demand, 5-day): ")
bullet("the particulate matter suspended in the sewage. It settles in clarifiers and largely becomes primary/secondary sludge, so it sizes the clarifiers and the sludge handling line.", bold_lead="TSS (total suspended solids): ")
bullet("the oxygen equivalent of everything chemically oxidisable, measured in a fast chemical test. COD ≥ BOD5 always; their ratio measures biodegradability — domestic sewage runs COD/BOD = 1.8-2.2 (G203-p74), and a higher ratio warns of industrial or septic inputs that biology alone cannot remove.", bold_lead="COD (chemical oxygen demand): ")
H(2, "Why loads are fixed per person, not per litre")
para("A person excretes and washes away a nearly constant daily mass of organic matter regardless of how much water carries it. The guidelines therefore fix minimum per-capita loads (G203-p74): at least 60 g BOD5 and 80 g TSS per capita per day. Load calculation is then simply mass times population:")
equation(mr("L") + mr(" = ") + frac(mr("P × ") + ssub(mr("l"), mr("cap")), mr("1000")))
para("with L in kg/d, P the population and l(cap) the per-capita load in g/c/d. Concentration is always derived afterwards, never assumed:")
equation(mr("C") + mr(" = ") + frac(mr("L × 1000"), Q("adf")))
para("with C in mg/l. Because the mass is fixed while Oman's water use is low, the concentration comes out high: around 300-400 mg/l BOD5, versus about 200 mg/l in water-rich European systems. This matters in practice — a concentrated influent shifts the STP process choice (oxygen transfer, sludge yield, possible primary treatment) and makes the infiltration assumption visible in the influent quality data: excessive assumed infiltration would predict dilute sewage that the STP's laboratory records will contradict.")

# ================= 11 STEP 8 USES =================
H(1, "Step 8 — Which Flow Sizes What")
para("Each element of the system is governed by the flow that physically challenges it. A pipe never sees the annual average — it sees this morning's peak; a biological reactor barely notices the peak hour — bacteria respond to the daily mass. The table below assigns the governing flow to each element, and the notes below explain each line.")
table(["Design element", "Governing flow", "Additional rules"], [
 ["Gravity pipe sizing", "Peak (hourly) flow", "d/D ≤ 0.65 (D ≤ 350 mm) or ≤ 0.50 (D > 350 mm); v = 0.75-3.0 m/s; Table 11 minimum gradients (G203-p26-29)"],
 ["Pumping stations / force mains", "Peak flow, with any one pump out of service", "v = 1.0 (intermittent) to 2.5 m/s max (G203-p39, p50)"],
 ["STP hydraulic pass-through", "PHF", "screens, channels, distribution structures pass the peak hour (G203-p65-66)"],
 ["STP biological process", "AAF + organic loads", "reactor volume, aeration, clarifiers, sludge line (G203-p65-66)"],
 ["TE / TSE pipelines", "TSE production = 95% of STP inlet", "TE roughness penalty: epsilon +30%, C −10% vs potable values (G202-p104)"],
], widths=[1.9, 1.8, 2.8], font=8)
tab_caption("Governing flow for each design element")
bullet("Gravity pipes carry the peak flow only partly full: the depth-to-diameter limit (d/D) keeps an air space for ventilation and capacity reserve, the minimum velocity 0.75 m/s at peak keeps solids moving (self-cleansing), and the maximum 3.0 m/s prevents abrasion of the invert.")
bullet("Pump stations must deliver the peak with their largest unit out of service (duty/standby) — pumps fail, sewage does not stop.")
bullet("The STP splits in two: everything the sewage flows through is sized on PHF, while the biological process is sized on AAF plus the Step 7 loads. Sizing biology on PHF would roughly double the reactors for no benefit; sizing hydraulics on AAF would flood the works every morning.")
bullet("The TE network is designed to G202 criteria with the treated-effluent roughness penalty, because TSE carries residual solids and biofilm potential that potable water does not.")

# ================= 12 STEP 9 STP =================
H(1, "Step 9 — STP Incoming Flow, TSE and Sludge")
H(2, "The STP design flow")
para("The flow the treatment plant must be designed to receive is a defined sum (G203-p65 Table 29, G201-p73), expressed as:")
equation(Q("STP") + mr(" = 1.10 × (") + Q("adf") + mr(" + ") + Q("tank") + mr(")"))
para("read as: the network's average flow including its infiltration, plus the tankered deliveries arriving by road, all increased by a 10 percent operational allowance. The allowance covers what the estimate cannot see: metering error, unplanned connections, wet-year infiltration, and the operational reality that plants must work with one unit in maintenance. The hydraulic elements of the plant then apply the Step 6 peak factors on top of this average, while the biological elements combine it with the Step 7 loads.")
para("The resulting capacity places the plant in the G203-p65 size categories (Medium 500-20,000 m3/d, Large ≥ 20,000 m3/d), and — per the TOR — the Phase I capacity relative to 20,000 m3/d decides whether the new STP's preliminary design and EPC tender remain within this consultancy.")
H(2, "TSE — the product")
para("The plant returns 95 percent of its inflow as treated sewage effluent (G201-p73); the remaining 5 percent leaves with the sludge and process losses. TSE is not waste: it is the feedstock of the TE network that this project also designs, irrigating landscaping and farms. Its quality must meet Omani Class A standards where discharge to wadis is foreseen (G203-p73). The TSE volume from the equation above is therefore the input to the TE network's own demand-and-distribution design.")
H(2, "Sludge — the by-product")
para("Treatment concentrates the removed pollution into sludge — as a planning rate, about 0.25 kg of dry solids per m3 treated (R0). The sludge line thickens and dewaters it (volume reduction), stabilises it (odour and pathogen control), and directs it to its fate: beneficial reuse (soil conditioning, subject to quality) or landfill disposal. The TOR requires a sludge management strategy as a concept-stage deliverable, and the Step 7 TSS load is the primary input to its sizing.")
pagebreak()

# ================= 13 WORKED EXAMPLE =================
H(1, "Worked Example")
para("The example is constructed for this tutorial (it is not taken from a source document): a hypothetical settlement of 10,000 persons, served by 25 km of new sewers, lying inland with deep groundwater — deliberately round numbers so each step is easy to follow. Values are rounded for readability.", italic=True)
para("Walk-through of the solution:")
bullet("Steps 1-2: the population is given (10,000). Water demand = 164 l/c/d domestic × 1.36 (adding 22% + 14%) = 223 l/c/d, i.e. 2,230 m3/d of water supplied.")
bullet("Step 3: sewage per person = 164 × 0.85 + 59.1 × 0.54 = 171.3 l/c/d, i.e. 1,713 m3/d entering the sewers.")
bullet("Step 4: infiltration = 720 L/d/km × 25 km = 18 m3/d — barely 1 percent of the sewage, as expected for a new inland network. (Under the R0's 10 percent rule it would be 171 m3/d — the difference the reconciliation register tracks.) No tankers: the settlement is fully networked.")
bullet("Step 5: Qadf = 1,713 + 18 = 1,731 m3/d. Divide by 86.4 to convert m3/d to L/s: 20.0 L/s.")
bullet("Step 6: Peltier PF = 1.5 + 1/sqrt(20.0) = 1.72, so peak-hour flow = 1.72 × 20.0 = 34.5 L/s — this sizes the outfall sewer. Merrimack: Qadf = 1.731 Ml/d, so Qpdf = 2.65 × 1.731^0.879 = 4.29 Ml/d (49.7 L/s, an implied factor of 2.48) — the peak-day cross-check.")
bullet("Step 7: loads = 10,000 × 60 / 80 / 120 g/d = 600 kg BOD5, 800 kg TSS, 1,200 kg COD per day (COD taken at 2.0 × BOD). Concentrations = load × 1000 / 1,731: BOD5 347 mg/l, TSS 462 mg/l, COD 693 mg/l — correctly in the concentrated range expected for Oman.")
bullet("Steps 8-9: STP design flow = 1.10 × 1,731 = 1,904 m3/d (Medium category); TSE production = 0.95 × 1,904 = 1,809 m3/d available to the TE network; sludge ≈ 0.25 × 1,904 = 476 kg/d dry solids.")
table(["#", "Step", "Calculation", "Result"], [
 ["1", "Population", "given", "10,000 cap"],
 ["2", "Water demand", "164 × 1.36", "223 l/c/d → 2,230 m3/d"],
 ["3", "Wastewater return", "164 × 0.85 + 59.1 × 0.54", "171.3 l/c/d → 1,713 m3/d"],
 ["4", "Infiltration (new network)", "720 L/d/km × 25 km", "+18 m3/d (≈ 1%)"],
 ["5", "Average flow Qadf", "1,713 + 18", "1,731 m3/d = 20.0 L/s"],
 ["6a", "Peltier peak (hourly)", "PF = 1.5 + 1/√20.0 = 1.72", "peak 34.5 L/s"],
 ["6b", "Merrimack peak (daily)", "2.65 × 1.731^0.879", "4.29 Ml/d = 49.7 L/s (PF 2.48)"],
 ["7", "Loads BOD5 / TSS / COD", "10,000 × 60 / 80 / 120 g/d", "600 / 800 / 1,200 kg/d"],
 ["7b", "Concentrations", "load × 1000 / Qadf", "BOD5 347, TSS 462, COD 693 mg/l"],
 ["8", "STP design flow", "1.10 × 1,731", "1,904 m3/d"],
 ["9", "TSE production", "0.95 × 1,904", "1,809 m3/d"],
], widths=[0.45, 1.9, 2.5, 1.9], font=9)
tab_caption("Worked example — hypothetical 10,000-person settlement (illustrative)")
H(2, "Sanity checks — and why they work")
para("Three quick checks catch most calculation errors, each grounded in the physics of the previous sections:")
bullet("Because the per-capita mass is fixed (Step 7) while Omani water use is low, dividing the two must land in this range. A dilute result (~200 mg/l) almost always means the flow is overstated — typically an inflated infiltration or per-capita water figure.", bold_lead="BOD5 concentration 300-400 mg/l. ")
bullet("The Peltier structure guarantees PF > 1.5, and the guideline caps it at 5.0. A computed PF outside this band means the flow unit is wrong (m3/d fed into a formula expecting L/s is the classic error).", bold_lead="Peak factor between 1.5 and 5.0. ")
bullet("At 720 L/d/km, even hundreds of kilometres of sewer add only a few percent. If infiltration rivals the sewage flow in a new inland design, an existing-network rate (10-40%) has leaked into the wrong context.", bold_lead="Infiltration a small fraction of sewage for a new inland network. ")

# ================= 14 RECONCILIATION =================
H(1, "Guideline vs Inception R0 — Reconciliation Register")
para("The R0 demand model and the guidelines agree on the core parameters; the differences below are carried openly until confirmed with NWS at kickoff. None of them invalidates the method of this tutorial — they change input values, and the tutorial states at each point which value it uses.")
table(["Item", "Guideline (binding)", "R0 adopted", "Position"], [
 ["Domestic per-capita demand", "164 l/c/d (G201-p60)", "163.5 computed from billing", "Consistent — use 164"],
 ["Return ratios", "85% / 54% (G201-p71)", "Same", "Consistent"],
 ["Infiltration", "720 L/d/km, new networks (G201-p72)", "10% of wastewater flow", "Guideline value as design basis; 10% kept as conservative upper sensitivity — NWS to confirm"],
 ["Peaking", "Peltier / Merrimack, PF ≤ 5 (G201-p71-72)", "+20% weekly peak added", "No guideline source — basis to be confirmed"],
 ["Tanker catchment", "Not specified", "25 km radius", "R0 assumption — do not mix into design until NWS confirms; site visit shows up to 150 km actual"],
 ["STP margin / TSE ratio", "+10% / 95% (G201-p73)", "Same", "Consistent"],
 ["Sludge rate", "Not specified", "0.25 kg/m3", "R0 planning value — refine at process design"],
], widths=[1.5, 2.0, 1.6, 1.9], font=8)
tab_caption("Reconciliation of guideline values against the R0 demand model")

# ================= 15 CONCLUSION =================
H(1, "Conclusions")
bullet("The sewage flow and load calculation is a fully determined nine-step chain: every parameter traces to a cited guideline value, an NCSI statistic, or a flagged assumption — nothing is discretionary once the inputs are fixed.")
bullet("Population is the root input and its two routes serve different decisions: census projection for the phased facilities (STP), plot saturation for the once-only network. Their consistency (projection below ceiling, zone by zone) is itself a design check.")
bullet("Flows and loads are independent tracks that meet at the STP: flows follow the water, loads follow the people. Oman's low water use therefore produces concentrated sewage (300-400 mg/l BOD5), which the process design must expect.")
bullet("The design-governing quantities are: Route B saturation flow for pipes; Route A dated flows for STP phases; PHF for everything hydraulic; AAF + loads for everything biological; and the +10% allowance at the plant gate.")
bullet("Four input questions remain open — infiltration basis, peaking basis, tanker catchment, occupancy rate — and all four are data/policy questions for NWS, not methodological gaps.")
H(1, "Recommendations")
bullet("Request at kickoff: NCSI housing-unit counts for the occupancy rate (not in the R0 package), electricity account counts per settlement (for sub-settlement disaggregation), and NWS confirmation of the infiltration and peaking bases.")
bullet("Adopt the guideline infiltration (720 L/d/km) as the design basis for the new network and carry the R0's 10 percent as an upper sensitivity, so that STP phasing is not driven by phantom flow.")
bullet("Use Peltier for hydraulic sizing (current IMP method) with Merrimack as a peak-day cross-check, pending NWS confirmation.")
bullet("Obtain an NWS policy decision on the tanker catchment obligation (25 km assumption vs the observed 150 km deliveries) before sizing the tanker reception facility.")
bullet("Validate the aggregate non-domestic allowance (22% + 14%) against the spatially-assigned Table 12 loads once the land-use model is built, and investigate any large discrepancy.")

# ================= 16 REFERENCES =================
H(1, "References")
bullet("PAM-GUD-201 — General Design Guidelines v1.0, Rev 01, Nama Water Services (cited G201-p##).")
bullet("PAM-GUD-202 — Potable Water & Treated Sewerage Effluent (TSE) Design Guidelines v1.0, Rev 01, Nama Water Services (cited G202-p##).")
bullet("PAM-GUD-203 — Wastewater Design Guidelines v1.0, Rev 01, Nama Water Services (cited G203-p##).")
bullet("Terms of Reference, Section 03, Tender T/2719110/2025, Nama Water Services (cited TOR).")
bullet("Ibri Sewer Demand R0 workbook and Inception Report R0, Renardet, August 2026 (cited R0).")
bullet("NCSI population and housing statistics, National Centre for Statistics and Information, data portal (as transmitted in the R0 workbook).")

# ================= APPENDIX =================
H(1, "Appendix A — NCSI Population Series, Ibri Wilayat")
yrs = sorted(NCSI)
table(["Year"] + [str(y) for y in yrs],
      [["Population"] + [f"{NCSI[y]:,}" for y in yrs]], font=7)
tab_caption("Full NCSI population series for Ibri wilayat as carried in the R0 workbook (2021-2033)")
para("Growth rates implied by the series decline from 2.97 %/yr (2022) to 1.29 %/yr (2033). The connected-population ratio in the R0 workbook (share of population on the potable network) rises from 46.7% (2021) to 74.6% (2033).")

# ---- populate List of Figures / List of Tables at the front markers ----
def fill_list(marker, items):
    for it in items:
        p = doc.add_paragraph(it)
        p.paragraph_format.space_after = Pt(2)
        for r in p.runs: r.font.size = Pt(10)
        marker._p.addprevious(p._p)
fill_list(LOF_MARK, FIGS)
fill_list(LOT_MARK, TABS)

doc.save(OUT)
print("saved", OUT, "| figures:", len(FIGS), "| tables:", len(TABS))
