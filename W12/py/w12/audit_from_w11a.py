"""The W11a auditor — stage 0, written before any design.

One check per constraint in `_BRAIN/08_DESIGN_PHILOSOPHY.md`, so a rule cannot exist without
a check and the two lists cannot drift apart. That drift is exactly what happened in W10: it
carried thirteen hard constraints and a checklist that named none of them, and shipped with
2.80 km of surcharged trunk, 45.92 km below minimum cover and 1.67 km of pipe along a dual
carriageway.

TWO ARCHITECTURAL DECISIONS, both taken because of how W10 failed:

  1. It audits the PUBLISHED LAYERS, not an in-memory model. W10's flow tree existed only
     inside a script; the shapefile it wrote out was 7,919 disconnected pieces and nobody
     could have known. If the auditor cannot read it from disk, it does not exist.

  2. A check that CANNOT RUN is a failure, not a blank. W10's pipe layer has no TIER field
     and no laid gradient, so several checks here will report NOT_CHECKABLE against it —
     and that is the correct answer, not an excuse. Per the philosophy: "any check that
     cannot run" is blocking.

Run it against W10's layers on day one. The failing table is the specification for W11a.

    python -m w11a.audit --pipes ../W10/shp/W10_pipes.shp --nodes ../W10/shp/W10_nodes_depth.shp
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import geopandas as gpd
import networkx as nx
import numpy as np
from scipy.spatial import cKDTree
from shapely.ops import unary_union

# --------------------------------------------------------------------------- results

PASS, FAIL, NOT_CHECKABLE = "PASS", "FAIL", "NOT_CHECKABLE"

# Endpoints closer than this are the same node. Deliberately tight: see h15.
SNAP_M = 0.01

# --- wadi crossing tolerances (philosophy H1a) ------------------------------------------
# H1 says a crossing is "perpendicular". These put a number on that word. They are PROJECT
# tolerances on our own rule, NOT guideline values - the guidelines give the cover at a
# crossing (G203-p52 8.2.4) and the procedure for one (G201 9.3) but never say how square it
# must be, and inventing a guideline number is prohibited.
# WADI_SAMPLE_M is NOT declared here any more. It was 1.5 m here and 3.0 m in the export
# stage, with the two comments disagreeing about the grid size as well (3 m against 5 m).
# Measured 2026-09-06: Hazard_T50y.tif is 3.000 m. One source of truth now, in criteria.
from w12.criteria import hazard_sample_step_m as _hazard_step
WADI_SAMPLE_M = _hazard_step()          # half the cell - see criteria.hazard_sample_step_m

WADI_XING_SKEW = 1.155  # contact / band-width across the pipe; 1/cos(30 deg)
WADI_PROBE_M = 400.0    # how far a perpendicular probe looks for the far bank before
                        # concluding the pipe runs ALONG the band rather than across it


@dataclass
class Result:
    id: str
    group: str
    requirement: str
    source: str
    blocking: bool
    status: str
    summary: str
    n_bad: int = 0
    extent: str = ""


@dataclass
class Check:
    id: str
    group: str
    requirement: str
    source: str
    blocking: bool
    fn: Callable


REGISTRY: List[Check] = []


def check(id, group, requirement, source, blocking=True):
    def deco(fn):
        REGISTRY.append(Check(id, group, requirement, source, blocking, fn))
        return fn
    return deco


# --------------------------------------------------------------------------- context

class Ctx:
    """Everything a check may look at. Nothing is computed that a check does not ask for."""

    def __init__(self, pipes=None, nodes=None, crit=None, hazard=None,
                 roads=None, existing=None, crossings=None):
        # `terrain` and `plots` were accepted and read by no check. A parameter nothing
        # uses is a promise the auditor does not keep; removed rather than left dangling.
        self.pipes = pipes
        self.nodes = nodes
        self.crit = crit
        self.hazard = hazard
        self.roads = roads
        self.existing = existing
        # The crossings REGISTER. A CROSS_ID on a pipe is a pointer; the register is
        # what carries the G201 9.3 obligations. Without it, nothing is scheduled.
        self.crossings = crossings
        self._cache = {}

    def need(self, *cols):
        """Raise if the pipe layer lacks a field a check depends on.

        Raising rather than returning False is deliberate: the runner turns it into
        NOT_CHECKABLE, which the philosophy treats as a failure. A missing field is a
        missing answer, not a pass.
        """
        if self.pipes is None:
            raise KeyError("no pipe layer")
        missing = [c for c in cols if c not in self.pipes.columns]
        if missing:
            raise KeyError("pipe layer has no " + ", ".join(missing))
        return True

    def graph(self, snap=SNAP_M):
        """The network as published, snapped only at the tolerance a GIS would use.

        Deliberately tight. A layer that needs 2.5 m of snapping to become connected is not
        a connected layer, and pretending otherwise is what let W10 publish 7,919 pieces.
        """
        key = ("graph", snap)
        if key in self._cache:
            return self._cache[key]
        ends = []
        # A MultiLineString contributes ALL its parts. Taking geoms[0] silently dropped
        # the rest, so a layer could look connected because half of it was invisible.
        for g in self.pipes.geometry:
            parts = g.geoms if g.geom_type == "MultiLineString" else [g]
            for ls in parts:
                ends.append(ls.coords[0][:2])
                ends.append(ls.coords[-1][:2])
        arr = np.array(ends)
        tree = cKDTree(arr)
        lab = np.full(len(arr), -1, dtype=np.int64)
        for i in range(len(arr)):
            if lab[i] != -1:
                continue
            lab[i] = i
            for j in tree.query_ball_point(arr[i], snap):
                if lab[j] == -1:
                    lab[j] = i
        G = nx.Graph()
        k = 0
        for i, g in enumerate(self.pipes.geometry):
            n_parts = len(g.geoms) if g.geom_type == "MultiLineString" else 1
            for _ in range(n_parts):
                G.add_edge(int(lab[2 * k]), int(lab[2 * k + 1]), idx=i)
                k += 1
        self._cache[key] = G
        return G


def od(ctx, dn):
    """Outside diameter, from the SAME constant the design lays to.

    This was hardcoded at 0.10 m and the criteria use WALL_ALLOW = 0.05. A design laid
    correctly to criteria.invert_depth_min was 50 mm short of what H3 demanded, on every
    reach, at every diameter - a blocking failure caused entirely by the auditor. Found by
    an agent reading both files side by side, which is the only way this kind of defect
    ever surfaces.
    """
    return dn / 1000.0 + ctx.crit.WALL_ALLOW


def km(gdf_or_mask, ctx):
    """Length in km of a boolean mask over the pipe layer."""
    if "LEN_M" in ctx.pipes.columns:
        return float(ctx.pipes.LEN_M[gdf_or_mask].sum()) / 1000
    return float(ctx.pipes.geometry[gdf_or_mask].length.sum()) / 1000


# --------------------------------------------------------------------------- H checks

@check("H1", "corridor", "No pipe along a dual carriageway; no pipe or chamber in a wadi",
       "project rules 7, 8")
def h1(ctx):
    if ctx.roads is None:
        raise KeyError("no road layer")
    dual = ctx.roads[ctx.roads["dual"].astype(str) == "1"]
    buf = unary_union(dual.geometry.buffer(6.0))
    along = ctx.pipes.geometry.intersection(buf).length
    bad = along > 30.0
    n = int(bad.sum())
    if n == 0:
        return PASS, "no reach runs more than 30 m inside the 6 m dual band", 0, ""
    return FAIL, f"{n} reaches run along a dual carriageway", n, f"{along[bad].sum()/1000:.2f} km"


@check("H2", "hydraulics", "Capacity >= discharge, within the d/D limit", "G203-p27 T10")
def h2(ctx):
    ctx.need("DN", "QPK_LS")
    from sewnet import hydra
    slope_col = "SLOPE_LAID" if "SLOPE_LAID" in ctx.pipes.columns else "SLOPE_PCT"
    surch, over = 0, 0
    for _, r in ctx.pipes.iterrows():
        y, v = hydra.pipe_state(int(r.DN), float(r[slope_col]) / 100.0,
                                float(r.QPK_LS) / 1000.0, ctx.crit)
        if y is None:
            surch += 1
        elif y > hydra.dod_limit(int(r.DN), ctx.crit):
            over += 1
    if surch == 0 and over == 0:
        return PASS, "every pipe passes its peak flow within d/D", 0, ""
    return FAIL, f"{surch} surcharged, {over} over the d/D limit", surch + over, ""


@check("H3", "cover", "Minimum cover 1.30 m to crown, on the reach's OWN outside diameter",
       "G203-p33")
def h3(ctx):
    ctx.need("DN", "US_DEPTH", "DS_DEPTH")
    odm = ctx.pipes.DN.map(lambda d: od(ctx, int(d)))
    bad = ((ctx.pipes.US_DEPTH - odm) < 1.30 - 1e-6) | ((ctx.pipes.DS_DEPTH - odm) < 1.30 - 1e-6)
    n = int(bad.sum())
    if n == 0:
        return PASS, "every reach has at least 1.30 m of cover", 0, ""
    worst = float((ctx.pipes.US_DEPTH - odm).min())
    return FAIL, f"{n} reaches below minimum cover, worst {worst:.2f} m", n, f"{km(bad, ctx):.2f} km"


@check("H4", "cover", "Maximum cover 12 m, exits only via philosophy 5", "G203-p33")
def h4(ctx):
    ctx.need("DN", "US_DEPTH", "DS_DEPTH")
    odm = ctx.pipes.DN.map(lambda d: od(ctx, int(d)))
    cov = np.maximum(ctx.pipes.US_DEPTH - odm, ctx.pipes.DS_DEPTH - odm)
    bad = cov > 12.0 + 1e-6
    n = int(bad.sum())
    flagged = "PAST_CAP" in ctx.pipes.columns
    if n == 0:
        return PASS, "nothing past 12 m of cover", 0, ""
    if not flagged:
        return FAIL, f"{n} reaches past the cap and NO flag field to justify them", n, ""
    unflagged = int((bad & (ctx.pipes.PAST_CAP.fillna(0) == 0)).sum())
    if unflagged:
        return FAIL, f"{unflagged} of {n} past the cap are unflagged", unflagged, ""
    return PASS, f"{n} past the cap, all flagged with an exit", 0, ""


@check("H5", "hydraulics", "Self-cleansing by EITHER route - velocity or tractive force",
       "G203-p26-27")
def h5(ctx):
    """G203 offers two methods, not two tests. A pipe passes if it satisfies either.

    The velocity route is unreachable for a small lightly-loaded sewer - a DN200 carrying a
    few L/s runs far too shallow - which is exactly why the tractive method is derived at
    d/D = 0.2. Applying velocity as an absolute condemns almost every small sewer ever built.
    So the check reports the SPLIT, and flags only pipes that satisfy neither.
    """
    ctx.need("DN", "QPK_LS")
    from sewnet import hydra
    slope_col = "SLOPE_LAID" if "SLOPE_LAID" in ctx.pipes.columns else "SLOPE_PCT"
    by_vel, by_tractive, neither = 0, 0, 0
    for _, r in ctx.pipes.iterrows():
        s_laid = float(r[slope_col]) / 100.0
        q = float(r.QPK_LS) / 1000.0
        y, v = hydra.pipe_state(int(r.DN), s_laid, q, ctx.crit)
        if v is not None and v >= 0.75:
            by_vel += 1
        elif s_laid >= hydra.smin_tractive(q, ctx.crit) - 1e-9:
            by_tractive += 1
        else:
            neither += 1
    share = 100.0 * by_tractive / max(len(ctx.pipes), 1)
    if neither == 0:
        return PASS, (f"all self-cleansing: {by_vel:,} by velocity, {by_tractive:,} by "
                      f"tractive force ({share:.0f} % - exposed to the tau = 1.0 Pa "
                      f"assumption, GAP-9)"), 0, ""
    return FAIL, f"{neither:,} reaches satisfy neither route", neither, ""


@check("H6", "hydraulics", "Gradient >= Table 11 for the diameter", "G203-p29 T11")
def h6(ctx):
    ctx.need("DN", "QPK_LS")
    from sewnet import hydra
    slope_col = "SLOPE_LAID" if "SLOPE_LAID" in ctx.pipes.columns else "SLOPE_PCT"
    bad = 0
    for _, r in ctx.pipes.iterrows():
        need = hydra.smin_for(int(r.DN), float(r.QPK_LS) / 1000.0, ctx.crit)
        if float(r[slope_col]) / 100.0 < need - 1e-9:
            bad += 1
    if bad == 0:
        return PASS, "every gradient meets its minimum", 0, ""
    return FAIL, f"{bad} reaches below their minimum gradient", bad, ""


@check("H7", "hydraulics", "Maximum velocity 3.0 m/s gravity", "G203-p27")
def h7(ctx):
    ctx.need("DN", "QPK_LS")
    from sewnet import hydra
    if "SLOPE_LAID" not in ctx.pipes.columns:
        raise KeyError("pipe layer has no SLOPE_LAID - the laid gradient is not published, "
                       "so velocity cannot be checked (philosophy 5)")
    fast = 0
    for _, r in ctx.pipes.iterrows():
        y, v = hydra.pipe_state(int(r.DN), float(r.SLOPE_LAID) / 100.0,
                                float(r.QPK_LS) / 1000.0, ctx.crit)
        if v is not None and v > ctx.crit.V_MAX:
            fast += 1
    if fast == 0:
        return PASS, f"nothing over {ctx.crit.V_MAX} m/s", 0, ""
    return FAIL, f"{fast} reaches over {ctx.crit.V_MAX} m/s", fast, ""


@check("H8", "sizing", "Diameter set by flow, never by the depth wanted", "G203-p29")
def h8(ctx):
    ctx.need("SIZED_BY")
    bad = ctx.pipes.SIZED_BY.astype(str).str.lower().isin(["depth", "cover"])
    n = int(bad.sum())
    allowed = {"capacity", "dod", "velocity", "horizon", "minimum"}
    unknown = int((~ctx.pipes.SIZED_BY.astype(str).str.lower().isin(allowed | {"depth", "cover"})).sum())
    if n == 0 and unknown == 0:
        return PASS, "every diameter attributed to a permitted cause", 0, ""
    return FAIL, f"{n} sized by depth, {unknown} with an unrecognised cause", n + unknown, ""


@check("H9", "sizing", "Minimum sizes and materials by tier", "G203-p22 T6")
def h9(ctx):
    ctx.need("TIER", "DN")
    # Keys normalised: the layer may hold "sub main", "sub_main" or "SubMain", and a
    # dict.get() miss returned None, which silently skipped the pipe. A check that quietly
    # passes what it cannot classify is worse than one that fails.
    floor = {"lateral": 200, "main": 200, "submain": 200, "trunkmain": 200, "rider": 160}
    def norm(t):
        return "".join(ch for ch in str(t).lower() if ch.isalpha())
    bad, unknown = 0, 0
    for _, r in ctx.pipes.iterrows():
        f = floor.get(norm(r.TIER))
        if f is None:
            unknown += 1
        elif int(r.DN) < f:
            bad += 1
    if unknown:
        return FAIL, f"{unknown} pipes carry a TIER this check cannot classify", unknown, ""
    if bad == 0:
        return PASS, "every pipe at or above its tier minimum", 0, ""
    return FAIL, f"{bad} pipes below the minimum size for their tier", bad, ""


@check("H10", "chambers", "Inlet angle >= 90 degrees", "G203-p30")
def h10(ctx):
    if ctx.nodes is None or "INLET_DEG" not in getattr(ctx.nodes, "columns", []):
        raise KeyError("no node layer with INLET_DEG - inlet angles are not computed")
    bad = ctx.nodes.INLET_DEG < 90.0 - 1e-6
    n = int(bad.sum())
    flagged = "INLET_FLAG" in ctx.nodes.columns
    if n == 0:
        return PASS, "every inlet at 90 degrees or better", 0, ""
    if not flagged:
        return FAIL, f"{n} inlets below 90 degrees and no flag field", n, ""
    return FAIL, f"{n} inlets below 90 degrees (flagged: {int(ctx.nodes.INLET_FLAG.sum())})", n, ""


@check("H11", "levels", "No reverse gradient; laying tolerance 20 mm", "G203-p29")
def h11(ctx):
    ctx.need("INV_UP", "INV_DN")
    fall = ctx.pipes.INV_UP - ctx.pipes.INV_DN
    bad = fall < 0.020
    n = int(bad.sum())
    if n == 0:
        return PASS, "every reach falls by more than the 20 mm tolerance", 0, ""
    return FAIL, f"{n} reaches with less than 20 mm of fall", n, ""


@check("H12", "chambers", "Chamber spacing within Table 12", "G203-p30")
def h12(ctx):
    ctx.need("DN", "LEN_M")
    sp = getattr(ctx.crit, "mh_max_spacing", None)
    if sp is None:
        raise KeyError("criteria has no mh_max_spacing")
    lim = ctx.pipes.DN.map(lambda d: sp(int(d)))
    bad = ctx.pipes.LEN_M > lim + 1e-6
    n = int(bad.sum())
    if n == 0:
        return PASS, "every reach within its Table 12 spacing", 0, ""
    return FAIL, (f"{n} reaches exceed Table 12 spacing, longest "
                  f"{ctx.pipes.LEN_M.max():.0f} m"), n, f"{km(bad, ctx):.1f} km"


@check("H13", "levels", "Uniform slope between successive manholes", "G203-p29")
def h13(ctx):
    if "SLOPE_LAID" not in ctx.pipes.columns:
        raise KeyError("no SLOPE_LAID - cannot verify slope uniformity within a reach")
    return PASS, "one gradient per reach by construction", 0, ""


@check("H14", "levels", "An existing structure's invert is fixed; tie in soffit to soffit",
       "practice")
def h14(ctx):
    if ctx.existing is None:
        raise KeyError("no existing-network layer supplied")
    if "TIE_TYPE" not in ctx.pipes.columns:
        raise KeyError("pipe layer has no TIE_TYPE - connections to the existing network "
                       "are not recorded")
    bad = int((ctx.pipes.TIE_TYPE.astype(str).str.lower() == "invert").sum())
    if bad == 0:
        return PASS, "every tie-in is soffit to soffit", 0, ""
    return FAIL, f"{bad} tie-ins made invert to invert", bad, ""


@check("H15", "topology",
       "The network is a FOREST - zero loops, and every component reaches exactly one outfall",
       "project rule")
def h15(ctx):
    """Zero loops, but NOT necessarily one component.

    The first version of this check demanded a single connected component, which would have
    failed any compliant design: philosophy 8a explicitly contemplates satellite works and
    on-site systems for outlying settlements, and the TOR requires every plot served without
    requiring one network. The forest property is what matters - no loops, and each tree
    draining to exactly one outfall. An isolated piece with NO outfall is still a failure.
    """
    G = ctx.graph()
    parts = nx.number_connected_components(G)
    cycles = G.number_of_edges() - G.number_of_nodes() + parts

    # Report the failure that matters first. A layer in thousands of disconnected pieces is
    # loop-free BY ACCIDENT, and leading with "loop-free" reads like a pass. Measured on
    # W10: 7,919 pieces and 0 cycles at 0.01 m, but 105 pieces and 311 cycles at 2.5 m -
    # the same layer, squeezed harder. The loops were never in the design; they appear the
    # moment you snap hard enough to hide the disconnection. Both are one root cause, and
    # G3 names it: no US_NODE/DS_NODE, so connectivity is inferred from a tolerance.
    # An outfall is a property of a CHAMBER, not of a pipe. This check read
    # ctx.pipes.IS_OUTFALL, stage 4 writes it on the node layer, and contract.py declared it
    # on neither - so a design with exactly one outfall per component returned
    # "no IS_OUTFALL to prove any piece drains", a BLOCKING false failure. Read the nodes.
    have_ids = {"US_NODE", "DS_NODE"} <= set(ctx.pipes.columns)
    nodes_ok = (ctx.nodes is not None and "IS_OUTFALL" in getattr(ctx.nodes, "columns", [])
                and "NODE_UID" in getattr(ctx.nodes, "columns", []))

    if cycles:
        return FAIL, f"{cycles} independent cycles across {parts} component(s)", cycles, ""
    if not nodes_ok:
        return FAIL, (f"loop-free in {parts:,} piece(s), but no node layer carrying "
                      f"IS_OUTFALL - nothing proves any piece drains"), parts, ""
    if not have_ids:
        return FAIL, (f"loop-free in {parts:,} piece(s), but no US_NODE/DS_NODE - an outfall "
                      f"cannot be attributed to a component (see H16)"), parts, ""

    # Components on the DECLARED graph, which is what the outfall ids can be joined to.
    D = nx.Graph()
    D.add_edges_from(zip(ctx.pipes.US_NODE.astype(str), ctx.pipes.DS_NODE.astype(str)))
    comp_of = {}
    for i, cc in enumerate(nx.connected_components(D)):
        for u in cc:
            comp_of[u] = i
    n_comp = max(comp_of.values()) + 1 if comp_of else 0

    outs = ctx.nodes.loc[ctx.nodes.IS_OUTFALL.astype(float).fillna(0) > 0, "NODE_UID"].astype(str)
    per = {}
    for u in outs:
        if u in comp_of:
            per[comp_of[u]] = per.get(comp_of[u], 0) + 1
    none_ = [i for i in range(n_comp) if per.get(i, 0) == 0]
    many = [i for i in range(n_comp) if per.get(i, 0) > 1]
    if none_ or many:
        return FAIL, (f"{len(none_):,} component(s) drain NOWHERE and {len(many):,} carry "
                      f"more than one outfall, of {n_comp:,}"), len(none_) + len(many), ""
    return PASS, (f"loop-free forest, {n_comp:,} component(s), exactly one outfall each "
                  f"({len(outs):,} outfalls)"), 0, ""


# --------------------------------------------------------------------------- regression

@check("R1", "regression", "No surcharged pipe (W10 shipped 2.80 km)", "W10 post-mortem")
def r1(ctx):
    return h2(ctx)


@check("R2", "regression", "No reach below minimum cover (W10 shipped 45.92 km)",
       "W10 post-mortem")
def r2(ctx):
    return h3(ctx)


@check("R3", "regression", "No pipe along a dual carriageway (W10 shipped 1.67 km)",
       "W10 post-mortem")
def r3(ctx):
    return h1(ctx)


def _scheduled_as_wadi(ctx, i) -> bool:
    """Is reach `i` actually SCHEDULED as a wadi crossing?

    The first version accepted any non-blank CROSS_ID. That is not scheduling, it is a
    pointer, and on one publish FOUR reaches carrying a DUAL-CARRIAGEWAY crossing id were
    scored as legal wadi crossings on a coincidence of field names - with nothing in the
    register mentioning a wadi at all. H1a item 4 requires the crossing to be IN the
    schedule, because the schedule is what carries the G201 9.3 obligations: bed profile,
    1:20/1:50/1:100 flood levels, bed material and MoAFWR approval. An id with no row
    behind it carries none of them.
    """
    if "CROSS_ID" not in ctx.pipes.columns:
        return False
    cid = str(ctx.pipes.CROSS_ID.iloc[i])
    if cid in ("", "nan", "None", "0"):
        return False
    reg = ctx.crossings
    if reg is None or "CROSS_ID" not in getattr(reg, "columns", []):
        return False          # no register: nothing is scheduled, however many ids exist
    rows = reg[reg.CROSS_ID.astype(str) == cid]
    if "OBSTACLE" in reg.columns:
        rows = rows[rows.OBSTACLE.astype(str).str.lower() == "wadi"]
    return len(rows) > 0


def _wadi_classes(ctx):
    """The hazard classes that mean 'wadi', from criteria - not hardcoded in two places."""
    crit = getattr(ctx, "crit", None)
    cl = getattr(crit, "HAZARD_WADI_CLASSES", None) if crit is not None else None
    return tuple(cl) if cl else (4, 5, 6)


def _r4_classify(ctx):
    """One walk over the geometry. Returns (along, unscheduled, scheduled_ok, n_samples,
    n_nodata, n_reaches_entirely_nodata).

    Split out so `r4` (which reports) and `r4_failing_mask` (which names the rows a stage
    must remove) cannot diverge. They diverged before: s2 carried its own sampler, and 44
    corridors of 25,166 were legal to the stage and illegal to the auditor.
    """
    if ctx.hazard is None:
        raise KeyError("no hazard grid")
    import rasterio
    from shapely.geometry import Point

    with rasterio.open(ctx.hazard) as src:
        # The grid's declared nodata is -9999.0, and np.isfinite(-9999) is True. Testing
        # finiteness alone counted every nodata cell as TESTED and scored it not-a-wadi,
        # which is how this check first reported "0 % untested" over a grid that is largely
        # fill. Read the declared nodata and honour it.
        ND = src.nodata

        lo = min(_wadi_classes(ctx))

        def onwadi(pts):
            """(is_wadi, is_known). Nodata is neither on nor off - it is unknown."""
            v = np.array([w[0] for w in src.sample(pts)], dtype=float)
            known = np.isfinite(v)
            if ND is not None:
                known &= (v != ND)
            return (known & (np.floor(v) >= lo)), known

        along, xing_ok, xing_bad, no_data_reach = [], [], [], 0
        unknown = []       # touches a wadi, far bank outside the grid
        # index -> (contact_m, band_width_m, banks_found). The MEASUREMENT, so a
        # stage publishing a crossings register can carry the real skew instead of
        # declaring one. s5c wrote ANGLE_DEG = 90.0 on all 3,290 rows; stage 3, on
        # the same geometry, measures a minimum of 0.84 deg with 7 of 91 below 45.
        geom = {}
        n_samp = n_nodata = 0
        for i, g in enumerate(ctx.pipes.geometry):
            if g is None or g.is_empty:
                continue
            L = g.length
            n = max(2, int(L / WADI_SAMPLE_M) + 1)
            ds = np.linspace(0, L, n)
            pts = [(p.x, p.y) for p in (g.interpolate(d) for d in ds)]
            on, known = onwadi(pts)
            n_samp += known.size; n_nodata += int((~known).sum())
            if not known.any():
                no_data_reach += 1
                continue
            if not on.any():
                continue

            # contiguous on-wadi runs
            runs, a = [], None
            for k, flag in enumerate(on):
                if flag and a is None:
                    a = k
                elif not flag and a is not None:
                    runs.append((a, k - 1)); a = None
            if a is not None:
                runs.append((a, len(on) - 1))

            if len(runs) > 1:
                along.append(i); continue          # more than one contact is not one crossing

            a, b = runs[0]
            contact = float(ds[b] - ds[a]) + WADI_SAMPLE_M
            mid = 0.5 * (ds[a] + ds[b])
            p0 = g.interpolate(max(0.0, mid - 1.0)); p1 = g.interpolate(min(L, mid + 1.0))
            vx, vy = p1.x - p0.x, p1.y - p0.y
            m = (vx * vx + vy * vy) ** 0.5 or 1.0
            nx_, ny_ = -vy / m, vx / m             # unit normal to the pipe
            c = g.interpolate(mid)

            # Probe both ways along the normal until KNOWN DRY ground is found.
            #
            # This is where the nodata defect walked back in after being cured at the
            # sampler. `off` needs a cell that is both KNOWN and NOT wadi; across the 53 %
            # of the grid that is nodata no such cell exists, so the probe ran to its 400 m
            # cap and the cap was ADDED TO THE WIDTH as though a bank had been found. Both
            # sides capped gives a width of 800 m, and contact <= 1.155 x 800 = 924 m passes
            # essentially any contact. Measured independently by distance transform: 546
            # corridors, 47.40 km, run ALONG a wadi that this check scored as square
            # crossings - roughly five times the exposure it was reporting. Worst case was
            # 150 m of continuous contact in a channel 8.5 m wide, skew 17.7.
            #
            # An unfound bank is an UNKNOWN width, never a wide one. Where the width cannot
            # be established the reach is UNTESTABLE, and philosophy sec 8 makes that a
            # failure rather than a pass.
            width, banks = 0.0, 0
            for sgn in (1.0, -1.0):
                probe = [(c.x + sgn * t * nx_, c.y + sgn * t * ny_)
                         for t in np.arange(0.0, WADI_PROBE_M, WADI_SAMPLE_M)]
                pon, pknown = onwadi(probe)
                off = np.where(pknown & ~pon)[0]
                if len(off):
                    width += float(off[0] * WADI_SAMPLE_M)
                    banks += 1
                else:
                    width += WADI_PROBE_M

            geom[i] = (contact, width, banks)
            if banks < 2:
                unknown.append(i)
                continue

            square = contact <= WADI_XING_SKEW * max(width, WADI_SAMPLE_M)
            has_id = _scheduled_as_wadi(ctx, i)
            if square and has_id:
                xing_ok.append(i)
            elif square:
                xing_bad.append(i)                 # geometrically a crossing, not scheduled
            else:
                along.append(i)

    # Coverage is reported at SAMPLE level, not reach level. A reach with one cell of grid
    # under it and the rest nodata was passing the reach-level test and hiding the gap; the
    # 50-year grid does not cover the study area and every wadi result must say so.
    return along, xing_bad, xing_ok, n_samp, n_nodata, no_data_reach, unknown, geom


def wadi_crossing_geometry(ctx):
    """{reach index: (contact_m, band_width_m, banks_found)} for every reach touching a wadi.

    Exists so a stage publishing the crossings register carries the MEASURED skew. s5c wrote
    ANGLE_DEG = 90.0 on all 3,290 rows and called it a declaration; on the same geometry
    stage 3 measures a minimum of 0.84 degrees, with 7 of 91 below 45 - including a 150 m
    "crossing" at 0.84 deg, which is a pipe running down the road. A constant in a published
    register is not a declaration, it is a fabricated measurement.
    """
    return _r4_classify(ctx)[7]


def r4_failing_mask(ctx):
    """Boolean mask of the rows R4 rejects - WHICH, not HOW MANY."""
    along, xing_bad, _ok, _s, _n, _r, unk, _g = _r4_classify(ctx)
    m = np.zeros(len(ctx.pipes), bool)
    bad = along + xing_bad + unk
    if bad:
        m[np.array(bad, dtype=int)] = True
    return m


@check("R4", "regression",
       "No pipe ALONG a wadi. A crossing is legal only under H1a (W10 shipped 131.7 km)",
       "philosophy H1a / G203-p30 4.4.1, p33 / G201-p85-86")
def r4(ctx):
    """Along, not across - and say what fraction of the area was never tested.

    Three defects in the first version, all of them mine:

    1. It sampled the MIDPOINT ONLY, so a reach could run 200 m down a wadi and pass
       because its centre happened to fall clear.
    2. Nodata scored as a PASS, silently - and the grid's nodata is -9999.0, which is
       finite, so even the finiteness guard let it through. The 50-year grid covers under
       half the study area, so "no pipe on wadi ground" was a statement about the tested
       part being read as a statement about all of it.
    3. It had no exemption for a crossing, though H1 itself says crossings are legal and
       G201 9.3 gives the procedure. Applied literally it cut the corridor network into
       1,381 pieces - a prohibition on presence read as a prohibition on passage.

    The along/across test is geometric, not a length threshold: at the middle of each
    on-wadi run, probe PERPENDICULAR to the pipe until both banks are found. A pipe
    crossing a band square has a contact no longer than the band is wide across it; a pipe
    running down a band has a long contact and a narrow perpendicular extent. The ratio is
    the measurement, and WADI_XING_SKEW is the stated tolerance on the word "perpendicular".
    """
    res4 = _r4_classify(ctx)
    along, xing_bad, xing_ok, n_samp, n_nodata, no_data_reach, unknown, _g = res4

    # Coverage is reported at SAMPLE level. A reach with one cell of grid under it and the
    # rest nodata passed a reach-level test and hid the gap.
    cover = ""
    if n_nodata:
        cover = (f"; {100.0 * n_nodata / max(n_samp, 1):.0f} % of samples fall outside the "
                 f"hazard grid and are UNTESTED ({no_data_reach:,} reaches entirely so)")
    if along or unknown:
        m = np.zeros(len(ctx.pipes), bool)
        m[np.array(along + unknown, dtype=int)] = True
        extra = f", {len(xing_bad):,} cross one without a scheduled CROSS_ID" if xing_bad else ""
        unk = ""
        if unknown:
            unk = (f", and {len(unknown):,} touch a wadi whose far bank lies outside the "
                   f"grid, so along-or-across CANNOT BE DECIDED")
        msg = f"{len(along):,} reaches run ALONG a wadi{extra}{unk}{cover}"
        return FAIL, msg, len(along) + len(unknown), f"{km(m, ctx):.1f} km"
    if xing_bad:
        m = np.zeros(len(ctx.pipes), bool); m[np.array(xing_bad, dtype=int)] = True
        return FAIL, (f"{len(xing_bad):,} wadi crossings with no CROSS_ID - H1a(4) requires "
                      f"each in the crossings schedule{cover}"), len(xing_bad), f"{km(m, ctx):.1f} km"
    return PASS, f"nothing along a wadi; {len(xing_ok):,} scheduled crossing(s){cover}", 0, ""


# --------------------------------------------------------------------------- provenance

@check("G1", "provenance", "The laid gradient is published, with the minimum beside it",
       "philosophy 5")
def g1(ctx):
    have = [c for c in ("SLOPE_LAID", "SLOPE_MIN") if c in ctx.pipes.columns]
    if len(have) == 2:
        return PASS, "both gradients published", 0, ""
    return FAIL, ("only the minimum gradient is published, so nothing about velocity, "
                  "fall or drop can be checked"), 0, ""


@check("G2", "provenance", "Every reach records what set its diameter and its gradient",
       "philosophy 3")
def g2(ctx):
    missing = [c for c in ("SIZED_BY", "GRAD_BY") if c not in ctx.pipes.columns]
    if not missing:
        return PASS, "constraint provenance present on every reach", 0, ""
    return FAIL, "missing " + ", ".join(missing), 0, ""


@check("H16", "topology",
       "Every pipe publishes US_NODE/DS_NODE, and the declared graph MATCHES the geometry",
       "philosophy 3.6a / H16")
def h16(ctx):
    """Topology is written down, not inferred - and the two must agree.

    The weak version of this check only asked whether the fields exist. That is not the
    failure worth catching. The failure worth catching is a layer that DECLARES a connected
    network and DRAWS a disconnected one: both halves look fine alone, and the declared
    graph is what a modeller imports while the drawn geometry is what a contractor sets out.
    """
    missing = [c for c in ("US_NODE", "DS_NODE") if c not in ctx.pipes.columns]
    if missing:
        return FAIL, ("no " + "/".join(missing) + " - topology can only be guessed from a "
                      "tolerance, and the guess moves with it (see H15)"), 0, ""
    D = nx.Graph()
    D.add_edges_from(zip(ctx.pipes.US_NODE.astype(str), ctx.pipes.DS_NODE.astype(str)))
    dc = nx.number_connected_components(D)
    gc = nx.number_connected_components(ctx.graph())
    if dc != gc:
        return FAIL, (f"declared topology has {dc:,} component(s), the drawn geometry has "
                      f"{gc:,} at {SNAP_M} m - the layer says one thing and draws another"), abs(dc - gc), ""
    self_j = int((ctx.pipes.US_NODE.astype(str) == ctx.pipes.DS_NODE.astype(str)).sum())
    if self_j:
        return FAIL, f"{self_j} pipes start and end at the same node", self_j, ""
    return PASS, f"declared and drawn topology agree: {dc:,} component(s)", 0, ""


# --------------------------------------------------------------------------- runner

def run_one(check_id: str, ctx):
    """Run ONE registered check and return its raw (status, summary, n, extent).

    Exists so a stage can gate itself on the auditor's ACTUAL arithmetic instead of a
    copy of it. s2 carried a hand-lifted copy of h1 and r4; when r4 gained the H1a
    along/across test the copy stayed on the superseded midpoint rule and rejected every
    legal crossing the stage had just kept. One function, one answer (philosophy P2).
    """
    for c in REGISTRY:
        if c.id == check_id:
            return c.fn(ctx)
    raise KeyError(f"no check {check_id!r}")


def run(ctx) -> List[Result]:
    out = []
    for c in REGISTRY:
        try:
            status, summary, n_bad, extent = c.fn(ctx)
        except Exception as e:
            status, summary, n_bad, extent = NOT_CHECKABLE, f"{e}", 0, ""
        out.append(Result(c.id, c.group, c.requirement, c.source, c.blocking,
                          status, summary, n_bad, extent))
    # Report in ID order, not the order the checks happen to be defined in. A reader looking
    # for H16 should find it next to H15, not at the bottom because it was written last.
    order = {"H": 0, "R": 1, "G": 2}
    return sorted(out, key=lambda r: (order.get(r.id[0], 9), int(r.id[1:])))


def report(results: List[Result]) -> str:
    w = max(len(r.summary) for r in results)
    lines = [f"{'id':<5}{'group':<12}{'status':<15}summary",
             "-" * (32 + min(w, 90))]
    for r in results:
        mark = {"PASS": "ok  ", "FAIL": "FAIL", "NOT_CHECKABLE": "CANT"}[r.status]
        lines.append(f"{r.id:<5}{r.group:<12}{mark:<15}{r.summary}"
                     + (f"  [{r.extent}]" if r.extent else ""))
    f = sum(1 for r in results if r.status == FAIL)
    n = sum(1 for r in results if r.status == NOT_CHECKABLE)
    p = sum(1 for r in results if r.status == PASS)
    lines += ["", f"{p} pass, {f} FAIL, {n} cannot run.",
              "A check that cannot run is a failure, not a blank (philosophy 8)."]
    return "\n".join(lines)
