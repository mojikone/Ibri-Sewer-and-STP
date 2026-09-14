"""Build the Word template from the firm's sample report.

The sample (Data/sample report/2621_MPR_AUG_00.docx, outside the repository)
carries the cover the engineer wants — the client's logo, the project title in
a text box over the red and gold swoosh, the firm's logo and address — and the
header and footer with the two logos and the page number. This script keeps
exactly those parts, drops the sample's body, styles the headings without the
sample's automatic numbering (the build writes its own section numbers) and
writes placeholders where the build fills the report name:

    {TITLE_1}   the project title on the cover (kept from the sample)
    {TITLE_2}   the report name on the cover
    {TITLE_3}   the subtitle, revision and date on the cover
    {FOOTER}    the report name in the footer

    python make_template.py            writes Renardet_A4.docx beside this file
"""
import copy
import os
import sys

from docx import Document
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "..", "..", "..", "..", "..", "Data", "sample report", "2621_MPR_AUG_00.docx")
OUT = os.path.join(HERE, "Renardet_A4.docx")

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

NAVY = "1F497D"          # the sample's heading colour, theme text2
ACCENT = "4F81BD"        # theme accent1
FONT_HEAD = "Century Gothic"
FONT_BODY = "Calibri"


def _set_text(t_el, text):
    """Replace one w:t; a newline in the text becomes a line break in the run."""
    run = t_el.getparent()
    parts = text.split("\n")
    t_el.text = parts[0]
    t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    tail = t_el
    for part in parts[1:]:
        br = OxmlElement("w:br")
        tail.addnext(br)
        t2 = OxmlElement("w:t")
        t2.text = part
        t2.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        br.addnext(t2)
        tail = t2


def _pct_width(tbl):
    """A header or footer table set to the full text width follows the page
    into a landscape section instead of sitting at the portrait width."""
    tblpr = tbl.find(qn("w:tblPr"))
    if tblpr is None:
        return
    w = tblpr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW"); tblpr.append(w)
    w.set(qn("w:type"), "pct"); w.set(qn("w:w"), "5000")


def build(sample=SAMPLE, out=OUT):
    d = Document(sample)
    body = d.element.body
    kids = list(body)

    # keep the cover paragraph, the address table and the page break; drop the rest
    keep = 3
    for el in kids[keep:]:
        if el.tag == qn("w:sectPr"):
            continue
        body.remove(el)

    # placeholders on the cover (the text box holds the title twice: the
    # drawing and its fallback, both replaced)
    cover = kids[0]
    for t in cover.iter(qn("w:t")):
        txt = (t.text or "").strip()
        if txt.startswith("Consultancy Services"):
            _set_text(t, "{TITLE_1}")
        elif txt == "Weekly Progress Report":
            _set_text(t, "{TITLE_2}")
        elif txt == "August 2026":
            _set_text(t, "{TITLE_3}")

    # the footer: the report name line becomes a placeholder; the contract
    # line and the page number stay
    sec = d.sections[0]
    for t in sec.footer._element.iter(qn("w:t")):
        if (t.text or "").startswith("Monthly Progress Report"):
            _set_text(t, "{FOOTER}")
    for hf in (sec.header, sec.footer):
        for tbl in hf._element.iter(qn("w:tbl")):
            _pct_width(tbl)

    # the footer (engineer, 2026-09-14): text lines left, the page number centred in its box,
    # the box and the rule above the footer grey instead of black and blue
    GREY_FILL, GREY_LINE = "7F7F7F", "BFBFBF"
    ftbl = next(sec.footer._element.iter(qn("w:tbl")))
    tblpr = ftbl.find(qn("w:tblPr"))
    for b in tblpr.iter(qn("w:top")):
        b.set(qn("w:color"), GREY_LINE); b.set(qn("w:sz"), "12")
        for k in ("w:themeColor", "w:themeTint"):
            if b.get(qn(k)) is not None:
                del b.attrib[qn(k)]
    cells = list(ftbl.iter(qn("w:tc")))
    for i, tc in enumerate(cells):
        tcpr = tc.find(qn("w:tcPr"))
        for b in tcpr.iter(qn("w:top")):
            b.set(qn("w:color"), GREY_LINE)
        for p in tc.iter(qn("w:p")):
            ppr = p.get_or_add_pPr()
            for jc in ppr.findall(qn("w:jc")):
                ppr.remove(jc)
            jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "left" if i == 0 else "center"); ppr.append(jc)
        if i == len(cells) - 1:
            shd = tcpr.find(qn("w:shd"))
            if shd is not None:
                shd.set(qn("w:fill"), GREY_FILL)
                for k in ("w:themeFill", "w:themeFillTint", "w:themeFillShade"):
                    if shd.get(qn(k)) is not None:
                        del shd.attrib[qn(k)]
            for old_v in tcpr.findall(qn("w:vAlign")):
                tcpr.remove(old_v)
            va = OxmlElement("w:vAlign"); va.set(qn("w:val"), "center"); tcpr.append(va)

    # wider text (engineer, 2026-09-14): 1.5 cm at the sides, the top kept for the header
    from docx.shared import Cm
    sec.left_margin = sec.right_margin = Cm(1.5)
    sec.bottom_margin = Cm(2.2)

    # the sample's first page has no header and footer (titlePg): keep that,
    # and give every later section the same header and footer by linking
    sec.different_first_page_header_footer = True

    # headings: the sample's look, without its automatic numbering and without
    # the indent that numbering brings; the build writes "3.2   Title" itself
    for name, size, colour, before, after in (
        ("Heading 1", 14, NAVY, 18, 6),
        ("Heading 2", 12, NAVY, 12, 4),
        ("Heading 3", 11, ACCENT, 10, 3),
    ):
        st = d.styles[name]
        st.font.name = FONT_HEAD
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(colour)
        pf = st.paragraph_format
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        pf.left_indent = pf.first_line_indent = 0
        pf.keep_with_next = True
        ppr = st.element.get_or_add_pPr()
        for num in ppr.findall(qn("w:numPr")):
            ppr.remove(num)
        for ind in ppr.findall(qn("w:ind")):
            ppr.remove(ind)
        rpr = st.element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is not None:
            for k in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
                if fonts.get(qn(k)) is not None:
                    del fonts.attrib[qn(k)]
            fonts.set(qn("w:ascii"), FONT_HEAD); fonts.set(qn("w:hAnsi"), FONT_HEAD)

    n = d.styles["Normal"]
    n.font.name = FONT_BODY
    n.font.size = Pt(10.5)
    n.paragraph_format.space_after = Pt(6)
    n.paragraph_format.line_spacing = 1.12
    # the sample justifies its body text; ragged right reads more easily
    ppr = n.element.get_or_add_pPr()
    for jc in ppr.findall(qn("w:jc")):
        ppr.remove(jc)

    cap = d.styles["Caption"]
    cap.font.name = FONT_BODY
    cap.font.size = Pt(9)
    cap.font.italic = False
    cap.font.color.rgb = RGBColor.from_string(NAVY)
    ppr = cap.element.get_or_add_pPr()
    for ind in ppr.findall(qn("w:ind")):
        ppr.remove(ind)
    for jc in ppr.findall(qn("w:jc")):
        ppr.remove(jc)

    # the contents styles the sample carries are capitals, underlined and widely
    # spaced; plain entries are wanted
    for sid, bold, size, before, after in (("toc 1", True, 10.5, 6, 2), ("toc 2", False, 10.5, 0, 2),
                                           ("toc 3", False, 10, 0, 2), ("table of figures", False, 10, 0, 2)):
        try:
            st = d.styles[sid]
        except KeyError:
            continue
        st.font.bold = bold; st.font.all_caps = False; st.font.small_caps = False; st.font.underline = False
        st.font.italic = False
        st.font.name = FONT_BODY; st.font.size = Pt(size)
        pf = st.paragraph_format
        pf.space_before = Pt(before); pf.space_after = Pt(after); pf.line_spacing = 1.0
        rpr = st.element.get_or_add_rPr()
        for tag in ("w:caps", "w:smallCaps", "w:u", "w:i", "w:iCs"):
            for el in rpr.findall(qn(tag)):
                rpr.remove(el)
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is not None:
            for k in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
                if fonts.get(qn(k)) is not None:
                    del fonts.attrib[qn(k)]
            fonts.set(qn("w:ascii"), FONT_BODY); fonts.set(qn("w:hAnsi"), FONT_BODY)

    # the cover's text box is a fixed height that clips a third line: let it
    # grow with its text
    for body_pr in cover.iter("{http://schemas.microsoft.com/office/word/2010/wordprocessingShape}bodyPr"):
        for ch in list(body_pr):
            if ch.tag.endswith("}noAutofit") or ch.tag.endswith("}spAutoFit") or ch.tag.endswith("}normAutofit"):
                body_pr.remove(ch)
        body_pr.append(OxmlElement("a:spAutoFit"))

    # footnotes restart on every page, as the concept report does
    sect = sec._sectPr
    for old in sect.findall(qn("w:footnotePr")):
        sect.remove(old)
    sect.append(parse_xml(f'<w:footnotePr xmlns:w="{W}"><w:numRestart w:val="eachPage"/></w:footnotePr>'))

    d.save(out)
    return out


if __name__ == "__main__":
    print("wrote", build())
