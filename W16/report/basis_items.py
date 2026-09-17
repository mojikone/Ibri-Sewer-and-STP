"""The decisions asked of Nama Water Services and the values adopted for information, as the
Design Basis Report lists them (report_basis/decisions.py), with the section references of
this report. One list feeds both reports, so they cannot differ."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report_basis"))
from decisions import APPROVALS as _A, INFORMED as _I, DATA_REQUESTS, BASIS  # noqa: E402,F401

import doc as D  # noqa: E402

# where each item is explained in the Concept Design Report, by its title
SECTION = {
    "Settlement boundaries": "4.1.2", "Persons per property": "4.1.4", "Use of each plot": "4.1.5",
    "The overflow": "4.1.8", "The design horizon": "4.1.9", "The growth beyond 2050": "4.1.7",
    "Gradients and self-cleansing at the concept stage": "3.3.2",
    "The 126 meters with no plot within 15 metres": "4.1.3", "Water demand and return": "4.2.1 and 4.2.3",
    "The industrial estates": "4.2.2", "The connection ratio": "4.2.8", "Infiltration and peak flow": "4.2.5 and 4.2.6",
    "Depth": "3.3.3", "STP flows and loads": "3.4.1 and 4.2.8", "Treated effluent": "4.4",
}


def _here(item):
    ask, group, title, what = item
    what = re.sub(r"\s*\(Sections? [^)]*\)\.?\s*$", "", what).rstrip(".")
    sec = SECTION[title]
    return ask, group, title, f"{what} (Section{'s' if ' and ' in sec else ''} {sec})."


APPROVALS = [_here(i) for i in _A]
INFORMED = [_here(i) for i in _I]


def ask(d, n):
    """The approval box of decision n (1-based)."""
    D.callout(d, f"Decision {n}.", APPROVALS[n - 1][3])


def adopt(d, n):
    """The information box of adopted item n (1-based), numbered after the decisions."""
    D.callout(d, f"Adopted ({len(APPROVALS) + n}).", INFORMED[n - 1][3], fill="F2F2F2", colour=D.GREY, border="BFBFBF")
