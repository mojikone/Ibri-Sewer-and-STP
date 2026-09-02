"""W11a stage 4 - THE HIERARCHY. Tier every pipe by the RULES, never by capping joins.

WHY THIS STAGE EXISTS, IN ONE SENTENCE. W7 had no sub-main tier at all, so thirty things
touched the trunk main; W8 got roughly the right shape by SWEEPING a cap on trunk joins until
the pumping-station count came out low, and its own closing note admits the cap was a proxy;
W10 then shipped 1,883 km of pipe with no TIER field whatsoever. A network without a
hierarchy is not a network - it is a pile of pipe that happens to drain. This stage generates
the hierarchy from the rules in `_BRAIN/08_DESIGN_PHILOSOPHY.md` sec 4, which were measured off
NAMA's own 101 km as-built in `W10/docs/research/HIERARCHY_RULES.md`, and it reports every
generated shape against the as-built band it came from.

THE FOUR TIERS, AND WHAT GENERATES EACH
---------------------------------------
The governing vocabulary is philosophy sec 4: *rider, lateral, main, sub main, trunk main*.
This stage lays the four NETWORK tiers; the rider is a property-connection tier and belongs
to the connections layer, not here.

  trunk main  An INPUT, not a result. Philosophy sec 2 puts the trunk at stage 3, end to end,
              at main diameter, BEFORE anything drains to it - "a trunk that emerges from
              accumulated flow is not a trunk". Read from `SHP/Main Pipe/Main Pipe.shp` (the
              user's own drawing) or from stage 3 when it exists, and LOCKED.

  sub main    A collector route DEFINED BY ITS OUTLET (philosophy sec 4, HIERARCHY_RULES R4).
              Not by a load threshold: 4 of the 10 as-built sub mains start with ZERO
              properties on them, and the median load at a sub-main head is 20 properties -
              there is no head-load rule to find. What is consistent is the outlet, so the
              generator is a MAIN-STEM DECOMPOSITION: from each point where the network meets
              the trunk, walk upstream always into the child carrying the largest contributing
              length, and keep walking while that child still gathers a catchment worth a
              collector. Side branches that themselves carry a catchment that size spawn their
              own sub main. That is R4 stated as an algorithm.

  main        The tier a chain of laterals drains into. Philosophy sec 4: "At most 3 laterals
              and 750 m of flow path before A MAIN." Read literally against the governing
              vocabulary, that sentence names `main`, not `sub main` - and it is the only
              generative rule the philosophy gives for this tier. It is also why the stated
              target shares (lateral 66 %, sub main 18 %, trunk 5 %) sum to 89 and not 100:
              the residual is the main tier. Stated as an inference, not as a measurement -
              NAMA's own tokens carry no M label, so there is no as-built band to check it
              against, and its size is reported as a DIAGNOSTIC of the tree rather than as a
              target hit.

  lateral     One unbranched street run - the residue. Median ~130 m, cap 920 m (sec 4;
              as-built p50 132 m, p95 500 m, max 916 m).

WHAT THIS STAGE REFUSES TO DO
-----------------------------
It does not cap trunk joins. W8's cap was tuned on pumping-station count and reproduced the
right shape for the wrong reason (HIERARCHY_RULES R10). Trunk joins here are a REPORTED
number, checked against the as-built one-per-4.6-km-of-network, and nothing in the generator
looks at them.

It does not size anything, level anything or place a chamber. Philosophy sec 2 puts chambers
at stage 5 and levels at stage 6, and sec 7 is explicit that "no solver chooses a layout".
The output is a tiered flow tree with identity on every node and every edge.

THE W10 FAILURES THIS PREVENTS
------------------------------
  no TIER on any pipe            every edge carries TIER and TIER_BY - what rule set it
  7,919 disconnected pieces      geometry is built from node coordinates by contract.Network,
                                 so an edge physically cannot stop short of its own chamber;
                                 Network.assert_round_trip re-reads what was WRITTEN and
                                 proves it is still the graph
  no US_NODE / DS_NODE           written from the graph, never re-derived by a tolerance
  loops                          contract.Network.add_edge refuses a second outgoing edge, so
                                 H15 holds by construction rather than by audit
  silent drops                   every corridor metre that does not become a tiered edge is
                                 named in a Funnel with its count and its reason
  a stage that quietly no-ops    Manifest.stage() raises if this writes nothing without saying
                                 why (invariant 10 - W10's RoadTreatment ran with units=None)

WHERE THE NUMBERS COME FROM. Nothing here is invented. Each constant carries its source in
the RULES block below: philosophy sec 4 where the philosophy states it, HIERARCHY_RULES R-number
where it is a measurement off the as-built, `sewnet.criteria` where it is an existing project
constant. Two are geometric tolerances rather than design values and say so.

UPSTREAM. Stages 1 (scope), 2 (corridors) and 3 (trunk) are not written yet. This module
looks for their published layers first and uses them when they exist. When they do not it
runs in FALLBACK mode on the layers the build brief names for reuse, marks the whole output
CONFIDENCE = provisional, and prints exactly what it is waiting for - it does not pretend the
corridor exclusions have been applied when stage 2 has not run.
"""
from __future__ import annotations

import collections
import heapq
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py
W11A = os.path.dirname(_HERE)                               # .../W11a
REPO = os.path.dirname(W11A)                                # .../Hydraulic/Claude
BASE = os.path.dirname(os.path.dirname(REPO))               # .../2621 Ibri Sewer STP
for p in (_HERE, os.path.join(REPO, "W8", "py")):
    if p not in sys.path:
        sys.path.insert(0, p)

import geopandas as gpd                                      # noqa: E402
import networkx as nx                                        # noqa: E402
import rasterio                                              # noqa: E402
from shapely.ops import unary_union                          # noqa: E402

from w11a import contract                                    # noqa: E402  the shared contract
# W8's own cost weight for a gravity-friendly spanning tree. IMPORTED, not restated: the
# build brief says reuse, and re-typing 300.0 here would make a second definition of a number
# that already exists. Both are documented in W8 as METHOD CHOICES, not guideline values.
from sewnet.stages.tree import CLIMB_PENALTY                 # noqa: E402

STAGE = "s4_hierarchy"


# ======================================================================================
# RULES - every number, with the line it came from. No value below is invented.
# ======================================================================================

# --- philosophy sec 4, stated verbatim in the file ------------------------------------
LATERAL_CAP_M = 920.0        # "A lateral is one unbranched street run (median ~130 m, cap
                             # 920 m)". As-built max 916 m (HIERARCHY_RULES R2).
CHAIN_MAX_RUNS = 3           # "At most 3 laterals ... before a main". As-built p50 2, max 5
                             # on the labelled packages (R12).
CHAIN_MAX_M = 750.0          # "... and 750 m of flow path before a main". As-built flow path
                             # to the first main: p50 258 m, p95 722 m, max 1,153 m (R12).
SM_CATCH_MIN_M = 4_000.0     # "one per 4-10 km of network" - the LOWER end. A catchment
                             # smaller than this gets no sub-main tier at all, which is
                             # exactly what package 5A-3 does: 3.46 km of sewer, zero sub
                             # mains, its 20 laterals straight onto the trunk (R5, R6).
SM_CATCH_MAX_M = 10_000.0    # ... and the UPPER end. A collector route that has gathered
                             # this much hands over and the next one starts, which is what
                             # keeps the count inside the band instead of producing one
                             # 90 km stem.
FINGER_M = 60.0              # "No fingers - a dead-end reach under ~60 m serving nothing is
                             # pruned or absorbed. Ours, on cost grounds; no adoption
                             # standard requires it."
WADI_CLASS_MIN = 4           # Hazard_T50y classes 4/5/6 ARE wadi ground. Not our number:
                             # `audit.r4` floors the sampled class at 4 and this stage must
                             # test H1 the way the auditor does, or it is measuring a
                             # different constraint from the one it claims to have met.

# --- the as-built bands every generated shape is REPORTED against (HIERARCHY_RULES) ----
# These steer nothing. They exist so a generated distribution can be compared with the one
# real engineer's answer available for this town, per philosophy P10: calibration reference,
# not template.
ASBUILT = dict(
    run_len_m=(132, 500, 916),            # R2  lateral zone length p50 / p95 / max
    chain_runs=(2, 3, 5),                 # R12 lateral zones crossed before a main
    chain_path_m=(258, 722, 1153),        # R12 flow path to the first main p50 / p95 / max
    sm_route_m=(910, 231, 1805),          # R4  sub-main route length p50 / min / max
    sm_catch_m=(4159, 1237, 15994),       # R4  contributing sewer at a sub-main outlet
    sm_share_pct=(21.0, 11.3, 35.2),      # R4  own length as a share of its catchment
    sm_per_km=(4.0, 10.0),                # R5  one sub main per 4-10 km of package sewer
    trunk_joins_per_km_network=1 / 4.6,   # R10 22 joins over 101 km of network
    trunk_joins_per_km_trunk=22 / 10.18,  # R10 ... or one per 460 m of trunk
    tier_share_pct=dict(lateral=66.0, sub_main=18.0, trunk_main=5.0),   # philosophy sec 4
)

# --- project constants, reused not restated -------------------------------------------
NODE_MERGE_M = contract.NODE_MERGE_M      # 3.0 m = criteria.MH_SNAP_M, "closer than the
                                          # clearance => ONE structure, merge"
PLOT_FRONT_M = 60.0                       # config_w10_reference.PLOT_SERVED_M - the frontage
                                          # distance the whole project has used for "does this
                                          # corridor serve that plot"
STP_EXISTING = (444422.8, 2563337.9)      # user-confirmed 2026-09-01, ground 328.7 m

# --- geometric tolerances. NOT design values. -----------------------------------------
TRUNK_ON_M = 0.5             # W10's NODE_SNAP_M. Kept only as the historical record of what
                             # the mask used to be - NO test reads it any more; the report
                             # quotes it to say what the superseded rule was. On the adopted
                             # path it asked a midpoint question of an UN-noded corridor set
                             # and turned a 4-piece trunk into 74 - see `weld_trunk` and
                             # OPEN-S4-1. On the fallback path the same probe over-selected,
                             # flagging 128.5 km of "trunk" against an 85.5 km alignment,
                             # because after planar noding a segment is short enough for any
                             # parallel corridor to sit inside the tolerance. Both now use
                             # containment in a TRUNK_WELD_M buffer instead.
TRUNK_WELD_M = 0.05          # the drawing tolerance at which stage 3's alignment and a stage
                             # 2 corridor are THE SAME LINE. 50 mm is the coordinate agreement
                             # of the two layers, not a design distance: nothing is served or
                             # not served by it, and nothing is moved by it.
MIN_SEG_M = 1e-6             # a zero-length artefact of the noding, not a pipe.

# --- input paths ----------------------------------------------------------------------
P_GPKG_W11A = os.path.join(W11A, "shp", "W11a.gpkg")                     # stages 1-3 publish here
P_CORR_FALL = os.path.join(REPO, "W10", "shp", "W10_corridor_quality.shp")
P_TRUNK_FALL = os.path.join(BASE, "Hydraulic", "SHP", "Main Pipe", "Main Pipe.shp")
P_LOADS = os.path.join(REPO, "W10", "shp", "W10_plot_loads.gpkg")
P_TERRAIN = os.path.join(BASE, "Data", "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt")
P_HAZARD = os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif")

# --- output paths ---------------------------------------------------------------------
OUT_GPKG = os.path.join(W11A, "shp", "W11a_s4.gpkg")
P_GPKG_TRUNK = os.path.join(W11A, "shp", "W11a_trunk.gpkg")   # stage 3's own
OUT_RUN = os.path.join(W11A, "run")


def _say(msg=""):
    print(msg, flush=True)


# ======================================================================================
# 1. INPUTS - upstream first, named fallbacks second, and never a silent substitution
# ======================================================================================

def _layers(path):
    if not os.path.exists(path):
        return []
    try:
        import fiona
        return list(fiona.listlayers(path))
    except Exception as e:
        # The file EXISTS and could not be opened. Returning [] silently would make the
        # stage announce "stage 2 has not published" and drop into FALLBACK mode - the
        # opposite of the truth, and a substitution nobody would see. Say it out loud.
        _say(f"  !! {path} exists but its layers could not be listed: {e}")
        _say("     Treating it as ABSENT. If stage 2 did publish, this is a corrupt or "
             "locked GeoPackage, not a missing upstream stage.")
        return []


def load_corridors(rec):
    """Stage 2's `corridors` layer if it exists; otherwise the reuse layer, declared.

    Stage 2 is where the wadi and dual-carriageway exclusions are applied (philosophy sec 2:
    "exclusions apply HERE, not in the router"). When it has not run, this stage must not
    quietly behave as though it had: the fallback carries the parent corridor's defect flags
    through onto every child segment as DUAL_WARN / WADI_WARN, and the whole output is graded
    provisional.
    """
    if "corridors" in _layers(P_GPKG_W11A):
        g = gpd.read_file(P_GPKG_W11A, layer="corridors")
        contract.validate(g, "corridors", stage=STAGE, strict=False)
        rec.read("corridors (stage 2)", P_GPKG_W11A, len(g))
        return g, True
    if not os.path.exists(P_CORR_FALL):
        return None, False
    g = gpd.read_file(P_CORR_FALL)
    rec.read("corridor_quality (FALLBACK)", P_CORR_FALL, len(g))
    return g, False


def load_trunk(corr, rec):
    """The trunk, in order of preference. It is an INPUT at every level and never re-derived
    here - CLAUDE.md: "the trunk is an INPUT now - the user's drawing, not derived".

      1. stage 3's published trunk reaches
      2. the corridors stage 2 already tagged SRC = 'main_pipe' - the SAME lines, but noded
         into the corridor network and with the exclusions applied. Preferred over the raw
         drawing because adding the drawing on top would lay a second copy of the trunk
         alongside the one already in the corridor set
      3. the user's Main Pipe drawing
    """
    # Stage 3 publishes to its OWN GeoPackage (W11a_trunk.gpkg) so that stage 4 cannot
    # overwrite an audited design. Looking for it in W11a.gpkg found nothing and fell
    # through to the corridor copy - which is how a trunk that nodes into 2 pieces reached
    # this stage in 58. Look where stage 3 actually writes, then where stage 4 later does.
    for _src in (P_GPKG_TRUNK, P_GPKG_W11A):
        if os.path.exists(_src) and "reaches" in _layers(_src):
            g = gpd.read_file(_src, layer="reaches")
            if "TIER" not in g.columns:
                continue
            g = g[g.TIER.astype(str).str.strip() == "trunk main"]
            if len(g):
                rec.read("trunk (stage 3)", _src, len(g))
                return g, True, "stage3"
    if corr is not None and "SRC" in corr.columns:
        g = corr[corr.SRC.astype(str).str.strip() == "main_pipe"]
        if len(g):
            rec.read("trunk (stage 2 corridors, SRC=main_pipe)", P_GPKG_W11A, len(g))
            # The trunk is the one alignment where fragmentation is fatal rather than
            # untidy, so it is measured against the drawing it came from before it is used.
            if os.path.exists(P_TRUNK_FALL):
                raw = gpd.read_file(P_TRUNK_FALL)
                if raw.crs is None:
                    raw = raw.set_crs(contract.CRS_EPSG)
                lost = raw.geometry.length.sum() / 1000 - g.LEN_M.sum() / 1000
                rec.metric("trunk_km_lost_vs_drawing", round(lost, 2))
                if lost > 0.5:
                    _say(f"  NOTE the stage 2 trunk is {g.LEN_M.sum() / 1000:.2f} km against "
                         f"{raw.geometry.length.sum() / 1000:.2f} km in the user's drawing - "
                         f"{lost:.2f} km short.")
            return g, True, "in_corridors"
    if not os.path.exists(P_TRUNK_FALL):
        return None, False, ""
    g = gpd.read_file(P_TRUNK_FALL)
    if g.crs is None:
        g = g.set_crs(contract.CRS_EPSG)
    rec.read("Main Pipe (FALLBACK, an INPUT either way)", P_TRUNK_FALL, len(g))
    return g, False, "drawing"


def load_servicing(rec):
    """Stage 1's served-set decision, one row per settlement with the SYSTEM that serves it.

    Philosophy sec 8a: every plot is served and the question is by WHICH system - central,
    satellite works, or on-site. When stage 1 has published, SYSTEM on a reach comes from that
    decision rather than from a guess about this stage's own graph connectivity.
    """
    if "servicing" not in _layers(P_GPKG_W11A):
        return None
    g = gpd.read_file(P_GPKG_W11A, layer="servicing")
    rec.read("servicing (stage 1 scope decision)", P_GPKG_W11A, len(g))
    return g


def load_plots(rec):
    """Load-bearing plots, for the finger rule and for the frontage diagnostics.

    NOT the load allocation - that is fixed doctrine in PROJECT-STATE sec 2 and belongs to the
    loads stage. What this reads is "does anything front this corridor at all", which is the
    P7 question: 117.3 km of W10 had no load-bearing plot within 60 m and carried under
    1 m3/d, so it neither collected nor conveyed.
    """
    if not os.path.exists(P_LOADS):
        return None
    g = gpd.read_file(P_LOADS, layer="plot_loads")
    g = g[pd.to_numeric(g["Q_AVG_M3D"], errors="coerce").fillna(0) > 0]
    rec.read("plot_loads (load-bearing only)", P_LOADS, len(g))
    return g[["geometry", "N_PROP", "Q_AVG_M3D"]]


# ======================================================================================
# 2. THE CORRIDOR GRAPH - noded, merged at the chamber clearance
# ======================================================================================

def adopt_graph(corr, corr_nodes, trunk_where, rec):
    """Take stage 2's topology as published. THE PREFERRED PATH.

    Contract P3, verbatim: "every layer carries explicit US_NODE / DS_NODE identifiers written
    FROM the graph. Connectivity is an attribute, never something to be re-derived by a
    tolerance." Stage 2 published both, so re-noding its corridors with a union and a 3 m
    merge would be exactly the re-derivation the contract forbids - and would also mint a
    second set of node identities for structures that already have one, which is how two
    layers end up describing different networks.

    Node coordinates come from `corridor_nodes` where stage 2 published it, so the geometry
    this stage rebuilds lands on stage 2's own nodes rather than on the line's end vertex.
    The offset between the two is measured and reported rather than assumed to be zero.
    """
    idx = contract.NodeIndex(NODE_MERGE_M)
    if corr_nodes is not None and {"NODE_UID", "X", "Y"} <= set(corr_nodes.columns):
        for r in corr_nodes.itertuples():
            uid = str(r.NODE_UID)
            idx.nodes[uid] = contract.Node(uid=uid, x=float(r.X), y=float(r.Y))
            idx._cells.setdefault(idx._cell(float(r.X), float(r.Y)), []).append(uid)
    else:
        for r in corr.itertuples():
            c = list(r.geometry.coords)
            for uid, pt in ((str(r.US_NODE), c[0]), (str(r.DS_NODE), c[-1])):
                if uid not in idx.nodes:
                    idx.nodes[uid] = contract.Node(uid=uid, x=float(pt[0]), y=float(pt[1]))
                    idx._cells.setdefault(idx._cell(pt[0], pt[1]), []).append(uid)
    # The next uid this index mints must be above every uid already in it, and the COUNT is
    # not that number. Stage 2 published 23,916 corridor nodes whose highest uid is N0000023935
    # - 19 of its own ids sit above its own count - so seeding the counter with the count
    # would mint N0000023917 straight on top of a live corridor node, silently move that
    # chamber and take every reach referencing it with it. It never bit before because
    # nothing minted a node after this point; `weld_trunk` does.
    hi = 0
    for uid in idx.nodes:
        tail = uid[1:] if uid[:1].isalpha() else uid
        if tail.isdigit():
            hi = max(hi, int(tail))
    idx._n = max(len(idx.nodes), hi)

    fun = rec.funnel("corridor segments -> tiered edges", len(corr))
    G = nx.Graph()
    n_bad, n_self, n_par, par_m, off = 0, 0, 0, 0.0, 0.0
    for r in corr.itertuples():
        a, b = str(r.US_NODE), str(r.DS_NODE)
        g = r.geometry
        if a not in idx.nodes or b not in idx.nodes or g is None or g.is_empty:
            n_bad += 1
            continue
        if g.geom_type.startswith("Multi"):
            n_bad += 1                      # a multipart corridor is not one reach
            continue
        if a == b:
            n_self += 1
            continue
        c = list(g.coords)
        na, nb = idx.nodes[a], idx.nodes[b]
        off = max(off, min(np.hypot(c[0][0] - na.x, c[0][1] - na.y),
                           np.hypot(c[-1][0] - na.x, c[-1][1] - na.y)))
        is_tr = bool(trunk_where(r, g))
        if G.has_edge(a, b):
            if G[a][b]["trunk"] or (not is_tr and G[a][b]["length"] <= g.length):
                n_par += 1
                par_m += g.length
                continue
            n_par += 1
            par_m += G[a][b]["length"]
        G.add_edge(a, b, length=float(g.length), geom=g, trunk=is_tr,
                   meta=dict(SRC=str(getattr(r, "SRC", "draft") or "draft"),
                             CORR_ID=str(getattr(r, "CORR_ID", "") or ""), QFLAG="",
                             CONF=str(getattr(r, "CONFIDENCE", "") or ""),
                             DUAL_WARN=int(float(getattr(r, "ON_DUAL_M", 0) or 0) > 0),
                             WADI_WARN=int(float(getattr(r, "ON_WADI_M", 0) or 0) > 0)))
    fun.drop("corridor with an unresolvable node reference or multipart geometry", n=n_bad)
    fun.drop("corridor whose two ends are the same node", n=n_self)
    fun.drop(f"parallel corridor between the same two nodes ({par_m / 1000:.2f} km)", n=n_par)
    rec.metric("node_offset_max_m", round(off, 4))
    rec.metric("graph_nodes", G.number_of_nodes())
    # STAGE 2's OWN piece count, recorded here where the graph is still only stage 2's.
    # `corridor_components` is measured in build_tree, AFTER the weld, and the two are
    # different numbers: printing the post-weld figure under the words "arrives from stage 2"
    # is the sort of relabelling P2 exists to stop.
    rec.metric("corridor_components_stage2", nx.number_connected_components(G))
    _say(f"  adopted stage 2 topology: {G.number_of_nodes():,} nodes, "
         f"{G.number_of_edges():,} edges, "
         f"{nx.number_connected_components(G):,} pieces; worst line-end to node offset "
         f"{off:.3f} m")
    # Nodes stage 2 published that no surviving corridor uses. The SPATIAL index has to be
    # purged with them: NodeIndex.find walks `_cells` and dereferences every uid it holds, so
    # a uid popped from `nodes` and left in a cell raises KeyError the moment anything asks
    # this index for a node again - which is exactly what `weld_trunk` does next.
    dead = {u for u in idx.nodes if u not in G}
    for u in dead:
        idx.nodes.pop(u, None)
    if dead:
        for cell, uids in list(idx._cells.items()):
            keep = [u for u in uids if u not in dead]
            if keep:
                idx._cells[cell] = keep
            else:
                idx._cells.pop(cell, None)
    # This funnel is CLOSED here, on the corridors alone. The trunk is a SECOND input welded
    # in next, and a funnel whose n0 is `len(corr)` cannot account for edges that were never
    # corridors - it would have to "drop" a negative number. The tiering funnel that follows
    # therefore starts at the GRAPH, after the weld. Two funnels, each closing on its own
    # arithmetic, is the only way both additions and losses stay visible (P2).
    fun.close(G.number_of_edges())
    return G, idx


def weld_trunk(G, idx, trunk, rec):
    """Stage 3's trunk, WELDED INTO stage 2's corridor graph as edges of its own.

    THE DEFECT THIS FIXES (OPEN-S4-1). Until now the trunk was never in this graph. It was a
    TRUNK_ON_M proximity MASK over stage 2's corridors: a corridor whose midpoint fell within
    0.5 m of the alignment was called `trunk`, so the trunk arrived in as many pieces as
    stage 2's COPY of it - 74, against the 4 stage 3 designed and the 3 in the user's
    drawing. Measured 2026-09-02: only 3.2 % of stage 3's 758 chambers land within 0.5 m of a
    corridor node and 6.9 % within the 3 m merge radius, median offset 42.4 m, max 379 m - so
    there is nothing to snap to either, and a tolerance big enough to catch the median would
    move a client INPUT by tens of metres. The 74 pieces cannot be rejoined through the
    corridor graph at all: 35 of them are mutually unreachable.

    THE METHOD. The trunk lines and ONLY the corridors they touch go into one planar union,
    exactly as `build_graph` already does for the fallback path - "noding it separately and
    snapping afterwards is how a trunk ends up 1.0 m from the network that is supposed to
    drain into it". A corridor is CUT at the trunk and the cut becomes a node in both.
    Nothing else is re-derived: the corridors the trunk never touches keep the US_NODE /
    DS_NODE stage 2 wrote, so contract P3 still holds for the overwhelming majority of the
    layer, and the share re-noded is published as `weld_corridors_renoded`.

    WHAT MOVES. The trunk's own vertices do not - a planar union splits lines, it does not
    move them. What can move is a CHAMBER, by up to the NODE_MERGE_M radius stage 2 itself
    applies, where a trunk chamber and a corridor node are closer than the chamber clearance
    and philosophy sec 4 therefore makes them ONE structure. The worst move is asserted below
    that radius and published as `weld_chamber_move_max_m`; past it this raises, because the
    alignment is a client INPUT (CLAUDE.md) and is never re-routed. NO PIPE MOVES.
    """
    from shapely.strtree import STRtree

    t_lines, t_attr = [], []
    for r in trunk.itertuples():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        for p in (g.geoms if g.geom_type.startswith("Multi") else [g]):
            t_lines.append(p)
            t_attr.append(r)
    if not t_lines:
        rec.note("stage 3 published no trunk geometry - nothing welded")
        return
    t_km_in = sum(g.length for g in t_lines) / 1000.0

    # 1. stage 3's chambers enter the node index FIRST, so a corridor split point lands on a
    #    DESIGNED chamber rather than the reverse.
    n0_nodes, reuse_max = len(idx.nodes), 0.0
    for g in t_lines:
        c = list(g.coords)
        for x, y in (c[0], c[-1]):
            uid = idx.get_or_create(float(x), float(y))
            nd = idx.nodes[uid]
            reuse_max = max(reuse_max, float(np.hypot(nd.x - x, nd.y - y)))
    if reuse_max > NODE_MERGE_M:
        raise contract.ContractError(
            f"a trunk chamber moved {reuse_max:.2f} m onto a corridor node, past the "
            f"{NODE_MERGE_M:.1f} m merge radius. The trunk is a client INPUT.")

    # 2. the corridors the trunk actually touches - and only those
    ekeys = list(G.edges())
    egeom = [G[a][b]["geom"] for a, b in ekeys]
    emeta = [G[a][b]["meta"] for a, b in ekeys]
    live = [i for i, g in enumerate(egeom) if g is not None and not g.is_empty]
    tree = STRtree([egeom[i] for i in live])
    touched = set()
    for t in t_lines:
        for j in tree.query(t.buffer(TRUNK_WELD_M)):
            i = live[int(j)]
            if egeom[i].distance(t) <= TRUNK_WELD_M:
                touched.add(i)
    order = sorted(touched)
    plines = [egeom[i] for i in order]
    pmeta = [emeta[i] for i in order]
    p_km = sum(g.length for g in plines) / 1000.0
    for i in order:
        a, b = ekeys[i]
        if G.has_edge(a, b):
            G.remove_edge(a, b)

    # 3. ONE planar union - the trunk and its neighbours noded together, never separately
    noded = unary_union(plines + t_lines)
    segs = [s for s in (noded.geoms if noded.geom_type.startswith("Multi") else [noded])
            if s.length > MIN_SEG_M]
    ptree = STRtree(plines) if plines else None
    ttree = STRtree(t_lines)
    tbuf = unary_union(t_lines).buffer(TRUNK_WELD_M)
    mids = [s.interpolate(0.5, normalized=True) for s in segs]
    pnear = np.asarray(ptree.nearest(mids)).reshape(-1) if ptree else None
    tnear = np.asarray(ttree.nearest(mids)).reshape(-1)

    fun = rec.funnel("trunk weld: corridor + trunk lines -> welded edges", len(segs))
    n_self, self_m, n_par, par_m, move = 0, 0.0, 0, 0.0, 0.0
    for i, s in enumerate(segs):
        c = list(s.coords)
        u = idx.get_or_create(c[0][0], c[0][1])
        v = idx.get_or_create(c[-1][0], c[-1][1])
        nu, nv = idx.nodes[u], idx.nodes[v]
        move = max(move, float(np.hypot(c[0][0] - nu.x, c[0][1] - nu.y)),
                   float(np.hypot(c[-1][0] - nv.x, c[-1][1] - nv.y)))
        if u == v:
            n_self += 1
            self_m += s.length
            continue
        # CONTAINMENT, not a midpoint probe. A midpoint probe on a noded set flagged 128 km
        # of "trunk" against an 85.5 km alignment, because after noding a segment is short
        # enough for any parallel corridor to sit inside the tolerance.
        is_tr = bool(tbuf.covers(s))
        if is_tr:
            t = t_attr[int(tnear[i])]
            # H1 flags come from STAGE 3's own exposure figures, not zeroed. Project rule 7 is
            # explicit that no pipe of any kind runs along a dual carriageway, trunk included,
            # and stage 3 measures ON_DUAL_M and ON_WADI_M on this alignment. Clearing them
            # here would hide the evidence on the reaches where a late H1 discovery is most
            # expensive.
            meta = dict(SRC="main_pipe", CORR_ID="", QFLAG="", CONF="drafted",
                        DUAL_WARN=int(float(getattr(t, "ON_DUAL_M", 0) or 0) > 0),
                        WADI_WARN=int(float(getattr(t, "ON_WADI_M", 0) or 0) > 0))
        else:
            meta = dict(pmeta[int(pnear[i])])       # the parent corridor's provenance, P6
        if G.has_edge(u, v):
            if G[u][v]["trunk"] or (not is_tr and G[u][v]["length"] <= s.length):
                n_par += 1
                par_m += s.length
                continue
            n_par += 1
            par_m += G[u][v]["length"]
        G.add_edge(u, v, length=float(s.length), geom=s, trunk=is_tr, meta=meta)
    fun.drop(f"welded segment whose two ends fall in one {NODE_MERGE_M:.0f} m chamber "
             f"({self_m / 1000:.3f} km)", n=n_self)
    fun.drop(f"parallel welded segment between the same two chambers "
             f"({par_m / 1000:.3f} km)", n=n_par)
    fun.close(len(segs) - n_self - n_par)

    # 4. THE SPINE IS A TREE. Stage 2 publishes its own copy of the alignment a few
    #    centimetres off stage 3's, so the weld leaves a shadow beside the trunk. It shows up
    #    as a cycle in the trunk subgraph - a spine cannot have one - and the longest edge of
    #    each cycle is the shadow.
    Gt = nx.Graph([(a, b, d) for a, b, d in G.edges(data=True) if d["trunk"]])
    n_shadow, shadow_m = 0, 0.0
    while True:
        try:
            cyc = nx.find_cycle(Gt)
        except nx.NetworkXNoCycle:
            break
        a, b = max(((e[0], e[1]) for e in cyc), key=lambda e: Gt[e[0]][e[1]]["length"])
        shadow_m += Gt[a][b]["length"]
        n_shadow += 1
        Gt.remove_edge(a, b)
        G.remove_edge(a, b)

    t_km_out = sum(d["length"] for *_, d in G.edges(data=True) if d["trunk"]) / 1000.0
    pieces = nx.number_connected_components(Gt) if len(Gt) else 0
    rec.metric("weld_corridors_renoded", len(order))
    rec.metric("weld_segments", len(segs))
    rec.metric("weld_new_nodes", len(idx.nodes) - n0_nodes)
    rec.metric("weld_chamber_move_max_m", round(max(move, reuse_max), 3))
    rec.metric("weld_shadow_km", round(shadow_m / 1000, 3))
    rec.metric("trunk_km_welded", round(t_km_out, 2))
    rec.metric("trunk_km_stage3", round(t_km_in, 2))
    _say(f"  welded stage 3's trunk in: {len(order):,} corridors ({p_km:.2f} km) re-noded "
         f"with {len(t_lines):,} trunk lines ({t_km_in:.2f} km) -> {len(segs):,} segments")
    _say(f"    {len(idx.nodes) - n0_nodes:,} new chambers, worst chamber move "
         f"{max(move, reuse_max):.3f} m (merge radius {NODE_MERGE_M:.1f} m); "
         f"{n_shadow} shadow edges, {shadow_m / 1000:.2f} km, removed so the spine is a tree")
    _say(f"    TRUNK now {t_km_out:.2f} km in {pieces} piece(s) against stage 3's "
         f"{t_km_in:.2f} km")
    if abs(t_km_out - t_km_in) > 0.01 * t_km_in:
        rec.note(f"the welded trunk is {t_km_out:.2f} km against stage 3's {t_km_in:.2f} km "
                 f"({100 * (t_km_out - t_km_in) / t_km_in:+.1f} %). Stage 2 publishes its own "
                 "copy of the alignment a few centimetres off stage 3's; the two are welded "
                 "as one spine and the excess is reported, not laundered.")


def build_graph(corr, trunk, rec):
    """FALLBACK: node the corridors ourselves, when the upstream layer has no topology.

    The trunk goes into the SAME union as the corridors so it is noded WITH them. Noding it
    separately and snapping afterwards is how a trunk ends up 1.0 m from the network that is
    supposed to drain into it - the W10 stitch defect in miniature.

    Nodes are minted by contract.NodeIndex at 3.0 m, so two corridors arriving at one street
    corner produce one chamber rather than two 0.4 m apart with a 0.4 m pipe between them.
    """
    corr_lines, corr_attr = [], []
    for r in corr.itertuples():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        parts = list(g.geoms) if g.geom_type.startswith("Multi") else [g]
        for p in parts:
            corr_lines.append(p)
            corr_attr.append(r)

    trunk_lines = []
    for g in trunk.geometry:
        if g is None or g.is_empty:
            continue
        trunk_lines += list(g.geoms) if g.geom_type.startswith("Multi") else [g]
    trunk_u = unary_union(trunk_lines)
    # PATCH 3, and the same rule `weld_trunk` uses: a noded segment IS the trunk when the
    # trunk CONTAINS it, not when its midpoint is near it. Measured on a planar-noded set,
    # `midpoint < TRUNK_ON_M` flags 128.5 km against an 85.5 km alignment and yields 11
    # pieces; containment flags 93.6 km and yields 4. Built ONCE, not per segment.
    trunk_buf = trunk_u.buffer(TRUNK_WELD_M)

    t0 = time.time()
    noded = unary_union(corr_lines + trunk_lines)
    segs = [s for s in (noded.geoms if noded.geom_type.startswith("Multi") else [noded])
            if s.length > MIN_SEG_M]
    _say(f"  noded {len(corr_lines):,} corridor + {len(trunk_lines):,} trunk lines "
         f"-> {len(segs):,} segments in {time.time() - t0:.1f} s")

    # provenance: each noded child inherits SRC/flags from the nearest parent corridor line.
    # P6 - "SRC and a CONFIDENCE grade travel on every pipe to the drawings and the schedules";
    # the union throws attributes away, so they are put back explicitly rather than lost.
    from shapely.strtree import STRtree
    tree = STRtree(corr_lines)
    mids = [s.interpolate(0.5, normalized=True) for s in segs]
    near = tree.nearest(mids)
    near = np.asarray(near).reshape(-1)

    fun = rec.funnel("corridor segments -> tiered edges", len(segs))
    idx = contract.NodeIndex(NODE_MERGE_M)
    G = nx.Graph()
    n_self, self_m, n_par, par_m = 0, 0.0, 0, 0.0
    seg_src, seg_meta = {}, {}
    for i, s in enumerate(segs):
        c = list(s.coords)
        a = idx.get_or_create(c[0][0], c[0][1])
        b = idx.get_or_create(c[-1][0], c[-1][1])
        is_tr = bool(trunk_buf.covers(s))
        if a == b:
            # Both endpoints fell inside one 3 m chamber. The structure absorbs it; nothing is
            # disconnected, because every neighbouring segment now shares that same node.
            n_self += 1
            self_m += s.length
            continue
        par = corr_attr[int(near[i])]
        meta = dict(
            SRC=str(getattr(par, "SRC", "draft") or "draft"),
            CORR_ID=str(getattr(par, "CORR_ID", "") or ""),
            QFLAG=str(getattr(par, "QFLAG", "") or ""),
            CONF="",
            DUAL_WARN=int(float(getattr(par, "ON_DUAL_M", 0) or 0) > 0),
            WADI_WARN=int(float(getattr(par, "WADI_M", getattr(par, "ON_WADI_M", 0)) or 0) > 0),
        )
        if is_tr:
            meta["SRC"] = "main_pipe"
            # SRC is the trunk's own; its H1 flags are NOT. Project rule 7 is explicit that
            # "no pipe of any kind runs along a dual carriageway, TRUNK INCLUDED", and H1
            # bars a wadi to every tier equally. Zeroing the flags here cleared the evidence
            # on exactly the reaches where a late H1 discovery is most expensive - and the
            # trunk corridors DO carry 158.8 m of dual-carriageway length, measured.
        if G.has_edge(a, b):
            # A parallel pair between the same two chambers. Keep the trunk if either is the
            # trunk - dropping a trunk edge in favour of a 3 m shortcut is how a spine breaks
            # into twenty pieces - otherwise keep the shorter.
            if G[a][b]["trunk"] or (not is_tr and G[a][b]["length"] <= s.length):
                n_par += 1
                par_m += s.length
                continue
            n_par += 1
            par_m += G[a][b]["length"]
        G.add_edge(a, b, length=s.length, geom=s, trunk=is_tr, meta=meta)
        seg_src[(a, b)] = meta["SRC"]
        seg_meta[(a, b)] = meta

    fun.drop(f"segment shorter than the {NODE_MERGE_M} m chamber clearance - both ends are "
             f"one structure ({self_m / 1000:.2f} km)", n=n_self)
    fun.drop(f"parallel segment between the same two chambers ({par_m / 1000:.2f} km)",
             n=n_par)
    rec.metric("graph_nodes", G.number_of_nodes())
    rec.metric("graph_km", round(sum(d["length"] for *_, d in G.edges(data=True)) / 1000, 1))
    # Closed here for the same reason `adopt_graph` closes its own: this funnel counts the
    # noding, and the tiering funnel that follows starts at the graph both paths produce.
    fun.close(G.number_of_edges())
    return G, idx, trunk_u


def wadi_recheck(reaches, nodes, rec):
    """H1 recomputed from the RAW hazard grid. Never inherited, never assumed.

    THE DEFECT THIS FIXES. WADI_WARN was carried through from the parent corridor's
    ON_WADI_M, stage 2 published ON_WADI_M = 0 everywhere, and this stage therefore reported
    "0 reaches inherit a corridor with wadi length" and treated H1 as satisfied. Sampling
    Hazard_T50y directly - the way `audit.r4` does, at the reach midpoint, class >= 4 - finds
    46 reaches on wadi ground, 0.301 km, 83.6 m of it TRUNK MAIN. An inherited flag is a
    claim about an upstream stage; it is not a measurement of our own geometry, and
    philosophy sec 8 requires every check to recompute "from the designed values and the raw
    terrain".

    H1 also bars a CHAMBER from a wadi, not only a pipe, and nothing in this stage measured
    that at all. Nodes are sampled here too so the number exists before stage 5 places
    structures on top of it.

    Nothing is removed. Re-routing is stage 2/3's, and dropping reaches here would break the
    funnel and hide the finding. What changes is that the flag now tells the truth.
    """
    if not os.path.exists(P_HAZARD):
        rec.note("Hazard_T50y grid missing - WADI_WARN is the INHERITED corridor flag only "
                 "and H1 has NOT been independently verified on this output")
        return reaches, nodes
    with rasterio.open(P_HAZARD) as src:
        mids = reaches.geometry.interpolate(0.5, normalized=True)
        vr = np.array([w[0] for w in src.sample(zip(mids.x, mids.y))], dtype=float)
        vn = np.array([w[0] for w in src.sample(zip(nodes.geometry.x, nodes.geometry.y))],
                      dtype=float)
    # Nodata is -9999, and it is NOT "no wadi" - it is "no answer". More than half of this
    # network sits outside the Lekhuwair grid's footprint, so "0 reaches on wadi ground" is
    # a statement about the tested part only. audit.r4 has exactly the same blind spot
    # (`np.isfinite(v) & (floor(v) >= 4)` scores nodata as a pass), which is why the untested
    # share is published here rather than left for someone to infer.
    cov_r = np.isfinite(vr) & (vr > -1000)
    cov_n = np.isfinite(vn) & (vn > -1000)
    on_r = cov_r & (np.floor(vr) >= WADI_CLASS_MIN)
    on_n = cov_n & (np.floor(vn) >= WADI_CLASS_MIN)
    inherited = reaches["WADI_WARN"].astype(int).values
    reaches["WADI_WARN"] = np.maximum(inherited, on_r.astype(int))
    reaches["WADI_HERE"] = on_r.astype(int)      # measured on OUR geometry, not inherited
    nodes["WADI_HERE"] = on_n.astype(int)

    # H1a: ACROSS is legal, ALONG is not, so one undifferentiated "on wadi ground" count is
    # not a finding - it lumps a designed crossing in with a pipe laid down a flood channel.
    # The classifier is the auditor's own (audit._r4_classify), not a copy: the stage that
    # measures and the check that judges must not be able to disagree.
    reaches["WADI_ALONG"] = 0
    reaches["WADI_XING"] = 0
    try:
        from w11a import audit as _audit
        _ctx = _audit.Ctx(pipes=reaches, hazard=P_HAZARD)
        _along, _xing_bad, _xing_ok, _ns, _nd, _ndr = _audit._r4_classify(_ctx)
        if _along:
            reaches.iloc[np.array(_along, dtype=int),
                         reaches.columns.get_loc("WADI_ALONG")] = 1
        _xa = _xing_bad + list(range(0))          # every crossing here is unscheduled yet
        if _xa:
            reaches.iloc[np.array(_xa, dtype=int),
                         reaches.columns.get_loc("WADI_XING")] = 1
        rec.metric("reaches_along_a_wadi", int(len(_along)))
        # `_r4_classify` returns three LISTS, not two lists and a count. `len(_xing_bad) +
        # _xing_ok` therefore raised TypeError, the except below caught it, and the run
        # recorded a note saying the along/across classification "did not run" when it had
        # run and had already written WADI_ALONG / WADI_XING. The crossing count went
        # unpublished and the report printed 0 crossings from `metrics.get(..., 0)`.
        rec.metric("reaches_crossing_a_wadi", int(len(_xing_bad) + len(_xing_ok)))
    except Exception as _e:                       # noqa: BLE001 - reported, never swallowed
        rec.note(f"H1a along/across classification did not run ({type(_e).__name__}: {_e}); "
                 "WADI_HERE is an undifferentiated contact count and OVERSTATES the defect, "
                 "because a legal crossing has its midpoint on the wadi by definition")
    km = float(reaches.LEN_M[on_r].sum()) / 1000
    rec.metric("reaches_on_wadi_measured", int(on_r.sum()))
    rec.metric("km_on_wadi_measured", round(km, 3))
    rec.metric("chambers_on_wadi_measured", int(on_n.sum()))
    rec.metric("reaches_on_wadi_inherited", int(inherited.sum()))
    km_untested = float(reaches.LEN_M[~cov_r].sum()) / 1000
    rec.metric("km_outside_hazard_grid_untestable", round(km_untested, 1))
    reaches["WADI_COV"] = cov_r.astype(int)      # 0 = H1 could not be tested here at all
    nodes["WADI_COV"] = cov_n.astype(int)
    _say(f"  H1 wadi recheck against the raw grid: {int(on_r.sum()):,} reaches "
         f"({km:.3f} km) and {int(on_n.sum()):,} chambers sit on class >= "
         f"{WADI_CLASS_MIN} ground, against {int(inherited.sum()):,} the inherited corridor "
         f"flag claimed. audit.R4 reads the grid, not the flag.")
    _say(f"  BUT {km_untested:,.1f} km ({100 * km_untested / max(1e-9, reaches.LEN_M.sum() / 1000):.0f} %) "
         f"lies outside the hazard grid's footprint and could NOT be tested. Nodata scores "
         f"as a pass in audit.R4 too, so this is an untested share, not a clean one.")
    return reaches, nodes


def sample_terrain(idx, rec):
    """Ground level at every node, from the 0.5 m VRT (project rule 6).

    Used ONLY to orient flow - which way is downhill - never to set a level. Levels are stage
    6 and nothing here may pre-empt them.
    """
    if not os.path.exists(P_TERRAIN):
        rec.note("terrain VRT missing - the tree is oriented on length alone, which will "
                 "route uphill wherever the shortest path does")
        return {u: float("nan") for u in idx.nodes}
    t0 = time.time()
    ds = rasterio.open(P_TERRAIN)
    uids = list(idx.nodes)
    pts = [(idx.nodes[u].x, idx.nodes[u].y) for u in uids]
    z = np.array([v[0] for v in ds.sample(pts)], dtype=float)
    z[z < -1000] = np.nan                       # VRT nodata is -9999
    _say(f"  sampled {len(uids):,} ground levels in {time.time() - t0:.1f} s "
         f"({int(np.isnan(z).sum()):,} outside coverage)")
    rec.read("terrain 0.5 m VRT", P_TERRAIN, len(uids))
    return dict(zip(uids, z))


# ======================================================================================
# 3. THE FLOW TREE - the trunk first, then everything drains to it
# ======================================================================================

def build_tree(G, idx, Z, rec):
    """A directed forest: parent[v] = the node v discharges into.

    TWO PASSES, in the order philosophy sec 2 requires - "Stage 3 before stage 6. A trunk that
    emerges from accumulated flow is not a trunk."

      pass 1  On the trunk edges ALONE, rooted at the works. This fixes the spine's direction
              from its own geometry, so no amount of cheap corridor can re-route it.
      pass 2  A multi-source Dijkstra seeded with EVERY trunk node at zero cost. Each corridor
              node therefore drains to its nearest trunk node, and the trunk's own orientation
              from pass 1 is untouched. Seeding at zero needs no weighting constant - the
              trunk is preferred because it is the destination, not because it was discounted.

    Cost of a search step u -> v is W8's: the corridor length plus CLIMB_PENALTY per metre the
    FLOW would have to climb (the search runs outward from the outfall, so a search step u->v
    is a flow step v->u and climbs when z_u > z_v).

    Components with no trunk in them get their own root at their lowest node. Those are not a
    defect to be hidden - they are the satellite / on-site question philosophy sec 8a leaves
    deliberately open, and they are counted and reported as such.
    """
    Gt = nx.Graph([(a, b, d) for a, b, d in G.edges(data=True) if d["trunk"]])
    parent, roots = {}, {}

    tcomps = sorted(nx.connected_components(Gt),
                    key=lambda c: sum(Gt[a][b]["length"] for a, b in Gt.subgraph(c).edges()),
                    reverse=True) if len(Gt) else []
    rec.metric("trunk_pieces", len(tcomps))
    if tcomps:
        tk = sorted((sum(Gt[a][b]["length"] for a, b in Gt.subgraph(c).edges()) / 1000
                     for c in tcomps), reverse=True)
        rec.metric("trunk_longest_piece_km", round(tk[0], 2))
        _say(f"  the trunk arrives in {len(tcomps)} disconnected pieces "
             f"(longest {tk[0]:.2f} km, then {', '.join(f'{x:.2f}' for x in tk[1:5])} ...); "
             f"each is rooted separately")
    for ci, c in enumerate(tcomps):
        sub = Gt.subgraph(c)
        if ci == 0:
            root = min(c, key=lambda n: (idx.nodes[n].x - STP_EXISTING[0]) ** 2
                       + (idx.nodes[n].y - STP_EXISTING[1]) ** 2)
        else:
            # A detached trunk leg. config_w10_reference records that the western leg is cut
            # off by topography and that its fate - used, pumped, or replaced by a satellite
            # works - is an options question. Root it at its own low point and flag it.
            root = min(c, key=lambda n: Z[n] if np.isfinite(Z[n]) else 1e9)
        _, paths = nx.single_source_dijkstra(sub, root, weight="length")
        for n, p in paths.items():
            if len(p) >= 2:
                parent[n] = p[-2]              # the node one step TOWARD the root
        roots[root] = "trunk_main" if ci == 0 else "trunk_detached"

    def dijkstra(sources):
        dist = {s: 0.0 for s in sources}
        pq = [(0.0, s) for s in sources]
        heapq.heapify(pq)
        done, par = set(), {}
        while pq:
            d, u = heapq.heappop(pq)
            if u in done:
                continue
            done.add(u)
            for v, ed in G[u].items():
                if v in done:
                    continue
                zu, zv = Z.get(u, np.nan), Z.get(v, np.nan)
                climb = max(0.0, zu - zv) if np.isfinite(zu) and np.isfinite(zv) else 0.0
                nd = d + ed["length"] + CLIMB_PENALTY * climb
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    par[v] = u
                    heapq.heappush(pq, (nd, v))
        return dist, par

    if len(Gt):
        dist, par = dijkstra(set(Gt.nodes))
        for v, p in par.items():
            parent.setdefault(v, p)
    else:
        dist = {}

    orphan = [n for n in G if n not in parent and n not in roots]
    for c in nx.connected_components(G.subgraph(orphan)):
        r = min(c, key=lambda n: Z[n] if np.isfinite(Z[n]) else 1e9)
        _, p2 = dijkstra([r])
        for v, p in p2.items():
            if v in c:
                parent.setdefault(v, p)
        roots[r] = "no_trunk"

    rec.metric("corridor_components", nx.number_connected_components(G))
    edges = {v: p for v, p in parent.items() if G.has_edge(v, p)}
    lost = len(parent) - len(edges)
    if lost:
        rec.note(f"{lost} parent pointers did not resolve to a graph edge and were dropped")

    tree_m = sum(G[v][p]["length"] for v, p in edges.items())
    graph_m = sum(d["length"] for *_, d in G.edges(data=True))
    rec.metric("tree_km", round(tree_m / 1000, 1))
    rec.metric("loop_closing_km_no_pipe", round((graph_m - tree_m) / 1000, 1))
    rec.metric("outfalls", len(roots))
    return edges, roots, (graph_m - tree_m)


def topology(edges, roots):
    """kids, an upstream-first order, and the contributing length at every edge.

    An edge is keyed by its UPSTREAM node, which is unique in a forest - every node has at
    most one outgoing edge, and contract.Network.add_edge enforces exactly that.
    """
    kids = collections.defaultdict(list)
    for v, p in edges.items():
        kids[p].append(v)
    order, seen, stack = [], set(), list(roots)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        order.append(n)
        stack.extend(kids.get(n, ()))
    rev = list(reversed(order))                # upstream-first
    return kids, rev


def contributing(edges, kids, rev, L):
    """Network length upstream of and including each edge.

    HIERARCHY_RULES R14: contributing LENGTH beats contributing properties as a predictor of
    the designer's own tier label - "the designer was laying a network, not counting houses".
    """
    c = {}
    for v in rev:
        if v in edges:
            c[v] = L[v] + sum(c[w] for w in kids.get(v, ()) if w in c)
    return c


# ======================================================================================
# 4. THE HIERARCHY
# ======================================================================================

def prune_fingers(edges, kids, L, nplot, trunk_of, rec):
    """Philosophy sec 4: a dead-end reach under ~60 m serving nothing is pruned or absorbed.

    Strictly as written - a LEAF edge, shorter than 60 m, with no load-bearing plot inside the
    60 m frontage. Applied repeatedly, because pruning a leaf exposes the next one. Anything
    longer than 60 m that also serves nothing is NOT pruned here: that is the P7 scope
    question and it belongs to stage 1 with the user, not to a tiering script. Its extent is
    measured and reported instead.

    THE TRUNK IS EXEMPT, and it has to be said out loud because the weld is what made this
    bite. The finger rule is a rule about laterals - "a dead-end reach ... SERVING NOTHING" -
    and the trunk serves nothing by design: it conveys. It is also a client INPUT (CLAUDE.md)
    and this stage declares it LOCKED. Before `weld_trunk` the trunk arrived as whole stage 2
    corridors, mostly longer than FINGER_M, and the rule rarely reached it. After the weld it
    arrives as segments cut wherever stage 2's shadow copy of the alignment crosses stage 3's,
    which in open ground averages ~48 m - under the 60 m threshold. Measured 2026-09-02: with
    no exemption the rule walked 524.9 m off the eastern tail of the 11.54 km trunk leg, one
    leaf at a time, and the published trunk came out 85.75 km against the 86.11 km in the
    graph. A design must not delete a client's alignment as untidy.
    """
    removed, removed_m = set(), 0.0
    kept = set()                      # a SET: the loop revisits the same leaf every pass
    live_kids = {k: list(v) for k, v in kids.items()}
    changed = True
    while changed:
        changed = False
        for v in list(edges):
            if v in removed or live_kids.get(v):
                continue
            if L[v] < FINGER_M and nplot.get(v, 0) == 0:
                if trunk_of.get(v):
                    kept.add(v)
                    continue
                removed.add(v)
                removed_m += L[v]
                p = edges[v]
                if v in live_kids.get(p, ()):
                    live_kids[p].remove(v)
                changed = True
    rec.metric("fingers_pruned", len(removed))
    rec.metric("fingers_pruned_km", round(removed_m / 1000, 3))
    rec.metric("fingers_trunk_exempt", len(kept))
    rec.metric("fingers_trunk_exempt_km", round(sum(L[v] for v in kept) / 1000, 3))
    return removed, removed_m


def assign_sub_mains(edges, kids, contrib, L, trunk_of):
    """The main-stem decomposition. HIERARCHY_RULES R4/R5/R6, philosophy sec 4.

    A sub main is generated where a catchment needs one way out, and it stops where the
    catchment stops being worth a collector. Seeds are the edges that discharge straight into
    the trunk or into an outfall; each seed with at least SM_CATCH_MIN_M of network behind it
    starts a route, and the route walks upstream into the largest child while:

        the next stem edge still carries SM_CATCH_MIN_M of catchment, and
        this route has not yet gathered SM_CATCH_MAX_M of it

    Side branches that themselves carry SM_CATCH_MIN_M spawn their own route - that is what
    makes the sub-main tier a NETWORK rather than a single stem. A seed below the floor is
    left as lateral, which is package 5A-3 exactly: 3.46 km of sewer, no sub-main tier, its
    laterals straight onto the trunk (R6).

    A seed must also have something UPSTREAM of it. R4 defines a sub main as a route that
    "gathers a cluster of lateral zones"; a head reach gathers nothing, so a single 4 km rural
    corridor that happens to clear the catchment floor on its own length alone is a long
    lateral, not a collector.
    """
    tier = {v: ("trunk main" if trunk_of[v] else "lateral") for v in edges}
    why = {v: ("trunk_input" if trunk_of[v] else "residual") for v in edges}
    sm_id, routes = {}, []

    def collects(v):
        return any(w in edges for w in kids.get(v, ()))

    seeds = [v for v, p in edges.items()
             if not trunk_of[v] and (p not in edges or trunk_of[p])
             and contrib.get(v, 0.0) >= SM_CATCH_MIN_M and collects(v)]
    stack = list(seeds)
    while stack:
        v = stack.pop()
        if tier[v] == "sub main" or not collects(v):
            continue
        rid = len(routes)
        members, cur, c0 = [], v, contrib[v]
        while True:
            tier[cur] = "sub main"
            why[cur] = "stem"
            sm_id[cur] = rid
            members.append(cur)
            ks = [w for w in kids.get(cur, ()) if w in edges and not trunk_of[w]]
            if not ks:
                break
            nxt = max(ks, key=lambda w: contrib[w])
            for w in ks:
                if w is not nxt and contrib[w] >= SM_CATCH_MIN_M:
                    stack.append(w)
            if contrib[nxt] < SM_CATCH_MIN_M:
                break
            if c0 - contrib[nxt] > SM_CATCH_MAX_M:
                stack.append(nxt)              # hand over: the next route starts here
                break
            cur = nxt
        routes.append(dict(rid=rid, outlet=v, members=members,
                           own_m=sum(L[w] for w in members), catch_m=contrib[v]))
    return tier, why, sm_id, routes


def split_runs(edges, kids, rev, tier, L):
    """Cut the tiered tree into RUNS - one unbranched street run each, capped at 920 m.

    A run ends where the tier changes, where the upstream node is a junction (more than one
    incoming reach of the same tier), or where the 920 m cap is reached. That is
    HIERARCHY_RULES R1 - 99.6 % of as-built lateral zones are a simple unbranched path with
    one head and one outlet - expressed on our own graph.
    """
    run_of, run_len = {}, collections.defaultdict(float)
    n = 0
    for v in rev:
        if v not in edges:
            continue
        same = [w for w in kids.get(v, ()) if w in edges and tier[w] == tier[v]]
        if len(same) == 1 and run_len[run_of[same[0]]] + L[v] <= LATERAL_CAP_M:
            run_of[v] = run_of[same[0]]
        else:
            n += 1
            run_of[v] = n
        run_len[run_of[v]] += L[v]
    return run_of, run_len


def apply_chain_bound(edges, kids, rev, tier, why, run_of, L):
    """Philosophy sec 4: "At most 3 laterals and 750 m of flow path before a main."

    Two counters ride down every flow path, both taking the WORST incoming branch at a
    junction - the bound is a maximum, so the longest arriving chain governs:

        CHAIN_N  lateral RUNS crossed since the last main-or-above
        CHAIN_M  metres of lateral flow path since the last main-or-above

    An edge that would carry the count past 3 runs or the path past 750 m is promoted to
    `main`. Promotion resets both counters, and because a main may never discharge into a
    lateral (F2), everything downstream stays at least a main - so the promoted length is the
    stretch between the breach and the collector that should already have been there.

    TWO INTERPRETATIONS, STATED RATHER THAN HIDDEN.

      1. The bound is applied at RUN BOUNDARIES, never inside a run. Promoting the middle of
         an unbranched street run would contradict the sentence immediately before it - "a
         lateral is ONE unbranched street run" - and would put a tier change where there is
         no junction to change tier at.
      2. A HEAD run is never promoted, however long it is. A run that starts at a gate and
         reaches 750 m before its first junction satisfies one sentence of sec 4 and breaches
         the other; calling a dead-end street a collector describes the network wrongly, and
         the as-built itself runs a 1,153 m flow path to its first main (R12). Those are
         flagged CHAIN_OVR instead, so the count is visible.
    """
    cn, cm = {}, {}
    promoted_m = 0.0
    for v in rev:
        if v not in edges:
            continue
        if tier[v] != "lateral":
            cn[v], cm[v] = 0, 0.0
            continue
        lk = [w for w in kids.get(v, ()) if w in edges and tier[w] == "lateral"]
        # runs crossed: a child in the SAME run does not add one; a child in another run does
        n_in = 0
        for w in lk:
            n_in = max(n_in, cn[w] + (0 if run_of[w] == run_of[v] else 1))
        m_here = max([cm[w] for w in lk], default=0.0) + L[v]
        n_here = max(n_in, 1)
        starts_run = bool(lk) and not any(run_of[w] == run_of[v] for w in lk)
        if (n_here > CHAIN_MAX_RUNS or m_here > CHAIN_MAX_M) and starts_run:
            tier[v] = "main"
            why[v] = "chain_bound"
            promoted_m += L[v]
            cn[v], cm[v] = 0, 0.0
        else:
            cn[v], cm[v] = n_here, m_here
    return cn, cm, promoted_m


def enforce_monotonic(edges, kids, order, tier, why):
    """F2 - a lateral never receives from a main, a sub main or the trunk.

    Swept downstream so a promotion anywhere upstream cannot leave a smaller pipe below it.
    Most of what it does is legitimate work rather than repair: the chain bound promotes the
    reach at the breach, and this sweep carries that promotion down to the collector that
    should already have been there. The count is published either way, because "the sweep
    changed nothing" is a claim that has to be measurable rather than asserted.
    """
    rank = {"rider": 0, "lateral": 1, "main": 2, "sub main": 3, "trunk main": 4}
    inv = {v: k for k, v in rank.items()}
    fixed = 0
    # `order` is root-first (a parent always precedes its children), so walking it backwards
    # settles every child before the parent that receives it.
    for v in reversed(order):
        if v not in edges or tier[v] == "trunk main":
            continue
        r = rank[tier[v]]
        for w in kids.get(v, ()):
            if w in edges:
                r = max(r, rank[tier[w]])
        if r > rank[tier[v]]:
            # a reach receiving the trunk is not itself the trunk - the trunk is an input and
            # is never extended by this stage; the highest tier it may be given is sub main
            tier[v] = "sub main" if inv[r] == "trunk main" else inv[r]
            why[v] = "monotonic"
            fixed += 1
    return fixed


# ======================================================================================
# 5. REPORTING - every generated shape against the band it came from
# ======================================================================================

@contract.published("tier_length_km", "km", "s4_hierarchy.tier_shares")
def tier_shares(tier, L, live):
    """The ONE function that produces a tier length. P2 - seven different station counts are
    in circulation on this project because each was computed at the point of reporting."""
    out = collections.OrderedDict()
    tot = sum(L[v] for v in live)
    for t in ("lateral", "main", "sub main", "trunk main"):
        km = sum(L[v] for v in live if tier[v] == t) / 1000
        out[t] = (km, 100 * km / (tot / 1000) if tot else 0.0)
    out["_total_km"] = (tot / 1000, 100.0)
    return out


def band(name, vals, ref, fmt="%.0f", labels=("p50", "p95", "max")):
    v = np.asarray(vals, dtype=float)
    if not len(v):
        return f"  {name:<34} (none)"
    if labels == ("p50", "p95", "max"):
        got = (np.median(v), np.percentile(v, 95), v.max())
    else:
        got = (np.median(v), v.min(), v.max())
    g = " / ".join(fmt % x for x in got)
    r = " / ".join(fmt % x for x in ref)
    return f"  {name:<34} {g:<26} as-built {r}"


# ======================================================================================
# 6. MAIN
# ======================================================================================

def main():
    t_start = time.time()
    os.makedirs(os.path.join(W11A, "shp"), exist_ok=True)
    os.makedirs(OUT_RUN, exist_ok=True)

    _say("=" * 88)
    _say("W11a STAGE 4 - HIERARCHY AND TIERS")
    _say("=" * 88)

    # Manifest.records is a class attribute, so a standalone run of one stage would rewrite
    # the shared manifest.json with only its own record and erase stages 1-3. Written to a
    # stage file instead; an orchestrator that runs every stage in one process still gets the
    # complete picture, because the records accumulate.
    with contract.Manifest.stage(STAGE, 4,
                                 path=os.path.join(OUT_RUN, "manifest_s4.json")) as rec:
        corr, corr_upstream = load_corridors(rec)
        trunk, trunk_upstream, trunk_how = load_trunk(corr, rec)
        corr_nodes = None
        if corr_upstream and "corridor_nodes" in _layers(P_GPKG_W11A):
            corr_nodes = gpd.read_file(P_GPKG_W11A, layer="corridor_nodes")
            rec.read("corridor_nodes (stage 2)", P_GPKG_W11A, len(corr_nodes))
        servicing = load_servicing(rec)

        waiting = []
        if corr is None:
            waiting.append("stage 2 `corridors` in W11a/shp/W11a.gpkg, or the reuse layer "
                           f"{P_CORR_FALL}")
        if trunk is None:
            waiting.append("stage 3 trunk (TIER='trunk main' in W11a.gpkg), or the input "
                           f"{P_TRUNK_FALL}")
        if waiting:
            _say("\nSTOPPED - waiting on an upstream stage. Nothing was written.")
            for w in waiting:
                _say(f"   needs: {w}")
            rec.did_nothing("upstream inputs absent: " + "; ".join(waiting))
            return 0

        _say(f"  corridors : {'stage 2' if corr_upstream else 'FALLBACK ' + P_CORR_FALL}")
        _say(f"  trunk     : {trunk_how}")
        _say(f"  scope     : {'stage 1 servicing' if servicing is not None else 'NOT SET'}")
        if not corr_upstream or not trunk_upstream:
            _say("")
            _say("  " + "!" * 84)
            _say("  FALLBACK MODE - stages 1-3 have not published. This stage is running on the")
            _say("  layers the build brief names for reuse, and the whole output is graded")
            _say("  CONFIDENCE = provisional. Specifically NOT yet true of this tree:")
            if not corr_upstream:
                _say("    * stage 1 has not set the served set, so every corridor is carried")
                _say("    * stage 2 has not applied the wadi / dual-carriageway exclusions AT")
                _say("      SOURCE (philosophy sec 2). Segments inheriting a parent corridor with")
                _say("      dual or wadi length are flagged DUAL_WARN / WADI_WARN, not removed")
            if not trunk_upstream:
                _say("    * stage 3 has not published a trunk; the user's Main Pipe drawing is")
                _say("      used directly, which is what it is for (CLAUDE.md: an INPUT)")
            _say("  " + "!" * 84)
            _say("")

        _say("[1] corridor graph")
        has_topo = ({"US_NODE", "DS_NODE"} <= set(corr.columns)
                    and not corr[["US_NODE", "DS_NODE"]].isna().any().any())
        if has_topo:
            if trunk_how == "in_corridors":
                # the trunk IS a subset of the corridors here and is matched by IDENTITY,
                # not by a tolerance. Nothing to weld.
                trunk_ids = set(trunk.CORR_ID.astype(str)) if "CORR_ID" in trunk.columns \
                    else set()

                def trunk_where(r, g, _ids=trunk_ids):
                    return str(getattr(r, "CORR_ID", "")) in _ids

                G, idx = adopt_graph(corr, corr_nodes, trunk_where, rec)
            else:
                # stage 3's trunk (or the user's drawing) is a SEPARATE layer with its own
                # chambers. It is WELDED in, never matched by proximity - OPEN-S4-1.
                G, idx = adopt_graph(corr, corr_nodes, lambda r, g: False, rec)
                weld_trunk(G, idx, trunk, rec)
        else:
            G, idx, _ = build_graph(corr, trunk, rec)
        # The trunk is a SECOND input, so the tiering funnel starts at the GRAPH, not at the
        # corridor count: a funnel that starts upstream of an addition cannot close. The
        # noding funnel closed inside adopt_graph / build_graph, and the weld closed its own.
        fun = rec.funnel("graph edges -> tiered reaches", G.number_of_edges())
        _say(f"  {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges, "
             f"{sum(d['length'] for *_, d in G.edges(data=True)) / 1000:,.1f} km")

        _say("[2] ground levels (orientation only - levels are stage 6)")
        Z = sample_terrain(idx, rec)

        _say("[3] flow tree - trunk first, then everything drains to it")
        edges, roots, loop_m = build_tree(G, idx, Z, rec)
        L = {v: G[v][p]["length"] for v, p in edges.items()}
        trunk_of = {v: bool(G[v][p]["trunk"]) for v, p in edges.items()}
        kids, rev = topology(edges, roots)
        order = list(reversed(rev))
        contrib = contributing(edges, kids, rev, L)
        _say(f"  {len(edges):,} directed reaches, {sum(L.values()) / 1000:,.1f} km, "
             f"{len(roots):,} outfalls, trunk "
             f"{sum(L[v] for v in edges if trunk_of[v]) / 1000:,.2f} km")
        _say(f"  {loop_m / 1000:,.1f} km of corridor closes a loop and carries no pipe in this "
             f"tree")
        fun.drop(f"loop-closing street - a spanning tree cannot lay pipe on every edge of a "
                 f"grid without a cycle (H15). W8's augment_cross_streets is the fix and it "
                 f"belongs to stage 2/3 ({loop_m / 1000:.1f} km)",
                 n=G.number_of_edges() - len(edges))

        _say("[4] plot frontage (the P7 question, not the load allocation)")
        plots = load_plots(rec)
        nplot = collections.defaultdict(int)
        nprop = collections.defaultdict(float)
        qfront = collections.defaultdict(float)
        if plots is not None:
            keys = list(edges.items())
            buf = gpd.GeoDataFrame(
                {"i": range(len(keys))},
                geometry=[G[v][p]["geom"].buffer(PLOT_FRONT_M) for v, p in keys],
                crs=contract.CRS_EPSG)
            j = gpd.sjoin(buf, plots, how="left", predicate="intersects")
            agg = j.groupby("i").agg(n=("index_right", "count"),
                                     prop=("N_PROP", "sum"), q=("Q_AVG_M3D", "sum"))
            for i, (v, _p) in enumerate(keys):
                if i in agg.index:
                    nplot[v] = int(agg.n.loc[i])
                    nprop[v] = float(agg.prop.loc[i] or 0.0)
                    qfront[v] = float(agg.q.loc[i] or 0.0)
            # Counted BEFORE the finger prune, so it is a diagnostic of the corridor set and
            # NOT the published P7 number. The published one is measured once, on the
            # published length, after pruning - see `d0` in the report. Two numbers under one
            # name is what put seven lifting-station counts into circulation (P2): the
            # manifest said 185.6 km and the report said 168.8 km, both labelled the same.
            dead = sum(L[v] for v in edges if nplot[v] == 0)
            _say(f"  {dead / 1000:,.1f} km has no load-bearing plot within {PLOT_FRONT_M:.0f} m "
                 f"before the finger prune - the P7 scope question, for stage 1")
        else:
            rec.note("plot_loads absent - the finger rule could not be applied and the P7 "
                     "no-load extent is unmeasured")
            _say("  plot_loads absent: finger rule NOT applied, P7 extent unmeasured")

        _say("[5] fingers")
        # With no plot layer, `nplot` is empty and `nplot.get(v, 0) == 0` is true for EVERY
        # reach - so the rule would prune every dead-end under 60 m whether or not it serves
        # houses, while the note above declares it was not applied. A stage may do nothing;
        # it may not declare a no-op and then act (invariant 10).
        if plots is None:
            pruned, pruned_m = set(), 0.0
            rec.metric("fingers_pruned", 0)
            rec.metric("fingers_pruned_km", 0.0)
            _say("  SKIPPED - the finger rule needs the plot layer to know what serves "
                 "nothing, and pruning on an empty one prunes served streets too")
        else:
            pruned, pruned_m = prune_fingers(edges, kids, L, nplot, trunk_of, rec)
        if pruned:
            for v in pruned:
                edges.pop(v, None)
            kids, rev = topology(edges, roots)
            order = list(reversed(rev))
            contrib = contributing(edges, kids, rev, L)
        fun.drop(f"dead-end reach under {FINGER_M:.0f} m serving nothing - philosophy sec 4 "
                 f"finger rule ({pruned_m / 1000:.3f} km)", n=len(pruned))
        _say(f"  pruned {len(pruned):,} fingers, {pruned_m / 1000:.3f} km"
             + (f"; {int(rec.metrics.get('fingers_trunk_exempt', 0)):,} trunk leaves "
                f"({rec.metrics.get('fingers_trunk_exempt_km', 0):.3f} km) met the rule and "
                f"were EXEMPT - the trunk is an INPUT"
                if rec.metrics.get("fingers_trunk_exempt") else ""))

        _say("[6] tiers")
        tier, why, sm_id, routes = assign_sub_mains(edges, kids, contrib, L, trunk_of)
        run_of, run_len = split_runs(edges, kids, rev, tier, L)
        cn, cm, promoted_m = apply_chain_bound(edges, kids, rev, tier, why, run_of, L)
        run_of, run_len = split_runs(edges, kids, rev, tier, L)   # re-cut after promotion
        fixed = enforce_monotonic(edges, kids, order, tier, why)
        rec.metric("monotonicity_fixes", fixed)
        _say(f"  {len(routes):,} sub-main routes; chain bound promoted "
             f"{promoted_m / 1000:,.1f} km to `main`; {fixed} monotonicity fixes")

        # ---------------------------------------------------------------- build the graph
        _say("[7] contract graph and published layers")
        net = contract.Network(index=idx)
        conf = "provisional" if not (corr_upstream and trunk_upstream) else "drafted"
        # every component's SYSTEM: reaching the works is central; anything else is the
        # satellite / on-site question philosophy sec 8a leaves open on purpose.
        root_kind = dict(roots)
        # which outfall each node reaches. `order` is root-first, so a parent is always
        # resolved before the child that drains into it - one pass, no recursion.
        comp_root = {}
        for n in order:
            comp_root[n] = comp_root[edges[n]] if n in edges else n

        for v, p in edges.items():
            geom = G[v][p]["geom"]
            c = list(geom.coords)
            a = idx.nodes[v]
            if (c[0][0] - a.x) ** 2 + (c[0][1] - a.y) ** 2 > \
               (c[-1][0] - a.x) ** 2 + (c[-1][1] - a.y) ** 2:
                c = c[::-1]                       # orient the line along the flow
            meta = G[v][p]["meta"]
            src = meta["SRC"] if meta["SRC"] in contract.SRC else "draft"
            # P6: never launder. Take the corridor's own grade where stage 2 gave one, then
            # the SRC ceiling (auto_block / auto_link can never be better than provisional),
            # then this stage's own floor. Whichever is WEAKEST wins.
            cf = meta["CONF"] if meta["CONF"] in contract.CONFIDENCE else conf
            ceil = contract.SRC_CONFIDENCE_CEILING.get(src)
            for cand in (ceil, conf):
                if cand and contract._CONF_RANK[cand] > contract._CONF_RANK[cf]:
                    cf = cand
            r = comp_root.get(v, v)
            net.index.nodes[v].tier = tier[v]
            net.index.nodes[v].src = src
            net.index.nodes[v].confidence = cf
            net.index.nodes[v].stage = STAGE
            net.index.nodes[v].system = ("central" if root_kind.get(r) == "trunk_main"
                                         else "satellite")
            net.add_edge(v, p, vertices=tuple(c[1:-1]), stage=STAGE, tier=tier[v],
                         src=src, confidence=cf,
                         attrs=dict(TIER_BY=why[v],
                                    RUN_UID=int(run_of[v]),
                                    RUN_LEN_M=round(run_len[run_of[v]], 2),
                                    CONTRIB_M=round(contrib.get(v, 0.0), 1),
                                    CHAIN_N=int(cn.get(v, 0)),
                                    CHAIN_M=round(cm.get(v, 0.0), 1),
                                    CHAIN_OVR=int(tier[v] == "lateral"
                                                  and cm.get(v, 0.0) > CHAIN_MAX_M),
                                    SM_ID=int(sm_id.get(v, -1)),
                                    N_PLOT_FR=int(nplot[v]),
                                    N_PROP_FR=round(nprop[v], 3),
                                    Q_FRONT=round(qfront[v], 4),
                                    DUAL_WARN=int(meta["DUAL_WARN"]),
                                    WADI_WARN=int(meta["WADI_WARN"]),
                                    CORR_ID=meta["CORR_ID"],
                                    QFLAG=meta["QFLAG"],
                                    ON_TRUNK=int(str(root_kind.get(r, "")).startswith("trunk")),
                                    SYSTEM=("central" if root_kind.get(r) == "trunk_main"
                                            else "satellite")))

        # node kinds and node-side attributes
        for u, nd in list(net.nodes.items()):
            n_in = len(net.in_edges.get(u, ()))
            if u not in net.out_edge:
                # terminal: the works, or a provisional outfall standing in for a decision
                # stage 5/7 has to make. Its tier is the highest arriving at it.
                nd.kind = "outfall"
                rk = {"lateral": 1, "main": 2, "sub main": 3, "trunk main": 4}
                arriving = [net.edges[e].tier for e in net.in_edges.get(u, ())]
                if arriving:
                    nd.tier = max(arriving, key=lambda t: rk.get(t, 0))
            elif n_in == 0:
                nd.kind = "head"                        # sec 4: "a head starts at the gate"
            elif n_in > 1:
                nd.kind = "junction"
            else:
                nd.kind = "chamber"
            nd.attrs = dict(
                CONTRIB_M=round(contrib.get(u, 0.0), 1),
                N_PLOT_FR=int(nplot.get(u, 0)),
                N_PROP_FR=round(nprop.get(u, 0.0), 3),
                SYSTEM=("central" if root_kind.get(comp_root.get(u, u)) == "trunk_main"
                        else "satellite"),
                IS_OUTFALL=int(u not in net.out_edge),
                OUT_WHY=root_kind.get(u, ""),
                GRD_SRC="VRT_0p5m",
            )
            nd.grd_m = float(Z.get(u, np.nan))
            nd.stage = STAGE

        # drop nodes the tree never used (a 3 m collapse can strand one)
        orphan = [u for u in list(net.nodes)
                  if u not in net.out_edge and not net.in_edges.get(u)]
        for u in orphan:
            net.index.nodes.pop(u, None)
        if orphan:
            rec.note(f"{len(orphan):,} nodes carried no reach after the {NODE_MERGE_M} m "
                     "merge and were dropped")

        problems = net.check()

        reaches = net.to_edges_gdf("gravity")
        nodes = net.to_nodes_gdf()

        # SYSTEM: stage 1's decision beats this stage's guess. The attr written above is a
        # topological reading - "does this reach drain to the trunk system" - which is kept
        # under its own name, ON_TRUNK. Which SYSTEM serves a settlement is philosophy sec 8a
        # and it is stage 1's to answer, not a by-product of our spanning tree.
        if servicing is not None and "SYSTEM" in servicing.columns:
            mid = gpd.GeoDataFrame(
                {"i": range(len(reaches))},
                geometry=reaches.geometry.interpolate(0.5, normalized=True),
                crs=contract.CRS_EPSG)
            jj = gpd.sjoin(mid, servicing[["geometry", "SYSTEM"]], how="left",
                           predicate="within")
            jj = jj[~jj.index.duplicated(keep="first")]
            got = jj.SYSTEM.reindex(range(len(reaches)))
            n_out = int(got.isna().sum())
            reaches["SYSTEM"] = [s if isinstance(s, str) and s in contract.SYSTEM
                                 else "central" for s in got]
            rec.metric("reaches_outside_a_servicing_polygon", n_out)
            _say(f"  SYSTEM taken from stage 1's servicing decision; {n_out:,} reaches fall "
                 f"outside every settlement polygon and default to central")
            # ... and the NODE layer must be told. Before this, `nodes.SYSTEM` held the
            # topological reading (19,108 satellite / 2,049 central) while `reaches.SYSTEM`
            # held stage 1's (1,738.5 km central / 25.9 satellite): two layers of ONE
            # GeoPackage, one field name, two definitions, written in one run and never
            # reconciled. That is the W10 defect the contract names by name - "the node
            # layer and the pipe layer came out of different solves". A node takes the
            # SYSTEM of its own outgoing reach; a terminal takes it from what arrives.
            sys_out = dict(zip(reaches.US_NODE, reaches.SYSTEM))
            sys_in = dict(zip(reaches.DS_NODE, reaches.SYSTEM))
            before = nodes.SYSTEM.copy()
            nodes["SYSTEM"] = [sys_out.get(u, sys_in.get(u, s))
                               for u, s in zip(nodes.NODE_UID, nodes.SYSTEM)]
            moved = int((before != nodes.SYSTEM).sum())
            rec.metric("node_system_reconciled_to_reaches", moved)
            _say(f"  {moved:,} nodes took their SYSTEM from the reach they drain through, so "
                 f"the two published layers now say the same thing")
        # LEN_M comes out of to_edges_gdf measuring the geometry it actually built, so the
        # tier shares below are computed on the PUBLISHED length, not on the graph's.
        Lpub = dict(zip(reaches.US_NODE, reaches.LEN_M))
        live = list(Lpub)
        shares = tier_shares({v: tier[v] for v in live}, Lpub, live)

        # ------------------------------------------------------- sub-main route summary
        rows = []
        for r in routes:
            mem = [m for m in r["members"] if m in Lpub]
            own = sum(Lpub[m] for m in mem)
            rows.append(dict(SM_ID=r["rid"], OUTLET=r["outlet"], N_REACH=len(mem),
                             LEN_M=round(own, 1), CATCH_M=round(r["catch_m"], 1),
                             SHARE_PCT=round(100 * own / r["catch_m"], 2) if r["catch_m"] else 0,
                             N_PROP_FR=round(sum(nprop[m] for m in mem), 2),
                             KM_PER_SM=None))
        sm = pd.DataFrame(rows)
        sm_geom = None
        if len(sm):
            # the sub-main reaches themselves, carrying their route's outlet statistics. NOT
            # dissolved: a dissolved route is a MultiLineString, and a multipart reach is
            # exactly what contract.validate refuses because audit.Ctx.graph() reads only its
            # first part and silently drops the rest.
            sm_geom = reaches[reaches.SM_ID >= 0].copy()
            sm_geom = sm_geom[["EDGE_UID", "US_NODE", "DS_NODE", "SM_ID", "LEN_M",
                               "TIER", "TIER_BY", "SRC", "CONFIDENCE", "geometry"]].merge(
                sm[["SM_ID", "N_REACH", "CATCH_M", "SHARE_PCT", "N_PROP_FR"]].rename(
                    columns={"N_REACH": "SM_NREACH"}), on="SM_ID", how="left")

        # H1 verified against the raw grid before anything is written. Recomputed, never
        # inherited (philosophy sec 8: every check recomputes from the raw terrain).
        reaches, nodes = wadi_recheck(reaches, nodes, rec)

        # ------------------------------------------------------------------ write it out
        if os.path.exists(OUT_GPKG):
            os.remove(OUT_GPKG)
        reaches.to_file(OUT_GPKG, layer="s4_reaches", driver="GPKG")
        nodes.to_file(OUT_GPKG, layer="s4_nodes", driver="GPKG")
        rec.wrote("s4_reaches", OUT_GPKG, len(reaches))
        rec.wrote("s4_nodes", OUT_GPKG, len(nodes))

        # The chain's canonical names. s5b, s6 and s7 read `reaches` and `nodes` from
        # W11a.gpkg - the names contract.py declares - and stage 4 is where the full
        # network first exists. Writing only s4_reaches into a side file left stage 6
        # reporting "WAITING ON AN UPSTREAM STAGE" against a network that was ready.
        reaches.to_file(P_GPKG_W11A, layer="reaches", driver="GPKG")
        nodes.to_file(P_GPKG_W11A, layer="nodes", driver="GPKG")
        rec.wrote("reaches (canonical)", P_GPKG_W11A, len(reaches))
        rec.wrote("nodes (canonical)", P_GPKG_W11A, len(nodes))

        # USED, written BACK onto the corridors. Stage 2 publishes it as 0 on every row
        # because at stage 2 nothing has been laid yet, and until now nothing ever wrote it
        # - so 202 km of corridor that carries no pipe could not be told from corridor
        # deliberately not used. A field that is 0 everywhere is a claim, not a number; it
        # is the same defect stage 2 fixed in ON_WADI_M, one layer along.
        #
        # It matters because the conversion rate PER SOURCE is the number that exposed the
        # W10 inversion: the sources trusted least were used most. A corridor is a proposal;
        # USED is whether the proposal was taken.
        try:
            _cor = gpd.read_file(P_GPKG_W11A, layer="corridors")
            _laid = set(reaches["CORR_ID"].astype(str)) - {"", "nan", "None"}
            _cor["USED"] = _cor["CORR_ID"].astype(str).isin(_laid).astype(int)
            _cor.to_file(P_GPKG_W11A, layer="corridors", driver="GPKG")
            _by = _cor.groupby(["SRC", "CONFIDENCE"]).agg(
                n=("USED", "size"), used=("USED", "sum"),
                km=("LEN_M", lambda x: x.sum() / 1000.0))
            _say(f"      USED written back: {int(_cor.USED.sum()):,} of {len(_cor):,} "
                 f"corridors carry a reach "
                 f"({_cor.loc[_cor.USED == 1, 'LEN_M'].sum() / 1000:,.1f} km of "
                 f"{_cor.LEN_M.sum() / 1000:,.1f} km)")
            for (src, conf), r in _by.iterrows():
                _say(f"         {src:<11s} {conf:<12s} {int(r['used']):>6,} of "
                     f"{int(r['n']):>6,}  ({100.0 * r['used'] / max(r['n'], 1):5.1f} %)"
                     f"   {r['km']:>7.1f} km offered")
            rec.metric("corridors_used", int(_cor.USED.sum()))
            rec.metric("corridors_used_km",
                       round(float(_cor.loc[_cor.USED == 1, "LEN_M"].sum()) / 1000.0, 1))
        except Exception as _e:                    # noqa: BLE001 - reported, never swallowed
            rec.note(f"USED not written back ({type(_e).__name__}: {_e}); the corridors layer "
                     f"still reads 0 everywhere, which cannot be distinguished from a "
                     f"corridor deliberately not used")
        if sm_geom is not None and len(sm_geom):
            sm_geom.to_file(OUT_GPKG, layer="s4_submains", driver="GPKG")
            rec.wrote("s4_submains", OUT_GPKG, len(sm_geom))
        # CAD / QGIS mirrors. NOT the artefact anything is audited against: every field name
        # here happens to be 10 characters or fewer today, but a DBF truncates silently and
        # contract.assert_audited_path exists precisely so a .shp never reaches the auditor.
        for nm, gg in (("reaches", reaches), ("nodes", nodes)):
            gg.to_file(os.path.join(W11A, "shp", f"W11a_s4_{nm}.shp"))
        with open(os.path.join(W11A, "shp", "W11a_s4_SHAPEFILES.README.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write("CAD / QGIS MIRRORS - NOT THE AUDITED LAYERS.\n"
                     "The audited artefact is W11a_s4.gpkg (layers s4_reaches, s4_nodes,\n"
                     "s4_submains). A shapefile DBF truncates field names at 10 characters\n"
                     "and turns a null string into '', so a check that passes on the\n"
                     "GeoPackage can fail on the mirror for reasons that have nothing to do\n"
                     "with the design. Point every check at the GeoPackage.\n")

        # invariant 1 in its general form: every corridor segment that did not become a
        # tiered reach is named, counted and retrievable. close() raises if the arithmetic
        # does not land on what was actually published.
        fun.close(len(reaches))

        # ------------------------------------------------------- invariant 2: round trip
        rb = gpd.read_file(OUT_GPKG, layer="s4_reaches")
        nb = gpd.read_file(OUT_GPKG, layer="s4_nodes")
        rt_ok, rt_msg = True, ""
        try:
            contract.Network.assert_round_trip(nb, rb)
            contract.Network.assert_degrees(nb, rb)
        except contract.ContractError as e:
            rt_ok, rt_msg = False, str(e)

        # ----------------------------------------------------------------- the F-checks
        live_set = set(live)
        f1 = int((~reaches.TIER.isin(contract.TIERS)).sum())
        rank = {"lateral": 1, "main": 2, "sub main": 3, "trunk main": 4}
        f2 = 0
        for v, p in edges.items():
            if v in live_set and p in edges and p in live_set:
                if rank[tier[p]] < rank[tier[v]]:
                    f2 += 1
        trunk_km = shares["trunk main"][0]
        net_km = shares["_total_km"][0]
        joins = [v for v, p in edges.items()
                 if v in live_set and not trunk_of[v] and p in edges and trunk_of[p]]
        lat_joins = [v for v in joins if tier[v] == "lateral"]

        lat = [v for v in live if tier[v] == "lateral"]
        runs_lat = {run_of[v] for v in lat}
        run_lens = [run_len[r] for r in runs_lat]

        rep = []
        rep.append("")
        rep.append("=" * 88)
        rep.append("TIER SHARES  (philosophy sec 4 target: lateral 66 / sub main 18 / trunk 5;")
        rep.append("              the 11 % those three leave unattributed is the `main` tier)")
        rep.append("=" * 88)
        for t in ("lateral", "main", "sub main", "trunk main"):
            km_, pc = shares[t]
            tgt = ASBUILT["tier_share_pct"].get(t.replace(" ", "_"))
            tg = f"   target {tgt:.0f} %" if tgt else "   (residual - inferred, no as-built band)"
            rep.append(f"  {t:<12} {km_:9,.1f} km   {pc:5.1f} %{tg}")
        rep.append(f"  {'TOTAL':<12} {net_km:9,.1f} km")
        rep.append("")
        rep.append(f"  SUB MAIN = {shares['sub main'][0]:,.1f} km against the philosophy sec 4 "
                   f"expectation of ROUGHLY 270 km")
        rep.append(f"             ('a design producing 20 km is wrong on sight')")
        rep.append("")
        rep.append("F-CHECKS (W8_W10_POSTMORTEM contract F1-F4; F5 is diameters, stage 6)")
        rep.append(f"  F1 every pipe carries a legal TIER        "
                   f"{'PASS' if f1 == 0 else f'FAIL - {f1:,} reaches'}")
        rep.append(f"  F2 tier monotonic (no lateral below a main) "
                   f"{'PASS' if f2 == 0 else f'FAIL - {f2:,} reaches'}")
        rep.append(f"  F3 trunk joins   {len(joins):,} "
                   f"({net_km / max(1, len(joins)):.2f} km of network each; as-built 4.6) "
                   f"({trunk_km * 1000 / max(1, len(joins)):.0f} m of trunk each; as-built 460) "
                   f"[REPORTING]")
        lat_join_km = sum(contrib.get(v, 0.0) for v in lat_joins) / 1000
        rep.append(f"     of which laterals straight onto the trunk: {len(lat_joins):,} "
                   f"(as-built 13 of 22, R10) [REPORTING]")
        rep.append(f"     they bring {lat_join_km:,.1f} km of network between them, "
                   f"{lat_join_km * 1000 / max(1, len(lat_joins)):,.0f} m each - every one "
                   f"below the")
        rep.append(f"     {SM_CATCH_MIN_M / 1000:.0f} km floor, so R6 says the sub-district is "
                   f"too small to justify a sub main (5A-3 does exactly this)")
        rep.append(f"  F4 tier shares above [REPORTING]")
        rep.append("")
        rep.append("GENERATED SHAPES against the as-built bands (HIERARCHY_RULES)")
        rep.append(band("lateral run length m", run_lens, ASBUILT["run_len_m"]))
        over_cap = [r for r in runs_lat if run_len[r] > LATERAL_CAP_M]
        one_edge = [r for r in over_cap
                    if sum(1 for v in lat if run_of[v] == r) == 1]
        rep.append(f"     {len(over_cap):,} lateral runs exceed the {LATERAL_CAP_M:.0f} m cap, "
                   f"{len(one_edge):,} of them a SINGLE corridor segment with no node inside "
                   f"it -")
        rep.append(f"     those are cut by the chamber spacing at stage 5 (H12, G203-p30 "
                   f"Tab 12), not here")
        rep.append(band("lateral chain, runs", [cn[v] for v in lat], ASBUILT["chain_runs"]))
        rep.append(band("lateral flow path to a main m", [cm[v] for v in lat],
                        ASBUILT["chain_path_m"]))
        if len(sm):
            rep.append(band("sub-main route length m", sm.LEN_M, ASBUILT["sm_route_m"],
                            labels=("p50", "min", "max")))
            rep.append(band("sub-main catchment sewer m", sm.CATCH_M, ASBUILT["sm_catch_m"],
                            labels=("p50", "min", "max")))
            rep.append(band("sub-main own/catchment %", sm.SHARE_PCT, ASBUILT["sm_share_pct"],
                            fmt="%.1f", labels=("p50", "min", "max")))
            rep.append(f"  {'network km per sub main':<34} "
                       f"{net_km / len(sm):<26.2f} as-built 4.0 - 10.0")
        rep.append("")
        rep.append("PROVENANCE (P6 - SRC and CONFIDENCE travel to the drawings)")
        for s, d in reaches.groupby("SRC"):
            rep.append(f"  {s:<12} {d.LEN_M.sum() / 1000:8,.1f} km   "
                       f"{sorted(set(d.CONFIDENCE))}")
        rep.append("")
        rep.append("WHAT SET EACH TIER")
        for w, d in reaches.groupby("TIER_BY"):
            rep.append(f"  {w:<14} {d.LEN_M.sum() / 1000:8,.1f} km   {len(d):,} reaches")
        rep.append("")
        rep.append("OPEN AND HANDED ON")
        rep.append(f"  {loop_m / 1000:,.1f} km of corridor closes a loop and gets no pipe in "
                   f"this tree.")
        rep.append(f"     A spanning tree omits every loop-closing street. W8 solved it with "
                   f"augment_cross_streets;")
        rep.append(f"     it belongs to stage 2/3, and it is the reason the lateral chains "
                   f"here run deeper than")
        rep.append(f"     the as-built - which is what inflates the `main` tier.")
        d0 = sum(Lpub[v] for v in live if nplot[v] == 0) / 1000
        # THE one definition of this number, on the published length after pruning. The
        # manifest metric is written from this same variable, not recomputed (P2).
        rec.metric("km_no_loadbearing_plot_within_60m", round(d0, 1))
        rep.append(f"  {d0:,.1f} km carries no load-bearing plot within {PLOT_FRONT_M:.0f} m "
                   f"- the P7 scope question, stage 1.")
        rep.append(f"  {int(reaches.DUAL_WARN.sum()):,} reaches inherit a corridor with dual-"
                   f"carriageway length ({reaches.LEN_M[reaches.DUAL_WARN == 1].sum() / 1000:,.1f} km).")
        if "WADI_HERE" in reaches.columns:
            wr = reaches.WADI_HERE == 1
            n_al = int(reaches.get("WADI_ALONG", pd.Series(0, index=reaches.index)).sum())
            n_xg = int(reaches.get("WADI_XING", pd.Series(0, index=reaches.index)).sum())
            al = reaches.get("WADI_ALONG", pd.Series(0, index=reaches.index)) == 1
            rep.append(f"  H1a WADI, MEASURED ON OUR OWN GEOMETRY against Hazard_T50y class "
                       f">= {WADI_CLASS_MIN}, classified ALONG vs ACROSS by audit._r4_classify:")
            n_cross = int(rec.metrics.get("reaches_crossing_a_wadi", 0))
            rep.append(f"     {n_al:,} reaches ({reaches.LEN_M[al].sum() / 1000:,.1f} km) run "
                       f"ALONG a wadi - the defect H1 forbids. {n_cross:,} CROSS one, which "
                       f"H1a permits once each is scheduled with a CROSS_ID and given 1.5 m "
                       f"cover to crown (G203-p52 8.2.4)."
                       )
            rep.append(f"     (A midpoint test alone reports {int(wr.sum()):,} reaches, "
                       f"{reaches.LEN_M[wr].sum() / 1000:,.1f} km, touching wadi ground. It "
                       f"samples ONE point per reach where the classifier samples the whole "
                       f"length, so the two are not comparable and only the classified "
                       f"counts are a finding.)")
            if n_al:
                bt = reaches[al].groupby("TIER").LEN_M.sum().sort_values(ascending=False)
                rep.append("     running along, by tier: "
                           + ", ".join(f"{k} {v:,.0f} m" for k, v in bt.items())
                           + ".  H1 admits no tier exemption (project rule 7).")
            rep.append(f"     {int(nodes.WADI_HERE.sum()):,} CHAMBERS sit on wadi ground. "
                       f"H1a item 2 admits no exemption for a chamber, on a crossing or "
                       f"anywhere else (G201-p86) - every one is a defect to re-site.")
            rep.append(f"     UNTESTED: {rec.metrics.get('km_outside_hazard_grid_untestable', 0):,} km "
                       f"({100 * float(rec.metrics.get('km_outside_hazard_grid_untestable', 0)) / max(1e-9, net_km):.0f} %) "
                       f"falls outside the Lekhuwair grid and carries NO wadi answer either "
                       f"way. audit.R4 now PUBLISHES this share rather than scoring it a "
                       f"pass, so a clean R4 is explicitly a clean result on the tested "
                       f"half. Full-coverage flood mapping is a data request, not a "
                       f"modelling choice.")
        n_sat = int((nodes.IS_OUTFALL == 1).sum())
        km_off = reaches.LEN_M[reaches.ON_TRUNK == 0].sum() / 1000
        comp_km = (reaches.groupby(reaches.US_NODE.map(comp_root)).LEN_M.sum() / 1000
                   ).sort_values(ascending=False)
        n_corr_comp = int(rec.metrics.get("corridor_components", 0))
        n_trunk_pieces = int(rec.metrics.get("trunk_pieces", 0))
        n_s2 = int(rec.metrics.get("corridor_components_stage2", n_corr_comp))
        rep.append(f"  THE CORRIDOR NETWORK arrives from stage 2 in {n_s2:,} disconnected "
                   f"pieces"
                   + (f"; welding the trunk in joins {n_s2 - n_corr_comp:,} of them and "
                      f"leaves {n_corr_comp:,}" if n_s2 != n_corr_comp else "")
                   + f". THE TRUNK is in {n_trunk_pieces:,}.")
        rep.append(f"     A hierarchy can only be as connected as the corridors under it. "
                   f"Each trunk piece has to be rooted separately,")
        rep.append(f"     so every piece past the first is an extra outfall and an H15 breach; "
                   f"the design comes out with {len(comp_km):,} drainage")
        rep.append(f"     systems (largest {comp_km.iloc[0]:,.1f} km; "
                   f"{int((comp_km >= 10).sum()):,} carry 10 km or more), and that count is a "
                   f"STAGE 2 finding before it is a")
        rep.append(f"     satellite-works question for the options appraisal (sec 8a).")
        tl = rec.metrics.get("trunk_km_lost_vs_drawing")
        if tl:
            rep.append(f"     The trunk as used here is {trunk_km:,.1f} km against the user's "
                       f"drawing - {tl} km short.")
        # Printed ALWAYS, not only when length is lost. The piece count is the finding and
        # it survives a trunk of exactly the right length; gating this on the length made it
        # invisible the moment the right source was wired in.
        rep.append(f"     MEASURED 2026-09-02, the same 85.5 km noded at 10 mm from each "
                   f"available source:")
        rep.append(f"        the user's drawing as given .......  3 components, 85.5 km")
        rep.append(f"        stage 3's DESIGNED trunk ..........  4 components, 85.5 km")
        rep.append(f"        stage 2 corridors, SRC=main_pipe ... 58 components, 80.3 km")
        rep.append(f"     Stage 3's trunk is the best source and is the one used. Two separate "
                   f"defects followed, and they had been reported as one:")
        rep.append(f"       (a) the CORRIDOR treatment shreds the trunk from 3 pieces to 58 "
                   f"and loses 5.2 km of it - a stage 2 defect, not an alignment one. STILL "
                   f"OPEN (OPEN-S2-2);")
        rep.append(f"       (b) THIS STAGE used to take that 4-piece trunk to 74, because the "
                   f"trunk was never in the graph - it was a "
                   f"{TRUNK_ON_M:.1f} m proximity MASK over stage 2's corridors, so it "
                   f"arrived in as many pieces as stage 2's COPY of it. CLOSED.")
        if "weld_corridors_renoded" in rec.metrics:
            rep.append(f"     OPEN-S4-1 is CLOSED by the WELD in `weld_trunk`: stage 3's "
                       f"alignment enters the graph as edges of its own and the "
                       f"{int(rec.metrics['weld_corridors_renoded']):,} corridors it touches "
                       f"are re-noded WITH it")
            rep.append(f"     ({100 * int(rec.metrics['weld_corridors_renoded']) / max(1, len(corr)):.1f} % "
                       f"of the layer; the rest keep the US_NODE / DS_NODE stage 2 wrote, so "
                       f"contract P3 still holds for the remainder).")
            rep.append(f"     The trunk is now {rec.metrics.get('trunk_km_welded', 0):,.2f} km "
                       f"in {n_trunk_pieces:,} piece(s) against stage 3's "
                       f"{rec.metrics.get('trunk_km_stage3', 0):,.2f} km; "
                       f"{rec.metrics.get('weld_shadow_km', 0):,.3f} km of stage 2's shadow "
                       f"copy was removed so the spine is a tree.")
            rep.append(f"     NO PIPE MOVED and the client's alignment was NOT re-routed: a "
                       f"planar union splits lines, it does not move them. The only thing "
                       f"that moved is a CHAMBER, worst case")
            rep.append(f"     {rec.metrics.get('weld_chamber_move_max_m', 0):.3f} m, inside "
                       f"the {NODE_MERGE_M:.1f} m merge radius stage 2 itself applies "
                       f"(criteria.MH_SNAP_M - closer than the clearance means ONE "
                       f"structure). Past that radius the weld raises.")
        else:
            rep.append(f"     The trunk was already a subset of the corridors and was matched "
                       f"by CORR_ID identity, not by a tolerance - nothing to weld.")
        rep.append(f"     {km_off:,.1f} km ({100 * km_off / net_km:.0f} %) reaches no piece of "
                   f"the trunk at all and drains to a provisional outfall.")
        if "SYSTEM" in reaches.columns:
            sy = reaches.groupby("SYSTEM").LEN_M.sum().div(1000).round(1)
            rep.append(f"  SYSTEM as stage 1 decided it: "
                       + ", ".join(f"{k} {v:,.1f} km" for k, v in sy.items()))
        rep.append("")
        rep.append("THE ACCOUNTING (invariant 1 - every input that did not become a published "
                   "reach is named)")
        rep.append("  Three funnels, not one, because the trunk is a SECOND input: a funnel "
                   "starting at the corridor")
        rep.append("  count cannot account for edges that were never corridors. Each closes "
                   "on its own arithmetic.")
        for f_ in rec.funnels:
            rep.append(f"  {f_.line()}")
            for s_ in f_.steps:
                rep.append(f"     -{s_['n']:,}  {s_['reason']}")
        rep.append("")
        rep.append("GRAPH INVARIANTS")
        rep.append(f"  invariant 2 (published layers ARE the graph): "
                   f"{'PASS' if rt_ok else 'FAIL'}")
        if not rt_ok:
            rep.append("    " + rt_msg[:900])
        for p_ in problems:
            rep.append(f"  Network.check: {p_[:300]}")
        rep.append("")

        text = "\n".join(rep)
        _say(text)

        ar = contract.audit_readiness(reaches=reaches, nodes=nodes)
        ar.to_csv(os.path.join(OUT_RUN, "s4_audit_readiness.csv"), index=False)
        _say(f"audit readiness at stage 4: {int(ar.can_run.sum())} of {len(ar)} checks can "
             f"already run; the rest wait on stages 5-6 (levels, sizes, chambers)")

        with open(os.path.join(OUT_RUN, "s4_hierarchy_report.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)
        pd.DataFrame([dict(tier=t, km=round(shares[t][0], 2), pct=round(shares[t][1], 2))
                      for t in ("lateral", "main", "sub main", "trunk main")]
                     ).to_csv(os.path.join(OUT_RUN, "s4_tier_shares.csv"), index=False)
        if len(sm):
            sm.drop(columns=["KM_PER_SM"]).to_csv(
                os.path.join(OUT_RUN, "s4_submain_catchments.csv"), index=False)
        rec.wrote("s4_hierarchy_report.txt", os.path.join(OUT_RUN,
                                                          "s4_hierarchy_report.txt"))
        for t in ("lateral", "main", "sub main", "trunk main"):
            rec.metric(f"km_{t.replace(' ', '_')}", round(shares[t][0], 2))
        rec.metric("trunk_joins", len(joins))
        rec.metric("sub_main_routes", int(len(sm)))
        rec.metric("F1_untiered", f1)
        rec.metric("F2_monotonicity_breaches", f2)
        rec.metric("round_trip", "PASS" if rt_ok else "FAIL")

    _say(f"\nwritten: {OUT_GPKG}  (layers s4_reaches, s4_nodes, s4_submains)")
    _say(f"         {OUT_RUN}\\s4_hierarchy_report.txt, s4_tier_shares.csv, "
         f"s4_submain_catchments.csv, s4_audit_readiness.csv")
    _say(f"         {os.path.join(OUT_RUN, 'manifest_s4.json')}")
    _say(f"total {time.time() - t_start:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
