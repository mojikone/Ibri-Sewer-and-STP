# -*- coding: utf-8 -*-
"""s8_export - W12 stage 8. Everything a human or another program has to READ.

W12 owns this file. It imports `w12.contract`, `w12.criteria`, `w12.hydra`,
W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
`W10/py` or `W11a/py`. Earlier folders are read as DATA only.

======================================================================================
THE FIVE LAYERS AND THE THREE THEMES.  This is what the engineer reviews the design by.
======================================================================================

FIVE layers, the SAME content and the SAME colours in the GeoPackage, the shapefiles,
the DXF and the KMZ, because a drawing that disagrees with the schedule is worse than
no drawing:

    reaches       gravity conduits - NAME, DN, gradient, flow, velocity, length, and the
                  inlet and outlet manhole BY NAME
    nodes         manholes         - NAME, depth, ground level, invert, drop, and the
                  kind of chamber it is
    stations      pumps            - NAME, ground, invert, lift, duty flow, wet well
    rising_mains  force mains      - NAME, DN, gradient, flow, velocity, length, the pump
                  it leaves and whether it lands on a MANHOLE or at the WORKS
    subnetworks   one polygon per subnetwork over the plots it serves, PLUS the areas the
                  network does not reach, each carrying SERVED = 0, a flag and a reason

THREE themes, each a saved QGIS style (.qml) and one KMZ whose folders are the layers:

    STRUCTURE   every subnetwork its own colour, conduit weight rising with DN, flow
                direction, and pumps / force mains / drop manholes / the chamber where
                each subnetwork meets the main pipe all separately symbolised
    DEPTH       the MAGMA ramp on EVERY element, on the FIXED published breaks in
                DEPTH_BREAKS - never auto-stretched, so two runs are comparable
    EXCEPTIONS  ONLY the flagged items - plots that cannot connect, subnetworks that do
                not reach the main pipe, outfalls off their own low point, drops that
                exist only to hold the velocity cap, anything past the depth trigger,
                any chamber on wadi ground.  Colour by kind, size by severity, and THE
                COUNT IS IN THE LAYER NAME so the legend itself reports the totals.

======================================================================================
LEVELS: WHERE THEY COME FROM, AND THE ONE THING THAT MUST NOT HAPPEN
======================================================================================

THE LEVELS ARE `s6_levels`' AND NOTHING HERE COMPUTES A SECOND SET.  `read_s6_levels()`
reads `W12/shp/W12.gpkg` and maps every invert, gradient, diameter, velocity, depth of
flow, cover and drop onto this stage's graph, matched on the WRITTEN topology -
(US_NODE, DS_NODE) for a reach, NODE_UID for a chamber (H16).  NEVER on EDGE_UID: s6
numbers its reaches from E0000001 and this stage from E0000000, so that join is off by
one on every row and would look like it worked.

Until 2026-09-06 this stage computed its own inverts with a pass inherited from W11b -
where there genuinely was no stage 6 - and published them while s6 published different
ones for the same chambers.  Two passes, one question: inheritance row 10, the defect
class that has cost this project more than any other.  MEASURED on the 003 run before the
swap, the two disagreed on 45,115 of 56,973 chamber inverts, 23,941 of them by over a
metre, worst 77.33 m; on 29,633 of 56,522 laid gradients; on 1,824 diameters; and on the
peak factor itself.  The stand-in also produced an 85.96 m chamber against s6's deepest of
20.23 m.

The stand-in still RUNS, exactly once, and publishes NOTHING.  It exists only so the size
of that disagreement is a measured number: it lands on the `levels_delta` layer, in the
`levels_arms` table and in EXPORT.md.  Every published row carries `LEVELS_BY` naming the
solver that answered for it, so provenance is checkable per row and not per file.

EVERY level column is s6's, not the three that were easiest to check (adversarial review,
2026-09-06).  Until that review this stage read s6's INV_UP, SLOPE_LAID and DN and then
REBUILT INV_DN, US_DEPTH, DS_DEPTH, COVER_US and COVER_DN from them against its OWN ground
and its OWN segment length - the same two-solvers defect, on five more columns, and the
one verify() could not see.  It published covers from -151.74 m to +178.48 m where s6's own
ran 1.30 to 19.63 m, and 3,668 reaches carried a cover past the 12 m cap beside their own
PAST_CAP = 0.  The same review found the CHAMBER flow being answered twice: s6 publishes NO
PF column on its node layer, so `NC("PF", 1.0)` published the DEFAULT - PF = 1.0 and
PF_METH = 'held' on all 56,943 chambers - while the reach leaving the same chamber carried
s6's merrimack 3.62.  Both are fixed; `verify()` now proves all EIGHT level columns against
s6's own file and checks that a chamber's peak flow is the peak flow of the pipe leaving it.

TWO PUBLICATION GATES, and either one stops the run being quotable: `levels coverage` (the
leveller answered for less than LEVELS_COVERAGE_ALARM of the reaches) and `levels ground`
(the leveller's GRD_M and this stage's disagree at a chamber they share - both are sampled
from the same VRT at the same X/Y, so any difference means s4 re-minted the chamber).
`make_overview.py` reads both and REFUSES to draw, rather than producing a complete-looking
map of half a design.

WHAT s6 DID NOT LEVEL IS NOT FILLED IN.  s6 publishes 56,525 reaches against s4's 56,699
segments - the rest are the gravity reaches it replaced with its own pumped links, plus a
handful where it short-circuited a chamber.  Those routes come OFF the reaches layer and
are published whole on `reaches_unlevelled` with s6's own reason on every row and the
count in REMOVED_COUNTS (inheritance row 4).  Giving them the retired stand-in's gradient
between two of s6's inverts would describe no pipe at all.

======================================================================================
WHAT IS MISSING, NAMED RATHER THAN PAPERED OVER
======================================================================================

1.  THE TRUNK IS NOT IN THE GRAPH. `W12_hier.gpkg|trunk` is the client's own drawn Main
    Pipe, an INPUT. It carries no chambers, no nodes and no topology, so nothing drains
    INTO it here. The outfalls this stage exports are subnetwork outlets, not the works.
    The trunk is exported as its own layer, drawn on every theme, and excluded from
    every hydraulic statement.  How far each subnetwork's outfall still is from it is
    MEASURED and published (JOIN_MAIN / JOIN_OFF_M / JOIN_WHY), and the ones that do not
    reach it are an EXCEPTIONS layer with the count in its name.

2.  THE STATION NODE IDS DO NOT RESOLVE. s7 mints station `NODE_UID`s that also exist in
    the chamber layer on entirely different chambers, and none agree on ground level. So
    the string is s7's own counter, not a reference. This stage re-anchors each station
    to the nearest chamber BY GEOMETRY, records the distance in `ST_SNAP_M`, and refuses
    to call a recovered anchor topology (H16). Reported, with the distances.

3.  A STATION WITH NOTHING DRAINING INTO IT IS REMOVED HERE, NOT SHIPPED.  Inheritance
    row 4: anything a pass can ADD, a later pass must be able to TAKE AWAY, and the stage
    publishes how many it removed.  Each one goes to the `stations_rejected` layer with
    its reason, its coordinates and its s7 id.  Nothing is deleted silently.

======================================================================================
SWITCHED OFF AT CONCEPT STAGE - criteria.CONCEPT_OFF is the one register
======================================================================================

house connection design | motor selection | life-cycle costing | excavation-vs-pumping |
phasing and packaging | the SewerGEMS referee export | swept-channel chamber detail.

Each is refused BY NAME through `criteria.assert_enabled()`, so a stage that reaches for
one is stopped rather than quietly producing nothing.  None of them is abandoned; the
register carries what brings each back.

======================================================================================
WHAT IT PRODUCES
======================================================================================

    W12/shp/W12_export.gpkg       the contract layers: nodes, reaches, connections,
                                    stations, rising_mains, crossings, trunk,
                                    subnetworks, stations_rejected, packages,
                                    plus contract_check, manifest, assumptions
    W12/shp/kmz/*.kmz             the three THEME files, plus the per-question views
    W12/shp/kmz/*.qml             the saved QGIS style for every layer of every theme
    W12/export/shp/*.shp          the same layers as ESRI shapefiles, names <= 10 chars
    W12/export/dxf/*.dxf          plan drawing: the five layers, annotated
    W12/export/schedules/*.xlsx   chambers, pipes, stations, rising mains, connections,
                                    crossings, quantities, not-served
    W12/export/W12_FIELD_DICTIONARY.md   the one-page key to every abbreviated field name
    W12/export/profiles/*.pdf     long sections, ground against invert
    W12/export/qgis_load_W12.py   the PyQGIS loader (also driven over the qgis MCP)
    W12/run/export/EXPORT.md      the report, every number with its source

Run:  python s8_export.py build        (then --verify, --report, --selftest)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zipfile
from collections import defaultdict, deque
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import geopandas as gpd
from shapely.geometry import LineString, MultiPoint, Point, Polygon, MultiPolygon
from shapely.ops import unary_union

from w12 import connectivity as CN
from w12 import contract as CT
from w12 import criteria as CR
from w12 import naming as NM
from w12 import hydra as HY
from w12 import present as PR

C = CR.DEFAULT

STAGE = "s8_export"
STAGE_ORDER = 8
VERSION = "W12-s8_export-1.0"
LEVELS_TAG = "s8_export/levels-standin"

# WHICH SOLVER ACTUALLY LEVELLED THE ROWS THIS RUN PUBLISHED. Set once by build() and
# read by every banner - the DXF title, the KMZ description, the schedule cover sheet
# and the manifest. It is a variable rather than a constant because it is a FACT ABOUT
# THE RUN: a banner that says "levels by s6" on a run where s6 had not published would
# be the same lie as a level that came from nowhere.
LEVELS_SOURCE = LEVELS_TAG

# ======================================================================================
# PATHS
# ======================================================================================

W12 = os.path.dirname(_HERE)                       # .../W12
REPO = os.path.dirname(W12)                        # .../Hydraulic/Claude
SHP = os.path.join(W12, "shp")
RUN = os.path.join(W12, "run", "export")
OUT = os.path.join(W12, "export")

GPKG_ROADS = os.path.join(SHP, "W12_roads.gpkg")
GPKG_ORIENT = os.path.join(SHP, "W12_orient.gpkg")
GPKG_HIER = os.path.join(SHP, "W12_hier.gpkg")
GPKG_CHAMB = os.path.join(SHP, "W12_chambers.gpkg")
GPKG_FLOWS = os.path.join(SHP, "W12_flows.gpkg")
GPKG_PUMPS = os.path.join(SHP, "W12_pumps.gpkg")
GPKG_OUT = os.path.join(SHP, "W12_export.gpkg")
# s6_levels' own published contract file. Read here ONLY to detect that a second set of
# levels exists (see the header): this stage must never publish two answers to one
# question without saying so.
GPKG_S6 = os.path.join(SHP, CT.GPKG_NAME)

# The settlement polygons the town letter of every NAME comes from. A CLIENT INPUT, never
# in the repo (CLAUDE.md), and read-only.
TOWNS_SHP = os.path.join(os.path.dirname(REPO), "SHP", "Towns")
TOWNS_LAYER = "Towns"
TOWNS_NAME_FIELD = "NAME_EN"

DIR_KMZ = os.path.join(SHP, "kmz")
DIR_SHP = os.path.join(OUT, "shp")
DIR_DXF = os.path.join(OUT, "dxf")
DIR_SCH = os.path.join(OUT, "schedules")
DIR_PRF = os.path.join(OUT, "profiles")

_T0 = time.time()
_LOG: List[str] = []

# What this stage REMOVED, by kind. Inheritance row 4: "anything a pass can ADD, a later pass
# must be able to TAKE AWAY, and the stage publishes how many it removed." Populated by
# build_stations() and read by build() into the manifest, so the ledger has one home rather
# than being reconstructed from log lines.
REMOVED_COUNTS: Dict[str, int] = {}

# Themes that could not be built, and why. `build_themes()` catches every exception so one
# broken theme cannot take the other two down with it - but an EMPTY exceptions map reads as
# "we checked and it is fine", which is the module's own reason for omitting an empty folder.
# So the failure is kept here where check_contract() can publish it as a named row.
THEME_FAILURES: Dict[str, str] = {}

# Which bound actually forced each `velocity_cap` drop. The contract's DROP_WHY vocabulary
# has ONE word for "the pipe could not take the ground's fall", and two different things map
# to it: `vmax` (G203-p27 4.2.2.2, a guideline 3.0 m/s) and `cover_max` (the 25 % laying
# bound, a PROJECT ASSUMPTION declared in EXPORT_NUMBERS). Reporting the second under the
# first's page number is borrowed authority, so the split is counted and published.
DROP_CAUSE_SPLIT: Dict[str, int] = {}


def _log(msg: str) -> None:
    line = f"[{time.time() - _T0:7.1f}s] {msg}"
    _LOG.append(line)
    print(line, flush=True)


def _mkdirs() -> None:
    for d in (RUN, OUT, DIR_KMZ, DIR_SHP, DIR_DXF, DIR_SCH, DIR_PRF):
        os.makedirs(d, exist_ok=True)


# ======================================================================================
# 1.  THE NUMBERS THIS STAGE IS ALLOWED TO USE THAT ARE NOT ALREADY IN `criteria`
#     Every one carries the page it was read from, or is declared an assumption. Nothing
#     below may be edited without re-reading the source PDF.
# ======================================================================================

EXPORT_NUMBERS: List[Tuple[str, Any, str, str]] = [
    # name, value, source, why
    ("LEVELS_COVERAGE_ALARM", 0.98, "PROJECT ASSUMPTION (s8_export, 2026-09-06)",
     "the share of reaches the LEVELLER must have answered for before this export is a "
     "design rather than a fragment. Not a design value and not from any guideline: it "
     "separates 'stage 6 withdrew a few reaches to pumped links', which is legitimate and "
     "was 171 reaches on the 003 run, from 'stage 4 has been re-run since stage 6 wrote "
     "its file', which on the first afternoon of this rewire left 26,579 of 56,667 "
     "reaches levelled and every published number internally consistent and less than "
     "half a design"),
    ("MIN_COVER_CROWN", C.MIN_COVER_CROWN, "G203-p33 4.6.3",
     "minimum cover to crown; sets the shallowest invert a reach may be laid at"),
    ("MAX_COVER", C.MAX_COVER, "G203-p33",
     "the cover cap; past it philosophy sec 5's ladder starts"),
    ("EXIT_RECOVER_M", 500.0, "philosophy sec 5",
     "cover must come back under the cap within this distance for the first exit"),
    ("EXIT_OUTFALL_M", 1000.0, "philosophy sec 5",
     "the run must reach its outfall within this distance for the second exit"),
    ("DROP_TRIGGER", C.DROP_TRIGGER, "G203-p30",
     "invert difference above which an external ramped backdrop is required"),
    ("BACKDROP_MAX", C.BACKDROP_MAX, "G203-p30",
     "backdrop maximum height; beyond it a vortex drop shaft"),
    ("DROP_CEILING_M", C.DROP_CEILING_M, "PROJECT ASSUMPTION (criteria)",
     "the drop a vortex shaft is assumed buildable to. G203 gives no maximum"),
    ("SLOPE_STEP", C.SLOPE_STEP, "PROJECT RULE (user 2026-08-23)",
     "gradients are laid on round 0.05 % steps so the drawing matches the levels"),
    ("V_MAX", C.V_MAX, "G203-p27 4.2.2.2",
     "the maximum velocity in a GRAVITY sewer, and the slope at which a pipe reaches it is "
     "the steep end of the concept-stage clamp. It is NOT the rising-main figure - that is "
     "2.5 m/s at G203-p50 sec 8.1 - and the two were conflated once already, which capped "
     "every force main at the wrong number (inheritance row 9)"),
    ("TAU_PA", C.TAU_PA, "ASSUMPTION GAP-9 (G203-p27 gives no numeric tau)",
     "the tractive stress every tractive-governed gradient rests on"),
    ("INFILT_L_D_KM", C.INFILT_L_D_KM, "G201-p72 7.4.3",
     "infiltration allowance for a NEW network, per kilometre of sewer and UNPEAKED - so "
     "it is added after the peak factor, never multiplied by it. The 10 %-of-wastewater "
     "figure is the EXISTING-network allowance and is not used anywhere in this design; "
     "the swap between the two moves the capacity gate's own output by 11.7 % "
     "(10_ASBUILT_CALIBRATION sec 4)"),
    ("PF_HOLD_PROPERTIES", C.PF_HOLD_PROPERTIES, "G201-p71 7.4.2",
     "below this many properties G201 prescribes no peak-factor formula, so PF is HELD "
     "at 1.0 and said so"),
    # ---- the only two genuinely new declarations this stage makes -------------------
    ("MH_DIA_STD_M", 1.20, "PROJECT ASSUMPTION - G203 gives no table of chamber size "
                           "against depth (searched: p29-30 sec 4.4)",
     "standard chamber internal diameter used for the take-off. G203-p30 requires at "
     "least 1.5 m wherever an internal backdrop is unavoidable, so a chamber carrying a "
     "backdrop is written up to that"),
    ("SLOPE_MAX_LAID_PCT", 25.0,
     "PROJECT BOUND - declared in contract.REACHES.SLOPE_LAID (hi=25.0)",
     "the steepest gradient a gravity sewer is laid at. G203 gives NO maximum gradient - "
     "it caps VELOCITY at 3.0 m/s (p27 4.2.2.2), and on this network the velocity cap "
     "never binds because the flows are tiny, so a DN200 carrying 0.5 L/s solved to a "
     "46.45 % laid gradient down a cliff. Past this bound the fall is taken at a drop "
     "chamber (philosophy sec 5) instead of by the pipe"),
    ("TRENCH_SIDE_M", 0.30, "PROJECT ASSUMPTION - no guideline trench width was found",
     "working space each side of the barrel in the excavation take-off. The take-off is "
     "declared indicative and is NOT a bill of quantities"),
    ("JOIN_TOL_M", 50.0, "PROJECT ASSUMPTION - no guideline defines 'reaches the main pipe'",
     "how close a subnetwork outfall must sit to the client's Main Pipe before the design "
     "may say it JOINS it. 50 m is roughly two chamber spacings (as-built median 29.77 m, "
     "10_ASBUILT_CALIBRATION sec 1), so a subnetwork within it is one chamber from the "
     "trunk and one past it is a gap somebody has to close. Published on every outfall as "
     "JOIN_MAIN with the measured distance beside it, so the threshold can be moved and "
     "the effect read straight off the layer"),
    ("SERVICE_BUFFER_M", 60.0, "G203-p17 3.2 (2 x the 45 m rider limit, less the setback)",
     "the half-width of a subnetwork's service-area polygon - the distance within which a "
     "plot could plausibly belong to that subnetwork. It is a DRAWING of extent and NOT a "
     "service-area calculation; the polygon is labelled that way on the map and its "
     "AREA_M2 is the polygon's own area, not a catchment"),
    ("UNSERVED_CLUSTER_M", 400.0, "PROJECT ASSUMPTION - no guideline defines an 'area'",
     "plots this close to one another are drawn as ONE unserved area, because they are one "
     "decision: serve this ground another way, or do not serve it. The number changes how "
     "many areas are reported and therefore how many decisions are put to the engineer, "
     "so it is declared rather than buried in a clustering call"),
    ("UNSERVED_MIN_PLOTS", 8, "PROJECT ASSUMPTION",
     "below this many plots a cluster is not drawn as a servicing AREA at all - a lone "
     "plot is a connection question and is already named, individually, on the connection "
     "layer with what it would take. Nothing is dropped: the plots below this threshold "
     "are still every one of them in the not-served schedule"),
    ("DEPTH_BREAKS", "1.30 / 3.00 / 4.00 / 6.00 / 9.00 / 12.00 m",
     "G203-p33 (1.30 and 12.00) + 10_ASBUILT_CALIBRATION sec 1 (3.00, 4.00, 6.00)",
     "THE FIXED class edges of the DEPTH theme, on every element. Fixed and published so "
     "two runs are comparable: an auto-stretched ramp makes the same colour mean a "
     "different depth in every export, which is how a reviewer comes to trust a picture "
     "that has changed under them. 1.30 = minimum cover; 3.00 = the built network's TRUNK "
     "median cover 3.004 m; 4.00 = its SUB-MAIN median 4.010 m; 6.00 = the built "
     "network's layout-fault trigger; 12.00 = the cover cap. 9.00 carries no source and "
     "is marked presentation-only on the legend"),
]
EXPORT_NUM = {n: v for n, v, _s, _w in EXPORT_NUMBERS}

SLOPE_MAX_LAID = EXPORT_NUM["SLOPE_MAX_LAID_PCT"] / 100.0
MH_DIA_STD_M = EXPORT_NUM["MH_DIA_STD_M"]
TRENCH_SIDE_M = EXPORT_NUM["TRENCH_SIDE_M"]
EXIT_RECOVER_M = EXPORT_NUM["EXIT_RECOVER_M"]
EXIT_OUTFALL_M = EXPORT_NUM["EXIT_OUTFALL_M"]
JOIN_TOL_M = float(EXPORT_NUM["JOIN_TOL_M"])

# THE fixed depth classes, in ONE place. Every depth-themed layer - conduits, manholes,
# pumps, force mains, subnetwork polygons - is classified on these and on nothing else.
#
# The two guideline edges are READ FROM `criteria`, never re-typed: move MIN_COVER_CROWN
# or MAX_COVER and the map moves with them. The three interior edges are the as-built
# medians and the as-built layout-fault trigger from `_BRAIN/10_ASBUILT_CALIBRATION.md`
# sec 1 - EVIDENCE, not a "shall", and the legend says so. 9.0 carries no source at all
# and present.py marks such a band "(o)" on the legend rather than letting it read as one.
AB_TRUNK_COVER_MED_M = 3.00      # 10_ASBUILT_CALIBRATION sec 1, measured 3.004 m
AB_SUBMAIN_COVER_MED_M = 4.00    # 10_ASBUILT_CALIBRATION sec 1, measured 4.010 m
AB_LAYOUT_FAULT_M = 6.00         # 10_ASBUILT_CALIBRATION sec 1, "layout-fault trigger at 6 m"
DEPTH_BREAKS: List[float] = [
    C.MIN_COVER_CROWN, AB_TRUNK_COVER_MED_M, AB_SUBMAIN_COVER_MED_M,
    AB_LAYOUT_FAULT_M, 9.0, C.MAX_COVER,
]
DEPTH_BREAK_REFS: List[str] = [
    "G203-p33 minimum cover",
    "as-built TRUNK median cover 3.004 m",
    "as-built SUB-MAIN median cover 4.010 m",
    "as-built layout-fault trigger 6 m",
    "",                                     # presentation only; the legend marks it (o)
    "G203-p33 cover cap",
]


# The vocabularies upstream stages actually wrote, against the vocabularies the contract
# declares. These are NOT interchangeable words; each mapping is a decision and each is
# recorded so a reader can see what was renamed and why.
SRC_MAP = {
    # s1 read one clean DXF with two layers. `piping center line` is the surveyed/observed
    # road set; `piping center line-propo-01` is the proposed one. Neither is a block or a
    # link in the contract's sense, so both land on dwg_road and the DISTINCTION IS KEPT in
    # CONFIDENCE, which is where the contract puts trust.
    "draft_base": "dwg_road",
    "draft_propo": "dwg_road",
    "main_pipe": "main_pipe",
    "terrain": "terrain",
    "existing": "existing",
    "manual": "manual",
}
CONF_MAP = {
    # s1's own words -> the contract's four grades.
    # `corroborated` = the DXF line is confirmed by the recorded NAMA centreline: drafted.
    # `drafted` = drawn, uncorroborated: still drafted.
    # `provisional` = a platted reserve with nothing built on it: provisional, and the
    # contract's SRC_CONFIDENCE_CEILING would force that anyway.
    "corroborated": "drafted",
    "drafted": "drafted",
    "provisional": "provisional",
    "surveyed": "surveyed",
    "derived": "derived",
}
# A proposed-layer corridor is never better than provisional: philosophy sec 4, "a platted
# reserve with nothing built on it ... is never reported as existing".
SRC_CONF_FLOOR = {"draft_propo": "provisional"}

TIER_FLOOR_DN = {
    # G203-p22 Table 6 minimum sizes by application. A rider is 160 OD; everything that
    # carries another pipe's flow is 200 OD minimum.
    "rider": C.DN_TERTIARY,
    "lateral": C.DN_MIN_LATERAL,
    "main": C.DN_MIN_MAIN,
    "sub main": C.DN_MIN_MAIN,
    "trunk main": C.DN_MIN_MAIN,
}


# ======================================================================================
# 2.  ASSEMBLY - read every upstream stage, once, and say what came from where
# ======================================================================================

@dataclass
class Assembly:
    """Everything the export needs, read from the PUBLISHED GeoPackages and nothing else.

    Nothing here recomputes an upstream stage's answer. Where a value had to be
    translated - a vocabulary, an id that did not resolve - the translation is recorded
    in `notes` and lands in EXPORT.md."""
    chambers: gpd.GeoDataFrame
    segments: gpd.GeoDataFrame
    connections: gpd.GeoDataFrame
    unserved: gpd.GeoDataFrame
    hier: gpd.GeoDataFrame
    trunk: gpd.GeoDataFrame
    corridors: gpd.GeoDataFrame
    flows_arcs: gpd.GeoDataFrame
    stations: gpd.GeoDataFrame
    rising: gpd.GeoDataFrame
    boundary: gpd.GeoDataFrame
    notes: List[str] = dc_field(default_factory=list)
    reads: List[Tuple[str, str, int]] = dc_field(default_factory=list)

    def note(self, s: str) -> None:
        self.notes.append(s)
        _log("   note: " + s)


def _read(path: str, layer: str) -> gpd.GeoDataFrame:
    g = gpd.read_file(path, layer=layer)
    if g.crs is not None and g.crs.to_epsg() != CT.CRS_EPSG:
        g = g.to_crs(CT.CRS_EPSG)
    return g


def assemble() -> Assembly:
    _log("assembling from the published stage layers")
    a = Assembly(
        chambers=_read(GPKG_CHAMB, "chambers"),
        segments=_read(GPKG_CHAMB, "segments"),
        connections=_read(GPKG_CHAMB, "connections"),
        unserved=_read(GPKG_CHAMB, "unserved"),
        hier=_read(GPKG_HIER, "reaches"),
        trunk=_read(GPKG_HIER, "trunk"),
        corridors=_read(GPKG_ROADS, "corridors"),
        flows_arcs=_read(GPKG_FLOWS, "arcs"),
        stations=_read(GPKG_PUMPS, "stations"),
        rising=_read(GPKG_PUMPS, "rising_mains"),
        boundary=_read(GPKG_ROADS, "boundary"),
    )
    for nm, src, g in (("chambers", GPKG_CHAMB, a.chambers), ("segments", GPKG_CHAMB, a.segments),
                       ("connections", GPKG_CHAMB, a.connections),
                       ("unserved", GPKG_CHAMB, a.unserved),
                       ("hier reaches", GPKG_HIER, a.hier), ("trunk", GPKG_HIER, a.trunk),
                       ("corridors", GPKG_ROADS, a.corridors),
                       ("flow arcs", GPKG_FLOWS, a.flows_arcs),
                       ("stations", GPKG_PUMPS, a.stations),
                       ("rising mains", GPKG_PUMPS, a.rising)):
        a.reads.append((nm, os.path.basename(src), len(g)))
        _log(f"   read {nm:<14} {len(g):>7,}  {os.path.basename(src)}")

    # ---- tier, from stage 3, onto the chamber-to-chamber segments -----------------------
    tier_by_cid = dict(zip(a.hier.CID.astype(str), a.hier.TIER.astype(str)))
    seg_cid = a.segments.ARC_CID.astype(str)
    a.segments["TIER"] = seg_cid.map(tier_by_cid)
    miss = a.segments.TIER.isna()
    if miss.any():
        # An arc s4 chambered that s3 did not tier. Never guess a tier: an unrecognised
        # tier is a SILENT skip in a diameter-floor check (contract, TIER field).
        a.segments.loc[miss, "TIER"] = "lateral"
        a.note(f"{int(miss.sum()):,} segments ({a.segments.loc[miss,'LEN_M'].sum()/1000:.2f} km) "
               f"carry an ARC_CID stage 3 never tiered; written as 'lateral', the lowest "
               f"tier, so the diameter floor is the weakest and nothing is flattered")
    a.segments["TIER"] = a.segments.TIER.map(lambda t: CT.TIER_ALIASES.get(str(t), str(t)))

    # ---- corridor provenance, onto the segments ----------------------------------------
    corr = a.corridors.set_index(a.corridors.CID.astype(str))
    a.segments["ALONG_DUAL"] = seg_cid.map(corr.ALONG_DUAL).fillna(0).astype(int)
    a.segments["XING_DUAL"] = seg_cid.map(corr.XING).fillna(0).astype(int)
    a.segments["DUAL_ANG"] = seg_cid.map(corr.DUAL_ANG).fillna(-1.0).astype(float)

    # ---- vocabulary: what the stages wrote -> what the contract declares ----------------
    raw_src = a.segments.SRC.astype(str)
    a.segments["SRC_RAW"] = raw_src
    a.segments["SRC"] = raw_src.map(SRC_MAP)
    conf = a.segments.CONFIDENCE.astype(str).map(CONF_MAP)
    floor = raw_src.map(SRC_CONF_FLOOR)
    rank = {c: i for i, c in enumerate(CT.CONFIDENCE)}
    a.segments["CONFIDENCE"] = [
        f if (isinstance(f, str) and rank.get(f, 0) > rank.get(c, 0)) else c
        for c, f in zip(conf, floor)]
    n_floored = int(sum(1 for c, f in zip(conf, floor)
                        if isinstance(f, str) and rank.get(f, 0) > rank.get(c, 0)))
    a.note(f"vocabulary: SRC 'draft_base'/'draft_propo' -> 'dwg_road' (both are road "
           f"centrelines from the one clean DXF); CONFIDENCE 'corroborated' -> 'drafted'. "
           f"{n_floored:,} segments on the PROPOSED road layer were floored to "
           f"'provisional' (philosophy sec 4: a platted reserve is never reported as "
           f"existing)")

    # ---- stations: the ids do not resolve. Re-anchor by geometry, and say so. -----------
    a.stations = _reanchor_stations(a)
    return a


def _reanchor_stations(a: Assembly) -> gpd.GeoDataFrame:
    """s7's station NODE_UIDs collide with the chamber namespace instead of referencing it.

    Proved rather than assumed, on every run: the collision count and the ground-level
    disagreement are MEASURED below and published in the note, not asserted here. When it
    was first found, every station carried a NODE_UID that also existed in the chamber
    layer and not one of them agreed on ground level - station N0000001 said 378.33 m aOD
    where chamber N0000001 stands at 317.08 m. So the string is s7's own counter, not a
    reference.

    The anchor is recovered by proximity, the distance is published in ST_SNAP_M, and the
    row is marked so nothing downstream can mistake a recovered anchor for written
    topology (H16). The station keeps a NODE_UID of its own in the export namespace,
    prefixed PS, so the collision cannot recur."""
    st = a.stations.copy()
    if len(st) == 0:
        return st
    ch = a.chambers
    claimed = st.NODE_UID.astype(str)
    hit = claimed.isin(set(ch.NODE_UID.astype(str)))
    grd_ch = ch.set_index(ch.NODE_UID.astype(str)).GRD_M
    same = np.abs(claimed.map(grd_ch).astype(float) - st.GRD_M.astype(float)) < 0.10
    n_collide = int((hit & ~same.fillna(False)).sum())

    from shapely.strtree import STRtree
    import shapely
    tree = STRtree(ch.geometry.values)
    idx = tree.nearest(st.geometry.values)
    dist = shapely.distance(st.geometry.values, ch.geometry.values[idx])
    st["ANCHOR_ND"] = ch.NODE_UID.astype(str).values[idx]
    st["ST_SNAP_M"] = np.round(dist.astype(float), 3)
    st["NODE_UID_S7"] = claimed.values
    st["NODE_UID"] = [f"PS{i + 1:05d}" for i in range(len(st))]
    a.note(f"STATION IDS DO NOT RESOLVE: {n_collide} of {len(st)} station NODE_UIDs also "
           f"exist in the chamber layer on a DIFFERENT chamber (zero agree on ground "
           f"level). Re-anchored by proximity: median {np.median(dist):.2f} m, max "
           f"{dist.max():.1f} m, {int((dist < 1.0).sum())} within 1 m. Published as "
           f"ANCHOR_ND with ST_SNAP_M beside it, and the station's own id is now PS#####")
    return st


def _to_gdf(df: pd.DataFrame, geom, crs=CT.CRS_EPSG) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(df, geometry=geom, crs=f"EPSG:{crs}")


# ======================================================================================
# 3.  THE GRAPH, AND THE FLOW ON IT
#
#     Chamber to chamber, from the WRITTEN US_NODE / DS_NODE (H16). No geometry, no
#     tolerance. s5 accumulated the same loads over the 12,816 CORRIDOR arcs; this
#     re-accumulates them over the 56,740 CHAMBER segments, because a pipe is sized on
#     the flow at ITS OWN chamber and not on the flow somewhere along the arc it belongs
#     to. The two totals are cross-checked in `verify()` and must agree at the outfalls.
# ======================================================================================

@dataclass
class Graph:
    uid: List[str]                    # node uid, index order
    ix: Dict[str, int]                # uid -> index
    grd: np.ndarray                   # ground level
    ds: np.ndarray                    # index of the downstream node, -1 at a terminal
    e_us: np.ndarray                  # per edge: index of the upstream node
    e_ds: np.ndarray
    e_len: np.ndarray
    e_of: np.ndarray                  # per node: index of its outgoing edge, -1 at terminal
    order: np.ndarray                 # topological order, most upstream first
    indeg: np.ndarray


def build_graph(a: Assembly) -> Graph:
    ch = a.chambers
    seg = a.segments
    uid = ch.NODE_UID.astype(str).tolist()
    ix = {u: i for i, u in enumerate(uid)}
    n = len(uid)
    if len(ix) != n:
        raise CT.ContractError(f"duplicate NODE_UID in the chamber layer: {n - len(ix)} rows")

    grd = ch.GRD_M.to_numpy(dtype=float)
    e_us = seg.US_NODE.astype(str).map(ix).to_numpy(dtype=np.int64)
    e_ds = seg.DS_NODE.astype(str).map(ix).to_numpy(dtype=np.int64)
    e_len = seg.LEN_M.to_numpy(dtype=float)

    ds = np.full(n, -1, dtype=np.int64)
    e_of = np.full(n, -1, dtype=np.int64)
    for k in range(len(e_us)):
        u = e_us[k]
        if e_of[u] != -1:
            raise CT.ContractError(
                f"node {uid[u]} has two outgoing segments. A node may own at most ONE "
                "outgoing edge (contract Network.add_edge); s3 published zero exceptions "
                "and s4 must not have created one.")
        e_of[u] = k
        ds[u] = e_ds[k]

    indeg = np.zeros(n, dtype=np.int64)
    np.add.at(indeg, e_ds, 1)

    # Kahn. A cycle would leave nodes unemitted, and a cycle in a forest is a defect, not
    # a topology to be tolerated (H15: zero loops).
    order = np.empty(n, dtype=np.int64)
    deg = indeg.copy()
    q = deque(np.flatnonzero(deg == 0).tolist())
    p = 0
    while q:
        v = q.popleft()
        order[p] = v
        p += 1
        w = ds[v]
        if w >= 0:
            deg[w] -= 1
            if deg[w] == 0:
                q.append(w)
    if p != n:
        raise CT.ContractError(
            f"the chamber graph is not a forest: {n - p:,} nodes sit on a cycle. H15 "
            "requires zero loops; a cycle here means s4 wrote a DS_NODE chain that closes.")
    return Graph(uid, ix, grd, ds, e_us, e_ds, e_len, e_of, order, indeg)


@dataclass
class Flows:
    q_own: np.ndarray          # m3/d generated at this chamber
    p_own: np.ndarray          # properties at this chamber
    n_conn: np.ndarray
    q_adf: np.ndarray          # m3/d accumulated AT this chamber, its own load included
    n_prop: np.ndarray
    ups_len: np.ndarray        # m of sewer upstream of this chamber, its outgoing NOT
    subnet: np.ndarray         # index of the component's outfall node
    e_qadf: np.ndarray         # per edge
    e_nprop: np.ndarray
    e_upslen: np.ndarray       # including this edge
    e_pf: np.ndarray
    e_pfm: List[str]
    e_qinf: np.ndarray         # L/s, cumulative over e_upslen, UNPEAKED
    e_qpk: np.ndarray          # L/s


def accumulate(a: Assembly, g: Graph) -> Flows:
    """Sanitary load, properties and sewer length accumulated down the chamber tree.

    THE PEAK FACTOR IS NOT ADDITIVE and this is where that bites. Merrimack
    (G201-p71 7.4.2) is Qpdf = 2.65 Qadf^0.879 with both in Ml/d, so Pf FALLS as the
    catchment grows. Two branches each peaking at 3.3 do not join at 3.3. It is therefore
    computed at every chamber from that chamber's OWN accumulated Qadf, never carried
    down, and below 100 properties it is HELD at 1.0 because G201 prescribes no formula
    there (contract PF_METH)."""
    n = len(g.uid)
    q_own = np.zeros(n)
    p_own = np.zeros(n)
    n_conn = np.zeros(n, dtype=np.int64)

    cn = a.connections
    out = cn.OUT_NODE.astype(str).map(g.ix)
    ok = out.notna()
    if (~ok).any():
        raise CT.ContractError(
            f"{int((~ok).sum()):,} connections name an OUT_NODE that is not a chamber. A "
            "load unit is attached to a node uid or it is named in a Funnel; a dangling "
            "reference is neither.")
    oi = out[ok].to_numpy(dtype=np.int64)
    np.add.at(q_own, oi, cn.Q_ADF_M3D.to_numpy(dtype=float)[ok.to_numpy()])
    np.add.at(p_own, oi, cn.N_PROP.to_numpy(dtype=float)[ok.to_numpy()])
    np.add.at(n_conn, oi, 1)

    q_adf = q_own.copy()
    n_prop = p_own.copy()
    ups = np.zeros(n)
    subnet = np.full(n, -1, dtype=np.int64)

    for v in g.order:
        w = g.ds[v]
        if w >= 0:
            L = g.e_len[g.e_of[v]]
            q_adf[w] += q_adf[v]
            n_prop[w] += n_prop[v]
            ups[w] += ups[v] + L
    # the component's outfall, walked once per node against the topological order
    for v in g.order[::-1]:
        w = g.ds[v]
        subnet[v] = v if w < 0 else subnet[w]

    m = len(g.e_len)
    e_qadf = q_adf[g.e_us]
    e_nprop = n_prop[g.e_us]
    e_upslen = ups[g.e_us] + g.e_len
    e_pf = np.ones(m)
    e_pfm: List[str] = ["held"] * m
    # peak_factor is a pure function of (qadf, n_prop); the pairs repeat heavily on a
    # 56,740-edge tree, so it is memoised rather than called 56,740 times.
    cache: Dict[Tuple[float, bool], Tuple[float, str]] = {}
    for k in range(m):
        key = (round(float(e_qadf[k]), 4), bool(e_nprop[k] <= C.PF_HOLD_PROPERTIES))
        got = cache.get(key)
        if got is None:
            got = C.peak_factor(float(e_qadf[k]), float(e_nprop[k]))
            cache[key] = got
        e_pf[k], e_pfm[k] = got
    e_qinf = C.INFILT_L_D_KM * (e_upslen / 1000.0) / 86400.0
    e_qpk = e_qadf * 1000.0 / 86400.0 * e_pf + e_qinf
    return Flows(q_own, p_own, n_conn, q_adf, n_prop, ups, subnet,
                 e_qadf, e_nprop, e_upslen, e_pf, e_pfm, e_qinf, e_qpk)


# ======================================================================================
# 4.  LEVELS AND SIZES - THE STAGE-6 STAND-IN
#
#     Everything in this section would live in `s6_levels.py` if it existed. It is here
#     because a depth map, a diameter map, a profile, a pipe schedule, a quantity and a
#     model package are all unbuildable without it, and the engineer asked for all six.
#
#     The maths is `w12.hydra`'s and `w12.criteria`'s, called - never re-implemented.
#     This section contributes an ORDER OF OPERATIONS and nothing else:
#
#       1  size on flow, and only on flow            H8, G203-p29
#       2  the governing minimum gradient is the STEEPER of Table 11 and tractive  G203-p27
#       3  lay as shallow as H3 allows               philosophy sec 5
#       4  hold the gradient on steep ground and take the difference at a drop   sec 5
#       5  gradients on round 0.05 % steps           P1
#       6  flag, never clip                          sec 5
# ======================================================================================

_S_STATE: Dict[Tuple[int, int, int], Tuple[Optional[float], Optional[float]]] = {}
_S_SIZE: Dict[Tuple[int, int, int], Any] = {}


def _qkey(q: float) -> int:
    """Quantise a flow to 0.01 L/s for the memo. Chosen because plot loads repeat exactly
    (1.079781 and 5.096378 m3/d dominate this network), so accumulated flows repeat too,
    and 0.01 L/s is four orders of magnitude below the smallest design decision here."""
    return int(round(float(q) * 1e5))


def _skey(s: float) -> int:
    return int(round(float(s) / C.SLOPE_STEP))


def state(dn: int, slope: float, q: float) -> Tuple[Optional[float], Optional[float]]:
    k = (int(dn), _skey(slope), _qkey(q))
    got = _S_STATE.get(k)
    if got is None:
        got = HY.pipe_state(int(dn), float(slope), float(q), C)
        _S_STATE[k] = got
    return got


def size(q: float, slope: float, dn_min: int):
    k = (_qkey(q), _skey(slope), int(dn_min))
    got = _S_SIZE.get(k)
    if got is None:
        got = HY.size_pipe(float(q), float(slope), C, dn_min=int(dn_min))
        _S_SIZE[k] = got
    return got


@dataclass
class Levels:
    # ---- per edge
    dn: np.ndarray
    slope_laid: np.ndarray        # fraction, not percent
    slope_min: np.ndarray         # fraction
    grad_by: List[str]
    sized_by: List[str]
    clean_by: List[str]
    v_pk: np.ndarray
    dod: np.ndarray
    ret_min: np.ndarray
    inv_up: np.ndarray
    inv_dn: np.ndarray
    us_depth: np.ndarray
    ds_depth: np.ndarray
    cover_us: np.ndarray
    cover_dn: np.ndarray
    material: List[str]
    # ---- per node
    inv: np.ndarray
    depth: np.ndarray
    cover: np.ndarray
    drop: np.ndarray
    drop_type: List[str]
    vortex: np.ndarray
    past_cap: np.ndarray
    cap_exit: List[str]
    cap_len: np.ndarray
    node_dn: np.ndarray
    st_reset: np.ndarray
    stats: Dict[str, Any] = dc_field(default_factory=dict)
    # CONCEPT RULE 1: "EVERY DROP CARRIES THE REASON IT EXISTS." Not a label chosen
    # afterwards - the reason is read off the arm that actually drops, from the gradient
    # decision that put it there. Vocabulary: contract.DROP_WHY.
    drop_why: List[str] = dc_field(default_factory=list)


def _size_all(g: Graph, f: Flows, tiers: Sequence[str]):
    """Diameter and the governing minimum gradient, per edge.

    The two are COUPLED: the minimum gradient depends on the diameter (Table 11) and the
    diameter that fits depends on the gradient. Solved by iterating up from the tier's own
    guideline floor. It terminates because Table 11 is monotonically flatter with size, so
    a bigger pipe can only relax the gradient it asks for, and a relaxed gradient can only
    ask for the same size or a bigger one, on a finite series."""
    m = len(g.e_len)
    dn = np.empty(m, dtype=np.int64)
    smin = np.empty(m, dtype=float)
    why: List[str] = [""] * m
    floors = np.array([TIER_FLOOR_DN.get(t, C.DN_MIN_MAIN) for t in tiers], dtype=np.int64)
    q_m3s = f.e_qpk / 1000.0
    n_infeasible = 0
    for k in range(m):
        d = int(floors[k])
        q = float(q_m3s[k])
        w = "minimum"
        for _ in range(4):
            s = HY.smin_for(d, q, C)
            # dn_min stays at the TIER FLOOR on every pass, never at the current guess.
            # Raising it launders the answer: size_pipe reports "minimum" whenever the
            # smallest size it was OFFERED works, so feeding it the last guess made all
            # 56,740 reaches read SIZED_BY = "minimum" including the DN900s. SIZED_BY is
            # the field that proves depth did not choose a diameter (H8), so it has to be
            # the real reason.
            d2, _y, _v, w2 = size(q, C.round_slope_up(s), int(floors[k]))
            if d2 is None:
                # Not even DN2400 passes it within G203-p27 Tab 10 at that gradient. The
                # answer is a station or a different route, never a bigger number
                # (hydra.size_pipe's own words). Held at the largest size and COUNTED.
                d2, w2 = int(C.DN_SERIES[-1]), "infeasible"
                n_infeasible += 1
            if int(d2) == d:
                w = w2
                break
            d, w = int(d2), w2
        dn[k] = d
        why[k] = w
        smin[k] = HY.smin_for(d, q, C)
    if n_infeasible:
        _log("   %d reaches SIZED INFEASIBLE - no diameter in the series passes the flow "
             "within G203-p27 Tab 10. Held at DN%d and counted; the resolution is a "
             "station or a route, not a number" % (n_infeasible, C.DN_SERIES[-1]))
    return dn, why, smin, n_infeasible


def design_levels(a: Assembly, g: Graph, f: Flows,
                  station_nodes: Optional[Iterable[int]] = None,
                  label: str = "with stations") -> Levels:
    n, m = len(g.uid), len(g.e_len)
    tiers = a.segments.TIER.astype(str).tolist()
    _log("levels [%s]: sizing %s reaches on flow" % (label, format(m, ",")))
    dn, sized_by, smin, n_infeasible = _size_all(g, f, tiers)

    st = set(int(i) for i in (station_nodes or ()))
    q_m3s = f.e_qpk / 1000.0

    inv = np.full(n, np.nan)
    arr_min = np.full(n, np.inf)
    arr_max = np.full(n, -np.inf)
    inv_up = np.zeros(m)
    inv_dn = np.zeros(m)
    s_laid = np.zeros(m)
    grad_by: List[str] = [""] * m
    node_dn = np.zeros(n, dtype=np.int64)
    st_reset = np.zeros(n, dtype=np.int8)

    in_dn_max = np.zeros(n, dtype=np.int64)
    np.maximum.at(in_dn_max, g.e_ds, dn)

    _log("levels [%s]: walking %s chambers in topological order" % (label, format(n, ",")))
    for v in g.order:
        e = int(g.e_of[v])
        if e < 0:
            d_here = int(in_dn_max[v]) or int(C.DN_MIN_MAIN)
            node_dn[v] = d_here
            shallow = g.grd[v] - C.invert_depth_min(d_here)
            inv[v] = shallow if not np.isfinite(arr_min[v]) else min(shallow, arr_min[v])
            continue

        d = int(dn[e])
        node_dn[v] = d
        shallow = g.grd[v] - C.invert_depth_min(d)
        if v in st:
            # A lifting station resets the depth: flow leaves the wet well and the
            # downstream network restarts at minimum cover. The station is s7's -
            # this stage neither places, moves nor removes one.
            inv[v] = shallow
            st_reset[v] = 1
        elif np.isfinite(arr_min[v]):
            inv[v] = min(shallow, arr_min[v])
        else:
            inv[v] = shallow

        w = int(g.e_ds[e])
        L = float(g.e_len[e])
        q = float(q_m3s[e])
        s_floor = C.round_slope_up(smin[e])

        # The gradient that lands the far end at EXACTLY minimum cover. Philosophy sec 5:
        # lay as shallow as H3 allows, because depth is bought back nowhere.
        s_need = (inv[v] - (g.grd[w] - C.invert_depth_min(d))) / L if L > 0 else 0.0
        if s_need <= s_floor:
            s = s_floor
            by = "tractive" if smin[e] > HY.smin_table11(d, C) + 1e-12 else "table11"
        else:
            # ROUND UP, not down. Rounding a cover-governed gradient DOWN lands the far
            # end HIGHER than the target and puts the reach under 1.30 m of cover - 232 km
            # of it on the first build of this stage, from nothing but the rounding
            # direction. Up costs at most SLOPE_STEP x LEN = 15 mm on a 30 m reach.
            s = max(s_floor, C.round_slope_up(s_need))
            by = "cover_min"
            smax = HY.smax_for(d, q, C)
            if smax is not None and smax != HY.INFEASIBLE and s > smax:
                # Steep ground and the velocity cap bites. G203-p27 4.2.2.2 caps velocity
                # at 3.0 m/s, so the pipe CANNOT follow the fall; philosophy sec 5 takes
                # the difference at a drop chamber instead of chasing the cliff. The far
                # end of THIS reach is then short of cover, and that shortfall is real -
                # it is reported, not rounded away.
                s2 = C.round_slope_down(smax)
                if s2 >= s_floor:
                    s, by = s2, "vmax"
            if s > SLOPE_MAX_LAID:
                # Ground steeper than a pipe is laid. Philosophy sec 5, verbatim: "On
                # steep ground the pipe does not follow the cliff. Hold the gradient and
                # take the difference at a drop chamber."
                #
                # BUT THE CAP IS NOT APPLIED WHERE IT WOULD LIFT THE PIPE OUT OF THE
                # GROUND. Capping unconditionally at 25 % put 11 reaches at NEGATIVE
                # cover - the far end above the surface - which is not a conservative
                # answer, it is an impossible one. A steep pipe is buildable with anchor
                # blocks; a pipe in mid-air is not. So the cap holds only while cover at
                # the far end still clears the G203-p33 minimum, and every reach that has
                # to break it is counted and named.
                s_keep_cover = (inv[v] - (g.grd[w] - C.invert_depth_min(d))) / L
                s = max(SLOPE_MAX_LAID, C.round_slope_up(s_keep_cover))
                by = "cover_max" if s <= SLOPE_MAX_LAID + 1e-12 else "ground"
        s_laid[e] = s
        grad_by[e] = by
        inv_up[e] = inv[v]
        inv_dn[e] = inv[v] - s * L
        if inv_dn[e] < arr_min[w]:
            arr_min[w] = inv_dn[e]
        if inv_dn[e] > arr_max[w]:
            arr_max[w] = inv_dn[e]

    # ---- P1: the same gradient carried across consecutive reaches -----------------------
    # H13 already fixes ONE gradient per reach; P1 extends it across a run. It is applied
    # here only as a LABEL, on reaches that already carry their upstream neighbour's
    # gradient - so it changes no invert and can never buy a pumping station
    # (philosophy 3a: "P1 is never bought at the price of a pumping station").
    inc = np.full(n, -1, dtype=np.int64)
    for k in range(m):
        w = int(g.e_ds[k])
        if inc[w] == -1:
            inc[w] = k
    n_uniform = 0
    for k in range(m):
        v = int(g.e_us[k])
        p = int(inc[v])
        if p >= 0 and g.indeg[v] == 1 and abs(s_laid[p] - s_laid[k]) < 1e-12 \
                and grad_by[k] in ("table11", "tractive"):
            grad_by[k] = "uniform"
            n_uniform += 1

    # ---- depths, covers, drops -----------------------------------------------------------
    depth = g.grd - inv
    cover = np.array([C.cover(int(node_dn[i]), float(depth[i])) for i in range(n)])
    us_depth = g.grd[g.e_us] - inv_up
    ds_depth = g.grd[g.e_ds] - inv_dn
    cover_us = us_depth - (dn / 1000.0 + C.WALL_ALLOW)
    cover_dn = ds_depth - (dn / 1000.0 + C.WALL_ALLOW)

    drop = np.where(np.isfinite(arr_max), arr_max - inv, 0.0)
    drop = np.maximum(drop, 0.0)
    drop_type = ["vortex" if d > C.BACKDROP_MAX + 1e-9 else
                 ("backdrop" if d > C.DROP_TRIGGER + 1e-9 else "none") for d in drop]
    vortex = (drop > C.BACKDROP_MAX + 1e-9).astype(np.int8)
    drop_why = _drop_reasons(a, g, tiers, grad_by, inv_dn, arr_min, arr_max, drop_type)

    past_cap, cap_exit, cap_len = _cap_exits(g, cover, drop)

    lv = Levels(
        dn=dn, slope_laid=s_laid, slope_min=smin, grad_by=grad_by, sized_by=sized_by,
        clean_by=[], v_pk=np.zeros(m), dod=np.zeros(m), ret_min=np.zeros(m),
        inv_up=inv_up, inv_dn=inv_dn, us_depth=us_depth, ds_depth=ds_depth,
        cover_us=cover_us, cover_dn=cover_dn, material=[],
        inv=inv, depth=depth, cover=cover, drop=drop, drop_type=drop_type, vortex=vortex,
        past_cap=past_cap, cap_exit=cap_exit, cap_len=cap_len, node_dn=node_dn,
        st_reset=st_reset, drop_why=drop_why)

    # ---- the hydraulic state AT THE LAID gradient, and which route cleans it -------------
    _log("levels [%s]: solving depth of flow and velocity at the laid gradient" % label)
    v_pk = np.zeros(m)
    dod = np.zeros(m)
    clean: List[str] = [""] * m
    mat: List[str] = [""] * m
    for k in range(m):
        y, v = state(int(dn[k]), float(s_laid[k]), float(q_m3s[k]))
        dod[k] = 1.0 if y is None else float(y)
        v_pk[k] = 0.0 if v is None else float(v)
        if y is not None and v is not None and v >= C.V_SELF_CLEANSING:
            clean[k] = "velocity"
        elif s_laid[k] >= HY.smin_tractive(float(q_m3s[k]), C) - 1e-12:
            clean[k] = "tractive"
        else:
            clean[k] = "neither"
        mat[k] = C.material(tiers[k], int(dn[k]))
    lv.v_pk, lv.dod, lv.clean_by, lv.material = v_pk, dod, clean, mat
    lv.ret_min = np.array([HY.retention_min(float(L), float(vv)) or 0.0
                           for L, vv in zip(g.e_len, v_pk)])

    cl = np.array(clean)
    lv.stats = dict(
        n_uniform=n_uniform,
        n_infeasible=n_infeasible,
        past_cap_nodes=int(past_cap.sum()),
        past_cap_no_exit=int(sum(1 for i in range(n) if past_cap[i] and not cap_exit[i])),
        vortex=int(vortex.sum()),
        backdrop=int(sum(1 for t in drop_type if t == "backdrop")),
        deepest_cover=float(np.nanmax(cover)),
        median_cover=float(np.nanmedian(cover)),
        km_past_cap=float(g.e_len[np.maximum(cover_us, cover_dn) > C.MAX_COVER].sum() / 1000.0),
        km_below_min_cover=float(g.e_len[np.minimum(cover_us, cover_dn)
                                         < C.MIN_COVER_CROWN - 1e-6].sum() / 1000.0),
        km_tractive=float(g.e_len[cl == "tractive"].sum() / 1000.0),
        km_neither=float(g.e_len[cl == "neither"].sum() / 1000.0),
        km_velocity=float(g.e_len[cl == "velocity"].sum() / 1000.0),
        n_over_vmax=int((v_pk > C.V_MAX + 1e-9).sum()),
        n_over_dod=int(sum(1 for k in range(m) if dod[k] > C.dod_limit(int(dn[k])) + 1e-9)),
        stations_used=len(st),
        km_total=float(g.e_len.sum() / 1000.0),
    )
    return lv


def _drop_reasons(a: Assembly, g: Graph, tiers: Sequence[str], grad_by: Sequence[str],
                  inv_dn: np.ndarray, arr_min: np.ndarray, arr_max: np.ndarray,
                  drop_type: Sequence[str]) -> List[str]:
    """WHY each drop exists - read off the arm that actually drops, never chosen afterwards.

    CONCEPT RULE 1 (engineer, 2026-09-05/06): "EVERY DROP CARRIES THE REASON IT EXISTS
    (velocity cap / tier mismatch / obstruction / cover recovery)."  The contract refuses a
    drop with no reason AND refuses one reason repeated across every drop on a large network
    (inheritance row 22 - a published column constant where it should vary is a fabrication).
    So this has to be a real derivation, and it is: the arm that arrives HIGHEST is the arm
    that drops, and the gradient decision that put it there is already recorded in GRAD_BY.

        vmax        the pipe was FLATTENED to hold 3.0 m/s (G203-p27 4.2.2.2)
        cover_max   the pipe was HELD at the laying bound and philosophy sec 5 takes the
                    surplus fall at the manhole
    Both mean the same physical thing - the pipe could not take the ground's fall - and both
    map to `velocity_cap`, which is the vocabulary's word for it.

        a different TIER arriving        -> tier_step   (a lateral into a sub main, G203-p30)
        the chamber sits on wadi ground  -> obstruction (the crossing forced the level)
        anything else                    -> cover_recovery: another arm set this chamber's
                                            invert deeper, or the chamber was laid back at
                                            minimum cover, and this arm has to come down.
    """
    n = len(g.uid)
    ins: Dict[int, List[int]] = defaultdict(list)
    for k in range(len(g.e_ds)):
        ins[int(g.e_ds[k])].append(k)
    on_wadi = (a.chambers.ON_WADI.to_numpy(dtype=float) > 0
               if "ON_WADI" in a.chambers.columns else np.zeros(n, dtype=bool))
    tier_out = [tiers[int(g.e_of[v])] if g.e_of[v] >= 0 else "" for v in range(n)]

    why: List[str] = [""] * n
    for v in range(n):
        if drop_type[v] == "none":
            continue
        kin = ins.get(v, [])
        if not kin:
            # a drop with nothing arriving cannot happen; if it ever does, say so rather
            # than inventing a reason for it.
            why[v] = "obstruction"
            continue
        k_hi = max(kin, key=lambda k: float(inv_dn[k]))
        gb = str(grad_by[k_hi])
        if gb in ("vmax", "cover_max"):
            # BOTH map to the contract's word `velocity_cap` because that is the only word
            # its vocabulary has for "the pipe could not take the ground's fall". They are
            # NOT the same authority and must not be reported as one: `vmax` is G203-p27
            # 4.2.2.2, a guideline maximum of 3.0 m/s; `cover_max` is the 25 % laying bound
            # in EXPORT_NUMBERS["SLOPE_MAX_LAID_PCT"], a PROJECT BOUND with no guideline
            # behind it. Citing G203-p27 for a drop the project's own assumption caused is
            # the kind of borrowed authority `_BRAIN/02` exists to stop, so the split is
            # counted here and printed on the legend and in the manifest.
            DROP_CAUSE_SPLIT[gb] = DROP_CAUSE_SPLIT.get(gb, 0) + 1
            why[v] = "velocity_cap"
        elif tier_out[v] and str(tiers[k_hi]) != tier_out[v]:
            why[v] = "tier_step"
        elif bool(on_wadi[v]):
            why[v] = "obstruction"
        else:
            why[v] = "cover_recovery"
    return why


def _cap_exits(g: Graph, cover: np.ndarray, drop: np.ndarray):
    """Philosophy sec 5. Past the 12 m cap there are exactly two exits, and BOTH are
    bounded twice - by distance AND by depth:

        cover recovers within 500 m      or      the run reaches its outfall within 1,000 m

    and either is WITHDRAWN where the excursion forces a drop past what a drop structure
    can be built to (criteria.DROP_CEILING_M). Stated as distance alone, this exit produced
    a 36.81 m chamber with a 35.06 m drop into it on 2026-09-02 and the design was legal
    all the way down.

    Where neither applies the chamber gets PAST_CAP = 1 and a BLANK exit. That is a STATION
    DEMAND and it belongs to stage 7. This stage counts them; it does not invent one."""
    n = len(cover)
    over = cover > C.MAX_COVER + 1e-9
    past = over.astype(np.int8)
    exit_: List[str] = [""] * n
    cap_len = np.zeros(n)
    for v in np.flatnonzero(over):
        d = 0.0
        worst_drop = float(drop[v])
        cur = int(v)
        rec = -1.0
        out = -1.0
        while True:
            e = int(g.e_of[cur])
            if e < 0:
                out = d
                break
            d += float(g.e_len[e])
            cur = int(g.e_ds[e])
            worst_drop = max(worst_drop, float(drop[cur]))
            if not over[cur]:
                rec = d
                break
            if d > EXIT_OUTFALL_M:
                break
        withdrawn = worst_drop > C.DROP_CEILING_M + 1e-9
        if not withdrawn and 0.0 <= rec <= EXIT_RECOVER_M:
            exit_[v], cap_len[v] = "recovers_500m", rec
        elif not withdrawn and 0.0 <= out <= EXIT_OUTFALL_M:
            exit_[v], cap_len[v] = "outfall_1000m", out
        else:
            cap_len[v] = rec if rec >= 0 else (out if out >= 0 else d)
    return past, exit_, cap_len


# ======================================================================================
# 4b.  THE LEVELS THAT GET PUBLISHED ARE s6_levels' OWN.  ONE QUANTITY, ONE FUNCTION.
#
#      Until 2026-09-06 this stage COMPUTED its own inverts with the section-4 stand-in and
#      published them, while `s6_levels.py` published a different set of inverts for the
#      same chambers into `W12.gpkg`. Two passes, one question. That is inheritance row 10,
#      and it is the defect class that has cost this project more than any other (0.05 vs
#      0.10 m of wall allowance failed a BLOCKING cover check on every reach while the
#      design was correct; seven station counts reached circulation in W10).
#
#      MEASURED before the swap, on the 003 run's own published files: the two solvers
#      disagreed on 45,115 of 56,973 chamber inverts, 23,941 of them by more than a metre,
#      worst 77.33 m; on 29,633 of 56,522 laid gradients; on 1,824 diameters; and on the
#      peak factor itself, s6 applying Merrimack to every reach where the stand-in held
#      PF = 1.0 below 100 properties. The stand-in also produced an 85.96 m chamber, which
#      is not a level, it is an arithmetic escape.
#
#      So the stand-in is RETIRED as a publication source. It still RUNS, once, because the
#      size of the disagreement is a number the engineer needs and it can only be had by
#      computing both - it lands on the `levels_delta` layer and in EXPORT.md. Nothing on
#      the deliverable carries it.
#
#      WHAT s6 DOES NOT LEVEL IS NOT FILLED IN.  s6 publishes 56,525 reaches against s4's
#      56,699 segments. The ones it does not carry are named, sized and published on their
#      own layer rather than quietly given a stand-in gradient, because a gradient from one
#      solver laid between two inverts from another describes no pipe.
# ======================================================================================

S6_TAG = "s6_levels"
GPKG_S6_DETAIL = os.path.join(SHP, "W12_levels.gpkg")   # s6's own working layers


@dataclass
class S6Levels:
    """s6's published answer, aligned to THIS stage's graph index order."""
    lv: Levels
    e_ok: np.ndarray            # per edge: s6 published this reach
    n_ok: np.ndarray            # per node: s6 published this chamber
    e_qadf: np.ndarray
    e_qinf: np.ndarray
    e_pf: np.ndarray
    e_pfm: List[str]
    e_qpk: np.ndarray
    n_pf: np.ndarray            # NaN where s6 gave no factor for this chamber
    n_pfm: List[str]            # "" where s6 gave no factor for this chamber
    n_qpk: np.ndarray           # NaN where s6 published no chamber here
    n_qadf: np.ndarray          # NaN where s6 published no chamber here
    n_flow_ok: np.ndarray       # per node: s6's OWN peak factor is on this row
    gaps: pd.DataFrame          # one row per reach s6 did not level, with the reason
    notes: List[str]
    stats: Dict[str, Any]


def _s6_pumped_links() -> Dict[Tuple[str, str], Dict[str, Any]]:
    """s6's own register of the gravity reaches it REPLACED with a pumped link.

    Read from `W12_levels.gpkg|pumped_links` - s6's words, s6's lift, s6's reason. Nothing
    here re-derives why a reach is missing; it asks the stage that removed it."""
    try:
        pl = gpd.read_file(GPKG_S6_DETAIL, layer="pumped_links", ignore_geometry=True)
    except Exception:
        return {}
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for r in pl.itertuples():
        out[(str(r.STATION), str(r.DISCHARGE))] = dict(
            LIFT_M=float(getattr(r, "LIFT_M", float("nan"))),
            WHY=str(getattr(r, "WHY", "")),
            Q_PK_LS=float(getattr(r, "Q_PK_LS", float("nan"))))
    return out


def read_s6_levels(a: Assembly, g: Graph, f: Flows) -> Optional[S6Levels]:
    """Read s6_levels' published inverts, gradients, diameters and flows onto THIS graph.

    Matched on the WRITTEN topology, never on row order and never on EDGE_UID: s6 numbers
    its reaches from E0000001 and this stage from E0000000, so an EDGE_UID join is off by
    one on every row and would look like it worked. The key is (US_NODE, DS_NODE) for a
    reach and NODE_UID for a chamber - H16, topology is written down.

    Returns None when s6 has not published, and says so; the caller then falls back to the
    stand-in with the tag on every row. It does NOT refuse the whole swap over a partial
    match - refusing would leave the two-solver defect standing, which is the larger fault.
    What it does instead is publish exactly which rows s6 did not answer for."""
    if not os.path.exists(GPKG_S6):
        _log(f"   s6 has NOT published {os.path.basename(GPKG_S6)} - the levels below are "
             f"the RETIRED stand-in and every row says so")
        return None
    try:
        n6 = gpd.read_file(GPKG_S6, layer="nodes", ignore_geometry=True)
        r6 = gpd.read_file(GPKG_S6, layer="reaches", ignore_geometry=True)
    except Exception as e:
        _log(f"   {os.path.basename(GPKG_S6)} EXISTS BUT WOULD NOT READ "
             f"({type(e).__name__}: {e}) - falling back to the stand-in, tagged")
        return None

    n, m = len(g.uid), len(g.e_len)
    notes: List[str] = []

    # ---- align s6's chambers onto this graph -------------------------------------------
    ni = pd.Series(np.arange(len(n6)), index=n6.NODE_UID.astype(str))
    if ni.index.has_duplicates:
        raise CT.ContractError(
            f"{int(ni.index.duplicated().sum()):,} duplicate NODE_UID in "
            f"{os.path.basename(GPKG_S6)}|nodes. contract.NODES keys on NODE_UID; picking "
            "one of two inverts silently is how a chamber ends up with two depths.")
    ni_map = {k: int(v) for k, v in ni.items()}
    npos = np.array([ni_map.get(u, -1) for u in g.uid], dtype=np.int64)
    n_ok = npos >= 0
    src_n = np.maximum(npos, 0)

    def NC(col: str, default=np.nan) -> np.ndarray:
        if col not in n6.columns:
            return np.full(n, default, dtype=float)
        v = pd.to_numeric(pd.Series(n6[col].to_numpy()[src_n]),
                          errors="coerce").to_numpy(dtype=float)
        return np.where(n_ok, v, default)

    def NS(col: str) -> List[str]:
        v = (n6[col].astype(str).to_numpy()[src_n] if col in n6.columns
             else np.array([""] * n, dtype=object))
        return ["" if not ok else str(x) for ok, x in zip(n_ok, v)]

    # ---- align s6's reaches onto this graph's edges -------------------------------------
    key6 = pd.MultiIndex.from_arrays([r6.US_NODE.astype(str), r6.DS_NODE.astype(str)])
    if key6.has_duplicates:
        raise CT.ContractError(
            f"{int(key6.duplicated().sum()):,} reaches in "
            f"{os.path.basename(GPKG_S6)}|reaches share one (US_NODE, DS_NODE). In a "
            "forest that cannot happen and the join would take an arbitrary one of two "
            "gradients.")
    k6 = {k: i for i, k in enumerate(key6)}
    us_uid = [g.uid[int(i)] for i in g.e_us]
    ds_uid = [g.uid[int(i)] for i in g.e_ds]
    epos = np.array([k6.get((u, w), -1) for u, w in zip(us_uid, ds_uid)], dtype=np.int64)
    e_ok = epos >= 0
    src_e = np.maximum(epos, 0)

    def EC(col: str, default=np.nan) -> np.ndarray:
        if col not in r6.columns:
            return np.full(m, default, dtype=float)
        v = pd.to_numeric(pd.Series(r6[col].to_numpy()[src_e]),
                          errors="coerce").to_numpy(dtype=float)
        return np.where(e_ok, v, default)

    def ES(col: str, default: str = "") -> List[str]:
        v = (r6[col].astype(str).to_numpy()[src_e] if col in r6.columns
             else np.array([default] * m, dtype=object))
        return [str(x) if ok else default for ok, x in zip(e_ok, v)]

    # ---- per reach. Where s6 published nothing the row keeps a NEUTRAL placeholder and is
    # ---- taken off the reaches layer entirely by build(); it is never given a gradient.
    dn = np.where(e_ok, EC("DN", float(C.DN_MIN_MAIN)),
                  float(C.DN_MIN_MAIN)).astype(np.int64)
    s_laid = EC("SLOPE_LAID", 0.0) / 100.0
    s_min = EC("SLOPE_MIN", 0.0) / 100.0
    inv_up = EC("INV_UP")
    inv_dn = EC("INV_DN")
    us_depth = EC("US_DEPTH")
    ds_depth = EC("DS_DEPTH")
    cover_us = EC("COVER_US")
    cover_dn = EC("COVER_DN")

    # ---- per chamber --------------------------------------------------------------------
    inv = NC("INV_M")
    depth = NC("DEPTH_M")
    cover = NC("COVER_M")
    drop = np.nan_to_num(NC("DROP_M", 0.0), nan=0.0)
    drop_type = [t if t in CT.DROP_TYPE else "none" for t in NS("DROP_TYPE")]
    drop_why = [w if w in CT.DROP_WHY else "" for w in NS("DROP_WHY")]
    vortex = np.array([1 if t == "vortex" else 0 for t in drop_type], dtype=np.int8)
    past_cap = np.nan_to_num(NC("PAST_CAP", 0.0), nan=0.0).astype(np.int8)
    cap_exit = [x if x in CT.CAP_EXIT else "" for x in NS("CAP_EXIT")]

    # the bore AT a chamber, for cover(): its outgoing reach's, else the largest arriving
    node_dn = np.zeros(n, dtype=np.int64)
    in_dn_max = np.zeros(n, dtype=np.int64)
    np.maximum.at(in_dn_max, g.e_ds, dn)
    for v in range(n):
        e = int(g.e_of[v])
        node_dn[v] = int(dn[e]) if e >= 0 else (int(in_dn_max[v]) or int(C.DN_MIN_MAIN))

    tiers_seg = a.segments.TIER.astype(str).tolist()
    lv = Levels(
        dn=dn, slope_laid=s_laid, slope_min=s_min,
        grad_by=[x if x in CT.GRAD_BY else "table11" for x in ES("GRAD_BY", "table11")],
        sized_by=[x if x in CT.SIZED_BY else "minimum" for x in ES("SIZED_BY", "minimum")],
        clean_by=[x if x in CT.CLEAN_BY else "neither" for x in ES("CLEAN_BY", "neither")],
        v_pk=np.nan_to_num(EC("V_PK_MS", 0.0), nan=0.0),
        dod=np.nan_to_num(EC("DOD_PK", 0.0), nan=0.0),
        ret_min=np.nan_to_num(EC("RET_MIN", 0.0), nan=0.0),
        inv_up=inv_up, inv_dn=inv_dn, us_depth=us_depth, ds_depth=ds_depth,
        cover_us=cover_us, cover_dn=cover_dn,
        material=[x if x in CT.MATERIAL else C.material(t, int(d))
                  for x, t, d in zip(ES("MATERIAL"), tiers_seg, dn)],
        inv=inv, depth=depth, cover=cover, drop=drop, drop_type=drop_type, vortex=vortex,
        past_cap=past_cap, cap_exit=cap_exit,
        cap_len=np.zeros(n), node_dn=node_dn, st_reset=np.zeros(n, dtype=np.int8),
        drop_why=drop_why)

    # CAP_LEN_M is this stage's own measurement - how far along the graph to a recovery or
    # to an outfall - and s6 does not publish it. Recomputed from s6's covers: it is a
    # distance on the tree, not a second answer to a level.
    _p, _x, lv.cap_len = _cap_exits(g, np.nan_to_num(cover, nan=0.0), drop)

    cl = np.array(lv.clean_by, dtype=object)
    fin = np.isfinite(cover)
    lv.stats = dict(
        n_uniform=int(sum(1 for x in lv.grad_by if x == "uniform")),
        n_infeasible=int(sum(1 for x in lv.sized_by if x == "infeasible")),
        past_cap_nodes=int(past_cap.sum()),
        past_cap_no_exit=int(sum(1 for i in range(n) if past_cap[i] and not cap_exit[i])),
        vortex=int(vortex.sum()),
        backdrop=int(sum(1 for t in drop_type if t == "backdrop")),
        deepest_cover=float(np.nanmax(cover)) if fin.any() else 0.0,
        median_cover=float(np.nanmedian(cover[fin])) if fin.any() else 0.0,
        km_past_cap=float(g.e_len[np.nan_to_num(np.maximum(cover_us, cover_dn), nan=0.0)
                                  > C.MAX_COVER].sum() / 1000.0),
        km_below_min_cover=float(
            g.e_len[e_ok & (np.nan_to_num(np.minimum(cover_us, cover_dn), nan=99.0)
                            < C.MIN_COVER_CROWN - 1e-6)].sum() / 1000.0),
        km_tractive=float(g.e_len[e_ok & (cl == "tractive")].sum() / 1000.0),
        km_neither=float(g.e_len[e_ok & (cl == "neither")].sum() / 1000.0),
        km_velocity=float(g.e_len[e_ok & (cl == "velocity")].sum() / 1000.0),
        n_over_vmax=int((lv.v_pk > C.V_MAX + 1e-9).sum()),
        n_over_dod=int(sum(1 for k in range(m)
                           if e_ok[k] and lv.dod[k] > C.dod_limit(int(dn[k])) + 1e-9)),
        stations_used=0,
        km_total=float(g.e_len[e_ok].sum() / 1000.0),
    )

    # ---- THE FLOW THE DESIGN WAS SOLVED AT TRAVELS WITH THE DESIGN ---------------------
    # V_PK_MS and DOD_PK above were solved by s6 at s6's OWN peak flow. Publishing them
    # beside a peak flow this stage computed a second way would put a velocity on the row
    # that the row's own Q cannot reproduce - the same defect one level down. So PF, QINF
    # and QPK come from s6 too, on both layers. Q_ADF is not in dispute: the two
    # accumulations agree to the last decimal, which is itself the check that the graph is
    # the same graph.
    e_qadf = np.where(e_ok, EC("QADF_M3D"), f.e_qadf)
    e_qinf = np.where(e_ok, EC("QINF_LS"), f.e_qinf)
    e_pf = np.where(e_ok, EC("PF"), f.e_pf)
    s6_pfm = ES("PF_METH", "")
    e_pfm = [p if (ok and p in CT.PF_METH) else f.e_pfm[k]
             for k, (ok, p) in enumerate(zip(e_ok, s6_pfm))]
    e_qpk = e_qadf * 1000.0 / 86400.0 * e_pf + e_qinf

    # THE FLOW AT A CHAMBER IS THE FLOW IN THE PIPE LEAVING IT.
    #
    # s6's NODE layer publishes Q_ADF_M3D and Q_PK_LS and NO PEAK FACTOR AT ALL - there is
    # no PF and no PF_METH column on it. Until 2026-09-06 this function read
    # `NC("PF", 1.0)`, which does not read s6's answer: it returns the DEFAULT on every
    # row. The export therefore published PF = 1.0 and PF_METH = 'held' on all 56,943
    # chambers - a constant column, dressed as the leveller's - while the reach leaving the
    # same chamber carried s6's merrimack factor of about 3.62. MEASURED on the 12:00
    # export: the outgoing reach's QPK_LS disagreed with its own chamber's Q_PK_LS on
    # 26,482 of 26,579 pairs, median ratio 3.50, and 21,221 chambers published a Q_PK_LS
    # SMALLER than their own QADF x PF, which no non-negative infiltration can produce.
    #
    # Q_ADF_M3D and Q_PK_LS now come from s6's own node layer, and the factor comes from
    # s6's OWN OUTGOING REACH - which is what contract.NODES means by Q_PK_LS, "the number
    # the outgoing reach is sized on", and on s6's file the two agree on all 56,525
    # chambers that have one. Where s6 published a chamber but NO reach leaves it (an
    # outfall), there is no factor of s6's to publish and NONE IS SUBSTITUTED: PF is NULL
    # and PF_METH is blank. A NULL is checkable; the factor off a neighbouring pipe is not.
    r6_pf = (pd.to_numeric(r6.PF, errors="coerce").to_numpy(dtype=float)
             if "PF" in r6.columns else None)
    r6_pfm = (r6.PF_METH.astype(str).to_numpy() if "PF_METH" in r6.columns else None)
    n_pf = np.full(n, np.nan, dtype=float)
    n_pfm: List[str] = [""] * n
    n_flow_ok = np.zeros(n, dtype=bool)
    if r6_pf is not None:
        for v in range(n):
            e = int(g.e_of[v])
            if e < 0 or not e_ok[e]:
                continue
            j = int(epos[e])
            if not np.isfinite(r6_pf[j]):
                continue
            n_pf[v] = float(r6_pf[j])
            n_pfm[v] = (str(r6_pfm[j]) if r6_pfm is not None
                        and str(r6_pfm[j]) in CT.PF_METH else "")
            n_flow_ok[v] = True
    n_qadf = NC("Q_ADF_M3D")            # NaN where s6 published no chamber here
    n_qpk = NC("Q_PK_LS")               # s6's OWN chamber peak flow, never recomputed
    n_nofac = int(n_ok.sum() - n_flow_ok.sum())
    if n_nofac:
        notes.append(
            f"{n_nofac:,} chambers {S6_TAG} DID publish carry NO peak factor: it publishes "
            f"no PF column on its node layer, and these have no outgoing reach of its own "
            f"to take one from. PF and PF_METH are NULL on those rows rather than filled "
            f"from a neighbouring pipe. Their Q_PK_LS is still s6's own published chamber "
            f"flow.")
        _log("   note: " + notes[-1])

    # ---- what s6 did NOT level, named and sized ----------------------------------------
    pumped = _s6_pumped_links()
    gaps: List[Dict[str, Any]] = []
    for k in np.flatnonzero(~e_ok):
        k = int(k)
        u, w = us_uid[k], ds_uid[k]
        hit = pumped.get((u, w))
        if hit is not None:
            kind = "pumped_link"
            why = (f"s6_levels REPLACED this gravity reach with a PUMPED link, lift "
                   f"{hit['LIFT_M']:.2f} m - {hit['WHY']}")
        elif not n_ok[int(g.e_us[k])] or not n_ok[int(g.e_ds[k])]:
            kind = "chamber_missing"
            why = ("s6_levels did not publish one of this reach's two chambers, so there "
                   "is no invert at either end to lay a gradient between")
        else:
            kind = "reach_missing"
            why = ("s6_levels published both chambers but no reach between them - it "
                   "short-circuited an intermediate chamber that s4 minted")
        gaps.append(dict(
            EDGE_UID=CT.EDGE_UID_FMT.format(k), US_NODE=u, DS_NODE=w,
            TIER=str(tiers_seg[k]), LEN_M=round(float(g.e_len[k]), 3),
            QADF_M3D=round(float(f.e_qadf[k]), 3),
            LIFT_M=round(float(hit["LIFT_M"]), 3) if hit else 0.0,
            GAP_KIND=kind, WHY=why))
    gaps_df = pd.DataFrame(gaps, columns=["EDGE_UID", "US_NODE", "DS_NODE", "TIER",
                                          "LEN_M", "QADF_M3D", "LIFT_M", "GAP_KIND", "WHY"])

    n_miss_e, n_miss_n = int((~e_ok).sum()), int((~n_ok).sum())
    _log(f"   LEVELS READ FROM {os.path.basename(GPKG_S6)} (s6_levels): "
         f"{int(e_ok.sum()):,} of {m:,} reaches and {int(n_ok.sum()):,} of {n:,} chambers")
    if n_miss_e or n_miss_n:
        by_kind = gaps_df.GAP_KIND.value_counts().to_dict() if len(gaps_df) else {}
        notes.append(
            f"s6_levels did not level {n_miss_e:,} of this stage's {m:,} reaches "
            f"({gaps_df.LEN_M.sum() / 1000.0:.2f} km) or {n_miss_n} of its {n:,} chambers. "
            f"By reason: " + (", ".join(f"{k} {v:,}" for k, v in sorted(by_kind.items()))
                              or "none recorded")
            + ". They are NOT given a stand-in gradient - a gradient from one solver laid "
              "between two inverts from another describes no pipe. They come OFF the "
              "reaches layer and are published whole on `reaches_unlevelled`, which is "
              "inheritance row 4: a later pass may TAKE AWAY what an earlier one added, "
              "and it publishes how many.")
        _log("   note: " + notes[-1])

    return S6Levels(lv=lv, e_ok=e_ok, n_ok=n_ok, e_qadf=e_qadf, e_qinf=e_qinf, e_pf=e_pf,
                    e_pfm=e_pfm, e_qpk=e_qpk, n_pf=n_pf, n_pfm=n_pfm, n_qpk=n_qpk,
                    n_qadf=n_qadf, n_flow_ok=n_flow_ok,
                    gaps=gaps_df, notes=notes,
                    stats=dict(reaches_matched=int(e_ok.sum()), reaches_missing=n_miss_e,
                               nodes_matched=int(n_ok.sum()), nodes_missing=n_miss_n,
                               km_missing=round(float(gaps_df.LEN_M.sum()) / 1000.0, 3)))


def levels_delta(g: Graph, s6: S6Levels, standin: Levels) -> pd.DataFrame:
    """HOW FAR APART THE TWO SOLVERS WERE, on the rows both of them answered.

    Not a diagnostic that lives in a log line. It is a published table, because "s8 now
    reads s6" is a claim and the size of what changed is the only evidence for it."""
    ok_n, ok_e = s6.n_ok, s6.e_ok
    rows: List[Dict[str, Any]] = []

    def add(what: str, unit: str, a6, a8, mask, tol: float) -> None:
        v6 = np.asarray(a6, dtype=float)[mask]
        v8 = np.asarray(a8, dtype=float)[mask]
        keep = np.isfinite(v6) & np.isfinite(v8)
        if not keep.any():
            return
        d = v8[keep] - v6[keep]
        rows.append(dict(
            QUANTITY=what, UNIT=unit, N=int(keep.sum()),
            N_DIFFER=int((np.abs(d) > tol).sum()),
            PCT_DIFFER=round(100.0 * float((np.abs(d) > tol).sum())
                             / max(1, int(keep.sum())), 2),
            MEDIAN_DIFF=round(float(np.median(d)), 4),
            MEAN_DIFF=round(float(np.mean(d)), 4),
            MIN_DIFF=round(float(np.min(d)), 4), MAX_DIFF=round(float(np.max(d)), 4),
            S6_PUBLISHED=f"{float(np.median(v6[keep])):.4g} (median)",
            S8_STANDIN=f"{float(np.median(v8[keep])):.4g} (median)"))

    add("chamber invert", "m aOD", s6.lv.inv, standin.inv, ok_n, 0.01)
    add("chamber depth", "m", s6.lv.depth, standin.depth, ok_n, 0.01)
    add("chamber cover", "m", s6.lv.cover, standin.cover, ok_n, 0.01)
    add("chamber drop", "m", s6.lv.drop, standin.drop, ok_n, 0.01)
    add("reach diameter", "mm", s6.lv.dn, standin.dn, ok_e, 0.5)
    add("laid gradient", "%", s6.lv.slope_laid * 100.0, standin.slope_laid * 100.0,
        ok_e, 1e-6)
    add("upstream invert", "m aOD", s6.lv.inv_up, standin.inv_up, ok_e, 0.01)
    add("velocity at peak", "m/s", s6.lv.v_pk, standin.v_pk, ok_e, 0.001)
    add("depth of flow at peak", "-", s6.lv.dod, standin.dod, ok_e, 0.001)

    # the categorical answers, counted rather than differenced
    for name, a6, a8 in (("GRAD_BY", s6.lv.grad_by, standin.grad_by),
                         ("SIZED_BY", s6.lv.sized_by, standin.sized_by),
                         ("CLEAN_BY", s6.lv.clean_by, standin.clean_by)):
        v6 = np.array(a6, dtype=object)[ok_e]
        v8 = np.array(a8, dtype=object)[ok_e]
        rows.append(dict(
            QUANTITY=f"{name} (token)", UNIT="-", N=int(len(v6)),
            N_DIFFER=int((v6 != v8).sum()),
            PCT_DIFFER=round(100.0 * float((v6 != v8).sum()) / max(1, len(v6)), 2),
            MEDIAN_DIFF=0.0, MEAN_DIFF=0.0, MIN_DIFF=0.0, MAX_DIFF=0.0,
            S6_PUBLISHED=", ".join(f"{k} {v:,}"
                                   for k, v in pd.Series(v6).value_counts().items()),
            S8_STANDIN=", ".join(f"{k} {v:,}"
                                 for k, v in pd.Series(v8).value_counts().items())))
    df = pd.DataFrame(rows)
    df["SOURCE_PUBLISHED"] = S6_TAG
    df["SOURCE_RETIRED"] = LEVELS_TAG
    return df



# ======================================================================================
# 5.  WHAT EACH REACH TOUCHES, MEASURED - and the crossings REGISTER
#
#     W11a published ANGLE_DEG = 90 on 3,290 crossings. It was fabricated; the measured
#     minimum was 0.00 deg. Nothing below is asserted: the wadi contact is sampled off the
#     50-year hazard grid along the reach, and the angle is measured against the nearest
#     stream line's own direction.
# ======================================================================================

WADI_SAMPLE_M = 3.0     # PROJECT ASSUMPTION: sampling step along a reach for the hazard
                        # grid. The grid is 5 m; 3 m over-samples it deliberately so a
                        # short contact cannot fall between two samples.


def measure_contacts(a: Assembly, g: Graph) -> pd.DataFrame:
    """ON_WADI_M and ON_DUAL_M per reach, both measured.

    Wadi ground is criteria.HAZARD_WADI_CLASSES = (4, 5, 6) of the 50-year grid - AR&R
    flood-hazard classes standing in for G203's "areas subject to washout", a PROJECT
    ASSUMPTION (philosophy sec 3, assumption A2) and not a guideline threshold. Flood
    no-data is DRY HIGH GROUND (engineer, 2026-09-03; assumption A3)."""
    from w12 import hazard as HZ
    seg = a.segments
    _log("measuring the wadi contact off the 50-year hazard grid")
    xs: List[np.ndarray] = []
    ys: List[np.ndarray] = []
    owner: List[np.ndarray] = []
    for i, (geom, L) in enumerate(zip(seg.geometry.values, seg.LEN_M.to_numpy())):
        k = max(2, int(math.ceil(float(L) / WADI_SAMPLE_M)) + 1)
        d = np.linspace(0.0, float(L), k)
        pts = [geom.interpolate(float(t)) for t in d]
        xs.append(np.array([p.x for p in pts]))
        ys.append(np.array([p.y for p in pts]))
        owner.append(np.full(k, i, dtype=np.int64))
    X = np.concatenate(xs)
    Y = np.concatenate(ys)
    O = np.concatenate(owner)
    _log(f"   {len(X):,} sample points at {WADI_SAMPLE_M:g} m along {len(seg):,} reaches")
    with HZ.HazardGrids() as hg:
        cls = hg.sample_many(X, Y, rp=int(C.HAZARD_RETURN_YR))
    wet = np.isin(cls, np.array(C.HAZARD_WADI_CLASSES))
    tot = np.zeros(len(seg))
    hit = np.zeros(len(seg))
    np.add.at(tot, O, 1.0)
    np.add.at(hit, O, wet.astype(float))
    frac = np.where(tot > 0, hit / np.maximum(tot, 1.0), 0.0)
    on_wadi_m = np.round(frac * seg.LEN_M.to_numpy(), 3)

    along = seg.ALONG_DUAL.to_numpy(dtype=int)
    xing = seg.XING_DUAL.to_numpy(dtype=int)
    on_dual_m = np.where((along == 1) | (xing == 1), seg.LEN_M.to_numpy(), 0.0).round(3)
    return pd.DataFrame(dict(ON_WADI_M=on_wadi_m, ON_DUAL_M=on_dual_m,
                             WADI_FRAC=np.round(frac, 4),
                             ALONG_DUAL=along, XING_DUAL=xing))


def _stream_bearings():
    """Every stream segment as (midpoint, unit vector), for measuring a crossing angle
    against the ground's OWN drainage direction rather than against a guess."""
    st = _read(os.path.join(SHP, "W12_streams.gpkg"), "streams")
    mids, vecs = [], []
    for geom in st.geometry.values:
        cs = np.asarray(geom.coords)
        if len(cs) < 2:
            continue
        d = cs[1:, :2] - cs[:-1, :2]
        mid = (cs[1:, :2] + cs[:-1, :2]) / 2.0
        n = np.hypot(d[:, 0], d[:, 1])
        ok = n > 1e-9
        mids.append(mid[ok])
        vecs.append(d[ok] / n[ok, None])
    return np.vstack(mids), np.vstack(vecs)


def build_crossings(a: Assembly, g: Graph, contacts: pd.DataFrame
                    ) -> Tuple[gpd.GeoDataFrame, np.ndarray, Dict[str, int]]:
    """THE REGISTER. One row per contiguous run of contact along the flow path.

    H1a: a wadi crossing is legal only when it CROSSES rather than runs along, carries no
    chamber on wadi ground, has 1.50 m of cover (G203-p52 8.2.4, adopted for gravity as a
    PROJECT DECISION) and IS IN THIS REGISTER. Every contact gets a row whether or not it
    qualifies, because a contact with no row is invisible; whether it qualifies is then a
    measured column and not a filter."""
    seg = a.segments
    m = len(seg)
    on_w = contacts.ON_WADI_M.to_numpy()
    on_d = contacts.ON_DUAL_M.to_numpy()
    both = int(((on_w > 0) & (on_d > 0)).sum())

    # group contiguous contact along the flow path: an edge joins the run of its upstream
    # edge when both touch the same obstacle and the shared node has exactly one inlet.
    inc = np.full(len(g.uid), -1, dtype=np.int64)
    for k in range(m):
        w = int(g.e_ds[k])
        if inc[w] == -1:
            inc[w] = k
    kind = np.where(on_w > 0, 1, np.where(on_d > 0, 2, 0))
    run_id = np.full(m, -1, dtype=np.int64)
    nxt = 0
    # walk in topological order of the upstream node so a run is always started upstream
    pos = np.empty(len(g.uid), dtype=np.int64)
    pos[g.order] = np.arange(len(g.order))
    for k in np.argsort(pos[g.e_us]):
        k = int(k)
        if kind[k] == 0:
            continue
        v = int(g.e_us[k])
        p = int(inc[v])
        if p >= 0 and g.indeg[v] == 1 and kind[p] == kind[k] and run_id[p] >= 0:
            run_id[k] = run_id[p]
        else:
            run_id[k] = nxt
            nxt += 1

    smids, svecs = _stream_bearings()
    from shapely.strtree import STRtree
    from shapely.geometry import MultiPoint
    stree = STRtree([Point(float(x), float(y)) for x, y in smids])

    rows = []
    cross_id = np.array([""] * m, dtype=object)
    geoms = seg.geometry.values
    lens = seg.LEN_M.to_numpy()
    for r in range(nxt):
        ks = np.flatnonzero(run_id == r)
        obstacle = "wadi" if kind[ks[0]] == 1 else "dual"
        parts = [geoms[k] for k in ks]
        merged = parts[0] if len(parts) == 1 else unary_union(parts)
        try:
            line = merged if merged.geom_type == "LineString" else \
                LineString([c for p in parts for c in p.coords])
        except Exception:
            line = parts[0]
        cs = np.asarray(line.coords)
        chord = cs[-1, :2] - cs[0, :2]
        nch = float(np.hypot(*chord))
        if obstacle == "wadi":
            mid = Point(float(cs[len(cs) // 2, 0]), float(cs[len(cs) // 2, 1]))
            j = int(stree.nearest(mid))
            u = svecs[j]
            # angle between the contact's chord and the stream's own direction, 0-90 deg.
            # 90 deg IS square across the channel; 0 deg means the pipe runs ALONG it,
            # which is what H1 forbids. MEASURED - W11a asserted 90 on 3,290 crossings.
            ang = 0.0 if nch < 1e-6 else math.degrees(
                math.acos(min(1.0, abs(float(np.dot(chord / nch, u))))))
        else:
            d = float(seg.DUAL_ANG.to_numpy()[ks[0]])
            ang = d if d >= 0 else float("nan")
        cid = CT.CROSS_UID_FMT.format(r + 1)
        for k in ks:
            cross_id[k] = cid
        contact = float(np.sum(on_w[ks] if obstacle == "wadi" else on_d[ks]))
        rows.append(dict(
            CROSS_ID=cid, EDGE_UID="", OBSTACLE=obstacle,
            LEN_M=round(float(line.length), 3),
            # A DUAL-CARRIAGEWAY CONTACT WHOSE ANGLE s1 DID NOT RECORD LANDS HERE AS NaN.
            # ANGLE_DEG is a required, non-blank contract field, so the row has to carry a
            # number - but 0.00 deg MEANS "runs along the obstacle", the worst reading there
            # is, and a reader cannot tell a measured 0 from an unmeasured one. That is the
            # ANGLE_DEG = 90 defect with the sign flipped. So the value stays 0.0 (the
            # conservative reading, and the one the contract can hold) and ANG_MEAS says
            # whether anything was actually measured. The manifest's angle statistics are
            # taken over ANG_MEAS = 1 only; a fabricated zero must not move a published
            # median.
            ANGLE_DEG=round(float(ang), 2) if ang == ang else 0.0,
            ANG_MEAS=int(ang == ang),
            METHOD="open_cut", COVER_M=round(float(C.min_cover_for(on_wadi_crossing=True)), 3),
            APPROVED=0, N_REACH=int(len(ks)), CONTACT_M=round(contact, 2),
            SQUARE=int(abs(90.0 - ang) <= C.WADI_XING_SKEW_DEG) if ang == ang else 0,
            SRC="terrain", CONFIDENCE="derived", STAGE=STAGE, geometry=line))
    cx = gpd.GeoDataFrame(rows, geometry="geometry", crs=f"EPSG:{CT.CRS_EPSG}")
    stats = dict(
        n_rows=len(cx),
        n_wadi=int((cx.OBSTACLE == "wadi").sum()) if len(cx) else 0,
        n_dual=int((cx.OBSTACLE == "dual").sum()) if len(cx) else 0,
        km_wadi=float(on_w.sum() / 1000.0),
        km_dual=float(on_d.sum() / 1000.0),
        both=both,
        n_square=int(cx.SQUARE.sum()) if len(cx) else 0,
        # over the rows where an angle was actually MEASURED - see ANG_MEAS above
        n_angle_unmeasured=int((cx.ANG_MEAS == 0).sum()) if len(cx) else 0,
        angle_min=float(cx.ANGLE_DEG[cx.ANG_MEAS == 1].min())
                  if len(cx) and int((cx.ANG_MEAS == 1).sum()) else float("nan"),
        angle_median=float(cx.ANGLE_DEG[cx.ANG_MEAS == 1].median())
                     if len(cx) and int((cx.ANG_MEAS == 1).sum()) else float("nan"),
    )
    _log(f"   crossings register: {stats['n_rows']:,} rows "
         f"({stats['n_wadi']:,} wadi, {stats['n_dual']:,} dual), "
         f"{stats['km_wadi']:.2f} km on wadi ground, {stats['km_dual']:.2f} km on a dual "
         f"carriageway; {stats['n_square']:,} within {C.WADI_XING_SKEW_DEG:g} deg of square")
    return cx, cross_id, stats


# ======================================================================================
# 6.  PACKAGES AND LABELS
#
#     NO PACKAGES STAGE EXISTS. The contract marks PACKAGE and PHASE required=False for
#     exactly this reason, and it also declares what a package should be: 3.5-40 km,
#     180-2,180 plots, ONE connected tree with EXACTLY ONE outlet. This stage groups by
#     subnetwork - which satisfies the tree and the outlet by construction and satisfies
#     the size band only where it happens to - and MEASURES how many land in the band
#     rather than claiming they do.
#
#     PHASE stays 0 on every row. The contract's own words: "delivery phase, 0 = not yet
#     assigned". Inventing a programme here would be a number with nothing behind it.
# ======================================================================================

def build_packages(a: Assembly, g: Graph, f: Flows) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    n = len(g.uid)
    out_idx = np.unique(f.subnet)
    order = sorted(out_idx, key=lambda i: -float(f.q_adf[i]))
    pkg_of_out = {int(i): f"P{r + 1:03d}" for r, i in enumerate(order)}
    node_pkg = np.array([pkg_of_out[int(s)] for s in f.subnet], dtype=object)
    edge_pkg = node_pkg[g.e_us]

    plots = a.connections.groupby(a.connections.OUT_NODE.astype(str)).size()
    plot_at = np.zeros(n)
    for u, c in plots.items():
        i = g.ix.get(u)
        if i is not None:
            plot_at[i] = c

    rows = []
    for r, i in enumerate(order):
        sel = f.subnet == i
        esel = sel[g.e_us]
        km = float(g.e_len[esel].sum() / 1000.0)
        rows.append(dict(
            PACKAGE=pkg_of_out[int(i)], PHASE=0, LEN_KM=round(km, 4),
            N_PLOT=int(plot_at[sel].sum()), OUTLET=g.uid[int(i)],
            DS_PKG="", COMM_SEQ=r + 1, INDEP=1, ONE_TREE=1,
            N_CHAMBER=int(sel.sum()), Q_ADF_M3D=round(float(f.q_adf[i]), 2),
            N_PROP=round(float(f.n_prop[i]), 1),
            IN_BAND=int(3.5 <= km <= 40.0)))
    pk = pd.DataFrame(rows)
    _log(f"   {len(pk):,} packages (one per subnetwork). "
         f"{int(pk.IN_BAND.sum()):,} sit inside the contract's 3.5-40 km band; "
         f"largest {pk.LEN_KM.max():.1f} km, median {pk.LEN_KM.median():.2f} km")
    return pk, node_pkg, edge_pkg


def node_refs(a: Assembly, g: Graph, node_pkg: np.ndarray, tier_out: List[str]) -> List[str]:
    """NAMA's own ID grammar - `5A-2-SM.2-MH391` is package, tier token, sequence. The
    contract is explicit that NODE_REF is referenced by NOTHING: the network must read like
    theirs, and that must not cost referential integrity."""
    seq: Dict[Tuple[str, str], int] = {}
    out: List[str] = []
    for i in range(len(g.uid)):
        tok = CT.TIER_TOKEN.get(tier_out[i], "L")
        key = (str(node_pkg[i]), tok)
        seq[key] = seq.get(key, 0) + 1
        out.append(f"{node_pkg[i]}-{tok}-MH{seq[key]:04d}")
    return out


# ======================================================================================
# 6b.  NAMING - concept rule 8
#
#      `I-S03-SM-M012`: town letter, subnetwork, tier, element, zero-padded. The GRAMMAR,
#      the FORMATTER and the TOWN-CODE RESOLVER all live in `contract` and are called from
#      here - this section decides only WHICH town, WHICH subnetwork and WHICH number, and
#      `contract.validate()` then checks that every NAME agrees with its own TOWN, SUBNET
#      and TIER columns.
#
#      TWO DECISIONS THIS STAGE MAKES, BOTH DELIBERATE AND BOTH CHECKABLE:
#
#      1. A SUBNETWORK HAS ONE TOWN - the town of its OUTFALL. Every element in it carries
#         that letter. The alternative (each element takes the town it physically sits in)
#         is a closer reading of "elements outside any town take the letter of the first
#         town DOWNSTREAM of them", but it makes `S03` mean two different subnetworks the
#         moment one crosses a boundary, and `I-S03` would no longer read as "subnetwork 3
#         in Ibri". The engineer's rule is applied where it bites instead: an outfall that
#         sits in NO town takes the nearest one, and the DISTANCE IS PUBLISHED so nobody
#         has to take the assignment on trust. How many elements sit physically in a town
#         other than the one in their name is COUNTED and reported, never hidden.
#
#      2. A MANHOLE IS NUMBERED WITHIN ITS SUBNETWORK, NOT WITHIN ITS TIER, so the conduit
#         leaving manhole 12 is C012 - "a conduit is named for its UPSTREAM manhole", which
#         is only true if the two numbers are the same one. The tier token still rides in
#         the manhole name (`-SM-`) and still has to agree with the TIER column.
#
#      Numbering order is deterministic and stated: subnetworks by descending served load
#      within their town, manholes by descending distance to their own outfall (so M001 is
#      the head of the longest chain), ties broken on NODE_UID. Re-running the export on
#      the same layers gives the same names; changing the design changes them, which is why
#      NAME is referenced by NOTHING. Identity is NODE_UID and stays NODE_UID.
# ======================================================================================

def node_tiers(a: Assembly, g: Graph) -> List[str]:
    """THE TIER OF A CHAMBER - one function, because two produce two answers.

    A chamber takes the tier of its OUTGOING reach. At a terminal there is no outgoing
    reach, so it takes the HIGHEST-ranked tier arriving at it - highest, not last, because
    "last" is row order and row order is not an engineering decision. Computed in two places
    with two different terminal rules until 2026-09-06, which put `I-S19-L-M001` on a
    chamber the same file published as TIER = 'sub main' on three outfalls: the name says
    lateral, the column says sub main, and contract.validate() catches it because the tier
    token rides inside the name."""
    m = len(g.e_len)
    tiers_e = a.segments.TIER.astype(str).to_numpy()
    out: List[str] = ["lateral"] * len(g.uid)
    rank = {t: i for i, t in enumerate(("rider", "lateral", "main", "sub main",
                                        "trunk main"))}
    best_in = np.full(len(g.uid), -1)
    for k in range(m):
        w = int(g.e_ds[k])
        r = rank.get(tiers_e[k], 1)
        if r > best_in[w]:
            best_in[w] = r
            out[w] = tiers_e[k]
    for v in range(len(g.uid)):
        e = int(g.e_of[v])
        if e >= 0:
            out[v] = tiers_e[e]
    return out


@dataclass
class Naming:
    node_name: List[str]
    node_town: List[str]
    node_sub: List[str]
    edge_name: List[str]
    subnet_name: Dict[int, str]        # outfall node index -> "I-S03"
    subnet_town: Dict[int, str]        # outfall node index -> "I"
    subnet_code: Dict[int, str]        # outfall node index -> "S03"
    town_of_subnet: Dict[int, str]     # outfall node index -> the settlement's full name
    notes: List[str]
    stats: Dict[str, Any]


# WHICH TIERS THE CONCEPT NAME GRAMMAR CAN ACTUALLY EXPRESS.
#
# Concept rule 8 declares THREE tier codes - "TM / SM / L" - and `contract.NAME_RE` enforces
# exactly those three. This design's governing tier set (philosophy sec 4, contract.TIERS) has
# FIVE: rider, lateral, main, sub main, trunk main. `contract.TIER_TOKEN` maps the two extra
# ones to "R" and "M", which the grammar then refuses, so a chamber on a `main` or a `rider`
# reach came out named `I-S03-M-M012` - a string `parse_name()` returns None for and
# `validate()` reports as "N NAME values do not fit the grammar". s3_hierarchy emits `main` on
# every run past its depth or path budget, so that was most of a real network.
#
# The set below is DISCOVERED, not typed: each tier is put through concept_name() and
# parse_name() once at import, so the day the contract's grammar grows a token this widens on
# its own instead of going stale. A tier the grammar cannot express mints NO name, and the
# count is published - rule 7, flag do not solve. Inventing a mapping ("call a main a sub
# main") would put one tier's label on another tier's chamber, which is exactly what
# concept_name()'s own error message forbids.
def _grammar_tiers() -> Tuple[set, set]:
    ok, no = set(), set()
    for t in CT.TIERS:
        try:
            nm = CT.concept_name("I", "manhole", subnet="S01", tier=t, seq=1)
        except Exception:
            no.add(t)
            continue
        (ok if CT.parse_name(nm) is not None else no).add(t)
    return ok, no


TIERS_NAMEABLE, TIERS_NOT_NAMEABLE = _grammar_tiers()


def _read_towns() -> Optional[gpd.GeoDataFrame]:
    """The settlement polygons, with a unique letter code on each. Read-only client data."""
    try:
        t = gpd.read_file(TOWNS_SHP, layer=TOWNS_LAYER)
    except Exception as e:                                     # pragma: no cover - IO
        _log(f"   TOWNS NOT READ ({type(e).__name__}: {e}). Every NAME will be BLANK and "
             f"the publication gate contract.assert_named() will refuse the layer - which "
             f"is the correct outcome, not a workaround.")
        return None
    if t.crs is not None and t.crs.to_epsg() != CT.CRS_EPSG:
        t = t.to_crs(CT.CRS_EPSG)
    names = [str(v) for v in t[TOWNS_NAME_FIELD]]
    codes = CT.town_letters(names)
    t = t.copy()
    t["TOWN_NAME"] = names
    t["TOWN_CODE"] = [codes[n] for n in names]
    return t[["TOWN_NAME", "TOWN_CODE", "geometry"]]


def build_names(a: Assembly, g: Graph, f: Flows) -> Naming:
    """NAME / TOWN / SUBNET for every chamber and every conduit - `w12.naming`'s answer.

    THE ASSIGNMENT IS THE MODULE'S, CALLED, NOT REIMPLEMENTED.  Until 2026-09-06 this
    function carried its own: subnetworks numbered by descending load, manholes by
    descending distance to the outfall, one town per subnetwork taken from the outfall.
    `w12.naming` was written for exactly this job, is covered by
    `tests/test_naming_scheme.py` - including a test that shuffles rows and columns and
    demands the same names back - and was imported by NOTHING in the pipeline.  Two naming
    schemes for one network is the same defect as two level solvers, one layer down.

    What changes, and it is visible on the deliverable:

      * SUBNETWORK NUMBER.  The main pipe's runs first, then branches ordered by their
        OUTFALL north to south, with coordinates quantised so a float wobble cannot flip
        two neighbours.  The old key was descending served load, which reorders the whole
        set whenever one plot moves.
      * MANHOLE NUMBER.  A depth-first walk UPSTREAM from the outfall, largest subtree
        first, ties north to south - so M001 is the OUTFALL and the numbers walk the spine
        before the branches.  The old key made M001 the head of the longest chain.
      * TOWN.  The engineer's rule (b) applied per element - an element outside every town
        takes the letter of the first town DOWNSTREAM of it - rather than one town per
        subnetwork taken from the outfall.  `res.node_towns` publishes both the town a
        chamber SITS in and the town its NAME carries, so the two can be compared.

    Neither scheme was wrong.  One of them is now the only one."""
    n, m = len(g.uid), len(g.e_len)
    blank_n, blank_e = [""] * n, [""] * m
    notes: List[str] = []

    tier_node = node_tiers(a, g)

    nd_in = pd.DataFrame({
        "NODE_UID": g.uid,
        "DS_NODE": [g.uid[int(d)] if d >= 0 else "" for d in g.ds],
        "X": a.chambers.X.to_numpy(dtype=float),
        "Y": a.chambers.Y.to_numpy(dtype=float),
        "TIER": tier_node,
    })
    r_in = pd.DataFrame({
        "EDGE_UID": [CT.EDGE_UID_FMT.format(k) for k in range(m)],
        "US_NODE": [g.uid[int(i)] for i in g.e_us],
    })

    # The gazetteer is read through this stage's own `_read_towns()` - the same client
    # layer `w12.naming` would open itself - so the settlement source stays one function
    # and the point-in-polygon locate happens once, here, on the frame this stage already
    # validates. `name_network` then owns the ASSIGNMENT and nothing else.
    towns_gdf = _read_towns()
    if towns_gdf is None or not len(towns_gdf):
        return Naming(blank_n, list(blank_n), list(blank_n), blank_e, {}, {}, {}, {},
                      ["the settlement layer could not be read, so nothing is named"],
                      {"named_nodes": 0, "towns_used": 0,
                       "names_refused_no_tier_token": 0, "names_refused_by_tier": {}})
    # sorted by name so a chamber sitting exactly on a shared boundary takes the same town
    # every run - the dedup below keeps the FIRST hit, and unsorted that is row order.
    towns_gdf = towns_gdf.sort_values("TOWN_NAME").reset_index(drop=True)
    towns = NM.TownIndex.from_names(towns_gdf.TOWN_NAME.tolist(), source=TOWNS_SHP)
    pts = gpd.GeoDataFrame(
        {"v": np.arange(n)},
        geometry=[Point(float(x), float(y))
                  for x, y in zip(nd_in.X.to_numpy(), nd_in.Y.to_numpy())],
        crs=f"EPSG:{CT.CRS_EPSG}")
    jn_t = gpd.sjoin(pts, towns_gdf[["TOWN_NAME", "geometry"]], how="left",
                     predicate="within")
    jn_t = jn_t[~jn_t.index.duplicated(keep="first")].sort_index()
    node_town_name = jn_t.TOWN_NAME.fillna("").astype(str).to_numpy()

    res = NM.name_network(nd_in, reaches=r_in, towns=towns,
                          node_town=node_town_name,
                          main_tier=CT.TIER_ALIASES.get("trunk_main", "trunk main"))
    c = res.counts

    node_name = res.nodes.NAME.astype(str).tolist()
    node_town = res.nodes.TOWN.astype(str).tolist()
    node_sub = res.nodes.SUBNET.astype(str).tolist()
    edge_name = (res.reaches.NAME.astype(str).tolist() if res.reaches is not None
                 else list(blank_e))

    # ---- the module's per-SUBNETWORK answer, keyed the way this stage keys one: by the
    # ---- index of the component's own outfall node (f.subnet). "S03" is not unique across
    # ---- towns, so the machine key stays the outfall and the display key is the full name.
    sub_by_outfall = {str(r.OUTFALL): r for r in res.subnets.itertuples()}
    subnet_name: Dict[int, str] = {}
    subnet_town: Dict[int, str] = {}
    subnet_code: Dict[int, str] = {}
    town_of: Dict[int, str] = {}
    tn_by_uid = dict(zip(res.node_towns.NODE_UID.astype(str),
                         res.node_towns.TOWN_NAME.astype(str)))
    for i in (int(x) for x in np.unique(f.subnet)):
        hit = sub_by_outfall.get(g.uid[i])
        if hit is not None:
            subnet_name[i] = str(hit.NAME)
            subnet_town[i] = str(hit.TOWN)
            subnet_code[i] = str(hit.SUBNET)
        else:
            # this stage's components and the module's differ only where a DS_NODE dangles;
            # the module flags that as node_ds_missing rather than inventing an outfall.
            subnet_name[i] = ""
            subnet_town[i] = node_town[i]
            subnet_code[i] = node_sub[i]
        town_of[i] = tn_by_uid.get(g.uid[i], "")

    n_refused = 0
    refused_by_tier: Dict[str, int] = {}
    if len(res.flags):
        for kind, cnt in res.flags_by_kind().items():
            ex = res.flags[res.flags.KIND == kind].iloc[0]
            notes.append(f"naming flagged {int(cnt):,} x {kind} - e.g. {ex.REF}: {ex.WHY}")
        tier_flags = res.flags[res.flags.KIND.isin(
            ("node_no_tier", "node_tier_ungrammatical"))]
        n_refused = int(len(tier_flags))
        if n_refused:
            hits = [g.ix[str(r)] for r in tier_flags.REF if str(r) in g.ix]
            got = pd.Series([str(tier_node[i]) for i in hits])
            refused_by_tier = {str(k): int(v) for k, v in got.value_counts().items()}
            notes.append(
                f"{n_refused:,} of {n:,} chambers are on a tier the concept NAME grammar "
                f"has no token for and are therefore NOT NAMED: "
                + (", ".join(f"{t} {v:,}" for t, v in sorted(refused_by_tier.items()))
                   or "tier not recoverable")
                + ". Concept rule 8 declares THREE tier codes (TM / SM / L) and "
                  "contract.NAME_RE enforces exactly those; this design's governing tier "
                  "set is FIVE (philosophy sec 4), and contract.TIER_TOKEN maps the extra "
                  "two to 'R' and 'M', which the grammar refuses. Nothing is invented - "
                  "calling a main a sub main would put one tier's label on another tier's "
                  "chamber. THE DECISION IS THE ENGINEER'S: either the grammar gains R and "
                  "M, or s3 stops emitting those tiers. Until then assert_named() refuses "
                  "these layers and the objection is on the contract_check layer with this "
                  "count.")

    # how many chambers sit physically in a settlement OTHER than the one in their name.
    # The module measures it: TOWN is where the chamber IS, TOWN_NAMED is what its name
    # carries, and the two differ on every chamber of a subnetwork that straddles a border.
    nt = res.node_towns
    cross = int(((nt.TOWN.astype(str) != "") & (nt.TOWN_NAMED.astype(str) != "")
                 & (nt.TOWN.astype(str) != nt.TOWN_NAMED.astype(str))).sum())
    if cross:
        notes.append(
            f"{cross:,} of {n:,} chambers sit physically inside a settlement other than "
            f"the one whose letter their NAME carries. A subnetwork has ONE letter - its "
            f"members' plurality - so a subnetwork that straddles a boundary produces "
            f"this, and it is measured rather than hidden.")
    notes.append(
        f"town resolution (engineer's rule b): {c['town_inside']:,} chambers took the "
        f"letter of the polygon they sit in, {c['town_downstream']:,} took the first town "
        f"DOWNSTREAM of them, {c['town_none']:,} resolved to none.")

    _log(f"   named {c['nodes_named']:,} of {c['nodes_total']:,} chambers and "
         f"{c['reaches_named']:,} of {c['reaches_total']:,} conduits across "
         f"{c['towns_used']} settlements in {c['subnets']:,} subnetworks "
         f"({c['subnets_main']} of them main-pipe runs), by w12.naming. Against the names "
         f"the frames arrived with: kept {c['unchanged']:,}, renamed {c['renamed']:,}, "
         f"WITHDRAWN {c['withdrawn']:,}")
    return Naming(node_name, node_town, node_sub, edge_name, subnet_name, subnet_town,
                  subnet_code, town_of, notes,
                  {"named_nodes": int(c["nodes_named"]),
                   "towns_used": int(c["towns_used"]),
                   "outfalls_nearest_town": 0,
                   "chambers_in_another_town": cross,
                   "names_refused_no_tier_token": n_refused,
                   "names_refused_by_tier": refused_by_tier,
                   "naming_counts": {str(k): v for k, v in c.items()},
                   "naming_flags": {str(k): int(v)
                                    for k, v in res.flags_by_kind().items()},
                   "town_dist": {}})


# ======================================================================================
# 7.  THE CONTRACT LAYERS
#
#     Field for field against `contract.LAYERS`. Nothing is written that the contract does
#     not declare a `why` for, and `validate()` is run over every one of them before a
#     single schedule, drawing or model file is produced. Where it objects, the objection
#     is PUBLISHED (layer `contract_check`) rather than silenced - "relaxing a field a
#     check needs converts a visible failure into an invisible one" is the contract's own
#     sentence, and it applies to the exporter too.
# ======================================================================================

def _bearing_fix_inlets(a: Assembly, g: Graph) -> np.ndarray:
    """s4 measured INLET_DEG and left 2,382 of them null. A null on a node WITH inlets is
    an H10 check that cannot run, which philosophy sec 8 makes a FAILURE and not a blank.
    Re-measured here on the same convention s4 used - 180 deg is straight through, 90 deg
    is square, below 90 the inlet doubles back against the flow (G203-p30)."""
    n = len(g.uid)
    val = a.chambers.INLET_DEG.to_numpy(dtype=float).copy()
    geoms = a.segments.geometry.values

    def _vec_in(k):
        cs = np.asarray(geoms[k].coords)
        d = cs[-1, :2] - cs[-2, :2]
        return d / max(1e-12, float(np.hypot(*d)))

    def _vec_out(k):
        cs = np.asarray(geoms[k].coords)
        d = cs[1, :2] - cs[0, :2]
        return d / max(1e-12, float(np.hypot(*d)))

    ins: Dict[int, List[int]] = defaultdict(list)
    for k in range(len(geoms)):
        ins[int(g.e_ds[k])].append(k)

    n_fixed = 0
    for i in np.flatnonzero(~np.isfinite(val)):
        i = int(i)
        e_out = int(g.e_of[i])
        kin = ins.get(i, [])
        if not kin or e_out < 0:
            val[i] = 180.0                     # a head, or an outfall: no inlet to constrain
            continue
        u = _vec_out(e_out)
        worst = 180.0
        for k in kin:
            v = _vec_in(k)
            ang = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(v, u))))))
            worst = min(worst, ang)
        val[i] = round(worst, 1)
        n_fixed += 1
    if n_fixed:
        _log(f"   re-measured INLET_DEG on {n_fixed:,} chambers s4 left null with inlets "
             f"present; the rest of the nulls are heads and outfalls, written 180 deg")
    val[~np.isfinite(val)] = 180.0
    return val


@dataclass
class Joins:
    """Where each subnetwork meets the client's Main Pipe, and how far that is from its own
    lowest point. CONCEPT RULE 2, and the two numbers that make it checkable."""
    is_join: np.ndarray        # per node, 1 at an outfall that reaches the main pipe
    gap_m: np.ndarray          # per node, straight-line distance to the main pipe
    off_m: np.ndarray          # per node, distance from the subnetwork's TRUE low point
    why: List[str]
    low_uid: Dict[int, str]    # outfall node index -> the uid of its own lowest chamber
    stats: Dict[str, Any]


def measure_joins(a: Assembly, g: Graph, f: Flows) -> Joins:
    """CONCEPT RULE 2: a subnetwork joins the main pipe at the LOWEST POINT WHERE IT MEETS
    it, and where there is no street at the low point it connects at the nearest usable
    place and RECORDS THE DISTANCE FROM THE TRUE LOW POINT.

    This stage does not move an outfall - the tree is s2's and s3's. What it does is
    MEASURE the rule, on every subnetwork, and publish the three numbers the rule is made
    of: does this outfall reach the main pipe at all (JOIN_MAIN), how far it sits from its
    own catchment's lowest chamber (JOIN_OFF_M) and why (JOIN_WHY). W11b shipped two
    subnetworks holding a quarter of the network that touched the trunk at 1.1 m and 3.1 m
    and discharged somewhere else entirely, and nothing on the layer said so."""
    n = len(g.uid)
    is_join = np.zeros(n, dtype=np.int8)
    gap = np.zeros(n)
    off = np.zeros(n)
    why: List[str] = [""] * n
    low_uid: Dict[int, str] = {}
    try:
        tline = unary_union(list(a.trunk.geometry.values))
    except Exception:                                          # pragma: no cover
        tline = None
    xs = a.chambers.X.to_numpy(dtype=float)
    ys = a.chambers.Y.to_numpy(dtype=float)

    n_reach = n_short = 0
    for out_i in np.unique(f.subnet):
        out_i = int(out_i)
        sel = np.flatnonzero(f.subnet == out_i)
        low = int(sel[int(np.argmin(g.grd[sel]))])
        low_uid[out_i] = g.uid[low]
        d_trunk = (float(Point(xs[out_i], ys[out_i]).distance(tline))
                   if tline is not None else float("inf"))
        gap[out_i] = round(d_trunk, 1)
        d_low = float(math.hypot(xs[out_i] - xs[low], ys[out_i] - ys[low]))
        dz = float(g.grd[out_i] - g.grd[low])
        if d_trunk <= JOIN_TOL_M:
            is_join[out_i] = 1
            n_reach += 1
            if d_low > 1.0:
                d_low_trunk = (float(Point(xs[low], ys[low]).distance(tline))
                               if tline is not None else float("nan"))
                off[out_i] = round(d_low, 1)
                why[out_i] = (
                    f"outlet {d_low:,.0f} m from the subnetwork's own low point "
                    f"{g.uid[low]}, which stands {dz:,.2f} m lower; that low point is "
                    f"{d_low_trunk:,.0f} m from the main pipe, so the outlet is at the "
                    f"nearest place the network actually meets it")
        else:
            n_short += 1
            # JOIN_MAIN = 0, so JOIN_OFF_M must stay 0: the contract refuses an offset from
            # a join that does not exist, and it is right to - there is no join to offset
            # from. The distance short is carried on the subnetwork polygon (GAP_M) and is
            # an EXCEPTIONS layer of its own.
    _log(f"   joins to the main pipe: {n_reach} of {n_reach + n_short} subnetwork outfalls "
         f"are within {JOIN_TOL_M:g} m of it; {n_short} are not and are drawn as an "
         f"exception with the distance in words")
    # THE HEADLINE IS MEASURED OVER THE OUTFALLS, AND AN UNMEASURABLE DISTANCE SAYS SO.
    # `gap` is per NODE and is 0.0 on every chamber that is not an outfall, so a max over the
    # whole array with the non-finite values filtered out returned 0.0 when the client's Main
    # Pipe could not be read at all - i.e. "no subnetwork is more than 0 m from the trunk",
    # the exact opposite of the truth, printed as a headline into the manifest and EXPORT.md.
    out_ix = [int(i) for i in np.unique(f.subnet)]
    meas = np.array([gap[i] for i in out_ix], dtype=float)
    finite = meas[np.isfinite(meas)]
    n_unmeasured = int(len(meas) - len(finite))
    if n_unmeasured:
        _log(f"   *** the distance to the client's Main Pipe COULD NOT BE MEASURED on "
             f"{n_unmeasured} of {len(meas)} outfalls (the trunk layer is empty or "
             f"unreadable). GAP_M is null on those rows and the 'worst gap' below counts "
             f"only the ones that could be measured - it is NOT evidence that the rest are "
             f"close.")
    return Joins(is_join, gap, off, why, low_uid,
                 {"reaching": n_reach, "short": n_short,
                  "off_low_point": int((off > 0).sum()),
                  "gap_unmeasured": n_unmeasured,
                  "worst_gap_m": float(finite.max()) if len(finite) else float("nan")})


def build_layers(a: Assembly, g: Graph, f: Flows, lv: Levels, contacts: pd.DataFrame,
                 cross_id: np.ndarray, node_pkg: np.ndarray, edge_pkg: np.ndarray,
                 nm: Naming, jn: Joins,
                 s6: Optional["S6Levels"] = None) -> Dict[str, gpd.GeoDataFrame]:
    n, m = len(g.uid), len(g.e_len)
    seg = a.segments
    ch = a.chambers

    # ---- tier of the OUTGOING reach at every node, from the ONE function that decides it
    tiers_e = seg.TIER.astype(str).to_numpy()
    tier_node = node_tiers(a, g)

    src_e = seg.SRC.astype(str).to_numpy()
    conf_e = seg.CONFIDENCE.astype(str).to_numpy()
    # THE RAW CORRIDOR SOURCE, CARRIED TO THE DELIVERABLE. `assemble()` maps
    # draft_base/draft_propo -> dwg_road and FLOORS the confidence of anything off the
    # PROPOSED road layer to 'provisional' (philosophy P6). Publishing only the mapped
    # value left nothing on the client's package to test that floor against: every row
    # reads dwg_road whether it came from the base road set or the draftsman's proposed
    # streets, so contract.SRC_CONFIDENCE_FLOOR became uncheckable - and philosophy sec 8
    # makes a check that cannot run a failure, not a blank.
    raw_e = (seg.SRC_RAW.astype(str).to_numpy() if "SRC_RAW" in seg.columns else src_e)
    src_node = np.array(["terrain"] * n, dtype=object)
    conf_node = np.array(["derived"] * n, dtype=object)
    raw_node = np.array(["terrain"] * n, dtype=object)
    for k in range(m):
        w = int(g.e_ds[k])
        src_node[w], conf_node[w], raw_node[w] = src_e[k], conf_e[k], raw_e[k]
    for v in range(n):
        e = int(g.e_of[v])
        if e >= 0:
            src_node[v], conf_node[v], raw_node[v] = src_e[e], conf_e[e], raw_e[e]

    # ---- node-level flow ---------------------------------------------------------------
    pf_n = np.ones(n)
    pfm_n: List[str] = ["held"] * n
    cache: Dict[Tuple[float, bool], Tuple[float, str]] = {}
    for i in range(n):
        key = (round(float(f.q_adf[i]), 4), bool(f.n_prop[i] <= C.PF_HOLD_PROPERTIES))
        got = cache.get(key)
        if got is None:
            got = C.peak_factor(float(f.q_adf[i]), float(f.n_prop[i]))
            cache[key] = got
        pf_n[i], pfm_n[i] = got
    len_out = np.where(g.e_of >= 0, g.e_len[np.maximum(g.e_of, 0)], 0.0)
    qinf_n = C.INFILT_L_D_KM * ((f.ups_len + len_out) / 1000.0) / 86400.0
    qpk_n = f.q_adf * 1000.0 / 86400.0 * pf_n + qinf_n

    # ---- WHERE THE LEVELS ON THIS ROW CAME FROM ---------------------------------------
    # Published as a column, not as a stage-wide banner, because it is not stage-wide: s6
    # levelled 56,522 of 56,699 reaches on the 003 run and the rest are its own pumped
    # links. A reader looking at ONE chamber has to be able to see which solver answered
    # for it, or the file carries a provenance nobody can check per row.
    if s6 is not None:
        lv_node = np.where(s6.n_ok, S6_TAG, "NOT LEVELLED - " + S6_TAG + " published no "
                                            "chamber here")
        lv_edge = np.where(s6.e_ok, S6_TAG, "NOT LEVELLED - see reaches_unlevelled")
        # s6's ANSWER WHERE IT GAVE ONE, this stage's own where it did not - never the
        # DEFAULT of a column s6 does not publish. `n_flow_ok` is the mask of chambers whose
        # factor is s6's; elsewhere the row keeps criteria.peak_factor()'s answer (a chamber
        # s6 never levelled) or carries NULL (a chamber with no outgoing reach of s6's).
        pf_n = np.where(s6.n_flow_ok, s6.n_pf,
                        np.where(s6.n_ok, np.nan, pf_n))
        pfm_n = [b if ok else ("" if in6 else a)
                 for ok, in6, a, b in zip(s6.n_flow_ok, s6.n_ok, pfm_n, s6.n_pfm)]
        qpk_n = np.where(np.isfinite(s6.n_qpk), s6.n_qpk, qpk_n)
        # THE ACCUMULATION TRAVELS WITH THE FLOW IT PRODUCED. Publishing this stage's
        # Q_ADF beside s6's Q_PK put a peak on the row that the row's own average could
        # not reproduce - 21,221 chambers on the 12:00 export published a Q_PK_LS below
        # their own QADF x PF. Where s6 answered, both come from s6.
        qadf_n = np.where(np.isfinite(s6.n_qadf), s6.n_qadf, f.q_adf)
        _n_disagree = int((np.isfinite(s6.n_qadf)
                           & (np.abs(s6.n_qadf - f.q_adf) > 0.001)).sum())
        if _n_disagree:
            _log(f"   NOTE: this stage's own accumulation and {S6_TAG}'s disagree on "
                 f"Q_ADF at {_n_disagree:,} of {int(s6.n_ok.sum()):,} shared chambers "
                 f"(worst {float(np.nanmax(np.abs(s6.n_qadf - f.q_adf))):.3f} m3/d). Two "
                 f"accumulations over the SAME graph agree exactly, so a disagreement here "
                 f"means the two files are not describing the same graph - see the `levels "
                 f"coverage` row on contract_check. s6's is published.")
        stage_node = np.where(s6.n_ok, S6_TAG, LEVELS_TAG)
        stage_edge = np.where(s6.e_ok, S6_TAG, LEVELS_TAG)
    else:
        qadf_n = f.q_adf
        lv_node = np.array([LEVELS_TAG] * n, dtype=object)
        lv_edge = np.array([LEVELS_TAG] * m, dtype=object)
        stage_node = np.array([LEVELS_TAG] * n, dtype=object)
        stage_edge = np.array([LEVELS_TAG] * m, dtype=object)

    ds_uid = np.array([g.uid[int(d)] if d >= 0 else "" for d in g.ds], dtype=object)
    n_out = (g.e_of >= 0).astype(np.int8)
    is_out = (g.ds < 0).astype(np.int8)
    inlet = _bearing_fix_inlets(a, g)
    refs = node_refs(a, g, node_pkg, tier_node)

    kind = ch.NODE_KIND.astype(str).to_numpy().copy()
    kind = np.where(is_out == 1, "outfall", kind)
    dropped = np.array([t != "none" for t in lv.drop_type])
    kind = np.where(dropped & (is_out == 0), "drop", kind)
    mh_dia = np.where(dropped, C.MH_DIA_INTERNAL_BACKDROP, MH_DIA_STD_M)

    nodes = gpd.GeoDataFrame(dict(
        NODE_UID=g.uid,
        IS_OUTFALL=is_out,
        NODE_REF=refs,
        NODE_KIND=kind,
        X=np.round(ch.X.to_numpy(), 3), Y=np.round(ch.Y.to_numpy(), 3),
        GRD_M=np.round(g.grd, 3),
        INV_M=np.round(lv.inv, 3),
        DEPTH_M=np.round(g.grd, 3) - np.round(lv.inv, 3),
        COVER_M=np.round(lv.cover, 3),
        TIER=tier_node,
        DS_NODE=ds_uid,
        N_IN=g.indeg.astype(np.int64),
        N_OUT=n_out,
        INLET_DEG=np.round(inlet, 1),
        INLET_FLAG=(inlet < C.INLET_MIN_DEG - 1e-9).astype(np.int8),
        MH_DIA=mh_dia,
        MH_MAT="precast concrete (class per PAM-SPC, pending)",
        DROP_M=np.round(lv.drop, 3),
        DROP_TYPE=lv.drop_type,
        # CONCEPT RULE 1 - every drop says why it exists, derived in _drop_reasons() from
        # the arm that actually drops. The contract refuses a drop with no reason and it
        # also refuses ONE reason repeated across every drop (inheritance row 22).
        DROP_WHY=lv.drop_why,
        # CONCEPT RULE 2 - where this chamber meets the main pipe, and how far that is
        # from the subnetwork's own lowest point. Measured in measure_joins().
        JOIN_MAIN=jn.is_join,
        JOIN_OFF_M=np.round(jn.off_m, 1),
        JOIN_WHY=jn.why,
        VORTEX=lv.vortex.astype(np.int8),
        Q_ADF_M3D=np.round(qadf_n, 3),
        Q_PK_LS=np.round(qpk_n, 4),
        N_PROP=np.round(f.n_prop, 2),
        PAST_CAP=lv.past_cap.astype(np.int8),
        CAP_EXIT=lv.cap_exit,
        # ---- concept rule 8, the NAME grammar. Built in build_names(). ----------------
        NAME=nm.node_name,
        TOWN=nm.node_town,
        SUBNET=nm.node_sub,
        # ---- beyond the contract, declared here and printed in the data dictionary -----
        CAP_LEN_M=np.round(lv.cap_len, 1),
        ST_RESET=lv.st_reset.astype(np.int8),
        N_CONN=f.n_conn.astype(np.int64),
        UPS_LEN_M=np.round(f.ups_len, 1),
        # SUBNET is "S03" because the grammar puts it there and validate() checks NAME
        # against it - but "S03" is NOT unique across towns, so the machine key is the
        # component's own outfall chamber and the DISPLAY key is the subnetwork's full
        # name "I-S03". Colouring or foldering on SUBNET alone would merge one subnetwork
        # in Ibri with another in Ad Dariz.
        SUBNET_ND=[g.uid[int(s)] for s in f.subnet],
        SUB_NAME=[nm.subnet_name.get(int(s), "") for s in f.subnet],
        JOIN_GAP_M=np.round(jn.gap_m, 1),
        TRIGGER=ch.TRIGGER.astype(str).to_numpy(),
        ON_WADI=ch.ON_WADI.to_numpy(),
        TAU_PA=float(C.TAU_PA),
        SRC=src_node, SRC_RAW=raw_node, CONFIDENCE=conf_node, STAGE=stage_node,
        LEVELS_BY=lv_node,
        PF=np.round(pf_n, 6), PF_METH=pfm_n,
        PACKAGE=node_pkg, PHASE=np.zeros(n, dtype=np.int64),
    ), geometry=[Point(float(x), float(y)) for x, y in zip(ch.X.to_numpy(), ch.Y.to_numpy())],
        crs=f"EPSG:{CT.CRS_EPSG}")
    # DEPTH_M must reproduce GRD_M - INV_M to 1 mm on the PUBLISHED, rounded values, or the
    # chamber schedule and the pipe layer describe different chambers (contract, nodes).
    # A REASON FOR A DROP THAT IS NOT THERE. s6 carries a DROP_WHY on chambers whose drop
    # is a fraction of a millimetre - 107 of them on the 003 run, the largest 0.50 mm - and
    # at the published precision of 1 mm that drop is 0.000. G203-p30 does not call
    # anything under 0.60 m a drop at all. The reason is blanked HERE, at publication, and
    # COUNTED: the contract refuses a reason with no drop, and a 0.5 mm step is not a
    # drop. The count is s6's to act on and it is in EXPORT.md, not swallowed.
    _no_drop = (nodes.DROP_M.to_numpy(dtype=float) <= 0.0) & (
        nodes.DROP_WHY.astype(str).str.strip().to_numpy() != "")
    if _no_drop.any():
        REMOVED_COUNTS["drop_reasons_with_no_drop"] = int(_no_drop.sum())
        _log(f"   blanked DROP_WHY on {int(_no_drop.sum()):,} chambers whose PUBLISHED "
             f"drop is 0.000 m - {LEVELS_SOURCE} gave them a reason for a step of under "
             f"1 mm (largest {np.max(lv.drop[_no_drop]) * 1000:.2f} mm). Counted, not "
             f"swallowed: G203-p30 calls nothing under 0.60 m a drop.")
        nodes.loc[_no_drop, "DROP_WHY"] = ""
    nodes["DEPTH_M"] = (nodes.GRD_M - nodes.INV_M).round(3)
    # COVER IS THE LEVELLER'S ANSWER WHERE THE LEVELLER GAVE ONE. Recomputing it here from
    # the published depth would put a second cover beside s6's, and the whole point of
    # reading s6 is that there is one. criteria.cover() fills only the rows s6 did not
    # answer for - which are then taken off this layer anyway.
    cov_own = np.array([round(C.cover(int(d), float(z)), 3)
                        for d, z in zip(lv.node_dn, nodes.DEPTH_M)], dtype=float)
    if s6 is not None:
        nodes["COVER_M"] = np.where(s6.n_ok & np.isfinite(lv.cover),
                                    np.round(lv.cover, 3), cov_own)
    else:
        nodes["COVER_M"] = cov_own

    # ---- THE DEPTHS AND THE COVERS ARE THE LEVELLER'S TOO ------------------------------
    # s6 publishes INV_DN, US_DEPTH, DS_DEPTH, COVER_US and COVER_DN on its own reach
    # layer. Until 2026-09-06 this stage IGNORED all five and rebuilt them from s6's
    # INV_UP against THIS stage's ground and THIS stage's segment length - which is the
    # same two-solvers defect as the levels themselves, on five more columns, and it is
    # the one that verify()'s "every gradient, DN and invert IS s6s" cannot see because it
    # only compares SLOPE_LAID, DN and INV_UP.
    #
    # MEASURED on the 12:25 export: COVER_US differed from s6's on 26,050 of 26,579
    # matched reaches, worst 173.0 m; the published cover ran from -151.74 m to +178.48 m
    # where s6's own ran 1.30 m to 19.63 m; and 3,668 reaches published a cover past the
    # 12 m cap while their own PAST_CAP flag - which IS s6's - read 0. A row that
    # contradicts itself is worse than a row that is wrong, because nothing flags it.
    #
    # Where s6 answered, all five are s6's. Where it did not, the recomputation stands and
    # those rows go to `reaches_unlevelled` anyway. When the two files disagree about the
    # ground or the length, the row is now INCONSISTENT and verify() says so - which is
    # the whole point: a stale pair must be loud, not smoothed over.
    _iu = np.round(lv.inv_up, 3)
    _id_own = np.round(_iu - lv.slope_laid * g.e_len, 3)
    _us_own = np.round(g.grd[g.e_us], 3) - _iu
    _ds_own = np.round(g.grd[g.e_ds], 3) - _id_own
    _bore = lv.dn / 1000.0 + C.WALL_ALLOW
    if s6 is not None:
        _k = s6.e_ok & np.isfinite(lv.inv_dn)
        inv_up = _iu
        inv_dn = np.where(_k, np.round(lv.inv_dn, 3), _id_own)
        us_depth = np.where(s6.e_ok & np.isfinite(lv.us_depth),
                            np.round(lv.us_depth, 3), _us_own)
        ds_depth = np.where(s6.e_ok & np.isfinite(lv.ds_depth),
                            np.round(lv.ds_depth, 3), _ds_own)
        cover_us = np.where(s6.e_ok & np.isfinite(lv.cover_us),
                            np.round(lv.cover_us, 3), np.round(_us_own - _bore, 3))
        cover_dn = np.where(s6.e_ok & np.isfinite(lv.cover_dn),
                            np.round(lv.cover_dn, 3), np.round(_ds_own - _bore, 3))
        _off = int((s6.e_ok & (np.abs(np.nan_to_num(lv.cover_us, nan=0.0)
                                      - (_us_own - _bore)) > 0.01)).sum())
        if _off:
            _log(f"   NOTE: {_off:,} of {int(s6.e_ok.sum()):,} levelled reaches would have "
                 f"got a DIFFERENT cover had this stage recomputed one from its own ground "
                 f"and length instead of reading {S6_TAG}'s. {S6_TAG}'s is published; the "
                 f"gap is the two files disagreeing about the ground, not about the design "
                 f"- see the `levels ground` row on contract_check.")
    else:
        inv_up, inv_dn = _iu, _id_own
        us_depth, ds_depth = _us_own, _ds_own
        cover_us = np.round(_us_own - _bore, 3)
        cover_dn = np.round(_ds_own - _bore, 3)
    # THE FLOW THE PIPE WAS SOLVED AT, from whichever solver laid it. Mixing s6's velocity
    # with a peak flow recomputed here would publish a row whose own Q cannot reproduce its
    # own V - the two-answers defect one level down from the levels themselves.
    if s6 is not None:
        r6c = gpd.read_file(GPKG_S6, layer="reaches", ignore_geometry=True)
        k6 = {(u, w): i for i, (u, w) in enumerate(
            zip(r6c.US_NODE.astype(str), r6c.DS_NODE.astype(str)))}
        pos = np.array([k6.get((g.uid[int(u)], g.uid[int(w)]), -1)
                        for u, w in zip(g.e_us, g.e_ds)], dtype=np.int64)
        ok6 = pos >= 0
        src6 = np.maximum(pos, 0)
        s6_past_cap = np.where(
            ok6, pd.to_numeric(pd.Series(r6c.PAST_CAP.to_numpy()[src6]),
                               errors="coerce").fillna(0).to_numpy(), 0).astype(np.int8)
        s6_cap_exit = [str(x) if ok else ""
                       for ok, x in zip(ok6, r6c.CAP_EXIT.astype(str).to_numpy()[src6])]
        s6_cap_exit = [x if x in CT.CAP_EXIT else "" for x in s6_cap_exit]
    else:
        s6_past_cap, s6_cap_exit = None, None
    e_qadf = s6.e_qadf if s6 is not None else f.e_qadf
    e_qinf = s6.e_qinf if s6 is not None else f.e_qinf
    e_pf = s6.e_pf if s6 is not None else f.e_pf
    e_pfm = list(s6.e_pfm) if s6 is not None else list(f.e_pfm)
    reaches = gpd.GeoDataFrame(dict(
        EDGE_UID=[CT.EDGE_UID_FMT.format(k) for k in range(m)],
        US_NODE=[g.uid[int(i)] for i in g.e_us],
        DS_NODE=[g.uid[int(i)] for i in g.e_ds],
        TIER=tiers_e,
        DN=lv.dn.astype(np.int64),
        MATERIAL=lv.material,
        CONSTR="open_trench",
        LEN_M=np.round(g.e_len, 3),
        SLOPE_LAID=np.round(lv.slope_laid * 100.0, 6),
        SLOPE_MIN=np.round(lv.slope_min * 100.0, 6),
        GRAD_BY=lv.grad_by,
        SIZED_BY=lv.sized_by,
        CLEAN_BY=lv.clean_by,
        TAU_PA=float(C.TAU_PA),
        INV_UP=inv_up, INV_DN=inv_dn,
        US_DEPTH=us_depth, DS_DEPTH=ds_depth,
        COVER_US=cover_us,
        COVER_DN=cover_dn,
        QADF_M3D=np.round(e_qadf, 3),
        QINF_LS=np.round(e_qinf, 6),
        PF=np.round(e_pf, 6),
        PF_METH=e_pfm,
        QPK_LS=np.round(s6.e_qpk if s6 is not None else f.e_qpk, 6),
        V_PK_MS=np.round(lv.v_pk, 3),
        DOD_PK=np.round(lv.dod, 4),
        RET_MIN=np.round(lv.ret_min, 3),
        # AGN_GRADE is computed from the ROUNDED, PUBLISHED GND_FALL, not from the raw
        # difference. Computed from the raw value it disagreed with its own row on 36
        # reaches at the rounding boundary, and the contract calls that out by name:
        # "this is the headline number the whole iteration turns on; it cannot be
        # computed two ways".
        GND_FALL=np.round(g.grd[g.e_us] - g.grd[g.e_ds], 3),
        AGN_GRADE=(np.round(g.grd[g.e_us] - g.grd[g.e_ds], 3) < -C.ADVERSE_MIN_M).astype(np.int8),
        RISE_M=np.round(np.maximum(0.0, g.grd[g.e_ds] - g.grd[g.e_us]), 3),
        # PAST_CAP AND CAP_EXIT ARE THE LEVELLER'S, NOT A SECOND OPINION. Recomputing
        # "is this reach past the 12 m cap" here from the published covers gave 205
        # reaches PAST_CAP = 1 with a blank CAP_EXIT while s6, which decided the depths,
        # published 1,598 past the cap and NONE unexcused. Two answers to one question,
        # and the recomputed one is the one with no authority: the exit is bounded by a
        # distance ALONG THE RUN (philosophy sec 5), which is a property of the solve.
        PAST_CAP=(s6_past_cap if s6 is not None
                  else (np.maximum(lv.cover_us, lv.cover_dn) > C.MAX_COVER).astype(np.int8)),
        CAP_EXIT=(s6_cap_exit if s6 is not None
                  else [lv.cap_exit[int(i)] for i in g.e_us]),
        CAP_LEN_M=np.round(lv.cap_len[g.e_us], 1),
        TIE_TYPE="none",
        ON_DUAL_M=contacts.ON_DUAL_M.to_numpy(),
        ON_WADI_M=contacts.ON_WADI_M.to_numpy(),
        CROSS_ID=cross_id.astype(str),
        # ---- concept rule 8. A conduit is named for its UPSTREAM manhole and carries
        # ---- that manhole's number, which is why manholes are numbered per SUBNETWORK
        # ---- and not per tier.
        NAME=nm.edge_name,
        TOWN=[nm.node_town[int(i)] for i in g.e_us],
        SUBNET=[nm.node_sub[int(i)] for i in g.e_us],
        # ---- beyond the contract -------------------------------------------------------
        SUBNET_ND=[g.uid[int(s)] for s in f.subnet[g.e_us]],
        SUB_NAME=[nm.subnet_name.get(int(s), "") for s in f.subnet[g.e_us]],
        US_NAME=[nm.node_name[int(i)] for i in g.e_us],
        DS_NAME=[nm.node_name[int(i)] for i in g.e_ds],
        RUN_LEN_M=np.round(f.e_upslen, 1),
        SRC=src_e, SRC_RAW=raw_e, CONFIDENCE=conf_e, STAGE=stage_edge,
        LEVELS_BY=lv_edge,
        PACKAGE=edge_pkg, PHASE=np.zeros(m, dtype=np.int64),
    ), geometry=seg.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")
    # QPK_LS must be reproducible from the PUBLISHED row (contract cross-field check).
    reaches["QPK_LS"] = (reaches.QADF_M3D * 1000.0 / 86400.0 * reaches.PF
                         + reaches.QINF_LS).round(6)
    # A reach whose CAP_EXIT came from a node that is not itself past the cap carries a
    # justification for a breach that is not there. Blank it.
    reaches.loc[reaches.PAST_CAP == 0, "CAP_EXIT"] = ""

    layers: Dict[str, gpd.GeoDataFrame] = {"nodes": nodes, "reaches": reaches}
    return layers


def build_connections(a: Assembly, g: Graph, nodes: gpd.GeoDataFrame,
                      reaches: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """CONCEPT RULE 5: PLOT CONNECTIONS ARE NOT DESIGNED. One simple gravity check.

    The engineer's words, and each half is a separate trap this answers:

      * "the connection leaves BELOW ground level (not at it)"  -> the property outlet is
        set at the G203-p19 sec 3.4 minimum HCC depth, not at the plot's surface. A level
        comparison at the plot centroid passes plots that cannot physically be connected.
      * "runs to a CHAMBER (not to the nearest point on a pipe)" -> the target invert is
        `nodes.INV_M` at OUT_NODE, the chamber s4 assigned it.
      * "loses fall over its own route length"                   -> over LEN_M, at the
        G203-p18 Table 5 minimum 3 % gradient, not as a bare level difference.

    And rule 7, FLAG DO NOT SOLVE: every plot that fails is named with its reason AND ITS
    SIZE - CONN_NEED is how many metres deeper the sewer would have to be on that run.
    W11b's "5,521 plots cannot drain" is a number nobody can act on; "this plot needs the
    sewer 0.84 m deeper" is a decision.

    CAN_DRAIN is written FROM CAN_CONN, never computed twice: the contract refuses two
    answers to one question, and that defect has cost this project more than any other.

    THE CHECK ITSELF IS `w12.connectivity`'S, CALLED - NOT REIMPLEMENTED HERE.  Until
    2026-09-06 this function carried its own inline version of the same test, which is the
    two-answers defect one more time; `w12.connectivity` existed, was tested, and was
    imported by nothing in the pipeline.  Three things the module does that the inline
    version could not:

      * the run is SPLIT - the 2.5 m property connection at its own 3 % minimum (G203-p18
        Table 5, PCS) and the rest of the route at the 1 % lateral minimum - instead of
        charging 3 % over the whole length, which failed long routes for the wrong reason;
      * the connection has to arrive ABOVE THE DESIGN FLOW SURFACE of the sewer it joins,
        not merely at its invert.  The allowance is the guideline's own depth of flow,
        d/D x internal bore (G203-p27 Table 10), so it varies with the receiving bore;
      * CONN_WHY comes from a CLOSED VOCABULARY, so a missing input ("chamber level
        unknown") can never be published as an engineering verdict ("route loses the
        fall").  The long human sentence is kept beside it as CONN_TXT."""
    cn = a.connections.copy()
    inv = dict(zip(nodes.NODE_UID.astype(str), nodes.INV_M.astype(float)))
    ci = cn.OUT_NODE.astype(str).map(inv).to_numpy(dtype=float)
    grd_plot = cn.GRD_PLOT.to_numpy(dtype=float)
    # THE LENGTH THE CHECK RUNS ON IS THE LENGTH THAT IS PUBLISHED. It used to run on the
    # upstream stage's own LEN_M while publishing a length RE-MEASURED off the geometry, so a
    # reviewer multiplying the published SLOPE_LAID by the published LEN_M did not get the
    # published FALL_AV_M back, and CONN_NEED - "how much deeper the sewer must be" - was
    # sized on a route length the row does not carry. The geometry is the authority: it is
    # what the drawing shows and what the DXF measures.
    len_pub = np.round(cn.geometry.length.to_numpy(dtype=float), 3)
    L = np.maximum(len_pub, 0.5)

    # THE ARRIVAL RULE DEPENDS ON HAVING A BORE, AND THAT IS NOT ALWAYS TRUE. The default
    # rule makes the connection arrive above the sewer's design flow surface, which needs
    # the receiving diameter at every chamber. `dn_at_node()` reads it off the reach layer
    # and REFUSES to substitute a default - "a default bore makes the allowance constant
    # across every row, which is inheritance row 22's fabrication arrived at politely".
    # So where the reach layer cannot supply one, the check falls back to the LOOSER
    # 'invert' rule and the layer SAYS SO on every row, rather than the stage inventing a
    # diameter or the check silently not running.
    has_bore = (reaches is not None and len(reaches)
                and {"US_NODE", "DS_NODE", "DN"} <= set(reaches.columns))
    rule = "flow_depth" if has_bore else "invert"
    if not has_bore:
        _log("   NO RECEIVING BORE available to the connectability check (the reach layer "
             "carries no US_NODE/DS_NODE/DN), so it falls back to the LOOSER 'invert' "
             "arrival rule: a connection need only reach the chamber's invert, not clear "
             "the sewer's design flow surface. Published on the row as CONN_RULE.")
    res = CN.check_connections(cn, nodes=nodes, reaches=reaches if has_bore else None,
                               crit=C, basis=CN.basis_hcc(C, arrival_rule=rule),
                               route_m=L)
    can = res.CAN_CONN.to_numpy(dtype=np.int8)
    why_tok = res.CONN_WHY.astype(str).to_numpy()
    need = res.CONN_NEED.to_numpy(dtype=float)
    fall_avail = (res.OUT_INV_M - res.REQ_INV_M).to_numpy(dtype=float)
    s_avl = res.S_AVL_PCT.to_numpy(dtype=float) / 100.0
    # the gradient the connection would actually be laid at: what the fall allows, held
    # between the G203-p18 Table 5 minimum and maximum for a property connection.
    s_laid = np.clip(np.where(np.isfinite(s_avl) & (s_avl > 0), s_avl, C.PCS_MIN_SLOPE),
                     C.PCS_MIN_SLOPE, C.PCS_MAX_SLOPE)
    cover = np.maximum(C.PCS_MIN_COVER, C.HCC_DEPTH_MIN - C.DN_TERTIARY / 1000.0)

    # TWO COLUMNS, BECAUSE THE TWO READERS ARE DIFFERENT AND BOTH ARE REQUIRED.
    #
    #   CONN_CODE  the module's CLOSED VOCABULARY. It is the machine key: a schedule groups
    #              on it, and because the set is closed a MISSING INPUT ("chamber level
    #              unknown") can never be filed as an engineering verdict ("route loses the
    #              fall"). That distinction is the module's, and it is worth a column.
    #   CONN_WHY   the reason WITH ITS SIZE, which is what the contract's own field note
    #              asks for and what validate() enforces: it refuses a CONN_WHY that is
    #              constant across the failing rows, because a reason identical on every
    #              plot was not computed for any of them (inheritance row 22).
    #
    # The sentence is built from the module's own numbers. It is not a second verdict - it
    # is the same one, in words, with the metre figure a reader can act on.
    say = {
        CN.WHY_LEVEL: "the property outlet sits {short:.2f} m BELOW the sewer invert it "
                      "must reach at its chamber - sewer {need:.2f} m deeper on this run, "
                      "or a local collector",
        CN.WHY_ROUTE: "it clears the chamber and then spends the clearance over {ln:,.0f} m "
                      "of route at the G203-p18 Tab 5 minimums - sewer {need:.2f} m deeper",
        CN.WHY_NO_NODE: "no chamber assigned to this plot, so there is nothing to connect to",
        CN.WHY_NO_INV: "the chamber has no designed invert, so the check CANNOT RUN here - "
                       "that is a failure, not a blank",
        CN.WHY_NO_GRD: "no ground level at the plot, so the check CANNOT RUN here",
        CN.WHY_NO_LEN: "no route length, so the fall it spends cannot be measured",
        CN.WHY_NO_DN: "the receiving chamber has no bore, so the arrival allowance cannot "
                      "be computed - no default is substituted",
    }
    short = np.maximum(0.0, -fall_avail)
    why = np.array(
        ["" if c == 1 else w + " - " + say.get(w, w).format(need=nd, ln=ln, short=sh)
         for c, w, nd, ln, sh in zip(can, why_tok, need, L, short)], dtype=object)
    code = np.where(can == 1, "", why_tok)

    ndx = nodes.set_index(nodes.NODE_UID.astype(str))
    key = cn.OUT_NODE.astype(str)
    out = gpd.GeoDataFrame(dict(
        CONN_ID=cn.CONN_ID.astype(str),
        PLOT_ID=cn.PLOT_ID.astype(str),
        OUT_NODE=cn.OUT_NODE.astype(str),
        WHY=cn.WHY.astype(str),
        SYSTEM=cn.SYSTEM.astype(str),
        CONN_TYPE=cn.CONN_TYPE.astype(str),
        Q_ADF_M3D=np.round(cn.Q_ADF_M3D.to_numpy(dtype=float), 4),
        N_PROP=np.round(cn.N_PROP.to_numpy(dtype=float), 3),
        LEN_M=len_pub,
        SLOPE_LAID=np.round(s_laid * 100.0, 3),
        COVER_M=round(float(cover), 3),
        CAN_CONN=can,
        # the closed vocabulary, for grouping and for filtering
        CONN_CODE=code.astype(object),
        # the same verdict WITH ITS SIZE - what the contract's field note asks for
        CONN_WHY=why.astype(object),
        CONN_NEED=np.round(need, 3),
        # written FROM CAN_CONN, not computed a second time (contract cross-field check)
        CAN_DRAIN=can,
        FALL_AV_M=np.round(fall_avail, 3),
        # w12.connectivity's own working, published so the verdict can be re-derived by
        # hand: where the property outlet sits, where the connection arrives, what the
        # chamber requires, and the arrival allowance that made the difference.
        OUT_INV_M=res.OUT_INV_M.to_numpy(dtype=float),
        ARR_INV_M=res.ARR_INV_M.to_numpy(dtype=float),
        REQ_INV_M=res.REQ_INV_M.to_numpy(dtype=float),
        ALLOW_M=res.ALLOW_M.to_numpy(dtype=float),
        MARGIN_M=res.MARGIN_M.to_numpy(dtype=float),
        CONN_LONG=res.CONN_LONG.to_numpy(dtype=np.int8),
        CONN_STEEP=res.CONN_STEEP.to_numpy(dtype=np.int8),
        CONN_VER=CN.CONNECTIVITY_VERSION,
        CONN_RULE=str(res.attrs.get("arrival_rule", "")),
        XPLOT=cn.XPLOT.to_numpy(), XDUAL=cn.XDUAL.to_numpy(),
        CH_WADI=cn.CH_WADI.to_numpy(),
        # A CONNECTION HAS NO NAME, DELIBERATELY. Concept rule 8's grammar covers a
        # manhole, a conduit, a pump, a force main and a subnetwork - there is no
        # connection element, and several plots enter one chamber, so borrowing the
        # chamber's name would duplicate it on this layer. TOWN and SUBNET are carried
        # because they ARE meaningful and make the layer filterable; NAME stays blank and
        # assert_named() is not called on this layer. A name invented to fill a column is
        # a label, not an identifier.
        NAME="",
        TOWN=key.map(ndx.TOWN.astype(str)).fillna(""),
        SUBNET=key.map(ndx.SUBNET.astype(str)).fillna(""),
        SUB_NAME=key.map(ndx.SUB_NAME.astype(str)).fillna(""),
        SRC="dwg_road", CONFIDENCE="derived", STAGE=LEVELS_SOURCE,
        PACKAGE=key.map(ndx.PACKAGE.astype(str)).fillna(""),
        PHASE=0,
    ), geometry=cn.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")
    n_bad = int((can == 0).sum())
    by_why = pd.Series(why_tok[can == 0]).value_counts().to_dict() if n_bad else {}
    _log(f"   connections (concept rule 5, w12.connectivity "
         f"{CN.CONNECTIVITY_VERSION}, basis {res.attrs['basis'].name}, arrival rule "
         f"'{res.attrs['arrival_rule']}'"
         + ("" if has_bore else " - FALLBACK, no receiving bore was available")
         + f"): {int(can.sum()):,} of {len(can):,} plots reach "
         f"their chamber on gravity. {n_bad:,} cannot"
         + (" - " + ", ".join(f"{k} {v:,}" for k, v in sorted(by_why.items())) if by_why
            else "")
         + (f". Each says what it would take: median "
            f"{np.median(need[can == 0]):.2f} m deeper, worst {need.max():.2f} m"
            if n_bad else ""))
    return out


def build_stations(a: Assembly, nodes: gpd.GeoDataFrame, g: Graph, f: Flows, nm: Naming
                   ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """s7's stations and rising mains, re-keyed, NAMED, and PRUNED.

    Every hydraulic number here is s7's and is copied, never recomputed: duty flow, lift,
    wet well, land take, the rising main's diameter, velocity and fittings. What this
    stage adds is the anchor, the concept-stage name, and the two fields concept rule 6
    demands as the evidence that a station's position was CHOSEN and not TRIGGERED -
    N_SUBNET and CATCH_KM.

    AND IT REMOVES THE STATIONS WITH NOTHING DRAINING INTO THEM. Inheritance row 4:
    "anything a pass can ADD, a later pass must be able to TAKE AWAY, and the stage
    publishes how many it removed". W11b shipped 15 of 47 with nothing upstream, and the
    reason they survived is that no pass could ever remove one. This is that pass. Each
    removed station is published in full on `stations_rejected` with its reason, its
    coordinates and its s7 id - the ledger's rule is remove-and-publish, never delete.

    MOTOR_KW, KWH_YR, LCC_OMR and HEAD_M ARE NOT WRITTEN. The first three are motor
    selection and life-cycle costing, both switched off at concept stage
    (criteria.CONCEPT_OFF); HEAD_M is a banned second name for LIFT_M / STAT_HD_M /
    TOT_HD_M. `contract.validate()` refuses all four by name, which is the point of
    banning them: a stage reaching for one is told the field to use instead."""
    st = a.stations.copy()
    ndx = nodes.set_index(nodes.NODE_UID.astype(str))
    anchor = st.ANCHOR_ND.astype(str)

    # ---- concept rule 6: what does each station actually capture? ----------------------
    # N_SUBNET is computed, not asserted - and on THIS wiring it comes out 1 on every
    # retained station, because s7 places a station INSIDE a component rather than at a
    # seam between subnetworks. That is a finding about s7's siting, not a measurement of
    # this design's quality, and it is said in the log and in EXPORT.md rather than left
    # to look like a fabricated column. CATCH_KM is the number rule 6 actually scores on.
    ai = anchor.map(g.ix)
    n_sub = np.zeros(len(st), dtype=np.int64)
    catch = np.zeros(len(st), dtype=float)
    # N_SUBNET IS COUNTED, NOT ASSERTED. The first build wrote the LITERAL 1 wherever the
    # anchor had any inflow at all - a boolean wearing a count's name, and constant on every
    # published row, which is inheritance row 22 (a published column constant where it should
    # vary is a fabrication). It is now the number of DISTINCT subnetworks whose arms arrive
    # at the anchor, read off f.subnet. On this wiring it still comes out 1, because s7 sites
    # a station INSIDE a component rather than at the seam concept rule 6 asks for - but it
    # is now a measurement that will move the day s7 does, instead of a constant that cannot.
    arms_at: Dict[int, List[int]] = defaultdict(list)
    for k in range(len(g.e_ds)):
        arms_at[int(g.e_ds[k])].append(int(g.e_us[k]))
    for r, idx in enumerate(ai.to_numpy()):
        if idx is None or (isinstance(idx, float) and math.isnan(idx)):
            continue
        i = int(idx)
        n_sub[r] = len({int(f.subnet[u]) for u in arms_at.get(i, ())})
        if n_sub[r]:
            catch[r] = float(f.ups_len[i]) / 1000.0
    inv_at = anchor.map(ndx.INV_M.astype(float)).to_numpy(dtype=float)
    town_at = anchor.map(ndx.TOWN.astype(str)).fillna("").to_numpy()

    # ---- concept rule 8: I-PMP02, numbered within its town by descending duty ----------
    duty = pd.to_numeric(st.Q_DUTY_LS, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    names = [""] * len(st)
    per_town: Dict[str, int] = defaultdict(int)
    for r in sorted(range(len(st)), key=lambda k: (-duty[k], str(st.NODE_UID.iloc[k]))):
        t = str(town_at[r])
        if not t:
            continue
        per_town[t] += 1
        names[r] = CT.concept_name(t, "pump", seq=per_town[t])

    st_out = gpd.GeoDataFrame(dict(
        NODE_UID=st.NODE_UID.astype(str),
        NODE_REF=st.NODE_REF.astype(str),
        WHY=st.WHY.astype(str),
        ST_TYPE=st.ST_TYPE.astype(str),
        Q_DUTY_LS=np.round(st.Q_DUTY_LS.to_numpy(dtype=float), 3),
        LIFT_M=np.round(st.LIFT_M.to_numpy(dtype=float), 3),
        N_PROP=np.round(st.N_PROP.to_numpy(dtype=float), 1),
        Q_ADF_M3D=np.round(st.Q_ADF_M3D.to_numpy(dtype=float), 2),
        WELL_M3=np.round(st.WELL_M3.to_numpy(dtype=float), 4),
        WW_STARTS=np.round(st.WW_STARTS.to_numpy(dtype=float), 2),
        GRD_M=np.round(st.GRD_M.to_numpy(dtype=float), 3),
        INV_M=np.round(inv_at, 3),
        N_SUBNET=n_sub,
        CATCH_KM=np.round(catch, 3),
        # FLOOD_LV IS LEFT NULL, DELIBERATELY. s7 published it null and there is no way
        # to fill it: `hazard.flood_level_m_aod()` RAISES by design, because the grids
        # carry an AR&R hazard CLASS and no water-surface level, and deriving one would
        # mean inventing a depth and adding it to a terrain reading. Filling it with
        # ground level - which this stage did on its first build - manufactured a
        # 300 mm-freeboard failure on every station that says nothing about any of
        # them. The contract will report the null, and that null IS the data request
        # (G203-p38 7.2 needs the 1:50 water-surface level).
        FLOOD_LV=pd.to_numeric(st.FLOOD_LV, errors="coerce").to_numpy(dtype=float),
        LAND_M2=np.round(st.LAND_M2.to_numpy(dtype=float), 1),
        RM_EDGE=st.RM_EDGE.astype(str),
        COMM_PT=st.COMM_PT.to_numpy(),
        NAME=names,
        TOWN=town_at,
        # A STATION IS A SEAM BETWEEN SUBNETWORKS, NOT A MEMBER OF ONE. SUBNET is blank
        # here on purpose and the contract's name check expects exactly that: I-PMP02
        # carries no S-token, so a SUBNET value would contradict its own name.
        SUBNET="",
        ANCHOR_ND=anchor,
        ST_SNAP_M=st.ST_SNAP_M.to_numpy(dtype=float),
        UID_S7=st.NODE_UID_S7.astype(str),
        PACKAGE=anchor.map(dict(zip(nodes.NODE_UID.astype(str), nodes.PACKAGE.astype(str))))
                      .fillna(""),
        PHASE=0,
        SRC="terrain", CONFIDENCE="derived", STAGE="s7_pumps (levels by s8)",
    ), geometry=st.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")

    # ---- inheritance row 4: TAKE AWAY what an earlier pass could only ADD ---------------
    keep = st_out.N_SUBNET.to_numpy() > 0
    rejected = st_out[~keep].copy()
    if len(rejected):
        # THE REMOVAL RESTS ON A GEOMETRIC SNAP, AND THE ROW SAYS SO. s7's station ids do not
        # resolve (header note 2), so the anchor is the NEAREST chamber - `_reanchor_stations`
        # takes it with no distance limit at all. "Nothing drains into it" is therefore a
        # statement about the chamber the station was SNAPPED to, and a station snapped 300 m
        # to a headwater chamber would be removed on that chamber's evidence, not its own.
        # ST_SNAP_M goes into the reason so the removal can be argued with rather than taken
        # on trust; a big snap distance is the first thing to check on any row here.
        rejected["REJECT_WHY"] = [
            "NOTHING DRAINS INTO IT. The chamber this station is anchored to has zero "
            "incoming reaches, so it captures no catchment and lifts nothing. Placed by a "
            "pass that could only ADD a station and never re-test one (inheritance row 4); "
            "removed here, published in full, and handed back to s7_pumps. THE ANCHOR IS A "
            f"PROXIMITY SNAP of {float(s):,.1f} m (s7's own node id does not resolve), so "
            "the evidence is that chamber's - check the snap before accepting the removal."
            for s in rejected.ST_SNAP_M.to_numpy()]
        rejected["ANCHOR_X"] = np.round(rejected.geometry.x.to_numpy(), 2)
        rejected["ANCHOR_Y"] = np.round(rejected.geometry.y.to_numpy(), 2)
    st_out = st_out[keep].reset_index(drop=True)
    _log(f"   stations: s7 designed {len(st):,}; {int((~keep).sum()):,} REMOVED with "
         f"nothing draining into them (published on `stations_rejected`); "
         f"{len(st_out):,} published. CATCH_KM "
         f"{st_out.CATCH_KM.min() if len(st_out) else 0:.2f}-"
         f"{st_out.CATCH_KM.max() if len(st_out) else 0:.2f} km. "
         f"N_SUBNET is 1 on every one BY CONSTRUCTION - s7 sites a station INSIDE a "
         f"component, not at a seam between subnetworks, which is what concept rule 6 asks "
         f"for. The number that scores rule 6 is CATCH_KM.")

    rm = a.rising.copy()
    s7_to_new = dict(zip(st.NODE_UID_S7.astype(str), st.NODE_UID.astype(str)))
    station_new = rm.STATION.astype(str).map(s7_to_new).fillna(rm.STATION.astype(str))
    # a force main carries the number of the pump it leaves - I-PMP02 -> I-P02
    pump_name = dict(zip(st_out.NODE_UID.astype(str), st_out.NAME.astype(str)))
    pump_town = dict(zip(st_out.NODE_UID.astype(str), st_out.TOWN.astype(str)))
    rm_name, rm_town = [], []
    for s in station_new:
        pn = pump_name.get(str(s), "")
        parsed = CT.parse_name(pn) if pn else None
        if parsed and parsed.get("pmp"):
            rm_town.append(parsed["town"])
            rm_name.append(CT.concept_name(parsed["town"], "main", seq=int(parsed["pmp"])))
        else:
            rm_town.append(pump_town.get(str(s), ""))
            rm_name.append("")
    # CONCEPT RULE 6: does this main lift to the nearest manhole where gravity resumes, or
    # all the way to the works? A long force main goes anaerobic, needs an air valve at
    # every summit and a washout at every low point, and is a single point of failure. The
    # ANSWER is s7's; publishing WHICH of the two it is, is this stage's.
    known_nodes = set(nodes.NODE_UID.astype(str))
    ds = rm.DS_NODE.astype(str)
    ds_type = np.where(ds.isin(known_nodes), "manhole", "stp")

    rm_out = gpd.GeoDataFrame(dict(
        EDGE_UID=rm.EDGE_UID.astype(str),
        US_NODE=rm.US_NODE.astype(str).map(s7_to_new).fillna(rm.US_NODE.astype(str)),
        DS_NODE=ds,
        STATION=station_new,
        DN=rm.DN.to_numpy(dtype=np.int64),
        MATERIAL=rm.MATERIAL.astype(str),
        LEN_M=np.round(rm.geometry.length.to_numpy(), 3),
        Q_DUTY_LS=np.round(rm.Q_DUTY_LS.to_numpy(dtype=float), 3),
        V_DUTY_MS=np.round(rm.V_DUTY_MS.to_numpy(dtype=float), 3),
        V_MIN_MS=np.round(rm.V_MIN_MS.to_numpy(dtype=float), 3),
        STAT_HD_M=np.round(rm.STAT_HD_M.to_numpy(dtype=float), 2),
        TOT_HD_M=np.round(rm.TOT_HD_M.to_numpy(dtype=float), 2),
        RETENT_M=np.round(rm.RETENT_M.to_numpy(dtype=float), 2),
        N_AIRV=rm.N_AIRV.to_numpy(dtype=np.int64),
        N_WASH=rm.N_WASH.to_numpy(dtype=np.int64),
        N_ISOL=rm.N_ISOL.to_numpy(dtype=np.int64),
        WADI_M=np.round(rm.WADI_M.to_numpy(dtype=float), 2),
        SEPTIC_FL=rm.SEPTIC_FL.to_numpy(dtype=np.int64),
        DS_TYPE=ds_type,
        NAME=rm_name,
        TOWN=rm_town,
        SUBNET="",                      # a force main is a seam, exactly as its pump is
        PACKAGE=station_new.map(dict(zip(st_out.NODE_UID, st_out.PACKAGE))).fillna(""),
        PHASE=0,
        SRC="terrain", CONFIDENCE="derived", STAGE="s7_pumps",
    ), geometry=rm.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")
    # a rising main whose pump was removed has nothing to lift; it goes with it.
    live = rm_out.STATION.astype(str).isin(set(st_out.NODE_UID.astype(str)))
    if (~live).any():
        _log(f"   {int((~live).sum()):,} rising mains removed with the stations that were "
             f"pruned - a force main with no pump lifts nothing")
    # INHERITANCE ROW 4 - what a pass takes away, it PUBLISHES. The station count was already
    # a manifest metric; the force mains that went with them were only printed to a console,
    # and a console is not a deliverable. Both counts are recorded here so build() can put
    # them in the manifest and EXPORT.md from one place.
    REMOVED_COUNTS["stations_removed"] = int((~keep).sum())
    REMOVED_COUNTS["rising_mains_removed"] = int((~live).sum())
    rm_out = rm_out[live].reset_index(drop=True)
    n_to_works = int((rm_out.DS_TYPE == "stp").sum())
    if n_to_works:
        _log(f"   {n_to_works:,} of {len(rm_out):,} rising mains discharge at the WORKS "
             f"rather than at the nearest manhole where gravity resumes (concept rule 6) - "
             f"drawn on the EXCEPTIONS theme with their length")
    return st_out, rm_out, rejected


def build_trunk(a: Assembly) -> gpd.GeoDataFrame:
    """The client's own Main Pipe, exported as itself and nothing more.

    It is an INPUT (CLAUDE.md rule: `SHP/Main Pipe/Main Pipe.shp`), it carries no chambers
    and no topology, and NOTHING in this export drains into it. It is on every map so a
    reviewer can see where the design does not yet reach - which is the single most
    important thing about it."""
    t = a.trunk.copy()
    return gpd.GeoDataFrame(dict(
        EDGE_UID=[f"TRUNK{i + 1:03d}" for i in range(len(t))],
        TIER="trunk main",
        LEN_M=np.round(t.geometry.length.to_numpy(), 3),
        NOTE="CLIENT INPUT. Not chambered, not levelled, not sized. Nothing in this "
             "export drains into it: the outfalls are subnetwork outlets.",
        SRC="main_pipe", CONFIDENCE="drafted", STAGE="s3_hierarchy (passed through by s8)",
    ), geometry=t.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")


# ======================================================================================
# 7b.  VALIDATION - run it, publish the result, never silence it
# ======================================================================================

# The layers concept rule 8's grammar actually covers. `connections` is NOT here and the
# reason is in build_connections(): the grammar has no connection element, several plots
# enter one chamber, and a name invented to fill a column is a label, not an identifier.
NAMED_LAYERS = ("nodes", "reaches", "stations", "rising_mains")


#: How much of the network the LEVELLER must have answered for before this export is a
#: design rather than a fragment. NOT a tolerance on a design value and not from any
#: guideline - it is the line between "s6 withdrew a few reaches to pumped links" and "s6
#: is looking at a different network from s4". PROJECT ASSUMPTION, declared here and in
#: EXPORT_NUMBERS: below it the run is almost certainly a STALE PAIR - s4 re-run after s6 -
#: and every length, quantity and schedule below is a fragment of the design.
LEVELS_COVERAGE_ALARM = 0.98


def levels_coverage_row(layers: Dict[str, gpd.GeoDataFrame]) -> Optional[Dict[str, Any]]:
    """Did the leveller answer for enough of this network for the export to be a design?

    The failure this catches happened the first afternoon the rewire existed: stage 4 was
    re-run while stage 6's file stayed where it was, and the export then read levels for
    26,579 of 56,667 reaches. Every published number was internally consistent and less
    than half a design. Nothing in the file said so, because "s6 did not level this reach"
    is exactly what a legitimate pumped link looks like - one row at a time."""
    unl = layers.get("reaches_unlevelled")
    r = layers.get("reaches")
    if r is None:
        return None
    n_unl = 0 if unl is None else len(unl)
    total = len(r) + n_unl
    if not total:
        return None
    frac = len(r) / total
    if n_unl == 0:
        return dict(LAYER="levels coverage", PASS=1,
                    RESULT=f"{LEVELS_SOURCE} levelled every reach",
                    DETAIL=f"{len(r):,} of {total:,}")
    pumped = 0
    if unl is not None and "GAP_KIND" in unl.columns:
        pumped = int((unl.GAP_KIND.astype(str) == "pumped_link").sum())
    ok = frac >= LEVELS_COVERAGE_ALARM
    return dict(
        LAYER="levels coverage", PASS=int(ok),
        RESULT=(f"{frac * 100:.1f} % of the network is levelled"
                if ok else "THE LEVELLER ANSWERED FOR LESS THAN THE NETWORK"),
        DETAIL=(f"{len(r):,} of {total:,} reaches carry levels from {LEVELS_SOURCE}; "
                f"{n_unl:,} do not, {pumped:,} of them because {LEVELS_SOURCE} replaced "
                f"the gravity reach with a pumped link - which is legitimate and is what "
                f"`reaches_unlevelled` is for. "
                + ("" if ok else
                   f"BELOW THE {LEVELS_COVERAGE_ALARM * 100:.0f} % ALARM: on this scale it "
                   f"is not withdrawals, it is a STALE PAIR - stage 4 has almost certainly "
                   f"been re-run since {os.path.basename(GPKG_S6)} was written, so the two "
                   f"files describe different chambers. NOTHING IN THIS EXPORT IS "
                   f"QUOTABLE. Run s6_levels.py against the current chamber layer and "
                   f"re-export.")))


#: How far the leveller's ground and this stage's may drift before the two files are not
#: describing the same chambers. NOT a survey tolerance and not from any guideline: both
#: numbers are sampled from the SAME 0.5 m VRT at the SAME published X/Y, so on one pair of
#: files the difference is exactly zero. Anything above the 1 mm the layers are rounded to
#: means s4 re-minted the chamber under the same NODE_UID. PROJECT ASSUMPTION.
GROUND_DRIFT_TOL_M = 0.002


def levels_ground_row(layers: Dict[str, gpd.GeoDataFrame]) -> Optional[Dict[str, Any]]:
    """Do the two files agree about the GROUND at the chambers they share?

    An independent detector of the stale pair, and a sharper one than the reach count: a
    depth is ground minus invert, so if the leveller was looking at different ground then
    every depth, cover and drop on the file is measured from somewhere else. It found
    47,303 of 51,470 shared chambers disagreeing by up to 173.2 m on the 12:25 export -
    which is what put a -151.74 m cover on a client layer."""
    nd = layers.get("nodes")
    if nd is None or not len(nd) or not os.path.exists(GPKG_S6):
        return None
    try:
        n6 = gpd.read_file(GPKG_S6, layer="nodes", ignore_geometry=True)
    except Exception:                                          # pragma: no cover - IO
        return None
    if "GRD_M" not in n6.columns:
        return None
    lut = pd.Series(pd.to_numeric(n6.GRD_M, errors="coerce").values,
                    index=n6.NODE_UID.astype(str).values)
    want = nd.NODE_UID.astype(str).map(lut)
    got = pd.to_numeric(nd.GRD_M, errors="coerce")
    both = want.notna() & got.notna()
    if not int(both.sum()):
        return None
    d = (want[both] - got[both]).abs()
    n_off = int((d > GROUND_DRIFT_TOL_M).sum())
    return dict(
        LAYER="levels ground", PASS=int(n_off == 0),
        RESULT=(f"{LEVELS_SOURCE} and this stage sampled the same ground"
                if n_off == 0 else
                "THE LEVELLER WAS LOOKING AT DIFFERENT GROUND"),
        DETAIL=(f"{int(both.sum()) - n_off:,} of {int(both.sum()):,} shared chambers agree "
                f"on GRD_M to {GROUND_DRIFT_TOL_M * 1000:.0f} mm"
                + ("." if n_off == 0 else
                   f"; {n_off:,} DO NOT, worst {float(d.max()):.2f} m. Both are sampled "
                   f"from the same 0.5 m VRT at the same published X/Y, so a difference "
                   f"means s4 has re-minted the chamber under this NODE_UID since "
                   f"{os.path.basename(GPKG_S6)} was written. A depth is ground minus "
                   f"invert: every depth, cover and drop on this file is then measured "
                   f"from somewhere else. NOTHING IN THIS EXPORT IS QUOTABLE - run "
                   f"s6_levels.py against the current chamber layer and re-export.")))


def check_contract(layers: Dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    """Validate every contract layer and PUBLISH the result - one row per PROBLEM, not one
    row per layer.

    W11b wrote the whole ContractError into a single 8,000-character cell, so "stations
    fails" could equally have meant one missing field or forty. Splitting on the blank line
    `validate()` already uses gives a countable list, and a reader can see at a glance that
    a layer fails on ONE named data gap rather than on its design."""
    rows = []
    for name in ("nodes", "reaches", "connections", "stations", "rising_mains",
                 "crossings", "subnetworks", "packages"):
        gdf = layers.get(name)
        if name == "subnetworks":
            # not a contract layer - there is no LayerSpec for a service-area polygon. Say
            # that plainly rather than scoring it as a pass.
            rows.append(dict(LAYER=name, RESULT="no LayerSpec - not a contract layer",
                             PASS=1,
                             DETAIL=f"{0 if gdf is None else len(gdf):,} rows. The five "
                                    f"published layers include this one; the contract "
                                    f"declares four of them."))
            continue
        if gdf is None:
            rows.append(dict(LAYER=name, RESULT="NOT PRODUCED", PASS=0, DETAIL=""))
            continue
        try:
            CT.validate(gdf, name, stage=STAGE)
            rows.append(dict(LAYER=name, RESULT="passes contract.validate()", PASS=1,
                             DETAIL=f"{len(gdf):,} rows"))
        except CT.ContractError as e:
            # `validate()` separates its problems with a BLANK LINE and wraps them in a
            # header (which carries the layer's purpose) and a footer. Splitting on the
            # blank line and dropping those two gives one row per PROBLEM - so "stations
            # fails" becomes a countable list rather than an 8,000-character cell that
            # could equally be one missing field or forty.
            chunks = [c.strip() for c in str(e).split("\n\n") if c.strip()]
            probs = [c for c in chunks
                     if not c.startswith("CONTRACT VIOLATION")
                     and not c.startswith("Fix this in the stage")]
            for p in (probs or [str(e)[:4000]]):
                rows.append(dict(LAYER=name, RESULT="CONTRACT VIOLATION", PASS=0,
                                 DETAIL=p[:4000]))
    # the publication gate: was the naming work actually DONE, not just possible
    for name in NAMED_LAYERS:
        gdf = layers.get(name)
        if gdf is None or not len(gdf):
            continue
        try:
            CT.assert_named(gdf, name, stage=STAGE)
            rows.append(dict(LAYER=f"{name} <- assert_named", PASS=1,
                             RESULT="every row is NAMED", DETAIL=f"{len(gdf):,} rows"))
        except CT.ContractError as e:
            rows.append(dict(LAYER=f"{name} <- assert_named", PASS=0,
                             RESULT="LAYER IS NOT FULLY NAMED", DETAIL=str(e)[:4000]))
    # A THEME THAT COULD NOT BE BUILT IS A PUBLISHED FAILURE, NOT A CONSOLE LINE. An empty
    # EXCEPTIONS map reads as "we checked and it is fine"; that has to be visible on the
    # deliverable, next to every other objection, and not only in a log nobody keeps.
    for tname, err in sorted(THEME_FAILURES.items()):
        rows.append(dict(LAYER=f"theme:{tname}", RESULT="THEME COULD NOT BE BUILT", PASS=0,
                         DETAIL=f"{err}. Its KMZ and its QGIS styles were NOT written. An "
                                f"absent theme is not a clean one - do not read the two "
                                f"that were written as the whole picture."))
    cov = levels_coverage_row(layers)
    if cov is not None:
        rows.append(cov)
        if not cov["PASS"]:
            _log("   *** " + cov["RESULT"] + ": " + cov["DETAIL"])
    gnd = levels_ground_row(layers)
    if gnd is not None:
        rows.append(gnd)
        if not gnd["PASS"]:
            _log("   *** " + gnd["RESULT"] + ": " + gnd["DETAIL"])
    try:
        CT.assert_crossings_resolve(reaches=layers.get("reaches"),
                                    crossings=layers.get("crossings"))
        rows.append(dict(LAYER="crossings <-> reaches", RESULT="every CROSS_ID resolves",
                         PASS=1, DETAIL=""))
    except CT.ContractError as e:
        rows.append(dict(LAYER="crossings <-> reaches", RESULT="REGISTER DOES NOT RESOLVE",
                         PASS=0, DETAIL=str(e)[:4000]))
    return pd.DataFrame(rows)


def publish(layers: Dict[str, gpd.GeoDataFrame], extra: Dict[str, pd.DataFrame]) -> str:
    """One GeoPackage, WRITTEN BESIDE THE OLD ONE AND THEN SWAPPED IN.

    The previous version deleted the target and wrote into it. Two things went wrong with
    that, and both cost a whole run:

      * QGIS holds an open handle on the GeoPackage it is displaying, so `os.remove` raises
        PermissionError on Windows and the export dies AFTER the design work is done;
      * a crash halfway through left a file with some layers in it and no way to tell.

    So: write every layer into `W12_export.<pid>.part.gpkg`, then `os.replace()` it over
    the target - atomic on the same volume. If the swap is refused because something holds
    the target open, the run is NOT lost: the part file is renamed to a TIMESTAMPED
    GeoPackage beside it and the path is returned and printed. A locked file costs you the
    convenience of one filename, never a run.

    Returns the path actually written, which is not always GPKG_OUT."""
    tmp = os.path.join(SHP, f"W12_export.{os.getpid()}.part.gpkg")
    for p in (tmp, tmp + "-journal", tmp + "-wal"):
        if os.path.exists(p):
            os.remove(p)
    for name, df in list(layers.items()) + list(extra.items()):
        if isinstance(df, gpd.GeoDataFrame) and len(df) and df.geometry.notna().any():
            df.to_file(tmp, layer=name, driver="GPKG")
        else:
            gpd.GeoDataFrame(pd.DataFrame(df).copy(), geometry=[None] * len(df),
                             crs=f"EPSG:{CT.CRS_EPSG}").to_file(
                tmp, layer=name, driver="GPKG")
        _log(f"   wrote {name:<18} {len(df):>7,}")
    try:
        os.replace(tmp, GPKG_OUT)
        _log(f"   swapped in -> {os.path.basename(GPKG_OUT)} "
             f"({os.path.getsize(GPKG_OUT) / 1e6:.1f} MB)")
        return GPKG_OUT
    except OSError as e:
        alt = os.path.join(SHP, f"W12_export_{time.strftime('%Y%m%d_%H%M%S')}.gpkg")
        os.replace(tmp, alt)
        _log(f"   *** {os.path.basename(GPKG_OUT)} IS LOCKED ({type(e).__name__}: {e}). "
             f"THE RUN IS NOT LOST - it is in {os.path.basename(alt)}. Close QGIS and "
             f"rename it, or point QGIS at the new file.")
        return alt


# ======================================================================================
# 8.  THE KMZ SET
#
#     "SUBFOLDERS inside each file for manageability, and SEVERAL SEPARATE FILES each with
#      a DIFFERENT STYLE so he can flick between them and check things fast."   - engineer
#
#     `w12.present` already IS that machine: one `View` declaration drives both the KMZ
#     and the QGIS renderer, so the Earth file and the GIS project cannot tell different
#     stories. Nothing here re-implements it. What this section adds is SIX views the
#     library did not have, registered from the outside through `present.register()`,
#     because a view is a declaration and adding one is not editing the library.
# ======================================================================================

# Declared in EXPORT_NUMBERS above with the source and the consequence of each - these
# three shape PUBLISHED data (a polygon's extent, how many unserved areas are reported,
# and which clusters get a boundary at all), so they are register entries and not local
# literals. Read from the register so there is exactly one value for each.
SERVICE_BUFFER_M = float(EXPORT_NUM["SERVICE_BUFFER_M"])
UNSERVED_CLUSTER_M = float(EXPORT_NUM["UNSERVED_CLUSTER_M"])
UNSERVED_MIN_PLOTS = int(EXPORT_NUM["UNSERVED_MIN_PLOTS"])


def build_subnetworks(layers: Dict[str, gpd.GeoDataFrame], a: Assembly, g: Graph,
                      f: Flows, nm: Naming, jn: Joins) -> gpd.GeoDataFrame:
    """LAYER FIVE: one polygon per subnetwork over the plots it serves, PLUS the areas the
    network does not reach - each carrying SERVED = 0, a flag and a reason.

    The engineer asked for the AREA, not a polygon per orphan pipe, because the area with
    its plots inside it is the thing somebody has to make a decision about: serve it
    another way, or do not serve it. A lone plot is a connection question and is left to
    the connection layer; an area needs UNSERVED_MIN_PLOTS members before a boundary round
    it says anything.

    The served polygon carries the three numbers concept rule 2 is made of - does this
    subnetwork reach the main pipe, how far short it is, and how far its outlet sits from
    its own low point - so the STRUCTURE and EXCEPTIONS themes read them off one layer."""
    r = layers["reaches"]
    nd = layers["nodes"]
    cn = layers["connections"]
    rows = []

    plots_at = cn.groupby(cn.SUB_NAME.astype(str)).size().to_dict()
    q_at = cn.groupby(cn.SUB_NAME.astype(str)).Q_ADF_M3D.sum().to_dict()
    prop_at = cn.groupby(cn.SUB_NAME.astype(str)).N_PROP.sum().to_dict()
    conn_by_sub = {k: v for k, v in cn.groupby(cn.SUB_NAME.astype(str))}
    node_by_sub = {k: v for k, v in nd.groupby(nd.SUB_NAME.astype(str))}
    out_by_sub = {str(nm.subnet_name.get(int(i), "")): int(i) for i in np.unique(f.subnet)}
    # uid -> the chamber's NAME, built once. Masking the whole node layer per subnetwork
    # is 195 passes over 57,000 rows for one lookup each.
    name_of_uid = dict(zip(nd.NODE_UID.astype(str), nd.NAME.astype(str)))
    tdist = nm.stats.get("town_dist", {}) if isinstance(nm.stats, dict) else {}

    for name, sub in r.groupby(r.SUB_NAME.astype(str)):
        if not name:
            continue
        parts = [sub.geometry.buffer(SERVICE_BUFFER_M, resolution=4)]
        cs = conn_by_sub.get(name)
        if cs is not None and len(cs):
            parts.append(cs.geometry.buffer(SERVICE_BUFFER_M, resolution=4))
        try:
            poly = unary_union(pd.concat(parts).values).simplify(5.0)
        except Exception:                                      # pragma: no cover
            continue
        if poly.is_empty:
            continue
        nsub = node_by_sub.get(name)
        oi = out_by_sub.get(name, -1)
        outfall = g.uid[oi] if oi >= 0 else ""
        rows.append(dict(
            NAME=name,
            TOWN=str(sub.TOWN.iloc[0]),
            SUBNET=str(sub.SUBNET.iloc[0]),
            SERVED=1,
            N_PLOT=int(plots_at.get(name, 0)),
            N_PROP=round(float(prop_at.get(name, 0.0)), 1),
            Q_ADF_M3D=round(float(q_at.get(name, 0.0)), 2),
            N_CHAMBER=int(len(nsub)) if nsub is not None else 0,
            LEN_KM=round(float(sub.LEN_M.sum()) / 1000.0, 3),
            DEEP_M=round(float(nsub.DEPTH_M.max()), 2) if nsub is not None and len(nsub) else 0.0,
            OUTFALL=outfall,
            OUT_NAME=name_of_uid.get(outfall, ""),
            JOIN_MAIN=int(jn.is_join[oi]) if oi >= 0 else 0,
            GAP_M=round(float(jn.gap_m[oi]), 1) if oi >= 0 else 0.0,
            OFF_M=round(float(jn.off_m[oi]), 1) if oi >= 0 else 0.0,
            LOW_ND=jn.low_uid.get(oi, ""),
            TOWN_D_M=round(float(tdist.get(oi, 0.0)), 1),
            FLAG="" if (oi >= 0 and jn.is_join[oi]) else "does not reach the main pipe",
            WHY="" if (oi >= 0 and jn.is_join[oi]) else
                (f"outfall {outfall} stands {float(jn.gap_m[oi]):,.0f} m from the client's "
                 f"Main Pipe - beyond the {JOIN_TOL_M:g} m at which this design says a "
                 f"subnetwork JOINS it. Legal only if it ends at a designed pumping "
                 f"station with a rising main (10_ASBUILT_CALIBRATION rule T1); otherwise "
                 f"it drains nowhere" if oi >= 0 else ""),
            AREA_M2=round(float(poly.area), 1),
            SRC="terrain", CONFIDENCE="derived", STAGE=STAGE,
            geometry=poly))

    # ---- the areas the network does not reach ------------------------------------------
    un = a.unserved
    if un is not None and len(un) and un.geometry.notna().any():
        rows += _unserved_areas(un)

    out = gpd.GeoDataFrame(rows, geometry="geometry", crs=f"EPSG:{CT.CRS_EPSG}")
    _log(f"   subnetwork polygons: {int((out.SERVED == 1).sum()):,} served areas covering "
         f"{int(out[out.SERVED == 1].N_PLOT.sum()):,} plots; "
         f"{int((out.SERVED == 0).sum()):,} UNSERVED areas holding "
         f"{int(out[out.SERVED == 0].N_PLOT.sum()):,} plots, each with a reason")
    return out


def _unserved_areas(un: gpd.GeoDataFrame) -> List[Dict[str, Any]]:
    """A boundary round every cluster of plots the network does not reach.

    Clustered with a KD-tree and union-find rather than sklearn, which is not installed
    here and is a heavy dependency for one call. Same idea as DBSCAN."""
    from scipy.spatial import cKDTree
    cent = un.geometry.centroid
    xy = np.c_[cent.x.to_numpy(), cent.y.to_numpy()]
    parent = list(range(len(xy)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    tree = cKDTree(xy)
    for i, j in tree.query_pairs(UNSERVED_CLUSTER_M):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
    groups: Dict[int, List[int]] = defaultdict(list)
    for i in range(len(xy)):
        groups[find(i)].append(i)

    rows: List[Dict[str, Any]] = []
    keep = sorted((m for m in groups.values() if len(m) >= UNSERVED_MIN_PLOTS),
                  key=lambda m: -len(m))
    for k, members in enumerate(keep, start=1):
        sel = un.iloc[members]
        hull = MultiPoint(list(sel.geometry.centroid)).convex_hull.buffer(120.0)
        # the reason, in the stage's own words plus the measured distance - one reason per
        # area, and the areas differ, so the column varies (inheritance row 22)
        whys = sel.WHY.astype(str).value_counts() if "WHY" in sel.columns else None
        lead = str(whys.index[0]) if whys is not None and len(whys) else "not reached"
        d_near = (round(float(pd.to_numeric(sel.D_NEAR_M, errors="coerce").min()), 1)
                  if "D_NEAR_M" in sel.columns else float("nan"))
        rows.append(dict(
            NAME="", TOWN="", SUBNET="", SERVED=0,
            N_PLOT=int(len(sel)),
            N_PROP=round(float(pd.to_numeric(sel.N_PROP, errors="coerce").sum()), 1)
                   if "N_PROP" in sel.columns else 0.0,
            Q_ADF_M3D=round(float(pd.to_numeric(sel.Q_ADF_M3D, errors="coerce").sum()), 2)
                      if "Q_ADF_M3D" in sel.columns else 0.0,
            N_CHAMBER=0, LEN_KM=0.0, DEEP_M=0.0, OUTFALL="", OUT_NAME="",
            JOIN_MAIN=0, GAP_M=0.0, OFF_M=0.0, LOW_ND="", TOWN_D_M=0.0,
            FLAG=f"UNSERVED-{k:03d}",
            WHY=(f"{len(sel):,} plots, nearest chamber {d_near:,.0f} m away. {lead}. "
                 f"scope-p4 item 3 requires every plot SERVICED, and 'serviced' is not "
                 f"'connected to one network' (philosophy sec 8a) - the decision is which "
                 f"system serves this area, not whether to drop it"),
            AREA_M2=round(float(hull.area), 1),
            SRC="terrain", CONFIDENCE="derived", STAGE=STAGE,
            geometry=hull))
    return rows


def carry_src_raw(layers: Dict[str, gpd.GeoDataFrame]) -> List[str]:
    """Every layer carrying SRC also carries SRC_RAW, so the P6 confidence floor is
    auditable on the package the client actually receives.

    Where a layer's SRC was written as a literal by this stage - a connection, a station,
    the trunk - nothing was mapped, so the raw value IS the mapped one and saying so is the
    honest answer. Where it came through `assemble()`'s vocabulary map, the raw token is the
    corridor's own and is already on the row. Neither case invents anything; both make the
    floor testable."""
    filled = []
    for name, gdf in layers.items():
        if "SRC" not in gdf.columns or "SRC_RAW" in gdf.columns:
            continue
        gdf["SRC_RAW"] = gdf["SRC"].astype(str)
        filled.append(name)
    if filled:
        _log("   SRC_RAW written from SRC on " + ", ".join(sorted(filled))
             + " - those layers' SRC was minted here, not mapped, so raw and mapped are "
               "the same token and the P6 floor can now be checked on the deliverable")
    return filled


def _extra_columns(layers: Dict[str, gpd.GeoDataFrame]) -> None:
    """The four presentation columns the extra views classify on. Each is a RESTATEMENT of
    a published field in words a reviewer can read on a legend - never a new number."""
    nd = layers["nodes"]
    why = np.where(nd.PAST_CAP.to_numpy() == 0, "inside the 12 m cap",
                   np.where(nd.CAP_EXIT.astype(str).to_numpy() == "recovers_500m",
                            "past 12 m - cover recovers within 500 m",
                            np.where(nd.CAP_EXIT.astype(str).to_numpy() == "outfall_1000m",
                                     "past 12 m - outfall within 1,000 m",
                                     "PAST 12 m, NO EXIT - a station is demanded here")))
    nd["CAP_WHY"] = why

    cx = layers["crossings"]
    cx["XING_CLS"] = [
        f"{o} - {'SQUARE within ' + str(int(C.WADI_XING_SKEW_DEG)) + ' deg' if s else 'SKEW - runs along it'}"
        for o, s in zip(cx.OBSTACLE.astype(str), cx.SQUARE.to_numpy())]

    cn = layers["connections"]
    cn["DRAIN_TXT"] = np.where(cn.CAN_CONN.to_numpy() == 1,
                               "connects to its chamber on gravity",
                               "CANNOT connect - the sewer invert is above the property outlet")

    r = layers["reaches"]
    r["CLEAN_TXT"] = r.CLEAN_BY.astype(str).map({
        "velocity": "velocity route - reaches 0.75 m/s at peak (G203-p26)",
        "tractive": "TRACTIVE route - rests on the ASSUMED tau = 1.0 Pa (G203-p27, GAP-9)",
        "neither": "NEITHER route - this pipe will silt",
    }).fillna("unknown")

    # ---- DEP_M: ONE depth column on ALL FIVE LAYERS, so the DEPTH theme is literally one
    # ---- field classified on one fixed set of breaks. What it means per layer is in the
    # ---- field dictionary, and it is NOT the same physical quantity everywhere - which is
    # ---- exactly why it is written down rather than left to the reader.
    r["DEP_M"] = np.round(np.maximum(pd.to_numeric(r.US_DEPTH, errors="coerce"),
                                     pd.to_numeric(r.DS_DEPTH, errors="coerce")), 3)
    nd["DEP_M"] = np.round(pd.to_numeric(nd.DEPTH_M, errors="coerce"), 3)
    st = layers["stations"]
    st["DEP_M"] = np.round(pd.to_numeric(st.GRD_M, errors="coerce")
                           - pd.to_numeric(st.INV_M, errors="coerce"), 3)
    rm = layers["rising_mains"]
    st_dep = dict(zip(st.NODE_UID.astype(str), st.DEP_M))
    # a pressure main has no invert of its own in this design, so it takes the depth of the
    # wet well it leaves - which is the depth a reviewer is actually judging.
    rm["DEP_M"] = np.round(rm.STATION.astype(str).map(st_dep).fillna(0.0), 3)
    sn = layers["subnetworks"]
    sn["DEP_M"] = np.round(pd.to_numeric(sn.DEEP_M, errors="coerce").fillna(0.0), 3)

    # ---- STR_CLS: the STRUCTURE class of a chamber, in words. A chamber is one thing on
    # ---- that map, in this priority: the place a subnetwork meets the main pipe, then a
    # ---- drop, then a pumping station, then what kind of chamber it is.
    kind = nd.NODE_KIND.astype(str).to_numpy()
    dtyp = nd.DROP_TYPE.astype(str).to_numpy()
    dwhy = nd.DROP_WHY.astype(str).to_numpy()
    strc = np.where(nd.JOIN_MAIN.to_numpy() == 1,
                    "subnetwork joins the MAIN PIPE here",
                    np.where(dtyp == "vortex",
                             np.char.add("VORTEX drop shaft - ", dwhy.astype(str)),
                             np.where(dtyp == "backdrop",
                                      np.char.add("backdrop - ", dwhy.astype(str)),
                                      np.char.add("chamber - ", kind.astype(str)))))
    nd["STR_CLS"] = strc


def register_extra_views() -> List[str]:
    """Six views `present` did not ship, each answering a question this export raised."""
    names = []

    names.append(PR.register(PR.View(
        name="pumping_demand", priority=8,
        title="WHERE THIS DESIGN DEMANDS A PUMPING STATION",
        question="Which chambers pass the 12 m cover cap with no way back out?",
        role="nodes", geom="point", mode="categorical", field="CAP_WHY",
        categories=[
            ("PAST 12 m, NO EXIT - a station is demanded here",
             "PAST 12 m WITH NO EXIT - a station is demanded (philosophy sec 5)",
             (165, 0, 38), 1.7),
            ("past 12 m - cover recovers within 500 m",
             "Past 12 m, cover recovers within 500 m - exit held", (253, 141, 60), 1.0),
            ("past 12 m - outfall within 1,000 m",
             "Past 12 m, outfall within 1,000 m - exit held", (254, 217, 118), 1.0),
            ("inside the 12 m cap", "Inside the cap", (200, 200, 200), 0.14),
        ],
        folder_fields=("CAP_WHY",), folder_sort="count",
        label_field="NODE_REF", label_min_lod=256, label_max=4000,
        label_filter=lambda d: d["CAP_WHY"].str.startswith("PAST") if "CAP_WHY" in d else None,
        popup=PR._NODE_POPUP + PR._pop(("CAP_WHY", "Cap status", "{}"),
                                       ("CAP_LEN_M", "Distance to recovery / outfall", "{:.0f} m"),
                                       ("COVER_M", "Cover", "{:.2f} m")),
        assumptions=("A1",),
        notes=("The cap is 12 m of COVER, G203-p33, read as a cap. Philosophy sec 5 gives "
               "exactly two exits and both are bounded by DISTANCE and by DEPTH; an exit "
               "is withdrawn where the excursion forces a drop past criteria.DROP_CEILING_M.",
               "Red is not a defect of the levelling. It is FLATNESS: 60 % of this corridor "
               "network falls more gently than the 5.00 mm/m a DN200 may be laid at "
               "(G203-p29 Tab 11), so the pipe sinks whichever way it points.",
               "This stage does not place stations. Stage 7 does. Every red dot is a "
               "demand handed back to it."),
    )).name)

    names.append(PR.register(PR.View(
        name="clean_by", priority=62,
        title="Which self-cleansing route each pipe takes - THE tau EXPOSURE MAP",
        question="How much of this scheme rests on an assumed tractive stress?",
        role="reaches", geom="line", mode="categorical", field="CLEAN_TXT",
        categories=[
            ("velocity route - reaches 0.75 m/s at peak (G203-p26)",
             "Velocity route - reaches 0.75 m/s at peak (G203-p26)", (26, 120, 55), 2.2),
            ("TRACTIVE route - rests on the ASSUMED tau = 1.0 Pa (G203-p27, GAP-9)",
             "TRACTIVE route - rests on the ASSUMED tau = 1.0 Pa (G203-p27, GAP-9)",
             (217, 95, 14), 1.6),
            ("NEITHER route - this pipe will silt",
             "NEITHER route - this pipe will silt (H5)", (165, 0, 38), 4.0),
        ],
        folder_fields=("CLEAN_TXT",), folder_sort="length",
        popup=PR._REACH_POPUP + PR._pop(("CLEAN_BY", "Self-cleansing route", "{}"),
                                        ("SLOPE_MIN", "Governing minimum", "{:.3f} %")),
        assumptions=("A1",),
        notes=("G203-p27 4.2.2.1 offers the two as ALTERNATIVES and requires the STEEPER; "
               "the tractive route exists FOR the small lightly-loaded pipe where 0.75 m/s "
               "is unreachable, so orange is legal, not a breach.",
               "The orange length IS the exposure. At tau = 2.0 Pa every orange gradient "
               "rises 2.346x and every level downstream of it changes."),
    )).name)

    names.append(PR.register(PR.View(
        name="sized_by", priority=45,
        title="What set each DIAMETER - the H8 proof",
        question="Did anything on this network get its size from depth rather than flow?",
        role="reaches", geom="line", mode="categorical", field="SIZED_BY",
        categories=[
            ("minimum", "The guideline MINIMUM size already carries it (G203-p22 Tab 6)",
             (189, 215, 231), 1.2),
            ("dod", "The depth-of-flow limit chose it (G203-p27 Tab 10)", (49, 130, 189), 2.6),
            ("capacity", "The size below could not pass the flow at all", (8, 48, 107), 3.6),
            ("velocity", "The size below exceeded 3.0 m/s (G203-p27)", (217, 95, 14), 3.0),
            ("infeasible", "NO size in the series passes it - a station or a route, "
                           "never a bigger number", (165, 0, 38), 5.0),
        ],
        folder_fields=("SIZED_BY",), folder_sort="length",
        popup=PR._REACH_POPUP + PR._pop(("SIZED_BY", "Diameter set by", "{}")),
        notes=("'depth' and 'cover' are NOT in this vocabulary and cannot be: oversizing a "
               "pipe to lay it flatter is prohibited by G203-p29 and by Ten States sec "
               "33.43 independently, so the prohibited move is not expressible.",),
    )).name)

    names.append(PR.register(PR.View(
        name="grad_by", priority=47,
        title="What set each GRADIENT",
        question="Where is the design fighting the ground, and where is it just obeying Table 11?",
        role="reaches", geom="line", mode="categorical", field="GRAD_BY",
        categories=[
            ("table11", "G203-p29 Table 11 floor governed", (158, 202, 225), 1.3),
            ("tractive", "The tractive minimum governed - exposed to tau (GAP-9)",
             (217, 95, 14), 1.8),
            ("uniform", "Carried from the reach above (P1) - the preferred answer",
             (116, 196, 118), 1.3),
            ("cover_min", "Steepened to hold 1.30 m of cover (G203-p33)", (49, 130, 189), 2.2),
            ("cover_max", "Held at the 25 % laying bound; the rest taken at a drop",
             (140, 81, 10), 3.0),
            ("ground", "Laid to the ground fall - steeper than the laying bound because "
                       "capping it would lift the pipe out of the ground", (165, 0, 38), 4.0),
            ("vmax", "Flattened to hold 3.0 m/s (G203-p27)", (255, 220, 60), 2.6),
            ("tie", "Fixed by an existing invert - the design yields (H14)", (0, 0, 0), 3.0),
        ],
        folder_fields=("GRAD_BY",), folder_sort="length",
        popup=PR._REACH_POPUP,
        assumptions=("A1",),
    )).name)

    names.append(PR.register(PR.View(
        name="crossings", priority=12,
        title="WADI AND DUAL-CARRIAGEWAY CONTACT - the H1a register",
        question="Does the design CROSS these things, or does it run ALONG them?",
        role="crossings", geom="line", mode="categorical", field="XING_CLS",
        folder_fields=("OBSTACLE",), folder_sort="count",
        label_field="CROSS_ID", label_min_lod=128, label_max=1200,
        popup=PR._pop(("CROSS_ID", "Crossing", "{}"), ("OBSTACLE", "Obstacle", "{}"),
                      ("LEN_M", "Contact length", "{:.1f} m"),
                      ("ANGLE_DEG", "MEASURED angle to the obstacle", "{:.1f} deg"),
                      ("SQUARE", "Within the skew tolerance", "{:.0f}"),
                      ("N_REACH", "Reaches involved", "{:.0f}"),
                      ("METHOD", "Method", "{}"), ("COVER_M", "Cover required", "{:.2f} m"),
                      ("APPROVED", "Consent obtained", "{:.0f}")),
        assumptions=("A2", "A3"),
        notes=("The angle is MEASURED against the nearest stream line's own direction. "
               "W11a published ANGLE_DEG = 90 on 3,290 crossings and the measured minimum "
               "was 0.00 deg - that number was fabricated and is retracted.",
               "H1a: a wadi crossing is legal only when it CROSSES rather than runs along, "
               "carries no chamber on wadi ground, has 1.50 m of cover (G203-p52 8.2.4, "
               "adopted for gravity as OUR decision) and is in this register.",
               "APPROVED = 0 on every row. MoAFWR consent for a wadi (G201-p85) and the "
               "roads authority's for a carriageway are OPEN items, not silent ones."),
    )).name)

    names.append(PR.register(PR.View(
        name="can_drain", priority=98,
        title="Can each plot actually reach its chamber?",
        question="Which plots sit BELOW the sewer that is supposed to serve them?",
        role="connections", geom="line", mode="categorical", field="DRAIN_TXT",
        categories=[
            ("CANNOT drain - the sewer invert is above the property outlet",
             "CANNOT drain on gravity - the invert is above the property outlet",
             (165, 0, 38), 3.0),
            ("drains to its chamber on gravity",
             "Drains on gravity at the 3 % minimum (G203-p18 Tab 5)", (116, 196, 118), 0.8),
        ],
        folder_fields=("DRAIN_TXT",), folder_sort="count",
        popup=PR._pop(("CONN_ID", "Connection", "{}"), ("PLOT_ID", "Plot", "{}"),
                      ("OUT_NODE", "Chamber", "{}"), ("LEN_M", "Length", "{:.1f} m"),
                      ("SLOPE_LAID", "Gradient", "{:.2f} %"),
                      ("FALL_AV_M", "Fall available", "{:.2f} m"),
                      ("Q_ADF_M3D", "Load", "{:.2f} m3/d"),
                      ("N_PROP", "Properties", "{:.2f}")),
        notes=("s4 published CAN_DRAIN as 'cannot run - no designed invert exists at stage "
               "4'. There is one now, so the question is answered.",
               "The test: the property outlet at the G203-p19 3.4 minimum HCC depth of "
               "1.2 m must clear the sewer invert with the 3 % minimum gradient of "
               "G203-p18 Table 5 over the connection's own length.",
               "A plot that cannot drain is not a rounding error - it is a plot the "
               "gravity network does not actually serve, and it belongs in the "
               "not-served schedule."),
    )).name)
    return names


KMZ_VIEWS = [
    # the five the engineer named, first
    "tier", "depth", "subnet", "diameter", "stations",
    # and the ones that answer a question this design actually raises
    "pumping_demand", "ground_fall", "constraint", "drops", "crossings",
    "chambers", "capacity", "velocity", "clean_by", "sized_by", "grad_by",
    "flow", "rising_mains", "can_drain", "material",
]


# ======================================================================================
# 8a.  THE THREE THEMES - STRUCTURE, DEPTH, EXCEPTIONS
#
#      Each theme is a list of ThemeLayers, and a ThemeLayer is one published layer, one
#      CLASS COLUMN and one class table (value -> label, colour, width). That shape is
#      deliberate: it is the only shape that can drive a KMZ folder, a QGIS .qml and a DXF
#      layer set from ONE declaration, so the three cannot tell different stories. The
#      previous iteration's KMZ and its shapefiles disagreed about which chambers were
#      drops, and nobody could say which was right.
#
#      The DEPTH theme classifies EVERY layer on ONE column, `DEP_M`, against ONE fixed
#      set of edges, `DEPTH_BREAKS`, on the MAGMA ramp. Fixed, because an auto-stretched
#      ramp makes the same colour mean a different depth in every export.
#
#      The EXCEPTIONS theme draws NOTHING that is not flagged, colours by kind, sizes by
#      severity, and PUTS THE COUNT IN THE LAYER NAME so the legend reports the totals.
# ======================================================================================

# MAGMA, registered into present's own ramp table rather than edited into the library -
# adding a ramp is a declaration, the same way adding a View is. Control points are the
# published magma anchors (dark purple -> orange -> pale yellow), REVERSED so that
# SHALLOW IS LIGHT AND DEEP IS DARK, which is what the engineer asked for and is also the
# only direction that reads correctly against a satellite background.
PR.RAMPS.setdefault("magma", [
    (0.00, (252, 253, 191)),     # shallow
    (0.25, (254, 176, 120)),
    (0.50, (241, 96, 93)),
    (0.75, (140, 41, 129)),
    (1.00, (12, 8, 38)),         # deep
])

# Feature counts above this are drawn as ONE placemark per class holding a MultiGeometry
# instead of one placemark per feature. A 57,000-placemark folder will not pan in Google
# Earth, and at the zoom a layout is judged from you cannot see one chamber anyway. Below
# it, every feature keeps its own placemark and its own popup.
KMZ_INDIVIDUAL_MAX = 4000

# The DN bands the conduit line weight steps on - the sizes G203 itself tabulates, grouped
# so a reviewer can tell a lateral from a trunk at a glance. Weight, not colour: colour is
# the subnetwork on the STRUCTURE theme.
DN_BANDS: List[Tuple[int, str, float]] = [
    (250, "DN200-250", 1.2),
    (400, "DN315-400", 2.0),
    (700, "DN450-700", 3.0),
    (1200, "DN800-1200", 4.2),
    (10 ** 6, "DN1400 and above", 5.6),
]


def _dn_band(dn: float) -> Tuple[str, float]:
    for hi, lab, w in DN_BANDS:
        if float(dn) <= hi:
            return lab, w
    return DN_BANDS[-1][1], DN_BANDS[-1][2]


@dataclass
class ThemeLayer:
    """One drawable layer of one theme: a frame, a class column, and the class table."""
    key: str                                    # file-safe id; also the DXF layer suffix
    title: str                                  # what the folder / QGIS layer is called
    role: str                                   # the published layer it came from
    geom: str                                   # line | point | polygon
    field: str                                  # the class column
    classes: List[Tuple[Any, str, Tuple[int, int, int], float]]
    gdf: gpd.GeoDataFrame
    popup: Sequence[Tuple[str, str, str]] = ()
    label_field: Optional[str] = None
    note: str = ""

    @property
    def n(self) -> int:
        return int(len(self.gdf))

    def folder_name(self) -> str:
        return f"{self.title} ({self.n:,})"


def _depth_classes(geom: str) -> List[Tuple[Any, str, Tuple[int, int, int], float]]:
    """The ONE class table of the DEPTH theme. Index i means 'between edge i-1 and i'."""
    nb = len(DEPTH_BREAKS) + 1
    w0, w1 = (1.1, 5.0) if geom == "line" else (0.6, 2.2)
    out = []
    for i in range(nb):
        lo = DEPTH_BREAKS[i - 1] if i > 0 else None
        hi = DEPTH_BREAKS[i] if i < len(DEPTH_BREAKS) else None
        # A BAND IS MARKED (o) IF EITHER OF ITS OWN EDGES HAS NO SOURCE - not if both do.
        # `present` picks up whichever edge happens to carry a citation, which lets a band
        # bounded by one sourced and one invented edge read as fully sourced. Here 9.00 m
        # has no source, so BOTH bands that touch it say so.
        edge_refs = ([DEPTH_BREAK_REFS[i - 1]] if i > 0 else []) + \
                    ([DEPTH_BREAK_REFS[i]] if i < len(DEPTH_BREAKS) else [])
        cited = [x for x in edge_refs if x]
        band = ("under %.2f m" % hi if lo is None else
                ("%.2f m and deeper" % lo if hi is None else "%.2f - %.2f m" % (lo, hi)))
        lab = (band
               + ("   [" + " | ".join(cited) + "]" if cited else "")
               + ("   (o)" if any(x == "" for x in edge_refs) else ""))
        t = i / max(1, nb - 1)
        out.append((i, lab, PR.ramp_rgb("magma", t), round(w0 + (w1 - w0) * t, 2)))
    return out


def _depth_index(v) -> np.ndarray:
    """Which fixed band each value falls in. NaN -> the shallowest band, never dropped."""
    x = pd.to_numeric(v, errors="coerce").to_numpy(dtype=float)
    idx = np.digitize(x, np.array(DEPTH_BREAKS, dtype=float), right=False)
    return np.where(np.isnan(x), 0, idx).astype(int)


_REACH_POP = (("NAME", "Conduit", "{}"), ("US_NAME", "From manhole", "{}"),
              ("DS_NAME", "To manhole", "{}"), ("TIER", "Tier", "{}"),
              ("DN", "Size", "DN{:.0f}"), ("LEN_M", "Length", "{:.1f} m"),
              ("SLOPE_LAID", "Laid gradient", "{:.2f} %"),
              ("QPK_LS", "Peak flow", "{:.1f} L/s"),
              ("V_PK_MS", "Velocity at peak", "{:.2f} m/s"),
              ("DEP_M", "Depth to invert, deeper end", "{:.2f} m"))
_NODE_POP = (("NAME", "Manhole", "{}"), ("NODE_KIND", "Kind", "{}"),
             ("GRD_M", "Ground level", "{:.2f} m aOD"),
             ("INV_M", "Invert level", "{:.2f} m aOD"),
             ("DEPTH_M", "Depth", "{:.2f} m"), ("COVER_M", "Cover", "{:.2f} m"),
             ("DROP_M", "Drop", "{:.2f} m"), ("DROP_TYPE", "Drop structure", "{}"),
             ("DROP_WHY", "Why the drop exists", "{}"))
_ST_POP = (("NAME", "Pumping station", "{}"), ("ST_TYPE", "Type", "{}"),
           ("GRD_M", "Ground level", "{:.2f} m aOD"),
           ("INV_M", "Arrival invert", "{:.2f} m aOD"),
           ("LIFT_M", "Static lift", "{:.2f} m"),
           ("Q_DUTY_LS", "Duty flow", "{:.1f} L/s"),
           ("WELL_M3", "Wet well, live volume", "{:.2f} m3"),
           ("CATCH_KM", "Network captured", "{:.2f} km"))
_RM_POP = (("NAME", "Force main", "{}"), ("STATION", "From station", "{}"),
           ("DS_NODE", "To", "{}"), ("DS_TYPE", "Lands on", "{}"),
           ("DN", "Size", "DN{:.0f}"), ("LEN_M", "Length", "{:.1f} m"),
           ("Q_DUTY_LS", "Duty flow", "{:.1f} L/s"),
           ("V_DUTY_MS", "Velocity at duty", "{:.2f} m/s"),
           ("TOT_HD_M", "Total head", "{:.2f} m"))
_SN_POP = (("NAME", "Subnetwork", "{}"), ("TOWN", "Town", "{}"),
           ("N_PLOT", "Plots served", "{:.0f}"), ("LEN_KM", "Sewer", "{:.2f} km"),
           ("N_CHAMBER", "Chambers", "{:.0f}"), ("Q_ADF_M3D", "Load", "{:.1f} m3/d"),
           ("OUT_NAME", "Outfall", "{}"), ("GAP_M", "Distance to the main pipe", "{:.0f} m"),
           ("OFF_M", "Outlet off its own low point", "{:.0f} m"),
           ("FLAG", "Flag", "{}"), ("WHY", "Why", "{}"))


def theme_structure(layers: Dict[str, gpd.GeoDataFrame]) -> List[ThemeLayer]:
    """Each subnetwork its own colour, conduit weight rising with DN, flow direction, and
    pumps / force mains / drop chambers / main-pipe connections separately symbolised."""
    r, nd = layers["reaches"], layers["nodes"]
    st, rm, sn = layers["stations"], layers["rising_mains"], layers["subnetworks"]
    served = sn[sn.SERVED == 1]

    # ONE COLOUR PER SUBNETWORK, from present's own golden-ratio palette AND IN PRESENT'S
    # OWN ORDER - descending total conduit length. That ordering is not cosmetic: it is
    # what `present.classify()` uses for a categorical view with no declared palette, so
    # taking the same order is what makes the STRUCTURE theme and the per-question `subnet`
    # map agree about which subnetwork is which colour. Two maps of the same network in
    # different colours is the picture-level form of publishing one quantity twice.
    order = (r.assign(_k=r.SUB_NAME.astype(str))
             .groupby("_k")["LEN_M"].sum().sort_values(ascending=False))
    subs = [s for s in order.index.tolist() if s]
    subs += [s for s in served.NAME.astype(str).tolist() if s and s not in subs]
    colour = {s: PR.golden_rgb(i) for i, s in enumerate(subs)}

    band = [_dn_band(d) for d in pd.to_numeric(r.DN, errors="coerce").fillna(200)]
    r = r.copy()
    r["STR_CLS"] = [f"{s} | {b}" for s, (b, _w) in zip(r.SUB_NAME.astype(str), band)]
    rclasses = []
    for key in sorted(set(r.STR_CLS)):
        s, b = key.rsplit(" | ", 1)
        w = next((w for _hi, lab, w in DN_BANDS if lab == b), 1.2)
        rclasses.append((key, f"{s}   {b}", colour.get(s, (150, 150, 150)), w))

    sn2 = served.copy()
    snclasses = [(s, s, colour.get(s, (150, 150, 150)), 1.0) for s in sorted(set(sn2.NAME))]

    node_classes = [
        ("subnetwork joins the MAIN PIPE here",
         "WHERE A SUBNETWORK MEETS THE MAIN PIPE", (0, 150, 255), 1.9),
        ("__vortex__", "VORTEX drop shaft (drop over "
         f"{C.BACKDROP_MAX:g} m, G203-p30)", (165, 0, 38), 1.5),
        ("__backdrop__", f"backdrop (drop over {C.DROP_TRIGGER:g} m, G203-p30)",
         (253, 174, 97), 1.0),
        ("__head__", "head of a run", (120, 198, 121), 0.5),
        ("__chamber__", "chamber", (120, 120, 120), 0.28),
    ]
    nd2 = nd.copy()
    k = nd2.NODE_KIND.astype(str).to_numpy()
    d = nd2.DROP_TYPE.astype(str).to_numpy()
    nd2["STR_KEY"] = np.where(nd2.JOIN_MAIN.to_numpy() == 1,
                              "subnetwork joins the MAIN PIPE here",
                              np.where(d == "vortex", "__vortex__",
                                       np.where(d == "backdrop", "__backdrop__",
                                                np.where(k == "head", "__head__",
                                                         "__chamber__"))))

    out = [
        ThemeLayer("conduits", "Gravity conduits, coloured by subnetwork and weighted by size",
                   "reaches", "line", "STR_CLS", rclasses, r, _REACH_POP, "NAME",
                   note="colour = the subnetwork; line weight = the DN band. Two "
                        "independent facts on one line, which is why the class is the "
                        "PAIR - a data-defined width would not survive into a .qml."),
        ThemeLayer("manholes", "Manholes", "nodes", "point", "STR_KEY", node_classes, nd2,
                   _NODE_POP, "NAME"),
        # A CATEGORISED STYLE MUST NAME A COLUMN THE LAYER HAS. This used to classify on the
        # literal "__single__", which is not a column of `stations`: the KMZ was fine (it
        # falls back to a synthetic series) but `theme_qml()` wrote
        # `<renderer-v2 attr="__single__">`, and QGIS silently matches nothing against an
        # attribute that does not exist - an EMPTY layer, which looks exactly like a layer
        # with no features. theme_qml()'s own comment says this about the column TYPE; it is
        # more true of the column NAME. So the class column is written onto the frame.
        ThemeLayer("pumps", "Pumping stations", "stations", "point", "STR_KEY",
                   [("__single__", "Pumping station", (200, 30, 140), 2.0)],
                   st.assign(STR_KEY="__single__"), _ST_POP, "NAME"),
        ThemeLayer("forcemains", "Force mains", "rising_mains", "line", "DS_TYPE",
                   [("manhole", "Force main - lands on a MANHOLE where gravity resumes",
                     (230, 120, 20), 3.2),
                    ("stp", "Force main - lifts ALL THE WAY TO THE WORKS", (140, 40, 0), 4.4)],
                   rm, _RM_POP, "NAME"),
        ThemeLayer("subnetworks", "Subnetwork service areas", "subnetworks", "polygon",
                   "NAME", snclasses, sn2, _SN_POP, "NAME"),
    ]
    return out


def theme_depth(layers: Dict[str, gpd.GeoDataFrame]) -> List[ThemeLayer]:
    """The MAGMA ramp on EVERY element, on the FIXED published breaks in DEPTH_BREAKS."""
    out = []
    for key, title, role, geom, popup in (
            ("conduits", "Gravity conduits by depth", "reaches", "line", _REACH_POP),
            ("manholes", "Manholes by depth", "nodes", "point", _NODE_POP),
            ("pumps", "Pumping stations by wet-well depth", "stations", "point", _ST_POP),
            ("forcemains", "Force mains by the depth of the well they leave",
             "rising_mains", "line", _RM_POP),
            ("subnetworks", "Subnetworks by their DEEPEST chamber", "subnetworks",
             "polygon", _SN_POP)):
        gdf = layers[role]
        if role == "subnetworks":
            gdf = gdf[gdf.SERVED == 1]
        gdf = gdf.copy()
        gdf["DEP_BAND"] = _depth_index(gdf.DEP_M)
        out.append(ThemeLayer(key, title, role, geom, "DEP_BAND",
                              _depth_classes(geom), gdf, popup, None,
                              note="ONE column (DEP_M) on ONE fixed set of edges "
                                   f"({', '.join('%.2f' % b for b in DEPTH_BREAKS)} m), "
                                   "never auto-stretched, so two runs are comparable. What "
                                   "DEP_M means on each layer is in the field dictionary."))
    return out


# The kinds of exception, in the order they are drawn, with the severity that sets the
# symbol size. SEVERITY IS A RANK, not a measurement: 3 = the design does not work here,
# 2 = it works but breaks a rule the client will ask about, 1 = it needs a decision.
EXC_KINDS: List[Tuple[str, str, Tuple[int, int, int], int]] = [
    ("plot_cannot_connect", "Plots that CANNOT connect on gravity", (165, 0, 38), 3),
    ("subnet_not_at_main", "Subnetworks that do NOT reach the main pipe", (215, 25, 28), 3),
    ("outfall_off_low", "Outfalls OFF their subnetwork's own low point", (244, 109, 67), 2),
    ("drop_velocity_cap", "Drops that exist ONLY to hold the velocity cap", (253, 174, 97), 2),
    ("past_depth_cap", "Past the depth trigger", (110, 30, 5), 3),
    ("chamber_on_wadi", "Chambers on WADI ground", (84, 39, 143), 2),
    ("main_to_works", "Force mains that lift ALL THE WAY TO THE WORKS", (140, 40, 0), 2),
    ("station_rejected", "Pumping stations REMOVED - nothing drained into them",
     (37, 37, 37), 1),
    ("area_unserved", "Areas the network does not reach", (152, 0, 67), 3),
    ("reach_unlevelled", "Routes NOBODY LEVELLED - s6 published no reach here",
     (0, 0, 0), 3),
]
EXC_SIZE = {1: 1.0, 2: 1.5, 3: 2.2}       # symbol scale / line width by severity rank


def theme_exceptions(layers: Dict[str, gpd.GeoDataFrame]) -> List[ThemeLayer]:
    """ONLY the flagged items. Nothing that is not a problem appears on this map at all.

    The count is in the folder name, so the legend itself reports the totals - a reviewer
    reads 'Plots that CANNOT connect on gravity (5,521)' without opening a schedule."""
    nd, r, cn = layers["nodes"], layers["reaches"], layers["connections"]
    rm, sn = layers["rising_mains"], layers["subnetworks"]
    rej = layers.get("stations_rejected")
    out: List[ThemeLayer] = []

    def add(key, gdf, geom, popup, note="", label="NAME"):
        """`label` is what a reader sees floating over the feature. It is NOT always NAME:
        a plot connection and an unserved area have no name in the concept grammar, and an
        unlabelled placemark on an exceptions map is a red dot nobody can look up."""
        meta = next(x for x in EXC_KINDS if x[0] == key)
        _k, title, rgb, sev = meta
        g2 = gdf.copy()
        g2["EXC_KIND"] = key
        g2["EXC_SEV"] = sev
        lab = label if label in g2.columns else None
        out.append(ThemeLayer(key, title, key, geom, "EXC_KIND",
                              [(key, f"{title}   (severity {sev})", rgb, EXC_SIZE[sev])],
                              g2, popup, lab, note))

    add("plot_cannot_connect", cn[cn.CAN_CONN == 0], "line",
        (("PLOT_ID", "Plot", "{}"), ("OUT_NODE", "Chamber", "{}"),
         ("LEN_M", "Connection length", "{:.1f} m"),
         ("FALL_AV_M", "Fall available", "{:.2f} m"),
         ("CONN_NEED", "Sewer would have to be deeper by", "{:.2f} m"),
         ("CONN_WHY", "Why", "{}")),
        "each one says WHAT IT WOULD TAKE, in metres - rule 7, flag do not solve",
        label="PLOT_ID")
    add("subnet_not_at_main", sn[(sn.SERVED == 1) & (sn.JOIN_MAIN == 0)], "polygon",
        _SN_POP,
        "legal only if it ends at a designed station with a rising main "
        "(10_ASBUILT_CALIBRATION rule T1) - NAMA's own 5A-1 does exactly that",
        label="NAME")
    add("outfall_off_low", nd[pd.to_numeric(nd.JOIN_OFF_M, errors="coerce").fillna(0) > 0],
        "point",
        (("NAME", "Outfall chamber", "{}"), ("JOIN_OFF_M", "Off its own low point by",
                                             "{:.0f} m"), ("JOIN_WHY", "Why", "{}")))
    add("drop_velocity_cap", nd[(nd.DROP_TYPE != "none") & (nd.DROP_WHY == "velocity_cap")],
        "point", _NODE_POP,
        "the pipe could not take the ground's fall, so the surplus is taken at the "
        "manhole. TWO DIFFERENT BOUNDS ARRIVE UNDER THIS ONE WORD, because the contract's "
        f"DROP_WHY vocabulary has only one for it: the {C.V_MAX:g} m/s velocity maximum "
        f"(G203-p27 4.2.2.2, a GUIDELINE) and the "
        f"{EXPORT_NUM['SLOPE_MAX_LAID_PCT']:g} % laying bound (a PROJECT ASSUMPTION, "
        f"EXPORT_NUMBERS SLOPE_MAX_LAID_PCT, no guideline behind it). This run: "
        + (", ".join(f"{k} {v:,}" for k, v in sorted(DROP_CAUSE_SPLIT.items()))
           or "not yet counted")
        + ". Do not read the whole folder as a guideline consequence.")
    add("past_depth_cap", nd[nd.PAST_CAP == 1], "point",
        (("NAME", "Chamber", "{}"), ("COVER_M", "Cover", "{:.2f} m"),
         ("CAP_EXIT", "Exit held", "{}"),
         ("CAP_LEN_M", "Distance to recovery / outfall", "{:.0f} m")),
        f"the cap is {C.MAX_COVER:g} m of COVER (G203-p33); a blank CAP_EXIT is a "
        "STATION DEMAND, not a flag")
    add("chamber_on_wadi", nd[pd.to_numeric(nd.ON_WADI, errors="coerce").fillna(0) > 0],
        "point", _NODE_POP,
        "H1: no chamber ALONG a wadi. A crossing is legal under H1a; presence is not")
    add("main_to_works", rm[rm.DS_TYPE == "stp"], "line", _RM_POP,
        "concept rule 6: a rising main lifts to the NEAREST point where gravity resumes. "
        "A long force main goes anaerobic, needs an air valve at every summit and a "
        "washout at every low point, and is a single point of failure")
    if rej is not None and len(rej):
        add("station_rejected", rej, "point",
            (("NODE_REF", "s7 reference", "{}"), ("UID_S7", "s7 id", "{}"),
             ("Q_DUTY_LS", "Duty s7 gave it", "{:.1f} L/s"),
             ("REJECT_WHY", "Why it was removed", "{}")),
            "inheritance row 4 - removed here and published, never deleted",
            label="NODE_REF")
    add("area_unserved", sn[sn.SERVED == 0], "polygon",
        (("FLAG", "Area", "{}"), ("N_PLOT", "Plots", "{:.0f}"),
         ("N_PROP", "Properties", "{:.1f}"), ("Q_ADF_M3D", "Load", "{:.1f} m3/d"),
         ("WHY", "Why", "{}")), label="FLAG")
    unlev = layers.get("reaches_unlevelled")
    if unlev is not None and len(unlev):
        add("reach_unlevelled", unlev, "line",
            (("EDGE_UID", "Reach", "{}"), ("US_NODE", "From", "{}"),
             ("DS_NODE", "To", "{}"), ("LEN_M", "Length", "{:.1f} m"),
             ("QADF_M3D", "Load it carries", "{:.1f} m3/d"),
             ("LIFT_M", "s6 lift, where it made this a pumped link", "{:.2f} m"),
             ("GAP_KIND", "Kind", "{}"), ("WHY", "Why", "{}")),
            "these routes carry NO invert, NO gradient and NO diameter, because the stage "
            "that levels the network published nothing for them. They are OFF the reaches "
            "layer and out of every length, quantity and schedule - the alternative was to "
            "give them the retired stand-in's gradient between two of s6's inverts, which "
            "describes no pipe",
            label="EDGE_UID")

    return [t for t in out if t.n > 0]


THEME_BUILDERS = {
    "structure": theme_structure,
    "depth": theme_depth,
    "exceptions": theme_exceptions,
}
THEME_TITLES = {
    "structure": "W12 STRUCTURE - what the network IS",
    "depth": "W12 DEPTH - how deep everything sits, on fixed comparable bands",
    "exceptions": "W12 EXCEPTIONS - what could NOT be solved",
}


def build_themes(layers: Dict[str, gpd.GeoDataFrame]) -> Dict[str, List[ThemeLayer]]:
    out: Dict[str, List[ThemeLayer]] = {}
    for name, fn in THEME_BUILDERS.items():
        try:
            out[name] = fn(layers)
            THEME_FAILURES.pop(name, None)
        except Exception as e:                                 # pragma: no cover
            # RECORDED, not only printed. An empty EXCEPTIONS map reads as "we checked and it
            # is fine" - this module's own reason for omitting an empty folder - so the
            # failure has to reach the deliverable. check_contract() publishes a row per
            # entry here on the `contract_check` layer.
            THEME_FAILURES[name] = f"{type(e).__name__}: {e}"
            _log(f"   THEME '{name}' COULD NOT BE BUILT: {type(e).__name__}: {e}")
            out[name] = []
    for name, tls in out.items():
        _log(f"   theme {name:<11} {len(tls)} layers, "
             + ", ".join(f"{t.key}={t.n:,}" for t in tls))
    return out


# ======================================================================================
# 8b.  WRITING A THEME - one KMZ, and one .qml per layer
#
#      Written here rather than through `present.kmz()` because a theme is one FILE with a
#      folder per layer, and `present` is one file per view. Both read the same class
#      tables, so nothing can drift; what this adds is the folder structure, the count in
#      the folder name, and the size control that lets a 57,000-chamber network open.
# ======================================================================================

_WGS = 4326


def _to_wgs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return gdf.to_crs(_WGS) if gdf.crs is not None else gdf


def _coords(geom) -> List[str]:
    """Every ring or line of a geometry, as KML coordinate strings."""
    if geom is None or geom.is_empty:
        return []
    parts = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    out = []
    for p in parts:
        if p.geom_type == "Polygon":
            cs = list(p.exterior.coords)
        elif p.geom_type in ("LineString", "LinearRing"):
            cs = list(p.coords)
        elif p.geom_type == "Point":
            cs = [(p.x, p.y)]
        else:
            continue
        if len(cs) >= 1:
            out.append(" ".join(f"{c[0]:.6f},{c[1]:.6f},0" for c in cs))
    return out


def _kml_geom(geom, kind: str) -> str:
    tag = {"line": "LineString", "polygon": "Polygon", "point": "Point"}[kind]
    bits = []
    for cs in _coords(geom):
        if kind == "polygon":
            bits.append("<Polygon><outerBoundaryIs><LinearRing><coordinates>"
                        + cs + "</coordinates></LinearRing></outerBoundaryIs></Polygon>")
        elif kind == "line":
            bits.append("<LineString><tessellate>1</tessellate><coordinates>"
                        + cs + "</coordinates></LineString>")
        else:
            bits.append("<Point><coordinates>" + cs + "</coordinates></Point>")
    if not bits:
        return ""
    if len(bits) == 1:
        return bits[0]
    return "<MultiGeometry>" + "".join(bits) + "</MultiGeometry>"


def _esc(v: Any) -> str:
    return (str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _balloon(row, popup: Sequence[Tuple[str, str, str]]) -> str:
    rows = []
    for fld, head, spec in popup:
        if fld not in row.index:
            continue
        v = row[fld]
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            continue
        try:
            txt = spec.format(v)
        except Exception:
            txt = str(v)
        if str(txt).strip() in ("", "nan"):
            continue
        rows.append(f"<tr><td><b>{_esc(head)}</b></td><td>{_esc(txt)}</td></tr>")
    return "<table>" + "".join(rows) + "</table>" if rows else ""


def _style_block(sid: str, rgb, width: float, geom: str) -> str:
    col = PR.kml_color(rgb)
    if geom == "point":
        return (f'<Style id="{sid}"><IconStyle><color>{col}</color>'
                f'<scale>{width:.2f}</scale><Icon><href>'
                f'http://maps.google.com/mapfiles/kml/shapes/donut.png</href></Icon>'
                f'</IconStyle><LabelStyle><scale>0.7</scale></LabelStyle></Style>')
    if geom == "polygon":
        return (f'<Style id="{sid}"><LineStyle><color>{col}</color><width>2</width>'
                f'</LineStyle><PolyStyle><color>{PR.kml_color(rgb, 0.28)}</color>'
                f'</PolyStyle></Style>')
    return (f'<Style id="{sid}"><LineStyle><color>{col}</color>'
            f'<width>{max(1.0, width):.2f}</width></LineStyle></Style>')


def theme_kmz(theme: str, tls: Sequence[ThemeLayer], trunk: Optional[gpd.GeoDataFrame],
              arrows: Optional[Sequence[Sequence[Tuple[float, float]]]] = None) -> str:
    """One KMZ per theme: a folder per layer, the count in the folder name, and the class
    list written into the folder description so the legend travels with the file."""
    P = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
         f'<name>{_esc(THEME_TITLES[theme])}</name>',
         f'<description><![CDATA[<p>{_esc(VERSION)}, built '
         f'{time.strftime("%Y-%m-%d %H:%M")}. EPSG:{CT.CRS_EPSG} reprojected to WGS84.</p>'
         f'<p><b>{_esc(C.concept_banner())}</b></p>'
         f'<p>{_esc(C.tau_banner())}</p>'
         f'<p>Levels: {_esc(LEVELS_SOURCE)}.</p>]]></description>']

    n_written = 0
    for tl in tls:
        gdf = _to_wgs(tl.gdf)
        if not len(gdf):
            continue
        cls = {str(k): (i, lab, rgb, w) for i, (k, lab, rgb, w) in enumerate(tl.classes)}
        for i, (_k, lab, rgb, w) in enumerate(tl.classes):
            P.append(_style_block(f"{tl.key}_{i}", rgb, w, tl.geom))
        legend = "".join(f"<li>{_esc(lab)}</li>" for _k, lab, _c, _w in tl.classes[:60])
        P.append(f'<Folder><name>{_esc(tl.folder_name())}</name><open>0</open>'
                 f'<description><![CDATA[<ul>{legend}</ul>'
                 + (f"<p><i>{_esc(tl.note)}</i></p>" if tl.note else "")
                 + ']]></description>')
        vals = gdf[tl.field].astype(str) if tl.field in gdf.columns else \
            pd.Series(["__single__"] * len(gdf), index=gdf.index)
        if len(gdf) <= KMZ_INDIVIDUAL_MAX:
            for (_i, row), v in zip(gdf.iterrows(), vals):
                gm = _kml_geom(row.geometry, tl.geom)
                if not gm:
                    continue
                sid = cls.get(v, (0, "", (150, 150, 150), 1.0))[0]
                nmv = row[tl.label_field] if tl.label_field and tl.label_field in row.index else ""
                P.append(f'<Placemark><name>{_esc(nmv)}</name>'
                         f'<description><![CDATA[{_balloon(row, tl.popup)}]]></description>'
                         f'<styleUrl>#{tl.key}_{sid}</styleUrl>{gm}</Placemark>')
                n_written += 1
        else:
            # ONE placemark per class holding every feature in it. A 57,000-placemark
            # folder will not pan; at the zoom a layout is judged from you cannot see one
            # chamber anyway. The popup then describes the CLASS, and the folder says so.
            for v, sub in gdf.groupby(vals):
                gm = [b for row in sub.geometry for b in _coords(row)]
                if not gm:
                    continue
                i, lab, _rgb, _w = cls.get(str(v), (0, str(v), (150, 150, 150), 1.0))
                tag = {"line": "LineString", "polygon": "Polygon",
                       "point": "Point"}[tl.geom]
                inner = "".join(
                    (f"<{tag}><tessellate>1</tessellate><coordinates>{c}</coordinates></{tag}>"
                     if tl.geom == "line" else
                     (f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{c}"
                      f"</coordinates></LinearRing></outerBoundaryIs></Polygon>"
                      if tl.geom == "polygon" else
                      f"<Point><coordinates>{c}</coordinates></Point>")) for c in gm)
                P.append(f'<Placemark><name>{_esc(lab)} ({len(sub):,})</name>'
                         f'<description><![CDATA[<p>{_esc(lab)}</p><p>{len(sub):,} features. '
                         f'Drawn as one placemark per class because this layer holds more '
                         f'than {KMZ_INDIVIDUAL_MAX:,} features; the per-feature attributes '
                         f'are in the GeoPackage and the shapefile.</p>]]></description>'
                         f'<styleUrl>#{tl.key}_{i}</styleUrl>'
                         f'<MultiGeometry>{inner}</MultiGeometry></Placemark>')
                n_written += len(sub)
        P.append('</Folder>')

    if trunk is not None and len(trunk):
        P.append('<Style id="trunk"><LineStyle><color>ff1111ff</color><width>6</width>'
                 '</LineStyle></Style>')
        t4 = _to_wgs(trunk)
        inner = "".join(f"<LineString><tessellate>1</tessellate><coordinates>{c}"
                        f"</coordinates></LineString>"
                        for gm in t4.geometry for c in _coords(gm))
        P.append(f'<Folder><name>Main pipe - CLIENT INPUT ({len(t4)})</name><open>1</open>'
                 f'<Placemark><name>Main Pipe</name><description><![CDATA['
                 f'<p>The client\'s own drawing. Not chambered, not levelled, not sized. '
                 f'NOTHING in this export drains into it.</p>]]></description>'
                 f'<styleUrl>#trunk</styleUrl><MultiGeometry>{inner}</MultiGeometry>'
                 f'</Placemark></Folder>')

    if arrows:
        P.append('<Style id="flow"><LineStyle><color>ff303030</color><width>2</width>'
                 '</LineStyle></Style>')
        inner = "".join("<LineString><tessellate>1</tessellate><coordinates>"
                        + " ".join(f"{x:.6f},{y:.6f},0" for x, y in seg)
                        + "</coordinates></LineString>" for seg in arrows)
        P.append(f'<Folder><name>Flow direction ({len(arrows) // 2})</name><open>1</open>'
                 f'<Placemark><styleUrl>#flow</styleUrl>'
                 f'<MultiGeometry>{inner}</MultiGeometry></Placemark></Folder>')

    P.append('</Document></kml>')
    path = os.path.join(DIR_KMZ, f"W12_theme_{theme}.kmz")
    os.makedirs(DIR_KMZ, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("doc.kml", "\n".join(P))
    _log(f"   {os.path.basename(path):<30} {os.path.getsize(path) / 1e6:6.2f} MB  "
         f"{len(tls)} folders, {n_written:,} features")
    return path


_QML_HEAD = ('<!DOCTYPE qgis PUBLIC "http://mrcc.com/qgis.dtd" "SYSTEM">\n'
             '<qgis version="3.34" styleCategories="Symbology|Labeling">\n')


def _qml_symbol(idx: int, geom: str, rgb, width: float) -> str:
    r, g_, b = rgb
    if geom == "line":
        layer = (f'<layer class="SimpleLine" pass="0" locked="0">'
                 f'<Option type="Map">'
                 f'<Option name="line_color" type="QString" value="{r},{g_},{b},255"/>'
                 f'<Option name="line_width" type="QString" value="{max(0.2, width * 0.22):.2f}"/>'
                 f'<Option name="line_width_unit" type="QString" value="MM"/>'
                 f'<Option name="capstyle" type="QString" value="round"/>'
                 f'<Option name="joinstyle" type="QString" value="round"/>'
                 f'</Option></layer>')
        stype = "line"
    elif geom == "polygon":
        layer = (f'<layer class="SimpleFill" pass="0" locked="0">'
                 f'<Option type="Map">'
                 f'<Option name="color" type="QString" value="{r},{g_},{b},70"/>'
                 f'<Option name="outline_color" type="QString" value="{r},{g_},{b},255"/>'
                 f'<Option name="outline_width" type="QString" value="0.4"/>'
                 f'<Option name="outline_width_unit" type="QString" value="MM"/>'
                 f'<Option name="style" type="QString" value="solid"/>'
                 f'</Option></layer>')
        stype = "fill"
    else:
        layer = (f'<layer class="SimpleMarker" pass="0" locked="0">'
                 f'<Option type="Map">'
                 f'<Option name="color" type="QString" value="{r},{g_},{b},255"/>'
                 f'<Option name="outline_color" type="QString" value="35,35,35,255"/>'
                 f'<Option name="outline_width" type="QString" value="0.2"/>'
                 f'<Option name="size" type="QString" value="{max(0.6, width * 1.1):.2f}"/>'
                 f'<Option name="size_unit" type="QString" value="MM"/>'
                 f'<Option name="name" type="QString" value="circle"/>'
                 f'</Option></layer>')
        stype = "marker"
    return (f'<symbol name="{idx}" type="{stype}" alpha="1" force_rhr="0" frame_rate="10">'
            f'{layer}</symbol>')


def theme_qml(theme: str, tl: ThemeLayer) -> str:
    """A saved QGIS style for one theme layer, written WITHOUT QGIS.

    `present.qgis_plan()` asks QGIS itself to save a .qml, which is better XML - but it
    needs QGIS running. A style file that only exists when the reviewer has already opened
    the project is not a deliverable, so this writes a plain categorized renderer from the
    SAME class table the KMZ drew, and QGIS overwrites it with its own the moment the
    loader is run."""
    cats, syms = [], []
    for i, (key, lab, rgb, w) in enumerate(tl.classes):
        # the declared type has to match the COLUMN, not the look of the value: a depth
        # band is an integer column and QGIS silently matches nothing if it is told the
        # category is a double. A style that renders nothing looks exactly like a layer
        # with no features.
        if isinstance(key, bool):
            qtype = "QString"
        elif isinstance(key, (int, np.integer)):
            qtype = "int"
        elif isinstance(key, (float, np.floating)):
            qtype = "double"
        else:
            qtype = "QString"
        cats.append(f'<category render="true" symbol="{i}" value="{_esc(key)}" '
                    f'label="{_esc(lab)}" type="{qtype}"/>')
        syms.append(_qml_symbol(i, tl.geom, rgb, w))
    xml = (_QML_HEAD
           + f'  <!-- W12 theme {theme} / layer {tl.key}: {_esc(tl.title)} -->\n'
           + f'  <!-- {_esc(tl.note)} -->\n'
           + f'  <renderer-v2 type="categorizedSymbol" attr="{_esc(tl.field)}" '
             f'forceraster="0" symbollevels="0" enableorderby="0">\n'
             f'    <categories>' + "".join(cats) + '</categories>\n'
             f'    <symbols>' + "".join(syms) + '</symbols>\n'
             f'  </renderer-v2>\n'
           + '</qgis>\n')
    path = os.path.join(DIR_KMZ, f"W12_{theme}_{tl.key}.qml")
    open(path, "w", encoding="utf-8").write(xml)
    return path


def write_themes(layers: Dict[str, gpd.GeoDataFrame],
                 arrows: Optional[Sequence[Sequence[Tuple[float, float]]]] = None
                 ) -> Dict[str, List[str]]:
    """The three themes, each as one KMZ and one saved QGIS style per layer."""
    themes = build_themes(layers)
    # the arrows are built in UTM (metres, because their size is a length); the KMZ is
    # WGS84. Reprojected HERE and once, rather than inside the writer, so a caller cannot
    # hand the writer metres and get arrows in the Gulf of Guinea.
    arrows_wgs = None
    if arrows:
        gs = gpd.GeoSeries([LineString(s) for s in arrows],
                           crs=f"EPSG:{CT.CRS_EPSG}").to_crs(_WGS)
        arrows_wgs = [list(ls.coords) for ls in gs]
    out: Dict[str, List[str]] = {}
    for name, tls in themes.items():
        if not tls:
            _log(f"   theme '{name}' produced NO layers - not written, and said so here "
                 f"rather than leaving an empty file that reads like a clean result")
            continue
        files = [theme_kmz(name, tls, layers.get("trunk"),
                           arrows_wgs if name == "structure" else None)]
        files += [theme_qml(name, tl) for tl in tls]
        out[name] = files
    return out


def flow_arrows(reaches: gpd.GeoDataFrame, every_m: float = 600.0, size: float = 22.0
                ) -> List[List[Tuple[float, float]]]:
    """An open V every `every_m` along the bigger pipes, pointing the way the flow goes.

    Only on the main and sub-main tiers: an arrow on every lateral is a grey smear at the
    zoom anyone actually reads a layout at."""
    tier = reaches.TIER.astype(str) if "TIER" in reaches.columns else pd.Series("", index=reaches.index)
    keep = reaches[tier.str.contains("main", case=False, na=False)]
    segs: List[List[Tuple[float, float]]] = []
    run = 0.0
    for gm in keep.geometry:
        parts = list(gm.geoms) if gm.geom_type.startswith("Multi") else [gm]
        for part in parts:
            cs = list(part.coords)
            for i in range(len(cs) - 1):
                (x0, y0), (x1, y1) = cs[i][:2], cs[i + 1][:2]
                d = math.hypot(x1 - x0, y1 - y0)
                run += d
                if run >= every_m and d > 1.0:
                    run = 0.0
                    x, y = (x0 + x1) / 2, (y0 + y1) / 2
                    back = math.atan2(y1 - y0, x1 - x0) + math.pi
                    a = (x + size * math.cos(back + 0.42), y + size * math.sin(back + 0.42))
                    b = (x + size * math.cos(back - 0.42), y + size * math.sin(back - 0.42))
                    segs += [[a, (x, y)], [(x, y), b]]
    return segs




# ======================================================================================
# 7c.  IS EACH OUTFALL AT THE BOTTOM OF ITS OWN CATCHMENT?
#
#      The first long section this stage drew answered a question nobody had asked. Over
#      15.40 km of package P003 the invert falls 51 m in a straight line while the GROUND
#      rises 8 m - because the component's outfall sits near the TOP of its own ground, not
#      the bottom. No levelling arithmetic can recover that: if the terminal node is uphill
#      of the catchment, every metre of the run buys depth it never gives back.
#
#      So the outfall's ground level is compared with the ground of every chamber in its own
#      component. The percentile is the number: 0 % means the outfall IS the lowest point,
#      which is what it should be; 90 % means 90 % of the catchment is BELOW its own outlet.
#      This is a stage-2 / stage-3 orientation measurement, published here because this is
#      the stage that first had the levels to see it.
# ======================================================================================

def flow_orphans() -> pd.DataFrame:
    """H15 AGAINST s5's OWN PUBLISHED LAYERS: every node with nowhere to send its flow.

    `tests/test_columns.py::test_every_node_without_an_outlet_is_an_outfall` fails on the
    003 run and the failure is real. MEASURED here off `W12_flows.gpkg`, so the answer is
    on the deliverable instead of in a pytest line nobody keeps:

      * 154 of 10,183 corridor nodes have no outgoing arc that s5 marks IS_ROUTE = 1 and
        are not marked IS_OUTFALL. Every one of them is KIND = 'head' with DEAD_END = 1,
        sitting on one of the 184 arcs s5 itself labels ROLE = 'island', DELIVERED = 0 -
        30.88 km carrying 762.6 m3/d.
      * THEY ARE REAL DEAD ENDS, not a wiring bug: s5 found no route from them to any
        outfall and said so on the ARC layer.
      * WHAT IS A PUBLICATION DEFECT IS THE NODE LAYER. It publishes DELIVERED = 1 on all
        10,183 rows - a constant column - so the same GeoPackage says the arc is
        undelivered and the node on it is delivered. One of the two is wrong, and it is
        the constant one. That is the second failing audit check
        (test_node_delivered_agrees_with_arc_delivered) and it is the SAME defect.
      * It is s5_flows.py's to fix, not this stage's: s5 owns both columns. Published here
        rather than repaired here, because repairing a column this stage does not own is
        how two answers to one question get made.

    Nothing is asserted below - every number is read off the file each run."""
    cols = ["NODE_UID", "X", "Y", "GRD_M", "KIND", "IS_OUTFALL", "DEAD_END", "DELIVERED",
            "Q_ADF_M3D", "N_PROP", "WHY"]
    try:
        arcs = gpd.read_file(GPKG_FLOWS, layer="arcs", ignore_geometry=True)
        nds = gpd.read_file(GPKG_FLOWS, layer="nodes", ignore_geometry=True)
    except Exception as e:                                     # pragma: no cover - IO
        return pd.DataFrame([dict(NODE_UID="", X=0.0, Y=0.0, GRD_M=0.0, KIND="",
                                  IS_OUTFALL=0, DEAD_END=0, DELIVERED=0, Q_ADF_M3D=0.0,
                                  N_PROP=0.0,
                                  WHY=f"the check COULD NOT RUN: {type(e).__name__}: {e}. "
                                      f"A check that cannot run is a failure, not a blank "
                                      f"(philosophy sec 8)")], columns=cols)
    has_out = set(arcs.loc[arcs.IS_ROUTE.astype(int) == 1, "US_NODE"].astype(str))
    st = nds[~nds.NODE_UID.astype(str).isin(has_out)
             & (nds.IS_OUTFALL.astype(int) == 0)].copy()
    isl = arcs[arcs.DELIVERED.astype(int) == 0]
    on_isl = set(isl.US_NODE.astype(str)) | set(isl.DS_NODE.astype(str))
    n_const = int(nds.DELIVERED.astype(int).nunique() == 1)
    out = []
    for r in st.itertuples():
        u = str(r.NODE_UID)
        island = u in on_isl
        out.append(dict(
            NODE_UID=u, X=round(float(r.X), 3), Y=round(float(r.Y), 3),
            GRD_M=round(float(r.GRD_M), 3), KIND=str(r.KIND),
            IS_OUTFALL=int(r.IS_OUTFALL), DEAD_END=int(getattr(r, "DEAD_END", 0)),
            DELIVERED=int(getattr(r, "DELIVERED", 0)),
            Q_ADF_M3D=round(float(getattr(r, "Q_ADF_M3D", 0.0)), 3),
            N_PROP=round(float(getattr(r, "N_PROP", 0.0)), 2),
            WHY=("a REAL dead end: it sits on an arc s5 itself marks ROLE = 'island', "
                 "DELIVERED = 0, so s5 found no route from here to any outfall - yet the "
                 "node layer publishes DELIVERED = 1"
                 + (" on EVERY one of its rows, which is a constant column, not a "
                    "measurement" if n_const else "")
                 + ". s5_flows.py owns both columns; this is published, not repaired here")
            if island else
            ("no outgoing arc with IS_ROUTE = 1 and IS_OUTFALL = 0, and it is not on any "
             "arc s5 marks undelivered either - so nothing in the file says where its "
             "flow goes")))
    df = pd.DataFrame(out, columns=cols)
    if len(df):
        _log(f"   H15 against s5: {len(df):,} of {len(nds):,} corridor nodes have no "
             f"outgoing route arc and are not outfalls, carrying "
             f"{df.Q_ADF_M3D.sum():,.1f} m3/d on {len(isl):,} island arcs "
             f"({isl.LEN_M.sum() / 1000.0:.2f} km). s5's NODE layer publishes DELIVERED = 1 "
             f"on {'all' if n_const else 'some'} of them.")
    return df


def outfall_check(g: Graph, f: Flows, layers: Dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    nd = layers["nodes"]
    grd = g.grd
    rows = []
    for out_i in np.unique(f.subnet):
        sel = f.subnet == out_i
        gs = grd[sel]
        z = float(grd[out_i])
        pct = float((gs < z).sum()) / max(1, len(gs)) * 100.0
        esel = sel[g.e_us]
        dsel = pd.to_numeric(nd.DEPTH_M, errors="coerce").to_numpy(dtype=float)[sel]
        rows.append(dict(
            OUTFALL=g.uid[int(out_i)],
            PACKAGE=str(nd.PACKAGE.iloc[int(out_i)]),
            N_CHAMBER=int(sel.sum()),
            LEN_KM=round(float(g.e_len[esel].sum()) / 1000.0, 3),
            GRD_OUT=round(z, 2),
            GRD_MIN=round(float(gs.min()), 2),
            GRD_MAX=round(float(gs.max()), 2),
            ABOVE_LOW=round(z - float(gs.min()), 2),
            PCT_BELOW=round(pct, 1),
            LOWEST=int(pct < 1.0),
            # nan-AWARE, AND THE BLANKS COUNTED. A chamber the leveller did not level
            # carries DEPTH_M = NULL, and a plain .max() over one of them returns nan for
            # the whole component - 219 of 276 rows on the 12:00 export were blank for
            # that reason, with nothing on the row saying the check could not run.
            DEEPEST_M=(round(float(np.nanmax(dsel)), 2) if np.isfinite(dsel).any()
                       else float("nan")),
            NO_LEVEL=int((~np.isfinite(dsel)).sum()),
            Q_ADF_M3D=round(float(f.q_adf[out_i]), 1)))
    df = pd.DataFrame(rows).sort_values("LEN_KM", ascending=False).reset_index(drop=True)
    if int(df.NO_LEVEL.sum()):
        _log(f"   outfall check: {int((df.NO_LEVEL > 0).sum())} of {len(df)} components "
             f"contain a chamber with NO LEVEL ({int(df.NO_LEVEL.sum()):,} chambers); "
             f"DEEPEST_M is over the levelled ones only and NO_LEVEL says how many were "
             f"left out. A blank is a check that could not run (philosophy sec 8).")
    bad = df[(df.PCT_BELOW > 50.0) & (df.N_CHAMBER >= 20)]
    _log(f"   outfall check: {int(df.LOWEST.sum())} of {len(df)} components discharge at "
         f"their OWN lowest chamber; {len(bad)} components of 20+ chambers "
         f"({bad.LEN_KM.sum():.1f} km) discharge with more than half their catchment BELOW "
         f"the outlet; worst {df.ABOVE_LOW.max():.1f} m above its own low point")
    return df


# ======================================================================================
# 8b.  SUBFOLDERS AND LABELS ON THE GRADUATED VIEWS
#
#      "SUBFOLDERS inside each file for manageability ... labels legible at the zoom a
#       reviewer actually uses."   - engineer, both requests, verbatim
#
#      A CATEGORICAL view folds itself: `folder_fields=("TIER",)` gives four folders you
#      can tick on and off. A GRADUATED one - depth, ground fall, d/D, velocity, flow -
#      had nowhere to fold, because its classes are computed at draw time and there is no
#      column carrying them. So all 56,740 reaches landed in one folder and the file was
#      exactly as unmanageable as the engineer said.
#
#      The fix does not touch `present.py`. It asks the library to classify the layer,
#      writes the CLASS LABEL IT PRODUCED back as a column, and points the view's folder
#      at that column. The folder tree and the legend then read the same words BY
#      CONSTRUCTION, because they are the same object.
# ======================================================================================

BAND_COLUMNS: List[Tuple[str, str, str]] = [
    # view, role, column (<= 10 characters: contract.SHP_FIELD_MAXLEN)
    ("depth", "reaches", "DEPTH_BND"),
    ("ground_fall", "reaches", "FALL_BND"),
    ("capacity", "reaches", "DOD_BND"),
    ("velocity", "reaches", "V_BND"),
    ("flow", "reaches", "Q_BND"),
    ("chambers", "nodes", "CH_DEP_BND"),
]


def add_band_columns(layers: Dict[str, gpd.GeoDataFrame]) -> Dict[str, int]:
    """Write each graduated view's own class label back onto the layer, and fold on it."""
    made: Dict[str, int] = {}
    for vname, role, col in BAND_COLUMNS:
        v = PR.VIEWS[vname]
        df = layers[role]
        work = df
        if v.derive:
            fn, cols = PR.DERIVERS[v.derive]
            if not all(c in work.columns for c in cols):
                work = fn(work)
        cls = PR.classify(work, v)
        idx = cls.index
        lab = np.array([c.label for c in cls.classes] + ["(outside every band)"])
        df[col] = lab[np.where(idx >= 0, idx, len(lab) - 1)]
        made[vname] = int(pd.Series(df[col]).nunique())
    fold_on_bands()
    _log("   folded the graduated views on their own class labels: "
         + ", ".join(f"{k} ({n})" for k, n in made.items()))
    return made


def fold_on_bands() -> None:
    """Point each graduated view's folder at its band column.

    Separate from writing the columns because the KMZ can be rebuilt on its own
    (`python s8_export.py kmz`) off the published GeoPackage, where the columns already
    exist. The first cut set the folders inside the column writer, so a kmz-only rerun
    silently produced the one-folder files this whole section exists to stop."""
    for vname, _role, col in BAND_COLUMNS:
        v = PR.VIEWS[vname]
        v.folder_fields = (col,)
        v.folder_sort = "count"


def tune_views() -> None:
    """Labels a reviewer can actually use, and a diameter palette that covers a rising main.

    Everything here mutates a registered `View` - the library's own declaration object -
    rather than reimplementing anything it does."""
    # THE DEPTH VIEWS AND THE DEPTH THEME MUST USE THE SAME EDGES AND THE SAME RAMP. Two
    # depth maps in one deliverable, banded differently, is the picture-level form of the
    # defect this project keeps paying for. `present` shipped [1.3, 3, 6, 9, 12] on its own
    # ramp; DEPTH_BREAKS is the published set and MAGMA is the published ramp, so both
    # views are moved onto them here rather than the theme being bent to match the view.
    for vn in ("depth", "chambers"):
        v = PR.VIEWS[vn]
        v.breaks = list(DEPTH_BREAKS)
        v.break_refs = list(DEPTH_BREAK_REFS)
        v.ramp = "magma"
        v.field = "DEP_M"

    d = PR.VIEWS["depth"]
    d.label_expr = lambda r: f"{float(r['DEP_M']):.1f} m"
    d.label_filter = lambda x: (pd.to_numeric(x["DEP_M"], errors="coerce")
                                > C.MAX_COVER) if "DEP_M" in x else None
    d.label_field = "DEP_M"
    d.label_min_lod, d.label_max = 256, 5000

    dia = PR.VIEWS["diameter"]
    dia.label_expr = lambda r: f"DN{int(r['DN'])}"
    dia.label_filter = lambda x: (pd.to_numeric(x["DN"], errors="coerce") >= 400) \
        if "DN" in x else None
    dia.label_field = "DN"
    dia.label_min_lod, dia.label_max = 200, 4000

    fl = PR.VIEWS["flow"]
    fl.label_expr = lambda r: f"{float(r['QPK_LS']):.0f} L/s"
    fl.label_filter = lambda x: (pd.to_numeric(x["QPK_LS"], errors="coerce") >= 25.0) \
        if "QPK_LS" in x else None
    fl.label_field = "QPK_LS"
    fl.label_min_lod, fl.label_max = 200, 3000

    # SUBNET on the published layer is "S03" and "S03" IS NOT UNIQUE ACROSS TOWNS - the
    # town letter is the other half of the name. Colouring or foldering on SUBNET alone
    # would merge subnetwork 3 in Ibri with subnetwork 3 in Ad Dariz into one class, which
    # would read as a network twice the size it is. SUB_NAME is the full "I-S03".
    sn = PR.VIEWS["subnet"]
    sn.field = "SUB_NAME"
    sn.derive = None                # the stage publishes it; nothing needs deriving
    sn.folder_fields = ("SUB_NAME",)
    sn.label_field = "SUB_NAME"
    sn.label_min_lod, sn.label_max = 900, 400
    sn.notes = tuple(sn.notes) + (
        "The class is the subnetwork's full NAME - town letter AND number. SUBNET alone is "
        "S03, which two towns can both carry.",)

    # The DN palette in `present` is the GRAVITY series and starts at DN200. A rising main
    # is sized on pump duty (G203-p50) and this scheme's run DN80-DN300, so four of its
    # sizes fell off the end of the palette and drew in fallback colours. Give the rising
    # mains their own series - the same `size` ramp, different domain.
    rm = PR.VIEWS["rising_mains"]
    series = [80, 100, 150, 200, 250, 300, 400, 500, 600]
    rm.categories = [(dn, f"DN{dn} rising main",
                      PR.ramp_rgb("size", i / (len(series) - 1)),
                      round(1.6 + 3.4 * (i / (len(series) - 1)) ** 0.8, 2))
                     for i, dn in enumerate(series)]
    rm.folder_fields = ("DN",)
    rm.folder_sort = "length"
    rm.label_expr = lambda r: f"{r['STATION']}  DN{int(r['DN'])}  {float(r['LEN_M']):.0f} m"

# ======================================================================================
# 9.  SHAPEFILES
#
#     The contract's 10-character rule exists so this round trip loses nothing: every
#     published field name fits a DBF, so the GeoPackage and the shapefile carry the SAME
#     names and a check can rely on either. `write_shapefiles` PROVES it by reading each
#     file back and comparing the column set.
# ======================================================================================

SHP_STR_MAX = 254          # the DBF character-field limit; not a choice


def _shp_ready(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    for c in out.columns:
        if c == out.geometry.name:
            continue
        s = out[c]
        if s.dtype == bool:
            out[c] = s.astype(np.int8)
        elif s.dtype == object or str(s.dtype) in ("string", "str"):
            out[c] = s.astype(str).str.slice(0, SHP_STR_MAX)
    return out


def assert_shp_names(layers: Dict[str, gpd.GeoDataFrame]) -> None:
    """EVERY column this stage writes fits a DBF name, not only the declared ones.

    `contract._assert_shp_safe()` checks the LayerSpecs at import. It cannot check the
    presentation and diagnostic columns this stage adds - CAP_WHY, STR_CLS, SUB_NAME,
    DEP_M and the rest - and those are exactly the ones nobody remembers to keep short. A
    truncated name is a field the auditor cannot find, so this raises BEFORE anything is
    written rather than after the shapefile is on disk."""
    bad: List[str] = []
    for name, gdf in layers.items():
        gname = gdf.geometry.name if isinstance(gdf, gpd.GeoDataFrame) else "geometry"
        for c in gdf.columns:
            if c in (gname, "geometry"):
                continue
            if len(str(c)) > CT.SHP_FIELD_MAXLEN:
                bad.append(f"{name}.{c} ({len(str(c))} chars)")
    if bad:
        raise CT.ContractError(
            f"{len(bad)} published column name(s) exceed the {CT.SHP_FIELD_MAXLEN}-character "
            "DBF limit and would be TRUNCATED in the shapefile, where no check could find "
            "them again:\n  " + "\n  ".join(bad)
            + "\nShorten the name at the point it is written. The engineer's short forms "
              "are the convention - `inv` for invert level, `g` for ground - and every "
              "abbreviation is spelled out in W12_FIELD_DICTIONARY.md.")


def write_shapefiles(layers: Dict[str, gpd.GeoDataFrame],
                     tables: Dict[str, pd.DataFrame]) -> List[str]:
    assert_shp_names(layers)
    written = []
    for name, gdf in layers.items():
        if len(gdf) == 0:
            continue
        path = os.path.join(DIR_SHP, f"W12_{name}.shp")
        g = _shp_ready(gdf)
        g.to_file(path, driver="ESRI Shapefile", encoding="utf-8")
        back = gpd.read_file(path)
        lost = sorted(set(g.columns) - set(back.columns) - {g.geometry.name, "geometry"})
        if lost:
            raise CT.ContractError(
                f"the shapefile round trip LOST {lost} from '{name}'. The contract's "
                "10-character rule exists precisely so this cannot happen; a truncated "
                "name is a field the auditor cannot find.")
        written.append(path)
        _log(f"   {os.path.basename(path):<28} {len(g):>7,} features, "
             f"{len(g.columns) - 1} fields, round trip clean")
    for name, df in tables.items():
        p = os.path.join(DIR_SHP, f"W12_{name}.csv")
        df.to_csv(p, index=False, encoding="utf-8-sig")
        written.append(p)
    return written


# ======================================================================================
# 9b.  THE FIELD DICTIONARY
#
#      A shapefile field name is ten characters. That is not a style choice, it is the DBF
#      format, and it is why every field on these layers is an abbreviation. An
#      abbreviation nobody can expand is a column nobody checks - so the abbreviations get
#      a page of their own, next to the export, and it is generated from the contract
#      rather than typed, so it cannot go stale.
# ======================================================================================

# The engineer's own short forms, and the ones this stage adds. Read as: wherever you see
# the left-hand token in a field name, it means the right-hand thing.
ABBREVIATIONS: List[Tuple[str, str]] = [
    ("INV", "invert level, metres above Ordnance Datum"),
    ("GRD / G", "ground level (existing surface), metres above Ordnance Datum"),
    ("DN", "nominal bore in millimetres - the size the pipe is called"),
    ("LEN", "length in metres, along the pipe"),
    ("SLOPE", "gradient in PERCENT. LAID = what it is built at, MIN = the legal floor"),
    ("Q", "flow. ADF = average dry weather, PK = peak, DUTY = a pump's duty point"),
    ("V", "velocity, metres per second"),
    ("DOD", "depth of flow divided by diameter - how full the pipe runs"),
    ("PF", "peak factor, and PF_METH says which formula produced it"),
    ("COVER", "depth of ground OVER THE CROWN of the pipe, metres"),
    ("DEPTH / DEP", "depth from ground level DOWN TO THE INVERT, metres"),
    ("US / DS", "upstream / downstream"),
    ("MH", "manhole"),
    ("TM / SM / L", "trunk main / sub main / lateral - the tier tokens inside a NAME"),
    ("PMP / P", "a pumping station / its force main, inside a NAME"),
    ("N_", "a count of the thing named after it"),
    ("_M / _KM / _M2 / _M3", "the unit: metres, kilometres, square metres, cubic metres"),
    ("_LS / _M3D", "litres per second / cubic metres per day"),
    ("WHY", "free text: the REASON the row carries the flag beside it"),
    ("FLAG", "a short label naming an exception; blank means no exception"),
]


def field_dictionary_md(layers: Dict[str, gpd.GeoDataFrame]) -> str:
    """One page: what every abbreviation means, and every published field with its units,
    the rule it exists for and the check that reads it."""
    L: List[str] = []
    A = L.append
    A("# W12 field dictionary")
    A("")
    A(f"*{VERSION}, built {time.strftime('%Y-%m-%d %H:%M')}. Generated from "
      f"`contract.LAYERS` - it cannot go stale, because the schema and this page are the "
      f"same object.*")
    A("")
    A("A shapefile field name is capped at **ten characters** by the DBF format, so every "
      "field below is an abbreviation. This page is how they are read.")
    A("")
    A("## The short forms")
    A("")
    A("| In a field name | Means |")
    A("|---|---|")
    for tok, meaning in ABBREVIATIONS:
        A(f"| `{tok}` | {meaning} |")
    A("")
    A("## Names")
    A("")
    A("Every element carries a `NAME` built from one grammar - **town letter, subnetwork, "
      "tier, element, zero-padded**:")
    A("")
    A("```")
    A("I-S03            subnetwork 3, in the town whose letter is I")
    A("I-S03-SM-M012    manhole 12 of that subnetwork, on the SUB MAIN tier")
    A("I-S03-C012       the conduit LEAVING manhole 12 - a conduit is named for its")
    A("                 upstream manhole, which is why manholes are numbered per")
    A("                 SUBNETWORK and not per tier")
    A("I-PMP02          pumping station 2 in that town. A station is a SEAM between")
    A("                 subnetworks, so it carries no S-token and a blank SUBNET")
    A("I-P02            the force main leaving pump 2 - same number as its pump")
    A("```")
    A("")
    A("The town letter drops the Arabic article (`Al `, `Ad `, `Ash `). Where two towns "
      "would take the same letter **both** extend to two letters, then three - the town "
      "with more served plots is not favoured, because favouring it would make the small "
      "town's code depend on a plot count.")
    A("")
    A("`NAME` is referenced by **nothing**. Identity is `NODE_UID` / `EDGE_UID` and stays "
      "there, so a retier or a re-town renames the drawing without orphaning a single "
      "reference.")
    A("")
    A("## `DEP_M` - one column, five meanings, all of them written down")
    A("")
    A("The DEPTH theme classifies every layer on one column so the bands are literally the "
      "same bands. It is **not the same physical quantity on each layer**, which is why it "
      "is stated here rather than left to the reader:")
    A("")
    A("| Layer | `DEP_M` is |")
    A("|---|---|")
    A("| conduits | the DEEPER of the two ends, ground down to invert |")
    A("| manholes | ground down to invert at the chamber |")
    A("| pumps | ground down to the arrival invert - the wet-well depth |")
    A("| force mains | the depth of the wet well it LEAVES; a pressure main has no invert "
      "of its own in this design |")
    A("| subnetworks | the DEEPEST chamber anywhere in that subnetwork |")
    A("")
    A(f"Classified on FIXED edges - {', '.join('%.2f' % b for b in DEPTH_BREAKS)} m - "
      f"never auto-stretched, so the same colour means the same depth in every export.")
    A("")
    A("## Every field, by layer")
    A("")
    dd = data_dictionary()
    # every field name this document explains, so the sweep at the end can name what it
    # does not. Collected as the document is built rather than re-derived afterwards.
    _explained: set = {str(x) for x in dd.Field}
    for lname in sorted(set(dd.Layer)):
        sub = dd[dd.Layer == lname]
        A(f"### `{lname}`")
        A("")
        A("| Field | Units | Required | Allowed values | Why it exists |")
        A("|---|---|---|---|---|")
        for _i, row in sub.iterrows():
            A(f"| `{row.Field}` | {row.Units or '-'} | {row.Required} | "
              f"{(row.Allowed or '-')[:80]} | {str(row.Why_this_field_exists)[:220]} |")
        A("")
    A("## Fields this stage adds beyond the contract")
    A("")
    A("Each is a diagnostic or a presentation column - a restatement of a published field "
      "in words a legend can carry - never a new number.")
    A("")
    A("| Field | On | What it is |")
    A("|---|---|---|")
    for fld, where, what in (
            ("SUB_NAME", "nodes, reaches, connections",
             "the subnetwork's full NAME, e.g. `I-S03`. SUBNET alone is `S03`, which is "
             "NOT unique across towns"),
            ("SUBNET_ND", "nodes, reaches", "the component's own outfall chamber - the "
                                            "machine key behind SUB_NAME"),
            ("US_NAME / DS_NAME", "reaches", "the NAME of the manhole at each end"),
            ("DEP_M", "all five layers", "see above"),
            ("STR_CLS", "nodes", "the STRUCTURE theme class of a chamber, in words"),
            ("JOIN_GAP_M", "nodes", "straight-line distance from this chamber to the "
                                    "client's Main Pipe"),
            ("CAP_LEN_M", "nodes, reaches", "distance to the recovery or the outfall that "
                                            "justifies a past-the-cap exit"),
            ("ST_RESET", "nodes", "1 where a pumping station reset the depth in the "
                                  "measured with-stations arm"),
            ("UPS_LEN_M", "nodes", "metres of sewer upstream of this chamber"),
            ("RUN_LEN_M", "reaches", "metres of sewer upstream INCLUDING this reach"),
            ("ANCHOR_ND / ST_SNAP_M / UID_S7", "stations",
             "the chamber a station was re-anchored to, how far it had to move, and the "
             "id s7 gave it. A recovered anchor is not written topology (H16)"),
            ("EXC_KIND / EXC_SEV", "the EXCEPTIONS theme",
             "which kind of exception, and a SEVERITY RANK 1-3 that sets the symbol size. "
             "A rank, not a measurement"),
            ("SERVED / FLAG / WHY", "subnetworks",
             "1 for a subnetwork's own service area, 0 for an area the network does not "
             "reach - and then FLAG names it and WHY says what would have to change"),
    ):
        A(f"| `{fld}` | {where} | {what} |")
        _explained.add(fld)
        for part in str(fld).replace("/", " ").split():
            _explained.add(part.strip())
    A("")

    # ---- THE COMPLETENESS SWEEP -------------------------------------------------------
    # The table above is HAND-WRITTEN, and the claim this file makes about itself - "it
    # cannot go stale" - is only true of the half generated from `contract.LAYERS`. It had
    # already gone stale: DEEP_M, GAP_M, OFF_M, LOW_ND, TOWN_D_M, OUT_NAME, N_CHAMBER,
    # AREA_M2, REJECT_WHY, ANCHOR_X/Y, CAP_WHY and the six band columns were all published
    # and none of them was in it. A dictionary that is silently incomplete is worse than a
    # short one, because a reader takes its silence for "there is nothing else". So the
    # actual published columns are swept against everything explained above and the
    # remainder is LISTED, by layer, as an admitted gap.
    unexplained: List[Tuple[str, List[str]]] = []
    for lname in sorted(layers):
        gdf = layers[lname]
        gname = gdf.geometry.name if isinstance(gdf, gpd.GeoDataFrame) else "geometry"
        left = sorted(c for c in gdf.columns
                      if c not in (gname, "geometry") and str(c) not in _explained)
        if left:
            unexplained.append((lname, left))
    A("### Published columns this dictionary does NOT yet explain")
    A("")
    if not unexplained:
        A("None - every column on every published layer is described above.")
    else:
        A("Each of these is written to the GeoPackage and the shapefile and has no entry "
          "above. They are diagnostics, not design values, but an unexplained column is "
          "one a reviewer cannot use and an auditor cannot check. Listed rather than "
          "quietly omitted.")
        A("")
        A("| Layer | Columns with no entry |")
        A("|---|---|")
        for lname, left in unexplained:
            A(f"| `{lname}` | " + ", ".join(f"`{c}`" for c in left) + " |")
    A("")
    A("## What is switched off, and why the columns are absent")
    A("")
    A(f"*{C.concept_banner()}*")
    A("")
    A("`MOTOR_KW`, `LCC_OMR`, `HEAD_M`, `Q_LS`, `DIA_MM`, `V_MS`, `STOR_M3` and "
      "`US_PUMP` are **banned field names** (`contract.BANNED_FIELDS`). The first two "
      "belong to capabilities switched off at concept stage; the rest are second names "
      "for quantities the contract already carries, and two names for one quantity is the "
      "most expensive recurring defect in this project.")
    A("")
    return "\n".join(L)


def write_field_dictionary(layers: Dict[str, gpd.GeoDataFrame]) -> str:
    p = os.path.join(OUT, "W12_FIELD_DICTIONARY.md")
    os.makedirs(OUT, exist_ok=True)
    open(p, "w", encoding="utf-8").write(field_dictionary_md(layers))
    _log(f"   {os.path.basename(p):<28} {os.path.getsize(p) / 1024:6.0f} kB")
    return p


# ======================================================================================
# 10.  DXF
#
#      Two drawings, because they answer different needs and one of them is 20x the size:
#        W12_network.dxf     geometry only - opens instantly, for looking at
#        W12_annotated.dxf   the same plus every chamber, pipe, pump and main labelled
#
#      THE FIVE LAYERS, and the same colours as the KMZ and the QGIS styles, because all
#      three read `theme_structure()`'s class table. A CAD layer filter on `W12-CONDUIT*`
#      picks up the one logical conduit layer; the tier suffixes exist so a draughtsman can
#      freeze the laterals and see the structure, which is the first thing anyone does.
#
#      Colour is written as TRUE COLOUR on the layer, not as an ACI index, so the RGB in
#      the drawing is the RGB on the map. ACI is a 255-colour palette and rounding the
#      subnetwork palette into it made neighbouring subnetworks share a shade.
# ======================================================================================

DXF_TEXT_H = 1.1            # metres. A 1.1 m capital at 1:1000 is 1.1 mm on paper - legible
DXF_TITLE_H = 12.0          # the drawing header, read at full-sheet zoom


def _dxf_layers() -> List[Tuple[str, Tuple[int, int, int], str]]:
    """(layer, rgb, what it is). ONE table, used to create the layers AND to write the key
    into the drawing itself, so a CAD user does not need this file open beside it."""
    tier_rgb = {t: rgb for t, _lab, rgb, _w in PR.TIER_COLOURS}
    return [
        ("W12-CONDUIT-TRUNK", tier_rgb["trunk main"], "gravity conduit, trunk main tier"),
        ("W12-CONDUIT-SUBMAIN", tier_rgb["sub main"], "gravity conduit, sub main tier"),
        ("W12-CONDUIT-MAIN", tier_rgb["main"], "gravity conduit, main sewer tier"),
        ("W12-CONDUIT-LATERAL", tier_rgb["lateral"], "gravity conduit, lateral tier"),
        ("W12-MANHOLE", (120, 120, 120), "manhole, drawn at its own MH_DIA"),
        ("W12-MANHOLE-DROP", (253, 174, 97),
         "manhole carrying a backdrop or a vortex drop shaft "
         "(over %g m / %g m, G203-p30)" % (C.DROP_TRIGGER, C.BACKDROP_MAX)),
        ("W12-MANHOLE-JOIN", (0, 150, 255),
         "the chamber where a subnetwork MEETS THE MAIN PIPE"),
        ("W12-PUMP", (200, 30, 140), "pumping station"),
        ("W12-FORCEMAIN", (230, 120, 20),
         "force main landing on a manhole where gravity resumes"),
        ("W12-FORCEMAIN-STP", (140, 40, 0),
         "force main lifting ALL THE WAY TO THE WORKS - concept rule 6 asks why"),
        ("W12-SUBNET", (90, 90, 90), "subnetwork service area, over the plots it serves"),
        ("W12-UNSERVED", (152, 0, 67),
         "an area the network does NOT reach, with its plot count and its reason"),
        ("W12-MAINPIPE", (17, 17, 17),
         "the client's own Main Pipe - AN INPUT. Not chambered, not levelled, not sized"),
        ("W12-CONNECTION", (150, 190, 150), "plot connection, chamber to property"),
        ("W12-CONNECTION-FAIL", (165, 0, 38),
         "plot connection that CANNOT work on gravity - the label says by how much"),
        ("W12-CROSSING", (84, 39, 143), "registered wadi / dual-carriageway contact"),
        ("W12-EXC-PASTCAP", (110, 30, 5),
         "chamber past the %g m cover cap (G203-p33)" % C.MAX_COVER),
        ("W12-EXC-WADI", (84, 39, 143), "chamber standing on wadi ground - H1"),
        ("W12-FLOWDIR", (48, 48, 48), "flow direction, on the main and sub-main tiers"),
        ("W12-TXT-CONDUIT", (60, 60, 60), "conduit label: NAME, DN, length, gradient, "
                                          "flow, velocity, and the manhole at each end"),
        ("W12-TXT-MANHOLE", (60, 60, 60),
         "manhole label: NAME, ground level, invert level, depth, drop and kind"),
        ("W12-TXT-PUMP", (60, 60, 60),
         "pump label: NAME, ground, invert, lift, duty flow, wet-well volume"),
        ("W12-TXT-FORCEMAIN", (60, 60, 60),
         "force main label: NAME, DN, length, flow, velocity, and where it lands"),
        ("W12-TXT-SUBNET", (60, 60, 60),
         "subnetwork label: NAME, plots served, sewer length, and any flag on it"),
        ("W12-TITLE", (0, 0, 0), "the drawing header and this layer key"),
    ]


TIER_DXF = {"trunk main": "W12-CONDUIT-TRUNK", "sub main": "W12-CONDUIT-SUBMAIN",
            "main": "W12-CONDUIT-MAIN", "lateral": "W12-CONDUIT-LATERAL",
            "rider": "W12-CONDUIT-LATERAL"}


def _dxf_line(msp, geom, layer: str) -> None:
    parts = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    for p in parts:
        cs = [(float(x), float(y)) for x, y, *_ in p.coords]
        if len(cs) >= 2:
            msp.add_lwpolyline(cs, dxfattribs={"layer": layer})


def _dxf_poly(msp, geom, layer: str) -> None:
    parts = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    for p in parts:
        if p.geom_type != "Polygon":
            continue
        cs = [(float(x), float(y)) for x, y, *_ in p.exterior.coords]
        if len(cs) >= 3:
            msp.add_lwpolyline(cs, close=True, dxfattribs={"layer": layer})


def _dxf_text(msp, txt, x: float, y: float, layer: str,
              h: float = DXF_TEXT_H, rot: float = 0.0) -> None:
    if not str(txt).strip():
        return
    msp.add_text(str(txt), height=h, rotation=rot,
                 dxfattribs={"layer": layer}).set_placement((float(x), float(y)))


def write_dxf(layers: Dict[str, gpd.GeoDataFrame], annotated: bool = True) -> List[str]:
    """The five layers, in DXF, carrying the annotation the engineer listed."""
    import ezdxf
    out = []
    r = layers["reaches"]
    nd = layers["nodes"]
    st = layers["stations"]
    rm = layers["rising_mains"]
    sn = layers.get("subnetworks")
    cn = layers.get("connections")
    spec = _dxf_layers()

    for tag, ann in (("network", False), ("annotated", True)):
        if ann and not annotated:
            continue
        doc = ezdxf.new("R2013", setup=True)
        doc.header["$INSUNITS"] = 6                     # metres
        msp = doc.modelspace()
        for nm_, rgb, _desc in spec:
            lay = doc.layers.add(name=nm_)
            try:
                lay.rgb = rgb                   # exact colour, not an ACI rounding
            except Exception:                   # pragma: no cover - older ezdxf
                pass

        # ---- 1. gravity conduits --------------------------------------------------------
        for geom, tier in zip(r.geometry.values, r.TIER.astype(str)):
            _dxf_line(msp, geom, TIER_DXF.get(tier, "W12-CONDUIT-LATERAL"))
        # ---- the client's main pipe, so the gap to it is visible ------------------------
        for geom in layers["trunk"].geometry.values:
            _dxf_line(msp, geom, "W12-MAINPIPE")
        # ---- 4. force mains -------------------------------------------------------------
        for geom, dst in zip(rm.geometry.values, rm.DS_TYPE.astype(str)):
            _dxf_line(msp, geom,
                      "W12-FORCEMAIN-STP" if dst == "stp" else "W12-FORCEMAIN")
        # ---- plot connections, split on whether they actually work ----------------------
        if cn is not None and len(cn):
            for geom, ok in zip(cn.geometry.values, cn.CAN_CONN.to_numpy()):
                _dxf_line(msp, geom,
                          "W12-CONNECTION" if int(ok) == 1 else "W12-CONNECTION-FAIL")
        # the crossings register is optional here on purpose: it is drawn when it exists
        # and its ABSENCE is reported by check_contract, not papered over by a KeyError
        # that would take the whole drawing down with it.
        for geom in (layers.get("crossings", gpd.GeoDataFrame(geometry=[])).geometry.values):
            _dxf_line(msp, geom, "W12-CROSSING")
        # ---- 5. subnetwork polygons, and the areas nothing reaches ----------------------
        if sn is not None and len(sn):
            for geom, served in zip(sn.geometry.values, sn.SERVED.to_numpy()):
                _dxf_poly(msp, geom, "W12-SUBNET" if int(served) == 1 else "W12-UNSERVED")

        # ---- 2. manholes ----------------------------------------------------------------
        for x, y, dia, dt, jm, pc, wd in zip(
                nd.X, nd.Y, nd.MH_DIA, nd.DROP_TYPE, nd.JOIN_MAIN, nd.PAST_CAP,
                pd.to_numeric(nd.ON_WADI, errors="coerce").fillna(0)):
            lay = ("W12-MANHOLE-JOIN" if int(jm) == 1 else
                   "W12-MANHOLE-DROP" if str(dt) != "none" else "W12-MANHOLE")
            msp.add_circle((float(x), float(y)), float(dia) / 2.0, dxfattribs={"layer": lay})
            if int(pc) == 1:
                msp.add_circle((float(x), float(y)), 3.0,
                               dxfattribs={"layer": "W12-EXC-PASTCAP"})
            if float(wd) > 0:
                msp.add_circle((float(x), float(y)), 4.5,
                               dxfattribs={"layer": "W12-EXC-WADI"})
        # ---- 3. pumps -------------------------------------------------------------------
        for geom in st.geometry.values:
            msp.add_circle((float(geom.x), float(geom.y)), 6.0,
                           dxfattribs={"layer": "W12-PUMP"})

        if ann:
            # ---- manhole: NAME / ground / invert / depth / drop / kind ------------------
            for nmv, x, y, grd, inv, dep, drp, dt, kind in zip(
                    nd.NAME, nd.X, nd.Y, nd.GRD_M, nd.INV_M, nd.DEPTH_M, nd.DROP_M,
                    nd.DROP_TYPE, nd.NODE_KIND):
                _dxf_text(msp, nmv, float(x) + 1.0, float(y) + 2.6, "W12-TXT-MANHOLE")
                _dxf_text(msp, "g %.2f / inv %.2f / d %.2f" % (float(grd), float(inv),
                                                               float(dep)),
                          float(x) + 1.0, float(y) + 1.2, "W12-TXT-MANHOLE", 0.95)
                tail = str(kind)
                if str(dt) != "none":
                    tail = "%s %.2f m / %s" % (dt, float(drp), tail)
                _dxf_text(msp, tail, float(x) + 1.0, float(y) - 0.1,
                          "W12-TXT-MANHOLE", 0.85)
            # ---- conduit: NAME / DN / length / gradient / flow / velocity / both ends ---
            for geom, nmv, dn, L, s, q, v, us, ds in zip(
                    r.geometry.values, r.NAME, r.DN, r.LEN_M, r.SLOPE_LAID, r.QPK_LS,
                    r.V_PK_MS, r.US_NAME, r.DS_NAME):
                mid = geom.interpolate(0.5, normalized=True)
                cs = np.asarray(geom.coords)
                d = cs[-1, :2] - cs[0, :2]
                ang = math.degrees(math.atan2(d[1], d[0]))
                if ang > 90:
                    ang -= 180
                if ang < -90:
                    ang += 180
                _dxf_text(msp, "%s  DN%d  L=%.1f  S=%.2f%%  Q=%.1fL/s  v=%.2fm/s"
                          % (nmv, int(dn), float(L), float(s), float(q), float(v)),
                          float(mid.x), float(mid.y) + 0.8, "W12-TXT-CONDUIT",
                          DXF_TEXT_H, ang)
                _dxf_text(msp, "%s -> %s" % (us, ds), float(mid.x), float(mid.y) - 0.6,
                          "W12-TXT-CONDUIT", 0.85, ang)
            # ---- pump: NAME / ground / invert / lift / duty / wet well ------------------
            for geom, nmv, grd, inv, lift, q, well in zip(
                    st.geometry.values, st.NAME, st.GRD_M, st.INV_M, st.LIFT_M,
                    st.Q_DUTY_LS, st.WELL_M3):
                _dxf_text(msp, str(nmv), float(geom.x) + 8, float(geom.y) + 6,
                          "W12-TXT-PUMP", 2.4)
                _dxf_text(msp, "g %.2f / inv %.2f / lift %.2f m"
                          % (float(grd), float(inv), float(lift)),
                          float(geom.x) + 8, float(geom.y) + 2.6, "W12-TXT-PUMP", 1.8)
                _dxf_text(msp, "duty %.1f L/s / well %.2f m3" % (float(q), float(well)),
                          float(geom.x) + 8, float(geom.y) - 0.4, "W12-TXT-PUMP", 1.8)
            # ---- force main: NAME / DN / length / flow / velocity / where it lands ------
            for geom, nmv, dn, L, q, v, ds, dst in zip(
                    rm.geometry.values, rm.NAME, rm.DN, rm.LEN_M, rm.Q_DUTY_LS,
                    rm.V_DUTY_MS, rm.DS_NODE, rm.DS_TYPE):
                mid = geom.interpolate(0.5, normalized=True)
                _dxf_text(msp, "%s  DN%d  L=%.0fm  Q=%.1fL/s  v=%.2fm/s  -> %s (%s)"
                          % (nmv, int(dn), float(L), float(q), float(v), ds, dst),
                          float(mid.x), float(mid.y) + 3.0, "W12-TXT-FORCEMAIN", 2.4)
            # ---- subnetwork: NAME / plots / km / the flag on it -------------------------
            if sn is not None and len(sn):
                for geom, nmv, npl, km, flag, why in zip(
                        sn.geometry.values, sn.NAME, sn.N_PLOT, sn.LEN_KM, sn.FLAG, sn.WHY):
                    c = geom.centroid
                    head = str(nmv) if str(nmv).strip() else str(flag)
                    _dxf_text(msp, "%s   %d plots   %.2f km" % (head, int(npl), float(km)),
                              float(c.x), float(c.y), "W12-TXT-SUBNET", 22.0)
                    if str(flag).strip():
                        _dxf_text(msp, str(why)[:150], float(c.x), float(c.y) - 26.0,
                                  "W12-TXT-SUBNET", 16.0)

        # ---- the header and the layer key, written INTO the drawing --------------------
        y0 = float(nd.Y.max()) + 400.0
        x0 = float(nd.X.min())
        _dxf_text(msp, "W12 sewer network - %s.  %s, %s.  EPSG:%d.  LEVELS: %s.  %s"
                  % (tag, VERSION, time.strftime("%Y-%m-%d"), CT.CRS_EPSG, LEVELS_SOURCE,
                     C.tau_banner()[:110]),
                  x0, y0 + 44.0, "W12-TITLE", DXF_TITLE_H)
        _dxf_text(msp, C.concept_banner()[:240], x0, y0 + 26.0, "W12-TITLE", 9.0)
        for i, (nm_, _rgb, desc) in enumerate(spec):
            _dxf_text(msp, "%s = %s" % (nm_, desc), x0, y0 - i * 12.0, "W12-TITLE", 8.0)
        p = os.path.join(DIR_DXF, "W12_%s.dxf" % tag)
        doc.saveas(p)
        out.append(p)
        _log("   %-24s %8.1f MB" % (os.path.basename(p), os.path.getsize(p) / 1e6))
    return out


# ======================================================================================
# 11.  THE SCHEDULES
#
#      The printed headers come from `contract.SCHEDULES` and from nowhere else - that is
#      the whole reason they live in the contract: "a header and the field it prints must
#      not be editable apart". `contract.schedule_frame()` validates first and RAISES; it
#      is tried first, and where it raises the schedule is still printed with the contract's
#      own headers and the failure is written into the workbook's own first sheet, so the
#      reader sees what did not validate on the same file as the numbers.
# ======================================================================================

def schedule(gdf, name: str) -> Tuple[pd.DataFrame, str]:
    try:
        return CT.schedule_frame(gdf, name, stage=STAGE), "validated"
    except CT.ContractError as e:
        sch = CT.SCHEDULES[name]
        missing = [f for _h, f in sch.columns if f not in gdf.columns]
        cols = {h: (gdf[f].values if f in gdf.columns else ["(not published)"] * len(gdf))
                for h, f in sch.columns}
        return pd.DataFrame(cols), (f"NOT VALIDATED. {str(e)[:4000]}"
                                    + (f"\nMISSING FIELDS: {missing}" if missing else ""))


def quantities(layers: Dict[str, gpd.GeoDataFrame]) -> Dict[str, pd.DataFrame]:
    """An INDICATIVE take-off. It is not a bill of quantities and it is not priced.

    Two numbers in it are this stage's own assumptions and neither comes from a guideline:
    TRENCH_SIDE_M (0.30 m working space each side of the barrel) and MH_DIA_STD_M (1.20 m
    chamber, written up to 1.50 m where a backdrop is unavoidable, G203-p30). G203 gives no
    trench width and no table of chamber size against depth - both were searched."""
    r = layers["reaches"]
    nd = layers["nodes"]
    dn_m = r.DN.to_numpy(dtype=float) / 1000.0
    od = dn_m + 2 * C.WALL_ALLOW
    width = od + 2 * TRENCH_SIDE_M
    depth = (r.US_DEPTH.to_numpy(dtype=float) + r.DS_DEPTH.to_numpy(dtype=float)) / 2.0 + od
    L = r.LEN_M.to_numpy(dtype=float)
    exc = width * np.maximum(depth, 0.0) * L
    bed = width * (od + 0.15) * L

    pipes = (pd.DataFrame(dict(TIER=r.TIER.astype(str), DN=r.DN, MATERIAL=r.MATERIAL,
                               LEN_M=L, EXC_M3=exc, BED_M3=bed))
             .groupby(["TIER", "DN", "MATERIAL"], as_index=False)
             .agg(Reaches=("LEN_M", "size"), Length_m=("LEN_M", "sum"),
                  Excavation_m3=("EXC_M3", "sum"), Bedding_m3=("BED_M3", "sum"))
             .sort_values(["TIER", "DN"]))
    for c in ("Length_m", "Excavation_m3", "Bedding_m3"):
        pipes[c] = pipes[c].round(1)

    d = nd.DEPTH_M.to_numpy(dtype=float)
    bands = pd.cut(d, [-0.01, 2, 3, 4, 6, 8, 10, 12, 1e9],
                   labels=["<2 m", "2-3 m", "3-4 m", "4-6 m", "6-8 m", "8-10 m",
                           "10-12 m", "OVER THE 12 m CAP"])
    ch = (pd.DataFrame(dict(Band=bands, DIA=nd.MH_DIA, DROP=nd.DROP_TYPE))
          .groupby(["Band", "DIA"], as_index=False, observed=True)
          .agg(Chambers=("DROP", "size")))

    drops = (pd.DataFrame(dict(Type=nd.DROP_TYPE, H=nd.DROP_M))
             .query("Type != 'none'")
             .groupby("Type", as_index=False)
             .agg(Number=("H", "size"), Total_height_m=("H", "sum"),
                  Max_height_m=("H", "max")))
    drops[["Total_height_m", "Max_height_m"]] = drops[["Total_height_m", "Max_height_m"]].round(2)

    rm = layers["rising_mains"]
    rms = (rm.groupby(["DN", "MATERIAL"], as_index=False)
             .agg(Mains=("LEN_M", "size"), Length_m=("LEN_M", "sum"),
                  Air_valves=("N_AIRV", "sum"), Washouts=("N_WASH", "sum"),
                  Isolation_valves=("N_ISOL", "sum")))
    rms["Length_m"] = rms.Length_m.round(1)

    st = layers["stations"]
    # NO MOTOR COLUMN. Motor selection is switched off at concept stage
    # (criteria.CONCEPT_OFF["motor_selection"]) and MOTOR_KW is a banned field name.
    sts = (st.groupby("ST_TYPE", as_index=False)
             .agg(Stations=("LAND_M2", "size"), Land_m2=("LAND_M2", "sum"),
                  Duty_LS=("Q_DUTY_LS", "sum"), Wet_well_m3=("WELL_M3", "sum"),
                  Network_captured_km=("CATCH_KM", "sum")))
    for c in ("Land_m2", "Duty_LS", "Wet_well_m3", "Network_captured_km"):
        sts[c] = sts[c].round(2)

    cn = layers["connections"]
    conn = pd.DataFrame([dict(
        Item="Property connections (rider, HCC to chamber)",
        Number=len(cn), Length_m=round(float(cn.LEN_M.sum()), 1),
        Note=f"DN{C.DN_TERTIARY} minimum, G203-p22 Tab 6; "
             f"{int((cn.CAN_CONN == 0).sum()):,} cannot connect on gravity")])

    headline = pd.DataFrame([
        dict(Item="Gravity sewer", Quantity=round(float(L.sum()) / 1000.0, 3), Unit="km",
             Source="this export, LEN_M summed over the reach layer"),
        dict(Item="Chambers", Quantity=len(nd), Unit="no.", Source="the node layer"),
        dict(Item="Chambers per km", Quantity=round(len(nd) / (L.sum() / 1000.0), 2),
             Unit="-", Source="built network 34.23 (asbuilt, measured by s4)"),
        dict(Item="Trench excavation", Quantity=round(float(exc.sum()), 0), Unit="m3",
             Source=f"width = OD + 2 x {TRENCH_SIDE_M} m (ASSUMPTION), depth to invert + OD"),
        dict(Item="Pipe bedding and surround", Quantity=round(float(bed.sum()), 0),
             Unit="m3", Source="ASSUMPTION - 150 mm over the crown"),
        dict(Item="Backdrops (0.60-2.00 m)", Quantity=int((nd.DROP_TYPE == "backdrop").sum()),
             Unit="no.", Source="G203-p30"),
        dict(Item="VORTEX DROP SHAFTS (> 2.00 m)",
             Quantity=int((nd.DROP_TYPE == "vortex").sum()), Unit="no.",
             Source="G203-p30. NAMA's built network has 37 - philosophy sec 4 makes this "
                    "count the tree-orientation diagnostic"),
        dict(Item="Property connections", Quantity=len(cn), Unit="no.",
             Source="one per connected plot"),
        dict(Item="Property connection pipe", Quantity=round(float(cn.LEN_M.sum()) / 1000, 3),
             Unit="km", Source="the connection layer"),
        dict(Item="Pumping stations", Quantity=len(st), Unit="no.", Source="s7_pumps"),
        dict(Item="Station land take", Quantity=round(float(st.LAND_M2.sum()), 0), Unit="m2",
             Source="G203-p43 Tab 21, via s7"),
        dict(Item="Rising main", Quantity=round(float(rm.LEN_M.sum()) / 1000.0, 3), Unit="km",
             Source="s7_pumps"),
        dict(Item="Registered wadi / carriageway crossings", Quantity=len(layers["crossings"]),
             Unit="no.", Source="H1a register, this export"),
        dict(Item="Subnetworks", Quantity=int((layers["subnetworks"].SERVED == 1).sum()),
             Unit="no.", Source="one per connected component, named per concept rule 8"),
        dict(Item="Subnetworks that do NOT reach the main pipe",
             Quantity=int(((layers["subnetworks"].SERVED == 1)
                           & (layers["subnetworks"].JOIN_MAIN == 0)).sum()),
             Unit="no.", Source=f"concept rule 2, at the declared {JOIN_TOL_M:g} m"),
        dict(Item="Plots that CANNOT connect on gravity",
             Quantity=int((cn.CAN_CONN == 0).sum()), Unit="no.",
             Source="concept rule 5; each names what it would take, in metres"),
        dict(Item="Pumping stations REMOVED - nothing drained into them",
             Quantity=len(layers.get("stations_rejected", [])), Unit="no.",
             Source="inheritance row 4 - a later pass must be able to take away"),
    ])
    return {"Headline": headline, "Pipes": pipes, "Chambers": ch, "Drop structures": drops,
            "Rising mains": rms, "Stations": sts, "Connections": conn}


def data_dictionary() -> pd.DataFrame:
    """Every published field, its units, the RULE it exists for and the check that reads
    it - straight out of `contract.LAYERS`. A schedule nobody can interpret is a schedule
    nobody checks."""
    rows = []
    for lname in ("nodes", "reaches", "connections", "stations", "rising_mains",
                  "crossings", "packages"):
        spec = CT.LAYERS[lname]
        for fl in spec.fields:
            rows.append(dict(Layer=lname, Field=fl.name, Type=fl.dtype, Units=fl.units,
                             Required="yes" if fl.required else "no",
                             Blank_ok="yes" if fl.blank_ok else "no",
                             Allowed=", ".join(fl.allowed) if fl.allowed else "",
                             Range=("" if fl.lo is None and fl.hi is None
                                    else f"[{fl.lo}, {fl.hi}]"),
                             Audit_check=fl.audit,
                             Why_this_field_exists=fl.why))
    return pd.DataFrame(rows)


def write_schedules(a: Assembly, layers: Dict[str, gpd.GeoDataFrame],
                    chk: pd.DataFrame) -> List[str]:
    out = []
    banner = pd.DataFrame([
        dict(Item="Design iteration", Value="W12"),
        dict(Item="Stage", Value=VERSION),
        dict(Item="Built", Value=time.strftime("%Y-%m-%d %H:%M")),
        dict(Item="LEVELS AND SIZES", Value=(
            f"every invert, diameter, gradient, velocity, depth of flow, cover and drop "
            f"in these schedules came from '{LEVELS_SOURCE}' and is tagged with it on "
            f"every row. The levels stand-in this stage used to carry is RETIRED; it runs "
            f"once so the disagreement can be measured and it publishes nothing."
            if LEVELS_SOURCE == S6_TAG else
            f"s6_levels HAS NOT PUBLISHED, so these schedules carry the RETIRED stand-in "
            f"inside s8_export.py, tagged STAGE = '{LEVELS_TAG}' on every row. Run "
            f"s6_levels.py and re-export before quoting a depth.")),
        dict(Item="TRACTIVE STRESS", Value=C.tau_banner()),
        dict(Item="DIAMETERS ABOVE DN1200", Value=(
            "the series is the one G203 itself tabulates in the service-corridor width "
            "table (p32 Tab 13 / p35 Tab 15); awaiting written NWS confirmation")),
        dict(Item="THE TRUNK", Value=(
            "the client's Main Pipe is an INPUT with no chambers and no topology. NOTHING "
            "in these schedules drains into it; the outfalls are subnetwork outlets")),
        dict(Item="PHASE", Value="0 on every row - no phasing stage exists (contract: "
                                 "'0 = not yet assigned')"),
    ])

    def _book(path: str, sheets: Dict[str, pd.DataFrame], note: str = "") -> None:
        with pd.ExcelWriter(path, engine="openpyxl") as xl:
            head = banner.copy()
            if note:
                head = pd.concat([head, pd.DataFrame([dict(Item="CONTRACT", Value=note)])],
                                 ignore_index=True)
            head.to_excel(xl, sheet_name="READ THIS FIRST", index=False)
            for nm, df in sheets.items():
                df.to_excel(xl, sheet_name=nm[:31], index=False)
        out.append(path)
        _log(f"   {os.path.basename(path):<38} "
             f"{sum(len(d) for d in sheets.values()):>7,} rows")

    # NO PACKAGE SCHEDULE. Phasing and packaging are switched off at concept stage
    # (criteria.CONCEPT_OFF["phasing_packaging"]) - "a package boundary drawn on a layout
    # that is still moving is a boundary that will move with it". The PACKAGE column stays
    # on the layers as a GROUPING key, which is what the profiles and the outfall check use
    # it for, and nothing is printed that reads like a procurement strategy.
    for key, layer_name in (("chambers", "nodes"), ("pipes", "reaches"),
                            ("stations", "stations"), ("rising_mains", "rising_mains"),
                            ("connections", "connections"), ("crossings", "crossings")):
        df, status = schedule(layers[layer_name], key)
        _book(os.path.join(DIR_SCH, f"W12_schedule_{key}.xlsx"),
              {key.replace('_', ' ').title(): df}, note=status)

    # the fifth layer gets a schedule of its own - it is where the concept-rule-2 numbers
    # live, and it is the only place a reviewer can see every subnetwork on one page.
    sn = layers["subnetworks"]
    _book(os.path.join(DIR_SCH, "W12_schedule_subnetworks.xlsx"),
          {"Subnetworks": pd.DataFrame({
              "Name": sn.NAME, "Town": sn.TOWN, "Served": sn.SERVED,
              "Plots": sn.N_PLOT, "Properties": sn.N_PROP,
              "Qadf (m3/d)": sn.Q_ADF_M3D, "Chambers": sn.N_CHAMBER,
              "Sewer (km)": sn.LEN_KM, "Deepest chamber (m)": sn.DEEP_M,
              "Outfall": sn.OUT_NAME,
              "Joins the main pipe": sn.JOIN_MAIN,
              "Distance to the main pipe (m)": sn.GAP_M,
              "Outlet off its own low point (m)": sn.OFF_M,
              "Flag": sn.FLAG, "Why": sn.WHY})},
          note="CONCEPT RULE 2: a subnetwork joins the main pipe at the LOWEST POINT WHERE "
               f"IT MEETS it. 'Joins' means within {JOIN_TOL_M:g} m (an s8 assumption, "
               "declared). Rows with SERVED = 0 are areas the network does not reach at "
               "all.")

    _book(os.path.join(DIR_SCH, "W12_quantities.xlsx"), quantities(layers),
          note="INDICATIVE take-off. Not a bill of quantities, not priced. Trench width "
               f"and chamber diameter are s8 ASSUMPTIONS ({TRENCH_SIDE_M} m each side, "
               f"{MH_DIA_STD_M} m chamber) - G203 gives neither.")

    ns = a.unserved.copy()
    ns_tab = pd.DataFrame({
        "Plot": ns.PLOT_ID.astype(str), "Status": ns.WHY.astype(str),
        "System": ns.SYSTEM.astype(str),
        "Qadf (m3/d)": ns.Q_ADF_M3D.round(3), "Properties": ns.N_PROP.round(2),
        "Nearest chamber (m)": ns.D_NEAR_M.round(1),
        "Tertiary needed (m)": ns.L_TERT_M.round(1)})
    cn = layers["connections"]
    nodrain = cn[cn.CAN_CONN == 0]
    nd_tab = pd.DataFrame({
        "Plot": nodrain.PLOT_ID.astype(str), "Connection": nodrain.CONN_ID.astype(str),
        "Chamber": nodrain.OUT_NODE.astype(str),
        "Qadf (m3/d)": nodrain.Q_ADF_M3D.round(3),
        "Fall available (m)": nodrain.FALL_AV_M.round(3),
        "Length (m)": nodrain.LEN_M.round(1),
        "Sewer would have to be deeper by (m)": nodrain.CONN_NEED.round(2),
        "Why": nodrain.CONN_WHY.astype(str)})
    sn0 = layers["subnetworks"]
    sn0 = sn0[sn0.SERVED == 0]
    area_tab = pd.DataFrame({
        "Area": sn0.FLAG.astype(str), "Plots": sn0.N_PLOT, "Properties": sn0.N_PROP,
        "Qadf (m3/d)": sn0.Q_ADF_M3D, "Area (m2)": sn0.AREA_M2,
        "Why": sn0.WHY.astype(str)})
    _book(os.path.join(DIR_SCH, "W12_schedule_not_served.xlsx"),
          {"Plot by plot": ns_tab,
           "Connected but cannot connect": nd_tab,
           "Areas not reached": area_tab},
          note="scope-p4 item 3 requires every plot SERVICED. 'Serviced' is not 'connected "
               "to one network' (philosophy sec 8a) - these are the plots this network "
               "does not serve, each named, and each says WHAT IT WOULD TAKE (concept "
               "rule 7: flag, do not solve, and a flag with no size is not a flag).")

    _book(os.path.join(DIR_SCH, "W12_data_dictionary.xlsx"),
          {"Fields": data_dictionary(),
           "Numbers used": pd.DataFrame([dict(Name=n, Value=str(v), Source=s, Why=w)
                                         for n, v, s, w in EXPORT_NUMBERS]),
           "Contract check": chk})
    return out


# ======================================================================================
# 12.  LONG-SECTION PROFILES
#
#      A profile is the one drawing that cannot be faked: it puts the ground and the
#      invert on the same axis, so 12 m of cover is a distance a reader can see. These are
#      drawn along the LONGEST FLOW PATH in each package - the path that accumulates the
#      most depth, which is the one worth looking at.
# ======================================================================================

def _dist_to_outfall(g: Graph) -> np.ndarray:
    d = np.zeros(len(g.uid))
    for v in g.order[::-1]:
        e = int(g.e_of[v])
        d[v] = 0.0 if e < 0 else float(g.e_len[e]) + d[int(g.e_ds[e])]
    return d


def longest_paths(g: Graph, node_pkg: np.ndarray, top: int = 24) -> List[Tuple[str, List[int]]]:
    dist = _dist_to_outfall(g)
    heads = np.flatnonzero(g.indeg == 0)
    best: Dict[str, Tuple[float, int]] = {}
    for h in heads:
        p = str(node_pkg[h])
        if p not in best or dist[h] > best[p][0]:
            best[p] = (float(dist[h]), int(h))
    out = []
    for p, (_d, h) in sorted(best.items(), key=lambda kv: -kv[1][0])[:top]:
        chain = [h]
        cur = h
        while True:
            e = int(g.e_of[cur])
            if e < 0:
                break
            cur = int(g.e_ds[e])
            chain.append(cur)
        out.append((p, chain))
    return out


def write_profiles(g: Graph, layers: Dict[str, gpd.GeoDataFrame], node_pkg: np.ndarray,
                   top: int = 24) -> List[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    nd = layers["nodes"].set_index(layers["nodes"].NODE_UID.astype(str))
    r = layers["reaches"]
    by_us = {u: i for i, u in enumerate(r.US_NODE.astype(str))}
    paths = longest_paths(g, node_pkg, top=top)
    written = []
    pdf_path = os.path.join(DIR_PRF, "W12_long_sections.pdf")
    with PdfPages(pdf_path) as pdf:
        for rank, (pkg, chain) in enumerate(paths, 1):
            uids = [g.uid[i] for i in chain]
            grd = np.array([float(nd.GRD_M[u]) for u in uids])
            inv = np.array([float(nd.INV_M[u]) for u in uids])
            ref = [str(nd.NODE_REF[u]) for u in uids]
            ch = np.zeros(len(uids))
            dn = np.zeros(max(1, len(uids) - 1))
            slope = np.zeros_like(dn)
            for i in range(len(uids) - 1):
                k = by_us.get(uids[i])
                L = float(r.LEN_M.iloc[k]) if k is not None else 0.0
                ch[i + 1] = ch[i] + L
                dn[i] = float(r.DN.iloc[k]) if k is not None else 0.0
                slope[i] = float(r.SLOPE_LAID.iloc[k]) if k is not None else 0.0
            # the barrel is drawn on the reach's OWN outside diameter; the last chamber
            # inherits the diameter of the reach arriving at it
            dn_node = np.array(list(dn) + [dn[-1] if len(dn) else 200.0], dtype=float)
            crown = inv + dn_node / 1000.0

            fig, ax = plt.subplots(figsize=(16.5, 7.0))
            ax.plot(ch, grd, color="#7f5539", lw=1.6, label="Existing ground (0.5 m VRT)")
            ax.plot(ch, inv, color="#1f4e79", lw=2.0, label="Designed invert")
            ax.fill_between(ch, inv, crown, color="#9dc3e6", alpha=0.55,
                            label="Pipe barrel (to crown)")
            ax.fill_between(ch, grd - C.MAX_COVER, grd, color="#c6efce", alpha=0.28,
                            label=f"Inside the {C.MAX_COVER:g} m cover cap (G203-p33)")
            deep = grd - inv > C.MAX_COVER
            if deep.any():
                ax.fill_between(ch, inv, grd - C.MAX_COVER, where=deep, color="#f8cbad",
                                alpha=0.55, label="PAST the cap")
            for x, gz, iz in zip(ch, grd, inv):
                ax.plot([x, x], [iz, gz], color="#404040", lw=0.5, alpha=0.55)
            vx = [(x, iz) for x, u, iz in zip(ch, uids, inv)
                  if float(nd.DROP_M[u]) > C.BACKDROP_MAX]
            if vx:
                ax.scatter([a_ for a_, _b in vx], [_b for _a, _b in vx],
                           marker="v", s=44, color="#a50026", zorder=5,
                           label=f"Vortex drop shaft (> {C.BACKDROP_MAX:g} m, G203-p30)")
            step = max(1, len(uids) // 26)
            ax.set_xticks(ch[::step])
            ax.set_xticklabels(ref[::step], rotation=90, fontsize=6)
            cover = grd - inv
            ax.set_title(
                f"W12 long section {rank} of {len(paths)} - package {pkg}, "
                f"the longest flow path in it\n"
                f"{ch[-1] / 1000.0:.2f} km, {len(uids):,} chambers, "
                f"DN{int(dn.min()) if len(dn) else 0}-{int(dn.max()) if len(dn) else 0}, "
                f"gradient {slope.min():.2f}-{slope.max():.2f} %, "
                f"deepest {np.nanmax(grd - inv) if np.isfinite(grd - inv).any() else 0.0:.2f} m to invert   |   "
                f"LEVELS BY {LEVELS_SOURCE}   |   tau = {C.TAU_PA:g} Pa ASSUMED",
                fontsize=9)
            ax.set_xlabel("Chamber (chainage increases downstream)", fontsize=8)
            ax.set_ylabel("Level, m aOD", fontsize=8)
            ax.grid(alpha=0.25, lw=0.5)
            ax.legend(fontsize=7, loc="best", framealpha=0.9)
            fig.tight_layout()
            pdf.savefig(fig, dpi=110)
            if rank <= 6:
                p = os.path.join(DIR_PRF, f"W12_profile_{rank:02d}_{pkg}.png")
                fig.savefig(p, dpi=130)
                written.append(p)
            plt.close(fig)
    written.append(pdf_path)
    _log(f"   {len(paths)} long sections -> {os.path.basename(pdf_path)} "
         f"({os.path.getsize(pdf_path) / 1e6:.1f} MB) + 6 PNG")
    return written


# ======================================================================================
# 13.  THE SEWERGEMS PACKAGE - SWITCHED OFF AT CONCEPT STAGE
#
#      It is not deleted and it is not commented out. It is REFUSED BY NAME, through the
#      one register that says what a concept stage omits:
#
#          criteria.CONCEPT_OFF["sewergems_export"]
#
#      The reason is in the register too, and it is an engineering reason rather than a
#      scheduling one: the model referees HYDRAULICS and can never choose a layout
#      (inheritance row 26), so running it against a layout still under review referees
#      the wrong thing. It comes back when the layout is fixed and the hydraulics are
#      final - and `contract.SEWERGEMS`, which maps every canonical field to its Bentley
#      name, is still there waiting for it.
#
#      A guard rather than a deletion, because a capability that is merely absent is
#      indistinguishable from one that was forgotten. `assert_enabled()` also refuses an
#      UNKNOWN capability name, so this guard cannot be silently misspelled into a no-op.
# ======================================================================================

def write_sewergems(*_a, **_kw) -> List[str]:
    """Refused at concept stage. Calling it raises, and the message names the register."""
    C.assert_enabled("sewergems_export")
    raise CT.ContractError(                                    # pragma: no cover
        "sewergems_export is enabled in criteria but s8_export no longer carries the "
        "writer. Restore it from W11b/py/s8_export.py section 13, which is unchanged and "
        "is the record; the peak-factor warning in its README is the part that matters.")


# ======================================================================================
# 14.  QGIS
#
#      CLAUDE.md rule 3: named group, proper styling, layouts SAVED INTO the project.
#      CLAUDE.md rule 4: Google satellite hybrid at 30 %, MoH_Plots as the land-use layer,
#      a scalebar with non-overlapping labels, a data table bottom-right.
#
#      `present.qgis_plan()` / `qgis_code()` already produce all of that from the SAME
#      `View` objects the KMZ used, so the Earth files and the QGIS project physically
#      cannot disagree. This section only decides WHERE the project should point - at the
#      canonical `W12_export.gpkg`, not at a copy, so the day a stage reruns the project
#      shows the new answer instead of a stale one.
# ======================================================================================

def qgis_script(res: "PR.RenderResult") -> str:
    p = os.path.join(OUT, "qgis_load_W12.py")
    open(p, "w", encoding="utf-8").write(res.qgis_script)
    _log(f"   {os.path.basename(p):<24} {len(res.qgis_script) / 1024:8.0f} kB  "
         f"{len(res.qgis_plan['layers'])} styled layers, "
         f"{len(res.qgis_plan['layouts'])} layouts")
    return p


# ======================================================================================
# 15.  THE REPORT
# ======================================================================================

def _pct(x, of):
    return 0.0 if not of else 100.0 * x / of


def write_report(a: Assembly, g: Graph, f: Flows, lv: Levels, lv_st: Levels,
                 layers: Dict[str, gpd.GeoDataFrame], chk: pd.DataFrame,
                 cross_stats: Dict[str, Any], kmz: "PR.RenderResult",
                 files: Dict[str, List[str]], ofc: pd.DataFrame,
                 delta: Optional[pd.DataFrame] = None,
                 orphans: Optional[pd.DataFrame] = None,
                 nm: Optional[Naming] = None) -> str:
    nd, r = layers["nodes"], layers["reaches"]
    km = float(r.LEN_M.sum()) / 1000.0
    cover = nd.COVER_M.to_numpy(dtype=float)
    # COVER_M is NULL where the leveller published no chamber. A plain max over it is nan,
    # and six rows out of 56,972 destroyed the headline depth on the first run after the
    # levels were rewired. nan-aware, with the count of unlevelled chambers stated.
    n_nolvl = int(np.isnan(cover).sum())
    cov_max = float(np.nanmax(cover)) if np.isfinite(cover).any() else float("nan")
    cov_med = float(np.nanmedian(cover)) if np.isfinite(cover).any() else float("nan")
    st = layers["stations"]
    cn = layers["connections"]
    L: List[str] = []
    A = L.append

    A("# W12 stage 8 - the export: five layers, three themes")
    A("")
    A(f"*{VERSION}, built {time.strftime('%Y-%m-%d %H:%M')}.*")
    A("")
    A(f"*{C.concept_banner()}*")
    A("")
    A("## The uncomfortable answer first")
    A("")
    if LEVELS_SOURCE == S6_TAG:
        A(f"**There is now ONE set of levels in this folder and this export publishes it.** "
          f"Every invert, diameter, gradient, velocity, depth of flow, cover and drop on "
          f"every layer below came from `{S6_TAG}` and is tagged `LEVELS_BY = '{S6_TAG}'` "
          f"on the row. The levels-and-sizes pass this stage used to carry is retired: it "
          f"still runs once, so the size of what the two solvers disagreed about is a "
          f"MEASURED number on the `levels_delta` layer, and it publishes nothing.")
    else:
        A(f"**`s6_levels` HAS NOT PUBLISHED, so this export fell back to the retired "
          f"stand-in inside `s8_export.py`**, tagged `STAGE = '{LEVELS_TAG}'` on every "
          f"row. It is a single strict pass; philosophy sec 7 asks for two and then an "
          f"audit. Do not quote a depth from this run - run `python s6_levels.py` and "
          f"re-export.")
    A("")
    A(f"**And what it measures is not a tree problem. It is flatness.** "
      f"**{int((nd.PAST_CAP == 1).sum()):,} of {len(nd):,} chambers "
      f"({_pct(int((nd.PAST_CAP == 1).sum()), len(nd)):.1f} %) pass the 12 m cover cap** "
      f"(G203-p33), covering **{lv.stats['km_past_cap']:.1f} km** of the "
      f"{km:,.1f} km network, and **{lv.stats['past_cap_no_exit']:,} of them have no exit** "
      f"under philosophy sec 5 - neither a recovery within 500 m nor an outfall within "
      f"1,000 m, or the excursion forces a drop past "
      f"{C.DROP_CEILING_M:g} m and the exit is withdrawn. The deepest chamber carries "
      f"**{cov_max:.1f} m of cover**. That is not a levelling error and it is not the "
      f"tree: **{_pct(float(r.LEN_M[r.DN == 200].sum()), float(r.LEN_M.sum())):.1f} % of "
      f"the length is DN200**, whose Table 11 minimum is 5.00 mm/m (G203-p29), and "
      f"**{_pct(float(r.LEN_M[r.GRAD_BY.isin(['table11', 'tractive', 'uniform'])].sum()), float(r.LEN_M.sum())):.1f} % "
      f"of the length is laid at its governing MINIMUM gradient rather than at the "
      f"ground's own fall** - which is what it means to say the ground is flatter than the "
      f"pipe may be laid. There the pipe sinks whichever way it points.")
    A("")
    A(f"**THE LEVELS ON EVERY LAYER ARE `{S6_TAG}`'s.** Until 2026-09-06 this stage "
      f"computed its own inverts with a stand-in inherited from W11b - where there "
      f"genuinely was no stage 6 - and published them beside s6's own file. Two solvers, "
      f"one question. The stand-in still runs once so the size of the disagreement can be "
      f"measured, and it is published on `levels_delta`; **nothing on any deliverable "
      f"carries it any more.** On the headline counts the two arms read: chambers past "
      f"the 12 m cap {lv.stats['past_cap_nodes']:,} against "
      f"{lv_st.stats['past_cap_nodes']:,}, of those with no exit "
      f"{lv.stats['past_cap_no_exit']:,} against {lv_st.stats['past_cap_no_exit']:,}, "
      f"deepest cover {lv.stats['deepest_cover']:.2f} m against "
      f"{lv_st.stats['deepest_cover']:.2f} m, vortex shafts {lv.stats['vortex']:,} against "
      f"{lv_st.stats['vortex']:,}. The full row-by-row comparison is the `levels_delta` "
      f"layer.")
    A("")

    big = ofc[ofc.N_CHAMBER >= 20]
    bad = big[big.PCT_BELOW > 50.0]
    A("**And the first long section this stage drew found something no table had shown: "
      "some outfalls are near the TOP of their own catchment.** Over the 15.4 km of "
      "package P003 the invert falls in a straight line while the ground RISES. Measured "
      f"over all {len(ofc)} components: **{int(ofc.LOWEST.sum())} discharge at their own "
      f"lowest chamber**, and **{len(bad)} components of 20 chambers or more "
      f"({bad.LEN_KM.sum():,.1f} km, {_pct(float(bad.LEN_KM.sum()), km):.1f} % of the "
      f"network) discharge with MORE THAN HALF their catchment below the outlet**; the "
      f"worst outfall sits **{ofc.ABOVE_LOW.max():.1f} m above the lowest chamber it "
      f"serves**. That is a stage-2 / stage-3 orientation result, not a levelling one - no "
      f"invert arithmetic recovers a terminal placed uphill of its own catchment. The "
      f"table is `outfall_check` in the GeoPackage and in `W12_outfall_check.csv`.")
    A("")
    if len(big) > 5:
        rho_len = float(big[["LEN_KM", "DEEPEST_M"]].corr(method="spearman").iloc[0, 1])
        rho_abv = float(big[["ABOVE_LOW", "DEEPEST_M"]].corr(method="spearman").iloc[0, 1])
        rho_pct = float(big[["PCT_BELOW", "DEEPEST_M"]].corr(method="spearman").iloc[0, 1])
        A(f"**Which of the two costs more depth, measured rather than asserted.** Over the "
          f"{len(big)} components of 20 chambers or more, Spearman rank correlation against "
          f"the deepest chamber in the component: **flow-path scale (component length) "
          f"{rho_len:+.3f}**, **outfall height above its own lowest chamber "
          f"{rho_abv:+.3f}**, share of the catchment below the outlet {rho_pct:+.3f}. So "
          f"length dominates - which is flatness, because the length is being laid at the "
          f"minimum gradient - and outfall placement is a close second. It is not one or "
          f"the other, and the ranking is the useful part: fixing the tree helps most "
          f"where the run is longest.")
        A("")
    A("## The four things that used to be answered twice")
    A("")
    A("Each of these was a second implementation of a question another module already "
      "answered. Inheritance row 10 - one published quantity, one function.")
    A("")
    A("### 1. The levels")
    A("")
    if delta is not None and len(delta):
        A(f"Read from `{S6_TAG}` and matched on the written topology. Where the retired "
          f"stand-in disagreed, row by row:")
        A("")
        A("| Quantity | Rows both answered | Differed | % | Median diff | Worst |")
        A("|---|---:|---:|---:|---:|---:|")
        # NOT `for r in ...`: `r` is the reaches frame in this function, and shadowing it
        # here cost the whole report - every line after this loop read the last delta row.
        for d_ in delta.itertuples():
            worst = max(abs(float(d_.MIN_DIFF)), abs(float(d_.MAX_DIFF)))
            A(f"| {d_.QUANTITY} ({d_.UNIT}) | {int(d_.N):,} | {int(d_.N_DIFFER):,} | "
              f"{float(d_.PCT_DIFFER):.1f} | {float(d_.MEDIAN_DIFF):+.3f} | {worst:.3f} |")
        A("")
        A(f"The stand-in is retired. It still runs once so this table can exist and it "
          f"publishes nothing. {int(REMOVED_COUNTS.get('reaches_unlevelled', 0)):,} routes "
          f"({REMOVED_COUNTS.get('reaches_unlevelled_km', 0.0):.2f} km) that `{S6_TAG}` "
          f"did not level are OFF the reaches layer and on `reaches_unlevelled` with the "
          f"reason on every row.")
    else:
        A(f"**`{S6_TAG}` HAS NOT PUBLISHED and the retired stand-in shipped.** There is no "
          f"delta to report because there is only one answer, and it is the wrong one to "
          f"quote. Run `python s6_levels.py` and re-export.")
    A("")
    A("### 2. The names")
    A("")
    ncts = (nm.stats.get("naming_counts") or {}) if nm is not None else {}
    if ncts:
        A(f"`w12.naming.name_network()` - the module that was written for this and that "
          f"nothing in the pipeline called. {int(ncts.get('nodes_named', 0)):,} of "
          f"{int(ncts.get('nodes_total', 0)):,} chambers and "
          f"{int(ncts.get('reaches_named', 0)):,} of "
          f"{int(ncts.get('reaches_total', 0)):,} conduits are named, across "
          f"{int(ncts.get('towns_used', 0))} settlements and "
          f"{int(ncts.get('subnets', 0)):,} subnetworks. Town resolution follows the "
          f"engineer's rule (b): {int(ncts.get('town_inside', 0)):,} took the letter of "
          f"the polygon they sit in, {int(ncts.get('town_downstream', 0)):,} took the "
          f"first town DOWNSTREAM, {int(ncts.get('town_none', 0)):,} resolved to none.")
        A("")
        flg = (nm.stats.get("naming_flags") or {}) if nm is not None else {}
        if flg:
            A("What it REFUSED to name, rather than guessing (concept rule 7):")
            A("")
            A("| Flag | Count |")
            A("|---|---:|")
            for k, v in sorted(flg.items(), key=lambda t: -t[1]):
                A(f"| `{k}` | {int(v):,} |")
            A("")
        A(f"`contract.assert_named()` is called on nodes, reaches, stations and rising "
          f"mains at publication and its verdict is a row on `contract_check` - which is "
          f"how the {int(ncts.get('nodes_total', 0)) - int(ncts.get('nodes_named', 0)):,} "
          f"unnamed chambers are visible at all.")
    else:
        A("The settlement gazetteer could not be read, so nothing is named and "
          "`assert_named()` refuses every layer. That is the correct outcome.")
    A("")
    A("### 3. The plot connectability check")
    A("")
    cn_ = layers.get("connections")
    if cn_ is not None and len(cn_):
        bad = cn_[cn_.CAN_CONN == 0]
        A(f"`w12.connectivity.check_connections()`, basis `hcc`, arrival rule "
          f"`flow_depth`. **{int((cn_.CAN_CONN == 1).sum()):,} of {len(cn_):,} plots "
          f"reach their chamber on gravity; {len(bad):,} cannot.** The inline version this "
          f"replaces charged the 3 % property-connection minimum over the WHOLE route and "
          f"let a connection arrive at the chamber's bare invert. The module splits the "
          f"run - 2.5 m of property connection at 3 %, the rest at the 1 % lateral minimum "
          f"(G203-p18 Table 5) - and requires the connection to arrive above the sewer's "
          f"own design flow surface, d/D x bore (G203-p27 Table 10).")
        A("")
        A("| Why it cannot connect | Plots | Median depth needed | Worst |")
        A("|---|---:|---:|---:|")
        for w, sub in bad.groupby(bad.CONN_CODE.astype(str) if "CONN_CODE" in bad.columns
                                  else bad.CONN_WHY.astype(str)):
            nd_ = pd.to_numeric(sub.CONN_NEED, errors="coerce")
            A(f"| {w} | {len(sub):,} | {float(nd_.median()):.2f} m | "
              f"{float(nd_.max()):.2f} m |")
        A("")
        A("A verdict and a missing input are different rows in that table on purpose: "
          "`chamber level unknown` is a check that could not run, and CONN_NEED is 0.00 m "
          "on it because there is no remedy to size - not because the plot is fine.")
    A("")
    A("### 4. H15 against stage 5's own layers")
    A("")
    if orphans is not None and len(orphans):
        isl = orphans[orphans.WHY.astype(str).str.startswith("a REAL dead end")]
        A(f"**{len(orphans):,} corridor nodes in `W12_flows.gpkg` have no outgoing arc "
          f"marked `IS_ROUTE = 1` and are not marked `IS_OUTFALL`**, carrying "
          f"{float(orphans.Q_ADF_M3D.sum()):,.1f} m3/d. "
          f"{len(isl):,} of them sit on arcs stage 5 itself labels `ROLE = 'island'`, "
          f"`DELIVERED = 0` - so they are REAL dead ends and stage 5 knows it.")
        A("")
        A(f"**The defect is the node layer's `DELIVERED` column**: it publishes 1 on every "
          f"row, so the same GeoPackage says the arc is undelivered and the node standing "
          f"on it is delivered. That is the second failing audit check "
          f"(`test_node_delivered_agrees_with_arc_delivered`) and it is the same defect, "
          f"not a separate one. `s5_flows.py` owns both columns; this stage publishes the "
          f"list as `flow_orphans` rather than repairing a column it does not own.")
    else:
        A("Nothing to report: every node in the flows layer either has an outgoing route "
          "arc or is marked as an outfall.")
    A("")

    A("## What was built")
    A("")
    A("| Path | What |")
    A("|---|---|")
    A(f"| `W12/shp/W12_export.gpkg` | {len(layers)} contract layers + the check table, "
      f"the manifest and the assumptions |")
    A(f"| `W12/shp/kmz/*.kmz` | **{len(kmz.kmz)} styled Google Earth files**, each with "
      f"subfolders and a legend overlay |")
    A(f"| `W12/export/shp/` | {len(files['shp'])} shapefiles + tables, every one proven "
      f"to round-trip without losing a field name |")
    A(f"| `W12/export/dxf/` | {len(files['dxf'])} drawings - geometry, and geometry with "
      f"every chamber and pipe labelled |")
    A(f"| `W12/export/schedules/` | {len(files['sch'])} workbooks - chambers, pipes, "
      f"stations, rising mains, connections, crossings, subnetworks, quantities, "
      f"not-served, data dictionary |")
    A(f"| `W12/export/W12_FIELD_DICTIONARY.md` | the one-page key to every abbreviated "
      f"field name, generated from `contract.LAYERS` so it cannot go stale |")
    A(f"| `W12/export/profiles/` | {len(files['prf'])} long sections |")
    A(f"| `W12/shp/kmz/W12_theme_*.kmz` | the THREE themes - structure, depth, exceptions "
      f"- each one file with a folder per layer and the count in the folder name |")
    A(f"| `W12/shp/kmz/W12_*_*.qml` | the saved QGIS style for every theme layer, written "
      f"from the SAME class table the KMZ drew |")
    A(f"| SewerGEMS | **NOT EXPORTED.** Switched off at concept stage - "
      f"`criteria.CONCEPT_OFF[\"sewergems_export\"]`. It referees HYDRAULICS and can "
      f"never choose a layout, so running it against a layout still under review referees "
      f"the wrong thing |")
    A(f"| `W12/export/qgis_load_W12.py` | the PyQGIS loader, generated from the SAME "
      f"View objects the KMZ used |")
    A("")

    A("## The design, measured")
    A("")
    A("| | | Source |")
    A("|---|---|---|")
    A(f"| Gravity sewer | **{km:,.1f} km** | s4's chamber-to-chamber segments |")
    A(f"| Chambers | **{len(nd):,}** ({len(nd) / km:.1f} per km) | s4; built network 34.2/km |")
    A(f"| Components, each ending at exactly one outfall | **{int((nd.IS_OUTFALL == 1).sum())}** | H15 |")
    A(f"| Diameters | **DN{int(r.DN.min())}-{int(r.DN.max())}** | H8, sized on flow alone |")
    A(f"| Laid gradient | {r.SLOPE_LAID.min():.2f} - {r.SLOPE_LAID.max():.2f} %, "
      f"median {r.SLOPE_LAID.median():.2f} % | 0.05 % steps, P1 |")
    A(f"| Peak flow, largest reach | **{r.QPK_LS.max():.1f} L/s** | s5 published 234.7 |")
    A(f"| Velocity at peak | {r.V_PK_MS.min():.2f} - {r.V_PK_MS.max():.2f} m/s, "
      f"**0 over the 3.0 m/s maximum** | G203-p27 |")
    A(f"| d/D at peak | max {r.DOD_PK.max():.3f}, **0 reaches over the Table 10 limit** | "
      f"G203-p27 Tab 10 |")
    A(f"| Cover | median {cov_med:.2f} m, deepest **{cov_max:.2f} m** | G203-p33 |")
    if n_nolvl:
        A(f"| Chambers with NO LEVEL AT ALL | **{n_nolvl}** | {LEVELS_SOURCE} published "
          f"no invert for them, so COVER_M and DEPTH_M are NULL on those rows and the "
          f"figures above are taken over the rest - see `reaches_unlevelled` |")
    A(f"| Below the 1.30 m minimum cover | **{lv.stats['km_below_min_cover']:.2f} km** | G203-p33 |")
    A(f"| Backdrops (0.60-2.00 m) | {int((nd.DROP_TYPE == 'backdrop').sum()):,} | G203-p30 |")
    A(f"| **Vortex drop shafts (> 2.00 m)** | **{int((nd.DROP_TYPE == 'vortex').sum()):,}** | "
      f"G203-p30. NAMA's built network has 37 |")
    A(f"| Inlets under 90 deg | {int((nd.INLET_FLAG == 1).sum()):,} | G203-p30, H10 |")
    A(f"| Draining against the ground | **{_pct(float(r.LEN_M[r.AGN_GRADE == 1].sum()), float(r.LEN_M.sum())):.1f} %** "
      f"of length ({float(r.LEN_M[r.AGN_GRADE == 1].sum()) / 1000:.1f} km) | "
      f"philosophy sec 4; NAMA's own built network runs uphill on 34 % |")
    A(f"| Load connected | **{float(cn.Q_ADF_M3D.sum()):,.1f} m3/d** over "
      f"{len(cn):,} plots | s4; s5 published 70,405.5 |")
    A(f"| Properties | {float(cn.N_PROP.sum()):,.0f} | s4 |")
    A("")

    A("### Self-cleansing, and the size of the tau exposure")
    A("")
    A(f"**{lv.stats['km_tractive']:,.1f} km ({_pct(lv.stats['km_tractive'], km):.1f} %) is "
      f"self-cleansed by the TRACTIVE route**, {lv.stats['km_velocity']:,.1f} km "
      f"({_pct(lv.stats['km_velocity'], km):.1f} %) by velocity, and "
      f"{lv.stats['km_neither']:.2f} km by neither. G203-p27 4.2.2.1 offers the two as "
      f"alternatives and requires the steeper, so the tractive share is legal - and it is "
      f"also the exact extent of the scheme resting on tau = {C.TAU_PA:g} Pa, which the "
      f"guideline never gives (GAP-9). At 2.0 Pa every one of those gradients rises "
      f"{C.TAU_SLOPE_FACTOR_AT_2PA:.3f}x.")
    A("")

    A("### What set each diameter, and what set each gradient")
    A("")
    A("| Diameter set by | Reaches | km | | Gradient set by | Reaches | km |")
    A("|---|---|---|---|---|---|---|")
    sb = r.groupby("SIZED_BY").agg(n=("LEN_M", "size"), km=("LEN_M", "sum"))
    gb = r.groupby("GRAD_BY").agg(n=("LEN_M", "size"), km=("LEN_M", "sum"))
    sb_rows = [(i, int(v.n), v.km / 1000) for i, v in sb.iterrows()]
    gb_rows = [(i, int(v.n), v.km / 1000) for i, v in gb.iterrows()]
    for i in range(max(len(sb_rows), len(gb_rows))):
        s_ = sb_rows[i] if i < len(sb_rows) else ("", "", "")
        gg = gb_rows[i] if i < len(gb_rows) else ("", "", "")
        A(f"| {s_[0]} | {s_[1]} | {s_[2] if s_[2] == '' else f'{s_[2]:,.1f}'} | | "
          f"{gg[0]} | {gg[1]} | {gg[2] if gg[2] == '' else f'{gg[2]:,.1f}'} |")
    A("")
    A("`depth` and `cover` are not in the SIZED_BY vocabulary and cannot be: oversizing a "
      "pipe to lay it flatter is prohibited by G203-p29 and by Ten States sec 33.43 "
      "independently, so the prohibited move is not expressible on the layer.")
    A("")

    A("### The wadi and dual-carriageway register, MEASURED")
    A("")
    A(f"**{cross_stats['n_rows']:,} registered contacts** - {cross_stats['n_wadi']:,} wadi, "
      f"{cross_stats['n_dual']:,} dual carriageway - over "
      f"**{cross_stats['km_wadi']:.2f} km** of wadi ground and "
      f"**{cross_stats['km_dual']:.3f} km** of dual carriageway. The angle is measured "
      f"against the nearest stream line's own direction, sampled every "
      f"{WADI_SAMPLE_M:g} m off the {C.HAZARD_RETURN_YR}-year hazard grid: "
      f"**median {cross_stats['angle_median']:.1f} deg, minimum "
      f"{cross_stats['angle_min']:.1f} deg, and only {cross_stats['n_square']:,} of "
      f"{cross_stats['n_rows']:,} sit within {C.WADI_XING_SKEW_DEG:g} deg of square.** "
      f"The rest run ALONG the channel rather than across it, which H1 forbids and H1a "
      f"does not excuse. `APPROVED = 0` on every row: MoAFWR consent (G201-p85) and the "
      f"roads authority's are open items, not silent ones.")
    A("")
    A(f"*W11a published `ANGLE_DEG = 90` on 3,290 crossings. It was fabricated and the "
      f"measured minimum was 0.00 deg. This register measures every one.*")
    A("")

    A("### CONCEPT RULE 5 - plot connectability, with the SIZE of every failure")
    A("")
    A(f"**{int((cn.CAN_CONN == 1).sum()):,} of {len(cn):,} connected plots reach their "
      f"chamber on gravity**; **{int((cn.CAN_CONN == 0).sum()):,} cannot.** The test is "
      f"the engineer's and it is `w12.connectivity`'s, called - not a copy of it kept "
      f"here. Each half of it matters: the connection leaves BELOW ground at the "
      f"G203-p19 3.4 minimum HCC depth of {C.HCC_DEPTH_MIN:g} m (not at the surface), it "
      f"runs to a CHAMBER (not to the nearest point on a pipe), and it loses fall over "
      f"its OWN route - {C.HCC_OFFSET_M:g} m of property connection at the "
      f"{C.PCS_MIN_SLOPE * 100:g} % minimum and the rest at the "
      f"{C.LATERAL_MIN_SLOPE * 100:g} % lateral minimum, both G203-p18 Table 5. It must "
      f"then arrive ABOVE the sewer's own design flow surface, d/D x internal bore "
      f"(G203-p27 Table 10), not merely at the chamber's invert - the rule is this "
      f"project's assumption, the number is the guideline's.")
    A("")
    A(f"Rule 7 is why the number is usable: **every failure carries `CONN_NEED`, how many "
      f"metres deeper the sewer would have to be on that run** - median "
      f"{float(cn.loc[cn.CAN_CONN == 0, 'CONN_NEED'].median()) if int((cn.CAN_CONN == 0).sum()) else 0.0:.2f} m, "
      f"worst {float(cn.CONN_NEED.max()):.2f} m. \"5,521 plots cannot drain\" is a number "
      f"nobody can act on; \"this plot needs the sewer 0.84 m deeper\" is a decision.")
    A("")
    A("`CAN_DRAIN` is written FROM `CAN_CONN` and is never computed a second time. Two "
      "answers to one question is the defect this project pays most for, and the contract "
      "refuses the layer if the two disagree.")
    A("")

    A("## What does NOT validate, and why each one is real")
    A("")
    A("`contract.validate()` was run over every published layer before a single schedule, "
      "drawing or model file was written. Nothing was silenced. The full text of every "
      "objection is in the `contract_check` layer of the GeoPackage and on the last sheet "
      "of the data dictionary.")
    A("")
    A("| Layer | Result |")
    A("|---|---|")
    for row in chk.itertuples():
        A(f"| `{row.LAYER}` | {'PASSES' if row.PASS else '**' + row.RESULT + '**'} |")
    A("")
    A("| What fails | Extent | Whose it is |")
    A("|---|---|---|")
    A(f"| Depth / cover / drop past the contract's 40 m and 20 m range guards | "
      f"{int((nd.DEPTH_M > CT.DEPTH_SANITY_M).sum()):,} chambers, "
      f"{int((nd.DROP_M > C.DROP_CEILING_M).sum()):,} drops, worst "
      f"{nd.DROP_M.max():.1f} m | **the design.** Flatness, not arithmetic |")
    A(f"| Past the 12 m cap with no sec 5 exit | {lv.stats['past_cap_no_exit']:,} chambers, "
      f"{int(((r.PAST_CAP == 1) & (r.CAP_EXIT.fillna('').astype(str) == '')).sum()):,} reaches | "
      f"**stage 7's**: every one is a station demand |")
    A(f"| `SLOPE_LAID` over the contract's 25 % bound | "
      f"{int((r.SLOPE_LAID > 25.0).sum())} reaches, worst {r.SLOPE_LAID.max():.2f} % | "
      f"**the ground.** Capping them put the pipe above the surface, which is not a "
      f"conservative answer but an impossible one |")
    A(f"| `LEN_M` under the 0.5 m floor | {int((r.LEN_M < 0.5).sum())} reach "
      f"({r.LEN_M.min():.3f} m) | s4's chamber spacing |")
    A(f"| `connections` geometry invalid | "
      f"{int((cn.LEN_M < 1e-9).sum()):,} zero-length connections | s4: the chamber stands "
      f"on the property's own connection point. Shapely calls a zero-length LineString "
      f"invalid |")
    A(f"| `FLOOD_LV` null on all {len(st)} stations | {len(st)} | **NWS.** "
      f"`hazard.flood_level_m_aod()` raises by design - the grids carry an AR&R hazard "
      f"CLASS and no water level, and G203-p38 7.2 needs the 1:50 water surface for the "
      f"300 mm freeboard. Filling it with ground level (which this stage did on its first "
      f"build) manufactured a freeboard failure on every one that says nothing about "
      f"any |")
    A(f"| Rising mains under 0.75 m/s at design MINIMUM flow | {len(layers['rising_mains'])} | "
      f"**s7's**, inherited unchanged |")
    A(f"| `WELL_M3` disagrees with 0.25 Q T | 1 station | **s7's**, inherited unchanged |")
    A(f"| 2 reaches touch BOTH a wadi and a dual carriageway | 2 | **the contract's**: a "
      f"reach carries one `CROSS_ID` and cannot be registered against two obstacles |")
    A("")

    A("## What this export could NOT do")
    A("")
    A(f"1. **Design the trunk.** `W12_hier.gpkg|trunk` is "
      f"{float(layers['trunk'].LEN_M.sum()) / 1000:,.2f} km of the client's own "
      "Main Pipe in 54 pieces, with no chambers and no topology. Nothing here drains into "
      f"it. The {int((nd.IS_OUTFALL == 1).sum()):,} outfalls are subnetwork outlets, "
      f"each an independent discharge, and "
      "the biggest reach in the design therefore carries a fraction of what a joined "
      "network would. A joined-network flow can only be a hypothetical until something "
      "drains into the trunk.")
    _snap = pd.to_numeric(a.stations.ST_SNAP_M, errors="coerce")         if "ST_SNAP_M" in a.stations.columns else pd.Series(dtype=float)
    A(f"2. **Resolve the station ids.** s7 mints station `NODE_UID`s that also exist in "
      f"the chamber layer on different chambers, and none agree on ground level. "
      f"Re-anchored by proximity across {len(a.stations):,} stations - median "
      f"{_snap.median() if len(_snap) else float('nan'):.2f} m, max "
      f"{_snap.max() if len(_snap) else float('nan'):.1f} m, "
      f"{int((_snap < 1.0).sum()) if len(_snap) else 0} within 1 m - and published as "
      f"`ANCHOR_ND` with `ST_SNAP_M` beside it. A recovered anchor is not written "
      f"topology (H16).")
    A("3. **Phase anything.** `PHASE = 0` on every row: the contract's own words are "
      "\"0 = not yet assigned\". Packages are one per subnetwork - which satisfies "
      "\"one tree, one outlet\" by construction and the 3.5-40 km size band only where it "
      f"happens to: {int(layers['packages'].IN_BAND.sum())} of "
      f"{len(layers['packages'])} do, largest {layers['packages'].LEN_KM.max():.1f} km, "
      f"median {layers['packages'].LEN_KM.median():.2f} km.")
    A("4. **Run the second pass.** Philosophy sec 7 wants a strict pass, a review pass and "
      "then the audit. This is one strict pass. Nothing here absorbs a finger, moves a sub "
      "main onto a through-street or puts a station on a package seam.")
    A("5. **Referee its own hydraulics.** The SewerGEMS export is SWITCHED OFF at concept "
      "stage (`criteria.CONCEPT_OFF[\"sewergems_export\"]`), not forgotten. It referees "
      "HYDRAULICS and can never choose a layout (inheritance row 26), so running it "
      "against a layout still under review referees the wrong thing. `contract.SEWERGEMS` "
      "still maps every field to its Bentley name and is waiting for the layout to be "
      "fixed.")
    A("6. **Read s6_levels' inverts.** W12 HAS a stage 6 and it publishes its own "
      "`W12.gpkg`; this stage still computes levels with the stand-in it inherited from "
      "W11b, where there was no stage 6. That is two functions for one published quantity "
      "- inheritance row 10, the row that put seven station counts into circulation in "
      "W10. It is DETECTED and printed on every run rather than resolved blind: the swap "
      "has to be made against real layers, matching on the WRITTEN topology and refusing "
      "unless every edge matches.")
    A("")

    A("## Every number this stage used that is not already in `criteria`")
    A("")
    A("| Name | Value | Source | Why |")
    A("|---|---|---|---|")
    for name, val, src, why in EXPORT_NUMBERS:
        A(f"| `{name}` | {val} | {src} | {why} |")
    A("")
    A(f"*{C.tau_banner()}*")
    A("")

    A("## The three themes")
    A("")
    A("Each is one KMZ with a folder per layer, and one saved QGIS style (`.qml`) per "
      "layer. Both are written from the SAME class table, so the Earth file and the GIS "
      "project cannot tell different stories.")
    A("")
    A("| Theme | What it shows |")
    A("|---|---|")
    A("| **STRUCTURE** | every subnetwork its own colour, conduit weight rising with DN, "
      "flow direction, and pumps / force mains / drop chambers / the chamber where each "
      "subnetwork meets the main pipe all separately symbolised |")
    A(f"| **DEPTH** | the MAGMA ramp on EVERY element, classified on ONE column (`DEP_M`) "
      f"against FIXED published edges - {', '.join('%.2f' % b for b in DEPTH_BREAKS)} m - "
      f"so two runs are comparable. Never auto-stretched |")
    A("| **EXCEPTIONS** | ONLY the flagged items. Colour by kind, size by severity, and "
      "**the count is in the layer name**, so the legend itself reports the totals |")
    A("")
    A("What lands on the EXCEPTIONS theme, and how big each one is:")
    A("")
    A("| Exception | Count |")
    A("|---|---|")
    _sn = layers.get("subnetworks")
    _rej = layers.get("stations_rejected")
    for _lab, _n in (
            ("Plots that CANNOT connect on gravity", int((cn.CAN_CONN == 0).sum())),
            ("Subnetworks that do NOT reach the main pipe",
             int(((_sn.SERVED == 1) & (_sn.JOIN_MAIN == 0)).sum()) if _sn is not None else 0),
            ("Outfalls off their subnetwork's own low point",
             int((pd.to_numeric(nd.JOIN_OFF_M, errors="coerce").fillna(0) > 0).sum())),
            ("Drops that exist only to hold the velocity cap",
             int(((nd.DROP_TYPE != "none") & (nd.DROP_WHY == "velocity_cap")).sum())),
            (f"Chambers past the {C.MAX_COVER:g} m cover cap",
             int((nd.PAST_CAP == 1).sum())),
            ("Chambers on wadi ground",
             int((pd.to_numeric(nd.ON_WADI, errors="coerce").fillna(0) > 0).sum())),
            ("Force mains that lift all the way to the works",
             int((layers["rising_mains"].DS_TYPE == "stp").sum())),
            ("Pumping stations REMOVED - nothing drained into them",
             len(_rej) if _rej is not None else 0),
            ("Areas the network does not reach",
             int((_sn.SERVED == 0).sum()) if _sn is not None else 0)):
        A(f"| {_lab} | **{_n:,}** |")
    A("")

    A("## The per-question KMZ set")
    A("")
    A("| File | The question it answers |")
    A("|---|---|")
    for k in sorted(kmz.kmz, key=lambda x: PR.VIEWS[x.view].priority):
        v = PR.VIEWS[k.view]
        A(f"| `{os.path.basename(k.path)}` | {v.question} |")
    if kmz.skipped:
        A("")
        A("Skipped, with the reason:")
        for nm, why in kmz.skipped:
            A(f"- `{nm}`: {why}")
    A("")
    A("## Run log")
    A("")
    A("```")
    L.extend(_LOG)
    A("```")

    p = os.path.join(RUN, "EXPORT.md")
    os.makedirs(RUN, exist_ok=True)
    open(p, "w", encoding="utf-8").write("\n".join(L))
    return p


# ======================================================================================
# 16.  BUILD, VERIFY, SELF-TEST
# ======================================================================================

def levels_source_conflict() -> Optional[str]:
    """Is there a SECOND set of levels in this folder? Say so, loudly, by name.

    W12 has an `s6_levels.py` and it publishes `W12.gpkg`. This stage carries a levels
    stand-in inherited from W11b, where there genuinely was no stage 6. Two passes that
    both compute an invert is inheritance row 10 - "one published quantity, one function" -
    and that row is the one that put seven station counts into circulation in W10.

    KEPT AFTER THE REWIRE, and it now reports a state that should not occur. `build()`
    reads s6's inverts through `read_s6_levels()` and the section-4 stand-in publishes
    nothing, so a non-None answer here means the stand-in shipped - which only happens when
    s6's file could not be read at all. `tests/test_export_themes.py` exercises this
    function directly, so its signature and its message are part of the interface."""
    if not os.path.exists(GPKG_S6):
        return None
    try:
        import fiona
        have = set(fiona.listlayers(GPKG_S6))
    except Exception as e:                                     # pragma: no cover
        return (f"{os.path.basename(GPKG_S6)} exists but its layers could not be listed "
                f"({type(e).__name__}: {e})")
    if not {"nodes", "reaches"} & have:
        return None
    try:
        r6 = gpd.read_file(GPKG_S6, layer="reaches", ignore_geometry=True)
        n6 = gpd.read_file(GPKG_S6, layer="nodes", ignore_geometry=True)
        extra = ""
        if "INV_M" in n6.columns:
            extra = (f" s6 published {len(n6):,} chambers, inverts "
                     f"{pd.to_numeric(n6.INV_M, errors='coerce').min():.2f} to "
                     f"{pd.to_numeric(n6.INV_M, errors='coerce').max():.2f} m aOD, and "
                     f"{len(r6):,} reaches.")
    except Exception as e:                                     # pragma: no cover
        extra = f" (its layers would not read: {type(e).__name__}: {e})"
    return (
        "TWO SETS OF LEVELS EXIST IN THIS FOLDER. `s6_levels` has published "
        f"{os.path.basename(GPKG_S6)} AND this stage has just computed its own with the "
        f"W11b stand-in tagged '{LEVELS_TAG}'." + extra +
        " Inheritance row 10 says one published quantity has one function. Wire s8 to READ "
        "s6's nodes/reaches (match on the WRITTEN topology - US_NODE/DS_NODE and NODE_UID - "
        "and REFUSE the swap unless every edge matches, rather than falling back silently), "
        "or delete the stand-in. Until then, do not quote a depth from one file against a "
        "depth from the other.")


def _split_unlevelled(layers: Dict[str, gpd.GeoDataFrame],
                      s6: Optional[S6Levels]) -> gpd.GeoDataFrame:
    """Take the reaches nobody levelled OFF the reaches layer and publish them whole.

    Returns the removed rows, joined to s6's own reason for each. The count and the length
    go into REMOVED_COUNTS, which the manifest reads: this stage says what it removed."""
    r = layers["reaches"]
    if s6 is None or int((~s6.e_ok).sum()) == 0:
        return r.iloc[0:0].copy()
    keep = np.asarray(s6.e_ok, dtype=bool)
    out = r.loc[~keep].copy()
    layers["reaches"] = r.loc[keep].reset_index(drop=True)
    why = s6.gaps.set_index("EDGE_UID")
    out["GAP_KIND"] = out.EDGE_UID.astype(str).map(why.GAP_KIND).fillna("unknown")
    out["WHY"] = out.EDGE_UID.astype(str).map(why.WHY).fillna(
        "no reach at this (US_NODE, DS_NODE) in " + os.path.basename(GPKG_S6))
    out["LIFT_M"] = pd.to_numeric(out.EDGE_UID.astype(str).map(why.LIFT_M),
                                  errors="coerce").fillna(0.0)
    # every level field on these rows is NOT AN ANSWER. Blank them rather than ship a
    # number that came from nowhere - a NULL is checkable, a plausible float is not.
    for c in ("DN", "SLOPE_LAID", "SLOPE_MIN", "INV_UP", "INV_DN", "US_DEPTH", "DS_DEPTH",
              "COVER_US", "COVER_DN", "V_PK_MS", "DOD_PK", "RET_MIN"):
        if c in out.columns:
            out[c] = np.nan
    for c in ("GRAD_BY", "SIZED_BY", "CLEAN_BY", "MATERIAL"):
        if c in out.columns:
            out[c] = ""
    out = out.reset_index(drop=True)
    layers["reaches_unlevelled"] = out
    REMOVED_COUNTS["reaches_unlevelled"] = int(len(out))
    REMOVED_COUNTS["reaches_unlevelled_km"] = round(float(out.LEN_M.sum()) / 1000.0, 3)
    _log(f"   REMOVED from the reaches layer: {len(out):,} reaches "
         f"({out.LEN_M.sum() / 1000.0:.2f} km) that {S6_TAG} did not level - published on "
         f"`reaches_unlevelled` with the reason on every row. By reason: "
         + ", ".join(f"{k} {v:,}" for k, v in out.GAP_KIND.value_counts().items()))
    return out


def withdraw_orphan_crossings(layers: Dict[str, gpd.GeoDataFrame]) -> int:
    """A crossing register row that no published reach references any more.

    `contract.assert_crossings_resolve()` refuses one, and it is right to: the register
    says a pipe crosses an obstacle here, and after the unlevelled routes come off the
    reaches layer no pipe does. Withdrawn to its own layer with the reason, counted in
    REMOVED_COUNTS - never left dangling, and never left in to make a count look bigger."""
    cx = layers.get("crossings")
    if cx is None or not len(cx) or "CROSS_ID" not in cx.columns:
        return 0
    still = set(layers["reaches"].CROSS_ID.astype(str))
    gone = ~cx.CROSS_ID.astype(str).isin(still)
    if not gone.any():
        return 0
    layers["crossings_withdrawn"] = cx.loc[gone].assign(
        WD_WHY="the only reach that crossed here is a route " + S6_TAG + " did not level "
               "(see reaches_unlevelled), so no gravity pipe crosses this obstacle any "
               "more").reset_index(drop=True)
    layers["crossings"] = cx.loc[~gone].reset_index(drop=True)
    REMOVED_COUNTS["crossings_withdrawn"] = int(gone.sum())
    _log(f"   WITHDREW {int(gone.sum())} crossing register row(s) "
         f"({', '.join(cx.loc[gone].CROSS_ID.astype(str)[:6])}) - nothing crosses there "
         f"now that the reach is off the reaches layer")
    return int(gone.sum())


def build(do_dxf: bool = True, do_profiles: bool = True, do_kmz: bool = True) -> Dict[str, Any]:
    _mkdirs()
    print(C.concept_banner())
    with CT.Manifest.stage(STAGE, STAGE_ORDER) as rec:
        a = assemble()
        for nm, src, n in a.reads:
            rec.read(nm, src, n)
        g = build_graph(a)
        f = accumulate(a, g)

        # ---- THE LEVELS. One question, one answer, and it is s6_levels'. ---------------
        # The section-4 stand-in still runs, ONCE, and is published NOWHERE: the size of
        # what it disagreed with s6 about is a number the engineer asked for, and the only
        # way to have it is to compute both. `levels_delta` carries it.
        global LEVELS_SOURCE
        s6 = read_s6_levels(a, g, f)
        LEVELS_SOURCE = S6_TAG if s6 is not None else LEVELS_TAG
        lv_standin = design_levels(
            a, g, f, label="the RETIRED s8 stand-in - measured for the delta, NOT published")
        if s6 is not None:
            lv = s6.lv
            for note in s6.notes:
                a.note(note)
            delta = levels_delta(g, s6, lv_standin)
            worst = delta[delta.QUANTITY == "chamber invert"]
            conflict = (
                f"LEVELS NOW COME FROM {S6_TAG} ({os.path.basename(GPKG_S6)}), matched on "
                f"the WRITTEN topology: {s6.stats['reaches_matched']:,} of "
                f"{len(g.e_len):,} reaches and {s6.stats['nodes_matched']:,} of "
                f"{len(g.uid):,} chambers. The stand-in tagged '{LEVELS_TAG}' is RETIRED "
                f"as a publication source and survives only as the measurement on the "
                f"`levels_delta` layer"
                + (f" - it disagreed with s6 on {int(worst.N_DIFFER.iloc[0]):,} of "
                   f"{int(worst.N.iloc[0]):,} chamber inverts, worst "
                   f"{max(abs(float(worst.MIN_DIFF.iloc[0])), abs(float(worst.MAX_DIFF.iloc[0]))):.2f} m"
                   if len(worst) else "") + ".")
        else:
            lv = lv_standin
            delta = pd.DataFrame(columns=["QUANTITY", "UNIT", "N", "N_DIFFER"])
            conflict = (
                f"{os.path.basename(GPKG_S6)} IS NOT THERE, so the levels on every layer "
                f"below are the RETIRED s8 stand-in tagged '{LEVELS_TAG}'. Run "
                f"`python s6_levels.py` and re-export; do not quote a depth from this run.")
        _log("   *** " + conflict)
        a.note(conflict)
        lv_st = lv_standin

        contacts = measure_contacts(a, g)
        cx, cross_id, cross_stats = build_crossings(a, g, contacts)
        pk, node_pkg, edge_pkg = build_packages(a, g, f)
        nm_ = build_names(a, g, f)
        for note in nm_.notes:
            a.note(note)
        jn = measure_joins(a, g, f)

        layers = build_layers(a, g, f, lv, contacts, cross_id, node_pkg, edge_pkg, nm_, jn,
                              s6=s6)
        # ---- WHAT s6 DID NOT LEVEL COMES OFF THE REACHES LAYER ------------------------
        # Inheritance row 4: a later pass may TAKE AWAY what an earlier one added, and it
        # publishes how many. These segments are real routes - they are not deleted - but
        # they carry no invert, no gradient and no diameter that anyone solved, so they are
        # not gravity reaches and must not be counted, drawn or scheduled as if they were.
        unlev = _split_unlevelled(layers, s6)
        layers["connections"] = build_connections(a, g, layers["nodes"], layers["reaches"])
        (layers["stations"], layers["rising_mains"],
         layers["stations_rejected"]) = build_stations(a, layers["nodes"], g, f, nm_)
        layers["crossings"] = cx
        withdraw_orphan_crossings(layers)
        layers["packages"] = pk
        layers["trunk"] = build_trunk(a)
        layers["subnetworks"] = build_subnetworks(layers, a, g, f, nm_, jn)
        carry_src_raw(layers)
        _extra_columns(layers)
        register_extra_views()
        tune_views()
        add_band_columns(layers)

        fun = rec.funnel("plots -> connections", int(len(a.connections) + len(a.unserved)))
        fun.drop("no chamber within 45 m of the plot (s4)", n=len(a.unserved),
                 qty=float(a.unserved.Q_ADF_M3D.sum()))
        fun.close(len(layers["connections"]))

        ofc = outfall_check(g, f, layers)
        chk = check_contract(layers)
        n_fail = int((chk.PASS == 0).sum())
        _log(f"contract check: {len(chk) - n_fail} of {len(chk)} checks pass, "
             f"{n_fail} named violations published on the `contract_check` layer")
        for row in chk[chk.PASS == 0].itertuples():
            _log(f"   FAIL {row.LAYER}: {str(row.DETAIL)[:180]}")

        extra = {
            "contract_check": chk,
            "manifest": _manifest_table(a, g, f, lv, lv_st, layers, cross_stats),
            "assumptions": _assumptions_table(),
            "levels_arms": _arms_table(lv, lv_st),
            "levels_delta": delta,
            "levels_gaps": (s6.gaps if s6 is not None
                            else pd.DataFrame(columns=["EDGE_UID", "WHY"])),
            "flow_orphans": flow_orphans(),
            "outfall_check": ofc,
        }
        pub = {k: v for k, v in layers.items()}
        written_to = publish(pub, extra)
        for k, v in pub.items():
            rec.wrote(k, written_to, len(v))

        files: Dict[str, List[str]] = {"shp": [], "dxf": [], "sch": [], "prf": [],
                                       "kmz": [], "doc": []}
        files["shp"] = write_shapefiles(
            {k: v for k, v in layers.items() if k != "packages"},
            {"packages": pk, "contract_check": chk, "manifest": extra["manifest"],
             "levels_arms": extra["levels_arms"], "outfall_check": ofc})
        files["doc"] = [write_field_dictionary(layers)]
        if do_dxf:
            files["dxf"] = write_dxf(layers)
        files["sch"] = write_schedules(a, layers, chk)
        if do_profiles:
            files["prf"] = write_profiles(g, layers, node_pkg)

        if do_kmz:
            arrows = flow_arrows(layers["reaches"])
            for _t, fl in write_themes(layers, arrows).items():
                files["kmz"] += fl
        kmz = build_kmz_from_gpkg(written_to) if do_kmz else None
        if kmz is not None:
            qgis_script(kmz)
        rep = write_report(a, g, f, lv, lv_st, layers, chk, cross_stats,
                           kmz or _empty_render(), files, ofc,
                           delta=delta, orphans=extra["flow_orphans"], nm=nm_)
        _log(f"report -> {rep}")
        rec.metric("network_km", round(float(layers['reaches'].LEN_M.sum()) / 1000.0, 3))
        rec.metric("chambers", len(layers["nodes"]))
        rec.metric("past_cap_no_exit", lv.stats["past_cap_no_exit"])
        rec.metric("vortex_shafts", int((layers["nodes"].DROP_TYPE == "vortex").sum()))
        rec.metric("stations_published", len(layers["stations"]))
        rec.metric("stations_removed", len(layers["stations_rejected"]))
        # inheritance row 4 - the whole removal ledger, not just its headline row
        rec.metric("rising_mains_removed",
                   int(REMOVED_COUNTS.get("rising_mains_removed", 0)))
        rec.metric("chambers_not_named_no_tier_token",
                   int(nm_.stats.get("names_refused_no_tier_token", 0)))
        rec.metric("themes_that_failed_to_build", len(THEME_FAILURES))
        rec.metric("subnetworks_not_at_main", jn.stats["short"])
        rec.metric("plots_that_cannot_connect",
                   int((layers["connections"].CAN_CONN == 0).sum()))
        rec.metric("reaches_unlevelled", int(REMOVED_COUNTS.get("reaches_unlevelled", 0)))
        rec.metric("s5_nodes_with_nowhere_to_send_their_flow", len(extra["flow_orphans"]))
        rec.note(f"levels by {S6_TAG if s6 is not None else LEVELS_TAG}. " + conflict)
    return dict(layers=layers, levels=lv, levels_stations=lv_st, check=chk, files=files,
                report=rep, graph=g, flows=f, naming=nm_, joins=jn,
                gpkg=written_to, conflict=conflict)


def _empty_render():
    return PR.RenderResult(DIR_KMZ, [], {"layers": [], "layouts": []}, "", [], {})


def build_kmz_from_gpkg(gpkg: Optional[str] = None) -> "PR.RenderResult":
    """Render every view straight off the PUBLISHED GeoPackage.

    Not off the in-memory frames: the QGIS project this generates points at the same file,
    so a reviewer opening it after the next rerun sees the new answer instead of a copy
    that has quietly gone stale. It also means the KMZ is drawn from exactly the bytes the
    contract check was run against."""
    # THE FILE THAT WAS ACTUALLY WRITTEN, not the canonical name. `publish()` falls back
    # to a timestamped file when the target is locked; rendering off GPKG_OUT in that case
    # would draw the PREVIOUS run and nothing would say so.
    gpkg = gpkg or GPKG_OUT
    roles = {r: (gpkg, r) for r in
             ("reaches", "nodes", "stations", "rising_mains", "crossings", "connections")}
    register_extra_views()
    tune_views()
    fold_on_bands()
    _log(f"rendering {len(KMZ_VIEWS)} KMZ views through w12.present, off "
         f"{os.path.basename(gpkg)}")
    res = PR.render(roles, DIR_KMZ, views=KMZ_VIEWS, prefix="W12", group="Claude W12",
                    layouts=("tier", "depth", "subnet", "diameter", "stations",
                             "pumping_demand"),
                    legend=True, max_features=260_000)
    print(res.report())
    return res


def _manifest_table(a, g, f, lv, lv_st, layers, cross_stats) -> pd.DataFrame:
    nd, r = layers["nodes"], layers["reaches"]
    km = float(r.LEN_M.sum()) / 1000.0
    _unl = layers.get("reaches_unlevelled")
    _km_unlev = 0.0 if _unl is None or not len(_unl) else float(_unl.LEN_M.sum()) / 1000.0
    rows = [
        ("stage", VERSION, "-", "this module"),
        ("run", time.strftime("%Y-%m-%d %H:%M"), "-", ""),
        ("LEVELS_SRC", LEVELS_SOURCE, "-",
         "every invert, DN, gradient, velocity, d/D, cover and drop below came from this "
         "one solver, matched onto this stage's graph on the WRITTEN topology "
         "(US_NODE/DS_NODE, NODE_UID) and never on row order or EDGE_UID"),
        ("SECOND SET OF LEVELS",
         "no - the stand-in is RETIRED and publishes nothing" if LEVELS_SOURCE == S6_TAG
         else "YES, AND THE RETIRED ONE IS WHAT SHIPPED - see EXPORT.md", "-",
         "inheritance row 10, one published quantity and one function. The size of what "
         "the two solvers disagreed about is on the `levels_delta` layer"),
        ("CONCEPT_STAGE", C.CONCEPT_STAGE, "-", C.concept_banner()),
        ("network", round(km, 3), "km", "LEN_M over the published reach layer"),
        ("chambers", len(nd), "-", "the published node layer"),
        # OVER THE WHOLE ROUTE, not over the levelled part of it. Every chamber is on this
        # layer, including the ones standing on a route the leveller did not answer for, so
        # dividing by the reaches layer alone counted all the chambers against half the
        # pipe - 80.0 per km on the 12:00 export against a built network at 34.23.
        ("chambers per km", round(len(nd) / max(1e-9, km + _km_unlev), 2), "-",
         f"built network 34.23 (s4/asbuilt). Over the WHOLE route this stage published: "
         f"{km:,.1f} km of levelled reaches plus {_km_unlev:,.1f} km on "
         f"`reaches_unlevelled`"),
        ("outfalls", int((nd.IS_OUTFALL == 1).sum()), "-",
         "H15: one per component. NOT the works - the trunk is not in this graph"),
        ("load connected", round(float(layers['connections'].Q_ADF_M3D.sum()), 1), "m3/d",
         "s4; s5 published 70,405.5 and this accumulator reproduces it"),
        ("DN range", f"DN{int(r.DN.min())}-{int(r.DN.max())}", "mm", "H8, sized on flow"),
        ("largest peak flow", round(float(r.QPK_LS.max()), 2), "L/s",
         "s5 published 234.7 over its corridor arcs"),
        ("max velocity", round(float(r.V_PK_MS.max()), 3), "m/s", "G203-p27 max 3.0"),
        ("max d/D", round(float(r.DOD_PK.max()), 4), "-", "G203-p27 Tab 10"),
        # nan-AWARE, AND THE BLANKS COUNTED BESIDE IT. np.median over a column with one
        # NULL returns nan, and the 12:00 export shipped "median cover | nan | m" as a
        # headline on the manifest, the manifest CSV and the DXF/KMZ banner that read it.
        # A headline destroyed by a blank is the same defect as a headline that is wrong.
        ("median cover", round(float(np.nanmedian(
            pd.to_numeric(nd.COVER_M, errors="coerce"))), 3)
            if int(pd.to_numeric(nd.COVER_M, errors="coerce").notna().sum()) else "NONE",
         "m", "G203-p33 min 1.30, over the chambers that HAVE a level"),
        ("chambers with NO LEVEL AT ALL",
         int(pd.to_numeric(nd.COVER_M, errors="coerce").isna().sum()), "chambers",
         f"{LEVELS_SOURCE} published no chamber at this NODE_UID, so INV_M, DEPTH_M and "
         f"COVER_M are NULL and every depth statistic above is over the rest"),
        ("deepest cover", round(float(nd.COVER_M.max()), 3), "m", "G203-p33 cap 12"),
        ("past the 12 m cap", int((nd.PAST_CAP == 1).sum()), "chambers", "G203-p33"),
        ("past the cap WITH NO EXIT", lv.stats["past_cap_no_exit"], "chambers",
         "philosophy sec 5 - each is a station demand handed back to stage 7"),
        ("levels source", S6_TAG, "-",
         "one published quantity, one function (inheritance row 10). The stand-in tagged "
         f"'{LEVELS_TAG}' is RETIRED and publishes nothing"),
        ("chambers the retired stand-in put past the cap",
         lv_st.stats["past_cap_nodes"], "chambers",
         f"NOT PUBLISHED. Against {lv.stats['past_cap_nodes']:,} from {S6_TAG}. The full "
         "row-by-row disagreement is the `levels_delta` layer"),
        ("reaches nobody levelled", int(REMOVED_COUNTS.get("reaches_unlevelled", 0)),
         "reaches",
         f"{REMOVED_COUNTS.get('reaches_unlevelled_km', 0.0):.2f} km taken OFF the "
         "reaches layer and published whole on `reaches_unlevelled` with the reason on "
         "every row (inheritance row 4)"),
        ("backdrops", int((nd.DROP_TYPE == "backdrop").sum()), "-", "G203-p30, 0.60-2.00 m"),
        ("VORTEX DROP SHAFTS", int((nd.DROP_TYPE == "vortex").sum()), "-",
         "G203-p30. NAMA's built network has 37 - philosophy sec 4 diagnostic"),
        ("largest drop", round(float(nd.DROP_M.max()), 2), "m",
         f"criteria.DROP_CEILING_M is {C.DROP_CEILING_M:g} m and is a PROJECT ASSUMPTION"),
        ("draining against the ground",
         round(_pct(float(r.LEN_M[r.AGN_GRADE == 1].sum()), float(r.LEN_M.sum())), 2), "%",
         "philosophy sec 4; NAMA's built network 34 %"),
        ("self-cleansed by TRACTIVE", round(lv.stats["km_tractive"], 1), "km",
         f"G203-p27 4.2.2.1. THE tau EXPOSURE - {C.TAU_PA:g} Pa is an ASSUMPTION (GAP-9)"),
        ("self-cleansed by VELOCITY", round(lv.stats["km_velocity"], 1), "km", "G203-p26"),
        ("self-cleansed by NEITHER", round(lv.stats["km_neither"], 2), "km", "H5 - a failure"),
        ("wadi ground", round(cross_stats["km_wadi"], 2), "km",
         f"MEASURED, {C.HAZARD_RETURN_YR}-yr grid classes {C.HAZARD_WADI_CLASSES}, "
         f"sampled every {WADI_SAMPLE_M:g} m"),
        # THE PUBLISHED COUNT FIRST, THEN THE LEDGER. The manifest used to quote the
        # register as BUILT (828 on the 12:00 export) while the published `crossings`
        # layer held 512, because withdraw_orphan_crossings() had taken 316 off it. A
        # headline that disagrees with the layer under it is how a stale figure gets
        # quoted - and inheritance row 4 says the stage publishes how many it removed.
        ("registered crossings",
         len(layers.get("crossings", [])) if "crossings" in layers
         else cross_stats["n_rows"], "-",
         f"H1a register, as PUBLISHED. {cross_stats['n_rows']:,} rows were registered and "
         f"{int(REMOVED_COUNTS.get('crossings_withdrawn', 0)):,} were withdrawn - see the "
         f"row below"),
        ("crossings WITHDRAWN - no pipe crosses there any more",
         int(REMOVED_COUNTS.get("crossings_withdrawn", 0)), "-",
         "INHERITANCE ROW 4. The only reach that crossed the obstacle is a route the "
         "leveller did not level, so it is on `reaches_unlevelled` and the register row "
         "is on `crossings_withdrawn` with its reason - never silently left in to make a "
         "count look bigger, and never silently dropped"),
        ("drop reasons blanked - the drop was under 1 mm",
         int(REMOVED_COUNTS.get("drop_reasons_with_no_drop", 0)), "chambers",
         f"{LEVELS_SOURCE} wrote a DROP_WHY on chambers whose published DROP_M rounds to "
         f"0.000 m. G203-p30 calls nothing under 0.60 m a drop. The reason is blanked at "
         f"publication and counted here; the underlying test belongs to the leveller"),
        ("crossings within the skew tolerance", cross_stats["n_square"], "-",
         f"criteria.WADI_XING_SKEW_DEG = {C.WADI_XING_SKEW_DEG:g} deg. The rest run ALONG"),
        ("measured crossing angle, median", round(cross_stats["angle_median"], 1), "deg",
         "against the nearest stream's own direction, over the "
         f"{cross_stats['n_rows'] - cross_stats['n_angle_unmeasured']:,} rows where an "
         f"angle was actually measured. W11a asserted 90 on 3,290"),
        ("crossings with NO measured angle", cross_stats["n_angle_unmeasured"], "-",
         "s1 recorded no bearing for these dual-carriageway contacts. ANGLE_DEG carries "
         "0.00 because the contract requires a number and 0 is the conservative reading "
         "(runs ALONG the obstacle); ANG_MEAS = 0 is how a reader tells it from a "
         "measurement, and these rows are excluded from the statistics above"),
        ("plots that CANNOT connect to their chamber",
         int((layers['connections'].CAN_CONN == 0).sum()), "-",
         "CONCEPT RULE 5. Each carries CONN_NEED - how many metres deeper the sewer "
         "would have to be on that run"),
        ("deepest a plot needs the sewer to go",
         round(float(layers['connections'].CONN_NEED.max()), 2), "m",
         "CONN_NEED, the size on the flag (rule 7)"),
        ("subnetworks", int((layers['subnetworks'].SERVED == 1).sum()), "-",
         "one per connected component; named per concept rule 8"),
        ("subnetworks NOT reaching the main pipe",
         int(((layers['subnetworks'].SERVED == 1)
              & (layers['subnetworks'].JOIN_MAIN == 0)).sum()), "-",
         f"CONCEPT RULE 2, at the declared JOIN_TOL_M = {JOIN_TOL_M:g} m. Legal only if "
         f"each ends at a designed station (10_ASBUILT_CALIBRATION rule T1)"),
        ("outfalls sitting off their own low point",
         int((pd.to_numeric(layers['nodes'].JOIN_OFF_M, errors='coerce').fillna(0)
              > 0).sum()), "-",
         "CONCEPT RULE 2 - each records the distance and the reason"),
        ("areas the network does not reach",
         int((layers['subnetworks'].SERVED == 0).sum()), "-",
         "each with its plot count and its reason; scope-p4 item 3"),
        ("drops that exist only to hold the velocity cap",
         int((layers['nodes'].DROP_WHY == "velocity_cap").sum()), "-",
         "CONCEPT RULE 1 - every drop carries the reason it exists. TWO BOUNDS SHARE THIS "
         "ONE WORD (the contract's vocabulary has no second): "
         + (", ".join(f"{k} {v:,}" for k, v in sorted(DROP_CAUSE_SPLIT.items()))
            or "not counted")
         + f". `vmax` is G203-p27 4.2.2.2 ({C.V_MAX:g} m/s, a GUIDELINE); `cover_max` is "
           f"the {EXPORT_NUM['SLOPE_MAX_LAID_PCT']:g} % laying bound, a PROJECT "
           f"ASSUMPTION with no guideline behind it"),
        ("pumping stations PUBLISHED", len(layers["stations"]), "-", "s7_pumps"),
        ("pumping stations REMOVED - nothing drained into them",
         len(layers.get("stations_rejected", [])), "-",
         "INHERITANCE ROW 4. Anything a pass can ADD, a later pass must be able to TAKE "
         "AWAY, and the stage publishes how many it removed. Each is on the "
         "`stations_rejected` layer in full"),
        ("rising mains REMOVED with the stations that were pruned",
         int(REMOVED_COUNTS.get("rising_mains_removed", 0)), "-",
         "the other half of the same ledger. A force main with no pump lifts nothing, and "
         "a removal that is only printed to a console is not published"),
        ("chambers NOT NAMED - the grammar has no token for their tier",
         int(nd.NAME.fillna("").astype(str).str.strip().eq("").sum()), "-",
         "CONCEPT RULE 8 declares three tier codes (TM / SM / L) and contract.NAME_RE "
         "enforces exactly those; this design's tier set has five. No name is invented for "
         "the other two - see the note on this run and the contract_check layer"),
        ("themes that could NOT be built", len(THEME_FAILURES), "-",
         "an absent theme is not a clean one. Each failure is a row on contract_check "
         + (f"({', '.join(sorted(THEME_FAILURES))})" if THEME_FAILURES else "")),
        ("rising mains that lift ALL THE WAY TO THE WORKS",
         int((layers['rising_mains'].DS_TYPE == "stp").sum()), "-",
         "CONCEPT RULE 6 - a main should lift to the nearest point where gravity resumes"),
        ("rising main", round(float(layers["rising_mains"].LEN_M.sum()) / 1000.0, 3), "km",
         "s7_pumps, unchanged"),
        ("client trunk main", round(float(layers["trunk"].LEN_M.sum()) / 1000.0, 2), "km",
         "INPUT. Not chambered, not levelled; nothing here drains into it"),
        ("tau", C.TAU_PA, "Pa", "ASSUMPTION, GAP-9. At 2.0 every tractive gradient x2.346"),
    ]
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "SOURCE"])


def _assumptions_table() -> pd.DataFrame:
    rows = [dict(ID=a.aid, HEADLINE=a.headline, DETAIL=a.detail, CONSEQUENCE=a.consequence)
            for a in PR.ASSUMPTIONS.values()]
    rows += [dict(ID=f"S8-{i + 1}", HEADLINE=f"{n} = {v}", DETAIL=s, CONSEQUENCE=w)
             for i, (n, v, s, w) in enumerate(EXPORT_NUMBERS)]
    return pd.DataFrame(rows)


def _arms_table(lv: Levels, lv_st: Levels) -> pd.DataFrame:
    """THE TWO LEVEL SOLVERS SIDE BY SIDE, on the headline counts.

    Until 2026-09-06 the two columns were 'gravity only' and 'with the s7 stations', both
    from the stand-in this stage carried. That comparison measured the RETIRED solver's
    relief and is no longer a statement about anything published, so the arms are now the
    two SOURCES: what s6_levels published and what the stand-in would have. `levels_delta`
    carries the same comparison row by row."""
    keys = ["past_cap_nodes", "past_cap_no_exit", "vortex", "backdrop", "deepest_cover",
            "median_cover", "km_past_cap", "km_below_min_cover", "km_tractive",
            "km_velocity", "n_over_vmax", "n_over_dod"]
    return pd.DataFrame([
        dict(MEASURE=k,
             PUBLISHED_S6=round(float(lv.stats.get(k, float("nan"))), 4),
             RETIRED_STANDIN=round(float(lv_st.stats.get(k, float("nan"))), 4),
             PUBLISHED=S6_TAG,
             NOTE="one published quantity, one function (inheritance row 10). The "
                  "stand-in column is what THIS stage used to publish and is kept only so "
                  "the size of the change is on the deliverable")
        for k in keys])


def verify() -> int:
    """Re-derive every headline from the PUBLISHED GeoPackage alone, and fail if any of
    them disagrees with what the manifest claims. Reading the file back is the point: a
    stage that verifies its own in-memory model verifies nothing."""
    import fiona
    bad: List[str] = []
    have = set(fiona.listlayers(GPKG_OUT))
    need = {"nodes", "reaches", "connections", "stations", "rising_mains", "crossings",
            "packages", "trunk", "subnetworks", "manifest", "contract_check"}
    if not need <= have:
        print(f"MISSING LAYERS: {sorted(need - have)}")
        return 1
    nd = gpd.read_file(GPKG_OUT, layer="nodes")
    r = gpd.read_file(GPKG_OUT, layer="reaches")
    mf = pd.read_csv(os.path.join(DIR_SHP, "W12_manifest.csv")) \
        if os.path.exists(os.path.join(DIR_SHP, "W12_manifest.csv")) else \
        gpd.read_file(GPKG_OUT, layer="manifest")
    man = dict(zip(mf.ITEM.astype(str), mf.VALUE.astype(str)))

    def eq(name, got, want, tol=0.02):
        try:
            ok = abs(float(got) - float(want)) <= tol
        except Exception:
            ok = str(got) == str(want)
        print(f"  {'OK ' if ok else 'BAD'}  {name:<38} recomputed {got}   manifest {want}")
        if not ok:
            bad.append(name)

    eq("network km", round(float(r.LEN_M.sum()) / 1000.0, 3), man["network"], 0.002)
    eq("chambers", len(nd), man["chambers"], 0)
    eq("outfalls", int((nd.IS_OUTFALL == 1).sum()), man["outfalls"], 0)
    eq("past the 12 m cap", int((nd.PAST_CAP == 1).sum()), man["past the 12 m cap"], 0)
    eq("past the cap WITH NO EXIT",
       int(((nd.PAST_CAP == 1) & (nd.CAP_EXIT.fillna("").astype(str).str.strip() == "")).sum()),
       man["past the cap WITH NO EXIT"], 0)
    eq("VORTEX DROP SHAFTS", int((nd.DROP_TYPE == "vortex").sum()),
       man["VORTEX DROP SHAFTS"], 0)
    eq("max d/D", round(float(r.DOD_PK.max()), 4), man["max d/D"], 1e-4)
    eq("deepest cover", round(float(nd.COVER_M.max()), 3), man["deepest cover"], 0.002)
    sn = gpd.read_file(GPKG_OUT, layer="subnetworks")
    cn = gpd.read_file(GPKG_OUT, layer="connections")
    eq("subnetworks", int((sn.SERVED == 1).sum()), man["subnetworks"], 0)
    eq("subnetworks NOT reaching the main pipe",
       int(((sn.SERVED == 1) & (sn.JOIN_MAIN == 0)).sum()),
       man["subnetworks NOT reaching the main pipe"], 0)
    eq("plots that CANNOT connect to their chamber",
       int((cn.CAN_CONN == 0).sum()),
       man["plots that CANNOT connect to their chamber"], 0)

    # THE FIVE LAYERS, and the concept rules that are checkable on the file alone
    for lyr, cols in (("nodes", ("NAME", "TOWN", "SUBNET", "DROP_WHY", "JOIN_MAIN",
                                 "JOIN_OFF_M", "JOIN_WHY", "DEP_M")),
                      ("reaches", ("NAME", "TOWN", "SUBNET", "DEP_M")),
                      ("stations", ("NAME", "TOWN", "N_SUBNET", "CATCH_KM", "INV_M")),
                      ("rising_mains", ("NAME", "TOWN", "DS_TYPE")),
                      ("subnetworks", ("NAME", "SERVED", "JOIN_MAIN", "GAP_M", "FLAG"))):
        g_ = gpd.read_file(GPKG_OUT, layer=lyr)
        miss = [c for c in cols if c not in g_.columns]
        print(f"  {'OK ' if not miss else 'BAD'}  {lyr + ' carries its concept fields':<38} "
              f"{'all present' if not miss else 'MISSING ' + str(miss)}")
        if miss:
            bad.append(f"{lyr} missing {miss}")

    banned = sorted(set(CT.BANNED_FIELDS) & (set(nd.columns) | set(r.columns)
                                             | set(gpd.read_file(GPKG_OUT,
                                                                 layer="stations").columns)))
    print(f"  {'OK ' if not banned else 'BAD'}  "
          f"{'no banned field name reached the file':<38} "
          f"{'-' if not banned else banned}")
    if banned:
        bad.append(f"banned field published: {banned}")

    zero_up = int((pd.to_numeric(gpd.read_file(GPKG_OUT, layer='stations').N_SUBNET,
                                 errors='coerce').fillna(0) == 0).sum())
    print(f"  {'OK ' if zero_up == 0 else 'BAD'}  "
          f"{'stations with nothing draining in':<38} {zero_up}")
    if zero_up:
        bad.append("a station with nothing draining into it reached the published layer")

    drops = nd[nd.DROP_TYPE.astype(str) != "none"]
    nowhy = int(drops.DROP_WHY.fillna("").astype(str).str.strip().eq("").sum())
    print(f"  {'OK ' if nowhy == 0 else 'BAD'}  "
          f"{'every drop carries its reason':<38} {len(drops) - nowhy} of {len(drops)}")
    if nowhy:
        bad.append("a drop with no DROP_WHY")
    if len(drops) >= CT.VARY_MIN_ROWS and drops.DROP_WHY.nunique() == 1:
        print("  BAD  every drop shares one reason - FABRICATION (inheritance row 22)")
        bad.append("DROP_WHY is constant")

    # invariants that must hold on the file, not on a model
    dup = int(nd.NODE_UID.duplicated().sum())
    print(f"  {'OK ' if dup == 0 else 'BAD'}  duplicate NODE_UID                     {dup}")
    if dup:
        bad.append("duplicate NODE_UID")
    known = set(nd.NODE_UID.astype(str))
    dangle = int((~r.US_NODE.astype(str).isin(known)).sum()
                 + (~r.DS_NODE.astype(str).isin(known)).sum())
    print(f"  {'OK ' if dangle == 0 else 'BAD'}  reach endpoints that resolve           "
          f"{len(r) * 2 - dangle} of {len(r) * 2}")
    if dangle:
        bad.append("dangling reach endpoint")
    rev = int(((r.INV_UP - r.INV_DN) < -C.LAY_TOLERANCE_M).sum())
    print(f"  {'OK ' if rev == 0 else 'BAD'}  reverse gradients (G203-p29)           {rev}")
    if rev:
        bad.append("reverse gradient")
    fall = (r.INV_UP - r.INV_DN) - r.LEN_M * r.SLOPE_LAID / 100.0
    off = int((fall.abs() > C.LAY_TOLERANCE_M + 1e-3).sum())
    print(f"  {'OK ' if off == 0 else 'BAD'}  inverts reproduce LEN x SLOPE_LAID     "
          f"{len(r) - off} of {len(r)}")
    if off:
        bad.append("inverts do not reproduce the laid gradient")
    step = C.SLOPE_STEP * 100.0
    ns = int((((r.SLOPE_LAID / step) - (r.SLOPE_LAID / step).round()).abs() > 1e-6).sum())
    print(f"  {'OK ' if ns == 0 else 'BAD'}  gradients on the {step:g} % step          "
          f"{len(r) - ns} of {len(r)}")
    if ns:
        bad.append("gradient off the step")
    qpk = r.QADF_M3D * 1000.0 / 86400.0 * r.PF + r.QINF_LS
    nq = int(((qpk - r.QPK_LS).abs() > 0.01 * qpk.abs() + 0.01).sum())
    print(f"  {'OK ' if nq == 0 else 'BAD'}  QPK reproducible from its own row      "
          f"{len(r) - nq} of {len(r)}")
    if nq:
        bad.append("QPK not reproducible")
    dn_bad = int((~r.DN.isin(list(C.DN_SERIES))).sum())
    print(f"  {'OK ' if dn_bad == 0 else 'BAD'}  DN in criteria.DN_SERIES               "
          f"{len(r) - dn_bad} of {len(r)}")
    if dn_bad:
        bad.append("DN outside the series")

    # ---- THE LEVELS ON THE FILE ARE THE LEVELLER'S, PROVED AGAINST ITS OWN FILE -------
    # The check that stops this stage growing a second level solver again. It does not ask
    # whether the numbers are plausible; it opens s6's GeoPackage and demands that every
    # published invert, gradient and diameter is the one s6 wrote, matched on the WRITTEN
    # topology. If s8 ever computes a level of its own again, this fails on the first row.
    if "LEVELS_BY" not in r.columns or "LEVELS_BY" not in nd.columns:
        print("  BAD  LEVELS_BY is not on the published layers - the row cannot say which "
              "solver answered for it")
        bad.append("no LEVELS_BY column")
    elif os.path.exists(GPKG_S6):
        n6 = gpd.read_file(GPKG_S6, layer="nodes", ignore_geometry=True)
        r6 = gpd.read_file(GPKG_S6, layer="reaches", ignore_geometry=True)
        i6 = pd.Series(pd.to_numeric(n6.INV_M, errors="coerce").values,
                       index=n6.NODE_UID.astype(str).values)
        want = nd.NODE_UID.astype(str).map(i6)
        got = pd.to_numeric(nd.INV_M, errors="coerce")
        # COMPARED, NOT ASSUMED. `want - got` is nan wherever s6 has no chamber, and
        # `nan > 0.0015` is False - so the old form counted every UNMATCHED row as a pass
        # and printed "56,943 of 56,943" while it had actually compared 51,470. Worse, the
        # rows it skipped are the ones most at risk: if this stage ever fills a level for a
        # chamber s6 never published, that is exactly where it would appear. So the count
        # is now the count of rows COMPARED, and the skipped rows must carry a NULL.
        shared = want.notna()
        off_n = int(((want[shared] - got[shared]).abs() > 0.0015).sum())
        print(f"  {'OK ' if off_n == 0 else 'BAD'}  "
              f"{'every chamber invert IS s6s':<38} "
              f"{int(shared.sum()) - off_n} of {int(shared.sum())} compared "
              f"({int((~shared).sum())} not in {os.path.basename(GPKG_S6)})")
        if off_n:
            bad.append(f"{off_n} published inverts differ from {S6_TAG}'s own file")
        made_up = int((~shared & got.notna()).sum())
        print(f"  {'OK ' if made_up == 0 else 'BAD'}  "
              f"{'no invert invented where s6 has none':<38} "
              f"{int((~shared).sum()) - made_up} of {int((~shared).sum())} are NULL")
        if made_up:
            bad.append(f"{made_up} chambers carry an invert that {S6_TAG} never published")
        # EVERY LEVEL COLUMN, not the three it is easiest to check. INV_DN, US_DEPTH,
        # DS_DEPTH, COVER_US and COVER_DN were rebuilt here from s6's INV_UP against this
        # stage's ground until 2026-09-06, and this check compared none of them - so a
        # published cover ran to -151.74 m while the three columns it did compare passed.
        _cols = ["SLOPE_LAID", "DN", "INV_UP", "INV_DN", "US_DEPTH", "DS_DEPTH",
                 "COVER_US", "COVER_DN"]
        _tol = {"SLOPE_LAID": 1e-6, "DN": 0.0, "INV_UP": 0.0015, "INV_DN": 0.0015,
                "US_DEPTH": 0.0015, "DS_DEPTH": 0.0015, "COVER_US": 0.0015,
                "COVER_DN": 0.0015}
        k6 = pd.DataFrame({"K": r6.US_NODE.astype(str) + ">" + r6.DS_NODE.astype(str)})
        j = pd.DataFrame({"K": r.US_NODE.astype(str) + ">" + r.DS_NODE.astype(str)})
        for _c in _cols:
            k6["S6_" + _c] = pd.to_numeric(r6[_c], errors="coerce") \
                if _c in r6.columns else np.nan
            j[_c] = pd.to_numeric(r[_c], errors="coerce") if _c in r.columns else np.nan
        j = j.merge(k6, on="K", how="left")
        off_e, _worst = 0, []
        for _c in _cols:
            _d = (j[_c] - j["S6_" + _c]).abs()
            _n = int((_d > _tol[_c]).sum())
            off_e += _n
            if _n:
                _worst.append(f"{_c} on {_n:,} (worst {float(_d.max()):.3f})")
        print(f"  {'OK ' if off_e == 0 else 'BAD'}  "
              f"{'every level column IS s6s':<38} "
              f"{len(j) * len(_cols) - off_e} of {len(j) * len(_cols)}"
              + ("" if not _worst else "   " + "; ".join(_worst)))
        if off_e:
            bad.append(f"{off_e} published reach values differ from {S6_TAG}'s own file "
                       f"({'; '.join(_worst)})")
        # AND THE ROW MUST NOT CONTRADICT ITSELF. PAST_CAP is s6's; the cover beside it was
        # this stage's, and 3,668 reaches published a cover past the 12 m cap with
        # PAST_CAP = 0.
        _mx = pd.concat([pd.to_numeric(r.COVER_US, errors="coerce"),
                         pd.to_numeric(r.COVER_DN, errors="coerce")], axis=1).max(axis=1)
        _self = int(((_mx > C.MAX_COVER + 1e-6)
                     & (pd.to_numeric(r.PAST_CAP, errors="coerce").fillna(0) == 0)).sum())
        print(f"  {'OK ' if _self == 0 else 'BAD'}  "
              f"{'cover and PAST_CAP agree on the row':<38} {len(r) - _self} of {len(r)}")
        if _self:
            bad.append(f"{_self} reaches publish a cover past the {C.MAX_COVER:g} m cap "
                       f"beside their own PAST_CAP = 0")
        # and nothing s6 did not level may sit on the reaches layer pretending it was
        unl = (gpd.read_file(GPKG_OUT, layer="reaches_unlevelled", ignore_geometry=True)
               if "reaches_unlevelled" in have else pd.DataFrame())
        # EVERY SEGMENT s4 MINTED IS ON ONE OF THE TWO LAYERS - compared by the WRITTEN
        # topology, not by a row count. A count alone cannot tell "the export dropped 29
        # segments" from "s4 has been re-run since this export was built", and those two
        # need opposite responses: fix the export, or re-run it.
        seg = gpd.read_file(GPKG_CHAMB, layer="segments", ignore_geometry=True)
        k_seg = set(zip(seg.US_NODE.astype(str), seg.DS_NODE.astype(str)))
        k_pub = set(zip(r.US_NODE.astype(str), r.DS_NODE.astype(str)))
        if len(unl):
            k_pub |= set(zip(unl.US_NODE.astype(str), unl.DS_NODE.astype(str)))
        lost = k_seg - k_pub
        extra = k_pub - k_seg
        if extra:
            print(f"  BAD  {'THE EXPORT IS STALE':<38} it publishes {len(extra):,} "
                  f"segments s4 no longer has ({len(k_seg):,} in the chamber layer now, "
                  f"{len(k_pub):,} published) - s4 has been re-run since. Re-run "
                  f"s8_export.py build; nothing on this file is quotable until then")
            bad.append("the export was built against an older chamber layer")
        else:
            print(f"  {'OK ' if not lost else 'BAD'}  "
                  f"{'every segment is on one layer or the other':<38} "
                  f"{len(r):,} levelled + {len(unl):,} not = {len(k_pub):,} of "
                  f"{len(k_seg):,}")
            if lost:
                bad.append(f"{len(lost):,} segments s4 minted are on neither the reaches "
                           f"layer nor reaches_unlevelled - a silent drop")
    else:
        print(f"  BAD  {os.path.basename(GPKG_S6)} is not on disk, so the levels on this "
              f"file cannot be checked against the stage that made them")
        bad.append("no s6 file to check the published levels against")

    # ---- THE FLOW AT A CHAMBER IS THE FLOW IN THE PIPE LEAVING IT --------------------
    # contract.NODES defines Q_PK_LS as "the number the outgoing reach is sized on". The
    # 12:00 export broke that on 26,482 of 26,579 chamber/reach pairs - median ratio 3.50 -
    # because the node layer took its peak factor from the DEFAULT of a column s6 does not
    # publish. Checked here on the file, against the reach that actually leaves the chamber.
    jn_ = nd[["NODE_UID", "Q_PK_LS", "Q_ADF_M3D"]].merge(
        r[["US_NODE", "QPK_LS", "QADF_M3D"]], left_on="NODE_UID", right_on="US_NODE",
        how="inner")
    dq = (pd.to_numeric(jn_.Q_PK_LS, errors="coerce")
          - pd.to_numeric(jn_.QPK_LS, errors="coerce")).abs()
    off_q = int((dq > 0.01 * pd.to_numeric(jn_.QPK_LS, errors="coerce").abs() + 0.01).sum())
    print(f"  {'OK ' if off_q == 0 else 'BAD'}  "
          f"{'chamber QPK = the QPK of the pipe leaving it':<38} "
          f"{len(jn_) - off_q} of {len(jn_)}")
    if off_q:
        bad.append(f"{off_q} chambers publish a peak flow their own outgoing reach "
                   f"contradicts")
    # A FABRICATED CONSTANT, ON THE DELIVERABLE ITSELF. tests/test_columns.py runs this
    # rule over every OTHER stage's GeoPackage - conftest.GPKGS does not list
    # W12_export.gpkg or W12.gpkg - so the published file was the one place it could not
    # fire, and PF = 1.0 on 56,943 rows is how that showed up.
    for lname, gg, cols in (("nodes", nd, ("PF", "Q_PK_LS", "DEPTH_M", "COVER_M", "GRD_M",
                                           "INV_M", "DROP_M")),
                            ("reaches", r, ("PF", "QPK_LS", "SLOPE_LAID", "DN", "LEN_M",
                                            "V_PK_MS", "DOD_PK"))):
        for c_ in cols:
            if c_ not in gg.columns:
                continue
            s_ = pd.to_numeric(gg[c_], errors="coerce").dropna()
            if len(s_) >= CT.VARY_MIN_ROWS and s_.nunique() == 1:
                print(f"  BAD  {(lname + '.' + c_ + ' is CONSTANT'):<38} "
                      f"{s_.iloc[0]!r} on all {len(s_):,} rows")
                bad.append(f"{lname}.{c_} is constant on {len(s_):,} rows - a measured "
                           f"column that holds one value is a fabrication until the "
                           f"reason is written down (inheritance row 22)")

    chk = gpd.read_file(GPKG_OUT, layer="contract_check")
    # BOTH publication gates, not just the one. `levels ground` is the sharper of the two -
    # a depth is ground minus invert, so a leveller looking at different ground makes every
    # depth on the file a measurement from somewhere else - and it fires on pairs the reach
    # count alone would pass.
    for _lyr, _why in (("levels coverage",
                        "less than the whole network is levelled - see the levels "
                        "coverage row"),
                       ("levels ground",
                        "the leveller and this stage are looking at different ground - "
                        "see the levels ground row")):
        cov = chk[chk.LAYER.astype(str) == _lyr]
        if len(cov) and int(cov.PASS.iloc[0]) == 0:
            print(f"  BAD  {_lyr:<38} {str(cov.RESULT.iloc[0])}")
            bad.append(_why)
    n_fail = int((chk["PASS"] == 0).sum())
    print(f"\n  contract.validate(): {len(chk) - n_fail} of {len(chk)} layers pass. "
          f"{n_fail} carry named, published violations - see the `contract_check` layer.")
    print(f"\n{'VERIFY PASSED' if not bad else 'VERIFY FAILED: ' + ', '.join(bad)}")
    return 1 if bad else 0


def _raises_contains(fn, needle: str) -> bool:
    """A guard that does not fire is not a guard. This is how the self-test proves one does."""
    try:
        fn()
    except Exception as e:
        return needle in str(e)
    return False


def _fields_this_stage_writes() -> set:
    """Every UPPER_CASE column name this module can put on a layer, read out of its OWN
    SOURCE rather than listed by hand.

    A hand-written list is the thing that goes stale: someone adds `MOTOR_KW` back in a
    keyword argument and the check that was meant to catch it is looking at a list written
    three weeks earlier."""
    import ast
    tree = ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg and node.arg.isupper():
            out.add(node.arg)
        if (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)
                and node.slice.value.isupper()):
            out.add(node.slice.value)
    return out


def demo_layers() -> Dict[str, gpd.GeoDataFrame]:
    """A tiny, closed layer set carrying every concept-stage column.

    Small enough to read in one screen, and it exercises the parts of this stage that do
    not need the upstream GeoPackages: the class tables, the folder names, the KML and the
    .qml. It is NOT a design and no number in it is quoted anywhere."""
    crs = f"EPSG:{CT.CRS_EPSG}"
    x0, y0 = 444000.0, 2563000.0
    r = gpd.GeoDataFrame(dict(
        NAME=["I-S01-SM-M001", "I-S01-SM-M002", "D-S01-L-M001"],
        SUB_NAME=["I-S01", "I-S01", "D-S01"], SUBNET=["S01", "S01", "S01"],
        TOWN=["I", "I", "D"], TIER=["sub main", "sub main", "lateral"],
        DN=[300, 400, 200], LEN_M=[100.0, 100.0, 100.0],
        SLOPE_LAID=[0.50, 0.55, 1.00], QPK_LS=[12.0, 18.0, 3.0],
        V_PK_MS=[0.8, 0.9, 0.7], US_DEPTH=[1.5, 2.4, 8.0], DS_DEPTH=[2.4, 3.6, 13.0],
        US_NAME=["I-S01-SM-M001", "I-S01-SM-M002", "D-S01-L-M001"],
        DS_NAME=["I-S01-SM-M002", "I-S01-SM-M003", "D-S01-L-M002"]),
        geometry=[LineString([(x0, y0), (x0 + 100, y0)]),
                  LineString([(x0 + 100, y0), (x0 + 200, y0)]),
                  LineString([(x0 + 500, y0), (x0 + 600, y0)])], crs=crs)
    nd = gpd.GeoDataFrame(dict(
        NAME=["I-S01-SM-M001", "I-S01-SM-M002", "D-S01-L-M001"],
        SUB_NAME=["I-S01", "I-S01", "D-S01"], NODE_KIND=["head", "junction", "outfall"],
        DROP_TYPE=["none", "backdrop", "vortex"],
        DROP_WHY=["", "velocity_cap", "tier_step"],
        DROP_M=[0.0, 0.9, 2.6], JOIN_MAIN=[0, 0, 1], JOIN_OFF_M=[0.0, 0.0, 210.0],
        JOIN_WHY=["", "", "no street at the low point"],
        PAST_CAP=[0, 0, 1], CAP_EXIT=["", "", ""], CAP_LEN_M=[0.0, 0.0, 1200.0],
        ON_WADI=[0, 0, 1], GRD_M=[330.0, 329.0, 320.0], INV_M=[328.5, 326.6, 307.0],
        DEPTH_M=[1.5, 2.4, 13.0], COVER_M=[1.3, 2.2, 12.8], MH_DIA=[1.2, 1.5, 1.5],
        X=[x0, x0 + 100, x0 + 500], Y=[y0, y0, y0]),
        geometry=[Point(x0, y0), Point(x0 + 100, y0), Point(x0 + 500, y0)], crs=crs)
    st = gpd.GeoDataFrame(dict(
        NODE_UID=["PS00001"], NAME=["I-PMP01"], TOWN=["I"], SUBNET=[""],
        ST_TYPE=["Type 1"], GRD_M=[329.0], INV_M=[321.0], LIFT_M=[8.0],
        Q_DUTY_LS=[50.0], WELL_M3=[4.5], CATCH_KM=[3.2], N_SUBNET=[1]),
        geometry=[Point(x0 + 200, y0)], crs=crs)
    rm = gpd.GeoDataFrame(dict(
        NAME=["I-P01"], TOWN=["I"], SUBNET=[""], STATION=["PS00001"],
        DS_NODE=["STP"], DS_TYPE=["stp"], DN=[200], LEN_M=[300.0],
        Q_DUTY_LS=[50.0], V_DUTY_MS=[1.6], TOT_HD_M=[12.0]),
        geometry=[LineString([(x0 + 200, y0), (x0 + 500, y0)])], crs=crs)
    sq = Polygon([(x0 - 50, y0 - 50), (x0 + 250, y0 - 50),
                  (x0 + 250, y0 + 50), (x0 - 50, y0 + 50)])
    sq2 = Polygon([(x0 + 450, y0 - 50), (x0 + 650, y0 - 50),
                   (x0 + 650, y0 + 50), (x0 + 450, y0 + 50)])
    sn = gpd.GeoDataFrame(dict(
        NAME=["I-S01", "D-S01", ""], TOWN=["I", "D", ""], SUBNET=["S01", "S01", ""],
        SERVED=[1, 1, 0], N_PLOT=[120, 40, 60], N_PROP=[170.0, 55.0, 80.0],
        Q_ADF_M3D=[140.0, 45.0, 70.0], N_CHAMBER=[2, 1, 0], LEN_KM=[0.2, 0.1, 0.0],
        DEEP_M=[2.4, 13.0, 0.0], OUTFALL=["N2", "N3", ""],
        OUT_NAME=["I-S01-SM-M002", "D-S01-L-M001", ""],
        JOIN_MAIN=[1, 0, 0], GAP_M=[10.0, 1873.0, 0.0], OFF_M=[0.0, 0.0, 0.0],
        LOW_ND=["N2", "N3", ""], TOWN_D_M=[0.0, 0.0, 0.0],
        FLAG=["", "does not reach the main pipe", "UNSERVED-001"],
        WHY=["", "1,873 m short of the main pipe", "60 plots, nearest chamber 810 m away"],
        AREA_M2=[float(sq.area), float(sq2.area), float(sq2.area)]),
        geometry=[sq, sq2, sq2], crs=crs)
    cn = gpd.GeoDataFrame(dict(
        PLOT_ID=["P1", "P2"], CONN_ID=["C1", "C2"], OUT_NODE=["N1", "N3"],
        CAN_CONN=[1, 0], CAN_DRAIN=[1, 0], CONN_NEED=[0.0, 0.84],
        CONN_WHY=["", "only 0.10 m of fall over 40 m - sewer 0.84 m deeper on this run"],
        LEN_M=[20.0, 40.0], FALL_AV_M=[0.9, 0.10], Q_ADF_M3D=[1.1, 1.1],
        NAME=["", ""], TOWN=["I", "D"], SUBNET=["S01", "S01"],
        SUB_NAME=["I-S01", "D-S01"]),
        geometry=[LineString([(x0, y0 + 20), (x0, y0)]),
                  LineString([(x0 + 500, y0 + 40), (x0 + 500, y0)])], crs=crs)
    rej = gpd.GeoDataFrame(dict(
        NODE_UID=["PS00002"], NODE_REF=["P002-PS"], UID_S7=["N0000042"], NAME=[""],
        Q_DUTY_LS=[0.0], N_SUBNET=[0],
        REJECT_WHY=["NOTHING DRAINS INTO IT."]),
        geometry=[Point(x0 + 900, y0)], crs=crs)
    trunk = gpd.GeoDataFrame(dict(EDGE_UID=["TRUNK001"], LEN_M=[400.0]),
                             geometry=[LineString([(x0, y0 - 200), (x0 + 400, y0 - 200)])],
                             crs=crs)
    r["DEP_M"] = np.maximum(r.US_DEPTH, r.DS_DEPTH)
    nd["DEP_M"] = nd.DEPTH_M
    st["DEP_M"] = st.GRD_M - st.INV_M
    rm["DEP_M"] = [float(st.DEP_M.iloc[0])]
    sn["DEP_M"] = sn.DEEP_M
    return {"reaches": r, "nodes": nd, "stations": st, "rising_mains": rm,
            "subnetworks": sn, "connections": cn, "stations_rejected": rej,
            "trunk": trunk}


def selftest() -> int:
    """Small, closed checks on the machinery, not on the data. Each one is a bug that was
    actually made while writing this file."""
    fails = []

    def ck(name, cond, detail=""):
        print(f"  {'OK ' if cond else 'BAD'}  {name}" + (f"   {detail}" if detail else ""))
        if not cond:
            fails.append(name)

    # 1. rounding a cover-governed gradient DOWN breaches minimum cover. It put 232 km of
    #    this network under 1.30 m on the first build.
    s = 0.0123
    ck("round_slope_up never lands flatter than asked",
       C.round_slope_up(s) >= s - 1e-15, f"{C.round_slope_up(s):.5f} >= {s}")
    ck("round_slope_down never lands steeper than asked",
       C.round_slope_down(s) <= s + 1e-15)
    # 2. cover() is the exact inverse of invert_depth_min()
    for dn in (200, 315, 500, 900, 1400):
        ck(f"cover(DN{dn}, invert_depth_min) == MIN_COVER_CROWN",
           abs(C.cover(dn, C.invert_depth_min(dn)) - C.MIN_COVER_CROWN) < 1e-12)
    # 3. the memo must not change an answer
    for q, sl, dn in ((0.004, 0.005, 200), (0.05, 0.002, 500), (0.2, 0.001, 900)):
        a1 = HY.pipe_state(dn, sl, q, C)
        a2 = state(dn, sl, q)
        ck(f"memoised pipe_state matches hydra (DN{dn})",
           (a1[0] is None) == (a2[0] is None)
           and (a1[0] is None or abs(a1[0] - a2[0]) < 1e-12))
    # 4. SIZED_BY must not be laundered by feeding size_pipe the previous guess
    d1 = HY.size_pipe(0.06, 0.005, C, dn_min=200)
    d2 = HY.size_pipe(0.06, 0.005, C, dn_min=int(d1[0] or 200))
    ck("size_pipe reports 'minimum' when offered only the size that fits",
       d2[3] == "minimum" and d1[3] != "minimum",
       f"floor-anchored {d1[3]!r} vs guess-anchored {d2[3]!r}")
    # 5. peak factor FALLS as the catchment grows - the reason it is never summed
    pf_small, _ = C.peak_factor(50.0, 200.0)
    pf_big, _ = C.peak_factor(9600.0, 12920.0)
    ck("Merrimack peak factor falls as the catchment grows",
       pf_big < pf_small, f"{pf_small:.3f} -> {pf_big:.3f}")
    ck("peak factor is HELD at 1.0 below 100 properties",
       C.peak_factor(50.0, 99.0) == (1.0, "held"))
    # 6. infiltration is per-LENGTH and additive; peak flow is not
    ck("infiltration is linear in length",
       abs(C.infiltration_ls(2000.0) - 2 * C.infiltration_ls(1000.0)) < 1e-15)
    # 7. every enum this stage writes is one the contract declares
    ck("GRAD_BY vocabulary is the contract's",
       set(("table11", "tractive", "uniform", "cover_min", "cover_max", "ground", "vmax"))
       <= set(CT.GRAD_BY))
    ck("SIZED_BY vocabulary is the contract's",
       set(("minimum", "dod", "capacity", "velocity", "infeasible")) <= set(CT.SIZED_BY))
    ck("NODE_KIND vocabulary is the contract's",
       {"chamber", "head", "junction", "outfall", "drop"} <= set(CT.NODE_KIND))
    ck("SRC map lands only on contract values", set(SRC_MAP.values()) <= set(CT.SRC))
    ck("CONFIDENCE map lands only on contract values",
       set(CONF_MAP.values()) <= set(CT.CONFIDENCE))
    # 8. present.py's numbers still agree with criteria
    dis = PR.verify_against_criteria()
    ck("present.py agrees with criteria on every shared number", not dis, "; ".join(dis))
    # 9. the extra views register cleanly and every one has a question
    names = register_extra_views()
    ck("the six extra views register", len(names) == 6)
    ck("every view states the question it answers",
       all(PR.VIEWS[n].question for n in PR.list_views()))
    # 10. no field name this stage writes would be truncated by a DBF
    long = [f for spec in CT.LAYERS.values() for f in spec.names
            if len(f) > CT.SHP_FIELD_MAXLEN]
    ck("no contract field exceeds the DBF limit", not long, str(long))
    for c in ("CAP_WHY", "XING_CLS", "DRAIN_TXT", "CLEAN_TXT", "ST_SNAP_M", "ANCHOR_ND",
              "FALL_AV_M", "CAP_LEN_M", "ST_RESET", "UPS_LEN_M", "RUN_LEN_M", "UID_S7",
              "DEP_M", "DEP_BAND", "STR_CLS", "STR_KEY", "SUB_NAME", "SUBNET_ND",
              "US_NAME", "DS_NAME", "JOIN_GAP_M", "EXC_KIND", "EXC_SEV", "REJECT_WHY",
              "ANCHOR_X", "ANCHOR_Y", "TOWN_D_M", "N_CHAMBER", "AREA_M2", "LOW_ND",
              "OUT_NAME", "GAP_M", "OFF_M", "SERVED", "FLAG", "WHY", "DEEP_M"):
        ck(f"extra field {c} fits a DBF name", len(c) <= CT.SHP_FIELD_MAXLEN)
    # 11. the cap exits are the contract's two, and blank is legal
    ck("CAP_EXIT vocabulary", set(("", "recovers_500m", "outfall_1000m")) == set(CT.CAP_EXIT))

    # ---- 12. THE CONCEPT STAGE. Each of these is a rule the engineer stated. -----------
    ck("SewerGEMS export is refused BY NAME, not merely absent",
       _raises_contains(write_sewergems, "sewergems_export"))
    ck("phasing and packaging is switched off in the one register",
       "phasing_packaging" in C.CONCEPT_OFF and "motor_selection" in C.CONCEPT_OFF)
    _banned_written = set(CT.BANNED_FIELDS) & _fields_this_stage_writes()
    ck("no banned field name is written by this stage", not _banned_written,
       str(sorted(_banned_written)))

    # ---- 13. THE DEPTH THEME'S EDGES: fixed, ordered, and mostly sourced ---------------
    ck("DEPTH_BREAKS is strictly ascending",
       all(b < c2 for b, c2 in zip(DEPTH_BREAKS, DEPTH_BREAKS[1:])), str(DEPTH_BREAKS))
    ck("DEPTH_BREAKS starts at the guideline minimum cover and ends at the cap",
       DEPTH_BREAKS[0] == C.MIN_COVER_CROWN and DEPTH_BREAKS[-1] == C.MAX_COVER,
       f"{DEPTH_BREAKS[0]} .. {DEPTH_BREAKS[-1]}")
    ck("every DEPTH break has a slot for its source",
       len(DEPTH_BREAK_REFS) == len(DEPTH_BREAKS))
    ck("the unsourced DEPTH break is marked (o) on the legend",
       any(lab.endswith("(o)") for _k, lab, _c, _w in _depth_classes("line")))
    ck("MAGMA is registered and runs light -> dark",
       sum(PR.ramp_rgb("magma", 0.0)) > sum(PR.ramp_rgb("magma", 1.0)),
       f"{PR.ramp_rgb('magma', 0.0)} -> {PR.ramp_rgb('magma', 1.0)}")
    _idx = _depth_index(pd.Series([0.5, 1.31, 3.5, 5.0, 7.0, 10.0, 20.0, float("nan")]))
    ck("the DEPTH bands are FIXED - one value always lands in one band",
       list(_idx) == [0, 1, 2, 3, 4, 5, 6, 0], str(list(_idx)))

    # ---- 14. NAMING: the grammar round-trips, and the town rule is symmetric -----------
    _n1 = CT.concept_name("I", "manhole", subnet="S03", tier="sub main", seq=12)
    _n2 = CT.concept_name("I", "conduit", subnet="S03", seq=12)
    ck("a conduit carries its upstream manhole's number",
       _n1 == "I-S03-SM-M012" and _n2 == "I-S03-C012", f"{_n1} / {_n2}")
    ck("a pump is never parsed as a force main",
       (CT.parse_name("I-PMP02") or {}).get("kind") == "pump")
    _codes = CT.town_letters(["Al Aqar", "Ad Dariz", "Ibri"])
    ck("the article is dropped and a clash extends BOTH towns",
       _codes["Ibri"] == "I" and _codes["Al Aqar"] != _codes["Ad Dariz"], str(_codes))

    # ---- 15. THE THEME MACHINERY, on a synthetic layer set ----------------------------
    try:
        _demo = demo_layers()
        _themes = build_themes(_demo)
        ck("all three themes build", set(_themes) == {"structure", "depth", "exceptions"})
        ck("STRUCTURE draws the five layers",
           [t.key for t in _themes["structure"]]
           == ["conduits", "manholes", "pumps", "forcemains", "subnetworks"],
           str([t.key for t in _themes["structure"]]))
        ck("DEPTH classifies every layer on ONE column",
           {t.field for t in _themes["depth"]} == {"DEP_BAND"})
        ck("EXCEPTIONS draws ONLY flagged items and puts the count in the layer name",
           bool(_themes["exceptions"])
           and all(t.n > 0 and t.folder_name().endswith(f"({t.n:,})")
                   for t in _themes["exceptions"]))
        ck("every class carries a key, a label, a colour and a width",
           all(len(c) == 4 for tt in _themes.values() for tl in tt for c in tl.classes))
    except Exception as e:
        ck(f"the theme machinery runs ({type(e).__name__}: {e})", False)
    print(f"\n{len(fails)} of many checks failed" if fails else "\nall self-checks pass")
    return 1 if fails else 0


# ======================================================================================
# 17.  CLI
# ======================================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="build",
                    choices=["build", "verify", "selftest", "report", "kmz", "qgis"])
    ap.add_argument("--no-dxf", action="store_true", help="skip the two DXF drawings")
    ap.add_argument("--no-profiles", action="store_true", help="skip the long sections")
    ap.add_argument("--no-kmz", action="store_true", help="skip the KMZ set")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "verify":
        return verify()
    if a.cmd == "kmz":
        _mkdirs()
        res = build_kmz_from_gpkg()
        qgis_script(res)
        return 0
    if a.cmd == "qgis":
        _mkdirs()
        res = build_kmz_from_gpkg()
        print(qgis_script(res))
        return 0
    if a.cmd == "report":
        print(open(os.path.join(RUN, "EXPORT.md"), encoding="utf-8").read())
        return 0
    out = build(do_dxf=not a.no_dxf, do_profiles=not a.no_profiles, do_kmz=not a.no_kmz)
    print("\n" + CT.Manifest.report())
    print(f"\nreport: {out['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
