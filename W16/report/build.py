"""Build the Concept Design Report.

    python build.py            build the .docx into R<n>/
    python build.py --pdf      build and render to PDF through Word
    python build.py --pages    also render every PDF page to PNG contact sheets (R<n>/check/)

Revision 3 (W16) carries the Design Basis Report's furniture and content: the firm's
template, native captions, symbol lines, the decisions and adopted values of
report_basis/decisions.py, the same facts modules. Revisions 0 to 2 stay in W14/report/.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "report_basis"))

import doc as D  # noqa: E402
import notes as N  # noqa: E402

REV = "R3"
DATE = "September 2026"
PROJECT = "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri"
TITLE = "Concept Design Report"
OUT_DIR = os.path.join(HERE, REV)
OUT = os.path.join(OUT_DIR, f"Ibri_Concept_Design_Report_{REV}.docx")


def main(render_pdf=False, pages=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    d = D.new_document({
        "TITLE_1": PROJECT,
        "TITLE_2": TITLE,
        "TITLE_3": f"Revision {REV[1:]}  ·  {DATE}",
        "FOOTER": f"{TITLE}  ·  Revision {REV[1:]}",
    })
    N.reset()
    N.ensure_style(d)

    import rpt_front
    D.front_matter(d)                # the cover unnumbered, then i, ii, iii
    rpt_front.contents(d)
    rpt_front.abbreviations(d)
    rpt_front.executive_summary(d)
    D.body_start(d)                  # 1, 2, 3 from the first chapter to the end

    for mod, fns in (("rpt_ab", ("part_a", "part_b")), ("rpt_c", ("part_c",)), ("rpt_d", ("part_d",)),
                     ("rpt_ef", ("part_e", "part_f")), ("rpt_gh", ("part_g", "part_h")), ("rpt_app", ("appendices",))):
        m = __import__(mod)
        for fn in fns:
            getattr(m, fn)(d)

    D.number_pages(d)
    out = OUT
    try:
        N.save(d, out)
    except PermissionError:
        out = OUT.replace(".docx", "_new.docx")
        N.save(d, out)
        print("NOTE: the target file is open in Word; wrote a copy instead.")
    print(f"wrote {out}")

    if render_pdf:
        import to_pdf
        pdf, n = to_pdf.convert(out)
        print(f"wrote {pdf}  ({n} pages)")
        if pages:
            contact_sheets(pdf)


def contact_sheets(pdf, per=6, dpi=45):
    """Every page as a thumbnail, six to a sheet, in check/ beside the PDF: the render is
    looked at, not assumed."""
    import fitz
    from PIL import Image
    doc = fitz.open(pdf)
    folder = os.path.join(os.path.dirname(pdf), "check")
    os.makedirs(folder, exist_ok=True)
    for f in os.listdir(folder):
        os.remove(os.path.join(folder, f))
    thumbs = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        thumbs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    for k in range(0, len(thumbs), per):
        grp = thumbs[k:k + per]
        w = sum(t.width for t in grp) + 8 * (len(grp) + 1); h = max(t.height for t in grp) + 16
        sheet = Image.new("RGB", (w, h), "#bdbdbd"); x = 8
        for t in grp:
            sheet.paste(t, (x, 8)); x += t.width + 8
        sheet.save(os.path.join(folder, f"pages_{k + 1:03d}-{k + len(grp):03d}.png"))
    print("contact sheets ->", folder)


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv or "--pages" in sys.argv, pages="--pages" in sys.argv)
