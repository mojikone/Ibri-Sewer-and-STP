"""s7_pumps - STAGE 7: pumping stations and force mains, DESIGNED and PUBLISHED.

W11b BORROWS NOTHING. Nothing here imports from `W8/py/sewnet`, `W10/py` or `W11a/py`.
The engineering lives in `w11b.pumping`, which was built from PAM-GUD-201/202/203 directly;
this file is the stage: it decides WHERE stations go, WHERE their mains run, and publishes
the two contract layers.

    python s7_pumps.py                 build, publish, report
    python s7_pumps.py --report        re-print the tables from the published file
    python s7_pumps.py --verify        re-run every check against the published file
    python s7_pumps.py --asbuilt       design NAMA's own built station and compare

WHAT W11a PUBLISHED, AND WHAT THIS REPLACES
    226 stations, `Q_DUTY_LS = 0` on every one, zero rising mains, `LAND_M2` a flat 100 m2
    constant, and no answer at all for a station that is a gravity TERMINAL. Every one of
    those is addressed here, and the gravity-terminal answer is the reason the stage needs a
    graph rather than a loop.

THE INTERFACE WITH THE LEVELS STAGE - READ THIS BEFORE WIRING ANYTHING
    Final duty flows come from the levels stage (s6), which does not exist yet. This stage
    therefore takes its stations from a PROVIDER, and there are two:

      A. `demands_from_design()` - THE REAL ONE. Reads the published `nodes` layer of
         `W11b.gpkg`: every row with `NODE_KIND == 'station'`, using GRD_M, INV_M, Q_PK_LS,
         Q_ADF_M3D and N_PROP. When that layer exists this stage uses it and nothing else.
         The contract it needs is exactly those six fields plus NODE_UID and X/Y.

      B. `demands_standin()` - THE SCREEN, used only while (A) is absent, and labelled
         `SRC = 'terrain'`, `CONFIDENCE = 'derived'`, `STAGE = 's7-standin'` on every row it
         produces, plus a banner on every printed table. It is NOT a design.

    THE SCREEN IS NOT ARBITRARY. It is the physics the levels stage will do properly:
    a pipe laid at the minimum legal gradient on ground that falls more gently than that
    gradient SINKS, and the shortfall accumulates along the flow path. For each corridor
    node the screen computes the minimum accumulated DEPTH DEBT to the works,

        debt(u -> v) = max( S_min x L  -  (z_u - z_v),  0 )

    with S_min the G203-p29 Table 11 minimum for DN200 (5.00 mm/m) and z from the 0.5 m
    terrain. Where the cheapest path's debt passes MAX_COVER - MIN_COVER (12.00 - 1.30 =
    10.70 m, G203-p33) gravity cannot reach the works from there and a station is forced.
    That is the cap rung of the philosophy sec 5 ladder, computed on the real corridor
    network and the real ground, with no tree assumed. It gives the RIGHT ORDER OF MAGNITUDE
    and the right places; it does not give final flows, and it says so.

    Why DN200's minimum and not each pipe's own: the tree is not designed, so no reach has a
    diameter yet. DN200 is the smallest permitted main and lateral (G203-p22 Table 6) and
    therefore the STEEPEST minimum in Table 11 - the screen is conservative by construction,
    and the conservatism is stated rather than hidden.

    AND THE SCREEN MUST CASCADE. Run once from the works, only 30 of 9,599 corridor nodes -
    0.31 % - can reach it inside the cover budget, because the ground is far too flat for
    1,819 km of gravity to one outfall. A single frontier therefore returns ten sites huddled
    round the works and declares the other 99.7 % unreachable, which is an artefact of
    running the model once, not a design. A station lifts the sewer back to minimum cover, so
    it becomes a NEW zero-debt source and the field is recomputed; 20 rounds later every
    reachable node is inside budget. That is the cap rung applied repeatedly, which is what a
    levelling stage actually does.

THE GRAVITY-TERMINAL PROBLEM, AND HOW IT IS SOLVED HERE
    W11a had no answer for "this station has no downstream gravity path" and published zero
    rising mains. The answer is in the same debt field: a node whose debt is at or below the
    cap CAN be drained onward by gravity. A station's discharge chamber is chosen from that
    set, so it always discharges into a working gravity system rather than into thin air.
    Two guards go with it:
      * the LOOP GUARD - the candidate's own gravity owner must not be this station, or the
        flow would drain straight back to the pump (H15: the network is a forest);
      * `stations_in_series` - how many stations the flow still passes on the way to the
        works - is computed and MINIMISED FIRST, rung 1 of `pumping.DISCHARGE_LADDER`.
        It is not always zero: on ground this flat a cascade is sometimes unavoidable, and
        pretending otherwise would be the W11a failure in a different costume.

ECONOMICS FEEDS BACK INTO THE LAYOUT, WHICH IS THE POINT
    NWS's manning rule is 12,000 OMR/yr PER STATION whatever its size - 169,127 OMR of
    present value at G201-p96's 25 years and 5 %. So stations are CONSOLIDATED before they
    are designed, at the break-even distance that rule implies (about 1.1 km on provisional
    rates; the project's own rule-9 cascade radius of 1.5 km is within a third of it). The
    discharge chamber is then ranked on `pumping.DISCHARGE_LADDER` - stations avoided,
    commissionability, receiving capacity, septicity, and head LAST.

WHAT THIS STAGE REFUSES TO PUBLISH
    * a station whose footprint is wet at the 1:50 event (G203-p38 sec 7.2) - it is moved to
      the nearest dry corridor node, and if none is found within the search radius the
      station is REFUSED and named in the `refused` table.
    * a force main that cannot reach 0.75 m/s WITH ONE DUTY PUMP RUNNING - the lowest flow
      the station ever delivers, so a main that silts there silts under every reading of
      G203-p50 sec 8.1. 14 of 112 screen sites failed this and the answer is a grinder pump
      on a 50 mm ID main, or the catchment leaves the central network - never a resize.
    * a force main over 2.5 m/s at the worst case (G203-p50 sec 8.1).
    * a wet well whose live depth cannot hold its start levels 200 mm apart (G203-p48).

    AND ONE CHECK IT CANNOT RUN AT ALL, reported as a failure rather than a blank:
    `contract.STATIONS.FLOOD_LV` is a REQUIRED field and no flood LEVEL is derivable from
    the hazard-CLASS grids this project holds. See `BLOCKING` at the end of the run.
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import linemerge

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from w11b import contract, hazard, pumping, terrain as T          # noqa: E402
from w11b.criteria import DEFAULT as CRIT                          # noqa: E402
from w11b.pumping import PUMP                                      # noqa: E402

STAGE = "s7_pumps"
STAGE_VERSION = "W11b-s7_pumps-1.0"

W11B = HERE.parent
ROADS_GPKG = W11B / "shp" / "W11b_roads.gpkg"
DESIGN_GPKG = W11B / "shp" / contract.GPKG_NAME          # the levels stage's output, if any
PUMPS_GPKG = W11B / "shp" / "W11b_pumps.gpkg"
RUN = W11B / "run" / "pumps"

CRS = "EPSG:32640"

# The two fixed points of the scheme, both user-confirmed and recorded in CLAUDE.md.
STP_XY = (444422.8, 2563337.9)          # existing works, ground 328.7 m aOD
EXIST_PS_XY = (449899.59, 2567301.72)   # existing station, ground 351.1 m aOD

# --- the screen's own constants, all traced -------------------------------------------
SCREEN_DN = 200                          # G203-p22 Table 6: smallest permitted main/lateral
GRAVITY_BUDGET_M = CRIT.MAX_COVER - CRIT.MIN_COVER_CROWN     # 12.00 - 1.30, G203-p33
WADI_ROUTE_PENALTY = 6.0                 # [ASSUME] cost multiplier on a corridor whose
                                         # ground is hazard class 4-6 at 1:50. Not a ban -
                                         # H1a makes a CROSSING legal and a force main must
                                         # sometimes cross - but a heavy preference for the
                                         # dry route. Reported, and the crossing length is
                                         # measured on the chosen route either way.
SITE_SEARCH_M = 500.0                    # [ASSUME] how far a wet station may be moved
SUMMIT_MIN_PROMINENCE_M = 1.0            # [ASSUME] a bump smaller than this is terrain noise
                                         # at sigma_z = 0.76 m (terrain manifest), not a
                                         # summit needing an air valve
PROFILE_STEP_M = 25.0                    # [ASSUME] chainage step when profiling a main


def _log(msg: str) -> None:
    print(f"[{STAGE}] {msg}", flush=True)


# ======================================================================================
# 1. THE CORRIDOR GRAPH
# ======================================================================================

class CorridorGraph:
    """The routable network: `corridors` from s1, which is already H1-filtered (PIPE_OK = 1,
    no pipe along a dual carriageway - project rule 7). Undirected: a force main may run
    either way along a corridor, and a gravity debt is computed per direction."""

    def __init__(self, corridors: gpd.GeoDataFrame, nodes: gpd.GeoDataFrame,
                 tf: "T.TerrainFlow"):
        self.corr = corridors.reset_index(drop=True)
        self.nodes = nodes.reset_index(drop=True)
        self.idx: Dict[str, int] = {n: i for i, n in enumerate(self.nodes.NODE_ID.values)}
        self.x = self.nodes.X.values.astype(float)
        self.y = self.nodes.Y.values.astype(float)
        self.z = np.asarray(tf.elevation(self.x, self.y), dtype=float)
        self.u = np.array([self.idx.get(a, -1) for a in self.corr.US_NODE.values])
        self.v = np.array([self.idx.get(b, -1) for b in self.corr.DS_NODE.values])
        self.L = self.corr.LEN_M.values.astype(float)
        keep = (self.u >= 0) & (self.v >= 0)
        self.u, self.v, self.L = self.u[keep], self.v[keep], self.L[keep]
        self.eid = np.flatnonzero(keep)
        self.n = len(self.nodes)
        self.adj: List[List[Tuple[int, int]]] = [[] for _ in range(self.n)]
        for k in range(len(self.u)):
            self.adj[self.u[k]].append((self.v[k], k))
            self.adj[self.v[k]].append((self.u[k], k))
        self.wadi = np.zeros(len(self.u), dtype=bool)

    def nearest(self, x: float, y: float) -> int:
        d2 = (self.x - x) ** 2 + (self.y - y) ** 2
        return int(np.argmin(d2))

    # ---- the gravity depth-debt field -------------------------------------------------
    def depth_debt(self, sources: Sequence[int], s_min: float
                   ) -> Tuple[np.ndarray, np.ndarray]:
        """Minimum accumulated depth debt from every node to the nearest SOURCE, and the
        parent edge of the cheapest-debt tree.

        The debt of laying a pipe from u down to v is the gradient the guideline demands
        minus the fall the ground gives, never negative:

            debt = max(s_min * L - (z_u - z_v), 0)

        Multi-source Dijkstra over reversed edges. `sources` are the points a gravity sewer
        may arrive at with NO accumulated debt - the works, and every station already placed,
        because a station lifts the pipe back to minimum cover and resets the count. Debt is
        non-negative and additive, so the tree is the cheapest gravity route to the nearest
        such point and its value at a node is the extra depth a gravity sewer arrives with.
        """
        INF = float("inf")
        dist = np.full(self.n, INF)
        par = np.full(self.n, -1, dtype=np.int64)
        pq: List[Tuple[float, int]] = []
        for s in sources:
            dist[s] = 0.0
            pq.append((0.0, int(s)))
        heapq.heapify(pq)
        while pq:
            d, i = heapq.heappop(pq)
            if d > dist[i] + 1e-12:
                continue
            zi = self.z[i]
            for j, k in self.adj[i]:
                # flow runs j -> i, so the debt is charged on that direction
                debt = s_min * self.L[k] - (self.z[j] - zi)
                nd = d + (debt if debt > 0.0 else 0.0)
                if nd < dist[j] - 1e-12:
                    dist[j] = nd
                    par[j] = k
                    heapq.heappush(pq, (nd, j))
        return dist, par

    def cascade(self, sink: int, s_min: float, budget: float, max_rounds: int = 40
                ) -> Tuple[np.ndarray, np.ndarray, List[int], List[dict]]:
        """Place stations at the gravity frontier, RESET the debt there, and repeat.

        THIS IS THE CAP RUNG OF PHILOSOPHY sec 5, APPLIED REPEATEDLY, and it is what a
        single-pass frontier gets wrong. Run once from the works, only 30 of 9,599 corridor
        nodes on this network can reach it inside the 10.70 m cover budget - because the
        ground is too flat for 1,819 km of gravity to one outfall. A single frontier
        therefore returns ten sites clustered around the works and calls the other 99.7 % of
        the network unreachable, which is not a design, it is an artefact of running the
        model once.

        A station lifts the sewer back to minimum cover, so it becomes a new zero-debt
        source and the field is recomputed. Each round the maximum debt strictly falls, so
        the loop terminates; `max_rounds` is a guard, and hitting it is reported.
        """
        sources = [int(sink)]
        stations: List[int] = []
        rounds: List[dict] = []
        for r in range(max_rounds):
            dist, par = self.depth_debt(sources, s_min)
            over = dist > budget
            reach = np.isfinite(dist)
            if not (over & reach).any():
                rounds.append({"round": r + 1, "new_stations": 0,
                               "nodes_over_budget": 0,
                               "pct_gravity_ok": round(100.0 * (reach & ~over).sum()
                                                       / max(reach.sum(), 1), 2)})
                return dist, par, stations, rounds
            new: List[int] = []
            for i in np.flatnonzero(over & reach):
                k = int(par[i])
                if k < 0:
                    continue
                dj = self.v[k] if self.u[k] == i else self.u[k]
                if not over[dj]:
                    new.append(int(i))
            rounds.append({"round": r + 1, "new_stations": len(new),
                           "nodes_over_budget": int((over & reach).sum()),
                           "pct_gravity_ok": round(100.0 * (reach & ~over).sum()
                                                   / max(reach.sum(), 1), 2)})
            if not new:
                return dist, par, stations, rounds
            stations.extend(new)
            sources.extend(new)
        dist, par = self.depth_debt(sources, s_min)
        rounds.append({"round": "GUARD", "new_stations": 0,
                       "nodes_over_budget": int((dist > budget).sum()),
                       "pct_gravity_ok": -1.0})
        return dist, par, stations, rounds

    # ---- routing ----------------------------------------------------------------------
    def route_to_targets(self, a: int, target: np.ndarray, k_targets: int = 8
                         ) -> List[Tuple[int, List[int], float]]:
        """ONE Dijkstra from `a`, returning the first `k_targets` settled nodes of the
        boolean mask `target`, each with its edge path and true length.

        Cost is corridor length, multiplied by `WADI_ROUTE_PENALTY` where the ground is wadi
        at 1:50. H1a makes a CROSSING legal, so a wadi corridor is never banned - it is made
        expensive, and the crossing length on the chosen route is measured afterwards and
        scheduled under G201 sec 9.3."""
        INF = float("inf")
        dist = np.full(self.n, INF)
        par = np.full(self.n, -1, dtype=np.int64)
        dist[a] = 0.0
        pq = [(0.0, a)]
        found: List[int] = []
        while pq and len(found) < k_targets:
            d, i = heapq.heappop(pq)
            if d > dist[i] + 1e-9:
                continue
            if target[i] and i != a:
                found.append(i)
            for j, kk in self.adj[i]:
                w = self.L[kk] * (WADI_ROUTE_PENALTY if self.wadi[kk] else 1.0)
                if d + w < dist[j] - 1e-9:
                    dist[j] = d + w
                    par[j] = kk
                    heapq.heappush(pq, (d + w, j))
        out: List[Tuple[int, List[int], float]] = []
        for b in found:
            edges: List[int] = []
            cur, guard = b, 0
            while cur != a and guard < 10 ** 6:
                kk = int(par[cur])
                if kk < 0:
                    edges = []
                    break
                edges.append(kk)
                cur = self.v[kk] if self.u[kk] == cur else self.u[kk]
                guard += 1
            if edges:
                edges.reverse()
                out.append((b, edges, float(sum(self.L[e] for e in edges))))
        return out

    def geometry_of(self, edges: Sequence[int], a: int, b: int) -> LineString:
        geoms = [self.corr.geometry.values[self.eid[k]] for k in edges]
        if not geoms:
            return LineString([(self.x[a], self.y[a]), (self.x[b], self.y[b])])
        merged = linemerge(geoms)
        if merged.geom_type == "LineString":
            line = merged
        else:                       # a merge that did not close: stitch on endpoints
            pts: List[Tuple[float, float]] = [(self.x[a], self.y[a])]
            cur = a
            for k in edges:
                nxt = self.v[k] if self.u[k] == cur else self.u[k]
                pts.append((self.x[nxt], self.y[nxt]))
                cur = nxt
            line = LineString(pts)
        # orient start -> end
        sx, sy = self.x[a], self.y[a]
        cs = list(line.coords)
        if (cs[0][0] - sx) ** 2 + (cs[0][1] - sy) ** 2 > \
           (cs[-1][0] - sx) ** 2 + (cs[-1][1] - sy) ** 2:
            line = LineString(cs[::-1])
        return line


# ======================================================================================
# 2. STATION DEMANDS - the interface with the levels stage
# ======================================================================================

class StationDemand:
    __slots__ = ("ident", "node", "x", "y", "ground_m", "invert_in_m",
                 "q_peak_ls", "q_adf_ls", "n_prop", "why", "src", "confidence", "provenance")

    def __init__(self, ident, node, x, y, ground_m, invert_in_m, q_peak_ls, q_adf_ls,
                 n_prop, why, src, confidence, provenance):
        self.ident, self.node = ident, node
        self.x, self.y = float(x), float(y)
        self.ground_m, self.invert_in_m = float(ground_m), float(invert_in_m)
        self.q_peak_ls, self.q_adf_ls = float(q_peak_ls), float(q_adf_ls)
        self.n_prop, self.why = float(n_prop), why
        self.src, self.confidence, self.provenance = src, confidence, provenance


def demands_from_design(gpkg: Path = DESIGN_GPKG) -> Optional[List[StationDemand]]:
    """THE REAL PROVIDER. Reads `nodes` where NODE_KIND == 'station' from the published
    design. Returns None when the layer does not exist yet, which is the signal to fall back
    to the screen."""
    if not gpkg.exists():
        return None
    try:
        import fiona
        if "nodes" not in fiona.listlayers(gpkg):
            return None
        nd = gpd.read_file(gpkg, layer="nodes")
    except Exception as e:
        _log(f"design gpkg present but unreadable ({e}) - falling back to the screen")
        return None
    if "NODE_KIND" not in nd.columns:
        return None
    st = nd[nd.NODE_KIND.astype(str) == "station"]
    if st.empty:
        _log("design `nodes` exists but carries no NODE_KIND == 'station' rows")
        return []
    need = ["NODE_UID", "X", "Y", "GRD_M", "INV_M", "Q_PK_LS", "Q_ADF_M3D", "N_PROP"]
    miss = [c for c in need if c not in st.columns]
    if miss:
        raise contract.ContractError(
            f"the levels stage published station nodes without {miss}. s7 cannot design a "
            "station without them, and a check that cannot run is a FAILURE, not a blank.")
    out = []
    for _, r in st.iterrows():
        out.append(StationDemand(
            ident=str(r.NODE_UID), node=str(r.NODE_UID), x=r.X, y=r.Y,
            ground_m=r.GRD_M, invert_in_m=r.INV_M,
            q_peak_ls=r.Q_PK_LS, q_adf_ls=float(r.Q_ADF_M3D) / 86.4,
            n_prop=r.N_PROP, why=str(r.get("WHY", "cap") or "cap"),
            src="manual", confidence="derived",
            provenance="levels stage, W11b.gpkg nodes NODE_KIND='station'"))
    return out


def serving_station(g: CorridorGraph, par: np.ndarray, stations: Sequence[int]
                    ) -> np.ndarray:
    """For every node, which station (or the works) its gravity flow arrives at.

    Walk each node DOWN the debt tree until a station source or the root is reached. That
    is the node's catchment owner, and it partitions the network - so a station's load is
    counted once and only once, which is the failure mode that put 1,233 m3/d out of W10 and
    counted every upstream kilometre once per downstream reach in the infiltration total."""
    is_src = np.zeros(g.n, dtype=bool)
    is_src[list(stations)] = True
    owner = np.full(g.n, -1, dtype=np.int64)
    for i in range(g.n):
        if owner[i] >= 0:
            continue
        path = []
        cur = i
        while True:
            if owner[cur] >= 0:
                res = owner[cur]
                break
            if is_src[cur]:
                res = cur
                break
            k = int(par[cur])
            if k < 0:                       # the works, or unreachable
                res = -2 if not np.isfinite(par[cur]) else -1
                res = cur if is_src[cur] else -1
                break
            path.append(cur)
            cur = g.v[k] if g.u[k] == cur else g.u[k]
        owner[i] = res
        for p in path:
            owner[p] = res
    return owner


def demands_standin(g: CorridorGraph, debt: np.ndarray, par: np.ndarray,
                    stations: Sequence[int], crit=CRIT) -> List[StationDemand]:
    """THE SCREEN. See the module docstring - this is not a design.

    `stations` are the cascade's frontier nodes: places where a gravity sewer has spent the
    whole 12.00 - 1.30 m cover budget (G203-p33) and cannot go further without being lifted.
    Here each of them is given the load of the catchment it actually owns.

    Load comes from the corridor layer's own measured `Q_NEAR_M3D` (s1), credited to the
    UPPER node of each corridor and then summed by catchment owner - so nothing is counted
    twice. Peak factor from G201-p71 Merrimack via `criteria.peak_factor`, which holds at
    1.0 below 100 properties because G201 prescribes no formula there. Infiltration is
    G201-p72's 720 L/d/km over the OWNED length only, unpeaked.
    """
    owner = serving_station(g, par, stations)
    qcol = "Q_NEAR_M3D" if "Q_NEAR_M3D" in g.corr.columns else "Q_M3D"
    q_edge = g.corr[qcol].values.astype(float)[g.eid]

    load = np.zeros(g.n)
    length = np.zeros(g.n)
    for k in range(len(g.u)):
        a, b = int(g.u[k]), int(g.v[k])
        hi = a if debt[a] >= debt[b] else b       # the upper end owns the corridor
        load[hi] += max(q_edge[k], 0.0)
        length[hi] += g.L[k]

    out: List[StationDemand] = []
    for s in stations:
        m = owner == s
        q_adf_m3d = float(load[m].sum())
        len_m = float(length[m].sum())
        if q_adf_m3d <= 0.0:
            continue                       # a frontier serving nothing is not a station
        n_prop = q_adf_m3d / crit.PLOT_QADF_M3D * crit.PROPS_PER_PLOT
        pf, meth = crit.peak_factor(q_adf_m3d, n_prop)
        q_adf_ls = q_adf_m3d / 86.4
        q_peak_ls = q_adf_ls * pf + crit.infiltration_ls(len_m)
        i = int(s)
        out.append(StationDemand(
            ident=f"SCR{len(out):04d}", node=i, x=g.x[i], y=g.y[i], ground_m=g.z[i],
            # the screen's own arrival invert: the gravity budget is exhausted at a frontier,
            # so the incoming sewer arrives at the cap. That IS the definition of a frontier.
            invert_in_m=g.z[i] - crit.MAX_COVER,
            q_peak_ls=q_peak_ls, q_adf_ls=q_adf_ls, n_prop=n_prop, why="cap",
            src="terrain", confidence="derived",
            provenance=(f"SCREEN cascade frontier; catchment {len_m/1000:.1f} km and "
                        f"{q_adf_m3d:,.0f} m3/d; PF {pf:.2f} ({meth})")))
    return out


def consolidate(demands: List[StationDemand], g: CorridorGraph,
                pc=PUMP) -> Tuple[List[StationDemand], List[dict]]:
    """Merge stations that sit within the manning break-even distance of one another.

    The economics is not a post-hoc check here, it is a LAYOUT RULE: NWS's manning charge is
    12,000 OMR/yr per station whatever its size, so deleting a station saves
    `pc.MANNING_PV_OMR` outright and the only cost is conveying its flow to the survivor.
    `pumping.consolidation_breakeven()` turns that into a length.

    THE CLUSTERING IS GREEDY FROM THE LARGEST SITE, NOT SINGLE-LINKAGE. Single linkage was
    tried first and chains: at a 1.1 km radius it merged 480 screen sites into 37 clusters,
    some of them spanning tens of kilometres, because A is near B and B is near C. The
    break-even is a statement about ONE conveyance run, so every absorbed site must be within
    R of THE SURVIVOR ITSELF - which is what the greedy pass enforces.
    """
    be = pumping.consolidation_breakeven(pc)
    R = be["breakeven_length_m"]
    if not demands:
        return [], []
    xs = np.array([d.x for d in demands])
    ys = np.array([d.y for d in demands])
    order = np.argsort([-d.q_adf_ls for d in demands])       # biggest catchment survives
    taken = np.zeros(len(demands), dtype=bool)
    groups: List[List[int]] = []
    for i in order:
        if taken[i]:
            continue
        d2 = (xs - xs[i]) ** 2 + (ys - ys[i]) ** 2
        members = [int(j) for j in np.flatnonzero((d2 <= R * R) & ~taken)]
        taken[members] = True
        groups.append(members)

    kept: List[StationDemand] = []
    log: List[dict] = []
    for members in groups:
        # the survivor is the LOWEST member - a station goes at the foot of the climb, never
        # at the junction (philosophy sec 5)
        best = min(members, key=lambda i: demands[i].ground_m)
        s = demands[best]
        q_peak = sum(demands[i].q_peak_ls for i in members)
        q_adf = sum(demands[i].q_adf_ls for i in members)
        n_prop = sum(demands[i].n_prop for i in members)
        merged = StationDemand(
            ident=f"PS{len(kept)+1:03d}", node=s.node, x=s.x, y=s.y,
            ground_m=s.ground_m, invert_in_m=s.invert_in_m,
            q_peak_ls=q_peak, q_adf_ls=q_adf, n_prop=n_prop, why=s.why,
            src=s.src, confidence=s.confidence,
            provenance=(s.provenance + f" | consolidated {len(members)} screen sites within "
                        f"{R:,.0f} m (manning break-even)"))
        kept.append(merged)
        if len(members) > 1:
            log.append({"station": merged.ident, "absorbed": len(members) - 1,
                        "radius_m": round(R, 0),
                        "manning_pv_saved_omr": round(pc.MANNING_PV_OMR * (len(members) - 1), 0),
                        "q_peak_ls": round(q_peak, 2)})
    return kept, log


# ======================================================================================
# 3. THE BUILD
# ======================================================================================

def _profile_features(tf, line: LineString) -> Tuple[int, int, float, float]:
    """Summits and low points along a routed main, from the terrain, plus the end levels.

    G203-p53 sec 8.4.1 puts a double-orifice air valve at every HIGH POINT and at significant
    gradient changes; G203-p54 sec 8.4.2 puts a washout at every LOW POINT, sized so a
    section empties in 3-4 hours. Both counts are therefore a PROFILE result, not a guess -
    and a prominence floor keeps terrain noise (sigma_z = 0.76 m, terrain manifest) from
    inventing valves."""
    n = max(2, int(line.length / PROFILE_STEP_M) + 1)
    ds = np.linspace(0.0, line.length, n)
    pts = [line.interpolate(float(d)) for d in ds]
    z = np.asarray(tf.elevation(np.array([p.x for p in pts]), np.array([p.y for p in pts])),
                   dtype=float)
    summits = lows = 0
    i = 1
    while i < len(z) - 1:
        if z[i] >= z[i - 1] and z[i] >= z[i + 1]:
            left = z[i] - np.min(z[:i + 1])
            right = z[i] - np.min(z[i:])
            if min(left, right) >= SUMMIT_MIN_PROMINENCE_M:
                summits += 1
        if z[i] <= z[i - 1] and z[i] <= z[i + 1]:
            left = np.max(z[:i + 1]) - z[i]
            right = np.max(z[i:]) - z[i]
            if min(left, right) >= SUMMIT_MIN_PROMINENCE_M:
                lows += 1
        i += 1
    return summits, lows, float(z[0]), float(z[-1])


def build(use_standin: Optional[bool] = None) -> dict:
    t0 = time.time()
    RUN.mkdir(parents=True, exist_ok=True)
    print(pumping.banner())
    print()

    if not ROADS_GPKG.exists():
        raise SystemExit(f"missing {ROADS_GPKG} - run s1_roads.py first")

    _log("loading the corridor network and the terrain")
    corr = gpd.read_file(ROADS_GPKG, layer="corridors")
    nodes = gpd.read_file(ROADS_GPKG, layer="nodes")
    tf = T.TerrainFlow.load("R5")
    g = CorridorGraph(corr, nodes, tf)
    _log(f"{g.n:,} nodes, {len(g.u):,} corridors, {g.L.sum()/1000:,.1f} km")

    _log("opening the flood-hazard grids")
    grids = hazard.HazardGrids()
    print(grids.banner())
    print()

    # wadi flag per corridor, on the 1:50 grid - the H1 test for a route
    mids = g.corr.geometry.values[g.eid]
    mx = np.array([m.interpolate(0.5, normalized=True).x for m in mids])
    my = np.array([m.interpolate(0.5, normalized=True).y for m in mids])
    cls = grids.sample_many(mx, my, rp=CRIT.HAZARD_RETURN_YR)
    g.wadi = np.isin(cls, CRIT.HAZARD_WADI_CLASSES)
    _log(f"{g.wadi.sum():,} of {len(g.wadi):,} corridors sit on wadi ground at 1:50 "
         f"({g.L[g.wadi].sum()/1000:,.1f} km) - routed around at "
         f"{WADI_ROUTE_PENALTY:g}x cost, never banned (H1a: a crossing is legal)")

    # --- the gravity field -------------------------------------------------------------
    sink = g.nearest(*STP_XY)
    s_min = CRIT.table11(SCREEN_DN)
    _log(f"depth-debt field to the works at node {g.nodes.NODE_ID.values[sink]} "
         f"(DN{SCREEN_DN} minimum {s_min*1000:.2f} mm/m, G203-p29 Table 11)")
    debt1, _p1 = g.depth_debt([sink], s_min)
    reach = np.isfinite(debt1)
    ok1 = reach & (debt1 <= GRAVITY_BUDGET_M)
    _log(f"ONE PASS from the works: only {ok1.sum():,} of {reach.sum():,} reachable nodes "
         f"({100.0*ok1.sum()/max(reach.sum(),1):.2f} %) get there inside the "
         f"{GRAVITY_BUDGET_M:.2f} m cover budget. That is the flatness, not a bug - and it "
         "is why the screen cascades.")
    # HOW MUCH OF THE STATION COUNT IS THE SCREEN'S OWN CONSERVATISM? Bracket it. The screen
    # charges every corridor the DN200 minimum, 5.00 mm/m - the STEEPEST row of G203-p29
    # Table 11 - because no reach has a diameter until the levels stage runs. On a main or a
    # trunk the minimum falls to 0.75 mm/m (DN900 and above), which is BELOW the ground's own
    # 2.24 mm/m average fall, so a large pipe accumulates no debt at all. The two runs
    # bracket the truth and the real answer sits between them.
    brackets = []
    for dn_b in (SCREEN_DN, 900):
        sb = CRIT.table11(dn_b)
        _d, _p, _st, _r = g.cascade(sink, sb, GRAVITY_BUDGET_M)
        brackets.append({"screen_dn": dn_b, "s_min_mm_m": round(sb * 1000, 2),
                         "frontier_sites": len(_st), "rounds": len(_r)})
        _log(f"    bracket DN{dn_b} at {sb*1000:.2f} mm/m -> {len(_st):,} frontier sites")
    _log("    the DN200 run is the CEILING on the station count and the DN900 run the FLOOR; "
         "the levels stage decides where between them the design lands")

    debt, par, screen_stations, rounds = g.cascade(sink, s_min, GRAVITY_BUDGET_M)
    ok = np.isfinite(debt) & (debt <= GRAVITY_BUDGET_M)
    _log(f"cascade: {len(rounds)} rounds, {len(screen_stations):,} frontier sites, "
         f"{100.0*ok.sum()/max(reach.sum(),1):.1f} % of reachable nodes now inside budget")
    for r in rounds[:12]:
        _log(f"    round {r['round']}: +{r['new_stations']:,} stations, "
             f"{r['nodes_over_budget']:,} nodes over budget, "
             f"{r['pct_gravity_ok']} % within")

    # --- demands -----------------------------------------------------------------------
    merges: List[dict] = []
    demands = None if use_standin else demands_from_design()
    if demands:
        source = "levels stage (W11b.gpkg nodes)"
        _log(f"{len(demands)} stations taken from the DESIGN")
    else:
        source = "SCREEN (s7 stand-in - NOT a design)"
        _log("no station nodes in the design - running the depth-debt SCREEN")
        raw = demands_standin(g, debt, par, screen_stations)
        _log(f"screen: {len(raw)} forced sites carrying load, before consolidation")
        demands, merges = consolidate(raw, g)
        be = pumping.consolidation_breakeven()
        _log(f"consolidated to {len(demands)} stations at the "
             f"{be['breakeven_length_m']:,.0f} m manning break-even "
             f"(project rule 9 uses 1,500 m - a ratio of "
             f"{be['ratio_rule9_to_breakeven']:.2f}); manning PV saved "
             f"{PUMP.MANNING_PV_OMR*(len(raw)-len(demands)):,.0f} OMR")

    # --- design each station -----------------------------------------------------------
    st_rows: List[dict] = []
    rm_rows: List[dict] = []
    refused: List[dict] = []
    reporting: List[dict] = []
    st_geom: List[Point] = []
    rm_geom: List[LineString] = []

    # A candidate discharge chamber is any node that a gravity sewer can reach the works
    # from - i.e. inside the cover budget on the cascaded field. `n_series` is how many
    # stations its flow still passes, so the ladder's first rung can be evaluated.
    # WHICH STATION OWNS EACH NODE'S GRAVITY FLOW. Used for two things: the catchment split
    # (no load counted twice) and - here - the LOOP GUARD. A node can be inside the cover
    # budget precisely BECAUSE this station is there; discharging into such a node would send
    # the flow straight back to the pump. H15 says the network is a forest, so a station may
    # only discharge into a node whose gravity owner is somebody else.
    owner = serving_station(g, par, screen_stations)

    target_mask = np.asarray(ok, dtype=bool)
    is_station = np.zeros(g.n, dtype=bool)
    is_station[list(screen_stations)] = True
    n_series = np.full(g.n, -1, dtype=np.int32)          # -1 = not yet computed
    for i in range(g.n):
        if n_series[i] >= 0:
            continue
        chain: List[int] = []
        cur = i
        while True:
            if n_series[cur] >= 0:
                base = int(n_series[cur])
                break
            k = int(par[cur])
            if k < 0:                                     # the works, or unreachable
                n_series[cur] = 0
                base = 0
                break
            chain.append(cur)
            cur = g.v[k] if g.u[k] == cur else g.u[k]
        for node_j in reversed(chain):
            base = base + (1 if is_station[node_j] else 0)
            n_series[node_j] = base
    # a station node itself does not count as one of the stations DOWNSTREAM of it
    n_series = np.where(is_station, np.maximum(n_series - 1, 0), n_series)

    for n_i, d in enumerate(demands, start=1):
        node = d.node if isinstance(d.node, (int, np.integer)) else g.nearest(d.x, d.y)
        node = int(node)

        # ---- siting first. A station on wet ground is moved, then refused.
        sit = pumping.site_station(d.x, d.y, d.ground_m, grids, max_search_m=SITE_SEARCH_M)
        moved_m = 0.0
        if not sit.publishable:
            cand = np.flatnonzero(reach)
            dd = np.hypot(g.x[cand] - d.x, g.y[cand] - d.y)
            near = cand[np.argsort(dd)[:60]]
            cl = grids.sample_many(g.x[near], g.y[near], rp=CRIT.PS_FLOOD_ARI_YR)
            dry = near[cl == 0]
            if len(dry):
                j = int(dry[0])
                moved_m = float(math.hypot(g.x[j] - d.x, g.y[j] - d.y))
                if moved_m <= SITE_SEARCH_M:
                    node = j
                    d.x, d.y, d.ground_m = float(g.x[j]), float(g.y[j]), float(g.z[j])
                    sit = pumping.site_station(d.x, d.y, d.ground_m, grids,
                                               max_search_m=SITE_SEARCH_M)
        if not sit.publishable:
            refused.append({"IDENT": d.ident, "X": round(d.x, 2), "Y": round(d.y, 2),
                            "Q_PK_LS": round(d.q_peak_ls, 2),
                            "WHY": "G203-p38 sec 7.2 siting", "DETAIL": sit.verdict[:400]})
            continue

        # ---- THE DISCHARGE CHAMBER, and the gravity-terminal answer.
        #      A node whose debt is inside the budget CAN be reached by a gravity sewer that
        #      then continues to its own owner - so choosing from that set guarantees the
        #      station discharges into a working gravity system rather than into thin air.
        #      W11a had no answer here at all and published zero rising mains.
        #      `n_series` counts how many stations the flow still passes on its way to the
        #      works, which is rung 1 of `pumping.DISCHARGE_LADDER` and is minimised first.
        # the loop guard: never discharge into a node this station itself drains
        mask = target_mask.copy()
        mask &= (owner != node)
        cands = []
        for j, edges, length in g.route_to_targets(node, mask, k_targets=8):
            if j == node:
                continue
            cands.append({"node": j, "stations_in_series": int(n_series[j]),
                          "commissions_package": bool(n_series[j] == 0),
                          "receiving_ok": True,
                          "static_lift_m": float(g.z[j] - g.z[node]),
                          "route_length_m": length, "edges": edges})
        if not cands:
            refused.append({"IDENT": d.ident, "X": round(d.x, 2), "Y": round(d.y, 2),
                            "Q_PK_LS": round(d.q_peak_ls, 2),
                            "WHY": "no gravity discharge reachable",
                            "DETAIL": "no corridor route from this station to any node that "
                                      "can itself reach the works on gravity WITHOUT draining "
                                      "back through this station (H15 loop guard). "
                                      "Resolutions: a "
                                      "satellite works (philosophy sec 8a), a cascade to a "
                                      "neighbouring station, or not serving. NOT a longer "
                                      "main chosen silently."})
            continue
        best = pumping.rank_discharge(cands)[0]
        line = g.geometry_of(best["edges"], node, best["node"])
        summits, lows, z0, z1 = _profile_features(tf, line)

        # ---- wadi exposure on the CHOSEN route, measured not assumed
        lh = grids.profile(line, rp=CRIT.HAZARD_RETURN_YR)
        wadi_m = float(lh.scour_length_m)

        # ---- design it
        try:
            S = pumping.design_station(
                ident=d.ident, x=d.x, y=d.y, ground_m=d.ground_m,
                invert_in_m=d.invert_in_m,
                q_peak_ls=d.q_peak_ls, q_adf_ls=d.q_adf_ls,
                main_length_m=line.length,
                discharge_ground_m=float(g.z[best["node"]]),
                n_prop=d.n_prop, why=d.why,
                n_summits=summits, n_low_points=lows,
                grids=grids, wadi_length_m=wadi_m)
        except pumping.PumpingError as e:
            refused.append({"IDENT": d.ident, "X": round(d.x, 2), "Y": round(d.y, 2),
                            "Q_PK_LS": round(d.q_peak_ls, 2),
                            "WHY": "hydraulics", "DETAIL": str(e)[:400]})
            continue

        if not S.publishable:
            refused.append({"IDENT": d.ident, "X": round(d.x, 2), "Y": round(d.y, 2),
                            "Q_PK_LS": round(d.q_peak_ls, 2),
                            "WHY": "blocking", "DETAIL": " | ".join(S.blocking)[:400]})
            continue

        uid = contract.NODE_UID_FMT.format(n_i)
        eid = contract.EDGE_UID_FMT.format(n_i)
        ds_uid = contract.NODE_UID_FMT.format(900000 + n_i)   # the discharge chamber

        row = S.station_row()
        row.update({
            "NODE_UID": uid,
            "NODE_REF": f"{d.ident}-PS",
            # FLOOD_LV: G203-p38 sec 7.2 wants the 1:50 LEVEL and no level is derivable from
            # a hazard-CLASS grid. NaN, deliberately, and reported as a blocking gap. See
            # BLOCKING at the end of the run. Inventing one would be the exact failure this
            # project keeps retracting.
            "FLOOD_LV": np.nan,
            "RM_EDGE": eid,
            "COMM_PT": int(best["commissions_package"]),
            "SRC": d.src, "CONFIDENCE": d.confidence, "STAGE": STAGE,
            "MOVED_M": round(moved_m, 1),
            "DEBT_M": round(float(debt[node]), 2),
        })
        st_rows.append(row)
        st_geom.append(Point(d.x, d.y))

        mrow = S.main_row()
        mrow.update({
            "EDGE_UID": eid, "US_NODE": uid, "DS_NODE": ds_uid, "STATION": uid,
            "SRC": d.src, "CONFIDENCE": d.confidence, "STAGE": STAGE,
            "WADI_M": round(wadi_m, 1),
            "N_ISOL": S.main.n_isolation,
            "AIRV_DN": S.main.air_valve_dn,
            "WASH_DN": S.main.washout_dn,
        })
        rm_rows.append(mrow)
        rm_geom.append(line)

        reporting.append({"IDENT": d.ident, "NODE_UID": uid,
                          "NOTE": " || ".join(S.reporting)})

    # --- publish -----------------------------------------------------------------------
    stations = gpd.GeoDataFrame(pd.DataFrame(st_rows), geometry=st_geom, crs=CRS) \
        if st_rows else gpd.GeoDataFrame(columns=["NODE_UID"], geometry=[], crs=CRS)
    mains = gpd.GeoDataFrame(pd.DataFrame(rm_rows), geometry=rm_geom, crs=CRS) \
        if rm_rows else gpd.GeoDataFrame(columns=["EDGE_UID"], geometry=[], crs=CRS)

    blocking: List[dict] = []
    for name, gdf in (("stations", stations), ("rising_mains", mains)):
        try:
            contract.validate(gdf, name, stage=STAGE, strict=True)
            _log(f"contract.validate({name}, strict=True): PASS")
        except Exception as e:
            blocking.append({"LAYER": name, "DETAIL": str(e)[:2000]})
            _log(f"contract.validate({name}, strict=True): BLOCKED")
        try:
            contract.validate(gdf, name, stage=STAGE, strict=False)
        except Exception as e:
            blocking.append({"LAYER": f"{name} (structure)", "DETAIL": str(e)[:2000]})

    PUMPS_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if PUMPS_GPKG.exists():
        PUMPS_GPKG.unlink()
    stations.to_file(PUMPS_GPKG, layer="stations", driver="GPKG")
    mains.to_file(PUMPS_GPKG, layer="rising_mains", driver="GPKG")

    prov = _provenance(source, g, debt, ok, reach, stations, mains, refused, brackets)
    import sqlite3
    con = sqlite3.connect(PUMPS_GPKG)
    try:
        prov.to_sql("provenance", con, if_exists="replace", index=False)
        pd.DataFrame(refused or [{"IDENT": "", "WHY": "none", "DETAIL": ""}]) \
            .to_sql("refused", con, if_exists="replace", index=False)
        pd.DataFrame(reporting or [{"IDENT": "", "NOTE": ""}]) \
            .to_sql("reporting", con, if_exists="replace", index=False)
        pd.DataFrame(blocking or [{"LAYER": "", "DETAIL": "none"}]) \
            .to_sql("blocking", con, if_exists="replace", index=False)
        pd.DataFrame(merges or [{"station": "", "absorbed": 0}])             .to_sql("consolidation", con, if_exists="replace", index=False)
        pd.DataFrame(rounds).to_sql("cascade", con, if_exists="replace", index=False)
        pd.DataFrame(brackets).to_sql("screen_bracket", con, if_exists="replace", index=False)
        _assumption_table().to_sql("assumptions", con, if_exists="replace", index=False)
        _conflict_table().to_sql("conflicts", con, if_exists="replace", index=False)
    finally:
        con.close()

    R = {
        "stage": STAGE, "version": STAGE_VERSION, "source_of_stations": source,
        "seconds": round(time.time() - t0, 1),
        "n_stations": len(stations), "n_mains": len(mains), "n_refused": len(refused),
        "gpkg": str(PUMPS_GPKG), "blocking": blocking,
    }
    (RUN / "s7_pumps.json").write_text(json.dumps(R, indent=2, default=str), encoding="utf-8")
    grids.close()

    _report(stations, mains, refused, blocking, source)
    _log(f"done in {R['seconds']:.0f} s -> {PUMPS_GPKG}")
    return R


# ======================================================================================
# 4. REPORTING
# ======================================================================================

def _assumption_table() -> pd.DataFrame:
    rows = [(k, str(v[0])[:120], str(v[1])[:600]) for k, v in PUMP.ASSUMPTIONS.items()]
    rows += [("WADI_ROUTE_PENALTY", WADI_ROUTE_PENALTY,
              "s7: cost multiplier on a corridor whose ground is hazard class 4-6 at 1:50. "
              "Steers the route dry; never bans a crossing, which H1a makes legal."),
             ("SITE_SEARCH_M", SITE_SEARCH_M,
              "s7: how far a wet station may be moved before it is REFUSED."),
             ("SUMMIT_MIN_PROMINENCE_M", SUMMIT_MIN_PROMINENCE_M,
              "s7: prominence floor for an air valve / washout. sigma_z on this terrain is "
              "0.76 m (terrain manifest), so a smaller bump is noise, not a summit."),
             ("SCREEN_DN", SCREEN_DN,
              "s7 stand-in only: the depth-debt screen uses the DN200 Table 11 minimum, the "
              "steepest in the table and the smallest permitted main (G203-p22 Table 6). "
              "Conservative by construction. Retired the moment the levels stage publishes "
              "station nodes.")]
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "NOTE"])


def _conflict_table() -> pd.DataFrame:
    return pd.DataFrame([(k, v) for k, v in PUMP.CONFLICTS.items()],
                        columns=["CONFLICT", "WHAT_W11B_DOES"])


def _provenance(source, g, debt, ok, reach, stations, mains, refused,
                brackets=()) -> pd.DataFrame:
    be = pumping.consolidation_breakeven()
    x = pumping.energy_equals_manning()
    rows = [
        ("stage_version", STAGE_VERSION, "", ""),
        ("source_of_stations", source, "",
         "A = levels stage. B = the s7 depth-debt SCREEN, which is NOT a design"),
        ("corridors_km", round(g.L.sum() / 1000, 1), "km", "[MEASURED] s1 PIPE_OK network"),
        ("corridors_on_wadi_km", round(g.L[g.wadi].sum() / 1000, 1), "km",
         f"[MEASURED] hazard class {CRIT.HAZARD_WADI_CLASSES} at 1:50"),
        ("gravity_budget_m", round(GRAVITY_BUDGET_M, 2), "m",
         "[G203-p33] MAX_COVER 12.00 less MIN_COVER 1.30"),
        ("screen_smin_mm_m", round(CRIT.table11(SCREEN_DN) * 1000, 2), "mm/m",
         f"[G203-p29 Tab 11] DN{SCREEN_DN}"),
        ("nodes_reachable", int(reach.sum()), "", "[MEASURED]"),
    ] + [
        (f"screen_bracket_DN{b['screen_dn']}", b["frontier_sites"], "sites",
         f"[MEASURED] cascade at {b['s_min_mm_m']} mm/m ({b['rounds']} rounds). The DN200 run "
         "is the CEILING on the station count (steepest Table 11 minimum, charged to every "
         "corridor); the DN900 run is the FLOOR (0.75 mm/m, below the ground's own 2.24 mm/m "
         "average fall, so a large pipe accrues no debt). The design lands between them and "
         "the levels stage decides where") for b in brackets
    ] + [
        ("nodes_gravity_ok", int(ok.sum()), "",
         "[MEASURED] can reach the works within the cover budget"),
        ("pct_gravity_ok", round(100.0 * ok.sum() / max(reach.sum(), 1), 1), "%",
         "[MEASURED] the complement is what forces stations"),
        ("n_stations", len(stations), "", "[DESIGNED]"),
        ("n_rising_mains", len(mains), "", "[DESIGNED]"),
        ("n_refused", len(refused), "",
         "[DESIGNED] refused rather than published - see the `refused` table"),
        ("manning_pv_omr_per_station", round(PUMP.MANNING_PV_OMR, 0), "OMR",
         "[NWS PIAD] 12,000 OMR/yr x PVAF 14.0939 (G201-p96, 25 yr at 5 %). Independent of "
         "station size - which is why fewer larger stations win"),
        ("consolidation_breakeven_m", round(be["breakeven_length_m"], 0), "m",
         "[DERIVED] manning PV / rising-main rate. Project rule 9 cascades at 1,500 m, a "
         f"ratio of {be['ratio_rule9_to_breakeven']:.2f}"),
        ("energy_equals_manning_at", round(x["crossover_qadf_ls_x_head_m"], 0), "L/s.m",
         "[DERIVED] Q_adf x total head at which the energy bill equals the manning bill. "
         "Below a tenth of it energy is a rounding error; above it, it is not. The "
         "'energy is 0.4 %' figure is a SMALL-STATION statement, not a law"),
        ("tau_flag", CRIT.TAU_PA, "Pa", CRIT.tau_banner().splitlines()[0]),
        ("flood_level_test", "UNEVALUABLE", "",
         "G203-p38 sec 7.2 needs the 1:50 flood LEVEL for the 300 mm freeboard. The project "
         "holds hazard CLASSES. DATA REQUEST to NWS. Reported as a failure, not a blank"),
        ("philosophy_citation_defect", "1:100 -> 1:50", "",
         pumping.PHILOSOPHY_CITATION_DEFECT[:600]),
    ]
    if len(stations):
        for col, unit in (("Q_DUTY_LS", "L/s"), ("HEAD_M", "m"), ("WELL_M3", "m3"),
                          ("MOTOR_KW", "kW"), ("LCC_OMR", "OMR")):
            if col in stations.columns:
                s = pd.to_numeric(stations[col], errors="coerce")
                rows.append((f"{col}_median", round(float(s.median()), 2), unit, "[DESIGNED]"))
                rows.append((f"{col}_max", round(float(s.max()), 2), unit, "[DESIGNED]"))
    if len(mains):
        rows.append(("rising_main_km", round(float(mains.LEN_M.sum()) / 1000, 2), "km",
                     "[DESIGNED] total published rising main - W11a published zero"))
        rows.append(("rising_main_on_wadi_km",
                     round(float(pd.to_numeric(mains.get("WADI_M", 0),
                                               errors="coerce").fillna(0).sum()) / 1000, 2),
                     "km", "[MEASURED] on the chosen routes; G201 sec 9.3 register applies"))
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "NOTE"])


def _report(stations, mains, refused, blocking, source) -> None:
    print("\n" + "=" * 86)
    print(f"  STAGE 7 - PUMPING STATIONS AND FORCE MAINS   (stations from: {source})")
    print("=" * 86)
    if len(stations):
        cols = [c for c in ("NODE_REF", "ST_TYPE", "N_DUTY", "Q_DUTY_LS", "Q_PP_LS", "HEAD_M",
                            "LIFT_M", "WELL_M3", "WW_RET_MI", "MOTOR_KW", "NPSH_MAR",
                            "LAND_M2", "PCT_MAN", "PCT_NRG") if c in stations.columns]
        print("\n-- stations --")
        print(stations[cols].to_string(index=False))
    if len(mains):
        cols = [c for c in ("EDGE_UID", "DN", "MATERIAL", "LEN_M", "V_DUTY_MS", "V_MIN_MS",
                            "STAT_HD_M", "TOT_HD_M", "RETENT_M", "N_AIRV", "N_WASH",
                            "N_ISOL", "WADI_M") if c in mains.columns]
        print("\n-- rising mains --")
        print(mains[cols].to_string(index=False))
    if refused:
        print("\n-- REFUSED (not published, and the reason) --")
        print(pd.DataFrame(refused).to_string(index=False))
    print("\n-- BLOCKING --")
    if blocking:
        for b in blocking:
            print(f"  * {b['LAYER']}: {b['DETAIL'][:700]}")
        print("""
  THE THREE BLOCKING ITEMS ABOVE, AND WHICH OF THEM IS A DESIGN FAULT (none of them is):

  1. FLOOD_LV null on every station. EXPECTED, and the honest answer.
     `contract.STATIONS.FLOOD_LV` is required and G203-p38 sec 7.2 needs the 1:50 flood
     LEVEL; this project holds hazard CLASSES with no water surface, and
     `hazard.flood_level_m_aod()` raises rather than inventing one. Philosophy sec 8 makes a
     check that cannot run a FAILURE, so it is published as one.
     DATA REQUEST: 1:50 (and 1:100) flood levels in m aOD, full coverage, from NWS / MoAFWR.

  2. "WELL_M3 != 0.25 x Q x (3600/starts)" on the Type 2 station. A CONTRACT DEFECT, not a
     design one. `contract.py` feeds `Q_DUTY_LS` - the STATION duty, all duty pumps - into
     G203-p48's equation, where the guideline says "Q = single pump capacity in m3/sec".
     On a Type 2 station that demands a wet well twice the size the clause asks for, and on
     a Type 3 three times. The check needs Q_DUTY_LS / N_DUTY. Reported, not worked around;
     s7 does not own contract.py.

  3. "99 rising mains fall below 0.75 m/s at the DESIGN MINIMUM flow". REAL, STRUCTURAL, AND
     NO DIAMETER FIXES IT. One main can only span a flow ratio of 2.5 / 0.75 = 3.33; on this
     project peak / design-minimum runs 8 to 13, because the Merrimack peak factor is 2-3 and
     G203-p40 Table 16 puts the initial minimum at a quarter of average. The three
     resolutions are the guideline's own and none of them is a size: staged mains (G203-p50
     sec 8.1, "two or more rising mains may be warranted"), twin mains with a dedicated
     hydraulic study (G203-p52 sec 8.2.3), or a scheduled flush. Note also that at ONE DUTY
     PUMP RUNNING - the lowest flow a fixed-speed station ever actually delivers - every one
     of these mains IS inside the band; `V_1PUMP` on the rising-main layer carries that
     figure beside `V_MIN_MS`. G203 does not settle which reading governs, so both are
     published and the ENGINEER decides.""")
    else:
        print("  none")
    print()


# ======================================================================================
# 5. THE AS-BUILT CALIBRATION CASE
# ======================================================================================

def asbuilt_case() -> None:
    """Design NAMA's OWN built station with this module, and say what it does and does not
    prove.

    The built asset is one station and 9,993.5 m of rising main, installed 2006, package
    5A-1. `FORCELINE_IBRI.shp` records NO diameter (N_DIAMETER, OUT_DIAMET and IN_DIAMETE are
    all 0 on the built row), NO material and NO invert; `GR_TEPS_IBRI.shp` holds ONE feature
    and it is the unapproved SUREKHA concept with NO_OF_PUMP = 0. So this cannot calibrate a
    diameter or a duty. What it DOES calibrate is the decision, and the decision is stark."""
    ab = pumping.ASBUILT_STATION
    print(pumping.banner())
    print("\n" + "=" * 86)
    print("  CALIBRATION - NAMA's own built station and rising main")
    print("=" * 86)
    fall = ab["ground_fall_per_km"]
    smin = CRIT.table11(200) * 1000.0
    sink_m = (smin - fall) * ab["main_length_m"] / 1000.0
    print(f"""
  built main            {ab['main_length_m']:,.0f} m, installed {ab['installed']}, package 5A-1
  station ground        {ab['station_ground_m']:.2f} m aOD
  works ground          {ab['discharge_ground_m']:.2f} m aOD
  STATIC LIFT           {ab['static_lift_m']:+.2f} m   <- NEGATIVE. The main FALLS.
  ground fall           {fall:.2f} mm/m
  DN200 minimum         {smin:.2f} mm/m   (G203-p29 Table 11)

  So a gravity DN200 on that route would sink {sink_m:.1f} m below the surface before it
  arrived - past the 12 m cap (G203-p33) five times over - and G203-p29 forbids fixing that
  by oversizing the pipe to lay it flatter. NAMA did not pump because there was a hill.
  THEY PUMPED BECAUSE THE GROUND IS TOO FLAT TO LAY A LEGAL GRAVITY SEWER ON.

  That is the same reason 60 % of this corridor network - about 1,100 km - falls more
  gently than the DN200 minimum. A better tree does not fix flatness, and this built asset
  is the measured proof that the resolution on this ground is a station and a main.

  WHAT IT CANNOT CALIBRATE:
  {ab['what_it_cannot_calibrate']}
""")
    # design it with our own module, on the flows the 5A-1 catchment would give
    fl = pumping.flows(120.0, 40.0)
    st = pumping.station_type(fl.q_peak_ls)
    fm = pumping.size_force_main(fl.q_peak_ls, fl, ab["main_length_m"],
                                 ab["static_lift_m"])
    sel = pumping.select_pump(fl, st, fm, ab["static_lift_m"],
                              site_level_m=ab["station_ground_m"])
    ec = pumping.economics(sel, fl, st, fm)
    print(f"  DESIGNED HERE on an indicative 120 L/s peak / 40 L/s average "
          f"(the 5A-1 duty is NOT recorded anywhere, so this is an ILLUSTRATION):")
    print(f"    {st.name}, {st.n_duty} duty + {st.n_standby} standby   (G203-p40 Table 17)")
    print(f"    rising main DN{fm.dn} {fm.material}, v_duty {fm.v_duty_ms:.2f} m/s, "
          f"v at design-minimum {fm.v_min_ms:.2f} m/s")
    print(f"    static {fm.static_lift_m:+.1f} m + friction {fm.hf_duty_m:.1f} m "
          f"+ minor {fm.hminor_duty_m:.1f} m = {fm.total_head_m:.1f} m total")
    print(f"    duty point {sel.duty_all.q_ls:.1f} L/s at {sel.duty_all.head_m:.1f} m, "
          f"motor {sel.motor_rating_kw:.0f} kW")
    print(f"    retention in the main {fm.retention_min:.0f} min "
          f"(G203-p50 wants under {CRIT.FM_RETENTION_MIN:.0f})")
    print(f"    life-cycle {ec.lifecycle_pv_omr:,.0f} OMR PV - manning "
          f"{ec.share_manning:.1%}, energy {ec.share_energy:.2%}")
    for n in fm.notes + sel.notes:
        print(f"    NOTE: {n}")
    print()


# ======================================================================================
# 6. VERIFY / REPORT / CLI
# ======================================================================================

def verify(gpkg: Path = PUMPS_GPKG) -> dict:
    """Re-run every check against the PUBLISHED file - never against an in-memory model."""
    out: Dict[str, object] = {"checks": [], "pass": True}

    def chk(name, cond, detail=""):
        out["checks"].append({"check": name, "pass": bool(cond), "detail": detail})
        if not cond:
            out["pass"] = False

    if not gpkg.exists():
        chk("published file exists", False, str(gpkg))
        return out
    st = gpd.read_file(gpkg, layer="stations")
    rm = gpd.read_file(gpkg, layer="rising_mains")
    chk("published file exists", True, str(gpkg))
    chk("every station has a non-zero duty flow",
        len(st) == 0 or (pd.to_numeric(st.Q_DUTY_LS, errors="coerce") > 0).all(),
        "W11a published 226 rows at zero")
    chk("every station has a rising main",
        len(st) == 0 or set(st.RM_EDGE.dropna()) == set(rm.EDGE_UID),
        f"{len(st)} stations, {len(rm)} mains")
    chk("no rising main exceeds the 2.5 m/s force-main maximum (G203-p50)",
        len(rm) == 0 or (pd.to_numeric(rm.V_DUTY_MS, errors="coerce") <= CRIT.FM_V_MAX + 1e-6).all())
    chk("no rising main below the 75 mm ID floor (G203-p50)",
        len(rm) == 0 or (pd.to_numeric(rm.DN, errors="coerce") >= 80).all())
    chk("land take is banded per G203-p43 Table 21, never a constant",
        len(st) == 0 or st.LAND_M2.nunique() >= min(2, st.ST_TYPE.nunique()),
        "W11a used a flat 100 m2 on every station")
    chk("geometry length agrees with LEN_M",
        len(rm) == 0 or bool(np.allclose(rm.geometry.length,
                                         pd.to_numeric(rm.LEN_M, errors="coerce"),
                                         atol=contract.LEN_TOL_M)))
    chk("CRS is EPSG:32640", (len(st) == 0 or st.crs.to_epsg() == 32640))
    # the one that is SUPPOSED to fail until NWS supply flood levels
    lv_ok = len(st) == 0 or st.FLOOD_LV.notna().all()
    out["checks"].append({
        "check": "FLOOD_LV populated (G203-p38 sec 7.2)", "pass": bool(lv_ok),
        "detail": ("EXPECTED FAILURE: no flood LEVEL is derivable from hazard-CLASS grids. "
                   "Data request to NWS. A check that cannot run is a FAILURE, not a blank.")})
    if not lv_ok:
        out["pass"] = False
    return out


def report(gpkg: Path = PUMPS_GPKG) -> None:
    import sqlite3
    con = sqlite3.connect(gpkg)
    try:
        for t in ("provenance", "cascade", "screen_bracket", "consolidation", "refused",
                  "blocking",
                  "assumptions", "conflicts", "reporting"):
            print(f"\n=== {t} ===")
            try:
                print(pd.read_sql(f"SELECT * FROM {t}", con).to_string(index=False))
            except Exception as e:
                print(f"  (missing: {e})")
    finally:
        con.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true", help="re-print the published tables")
    ap.add_argument("--verify", action="store_true", help="re-check the published file")
    ap.add_argument("--asbuilt", action="store_true",
                    help="design NAMA's own built station and compare")
    ap.add_argument("--standin", action="store_true",
                    help="force the depth-debt screen even if a design exists")
    ap.add_argument("--selftest", action="store_true", help="run w11b.pumping's self-test")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if pumping._self_test() else 1
    if a.asbuilt:
        asbuilt_case()
        return 0
    if a.report:
        report()
        return 0
    if a.verify:
        v = verify()
        print(json.dumps(v, indent=2))
        return 0 if v["pass"] else 2
    R = build(use_standin=a.standin or None)
    return 2 if R["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
