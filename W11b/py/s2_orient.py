"""W11b stage 2 - THE DRAINAGE TREE, BUILT DOWNHILL BY CONSTRUCTION.

W11b BORROWS NOTHING.  Nothing in this file is imported from `W8/py/sewnet`, `W10/py` or
`W11a/py`.  The only imports from inside the project are `w11b.criteria`, `w11b.terrain`,
`w11b.asbuilt` and `w11b.contract`, which are W11b's own, plus `w11b.present` for the KMZ.
Earlier folders are read for DATA only.

WHAT THIS STAGE DECIDES, AND WHAT IT DOES NOT
It decides, for every corridor in `W11b/shp/W11b_roads.gpkg`, WHICH WAY THE SEWAGE RUNS,
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

ROOTS.  The outfalls are the corridor nodes that touch the client's Main Pipe, which is an
INPUT (`SHP/Main Pipe/Main Pipe.shp`, 85.49 km).  193 corridor nodes lie within 5 m of it,
and ALL of them are taken.  The intention had been to price a join so the count stayed near
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

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11b/py
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from w11b import criteria as CR                              # noqa: E402
from w11b import terrain as T                                # noqa: E402
from w11b import asbuilt as AB                               # noqa: E402

C = CR.DEFAULT

STAGE = "s2_orient"
STAGE_VERSION = "W11b-orient-1.0"

# ================================================================== paths
W11B = os.path.dirname(_HERE)                                # .../W11b
CLAUDE = os.path.dirname(W11B)                               # .../Hydraulic/Claude
HYDRAULIC = os.path.dirname(CLAUDE)

ROADS_GPKG = os.path.join(W11B, "shp", "W11b_roads.gpkg")
MAIN_PIPE = os.path.join(HYDRAULIC, "SHP", "Main Pipe", "Main Pipe.shp")
OUT_GPKG = os.path.join(W11B, "shp", "W11b_orient.gpkg")
RUN = os.path.join(W11B, "run", "orient")
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
MAIN_SNAP_M = 5.0         # PROJECT. A corridor node this close to the Main Pipe can
#                           discharge into it. 193 nodes qualify; the sensitivity of the
#                           count to this radius is published in `sweep_snap`.
GRID = "R5"               # the 5 m working grid. terrain.py measured native 0.5 m sampling
#                           to be NO more accurate (SD 0.7564 vs 0.7561 m) and to give an
#                           identical drain direction on every decidable test line.

TAU_FLAG = f"tau={C.TAU_PA:g} Pa ASSUMED (GAP-9)"


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
        self.roots = np.nonzero(d <= snap)[0]
        rows = [dict(WITHIN_M=t, N_NODES=int((d <= t).sum())) for t in
                (1, 3, 5, 10, 15, 20, 25, 30, 50, 100, 200)]
        self.snap_sweep = pd.DataFrame(rows)

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
            b = self.gpd.read_file(os.path.join(W11B, "run", "terrain",
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
        # re-measured.  5 m is literally "meets the trunk"; anything larger buys the
        # connection with a spur, which is a legitimate pipe and an engineer's decision.
        rows = []
        for t in (5.0, 15.0, 25.0, 50.0, 100.0):
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

        rows = []
        for j in sorted(set(int(x) for x in out if x >= 0)):
            m = out == j
            arcs = np.array([k for k, e in enumerate(tr.arc)
                             if m[self.u[int(e)]] or m[self.v[int(e)]]])
            km = float(self.L[tr.arc[arcs]].sum() / 1000.0) if arcs.size else 0.0
            q = float(self.Q[tr.arc[arcs]].sum()) if arcs.size else 0.0
            d = deficit[m]
            d = d[np.isfinite(d)]
            df = deficit_floor[m]
            df = df[np.isfinite(df)]
            rows.append(dict(
                SUBNET="", OUTFALL=self.node_ids[j], N_NODES=int(m.sum()), KM=km,
                Q_M3D=q, X=float(self.NX[j]), Y=float(self.NY[j]), Z=float(self.NZ[j]),
                D_MAIN_M=float(self.d_main[j]),
                PATH_MAX_M=float(np.nanmax(plen[m])) if m.any() else 0.0,
                # the LEAST fall any node in this sub-network has to its outfall.  Negative
                # means that node sits BELOW the point where its branch meets the trunk, so
                # the flow has to climb before it has bought a single millimetre of gradient.
                FALL_MIN_M=float(np.nanmin(pfall[m])) if m.any() else 0.0,
                N_BELOW=int(np.nansum(pfall[m] < -ADVERSE_MIN_M)),
                DEF_MAX_M=float(d.max()) if d.size else 0.0,
                DEF_FLOOR_M=float(df.max()) if df.size else 0.0,
                N_OVER_BUDGET=int((deficit[m] > DEPTH_BUDGET_M).sum())))
        sn = pd.DataFrame(rows).sort_values("KM", ascending=False).reset_index(drop=True)
        sn["SUBNET"] = [f"S{i+1:03d}" for i in range(len(sn))]
        sn["GRAVITY"] = np.where(sn.DEF_MAX_M <= DEPTH_BUDGET_M, "gravity",
                                 np.where(sn.DEF_FLOOR_M <= DEPTH_BUDGET_M,
                                          "gravity if the big pipes are laid flat",
                                          "NOT on gravity inside the cover cap"))
        self.subnet_of = {}
        for k, row in sn.iterrows():
            j = self.nid[row.OUTFALL]
            for a in np.nonzero(out == j)[0]:
                self.subnet_of[int(a)] = row.SUBNET

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
        self.presplit_ridges()
        self.find_roots()
        self._arc_arrays()
        self._detour()

        cmp_df = self.compare()
        sw = self.sweeps()
        self.published_snap = sw["sweep_main_snap"]

        _log("solving the shipped tree")
        tr = self.solve_with_bends()
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
                             TAU_FLAG=TAU_FLAG))
            geoms.append(r.geometry)
        return gpd.GeoDataFrame(recs, geometry=geoms, crs=f"EPSG:{CRS_EPSG}")

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
        recs = []
        for a in range(self.NV):
            p = tr.parent.get(a, None)
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
            ("criteria", CR.CRITERIA_VERSION, "", "w11b/criteria.py"),
            ("run_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "", ""),
            ("corridors_sha1", _sha1(ROADS_GPKG), "", ROADS_GPKG),
            ("main_pipe_sha1", _sha1(os.path.splitext(MAIN_PIPE)[0] + ".shp"), "", MAIN_PIPE),
            ("terrain_grid", GRID, "", "w11b/terrain.py, 5 m working grid"),
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
             "criteria.BENCHMARKS - the defect W11b exists to fix"),
            # --- project choices
            ("LAMBDA_SLOPE", LAMBDA_SLOPE, "", "PROJECT, swept: sweep_lambda_slope"),
            ("SLOPE_CAP", SLOPE_CAP, "", "PROJECT"),
            ("LAMBDA_DETOUR", LAMBDA_DETOUR, "", "PROJECT, forced by measurement, swept"),
            ("LAMBDA_BEND", LAMBDA_BEND, "", "PROJECT"),
            ("BEND_EQUIV_M", BEND_EQUIV_M, "m", "PROJECT"),
            ("BEND_PASSES", BEND_PASSES, "", "PROJECT"),
            ("JOIN_COST_M", JOIN_COST_M, "m", "PROJECT, swept: sweep_join_cost"),
            ("MAIN_SNAP_M", MAIN_SNAP_M, "m", "PROJECT, swept: sweep_main_snap"),
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

    def _write(self, arcs, nodes, sn, nb, cmp_df, sw, man):
        os.makedirs(RUN, exist_ok=True)
        os.makedirs(os.path.dirname(OUT_GPKG), exist_ok=True)
        if os.path.exists(OUT_GPKG):
            os.remove(OUT_GPKG)
        _log(f"writing {OUT_GPKG}")
        arcs.to_file(OUT_GPKG, layer="arcs", driver="GPKG")
        nodes.to_file(OUT_GPKG, layer="nodes", driver="GPKG")
        tabs = dict(subnets=sn, neighbours=nb, compare=cmp_df, manifest=man,
                    bend_passes=self.bend_hist, ridge_splits=self.split_rows, **sw)
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
            from w11b import present as P
        except Exception as exc:                                   # pragma: no cover
            self.notes.append(f"KMZ skipped: {exc}")
            return
        d = arcs[arcs.ROLE.isin(["tree", "head", "split_head"])].copy()
        for view, tag in (("ground_fall", "ground_fall"), ("subnet", "subnets")):
            try:
                out = os.path.join(W11B, "shp", f"W11b_orient_{tag}.kmz")
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
        A("# W11b stage 2 - orientation: what the tree actually achieved\n")
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

    out = dict(ok=not fails, fails=fails, uphill_pct=got, published_km=km,
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
    o.measure(); o.presplit_ridges(); o.find_roots(); o._arc_arrays(); o._detour()
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
