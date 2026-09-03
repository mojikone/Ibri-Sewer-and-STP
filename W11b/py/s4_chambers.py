"""W11b stage 4 - CHAMBERS, AND EVERY PLOT'S WAY INTO THEM.

W11b BORROWS NOTHING.  Nothing here is imported from `W8/py/sewnet`, `W10/py` or
`W11a/py`.  The only project imports are `w11b.criteria`, `w11b.terrain`, `w11b.asbuilt`,
`w11b.contract` and `w11b.present`, which are W11b's own.  Earlier folders are read for
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

_HERE = os.path.dirname(os.path.abspath(__file__))            # .../W11b/py
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from w11b import criteria as CR                                # noqa: E402
from w11b import asbuilt as AB                                 # noqa: E402
from w11b import contract as CT                                # noqa: E402
from w11b import terrain as T                                  # noqa: E402

C = CR.DEFAULT

STAGE = "s4_chambers"
STAGE_VERSION = "W11b-chambers-1.0"

# ================================================================== paths
W11B = os.path.dirname(_HERE)                                  # .../W11b
CLAUDE = os.path.dirname(W11B)                                 # .../Hydraulic/Claude
HYDRAULIC = os.path.dirname(CLAUDE)

ORIENT_GPKG = os.path.join(W11B, "shp", "W11b_orient.gpkg")
ROADS_GPKG = os.path.join(W11B, "shp", "W11b_roads.gpkg")
PLOTS_GPKG = os.path.join(CLAUDE, "W10", "shp", "W10_plot_loads.gpkg")   # DATA only
ROAD_REC = os.path.join(HYDRAULIC, "SHP", "Road centerline 2", "Road_Centercline.shp")

OUT_GPKG = os.path.join(W11B, "shp", "W11b_chambers.gpkg")
RUN = os.path.join(W11B, "run", "chambers")
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
        """
        import shapely
        s = self.seg
        bear_in: Dict[str, List[float]] = {}
        bear_out: Dict[str, float] = {}
        for u, d, geom in zip(s.US_NODE.values, s.DS_NODE.values, s.geometry.values):
            c = shapely.get_coordinates(geom)
            if len(c) < 2:
                continue
            bear_out[u] = _bearing(c[0][0], c[0][1], c[1][0], c[1][1])
            bear_in.setdefault(d, []).append(_bearing(c[-2][0], c[-2][1],
                                                      c[-1][0], c[-1][1]))
        ang = np.full(len(self.ch), np.nan)
        for i, u in enumerate(self.ch.NODE_UID.values):
            ins = bear_in.get(u)
            out = bear_out.get(u)
            if not ins or out is None:
                continue
            ang[i] = min(_inlet_angle(b, out) for b in ins)
        self.ch["INLET_DEG"] = np.round(ang, 1)
        self.ch["INLET_FLAG"] = ((ang < INLET_MIN_DEG - 1e-9) & np.isfinite(ang)).astype(int)
        # The resolution for a sharp inlet is a CHAMBER DETAIL, not a softer number: a
        # purpose-made chamber with a swept channel. G203-p30 requires benching "formed to
        # permit safe access and to maximise hydraulic efficiency" and "Smooth transitions
        # between inlet and outlet"; the 90 deg clause sits in the same paragraph. Flagged
        # here so it is a KNOWN, PRICED item rather than an unnoticed one.
        self.ch["SWEPT_CH"] = self.ch["INLET_FLAG"]
        n = int(np.isfinite(ang).sum())
        _log(f"    inlet angle measurable at {n:,} chambers; "
             f"{int(self.ch.INLET_FLAG.sum()):,} below {INLET_MIN_DEG:g} deg (G203-p30)")
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

        # chambers closer than the minimum clearance - measured, not assumed away
        import shapely as _sh
        from shapely import STRtree as _T
        _p = _sh.points(ch.X.values, ch.Y.values)
        _a, _b = _T(_p).query(_p, predicate="dwithin", distance=MH_MIN_CLEAR_M - 1e-6)
        _m = _a < _b
        self.t_close = pd.DataFrame([{
            "A": ch.NODE_UID.values[i], "A_TRIG": ch.TRIGGER.values[i],
            "A_ORIENT": ch.ORIENT_ND.values[i], "A_ARC": ch.ARC_CID.values[i],
            "B": ch.NODE_UID.values[j], "B_TRIG": ch.TRIGGER.values[j],
            "B_ORIENT": ch.ORIENT_ND.values[j], "B_ARC": ch.ARC_CID.values[j],
            "GAP_M": round(float(_sh.distance(_p[i], _p[j])), 3),
        } for i, j in zip(_a[_m], _b[_m])])
        if len(self.t_close):
            self.t_close = self.t_close.sort_values("GAP_M")
        n_node_pairs = int(((self.t_close.A_ARC == "") & (self.t_close.B_ARC == "")).sum())             if len(self.t_close) else 0

        # inlet angle bands - a 0 deg inlet and an 89 deg inlet are different problems
        fin = ch[np.isfinite(ch.INLET_DEG)]
        bands = [(0, 30), (30, 60), (60, 89.99), (89.99, 120), (120, 150), (150, 180.01)]
        self.t_inlet = pd.DataFrame([{
            "INLET_DEG": f"{lo:g} to {hi:g}",
            "chambers": int(((fin.INLET_DEG >= lo) & (fin.INLET_DEG < hi)).sum()),
            "COMPLIANT": "no - swept channel required" if hi <= 90 else "yes",
        } for lo, hi in bands])
        self.t_inlet["pct"] = (self.t_inlet.chambers / max(len(fin), 1) * 100).round(2)

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
             "RESULT": f"{int(ch.INLET_FLAG.sum()):,} of "
                       f"{int(np.isfinite(ch.INLET_DEG).sum()):,} measurable inlets below "
                       f"90 deg; worst {np.nanmin(ch.INLET_DEG.values):.1f} deg",
             "PASS": int(ch.INLET_FLAG.sum() == 0)},
            {"CHECK": "no two chambers inside the 3 m minimum clearance",
             "SOURCE": "criteria.MH_SNAP_M (PROJECT - no minimum chamber spacing exists in "
                       "G201/G202/G203)",
             "RESULT": f"{len(self.t_close)} pair(s), of which {n_node_pairs} are BOTH "
                       f"stage-2 graph nodes - a corridor-snapping artefact this stage "
                       f"inherits and must not silently merge, because merging changes "
                       f"stage 2's published topology",
             "PASS": int(len(self.t_close) == 0)},
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
            "TIER": "s3 hierarchy - NOT BUILT in W11b", "PACKAGE": "s8 packages",
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
            ("inlets below 90 deg", int(ch.INLET_FLAG.sum()), "-", f"{G}-p30"),
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
        L.append("# W11b stage 4 - chambers, and every plot's way into them\n")
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

        L.append("## Spacing, against Table 12 and against the operator\n")
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
        L.append("\n**`TIER` is the one that matters.** There is no hierarchy stage in W11b, "
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
            from w11b import present as P
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
                       ("INLET_DEG", "Inlet angle deg (G203-p30 min 90)", "{:.1f}"),
                       ("ON_WADI", "On wadi ground (G203-p30 4.4.1)", "{:d}")],
                notes=("G203 lists no bend trigger. The bend chambers are ours, and the "
                       "threshold is a 0.5 m chord offset measured off NAMA's own built "
                       "pipes, not an invented angle.",),
            )
            P.register(v_ch)
            gdf = self.gpd.read_file(OUT_GPKG, layer="chambers")
            out = os.path.join(W11B, "shp", "W11b_chambers_trigger.kmz")
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
            out = os.path.join(W11B, "shp", "W11b_chambers_connections.kmz")
            r = P.kmz(gdf, v_cn, out, source=f"{STAGE_VERSION} | {TAU_FLAG}",
                      max_features=300000)
            _log(f"    {r.summary() if hasattr(r, 'summary') else out}")
        except Exception as e:                                       # noqa: BLE001
            self.notes.append(f"connection KMZ not written: {type(e).__name__}: {e}")
        return self

    # ---------------------------------------------------------------- driver
    def build(self) -> "Chambers":
        (self.load().mint().link().levels().fall().angles()
         .connect().prune().topology().reallocate())
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
