"""Build T03 - Concept Design Methodology, Equations and Workflows.

    python build.py          build the .docx
    python build.py --pdf    build and render to PDF through Word
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import doc as D
import front

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "T03_Concept_Design_Methodology.docx")


def main(render_pdf=False):
    d = D.new_document()

    front.cover(d)

    D.h(d, 1, "Contents")
    D.toc(d)
    D.pagebreak(d)

    front.how_to_use(d)
    front.executive_summary(d)

    import body
    body.build_part1(d)

    try:
        import body2
        body2.build_part2(d)
    except ImportError:
        pass

    D.footer_pagenum(d, "T03 Concept Design Methodology  ·  Project 2621")
    d.save(OUT)
    print(f"wrote {OUT}")

    if render_pdf:
        import to_pdf
        pdf, pages = to_pdf.convert(OUT)
        print(f"wrote {pdf}  ({pages} pages)")


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv)
