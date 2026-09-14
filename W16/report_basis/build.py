"""Build the Design Basis Report: settlement boundaries, population, flows and loads.

    python build.py            build the .docx into R<n>/
    python build.py --pdf      build and render to PDF through Word
    python build.py --pages    also render every PDF page to PNG contact sheets (check/)

Before the build, when the facts changed: python facts_basis.py; python charts_basis.py;
python make_panels.py; the maps in QGIS (qgis_maps_basis.run()); python compose_panels.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "report"))
sys.path.insert(0, HERE)

import doc as D  # noqa: E402
import notes as N  # noqa: E402

REV = "R0"
DATE = "September 2026"
PROJECT = "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri"
TITLE = "Design Basis Report"
SUBTITLE = "Settlement Boundaries, Population, Flows and Loads"
OUT_DIR = os.path.join(HERE, REV)
OUT = os.path.join(OUT_DIR, f"Ibri_Design_Basis_Report_{REV}.docx")


def main(render_pdf=False, pages=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    d = D.new_document({
        "TITLE_1": PROJECT,
        "TITLE_2": TITLE,
        "TITLE_3": f"{SUBTITLE}\nRevision {REV[1:]}  ·  {DATE}",
        "FOOTER": f"{TITLE}: {SUBTITLE}  ·  Revision {REV[1:]}",
    })
    N.reset()
    N.ensure_style(d)

    import rpt_basis as R
    R.front(d)
    R.s1_purpose(d)
    R.s2_boundaries(d)
    R.s3_people(d)
    R.s4_landuse(d)
    R.s5_demand(d)
    R.s6_growth(d)
    R.s7_flows(d)
    R.s8_assumptions(d)
    R.s9_data(d)
    R.s10_decisions(d)
    R.appendices(d)

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
    for i in range(len(doc)):
        pix = doc[i].get_pixmap(dpi=dpi)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        thumbs.append((i + 1, im))
    w = max(im.width for _, im in thumbs); h = max(im.height for _, im in thumbs)
    cols = 3; rows = (per + cols - 1) // cols
    for s in range(0, len(thumbs), per):
        sheet = Image.new("RGB", (cols * (w + 10) + 10, rows * (h + 30) + 10), "#d9d9d9")
        from PIL import ImageDraw
        dr = ImageDraw.Draw(sheet)
        for k, (n, im) in enumerate(thumbs[s:s + per]):
            x = 10 + (k % cols) * (w + 10); y = 10 + (k // cols) * (h + 30)
            sheet.paste(im, (x, y)); dr.text((x + 4, y + h + 6), f"page {n}", fill="black")
        p = os.path.join(folder, f"pages_{s + 1:03d}_{min(s + per, len(thumbs)):03d}.png")
        sheet.save(p)
    print(f"contact sheets in {folder}")


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv, pages="--pages" in sys.argv)
