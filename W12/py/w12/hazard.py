"""W12 — flood hazard.

Ibri sewer & STP (2621).  One module, owning every question the design asks of the
flood-hazard grids in ``Data/04 Lekhuwair``:

    is this point in a channel · at what return period · how deep · how far to dry ground

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
``w12.criteria`` (which imports nothing).  No W8/W10/W11a code is reached, directly or
indirectly.

--------------------------------------------------------------------------------------
THE FOUR THINGS EVERY CALLER MUST KNOW
--------------------------------------------------------------------------------------

0.  THE CLASS THRESHOLDS ARE NOT DECLARED HERE.  "Which classes are washout ground",
    "which return period governs the wadi test" and "is no-data dry" live in
    ``w12.criteria`` and this module reads them.  Until 2026-09-03 both files declared
    them, and they DISAGREED: criteria said washout ground is H4+, this module said H5+.
    Measured on the client's Main Pipe at the 50-year event, that is 11.02 km against
    6.77 km — a 4.25 km gap on one input alignment.  See ``channel_min_class()`` and
    ``scour_min_class()``.

1.  NO-DATA IS DRY HIGH GROUND.  Engineer's ruling, 2026-09-03.  A cell with -9999 was
    not inundated in that event; it is not "untested".  See ``EVIDENCE_NODATA_IS_DRY``
    below — the ruling was checked against the data and holds.  BUT: the grids contain
    NO class-0 cell, so "dry" and "no-data" are the SAME set of cells and a search for
    dry ground can only ever land on a no-data cell.  ``DryGround`` now says so on every
    answer — see ``EVIDENCE_NO_CLASS_ZERO`` and point 4.

2.  THESE GRIDS HOLD AR&R FLOOD-HAZARD CLASSES 1-6, NOT DEPTH.  The class is keyed on
    danger to people, vehicles and buildings.  Using it as a proxy for the guideline's
    washout / scour criterion (PAM-GUD-203 p30 §4.4.1) is a PROJECT ASSUMPTION —
    ``ASSUMP-HAZ-2`` — because the guideline attaches no return period and no threshold
    to "areas subject to washout during heavy storms".

3.  NEVER READ THESE RASTERS DECIMATED.  The GeoTIFFs carry AVERAGE-built overviews.
    A read that passes ``out_shape``, or a warp, or a QGIS view zoomed out, silently
    averages neighbouring classes and returns values such as 1.0046296.  Measured over
    the 531.4 km2 boundary at a 30 m decimated read, only 53.95 % of wet cells came back
    as an integer class; at native resolution, 100.00 % did.  Every read in this module
    is native-resolution and is asserted to be integral.

4.  A LENGTH ALONG A LINE IS CELL-WISE, NOT RUN-WISE.  ``LineHazard.channel_length_m``
    and ``.scour_length_m`` sum the samples that ARE in a channel / at scour risk.  Until
    2026-09-03 they summed the whole width of every wet RUN that contained at least one
    such sample, so a single H5 cell painted its entire run.  Measured on the client's
    Main Pipe at the 50-year event: 15.41 km of "scour" ground where the cell-wise figure
    is 6.77 km (2.28x), and 25.67 km of "channel" against 16.26 km (1.58x).  The
    run-envelope figures still exist, because "how long is the wet run this pipe is
    inside" is a real question — but they are named ``run_span_scour_m`` and
    ``run_span_channel_m`` and they are documented as an upper bound, never as a length
    of affected pipe.

--------------------------------------------------------------------------------------
WHICH RETURN PERIOD GOVERNS WHICH DECISION — established from the source PDFs
--------------------------------------------------------------------------------------

An exhaustive regex sweep of PAM-GUD-201, -202 and -203 for return-period language
("1-in-N year", "1:N ARI", "N year flood", "return period") returns FIVE hits in the
three documents and no others:

  G201 p85  §9.3 Wadi crossings
            "...flood frequency analysis (1-in-20 year, 1-in-50 year, 1-in-100 year,
            etc... floods)..."
  G203 p38  §7.2 Site Selection & Layout (pumping stations)
            "Pump pedestal level or building floor, electrical transformers/ pad mounted
            substation or emergency generator are to be located above maximum flood
            level, with the floors being a minimum of 300 mm above the 1:50 year flood
            level. ... properly design the surface/stormwater management considering the
            1:50 ARI."
  G203 p63  Table 27 Site Selection Requirements, row (i) — STPs
            "Flood considerations (25 and 100 year flood levels, compliance when
            constructing in flood prone areas) / STPs shall be fully operational during
            floods (existing and future sites)"
  G202 p78  water pumping stations — same 300 mm / 1:50 ARI wording as G203 p38
  G202 p79  "The pumping station site, electrical infrastructures, access road shall not
            be liable to flooding during a 1 in 50 year ARI"

So the guidelines name 20, 25, 50 and 100 year.  They never name 10 or 500 year, and
they never attach a return period to the washout prohibition.  That is the whole of the
authority; everything else in this module is a labelled project assumption.

SUBSTITUTION.  We hold a 25-year grid and no 20-year grid.  For the wadi-crossing
procedure we substitute 25 for the guideline's 1-in-20 (``SUBST-HAZ-1``).  The
substitution is CONSERVATIVE: a 25-year event is larger than a 20-year event, so the
25-year wet extent contains the 20-year wet extent.  Measured nesting over the study
area supports this — 0.093 % of 10-year wet cells are dry at 25 year, 0.049 % of 25-year
wet cells are dry at 50 year, 0.027 % of 50-year wet cells are dry at 500 year.  Note
also that 25 year is not a free invention: G203 p63 uses it in its own right for STP
siting.

--------------------------------------------------------------------------------------
WHAT THIS MODULE CANNOT DO
--------------------------------------------------------------------------------------

It cannot give a FLOOD LEVEL in m aOD.  G203 p38 §7.2 wants a pumping-station floor
300 mm above the 1:50 flood level; that needs a water-surface grid and we hold a hazard
CLASS grid.  ``flood_level_m_aod`` therefore raises ``HazardDataUnavailable`` rather
than returning a made-up number.  ``NWS_REQUESTS`` records the ask.

--------------------------------------------------------------------------------------
API
--------------------------------------------------------------------------------------

    from w12.hazard import HazardGrids, governing, RETURN_PERIODS, HAZARD_FLAGS

    with HazardGrids() as hz:
        s  = hz.sample(449899.6, 2567301.7, rp=50)     # -> HazardSample
        cs = hz.sample_many(xs, ys, rp=50)             # -> int8 array, 0 = dry
        allrp = hz.sample_all(x, y)                    # -> {10: .., 25: .., ...}
        rp0 = hz.first_wet_rp(x, y)                    # smallest rp at which it is wet
        d   = hz.distance_to_dry(x, y, rp=50)          # -> DryGround(found=..., ...)
        pr  = hz.profile(coords, rp=50)                # -> LineHazard, .crossings
        duty = governing("pumping_station")            # -> Duty, with its citation
        hz.provenance()                                # -> dict to stamp on every output

Author: W12 pipeline.  2026-09-03.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:  # rasterio is the only heavyweight dependency
    import rasterio
    from rasterio.windows import Window
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "w12.hazard needs rasterio.  See _SETUP/ENVIRONMENT.md."
    ) from _exc

# The design basis.  A SIBLING, not a borrow: w12.criteria imports nothing at all, so
# there is no cycle and no path into W8/W10/W11a.  It is imported for exactly three
# quantities — the washout classes, the channel class and the wadi return period — which
# this module must NOT declare a second time.  The try/except is only so
# `python W12/py/w12/hazard.py` still runs as a bare script.
try:
    from .criteria import Criteria, DEFAULT as CRIT
except ImportError:  # pragma: no cover - direct script execution
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from w12.criteria import Criteria, DEFAULT as CRIT


# =====================================================================================
# 1.  THE DATA
# =====================================================================================

#: Grid file name for each return period, as shipped by the client.
GRID_FILES: Dict[int, str] = {
    10: "Hazard_T10y.tif",
    25: "Hazard_T25y.tif",
    50: "Hazard_T50y.tif",
    100: "Hazard_T100y.tif",
    500: "Hazard_T500y.tif",
}

#: Return periods we hold, ascending.
RETURN_PERIODS: Tuple[int, ...] = (10, 25, 50, 100, 500)

#: The value the client's raster script writes where the model reports nothing.
NODATA = -9999.0

#: Every grid is EPSG:32640 (UTM 40N).  Callers must pass eastings/northings in it.
CRS = "EPSG:32640"

#: MEASURED 2026-09-03 with rasterio, straight off the shipped files.
#: (pixel size m, width px, height px, west, south, east, north).
GRID_GEOMETRY: Dict[int, dict] = {
    10:  dict(res_m=3.0, width=68000, height=58097,
              bounds=(320000.0, 2439998.5, 524000.0, 2614289.5)),
    25:  dict(res_m=3.0, width=68000, height=58097,
              bounds=(320000.0, 2439998.5, 524000.0, 2614289.5)),
    50:  dict(res_m=3.0, width=68000, height=58097,
              bounds=(320000.0, 2439998.5, 524000.0, 2614289.5)),
    100: dict(res_m=2.0, width=99994, height=84669,
              bounds=(322229.1, 2443923.1, 522217.1, 2613261.1)),
    500: dict(res_m=3.0, width=68000, height=58097,
              bounds=(320000.0, 2439998.5, 524000.0, 2614289.5)),
}

#: WARNING for raster algebra.  The 100-year grid is on a DIFFERENT grid from the other
#: four: 2 m cells on its own origin, against 3 m cells on a shared origin.  Point
#: sampling across return periods is safe (each grid is sampled independently, which is
#: what this module does).  CELL-BY-CELL raster algebra mixing T100y with any other
#: return period is NOT valid without an explicit nearest-neighbour resample.
GRID_100Y_IS_NOT_CO_REGISTERED = True


def _find_hazard_dir() -> Path:
    """Locate ``Data/04 Lekhuwair``.

    Order: ``$W12_HAZARD_DIR``, then a walk up from this file looking for the project
    tree.  Nothing is guessed silently — if it is not found, we say where we looked.
    """
    env = os.environ.get("W12_HAZARD_DIR")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
        raise FileNotFoundError(f"W12_HAZARD_DIR is set to {p!s} but it is not a directory")

    tried: List[Path] = []
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "Data" / "04 Lekhuwair"
        tried.append(cand)
        if cand.is_dir():
            return cand
    raise FileNotFoundError(
        "Could not find the flood-hazard grids.  Set $W12_HAZARD_DIR.  Looked in:\n  "
        + "\n  ".join(str(t) for t in tried)
    )


# =====================================================================================
# 2.  THE CLASS DEFINITION — read off the CLIENT'S OWN raster script, not from memory
# =====================================================================================

#: Verbatim from ``Data/04 Lekhuwair/Hazard_T100y.rasscript`` (and T500y, identical).
#: This is the client's derivation of the shipped grids from their depth (d) and
#: velocity (v) model output, so it is the authoritative definition of what the numbers
#: in the GeoTIFFs mean.
RASSCRIPT_VERBATIM = """\
If d = NoData OrElse v = NoData Then
Output = NoData
ElseIf d > 4 Or v > 4 Or d*v > 4 Then
Output = 6 'H6 unsafe for people, vehicles & all buildings
ElseIf d > 2 Or v>2 Or d*v>1 Then
Output = 5 'H5 unsafe for people, vehicles & some buildings
ElseIf d > 1.2 Or d * v > 0.6 Then
Output = 4 'H4 unsafe for people & vehicle
ElseIf d > 0.5 Then
Output = 3 'H3 unsafe for vehicle and vulnerable people
ElseIf d > 0.3 Or d * v > 0.3 Then
Output = 2 'H2 unsafe for small vehicles
Else
Output = 1 'H1 generally safe for people, vehicles, & buildings
End If"""


@dataclass(frozen=True)
class HazardClass:
    """One AR&R hazard class, with what it does and does not tell you about depth."""

    code: int
    label: str
    #: Depth bounds implied by the class, derived by exhausting the rasscript's decision
    #: tree over d in [0, 8] m at 0.5 mm and v in [0, 8] m/s at 5 mm/s (2026-09-03).
    depth_lo_m: float
    depth_hi_m: float
    vel_lo_ms: float
    vel_hi_ms: float
    #: True only where the class band is bounded above AND rises monotonically with the
    #: class number, i.e. where the class really is a statement about depth.  From
    #: class 4 up the class can be driven by velocity alone and the depth band collapses
    #: back towards zero — H5 admits 0.05 m of water at 3 m/s.
    depth_determinate: bool


#: The measured bounds.  Note H4's lower bound (0.300 m) sits BELOW H3's (0.500 m):
#: a higher hazard class does not imply deeper water.  This is not an error.
HAZARD_CLASSES: Dict[int, HazardClass] = {
    1: HazardClass(1, "H1 generally safe for people, vehicles & buildings",
                   0.000, 0.300, 0.0, 2.000, True),
    2: HazardClass(2, "H2 unsafe for small vehicles",
                   0.150, 0.500, 0.0, 2.000, True),
    3: HazardClass(3, "H3 unsafe for vehicles and vulnerable people",
                   0.500, 1.200, 0.0, 1.200, True),
    4: HazardClass(4, "H4 unsafe for people & vehicles",
                   0.300, 2.000, 0.0, 2.000, False),
    5: HazardClass(5, "H5 unsafe for people, vehicles & some buildings",
                   0.000, 4.000, 0.0, 4.000, False),
    6: HazardClass(6, "H6 unsafe for people, vehicles & all buildings",
                   0.000, math.inf, 0.0, math.inf, False),
}

#: Sentinel for "no class here".  Under the engineer's ruling this means DRY GROUND.
DRY = 0


# --- project thresholds: DECLARED IN w12.criteria, READ HERE -------------------------
#
# DEFECT 4, fixed 2026-09-03.  This module used to declare DEFAULT_CHANNEL_CLASS = 3 and
# DEFAULT_SCOUR_CLASS = 5 while `criteria.HAZARD_WADI_CLASSES = (4, 5, 6)` answered the
# SAME washout question with 4.  Nothing reconciled them, and the number a stage got
# depended on which module it happened to import.  MEASURED on the client's Main Pipe at
# the 50-year event, cell-wise: H5+ gives 6.77 km of washout ground, H4+ gives 11.02 km.
# A 4.25 km disagreement on an INPUT alignment, from two constants for one quantity.
#
# The surviving value is the project register's -- `_BRAIN/02_DESIGN_CRITERIA.md` sec 6,
# "What counts as 'wadi ground'" = classes 4/5/6 -- which is also what `terrain.py`,
# `contract.py` and `present.py` already read.  This module's H5 was the unregistered
# fourth answer and it is withdrawn.  The H5 ARGUMENT is not withdrawn: H5 is still the
# first class admitting v > 2 m/s, and if NWS answer NWS_REQUESTS["scour_criterion"] with
# a velocity, H5 may well be right.  Changing it is a one-line edit in
# `criteria.HAZARD_WADI_CLASSES`, and every module in W12 follows.


def scour_min_class(crit: "Criteria" = CRIT) -> int:
    """Lowest hazard class counted as scour / washout ground.  ASSUMP-HAZ-4.

    Read from ``criteria.HAZARD_WADI_CLASSES``; this module declares no copy.  The
    guideline (G203 p30 4.4.1) prohibits pipes and chambers in "areas subject to washout
    during heavy storms" and attaches neither a threshold nor a return period, so the
    threshold is a PROJECT ASSUMPTION and travels on every output as ASSUMP-HAZ-4.
    """
    cls = tuple(sorted(int(c) for c in crit.HAZARD_WADI_CLASSES))
    if not cls or cls != tuple(range(cls[0], 7)):
        raise HazardDataError(
            f"criteria.HAZARD_WADI_CLASSES = {crit.HAZARD_WADI_CLASSES!r} is not a "
            "contiguous run up to class 6.  This module tests washout ground as "
            "'class >= threshold'; a set with a hole in it cannot be expressed that way, "
            "and silently taking the minimum would flag classes the criteria excluded.")
    return cls[0]


def channel_min_class(crit: "Criteria" = CRIT) -> int:
    """Lowest hazard class counted as "in the running channel".  ASSUMP-HAZ-3.

    Read from ``criteria.HAZARD_CHANNEL_MIN_CLASS``.  H3 is the shallowest class whose
    trigger is unambiguously depth (d > 0.5 m in the client's own rasscript) and the class
    at which a vehicle can no longer stand in the flow -- the practical edge of the running
    channel.  PROJECT ASSUMPTION: the guidelines define no channel edge.
    """
    return int(crit.HAZARD_CHANNEL_MIN_CLASS)

#: Default cap on the outward search for dry ground, metres.
#: MEASURED 2026-09-03 on the 50-year grid inside the 531.4 km2 boundary: 1,032,498
#: east-west wet runs, median width 30 m, p90 171 m, p95 294 m, p99 834 m, max 8,544 m.
#: A point at mid-channel needs a search of half the run width, so 500 m resolves any
#: run up to 1,000 m wide — about 99 % of them.  The cap is NEVER returned as an answer:
#: an unresolved search returns ``found=False`` and ``distance_m=None``.
DEFAULT_MAX_SEARCH_M = 500.0


# =====================================================================================
# 3.  WHICH RETURN PERIOD GOVERNS WHICH DECISION
# =====================================================================================

@dataclass(frozen=True)
class Duty:
    """A design decision, the return period(s) that govern it, and the authority."""

    decision: str
    return_periods: Tuple[int, ...]
    #: "GUIDELINE" = the return period is written in a PAM guideline, cited below.
    #: "ASSUMPTION" = the guideline is silent; this is our choice and must be flagged.
    status: str
    citation: str
    quote: str
    note: str = ""

    @property
    def is_assumption(self) -> bool:
        return self.status == "ASSUMPTION"


_DUTIES: Dict[str, Duty] = {
    "wadi_crossing": Duty(
        decision="wadi_crossing",
        return_periods=(25, 50, 100),
        status="GUIDELINE",
        citation="G201-p85 §9.3 Wadi crossings",
        quote="flood frequency analysis (1-in-20 year, 1-in-50 year, 1-in-100 year, "
              "etc... floods)",
        note="SUBST-HAZ-1: the guideline asks 1-in-20 and we hold no 20-year grid, so "
             "25-year is substituted.  Conservative — the 25-year extent contains the "
             "20-year extent.  25-year is itself a guideline period (G203-p63 Tab 27 i). "
             "Same clause: DI pipe over the crossing plus 15 m each side; wadi protection "
             "to PAM-STD-404; minimum cover 2 m in soft soil; and (G201-p86) no valve "
             "chambers or marker posts in the wadi bed or on its embankments.",
    ),
    "pumping_station": Duty(
        decision="pumping_station",
        return_periods=(50,),
        status="GUIDELINE",
        citation="G203-p38 §7.2 Site Selection & Layout",
        quote="Pump pedestal level or building floor, electrical transformers/ pad "
              "mounted substation or emergency generator are to be located above maximum "
              "flood level, with the floors being a minimum of 300 mm above the 1:50 year "
              "flood level.",
        note="Freeboard 300 mm above the 1:50 LEVEL.  We hold a hazard CLASS grid and no "
             "water level, so the level test cannot be evaluated — see "
             "flood_level_m_aod() and NWS_REQUESTS['flood_levels'].  What this module CAN "
             "answer is the siting question: is the station footprint wet at 50-year, and "
             "how far is dry ground.  Mirrored for water at G202-p78 and G202-p79 ('shall "
             "not be liable to flooding during a 1 in 50 year ARI').",
    ),
    "station_stormwater": Duty(
        decision="station_stormwater",
        return_periods=(50,),
        status="GUIDELINE",
        citation="G203-p38 §7.2",
        quote="properly design the surface/stormwater management considering the 1:50 ARI",
        note="Site drainage design storm, distinct from the floor-level test above.",
    ),
    "stp_site": Duty(
        decision="stp_site",
        return_periods=(25, 100),
        status="GUIDELINE",
        citation="G203-p63 Table 27 Site Selection Requirements, row (i)",
        quote="Flood considerations (25 and 100 year flood levels, compliance when "
              "constructing in flood prone areas) / STPs shall be fully operational "
              "during floods (existing and future sites)",
        note="Both periods apply, and the operability duty ('fully operational during "
             "floods') binds access roads and power as well as the works.",
    ),
    "pipe_washout": Duty(
        decision="pipe_washout",
        # DEFECT 4: this was a literal 50 beside `criteria.HAZARD_RETURN_YR = 50`.  One
        # declaration now, and it is criteria's -- so a sensitivity run at another return
        # period cannot move one of the two and leave the other behind.
        return_periods=(int(CRIT.HAZARD_RETURN_YR),),
        status="ASSUMPTION",
        citation="G203-p30 §4.4.1(i)(a); repeated G203-p33 and G203-p36",
        quote="Wadis and Flood-Prone Areas: Locating pipelines and associated chambers "
              "in wadis or areas subject to washout during heavy storms must be avoided.",
        note="ASSUMP-HAZ-1.  The guideline names NO return period and NO threshold for "
             "'washout during heavy storms'.  We adopt 50-year because it is the period "
             "the same guideline set uses for every other flood duty on buried and "
             "surface infrastructure (G203-p38, G202-p78/79) and it sits mid-range of the "
             "wadi-crossing triplet.  Combined with ASSUMP-HAZ-2 (hazard class as a "
             "washout proxy) and ASSUMP-HAZ-4, the scour class threshold, which is "
             "criteria.HAZARD_WADI_CLASSES and is currently H4 and worse.",
    ),
    "sensitivity_low": Duty(
        decision="sensitivity_low",
        return_periods=(10,),
        status="ASSUMPTION",
        citation="no guideline names a 10-year event",
        quote="",
        note="ASSUMP-HAZ-5.  The 10-year grid carries no design duty.  We use it only as "
             "the 'wets often' indicator — a corridor wet at 10-year is an active channel "
             "and should not be crossed at grade or used for a corridor at all.  Never "
             "quote it as compliance.",
    ),
    "sensitivity_high": Duty(
        decision="sensitivity_high",
        return_periods=(500,),
        status="ASSUMPTION",
        citation="no guideline names a 500-year event",
        quote="",
        note="ASSUMP-HAZ-6.  The 500-year grid carries no design duty.  We use it only as "
             "the upper-bound sensitivity case — how much worse does the answer get if "
             "the hydrology is understated.  Never quote it as compliance.",
    ),
}


def governing(decision: str) -> Duty:
    """Return the ``Duty`` — return periods plus citation — for a named decision.

    Raises ``KeyError`` with the full menu rather than guessing.
    """
    try:
        return _DUTIES[decision]
    except KeyError:
        raise KeyError(
            f"No hazard duty registered for {decision!r}.  Registered: "
            + ", ".join(sorted(_DUTIES))
        ) from None


def duties() -> Dict[str, Duty]:
    """The whole registry, for reports and audit tables."""
    return dict(_DUTIES)


# =====================================================================================
# 4.  PROVENANCE — the flags that must appear on every output built from this module
# =====================================================================================

#: Short tags for stamping onto shapefile/GeoPackage attribute tables (10-char safe).
FLAG_FIELDS = {
    "HAZ_RP": "return period of the governing grid, years",
    "HAZ_CLS": "AR&R hazard class 1-6 at the point, 0 = dry (no data)",
    "HAZ_ND": "no-data rule in force: DRY (engineer 2026-09-03)",
    "HAZ_ASM": "semicolon list of project assumptions applied",
    "DRY_THR": "class threshold the dry search was run against (target is below it)",
    "DRY_TCLS": "hazard class of the cell the dry search landed on; 0 = no model result",
    "DRY_TND": "1 where that target cell carries no model result (see LIMIT-HAZ-3)",
}

HAZARD_FLAGS: Tuple[str, ...] = (
    "NO-DATA IS DRY HIGH GROUND.  Engineer's ruling 2026-09-03.  A -9999 cell was not "
    "inundated in that event; it is not 'untested'.  Verified: wet extent grows "
    "monotonically with return period and is nested to within 0.09 %.",
    "ASSUMP-HAZ-1  The 50-year grid is used for the pipe/chamber washout prohibition.  "
    "G203-p30 §4.4.1 attaches no return period to 'washout during heavy storms'.",
    "ASSUMP-HAZ-2  These are AR&R flood-HAZARD classes, keyed on danger to people and "
    "vehicles.  Using them as a proxy for the guideline's washout / SCOUR criterion is a "
    "PROJECT ASSUMPTION, not a guideline test.",
    "ASSUMP-HAZ-3  'In a channel' = hazard class H3 or worse (d > 0.5 m).",
    "ASSUMP-HAZ-4  'Scour risk' / 'wadi ground' = the classes in "
    "criteria.HAZARD_WADI_CLASSES, currently H4 and worse.  THE VALUE IS DECLARED IN "
    "w12.criteria AND NOWHERE ELSE; the banner prints the one in force.  Until "
    "2026-09-03 this module carried its own H5 and disagreed with the project register "
    "by 4.25 km on the client's Main Pipe.  The H5 case (H5 is the first class admitting "
    "v > 2 m/s) is still the best argument available if NWS answer the scour question "
    "with a velocity - it is recorded, not applied.",
    "ASSUMP-HAZ-5  The 10-year grid carries no guideline duty; indicative only.",
    "ASSUMP-HAZ-6  The 500-year grid carries no guideline duty; sensitivity only.",
    "SUBST-HAZ-1   G201-p85 asks for a 1-in-20 year flood at wadi crossings.  No 20-year "
    "grid exists; the 25-year grid is substituted.  Conservative.",
    "LIMIT-HAZ-1   No flood LEVEL (m aOD) can be produced from these grids.  The "
    "300 mm-above-1:50 freeboard of G203-p38 §7.2 CANNOT be checked until NWS supply a "
    "water-surface grid.",
    "LIMIT-HAZ-2   The 100-year grid is 2 m on its own origin; the other four are 3 m on "
    "a shared origin.  Point sampling across return periods is safe; cell-by-cell raster "
    "algebra mixing T100y with the others is not.",
    "LIMIT-HAZ-3   THERE IS NO CLASS-0 CELL IN THESE GRIDS.  Censused over 822 million "
    "cells: only -9999 and the integers 1-6.  'Dry' and 'no model result' are the same "
    "set of cells, so distance_to_dry() at its default threshold always measures to the "
    "nearest UNMODELLED cell.  Every DryGround now carries target_class and "
    "target_is_nodata; ask dry_below_class=<channel class> for the bank instead.",
    "LENGTH-HAZ-1  A hazard length along a line is CELL-WISE.  channel_length_m and "
    "scour_length_m sum the samples that are in a channel / at scour risk.  The "
    "run_span_* properties are the width of the wet RUNS that merely TOUCH such a cell "
    "and are an upper bound, measured 2.28x on the client's Main Pipe.",
)

#: What NWS must supply before the flagged limits can be closed.
NWS_REQUESTS: Dict[str, str] = {
    "flood_levels": (
        "Water-surface elevation grids (m aOD) for the 1:50 event, to evaluate the "
        "300 mm freeboard of PAM-GUD-203 p38 §7.2 at each pumping station and at the "
        "STP.  A hazard-class grid cannot answer it."
    ),
    "scour_criterion": (
        "The threshold NWS intend by 'areas subject to washout during heavy storms' "
        "(PAM-GUD-203 p30 §4.4.1) — a velocity, a bed shear, or a mapped wadi corridor.  "
        "Until then ASSUMP-HAZ-2 and -4 stand."
    ),
    "twenty_year": (
        "A 1-in-20 year hazard or depth grid, as PAM-GUD-201 p85 §9.3 requires for wadi "
        "crossings.  We substitute the 25-year grid (SUBST-HAZ-1)."
    ),
}

#: The check that turned the engineer's ruling from an assertion into a measurement.
#: Study area = Hydraulic/SHP/Study area/Project Boundary.shp, 531.4 km2, EPSG:32640.
#: Native-resolution census, 2026-09-03.  no-data share falls monotonically as the event
#: grows, and the wet extents nest.  If -9999 meant "not modelled" neither would hold.
EVIDENCE_NODATA_IS_DRY: Dict[str, object] = {
    "study_area_km2": 531.4,
    "nodata_share_pct": {10: 67.40, 25: 59.82, 50: 54.21, 100: 49.15, 500: 41.03},
    "wet_share_pct": {10: 32.60, 25: 40.18, 50: 45.79, 100: 50.85, 500: 58.97},
    "wet_km2": {10: 173.2, 25: 213.5, 50: 243.3, 100: 270.2, 500: 313.4},
    "nesting_violation_pct": {"10>25": 0.093, "25>50": 0.049, "50>500": 0.027},
    "note": "T100y is a 2 m grid on a different origin, so its share is comparable in "
            "trend but not cell-for-cell with the 3 m grids.",
}

#: WHY ``distance_to_dry`` HAS TO FLAG ITS TARGET.  Full native-resolution census of the
#: raw cell values over the 531.4 km2 study-area bounding box, all five grids, 2026-09-03:
#: 822,313,384 cells, and the ONLY values present are -9999 and the integers 1 to 6.
#: There is no class-0 cell anywhere.  ``_to_classes`` maps no-data to 0, so "class 0",
#: "dry" and "no model result" are one and the same set of cells, and a search for ground
#: below class 1 can land nowhere but a no-data cell.  Measured consequence before the
#: fix: on 78 in-channel points along the client's Main Pipe at the 50-year event, 100 %
#: of the targets ``distance_to_dry`` returned were no-data cells, at a median 25.4 m —
#: reported as plain "nearest cell below class 1" with nothing to say so.
EVIDENCE_NO_CLASS_ZERO: Dict[str, object] = {
    "cells_censused": 822_313_384,
    "window": "bounding box of Hydraulic/SHP/Study area/Project Boundary.shp, 531.4 km2",
    "raw_values_present": [-9999.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "class_zero_cells": 0,
    "non_integer_cells": 0,
    "by_grid_cells": {10: 131_573_019, 25: 131_573_019, 50: 131_573_019,
                      100: 296_021_308, 500: 131_573_019},
    "probe": "78 in-channel points on SHP/Main Pipe at rp=50: 78/78 dry targets were "
             "no-data, median distance 25.4 m, range 2.2-117.2 m",
    "consequence": "at dry_below_class=None the answer is 'nearest cell the model did not "
                   "report'.  Legitimate under the no-data-is-dry ruling, but it is not "
                   "'nearest surveyed dry ground', and DryGround now says which it is.",
}

#: Class census over the same 531.4 km2, native resolution, share of total area (%).
CLASS_CENSUS_PCT: Dict[int, Dict[int, float]] = {
    10:  {1: 21.901, 2: 3.619, 3: 2.580, 4: 1.466, 5: 2.825, 6: 0.209},
    25:  {1: 24.253, 2: 5.218, 3: 3.554, 4: 1.896, 5: 4.410, 6: 0.853},
    50:  {1: 24.672, 2: 6.561, 3: 4.629, 4: 2.389, 5: 5.792, 6: 1.745},
    100: {1: 23.987, 2: 7.666, 3: 5.752, 4: 3.066, 5: 7.476, 6: 2.905},
    500: {1: 20.970, 2: 9.177, 3: 7.454, 4: 4.510, 5: 10.343, 6: 6.520},
}


# =====================================================================================
# 5.  RESULT TYPES
# =====================================================================================

class HazardError(RuntimeError):
    """Base for every fault this module raises."""


class HazardDataError(HazardError):
    """The grid did not read back as a clean class field."""


class HazardDataUnavailable(HazardError):
    """A question that the data we hold cannot answer.  Raised, never fudged."""


@dataclass(frozen=True)
class HazardSample:
    """What one point looks like at one return period."""

    x: float
    y: float
    return_period: int
    hazard_class: int          # 0 = dry (no data), else 1..6
    in_extent: bool            # False = outside the raster footprint entirely

    # -- derived, all keyed to the thresholds this HazardGrids was built with ----------
    is_wet: bool
    in_channel: bool
    scour_risk: bool

    # -- what the class does and does not say about depth ------------------------------
    depth_lo_m: float
    depth_hi_m: float
    depth_determinate: bool

    label: str
    nodata_rule: str = "DRY (engineer 2026-09-03)"
    assumptions: Tuple[str, ...] = ()

    @property
    def depth_band_text(self) -> str:
        """A depth statement that is honest about what a hazard class can support."""
        if not self.is_wet:
            return "dry"
        hi = "unbounded" if math.isinf(self.depth_hi_m) else f"{self.depth_hi_m:.2f} m"
        band = f"{self.depth_lo_m:.2f}-{hi}"
        if self.depth_determinate:
            return f"{band} (depth-determined class)"
        return f"{band} (INDETERMINATE - class may be driven by velocity, not depth)"

    def as_row(self) -> dict:
        """Flat dict for a schedule or an attribute table."""
        return {
            "X": round(self.x, 3),
            "Y": round(self.y, 3),
            "HAZ_RP": self.return_period,
            "HAZ_CLS": self.hazard_class,
            "HAZ_WET": int(self.is_wet),
            "HAZ_CHAN": int(self.in_channel),
            "HAZ_SCOUR": int(self.scour_risk),
            "HAZ_DLO": None if not self.is_wet else round(self.depth_lo_m, 3),
            "HAZ_DHI": None if (not self.is_wet or math.isinf(self.depth_hi_m))
                       else round(self.depth_hi_m, 3),
            "HAZ_DDET": int(self.depth_determinate) if self.is_wet else None,
            "HAZ_ND": self.nodata_rule,
            "HAZ_ASM": ";".join(self.assumptions),
        }


@dataclass(frozen=True)
class DryGround:
    """The answer to 'how far to dry ground', including the answer 'we did not find it'.

    ``found`` is the only field a caller may branch on.  When it is False,
    ``distance_m`` is None — the search cap is reported separately in ``searched_m`` and
    must never be used as a distance.  This is the failure that produced W11a's
    "800 m wide channel": a cap treated as a measurement.

    AND THE TARGET IS FLAGGED.  ``target_class`` is the hazard class of the cell the
    search landed on and ``target_is_nodata`` says whether the model reported anything
    there at all.  DEFECT 2, fixed 2026-09-03: the grids hold NO class-0 cell (measured —
    see ``EVIDENCE_NO_CLASS_ZERO``), so a search for truly dry ground can only ever land
    on a no-data cell, and every answer was silently of the form "the nearest cell the
    model did not report".  Measured on 78 in-channel points along the client's Main Pipe,
    100 % of targets were no-data, at a median 25 m.  Under the engineer's ruling that
    ground IS dry — but a router being told "move 25 m and you are clear" is entitled to
    know that the 25 m ends at the edge of what was modelled, not at surveyed dry ground.
    Pass ``require_modelled=True`` to refuse a no-data target outright.
    """

    found: bool
    distance_m: Optional[float]
    x: Optional[float]
    y: Optional[float]
    bearing_deg: Optional[float]     # 0 = north, clockwise
    searched_m: float
    return_period: int
    start_was_dry: bool
    clipped_by_extent: bool
    reason: str
    #: the class threshold the search was run against: the target is strictly below it
    threshold_class: int = 1
    #: hazard class of the cell the search landed on; 0 means no modelled inundation
    target_class: Optional[int] = None
    #: True when that cell carries no model result.  With ``threshold_class == 1`` this is
    #: True by construction, because no class-0 cell exists in these grids.
    target_is_nodata: bool = False

    @property
    def target_is_modelled_dry(self) -> bool:
        """The target is ground the model DID report, and reported below the threshold.
        Impossible at ``threshold_class == 1``; the useful case is a bank search, e.g.
        ``dry_below_class=3``, which can land on modelled H1 or H2 ground."""
        return self.found and not self.target_is_nodata and not self.start_was_dry

    def as_row(self) -> dict:
        return {
            "DRY_FOUND": int(self.found),
            "DRY_DIST": None if self.distance_m is None else round(self.distance_m, 2),
            "DRY_X": None if self.x is None else round(self.x, 2),
            "DRY_Y": None if self.y is None else round(self.y, 2),
            "DRY_BRG": None if self.bearing_deg is None else round(self.bearing_deg, 1),
            "DRY_SRCH": round(self.searched_m, 1),
            "DRY_RP": self.return_period,
            "DRY_THR": self.threshold_class,
            "DRY_TCLS": self.target_class,
            "DRY_TND": int(self.target_is_nodata),
            "DRY_WHY": self.reason,
        }


@dataclass(frozen=True)
class Crossing:
    """One continuous WET run along a line.

    ``width_m`` is the run's full span -- every sample in it is wet, which is what makes
    the run a run.  ``channel_m`` and ``scour_m`` are the CELL-WISE lengths INSIDE that
    span, and they are what a schedule or an audit must quote.  ``in_channel`` and
    ``scour_risk`` stay any()-flags, because "does this crossing touch a channel at all"
    is a real yes/no; they are NOT lengths and must never be multiplied by ``width_m``.
    That multiplication was the defect: on the client's Main Pipe it turned 6.77 km of
    scour ground into 15.41 km.
    """

    start_m: float          # chainage at which the line enters the wet ground
    end_m: float            # chainage at which it leaves
    width_m: float          # the whole wet span (every sample in it IS wet)
    max_class: int
    mean_class: float
    in_channel: bool        # any sample at or above the channel threshold
    scour_risk: bool        # any sample at or above the scour threshold
    channel_m: float = 0.0  # CELL-WISE length at or above the channel threshold
    scour_m: float = 0.0    # CELL-WISE length at or above the scour threshold

    @property
    def channel_share(self) -> float:
        """How much of this wet run is actually channel, 0..1.  A crossing at 0.04 is a
        pipe passing the damp margin of a wadi; one at 0.95 is a pipe in the wadi."""
        return self.channel_m / self.width_m if self.width_m > 0 else 0.0


@dataclass
class LineHazard:
    """Hazard along a polyline: the samples, and the wet runs picked out of them.

    LENGTHS ARE CELL-WISE.  Every ``*_length_m`` below is the sum of the line each SAMPLE
    owns, over the samples that satisfy the test.  Each sample owns the half-step to its
    neighbour either side, clamped to the ends of the line, so the owned lengths partition
    the line exactly and ``wet_length_m + dry_length_m == length_m`` to floating point.

    THE RUN-ENVELOPE FIGURES ARE STILL HERE, under names that say what they are:
    ``run_span_channel_m`` and ``run_span_scour_m`` are the total width of the wet RUNS
    that touch a channel / a scour class.  They answer "how wide is the wet ground this
    pipe is inside", which is what a crossing detail has to span.  They are an UPPER BOUND
    on the affected pipe length and they are never the affected pipe length.  Until
    2026-09-03 they were what ``channel_length_m`` and ``scour_length_m`` returned: on the
    client's Main Pipe at 50 year that reported 25.67 km of channel against a true 16.26
    km, and 15.41 km of scour against a true 6.77 km -- 2.28x.
    """

    return_period: int
    step_m: float
    chainage_m: np.ndarray
    hazard_class: np.ndarray            # int8, 0 = dry
    crossings: List[Crossing] = field(default_factory=list)
    #: True length of the polyline.  Sampling is uniform at ``step_m`` and the last
    #: sample sits at or before the end, so lengths are derived from the crossings
    #: (which are clamped to this) and never from a sample count times the step -- that
    #: overstates a short segment by up to one step, which showed as "101 % wet".
    total_length_m: float = 0.0
    #: which class thresholds produced ``in_channel`` / ``scour_risk``.  Stamped so a
    #: length read off this object in six months can be traced to the threshold that made
    #: it -- the thresholds themselves are declared in ``w12.criteria``, not here.
    channel_class: int = 0
    scour_class: int = 0

    # -- cell-wise machinery ------------------------------------------------------------

    def owned_length_m(self) -> np.ndarray:
        """Metres of line each sample stands for.  Midpoint rule, clamped to the ends.

        Sums EXACTLY to ``length_m``, which the self-test asserts.  THIS IS THE ONE PLACE
        a "length along the line" is defined; every length property below is a masked sum
        of it, so a new test cannot reintroduce the one-cell-paints-the-run bug.
        """
        ch = np.asarray(self.chainage_m, dtype=np.float64)
        n = ch.size
        if n == 0:
            return np.zeros(0)
        total = float(self.total_length_m)
        if n == 1:
            return np.array([total])
        mid = 0.5 * (ch[:-1] + ch[1:])
        edges = np.empty(n + 1)
        edges[0] = 0.0
        edges[1:-1] = mid
        edges[-1] = total
        return np.clip(np.diff(edges), 0.0, None)

    def _len_where(self, mask: np.ndarray) -> float:
        if mask.size == 0:
            return 0.0
        return float(self.owned_length_m()[mask].sum())

    @property
    def length_m(self) -> float:
        return float(self.total_length_m)

    @property
    def wet_length_m(self) -> float:
        """CELL-WISE length of line on wet ground (class >= 1)."""
        return self._len_where(np.asarray(self.hazard_class) > 0)

    @property
    def dry_length_m(self) -> float:
        """CELL-WISE length on ground with no modelled inundation.  Under the engineer's
        ruling that is DRY HIGH GROUND, not "untested"."""
        return self._len_where(np.asarray(self.hazard_class) == 0)

    @property
    def channel_length_m(self) -> float:
        """CELL-WISE length of line in the running channel (class >= channel_class)."""
        return self._len_where(np.asarray(self.hazard_class) >= self.channel_class)

    @property
    def scour_length_m(self) -> float:
        """CELL-WISE length of line on scour / washout ground (class >= scour_class).

        This is the number that answers the washout prohibition for a pipe: how much of
        it lies where the guideline says a pipe must not be."""
        return self._len_where(np.asarray(self.hazard_class) >= self.scour_class)

    def class_length_m(self) -> Dict[int, float]:
        """CELL-WISE metres per hazard class, 0..6.  Sums to ``length_m``."""
        cls = np.asarray(self.hazard_class)
        own = self.owned_length_m()
        return {c: float(own[cls == c].sum()) for c in range(0, 7)
                if bool((cls == c).any())}

    # -- run-envelope figures, honestly named -------------------------------------------

    @property
    def run_span_wet_m(self) -> float:
        """Total width of the wet runs.  Equals ``wet_length_m`` to within the endpoint
        sample; kept so the two can be compared rather than confused."""
        return float(sum(c.width_m for c in self.crossings))

    @property
    def run_span_channel_m(self) -> float:
        """Total width of the wet runs that TOUCH a channel cell.  An UPPER BOUND on
        ``channel_length_m``, and the width of wet ground a crossing detail has to span --
        not a length of pipe in a channel."""
        return float(sum(c.width_m for c in self.crossings if c.in_channel))

    @property
    def run_span_scour_m(self) -> float:
        """Total width of the wet runs that TOUCH a scour cell.  An UPPER BOUND on
        ``scour_length_m``.  NEVER report this as a length of pipe at risk of washout."""
        return float(sum(c.width_m for c in self.crossings if c.scour_risk))

    @property
    def inflation_factor(self) -> float:
        """``run_span_scour_m / scour_length_m`` -- the size of the defect this class was
        rewritten to remove.  1.0 means every wet run touching scour ground is scour
        ground throughout.  Measured 2.28 on the client's Main Pipe at 50 year."""
        s = self.scour_length_m
        return self.run_span_scour_m / s if s > 0 else 1.0

    @property
    def runs_along_channel(self) -> bool:
        """True where the line does not merely CROSS a channel but runs down one.

        The distinction G203-p30 §4.4.1 draws is between a pipe located IN a wadi and a
        pipe passing over one.  The test is on the run's CELL-WISE channel length, not on
        its wet width: a 300 m wet run holding 12 m of channel is a pipe crossing the damp
        margin of a wadi, and calling that "running along a channel" is the same
        one-cell-paints-the-run error in boolean form.  ASSUMP-HAZ-7, threshold below.

        MEASURED on the client's 85.5 km Main Pipe at 50 year: the old wet-width test
        found 42 along-channel runs on 32 of the 54 features; the cell-wise test finds 23
        runs on 22 features.  19 of the 42 were a pipe crossing a wide wet margin that
        holds under 200 m of channel.
        """
        return any(c.channel_m > ALONG_CHANNEL_M for c in self.crossings)


#: ASSUMP-HAZ-7.  A wet run longer than this along a pipe is treated as the pipe running
#: ALONG the channel rather than crossing it.  MEASURED basis: the median east-west wet
#: run on the 50-year grid inside the study boundary is 30 m and p90 is 171 m, so a
#: crossing longer than 200 m is at the 91st percentile of channel widths and is far more
#: likely to be a pipe in the wadi than a pipe over it.  PROJECT ASSUMPTION: the
#: guideline draws the distinction but sets no length.
ALONG_CHANNEL_M = 200.0


# =====================================================================================
# 6.  THE GRIDS
# =====================================================================================

class HazardGrids:
    """Sampler over the five flood-hazard grids.

    Files are opened lazily and kept open; use as a context manager, or call ``close()``.
    Every read is native-resolution — see the module docstring, point 3.
    """

    def __init__(
        self,
        hazard_dir: Optional[os.PathLike] = None,
        crit: "Criteria" = CRIT,
        channel_class: Optional[int] = None,
        scour_class: Optional[int] = None,
        nodata_is_dry: Optional[bool] = None,
    ) -> None:
        """All three thresholds default to ``w12.criteria``, which is where they are
        declared.  Pass ``crit=replace(DEFAULT, HAZARD_WADI_CLASSES=(5, 6))`` for a
        sensitivity run; the explicit ``channel_class`` / ``scour_class`` arguments are a
        deliberate local override and are recorded as such in ``provenance()``."""
        self.hazard_dir = Path(hazard_dir) if hazard_dir else _find_hazard_dir()
        self.crit = crit
        self.threshold_source = "w12.criteria"
        if channel_class is None:
            channel_class = channel_min_class(crit)
        else:
            self.threshold_source = "caller override"
        if scour_class is None:
            scour_class = scour_min_class(crit)
        else:
            self.threshold_source = "caller override"
        if not 1 <= channel_class <= 6:
            raise ValueError("channel_class must be 1..6")
        if not 1 <= scour_class <= 6:
            raise ValueError("scour_class must be 1..6")
        if scour_class < channel_class:
            raise ValueError("scour_class must not be below channel_class")
        self.channel_class = int(channel_class)
        self.scour_class = int(scour_class)
        if nodata_is_dry is None:
            nodata_is_dry = bool(crit.HAZARD_NODATA_IS_DRY)
        if not nodata_is_dry:
            raise ValueError(
                "nodata_is_dry=False is not implemented.  The engineer settled this on "
                "2026-09-03: no data means dry high ground.  If that is ever reversed, "
                "the reversal belongs in the philosophy document first, then in "
                "criteria.HAZARD_NODATA_IS_DRY, and every output must be re-flagged."
            )
        self.nodata_is_dry = True
        self._src: Dict[int, "rasterio.DatasetReader"] = {}

    # -- lifecycle --------------------------------------------------------------------

    def __enter__(self) -> "HazardGrids":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        for s in self._src.values():
            try:
                s.close()
            except Exception:
                pass
        self._src.clear()

    def src(self, rp: int):
        """The open dataset for a return period, opening it on first use."""
        rp = self._check_rp(rp)
        if rp not in self._src:
            path = self.hazard_dir / GRID_FILES[rp]
            if not path.is_file():
                raise FileNotFoundError(f"hazard grid missing: {path}")
            s = rasterio.open(path)
            if s.crs is None or s.crs.to_string() != CRS:
                raise HazardDataError(
                    f"{path.name} is in {s.crs}, expected {CRS}.  Every W12 coordinate "
                    f"is EPSG:32640; this module does not reproject."
                )
            self._src[rp] = s
        return self._src[rp]

    @staticmethod
    def _check_rp(rp: int) -> int:
        rp = int(rp)
        if rp not in GRID_FILES:
            raise ValueError(
                f"no {rp}-year hazard grid.  We hold {RETURN_PERIODS}.  "
                f"For the guideline's 1-in-20 at wadi crossings see SUBST-HAZ-1: use 25."
            )
        return rp

    # -- the guard against the averaged-overview trap ---------------------------------

    @staticmethod
    def _to_classes(a: np.ndarray, where: str) -> np.ndarray:
        """Turn a raw float32 block into int8 classes, 0 for dry.

        Raises if anything arrives that is neither the no-data value nor an exact class.
        That is the trip-wire for a decimated / warped / resampled read: the shipped
        GeoTIFFs carry AVERAGE-built overviews, so any such read returns fractional
        classes like 1.0046296 and every ``== 5`` test in the pipeline silently fails.
        """
        out = np.zeros(a.shape, dtype=np.int8)
        wet = np.isfinite(a) & (a > 0.0)
        if not wet.any():
            return out
        vals = a[wet]
        rounded = np.rint(vals)
        bad = ~np.isclose(vals, rounded, atol=1e-6) | (rounded < 1) | (rounded > 6)
        if bad.any():
            sample = np.unique(vals[bad])[:5]
            raise HazardDataError(
                f"{where}: the grid returned non-integer hazard classes {sample}.  These "
                f"rasters carry AVERAGE-built overviews, so a decimated or resampled read "
                f"averages neighbouring classes.  Read at native resolution — do not pass "
                f"out_shape, and do not sample through a WarpedVRT."
            )
        out[wet] = rounded.astype(np.int8)
        return out

    # -- point sampling ---------------------------------------------------------------

    def sample_many(self, xs, ys, rp: int = 50) -> np.ndarray:
        """Hazard class at each (x, y).  Returns int8; 0 means dry (no data or outside).

        Points outside the raster footprint come back as 0 — dry — consistent with the
        no-data rule; use ``in_extent_many`` if you need to tell the two apart.
        Reads are batched by 512x512 tile so a long list costs one read per tile touched,
        not one read per point.
        """
        rp = self._check_rp(rp)
        s = self.src(rp)
        xs = np.asarray(xs, dtype=np.float64).ravel()
        ys = np.asarray(ys, dtype=np.float64).ravel()
        if xs.size != ys.size:
            raise ValueError("xs and ys must be the same length")
        out = np.zeros(xs.size, dtype=np.int8)
        if xs.size == 0:
            return out

        rows, cols = self._rowcol(s, xs, ys)
        inside = ((rows >= 0) & (rows < s.height) & (cols >= 0) & (cols < s.width))
        if not inside.any():
            return out

        TILE = 512
        tr = rows[inside] // TILE
        tc = cols[inside] // TILE
        idx = np.flatnonzero(inside)
        key = tr.astype(np.int64) * 1_000_000 + tc.astype(np.int64)
        order = np.argsort(key, kind="stable")
        key_s = key[order]
        bounds = np.flatnonzero(np.diff(key_s)) + 1
        for grp in np.split(order, bounds):
            r0 = int(tr[grp[0]]) * TILE
            c0 = int(tc[grp[0]]) * TILE
            h = min(TILE, s.height - r0)
            w = min(TILE, s.width - c0)
            block = s.read(1, window=Window(c0, r0, w, h))
            cl = self._to_classes(block, f"{GRID_FILES[rp]} tile r{r0} c{c0}")
            gi = idx[grp]
            out[gi] = cl[rows[gi] - r0, cols[gi] - c0]
        return out

    def in_extent_many(self, xs, ys, rp: int = 50) -> np.ndarray:
        """Boolean: is each point inside the raster footprint at all."""
        rp = self._check_rp(rp)
        s = self.src(rp)
        xs = np.asarray(xs, dtype=np.float64).ravel()
        ys = np.asarray(ys, dtype=np.float64).ravel()
        rows, cols = self._rowcol(s, xs, ys)
        return (rows >= 0) & (rows < s.height) & (cols >= 0) & (cols < s.width)

    @staticmethod
    def _rowcol(s, xs: np.ndarray, ys: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Vectorised world -> (row, col), floor-rounded, for a north-up grid."""
        t = s.transform
        if t.b != 0 or t.d != 0:  # pragma: no cover - shipped grids are north-up
            raise HazardDataError("rotated grid; _rowcol assumes north-up")
        cols = np.floor((xs - t.c) / t.a).astype(np.int64)
        rows = np.floor((ys - t.f) / t.e).astype(np.int64)
        return rows, cols

    def sample(self, x: float, y: float, rp: int = 50) -> HazardSample:
        """Full answer for one point at one return period."""
        rp = self._check_rp(rp)
        cls = int(self.sample_many([x], [y], rp=rp)[0])
        in_ext = bool(self.in_extent_many([x], [y], rp=rp)[0])
        return self._build_sample(x, y, rp, cls, in_ext)

    def _build_sample(self, x, y, rp, cls, in_ext) -> HazardSample:
        wet = cls > 0
        if wet:
            hc = HAZARD_CLASSES[cls]
            lo, hi, det, label = hc.depth_lo_m, hc.depth_hi_m, hc.depth_determinate, hc.label
        else:
            lo = hi = 0.0
            det = True
            label = ("dry - no modelled inundation at this return period "
                     "(no data = DRY, engineer 2026-09-03)")
        asm = ["ASSUMP-HAZ-2"]
        if cls >= self.channel_class:
            asm.append("ASSUMP-HAZ-3")
        if cls >= self.scour_class:
            asm.append("ASSUMP-HAZ-4")
        if rp == 25:
            asm.append("SUBST-HAZ-1")
        if rp in (10, 500):
            asm.append("ASSUMP-HAZ-5" if rp == 10 else "ASSUMP-HAZ-6")
        return HazardSample(
            x=float(x), y=float(y), return_period=rp,
            hazard_class=cls, in_extent=in_ext,
            is_wet=wet,
            in_channel=cls >= self.channel_class,
            scour_risk=cls >= self.scour_class,
            depth_lo_m=lo, depth_hi_m=hi, depth_determinate=det,
            label=label, assumptions=tuple(asm),
        )

    def sample_all(self, x: float, y: float) -> Dict[int, HazardSample]:
        """The point at every return period we hold."""
        return {rp: self.sample(x, y, rp=rp) for rp in RETURN_PERIODS}

    def first_wet_rp(self, x: float, y: float) -> Optional[int]:
        """Smallest return period at which the point is wet; None if dry even at 500.

        This is the 'at what return period' half of the API: a point that first wets at
        10 years is in an active channel; one that first wets at 500 is high ground with
        a tail risk.
        """
        for rp in RETURN_PERIODS:
            if int(self.sample_many([x], [y], rp=rp)[0]) > 0:
                return rp
        return None

    def first_channel_rp(self, x: float, y: float) -> Optional[int]:
        """Smallest return period at which the point is in a CHANNEL (ASSUMP-HAZ-3)."""
        for rp in RETURN_PERIODS:
            if int(self.sample_many([x], [y], rp=rp)[0]) >= self.channel_class:
                return rp
        return None

    # -- convenience predicates --------------------------------------------------------

    def is_wet(self, x: float, y: float, rp: int = 50) -> bool:
        return int(self.sample_many([x], [y], rp=rp)[0]) > 0

    def in_channel(self, x: float, y: float, rp: int = 50) -> bool:
        return int(self.sample_many([x], [y], rp=rp)[0]) >= self.channel_class

    def scour_risk(self, x: float, y: float, rp: int = 50) -> bool:
        return int(self.sample_many([x], [y], rp=rp)[0]) >= self.scour_class

    # -- distance to dry ground --------------------------------------------------------

    def distance_to_dry(
        self,
        x: float,
        y: float,
        rp: int = 50,
        max_search_m: float = DEFAULT_MAX_SEARCH_M,
        dry_below_class: Optional[int] = None,
        require_modelled: bool = False,
    ) -> DryGround:
        """Straight-line distance from (x, y) to the nearest ground below a hazard class.

        ``dry_below_class`` sets the threshold.  Default None means class 1 — "no
        modelled inundation at all".

        READ THIS BEFORE USING THE DEFAULT.  These grids contain NO class-0 cell: every
        cell is -9999 or an integer 1..6 (measured, ``EVIDENCE_NO_CLASS_ZERO``).  So at
        the default threshold "dry" and "no data" are the SAME set of cells, and the
        answer is always "the nearest cell the model did not report".  Under the
        engineer's ruling of 2026-09-03 that ground IS dry, so the answer is legitimate —
        but it is not the same statement as "surveyed dry ground", and until 2026-09-03
        nothing in the result said which it was.  Two ways to be honest about it:

          * ``dry_below_class=self.channel_class`` asks for the nearest ground OUTSIDE
            the running channel — the bank.  That can and usually does land on modelled
            H1/H2 ground, and it is what a router actually wants.
          * ``require_modelled=True`` refuses a no-data target: if the only qualifying
            cells carry no model result, it returns ``found=False`` with a reason saying
            so, rather than a distance to the edge of the modelled domain.

        Either way ``target_class`` and ``target_is_nodata`` are set on every answer.

        Contract, and it is the point of this function:
          * if nothing is found inside ``max_search_m``, ``found`` is False and
            ``distance_m`` is None.  THE CAP IS NEVER RETURNED AS A DISTANCE.
          * a start point that is already below the threshold returns distance 0.0 and
            ``start_was_dry``.
          * where the search box runs off the raster, ``clipped_by_extent`` is set;
            ground outside the footprint counts as dry under the no-data rule, so the
            answer is still valid, but the flag lets a caller decide.
        """
        rp = self._check_rp(rp)
        s = self.src(rp)
        res = float(abs(s.transform.a))
        thresh = 1 if dry_below_class is None else int(dry_below_class)
        if not 1 <= thresh <= 6:
            raise ValueError("dry_below_class must be 1..6")
        if max_search_m <= 0:
            raise ValueError("max_search_m must be positive")
        if thresh == 1 and require_modelled:
            raise ValueError(
                "require_modelled=True with dry_below_class=None (threshold 1) can never "
                "succeed: these grids hold no class-0 cell, so no MODELLED cell is below "
                "class 1.  Ask for a bank instead — dry_below_class=self.channel_class — "
                "or drop require_modelled and read target_is_nodata off the result."
            )

        start = int(self.sample_many([x], [y], rp=rp)[0])
        if start < thresh:
            return DryGround(
                found=True, distance_m=0.0, x=float(x), y=float(y), bearing_deg=None,
                searched_m=0.0, return_period=rp, start_was_dry=True,
                clipped_by_extent=False,
                reason=f"start point is already below class {thresh} (class {start})",
                threshold_class=thresh, target_class=start,
                target_is_nodata=(start == DRY),
            )

        rad = int(math.ceil(max_search_m / res))
        r0c, c0c = self._rowcol(s, np.array([x]), np.array([y]))
        rc, cc = int(r0c[0]), int(c0c[0])
        r_lo, r_hi = rc - rad, rc + rad + 1
        c_lo, c_hi = cc - rad, cc + rad + 1
        clipped = (r_lo < 0 or c_lo < 0 or r_hi > s.height or c_hi > s.width)
        rr0, cc0 = max(r_lo, 0), max(c_lo, 0)
        rr1, cc1 = min(r_hi, s.height), min(c_hi, s.width)
        if rr1 <= rr0 or cc1 <= cc0:  # pragma: no cover
            return DryGround(False, None, None, None, None, float(max_search_m), rp,
                             False, True, "search box falls entirely outside the grid")

        block = s.read(1, window=Window(cc0, rr0, cc1 - cc0, rr1 - rr0))
        cls = self._to_classes(block, f"{GRID_FILES[rp]} dry-search at {x:.0f},{y:.0f}")

        # Cell centres relative to the query point, in metres.
        t = s.transform
        cx = t.c + (np.arange(cc0, cc1) + 0.5) * t.a
        cy = t.f + (np.arange(rr0, rr1) + 0.5) * t.e
        dx = cx[None, :] - x
        dy = cy[:, None] - y
        dist = np.hypot(dx, dy)

        cand = (cls < thresh) & (dist <= max_search_m)
        if require_modelled:
            # Only ground the model actually reported on.  With thresh > 1 this is the
            # H1/H2 shoulder of the channel; the constructor above refuses thresh == 1,
            # where the set is empty by construction.
            cand &= cls > DRY
        if clipped:
            # Ground beyond the footprint is dry under the no-data rule, but we cannot
            # measure a distance to a cell we do not have.  The flag says so; we still
            # answer from what is inside the footprint.
            pass
        if not cand.any():
            why = (f"no cell below class {thresh} within {max_search_m:.0f} m; "
                   f"NOT a measurement of channel width - widen max_search_m or "
                   f"treat as undecided")
            if require_modelled:
                why = (f"no MODELLED cell below class {thresh} within "
                       f"{max_search_m:.0f} m (require_modelled=True; no-data cells were "
                       f"refused).  NOT a measurement of anything - the model reported "
                       f"nothing dry near this point")
            return DryGround(
                found=False, distance_m=None, x=None, y=None, bearing_deg=None,
                searched_m=float(max_search_m), return_period=rp, start_was_dry=False,
                clipped_by_extent=clipped, reason=why,
                threshold_class=thresh, target_class=None, target_is_nodata=False,
            )

        d = np.where(cand, dist, np.inf)
        k = int(np.argmin(d))
        i, j = np.unravel_index(k, d.shape)
        bx, by = float(cx[j]), float(cy[i])
        tcls = int(cls[i, j])
        brg = (math.degrees(math.atan2(bx - x, by - y)) + 360.0) % 360.0
        if tcls == DRY:
            why = (f"nearest cell with NO MODEL RESULT ({max_search_m:.0f} m searched).  "
                   f"Read as dry high ground under the engineer's ruling of 2026-09-03, "
                   f"NOT as surveyed dry ground - these grids hold no class-0 cell, so a "
                   f"search below class {thresh} can land nowhere else.  For the bank of "
                   f"the channel ask dry_below_class={self.channel_class}")
        else:
            why = f"nearest MODELLED cell below class {thresh} (class {tcls})"
        return DryGround(
            found=True, distance_m=float(d[i, j]), x=bx, y=by, bearing_deg=brg,
            searched_m=float(max_search_m), return_period=rp, start_was_dry=False,
            clipped_by_extent=clipped, reason=why,
            threshold_class=thresh, target_class=tcls, target_is_nodata=(tcls == DRY),
        )

    # -- along a line ------------------------------------------------------------------

    def profile(
        self,
        coords: Iterable[Sequence[float]],
        rp: int = 50,
        step_m: Optional[float] = None,
    ) -> LineHazard:
        """Sample hazard along a polyline and pick out the wet runs.

        ``coords`` is any iterable of (x, y), or a shapely geometry with ``.coords``.
        ``step_m`` defaults to the grid's own cell size, so nothing is skipped and
        nothing is over-sampled.
        """
        rp = self._check_rp(rp)
        s = self.src(rp)
        step = float(step_m) if step_m else float(abs(s.transform.a))

        pts, total = self._densify(coords, step)
        if pts.shape[0] == 0:
            return LineHazard(rp, step, np.zeros(0), np.zeros(0, dtype=np.int8), [], 0.0,
                              self.channel_class, self.scour_class)
        cls = self.sample_many(pts[:, 0], pts[:, 1], rp=rp)
        ch = np.minimum(np.arange(pts.shape[0], dtype=np.float64) * step, total)

        lh = LineHazard(rp, step, ch, cls, [], total,
                        self.channel_class, self.scour_class)
        own = lh.owned_length_m()          # the ONE definition of length along the line

        crossings: List[Crossing] = []
        wet = cls > 0
        if wet.any():
            padded = np.concatenate(([False], wet, [False]))
            d = np.diff(padded.astype(np.int8))
            starts = np.flatnonzero(d == 1)
            ends = np.flatnonzero(d == -1)
            for a, b in zip(starts, ends):
                seg = cls[a:b]
                seg_own = own[a:b]
                # Each sample owns the half-step either side of it, clamped to the line,
                # so a run can never be reported longer than the line it sits on.
                s_m = max(0.0, float(ch[a]) - step / 2.0)
                e_m = min(total, float(ch[b - 1]) + step / 2.0)
                crossings.append(Crossing(
                    start_m=s_m,
                    end_m=e_m,
                    width_m=max(0.0, e_m - s_m),
                    max_class=int(seg.max()),
                    mean_class=float(seg.mean()),
                    # any()-flags: does this run TOUCH channel / scour ground at all
                    in_channel=bool((seg >= self.channel_class).any()),
                    scour_risk=bool((seg >= self.scour_class).any()),
                    # and the cell-wise lengths INSIDE the run, which are what a
                    # schedule quotes.  The flag above must never be multiplied by
                    # width_m to get one of these; that was the 2.28x defect.
                    channel_m=float(seg_own[seg >= self.channel_class].sum()),
                    scour_m=float(seg_own[seg >= self.scour_class].sum()),
                ))
        lh.crossings = crossings
        return lh

    @staticmethod
    def _densify(coords, step: float) -> Tuple[np.ndarray, float]:
        """Resample a polyline to points every ``step`` m.  Returns (points, length)."""
        if hasattr(coords, "coords"):
            coords = list(coords.coords)
        pts = np.asarray([(float(p[0]), float(p[1])) for p in coords], dtype=np.float64)
        if pts.shape[0] == 0:
            return pts.reshape(0, 2), 0.0
        if pts.shape[0] == 1:
            return pts, 0.0
        seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
        cum = np.concatenate(([0.0], np.cumsum(seg)))
        total = float(cum[-1])
        if total <= 0:
            return pts[:1], 0.0
        n = int(math.floor(total / step)) + 1
        want = np.arange(n, dtype=np.float64) * step
        # Always sample the true end of the line, so a segment shorter than one step is
        # still represented by both its ends.
        if want[-1] < total - 1e-9:
            want = np.concatenate([want, [total]])
        return np.column_stack([
            np.interp(want, cum, pts[:, 0]),
            np.interp(want, cum, pts[:, 1]),
        ]), total

    # -- the question we cannot answer --------------------------------------------------

    def flood_level_m_aod(self, x: float, y: float, rp: int = 50) -> float:
        """Water-surface level in m aOD.  ALWAYS raises — we do not have it.

        PAM-GUD-203 p38 §7.2 wants a pumping-station floor 300 mm above the 1:50 flood
        LEVEL, and PAM-GUD-201 p85 §9.3 wants flood levels at wadi crossings.  These
        grids carry an AR&R hazard CLASS, so no level can be derived from them without
        inventing a depth and adding it to a terrain reading.  Rather than let that
        happen quietly, this raises.  See ``NWS_REQUESTS['flood_levels']``.
        """
        raise HazardDataUnavailable(
            "No flood LEVEL is derivable from the hazard-class grids (LIMIT-HAZ-1).  "
            "G203-p38 §7.2 needs the 1:50 water-surface level for the 300 mm freeboard; "
            "G201-p85 §9.3 needs levels at wadi crossings.  Request from NWS: "
            + NWS_REQUESTS["flood_levels"]
        )

    #: The freeboard the guideline requires once a level does arrive:
    #: `criteria.PS_FLOOR_ABOVE_FLOOD_M`.  DEFECT 4, fixed 2026-09-03: this class carried
    #: its own `STATION_FREEBOARD_M = 0.300` beside criteria's `PS_FLOOR_ABOVE_FLOOD_M =
    #: 0.30` for the one quantity in G203-p38 §7.2 ("the floors being a minimum of 300 mm
    #: above the 1:50 year flood level"), and `contract.py` already audits against
    #: criteria's.  The copy is removed rather than aliased, so a caller that used it
    #: fails loudly instead of reading a value nobody maintains.
    @property
    def station_freeboard_m(self) -> float:
        """G203-p38 §7.2 freeboard, m.  Read from criteria; declared nowhere here."""
        return float(CRIT.PS_FLOOR_ABOVE_FLOOD_M)

    # -- provenance --------------------------------------------------------------------

    def provenance(self) -> dict:
        """Everything an output must carry to be readable in six months' time."""
        return {
            "module": "w12.hazard",
            "iteration": "W12",
            "date": "2026-09-03",
            "hazard_dir": str(self.hazard_dir),
            "grids": {rp: GRID_FILES[rp] for rp in RETURN_PERIODS},
            "crs": CRS,
            "nodata_rule": "DRY HIGH GROUND (engineer 2026-09-03)",
            "channel_class": self.channel_class,
            "scour_class": self.scour_class,
            "threshold_source": self.threshold_source,
            "criteria_version": getattr(self.crit, "CRITERIA_VERSION", None)
                                or globals().get("CRITERIA_VERSION"),
            "criteria_wadi_classes": tuple(self.crit.HAZARD_WADI_CLASSES),
            "criteria_channel_min_class": int(self.crit.HAZARD_CHANNEL_MIN_CLASS),
            "along_channel_m": ALONG_CHANNEL_M,
            "length_convention": "CELL-WISE; run_span_* are an upper bound (LENGTH-HAZ-1)",
            "flags": list(HAZARD_FLAGS),
            "duties": {k: asdict(v) for k, v in _DUTIES.items()},
            "nws_requests": dict(NWS_REQUESTS),
            "evidence_nodata_is_dry": EVIDENCE_NODATA_IS_DRY,
            "evidence_no_class_zero": EVIDENCE_NO_CLASS_ZERO,
        }

    def banner(self) -> str:
        """The block of text to print at the head of any report or log."""
        lines = ["W12 flood hazard - flags that travel with every number below:"]
        lines += [f"  * {f}" for f in HAZARD_FLAGS]
        lines.append(f"  * thresholds in force: channel = H{self.channel_class}+, "
                     f"scour = H{self.scour_class}+, along-channel = {ALONG_CHANNEL_M:.0f} m")
        lines.append(f"  * thresholds declared in w12.criteria "
                     f"(HAZARD_WADI_CLASSES = {tuple(self.crit.HAZARD_WADI_CLASSES)}, "
                     f"HAZARD_CHANNEL_MIN_CLASS = {int(self.crit.HAZARD_CHANNEL_MIN_CLASS)}); "
                     f"source: {self.threshold_source}")
        # The engineer asked on 2026-09-03 for tau to be flagged on every output. Nothing
        # in THIS module uses tau; the flag rides along so a log that begins with a hazard
        # banner still carries it, and it names criteria as the single source.
        lines.append("  * project-wide design flag (not used by this module): "
                     + self.crit.tau_banner())
        return "\n".join(lines)


def stamp(record: dict, sample: Optional[HazardSample] = None,
          dry: Optional[DryGround] = None) -> dict:
    """Write the hazard fields, and the flags, onto an output record in place."""
    if sample is not None:
        record.update(sample.as_row())
    if dry is not None:
        record.update(dry.as_row())
    record["HAZ_ND"] = "DRY (engineer 2026-09-03)"
    return record


# =====================================================================================
# 7.  SELF-TEST
# =====================================================================================

def self_test(verbose: bool = True) -> bool:
    """Prove the module against the shipped grids.  Returns True on success."""
    ok = True

    def say(msg):
        if verbose:
            print(msg)

    # -- the class table matches the client's own script, re-derived here --------------
    def _cls(d, v):
        return np.where((d > 4) | (v > 4) | (d * v > 4), 6,
               np.where((d > 2) | (v > 2) | (d * v > 1), 5,
               np.where((d > 1.2) | (d * v > 0.6), 4,
               np.where(d > 0.5, 3,
               np.where((d > 0.3) | (d * v > 0.3), 2, 1)))))

    dd = np.arange(0.0, 6.0005, 0.002)
    vv = np.arange(0.0, 6.005, 0.01)
    D, V = np.meshgrid(dd, vv, indexing="ij")
    C = _cls(D, V)
    for c, hc in HAZARD_CLASSES.items():
        m = C == c
        if not m.any():
            continue
        lo, hi = float(D[m].min()), float(D[m].max())
        if lo + 1e-3 < hc.depth_lo_m or (not math.isinf(hc.depth_hi_m)
                                         and hi > hc.depth_hi_m + 1e-6):
            say(f"  FAIL H{c} depth band {lo:.3f}-{hi:.3f} vs table "
                f"{hc.depth_lo_m}-{hc.depth_hi_m}")
            ok = False
    say("  ok  class -> depth bands agree with the client's rasscript")

    with HazardGrids() as hz:
        say(f"  hazard dir: {hz.hazard_dir}")

        # -- geometry -----------------------------------------------------------------
        for rp in RETURN_PERIODS:
            s = hz.src(rp)
            g = GRID_GEOMETRY[rp]
            if (s.width, s.height) != (g["width"], g["height"]):
                say(f"  FAIL {rp}y size {s.width}x{s.height} vs recorded "
                    f"{g['width']}x{g['height']}")
                ok = False
            if abs(abs(s.transform.a) - g["res_m"]) > 1e-6:
                say(f"  FAIL {rp}y res {abs(s.transform.a)} vs {g['res_m']}")
                ok = False
            if s.nodata != NODATA:
                say(f"  FAIL {rp}y nodata {s.nodata} vs {NODATA}")
                ok = False
        say("  ok  all five grids match the recorded geometry, CRS and no-data value")

        # -- integrality guard ---------------------------------------------------------
        s = hz.src(50)
        blk = s.read(1, window=Window(40000, 15000, 512, 512))
        try:
            hz._to_classes(blk, "self-test native")
            say("  ok  native-resolution read returns clean integer classes")
        except HazardDataError as exc:
            say(f"  FAIL native read rejected: {exc}")
            ok = False
        dec = s.read(1, window=Window(40000, 15000, 4096, 4096), out_shape=(256, 256))
        try:
            hz._to_classes(dec, "self-test decimated")
            say("  NOTE decimated read happened to be clean here; the guard is still "
                "required - see module docstring point 3")
        except HazardDataError:
            say("  ok  decimated read is REJECTED by the guard (averaged overviews)")

        # -- known points --------------------------------------------------------------
        probes = [
            ("existing STP (E444422.8 N2563337.9)", 444422.8, 2563337.9),
            ("existing PS  (E449899.6 N2567301.7)", 449899.59, 2567301.72),
            ("trunk in wadi (E450050 N2569400)", 450050.0, 2569400.0),
        ]
        for name, px, py in probes:
            classes = {rp: int(hz.sample_many([px], [py], rp=rp)[0])
                       for rp in RETURN_PERIODS}
            fw = hz.first_wet_rp(px, py)
            d50 = hz.distance_to_dry(px, py, rp=50)
            s50 = hz.sample(px, py, rp=50)
            say(f"  {name}")
            say(f"      class by RP {classes}   first wet: {fw}")
            say(f"      50y: {s50.label}")
            say(f"           depth band {s50.depth_band_text}")
            say(f"      dry ground @50y: found={d50.found} "
                f"dist={d50.distance_m if d50.distance_m is None else round(d50.distance_m,1)} m "
                f"({d50.reason})")

        # -- the cap is never returned as a distance -----------------------------------
        deep = None
        for name, px, py in probes:
            if hz.in_channel(px, py, rp=500):
                deep = (px, py)
                break
        if deep:
            tiny = hz.distance_to_dry(deep[0], deep[1], rp=500, max_search_m=6.0)
            if tiny.found and tiny.distance_m is not None and tiny.distance_m > 6.0:
                say("  FAIL distance_to_dry returned a distance beyond its own cap")
                ok = False
            elif not tiny.found and tiny.distance_m is not None:
                say("  FAIL not-found returned a distance")
                ok = False
            else:
                say(f"  ok  tight search behaves: found={tiny.found} "
                    f"distance={tiny.distance_m}")

        # -- DEFECT 2: the dry target is FLAGGED, and can be refused --------------------
        # These grids hold no class-0 cell, so a search below class 1 always lands on a
        # no-data cell.  Prove the module now says so, and that require_modelled refuses.
        n_probe = n_nd = 0
        for name, px, py in probes:
            if not hz.in_channel(px, py, rp=50):
                continue
            n_probe += 1
            dg = hz.distance_to_dry(px, py, rp=50)
            if dg.found and dg.target_class != DRY:
                say(f"  FAIL {name}: a class-0 cell was found, which cannot exist")
                ok = False
            if dg.found and not dg.target_is_nodata:
                say(f"  FAIL {name}: no-data target not flagged")
                ok = False
            n_nd += int(bool(dg.found and dg.target_is_nodata))
            # asking for the BANK instead must be able to land on modelled ground
            bank = hz.distance_to_dry(px, py, rp=50,
                                      dry_below_class=hz.channel_class,
                                      require_modelled=True)
            say(f"  {name}")
            say(f"      dry(class<1):  found={dg.found} "
                f"dist={None if dg.distance_m is None else round(dg.distance_m, 1)} m  "
                f"target class {dg.target_class} nodata={dg.target_is_nodata}")
            say(f"      bank(class<{hz.channel_class}, modelled only): found={bank.found} "
                f"dist={None if bank.distance_m is None else round(bank.distance_m, 1)} m  "
                f"target class {bank.target_class} nodata={bank.target_is_nodata}")
            if bank.found and bank.target_is_nodata:
                say("  FAIL require_modelled returned a no-data target")
                ok = False
        if n_probe and n_nd != n_probe:
            say(f"  NOTE {n_nd} of {n_probe} in-channel probes landed on no-data")
        else:
            say(f"  ok  every dry-ground answer is flagged as no-data ({n_nd}/{n_probe}), "
                f"which is what EVIDENCE_NO_CLASS_ZERO predicts")
        try:
            hz.distance_to_dry(444422.8, 2563337.9, rp=50, require_modelled=True)
        except ValueError:
            say("  ok  require_modelled at threshold 1 raises instead of never matching")
        else:                                                   # pragma: no cover
            say("  FAIL require_modelled at threshold 1 must raise")
            ok = False

        # -- DEFECT 1: lengths are CELL-WISE, and the partition is exact ----------------
        line = [(448000.0, 2566000.0), (452000.0, 2570000.0)]
        pr = hz.profile(line, rp=50)
        own = pr.owned_length_m()
        if abs(float(own.sum()) - pr.length_m) > 1e-6:
            say(f"  FAIL owned lengths sum to {own.sum():.6f}, line is {pr.length_m:.6f}")
            ok = False
        if abs(pr.wet_length_m + pr.dry_length_m - pr.length_m) > 1e-6:
            say("  FAIL wet + dry != total")
            ok = False
        if abs(sum(pr.class_length_m().values()) - pr.length_m) > 1e-6:
            say("  FAIL class_length_m does not partition the line")
            ok = False
        # every cell-wise length is bounded by its run envelope, and by the one above it
        for a, b, lab in ((pr.scour_length_m, pr.run_span_scour_m, "scour"),
                          (pr.channel_length_m, pr.run_span_channel_m, "channel"),
                          (pr.wet_length_m, pr.run_span_wet_m + 1e-6, "wet")):
            if a > b + 1e-6:
                say(f"  FAIL cell-wise {lab} {a:.1f} exceeds its run envelope {b:.1f}")
                ok = False
        if not (pr.scour_length_m <= pr.channel_length_m <= pr.wet_length_m + 1e-6):
            say("  FAIL the three cell-wise lengths are not nested")
            ok = False
        # per-crossing cell-wise lengths must sum to the line's
        if abs(sum(c.channel_m for c in pr.crossings) - pr.channel_length_m) > 1e-6:
            say("  FAIL per-crossing channel_m does not sum to channel_length_m")
            ok = False
        say(f"  profile {pr.length_m:,.0f} m test line @50y: {len(pr.crossings)} wet runs")
        say(f"      CELL-WISE  wet {pr.wet_length_m:8.0f} m  "
            f"channel {pr.channel_length_m:8.0f} m  scour {pr.scour_length_m:8.0f} m")
        say(f"      RUN SPAN   wet {pr.run_span_wet_m:8.0f} m  "
            f"channel {pr.run_span_channel_m:8.0f} m  scour {pr.run_span_scour_m:8.0f} m"
            f"   (inflation {pr.inflation_factor:.2f}x)")
        say(f"      runs_along_channel={pr.runs_along_channel}  "
            f"classes {pr.class_length_m()}")

        # -- DEFECT 4: this module declares no threshold of its own ---------------------
        for gone in ("DEFAULT_CHANNEL_CLASS", "DEFAULT_SCOUR_CLASS", "STATION_FREEBOARD_M"):
            if gone in globals() or hasattr(HazardGrids, gone):
                say(f"  FAIL {gone} is back; the thresholds live in w12.criteria only")
                ok = False
        if hz.scour_class != min(CRIT.HAZARD_WADI_CLASSES):
            say("  FAIL scour_class does not follow criteria.HAZARD_WADI_CLASSES")
            ok = False
        if hz.channel_class != int(CRIT.HAZARD_CHANNEL_MIN_CLASS):
            say("  FAIL channel_class does not follow criteria.HAZARD_CHANNEL_MIN_CLASS")
            ok = False
        if governing("pipe_washout").return_periods != (int(CRIT.HAZARD_RETURN_YR),):
            say("  FAIL the washout duty holds its own return period")
            ok = False
        if abs(hz.station_freeboard_m - CRIT.PS_FLOOR_ABOVE_FLOOD_M) > 1e-12:
            say("  FAIL the station freeboard is not criteria's")
            ok = False
        say(f"  ok  thresholds come from w12.criteria: channel H{hz.channel_class}+, "
            f"scour H{hz.scour_class}+, washout RP {CRIT.HAZARD_RETURN_YR}, "
            f"freeboard {hz.station_freeboard_m:g} m")

        # -- duties --------------------------------------------------------------------
        for d in ("wadi_crossing", "pumping_station", "stp_site", "pipe_washout"):
            duty = governing(d)
            say(f"  duty {d:<18} RP {duty.return_periods}  [{duty.status}]  "
                f"{duty.citation}")

    say("  " + ("SELF-TEST PASSED" if ok else "SELF-TEST FAILED"))
    return ok


if __name__ == "__main__":  # pragma: no cover
    with HazardGrids() as _hz:
        print(_hz.banner())
    print()
    raise SystemExit(0 if self_test() else 1)
