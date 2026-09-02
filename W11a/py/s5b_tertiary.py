"""W11a stage 5b - THE TERTIARY LAYER. Property connections, riders, and future stub-outs.

WHAT THIS EXISTS TO FIX. W10 published 1,883 km of sewer and NOT ONE property connection.
Nothing connected to anything: 74,675 m3/d of plot load sat in a table beside a pipe network
it never entered, and the 1,233 m3/d (1.7 %) that an assignment radius dropped in silence
could not even be noticed, because there was no layer on which a plot was supposed to appear.
A network with no tertiary layer is not a design that is missing a detail - it is a design
whose load allocation is unverifiable end to end. This stage is the audit trail from a plot
polygon to a chamber identifier, one row per load unit, with the ones that DO NOT connect
named rather than subtracted.

THE ENGINEERING, in the order the guideline sets it out (G203 sec 3, pp17-19).

  PCC -> PC Sewer -> HCC -> (rider) -> lateral -> Main Sewer

  * The PROPERTY CONNECTION CHAMBER (PCC) sits inside the property at the boundary. What
    happens upstream of it is the owner's internal drainage and is not ours to design.
  * The PC SEWER runs from the PCC to the HOUSE CONNECTION CHAMBER, which "is usually
    installed 2.5 m from the property boundary in the public right-of-way" (p17 sec 3.2).
    It is laid at 3-10 % (p18 Tab 5), OD160 minimum (p22 Tab 6), 0.60 m minimum cover
    (p19 sec 3.5), and "should not exceed 50 m in order to allow maintenance" (p18, note
    under Tab 4).
  * A RIDER joins "several HCC (usually up to 3)" (p17 sec 3.2) at 1-10 % (p18 Tab 5).
  * The chain reaches the secondary network at a CHAMBER, never mid-pipe: "Connection to
    the Main Sewer will be done at a manhole ... There must be no penetrating connection"
    (p19 sec 3.6). Falls over 600 mm at that manhole need an external backdrop (p19 sec 3.6).
  * FUTURE plots get a capped stub, on the guideline's own instruction: "Chambers are to be
    provided with stubs / plugged ports for the future connections" (p19 sec 3.4). The stub
    is sized for the plot's SATURATION flow, because the network is sized on the ultimate
    horizon (philosophy sec 6) and a stub laid for today's zero flow is a trench dug twice.

THE 45 m / 50 m QUESTION, resolved against the source rather than inherited.
The build instruction for this stage said "MAXIMUM 45 m per G203-p18 Tab 4" and told me to
verify it. It does not survive verification as written, and the two numbers are different
rules about different pipes:

    50 m   G203-p18, the note under Table 4: "The length of the PCS should not exceed 50 m
           in order to allow maintenance. If necessary, a manhole will be added."  ->  the
           PROPERTY CONNECTION SEWER.  `criteria.PCS_MAX_LEN` already carries this correctly.
    45 m   G203-p22 Table 6, on the Lateral Sewer row: "OD 200 mm (minimal) / Maximum Length
           45 m", and G203-p17 sec 3.2: "Rider Sewers and Lateral Sewers (maximum Length 45 m)
           are forming the Tertiary Sewage Network".  ->  the TERTIARY RUN to the secondary
           network.  `criteria.LATERAL_MAX_LEN` carries this correctly, cited to p22 Tab 6.

So 45 m is real but it is not the property-connection limit; 50 m is, and Table 4 is a
material table, not a length table. Both are applied below, each to its own pipe. Where the
guideline is genuinely ambiguous - p17 attaches the 45 m to riders as well as laterals while
p22 Tab 6 attaches it only to laterals - the CONSERVATIVE reading is taken: the whole
tertiary path from an HCC to its chamber is capped at 45 m, and the count of plots that the
looser reading would recover is reported rather than assumed away.

THE CONSEQUENCE, and it is the most useful thing this stage produces. A 45 m cap on the
tertiary run means CHAMBER SPACING ON A FRONTED STREET IS SET BY THE TERTIARY LIMIT, NOT BY
TABLE 12. Table 12's 100 m (G203-p30) is a maintenance maximum; it leaves a mid-block plot
50 m from the nearest chamber, and 50 m > 45 m. NAMA's own built network runs 32.3
chambers/km - about 31 m spacing - which satisfies the 45 m rule everywhere and is the
calibration evidence that this reading is the one a real engineer here already applied.
Every plot this stage cannot reach is written out with the point on the carrier where a
chamber would fix it (`run/s5b_chamber_requests.csv`), so the finding goes back to the
chamber stage as coordinates rather than as a complaint.

WHAT THIS STAGE REFUSES TO DO.
  * It does not put HCCs into the `nodes` layer. The contract gives the tertiary its own
    layer keyed on CONN_ID with OUT_NODE as its only graph reference, and that is right:
    60,000 house chambers in `nodes` would swamp the chamber schedule, the node-per-km
    metric and audit H15's component count with structures that are not part of the
    conveyance graph. So this layer carries OUT_NODE and no US_NODE/DS_NODE - its upstream
    end is a PCC, which is not a network node and must not be minted as one here.
  * It does not add a field the contract does not declare. The connections spec carries no
    DN, so the OD160 diameter is reported in the manifest and in the stage summary and is
    NOT smuggled onto the layer (contract EXCLUDED: "a per-stage schema").
  * It does not modify anything under W10/ or W8/, and it re-runs from clean every time.

Sources: `_BRAIN/02_DESIGN_CRITERIA.md` sec 2, 3, 4 (every number, page-cited);
`_BRAIN/08_DESIGN_PHILOSOPHY.md` sec 3 H3/H9/H10, sec 4 (vocabulary, the gate), sec 8a
(every plot served, by SOME system); `W11a/py/w11a/contract.py` (field names, Funnel,
Manifest, publish); `W8/py/sewnet/criteria.py` + `hydra.py` (the design numbers and the
hydraulics, imported, never reimplemented).
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

warnings.filterwarnings("ignore")

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py
W11A_ROOT = os.path.dirname(_HERE)                          # .../W11a
REPO_ROOT = os.path.dirname(W11A_ROOT)                      # .../Hydraulic/Claude
BASE = os.path.dirname(os.path.dirname(REPO_ROOT))          # .../2621 Ibri Sewer STP
for _p in (_HERE, os.path.join(REPO_ROOT, "W8", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import geopandas as gpd                                     # noqa: E402
import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402
import rasterio                                             # noqa: E402
from shapely.geometry import LineString, Point              # noqa: E402
from shapely.ops import nearest_points                      # noqa: E402
from shapely.strtree import STRtree                         # noqa: E402

from w11a import contract as K                              # noqa: E402  THE shared contract
from sewnet.criteria import DEFAULT as C                    # noqa: E402  THE design numbers
from sewnet import hydra                                    # noqa: E402  never reimplemented

STAGE = "s5b_tertiary"
STAGE_ORDER = 52          # 5b: after the chambers (5a) and before the packages

# --------------------------------------------------------------------------------------
# Inputs. Absolute, and named here so a missing one is reported as a path, not a traceback.
# --------------------------------------------------------------------------------------

GPKG = K.gpkg_path(W11A_ROOT)                                     # W11a/shp/W11a.gpkg

# Where the chamber layer may be, best first. Each candidate is (label, node source, reach
# source), and the node and reach halves MAY come from different files - the chamber stage
# currently publishes 48,137 levelled nodes into `W11a.gpkg` while its split reaches are
# still in `run/s5_reach_skeleton.gpkg`.
#
# Mixing two files is the W10 defect (a node layer and a pipe layer out of different solves,
# disagreeing by 10.39 m of depth), so it is never done on faith: `_pairs()` requires every
# reach endpoint to resolve against that node layer's NODE_UID before the pair is accepted,
# and the pair actually used is printed and written to the manifest. A verified join is
# stronger than a rule against joining; an unverified one is how W10 happened.
_SHP = os.path.join(W11A_ROOT, "shp")
_RUN = os.path.join(W11A_ROOT, "run")
UPSTREAM: Tuple[Tuple[str, Tuple[str, str], Tuple[str, str]], ...] = (
    ("contract layers",
     (os.path.join(_SHP, "W11a.gpkg"), "nodes"), (os.path.join(_SHP, "W11a.gpkg"), "reaches")),
    ("levelled reaches, stage 6",
     (os.path.join(_SHP, "W11a_s6.gpkg"), "s6_nodes"),
     (os.path.join(_SHP, "W11a_s6.gpkg"), "s6_reaches")),
    ("chambers published + split reaches from the run folder",
     (os.path.join(_SHP, "W11a.gpkg"), "nodes"),
     (os.path.join(_RUN, "s5_reach_skeleton.gpkg"), "s5_reach_skeleton")),
    ("chambers, stage 5",
     (os.path.join(_SHP, "W11a_s5.gpkg"), "s5_nodes"),
     (os.path.join(_SHP, "W11a_s5.gpkg"), "s5_reaches")),
    ("hierarchy only, stage 4 - no chamber splitting, no levels",
     (os.path.join(_SHP, "W11a_s4.gpkg"), "s4_nodes"),
     (os.path.join(_SHP, "W11a_s4.gpkg"), "s4_reaches")),
)

# How much of the reach layer must resolve against the node layer for the pair to be used.
# Not 100 %: a published layer can legitimately carry a handful of tie-ins to an existing
# structure that is not in this node set. Anything below this is two different solves.
PAIR_MIN_RESOLVED = 0.999

# What this stage actually reads. Declared, so a partial upstream fails on the field it is
# missing rather than three functions later on a KeyError.
NEEDS_NODES = ("NODE_UID", "X", "Y", "GRD_M", "INV_M")
NEEDS_REACHES = ("EDGE_UID", "US_NODE", "DS_NODE", "TIER", "SRC", "CONFIDENCE")

PLOT_LOADS = os.path.join(REPO_ROOT, "W10", "shp", "W10_plot_loads.gpkg")
PLOT_LOADS_LAYER = "plot_loads"
TERRAIN = os.path.join(BASE, "Data", "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt")
GUIDELINE_PDF = os.path.join(BASE, "Data", "PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf")
RUN_DIR = os.path.join(W11A_ROOT, "run")   # the default; build() derives its own from `root`

# --------------------------------------------------------------------------------------
# Criteria used here. Every one is read from `sewnet.criteria` - none is redefined - and the
# citation beside it is the page verify_constants() re-reads at build time (philosophy P9).
# --------------------------------------------------------------------------------------

PCS_MIN_SLOPE_PCT = C.PCS_MIN_SLOPE * 100.0     # 3 %   G203-p18 Tab 5, Property Connection
PCS_MAX_SLOPE_PCT = C.PCS_MAX_SLOPE * 100.0     # 10 %  G203-p18 Tab 5
RIDER_MIN_SLOPE_PCT = C.RIDER_MIN_SLOPE * 100.0  # 1 %  G203-p18 Tab 5, Rider & Lateral
PCS_MAX_LEN_M = C.PCS_MAX_LEN                   # 50 m  G203-p18, note under Tab 4
TERTIARY_MAX_LEN_M = C.LATERAL_MAX_LEN          # 45 m  G203-p22 Tab 6 (Lateral Sewer)
MAX_HCC_PER_RIDER = C.MAX_HCC_PER_RIDER         # 3     G203-p17 sec 3.2
DN_TERTIARY = C.DN_TERTIARY                     # OD160 G203-p22 Tab 6, minimum
PCS_MIN_COVER_M = C.PCS_MIN_COVER               # 0.60 m G203-p19 sec 3.5
DROP_TRIGGER_M = C.DROP_TRIGGER                 # 0.60 m G203-p19 sec 3.6 and p30
SLOPE_STEP_PCT = K.SLOPE_STEP_PCT               # 0.05 % P1, so the drawing matches the levels

# Values this stage needs that `criteria` does not carry. Each is a QUOTED guideline number,
# not an invention; where the guideline gives none, it is tagged as an assumption below.
HCC_OFFSET_M = 2.5        # "The HCC is usually installed 2.5 m from the property boundary in
                          # the public right-of-way (ROW)" - G203-p17 sec 3.2
PCC_MAX_DEPTH_M = 1.50    # "a minimum cover of 600 mm is required and can go up to 1.50 m
                          # depth (in square dimension 800x800)" - G203-p19 sec 3.5
HCC_MAX_DEPTH_M = 2.00    # circular HCC "depth ranges from 1.0 m to 2.0 m" - G203-p19 sec 3.4

# Minimum invert depth for the tertiary, through the CONTRACT's definition and not the
# criteria helper. `criteria.invert_depth_min()` is 50 mm shallow against the auditor's own
# arithmetic at every diameter (contract OPEN-3), and a connection laid to it sits below the
# guideline cover it claims to meet. 0.60 + 0.160 + 0.10 = 0.86 m.
PCS_MIN_INV_DEPTH_M = PCS_MIN_COVER_M + DN_TERTIARY / 1000.0 + K.AUDITOR_OD_ALLOW_M

# Which tiers a house may connect to. G203-p35 (via 02 sec 3) DEFINES a trunk main as
# "length > 1,000 m WITHOUT CONNECTIONS", so the trunk is excluded by the guideline's own
# definition and not by preference. Everything else in the secondary network is a "Main
# Sewer" in G203's vocabulary and may receive a tertiary connection at a manhole.
CARRIER_TIERS: Tuple[str, ...] = ("lateral", "main", "sub main")

# A plot whose boundary is further than this from any carrier cannot be reached even with the
# whole tertiary allowance spent on the offset: HCC_OFFSET + the 45 m tertiary run.
CARRIER_SEARCH_M = HCC_OFFSET_M + TERTIARY_MAX_LEN_M

# CLASS on W10_plot_loads: 'B' built, 'A' agriculture (estimated), 'P' planned/vacant,
# 'U' unparceled building (W3/py/a6_landuse_class.py). 'P' is the FUTURE plot - a platted
# reserve with nothing built on it - and philosophy sec 4 requires it to be identified
# separately in every drawing and schedule and never reported as existing.
FUTURE_CLASS = "P"


# --------------------------------------------------------------------------------------
# P9 - re-extract the constants from the page they claim, at build time
# --------------------------------------------------------------------------------------

# The exact strings on the pages the numbers above are cited to. If the guideline is ever
# reissued and a number moves, this fails loudly instead of the design quietly carrying a
# figure from a page that no longer says it. Two errors of exactly this kind are already on
# record in this project (rising main 3.0 vs 2.5 m/s, INLET_MIN_DEG 85 vs 75).
_CONSTANT_GATE: Tuple[Tuple[int, str, str], ...] = (
    (17, "usually installed 2.5 m from the property boundary", "HCC_OFFSET_M = 2.5"),
    (17, "usually up to 3", "MAX_HCC_PER_RIDER = 3"),
    (17, "maximum Length 45 m", "TERTIARY_MAX_LEN_M = 45 (p17 sec 3.2 wording)"),
    (18, "should not exceed 50 m", "PCS_MAX_LEN_M = 50 (the PCS limit, NOT 45)"),
    (18, "3 %", "PCS_MIN_SLOPE_PCT = 3 (Tab 5, Property Connection Sewer)"),
    (19, "minimum cover of 600 mm", "PCS_MIN_COVER_M = 0.60"),
    (19, "up to 1.50 m depth", "PCC_MAX_DEPTH_M = 1.50"),
    (19, "1.0 m to 2.0 m", "HCC_MAX_DEPTH_M = 2.00"),
    (19, "stubs / plugged ports for the future connections", "the stub-out is required, not chosen"),
    (19, "Falls of more than 600 mm are not permitted", "DROP_TRIGGER_M = 0.60"),
    (19, "no penetrating connection", "OUT_NODE is always a chamber"),
    (22, "Maximum", "TERTIARY_MAX_LEN_M = 45 (Tab 6, Lateral Sewer row)"),
    (22, "OD 160 mm", "DN_TERTIARY = 160"),
)


def verify_constants(pdf_path: str = GUIDELINE_PDF) -> Tuple[bool, List[str]]:
    """Re-read every cited page and confirm it still says what the constant claims.

    Returns (ran, messages). A missing pdfplumber or a missing PDF returns ran=False with a
    message - the gate could not run, which is recorded in the manifest rather than passed
    over, because "a check that cannot run is a failure" (philosophy sec 8) and pretending
    otherwise is how a constant outlives its page.
    """
    try:
        import pdfplumber                                    # noqa: PLC0415
    except Exception as e:                                   # pragma: no cover
        return False, [f"pdfplumber not available ({e}) - constants NOT re-verified"]
    if not os.path.exists(pdf_path):
        return False, [f"{pdf_path} not found - constants NOT re-verified"]
    msgs: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        cache: Dict[int, str] = {}
        for page, phrase, what in _CONSTANT_GATE:
            if page not in cache:
                cache[page] = (pdf.pages[page - 1].extract_text() or "").replace("\n", " ")
            if phrase.lower() not in cache[page].lower():
                msgs.append(f"G203-p{page} no longer contains {phrase!r} -> {what}")
    return True, msgs


# --------------------------------------------------------------------------------------
# Small geometry helpers
# --------------------------------------------------------------------------------------

def _lerp(a: Tuple[float, float], b: Tuple[float, float], d: float) -> Tuple[float, float]:
    """The point d metres from a towards b. Returns b when a and b coincide."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return b
    t = min(max(d / L, 0.0), 1.0)
    return (a[0] + dx * t, a[1] + dy * t)


def _clean(coords: Sequence[Tuple[float, float]], tol: float = 1e-6) -> List[Tuple[float, float]]:
    """Drop consecutive duplicates. A zero-length segment is not invalid geometry, but it is
    a vertex nobody surveyed and it makes a length check ambiguous."""
    out: List[Tuple[float, float]] = []
    for p in coords:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > tol:
            out.append((float(p[0]), float(p[1])))
    return out


def _substring(line: LineString, s0: float, s1: float) -> List[Tuple[float, float]]:
    """Vertices of `line` between stations s0 and s1, endpoints included, in THAT order.

    The rider has to follow the carrier's REAL alignment. A straight chord between two
    stations understates the pipe on every curved street, and the length is a quantity the
    client pays for - so the intermediate vertices are kept.
    """
    lo, hi = (s0, s1) if s0 <= s1 else (s1, s0)
    pts: List[Tuple[float, float]] = [tuple(line.interpolate(lo).coords[0][:2])]
    run = 0.0
    cs = [tuple(c[:2]) for c in line.coords]
    for a, b in zip(cs[:-1], cs[1:]):
        run += math.hypot(b[0] - a[0], b[1] - a[1])
        if lo < run < hi:                       # a vertex strictly inside the span
            pts.append(b)
    pts.append(tuple(line.interpolate(hi).coords[0][:2]))
    out = _clean(pts)
    return out if s0 <= s1 else out[::-1]


def _offset(line: LineString, d: float) -> LineString:
    """Shift the whole line d metres square to its first segment.

    A rigid TRANSLATION, not shapely's parallel_offset: translation preserves length exactly,
    so LEN_M still measures the geometry it sits on, and the contract checks that to 50 mm.
    Used only for a second property connection on one plot (G203-p19 3.4), which is a second
    trench and must not be drawn on top of the first.
    """
    c = list(line.coords)
    dx, dy = c[1][0] - c[0][0], c[1][1] - c[0][1]
    L = math.hypot(dx, dy) or 1.0
    return LineString([(x - dy / L * d, y + dx / L * d) for x, y in c])


def _round_step(x: float, step: float, up: bool = True) -> float:
    """Round a gradient onto the 0.05 % step (P1). Rounding UP by default: a steeper pipe
    arrives higher, which costs nothing, while rounding down can drop the arrival below the
    chamber flow line and turn a working connection into one that does not drain."""
    n = x / step
    n = math.ceil(n - 1e-9) if up else math.floor(n + 1e-9)
    return n * step


# --------------------------------------------------------------------------------------
# Levels - the one place a tertiary gradient or invert is decided
# --------------------------------------------------------------------------------------

@dataclass
class Link:
    """One published connection: PC sewer, then the rider/lateral leg to the discharge point.

    TWO PIPES, TWO GRADIENTS, and that distinction is worth about a quarter of the network.
    G203-p18 Tab 5 gives them different minima - Property Connection Sewer 3-10 %, Rider and
    Lateral 1-10 % - and laying the whole chain at the PC sewer's 3 % throws away fall the
    design needs. A connection starts 0.86 m below the plot (0.60 m cover on OD160, G203-p19
    3.5) and has to arrive AT OR ABOVE the chamber flow line, which sits about 1.60 m down on
    a DN200 at minimum cover. That leaves roughly 0.74 m of head, so at 3 % the chain dies at
    about 25 m; at 1 % it reaches about 74 m, and the binding limit becomes the 45 m of
    G203-p22 Tab 6 instead of the gradient. Measured on the real layers, forcing one gradient
    over the whole chain cost 10,632 connections that drain perfectly well at the rates the
    guideline actually gives.

    So the PC sewer runs its 2.5 m from the boundary to the HCC (G203-p17 3.2) at the 3 %
    minimum - a standard detail, not a designed length - and `slope_pct` is the gradient of
    the LEG, which is the pipe that is actually designed and the one the schedule prints.
    """
    length: float                 # the leg: HCC -> discharge point
    pcs_len: float                # the PC sewer: PCC -> HCC, 0 on a stub
    grd_up: float                 # ground at the plot end
    s_min_pct: float              # 1 % on the leg (G203-p18 Tab 5, Rider & Lateral Sewer)
    d_min: float                  # minimum invert depth below ground
    d_max: float                  # maximum invert depth at the HCC
    inv_target: float             # invert at the discharge point
    at_chamber: bool              # True = arriving at a manhole, where a fall is allowed

    slope_pct: float = float("nan")
    inv_up: float = float("nan")      # invert at the HCC, the head of the leg
    inv_pcc: float = float("nan")     # invert at the PCC, inside the plot
    inv_arrive: float = float("nan")
    drop_m: float = 0.0
    can_drain: int = 1
    note: str = ""

    @property
    def pcs_fall(self) -> float:
        """The PC sewer's own fall, at its G203-p18 Tab 5 minimum of 3 %."""
        return PCS_MIN_SLOPE_PCT / 100.0 * self.pcs_len

    def solve(self) -> "Link":
        """Choose the leg's gradient and the HCC invert.

        Order of preference, and it is the philosophy's order, not a solver's:
          P6  lay as shallow as the cover rule allows -> start at the minimum invert depth
          H3  never break the 0.60 m minimum cover on the property connection (G203-p19 3.5)
          G203-p19 3.6  arrive within 600 mm above the manhole flow line, or take an
                        external backdrop - and NEVER below it, which is not a small error
                        but a plot the gravity network does not serve.
        """
        L = max(self.length, 1e-6)
        s_lo, s_hi = self.s_min_pct, PCS_MAX_SLOPE_PCT

        # Shallowest legal start, then the gradient that lands exactly on the target. The
        # HCC sits one PC-sewer fall below the shallowest legal PCC.
        inv_up = self.grd_up - self.d_min - self.pcs_fall
        s_need = (inv_up - self.inv_target) / L * 100.0

        if s_need < s_lo:
            # Too little fall available. Raising the upstream end is not open to us - it is
            # already at minimum cover - so at the minimum gradient the pipe would arrive
            # BELOW the flow line. That is not a level to be nudged; it is a plot that does
            # not drain here (contract: "0 is not a rounding error").
            s = s_lo
            inv_arrive = inv_up - s / 100.0 * L
            self.can_drain = 0
            self.note = (f"arrives {self.inv_target - inv_arrive:.2f} m below the discharge "
                         f"invert at the {s_lo:.0f} % minimum (G203-p18 Tab 5)")
        elif s_need > s_hi:
            # More fall than the maximum gradient can take. Absorb what we can by starting
            # the HCC deeper - up to the 2.00 m of G203-p19 3.4 - before reaching for a
            # backdrop, because a deeper chamber is cheaper than a drop structure.
            s = s_hi
            want_inv_up = self.inv_target + s / 100.0 * L
            inv_up = min(self.grd_up - self.d_min - self.pcs_fall,
                         max(want_inv_up, self.grd_up - self.d_max))
            inv_arrive = inv_up - s / 100.0 * L
        else:
            # Round DOWN onto the 0.05 % step, not up. The upstream end is FIXED here - it
            # is already at the shallowest legal cover and cannot rise - so a steeper pipe
            # arrives LOWER, not higher, and rounding up lands the connection up to
            # 0.0005 x 45 m = 22.5 mm BELOW the chamber flow line: past H11's 20 mm laying
            # tolerance, and the one thing this method's own contract forbids ("NEVER below
            # it"). It was invisible because `drop_m = max(drop, 0.0)` clamps the negative
            # away. Rounding down can only lift the arrival, which is a fall at a manhole
            # and is legal to 600 mm (G203-p19 3.6). It cannot break the Tab 5 minimum
            # either: s_need >= s_lo in this branch, so the clamp below can only raise s
            # back to s_lo, which is still <= s_need.
            s = _round_step(s_need, SLOPE_STEP_PCT, up=False)
            s = min(max(s, s_lo), s_hi)
            inv_arrive = inv_up - s / 100.0 * L

        drop = inv_arrive - self.inv_target
        if not self.at_chamber and abs(drop) > 0.001 and self.can_drain:
            # An upstream member joins the rider at a BRANCH FITTING, not at a chamber, and
            # there is no structure mid-pipe to take a fall. The invert has to meet exactly,
            # so one of the two free variables has to give. P1 (round 0.05 % gradients) is a
            # preference and the invert match is physics, so P1 yields - but only after both
            # neighbouring steps have been tried, because a preference abandoned without
            # trying is a preference that was never applied.
            inv_arrive = self.inv_target
            drop = 0.0
            done = False
            for up in (False, True):
                s_try = _round_step((inv_up - self.inv_target) / L * 100.0,
                                    SLOPE_STEP_PCT, up=up)
                if not (s_lo - 1e-9 <= s_try <= s_hi + 1e-9):
                    continue
                d_try = (self.grd_up - self.pcs_fall
                         - (self.inv_target + s_try / 100.0 * L))
                if self.d_min - 1e-6 <= d_try <= HCC_MAX_DEPTH_M + 1e-6:
                    s = s_try
                    inv_up = self.inv_target + s / 100.0 * L
                    done = True
                    break
            if not done:
                s_exact = (inv_up - self.inv_target) / L * 100.0
                if s_lo - 1e-9 <= s_exact <= s_hi + 1e-9:
                    s = s_exact
                    self.note = (f"gradient {s:.3f} % is off the {SLOPE_STEP_PCT} % step (P1): "
                                 "the rider junction fixes the invert and there is no chamber "
                                 "there to take a fall")
                else:
                    s = min(max(s, s_lo), s_hi)
                    inv_up = self.inv_target + s / 100.0 * L
                    if (self.grd_up - self.pcs_fall - inv_up) < self.d_min - 1e-6:
                        self.can_drain = 0
                        self.note = (f"joining the rider would leave only "
                                     f"{self.grd_up - self.pcs_fall - inv_up:.2f} m to "
                                     f"invert, under the {self.d_min:.2f} m minimum "
                                     f"(G203-p19 3.5)")

        self.slope_pct = float(s)
        self.inv_up = float(inv_up)
        self.inv_pcc = float(inv_up + self.pcs_fall)
        self.inv_arrive = float(inv_arrive)
        self.drop_m = float(max(drop, 0.0))
        if self.at_chamber and self.drop_m > DROP_TRIGGER_M + 1e-9 and not self.note:
            self.note = (f"fall of {self.drop_m:.2f} m at the manhole - external backdrop "
                         f"required (G203-p19 3.6)")
        if self.can_drain and self.depth_hcc > HCC_MAX_DEPTH_M + 1e-6 and not self.note:
            self.note = (f"house connection chamber {self.depth_hcc:.2f} m deep, past the "
                         f"{HCC_MAX_DEPTH_M:.2f} m of G203-p19 3.4 - non-standard chamber")
        elif (self.can_drain and self.pcs_len > 0 and not self.note
              and self.depth_pcc > PCC_MAX_DEPTH_M + 1e-6):
            self.note = (f"property connection chamber {self.depth_pcc:.2f} m deep - G203-p19 "
                         f"3.5 puts the PC sewer at 0.60 m cover 'up to {PCC_MAX_DEPTH_M:.2f} "
                         "m depth (in square dimension 800x800)', so this one needs the "
                         "circular chamber of 3.4 instead")
        return self

    @property
    def depth_hcc(self) -> float:
        return self.grd_up - self.pcs_fall - self.inv_up

    @property
    def depth_pcc(self) -> float:
        return self.grd_up - self.inv_pcc

    @property
    def cover_min(self) -> float:
        """Least cover anywhere on the chain, through contract.cover() and no other
        arithmetic. W10 subtracted a hardcoded 0.30 m regardless of diameter and shipped
        45.92 km below minimum cover. The shallow end is the PCC on a live connection (it is
        laid AT the 0.60 m minimum) and the HCC on a stub."""
        d = self.d_min if self.pcs_len > 0 else self.depth_hcc
        return K.cover(DN_TERTIARY, min(d, self.depth_hcc))


# --------------------------------------------------------------------------------------
# Inputs, and the graceful stop
# --------------------------------------------------------------------------------------

class Missing(Exception):
    """An upstream layer this stage cannot invent. Caught in main(), printed, exit 0."""


def _try_pair(pn: str, ln: str, pr: str, lr: str):
    """Load a node layer and a reach layer and prove they describe the SAME network.

    Returns (ok, why_not, (nodes, reaches, resolved_fraction)). The proof is that the reach
    layer's US_NODE and DS_NODE resolve against the node layer's NODE_UID - which is the
    check nobody made in W10, where the node layer and the pipe layer came out of different
    solves and disagreed by up to 10.39 m of depth. Node ids are minted per stage, so two
    files agreeing on 99.9 % of 47,021 endpoints is not a coincidence; it is the same graph.
    """
    import fiona
    for p, lyr in ((pn, ln), (pr, lr)):
        if not p or not os.path.exists(p):
            return False, f"{os.path.basename(p or '?')} not written yet", None
        try:
            if lyr not in set(fiona.listlayers(p)):
                return False, f"{os.path.basename(p)} has no layer '{lyr}'", None
        except Exception as e:
            return False, f"{os.path.basename(p)} unreadable ({e})", None

    nodes = gpd.read_file(pn, layer=ln)
    reaches = gpd.read_file(pr, layer=lr)
    for gdf, want, what in ((nodes, NEEDS_NODES, ln), (reaches, NEEDS_REACHES, lr)):
        miss = [c for c in want if c not in gdf.columns]
        if miss:
            return False, f"`{what}` has no {miss} (this stage reads {list(want)})", None
        if gdf.crs is None or gdf.crs.to_epsg() != K.CRS_EPSG:
            gdf.set_crs(K.CRS_EPSG, allow_override=True, inplace=True)

    ids = set(nodes.NODE_UID.astype(str))
    hit = (reaches.US_NODE.astype(str).isin(ids) & reaches.DS_NODE.astype(str).isin(ids))
    resolved = float(hit.mean()) if len(reaches) else 0.0
    if resolved < PAIR_MIN_RESOLVED:
        return False, (f"only {resolved:.1%} of `{lr}` endpoints resolve in `{ln}` "
                       f"({len(reaches):,} reaches against {len(nodes):,} nodes) - these are "
                       "two different solves, not one network"), None
    if resolved < 1.0:
        reaches = reaches[hit].reset_index(drop=True)
    return True, "", (nodes, reaches, resolved)


@dataclass
class Inputs:
    plots: gpd.GeoDataFrame
    nodes: gpd.GeoDataFrame
    reaches: gpd.GeoDataFrame
    terrain: str
    source: str = ""              # which file and layers were actually read
    levels_known: bool = False    # are the chamber inverts published yet?
    levelled_elsewhere: str = ""  # a levelled node layer exists but has no reaches yet

    @staticmethod
    def load(gpkg: Optional[str] = None, plots_path: str = PLOT_LOADS,
             terrain: str = TERRAIN, strict_upstream: bool = False) -> "Inputs":
        if not os.path.exists(plots_path):
            raise Missing(f"the plot loads: {plots_path}")
        plots = gpd.read_file(plots_path, layer=PLOT_LOADS_LAYER)
        if plots.crs is None or plots.crs.to_epsg() != K.CRS_EPSG:
            plots = plots.set_crs(K.CRS_EPSG, allow_override=True)

        cands = ((("explicit --gpkg"), (gpkg, "nodes"), (gpkg, "reaches")),) if gpkg \
            else UPSTREAM
        found, seen = None, []
        for label, (pn, ln), (pr, lr) in cands:
            ok, why, pair = _try_pair(pn, ln, pr, lr)
            if ok:
                found = (label, pn, ln, pr, lr, pair)
                break
            seen.append(f"{label}: {why}")
        if found is None:
            raise Missing(
                "a chamber layer - a node set and a reach set that belong to each other.\n"
                "        tried, best first:\n          " + "\n          ".join(seen)
                + "\n\n        A property connection must terminate at a CHAMBER (G203-p19 3.6:"
                  " 'Connection to\n        the Main Sewer will be done at a manhole ... There "
                  "must be no penetrating\n        connection'), so there is nothing legal to "
                  "connect to until the chambers exist.")

        label, pn, ln, pr, lr, (nodes, reaches, resolved) = found
        src = (f"{os.path.basename(pn)}[{ln}] + {os.path.basename(pr)}[{lr}]"
               f"  ({label}; {resolved:.3%} of reach endpoints resolve)")

        # Are the chamber inverts real? The tertiary is levelled against them, and until the
        # levelling stage has run they are null - which is not a fault, it is the sequence.
        # The load allocation this stage produces is what the levelling stage sizes against,
        # so the two are circular and the break is deliberate: assign first, level second,
        # re-run. Nothing is guessed in between; the placeholder is declared as one.
        levels_known = bool(pd.to_numeric(nodes["INV_M"], errors="coerce").notna().any())
        levelled_elsewhere = ""
        if not levels_known and seen:
            levelled_elsewhere = ("a better-levelled pair was not available; rejected: "
                                  + " | ".join(seen))

        if strict_upstream:
            # The contract's own gate. Applied when asked for, and NOT by default: a
            # mid-pipeline layer legitimately lacks the fields a finished one carries, and
            # blocking on them would only mean this stage never runs at all.
            K.validate(nodes, "nodes", stage=STAGE)
            K.validate(reaches, "reaches", stage=STAGE)
        return Inputs(plots=plots, nodes=nodes, reaches=reaches, terrain=terrain,
                      source=src, levels_known=levels_known,
                      levelled_elsewhere=levelled_elsewhere)


class Ground:
    """Ground level from the 0.5 m terrain VRT (project rule 6), sampled in one pass.

    Sampled rather than interpolated from the chamber: a plot 40 m off the street can sit a
    metre above or below it, and a connection designed on the street's level is a connection
    whose cover is unknown at the end that matters.
    """

    def __init__(self, path: str):
        self.path = path
        self.ok = os.path.exists(path)

    def at(self, xy: Sequence[Tuple[float, float]]) -> np.ndarray:
        if not len(xy):
            return np.zeros(0)
        if not self.ok:
            return np.full(len(xy), np.nan)
        with rasterio.open(self.path) as ds:
            nod = ds.nodata
            v = np.array([s[0] for s in ds.sample(xy)], dtype="float64")
        if nod is not None:
            v[v == nod] = np.nan
        return v


# --------------------------------------------------------------------------------------
# The frontage: where a plot meets the network
# --------------------------------------------------------------------------------------

@dataclass
class Frontage:
    """One plot's geometric relationship to the carrier it will connect to.

    `gate` is the foot of the perpendicular from the plot onto the carrier - philosophy sec 4
    ("a head starts at the gate ... on the road, at the foot of the perpendicular"). `pcc` is
    where that perpendicular leaves the plot, which is the boundary, which is where G203-p17
    puts the property connection chamber. `hcc` is 2.5 m into the ROW from the boundary
    (G203-p17 sec 3.2), or the gate itself where the street is closer than that.
    """
    plot_i: int
    reach_i: int
    pcc: Tuple[float, float]
    hcc: Tuple[float, float]
    gate: Tuple[float, float]
    station: float                 # gate's distance along the carrier from its US end
    offset: float                  # plot boundary to carrier
    out_node: str                  # the chamber the chain discharges at
    d_along: float                 # gate to that chamber, along the carrier
    to_us: bool                    # discharging at the carrier's upstream end

    @property
    def pcs_len(self) -> float:
        return min(HCC_OFFSET_M, self.offset)

    @property
    def leg_len(self) -> float:
        """HCC to the chamber: the spur across the remaining offset, plus the run along the
        carrier. This is the length the 45 m tertiary limit applies to."""
        return max(0.0, self.offset - HCC_OFFSET_M) + self.d_along


class Frontages:
    """Assign every load-bearing plot to a carrier, a gate and a discharge chamber."""

    def __init__(self, inp: Inputs, rec: K.StageRecord):
        self.inp = inp
        self.rec = rec
        self.carriers = inp.reaches[inp.reaches.TIER.isin(CARRIER_TIERS)].reset_index(drop=True)
        self.node_xy = {r.NODE_UID: (r.geometry.x, r.geometry.y)
                        for r in inp.nodes.itertuples()}

    def build(self, plots: gpd.GeoDataFrame) -> Tuple[List[Frontage], Dict[int, str]]:
        """Returns the frontages, and the plots that could not get one with the reason."""
        rejected: Dict[int, str] = {}
        out: List[Frontage] = []
        if not len(self.carriers):
            for i in plots.index:
                rejected[i] = "no carrier reach of any tier exists"
            return out, rejected

        geoms = list(self.carriers.geometry.values)
        tree = STRtree(geoms)
        us = self.carriers.US_NODE.astype(str).values
        ds = self.carriers.DS_NODE.astype(str).values

        for i, pg in zip(plots.index, plots.geometry.values):
            hit = tree.query_nearest(pg, max_distance=CARRIER_SEARCH_M,
                                     return_distance=False, all_matches=False)
            hit = np.atleast_1d(hit)
            if not hit.size:
                rejected[i] = (f"no {'/'.join(CARRIER_TIERS)} reach within "
                               f"{CARRIER_SEARCH_M:.1f} m of the plot boundary")
                continue
            j = int(hit[0])
            line = geoms[j]
            g_pt, p_pt = nearest_points(line, pg)
            gate = (g_pt.x, g_pt.y)
            pcc = (p_pt.x, p_pt.y)
            offset = math.hypot(gate[0] - pcc[0], gate[1] - pcc[1])
            hcc = _lerp(pcc, gate, min(HCC_OFFSET_M, offset))
            st = float(line.project(g_pt))
            L = float(line.length)
            # Either end of the reach is a legal discharge: a chamber upstream of the flow is
            # still a chamber, and it is often the nearer one. Both are manholes, which is
            # what G203-p19 3.6 requires.
            to_us = st <= (L - st)
            out.append(Frontage(plot_i=i, reach_i=j, pcc=pcc, hcc=hcc, gate=gate,
                                station=st, offset=offset,
                                out_node=(us[j] if to_us else ds[j]),
                                d_along=(st if to_us else L - st), to_us=to_us))
        return out, rejected


# --------------------------------------------------------------------------------------
# Riders: at most three house connections joined together
# --------------------------------------------------------------------------------------

@dataclass
class Rider:
    """A chain of at most 3 HCCs discharging at one chamber (G203-p17 sec 3.2).

    `members` is ordered UPSTREAM FIRST, so the last member is the one nearest the chamber.
    That order is also the solve order reversed: levels are worked from the chamber back.
    """
    out_node: str
    reach_i: int
    to_us: bool
    members: List[Frontage] = field(default_factory=list)


def group_riders(frontages: List[Frontage]) -> List[Rider]:
    """Chain the frontages into riders of at most three.

    Grouped by (carrier, discharge chamber, direction) and ordered by distance from that
    chamber, so a rider is a run of neighbours and never three plots picked from opposite
    ends of the street. Beyond three, another rider is started - G203 allows "one or several
    Rider Sewers" at one chamber, so this is not a deviation; it is the reason the built
    network runs 32.3 chambers/km.
    """
    buckets: Dict[Tuple[int, str, bool], List[Frontage]] = {}
    for f in frontages:
        buckets.setdefault((f.reach_i, f.out_node, f.to_us), []).append(f)
    riders: List[Rider] = []
    for (ri, node, to_us), fs in buckets.items():
        fs.sort(key=lambda f: -f.d_along)          # furthest from the chamber first
        for k in range(0, len(fs), MAX_HCC_PER_RIDER):
            riders.append(Rider(out_node=node, reach_i=ri, to_us=to_us,
                                members=fs[k:k + MAX_HCC_PER_RIDER]))
    return riders


# --------------------------------------------------------------------------------------
# The stage
# --------------------------------------------------------------------------------------

class Tertiary:
    """Build, level and publish the connections layer."""

    def __init__(self, inp: Inputs, rec: K.StageRecord):
        self.inp = inp
        self.rec = rec
        self.ground = Ground(inp.terrain)
        self.levels_known = inp.levels_known
        self.source = inp.source
        self.node = inp.nodes.set_index("NODE_UID")
        self.carriers = inp.reaches[inp.reaches.TIER.isin(CARRIER_TIERS)].reset_index(drop=True)
        self.rows: List[Dict] = []
        self.geoms: List[LineString] = []
        self.requests: List[Dict] = []       # chambers and corridors the layout owes us
        self.unassigned: List[Dict] = []     # every plot named, never subtracted
        self.degenerate: List[str] = []      # plots the corridor runs through
        self._n = 0
        self.stats: Dict[str, float] = {}
        self.q_total = self.q_unassigned = self.q_gap = 0.0

    # ---- the funnel, in the order the guideline eliminates things ---------------------
    def _select(self) -> Tuple[gpd.GeoDataFrame, K.Funnel]:
        p = self.inp.plots
        fn = self.rec.funnel("plots -> load units", len(p))

        out = p[p.get("IN_BND", pd.Series(1, index=p.index)).astype(int) == 1]
        drop = p.index.difference(out.index)
        if len(drop):
            fn.drop("outside the project boundary", ids=p.loc[drop, "PLOT_ID"].tolist())
            self._name_unassigned(p.loc[drop], "outside the project boundary")

        q = pd.to_numeric(out["Q_AVG_M3D"], errors="coerce").fillna(0.0)
        keep = out[q > 0]
        drop = out.index.difference(keep.index)
        if len(drop):
            # Not a loss. A service parcel, an agricultural plot with no dwelling and an
            # industrial plot with no allowance generate no wastewater, so they are not load
            # units and there is nothing to connect. They are named anyway - a plot that
            # leaves the chain without a name is exactly how W10 lost 1,233 m3/d.
            why = out.loc[drop, "ZERO_WHY"].fillna("no load").astype(str)
            for reason, sub in out.loc[drop].groupby(why):
                fn.drop(f"no wastewater load ({reason})", ids=sub["PLOT_ID"].tolist())
                self._name_unassigned(sub, f"no wastewater load ({reason})")
        return keep, fn

    def _name_unassigned(self, sub: pd.DataFrame, why: str) -> None:
        for r in sub.itertuples():
            self.unassigned.append(dict(PLOT_ID=str(r.PLOT_ID), CLASS=getattr(r, "CLASS", ""),
                                        CAT=getattr(r, "CAT", ""),
                                        Q_ADF_M3D=float(getattr(r, "Q_AVG_M3D", 0.0) or 0.0),
                                        N_PROP=float(getattr(r, "N_PROP", 0.0) or 0.0),
                                        WHY=why))

    # ---- the build --------------------------------------------------------------------
    def run(self) -> gpd.GeoDataFrame:
        plots, fn = self._select()
        self.rec.metric("load_units", len(plots))
        self.rec.metric("qadf_m3d_in", round(float(plots.Q_AVG_M3D.sum()), 1))

        fr = Frontages(self.inp, self.rec)
        frontages, rejected = fr.build(plots)
        if rejected:
            fn.drop(f"no carrier within {CARRIER_SEARCH_M:.1f} m",
                    ids=plots.loc[list(rejected), "PLOT_ID"].tolist())
            for i, why in rejected.items():
                self._name_unassigned(plots.loc[[i]], why)

        # The 45 m tertiary limit, applied BEFORE the levels. A plot beyond it is not a level
        # problem; it is a chamber the layout does not have, and it goes back as coordinates.
        reach_over: List[Frontage] = [f for f in frontages if f.leg_len > TERTIARY_MAX_LEN_M]
        frontages = [f for f in frontages if f.leg_len <= TERTIARY_MAX_LEN_M]
        if reach_over:
            fn.drop(f"no chamber within the {TERTIARY_MAX_LEN_M:.0f} m tertiary run "
                    "(G203-p22 Tab 6)",
                    ids=plots.loc[[f.plot_i for f in reach_over], "PLOT_ID"].tolist())
            for f in reach_over:
                row = plots.loc[f.plot_i]
                self._name_unassigned(plots.loc[[f.plot_i]],
                                      f"nearest chamber {f.leg_len:.1f} m away along the "
                                      f"tertiary path, over the {TERTIARY_MAX_LEN_M:.0f} m "
                                      f"limit (G203-p22 Tab 6)")
                self.requests.append(dict(PLOT_ID=str(row.PLOT_ID), X=f.gate[0], Y=f.gate[1],
                                          REACH=str(self.carriers.EDGE_UID.iloc[f.reach_i]),
                                          STATION_M=round(f.station, 2),
                                          SHORT_BY_M=round(f.leg_len - TERTIARY_MAX_LEN_M, 2),
                                          ISSUE="beyond the 45 m tertiary run"))
        # The finding, made actionable. A plot beyond the 45 m tertiary run is not a plot
        # problem, it is a chamber the layout does not have - so what goes back to the
        # chamber stage is the SPACING that would clear it, not a count of failures.
        # A chamber every S metres puts the worst mid-block frontage S/2 along the street,
        # and the tertiary allowance left for that run is 45 m minus the plot's own offset
        # from the carrier. Taking the 90th percentile offset as the design case:
        #     S_max = 2 x (45 - offset_p90)
        # Table 12's 100 m (G203-p30) is a MAINTENANCE maximum and is not this number.
        offs = np.array([f.offset for f in (frontages + reach_over)], dtype="float64")
        if offs.size:
            for pct in (50, 90):
                o = float(np.percentile(offs, pct))
                self.stats[f"offset_p{pct}_m"] = round(o, 2)
                # A negative answer is not a spacing of zero. It means the plot at that
                # percentile has already spent the whole 45 m allowance getting off its own
                # boundary to the carrier, and NO chamber spacing fixes that - it needs a
                # nearer corridor. Recorded as -1 so the summary can say which problem it is.
                s = 2.0 * (TERTIARY_MAX_LEN_M - o)
                self.stats[f"chamber_spacing_p{pct}_m"] = round(s, 1) if s > 0 else -1.0
        if reach_over:
            sh = np.array([f.leg_len - TERTIARY_MAX_LEN_M for f in reach_over])
            self.stats["shortfall_median_m"] = round(float(np.median(sh)), 1)
            self.stats["shortfall_max_m"] = round(float(sh.max()), 1)

        riders = group_riders(frontages)
        self.rec.metric("riders", len(riders))
        self._level_and_emit(plots, riders)

        if self.degenerate:
            fn.drop("the carrier runs through or along the plot boundary - no right-of-way "
                    "for a property connection chamber", ids=self.degenerate)
        fn.close(len(set(r["PLOT_ID"] for r in self.rows)))
        gdf = gpd.GeoDataFrame(self.rows, geometry=self.geoms, crs=K.CRS_EPSG)

        # The funnel closes on COUNTS. This closes on LOAD, which is the quantity that
        # actually matters and the one W10 lost 1,233 m3/d of. A plot's flow either reaches a
        # chamber or appears by name in the not-served file; there is no third place for it
        # to be, and if the two do not add up the stage says so instead of publishing.
        self.q_total = float(pd.to_numeric(self.inp.plots.Q_AVG_M3D,
                                           errors="coerce").fillna(0.0).sum())
        self.q_unassigned = float(sum(u["Q_ADF_M3D"] for u in self.unassigned))
        self.q_gap = self.q_total - K.value("tertiary_qadf_m3d", gdf) - self.q_unassigned
        if abs(self.q_gap) > 0.1:
            raise K.ContractError(
                f"LOAD DOES NOT BALANCE: {self.q_total:,.1f} m3/d in the plot file, "
                f"{K.value('tertiary_qadf_m3d', gdf):,.1f} reaching a chamber, "
                f"{self.q_unassigned:,.1f} named as unassigned - {self.q_gap:,.1f} m3/d is in "
                "neither place. Invariant 1: every load unit is assigned to exactly one "
                "chamber, or listed by name. W10 lost 1,233 m3/d (1.7 %) precisely here, "
                "because an assignment radius failed quietly and nobody differenced the "
                "totals.")
        return gdf

    # ---- levels and geometry ----------------------------------------------------------
    def _level_and_emit(self, plots: gpd.GeoDataFrame, riders: List[Rider]) -> None:
        # One terrain pass for every PCC that needs a ground level. Sampled at the plot end,
        # not at the chamber: a plot 40 m off the street can sit a metre above or below it,
        # and a connection levelled off the street has unknown cover at the end that matters.
        pts = [f.pcc for rd in riders for f in rd.members]
        grd_all = self.ground.at(pts)

        # Column access by attribute inside a 60,000-row loop is the slow way round; the
        # values are pulled out once and looked up by index.
        cls_of = plots["CLASS"].astype(str).to_dict() if "CLASS" in plots.columns else {}
        pid_of = plots["PLOT_ID"].astype(str).to_dict()
        q_of = pd.to_numeric(plots["Q_AVG_M3D"], errors="coerce").fillna(0.0).to_dict()
        np_of = pd.to_numeric(plots["N_PROP"], errors="coerce").fillna(0.0).to_dict()

        carriers = self.carriers
        n_backdrop = n_nodrain = n_deep = n_grd_fallback = 0
        shortfall: List[float] = []      # how far below the flow line a failed arrival lands
        gi = 0

        for rd in riders:
            line = carriers.geometry.iloc[rd.reach_i]
            src = str(carriers.SRC.iloc[rd.reach_i])
            conf = str(carriers.CONFIDENCE.iloc[rd.reach_i])
            # SYSTEM comes from the CARRIER, not the chamber: the connection is laid in that
            # corridor and it is the reach that conveys the flow. Where the upstream layers
            # disagree between the two - and in the layer read on 2026-09-02 they disagree on
            # most rows - the count is reported back rather than silently resolved here.
            sysv = str(carriers.SYSTEM.iloc[rd.reach_i]) if "SYSTEM" in carriers.columns \
                else "central"
            if sysv not in K.SYSTEM:
                sysv = "central"
            nd = self.node.loc[rd.out_node]
            node_xy = (float(nd.X), float(nd.Y))
            pkg = str(getattr(nd, "PACKAGE", "") or "")
            phase = int(getattr(nd, "PHASE", 0) or 0)

            g_of = {}
            for f in rd.members:
                g_of[f.plot_i] = float(grd_all[gi]); gi += 1

            # Solve from the chamber BACKWARDS. `members` is furthest-first, so reverse it:
            # the level of every upstream member depends on where the one below it sits.
            chain = list(reversed(rd.members))
            inv_target = float(nd.INV_M)         # the chamber flow line, for the first member
            end_xy = node_xy                     # ... and the point it discharges at
            end_station: Optional[float] = None  # None => discharge at the reach end/chamber
            # Once a member of a chain cannot drain, NOTHING above it drains either - its
            # flow path runs through that pipe. Marking the upstream members "assigned"
            # because their own local solve worked is precisely the kind of optimism that
            # lets a network report load it never receives.
            dead_below = ""

            for k, f in enumerate(chain):
                is_future = cls_of.get(f.plot_i, "") == FUTURE_CLASS
                at_chamber = (end_station is None)

                # --- geometry, EXCLUSIVE to this plot so no metre is counted twice --------
                # PCC -> HCC -> gate -> along the carrier -> (the chamber, or the gate of the
                # member below). The union of every row is the tertiary network, once over.
                if at_chamber:
                    tail = _substring(line, f.station,
                                      0.0 if rd.to_us else float(line.length)) + [end_xy]
                else:
                    tail = _substring(line, f.station, float(end_station))
                head = [f.hcc] if is_future else [f.pcc, f.hcc]
                coords = _clean(head + [f.gate] + tail)
                if len(coords) < 2 or LineString(coords).length < 0.05:
                    # The whole chain has collapsed to a point, which happens only when the
                    # carrier runs through or along the plot boundary AND its gate lands on
                    # the chamber. That is not a plot with a very short connection - it is a
                    # CORRIDOR fault: there is no right-of-way between the plot and the pipe,
                    # so there is nowhere to put the PCC or the HCC. It goes back to the
                    # corridor stage named, and the next member up still discharges where
                    # this one would have.
                    why = (f"the carrier runs through or along the plot boundary (offset "
                           f"{f.offset:.2f} m) and its gate lands on the chamber - no "
                           f"right-of-way for a property connection chamber; the corridor "
                           f"needs re-cutting")
                    self._name_unassigned(plots.loc[[f.plot_i]], why)
                    self.degenerate.append(pid_of.get(f.plot_i, ""))
                    self.requests.append(dict(PLOT_ID=pid_of.get(f.plot_i, ""),
                                              X=f.gate[0], Y=f.gate[1],
                                              REACH=str(carriers.EDGE_UID.iloc[rd.reach_i]),
                                              STATION_M=round(f.station, 2),
                                              SHORT_BY_M=0.0, ISSUE="corridor through plot"))
                    continue
                geom = LineString(coords)

                # HCC to the gate: the spur across whatever offset the PC sewer did not
                # cover. Everything past the gate runs along the carrier, and the invert at
                # the gate is what the member above discharges onto.
                spur = max(0.0, f.offset - HCC_OFFSET_M)

                # --- levels ------------------------------------------------------------
                grd_up = g_of[f.plot_i]
                grd_fallback = not np.isfinite(grd_up)
                if grd_fallback:
                    # The terrain sample failed at the plot end, so the CHAMBER's ground is
                    # substituted. That is the exact substitution `Ground` exists to prevent
                    # ("a connection levelled off the street has unknown cover at the end
                    # that matters"), so it is counted and it goes onto the row - a silent
                    # substitution here would be a whole missing VRT publishing 45,127
                    # connections levelled off the street with nothing to show it.
                    grd_up = float(nd.GRD_M)
                    n_grd_fallback += 1
                # A stub starts at the HCC in the ROW and has no PC sewer at all - the pipe is
                # capped at the frontage - so its whole length is a rider/lateral leg at the
                # 1 % floor. A live connection carries a 2.5 m PC sewer at its own 3 % floor
                # first, then the same leg. Both floors are G203-p18 Tab 5.
                pcs_len = 0.0 if is_future else min(f.pcs_len, geom.length)
                link = Link(length=max(geom.length - pcs_len, 1e-6), pcs_len=pcs_len,
                            grd_up=grd_up, s_min_pct=RIDER_MIN_SLOPE_PCT,
                            d_min=PCS_MIN_INV_DEPTH_M, d_max=HCC_MAX_DEPTH_M,
                            inv_target=inv_target, at_chamber=at_chamber)
                if self.levels_known:
                    link.solve()
                else:
                    # No chamber invert exists yet, so there is nothing to solve against.
                    # The connection is DECLARED at the guideline minimum rather than
                    # computed, CAN_DRAIN is left null (not checked, which is different from
                    # checked and failed), and the row says so. Re-run after the levelling
                    # stage and every one of these is replaced by a solve.
                    link.slope_pct = RIDER_MIN_SLOPE_PCT
                    link.inv_up = grd_up - PCS_MIN_INV_DEPTH_M - link.pcs_fall
                    link.inv_pcc = link.inv_up + link.pcs_fall
                    link.inv_arrive = link.inv_up - RIDER_MIN_SLOPE_PCT / 100.0 * link.length
                    link.can_drain = 1
                    link.note = ""

                if grd_fallback and not link.note:
                    link.note = ("ground taken from the chamber, not the plot - the 0.5 m "
                                 "terrain VRT returned no value at the PCC, so COVER_M here "
                                 "is the street's cover and not this plot's")
                if dead_below and link.can_drain and self.levels_known:
                    link.can_drain = 0
                    link.note = f"the rider below it does not drain: {dead_below}"
                if link.drop_m > DROP_TRIGGER_M:
                    n_backdrop += 1
                if not link.can_drain:
                    n_nodrain += 1
                    if not dead_below:
                        dead_below = link.note
                    shortfall.append(max(0.0, inv_target - link.inv_arrive))
                if (grd_up - link.inv_up) > HCC_MAX_DEPTH_M + 1e-6:
                    n_deep += 1

                # --- how many OD160 connections does this plot need? --------------------
                # G203-p19 3.4: "big plots might require more than one property connection".
                # The guideline's trigger is plot SIZE and it gives no number, so the test
                # made here is hydraulic instead: one OD160 at the laid gradient inside its
                # d/D limit (0.65 to DN350, G203-p27 Tab 10). Over all 64,071 plots this
                # returns 1 everywhere - the largest peaks near 7 L/s against 20 L/s of
                # capacity - and it is COMPUTED rather than assumed, so the day a 500 m3/d
                # consumer appears the layer says two pipes instead of overloading one.
                qadf = float(q_of.get(f.plot_i, 0.0))
                n_conn = self._connections_needed(qadf, link.slope_pct)

                why = ("assigned; capped stub-out at the frontage, plot not yet built "
                       "(G203-p19 3.4)" if is_future else "assigned")
                if not link.can_drain:
                    why = f"cannot drain to {rd.out_node}: {link.note}"
                    self._name_unassigned(plots.loc[[f.plot_i]], why)
                elif link.note:
                    why = f"assigned; {link.note}"
                if not self.levels_known:
                    why += ("; LEVELS PENDING - gradient is the G203-p18 Tab 5 minimum, not a "
                            "solve, and the arrival at the chamber is unchecked")

                for _c in range(n_conn):
                    # A second connection is a SECOND PIPE, so it is offset into its own
                    # trench rather than drawn on top of the first. Translation preserves
                    # length exactly, which keeps LEN_M and the geometry in agreement.
                    g_c = geom if _c == 0 else _offset(geom, 1.0 * _c)
                    self._n += 1
                    self.rows.append(dict(
                        CONN_ID=f"C{self._n:07d}",
                        PLOT_ID=pid_of.get(f.plot_i, ""),
                        OUT_NODE=rd.out_node if link.can_drain else "",
                        WHY=why,
                        SYSTEM=sysv if link.can_drain else "unserved",
                        CONN_TYPE=("stub" if is_future else
                                   ("lateral" if at_chamber else "rider")),
                        Q_ADF_M3D=qadf / n_conn,
                        N_PROP=float(np_of.get(f.plot_i, 0.0)) / n_conn,
                        LEN_M=float(g_c.length),
                        SLOPE_LAID=round(link.slope_pct, 4),
                        COVER_M=max(0.0, round(link.cover_min, 3)),
                        # null, not 1: "not checked" and "checked and it drains" are
                        # different answers, and only one of them is a design statement.
                        CAN_DRAIN=(int(link.can_drain) if self.levels_known else None),
                        SRC=src, CONFIDENCE=conf, STAGE=STAGE,
                        PACKAGE=pkg, PHASE=phase))
                    self.geoms.append(g_c)

                # The member above discharges onto THIS pipe at THIS gate, so that gate's
                # invert is the next target. No drop is available mid-pipe - there is no
                # structure there - which is why Link.solve() trims the gradient instead.
                inv_target = link.inv_up - link.slope_pct / 100.0 * spur
                end_xy, end_station = f.gate, f.station

        self.stats.update(backdrops=n_backdrop, cannot_drain=n_nodrain,
                          chambers_over_2m=n_deep,
                          ground_from_chamber=n_grd_fallback)
        if shortfall:
            # The actionable half of "cannot drain": how much shallower the chamber would
            # have to sit. A 0.10 m answer is a levelling decision for stage 5; a 2 m answer
            # is a plot the gravity network genuinely does not serve.
            s = np.array([v for v in shortfall if v > 0]) if any(v > 0 for v in shortfall) \
                else np.array([0.0])
            self.stats["nodrain_shortfall_median_m"] = round(float(np.median(s)), 2)
            self.stats["nodrain_shortfall_max_m"] = round(float(s.max()), 2)

    @staticmethod
    def _connections_needed(qadf_m3d: float, slope_pct: float) -> int:
        """How many OD160 property connections this plot's saturation flow needs.

        Peak flow uses Merrimack (G201-p71). Below 100 properties G201 prescribes NO formula
        (contract PF_METH 'held'), so applying Merrimack here is an ASSUMPTION - and it is the
        conservative one, returning about 6.0 on a single dwelling against Peltier's 4.6 and
        the guideline's own 5.0 advisory. It is used only to test capacity, never published.
        """
        if qadf_m3d <= 0:
            return 1
        pf = C.pf_merrimack(qadf_m3d / 1000.0)
        q_pk = qadf_m3d * pf / 86400.0                       # m3/s
        cap = hydra.q_partial(C.internal_diameter(DN_TERTIARY), slope_pct / 100.0,
                              hydra.dod_limit(DN_TERTIARY))
        return max(1, int(math.ceil(q_pk / cap - 1e-9)))


# --------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------

@K.published("tertiary_km", "km", "s5b_tertiary")
def tertiary_km(gdf) -> float:
    """The ONE definition of tertiary pipe length: everything DRAWN on the layer.

    Every row's geometry is exclusive to its own plot, so this sum is a quantity and not an
    overlapping total. It is not the buildable quantity - see tertiary_km_drainable - and the
    two are separate functions rather than one function with a flag, because the project
    already has seven different lifting-station counts in circulation from exactly that
    habit (P2).
    """
    return float(pd.to_numeric(gdf.LEN_M, errors="coerce").sum()) / 1000.0


@K.published("tertiary_km_drainable", "km", "s5b_tertiary")
def tertiary_km_drainable(gdf) -> float:
    """The length that actually drains. A connection with CAN_DRAIN = 0 is drawn so the plot
    is visible on the map and in the schedule, but it is not pipe anyone can build yet, and
    it must never reach a bill of quantities."""
    g = gdf[pd.to_numeric(gdf.CAN_DRAIN, errors="coerce").fillna(1) == 1]
    return float(pd.to_numeric(g.LEN_M, errors="coerce").sum()) / 1000.0


@K.published("tertiary_qadf_m3d", "m3/d", "s5b_tertiary")
def tertiary_qadf(gdf) -> float:
    """Load that reaches a chamber. A row with no OUT_NODE carries load the network does not
    receive, so counting it here would restate W10's 1,233 m3/d as if it had arrived."""
    g = gdf[gdf.OUT_NODE.astype(str).str.strip() != ""]
    return float(pd.to_numeric(g.Q_ADF_M3D, errors="coerce").sum())


def _spacing_line(st: Dict[str, float]) -> str:
    """Say which of the two problems the numbers describe.

    A chamber spacing only helps a plot that is close to its carrier. Where the offset alone
    has spent the 45 m allowance, no spacing fixes it and reporting one would send the
    chamber stage to work on the wrong thing - the corridor is too far away, which is a
    stage 2 answer, or a plot served by another system, which is a stage 1 answer.
    """
    out = []
    for pct in (50, 90):
        s = st.get(f"chamber_spacing_p{pct}_m")
        if s is None:
            continue
        out.append(f"p{pct} " + (f"{s:.0f} m" if s > 0 else
                                 "NO spacing helps - the offset alone exceeds 45 m"))
    return ", ".join(out) or "n/a"


def summarise(gdf: gpd.GeoDataFrame, t: Tertiary, fn_line: str) -> str:
    n = len(gdf)
    assigned = gdf[gdf.OUT_NODE.astype(str).str.strip() != ""]
    by_type = gdf.CONN_TYPE.value_counts().to_dict()
    L = ["", f"  upstream read: {t.source}"]
    if not t.levels_known:
        L += [
            "",
            "  +-----------------------------------------------------------------------+",
            "  | LEVELS PENDING. The chamber layer carries no INV_M, so the gradients   |",
            "  | below are the G203-p18 Tab 5 MINIMA declared as placeholders, not a    |",
            "  | solve, and CAN_DRAIN is null - not checked, which is not the same as   |",
            "  | checked and passing. What IS designed here is the ASSIGNMENT: which    |",
            "  | plot enters the network at which chamber, by what route, over what     |",
            "  | length. The levelling stage needs exactly that to accumulate flow, so  |",
            "  | the order is assign -> level -> RE-RUN THIS STAGE, and the re-run      |",
            "  | replaces every placeholder with a solve.                               |",
            "  +-----------------------------------------------------------------------+",
        ]
    L += [
        "",
        f"  {fn_line}",
        f"  connections written        {n:,}   ({gdf.PLOT_ID.nunique():,} plots)",
        "  by type                    " + ", ".join(f"{k} {v:,}" for k, v in sorted(by_type.items())),
        f"  assigned to a chamber      {len(assigned):,}",
        f"  tertiary pipe drawn        {K.value('tertiary_km', gdf):,.2f} km at OD{DN_TERTIARY}"
        f"  (G203-p22 Tab 6 minimum)",
        f"  ... of which buildable     {K.value('tertiary_km_drainable', gdf):,.2f} km",
        f"  load reaching a chamber    {K.value('tertiary_qadf_m3d', gdf):,.1f} m3/d",
        f"  gradient {'laid':<18}{gdf.SLOPE_LAID.min():.2f} - {gdf.SLOPE_LAID.max():.2f} %"
        f"  (G203-p18 Tab 5: 3-10 % PCS, 1-10 % rider)"
        if t.levels_known else
        f"  gradient (placeholder)     {gdf.SLOPE_LAID.min():.2f} - "
        f"{gdf.SLOPE_LAID.max():.2f} %  = the G203-p18 Tab 5 minima, NOT a solve",
        f"  minimum cover              {gdf.COVER_M.min():.2f} m"
        f"  (G203-p19 3.5 requires {PCS_MIN_COVER_M:.2f} m)",
    ] + ([
        f"  external backdrops needed  {t.stats.get('backdrops', 0):,}   (G203-p19 3.6, fall > 0.60 m)",
        f"  cannot drain by gravity    {t.stats.get('cannot_drain', 0):,}"
        f"   (chamber sits {t.stats.get('nodrain_shortfall_median_m', 0)} m too deep at the "
        f"median, {t.stats.get('nodrain_shortfall_max_m', 0)} m at worst)",
        f"  chambers over 2.00 m deep  {t.stats.get('chambers_over_2m', 0):,}   (G203-p19 3.4)",
    ] if t.levels_known else [
        "  backdrops / drainability   NOT CHECKED - waiting on the chamber inverts",
    ]) + [
        "",
        "  BACK TO THE CHAMBER STAGE",
        f"    plots beyond the {TERTIARY_MAX_LEN_M:.0f} m tertiary run   "
        f"{sum(1 for r in t.requests if r['ISSUE'].startswith('beyond')):,}",
        f"    carrier runs through the plot      "
        f"{sum(1 for r in t.requests if r['ISSUE'] == 'corridor through plot'):,}"
        f"   (a corridor fault, not a chamber one)",
        "    ... coordinates for both in run/s5b_chamber_requests.csv",
        f"    shortfall, median / worst          "
        f"{t.stats.get('shortfall_median_m', 0)} / {t.stats.get('shortfall_max_m', 0)} m",
        f"    plot offset from its carrier       "
        f"p50 {t.stats.get('offset_p50_m', 0)} m, p90 {t.stats.get('offset_p90_m', 0)} m",
        "    chamber spacing that would clear   " + _spacing_line(t.stats),
        "    - Table 12's 100 m (G203-p30) is a MAINTENANCE maximum and does not satisfy",
        "      the tertiary limit. NAMA's built network runs 32.3 chambers/km, about 31 m,",
        "      which does - the calibration agrees with the rule.",
        "",
        "  LOAD BALANCE  (invariant 1: every load unit assigned, or named)",
        f"    every plot in the file             {t.q_total:>12,.1f} m3/d",
        f"    reaching a chamber                 {K.value('tertiary_qadf_m3d', gdf):>12,.1f} m3/d",
        f"    named, not connected here          {t.q_unassigned:>12,.1f} m3/d"
        f"   ({len(t.unassigned):,} plots, run/s5b_unassigned.csv)",
        f"    unaccounted                        {t.q_gap:>12,.1f} m3/d"
        + ("   <- W10 lost 1,233 m3/d exactly here" if abs(t.q_gap) > 0.1 else ""),
    ]
    return "\n".join(L)


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------

def build(gpkg: Optional[str] = None, root: str = W11A_ROOT, plots_path: str = PLOT_LOADS,
          terrain: str = TERRAIN, strict_upstream: bool = False,
          mirror: bool = True) -> Optional[gpd.GeoDataFrame]:
    """Run the stage. Returns the published layer, or None when it stopped on an input."""
    # A manifest PER STAGE, which is the convention the other stages here already follow
    # (manifest_s1_scope.json, manifest_s4.json, ...). `Manifest.records` is a class
    # attribute that starts empty in each process and `save()` writes the whole list, so a
    # shared `manifest.json` does not accumulate stages - it ends up holding only whichever
    # stage ran last. Writing to the shared name silently erased the other stages' records
    # once during this build; that is the reason for this line.
    with K.Manifest.stage(STAGE, STAGE_ORDER,
                          path=os.path.join(root, "run",
                                            f"manifest_{STAGE}.json")) as rec:
        ran, msgs = verify_constants()
        if not ran:
            rec.note("CONSTANT GATE DID NOT RUN: " + "; ".join(msgs))
            print("  ! constant gate did not run:", "; ".join(msgs))
        elif msgs:
            rec.note("CONSTANT GATE FAILED: " + "; ".join(msgs))
            raise K.ContractError(
                "a design constant no longer matches the page it cites (philosophy P9):\n  "
                + "\n  ".join(msgs))
        else:
            rec.note(f"constant gate: {len(_CONSTANT_GATE)} phrases re-read from "
                     "PAM-GUD-203 pp17-22 and all still present")

        try:
            inp = Inputs.load(gpkg, plots_path, terrain, strict_upstream)
        except Missing as m:
            rec.did_nothing(f"waiting on {m}")
            print(f"\n{STAGE}: STOPPED - waiting on an upstream stage.\n")
            print(f"    needs: {m}\n")
            print("    Nothing was written. This stage designs the pipe between a plot and a")
            print("    CHAMBER, so it cannot run before the chamber layer exists.")
            return None

        rec.read("plot_loads", plots_path, len(inp.plots))
        rec.read("nodes", inp.source, len(inp.nodes))
        rec.read("reaches", inp.source, len(inp.reaches))
        if inp.levelled_elsewhere:
            rec.note("LEVELLED NODES EXIST ELSEWHERE: " + inp.levelled_elsewhere)
            print("  ! " + inp.levelled_elsewhere)
        if not inp.levels_known:
            rec.note("LEVELS PENDING: the chamber layer carries no INV_M, so every "
                     "SLOPE_LAID is the G203-p18 Tab 5 minimum DECLARED as a placeholder and "
                     "CAN_DRAIN is null (not checked). What is designed is the assignment - "
                     "plot to chamber, route and length - which is what the levelling stage "
                     "accumulates flow from. Re-run this stage after it publishes inverts.")

        t = Tertiary(inp, rec)
        gdf = t.run()

        p = K.publish(gdf, "connections", root, stage=STAGE)
        rec.wrote("connections", p, len(gdf))
        shp = K.mirror_shapefile(gdf, "connections", root) if mirror else ""
        if shp:
            rec.wrote("connections (CAD mirror)", shp, len(gdf))

        # Derived from `root`, never from a module constant: the self-test runs the whole
        # stage against a fixture, and a fixed run directory would have it quietly overwrite
        # the real run's not-served register with 33 test rows.
        run_dir = os.path.join(root, "run")
        os.makedirs(run_dir, exist_ok=True)
        if t.unassigned:
            # Invariant 1: assigned to exactly one chamber, OR LISTED BY NAME. The Funnel
            # truncates its id list at 200; this is the full list, and it is the file the
            # not-served schedule is built from.
            up = os.path.join(run_dir, "s5b_unassigned.csv")
            pd.DataFrame(t.unassigned).to_csv(up, index=False, encoding="utf-8")
            rec.wrote("unassigned plots (named)", up, len(t.unassigned))
        if t.requests:
            cr = os.path.join(run_dir, "s5b_chamber_requests.csv")
            pd.DataFrame(t.requests).to_csv(cr, index=False, encoding="utf-8")
            rec.wrote("chamber requests", cr, len(t.requests))

        rec.metric("tertiary_km", round(K.value("tertiary_km", gdf), 3))
        rec.metric("tertiary_km_drainable", round(K.value("tertiary_km_drainable", gdf), 3))
        rec.metric("qadf_m3d_to_chamber", round(K.value("tertiary_qadf_m3d", gdf), 1))
        rec.metric("dn_tertiary_mm", DN_TERTIARY)
        for k, v in t.stats.items():
            rec.metric(k, v)
        rec.note("DN is not on the layer: the contract's connections spec declares none, and "
                 "a field is not added here (EXCLUDED: 'a per-stage schema'). Every "
                 f"connection is OD{DN_TERTIARY}, G203-p22 Tab 6 minimum.")
        rec.note("AUDIT GAP: none of audit.py's 22 checks reads this layer - all of them "
                 "take ctx.pipes (the gravity reaches) or ctx.nodes. So "
                 f"{K.value('tertiary_km', gdf):,.0f} km of OD{DN_TERTIARY}, roughly half the "
                 "length of the gravity network, is verified only by contract.validate() and "
                 "by this stage's own arithmetic. Philosophy sec 8 wants one check per "
                 "constraint; the tertiary gradients (G203-p18 Tab 5), the 0.60 m cover "
                 "(p19 3.5), the 45 m run (p22 Tab 6), the 3-HCC rule (p17 3.2) and the "
                 "600 mm arrival (p19 3.6) each need one.")
        rec.note(f"the {PCS_MAX_LEN_M:.0f} m PC-sewer limit (G203-p18, note under Tab 4) does "
                 f"not bind at concept scale: the PCC is placed at the plot boundary and the "
                 f"HCC {HCC_OFFSET_M} m into the ROW (G203-p17 3.2), so the PC sewer is "
                 f"{HCC_OFFSET_M} m by construction. It binds in detailed design, where the "
                 "PCC sits at the building and the run across a deep plot is real. The 45 m "
                 "that governs here is a different rule on a different pipe - G203-p22 Tab 6, "
                 "Lateral Sewer.")

        print(summarise(gdf, t, rec.funnels[0].line() if rec.funnels else ""))
        print(f"\n  published  {p}")
        if shp:
            print(f"  mirrored   {shp}")
        return gdf


# --------------------------------------------------------------------------------------
# Self-test: prove the stage works on real plot geometry before the chambers exist
# --------------------------------------------------------------------------------------

def _synthetic_upstream(out_gpkg: str, plots_path: str = PLOT_LOADS,
                        terrain: str = TERRAIN) -> Tuple[str, int]:
    """Build a small, CONTRACT-VALID `nodes` + `reaches` pair over REAL plots and a REAL
    drafted corridor, so the stage can be exercised end to end before stage 5a exists.

    This is a test fixture and it is written to a scratch path, never to W11a/shp - a
    synthetic chamber layer sitting next to the deliverables is exactly how a fixture becomes
    a design. It uses the real corridor alignment, the real terrain and real plot polygons,
    so what it proves about the geometry and the levels is real.
    """
    corridors = os.path.join(REPO_ROOT, "W10", "shp", "W10_corridors_drafted.shp")
    cg = gpd.read_file(corridors)
    if cg.crs is None or cg.crs.to_epsg() != K.CRS_EPSG:
        cg = cg.set_crs(K.CRS_EPSG, allow_override=True)
    plots = gpd.read_file(plots_path, layer=PLOT_LOADS_LAYER)

    # Pick a real street that fronts BOTH built and planned plots. Scored on the smaller of
    # the two counts, deliberately: a corridor with 300 vacant plots and none built exercises
    # only the stub branch, and a test that never runs the live property connection proves
    # nothing about it.
    cand = cg[(cg.length > 300) & (cg.length < 900)].reset_index(drop=True)
    pc = plots[plots.Q_AVG_M3D > 0].copy()
    built_c = list(pc[pc.CLASS != FUTURE_CLASS].geometry.centroid.values)
    plan_c = list(pc[pc.CLASS == FUTURE_CLASS].geometry.centroid.values)
    t_built, t_plan = STRtree(built_c), STRtree(plan_c)
    best, best_score, best_nb, best_np = None, -1, 0, 0
    for i, g in enumerate(cand.geometry.values):
        buf = g.buffer(40.0)
        nb, npl = len(t_built.query(buf)), len(t_plan.query(buf))
        if min(nb, npl) > best_score:
            best, best_score, best_nb, best_np = i, min(nb, npl), nb, npl
    line = cand.geometry.iloc[best]
    print(f"  fixture: real drafted corridor #{best}, {line.length:.0f} m, "
          f"{best_nb} built and {best_np} planned plots within 40 m")
    best_n = best_nb + best_np

    # Chambers at 100 m - Table 12's maximum for DN200-315 (G203-p30) - deliberately, so the
    # stage is tested against the spacing a designer who read only Table 12 would produce.
    step = 100.0
    stations = list(np.arange(0.0, line.length, step)) + [line.length]
    xy = [line.interpolate(s).coords[0] for s in stations]
    grd = Ground(terrain).at(xy)
    grd = np.where(np.isfinite(grd), grd, np.nanmean(grd[np.isfinite(grd)]) if
                   np.isfinite(grd).any() else 330.0)

    dn = 200
    d0 = K.min_invert_depth(dn)
    # Fall downhill: order the chain so the flow goes to the lower end.
    if grd[-1] > grd[0]:
        stations, xy, grd = stations[::-1], xy[::-1], grd[::-1]
    inv = [g - d0 for g in grd]          # provisional; the edge loop below chains them

    net = K.Network()
    uids = [net.node(x, y, kind="chamber", tier="lateral", grd_m=float(g), inv_m=float(v),
                     src="draft", confidence="drafted", stage="fixture")
            for (x, y), g, v in zip(xy, grd, inv)]
    net.nodes[uids[0]].kind = "head"
    net.nodes[uids[-1]].kind = "outfall"
    for a, b in zip(uids[:-1], uids[1:]):
        L = math.dist((net.nodes[a].x, net.nodes[a].y), (net.nodes[b].x, net.nodes[b].y))
        q_pk = 5.0                                       # L/s, a plausible lateral
        s_min = hydra.smin_for(dn, q_pk / 1000.0) * 100.0
        # Follow the ground where it falls faster than the minimum, otherwise lay the
        # minimum - the same rule stage 5 will use, so the fixture is not a softer case.
        s_pct = max((net.nodes[a].inv_m - net.nodes[b].inv_m) / L * 100.0, s_min)
        s_pct = _round_step(s_pct, K.SLOPE_STEP_PCT, up=True)
        net.nodes[b].inv_m = net.nodes[a].inv_m - s_pct / 100.0 * L
        y_, v_ = hydra.pipe_state(dn, s_pct / 100.0, q_pk / 1000.0)
        net.add_edge(a, b, tier="lateral", stage="fixture", src="draft",
                     confidence="drafted",
                     attrs=dict(DN=dn, MATERIAL=C.material(dn), CONSTR="open_trench",
                                SLOPE_LAID=round(s_pct, 4), SLOPE_MIN=round(s_min, 4),
                                GRAD_BY="ground", SIZED_BY="minimum",
                                CLEAN_BY="tractive", TAU_PA=C.TAU_PA,
                                PF=3.0, PF_METH="held", QADF_M3D=round(q_pk * 86.4 / 3.0, 3),
                                QINF_LS=0.0, QPK_LS=q_pk,
                                V_PK_MS=round(v_ or 0.0, 3), DOD_PK=round(y_ or 0.0, 3),
                                RET_MIN=round(L / max(v_ or 0.5, 0.01) / 60.0, 3),
                                PAST_CAP=0, CAP_EXIT="", CAP_LEN_M=0.0,
                                TIE_TYPE="none", ON_DUAL_M=0.0, ON_WADI_M=0.0,
                                CROSS_ID=""))

    ng = net.to_nodes_gdf()
    eg = net.to_edges_gdf()
    # Levels on the reach, taken from the nodes so the two layers cannot disagree - which is
    # the W10 defect where the node and pipe layers came out of different solves and differed
    # by up to 10.39 m of depth.
    g_of = ng.set_index("NODE_UID").GRD_M.to_dict()
    i_of = ng.set_index("NODE_UID").INV_M.to_dict()
    eg["INV_UP"] = [i_of[u] for u in eg.US_NODE]
    eg["INV_DN"] = [i_of[v] for v in eg.DS_NODE]
    eg["US_DEPTH"] = [g_of[u] - i_of[u] for u in eg.US_NODE]
    eg["DS_DEPTH"] = [g_of[v] - i_of[v] for v in eg.DS_NODE]
    eg["COVER_US"] = [K.cover(int(d), z) for d, z in zip(eg.DN, eg.US_DEPTH)]
    eg["COVER_DN"] = [K.cover(int(d), z) for d, z in zip(eg.DN, eg.DS_DEPTH)]
    # Fill the node fields the fixture owes the contract, all from the graph it just built.
    dn_of = eg.set_index("US_NODE").DN.to_dict()
    ng["COVER_M"] = [K.cover(int(dn_of.get(u, dn)), d)
                     for u, d in zip(ng.NODE_UID, ng.DEPTH_M)]
    ng["INLET_DEG"] = 180.0
    ng["INLET_FLAG"] = 0
    ng["MH_DIA"] = 1.0
    ng["MH_MAT"] = "concrete"
    ng["DROP_M"] = 0.0
    ng["DROP_TYPE"] = "none"
    ng["VORTEX"] = 0
    ng["Q_ADF_M3D"] = 144.0
    ng["Q_PK_LS"] = 5.0
    ng["N_PROP"] = 10.0
    ng["PAST_CAP"] = 0
    ng["CAP_EXIT"] = ""
    K.validate(ng, "nodes", stage="fixture")
    K.validate(eg, "reaches", stage="fixture")
    K.Network.assert_round_trip(ng, eg)
    K.Network.assert_degrees(ng, eg)

    os.makedirs(os.path.dirname(out_gpkg), exist_ok=True)
    if os.path.exists(out_gpkg):
        os.remove(out_gpkg)
    ng.to_file(out_gpkg, layer="nodes", driver="GPKG")
    eg.to_file(out_gpkg, layer="reaches", driver="GPKG")
    return out_gpkg, best_n


def selftest(scratch: Optional[str] = None) -> None:
    """Exercise the stage end to end on the fixture, then prove the invariants bite."""
    scratch = scratch or os.environ.get("CLAUDE_SCRATCH") or os.path.join(
        os.path.expanduser("~"), ".w11a_s5b_selftest")
    os.makedirs(scratch, exist_ok=True)
    print("SELF-TEST - real plots and a real corridor, synthetic chambers, scratch output")
    print(f"  scratch: {scratch}")

    # --- the level solver, in isolation, at both ends of its range -----------------------
    def mk(leg, target, pcs=HCC_OFFSET_M, grd=330.0, at_ch=True, s_lo=RIDER_MIN_SLOPE_PCT):
        return Link(length=leg, pcs_len=pcs, grd_up=grd, s_min_pct=s_lo,
                    d_min=PCS_MIN_INV_DEPTH_M, d_max=HCC_MAX_DEPTH_M,
                    inv_target=target, at_chamber=at_ch).solve()

    lk = mk(20.0, 328.0)
    assert lk.can_drain == 1 and RIDER_MIN_SLOPE_PCT <= lk.slope_pct <= PCS_MAX_SLOPE_PCT
    assert abs(K.cover(DN_TERTIARY, lk.depth_pcc) - PCS_MIN_COVER_M) < 1e-9, \
        "the shallowest legal start must give exactly the 0.60 m of G203-p19 3.5"
    assert abs(lk.inv_pcc - lk.inv_up - lk.pcs_fall) < 1e-12, "the PC sewer's own fall"

    # THE FIX THIS CLASS EXISTS FOR. Level ground, a DN200 chamber at minimum cover, and a
    # 40 m leg. At the rider's 1 % floor (G203-p18 Tab 5) it drains; forcing the PC sewer's
    # 3 % onto the same leg - which is what one gradient per chain does - condemns it. That
    # single distinction was worth 10,632 connections on the real layers.
    inv_ch = 330.0 - K.min_invert_depth(200)
    assert mk(40.0, inv_ch).can_drain == 1, "a 40 m leg at 1 % must drain to a DN200 chamber"
    assert mk(40.0, inv_ch, s_lo=PCS_MIN_SLOPE_PCT).can_drain == 0, \
        "... and the same leg forced to 3 % must not - that is the whole point"

    # a chamber the plot cannot reach at all: it sits at plot level
    lk = mk(40.0, 330.0)
    assert lk.can_drain == 0 and "below the discharge invert" in lk.note
    # a chamber far below: 10 % maximum, and a backdrop declared
    lk = mk(40.0, 310.0)
    assert lk.slope_pct == PCS_MAX_SLOPE_PCT and lk.drop_m > DROP_TRIGGER_M
    assert "backdrop" in lk.note
    # a stub has no PC sewer at all, so no PC-sewer fall to pay for
    assert mk(20.0, 328.0, pcs=0.0).pcs_fall == 0.0
    print("  level solver ....... ok (min-cover start, the 1 % vs 3 % reach, no-drain, "
          "backdrop, stub)")

    # --- the multi-connection rule, which real data never triggers -----------------------
    assert Tertiary._connections_needed(1.08, 3.0) == 1
    assert Tertiary._connections_needed(176.6, 3.0) == 1, "the largest real plot needs one"
    assert Tertiary._connections_needed(20000.0, 3.0) > 1, \
        "G203-p19 3.4 - a big enough consumer must return more than one connection"
    print("  OD160 capacity rule  ok (1 for every real plot, >1 when the flow demands it)")

    # --- riders never exceed three -------------------------------------------------------
    fs = [Frontage(i, 0, (0, 0), (0, 0), (0, 0), float(i * 10), 2.0, "N1", float(i * 10), True)
          for i in range(7)]
    rs = group_riders(fs)
    assert all(len(r.members) <= MAX_HCC_PER_RIDER for r in rs) and sum(
        len(r.members) for r in rs) == 7
    print(f"  rider grouping ..... ok (7 HCCs -> {len(rs)} riders, none over "
          f"{MAX_HCC_PER_RIDER})")

    # --- the constant gate ---------------------------------------------------------------
    ran, msgs = verify_constants()
    if ran:
        assert not msgs, msgs
        print(f"  constant gate ...... ok ({len(_CONSTANT_GATE)} phrases re-read from the PDF)")
    else:
        print("  constant gate ...... COULD NOT RUN:", "; ".join(msgs))

    # --- the whole stage on real geometry ------------------------------------------------
    fx = os.path.join(scratch, "fixture.gpkg")
    fx, n_near = _synthetic_upstream(fx)
    K.Manifest.records = []
    gdf = build(gpkg=fx, root=scratch, plots_path=PLOT_LOADS, terrain=TERRAIN,
                strict_upstream=True, mirror=True)
    assert gdf is not None and len(gdf), "the fixture produced no connections"
    K.validate(gdf, "connections", stage=STAGE)
    # every metre owned once: the sum of the rows equals the union of their geometry
    from shapely.ops import unary_union
    u = unary_union(list(gdf.geometry.values))
    assert u.length <= gdf.LEN_M.sum() + 1e-6
    # no row is laid outside G203-p18 Tab 5
    assert gdf.SLOPE_LAID.min() >= RIDER_MIN_SLOPE_PCT - 1e-9
    assert gdf.SLOPE_LAID.max() <= PCS_MAX_SLOPE_PCT + 1e-9
    # every assigned row resolves to a real chamber
    nodes = gpd.read_file(fx, layer="nodes")
    have = set(nodes.NODE_UID)
    bad = [u_ for u_ in gdf.OUT_NODE if str(u_).strip() and u_ not in have]
    assert not bad, bad[:5]
    # Both branches must have run. A live property connection starts at the PCC inside the
    # plot; a stub starts at the HCC in the ROW. A fixture that only ever produced one of
    # them would prove nothing about the other, which is why the corridor was chosen on the
    # SMALLER of the built and planned counts.
    kinds = set(gdf.CONN_TYPE)
    assert "stub" in kinds, kinds
    assert kinds & {"lateral", "rider"}, f"no live property connection exercised: {kinds}"
    # the PCS is 2.5 m by construction, so the G203-p18 50 m limit cannot be breached here
    assert gdf.LEN_M.max() <= HCC_OFFSET_M + TERTIARY_MAX_LEN_M + 1e-6
    # A draining connection may only discharge into a chamber or into another DRAINING pipe.
    # This is the regression test for the defect the fixture found: a rider member solved
    # fine on its own levels and was published as "assigned" while the member below it could
    # not drain, so the layer claimed load the network would never have received.
    live = gdf[gdf.CAN_DRAIN == 1]
    npts = [(p.x, p.y) for p in nodes.geometry]
    live_u = unary_union(list(live.geometry.values))
    for r in live.itertuples():
        end = r.geometry.coords[-1]
        on_node = any(math.hypot(end[0] - x, end[1] - y) <= 0.02 for x, y in npts)
        assert on_node or live_u.distance(Point(end)) <= 0.02, \
            f"{r.CONN_ID} drains into something that does not drain"
    # the CAD mirror has to survive the DBF, which is the point of mirror_shapefile()
    back = gpd.read_file(os.path.join(scratch, "shp", "W11a_connections.shp"))
    assert set(K.LAYERS["connections"].required_names) <= set(back.columns), \
        sorted(set(K.LAYERS["connections"].required_names) - set(back.columns))
    print(f"\n  SELF-TEST PASSED - {len(gdf):,} connections on {gdf.PLOT_ID.nunique():,} "
          f"plots of the {n_near:,} within 40 m, {K.value('tertiary_km', gdf):.2f} km, "
          f"types {sorted(kinds)}")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="run the stage against a fixture built from real plots and a real "
                         "corridor, writing to scratch")
    ap.add_argument("--gpkg", default=None,
                    help="read `nodes` and `reaches` from this GeoPackage instead of "
                         "searching the stage outputs in order")
    ap.add_argument("--no-mirror", action="store_true", help="skip the CAD shapefile")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    print(f"{STAGE}  (W11a stage 5b - the tertiary layer)")
    build(gpkg=a.gpkg, mirror=not a.no_mirror)
    return 0


if __name__ == "__main__":
    sys.exit(main())
