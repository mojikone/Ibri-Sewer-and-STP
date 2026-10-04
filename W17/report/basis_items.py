"""The decisions asked of Nama Water Services and the values adopted for information, as the
Design Basis Report lists them (report_basis/decisions.py), with the section references of
this report. One list feeds both reports, so they cannot differ.

W17 (engineer, 2026-10-03): the use of each plot is adopted, not asked ("drop this from decisions. We have adopted
it."), and two items carry the client's terms, the occupancy rate and the growth rate. The Design Basis Report keeps its
own list; this report renames, moves and renumbers here. The chapter modules still call ask() and adopt() by the basis
report's numbers, and each box comes out under this report's name and number."""
import os
import re
import sys

# W17: the decisions list stays where the basis report keeps it, in W16
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "W16", "report_basis"))
from decisions import APPROVALS as _A, INFORMED as _I, DATA_REQUESTS as _DR, BASIS as _B  # noqa: E402,F401

import doc as D  # noqa: E402

# the basis report's seven data requests, and those this report adds (engineer, 2026-10-04)
DATA_REQUESTS = list(_DR) + [
    ("Regional Master Plan", "The master plan report and the flows it adopts for Ibri",
     "Needed for the verification of Section 5.3; not provided."),
    ("Treated effluent demand", "Each customer's demand now and its plans for 2030, 2040 and 2050, on the template "
     "issued after the meeting of 23 September 2026",
     "Defines the customers and the treated effluent network options (Sections 4.4 and 6.4)."),
    ("Meteorological record", "Hourly wind speed, direction and temperature from the nearest station, five years",
     "Needed for the odour dispersion modelling of the plant sites (Section 7.3)."),
]

# the basis report's title -> this report's title
RENAME = {"Persons per property": "Occupancy rate", "Use of each plot": "Land-use layer",
          "The growth beyond 2050": "Growth rate beyond 2050"}
# the text, where it changes with the name
TEXT = {
    "Occupancy rate": "Approve the occupancy rate calculated for each settlement, in persons per property, with the floor "
                      "of 4.0, the cap of 6.12 and the rule for settlements under a thousand people.",
    "Land-use layer": "The use of each plot is determined from its meters and the satellite image, and is the basis for "
                      "placing the loads.",
    "Growth rate beyond 2050": "Approve the growth rate beyond 2050, where the population series is extended: the rise to "
                               "2.40 per cent a year by 2058 and that rate held to 2100. The series to 2050 is the "
                               "client's own.",
}
# a decision of the basis report adopted here, and the adopted value it follows
MOVED = {"Land-use layer": "The 126 meters with no plot within 15 metres"}

# where each item is explained in the Concept Design Report, by its title
SECTION = {
    "Settlement boundaries": "4.1.2", "Occupancy rate": "4.1.4", "Land-use layer": "4.1.5",
    "The overflow": "4.1.8", "The design horizon": "4.1.9", "Growth rate beyond 2050": "4.1.7",
    "Gradients and self-cleansing at the concept stage": "3.3.2 and 6.2.8",   # W17: Section 6.2.8 extends it
    "The 126 meters with no plot within 15 metres": "4.1.3", "Water demand and return": "4.2.1 and 4.2.3",
    "The industrial estates": "4.2.2", "The connection ratio": "4.2.8", "Infiltration and peak flow": "4.2.5 and 4.2.6",
    "Depth": "3.3.3", "STP flows and loads": "3.4.1 and 4.2.8", "Treated effluent": "4.4",
}

# status and basis of every item, for the table of Section 1.5.1
BASIS = {RENAME.get(k, k): v for k, v in _B.items()}
BASIS["Land-use layer"] = ("Adopted: design method", "The cadastre's own land-use field is not usable as it stands; the "
                                                     "use is determined from the meters and the satellite image")


def _here(item):
    ask, group, title, what = item
    title = RENAME.get(title, title)
    what = TEXT.get(title, what)
    what = re.sub(r"\s*\(Sections? [^)]*\)\.?\s*$", "", what).rstrip(".")
    sec = SECTION[title]
    return ask, group, title, f"{what} (Section{'s' if ' and ' in sec else ''} {sec})."


_asked = [_here(i) for i in _A]
APPROVALS = [i for i in _asked if i[2] not in MOVED]
INFORMED = []
for _i in (_here(i) for i in _I):
    INFORMED.append(_i)
    INFORMED += [("inform",) + a[1:] for a in _asked if MOVED.get(a[2]) == _i[2]]


def number(title):
    """'Decision 4' or 'Adopted (8)': the number an item carries in this report, by its title in either report."""
    titles = [t for _, _, t, _ in APPROVALS + INFORMED]
    k = titles.index(RENAME.get(title, title)) + 1
    return f"Decision {k}" if k <= len(APPROVALS) else f"Adopted ({k})"


def box(d, title):
    """The box of an item, by its title: a decision, or an adopted value numbered after the decisions."""
    title = RENAME.get(title, title)
    for i, (_, _, t, what) in enumerate(APPROVALS):
        if t == title:
            return D.callout(d, f"Decision {i + 1}.", what)
    for i, (_, _, t, what) in enumerate(INFORMED):
        if t == title:
            return D.callout(d, f"Adopted ({len(APPROVALS) + i + 1}).", what, fill="F2F2F2", colour=D.GREY, border="BFBFBF")
    raise KeyError(title)


def ask(d, n):
    """The box of the basis report's decision n (1-based), under this report's number."""
    box(d, _A[n - 1][2])


def adopt(d, n):
    """The box of the basis report's adopted value n (1-based), under this report's number."""
    box(d, _I[n - 1][2])
