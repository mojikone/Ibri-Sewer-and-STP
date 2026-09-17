"""The decisions asked of Nama Water Services and the values adopted for information, as the
Design Basis Report lists them (report_basis/decisions.py), with the section references of
this report. One list feeds both reports, so they cannot differ."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report_basis"))
from decisions import APPROVALS as _A, INFORMED as _I, DATA_REQUESTS  # noqa: E402,F401

import doc as D  # noqa: E402

# where each item is explained in the Concept Design Report, by its title
SECTION = {
    "Settlement boundaries": "14.2", "Persons per property": "14.4", "Use of each plot": "14.5",
    "The overflow": "14.8", "The design horizon": "14.9", "The growth beyond 2050": "14.7",
    "Gradients and self-cleansing at the concept stage": "12.2",
    "The 126 meters with no plot within 15 metres": "14.3", "Water demand and return": "15.1 and 15.3",
    "The industrial estates": "15.2", "The connection ratio": "15.8", "Infiltration and peak flow": "15.5 and 15.6",
    "Depth": "12.3", "STP flows and loads": "13.1 and 15.8", "Treated effluent": "17",
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
