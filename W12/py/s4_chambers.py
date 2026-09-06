"""W12 stage 4 - CHAMBERS, AND EVERY PLOT'S WAY INTO THEM.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
`W11a/py`.  The only project imports are `w12.criteria`, `w12.terrain`, `w12.asbuilt`,
`w12.contract` and `w12.present`, which are W12's own.  Earlier folders are read for
DATA (`W10/shp/W10_plot_loads.gpkg`) and for data only.

WHAT THIS STAGE DECIDES
  1. WHERE THE CHAMBERS GO, on the oriented corridor tree stage 2 published.
  2. HOW EVERY LOAD-BEARING PLOT GETS INTO ONE, and which plots cannot.
  3. WHICH CORRIDORS ARE NOT NEEDED - the ones that neither collect nor convey.

WHAT IT DOES NOT DECIDE
  It sets no invert, no gradient, no diameter, and it sites no pumping station.  It
  therefore CANNOT answer "does this plot drain".  That test needs a designed invert at
  the chamber, and stage 6 has not run.  The last iteration ran it against a SEEDED depth
  and rejected 5,715 plots for nothing.  This stage refuses to run it and says so; what it
  publishes instead is a bound that needs no invert at all - see DRAIN_SHALLOW below.

THE GUIDELINE, VERBATIM, READ FROM THE PDF ON 2026-09-03
G203-p29 sec 4.4 "Manholes & Access Points": "Manholes shall be provided at the following
locations:  * Change in pipe gradient  * Change in pipe diameter  * Junction of two or more
pipes  * At regular spacing on straight pipeline based on maintenance equipment" and, first
line of p30, "* End of each lateral sewer".

FIVE TRIGGERS.  THREE ARE PLACED; TWO ARE SATISFIED BY CONSTRUCTION, AND THAT IS AN
ARGUMENT, NOT AN EXCUSE:

  junction        PLACED. One chamber at every node of the tree with two or more inflows.
  end of lateral  PLACED. One chamber at every head.
  regular spacing PLACED. See the calibration below - the guideline hands this trigger to
                  "maintenance equipment", and NAMA's own built network is the record of
                  what their maintenance equipment is.
  diameter change SATISFIED BY CONSTRUCTION.  A diameter can only change where flow
                  changes, flow only enters at a chamber (G203-p19 sec 3.6: "Connection to
                  the Main Sewer will be done at a manhole... There must be no penetrating
                  connection"), and a reach in this design IS chamber-to-chamber.  So a
                  diameter change cannot fall between two chambers.  Re-checked at sizing.
  gradient change SATISFIED BY CONSTRUCTION AT THIS SPACING, to the limit of what the
                  terrain can resolve.  H13/G203-p29 already require "Uniform slopes...
                  between successive manholes", so a DESIGNED gradient change lands on a
                  chamber by definition.  A GROUND grade break finer than
                  GRADE_BREAK_MIN_MM_M cannot be seen at all - the derivation is below -
                  and every break coarser than it is longer than the chamber spacing.

THE ONE NUMBER THAT DOMINATES THIS STAGE, AND IT IS MEASURED
Table 12 (G203-p30) caps chamber spacing at 100 m for DN200-315.  NAMA DO NOT BUILD
ANYWHERE NEAR IT.  Measured over their 3,265 built gravity pipes: median spacing 29.77 m,
mean 29.23 m, p90 38.25 m, MAXIMUM EVER BUILT 71.38 m, and 34.23 chambers per km.  NOT ONE
of the 3,265 exceeds Table 12.  Since the guideline itself defers regular spacing to
"maintenance equipment", the operator's own built network is the evidence of what that
equipment reaches, and this stage lays chambers at their median rather than at the legal
ceiling.  The whole sweep is published, because this single choice moves the chamber count
by a factor of three and nothing else in the stage comes close.

STRAIGHTNESS IS ALSO MEASURED, NOT ASSUMED
98.1 % of NAMA's built pipes are a straight two-point line; the polyline departs from its
own chord by a median 0.000 m and a p99 of 0.020 m, and only 0.64 % depart by more than
0.5 m.  A pipe is laid straight between chambers.  So a corridor is split wherever it
departs from the chord since the last chamber by more than STRAIGHT_TOL_M - which places a
chamber at every bend WITHOUT needing an invented angle threshold.  For context the
deflection at their own through-chambers is bimodal: 74.7 % below 5 deg (a chamber on a
straight run) and a spike of 11.2 % between 85 and 95 deg (a chamber at a corner).

PLOT CONNECTIONS - RANK EVERY CARRIER, NEVER JUST THE NEAREST
The last iteration searched only the NEAREST carrier and rejected 30 % of the load;
ranking every carrier within reach recovered 20 points of it on 53 km LESS pipe and no new
chambers.  So this stage ranks EVERY chamber within reach of every plot, on one declared
cost in metres, and publishes the A/B against the two poorer searches on the same chamber
set and the same cost - arms A (nearest chamber) and B (nearest corridor) in `search_ab`.

ZERO SILENT DROPS
Every load-bearing plot appears exactly once in `connections` or in `unserved`, each with a
WHY, and `verify()` re-reads the published file and reconciles the load to the milligram.

TWO DEFECTS THE FIRST FULL RUN PUBLISHED, AND WHAT WAS DONE ABOUT THEM
1. THREE PAIRS OF CHAMBERS STOOD INSIDE THE MINIMUM CLEARANCE and `verify()` said so.
   `criteria.MH_SNAP_M` = 3.0 m is the radius at which `s1_roads` merged two positions into
   ONE node AND the minimum clear distance between two chambers, so publishing a pair inside
   it is a contradiction.  Every one was the two ends of an arc SHORTER than the clearance -
   `split_positions` keeps interior chambers 3 m clear but always keeps both arc ends, and
   a handful of stage 2's ~13,100 arcs are under 3.0 m.  `contract_pairs()` now merges them
   into one structure and publishes what it removed.  See that method for why this is not
   "changing stage 2's topology", the previous run's reason for leaving them.  EVERY COUNT
   IN THIS PARAGRAPH MOVES WITH THE UPSTREAM LAYER and is computed fresh each run - the
   published figures are in `close_pairs` and the manifest, never here.
2. THE INLET ANGLE WAS MEASURED ON THE WRONG NETWORK - before the prune, so (in that run)
   2,324 chambers carried an angle off a pipe that is not in the layer and 145 carried a
   priced swept-channel flag for an inlet that had been deleted; and the direction of flow
   was taken from a segment's first two coordinates, which `substring` leaves duplicated on
   about 1,900 of them.  `angles()` now runs after `prune()` and takes the direction from
   the CHORD.  The count went UP, not down, because the sliver had been reporting corridors
   that turn back on themselves as 179.9 deg - straight through.  The breaches are split by
   cause in `inlet_split`, the number fixable by MOVING a chamber is measured there rather
   than asserted, and each is priced as a swept-channel chamber, which is what G203-p30
   asks for in the same paragraph as the 90 deg clause.

3. AND THE DEFECT THE FIX ITSELF LEFT, NAMED HERE RATHER THAN FOUND LATER.  The chord is
   the right basis only where the reach is straight, and the stage had never measured that
   on its own output: a few published reaches depart from their own chord by more than
   STRAIGHT_TOL_M, which is a bend with no chamber at it - `split_positions` drops a bend
   cut that lands inside the 3 m clearance, and `contract_pairs` re-divides an absorbed
   reach for LENGTH but not for straightness.  On exactly those reaches the H10 verdict
   changes if the direction of flow is read locally instead of across the chord.  Both
   counts are measured every run (`n_bent`, `n_basis_amb`), published in the manifest, the
   compliance table and `inlet_split`, and NOT resolved here: chambering those bends would
   put two chambers inside the very clearance the contraction exists to honour.

RUN
  python s4_chambers.py                 build, publish, report
  python s4_chambers.py --verify        re-read the published file and re-check it
  python s4_chambers.py --selftest      prove every rule on a synthetic network
  python s4_chambers.py --sweep         spacing sensitivity only, no publish
  python s4_chambers.py --split 50      build at a different chamber spacing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))            # .../W12/py
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from w12 import criteria as CR                                # noqa: E402
from w12 import asbuilt as AB                                 # noqa: E402
from w12 import contract as CT                                # noqa: E402
from w12 import terrain as T                                  # noqa: E402

C = CR.DEFAULT

STAGE = "s4_chambers"
STAGE_VERSION = "W12-chambers-1.0"

# ================================================================== paths
W12 = os.path.dirname(_HERE)                                  # .../W12
CLAUDE = os.path.dirname(W12)                                 # .../Hydraulic/Claude
HYDRAULIC = os.path.dirname(CLAUDE)

ORIENT_GPKG = os.path.join(W12, "shp", "W12_orient.gpkg")
ROADS_GPKG = os.path.join(W12, "shp", "W12_roads.gpkg")
PLOTS_GPKG = os.path.join(CLAUDE, "W10", "shp", "W10_plot_loads.gpkg")   # DATA only
ROAD_REC = os.path.join(HYDRAULIC, "SHP", "Road centerline 2", "Road_Centercline.shp")

OUT_GPKG = os.path.join(W12, "shp", "W12_chambers.gpkg")
RUN = os.path.join(W12, "run", "chambers")
REPORT_MD = os.path.join(RUN, "CHAMBERS.md")
MANIFEST_JSON = os.path.join(RUN, "chambers_manifest.json")

CRS_EPSG = CT.CRS_EPSG                       # 32640, project rule, every layer

# ==========================================================================================
# CONSTANTS.  Every one is a guideline value with its page, a value MEASURED in this
# project, or a PROJECT choice that says it is one.  Nothing here is invented.
# ==========================================================================================

# --- guideline: chamber spacing and the triggers -----------------------------------------
TAB12_BANDS = C.MH_SPACING_BANDS      # G203-p30 Table 12, transcribed in criteria.py:
#                                       200-315 -> 100 m | 350-900 -> 120 m
#                                       1000-1400 -> 150 m | more than 1400 -> 200 m
TAB12_TIGHTEST_M = C.mh_max_spacing(200)      # 100.0 m. The DN200-315 band, and the binding
#                                       one before a diameter exists: any spacing legal at
#                                       DN200 is legal at every larger size.
INLET_MIN_DEG = C.INLET_MIN_DEG       # 90 deg. G203-p30, verbatim: "No inlet pipe at
#                                       manholes shall have an angle less than 90 deg to
#                                       the direction of flow."
DROP_TRIGGER_M = C.DROP_TRIGGER       # 0.60 m. G203-p30 / p19 sec 3.6. NOT APPLIED HERE -
#                                       a drop is an INVERT difference and there are no
#                                       inverts at stage 4. Named so it is visibly deferred.
MH_MIN_CLEAR_M = C.MH_MIN_CLEAR_M     # 3.0 m. PROJECT (criteria): two chambers closer than
#                                       this ARE one structure.
FANOUT_OFFSET_M = C.FANOUT_OFFSET_M   # 10.0 m. PROJECT (user rule 2026-08-18; philosophy
#                                       sec 4's "10 m clearance between a branch start and
#                                       the chamber it joins"): a branch leaving a chamber
#                                       that already has an outlet starts 10 m away. It is
#                                       what keeps "exactly one pipe leaves a junction"
#                                       true on a corridor graph that offers more.

# --- guideline: the tertiary chain, G203 section 3 ---------------------------------------
HCC_OFFSET_M = C.HCC_OFFSET_M         # 2.5 m. G203-p17 sec 3.2, verbatim: "The HCC is
#                                       usually installed 2.5 m from the property boundary
#                                       in the public right-of-way (ROW)".
TERT_MAX_M = C.LATERAL_MAX_LEN        # 45.0 m. G203-p22 Table 6 prints "Maximum Length
#                                       45 m" on the LATERAL SEWER ROW ONLY - checked
#                                       against the PDF today, that is the row it is on.
#                                       G203-p17 sec 3.2 then writes "Rider Sewers and
#                                       Lateral Sewers (maximum Length 45 m)", attaching it
#                                       to both. We take the conservative reading, 45 m on
#                                       the whole tertiary run, as a declared PROJECT cap.
PCS_MAX_M = C.PCS_MAX_LEN             # 50.0 m. G203-p18 under Table 4: "The length of the
#                                       PCS should not exceed 50 m in order to allow
#                                       maintenance. If necessary, a manhole will be added."
#                                       The PCS is INSIDE the property (p17: the PCC is
#                                       "inside the property and at the boundary"), so it
#                                       is not our geometry - it is reported, not designed.
HCC_PER_RIDER = C.MAX_HCC_PER_RIDER   # 3. G203-p17 sec 3.2: "Several HCC (usually up to 3)
#                                       may be connected together by one or several Rider
#                                       Sewers within the public ROW." "usually" - so it is
#                                       a convention, and it is used here as the point at
#                                       which a chamber starts to be charged for congestion,
#                                       never as a hard cap that could drop a plot.
HCC_DEPTH_MIN = C.HCC_DEPTH_MIN       # 1.2 m. G203-p19 sec 3.4: HCC depth "ranges between
HCC_DEPTH_MAX = C.HCC_DEPTH_MAX       # 1.2 m and 2.0 m depending on the size of the plot".
TERT_SLOPE_MIN = C.RIDER_MIN_SLOPE    # 0.01 = 1 %. G203-p18 Table 5, Rider and Lateral rows.
TERT_SLOPE_MAX = C.RIDER_MAX_SLOPE    # 0.10 = 10 %.
PCS_SLOPE_MIN = C.PCS_MIN_SLOPE       # 0.03 = 3 %. G203-p18 Table 5, PCS row.
MIN_COVER_M = C.MIN_COVER_CROWN       # 1.30 m. G203-p33 sec 4.6.3.
DN_TERTIARY = C.DN_TERTIARY           # 160 mm OD. G203-p22 Table 6, Rider/PC Sewer row.
DN_MIN_LATERAL = C.DN_MIN_LATERAL     # 200 mm OD. G203-p22 Table 6, Lateral Sewer row.

# --- guideline: chamber type, which is a LOCATION rule and belongs here -------------------
RECT_MAX_DEPTH_M = 1.4                # m. G203-p19 sec 3.4a, verbatim: rectangular concrete
#                                       chambers 600 x 750 mm "are usually used for shallow
#                                       connection with depth not exceeding 1.4 m and are
#                                       not recommended where chambers are located under
#                                       the traffic lanes". Repeated as a RESTRICTED
#                                       LOCATION at G203-p31 sec 4.4.1 i.b.
CIRC_ID_M = 1.0                       # m. G203-p19 sec 3.4b: circular HCC internal diameter
#                                       1.0 m, "widely used for plot connections", depth
#                                       1.0 to 2.0 m.

# --- measured, read at run time so they cannot go stale ----------------------------------
# The values in these comments are what they measured on 2026-09-03; the code reads them
# fresh every run and the manifest publishes what it actually got.
#   BUILT_SPACING_MED_M   29.77 m   asbuilt.m_spacing()['mh_spacing_median_m']
#   BUILT_SPACING_MAX_M   71.38 m   asbuilt.m_spacing()['mh_spacing_max_m']
#   BUILT_MH_PER_KM       34.23     asbuilt.m_spacing()['mh_per_km']
#   BUILT_OVER_TAB12_PCT   0.00 %   asbuilt.m_spacing()['spacing_over_tab12_pct']
#   BUILT_RUN_MED_M       68.74 m   asbuilt.m_runs()['run_between_junctions_median_m']
#   SIGMA_DZ_M            0.4769 m  terrain manifest, DIFFERENTIAL error vs NAMA's surveyed
#                                   levels. The right sigma for a FALL, per terrain.py.

# --- project choices, each declared, each swept or measured -------------------------------
STRAIGHT_TOL_M = 0.5      # PROJECT, CALIBRATED. A run is split where the corridor departs
#                           from the straight chord since the last chamber by more than
#                           this. Measured: 99.36 % of NAMA's built pipes are inside 0.5 m
#                           of their own chord (median 0.000, p99 0.020, max 23.67). It
#                           replaces an invented bend-angle threshold with the physical
#                           rule a straight pipe actually obeys.
SPACING_SWEEP_M = (20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0, 71.4, 100.0)
#                           the split lengths reported. 29.77 is the built median, 71.4 the
#                           longest pipe NAMA ever built, 100.0 Table 12's DN200 ceiling.

# The plot-connection cost, in METRES OF EQUIVALENT PIPE so the terms can be added and read.
PEN_CROSS_PLOT_M = 45.0   # PROJECT. A tertiary run that crosses a third party's plot needs
#                           a wayleave. Priced at one full legal run (TERT_MAX_M) so it is
#                           always worth avoiding and never worth dropping a plot for.
PEN_CROSS_DUAL_M = 45.0   # PROJECT. Same price. Project rule 7 forbids a pipe ALONG a dual
#                           carriageway; crossing one is legal (philosophy H1a) but it is a
#                           priced structure, not a free straight line.
PEN_WADI_M = 45.0         # PROJECT. Same price, for a chamber standing on wadi ground,
#                           which G203-p30 sec 4.4.1 i.a prohibits. It is a penalty and not
#                           a veto because a veto would drop the load silently; the
#                           chambers themselves are flagged and counted for re-siting.
CONGEST_M = 15.0          # PROJECT. Charged per connection already on a chamber BEYOND the
#                           free HCC_PER_RIDER = 3 (G203-p17). One third of a legal run.
#                           Swept in `congestion_sweep`; the answer barely moves, which is
#                           the point of publishing it.
CAND_TOPK = 8             # PROJECT. How many candidates per plot carry the expensive
#                           crossing tests. Ranked by bare length first, so the cheap ones
#                           are always in. Sensitivity in `topk_sweep`.
DUAL_BAND_M = 6.0         # PROJECT, matching stage 1's own constant (its `dual_band` table
#                           publishes the exposure at eight half-widths). Re-declared here
#                           rather than imported, because a stage must not depend on
#                           another stage's internals.

BEARING_MIN_LEG_M = 1e-6  # m. NOT a design value and NOT a tolerance: the only thing it
#                           guards is a segment whose two ends are the same point, where
#                           `atan2(0, 0)` returns 0.0 and manufactures a due-north bearing
#                           out of nothing. The direction of flow is taken from the CHORD -
#                           see `angles()` for why, and for the measurement behind it.

BEARING_LEG_SWEEP_M = (0.5, 1.0, 2.0)
#                           A SWEEP, NOT A CHOSEN VALUE, and it sets nothing in the design.
#                           The published direction of flow is the CHORD, which is right
#                           wherever the reach is straight - and 52,610 of 56,667 reaches
#                           are a two-point line, so on those the chord IS the leg and the
#                           two bases are the same number. Where a reach BENDS, they are
#                           not, and no single basis is defensible: the pipe leaves the
#                           chamber along the local leg, but the stage's own rule says a
#                           pipe is laid straight between chambers, which makes the chord
#                           the pipe. Rather than pick, the H10 verdict is re-taken over
#                           the first/last stretch of the reach at each of these floors and
#                           the chambers whose verdict CHANGES are counted, published and
#                           named. A swept bound, not an invented tolerance.

# The built network's own inlet-angle profile, MEASURED in this project on NAMA's 2006
# as-built and written up as finding N10 of `W12/docs/ASBUILT_STUDY.md`. It is the benchmark
# this stage is read against, and it is quoted here as a measurement with its source, never
# as a target: G203-p30's 90 deg is the requirement and the built network breaches it too.
AB_INLET = {
    "inlets": 3261, "under90": 371, "under90_pct": 11.38,
    "branch_n": 240, "branch_med": 88.55, "branch_within5": 186, "branch_within5_pct": 77.5,
    "hairpin_n": 122,
    "junction_pct": 26.46, "passthrough_pct": 5.26,
    "src": "W12/docs/ASBUILT_STUDY.md N10, measured on the 2006 as-built",
}

FINGER_M = 60.0           # PROJECT (philosophy sec 4, ours on cost grounds; no adoption
#                           standard requires it). A dead-end reach under this length
#                           serving nothing is a finger. Reported, not used as the prune
#                           rule - the prune rule is stronger and needs no length at all.

GRID = "R5"               # the 5 m working grid, for the fast pass. Every PUBLISHED chamber
#                           level is resampled off the NATIVE 0.5 m VRT, because terrain.py
#                           states that anything which becomes a LEVEL must be.

TAU_FLAG = f"tau={C.TAU_PA:g} Pa ASSUMED (GAP-9)"


def _log(msg: str) -> None:
    print(f"[{STAGE}] {msg}", flush=True)


# ==========================================================================================
# small helpers
# ==========================================================================================

def _md(df: pd.DataFrame, nd: int = 2, maxrows: Optional[int] = None) -> str:
    """A markdown table with no dependency on tabulate."""
    d = df if maxrows is None else df.head(maxrows)
    if len(d) == 0:
        return "_(no rows)_\n"
    cols = list(d.columns)
    txt = []
    for _, r in d.iterrows():
        row = []
        for c in cols:
            v = r[c]
            if isinstance(v, float) and np.isfinite(v):
                row.append(f"{v:,.{nd}f}")
            elif v is None or (isinstance(v, float) and not np.isfinite(v)):
                row.append("-")
            elif isinstance(v, (int, np.integer)):
                row.append(f"{int(v):,}")
            else:
                row.append(str(v))
        txt.append(row)
    w = [max(len(str(c)), *(len(t[i]) for t in txt)) for i, c in enumerate(cols)]
    out = ["| " + " | ".join(str(c).ljust(w[i]) for i, c in enumerate(cols)) + " |",
           "|" + "|".join("-" * (x + 2) for x in w) + "|"]
    for t in txt:
        out.append("| " + " | ".join(t[i].ljust(w[i]) for i in range(len(cols))) + " |")
    if maxrows is not None and len(df) > maxrows:
        out.append(f"\n_({len(df) - maxrows:,} more rows in the csv)_")
    return "\n".join(out) + "\n"


def _write_table(df: pd.DataFrame, name: str) -> None:
    os.makedirs(RUN, exist_ok=True)
    df.to_csv(os.path.join(RUN, f"{name}.csv"), index=False, encoding="utf-8")


def _sha1(path: str, n: int = 16) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:n]


def _bearing(ax, ay, bx, by) -> float:
    return math.degrees(math.atan2(bx - ax, by - ay)) % 360.0


def _end_bearings(c: np.ndarray, min_leg_m: float) -> Tuple[float, float]:
    """(departure at the first coordinate, arrival at the last) over a stretch of at least
    `min_leg_m`, or over the whole reach when it is shorter than that.

    `min_leg_m <= 0` gives the CHORD, which is what the stage publishes.  A positive floor
    gives the LOCAL direction of the pipe at the chamber, guarded so that `substring`'s
    duplicated vertex - measured on this stage's own output, about 3,800 of 113,000 reach
    ends carry a leg under one micrometre - cannot set it.  Both are needed: see
    `BEARING_LEG_SWEEP_M`.
    """
    if min_leg_m <= 0.0:
        b = _bearing(c[0][0], c[0][1], c[-1][0], c[-1][1])
        return b, b
    k = 1
    while k < len(c) - 1 and math.hypot(c[k][0] - c[0][0], c[k][1] - c[0][1]) < min_leg_m:
        k += 1
    j = len(c) - 2
    while j > 0 and math.hypot(c[-1][0] - c[j][0], c[-1][1] - c[j][1]) < min_leg_m:
        j -= 1
    return (_bearing(c[0][0], c[0][1], c[k][0], c[k][1]),
            _bearing(c[j][0], c[j][1], c[-1][0], c[-1][1]))


def chord_offset_of(c: np.ndarray) -> float:
    """How far a reach departs from its OWN chord.  The stage rests on this being small -
    it is why a corridor is split at every bend and why the direction of flow is taken from
    the chord - and it was never measured on the reaches the stage publishes."""
    ax, ay = float(c[0][0]), float(c[0][1])
    bx, by = float(c[-1][0]), float(c[-1][1])
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L < 1e-12 or len(c) < 3:
        return 0.0
    return float(max(abs((px - ax) * dy - (py - ay) * dx) / L for px, py in c))


def _inlet_angle(arr_bearing: float, dep_bearing: float) -> float:
    """G203-p30's angle: 180 deg is straight on, 90 deg is a right-angle inlet, 0 deg is
    flow doubling back on itself.  Same convention as stage 2, so the two are comparable."""
    turn = abs(((dep_bearing - arr_bearing + 180.0) % 360.0) - 180.0)
    return 180.0 - turn


def grade_break_floor_mm_m(sigma_dz_m: float, window_m: float) -> float:
    """The smallest change in GROUND gradient the terrain can actually resolve, mm/m.

    A gradient over a window W is (z2 - z1)/W, and the error on a difference of two levels
    a corridor-length apart is sigma_dz (terrain.py: the DIFFERENTIAL error, which is the
    right one for a fall).  Two such gradients differ by sqrt(2) * sigma_dz / W in the
    noise alone; at 3 sigma the detectable change is 3 * sqrt(2) * sigma_dz / W.

    At sigma_dz = 0.4769 m and W = 30 m this is 67.4 mm/m - a 6.7 % break.  Anything
    gentler than that is invisible, which is WHY the gradient-change trigger is not fired
    from the terrain at this stage.
    """
    return 3.0 * math.sqrt(2.0) * sigma_dz_m / window_m * 1000.0


# ==========================================================================================
# 1.  CHAMBER MINTING - the geometry rules, isolated so the self-test can prove them
# ==========================================================================================

def chord_offset_max(xy: np.ndarray, i0: int, i1: int) -> float:
    """Largest perpendicular distance from vertices i0..i1 to the chord i0->i1, metres."""
    if i1 - i0 < 2:
        return 0.0
    a = xy[i0]
    b = xy[i1]
    v = b - a
    L = math.hypot(v[0], v[1])
    if L < 1e-9:
        return float(np.max(np.hypot(*(xy[i0:i1 + 1] - a).T)))
    n = np.array([-v[1], v[0]]) / L
    return float(np.max(np.abs((xy[i0:i1 + 1] - a) @ n)))


def bend_breaks(xy: np.ndarray, tol_m: float) -> List[int]:
    """Vertex indices at which the polyline must be broken so that every piece lies within
    `tol_m` of its own chord.  Greedy and minimal-from-the-left: extend the current piece
    until it bulges, then close it at the last vertex that did not.

    This is the physical rule, measured: 98.1 % of NAMA's built pipes are a straight
    two-point line and 99.36 % lie inside 0.5 m of their own chord.  A pipe is laid
    straight between chambers; where the corridor is not straight, a chamber is required.
    """
    n = len(xy)
    if n < 3:
        return []
    breaks: List[int] = []
    anchor = 0
    k = 2
    while k < n:
        if chord_offset_max(xy, anchor, k) > tol_m:
            cut = k - 1
            if cut <= anchor:                      # a single segment cannot bulge; guard
                cut = k
            breaks.append(cut)
            anchor = cut
            k = anchor + 2
        else:
            k += 1
    return breaks


def split_positions(s: np.ndarray, xy: np.ndarray, split_m: float,
                    tol_m: float) -> np.ndarray:
    """Distances along one corridor at which a chamber stands, ENDPOINTS INCLUDED.

    Two rules, in this order:
      1. break at every bend (`bend_breaks`), because a pipe is straight between chambers;
      2. divide each straight piece into EQUAL parts, as few as possible, such that no
         part exceeds `split_m`.

    Equal division rather than criteria.MH_ROUND_STEP rounding: rounding a 95 m piece to
    10 m steps leaves a 5 m stub and a chamber 5 m from its neighbour, inside the 3 m
    minimum clearance's own order of magnitude.  Equal division leaves no stub.  This is a
    DECLARED departure from that project assumption, and it never lengthens a spacing.
    """
    L = float(s[-1])
    cuts = [0.0]
    for b in bend_breaks(xy, tol_m):
        cuts.append(float(s[b]))
    cuts.append(L)
    cuts = sorted(set(round(c, 6) for c in cuts))
    out: List[float] = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        seg = b - a
        if seg <= 1e-6:
            continue
        n = max(1, int(math.ceil(seg / split_m - 1e-9)))
        step = seg / n
        out.extend(a + step * i for i in range(n))
    out.append(L)
    arr = np.array(sorted(set(round(v, 6) for v in out)))
    # two chambers closer than the minimum clearance ARE one structure (criteria.MH_SNAP_M)
    keep = [arr[0]]
    for v in arr[1:-1]:
        if v - keep[-1] >= MH_MIN_CLEAR_M:
            keep.append(v)
    if len(arr) > 1:
        if arr[-1] - keep[-1] < MH_MIN_CLEAR_M and len(keep) > 1:
            keep.pop()
        keep.append(arr[-1])
    return np.array(keep)


def trim(s: np.ndarray, xy: np.ndarray, s0: float) -> Tuple[np.ndarray, np.ndarray]:
    """The part of a corridor from `s0` to its end, as (distances, coordinates).

    Used for the FANOUT: a run that starts at a chamber which already has an outlet begins
    FANOUT_OFFSET_M along, not at the chamber (criteria.FANOUT_OFFSET_M, project rule
    2026-08-18; philosophy sec 4 "10 m clearance between a branch start and the chamber it
    joins").
    """
    if s0 <= 1e-9:
        return s, xy
    k = int(np.searchsorted(s, s0, side="right"))
    if k >= len(s):
        return s[-1:], xy[-1:]
    a = xy[k - 1]
    b = xy[k]
    seg = s[k] - s[k - 1]
    f = 0.0 if seg <= 0 else (s0 - s[k - 1]) / seg
    p = a + (b - a) * f
    return (np.concatenate([[s0], s[k:]]) - s0,
            np.vstack([p, xy[k:]]))


# ==========================================================================================
# 2.  THE STAGE
# ==========================================================================================

class Chambers:
    """Reads stage 2's oriented tree, mints the chambers, connects the plots, prunes what
    neither collects nor conveys, and publishes."""

    def __init__(self, split_m: Optional[float] = None, quiet: bool = False):
        import geopandas as gpd
        self.gpd = gpd
        self.quiet = quiet
        self.notes: List[str] = []
        self.t0 = time.time()
        self.split_override = split_m

    # ---------------------------------------------------------------- inputs
    def load(self) -> "Chambers":
        gpd = self.gpd
        _log("reading stage 2's oriented tree")
        self.arcs = gpd.read_file(ORIENT_GPKG, layer="arcs").set_crs(CRS_EPSG,
                                                                    allow_override=True)
        self.onodes = gpd.read_file(ORIENT_GPKG, layer="nodes").set_crs(CRS_EPSG,
                                                                       allow_override=True)
        _log(f"    {len(self.arcs):,} arcs, {self.arcs.LEN_M.sum() / 1000:,.1f} km; "
             f"{len(self.onodes):,} nodes")

        _log("reading the plot loads (DATA from W10, not code)")
        pl = gpd.read_file(PLOTS_GPKG, layer="plot_loads").set_crs(CRS_EPSG,
                                                                  allow_override=True)
        pl["Q_AVG_M3D"] = pd.to_numeric(pl["Q_AVG_M3D"], errors="coerce").fillna(0.0)
        self.plots_all = pl
        self.plots = pl[pl.Q_AVG_M3D > 0].reset_index(drop=True).copy()
        _log(f"    {len(self.plots):,} load-bearing plots, "
             f"{self.plots.Q_AVG_M3D.sum():,.1f} m3/d, "
             f"{self.plots.N_PROP.sum():,.0f} properties")

        _log("measuring the built network")
        ab = AB.AsBuilt()
        self.m_spacing = ab.m_spacing()
        self.m_runs = ab.m_runs()
        self.m_inv = ab.m_inventory()
        self.built_straight = self._measure_built_straightness(ab)
        _log(f"    built spacing median {self.m_spacing['mh_spacing_median_m']:.2f} m, "
             f"max {self.m_spacing['mh_spacing_max_m']:.2f} m, "
             f"{self.m_spacing['mh_per_km']:.2f} chambers/km, "
             f"{self.m_spacing['spacing_over_tab12_pct']:.2f} % over Table 12")

        man = T.manifest_read()
        self.sigma_dz = float(man["dem_quality"]["sigma_dz_m"])
        self.sigma_z = float(man["dem_quality"]["sigma_z_m"])
        self.tf = T.TerrainFlow.load(GRID)

        # THE calibration: the split length, from the operator's own network.
        med = float(self.m_spacing["mh_spacing_median_m"])
        step = C.MH_ROUND_STEP
        self.split_m = (float(self.split_override) if self.split_override
                        else max(step, round(med / step) * step))
        _log(f"    chamber spacing set to {self.split_m:.1f} m "
             f"(built median {med:.2f} m rounded to {step:g} m; "
             f"Table 12 allows {TAB12_TIGHTEST_M:.0f} m at DN200-315)")
        self.grade_floor = grade_break_floor_mm_m(self.sigma_dz, self.split_m)
        return self

    @staticmethod
    def _measure_built_straightness(ab) -> dict:
        """How straight is a pipe NAMA actually built?  The evidence behind STRAIGHT_TOL_M."""
        import shapely
        g = ab.pipes
        sag = np.zeros(len(g))
        nv = np.zeros(len(g), dtype=int)
        for i, geom in enumerate(g.geometry.values):
            c = shapely.get_coordinates(geom)
            nv[i] = len(c)
            if len(c) > 2:
                sag[i] = chord_offset_max(c, 0, len(c) - 1)
        return {
            "pipes_n": int(len(g)),
            "two_point_pct": float((nv == 2).mean() * 100.0),
            "sagitta_median_m": float(np.median(sag)),
            "sagitta_p99_m": float(np.percentile(sag, 99)),
            "sagitta_max_m": float(sag.max()),
            "within_0p5m_pct": float((sag <= 0.5).mean() * 100.0),
        }

    # ---------------------------------------------------------------- minting
    def mint(self) -> "Chambers":
        """Place chambers on every arc.  One identity space, minted once."""
        import shapely
        from shapely.geometry import Point

        a = self.arcs
        drop_ring = a.ROLE.eq("ring") | a.US_NODE.eq(a.DS_NODE)
        if drop_ring.any():
            self.notes.append(
                f"{int(drop_ring.sum())} arc(s) excluded: a closed ring whose two ends are "
                f"the same node ({a.loc[drop_ring, 'LEN_M'].sum():,.0f} m). It cannot carry "
                f"a direction, so it cannot carry a chamber sequence.")
        self.arcs = a = a[~drop_ring].reset_index(drop=True).copy()

        _log(f"minting chambers at {self.split_m:.0f} m, "
             f"straightness tolerance {STRAIGHT_TOL_M:g} m")
        geoms = list(a.geometry.values)
        self._geoms = geoms
        owner = self._owners()

        # ---- where each arc's run STARTS -------------------------------------------------
        # "AT A JUNCTION, EXACTLY ONE PIPE LEAVES" (philosophy sec 4). Stage 2's arborescence
        # gives every node exactly one outgoing TREE arc, but it also publishes 3,081 `head`
        # corridors the branching did not use, oriented to their own low end - and 2,887 of
        # them leave a node that already has a tree outlet. Two pipes leaving one chamber is
        # a bifurcation and H15 forbids it. The project rule for exactly this case already
        # exists: criteria.FANOUT_OFFSET_M, "a branch leaving a chamber that already has an
        # outlet starts 10 m away" (user 2026-08-18; philosophy sec 4's 10 m clearance).
        s_start = np.zeros(len(a))
        absorbed: List[int] = []
        for i in range(len(a)):
            if owner.get(str(a.US_NODE.values[i])) == i:
                continue
            L = float(a.LEN_M.values[i])
            f = min(FANOUT_OFFSET_M, L / 2.0)
            if f < MH_MIN_CLEAR_M or L - f < MH_MIN_CLEAR_M:
                absorbed.append(i)
                s_start[i] = np.nan
            else:
                s_start[i] = f
        self.s_start = s_start
        self.absorbed = set(absorbed)
        nfan = int(np.nansum(s_start > 0))
        _log(f"    {nfan:,} runs start {FANOUT_OFFSET_M:g} m off a chamber that already has "
             f"an outlet (criteria.FANOUT_OFFSET_M); {len(absorbed)} corridor(s) too short "
             f"to fan out and absorbed")
        if absorbed:
            self.notes.append(
                f"{len(absorbed)} corridor(s), "
                f"{a.LEN_M.values[absorbed].sum():,.0f} m in total, leave a chamber that "
                f"already has an outlet and are shorter than twice the 3 m minimum chamber "
                f"clearance, so no run can start on them. They are absorbed and appear in "
                f"the `pruned` layer.")

        recs_pos: List[Tuple[int, float, str]] = []      # arc index, s along, trigger
        arc_pos: List[np.ndarray] = []
        for i, g in enumerate(geoms):
            if i in self.absorbed:
                arc_pos.append(np.zeros(0))
                continue
            xy = shapely.get_coordinates(g)
            d = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xy[:, 0]),
                                                          np.diff(xy[:, 1])))])
            s0 = float(s_start[i])
            dt, xt = trim(d, xy, s0)
            pos = split_positions(dt, xt, self.split_m, STRAIGHT_TOL_M) + s0
            arc_pos.append(pos)
            bset = (set(np.round(dt[bend_breaks(xt, STRAIGHT_TOL_M)] + s0, 6))
                    if len(xt) > 2 else set())
            for p in pos[1:-1]:
                recs_pos.append((i, float(p), "bend" if round(p, 6) in bset else "spacing"))
        self.arc_pos = arc_pos

        # --- node chambers: one per orient node, keeping the orient identity as a label
        on = self.onodes.set_index("NODE_ID")
        keep_arcs = [i for i in range(len(a)) if i not in self.absorbed]
        used_nodes = pd.unique(np.concatenate([a.US_NODE.values[keep_arcs],
                                               a.DS_NODE.values[keep_arcs]]))
        on = on.loc[on.index.intersection(used_nodes)]
        kind_map = {"junction": "junction", "head": "head", "outfall": "outfall",
                    "through": "chamber"}

        rows = []
        uid = 0
        node_uid: Dict[str, str] = {}
        for nid, r in on.iterrows():
            uid += 1
            u = CT.NODE_UID_FMT.format(uid)
            node_uid[str(nid)] = u
            rows.append({"NODE_UID": u, "ORIENT_ND": str(nid), "X": float(r.X),
                         "Y": float(r.Y), "TRIGGER": kind_map.get(str(r.KIND), "chamber"),
                         "ARC_CID": "", "S_ALONG": np.nan, "SUBNET": str(r.SUBNET)})
        n_node_ch = len(rows)

        # --- the fan-out chambers, one per arc that does not own its upstream node
        cid = a.CID.astype(str).values
        sub = a.SUBNET.astype(str).values
        fan_uid: Dict[int, str] = {}
        for i in keep_arcs:
            if s_start[i] <= 0:
                continue
            uid += 1
            u = CT.NODE_UID_FMT.format(uid)
            fan_uid[i] = u
            p = geoms[i].interpolate(float(s_start[i]))
            rows.append({"NODE_UID": u, "ORIENT_ND": "", "X": float(p.x), "Y": float(p.y),
                         "TRIGGER": "fanout", "ARC_CID": cid[i],
                         "S_ALONG": float(s_start[i]), "SUBNET": sub[i]})
        self.fan_uid = fan_uid

        # --- interior chambers
        for i, s, trig in recs_pos:
            uid += 1
            p = geoms[i].interpolate(s)
            rows.append({"NODE_UID": CT.NODE_UID_FMT.format(uid), "ORIENT_ND": "",
                         "X": float(p.x), "Y": float(p.y), "TRIGGER": trig,
                         "ARC_CID": cid[i], "S_ALONG": float(s), "SUBNET": sub[i]})

        ch = pd.DataFrame(rows)
        self._uid_next = uid + 1          # the identity space continues here, never restarts
        self.node_uid = node_uid
        _log(f"    {n_node_ch:,} at graph nodes  +  {len(fan_uid):,} fan-out  +  "
             f"{len(recs_pos):,} interior = {len(ch):,} chambers")
        self.ch = ch
        return self

    def _owners(self) -> Dict[str, int]:
        """Which arc owns each node's ONE outgoing chamber connection.

        A node's outlet is its TREE arc, because that is what stage 2's arborescence chose.
        An OUTFALL never owns one - it discharges to the Main Pipe and a pipe leaving it
        would carry sewage away from the works.  An island component has no tree arc at all,
        so there the steepest outgoing arc owns the node, which cannot cycle because every
        island arc runs from its higher end to its lower one; a cycle guard asserts it.
        """
        a = self.arcs
        outfall = set(self.onodes.loc[self.onodes.KIND == "outfall", "NODE_ID"].astype(str))
        owner: Dict[str, int] = {}
        for i in np.flatnonzero(a.ROLE.values == "tree"):
            u = str(a.US_NODE.values[i])
            if u in outfall:
                continue
            if u in owner:
                raise RuntimeError(f"node {u} has two outgoing TREE arcs - stage 2's "
                                   f"arborescence is not an arborescence")
            owner[u] = int(i)
        isl = np.flatnonzero(a.ROLE.values == "island")
        cand: Dict[str, Tuple[float, str, int]] = {}
        for i in isl:
            u = str(a.US_NODE.values[i])
            if u in outfall or u in owner:
                continue
            f = float(a.FALL_M.values[i])
            if not np.isfinite(f) or f <= 0:
                continue
            k = (f, str(a.CID.values[i]), int(i))
            if u not in cand or k > cand[u]:
                cand[u] = k
        for u, (_, _, i) in cand.items():
            owner[u] = i
        # cycle guard on the island chains
        nxt = {u: str(a.DS_NODE.values[v[2]]) for u, v in cand.items()}
        for start in list(nxt):
            u, path = start, set()
            while u in nxt:
                if u in path:
                    raise RuntimeError(f"island chaining produced a cycle at {u}")
                path.add(u)
                u = nxt[u]
        return owner

    def link(self) -> "Chambers":
        """Chain the chambers along each arc into segments.  Topology is WRITTEN DOWN
        (philosophy H16), never inferred from geometry afterwards."""
        from shapely.ops import substring
        a = self.arcs
        ch = self.ch
        inter = ch[(ch.ARC_CID != "") & (ch.TRIGGER != "fanout")]
        by_arc: Dict[str, pd.DataFrame] = {k: v.sort_values("S_ALONG")
                                           for k, v in inter.groupby("ARC_CID")}
        rows = []
        chain: Dict[str, List[str]] = {}
        for i in range(len(a)):
            if i in self.absorbed:
                continue
            r = a.iloc[i]
            c = str(r.CID)
            s0 = float(self.s_start[i])
            u = self.fan_uid[i] if s0 > 0 else self.node_uid[str(r.US_NODE)]
            d = self.node_uid[str(r.DS_NODE)]
            mid = by_arc.get(c)
            ids = [u] + (list(mid.NODE_UID.values) if mid is not None else []) + [d]
            pos = [s0] + (list(mid.S_ALONG.values) if mid is not None else []) + \
                  [float(self.arc_pos[i][-1])]
            chain[c] = ids
            g = self._geoms[i]
            for k in range(len(ids) - 1):
                rows.append({"US_NODE": ids[k], "DS_NODE": ids[k + 1],
                             "ARC_CID": c, "SEQ": k,
                             "S0": pos[k], "S1": pos[k + 1],
                             "LEN_M": pos[k + 1] - pos[k],
                             "ROLE": str(r.ROLE), "SUBNET": str(r.SUBNET),
                             "SRC": str(r.SRC), "CONFIDENCE": str(r.CONFIDENCE),
                             "geometry": substring(g, pos[k], pos[k + 1])})
        self.seg = pd.DataFrame(rows)
        self.chain = chain
        _log(f"    {len(self.seg):,} chamber-to-chamber segments, "
             f"{self.seg.LEN_M.sum() / 1000:,.1f} km")
        return self

    # ---------------------------------------------------------------- contraction
    def contract_pairs(self) -> "Chambers":
        """Two chambers inside the minimum clearance ARE one structure - so build one.

        `criteria.MH_SNAP_M` = 3.0 m is a single constant wearing two hats: it is the radius
        at which `s1_roads` merged positions into one node ("noding at MH_SNAP_M = 3 m"),
        and it is the minimum clear distance between two chambers.  Publishing two chambers
        closer than the radius that merges nodes is a contradiction, not a tolerance.

        WHERE THEY COME FROM, MEASURED, NOT ASSUMED.  A handful of stage 2's ~13,100 arcs
        are shorter than 3.0 m - eight when this was written, seven an hour later, because
        the orient layer moved under it - and every node pair within 3.0 m in the whole
        `orient` node layer was one of them: there is no such pair that is not joined by an
        arc.  The count is taken from the data every run and published in `close_pairs`;
        nothing here depends on it.  `split_positions` already keeps
        every interior chamber 3 m clear WITHIN an arc; what it cannot do is refuse to put a
        chamber at each END of an arc that is itself shorter than the clearance.  So the
        defect is exactly one shape: a whole corridor shorter than the clearance.

        WHY MERGING IS NOT "CHANGING STAGE 2'S TOPOLOGY".  The two nodes are inside the very
        radius s1 used to declare two positions one node; s2 inherited the pair, it did not
        design it.  Merging is also NOT silent - the pairs are published in `close_pairs`
        with what happened to each, the count is in the manifest, and the absorbed arcs fall
        into the `pruned` layer.  `s6_levels` A-LEV-13 already contracts these downstream;
        doing it HERE is what makes this stage's own published layers self-consistent, and
        it leaves s6 nothing to contract.

        Anything a pass can ADD, a later pass must be able to TAKE AWAY: `mint` added the
        chambers, this pass removes them, and it says how many.
        """
        import shapely
        from shapely.geometry import LineString
        seg = self.seg
        short = (seg.LEN_M.values < MH_MIN_CLEAR_M)
        self.n_contracted = 0
        self.n_resplit = 0
        self.n_resplit_live = 0
        self.resplit_uids = []
        self.contracted = pd.DataFrame(columns=["A", "B", "GAP_M"])
        if not short.any():
            _log(f"    no segment shorter than the {MH_MIN_CLEAR_M:g} m minimum clearance; "
                 f"nothing to contract")
            self._close_after_contract()
            return self

        sh = seg[short]
        # merge the UPSTREAM chamber into the DOWNSTREAM one: the downstream chamber is the
        # one that carries the outgoing pipe onward, and the upstream chamber's only outgoing
        # pipe IS the segment being contracted (out-degree is 1 on a forest).
        into: Dict[str, str] = dict(zip(sh.US_NODE.astype(str), sh.DS_NODE.astype(str)))
        tail: Dict[str, List[tuple]] = {}
        for u, d, g in zip(sh.US_NODE.astype(str), sh.DS_NODE.astype(str),
                           sh.geometry.values):
            tail[u] = [tuple(c) for c in shapely.get_coordinates(g)][1:]
        # resolve chains A->B->C.  The graph is a forest and every hop follows the flow, so
        # this terminates; the guard is there because a cycle here would loop for ever.
        for _ in range(len(into) + 1):
            nxt = {a: into.get(b, b) for a, b in into.items()}
            if nxt == into:
                break
            into = nxt
        else:
            raise RuntimeError("contracting the sub-clearance pairs did not settle - the "
                               "segment graph is not a forest")
        hop = {u: v for u, v in zip(sh.US_NODE.astype(str), sh.DS_NODE.astype(str))}
        path_to: Dict[str, List[tuple]] = {}
        for a in list(hop):
            path, u = [], a
            while u in hop:                       # A -> B -> C walks tail[A] then tail[B]
                path.extend(tail[u])
                u = hop[u]
            path_to[a] = path

        xy = dict(zip(self.ch.NODE_UID.astype(str),
                      zip(self.ch.X.astype(float), self.ch.Y.astype(float))))
        keep = seg[~short].copy()
        old_ds = keep.DS_NODE.astype(str).values.copy()
        moved = np.array([d in into for d in old_ds])
        if keep.US_NODE.astype(str).isin(into).any():
            raise RuntimeError("a chamber being contracted away still has an outgoing "
                               "segment - out-degree was not 1 at minting")
        keep["DS_NODE"] = [into.get(str(v), str(v)) for v in keep.DS_NODE.values]
        if moved.any():
            g = list(keep.geometry.values)
            L = list(keep.LEN_M.values)
            for r in np.flatnonzero(moved):
                c = [tuple(p) for p in shapely.get_coordinates(g[r])]
                # follow the REAL corridor to the surviving chamber, not a straight jump:
                # the contracted segment's own coordinates are the path between them.
                for p in path_to.get(old_ds[r], []):
                    if math.hypot(p[0] - c[-1][0], p[1] - c[-1][1]) > 1e-6:
                        c.append(p)
                dest = xy[str(keep.DS_NODE.values[r])]
                if math.hypot(dest[0] - c[-1][0], dest[1] - c[-1][1]) > 1e-6:
                    c.append(dest)
                g[r] = LineString(c)
                L[r] = float(g[r].length)
            keep["geometry"] = g
            keep["LEN_M"] = L
        # A kept segment whose two ends land on the same surviving chamber would be a
        # 2-cycle in a forest and cannot happen - but dropping it QUIETLY if it ever did is
        # a silent drop, which is the worst defect this project has shipped. Refuse instead.
        loop = int((keep.US_NODE.astype(str) == keep.DS_NODE.astype(str)).sum())
        if loop:
            raise RuntimeError(
                f"contracting the sub-clearance pairs turned {loop} segment(s) into a "
                f"self-loop, which means the segment graph is not a forest. Nothing is "
                f"dropped here to hide it")
        self.seg = keep.reset_index(drop=True)
        gone = set(into)
        self.ch = self.ch[~self.ch.NODE_UID.astype(str).isin(gone)].reset_index(drop=True)
        self.chain = {c: [into.get(str(u), str(u)) for u in ids]
                      for c, ids in self.chain.items()}

        self.contracted = pd.DataFrame({
            "A": sh.US_NODE.astype(str).values,
            "B": sh.DS_NODE.astype(str).values,
            "GAP_M": np.round(sh.LEN_M.values.astype(float), 3),
        })
        self.n_contracted = len(gone)
        self._resplit_over_split_length()
        _log(f"    {len(sh)} segment(s) shorter than the {MH_MIN_CLEAR_M:g} m minimum "
             f"clearance CONTRACTED: {self.n_contracted} chamber(s) removed, "
             f"{sh.LEN_M.sum():.2f} m of pipe absorbed, "
             f"{len(self.ch):,} chambers / {len(self.seg):,} segments left")
        self.notes.append(
            f"{len(sh)} pair(s) of chambers stood closer than the {MH_MIN_CLEAR_M:g} m "
            f"minimum clearance (criteria.MH_SNAP_M), every one of them at the two ends of "
            f"a corridor shorter than the clearance itself. Two chambers inside the radius "
            f"that MERGES nodes are one structure, so they were contracted into one: "
            f"{self.n_contracted} chamber(s) removed and {sh.LEN_M.sum():.2f} m of pipe "
            f"absorbed into the reach above. The record is in `close_pairs`.")
        self._close_after_contract()
        return self

    def _resplit_over_split_length(self) -> None:
        """A reach that absorbed a stub and is now over the split length gets a chamber back.

        Contracting a pair hands the sub-clearance stub to the reach above it, so that reach
        can end up to MH_SNAP_M longer than the shipped spacing - one segment did, at
        31.02 m against 30 m.  It is still far inside Table 12's 100 m, so nothing illegal
        happened; but "no segment over the shipped split length" is a check this stage makes
        about itself, and the way to keep a check true is to fix the thing it measures, not
        to widen the check.  The reach is divided into equal parts by the SAME rule
        `split_positions` uses, so no stub is left behind.
        """
        from shapely.ops import substring
        over = np.flatnonzero(self.seg.LEN_M.values > self.split_m + 1e-6)
        self.n_resplit = 0
        self.resplit_uids: List[str] = []
        if not len(over):
            return
        uid = getattr(self, "_uid_next", len(self.ch) + 1)
        rows_ch, rows_sg, drop = [], [], []
        for r in over:
            row = self.seg.iloc[r]
            g = row.geometry
            L = float(g.length)
            n = max(2, int(math.ceil(L / self.split_m - 1e-9)))
            step = L / n
            ids = [str(row.US_NODE)]
            for k in range(1, n):
                p = g.interpolate(step * k)
                u = CT.NODE_UID_FMT.format(uid)
                uid += 1
                ids.append(u)
                self.resplit_uids.append(u)
                rows_ch.append({"NODE_UID": u, "ORIENT_ND": "", "X": float(p.x),
                                "Y": float(p.y), "TRIGGER": "spacing",
                                "ARC_CID": str(row.ARC_CID), "S_ALONG": np.nan,
                                "SUBNET": str(row.SUBNET)})
            ids.append(str(row.DS_NODE))
            for k in range(n):
                d = row.to_dict()
                # SEQ and S0/S1 belong to the run BEFORE the contraction: the sub-parts all
                # carry the parent's ordinal, and S along the arc is meaningless once a
                # reach crosses into the corridor that was absorbed. Nothing downstream
                # reads either (checked), and a fabricated position would be worse than a
                # blank. US_NODE/DS_NODE carry the topology, as H16 requires.
                d.update({"US_NODE": ids[k], "DS_NODE": ids[k + 1], "SEQ": int(row.SEQ),
                          "S0": np.nan, "S1": np.nan,
                          "geometry": substring(g, step * k, step * (k + 1))})
                d["LEN_M"] = float(d["geometry"].length)
                rows_sg.append(d)
            drop.append(r)
            self.n_resplit += n - 1
            # A chamber that is not in `self.chain` is invisible to `_chamber_arcs()`, and
            # `connect()` uses that to decide which chambers sit on a plot's nearest
            # corridor - so an unregistered chamber silently drops out of arm B and out of
            # the keep-rule that saves a same-corridor carrier from the top-K cut. Register
            # it where it stands.
            arc = str(row.ARC_CID)
            ch_ids = self.chain.get(arc)
            if ch_ids is not None and str(row.US_NODE) in ch_ids:
                at = ch_ids.index(str(row.US_NODE))
                self.chain[arc] = ch_ids[:at + 1] + ids[1:-1] + ch_ids[at + 1:]
            else:
                self.notes.append(
                    f"{len(ids) - 2} re-split chamber(s) on arc {arc} could not be placed "
                    f"in the corridor chain, so they are not candidates on arm B of the "
                    f"connection search. Named rather than left to be noticed.")
        self._uid_next = uid
        keep = self.seg.drop(index=self.seg.index[drop])
        self.seg = pd.concat([keep, pd.DataFrame(rows_sg)],
                             ignore_index=True).reset_index(drop=True)
        self.ch = pd.concat([self.ch, pd.DataFrame(rows_ch)],
                            ignore_index=True).reset_index(drop=True)
        _log(f"    {len(drop)} reach(es) went over the {self.split_m:g} m split length once "
             f"the stub was absorbed; {self.n_resplit} chamber(s) put back so no reach does")
        self.notes.append(
            f"{len(drop)} reach(es) exceeded the {self.split_m:g} m split length after "
            f"absorbing a contracted stub and were divided into equal parts by the same "
            f"rule `split_positions` uses, putting {self.n_resplit} chamber(s) back. The "
            f"check was not widened to let them through. That count is taken HERE, before "
            f"the prune - `tables()` reports how many of them are still in the published "
            f"layer, because a number a reader cannot find in the deliverable is the "
            f"defect this stage just finished removing from the inlet angles.")

    def _close_after_contract(self) -> None:
        """What, if anything, is STILL inside the clearance once the pairs are contracted.

        A pair joined by a pipe can be contracted.  A pair NOT joined by a pipe cannot -
        merging it would fuse two independent branches into one, which is a layout decision
        and not a levelling one.

        This scan runs on the WHOLE minted set, before the prune, so it is a build-time
        diagnostic and NOT the published number: `tables()` re-scans the chambers that are
        actually published and that is what `close_pairs`, the compliance row and `verify()`
        all report.  Publishing the pre-prune count would overstate the defect.
        """
        import shapely as _sh
        from shapely import STRtree as _T
        p = _sh.points(self.ch.X.values, self.ch.Y.values)
        a, b = _T(p).query(p, predicate="dwithin", distance=MH_MIN_CLEAR_M - 1e-6)
        m = a < b
        self.residual_pairs = int(m.sum())
        if self.residual_pairs:
            _log(f"    {self.residual_pairs} pair(s) are inside {MH_MIN_CLEAR_M:g} m and "
                 f"NOT joined by a pipe, so they cannot be contracted without fusing two "
                 f"branches. Re-counted on the PUBLISHED chambers after pruning")

    # ---------------------------------------------------------------- levels
    def levels(self, native: bool = True) -> "Chambers":
        """Ground at every chamber.  NATIVE 0.5 m VRT, because terrain.py states that
        anything which becomes a LEVEL must be read off it and a chamber cover is one."""
        x = self.ch.X.values
        y = self.ch.Y.values
        _log(f"sampling ground at {len(x):,} chambers "
             f"({'native 0.5 m VRT' if native else 'the 5 m working grid'})")
        t0 = time.time()
        if native:
            # order by native tile so the tile cache is hit rather than thrashed
            key = np.lexsort(((x // 256).astype(np.int64), (y // 256).astype(np.int64)))
            z = np.empty(len(x), float)
            z[key] = self.tf.elevation(x[key], y[key], native=True)
        else:
            z = self.tf.elevation(x, y)
        zg = self.tf.elevation(x, y)                       # the grid value, for comparison
        self.ch["GRD_M"] = np.where(np.isfinite(z), z, zg)
        self.ch["GRD_GRID"] = zg
        self.ch["HAZ"] = self.tf.hazard_class(x, y).astype(int)
        self.ch["ON_WADI"] = np.isin(self.ch.HAZ.values,
                                     list(C.HAZARD_WADI_CLASSES)).astype(int)
        d = np.abs(self.ch.GRD_M.values - zg)
        _log(f"    {time.time() - t0:.0f} s; native minus grid: mean {np.nanmean(d):.3f} m, "
             f"p99 {np.nanpercentile(d, 99):.3f} m, max {np.nanmax(d):.3f} m")
        _log(f"    {int(self.ch.ON_WADI.sum()):,} chambers stand on wadi ground "
             f"(hazard class 4/5/6 of the 50-yr grid) - G203-p30 4.4.1 prohibits it")
        return self

    def fall(self) -> "Chambers":
        """Ground fall on every segment, and the inlet angle at every chamber."""
        g = dict(zip(self.ch.NODE_UID, self.ch.GRD_M))
        self.seg["GRD_US"] = self.seg.US_NODE.map(g).astype(float)
        self.seg["GRD_DN"] = self.seg.DS_NODE.map(g).astype(float)
        self.seg["GND_FALL"] = self.seg.GRD_US - self.seg.GRD_DN
        self.seg["GND_SLOPE"] = np.where(self.seg.LEN_M > 0,
                                         self.seg.GND_FALL / self.seg.LEN_M * 100.0, 0.0)
        self.seg["AGN_GRADE"] = (self.seg.GND_FALL < -C.ADVERSE_MIN_M).astype(int)
        self.seg["RISE_M"] = np.maximum(0.0, -self.seg.GND_FALL)
        # Table 12 is a MAXIMUM by diameter; before a diameter exists the binding band is
        # the DN200-315 one, and any spacing legal there is legal at every larger size.
        self.seg["SPACE_OK"] = (self.seg.LEN_M <= TAB12_TIGHTEST_M + 1e-6).astype(int)
        w = dict(zip(self.ch.NODE_UID, self.ch.ON_WADI))
        self.seg["ON_WADI"] = ((self.seg.US_NODE.map(w).fillna(0).astype(int)
                                + self.seg.DS_NODE.map(w).fillna(0).astype(int)) == 2
                               ).astype(int)
        return self

    def angles(self) -> "Chambers":
        """The angle at every chamber between an arriving pipe and the pipe that leaves.

        G203-p30, verbatim: "No inlet pipe at manholes shall have an angle less than 90 deg
        to the direction of flow."  Recomputed here on the CHAMBERED geometry - stage 2
        measured it on whole corridors, this measures it on the pipe that is actually laid.

        IT RUNS AFTER THE PRUNE, AND THAT IS THE POINT.  Measured before it, the angle at a
        chamber is the smallest over inlets that include pipes the prune then threw away:
        the previous run published 2,324 angles derived from a pipe that is not in the
        published layer and 145 SWEPT_CH flags - a priced chamber detail each - for an
        inlet that does not exist.  The minimum over a subset can only rise, so every one of
        those was an over-count, never an under-count; but a priced item for a pipe that was
        deleted is a defect whichever way it leans.

        THE DIRECTION OF FLOW IS THE CHORD, AND THAT IS MEASURED, NOT PREFERRED.  A pipe is
        laid straight between two chambers - 98.1 % of NAMA's built pipes are a two-point
        line and 99.36 % lie inside 0.5 m of their own chord, which is the same evidence
        `STRAIGHT_TOL_M` rests on and the reason this stage breaks a corridor at every bend.
        On this design the segments come out straighter still: median sagitta 0.0000 m,
        p99 0.0000 m.  The previous run took the bearing from a segment's FIRST TWO and LAST
        TWO coordinates instead, and `substring` leaves a duplicated vertex: **about 1,900
        segments in 56,700 begin with a leg shorter than one millimetre** (counted fresh
        every run into `n_sliver`), so the "direction of flow" out of those chambers was
        read off a sub-millimetre sliver rather than off the 25 m pipe.  It hid breaches -
        corridors turning back on themselves at a chamber - by reporting them as 179.9 deg,
        straight through.

        AND THE CHORD IS RIGHT ONLY WHERE THE REACH IS STRAIGHT, WHICH IS MEASURED HERE AND
        IS NOT ALWAYS TRUE.  `chord_offset_of` is applied to every published reach: the ones
        past `STRAIGHT_TOL_M` carry a bend with no chamber at it, and on those the chord is
        a fiction in exactly the way the sliver was.  The verdict is therefore re-taken over
        the pipe's LOCAL direction at each floor of `BEARING_LEG_SWEEP_M` and the chambers
        that change side are counted into `n_basis_amb` - with the ones published COMPLIANT
        called out separately, because those carry no priced swept channel.  Swept and
        published; NOT settled by choosing whichever basis gives the smaller number.

        INLET_DEG IS FLOORED TO 2 dp, NOT ROUNDED TO 1.  At 1 dp an 89.96 deg inlet
        publishes as "90.0" beside INLET_FLAG = 1: the number says compliant and the flag
        says not.  That happened on 85 chambers, which is why INLET_FLAG (2,952) and a
        re-derivation from INLET_DEG (2,867) disagreed.  Rounding at ANY precision can round
        a breach up onto the limit, so the published angle is FLOORED - it may understate
        compliance by up to 0.01 deg and can never overstate it.
        """
        import shapely
        s = self.seg
        bear_in: Dict[str, List[Tuple[float, str]]] = {}
        bear_out: Dict[str, float] = {}
        # the same two dictionaries at every floor of BEARING_LEG_SWEEP_M, so the H10
        # verdict can be re-taken on the LOCAL direction of the pipe as well as on the chord
        leg_in: Dict[float, Dict[str, List[float]]] = {m: {} for m in BEARING_LEG_SWEEP_M}
        leg_out: Dict[float, Dict[str, float]] = {m: {} for m in BEARING_LEG_SWEEP_M}
        n_degen = 0
        n_sliver = 0
        bend: List[Tuple[str, str, float, float]] = []
        for u, d, cid, geom in zip(s.US_NODE.values, s.DS_NODE.values,
                                   s.ARC_CID.values, s.geometry.values):
            c = shapely.get_coordinates(geom)
            if len(c) < 2 or math.hypot(c[-1][0] - c[0][0],
                                        c[-1][1] - c[0][1]) < BEARING_MIN_LEG_M:
                n_degen += 1
                continue
            if math.hypot(c[1][0] - c[0][0], c[1][1] - c[0][1]) < 1e-3:
                n_sliver += 1            # the evidence for taking the bearing off the chord
            off = chord_offset_of(c)
            if off > STRAIGHT_TOL_M:
                bend.append((str(u), str(d), round(off, 3), float(shapely.length(geom))))
            b = _bearing(c[0][0], c[0][1], c[-1][0], c[-1][1])
            bear_out[u] = b
            bear_in.setdefault(d, []).append((b, str(cid)))
            if off > 0.0:                    # a straight reach gives the same two bearings
                for m in BEARING_LEG_SWEEP_M:
                    b0, b1 = _end_bearings(c, m)
                    leg_out[m][u] = b0
                    leg_in[m].setdefault(d, []).append(b1)
            else:
                for m in BEARING_LEG_SWEEP_M:
                    leg_out[m][u] = b
                    leg_in[m].setdefault(d, []).append(b)
        self.n_sliver = n_sliver
        self.t_bent = pd.DataFrame(bend, columns=["US_NODE", "DS_NODE", "OFFSET_M",
                                                  "LEN_M"]).sort_values(
            "OFFSET_M", ascending=False) if bend else pd.DataFrame(
            columns=["US_NODE", "DS_NODE", "OFFSET_M", "LEN_M"])
        self.n_bent = len(bend)
        if n_degen:
            self.notes.append(
                f"{n_degen} segment(s) start and end at the same point, so no bearing and "
                f"no inlet angle can be taken at either end. A bearing from two identical "
                f"points is 0 deg due north, which is a fabricated measurement.")

        ang = np.full(len(self.ch), np.nan)
        out_cid = dict(zip(s.US_NODE.values, s.ARC_CID.astype(str).values))
        is_node = dict(zip(self.ch.NODE_UID.values,
                           (self.ch.ORIENT_ND.astype(str).values != "").astype(int)))
        rows: List[dict] = []
        for i, u in enumerate(self.ch.NODE_UID.values):
            ins = bear_in.get(u)
            out = bear_out.get(u)
            if not ins or out is None:
                continue
            # floored ONCE, off the raw angle. Flooring an already-floored float again can
            # drop another 0.01 (88.27 * 100 is 8826.999999999998 in binary), which is how
            # the published minimum and a re-measurement came to differ by exactly 0.01.
            vals = [_inlet_angle(b, out) for b, _ in ins]
            ang[i] = min(vals)
            for (b, cid), v in zip(ins, vals):
                vf = math.floor(v * 100.0) / 100.0
                if vf < INLET_MIN_DEG:
                    rows.append({"CHAMBER": u, "DEG": vf, "N_IN": len(ins),
                                 "SAME_ARC": int(cid == out_cid.get(u, "")),
                                 # a chamber standing ON a stage-2 graph node cannot be
                                 # moved at all - the node IS where the corridors meet. One
                                 # that is not could in principle be slid along its
                                 # corridor. This is what makes "fixable by moving a
                                 # chamber" a MEASUREMENT rather than a claim.
                                 "AT_NODE": int(is_node.get(u, 0))})
        # The FLAG is derived from the PUBLISHED number, not from the raw one, so the two can
        # never tell different stories - a reader who re-derives the flag from INLET_DEG must
        # get the flag that is there. It leans the only safe way: an angle within a hundredth
        # of the limit is published as a breach, never as compliance we cannot show.
        pub = np.floor(ang * 100.0) / 100.0
        self.ch["INLET_DEG"] = pub
        self.ch["INLET_FLAG"] = ((pub < INLET_MIN_DEG) & np.isfinite(pub)).astype(int)
        # The resolution for a sharp inlet is a CHAMBER DETAIL, not a softer number: a
        # purpose-made chamber with a swept channel. G203-p30 requires benching "formed to
        # permit safe access and to maximise hydraulic efficiency" and "Smooth transitions
        # between inlet and outlet"; the 90 deg clause sits in the same paragraph. Flagged
        # here so it is a KNOWN, PRICED item rather than an unnoticed one.
        self.ch["SWEPT_CH"] = self.ch["INLET_FLAG"]
        self._sub90 = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["CHAMBER", "DEG", "N_IN", "SAME_ARC", "AT_NODE"])
        # THE DENOMINATOR IS THE INLETS THE RULE CAN BE APPLIED TO, not every pipe end.
        # An inlet at an outfall has no outgoing pipe to be measured against, so it can
        # never breach; counting it dilutes the breach rate. It is 355 inlets here, and it
        # moved the branch rate from 25.96 % to 26.44 % - the difference between beating
        # NAMA's own 26.46 % and matching it, which is exactly the direction a flattering
        # denominator always leans.
        self._n_inlets_all = int(sum(len(v) for v in bear_in.values()))
        self._n_inlets = int(sum(len(v) for u, v in bear_in.items() if u in bear_out))
        self._n_in_branch = int(sum(len(v) for u, v in bear_in.items()
                                    if u in bear_out and len(v) >= 2))
        n = int(np.isfinite(ang).sum())
        self.n_inlet_na = int(len(self.ch) - n)

        # --- IS THE VERDICT AN ARTEFACT OF THE BASIS?  Re-take it on the local direction
        # of the pipe at each swept floor and count the chambers that change side. On a
        # straight reach the two are the same number, so this can only ever name the
        # reaches that bend - and it is those the chord assumption is weakest on.
        amb = np.zeros(len(self.ch), bool)
        self.amb_by_floor: Dict[float, int] = {}
        base_flag = self.ch["INLET_FLAG"].values.astype(bool)
        for m in BEARING_LEG_SWEEP_M:
            lo, li = leg_out[m], leg_in[m]
            a2 = np.array([min((_inlet_angle(b, lo[u]) for b in li[u]), default=np.nan)
                           if (u in li and u in lo) else np.nan
                           for u in self.ch.NODE_UID.values])
            f2 = (np.floor(a2 * 100.0) / 100.0 < INLET_MIN_DEG) & np.isfinite(a2)
            self.amb_by_floor[m] = int((f2 != base_flag).sum())
            amb |= (f2 != base_flag)
        self.n_basis_amb = int(amb.sum())
        self.n_basis_amb_unpriced = int((amb & ~base_flag).sum())
        self.amb_uids = list(self.ch.NODE_UID.values[amb])
        if self.n_basis_amb:
            self.notes.append(
                f"{self.n_basis_amb} chambers change side of the {INLET_MIN_DEG:g} deg rule "
                f"depending on whether the direction of flow is read from the reach's CHORD "
                f"(what is published) or from the pipe's LOCAL direction at the chamber "
                f"({'/'.join(f'{m:g}' for m in BEARING_LEG_SWEEP_M)} m). All of them sit on "
                f"one of the {self.n_bent} reaches that depart from their own chord by more "
                f"than STRAIGHT_TOL_M = {STRAIGHT_TOL_M:g} m, where the stage's own rule "
                f"that a pipe is laid straight between chambers does not hold. "
                f"{self.n_basis_amb_unpriced} of them are published as COMPLIANT and would "
                f"be a breach on the local reading, so their swept channel is NOT priced. "
                f"NOT RESOLVED HERE: fixing it means chambering the bend, which would put "
                f"two chambers inside the {MH_MIN_CLEAR_M:g} m clearance on the contracted "
                f"reaches - two project rules that genuinely conflict on this geometry.")
        if self.n_bent:
            self.notes.append(
                f"{self.n_bent} published reach(es) depart from their own chord by more "
                f"than STRAIGHT_TOL_M = {STRAIGHT_TOL_M:g} m (worst "
                f"{self.t_bent.OFFSET_M.max():.2f} m) - a bend with no chamber at it. The "
                f"stage claims the opposite and had no check for it. "
                f"`split_positions` drops a bend cut that falls within the "
                f"{MH_MIN_CLEAR_M:g} m minimum clearance of a neighbour, and "
                f"`contract_pairs` re-splits an absorbed reach for LENGTH but not for "
                f"straightness. Named and sized, not silently fixed.")

        _log(f"    inlet angle measurable at {n:,} chambers on {self._n_inlets:,} inlets "
             f"the rule applies to ({self._n_inlets_all:,} pipe ends in all); "
             f"{int(self.ch.INLET_FLAG.sum()):,} below {INLET_MIN_DEG:g} deg (G203-p30); "
             f"{self.n_inlet_na:,} chambers have no inlet pipe to measure")
        if self.n_bent or self.n_basis_amb:
            _log(f"    {self.n_bent} reach(es) bend beyond STRAIGHT_TOL_M "
                 f"{STRAIGHT_TOL_M:g} m; {self.n_basis_amb} chambers' H10 verdict depends "
                 f"on whether the direction of flow is the chord or the local leg "
                 f"({self.n_basis_amb_unpriced} of them published as compliant)")
        return self

    # ---------------------------------------------------------------- connections
    def connect(self) -> "Chambers":
        """Every load-bearing plot to a chamber, ranking EVERY carrier within reach."""
        import shapely
        from shapely import STRtree

        pl = self.plots
        ch = self.ch
        _log(f"connecting {len(pl):,} load-bearing plots; reach "
             f"{TERT_MAX_M:g} m of tertiary + {HCC_OFFSET_M:g} m HCC offset "
             f"= {TERT_MAX_M + HCC_OFFSET_M:g} m from the plot boundary")

        pts = shapely.points(ch.X.values, ch.Y.values)
        tree = STRtree(pts)
        reach = TERT_MAX_M + HCC_OFFSET_M
        pg = pl.geometry.values
        t0 = time.time()
        pi, ci = tree.query(pg, predicate="dwithin", distance=reach)
        _log(f"    {len(pi):,} plot-chamber candidate pairs in {time.time() - t0:.0f} s "
             f"({len(pi) / max(len(pl), 1):.1f} per plot)")

        # Distance is measured to the plot BOUNDARY, not to the polygon.  A polygon returns
        # zero for a chamber standing INSIDE it - a road corridor crossing a large holding -
        # and that reads as a free connection when the run is in fact the whole way out to
        # the boundary.  `verify()` caught exactly that: a 65.64 m line carrying L_TERT = 0.
        bnd = shapely.boundary(pg)
        d = shapely.distance(bnd[pi], pts[ci])
        tert = np.maximum(0.0, d - HCC_OFFSET_M)
        ok = tert <= TERT_MAX_M + 1e-9
        pi, ci, d, tert = pi[ok], ci[ok], d[ok], tert[ok]

        # --- the expensive terms, only on the top-K by bare length, plus arm B's pick
        order = np.lexsort((tert, pi))
        pi, ci, d, tert = pi[order], ci[order], d[order], tert[order]
        rank = np.zeros(len(pi), dtype=int)
        if len(pi):
            newp = np.r_[True, pi[1:] != pi[:-1]]
            grp = np.cumsum(newp) - 1
            start = np.zeros(grp.max() + 1, dtype=int)
            start[grp[newp]] = np.flatnonzero(newp)
            rank = np.arange(len(pi)) - start[grp]

        # arm B's candidate set: the chambers on the plot's NEAREST corridor.  A chamber at
        # a graph node sits on EVERY corridor meeting there, so membership is a set.
        arcs_of_ch = self._chamber_arcs()
        near_arc = self._nearest_arc(pl)
        same_arc = np.array([near_arc[p] in arcs_of_ch[c] for p, c in zip(pi, ci)])

        keep = (rank < CAND_TOPK) | same_arc
        pi, ci, d, tert, rank, same_arc = (pi[keep], ci[keep], d[keep], tert[keep],
                                           rank[keep], same_arc[keep])
        _log(f"    {len(pi):,} pairs carry the crossing tests "
             f"(top {CAND_TOPK} by length, plus every chamber on the nearest corridor)")

        # --- HCC point: on the plot boundary, offset HCC_OFFSET_M toward the chamber
        near = shapely.shortest_line(bnd[pi], pts[ci])
        nc = shapely.get_coordinates(near).reshape(-1, 2, 2)
        p0, p1 = nc[:, 0, :], nc[:, 1, :]
        v = p1 - p0
        L = np.hypot(v[:, 0], v[:, 1])
        step = np.minimum(HCC_OFFSET_M, L)
        u = np.divide(v, np.where(L[:, None] > 0, L[:, None], 1.0))
        hcc = p0 + u * step[:, None]
        coords = np.empty((2 * len(hcc), 2), float)
        coords[0::2] = hcc
        coords[1::2] = p1
        lines = shapely.linestrings(coords, indices=np.repeat(np.arange(len(hcc)), 2))

        # --- penalty 1: does the run cross somebody else's plot?
        t0 = time.time()
        ptree = STRtree(self.plots_all.geometry.values)
        li, qi = ptree.query(lines, predicate="intersects")
        own = self.plots_all.index.get_indexer(pl.index.values)   # plots is a slice of _all
        own_of_pair = own[pi]
        cross_plot = np.zeros(len(lines), dtype=bool)
        if len(li):
            bad = qi != own_of_pair[li]
            np.logical_or.at(cross_plot, li[bad], True)
        _log(f"    third-party plot crossings tested in {time.time() - t0:.0f} s; "
             f"{int(cross_plot.sum()):,} of {len(lines):,} candidate runs cross one")

        # --- penalty 2: does the run cross a tagged dual carriageway?
        cross_dual = self._dual_crossing(lines)

        # --- penalty 3: is the chamber standing on wadi ground?
        onwadi = ch.ON_WADI.values[ci].astype(bool)

        base = tert.copy()
        pen = (PEN_CROSS_PLOT_M * cross_plot + PEN_CROSS_DUAL_M * cross_dual
               + PEN_WADI_M * onwadi)
        self._n_ch_cand = len(ch)
        self._cand = dict(pi=pi, ci=ci, d=d, tert=tert, rank=rank, same_arc=same_arc,
                          base=base, pen=pen, hcc=hcc, chpt=p1,
                          cross_plot=cross_plot, cross_dual=cross_dual, onwadi=onwadi)

        # --- the three arms, same cost, different candidate sets
        arms = {}
        for name, mask in (("A nearest chamber only", rank == 0),
                           ("B nearest corridor only", same_arc),
                           ("C every carrier ranked", np.ones(len(pi), bool))):
            arms[name] = self._allocate(mask, congest=CONGEST_M)
        self.arms = arms
        self.alloc = arms["C every carrier ranked"]
        _log("    " + " | ".join(
            f"{k.split()[0]}: {v['q_conn']:,.0f} m3/d "
            f"({v['q_conn'] / self.plots.Q_AVG_M3D.sum() * 100:.1f} %), "
            f"{v['km']:.1f} km" for k, v in arms.items()))
        return self

    def _chamber_arcs(self) -> List[set]:
        """Every corridor each chamber sits on, by chamber ROW INDEX.  An interior or
        fan-out chamber is on one; a chamber at a graph node is on all of them."""
        pos = {u: k for k, u in enumerate(self.ch.NODE_UID.values)}
        out: List[set] = [set() for _ in range(len(self.ch))]
        for c, ids in self.chain.items():
            for u in ids:
                k = pos.get(u)
                if k is not None:
                    out[k].add(c)
        return out

    def _nearest_arc(self, pl) -> np.ndarray:
        import shapely
        from shapely import STRtree
        tree = STRtree(self.arcs.geometry.values)
        idx = tree.nearest(pl.geometry.values)
        return self.arcs.CID.astype(str).values[idx]

    def _dual_crossing(self, lines) -> np.ndarray:
        import shapely
        from shapely import STRtree
        try:
            d = self.gpd.read_file(ROAD_REC)
            d = d.set_crs(CRS_EPSG, allow_override=True)
            col = [c for c in d.columns if c.lower() == "dual"]
            if not col:
                raise KeyError("no 'dual' column")
            dd = d[pd.to_numeric(d[col[0]], errors="coerce").fillna(0) == 1]
            band = dd.geometry.buffer(DUAL_BAND_M)
        except Exception as e:                                     # noqa: BLE001
            self.notes.append(f"dual-carriageway crossing test COULD NOT RUN: {e}. "
                              "Its penalty is therefore absent from the ranking and the "
                              "count below is not a zero, it is a blank.")
            self.dual_ok = False
            return np.zeros(len(lines), dtype=bool)
        self.dual_ok = True
        tree = STRtree(band.values)
        li, _ = tree.query(lines, predicate="intersects")
        out = np.zeros(len(lines), dtype=bool)
        if len(li):
            out[np.unique(li)] = True
        return out

    def _allocate(self, mask: np.ndarray, congest: float) -> dict:
        """Greedy assignment on the declared cost.  The most CONSTRAINED plots pick first -
        a plot with one option loses nothing by waiting and everything by being crowded out.
        """
        c = self._cand
        pi, ci = c["pi"][mask], c["ci"][mask]
        cost0 = c["base"][mask] + c["pen"][mask]
        tert = c["tert"][mask]
        if len(pi) == 0:
            return {"pairs": np.zeros(0, int), "q_conn": 0.0, "km": 0.0,
                    "n_conn": 0, "chambers": 0, "by_plot": {}}
        nplot = len(self.plots)
        opts = np.bincount(pi, minlength=nplot)
        best = np.full(nplot, np.inf)
        np.minimum.at(best, pi, cost0)
        order_plots = np.lexsort((best, opts))
        by_plot: Dict[int, np.ndarray] = {}
        srt = np.lexsort((cost0, pi))
        pi_s, ci_s, cost_s, tert_s = pi[srt], ci[srt], cost0[srt], tert[srt]
        bounds = np.searchsorted(pi_s, np.arange(nplot + 1))
        load = np.zeros(self._n_ch_cand, dtype=int)
        chosen = np.full(nplot, -1, dtype=int)
        chosen_len = np.full(nplot, np.nan)
        for p in order_plots:
            lo, hi = bounds[p], bounds[p + 1]
            if hi <= lo:
                continue
            cc = ci_s[lo:hi]
            cst = cost_s[lo:hi] + congest * np.maximum(0, load[cc] - HCC_PER_RIDER + 1)
            k = int(np.argmin(cst))
            chosen[p] = cc[k]
            chosen_len[p] = tert_s[lo + k]
            load[cc[k]] += 1
        got = chosen >= 0
        q = float(self.plots.Q_AVG_M3D.values[got].sum())
        # what the chosen runs actually cost in wayleaves and crossings, per arm
        key = {}
        for k, (pp, cc2) in enumerate(zip(pi, ci)):
            key.setdefault((int(pp), int(cc2)), k)
        idx = [key[(p, int(chosen[p]))] for p in np.flatnonzero(got)]
        idx = np.array(idx, dtype=int)
        cp = c["cross_plot"][mask][idx] if len(idx) else np.zeros(0, bool)
        cd = c["cross_dual"][mask][idx] if len(idx) else np.zeros(0, bool)
        cw = c["onwadi"][mask][idx] if len(idx) else np.zeros(0, bool)
        return {"chosen": chosen, "chosen_len": chosen_len, "load": load,
                "q_conn": q, "km": float(np.nansum(chosen_len[got]) / 1000.0),
                "n_conn": int(got.sum()),
                "chambers": int((load > 0).sum()),
                "cross_plot": int(cp.sum()), "cross_dual": int(cd.sum()),
                "on_wadi": int(cw.sum()),
                "max_per_chamber": int(load.max()) if len(load) else 0}

    # ---------------------------------------------------------------- pruning
    def prune(self) -> "Chambers":
        """Drop every arc that neither COLLECTS a connection nor CONVEYS one from upstream.

        W10 shipped 117.3 km with no load-bearing plot within 60 m carrying under 1 m3/d -
        it neither collected nor conveyed.  This is the rule that makes that unpublishable.
        It never removes an arc a plot chose, so no load can be lost: `verify()` proves it.
        """
        ch = self.ch
        seg = self.seg
        chosen = self.alloc["chosen"]
        uid = ch.NODE_UID.values
        ds = dict(zip(seg.US_NODE.values, seg.DS_NODE.values))

        # A chosen chamber keeps its WHOLE PATH to the outfall.  Walking down and stopping
        # at the first already-kept chamber makes the whole pass O(segments), not O(paths).
        kept: set = set()
        for c in chosen[chosen >= 0]:
            u = uid[c]
            while u is not None and u not in kept:
                kept.add(u)
                u = ds.get(u)
        # a segment is kept exactly when its upstream chamber is - "keep" propagates down
        seg_keep = seg.US_NODE.isin(kept).values
        self.seg_all = seg
        self.seg = seg[seg_keep].reset_index(drop=True).copy()
        live = set(self.seg.US_NODE) | set(self.seg.DS_NODE)
        self.ch_all = ch
        self.ch = ch[ch.NODE_UID.isin(live)].reset_index(drop=True).copy()

        keepc = set(self.seg.ARC_CID.astype(str))
        a = self.arcs.assign(KEEP=self.arcs.CID.astype(str).isin(keepc).astype(int))
        a.loc[a.index[list(self.absorbed)], "KEEP"] = 0
        pruned = a[a.KEEP == 0]
        self.pruned_arcs = pruned
        self.arcs_kept = a[a.KEEP == 1].copy()
        _log(f"pruning: {len(pruned):,} arcs / {pruned.LEN_M.sum() / 1000:,.1f} km "
             f"neither collect nor convey "
             f"({pruned.LEN_M.sum() / self.arcs.LEN_M.sum() * 100:.1f} % of the corridors)")
        f = pruned[(pruned.ROLE == "head") & (pruned.LEN_M < FINGER_M)]
        _log(f"    of those, {len(f):,} are fingers under {FINGER_M:g} m "
             f"({f.LEN_M.sum() / 1000:,.1f} km)")
        _log(f"    kept {len(self.arcs_kept):,} arcs / "
             f"{self.arcs_kept.LEN_M.sum() / 1000:,.1f} km, {len(self.ch):,} chambers, "
             f"{len(self.seg):,} segments")
        return self

    def topology(self) -> "Chambers":
        """DS_NODE, N_IN, N_OUT and the chamber kind, WRITTEN DOWN (H16)."""
        s = self.seg
        ds = dict(zip(s.US_NODE, s.DS_NODE))
        nin = s.DS_NODE.value_counts()
        nout = s.US_NODE.value_counts()
        ch = self.ch
        ch["DS_NODE"] = ch.NODE_UID.map(ds).fillna("")
        ch["N_IN"] = ch.NODE_UID.map(nin).fillna(0).astype(int)
        ch["N_OUT"] = ch.NODE_UID.map(nout).fillna(0).astype(int)
        ch["IS_OUTFALL"] = (ch.N_OUT == 0).astype(int)
        kind = np.where(ch.N_OUT == 0, "outfall",
                        np.where(ch.N_IN >= 2, "junction",
                                 np.where(ch.N_IN == 0, "head", "chamber")))
        ch["NODE_KIND"] = kind
        # TRIGGER keeps WHY the chamber was minted; NODE_KIND says what it turned out to be
        bad = ch.N_OUT > 1
        if bad.any():
            raise RuntimeError(f"{int(bad.sum())} chambers have more than one outgoing "
                               f"segment - the forest invariant is broken at minting")
        _log("    " + ", ".join(f"{k} {int(v):,}"
                                for k, v in ch.NODE_KIND.value_counts().items()))
        return self

    def reallocate(self) -> "Chambers":
        """After pruning, re-point any connection whose chamber is gone.

        A chosen chamber keeps its whole path to the outfall, so almost none can be lost.
        The exception is a chosen chamber that is itself a TERMINAL with nothing kept above
        it: no segment then mentions it, and it falls out of the network.  Those plots are
        re-ranked over the SURVIVING chambers, and any that cannot reach one moves to the
        unserved schedule with a reason.  Nothing is dropped in silence.
        """
        live = set(self.ch.NODE_UID)
        uid = self.ch_all.NODE_UID.values
        chosen = self.alloc["chosen"]
        lost = [p for p, c in enumerate(chosen) if c >= 0 and uid[c] not in live]
        if not lost:
            self.notes.append("Pruning removed no connection: a chosen chamber keeps its "
                              "whole path to the outfall, and that is asserted, not "
                              "assumed.")
            self.n_relocated = 0
            return self
        c = self._cand
        live_idx = np.array([u in live for u in uid])
        srt = np.lexsort((c["base"] + c["pen"], c["pi"]))
        pi_s, ci_s = c["pi"][srt], c["ci"][srt]
        bounds = np.searchsorted(pi_s, np.arange(len(self.plots) + 1))
        moved = failed = 0
        for p in lost:
            lo, hi = bounds[p], bounds[p + 1]
            alt = [int(x) for x in ci_s[lo:hi] if live_idx[x]]
            if alt:
                chosen[p] = alt[0]
                moved += 1
            else:
                chosen[p] = -1
                failed += 1
        self.n_relocated = moved
        _log(f"    {len(lost)} connections lost a terminal chamber to the prune: "
             f"{moved} re-pointed to a surviving chamber, {failed} moved to unserved")
        self.notes.append(
            f"{len(lost)} plots had chosen a chamber that was a TERMINAL with nothing kept "
            f"above it, so no segment mentioned it and the prune removed it. {moved} were "
            f"re-ranked onto a surviving chamber and {failed} moved to the unserved "
            f"schedule. None was dropped in silence.")
        return self

    def orphans(self) -> "Chambers":
        """Components that end nowhere.  H15 allows several components - satellite works
        are legal - but never "a piece that drains nowhere"."""
        real = set(self.onodes.loc[self.onodes.KIND == "outfall", "NODE_ID"].astype(str))
        parent: Dict[str, str] = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in zip(self.seg.US_NODE.values, self.seg.DS_NODE.values):
            a, b = find(u), find(v)
            if a != b:
                parent[a] = b
        ch = self.ch
        root = np.array([find(u) for u in ch.NODE_UID.values])
        has_real = {}
        for r, o in zip(root, ch.ORIENT_ND.values):
            has_real[r] = has_real.get(r, False) or (str(o) in real)
        ch["ORPHAN"] = np.array([0 if has_real.get(r, False) else 1 for r in root])
        self.ch = ch
        seglen = self.seg.groupby(self.seg.US_NODE.map(dict(zip(ch.NODE_UID, root)))) \
            .LEN_M.sum()
        rows = []
        for r, ok in has_real.items():
            if ok:
                continue
            m = root == r
            rows.append({"ROOT": r, "chambers": int(m.sum()),
                         "km": round(float(seglen.get(r, 0.0)) / 1000, 2),
                         "load_m3d": round(float(ch.loc[m, "Q_LOC_M3D"].sum())
                                           if "Q_LOC_M3D" in ch else 0.0, 2)})
        self.t_orphan = pd.DataFrame(rows).sort_values("km", ascending=False) \
            if rows else pd.DataFrame(columns=["ROOT", "chambers", "km", "load_m3d"])
        n = int(ch.ORPHAN.sum())
        if n:
            _log(f"    {len(self.t_orphan):,} components with {n:,} chambers end at a low "
                 f"point with no path to the Main Pipe - stage 2's `island` corridors. "
                 f"H15: a piece that drains nowhere is never legal")
            self.notes.append(
                f"{len(self.t_orphan):,} components ({n:,} chambers, "
                f"{self.t_orphan.km.sum():,.1f} km) have NO outfall on the client's Main "
                f"Pipe. They are stage 2's `island` corridors, which it published with "
                f"'no path to the Main Pipe; direction provisional'. H15 allows several "
                f"components - a satellite works is legal - but never a piece that drains "
                f"nowhere. Each needs a connection or its own works: an engineer's "
                f"decision, and it is NOT resolved here.")
        return self

    # ---------------------------------------------------------------- the drainability bound
    def drain_bound(self) -> "Chambers":
        """A LEVEL-FREE bound, published INSTEAD of the drainability test.

        CAN_DRAIN asks whether the plot's outlet sits above the sewer invert where it joins.
        There is no designed invert at stage 4, and running that test against a seeded depth
        is what rejected 5,715 plots for nothing last time.  So it is NOT RUN, and this is
        published in its place:

          DRAIN_SHALLOW = 1 where the plot could drain into a sewer laid at the MINIMUM
          legal cover - the shallowest sewer the guideline permits, and therefore the
          hardest case:
              GRD_plot - HCC_DEPTH_MIN - TERT_SLOPE_MIN * L   >=   GRD_ch - (1.30 + OD)
          with HCC depth 1.2 m (G203-p19 3.4), the tertiary minimum 1 % (G203-p18 Tab 5),
          cover 1.30 m (G203-p33) and OD 200 mm (G203-p22 Tab 6 lateral row).

        A 0 does NOT mean the plot cannot be served.  It means the sewer must be laid deeper
        than its minimum there, which is stage 6's business.  A 1 is a guarantee; a 0 is a
        question.  Neither is CAN_DRAIN.
        """
        cn = self.conn
        if len(cn) == 0:
            return self
        need = (cn.GRD_PLOT.values - HCC_DEPTH_MIN
                - TERT_SLOPE_MIN * cn.L_TERT_M.values)
        have = cn.GRD_CH.values - (MIN_COVER_M + DN_MIN_LATERAL / 1000.0)
        cn["DRAIN_SHAL"] = (need >= have - 1e-9).astype(int)
        cn["DRAIN_MARG"] = np.round(need - have, 3)
        self.conn = cn
        n = int(cn.DRAIN_SHAL.sum())
        _log(f"    DRAIN_SHALLOW: {n:,} of {len(cn):,} connections "
             f"({n / len(cn) * 100:.1f} %) drain into a sewer laid at MINIMUM cover; "
             f"the rest need it deeper, which is stage 6's decision")
        return self

    # ---------------------------------------------------------------- assembly
    def assemble(self) -> "Chambers":
        """Build the published connection and unserved layers.  Every load-bearing plot
        appears in exactly one of them."""
        import shapely
        c = self._cand
        chosen = self.alloc["chosen"]
        uid = self.ch_all.NODE_UID.values
        grd = self.ch_all.GRD_M.values
        pl = self.plots

        # index the candidate rows so the chosen pair can be recovered with its geometry
        keymap: Dict[Tuple[int, int], int] = {}
        for k, (p, cc) in enumerate(zip(c["pi"], c["ci"])):
            kk = (int(p), int(cc))
            if kk not in keymap:
                keymap[kk] = k
        rows = []
        for p in range(len(pl)):
            cc = chosen[p]
            if cc < 0:
                continue
            k = keymap[(p, int(cc))]
            h = c["hcc"][k]
            q = c["chpt"][k]
            rows.append({
                "CONN_ID": f"K{p:06d}",
                "PLOT_ID": str(pl.PLOT_ID.values[p]),
                "OUT_NODE": uid[cc],
                "WHY": "assigned",
                "SYSTEM": "central",
                "CONN_TYPE": "rider",
                "Q_ADF_M3D": float(pl.Q_AVG_M3D.values[p]),
                "N_PROP": float(pl.N_PROP.values[p]),
                "L_TERT_M": float(c["tert"][k]),
                "LEN_M": float(c["tert"][k]),
                "D_BND_M": float(c["d"][k]),
                "RANK": int(c["rank"][k]),
                "XPLOT": int(c["cross_plot"][k]),
                "XDUAL": int(c["cross_dual"][k]),
                "CH_WADI": int(c["onwadi"][k]),
                "GRD_PLOT": float("nan"),
                "GRD_CH": float(grd[cc]),
                "HCC_X": float(h[0]), "HCC_Y": float(h[1]),
                "geometry": shapely.linestrings([[h[0], h[1]], [q[0], q[1]]]),
            })
        cn = pd.DataFrame(rows)
        if len(cn):
            hx = cn.HCC_X.values
            hy = cn.HCC_Y.values
            key = np.lexsort(((hx // 256).astype(np.int64), (hy // 256).astype(np.int64)))
            z = np.empty(len(hx), float)
            z[key] = self.tf.elevation(hx[key], hy[key], native=True)
            zg = self.tf.elevation(hx, hy)
            cn["GRD_PLOT"] = np.where(np.isfinite(z), z, zg)
            # G203-p18 Tab 5: 1-10 % on a rider/lateral. What the GROUND offers, reported.
            with np.errstate(divide="ignore", invalid="ignore"):
                cn["GND_SLOPE"] = np.where(cn.L_TERT_M > 0,
                                           (cn.GRD_PLOT - cn.GRD_CH) / cn.L_TERT_M * 100.0,
                                           np.nan)
        self.conn = cn

        # --- the unserved, each with a reason, none silent
        served = set(cn.PLOT_ID.astype(str)) if len(cn) else set()
        rest = pl[~pl.PLOT_ID.astype(str).isin(served)].copy()
        if len(rest):
            import shapely as sh
            from shapely import STRtree
            tree = STRtree(sh.points(self.ch_all.X.values, self.ch_all.Y.values))
            idx = tree.nearest(rest.geometry.values)
            dmin = sh.distance(rest.geometry.values,
                               sh.points(self.ch_all.X.values[idx],
                                         self.ch_all.Y.values[idx]))
            tert = np.maximum(0.0, dmin - HCC_OFFSET_M)
            why = np.where(tert <= 2 * TERT_MAX_M,
                           f"nearest chamber {'{:.0f}'.format(0)}",
                           "")
            why = [f"no chamber within {TERT_MAX_M:g} m: nearest is {t:.0f} m of tertiary; "
                   + ("a chained rider+lateral (2 x 45 m, G203-p17) would reach it, but "
                      "that needs a corridor which the drawing does not have"
                      if t <= 2 * TERT_MAX_M else
                      "beyond even a chained rider+lateral - this plot is not served by "
                      "the central network and belongs in the options appraisal")
                   for t in tert]
            self.unserved = pd.DataFrame({
                "PLOT_ID": rest.PLOT_ID.astype(str).values,
                "WHY": why,
                "SYSTEM": np.where(tert <= 2 * TERT_MAX_M, "central", "unserved"),
                "Q_ADF_M3D": rest.Q_AVG_M3D.values,
                "N_PROP": rest.N_PROP.values,
                "D_NEAR_M": np.round(dmin, 1),
                "L_TERT_M": np.round(tert, 1),
                "geometry": rest.geometry.representative_point().values,
            })
        else:
            self.unserved = pd.DataFrame(columns=["PLOT_ID", "WHY", "SYSTEM", "Q_ADF_M3D",
                                                  "N_PROP", "D_NEAR_M", "L_TERT_M",
                                                  "geometry"])
        _log(f"    {len(cn):,} connected / {len(self.unserved):,} not; "
             f"{cn.Q_ADF_M3D.sum() if len(cn) else 0:,.1f} of "
             f"{pl.Q_AVG_M3D.sum():,.1f} m3/d "
             f"({(cn.Q_ADF_M3D.sum() if len(cn) else 0) / pl.Q_AVG_M3D.sum() * 100:.1f} %)")
        return self

    def chamber_loads(self) -> "Chambers":
        """Connections per chamber, and the chamber type G203-p19 3.4 allows."""
        cn = self.conn
        n = cn.OUT_NODE.value_counts() if len(cn) else pd.Series(dtype=int)
        q = cn.groupby("OUT_NODE").Q_ADF_M3D.sum() if len(cn) else pd.Series(dtype=float)
        p = cn.groupby("OUT_NODE").N_PROP.sum() if len(cn) else pd.Series(dtype=float)
        ch = self.ch
        ch["N_CONN"] = ch.NODE_UID.map(n).fillna(0).astype(int)
        ch["Q_LOC_M3D"] = ch.NODE_UID.map(q).fillna(0.0).round(3)
        ch["N_PROP"] = ch.NODE_UID.map(p).fillna(0.0).round(2)
        ch["OVER_HCC3"] = (ch.N_CONN > HCC_PER_RIDER).astype(int)
        self.ch = ch
        return self

    # ---------------------------------------------------------------- tables
    def tables(self) -> "Chambers":
        ch, seg, cn = self.ch, self.seg, self.conn
        tot_q = float(self.plots.Q_AVG_M3D.sum())

        # triggers, each with the clause it comes from
        src = {
            "junction": "G203-p29 4.4 'Junction of two or more pipes'",
            "head": "G203-p30 'End of each lateral sewer'",
            "outfall": "G203-p29 4.4 (terminal); the only chamber with no DS_NODE",
            "spacing": "G203-p29 4.4 'At regular spacing on straight pipeline based on "
                       "maintenance equipment', G203-p30 Table 12 the ceiling",
            "bend": "PROJECT, calibrated: a pipe is laid straight between chambers "
                    "(98.1 % of NAMA's built pipes are a straight 2-point line). "
                    "G203 lists NO bend trigger",
            "chamber": "a stage-2 graph node that is neither a junction nor a head - two "
                       "corridors meeting end to end",
            "fanout": "PROJECT (criteria.FANOUT_OFFSET_M, user rule 2026-08-18; philosophy "
                      "sec 4's 10 m clearance): a run leaving a chamber that already has an "
                      "outlet starts 10 m away. It is what keeps 'exactly one pipe leaves a "
                      "junction' true where stage 2 hands over more than one corridor out "
                      "of one node",
        }
        t = (ch.groupby("TRIGGER").size().rename("N").reset_index()
             .sort_values("N", ascending=False))
        t["PER_KM"] = (t.N / (seg.LEN_M.sum() / 1000.0)).round(2)
        t["SOURCE"] = t.TRIGGER.map(src).fillna("")
        self.t_trigger = t

        # the two triggers that are satisfied by construction rather than placed
        self.t_deferred = pd.DataFrame([
            {"TRIGGER": "change in pipe diameter",
             "SOURCE": "G203-p29 4.4",
             "STATUS": "SATISFIED BY CONSTRUCTION",
             "ARGUMENT": "flow only enters at a chamber (G203-p19 3.6 'Connection to the "
                         "Main Sewer will be done at a manhole ... There must be no "
                         "penetrating connection'), and a reach here IS chamber to "
                         "chamber, so a diameter cannot change between two chambers. "
                         "Re-checked when the diameters exist."},
            {"TRIGGER": "change in pipe gradient",
             "SOURCE": "G203-p29 4.4",
             "STATUS": f"SATISFIED BY CONSTRUCTION at {self.split_m:g} m spacing, to the "
                       f"limit of what the terrain resolves",
             "ARGUMENT": f"a DESIGNED gradient change lands on a chamber by definition "
                         f"(G203-p29: 'Uniform slopes must be maintained between successive "
                         f"manholes'). A GROUND grade break below "
                         f"{self.grade_floor:.1f} mm/m cannot be seen at all: sigma_dz = "
                         f"{self.sigma_dz:.4f} m over a {self.split_m:g} m window gives a "
                         f"3-sigma detection floor of that size. Breaks coarser than it are "
                         f"longer than the spacing."},
            {"TRIGGER": "drop / backdrop chamber",
             "SOURCE": "G203-p30 (>0.60 m backdrop, >2.0 m vortex)",
             "STATUS": "CANNOT RUN AT THIS STAGE",
             "ARGUMENT": "a drop is a difference of INVERTS and there are no inverts until "
                         "stage 6. Reported as a blank, not as a zero."},
        ])

        # chambers closer than the minimum clearance - what was found and what was done.
        # This table is now the RECORD of the contraction, not a list of survivors: every
        # pair is here with what happened to it, so removing a chamber is never silent.
        import shapely as _sh
        from shapely import STRtree as _T
        rows_close = [{
            "A": a, "B": b, "GAP_M": g, "JOINED_BY_A_PIPE": 1,
            "STATUS": "CONTRACTED into one structure (criteria.MH_SNAP_M): the two ends of "
                      "a corridor shorter than the clearance itself",
        } for a, b, g in zip(self.contracted.A, self.contracted.B, self.contracted.GAP_M)] \
            if len(self.contracted) else []
        _p = _sh.points(ch.X.values, ch.Y.values)
        _a, _b = _T(_p).query(_p, predicate="dwithin", distance=MH_MIN_CLEAR_M - 1e-6)
        _m = _a < _b
        rows_close += [{
            "A": ch.NODE_UID.values[i], "B": ch.NODE_UID.values[j],
            "GAP_M": round(float(_sh.distance(_p[i], _p[j])), 3),
            "JOINED_BY_A_PIPE": 0,
            "STATUS": "REMAINS - no pipe joins these two, so contracting them would fuse "
                      "two independent branches. A layout decision, NOT resolved here",
        } for i, j in zip(_a[_m], _b[_m])]
        self.t_close = pd.DataFrame(
            rows_close, columns=["A", "B", "GAP_M", "JOINED_BY_A_PIPE", "STATUS"])
        if len(self.t_close):
            self.t_close = self.t_close.sort_values("GAP_M")
        # measured on the PUBLISHED chambers, which is what `verify()` re-reads. The
        # pre-prune scan in `contract_pairs` is a build-time diagnostic, not the number.
        n_remaining = int(_m.sum())
        self.residual_pairs = n_remaining
        # and the SAME discipline applied to the chambers this stage PUT BACK. `n_resplit`
        # is counted before the prune; the prune can delete the very reach that was
        # re-divided, and on the first run with this code it did - the manifest said "1
        # chamber put back" and there was not one in the published layer to find. Publish
        # both numbers, never just the build-time one.
        _live_uid = set(ch.NODE_UID.astype(str))
        self.n_resplit_live = int(sum(1 for u in getattr(self, "resplit_uids", [])
                                      if u in _live_uid))

        # inlet angle bands - a 0 deg inlet and an 89 deg inlet are different problems.
        # The band edge is INLET_MIN_DEG itself, so the non-compliant bands sum EXACTLY to
        # INLET_FLAG; an edge at 89.99 put 29 breaches in the compliant row.
        fin = ch[np.isfinite(ch.INLET_DEG)]
        bands = [(0, 30), (30, 60), (60, INLET_MIN_DEG), (INLET_MIN_DEG, 120),
                 (120, 150), (150, 180.01)]
        self.t_inlet = pd.DataFrame([{
            "INLET_DEG": f"{lo:g} to {hi:g}",
            "chambers": int(((fin.INLET_DEG >= lo) & (fin.INLET_DEG < hi)).sum()),
            "COMPLIANT": "no - swept channel required" if hi <= 90 else "yes",
        } for lo, hi in bands])
        self.t_inlet["pct"] = (self.t_inlet.chambers / max(len(fin), 1) * 100).round(2)

        # ---- the inlet angles SPLIT BY CAUSE, because one rule does not fix two defects.
        # The as-built study (N10) found the built network's breaches split into 240 BRANCH
        # inlets clustered just under 90 deg - which aiming at 95 deg fixes - and 122
        # PASS-THROUGH HAIRPINS at chambers with a single inflow and no branch at all, which
        # the 95 deg target does not touch.  Ours is split the same way before anything is
        # decided about it.
        sb = self._sub90
        n_pass = max(self._n_inlets - self._n_in_branch, 0)
        rows_split = []
        for lab, mask, denom, ab_pct in (
                ("BRANCH - the chamber has two or more inflows",
                 sb.N_IN >= 2 if len(sb) else pd.Series(dtype=bool),
                 self._n_in_branch, AB_INLET["junction_pct"]),
                ("PASS-THROUGH HAIRPIN - one inflow, no branch at all",
                 sb.N_IN == 1 if len(sb) else pd.Series(dtype=bool),
                 n_pass, AB_INLET["passthrough_pct"])):
            v = sb.loc[mask, "DEG"] if len(sb) else pd.Series(dtype=float)
            rows_split.append({
                "CLASS": lab,
                "inlets": len(v),
                "of_that_kind": denom,
                "pct": round(len(v) / denom * 100, 2) if denom else 0.0,
                "NAMA_pct": ab_pct,
                "median_deg": round(float(v.median()), 2) if len(v) else np.nan,
                "worst_deg": round(float(v.min()), 2) if len(v) else np.nan,
                "within_5_deg": int((v >= INLET_MIN_DEG - 5.0).sum()) if len(v) else 0,
                "within_5_pct": round(float((v >= INLET_MIN_DEG - 5.0).mean() * 100), 1)
                if len(v) else 0.0,
            })
        n_same_arc = int(sb.SAME_ARC.sum()) if len(sb) else 0
        vs = sb.loc[sb.SAME_ARC == 1, "DEG"] if len(sb) else pd.Series(dtype=float)
        # the denominator of a row labelled "of the above" is the above, not every inlet in
        # the network. It read 0.30 % against 56,667 where it means 5.70 % of the breaches.
        rows_split.append({
            "CLASS": "of the above, ONE corridor turning back on itself at a chamber",
            "inlets": n_same_arc, "of_that_kind": len(sb),
            "pct": round(n_same_arc / max(len(sb), 1) * 100, 2),
            "NAMA_pct": np.nan,
            "median_deg": round(float(vs.median()), 2) if len(vs) else np.nan,
            "worst_deg": round(float(vs.min()), 2) if len(vs) else np.nan,
            "within_5_deg": int((vs >= INLET_MIN_DEG - 5.0).sum()) if len(vs) else 0,
            "within_5_pct": round(float((vs >= INLET_MIN_DEG - 5.0).mean() * 100), 1)
            if len(vs) else 0.0})
        # MEASURED, not asserted. A chamber standing on a stage-2 graph node is where two
        # corridors meet and cannot be moved at all; one that is not can only slide ALONG
        # its own corridor, which keeps the same bend. So a breach is fixable here only if
        # the chamber is NOT a graph node AND its inlet arrives on a different corridor
        # from the one its outlet leaves on - and the count of those is taken from the data
        # rather than written down as a nought.
        mv = ((sb.AT_NODE == 0) & (sb.SAME_ARC == 0)) if len(sb) else pd.Series(dtype=bool)
        vm = sb.loc[mv, "DEG"] if len(sb) else pd.Series(dtype=float)
        rows_split.append({
            "CLASS": "of the above, fixable by MOVING A CHAMBER at this stage",
            "inlets": int(mv.sum()) if len(sb) else 0, "of_that_kind": len(sb),
            "pct": round(float(mv.mean()) * 100, 2) if len(sb) else 0.0,
            "NAMA_pct": np.nan,
            "median_deg": round(float(vm.median()), 2) if len(vm) else np.nan,
            "worst_deg": round(float(vm.min()), 2) if len(vm) else np.nan,
            "within_5_deg": int((vm >= INLET_MIN_DEG - 5.0).sum()) if len(vm) else 0,
            "within_5_pct": round(float((vm >= INLET_MIN_DEG - 5.0).mean() * 100), 1)
            if len(vm) else 0.0})
        # and the count that says how much of the verdict is the BASIS rather than the
        # geometry. It is not a class of breach; it is the uncertainty on the classes above.
        rows_split.append({
            "CLASS": f"NOT a class - chambers whose verdict CHANGES if the direction of "
                     f"flow is read from the pipe's local direction "
                     f"({'/'.join(f'{m:g}' for m in BEARING_LEG_SWEEP_M)} m) instead of "
                     f"the chord; {self.n_basis_amb_unpriced} of them are published as "
                     f"COMPLIANT and so carry no priced swept channel",
            "inlets": self.n_basis_amb, "of_that_kind": len(fin),
            "pct": round(self.n_basis_amb / max(len(fin), 1) * 100, 3),
            "NAMA_pct": np.nan, "median_deg": np.nan, "worst_deg": np.nan,
            "within_5_deg": 0, "within_5_pct": 0.0})
        self.t_inlet_split = pd.DataFrame(rows_split)
        self.n_same_arc = n_same_arc
        self.n_movable = int(mv.sum()) if len(sb) else 0

        # spacing against Table 12 and against the built network
        km = seg.LEN_M.sum() / 1000.0
        self.t_spacing = pd.DataFrame([{
            "WHAT": "this design", "median_m": round(float(seg.LEN_M.median()), 2),
            "mean_m": round(float(seg.LEN_M.mean()), 2),
            "p90_m": round(float(seg.LEN_M.quantile(0.90)), 2),
            "max_m": round(float(seg.LEN_M.max()), 2),
            "per_km": round(len(ch) / km, 2),
            "over_tab12_pct": round(float((seg.LEN_M > TAB12_TIGHTEST_M).mean() * 100), 3),
        }, {
            "WHAT": "NAMA built", "median_m": round(self.m_spacing["mh_spacing_median_m"], 2),
            "mean_m": round(self.m_spacing["mh_spacing_mean_m"], 2),
            "p90_m": round(self.m_spacing["mh_spacing_p90_m"], 2),
            "max_m": round(self.m_spacing["mh_spacing_max_m"], 2),
            "per_km": round(self.m_spacing["mh_per_km"], 2),
            "over_tab12_pct": round(self.m_spacing["spacing_over_tab12_pct"], 3),
        }, {
            "WHAT": "G203-p30 Tab 12 ceiling (DN200-315)", "median_m": np.nan,
            "mean_m": np.nan, "p90_m": np.nan, "max_m": TAB12_TIGHTEST_M,
            "per_km": np.nan, "over_tab12_pct": 0.0,
        }])

        # the A/B on the search
        rows = []
        for k, v in self.arms.items():
            rows.append({"SEARCH": k, "connected_n": v["n_conn"],
                         "connected_pct": round(v["n_conn"] / len(self.plots) * 100, 2),
                         "load_m3d": round(v["q_conn"], 1),
                         "load_pct": round(v["q_conn"] / tot_q * 100, 2),
                         "tertiary_km": round(v["km"], 1),
                         "chambers_used": v["chambers"],
                         "crosses_a_plot": v["cross_plot"],
                         "crosses_a_dual": v["cross_dual"],
                         "chamber_on_wadi": v["on_wadi"],
                         "max_conn_per_chamber": v["max_per_chamber"]})
        ab = pd.DataFrame(rows)
        base = ab.iloc[0]
        ab["load_pts_vs_A"] = (ab.load_pct - base.load_pct).round(2)
        ab["km_vs_A"] = (ab.tertiary_km - base.tertiary_km).round(1)
        ab["wayleaves_vs_A"] = (ab.crosses_a_plot - base.crosses_a_plot)
        self.t_search = ab

        # congestion
        cc = ch[ch.N_CONN > 0].N_CONN
        self.t_congest = pd.DataFrame([{
            "connections_per_chamber": f"{lo}-{hi}" if hi else f"{lo}+",
            "chambers": int(((cc >= lo) & (cc <= (hi or 10 ** 9))).sum()),
        } for lo, hi in ((1, 1), (2, 3), (4, 6), (7, 10), (11, None))])
        self.t_congest["pct"] = (self.t_congest.chambers /
                                 max(len(cc), 1) * 100).round(2)

        # prune
        p = self.pruned_arcs
        wholly = float(p.LEN_M.sum() / 1000)
        all_seg = float(self.seg_all.LEN_M.sum() / 1000)
        pub = float(seg.LEN_M.sum() / 1000)
        corr = float(self.arcs.LEN_M.sum() / 1000)
        self.t_prune = pd.DataFrame([
            {"WHAT": "corridors handed over by stage 2", "arcs": len(self.arcs),
             "km": round(corr, 1)},
            {"WHAT": "  less the 10 m fan-out at a chamber that already has an outlet",
             "arcs": int(np.nansum(self.s_start > 0)), "km": -round(corr - all_seg, 1)},
            {"WHAT": "  less arcs that neither collect nor convey, WHOLLY pruned",
             "arcs": len(p), "km": -round(wholly, 1)},
            {"WHAT": "  less the upper part of arcs pruned only in PART",
             "arcs": np.nan, "km": -round(all_seg - wholly - pub, 1)},
            {"WHAT": "= published", "arcs": len(self.arcs_kept), "km": round(pub, 1)},
            {"WHAT": "   memo: pruned fingers under %g m (philosophy sec 4)" % FINGER_M,
             "arcs": int(((p.ROLE == "head") & (p.LEN_M < FINGER_M)).sum()),
             "km": round(float(p.loc[(p.ROLE == "head") &
                                     (p.LEN_M < FINGER_M), "LEN_M"].sum() / 1000), 1)},
            {"WHAT": "   memo: pruned arcs carrying a chamber on wadi ground",
             "arcs": int(self._pruned_wadi_arcs()), "km": np.nan},
        ])

        # compliance, recomputed here and again in verify()
        n_out = int((ch.N_OUT == 0).sum())
        self.t_compliance = pd.DataFrame([
            {"CHECK": "H12 chamber spacing within G203-p30 Table 12 (DN200-315 band)",
             "SOURCE": "G203-p30 Tab 12",
             "RESULT": f"{int((seg.LEN_M > TAB12_TIGHTEST_M).sum())} of {len(seg):,} "
                       f"segments over {TAB12_TIGHTEST_M:g} m",
             "PASS": int((seg.LEN_M > TAB12_TIGHTEST_M).sum() == 0)},
            {"CHECK": "chamber spacing within the shipped split length",
             "SOURCE": f"PROJECT, calibrated to the built median",
             "RESULT": f"{int((seg.LEN_M > self.split_m + 0.01).sum())} over "
                       f"{self.split_m:g} m",
             "PASS": int((seg.LEN_M > self.split_m + 0.01).sum() == 0)},
            {"CHECK": "H10 inlet angle at least 90 deg",
             "SOURCE": "G203-p30",
             "RESULT": f"{int(ch.INLET_FLAG.sum()):,} chambers on "
                       f"{len(self._sub90):,} of {self._n_inlets:,} inlets below 90 deg; "
                       f"worst {np.nanmin(ch.INLET_DEG.values):.2f} deg. Split: "
                       f"{int((self._sub90.N_IN >= 2).sum()) if len(self._sub90) else 0} "
                       f"branch inlets, "
                       f"{int((self._sub90.N_IN == 1).sum()) if len(self._sub90) else 0} "
                       f"pass-through hairpins, {self.n_same_arc} one corridor turning "
                       f"back on itself. {self.n_movable} are fixable by moving a chamber "
                       f"(MEASURED: a breach at a stage-2 graph node cannot be moved, and "
                       f"sliding a chamber along its own corridor keeps the same bend). "
                       f"Each is flagged SWEPT_CH and priced as a chamber detail; see "
                       f"`inlet_split`. CAVEAT, and it is not small: {self.n_basis_amb} "
                       f"chambers change side of this rule depending on whether the "
                       f"direction of flow is read from the reach's chord (published) or "
                       f"from the pipe's local direction, and "
                       f"{self.n_basis_amb_unpriced} of those are published as compliant "
                       f"and carry no priced swept channel",
             "PASS": int(ch.INLET_FLAG.sum() == 0)},
            {"CHECK": "a pipe is laid straight between chambers "
                      "(the rule this stage's bend trigger AND its inlet angle both rest on)",
             "SOURCE": "PROJECT STRAIGHT_TOL_M, calibrated: 99.36 % of NAMA's built pipes "
                       "lie inside 0.5 m of their own chord",
             "RESULT": f"{self.n_bent} of {len(seg):,} published reaches depart from their "
                       f"own chord by more than {STRAIGHT_TOL_M:g} m"
                       + (f", worst {self.t_bent.OFFSET_M.max():.2f} m on a "
                          f"{self.t_bent.iloc[0].LEN_M:.1f} m reach" if self.n_bent else "")
                       + f". A bend with no chamber at it. The stage asserted this and "
                         f"never measured it. TWO CAUSES, both named: `split_positions` "
                         f"drops a bend cut that lands within the {MH_MIN_CLEAR_M:g} m "
                         f"minimum clearance of a neighbour, and `contract_pairs` "
                         f"re-splits an absorbed reach for LENGTH but not for straightness. "
                         f"NOT resolved here - chambering these bends would put two "
                         f"chambers inside the clearance, so the two project rules conflict "
                         f"on this geometry and the choice is the engineer's",
             "PASS": int(self.n_bent == 0)},
            {"CHECK": "no two chambers inside the 3 m minimum clearance",
             "SOURCE": "criteria.MH_SNAP_M (PROJECT - no minimum chamber spacing exists in "
                       "G201/G202/G203)",
             "RESULT": f"{self.n_contracted} chamber(s) were inside the clearance and were "
                       f"CONTRACTED into the structure they touch - every one of them at "
                       f"the two ends of a corridor shorter than the clearance itself. "
                       f"{n_remaining} pair(s) remain, which would need two branches fused "
                       f"and is a layout decision",
             "PASS": int(n_remaining == 0)},
            {"CHECK": "H1 no chamber on wadi ground",
             "SOURCE": "G203-p30 4.4.1 i.a; the CLASS test is a project assumption",
             "RESULT": f"{int(ch.ON_WADI.sum()):,} chambers on hazard class 4/5/6 of the "
                       f"50-yr grid",
             "PASS": int(ch.ON_WADI.sum() == 0)},
            {"CHECK": "tertiary run within 45 m",
             "SOURCE": "G203-p22 Tab 6 lateral row + p17 3.2, taken on both",
             "RESULT": f"{int((cn.L_TERT_M > TERT_MAX_M + 1e-6).sum()) if len(cn) else 0} "
                       f"of {len(cn):,} over {TERT_MAX_M:g} m",
             "PASS": int(len(cn) == 0 or (cn.L_TERT_M > TERT_MAX_M + 1e-6).sum() == 0)},
            {"CHECK": "H15 every component ends at exactly one outfall",
             "SOURCE": "project rule / philosophy H15",
             "RESULT": self._component_check(),
             "PASS": int(self._component_check().startswith("OK"))},
            {"CHECK": "H16 topology written down (US_NODE / DS_NODE on every segment)",
             "SOURCE": "project rule / philosophy H16",
             "RESULT": f"{len(seg):,} segments, 0 inferred from geometry",
             "PASS": 1},
            {"CHECK": "zero silent drops - every load-bearing plot accounted for",
             "SOURCE": "project doctrine",
             "RESULT": f"{len(cn):,} connected + {len(self.unserved):,} named = "
                       f"{len(cn) + len(self.unserved):,} of {len(self.plots):,}",
             "PASS": int(len(cn) + len(self.unserved) == len(self.plots))},
            {"CHECK": "CAN_DRAIN - does the plot outlet sit above the sewer invert",
             "SOURCE": "contract.CONNECTIONS.CAN_DRAIN",
             "RESULT": "CANNOT RUN - no designed invert exists at stage 4. NOT run against "
                       "a seeded depth. DRAIN_SHALLOW published instead",
             "PASS": -1},
        ])
        self.t_compliance["PASS"] = self.t_compliance.PASS.map(
            {1: "pass", 0: "FAIL", -1: "cannot run"})
        self.n_outfalls = n_out
        return self

    def _pruned_wadi_arcs(self) -> int:
        w = set(self.ch_all.loc[self.ch_all.ON_WADI == 1, "ARC_CID"].astype(str))
        w.discard("")
        return int(self.pruned_arcs.CID.astype(str).isin(w).sum())

    def _component_check(self) -> str:
        parent: Dict[str, str] = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in zip(self.seg.US_NODE.values, self.seg.DS_NODE.values):
            a, b = find(u), find(v)
            if a != b:
                parent[a] = b
        comp: Dict[str, int] = {}
        for u in self.ch.NODE_UID.values:
            comp[find(u)] = comp.get(find(u), 0) + 1
        outs = {}
        for u in self.ch.loc[self.ch.N_OUT == 0, "NODE_UID"].values:
            r = find(u)
            outs[r] = outs.get(r, 0) + 1
        bad = [r for r in comp if outs.get(r, 0) != 1]
        if not bad:
            return f"OK - {len(comp):,} components, exactly one outfall each"
        return f"{len(bad):,} of {len(comp):,} components do not have exactly one outfall"

    # ---------------------------------------------------------------- sweeps
    def sweep_spacing(self) -> pd.DataFrame:
        """The single biggest quantity decision in the stage, priced in chambers."""
        import shapely
        rows = []
        km = self.arcs.LEN_M.sum() / 1000.0
        nnodes = len(self.node_uid)
        cache = []
        for i, g in enumerate(self.arcs.geometry.values):
            xy = shapely.get_coordinates(g)
            d = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xy[:, 0]),
                                                          np.diff(xy[:, 1])))])
            cache.append((d, xy))
        for s in SPACING_SWEEP_M:
            n = 0
            worst = 0.0
            for d, xy in cache:
                pos = split_positions(d, xy, s, STRAIGHT_TOL_M)
                n += len(pos) - 2
                if len(pos) > 1:
                    worst = max(worst, float(np.max(np.diff(pos))))
            rows.append({"SPLIT_M": s, "chambers": n + nnodes,
                         "per_km": round((n + nnodes) / km, 2),
                         "max_spacing_m": round(worst, 1),
                         "over_tab12": int(worst > TAB12_TIGHTEST_M + 1e-6),
                         "vs_built_per_km": round((n + nnodes) / km
                                                  - self.m_spacing["mh_per_km"], 2)})
        return pd.DataFrame(rows)

    def sweep_congestion(self) -> pd.DataFrame:
        rows = []
        allm = np.ones(len(self._cand["pi"]), bool)
        for g in (0.0, 5.0, 15.0, 30.0, 60.0):
            v = self._allocate(allm, congest=g)
            rows.append({"CONGEST_M": g, "connected_n": v["n_conn"],
                         "load_m3d": round(v["q_conn"], 1),
                         "tertiary_km": round(v["km"], 1),
                         "chambers_used": v["chambers"],
                         "crosses_a_plot": v["cross_plot"],
                         "max_per_chamber": v["max_per_chamber"],
                         "SHIPPED": int(abs(g - CONGEST_M) < 1e-9)})
        return pd.DataFrame(rows)

    # ---------------------------------------------------------------- readiness
    def readiness(self) -> pd.DataFrame:
        """Which CONTRACT fields this stage can fill, and which wait on which stage.

        Philosophy sec 8: a check that cannot run is a failure, not a blank.  The same
        applies to a field: an unfilled one is named here rather than left to be noticed.
        """
        have = {
            "nodes": set(self.ch.columns) | {"NODE_UID", "X", "Y", "GRD_M", "NODE_KIND",
                                             "DS_NODE", "N_IN", "N_OUT", "IS_OUTFALL",
                                             "INLET_DEG", "INLET_FLAG"},
            "reaches": set(self.seg.columns),
            "connections": set(self.conn.columns) | {"CONN_ID", "PLOT_ID", "OUT_NODE",
                                                     "WHY", "SYSTEM", "Q_ADF_M3D",
                                                     "N_PROP", "LEN_M"},
        }
        waits = {
            "INV_M": "s6 levels", "DEPTH_M": "s6 levels", "COVER_M": "s6 levels",
            "COVER_US": "s6 levels", "COVER_DN": "s6 levels", "INV_UP": "s6 levels",
            "INV_DN": "s6 levels", "US_DEPTH": "s6 levels", "DS_DEPTH": "s6 levels",
            "DROP_M": "s6 levels", "DROP_TYPE": "s6 levels", "VORTEX": "s6 levels",
            "PAST_CAP": "s6 levels", "CAP_EXIT": "s6 levels", "CAP_LEN_M": "s6 levels",
            "DN": "s6 sizing", "MATERIAL": "s6 sizing", "SIZED_BY": "s6 sizing",
            "SLOPE_LAID": "s6 sizing", "SLOPE_MIN": "s6 sizing", "GRAD_BY": "s6 sizing",
            "CLEAN_BY": "s6 sizing", "V_PK_MS": "s6 sizing", "DOD_PK": "s6 sizing",
            "RET_MIN": "s6 sizing", "CONSTR": "s6 sizing",
            "Q_ADF_M3D": "s5 flows", "Q_PK_LS": "s5 flows", "QADF_M3D": "s5 flows",
            "QINF_LS": "s5 flows", "PF": "s5 flows", "PF_METH": "s5 flows",
            "QPK_LS": "s5 flows",
            "TIER": "s3 hierarchy - NOT BUILT in W12", "PACKAGE": "s8 packages",
            "PHASE": "s8 packages", "NODE_REF": "s8 packages (needs the tier and package)",
            "TIE_TYPE": "s6 (existing-network tie-in)",
            "CAN_DRAIN": "s6 levels - REFUSED here rather than seeded",
            "CROSS_ID": "a crossings register, not built in this stage",
            "MH_DIA": "detail design (contractor's number)", "MH_MAT": "detail design",
            "TAU_PA": "carried on the reach at sizing",
        }
        rows = []
        for lname in ("nodes", "reaches", "connections"):
            spec = CT._spec(lname)
            for f in spec.fields:
                filled = f.name in have[lname]
                rows.append({"LAYER": lname, "FIELD": f.name,
                             "STATUS": "filled" if filled else "deferred",
                             "WAITS_ON": "" if filled else waits.get(f.name, "a later stage"),
                             "AUDIT": ",".join(f.checks)})
        df = pd.DataFrame(rows)
        n = int((df.STATUS == "filled").sum())
        _log(f"    contract readiness: {n} of {len(df)} fields filled; "
             f"{len(df) - n} named as deferred")
        return df

    def assumptions(self) -> pd.DataFrame:
        b = self.built_straight
        rows = [
            ("MH_SPLIT_M", self.split_m, "m",
             f"MEASURED. The built network's median chamber spacing "
             f"({self.m_spacing['mh_spacing_median_m']:.2f} m) rounded to "
             f"{C.MH_ROUND_STEP:g} m. G203-p29 4.4 hands regular spacing to 'maintenance "
             f"equipment' and the operator's own 3,265 built pipes are the record of what "
             f"that reaches - none of them exceeds Table 12's 100 m and their longest is "
             f"{self.m_spacing['mh_spacing_max_m']:.2f} m."),
            ("STRAIGHT_TOL_M", STRAIGHT_TOL_M, "m",
             f"PROJECT, CALIBRATED. {b['two_point_pct']:.1f} % of built pipes are a straight "
             f"2-point line; the polyline departs from its chord by a median "
             f"{b['sagitta_median_m']:.3f} m and p99 {b['sagitta_p99_m']:.3f} m, and "
             f"{b['within_0p5m_pct']:.2f} % are inside 0.5 m. Replaces an invented bend "
             f"angle with the physical rule a straight pipe obeys."),
            ("TERT_MAX_M", TERT_MAX_M, "m",
             "G203-p22 Table 6 prints 'Maximum Length 45 m' on the LATERAL SEWER ROW ONLY "
             "(read from the PDF 2026-09-03). G203-p17 3.2 writes 'Rider Sewers and Lateral "
             "Sewers (maximum Length 45 m)', attaching it to both. Conservative reading "
             "taken: 45 m on the whole tertiary run. PROJECT."),
            ("HCC_OFFSET_M", HCC_OFFSET_M, "m", "G203-p17 3.2, verbatim."),
            ("PEN_CROSS_PLOT_M", PEN_CROSS_PLOT_M, "m",
             "PROJECT. One full legal tertiary run, so a wayleave is always worth avoiding "
             "and never worth dropping a plot for."),
            ("PEN_CROSS_DUAL_M", PEN_CROSS_DUAL_M, "m",
             "PROJECT. Same price. Crossing is legal (philosophy H1a); running ALONG is not "
             "(project rule 7)."),
            ("PEN_WADI_M", PEN_WADI_M, "m",
             "PROJECT. A chamber on wadi ground is prohibited (G203-p30 4.4.1 i.a). A "
             "penalty and not a veto, because a veto drops load silently."),
            ("CONGEST_M", CONGEST_M, "m/connection",
             f"PROJECT. Charged beyond the free {HCC_PER_RIDER} of G203-p17 3.2 ('usually "
             f"up to 3'). A third of a legal run. Swept - see congestion_sweep."),
            ("CAND_TOPK", CAND_TOPK, "-",
             "PROJECT. How many candidates per plot carry the crossing tests. The cheap "
             "ones are always in, because the ranking is by bare length first."),
            ("DUAL_BAND_M", DUAL_BAND_M, "m",
             "PROJECT, matching stage 1's own band half-width, whose `dual_band` table "
             "publishes the exposure at eight widths."),
            ("FINGER_M", FINGER_M, "m",
             "PROJECT (philosophy sec 4, ours on cost grounds). REPORTED ONLY - the prune "
             "rule is 'neither collects nor conveys' and needs no length threshold."),
            ("GRADE_BREAK_FLOOR", round(self.grade_floor, 1), "mm/m",
             f"DERIVED. 3 * sqrt(2) * sigma_dz / window, sigma_dz = {self.sigma_dz:.4f} m "
             f"(terrain manifest, the DIFFERENTIAL error) over the {self.split_m:g} m "
             f"spacing. Below this a ground grade break is indistinguishable from DEM "
             f"noise, which is why the gradient trigger is not fired from the terrain."),
            ("HAZARD_WADI_CLASSES", str(tuple(C.HAZARD_WADI_CLASSES)), "-",
             "PROJECT ASSUMPTION. AR&R flood-hazard classes 4/5/6 of the 50-yr grid stand "
             "in for G203's 'areas subject to washout', which is a SCOUR criterion. "
             "No-data is read as DRY HIGH GROUND (engineer, 2026-09-03)."),
            ("MH_ROUND_STEP", C.MH_ROUND_STEP, "m",
             "NOT APPLIED. A straight piece is divided into EQUAL parts instead; rounding "
             "leaves a stub chamber a few metres from its neighbour. Declared departure."),
            ("MH_SNAP_M contraction", MH_MIN_CLEAR_M, "m",
             f"METHOD. Two chambers inside criteria.MH_SNAP_M are ONE structure, so the "
             f"{self.n_contracted} pair(s) that were are contracted rather than published "
             f"as two. MH_SNAP_M is the same constant s1_roads used to node the corridor "
             f"graph, so the pair is inside the radius that already declares two positions "
             f"one node; s2 inherited it and did not design it. Every one is listed in "
             f"`close_pairs` with what was done. The reach above absorbs the stub, and any "
             f"reach that then exceeds the split length is re-divided "
             f"({self.n_resplit} chamber(s) put back at build time, "
             f"{self.n_resplit_live} of them still in the published layer after the prune) "
             f"rather than the check widened. It does NOT re-split for straightness, so a "
             f"reach that absorbs a stub can keep a bend with no chamber at it - "
             f"{self.n_bent} published reach(es) are past STRAIGHT_TOL_M, and the worst is "
             f"one of these. Chambering that bend would put two chambers inside this very "
             f"clearance, so the two rules conflict and the resolution is the engineer's."),
            ("INLET_DEG basis", "chord, after pruning, floored to 0.01", "-",
             f"METHOD, WITH A NAMED EXPOSURE. The direction of flow is the reach's CHORD, "
             f"because a pipe is laid straight between chambers "
             f"({b['two_point_pct']:.1f} % of built pipes are a 2-point line, "
             f"{b['within_0p5m_pct']:.2f} % inside 0.5 m of their chord) and "
             f"`substring` leaves a duplicated vertex on {self.n_sliver:,} of "
             f"{len(self.seg):,} segments, whose first leg is under 1 mm. Measured AFTER "
             f"the prune, so no angle comes off a pipe that was deleted. FLOORED to 0.01 "
             f"deg and the flag taken from the published number, so the two can never "
             f"disagree and an angle is never printed as compliant while it is flagged. "
             f"THE EXPOSURE: where a reach is straight the chord IS the pipe and the "
             f"question does not arise, but on the {self.n_bent} reach(es) that bend past "
             f"STRAIGHT_TOL_M it is not, and {self.n_basis_amb} chamber(s) change side of "
             f"the 90 deg rule if the direction is read locally instead "
             f"({'/'.join(f'{m:g}' for m in BEARING_LEG_SWEEP_M)} m sweep) - "
             f"{self.n_basis_amb_unpriced} of them published as compliant and therefore "
             f"unpriced. Swept and published rather than settled by picking a basis."),
            ("INLET_DEG where there is no inlet pipe", "blank", "-",
             f"METHOD. {self.n_inlet_na:,} chambers - heads with no inlet pipe and outfalls "
             f"with no outgoing pipe - carry no angle. G203-p30 governs an INLET PIPE, so "
             f"the rule does not APPLY there; that is not the same as a check that could "
             f"not run. Filling it with 90 or 180 would make a not-applicable look "
             f"measured, which is the ANGLE_DEG = 90 defect in another costume."),
            ("tau", C.TAU_PA, "Pa",
             "ASSUMED (GAP-9). Not used by this stage - no gradient is set here - and "
             "carried on the outputs so the exposure travels."),
        ]
        return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "BASIS"])

    # ---------------------------------------------------------------- publish
    def publish(self) -> "Chambers":
        gpd = self.gpd
        import shapely
        os.makedirs(os.path.dirname(OUT_GPKG), exist_ok=True)
        if os.path.exists(OUT_GPKG):
            os.remove(OUT_GPKG)

        ch = self.ch.copy()
        ch["STAGE"] = STAGE
        ch["TAU_FLAG"] = TAU_FLAG
        chg = gpd.GeoDataFrame(ch, geometry=shapely.points(ch.X.values, ch.Y.values),
                               crs=f"EPSG:{CRS_EPSG}")
        seg = self.seg.copy()
        seg["STAGE"] = STAGE
        segg = gpd.GeoDataFrame(seg, geometry=seg.geometry.values, crs=f"EPSG:{CRS_EPSG}")
        cn = self.conn.copy()
        cn["STAGE"] = STAGE
        cng = gpd.GeoDataFrame(cn, geometry=cn.geometry.values, crs=f"EPSG:{CRS_EPSG}") \
            if len(cn) else None
        un = self.unserved.copy()
        ung = gpd.GeoDataFrame(un, geometry=un.geometry.values, crs=f"EPSG:{CRS_EPSG}") \
            if len(un) else None
        pr = self.pruned_arcs.copy()
        prg = gpd.GeoDataFrame(pr.drop(columns=["_P"], errors="ignore"),
                               geometry=pr.geometry.values, crs=f"EPSG:{CRS_EPSG}")

        _log(f"writing {OUT_GPKG}")
        chg.to_file(OUT_GPKG, layer="chambers", driver="GPKG")
        segg.to_file(OUT_GPKG, layer="segments", driver="GPKG")
        if cng is not None:
            cng.to_file(OUT_GPKG, layer="connections", driver="GPKG")
        if ung is not None:
            ung.to_file(OUT_GPKG, layer="unserved", driver="GPKG")
        prg.to_file(OUT_GPKG, layer="pruned", driver="GPKG")

        for name, df in self._table_set().items():
            _write_table(df, name)
            df.to_file(OUT_GPKG, layer=name, driver="GPKG") if hasattr(df, "to_file") \
                else gpd.GeoDataFrame(df).to_file(OUT_GPKG, layer=name, driver="GPKG")
        _log(f"    {os.path.getsize(OUT_GPKG) / 1e6:.1f} MB, sha1 {_sha1(OUT_GPKG)}")
        return self

    def _table_set(self) -> Dict[str, pd.DataFrame]:
        return {
            "triggers": self.t_trigger,
            "triggers_deferred": self.t_deferred,
            "spacing": self.t_spacing,
            "spacing_sweep": self.t_spacing_sweep,
            "search_ab": self.t_search,
            "congestion": self.t_congest,
            "congestion_sweep": self.t_congest_sweep,
            "prune": self.t_prune,
            "inlet_angle": self.t_inlet,
            "inlet_split": self.t_inlet_split,
            "close_pairs": self.t_close,
            "orphan_components": self.t_orphan,
            "compliance": self.t_compliance,
            "readiness": self.t_readiness,
            "assumptions": self.t_assumptions,
            "manifest": self.t_manifest,
        }

    # ---------------------------------------------------------------- manifest & report
    def manifest(self) -> "Chambers":
        ch, seg, cn = self.ch, self.seg, self.conn
        km = seg.LEN_M.sum() / 1000.0
        tot_q = float(self.plots.Q_AVG_M3D.sum())
        q = float(cn.Q_ADF_M3D.sum()) if len(cn) else 0.0
        G = "G203"
        rows = [
            ("chambers", len(ch), "-", "this stage"),
            ("chambers per km", round(len(ch) / km, 2), "-",
             f"built network {self.m_spacing['mh_per_km']:.2f} (asbuilt, measured)"),
            ("network published", round(km, 1), "km", "this stage, after pruning"),
            ("corridors in", round(self.arcs.LEN_M.sum() / 1000, 1), "km", "stage 2"),
            ("pruned - neither collects nor conveys",
             round(self.pruned_arcs.LEN_M.sum() / 1000, 1), "km", "this stage"),
            ("segments", len(seg), "-", "chamber to chamber"),
            ("spacing median", round(float(seg.LEN_M.median()), 2), "m",
             f"{G}-p30 Tab 12 allows {TAB12_TIGHTEST_M:g} m at DN200-315"),
            ("spacing max", round(float(seg.LEN_M.max()), 2), "m", f"{G}-p30 Tab 12"),
            ("segments over Table 12", int((seg.LEN_M > TAB12_TIGHTEST_M).sum()), "-",
             f"{G}-p30 Tab 12"),
            ("junction chambers", int((ch.TRIGGER == "junction").sum()), "-",
             f"{G}-p29 4.4 'Junction of two or more pipes'"),
            ("head chambers", int((ch.TRIGGER == "head").sum()), "-",
             f"{G}-p30 'End of each lateral sewer'"),
            ("bend chambers", int((ch.TRIGGER == "bend").sum()), "-",
             "PROJECT, calibrated to built straightness"),
            ("spacing chambers", int((ch.TRIGGER == "spacing").sum()), "-",
             f"{G}-p29 4.4 regular spacing"),
            ("outfalls", int((ch.N_OUT == 0).sum()), "-", "philosophy H15"),
            ("chambers with an inlet below 90 deg", int(ch.INLET_FLAG.sum()), "-",
             f"{G}-p30; measured AFTER pruning, on the published pipes"),
            ("  of the inlets, BRANCH (chamber has 2+ inflows)",
             int((self._sub90.N_IN >= 2).sum()) if len(self._sub90) else 0, "-",
             f"{self._n_in_branch:,} branch inlets in all; NAMA's own built network breaches "
             f"{AB_INLET['junction_pct']:g} % of theirs ({AB_INLET['src']})"),
            ("  of the inlets, PASS-THROUGH HAIRPIN (one inflow, no branch)",
             int((self._sub90.N_IN == 1).sum()) if len(self._sub90) else 0, "-",
             f"NAMA {AB_INLET['passthrough_pct']:g} % ({AB_INLET['src']})"),
            ("  of the inlets, a bend WITHIN one corridor", self.n_same_arc, "-",
             "the only kind this stage could move a chamber to fix"),
            ("  of the inlets, fixable by MOVING A CHAMBER", self.n_movable, "-",
             "MEASURED, not asserted: not standing on a stage-2 graph node AND its inlet "
             "arrives on a different corridor from the one its outlet leaves on"),
            ("  chambers whose 90 deg verdict depends on the BASIS", self.n_basis_amb, "-",
             f"the direction of flow is published as the reach's CHORD; read from the "
             f"pipe's local direction "
             f"({'/'.join(f'{m:g}' for m in BEARING_LEG_SWEEP_M)} m) these change side. "
             f"{self.n_basis_amb_unpriced} of them are published COMPLIANT and so carry no "
             f"priced swept channel. All sit on a reach that bends beyond STRAIGHT_TOL_M"),
            ("reaches bent beyond STRAIGHT_TOL_M with no chamber at the bend",
             self.n_bent, "-",
             f"PROJECT {STRAIGHT_TOL_M:g} m. The rule this stage's bend trigger and its "
             f"inlet angle both rest on, asserted since W12 began and measured here for "
             f"the first time. See the compliance row for the two causes"),
            ("chambers with no inlet pipe to measure", self.n_inlet_na, "-",
             "a head has no inlet and an outfall has no outgoing pipe to measure against; "
             "published as blank, NEVER as a fabricated 90 or 180"),
            ("chambers contracted - inside the 3 m minimum clearance", self.n_contracted,
             "-", "criteria.MH_SNAP_M: two chambers inside the node-merge radius ARE one "
                  "structure. Removed by this stage, listed in `close_pairs`"),
            ("chamber pairs still inside 3 m", self.residual_pairs, "-",
             "not joined by a pipe, so contracting them would fuse two branches"),
            ("chambers put back after contraction", self.n_resplit, "-",
             f"a reach that absorbed a stub and went over the {self.split_m:g} m split "
             f"length is re-divided, rather than the check being widened to admit it. "
             f"COUNTED BEFORE THE PRUNE - see the next row for how many a reader can find"),
            ("  of those, still in the published layer", self.n_resplit_live, "-",
             "the prune can delete the very reach that was re-divided. On the first run "
             "with this code it did: the manifest said 1 and the layer held none, which is "
             "the same 'measured on a network that was then thrown away' defect this stage "
             "had just removed from the inlet angles"),
            ("chambers on wadi ground", int(ch.ON_WADI.sum()), "-",
             f"{G}-p30 4.4.1 i.a; class test is a project assumption"),
            ("pipe with BOTH chambers on wadi ground",
             round(float(seg.loc[seg.ON_WADI == 1, "LEN_M"].sum() / 1000), 2), "km",
             f"{G}-p30 4.4.1 i.a - running ALONG a wadi, not crossing it (H1)"),
            ("components with no path to the Main Pipe", len(self.t_orphan), "-",
             "H15: a piece that drains nowhere is never legal. Stage 2's `island` arcs"),
            ("chambers in those components", int(ch.ORPHAN.sum()), "-", "H15"),
            ("plots connected", len(cn), "-", "this stage"),
            ("plots not connected", len(self.unserved), "-", "each with a WHY"),
            ("load connected", round(q, 1), "m3/d",
             f"of {tot_q:,.1f} = {q / tot_q * 100:.2f} %"),
            ("load connected", round(q / tot_q * 100, 2), "%", "of the load-bearing plots"),
            ("properties connected", round(float(cn.N_PROP.sum()) if len(cn) else 0, 0), "-",
             f"of {self.plots.N_PROP.sum():,.0f}"),
            ("tertiary pipe", round(float(cn.L_TERT_M.sum()) / 1000 if len(cn) else 0, 1),
             "km", f"HCC to chamber, each within {TERT_MAX_M:g} m"),
            ("tertiary run median", round(float(cn.L_TERT_M.median()) if len(cn) else 0, 1),
             "m", f"{G}-p22 Tab 6 lateral row caps it at {TERT_MAX_M:g} m"),
            ("connections crossing a third-party plot",
             int(cn.XPLOT.sum()) if len(cn) else 0, "-", "needs a wayleave"),
            ("connections crossing a dual carriageway",
             int(cn.XDUAL.sum()) if len(cn) else 0, "-",
             "legal as a crossing (H1a), priced as a structure"),
            ("load not connected", round(float(self.unserved.Q_ADF_M3D.sum()), 1), "m3/d",
             f"{self.unserved.Q_ADF_M3D.sum() / tot_q * 100:.2f} % - every plot named"),
            ("  of it, within a chained rider+lateral (2 x 45 m)",
             round(float(self.unserved.loc[self.unserved.L_TERT_M <= 2 * TERT_MAX_M,
                                           "Q_ADF_M3D"].sum()), 1), "m3/d",
             f"{G}-p17 3.2 chain; needs a corridor the drawing does not have"),
            ("  of it, beyond even that",
             round(float(self.unserved.loc[self.unserved.L_TERT_M > 2 * TERT_MAX_M,
                                           "Q_ADF_M3D"].sum()), 1), "m3/d",
             "philosophy 8a: served by ANOTHER system, not by this network"),
            ("chambers with more than 3 connections", int(ch.OVER_HCC3.sum()), "-",
             f"{G}-p17 3.2 'usually up to 3'"),
            ("DRAIN_SHALLOW", int(cn.DRAIN_SHAL.sum()) if len(cn) else 0, "-",
             "connections that drain into a sewer at MINIMUM cover; a bound, NOT CAN_DRAIN"),
            ("CAN_DRAIN", "cannot run", "-",
             "no designed invert exists at stage 4; NOT run against a seed"),
            ("uphill share of the published length",
             round(float(seg.loc[seg.AGN_GRADE == 1, "LEN_M"].sum() / seg.LEN_M.sum()
                         * 100), 2), "%",
             "stage 2 published 23.15 % over ALL its arcs; this is over the pruned network"),
            ("tau", C.TAU_PA, "Pa", "ASSUMED (GAP-9), unused by this stage"),
            ("split length", self.split_m, "m", "MEASURED from the built median"),
            ("sigma_dz", round(self.sigma_dz, 4), "m", "terrain manifest, differential"),
            ("grade-break detection floor", round(self.grade_floor, 1), "mm/m",
             "derived; below it a ground grade break is DEM noise"),
            ("runtime", round(time.time() - self.t0, 1), "s", ""),
            ("stage version", STAGE_VERSION, "-", ""),
        ]
        self.t_manifest = pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "SOURCE"])
        os.makedirs(RUN, exist_ok=True)
        with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
            json.dump({r[0]: r[1] for r in rows}, f, indent=1, default=str)
        return self

    def report(self) -> "Chambers":
        ch, seg, cn = self.ch, self.seg, self.conn
        tot_q = float(self.plots.Q_AVG_M3D.sum())
        q = float(cn.Q_ADF_M3D.sum()) if len(cn) else 0.0
        km = seg.LEN_M.sum() / 1000.0
        ab = self.t_search
        sw = self.t_spacing_sweep
        A = ab.iloc[0]
        Cc = ab.iloc[2]
        L: List[str] = []
        L.append("# W12 stage 4 - chambers, and every plot's way into them\n")
        L.append(f"_{time.strftime('%Y-%m-%d %H:%M')} - {STAGE_VERSION} - {TAU_FLAG}_\n")

        L.append("## The headline\n")
        L.append(
            f"**{len(ch):,} chambers on {km:,.1f} km - {len(ch) / km:.1f} per km against the "
            f"built network's {self.m_spacing['mh_per_km']:.1f}** - and "
            f"**{len(cn):,} of {len(self.plots):,} load-bearing plots connected, carrying "
            f"{q:,.0f} of {tot_q:,.0f} m3/d ({q / tot_q * 100:.1f} %)** on "
            f"{cn.L_TERT_M.sum() / 1000 if len(cn) else 0:,.1f} km of tertiary pipe. "
            f"{len(self.unserved):,} plots are NOT connected and every one of them is named "
            f"with a reason.\n")
        L.append(
            f"**{self.pruned_arcs.LEN_M.sum() / 1000:,.1f} km of corridor was thrown away** "
            f"because it neither collects a connection nor conveys one - "
            f"{self.pruned_arcs.LEN_M.sum() / self.arcs.LEN_M.sum() * 100:.0f} % of what "
            f"stage 2 handed over. W10 shipped 117.3 km of exactly that.\n")

        L.append("## The uncomfortable part first\n")
        L.append(
            f"**The drainability test is not run.** `CAN_DRAIN` asks whether a plot's outlet "
            f"sits above the sewer invert where it joins, and there is no designed invert at "
            f"stage 4. Running it against a seeded depth is what rejected 5,715 plots for "
            f"nothing last time. What is published instead is a bound that needs no invert: "
            f"**DRAIN_SHALLOW = 1 on {int(cn.DRAIN_SHAL.sum()) if len(cn) else 0:,} of "
            f"{len(cn):,} connections "
            f"({(cn.DRAIN_SHAL.mean() * 100) if len(cn) else 0:.1f} %)**, meaning the plot "
            f"can drain into a sewer laid at the MINIMUM legal cover. A 1 is a guarantee. A "
            f"0 is not a rejection - it says the sewer must be deeper there, which is stage "
            f"6's decision.\n")
        L.append(
            f"**And the biggest number in this stage is a choice, not a calculation.** "
            f"Table 12 (G203-p30) permits 100 m between chambers at DN200-315. NAMA build at "
            f"a median of {self.m_spacing['mh_spacing_median_m']:.2f} m and have never built "
            f"one longer than {self.m_spacing['mh_spacing_max_m']:.2f} m - not one of their "
            f"3,265 pipes exceeds Table 12. Since G203-p29 4.4 hands regular spacing to "
            f"\"maintenance equipment\", their network is the evidence of what that equipment "
            f"reaches, and this design is laid at {self.split_m:g} m. **On the same "
            f"corridors before any pruning that is "
            f"{int(sw.loc[sw.SPLIT_M == self.split_m, 'chambers'].iloc[0]):,} chambers "
            f"against {int(sw.loc[sw.SPLIT_M == 100.0, 'chambers'].iloc[0]):,} at Table "
            f"12's ceiling - a factor of "
            f"{sw.loc[sw.SPLIT_M == self.split_m, 'chambers'].iloc[0] / sw.loc[sw.SPLIT_M == 100.0, 'chambers'].iloc[0]:.1f}.** "
            f"The whole sweep is below. Nothing else in this stage moves a quantity by that "
            f"much, and it is the one number an engineer should overrule if NWS say their "
            f"jetting equipment reaches further than their 2006 contractor's did.\n")

        L.append("## What G203 asks for, and what was done about it\n")
        L.append("G203-p29 4.4, verbatim: _\"Manholes shall be provided at the following "
                 "locations: Change in pipe gradient; Change in pipe diameter; Junction of "
                 "two or more pipes; At regular spacing on straight pipeline based on "
                 "maintenance equipment\"_, continuing on p30 with _\"End of each lateral "
                 "sewer\"_. Five triggers. Three are placed:\n")
        L.append(_md(self.t_trigger))
        L.append("\nTwo are not placed because they cannot fall between two chambers. That "
                 "is an argument, and it is written out so it can be attacked:\n")
        L.append(_md(self.t_deferred))
        L.append("\n**Note what G203 does NOT list: a change of direction.** A bend chamber "
                 "is not a guideline requirement. It is here because a pipe is laid straight "
                 "between chambers, and that is measured, not assumed: "
                 f"{self.built_straight['two_point_pct']:.1f} % of NAMA's built pipes are a "
                 f"straight two-point line, the median departure from the chord is "
                 f"{self.built_straight['sagitta_median_m']:.3f} m and the p99 is "
                 f"{self.built_straight['sagitta_p99_m']:.3f} m. So the split rule is a "
                 f"CHORD OFFSET of {STRAIGHT_TOL_M:g} m, not an invented angle.\n")

        sb = self._sub90
        n_br = int((sb.N_IN >= 2).sum()) if len(sb) else 0
        n_hp = int((sb.N_IN == 1).sum()) if len(sb) else 0
        L.append("## Inlet angles - two defects, and only one of them is ours\n")
        L.append(
            f"G203-p30, verbatim: _\"No inlet pipe at manholes shall have an angle less than "
            f"90 deg to the direction of flow.\"_ **{int(ch.INLET_FLAG.sum()):,} chambers "
            f"breach it, on {len(sb):,} of {self._n_inlets:,} inlets, worst "
            f"{np.nanmin(ch.INLET_DEG.values):.2f} deg.** The as-built study found NAMA's "
            f"own network breaches it too and that the breaches are TWO different things "
            f"({AB_INLET['src']}), so ours are split the same way before anything is "
            f"decided about them.\n")
        L.append(_md(self.t_inlet_split))
        L.append(
            f"\n**On the operator's own measure this layout matches what they built at a "
            f"branch and beats it on a pass-through - and the first of those two is a "
            f"dead heat, not a win.** At a branch we breach "
            f"{n_br / max(self._n_in_branch, 1) * 100:.2f} % of inlets against their "
            f"{AB_INLET['junction_pct']:g} %; on a pass-through we breach "
            f"{n_hp / max(self._n_inlets - self._n_in_branch, 1) * 100:.2f} % against their "
            f"{AB_INLET['passthrough_pct']:g} %. Read the branch number carefully: the "
            f"denominator is the {self._n_in_branch:,} inlets the rule can be APPLIED to - "
            f"an inlet at an outfall has no outgoing pipe to be measured against and can "
            f"never breach, and counting those {self._n_inlets_all - self._n_inlets} extra "
            f"pipe ends would print 25.96 % instead. Their two denominators are also not "
            f"identical: {AB_INLET['src']} counts 249 breaching JUNCTION PAIRS in 941, "
            f"while this counts breaching branch INLETS. Close enough to compare, not close "
            f"enough to claim a margin of two hundredths of a point.\n")
        L.append(
            f"**{self.n_movable} of the {len(sb):,} can be designed away by moving a "
            f"chamber, and that number is measured rather than asserted.** A breach is "
            f"movable here only if the chamber is NOT standing on a stage-2 graph node - "
            f"where two corridors meet, the node IS the position - and its inlet arrives "
            f"on a different corridor from the one its outlet leaves on; the count of those "
            f"is taken from the published reaches, not written down as a nought. "
            f"A chamber can otherwise only be moved "
            f"ALONG the corridor it stands on. {len(sb) - self.n_same_arc:,} of the "
            f"breaches are the angle at which two mapped streets MEET, with which of them "
            f"drains into which fixed by stage 2's arborescence - moving a chamber does not "
            f"rotate a street. The other {self.n_same_arc} are one corridor turning back on "
            f"itself by more than 90 deg at a chamber the bend rule correctly put there - "
            f"sliding it along the same bend keeps the same turn. What WOULD move them is a "
            f"different corridor choice or a different join, which are stage 1 and stage 2 "
            f"decisions, and they are named here rather than absorbed.\n")
        L.append(
            f"**So they are flagged, sized and priced, not forced to a number.** "
            f"`SWEPT_CH` = 1 on all {int(ch.SWEPT_CH.sum()):,} of them: the resolution for a "
            f"sharp inlet is a purpose-made chamber with a swept channel, which G203-p30 "
            f"asks for in the same paragraph - benching _\"formed to permit safe access and "
            f"to maximise hydraulic efficiency\"_ and _\"Smooth transitions between inlet "
            f"and outlet\"_. What is NOT acceptable is a softer angle, and what is not "
            f"acceptable either is a count taken off the wrong network: this measurement is "
            f"made AFTER pruning, on the pipes that are published. Taken before it - which "
            f"is what the previous run did - it published 2,952, of which 145 were a priced "
            f"chamber detail for an inlet the prune had deleted, and 2,324 angles came off "
            f"a pipe that is not in the layer. The count also went UP, not down, when the "
            f"bearing stopped being read off a sub-millimetre digitising sliver: "
            f"{self.n_sliver:,} of {len(seg):,} segments begin with a leg under 1 mm, and "
            f"taking the direction of flow from "
            f"the chord instead - which is how a pipe is actually laid - uncovered "
            f"{self.n_same_arc} breaches the sliver had reported as 179.9 deg.\n")
        L.append(
            f"**And the number that measures how much of this rests on a choice: "
            f"{self.n_basis_amb} chambers change side of the 90 deg rule depending on "
            f"whether the direction of flow is read from the reach's chord or from the "
            f"pipe's own direction where it meets the chamber.** On a two-point reach the "
            f"two ARE the same number, exactly, and there is nothing to choose - that is "
            f"most of the layer, and it is why the change to the chord was right. But "
            f"{self.n_bent} reach(es) depart from their own chord by more than "
            f"STRAIGHT_TOL_M = {STRAIGHT_TOL_M:g} m - a bend with no chamber at it, which "
            f"is the one thing this stage's own straightness rule forbids and which it had "
            f"never measured on its own output - and every one of the 11 sits on one of "
            f"those. {self.n_basis_amb_unpriced} of the "
            f"{self.n_basis_amb} are published as COMPLIANT and therefore carry no priced "
            f"swept channel, so this is an under-count of a priced item, not a rounding "
            f"argument. Two causes, both ours: `split_positions` drops a bend cut that "
            f"lands within the {MH_MIN_CLEAR_M:g} m minimum clearance of a neighbour, and "
            f"`contract_pairs` re-divides an absorbed reach for LENGTH but not for "
            f"straightness. **It is not fixed here and it should not be forced**: "
            f"chambering those bends would put two chambers inside the very clearance the "
            f"contraction exists to honour, so the two project rules genuinely conflict on "
            f"this geometry and the resolution is the engineer's.\n")
        if self.n_bent:
            L.append(_md(self.t_bent, maxrows=10))
            L.append("\n")
        L.append(
            f"{self.n_inlet_na:,} chambers carry no angle at all, and that is not a gap in "
            f"the measurement: a head has no inlet pipe and an outfall has no outgoing pipe "
            f"to measure against, so G203-p30's rule does not apply to either. It is "
            f"published as a blank rather than as a fabricated 90 or 180.\n")

        if self.n_contracted or self.residual_pairs:
            L.append("\n## Chambers that were one structure pretending to be two\n")
            L.append(
                f"`criteria.MH_SNAP_M` = {MH_MIN_CLEAR_M:g} m is one constant wearing two "
                f"hats: the radius at which stage 1 merged positions into a single node, "
                f"and the minimum clear distance between two chambers. Two chambers closer "
                f"than the radius that merges nodes are one structure. "
                f"**{self.n_contracted} were, and they have been contracted into one** - "
                f"every one of them at the two ends of a corridor shorter than the "
                f"clearance itself, which is the one case `split_positions` cannot catch "
                f"because it keeps both ends of every arc. "
                f"{self.residual_pairs} pair(s) remain.\n")
            L.append(_md(self.t_close, maxrows=20))

        L.append("\n## Spacing, against Table 12 and against the operator\n")
        L.append(_md(self.t_spacing))
        L.append("\n")
        L.append(_md(self.t_spacing_sweep))
        L.append("\n`over_tab12` is 0 on every row up to 100 m, which is the point: Table 12 "
                 "is not the binding constraint anywhere in this design. The binding "
                 "constraint is the operator's own practice, and it costs "
                 f"{len(ch) / km:.0f} chambers per km.\n")

        L.append("## Plot connections - ranking every carrier, and what that is worth\n")
        L.append(
            f"Same cost function, same chamber set, three candidate sets. Arm A is what the "
            f"last iteration did.\n")
        L.append(_md(self.t_search))
        L.append(
            f"\n**Ranking every carrier is worth "
            f"{Cc.load_pct - A.load_pct:+.2f} percentage points of load. That is the honest "
            f"number and it is nearly nothing.** With a chamber every {self.split_m:g} m "
            f"the nearest one is almost always inside 45 m already, so there is no load "
            f"left for a better search to find. **The last iteration's 30 % rejection was "
            f"its sparse carrier set, not its search**, and this stage cannot reproduce "
            f"that gain because it does not have that problem.\n")
        L.append(
            f"**What ranking every carrier DOES buy is legality.** Same load, same plots, "
            f"and: third-party plot crossings fall from {int(A.crosses_a_plot):,} to "
            f"{int(Cc.crosses_a_plot):,} "
            f"({(Cc.crosses_a_plot - A.crosses_a_plot) / max(A.crosses_a_plot, 1) * 100:+.0f} %), "
            f"dual-carriageway crossings from {int(A.crosses_a_dual)} to "
            f"{int(Cc.crosses_a_dual)}, connections onto a chamber standing on wadi ground "
            f"from {int(A.chamber_on_wadi):,} to {int(Cc.chamber_on_wadi):,} "
            f"({(Cc.chamber_on_wadi - A.chamber_on_wadi) / max(A.chamber_on_wadi, 1) * 100:+.0f} %), "
            f"and the busiest chamber from {int(A.max_conn_per_chamber)} connections to "
            f"{int(Cc.max_conn_per_chamber)}. The price is "
            f"{Cc.tertiary_km - A.tertiary_km:+.1f} km of tertiary pipe, about "
            f"{(Cc.tertiary_km - A.tertiary_km) * 1000 / max(len(cn), 1):.1f} m per "
            f"connection. **A wayleave over a neighbour's plot is not a length, it is a "
            f"negotiation, and {int(A.crosses_a_plot - Cc.crosses_a_plot):,} fewer of them "
            f"is what the extra pipe buys.**\n")
        L.append("_The three arms are measured BEFORE pruning, on one candidate set and one "
                 "cost, so their counts differ from the published layer by the handful of "
                 "connections the prune re-pointed._\n")
        L.append("The cost, in metres of equivalent pipe, is: the tertiary length, plus "
                 f"{PEN_CROSS_PLOT_M:g} m if the run crosses a third party's plot, plus "
                 f"{PEN_CROSS_DUAL_M:g} m if it crosses a dual carriageway, plus "
                 f"{PEN_WADI_M:g} m if the chamber stands on wadi ground, plus "
                 f"{CONGEST_M:g} m for every connection already on that chamber beyond the "
                 f"{HCC_PER_RIDER} G203-p17 calls usual. Constrained plots choose first.\n")
        L.append(_md(self.t_congest_sweep))
        L.append("\n")
        L.append(_md(self.t_congest))

        L.append("\n## What is not connected, and why\n")
        if len(self.unserved):
            u = self.unserved
            near = u[u.L_TERT_M <= 2 * TERT_MAX_M]
            far = u[u.L_TERT_M > 2 * TERT_MAX_M]
            L.append(
                f"{len(u):,} load-bearing plots carrying {u.Q_ADF_M3D.sum():,.0f} m3/d "
                f"({u.Q_ADF_M3D.sum() / tot_q * 100:.1f} %) have no chamber within "
                f"{TERT_MAX_M:g} m of tertiary run.\n\n"
                f"- **{len(near):,} of them ({near.Q_ADF_M3D.sum():,.0f} m3/d) sit within a "
                f"chained rider + lateral** (2 x 45 m, the chain G203-p17 3.2 describes). "
                f"They are reachable, but only by laying a lateral where the drawing has no "
                f"corridor. That is a corridor question, not a connection one.\n"
                f"- **{len(far):,} ({far.Q_ADF_M3D.sum():,.0f} m3/d) are beyond even that** "
                f"and are not served by the central network at all. Philosophy 8a: every "
                f"plot is SERVED, the question is by which system, and these belong in the "
                f"options appraisal as satellite or on-site.\n")
        L.append("\n## Compliance, recomputed\n")
        L.append(_md(self.t_compliance))

        L.append("\n## What this stage cannot fill\n")
        r = self.t_readiness
        L.append(f"{int((r.STATUS == 'filled').sum())} of {len(r)} contract fields are "
                 f"filled. The rest are named, with what they wait on - an unfilled field "
                 f"that nobody named is how a stage silently does nothing.\n")
        L.append(_md(r[r.STATUS == "deferred"].groupby("WAITS_ON").size()
                     .rename("FIELDS").reset_index().sort_values("FIELDS",
                                                                 ascending=False)))
        L.append("\n**`TIER` is the one that matters.** There is no hierarchy stage in W12, "
                 "so no reach here knows whether it is a lateral, a sub main or a trunk "
                 "main. Table 12's spacing band, the minimum diameter (G203-p22 Tab 6) and "
                 "the permitted materials all key off it. This design is laid at the "
                 "DN200-315 band, which is the tightest, so nothing here becomes illegal "
                 "when the tiers arrive - but the larger pipes are carrying more chambers "
                 "than they need.\n")

        L.append("\n## Pruning\n")
        L.append(_md(self.t_prune))
        L.append(
            f"\nThe rule is 'a chosen chamber keeps its whole path to the outfall; "
            f"everything else goes'. It uses no length threshold, so it is not the "
            f"philosophy's 60 m finger rule - it is stronger, and the finger count is "
            f"reported inside it. Note that an arc can be pruned in PART: a corridor whose "
            f"upper end serves nothing but whose lower end conveys keeps only the lower "
            f"end, which is why the two 'less' rows do not add up to the arc count.\n"
            f"{getattr(self, 'n_relocated', 0)} connections were re-pointed onto a "
            f"surviving chamber because the one they had chosen was a TERMINAL with nothing "
            f"kept above it. Nothing was dropped in silence - `verify()` reconciles the "
            f"load to the milligram against the source plot file.\n")

        L.append("\n## Every number, with where it came from\n")
        L.append(_md(self.t_manifest))
        L.append("\n## Assumptions\n")
        L.append(_md(self.t_assumptions))
        if self.notes:
            L.append("\n## Notes\n")
            for n in self.notes:
                L.append(f"- {n}\n")
        os.makedirs(RUN, exist_ok=True)
        with open(REPORT_MD, "w", encoding="utf-8") as f:
            f.write("\n".join(L))
        _log(f"report -> {REPORT_MD}")
        return self

    # ---------------------------------------------------------------- kmz
    def present(self) -> "Chambers":
        try:
            from w12 import present as P
        except Exception as e:                                       # noqa: BLE001
            self.notes.append(f"KMZ not written: {e}")
            return self
        try:
            v_ch = P.View(
                name="chamber_trigger", title="Chambers by WHY THEY EXIST",
                question="Which of G203-p29 4.4's triggers put each chamber there?",
                role="chambers", geom="point", mode="categorical", field="TRIGGER",
                categories=[
                    ("junction", "Junction of two or more pipes (G203-p29 4.4)",
                     (215, 48, 39), 1.1),
                    ("head", "End of a lateral - a head (G203-p30)", (69, 117, 180), 0.9),
                    ("outfall", "Outfall (H15: exactly one per component)", (0, 0, 0), 1.6),
                    ("bend", "Bend - a pipe is laid straight between chambers (PROJECT)",
                     (255, 158, 23), 0.7),
                    ("spacing", "Regular spacing (G203-p29 4.4; Tab 12 the ceiling)",
                     (150, 150, 150), 0.5),
                    ("chamber", "Two corridors meeting end to end", (120, 180, 120), 0.6),
                ],
                folder_fields=("TRIGGER",),
                popup=[("NODE_UID", "Chamber", "{}"), ("TRIGGER", "Why it exists", "{}"),
                       ("NODE_KIND", "What it turned out to be", "{}"),
                       ("GRD_M", "Ground m aOD", "{:.2f}"),
                       ("N_CONN", "Plot connections", "{:d}"),
                       # 2 dp, not 1: at 1 dp an 89.96 deg inlet prints as "90.0" on the
                       # popup of a chamber the same layer flags SWEPT_CH - the exact
                       # contradiction the published column was floored to remove.
                       ("INLET_DEG", "Inlet angle deg (G203-p30 min 90)", "{:.2f}"),
                       ("ON_WADI", "On wadi ground (G203-p30 4.4.1)", "{:d}")],
                notes=("G203 lists no bend trigger. The bend chambers are ours, and the "
                       "threshold is a 0.5 m chord offset measured off NAMA's own built "
                       "pipes, not an invented angle.",),
            )
            P.register(v_ch)
            gdf = self.gpd.read_file(OUT_GPKG, layer="chambers")
            out = os.path.join(W12, "shp", "W12_chambers_trigger.kmz")
            r = P.kmz(gdf, v_ch, out, source=f"{STAGE_VERSION} | {TAU_FLAG}")
            _log(f"    {r.summary() if hasattr(r, 'summary') else out}")
        except Exception as e:                                       # noqa: BLE001
            self.notes.append(f"chamber KMZ not written: {type(e).__name__}: {e}")
        try:
            v_cn = P.View(
                name="conn_len", title="Plot connections by TERTIARY RUN LENGTH",
                question="How far does each plot have to reach, and where is the 45 m cap "
                         "binding?",
                role="connections", geom="line", mode="graduated", field="L_TERT_M",
                breaks=[10.0, 20.0, 30.0, TERT_MAX_M],
                break_refs=["", "", "", "G203-p22 Tab 6 lateral row / p17 3.2"],
                ramp="traffic", width_range=(0.9, 3.0),
                popup=[("PLOT_ID", "Plot", "{}"), ("OUT_NODE", "Chamber", "{}"),
                       ("L_TERT_M", "Tertiary run m", "{:.1f}"),
                       ("RANK", "Rank of this chamber by bare length", "{:d}"),
                       ("Q_ADF_M3D", "Load m3/d", "{:.2f}"),
                       ("XPLOT", "Crosses another plot", "{:d}"),
                       ("DRAIN_SHAL", "Drains into a MINIMUM-cover sewer", "{:d}")],
                notes=("45 m is the last break and it is the cap, from G203-p22 Table 6's "
                       "lateral row. Nothing is published beyond it.",),
            )
            P.register(v_cn)
            gdf = self.gpd.read_file(OUT_GPKG, layer="connections")
            out = os.path.join(W12, "shp", "W12_chambers_connections.kmz")
            r = P.kmz(gdf, v_cn, out, source=f"{STAGE_VERSION} | {TAU_FLAG}",
                      max_features=300000)
            _log(f"    {r.summary() if hasattr(r, 'summary') else out}")
        except Exception as e:                                       # noqa: BLE001
            self.notes.append(f"connection KMZ not written: {type(e).__name__}: {e}")
        return self

    # ---------------------------------------------------------------- driver
    def build(self) -> "Chambers":
        # `angles` sits AFTER `prune` on purpose: measured before it, the inlet angle at a
        # chamber is the smallest over pipes the prune then deletes, and the last run
        # published 145 priced swept-channel chambers for inlets that are not in the
        # published layer. `contract_pairs` sits before `levels` so no terrain is sampled at
        # a chamber that is about to be merged away.
        (self.load().mint().link().contract_pairs().levels().fall()
         .connect().prune().topology().angles().reallocate())
        self.assemble()
        self.drain_bound()
        self.chamber_loads()
        self.orphans()
        _log("sweeps")
        self.t_spacing_sweep = self.sweep_spacing()
        self.t_congest_sweep = self.sweep_congestion()
        self.tables()
        self.t_readiness = self.readiness()
        self.t_assumptions = self.assumptions()
        self.manifest()
        self.publish()
        self.report()
        self.present()
        return self


# ==========================================================================================
# 3.  VERIFY - re-read what was PUBLISHED and check it independently
# ==========================================================================================

def verify() -> dict:
    """Re-open the published GeoPackage and re-derive every claim from it.

    It audits the PUBLISHED layers, never an in-memory model, because that is the one
    architectural rule W11a's auditor was built on and the reason W10 could publish a node
    layer and a pipe layer that disagreed by 10.39 m of depth.
    """
    import geopandas as gpd
    import shapely
    out: Dict[str, object] = {}
    fails: List[str] = []

    ch = gpd.read_file(OUT_GPKG, layer="chambers")
    seg = gpd.read_file(OUT_GPKG, layer="segments")
    cn = gpd.read_file(OUT_GPKG, layer="connections")
    un = gpd.read_file(OUT_GPKG, layer="unserved")

    def chk(name: str, ok: bool, detail: str):
        out[name] = ("pass" if ok else "FAIL") + " - " + detail
        if not ok:
            fails.append(name)

    # 1. LEN_M is the geometry it claims to measure
    gl = seg.geometry.length.values
    d = np.abs(gl - seg.LEN_M.values)
    chk("LEN_M matches the geometry", float(d.max()) <= CT.LEN_TOL_M,
        f"worst {d.max() * 1000:.1f} mm, tolerance {CT.LEN_TOL_M * 1000:.0f} mm")

    # 2. Table 12
    over = int((seg.LEN_M > TAB12_TIGHTEST_M + 1e-6).sum())
    chk("H12 spacing within Table 12", over == 0,
        f"{over} of {len(seg):,} segments over {TAB12_TIGHTEST_M:g} m "
        f"(G203-p30, DN200-315 band); longest {seg.LEN_M.max():.2f} m")

    # 3. topology resolves, no self-loops, out-degree at most 1
    uid = set(ch.NODE_UID)
    bad = int((~seg.US_NODE.isin(uid)).sum() + (~seg.DS_NODE.isin(uid)).sum())
    chk("every segment endpoint resolves to a chamber", bad == 0, f"{bad} dangling")
    chk("no self-loop", int((seg.US_NODE == seg.DS_NODE).sum()) == 0,
        f"{int((seg.US_NODE == seg.DS_NODE).sum())} segments start and end at one chamber")
    od = seg.US_NODE.value_counts()
    chk("out-degree at most 1 (the forest invariant)", int((od > 1).sum()) == 0,
        f"{int((od > 1).sum())} chambers with two outgoing segments")

    # 4. one outfall per component, and no cycle
    parent: Dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in zip(seg.US_NODE.values, seg.DS_NODE.values):
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b
    comp = {}
    for u in ch.NODE_UID.values:
        comp[find(u)] = comp.get(find(u), 0) + 1
    outs = {}
    for u in ch.loc[ch.N_OUT == 0, "NODE_UID"].values:
        outs[find(u)] = outs.get(find(u), 0) + 1
    badc = [r for r in comp if outs.get(r, 0) != 1]
    chk("H15 exactly one outfall per component", len(badc) == 0,
        f"{len(comp):,} components, {len(badc)} without exactly one outfall")
    # a forest has exactly (nodes - components) edges
    chk("no cycle (edges == nodes - components)",
        len(seg) == len(ch) - len(comp),
        f"{len(seg):,} segments, {len(ch):,} chambers, {len(comp):,} components")

    # 5. the tertiary cap, recomputed from the geometry rather than from the field
    if len(cn):
        cl = cn.geometry.length.values
        chk("tertiary run within 45 m, measured on the line",
            float(cl.max()) <= TERT_MAX_M + 0.01,
            f"longest {cl.max():.2f} m against the {TERT_MAX_M:g} m cap "
            f"(G203-p22 Tab 6 lateral row)")
        dd = np.abs(cl - cn.L_TERT_M.values)
        chk("L_TERT_M matches the line it sits on", float(dd.max()) < 0.05,
            f"worst {dd.max() * 1000:.1f} mm")
        chk("every connection lands on a published chamber",
            bool(cn.OUT_NODE.isin(uid).all()),
            f"{int((~cn.OUT_NODE.isin(uid)).sum())} land nowhere")

    # 6. ZERO SILENT DROPS - reconcile the load against the source data
    pl = gpd.read_file(PLOTS_GPKG, layer="plot_loads")
    pl["Q_AVG_M3D"] = pd.to_numeric(pl["Q_AVG_M3D"], errors="coerce").fillna(0.0)
    lb = pl[pl.Q_AVG_M3D > 0]
    ids = set(cn.PLOT_ID.astype(str)) | set(un.PLOT_ID.astype(str))
    chk("every load-bearing plot appears exactly once",
        len(ids) == len(lb) and len(cn) + len(un) == len(lb),
        f"{len(cn):,} connected + {len(un):,} named = {len(cn) + len(un):,} against "
        f"{len(lb):,} load-bearing plots")
    qsum = float(cn.Q_ADF_M3D.sum() + un.Q_ADF_M3D.sum())
    qtot = float(lb.Q_AVG_M3D.sum())
    chk("the load reconciles", abs(qsum - qtot) < 1e-3,
        f"{qsum:,.3f} against {qtot:,.3f} m3/d, difference {qsum - qtot:+.6f}")
    chk("no connection is blank on WHY", int((cn.WHY.astype(str) == "").sum()) == 0,
        f"{int((cn.WHY.astype(str) == '').sum())} blank")
    chk("no unserved plot is blank on WHY", int((un.WHY.astype(str) == "").sum()) == 0,
        f"{int((un.WHY.astype(str) == '').sum())} blank")

    # 7. CAN_DRAIN is genuinely absent, not silently seeded
    chk("CAN_DRAIN is NOT published", "CAN_DRAIN" not in cn.columns,
        "a seeded drainability flag rejected 5,715 plots last iteration; this stage "
        "publishes the level-free DRAIN_SHAL bound instead and names CAN_DRAIN as "
        "'cannot run'")

    # 8. no two chambers closer than the minimum clearance - they would be one structure
    from shapely import STRtree
    pts = shapely.points(ch.X.values, ch.Y.values)
    tr = STRtree(pts)
    a_i, b_i = tr.query(pts, predicate="dwithin", distance=C.MH_MIN_CLEAR_M - 1e-6)
    pairs = int(((a_i < b_i)).sum())
    chk("no two chambers inside the 3 m minimum clearance", pairs == 0,
        f"{pairs} pair(s) closer than {C.MH_MIN_CLEAR_M:g} m, which criteria.MH_SNAP_M "
        f"says ARE one structure")

    # 8b. and the contraction that got there is on the record, not silent
    try:
        cp = gpd.read_file(OUT_GPKG, layer="close_pairs", ignore_geometry=True)
    except Exception:                                              # noqa: BLE001
        cp = pd.DataFrame(columns=["JOINED_BY_A_PIPE", "STATUS"])
    n_con = int((cp.JOINED_BY_A_PIPE == 1).sum()) if len(cp) else 0
    chk("every contracted chamber is named in close_pairs",
        n_con == 0 or (n_con > 0 and cp.STATUS.astype(str).ne("").all()),
        f"{n_con} pair(s) contracted, each with an A, a B, the gap and what was done. "
        f"Anything a pass can ADD a later pass must be able to TAKE AWAY, and it publishes "
        f"how many")

    # 8c. INLET_DEG and INLET_FLAG must tell the same story. At 1 decimal an 89.96 deg
    # inlet printed as "90.0" beside a raised flag on 85 chambers - the number said
    # compliant and the flag said not.
    dg = pd.to_numeric(ch.INLET_DEG, errors="coerce")
    contra = int((((dg < C.INLET_MIN_DEG) & np.isfinite(dg)).astype(int)
                  != ch.INLET_FLAG.astype(int)).sum())
    chk("INLET_DEG and INLET_FLAG agree", contra == 0,
        f"{contra} chambers where the published angle and the published flag disagree")

    # 8d. the angle was measured on the PUBLISHED pipes, not on ones the prune deleted
    import shapely as _sh2
    bo: Dict[str, float] = {}
    bi: Dict[str, List[float]] = {}
    for u, d, gm in zip(seg.US_NODE.values, seg.DS_NODE.values, seg.geometry.values):
        c = _sh2.get_coordinates(gm)
        if len(c) < 2 or math.hypot(c[-1][0] - c[0][0],
                                    c[-1][1] - c[0][1]) < BEARING_MIN_LEG_M:
            continue
        b = _bearing(c[0][0], c[0][1], c[-1][0], c[-1][1])
        bo[u] = b
        bi.setdefault(d, []).append(b)
    re_ang = np.array([min((_inlet_angle(b, bo[u]) for b in bi[u]), default=np.nan)
                       if (u in bi and u in bo) else np.nan
                       for u in ch.NODE_UID.values])
    re_ang = np.floor(re_ang * 100.0) / 100.0          # the published rounding, applied here
    both = np.isfinite(re_ang) & np.isfinite(dg.values)
    worst = float(np.abs(re_ang[both] - dg.values[both]).max()) if both.any() else 0.0
    ghost = int((np.isfinite(dg.values) & ~np.isfinite(re_ang)).sum())
    chk("INLET_DEG was measured on the published pipes",
        worst <= 1e-6 and ghost == 0,
        f"{ghost} chambers carry an angle no published pipe can produce; worst "
        f"disagreement {worst:.4f} deg over {int(both.sum()):,} re-measured")

    # 8e. every number the manifest publishes about this stage's own EDITS must be findable
    # in the layer. `n_resplit` is counted before the prune, and the prune can delete the
    # very reach that was re-divided: the first run with that code published "1 chamber put
    # back" with none in the layer to find. This does not forbid the prune - it forbids the
    # manifest saying something the deliverable cannot show.
    try:
        man = gpd.read_file(OUT_GPKG, layer="manifest", ignore_geometry=True)
        mrow = man[man.ITEM.astype(str).str.strip()
                   == "of those, still in the published layer"]
        claimed = int(float(mrow.VALUE.iloc[0])) if len(mrow) else 0
    except Exception:                                              # noqa: BLE001
        claimed = 0
    # a re-split chamber is the only kind that carries a corridor and no position along it
    sig = int(((ch.ARC_CID.astype(str) != "") & (~np.isfinite(
        pd.to_numeric(ch.S_ALONG, errors="coerce")))).sum())
    chk("the re-split chambers the manifest claims are in the layer", claimed == sig,
        f"manifest says {claimed} survive the prune, the layer holds {sig}")

    # 8f. and the straightness the chord bearing rests on, re-measured off the file. This
    # does NOT assert it is zero - it is not, and the compliance table fails on it honestly.
    # What it asserts is that the published count is the true one.
    off = np.array([chord_offset_of(_sh2.get_coordinates(g)) for g in seg.geometry.values])
    n_bent = int((off > STRAIGHT_TOL_M).sum())
    try:
        brow = man[man.ITEM.astype(str).str.strip().str.startswith("reaches bent beyond")]
        claimed_bent = int(float(brow.VALUE.iloc[0])) if len(brow) else -1
    except Exception:                                              # noqa: BLE001
        claimed_bent = -1
    chk("the reaches bent past STRAIGHT_TOL_M are counted honestly",
        claimed_bent == n_bent,
        f"manifest says {claimed_bent}, the published geometry gives {n_bent} "
        f"(worst {off.max():.2f} m). A bend with no chamber at it is a real "
        f"non-conformity - it fails in `compliance`, it is not hidden here")

    # 9. ground levels agree with an independent resample of the terrain
    tf = T.TerrainFlow.load(GRID)
    k = min(4000, len(ch))
    idx = np.linspace(0, len(ch) - 1, k).astype(int)
    z = tf.elevation(ch.X.values[idx], ch.Y.values[idx], native=True)
    dz = np.abs(z - ch.GRD_M.values[idx])
    chk("GRD_M reproduces from the terrain", float(np.nanmax(dz)) < 0.01,
        f"{k:,} resampled, worst {np.nanmax(dz) * 1000:.1f} mm")

    out["_fails"] = fails
    return out


# ==========================================================================================
# 4.  SELF-TEST - prove each rule on a network small enough to check by hand
# ==========================================================================================

def selftest(verbose: bool = True) -> bool:
    ok = True

    def t(name: str, cond: bool, detail: str = ""):
        nonlocal ok
        ok = ok and cond
        if verbose:
            print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f"  {detail}" if detail else ""))

    print("s4_chambers self-test")

    # --- chord offset and bend breaking
    st = np.array([[0., 0.], [50., 0.], [100., 0.]])
    t("a straight line has zero chord offset", chord_offset_max(st, 0, 2) == 0.0)
    t("a straight line needs no bend break", bend_breaks(st, 0.5) == [])
    L = np.array([[0., 0.], [50., 0.], [50., 50.]])
    t("a right-angle corner is broken at the corner", bend_breaks(L, 0.5) == [1],
      str(bend_breaks(L, 0.5)))
    tiny = np.array([[0., 0.], [50., 0.2], [100., 0.]])
    t("a 0.2 m bulge over 100 m is NOT broken", bend_breaks(tiny, 0.5) == [])
    big = np.array([[0., 0.], [50., 3.0], [100., 0.]])
    t("a 3 m bulge IS broken", bend_breaks(big, 0.5) == [1])

    # --- split positions
    s = np.array([0., 100.])
    xy = np.array([[0., 0.], [100., 0.]])
    p = split_positions(s, xy, 30.0, 0.5)
    t("a 100 m straight run splits into equal parts none over 30 m",
      abs(np.diff(p).max() - 25.0) < 1e-6 and len(p) == 5, f"{np.diff(p)}")
    t("splits never exceed Table 12's tightest band",
      np.diff(split_positions(np.array([0., 250.]),
                              np.array([[0., 0.], [250., 0.]]), 100.0, 0.5)).max()
      <= TAB12_TIGHTEST_M + 1e-9)
    t("a run shorter than the split gets no interior chamber",
      len(split_positions(np.array([0., 12.]), np.array([[0., 0.], [12., 0.]]),
                          30.0, 0.5)) == 2)
    p2 = split_positions(np.array([0., 100.]), np.array([[0., 0.], [100., 0.]]), 30.0, 0.5)
    t("no two chambers closer than the 3 m minimum clearance",
      float(np.diff(p2).min()) >= MH_MIN_CLEAR_M - 1e-9, f"{np.diff(p2).min():.3f} m")
    p3 = split_positions(np.array([0., 3.5, 4.0]), np.array([[0., 0.], [3.5, 0.], [4., 0.]]),
                         30.0, 0.5)
    t("a 4 m corridor keeps only its two ends", len(p3) == 2, str(p3))

    # --- inlet angle convention (G203-p30)
    t("straight through is 180 deg", abs(_inlet_angle(90.0, 90.0) - 180.0) < 1e-9)
    t("a right-angle inlet is 90 deg", abs(_inlet_angle(0.0, 90.0) - 90.0) < 1e-9)
    t("flow doubling back is 0 deg", abs(_inlet_angle(0.0, 180.0) - 0.0) < 1e-9)
    t("90 deg is the guideline floor, not below it", INLET_MIN_DEG == 90.0)
    # the published angle may understate compliance, never overstate it: a rounded 89.96
    # printed as "90.0" beside a raised flag is what made INLET_DEG and INLET_FLAG disagree
    # on 85 chambers.
    _f = lambda v: math.floor(v * 100.0) / 100.0            # noqa: E731
    t("an 89.96 deg inlet never publishes as 90", _f(89.9612) < INLET_MIN_DEG,
      f"{_f(89.9612)}")
    t("a breach can never publish a compliant number",
      all(_f(v) < INLET_MIN_DEG for v in (89.99999, 89.995, 89.9, 88.27, 23.18)))
    t("a compliant angle is never turned into a breach",
      all(_f(v) >= INLET_MIN_DEG for v in (90.0, 90.00001, 90.01, 179.999, 180.0)))
    t("flooring never lifts an angle", all(_f(v) <= v + 1e-12
                                           for v in (89.9999999, 88.27, 23.18, 179.9999)))
    t("flooring twice can drop another 0.01 - so the raw angle is floored ONCE",
      _f(_f(20.0602)) < _f(20.0602), f"{_f(_f(20.0602))} vs {_f(20.0602)}")
    t("the published minimum is a single floor of the raw minimum",
      _f(min(88.2661, 91.4)) == _f(88.2661))
    # --- the chord is the pipe only where the reach is straight, and that is checkable
    _straight = np.array([[0.0, 0.0], [0.0, 25.0]])
    _bent = np.array([[0.0, 0.0], [10.0, 1.0], [20.0, 0.0]])
    _sliver = np.array([[0.0, 0.0], [0.0, 1e-9], [0.0, 25.0]])
    t("a two-point reach has no chord offset", chord_offset_of(_straight) == 0.0)
    t("a bent reach reports the bulge it actually has",
      abs(chord_offset_of(_bent) - 1.0) < 1e-9, f"{chord_offset_of(_bent):.4f}")
    t("on a straight reach the chord and the local leg are the SAME bearing - which is why "
      "the chord change was exact on 52,610 of 56,667 reaches",
      _end_bearings(_straight, 0.0) == _end_bearings(_straight, 1.0))
    t("on a bent reach they are NOT, and that is the exposure this stage publishes",
      abs(_end_bearings(_bent, 0.0)[0] - _end_bearings(_bent, 1.0)[0]) > 1.0,
      f"{_end_bearings(_bent, 0.0)[0]:.2f} vs {_end_bearings(_bent, 1.0)[0]:.2f}")
    t("a duplicated vertex cannot set the direction of flow",
      abs(_end_bearings(_sliver, 1.0)[0] - _bearing(0.0, 0.0, 0.0, 25.0)) < 1e-9)

    # --- Table 12 bands, from criteria, against the PDF transcription
    t("Table 12 DN200 band is 100 m", C.mh_max_spacing(200) == 100.0)
    t("Table 12 DN900 band is 120 m", C.mh_max_spacing(900) == 120.0)
    t("Table 12 DN1400 band is 150 m", C.mh_max_spacing(1400) == 150.0)
    t("Table 12 above DN1400 is 200 m", C.mh_max_spacing(1700) == 200.0)
    t("the tightest band is the one used before a diameter exists",
      TAB12_TIGHTEST_M == min(v for _, v in C.MH_SPACING_BANDS))

    # --- the tertiary numbers, against the pages
    t("tertiary cap is 45 m (G203-p22 Tab 6 lateral row)", TERT_MAX_M == 45.0)
    t("HCC offset is 2.5 m (G203-p17 3.2)", HCC_OFFSET_M == 2.5)
    t("PCS cap is 50 m (G203-p18)", PCS_MAX_M == 50.0)
    t("3 HCC per rider (G203-p17 3.2)", HCC_PER_RIDER == 3)
    t("HCC depth band 1.2-2.0 m (G203-p19 3.4)",
      (HCC_DEPTH_MIN, HCC_DEPTH_MAX) == (1.2, 2.0))
    t("tertiary slope band 1-10 % (G203-p18 Tab 5)",
      (TERT_SLOPE_MIN, TERT_SLOPE_MAX) == (0.01, 0.10))

    # --- the grade-break floor
    f30 = grade_break_floor_mm_m(0.4769, 30.0)
    t("the grade-break floor at 30 m is about 67 mm/m", abs(f30 - 67.4) < 0.5, f"{f30:.1f}")
    t("a longer window resolves a finer break",
      grade_break_floor_mm_m(0.4769, 100.0) < f30)

    # --- a synthetic network: prune, forest invariant, and allocation
    # three corridors in a chain; only the middle one has a plot
    class _Fake:
        pass

    parent: Dict[str, str] = {}
    edges = [("A", "B"), ("B", "C"), ("C", "OUT"), ("D", "B")]
    collects = {("B", "C")}
    pathm = {"A": 300., "B": 200., "C": 100., "OUT": 0., "D": 250.}
    order = sorted(edges, key=lambda e: -pathm[e[0]])
    keep_node: Dict[str, bool] = {}
    kept = []
    for u, v in order:
        k = ((u, v) in collects) or keep_node.get(u, False)
        if k:
            keep_node[v] = True
            kept.append((u, v))
    t("prune keeps the collecting arc and everything below it",
      set(kept) == {("B", "C"), ("C", "OUT")}, str(kept))
    t("prune drops what neither collects nor conveys",
      ("A", "B") not in kept and ("D", "B") not in kept)

    # --- the drain bound is a bound, not a test
    grd_plot, grd_ch, Ln = 100.0, 99.0, 20.0
    need = grd_plot - HCC_DEPTH_MIN - TERT_SLOPE_MIN * Ln
    have = grd_ch - (MIN_COVER_M + DN_MIN_LATERAL / 1000.0)
    t("a plot 1 m above the chamber drains into a MINIMUM-cover sewer", need >= have,
      f"need {need:.2f} >= have {have:.2f}")
    need2 = 96.0 - HCC_DEPTH_MIN - TERT_SLOPE_MIN * Ln
    t("a plot 3 m BELOW the chamber does not - and that is a question, not a rejection",
      need2 < have)

    # --- the penalties are in metres and comparable
    t("every connection penalty is priced in metres of pipe",
      PEN_CROSS_PLOT_M == PEN_CROSS_DUAL_M == PEN_WADI_M == TERT_MAX_M)
    t("no penalty is a veto that could drop load silently",
      all(np.isfinite([PEN_CROSS_PLOT_M, PEN_CROSS_DUAL_M, PEN_WADI_M, CONGEST_M])))

    print("  " + ("ALL PASS" if ok else "SOME FAILED"))
    return ok


# ==========================================================================================
# 5.  CLI
# ==========================================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--split", type=float, default=None)
    a = ap.parse_args(argv)

    if a.selftest:
        return 0 if selftest() else 1
    if a.verify:
        r = verify()
        for k, v in r.items():
            if k.startswith("_"):
                continue
            print(f"  {v.split(' - ')[0]:9s}  {k}")
            print(f"             {v.split(' - ', 1)[1]}")
        f = r["_fails"]
        print(f"\n  {len(f)} failure(s)" + (": " + ", ".join(f) if f else ""))
        return 1 if f else 0
    if a.sweep:
        c = Chambers(split_m=a.split).load().mint()
        s = c.sweep_spacing()
        print(_md(s))
        _write_table(s, "spacing_sweep")
        return 0

    c = Chambers(split_m=a.split).build()
    print()
    print(_md(c.t_manifest.head(24)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
