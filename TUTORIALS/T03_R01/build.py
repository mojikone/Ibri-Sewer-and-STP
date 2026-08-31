"""Build T03 Revision 01.

    python build.py          build the .docx
    python build.py --pdf    build and render to PDF through Word
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import body
import body2
import body3
import body4
import doc as D
import front

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "T03_R01_Concept_Design_Methodology.docx")


def main(render_pdf=False):
    d = D.new_document()

    front.cover(d)

    D.h(d, 1, "Contents")
    D.toc(d)
    D.pagebreak(d)

    front.how_to_use(d)
    front.executive_summary(d)

    # establishing the flow
    body.s3_data(d)
    body.s4_population(d)
    body.s5_demand(d)
    body.s6_wastewater(d)
    body.s7_time(d)
    body.s8_peak(d)

    # the network
    body.s9_gravity(d)
    body3.s10_selfcleansing(d)
    body2.s10_pumping(d)
    body3.s12_septicity(d)
    body3.s13_utilities(d)
    body3.s14_modelling(d)
    body3.s15_existing(d)

    # the works
    body2.s11_stp(d)
    body2.s12_tse(d)
    body2.s13_sludge(d)

    # money and choosing
    body4.s19_cost(d)
    body4.s20_financial(d)
    body2.s14_appraisal(d)

    # reliability of the sources
    body2.s15_defects(d)

    D.footer_pagenum(d, "T03 Rev 01  Concept Design Methodology  ·  Project 2621")
    d.save(OUT)
    print(f"wrote {OUT}")

    if render_pdf:
        import to_pdf
        pdf, pages = to_pdf.convert(OUT)
        print(f"wrote {pdf}  ({pages} pages)")


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv)
