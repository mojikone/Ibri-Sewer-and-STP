"""W11a stage 5 - THE CHAMBERS. Philosophy sec 2 step 5, run after the hierarchy and before levels.

WHY A CHAMBER IS THE UNIT OF DESIGN, AND WHAT W10 LOST BY TREATING A CORRIDOR AS ONE

W10 published 20,936 "reaches" that were corridor segments, not chamber-to-chamber pipes.
The consequences, all measured in `W10/docs/research/W8_W10_POSTMORTEM.md`:

    4,763 reaches over the G203-p30 Table 12 spacing - 1,220 km, 64.8 % of the length,
        the longest a single 6,541 m "pipe" with nothing on it. Nobody can build, rod,
        survey or model that.
    11.1 nodes/km against NAMA's built 32.3 and W8's 19.8 - the layer was not a network
        of structures at all.
    7,919 disconnected components at 0.01 m, because connectivity was re-derived by a
        tolerance instead of being an attribute written from a graph.
    No chamber schedule, no profile, no take-off, no SewerGEMS model and no package -
        one absence blocked five deliverables.

So this stage does exactly one thing and does it structurally: it turns directed, tiered
ROUTES into a graph of CHAMBERS and the reaches between them, using `contract.Network`, so
that (a) a reach physically cannot end anywhere but on its own two chambers, (b) a node can
own at most one outgoing reach, and (c) the Table 12 spacing is satisfied by construction
rather than checked afterwards.

WHERE EACH CHAMBER COMES FROM - the six triggers, each with its source

    junction        every point where another route discharges. G203-p29 sec 4.4. A junction
                    that is not a chamber is a blind tee: unrodable, and the inlet angle
                    cannot be controlled.
    head at gate    philosophy sec 4: "A head starts at the gate - on the road, at the foot of
                    the perpendicular from the first plot's centroid." Not at a fixed offset
                    from the junction (criteria ASSUMPTIONS/HEAD_AT_GATE, user 2026-08-20).
                    Everything upstream of the first fronting plot is pipe that serves
                    nothing; W10 laid 117.3 km of exactly that (P7).
    change of       any vertex deflecting more than `criteria.ROAD_COLLINEAR_DEG` (10 deg -
    direction       a break straighter than this is survey wobble and is dissolved), AND any
                    place the straight pipe would stray more than `ROAD_CHORD_DEV_M`
                    (0.50 m) off the corridor it follows. The second rule is what makes P2
                    ("straight between chambers") TRUE rather than aspirational: because
                    every span is split before it strays 0.5 m, the published reach can be
                    a straight two-point line and still sit on the road. ROAD_CHORD_DEV_M
                    was declared in criteria and never enforced ("a W5 item"); it is
                    enforced here.
    change of       G203 requires a chamber at a change of gradient and gives NO numeric
    grade           threshold for it. See PENDING_GRADE_BREAK below - this is the one number
                    in this module that is an assumption, and it is tagged, not buried.
    change of       guaranteed by construction, not by a test: DN and TIER are attributes of
    diameter/tier   a REACH, and a reach begins and ends at a chamber, so a diameter or tier
                    can only change where one already stands. Routes carry one tier each and
                    meet at nodes, so a tier change is always a chamber.
    Table 12        `criteria.mh_max_spacing()` is DN-dependent (100/120/150/200 m) and the
    spacing         diameter is stage 6's. So the fill uses `MH_SPLIT_LEN` = 100 m, which is
                    the value that satisfies EVERY Table 12 class - the only safe choice
                    when the diameter is not yet known, and never wrong afterwards.

THE THREE LAYOUT RULES THAT ARE NOT SPACING

    one outlet per structure   `Network.add_edge` refuses a second outgoing edge. H15 (the
                               forest) becomes unreachable rather than audited.
    10 m branch clearance      `criteria.FANOUT_OFFSET_M`. No chamber sits within 10 m
                               upstream of the junction it discharges into, and a branch
                               with less than 10 m of usable length is absorbed into that
                               junction and COUNTED in a Funnel - never dropped silently.
    inlet angle >= 90 deg      H10, G203-p30. Measured as the angle the arriving flow makes
                               with the departing flow: 180 deg is straight through, 90 deg
                               is a square inlet, below 90 deg the flow is forced to turn
                               back on itself. Every chamber carries INLET_DEG; every one
                               below 90 carries INLET_FLAG = 1 AND IS NAMED, row by row, in
                               `W11a/run/s5_sharp_inlets.csv`. It is not fixed by inserting
                               a bend chamber - the user refused that on 2026-08-20 because
                               it added ~200 chambers for no construction benefit - it is
                               fixed by a purpose-made chamber with a swept channel, which
                               is a priced item and therefore has to be a named list.

WHAT THIS STAGE DOES NOT DECIDE, AND WHY THE FIELDS ARE STILL WRITTEN

`contract.NODES` is the FINAL chamber schedule, so it requires levels and flows that belong
to stage 6. This stage writes them as a declared seed, never as a design:

    INV_M / DEPTH_M / COVER_M   seeded at the SHALLOWEST LEGAL INVERT for the tier's
                                minimum diameter - `contract.min_invert_depth()`, giving
                                exactly 1.30 m of cover (G203-p33). That is not a guess; it
                                is philosophy sec 5's own starting rule, "lay as shallow as
                                H3 allows", and it is the datum every levelling run begins
                                from. Stage 6 pushes it down and owns it thereafter.
    DROP_M / DROP_TYPE / VORTEX zero and "none", because a drop is triggered by an INVERT
                                difference (G203-p30: > 0.60 m backdrop, > 2.0 m vortex
                                shaft) and there are no inverts yet. `classify_drop()` below
                                is THE single definition of that rule (P2, one function per
                                published quantity) and stage 6 imports it rather than
                                writing the thresholds again.
    Q_ADF_M3D / Q_PK_LS/N_PROP  zero. Load ASSIGNMENT is the connections stage; this stage
                                touches plots only to find the gate. A zero here is not a
                                measured zero, and `STAGE` on every row says which stage
                                last wrote it - a node still reading "s5_chambers" has no
                                levels and no flow.

That tension is real and is reported rather than papered over: `contract.NODES` cannot be
LEGALLY published before stage 6, because every level and flow field is required and
non-null. The seed is the least-bad answer available; the alternative (NaN) is refused by
the contract, and the worse alternative (a fabricated gradient) is refused by us.

INPUT - what stage 4 hands over, and what stage 5 makes of it

Stage 4 publishes `W11a/shp/W11a_s4.gpkg`: `s4_reaches`, a DIRECTED TIERED GRAPH of
corridor edges (US_NODE / DS_NODE / TIER / SYSTEM), and `s4_nodes` for the positions those
ids resolve against. Those edges are corridor segments and NOT reaches - median 36 m, but
the longest is 6,541 m, which is W10's headline defect verbatim. Stage 5 groups them into
maximal unbranched RUNS of one tier and one system, and places chambers along each run.

A run breaks exactly where a chamber is required for another reason anyway: where a second
reach arrives (a junction), where the tier changes (which is where the diameter changes,
and a diameter may only change at a chamber), and where the servicing system changes - a
satellite is a different network, not a branch of this one (philosophy sec 8a).

A second handover is also accepted, if stage 4 ever publishes runs directly: a `corridors`
layer carrying TIER and DS_CORR. If neither exists the stage prints exactly what it waits
on and exits 0 - it does not invent a hierarchy. `--rehearse` runs the same engine over
real drafted corridor geometry with a stand-in tiering, writes to `W11a/run/`, and never
touches `W11a/shp/`, so a rehearsal cannot be mistaken for a design.

Sources: `_BRAIN/08_DESIGN_PHILOSOPHY.md` (sec 2 order, sec 4 layout, sec 5 drops, H10/H12/H15),
`_BRAIN/02_DESIGN_CRITERIA.md` via `W8/py/sewnet/criteria.py` (every number),
G203-p29 sec 4.4 / p30 Tab 12 / p30 drops / p30 inlet angle / p33 cover,
`W10/docs/research/W11a_BUILD_BRIEF.md` (P3, P4, invariants 1, 2 and 10).
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

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# The contract puts W8/py on sys.path and imports sewnet.criteria itself, so importing it
# first is what makes `from sewnet.criteria import ...` work below. It is imported HARD, not
# in a try/except: a stage that degrades quietly when the contract is missing is how W10's
# RoadTreatment ran with units=None and three of its steps became no-ops (invariant 10).
from w11a import contract as K                                    # noqa: E402
from w11a.contract import ContractError                           # noqa: E402
from sewnet.criteria import DEFAULT as C                          # noqa: E402

import geopandas as gpd                                           # noqa: E402
import rasterio                                                   # noqa: E402
from shapely.geometry import LineString, Point                    # noqa: E402
from shapely.ops import linemerge, unary_union                    # noqa: E402

import config_w10_reference as P                                  # noqa: E402  paths only

STAGE = "s5_chambers"
STAGE_ORDER = 5

RUN_DIR = os.path.join(K.W11A_ROOT, "run")
SHP_DIR = os.path.join(K.W11A_ROOT, "shp")
GPKG = K.gpkg_path(K.W11A_ROOT)                 # W11a/shp/W11a.gpkg - the audited artefact
ROUTES_LAYER = "corridors"                      # stage 2's layer; carries a tier only if
ROUTES_NEEDS = ("CORR_ID", "TIER", "DS_CORR")   # stage 4 ever publishes runs directly

# The deliverable the brief names. It is a CAD MIRROR: `contract.assert_audited_path()`
# refuses to hand a .shp to the auditor at all, because the DBF truncates GRADIENT_BY to
# GRADIENT_B and audit G2 then fails a design that was correct in memory.
MANHOLES_SHP = os.path.join(SHP_DIR, "W11a_manholes.shp")
SHARP_INLETS_CSV = os.path.join(RUN_DIR, "s5_sharp_inlets.csv")
WADI_CHAMBERS_CSV = os.path.join(RUN_DIR, "s5_wadi_chambers.csv")
JUNCTION_GAPS_CSV = os.path.join(RUN_DIR, "s5_junction_gaps.csv")
SKELETON_GPKG = os.path.join(RUN_DIR, "s5_reach_skeleton.gpkg")   # handover to stage 6

# What stage 4 publishes: a DIRECTED, TIERED graph of corridor edges. Its `s4_reaches` are
# corridor segments, not reaches - median 36 m but the longest 6,541 m - so stage 5 groups
# them into unbranched RUNS and puts chambers on them.
S4_GPKG = os.path.join(SHP_DIR, "W11a_s4.gpkg")
S4_REACHES = "s4_reaches"
S4_NODES = "s4_nodes"


# ======================================================================================
# The one number in this module that is not in 02_DESIGN_CRITERIA.md
# ======================================================================================

PENDING_GRADE_BREAK = dict(
    name="GRADE_BREAK_DEV_M",
    value=0.50,
    units="m",
    rule="G203-p29 sec 4.4 requires a chamber at a change of gradient.",
    gap=("The guideline names the trigger and gives NO numeric threshold for it. Neither "
         "02_DESIGN_CRITERIA.md nor sewnet.criteria carries one. Without a value the rule "
         "cannot be applied at all - the alternative is to ignore 'change of grade', which "
         "is how a pipe ends up laid on a chord 2 m above the ground it is meant to follow "
         "and the cover breaches between chambers (invariant 5: depth is checked BETWEEN "
         "nodes, not only at them)."),
    basis=("0.50 m, taken as the VERTICAL twin of `criteria.ROAD_CHORD_DEV_M` = 0.50 m - "
           "the horizontal departure from the corridor the project already accepts. One "
           "tolerance, two axes. A chamber goes wherever the ground profile departs more "
           "than this from the straight profile through the chambers already placed."),
    sensitivity=("Loosening it to 1.0 m roughly halves the grade-break chambers and lets "
                 "the pipe sit up to 1.0 m off the ground between them; tightening it to "
                 "0.25 m roughly doubles them. It changes chamber COUNT, never compliance - "
                 "cover is enforced by H3 either way."),
    confirm_with="NWS, or accept as a stated design assumption in the report",
)
GRADE_BREAK_DEV_M = float(PENDING_GRADE_BREAK["value"])

# Table 12 is a "shall" (G203-p30) and it is tested on the PUBLISHED reach, which is the
# straight line between two chamber COORDINATES - not the arc of the corridor the stations
# were measured along. Node identity merges anything within `contract.NODE_MERGE_M` (3 m,
# = criteria.MH_SNAP_M: "closer than the clearance => ONE structure"), so either end of a
# reach can be pulled up to 3 m from where the spacing put it. Filling to the bare 100 m
# therefore produced a 100.2 m reach on the first large run - a blocking H12 failure
# measured in centimetres. The fill reserves the merge radius at BOTH ends, which costs
# about 3 % in chamber count and makes H12 true by construction instead of nearly true.
SPACING_TARGET_M = C.MH_SPLIT_LEN - 2.0 * K.NODE_MERGE_M          # 100 - 6 = 94 m

# Numerical, not a design criterion: how finely the ground is read before the 0.50 m test is
# applied to it. 5 m is ten DEM cells (rule 6: 0.5 m terrain). Halving it does not change a
# chamber position by more than the DEM's own noise; the CRITERION is the 0.50 m, not this.
GRADE_SAMPLE_M = 5.0

# H10 is written against 90 deg (G203-p30) and audit.h10 tests exactly that, so 90 is what
# INLET_FLAG is set on. The project ALSO carries a user deviation - criteria.INLET_MIN_DEG =
# 85 deg, "anything sharper than 75 deg is flagged for a look, never fixed by adding a
# chamber" - and those two bands are reported per chamber in the named CSV, because they are
# the difference between a chamber that needs a benched channel and one that needs redesign.
INLET_GUIDELINE_DEG = 90.0
INLET_PROJECT_DEG = float(C.INLET_MIN_DEG)          # 85, stated deviation
INLET_REVIEW_DEG = 75.0                             # criteria ASSUMPTIONS/INLET_ANGLE


# ======================================================================================
# Rules as functions. Each is the ONE definition of its rule (P2) and each is exercised by
# _self_test() on every run, so a rule cannot rot quietly between design runs.
# ======================================================================================

def classify_drop(d_invert_m: float) -> Tuple[float, str, int]:
    """The G203-p30 drop rule. THE single definition; stage 6 imports this, never re-writes it.

    Returns (DROP_M, DROP_TYPE, VORTEX) for an invert difference at a chamber.

      <= 0.60 m   the channel takes it - no structure
      >  0.60 m   an EXTERNAL backdrop, ramped not vertical (philosophy sec 5). External
                  matters: an internal backdrop forces the chamber to 1.5 m internal
                  diameter (G203-p30) and puts a falling jet in the working space.
      >  2.00 m   a vortex drop shaft. A DIFFERENT STRUCTURE with a different cost, not a
                  taller backdrop - which is why VORTEX is its own flag. The as-built has
                  37 drops over 2 m built as plain backdrops (P10): that is the calibration
                  reference being wrong, not a precedent.

    DROP_M is 0.0 where no structure is required, because the field means "backdrop height"
    and not "fall at the chamber" - the contract's cross-field check reads it that way.

    Never used to dodge a station (philosophy sec 5): a drop takes the difference on STEEP
    GROUND where the pipe holds its gradient, and it cannot buy back depth the cap-and-veto
    ladder has already spent.
    """
    d = float(d_invert_m)
    if not np.isfinite(d) or d <= C.DROP_TRIGGER + 1e-9:
        return 0.0, "none", 0
    if d <= C.BACKDROP_MAX + 1e-9:
        return d, "backdrop", 0
    return d, "vortex", 1


def inlet_angle_deg(vec_in: Tuple[float, float], vec_out: Tuple[float, float]) -> float:
    """The angle an arriving reach makes with the departing one, H10 / G203-p30.

    `vec_in` points INTO the chamber along the incoming flow; `vec_out` points AWAY along
    the outgoing flow. The convention is the one G203's ">= 90 degrees" is written in:

        180 deg   straight through - the flow is not turned at all
         90 deg   a square inlet - the flow turns through a right angle
          0 deg   a reversal - the flow is turned back on itself

    so it is `180 - (the deflection the flow is forced to make)`. Below 90 the incoming
    reach points partly back up the outgoing one, the channel cannot be benched to carry it,
    and the chamber has to be purpose-made with a swept channel.
    """
    ax, ay = vec_in
    bx, by = vec_out
    na = math.hypot(ax, ay)
    nb = math.hypot(bx, by)
    if na < 1e-9 or nb < 1e-9:
        return 180.0                       # degenerate: no direction, so no constraint
    cos = max(-1.0, min(1.0, (ax * bx + ay * by) / (na * nb)))
    return 180.0 - math.degrees(math.acos(cos))


def spacing_positions(span_m: float,
                      split: float = None,
                      step: float = None,
                      fallback: float = None,
                      min_clear: float = None) -> List[float]:
    """Interior chamber stations that keep every gap inside the Table 12 spacing.

    `split` defaults to `criteria.MH_SPLIT_LEN` = 100 m, which is the value that satisfies
    EVERY Table 12 class (G203-p30: 100 m to DN315, 120 to DN900, 150 to DN1400, 200 above).
    The diameter is stage 6's, so 100 m is the only safe choice here - and it is never wrong
    later, only conservative on a large pipe.

    Spacing is laid on ROUND steps of `MH_ROUND_STEP` (10 m, 5 m fallback; user rule
    2026-08-18) rather than by exact equal division, so the chainage on the drawing is a
    number a setting-out crew can hold. The step is rounded DOWN, never up - rounding up
    would push a gap past the Table 12 limit, which is the whole rule.

    The remainder falls at the DOWNSTREAM end of the span, and is never shorter than
    `MH_MIN_CLEAR_M` (3 m) - two chambers closer than that are one structure, and the
    contract's NodeIndex would merge them anyway.
    """
    split = C.MH_SPLIT_LEN if split is None else float(split)
    step = C.MH_ROUND_STEP if step is None else float(step)
    fallback = C.MH_ROUND_FALLBACK if fallback is None else float(fallback)
    min_clear = C.MH_MIN_CLEAR_M if min_clear is None else float(min_clear)

    span = float(span_m)
    if span <= split + 1e-9:
        return []
    n = int(math.ceil(span / split))
    exact = span / n
    s = math.floor(exact / step) * step                 # round DOWN to the 10 m step
    if s < min_clear:
        s = math.floor(exact / fallback) * fallback     # ... then the 5 m step
    if s < min_clear:
        s = exact                                       # ... then no rounding at all
    k = int(math.floor((span - min_clear) / s))
    out = [i * s for i in range(1, k + 1)]
    # Assert rather than trust: this is the rule W10 broke 4,763 times.
    gaps = np.diff([0.0] + out + [span])
    assert gaps.max() <= split + 1e-6, f"spacing_positions left a {gaps.max():.1f} m gap"
    assert gaps.min() >= min_clear - 1e-6, f"spacing_positions left a {gaps.min():.2f} m gap"
    return out


def deflection_stations(coords: Sequence[Tuple[float, float]],
                        min_deg: float = None) -> List[Tuple[float, float]]:
    """Vertices where the corridor turns by more than `criteria.ROAD_COLLINEAR_DEG` (10 deg).

    A pipe is straight between chambers, so any real change of direction needs one
    (G203-p29 sec 4.4). Ten degrees is the project's own dissolve threshold - a break
    straighter than that is survey wobble on a digitised centreline, not a corner.

    Returns (station along the line, deflection in degrees).
    """
    min_deg = C.ROAD_COLLINEAR_DEG if min_deg is None else float(min_deg)
    out: List[Tuple[float, float]] = []
    s = 0.0
    for i in range(1, len(coords) - 1):
        ax, ay = coords[i - 1]
        bx, by = coords[i]
        cx, cy = coords[i + 1]
        s += math.hypot(bx - ax, by - ay)
        u = (bx - ax, by - ay)
        v = (cx - bx, cy - by)
        nu, nv = math.hypot(*u), math.hypot(*v)
        if nu < 1e-9 or nv < 1e-9:
            continue
        cos = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (nu * nv)))
        defl = math.degrees(math.acos(cos))
        if defl > min_deg:
            out.append((s, defl))
    return out


def profile_break_stations(stations: np.ndarray, ground: np.ndarray,
                           tol: float = None) -> List[float]:
    """Ground-profile breaks: where the ground departs vertically from the straight profile
    between the chambers either side of it by more than `GRADE_BREAK_DEV_M`.

    Douglas-Peucker with a VERTICAL distance rather than a perpendicular one, because the
    thing being controlled is how far the pipe sits off the ground it is meant to parallel,
    and a perpendicular measure in a (chainage, level) plane mixes two units.

    This is the "change of grade" trigger of G203-p29 sec 4.4. The threshold is an
    ASSUMPTION - see PENDING_GRADE_BREAK. It changes chamber COUNT, never compliance.
    """
    tol = GRADE_BREAK_DEV_M if tol is None else float(tol)
    n = len(stations)
    if n < 3:
        return []
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        s0, s1 = stations[i], stations[j]
        z0, z1 = ground[i], ground[j]
        if s1 - s0 < 1e-9:
            continue
        chord = z0 + (z1 - z0) * (stations[i + 1:j] - s0) / (s1 - s0)
        dev = np.abs(ground[i + 1:j] - chord)
        if not len(dev) or not np.isfinite(dev).any():
            continue
        m = int(np.nanargmax(dev))
        if dev[m] > tol:
            k = i + 1 + m
            keep[k] = True
            stack.append((i, k))
            stack.append((k, j))
    return [float(stations[i]) for i in range(1, n - 1) if keep[i]]


def merge_close(stations: Sequence[float], priority: Dict[float, int],
                min_clear: float = None) -> List[float]:
    """Collapse chamber stations closer together than `MH_MIN_CLEAR_M` (3 m).

    Two chambers 0.4 m apart are one structure with a 0.4 m pipe between them - the contract's
    NodeIndex merges at the same 3 m radius, so leaving them in would silently produce a
    self-loop or a zero-length reach. Higher `priority` wins the survivor's position: a
    junction is not moved to suit a bend.
    """
    min_clear = C.MH_MIN_CLEAR_M if min_clear is None else float(min_clear)
    xs = sorted(set(float(s) for s in stations))
    if not xs:
        return []
    out = [xs[0]]
    for s in xs[1:]:
        if s - out[-1] < min_clear:
            if priority.get(s, 0) > priority.get(out[-1], 0):
                out[-1] = s                      # the junction keeps its place
        else:
            out.append(s)
    return out


# ======================================================================================
# Terrain and hazard. Rule 6: the 0.5 m VRT is the authoritative surface.
# ======================================================================================

class Surface:
    """Ground level and flood hazard, sampled once and in bulk.

    Two rasters, two different jobs:
      terrain  the 0.5 m bare-earth VRT (project rule 6). GRD_M on every chamber.
      hazard   Hazard_T50y, classes 4/5/6 = wadi. H1: "no pipe or chamber in a wadi." The
               corridors should already be clear of it after stage 2, so a hit here is an
               INPUT DEFECT and is reported as one rather than quietly designed around.
    """

    def __init__(self, terrain: str = P.TERRAIN, hazard: str = P.HAZARD):
        self.terrain_path = terrain
        self.hazard_path = hazard
        self._t = rasterio.open(terrain)
        if not os.path.exists(hazard):
            # H1 has no exit, so a missing hazard grid cannot be tolerated. With `_h = None`
            # both is_wadi() calls return all-False, the nudge and the breach register apply
            # to nothing, and the run prints a clean result with no count, no CSV and no
            # message - the wadi rule silently doing nothing, which is invariant 10 and the
            # same defect as W10's RoadTreatment running with units=None.
            raise ContractError(
                f"the flood hazard grid is missing: {hazard}. H1 forbids a pipe or a chamber "
                "in a wadi and has no exit, so chambers cannot be placed without it. Fix "
                "config_w10_reference.HAZARD rather than letting the rule apply to nothing.")
        self._h = rasterio.open(hazard)

    def ground(self, xs, ys) -> np.ndarray:
        if not len(xs):
            return np.array([], dtype=float)
        v = np.array([w[0] for w in self._t.sample(zip(xs, ys))], dtype=float)
        nod = self._t.nodata
        if nod is not None:
            v[v == nod] = np.nan
        v[v < -1000] = np.nan
        return v

    def is_wadi(self, xs, ys) -> np.ndarray:
        """audit.r4's own test, recomputed here so the design does not have to be told."""
        if self._h is None or not len(xs):
            return np.zeros(len(xs), dtype=bool)
        v = np.array([w[0] for w in self._h.sample(zip(xs, ys))], dtype=float)
        return np.isfinite(v) & (np.floor(v) >= min(C.HAZARD_WADI_CLASSES))

    def close(self):
        self._t.close()
        if self._h is not None:
            self._h.close()


# ======================================================================================
# The input from stage 4
# ======================================================================================

WAITING = f"""
================================================================================
STAGE 5 (CHAMBERS) IS WAITING ON STAGE 4 (HIERARCHY). Nothing was written.
================================================================================
A chamber is placed ON a route, and a route is a tiered, DIRECTED collector run.
Stage 5 does not invent one: the philosophy fixes the order (sec 2), and deciding a
hierarchy inside the chamber stage is exactly how W10's tiers ended up existing only
in memory.

WHAT IS MISSING - either of these two handovers is enough

  1. THE ONE STAGE 4 ACTUALLY PUBLISHES (preferred)
     file    {S4_GPKG}
     layers  "{S4_REACHES}"  directed tiered edges: EDGE_UID, US_NODE, DS_NODE, TIER
             "{S4_NODES}"    the node positions those ids resolve against
     Stage 5 decomposes that forest into maximal unbranched RUNS of one tier, and
     places chambers along each. The junctions come from the graph itself.

  2. A ROUTE LAYER, if stage 4 ever publishes runs directly
     file    {GPKG}
     layer   "{ROUTES_LAYER}"   (contract.CORRIDORS)
     extra   TIER      one of {list(K.TIERS)}, spelled the AUDITOR's way - audit.h9 does
                       floor.get(tier) and skips an unrecognised tier SILENTLY, so
                       "sub_main" reads as a PASS
             DS_CORR   the CORR_ID this run discharges into; BLANK at an outfall
     geometry ONE LineString per row, DRAWN IN THE DIRECTION OF FLOW.

Expected shape, from philosophy sec 4, so stage 4 knows when it is done:
  lateral 66 %, sub main 18 %, trunk 5 % of length; of the order of 270 km of sub main.

TO EXERCISE THIS STAGE WITHOUT STAGE 4
  python s5_chambers.py --rehearse
    Runs the identical placement engine over REAL drafted corridor geometry
    (W10/shp/W10_corridors_drafted.shp) with a stand-in direction and tiering, validates
    the result against the contract, and writes to W11a/run/ ONLY. It never touches
    W11a/shp/, so a rehearsal cannot be mistaken for a design.
================================================================================
"""


@dataclass
class Routes:
    """Directed, tiered routes - the stage 4 handover, normalised."""
    gdf: gpd.GeoDataFrame
    rehearsal: bool = False
    source: str = ""

    @property
    def n(self) -> int:
        return len(self.gdf)


def load_routes(rec) -> Optional[Routes]:
    """Stage 4's output as ROUTES, or None so the caller can exit 0 with a reason.

    Two handovers are accepted, in this order. The first is what stage 4 publishes today.
    """
    r = _load_from_s4(rec)
    if r is not None:
        return r
    return _load_from_corridors(rec)


def _load_from_s4(rec) -> Optional[Routes]:
    """Stage 4 publishes a DIRECTED TIERED GRAPH, not runs, so stage 5 makes the runs.

    Its edges are corridor segments - 24,051 of them, median 36 m, LONGEST 6,541 m. That
    longest edge is precisely the W10 defect, a "reach" with no chamber anywhere on it, so
    those edges cannot be reaches and turning them into some is this stage's whole job.

    A RUN is a maximal unbranched chain of one tier and one system. It breaks wherever a
    second reach arrives (a junction is a chamber, G203-p29 sec 4.4), wherever the tier
    changes (which is where the diameter changes, and a diameter may only change at a
    chamber), and wherever the servicing system changes - philosophy sec 8a: a satellite is
    a different network, not a branch of this one. Everything else about a run is geometry,
    and geometry is what the placement rules read.

    Chamber identity is RE-MINTED here rather than inherited from `s4_nodes`, deliberately:
    19,594 corridor vertices are not 19,594 chambers, and carrying the corridor ids onto
    the chamber layer would give NODE_UID two meanings - "a place where two drafted lines
    met" on some rows and "a manhole" on others.
    """
    if not os.path.exists(S4_GPKG):
        return None
    import fiona
    layers = fiona.listlayers(S4_GPKG)
    if S4_REACHES not in layers:
        return None
    e = gpd.read_file(S4_GPKG, layer=S4_REACHES)
    need = ["EDGE_UID", "US_NODE", "DS_NODE", "TIER"]
    missing = [c for c in need if c not in e.columns]
    if missing:
        raise ContractError(
            f"'{S4_REACHES}' has no {missing}. Stage 5 reads the hierarchy from the graph; "
            "without US_NODE/DS_NODE connectivity can only be guessed by a tolerance, "
            "which is how W10 published 7,919 pieces.")
    bad = e.geom_type != "LineString"
    if bad.any():
        raise ContractError(f"{int(bad.sum()):,} stage-4 edges are multipart. Explode them "
                            "in stage 4: audit.Ctx.graph() reads geoms[0] and drops the "
                            "rest, so H15 would report on a network it only half read.")
    rec.read(S4_REACHES, S4_GPKG, len(e))

    pos: Dict[str, Tuple[float, float]] = {}
    if S4_NODES in layers:
        nd = gpd.read_file(S4_GPKG, layer=S4_NODES)
        pos = {r.NODE_UID: (r.geometry.x, r.geometry.y) for r in nd.itertuples()}
        rec.read(S4_NODES, S4_GPKG, len(nd))

    e = e.copy()
    e["TIER"] = (e["TIER"].astype(str).str.strip().str.lower()
                 .map(lambda t: K.TIER_ALIASES.get(t, t)))
    if "SYSTEM" not in e.columns:
        e["SYSTEM"] = "central"
    for col, dflt in (("SRC", "draft"), ("CONFIDENCE", "drafted")):
        if col not in e.columns:
            e[col] = dflt

    dup_out = len(e) - e["US_NODE"].nunique()
    if dup_out:
        raise ContractError(
            f"{dup_out:,} stage-4 chambers carry more than one outgoing edge. H15 makes "
            "the network a FOREST - one pipe leaves a structure - and a second outlet is a "
            "layout error, not something stage 5 can chamber its way out of.")

    us = e["US_NODE"].to_numpy()
    ds = e["DS_NODE"].to_numpy()
    uid = e["EDGE_UID"].to_numpy()
    tier = e["TIER"].to_numpy()
    system = e["SYSTEM"].to_numpy()
    geom = e.geometry.to_numpy()
    src = e["SRC"].astype(str).to_numpy()
    conf = e["CONFIDENCE"].astype(str).to_numpy()

    out_edge: Dict[str, int] = {u: i for i, u in enumerate(us)}
    in_edges: Dict[str, List[int]] = {}
    for i, v in enumerate(ds):
        in_edges.setdefault(v, []).append(i)

    def _same(i: int, j: int) -> bool:
        return tier[i] == tier[j] and system[i] == system[j]

    # An edge STARTS a run when the chamber above it is a junction, a head, or a tier or
    # system change - i.e. exactly the places G203 and the philosophy already require a
    # chamber for another reason.
    starts = [i for i in range(len(uid))
              if len(in_edges.get(us[i], ())) != 1 or not _same(in_edges[us[i]][0], i)]

    runs: List[List[int]] = []
    seen = set()
    for s0 in starts:
        chain, cur = [], s0
        while cur is not None and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            v = ds[cur]
            nxt = out_edge.get(v)
            if nxt is None or len(in_edges.get(v, ())) != 1 or not _same(cur, nxt):
                break
            cur = nxt
        if chain:
            runs.append(chain)
    orphan = [i for i in range(len(uid)) if i not in seen]
    if orphan:                                       # only reachable from a cycle
        raise ContractError(
            f"{len(orphan):,} stage-4 edges belong to no run. An edge with no run-start "
            "above it can only sit on a cycle, and H15 forbids one.")

    run_of = {i: r for r, ch in enumerate(runs) for i in ch}
    out: List[Dict] = []
    for r, ch in enumerate(runs):
        coords: List[Tuple[float, float]] = []
        for i in ch:
            c = list(geom[i].coords)
            # Orient on the NODE positions, never on the assumption that stage 4 digitised
            # every edge downstream. One reversed edge folds a run back on itself, and the
            # fold survives as a real, buildable-looking pipe nobody would spot on a plan.
            a = pos.get(us[i])
            if a is not None and ((c[0][0] - a[0]) ** 2 + (c[0][1] - a[1]) ** 2 >
                                  (c[-1][0] - a[0]) ** 2 + (c[-1][1] - a[1]) ** 2):
                c = c[::-1]
            coords.extend(c if not coords else c[1:])
        if len(coords) < 2:
            continue
        nxt = out_edge.get(ds[ch[-1]])
        out.append(dict(
            CORR_ID=f"RUN-{r:06d}",
            DS_CORR="" if nxt is None else f"RUN-{run_of[nxt]:06d}",
            TIER=str(tier[ch[0]]), SYSTEM=str(system[ch[0]]),
            SRC=str(src[ch[0]]), CONFIDENCE=str(conf[ch[0]]),
            geometry=LineString(coords)))
    gdf = gpd.GeoDataFrame(out, geometry="geometry", crs=K.CRS_EPSG)
    gdf["LEN_M"] = gdf.geometry.length
    return Routes(gdf=_normalise(gdf), source=f"{S4_GPKG}::{S4_REACHES} -> runs")


def _load_from_corridors(rec) -> Optional[Routes]:
    """The alternative handover: a route layer that already carries TIER and DS_CORR."""
    if not os.path.exists(GPKG):
        return None
    import fiona
    if ROUTES_LAYER not in fiona.listlayers(GPKG):
        return None
    g = gpd.read_file(GPKG, layer=ROUTES_LAYER)
    missing = [c for c in ROUTES_NEEDS if c not in g.columns]
    if missing:
        # NOT an error. Stage 2 publishes `corridors` with no tier on it, which is correct -
        # the hierarchy is stage 4's decision. Say what is missing and let the caller wait.
        print(f"[{STAGE}] '{ROUTES_LAYER}' in {os.path.basename(GPKG)} exists but carries "
              f"no {missing}: that is stage 2's corridor layer, not a tiered route layer.")
        return None
    K.validate(g, "corridors", stage=STAGE)
    rec.read(ROUTES_LAYER, GPKG, len(g))
    return Routes(gdf=_normalise(g), source=f"{GPKG}::{ROUTES_LAYER}")


def _normalise(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Explode nothing, refuse multipart, normalise the tier spelling, index by CORR_ID."""
    g = g.copy()
    bad = g.geometry.geom_type != "LineString"
    if bad.any():
        raise ContractError(
            f"{int(bad.sum()):,} routes are not a single LineString. A multipart route is "
            "two routes; explode it in stage 4 and account for the parts in a Funnel, "
            "because audit.Ctx.graph() reads geoms[0] and drops the rest.")
    g["TIER"] = (g["TIER"].astype(str).str.strip().str.lower()
                 .map(lambda t: K.TIER_ALIASES.get(t, t)))
    g["DS_CORR"] = g["DS_CORR"].fillna("").astype(str).str.strip()
    g["CORR_ID"] = g["CORR_ID"].astype(str)
    if "SRC" not in g.columns:
        g["SRC"] = "draft"
    if "CONFIDENCE" not in g.columns:
        g["CONFIDENCE"] = "drafted"
    return g.set_index("CORR_ID", drop=False)


# ======================================================================================
# The engine
# ======================================================================================

@dataclass
class Placement:
    """One route's chamber stations, before they become nodes."""
    corr_id: str
    stations: List[float] = field(default_factory=list)
    why: Dict[float, str] = field(default_factory=dict)


class ChamberPlacer:
    """Routes in, a `contract.Network` of chambers and reaches out.

    The order of operations is the design, so it is written out rather than left implicit:

      1. junctions      every route's outlet is projected onto its downstream route. That
                        station is a FORCED chamber on the receiving route, and the two
                        share ONE node - snapped to the same coordinate, not merely close.
      2. gates          a head route is trimmed to the first fronting plot (philosophy sec 4).
      3. direction      vertices deflecting past 10 deg, plus chord-deviation splits so the
                        straight published reach never strays 0.50 m off the corridor.
      4. grade          ground-profile breaks past GRADE_BREAK_DEV_M (tagged assumption).
      5. clearance      nothing within 10 m upstream of a junction; nothing within 3 m of
                        anything else.
      6. spacing        Table 12 fill at 100 m, on round 10 m steps.
      7. wadi           any chamber on hazard class 4/5/6 is nudged along the route; what
                        cannot be moved is REPORTED, because it is a stage-2 corridor defect.
      8. graph          nodes minted once by NodeIndex, edges by Network.add_edge, which is
                        where one-outlet-per-structure and the forest stop being checks.
    """

    def __init__(self, routes: Routes, surface: Surface, rec, plots: Optional[gpd.GeoDataFrame]):
        self.routes = routes
        self.surf = surface
        self.rec = rec
        self.plots = plots
        self.net = K.Network()
        self.placements: Dict[str, Placement] = {}
        self.junctions: Dict[str, List[Tuple[float, str]]] = {}      # corr -> [(station, from)]
        self.gate_station: Dict[str, float] = {}
        self.notes: Dict[str, int] = dict(
            heads_at_gate=0, heads_no_plot=0, branches_absorbed=0,
            wadi_moved=0, wadi_stuck=0, terrain_gaps=0, outlet_conflicts=0,
            routes_too_short=0, junction_gaps=0, runs_no_reach=0)
        # H1 is a HARD constraint with no exit. A chamber left on wadi ground is a breach,
        # and a breach that is only counted is the W10 disease - so every one is named.
        self.wadi_stuck_rows: List[Dict] = []
        self.junction_gap_rows: List[Dict] = []

    # ---------------------------------------------------------------- 1. junctions
    def build_junctions(self) -> None:
        g = self.routes.gdf
        for cid, row in g.iterrows():
            ds = row["DS_CORR"]
            if not ds:
                continue
            if ds not in g.index:
                raise ContractError(
                    f"route {cid} names DS_CORR={ds!r}, which is not a route. A dangling "
                    "downstream reference is a reach with nowhere to go - stage 4 must "
                    "resolve it or mark the route an outfall.")
            pt = Point(row.geometry.coords[-1])
            parent = g.loc[ds, "geometry"]
            s = float(parent.project(pt))
            # The junction chamber is placed on the PARENT's geometry, and the child's last
            # chamber is snapped to it. If the two are further apart than the node merge
            # radius, the child does not actually reach the route it claims to discharge
            # into, and snapping would drag its last reach across open ground. That is a
            # stage-4 defect - W10's auto_link had EVERY endpoint 1.0 m short of what it
            # joined, and the layer shipped in 7,919 pieces because nothing measured it.
            gap = float(parent.interpolate(s).distance(pt))
            if gap > K.NODE_MERGE_M:
                self.notes["junction_gaps"] += 1
                self.junction_gap_rows.append(dict(
                    CORR_ID=cid, DS_CORR=ds, GAP_M=round(gap, 3),
                    X=round(pt.x, 3), Y=round(pt.y, 3),
                    NOTE=("the route's downstream end is more than the "
                          f"{K.NODE_MERGE_M} m node merge radius from the route it names "
                          "as DS_CORR. Stage 4 must node them, or the DS_CORR is wrong.")))
            self.junctions.setdefault(ds, []).append((s, cid))

    # ---------------------------------------------------------------- 2. the gate
    def build_gates(self) -> None:
        """Philosophy sec 4: a head starts at the gate - the foot of the perpendicular from
        the first fronting plot's centroid, within `criteria.GATE_SEARCH_M` (45 m).

        Only LOAD-BEARING plots count. A run that starts at a plot generating nothing is a
        run collecting nothing, and W10 laid 117.3 km of pipe with no load-bearing plot
        within 60 m (P7). Where no plot fronts the route at all the head stays at the route
        start and the route is COUNTED as a finger for stage 2/4 to prune - it is not
        deleted here, because scope is decided before the design and not inside it.
        """
        g = self.routes.gdf
        heads = self._head_routes()
        if self.plots is None or not len(self.plots) or not heads:
            self.notes["heads_no_plot"] = len(heads)
            return
        cent = self.plots
        # reset_index: the routes frame carries CORR_ID as BOTH index and column, and
        # sjoin_nearest then refuses to insert the index ("cannot insert CORR_ID, already
        # exists"). This was wrapped in a try/except once and every gate silently fell back
        # to the route start - a stage quietly doing nothing, which is invariant 10 exactly.
        # It is not caught any more: a failure here has to stop the run.
        sub = g.loc[list(heads), ["CORR_ID", "geometry"]].reset_index(drop=True)
        join = gpd.sjoin_nearest(cent, sub, max_distance=C.GATE_SEARCH_M, how="inner",
                                 distance_col="_d")
        if not len(join):
            self.notes["heads_no_plot"] = len(heads)
            return
        for cid, part in join.groupby("CORR_ID"):
            line = g.loc[cid, "geometry"]
            s = min(float(line.project(p)) for p in part.geometry)
            self.gate_station[cid] = s
        self.notes["heads_at_gate"] = len(self.gate_station)
        self.notes["heads_no_plot"] = len(heads) - len(self.gate_station)

    def _head_routes(self) -> List[str]:
        """A route whose UPSTREAM end nothing discharges into is the head of a run."""
        out = []
        for cid, row in self.routes.gdf.iterrows():
            js = self.junctions.get(cid, [])
            if not any(s <= C.MH_MIN_CLEAR_M for s, _ in js):
                out.append(cid)
        return out

    # ------------------------------------------------- 3-6. every station on every route
    def place(self) -> None:
        g = self.routes.gdf
        fn = self.rec.funnel("routes -> routes with chambers", len(g))
        short, absorbed = [], []
        for cid, row in g.iterrows():
            line = row.geometry
            L = float(line.length)
            if L < C.MH_MIN_CLEAR_M:
                short.append(cid)
                continue

            js = [s for s, _ in self.junctions.get(cid, [])]
            gate = self.gate_station.get(cid, 0.0)
            gate = min(max(gate, 0.0), max(L - C.FANOUT_OFFSET_M, 0.0))

            # A branch whose whole usable length is under the 10 m clearance has no room for
            # its own head chamber. Its load joins at the junction; the branch is ABSORBED
            # and counted, never dropped silently (invariant 1).
            if (L - gate) < C.FANOUT_OFFSET_M and not js:
                absorbed.append(cid)
                continue

            why: Dict[float, str] = {}
            forced = {0.0: "start", L: "outlet"}
            if gate > C.MH_MIN_CLEAR_M:
                forced.pop(0.0, None)
                forced[gate] = "head_at_gate"
            for s in js:
                if gate - 1e-6 <= s <= L + 1e-6:
                    forced[min(max(s, gate), L)] = "junction"

            coords = list(line.coords)
            for s, _deg in deflection_stations(coords):
                if gate + C.MH_MIN_CLEAR_M < s < L - C.MH_MIN_CLEAR_M:
                    forced.setdefault(s, "direction")
            for s in self._chord_breaks(line):
                if gate + C.MH_MIN_CLEAR_M < s < L - C.MH_MIN_CLEAR_M:
                    forced.setdefault(s, "chord")
            for s in self._grade_breaks(line, gate, L):
                if gate + C.MH_MIN_CLEAR_M < s < L - C.MH_MIN_CLEAR_M:
                    forced.setdefault(s, "grade")

            # 10 m branch clearance: nothing but the junction itself sits in the last 10 m.
            forced = {s: w for s, w in forced.items()
                      if w in ("outlet", "junction") or s <= L - C.FANOUT_OFFSET_M + 1e-6}

            prio = {s: {"junction": 4, "outlet": 4, "head_at_gate": 3, "start": 3,
                        "direction": 2, "chord": 2, "grade": 1}[w]
                    for s, w in forced.items()}
            kept = merge_close(list(forced), prio)
            why = {s: forced.get(s, "chamber") for s in kept}
            # Wadi avoidance FIRST, on the forced positions only, so the Table 12 fill that
            # follows is the last thing to touch the stations and its spacing is final.
            kept = self._nudge_off_wadi(line, kept, why)

            # Table 12 fill between every consecutive pair.
            full: List[float] = []
            for a, b in zip(kept[:-1], kept[1:]):
                full.append(a)
                for t in spacing_positions(b - a, split=SPACING_TARGET_M):
                    full.append(a + t)
                    why[a + t] = "spacing"
            full.append(kept[-1])
            full = sorted(set(full))

            gaps = np.diff(full) if len(full) > 1 else np.array([0.0])
            assert gaps.max() <= C.MH_SPLIT_LEN + 1e-6, (
                f"route {cid} left a {gaps.max():.2f} m gap - H12 is a 'shall'")

            self._report_wadi(line, full, why, cid)
            self.placements[cid] = Placement(cid, full, why)

        if short:
            fn.drop(f"route shorter than the {C.MH_MIN_CLEAR_M} m minimum chamber "
                    "clearance - it is a clip artefact, not a sewer", ids=short)
            self.notes["routes_too_short"] = len(short)
        if absorbed:
            fn.drop(f"branch shorter than the {C.FANOUT_OFFSET_M} m clearance between a "
                    "branch start and its junction - absorbed into the junction chamber",
                    ids=absorbed)
            self.notes["branches_absorbed"] = len(absorbed)
        fn.close(len(self.placements))

    def _chord_breaks(self, line: LineString) -> List[float]:
        """Where a straight pipe between chambers would leave the corridor.

        `criteria.ROAD_CHORD_DEV_M` = 0.50 m, declared in the criteria and never enforced
        ("chord-deviation splitting is a W5 item"). It is enforced here, and it is what
        earns the right to publish a reach as a straight two-point line (P2, "straight
        between chambers") while it still sits on the road.
        """
        simp = line.simplify(C.ROAD_CHORD_DEV_M, preserve_topology=False)
        return [float(line.project(Point(c))) for c in list(simp.coords)[1:-1]]

    def _grade_breaks(self, line: LineString, s0: float, s1: float) -> List[float]:
        """Ground-profile breaks. G203-p29 sec 4.4 + the PENDING_GRADE_BREAK assumption."""
        if s1 - s0 < 2 * GRADE_SAMPLE_M:
            return []
        st = np.arange(s0, s1 + 1e-9, GRADE_SAMPLE_M)
        pts = [line.interpolate(float(s)) for s in st]
        z = self.surf.ground([p.x for p in pts], [p.y for p in pts])
        ok = np.isfinite(z)
        if ok.sum() < 3:
            return []
        return profile_break_stations(st[ok], z[ok])

    def _nudge_off_wadi(self, line: LineString, stations: List[float],
                        why: Dict[float, str]) -> List[float]:
        """H1: no pipe OR CHAMBER in a wadi. Move what can legitimately be moved.

        Applied to the FORCED positions only, and BEFORE the Table 12 fill. Two reasons,
        the second learned from a 100.2 m reach on the first large run:

          a bend or grade chamber is a point the design chose, so sliding it a few metres
          to firm ground is a real fix; a SPACING chamber is not - if a 94 m span crosses a
          wadi then the PIPE crosses the wadi, and moving one chamber 5 m along it fixes
          nothing. That is a corridor problem and it belongs to stage 2.

          nudging after the fill silently widens a gap by up to the nudge distance, which
          is how a reach came out 0.2 m over the Table 12 limit while every rule in this
          module claimed to have been applied.

        A junction, an outlet and a gate are never moved: each is a point where the network
        physically meets something else.
        """
        if self.surf._h is None or not stations:
            return stations
        pts = [line.interpolate(float(s)) for s in stations]
        hit = self.surf.is_wadi([p.x for p in pts], [p.y for p in pts])
        if not hit.any():
            return stations
        L = float(line.length)
        out = list(stations)
        for i in np.flatnonzero(hit):
            s = stations[i]
            if why.get(s) in ("junction", "outlet", "head_at_gate", "start"):
                continue
            for d in (5.0, -5.0, 10.0, -10.0, 15.0, -15.0, 20.0, -20.0):
                t = s + d
                if not (0.0 <= t <= L):
                    continue
                p = line.interpolate(t)
                if not self.surf.is_wadi([p.x], [p.y])[0]:
                    out[i] = t
                    why[t] = why.get(s, "chamber")
                    self.notes["wadi_moved"] += 1
                    break
        return sorted(set(out))

    def _report_wadi(self, line: LineString, stations: List[float],
                     why: Dict[float, str], corr_id: str) -> None:
        """Name every chamber still standing on wadi ground. H1 has no exit, so a count on
        its own is the W10 disease: the fix is a re-routed corridor or a different system
        for the plots behind it, and neither can be actioned from a number."""
        if self.surf._h is None or not stations:
            return
        pts = [line.interpolate(float(s)) for s in stations]
        hit = self.surf.is_wadi([p.x for p in pts], [p.y for p in pts])
        for i in np.flatnonzero(hit):
            s = stations[i]
            trig = why.get(s, "chamber")
            self.notes["wadi_stuck"] += 1
            self.wadi_stuck_rows.append(dict(
                CORR_ID=corr_id, STATION_M=round(float(s), 2),
                X=round(pts[i].x, 3), Y=round(pts[i].y, 3), TRIGGER=trig,
                WHY_STUCK=("a junction, an outlet or a gate cannot be moved - it is where "
                           "the network physically meets something else"
                           if trig in ("junction", "outlet", "head_at_gate", "start") else
                           "a Table 12 spacing chamber inside a span that crosses the wadi; "
                           "moving it along the same pipe changes nothing"
                           if trig == "spacing" else
                           "wadi ground for at least 20 m either way along the route"),
                REMEDY=("H1 has no exit: re-route the corridor (stage 2), or the plots it "
                        "serves are served by another system (philosophy sec 8a)")))

    # ---------------------------------------------------------------- 8. the graph
    def build_graph(self) -> None:
        """Mint the nodes and add the reaches, downstream route first.

        Downstream-first matters: a route's outlet node must already exist on its receiving
        route so the two SHARE it, rather than two chambers appearing 0.4 m apart with a
        0.4 m pipe between them. The child's outlet coordinate is snapped to the parent's
        junction coordinate EXACTLY - not left to a tolerance, which is what produced W10's
        7,919 pieces.
        """
        g = self.routes.gdf
        order = self._downstream_first()
        junction_xy: Dict[Tuple[str, float], Tuple[float, float]] = {}

        # First pass: fix the exact coordinate of every junction, from the PARENT's geometry.
        for parent, js in self.junctions.items():
            if parent not in g.index:
                continue
            line = g.loc[parent, "geometry"]
            for s, child in js:
                p = line.interpolate(min(max(s, 0.0), float(line.length)))
                junction_xy[(child, "outlet")] = (p.x, p.y)

        for cid in order:
            pl = self.placements.get(cid)
            if pl is None:
                continue                  # short or absorbed - already named in a Funnel
            if len(pl.stations) < 2:
                # One station is not a reach, so this run contributes NOTHING - no chamber,
                # no pipe - and anything that named it as DS_CORR now discharges to a node
                # with no outlet. It happens when the 10 m branch-clearance filter strips a
                # run's own start station, which it can only do on a run under 10 m long
                # that receives a junction (172 such runs exist; none currently collapse).
                # Zero today, but a bare `continue` here is a stage silently doing nothing.
                self.notes["runs_no_reach"] += 1
                continue
            row = g.loc[cid]
            line = row.geometry
            tier = row["TIER"]
            src = str(row.get("SRC", "draft"))
            conf = str(row.get("CONFIDENCE", "drafted"))
            # SYSTEM travels onto the chamber so `Network.check()` can say WHICH
            # networks the components are, rather than only how many. Philosophy sec 8a
            # contemplates a central network plus satellites plus on-site systems, and
            # audit.h15 demands exactly one component - OPEN-1. A component count with
            # no systems beside it cannot tell a compliant multi-system design from
            # W10's 7,919 pieces.
            system = str(row.get("SYSTEM", "central"))
            # P6, enforced rather than trusted: a cadastral reserve on bare desert can never
            # be graded better than provisional, whatever stage 4 wrote.
            ceil_ = K.SRC_CONFIDENCE_CEILING.get(src)
            if ceil_ and K._CONF_RANK.get(conf, 99) < K._CONF_RANK[ceil_]:
                conf = ceil_

            xy: List[Tuple[float, float]] = []
            for i, s in enumerate(pl.stations):
                if i == len(pl.stations) - 1 and (cid, "outlet") in junction_xy:
                    xy.append(junction_xy[(cid, "outlet")])
                else:
                    p = line.interpolate(float(s))
                    xy.append((p.x, p.y))

            # Nodes are minted LAZILY, one pair at a time. Minting the whole chain first and
            # then discovering a conflict halfway leaves the rest of the chain as chambers
            # with no reach attached - orphans on the published layer, which is the W10
            # disease in miniature.
            prev = None
            for x, y in xy:
                if prev is not None and prev in self.net.out_edge:
                    # This chamber already drains. Two runs meeting at one chamber is
                    # correct sewerage - only one pipe leaves - so the chain ENDS here and
                    # its flow continues through the existing reach. Counted, because a
                    # frequent count means stage 4 handed over routes that cross without a
                    # declared junction.
                    self.notes["outlet_conflicts"] += 1
                    break
                uid = self.net.node(x, y, tier=tier, src=src, confidence=conf,
                                    system=system, stage=STAGE)
                if prev is None:
                    prev = uid
                    continue
                if uid == prev:
                    continue                       # merged by NodeIndex: one structure
                self.net.add_edge(prev, uid, tier=tier, src=src, confidence=conf,
                                  stage=STAGE)
                prev = uid

    def _downstream_first(self) -> List[str]:
        """Order the routes so a receiving route is built before the routes that join it.

        Iterative, not recursive: the DS_CORR chain on a real network is thousands deep and
        a recursive walk would die on the stack rather than on a design error. A chain that
        revisits a route is a loop, which H15 forbids, and it is raised here rather than
        discovered as a cycle in the published layer.
        """
        g = self.routes.gdf
        ds_of = dict(zip(g.index, g["DS_CORR"]))
        depth: Dict[str, int] = {}
        for start in g.index:
            if start in depth:
                continue
            chain, seen, cur = [], set(), start
            while cur is not None and cur not in depth:
                if cur in seen:
                    raise ContractError(
                        f"the DS_CORR chain through {cur} revisits itself - stage 4 "
                        "published a loop, and H15 makes the network a forest")
                seen.add(cur)
                chain.append(cur)
                nxt = ds_of.get(cur, "")
                cur = nxt if nxt and nxt in ds_of else None
            base = depth.get(cur, -1) if cur is not None else -1
            for i, c in enumerate(reversed(chain)):
                depth[c] = base + 1 + i
        return sorted(g.index, key=lambda c: depth[c])


# ======================================================================================
# Deriving what the node layer publishes
# ======================================================================================

def assign_kinds_and_tiers(net: K.Network) -> None:
    """NODE_KIND and TIER from the finished graph, by degree alone.

    Deterministic and re-derivable by anyone reading the layer, which is the test a
    published field has to pass. Kind is what the drawing symbol and the schedule read
    (G203-p29 sec 4.4 lists the triggers a chamber may exist for); TIER is defined by the
    contract as the tier of the OUTGOING reach, so it is taken from that reach and not from
    whichever route happened to mint the node first.

    Called BEFORE `Network.check()`, because check() refuses a terminal node that is not an
    outfall, a station or a tie - and until the kinds are set, every terminal is a
    "chamber".
    """
    for uid, nd in net.nodes.items():
        n_in = len(net.in_edges.get(uid, ()))
        out_e = net.out_edge.get(uid)
        if out_e is None:
            nd.kind = "outfall"          # the only terminal this stage can produce; a
                                         # station or a tie is stages 6-7
            ins = net.in_edges.get(uid, ())
            if ins:
                nd.tier = net.edges[ins[0]].tier
        else:
            nd.kind = "head" if n_in == 0 else ("junction" if n_in >= 2 else "chamber")
            nd.tier = net.edges[out_e].tier


def finish_nodes(net: K.Network, surf: Surface, rec) -> Tuple[gpd.GeoDataFrame,
                                                              gpd.GeoDataFrame,
                                                              pd.DataFrame]:
    """Ground, seeded levels, inlet angles, drop placeholders - then the two frames.

    Everything here is computed from the FINISHED graph, never from the routes, so the node
    layer and the reach layer are two views of one object. That is the whole point of P3:
    in W10 the node layer and the pipe layer came out of different solves and disagreed by
    up to 10.39 m of depth, and neither layer alone could reveal it.
    """
    nodes = net.nodes

    # ---- 2. ground level, in one bulk sample (rule 6: the 0.5 m VRT is authoritative).
    uids = list(nodes)
    xs = np.array([nodes[u].x for u in uids])
    ys = np.array([nodes[u].y for u in uids])
    z = surf.ground(xs, ys)
    gaps = int(np.isnan(z).sum())
    if gaps:
        # A chamber outside the terrain has no cover, no depth and no drop. Fill from the
        # nearest sampled neighbour rather than dropping the chamber, which would break the
        # chain; count it, because a silent fill is an invented level.
        good = np.flatnonzero(np.isfinite(z))
        if len(good):
            from scipy.spatial import cKDTree
            tree = cKDTree(np.c_[xs[good], ys[good]])
            bad = np.flatnonzero(np.isnan(z))
            _, j = tree.query(np.c_[xs[bad], ys[bad]], k=1)
            z[bad] = z[good][j]
        else:
            raise ContractError("no chamber has a ground level - the terrain VRT does not "
                                "cover this area. Every depth in the design would be "
                                "invented (rule 6).")

    # ---- 3. the seeded levels. Philosophy sec 5: lay as shallow as H3 allows.
    #        `contract.min_invert_depth()` and NOT `criteria.invert_depth_min()`, which is
    #        50 mm shallow against audit.h3 at every diameter and fails a BLOCKING check on
    #        every reach.
    for u, zz in zip(uids, z):
        nd = nodes[u]
        dn0 = C.DN_TERTIARY if nd.tier == "rider" else C.DN_MIN_MAIN   # audit.h9 floors
        depth = K.min_invert_depth(dn0)
        nd.grd_m = float(zz)
        nd.inv_m = float(zz) - depth
        nd.attrs["COVER_M"] = round(K.cover(dn0, depth), 4)            # exactly 1.30
        nd.attrs["MH_DIA"] = 1.0 if depth <= 3.0 else (1.2 if depth <= 6.0 else 1.5)
        nd.attrs["MH_MAT"] = ""
        # Owned by stage 6. Zero is not a measurement; STAGE says which stage wrote the row.
        nd.attrs["DROP_M"] = 0.0
        nd.attrs["DROP_TYPE"] = "none"
        nd.attrs["VORTEX"] = 0
        nd.attrs["Q_ADF_M3D"] = 0.0
        nd.attrs["Q_PK_LS"] = 0.0
        nd.attrs["N_PROP"] = 0.0
        nd.attrs["PAST_CAP"] = 0
        nd.attrs["CAP_EXIT"] = ""

    # ---- 4. inlet angles, on the finished graph (H10, G203-p30).
    sharp_rows = []
    for uid, nd in nodes.items():
        out_e = net.out_edge.get(uid)
        ins = net.in_edges.get(uid, ())
        if out_e is None or not ins:
            nd.attrs["INLET_DEG"] = 180.0      # no inlet, or no outlet: nothing is turned
            nd.attrs["INLET_FLAG"] = 0
            continue
        og = net.edge_geom(out_e)
        oc = list(og.coords)
        v_out = (oc[1][0] - oc[0][0], oc[1][1] - oc[0][1])
        worst, worst_e = 360.0, ""
        for e in ins:
            ig = net.edge_geom(e)
            ic = list(ig.coords)
            v_in = (ic[-1][0] - ic[-2][0], ic[-1][1] - ic[-2][1])
            a = inlet_angle_deg(v_in, v_out)
            if a < worst:
                worst, worst_e = a, e
        # Rounded DOWN, and the flag taken from the ROUNDED value. Two reasons, both
        # learned the hard way in this run: an angle rounded to nearest publishes 90.00 for
        # a real 89.996, which is a passing number for a failing chamber; and audit.h10
        # recomputes from the PUBLISHED INLET_DEG, so a flag set from the unrounded value
        # disagrees with the column beside it and the layer contradicts itself.
        deg = math.floor(worst * 100.0) / 100.0
        nd.attrs["INLET_DEG"] = deg
        nd.attrs["INLET_FLAG"] = int(deg < INLET_GUIDELINE_DEG)
        if nd.attrs["INLET_FLAG"]:
            sharp_rows.append(dict(
                NODE_UID=uid, NODE_REF=K.node_ref(nd, uid), X=round(nd.x, 3),
                Y=round(nd.y, 3), TIER=nd.tier, NODE_KIND=nd.kind,
                INLET_DEG=deg, INLET_EDGE=worst_e, OUT_EDGE=out_e,
                N_IN=len(ins),
                BAND=("below 90 deg - G203-p30" if deg >= INLET_PROJECT_DEG else
                      ("below the project's stated 85 deg deviation" if deg >= INLET_REVIEW_DEG
                       else "below 75 deg - REVIEW, the channel cannot be benched")),
                REMEDY=("purpose-made chamber with a swept/curved channel. NOT a bend "
                        "chamber: the user refused that on 2026-08-20 (~200 chambers for "
                        "no construction benefit)")))

    n_gdf = net.to_nodes_gdf()
    e_gdf = net.to_edges_gdf(kind="gravity")

    # A chamber with no reach at either end is not a chamber. It can only arise where a
    # route's chain ended at a node that already drained, and publishing it would put a
    # structure in the schedule and the take-off that no pipe reaches - while
    # assign_kinds_and_tiers would have to call it an "outfall" to satisfy the contract,
    # which is a lie the layer cannot be checked against. Dropped and COUNTED.
    orphan = (pd.to_numeric(n_gdf["N_IN"], errors="coerce").fillna(0) == 0) & \
             (pd.to_numeric(n_gdf["N_OUT"], errors="coerce").fillna(0) == 0)
    n_orphan = int(orphan.sum())
    if n_orphan:
        fn = rec.funnel("chambers minted -> chambers published", len(n_gdf))
        fn.drop("chamber with no reach at either end - its route's chain ended at a "
                "chamber that already drained (see outlet_conflicts)",
                ids=list(n_gdf.loc[orphan, "NODE_UID"]))
        n_gdf = n_gdf.loc[~orphan].reset_index(drop=True)
        fn.close(len(n_gdf))
    rec.metric("orphan_chambers_dropped", n_orphan)
    sharp = pd.DataFrame(sharp_rows).sort_values("INLET_DEG") if sharp_rows else pd.DataFrame(
        columns=["NODE_UID", "NODE_REF", "X", "Y", "TIER", "NODE_KIND", "INLET_DEG",
                 "INLET_EDGE", "OUT_EDGE", "N_IN", "BAND", "REMEDY"])
    rec.metric("terrain_gaps_filled", gaps)
    return n_gdf, e_gdf, sharp


# ======================================================================================
# Rehearsal: the same engine, real geometry, a stand-in hierarchy, output to run/ only
# ======================================================================================

REHEARSE_WINDOW = (444800, 2565200, 447300, 2567400)     # a dense built area east of the STP


def rehearsal_routes(surf: Surface, window=REHEARSE_WINDOW,
                     max_routes: int = 400) -> Routes:
    """A stage-4-SHAPED input built from REAL drafted corridors, for exercising this stage.

    NOT A DESIGN, and it says so in three places (this docstring, the printed banner, and
    the output going to run/ instead of shp/). What is real: the geometry, the terrain, the
    hazard grid, the plots and every placement rule. What is a stand-in: the DIRECTION (flow
    is sent toward the lowest endpoint in the window) and the TIER (by subtree size). Both
    are stage 4's to decide properly - a sub main exists because a catchment needs one way
    out, not because a ratio was met (philosophy sec 4).
    """
    src = os.path.join(K.REPO_ROOT, "W10", "shp", "W10_corridors_drafted.shp")
    g = gpd.read_file(src, bbox=window)
    if not len(g):
        raise ContractError(f"no drafted corridors in {window}")
    merged = linemerge(unary_union(list(g.geometry)))
    segs = list(merged.geoms) if merged.geom_type == "MultiLineString" else [merged]
    segs = [s for s in segs if s.length > C.MH_MIN_CLEAR_M][:max_routes]

    def key(pt):
        return (round(pt[0], 2), round(pt[1], 2))

    import networkx as nx
    G = nx.Graph()
    for i, s in enumerate(segs):
        a, b = key(s.coords[0]), key(s.coords[-1])
        G.add_edge(a, b, idx=i, length=s.length)
    comp = max(nx.connected_components(G), key=len)
    G = G.subgraph(comp).copy()

    # Root at the lowest endpoint: water goes downhill, so the outfall of the fixture is the
    # low point. Real routing is stage 3's trunk and stage 4's hierarchy.
    pts = list(G.nodes)
    zz = surf.ground([p[0] for p in pts], [p[1] for p in pts])
    root = pts[int(np.nanargmin(zz))]

    parent = nx.bfs_predecessors(G, root)
    par = dict(parent)
    rows = []
    edge_of: Dict[Tuple, int] = {}
    for n, p in par.items():
        edge_of[n] = G[n][p]["idx"]
    # subtree size drives the stand-in tier
    children: Dict[Tuple, List[Tuple]] = {}
    for n, p in par.items():
        children.setdefault(p, []).append(n)

    size: Dict[Tuple, int] = {}

    def sz(n):
        if n in size:
            return size[n]
        size[n] = 1 + sum(sz(c) for c in children.get(n, ()))
        return size[n]

    total = sz(root)
    for n, p in par.items():
        i = edge_of[n]
        line = segs[i]
        # draw it in the direction of flow: from n (upstream) to p (downstream)
        if key(line.coords[0]) != n:
            line = LineString(list(line.coords)[::-1])
        share = sz(n) / max(total, 1)
        tier = "trunk main" if share >= 0.30 else ("sub main" if share >= 0.08 else "lateral")
        rows.append(dict(CORR_ID=f"RH-{i:05d}", TIER=tier,
                         DS_CORR="" if p == root else f"RH-{edge_of[p]:05d}",
                         SRC="draft", CONFIDENCE="drafted", LEN_M=line.length,
                         geometry=line))
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=K.CRS_EPSG)
    return Routes(gdf=_normalise(gdf), rehearsal=True, source=f"REHEARSAL from {src}")


# ======================================================================================
# Plots - used ONLY for the gate
# ======================================================================================

def load_plot_centroids(rec, bbox=None) -> Optional[gpd.GeoDataFrame]:
    """Load-bearing plot centroids, for the gate rule and nothing else.

    Load ASSIGNMENT is the connections stage. This stage reads plots to answer one question:
    where does the first house on this street stand? A plot with no load is not a house.
    """
    p = os.path.join(K.REPO_ROOT, "W10", "shp", "W10_plot_loads.gpkg")
    if not os.path.exists(p):
        return None
    g = gpd.read_file(p, layer="plot_loads", bbox=bbox)
    if not len(g):
        return None
    g = g[pd.to_numeric(g["Q_AVG_M3D"], errors="coerce").fillna(0.0) > 0.0]
    if not len(g):
        return None
    cent = gpd.GeoDataFrame(g[["PLOT_ID"]].copy(), geometry=g.geometry.centroid,
                            crs=g.crs)
    rec.read("plot_loads (load-bearing, for the gate only)", p, len(cent))
    return cent


# ======================================================================================
# Runner
# ======================================================================================

def _write_skeleton(e_gdf: gpd.GeoDataFrame, path: str) -> None:
    """The reach skeleton handed to stage 6.

    NOT `contract.reaches`: that layer is the audited pipe schedule and requires DN,
    SLOPE_LAID, the inverts, the peak flow and the provenance of every one of them. Half of
    those, seeded, would be a pipe schedule nobody could tell from a designed one. What
    stage 6 needs from here is the topology and the geometry, and it carries US_NODE and
    DS_NODE written FROM the graph.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keep = ["EDGE_UID", "US_NODE", "DS_NODE", "TIER", "LEN_M", "SRC", "CONFIDENCE",
            "STAGE", "geometry"]
    e_gdf[[c for c in keep if c in e_gdf.columns]].to_file(
        path, layer="s5_reach_skeleton", driver="GPKG")


def _summary(n_gdf, e_gdf, sharp, placer) -> str:
    L = float(e_gdf["LEN_M"].sum())
    per_km = len(n_gdf) / (L / 1000.0) if L else float("nan")
    kinds = n_gdf["NODE_KIND"].value_counts().to_dict()
    tiers = e_gdf.groupby("TIER")["LEN_M"].sum().sort_values(ascending=False)
    lines = [
        f"  chambers                 {len(n_gdf):>10,}",
        f"  reaches                  {len(e_gdf):>10,}",
        f"  network length           {L/1000.0:>10.2f} km",
        f"  chambers per km          {per_km:>10.1f}    (NAMA built 32.3, W8 19.8, W10 11.1)",
        f"  longest reach            {e_gdf['LEN_M'].max():>10.1f} m   "
        f"(Table 12 floor {C.MH_SPLIT_LEN:.0f} m; W10's longest was 6,541 m)",
        f"  shortest reach           {e_gdf['LEN_M'].min():>10.2f} m",
        "  by kind                  " + ", ".join(f"{k} {v:,}" for k, v in sorted(kinds.items())),
        "  by tier (km)             " + ", ".join(f"{k} {v/1000.0:.2f}" for k, v in tiers.items()),
        f"  inlets below 90 deg      {len(sharp):>10,}    "
        f"({100.0*len(sharp)/max(len(n_gdf),1):.1f} % of chambers)",
    ]
    for k, v in placer.notes.items():
        if v:
            lines.append(f"  {k:<24} {v:>10,}")
    return "\n".join(lines)


def _self_test() -> None:
    """Prove the rules bite, on every run. Cheap, and it is the difference between a rule
    that is written down and a rule that is applied."""
    # Table 12 spacing: nothing over the limit, nothing under the clearance.
    for L in (1.0, 50.0, 99.9, 100.0, 100.1, 203.0, 6541.0):
        pos = spacing_positions(L)
        gaps = np.diff([0.0] + pos + [L])
        assert gaps.max() <= C.MH_SPLIT_LEN + 1e-6, (L, gaps.max())
        assert L <= C.MH_SPLIT_LEN or len(pos) >= 1
    assert len(spacing_positions(6541.0)) >= 65, "W10's longest reach must split 65+ ways"

    # The drop rule, at every G203-p30 boundary.
    assert classify_drop(0.0) == (0.0, "none", 0)
    assert classify_drop(0.60) == (0.0, "none", 0)
    assert classify_drop(0.61)[1] == "backdrop"
    assert classify_drop(2.0)[1] == "backdrop"
    assert classify_drop(2.01)[1] == "vortex" and classify_drop(2.01)[2] == 1

    # The inlet convention: 180 straight through, 90 square, 0 reversed.
    assert abs(inlet_angle_deg((1, 0), (1, 0)) - 180.0) < 1e-6
    assert abs(inlet_angle_deg((0, 1), (1, 0)) - 90.0) < 1e-6
    assert abs(inlet_angle_deg((1, 0), (-1, 0)) - 0.0) < 1e-6
    assert inlet_angle_deg((1, 0.2), (-1, 0.2)) < 90.0

    # The vertical DP keeps a break and ignores a straight fall.
    st = np.arange(0, 101, 5.0)
    assert profile_break_stations(st, 100.0 - 0.01 * st) == []
    v = np.where(st <= 50, 100.0 - 0.01 * st, 99.5 - 0.20 * (st - 50))
    assert profile_break_stations(st, v), "a 20 % grade break must place a chamber"

    # Merging: a junction is never moved to suit a bend.
    assert merge_close([10.0, 11.0], {10.0: 2, 11.0: 4}) == [11.0]
    assert merge_close([10.0, 30.0], {}) == [10.0, 30.0]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="W11a stage 5 - place the chambers.")
    ap.add_argument("--rehearse", action="store_true",
                    help="exercise the engine on real drafted corridors with a stand-in "
                         "hierarchy; writes to W11a/run/ only, never to W11a/shp/")
    ap.add_argument("--max-routes", type=int, default=400,
                    help="rehearsal only: cap on the number of fixture routes")
    ap.add_argument("--window", type=float, nargs=4, default=list(REHEARSE_WINDOW),
                    metavar=("X0", "Y0", "X1", "Y1"),
                    help="rehearsal only: the EPSG:32640 box to build the fixture from")
    args = ap.parse_args(argv)

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 50000))
    _self_test()
    print(f"[{STAGE}] rules self-test passed "
          f"(Table 12 spacing, G203-p30 drops, H10 inlet convention, grade break, merge)")
    print(f"[{STAGE}] PENDING ASSUMPTION {PENDING_GRADE_BREAK['name']} = "
          f"{PENDING_GRADE_BREAK['value']} {PENDING_GRADE_BREAK['units']}\n"
          f"           {PENDING_GRADE_BREAK['rule']}\n"
          f"           GAP   : {PENDING_GRADE_BREAK['gap']}\n"
          f"           BASIS : {PENDING_GRADE_BREAK['basis']}\n"
          f"           CONFIRM WITH: {PENDING_GRADE_BREAK['confirm_with']}")

    surf = Surface()
    try:
        with K.Manifest.stage(STAGE, STAGE_ORDER) as rec:
            if args.rehearse:
                print("\n" + "=" * 78)
                print("REHEARSAL - NOT A DESIGN. Real corridor geometry, real terrain, real "
                      "hazard\ngrid, real plots, every placement rule live; the DIRECTION and "
                      "the TIER are\nstand-ins for stage 4. Output goes to W11a/run/ and "
                      "never to W11a/shp/.")
                print("=" * 78)
                routes = rehearsal_routes(surf, window=tuple(args.window),
                                          max_routes=args.max_routes)
                rec.read("W10_corridors_drafted (rehearsal fixture)", routes.source,
                         routes.n)
            else:
                routes = load_routes(rec)
                if routes is None:
                    print(WAITING)
                    rec.did_nothing(
                        f"stage 4 has not published '{ROUTES_LAYER}' with TIER and DS_CORR "
                        f"to {GPKG}. A chamber is placed on a tiered directed route; this "
                        "stage does not invent one (philosophy sec 2, the order of design).")
                    return 0

            print(f"\n[{STAGE}] {routes.n:,} routes, "
                  f"{routes.gdf.geometry.length.sum()/1000.0:,.1f} km")

            bbox = tuple(routes.gdf.total_bounds)
            plots = load_plot_centroids(rec, bbox=bbox)
            print(f"[{STAGE}] {0 if plots is None else len(plots):,} load-bearing plots "
                  "in the window (gate rule only - assignment is the connections stage)")

            placer = ChamberPlacer(routes, surf, rec, plots)
            placer.build_junctions()
            placer.build_gates()
            placer.place()
            placer.build_graph()
            assign_kinds_and_tiers(placer.net)

            bad = placer.net.check()
            for b in bad:
                print(f"[{STAGE}] GRAPH NOTE: {b}")

            n_gdf, e_gdf, sharp = finish_nodes(placer.net, surf, rec)

            # Invariant 2, on what is about to be written, not on what is in memory.
            K.Network.assert_round_trip(n_gdf, e_gdf)
            K.Network.assert_degrees(n_gdf, e_gdf)

            # The named lists are written BEFORE the H12 gate below, deliberately. They are
            # the diagnostics for a failure as much as for a pass, and a stage that dies
            # with nothing recorded trips the manifest's own no-op guard and buries the real
            # message under a second exception.
            os.makedirs(RUN_DIR, exist_ok=True)
            # A rehearsal writes its own copies. The named lists are the design's H1 and H10
            # breach registers, and a rehearsal quietly overwriting them would leave 634 real
            # wadi chambers replaced by 9 rehearsal ones under the same filename.
            def _out(path: str) -> str:
                return (path.replace(".csv", "_rehearsal.csv")
                        if routes.rehearsal else path)

            sharp.to_csv(_out(SHARP_INLETS_CSV), index=False)
            rec.wrote("sharp inlets (named)", _out(SHARP_INLETS_CSV), len(sharp))
            pd.DataFrame(placer.wadi_stuck_rows).to_csv(_out(WADI_CHAMBERS_CSV), index=False)
            rec.wrote("chambers stuck on wadi ground (named)", _out(WADI_CHAMBERS_CSV),
                      len(placer.wadi_stuck_rows))
            if placer.junction_gap_rows:
                pd.DataFrame(placer.junction_gap_rows).to_csv(_out(JUNCTION_GAPS_CSV),
                                                              index=False)
                rec.wrote("routes not touching their DS_CORR (named)",
                          _out(JUNCTION_GAPS_CSV), len(placer.junction_gap_rows))

            # H12, recomputed here from the PUBLISHED geometry rather than trusted. The
            # spacing was laid along the corridor's arc; this measures the straight reach
            # that is actually published, after node merging has moved its ends.
            over = e_gdf[e_gdf["LEN_M"] > C.MH_SPLIT_LEN + 1e-6]
            if len(over):
                raise ContractError(
                    f"{len(over):,} reaches exceed the {C.MH_SPLIT_LEN:.0f} m Table 12 "
                    f"floor, longest {over['LEN_M'].max():.1f} m. That is the W10 defect "
                    "this stage exists to prevent (4,763 reaches, longest 6,541 m). "
                    f"SPACING_TARGET_M is {SPACING_TARGET_M:.0f} m precisely so node "
                    "merging cannot push a reach over - if this fires, the merge moved an "
                    "end further than the radius it is allowed.")

            if routes.rehearsal:
                out = os.path.join(RUN_DIR, "s5_rehearsal.gpkg")
                K.validate(n_gdf, "nodes", stage=STAGE)      # the contract, in full
                n_gdf.to_file(out, layer="nodes", driver="GPKG")
                e_gdf.to_file(out, layer="reach_skeleton", driver="GPKG")
                rec.wrote("nodes (REHEARSAL)", out, len(n_gdf))
                rec.wrote("reach_skeleton (REHEARSAL)", out, len(e_gdf))
                print(f"\n[{STAGE}] rehearsal written to {out}")
            else:
                K.publish(n_gdf, "nodes", K.W11A_ROOT, stage=STAGE)
                rec.wrote("nodes", GPKG, len(n_gdf))
                n_gdf.to_file(MANHOLES_SHP)
                with open(MANHOLES_SHP.replace(".shp", ".README.txt"), "w",
                          encoding="utf-8") as fh:
                    fh.write(
                        "CAD MIRROR - NOT THE AUDITED LAYER.\n"
                        "The audited artefact is W11a/shp/W11a.gpkg, layer 'nodes'.\n"
                        "contract.assert_audited_path() refuses to hand a .shp to the "
                        "auditor: the DBF truncates field names at 10 characters.\n"
                        "Levels and flows on this layer are stage 5 SEEDS (STAGE = "
                        f"'{STAGE}'): INV_M/DEPTH_M/COVER_M sit at the shallowest legal "
                        "invert (1.30 m cover, G203-p33) and Q_ADF_M3D/Q_PK_LS/N_PROP are "
                        "zero until stage 6.\n")
                rec.wrote("manholes (CAD mirror)", MANHOLES_SHP, len(n_gdf))
                _write_skeleton(e_gdf, SKELETON_GPKG)
                rec.wrote("reach skeleton (handover to stage 6)", SKELETON_GPKG, len(e_gdf))

            rec.metric("chambers", len(n_gdf))
            rec.metric("reaches", len(e_gdf))
            rec.metric("network_km", round(float(e_gdf["LEN_M"].sum()) / 1000.0, 3))
            rec.metric("chambers_per_km",
                       round(len(n_gdf) / max(float(e_gdf["LEN_M"].sum()) / 1000.0, 1e-9), 2))
            rec.metric("inlets_below_90", len(sharp))
            rec.note("levels and flows are stage 5 SEEDS, not design values: "
                     "INV_M/DEPTH_M/COVER_M at the shallowest legal invert (philosophy "
                     "sec 5, G203-p33), Q_ADF_M3D/Q_PK_LS/N_PROP zero until stage 6. "
                     "STAGE on every row says so.")

            print(f"\n[{STAGE}] RESULT")
            print(_summary(n_gdf, e_gdf, sharp, placer))
            print(f"\n[{STAGE}] sharp inlets named in {SHARP_INLETS_CSV}")
            if placer.wadi_stuck_rows:
                print(f"[{STAGE}] {len(placer.wadi_stuck_rows)} chambers left on WADI "
                      f"ground (H1, no exit) named in {WADI_CHAMBERS_CSV}\n"
                      "           They are a stage-2 corridor defect, not a chamber "
                      "problem: the fix is the route.")

            rd = K.audit_readiness(reaches=e_gdf, nodes=n_gdf,
                                   external=["roads", "hazard", "existing"])
            cant = rd[~rd["can_run"]]
            print(f"\n[{STAGE}] audit readiness: {int(rd['can_run'].sum())}/{len(rd)} checks "
                  "can run against what this stage published")
            if len(cant):
                print("           still unanswerable (they belong to stage 6, which "
                      "publishes `reaches`):")
                for _, r in cant.iterrows():
                    print(f"             {r['check']:<5} needs {r['missing']}")
            print(f"[{STAGE}] H10 will read INLET_DEG / INLET_FLAG and will FAIL while any "
                  f"inlet is under 90 deg\n           ({len(sharp):,} here). That is the "
                  "auditor working, not a defect to hide: each one\n           needs a "
                  "purpose-made chamber and each is named in the CSV above.")
    finally:
        surf.close()

    print(f"\n[{STAGE}] manifest: {K.Manifest.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
