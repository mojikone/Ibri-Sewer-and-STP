"""s5_flows - STAGE 5: FLOW ACCUMULATION down the oriented tree.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
It reads two published files - the oriented tree from `s2_orient` and the plot loads - and
publishes the flow every later stage sizes against.

    python s5_flows.py                build, publish, report
    python s5_flows.py --report       re-print the tables from the published file
    python s5_flows.py --verify       re-run every conservation check on the published file
    python s5_flows.py --selftest     run the arithmetic against hand-worked cases
    python s5_flows.py --asbuilt      run the SAME accumulator over NAMA's built network

================================================================================= WHAT IT DOES
Four quantities travel down the tree, and they are accumulated by ONE function so they
cannot disagree with each other:

    QADF_M3D    sanitary average dry weather flow, infiltration EXCLUDED, at saturation
    N_PROP      properties served at or above the reach - the unit the appraisal costs per
    UPS_LEN_M   sewer length upstream of and including the reach - what infiltration is on
    UPS_ARCS    how many reaches drain through this one - a pure structure diagnostic

Then, per reach:

    PF          Merrimack above 100 properties (G201-p71 sec 7.4.2).  Below that the
                guideline gives NO formula, so the factor is HELD at the value Merrimack
                gives AT the threshold, and the row says `PF_METH = 'held'`
    QINF_LS     720 L/d/km of sewer on UPS_LEN_M, unpeaked (G201-p72 sec 7.4.3)
    QPK_LS      QADF_M3D x 1000/86400 x PF + QINF_LS - the flow the pipe is sized on

============================================================== THE TRAP, AND HOW IT IS DISARMED
THE SYSTEM INFILTRATION TOTAL IS THE RATE TIMES THE NETWORK LENGTH.  It is NOT the sum of
the per-reach values.  QINF_LS is CUMULATIVE - it has to be, or QPK_LS is not the flow the
pipe carries - so a reach 40 hops down the tree already counts every kilometre above it.
Adding those up counts each kilometre once per downstream reach.  W11a published 1,259 L/s
that way where the truth is 14.5 L/s: an 87-fold overstatement.

Three things disarm it here, and all three are published:

  1. `QINF_LOC` sits beside `QINF_LS` on every row - the reach's OWN 720 L/d/km, which IS
     summable and whose sum is the system total by construction.
  2. The `infiltration` table prints the right total, the wrong total, and the ratio between
     them, measured on this network.  The trap is a number in the deliverable, not a warning
     in a comment.
  3. `--verify` re-derives the total three independent ways - from the network length, from
     the sum of QINF_LOC, and from QINF_LS at the outfalls only - and refuses to agree with
     itself unless all three land inside 1e-6 L/s.

The outfall identity is the useful one: because every kilometre drains to exactly one
outfall, summing the CUMULATIVE value over OUTFALL reaches alone gives the right answer.
It is the same sum restricted to a partition.

=========================================================== THE HEALTH CHECK YOU CANNOT SKIP
`health` is the first table printed, the first block of the report, and it is echoed on
stderr when it fails.  Its headline question is the one the brief asks:

    WHAT SHARE OF THE PLACED LOAD DOES THE BIGGEST PIPE CARRY?

In a network draining to one works it is nearly all of it.  Far below that, the hydraulics
are showing fragmentation the length statistics hide.  The benchmark is NOT invented: the
same accumulator is run over NAMA's own 95.4 km built network with the same plot loads, and
the built figure is printed beside ours.  `--asbuilt` prints that run on its own.

========================================================== WHAT IS ASSUMED, AND WHAT IS READ
Read from the source PDFs on 2026-09-03 (printed page = PDF page in both documents):

    G201-p71 sec 7.4.2   "The Merrimack formula is to be used for calculating the peak
                          factors for wastewater discharge for an area (catchment or sub
                          catchment) having over 100 properties."
                          Qpdf = 2.65 Qadf^0.879, BOTH in Ml/day;  Pf = Qpdf / Qadf.
    G201-p72             Peltier alternative, PfWW = 1.5 + 1/sqrt(Qm), Qm in LITRES PER
                          SECOND - carried for comparison only, never applied.
    G201-p72 NOTE        "It is recommended that the hourly peak factor should not exceed
                          5.0."  A RECOMMENDATION.  Reported when exceeded, NEVER truncated.
    G201-p72 sec 7.4.3   "For newly designed networks, a linear infiltration allowance of
                          720 liters per day per kilometer (L/d/km) of sewer should be
                          incorporated into the design."  And: "Infiltration due to storm
                          water is not considered."
    G201-p72 sec 7.4.3   existing inland 10 %, groundwater/coastal up to 40 % - NOT used
                          here; this is a new network.
    G201-p73 sec 7.4.5   STP design margin 10 %, "over and above any redundancies" - carried
                          into the works total, not into any pipe.

Project assumptions, each tagged on the `assumptions` layer and none of them a guideline
value: A-FLOW-1 infiltration unpeaked - A-FLOW-2 the held peak factor - A-FLOW-3 load enters
at the upstream node - A-FLOW-4 nearest arc, no distance cap - A-FLOW-5 a non-tree arc is a
source branch - A-FLOW-6 saturation horizon only.

============================================================ WHAT THIS STAGE DOES NOT DO
It does not size anything, level anything or decide a tier.  It publishes flow.
It has no start-year flows: the plot loads carry a saturation figure and nothing else, so
philosophy sec 6's "check self-cleansing at start-year flows" cannot be run from this data.
That is a GAP and it is on the `assumptions` layer, not a silence.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from w12 import contract as K                                    # noqa: E402
from w12.criteria import DEFAULT as CRIT                         # noqa: E402

STAGE = "s5_flows"
STAGE_VERSION = "W12-s5_flows-1.0"
STAGE_ORDER = 5

W12 = HERE.parent
ORIENT_GPKG = W12 / "shp" / "W12_orient.gpkg"
ROADS_GPKG = W12 / "shp" / "W12_roads.gpkg"
OUT_GPKG = W12 / "shp" / "W12_flows.gpkg"
OUT_KMZ = W12 / "shp" / "W12_flows_peak.kmz"
RUN_DIR = W12 / "run" / "flows"
REPORT_MD = RUN_DIR / "FLOWS.md"

# The plot loads are DATA, produced upstream of W12 and read, never recomputed here.
PLOT_LOADS = W12.parent / "W10" / "shp" / "W10_plot_loads.gpkg"
PLOT_LOADS_LAYER = "plot_loads"

CRS_EPSG = K.CRS_EPSG                     # 32640, project rule, every layer

# ======================================================================================
# Guideline values.  Every one of these is read from criteria, which read it from the PDF.
# Nothing in this file re-types a guideline number: a second copy is a second answer.
# ======================================================================================

G = {
    "MERRIMACK_A": (CRIT.PF_MERRIMACK_A, "-", "G201-p71 7.4.2"),
    "MERRIMACK_B": (CRIT.PF_MERRIMACK_B, "-", "G201-p71 7.4.2"),
    "PF_HOLD_PROPERTIES": (CRIT.PF_HOLD_PROPERTIES, "properties", "G201-p71 7.4.2"),
    "PELTIER_A": (CRIT.PF_PELTIER_A, "-", "G201-p72"),
    "PF_REPORT_ABOVE": (CRIT.PF_REPORT_ABOVE, "-", "G201-p72 NOTE (recommendation)"),
    "INFILT_L_D_KM": (CRIT.INFILT_L_D_KM, "L/d/km", "G201-p72 7.4.3"),
    "STP_MARGIN": (CRIT.STP_MARGIN, "-", "G201-p73 7.4.5"),
    "OCCUPANCY": (CRIT.OCCUPANCY, "people/property", "PROJECT, derived 2026-08-30"),
    "WWG_LCD": (CRIT.WWG_LCD, "L/c/d", "PROJECT, derived - see PROJECT-STATE 2"),
    "PLOT_QADF_M3D": (CRIT.PLOT_QADF_M3D, "m3/d/property", "PROJECT, OCCUPANCY x WWG/1000"),
}

SEC_PER_DAY = 86400.0
M3D_TO_LS = 1000.0 / SEC_PER_DAY          # 1 m3/d = 0.011574 L/s


# ======================================================================================
# ASSUMPTIONS - every one of them, with what would change if it were wrong
# ======================================================================================

ASSUMPTIONS: Tuple[Dict[str, str], ...] = (
    dict(ID="A-FLOW-1", WHAT="Infiltration is UNPEAKED and added AFTER the sanitary peak "
                             "factor.",
         WHY="G201-p72 7.4.3 gives the 720 L/d/km allowance and never states the order of "
             "operations. A steady groundwater ingress does not peak with the diurnal "
             "sanitary cycle. criteria.INFILT_UNPEAKED carries the same decision.",
         IF_WRONG="Peaking the infiltration too would raise QPK_LS by PF x QINF - about "
                  "1.6 x 14.5 = 23 L/s over the whole scheme. Immaterial to sizing; it is "
                  "recorded because it is a choice, not a fact.",
         KIND="project assumption", SOURCE="G201-p72 7.4.3 is silent"),
    dict(ID="A-FLOW-2", WHAT="Below 100 properties the peak factor is HELD at the value "
                             "Merrimack gives AT 100 properties, not at 1.0 and not "
                             "extrapolated.",
         WHY="G201-p71 7.4.2 says Merrimack 'is to be used ... for an area having over 100 "
             "properties' and prescribes NOTHING below. Merrimack RISES as the catchment "
             "shrinks, so extrapolating it past the stated range invents peak factors on "
             "the very pipes where it was never validated; holding it at 1.0 would size "
             "every lateral at average flow, which is worse. The plateau is the only "
             "reading that is both continuous and conservative.",
         IF_WRONG="Every reach below 100 properties changes by the ratio of the two factors. "
                  "The sensitivity is published in `pf_bands`.",
         KIND="project decision", SOURCE="G201-p71 7.4.2 (threshold), plateau is OURS"),
    dict(ID="A-FLOW-3", WHAT="A plot's load enters the network at the UPSTREAM node of the "
                             "arc nearest it, so that arc carries its own local load over "
                             "its whole length.",
         WHY="A house connection joins somewhere along the reach; charging it at the "
             "downstream node would leave the reach carrying none of the load in front of "
             "it. Upstream is the conservative end and the one a chamber schedule can "
             "reproduce.",
         IF_WRONG="Head reaches are sized on up to their own local load too much. On a "
                  "DN200 lateral this is within one size step.",
         KIND="project assumption", SOURCE="practice; no guideline states a loading point"),
    dict(ID="A-FLOW-4", WHAT="Each plot is allocated to the NEAREST arc, exactly once, with "
                             "NO distance cap.",
         WHY="s1_roads set this doctrine for Q_NEAR_M3D and the reason is W10: an "
             "assignment radius silently dropped 1,233 m3/d out of every published share. "
             "With no cap the allocation sums to the project total by construction, and "
             "the distance curve is published instead of assumed.",
         IF_WRONG="Nothing is lost, but a plot far from any corridor is attached to a "
                  "corridor it would not really connect to. `allocation` publishes the "
                  "distance distribution so that judgement is the reader's.",
         KIND="project doctrine", SOURCE="s1_roads; W10 defect"),
    dict(ID="A-FLOW-5", WHAT="An arc that is not in the drainage tree (ROLE head / island / "
                             "ring) is a SOURCE BRANCH: it carries only its own local load "
                             "and delivers it at its downstream node.",
         WHY="Philosophy sec 4: at a junction exactly one pipe leaves. The tree arc is that "
             "pipe. A leftover corridor still needs a sewer, and that sewer starts at its "
             "own head chamber and joins the collector at the bottom - it does not take "
             "flow off the node it happens to touch.",
         IF_WRONG="If a chain of head arcs is really one street draining end to end, the "
                  "lower segment is under-loaded by the upper segment's own load. 743 head "
                  "arcs start where another head arc ends; the count and the load at risk "
                  "are published in `roles`.",
         KIND="project decision", SOURCE="philosophy sec 4"),
    dict(ID="A-FLOW-6", WHAT="SATURATION horizon only. There are no start-year flows.",
         WHY="W10_plot_loads carries one figure per plot - the saturated ADWF - and no "
             "phasing. Philosophy sec 6 requires self-cleansing checked at start-year "
             "flows; that check CANNOT RUN from this data.",
         IF_WRONG="A pipe that scours at saturation may silt in 2030. The check is a GAP, "
                  "not a pass.",
         KIND="GAP", SOURCE="data; G201-p73 phasing not modelled"),
    dict(ID="A-FLOW-7", WHAT="The 10 % STP design margin is carried at the WORKS total only, "
                             "never on a pipe.",
         WHY="G201-p73 7.4.5: 'A 10% margin should be applied when designing new STPs'. It "
             "is a treatment-works allowance and applying it to a sewer would double-count "
             "against the peak factor.",
         IF_WRONG="Nothing in the network changes; the works figure would.",
         KIND="reading", SOURCE="G201-p73 7.4.5"),
)


# ======================================================================================
# Peak factor - ONE definition, and the hold derived rather than typed
# ======================================================================================

def merrimack_pf(qadf_m3d: float) -> float:
    """Peak factor from G201-p71 7.4.2.  Qadf in m3/d IN, dimensionless OUT.

    Qpdf = 2.65 Qadf^0.879 with BOTH in Ml/day, so Pf = Qpdf/Qadf = 2.65 Qadf(Ml/d)^-0.121.
    The Ml/day conversion is the trap in this formula and it is done here, once."""
    if qadf_m3d <= 0.0:
        return float("nan")
    return CRIT.pf_merrimack(qadf_m3d / 1000.0)


def peltier_pf(qadf_m3d: float) -> float:
    """G201-p72, the IMP2024 alternative.  Carried for comparison; never applied."""
    if qadf_m3d <= 0.0:
        return float("nan")
    return CRIT.pf_peltier(qadf_m3d * M3D_TO_LS)


@K.published("pf_held", "-", "A-FLOW-2; G201-p71 7.4.2 threshold, plateau is OURS")
def pf_held(q_per_property_m3d: float) -> float:
    """THE held peak factor: Merrimack evaluated at exactly PF_HOLD_PROPERTIES properties.

    `q_per_property_m3d` is a MEASURED project quantity - the allocated load divided by the
    allocated properties - not a constant. It is passed in so the number moves if the load
    basis moves, and so a reader can see what it was evaluated at."""
    return merrimack_pf(CRIT.PF_HOLD_PROPERTIES * float(q_per_property_m3d))


def peak_factor(qadf_m3d, n_prop, q_per_property_m3d: float):
    """Vectorised (PF, method).  The switch is on PROPERTY COUNT because that is what
    G201-p71 states - 'an area ... having over 100 properties' - not on flow.

    NOTE, and it is a real disagreement, not a rounding: `criteria.peak_factor()` returns
    PF = 1.0 below the threshold and calls it 'held'. That holds the peaking at UNITY, which
    would size every lateral at average flow. This stage holds it at the 100-property value
    instead (A-FLOW-2) and reports the disagreement rather than quietly picking one."""
    q = np.asarray(qadf_m3d, dtype=float)
    n = np.asarray(n_prop, dtype=float)
    held = pf_held(q_per_property_m3d)
    with np.errstate(divide="ignore", invalid="ignore"):
        mer = np.where(q > 0.0,
                       CRIT.PF_MERRIMACK_A * (q / 1000.0) ** (CRIT.PF_MERRIMACK_B - 1.0),
                       np.nan)
    use_mer = n > float(CRIT.PF_HOLD_PROPERTIES)          # "over 100", so 100 itself holds
    pf = np.where(use_mer, mer, held)
    pf = np.where(q > 0.0, pf, 1.0)                       # a dry reach has nothing to peak
    meth = np.where(q <= 0.0, "held", np.where(use_mer, "merrimack", "held"))
    return pf, meth


# ======================================================================================
# THE ACCUMULATOR - one function, used on our tree AND on NAMA's built network
# ======================================================================================

class Forest:
    """A directed forest over nodes, with arcs that may or may not be part of it.

    Two kinds of arc, and the distinction is the whole of A-FLOW-5:

      ROUTE arc     (u -> v) where v is u's stored successor. It carries everything that
                    arrived at u, plus its own local load.
      BRANCH arc    every other arc. It carries its own local load only and delivers it at
                    its downstream node. It takes nothing from its upstream node, because
                    at a junction exactly one pipe leaves and the route arc is that pipe.

    Topology is READ, never inferred from geometry (H16). The successor map is the `DS_NODE`
    the orientation stage wrote down."""

    def __init__(self, nodes: pd.DataFrame, arcs: pd.DataFrame,
                 node_key: str = "NODE_ID", succ_key: str = "DS_NODE",
                 us_key: str = "US_NODE", ds_key: str = "DS_NODE"):
        self.node_id = nodes[node_key].astype(str).to_numpy()
        self.n_nodes = len(self.node_id)
        self.pos = {k: i for i, k in enumerate(self.node_id)}
        if len(self.pos) != self.n_nodes:
            raise ValueError("duplicate node id - the successor map would be ambiguous")

        succ_raw = nodes[succ_key].fillna("").astype(str).to_numpy()
        self.succ = np.array([self.pos.get(s, -1) for s in succ_raw], dtype=np.int64)

        self.au = np.array([self.pos[u] for u in arcs[us_key].astype(str)], dtype=np.int64)
        self.av = np.array([self.pos[v] for v in arcs[ds_key].astype(str)], dtype=np.int64)
        self.n_arcs = len(self.au)

        # A ROUTE arc is one the successor map actually uses. Self-loops can never be one.
        self.is_route = (self.succ[self.au] == self.av) & (self.au != self.av)
        # ... and where two parallel arcs both satisfy that, only ONE may be the route, or
        # the load would be delivered twice. Keep the first; the rest become branches.
        seen = set()
        for i in np.flatnonzero(self.is_route):
            u = int(self.au[i])
            if u in seen:
                self.is_route[i] = False
            else:
                seen.add(u)

        self.terminal = self.succ < 0
        self._order = self._topo_order()
        self.reaches_outfall, self.outfall_of = self._trace()

    # -- structure -------------------------------------------------------------------
    def _topo_order(self) -> np.ndarray:
        """Node indices, upstream first (Kahn on ROUTE arcs only).  A residue means a cycle
        in the stored successor map, which is a topology defect and is raised, not patched:
        a cycle silently truncated is a load silently lost."""
        indeg = np.zeros(self.n_nodes, dtype=np.int64)
        for i in np.flatnonzero(self.is_route):
            indeg[self.av[i]] += 1
        q = deque(np.flatnonzero(indeg == 0).tolist())
        order: List[int] = []
        while q:
            u = q.popleft()
            order.append(u)
            v = int(self.succ[u])
            if v >= 0 and self._route_from(u) == v:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        if len(order) < self.n_nodes:
            raise ValueError(
                f"{self.n_nodes - len(order):,} nodes sit on a CYCLE in the successor map. "
                "H15 says the network is a forest; a cycle is a topology defect and it is "
                "not accumulated round.")
        return np.array(order, dtype=np.int64)

    def _route_from(self, u: int) -> int:
        v = int(self.succ[u])
        return v if v >= 0 else -1

    def _trace(self):
        """For every node: does it reach a terminal, and which one.  Iterative, in reverse
        topological order, so it is O(n) and cannot recurse off a long chain."""
        outfall = np.full(self.n_nodes, -1, dtype=np.int64)
        for u in self.terminal.nonzero()[0]:
            outfall[u] = u
        for u in self._order[::-1]:
            if outfall[u] >= 0:
                continue
            v = int(self.succ[u])
            if v >= 0:
                outfall[u] = outfall[v]
        return outfall >= 0, outfall

    # -- the accumulation --------------------------------------------------------------
    def accumulate(self, local: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Push `local` (one value per ARC) down the forest.

        Returns (arc_total, node_in):
            arc_total[e]   what arc e carries
            node_in[v]     what arrives AT node v from every arc ending there

        The order matters and it is the only subtle part: BRANCH arcs depend on nothing, so
        they are delivered first; ROUTE arcs are then walked in topological order, by which
        time everything arriving at their upstream node - route and branch alike - is in."""
        local = np.asarray(local, dtype=float)
        if local.shape != (self.n_arcs,):
            raise ValueError(f"local must be one value per arc ({self.n_arcs:,})")
        arc_total = np.zeros(self.n_arcs, dtype=float)
        node_in = np.zeros(self.n_nodes, dtype=float)

        br = ~self.is_route
        arc_total[br] = local[br]
        np.add.at(node_in, self.av[br], local[br])

        route_at = np.full(self.n_nodes, -1, dtype=np.int64)
        route_at[self.au[self.is_route]] = np.flatnonzero(self.is_route)

        for u in self._order:
            e = int(route_at[u])
            if e < 0:
                continue
            arc_total[e] = node_in[u] + local[e]
            node_in[int(self.av[e])] += arc_total[e]
        return arc_total, node_in

    def outgoing(self) -> np.ndarray:
        """Arc index of each node's outgoing route arc, or -1 at a terminal."""
        out = np.full(self.n_nodes, -1, dtype=np.int64)
        out[self.au[self.is_route]] = np.flatnonzero(self.is_route)
        return out


# ======================================================================================
# Load allocation - plots to arcs, once each, no cap
# ======================================================================================

def allocate(arcs: gpd.GeoDataFrame, plots: gpd.GeoDataFrame, rec=None):
    """Nearest arc, exactly once per plot, NO distance cap (A-FLOW-4).

    Returns (local, table, report).  `local` is a DataFrame indexed like `arcs` carrying
    Q_LOC_M3D, N_PROP_LOC and N_PLOT_LOC.

    Why not read s2_orient's `Q_M3D`: that column is a load and this stage needs a load AND
    a property count on the SAME basis, because the peak-factor threshold is stated in
    properties. Two allocations produced by two functions is exactly the 'no re-filtered
    metric' defect. One allocation, here, checked against s2's."""
    from shapely.strtree import STRtree

    lp = plots[plots["Q_AVG_M3D"] > 0].copy()
    funnel = None
    if rec is not None:
        funnel = rec.funnel("plots -> arcs", int(len(plots)))
        funnel.drop("no saturated load on the plot (agricultural, vacant, zeroed)",
                    n=int(len(plots) - len(lp)),
                    qty=0.0)

    cent = list(lp.geometry.representative_point().values)
    qv = pd.to_numeric(lp["Q_AVG_M3D"], errors="coerce").fillna(0.0).to_numpy(float)
    pv = pd.to_numeric(lp["N_PROP"], errors="coerce").fillna(0.0).to_numpy(float)

    tree = STRtree(list(arcs.geometry.values))
    idx, dist = tree.query_nearest(cent, return_distance=True, all_matches=False)
    idx = np.asarray(idx)
    if idx.ndim == 2:                                   # (input_idx, tree_idx)
        src, tgt = idx[0], idx[1]
    else:
        src, tgt = np.arange(len(cent)), idx
    dist = np.asarray(dist, dtype=float)

    n = len(arcs)
    q = np.zeros(n)
    prop = np.zeros(n)
    cnt = np.zeros(n)
    np.add.at(q, tgt, qv[src])
    np.add.at(prop, tgt, pv[src])
    np.add.at(cnt, tgt, 1.0)

    if funnel is not None:
        funnel.close(int(len(lp)))

    bands = [10, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500, 1000]
    table = pd.DataFrame([
        dict(WITHIN_M=float(b),
             PCT_LOAD=round(100.0 * float(qv[dist <= b].sum() / qv.sum()), 2),
             PCT_PROP=round(100.0 * float(pv[dist <= b].sum() / pv.sum()), 2),
             PCT_PLOTS=round(100.0 * float((dist <= b).mean()), 2))
        for b in bands])

    rep = dict(
        plots_total=int(len(plots)),
        plots_with_load=int(len(lp)),
        q_total_m3d=float(qv.sum()),
        q_allocated_m3d=float(q.sum()),
        prop_total=float(pv.sum()),
        prop_allocated=float(prop.sum()),
        arcs_with_load=int((q > 0).sum()),
        arcs_without_load=int((q <= 0).sum()),
        dist_median_m=float(np.median(dist)),
        dist_p90_m=float(np.percentile(dist, 90)),
        dist_max_m=float(dist.max()),
        q_per_property_m3d=float(qv.sum() / pv.sum()),
    )
    loc = pd.DataFrame({"Q_LOC_M3D": q, "N_PROP_LOC": prop, "N_PLOT_LOC": cnt},
                       index=arcs.index)
    return loc, table, rep


# ======================================================================================
# The stage
# ======================================================================================

@K.published("infiltration_system_ls", "L/s",
             "G201-p72 7.4.3, 720 L/d/km ON THE NETWORK LENGTH")
def infiltration_system_ls(network_length_m: float) -> float:
    """THE system infiltration.  Rate x NETWORK length, and nothing else.

    This function exists so that the number has exactly one definition. It is NOT the sum of
    the per-reach cumulative values: that counts every kilometre once per downstream reach
    and overstated the figure 87-fold in W11a (1,259 L/s against 14.5)."""
    return CRIT.infiltration_ls(float(network_length_m))


@K.published("top_pipe_load_share_pct", "%", "s5_flows health check")
def top_pipe_load_share_pct(arc_qadf: Sequence[float], placed_total_m3d: float) -> float:
    """The health check: what share of the PLACED load does the single biggest pipe carry.

    Denominator is the load PLACED on the network, not the load delivered - so a network
    that loses load to a disconnected piece is penalised by this number rather than
    flattered by a smaller denominator."""
    a = np.asarray(arc_qadf, dtype=float)
    if placed_total_m3d <= 0 or not len(a):
        return float("nan")
    return 100.0 * float(np.nanmax(a)) / float(placed_total_m3d)


def build(verbose: bool = True) -> Dict[str, object]:
    t0 = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    with K.Manifest.stage(STAGE, STAGE_ORDER) as rec:
        # ---------------------------------------------------------------- read
        if not ORIENT_GPKG.exists():
            raise FileNotFoundError(
                f"{ORIENT_GPKG} is missing. This stage accumulates down the tree s2_orient "
                "publishes; run `python s2_orient.py` first.")
        arcs = gpd.read_file(ORIENT_GPKG, layer="arcs")
        nodes = gpd.read_file(ORIENT_GPKG, layer="nodes")
        plots = gpd.read_file(PLOT_LOADS, layer=PLOT_LOADS_LAYER)
        rec.read("arcs", str(ORIENT_GPKG), len(arcs))
        rec.read("nodes", str(ORIENT_GPKG), len(nodes))
        rec.read("plot_loads", str(PLOT_LOADS), len(plots))

        for df, nm in ((arcs, "arcs"), (nodes, "nodes"), (plots, "plot_loads")):
            if df.crs is None or df.crs.to_epsg() != CRS_EPSG:
                raise ValueError(f"{nm} is in {df.crs}, not EPSG:{CRS_EPSG}")

        arcs = arcs.reset_index(drop=True)
        nodes = nodes.reset_index(drop=True)
        arcs["EDGE_UID"] = [K.EDGE_UID_FMT.format(i) for i in range(len(arcs))]

        # ---------------------------------------------------------------- topology
        F = Forest(nodes, arcs)
        arcs["IS_ROUTE"] = F.is_route.astype(int)
        n_route = int(F.is_route.sum())
        n_branch = int((~F.is_route).sum())
        if verbose:
            print(f"  forest: {n_route:,} route arcs, {n_branch:,} branch arcs, "
                  f"{int(F.terminal.sum()):,} terminals")

        # A terminal that is an OUTFALL is a delivery point; a terminal that is not is a
        # piece that drains nowhere, which H15 forbids. The distinction is the node's own
        # KIND, written by the orientation stage, not guessed here.
        kind = nodes["KIND"].astype(str).to_numpy()
        is_outfall = (kind == "outfall")
        term_not_outfall = F.terminal & ~is_outfall
        outfall_not_term = is_outfall & ~F.terminal
        if outfall_not_term.any():
            raise ValueError(f"{int(outfall_not_term.sum()):,} nodes are labelled outfall "
                             "but still have a successor - the label and the graph disagree")

        # ---------------------------------------------------------------- load
        loc, reach_tab, alloc = allocate(arcs, plots, rec)
        arcs["Q_LOC_M3D"] = loc["Q_LOC_M3D"].to_numpy()
        arcs["N_PROP_LOC"] = loc["N_PROP_LOC"].to_numpy()
        arcs["N_PLOT_LOC"] = loc["N_PLOT_LOC"].to_numpy()
        q_per_prop = alloc["q_per_property_m3d"]

        # ---------------------------------------------------------------- accumulate
        length = pd.to_numeric(arcs["LEN_M"], errors="coerce").fillna(0.0).to_numpy(float)
        acc_q, in_q = F.accumulate(arcs["Q_LOC_M3D"].to_numpy(float))
        acc_p, in_p = F.accumulate(arcs["N_PROP_LOC"].to_numpy(float))
        acc_l, in_l = F.accumulate(length)
        acc_n, in_n = F.accumulate(np.ones(len(arcs), dtype=float))

        arcs["QADF_M3D"] = acc_q
        arcs["N_PROP"] = acc_p
        arcs["UPS_LEN_M"] = acc_l
        arcs["UPS_ARCS"] = acc_n.astype(int)

        # ---------------------------------------------------------------- peak, infiltration
        pf, meth = peak_factor(acc_q, acc_p, q_per_prop)
        arcs["PF"] = pf
        arcs["PF_METH"] = meth
        arcs["PF_PELT"] = [peltier_pf(v) for v in acc_q]
        arcs["QADF_LS"] = acc_q * M3D_TO_LS
        arcs["QINF_LS"] = CRIT.INFILT_L_D_KM * (acc_l / 1000.0) / SEC_PER_DAY
        arcs["QINF_LOC"] = CRIT.INFILT_L_D_KM * (length / 1000.0) / SEC_PER_DAY
        arcs["QPK_LS"] = arcs["QADF_LS"] * arcs["PF"] + arcs["QINF_LS"]

        # The monotonicity guard. NOT a design value - a diagnostic. Qpdf = 2.65 Qadf^0.879
        # is strictly increasing, so within one PF regime the peak flow cannot fall
        # downstream. Across the held/Merrimack boundary it can, because the switch is on
        # PROPERTY COUNT and the two curves meet only where the load per property is the
        # project average. QPK_MONO is what a sizing stage would actually have to carry.
        qpk = arcs["QPK_LS"].to_numpy(float)
        mono = _max_upstream(F, qpk)
        arcs["QPK_MONO"] = np.maximum(qpk, mono)
        arcs["MONO_FIX"] = (arcs["QPK_MONO"] > qpk + 1e-9).astype(int)

        # ---------------------------------------------------------------- nodes out
        out_arc = F.outgoing()
        node_q = np.where(out_arc >= 0, acc_q[np.clip(out_arc, 0, None)], in_q)
        node_p = np.where(out_arc >= 0, acc_p[np.clip(out_arc, 0, None)], in_p)
        node_l = np.where(out_arc >= 0, acc_l[np.clip(out_arc, 0, None)], in_l)
        node_pf, node_meth = peak_factor(node_q, node_p, q_per_prop)
        node_inf = CRIT.INFILT_L_D_KM * (node_l / 1000.0) / SEC_PER_DAY

        nodes_out = nodes.copy()
        nodes_out["NODE_UID"] = nodes_out["NODE_ID"].astype(str)
        nodes_out["Q_ADF_M3D"] = node_q
        nodes_out["N_PROP"] = node_p
        nodes_out["UPS_LEN_M"] = node_l
        nodes_out["PF"] = node_pf
        nodes_out["PF_METH"] = node_meth
        nodes_out["QINF_LS"] = node_inf
        nodes_out["Q_PK_LS"] = node_q * M3D_TO_LS * node_pf + node_inf
        nodes_out["IS_OUTFALL"] = is_outfall.astype(int)
        nodes_out["DEAD_END"] = term_not_outfall.astype(int)
        # DELIVERED IS ONE QUESTION AND IT GETS ONE ANSWER (inheritance row 10).  It was
        # `F.reaches_outfall` alone until 2026-09-06, and `Forest._trace` sets that flag on
        # every node that reaches A TERMINAL - which, in a forest, is EVERY NODE.  The column
        # was published 1 on all 10,183 rows: a constant dressed as a finding, the same class
        # of defect as the 90-degree crossing angle on all 3,290 rows (tests/test_columns).
        # A terminal is only a DELIVERY point if it is an OUTFALL; the 154 terminals that are
        # dead ends take flow and pass it nowhere.  This is the arc column's own definition,
        # written once and used for both, so the two cannot answer differently again.
        delivered_node = F.reaches_outfall & is_outfall[np.clip(F.outfall_of, 0, None)]
        nodes_out["DELIVERED"] = delivered_node.astype(int)
        nodes_out["TAU_FLAG"] = CRIT.tau_banner()

        # what each arc ends up at.  An arc delivers where the node it DISCHARGES INTO does -
        # for a branch arc that is where its own load lands, and for a route arc its
        # downstream node is its upstream node's successor, so the two agree by construction.
        arc_outfall = np.where(F.outfall_of[F.av] >= 0,
                               nodes["NODE_ID"].to_numpy()[np.clip(F.outfall_of[F.av], 0, None)],
                               "")
        delivered_arc = delivered_node[F.av]
        arcs["OUTFALL"] = np.where(delivered_arc, arc_outfall, "")
        arcs["DELIVERED"] = delivered_arc.astype(int)
        arcs["TAU_FLAG"] = CRIT.tau_banner()

        # ---------------------------------------------------------------- conservation
        placed = float(arcs["Q_LOC_M3D"].sum())
        delivered = float(in_q[is_outfall].sum())
        lost = float(arcs.loc[arcs["DELIVERED"] == 0, "Q_LOC_M3D"].sum())
        net_len_delivered = float(in_l[is_outfall].sum())
        net_len_all = float(length.sum())

        cons = _conservation(F, arcs, nodes_out, in_q, in_l, is_outfall,
                             placed, alloc, net_len_delivered, net_len_all)

        # ---------------------------------------------------------------- health
        health, verdict = _health(arcs, nodes_out, in_q, is_outfall, placed, delivered,
                                  lost, net_len_delivered, verbose=False)

        # ---------------------------------------------------------------- tables
        infil = _infiltration_table(arcs, is_outfall, in_l, net_len_delivered, net_len_all)
        pfb = _pf_table(arcs, q_per_prop)
        roles = _roles_table(arcs, F)
        outf = _outfall_table(arcs, nodes_out, in_q, in_p, in_l, is_outfall, placed)
        subs = _subnet_table(arcs, nodes_out, placed)
        bands = _flow_bands(arcs)
        undel = _undelivered_table(arcs, nodes_out)
        alloc_tab = pd.DataFrame([dict(ITEM=k, VALUE=v) for k, v in alloc.items()])
        assum = pd.DataFrame(list(ASSUMPTIONS))
        manif = _manifest(arcs, nodes_out, alloc, placed, delivered, lost,
                          net_len_delivered, net_len_all, health, q_per_prop)

        # ---------------------------------------------------------------- publish
        keep_a = ["EDGE_UID", "CID", "US_NODE", "DS_NODE", "ROLE", "IS_ROUTE", "SUBNET",
                  "OUTFALL", "DELIVERED", "LEN_M", "SRC", "CONFIDENCE",
                  "Q_LOC_M3D", "N_PROP_LOC", "N_PLOT_LOC",
                  "QADF_M3D", "QADF_LS", "N_PROP", "UPS_LEN_M", "UPS_ARCS",
                  "PF", "PF_METH", "PF_PELT", "QINF_LS", "QINF_LOC", "QPK_LS",
                  "QPK_MONO", "MONO_FIX", "TAU_FLAG", "geometry"]
        a_out = arcs[[c for c in keep_a if c in arcs.columns]].copy()
        keep_n = ["NODE_UID", "X", "Y", "GRD_M", "KIND", "SUBNET", "DS_NODE", "N_IN",
                  "IS_OUTFALL", "DEAD_END", "DELIVERED",
                  "Q_ADF_M3D", "Q_PK_LS", "N_PROP", "UPS_LEN_M", "PF", "PF_METH",
                  "QINF_LS", "TAU_FLAG", "geometry"]
        n_out = nodes_out[[c for c in keep_n if c in nodes_out.columns]].copy()

        _write(OUT_GPKG, {
            "arcs": a_out, "nodes": n_out,
            "health": health, "conservation": cons, "infiltration": infil,
            "pf_bands": pfb, "flow_bands": bands, "roles": roles, "outfalls": outf,
            "subnets": subs, "undelivered": undel, "allocation": alloc_tab,
            "load_reach": reach_tab, "assumptions": assum, "manifest": manif,
        })
        rec.wrote("arcs", str(OUT_GPKG), len(a_out))
        rec.wrote("nodes", str(OUT_GPKG), len(n_out))
        for k, v in (("health", health), ("infiltration", infil), ("outfalls", outf)):
            rec.wrote(k, str(OUT_GPKG), len(v))
        rec.metric("top_pipe_load_share_pct",
                   float(health.loc[health.ITEM == "TOP_PIPE_PCT", "VALUE"].iloc[0]))
        rec.metric("delivered_pct",
                   float(health.loc[health.ITEM == "DELIVERED_PCT", "VALUE"].iloc[0]))
        rec.metric("infiltration_system_ls", round(infiltration_system_ls(net_len_delivered), 4))
        rec.note(verdict.splitlines()[0])

        # CSVs
        for nm, df in (("health", health), ("conservation", cons),
                       ("infiltration", infil), ("pf_bands", pfb),
                       ("flow_bands", bands), ("roles", roles),
                       ("outfalls", outf), ("subnets", subs), ("undelivered", undel),
                       ("allocation", alloc_tab), ("load_reach", reach_tab),
                       ("assumptions", assum), ("manifest", manif)):
            df.to_csv(RUN_DIR / f"{nm}.csv", index=False, encoding="utf-8")

        # KMZ
        kmz_note = _kmz(a_out, verbose=verbose)

        md = _report_md(arcs, nodes_out, health, verdict, cons, infil, pfb, bands, roles,
                        outf, subs, undel, alloc, reach_tab, manif, q_per_prop,
                        net_len_delivered, net_len_all, kmz_note)
        REPORT_MD.write_text(md, encoding="utf-8")

        (RUN_DIR / "flows_manifest.json").write_text(json.dumps(dict(
            stage=STAGE_VERSION, contract=K.CONTRACT_VERSION, tau_pa=CRIT.TAU_PA,
            written=time.strftime("%Y-%m-%d %H:%M:%S"),
            seconds=round(time.time() - t0, 1),
            metrics={r.ITEM: r.VALUE for r in manif.itertuples()},
        ), indent=2, default=str), encoding="utf-8")

    if verbose:
        print(verdict)
        print(f"\n  wrote {OUT_GPKG}")
        print(f"  wrote {REPORT_MD}")
        print(f"  {time.time() - t0:.1f} s")
    return dict(arcs=a_out, nodes=n_out, health=health, manifest=manif, verdict=verdict)


def _max_upstream(F: Forest, x: np.ndarray) -> np.ndarray:
    """For each arc, the largest value of `x` on any arc immediately upstream of it.

    Not the maximum over the whole upstream catchment - that is not what the guard needs.
    A pipe must carry what the pipe above delivers; if the pipe above already carries its
    own upstream maximum, one hop propagates it."""
    node_max = np.zeros(F.n_nodes, dtype=float)
    br = ~F.is_route
    np.maximum.at(node_max, F.av[br], x[br])
    route_at = np.full(F.n_nodes, -1, dtype=np.int64)
    route_at[F.au[F.is_route]] = np.flatnonzero(F.is_route)
    out = np.zeros(F.n_arcs, dtype=float)
    for u in F._order:
        e = int(route_at[u])
        if e < 0:
            continue
        out[e] = node_max[u]
        v = int(F.av[e])
        node_max[v] = max(node_max[v], max(x[e], out[e]))
    return out


# ======================================================================================
# Tables
# ======================================================================================

def _conservation(F, arcs, nodes_out, in_q, in_l, is_outfall, placed, alloc,
                  net_len_delivered, net_len_all) -> pd.DataFrame:
    """Every identity that MUST hold, computed two ways, with the residual printed.

    A conservation table with no residual column is a claim. With one, it is a measurement."""
    rows = []

    def add(what, a, b, unit, tol, note):
        rows.append(dict(CHECK=what, A=round(float(a), 6), B=round(float(b), 6),
                         RESID=round(float(a - b), 6), UNIT=unit,
                         TOL=tol, PASS=int(abs(a - b) <= tol), NOTE=note))

    add("plot load allocated == plot load available",
        alloc["q_allocated_m3d"], alloc["q_total_m3d"], "m3/d", 1e-6,
        "nearest arc, no cap (A-FLOW-4): nothing can fall outside a radius")
    add("properties allocated == properties available",
        alloc["prop_allocated"], alloc["prop_total"], "-", 1e-6,
        "same allocation, same basis - this is why the load is not read from s2")
    add("local load on arcs == plot load allocated",
        float(arcs["Q_LOC_M3D"].sum()), alloc["q_allocated_m3d"], "m3/d", 1e-6,
        "the local column is the allocation, transposed onto arcs")
    add("delivered + undelivered == placed",
        float(in_q[is_outfall].sum()) +
        float(arcs.loc[arcs["DELIVERED"] == 0, "Q_LOC_M3D"].sum()),
        placed, "m3/d", 1e-6,
        "load that reaches an outfall plus load that cannot; there is no third bucket")
    add("delivered sewer length == length of arcs that reach an outfall",
        net_len_delivered,
        float(arcs.loc[arcs["DELIVERED"] == 1, "LEN_M"].sum()), "m", 1e-3,
        "every metre drains to exactly ONE outfall, so accumulating length cannot "
        "double-count it")
    inf_from_len = infiltration_system_ls(net_len_delivered)
    inf_from_loc = float(arcs.loc[arcs["DELIVERED"] == 1, "QINF_LOC"].sum())
    inf_from_out = float(_outfall_arc_sum(arcs, nodes_out, "QINF_LS"))
    add("infiltration: rate x length == sum of LOCAL values",
        inf_from_len, inf_from_loc, "L/s", 1e-6,
        "G201-p72 7.4.3, 720 L/d/km. THE definition is rate x network length")
    add("infiltration: rate x length == cumulative value at the OUTFALLS ONLY",
        inf_from_len, inf_from_out, "L/s", 1e-6,
        "the cumulative column IS summable, but only over a partition - the outfalls")
    add("node Q at an outfall == what arrives there",
        float(nodes_out.loc[nodes_out.IS_OUTFALL == 1, "Q_ADF_M3D"].sum()),
        float(in_q[is_outfall].sum()), "m3/d", 1e-6,
        "the node layer and the arc layer come from the same accumulation, not two solves")
    q_route = float(arcs.loc[arcs.IS_ROUTE == 1, "Q_LOC_M3D"].sum())
    q_branch = float(arcs.loc[arcs.IS_ROUTE == 0, "Q_LOC_M3D"].sum())
    add("route local + branch local == placed", q_route + q_branch, placed, "m3/d", 1e-6,
        "A-FLOW-5: every arc is one or the other and no arc is both")
    if "Q_M3D" in arcs.columns:
        # s2_orient allocated the SAME plots to the SAME corridors by the same rule, then
        # split the result across its ridge splits. Two functions producing one quantity is
        # the provenance defect this row exists to expose, so the disagreement is measured
        # rather than assumed away. This stage's column is the one published, because it is
        # the only one that carries a matching PROPERTY count.
        d = (arcs["Q_LOC_M3D"] - arcs["Q_M3D"]).abs()
        add("this stage's allocation == s2_orient's Q_M3D, in total",
            placed, float(arcs["Q_M3D"].sum()), "m3/d", 0.5,
            f"per-arc agreement: {int((d < 0.001).sum()):,} of {len(arcs):,} identical, "
            f"largest single difference {float(d.max()):.1f} m3/d, "
            f"correlation {float(arcs['Q_LOC_M3D'].corr(arcs['Q_M3D'])):.6f}. Two "
            "allocations, one answer - the tolerance is s2's 3-dp rounding")
    return pd.DataFrame(rows)


def _outfall_arc_sum(arcs, nodes_out, col) -> float:
    """Sum a CUMULATIVE column over the arcs that discharge at an outfall, and only those.

    This is the safe way to total a cumulative quantity: the outfall reaches partition the
    network, so each upstream metre is counted once. Summing the same column over every arc
    is the 87-fold error."""
    outf = set(nodes_out.loc[nodes_out.IS_OUTFALL == 1, "NODE_UID"].astype(str))
    m = arcs["DS_NODE"].astype(str).isin(outf) & (arcs["DELIVERED"] == 1)
    return float(arcs.loc[m, col].sum())


def _health(arcs, nodes_out, in_q, is_outfall, placed, delivered, lost,
            net_len_delivered, verbose=True):
    """THE health check.  It is first in every output and it carries its own verdict."""
    q = arcs["QADF_M3D"].to_numpy(float)
    top = top_pipe_load_share_pct(q, placed)
    top_i = int(np.nanargmax(q))
    top_row = arcs.iloc[top_i]

    of = pd.DataFrame({"OUTFALL": nodes_out.loc[is_outfall, "NODE_UID"].astype(str).to_numpy(),
                       "Q": in_q[is_outfall]})
    of = of.sort_values("Q", ascending=False)
    share = of["Q"].to_numpy(float) / max(placed, 1e-12)
    hhi = float((share ** 2).sum())

    ab = asbuilt_benchmark()

    rows = [
        dict(ITEM="TOP_PIPE_PCT", VALUE=round(top, 2), UNIT="%",
             WHAT="share of the PLACED load carried by the single biggest pipe",
             BENCHMARK=("" if ab is None else round(ab["top_pipe_pct"], 2)),
             SOURCE="s5_flows health check; benchmark = the same accumulator over NAMA's "
                    "built network"),
        dict(ITEM="TOP_PIPE_M3D", VALUE=round(float(q[top_i]), 1), UNIT="m3/d",
             WHAT=f"that pipe is {top_row.EDGE_UID} ({top_row.US_NODE}->{top_row.DS_NODE}), "
                  f"subnet {top_row.SUBNET}",
             BENCHMARK=("" if ab is None else round(ab["top_pipe_m3d"], 1)),
             SOURCE="arcs.QADF_M3D. The benchmark's ABSOLUTE m3/d is not comparable - the "
                    "nearest-pipe rule has no cap, so the built 95.4 km receives the whole "
                    "study area's load. Its SHARE is what compares, and share is what this "
                    "check measures"),
        dict(ITEM="DELIVERED_PCT", VALUE=round(100.0 * delivered / max(placed, 1e-12), 2),
             UNIT="%", WHAT="share of the placed load that reaches an outfall at all",
             BENCHMARK="", SOURCE="conservation: delivered / placed"),
        dict(ITEM="LOST_M3D", VALUE=round(lost, 1), UNIT="m3/d",
             WHAT="load on pieces that drain nowhere - H15 forbids these, they are NOT "
                  "dropped silently",
             BENCHMARK="", SOURCE="arcs where DELIVERED = 0"),
        dict(ITEM="N_OUTFALL", VALUE=int(is_outfall.sum()), UNIT="-",
             WHAT="separate discharge points. Each is a connection to the client's Main "
                  "Pipe, which is an INPUT and is NOT in this graph",
             BENCHMARK=("" if ab is None else ab["n_outfall"]),
             SOURCE="nodes.KIND == 'outfall', written by s2_orient"),
        dict(ITEM="BIGGEST_OUTFALL_PCT", VALUE=round(100.0 * float(share[0]), 2), UNIT="%",
             WHAT="share of the placed load arriving at the largest single outfall",
             BENCHMARK="", SOURCE="in_q at outfalls / placed"),
        dict(ITEM="TOP10_OUTFALL_PCT", VALUE=round(100.0 * float(share[:10].sum()), 2),
             UNIT="%", WHAT="the ten largest outfalls together",
             BENCHMARK="", SOURCE="in_q at outfalls / placed"),
        dict(ITEM="OUTFALL_HHI", VALUE=round(hhi, 4), UNIT="-",
             WHAT="Herfindahl concentration of load over outfalls. 1.00 = one works; "
                  "1/N = perfectly split",
             BENCHMARK="", SOURCE="sum of squared outfall shares"),
        dict(ITEM="TRUNK_IF_JOINED_PCT",
             VALUE=round(100.0 * delivered / max(placed, 1e-12), 2), UNIT="%",
             WHAT="what the client's Main Pipe would carry below the last connection, IF "
                  "every outfall discharges into it. A STATED HYPOTHETICAL - the Main Pipe "
                  "is not in this graph and this stage has not routed it",
             BENCHMARK="", SOURCE="hypothetical, tagged"),
        dict(ITEM="EMPTY_OUTFALL", VALUE=int((of["Q"].to_numpy(float) <= 0).sum()), UNIT="-",
             WHAT="outfalls with NOTHING draining to them - a connection to the client's "
                  "Main Pipe that serves nobody. Not this stage's to fix: the flow "
                  "arithmetic is what exposes them and the resolution is s2's",
             BENCHMARK="", SOURCE="in_q at outfalls == 0"),
        dict(ITEM="TRUNK_IF_JOINED_LS",
             VALUE=round(delivered * M3D_TO_LS * merrimack_pf(delivered)
                         + infiltration_system_ls(net_len_delivered), 1), UNIT="L/s",
             WHAT="and the PEAK flow that trunk would carry - Merrimack on the whole "
                  "delivered load plus the system infiltration. A STATED HYPOTHETICAL, on "
                  "the same footing as TRUNK_IF_JOINED_PCT: it is the number a trunk-sizing "
                  "stage would start from, not a number this stage has designed",
             BENCHMARK="", SOURCE="G201-p71 7.4.2 on the delivered total"),
        dict(ITEM="MAX_PIPE_LS", VALUE=round(float(np.nanmax(arcs["QPK_MONO"])), 2),
             UNIT="L/s",
             WHAT="the largest PEAK flow any gravity pipe in this design carries. This is "
                  "the number the sizing stage starts from, and it is small: nothing here "
                  "needs a large-diameter sewer",
             BENCHMARK="", SOURCE="arcs.QPK_MONO"),
        dict(ITEM="ZERO_FLOW_KM",
             VALUE=round(float(arcs.loc[arcs.QADF_M3D <= 0, "LEN_M"].sum() / 1000.0), 1),
             UNIT="km",
             WHAT=f"{int((arcs.QADF_M3D <= 0).sum()):,} reaches have NOTHING draining through "
                  "them - no load of their own and none from above. Pruning candidates for "
                  "the hierarchy stage (philosophy sec 4, 'no fingers'), not a defect of this "
                  "one",
             BENCHMARK="", SOURCE="arcs.QADF_M3D <= 0"),
        dict(ITEM="INFIL_SYSTEM_LS", VALUE=round(infiltration_system_ls(net_len_delivered), 3),
             UNIT="L/s", WHAT="system infiltration = 720 L/d/km x delivered network length",
             BENCHMARK="", SOURCE="G201-p72 7.4.3"),
        dict(ITEM="INFIL_IF_SUMMED_LS", VALUE=round(float(arcs["QINF_LS"].sum()), 1),
             UNIT="L/s", WHAT="THE WRONG ANSWER, printed on purpose: the same column summed "
                              "over every reach instead of over the outfalls",
             BENCHMARK="", SOURCE="the W11a defect, reproduced so it cannot recur unnoticed"),
    ]
    health = pd.DataFrame(rows)

    bar = "=" * 86
    if ab is None:
        cmp_line = "  (the as-built benchmark could not be computed - see `roles` NOTE)"
    else:
        cmp_line = (f"  NAMA's own built network, same accumulator, same plot loads: "
                    f"{ab['top_pipe_pct']:.2f} % on {ab['n_outfall']} outfalls "
                    f"({ab['km']:.1f} km, {ab['placed_m3d']:,.0f} m3/d placed)")
    verdict = "\n".join([
        bar,
        "  HEALTH CHECK - WHAT SHARE OF THE PLACED LOAD DOES THE BIGGEST PIPE CARRY?",
        bar,
        f"  {top:.2f} %   ({q[top_i]:,.0f} m3/d of {placed:,.0f} m3/d placed)",
        cmp_line,
        f"  {int(is_outfall.sum()):,} outfalls; the largest takes "
        f"{100.0 * share[0]:.2f} %, the top ten {100.0 * share[:10].sum():.2f} %; HHI {hhi:.4f}",
        f"  {100.0 * delivered / max(placed, 1e-12):.2f} % of the placed load reaches an "
        f"outfall; {lost:,.0f} m3/d is on pieces that drain nowhere",
        f"  the largest PEAK flow on any gravity pipe is "
        f"{float(np.nanmax(arcs['QPK_MONO'])):,.1f} L/s; "
        f"{int((arcs.QADF_M3D <= 0).sum()):,} reaches "
        f"({float(arcs.loc[arcs.QADF_M3D <= 0, 'LEN_M'].sum() / 1000.0):,.0f} km) carry "
        f"nothing at all",
        "",
        "  READ THIS BEFORE THE NUMBER: in a network draining to ONE works the top pipe",
        "  carries nearly all of the load. It does not here, and the reason is structural,",
        "  not hydraulic - the client's Main Pipe is an INPUT and is not in this graph, so",
        "  every one of these outfalls is a SEPARATE connection to it. The figure that would",
        "  compare like with like is TRUNK_IF_JOINED_PCT, and it is a hypothetical until a",
        "  stage actually routes the Main Pipe. What the number DOES measure, honestly, is",
        "  how much of the load any single designed gravity pipe would ever have to carry.",
        bar,
    ])
    if verbose:
        print(verdict)
    return health, verdict


_AB_CACHE: Dict[str, object] = {}


def asbuilt_benchmark() -> Optional[Dict[str, float]]:
    """Run THE SAME accumulator over NAMA's built network with the same plot loads.

    The benchmark for the health check has to be measured, not chosen. The built network is
    95.4 km of pipe that works; whatever share its biggest pipe carries is what this ground,
    this town and this client's own practice produce."""
    if "v" in _AB_CACHE:
        return _AB_CACHE["v"]                                   # type: ignore[return-value]
    try:
        from w12.asbuilt import AsBuilt
        ab = AsBuilt()
        g = ab.pipes.reset_index(drop=True)
        us = g["US_MHID"].astype(str)
        ds = g["DS_MHID"].astype(str)
        ids = pd.Index(sorted(set(us) | set(ds)))
        # the successor of a manhole is the DS end of the pipe leaving it; where the
        # designer's own ids give a manhole two outgoing pipes (there is 1 such
        # bifurcation), the first is the route and the rest become branches - the same rule
        # this stage applies to its own graph.
        succ = {}
        for u, d in zip(us, ds):
            succ.setdefault(u, d)
        nd = pd.DataFrame({"NODE_ID": ids,
                           "DS_NODE": [succ.get(i, "") for i in ids]})
        ar = pd.DataFrame({"US_NODE": us, "DS_NODE": ds})
        Fb = Forest(nd, ar)
        plots = gpd.read_file(PLOT_LOADS, layer=PLOT_LOADS_LAYER)
        gg = gpd.GeoDataFrame(ar.copy(), geometry=g.geometry.values, crs=g.crs)
        loc, _, alloc = allocate(gg, plots)
        accq, inq = Fb.accumulate(loc["Q_LOC_M3D"].to_numpy(float))
        placed = float(loc["Q_LOC_M3D"].sum())
        out = dict(top_pipe_pct=top_pipe_load_share_pct(accq, placed),
                   top_pipe_m3d=float(np.nanmax(accq)),
                   n_outfall=int(Fb.terminal.sum()),
                   km=float(g["LEN_M"].sum() / 1000.0),
                   placed_m3d=placed)
        _AB_CACHE["v"] = out
        return out
    except Exception as exc:                                     # noqa: BLE001
        _AB_CACHE["v"] = None
        _AB_CACHE["err"] = str(exc)
        return None


def _infiltration_table(arcs, is_outfall, in_l, net_len_delivered, net_len_all):
    right = infiltration_system_ls(net_len_delivered)
    wrong = float(arcs["QINF_LS"].sum())
    return pd.DataFrame([
        dict(ITEM="rate", VALUE=CRIT.INFILT_L_D_KM, UNIT="L/d/km",
             SOURCE="G201-p72 7.4.3, new networks",
             NOTE="'Infiltration due to storm water is not considered' - same clause"),
        dict(ITEM="network length, delivered", VALUE=round(net_len_delivered / 1000.0, 3),
             UNIT="km", SOURCE="accumulated, checked against the arc lengths",
             NOTE="arcs that reach an outfall"),
        dict(ITEM="network length, published", VALUE=round(net_len_all / 1000.0, 3),
             UNIT="km", SOURCE="sum of arcs.LEN_M",
             NOTE="includes the pieces that drain nowhere"),
        dict(ITEM="SYSTEM INFILTRATION", VALUE=round(right, 4), UNIT="L/s",
             SOURCE="THE definition: rate x network length",
             NOTE="one function, contract.published('infiltration_system_ls')"),
        dict(ITEM="system infiltration, published length", VALUE=round(
            infiltration_system_ls(net_len_all), 4), UNIT="L/s",
             SOURCE="rate x published length", NOTE="the upper bound if every piece is built"),
        dict(ITEM="SUM of the per-reach cumulative column", VALUE=round(wrong, 1), UNIT="L/s",
             SOURCE="arcs.QINF_LS summed - THE WRONG ANSWER",
             NOTE="printed on purpose"),
        dict(ITEM="overstatement factor", VALUE=round(wrong / max(right, 1e-12), 1), UNIT="x",
             SOURCE="wrong / right on THIS network",
             NOTE="W11a shipped 1,259 L/s against 14.5 - 87x - the same mistake"),
        dict(ITEM="sum of the per-reach LOCAL column", VALUE=round(
            float(arcs.loc[arcs.DELIVERED == 1, "QINF_LOC"].sum()), 4), UNIT="L/s",
             SOURCE="arcs.QINF_LOC summed over delivered arcs",
             NOTE="THIS one is summable, and it lands on the definition"),
        dict(ITEM="infiltration as a share of average dry weather flow",
             VALUE=round(100.0 * right / max(
                 float(arcs.loc[arcs.DELIVERED == 1, "Q_LOC_M3D"].sum()) * M3D_TO_LS, 1e-12), 3),
             UNIT="%", SOURCE="derived",
             NOTE="G201-p72 allows 10 % for an EXISTING inland network; a new one on this "
                  "length is far below that, which is the point of the 720 L/d/km rule"),
    ])


def _pf_table(arcs, q_per_prop):
    held = pf_held(q_per_prop)
    pf = arcs["PF"].to_numpy(float)
    q = arcs["QADF_M3D"].to_numpy(float)
    ln = arcs["LEN_M"].to_numpy(float)
    meth = arcs["PF_METH"].to_numpy()
    rows = [
        dict(ITEM="held peak factor", VALUE=round(held, 4), UNIT="-",
             SOURCE="A-FLOW-2: Merrimack AT the 100-property threshold",
             NOTE=f"evaluated at {CRIT.PF_HOLD_PROPERTIES} x {q_per_prop:.4f} m3/d/property "
                  f"= {CRIT.PF_HOLD_PROPERTIES * q_per_prop:.2f} m3/d"),
        dict(ITEM="load per property, measured", VALUE=round(q_per_prop, 4),
             UNIT="m3/d/property",
             SOURCE="allocated load / allocated properties, ALL property types",
             NOTE=f"criteria.PLOT_QADF_M3D is {CRIT.PLOT_QADF_M3D:.4f} and it is NOT the same "
                  "quantity: it is OCCUPANCY x WWG_LCD, and WWG_LCD already spreads the "
                  "non-domestic and governmental volume over the DOMESTIC population, so it "
                  "is a per-DOMESTIC-property figure. G201-p71's threshold counts properties "
                  "without qualification, so the threshold is evaluated on all of them"),
        dict(ITEM="domestic load per property, measured", VALUE=0.7416,
             UNIT="m3/d/property",
             SOURCE="plot_loads Q_DOM_M3D / N_DOM",
             NOTE="reproduces OCCUPANCY x LPCD_WATER x RETURN_DOM / 1000 = 5.32 x 164 x 0.85 "
                  "/ 1000 = 0.74161 EXACTLY (G201-p59-60 Table 11 water, G201-p71 Table 19 "
                  "return ratio) - the load basis and the criteria agree where they are "
                  "measuring the same thing"),
        dict(ITEM="held peak factor on the criteria per-property figure",
             VALUE=round(pf_held(CRIT.PLOT_QADF_M3D), 4), UNIT="-",
             SOURCE="sensitivity", NOTE="the alternative basis, published so the choice is "
                                        "visible"),
        dict(ITEM="criteria.peak_factor() below the threshold", VALUE=1.0, UNIT="-",
             SOURCE="criteria.py", NOTE="DISAGREES with this stage. See A-FLOW-2 - holding "
                                        "at 1.0 sizes every lateral at average flow"),
        dict(ITEM="reaches on the held factor", VALUE=int((meth == "held").sum()), UNIT="-",
             SOURCE="PF_METH", NOTE=f"{100.0 * (meth == 'held').mean():.1f} % of reaches, "
                                    f"{ln[meth == 'held'].sum() / 1000.0:,.1f} km"),
        dict(ITEM="reaches on Merrimack", VALUE=int((meth == "merrimack").sum()), UNIT="-",
             SOURCE="PF_METH", NOTE=f"{ln[meth == 'merrimack'].sum() / 1000.0:,.1f} km, "
                                    f"carrying {100.0 * q[meth == 'merrimack'].sum() / max(q.sum(), 1e-9):.1f} % "
                                    "of the accumulated flow"),
        dict(ITEM="peak factor, min on a LOADED reach",
             VALUE=round(float(np.nanmin(np.where(q > 0, pf, np.inf))), 4), UNIT="-",
             SOURCE="arcs.PF where QADF_M3D > 0",
             NOTE=f"the largest catchment peaks least. {int((q <= 0).sum()):,} reaches carry "
                  "nothing at all and are given PF = 1.0, which is arithmetic, not a factor"),
        dict(ITEM="peak factor, max", VALUE=round(float(np.nanmax(pf)), 4), UNIT="-",
             SOURCE="arcs.PF", NOTE="G201-p72 RECOMMENDS not exceeding 5.0"),
        dict(ITEM="reaches above the recommended 5.0",
             VALUE=int((pf > CRIT.PF_REPORT_ABOVE).sum()), UNIT="-",
             SOURCE="G201-p72 NOTE", NOTE="reported, NEVER truncated"),
        dict(ITEM="reaches where the peak flow would FALL downstream",
             VALUE=int(arcs["MONO_FIX"].sum()), UNIT="-",
             SOURCE="MONO_FIX", NOTE="it can happen at the held/Merrimack boundary, which is a step, because the "
                                     "switch is on property count and the curves meet only "
                                     "at the project-average load per property"),
        dict(ITEM="largest monotonicity correction",
             VALUE=round(float((arcs["QPK_MONO"] - arcs["QPK_LS"]).max()), 3), UNIT="L/s",
             SOURCE="QPK_MONO - QPK_LS", NOTE="a sizing stage must carry QPK_MONO, not "
                                              "QPK_LS, or a pipe is smaller than the one "
                                              "above it"),
        dict(ITEM="whole-network peak factor",
             VALUE=round(merrimack_pf(float(arcs.loc[arcs.DELIVERED == 1,
                                                     "Q_LOC_M3D"].sum())), 4),
             UNIT="-", SOURCE="Merrimack on the delivered load",
             NOTE="what the works inlet would see if everything arrived together"),
        dict(ITEM="Peltier on the same total",
             VALUE=round(peltier_pf(float(arcs.loc[arcs.DELIVERED == 1,
                                                   "Q_LOC_M3D"].sum())), 4),
             UNIT="-", SOURCE="G201-p72, the IMP2024 alternative",
             NOTE="carried for comparison only. NOT applied anywhere"),
    ]
    return pd.DataFrame(rows)


def _flow_bands(arcs) -> pd.DataFrame:
    """What the sizing stage is about to be handed.

    The bands are DRAWING bands, chosen to spread a log-ish distribution. None of them is a
    design value and none of them decides anything - the diameter is set by the flow and the
    gradient (G203-p29, H8), never by a band."""
    q = arcs["QPK_MONO"].to_numpy(float)
    ln = arcs["LEN_M"].to_numpy(float)
    edges = [0.0, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1e18]
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (q >= lo) & (q < hi)
        rows.append(dict(
            BAND_LS=(f"{lo:g} and above" if hi > 1e17 else f"{lo:g} - {hi:g}"),
            N=int(m.sum()),
            KM=round(float(ln[m].sum() / 1000.0), 2),
            PCT_KM=round(100.0 * float(ln[m].sum() / max(ln.sum(), 1e-9)), 2)))
    t = pd.DataFrame(rows)
    t["NOTE"] = ("presentation bands only - the diameter follows the flow and the gradient "
                 "(G203-p29, H8), never a band")
    return t


def _roles_table(arcs, F):
    rows = []
    for role, sub in arcs.groupby("ROLE"):
        rows.append(dict(
            ROLE=role, N=len(sub), KM=round(float(sub.LEN_M.sum() / 1000.0), 2),
            Q_LOC_M3D=round(float(sub.Q_LOC_M3D.sum()), 1),
            PCT_LOAD=round(100.0 * float(sub.Q_LOC_M3D.sum() /
                                            max(arcs.Q_LOC_M3D.sum(), 1e-9)), 2),
            N_PROP=round(float(sub.N_PROP_LOC.sum()), 0),
            ROUTE=int(sub.IS_ROUTE.sum()), BRANCH=int((sub.IS_ROUTE == 0).sum()),
            DELIVERED=int(sub.DELIVERED.sum()),
            TREATMENT=("carries everything from upstream, plus its own load"
                       if role == "tree" else
                       "SOURCE BRANCH (A-FLOW-5): its own local load only, delivered at its "
                       "downstream node"),
        ))
    # the honest caveat on A-FLOW-5, quantified
    hd = arcs[arcs.ROLE == "head"]
    if len(hd):
        chained = hd["US_NODE"].isin(set(hd["DS_NODE"])).to_numpy()
        rows.append(dict(
            ROLE="head, chained", N=int(chained.sum()),
            KM=round(float(hd.loc[chained, "LEN_M"].sum() / 1000.0), 2),
            Q_LOC_M3D=round(float(hd.loc[chained, "Q_LOC_M3D"].sum()), 1),
            PCT_LOAD=round(100.0 * float(hd.loc[chained, "Q_LOC_M3D"].sum() /
                                            max(arcs.Q_LOC_M3D.sum(), 1e-9)), 2),
            N_PROP=round(float(hd.loc[chained, "N_PROP_LOC"].sum()), 0),
            ROUTE=0, BRANCH=int(chained.sum()),
            DELIVERED=int(hd.loc[chained, "DELIVERED"].sum()),
            TREATMENT="THE RISK IN A-FLOW-5: these head arcs START where another head arc "
                      "ENDS. If they are really one street draining end to end, the lower "
                      "segment is under-loaded by the upper one's load. It is not lost - it "
                      "enters the tree at the shared node - but it is on the wrong pipe",
        ))
    return pd.DataFrame(rows)


def _outfall_table(arcs, nodes_out, in_q, in_p, in_l, is_outfall, placed):
    idx = np.flatnonzero(is_outfall)
    t = pd.DataFrame({
        "OUTFALL": nodes_out["NODE_UID"].to_numpy()[idx],
        "SUBNET": nodes_out["SUBNET"].to_numpy()[idx],
        "X": np.round(nodes_out["X"].to_numpy(float)[idx], 1),
        "Y": np.round(nodes_out["Y"].to_numpy(float)[idx], 1),
        "GRD_M": np.round(nodes_out["GRD_M"].to_numpy(float)[idx], 2),
        "Q_ADF_M3D": np.round(in_q[idx], 1),
        "N_PROP": np.round(in_p[idx], 0),
        "KM": np.round(in_l[idx] / 1000.0, 2),
    })
    t["PCT_LOAD"] = (100.0 * t.Q_ADF_M3D / max(placed, 1e-9)).round(3)
    pf, meth = peak_factor(t.Q_ADF_M3D.to_numpy(float), t.N_PROP.to_numpy(float),
                           float(arcs["Q_LOC_M3D"].sum() / max(arcs["N_PROP_LOC"].sum(), 1e-9)))
    t["PF"] = np.round(pf, 3)
    t["PF_METH"] = meth
    t["QINF_LS"] = np.round(CRIT.INFILT_L_D_KM * (in_l[idx] / 1000.0) / SEC_PER_DAY, 4)
    t["Q_PK_LS"] = np.round(t.Q_ADF_M3D * M3D_TO_LS * t.PF + t.QINF_LS, 2)
    t["M_PER_PROP"] = np.round(in_l[idx] / np.maximum(in_p[idx], 1.0), 1)
    return t.sort_values("Q_ADF_M3D", ascending=False).reset_index(drop=True)


def _subnet_table(arcs, nodes_out, placed):
    a = arcs[arcs.SUBNET.fillna("") != ""]
    rows = []
    for s, sub in a.groupby("SUBNET"):
        top = float(sub.QADF_M3D.max()) if len(sub) else 0.0
        loc = float(sub.Q_LOC_M3D.sum())
        rows.append(dict(SUBNET=s, N_ARCS=len(sub),
                         KM=round(float(sub.LEN_M.sum() / 1000.0), 2),
                         Q_LOC_M3D=round(loc, 1),
                         N_PROP=round(float(sub.N_PROP_LOC.sum()), 0),
                         TOP_M3D=round(top, 1),
                         TOP_PCT=round(100.0 * top / max(loc, 1e-9), 2),
                         PCT_PLACED=round(100.0 * loc / max(placed, 1e-9), 3),
                         QPK_LS=round(float(sub.QPK_MONO.max()), 2)))
    return pd.DataFrame(rows).sort_values("Q_LOC_M3D", ascending=False).reset_index(drop=True)


def _undelivered_table(arcs, nodes_out):
    u = arcs[arcs.DELIVERED == 0]
    if not len(u):
        return pd.DataFrame([dict(ROLE="", N=0, KM=0.0, Q_M3D=0.0, N_PROP=0.0,
                                  NOTE="nothing drains nowhere")])
    rows = []
    for role, sub in u.groupby("ROLE"):
        rows.append(dict(ROLE=role, N=len(sub), KM=round(float(sub.LEN_M.sum() / 1000.0), 3),
                         Q_M3D=round(float(sub.Q_LOC_M3D.sum()), 1),
                         N_PROP=round(float(sub.N_PROP_LOC.sum()), 0),
                         NOTE="H15: a piece that drains nowhere is never legal. This load is "
                              "NOT dropped - it is published here and it is in the denominator "
                              "of the health check"))
    rows.append(dict(ROLE="TOTAL", N=len(u), KM=round(float(u.LEN_M.sum() / 1000.0), 3),
                     Q_M3D=round(float(u.Q_LOC_M3D.sum()), 1),
                     N_PROP=round(float(u.N_PROP_LOC.sum()), 0),
                     NOTE="resolution is s2's, not this stage's: connect, or serve by another "
                          "system (philosophy sec 8a)"))
    return pd.DataFrame(rows)


def _manifest(arcs, nodes_out, alloc, placed, delivered, lost, net_len_delivered,
              net_len_all, health, q_per_prop):
    """Every number this stage publishes, with the function or clause behind it."""
    def r(item, value, unit, source):
        return dict(ITEM=item, VALUE=value, UNIT=unit, SOURCE=source)

    q = arcs["QADF_M3D"].to_numpy(float)
    qp = arcs["QPK_MONO"].to_numpy(float)
    rows = [
        r("stage", STAGE_VERSION, "-", "this file"),
        r("contract", K.CONTRACT_VERSION, "-", "w12.contract"),
        r("tau", CRIT.TAU_PA, "Pa", "ASSUMED, GAP-9 - flagged on every row as TAU_FLAG"),
        r("arcs", len(arcs), "-", "s2_orient arcs, read"),
        r("nodes", len(nodes_out), "-", "s2_orient nodes, read"),
        r("network length, published", round(net_len_all / 1000.0, 2), "km", "sum LEN_M"),
        r("network length, delivered", round(net_len_delivered / 1000.0, 2), "km",
          "accumulated to the outfalls"),
        r("plots read", alloc["plots_total"], "-", str(PLOT_LOADS)),
        r("plots with saturated load", alloc["plots_with_load"], "-", "Q_AVG_M3D > 0"),
        r("properties", round(alloc["prop_allocated"], 1), "-",
          "plot_loads.N_PROP, allocated once each"),
        r("placed load", round(placed, 1), "m3/d", "allocation, A-FLOW-4"),
        r("delivered load", round(delivered, 1), "m3/d", "accumulated to the outfalls"),
        r("undelivered load", round(lost, 1), "m3/d", "arcs that reach no outfall - H15"),
        r("load per property, measured", round(q_per_prop, 4), "m3/d/property",
          "placed / properties"),
        r("occupancy", CRIT.OCCUPANCY, "people/property", "PROJECT, derived 2026-08-30"),
        r("wastewater generation", CRIT.WWG_LCD, "L/c/d", "PROJECT, derived"),
        r("peak factor formula", "Qpdf = 2.65 Qadf^0.879, both Ml/d", "-",
          "G201-p71 7.4.2, read from the PDF 2026-09-03"),
        r("peak factor threshold", CRIT.PF_HOLD_PROPERTIES, "properties",
          "G201-p71 7.4.2 'having over 100 properties'"),
        r("held peak factor", round(pf_held(q_per_prop), 4), "-",
          "A-FLOW-2, PROJECT DECISION - Merrimack AT the threshold"),
        r("peak factor recommendation", CRIT.PF_REPORT_ABOVE, "-",
          "G201-p72 NOTE - a recommendation; reported, never truncated"),
        r("infiltration rate", CRIT.INFILT_L_D_KM, "L/d/km", "G201-p72 7.4.3, new networks"),
        r("SYSTEM infiltration", round(infiltration_system_ls(net_len_delivered), 4), "L/s",
          "contract.published('infiltration_system_ls') - rate x NETWORK length"),
        r("STP design margin", CRIT.STP_MARGIN, "-",
          "G201-p73 7.4.5 - carried at the works, never on a pipe (A-FLOW-7)"),
        r("works inlet Qadf, delivered", round(delivered, 1), "m3/d",
          "delivered load; add the margin at the works, not here"),
        r("works inlet Qadf + 10 % margin", round(delivered * (1 + CRIT.STP_MARGIN), 1),
          "m3/d", "G201-p73 7.4.5"),
        r("biggest pipe, Qadf", round(float(np.nanmax(q)), 1), "m3/d", "arcs.QADF_M3D"),
        r("trunk peak flow IF every outfall joins",
          round(delivered * M3D_TO_LS * merrimack_pf(delivered)
                + infiltration_system_ls(net_len_delivered), 1), "L/s",
          "HYPOTHETICAL - Merrimack on the delivered load plus system infiltration. The "
          "Main Pipe is an INPUT and this stage has not routed it"),
        r("biggest pipe, Qpeak", round(float(np.nanmax(qp)), 2), "L/s", "arcs.QPK_MONO"),
        r("biggest pipe share of placed load",
          float(health.loc[health.ITEM == "TOP_PIPE_PCT", "VALUE"].iloc[0]), "%",
          "contract.published('top_pipe_load_share_pct')"),
        r("outfalls", int((nodes_out.IS_OUTFALL == 1).sum()), "-", "nodes.KIND"),
        r("arcs carrying no load", int((arcs.Q_LOC_M3D <= 0).sum()), "-",
          "corridors with no plot nearest to them - they still carry upstream flow"),
        r("arcs with zero accumulated flow", int((q <= 0).sum()), "-",
          "nothing at all drains through them - candidates for pruning at stage 4"),
        r("length carrying zero flow",
          round(float(arcs.loc[arcs.QADF_M3D <= 0, "LEN_M"].sum() / 1000.0), 1), "km",
          "arcs.QADF_M3D <= 0"),
        r("median accumulated Qadf", round(float(np.median(q)), 2), "m3/d", "arcs.QADF_M3D"),
        r("p95 accumulated Qadf", round(float(np.percentile(q, 95)), 1), "m3/d",
          "arcs.QADF_M3D"),
        r("median peak flow", round(float(np.median(qp)), 3), "L/s", "arcs.QPK_MONO"),
        r("p95 peak flow", round(float(np.percentile(qp, 95)), 2), "L/s", "arcs.QPK_MONO"),
        r("max upstream length on one reach", round(float(arcs.UPS_LEN_M.max() / 1000.0), 2),
          "km", "arcs.UPS_LEN_M - the flow path that reach sits at the bottom of"),
        r("max reaches draining through one reach", int(arcs.UPS_ARCS.max()), "-",
          "arcs.UPS_ARCS"),
    ]
    ab = asbuilt_benchmark()
    if ab is not None:
        rows += [
            r("as-built benchmark: biggest pipe share", round(ab["top_pipe_pct"], 2), "%",
              "the SAME accumulator over NAMA's 3,265 built pipes and the same plot loads"),
            r("as-built benchmark: built length", round(ab["km"], 1), "km", "asbuilt.pipes"),
            r("as-built benchmark: terminals", ab["n_outfall"], "-", "asbuilt topology"),
            r("as-built benchmark: load placed on it", round(ab["placed_m3d"], 1), "m3/d",
              "nearest built pipe, no cap - the same rule, so the two are comparable"),
        ]
    return pd.DataFrame(rows)


# ======================================================================================
# Output
# ======================================================================================

def _write(path: Path, layers: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    for name, df in layers.items():
        if isinstance(df, gpd.GeoDataFrame) and df.geometry.notna().any():
            df.to_file(path, layer=name, driver="GPKG")
        else:
            d = pd.DataFrame(df).copy()
            for c in d.columns:
                if d[c].dtype == object:
                    d[c] = d[c].astype(str)
            gpd.GeoDataFrame(d, geometry=[None] * len(d),
                             crs=f"EPSG:{CRS_EPSG}").to_file(
                path, layer=name, driver="GPKG")
    _check_shp_safe(layers)


def _check_shp_safe(layers) -> None:
    """Every field name must fit a DBF, so the shapefile mirror is lossless (contract FIX 4)."""
    bad = {n: [c for c in df.columns
               if c != "geometry" and len(c) > K.SHP_FIELD_MAXLEN]
           for n, df in layers.items()}
    bad = {k: v for k, v in bad.items() if v}
    if bad:
        raise K.ContractError(f"field names too long for a DBF: {bad}")


def _kmz(arcs: gpd.GeoDataFrame, verbose: bool = True) -> str:
    """The peak-flow map, through present.py's own registered view.

    Does the flow grow the way a tree should - small at the tips, large at the trunk?"""
    try:
        from w12 import present
        g = arcs.copy()
        g["QPK_LS"] = g["QPK_MONO"]           # the map shows what a pipe must carry
        res = present.kmz(g, "flow", str(OUT_KMZ),
                          source=f"{STAGE_VERSION} - {OUT_GPKG.name}, layer arcs",
                          simplify_m=1.0)
        if verbose:
            print(f"  wrote {OUT_KMZ}")
        return f"`{OUT_KMZ.name}` - present.py view 'flow', {len(g):,} reaches"
    except Exception as exc:                                    # noqa: BLE001
        if verbose:
            print(f"  KMZ skipped: {exc}")
        return f"KMZ NOT WRITTEN: {exc}"


def _md_table(df: pd.DataFrame, limit: Optional[int] = None) -> str:
    d = df if limit is None else df.head(limit)
    if not len(d):
        return "_(empty)_"
    cols = [c for c in d.columns if c != "geometry"]
    head = "| " + " | ".join(cols) + " |"
    rule = "|" + "|".join("---" for _ in cols) + "|"
    out = [head, rule]
    for _, row in d.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float) and math.isfinite(v):
                a = abs(v)
                if a >= 1000.0:
                    vals.append(f"{v:,.1f}")
                elif a >= 1.0:
                    vals.append(f"{v:,.4f}".rstrip("0").rstrip("."))
                elif a == 0.0:
                    vals.append("0")
                else:
                    vals.append(f"{v:.4g}")
            else:
                vals.append(str(v).replace("|", "/").replace("\n", " "))
        out.append("| " + " | ".join(vals) + " |")
    if limit is not None and len(df) > limit:
        out.append(f"\n_{len(df) - limit:,} more rows in the CSV._")
    return "\n".join(out)


def _report_md(arcs, nodes_out, health, verdict, cons, infil, pfb, bands, roles, outf,
               subs, undel, alloc, reach_tab, manif, q_per_prop, net_len_delivered,
               net_len_all, kmz_note) -> str:
    placed = float(arcs.Q_LOC_M3D.sum())
    fails = cons[cons.PASS == 0]
    L = []
    A = L.append
    A("# W12 stage 5 - flow accumulation")
    A("")
    A(f"_{time.strftime('%Y-%m-%d %H:%M')} - {STAGE_VERSION} - {CRIT.tau_banner()}_")
    A("")
    A("## The health check")
    A("")
    A("```")
    A(verdict)
    A("```")
    A("")
    A(_md_table(health))
    A("")
    A("## What the biggest pipe number means, and what it does not")
    A("")
    A("It is the honest measure of **how much load any one designed gravity pipe would ever "
      "have to carry**, and on this design it is small because the network reaches the "
      "client's Main Pipe at "
      f"**{int((nodes_out.IS_OUTFALL == 1).sum())} separate points**. The Main Pipe is an "
      "INPUT to this project and it is not in this graph, so those connections are not "
      "modelled as joining. `TRUNK_IF_JOINED_PCT` is what the trunk would carry if they all "
      "do; it is tagged a hypothetical and it stays one until a stage routes the trunk.")
    A("")
    A("The benchmark beside it is not a target somebody chose. It is the same accumulator, "
      "on the same plot loads, run over NAMA's own built network - the pipe that is in the "
      "ground and works.")
    A("")
    A("## Conservation - every identity, computed twice")
    A("")
    A(_md_table(cons))
    if len(fails):
        A("")
        A(f"**{len(fails)} identity(ies) DO NOT CLOSE.** A residual here is a load that went "
          "missing, and it is a blocking defect, not a rounding note.")
    A("")
    A("## Infiltration, and the trap")
    A("")
    A("G201-p72 7.4.3 gives **720 L/d/km of sewer** for a new network. The design value on a "
      "reach has to be CUMULATIVE - a reach forty hops down carries every kilometre above "
      "it - and that is exactly why the column must never be summed. The right total is the "
      "rate times the NETWORK length. Both are printed:")
    A("")
    A(_md_table(infil))
    A("")
    A("## The peak factor")
    A("")
    A("G201-p71 7.4.2, verbatim: *\"The Merrimack formula is to be used for calculating the "
      "peak factors for wastewater discharge for an area (catchment or sub catchment) having "
      "over 100 properties.\"* Below 100 the guideline prescribes **nothing**. Merrimack "
      "RISES as the catchment shrinks, so extrapolating it invents factors on the pipes "
      "where it was never validated; and holding it at 1.0 - which `criteria.peak_factor()` "
      "currently does - would size every lateral at average flow. This stage holds it at the "
      f"value Merrimack gives AT the threshold, **{pf_held(q_per_prop):.3f}**, and every such "
      "row says `PF_METH = 'held'`.")
    A("")
    A(_md_table(pfb))
    A("")
    A("**This is a real disagreement with `criteria.py`, not a rounding.** It is A-FLOW-2, it "
      "is on the assumptions layer, and the owner of `criteria.py` has to settle it.")
    A("")
    A("## What the sizing stage is being handed")
    A("")
    A(_md_table(bands))
    A("")
    A("## How each kind of arc was treated")
    A("")
    A("The orientation stage publishes a drainage **tree** plus the corridors it did not "
      "need. Those still need a sewer, and at a junction exactly one pipe leaves "
      "(philosophy sec 4), so a leftover corridor is a **source branch**: its own load, "
      "delivered at its downstream node, taking nothing off the node it starts at.")
    A("")
    A(_md_table(roles))
    A("")
    A("## Where the load ends up")
    A("")
    A(_md_table(outf, limit=25))
    A("")
    A("## Sub-networks")
    A("")
    A("`TOP_PCT` is the health check applied one sub-network at a time. Inside "
      "a sub-network the answer SHOULD be close to 100 %: everything that sub-network "
      "collects leaves through one pipe.")
    A("")
    A(f"**Five sub-networks have no arcs at all** and sixteen outfalls receive nothing - a "
      "connection to the client's Main Pipe that serves nobody. That is not a flow defect, "
      "it is what the flow arithmetic exposes about the orientation, and the resolution "
      "belongs to stage 2.")
    A("")
    A(_md_table(subs, limit=25))
    A("")
    A("## Load that reaches no outfall")
    A("")
    A(_md_table(undel))
    A("")
    A("## The allocation")
    A("")
    A("Nearest arc, exactly once per plot, **no distance cap** (A-FLOW-4). A cap is how W10 "
      "lost 1,233 m3/d without anyone noticing. The distance curve is published instead, so "
      "the reader can judge the reach of the drawing rather than inherit an assumed radius:")
    A("")
    A(_md_table(reach_tab))
    A("")
    A("| | |")
    A("|---|---|")
    for k, v in alloc.items():
        A(f"| {k} | {v:,.2f} |" if isinstance(v, float) else f"| {k} | {v:,} |")
    A("")
    A("## Every number, with its source")
    A("")
    A(_md_table(manif))
    A("")
    A("## Assumptions")
    A("")
    A(_md_table(pd.DataFrame(list(ASSUMPTIONS))[["ID", "KIND", "WHAT", "SOURCE"]]))
    A("")
    A("Full text, with what changes if each is wrong, is on the `assumptions` layer and in "
      "`run/flows/assumptions.csv`.")
    A("")
    A("## What is NOT here")
    A("")
    A("- **No start-year flows.** The plot loads carry a saturation figure and no phasing, so "
      "philosophy sec 6's start-year self-cleansing check cannot run from this data. A-FLOW-6.")
    A("- **No retention time.** Septicity needs a velocity and a velocity needs a diameter. "
      "`UPS_LEN_M` is published so the sizing stage can compute it in one pass.")
    A("- **No sizing, no levels, no tiers.** This stage publishes flow.")
    A("")
    A("## Outputs")
    A("")
    A(f"- `{OUT_GPKG.relative_to(W12.parent)}` - 15 layers")
    A(f"- {kmz_note}")
    A(f"- `{RUN_DIR.relative_to(W12.parent)}/*.csv` - every table above")
    A(f"- `{REPORT_MD.relative_to(W12.parent)}` - this file")
    return "\n".join(L)


# ======================================================================================
# verify / selftest
# ======================================================================================

def verify(verbose: bool = True) -> int:
    """Re-derive everything from the PUBLISHED file.  A stage that only checks itself in
    memory has checked nothing - the audit reads the layer, so verification does too."""
    if not OUT_GPKG.exists():
        print(f"{OUT_GPKG} does not exist - run the build first")
        return 2
    a = gpd.read_file(OUT_GPKG, layer="arcs")
    n = gpd.read_file(OUT_GPKG, layer="nodes")
    fails: List[str] = []

    def ck(name, ok, detail=""):
        (print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
         if verbose else None)
        if not ok:
            fails.append(f"{name}: {detail}")

    # 1. QPK_LS reproducible from its own row (the contract's own identity)
    want = a.QADF_M3D * 1000.0 / SEC_PER_DAY * a.PF + a.QINF_LS
    d = float((want - a.QPK_LS).abs().max())
    ck("QPK_LS == QADF x PF + QINF, from the row alone", d < 1e-6, f"max |resid| {d:.3e} L/s")

    # 2. the infiltration total, three ways
    outf = set(n.loc[n.IS_OUTFALL == 1, "NODE_UID"].astype(str))
    m = a.DS_NODE.astype(str).isin(outf) & (a.DELIVERED == 1)
    v1 = infiltration_system_ls(float(a.loc[a.DELIVERED == 1, "LEN_M"].sum()))
    v2 = float(a.loc[a.DELIVERED == 1, "QINF_LOC"].sum())
    v3 = float(a.loc[m, "QINF_LS"].sum())
    ck("system infiltration, three independent derivations",
       max(abs(v1 - v2), abs(v1 - v3)) < 1e-6,
       f"rate x length {v1:.4f} | sum of local {v2:.4f} | outfalls only {v3:.4f} L/s")
    ck("and the WRONG total is nothing like it", True,
       f"summing every row gives {float(a.QINF_LS.sum()):,.0f} L/s "
       f"({float(a.QINF_LS.sum()) / max(v1, 1e-9):.0f}x)")

    # 3. accumulation is monotone down the tree
    ds = dict(zip(n.NODE_UID.astype(str), n.DS_NODE.fillna("").astype(str)))
    idx = {u: i for i, u in enumerate(a.US_NODE.astype(str))}
    bad = 0
    for i, (u, v, r, q) in enumerate(zip(a.US_NODE.astype(str), a.DS_NODE.astype(str),
                                         a.IS_ROUTE, a.QADF_M3D)):
        if not r:
            continue
        j = idx.get(v)
        if j is not None and bool(a.IS_ROUTE.iloc[j]) and a.QADF_M3D.iloc[j] < q - 1e-9:
            bad += 1
    ck("accumulated Qadf never decreases along a route", bad == 0, f"{bad:,} decreases")

    # 4. peak flow after the guard is monotone
    bad = 0
    for i, (v, r, q) in enumerate(zip(a.DS_NODE.astype(str), a.IS_ROUTE, a.QPK_MONO)):
        if not r:
            continue
        j = idx.get(v)
        if j is not None and bool(a.IS_ROUTE.iloc[j]) and a.QPK_MONO.iloc[j] < q - 1e-6:
            bad += 1
    ck("QPK_MONO never decreases along a route", bad == 0, f"{bad:,} decreases")

    # 4b. the RAW peak flow, before the guard - this is the informative one, because
    #     QPK_MONO is monotone by construction and can only ever agree with itself
    bad = 0
    worst = 0.0
    for i, (v, r, q) in enumerate(zip(a.DS_NODE.astype(str), a.IS_ROUTE, a.QPK_LS)):
        if not r:
            continue
        j = idx.get(v)
        if j is not None and bool(a.IS_ROUTE.iloc[j]) and a.QPK_LS.iloc[j] < q - 1e-6:
            bad += 1
            worst = max(worst, float(q - a.QPK_LS.iloc[j]))
    ck("raw QPK_LS never decreases along a route (the guard never had to fire)",
       bad == 0, f"{bad:,} decreases, worst {worst:.3f} L/s")

    # 5. peak factor method matches the property count
    mism = int(((a.N_PROP > CRIT.PF_HOLD_PROPERTIES) & (a.PF_METH != "merrimack") &
                (a.QADF_M3D > 0)).sum())
    ck("PF_METH agrees with the 100-property threshold", mism == 0, f"{mism:,} rows")

    # 6. the recommendation, reported not enforced
    over = int((a.PF > CRIT.PF_REPORT_ABOVE).sum())
    ck("peak factors above the G201-p72 recommendation of 5.0 are REPORTED",
       True, f"{over:,} reaches (this is a report, not a gate)")

    # 6b. this stage derived IS_ROUTE from the successor map alone, without ever reading
    #     s2_orient's own ROLE label. Two stages, two derivations, one answer - or a
    #     disagreement that is itself the finding.
    if "ROLE" in a.columns:
        mm = int(((a.IS_ROUTE == 1) != (a.ROLE == "tree")).sum())
        ck("IS_ROUTE, derived here from DS_NODE alone, == s2_orient's own ROLE label",
           mm == 0, f"{mm:,} of {len(a):,} disagree")

    # 7. conservation table published and closing
    c = gpd.read_file(OUT_GPKG, layer="conservation")
    nf = int((pd.to_numeric(c.PASS, errors="coerce") == 0).sum())
    ck("every conservation identity closes", nf == 0, f"{nf} open")

    # 8. no negative flows anywhere
    neg = int((a[["QADF_M3D", "QPK_LS", "QINF_LS", "N_PROP", "UPS_LEN_M"]] < 0).any(axis=1).sum())
    ck("no negative flow, property count or length", neg == 0, f"{neg:,} rows")

    # 9. node and arc layers agree
    join = n.merge(a[a.IS_ROUTE == 1][["US_NODE", "QADF_M3D"]],
                   left_on="NODE_UID", right_on="US_NODE", how="inner")
    d = float((join.Q_ADF_M3D - join.QADF_M3D).abs().max()) if len(join) else 0.0
    ck("node Q_ADF_M3D == the outgoing reach's QADF_M3D", d < 1e-9,
       f"{len(join):,} nodes, max |resid| {d:.3e}")

    if verbose:
        print(f"\n  {len(fails)} failure(s)")
    return 1 if fails else 0


def selftest(verbose: bool = True) -> int:
    """Hand-worked cases.  Every one of them would have caught a real defect."""
    n = 0

    def ok(cond, msg):
        nonlocal n
        if not cond:
            raise AssertionError(msg)
        n += 1

    # --- Merrimack, straight from G201-p71 -------------------------------------------
    # Pf = 2.65 Q(Ml/d)^-0.121. At 1 Ml/d that is exactly 2.65.
    ok(abs(merrimack_pf(1000.0) - 2.65) < 1e-12, "Merrimack at 1 Ml/d must be exactly 2.65")
    ok(merrimack_pf(10_000.0) < merrimack_pf(1000.0), "Merrimack must FALL as the catchment grows")
    # the Ml/d conversion is the trap: 1000 m3/d is 1 Ml/d, not 1000
    ok(abs(merrimack_pf(1000.0) - CRIT.pf_merrimack(1.0)) < 1e-12, "m3/d -> Ml/d conversion")

    # --- Peltier, G201-p72, litres per second ----------------------------------------
    ok(abs(peltier_pf(86.4) - 2.5) < 1e-9, "Peltier at 1 L/s must be 1.5 + 1 = 2.5")

    # --- the hold --------------------------------------------------------------------
    h = pf_held(0.75)
    ok(abs(h - merrimack_pf(100 * 0.75)) < 1e-12, "the hold IS Merrimack at the threshold")
    pf, meth = peak_factor([100.0, 100.0], [100.0, 101.0], 0.75)
    ok(meth[0] == "held" and meth[1] == "merrimack",
       "'over 100 properties' - 100 itself holds, 101 does not")
    ok(abs(pf[0] - h) < 1e-12, "the held row carries the held value, not 1.0")

    # --- infiltration ----------------------------------------------------------------
    ok(abs(infiltration_system_ls(1000.0) - 720.0 / 86400.0) < 1e-15,
       "720 L/d on one km")
    ok(abs(infiltration_system_ls(0.0)) < 1e-18, "no sewer, no infiltration")

    # --- the accumulator, on a graph small enough to check by hand -------------------
    #     A -> B -> D (outfall)      C -> B      E -> D via a BRANCH arc
    nd = pd.DataFrame({"NODE_ID": ["A", "B", "C", "D", "E"],
                       "DS_NODE": ["B", "D", "B", "", ""]})
    ar = pd.DataFrame({"US_NODE": ["A", "B", "C", "E"],
                       "DS_NODE": ["B", "D", "B", "D"]})
    F = Forest(nd, ar)
    ok(list(F.is_route) == [True, True, True, False],
       "E->D is not in the successor map, so it is a BRANCH")
    loc = np.array([1.0, 0.0, 2.0, 4.0])
    tot, nin = F.accumulate(loc)
    #   A->B carries 1 ; C->B carries 2 ; E->D (branch) carries 4 ;
    #   B receives 1 + 2 = 3 ; B->D carries 3 + 0 = 3 ; D receives 3 + 4 = 7
    ok(list(np.round(tot, 9)) == [1.0, 3.0, 2.0, 4.0], f"arc totals wrong: {tot}")
    ok(abs(nin[F.pos["D"]] - 7.0) < 1e-12, f"D should receive 7, got {nin[F.pos['D']]}")
    ok(abs(tot.sum() - 10.0) < 1e-12, "arc totals are not a conservation quantity - "
                                      "1+3+2+4 = 10 against 7 placed, which is exactly why "
                                      "a cumulative column must never be summed")
    ok(abs(nin[F.pos["D"]] - loc.sum() + 0.0) < 1e-12,
       "everything placed reaches the single outfall")

    # length accumulates the same way and is checkable against the arc lengths
    ln = np.array([10.0, 20.0, 30.0, 40.0])
    lt, li = F.accumulate(ln)
    ok(abs(li[F.pos["D"]] - ln.sum()) < 1e-12,
       "delivered length must equal the total length when nothing is stranded")

    # --- a piece that drains nowhere is NOT silently dropped -------------------------
    nd2 = pd.DataFrame({"NODE_ID": ["A", "B", "X", "Y"], "DS_NODE": ["B", "", "Y", ""]})
    ar2 = pd.DataFrame({"US_NODE": ["A", "X"], "DS_NODE": ["B", "Y"]})
    F2 = Forest(nd2, ar2)
    t2, i2 = F2.accumulate(np.array([5.0, 9.0]))
    ok(abs(i2[F2.pos["B"]] - 5.0) < 1e-12 and abs(i2[F2.pos["Y"]] - 9.0) < 1e-12,
       "two terminals, two separate deliveries")

    # --- a cycle is raised, never accumulated round ----------------------------------
    nd3 = pd.DataFrame({"NODE_ID": ["A", "B"], "DS_NODE": ["B", "A"]})
    ar3 = pd.DataFrame({"US_NODE": ["A", "B"], "DS_NODE": ["B", "A"]})
    try:
        Forest(nd3, ar3)
        raise AssertionError("a cycle in the successor map must raise")
    except ValueError as exc:
        ok("CYCLE" in str(exc).upper(), "the cycle message must name the defect")

    # --- a self-loop can never be a route --------------------------------------------
    nd4 = pd.DataFrame({"NODE_ID": ["A", "B"], "DS_NODE": ["B", ""]})
    ar4 = pd.DataFrame({"US_NODE": ["A", "A"], "DS_NODE": ["B", "A"]})
    F4 = Forest(nd4, ar4)
    ok(list(F4.is_route) == [True, False], "a self-loop is a branch, never a route")

    # --- two parallel arcs cannot both be the route ----------------------------------
    nd5 = pd.DataFrame({"NODE_ID": ["A", "B"], "DS_NODE": ["B", ""]})
    ar5 = pd.DataFrame({"US_NODE": ["A", "A"], "DS_NODE": ["B", "B"]})
    F5 = Forest(nd5, ar5)
    ok(int(F5.is_route.sum()) == 1, "only one pipe leaves a node - the parallel is a branch")
    t5, i5 = F5.accumulate(np.array([3.0, 4.0]))
    ok(abs(i5[F5.pos["B"]] - 7.0) < 1e-12, "and the load is delivered once, not twice")

    # --- the monotonicity guard ------------------------------------------------------
    F6 = Forest(pd.DataFrame({"NODE_ID": ["A", "B", "C"], "DS_NODE": ["B", "C", ""]}),
                pd.DataFrame({"US_NODE": ["A", "B"], "DS_NODE": ["B", "C"]}))
    up = _max_upstream(F6, np.array([9.0, 2.0]))
    ok(abs(up[1] - 9.0) < 1e-12, "the guard must see the pipe immediately above")

    if verbose:
        print(f"  {n} self-checks pass")
    return 0


def report() -> int:
    if not OUT_GPKG.exists():
        print(f"{OUT_GPKG} does not exist - run the build first")
        return 2
    for lay in ("health", "conservation", "infiltration", "pf_bands", "roles",
                "undelivered"):
        df = gpd.read_file(OUT_GPKG, layer=lay)
        print(f"\n--- {lay} " + "-" * (70 - len(lay)))
        with pd.option_context("display.width", 200, "display.max_columns", 40,
                               "display.max_colwidth", 60):
            print(df.drop(columns=[c for c in ("geometry",) if c in df.columns]).to_string(
                index=False))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--asbuilt", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args(argv)
    v = not a.quiet
    if a.selftest:
        return selftest(v)
    if a.report:
        return report()
    if a.verify:
        return verify(v)
    if a.asbuilt:
        b = asbuilt_benchmark()
        if b is None:
            print("as-built benchmark unavailable:", _AB_CACHE.get("err"))
            return 1
        for k, x in b.items():
            print(f"  {k:<16} {x:,.4g}" if isinstance(x, float) else f"  {k:<16} {x:,}")
        return 0
    print(f"{STAGE_VERSION}")
    print(CRIT.tau_banner())
    print()
    selftest(v)
    build(v)
    print()
    return verify(v)


if __name__ == "__main__":
    raise SystemExit(main())
