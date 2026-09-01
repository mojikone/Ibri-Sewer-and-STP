"""Build the Concept Design Report.

    python build.py          build the .docx
    python build.py --pdf    build and render to PDF through Word
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import doc as D
import notes as N

REV = "R1"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, REV,
                   f"Ibri_Concept_Design_Report_{REV}.docx")


def main(render_pdf=False):
    os.makedirs(os.path.join(HERE, REV), exist_ok=True)
    d = D.new_document()
    N.reset()
    N.ensure_style(d)

    import rpt_front
    rpt_front.cover(d)
    rpt_front.contents(d)
    rpt_front.abbreviations(d)
    rpt_front.executive_summary(d)

    import rpt_ab
    rpt_ab.part_a(d)
    rpt_ab.part_b(d)

    for mod, fns in (("rpt_cd", ("part_c", "part_d")),
                     ("rpt_ef", ("part_e", "part_f")),
                     ("rpt_gh", ("part_g", "part_h"))):
        try:
            m = __import__(mod)
        except ImportError:
            continue
        for fn in fns:
            getattr(m, fn)(d)

    D.footer_pagenum(d, f"Ibri Concept Design Report  ·  Revision "
                        f"{REV[1:]}  ·  Renardet Project 2621")

    out = OUT
    try:
        N.save(d, out)
    except PermissionError:
        # the document is open in Word; write beside it rather than fail
        out = OUT.replace(".docx", "_new.docx")
        N.save(d, out)
        print("NOTE: the target file is open in Word; wrote a copy instead.")
    print(f"wrote {out}")

    if render_pdf:
        import to_pdf
        pdf, pages = to_pdf.convert(out)
        print(f"wrote {pdf}  ({pages} pages)")


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv)
