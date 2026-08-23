# -*- coding: utf-8 -*-
"""T02 tutorial -> PDF, rendered directly with reportlab (NO Word needed).

Word COM proved unreliable here (a stray instance blocks the export), so the PDF is
now produced independently from the same content blocks as the docx
(report_content.build()). Re-run: python W8/report/make_methodology_pdf.py
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

import t02_content as RC

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "T02_Hydraulic_Design_of_a_Gravity_Sewer.pdf")

NAVY = colors.HexColor("#1F3864")
BLUE = colors.HexColor("#2E5A88")
GREY = colors.HexColor("#555555")
HDRFILL = colors.HexColor("#D9E2F3")

ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.6,
                      leading=13.4, spaceAfter=6, alignment=TA_JUSTIFY)
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=14.5,
                    textColor=NAVY, spaceBefore=12, spaceAfter=7)
BUL = ParagraphStyle("bul", parent=BODY, leftIndent=14, bulletIndent=3, spaceAfter=4)
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8.2, textColor=GREY, alignment=TA_CENTER,
                     spaceBefore=3, spaceAfter=10)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.2, leading=10.6, spaceAfter=0,
                      alignment=TA_JUSTIFY)
CELLH = ParagraphStyle("cellh", parent=CELL, fontName="Helvetica-Bold", alignment=TA_CENTER)
TOCS = [ParagraphStyle("toc1", parent=BODY, fontSize=10, leading=15, firstLineIndent=0,
                       leftIndent=0)]


class Doc(BaseDocTemplate):
    """Adds the TOC hook and a page footer."""

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "h1":
            txt = flowable.getPlainText()
            if txt != "Contents":
                self.notify("TOCEntry", (0, txt, self.page))

    def footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GREY)
        canvas.drawString(2.1 * cm, 1.2 * cm,
                          "Ibri 2621 — W8 Sewer Network Design Pipeline (internal)")
        canvas.drawRightString(A4[0] - 2.1 * cm, 1.2 * cm, f"{doc.page}")
        canvas.restoreState()


def fit(path, want_in):
    """Scale an image to `want_in` inches wide, capped to the frame, keeping ratio."""
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    max_w = min(want_in * inch, A4[0] - 4.4 * cm)
    max_h = A4[1] - 8.0 * cm
    scale = min(max_w / w, max_h / h)
    return Image(path, width=w * scale, height=h * scale)


def build():
    blocks = RC.build()
    doc = Doc(OUT, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
              topMargin=2.0 * cm, bottomMargin=1.9 * cm,
              title="W8 Sewer Network Design Pipeline — Methodology",
              author="Ibri 2621 design team")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=doc.footer)])

    story = []
    for b in blocks:
        kind = b[0]
        if kind == "cover":
            c = b[1]
            story += [Spacer(1, 3.4 * cm),
                      Paragraph(c["eyebrow"], ParagraphStyle("e", parent=BODY, alignment=TA_CENTER,
                                                             fontSize=11, textColor=GREY)),
                      Spacer(1, 0.5 * cm),
                      Paragraph(c["title"], ParagraphStyle("t", parent=BODY, alignment=TA_CENTER,
                                                           fontName="Helvetica-Bold", fontSize=23,
                                                           leading=28, textColor=NAVY)),
                      Paragraph(c["subtitle"], ParagraphStyle("s", parent=BODY, alignment=TA_CENTER,
                                                              fontSize=14, textColor=BLUE)),
                      Spacer(1, 1.3 * cm),
                      Paragraph(c["note"], ParagraphStyle("n", parent=BODY, alignment=TA_CENTER,
                                                          fontName="Helvetica-Oblique", fontSize=10,
                                                          textColor=GREY)),
                      Paragraph(c["date"], ParagraphStyle("d", parent=BODY, alignment=TA_CENTER,
                                                          fontSize=10, textColor=GREY)),
                      Spacer(1, 1.2 * cm)]
            rows = [[Paragraph("Item", CELLH), Paragraph("Value", CELLH)]] + \
                   [[Paragraph(k, CELL), Paragraph(v, CELL)] for k, v in c["facts"]]
            t = Table(rows, colWidths=[5.0 * cm, 9.6 * cm], hAlign="CENTER")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA6B2")),
                ("BACKGROUND", (0, 0), (-1, 0), HDRFILL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            story.append(t)
        elif kind == "toc":
            toc = TableOfContents()
            toc.levelStyles = TOCS
            story.append(toc)
        elif kind == "pagebreak":
            story.append(PageBreak())
        elif kind == "h1":
            story.append(Paragraph(b[1], H1))
        elif kind == "p":
            story.append(Paragraph(b[1], BODY))
        elif kind == "bullet":
            story.append(Paragraph(f"<b>{b[1]}</b>{b[2]}", BUL, bulletText="•"))
        elif kind == "table":
            headers, rows, widths = b[1], b[2], b[3]
            data = [[Paragraph(h, CELLH) for h in headers]]
            for r in rows:
                data.append([Paragraph(str(x), CELL) for x in r])
            total = sum(widths)
            avail = (A4[0] - 4.4 * cm)
            cw = [w / total * avail for w in widths]
            t = Table(data, colWidths=cw, repeatRows=1, hAlign="CENTER")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA6B2")),
                ("BACKGROUND", (0, 0), (-1, 0), HDRFILL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
            story += [t, Spacer(1, 0.35 * cm)]
        elif kind == "img":
            path, want, cap = b[1], b[2], b[3]
            if os.path.exists(path):
                story.append(KeepTogether([fit(path, want), Paragraph(cap, CAP)]))
        elif kind == "img2":
            p1, p2, cap = b[1], b[2], b[3]
            if os.path.exists(p1) and os.path.exists(p2):
                i1, i2 = fit(p1, 2.6), fit(p2, 3.0)
                t = Table([[i1, i2]], hAlign="CENTER")
                t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
                story.append(KeepTogether([t, Paragraph(cap, CAP)]))

    doc.multiBuild(story)
    print("saved", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    # If a viewer has the PDF open, Windows locks it. Write a timestamped copy rather than
    # losing the deliverable, and say so loudly (user 2026-08-20: outputs must be complete).
    try:
        build()
    except PermissionError:
        import datetime
        alt = OUT.replace(".pdf", "_" + datetime.datetime.now().strftime("%H%M") + ".pdf")
        globals()["OUT"] = alt
        build()
        print(f"  NOTE: the usual PDF was open in a viewer, so this run wrote {alt}")
