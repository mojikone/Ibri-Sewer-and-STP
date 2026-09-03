# -*- coding: utf-8 -*-
"""w11b.present — the presentation library. One style spec, two outputs: KMZ and QGIS.

WHY THIS MODULE EXISTS, IN ONE LINE
-----------------------------------
The last review was unreadable, so the design could not be judged. A design that cannot be
LOOKED AT is a design nobody checks, and W11a shipped 42.5 % of its length draining uphill
with 2,449 vortex drop shafts against NAMA's 37 — a defect that is instantly obvious on a
map coloured by ground fall and invisible in a table. This module's job is to make every
claim about the network checkable by eye in under a minute.

THE ONE IDEA: ONE SPEC, TWO RENDERERS
-------------------------------------
A `View` is a declaration — what field carries the meaning, how it bands, what colour each
band gets, how thick the line is, what the balloon says, what the folders are. `kmz()` turns
it into a Google Earth file; `qgis_plan()` / `qgis_code()` turn the SAME object into a QGIS
renderer and a saved .qml. Neither is written twice, so the Earth file and the GIS project
physically cannot tell different stories. W8 had two separate stylings and they drifted.

WHAT IT WILL NOT DO
-------------------
  * It borrows NOTHING. No import from W8/py/sewnet, W10/py or W11a/py. Every number below
    is quoted from PAM-GUD-203 / -201 / -202 by page, or tagged as an assumption in
    `ASSUMPTIONS` and printed on the legend of every output that depends on it.
  * It never invents a design value. Where a map needs a band edge that the guideline does
    not give — a mid-band on a depth ramp, say — the edge is listed in `PRESENTATION_ONLY`
    and marked on the legend with a degree sign, so a reader can tell a rule from a ramp.
  * It depends on NO W11b stage. Hand it a GeoDataFrame or a path; it neither knows nor
    cares which stage produced it. That is deliberate: the library was written and proven
    against W11a's layers before W11b had any of its own.

THE FLAGS, CARRIED ON EVERY OUTPUT
----------------------------------
Three engineering decisions were taken on 3 Sep 2026 that a reviewer must see beside the
picture, not in a file somewhere else. They are printed on every legend, in every KMZ
document balloon, and in the QGIS group name:

  tau = 1.0 Pa           an ASSUMPTION, not a guideline value. G203-p27 4.2.2.1 gives the
                         equation Smin = K * tau^1.23 * Q^-0.461 and NO numeric design tau.
                         1.0 Pa gives shallower slopes, so shallower pipes and fewer pumps.
                         If NWS return 2.0 Pa the required gradient rises by 2^1.23 = 2.345x
                         and every depth on every map below changes. (GAP-9)
  DN above 1200          taken from the sizes the guideline itself tabulates — G203-p32
                         Tab 13 and p35 Tab 15 name DN1400, 1700, 1800, 2000 and 2400 in the
                         service-corridor width table. Flagged on the diameter view, awaiting
                         written NWS confirmation.
  wadi risk accepted     72 trunk chambers sit in a class 5/6 wadi on the client's own drawn
                         alignment, which is an INPUT. Risk accepted by the engineer, flagged
                         on the constraint view.

Sources read for this file: `_BRAIN/02_DESIGN_CRITERIA.md` (every number, each with its own
page reference back to the source PDF), `_BRAIN/08_DESIGN_PHILOSOPHY.md` (H1, H1a, H15, H16,
section 4 on tree orientation and the drop-structure diagnostic), `CLAUDE.md` rules 3 and 4
(named QGIS groups, saved layouts, satellite hybrid at 30 %, MoH_Plots as the land-use
layer, scalebar with non-overlapping labels).

Author's note on labels. Google Earth will happily draw 49,000 overlapping names into an
unreadable smear. Every label here is gated by a KML `<Region>`/`<Lod>` block, so a label
only draws once its own feature occupies enough of the screen. That is the correct KML
mechanism and it is why the label folders are on by default rather than off.
"""

from __future__ import annotations

import colorsys
import json
import math
import os
import re
import time
import zipfile
from dataclasses import dataclass, field as dc_field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# Hard imports, never a try/except fallback. A presentation library that silently degrades
# when pyproj is missing draws a map in the wrong place, and a wrong map is worse than none.
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point, Polygon, MultiPolygon


PRESENT_VERSION = "w11b-present-1.0"

CRS_EPSG = 32640                 # project rule; every input layer is expected in UTM 40N
WGS84_EPSG = 4326                # Google Earth
_TO_WGS = Transformer.from_crs(CRS_EPSG, WGS84_EPSG, always_xy=True)


# ======================================================================================
# 1.  THE ONLY DESIGN NUMBERS THIS LIBRARY IS ALLOWED TO QUOTE
#     Every entry carries the page it came from. Nothing here may be edited without
#     re-reading the source PDF. Values transcribed from _BRAIN/02_DESIGN_CRITERIA.md,
#     which is itself page-audited against the guideline PDFs in Data/ and _STANDARDS/.
# ======================================================================================

G = {
    # --- gravity hydraulics -----------------------------------------------------------
    "V_SELFCLEAN_MS":      (0.75,  "G203-p26",      "min self-cleansing velocity at peak flow"),
    "V_PREFERRED_MS":      (0.90,  "G203-p26",      "preferred self-cleansing velocity"),
    "V_MAX_MS":            (3.00,  "G203-p27",      "max velocity at design depth of flow"),
    "DOD_MAX_LE350":       (0.65,  "G203-p27 T10",  "max d/D at peak flow, DN <= 350"),
    "DOD_MAX_GT350":       (0.50,  "G203-p27 T10",  "max d/D at peak flow, DN > 350"),
    "DOD_DN_SPLIT_MM":     (350,   "G203-p27 T10",  "diameter at which the d/D limit changes"),
    # --- gradients (Table 11, Colebrook-White at 0.75 m/s) ----------------------------
    "SMIN_STEEPEST_PCT":   (0.500, "G203-p29 T11",  "steepest Table 11 minimum gradient (DN200, 5.00 mm/m)"),
    "SMIN_FLATTEST_PCT":   (0.075, "G203-p29 T11",  "flattest Table 11 minimum gradient (DN>=900, 0.75 mm/m)"),
    "SLOPE_STEP_PCT":      (0.05,  "project rule P1", "gradients laid on round 0.05 % steps"),
    # --- tractive force ---------------------------------------------------------------
    "TAU_EXPONENT":        (1.23,  "G203-p27 4.2.2.1", "exponent on tau in Smin = K.tau^1.23.Q^-0.461"),
    # --- depth and cover ---------------------------------------------------------------
    "MIN_COVER_CROWN_M":   (1.30,  "G203-p33",      "min cover to crown, gravity sewer"),
    "MIN_COVER_PROT_M":    (0.50,  "G203-p33",      "min cover where concrete-protected"),
    "MAX_COVER_M":         (12.0,  "G203-p33",      "max cover, 'approximately 10-12 m'; beyond -> pumping station"),
    "MAX_COVER_SOFT_M":    (10.0,  "G203-p33",      "lower bound of the same 10-12 m recommendation"),
    "CLEAR_UTILITY_M":     (3.0,   "G203-p33",      "min horizontal clearance to other utilities"),
    # --- manholes -----------------------------------------------------------------------
    "MH_SPACING_M": ({200: 100, 250: 100, 315: 100,
                      350: 120, 400: 120, 500: 120, 600: 120, 700: 120, 800: 120, 900: 120,
                      1000: 150, 1200: 150, 1400: 150,
                      1700: 200, 1800: 200, 2000: 200, 2400: 200},
                     "G203-p30 T12", "max manhole spacing by DN"),
    "DROP_BACKDROP_M":     (0.60,  "G203-p30",      "backdrop required when the invert drop exceeds this"),
    "DROP_VORTEX_M":       (2.00,  "G203-p30",      "backdrop max height; beyond -> vortex drop shaft"),
    "INLET_ANGLE_DEG":     (90.0,  "G203-p30",      "min inlet angle to the flow direction"),
    # --- diameters --------------------------------------------------------------------
    "DN_MIN_CONNECTION":   (160,   "G203-p22 T6",   "min property connection OD"),
    "DN_MIN_LATERAL":      (200,   "G203-p22 T6",   "min lateral OD; max lateral length 45 m"),
    "LATERAL_MAX_LEN_M":   (45.0,  "G203-p22 T6",   "max lateral length"),
    "DN_TRUNK_DEF_MM":     (800,   "G203-p35",      "trunk main definition: D > 800 mm and > 1000 m without connections"),
    # Service-corridor widths, G203-p32 Tab 13 / p35 Tab 15. The KEYS of this table are the
    # only diameters above DN1200 the guideline itself prints; that is the authority for
    # using DN1400 / 1700 / 1800 / 2000 / 2400 at all. Flagged, awaiting NWS confirmation.
    "CORRIDOR_W_M": ([((200, 500), 2.0), ((600, 900), 2.8), ((1000, 1200), 3.2),
                      ((1400, 1700), 4.0), ((1800, 1800), 4.1), ((2000, 2400), 4.4)],
                     "G203-p32 T13 / p35 T15", "service corridor width by DN band"),
    # --- pumping stations ---------------------------------------------------------------
    "PS_TYPE1_MAX_LS":     (100.0, "G203-p40-41 T17", "Type 1 station, <= 100 L/s, 1 duty + 1 standby"),
    "PS_TYPE2_MAX_LS":     (300.0, "G203-p40-41 T17", "Type 2 station, >100-300 L/s, 2 duty + 1 standby"),
    "PS_LAND_T1_M2":       ((50, 100),   "G203-p43 T21", "min land area, Type 1"),
    "PS_LAND_T2_M2":       ((200, 400),  "G203-p43 T21", "min land area, Type 2"),
    "PS_LAND_T3_M2":       ((900, None), "G203-p43 T21", "min land area, Type 3"),
    "PS_BUFFER_RES_M":     (30.0,  "G201-p43-44 T8", "pumping station buffer to residential"),
    # --- force mains -------------------------------------------------------------------
    "FM_V_MIN_MS":         (0.75,  "G203-p50",      "force main min velocity, continuous, at design MINIMUM flow"),
    "FM_V_MAX_MS":         (2.50,  "G203-p50",      "force main max velocity"),
    "FM_COVER_WADI_M":     (1.50,  "G203-p52 8.2.4", "FORCE MAIN cover to crown at a wadi crossing"),
    "FM_RETENTION_MIN":    (30.0,  "G203-p50",      "force main retention time, ideally not exceeded"),
    # --- wadi ---------------------------------------------------------------------------
    "HAZARD_WADI_CLASSES": ((4, 5, 6), "assumption (see ASSUMPTIONS A2)",
                            "flood-hazard classes read as 'wadi ground'"),
}


def g(key: str):
    """The value of a guideline constant. Use `gref(key)` to print it with its page."""
    return G[key][0]


def gref(key: str) -> str:
    """'0.75 m/s (G203-p26)' — a value and the page it came from, for a legend or a balloon."""
    v, page, _why = G[key]
    return f"{v} [{page}]"


def gwhy(key: str) -> str:
    v, page, why = G[key]
    return f"{why} = {v} ({page})"


# Names in `w11b.criteria` that hold the same quantity as a row of G above. This module does
# NOT import criteria — a presentation library must draw a layer that exists on disk without
# dragging the design basis in behind it, and it is deliberately runnable on a machine that
# has only geopandas. But two page-cited copies of the same number, maintained by two
# different people, will drift, so `verify_against_criteria()` below compares them on demand
# and the CLI runs it. A disagreement is a defect in one of the two files, never a rounding.
_CRITERIA_ALIASES = {
    "V_MAX_MS": "V_MAX",
    "MIN_COVER_CROWN_M": "MIN_COVER_CROWN",
    "MIN_COVER_PROT_M": "MIN_COVER_PROTECTED",
    "MAX_COVER_M": "MAX_COVER",
    "DOD_MAX_LE350": "DOD_MAX_SMALL",
    "DOD_MAX_GT350": "DOD_MAX_LARGE",
    "DOD_DN_SPLIT_MM": "DOD_DN_THRESHOLD",
    "DROP_BACKDROP_M": "DROP_TRIGGER",
    "DROP_VORTEX_M": "BACKDROP_MAX",
    "TAU_EXPONENT": "TRACTIVE_TAU_EXP",
    "FM_COVER_WADI_M": "MIN_COVER_WADI_XING",
}


def verify_against_criteria() -> List[str]:
    """Compare every number this module quotes with `w11b.criteria`, if that module is
    importable. Returns a list of disagreements — empty is the passing result.

    Checked 2026-09-03 against `w11b/criteria.py` (W11b-criteria-1.0): all eleven overlapping
    values agreed exactly, including the tau sensitivity factor, which both files put at
    2 ** 1.23 = 2.3457."""
    try:
        from w11b.criteria import DEFAULT as C          # type: ignore
    except Exception as e:
        return [f"w11b.criteria not importable ({type(e).__name__}); nothing cross-checked"]
    bad = []
    for mine, theirs in _CRITERIA_ALIASES.items():
        if not hasattr(C, theirs):
            bad.append(f"criteria has no '{theirs}' to check present.'{mine}' against")
            continue
        a, b = float(g(mine)), float(getattr(C, theirs))
        if abs(a - b) > 1e-9:
            bad.append(f"DISAGREE {mine}={a} ({G[mine][1]}) vs criteria.{theirs}={b}")
    fac = getattr(C, "TAU_SLOPE_FACTOR_AT_2PA", None)
    if fac is not None and abs(float(fac) - 2.0 ** g("TAU_EXPONENT")) > 1e-6:
        bad.append(f"DISAGREE tau sensitivity {2.0 ** g('TAU_EXPONENT')} vs {fac}")
    return bad


# --------------------------------------------------------------------------------------
# 1b.  Values that exist ONLY to make a map readable. Not design values. Marked on every
#      legend with a degree sign so a reader can tell a rule from a ramp.
# --------------------------------------------------------------------------------------

PRESENTATION_ONLY = {
    "depth_mid_m": [3.0, 6.0, 9.0],
    "flow_bands_ls": [1.0, 5.0, 25.0, 100.0, 500.0],
    "dod_util_bands": [0.50, 0.80, 1.00],
    "reason": ("intermediate band edges chosen so the colour ramp separates evenly across "
               "the observed range; they carry no engineering meaning. The OUTER edges of "
               "every band set below are guideline values and are cited."),
}


# ======================================================================================
# 2.  ASSUMPTIONS. Anything here is printed on the legend of every output that uses it.
# ======================================================================================

@dataclass(frozen=True)
class Assumption:
    aid: str
    headline: str
    detail: str
    consequence: str


ASSUMPTIONS: Dict[str, Assumption] = {
    "A1": Assumption(
        "A1",
        "tau = 1.0 Pa  (ASSUMED — G203 gives no numeric design tau)",
        "G203-p27 4.2.2.1 gives Smin = K.tau^1.23.Q^-0.461 and no design value for tau. "
        "1.0 Pa is the engineer's decision of 2026-09-03 and is GAP-9 with NWS.",
        f"At tau = 2.0 Pa the required gradient rises by 2^{g('TAU_EXPONENT')} = "
        f"{2.0 ** g('TAU_EXPONENT'):.3f}x. Every depth, every drop and every station count on "
        f"these maps would change. 1.0 Pa is the SHALLOWER, cheaper end.",
    ),
    "A2": Assumption(
        "A2",
        "'Wadi ground' = flood-hazard classes 4, 5, 6 of the 50-year grid",
        "G203-p30 4.4.1 and p33 prohibit pipes and chambers in wadis and washout areas but "
        "define neither. The AR&R hazard classes stand in for the guideline's washout/scour "
        "criterion. A project assumption, recorded beside GAP-9.",
        "A scour-depth check would replace it. Until then, 'in a wadi' on these maps means "
        "'in hazard class 4-6', not 'the guideline says so'.",
    ),
    "A3": Assumption(
        "A3",
        "Flood no-data is DRY HIGH GROUND, not 'untested'",
        "Engineer's decision 2026-09-03. The hazard grids cover part of the area; outside "
        "them the ground is treated as dry. Flow runs in the wadis.",
        "Reverses W11a, where 1,170 reaches were 'undecidable'. On these maps a reach "
        "outside the grid draws as clear, not as unknown.",
    ),
    "A4": Assumption(
        "A4",
        "DN above 1200 uses the sizes the guideline tabulates",
        "DN1400, 1700, 1800, 2000 and 2400 appear in the service-corridor width table, "
        "G203-p32 Tab 13 / p35 Tab 15. That table is the authority for the series; it is "
        "not a hydraulic endorsement of any of those sizes.",
        "Flagged on every diameter view. Awaiting written NWS confirmation of DN1400-2400.",
    ),
    "A5": Assumption(
        "A5",
        "72 trunk chambers in a class 5/6 wadi: risk ACCEPTED",
        "The trunk alignment is the client's own drawing and an INPUT, never re-routed. "
        "Engineer's decision 2026-09-03.",
        "Drawn, not hidden. The constraint view puts them in their own folder so the "
        "accepted risk is visible rather than filtered away.",
    ),
    "A6": Assumption(
        "A6",
        "Map band edges that are not guideline values are marked with a degree sign",
        PRESENTATION_ONLY["reason"],
        "A band edge without a page reference is a drawing choice. Do not quote one as a "
        "design criterion.",
    ),
}


# ======================================================================================
# 3.  COLOUR
# ======================================================================================

RGB = Tuple[int, int, int]


def _clamp8(v: float) -> int:
    return max(0, min(255, int(round(v))))


def golden_rgb(i: int, sat: float = 0.68, val: float = 0.92) -> RGB:
    """A colour for category i, spaced by the golden angle so neighbours never look alike.

    Used for categories with no natural order and no fixed meaning — sub-networks, packages.
    Value is nudged on alternate indices so two hues that do collide still separate by
    lightness, which is what a colour-blind reviewer actually reads."""
    h = (i * 0.6180339887498949) % 1.0
    s = sat + 0.14 * ((i % 3) / 2.0)
    v = val - 0.22 * (i % 2)
    r, gg, b = colorsys.hsv_to_rgb(h, min(1.0, s), max(0.35, v))
    return _clamp8(r * 255), _clamp8(gg * 255), _clamp8(b * 255)


# Ramps as explicit stops, so KMZ and QGIS interpolate identically. No matplotlib colormap
# is used for the data itself — only for the legend picture.
RAMPS: Dict[str, List[Tuple[float, RGB]]] = {
    # shallow -> deep. Blue is cheap, red is a problem.
    "depth": [(0.00, (49, 130, 189)), (0.35, (116, 196, 118)), (0.60, (254, 217, 118)),
              (0.82, (253, 141, 60)), (1.00, (189, 0, 38))],
    # small -> large. Deliberately different from `depth` so two maps are never confused.
    "size": [(0.00, (222, 235, 247)), (0.30, (158, 202, 225)), (0.60, (66, 146, 198)),
             (0.85, (33, 66, 145)), (1.00, (8, 29, 88))],
    # compliant -> breach
    "traffic": [(0.00, (26, 150, 65)), (0.45, (166, 217, 106)), (0.65, (255, 220, 60)),
                (0.85, (253, 141, 60)), (1.00, (215, 25, 28))],
    # climbs <- flat -> falls.  RED = the pipe is fighting the ground.
    "fall": [(0.00, (165, 0, 38)), (0.25, (244, 109, 67)), (0.50, (200, 200, 200)),
             (0.75, (145, 207, 96)), (1.00, (26, 120, 55))],
    # head / lift on a station
    "head": [(0.00, (255, 245, 200)), (0.40, (254, 196, 79)), (0.75, (217, 95, 14)),
             (1.00, (110, 30, 5))],
}


def ramp_rgb(name: str, t: float) -> RGB:
    stops = RAMPS[name]
    t = 0.0 if t != t else max(0.0, min(1.0, float(t)))     # NaN -> 0.0
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(_clamp8(c0[k] + f * (c1[k] - c0[k])) for k in range(3))  # type: ignore
    return stops[-1][1]


def kml_color(rgb: RGB, alpha: float = 1.0) -> str:
    """KML wants aabbggrr, NOT rrggbb. Getting this backwards is the classic KML bug."""
    a = _clamp8(alpha * 255)
    r, gg, b = rgb
    return f"{a:02x}{b:02x}{gg:02x}{r:02x}"


def hex_color(rgb: RGB) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# Fixed, ordered, colour-blind-safe palette for the tiers. These four have a natural order
# (a trunk carries everything a lateral does) so the colours are ordered too: dark and heavy
# for the trunk, light and thin for the lateral.
TIER_COLOURS: List[Tuple[str, str, RGB, float]] = [
    ("trunk main", "Trunk main — everything drains here", (17, 17, 17), 6.0),
    ("sub main",   "Sub main",                            (202, 0, 32), 3.8),
    ("main",       "Main sewer",                          (5, 113, 176), 2.4),
    ("lateral",    "Lateral",                             (146, 197, 222), 1.2),
]
# audit.py keys its diameter floors "sub main" / "trunk main" WITH A SPACE. Some client
# layers carry the underscore forms. Both are accepted on input; the space form is canonical.
TIER_ALIASES = {"sub_main": "sub main", "trunk_main": "trunk main",
                "submain": "sub main", "trunkmain": "trunk main"}


# ======================================================================================
# 4.  THE SPEC OBJECTS
# ======================================================================================

@dataclass
class ClassDef:
    """One legend row: a colour, a width, a label, and how many features landed in it."""
    key: Any
    label: str
    rgb: RGB
    width: float = 1.6              # line width, or icon scale for points
    lo: Optional[float] = None      # graduated views only
    hi: Optional[float] = None
    n: int = 0
    length_km: float = 0.0
    guideline: str = ""             # the page a band edge came from, "" if presentation-only

    def legend_text(self) -> str:
        bits = [self.label]
        if self.n:
            bits.append(f"n={self.n:,}")
        if self.length_km:
            bits.append(f"{self.length_km:,.1f} km")
        return "   ".join(bits)


@dataclass
class View:
    """A declaration of how one layer should be looked at. The whole library is driven by
    these; adding a new way to see the design is adding one of these, not writing code."""
    name: str                                   # file-safe id, e.g. "tier"
    title: str                                  # what the reviewer reads
    question: str                               # THE QUESTION THIS MAP ANSWERS. Mandatory.
    role: str = "reaches"                       # which input layer it wants
    geom: str = "line"                          # line | point | polygon
    mode: str = "categorical"                   # categorical | graduated | single
    field: Optional[str] = None                 # the attribute carrying the meaning
    derive: Optional[str] = None                # a name in DERIVERS, run before classifying
    categories: Optional[List[Tuple[Any, str, RGB, float]]] = None   # key,label,rgb,width
    breaks: Optional[List[float]] = None        # graduated: interior edges, ascending
    break_refs: Optional[List[str]] = None      # the page each break came from, "" if none
    ramp: str = "depth"
    # Where each graduated class sits on the ramp (0-1), and on the width scale. Default is
    # evenly spaced, which is right for a one-directional quantity like depth. It is WRONG
    # whenever both ends are bad: a velocity below 0.75 m/s and one above 3.0 m/s are both
    # failures, and the even default painted the slow end green. It is also wrong whenever
    # the interesting class is not the largest one — on the ground-fall map the problem is
    # the CLIMB, so the climbing classes are drawn thickest, not thinnest.
    class_t: Optional[List[float]] = None
    width_t: Optional[List[float]] = None
    width_range: Tuple[float, float] = (1.2, 5.5)
    width_field: Optional[str] = None           # thickness driven by a second attribute
    width_breaks: Optional[List[float]] = None
    size_field: Optional[str] = None            # points: icon scale driven by this
    size_range: Tuple[float, float] = (0.6, 2.4)
    size_fallbacks: Sequence[str] = ()          # tried in order when size_field is empty
    folder_fields: Sequence[str] = ()           # KMZ subfolders, outer first, max 2 deep
    folder_sort: str = "count"                  # count | name | length
    label_field: Optional[str] = None
    label_expr: Optional[Callable[[pd.Series], str]] = None
    label_min_lod: int = 256                    # pixels the feature must occupy to be named
    label_max: int = 12000                      # never write more labels than this
    label_filter: Optional[Callable[["pd.DataFrame"], "pd.Series"]] = None
    popup: Sequence[Tuple[str, str, str]] = ()  # (field, header, python format spec)
    only: Optional[Callable[["pd.DataFrame"], "pd.Series"]] = None   # row filter
    assumptions: Sequence[str] = ()             # ids into ASSUMPTIONS
    opacity: float = 1.0
    notes: Sequence[str] = ()
    priority: int = 50                          # display order in the loader / index

    def used_assumptions(self) -> List[Assumption]:
        return [ASSUMPTIONS[a] for a in self.assumptions if a in ASSUMPTIONS]


# ======================================================================================
# 5.  DERIVED FIELDS
#     Anything a view needs that a stage did not publish. Each writes ONE new column and
#     says so, so a QGIS layer can be materialised with the column present.
# ======================================================================================

def _first_field(df: pd.DataFrame, names: Sequence[str]) -> Optional[str]:
    for n in names:
        if n in df.columns:
            return n
    return None


def derive_components(df: pd.DataFrame) -> pd.DataFrame:
    """`SUBNET` — the connected component each reach belongs to, from the WRITTEN topology.

    Philosophy H16: topology is written down, never inferred from geometry. So this walks
    US_NODE/DS_NODE with a union-find and never touches a coordinate. If the stage already
    published a component/system field, that field is used unchanged and nothing is derived.

    Components are numbered by descending total length, so S001 is always the biggest thing
    on the map and the numbering does not shuffle between runs."""
    existing = _first_field(df, ["SUBNET", "SYS_ID", "COMP_ID", "NET_ID", "SYSTEM_ID"])
    if existing:
        out = df.copy()
        out["SUBNET"] = df[existing].astype(str)
        return out
    if not {"US_NODE", "DS_NODE"} <= set(df.columns):
        raise KeyError("derive_components needs US_NODE and DS_NODE (philosophy H16), or a "
                       "published SUBNET/SYS_ID/COMP_ID field. Neither is present.")

    parent: Dict[Any, Any] = {}

    def find(x):
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:          # path compression
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    us = df["US_NODE"].to_numpy()
    ds = df["DS_NODE"].to_numpy()
    for a, b in zip(us, ds):
        union(a, b)
    roots = np.array([find(a) for a in us])

    lens = (df["LEN_M"].to_numpy(dtype=float) if "LEN_M" in df.columns
            else np.ones(len(df), dtype=float))
    order = (pd.DataFrame({"root": roots, "len": lens})
             .groupby("root")["len"].sum().sort_values(ascending=False))
    rank = {r: i + 1 for i, r in enumerate(order.index)}
    out = df.copy()
    out["SUBNET"] = [f"S{rank[r]:03d}" for r in roots]
    return out


def derive_ground_slope(df: pd.DataFrame) -> pd.DataFrame:
    """`GRD_SLOPE` (%, positive = the ground FALLS in the direction of flow) and `GRD_FALL_M`.

    This is the W11b headline metric. W11a laid its tree on road connectivity and used the
    terrain only to check the answer; the result was 42.5 % of the length carrying flow
    uphill and 2,449 vortex shafts against NAMA's 37 (philosophy sec 4). A map coloured by
    this column shows in one glance whether W11b actually fixed it.

    Ground is reconstructed as invert + depth-below-ground at each end, because that pair is
    published on every reach. Where a stage publishes ground directly (GRD_US / GRD_DN) that
    is preferred and nothing is reconstructed."""
    out = df.copy()
    gu = _first_field(df, ["GRD_US", "GRND_US", "GL_US"])
    gd = _first_field(df, ["GRD_DN", "GRND_DN", "GL_DN"])
    if gu and gd:
        z_us = out[gu].astype(float)
        z_ds = out[gd].astype(float)
    elif {"INV_UP", "US_DEPTH", "INV_DN", "DS_DEPTH"} <= set(df.columns):
        z_us = out["INV_UP"].astype(float) + out["US_DEPTH"].astype(float)
        z_ds = out["INV_DN"].astype(float) + out["DS_DEPTH"].astype(float)
    else:
        raise KeyError("derive_ground_slope needs GRD_US/GRD_DN, or INV_UP+US_DEPTH and "
                       "INV_DN+DS_DEPTH. None of those pairs is present.")
    ln = out["LEN_M"].astype(float).replace(0.0, np.nan) if "LEN_M" in out.columns else np.nan
    out["GRD_FALL_M"] = z_us - z_ds
    out["GRD_SLOPE"] = 100.0 * out["GRD_FALL_M"] / ln
    return out


def derive_dod_util(df: pd.DataFrame) -> pd.DataFrame:
    """`DOD_UTIL` — d/D at peak as a fraction of the limit that applies to THAT diameter.

    The limit is not one number: G203-p27 Table 10 gives 0.65 for DN <= 350 and 0.50 above
    it. Colouring the raw d/D therefore paints a compliant DN200 and a breaching DN600 the
    same shade. The ratio removes the diameter dependence, so 1.00 is the breach line on
    every pipe on the map."""
    out = df.copy()
    dod = _first_field(df, ["DOD_PK", "DOD_PEAK", "D_OVER_D"])
    if dod is None or "DN" not in df.columns:
        raise KeyError("derive_dod_util needs DOD_PK (or DOD_PEAK) and DN.")
    lim = np.where(out["DN"].astype(float) <= g("DOD_DN_SPLIT_MM"),
                   g("DOD_MAX_LE350"), g("DOD_MAX_GT350"))
    out["DOD_LIMIT"] = lim
    out["DOD_UTIL"] = out[dod].astype(float) / lim
    return out


def derive_spacing_util(df: pd.DataFrame) -> pd.DataFrame:
    """`SPACE_UTIL` — reach length as a fraction of the max manhole spacing for its DN.

    G203-p30 Table 12: 100 m to DN315, 120 m to DN900, 150 m to DN1400, 200 m beyond.
    Deviation needs NWS pre-approval, so anything over 1.00 is a formal item, not a nuance."""
    out = df.copy()
    if not {"DN", "LEN_M"} <= set(df.columns):
        raise KeyError("derive_spacing_util needs DN and LEN_M.")
    table = g("MH_SPACING_M")
    keys = np.array(sorted(table.keys()), dtype=float)
    vals = np.array([table[int(k)] for k in keys], dtype=float)
    dn = out["DN"].astype(float).to_numpy()
    idx = np.clip(np.searchsorted(keys, dn, side="left"), 0, len(keys) - 1)
    out["MH_SPACE_MAX"] = vals[idx]
    out["SPACE_UTIL"] = out["LEN_M"].astype(float).to_numpy() / vals[idx]
    return out


def derive_constraint(df: pd.DataFrame) -> pd.DataFrame:
    """`BREACH` — the single worst rule this reach breaks, or 'clear'.

    Two things this got wrong on its first run against W11a's published layers, both fixed
    here and both worth stating because they are easy to repeat:

    1. SEVERITY MUST BE ASSIGNED HARDEST FIRST. A reach keeps the first label that sticks,
       so the list has to run from the prohibition down to the nuisance. Assigning upward
       filed 63 of the 74 reaches that run ALONG a dual carriageway under 'slow velocity'
       instead — a hard H1 breach hidden behind a soft one.

    2. BELOW 0.75 m/s IS NOT A BREACH WHERE THE TRACTIVE-FORCE METHOD GOVERNS. G203-p27
       4.2.2.1 requires the STEEPER of the two methods and explicitly sends network heads to
       tractive force where 0.75 m/s is unattainable. On W11a that is 44,952 reaches — 91 %
       of the network — so calling it a breach painted the whole map red and buried the 11
       things that were actually wrong. It now gets its own non-breach class, because the
       extent of it is exactly the extent of the exposure to the ASSUMED tau (A1)."""
    out = df.copy()
    n = len(out)
    breach = pd.Series(["clear"] * n, index=out.index, dtype=object)

    def mask(series_expr) -> np.ndarray:
        s = series_expr
        return (s.fillna(False).to_numpy() if isinstance(s, pd.Series) else np.asarray(s))

    ranked: List[Tuple[np.ndarray, str]] = []

    def add(cond, label):
        ranked.append((mask(cond), label))

    # ---- hardest first. A prohibition outranks a cost; a cost outranks a nuisance. -------
    if "ON_DUAL_M" in out.columns:
        add(pd.to_numeric(out["ON_DUAL_M"], errors="coerce") > 0,
            "ALONG a dual carriageway (rule 7)")
    if "ON_WADI_M" in out.columns:
        add(pd.to_numeric(out["ON_WADI_M"], errors="coerce") > 0,
            "ALONG a wadi (H1, p30 4.4.1)")
    for c in ("US_DEPTH", "DS_DEPTH"):
        if c in out.columns:
            add(pd.to_numeric(out[c], errors="coerce") > g("MAX_COVER_M"),
                "past the 12 m cap (p33)")
    for c in ("COVER_US", "COVER_DN"):
        if c in out.columns:
            add(pd.to_numeric(out[c], errors="coerce") < g("MIN_COVER_CROWN_M"),
                "below 1.30 m cover (p33)")
    if "DOD_UTIL" in out.columns:
        add(pd.to_numeric(out["DOD_UTIL"], errors="coerce") > 1.0,
            "over the d/D limit (p27 T10)")
    if "SPACE_UTIL" in out.columns:
        add(pd.to_numeric(out["SPACE_UTIL"], errors="coerce") > 1.0,
            "manhole spacing over Table 12")
    # A velocity below 0.75 m/s is a breach ONLY where the design says velocity governs.
    if "V_PK_MS" in out.columns:
        slow = pd.to_numeric(out["V_PK_MS"], errors="coerce") < g("V_SELFCLEAN_MS")
        by = None
        for c in ("CLEAN_BY", "SELFCLEAN_BY", "CLEANSE_BY"):
            if c in out.columns:
                by = out[c].astype(str).str.lower()
                break
        if by is None:
            add(slow, "below 0.75 m/s (p26)")
        else:
            add(slow & ~by.str.contains("tract"), "below 0.75 m/s (p26)")
            add(slow & by.str.contains("tract"),
                "below 0.75 m/s — tractive force governs (legal, p27)")

    for m, label in ranked:
        breach.loc[(breach == "clear").to_numpy() & m] = label
    out["BREACH"] = breach
    return out


def derive_station_type(df: pd.DataFrame) -> pd.DataFrame:
    """`ST_BAND` — Type 1/2/3 from the duty flow, G203-p40-41 Table 17, plus `LAND_MIN_M2`.

    Recomputed rather than trusted, because W11a published `ST_TYPE = 'Type 1'` on all 98
    of its stations while `Q_DUTY_LS` was 0.0 on every one of them — the type was not
    derived from anything. If duty flow is absent or all zero the band is 'not sized', which
    is what a reviewer needs to see."""
    out = df.copy()
    qf = _first_field(df, ["Q_DUTY_LS", "QDUTY_LS", "Q_DUTY"])
    if qf is None:
        out["ST_BAND"] = "not sized — no duty flow published"
        out["LAND_MIN_M2"] = np.nan
        return out
    q = pd.to_numeric(out[qf], errors="coerce")
    band = pd.Series("not sized — duty flow is zero", index=out.index, dtype=object)
    band[q > 0] = "Type 1  (<= 100 L/s)"
    band[q > g("PS_TYPE1_MAX_LS")] = "Type 2  (100-300 L/s)"
    band[q > g("PS_TYPE2_MAX_LS")] = "Type 3  (> 300 L/s)"
    land = pd.Series(np.nan, index=out.index, dtype=float)
    land[band.str.startswith("Type 1")] = g("PS_LAND_T1_M2")[0]
    land[band.str.startswith("Type 2")] = g("PS_LAND_T2_M2")[0]
    land[band.str.startswith("Type 3")] = g("PS_LAND_T3_M2")[0]
    out["ST_BAND"] = band
    out["LAND_MIN_M2"] = land
    return out


def derive_drop(df: pd.DataFrame) -> pd.DataFrame:
    """`DROP_BAND` — none / backdrop / vortex shaft, from the invert drop at the chamber.

    G203-p30: a backdrop is required beyond 600 mm and capped at 2 m; past 2 m it becomes a
    vortex drop shaft. The count of that last band IS the tree-orientation diagnostic
    (philosophy sec 4): NAMA built 37 of them across the whole existing network."""
    out = df.copy()
    df_ = _first_field(df, ["DROP_M", "DROP", "DROP_HT_M"])
    if df_ is None:
        raise KeyError("derive_drop needs DROP_M.")
    d = pd.to_numeric(out[df_], errors="coerce").fillna(0.0)
    band = pd.Series("no drop structure", index=out.index, dtype=object)
    band[d > g("DROP_BACKDROP_M")] = "backdrop (> 0.60 m)"
    band[d > g("DROP_VORTEX_M")] = "VORTEX DROP SHAFT (> 2.00 m)"
    out["DROP_BAND"] = band
    return out


DERIVERS: Dict[str, Tuple[Callable[[pd.DataFrame], pd.DataFrame], List[str]]] = {
    "components":    (derive_components,    ["SUBNET"]),
    "ground_slope":  (derive_ground_slope,  ["GRD_SLOPE", "GRD_FALL_M"]),
    "dod_util":      (derive_dod_util,      ["DOD_UTIL", "DOD_LIMIT"]),
    "spacing_util":  (derive_spacing_util,  ["SPACE_UTIL", "MH_SPACE_MAX"]),
    "constraint":    (derive_constraint,    ["BREACH"]),
    "station_type":  (derive_station_type,  ["ST_BAND", "LAND_MIN_M2"]),
    "drop_band":     (derive_drop,          ["DROP_BAND"]),
    # `constraint` wants the two utilisation columns first; chained here so a caller asking
    # for the constraint view never has to know that.
    "constraint_full": (lambda d: derive_constraint(
        _try(derive_spacing_util, _try(derive_dod_util, d))),
        ["BREACH", "DOD_UTIL", "SPACE_UTIL"]),
}


def _try(fn, df):
    """Run a deriver, and carry on without its column if the input cannot support it. Used
    ONLY inside `constraint_full`, where a missing d/D simply means that breach cannot be
    reported — never to paper over a missing field a view actually depends on."""
    try:
        return fn(df)
    except Exception:
        return df


# ======================================================================================
# 6.  THE VIEW CATALOGUE
#     Each entry states the question it answers. A view that cannot say what it is for is
#     a decoration, and decorations are why the last report was unreadable.
# ======================================================================================

def _pop(*rows: Tuple[str, str, str]) -> List[Tuple[str, str, str]]:
    return list(rows)


_REACH_POPUP = _pop(
    ("EDGE_UID", "Reach", "{}"),
    ("TIER", "Tier", "{}"),
    ("DN", "Diameter", "DN{:.0f}"),
    ("MATERIAL", "Material", "{}"),
    ("LEN_M", "Length", "{:.1f} m"),
    ("SLOPE_LAID", "Laid gradient", "{:.3f} %"),
    ("SLOPE_MIN", "Minimum required", "{:.3f} %"),
    ("GRAD_BY", "Gradient set by", "{}"),
    ("TAU_PA", "Tractive stress used", "{:.2f} Pa  (ASSUMED, see A1)"),
    ("QPK_LS", "Peak flow", "{:.2f} L/s"),
    ("V_PK_MS", "Velocity at peak", "{:.2f} m/s"),
    ("DOD_PK", "d/D at peak", "{:.3f}"),
    ("INV_UP", "Invert up", "{:.2f} m aOD"),
    ("INV_DN", "Invert down", "{:.2f} m aOD"),
    ("US_DEPTH", "Depth at head", "{:.2f} m"),
    ("DS_DEPTH", "Depth at tail", "{:.2f} m"),
    ("N_PROP", "Properties upstream", "{:.0f}"),
    ("PACKAGE", "Package", "{}"),
)

_NODE_POPUP = _pop(
    ("NODE_REF", "Chamber", "{}"),
    ("NODE_KIND", "Kind", "{}"),
    ("TIER", "Tier", "{}"),
    ("GRD_M", "Ground", "{:.2f} m aOD"),
    ("INV_M", "Invert", "{:.2f} m aOD"),
    ("DEPTH_M", "Depth", "{:.2f} m"),
    ("COVER_M", "Cover", "{:.2f} m"),
    ("DROP_M", "Invert drop", "{:.2f} m"),
    ("MH_DIA", "Chamber dia", "{:.2f} m"),
    ("Q_PK_LS", "Peak flow", "{:.2f} L/s"),
    ("INLET_DEG", "Sharpest inlet", "{:.0f} deg"),
    ("PACKAGE", "Package", "{}"),
)

_STATION_POPUP = _pop(
    ("NODE_REF", "Station", "{}"),
    ("ST_BAND", "Type (from duty flow)", "{}"),
    ("Q_DUTY_LS", "Duty flow", "{:.1f} L/s"),
    ("LIFT_M", "Static lift", "{:.2f} m"),
    ("TOT_HD_M", "Total head", "{:.2f} m"),
    ("WELL_M3", "Wet well live volume", "{:.1f} m3"),
    ("WW_STARTS", "Starts per hour", "{:.0f}"),
    ("Q_ADF_M3D", "Average day flow", "{:.0f} m3/d"),
    ("N_PROP", "Properties served", "{:.0f}"),
    ("LAND_MIN_M2", "Min land (p43 T21)", "{:.0f} m2"),
    ("LAND_M2", "Land reserved", "{:.0f} m2"),
    ("GRD_M", "Ground", "{:.2f} m aOD"),
    ("FLOOD_LV", "Flood level", "{:.2f} m aOD"),
    ("WHY", "Why here", "{}"),
)


def _dn_categories() -> List[Tuple[Any, str, RGB, float]]:
    """Diameter as a category, using the guideline's own printed series. DN above 1200 is
    flagged in its own label because it is assumption A4, not a settled size."""
    series = [200, 250, 315, 400, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1700, 1800, 2000, 2400]
    out = []
    for i, dn in enumerate(series):
        t = i / (len(series) - 1)
        w = 1.1 + 5.2 * (i / (len(series) - 1)) ** 0.75
        tag = "" if dn <= 1200 else "   [A4 — awaiting NWS]"
        out.append((dn, f"DN{dn}{tag}", ramp_rgb("size", t), round(w, 2)))
    return out


VIEWS: Dict[str, View] = {}


def register(v: View) -> View:
    VIEWS[v.name] = v
    return v


register(View(
    name="tier", priority=10,
    title="Sewers by TIER",
    question="Is this a hierarchy, or a flat mat of pipe? How many things touch the trunk?",
    role="reaches", geom="line", mode="categorical", field="TIER",
    categories=TIER_COLOURS,
    folder_fields=("TIER",), folder_sort="length",
    label_field="EDGE_UID", label_min_lod=400,
    label_filter=lambda d: d["TIER"].isin(["trunk main", "sub main"]) if "TIER" in d else None,
    popup=_REACH_POPUP,
    assumptions=("A1",),
    notes=("Trunk main is defined at G203-p35: D > 800 mm and > 1,000 m without connections.",
           "In NAMA's built network only ~16 things touch the trunk. Count the black line's "
           "junctions before you believe the hierarchy."),
))

register(View(
    name="depth", priority=20,
    title="Sewers by DEPTH",
    question="Where does this design get expensive, and where does it pass the 12 m cap?",
    role="reaches", geom="line", mode="graduated", field="US_DEPTH",
    breaks=[g("MIN_COVER_CROWN_M"), 3.0, 6.0, 9.0, g("MAX_COVER_M")],
    break_refs=["G203-p33 min cover", "", "", "", "G203-p33 max cover"],
    ramp="depth", width_range=(1.2, 5.0),
    folder_fields=(), label_field=None,
    popup=_REACH_POPUP,
    assumptions=("A1", "A6"),
    notes=("The 1.30 m and 12.0 m edges are guideline values (G203-p33). 3 / 6 / 9 m are "
           "drawing bands with no engineering meaning.",
           "Everything in the top band is a candidate for a pumping station: G203-p33 says "
           "that where excavation cost is prohibitive, incorporate one."),
))

register(View(
    name="subnet", priority=30,
    title="Sewers by SUB-NETWORK",
    question="How many separate systems is this really, and does each end at one outfall?",
    role="reaches", geom="line", mode="categorical", field="SUBNET",
    derive="components",
    folder_fields=("SUBNET",), folder_sort="length",
    popup=_REACH_POPUP + _pop(("SUBNET", "Sub-network", "{}")),
    assumptions=(),
    notes=("Components are walked from the WRITTEN US_NODE/DS_NODE topology, never from "
           "geometry (philosophy H16).",
           "H15: each component must end at EXACTLY ONE outfall. A component with two is a "
           "defect; a component with none drains nowhere.",
           "W10 published a layer in 7,919 pieces and nobody could see it. Count the folders."),
))

register(View(
    name="diameter", priority=40,
    title="Sewers by DIAMETER",
    question="Where are the big pipes, and how much of the scheme depends on DN above 1200?",
    role="reaches", geom="line", mode="categorical", field="DN",
    categories=_dn_categories(),
    folder_fields=("DN",), folder_sort="name",
    popup=_REACH_POPUP,
    assumptions=("A4",),
    notes=("The series is the guideline's own: DN1400 / 1700 / 1800 / 2000 / 2400 are "
           "printed in the service-corridor width table, G203-p32 Tab 13 / p35 Tab 15.",
           "Oversizing a pipe in order to lay it flatter is PROHIBITED (G203-p29). A large "
           "diameter on a flat gradient here should be carrying flow, not buying slope."),
))

register(View(
    name="ground_fall", priority=15,
    title="Does the pipe follow the ground?",
    question="THE W11b QUESTION. How much of this network carries flow UPHILL?",
    role="reaches", geom="line", mode="graduated", field="GRD_SLOPE",
    derive="ground_slope",
    breaks=[-g("SMIN_STEEPEST_PCT"), -g("SMIN_FLATTEST_PCT"),
            g("SMIN_FLATTEST_PCT"), g("SMIN_STEEPEST_PCT")],
    break_refs=["G203-p29 T11 steepest min", "G203-p29 T11 flattest min",
                "G203-p29 T11 flattest min", "G203-p29 T11 steepest min"],
    ramp="fall", width_range=(1.0, 4.6),
    # thickest where it CLIMBS: on this map the defect is what has to be loud
    width_t=[1.00, 0.62, 0.30, 0.12, 0.06],
    popup=_REACH_POPUP + _pop(("GRD_SLOPE", "Ground slope along flow", "{:+.3f} %"),
                              ("GRD_FALL_M", "Ground fall along flow", "{:+.2f} m")),
    assumptions=(),
    notes=("RED = the ground RISES in the direction of flow. The pipe is fighting gravity "
           "and buys its rise in depth at the minimum gradient for the whole length.",
           "The band edges are the guideline's own gradient extremes: 0.500 % is the "
           "STEEPEST Table 11 minimum (DN200, 5.00 mm/m) and 0.075 % the FLATTEST "
           "(DN >= 900, 0.75 mm/m). Ground flatter than 0.075 % cannot carry any pipe in "
           "the table without digging.",
           "W11a measured 42.5 % of length (737.7 km) uphill. That is the number to beat."),
))

register(View(
    name="flow", priority=50,
    title="Sewers by PEAK FLOW",
    question="Does the flow grow the way a tree should — small at the tips, large at the trunk?",
    role="reaches", geom="line", mode="graduated", field="QPK_LS",
    breaks=PRESENTATION_ONLY["flow_bands_ls"],
    break_refs=["", "", "", "", ""],
    ramp="size", width_range=(1.0, 6.0),
    popup=_REACH_POPUP,
    assumptions=("A6",),
    notes=("All five band edges are drawing bands, chosen to spread a log-ish distribution. "
           "None is a design value.",),
))

register(View(
    name="velocity", priority=60,
    title="Self-cleansing — velocity at peak (a RISK map, not a compliance map)",
    question="Which pipes will silt up? Not the same question as: which pipes are legal?",
    role="reaches", geom="line", mode="graduated", field="V_PK_MS",
    breaks=[g("V_SELFCLEAN_MS"), g("V_PREFERRED_MS"), g("V_MAX_MS")],
    break_refs=["G203-p26 min self-cleansing", "G203-p26 preferred", "G203-p27 max"],
    ramp="traffic", width_range=(1.1, 4.0),
    # BOTH ends of this scale are failures — too slow silts, too fast scours — so the ramp is
    # not monotonic. An evenly spaced default painted "below 0.75 m/s" green.
    class_t=[1.00, 0.50, 0.00, 1.00],
    width_t=[0.85, 0.35, 0.15, 1.00],
    popup=_REACH_POPUP,
    assumptions=("A1",),
    notes=("Every edge on this map is a guideline value.",
           "The colour is NOT monotonic: red at BOTH ends. Below 0.75 m/s silts up "
           "(G203-p26); above 3.0 m/s scours (G203-p27). Green is the middle.",
           "THIS MAP IS NOT A COMPLIANCE MAP. Red at the bottom means below 0.75 m/s, which "
           "at network heads is expected: G203-p27 4.2.2.1 sends those reaches to the "
           "tractive-force method instead, and they are LEGAL. Compliance is on the "
           "'WHAT IS WRONG' map. What this one shows is the silting RISK that remains, and "
           "the extent of the scheme that leans on the assumed tau = 1.0 Pa.",
           "G203-p28 4.2.6 adds that EARLY-PHASE flows sit below design flow, so a pipe "
           "that is marginal here will be worse in 2030 than at ultimate."),
))

register(View(
    name="capacity", priority=70,
    title="Capacity — d/D against the limit for that diameter",
    question="What is surcharged, or close to it?",
    role="reaches", geom="line", mode="graduated", field="DOD_UTIL",
    derive="dod_util",
    breaks=PRESENTATION_ONLY["dod_util_bands"],
    break_refs=["", "", "G203-p27 T10 limit"],
    ramp="traffic", width_range=(1.3, 4.5),
    popup=_REACH_POPUP + _pop(("DOD_UTIL", "d/D as a fraction of the limit", "{:.2f}"),
                              ("DOD_LIMIT", "The limit that applies here", "{:.2f}")),
    assumptions=("A6",),
    notes=("1.00 is the breach line on EVERY pipe here, whatever its diameter: the raw "
           "limit is 0.65 for DN <= 350 and 0.50 above (G203-p27 Tab 10), so the ratio is "
           "plotted rather than the raw d/D.",
           "0.50 and 0.80 are drawing bands."),
))

register(View(
    name="constraint", priority=5,
    title="WHAT IS WRONG — one folder per rule broken",
    question="Show me only the breaches, ranked, with everything compliant greyed out.",
    role="reaches", geom="line", mode="categorical", field="BREACH",
    derive="constraint_full",
    categories=[
        ("ALONG a dual carriageway (rule 7)", "ALONG a dual carriageway — no pipe may be laid", (0, 0, 0), 6.0),
        ("ALONG a wadi (H1, p30 4.4.1)", "ALONG a wadi — washout (G203-p30 4.4.1, p33)", (166, 0, 30), 5.0),
        ("past the 12 m cap (p33)", "Past the 12 m cover cap (G203-p33)", (227, 74, 51), 4.0),
        ("below 1.30 m cover (p33)", "Below 1.30 m cover (G203-p33)", (253, 141, 60), 3.2),
        ("below 0.75 m/s (p26)", "Below 0.75 m/s at peak, velocity governs (G203-p26)", (254, 196, 79), 2.6),
        ("over the d/D limit (p27 T10)", "Over the d/D limit (G203-p27 Tab 10)", (140, 81, 10), 3.0),
        ("manhole spacing over Table 12", "Manhole spacing over Table 12 (G203-p30)", (117, 112, 179), 2.2),
        ("below 0.75 m/s — tractive force governs (legal, p27)",
         "Below 0.75 m/s but LEGAL — tractive force governs (G203-p27 4.2.2.1). "
         "This is the extent of the tau = 1.0 Pa exposure", (120, 170, 200), 0.9),
        ("clear", "Clear", (200, 200, 200), 0.7),
    ],
    folder_fields=("BREACH",), folder_sort="count",
    popup=_REACH_POPUP + _pop(("BREACH", "Rule broken", "{}"),
                              ("ON_DUAL_M", "Length along a dual carriageway", "{:.1f} m"),
                              ("ON_WADI_M", "Length along a wadi", "{:.1f} m")),
    assumptions=("A1", "A2", "A3", "A5"),
    notes=("One reach, one folder: the WORST rule it breaks. A reach that is both over-deep "
           "and on a dual carriageway is filed under the dual carriageway, because a depth "
           "is a cost and H1 is a prohibition.",
           "'Below 0.75 m/s — tractive force governs' is NOT a breach. G203-p27 4.2.2.1 "
           "requires the steeper of the two methods and sends network heads to tractive "
           "force where 0.75 m/s is unattainable. The size of that band IS the size of the "
           "scheme's exposure to the assumed tau = 1.0 Pa (A1).",
           "The 72 trunk chambers in a class 5/6 wadi are an ACCEPTED risk (A5) on the "
           "client's own alignment. They are drawn, not filtered away."),
))

register(View(
    name="package", priority=80,
    title="Sewers by PACKAGE",
    question="What does one contract actually contain, and can it be commissioned alone?",
    role="reaches", geom="line", mode="categorical", field="PACKAGE",
    folder_fields=("PHASE", "PACKAGE"), folder_sort="length",
    popup=_REACH_POPUP,
    notes=("Colours are golden-angle spaced, so two adjacent packages never look alike. "
           "They carry no order and no meaning beyond identity.",
           "Folders nest phase over package: 500 packages in one flat list is not "
           "navigable in Google Earth."),
))

register(View(
    name="phase", priority=85,
    title="Sewers by PHASE",
    question="What gets built first?",
    role="reaches", geom="line", mode="categorical", field="PHASE",
    folder_fields=("PHASE",), folder_sort="name",
    popup=_REACH_POPUP,
))

register(View(
    name="material", priority=90,
    title="Sewers by MATERIAL",
    question="Is the material consistent with the diameter and the laying method?",
    role="reaches", geom="line", mode="categorical", field="MATERIAL",
    folder_fields=("MATERIAL",), folder_sort="length",
    popup=_REACH_POPUP,
    notes=("G203-p22: main sewers DN >= 350 are GRP, HDPE or lined RCC in open trench. "
           "G203-p35 Tab 14: above DN600 the trunk is GRP, lined RCC or profile-wall HDPE.",),
))

register(View(
    name="stations", priority=25,
    title="Pumping stations — size by DUTY FLOW, colour by LIFT",
    question="How many stations, how big, and how hard are they working?",
    role="stations", geom="point", mode="graduated", field="LIFT_M",
    derive="station_type",
    breaks=[2.0, 5.0, 10.0, 20.0],
    break_refs=["", "", "", ""],
    ramp="head",
    size_field="Q_DUTY_LS", size_range=(0.7, 2.6),
    size_fallbacks=("Q_ADF_M3D", "N_PROP"),
    folder_fields=("ST_BAND",), folder_sort="count",
    label_field="NODE_REF", label_min_lod=48, label_max=2000,
    popup=_STATION_POPUP,
    assumptions=("A1", "A6"),
    notes=("Icon AREA is proportional to duty flow, so a station twice the flow draws twice "
           "the ink — not four times.",
           "Type bands are G203-p40-41 Tab 17: Type 1 <= 100 L/s, Type 2 100-300, Type 3 "
           "> 300 L/s. Minimum land is p43 Tab 21: 50-100 / 200-400 / >= 900 m2.",
           "The lift bands are drawing bands.",
           "If the legend says 'not sized', duty flow is not published and the icons fell "
           "back to a proxy. Read nothing into their size until that is fixed."),
))

register(View(
    name="drops", priority=17,
    title="Drop structures — the tree-orientation diagnostic",
    question="How many vortex drop shafts does this layout demand? NAMA built 37.",
    role="nodes", geom="point", mode="categorical", field="DROP_BAND",
    derive="drop_band",
    categories=[
        ("VORTEX DROP SHAFT (> 2.00 m)", "VORTEX DROP SHAFT — invert drop over 2.00 m (G203-p30)", (165, 0, 38), 1.5),
        ("backdrop (> 0.60 m)", "Backdrop — invert drop over 0.60 m (G203-p30)", (253, 174, 97), 0.9),
        ("no drop structure", "No drop structure", (190, 190, 190), 0.16),
    ],
    folder_fields=("DROP_BAND",), folder_sort="count",
    label_field="NODE_REF", label_min_lod=256, label_max=4000,
    label_filter=lambda d: d["DROP_BAND"].str.startswith("VORTEX") if "DROP_BAND" in d else None,
    popup=_NODE_POPUP,
    notes=("G203-p30: backdrop required beyond 600 mm, capped at 2 m; past 2 m it is a "
           "vortex drop shaft.",
           "This count is the honest measure of whether the tree runs with the ground. "
           "W11a wanted 2,449 of them against NAMA's 37 across the whole built network."),
))

register(View(
    name="chambers", priority=35,
    title="Chambers by DEPTH",
    question="Where are the deep chambers, and are they clustered or scattered?",
    role="nodes", geom="point", mode="graduated", field="DEPTH_M",
    breaks=[g("MIN_COVER_CROWN_M"), 3.0, 6.0, 9.0, g("MAX_COVER_M")],
    break_refs=["G203-p33 min cover", "", "", "", "G203-p33 max cover"],
    ramp="depth", size_range=(0.35, 1.5),
    label_field="NODE_REF", label_min_lod=512, label_max=6000,
    popup=_NODE_POPUP,
    assumptions=("A1", "A6"),
))

register(View(
    name="rising_mains", priority=75,
    title="Rising mains — diameter and duty",
    question="Where does the scheme pump, how far, and how long does sewage sit in the main?",
    role="rising_mains", geom="line", mode="categorical", field="DN",
    categories=_dn_categories(),
    folder_fields=("STATION",), folder_sort="length",
    label_field="STATION", label_min_lod=128, label_max=1500,
    popup=_pop(("EDGE_UID", "Main", "{}"), ("STATION", "From station", "{}"),
               ("DN", "Diameter", "DN{:.0f}"), ("MATERIAL", "Material", "{}"),
               ("LEN_M", "Length", "{:.1f} m"), ("Q_DUTY_LS", "Duty flow", "{:.1f} L/s"),
               ("V_DUTY_MS", "Velocity at duty", "{:.2f} m/s"),
               ("V_MIN_MS", "Velocity at min flow", "{:.2f} m/s"),
               ("STAT_HD_M", "Static head", "{:.2f} m"),
               ("TOT_HD_M", "Total head", "{:.2f} m"),
               ("RETENT_M", "Retention time", "{:.1f} min"),
               ("N_AIRV", "Air valves", "{:.0f}"), ("N_WASH", "Washouts", "{:.0f}")),
    notes=("G203-p50: 0.75 m/s continuous, 1.0 m/s intermittent, 2.5 m/s max, and the "
           "minimum applies at design MINIMUM flow (Tab 16 factors, p40), not at average.",
           "G203-p50: retention ideally under 30 minutes; access every 500 m. "
           "G203-p53-54: isolation valves ~500 m, never over 800 m.",
           "G203-p55: a force main discharges to a manhole not more than 300 mm above the "
           "receiving flow line."),
))

register(View(
    name="packages_area", priority=95,
    title="Package areas",
    question="What ground does each contract cover, and do the areas nest sensibly?",
    role="packages", geom="polygon", mode="categorical", field="PACKAGE",
    folder_fields=("PHASE",), folder_sort="name",
    label_field="PACKAGE", label_min_lod=128, label_max=1500,
    opacity=0.35,
    popup=_pop(("PACKAGE", "Package", "{}"), ("PHASE", "Phase", "{}"),
               ("LEN_KM", "Sewer length", "{:.2f} km"), ("N_PLOT", "Plots", "{:.0f}"),
               ("OUTLET", "Outlet", "{}"), ("DS_PKG", "Drains to", "{}"),
               ("COMM_SEQ", "Commissioning order", "{:.0f}"),
               ("INDEP", "Commissionable alone", "{}")),
))

register(View(
    name="servicing", priority=97,
    title="Servicing decision — what is sewered and what is not",
    question="Which settlements get a network, which get a satellite works, which get nothing?",
    role="servicing", geom="polygon", mode="categorical", field="SYSTEM",
    folder_fields=("SYSTEM",), folder_sort="count",
    label_field="NAME", label_min_lod=96, label_max=800,
    opacity=0.35,
    popup=_pop(("NAME", "Settlement", "{}"), ("TOWN", "Town", "{}"),
               ("SYSTEM", "System", "{}"), ("WORKS", "Works", "{}"),
               ("DEC_RULE", "Decided by", "{}"), ("WHY", "Why", "{}"),
               ("N_PLOT", "Plots", "{:.0f}"), ("N_PROP", "Properties", "{:.0f}"),
               ("POP", "Population", "{:.0f}"),
               ("Q_ADF_M3D", "Average day flow", "{:.0f} m3/d"),
               ("M_PER_PRP", "Metres of sewer per property", "{:.1f}"),
               ("CONFIDENCE", "Confidence", "{}")),
))


def list_views(role: Optional[str] = None) -> List[str]:
    """The view names, in the order a reviewer should open them."""
    vs = [v for v in VIEWS.values() if role is None or v.role == role]
    return [v.name for v in sorted(vs, key=lambda v: (v.priority, v.name))]


def describe_views() -> str:
    """A printable catalogue: what each map answers and what it needs."""
    lines = []
    for n in list_views():
        v = VIEWS[n]
        lines.append(f"{v.name:<16} [{v.role}/{v.geom}]  {v.title}")
        lines.append(f"{'':<16}   ? {v.question}")
    return "\n".join(lines)


# ======================================================================================
# 7.  CLASSIFICATION
# ======================================================================================

@dataclass
class Classified:
    classes: List[ClassDef]
    index: np.ndarray            # class index per row, -1 = unclassifiable
    gdf: gpd.GeoDataFrame        # after derive + filter
    field: str
    flags: List[str] = dc_field(default_factory=list)
    stats: Dict[str, Any] = dc_field(default_factory=dict)


def _fmt_band(lo: Optional[float], hi: Optional[float], unit: str = "") -> str:
    if lo is None:
        return f"< {hi:g}{unit}"
    if hi is None:
        return f">= {lo:g}{unit}"
    return f"{lo:g} to {hi:g}{unit}"


def _normalise_tiers(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().replace(TIER_ALIASES)


def classify(gdf: gpd.GeoDataFrame, view: View,
             derived_here: Optional[Iterable[str]] = None) -> Classified:
    """Run the deriver, filter, band the data and count what landed where.

    Everything a legend needs comes out of here, so the KMZ legend, the QGIS renderer and
    the printed summary are all reading the same counts. They diverged in W8 because each
    counted for itself."""
    flags: List[str] = []
    df = gdf

    ours = set(derived_here or ())
    if view.derive:
        fn, cols = DERIVERS[view.derive]
        if all(c in df.columns for c in cols):
            # already there — enriched by render() earlier in this run, or genuinely
            # published by a stage. The two are NOT the same claim and the flag says which,
            # because a reader must know whether a column is the design's or the map's.
            if ours & set(cols):
                flags.append(f"{', '.join(cols)} was derived in this library earlier in "
                             f"this run, not published by a stage")
            else:
                flags.append(f"{', '.join(cols)} was PUBLISHED BY THE STAGE and is used "
                             f"as found — nothing was derived here")
        else:
            df = fn(df)
            if not isinstance(df, gpd.GeoDataFrame):
                df = gpd.GeoDataFrame(df, geometry=gdf.geometry.name, crs=gdf.crs)
            flags.append(f"derived {', '.join(cols)} in this library, "
                         f"not published by a stage")

    if view.only is not None:
        m = view.only(df)
        if m is not None:
            df = df[m.fillna(False).to_numpy()]

    fld = view.field
    if fld is None or fld not in df.columns:
        raise KeyError(f"view '{view.name}' needs field '{fld}', which the layer does not "
                       f"carry. Present: {sorted(df.columns)[:40]}")

    vals = df[fld]
    if fld == "TIER":
        vals = _normalise_tiers(vals)

    lengths = None
    if view.geom == "line":
        lengths = (pd.to_numeric(df["LEN_M"], errors="coerce")
                   if "LEN_M" in df.columns else df.geometry.length)
        lengths = lengths.fillna(0.0).to_numpy(dtype=float)

    classes: List[ClassDef] = []
    idx = np.full(len(df), -1, dtype=int)

    if view.mode == "categorical":
        if view.categories:
            declared = list(view.categories)
            seen = set()
            for i, (k, lab, rgb, w) in enumerate(declared):
                classes.append(ClassDef(k, lab, rgb, w))
                seen.add(str(k))
                idx[(vals.astype(str) == str(k)).to_numpy()] = i
            extras = sorted(set(vals.astype(str)) - seen)
            for j, k in enumerate(extras):
                classes.append(ClassDef(k, f"{k}   (not in the declared set)",
                                        golden_rgb(len(declared) + j), 1.4))
                idx[(vals.astype(str) == k).to_numpy()] = len(classes) - 1
            if extras:
                flags.append(f"{len(extras)} value(s) of {fld} were not in the declared "
                             f"palette and were given fallback colours: {extras[:8]}")
        else:
            keys = list(pd.unique(vals.astype(str).sort_values()))
            if lengths is not None and len(keys) > 1:
                order = (pd.DataFrame({"k": vals.astype(str), "L": lengths})
                         .groupby("k")["L"].sum().sort_values(ascending=False))
                keys = list(order.index)
            for i, k in enumerate(keys):
                w = view.width_range[0] + (view.width_range[1] - view.width_range[0]) * 0.25
                classes.append(ClassDef(k, str(k), golden_rgb(i), round(w, 2)))
                idx[(vals.astype(str) == k).to_numpy()] = i

    elif view.mode == "graduated":
        v = pd.to_numeric(vals, errors="coerce").to_numpy(dtype=float)
        edges = list(view.breaks or [])
        refs = list(view.break_refs or [""] * len(edges))
        refs += [""] * (len(edges) - len(refs))
        nb = len(edges) + 1
        w0, w1 = view.width_range if view.geom == "line" else view.size_range
        if view.class_t is not None and len(view.class_t) != nb:
            raise ValueError(f"view '{view.name}': class_t has {len(view.class_t)} entries "
                             f"for {nb} classes")
        if view.width_t is not None and len(view.width_t) != nb:
            raise ValueError(f"view '{view.name}': width_t has {len(view.width_t)} entries "
                             f"for {nb} classes")
        for i in range(nb):
            lo = edges[i - 1] if i > 0 else None
            hi = edges[i] if i < len(edges) else None
            t = view.class_t[i] if view.class_t else i / max(1, nb - 1)
            tw = view.width_t[i] if view.width_t else t
            ref = ""
            if i > 0 and refs[i - 1]:
                ref = refs[i - 1]
            elif i < len(edges) and refs[i]:
                ref = refs[i]
            mark = "" if ref else " (o)"
            classes.append(ClassDef(
                key=i, label=_fmt_band(lo, hi) + mark, rgb=ramp_rgb(view.ramp, t),
                width=round(w0 + (w1 - w0) * tw, 2), lo=lo, hi=hi, guideline=ref))
        with np.errstate(invalid="ignore"):
            idx = np.digitize(v, np.array(edges, dtype=float), right=False)
        idx = np.where(np.isnan(v), -1, idx).astype(int)
        n_nan = int(np.isnan(v).sum())
        if n_nan:
            flags.append(f"{n_nan:,} feature(s) have no value for {fld} and are not drawn")

    else:  # single
        classes.append(ClassDef("all", view.title, (30, 30, 30), view.width_range[0]))
        idx[:] = 0

    for i, c in enumerate(classes):
        m = idx == i
        c.n = int(m.sum())
        if lengths is not None:
            c.length_km = float(lengths[m].sum()) / 1000.0

    stats: Dict[str, Any] = {"features": int(len(df))}
    if lengths is not None:
        stats["length_km"] = round(float(lengths.sum()) / 1000.0, 2)
    if view.derive == "ground_slope":
        stats.update(_ground_fall_stats(df, lengths))
    if view.derive == "components":
        stats["components"] = int(df["SUBNET"].nunique())
    if view.derive == "drop_band":
        stats["vortex_shafts"] = int((df["DROP_BAND"].str.startswith("VORTEX")).sum())
        stats["backdrops"] = int((df["DROP_BAND"].str.startswith("backdrop")).sum())
        stats["nama_built_vortex_shafts"] = 37
    return Classified(classes, idx, df, fld, flags, stats)


def _ground_fall_stats(df: pd.DataFrame, lengths) -> Dict[str, Any]:
    """The headline W11b number: how much length runs uphill, and by how much."""
    s = pd.to_numeric(df["GRD_SLOPE"], errors="coerce").to_numpy(dtype=float)
    fall = pd.to_numeric(df["GRD_FALL_M"], errors="coerce").to_numpy(dtype=float)
    L = lengths if lengths is not None else np.ones(len(df))
    ok = ~np.isnan(s)
    up = ok & (s < 0)
    tot = float(L[ok].sum())
    return {
        "length_km_measured": round(tot / 1000.0, 2),
        "length_km_uphill": round(float(L[up].sum()) / 1000.0, 2),
        "pct_length_uphill": round(100.0 * float(L[up].sum()) / tot, 1) if tot else None,
        "cumulative_climb_m": round(float(-np.nansum(fall[fall < 0])), 0),
        "cumulative_descent_m": round(float(np.nansum(fall[fall > 0])), 0),
        "w11a_pct_length_uphill": 42.5,
    }


# ======================================================================================
# 8.  KML / KMZ
# ======================================================================================

def _esc(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _fmt(val: Any, spec: str) -> Optional[str]:
    if val is None:
        return None
    try:
        if isinstance(val, float) and math.isnan(val):
            return None
    except TypeError:
        pass
    if pd.isna(val):
        return None
    try:
        return spec.format(val)
    except (ValueError, TypeError):
        return _esc(val)


def _transform_all(geoms: Sequence[Any]) -> List[Any]:
    """Reproject every coordinate in one pyproj call. 49,000 per-geometry calls cost about
    two seconds of pure overhead; one call costs nothing, and the slicing is cheap."""
    parts: List[Tuple[int, str, int]] = []      # (geom index, part kind, n coords)
    xs: List[float] = []
    ys: List[float] = []
    rings: List[List[List[Tuple[float, float]]]] = []

    def take(coords):
        arr = list(coords)
        xs.extend(c[0] for c in arr)
        ys.extend(c[1] for c in arr)
        return len(arr)

    plan: List[List[Tuple[str, int]]] = []
    for gm in geoms:
        seq: List[Tuple[str, int]] = []
        if gm is None or gm.is_empty:
            plan.append(seq)
            continue
        gt = gm.geom_type
        if gt == "Point":
            seq.append(("pt", take([(gm.x, gm.y)])))
        elif gt == "LineString":
            seq.append(("ls", take(gm.coords)))
        elif gt == "MultiLineString":
            for p in gm.geoms:
                seq.append(("ls", take(p.coords)))
        elif gt == "Polygon":
            seq.append(("outer", take(gm.exterior.coords)))
            for r in gm.interiors:
                seq.append(("inner", take(r.coords)))
        elif gt == "MultiPolygon":
            for p in gm.geoms:
                seq.append(("outer", take(p.exterior.coords)))
                for r in p.interiors:
                    seq.append(("inner", take(r.coords)))
        elif gt == "MultiPoint":
            for p in gm.geoms:
                seq.append(("pt", take([(p.x, p.y)])))
        plan.append(seq)

    if xs:
        lon, lat = _TO_WGS.transform(np.asarray(xs), np.asarray(ys))
    else:
        lon, lat = np.array([]), np.array([])

    out = []
    cur = 0
    for seq in plan:
        made = []
        for kind, n in seq:
            made.append((kind, lon[cur:cur + n], lat[cur:cur + n]))
            cur += n
        out.append(made)
    return out


def _coord_str(lon, lat) -> str:
    return " ".join(f"{a:.7f},{b:.7f},0" for a, b in zip(lon, lat))


def _geom_kml(parts) -> str:
    """Assemble the KML geometry. Polygons are accumulated as a list so their inner rings
    land inside the right <Polygon>; everything else is a finished string."""
    if not parts:
        return ""
    tops: List[Any] = []
    cur_poly: Optional[List[str]] = None
    for kind, lon, lat in parts:
        if kind == "pt":
            tops.append(f"<Point><coordinates>{_coord_str(lon, lat)}</coordinates></Point>")
            cur_poly = None
        elif kind == "ls":
            tops.append("<LineString><tessellate>1</tessellate><coordinates>"
                        f"{_coord_str(lon, lat)}</coordinates></LineString>")
            cur_poly = None
        elif kind == "outer":
            cur_poly = ["<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing>"
                        f"<coordinates>{_coord_str(lon, lat)}</coordinates>"
                        "</LinearRing></outerBoundaryIs>"]
            tops.append(cur_poly)
        elif kind == "inner" and cur_poly is not None:
            cur_poly.append("<innerBoundaryIs><LinearRing><coordinates>"
                            f"{_coord_str(lon, lat)}</coordinates></LinearRing>"
                            "</innerBoundaryIs>")
    rendered = ["".join(t) + "</Polygon>" if isinstance(t, list) else t for t in tops]
    if len(rendered) == 1:
        return rendered[0]
    return f"<MultiGeometry>{''.join(rendered)}</MultiGeometry>"


def _region(lon, lat, min_lod: int, pad_deg: float = 0.0) -> str:
    """A KML Region. A placemark carrying one only draws when its own box occupies at least
    `min_lod` pixels on screen — which is the whole anti-clutter mechanism for labels."""
    n, s = float(np.max(lat)) + pad_deg, float(np.min(lat)) - pad_deg
    e, w = float(np.max(lon)) + pad_deg, float(np.min(lon)) - pad_deg
    if n - s < 1e-6:
        n += 5e-7
        s -= 5e-7
    if e - w < 1e-6:
        e += 5e-7
        w -= 5e-7
    return (f"<Region><LatLonAltBox><north>{n:.7f}</north><south>{s:.7f}</south>"
            f"<east>{e:.7f}</east><west>{w:.7f}</west></LatLonAltBox>"
            f"<Lod><minLodPixels>{min_lod}</minLodPixels>"
            f"<maxLodPixels>-1</maxLodPixels></Lod></Region>")


def _disc_png() -> bytes:
    """One white disc, tinted per style by KML's IconStyle <color>. One icon, every colour."""
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    import io
    fig = plt.figure(figsize=(0.64, 0.64), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.add_patch(plt.Circle((0.5, 0.5), 0.40, color="white", ec="white"))
    ax.add_patch(plt.Circle((0.5, 0.5), 0.40, fill=False, ec=(1, 1, 1, 0.85), lw=2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


@dataclass
class KmzResult:
    view: str
    path: str
    features: int
    classes: List[ClassDef]
    folders: int
    labels: int
    flags: List[str]
    stats: Dict[str, Any]
    seconds: float
    legend_png: Optional[str] = None

    def summary(self) -> str:
        bits = [f"{os.path.basename(self.path)}  {self.features:,} features",
                f"{self.folders} folders", f"{self.labels:,} labels"]
        if "length_km" in self.stats:
            bits.insert(1, f"{self.stats['length_km']:,.1f} km")
        return "  |  ".join(bits)


def _doc_description(view: View, cls: Classified, source: str) -> str:
    rows = [f"<tr><td colspan='3'><b>{_esc(view.title)}</b></td></tr>",
            f"<tr><td colspan='3'><i>{_esc(view.question)}</i></td></tr>",
            "<tr><td colspan='3'><hr/></td></tr>"]
    shown = [c for c in cls.classes if c.n > 0]
    over = 0
    if len(shown) > 40:
        shown = sorted(shown, key=lambda c: -(c.length_km or c.n))
        over, shown = len(shown) - 40, shown[:40]
    for c in shown:
        km = f"{c.length_km:,.1f} km" if c.length_km else ""
        rows.append(f"<tr><td bgcolor='{hex_color(c.rgb)}'>&nbsp;&nbsp;&nbsp;</td>"
                    f"<td>{_esc(c.label)}</td><td align='right'>{c.n:,} &nbsp; {km}</td></tr>")
    if over:
        rows.append(f"<tr><td></td><td colspan='2'><i>and {over} more — see the folder "
                    f"tree</i></td></tr>")
    rows.append("<tr><td colspan='3'><hr/></td></tr>")
    for k, v in cls.stats.items():
        rows.append(f"<tr><td></td><td>{_esc(k.replace('_', ' '))}</td>"
                    f"<td align='right'><b>{_esc(v)}</b></td></tr>")
    body = [f"<table cellpadding='3'>{''.join(rows)}</table>"]

    if view.notes:
        body.append("<p><b>Read this before you judge the map</b><br/>" +
                    "<br/>".join("&bull; " + _esc(n) for n in view.notes) + "</p>")
    ass = view.used_assumptions()
    if ass:
        body.append("<p><b>ASSUMPTIONS THIS MAP RESTS ON</b><br/>" + "<br/>".join(
            f"<b>{a.aid} &mdash; {_esc(a.headline)}</b><br/>{_esc(a.detail)}<br/>"
            f"<i>{_esc(a.consequence)}</i>" for a in ass) + "</p>")
    if cls.flags:
        body.append("<p><b>Notes on this run</b><br/>" +
                    "<br/>".join("&bull; " + _esc(f) for f in cls.flags) + "</p>")
    body.append(f"<p><font size='-1'>(o) = a drawing band, not a guideline value.<br/>"
                f"Source layer: {_esc(source)}<br/>"
                f"{PRESENT_VERSION} &middot; built {time.strftime('%Y-%m-%d %H:%M')}"
                f"</font></p>")
    return "".join(body)


def kmz(gdf: gpd.GeoDataFrame,
        view: View | str,
        out_path: str,
        source: str = "",
        legend: bool = True,
        max_features: int = 250_000,
        simplify_m: float = 0.0,
        cls: Optional[Classified] = None) -> KmzResult:
    """Write ONE view of ONE layer to a KMZ, with subfolders, a legend overlay and
    LOD-gated labels.

    `view` may be a View or the name of a registered one. `gdf` must be in EPSG:32640.
    Pass `cls` to reuse a classification the caller already computed — `render()` does, so a
    deriver never runs twice on 49,000 reaches."""
    t0 = time.time()
    if isinstance(view, str):
        view = VIEWS[view]
    if gdf.crs is not None and gdf.crs.to_epsg() != CRS_EPSG:
        gdf = gdf.to_crs(CRS_EPSG)
    if len(gdf) > max_features:
        raise ValueError(f"{len(gdf):,} features exceeds max_features={max_features:,}. "
                         f"Google Earth will crawl. Filter the layer or raise the cap "
                         f"deliberately.")
    if cls is None:
        cls = classify(gdf, view)
    df = cls.gdf
    if simplify_m > 0:
        df = df.set_geometry(df.geometry.simplify(simplify_m, preserve_topology=False))

    parts_all = _transform_all(list(df.geometry.to_numpy()))

    # ---- styles: one per (class, size/width band) --------------------------------------
    sized = _size_bands(df, view, cls)
    if sized is not None:
        band_idx, band_mul, size_fld = sized
        cls.flags.append(f"icon AREA is proportional to '{size_fld}', in five bands")
    else:
        band_idx, band_mul = _width_bands(df, view)
        size_fld = None

    styles: List[str] = []
    style_id: Dict[Tuple[int, int], str] = {}
    for ci, c in enumerate(cls.classes):
        for wi, wmul in enumerate(band_mul):
            sid = f"s{ci}_{wi}"
            style_id[(ci, wi)] = sid
            col = kml_color(c.rgb, view.opacity)
            if view.geom == "line":
                styles.append(f'<Style id="{sid}"><LineStyle><color>{col}</color>'
                              f'<width>{max(0.4, c.width * wmul):.2f}</width></LineStyle>'
                              f'<PolyStyle><fill>0</fill></PolyStyle>'
                              f'<LabelStyle><scale>0</scale></LabelStyle></Style>')
            elif view.geom == "polygon":
                styles.append(f'<Style id="{sid}"><LineStyle><color>{kml_color(c.rgb, 1.0)}'
                              f'</color><width>1.6</width></LineStyle>'
                              f'<PolyStyle><color>{kml_color(c.rgb, view.opacity)}</color>'
                              f'<fill>1</fill><outline>1</outline></PolyStyle>'
                              f'<LabelStyle><scale>0</scale></LabelStyle></Style>')
            else:
                # when a size field drives the icon, the BAND is the size; otherwise the
                # class width is, so a categorical point view still separates by symbol size
                scale = wmul if size_fld else c.width * wmul
                styles.append(f'<Style id="{sid}"><IconStyle><color>{col}</color>'
                              f'<scale>{max(0.25, scale):.2f}</scale>'
                              f'<Icon><href>files/disc.png</href></Icon></IconStyle>'
                              f'<LabelStyle><scale>0</scale></LabelStyle></Style>')
    styles.append('<Style id="lbl"><IconStyle><scale>0</scale>'
                  '<Icon><href></href></Icon></IconStyle>'
                  '<LabelStyle><color>ffffffff</color><scale>0.85</scale></LabelStyle></Style>')

    # ---- placemarks -------------------------------------------------------------------
    popup_cols = [(f, h, s) for f, h, s in view.popup if f in df.columns]
    folder_key = _folder_keys(df, view)
    rec = df.reset_index(drop=True)
    labels_wanted = _label_mask(rec, view)

    buckets: Dict[Tuple[str, ...], List[str]] = {}
    bucket_len: Dict[Tuple[str, ...], float] = {}
    label_marks: List[str] = []
    n_labels = 0
    lens = (pd.to_numeric(rec["LEN_M"], errors="coerce").fillna(0.0).to_numpy()
            if "LEN_M" in rec.columns else np.zeros(len(rec)))
    wid_idx = band_idx

    for i in range(len(rec)):
        ci = int(cls.index[i])
        if ci < 0:
            continue
        parts = parts_all[i]
        if not parts:
            continue
        sid = style_id[(ci, int(wid_idx[i]))]
        row = rec.iloc[i]
        name = _esc(row[view.label_field]) if (view.label_field and view.label_field in rec.columns
                                               and pd.notna(row[view.label_field])) else ""
        html = _balloon(row, popup_cols, view, cls.classes[ci])
        pm = (f"<Placemark><name>{name}</name>"
              f"<description><![CDATA[{html}]]></description>"
              f"<styleUrl>#{sid}</styleUrl>{_geom_kml(parts)}</Placemark>")
        key = folder_key[i]
        buckets.setdefault(key, []).append(pm)
        bucket_len[key] = bucket_len.get(key, 0.0) + float(lens[i])

        if labels_wanted[i] and n_labels < view.label_max:
            txt = (view.label_expr(row) if view.label_expr else
                   (str(row[view.label_field]) if view.label_field else ""))
            if txt and txt.lower() != "nan":
                lon = np.concatenate([p[1] for p in parts])
                lat = np.concatenate([p[2] for p in parts])
                clon, clat = float(lon.mean()), float(lat.mean())
                pad = 0.0025 if view.geom == "point" else 0.0
                label_marks.append(
                    f"<Placemark><name>{_esc(txt)}</name><styleUrl>#lbl</styleUrl>"
                    f"{_region(lon, lat, view.label_min_lod, pad)}"
                    f"<Point><coordinates>{clon:.7f},{clat:.7f},0</coordinates></Point>"
                    f"</Placemark>")
                n_labels += 1

    folders = _fold(buckets, bucket_len, view, cls)
    if label_marks:
        folders.append(f"<Folder><name>Labels ({n_labels:,}) — they appear as you zoom in"
                       f"</name><visibility>1</visibility><open>0</open>"
                       f"{''.join(label_marks)}</Folder>")

    # ---- legend overlay ----------------------------------------------------------------
    extra_files: Dict[str, bytes] = {}
    legend_path = None
    overlay = ""
    if legend:
        png = legend_png_bytes(view, cls, source)
        extra_files["files/legend.png"] = png
        legend_path = out_path[:-4] + "_legend.png"
        overlay = ('<ScreenOverlay><name>Legend</name><visibility>1</visibility>'
                   '<Icon><href>files/legend.png</href></Icon>'
                   '<overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>'
                   '<screenXY x="12" y="12" xunits="pixels" yunits="pixels"/>'
                   '<size x="0" y="0" xunits="fraction" yunits="fraction"/>'
                   '</ScreenOverlay>')
    if view.geom == "point":
        extra_files["files/disc.png"] = _disc_png()

    doc = ("<?xml version='1.0' encoding='UTF-8'?>"
           "<kml xmlns='http://www.opengis.net/kml/2.2'><Document>"
           f"<name>{_esc(view.title)}</name>"
           f"<description><![CDATA[{_doc_description(view, cls, source)}]]></description>"
           f"{''.join(styles)}{overlay}{''.join(folders)}</Document></kml>")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("doc.kml", doc)
        for k, v in extra_files.items():
            z.writestr(k, v)
    if legend_path and "files/legend.png" in extra_files:
        with open(legend_path, "wb") as fh:
            fh.write(extra_files["files/legend.png"])

    return KmzResult(view.name, out_path, int(len(rec)), cls.classes, len(folders),
                     n_labels, cls.flags, cls.stats, round(time.time() - t0, 2), legend_path)


def _balloon(row, popup_cols, view: View, cd: ClassDef) -> str:
    rows = [f"<tr><td colspan='2' bgcolor='{hex_color(cd.rgb)}'>&nbsp;</td></tr>",
            f"<tr><td colspan='2'><b>{_esc(cd.label)}</b></td></tr>"]
    for f, h, s in popup_cols:
        v = _fmt(row[f], s)
        if v is None or v == "":
            continue
        rows.append(f"<tr><td><b>{_esc(h)}</b></td><td>{_esc(v)}</td></tr>")
    tail = ""
    if "A1" in view.assumptions:
        tail = (f"<tr><td colspan='2'><font size='-1'><i>tau = 1.0 Pa ASSUMED (A1). "
                f"At 2.0 Pa the required gradient rises "
                f"{2.0 ** g('TAU_EXPONENT'):.2f}x.</i></font></td></tr>")
    return f"<table cellpadding='2'>{''.join(rows)}{tail}</table>"


def _width_bands(df: pd.DataFrame, view: View) -> Tuple[np.ndarray, List[float]]:
    """A second attribute can modulate line thickness on top of the class width. Returns the
    per-row band index and the multiplier for each band."""
    if not view.width_field or view.width_field not in df.columns or not view.width_breaks:
        return np.zeros(len(df), dtype=int), [1.0]
    v = pd.to_numeric(df[view.width_field], errors="coerce").to_numpy(dtype=float)
    idx = np.digitize(v, np.array(view.width_breaks, dtype=float))
    idx = np.where(np.isnan(v), 0, idx).astype(int)
    n = len(view.width_breaks) + 1
    return idx, [round(0.6 + 1.0 * i / max(1, n - 1), 2) for i in range(n)]


def _size_bands(df: pd.DataFrame, view: View, cls: Classified
                ) -> Optional[Tuple[np.ndarray, List[float], str]]:
    """Point icons: AREA proportional to the sizing attribute, so a station of twice the duty
    flow draws twice the ink rather than four times — sqrt on the scale, because KML's
    IconStyle <scale> is a LINEAR multiplier on the icon's edge.

    KML has no per-placemark scale, so the continuum is banded into five and each band gets
    its own style. Returns (band index per row, the scale for each band, the field used) or
    None when nothing usable is present — and in that case it SAYS SO on the legend rather
    than drawing 226 identical dots and letting the reviewer infer meaning from them."""
    if view.geom != "point" or not view.size_field:
        return None

    def usable(name: str) -> Optional[np.ndarray]:
        if name not in df.columns:
            return None
        vv = pd.to_numeric(df[name], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(vv).any():
            return None
        mx = np.nanmax(vv)
        return vv if (mx == mx and mx > 0) else None

    fld, v = view.size_field, usable(view.size_field)
    if v is None:
        for fb in view.size_fallbacks:
            vv = usable(fb)
            if vv is not None:
                cls.flags.append(
                    f"'{view.size_field}' is missing, empty or all zero, so icon size falls "
                    f"back to '{fb}'. SIZE on this map is a proxy, NOT a duty flow.")
                fld, v = fb, vv
                break
    if v is None:
        cls.flags.append(
            f"'{view.size_field}' carries no usable value and no fallback is available: every "
            f"icon is the same size. Read nothing into their size until it is populated.")
        return None

    finite = v[np.isfinite(v)]
    qs = np.unique(np.nanpercentile(finite, [20, 40, 60, 80]))
    idx = np.digitize(v, qs)
    idx = np.where(np.isnan(v), 0, idx).astype(int)
    n = len(qs) + 1
    lo, hi = view.size_range
    scales = [round(lo + (hi - lo) * math.sqrt(i / max(1, n - 1)), 2) for i in range(n)]
    return idx, scales, fld


def _folder_keys(df: pd.DataFrame, view: View) -> List[Tuple[str, ...]]:
    flds = [f for f in view.folder_fields if f in df.columns]
    if not flds:
        return [("",)] * len(df)
    cols = [df[f].astype(str).fillna("(none)").to_numpy() for f in flds[:2]]
    return list(zip(*cols)) if len(cols) > 1 else [(c,) for c in cols[0]]


def _fold(buckets, bucket_len, view: View, cls: Classified) -> List[str]:
    if list(buckets.keys()) == [("",)]:
        return [f"<Folder><name>{_esc(view.title)} ({len(buckets[('',)]):,})</name>"
                f"<open>1</open>{''.join(buckets[('',)])}</Folder>"]
    keys = list(buckets.keys())
    if view.folder_sort == "length":
        keys.sort(key=lambda k: -bucket_len.get(k, 0.0))
    elif view.folder_sort == "count":
        keys.sort(key=lambda k: -len(buckets[k]))
    else:
        keys.sort(key=lambda k: _natural(k[0]))

    tree: Dict[str, List[Tuple[Tuple[str, ...], List[str]]]] = {}
    for k in keys:
        tree.setdefault(k[0], []).append((k, buckets[k]))
    out = []
    for outer, entries in tree.items():
        inner = []
        for k, pms in entries:
            km = bucket_len.get(k, 0.0) / 1000.0
            tag = f" — {km:,.2f} km" if km else ""
            nm = f"{k[1]} ({len(pms):,}{tag})" if len(k) > 1 else f"{outer} ({len(pms):,}{tag})"
            inner.append(f"<Folder><name>{_esc(nm)}</name><visibility>1</visibility>"
                         f"{''.join(pms)}</Folder>")
        if len(entries) == 1 and len(entries[0][0]) == 1:
            out.append(inner[0])
        else:
            tot = sum(len(p) for _, p in entries)
            tkm = sum(bucket_len.get(k, 0.0) for k, _ in entries) / 1000.0
            tag = f" — {tkm:,.2f} km" if tkm else ""
            out.append(f"<Folder><name>{_esc(outer)} ({tot:,}{tag})</name>"
                       f"<open>0</open>{''.join(inner)}</Folder>")
    return out


def _natural(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(s))]


def _label_mask(df: pd.DataFrame, view: View) -> np.ndarray:
    """Which features get a name written on the map.

    When more qualify than `label_max`, the ones kept are the ones a reviewer would want:
    the longest reach, the deepest chamber, the biggest flow. Falling back to 'the first N
    rows' would label whatever the writer happened to sort by, which is meaningless and was
    what the first cut of this function did to 6,000 chambers."""
    if not (view.label_field or view.label_expr):
        return np.zeros(len(df), dtype=bool)
    m = np.ones(len(df), dtype=bool)
    if view.label_filter is not None:
        got = view.label_filter(df)
        if got is not None:
            m = got.fillna(False).to_numpy()
    if m.sum() <= view.label_max:
        return m
    rank_field = _first_field(df, ["LEN_M", "Q_PK_LS", "QPK_LS", "DROP_M", "DEPTH_M",
                                  "Q_DUTY_LS", "N_PROP", "LEN_KM"])
    if rank_field is None:
        keep = np.zeros(len(df), dtype=bool)
        idx = np.flatnonzero(m)
        keep[idx[np.linspace(0, len(idx) - 1, view.label_max).astype(int)]] = True
        return keep
    r = pd.to_numeric(df[rank_field], errors="coerce").fillna(-np.inf).to_numpy()
    cut = np.partition(r[m], -view.label_max)[-view.label_max]
    return m & (r >= cut)


# ======================================================================================
# 9.  THE LEGEND PICTURE
# ======================================================================================

def legend_png_bytes(view: View, cls: Classified, source: str = "") -> bytes:
    """The legend as a PNG, embedded in the KMZ as a ScreenOverlay and written beside it for
    the report. It carries the classes, the counts, the flags and the assumptions, because a
    map whose caption lives in another document is a map that gets misread."""
    import matplotlib
    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import io

    rows = [c for c in cls.classes if c.n > 0] or cls.classes
    # A legend with 502 rows is not a legend. Keep the biggest and say how many were dropped;
    # the KMZ folder tree carries every one of them with its own count anyway.
    LEGEND_MAX_ROWS = 28
    dropped = 0
    if len(rows) > LEGEND_MAX_ROWS:
        rows = sorted(rows, key=lambda c: -(c.length_km or c.n))
        dropped = len(rows) - LEGEND_MAX_ROWS
        rows = rows[:LEGEND_MAX_ROWS]
    notes = list(view.notes)
    if dropped:
        notes = [f"{dropped} further classes are not listed here — the KMZ folder tree "
                 f"carries all {dropped + LEGEND_MAX_ROWS} with their own counts."] + notes
    ass = view.used_assumptions()
    flags = list(cls.flags)
    stat_rows = [(k.replace("_", " "), v) for k, v in cls.stats.items()]

    def wrap(t, n=88):
        out, line = [], ""
        for w in str(t).split():
            if len(line) + len(w) + 1 > n:
                out.append(line); line = w
            else:
                line = (line + " " + w).strip()
        if line:
            out.append(line)
        return out

    note_lines: List[Tuple[str, str]] = []
    for s in stat_rows:
        note_lines.append(("stat", f"{s[0]}: {s[1]}"))
    for n in notes:
        for i, l in enumerate(wrap(n)):
            note_lines.append(("note", ("- " if i == 0 else "  ") + l))
    for a in ass:
        for i, l in enumerate(wrap(f"{a.aid} — {a.headline}. {a.detail} {a.consequence}")):
            note_lines.append(("assum", ("! " if i == 0 else "  ") + l))
    for f in flags:
        for i, l in enumerate(wrap(f)):
            note_lines.append(("flag", ("* " if i == 0 else "  ") + l))

    rh = 0.24
    h = 1.30 + rh * (len(rows) + len(note_lines) + 3)
    w = 8.2
    fig = plt.figure(figsize=(w, h), dpi=100)
    fig.patch.set_facecolor("#111417")
    fig.patch.set_alpha(0.92)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, w); ax.set_ylim(0, h)

    y = h - 0.32
    ax.text(0.22, y, view.title, color="white", fontsize=13, fontweight="bold", va="top")
    y -= 0.30
    ax.text(0.22, y, view.question, color="#9fd3ff", fontsize=9.5, va="top", style="italic")
    y -= 0.34
    for c in rows:
        ax.add_patch(Rectangle((0.24, y - 0.13), 0.42, 0.17,
                               facecolor=hex_color(c.rgb), edgecolor="#000000", lw=0.4))
        ax.text(0.78, y - 0.05, c.label, color="white", fontsize=9, va="center")
        right = f"{c.n:,}" + (f"   {c.length_km:,.1f} km" if c.length_km else "")
        ax.text(w - 0.22, y - 0.05, right, color="#cfd8dc", fontsize=8.5,
                va="center", ha="right")
        y -= rh
    y -= 0.08
    ax.plot([0.22, w - 0.22], [y, y], color="#37474f", lw=0.8)
    y -= 0.20
    palette = {"stat": "#ffffff", "note": "#b0bec5", "assum": "#ffb74d", "flag": "#ff8a80"}
    for kind, line in note_lines:
        ax.text(0.24, y, line, color=palette[kind], fontsize=8,
                va="center", fontweight="bold" if kind == "stat" else "normal")
        y -= rh * 0.78
    ax.text(0.24, 0.22, f"(o) = drawing band, not a guideline value   |   {PRESENT_VERSION}"
                        f"   |   {time.strftime('%Y-%m-%d %H:%M')}"
                        + (f"   |   {os.path.basename(source)}" if source else ""),
            color="#607d8b", fontsize=7, va="center")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()


# ======================================================================================
# 10.  QGIS
#      This library runs OUTSIDE QGIS, on geopandas. So the QGIS half is a plan plus a
#      generated PyQGIS script. The script builds the renderers from the same class list
#      the KMZ used, then asks QGIS itself to write the .qml — QGIS writes a better QML
#      than any hand-rolled XML, and it cannot go stale against a QGIS version.
# ======================================================================================

# The satellite hybrid the project already uses, read from the live project on 2026-09-03.
# CLAUDE.md rule 4: hybrid backdrop at 30 % opacity.
BASEMAP = {
    "name": "Google satellite hydbrid",
    "provider": "wms",
    "source": ("crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/"
               "lyrs%3Dy%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0"),
    "opacity": 0.30,
}

# CLAUDE.md rule 4: MoH_Plots is the land-use display layer on every map.
CONTEXT_LAYERS = [
    {"display": "MoH_Plots (land use)", "name": "MoH_Plots",
     "path": r"D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/SHP/MoHUP_DATA/MoH_Plots.shp",
     # 40 %: heavy enough to read land use, light enough that the design still wins. At 55 %
     # the plot fill swallowed the sewers through the middle of Ibri.
     "visible": True, "opacity": 0.30},
    {"display": "Towns", "name": "Towns",
     "path": r"D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/SHP/Towns/Towns.shp",
     "visible": False, "opacity": 1.0},
]


def _wrap_label(text: str, width: int = 52) -> str:
    """Insert newlines at word boundaries. QGIS's legend wraps only where it is told to."""
    out, line = [], ""
    for w in str(text).split():
        if line and len(line) + 1 + len(w) > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return "\n".join(out)


def spec_for_qgis(view: View, cls: Classified) -> Dict[str, Any]:
    """The renderer, as JSON. The SAME class list the KMZ drew, so the two cannot drift."""
    out: Dict[str, Any] = {
        "name": view.name, "title": view.title, "question": view.question,
        "geom": view.geom, "mode": view.mode, "field": cls.field,
        "opacity": view.opacity,
        "classes": [{"key": None if isinstance(c.key, (np.integer,)) and view.mode == "graduated"
                     else (c.key if not isinstance(c.key, np.generic) else c.key.item()),
                     # QGIS's legend column is 112 mm and does not wrap on its own; the
                     # break points are inserted here and the layout is told to wrap on
                     # them, so a label carrying its guideline page is not truncated to
                     # "...(G203-p3" — which is worse than no citation at all.
                     "label": _wrap_label(c.legend_text()), "rgb": list(c.rgb),
                     "width": float(c.width),
                     "lo": None if c.lo is None else float(c.lo),
                     "hi": None if c.hi is None else float(c.hi),
                     "n": int(c.n)} for c in cls.classes],
        "label": None,
        "notes": list(view.notes),
        "assumptions": [a.aid + " — " + a.headline for a in view.used_assumptions()],
        "flags": list(cls.flags),
        "stats": {k: (v.item() if isinstance(v, np.generic) else v)
                  for k, v in cls.stats.items()},
    }
    if view.label_field:
        out["label"] = {"field": view.label_field, "size": 8.0,
                        # a label every 100 m of screen is legible; below that it is a smear
                        "min_scale": 25000, "buffer": True}
    return out


def qgis_plan(results: Sequence[Tuple[View, Classified, str, str]],
              group: str = "Claude W11b",
              subgroup: str = "",
              qml_dir: str = "",
              layouts: Sequence[str] = ()) -> Dict[str, Any]:
    """Assemble everything the QGIS loader needs.

    `results` is a list of (view, classified, layer_path, layer_name)."""
    layers = []
    for view, cls, path, lname in results:
        # ALWAYS absolute. QGIS resolves a relative path against the .qgz, not against the
        # caller's working directory, so a relative path here loads nothing and says nothing.
        path = os.path.abspath(path).replace("\\", "/")
        layers.append({
            "display": f"W11b {view.title}",
            "path": path, "layer": lname,
            "visible": view.priority <= 20,
            "spec": spec_for_qgis(view, cls),
            "qml": os.path.abspath(os.path.join(qml_dir or os.path.dirname(path),
                                                f"W11b_{view.name}.qml")).replace("\\", "/"),
            "priority": view.priority,
        })
    layers.sort(key=lambda d: d["priority"])
    return {
        "version": PRESENT_VERSION,
        "group": group,
        "subgroup": subgroup,
        "basemap": BASEMAP,
        "context": CONTEXT_LAYERS,
        "layers": layers,
        "layouts": list(layouts),
        "banner": _banner(),
    }


def _banner() -> str:
    return (f"tau = 1.0 Pa ASSUMED (A1; at 2.0 Pa gradients x"
            f"{2.0 ** g('TAU_EXPONENT'):.2f})  |  DN>1200 per G203-p32 T13 (A4)  |  "
            f"72 trunk chambers in a class 5/6 wadi: risk ACCEPTED (A5)")


_QGIS_LOADER = r'''
# --- generated by w11b.present. Run inside QGIS (Python console, or the qgis MCP). --------
import json, os
from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer, QgsSymbol,
                       QgsRendererCategory, QgsCategorizedSymbolRenderer,
                       QgsRendererRange, QgsGraduatedSymbolRenderer,
                       QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
                       QgsVectorLayerSimpleLabeling, QgsLayerTreeGroup,
                       QgsLayoutItemMap, QgsLayoutItemScaleBar, QgsLayoutItemLegend,
                       QgsLayoutItemLabel, QgsPrintLayout, QgsLayoutSize, QgsLayoutPoint)
from qgis.PyQt.QtGui import QColor, QFont

PLAN = json.loads(r"""__PLAN_JSON__""")
proj = QgsProject.instance()
root = proj.layerTreeRoot()
report = {"added": [], "styled": [], "qml": [], "skipped": [], "layouts": []}


def _geom_name(gtype):
    # QGIS 3.44 returns an IntEnum whose __str__ is the NUMBER: str(GeometryType.Point)
    # is "0", not "Point". Matching on str() therefore fell through to the polygon branch
    # for every layer, and NOTHING got its size or width set - 49,000 chambers all drew at
    # the 2.0 mm default and the trunk was as thin as a lateral. Use .name where the
    # binding provides it and the documented ordinal where it does not.
    n = getattr(gtype, "name", None)
    if not n:
        n = {0: "Point", 1: "Line", 2: "Polygon"}.get(int(gtype), "Line")
    return str(n).lower()


def _sym(gtype, rgb, width, opacity):
    s = QgsSymbol.defaultSymbol(gtype)
    s.setColor(QColor(*rgb))
    name = _geom_name(gtype)
    if "line" in name:
        try:
            s.setWidth(max(0.16, width * 0.22))
        except Exception:
            pass
    elif "point" in name:
        try:
            s.setSize(max(0.30, width * 2.2))
            s.symbolLayer(0).setStrokeColor(QColor(20, 20, 20))
            s.symbolLayer(0).setStrokeWidth(0.14)
        except Exception:
            pass
    else:
        try:
            s.symbolLayer(0).setStrokeColor(QColor(*rgb).darker(150))
            s.symbolLayer(0).setStrokeWidth(0.3)
        except Exception:
            pass
    s.setOpacity(float(opacity))
    return s


def apply_spec(lyr, spec):
    gt = lyr.geometryType()
    if spec["mode"] == "graduated":
        ranges = []
        for c in spec["classes"]:
            lo = c["lo"] if c["lo"] is not None else -1e18
            hi = c["hi"] if c["hi"] is not None else 1e18
            ranges.append(QgsRendererRange(lo, hi,
                          _sym(gt, c["rgb"], c["width"], spec["opacity"]), c["label"]))
        r = QgsGraduatedSymbolRenderer(spec["field"], ranges)
    else:
        cats = []
        for c in spec["classes"]:
            cats.append(QgsRendererCategory(
                c["key"], _sym(gt, c["rgb"], c["width"], spec["opacity"]), c["label"]))
        r = QgsCategorizedSymbolRenderer(spec["field"], cats)
    lyr.setRenderer(r)

    lab = spec.get("label")
    if lab and lab["field"] in [f.name() for f in lyr.fields()]:
        st = QgsPalLayerSettings()
        st.fieldName = lab["field"]
        tf = QgsTextFormat()
        tf.setFont(QFont("Segoe UI", 9))
        tf.setSize(float(lab["size"]))
        tf.setColor(QColor(255, 255, 255))
        buf = QgsTextBufferSettings(); buf.setEnabled(True); buf.setSize(0.9)
        buf.setColor(QColor(0, 0, 0)); tf.setBuffer(buf)
        st.setFormat(tf)
        # non-overlapping by construction: QGIS drops a label it cannot place clear of
        # another, and the scale gate stops it trying at a zoom where nothing would fit.
        st.scaleVisibility = True
        st.maximumScale = 1
        st.minimumScale = float(lab["min_scale"])
        try:
            is_line = "line" in _geom_name(lyr.geometryType())
            st.placement = (QgsPalLayerSettings.Placement.Line if is_line
                            else QgsPalLayerSettings.Placement.AroundPoint)
        except Exception:
            pass
        lyr.setLabeling(QgsVectorLayerSimpleLabeling(st))
        lyr.setLabelsEnabled(True)
    lyr.setCustomProperty("w11b_question", spec.get("question", ""))
    lyr.setCustomProperty("w11b_flags", " | ".join(spec.get("assumptions", [])))
    lyr.triggerRepaint()


def find_group(parent, name):
    for ch in parent.children():
        if isinstance(ch, QgsLayerTreeGroup) and ch.name() == name:
            return ch
    return parent.addGroup(name)


grp = find_group(root, PLAN["group"])
if PLAN.get("subgroup"):
    grp = find_group(grp, PLAN["subgroup"])

# ---- the design layers ----------------------------------------------------------------
for spec in PLAN["layers"]:
    uri = spec["path"]
    if uri.lower().endswith(".gpkg"):
        uri = uri + "|layername=" + spec["layer"]
    lyr = QgsVectorLayer(uri, spec["display"], "ogr")
    if not lyr.isValid():
        report["skipped"].append([spec["display"], "layer would not load: " + uri])
        continue
    proj.addMapLayer(lyr, False)
    grp.insertLayer(0, lyr)
    node = grp.findLayer(lyr.id())
    if node:
        node.setItemVisibilityChecked(bool(spec["visible"]))
    report["added"].append(spec["display"])
    try:
        apply_spec(lyr, spec["spec"])
        report["styled"].append(spec["display"])
    except Exception as e:
        report["skipped"].append([spec["display"], "styling failed: %r" % (e,)])
    try:
        os.makedirs(os.path.dirname(spec["qml"]), exist_ok=True)
        lyr.saveNamedStyle(spec["qml"])
        report["qml"].append(spec["qml"])
    except Exception as e:
        report["skipped"].append([spec["display"], "qml save failed: %r" % (e,)])

# ---- context: land use, towns ----------------------------------------------------------
ctxgrp = find_group(grp, "Context")
have = {l.name() for l in proj.mapLayers().values()}
for c in PLAN["context"]:
    existing = [l for l in proj.mapLayers().values() if l.name() == c["name"]]
    if existing:
        lyr = existing[0]
        node = root.findLayer(lyr.id())
        if node is None:
            proj.addMapLayer(lyr, False); ctxgrp.addLayer(lyr)
    else:
        if not os.path.exists(c["path"]):
            report["skipped"].append([c["display"], "missing: " + c["path"]]); continue
        lyr = QgsVectorLayer(c["path"], c["display"], "ogr")
        if not lyr.isValid():
            report["skipped"].append([c["display"], "invalid"]); continue
        proj.addMapLayer(lyr, False); ctxgrp.addLayer(lyr)
        n = ctxgrp.findLayer(lyr.id())
        if n:
            n.setItemVisibilityChecked(bool(c["visible"]))
    try:
        lyr.setOpacity(float(c["opacity"]))
    except Exception:
        pass

# ---- basemap: satellite hybrid at 30 % (CLAUDE.md rule 4) --------------------------------
bm = PLAN["basemap"]
found = [l for l in proj.mapLayers().values() if l.name() == bm["name"]]
if found:
    base = found[0]
else:
    base = QgsRasterLayer(bm["source"], bm["name"], bm["provider"])
    if base.isValid():
        proj.addMapLayer(base, False)
        root.addLayer(base)
    else:
        base = None
        report["skipped"].append([bm["name"], "basemap would not load"])
if base is not None:
    base.renderer().setOpacity(float(bm["opacity"]))
    base.triggerRepaint()
    node = root.findLayer(base.id())
    if node:
        node.setItemVisibilityChecked(True)
    report["added"].append(bm["name"] + " @ %d%%" % int(bm["opacity"] * 100))

# ---- layouts: saved INTO the project, per CLAUDE.md rule 3 -------------------------------
def build_layout(name, layer_display, banner):
    mgr = proj.layoutManager()
    for lo in mgr.printLayouts():
        if lo.name() == name:
            mgr.removeLayout(lo)
    lay = QgsPrintLayout(proj)
    lay.initializeDefaults()
    lay.setName(name)
    pg = lay.pageCollection().page(0)
    pg.setPageSize(QgsLayoutSize(420, 297))          # A3 landscape

    lyrs = [l for l in proj.mapLayers().values() if l.name() == layer_display]
    # The map must be told WHICH layers to draw and to KEEP that set. Without it a layout
    # renders whatever happens to be ticked in the tree the day someone opens the project,
    # which is how the first cut of this produced a beautiful map of the wrong data.
    stack = list(lyrs)
    for c in PLAN["context"]:
        stack += [l for l in proj.mapLayers().values()
                  if l.name() in (c["name"], c["display"])]
    stack += [l for l in proj.mapLayers().values() if l.name() == PLAN["basemap"]["name"]]

    m = QgsLayoutItemMap(lay)
    lay.addLayoutItem(m)
    m.setLayers(stack)
    m.setKeepLayerSet(True)

    # Fit the FRAME to the data's aspect ratio inside the space available, so the sheet is
    # not two thirds white with the map letterboxed in the top of it.
    ax, ay, aw, ah = 10.0, 26.0, 280.0, 259.0
    fw, fh = aw, ah
    e = None
    if lyrs:
        e = lyrs[0].extent()
        e.scale(1.06)
        if e.height() > 0:
            r = e.width() / e.height()
            fw, fh = (aw, aw / r) if r > aw / ah else (ah * r, ah)
    ay = ay + max(0.0, (ah - fh) / 2.0)              # centre the block on the sheet
    m.attemptMove(QgsLayoutPoint(ax, ay))
    m.attemptResize(QgsLayoutSize(fw, fh))
    # setExtent LAST. Setting it before the resize and then re-zooming produced a NaN
    # extent and a blank sheet: QGIS re-derives the extent from the frame, so the frame has
    # to be its final size first.
    if e is not None:
        m.setExtent(e)
    m.setFrameEnabled(True)
    m.setBackgroundColor(QColor(255, 255, 255))
    tf = QFont("Segoe UI", 16); tf.setBold(True)
    t = QgsLayoutItemLabel(lay); t.setText(name); t.setFont(tf)
    t.adjustSizeToText(); lay.addLayoutItem(t); t.attemptMove(QgsLayoutPoint(10, 8))
    b = QgsLayoutItemLabel(lay); b.setText(banner); b.setFont(QFont("Segoe UI", 7))
    b.attemptResize(QgsLayoutSize(400, 8)); lay.addLayoutItem(b)
    b.attemptMove(QgsLayoutPoint(10, 19))
    sb = QgsLayoutItemScaleBar(lay)
    sb.setStyle("Single Box")
    sb.setLinkedMap(m)
    try:
        from qgis.core import Qgis
        sb.applyDefaultSize(Qgis.DistanceUnit.Kilometers)
    except Exception:
        try:
            from qgis.core import QgsUnitTypes
            sb.applyDefaultSize(QgsUnitTypes.DistanceKilometers)
        except Exception:
            sb.applyDefaultSize()
    sb.setNumberOfSegments(4)
    sb.setNumberOfSegmentsLeft(0)
    # non-overlapping labels: give the bar real room and a small font, and let QGIS lay the
    # numbers out at the segment ends rather than crowding them under a 2 mm box.
    sb.setFont(QFont("Segoe UI", 7))
    try:
        sb.setLabelBarSpace(1.6)
        sb.setBoxContentSpace(1.2)
        sb.setHeight(2.6)
    except Exception:
        pass
    sb.setBackgroundEnabled(True)
    sb.setBackgroundColor(QColor(255, 255, 255, 190))
    lay.addLayoutItem(sb)
    sb.attemptMove(QgsLayoutPoint(ax + 4, ay + fh - 12))     # inside the map, bottom-left
    lg = QgsLayoutItemLegend(lay); lg.setTitle("Legend"); lg.setLinkedMap(m)
    try:
        lg.setWrapString(chr(10))   # labels carry their own break points; chr(10) rather
                                    # than an escape, because this whole block is a raw
                                    # string that gets written out as a script

    except Exception:
        pass
    lg.setAutoUpdateModel(False)
    try:
        rg = lg.model().rootGroup()
        try:
            rg.removeAllChildren()
        except Exception:
            for ch in list(rg.children()):
                rg.removeChildNode(ch)
        if lyrs:
            rg.addLayer(lyrs[0])
    except Exception:
        pass
    lg.setBackgroundEnabled(True); lg.setBackgroundColor(QColor(255, 255, 255, 220))
    lay.addLayoutItem(lg); lg.attemptMove(QgsLayoutPoint(296, 26))
    lg.attemptResize(QgsLayoutSize(112, 240))
    mgr.addLayout(lay)
    return name


for lname in PLAN.get("layouts", []):
    disp, extra = None, []
    for spec in PLAN["layers"]:
        if spec["spec"]["name"] == lname:
            disp = spec["display"]
            extra = spec["spec"].get("flags", [])
    if disp:
        # the sheet carries this view's OWN data flags, not just the project-wide banner.
        # A stations sheet whose duty flow is unpopulated has to say so on the sheet: the
        # title still promises "size by DUTY FLOW" and the reader deserves the correction
        # in the same glance.
        ban = PLAN["banner"] + ("   ||   " + "   ".join(extra) if extra else "")
        report["layouts"].append(build_layout("W11b " + lname.upper(), disp, ban))

print(json.dumps(report, indent=1))
'''


def qgis_code(plan: Dict[str, Any]) -> str:
    """The PyQGIS script for this plan. Run it inside QGIS — Python console, or over the
    qgis MCP with `execute_code`. It returns a JSON report of what it added, styled and
    skipped, so the caller can prove the load rather than assume it."""
    js = json.dumps(plan)
    if '"""' in js:
        js = js.replace('"""', '\\"\\"\\"')
    return _QGIS_LOADER.replace("__PLAN_JSON__", js)


# ======================================================================================
# 11.  THE TOP-LEVEL CALL
# ======================================================================================

@dataclass
class RenderResult:
    out_dir: str
    kmz: List[KmzResult]
    qgis_plan: Dict[str, Any]
    qgis_script: str
    skipped: List[Tuple[str, str]]
    materialised: Dict[str, str]     # view -> gpkg layer written because a field was derived

    def report(self) -> str:
        L = [f"{len(self.kmz)} KMZ written to {self.out_dir}"]
        for k in self.kmz:
            L.append("  " + k.summary())
            for f in k.flags:
                L.append("      ! " + f)
        for name, why in self.skipped:
            L.append(f"  SKIPPED {name}: {why}")
        return "\n".join(L)


def _load(src) -> gpd.GeoDataFrame:
    if isinstance(src, gpd.GeoDataFrame):
        return src
    if isinstance(src, (tuple, list)) and len(src) == 2:
        return gpd.read_file(src[0], layer=src[1])
    return gpd.read_file(src)


def render(layers: Dict[str, Any],
           out_dir: str,
           views: Optional[Sequence[str]] = None,
           prefix: str = "W11b",
           group: str = "Claude W11b",
           subgroup: str = "",
           layouts: Sequence[str] = (),
           legend: bool = True,
           max_features: int = 250_000) -> RenderResult:
    """Build every view that the supplied layers can support.

    layers   {"reaches": path | (gpkg, layername) | GeoDataFrame, "nodes": ..., "stations":
             ..., "rising_mains": ..., "packages": ..., "servicing": ...}
    views    names from `list_views()`; None means all of them.

    A view whose layer or field is missing is SKIPPED WITH A REASON, never silently dropped.
    That is the whole difference between this and a pipeline that quietly draws less than it
    claims to."""
    os.makedirs(out_dir, exist_ok=True)
    names = list(views) if views else list_views()
    out: List[KmzResult] = []
    skipped: List[Tuple[str, str]] = []
    plan_rows: List[Tuple[View, Classified, str, str]] = []
    materialised: Dict[str, str] = {}
    mat_gpkg = os.path.join(out_dir, f"{prefix}_present.gpkg").replace("\\", "/")

    # Work role by role, not view by view. Seven views of `reaches` want five derived
    # columns between them; deriving per view ran a union-find over 49,000 edges four times
    # and wrote four near-identical copies of the layer — 107 MB of GeoPackage for what is
    # one enriched layer. The enrichment happens once and every view of that role shares it.
    by_role: Dict[str, List[str]] = {}
    for nm in names:
        v = VIEWS[nm]
        if v.role not in layers:
            skipped.append((nm, f"no '{v.role}' layer supplied"))
            continue
        by_role.setdefault(v.role, []).append(nm)

    for role, vnames in by_role.items():
        try:
            gdf = _load(layers[role])
        except Exception as e:
            for nm in vnames:
                skipped.append((nm, f"the '{role}' layer would not load: {e}"))
            continue
        if len(gdf) == 0:
            for nm in vnames:
                skipped.append((nm, f"the '{role}' layer is empty (0 features)"))
            continue

        enriched = gdf
        added: List[str] = []
        for nm in vnames:
            v = VIEWS[nm]
            if not v.derive:
                continue
            fn, cols = DERIVERS[v.derive]
            if all(c in enriched.columns for c in cols):
                continue
            try:
                got = fn(enriched)
                if not isinstance(got, gpd.GeoDataFrame):
                    got = gpd.GeoDataFrame(got, geometry=gdf.geometry.name, crs=gdf.crs)
                added += [c for c in got.columns if c not in enriched.columns]
                enriched = got
            except Exception as e:
                skipped.append((nm, f"deriver '{v.derive}' failed: {type(e).__name__}: {e}"))

        src = str(layers[role])[:160]
        qpath, qlayer = _materialise(layers[role], role, enriched, added, mat_gpkg,
                                     materialised)
        for nm in vnames:
            v = VIEWS[nm]
            if any(nm == s[0] for s in skipped):
                continue
            try:
                path = os.path.join(out_dir, f"{prefix}_{nm}.kmz")
                cls = classify(enriched, v, derived_here=added)   # once, both consumers
                out.append(kmz(enriched, v, path, source=src, legend=legend,
                               max_features=max_features, cls=cls))
                plan_rows.append((v, cls, qpath, qlayer))
            except Exception as e:
                skipped.append((nm, f"{type(e).__name__}: {e}"))

    plan = qgis_plan(plan_rows, group=group, subgroup=subgroup, qml_dir=out_dir,
                     layouts=layouts)
    script = qgis_code(plan)
    with open(os.path.join(out_dir, f"qgis_load_{prefix}.py"), "w", encoding="utf-8") as fh:
        fh.write(script)
    with open(os.path.join(out_dir, f"{prefix}_present_index.json"), "w", encoding="utf-8") as fh:
        json.dump({"version": PRESENT_VERSION,
                   "built": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "banner": _banner(),
                   "kmz": [{"view": k.view, "file": os.path.basename(k.path),
                            "question": VIEWS[k.view].question,
                            "features": k.features, "folders": k.folders,
                            "labels": k.labels, "flags": k.flags,
                            "stats": {kk: (vv.item() if isinstance(vv, np.generic) else vv)
                                      for kk, vv in k.stats.items()}} for k in out],
                   "skipped": [{"view": a, "why": b} for a, b in skipped],
                   "materialised": materialised,
                   "assumptions": {a.aid: {"headline": a.headline, "detail": a.detail,
                                           "consequence": a.consequence}
                                   for a in ASSUMPTIONS.values()}},
                  fh, indent=1)
    return RenderResult(out_dir, out, plan, script, skipped, materialised)


def _materialise(src, role: str, enriched: gpd.GeoDataFrame, added: List[str],
                 mat_gpkg: str, materialised: Dict[str, str]) -> Tuple[str, str]:
    """Where QGIS should point.

    Straight at the stage's own layer when nothing was derived — the honest default, because
    a QGIS project reading a copy will not notice the next time a stage reruns. Only when
    this library added a column does it write an enriched copy, ONE per role, and record in
    `materialised` which columns are ours rather than the stage's."""
    if not added:
        if isinstance(src, (tuple, list)) and len(src) == 2:
            return str(src[0]).replace("\\", "/"), str(src[1])
        if isinstance(src, str):
            return src.replace("\\", "/"), os.path.splitext(os.path.basename(src))[0]
    gcol = enriched.geometry.name
    keep = [c for c in enriched.columns if c != gcol]
    enriched[keep + [gcol]].to_file(mat_gpkg, layer=role, driver="GPKG")
    materialised[role] = f"{mat_gpkg}|{role}   (added by present.py: {', '.join(added)})"
    return mat_gpkg, role


# ======================================================================================
# 12.  CLI / self-test
# ======================================================================================

def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="w11b.present — build the KMZ set and the QGIS loader from a layer set.")
    ap.add_argument("--gpkg", help="a GeoPackage holding reaches / nodes / stations / ...")
    ap.add_argument("--out", help="output directory (required unless --catalogue/--verify)")
    ap.add_argument("--views", default="", help="comma-separated; default all")
    ap.add_argument("--prefix", default="W11b")
    ap.add_argument("--group", default="Claude W11b")
    ap.add_argument("--subgroup", default="")
    ap.add_argument("--layouts", default="", help="comma-separated view names to lay out")
    ap.add_argument("--catalogue", action="store_true", help="print the view catalogue and exit")
    ap.add_argument("--verify", action="store_true",
                    help="cross-check every quoted number against w11b.criteria and exit")
    a = ap.parse_args(argv)
    if a.catalogue:
        print(describe_views())
        return 0
    if a.verify:
        bad = verify_against_criteria()
        print("\n".join(bad) if bad else
              f"present.py agrees with w11b.criteria on all "
              f"{len(_CRITERIA_ALIASES)} overlapping values")
        return 1 if bad else 0
    if not a.out:
        ap.error("--out is required unless --catalogue or --verify")
    if not a.gpkg:
        ap.error("--gpkg is required unless --catalogue or --verify")
    import fiona
    have = set(fiona.listlayers(a.gpkg))
    roles = {r: (a.gpkg, r) for r in
             ("reaches", "nodes", "stations", "rising_mains", "packages", "servicing",
              "connections", "corridors") if r in have}
    res = render(roles, a.out,
                 views=[s.strip() for s in a.views.split(",") if s.strip()] or None,
                 prefix=a.prefix, group=a.group, subgroup=a.subgroup,
                 layouts=[s.strip() for s in a.layouts.split(",") if s.strip()])
    print(res.report())
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
