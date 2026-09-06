"""W12 stage 2 - THE DRAINAGE TREE, BUILT DOWNHILL BY CONSTRUCTION.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
`W11a/py`.  The only imports from inside the project are `w12.criteria`, `w12.terrain`,
`w12.asbuilt` and `w12.contract`, which are W12's own, plus `w12.present` for the KMZ.
Earlier folders are read for DATA only.

WHAT THIS STAGE DECIDES, AND WHAT IT DOES NOT
It decides, for every corridor in `W12/shp/W12_roads.gpkg`, WHICH WAY THE SEWAGE RUNS,
and which corridor each junction discharges through.  It does not mint chambers, does not
set inverts, does not size a pipe and does not site a pumping station.  What it publishes
for the levelling stage is an EARLY WARNING: per sub-network, the ground fall that is
actually available against the fall the tree demands at the flattest legal gradient.

WHY THE PREVIOUS METHOD FAILED
W11a assigned territory by Dijkstra and then routed top-down.  Adverse grade was paid for
AFTER the fact, in depth and in drop structures: 42.5 % of 1,731.7 km draining uphill and
2,449 vortex drop shafts where NAMA's built network has 37.  A shortest-path tree has no
term that prefers downhill, so it has no reason to find it.

WHAT IS DONE INSTEAD
A MINIMUM-COST DIRECTED SPANNING TREE - an optimum branching, Chu-Liu / Edmonds / Tarjan -
over arc weights that make downhill cheap.  Each junction takes exactly ONE outgoing arc
(philosophy sec 4), which is precisely the arborescence constraint, so the tree is biased
downhill BY CONSTRUCTION rather than corrected afterwards.

THE ALGORITHM, AND HOW IT WAS CONFIRMED
`networkx.minimum_spanning_arborescence` is the reference implementation and it is what
this file is checked against - but it could not be used to PRODUCE the answer.  Measured on
this machine, networkx's Edmonds costs 0.14 s at 197 nodes, 0.64 s at 401, 3.0 s at 785 and
21.1 s at 1,601: an empirical exponent of about 2.1 on the node count, which extrapolates to
roughly a quarter of an hour for the 9,600-node corridor graph, per solve, before any sweep
or iteration.  So `msa_edges()` here is a vectorised Chu-Liu/Edmonds - the public algorithm,
written out, not copied from any repository - and `verify_msa_against_networkx()` asserts
that it returns the SAME OPTIMUM VALUE as networkx on 30 random graphs and on a real
sub-graph of these corridors.  It solves the full graph in about 3.5 s.

NOTE ON ORIENTATION.  networkx's `arborescence` points edges AWAY from the root (every node
has in-degree <= 1).  A sewer is the mirror image: every node has out-degree exactly 1 and
the arcs converge on the outfall.  The graph handed to the solver is therefore REVERSED -
an arc is added as (downstream, upstream) - and flipped back on the way out.  Getting this
backwards produces a tree that looks fine and drains outwards from the works.

THE WEIGHTS - four terms, each declared, each published per arc
Every term is in EQUIVALENT METRES OF PIPE, so they can be added and the total read.

  W_LEN     = L                          the arc's own length.
  W_SLOPE   = L * S,  S in [0, SLOPE_CAP].  S is the Chahinian-style interpolation the
              brief asks for, anchored on the guideline: S = 0 where the ground already
              falls at least as fast as a DN200 must be laid (5.00 mm/m, G203-p29 Tab 11),
              S = 0.5 on dead-flat ground, S = 1 where the ground RISES at that same rate,
              and on beyond, capped.  It is exactly the DEPTH DEBT the arc buys, rescaled:
              debt rate = max(0, Smin - s) metres of extra depth per metre of pipe.
              THEN SHRUNK BY THE MEASURED CONFIDENCE.  The terrain decides the direction of
              a short reach only about one time in five, and NAMA's own surveyed levels
              agree with the direction their pipes run only 65 % of the time.  So S is pulled
              toward its neutral 0.5 by the MEASURED sign-agreement curve in the terrain
              manifest: S_used = 0.5 + (S_raw - 0.5) * (2p - 1), p = the probability that a
              fall of this size gives the right sign.  Where the ground cannot say, both
              directions cost the same and the slope term drops out of the decision instead
              of injecting noise into it.  That is the honest treatment of fact 1.
  W_DETOUR  = max(0, d(down) - d(up) + L), d = shortest-length distance to the nearest
              outfall.  Zero on an arc that lies on a shortest path; otherwise the extra
              metres to the works the arc creates.  THIS TERM WAS NOT IN THE BRIEF AND IT IS
              HERE BECAUSE THE MEASUREMENT DEMANDED IT.  An optimum branching minimises the
              SUM of arc costs and has no term at all for how far any one property's sewage
              then has to travel; with length alone the median flow path came out at 6.4 km
              and the longest at 31 km, against 2.3 km and 13.7 km for the tree it replaces.
              A tree that halves the uphill share and triples the flow path has moved the
              problem, not solved it.  The coefficient is swept and published.
  W_BEND    = BEND_EQUIV_M * (1 - inlet_angle/90 deg), zero at or above 90 deg.
              A turn happens between TWO arcs at a chamber and an arborescence weight can
              only see ONE arc, so this cannot be solved in a single pass; it is applied by
              re-weighting and re-solving, and the sharp-inlet count after each pass is
              published so the reader can see whether it converged.  Said plainly: the bend
              term is the weakest of the four and it is reported, not claimed.

HOW THE TWO COEFFICIENTS WERE CHOSEN, AND WHY NOT BY A FORMULA
Slope and detour pull against each other and there is no exchange rate between a percentage
point of uphill length and a kilometre of flow path that would not be invented.  So they are
not scalarised.  A 36-point grid is solved, the PARETO-OPTIMAL settings on (uphill share,
95th-percentile flow path) are marked, the whole front is published in `sweep_grid`, and the
shipped default is the knee of it.  Measured, the front runs from 26.6 % uphill at a 17.3 km
95th-percentile flow path to 44.6 % at 7.2 km; the naive tree sits at 46.6 % / 7.2 km.
Both ends are legal and the choice along the front is the engineer's, which is why it is
published as a table and not buried in a constant.

THE OUTFALL RULE (engineer 2026-09-05/06; philosophy sec 9) - THE MOST IMPORTANT CHANGE IN
W12, AND EVERYTHING DOWNSTREAM DEPENDS ON IT

    "A subnetwork joins the main pipe at the LOWEST POINT WHERE IT MEETS it.
     NO SUBNETWORK CROSSES THE MAIN PIPE AND GROWS PAST IT."

W11b could not obey it because it asked the question of the wrong object.  `find_roots` asks
whether a NODE is close to the trunk.  A corridor can cross the trunk, or run a metre from
it, with neither of its two nodes anywhere near - a 200 m street crossing at its midpoint has
both ends 100 m away.  Measured on W11b's own shipped `arcs` layer: 214 arcs, 48.49 km,
physically CROSS the Main Pipe, and 397 come within 3 m of it where only 193 NODES did.  Each
of those is a flow path that reaches the trunk, ignores it and grows out the other side, and
it is how two subnetworks came to hold a quarter of the whole network - 7,871 and 6,271
chambers - while touching the trunk at 1.1 m and 3.1 m and discharging somewhere else.
Re-measured here on the same file: 39 subnetworks discharge with more than half their
catchment BELOW the outlet, 517.9 km, worst outlet 26.34 m above its own low point.

Three things fix it, in this order:

  1  `meet_main_pipe()` moves the test from the NODE to the CORRIDOR.  Wherever a corridor
     crosses the Main Pipe, runs along it, or passes within MEET_TOL_M of it, a node is
     inserted and the corridor cut there.  Nothing is deleted and no length is lost - the
     equality is asserted, not asserted about.  MEET_TOL_M is DERIVED: it is
     `criteria.MH_SNAP_M`, the node-merge radius `s1_roads` used to node the whole corridor
     graph.  Two positions closer than that are ONE node in the published topology.  It
     replaced a 5.0 m project number chosen by eye, because a tolerance that decides where a
     network discharges may not be invented.
  2  every such node is an outfall (`find_roots` asserts it), so a flow path arriving at the
     trunk DISCHARGES instead of crossing - and every place a catchment meets the trunk is
     now a candidate outlet, which is what "the lowest point where it MEETS it" needs in
     order to be a choice at all.
  3  `reroot_below_outfall()` then MAKES that choice.  A node sitting below the outfall it
     drains to has its branch re-pointed to a neighbouring subnetwork whose outfall is at or
     below it, bounded by the built network's own detour ratio (4.0,
     `_BRAIN/10_ASBUILT_CALIBRATION.md` sec 1).  Because the new outfall is lower, the
     below-outlet length is monotone non-increasing, so the loop provably terminates; it
     stops the moment a pass moves nothing and the per-pass table is published.

EXPECT THE SUBNETWORK COUNT TO RISE SUBSTANTIALLY.  That is correct and approved: "more
subnetworks worth keeping the work clean, rather than monster useless subnetworks".

MEASURED, on W11b's own data, before this stage is re-run end to end:
  * the cut takes corridors meeting the trunk with no node on the meeting point from
    229 to 0, in one round, with the corridor length, plot count and load identical to
    within a millimetre (12,664 -> 12,949 corridors, 285 new nodes: 192 crossings and
    93 approaches inside the merge radius);
  * re-rooting alone, on W11b's published tree and its 193 outfalls - so without any of
    the new meeting points - takes the length draining up to its own outlet from
    438.6 km to 184.2 km, converging in 17 passes and 1.1 s, with the forest intact.
Both figures are recomputed on every build; these are what they were when it was written.

WHAT IS PUBLISHED PER SUBNETWORK: the outfall, its true LOW_NODE and LOW_Z, HEAD_M (how far
the outlet sits above that low point), JOIN_OFF_M (the flow-path distance from it),
JOIN_WHY, BELOW_KM and BELOW_PCT.  And per arc, `X_MAIN` - recomputed from the geometry about
to be written, never carried from the pass that made it - which must be 0 everywhere.

`reroot_below_outfall` is the general form of inheritance-ledger row 4: ANYTHING A PASS CAN
ADD, A LATER PASS MUST BE ABLE TO TAKE AWAY, AND THE STAGE PUBLISHES HOW MANY IT REMOVED.
The branching only ever ASSIGNS a node to the outfall its weights liked; this takes the
assignment away where the ground says it was wrong, and prints the count.

ROOTS.  The outfalls are the corridor nodes that touch the client's Main Pipe, which is an
INPUT (`SHP/Main Pipe/Main Pipe.shp`, 85.49 km) and is never derived.  Every node within
MEET_TOL_M of it is taken, including every node `meet_main_pipe` minted.  The intention had been to price a join so the count stayed near
NAMA's built 21 - until the RATE was checked: NAMA make 4.64 joins per km of their own
trunk, and 193 joins on 85.49 km is 2.26 per km, less than half that.  There is no evidence
for suppressing joins on this trunk, so JOIN_COST_M is 0 and the parameter is swept rather
than tuned.  A super-root is added with one arc to each candidate, which lets the branching
partition the network into sub-networks AND orient them in one solve.

CLOSED BASINS are not roots here.  `terrain.py` finds 59 real closed basins in the study
area and `PUMP_FORCED` is False on every one of them - the deepest is 7.83 m against the
12 m cover cap (G203-p33) - so not one of them is a basin that cannot be drained out.  The
test is run and the answer published rather than assumed.

THE RIDGE RULE.  A corridor whose profile has a genuine interior crest cannot be drained in
one direction: whichever end it points at, half of it climbs.  Where such a corridor is
LONGER than the built network's own median run between junctions - 68.74 m, measured by
`asbuilt.m_runs()`, not a number anyone picked - it is cut at the crest and a node inserted,
and the branching then decides each half for itself.  Shorter than that, it stays in one
piece and drains to its lower end, because splitting a 40 m street buys two stubs and an
extra junction for nothing.  A crest counts only if it rises more than 3 x the DEM's MEASURED
differential error (3 x 0.4769 = 1.431 m), so a ridge is never an artefact of the surface.

THE ARCS THE TREE DOES NOT USE.  A spanning tree of 9,743 reachable nodes uses 9,550 arcs
after the joins are taken out; the corridor graph has 12,815 after the ridge pre-split.  The
other 3,081 - 642.1 km - close loops, and the network must be a FOREST (H15).
They are not deleted - the streets are still there and the plots on them still need a sewer.
Each becomes a HEAD: a dead-end run entering the network at one end only, draining to its
LOW end, its start set back FANOUT_OFFSET_M (10 m) from the chamber it would otherwise
double-outlet.  Where such a corridor straddles a crest and is long enough, it is cut and
becomes TWO heads draining both ways - which is the ridge rule finishing the job.  So 100 %
of the corridor length is oriented and drained, and the headline uphill share is quoted over
the WHOLE published network, which is what W11a's 42.5 % was quoted over.

WHAT IS MEASURED AND PUBLISHED (see `run/orient/ORIENTATION.md` and the `compare` table)
Four trees are built on the SAME graph, because the comparison is the evidence:
  A  naive shortest-path tree on LENGTH             - the method this replaces
  B  optimum branching on LENGTH only               - isolates the ALGORITHM
  C  shortest-path tree on the slope-weighted cost  - isolates the WEIGHTS
  D  optimum branching on the slope-weighted cost   - both, and the deliverable
and the uphill share, cumulative climb, join count and flow-path distribution are reported
for all four.

WHAT THIS STAGE CANNOT DO, STATED PLAINLY
A graph algorithm cannot enforce a hydraulic constraint.  Minimum gradient is DIAMETER
dependent (G203-p29 Tab 11), minimum cover is 1.30 m and maximum cover 10-12 m (G203-p33),
and none of the three is a function of one arc.  The branching hands the levelling stage a
TREE; the levelling stage will still find it infeasible in places.  What is published here
to make that visible EARLY is, per sub-network and per node, the ground fall AVAILABLE
against the fall the tree DEMANDS at the flattest legal gradient - and the workable depth
budget between them, MAX_COVER - MIN_COVER = 10.70 m.

AND THE FLATNESS IS NOT A TREE PROBLEM AT ALL.  58.4 % of the corridor network - 1,062.7 km,
re-measured here after the ridge pre-split against the 60 % / 1,098.8 km measured before it -
lies on ground falling more gently than the minimum gradient a DN200 may be laid at.  There
the pipe sinks below the surface whichever way it points, and no tree fixes it.  A better
tree helps with the decidable fraction and nothing else; this file measures what it actually
achieves and claims nothing beyond it.

WHAT IT ACTUALLY ACHIEVED, MEASURED (2026-09-03, and re-measured on every run - the manifest
is the authority and this is a summary of it)

    23.15 % of the published 1,819.4 km drains against the ground, 414.0 km.  W11a published
    42.5 %; NAMA's built network runs 34.10 % uphill.  THE SAME GRAPH WITH THE METHOD W11a
    USED, on the same basis, gives 33.13 % - so the honest improvement is 10.0 percentage
    points, not the 19 the raw comparison with W11a would suggest.  Over the tree arcs
    alone, excluding the dead-end heads that drain to their low end by construction, the
    figure is 36.11 % against the naive tree's 46.62 %.
    Cumulative climb 2,451 m against 9,507 m of descent - 1.37 m of climb per km of sewer,
    against the built network's 4.06.
    151 corridors cut at a crest; 193 outfalls; 193 sub-networks; 2,887 heads that the
    chamber stage must set back 10 m; 2,104 of 9,360 inlets still under 90 deg.
    AND THE UNCOMFORTABLE ONE: 3,619 of 9,743 nodes demand more fall than the ground gives
    by more than the 10.70 m depth budget, 999 of them even at Table 11's flattest legal
    gradient.  Asking the neighbours first - philosophy sec 5's cheap step - rescues 158.
    The rest is where pumping starts, and it is a flatness problem, not a tree problem.

RUN
    python s2_orient.py build          the whole stage
    python s2_orient.py verify         re-read what was written and re-derive the headline
    python s2_orient.py selftest       the algorithm proof against networkx
    python s2_orient.py sweep          the weight sensitivity tables, nothing published
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../W12/py
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from w12 import criteria as CR                              # noqa: E402
from w12 import terrain as T                                # noqa: E402
from w12 import asbuilt as AB                               # noqa: E402

C = CR.DEFAULT

STAGE = "s2_orient"
STAGE_VERSION = "W12-orient-1.1-outfall"

# ================================================================== paths
W12 = os.path.dirname(_HERE)                                # .../W12
CLAUDE = os.path.dirname(W12)                               # .../Hydraulic/Claude
HYDRAULIC = os.path.dirname(CLAUDE)

ROADS_GPKG = os.path.join(W12, "shp", "W12_roads.gpkg")
MAIN_PIPE = os.path.join(HYDRAULIC, "SHP", "Main Pipe", "Main Pipe.shp")
ROAD_REC = os.path.join(HYDRAULIC, "SHP", "Road centerline 2", "Road_Centercline.shp")
# the recorded road centrelines, read here for ONE purpose: to re-measure H1 on the pieces
# this stage CUTS. See _remeasure_dual() for why inheriting the flag is not enough.
OUT_GPKG = os.path.join(W12, "shp", "W12_orient.gpkg")
RUN = os.path.join(W12, "run", "orient")
REPORT_MD = os.path.join(RUN, "ORIENTATION.md")
MANIFEST_JSON = os.path.join(RUN, "orient_manifest.json")

CRS_EPSG = 32640                     # project rule; every layer, no exceptions

# ================================================================== constants
# Every value below is a guideline number with its page, a value MEASURED in this project,
# or a PROJECT choice that says so.  Nothing here is invented.

# --- guideline ---------------------------------------------------------------------------
SMIN_DN200 = C.TABLE11[200]          # 0.00500 m/m. G203-p29 Tab 11, DN200 row: 5.00 mm/m.
#                                      The STEEPEST minimum in the table, so the flattest
#                                      ground a DN200 can be laid on without digging.
SMIN_FLOOR = C.TABLE11_FLOOR         # 0.00075 m/m. G203-p29, the "900 and above" row. The
#                                      flattest gradient any pipe in Table 11 may be laid at.
MIN_COVER_M = C.MIN_COVER_CROWN      # 1.30 m. G203-p33 sec 4.6.3.
MAX_COVER_M = C.MAX_COVER            # 12.00 m. G203-p33 sec 4.6.3 (recommended 10-12 m).
DEPTH_BUDGET_M = MAX_COVER_M - MIN_COVER_M      # 10.70 m of workable depth, by subtraction
INLET_MIN_DEG = C.INLET_MIN_DEG      # 90 deg. G203-p30, verbatim.
FANOUT_OFFSET_M = C.FANOUT_OFFSET_M  # 10 m. Project rule (user 2026-08-18): a branch leaving
#                                      a chamber that already has an outlet starts 10 m away.
ADVERSE_MIN_M = C.ADVERSE_MIN_M      # 0.05 m. PROJECT ASSUMPTION - below this a "rise" is
#                                      DEM noise, and counting it inflates the headline.

# --- measured ----------------------------------------------------------------------------
# Filled at run time from asbuilt.py and the terrain manifest so they cannot go stale.
# The values in the comments are what they measured on 2026-09-03.
#   RUN_MEDIAN_M      68.74 m   asbuilt.m_runs()['run_between_junctions_median_m']
#   SIGMA_DZ_M        0.4769 m  terrain manifest, differential error vs NAMA surveyed levels
#   BUILT_UPHILL_PCT  34.10 %   asbuilt.m_terrain()['uphill_length_pct']
#   BUILT_JOINS       21        asbuilt._zone_drainage()['joins_onto_trunk']
W11A_UPHILL_PCT = C.BENCHMARKS["UPHILL_SHARE_W11A"][0] * 100.0     # 42.5 %

# --- project choices, all swept and published --------------------------------------------
LAMBDA_SLOPE = 3.0        # PROJECT. Weight on the slope term. An arc that climbs at the
#                           DN200 minimum costs 4x a favourable one of the same length; a
#                           dead-flat one 2.5x. Swept 0-8: see `sweep_lambda`.
SLOPE_CAP = 4.0           # PROJECT. The slope factor stops growing past a climb of
#                           7 x SMIN_DN200 = 3.5 %. Beyond that every adverse arc is equally
#                           bad and the other terms decide.
LAMBDA_DETOUR = 1.0       # PROJECT, and forced by measurement - see the docstring. Swept.
LAMBDA_BEND = 1.0         # PROJECT. Multiplier on BEND_EQUIV_M.
BEND_EQUIV_M = 150.0      # PROJECT. A 0 deg inlet - flow doubling back on itself - costs the
#                           same as 150 m of extra pipe. About two median built runs.
BEND_PASSES = 3           # PROJECT. Re-weight and re-solve this many times; the sharp-inlet
#                           count after each pass is published.
JOIN_COST_M = 0.0         # MEASURED, not chosen.  A connection onto the client's Main Pipe
#                           was going to be priced in equivalent metres to keep the join
#                           count near NAMA's built 21 - until the rate was checked: NAMA
#                           make 4.64 joins per km of their own trunk (asbuilt), and taking
#                           EVERY one of the 193 candidate nodes gives 2.26 per km of the
#                           85.49 km Main Pipe, less than half the built density.  There is
#                           no evidence for suppressing joins, so none are suppressed and
#                           the parameter is set to zero rather than tuned.  Swept anyway.
# --- the OUTFALL RULE (engineer, 2026-09-05/06; philosophy sec 9) -------------------------
# "A subnetwork joins the main pipe at the LOWEST POINT WHERE IT MEETS it.  No subnetwork
#  crosses the main pipe and grows past it."
#
# MEET_TOL_M is DERIVED, not chosen.  The word "meets" needs a distance and the project
# already has exactly one: `criteria.MH_SNAP_M`, the node-merge radius s1_roads used to node
# the whole corridor graph (`s1_roads.py`: "noding at MH_SNAP_M = 3 m").  Two positions
# closer than that are ONE node in the published topology, so a corridor passing within it
# of the Main Pipe already shares a node with the trunk in every sense the graph can
# express.  Anything larger is a SPUR - a real pipe, an engineer's decision - and the
# sensitivity of the whole answer to that decision is swept in `sweep_main_snap`.
MEET_TOL_M = C.MH_SNAP_M  # 3.0 m. DERIVED from criteria.MH_SNAP_M, the node-merge radius.
MAIN_SNAP_M = MEET_TOL_M  # the old name, kept so the sweep and the manifest still read.

# THE BUFFER'S OWN APPROXIMATION ERROR, NOT A WIDER TOLERANCE. `meet_main_pipe` selects
# with `main.buffer(MEET_TOL_M)` and an `intersects` predicate; `find_roots` then recomputes
# the same distance point-to-line. GEOS builds a buffer from STRAIGHT SEGMENTS, so its
# boundary sits slightly OUTSIDE the true 3.0 m offset - a point on the buffer edge can
# measure a few microns past the tolerance. MEASURED on the first W12 run: M000211 at
# 3.0000045 m and M000214 at 3.0000018 m, i.e. 4.5 and 1.8 microns over.
# 1 mm is 0.03 % of the tolerance - geometrically nothing against a 3 m radius derived from
# a manhole-merge distance, three orders above the error observed, and far too small to
# admit a node that genuinely fails the rule.
# THE COST OF NOT HAVING IT: those two nodes were minted as meeting points and then refused
# as roots, so TWO REAL OUTFALLS WERE SILENTLY LOST. It is applied to the ROOT SELECTION as
# well as to the assertion, deliberately - applying it only to the assertion would silence
# the check and still lose the outfalls, a green check over a real loss.
MEET_EPS_M = 1e-3
#                           WAS 5.0 m, a PROJECT number chosen by eye. Replaced 2026-09-06
#                           because a tolerance that decides where a network discharges may
#                           not be invented; the old value is still a row in the sweep.
MEET_PASSES = 4           # PROJECT, STRUCTURAL cap only. A cut can reveal a meeting point
#                           the uncut corridor hid, so the cut repeats until nothing is
#                           left; on the real corridor set it converges in ONE round (229
#                           corridors meeting the trunk off-node -> 0), and the per-round
#                           table is published so that is read rather than claimed.
REROOT_PASSES = 40        # PROJECT, and a STRUCTURAL cap rather than a design value: the
#                           re-rooting loop stops the moment a pass accepts no move, and the
#                           per-pass table is published so convergence is visible rather
#                           than claimed.  MEASURED on W11b's own published tree - 9,743
#                           nodes, 193 outfalls - it converges in 17 passes and 1.1 s,
#                           taking the below-outlet length 438.6 -> 184.2 km.  40 only
#                           bounds a case that does not converge; if the table ever shows
#                           the cap being hit, the monotonicity argument needs looking at.
DETOUR_RATIO_MAX = 4.0    # MEASURED BOUND, _BRAIN/10_ASBUILT_CALIBRATION.md sec 1: "Detour
#                           ratio | median 1.23, p90 2.26 | median <= 1.45, p90 <= 2.8,
#                           <= 5 % above 4.0".  The quantity is defined there per CHAMBER as
#                           its flow-path length to the outfall divided by its straight-line
#                           distance to it (W12/docs/ASBUILT_STUDY.md H10, 1,992 chambers),
#                           which is exactly what is computed here.  A re-root that lands a
#                           node past 4.0 is refused: it would buy a lower outlet with pipe
#                           nobody would build.  This is a REFUSAL BOUND, not the band - the
#                           band is a gate on the finished layout and belongs to s3.
BELOW_OUTLET_FAIL_PCT = 50.0   # the ENGINEER'S OWN diagnostic, quoted from the defect
#                           register (_BRAIN/00_CURRENT.md, "42 components discharge with
#                           MORE THAN HALF their catchment BELOW the outlet"). It is the
#                           threshold the defect was stated at, not one chosen here.

GRID = "R5"               # the 5 m working grid. terrain.py measured native 0.5 m sampling
#                           to be NO more accurate (SD 0.7564 vs 0.7561 m) and to give an
#                           identical drain direction on every decidable test line.

TAU_FLAG = f"tau={C.TAU_PA:g} Pa ASSUMED (GAP-9)"

# ---- H1 / project rule 7 on the arcs this stage cuts ----------------------------------
H1_CONSTANTS = ("DUAL_BAND_M", "DUAL_XING_SKEW_DEG", "IN_BAND_MIN_FRAC")
# The three numbers that decide whether a line runs ALONG a tagged dual carriageway: the band
# half-width, the tolerance on the word "square", and the share of a line that must be inside
# the band before it is judged at all.
#
# THEY ARE NOT DEFINED HERE.  They are stage 1's, declared and derived in `s1_roads.py`, and
# this stage READS them off the published `W12_roads.gpkg` manifest at run time - see
# `_h1_constants()`.  Copying the values would put two definitions of one quantity in the
# repo, which is the defect `tests/test_constants.py` exists for: a wall/bedding allowance
# was 0.10 in one module and 0.05 in another and every reach failed a BLOCKING cover check by
# exactly 50 mm.  Reading them means the two stages cannot drift, and the values actually
# used are re-published on this stage's own manifest so the run is self-describing.


def _h1_constants() -> dict:
    """The three H1 constants, read from stage 1's published manifest. One definition."""
    import sqlite3

    con = sqlite3.connect(ROADS_GPKG)
    try:
        m = pd.read_sql("SELECT * FROM manifest", con).set_index("ITEM")["VALUE"]
    finally:
        con.close()
    missing = [k for k in H1_CONSTANTS if k not in m.index]
    if missing:
        raise ValueError(
            f"stage 1's manifest does not publish {missing}, so this stage cannot re-measure "
            f"H1 on the pieces it cuts. A check that cannot run is a FAILURE, not a blank")
    return {k: float(m[k]) for k in H1_CONSTANTS}


def _log(msg: str) -> None:
    print(f"[{STAGE}] {msg}", flush=True)


def _md(df: pd.DataFrame, nd: int = 2, maxrows: Optional[int] = None) -> str:
    """A markdown table, written out here rather than pulling in `tabulate`.

    One dependency for one pipe-separated string is not worth adding to a pipeline someone
    else has to be able to run.
    """
    d = df if maxrows is None else df.head(maxrows)
    def cell(v):
        if isinstance(v, float):
            if not np.isfinite(v):
                return "-"
            return f"{v:,.{nd}f}"
        if isinstance(v, (int, np.integer)):
            return f"{int(v):,}"
        return str(v)
    cols = list(d.columns)
    body = [[cell(v) for v in row] for row in d.itertuples(index=False, name=None)]
    w = [max(len(str(c)), *(len(r[i]) for r in body)) if body else len(str(c))
         for i, c in enumerate(cols)]
    out = ["| " + " | ".join(str(c).ljust(w[i]) for i, c in enumerate(cols)) + " |",
           "|" + "|".join("-" * (w[i] + 2) for i in range(len(cols))) + "|"]
    for r in body:
        out.append("| " + " | ".join(r[i].ljust(w[i]) for i in range(len(cols))) + " |")
    return "\n".join(out)


def _write_table(df: pd.DataFrame, layer: str) -> None:
    """An attribute-only table, written INTO the GeoPackage and registered in
    `gpkg_contents` so QGIS lists it.

    Every measured table is published rather than printed: a number that lives only in a
    console log is a number nobody can check next month.
    """
    import sqlite3
    con = sqlite3.connect(OUT_GPKG)
    try:
        df.to_sql(layer, con, if_exists="replace", index=False)
        con.execute(
            "INSERT OR REPLACE INTO gpkg_contents "
            "(table_name, data_type, identifier, description, last_change, srs_id) "
            "VALUES (?, 'attributes', ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL)",
            (layer, layer, f"{STAGE_VERSION} measured table"))
        con.commit()
    finally:
        con.close()


def _sha1(path: str, n: int = 16) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


# ==========================================================================================
# THE ALGORITHM
# ==========================================================================================

def _line_parts(g) -> list:
    """LineString components of a geometry, flattened."""
    if g is None or g.is_empty:
        return []
    t = g.geom_type
    if t == "LineString":
        return [g]
    if t in ("MultiLineString", "GeometryCollection"):
        out = []
        for p in g.geoms:
            out.extend(_line_parts(p))
        return out
    return []


def _point_parts(g) -> list:
    """Point components of a geometry, flattened."""
    if g is None or g.is_empty:
        return []
    t = g.geom_type
    if t == "Point":
        return [g]
    if t in ("MultiPoint", "GeometryCollection"):
        out = []
        for p in g.geoms:
            out.extend(_point_parts(p))
        return out
    return []


def meet_points(g, main, buf, tol: float) -> List[Tuple[float, str]]:
    """WHERE A CORRIDOR MEETS THE MAIN PIPE - the one definition, used twice.

    Returns (along-distance, kind) for every place `g` meets `main`:

        crosses      it passes through the trunk - the point of intersection
        along        it runs ON the trunk for a stretch - the TWO ENDS of that stretch, not
                     its middle.  A node at the middle leaves half the stretch on the trunk
                     on either side of it and the next pass cuts those in half again; nodes
                     at the ends isolate the on-trunk stretch as one corridor whose two
                     nodes are both outfalls, which is what it physically is.
        within_tol   it never touches but comes within `tol` - the point of CLOSEST
                     approach in that stretch, one per contiguous approach

    ONE function, because the pass that CUTS the corridors and the check that says whether
    any got past must be asking the same question.  Two definitions of "meets" is how a
    stage comes to satisfy its own validator while breaking the rule.
    """
    if g is None or g.is_empty or g.length <= 0:
        return []
    here: List[Tuple[float, str]] = []
    try:
        hit = g.intersection(main)
    except Exception:                                              # pragma: no cover
        hit = g.intersection(main.buffer(0))
    from shapely.geometry import Point as _Pt
    for p in _point_parts(hit):
        here.append((float(g.project(p)), "crosses"))
    for seg in _line_parts(hit):
        if len(seg.coords) < 2:
            continue
        here.append((float(g.project(_Pt(seg.coords[0]))), "along"))
        here.append((float(g.project(_Pt(seg.coords[-1]))), "along"))
    # ...and then every contiguous stretch inside the tolerance that does NOT already carry
    # one of the points above.  Doing this only when there are no crossings at all - which
    # is what the first draft did - hides every close approach on a corridor that also
    # crosses somewhere else, and those are real: measured on the built corridor set, four
    # corridors ran within the merge radius of the trunk for hundreds of metres and were
    # invisible because they happened to cross it once as well.
    from shapely.ops import nearest_points
    from shapely.geometry import Point
    for seg in _line_parts(g.intersection(buf)):
        if seg.is_empty or len(seg.coords) < 2:
            continue
        a = float(g.project(Point(seg.coords[0])))
        b = float(g.project(Point(seg.coords[-1])))
        lo, hi = (a, b) if a <= b else (b, a)
        if any(lo - tol <= at <= hi + tol for at, _k in here):
            continue
        p = nearest_points(seg, main)[0]
        here.append((float(g.project(p)), "within_tol"))
    return sorted(here, key=lambda t: t[0])


def meets_without_a_node(g, main, buf, tol: float) -> int:
    """How many places `g` meets the Main Pipe with NO node of its own within `tol`.

    THIS IS THE INVARIANT, and it must be 0 on every drained arc.  A crossing WITH a node on
    it is a legal junction - the node is an outfall, so the flow discharges there and does
    not continue.  A crossing with no node on it is a flow path that reaches the trunk,
    ignores it and grows out the other side, which is exactly what the outfall rule forbids.

    Stated on the along-distance to the arc's OWN ends, because those ends are its nodes.
    """
    pts = meet_points(g, main, buf, tol)
    if not pts:
        return 0
    L = float(g.length)
    return int(sum(1 for at, _k in pts if tol < at < L - tol))


def msa_edges(n: int, U, V, W, root: int) -> np.ndarray:
    """Minimum spanning arborescence: Chu-Liu / Edmonds, vectorised.

    `U[i] -> V[i]` with weight `W[i]`, arcs pointing AWAY from `root` (so every node other
    than the root ends with exactly one INCOMING arc).  Returns the indices of the chosen
    arcs.  Raises ValueError if no spanning arborescence exists, naming how many nodes are
    unreachable - it never returns a partial tree, because a partial tree published as a
    whole one is how a network ends up in 7,919 pieces.

    The method is the textbook one and is written out here rather than taken from any
    repository: take each node's cheapest incoming arc; if that choice has no cycle it is
    optimal; otherwise contract every cycle, reduce the weight of each arc entering a
    contracted cycle by the weight of the arc it would displace, and repeat.  Correctness is
    asserted against `networkx.minimum_spanning_arborescence` in
    `verify_msa_against_networkx()`; networkx is the oracle, not the engine, because it is
    about 250x too slow at this size (see the module docstring).
    """
    U = np.asarray(U, dtype=np.int64)
    V = np.asarray(V, dtype=np.int64)
    W = np.asarray(W, dtype=np.float64)
    eid = np.arange(U.size, dtype=np.int64)
    keep = (U != V) & (V != root)          # self-loops, and anything draining INTO the root
    U, V, W, eid = U[keep], V[keep], W[keep], eid[keep]

    stack: List[dict] = []
    cur_n, cur_root = int(n), int(root)
    while True:
        # cheapest incoming arc per node
        order = np.lexsort((W, V))
        Vs = V[order]
        first = np.ones(Vs.size, dtype=bool)
        first[1:] = Vs[1:] != Vs[:-1]
        sel = order[first]
        inedge = np.full(cur_n, -1, dtype=np.int64)
        inedge[V[sel]] = sel
        miss = np.nonzero(inedge < 0)[0]
        miss = miss[miss != cur_root]
        if miss.size:
            raise ValueError(f"no spanning arborescence: {miss.size} nodes have no path "
                             f"from the root")

        # cycles of the functional parent map
        par = np.where(inedge >= 0, U[np.maximum(inedge, 0)], np.arange(cur_n))
        par[cur_root] = cur_root
        colour = np.zeros(cur_n, dtype=np.int8)          # 0 unseen, 1 on stack, 2 closed
        cyc_of = np.full(cur_n, -1, dtype=np.int64)
        ncyc = 0
        for s in range(cur_n):
            if colour[s]:
                continue
            path, v = [], s
            while colour[v] == 0:
                colour[v] = 1
                path.append(v)
                v = par[v]
            if colour[v] == 1:
                k = path.index(v)
                if len(path) - k >= 2:       # a one-node "cycle" is the root's own self-link
                    for m in path[k:]:
                        cyc_of[m] = ncyc
                    ncyc += 1
            for m in path:
                colour[m] = 2

        if ncyc == 0:
            stack.append(dict(n=cur_n, inedge=inedge, eid=eid, V=V,
                              cyc_of=cyc_of, root=cur_root))
            break

        super_of = np.empty(cur_n, dtype=np.int64)
        free = cyc_of < 0
        n_free = int(free.sum())
        super_of[free] = np.arange(n_free)
        super_of[~free] = n_free + cyc_of[~free]
        stack.append(dict(n=cur_n, inedge=inedge, eid=eid, V=V,
                          cyc_of=cyc_of, root=cur_root))

        w_in = np.where(inedge >= 0, W[np.maximum(inedge, 0)], 0.0)
        W = W - np.where(cyc_of[V] >= 0, w_in[V], 0.0)
        U, V = super_of[U], super_of[V]
        keep = U != V
        U, V, W, eid = U[keep], V[keep], W[keep], eid[keep]
        cur_root = int(super_of[cur_root])
        cur_n = n_free + ncyc

    # expand, outermost contraction last
    top = stack[-1]
    picked = [e for v, e in enumerate(top["inedge"]) if v != top["root"] and e >= 0]
    chosen = set(int(top["eid"][e]) for e in picked)
    for lvl in range(len(stack) - 2, -1, -1):
        L = stack[lvl]
        cyc_of, inedge, eidl, Vl = L["cyc_of"], L["inedge"], L["eid"], L["V"]
        head_of = {int(eidl[i]): int(Vl[i]) for i in range(eidl.size)}
        entered = {}
        for e in chosen:
            v = head_of.get(e)
            if v is not None and cyc_of[v] >= 0:
                entered[int(cyc_of[v])] = v
        for v in range(L["n"]):
            c = int(cyc_of[v])
            if c >= 0 and entered.get(c) != v and inedge[v] >= 0:
                chosen.add(int(eidl[inedge[v]]))
    return np.array(sorted(chosen), dtype=np.int64)


def spt_edges(n: int, U, V, W, root: int) -> np.ndarray:
    """Shortest-path tree from `root` - the BASELINE, and the method W11a used.

    Same signature and same orientation as `msa_edges`, so the two are interchangeable and
    the comparison is like for like.  Dijkstra via scipy; every node takes the arc on its
    cheapest path from the root rather than its cheapest arc.
    """
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    U = np.asarray(U, dtype=np.int64)
    V = np.asarray(V, dtype=np.int64)
    W = np.asarray(W, dtype=np.float64)
    M = csr_matrix((W, (U, V)), shape=(n, n))
    _, pred = dijkstra(M, indices=int(root), return_predecessors=True, directed=True)
    best: Dict[Tuple[int, int], int] = {}
    for i in range(U.size):
        k = (int(U[i]), int(V[i]))
        if k not in best or W[i] < W[best[k]]:
            best[k] = i
    out = []
    for x in range(n):
        p = pred[x]
        if p < 0:
            continue
        i = best.get((int(p), int(x)))
        if i is not None:
            out.append(i)
    return np.array(sorted(out), dtype=np.int64)


def verify_msa_against_networkx(trials: int = 12, seed: int = 11,
                                real_subgraph: Optional[dict] = None,
                                verbose: bool = True) -> bool:
    """Assert that `msa_edges` finds the SAME OPTIMUM as networkx.

    networkx is the reference implementation of exactly this algorithm.  It is used here as
    an ORACLE on problems small enough for it, which is the only honest way to rely on a
    hand-written optimiser: the brief says confirm the algorithm is what you think it is
    before relying on it, and an assertion is the only form of confirmation that survives a
    later edit.
    """
    import networkx as nx
    rng = np.random.default_rng(seed)
    ok = True
    for t in range(trials):
        k = int(rng.integers(4, 12))
        n = k * k
        E = []
        for i in range(k):
            for j in range(k):
                u = i * k + j
                for di, dj in ((0, 1), (1, 0)):
                    a, b = i + di, j + dj
                    if a < k and b < k:
                        v = a * k + b
                        E.append((u, v, float(rng.random())))
                        E.append((v, u, float(rng.random())))
        root = int(rng.integers(0, n))
        U = np.array([e[0] for e in E]); V = np.array([e[1] for e in E])
        W = np.array([e[2] for e in E])
        sel = msa_edges(n, U, V, W, root)
        mine = float(W[sel].sum())
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        for u, v, w in E:
            if v == root:
                continue
            if G.has_edge(u, v):
                G[u][v]["weight"] = min(G[u][v]["weight"], w)
            else:
                G.add_edge(u, v, weight=w)
        A = nx.minimum_spanning_arborescence(G, attr="weight")
        ref = float(sum(d["weight"] for _, _, d in A.edges(data=True)))
        good = abs(mine - ref) < 1e-9 and sel.size == n - 1
        ok &= good
        if verbose:
            print(f"  random n={n:4d}  ours {mine:.6f}  networkx {ref:.6f}  "
                  f"{sel.size}/{n-1} arcs  {'OK' if good else '*** MISMATCH ***'}")
    if real_subgraph is not None:
        n = real_subgraph["n"]
        U, V, W, root = (real_subgraph["U"], real_subgraph["V"],
                         real_subgraph["W"], real_subgraph["root"])
        t0 = time.time()
        sel = msa_edges(n, U, V, W, root)
        mine = float(np.asarray(W)[sel].sum())
        dt_ours = time.time() - t0
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        for i in range(len(U)):
            u, v, w = int(U[i]), int(V[i]), float(W[i])
            if v == root or u == v:
                continue
            if G.has_edge(u, v):
                G[u][v]["weight"] = min(G[u][v]["weight"], w)
            else:
                G.add_edge(u, v, weight=w)
        t0 = time.time()
        A = nx.minimum_spanning_arborescence(G, attr="weight")
        ref = float(sum(d["weight"] for _, _, d in A.edges(data=True)))
        dt_nx = time.time() - t0
        good = abs(mine - ref) < 1e-6
        ok &= good
        if verbose:
            print(f"  REAL corridor sub-graph n={n} edges={len(U)}  "
                  f"ours {mine:.3f} in {dt_ours:.2f} s  "
                  f"networkx {ref:.3f} in {dt_nx:.2f} s  "
                  f"({dt_nx / max(dt_ours, 1e-9):.0f}x)  "
                  f"{'OK' if good else '*** MISMATCH ***'}")
    return bool(ok)


# ==========================================================================================
# THE STAGE
# ==========================================================================================

@dataclass
class Tree:
    """One solved tree.  `arc` and `fwd` are parallel arrays over the tree's arcs."""
    name: str
    arc: np.ndarray          # index into the corridor table
    fwd: np.ndarray          # True  = flow runs US_NODE -> DS_NODE as drawn
    parent: Dict[int, int]   # node index -> the node it discharges to
    via: Dict[int, int]      # node index -> corridor index it discharges through (-1 = join)
    joins: np.ndarray        # node indices that discharge straight into the Main Pipe
    weight: float


class Orient:
    """Stage 2.  Build it, then `build()`."""

    # ---------------------------------------------------------------- load
    def __init__(self, grid: str = GRID, verbose: bool = True):
        import geopandas as gpd
        from shapely.strtree import STRtree

        self.verbose = verbose
        self.t0 = time.time()
        self.gpd = gpd
        self.notes: List[str] = []

        _log("reading corridors")
        cor = gpd.read_file(ROADS_GPKG, layer="corridors")
        if cor.crs is None or cor.crs.to_epsg() != CRS_EPSG:
            raise ValueError(f"corridors are {cor.crs}, expected EPSG:{CRS_EPSG}")
        nodes = gpd.read_file(ROADS_GPKG, layer="nodes")

        # the CIDs AS READ, so `_remeasure_dual` can tell a piece this stage cut from one
        # it did not. A cut renames the piece (`9DF3.1` -> `9DF3.1/m0`), which is exactly how
        # an inherited flag ends up describing geometry that no longer exists.
        self.cor0_cids = set(cor.CID.astype(str))
        self.h1_in = {
            "corridors_along": int((cor.get("ALONG_DUAL", pd.Series(
                np.zeros(len(cor)))).astype(int) == 1).sum()),
            "corridors_h1_keep": int((cor.get("H1_KEEP", pd.Series(
                np.zeros(len(cor)))).astype(int) == 1).sum())}

        self.selfloop = cor[cor.US_NODE == cor.DS_NODE].copy()
        cor = cor[cor.US_NODE != cor.DS_NODE].reset_index(drop=True)
        self.cor = cor
        self.node_geom = dict(zip(nodes.NODE_ID, nodes.geometry))

        _log(f"  {len(cor):,} corridors, {cor.LEN_M.sum()/1000:,.1f} km, "
             f"{len(nodes):,} nodes, {len(self.selfloop)} closed ring(s) set aside")

        _log(f"loading terrain grid {grid}")
        self.tf = T.TerrainFlow.load(grid)
        self.sigma_dz = float(self.tf.sigma_dz)

        _log("loading the built network's own measurements")
        ab = AB.AsBuilt()
        runs = ab.m_runs()
        terr = ab.m_terrain()
        zd = ab._zone_drainage()
        drops = ab.m_drops()
        self.RUN_MEDIAN_M = float(runs["run_between_junctions_median_m"])
        self.RUN_P90_M = float(runs["run_between_junctions_p90_m"])
        self.BUILT_UPHILL_PCT = float(terr["uphill_length_pct"])
        self.BUILT_CLIMB_PER_KM = float(terr["climb_m_per_km"])
        self.BUILT_RATIO = float(terr["climb_to_descent_ratio"])
        self.BUILT_JOINS = int(zd["joins_onto_trunk"])
        self.BUILT_VORTEX = int(drops["vortex_n"])
        _log(f"  median built run between junctions {self.RUN_MEDIAN_M:.2f} m  "
             f"(the ridge-split threshold)")
        _log(f"  built network drains uphill on {self.BUILT_UPHILL_PCT:.2f} % of its length")

        _log("reading the client's Main Pipe (an INPUT)")
        mp = gpd.read_file(MAIN_PIPE)
        if mp.crs is not None and mp.crs.to_epsg() != CRS_EPSG:
            mp = mp.to_crs(CRS_EPSG)
        self.main = mp
        self.main_km = float(mp.length.sum() / 1000.0)
        self._main_tree = STRtree(list(mp.geometry))

        self.ridge_splits = 0
        self.published = {}

    # ---------------------------------------------------------------- terrain
    def measure(self) -> None:
        """Ground level at every node, ground fall along every corridor, and how much the
        terrain can actually be trusted to say about each one."""
        _log("sampling the terrain")
        cor = self.cor
        # Node levels come from the working grid at the node coordinate, so the ground fall
        # along a path TELESCOPES exactly: sum of arc falls == end-to-end fall.  The 0.5 m
        # VRT was NOT used: terrain.py measured it no more accurate for direction (SD 0.7564
        # vs 0.7561 m against NAMA's surveyed levels) and it costs 1.4 ms a point.
        ids = sorted(set(cor.US_NODE) | set(cor.DS_NODE))
        xs = np.array([self.node_geom[i].x for i in ids])
        ys = np.array([self.node_geom[i].y for i in ids])
        zs = np.asarray(self.tf.elevation(xs, ys), dtype=float)
        self.nid = {a: i for i, a in enumerate(ids)}
        self.node_ids = ids
        self.NX, self.NY, self.NZ = xs, ys, zs
        self.NV = len(ids)
        if not np.isfinite(zs).all():
            bad = int((~np.isfinite(zs)).sum())
            self.notes.append(f"{bad} nodes fall outside the DEM and were given the mean "
                              f"level; they cannot be levelled and are flagged Z_OK = 0.")
            zs[~np.isfinite(zs)] = float(np.nanmean(zs))
        self.Z_OK = np.isfinite(np.asarray(self.tf.elevation(xs, ys), dtype=float))

        self.u = cor.US_NODE.map(self.nid).to_numpy(np.int64)
        self.v = cor.DS_NODE.map(self.nid).to_numpy(np.int64)
        self.L = cor.LEN_M.to_numpy(float)
        self.dz = self.NZ[self.u] - self.NZ[self.v]        # + = US higher, drawn direction
        self.Q = cor.Q_NEAR_M3D.to_numpy(float)
        self.NP = cor.N_PLOT.to_numpy(float)

        # the measured confidence in the SIGN of that fall - the curve in the terrain
        # manifest, from NAMA's built pipes where the true direction is known
        p = np.array([self.tf.p_direction_correct(abs(d)) for d in self.dz], dtype=object)
        self.p_corr = np.array([0.5 if q is None else float(q) for q in p], dtype=float)

        # profile shape: ridges, hollows, and how sure the direction is
        _log("  profiling every corridor for a crest")
        dd = [self.tf.drain_direction(g) for g in cor.geometry]
        self.conf = np.array([d["confidence"] for d in dd], dtype=object)
        self.split_at = np.array([float(d.get("split_at_m") or np.nan) for d in dd])
        self.split_kind = np.array([str(d.get("split_kind") or "") for d in dd], dtype=object)
        self.split_prom = np.array([float(d.get("split_prominence_m") or np.nan) for d in dd])

        flat = self.L * 0.0
        s = self.dz / np.maximum(self.L, 1e-9)
        below = np.abs(s) < SMIN_DN200
        self.flat_km = float(self.L[below].sum() / 1000.0)
        self.flat_pct = float(self.L[below].sum() / self.L.sum() * 100.0)
        _log(f"  {self.flat_pct:.1f} % of corridor length ({self.flat_km:,.1f} km) lies on "
             f"ground flatter than the DN200 minimum, either way it points")

        conf_share = {}
        for k in ("certain", "likely", "uncertain", "flat", "split", "no-data"):
            m = self.conf == k
            conf_share[k] = float(self.L[m].sum() / self.L.sum() * 100.0)
        self.conf_share = conf_share
        _log("  terrain confidence by length: " +
             ", ".join(f"{k} {v:.1f} %" for k, v in conf_share.items() if v > 0))

    # ---------------------------------------------------------------- ridge rule
    def presplit_ridges(self) -> None:
        """Cut a corridor at a genuine interior crest, where it is long enough to be worth it.

        The threshold is the built network's own median run between junctions
        (`asbuilt.m_runs()`), not a number anyone picked - philosophy sec 4 requires exactly
        that.  Below it the street stays whole and drains to its lower end.  A crest counts
        only if it beats 3 x the DEM's MEASURED differential error.

        Only ONE node is inserted, not two.  Cutting the corridor in half outright would
        remove an edge from the graph and could disconnect whatever lies beyond it; inserting
        a node lets the branching decide, and if it chooses to run one half uphill it is
        because there was no alternative.  Where the half turns out to be surplus, the head
        rule then makes it a head draining away from the crest, which is the ridge rule
        finishing itself.
        """
        from shapely.ops import substring
        thresh = self.RUN_MEDIAN_M
        prom_min = max(3.0 * self.sigma_dz, T.RIDGE_MIN_PROMINENCE_M)
        cand = np.nonzero((self.conf == "split") & (self.L > thresh) &
                          np.isfinite(self.split_at) &
                          (self.split_prom >= prom_min) &
                          (self.split_kind == "ridge"))[0]
        _log(f"ridge rule: threshold {thresh:.2f} m (built median run), crest must exceed "
             f"{prom_min:.3f} m (3 x measured sigma_dz)")
        if cand.size == 0:
            _log("  nothing to split")
            self.ridge_splits = 0
            self.split_rows = pd.DataFrame(
                columns=["CID", "LEN_M", "CREST_M", "PROM_M", "NEW_NODE"])
            return

        cor = self.cor
        new_rows = []
        add_x, add_y, add_z = [], [], []
        keep_mask = np.ones(len(cor), bool)
        rec = []
        for i in cand:
            geom = cor.geometry.iloc[i]
            at = float(self.split_at[i])
            if not (5.0 < at < geom.length - 5.0):
                continue
            a = substring(geom, 0.0, at)
            b = substring(geom, at, geom.length)
            if a.is_empty or b.is_empty or a.length < 1.0 or b.length < 1.0:
                continue
            nid = f"X{len(add_x):06d}"
            pt = geom.interpolate(at)
            add_x.append(pt.x); add_y.append(pt.y)
            base = cor.iloc[i]
            for part, us, ds in ((a, base.US_NODE, nid), (b, nid, base.DS_NODE)):
                r = base.copy()
                r["geometry"] = part
                r["US_NODE"] = us
                r["DS_NODE"] = ds
                r["LEN_M"] = float(part.length)
                frac = part.length / geom.length
                r["CID"] = f"{base.CID}/{'a' if us != nid else 'b'}"
                r["N_PLOT"] = float(base.N_PLOT) * frac
                r["Q_NEAR_M3D"] = float(base.Q_NEAR_M3D) * frac
                r["Q_M3D"] = float(base.Q_M3D) * frac
                new_rows.append(r)
            keep_mask[i] = False
            rec.append(dict(CID=base.CID, LEN_M=float(base.LEN_M), CREST_M=at,
                            PROM_M=float(self.split_prom[i]), NEW_NODE=nid))

        if not new_rows:
            _log("  no candidate survived the geometry check")
            self.ridge_splits = 0
            self.split_rows = pd.DataFrame(
                columns=["CID", "LEN_M", "CREST_M", "PROM_M", "NEW_NODE"])
            return

        gpd = self.gpd
        add = gpd.GeoDataFrame(new_rows, crs=cor.crs)
        self.cor = pd.concat([cor[keep_mask], add], ignore_index=True)
        self.cor = gpd.GeoDataFrame(self.cor, geometry="geometry", crs=cor.crs)
        from shapely.geometry import Point
        for k, (x, y) in enumerate(zip(add_x, add_y)):
            self.node_geom[f"X{k:06d}"] = Point(x, y)
        self.ridge_splits = len(rec)
        self.split_rows = pd.DataFrame(rec)
        _log(f"  {len(rec)} corridors cut at a crest -> {len(add)} halves; "
             f"{len(self.cor):,} corridors now")
        self.measure()          # levels, falls and confidences for the new arcs

    # ---------------------------------------------------------------- the outfall rule
    def meet_main_pipe(self) -> None:
        """THE OUTFALL RULE, applied by CUTTING rather than by pricing.

        Engineer, 2026-09-05/06 (philosophy sec 9): *"A subnetwork joins the main pipe at
        the lowest point where it MEETS it.  NO SUBNETWORK CROSSES THE MAIN PIPE AND GROWS
        PAST IT."*

        WHY THE PREVIOUS RUN COULD NOT OBEY IT.  `find_roots` asks whether a NODE is close
        to the Main Pipe.  A corridor can cross the trunk, or run a metre from it, with
        neither of its two nodes anywhere near - a 200 m street crossing at its midpoint has
        both ends 100 m away.  Measured on W11b's own shipped `arcs` layer: **214 arcs,
        48.49 km, physically CROSS the Main Pipe**, and 397 come within this tolerance of it
        while only 193 NODES did.  Every one of those is a flow path that reaches the trunk,
        ignores it, and grows out the other side.  That is how two subnetworks came to hold
        a quarter of the whole network while discharging somewhere else entirely.

        SO THE TEST MOVES FROM THE NODE TO THE CORRIDOR.  Wherever a corridor meets the Main
        Pipe - crossing it, running along it, or passing within MEET_TOL_M of it - a node is
        inserted at that point and the corridor is cut there.  `find_roots` then picks the
        new node up as an outfall by its own unchanged distance test, so after this pass:

          * no corridor crosses the trunk without a node on it, and a node ON the trunk is
            an outfall, so no flow path can cross and continue - it discharges instead;
          * every place a catchment meets the trunk is a candidate outlet, which is what
            "the lowest point where it MEETS it" needs in order to be a choice at all.

        EXPECT THE SUBNETWORK COUNT TO RISE, substantially, and that is the intended
        result: the engineer's words are *"more subnetworks worth keeping the work clean,
        rather than monster useless subnetworks"*.

        NOTHING IS DELETED.  A cut corridor is replaced by its own pieces, end to end, with
        length, plot count and load prorated exactly as the ridge rule does it - so the
        published length before and after this pass is identical to within floating point,
        and that equality is asserted, not asserted-in-a-comment.
        """
        from shapely.ops import substring, unary_union
        from shapely.geometry import Point

        main = unary_union(list(self.main.geometry))
        buf = main.buffer(MEET_TOL_M)
        tol = MEET_TOL_M
        km_before = float(self.cor.LEN_M.sum())
        plot_before = float(self.cor.N_PLOT.sum())
        q_before = float(self.cor.Q_M3D.sum())
        qn_before = float(self.cor.Q_NEAR_M3D.sum())
        _log(f"outfall rule: cutting every corridor where it MEETS the Main Pipe "
             f"(MEET_TOL_M = {tol:g} m, DERIVED from criteria.MH_SNAP_M, the node-merge "
             f"radius)")

        gpd = self.gpd
        rec: List[dict] = []
        meet_nodes: List[str] = []
        kinds: Dict[str, int] = {"crosses": 0, "along": 0, "within_tol": 0}
        n_cut_total = 0
        rounds = []
        # MEETING POINTS DROPPED AT AN END WHOSE NODE IS NOT ITSELF ON THE TRUNK.
        # The end-drop below is stated on ALONG-distance, and along-distance is only a
        # PROXY for "the end node is on the meeting point".  For a crossing the two agree -
        # the crossing sits on the trunk, so a node within `tol` ALONG the line is within
        # `tol` of the trunk and `find_roots` takes it as an outfall.  For a CLOSE APPROACH
        # they can diverge: the meeting point may be up to `tol` from the trunk AND up to
        # `tol` from the end node, which puts that node as much as 2 x tol away, past the
        # radius `find_roots` uses.  Measured on a hand case: a corridor passing 2.6 m from
        # the trunk 1.3 m from its own end, whose end node is 3.4 m away and is therefore
        # NOT an outfall.  Nothing crosses in that case, so the hard rule holds - what is
        # lost is a CANDIDATE OUTLET, silently.  It is counted and published instead
        # (concept rule 7: flag, do not solve).
        end_gap: List[dict] = []
        # A CUT CAN REVEAL A MEETING POINT THE UNCUT CORRIDOR HID: splitting a stretch that
        # ran inside the tolerance turns one contiguous approach into two, each with its own
        # closest point.  So the pass repeats until nothing is left, bounded by MEET_PASSES
        # and stopped the moment a round cuts nothing.  The per-round table is published.
        for rnd in range(MEET_PASSES):
            cor = self.cor
            try:
                cand = np.asarray(cor.sindex.query(buf, predicate="intersects"),
                                  dtype=np.int64)
            except Exception:                                      # pragma: no cover
                cand = np.nonzero(cor.geometry.intersects(buf).to_numpy())[0]
            cand = np.unique(cand)

            cuts: Dict[int, List[Tuple[float, str]]] = {}
            for i in cand:
                here = meet_points(cor.geometry.iloc[int(i)], main, buf, tol)
                if here:
                    cuts[int(i)] = here
            if not cuts:
                rounds.append(dict(round=rnd, corridors_cut=0, nodes_minted=0))
                break

            new_rows, add_xy = [], []
            keep_mask = np.ones(len(cor), bool)
            for i, here in cuts.items():
                g = cor.geometry.iloc[i]
                base = cor.iloc[i]
                # drop any meeting point that lands on an END - that node already meets the
                # trunk, and a second node inside the merge radius is the duplicate chamber
                # MH_SNAP_M exists to forbid - and any that lands inside the merge radius of
                # the one before it, for the same reason.
                picked: List[Tuple[float, str]] = []
                for at, kind in here:
                    if at <= tol or at >= g.length - tol:
                        # the end node is only an outfall if it is itself inside the
                        # tolerance of the trunk.  Where it is not, the meeting point is
                        # dropped and NO node picks it up - so it is recorded here.
                        nm = str(base.US_NODE if at <= tol else base.DS_NODE)
                        gp = self.node_geom.get(nm)
                        if gp is not None and gp.distance(main) > tol:
                            end_gap.append(dict(CID=str(base.CID), NODE=nm, AT_M=float(at),
                                                KIND=kind, ROUND=rnd,
                                                NODE_DMAIN_M=round(
                                                    float(gp.distance(main)), 3)))
                        continue
                    if picked and at - picked[-1][0] < tol:
                        continue
                    picked.append((at, kind))
                if not picked:
                    continue
                bounds = [0.0] + [a for a, _ in picked] + [float(g.length)]
                ids = [str(base.US_NODE)]
                for at, kind in picked:
                    nid = f"M{len(meet_nodes):06d}"
                    pt = g.interpolate(at)
                    add_xy.append((nid, pt.x, pt.y))
                    ids.append(nid)
                    meet_nodes.append(nid)
                    kinds[kind] = kinds.get(kind, 0) + 1
                    rec.append(dict(CID=str(base.CID), LEN_M=float(base.LEN_M),
                                    AT_M=float(at), KIND=kind, NEW_NODE=nid, ROUND=rnd))
                ids.append(str(base.DS_NODE))
                for k in range(len(bounds) - 1):
                    part = substring(g, bounds[k], bounds[k + 1])
                    if part.is_empty or part.length <= 0:
                        continue
                    r = base.copy()
                    r["geometry"] = part
                    r["US_NODE"] = ids[k]
                    r["DS_NODE"] = ids[k + 1]
                    r["LEN_M"] = float(part.length)
                    frac = part.length / g.length
                    r["CID"] = f"{base.CID}/m{k}"
                    r["N_PLOT"] = float(base.N_PLOT) * frac
                    r["Q_NEAR_M3D"] = float(base.Q_NEAR_M3D) * frac
                    r["Q_M3D"] = float(base.Q_M3D) * frac
                    new_rows.append(r)
                keep_mask[i] = False

            n_cut = int((~keep_mask).sum())
            rounds.append(dict(round=rnd, corridors_cut=n_cut,
                               nodes_minted=len(add_xy)))
            if not new_rows:
                break
            add = gpd.GeoDataFrame(new_rows, crs=cor.crs)
            self.cor = gpd.GeoDataFrame(
                pd.concat([cor[keep_mask], add], ignore_index=True),
                geometry="geometry", crs=cor.crs)
            for nid, x, y in add_xy:
                self.node_geom[nid] = Point(x, y)
            n_cut_total += n_cut

        self.meet_rounds = pd.DataFrame(rounds)
        self.meet_splits = int(n_cut_total)
        self.meet_nodes = meet_nodes
        self.meet_kinds = dict(kinds)
        self.meet_rows = (pd.DataFrame(rec) if rec else
                          pd.DataFrame(columns=["CID", "LEN_M", "AT_M", "KIND",
                                                "NEW_NODE", "ROUND"]))
        # the meeting points nobody picked up, deduplicated on (corridor, node) because an
        # uncut corridor is re-examined in every round
        eg = (pd.DataFrame(end_gap).drop_duplicates(subset=["CID", "NODE"]) if end_gap
              else pd.DataFrame(columns=["CID", "NODE", "AT_M", "KIND", "ROUND",
                                         "NODE_DMAIN_M"]))
        self.meet_end_gap = eg.reset_index(drop=True)
        self.n_meet_end_gap = int(len(self.meet_end_gap))
        if self.n_meet_end_gap:
            _log(f"  NAMED GAP: {self.n_meet_end_gap} meeting point(s) sit within {tol:g} m "
                 f"of a corridor END whose own node is FURTHER than {tol:g} m from the "
                 f"trunk (worst {self.meet_end_gap.NODE_DMAIN_M.max():.2f} m). No node is "
                 f"minted there and `find_roots` will not take that end as an outfall, so "
                 f"a candidate outlet is lost. Published as `meet_cuts_end_gap`; none of "
                 f"them is a crossing, so the no-crossing rule is not affected.")
        if not meet_nodes:
            _log("  no corridor meets the Main Pipe away from a node it already has - "
                 "nothing cut")
            self.n_meet_off_node = 0
            self.km_meet_off_node = 0.0
            return

        km_after = float(self.cor.LEN_M.sum())
        # ZERO SILENT DROPS: cutting must not lose a metre, a plot or a litre.  Asserted,
        # not asserted about - and on all three, because the docstring claims all three.
        if abs(km_after - km_before) > 1e-3 * max(1.0, km_before / 1000.0):
            raise AssertionError(
                f"the Main-Pipe cut changed the corridor length: {km_before:,.3f} m -> "
                f"{km_after:,.3f} m. Nothing may be lost here.")
        for what, was, now in (("plots", plot_before, float(self.cor.N_PLOT.sum())),
                               ("load m3/d", q_before, float(self.cor.Q_M3D.sum())),
                               ("near-load m3/d", qn_before,
                                float(self.cor.Q_NEAR_M3D.sum()))):
            if abs(now - was) > 1e-6 * max(1.0, abs(was)):
                raise AssertionError(
                    f"the Main-Pipe cut changed the corridor {what}: {was:,.6f} -> "
                    f"{now:,.6f}. Prorating a cut may not create or destroy load.")
        _log(f"  {self.meet_splits:,} corridors meet the Main Pipe and were cut at "
             f"{len(meet_nodes):,} new nodes ({kinds['crosses']:,} crossings, "
             f"{kinds['along']:,} collinear stretches, {kinds['within_tol']:,} approaches "
             f"inside {tol:g} m) over {len(rounds)} round(s); {len(self.cor):,} corridors "
             f"now, length unchanged at {km_after/1000:,.3f} km")

        # THE INVARIANT, RECHECKED ON WHAT THE CUT PRODUCED, with the same definition of
        # "meets" the cut used.  A meeting point with a node on it is a legal junction; one
        # without is a flow path that will cross the trunk and grow past it.
        left = self.meets_off_node(self.cor.geometry)
        self.n_meet_off_node = int((left > 0).sum())
        self.km_meet_off_node = float(
            self.cor.LEN_M.to_numpy(float)[left > 0].sum() / 1000.0)
        if self.n_meet_off_node:
            _log(f"  WARNING: {self.n_meet_off_node} corridor(s) still meet the Main Pipe "
                 f"with no node on the meeting point ({self.km_meet_off_node:.2f} km) "
                 f"after {MEET_PASSES} rounds. Published as X_MAIN on `arcs`, not swept up.")
        else:
            _log("  every place a corridor meets the Main Pipe now carries a node, and "
                 "every one of those nodes is an outfall")
        self.measure()          # levels, falls and confidences for the new arcs

    def meets_off_node(self, geoms) -> np.ndarray:
        """Per geometry: how many places it meets the Main Pipe with no node of its own on
        the meeting point.

        The invariant this stage owes the reader is that the answer is ZERO on every drained
        arc, and it is recomputed from the geometry that is about to be PUBLISHED rather
        than trusted from the pass that created it.  A crossing that carries a node is a
        legal junction - the node is an outfall - so this counts the crossings that do NOT,
        which is the defect and not the geometry.
        """
        from shapely.ops import unary_union
        main = unary_union(list(self.main.geometry))
        buf = main.buffer(MEET_TOL_M)
        gl = list(geoms)
        out = np.zeros(len(gl), np.int64)
        try:                                   # only the ones anywhere near it can offend
            near = set(int(k) for k in
                       self.gpd.GeoSeries(gl, crs=f"EPSG:{CRS_EPSG}").sindex.query(
                           buf, predicate="intersects"))
        except Exception:                                          # pragma: no cover
            near = set(range(len(gl)))
        for k in near:
            out[k] = meets_without_a_node(gl[k], main, buf, MEET_TOL_M)
        return out

    # ---------------------------------------------------------------- roots
    def find_roots(self, snap: float = MAIN_SNAP_M, quiet: bool = False) -> None:
        """Outfalls: corridor nodes that touch the client's Main Pipe."""
        if not quiet:
            _log("finding outfalls on the client's Main Pipe")
        pts = [self.node_geom[i] for i in self.node_ids]
        ix = self._main_tree.nearest(pts)
        d = np.array([pts[i].distance(self.main.geometry.iloc[ix[i]])
                      for i in range(self.NV)])
        self.d_main = d
        self.roots = np.nonzero(d <= snap + MEET_EPS_M)[0]   # see MEET_EPS_M
        rows = [dict(WITHIN_M=t, N_NODES=int((d <= t).sum())) for t in
                (1, 3, 5, 10, 15, 20, 25, 30, 50, 100, 200)]
        self.snap_sweep = pd.DataFrame(rows)

        # EVERY NODE `meet_main_pipe` MINTED MUST BE AN OUTFALL.  It was placed ON the
        # trunk, so the distance test below has to find it; if it does not, the two steps
        # disagree about what "meets" means and the outfall rule is not being enforced.
        # Checked at the shipped radius only - the sweep deliberately runs others.
        mm = [self.nid[m] for m in getattr(self, "meet_nodes", []) if m in self.nid]
        if mm and abs(snap - MEET_TOL_M) < 1e-9:
            miss = [self.node_ids[i] for i in mm if d[i] > snap + MEET_EPS_M]
            if miss:
                raise AssertionError(
                    f"{len(miss)} node(s) minted ON the Main Pipe are not outfalls at "
                    f"MEET_TOL_M = {snap:g} m, e.g. {miss[:5]}. `meet_main_pipe` and "
                    f"`find_roots` disagree about what 'meets' means.")
            self.n_meet_roots = len(mm)

        # IS THE CLIENT'S TRUNK ABOVE THE TOWN?  For every corridor node, its ground level
        # less the ground level of the nearest point ON the Main Pipe.  If that is
        # systematically negative the trunk is drawn along high ground and nothing this
        # stage does can make the network drain into it - which would be a finding about
        # the INPUT, not about the tree, and the engineer's to act on.
        near = [self.main.geometry.iloc[ix[i]].interpolate(
            self.main.geometry.iloc[ix[i]].project(pts[i])) for i in range(self.NV)]
        zt = np.asarray(self.tf.elevation(np.array([p.x for p in near]),
                                          np.array([p.y for p in near])), dtype=float)
        rel = self.NZ - zt
        self.trunk_relief = rel
        q = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        self.relief_tab = pd.DataFrame(
            [dict(PCTILE=k, RELIEF_M=float(np.nanpercentile(rel, k))) for k in q] +
            [dict(PCTILE="mean", RELIEF_M=float(np.nanmean(rel))),
             dict(PCTILE="share_below_%", RELIEF_M=float(np.nanmean(rel < 0) * 100.0))])
        if not quiet:
            _log(f"  corridor node level minus the trunk beside it: median "
                 f"{np.nanmedian(rel):+.2f} m, {np.nanmean(rel < 0)*100:.1f} % of nodes "
                 f"sit BELOW the trunk that passes them")
        if not quiet:
            _log(f"  {len(self.roots)} nodes within {snap:g} m of the Main Pipe "
                 f"({self.main_km:.2f} km); NAMA's built network has {self.BUILT_JOINS} "
                 f"joins onto its own trunk, 4.64 per km of it against our "
                 f"{len(self.roots) / self.main_km:.2f}")

        # closed basins: run the test, publish the answer
        try:
            b = self.gpd.read_file(os.path.join(W12, "run", "terrain",
                                                f"{GRID}_basins.gpkg"),
                                   layer="closed_basins")
            forced = b[b.PUMP_FORCED.astype(bool)] if "PUMP_FORCED" in b.columns else b.iloc[:0]
            self.basins_n = int(len(b))
            self.basins_forced = int(len(forced))
            bid = self.tf.basin_at(self.NX, self.NY)
            self.nodes_in_basin = int((np.asarray(bid) > 0).sum())
            if not quiet:
                _log(f"  {self.basins_n} closed basins in the study area, "
                     f"{self.basins_forced} deeper than the {MAX_COVER_M:g} m cover cap; "
                     f"{self.nodes_in_basin} corridor nodes sit inside one")
        except Exception as exc:                                # pragma: no cover
            self.basins_n = self.basins_forced = self.nodes_in_basin = -1
            self.notes.append(f"closed-basin check could not run: {exc}")

        # which components can reach an outfall at all
        import networkx as nx
        g = nx.Graph()
        g.add_nodes_from(range(self.NV))
        g.add_edges_from(zip(self.u.tolist(), self.v.tolist()))
        rs = set(self.roots.tolist())
        served, islands = set(), []
        for cc in nx.connected_components(g):
            if cc & rs:
                served |= cc
            else:
                islands.append(cc)
        self.served = served
        self.islands = islands
        em = np.array([a in served for a in range(self.NV)])
        self.edge_in = em[self.u] & em[self.v]
        lost = self.L[~self.edge_in].sum() / 1000.0
        lostq = self.Q[~self.edge_in].sum()
        if islands and not quiet:
            _log(f"  {len(islands)} component(s) cannot reach the Main Pipe at all: "
                 f"{lost:.2f} km, {lostq:,.0f} m3/d. They are ROLE = 'island' in `arcs`.")
        self.island_km = float(lost)
        self.island_q = float(lostq)

    # ---------------------------------------------------------------- weights
    def slope_factor(self, signed_dz: np.ndarray) -> np.ndarray:
        """The Chahinian-style slope term, shrunk by the MEASURED confidence.

        `signed_dz` is the ground fall in the direction the flow would run, positive =
        downhill.  Returns S in [0, SLOPE_CAP]:
            S = 0    the ground already falls at the DN200 minimum or better - free
            S = 0.5  dead flat
            S = 1.0  the ground RISES at the DN200 minimum
        which is exactly the depth debt max(0, Smin - s) rescaled by 1/(2 Smin).
        """
        s = signed_dz / np.maximum(self.L, 1e-9)
        raw = np.clip((SMIN_DN200 - s) / (2.0 * SMIN_DN200), 0.0, SLOPE_CAP)
        k = np.clip(2.0 * self.p_corr - 1.0, 0.0, 1.0)     # Youden shrink toward neutral
        return 0.5 + (raw - 0.5) * k

    def _arc_arrays(self):
        """The reversed arc list handed to the solver, plus the bookkeeping to undo it.

        An arc is added as (DOWNSTREAM, UPSTREAM) because networkx-style arborescences point
        away from the root while a sewer converges on it.  Both directions of every corridor
        are offered; the solver picks at most one.
        """
        m = self.edge_in
        uu, vv = self.u[m], self.v[m]
        idx = np.nonzero(m)[0]
        S = self.NV                                # the super-root
        sub = sorted(self.served) + [S]
        r = np.full(self.NV + 1, -1, np.int64)
        for i, a in enumerate(sub):
            r[a] = i
        self._sub = sub
        self._r = r
        self._uu, self._vv, self._idx = uu, vv, idx
        return len(sub), r[S]

    def _detour(self):
        """Shortest LENGTH distance from every node to its nearest outfall."""
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import dijkstra
        n, _ = self._arc_arrays()
        r, uu, vv, idx = self._r, self._uu, self._vv, self._idx
        Lm = self.L[idx]
        rows = np.concatenate([r[uu], r[vv]])
        cols = np.concatenate([r[vv], r[uu]])
        M = csr_matrix((np.concatenate([Lm, Lm]), (rows, cols)), shape=(n, n))
        d = dijkstra(M, indices=r[self.roots], min_only=True, directed=True)
        d[~np.isfinite(d)] = 1e9
        self.d_out = d                       # indexed on the SOLVER node id
        return d

    def weights(self, lam_slope=LAMBDA_SLOPE, lam_detour=LAMBDA_DETOUR,
                bend_pen: Optional[Dict[Tuple[int, bool], float]] = None):
        """Every term, for both directions of every in-play corridor.  Equivalent metres."""
        idx = self._idx
        L = self.L[idx]
        Sf = self.slope_factor(self.dz)[idx]
        Sb = self.slope_factor(-self.dz)[idx]
        d = self.d_out
        r, uu, vv = self._r, self._uu, self._vv
        # detour: extra metres to the works this arc creates.  Flow US->DS means the
        # DOWNSTREAM node is vv, so a good arc has d[vv] + L == d[uu].
        det_f = np.maximum(0.0, d[r[vv]] - d[r[uu]] + L)
        det_b = np.maximum(0.0, d[r[uu]] - d[r[vv]] + L)
        bf = np.zeros(L.size)
        bb = np.zeros(L.size)
        if bend_pen:
            for k, val in bend_pen.items():
                i, fwd = k
                (bf if fwd else bb)[i] = val
        wf = L + lam_slope * L * Sf + lam_detour * det_f + LAMBDA_BEND * bf
        wb = L + lam_slope * L * Sb + lam_detour * det_b + LAMBDA_BEND * bb
        return dict(L=L, Sf=Sf, Sb=Sb, det_f=det_f, det_b=det_b, bf=bf, bb=bb,
                    wf=wf, wb=wb)

    def _solve(self, w, join_cost, method="branching") -> Tree:
        n, sroot = self._arc_arrays()
        r, uu, vv, idx = self._r, self._uu, self._vv, self._idx
        nR = len(self.roots)
        U = np.concatenate([r[vv], r[uu], np.full(nR, sroot)])
        V = np.concatenate([r[uu], r[vv], r[self.roots]])
        W = np.concatenate([w["wf"], w["wb"], np.full(nR, float(join_cost))])
        EI = np.concatenate([idx, idx, -np.ones(nR, np.int64)])
        FW = np.concatenate([np.ones(idx.size, bool), np.zeros(idx.size, bool),
                             np.zeros(nR, bool)])
        fn = msa_edges if method == "branching" else spt_edges
        sel = fn(n, U, V, W, sroot)
        isj = EI[sel] < 0
        parent, via = {}, {}
        inv = {i: a for i, a in enumerate(self._sub)}
        for e in sel:
            child = inv[int(V[e])]
            par = inv[int(U[e])]
            parent[child] = -1 if par == self.NV else par
            via[child] = int(EI[e])
        return Tree(name=method, arc=EI[sel][~isj], fwd=FW[sel][~isj], parent=parent,
                    via=via, joins=np.array([inv[int(V[e])] for e in sel[isj]]),
                    weight=float(W[sel].sum()))

    # ---------------------------------------------------------------- measure a tree
    def score(self, tr: Tree) -> dict:
        """Everything that decides whether a tree is any good.  All measured on the tree."""
        sdz = np.where(tr.fwd, self.dz[tr.arc], -self.dz[tr.arc])
        L = self.L[tr.arc]
        up = sdz < -ADVERSE_MIN_M
        # flow path from every node to its outfall
        plen, pfall, preq = self._paths(tr)
        good = np.isfinite(plen)
        # the gravity early warning, on the SAME footing for every tree so the comparison
        # is decided on engineering rather than on preference: how much fall the tree
        # demands at the DN200 minimum, less the fall the ground actually provides
        deficit = preq - pfall
        dgood = deficit[np.isfinite(deficit)]
        # the same sum charged at the FLATTEST gradient Table 11 allows any pipe (DN900 and
        # above, 0.75 mm/m).  The pair brackets the answer: nothing can do better than the
        # floor and nothing has to do worse than the DN200 minimum.
        dfl = (plen * SMIN_FLOOR - pfall)
        dfl = dfl[np.isfinite(dfl)]
        return dict(
            tree=tr.name, arcs=int(L.size), km=float(L.sum() / 1000.0),
            uphill_pct=float(L[up].sum() / L.sum() * 100.0),
            uphill_km=float(L[up].sum() / 1000.0),
            climb_m=float(-sdz[sdz < 0].sum()), descent_m=float(sdz[sdz > 0].sum()),
            climb_per_km=float(-sdz[sdz < 0].sum() / (L.sum() / 1000.0)),
            ratio=float(-sdz[sdz < 0].sum() / max(sdz[sdz > 0].sum(), 1e-9)),
            worst_rise_m=float(-sdz.min()) if sdz.size else 0.0,
            joins=int(tr.joins.size),
            path_med_m=float(np.median(plen[good])),
            path_p95_m=float(np.percentile(plen[good], 95)),
            path_max_m=float(plen[good].max()),
            def_p95_m=float(np.percentile(dgood, 95)) if dgood.size else float("nan"),
            def_max_m=float(dgood.max()) if dgood.size else float("nan"),
            n_over_budget=int((dgood > DEPTH_BUDGET_M).sum()),
            n_over_floor=int((dfl > DEPTH_BUDGET_M).sum()),
            n_nodes=int(good.sum()),
            uphill_pct_all=float(L[up].sum() / (self.L[self.edge_in].sum()) * 100.0),
            weight=tr.weight)

    def _paths(self, tr: Tree):
        """Per node: flow-path length to the outfall, the ground fall available along it,
        and the fall the tree DEMANDS at the flattest legal DN200 gradient."""
        parent, via = tr.parent, tr.via
        plen = np.full(self.NV, np.nan)
        preq = np.full(self.NV, np.nan)
        for x in list(parent.keys()):
            chain = []
            y = x
            while y in parent and np.isnan(plen[y]):
                chain.append(y)
                y = parent[y]
                if y < 0:
                    break
            base_l = 0.0 if y < 0 or y not in parent else plen[y]
            base_r = 0.0 if y < 0 or y not in parent else preq[y]
            if np.isnan(base_l):
                base_l, base_r = 0.0, 0.0
            for z in reversed(chain):
                e = via.get(z, -1)
                dl = 0.0 if e < 0 else self.L[e]
                base_l = base_l + dl
                base_r = base_r + dl * SMIN_DN200
                plen[z] = base_l
                preq[z] = base_r
        # ground fall available: node level minus its outfall's level
        outfall = np.full(self.NV, -1, np.int64)
        for x in list(parent.keys()):
            y, guard = x, 0
            while y in parent and parent[y] >= 0 and guard < 1_000_000:
                y = parent[y]
                guard += 1
            outfall[x] = y
        self._outfall = outfall
        pfall = np.where(outfall >= 0, self.NZ - self.NZ[np.maximum(outfall, 0)], np.nan)
        self._plen, self._pfall, self._preq = plen, pfall, preq
        return plen, pfall, preq

    # ---------------------------------------------------------------- bend
    def _inlet_angles(self, tr: Tree):
        """The angle at every chamber between an arriving pipe and the pipe that leaves.

        G203-p30: "No inlet pipe at manholes shall have an angle less than 90 deg to the
        direction of flow."  Measured on the drawn geometry, at the node, using the tangent
        of the first/last 15 m of each corridor so a kink at the far end cannot change it.
        """
        cor = self.cor
        bear_us, bear_ds = self._tangents()
        out_arc: Dict[int, Tuple[int, bool]] = {}
        for child, e in tr.via.items():
            if e >= 0:
                out_arc[child] = (e, bool(np.where(self.u[e] == child, True, False)))
        rows = []
        for k, (e, fwd) in enumerate(zip(tr.arc, tr.fwd)):
            e = int(e); fwd = bool(fwd)
            ds_node = int(self.v[e] if fwd else self.u[e])
            o = out_arc.get(ds_node)
            if o is None:
                continue
            oe, ofwd = o
            if oe == e:
                continue
            # bearing of the arriving pipe AT the node, pointing downstream
            arr = bear_ds[e] if fwd else (bear_us[e] + 180.0) % 360.0
            dep = bear_us[oe] if ofwd else (bear_ds[oe] + 180.0) % 360.0
            turn = abs(((dep - arr + 180.0) % 360.0) - 180.0)     # 0 = straight on
            inlet = 180.0 - turn                                   # G203's angle
            rows.append((k, e, fwd, ds_node, inlet))
        return rows

    def _tangents(self):
        if getattr(self, "_tan", None) is not None:
            return self._tan
        TAN = 15.0
        bu = np.zeros(len(self.cor)); bd = np.zeros(len(self.cor))
        for i, g in enumerate(self.cor.geometry):
            xy = np.asarray(g.coords, float)[:, :2]
            L = g.length
            a = g.interpolate(0.0); b = g.interpolate(min(TAN, L))
            bu[i] = math.degrees(math.atan2(b.x - a.x, b.y - a.y)) % 360.0
            a = g.interpolate(max(0.0, L - TAN)); b = g.interpolate(L)
            bd[i] = math.degrees(math.atan2(b.x - a.x, b.y - a.y)) % 360.0
        self._tan = (bu, bd)
        return self._tan

    def solve_with_bends(self, lam_slope=LAMBDA_SLOPE, lam_detour=LAMBDA_DETOUR,
                         join_cost=JOIN_COST_M, passes=BEND_PASSES):
        """Solve, measure the sharp inlets, penalise them, solve again.

        An arborescence weight sees ONE arc; a turn is a property of TWO.  So this is
        iterative re-weighting, and the point of publishing the per-pass count is that the
        reader can see for himself whether it converged rather than take a claim for it.
        """
        pen: Dict[Tuple[int, bool], float] = {}
        hist = []
        best = None
        for p in range(passes + 1):
            pen_now = dict(pen) if p else None
            w = self.weights(lam_slope, lam_detour, pen_now)
            tr = self._solve(w, join_cost, "branching")
            ang = self._inlet_angles(tr)
            bad = [a for a in ang if a[4] < INLET_MIN_DEG]
            sc = self.score(tr)
            hist.append(dict(pass_=p, inlets=len(ang), sharp=len(bad),
                             sharp_pct=100.0 * len(bad) / max(len(ang), 1),
                             worst_deg=min((a[4] for a in ang), default=float("nan")),
                             uphill_pct=sc["uphill_pct"], km=sc["km"]))
            _log(f"  bend pass {p}: {len(bad):,} of {len(ang):,} inlets under "
                 f"{INLET_MIN_DEG:g} deg ({100.0*len(bad)/max(len(ang),1):.2f} %), "
                 f"uphill {sc['uphill_pct']:.2f} %")
            if best is None or len(bad) < best[0]:
                best = (len(bad), p, tr, pen_now)
            if p == passes:
                break
            # ACCUMULATE the penalty rather than replace it.  Replacing it makes the
            # iteration a two-cycle: the arcs relieved in one pass come straight back in the
            # next, and the count oscillates instead of settling.  Accumulating is the usual
            # ascent and it at least cannot un-learn.
            for _, e, fwd, _, inlet in bad:
                k = (int(np.searchsorted(self._idx, e)), fwd)
                pen[k] = pen.get(k, 0.0) + BEND_EQUIV_M * (1.0 - inlet / INLET_MIN_DEG)
        self.bend_hist = pd.DataFrame(hist)
        self.bend_hist["kept"] = [i == best[1] for i in self.bend_hist.pass_]
        tr = best[2]
        _log(f"  keeping pass {best[1]} ({best[0]:,} sharp inlets) - the fewest of the "
             f"{passes + 1} tried")
        self.last_angles = self._inlet_angles(tr)
        self.weights_used = self.weights(lam_slope, lam_detour, best[3])
        return tr

    # ---------------------------------------------------------------- the outfall rule, 2
    def _below_outlet_km(self, tr: Tree, out: np.ndarray) -> float:
        """Length of tree arc whose UPSTREAM node sits below the outfall it drains to.

        This is the quantity the engineer's defect is stated in - *"42 components discharge
        with more than half their catchment BELOW the outlet"* - and it is the objective the
        re-rooting pass drives down.  Measured on the tree arcs only; a dead-end head drains
        to its own low end by construction and can neither help nor hurt it.
        """
        if tr.arc.size == 0:
            return 0.0
        us = np.where(tr.fwd, self.u[tr.arc], self.v[tr.arc])
        o = out[us]
        m = (o >= 0) & (self.NZ[us] < self.NZ[np.maximum(o, 0)] - ADVERSE_MIN_M)
        return float(self.L[tr.arc][m].sum() / 1000.0)

    def _rebuild(self, tr: Tree, parent: Dict[int, int], via: Dict[int, int]) -> Tree:
        """A Tree from a parent/via map, with its weight re-summed from the same weights
        the solver used - never carried over, because a weight that no longer matches its
        own tree is a number nobody can check."""
        pos = {int(e): k for k, e in enumerate(self._idx)}
        w = self.weights_used
        arcs, fwds, tot = [], [], 0.0
        for child, e in via.items():
            if e < 0:
                tot += float(JOIN_COST_M)
                continue
            fwd = bool(self.u[e] == child)
            arcs.append(int(e))
            fwds.append(fwd)
            k = pos.get(int(e))
            if k is not None:
                tot += float(w["wf"][k] if fwd else w["wb"][k])
        return Tree(name=tr.name, arc=np.asarray(arcs, np.int64),
                    fwd=np.asarray(fwds, bool), parent=parent, via=via,
                    joins=np.asarray([c for c, p in parent.items() if p < 0], np.int64),
                    weight=float(tot))

    @staticmethod
    def _cycle(parent: Dict[int, int]) -> List[int]:
        """One cycle in a parent map, or []. Iterative - the chains here reach 10,000 hops
        and a recursive walk would blow the stack on the real network."""
        colour: Dict[int, int] = {}
        for s in parent:
            if colour.get(s):
                continue
            stack, order = [s], []
            while stack:
                x = stack[-1]
                if colour.get(x) == 1:
                    stack.pop()
                    colour[x] = 2
                    continue
                if colour.get(x) == 2:
                    stack.pop()
                    continue
                colour[x] = 1
                order.append(x)
                p = parent.get(x, -1)
                if p is not None and p >= 0:
                    if colour.get(p) == 1:                 # back edge: a cycle
                        cyc, y = [p], parent.get(p, -1)
                        guard = 0
                        while y != p and y is not None and y >= 0 and guard < 1_000_000:
                            cyc.append(y)
                            y = parent.get(y, -1)
                            guard += 1
                        return cyc
                    if colour.get(p) is None:
                        stack.append(p)
        return []

    def reroot_below_outfall(self, tr: Tree) -> Tree:
        """A SUBNETWORK MUST NOT DISCHARGE ABOVE ITS OWN CATCHMENT.

        `meet_main_pipe` made every place a catchment meets the trunk into an outfall, so
        the *choice* of outlet now exists.  This pass makes it.

        THE MOVE, AND WHY IT CAN ONLY IMPROVE THINGS.  Take a node `x` that sits BELOW the
        outfall it currently drains to - its sewage climbs to get out.  If a corridor from
        `x` reaches a node in a NEIGHBOURING subnetwork whose outfall is at or below `x`,
        re-point `x` there.  That moves x's whole upstream subtree with it, and because the
        new outfall is lower than the old one, **every arc in that subtree that was below
        its outlet is still below the new one or better** - the count cannot rise.  So the
        below-outlet length is monotone non-increasing and the loop terminates; it is
        stopped early the moment a pass accepts nothing, and the per-pass table is published
        so convergence is read rather than claimed.

        THIS IS THE GENERAL RULE FROM THE INHERITANCE LEDGER, ROW 4, IN ITS OTHER FORM:
        *anything a pass can ADD, a later pass must be able to TAKE AWAY, and the stage
        publishes how many it removed.*  The branching only ever ASSIGNS a node to the
        outfall its weights liked; this pass takes that assignment away again where the
        ground says it was wrong, and prints the count.

        WHAT IT IS NOT.  It is not a re-solve.  It moves a branch onto a neighbour that is
        already there, at first order, exactly as the neighbour test in `subnetworks` does -
        and it is bounded by the built network's own detour ratio (DETOUR_RATIO_MAX = 4.0,
        `10_ASBUILT_CALIBRATION.md` sec 1) so a lower outlet can never be bought with pipe
        nobody would build.
        """
        inplay = np.nonzero(self.edge_in)[0]
        inc: Dict[int, List[int]] = {}
        for i in inplay:
            inc.setdefault(int(self.u[i]), []).append(int(i))
            inc.setdefault(int(self.v[i]), []).append(int(i))
        rootset = set(int(r) for r in self.roots)

        hist, moved_total = [], 0
        for p in range(REROOT_PASSES):
            plen, _pf, _pr = self._paths(tr)
            out = self._outfall.copy()
            before = self._below_outlet_km(tr, out)
            cand: List[Tuple[float, int, int, int]] = []
            for x in range(self.NV):
                if x in rootset:
                    continue                      # an outfall does not move; it IS the trunk
                ox = int(out[x])
                if ox < 0 or not (self.NZ[x] < self.NZ[ox] - ADVERSE_MIN_M):
                    continue                      # not climbing to its own outlet
                best = None
                for i in inc.get(x, ()):
                    y = int(self.v[i]) if int(self.u[i]) == x else int(self.u[i])
                    oy = int(out[y])
                    if oy < 0 or oy == ox:
                        continue
                    if self.NZ[oy] > self.NZ[x] + ADVERSE_MIN_M:
                        continue                  # the new outlet is not below x either
                    nlen = float(plen[y] + self.L[i])
                    if not np.isfinite(nlen):
                        continue
                    straight = math.hypot(self.NX[x] - self.NX[oy],
                                          self.NY[x] - self.NY[oy])
                    if straight > 1.0 and nlen > DETOUR_RATIO_MAX * straight:
                        continue                  # bought with pipe nobody would build
                    key = (float(self.NZ[oy]), nlen)
                    if best is None or key < best[0]:
                        best = (key, y, i)
                if best is not None:
                    cand.append((float(self.NZ[ox] - best[0][0]), x, best[1], best[2]))
            if not cand:
                hist.append(dict(pass_=p, candidates=0, moved=0, reverted_cycles=0,
                                 below_km_before=round(before, 3),
                                 below_km_after=round(before, 3)))
                break

            parent, via = dict(tr.parent), dict(tr.via)
            gain = {}
            for g, x, y, i in cand:
                parent[x], via[x], gain[x] = y, i, g
            # a re-point can only close a loop THROUGH another re-point, so a cycle always
            # contains one; break it at the smallest gain and try again.  H15 is a forest
            # and this pass may not be the thing that breaks it.
            reverted = 0
            while True:
                cyc = self._cycle(parent)
                if not cyc:
                    break
                inside = [z for z in cyc if z in gain]
                if not inside:                                     # pragma: no cover
                    raise AssertionError(
                        "a cycle with no re-pointed node in it: the tree handed to "
                        "reroot_below_outfall was not a forest")
                z = min(inside, key=lambda a: gain[a])
                parent[z], via[z] = tr.parent[z], tr.via[z]
                del gain[z]
                reverted += 1

            tr = self._rebuild(tr, parent, via)
            plen, _pf, _pr = self._paths(tr)
            after = self._below_outlet_km(tr, self._outfall)
            moved = len(gain)
            moved_total += moved
            hist.append(dict(pass_=p, candidates=len(cand), moved=moved,
                             reverted_cycles=reverted,
                             below_km_before=round(before, 3),
                             below_km_after=round(after, 3)))
            _log(f"  reroot pass {p}: {moved:,} branches moved to a lower outfall "
                 f"({reverted} reverted to keep the forest); catchment draining up to its "
                 f"own outlet {before:,.1f} -> {after:,.1f} km")
            if after > before + 1e-6:                              # pragma: no cover
                raise AssertionError(
                    f"re-rooting made it worse ({before:.3f} -> {after:.3f} km). The move "
                    f"is only legal when the new outfall is lower, so this cannot happen "
                    f"unless the monotonicity argument is wrong.")
            if moved == 0:
                break

        self.reroot_hist = pd.DataFrame(hist) if hist else pd.DataFrame(
            [{"pass_": 0, "candidates": 0, "moved": 0, "reverted_cycles": 0,
              "below_km_before": 0.0, "below_km_after": 0.0}])
        self.reroot_moved = int(moved_total)
        self.reroot_converged = bool(hist and int(hist[-1]["moved"]) == 0)
        _log(f"  outfall rule: {moved_total:,} branches re-pointed to a lower outfall in "
             f"{len(hist)} pass(es)"
             + ("" if self.reroot_converged else
                f" - AND IT DID NOT CONVERGE inside the {REROOT_PASSES}-pass cap; the last "
                f"pass still moved {hist[-1]['moved']}, so the remaining below-outlet "
                f"length is an upper bound and the cap needs raising"))
        # the inlet angles belong to the tree, so a re-pointed tree needs them again.  An
        # angle measured against a direction that no longer exists is not a number.
        if getattr(self, "cor", None) is not None:
            self.last_angles = self._inlet_angles(tr)
        else:                                       # a unit-test harness with no geometry
            self.last_angles = []
            self.notes.append("inlet angles were NOT re-measured after re-rooting: this "
                              "instance carries no corridor geometry")
        return tr

    # ---------------------------------------------------------------- comparison
    def compare(self, lam_slope=LAMBDA_SLOPE, lam_detour=LAMBDA_DETOUR,
                join_cost=JOIN_COST_M) -> pd.DataFrame:
        """The four trees on the same graph.  This table is the evidence."""
        _log("building the four comparison trees on the same graph")
        rows = []
        w0 = self.weights(0.0, 0.0)
        wS = self.weights(lam_slope, 0.0)
        wSD = self.weights(lam_slope, lam_detour)
        for label, w, meth in (
                ("A naive shortest-path tree, LENGTH only", w0, "spt"),
                ("B optimum branching, LENGTH only", w0, "branching"),
                ("C shortest-path tree, slope-weighted", wS, "spt"),
                ("D optimum branching, slope-weighted", wS, "branching"),
                ("E optimum branching, slope + detour  <- SHIPPED", wSD, "branching")):
            tr = self._solve(w, join_cost, meth)
            s = self.score(tr)
            s["tree"] = label
            rows.append(s)
            _log(f"  {label:48s} uphill {s['uphill_pct']:6.2f} %  climb {s['climb_m']:6.0f} m"
                 f"  joins {s['joins']:4d}  path med {s['path_med_m']:7.0f} m"
                 f"  over budget {s['n_over_budget']:5d}")
        df = pd.DataFrame(rows)
        cols = ["tree", "arcs", "km", "uphill_pct", "uphill_pct_all", "uphill_km",
                "climb_m", "descent_m", "climb_per_km", "ratio", "worst_rise_m", "joins",
                "path_med_m", "path_p95_m", "path_max_m", "def_p95_m", "def_max_m",
                "n_over_budget", "n_over_floor", "n_nodes", "weight"]
        return df[cols]

    def sweeps(self, join_cost=JOIN_COST_M) -> Dict[str, pd.DataFrame]:
        """Sensitivity of the answer to every project number in the weights."""
        _log("sweeping the weights")
        out = {}
        rows = []
        for lam in (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0):
            tr = self._solve(self.weights(lam, LAMBDA_DETOUR), join_cost, "branching")
            s = self.score(tr); s["LAMBDA_SLOPE"] = lam
            rows.append(s)
        out["sweep_lambda_slope"] = pd.DataFrame(rows)
        rows = []
        for det in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0):
            tr = self._solve(self.weights(LAMBDA_SLOPE, det), join_cost, "branching")
            s = self.score(tr); s["LAMBDA_DETOUR"] = det
            rows.append(s)
        out["sweep_lambda_detour"] = pd.DataFrame(rows)
        rows = []
        w = self.weights(LAMBDA_SLOPE, LAMBDA_DETOUR)
        for jc in (0.0, 100.0, 500.0, 1000.0, 2000.0, 5000.0, 20000.0):
            tr = self._solve(w, jc, "branching")
            s = self.score(tr); s["JOIN_COST_M"] = jc
            rows.append(s)
        out["sweep_join_cost"] = pd.DataFrame(rows)
        # THE SNAP RADIUS IS NOT A COSMETIC TOLERANCE, so it is not swept by node count
        # alone: at each radius the whole tree is re-solved and the gravity verdict
        # re-measured.  MEET_TOL_M is literally "meets the trunk" and it is DERIVED from the
        # node-merge radius, not chosen; anything larger buys the connection with a SPUR,
        # which is a legitimate pipe and an engineer's decision.  The old 5.0 m is kept as a
        # row so the change of tolerance can be read off rather than taken on trust.
        rows = []
        for t in (MEET_TOL_M, 5.0, 15.0, 25.0, 50.0, 100.0):
            self.find_roots(snap=t, quiet=True)
            self._arc_arrays()
            self._detour()
            s = self.score(self._solve(self.weights(LAMBDA_SLOPE, LAMBDA_DETOUR),
                                       join_cost, "branching"))
            below = int(np.nansum(self._pfall < -ADVERSE_MIN_M))
            s.update(MAIN_SNAP_M=t, roots=int(len(self.roots)), n_below_outfall=below)
            rows.append(s)
            _log(f"    snap {t:6.1f} m -> {len(self.roots):4d} outfalls, uphill "
                 f"{s['uphill_pct']:5.2f} %, {s['n_over_floor']:,} nodes past the depth "
                 f"budget even at the flattest legal gradient")
        self.find_roots(quiet=True)          # back to the shipped radius
        self._arc_arrays()
        self._detour()
        snap = pd.DataFrame(rows)
        out["sweep_main_snap"] = snap[["MAIN_SNAP_M", "roots", "km", "uphill_pct",
                                       "path_med_m", "path_p95_m", "n_over_budget",
                                       "n_over_floor", "n_below_outfall", "n_nodes"]]
        out["main_snap_nodes"] = self.snap_sweep
        out["trunk_relief"] = self.relief_tab

        # ------------------------------------------------------------------ the 2-D grid
        # This is a GENUINE TWO-OBJECTIVE TRADE and it is not scalarised, because any
        # exchange rate between "a percentage point of uphill length" and "a kilometre of
        # flow path" would be invented, and this project has withdrawn eight invented
        # numbers in three days.  So the whole grid is published, the PARETO-OPTIMAL
        # settings are marked, and the choice along the front is the ENGINEER'S.
        # The shipped default is the knee, and the two ends of the front are, measured:
        # about 27 % uphill at a 17 km 95th-percentile flow path, or about 47 % uphill at
        # 7 km.  Both are legal; neither is obviously right.
        rows = []
        for lam in (0.0, 1.0, 2.0, 3.0, 5.0, 8.0):
            for det in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
                for meth in ("branching",):
                    tr = self._solve(self.weights(lam, det), join_cost, meth)
                    s = self.score(tr)
                    s["LAMBDA_SLOPE"] = lam
                    s["LAMBDA_DETOUR"] = det
                    s["SHIPPED"] = int(lam == LAMBDA_SLOPE and det == LAMBDA_DETOUR)
                    rows.append(s)
        # the tree this replaces, on the same axes, so the front has a reference point
        s = self.score(self._solve(self.weights(0.0, 0.0), join_cost, "spt"))
        s.update(LAMBDA_SLOPE=0.0, LAMBDA_DETOUR=0.0, SHIPPED=0,
                 tree="A naive shortest-path tree (reference)")
        rows.append(s)
        grid = pd.DataFrame(rows)
        up = grid.uphill_pct.to_numpy(float)
        p95 = grid.path_p95_m.to_numpy(float)
        grid["PARETO"] = [int(not ((up < up[i]) & (p95 < p95[i])).any())
                          for i in range(len(grid))]
        grid = grid.sort_values(["uphill_pct", "path_p95_m"]).reset_index(drop=True)
        out["sweep_grid"] = grid
        front = grid[(grid.PARETO == 1) & (grid.tree == "branching")]
        _log(f"  Pareto front on (uphill share, 95th-percentile flow path): "
             f"{len(front)} of {len(grid)} settings")
        for _, r in front.iterrows():
            _log(f"    lam_slope {r.LAMBDA_SLOPE:>4.1f}  lam_detour {r.LAMBDA_DETOUR:>4.2f}"
                 f"  uphill {r.uphill_pct:6.2f} %  path p95 {r.path_p95_m:8,.0f} m"
                 f"  over budget {int(r.n_over_budget):5,d}"
                 f"{'   <- SHIPPED' if r.SHIPPED else ''}")
        self.pareto = front
        for k, v in out.items():
            _log(f"  {k}: {len(v)} rows")
        return out

    # ---------------------------------------------------------------- heads
    def heads(self, tr: Tree) -> pd.DataFrame:
        """The corridors the tree does not use, turned into dead-end heads.

        A spanning tree cannot use every corridor - the leftovers close loops, and the
        network must be a forest (H15).  They are not deleted: the street is there and the
        plots on it need a sewer.  Each becomes a run entering the network at ONE end.

          * a genuine crest inside it, and longer than the built median run -> CUT at the
            crest: two heads, draining both ways.  That is the ridge rule.
          * otherwise -> ONE head, draining to its LOW end, starting FANOUT_OFFSET_M back
            from the chamber at the high end so that chamber keeps a single outlet.

        A corridor whose two ends are within ADVERSE_MIN_M of the same level has no low end
        the terrain can pick; it drains to whichever end already has the shorter flow path,
        which is the "keep a run consistent with its neighbours" rule and never a silent
        default.
        """
        used = set(int(a) for a in tr.arc)
        allidx = np.nonzero(self.edge_in)[0]
        rest = np.array([i for i in allidx if i not in used], dtype=np.int64)
        _log(f"heads: {rest.size:,} corridors close a loop "
             f"({self.L[rest].sum()/1000:,.1f} km) and become dead-end runs")
        prom_min = max(3.0 * self.sigma_dz, T.RIDGE_MIN_PROMINENCE_M)
        rows = []
        for i in rest:
            i = int(i)
            dz = self.dz[i]
            crest = (self.conf[i] == "split" and self.split_kind[i] == "ridge"
                     and self.L[i] > self.RUN_MEDIAN_M
                     and np.isfinite(self.split_at[i])
                     and self.split_prom[i] >= prom_min)
            if crest:
                kind, fwd, why = "split_head", None, "crest inside a long street"
            elif abs(dz) <= ADVERSE_MIN_M:
                # undecidable: keep it consistent with its neighbours
                pu = self._plen[self.u[i]] if np.isfinite(self._plen[self.u[i]]) else np.inf
                pv = self._plen[self.v[i]] if np.isfinite(self._plen[self.v[i]]) else np.inf
                fwd = bool(pv <= pu)
                kind, why = "head", "flat: drained to the end with the shorter flow path"
            else:
                fwd = bool(dz > 0)
                kind, why = "head", "drained to its low end"
            rows.append(dict(i=i, ROLE=kind, FWD=fwd, WHY=why,
                             CREST_M=float(self.split_at[i]) if crest else np.nan))
        return pd.DataFrame(rows)

    # ---------------------------------------------------------------- sub-networks
    def subnetworks(self, tr: Tree) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """One row per sub-network, with the gravity early warning, and the NEIGHBOUR TEST.

        The warning is arithmetic, not a claim: over each node's flow path, the ground fall
        AVAILABLE minus the fall the tree DEMANDS at the DN200 minimum gradient.  A deficit
        larger than the workable depth budget (MAX_COVER - MIN_COVER = 10.70 m, G203-p33)
        says that branch cannot reach its outfall on gravity inside the cover cap - BEFORE
        a single invert is set.

        It is deliberately pessimistic on the big pipes: Table 11 lets DN900 and above be
        laid at 0.75 mm/m, so a trunk needs less fall than 5.00 mm/m buys.  Both bounds are
        reported.

        Then, and only then, the philosophy's cheap step: for every sub-network that breaches
        the budget, EVERY arc crossing into a neighbouring sub-network is tested as an
        alternative outlet, and the best is reported with what it would cost.  Skipping this
        and going straight to the pump ladder buys stations nobody needed.
        """
        out = self._outfall
        plen, pfall, preq = self._plen, self._pfall, self._preq
        deficit = preq - pfall                       # + = the tree wants more fall than exists
        req_floor = plen * SMIN_FLOOR
        deficit_floor = req_floor - pfall
        self.deficit = deficit

        # Vectorised, and it had to be: the outfall rule multiplies the sub-network count,
        # and the previous per-sub-network scan over every tree arc was already 1.8 million
        # Python iterations at 193 sub-networks.  Every tree arc belongs to exactly one
        # sub-network - the one its UPSTREAM node drains to - so the whole table is two
        # group-bys.
        arc_us = np.where(tr.fwd, self.u[tr.arc], self.v[tr.arc])
        arc_sub = out[arc_us]
        A = pd.DataFrame(dict(SUB=arc_sub, L=self.L[tr.arc], Q=self.Q[tr.arc],
                              ZUS=self.NZ[arc_us]))
        A = A[A.SUB >= 0].copy()
        A["ZOUT"] = self.NZ[A.SUB.to_numpy(np.int64)]
        A["BELOW_L"] = np.where(A.ZUS < A.ZOUT - ADVERSE_MIN_M, A.L, 0.0)
        ga = A.groupby("SUB")
        km_by = ga.L.sum() / 1000.0
        q_by = ga.Q.sum()
        below_by = ga.BELOW_L.sum() / 1000.0

        nix = np.nonzero(out >= 0)[0]
        N = pd.DataFrame(dict(SUB=out[nix], I=nix, Z=self.NZ[nix], PLEN=plen[nix],
                              PFALL=pfall[nix], DEF=deficit[nix], DEFF=deficit_floor[nix]))
        gn = N.groupby("SUB")
        n_by = gn.size()
        pathmax = gn.PLEN.max()
        fallmin = gn.PFALL.min()
        nbelow = gn.PFALL.apply(lambda s: int((s < -ADVERSE_MIN_M).sum()))
        defmax = gn.DEF.max()
        deffl = gn.DEFF.max()
        nover = gn.DEF.apply(lambda s: int((s > DEPTH_BUDGET_M).sum()))
        lowi = N.loc[gn.Z.idxmin(), ["SUB", "I"]].set_index("SUB").I

        rows = []
        for j in sorted(set(int(x) for x in out if x >= 0)):
            km = float(km_by.get(j, 0.0))
            lo = int(lowi.get(j, j))
            head_m = float(self.NZ[j] - self.NZ[lo])
            off_m = float(plen[lo]) if np.isfinite(plen[lo]) else 0.0
            # WHERE THE SUBNETWORK JOINS THE MAIN PIPE, AND WHY NOT AT ITS OWN LOW POINT.
            # The vocabulary is closed so the column can be counted; the SIZE is in
            # JOIN_OFF_M, HEAD_M and LOW_DMAIN, which is where a size belongs.
            if head_m <= ADVERSE_MIN_M:
                why = ""                                  # it joins AT its own low point
            elif float(self.trunk_relief[lo]) < 0.0:
                why = ("the true low point lies BELOW the Main Pipe beside it - gravity "
                       "cannot reach the trunk there at all")
            else:
                why = ("no corridor meets the Main Pipe at the true low point; joined at "
                       "the nearest corridor node that does")
            rows.append(dict(
                SUBNET="", OUTFALL=self.node_ids[j], N_NODES=int(n_by.get(j, 0)), KM=km,
                Q_M3D=float(q_by.get(j, 0.0)),
                X=float(self.NX[j]), Y=float(self.NY[j]), Z=float(self.NZ[j]),
                D_MAIN_M=float(self.d_main[j]),
                # --- the outfall rule, published per sub-network -------------------------
                JOIN_MAIN=1,
                LOW_NODE=self.node_ids[lo], LOW_Z=float(self.NZ[lo]),
                LOW_DMAIN=float(self.d_main[lo]),
                HEAD_M=round(head_m, 3),
                JOIN_OFF_M=round(off_m, 1),
                JOIN_WHY=why,
                BELOW_KM=round(float(below_by.get(j, 0.0)), 3),
                BELOW_PCT=round(100.0 * float(below_by.get(j, 0.0)) / km, 2) if km > 0
                else 0.0,
                # -------------------------------------------------------------------------
                PATH_MAX_M=float(pathmax.get(j, 0.0)),
                # the LEAST fall any node in this sub-network has to its outfall.  Negative
                # means that node sits BELOW the point where its branch meets the trunk, so
                # the flow has to climb before it has bought a single millimetre of gradient.
                FALL_MIN_M=float(fallmin.get(j, 0.0)),
                N_BELOW=int(nbelow.get(j, 0)),
                DEF_MAX_M=float(defmax.get(j, 0.0)) if np.isfinite(defmax.get(j, 0.0))
                else 0.0,
                DEF_FLOOR_M=float(deffl.get(j, 0.0)) if np.isfinite(deffl.get(j, 0.0))
                else 0.0,
                N_OVER_BUDGET=int(nover.get(j, 0))))
        sn = pd.DataFrame(rows).sort_values("KM", ascending=False).reset_index(drop=True)
        sn["SUBNET"] = [f"S{i+1:03d}" for i in range(len(sn))]
        sn["GRAVITY"] = np.where(sn.DEF_MAX_M <= DEPTH_BUDGET_M, "gravity",
                                 np.where(sn.DEF_FLOOR_M <= DEPTH_BUDGET_M,
                                          "gravity if the big pipes are laid flat",
                                          "NOT on gravity inside the cover cap"))
        j2s = {self.nid[r.OUTFALL]: r.SUBNET for r in sn.itertuples()}
        self.subnet_of = {int(a): j2s[int(out[a])] for a in np.nonzero(out >= 0)[0]}

        # ---- THE OUTFALL RULE, REPORTED EVERY RUN -----------------------------------
        # W11b shipped 42 components discharging with more than half their catchment BELOW
        # the outlet - 389.5 km, worst outlet 22.8 m above its own low point - and nothing
        # in the pipeline said so.  It says so here, on every build, in the manifest and in
        # the report, whether the number is bad or good.
        self.sn_by_outfall = {self.nid[r.OUTFALL]: r for r in sn.itertuples()}
        bad = sn[sn.BELOW_PCT > BELOW_OUTLET_FAIL_PCT]
        self.n_below_half = int(len(bad))
        self.km_below_half = float(bad.KM.sum())
        self.worst_head_m = float(sn.HEAD_M.max()) if len(sn) else 0.0
        self.km_below_all = float(sn.BELOW_KM.sum())
        # NO TREE ARC drains into these.  Not quite the same thing as "nothing arrives":
        # `KM` sums the TREE arcs only, and a dead-end HEAD can still discharge at an
        # outfall, so this is an UPPER bound on the joins that carry no flow.  Said here
        # rather than in the headline, because the headline number is the one that gets
        # quoted.  Nothing removes these: `meet_main_pipe` only ever ADDS an outfall, and
        # no later pass takes one away - which is inheritance-ledger row 4 unclosed for the
        # minting step, and the reason the count is published on every build.
        self.n_empty_outfall = int((sn.KM <= 0).sum())
        inplay_set = set(int(i) for i in np.nonzero(self.edge_in)[0])
        head_idx = inplay_set - set(int(a) for a in tr.arc)
        touched = set()
        for i in head_idx:
            touched.add(int(self.u[i])); touched.add(int(self.v[i]))
        self.n_empty_outfall_head = int(sum(
            1 for r in sn.itertuples() if r.KM <= 0 and self.nid[r.OUTFALL] in touched))
        # THE COUNT AND THE REASON COLUMN MUST BE THE SAME SET.  `JOIN_OFF_M > 0` is true
        # of almost every sub-network - it only says the low point is a DIFFERENT NODE from
        # the outlet - while `JOIN_WHY` is written only where the outlet is genuinely ABOVE
        # that low point.  Counting the first and describing the second published a number
        # most of whose rows carried no explanation.  The rule is stated on LEVEL, not on
        # distance ("the LOWEST POINT where it meets"), so the count is the rows with a
        # reason, and the rows whose low point is a different node at the SAME level are
        # published separately rather than folded in or dropped.
        _why = sn.JOIN_WHY.astype(str)
        self.n_join_offset = int((_why.str.len() > 0).sum())
        self.n_low_node_level = int(((sn.JOIN_OFF_M > 0) & (_why.str.len() == 0)).sum())
        _log(f"  outfall rule: {len(sn):,} sub-networks; "
             f"{self.n_below_half} discharge with more than "
             f"{BELOW_OUTLET_FAIL_PCT:g} % of their catchment BELOW the outlet "
             f"({self.km_below_half:,.1f} km); worst outlet sits "
             f"{self.worst_head_m:,.2f} m above its own low point; "
             f"{self.n_join_offset} join ABOVE their true low point and carry a reason; "
             f"{self.n_low_node_level} more have their low point at another node but at "
             f"the same level")
        if self.n_empty_outfall:
            _log(f"  {self.n_empty_outfall} outfall(s) have no TREE arc draining into them "
                 f"- published with KM = 0 rather than dropped. "
                 f"{self.n_empty_outfall_head} of them still touch a dead-end head, so the "
                 f"joins that genuinely carry nothing are between "
                 f"{self.n_empty_outfall - self.n_empty_outfall_head} and "
                 f"{self.n_empty_outfall}. NOTHING REMOVES THEM: this pass only ever adds "
                 f"an outfall (inheritance row 4, unclosed for the minting step)")

        # --- ASK THE NEIGHBOURS, BEFORE CALLING ANYTHING A PUMP -----------------------
        # Philosophy sec 5: when a run cannot reach its outfall by gravity, the first
        # question is not how deep or whether to pump - it is whether a NEIGHBOURING
        # sub-network takes it and at what cost.  Skipping this step buys stations nobody
        # needed, and it is the cheap one.
        #
        # It is asked PER NODE, not per sub-network, because that is where the problem
        # actually is: a sub-network breaches because one branch inside it cannot reach the
        # outfall, and the sub-network's boundary may be nowhere near that branch.
        #
        # And the re-route need not be AT the breaching node.  A node deep in the interior
        # is helped just as much by its branch being diverted at any point BETWEEN it and
        # its outfall.  So: every node y that touches a different sub-network gets its best
        # alternative costed once; then every breaching node x walks its own flow path
        # looking for the best such y on it.  The new deficit for x is
        #     (distance x->y  +  path from the neighbour  +  the connecting corridor)
        #     x the DN200 minimum  -  (x's level - the neighbour's outfall level)
        # which assumes x's branch re-routes and nothing else moves.  A FIRST-ORDER answer,
        # stated as one: a full re-solve would move the neighbour's own tree too.
        breach_nodes = np.nonzero(np.isfinite(deficit) & (deficit > DEPTH_BUDGET_M))[0]
        if breach_nodes.size:
            _log(f"  {breach_nodes.size:,} node(s) in {int((sn.N_OVER_BUDGET > 0).sum())} "
                 f"sub-network(s) breach the {DEPTH_BUDGET_M:.2f} m depth budget; asking "
                 f"the neighbours before calling any of it a pump")
        inplay = np.nonzero(self.edge_in)[0]
        inc: Dict[int, List[int]] = {}
        for i in inplay:
            inc.setdefault(int(self.u[i]), []).append(int(i))
            inc.setdefault(int(self.v[i]), []).append(int(i))
        # step 1 - the best alternative at every node that touches another sub-network
        alt: Dict[int, Tuple[float, int, int, float]] = {}
        for y, arcs_at in inc.items():
            best = None
            for i in arcs_at:
                z = int(self.v[i]) if int(self.u[i]) == y else int(self.u[i])
                if out[z] < 0 or out[z] == out[y] or not np.isfinite(plen[z]):
                    continue
                cand = (float(plen[z] + self.L[i]), z, int(out[z]), float(self.L[i]))
                if best is None or cand[0] < best[0]:
                    best = cand
            if best is not None:
                alt[y] = best
        # step 2 - every breaching node walks its own path looking for one
        nb_rows = []
        n_reachable = 0
        for x in breach_nodes:
            x = int(x)
            y, dist, best, guard = x, 0.0, None, 0
            while y >= 0 and guard < 1_000_000:
                a = alt.get(y)
                if a is not None:
                    cand = float((dist + a[0]) * SMIN_DN200 - (self.NZ[x] - self.NZ[a[2]]))
                    if best is None or cand < best[0]:
                        best = (cand, y, a[1], a[3], dist)
                nxt = tr.parent.get(y, -1)
                if nxt is None or nxt < 0:
                    break
                e = tr.via.get(y, -1)
                dist += 0.0 if e < 0 else float(self.L[e])
                y = nxt
                guard += 1
            if best is None:
                continue
            n_reachable += 1
            nb_rows.append(dict(
                NODE=self.node_ids[x], SUBNET=self.subnet_of.get(x, ""),
                WAS_M=round(float(deficit[x]), 2),
                DIVERT_AT=self.node_ids[best[1]],
                DIVERT_DOWN_M=round(best[4], 1),
                TO_NODE=self.node_ids[best[2]],
                TO_SUBNET=self.subnet_of.get(best[2], ""),
                EXTRA_M=round(best[3], 1), DEF_M=round(best[0], 2),
                RESCUED=int(best[0] <= DEPTH_BUDGET_M)))
        nb = pd.DataFrame(nb_rows)
        self.n_breach = int(breach_nodes.size)
        self.n_breach_reachable = n_reachable
        if len(nb):
            nb = nb.sort_values(["RESCUED", "WAS_M"], ascending=[False, False])
            resc = int(nb.RESCUED.sum())
            _log(f"    {n_reachable:,} of the {breach_nodes.size:,} breaching nodes have a "
                 f"neighbouring sub-network somewhere on their flow path; diverting there "
                 f"keeps {resc:,} of them on gravity "
                 f"({100.0*resc/max(breach_nodes.size,1):.1f} % of all breaches). The rest "
                 f"is where the pump ladder legitimately starts.")
            per = (nb.groupby("SUBNET")
                     .agg(N_BREACH=("NODE", "size"), N_RESCUED=("RESCUED", "sum"),
                          WORST_WAS_M=("WAS_M", "max"), WORST_AFTER_M=("DEF_M", "max"))
                     .reset_index())
            sn = sn.merge(per, on="SUBNET", how="left")
            sn[["N_BREACH", "N_RESCUED"]] = sn[["N_BREACH", "N_RESCUED"]].fillna(0)
        return sn, nb

    # ---------------------------------------------------------------- publish
    def build(self, publish: bool = True) -> dict:
        self.measure()
        # THE OUTFALL RULE COMES FIRST, before the ridge rule, because it changes which
        # corridors exist: a street cut where it meets the trunk is two streets, and the
        # crest test then applies to the halves that will actually be built.
        self.meet_main_pipe()
        self.presplit_ridges()
        self.find_roots()
        self._arc_arrays()
        self._detour()

        cmp_df = self.compare()
        sw = self.sweeps()
        self.published_snap = sw["sweep_main_snap"]

        _log("solving the shipped tree")
        tr = self.solve_with_bends()
        # ... and then TAKE AWAY the outlet assignments the ground says were wrong
        tr = self.reroot_below_outfall(tr)
        self.tree = tr
        sc = self.score(tr)
        hd = self.heads(tr)
        sn, nb = self.subnetworks(tr)

        arcs = self._arc_frame(tr, hd)
        nodes = self._node_frame(tr)
        whole = self._headline(arcs)
        # How many heads start at a chamber that already has an outlet.  Each of those needs
        # the FANOUT_OFFSET_M setback at the chamber stage - philosophy sec 4, "10 m
        # clearance between a branch start and the chamber it joins" - so it is a HAND-OVER
        # NUMBER, counted here rather than discovered there.
        outl = set(arcs.loc[arcs.ROLE == "tree", "US_NODE"])
        hh = arcs[arcs.ROLE.isin(["head", "split_head"])]
        km = float(sc["km"]) or 1.0
        whole["heads_setback"] = int(hh.US_NODE.isin(outl).sum())
        whole["heads_n"] = int(len(hh))
        whole["junctions_per_km"] = float((nodes.KIND == "junction").sum() / km)
        whole["heads_per_km"] = float((nodes.KIND == "head").sum() / km)

        man = self._manifest(sc, whole, cmp_df, sn, nb)
        if publish:
            self._write(arcs, nodes, sn, nb, cmp_df, sw, man)
        self.published = dict(arcs=arcs, nodes=nodes, subnets=sn, neighbours=nb,
                              compare=cmp_df, manifest=man, **sw)
        return self.published

    def _arc_frame(self, tr: Tree, hd: pd.DataFrame):
        """Every corridor, oriented, with its weight broken out term by term."""
        from shapely.ops import substring
        gpd = self.gpd
        cor = self.cor
        w = self.weights_used
        pos = {int(e): k for k, e in enumerate(self._idx)}
        ang_by_arc = {}
        for k, e, fwd, node, inlet in self.last_angles:
            ang_by_arc[int(e)] = inlet

        recs, geoms = [], []

        def push(i, fwd, role, why, geom, crest=np.nan):
            i = int(i)
            us, ds = (cor.US_NODE.iloc[i], cor.DS_NODE.iloc[i]) if fwd else \
                     (cor.DS_NODE.iloc[i], cor.US_NODE.iloc[i])
            k = pos.get(i)
            sdz = self.dz[i] if fwd else -self.dz[i]
            frac = geom.length / max(cor.geometry.iloc[i].length, 1e-9)
            wl = self.L[i] * frac
            ws = (w["Sf"][k] if fwd else w["Sb"][k]) * wl if k is not None else np.nan
            wd = (w["det_f"][k] if fwd else w["det_b"][k]) if k is not None else np.nan
            wb = (w["bf"][k] if fwd else w["bb"][k]) if k is not None else np.nan
            terms = {"length": wl, "slope": LAMBDA_SLOPE * ws,
                     "detour": LAMBDA_DETOUR * (wd if np.isfinite(wd) else 0.0),
                     "bend": LAMBDA_BEND * (wb if np.isfinite(wb) else 0.0)}
            tot = float(sum(terms.values()))
            dom = max(terms, key=lambda t: terms[t])
            recs.append(dict(
                CID=str(cor.CID.iloc[i]), US_NODE=str(us), DS_NODE=str(ds),
                LEN_M=float(geom.length), ROLE=role, WHY=why,
                GRD_US=float(self.NZ[self.u[i] if fwd else self.v[i]]),
                GRD_DN=float(self.NZ[self.v[i] if fwd else self.u[i]]),
                FALL_M=float(sdz * frac),
                SLOPE_PCT=float(100.0 * sdz * frac / max(geom.length, 1e-9)),
                UPHILL=int(sdz * frac < -ADVERSE_MIN_M),
                DIR_CONF=str(self.conf[i]), P_CORR=float(self.p_corr[i]),
                W_LEN=round(float(terms["length"]), 2),
                W_SLOPE=round(float(terms["slope"]), 2),
                W_DETOUR=round(float(terms["detour"]), 2),
                W_BEND=round(float(terms["bend"]), 2),
                W_TOT=round(tot, 2), W_DOM=dom,
                INLET_DEG=round(float(ang_by_arc.get(i, np.nan)), 1),
                CREST_M=float(crest),
                N_PLOT=float(cor.N_PLOT.iloc[i]) * frac,
                Q_M3D=float(cor.Q_NEAR_M3D.iloc[i]) * frac,
                SUBNET=self.subnet_of.get(int(self.v[i] if fwd else self.u[i]), ""),
                SRC=str(cor.SRC.iloc[i]), CONFIDENCE=str(cor.CONFIDENCE.iloc[i]),
                # H1 / project rule 7, carried from the corridor this arc came from.  It is
                # RE-MEASURED below on every arc this stage cut, because a cut renames the
                # piece and an inherited flag on a renamed piece is a guess.
                ALONG_DUAL=int(cor.ALONG_DUAL.iloc[i]) if "ALONG_DUAL" in cor.columns else 0,
                DUAL_ANG=float(cor.DUAL_ANG.iloc[i]) if "DUAL_ANG" in cor.columns else -1.0,
                H1_KEEP=int(cor.H1_KEEP.iloc[i]) if "H1_KEEP" in cor.columns else 0,
                TAU_FLAG=TAU_FLAG))
            geoms.append(geom if fwd else
                         geom.reverse() if hasattr(geom, "reverse") else geom)

        for e, fwd in zip(tr.arc, tr.fwd):
            push(int(e), bool(fwd), "tree", "in the drainage tree",
                 cor.geometry.iloc[int(e)])
        for _, r in hd.iterrows():
            i = int(r.i)
            g = cor.geometry.iloc[i]
            if r.ROLE == "split_head":
                at = float(r.CREST_M)
                a, b = substring(g, 0.0, at), substring(g, at, g.length)
                push(i, False, "split_head", "cut at the crest, drains to the low end", a,
                     crest=at)
                push(i, True, "split_head", "cut at the crest, drains to the low end", b,
                     crest=at)
            else:
                push(i, bool(r.FWD), "head", str(r.WHY), g)

        # everything the tree could not reach at all.  Oriented to its low end anyway, so
        # the layer carries a direction rather than the draughtsman's drawing order - but
        # PROVISIONAL, because a corridor with no outfall has no drainage direction in the
        # sense the rest of this layer means.
        for i in np.nonzero(~self.edge_in)[0]:
            i = int(i)
            push(i, bool(self.dz[i] >= 0), "island",
                 "no path to the client's Main Pipe; direction provisional",
                 cor.geometry.iloc[i])
        for _, r in self.selfloop.iterrows():
            recs.append(dict(CID=str(r.CID), US_NODE=str(r.US_NODE), DS_NODE=str(r.DS_NODE),
                             LEN_M=float(r.LEN_M), ROLE="ring",
                             WHY="a closed ring: both ends are the same node",
                             GRD_US=np.nan, GRD_DN=np.nan, FALL_M=np.nan, SLOPE_PCT=np.nan,
                             UPHILL=0, DIR_CONF="", P_CORR=np.nan, W_LEN=np.nan,
                             W_SLOPE=np.nan, W_DETOUR=np.nan, W_BEND=np.nan, W_TOT=np.nan,
                             W_DOM="", INLET_DEG=np.nan, CREST_M=np.nan,
                             N_PLOT=float(r.N_PLOT), Q_M3D=float(r.Q_NEAR_M3D), SUBNET="",
                             SRC=str(r.SRC), CONFIDENCE=str(r.CONFIDENCE),
                             ALONG_DUAL=int(getattr(r, "ALONG_DUAL", 0)),
                             DUAL_ANG=float(getattr(r, "DUAL_ANG", -1.0)),
                             H1_KEEP=int(getattr(r, "H1_KEEP", 0)),
                             TAU_FLAG=TAU_FLAG))
            geoms.append(r.geometry)
        gdf = gpd.GeoDataFrame(recs, geometry=geoms, crs=f"EPSG:{CRS_EPSG}")
        self._remeasure_dual(gdf)

        # THE OUTFALL RULE, CHECKED ON THE GEOMETRY ABOUT TO BE PUBLISHED.  `X_MAIN` counts
        # the places the arc meets the client's Main Pipe with NO node of its own on the
        # meeting point - a flow path that reaches the trunk, ignores it and grows out the
        # other side.  A crossing that DOES carry a node is a legal junction, because that
        # node is an outfall and the flow discharges there.  It must be 0 on every DRAINED
        # arc, and it is measured here, from the written geometry, never carried from the
        # pass that made it.
        from shapely.ops import unary_union
        main = unary_union(list(self.main.geometry))
        gdf["X_MAIN"] = self.meets_off_node(gdf.geometry)
        gdf["D_MAIN_M"] = np.round(gdf.geometry.distance(main).to_numpy(float), 2)
        drained = gdf.ROLE.isin(["tree", "head", "split_head"])
        self.n_cross_main = int((gdf.loc[drained, "X_MAIN"] > 0).sum())
        self.km_cross_main = float(gdf.loc[drained & (gdf.X_MAIN > 0), "LEN_M"].sum()
                                   / 1000.0)
        if self.n_cross_main:
            _log(f"  WARNING: {self.n_cross_main} drained arc(s) still meet the Main Pipe "
                 f"with no node on the meeting point ({self.km_cross_main:.2f} km). The "
                 f"outfall rule is NOT satisfied and the count is published as X_MAIN.")
        else:
            _log("  outfall rule: no drained arc meets the Main Pipe without a node on it "
                 "(X_MAIN = 0 everywhere)")
        return gdf

    def _node_frame(self, tr: Tree):
        from shapely.geometry import Point
        gpd = self.gpd
        plen, pfall, preq = self._plen, self._pfall, self._preq
        out = self._outfall
        deg_in = np.zeros(self.NV, int)
        for child, e in tr.via.items():
            if e >= 0:
                p = tr.parent.get(child, -1)
                if p >= 0:
                    deg_in[p] += 1
        by_out = getattr(self, "sn_by_outfall", {})
        meet = set(getattr(self, "meet_nodes", []))
        recs = []
        for a in range(self.NV):
            p = tr.parent.get(a, None)
            # THE OUTFALL RULE lives on the node that makes the join, so it can be read
            # straight off the map.  JOIN_OFF_M is the distance from the sub-network's TRUE
            # low point to this connection - 0.0 when it joins AT it - and JOIN_WHY is only
            # written where the offset is real, so a column of explanations cannot hide the
            # ones that matter.
            row = by_out.get(a)
            o = int(self._outfall[a])
            recs.append(dict(
                NODE_ID=self.node_ids[a], X=float(self.NX[a]), Y=float(self.NY[a]),
                GRD_M=float(self.NZ[a]),
                DS_NODE=("" if p is None else ("MAIN_PIPE" if p < 0
                                               else self.node_ids[p])),
                N_IN=int(deg_in[a]),
                KIND=("outfall" if p is not None and p < 0 else
                      "head" if deg_in[a] == 0 else
                      "junction" if deg_in[a] > 1 else "through"),
                SUBNET=self.subnet_of.get(a, ""),
                JOIN_MAIN=int(row is not None),
                JOIN_OFF_M=float(row.JOIN_OFF_M) if row is not None else 0.0,
                JOIN_WHY=(row.JOIN_WHY if row is not None else ""),
                LOW_NODE=(row.LOW_NODE if row is not None else ""),
                BELOW_OUT=int(o >= 0 and self.NZ[a] < self.NZ[o] - ADVERSE_MIN_M),
                MEET_MAIN=int(self.node_ids[a] in meet),
                PATH_M=float(plen[a]) if np.isfinite(plen[a]) else np.nan,
                FALL_M=float(pfall[a]) if np.isfinite(pfall[a]) else np.nan,
                REQ_M=float(preq[a]) if np.isfinite(preq[a]) else np.nan,
                DEF_M=float(preq[a] - pfall[a]) if np.isfinite(preq[a] - pfall[a]) else np.nan,
                OVER_BUD=int(np.isfinite(preq[a] - pfall[a]) and
                             (preq[a] - pfall[a]) > DEPTH_BUDGET_M),
                D_MAIN_M=float(self.d_main[a]), TAU_FLAG=TAU_FLAG))
        return gpd.GeoDataFrame(recs, geometry=[Point(x, y) for x, y in zip(self.NX, self.NY)],
                                crs=f"EPSG:{CRS_EPSG}")

    def _headline(self, arcs) -> dict:
        """The number that matters, over the WHOLE published network - which is what
        W11a's 42.5 % was quoted over, so it is the only like-for-like comparison."""
        d = arcs[arcs.ROLE.isin(["tree", "head", "split_head"])]
        L = d.LEN_M.to_numpy(float)
        f = d.FALL_M.to_numpy(float)
        up = f < -ADVERSE_MIN_M
        t = d[d.ROLE == "tree"]
        return dict(
            published_km=float(arcs.LEN_M.sum() / 1000.0),
            drained_km=float(L.sum() / 1000.0),
            uphill_pct_all=float(L[up].sum() / L.sum() * 100.0),
            uphill_km_all=float(L[up].sum() / 1000.0),
            uphill_pct_tree=float(t.loc[t.FALL_M < -ADVERSE_MIN_M, "LEN_M"].sum() /
                                  t.LEN_M.sum() * 100.0),
            climb_m=float(-f[f < 0].sum()), descent_m=float(f[f > 0].sum()),
            climb_per_km=float(-f[f < 0].sum() / (L.sum() / 1000.0)),
            ratio=float(-f[f < 0].sum() / max(f[f > 0].sum(), 1e-9)),
            worst_rise_m=float(-np.nanmin(f)),
            island_km=self.island_km, island_q_m3d=self.island_q)

    # ---------------------------------------------------------------- manifest + write
    def _manifest(self, sc, whole, cmp_df, sn, nb) -> pd.DataFrame:
        naive = cmp_df.iloc[0]
        rows = [
            ("stage", STAGE_VERSION, "", "this file"),
            ("criteria", CR.CRITERIA_VERSION, "", "w12/criteria.py"),
            ("run_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "", ""),
            ("corridors_sha1", _sha1(ROADS_GPKG), "", ROADS_GPKG),
            ("h1_corridors_along_in", self.h1_in["corridors_along"], "",
             "corridors arriving from stage 1 still flagged ALONG a dual carriageway. Stage "
             "1 excludes every ALONG run it can; what is left is what excluding would sever, "
             "each carrying H1_KEEP = 1 and a price - an OPEN H1 breach, not a pass"),
            ("h1_cut_arcs", getattr(self, "dual_remeasure", {}).get("cut_arcs", -1), "",
             "arcs this stage CUT, i.e. carrying a CID `corridors` does not hold. Their dual "
             "flag is not inherited, it is RE-MEASURED - an inherited flag describes the "
             "PARENT's geometry, and `s8_export` recovers the flag by a CID lookup whose miss "
             "used to fill in as 0"),
            ("h1_remeasured", getattr(self, "dual_remeasure", {}).get("remeasured", -1), "",
             "of those, how many were re-measured against the tagged dual = 1 centrelines"),
            ("h1_cut_newly_along", getattr(self, "dual_remeasure", {}).get(
                "changed_to_along", -1), "",
             "CUTS THAT PUT A PIECE ALONG A CARRIAGEWAY the whole corridor was not. This is "
             "the question 'did the outfall cut re-introduce a dual run', answered by "
             "measurement on every run rather than checked once. Above zero it is an H1 "
             "breach THIS STAGE CREATED and it belongs back in stage 1's exclusion"),
            ("h1_cut_cleared", getattr(self, "dual_remeasure", {}).get(
                "changed_to_clear", -1), "",
             "cuts whose piece left the band the parent was in"),
            ("h1_arcs_along_n", getattr(self, "dual_remeasure", {}).get("along_n", -1), "",
             "arcs published ALONG a dual carriageway, after the re-measure"),
            ("h1_arcs_along_m", getattr(self, "dual_remeasure", {}).get("along_m", -1.0),
             "m", "and their length"),
            ("h1_remeasure_note", getattr(self, "dual_remeasure", {}).get("note", ""), "",
             "blank when the re-measure ran; otherwise why it did not"),
            ("h1_band_m", getattr(self, "dual_remeasure", {}).get("band_m", -1.0), "m",
             "the band half-width this stage re-measured on. READ from stage 1's manifest, "
             "never defined here - two values for one quantity is the defect "
             "tests/test_constants.py exists for. Re-published so the run says what it "
             "actually used, and verify() checks it still agrees with the file it came from"),
            ("h1_skew_deg", getattr(self, "dual_remeasure", {}).get("skew_deg", -1.0), "deg",
             "the tolerance on 'square', read the same way"),
            ("h1_min_frac", getattr(self, "dual_remeasure", {}).get("min_frac", -1.0), "",
             "stage 1's share-of-a-line-inside-the-band rule, read the same way. IT IS NOT "
             "APPLIED HERE. It is valid in stage 1 only because split_at_band cuts every "
             "line at that same band first; this stage cuts at crests and at the Main Pipe, "
             "so a cut piece can straddle the band edge and the rule would refuse to judge "
             "it and publish a zero that reads as 'clear of a carriageway'. Read and "
             "re-published purely so verify() can check the two stages still agree on it"),
            ("h1_skipped_by_frac_rule", getattr(self, "dual_remeasure", {}).get(
                "skipped_by_frac_rule", -1), "",
             "cut arcs the whole-line fraction rule would have refused to judge. The size of "
             "the trap, measured every run"),
            ("h1_frac_rule_would_have_hidden", getattr(self, "dual_remeasure", {}).get(
                "frac_rule_would_have_hidden", -1), "",
             "of those, how many DO run along a carriageway on the in-band run. Above zero, "
             "that many H1 breaches were being published as zeros"),
            ("main_pipe_sha1", _sha1(os.path.splitext(MAIN_PIPE)[0] + ".shp"), "", MAIN_PIPE),
            ("terrain_grid", GRID, "", "w12/terrain.py, 5 m working grid"),
            # --- guideline constants
            ("SMIN_DN200", SMIN_DN200, "m/m", "G203-p29 Tab 11, DN200 row (5.00 mm/m)"),
            ("SMIN_FLOOR", SMIN_FLOOR, "m/m", "G203-p29 Tab 11, '900 and above' (0.75 mm/m)"),
            ("MIN_COVER_M", MIN_COVER_M, "m", "G203-p33 sec 4.6.3"),
            ("MAX_COVER_M", MAX_COVER_M, "m", "G203-p33 sec 4.6.3 (recommended 10-12 m)"),
            ("DEPTH_BUDGET_M", DEPTH_BUDGET_M, "m", "MAX_COVER - MIN_COVER, by subtraction"),
            ("INLET_MIN_DEG", INLET_MIN_DEG, "deg", "G203-p30, verbatim"),
            ("FANOUT_OFFSET_M", FANOUT_OFFSET_M, "m", "PROJECT rule, user 2026-08-18"),
            ("ADVERSE_MIN_M", ADVERSE_MIN_M, "m", "PROJECT ASSUMPTION - below this a rise "
                                                  "is DEM noise"),
            # --- measured
            ("RUN_MEDIAN_M", round(self.RUN_MEDIAN_M, 3), "m",
             "MEASURED asbuilt.m_runs() - the ridge-split threshold"),
            ("SIGMA_DZ_M", round(self.sigma_dz, 4), "m",
             "MEASURED differential DEM error vs NAMA's surveyed levels"),
            ("RIDGE_PROM_MIN_M", round(max(3 * self.sigma_dz, T.RIDGE_MIN_PROMINENCE_M), 3),
             "m", "3 x SIGMA_DZ_M"),
            ("BUILT_UPHILL_PCT", round(self.BUILT_UPHILL_PCT, 2), "%",
             "MEASURED asbuilt.m_terrain() - CONTEXT, NOT PERMISSION"),
            ("BUILT_JOINS", self.BUILT_JOINS, "", "MEASURED asbuilt joins onto the trunk"),
            ("BUILT_VORTEX", self.BUILT_VORTEX, "", "MEASURED vortex drops in the built net"),
            ("W11A_UPHILL_PCT", W11A_UPHILL_PCT, "%",
             "criteria.BENCHMARKS - the defect W12 exists to fix"),
            # --- project choices
            ("LAMBDA_SLOPE", LAMBDA_SLOPE, "", "PROJECT, swept: sweep_lambda_slope"),
            ("SLOPE_CAP", SLOPE_CAP, "", "PROJECT"),
            ("LAMBDA_DETOUR", LAMBDA_DETOUR, "", "PROJECT, forced by measurement, swept"),
            ("LAMBDA_BEND", LAMBDA_BEND, "", "PROJECT"),
            ("BEND_EQUIV_M", BEND_EQUIV_M, "m", "PROJECT"),
            ("BEND_PASSES", BEND_PASSES, "", "PROJECT"),
            ("JOIN_COST_M", JOIN_COST_M, "m", "PROJECT, swept: sweep_join_cost"),
            # --- the outfall rule
            ("MEET_TOL_M", MEET_TOL_M, "m",
             "DERIVED from criteria.MH_SNAP_M, the node-merge radius s1_roads used to node "
             "the corridor graph. The distance at which a corridor MEETS the Main Pipe. "
             "It replaced a PROJECT 5.0 m chosen by eye (engineer 2026-09-06: the tolerance "
             "that decides where a network discharges may not be invented). Swept"),
            ("MAIN_SNAP_M", MAIN_SNAP_M, "m",
             "the same number under its old name, swept: sweep_main_snap"),
            ("REROOT_PASSES", REROOT_PASSES, "",
             "PROJECT, STRUCTURAL cap only - the loop stops when a pass moves nothing"),
            ("DETOUR_RATIO_MAX", DETOUR_RATIO_MAX, "",
             "MEASURED BOUND, 10_ASBUILT_CALIBRATION.md sec 1: detour ratio p90 2.26, "
             "<= 5 % above 4.0. A re-root may not buy a lower outlet past it"),
            ("BELOW_OUTLET_FAIL_PCT", BELOW_OUTLET_FAIL_PCT, "%",
             "the ENGINEER'S OWN threshold, quoted from the defect register: '42 components "
             "discharge with MORE THAN HALF their catchment BELOW the outlet'"),
            ("TAU_PA", C.TAU_PA, "Pa", "ENGINEER 2026-09-03, GAP-9 open - flagged on output"),
            # --- inputs measured this run
            ("corridors_n", int(len(self.cor)), "", "after the ridge pre-split"),
            ("corridor_km", round(float(self.cor.LEN_M.sum() / 1000), 2), "km", ""),
            ("nodes_n", int(self.NV), "", ""),
            ("ridge_splits", int(self.ridge_splits), "", "corridors cut at a crest"),
            ("outfalls_n", int(len(self.roots)), "",
             f"corridor nodes within {MAIN_SNAP_M:g} m of the Main Pipe"),
            ("main_pipe_km", round(self.main_km, 2), "km", "client INPUT"),
            ("closed_basins_n", self.basins_n, "", "terrain.py"),
            ("closed_basins_forced", self.basins_forced, "",
             "basins deeper than the cover cap - roots if any"),
            ("flat_ground_pct", round(self.flat_pct, 2), "%",
             "corridor length on ground flatter than SMIN_DN200 either way"),
            ("flat_ground_km", round(self.flat_km, 1), "km", "the same, in km"),
            # --- results
            ("tree_arcs", sc["arcs"], "", "the drainage tree"),
            ("tree_km", round(sc["km"], 2), "km", ""),
            ("joins_realised", sc["joins"], "",
             f"onto the Main Pipe; NAMA built {self.BUILT_JOINS}"),
            ("subnetworks_n", int(len(sn)), "", "each ends at exactly one outfall"),
            # --- THE OUTFALL RULE, measured on this run
            ("meet_corridors_cut", int(getattr(self, "meet_splits", 0)), "",
             "corridors cut where they MEET the Main Pipe, so no flow path can cross it "
             "and grow past it. W11b shipped 214 arcs / 48.49 km that did"),
            ("meet_nodes_minted", int(len(getattr(self, "meet_nodes", []))), "",
             "new nodes ON the Main Pipe; every one of them is an outfall, asserted in "
             "find_roots"),
            ("meet_rounds", int(len(getattr(self, "meet_rounds", []))), "",
             "rounds the cut needed. A cut can reveal a meeting point the uncut corridor "
             "hid, so it repeats; measured on the real corridor set it converges in one"),
            ("meet_points_lost_at_an_end", int(getattr(self, "n_meet_end_gap", -1)), "",
             f"NAMED GAP. Meeting points dropped because they sit within {MEET_TOL_M:g} m "
             f"ALONG the corridor of one of its ends, where that END NODE is itself "
             f"further than {MEET_TOL_M:g} m from the trunk. A close approach can be "
             f"{MEET_TOL_M:g} m from the trunk AND {MEET_TOL_M:g} m from the node, so the "
             f"two distances can differ by a factor of two. No node is minted and no "
             f"outfall is created, so a CANDIDATE OUTLET is lost - listed row by row in "
             f"`meet_cuts_end_gap`. A crossing cannot land here (it lies ON the trunk, so "
             f"an end within tolerance along the line is within tolerance of the trunk), "
             f"which is why the no-crossing rule is unaffected"),
            ("corridors_meeting_off_node", int(getattr(self, "n_meet_off_node", -1)), "",
             "corridors still meeting the Main Pipe with no node on the meeting point, "
             "measured on the CORRIDOR set after the cut. MUST BE 0"),
            ("arcs_crossing_main", int(getattr(self, "n_cross_main", -1)), "",
             "drained arcs that STILL cross the Main Pipe, recomputed from the published "
             "geometry. MUST BE 0 - it is the outfall rule's own check"),
            ("km_crossing_main", round(float(getattr(self, "km_cross_main", 0.0)), 3), "km",
             "the length of those, if any"),
            ("reroot_converged", int(bool(getattr(self, "reroot_converged", False))), "",
             "1 = the last re-rooting pass moved nothing. 0 means the published "
             "below-outlet length is an UPPER BOUND and REROOT_PASSES needs raising"),
            ("reroot_branches_moved", int(getattr(self, "reroot_moved", 0)), "",
             "branches re-pointed to a LOWER outfall after the branching had assigned them. "
             "Inheritance ledger row 4 in its general form: anything a pass can ADD, a "
             "later pass must be able to TAKE AWAY, and the stage publishes how many"),
            ("subnets_below_half", int(getattr(self, "n_below_half", -1)), "",
             f"sub-networks discharging with more than {BELOW_OUTLET_FAIL_PCT:g} % of their "
             f"catchment BELOW the outlet. W11b: 42 components, 389.5 km. THIS IS THE "
             f"NUMBER THE OUTFALL RULE EXISTS TO DRIVE TO ZERO"),
            ("km_below_half", round(float(getattr(self, "km_below_half", 0.0)), 2), "km",
             "the length in those sub-networks"),
            ("km_below_outlet", round(float(getattr(self, "km_below_all", 0.0)), 2), "km",
             "length of tree arc whose upstream node sits below its own outfall, over the "
             "WHOLE network - the objective the re-rooting pass drives down"),
            ("worst_outlet_above_low_m",
             round(float(getattr(self, "worst_head_m", 0.0)), 2), "m",
             "the worst outfall's height above its own sub-network's low point. W11b: 22.8 m"),
            ("subnets_joining_off_low", int(getattr(self, "n_join_offset", 0)), "",
             "sub-networks whose outlet sits ABOVE their own low point - the rule is on "
             "LEVEL, not on distance. Every one of them carries JOIN_OFF_M (the distance), "
             "HEAD_M (the height) and JOIN_WHY (the reason), so the count and the reason "
             "column are the same set of rows"),
            ("subnets_low_point_at_another_node",
             int(getattr(self, "n_low_node_level", 0)), "",
             f"sub-networks whose lowest node is not the outlet but is within "
             f"{ADVERSE_MIN_M:g} m of its level. They join at the lowest point in every "
             f"sense the DEM can resolve, so they carry no JOIN_WHY - published here "
             f"rather than folded into the row above, which is what hid them"),
            ("outfalls_with_no_catchment", int(getattr(self, "n_empty_outfall", 0)), "",
             "outfalls with no TREE arc draining into them. Published with KM = 0, never "
             "dropped - W11b shipped 15 of these on its station layer unremarked. It is an "
             "UPPER bound on the joins that carry no flow, because KM counts tree arcs "
             "only and a dead-end head can still discharge at one. INHERITANCE ROW 4 IS "
             "NOT CLOSED HERE: meet_main_pipe only ever ADDS an outfall and no later pass "
             "takes one away, so a spurious trunk connection can only be flagged, not "
             "removed - the engineer's call, and the same shape as W11b's 15 stations"),
            ("outfalls_with_no_catchment_but_a_head",
             int(getattr(self, "n_empty_outfall_head", 0)), "",
             "of those, the ones a dead-end head still discharges at, so the number of "
             "joins carrying genuinely nothing is the row above MINUS this one"),
            ("heads_n", whole["heads_n"], "", "dead-end runs: the corridors the tree could "
                                              "not use, all draining to their low end"),
            ("heads_needing_setback", whole["heads_setback"], "",
             f"heads starting at a chamber that already has an outlet, so the chamber stage "
             f"must set them back {FANOUT_OFFSET_M:g} m (philosophy sec 4). A HAND-OVER "
             f"NUMBER, counted here rather than discovered there"),
            ("junctions_per_km", round(whole["junctions_per_km"], 2), "1/km",
             "MEASURED built network 4.83 (asbuilt.m_runs)"),
            ("heads_per_km", round(whole["heads_per_km"], 2), "1/km",
             "MEASURED built network 5.09 (asbuilt.m_runs)"),
            ("UPHILL_PCT_PUBLISHED", round(whole["uphill_pct_all"], 2), "%",
             f"THE HEADLINE. W11a {W11A_UPHILL_PCT:.1f} %, built network "
             f"{self.BUILT_UPHILL_PCT:.1f} %"),
            ("UPHILL_KM_PUBLISHED", round(whole["uphill_km_all"], 1), "km", ""),
            ("uphill_pct_tree_only", round(whole["uphill_pct_tree"], 2), "%",
             "over the tree arcs alone, excluding dead-end heads"),
            ("uphill_pct_naive", round(float(naive.uphill_pct_all), 2), "%",
             "THE SAME GRAPH with the method this replaces, on the SAME BASIS - the whole "
             "in-play corridor length, dead-end heads included, exactly as "
             "UPHILL_PCT_PUBLISHED is measured. This is the evidence"),
            ("uphill_pct_naive_tree_only", round(float(naive.uphill_pct), 2), "%",
             "the same tree measured over its own arcs only, to compare with "
             "uphill_pct_tree_only"),
            ("climb_m", round(whole["climb_m"], 0), "m", "cumulative climb along the flow"),
            ("descent_m", round(whole["descent_m"], 0), "m", ""),
            ("climb_per_km", round(whole["climb_per_km"], 2), "m/km",
             f"built network {self.BUILT_CLIMB_PER_KM:.2f}"),
            ("worst_rise_m", round(whole["worst_rise_m"], 2), "m", "worst single reach"),
            ("path_median_m", round(sc["path_med_m"], 0), "m", "flow path to the outfall"),
            ("path_p95_m", round(sc["path_p95_m"], 0), "m", ""),
            ("path_max_m", round(sc["path_max_m"], 0), "m", ""),
            ("published_km", round(whole["published_km"], 2), "km", "every corridor"),
            ("island_km", round(whole["island_km"], 2), "km",
             "cannot reach the Main Pipe at all"),
            ("island_q_m3d", round(whole["island_q_m3d"], 0), "m3/d", ""),
            ("nodes_over_budget", sc["n_over_budget"], "",
             f"flow path demands more fall than the ground gives, by more than "
             f"{DEPTH_BUDGET_M:.2f} m, charged at the DN200 minimum"),
            ("nodes_over_budget_floor", sc["n_over_floor"], "",
             "the same charged at G203-p29 Tab 11's flattest gradient (0.75 mm/m) - "
             "THE HARD NUMBER: it cannot be argued away by sizing"),
            ("nodes_total", sc["n_nodes"], "", "nodes with a flow path to an outfall"),
            ("subnets_over_budget", int((sn.N_OVER_BUDGET > 0).sum()), "",
             f"deficit beyond the {DEPTH_BUDGET_M:.2f} m depth budget"),
            ("breaching_nodes", int(getattr(self, "n_breach", 0)), "",
             f"nodes whose flow path demands more fall than the ground gives, by more than "
             f"the {DEPTH_BUDGET_M:.2f} m depth budget"),
            ("breaching_with_a_neighbour", int(getattr(self, "n_breach_reachable", 0)), "",
             "of those, the ones with a different sub-network somewhere on their flow path, "
             "so the neighbour question can even be asked"),
            ("neighbour_rescues", int(nb.RESCUED.sum()) if len(nb) else 0, "",
             "of those, the ones a NEIGHBOURING sub-network keeps on gravity. Philosophy "
             "sec 5's cheap step, run before anything is called a station"),
        ]
        return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "SOURCE"])

    def _remeasure_dual(self, gdf) -> None:
        """RE-MEASURE H1 on every arc this stage CUT, instead of trusting the flag it
        inherited from the corridor it was cut out of.

        WHY.  This stage does not move a metre of geometry, but it does CUT: 151 corridors
        at a crest and 229 where they meet the client's Main Pipe, and each cut piece gets a
        NEW CID - `9DF3.1` becomes `9DF3.1/m0`, `9DF3.1/m1`.  Measured on the run of
        2026-09-06 that is 814 arcs and 109.67 km whose CID exists nowhere in `corridors`.
        Two things follow and both are defects:

          * `s8_export` recovers the dual flag with `seg_cid.map(corr.ALONG_DUAL).fillna(0)`,
            so on every one of those 814 arcs the published flag is a FILLNA, not a
            measurement.  A zero that means "the lookup missed" is indistinguishable from a
            zero that means "this pipe is nowhere near a carriageway" - which is the
            no-data-treated-as-safe defect (tests/test_nodata.py) in a new place.
          * an inherited flag is a claim about the PARENT's geometry.  Halving a line that
            grazed a band leaves one half inside it and one half out, and the flag is wrong
            on both.

        So the flag is carried through the cut for the arcs that were NOT cut, and MEASURED
        from the geometry for the ones that were, against the same tagged `dual = 1`
        centrelines and the same three constants stage 1 uses.  Both counts are published.

        Measured on 2026-09-06 the re-measure changed NO arc: none of the 814 cut pieces
        lands along a tagged carriageway, and the four that touch a band touch it for less
        than a micrometre at the band edge.  That is the answer to "did the outfall cut
        re-introduce a dual run" - and it is now an answer this stage RE-DERIVES every run
        rather than a fact someone checked once.

        If the recorded centrelines cannot be read the arcs keep their inherited flag and
        the manifest says the re-measure did not run.  A skip that says so is honest; a
        silent zero is not.
        """
        import math

        K = _h1_constants()
        band_m = K["DUAL_BAND_M"]
        skew_deg = K["DUAL_XING_SKEW_DEG"]
        min_frac = K["IN_BAND_MIN_FRAC"]

        gdf["DUAL_SRC"] = "inherited from the corridor, uncut"
        self.dual_remeasure = {"read": 0, "cut_arcs": 0, "remeasured": 0,
                               "band_m": band_m, "skew_deg": skew_deg,
                               "min_frac": min_frac,
                               "changed_to_along": 0, "changed_to_clear": 0,
                               "skipped_by_frac_rule": 0,
                               "frac_rule_would_have_hidden": 0,
                               "along_n": int((gdf.ALONG_DUAL.astype(int) == 1).sum()),
                               "along_m": round(float(
                                   gdf.loc[gdf.ALONG_DUAL.astype(int) == 1, "LEN_M"].sum()), 1),
                               "note": ""}
        cut = ~gdf.CID.isin(set(self.cor0_cids))
        self.dual_remeasure["cut_arcs"] = int(cut.sum())
        if not cut.any():
            self.dual_remeasure["note"] = "this stage cut nothing; nothing to re-measure"
            return
        if not os.path.exists(ROAD_REC):
            self.dual_remeasure["note"] = (
                f"NOT RUN: {ROAD_REC} is missing, so {int(cut.sum())} cut arcs keep the flag "
                f"they inherited. That is a claim about their PARENT geometry, not about "
                f"them")
            gdf.loc[cut, "DUAL_SRC"] = "inherited onto a CUT piece - NOT re-measured"
            return

        from shapely.ops import unary_union
        from shapely.strtree import STRtree

        rec = self.gpd.read_file(ROAD_REC)
        d1 = [g for g in rec[rec["dual"] == 1].geometry.values if g is not None]
        self.dual_remeasure["read"] = len(d1)
        if not d1:
            self.dual_remeasure["note"] = "the recorded centrelines tag no dual carriageway"
            return
        band = unary_union([g.buffer(band_m) for g in d1])
        t1 = STRtree(d1)

        def bearing(line, at, half=2.0):
            a = line.interpolate(max(0.0, at - half))
            b = line.interpolate(min(line.length, at + half))
            return math.degrees(math.atan2(b.y - a.y, b.x - a.x))

        # MEASURED ON THE IN-BAND RUN, NOT ON THE WHOLE ARC.  `min_frac` asks how much of a
        # line is inside the band before it is judged, and stage 1 may use it because
        # `split_at_band` cuts every line AT that band first, so an in-band piece scores 1.0.
        # THIS stage cuts at crests and at the Main Pipe, which the band knows nothing about,
        # so a cut piece can straddle the band edge and score 0.4 - and a filter that then
        # refuses to judge publishes ALONG_DUAL = 0, a zero meaning "not measured" that reads
        # as "clear of a carriageway".  That is the same defect this function exists to close
        # in s8's `.fillna(0)`, and it was live in s1's own `measure_dual_exposure` until
        # 2026-09-06, where it pinned the 4 m exposure at zero.  So the run is measured on
        # its own terms and the fraction is published as a diagnostic rather than a gate.
        floor = 1e-3      # below the writing tolerance a "run" is the band edge, not geometry
        idx = np.nonzero(cut.to_numpy())[0]
        for i in idx:
            i = int(i)
            g = gdf.geometry.iloc[i]
            was = int(gdf.ALONG_DUAL.iloc[i])
            now, ang = 0, -1.0
            if g is not None and g.length > 0 and g.intersects(band):
                inter = g.intersection(band)
                runs = ([inter] if inter.geom_type == "LineString"
                        else [p for p in getattr(inter, "geoms", [])
                              if p.geom_type == "LineString"])
                for p in sorted(runs, key=lambda q: -q.length):
                    if p.length <= floor:
                        break
                    mid = p.interpolate(0.5, normalized=True)
                    c = d1[t1.nearest(mid)]
                    a = abs((bearing(p, p.length * 0.5)
                             - bearing(c, c.project(mid), half=5.0) + 90.0) % 180.0 - 90.0)
                    if ang < 0.0:
                        ang = a
                    if a < (90.0 - skew_deg):
                        now, ang = 1, a
                        break
            gdf.iloc[i, gdf.columns.get_loc("ALONG_DUAL")] = now
            gdf.iloc[i, gdf.columns.get_loc("DUAL_ANG")] = round(float(ang), 1)
            gdf.iloc[i, gdf.columns.get_loc("DUAL_SRC")] = "MEASURED on the cut piece"
            if now and not was:
                self.dual_remeasure["changed_to_along"] += 1
            elif was and not now:
                self.dual_remeasure["changed_to_clear"] += 1
            # what the whole-line fraction rule would have refused to judge here. Published
            # so the trap is visible as a number rather than as an argument in a comment.
            if g is not None and g.length > 0 and g.intersects(band):
                if g.intersection(band).length / g.length < min_frac:
                    self.dual_remeasure["skipped_by_frac_rule"] += 1
                    if now:
                        self.dual_remeasure["frac_rule_would_have_hidden"] += 1
        self.dual_remeasure["remeasured"] = len(idx)
        self.dual_remeasure["along_n"] = int((gdf.ALONG_DUAL.astype(int) == 1).sum())
        self.dual_remeasure["along_m"] = round(float(
            gdf.loc[gdf.ALONG_DUAL.astype(int) == 1, "LEN_M"].sum()), 1)
        r = self.dual_remeasure
        _log(f"  H1 re-measured on {r['remeasured']:,} arcs this stage CUT "
             f"({r['cut_arcs']:,} carry a CID `corridors` does not hold): "
             f"{r['changed_to_along']} newly ALONG, {r['changed_to_clear']} cleared. "
             f"Published ALONG total {r['along_n']} arcs / {r['along_m']:,.1f} m")
        if r["changed_to_along"]:
            _log(f"    THE CUT PUT {r['changed_to_along']} PIECE(S) ALONG A DUAL "
                 f"CARRIAGEWAY that the whole corridor was not. That is an H1 breach this "
                 f"stage CREATED and it belongs back in stage 1's exclusion.")

    def _write(self, arcs, nodes, sn, nb, cmp_df, sw, man):
        os.makedirs(RUN, exist_ok=True)
        os.makedirs(os.path.dirname(OUT_GPKG), exist_ok=True)
        if os.path.exists(OUT_GPKG):
            os.remove(OUT_GPKG)
        _log(f"writing {OUT_GPKG}")
        arcs.to_file(OUT_GPKG, layer="arcs", driver="GPKG")
        nodes.to_file(OUT_GPKG, layer="nodes", driver="GPKG")
        tabs = dict(subnets=sn, neighbours=nb, compare=cmp_df, manifest=man,
                    bend_passes=self.bend_hist, ridge_splits=self.split_rows,
                    meet_cuts=getattr(self, "meet_rows", None),
                    meet_cuts_end_gap=getattr(self, "meet_end_gap", None),
                    meet_rounds=getattr(self, "meet_rounds", None),
                    reroot_passes=getattr(self, "reroot_hist", None), **sw)
        for name, df in tabs.items():
            if df is None or not len(df):
                df = pd.DataFrame([{"NOTE": "empty"}])
            _write_table(df, name)
            df.to_csv(os.path.join(RUN, f"{name}.csv"), index=False)
        with open(MANIFEST_JSON, "w", encoding="utf-8") as fh:
            json.dump({r.ITEM: r.VALUE for _, r in man.iterrows()}, fh, indent=1,
                      default=str)
        self._kmz(arcs)
        self._write_report(arcs, sn, nb, cmp_df, man)

    def _kmz(self, arcs):
        """Google Earth, on `present.py`'s own `ground_fall` view.

        Worth the twenty lines: `present.py` recomputes the uphill share from the published
        columns with its OWN test - a negative ground slope rather than this file's
        ADVERSE_MIN_M dead band - so the KMZ's caption is an independent recount of the
        headline, not a copy of it.  If the two disagree by more than the dead band, one of
        them is wrong.
        """
        try:
            from w12 import present as P
        except Exception as exc:                                   # pragma: no cover
            self.notes.append(f"KMZ skipped: {exc}")
            return
        d = arcs[arcs.ROLE.isin(["tree", "head", "split_head"])].copy()
        for view, tag in (("ground_fall", "ground_fall"), ("subnet", "subnets")):
            try:
                out = os.path.join(W12, "shp", f"W12_orient_{tag}.kmz")
                r = P.kmz(d, view, out, source=f"{STAGE_VERSION}  {TAU_FLAG}")
                _log(f"  KMZ {os.path.basename(out)}: {r.features:,} features"
                     + (f", present.py's independent recount of the uphill share "
                        f"{r.stats.get('pct_length_uphill')} %"
                        if "pct_length_uphill" in r.stats else ""))
            except Exception as exc:                               # pragma: no cover
                self.notes.append(f"KMZ '{view}' skipped: {exc}")
                _log(f"  KMZ '{view}' skipped: {exc}")

    def _write_report(self, arcs, sn, nb, cmp_df, man):
        mv = {r.ITEM: r.VALUE for _, r in man.iterrows()}
        L = []
        A = L.append
        A("# W12 stage 2 - orientation: what the tree actually achieved\n")
        A(f"_{time.strftime('%Y-%m-%d %H:%M')} - {STAGE_VERSION} - {TAU_FLAG}_\n")
        A("## The headline\n")
        A(f"**{mv['UPHILL_PCT_PUBLISHED']} % of the published length "
          f"({mv['UPHILL_KM_PUBLISHED']} km) drains against the ground.**  "
          f"W11a measured **{W11A_UPHILL_PCT:.1f} %**; NAMA's own built network runs "
          f"**{self.BUILT_UPHILL_PCT:.2f} %** uphill, which is context and not permission.  "
          f"The same graph with the method W11a used gives "
          f"**{mv['uphill_pct_naive']} %**, so the improvement is "
          f"**{float(mv['uphill_pct_naive']) - float(mv['UPHILL_PCT_PUBLISHED']):.1f} "
          f"percentage points** and it is attributable to the algorithm and the weights, "
          f"not to a different input.\n")
        A(f"Over the **tree arcs alone** - excluding the {int(mv['heads_n']):,} dead-end "
          f"heads, which drain to their low end by construction and so cannot be uphill - "
          f"the figure is **{mv['uphill_pct_tree_only']} %**.  That is the honest measure "
          f"of the orientation itself; the published figure above is the one that compares "
          f"like for like with W11a's, which was also quoted over a whole published "
          f"network.  Both are in the manifest and neither is the headline on its own.\n")
        A(f"Cumulative climb **{mv['climb_m']:,.0f} m** against **{mv['descent_m']:,.0f} m** "
          f"of descent; **{mv['climb_per_km']} m** of climb per km of sewer against the "
          f"built network's **{self.BUILT_CLIMB_PER_KM:.2f}**.\n")
        A("## The outfall rule - where each sub-network joins the trunk\n")
        A(f"**A sub-network joins the Main Pipe at the lowest point where it MEETS it, and "
          f"nothing crosses the trunk and grows past it** (engineer 2026-09-05/06; "
          f"philosophy sec 9).  \"Meets\" is **{MEET_TOL_M:g} m**, which is not a number "
          f"chosen here: it is `criteria.MH_SNAP_M`, the node-merge radius `s1_roads` used "
          f"to node the whole corridor graph.  Two positions closer than that are one node "
          f"in the published topology, so a corridor passing within it of the trunk already "
          f"shares a node with it in every sense the graph can express.  Anything wider is a "
          f"spur - a real pipe, and an engineer's decision, swept below.\n")
        A(f"The test moved from the NODE to the CORRIDOR, and that is the whole fix.  W11b "
          f"asked whether a node was near the trunk; a 200 m street crossing the trunk at "
          f"its midpoint has both ends 100 m away, so it crossed and kept going.  Measured "
          f"on W11b's own shipped layer: **214 arcs, 48.49 km, physically crossed the Main "
          f"Pipe**.  Here **{mv['meet_corridors_cut']:,} corridors were cut at "
          f"{mv['meet_nodes_minted']:,} new nodes**, every one of them an outfall, and the "
          f"published layer carries `X_MAIN` per arc: "
          f"**{mv['arcs_crossing_main']} drained arcs still cross** "
          f"({mv['km_crossing_main']} km).\n")
        A(f"**{mv['subnetworks_n']:,} sub-networks.**  That count is much higher than "
          f"W11b's 193 and the rise is the intended result - the engineer's words are "
          f"*\"more subnetworks worth keeping the work clean, rather than monster useless "
          f"subnetworks\"*.  W11b's two largest held a quarter of the entire network "
          f"between them while discharging somewhere else entirely.\n")
        A(f"**{mv['subnets_below_half']} sub-networks discharge with more than "
          f"{BELOW_OUTLET_FAIL_PCT:g} % of their catchment BELOW the outlet** "
          f"({mv['km_below_half']} km), and the worst outfall sits "
          f"**{mv['worst_outlet_above_low_m']} m above its own low point**.  W11b shipped "
          f"42 such components, 389.5 km, worst 22.8 m.  Over the whole network "
          f"**{mv['km_below_outlet']} km** of pipe drains up to reach its own outlet.\n")
        A(f"Getting there took **{mv['reroot_branches_moved']:,} branches re-pointed to a "
          f"lower outfall** after the branching had already assigned them.  That is "
          f"inheritance-ledger row 4 in its general form - *anything a pass can ADD, a "
          f"later pass must be able to TAKE AWAY, and the stage publishes how many* - and "
          f"the per-pass table shows it converging rather than claiming it:\n")
        if getattr(self, "reroot_hist", None) is not None and len(self.reroot_hist):
            A(_md(self.reroot_hist, 2))
            A("")
        A(f"**{mv['subnets_joining_off_low']} sub-networks join away from their true low "
          f"point.**  Each carries `JOIN_OFF_M`, the distance from that low point along its "
          f"own flow path, and `JOIN_WHY`, which is one of two things: no corridor meets the "
          f"trunk at the low point, or the low point lies BELOW the trunk beside it and "
          f"gravity cannot reach it there at all.  The reason vocabulary is closed so the "
          f"column can be counted; the SIZE is in `JOIN_OFF_M`, `HEAD_M` and `LOW_DMAIN`, "
          f"which is where a size belongs.\n")
        A("## What a better tree cannot fix\n")
        A(f"**{mv['flat_ground_pct']} % of the corridor network - {mv['flat_ground_km']} km "
          f"- lies on ground falling more gently than the minimum gradient a DN200 may be "
          f"laid at** (5.00 mm/m, G203-p29 Tab 11).  There the pipe sinks below the surface "
          f"whichever way it points and no orientation helps.  Terrain confidence over the "
          f"corridor length: " +
          ", ".join(f"{k} {v:.1f} %" for k, v in self.conf_share.items() if v > 0) + ".\n")
        A("## The evidence - four trees on the same graph\n")
        A(_md(cmp_df[["tree", "km", "uphill_pct", "uphill_pct_all", "climb_m", "joins",
                      "path_med_m", "path_p95_m", "path_max_m", "n_over_budget"]], 1))
        A("\n`uphill_pct` is over each tree's own arcs; `uphill_pct_all` adds the dead-end "
          "heads, which drain to their low end whichever tree is built, and is therefore "
          "the column to compare with W11a's published 42.5 %.  **Part of the gap between "
          "the two columns is not orientation at all**: a branching leaves more corridors "
          "unused than a shortest-path tree does, and every unused corridor becomes a head "
          "that drains downhill.  That is a real property of the network that gets built - "
          "a dead-end run genuinely does drain downhill - but it is not the algorithm "
          "pointing pipes better, and it is why both columns are printed instead of "
          "whichever one flatters the answer.")
        A("\n\n**Read the last four columns.** An optimum branching minimises the sum of "
          "arc costs and has no term at all for how far one property's sewage then travels. "
          "That is why a detour term was added, why it is swept and published rather than "
          "asserted, and why `n_over_budget` - the count of nodes whose flow path demands "
          "more fall than the ground gives, by more than the workable depth - is in the "
          "same table.  A long path buys depth debt at every metre of it, so the two "
          "columns are not independent and the trade is not the one it first looks like.\n")
        A("**And there is a result in this table nobody was looking for.**  Charged at the "
          "DN200 minimum, the SHORT-PATH trees are the feasible ones (A 3,845 nodes over "
          "budget, D 5,615).  Charged at Table 11's FLATTEST gradient - the one a DN900 or "
          "larger may be laid at - the order reverses (D 613, A 1,254): with the gradient "
          "cost almost gone, all that is left is whether the pipe points downhill, and the "
          "branching wins.  Read together that says the two methods belong to different "
          "TIERS: the trunk and the sub mains, which are large and laid flat, want the "
          "downhill-biased branching, and the laterals, which are DN200 and pay 5.00 mm/m "
          "for every metre, want short paths.  This stage cannot act on that - it has no "
          "tiers yet - but the hierarchy stage can, and the numbers are here for it.\n")
        A("## The trade the engineer has to make, and it is not scalarised\n")
        A("Two objectives pull against each other and there is no exchange rate between "
          "them that is not invented: **a percentage point of uphill length** against "
          "**a kilometre of flow path**.  So the whole weight grid is published, the "
          "Pareto-optimal settings are marked, and the shipped default is the knee.  Move "
          "`LAMBDA_SLOPE` and `LAMBDA_DETOUR` at the top of `s2_orient.py` to move along "
          "the front.\n")
        if getattr(self, "pareto", None) is not None and len(self.pareto):
            A(_md(self.pareto[["LAMBDA_SLOPE", "LAMBDA_DETOUR", "uphill_pct", "km",
                               "path_med_m", "path_p95_m", "path_max_m",
                               "n_over_budget", "n_over_floor", "SHIPPED"]], 1))
            A("")
        A(f"`n_over_budget` is the count of the {int(mv['nodes_total']):,} nodes whose flow "
          f"path demands more fall, at the DN200 minimum, than the ground gives - by more "
          f"than the {DEPTH_BUDGET_M:.2f} m of workable depth.  "
          f"`n_over_floor` is the same count charged at the FLATTEST gradient Table 11 "
          f"allows any pipe (0.75 mm/m, DN900 and above).  **The floor figure is the hard "
          f"one**: it is what remains when every pipe on the path is a large one laid as "
          f"flat as the guideline permits, and it cannot be argued away by sizing.\n")
        A("## The bend term, and why it is the weak one\n")
        A(_md(self.bend_hist, 2))
        A("\n\nA turn is a property of two arcs and an arborescence weight can only see one, "
          "so this is iterative re-weighting.  The table is here so the reader can see "
          "whether it converged instead of taking a claim for it.\n")
        A("## Sub-networks and the gravity early warning\n")
        A(f"{len(sn)} sub-networks, each ending at exactly one outfall.  "
          f"{int((sn.N_OVER_BUDGET > 0).sum())} of them contain at least one node whose flow "
          f"path demands more fall than the ground provides, by more than the "
          f"{DEPTH_BUDGET_M:.2f} m of workable depth between the 1.30 m minimum cover and "
          f"the 12 m cap (both G203-p33).  That is arithmetic available BEFORE any invert is "
          f"set; it is deliberately pessimistic, because it charges every metre at the "
          f"DN200 minimum and Table 11 lets DN900 and above be laid at 0.75 mm/m "
          f"(`DEF_FLOOR_M` is the same sum at that floor).\n")
        A("**Two things overstate this deficit and both should be read before anyone "
          "prices a pumping station on it.**  First, the outfall level used is the GROUND "
          "at the point the corridor meets the Main Pipe - the trunk's own INVERT is not "
          "known (NWS still owe the existing works inlet invert), so every deficit is "
          "overstated by the trunk's depth there, somewhere between the 1.30 m minimum "
          "cover and the 8.78 m the trunk reaches at the works.  Second, it charges the "
          "DN200 minimum for the whole path; `DEF_FLOOR_M` is the same sum at Table 11's "
          "flattest gradient and is the figure that cannot be argued away by sizing.\n")
        A(_md(sn, 1, maxrows=25))
        A("\n\n### Asking the neighbours first\n")
        if len(nb):
            resc = int(nb.RESCUED.sum())
            A(f"**{self.n_breach:,} nodes breach the depth budget.  "
              f"{self.n_breach_reachable:,} of them have a different sub-network somewhere "
              f"on their flow path, and diverting the branch there keeps {resc:,} of them "
              f"on gravity - {100.0*resc/max(self.n_breach,1):.1f} % of all the breaches - "
              f"for a connecting corridor of median {nb.EXTRA_M.median():.0f} m.**  The "
              f"remaining {self.n_breach - resc:,} are where the pump ladder legitimately "
              f"starts.  This is philosophy sec 5's cheap step and it is run before "
              f"anything here is called a station.  The 25 worst are below; the full list "
              f"is `run/orient/neighbours.csv`.\n")
            A(_md(nb.sort_values("WAS_M", ascending=False), 2, maxrows=25))
            A("")
        else:
            A("No node breached the depth budget, so the neighbour test had nothing "
              "to run on.\n")
        A("## Is the client's trunk above the town?\n")
        A("A fair question, because if it were, no tree could drain into it.  Corridor node "
          "level less the ground level of the nearest point on the Main Pipe:\n")
        A(_md(self.relief_tab, 2))
        A("\n\nSo the trunk sits at about town level and is not the cause.\n")
        A("## The one lever with a big number on it: how close is 'meets the trunk'\n")
        A(f"The shipped radius is {MAIN_SNAP_M:g} m - a corridor node that literally touches "
          f"the Main Pipe.  Allowing a short spur instead changes the gravity picture "
          f"materially, and that is an engineer's decision, not a tolerance:\n")
        A(_md(self.published_snap, 1) if getattr(self, "published_snap", None) is not None
          else "")
        A("\n\n## What is NOT decided here\n")
        A("- No chamber, no invert, no diameter, no station.  The levelling stage will still "
          "find this tree infeasible in places; that is what the deficit columns are for.\n"
          f"- {mv['island_km']} km carrying {mv['island_q_m3d']} m3/d has no path to the "
          "client's Main Pipe at all and is published as `ROLE = island`, oriented to its "
          "low end but PROVISIONAL - a corridor with no outfall has no drainage direction "
          "in the sense the rest of the layer means.  That is a scope answer, not a routing "
          "one.\n"
          "- Nothing is deleted and no crossing is manufactured.\n"
          f"- The {mv['tree_arcs']:,} tree arcs are {mv['tree_km']} km; the other "
          f"{float(mv['published_km']) - float(mv['tree_km']) - float(mv['island_km']):,.1f} "
          "km are dead-end heads.  Every head drains to its low end BY CONSTRUCTION, so it "
          "contributes nothing to the uphill share - which is why the tree-only figure "
          f"({mv['uphill_pct_tree_only']} %) is quoted beside the published one and is the "
          "honest measure of the orientation itself.\n")
        A("## Every number in this run\n")
        A(_md(man, 4))
        A("")
        with open(REPORT_MD, "w", encoding="utf-8") as fh:
            fh.write("\n".join(L))
        _log(f"wrote {REPORT_MD}")


# ==========================================================================================
# verification
# ==========================================================================================

def verify() -> dict:
    """Re-read what was written and re-derive the headline from it.

    The headline is recomputed from the WRITTEN US_NODE / DS_NODE strings and the written
    ground levels - never from an in-memory model, never from geometry (H16).  If the
    recomputed value disagrees with the manifest the stage has failed.
    """
    import geopandas as gpd
    arcs = gpd.read_file(OUT_GPKG, layer="arcs")
    nodes = gpd.read_file(OUT_GPKG, layer="nodes")
    man = pd.read_csv(os.path.join(RUN, "manifest.csv"))
    mv = {r.ITEM: r.VALUE for _, r in man.iterrows()}
    fails = []

    d = arcs[arcs.ROLE.isin(["tree", "head", "split_head"])]
    L = d.LEN_M.to_numpy(float)
    f = (d.GRD_US.to_numpy(float) - d.GRD_DN.to_numpy(float))
    up = f < -ADVERSE_MIN_M
    got = float(L[up].sum() / L.sum() * 100.0)
    want = float(mv["UPHILL_PCT_PUBLISHED"])
    if abs(got - want) > 0.05:
        fails.append(f"uphill share recomputed {got:.2f} % vs manifest {want:.2f} %")

    # H15: a forest, and every node has at most one outlet
    if nodes.DS_NODE.astype(str).eq("").sum() != int((nodes.KIND == "").sum()):
        pass
    tree = arcs[arcs.ROLE == "tree"]
    if tree.US_NODE.duplicated().any():
        n = int(tree.US_NODE.duplicated().sum())
        fails.append(f"{n} nodes have more than one outgoing TREE arc - not an arborescence")
    # every tree arc's US node must be a node that exists
    known = set(nodes.NODE_ID.astype(str))
    miss = set(tree.US_NODE.astype(str)) | set(tree.DS_NODE.astype(str))
    miss -= known
    if miss:
        fails.append(f"{len(miss)} node ids on tree arcs are not in `nodes`")
    # loops
    par = dict(zip(tree.US_NODE.astype(str), tree.DS_NODE.astype(str)))
    seen, loops = {}, 0
    for s in par:
        x, path = s, []
        while x in par and x not in seen:
            seen[x] = s
            path.append(x)
            x = par[x]
        if x in par and seen.get(x) == s and x in path:
            loops += 1
    if loops:
        fails.append(f"{loops} loop(s) in the written topology - H15 requires a forest")

    km = float(arcs.LEN_M.sum() / 1000.0)
    if abs(km - float(mv["published_km"])) > 0.05:
        fails.append(f"published km {km:.2f} vs manifest {mv['published_km']}")

    # ---- THE OUTFALL RULE, re-derived from the written layers ------------------------
    # Not from X_MAIN, which the build wrote: from the GEOMETRY, against the client's own
    # Main Pipe file.  A check that reads back the column the build wrote is not a check.
    from shapely.ops import unary_union
    mp = gpd.read_file(MAIN_PIPE)
    if mp.crs is not None and mp.crs.to_epsg() != CRS_EPSG:
        mp = mp.to_crs(CRS_EPSG)
    main = unary_union(list(mp.geometry))
    buf = main.buffer(MEET_TOL_M)
    dr = arcs[arcs.ROLE.isin(["tree", "head", "split_head"])]
    xn = int(sum(1 for g in dr.geometry
                 if meets_without_a_node(g, main, buf, MEET_TOL_M) > 0))
    if xn:
        fails.append(f"{xn} drained arc(s) meet the Main Pipe with no node on the meeting "
                     f"point - they cross it and grow past it, and the outfall rule is "
                     f"broken on the published layer")
    if "arcs_crossing_main" in mv and int(float(mv["arcs_crossing_main"])) != xn:
        fails.append(f"arcs crossing the Main Pipe recomputed {xn} vs manifest "
                     f"{mv['arcs_crossing_main']}")

    # catchment below the outlet, recomputed from the written SUBNET / GRD_US / KIND
    outz = (nodes[nodes.KIND == "outfall"].set_index("SUBNET")["GRD_M"]
            if "SUBNET" in nodes.columns else pd.Series(dtype=float))
    t = arcs[(arcs.ROLE == "tree") & arcs.SUBNET.astype(str).ne("")].copy()
    if len(t) and len(outz):
        t["ZO"] = t.SUBNET.map(outz)
        t = t[t.ZO.notna()]
        t["BL"] = np.where(t.GRD_US.to_numpy(float) < t.ZO.to_numpy(float) - ADVERSE_MIN_M,
                           t.LEN_M.to_numpy(float), 0.0)
        g = t.groupby("SUBNET").agg(KM=("LEN_M", "sum"), BKM=("BL", "sum"))
        pct = 100.0 * g.BKM / g.KM.replace(0.0, np.nan)
        nbad = int((pct > BELOW_OUTLET_FAIL_PCT).sum())
        if "subnets_below_half" in mv and int(float(mv["subnets_below_half"])) != nbad:
            fails.append(f"sub-networks discharging above half their catchment recomputed "
                         f"{nbad} vs manifest {mv['subnets_below_half']}")
    else:
        nbad = -1
        fails.append("the below-outlet check CANNOT RUN on the published layers - a check "
                     "that cannot run is a FAILURE, not a blank (inheritance row 2)")

    # ---- H1 / project rule 7 on the PUBLISHED arcs, re-read from disk -------------------
    # Three things, and each has cost this project a day at some point:
    #   1. ONE VALUE FOR ONE QUANTITY. The band half-width and the skew tolerance are stage
    #      1's; if this stage re-measured on a different band the two layers would disagree
    #      about which pipes are legal and nothing would say so. That is the two-constants
    #      defect (tests/test_constants.py), and it is checked against stage 1's own
    #      manifest rather than against a number typed here twice.
    #   2. NO UNDECLARED BREACH. An arc that runs along a carriageway must carry H1_KEEP = 1,
    #      which is stage 1's declaration that it was retained deliberately and priced. A
    #      breach without that flag is one nobody decided.
    #   3. THE FLAG MUST EXIST AT ALL. `s8_export` recovers it by a CID lookup; a missing
    #      column there fills in as 0 on every row and reads as a clean pass.
    n_along = -1
    if "ALONG_DUAL" not in arcs.columns:
        fails.append("`arcs` publishes no ALONG_DUAL column - s8 recovers the dual flag by "
                     "a CID lookup whose miss fills in as 0, so a missing column here reads "
                     "downstream as 'no pipe is near a carriageway'")
    else:
        al = arcs[arcs.ALONG_DUAL.astype(int) == 1]
        n_along = int(len(al))
        if "H1_KEEP" not in arcs.columns:
            fails.append(f"{n_along} arcs run ALONG a dual carriageway and `arcs` carries no "
                         f"H1_KEEP column to declare them")
        elif len(al) and (al.H1_KEEP.astype(int) != 1).any():
            n = int((al.H1_KEEP.astype(int) != 1).sum())
            fails.append(f"{n} arc(s) run ALONG a dual carriageway without H1_KEEP = 1 - an "
                         f"H1 breach nobody declared. If this stage's CUT created them they "
                         f"belong back in stage 1's exclusion (manifest h1_cut_newly_along)")
    try:
        import sqlite3
        con = sqlite3.connect(ROADS_GPKG)
        try:
            s1man = pd.read_sql("SELECT * FROM manifest", con).set_index("ITEM")["VALUE"]
        finally:
            con.close()
        for item, mine in (("DUAL_BAND_M", "h1_band_m"),
                           ("DUAL_XING_SKEW_DEG", "h1_skew_deg"),
                           ("IN_BAND_MIN_FRAC", "h1_min_frac")):
            if item not in s1man.index or mine not in mv:
                fails.append(f"the H1 constant {item} is not published by both stages, so "
                             f"the two cannot be checked to agree - a check that cannot run "
                             f"is a FAILURE, not a blank")
                continue
            if abs(float(s1man[item]) - float(mv[mine])) > 1e-9:
                fails.append(f"{item} is {mv[mine]} on this stage's manifest and "
                             f"{s1man[item]} on stage 1's - the roads layer changed under "
                             f"this run, or two values exist for one quantity, which is how "
                             f"a 50 mm bedding allowance failed every cover check here")
    except Exception as e:                                   # pragma: no cover - IO
        fails.append(f"could not read stage 1's manifest to check the H1 constants agree "
                     f"({type(e).__name__}: {e}) - a check that cannot run is a FAILURE, "
                     f"not a blank")

    out = dict(ok=not fails, fails=fails, uphill_pct=got, published_km=km,
               arcs_crossing_main=xn, subnets_below_half=nbad,
               arcs_along_dual=n_along,
               arcs=int(len(arcs)), nodes=int(len(nodes)))
    print(json.dumps(out, indent=1))
    return out


def selftest(verbose: bool = True) -> bool:
    """The algorithm proof, plus a real corridor sub-graph as the hardest oracle case."""
    print("Chu-Liu/Edmonds against networkx.minimum_spanning_arborescence:")
    real = None
    try:
        import geopandas as gpd
        cor = gpd.read_file(ROADS_GPKG, layer="corridors")
        cor = cor[cor.US_NODE != cor.DS_NODE]
        # a compact spatial window, so the sub-graph is a real street network
        b = cor.total_bounds
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        # a spatial window cuts the street network into pieces; the oracle needs ONE
        # connected component, because an arborescence over a disconnected graph does not
        # exist and that failure would say nothing about the algorithm
        import networkx as nx
        big, sub = set(), cor.iloc[:0]
        for half in (900, 1400, 2000, 2800, 4000):
            s = cor.cx[cx - half:cx + half, cy - half:cy + half]
            g = nx.Graph()
            g.add_edges_from(zip(s.US_NODE, s.DS_NODE))
            if not g:
                continue
            b = max(nx.connected_components(g), key=len)
            big, sub = b, s[s.US_NODE.isin(b) & s.DS_NODE.isin(b)]
            if len(b) >= 600:            # big enough to be a real test, small enough for nx
                break
        ids = sorted(big)
        nid = {a: i for i, a in enumerate(ids)}
        u = sub.US_NODE.map(nid).to_numpy(); v = sub.DS_NODE.map(nid).to_numpy()
        w = sub.LEN_M.to_numpy(float)
        rng = np.random.default_rng(3)
        w = w * (1.0 + 0.5 * rng.random(w.size))       # break ties, as the real weights do
        n = len(ids) + 1
        U = np.concatenate([v, u, [len(ids)]])
        V = np.concatenate([u, v, [0]])
        W = np.concatenate([w, w * 1.13, [0.0]])
        real = dict(n=n, U=U, V=V, W=W, root=len(ids))
    except Exception as exc:                                       # pragma: no cover
        print(f"  (no real sub-graph: {exc})")
    ok = verify_msa_against_networkx(real_subgraph=real, verbose=verbose)
    print("PASS" if ok else "FAIL")
    return ok


def sweep_only():
    o = Orient()
    o.measure(); o.meet_main_pipe(); o.presplit_ridges(); o.find_roots()
    o._arc_arrays(); o._detour()
    cmp_df = o.compare()
    print("\n=== four trees on the same graph ===")
    print(cmp_df.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
    for k, v in o.sweeps().items():
        print(f"\n=== {k} ===")
        print(v.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "build"
    if cmd == "selftest":
        return 0 if selftest() else 1
    if cmd == "verify":
        return 0 if verify()["ok"] else 1
    if cmd == "sweep":
        sweep_only()
        return 0
    if cmd != "build":
        print(__doc__)
        return 2
    if not selftest(verbose=True):
        print("the optimiser does not agree with networkx - refusing to build")
        return 1
    o = Orient()
    o.build()
    _log(f"done in {time.time() - o.t0:.1f} s")
    r = verify()
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
