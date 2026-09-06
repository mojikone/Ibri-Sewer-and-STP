"""s7_pumps - STAGE 7: pumping stations and force mains, DESIGNED and PUBLISHED.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
The engineering lives in `w12.pumping`, which was built from PAM-GUD-201/202/203 directly;
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

CONCEPT-STAGE REVISION (engineer 2026-09-05/06) - WHAT CHANGED, AND WHY
    W11b TRIGGERED a station wherever a pipe crossed the depth cap. It designed 47, the
    levelling demanded 14, and 15 of the 47 had NOTHING draining into them. Three separate
    defects wearing one coat:

      * A TRIGGER IS NOT A DECISION. The frontier of a depth-debt field is an accident of
        terrain - it is where the ground happened to run out of fall, not where a station
        earns its manning bill. Philosophy sec 5: "its position is CHOSEN, NOT TRIGGERED".
      * TWO FUNCTIONS PRODUCED THE COUNT - the levels stage's prune, and this stage's own
        screen - so the shipped file disagreed with itself. Inheritance row 10: ONE published
        quantity, ONE function, and it prints its own funnel.
      * NOTHING EVER REMOVED A STATION. Inheritance row 4: anything a pass can ADD, a later
        pass must be able to TAKE AWAY, and the stage publishes how many it removed.

    So the stage is now three steps and they run in this order:

    a. WHERE GRAVITY GENUINELY FAILS.  `gravity_failure()` runs ONE depth-debt field from the
       LEGAL TERMINALS - the chambers where a subnetwork joins the client's Main Pipe, plus
       the works - and marks every corridor node whose cheapest gravity route costs more
       depth than the cover budget. NO STATION IS PLACED. That set, and only that set, is the
       input to siting. The physics is the same one the levels stage does properly: a pipe
       laid at the minimum legal gradient on ground that falls more gently than that gradient
       SINKS, and the shortfall accumulates along the flow path -

           debt(u -> v) = max( S_min x L  -  (z_u - z_v),  0 )

       with S_min the G203-p29 Table 11 minimum for DN200 (5.00 mm/m; the smallest permitted
       main or lateral, G203-p22 Table 6, and therefore the STEEPEST row in the table, so the
       screen is conservative by construction) and z from the 0.5 m terrain. Where the
       cheapest path's debt passes MAX_COVER - MIN_COVER (12.00 - 1.30 = 10.70 m, G203-p33),
       gravity cannot get there and something must lift it.

    b. A SEARCH, NOT A TRIGGER.  `search_sites()` is greedy maximum coverage. Every candidate
       is scored by HOW MUCH OF THE FAILED CATCHMENT IT CAPTURES - network length, failed
       chambers, and how many subnetworks - against the LIFT and the RISING MAIN it needs.
       The best one is placed, the field is RECOMPUTED with that station as a new zero-debt
       source, and the search repeats until nothing fails.

       ONE STATION PER ROUND, NOT THE WHOLE FRONTIER, AND THAT IS THE DIFFERENCE. On a
       MESHED road network a station on one branch can rescue a neighbouring branch through a
       cross-link that the debt TREE never shows, because the tree only ever records each
       node's single cheapest route to a terminal. W11b's cascade placed every frontier node
       at once and could not see that; recomputing after each placement can, and does.
       `tests/test_pump_siting.py` builds the two-branch mesh where the trigger needs two
       stations and the search needs one.

       WHY FEW, LARGE STATIONS.  Station cost correlates 0.99 with power and 0.72 with head,
       and 86 % of life-cycle cost is MANNING while 0.4 % is energy (inheritance row 25). So
       twenty small stations cost about twenty times one large one however little each lifts.
       The 2006 designer put ONE station in 95.45 km and took a third of the town through it.

    c. PRUNE, AND ONE FUNNEL.  `prune_redundant()` removes every station the others made
       unnecessary - a station whose removal leaves no node failed was never needed - and
       `station_funnel()` is THE function that produces the station count, printing
       N0 -> N1 -> N2 on every run and into the published `funnel` table. Nothing else in
       this file counts stations.

THE STATION LIST IS RE-TESTED, NEVER TRUSTED
    `demands_from_design()` still reads the published `nodes` layer of `W12.gpkg` (rows with
    `NODE_KIND == 'station'`, carrying GRD_M, INV_M, Q_PK_LS, Q_ADF_M3D and N_PROP) - that is
    where the real duty flows come from. But the LIST is re-tested against the failure field
    computed here and pruned like any other, which is the direct fix for "s7 reads a
    pre-prune list". A station the levels stage located and this stage cannot justify is
    REMOVED and counted, not published.

    Where the design has not been published yet the sites come from the search itself, every
    row labelled `SRC = 'terrain'`, `CONFIDENCE = 'derived'`, and a banner on every table.
    That is a SCREEN and it says so; it gives the right places and the right order of
    magnitude, not final flows.

A RISING MAIN LIFTS TO THE NEAREST POINT WHERE GRAVITY RESUMES - NOT TO THE WORKS
    Philosophy sec 6, concept rule 6. The discharge chamber is chosen from the nodes that can
    themselves reach a legal terminal on gravity, NEAREST FIRST, with two guards:
      * the LOOP GUARD - the candidate's own gravity owner must not be this station, or the
        flow would drain straight back to the pump (H15: the network is a forest);
      * `stations_in_series` - how many stations the flow still passes on the way out - is
        computed and MINIMISED FIRST, rung 1 of `pumping.DISCHARGE_LADDER`. It is not always
        zero: on ground this flat a cascade is sometimes unavoidable, and pretending
        otherwise would be W11a's failure in a different costume.
    `DS_TYPE` records whether the main ends at a `manhole` (gravity resumes there) or at the
    `stp`, and the share ending at `stp` is a PUBLISHED NUMBER rather than a claim in a
    paragraph. Retention time is reported per main, because a long force main is anaerobic by
    definition, needs an air valve at every summit and a washout at every low point, and is a
    single point of failure for everything upstream of it.

    THE BUILT 10.0 km MAIN IS A CRITIQUE, NOT A MODEL. It exists because in 2006 there was no
    gravity network to receive a shorter lift - see `--asbuilt`.

WHERE "FEWEST STATIONS" AND "SHORTEST MAIN" CONFLICT
    They are stated with BOTH numbers and never resolved silently. Within a round the trade
    goes to the `trades` table: what coverage was given up, in km and in failed chambers, and
    what main length was saved, in metres. Across the network, `cover_tol_sensitivity()`
    reruns the whole search at three coverage tolerances and publishes station count against
    total main length for each - so the one tuned number in the stage is a REPORTED
    SENSITIVITY rather than a hidden choice.

SWITCHED OFF AT CONCEPT, AND NAMED RATHER THAN QUIETLY ABSENT
    `motor_selection` and `life_cycle_cost` are `criteria.CONCEPT_OFF` entries. `w12.pumping`
    computes both internally as part of its OWN blocking checks - the NPSH margin needs a
    duty point, and the manning/energy regime is what tells a small station from a large one
    - and s7 does not own that module. So the columns are DROPPED at publication by
    `CONCEPT_DROP`, which names every one, says which capability it belongs to, and is
    printed on every run and written to the `concept_off` table. A declared drop, not a
    silent one.

WHAT THIS STAGE REFUSES TO PUBLISH
    * A STATION WITH NOTHING DRAINING INTO IT. Blocking, not a warning: it is pruned before
      design, counted in the funnel, and `verify()` fails the published file if one survives.
      `contract.STATIONS.N_SUBNET` refuses it a second time.
    * a station whose footprint is wet at the 1:50 event (G203-p38 sec 7.2) - it is moved to
      the nearest dry corridor node, and if none is found within the search radius the
      station is REFUSED and named in the `refused` table.
    * a force main that cannot reach 0.75 m/s WITH ONE DUTY PUMP RUNNING - the lowest flow
      the station ever delivers, so a main that silts there silts under every reading of
      G203-p50 sec 8.1. The answer is a grinder pump on a 50 mm ID main, or the catchment
      leaves the central network - never a resize.
    * a force main over 2.5 m/s at the worst case - G203-p50 sec 8.1, which is NOT the
      3.0 m/s gravity maximum of G203-p27. This project has conflated the two before, so the
      cap is read from `criteria.FM_V_MAX` in the sizing, in the publish check and in
      `verify()`, and never typed.
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

from w12 import contract, hazard, pumping, terrain as T          # noqa: E402
from w12.criteria import DEFAULT as CRIT                          # noqa: E402
from w12.pumping import PUMP                                      # noqa: E402

STAGE = "s7_pumps"
STAGE_VERSION = "W12-s7_pumps-2.0-concept-search"

W12 = HERE.parent
ROADS_GPKG = W12 / "shp" / "W12_roads.gpkg"
ORIENT_GPKG = W12 / "shp" / "W12_orient.gpkg"           # s2: which nodes join the Main Pipe
DESIGN_GPKG = W12 / "shp" / contract.GPKG_NAME          # the levels stage's output, if any
PUMPS_GPKG = W12 / "shp" / "W12_pumps.gpkg"
RUN = W12 / "run" / "pumps"

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

# --- the SEARCH's own constants. None of them is a design value; each bounds a SEARCH. ----
COVER_TOL = 0.9          # [ASSUME] the coverage band inside which two candidate sites are
                         # treated as equivalent on capture and decided on the LENGTH OF
                         # THEIR RISING MAIN instead. This is the one tuned number in the
                         # stage and it is never hidden: `cover_tol_sensitivity()` reruns the
                         # whole search at COVER_TOL_SCAN and publishes station count against
                         # total main length for each, so the reader sees what the choice
                         # bought. At 1.0 the rule is pure maximum coverage and the main
                         # length never enters; below about 0.5 a site that captures half as
                         # much can win on a shorter main, which is the wrong trade when
                         # manning is 86 % of the cost of a station (inheritance row 25).
COVER_TOL_SCAN = (1.0, 0.9, 0.75)        # [ASSUME] the tolerances the sensitivity reports
TOPK_MAINS = 6           # [ASSUME] how many of the best-covering candidates get a routed
                         # rising main during scoring. Routing is one Dijkstra per candidate
                         # and the frontier can be hundreds wide, so the trade is evaluated
                         # on the leaders. The CHOSEN site's main is re-routed afterwards
                         # against the FINAL field, which is the one that gets published.
MAX_SEARCH_ROUNDS = 400  # [ASSUME] a guard, not a target. Each round places exactly one
                         # station and strictly shrinks the failed set, so the search
                         # terminates on its own; hitting this is REPORTED as a guard hit.

# Columns `w12.pumping` computes that the concept stage does not publish. Each names the
# `criteria.CONCEPT_OFF` capability it belongs to (or the BANNED_FIELDS entry that refuses
# it), so the drop is a declaration rather than an omission. Printed on every run.
CONCEPT_DROP: Dict[str, Tuple[str, str]] = {
    "MOTOR_KW": ("motor_selection", "kW rating from the duty point. It does not move where a "
                                    "station goes, which is the only pump question the "
                                    "concept asks"),
    "NPSHA_M": ("motor_selection", "NPSH available - a machine-selection number; the MARGIN "
                                   "is still a blocking check inside w12.pumping"),
    "NPSHR_MAX": ("motor_selection", "the largest NPSH required a quoted machine may have"),
    "LCC_OMR": ("life_cycle_cost", "25-year present value. The finding it rests on - manning "
                                   "86 %, energy 0.4 % - already drives 'fewest stations'; "
                                   "the arithmetic adds nothing until unit rates exist"),
    "KWH_YR": ("life_cycle_cost", "annual energy, an input to the costing and to nothing "
                                  "else at concept"),
    "PCT_MAN": ("life_cycle_cost", "manning's share of the life-cycle cost"),
    "PCT_NRG": ("life_cycle_cost", "energy's share of the life-cycle cost"),
    "HEAD_M": ("contract.BANNED_FIELDS", "a third name for a head the layers already carry: "
                                         "LIFT_M on the station, STAT_HD_M / TOT_HD_M on its "
                                         "rising main"),
}


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

    # ---- the debt TREE, and what a candidate station would rescue ---------------------
    def children_of(self, par: np.ndarray) -> List[List[int]]:
        """Child lists of the debt tree, so a subtree can be walked once instead of
        re-derived per candidate. `par[i]` is the EDGE index i drains along, not a node."""
        kids: List[List[int]] = [[] for _ in range(self.n)]
        for i in range(self.n):
            k = int(par[i])
            if k < 0:
                continue
            dn = self.v[k] if self.u[k] == i else self.u[k]
            kids[int(dn)].append(i)
        return kids

    def subtree_within(self, kids: List[List[int]], par: np.ndarray, debt: np.ndarray,
                       p: int, budget: float) -> Tuple[List[int], float]:
        """What a station at `p` would rescue, and how much network comes with it.

        A station lifts the sewer back to minimum cover, so it is a NEW zero-debt source and
        every node u upstream of it arrives with debt(u) - debt(p). Debt is a sum of
        non-negative terms along the tree, so it never falls as you walk away from the root:
        the moment a descendant is over budget every node beyond it is too, and the walk can
        stop. That is what makes scoring every frontier candidate affordable.

        THIS IS A SCORE, AND IT IS DELIBERATELY CONSERVATIVE. It counts only what the debt
        TREE hangs off `p`. On a meshed road network a station can also rescue a node that
        currently drains a different way, through a cross-link the tree never shows - and
        that rescue is REALISED when `search_sites()` recomputes the field after placing the
        station. So the score under-counts and never over-counts, which is the right way
        round for a greedy that is choosing between candidates.
        """
        out: List[int] = [int(p)]
        km = 0.0
        stack = [int(p)]
        dp = float(debt[p])
        while stack:
            i = stack.pop()
            for c in kids[i]:
                if debt[c] - dp > budget:
                    continue
                k = int(par[c])
                km += float(self.L[k]) if k >= 0 else 0.0
                out.append(int(c))
                stack.append(int(c))
        return out, km / 1000.0

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
# 2. WHERE GRAVITY GENUINELY FAILS - step (a), and the ONLY input to siting
# ======================================================================================

class GravityFailure:
    """One depth-debt field, and the set of corridor nodes gravity cannot serve from it.

    NO STATION IS PLACED HERE. That separation is the whole point: W11b's station positions
    were an artefact of where a single pass of a solver happened to cross the depth cap, and
    philosophy sec 5 says a station's position is CHOSEN, not triggered. So the failure is
    established first, as a statement about the ground and the corridors alone, and the
    search that follows is answerable to it.

    Three sets come out, and each is reported rather than assumed away:
      * `failed`     reachable, but the cheapest gravity route costs more depth than budget
      * `served`     reachable inside the budget - the candidate discharge chambers
      * `orphan`     NO corridor route to any legal terminal at all. Not a pumping question:
                     a corridor-connectivity one, and it is named with its size rather than
                     rolled into the station count (concept rule 7, FLAG DO NOT SOLVE).
    """

    __slots__ = ("debt", "par", "failed", "served", "orphan", "budget", "s_min",
                 "terminals", "basis")

    def __init__(self, debt, par, budget, s_min, terminals, basis):
        self.debt, self.par = debt, par
        self.budget, self.s_min = float(budget), float(s_min)
        self.terminals = [int(t) for t in terminals]
        self.basis = str(basis)
        reach = np.isfinite(debt)
        self.orphan = ~reach
        self.failed = reach & (debt > self.budget)
        self.served = reach & ~self.failed

    @property
    def n_failed(self) -> int:
        return int(self.failed.sum())

    def summary(self) -> dict:
        n = len(self.debt)
        return {"nodes": n, "terminals": len(self.terminals), "basis": self.basis,
                "served": int(self.served.sum()), "failed": self.n_failed,
                "orphan": int(self.orphan.sum()),
                "pct_gravity_ok": round(100.0 * self.served.sum()
                                        / max(int(np.isfinite(self.debt).sum()), 1), 2),
                "worst_debt_m": (round(float(np.nanmax(self.debt[np.isfinite(self.debt)])), 2)
                                 if np.isfinite(self.debt).any() else float("nan"))}


def _matches(col, val) -> "pd.Series":
    """`col == val` that survives the dtype the writer happened to use.

    THE DEFECT THIS FIXES, measured 2026-09-06. `legal_terminals()` compared
    `df[col].astype(str) == str(val)`, so an `IS_OUTFALL` column that came back as float64 -
    which is what pandas gives the moment ONE row is null, and what a GeoPackage written from
    a float frame gives always - stringifies to '1.0' and never matches '1'. The filter
    emptied, the function fell through to the WORKS-ALONE basis, and the run went on to
    report a station count built on 0.31 % of the corridor network while saying "no published
    outfall layer was readable" - which was not true; it was read, and then silently
    discarded. That is the guard-that-quietly-no-ops failure (inheritance row 13), and here
    it lands on the one input that decides every number in the stage.

    So: numbers are compared as numbers, and text as text.
    """
    txt = col.astype(str).str.strip()
    try:
        want = float(val)
    except (TypeError, ValueError):
        return txt == str(val)
    num = pd.to_numeric(col, errors="coerce")
    hit = num.notna() & (num.sub(want).abs() < 1e-9)
    # a text column holding "1", or a boolean column holding True, is the same answer
    aliases = {str(val).strip().lower(), str(want)}
    if want == int(want):
        aliases.add(str(int(want)))
    if want == 1.0:
        aliases.add("true")
    return hit | txt.str.lower().isin(aliases)


def legal_terminals(g: CorridorGraph, *, design_gpkg: Path = DESIGN_GPKG,
                    orient_gpkg: Path = ORIENT_GPKG) -> Tuple[List[int], str]:
    """The nodes a gravity sewer may legally END at, and where that list came from.

    A TERMINAL IS LEGAL IF IT IS THE MAIN PIPE OR A PUMPING STATION WITH A DESIGNED RISING
    MAIN (`_BRAIN/10_ASBUILT_CALIBRATION.md` T1, measured from NAMA's own 5A-1 - a third of
    the built network, ending 6,754 m short of the works at a station and a 10 km main). The
    stations are what this stage is deciding, so the terminals it starts from are the FIXED
    ones: every chamber where a subnetwork joins the client's Main Pipe, plus the works.

    Read from the PUBLISHED layers in order of authority, never re-derived (inheritance
    row 3), and the basis is published beside every number because it changes the answer:

      1. `W12.gpkg` nodes, IS_OUTFALL == 1        - the design's own outfalls
      2. `W12_orient.gpkg` nodes, KIND == 'outfall' - s2's Main-Pipe joins
      3. the works alone                          - DEGRADED, and it says so. On this ground
         only 0.31 % of corridor nodes can reach the works inside the cover budget, so a
         works-only basis measures the flatness of Ibri and not the merit of a layout.
    """
    works = g.nearest(*STP_XY)
    for path, layer, col, val, why in (
            (design_gpkg, "nodes", "IS_OUTFALL", 1,
             "published design outfalls (W12.gpkg nodes IS_OUTFALL=1) plus the works"),
            (orient_gpkg, "nodes", "KIND", "outfall",
             "s2 Main-Pipe joins (W12_orient.gpkg nodes KIND='outfall') plus the works")):
        if not Path(path).exists():
            continue
        try:
            import fiona
            if layer not in fiona.listlayers(str(path)):
                continue
            df = gpd.read_file(str(path), layer=layer)
        except Exception as e:                       # noqa: BLE001 - reported, never hidden
            _log(f"terminals: {Path(path).name} present but unreadable ({e})")
            continue
        if col not in df.columns:
            continue
        key = "NODE_ID" if "NODE_ID" in df.columns else (
            "NODE_UID" if "NODE_UID" in df.columns else None)
        if key is None:
            continue
        sel = df[_matches(df[col], val)]
        idx = [g.idx[k] for k in sel[key].astype(str).values if k in g.idx]
        if not idx:
            continue
        out = sorted(set(idx) | {works})
        return out, f"{why}: {len(out):,} terminals"
    return [works], ("THE WORKS ALONE - no published outfall layer was readable. DEGRADED "
                     "BASIS: on this ground 0.31 % of corridor nodes reach the works inside "
                     "the cover budget, so the failed set below is a statement about the "
                     "flatness of Ibri, not about a layout. Run s2_orient (or s6_levels) and "
                     "re-run this stage before quoting a station count.")


def gravity_failure(g: CorridorGraph, terminals: Sequence[int], s_min: float,
                    budget: float, basis: str = "") -> GravityFailure:
    """Step (a). ONE depth-debt field from the legal terminals; no station placed."""
    debt, par = g.depth_debt(terminals, s_min)
    return GravityFailure(debt, par, budget, s_min, terminals, basis)


def subnet_labels(g: CorridorGraph, *, design_gpkg: Path = DESIGN_GPKG,
                  orient_gpkg: Path = ORIENT_GPKG) -> Tuple[List[str], str]:
    """A SUBNET label per corridor node, and where it came from.

    `contract.STATIONS.N_SUBNET` is 'how many subnetworks drain into this station', and a
    station with none is a blocking failure. The labels come from the published layers -
    the design's `nodes.SUBNET` first, s2's `nodes.SUBNET` second - and NEVER from anything
    invented here. When neither exists the list is empty and `catchment_of()` says so on
    every row it writes, counting upstream BRANCHES instead: the same physical question
    asked of the data that exists, with the basis named rather than left to be guessed."""
    blank = [""] * g.n
    for path, why in ((design_gpkg, "W12.gpkg nodes.SUBNET (the design)"),
                      (orient_gpkg, "W12_orient.gpkg nodes.SUBNET (s2)")):
        if not Path(path).exists():
            continue
        try:
            import fiona
            if "nodes" not in fiona.listlayers(str(path)):
                continue
            df = gpd.read_file(str(path), layer="nodes")
        except Exception as e:                       # noqa: BLE001 - reported, never hidden
            _log(f"subnets: {Path(path).name} present but unreadable ({e})")
            continue
        if "SUBNET" not in df.columns:
            continue
        key = "NODE_ID" if "NODE_ID" in df.columns else (
            "NODE_UID" if "NODE_UID" in df.columns else None)
        if key is None:
            continue
        out = list(blank)
        hit = 0
        for k, v in zip(df[key].astype(str).values, df["SUBNET"].astype(str).values):
            i = g.idx.get(k)
            if i is None or v in ("", "nan", "None"):
                continue
            out[i] = v
            hit += 1
        if hit:
            return out, f"{why}: {hit:,} of {g.n:,} corridor nodes labelled"
    return blank, ("NO SUBNET LABELLING PUBLISHED. N_SUBNET counts upstream branches "
                   "instead and every row says so - run s2_orient or s6_levels for the "
                   "real subnetwork count.")


def town_of_node(design_nodes, node_uid: str, max_hops: int = 200) -> str:
    """The town letter for an element that is not itself inside a town.

    CONCEPT RULE 8: "Elements outside any town take the letter of the first town DOWNSTREAM
    of them, so naming runs AFTER connectivity is known." A pumping station is exactly such
    an element - it is a SEAM between subnetworks, not a member of one - so its letter is the
    first non-blank TOWN found walking DS_NODE downstream from its discharge chamber.

    Returns '' when nothing downstream carries a town, which is legal mid-pipeline:
    `contract` makes NAME/TOWN required as COLUMNS and blank-able as VALUES, and
    `assert_named()` is the separate gate the final publish calls."""
    if design_nodes is None or not len(design_nodes):
        return ""
    if "TOWN" not in design_nodes.columns or "NODE_UID" not in design_nodes.columns:
        return ""
    town = dict(zip(design_nodes.NODE_UID.astype(str), design_nodes.TOWN.astype(str)))
    nxt = (dict(zip(design_nodes.NODE_UID.astype(str), design_nodes.DS_NODE.astype(str)))
           if "DS_NODE" in design_nodes.columns else {})
    cur, seen = str(node_uid), set()
    for _hop in range(int(max_hops)):
        if cur in seen:
            break
        seen.add(cur)
        t = town.get(cur, "")
        if t and t not in ("nan", "None"):
            return t
        cur = nxt.get(cur, "")
        if not cur or cur in ("nan", "None"):
            break
    return ""


# ======================================================================================
# 3. THE SEARCH - step (b). A station's POSITION IS CHOSEN, NOT TRIGGERED
# ======================================================================================

class Site:
    """One candidate station position, with everything the choice was made on.

    `cover_*` is what it CAPTURES; `lift_m` and `main_m` are what it COSTS. Both halves are
    published on the station row (N_SUBNET, CATCH_KM against LIFT_M and the main's LEN_M),
    because a station with a large lift and a small catchment is the one to argue about and
    neither number alone shows it."""

    __slots__ = ("node", "cover_nodes", "cover_km", "cover_n", "subnets", "n_subnet",
                 "lift_m", "main_m", "ds_node", "ds_edges", "why")

    def __init__(self, node, cover_nodes, cover_km, subnets, lift_m, main_m,
                 ds_node, ds_edges, why=""):
        self.node = int(node)
        self.cover_nodes = list(cover_nodes)
        self.cover_n = len(self.cover_nodes)
        self.cover_km = float(cover_km)
        self.subnets = set(subnets)
        self.n_subnet = len(self.subnets)
        self.lift_m = float(lift_m)
        self.main_m = float(main_m)
        self.ds_node = None if ds_node is None else int(ds_node)
        self.ds_edges = list(ds_edges)
        self.why = why

    def as_row(self) -> dict:
        return {"node": self.node, "cover_km": round(self.cover_km, 3),
                "cover_chambers": self.cover_n, "n_subnet": self.n_subnet,
                "lift_m": round(self.lift_m, 2), "main_m": round(self.main_m, 1),
                "why": self.why}


def frontier_candidates(g: CorridorGraph, gf: GravityFailure) -> List[int]:
    """The feet of the climbs: failed nodes whose own downstream neighbour on the debt tree
    is NOT failed.

    Philosophy sec 5: "the station goes at the FOOT of the climb, not at the junction. A drop
    is flow going down; a station lifts it up. One where they meet is physically incoherent."
    A failed node with no tree parent at all is a candidate too - it is a component that
    never reached a terminal and is reported separately as an orphan."""
    out: List[int] = []
    for i in np.flatnonzero(gf.failed):
        k = int(gf.par[i])
        if k < 0:
            continue
        dn = g.v[k] if g.u[k] == i else g.u[k]
        if not gf.failed[int(dn)]:
            out.append(int(i))
    return out


def _discharge_candidates(g: CorridorGraph, gf: GravityFailure, node: int,
                          owner: np.ndarray, n_series: np.ndarray,
                          k_targets: int = 8, guard_node: Optional[int] = None) -> List[dict]:
    """Where a station at `node` could discharge, nearest gravity chamber first.

    CONCEPT RULE 6: A RISING MAIN LIFTS TO THE NEAREST POINT WHERE GRAVITY RESUMES, NOT TO
    THE WORKS. The candidate set is exactly the nodes that can themselves reach a legal
    terminal on gravity, so the main always ends where a gravity sewer takes over.

    The LOOP GUARD is the second half: a node can be inside the cover budget precisely
    BECAUSE this station is there, and discharging into such a node would send the flow
    straight back to the pump. H15 makes the network a forest, so a station may only
    discharge into a node whose gravity owner is somebody else.

    `guard_node` is the node the OWNER map was built on, which is not always the node the main
    leaves from: a station standing on ground that is wet at 1:50 (G203-p38 sec 7.2) is moved
    to the nearest dry corridor node, and its catchment does not move with it. The guard has
    to follow the catchment, not the footprint."""
    mask = np.asarray(gf.served, dtype=bool).copy()
    mask &= (owner != (node if guard_node is None else int(guard_node)))
    cands: List[dict] = []
    for j, edges, length in g.route_to_targets(node, mask, k_targets=k_targets):
        if j == node:
            continue
        cands.append({"node": j, "stations_in_series": int(n_series[j]),
                      "commissions_package": bool(n_series[j] == 0),
                      "receiving_ok": True,
                      "static_lift_m": float(g.z[j] - g.z[node]),
                      "route_length_m": length, "edges": edges})
    return cands


def score_sites(g: CorridorGraph, gf: GravityFailure, candidates: Sequence[int],
                subnet_of: Sequence[str], owner: np.ndarray, n_series: np.ndarray,
                *, top_k: int = TOPK_MAINS) -> List[Site]:
    """Score every candidate on CAPTURE, then route a rising main for the leaders only.

    Capture is computed for all of them - it is a bounded tree walk. Routing is a Dijkstra
    apiece and the frontier can be hundreds wide, so only the `top_k` best-covering
    candidates get a main during scoring; the chosen one is re-routed afterwards against the
    FINAL field, and that is the route that gets published."""
    kids = g.children_of(gf.par)
    scored: List[Site] = []
    for p in candidates:
        nodes, km = g.subtree_within(kids, gf.par, gf.debt, p, gf.budget)
        subs = {subnet_of[i] for i in nodes if subnet_of[i]}
        scored.append(Site(p, nodes, km, subs, 0.0, float("inf"), None, []))
    scored.sort(key=lambda s: (-s.cover_km, -s.cover_n, s.node))
    for s in scored[:max(1, int(top_k))]:
        cands = _discharge_candidates(g, gf, s.node, owner, n_series)
        if not cands:
            continue
        best = pumping.rank_discharge(cands)[0]
        s.main_m = float(best["route_length_m"])
        s.lift_m = max(float(best["static_lift_m"]), 0.0)
        s.ds_node = int(best["node"])
        s.ds_edges = list(best["edges"])
    return scored


def choose_site(scored: Sequence[Site], cover_tol: float = COVER_TOL
                ) -> Tuple[Optional[Site], Optional[dict]]:
    """Pick one site, and RECORD THE TRADE when fewest-stations and shortest-main disagree.

    The rule, in order:
      1. the best capture in the round sets the bar;
      2. every candidate within `cover_tol` of it is treated as equivalent on capture and
         decided on the LENGTH OF ITS RISING MAIN - shortest wins;
      3. then least lift, then lowest node index so the answer is deterministic.

    Philosophy sec 6 is explicit that the two objectives can conflict - "a big catchment
    whose nearest gravity point is far" - and that where they do, the trade is STATED WITH
    BOTH NUMBERS rather than resolved silently. So whenever the chosen site is not the
    maximum-capture site, a `trades` row is returned carrying the capture given up (km and
    chambers) and the main length saved (m)."""
    live = [s for s in scored if s.ds_node is not None]
    if not live:
        # No candidate could be routed to a gravity discharge in this round. Still place the
        # best-capturing site - the depth cap is what demands it, and where its main goes is
        # settled after the search against the final field. The station is REFUSED later by
        # name if no discharge exists then either; what is not allowed is to skip the round
        # silently and leave the catchment failing with nothing said.
        if not scored:
            return None, None
        pick = scored[0]
        pick.why = (f"captures {pick.cover_km:.2f} km / {pick.cover_n:,} failed chambers; NO "
                    "gravity discharge was routable at scoring time - the main is settled "
                    "against the final field and the station is refused by name if none "
                    "exists then")
        return pick, None
    top = max(live, key=lambda s: (s.cover_km, s.cover_n))
    band = [s for s in live if s.cover_km >= float(cover_tol) * top.cover_km]
    pick = min(band, key=lambda s: (s.main_m, s.lift_m, s.node))
    trade = None
    if pick.node != top.node:
        trade = {"chosen_node": pick.node, "max_cover_node": top.node,
                 "cover_tol": float(cover_tol),
                 "cover_km_given_up": round(top.cover_km - pick.cover_km, 3),
                 "cover_chambers_given_up": top.cover_n - pick.cover_n,
                 "main_m_saved": round(top.main_m - pick.main_m, 1),
                 "lift_m_delta": round(pick.lift_m - top.lift_m, 2),
                 "NOTE": ("FEWEST STATIONS vs SHORTEST MAIN - both numbers stated, the trade "
                          "not resolved silently (philosophy sec 6). The site chosen "
                          f"captures {pick.cover_km:.2f} km against {top.cover_km:.2f} km "
                          f"and lifts it {pick.main_m:.0f} m against {top.main_m:.0f} m.")}
    pick.why = (f"captures {pick.cover_km:.2f} km / {pick.cover_n:,} failed chambers / "
                f"{pick.n_subnet} subnetwork(s) for a {pick.lift_m:.1f} m lift and a "
                f"{pick.main_m:.0f} m main"
                + ("" if trade is None else "; traded against the maximum-capture site, see "
                                            "the `trades` table"))
    return pick, trade


def search_sites(g: CorridorGraph, terminals: Sequence[int], s_min: float, budget: float,
                 subnet_of: Sequence[str], *, cover_tol: float = COVER_TOL,
                 basis: str = "", max_rounds: int = MAX_SEARCH_ROUNDS
                 ) -> Tuple[List[Site], GravityFailure, List[dict], List[dict]]:
    """Step (b). Greedy maximum coverage over the failed set.

    Place the best-scoring candidate, RECOMPUTE the field with it as a new zero-debt source,
    repeat until nothing fails. One station per round, and that is what separates a search
    from W11b's cascade: the cascade promoted the WHOLE frontier every round, so it could
    never discover that a station on one branch had rescued a neighbouring branch through a
    cross-link. Recomputing after each placement discovers exactly that, and on a road
    network - which is meshed, not a tree - it happens often.

    TERMINATION IS STRUCTURAL, not a guess. The chosen site is itself failed and becomes a
    source with zero debt, so |failed| strictly decreases every round; `max_rounds` is a
    guard and hitting it is reported in the round log rather than passed off as convergence.
    """
    placed: List[Site] = []
    sources = list(terminals)
    trades: List[dict] = []
    rounds: List[dict] = []
    gf = gravity_failure(g, sources, s_min, budget, basis)
    for r in range(int(max_rounds)):
        if gf.n_failed == 0:
            break
        cands = frontier_candidates(g, gf)
        if not cands:
            rounds.append({"round": r + 1, "candidates": 0, "placed": "",
                           "failed_before": gf.n_failed, "failed_after": gf.n_failed,
                           "NOTE": "GUARD: nodes are failing and no candidate site exists. "
                                   "This should be unreachable - debt is finite only where a "
                                   "route to a terminal exists, so walking down the tree from "
                                   "any failed node meets a served one and the first failed "
                                   "node above it IS a candidate. If this row appears, the "
                                   "debt field and the frontier disagree and that is a bug. "
                                   "(Orphans are a separate, REPORTED set: they have infinite "
                                   "debt, are never counted as failures, and are a corridor-"
                                   "connectivity finding rather than a pumping one.)"})
            break
        owner = serving_station(g, gf.par, [s.node for s in placed])
        n_series = stations_in_series(g, gf.par, [s.node for s in placed])
        scored = score_sites(g, gf, cands, subnet_of, owner, n_series)
        pick, trade = choose_site(scored, cover_tol)
        if pick is None:
            break
        before = gf.n_failed
        placed.append(pick)
        if trade is not None:
            trade["round"] = r + 1
            trades.append(trade)
        sources = list(terminals) + [s.node for s in placed]
        gf = gravity_failure(g, sources, s_min, budget, basis)
        rounds.append({"round": r + 1, "candidates": len(cands),
                       "placed": f"node {pick.node}",
                       "failed_before": before, "failed_after": gf.n_failed,
                       "NOTE": pick.why})
        if gf.n_failed >= before:                 # cannot happen; a guard that says so
            rounds.append({"round": r + 1, "candidates": len(cands), "placed": "",
                           "failed_before": before, "failed_after": gf.n_failed,
                           "NOTE": "GUARD: the failed set did not shrink. Stopping rather "
                                   "than looping - report this, it is a bug."})
            break
    else:
        # The loop ran out of rounds. That is only a GUARD HIT if something is still failing -
        # a network that needs exactly `max_rounds` stations and gets them is solved, and
        # reporting it as a guard hit would be a false alarm on a real answer.
        if gf.n_failed:
            rounds.append({"round": "GUARD", "candidates": 0, "placed": "",
                           "failed_before": gf.n_failed, "failed_after": gf.n_failed,
                           "NOTE": f"HIT MAX_SEARCH_ROUNDS = {max_rounds} with "
                                   f"{gf.n_failed:,} nodes still failing. The station count "
                                   "is a FLOOR, not an answer - raise the guard and re-run."})
    return placed, gf, trades, rounds


def cover_tol_sensitivity(g: CorridorGraph, terminals: Sequence[int], s_min: float,
                          budget: float, subnet_of: Sequence[str],
                          tols: Sequence[float] = COVER_TOL_SCAN) -> List[dict]:
    """Re-run the whole search at each coverage tolerance and publish what it bought.

    COVER_TOL is the one tuned number in this stage. Left alone it would be exactly the kind
    of hidden choice that makes a station count unarguable, so it is published as a
    SENSITIVITY: stations against total rising main, at 1.0 (pure maximum coverage, main
    length never enters) through 0.75. Rule (d) at network scale - both numbers, every
    time."""
    out: List[dict] = []
    for t in tols:
        sites, gf, trades, rounds = search_sites(g, terminals, s_min, budget, subnet_of,
                                                 cover_tol=float(t))
        out.append({"cover_tol": float(t), "stations": len(sites),
                    "total_main_m": round(sum(s.main_m for s in sites
                                              if math.isfinite(s.main_m)), 0),
                    "max_main_m": round(max([s.main_m for s in sites
                                             if math.isfinite(s.main_m)] or [0.0]), 0),
                    "captured_km": round(sum(s.cover_km for s in sites), 1),
                    "failed_left": gf.n_failed, "trades": len(trades),
                    "rounds": len(rounds)})
    return out


# ======================================================================================
# 4. THE PRUNE, AND THE ONE FUNCTION THAT COUNTS STATIONS
# ======================================================================================

def prune_redundant(g: CorridorGraph, sites: Sequence[Site], terminals: Sequence[int],
                    s_min: float, budget: float) -> Tuple[List[Site], List[dict]]:
    """INHERITANCE ROW 4, in code: anything a pass can ADD, a later pass must be able to
    TAKE AWAY, and the stage publishes how many it removed.

    W8 knew this on 2026-08-21 and cleared its pump flags at the top of every pass, with the
    reason in a comment. W11b lost the line and published three stations in a test area where
    the built network has none; pruning took the demand from 83 to 14.

    The test is the honest one: DELETE the station, recompute the field from the terminals
    and the SURVIVING stations, and see whether anything fails. If nothing does, the station
    was never needed - the others had already rescued its catchment, or a later placement
    did. Removals are tried smallest-capture first, because a small station is the one most
    likely to have been made redundant by a big one, and each removal is re-tested against
    the set that survives rather than against the original set."""
    keep = list(sites)
    removed: List[dict] = []

    def _field(sites_now):
        return gravity_failure(g, list(terminals) + [x.node for x in sites_now],
                               s_min, budget)

    # THE BASELINE IS WHAT THE FULL SET LEAVES FAILING, NOT ZERO. This is the line the prune
    # turned on, and it was wrong, measured 2026-09-06: the old test was `gf.n_failed == 0`,
    # so the moment ANY node was still failing with every station in - which is the ordinary
    # case for a list the LEVELS stage hands us, because that list was built against the
    # design's own diameters and this field charges the DN200 minimum to all 1,819 km - no
    # station could ever satisfy it and the whole prune became a silent no-op. Two adjacent,
    # plainly redundant stations survived it in a hand-built case. The prune is the headline
    # fix for "s7 reads a pre-prune list", so a prune that cannot fire is the defect wearing
    # the fix's clothes.
    #
    # The honest question is not "does the network solve without it" but "does removing it
    # break anything that was not already broken". So the test is a SET test: no node may
    # fail after the removal that was not failing before it.
    base_failed = _field(keep).failed.copy()

    # FIRST the station that captures nothing. It is the more specific finding and it is a
    # property of the station ALONE, not of what the others happen to cover - so it must not
    # be reported as "redundant", which would read as though a neighbour had absorbed it.
    for s in list(keep):
        if s.cover_n <= 1 and s.cover_km <= 0.0:
            trial = [x for x in keep if x is not s]
            after = _field(trial).failed
            stranded = int((after & ~base_failed).sum())
            keep = trial
            removed.append({"node": s.node, "cover_km": 0.0, "cover_chambers": s.cover_n,
                            "lift_m": round(s.lift_m, 2), "stranded_nodes": stranded,
                            "WHY": "NOTHING DRAINS INTO IT - the site captures no network "
                                   "length and no chamber but its own. 15 of W11b's 47 "
                                   "stations were like this. Blocking, not a warning: "
                                   "contract.STATIONS.N_SUBNET refuses the row and verify() "
                                   "fails the published file."
                                   + ("" if not stranded else
                                      f" IT IS REMOVED AND {stranded:,} CORRIDOR NODE(S) ARE "
                                      "LEFT WITH NO GRAVITY ROUTE AND NO STATION - a station "
                                      "for one chamber is not publishable (N_SUBNET = 0) and "
                                      "the ground still fails, so this is a FINDING for the "
                                      "engineer, not a solved problem. Concept rule 7: flag, "
                                      "do not solve. It is counted in `nodes_still_failing`.")})
            base_failed = base_failed | after

    for s in sorted(list(keep), key=lambda x: (x.cover_km, x.cover_n)):
        if s not in keep:
            continue
        trial = [x for x in keep if x is not s]
        after = _field(trial).failed
        if not bool((after & ~base_failed).any()):
            keep = trial
            removed.append({"node": s.node, "cover_km": round(s.cover_km, 3),
                            "cover_chambers": s.cover_n, "lift_m": round(s.lift_m, 2),
                            "stranded_nodes": 0,
                            "WHY": "REDUNDANT - deleting this station leaves no corridor node "
                                   "failing that was not already failing with it in place, "
                                   f"inside the {budget:.2f} m cover budget. Inheritance "
                                   "row 4: anything a pass can ADD, a later pass must be able "
                                   "to TAKE AWAY."})
    return keep, removed


def station_funnel(n0: int, n1: int, n2: int, *, source: str, removed: int,
                   refused: int, note: str = "") -> Dict[str, object]:
    """THE function that produces the station count. Inheritance row 10.

    W11b's levelling demanded 14 and its pump stage designed 47, and the shipped file carried
    both, because two functions computed the number in two places. W10 had SEVEN station
    counts in circulation - 19, 21, 25, 37, 140, 184, 239 - for the same reason. So there is
    exactly one funnel and everything that prints a station count reads it:

        N0  sites CONSIDERED   - what the provider offered, before any test of this stage's
        N1  sites DEMANDED     - after the search and the prune. This is 'how many stations
                                 the ground needs', and it is the number to quote
        N2  stations PUBLISHED - after refusals: a wet site with no dry ground inside the
                                 search radius, a main that cannot self-cleanse, a wet well
                                 that cannot hold its start levels

    N0 - N1 is what pruning removed; N1 - N2 is what the design refused. Both are published,
    because a number that shrinks with no accounting is how a silent drop looks from outside.
    """
    return {"N0_considered": int(n0), "N1_demanded": int(n1), "N2_published": int(n2),
            "pruned": int(removed), "refused": int(refused), "source": source,
            "NOTE": note or ("N0 considered -> N1 demanded (search + prune) -> N2 published "
                             "(after refusals). One function, one number - inheritance "
                             "row 10.")}


def funnel_frame(funnel: Dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame([{"STEP": k, "VALUE": v} for k, v in funnel.items()])


# ======================================================================================
# 5. STATION DEMANDS - the interface with the levels stage
# ======================================================================================

class StationDemand:
    __slots__ = ("ident", "node", "x", "y", "ground_m", "invert_in_m",
                 "q_peak_ls", "q_adf_ls", "n_prop", "why", "src", "confidence", "provenance",
                 "n_subnet", "catch_km", "site")

    def __init__(self, ident, node, x, y, ground_m, invert_in_m, q_peak_ls, q_adf_ls,
                 n_prop, why, src, confidence, provenance,
                 n_subnet=0, catch_km=0.0, site=None):
        self.ident, self.node = ident, node
        self.x, self.y = float(x), float(y)
        self.ground_m, self.invert_in_m = float(ground_m), float(invert_in_m)
        self.q_peak_ls, self.q_adf_ls = float(q_peak_ls), float(q_adf_ls)
        self.n_prop, self.why = float(n_prop), why
        self.src, self.confidence, self.provenance = src, confidence, provenance
        # THE EVIDENCE THAT THE POSITION WAS CHOSEN AND NOT TRIGGERED - published as
        # contract.STATIONS.N_SUBNET and CATCH_KM, and N_SUBNET = 0 is a blocking failure.
        self.n_subnet, self.catch_km = int(n_subnet), float(catch_km)
        self.site = site


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
            provenance="levels stage, W12.gpkg nodes NODE_KIND='station'"))
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
            if k < 0:                       # a source: the works, or a station
                res = cur if is_src[cur] else -1
                break
            path.append(cur)
            cur = g.v[k] if g.u[k] == cur else g.u[k]
        owner[i] = res
        for p in path:
            owner[p] = res
    return owner


def stations_in_series(g: CorridorGraph, par: np.ndarray,
                       stations: Sequence[int]) -> np.ndarray:
    """How many stations the flow at each node still passes on its way OUT.

    Rung 1 of `pumping.DISCHARGE_LADDER`, and it is minimised first: a station discharging
    into another station's catchment doubles the manning bill for one catchment and puts two
    failure points in series. It is NOT always zero - on ground this flat a cascade is
    sometimes unavoidable, and pretending otherwise would be W11a's failure in a different
    costume - so it is computed, published and ranked on rather than asserted away.

    IT IS A LOWER BOUND, and the bound is stated rather than left to be assumed. The debt
    tree STOPS at a station, because a station is a zero-debt source, so this counts the next
    station on the way out and cannot see the one after it. A node reading 1 passes AT LEAST
    one station. That is enough for the two jobs it has - ranking a discharge chamber that
    drains to the works above one that drains into another station, and flagging a main that
    lands in a cascade - and it is not enough to be quoted as a cascade DEPTH."""
    is_station = np.zeros(g.n, dtype=bool)
    if len(stations):
        is_station[list(stations)] = True
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
            if k < 0:
                # A ROOT OF THE DEBT TREE, AND IT IS USUALLY A STATION. This is the line that
                # was wrong, measured 2026-09-06 on a 120-node flat chain: a station IS a
                # zero-debt source, so `par` at a station is -1 and a station is therefore
                # NEVER a member of `chain`. The old code set the root to 0 whatever it was,
                # `is_station` never fired anywhere, and the function returned ZERO for every
                # node in the network - including nodes whose flow passes four stations on the
                # way out. Rung 1 of pumping.DISCHARGE_LADDER ("fewest stations in series"),
                # which this stage says it MINIMISES FIRST, was ranking on a constant, and
                # COMM_PT ("this station commissions its package on its own") published 1 on
                # every row. A published column constant where it should vary is a
                # fabrication - inheritance row 22.
                n_series[cur] = 1 if is_station[cur] else 0
                base = int(n_series[cur])
                break
            chain.append(cur)
            cur = g.v[k] if g.u[k] == cur else g.u[k]
        for node_j in reversed(chain):
            base = base + (1 if is_station[node_j] else 0)
            n_series[node_j] = base
    # a station node itself does not count as one of the stations DOWNSTREAM of it
    return np.where(is_station, np.maximum(n_series - 1, 0), n_series)


def catchment_of(g: CorridorGraph, gf: GravityFailure, sites: Sequence[Site],
                 subnet_of: Sequence[str], crit=CRIT
                 ) -> Dict[int, dict]:
    """What each placed station actually owns, once they are ALL placed.

    Scoring during the search used the debt subtree, which under-counts on a meshed network.
    This is the settled answer: the field is recomputed with every station in it, each node
    is walked down to the source it drains into, and the corridor edges are credited to the
    UPPER of their two ends so nothing is counted twice. That double-count is the failure
    that put 1,233 m3/d out of W10 and inflated an infiltration total by counting every
    upstream kilometre once per downstream reach.

    Load comes from the corridor layer's own measured `Q_NEAR_M3D` (s1). Peak factor from
    G201-p71 Merrimack via `criteria.peak_factor`, which holds at 1.0 below 100 properties
    because G201 prescribes no formula there. Infiltration is G201-p72's 720 L/d/km over the
    OWNED length only, unpeaked - the NEW-network allowance, not the existing-network
    percentage.
    """
    nodes = [s.node for s in sites]
    owner = serving_station(g, gf.par, nodes)
    qcol = "Q_NEAR_M3D" if "Q_NEAR_M3D" in g.corr.columns else "Q_M3D"
    q_edge = (g.corr[qcol].values.astype(float)[g.eid] if qcol in g.corr.columns
              else np.zeros(len(g.u)))
    load = np.zeros(g.n)
    length = np.zeros(g.n)
    debt = gf.debt
    for k in range(len(g.u)):
        a, b = int(g.u[k]), int(g.v[k])
        # the upper end owns the corridor; an exact tie goes to the FIRST end (US_NODE),
        # which is arbitrary but deterministic, and on ground this flat exact ties are not
        # rare. It keeps the split a partition either way - no kilometre counted twice.
        hi = a if debt[a] >= debt[b] else b
        load[hi] += max(q_edge[k], 0.0)
        length[hi] += g.L[k]

    out: Dict[int, dict] = {}
    for s in sites:
        m = owner == s.node
        q_adf_m3d = float(load[m].sum())
        len_m = float(length[m].sum())
        subs = {subnet_of[i] for i in np.flatnonzero(m) if subnet_of[i]}
        # PLOT_QADF_M3D IS PER PROPERTY, NOT PER PLOT, whatever its name says: criteria
        # defines it as OCCUPANCY x WWG_LCD / 1000 and its own docstring adds "the per-PLOT
        # figure multiplies by the counted properties on that plot, which is data, not this
        # constant"; s5_flows publishes its unit as m3/d/property and contract builds a
        # PLOT's load as PLOT_QADF_M3D x PROPS_PER_PLOT. So dividing a measured m3/d by it
        # ALREADY gives properties, and the inherited `* PROPS_PER_PLOT` (W11b s7_pumps:475,
        # carried into W12) inflated N_PROP by 45.6 % on every screen station. It is not a
        # cosmetic column: n_prop is the gate on `criteria.peak_factor`, which holds at 1.0
        # below PF_HOLD_PROPERTIES and switches to Merrimack above it, so the error could
        # move a station's peak flow, its ST_TYPE, its pump count and its land band.
        n_prop = q_adf_m3d / crit.PLOT_QADF_M3D
        pf, meth = crit.peak_factor(q_adf_m3d, n_prop)
        q_adf_ls = q_adf_m3d / 86.4
        out[s.node] = {
            "q_adf_m3d": q_adf_m3d, "q_adf_ls": q_adf_ls,
            "q_peak_ls": q_adf_ls * pf + crit.infiltration_ls(len_m),
            "n_prop": n_prop, "catch_km": len_m / 1000.0,
            "subnets": subs,
            # N_SUBNET, and what it means when the subnetworks are not labelled yet. With a
            # SUBNET column it is the count of distinct labels. Without one - a screen run
            # before s2/s6 have published - it is the number of distinct BRANCHES entering
            # the station, which is the same physical question ("how many separate pieces of
            # network drain into this?") asked of the data that exists. Which of the two was
            # used is on the row's provenance, never left to be guessed.
            "n_subnet": (len(subs) if subs else
                         int(sum(1 for j, kk in g.adj[s.node]
                                 if owner[j] == s.node and j != s.node))),
            "subnet_basis": "SUBNET labels" if subs else "upstream branches (no SUBNET yet)",
            "pf": pf, "pf_method": meth}
    return out


def demands_from_sites(g: CorridorGraph, gf: GravityFailure, sites: Sequence[Site],
                       subnet_of: Sequence[str], crit=CRIT) -> List[StationDemand]:
    """Turn the chosen sites into station demands. THE SCREEN - not a design, and it says so.

    Every row is labelled `SRC = 'terrain'`, `CONFIDENCE = 'derived'` and carries the
    provenance of the search that put it there. Final duty flows come from the levels stage;
    what this gives is the right places and the right order of magnitude."""
    cat = catchment_of(g, gf, sites, subnet_of, crit=crit)
    out: List[StationDemand] = []
    for s in sites:
        c = cat[s.node]
        i = s.node
        out.append(StationDemand(
            ident=f"PS{len(out)+1:03d}", node=i, x=g.x[i], y=g.y[i], ground_m=g.z[i],
            # the search's own arrival invert: a site is chosen at the foot of a climb where
            # the gravity budget is exhausted, so the incoming sewer arrives at the cap.
            invert_in_m=g.z[i] - crit.MAX_COVER,
            q_peak_ls=c["q_peak_ls"], q_adf_ls=c["q_adf_ls"], n_prop=c["n_prop"],
            why="cap", src="terrain", confidence="derived",
            n_subnet=c["n_subnet"], catch_km=c["catch_km"], site=s,
            provenance=(f"SEARCH site; captures {c['catch_km']:.1f} km, {c['n_subnet']} "
                        f"subnetwork(s) by {c['subnet_basis']}, {c['q_adf_m3d']:,.0f} m3/d; "
                        f"PF {c['pf']:.2f} ({c['pf_method']}); {s.why}")))
    return out


def drop_empty_catchments(demands: List[StationDemand]
                          ) -> Tuple[List[StationDemand], List[dict]]:
    """The LAST pass, on the MEASURED catchment rather than on the scored one.

    `prune_redundant()` works on the search's capture score, which is computed on the debt
    tree. `catchment_of()` then measures what each station actually owns once every station
    is in - and on a meshed network those can differ, because a site's scored subtree may end
    up draining to a neighbour instead. A station that owns nothing after that measurement is
    the W11b defect exactly: 15 of 47 with nothing draining into them.

    So it is removed HERE too, and counted into the same funnel. Two passes can add a station
    and both must be able to take one away (inheritance row 4); the alternative is a blocking
    contract failure at publish time, which tells you the same thing far too late."""
    keep, removed = [], []
    for d in demands:
        if d.n_subnet > 0 and d.catch_km > 0.0:
            keep.append(d)
            continue
        if str(d.why) != "cap":
            # a VETO or COMMISSIONING station is not there to drain a catchment, so an empty
            # one is a FINDING to argue about and not an automatic deletion. It is kept, and
            # `contract.STATIONS.N_SUBNET` will refuse it at publish with the reason on the
            # row - which is the right place for a decision this stage cannot make.
            keep.append(d)
            continue
        removed.append({"node": (d.site.node if d.site is not None else -1),
                        "cover_km": round(d.catch_km, 3), "cover_chambers": 0,
                        "lift_m": 0.0,
                        "WHY": "NOTHING DRAINS INTO IT once every station is placed - the "
                               f"measured catchment is {d.catch_km:.3f} km across "
                               f"{d.n_subnet} subnetwork(s). Scored capture and measured "
                               "catchment can differ on a meshed network, so the measured "
                               "one gets the last word."})
    return keep, removed


def demands_retested(g: CorridorGraph, gf: GravityFailure, demands: List[StationDemand],
                     subnet_of: Sequence[str], crit=CRIT
                     ) -> Tuple[List[StationDemand], List[dict]]:
    """Re-test a list the LEVELS STAGE handed us, and prune it. The direct fix for "s7 reads
    a pre-prune list".

    The design's station nodes are the authority on DUTY FLOW - they carry the accumulated
    Q_PK_LS and Q_ADF_M3D no screen can produce. They are NOT the authority on whether the
    station is needed: that is a statement about the ground, and this stage has just computed
    it. So each demanded station becomes a Site scored against THIS field, redundant ones are
    pruned by `prune_redundant()`, and the survivors keep the design's flows.

    Inheritance row 4 again: anything a pass can ADD, a later pass must be able to TAKE AWAY.
    """
    if not demands:
        return [], []
    # TWO STATIONS AT ONE NODE ARE ONE STATION. Deduplicating here rather than letting both
    # through is the same rule as crediting a corridor to one end only: a quantity counted
    # twice is the failure this project pays most for.
    removed: List[dict] = []
    seen: Dict[int, str] = {}
    kept_demands: List[StationDemand] = []
    for d in demands:
        i = (int(d.node) if isinstance(d.node, (int, np.integer)) else g.nearest(d.x, d.y))
        if i in seen:
            removed.append({"node": i, "cover_km": 0.0, "cover_chambers": 0, "lift_m": 0.0,
                            "WHY": f"DUPLICATE - the levels stage located {d.ident} at the "
                                   f"same corridor node as {seen[i]}. Two stations at one "
                                   "node is one station, and counting both is how a station "
                                   "count inflates."})
            continue
        seen[i] = d.ident
        kept_demands.append(d)
    demands = kept_demands
    sites = [Site(int(d.node) if isinstance(d.node, (int, np.integer))
                  else g.nearest(d.x, d.y), [], 0.0, set(), 0.0, float("inf"), None, [])
             for d in demands]
    kids = g.children_of(gf.par)
    for s in sites:
        s.cover_nodes, s.cover_km = g.subtree_within(kids, gf.par, gf.debt, s.node, gf.budget)
        s.cover_n = len(s.cover_nodes)
        s.subnets = {subnet_of[i] for i in s.cover_nodes if subnet_of[i]}
        s.n_subnet = len(s.subnets)
        s.why = (f"located by the levels stage; re-tested here - captures {s.cover_km:.2f} km "
                 f"/ {s.cover_n:,} chambers against the gravity-failure field")
    # ONLY A CAP STATION MAY BE PRUNED ON DEPTH. The cap-and-veto ladder has three other
    # rungs and this stage's depth-debt field cannot see any of them: a VETO station exists
    # because a chamber cannot be maintained, a COMMISSIONING one because it makes a package
    # independently buildable (philosophy sec 5-6, and NAMA's own 5A-1 is the measured
    # example), and an ECONOMICS one because pumping was cheaper than digging on. Pruning
    # those "because gravity reaches" would delete a decision made on evidence s7 does not
    # hold - the mirror image of the defect this whole revision is fixing.
    prunable = [s for s, d in zip(sites, demands) if str(d.why) == "cap"]
    protected = [(s, d) for s, d in zip(sites, demands) if str(d.why) != "cap"]
    for _s, d in protected:
        _log(f"    {d.ident} is a '{d.why}' station - NOT eligible for a depth prune "
             "(philosophy sec 5: layers 1 and 2 are not terms in a sum)")
    kept_prunable, dropped = prune_redundant(
        g, prunable, list(gf.terminals) + [s.node for s, _d in protected],
        gf.s_min, gf.budget)
    removed.extend(dropped)
    keep = kept_prunable + [s for s, _d in protected]
    keep_nodes = {s.node for s in keep}
    by_node = {s.node: s for s in sites}
    out: List[StationDemand] = []
    for d, s in zip(demands, sites):
        if s.node not in keep_nodes:
            continue
        d.site = by_node[s.node]
        out.append(d)
    # the catchment split is measured on the SURVIVING set, never on the list we were handed
    gf2 = gravity_failure(g, list(gf.terminals) + [s.node for s in keep],
                          gf.s_min, gf.budget, gf.basis)
    cat = catchment_of(g, gf2, keep, subnet_of, crit=crit)
    for d in out:
        c = cat[d.site.node]
        d.n_subnet, d.catch_km = c["n_subnet"], c["catch_km"]
        d.provenance = (d.provenance + f" | re-tested by s7: captures {c['catch_km']:.1f} km "
                        f"and {c['n_subnet']} subnetwork(s) by {c['subnet_basis']}")
    return out, removed


# ======================================================================================
# 6. THE BUILD
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


def _design_nodes(gpkg: Path = DESIGN_GPKG):
    """The published `nodes` layer, or None. Read ONCE per run and passed down - the same
    read inside the per-station loop would be the loop-invariant I/O `test_deadcode.py`
    fails a file for."""
    if not Path(gpkg).exists():
        return None
    try:
        import fiona
        if "nodes" not in fiona.listlayers(str(gpkg)):
            return None
        return gpd.read_file(str(gpkg), layer="nodes")
    except Exception as e:                           # noqa: BLE001 - reported, never hidden
        _log(f"design nodes present but unreadable ({e}) - naming will be left blank")
        return None


DISCHARGE_MATCH_M = 25.0   # [ASSUME] how far a design chamber may sit from the corridor node
                           # the main was routed to and still BE that chamber. A chamber is
                           # placed ON a corridor, so the two coincide to within the chamber
                           # spacing. IT IS NOT SAFE AGAINST JUMPING TO THE NEIGHBOUR, and
                           # saying so is the point: the built network's median chamber
                           # spacing is 29.77 m (_BRAIN/10_ASBUILT_CALIBRATION.md), so the
                           # half-span that would guarantee a unique match is 14.9 m and
                           # 25 m is well OVER it. It is a bound on how far the resolution
                           # may stray, not a proof that it is right. TIGHTEN IT to half the
                           # published median once s6 has run and that median is measured on
                           # our own chambers.


def _discharge_uid(g: CorridorGraph, design_nodes, node: int, n_i: int) -> str:
    """The NODE_UID of the chamber a rising main discharges into.

    THE MAIN MUST REFERENCE A CHAMBER THAT EXISTS. `contract.RISING_MAINS.refs` points DS_NODE
    at `nodes.NODE_UID`, and a reference with nothing behind it is the CROSS_ID defect wearing
    another coat - an id that resolves to no row schedules nothing.

    The corridor graph and the design use different id spaces (s1's NODE_ID against the
    contract's minted NODE_UID), so the match is by COORDINATE: the nearest published chamber
    within `DISCHARGE_MATCH_M`. Where the design has not been published, or no chamber is that
    close, a placeholder is minted OUT of the station range so it cannot be mistaken for one -
    and that is the honest answer for a screen run with no chambers to point at."""
    if (design_nodes is not None and len(design_nodes)
            and {"NODE_UID", "X", "Y"} <= set(design_nodes.columns)):
        dx = design_nodes.X.to_numpy(float) - float(g.x[node])
        dy = design_nodes.Y.to_numpy(float) - float(g.y[node])
        d2 = dx * dx + dy * dy
        j = int(np.argmin(d2))
        if float(d2[j]) <= DISCHARGE_MATCH_M ** 2:
            return str(design_nodes.NODE_UID.values[j])
    return contract.NODE_UID_FMT.format(900000 + n_i)


def _drop_switched_off(row: dict) -> dict:
    """Remove the columns `CONCEPT_DROP` names, and say nothing quietly.

    `w12.pumping.design_station()` selects a pump and computes a 25-year present value as
    part of its OWN blocking checks - the NPSH margin needs a duty point, and the
    manning/energy regime is what tells a small station from a large one. Both capabilities
    are `criteria.CONCEPT_OFF` entries and s7 does not own that module, so the columns are
    dropped HERE, by name, with the capability each belongs to recorded in `CONCEPT_DROP` and
    printed on every run and written to the `concept_off` table.

    A declared drop, not an omission. `contract.BANNED_FIELDS` refuses MOTOR_KW, LCC_OMR and
    HEAD_M outright, so leaving any of them on the frame would block the publish anyway - but
    a validator catching it is not the same as the stage meaning it."""
    return {k: v for k, v in row.items() if k not in CONCEPT_DROP}


def concept_off_table() -> pd.DataFrame:
    rows = []
    for col, (cap, why) in sorted(CONCEPT_DROP.items()):
        back = ""
        if cap in CRIT.CONCEPT_OFF:
            back = CRIT.CONCEPT_OFF[cap][1]
        rows.append({"COLUMN": col, "CAPABILITY": cap, "WHY": why, "COMES_BACK": back})
    return pd.DataFrame(rows)


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

    # --- (a) WHERE GRAVITY GENUINELY FAILS ----------------------------------------------
    s_min = CRIT.table11(SCREEN_DN)
    terminals, basis = legal_terminals(g)
    subnet_of, sub_basis = subnet_labels(g)
    _log(f"legal terminals: {basis}")
    _log(f"subnetwork labels: {sub_basis}")
    _log(f"depth-debt field at the DN{SCREEN_DN} minimum {s_min*1000:.2f} mm/m "
         "(G203-p29 Table 11), cover budget "
         f"{GRAVITY_BUDGET_M:.2f} m = MAX_COVER {CRIT.MAX_COVER:.2f} less MIN_COVER "
         f"{CRIT.MIN_COVER_CROWN:.2f} (G203-p33)")
    gf0 = gravity_failure(g, terminals, s_min, GRAVITY_BUDGET_M, basis)
    s0 = gf0.summary()
    _log(f"NO STATION PLACED YET: {s0['served']:,} nodes reach a terminal on gravity, "
         f"{s0['failed']:,} FAIL ({100.0 - s0['pct_gravity_ok']:.1f} %), "
         f"{s0['orphan']:,} have no corridor route to any terminal at all")
    if s0["orphan"]:
        _log(f"    the {s0['orphan']:,} orphans are a CONNECTIVITY finding, not a pumping "
             "one - reported in `failure`, never absorbed into the station count")

    # HOW MUCH OF THE COUNT IS THE SCREEN'S OWN CONSERVATISM? Bracket it. The screen charges
    # every corridor the DN200 minimum, 5.00 mm/m - the STEEPEST row of G203-p29 Table 11 -
    # because no reach has a diameter until the levels stage runs. On a main or a trunk the
    # minimum falls to 0.75 mm/m (DN900 and above), which is BELOW the ground's own 2.24 mm/m
    # average fall, so a large pipe accumulates no debt at all. The two runs bracket the truth
    # and the real answer sits between them. BOTH ARE RUN THROUGH THE SAME SEARCH, so the
    # bracket is a bracket on the same quantity and not on two different ones.
    brackets = []
    for dn_b in (SCREEN_DN, 900):
        sb = CRIT.table11(dn_b)
        _sites, _gf, _tr, _r = search_sites(g, terminals, sb, GRAVITY_BUDGET_M, subnet_of)
        brackets.append({"screen_dn": dn_b, "s_min_mm_m": round(sb * 1000, 2),
                         "stations": len(_sites), "rounds": len(_r),
                         "failed_left": _gf.n_failed})
        _log(f"    bracket DN{dn_b} at {sb*1000:.2f} mm/m -> {len(_sites):,} stations")
    _log("    the DN200 run is the CEILING on the station count and the DN900 run the FLOOR; "
         "the levels stage decides where between them the design lands")

    # --- (b) THE SEARCH, and (d) the trade stated with both numbers ----------------------
    sites, gf, trades, rounds = search_sites(g, terminals, s_min, GRAVITY_BUDGET_M, subnet_of,
                                             cover_tol=COVER_TOL, basis=basis)
    _log(f"SEARCH: {len(rounds)} rounds -> {len(sites):,} sites, {gf.n_failed:,} nodes still "
         f"failing, {len(trades)} recorded trade(s) between capture and main length")
    for r in rounds[:12]:
        _log(f"    round {r['round']}: {r['candidates']:,} candidates, "
             f"failed {r['failed_before']:,} -> {r['failed_after']:,}; {r['NOTE'][:110]}")
    sens = cover_tol_sensitivity(g, terminals, s_min, GRAVITY_BUDGET_M, subnet_of)
    for row in sens:
        _log(f"    COVER_TOL {row['cover_tol']:.2f}: {row['stations']:,} stations, "
             f"{row['total_main_m']:,.0f} m of rising main "
             f"({row['trades']} trade(s))  <- the tuned number, published not hidden")

    # --- the demands, and the PRUNE that makes the two counts agree ----------------------
    design_nodes = _design_nodes()
    demands = None if use_standin else demands_from_design()
    n0 = 0
    pruned: List[dict] = []
    if demands:
        source = "levels stage (W12.gpkg nodes), RE-TESTED and pruned here"
        n0 = len(demands)
        _log(f"{n0} stations located by the levels stage - re-testing every one against the "
             "gravity-failure field above (the fix for 's7 reads a pre-prune list')")
        demands, pruned = demands_retested(g, gf0, demands, subnet_of)
        _log(f"    {len(pruned)} pruned as redundant or empty, {len(demands)} demanded")
        gf = gravity_failure(g, list(terminals) + [d.site.node for d in demands],
                             s_min, GRAVITY_BUDGET_M, basis)
    else:
        source = "SEARCH (s7 screen - NOT a design)"
        _log("no station nodes in the design - siting from the SEARCH")
        sites, pruned = prune_redundant(g, sites, terminals, s_min, GRAVITY_BUDGET_M)
        n0 = len(sites) + len(pruned)
        _log(f"    prune: {len(pruned)} removed of {n0} -> {len(sites)} demanded "
             "(inheritance row 4: anything a pass can ADD, a later pass must TAKE AWAY)")
        gf = gravity_failure(g, list(terminals) + [s.node for s in sites],
                             s_min, GRAVITY_BUDGET_M, basis)
        demands = demands_from_sites(g, gf, sites, subnet_of)
    # THE LAST PASS, on the MEASURED catchment. Scored capture and measured catchment can
    # differ on a meshed network, and a station that owns nothing after the measurement is
    # W11b's defect exactly - so the measurement gets the last word and the removal is
    # counted into the same funnel.
    demands, empty = drop_empty_catchments(demands)
    pruned.extend(empty)
    if empty:
        sites = [s for s in sites if s.node in {d.site.node for d in demands if d.site}]
        # AND THE FIELD MUST FOLLOW THE REMOVAL. `gf` still had the dropped stations in it as
        # zero-debt sources, so `gf.served` - which is the candidate set every rising main is
        # routed into - counted nodes that were only inside the cover budget BECAUSE of a
        # station that no longer exists. A main discharging into one of those lands on ground
        # that does not drain, which is the loop-guard defect from the other end. Recomputed
        # here so the debt, the owner map and the discharge candidates all describe the same
        # set of stations.
        gf = gravity_failure(g, list(terminals) + [d.site.node for d in demands
                                                   if d.site is not None],
                             s_min, GRAVITY_BUDGET_M, basis)
    n1 = len(demands)
    for p in pruned:
        _log(f"    REMOVED node {p['node']}: {p['WHY'][:120]}")

    # --- design each station -----------------------------------------------------------
    st_rows: List[dict] = []
    rm_rows: List[dict] = []
    refused: List[dict] = []
    reporting: List[dict] = []
    cascades: List[dict] = []
    st_geom: List[Point] = []
    rm_geom: List[LineString] = []

    debt, par = gf.debt, gf.par
    reach = np.isfinite(debt)          # candidate ground for moving a station off wet ground
    station_nodes = [int(d.site.node) if d.site is not None else g.nearest(d.x, d.y)
                     for d in demands]
    # WHICH STATION OWNS EACH NODE'S GRAVITY FLOW - the LOOP GUARD's input. A node can be
    # inside the cover budget precisely BECAUSE this station is there; discharging into such a
    # node would send the flow straight back to the pump. H15 says the network is a forest, so
    # a station may only discharge into a node whose gravity owner is somebody else.
    owner = serving_station(g, par, station_nodes)
    n_series = stations_in_series(g, par, station_nodes)
    works_node = g.nearest(*STP_XY)

    for n_i, d in enumerate(demands, start=1):
        node = station_nodes[n_i - 1]

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
                    # THE SEWER HAS TO GET THERE. Moving a station off wet ground moves the
                    # POINT gravity arrives at, so the incoming sewer runs `moved_m` further
                    # and its invert falls with it - at the Table 11 minimum for its bore, the
                    # same arithmetic `depth_debt()` charges every corridor (G203-p29). The
                    # old code moved x, y and GRD_M and left INV_M standing at the level of a
                    # node up to SITE_SEARCH_M away, so the station published a ground level
                    # from one place and the invert below it from another - and INV_M is the
                    # bottom of LIFT_M, so the error went straight into the head, the pump
                    # and every number downstream of them.
                    d.invert_in_m = float(d.invert_in_m) - s_min * moved_m
                    sit = pumping.site_station(d.x, d.y, d.ground_m, grids,
                                               max_search_m=SITE_SEARCH_M)
        if not sit.publishable:
            refused.append({"IDENT": d.ident, "X": round(d.x, 2), "Y": round(d.y, 2),
                            "Q_PK_LS": round(d.q_peak_ls, 2),
                            "WHY": "G203-p38 sec 7.2 siting", "DETAIL": sit.verdict[:400]})
            continue

        # ---- THE DISCHARGE CHAMBER. A RISING MAIN LIFTS TO THE NEAREST POINT WHERE GRAVITY
        #      RESUMES, NOT TO THE WORKS (concept rule 6, philosophy sec 6). The candidate set
        #      is the nodes that can themselves reach a legal terminal on gravity, so the main
        #      always ends where a gravity sewer takes over; the loop guard removes the ones
        #      that only qualify BECAUSE this station is there. W11a had no answer here at all
        #      and published zero rising mains.
        cands = _discharge_candidates(g, gf, node, owner, n_series,
                                      guard_node=station_nodes[n_i - 1])
        if not cands:
            refused.append({"IDENT": d.ident, "X": round(d.x, 2), "Y": round(d.y, 2),
                            "Q_PK_LS": round(d.q_peak_ls, 2),
                            "WHY": "no gravity discharge reachable",
                            "DETAIL": "no corridor route from this station to any node that "
                                      "can itself reach a legal terminal on gravity WITHOUT "
                                      "draining back through this station (H15 loop guard). "
                                      "Resolutions: a "
                                      "satellite works (philosophy sec 8a), a cascade to a "
                                      "neighbouring station, or not serving. NOT a longer "
                                      "main chosen silently."})
            continue
        best = pumping.rank_discharge(cands)[0]
        # DS_TYPE - what the main actually ends at, MEASURED not assumed. 'stp' only where the
        # chosen chamber IS the works; everything else is a manhole where gravity resumes. The
        # share ending at 'stp' is published, because the built 10.0 km main straight to the
        # works is a critique and not a model.
        ds_type = "stp" if int(best["node"]) == int(works_node) else "manhole"
        # DOES THIS MAIN LAND IN A CASCADE? Philosophy sec 6, revised 2026-09-06: "A STATION
        # NEVER PUMPS INTO ANOTHER STATION... Cascading is a symptom of bad siting at every
        # separation." `contract` refuses only a main whose DS_TYPE is a STATION, and this one
        # is a manhole - but if the flow leaving that manhole still passes a station, the
        # objection holds in substance. So it is neither silently allowed nor silently
        # refused: it is COUNTED, published in `provenance` and the `cascades` table, printed
        # by `_report`, and carried per row as COMM_PT = 0. Refusing it outright here would
        # leave the catchment with no answer at all, which concept rule 7 forbids more
        # strongly than it forbids a cascade.
        if int(best.get("stations_in_series", 0)) > 0:
            cascades.append({"IDENT": d.ident, "DS_NODE_IDX": int(best["node"]),
                             "STATIONS_IN_SERIES_AT_LEAST": int(best["stations_in_series"]),
                             "MAIN_M": round(float(best["route_length_m"]), 1)})
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
        ds_uid = _discharge_uid(g, design_nodes, int(best["node"]), n_i)

        # NAMING, concept rule 8. A station is a SEAM between subnetworks, not a member of
        # one, so SUBNET is blank by rule and the name carries no S-token: I-PMP02, I-P02.
        # The town letter is the first town DOWNSTREAM of it - which is why naming can only
        # run here, after the discharge chamber is known.
        town = town_of_node(design_nodes, ds_uid)
        st_name = contract.concept_name(town, "pump", seq=n_i) if town else ""
        rm_name = contract.concept_name(town, "main", seq=n_i) if town else ""

        row = S.station_row()
        row.update({
            "NODE_UID": uid,
            "NODE_REF": f"{d.ident}-PS",
            "NAME": st_name, "TOWN": town, "SUBNET": "",
            # FLOOD_LV: G203-p38 sec 7.2 wants the 1:50 LEVEL and no level is derivable from
            # a hazard-CLASS grid. NaN, deliberately, and reported as a blocking gap. See
            # BLOCKING at the end of the run. Inventing one would be the exact failure this
            # project keeps retracting.
            "FLOOD_LV": np.nan,
            "INV_M": round(float(d.invert_in_m), 3),
            # THE EVIDENCE THAT THE POSITION WAS CHOSEN, NOT TRIGGERED. N_SUBNET = 0 is a
            # blocking failure and never reaches this point: `prune_redundant()` removes it
            # and `verify()` fails the published file if one ever survives.
            "N_SUBNET": int(d.n_subnet),
            "CATCH_KM": round(float(d.catch_km), 3),
            "RM_EDGE": eid,
            "COMM_PT": int(best["commissions_package"]),
            "SRC": d.src, "CONFIDENCE": d.confidence, "STAGE": STAGE,
            "MOVED_M": round(moved_m, 1),
            "DEBT_M": round(float(debt[node]), 2),
        })
        st_rows.append(_drop_switched_off(row))
        st_geom.append(Point(d.x, d.y))

        mrow = S.main_row()
        mrow.update({
            "EDGE_UID": eid, "US_NODE": uid, "DS_NODE": ds_uid, "STATION": uid,
            "NAME": rm_name, "TOWN": town, "SUBNET": "",
            "DS_TYPE": ds_type,
            "SRC": d.src, "CONFIDENCE": d.confidence, "STAGE": STAGE,
            "WADI_M": round(wadi_m, 1),
            "N_ISOL": S.main.n_isolation,
            "AIRV_DN": S.main.air_valve_dn,
            "WASH_DN": S.main.washout_dn,
        })
        rm_rows.append(_drop_switched_off(mrow))
        rm_geom.append(line)

        reporting.append({"IDENT": d.ident, "NODE_UID": uid,
                          "NOTE": " || ".join(S.reporting)})

    # --- publish -----------------------------------------------------------------------
    stations = gpd.GeoDataFrame(pd.DataFrame(st_rows), geometry=st_geom, crs=CRS) \
        if st_rows else gpd.GeoDataFrame(columns=["NODE_UID"], geometry=[], crs=CRS)
    mains = gpd.GeoDataFrame(pd.DataFrame(rm_rows), geometry=rm_geom, crs=CRS) \
        if rm_rows else gpd.GeoDataFrame(columns=["EDGE_UID"], geometry=[], crs=CRS)

    # THE ONE FUNNEL. Every station count printed, stored or returned by this stage reads
    # this dict and nothing else recomputes one (inheritance row 10).
    funnel = station_funnel(n0, n1, len(stations), source=source,
                            removed=len(pruned), refused=len(refused))
    _log(f"FUNNEL  N0 considered {funnel['N0_considered']:,} -> "
         f"N1 demanded {funnel['N1_demanded']:,} -> "
         f"N2 published {funnel['N2_published']:,}   "
         f"(pruned {funnel['pruned']:,}, refused {funnel['refused']:,})")

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

    # A STATION WITH NOTHING DRAINING INTO IT IS A BLOCKING FAILURE, NOT A WARNING. It should
    # be impossible - `prune_redundant()` removes it before the design runs - so this is the
    # belt to that brace, stated here as well as in `verify()` because the two answer
    # different questions: "did the stage let one through?" and "is one in the file?".
    if len(stations) and "N_SUBNET" in stations.columns:
        empty = pd.to_numeric(stations.N_SUBNET, errors="coerce").fillna(0) <= 0
        if empty.any():
            blocking.append({"LAYER": "stations",
                             "DETAIL": f"{int(empty.sum())} PUBLISHED STATIONS HAVE NOTHING "
                                       "DRAINING INTO THEM (N_SUBNET = 0). 15 of W11b's 47 "
                                       "were like this. The prune should have removed them - "
                                       "if one is here, prune_redundant() has a bug."})
    # NAMING is the publication gate, and it can only be met where a town is knowable - an
    # element outside a town takes the letter of the first town DOWNSTREAM of it, so a screen
    # run with no published design has nothing to take. Reported either way, never skipped.
    for name, gdf in (("stations", stations), ("rising_mains", mains)):
        if not len(gdf):
            continue
        try:
            contract.assert_named(gdf, name, stage=STAGE)
            _log(f"contract.assert_named({name}): PASS")
        except Exception as e:
            blocking.append({"LAYER": f"{name} (naming)", "DETAIL": str(e)[:1200]})

    PUMPS_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if PUMPS_GPKG.exists():
        PUMPS_GPKG.unlink()
    stations.to_file(PUMPS_GPKG, layer="stations", driver="GPKG")
    mains.to_file(PUMPS_GPKG, layer="rising_mains", driver="GPKG")

    prov = _provenance(source, g, gf, stations, mains, refused, brackets, funnel, sens,
                       cascades)
    import sqlite3
    con = sqlite3.connect(PUMPS_GPKG)
    try:
        prov.to_sql("provenance", con, if_exists="replace", index=False)
        funnel_frame(funnel).to_sql("funnel", con, if_exists="replace", index=False)
        pd.DataFrame([gf0.summary(), gf.summary()], index=["before_stations", "after"]) \
            .reset_index().rename(columns={"index": "WHEN"}) \
            .to_sql("failure", con, if_exists="replace", index=False)
        pd.DataFrame(refused or [{"IDENT": "", "WHY": "none", "DETAIL": ""}]) \
            .to_sql("refused", con, if_exists="replace", index=False)
        pd.DataFrame(reporting or [{"IDENT": "", "NOTE": ""}]) \
            .to_sql("reporting", con, if_exists="replace", index=False)
        pd.DataFrame(blocking or [{"LAYER": "", "DETAIL": "none"}]) \
            .to_sql("blocking", con, if_exists="replace", index=False)
        pd.DataFrame(pruned or [{"node": -1, "WHY": "none removed"}]) \
            .to_sql("pruned", con, if_exists="replace", index=False)
        pd.DataFrame(trades or [{"round": 0, "NOTE": "no trade: the maximum-capture site was "
                                                     "also the shortest main every round"}]) \
            .to_sql("trades", con, if_exists="replace", index=False)
        pd.DataFrame(sens).to_sql("sensitivity", con, if_exists="replace", index=False)
        # the sites actually DEMANDED, not the search's independent answer - in a design run
        # those are two different lists and publishing the wrong one is how a table comes to
        # disagree with the layer beside it
        pd.DataFrame([d.site.as_row() for d in demands if d.site is not None]
                     or [{"node": -1}]) \
            .to_sql("sites", con, if_exists="replace", index=False)
        pd.DataFrame([s.as_row() for s in sites] or [{"node": -1}]) \
            .to_sql("search_sites", con, if_exists="replace", index=False)
        pd.DataFrame(rounds).to_sql("search", con, if_exists="replace", index=False)
        pd.DataFrame(brackets).to_sql("screen_bracket", con, if_exists="replace", index=False)
        pd.DataFrame(cascades or [{"IDENT": "", "STATIONS_IN_SERIES_AT_LEAST": 0,
                                   "MAIN_M": 0.0}]).to_sql(
            "cascades", con, if_exists="replace", index=False)
        _assumption_table().to_sql("assumptions", con, if_exists="replace", index=False)
        concept_off_table().to_sql("concept_off", con, if_exists="replace", index=False)
        _conflict_table().to_sql("conflicts", con, if_exists="replace", index=False)
    finally:
        con.close()

    R = {
        "stage": STAGE, "version": STAGE_VERSION, "source_of_stations": source,
        "seconds": round(time.time() - t0, 1),
        "funnel": funnel,
        # ONE number, read from the funnel. Nothing here recounts.
        "n_stations": funnel["N2_published"], "n_mains": len(mains),
        "n_refused": funnel["refused"], "n_pruned": funnel["pruned"],
        "gpkg": str(PUMPS_GPKG), "blocking": blocking,
    }
    (RUN / "s7_pumps.json").write_text(json.dumps(R, indent=2, default=str), encoding="utf-8")
    grids.close()

    _report(stations, mains, refused, blocking, source, funnel, trades, sens, cascades)
    _log(f"done in {R['seconds']:.0f} s -> {PUMPS_GPKG}")
    return R


# ======================================================================================
# 7. REPORTING
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
              "station nodes."),
             ("SCREEN_ARRIVAL_INVERT", "ground - MAX_COVER",
              "s7 SCREEN only: a site chosen by the search is at the FOOT of a climb where "
              "the gravity budget is exhausted, so the incoming sewer is assumed to arrive "
              "at the cover cap - INV_M = GRD_M - MAX_COVER (12.00 m, G203-p33). Two things "
              "a reader must know. It makes GRD_M - INV_M a CONSTANT 12.00 m on every screen "
              "station, so that difference is an assumption and not a measurement; and "
              "MAX_COVER is cover to the CROWN, so the true invert is one outside diameter "
              "deeper and the screen's LIFT_M is correspondingly conservative. Both go away "
              "the moment the levels stage publishes station nodes, which carry the real "
              "INV_M."),
             ("COVER_TOL", COVER_TOL,
              "s7 SEARCH: the band inside which two candidate sites count as equivalent on "
              "capture and are decided on the LENGTH OF THEIR RISING MAIN instead. The one "
              "tuned number in the stage, and it is published rather than hidden - the "
              "`sensitivity` table reruns the whole search at "
              f"{', '.join(f'{t:g}' for t in COVER_TOL_SCAN)} and gives station count "
              "against total main length for each."),
             ("TOPK_MAINS", TOPK_MAINS,
              "s7 SEARCH: how many of the best-covering candidates get a routed rising main "
              "during scoring. Routing is one Dijkstra apiece and the frontier can be "
              "hundreds wide, so the capture-versus-main trade is evaluated on the leaders. "
              "The CHOSEN site's main is re-routed against the final field before publishing."),
             ("DISCHARGE_MATCH_M", DISCHARGE_MATCH_M,
              "s7: how far a published chamber may sit from the corridor node a rising main "
              "was routed to and still BE that chamber. The corridor graph and the design use "
              "different id spaces, so DS_NODE is resolved by coordinate - and a DS_NODE that "
              "resolves to no row schedules nothing (the CROSS_ID defect). IT DOES NOT RULE "
              "OUT A JUMP TO THE NEIGHBOURING CHAMBER: the built median spacing is 29.77 m, "
              "so the half-span that would make the match unique is 14.9 m and this is 25. "
              "Tighten to half our own published median once s6 has run."),
             ("MAX_SEARCH_ROUNDS", MAX_SEARCH_ROUNDS,
              "s7 SEARCH: a guard, not a target. Each round places one station and strictly "
              "shrinks the failed set, so the search terminates on its own; hitting this is "
              "reported in the `search` table as a GUARD row.")]
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "NOTE"])


def _conflict_table() -> pd.DataFrame:
    return pd.DataFrame([(k, v) for k, v in PUMP.CONFLICTS.items()],
                        columns=["CONFLICT", "WHAT_W12_DOES"])


def _provenance(source, g, gf, stations, mains, refused,
                brackets=(), funnel=None, sens=(), cascades=()) -> pd.DataFrame:
    f = funnel or {}
    s = gf.summary()
    rows = [
        ("stage_version", STAGE_VERSION, "", ""),
        ("source_of_stations", source, "",
         "the levels stage where it has published, otherwise the s7 SEARCH, which is a "
         "screen and NOT a design. The list is RE-TESTED and pruned either way"),
        ("terminal_basis", gf.basis, "",
         "[MEASURED] which published layer said where a gravity sewer may legally END. A "
         "terminal is legal if it is the Main Pipe or a station with a designed rising main "
         "(_BRAIN/10_ASBUILT_CALIBRATION.md T1)"),
        ("corridors_km", round(g.L.sum() / 1000, 1), "km", "[MEASURED] s1 PIPE_OK network"),
        ("corridors_on_wadi_km", round(g.L[g.wadi].sum() / 1000, 1), "km",
         f"[MEASURED] hazard class {CRIT.HAZARD_WADI_CLASSES} at 1:50"),
        ("gravity_budget_m", round(GRAVITY_BUDGET_M, 2), "m",
         "[G203-p33] MAX_COVER less MIN_COVER"),
        ("screen_smin_mm_m", round(CRIT.table11(SCREEN_DN) * 1000, 2), "mm/m",
         f"[G203-p29 Tab 11] DN{SCREEN_DN}"),
        ("nodes_reachable", s["served"] + s["failed"], "", "[MEASURED]"),
        ("nodes_orphan", s["orphan"], "",
         "[MEASURED] NO corridor route to any legal terminal. A CONNECTIVITY finding, named "
         "with its size and never absorbed into the station count (concept rule 7)"),
    ] + [
        (f"bracket_DN{b['screen_dn']}_stations", b["stations"], "stations",
         f"[MEASURED] the SAME search at {b['s_min_mm_m']} mm/m ({b['rounds']} rounds). The "
         "DN200 run is the CEILING on the station count (steepest Table 11 minimum, charged "
         "to every corridor); the DN900 run is the FLOOR (0.75 mm/m, below the ground's own "
         "2.24 mm/m average fall, so a large pipe accrues no debt). One quantity, two "
         "assumptions - not two quantities") for b in brackets
    ] + [
        (f"sensitivity_cover_tol_{r['cover_tol']:g}",
         f"{r['stations']} stations / {r['total_main_m']:,.0f} m main", "",
         "[MEASURED] FEWEST STATIONS against SHORTEST MAIN, both numbers, at the coverage "
         "tolerance named. COVER_TOL is the one tuned number in this stage and this row is "
         "why it is not a hidden choice") for r in sens
    ] + [
        ("nodes_gravity_ok", s["served"], "",
         "[MEASURED] reach a legal terminal within the cover budget WITH the stations in"),
        ("pct_gravity_ok", s["pct_gravity_ok"], "%",
         "[MEASURED] the complement is what forces stations"),
        ("nodes_still_failing", s["failed"], "",
         "[MEASURED] not served on gravity and not covered by a station. Non-zero is a FLAG "
         "with a size, never a silent drop"),
        ("N0_considered", f.get("N0_considered", len(stations)), "stations",
         "[FUNNEL] what the provider offered, before any test of this stage's"),
        ("N1_demanded", f.get("N1_demanded", len(stations)), "stations",
         "[FUNNEL] after the search and the prune. THE NUMBER TO QUOTE"),
        ("N2_published", f.get("N2_published", len(stations)), "stations",
         "[FUNNEL] after refusals. station_funnel() is the ONE function that produces a "
         "station count here - W11b shipped 14 and 47 because two functions did "
         "(inheritance row 10)"),
        ("n_pruned", f.get("pruned", 0), "stations",
         "[FUNNEL] removed because the survivors already covered their catchment. "
         "Inheritance row 4: anything a pass can ADD, a later pass must TAKE AWAY, and the "
         "stage publishes how many it removed"),
        ("n_rising_mains", len(mains), "", "[DESIGNED]"),
        ("mains_landing_in_a_cascade", len(cascades), f"of {len(mains)}",
         "[MEASURED] mains whose discharge chamber is a manhole, but whose flow STILL passes "
         "another station on the way out. Philosophy sec 6 (revised 2026-09-06): 'A STATION "
         "NEVER PUMPS INTO ANOTHER STATION... cascading is a symptom of bad siting at every "
         "separation' - which REVERSED the old 'cascade within 1.5 km' rule. contract refuses "
         "only a main whose DS_TYPE is a station, so this is the count that says whether the "
         "SUBSTANCE of the rule held. Non-zero is a finding with a size, not a pass, and the "
         "figure is a LOWER BOUND: the debt tree stops at a station, so a cascade three deep "
         "reads as one. See the `cascades` table"),
        ("n_refused", len(refused), "",
         "[DESIGNED] refused rather than published - see the `refused` table"),
        ("why_few_large_stations", "manning 86 %, energy 0.4 %", "",
         "[INHERITANCE ROW 25, the FINDING - the arithmetic is switched off] Station cost "
         "correlates 0.99 with power and 0.72 with head, and manning is per STATION whatever "
         "its size. Twenty small stations cost about twenty times one large one however "
         "little each lifts, and the 2006 designer put ONE station in 95.45 km. That finding "
         "is what the search optimises; life-cycle COSTING is criteria.CONCEPT_OFF["
         "'life_cycle_cost'] and no present value is computed or published here"),
        ("tau_flag", CRIT.TAU_PA, "Pa", CRIT.tau_banner().splitlines()[0]),
        ("flood_level_test", "UNEVALUABLE", "",
         "G203-p38 sec 7.2 needs the 1:50 flood LEVEL for the 300 mm freeboard. The project "
         "holds hazard CLASSES. DATA REQUEST to NWS. Reported as a failure, not a blank"),
        ("philosophy_citation_defect", "1:100 -> 1:50", "",
         pumping.PHILOSOPHY_CITATION_DEFECT[:600]),
        ("concept_off", ", ".join(sorted({c for c, _w in CONCEPT_DROP.values()})), "",
         "columns computed by w12.pumping and DROPPED here by name - see the `concept_off` "
         "table. Motor selection and life-cycle costing are switched off at concept"),
    ]
    if len(stations):
        for col, unit in (("Q_DUTY_LS", "L/s"), ("LIFT_M", "m"), ("WELL_M3", "m3"),
                          ("CATCH_KM", "km"), ("N_SUBNET", "-")):
            if col in stations.columns:
                sv = pd.to_numeric(stations[col], errors="coerce")
                rows.append((f"{col}_median", round(float(sv.median()), 2), unit, "[DESIGNED]"))
                rows.append((f"{col}_max", round(float(sv.max()), 2), unit, "[DESIGNED]"))
    if len(mains):
        rows.append(("rising_main_km", round(float(mains.LEN_M.sum()) / 1000, 2), "km",
                     "[DESIGNED] total published rising main - W11a published zero"))
        rows.append(("rising_main_longest_m", round(float(mains.LEN_M.max()), 0), "m",
                     "[DESIGNED] against the built network's 9,993 m, which is a CRITIQUE and "
                     "not a model: it exists because in 2006 there was no gravity network to "
                     "receive a shorter lift"))
        if "DS_TYPE" in mains.columns:
            to_stp = int((mains.DS_TYPE.astype(str) == "stp").sum())
            rows.append(("mains_ending_at_the_works", to_stp, "of "
                         f"{len(mains)}",
                         "[MEASURED] concept rule 6: a rising main lifts to the NEAREST point "
                         "where gravity resumes, NOT to the works. This is the count that "
                         "says whether the rule held, published rather than claimed"))
        if "RETENT_M" in mains.columns:
            rt = pd.to_numeric(mains.RETENT_M, errors="coerce")
            rows.append(("retention_max_min", round(float(rt.max()), 1), "min",
                         "[DESIGNED] retention in the main. G203-p50 wants under "
                         f"{CRIT.FM_RETENTION_MIN:g} min; a long force main is anaerobic by "
                         "definition and its discharge chamber is a septicity design"))
        rows.append(("rising_main_on_wadi_km",
                     round(float(pd.to_numeric(mains.get("WADI_M", 0),
                                               errors="coerce").fillna(0).sum()) / 1000, 2),
                     "km", "[MEASURED] on the chosen routes; G201 sec 9.3 register applies"))
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "NOTE"])


def _report(stations, mains, refused, blocking, source, funnel=None, trades=(),
            sens=(), cascades=()) -> None:

    # COMPUTED FROM THE PUBLISHED MAINS, never typed. See finding 3.
    def _below(col, lim=0.75):
        return int((mains[col].astype(float) < lim).sum()) if col in getattr(mains, "columns", []) else -1
    n_mains = len(mains)
    n_1pump = _below("V_1PUMP")
    n_vmin  = _below("V_MIN_MS")
    n_duty  = (int(((mains["V_DUTY_MS"].astype(float) < 0.75) |
                    (mains["V_DUTY_MS"].astype(float) > 2.5)).sum())
               if "V_DUTY_MS" in getattr(mains, "columns", []) else -1)
    print("\n" + "=" * 86)
    print(f"  STAGE 7 - PUMPING STATIONS AND FORCE MAINS   (stations from: {source})")
    print("=" * 86)
    print(CRIT.concept_banner())
    if funnel:
        print("\n-- THE STATION COUNT, and its funnel (one function, inheritance row 10) --")
        print(f"  N0 considered {funnel['N0_considered']:,}"
              f"  ->  N1 demanded {funnel['N1_demanded']:,}"
              f"  ->  N2 published {funnel['N2_published']:,}")
        print(f"     pruned {funnel['pruned']:,} (redundant, or nothing draining into them)"
              f" | refused {funnel['refused']:,} (siting or hydraulics)")
    if len(stations):
        # NO MOTOR SIZE AND NO LIFE-CYCLE COST - switched off at concept and dropped by name.
        # What a station publishes is its position, what it captures, and what it lifts.
        cols = [c for c in ("NAME", "TOWN", "NODE_REF", "ST_TYPE", "N_DUTY", "Q_DUTY_LS",
                            "GRD_M", "INV_M", "LIFT_M", "WELL_M3", "WW_STARTS", "WW_RET_MI",
                            "N_SUBNET", "CATCH_KM", "N_PROP", "LAND_M2", "COMM_PT")
                if c in stations.columns]
        print("\n-- stations: position, what it captures, what it lifts --")
        print(stations[cols].to_string(index=False))
    if len(mains):
        cols = [c for c in ("NAME", "EDGE_UID", "DS_TYPE", "DN", "MATERIAL", "LEN_M",
                            "V_DUTY_MS", "V_MIN_MS", "STAT_HD_M", "TOT_HD_M", "RETENT_M",
                            "N_AIRV", "N_WASH", "N_ISOL", "WADI_M") if c in mains.columns]
        print("\n-- rising mains: DS_TYPE says where gravity resumes --")
        print(mains[cols].to_string(index=False))
        if "DS_TYPE" in mains.columns:
            to_stp = int((mains.DS_TYPE.astype(str) == "stp").sum())
            print(f"  {len(mains) - to_stp} of {len(mains)} lift to the nearest MANHOLE where "
                  f"gravity resumes; {to_stp} run all the way to the works. Concept rule 6 - "
                  "the built 10.0 km main is a critique, not a model.")
    if len(mains):
        print(f"\n-- CASCADES: {len(cascades)} of {len(mains)} mains discharge into a "
              "chamber whose flow still passes another station --")
        if cascades:
            print(pd.DataFrame(cascades).to_string(index=False))
            print("  Philosophy sec 6 (2026-09-06): a station never pumps into another "
                  "station, and a cascade is a symptom of bad SITING at every "
                  "separation. Each row is a finding for the engineer, not a design "
                  "answer, and the count is a LOWER BOUND - the debt tree stops at a "
                  "station.")
        else:
            print("  none - every main lands where gravity carries the flow out "
                  "without passing another station.")
    if sens:
        print("\n-- FEWEST STATIONS vs SHORTEST MAIN: the trade, with both numbers --")
        print(pd.DataFrame(sens).to_string(index=False))
        print("  COVER_TOL is the one tuned number in this stage. It is published here rather "
              "than chosen quietly (philosophy sec 6: state the trade, do not resolve it).")
    if trades:
        print("\n-- per-round trades: where the chosen site was not the maximum-capture site --")
        print(pd.DataFrame(trades)[["round", "cover_km_given_up", "cover_chambers_given_up",
                                    "main_m_saved", "lift_m_delta"]].to_string(index=False))
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

  3. SELF-CLEANSING IN THE RISING MAINS - SETTLED BY THE ENGINEER, 2026-09-06.

     THE GOVERNING CASE IS ONE DUTY PUMP RUNNING, not the design-minimum inflow. The
     engineer's reasoning, and it is the physics: *"of course for when a pump is running -
     if the sewage is not enough, no flow can run in force pipes."* A fixed-speed pump
     delivers its duty or it delivers nothing. The wet well accumulates and the pump starts;
     the velocity in the main is set by PUMP DUTY and can never be set by inflow. A
     "velocity at the design-minimum inflow" is therefore a flow that never exists in the
     pipe - it is an arrival rate, not a pumped rate, and checking a main against it
     manufactures a failure out of a quantity the main never sees.

     Measured on the PUBLISHED mains, not typed:
""" + f"""       {n_mains} rising mains, one per station.
       below 0.75 m/s at ONE DUTY PUMP  (V_1PUMP,   the governing case): {n_1pump}
       below 0.75 m/s at design-minimum (V_MIN_MS,  published beside it): {n_vmin}
       duty velocity outside 0.75-2.5 m/s (V_DUTY_MS, G203-p26 / p50):    {n_duty}
""" + """
     BOTH COLUMNS STAY ON THE LAYER. V_MIN_MS is kept so the arrival-rate reading is
     visible and auditable, not deleted because it is inconvenient - but it does not gate.

     A PREVIOUS VERSION OF THIS BLOCK PRINTED "99 rising mains" AS A TYPED CONSTANT. There
     are 43 mains. The 99 was a stale count from before the prune, reported at the point of
     writing rather than computed from what was published - which is inheritance-ledger row
     10 and the same defect that put seven different station counts into circulation. The
     engineer caught it by noticing that a force main count cannot exceed the pump count.

     If a main ever DOES fall below the band at one duty pump, no diameter fixes it: a single
     main spans a flow ratio of only 2.5 / 0.75 = 3.33. The guideline's own answers are
     staged mains (G203-p50 sec 8.1, "two or more rising mains may be warranted"), twin mains
     with a dedicated hydraulic study (G203-p52 sec 8.2.3), or a scheduled flush.""")
    else:
        print("  none")
    print()


# ======================================================================================
# 8. THE AS-BUILT CALIBRATION CASE
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
    print(f"  DESIGNED HERE on an indicative 120 L/s peak / 40 L/s average "
          f"(the 5A-1 duty is NOT recorded anywhere, so this is an ILLUSTRATION):")
    print(f"    {st.name}, {st.n_duty} duty + {st.n_standby} standby   (G203-p40 Table 17)")
    print(f"    rising main DN{fm.dn} {fm.material}, v_duty {fm.v_duty_ms:.2f} m/s, "
          f"v at design-minimum {fm.v_min_ms:.2f} m/s")
    print(f"    static {fm.static_lift_m:+.1f} m + friction {fm.hf_duty_m:.1f} m "
          f"+ minor {fm.hminor_duty_m:.1f} m = {fm.total_head_m:.1f} m total")
    print(f"    retention in the main {fm.retention_min:.0f} min "
          f"(G203-p50 wants under {CRIT.FM_RETENTION_MIN:.0f}) - and THIS is the number that "
          "makes the built 10.0 km main a critique rather than a model")
    print("    NO MOTOR AND NO LIFE-CYCLE COST: both are criteria.CONCEPT_OFF, and neither "
          "moves the only question this calibration answers - WHY they pumped at all.")
    for n in fm.notes:
        print(f"    NOTE: {n}")
    print()


# ======================================================================================
# 9. VERIFY / REPORT / CLI
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
    # A STATION WITH NOTHING DRAINING INTO IT IS BLOCKING, NOT A WARNING. 15 of W11b's 47.
    chk("no station has nothing draining into it (N_SUBNET > 0)",
        len(st) == 0 or ("N_SUBNET" in st.columns
                         and (pd.to_numeric(st.N_SUBNET, errors="coerce").fillna(0) > 0).all()),
        "15 of W11b's 47 stations captured nothing; prune_redundant() removes them and this "
        "fails the published file if one ever survives")
    chk("every station says how much network it captures (CATCH_KM > 0)",
        len(st) == 0 or ("CATCH_KM" in st.columns
                         and (pd.to_numeric(st.CATCH_KM, errors="coerce").fillna(0) > 0).all()),
        "a station that captures no kilometres cannot be scored against its lift, which is "
        "the whole of the 'position is chosen, not triggered' test")
    chk("CATCH_KM is not constant across the stations",
        len(st) < contract.VARY_MIN_ROWS or "CATCH_KM" not in st.columns
        or st.CATCH_KM.nunique() > 1,
        "a published column that is constant where it should vary is a fabrication "
        "(inheritance row 22)")
    chk("no rising main exceeds the 2.5 m/s force-main maximum (G203-p50, NOT the 3.0 m/s "
        "gravity maximum of G203-p27)",
        len(rm) == 0 or (pd.to_numeric(rm.V_DUTY_MS, errors="coerce")
                         <= CRIT.FM_V_MAX + 1e-6).all(),
        f"cap read from criteria.FM_V_MAX = {CRIT.FM_V_MAX:g} m/s; the gravity maximum is "
        f"{CRIT.V_MAX:g} m/s and the two have been conflated on this project before")
    chk("no rising main below the 75 mm ID floor (G203-p50)",
        len(rm) == 0 or (pd.to_numeric(rm.DN, errors="coerce") >= 80).all())
    chk("every rising main declares where it discharges (DS_TYPE)",
        len(rm) == 0 or ("DS_TYPE" in rm.columns
                         and rm.DS_TYPE.astype(str).isin(contract.DS_TYPE).all()),
        "concept rule 6: a main lifts to the NEAREST point where gravity resumes, not to the "
        "works, and the share ending at 'stp' must be a number on the layer")
    chk("no motor size or life-cycle cost reached the published stations",
        len(st) == 0 or not (set(st.columns) & set(CONCEPT_DROP)),
        "motor selection and life-cycle costing are criteria.CONCEPT_OFF; the columns are "
        "dropped by name in CONCEPT_DROP and listed in the `concept_off` table")
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
    # THE FUNNEL AND THE FILE MUST AGREE. This is the check that would have caught W11b
    # shipping 14 demanded against 47 designed: the published station count is N2, and N2 is
    # what `station_funnel()` said, or one of the two is lying.
    try:
        import sqlite3
        con = sqlite3.connect(str(gpkg))
        try:
            fn = pd.read_sql("SELECT * FROM funnel", con)
        finally:
            con.close()
        n2 = int(fn.loc[fn.STEP == "N2_published", "VALUE"].iloc[0])
        chk("the published station count equals the funnel's N2", n2 == len(st),
            f"funnel N2 = {n2}, file holds {len(st)}. One quantity, one function "
            "(inheritance row 10) - W11b shipped 14 and 47 because two functions produced it")
    except Exception as e:                           # noqa: BLE001 - reported, never hidden
        chk("the published station count equals the funnel's N2", False,
            f"the `funnel` table could not be read ({e}). A check that cannot run is a "
            "FAILURE, not a blank (inheritance row 2)")
    return out


def report(gpkg: Path = PUMPS_GPKG) -> None:
    import sqlite3
    con = sqlite3.connect(gpkg)
    try:
        for t in ("provenance", "funnel", "failure", "search", "sites", "search_sites",
                  "trades", "sensitivity", "pruned", "cascades", "screen_bracket", "refused",
                  "blocking", "assumptions", "concept_off", "conflicts", "reporting"):
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
    ap.add_argument("--selftest", action="store_true", help="run w12.pumping's self-test")
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
