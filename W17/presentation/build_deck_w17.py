"""The concept design deck, October 2026: the engineer's design-basis deck as he last updated it (16 September 2026,
"- 2-1"), with the sewer network options added as section 03 and placeholders, a section cover and an empty page
each, for 04 the treated effluent network and 05 the cost analysis (engineer, 2026-10-02).

    python build_deck_w17.py          writes Options 2026-10/Presentation/Ibri_Concept_Design_Presentation_2026-10.pptx
    python build_deck_w17.py --png    ... and every slide as a PNG in presentation/check/, with contact sheets

His slides are kept as they are; only the cover's title, subtitle, date and revision change. Every new slide is a
copy of one of his own, made by PowerPoint (a section cover, a Network slide, a Decisions slide), so the title bar,
the category tab, the footer strip and the live page number are his; python-pptx then replaces the body. Every number
is read from report/facts_w17.py, the module the Concept Design Report reads, so the deck and the report agree.
The base deck is presentation/base/ (36 MB, not in git); the maps are re-encoded as JPEG in presentation/assets/.
"""
import copy
import json
import os
import re
import sys

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
REPO = os.path.dirname(W17)
sys.path.insert(0, os.path.join(W17, "report"))
import facts_w17 as F  # noqa: E402

BASE = os.path.join(HERE, "base", "Ibri_Design_Basis_Meeting_2026-09-16 - 2-1.pptx")
OUT = os.path.join(W17, "Options 2026-10", "Presentation", "Ibri_Concept_Design_Presentation_2026-10.pptx")
IMG = os.path.join(W17, "report", "img")
ASSETS = os.path.join(HERE, "assets")
TABLER = os.path.join(REPO, "W16", "report_basis", "deck", "assets", "icons")
CHECK = os.path.join(HERE, "check")
PT_PER_CM = 28.3465

# his slides used as templates (1-based in the base deck), and the end slide
SEC, NET, DEC, END = 8, 18, 22, 23

# his palette, read from the deck
TEAL = "315258"          # titles and table headers
INK, GREY, MUTE, LINE, ZEBRA = "262626", "5A5A5A", "8C8C8C", "D9D9D9", "F3F6FA"
NAVY, ASK = "1F497D", "EAF1F8"
# his footer strip as it came, category -> (text box, bar); replaced on every content slide by the sections below
FOOT = {"progress": ("TextBox Progress", "Rectangle Progress"), "overview": ("TextBox 6", "Rectangle 7"),
        "boundaries": ("TextBox 8", "Rectangle 9"), "population": ("TextBox 10", "Rectangle 11"),
        "growth": ("TextBox 12", "Rectangle 13"), "network": ("TextBox 14", "Rectangle 15"),
        "plant": ("TextBox 16", "Rectangle 17"), "decisions": ("TextBox 18", "Rectangle 19")}
STRIP = {n for pair in FOOT.values() for n in pair}
FURNITURE = {"Rounded Rectangle 1", "TextBox 2", "TextBox 3", "Connector 4", "Picture 5", "TextBox 20"} | STRIP
CONTENT_LAYOUT = "6_Custom Layout"
# the deck's five sections (engineer, 2026-10-02: the strip and the cover show them, the slide's own lit): number,
# label, colour, white icon on the cover (a Tabler name, "cost" drawn below; None keeps his own Progress icon)
SECTIONS = [("01", "Progress", "1F7F8C", None), ("02", "Design basis", "01474D", "clipboard-check"),
            ("03", "Sewer network", "3E8E5E", "pipeline"), ("04", "TE network", "2E86AB", "droplets"),
            ("05", "Cost analysis", "8A6D3B", "cost")]
# the Tabler set kept in W16 has no money icon and nothing is downloaded: a banknote drawn on its grid and stroke
COST_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>'
            '<path d="M6.5 9.5v5"/><path d="M17.5 9.5v5"/></svg>')
# the content area, under the title bar and above the footer
L, T, W, B = 1.5, 6.5, 64.3, 36.1
fmt = F.fmt
RANK = {o: ("1st", "2nd", "3rd")[i] for i, o in enumerate(F.RECOMMENDED)}
PLACE = []               # SVG icons PowerPoint places after the build: (slide no, svg, left, top, w, h)


def rgb(h):
    return RGBColor.from_string(h)


def tc(s):
    """His titles are in title case; keep words like 'STPs' and 'O1' as they are."""
    return " ".join(w[:1].upper() + w[1:] if w[:1].islower() else w for w in s.split(" "))


# ------------------------------------------------------------------ PowerPoint: copies of his slides
def com_duplicate(specs):
    """Copy the base to the output, open the copy, put a copy of each spec's template slide before the end slide, and
    save once, in place. Never SaveAs and then Save again: PowerPoint reads the pictures lazily, and on the second save
    it took them by their old part names from the new file, so maps and charts on his slides became logos and icons
    (found and tested 2026-10-02; copy, open, edit, one save is clean)."""
    import shutil
    import win32com.client
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    shutil.copy2(BASE, OUT)
    app = win32com.client.DispatchEx("PowerPoint.Application"); app.DisplayAlerts = 1
    try:
        pres = app.Presentations.Open(OUT, WithWindow=False)
        pos = END
        for sp in specs:
            pres.Slides(sp["template"]).Duplicate().MoveTo(pos)
            pos += 1
        pres.Save(); pres.Close()
    finally:
        app.Quit()


def com_finish(png=False):
    """Place the SVG icons as native graphics; with png, export every slide and contact sheets."""
    import win32com.client
    app = win32com.client.DispatchEx("PowerPoint.Application"); app.DisplayAlerts = 1
    paths = []
    try:
        pres = app.Presentations.Open(OUT, WithWindow=False)
        for n, svg, l, t, w, h in PLACE:
            pres.Slides(n).Shapes.AddPicture(svg, 0, -1, l * PT_PER_CM, t * PT_PER_CM, w * PT_PER_CM, h * PT_PER_CM)
        pres.Save()
        if png:
            os.makedirs(CHECK, exist_ok=True)
            for f in os.listdir(CHECK):
                os.remove(os.path.join(CHECK, f))
            for i in range(1, pres.Slides.Count + 1):
                p = os.path.join(CHECK, f"slide_{i:02d}.png")
                pres.Slides(i).Export(p, "PNG", 1600, int(1600 * 38.1 / 67.31)); paths.append(p)
        pres.Close()
    finally:
        app.Quit()
    if png:
        thumbs = [Image.open(p).convert("RGB").resize((560, 317)) for p in paths]
        for k in range(0, len(thumbs), 12):
            grp = thumbs[k:k + 12]; cols = 3; rows = (len(grp) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * 568 + 8, rows * 325 + 8), "#d9d9d9")
            for j, im in enumerate(grp):
                sheet.paste(im, (8 + (j % cols) * 568, 8 + (j // cols) * 325))
            sheet.save(os.path.join(CHECK, f"sheet_{k // 12 + 1}.png"))
        print("slides ->", CHECK)


# ------------------------------------------------------------------ python-pptx helpers, in his styling
def set_text(shape, s):
    """Replace a text box's text, keeping the first run's formatting (or the field, for the page number)."""
    tf = shape.text_frame
    p0 = tf.paragraphs[0]
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    runs = p0.runs
    if runs:
        runs[0].text = s
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    else:
        p0.add_run().text = s


def shape(slide, name):
    return next(sh for sh in slide.shapes if sh.name == name)


def _clone(slide, el, name):
    """A copy of a shape element on the same slide, with its own id and name; returns its proxy."""
    new = copy.deepcopy(el)
    slide.shapes._spTree.append(new)
    nv = new.find(".//" + qn("p:cNvPr"))
    nv.set("id", str(slide.shapes._next_shape_id)); nv.set("name", name)
    return slide.shapes[-1]


def section_strip(prs):
    """The bottom strip of every content slide, his and the new: the deck's five sections, the slide's own lit in its
    colour, drawn from his own strip's first item so the type and the bar are his. A slide belongs to the section of the
    last section cover before it ('01 PROGRESS' ... '05 COST ANALYSIS')."""
    sec, x0, x1, gap = None, 1.52, 60.0, 0.29
    pitch = (x1 - x0) / len(SECTIONS)
    for s in prs.slides:
        covers = [re.match(r"^(0[1-9]) ", sh.text_frame.text.strip()) for sh in s.shapes if sh.has_text_frame]
        if s.slide_layout.name != CONTENT_LAYOUT:
            sec = next((m.group(1) for m in covers if m), sec)
            continue
        tb0, bar0 = shape(s, "TextBox Progress")._element, shape(s, "Rectangle Progress")._element
        for sh in list(s.shapes):
            if sh.name in STRIP:
                sh._element.getparent().remove(sh._element)
        for k, (num, label, col, _) in enumerate(SECTIONS):
            on = num == sec
            tb = _clone(s, tb0, f"Section {num}")
            tb.left, tb.width = Cm(x0 + k * pitch), Cm(pitch - gap)
            set_text(tb, f"{num} {label}")
            r = tb.text_frame.paragraphs[0].runs[0]
            r.font.size = Pt(14); r.font.bold = on; r.font.color.rgb = rgb(col if on else MUTE)
            bar = _clone(s, bar0, f"Section {num} bar")
            bar.left, bar.width = Cm(x0 + k * pitch + 0.24), Cm(pitch - gap - 0.21)
            bar.fill.solid(); bar.fill.fore_color.rgb = rgb(col if on else LINE)


def cover_row(s):
    """The cover's row of circles: the five sections with their icons and names. His Progress circle, icon and name
    stay where they are; the topic circles of the 16 September meeting go."""
    for sh in list(s.shapes):
        if sh.top > Cm(31) and sh.name != "Oval Progress" and (
                sh.name.startswith("Oval ") or sh.name.startswith("icon ") or
                (sh.has_text_frame and sh.top > Cm(34) and sh.name != "TextBox Progress")):
            sh._element.getparent().remove(sh._element)
    oval0, label0 = shape(s, "Oval Progress"), shape(s, "TextBox Progress")
    c0 = oval0.left / 360000 + oval0.width / 720000          # his circle's centre, cm
    pitch = (62.90 - oval0.left / 360000) / (len(SECTIONS) - 1)  # to where the last topic circle stood
    for k, (num, label, col, ic) in enumerate(SECTIONS[1:], 1):
        c = c0 + k * pitch
        o = _clone(s, oval0._element, f"Oval {label}")
        o.left = Cm(c - oval0.width / 720000); o.fill.solid(); o.fill.fore_color.rgb = rgb(col)
        t = _clone(s, label0._element, f"TextBox {label}")
        t.left = Cm(c - label0.width / 720000)
        set_text(t, label)
        r = t.text_frame.paragraphs[0].runs[0]; r.font.color.rgb = rgb(col); r.font.bold = True; r.font.size = Pt(16)
        PLACE.append((1, svg(ic), c - 0.8, 32.10, 1.6, 1.6))


def furnish(slide, title, tab=None):
    """Keep his title bar and footer, drop the body; set the title and, for a new section, the tab."""
    for sh in list(slide.shapes):
        if sh.name not in FURNITURE and not sh.name.startswith("icon "):
            sh._element.getparent().remove(sh._element)
    set_text(shape(slide, "TextBox 3"), title)
    if tab:                                   # a category of its own: label, colour, and its icon placed later
        label, col, svg_path = tab
        set_text(shape(slide, "TextBox 2"), label.upper())
        r = shape(slide, "Rounded Rectangle 1"); r.fill.solid(); r.fill.fore_color.rgb = rgb(col)
        for sh in list(slide.shapes):
            if sh.name.startswith("icon "):
                sh._element.getparent().remove(sh._element)
        if svg_path:
            PLACE.append((slide_no(slide), svg_path, 1.35, 2.0, 1.2, 1.2))


def slide_no(slide):
    return list(slide.part.package.presentation_part.presentation.slides).index(slide) + 1


def text(slide, left, top, width, height, lines, size=24, colour=GREY, align=PP_ALIGN.LEFT, spacing=10,
         anchor=MSO_ANCHOR.TOP, bullets=True):
    """Paragraphs with his bullet (Wingdings v), or plain; a line is str or (str, {bold, colour, size, bullet})."""
    tb = slide.shapes.add_textbox(Cm(left), Cm(top), Cm(width), Cm(height))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        s, opt = (ln, {}) if isinstance(ln, str) else ln
        p.alignment = align; p.space_after = Pt(spacing)
        if opt.get("bullet", bullets):
            pPr = p._p.get_or_add_pPr(); pPr.set("marL", "457200"); pPr.set("indent", "-457200")
            bf = OxmlElement("a:buFont"); bf.set("typeface", "Wingdings"); bf.set("pitchFamily", "2"); bf.set("charset", "2")
            bc = OxmlElement("a:buChar"); bc.set("char", "v")
            pPr.append(bf); pPr.append(bc)
        for k, seg in enumerate(s.split("**")):
            if not seg:
                continue
            r = p.add_run(); r.text = seg; r.font.name = "Calibri"; r.font.size = Pt(opt.get("size", size))
            r.font.bold = opt.get("bold", False) or k % 2 == 1
            r.font.color.rgb = rgb(opt.get("colour", colour))
    return tb


def pic(slide, path, left, top, width, height, align="center"):
    """A picture fitted inside the box; the maps go in as JPEG to keep the deck light."""
    if path.endswith(".png") and os.path.getsize(path) > 1.5e6:
        os.makedirs(ASSETS, exist_ok=True)
        jpg = os.path.join(ASSETS, os.path.basename(path)[:-4] + ".jpg")
        if not os.path.exists(jpg) or os.path.getmtime(jpg) < os.path.getmtime(path):
            Image.open(path).convert("RGB").save(jpg, quality=88, optimize=True)
        path = jpg
    iw, ih = Image.open(path).size
    k = min(width / iw, height / ih); w, h = iw * k, ih * k
    x = left + (width - w) / 2 if align == "center" else left
    return slide.shapes.add_picture(path, Cm(x), Cm(top + (height - h) / 2), Cm(w), Cm(h))


def _borders(cell, top=None, bottom=None, w=0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for e in tcPr.findall(qn(tag)):
            tcPr.remove(e)
    for i, (tag, col) in enumerate((("a:lnL", None), ("a:lnR", None), ("a:lnT", top), ("a:lnB", bottom))):
        ln = OxmlElement(tag); ln.set("w", str(int(w * 12700))); ln.set("cap", "flat"); ln.set("cmpd", "sng"); ln.set("algn", "ctr")
        if col is None:
            ln.append(OxmlElement("a:noFill"))
        else:
            sf = OxmlElement("a:solidFill"); c = OxmlElement("a:srgbClr"); c.set("val", col); sf.append(c); ln.append(sf)
        tcPr.insert(i, ln)


def table(slide, headers, rows, left, top, width, col_w=None, size=20, row_h=1.4, left_cols=(0,), bold_rows=(),
          shade_cols=()):
    """His table: teal header, white and pale rows, light rules, no verticals; '**' marks bold text."""
    n, m = len(rows) + 1, len(headers)
    shp = slide.shapes.add_table(n, m, Cm(left), Cm(top), Cm(width), Cm(row_h * n))
    tbl = shp.table; tbl.first_row = True; tbl.horz_banding = False
    if col_w:
        k = width / sum(col_w)
        for j, w in enumerate(col_w):
            tbl.columns[j].width = Cm(w * k)
    for i in range(n):
        tbl.rows[i].height = Cm(row_h)
    for j, htxt in enumerate(headers):
        c = tbl.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = rgb(TEAL)
        c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j in left_cols else PP_ALIGN.CENTER
        r = c.text_frame.paragraphs[0].add_run(); r.text = str(htxt); r.font.size = Pt(size); r.font.bold = True
        r.font.color.rgb = rgb("FFFFFF"); r.font.name = "Calibri"
        c.vertical_anchor = MSO_ANCHOR.MIDDLE; c.margin_left = c.margin_right = Cm(0.3)
        c.margin_top = c.margin_bottom = Cm(0.1)
        _borders(c, None, "FFFFFF", 1.5)
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.fill.solid()
            c.fill.fore_color.rgb = rgb("DCE6F1") if j in shade_cols else rgb("FFFFFF" if i % 2 else ZEBRA)
            c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j in left_cols else PP_ALIGN.CENTER
            for k, seg in enumerate(("" if val is None else str(val)).split("**")):
                if seg:
                    r = c.text_frame.paragraphs[0].add_run(); r.text = seg; r.font.size = Pt(size); r.font.name = "Calibri"
                    r.font.bold = (k % 2 == 1) or (i - 1 in bold_rows); r.font.color.rgb = rgb(INK)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE; c.margin_left = c.margin_right = Cm(0.3)
            c.margin_top = c.margin_bottom = Cm(0.1)
            _borders(c, LINE, TEAL if i == n - 1 else LINE, 1.5 if i == n - 1 else 0.75)
    return shp


def box(slide, left, top, width, height, lead, body, fill=ASK, line="4F81BD", size=24):
    """His decision box: pale blue, a bold lead, the text."""
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(left), Cm(top), Cm(width), Cm(height))
    shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill); shp.line.color.rgb = rgb(line); shp.line.width = Pt(1.5)
    shp.shadow.inherit = False
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Cm(0.6)
    p = tf.paragraphs[0]
    for s, bold, col in ((lead, True, NAVY), (body, False, INK)):
        r = p.add_run(); r.text = s; r.font.bold = bold; r.font.size = Pt(size); r.font.color.rgb = rgb(col); r.font.name = "Calibri"
    return shp


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


# ------------------------------------------------------------------ the new slides
def s_model(s):
    sm = F.summary("S1"); Ld = F.loads()
    pic(s, os.path.join(IMG, "W17_overview_subnetworks.png"), L, T, 39.5, B - T)
    text(s, 42.3, T + 0.6, 23.5, 28, [
        "Twenty-four subnetworks, each draining by gravity to its lowest point, its outfall, and named after it: O1 to O24.",
        f"{fmt(sm['pipe_km'])} km of sewer and {fmt(sm['manholes'])} manholes, designed in SewerGEMS for the flow of 2070.",
        "The flow of every plot at its nearest manhole, for 2030, 2040, 2050, 2055, 2060 and 2070.",
        "Peak flow in each pipe from the flow upstream: Peltier up to 100 properties, Merrimack above.",
        f"Infiltration 720 l/d per km: {fmt(Ld['infiltration_m3d'])} m³/d over the network.",
        "Colebrook-White friction, 1.5 mm roughness, every size.",
        ("Every option, every year: no pipe over 3.0 m/s, none deeper than 65 % of its diameter up to 350 mm, or 50 % "
         "above.", {"bold": True, "colour": TEAL}),
    ], size=22, spacing=12)
    notes(s, "Report Section 6.2.5. The subnetworks are the same in every option; the options change where their flow goes.")


def s_flows(s):
    ys = ("2030", "2055", "2070"); c = {y: F.flow_chain(y) for y in ys}; Ld = F.loads()
    table(s, ["Average flow, m³/d"] + list(ys), [
        ["From the plots"] + [fmt(c[y]["plots"]) for y in ys],
        ["Not carried: planted areas awaiting the survey, three outlying catchments served on site"]
        + [fmt(c[y]["outside"]) for y in ys],
        ["Carried by the network"] + [fmt(c[y]["carried"]) for y in ys],
        [f"Infiltration, {fmt(Ld['active_sewer_km'])} km at 720 l/d per km"] + [fmt(c[y]["infiltration"]) for y in ys],
        ["**Arriving at the plants, every option**"] + [f"**{fmt(c[y]['at_plants'])}**" for y in ys],
        ["**Plant design average, with the 10 % margin**"] + [f"**{fmt(c[y]['design'])}**" for y in ys],
    ], L, T + 0.5, 40, col_w=[22, 6, 6, 6], size=22, row_h=3.2)
    pk = F.plants("S1")["O1"]["peak"]["2070"]
    text(s, 43.5, T + 0.6, 22.3, 28, [
        "The same in every option: the pipes and their infiltration do not change; only the split between the plants does.",
        "The ten per cent margin of the guideline is applied when each plant is sized.",
        f"The peak at a plant is the sum of the peaks of the outfalls that reach it: {fmt(pk)} l/s in 2070 when all the "
        "flow goes to one plant. The plant's peak hourly flow, one peak factor on its whole flow, is lower.",
        ("The flow of every year at every plant of every option: report Section 6.2.7.", {"bold": True, "colour": TEAL}),
    ], size=22, spacing=12)
    notes(s, "Report Table 1 and Section 6.2.7. This is the reconciliation: 60,099 from the plots, 60,456 at the plants, "
             "66,502 with the margin.")


def _served(o):
    out = {}
    for sub, z in F.plant_of(o).items():
        out.setdefault(z, []).append(sub)
    parts = []
    for z in F.summary(o)["stp"]:
        subs = sorted(out[z], key=lambda x: int(x[1:]))
        what = "its own subnetwork only" if len(subs) == 1 else ", ".join(subs) if len(subs) <= 6 else f"{len(subs)} subnetworks"
        parts.append(f"{z}: {what}")
    return "; ".join(parts)


def s_options(s):
    opts = F.available()
    table(s, ["Option", "Plants", "The plants and the subnetworks each serves"],
          [[o, str(len(F.plants(o))), _served(o)] for o in opts], L, T + 0.3, W, col_w=[5, 4, 55], size=19, row_h=1.75,
          left_cols=(0, 2))
    pic(s, os.path.join(IMG, "W01_plant_split.png"), L, 22.4, 30, B - 22.4)
    text(s, 34, 23.0, 31.8, 13, [
        "The pipes run in the same streets in every option.",
        "What changes: where each subnetwork's flow is sent, the trunk sizes, the pumping stations and their rising mains, "
        "and the number and size of the plants.",
        "S1 treats all the flow at O1, 760 m from the existing STP; S2 at O16; S3 to S7 at two to six plants.",
    ], size=21, spacing=10)
    notes(s, "Report Table 41 and Figure 77. The chart: the average flow arriving at each plant in 2070.")


def _strip(s, o, top):
    """The key figures of option o in one row under its diagram."""
    r = F.option_row(o); pl = F.plants(o)
    rank = f"Recommended, {RANK[o]}" if o in RANK else "Not shortlisted"
    table(s, ["Priority", "Plants, average 2070, m³/d", "Sewer at the plants, m deep", "Pumping stations",
              "Pumping energy 2070, MWh a year", "Rising mains, km", "Largest sewer, mm"],
          [[rank, "; ".join(f"{z} {fmt(v['avg']['2070'])}" for z, v in pl.items()), r["inlet_depths"], str(r["n_ps"]),
            f"{fmt(F.energy_total(o, '2070'))} (stations {fmt(r['mwh_2070'])})", fmt(r["rm_km"], 1),
            fmt(F.largest_od(o))]],
          L, top, W, col_w=[7, 16, 9, 6, 11, 6, 6], size=17, row_h=1.75, left_cols=())


def s_diagram(o):
    def f(s):
        pic(s, os.path.join(IMG, f"W17_{o}_transfer_diagram.png"), L, T, W, 32.2 - T)
        _strip(s, o, 32.5)
        notes(s, f"Report Section 6.2.6, option {o}: where the flow of every subnetwork goes, with the peak flow of each "
                 "transfer in 2070 and the depth of the sewer at each plant.")
    return f


def s_map(o):
    def f(s):
        r = F.option_row(o); pl = F.plants(o); ps = F.summary(o); il = F.inlet_lift(o)
        pic(s, os.path.join(IMG, f"W17_{o}_network.png"), L, T, 41.5, B - T, align="left")
        types = F.summary(o)["ps_by_type"]
        rows = [
            ["Plants, average 2070", "; ".join(f"{z} {fmt(v['avg']['2070'])}" for z, v in pl.items()) + " m³/d"],
            ["Sewer at the plants", f"{r['inlet_depths']} m deep"],
            ["Pumping stations", f"{r['n_ps']}: type 1 {types['1']}, type 2 {types['2']}, type 3 {types['3']}"],
            ["Pumps in duty", f"{fmt(r['kw'])} kW"],
            ["Energy 2070, stations", f"{fmt(r['mwh_2070'])} MWh a year"],
            ["Energy 2070, plant inlets", f"{fmt(il['mwh']['2070'])} MWh a year"],
            ["Rising mains", f"{fmt(r['rm_km'], 1)} km; longest {fmt(r['longest_rm']['L'] / 1000, 1)} km from {r['longest_rm']['ps']}"],
            ["Sewers of 1,000 mm and over", f"{fmt(F.km_od_at_least(o))} km, up to {fmt(F.largest_od(o))} mm"],
            ["Mains holding the 2030 flow over 30 minutes", str(len(F.retention_flags(o)))],
        ]
        table(s, ["", f"Option {o}"], rows, 44.0, T + 0.2, 21.8, col_w=[9, 12.8], size=17, row_h=2.35, left_cols=(0, 1))
        text(s, 44.0, 30.3, 21.8, 5.5, [("Station label: the outfall, its depth and the average flow in 2070; then the "
                                         "pump head and the duty.", {"size": 16, "colour": MUTE, "bullet": False})],
             spacing=4)
        notes(s, f"Report Section 6.2.6 and Appendix B, option {o}.")
    return f


def s_depth(s):
    rows = [F.option_row(o) for o in F.available()]
    n12 = sorted({r["mh_over_12"] for r in rows}); dms = [r["deepest"] for r in rows]; kms = [r["km_over_12"] for r in rows]
    pic(s, os.path.join(IMG, "W17_S1_depth.png"), L, T, 41.5, B - T, align="left")
    sm = F.summary("S1")["manholes_by_band"]
    text(s, 44.0, T + 0.4, 21.8, 12.5, [
        f"In every option {'/'.join(map(str, n12))} manholes are deeper than 12 m, {fmt(min(kms), 1)} km of sewer lies "
        f"deeper than 12 m, and the deepest manhole is {fmt(min(dms), 1)} to {fmt(max(dms), 1)} m.",
        "The deep runs are set by the ground within the subnetworks, which the options do not change.",
        ("Where the flow is treated changes the trunk sizes and the pumping, not the depth.", {"bold": True, "colour": TEAL}),
    ], size=21, spacing=10)
    table(s, ["Manholes by depth, S1", "Number"],
          [[b.replace("-", " to ").replace(">", "over "), fmt(v)] for b, v in sm.items()],
          44.0, 21.3, 21.8, col_w=[13, 8.8], size=17, row_h=1.75)
    notes(s, "Report Section 6.2.7 and Appendix B; the map is option S1. Depth from the cover to the invert.")


def s_glance(s):
    opts = F.available()
    pic(s, os.path.join(IMG, "W06_glance.png"), L, T, 39.5, B - T, align="left")
    rows = [[o + (f" ({RANK[o]})" if o in RANK else ""), str(len(F.plants(o))), str(F.summary(o)["pumping_stations"]),
             fmt(F.km_od_at_least(o)), fmt(F.energy_total(o, "2070"))] for o in opts]
    table(s, ["Option", "Plants", "Stations", "Sewers ≥ 1,000 mm, km", "Energy 2070, MWh"], rows, 42.3, T + 0.3, 23.5,
          col_w=[6, 3.6, 4.2, 5.6, 5.4], size=17, row_h=2.1, bold_rows=tuple(i for i, o in enumerate(opts) if o in RANK))
    text(s, 42.3, 24.2, 23.5, 11.5, [
        "Energy: the pumping stations and the lift at the plant inlets together.",
        "One pipe network in every option, so the same length and depth; the trunk sewers, the pumping and the plants "
        "differ.",
    ], size=19, spacing=8)
    notes(s, "Report executive summary, Figure 2 and Table 3.")


def s_energy(s):
    opts = F.available(); ref = opts[0]
    rows = []
    for o in opts:
        il = F.inlet_lift(o)["mwh"]; tot = F.energy_total(o, "2070")
        d = "" if o == ref else f"{100 * (tot / F.energy_total(ref, '2070') - 1):+.0f} %".replace("-", "−")
        rows.append([o, fmt(F.summary(o)["mwh_2030"]), fmt(il["2030"]), fmt(F.summary(o)["mwh_2070"]), fmt(il["2070"]),
                     f"**{fmt(tot)}**", d])
    table(s, ["Option", "Stations 2030", "Plant inlets 2030", "Stations 2070", "Plant inlets 2070", "Together 2070",
              f"Against {ref}"], rows, L, T + 0.3, 36.5, col_w=[4, 5, 5, 5, 5, 5, 5], size=17, row_h=1.85)
    pic(s, os.path.join(IMG, "W05_energy_total.png"), 39.5, T, 26.3, 14.0)
    il1 = F.inlet_lift(ref)
    big = max(F.plants(ref), key=lambda z: F.plants(ref)[z]["avg"]["2070"])
    text(s, 39.5, 21.2, 26.3, 14.6, [
        "Each plant's inlet works lift the arriving flow again: wet well 1.5 m below the arriving sewer, inlet works 3 m "
        "above the ground, 65 % wire-to-water, as for the stations.",
        f"In {ref} the whole flow arrives {F.plants(ref)[big]['inlet']:.1f} m deep: the lift uses {fmt(il1['mwh']['2070'])} "
        f"MWh a year in 2070, against {fmt(F.summary(ref)['mwh_2070'])} for its {F.summary(ref)['pumping_stations']} stations.",
        ("The lift narrows the differences between the options; it does not change their order.", {"bold": True, "colour": TEAL}),
    ], size=19, spacing=8)
    text(s, L, 22.0, 36.5, 13.5, [
        "MWh a year. Stations: the network's pumping stations, each pumping the 2070 peak of everything that reaches it, "
        "mains along roads and streets, Hazen-Williams C 120, fittings +10 %.",
    ], size=16, colour=MUTE, spacing=4, bullets=False)
    notes(s, "Report Section 6.2.7, Table 44 and Figure 81.")


def s_matters(s):
    ps1 = [r for r in F.pumps("S1") if r["ret2030"] > 30]
    ps1 = sorted(ps1, key=lambda r: -r["ret2030"])
    table(s, ["Main, option S1", "To", "Length, km", "Retention 2030, h"],
          [[r["ps"], f"STP at {r['to']}" if r["kind"] == "plant" else r["to"], fmt(r["L"] / 1000, 1), fmt(r["ret2030"] / 60, 1)]
           for r in ps1], L, T + 0.3, 31, col_w=[7, 9, 6, 8], size=17, row_h=1.6)
    counts = [len(F.retention_flags(o)) for o in F.available()]
    text(s, L, T + 0.6 + 1.6 * (len(ps1) + 1), 31, 8, [
        f"Between {min(counts)} and {max(counts)} mains, depending on the option, hold the 2030 flow longer than the 30 "
        "minutes the guideline aims for. Sulphide forms: hydrogen sulphide evaluation, dosing or a shorter route.",
    ], size=19, spacing=6)
    heads = {o: next((r for r in F.pumps(o) if r["ps"] == "O23"), None) for o in F.available()}
    hs = [r["H"] for r in heads.values() if r]
    o23 = heads["S1"]
    text(s, 35, T + 0.6, 30.8, 28, [
        ("O23: a few litres a second against a very high head", {"bold": True, "colour": TEAL, "bullet": False, "size": 23}),
        f"Duty {fmt(o23['duty'], 1)} l/s through a {o23['dn']} mm main of {fmt(o23['L'] / 1000, 1)} km to {o23['to']}, against "
        f"{fmt(o23['H'])} m of head (S1 to S5).",
        f"In S6 and S7 it pumps to the plant at O22 instead: {fmt(heads['S6']['L'] / 1000, 1)} km, {fmt(heads['S6']['H'])} m.",
        f"Head {fmt(round(min(hs), -1))} to {fmt(round(max(hs), -1))} m in every option.",
        ("To be reconsidered at the preliminary design: a shorter route to a nearer subnetwork, or local treatment.",
         {"bold": True, "colour": TEAL}),
    ], size=21, spacing=12)
    notes(s, "Report Section 6.2.7; Appendix B lists every station of every option.")


def s_selfclean(s):
    sy = json.load(open(os.path.join(F.RES, "S1", "selfcleansing_year.json"), encoding="utf-8"))
    si = json.load(open(os.path.join(F.RES, "S1", "selfcleansing_info.json"), encoding="utf-8"))
    table(s, ["Year", "Pipes", "Share", "Length, km", "Head pipes"],
          [[y, fmt(v["pipes"]), f"{100 * v['share']:.0f} %", fmt(v["km"]), f"{fmt(v['head_pipes'])} of {fmt(sy['head_pipes'])}"]
           for y, v in sy["years"].items()], L, T + 0.3, 30, col_w=[4, 5, 4, 5, 7], size=18, row_h=1.75)
    text(s, L, T + 0.3 + 1.75 * 7 + 0.4, 30, 4, [("Pipes reaching 0.75 m/s at their peak flow at a gradient of 4 % or less, "
                                                    "every property connected.", {"size": 16, "colour": MUTE, "bullet": False})])
    nv = sy["never"]; h30, h70 = si["groups"]["2030 head pipes"], si["groups"]["2070 head pipes"]
    text(s, 33.5, T + 0.4, 32.3, 21, [
        "In no year does every pipe reach 0.75 m/s, even laid at 4 %.",
        f"{fmt(nv['pipes'])} pipes, {fmt(nv['km'])} km of 200 mm sewer at the heads, never carry enough: a 200 mm sewer "
        f"needs {sy['dn200_q_need_ls']:.2f} l/s, the flow of about {sy['houses']} houses, to reach 0.75 m/s at 4 %.",
        f"There the guideline sets the gradient by tractive force: at 1 pascal the head pipes need a median "
        f"{h30['median_tractive_pc']:.1f} % in 2030 and {h70['median_tractive_pc']:.1f} % in 2070.",
        ("Whether a pipe cleans itself depends on how many houses drain into it, not on the year.",
         {"bold": True, "colour": TEAL}),
    ], size=20, spacing=10)
    box(s, L, 29.6, W, 6.0, "Decision required.  ",
        "The year from which the network is to be self-cleansing; the tractive stress for the head pipes; and whether 4 % "
        "is the steepest gradient for every pipe or for the head pipes only. It extends Decision 7.", size=22)
    notes(s, "Report Section 6.2.8. A steeper network is deeper and needs more pumping; its cost follows the decision.")


def s_recommend(s):
    ref = F.RECOMMENDED[0]; e_ref = F.energy_total(ref, "2070")
    gains = {
        "S1": ["One site, 760 m from the existing STP",
               f"Built in phases: {fmt(F.plants('S1')['O1']['avg']['2030'])} to {fmt(F.plants('S1')['O1']['avg']['2070'])} m³/d",
               "One plant to staff, one sludge line, one source of treated effluent"],
        "S4": [f"{_p(F.energy_total('S4', '2070'), e_ref)} % less pumping energy than S1",
               f"{('One', 'Two', 'Three', 'Four')[F.summary(ref)['pumping_stations'] - F.summary('S4')['pumping_stations'] - 1]} "
               "fewer pumping stations",
               f"{fmt(F.km_od_at_least(ref) - F.km_od_at_least('S4'))} km less sewer of 1,000 mm and over"],
        "S6": [f"Least pumping: {_p(F.energy_total('S6', '2070'), e_ref)} % below S1",
               f"Fewest stations, {F.summary('S6')['pumping_stations']}; shortest rising mains, {fmt(F.summary('S6')['rising_main_m'] / 1000, 1)} km",
               "O22, 446 m³/d in 2070, small enough for nature-based treatment"],
    }
    costs = {
        "S1": [f"Largest trunks: {fmt(F.km_od_at_least('S1'))} km of 1,000 mm and over, up to {fmt(F.largest_od('S1'))} mm",
               f"Deepest arrival, {F.plants('S1')['O1']['inlet']:.1f} m"],
        "S4": ["Two further plant sites, O4 and O9, each with its buffer, access, power and outlet"],
        "S6": ["Six sites and six plants to staff",
               f"O22 receives {fmt(F.plants('S6')['O22']['avg']['2030'])} and O16 {fmt(F.plants('S6')['O16']['avg']['2030'])} m³/d in 2030"],
    }
    cw, gap = 20.6, 1.25
    for i, o in enumerate(F.RECOMMENDED):
        x = L + i * (cw + gap)
        head = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(T + 0.2), Cm(cw), Cm(3.4))
        head.fill.solid(); head.fill.fore_color.rgb = rgb(TEAL); head.line.fill.background(); head.shadow.inherit = False
        tf = head.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for k, (sx, sz, b) in enumerate(((f"{RANK[o]}  ·  {o}", 30, True), (F.CHARACTER[o].capitalize(), 19, False))):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = sx; r.font.size = Pt(sz); r.font.bold = b; r.font.color.rgb = rgb("FFFFFF"); r.font.name = "Calibri"
        pl = F.plants(o); rr = F.option_row(o)
        table(s, ["Plants", ", ".join(pl)], [
            ["Largest plant 2070", f"{fmt(rr['largest_plant_2070'])} m³/d"],
            ["Pumping stations", str(rr["n_ps"])],
            ["Energy 2070", f"{fmt(F.energy_total(o, '2070'))} MWh"],
            ["Largest sewer", f"{fmt(F.largest_od(o))} mm"],
        ], x, T + 3.8, cw, col_w=[9, 11.6], size=17, row_h=1.45, left_cols=(0,))
        text(s, x, T + 12.9, cw, 12.5,
             [("Gains", {"bold": True, "colour": "3E8E5E", "bullet": False})] + gains[o]
             + [("Costs", {"bold": True, "colour": "B4453F", "bullet": False})] + costs[o], size=17, spacing=4)
    box(s, L, 31.0, W, 4.9, "The order rests on the technical results.  ",
        f"S2 is not recommended: {_p(F.energy_total('S2', '2070'), e_ref)} % more pumping energy than S1. The cost estimate "
        "and the multi-criteria appraisal confirm or change the order: S4 or S6 is preferred to S1 if its whole-life cost "
        "is within 10 % of S1's. The treated effluent network is designed on the three.", size=19)
    notes(s, "Report Section 7.11 and the executive summary. Priority set by the engineer, 2 October 2026.")


def _p(a, b):
    return f"{abs(100 * (a / b - 1)):.0f}"


def s_empty(s):
    """The placeholder page: the title bar and the footer only."""
    notes(s, "To be added.")


# ------------------------------------------------------------------ the deck
def specs():
    opts = F.available()
    sp = [dict(template=SEC, kind="section", num="03", title="SEWER NETWORK",
               sub="Twenty-four subnetworks, seven options, three recommended"),
          dict(template=NET, title="The Sewer Network: Twenty-Four Subnetworks, One Model", body=s_model),
          dict(template=NET, title="From The Plots To The Plants: The Flow Every Option Receives", body=s_flows),
          dict(template=NET, title="Seven Options For Where The Flow Is Treated", body=s_options)]
    for o in opts:
        sp.append(dict(template=NET, title=f"Option {o} · {tc(F.text(o))}", body=s_diagram(o)))
        sp.append(dict(template=NET, title=f"Option {o} · The Network And Its Pumping", body=s_map(o)))
    sp += [dict(template=NET, title="Depth: The Same In Every Option", body=s_depth),
           dict(template=NET, title="The Seven Options Side By Side", body=s_glance),
           dict(template=NET, title="Pumping Energy: The Stations And The Plant Inlets", body=s_energy),
           dict(template=NET, title="Two Matters Whichever Option Is Chosen", body=s_matters),
           dict(template=DEC, title="When The Network Becomes Self-Cleansing", body=s_selfclean),
           dict(template=DEC, title="Recommendation: S1, S4 And S6, In This Order", body=s_recommend),
           dict(template=SEC, kind="section", num="04", title="TE NETWORK",
                sub="To be added: designed on the three recommended options"),
           dict(template=NET, title="Treated Effluent Network", body=s_empty, tab=("TE network", "2E86AB", "droplets")),
           dict(template=SEC, kind="section", num="05", title="COST ANALYSIS",
                sub="To be added: capital, operating and life-cycle cost of the options"),
           dict(template=NET, title="Cost Analysis", body=s_empty, tab=("Cost", "8A6D3B", "cost"))]
    return sp


def svg(name, colour="FFFFFF"):
    """A white (or given colour) copy of a Tabler icon, or of the cost icon drawn above, for PowerPoint to place."""
    os.makedirs(ASSETS, exist_ok=True)
    p = os.path.join(ASSETS, f"{name}-{colour}.svg")
    s = COST_SVG if name == "cost" else open(os.path.join(TABLER, f"{name}.svg"), encoding="utf-8").read()
    open(p, "w", encoding="utf-8").write(s.replace('stroke="currentColor"', f'stroke="#{colour}"'))
    return p


def cover(s):
    """His cover with the deck's own title, subtitle, date and revision."""
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        new = {"Design Basis Report": "Concept Design",
               "Settlement boundaries, population, flows and loads": "Design basis and the sewer network options",
               "MEETING": "DATE", "16th September 2026": "October 2026", "Revision 0": "Revision 4"}.get(t)
        if new:
            set_text(sh, new)


def build():
    sp = specs()
    com_duplicate(sp)
    prs = Presentation(OUT)
    cover(prs.slides[0])
    cover_row(prs.slides[0])
    for k, spec in enumerate(sp):
        s = prs.slides[END - 1 + k]
        if spec.get("kind") == "section":
            for sh in s.shapes:
                if sh.has_text_frame:
                    t = sh.text_frame.text.strip()
                    if t.startswith("02 "):
                        set_text(sh, f"{spec['num']} {spec['title']}")
                    elif t.startswith("Settlement boundaries"):
                        set_text(sh, spec["sub"])
            continue
        tab = spec.get("tab")
        if tab:
            tab = (tab[0], tab[1], svg(tab[2]) if tab[2] else None)
        furnish(s, spec["title"], tab)
        spec["body"](s)
    section_strip(prs)
    prs.save(OUT)
    print("wrote", OUT, "|", len(prs.slides), "slides")


if __name__ == "__main__":
    build()
    com_finish(png="--png" in sys.argv)
    print(round(os.path.getsize(OUT) / 1e6, 1), "MB")
