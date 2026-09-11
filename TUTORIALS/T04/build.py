"""Build Tutorial T04 — the whole method in one tutorial.

    python build.py          build the .docx
    python build.py --pdf    build and render to PDF through Word (fills the contents)

Chapters are written by the ch*.py modules; every number is read live from the W14
outputs through W14/report/facts_w14.py, so a rebuild after a data change updates them.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours

import doc as D  # noqa: E402
import ch00_front as front  # noqa: E402
import ch01_data as c01  # noqa: E402
import ch02_population as c02  # noqa: E402
import ch03_flows as c03  # noqa: E402
import ch04_peak_tiers as c04  # noqa: E402
import ch05_gravity as c05  # noqa: E402
import ch06_selfclean as c06  # noqa: E402
import ch07_network_other as c07  # noqa: E402
import ch08_plant as c08  # noqa: E402
import ch09_appraisal as c09  # noqa: E402

OUT = os.path.join(HERE, "T04_From_Meter_to_Pipe.docx")


def main(render_pdf=False):
    d = D.new_document()
    front.cover(d)
    D.p(d, "Contents", bold=True, size=17, colour=D.BLUE)   # not a heading style, so the contents does not list itself
    D.toc(d)
    D.pagebreak(d)
    front.how_to_use(d)
    front.summary(d)

    # population and land
    c01.c01_data(d)
    c01.c02_plots(d)
    c02.c03_occupancy(d)
    c02.c04_capacity(d)
    c02.c05_growth(d)
    # flows
    c03.c06_demand(d)
    c03.c07_plot_flow(d)
    c03.c08_time(d)
    c04.c09_peak(d)
    # the network
    c04.c10_tiers(d)
    c05.c11_gravity(d)
    c06.c12_selfclean(d)
    c07.c13_pumping(d)
    c07.c14_septicity(d)
    c07.c15_utilities(d)
    c07.c16_modelling(d)
    c07.c17_existing(d)
    # the works
    c08.c18_plant(d)
    c08.c19_effluent(d)
    c08.c20_sludge(d)
    # money, choosing, and the limits of the sources
    c09.c21_cost(d)
    c09.c22_financial(d)
    c09.c23_options(d)
    c09.c24_limits(d)
    c09.appendix(d)

    D.footer_pagenum(d, "T04 Rev 00  From the Meter to the Pipe  ·  Project 2621")
    d.save(OUT)
    print(f"wrote {OUT}")
    if render_pdf:
        import to_pdf
        pdf, pages = to_pdf.convert(OUT)
        print(f"wrote {pdf}  ({pages} pages)")


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv)
