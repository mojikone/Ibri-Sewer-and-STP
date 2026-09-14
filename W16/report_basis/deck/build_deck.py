"""The meeting deck for the Design Basis Report: one hour, Wednesday 16 September 2026.

Built on the firm's kick-off presentation (Data/Received/2621/Kick-off Meeting Presentation
... R2.pptx, outside the repository): its cover, Q&A and Thank-you slides are kept and the
content slides are drawn on its blank layout with the same title bar, rule and client logo.
Every number is read from the report's facts modules, so the deck and the report agree.

    python build_deck.py            writes Ibri_Design_Basis_Meeting_2026-09-16.pptx and slide PNGs
"""
import copy
import io
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
BASIS = os.path.dirname(HERE)
sys.path.insert(0, BASIS)
sys.path.insert(0, os.path.join(os.path.dirname(BASIS), "report"))
import facts_basis as B  # noqa: E402
import facts_w14 as F  # noqa: E402
from decisions import APPROVALS, INFORMED, DATA_REQUESTS  # noqa: E402

KICKOFF = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASIS))), "..", "Data", "Received", "2621",
                       "Kick-off Meeting Presentation for Ibri New STP, Sewer & TE Networks R2.pptx")
IMG = os.path.join(BASIS, "img")
IMG_R = os.path.join(os.path.dirname(BASIS), "report", "img")
OUT = os.path.join(HERE, "Ibri_Design_Basis_Meeting_2026-09-16.pptx")
MEETING = "Wednesday 16th September 2026"

NAVY = RGBColor(0x1F, 0x49, 0x7D); BLUE = RGBColor(0x00, 0x70, 0xC0); MID = RGBColor(0x4F, 0x81, 0xBD)
GREY = RGBColor(0x5A, 0x5A, 0x5A); RED = RGBColor(0xC0, 0x50, 0x4D); RULE = RGBColor(0x89, 0xAC, 0xAF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF); LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
FONT = "Calibri"
fmt = F.fmt

# the content area on the 67.3 x 38.1 cm slide, under the title bar
L, T, W, H = 1.5, 6.6, 64.3, 30.0


# ------------------------------------------------------------------ furniture
def _delete_slides(prs, keep):
    """Drop the slides not in keep. The kept slides' parts are renamed out of the way:
    python-pptx names a new slide part by the slide count, so after deletions a new slide
    would collide with a kept part of the same name and the file would not open."""
    from pptx.opc.packuri import PackURI
    lst = prs.slides._sldIdLst
    for i, sld in enumerate(list(lst)):
        if i not in keep:
            prs.part.drop_rel(sld.rId); lst.remove(sld)
    for k, slide in enumerate(prs.slides, 1):
        slide.part.partname = PackURI(f"/ppt/slides/slide{900 + k}.xml")
        if slide.has_notes_slide:
            slide.notes_slide.part.partname = PackURI(f"/ppt/notesSlides/notesSlide{900 + k}.xml")


def _move_to_end(prs, n):
    lst = prs.slides._sldIdLst; items = list(lst)
    for sld in items[:n]:
        pass
    # the first n kept end slides sit after the cover: move them to the end
    for sld in items[1:1 + n]:
        lst.remove(sld); lst.append(sld)


def title_bar(slide, text, logo):
    tb = slide.shapes.add_textbox(Cm(0.6), Cm(0.6), Cm(57.2), Cm(4.0))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(40); r.font.bold = True; r.font.color.rgb = BLUE; r.font.name = "Arial"
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Cm(0.6), Cm(5.2), Cm(57.4), Cm(5.2))
    ln.line.color.rgb = RULE; ln.line.width = Pt(6)
    slide.shapes.add_picture(io.BytesIO(logo), Cm(57.8), Cm(0.6), Cm(7.7), Cm(4.9))


def text(slide, left, top, width, height, lines, size=24, colour=GREY, bold_first=False, align=PP_ALIGN.LEFT, spacing=6):
    """A text box; lines: str or (str, {"bold":..,"size":..,"colour":..}); a line starting with
    '• ' is a bullet."""
    tb = slide.shapes.add_textbox(Cm(left), Cm(top), Cm(width), Cm(height))
    tf = tb.text_frame; tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(spacing)
        s, opt = (ln, {}) if isinstance(ln, str) else ln
        r = p.add_run(); r.text = s
        r.font.size = Pt(opt.get("size", size)); r.font.name = FONT
        r.font.bold = opt.get("bold", bold_first and i == 0); r.font.color.rgb = opt.get("colour", colour)
    return tb


def bignum(slide, left, top, width, number, label, colour=NAVY, size=72):
    tb = slide.shapes.add_textbox(Cm(left), Cm(top), Cm(width), Cm(8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = number; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = colour; r.font.name = FONT
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    r = p2.add_run(); r.text = label; r.font.size = Pt(22); r.font.color.rgb = GREY; r.font.name = FONT
    return tb


def pic(slide, path, left, top, width, height):
    """A picture fitted inside the box, centred."""
    from PIL import Image
    iw, ih = Image.open(path).size
    k = min(width / iw, height / ih)
    w, h = iw * k, ih * k
    return slide.shapes.add_picture(path, Cm(left + (width - w) / 2), Cm(top + (height - h) / 2), Cm(w), Cm(h))


def table(slide, headers, rows, left, top, width, col_w=None, size=18, row_h=1.25, first_left=True, bold_rows=(), left_cols=()):
    n, m = len(rows) + 1, len(headers)
    left_cols = set(left_cols) | ({0} if first_left else set())
    shp = slide.shapes.add_table(n, m, Cm(left), Cm(top), Cm(width), Cm(row_h * n))
    tbl = shp.table
    tbl.first_row = True; tbl.horz_banding = False
    if col_w:
        k = width / sum(col_w)
        for j, w in enumerate(col_w):
            tbl.columns[j].width = Cm(w * k)
    for j, htxt in enumerate(headers):
        c = tbl.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = NAVY
        c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j in left_cols else PP_ALIGN.CENTER
        r = c.text_frame.paragraphs[0].add_run(); r.text = str(htxt); r.font.size = Pt(size); r.font.bold = True
        r.font.color.rgb = WHITE; r.font.name = FONT
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = WHITE if i % 2 else LIGHT
            c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j in left_cols else PP_ALIGN.CENTER
            txt = "" if val is None else str(val)
            for k, seg in enumerate(txt.split("**")):
                if not seg:
                    continue
                r = c.text_frame.paragraphs[0].add_run(); r.text = seg; r.font.size = Pt(size); r.font.name = FONT
                r.font.bold = (k % 2 == 1) or (i - 1 in bold_rows); r.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_top = c.margin_bottom = Cm(0.12)
    return shp


def ask_box(slide, left, top, width, text_, n=None):
    """The decision line, boxed like the report's."""
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(left), Cm(top), Cm(width), Cm(3.6))
    shp.fill.solid(); shp.fill.fore_color.rgb = RGBColor(0xEA, 0xF1, 0xF8)
    shp.line.color.rgb = MID; shp.line.width = Pt(1.5)
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Cm(0.5)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = (f"Decision {n}.  " if n else ""); r.font.bold = True; r.font.size = Pt(24); r.font.color.rgb = NAVY; r.font.name = FONT
    r = p.add_run(); r.text = text_; r.font.size = Pt(24); r.font.color.rgb = RGBColor(0x26, 0x26, 0x26); r.font.name = FONT
    return shp


def notes(slide, text_):
    slide.notes_slide.notes_text_frame.text = text_


def ask_short(n):
    """The decision's one-line ask, as in the register, without the section reference."""
    what = APPROVALS[n - 1][3]
    return what.rsplit(" (Section", 1)[0] + "."


# ------------------------------------------------------------------ the deck
def build():
    prs = Presentation(KICKOFF)
    logo = None
    for sh in prs.slides[1].shapes:
        if sh.name == "Picture 5":
            logo = sh.image.blob
    # keep the cover (0), the Q&A (10) and the Thank-you (11); drop the rest
    _delete_slides(prs, keep={0, 10, 11})
    blank = next(l for l in prs.slide_layouts if l.name == "6_Custom Layout")

    # the cover's texts
    cover = prs.slides[0]
    for sh in cover.shapes:
        if sh.name == "TextBox 7":
            tf = sh.text_frame
            lines = ["Design Basis Report", "", "Meeting for approval", f"Date: {MEETING}"]
            for i, p in enumerate(tf.paragraphs):
                if i < len(lines):
                    for r in p.runs[1:]:
                        r.text = ""
                    if p.runs:
                        p.runs[0].text = lines[i]
        if sh.name == "TextBox 1":
            tf = sh.text_frame
            # the box's paragraphs: 0 empty, 1 "Project:", 2 the title, 3 empty, 4 "Tender No:", 5 the number
            want = {1: "Project:", 2: "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri",
                    4: "Tender No:", 5: "T / 2719110 / 2025"}
            for i, p in enumerate(tf.paragraphs):
                if i in want and p.runs:
                    for r in p.runs[1:]:
                        r.text = ""
                    p.runs[0].text = want[i]
    notes(cover, "One hour. The purpose: the seven decisions on the answer sheet at the end. Everything else is the reason for each.")

    t = F.totals(); ult = t["ultimate"]; pf = B.plant_flows(); pl = B.process_loads(); ts = B.tse()
    ps = F.plot_summary(); mc = F.meter_counts(); st = F.settlement_table(); no = B.no_overflow(); gr = F.growth_rates()
    ib = next(r for r in st if r["key"] == "IBRI"); fm = B.free_meters()
    slides = []

    def new(title):
        s = prs.slides.add_slide(blank); title_bar(s, title, logo); slides.append(s); return s

    # 2 why this meeting
    s = new("Why this meeting: the foundation before the design")
    text(s, L, T + 1, 34, 20, [
        ("The concept design will be one document. Its options for the network and the STP rest on the numbers in the Design Basis Report.", {"size": 26}),
        ("If a number changes after the options are drawn, the options are drawn again.", {"size": 26}),
        ("So the foundation comes first: where the settlements are, how many people, how much the land can hold, and the sewage every element must carry.", {"size": 26}),
        ("Only what the guideline does not settle is put to you. The guideline's own values are adopted and reported.", {"size": 26, "colour": NAVY, "bold": True}),
    ], spacing=14)
    bignum(s, 40, T + 1, 12, str(len(APPROVALS)), "decisions to take", colour=NAVY)
    bignum(s, 52, T + 1, 12, str(len(INFORMED)), "values adopted, for information", colour=MID)
    bignum(s, 40, T + 12, 12, "7", "data requests", colour=GREY)
    bignum(s, 52, T + 12, 12, "40", "pages in the report", colour=GREY)
    notes(s, "Frame the hour: seven yes/no decisions. Say that the report is the record; today is for the decisions.")

    # 3 the chain
    s = new("From the meter to the STP: the chain of the numbers")
    pic(s, os.path.join(IMG_R, "D3_flow.png"), L, T, 36, H)
    text(s, 40, T + 1, 25, 26, [
        ("• Every domestic electricity meter is a property; the settlement's occupancy makes it people.", {}),
        ("• Water per person from the guideline; shops and government as shares; the return to the sewer per stream.", {}),
        ("• The plot carries an average flow for 2024, 2030, 2055 and the year the land is full.", {}),
        ("• The pipe adds the peak and the infiltration. The STP adds the margin.", {}),
        (f"• Today: {fmt(t['pop_today'])} people, {fmt(t['q_today'])} m³/d. Saturation {ult}: {fmt(t['pop_ult'])} people, {fmt(t['q_ult'])} m³/d.", {"bold": True, "colour": NAVY}),
    ], size=24, spacing=12)
    notes(s, "Report Sections 3 to 7. Keep it to one minute: the point is that every later number comes from this chain.")

    # 4 decision 1 boundaries
    s = new("Decision 1 · The settlement boundaries")
    pic(s, os.path.join(IMG, "B01_boundaries.png"), L, T, 44, H - 4.2)
    text(s, 47, T + 0.5, 18, 20, [
        ("• Received: 26 polygons for 25 settlements, drawn round the built cores, not touching.", {}),
        ("• Four miss part of their plots: Tanam, Satwah, Al Makhtibyah, Bat.", {}),
        ("• Redrawn: every plot in one settlement, no gaps. Names, series and plots as received.", {}),
        ("• Every rule of the basis is applied per settlement; this is why it matters.", {"colour": NAVY, "bold": True}),
    ], size=22, spacing=12)
    ask_box(s, L, T + H - 3.6, W, ask_short(1), 1)
    notes(s, "Section 2. Red dashed = received, blue = redrawn. The ask: approve the redrawn boundaries.")

    # 5 decision 2 persons per property
    s = new("Decision 2 · Persons per property, by settlement")
    pic(s, os.path.join(IMG_R, "C02_occupancy.png"), L, T, 40, 22)
    text(s, 43, T + 0.5, 22, 22, [
        (f"• Occupancy = 2024 population ÷ properties counted. Ibri {ib['or_used']:.2f}; area-wide {F.census_rate():.2f}.", {}),
        ("• Floor 4.0: institutional housing (police, college) drags some settlements to 1 to 4; those properties discharge all the same.", {}),
        (f"• Cap {max(r['or_used'] for r in st):.2f}, the highest among settlements of 2,000 or more.", {}),
        ("• Under 1,000 people: 4.0, one property per plot, home share 0.9 (13 settlements).", {}),
        (f"• Result: {fmt(t['pop_today'])} people in 2024 against 116,452 in the census series.", {"bold": True, "colour": NAVY}),
    ], size=22, spacing=10)
    ask_box(s, L, T + H - 3.6, W, ask_short(2), 2)
    notes(s, "Section 3.2, Table 4 has all 25. Housing units are not published at settlement level; counted properties replace them.")

    # 6 decision 3 use of plot
    s = new("Decision 3 · The use of each plot")
    pic(s, os.path.join(IMG, "B02_landuse.png"), L, T, 44, H - 4.2)
    text(s, 47, T + 0.5, 18, 22, [
        (f"• The cadastre's own land-use field disagrees with the meters on {fmt(F.cadastre_disagreement() * 100)} % of the metered plots and has no government class.", {}),
        ("• The use is determined from what is on the plot: estate, heritage, farm meter, planted (satellite), then the meters by proportion.", {}),
        (f"• {fmt(ps['classes'].get('Residential', 0))} homes, {fmt(ps['classes'].get('Commercial', 0))} shops, {fmt(ps['classes'].get('Government', 0))} government, {fmt(ps['classes'].get('Agricultural', 0))} farms; {fmt(ps['empty'])} empty.", {}),
        ("• It decides where the shop and government water sits, not how much.", {"colour": NAVY, "bold": True}),
    ], size=22, spacing=12)
    ask_box(s, L, T + H - 3.6, W, ask_short(3), 3)
    notes(s, "Section 4. The 126 meters with no plot within 15 m are left out (about 140 people); the map is in the report.")

    # 7 adopted rates
    s = new("Adopted from the guideline: water, sewage and the rates (for information)")
    table(s, ["Value", "Adopted", "Source"], [
        ["Domestic water use", "164 l per person per day", "PAM-GUD-201 Table 11, Adh Dhahirah"],
        ["Shops and offices", "22 % of domestic, placed on the shop meters", "Table 11, the distributed ratio"],
        ["Government", "14 % of domestic, placed on the government meters", "Table 11; unit rates need quantities not held"],
        ["Return to the sewer", "85 % domestic and tanker; 54 % the rest", "Table 19"],
        ["A person in a new home", "171.3 l of sewage a day", "164 × 0.85 + 36 × 0.54 + 23 × 0.54"],
        ["Industrial estates (special)", "4,500 + 1,800 workers at 93 l/d", "an assumption until the estates' records"],
        ["Farm meters", "no sewage", "irrigation pumps; the house is metered separately"],
        ["Tanker water, private wells", "not in any flow", "no records held: requested"],
    ], L, T + 0.5, W, col_w=[18, 24, 22], size=22, row_h=2.6)
    notes(s, "Section 5. These are informed, not asked. If NWS wants to change 164 or the ratios, it is their call; the numbers move accordingly.")

    # 8 decision 4 overflow
    s = new("Decision 4 · When a settlement is full: the overflow")
    pic(s, os.path.join(IMG, "K03_overflow_totals.png"), L, T, 32, 15.5)
    pic(s, os.path.join(IMG, "K04_overflow_settlements.png"), L, T + 15.5, 32, 11)
    text(s, 36, T + 0.5, 29, 24, [
        ("• A settlement grows at the series' rate until its empty plots are built.", {}),
        (f"• With the overflow its further growth moves to its neighbours: every settlement fills by {ult}, {fmt(t['pop_ult'])} people.", {}),
        (f"• Without it, {len(no['never'])} settlements never fill before 2100, the area holds {fmt(no['totals'][ult]['pop_own'])} in {ult}, and {fmt(t['pop_ult'] - no['totals'][ult]['pop_own'])} people of the series have nowhere to go.", {}),
        ("• Ibri's overflow: Al Araqi 70 %, Al Qurayn 20 %, Shalashil 10 %, then Ad Dariz, then the nearest with room.", {}),
        ("• A sewer sized on own growth in those settlements is sized for land that never fills.", {"bold": True, "colour": NAVY}),
    ], size=22, spacing=10)
    ask_box(s, L, T + H - 3.6, W, ask_short(4), 4)
    notes(s, "Section 6.3, Table 9 by settlement, the map of the routes in the report. The largest single decision.")

    # 9 decision 5 horizon
    s = new("Decision 5 · The design horizon: 2055, or the year the land is full")
    table(s, ["", "2055 = 2030 + 25 years", f"{ult} = the land is full"], [
        ["People", fmt(t["pop"][2055]), fmt(t["pop_ult"])],
        ["Average sewage flow, m³/d", fmt(t["q"][2055]), fmt(t["q_ult"])],
        ["STP average with the margin, m³/d", fmt(pf[2055]["aaf"]), fmt(pf[ult]["aaf"])],
        ["STP peak hour with the margin, m³/d", fmt(pf[2055]["phf"]), fmt(pf[ult]["phf"])],
        ["What it means for the network", "cheaper; full while the plots around it are still being built", "laid once; runs at low flow for longer"],
    ], L, T + 0.5, 34, col_w=[13, 11, 11], size=21, row_h=2.6)
    pic(s, os.path.join(IMG_R, "C08_growth.png"), 37, T, 28, 17)
    text(s, 37, T + 17.5, 28, 8, [
        ("• The Terms of Reference name both: completion plus 25 years, and the saturation of the area.", {}),
        (f"• Saturation is {fmt((t['q_ult'] / t['q'][2055] - 1) * 100)} % more flow than 2055. The STP is staged on the series either way.", {}),
    ], size=21, spacing=8)
    ask_box(s, L, T + H - 3.6, W, ask_short(5), 5)
    notes(s, "Section 6.4. No recommendation in the report: the two horizons and what each implies. Get the year.")

    # 10 decision 6 growth beyond 2050
    s = new("Decision 6 · The growth beyond 2050")
    pic(s, os.path.join(IMG_R, "C12_growth_rate.png"), L, T, 36, 22)
    text(s, 40, T + 0.5, 25, 24, [
        ("• To 2040: the official forecast for the wilayat. 2041 to 2050: its extension in the Inception Report. Both are the client's own.", {}),
        (f"• From 2051 the series rises from {fmt(gr['r2051'], 1)} % a year to 2.40 by {gr['year_240']} and holds it to 2100, the horizon NWS instructed.", {}),
        ("• The guideline allows ten years of extension beyond a forecast; this goes further.", {}),
        ("• Only the rate is used. The series' 2100 total is not a target: the land fills first.", {"bold": True, "colour": NAVY}),
    ], size=22, spacing=12)
    ask_box(s, L, T + H - 3.6, W, ask_short(6), 6)
    notes(s, "Section 6.2. The rate after 2058 drives when the last settlements fill, not how many people the land holds.")

    # 11 the flow each element gets
    s = new("The flow each element is designed for")
    table(s, ["Element", "Sized on", "Checked on", "Adds"], [
        ["Plot", "its average flow, each year", "—", "nothing: no peak, no infiltration"],
        ["Pipe", "saturation flow of the plots upstream, peaked, + infiltration", "2030 flow × 61 % connected, peaked, no infiltration: self-cleansing", "Merrimack > 100 properties, Peltier ≤ 100; 720 l/d per km"],
        ["Pumping station", "peak of its catchment + infiltration, at saturation", "rising main 0.75 to 2.5 m/s (1.0 start-stop)", "12 m of cover is the limit at this stage"],
        ["Trunk sewers", "sum of the settlements upstream, peaked", "—", "same rules as the pipe"],
        ["STP", "average annual flow × 1.10 (biology, with the load)", "peak hourly flow × 1.10 (pass-through structures)", "infiltration of the network; tankers when recorded; maximum day from records"],
    ], L, T + 0.5, W, col_w=[9, 20, 20, 17], size=20, row_h=3.2)
    notes(s, "Section 7. All of it is the guideline's, adopted; the one departure is the next slide.")

    # 12 decision 7 gradients
    s = new("Decision 7 · Gradients and self-cleansing at the concept stage")
    pic(s, os.path.join(IMG, "K02_mara_minimal.png"), L, T, 34, 20)
    text(s, 38, T + 0.5, 27, 24, [
        ("• Every pipe laid at the guideline's Table 11 minimum gradient, rounded up to 0.05 % steps (our rounding, for round figures on the drawings).", {}),
        ("• The guideline also asks for the tractive-force test and the steeper of the two. The tension it needs is not given; 1 pascal is used.", {}),
        ("• At this stage the test only lists the pipes that need early washing; it steepens nothing.", {}),
        (f"• A pipe under 1.5 l/s is checked as if it carried 1.5: the curve asks {B.mara_smin_pct(1.5):.2f} %, so a 200 mm pipe at Table 11 always passes.", {}),
        ("• This is a departure from PAM-GUD-203 §4.2.2.1, stated for approval.", {"bold": True, "colour": NAVY}),
    ], size=21, spacing=10)
    ask_box(s, L, T + H - 3.6, W, ask_short(7), 7)
    notes(s, "Section 7.3 and Appendix A2. The test area gave 70 % of the length needing early washing, all 200 mm under 1.3 l/s.")

    # 13 STP flows and the recipe map
    s = new("The STP flows by year, and how to read any catchment off the map")
    pic(s, os.path.join(IMG, "B03_saturation.png"), L, T, 40, H)
    table(s, ["", "2030", "2055", str(ult)], [
        ["People", fmt(pf[2030]["people"]), fmt(pf[2055]["people"]), fmt(pf[ult]["people"])],
        ["Average from the plots", fmt(pf[2030]["qadf"]), fmt(pf[2055]["qadf"]), fmt(pf[ult]["qadf"])],
        ["**Average annual flow, +10 %**", f"**{fmt(pf[2030]['aaf'])}**", f"**{fmt(pf[2055]['aaf'])}**", f"**{fmt(pf[ult]['aaf'])}**"],
        ["**Peak hourly flow, +10 %**", f"**{fmt(pf[2030]['phf'])}**", f"**{fmt(pf[2055]['phf'])}**", f"**{fmt(pf[ult]['phf'])}**"],
    ], 43, T + 0.5, 22, col_w=[10, 4, 4, 4], size=18, row_h=2.2)
    text(s, 43, T + 13, 22, 14, [
        ("• One STP for the whole area, before infiltration and tankers.", {}),
        (f"• Infiltration to add: {pf['infil_per_km']:.2f} m³/d per km of sewer, with the margin.", {}),
        ("• The four steps on the map give any grouping of settlements its own STP flow by hand.", {}),
        ("• Maximum day flow: from the existing STP's records, requested.", {}),
    ], size=20, spacing=8)
    notes(s, "Section 7.5. If NWS asks about two plants: the map and the four steps answer it on the spot.")

    # 14 loads and TSE
    s = new("The load on the STP, and the treated effluent (for information)")
    table(s, ["Load at the STP", "2030", "2055", str(ult)], [
        ["BOD, kg/d (60 g per person per day)", fmt(pl[2030]["bod_kgd"]), fmt(pl[2055]["bod_kgd"]), fmt(pl[ult]["bod_kgd"])],
        ["Suspended solids, kg/d (80 g per person per day)", fmt(pl[2030]["tss_kgd"]), fmt(pl[2055]["tss_kgd"]), fmt(pl[ult]["tss_kgd"])],
        ["BOD as a concentration, mg/l (guideline range 350 to 400)", fmt(pl[2030]["bod_mgl"]), fmt(pl[2055]["bod_mgl"]), fmt(pl[ult]["bod_mgl"])],
    ], L, T + 0.5, 40, col_w=[22, 6, 6, 6], size=20, row_h=2.6)
    table(s, ["Treated effluent, m³/d", "2030", "2055", str(ult)], [
        ["STP inflow, design average", fmt(ts[2030]["inflow"]), fmt(ts[2055]["inflow"]), fmt(ts[ult]["inflow"])],
        ["Produced, 95 %", fmt(ts[2030]["produced"]), fmt(ts[2055]["produced"]), fmt(ts[ult]["produced"])],
        ["Delivered, less 10 % in the network", fmt(ts[2030]["delivered"]), fmt(ts[2055]["delivered"]), fmt(ts[ult]["delivered"])],
    ], L, T + 13, 40, col_w=[22, 6, 6, 6], size=20, row_h=2.6)
    text(s, 44, T + 0.5, 21, 26, [
        ("• No laboratory data for Ibri's sewage is held: the guideline's minimum per person is used until the existing STP's results arrive.", {}),
        ("• Sewage by tanker is far stronger (350 to 1,050 mg/l BOD) and is provided for separately once its records arrive.", {}),
        ("• Two industrial estates, workshops on the commercial tariff: no wet industry found, no separate line foreseen.", {}),
    ], size=21, spacing=12)
    notes(s, "Sections 7.6 to 7.8. Adopted, not asked.")

    # 15 data requests
    s = new("Seven data requests: each replaces an assumption with a record")
    table(s, ["Item", "What is asked for", "Why"], [[a, b, c] for a, b, c in DATA_REQUESTS],
          L, T + 0.5, W, col_w=[14, 26, 24], size=20, row_h=3.0)
    notes(s, "Section 9. None stops the concept design.")

    # 16 the answer sheet
    s = new("The answer sheet: seven decisions")
    rows = [[str(i + 1), title, ask_short(i + 1), "☐ Yes    ☐ No"] for i, (_, _, title, _) in enumerate(APPROVALS)]
    table(s, ["", "Decision", "The ask", "Answer"], rows, L, T + 0.5, W, col_w=[2, 12, 40, 10], size=18, row_h=3.3, left_cols=(1, 2))
    notes(s, "Section 10 A. Read each line; take the answer; note who answered.")

    # the Q&A and Thank-you slides go last
    _move_to_end(prs, 2)
    os.makedirs(HERE, exist_ok=True)
    prs.save(OUT)
    print("wrote", OUT, "|", len(prs.slides), "slides")
    return OUT


def export_pngs(path, folder=None, width=1600):
    """Every slide as a PNG through PowerPoint, and a contact sheet, to look at."""
    import win32com.client
    from PIL import Image
    folder = folder or os.path.join(HERE, "check")
    os.makedirs(folder, exist_ok=True)
    for f in os.listdir(folder):
        os.remove(os.path.join(folder, f))
    app = win32com.client.DispatchEx("PowerPoint.Application")
    paths = []
    try:
        pres = app.Presentations.Open(os.path.abspath(path).replace("/", "\\"), WithWindow=False)
        for i in range(1, pres.Slides.Count + 1):
            out = os.path.join(folder, f"slide_{i:02d}.png").replace("/", "\\")
            pres.Slides(i).Export(out, "PNG", width, int(width * 38.1 / 67.3)); paths.append(out)
        pres.Close()
    finally:
        app.Quit()
    thumbs = [Image.open(p).convert("RGB").resize((640, 362)) for p in paths]
    cols = 3; rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 648 + 8, rows * 370 + 8), "#d9d9d9")
    for k, im in enumerate(thumbs):
        sheet.paste(im, (8 + (k % cols) * 648, 8 + (k // cols) * 370))
    sp = os.path.join(folder, "sheet.png"); sheet.save(sp)
    print("slides ->", folder)
    return sp


if __name__ == "__main__":
    out = build()
    if "--png" in sys.argv:
        export_pngs(out)
