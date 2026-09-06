"""
s3_hierarchy.py - W12 stage 3.  THE HIERARCHY, ON THE ORIENTED TREE.

WHAT THIS STAGE IS FOR
----------------------
`s2_orient` decided WHICH WAY every corridor drains and produced an in-tree over 9,550 of
the 12,816 arcs.  It left three things undone and said so in its own manifest:

    heads_needing_setback   2887   "a chamber that already has an outlet, so the chamber
                                    stage must set them back 10 m ... A HAND-OVER NUMBER"
    island_km               30.88  184 arcs that cannot reach the Main Pipe at all, each
                                    pointed downhill on its own, with no outfall and - as
                                    it turns out - cycles among them
    (no tier anywhere)             every arc is one undifferentiated corridor

This stage does those three, in that order, and measures the result against NAMA's built
network rather than against a target somebody liked.

THE HARD RULE, AND IT IS THE POINT OF THE STAGE
-----------------------------------------------
    AT A JUNCTION, EXACTLY ONE PIPE LEAVES.

Every other line meeting there is a HEAD: a run that STARTS at that point and drains away
down its own corridor, carrying none of the junction's flow.  A head is not an outlet.
Before this stage the published arc set has 2,718 nodes with two, three or four outgoing
arcs and 2,988 arcs too many - a layer that is CONNECTED but not BUILDABLE, because no
contractor can build two outlets in one chamber and no operator can rod them.

    A HEAD BEGINS AT THE FIRST HOUSE GATE - the point on the corridor at the foot of the
    perpendicular from the first plot's centroid.  NEVER at the end of a road line.

That second sentence is the one that costs money if it is ignored: a head starting at the
road end buys pipe upstream of every customer it serves.  The exceptions to the hard rule
are counted in `exceptions`, and the count must be ZERO.  It is a published layer, not a
console line, so the claim can be checked next month.

THE TIER VOCABULARY, STATED - philosophy sec 4 requires this and it is NOT pedantry
------------------------------------------------------------------------------------
Two vocabularies are in play and they use the SAME WORD for different things:

  G203-p17 sec 3.2   PCC -> PC Sewer -> HCC -> (Rider Sewer) -> LATERAL SEWER -> Main Sewer.
                     Here a "Lateral Sewer" is a TERTIARY pipe with a "Maximum Length 45 m"
                     (G203-p22 Table 6).  It is the pipe from a house connection chamber to
                     the street sewer.
  NAMA's own IDs     5A-2-TM-MH185 (trunk main) / 5A-2-SM.2-MH391 (sub main) /
                     5A-1-A49-MH3 (a lateral ZONE).  Here a "lateral" is A STREET RUN, and
                     the built median run between junctions is 68.74 m with a p90 of
                     218.6 m - lengths the 45 m rule would forbid outright.

THIS STAGE USES NAMA'S VOCABULARY, because the design has to read like the network next
door and because the built network is the only calibration that exists.  Consequently:

    *** G203's 45 m "Maximum Length" DOES NOT APPLY to the `lateral` tier published here. ***

It applies to the tertiary pipe, which stage 5b mints and which is not in this layer at all.
`criteria.LATERAL_MAX_LEN` is therefore READ, PRINTED and NOT ENFORCED here, with this
sentence beside it.  Enforcing it on street runs would condemn 71 % of NAMA's own built
length, and quoting a guideline number against the wrong object is how eight numbers came to
be retracted in three days.

The tier set published is `contract.TIERS` minus `rider`:  lateral / main / sub main /
trunk main.  `rider` is tertiary and belongs to stage 5b.

WHAT DECIDES A TIER
-------------------
Tiers are assigned to RUNS, not to arcs, because a lateral is defined as "one unbranched
street run" and an arc is only a piece of one.  A run is a maximal chain of arcs through
chambers that have exactly one pipe in and one pipe out - the same definition
`asbuilt.m_runs()` uses on the built network, so the two numbers are comparable.

    trunk main   the client's Main Pipe.  AN INPUT, not a derivation.  G203-p35 sec 5 gives
                 NWS's three criteria (D > 800 mm, "Length above 1,000 mm [sic - 1,000 m]
                 without connexions", upstream of the STP or the main pumping station); the
                 drawn alignment satisfies the third by construction.  Traced from the
                 outfall backwards means: everything else drains INTO it.
    sub main     a collector defined by its OUTLET.  The run through which at least
                 SUBMAIN_KM of network drains.  Every catchment gets one by construction,
                 because the run at the outfall always drains the whole catchment - which is
                 what "defined by its outlet, not by a load threshold" means.  SUBMAIN_KM is
                 CALIBRATED against the built sub-main share, and the sweep is published.
    main         a run past the lateral budget: more than 3 laterals, or more than 750 m of
                 flow path, upstream of it (philosophy sec 4).
    lateral      everything else - a street run at the top of the tree.

All three thresholds are monotone downstream, so the hierarchy cannot invert: a lateral can
never receive a main.  That is checked, not assumed (`tier_inversions`, must be 0).

THE CALIBRATION IS MEASURED PER SUB-NETWORK, NOT AS A NETWORK AVERAGE
---------------------------------------------------------------------
`_BRAIN/10_ASBUILT_CALIBRATION.md` sec 1 gives five structural gates, and rule T2 of that
file gives the reason they bind per sub-network rather than per design: *"One package is one
connected component with exactly one outlet."*  That is what a sub-network is here, so the
bands measured BETWEEN NAMA'S PACKAGES are the bands a sub-network is held to.  The file is
explicit about why an average will not do:

    "Tier length shares ... PER SUBNETWORK: trunk 1.5-13.5 %, sub-main 10.9-17.2 %.
     A subnetwork with 0 % sub-main FAILS even if the average passes."

    tier length share      trunk and sub main, against the measured package bands
    chain depth            lateral -> main: median <= 2, p90 <= 4, absolute 5
    lateral-zone density   > 7 zones/km means THE MAIN TIER IS MISSING
    hierarchy ratio        lateral runs into another lateral, 60-78 %

Three consequences, and the first is a bug this stage had been carrying:

  1  `tiers()` had always CLAIMED in its own docstring that "every catchment gets one by
     construction, because the run at the outfall always drains the whole catchment", and
     the code tested `run_sub_km >= submain_km` and nothing else - so a sub-network smaller
     than the threshold got NO collector tier at all.  s2's outfall rule multiplies the
     number of small sub-networks, which turns a rare case into the common one.  The outlet
     clause is now written down: the run that discharges a component is a sub main whatever
     its accumulated length, and the monotonicity a tier depends on is safe because that run
     has the largest accumulated length in its component.
  2  `label_subnets()` puts a SUBNET on EVERY published reach, taken from this stage's own
     forest.  s2 leaves it blank on the heads, the islands and every corridor its tree did
     not use - about a fifth of the length - and a reach nobody can attribute cannot be
     calibrated.  An island keeps its island id, because "drains to a local low point with
     no path to the trunk" is a different fact and must not be dressed up as one.
  3  The trunk share per sub-network needs an APPORTIONMENT and it says so: the Main Pipe is
     ONE client input serving every sub-network, so "this sub-network's trunk length" is not
     a measurable quantity.  Every metre goes to the nearest join, sampled at the node-merge
     radius; it conserves length exactly and needs no flow direction on the trunk, which
     this stage does not have and must not invent.

One number is typed against the _BRAIN file rather than read from `asbuilt.py`: the
hierarchy ratio.  `asbuilt.m_tiers()` still returns **87.69 %** and sec 4 of the calibration
retracts it by name - *"wrong twice; use 73.2 % on 272 exits, banded 60-78 %"*.  Both figures
are published side by side with the retraction stated, because quietly swapping one for the
other is how a withdrawn number gets back into circulation.

WHAT THIS STAGE REFUSES TO CLAIM
--------------------------------
It does not improve the uphill share.  That was s2's job and the four measured facts stand:
the terrain decides one short reach in five; NAMA's own surveyed levels agree with their own
pipes 65 % of the time; 60 % of the corridor network is flatter than the minimum gradient a
DN200 may be laid at; and NAMA drain uphill on 34 % of their length.  A hierarchy re-labels
pipe.  It does not tilt ground.  The uphill share is re-measured here only because trimming
and pruning change the denominator, and the before/after is published side by side so the
difference cannot be mistaken for an improvement.

RUN
    python s3_hierarchy.py build        the whole stage
    python s3_hierarchy.py verify       re-read what was written and re-derive every headline
    python s3_hierarchy.py selftest     the rules proved on a synthetic graph with known answers
    python s3_hierarchy.py sweep        the calibration tables only, nothing published
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
from w12 import asbuilt as AB                               # noqa: E402

C = CR.DEFAULT

STAGE = "s3_hierarchy"
STAGE_VERSION = "W12-hierarchy-1.1-subnet-calibration"

# ================================================================== paths
W12 = os.path.dirname(_HERE)                                # .../W12
CLAUDE = os.path.dirname(W12)                               # .../Hydraulic/Claude
HYDRAULIC = os.path.dirname(CLAUDE)

ORIENT_GPKG = os.path.join(W12, "shp", "W12_orient.gpkg")
ROADS_GPKG = os.path.join(W12, "shp", "W12_roads.gpkg")
PLOT_LOADS = os.path.join(CLAUDE, "W10", "shp", "W10_plot_loads.gpkg")
PLOT_LOADS_LAYER = "plot_loads"
MAIN_PIPE = os.path.join(HYDRAULIC, "SHP", "Main Pipe", "Main Pipe.shp")

OUT_GPKG = os.path.join(W12, "shp", "W12_hier.gpkg")
RUN = os.path.join(W12, "run", "hier")
REPORT_MD = os.path.join(RUN, "HIERARCHY.md")
MANIFEST_JSON = os.path.join(RUN, "hier_manifest.json")

CRS_EPSG = 32640                     # project rule; every layer, no exceptions

# ================================================================== constants
# Guideline value with its page, a value MEASURED in this project, or a PROJECT choice that
# says so.  Nothing here is invented and nothing is quoted from memory.

# --- guideline ---------------------------------------------------------------------------
INLET_MIN_DEG = C.INLET_MIN_DEG      # 90 deg.  G203-p30, verbatim: "No inlet pipe at
#                                      manholes shall have an angle less than 90 deg to the
#                                      direction of flow."  Reported per tier here; enforced
#                                      by the chamber stage, which owns the geometry.
DN_TRUNK_MIN = C.DN_TRUNK_MIN        # 800 mm.  G203-p35 sec 5, first criterion.
TRUNK_MIN_RUN_M = C.TRUNK_MIN_RUN_M  # 1,000 m.  G203-p35 sec 5, second criterion, with the
#                                      "1,000 mm" typo recorded in criteria.CONFLICTS.
LATERAL_MAX_LEN_G203 = C.LATERAL_MAX_LEN   # 45 m.  G203-p22 Table 6, LATERAL SEWER row.
#                                      READ AND NOT ENFORCED - see the header.  It governs
#                                      the TERTIARY pipe, which stage 5b mints.
PCS_MAX_LEN = C.PCS_MAX_LEN          # 50 m.  G203-p18 under Table 4: "The length of the PCS
#                                      should not exceed 50 m in order to allow maintenance."
#                                      Used to test whether a plot stranded by a head setback
#                                      can still reach the junction chamber it was cut from.
MH_SNAP_M = C.MH_SNAP_M              # 3.0 m.  criteria: THE minimum chamber clearance and
#                                      the node-merge radius.  A head shorter than this after
#                                      its setback is not a pipe, it is two chambers touching.

# --- project rules -----------------------------------------------------------------------
FANOUT_OFFSET_M = C.FANOUT_OFFSET_M  # 10.0 m.  PROJECT rule (user 2026-08-18): "a branch
#                                      leaving a chamber that already has an outlet starts
#                                      10 m away, or at the next house connection."  BOTH
#                                      halves are implemented: the setback is the first gate
#                                      AT OR BEYOND 10 m, and bare 10 m only where the
#                                      corridor has no gate at all.
FINGER_MIN_M = 60.0                  # PROJECT (philosophy sec 4, "ours, on cost grounds; no
#                                      adoption standard requires it"): a dead-end reach under
#                                      ~60 m serving nothing is pruned or absorbed.  The
#                                      philosophy's own "~" is why this is a project number
#                                      and not a guideline one.
FRONTAGE_M = 40.0                    # PROJECT, INHERITED FROM s1_roads unchanged, where it
#                                      is derived from the drawing's own MEASURED 24-30 m
#                                      block street grid.  A plot further than this from the
#                                      corridor does not front it and cannot set its gate.
LATERAL_BUDGET_RUNS = 3              # PROJECT (philosophy sec 4): "At most 3 laterals ...
LATERAL_BUDGET_PATH_M = 750.0        # ... and 750 m of flow path before a main."  Swept.

# --- calibrated, and the sweep is published ----------------------------------------------
SUBMAIN_KM = 2.0                     # CALIBRATED, not chosen.  A run is a sub main when at
#                                      least this much network drains through it.  Set by
#                                      `sweep_submain` to land the sub-main share inside the
#                                      MEASURED band from the built network's own manhole IDs
#                                      (asbuilt tier_share_submain_pct, 10.85-17.15 %).  The
#                                      whole sweep is published so the reader can re-grade.
SUBMAIN_SWEEP = (0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5, 3.75, 4.0,
                 5.0, 6.0, 8.0, 12.0)

# --- measured, read at run time so they cannot go stale ----------------------------------
# Values in the comments are what they measured on 2026-09-03.
#   tier_share_trunk_pct           5.78 %   |  band 1.48 - 13.45
#   tier_share_submain_pct        16.61 %   |  band 10.85 - 17.15
#   tier_share_lateral_pct        77.61 %   |  band 71.57 - 81.37
#   lateral_zone_into_lateral_pct 87.69 %   |  min
#   joins_per_km_of_trunk          4.64 1/km
#   run_between_junctions_median_m 68.74 m  |  p90 218.64 m
#   junctions_per_km               4.83 1/km ; heads_per_km 5.09 1/km

TAU_FLAG = f"tau={C.TAU_PA:g} Pa ASSUMED (GAP-9)"

# --- THE PER-SUB-NETWORK CALIBRATION GATES -----------------------------------------------
# `_BRAIN/10_ASBUILT_CALIBRATION.md` sec 1, measured from NAMA's built 2006 network.  The
# tier-share bands are READ FROM `asbuilt.targets()` at run time rather than typed here, so
# they cannot go stale against the measurement - only the two the measurement does not carry
# are constants, and both name their line in that file.
#
# THE UNIT OF COMPARISON IS THE PACKAGE, and rule T2 of that file says a package IS one
# connected component with exactly one outlet - which is exactly what a sub-network is here.
# So the band that was measured BETWEEN NAMA'S PACKAGES is applied PER SUB-NETWORK, and the
# file is explicit about why the average is not enough: "a subnetwork with 0 % sub-main
# fails even if the average passes".
CAL_CHAIN_MED_MAX = 2       # 10_ASBUILT_CALIBRATION sec 1: built median 2 hops (excl 5A-1)
CAL_CHAIN_P90_MAX = 4       #   built p90 3; the band for W12 is <= 4
CAL_CHAIN_ABS_MAX = 5       #   built max 5, and it is an absolute
CAL_ZONE_PER_KM_MAX = 7.0   #   built 4.27 zones/km; "> 7/km means the MAIN TIER IS MISSING
#                             - the single best structural symptom"
CAL_HIER_PCT = (60.0, 78.0)  # lateral runs discharging into ANOTHER lateral.
#   THE MEASURED VALUE IS 73.2 % ON 272 EXITS, banded 60-78 %.  `asbuilt.py` still returns
#   87.69 % for `lateral_zone_into_lateral_pct`, and 10_ASBUILT_CALIBRATION sec 4 retracts
#   that figure by name: "wrong twice; use 73.2 % on 272 exits, banded 60-78 %".  So this
#   one band is typed here, against the _BRAIN file, and BOTH numbers are published side by
#   side with the retraction stated - quoting the live code's figure would re-publish a
#   number this project has already withdrawn.
CAL_HIER_MEASURED_PCT = 73.2
CAL_HIER_RETRACTED_PCT = 87.69

SUBNET_MIN_KM_FOR_BAND = AB.A_PKG_MIN_KM_GEOM   # 3.0 km. DERIVED, not chosen: it is the
#   floor `asbuilt._pkg_band` itself uses to decide a package is big enough to set a band.
#   Applying a band measured only over packages above it to a sub-network below it would be
#   comparing against evidence that never included anything that small.
TRUNK_SAMPLE_M = C.MH_SNAP_M    # 3.0 m. A NUMERICAL RESOLUTION, not a design value: the
#   step at which the Main Pipe is sampled to apportion its length between the sub-networks
#   that join it.  Set to the node-merge radius because that is the finest distance the
#   published topology can distinguish - a finer step would be measuring below the
#   resolution of the thing being measured.


def _log(msg: str) -> None:
    print(f"[{STAGE}] {msg}", flush=True)


def _md(df: pd.DataFrame, nd: int = 2, maxrows: Optional[int] = None) -> str:
    """A markdown table.  Written out rather than pulling in `tabulate`: one dependency for
    one pipe-separated string is not worth adding to a pipeline someone else has to run."""
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


def _write_table(df: pd.DataFrame, layer: str, gpkg: str = "") -> None:
    """An attribute-only table, written INTO the GeoPackage and registered in
    `gpkg_contents` so QGIS lists it.  Every measured table is published rather than
    printed: a number that lives only in a console log is a number nobody can check."""
    import sqlite3
    con = sqlite3.connect(gpkg or OUT_GPKG)
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
# 1.  GRAPH PRIMITIVES
#     Written here rather than pulled from networkx so the rules are readable and the stage
#     has no dependency a reviewer has to trust.  Each is proved in `selftest`.
# ==========================================================================================

def out_arc_of(n_nodes: int, U: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """For each node, the index of its single outgoing arc among `keep`, or -1.

    RAISES if any node has two.  That is the hard rule made unrepresentable rather than
    merely checked - a stage that can express the violation will eventually publish it."""
    out = np.full(n_nodes, -1, dtype=np.int64)
    for e in np.flatnonzero(keep):
        u = U[e]
        if out[u] != -1:
            raise AssertionError(
                f"node {u} has two outgoing arcs ({out[u]} and {e}) - the hard rule of "
                f"stage 3 is violated before it could be published")
        out[u] = e
    return out


def roots_of(order: np.ndarray, out_arc: np.ndarray, V: np.ndarray) -> np.ndarray:
    """The root each node drains to.

    One reverse pass over the topological order: downstream nodes are settled first, so a
    node simply inherits its outlet's answer.  The earlier hand-rolled path-compression
    version of this used `is` to test list membership and mis-rooted 1,212 nodes - it is
    replaced rather than patched, and the wrong number it produced is retracted in the
    report."""
    root = np.arange(len(out_arc), dtype=np.int64)
    for u in order[::-1]:
        e = out_arc[u]
        if e != -1:
            root[u] = root[V[e]]
    return root


def topo_order(out_arc: np.ndarray, V: np.ndarray, n: int) -> np.ndarray:
    """Nodes ordered so every node precedes its downstream node.  Kahn on in-degree."""
    indeg = np.zeros(n, dtype=np.int64)
    for u in range(n):
        e = out_arc[u]
        if e != -1:
            indeg[V[e]] += 1
    stack = list(np.flatnonzero(indeg == 0))
    order = []
    while stack:
        u = stack.pop()
        order.append(u)
        e = out_arc[u]
        if e != -1:
            v = V[e]
            indeg[v] -= 1
            if indeg[v] == 0:
                stack.append(v)
    if len(order) != n:
        raise AssertionError(f"topological order covers {len(order)} of {n} nodes - "
                             f"the graph is not a forest")
    return np.asarray(order, dtype=np.int64)


def accumulate(order: np.ndarray, out_arc: np.ndarray, V: np.ndarray,
               own: np.ndarray) -> np.ndarray:
    """Sum `own` over each node's whole upstream subtree, in one pass."""
    acc = own.astype(float).copy()
    for u in order:
        e = out_arc[u]
        if e != -1:
            acc[V[e]] += acc[u]
    return acc


def longest_path(order: np.ndarray, out_arc: np.ndarray, V: np.ndarray,
                 w: np.ndarray) -> np.ndarray:
    """Longest upstream distance to any head, per node.  The flow path philosophy sec 4
    budgets at 750 m before a main."""
    best = np.zeros(len(out_arc), dtype=float)
    for u in order:
        e = out_arc[u]
        if e != -1:
            v = V[e]
            cand = best[u] + w[e]
            if cand > best[v]:
                best[v] = cand
    return best


# ==========================================================================================
# 2.  THE STAGE
# ==========================================================================================

@dataclass
class Hier:
    """The whole stage.  Every step leaves its evidence on `self` so `verify` can re-derive
    the headline from the PUBLISHED layers and disagree with it if it wants to."""

    verbose: bool = True
    submain_km: float = SUBMAIN_KM
    budget_runs: int = LATERAL_BUDGET_RUNS
    budget_path_m: float = LATERAL_BUDGET_PATH_M

    # ---------------------------------------------------------------- load
    def load(self):
        import geopandas as gpd
        t0 = time.time()
        self.arcs = gpd.read_file(ORIENT_GPKG, layer="arcs")
        self.onodes = gpd.read_file(ORIENT_GPKG, layer="nodes")
        if self.arcs.crs is None or self.arcs.crs.to_epsg() != CRS_EPSG:
            raise AssertionError(f"arcs are not EPSG:{CRS_EPSG}")
        self.main_pipe = gpd.read_file(MAIN_PIPE).to_crs(epsg=CRS_EPSG)
        self.plots = gpd.read_file(PLOT_LOADS, layer=PLOT_LOADS_LAYER).to_crs(epsg=CRS_EPSG)
        if self.verbose:
            _log(f"loaded {len(self.arcs):,} arcs, {len(self.onodes):,} nodes, "
                 f"{len(self.plots):,} plots, {len(self.main_pipe)} Main Pipe parts "
                 f"({time.time() - t0:.1f} s)")

        # node index -------------------------------------------------------------------
        self.nid = list(self.onodes.NODE_ID)
        self.nix = {k: i for i, k in enumerate(self.nid)}
        self.NX = self.onodes.X.to_numpy(float)
        self.NY = self.onodes.Y.to_numpy(float)
        self.NZ = self.onodes.GRD_M.to_numpy(float)
        self.n_nodes0 = len(self.nid)

        self.U = self.arcs.US_NODE.map(self.nix).to_numpy(np.int64).copy()
        self.V = self.arcs.DS_NODE.map(self.nix).to_numpy(np.int64).copy()
        self.L = self.arcs.LEN_M.to_numpy(float).copy()
        self.ROLE = self.arcs.ROLE.to_numpy(object)

        # Attributes that are DIRECTIONAL are carried in their own arrays, because a flipped
        # island arc has to have them turned round with it.  Leaving FALL_M on a flipped arc
        # would publish a fall in the wrong sign, which is exactly the class of quiet error
        # this iteration exists to stop.
        self.fall = self.arcs.FALL_M.to_numpy(float).copy()
        self.inlet = self.arcs.INLET_DEG.to_numpy(float).copy()
        self.geom0 = list(self.arcs.geometry)

        self.km_in = float(self.L.sum() / 1000.0)
        self.q_in = float(self.arcs.Q_M3D.sum())
        return self

    # ---------------------------------------------------------------- 2a. islands
    def fix_islands(self):
        """184 arcs, 30.88 km, 154 nodes, no outfall, cycles among them.

        s2 pointed each island arc downhill INDEPENDENTLY, which is the honest thing to do
        for a corridor with no outfall to aim at, but it leaves a graph that is not a
        forest.  H15 says a piece that drains nowhere is never legal, so each island
        component is given a LOCAL outfall - its own lowest node - and an in-tree toward it.

        METHOD, STATED: root at the lowest node, in-tree by SHORTEST PATH ON LENGTH.  This
        is NOT s2's slope-weighted optimum branching and it does not pretend to be.  Over
        1.7 % of the network, with no outfall to reach and a pumping station or a satellite
        works waiting at the root either way, the extra machinery would buy nothing that
        could be measured.  Where the resulting direction disagrees with s2's downhill
        choice the arc is FLIPPED and counted (`island_flips`)."""
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components, dijkstra

        isl = np.flatnonzero(self.arcs.ROLE.to_numpy(object) == "island")
        self.island_arcs = isl
        if len(isl) == 0:
            self.island_report = pd.DataFrame()
            self.island_tree = np.zeros(0, dtype=np.int64)
            self.island_flip = np.zeros(len(self.L), dtype=bool)
            return self

        nodes = np.unique(np.concatenate([self.U[isl], self.V[isl]]))
        loc = {int(g): i for i, g in enumerate(nodes)}
        m = len(nodes)
        a = np.array([loc[int(x)] for x in self.U[isl]])
        b = np.array([loc[int(x)] for x in self.V[isl]])
        w = self.L[isl]

        adj = coo_matrix((np.concatenate([w, w]),
                          (np.concatenate([a, b]), np.concatenate([b, a]))),
                         shape=(m, m)).tocsr()
        ncomp, lab = connected_components(adj, directed=False)

        keep = np.zeros(len(isl), dtype=bool)
        flip = np.zeros(len(isl), dtype=bool)
        rows = []
        for c in range(ncomp):
            mem = np.flatnonzero(lab == c)
            z = self.NZ[nodes[mem]]
            root_local = int(mem[int(np.argmin(z))])
            dist, pred = dijkstra(adj, directed=False, indices=root_local,
                                  return_predecessors=True)
            n_flip = 0
            for v in mem:
                if v == root_local:
                    continue
                p = int(pred[v])
                if p < 0:
                    continue
                # the physical arc realising v -> p, shortest if parallel arcs exist
                cand = np.flatnonzero(((a == v) & (b == p)) | ((a == p) & (b == v)))
                if len(cand) == 0:
                    continue
                e = int(cand[int(np.argmin(w[cand]))])
                keep[e] = True
                if a[e] != v:                       # s2 pointed it the other way
                    flip[e] = True
                    n_flip += 1
            rows.append({
                "COMP": f"ISL{c:03d}",
                "N_NODES": int(len(mem)),
                "N_ARCS": int(((lab[a] == c)).sum()),
                "KM": float(w[lab[a] == c].sum() / 1000.0),
                "ROOT": self.nid[int(nodes[root_local])],
                "ROOT_Z": float(self.NZ[nodes[root_local]]),
                "RELIEF_M": float(z.max() - z.min()),
                "IN_TREE_ARCS": int(keep[lab[a] == c].sum()),
                "FLIPPED": int(n_flip),
                "OUTFALL_KIND": "local low point - NO path to the Main Pipe; a station or a "
                                "satellite works decides this, not this stage",
            })

        self.island_report = pd.DataFrame(rows)
        self.island_tree_mask = np.zeros(len(self.L), dtype=bool)
        self.island_tree_mask[isl[keep]] = True
        self.island_flip = np.zeros(len(self.L), dtype=bool)
        self.island_flip[isl[flip]] = True
        self.island_roots = set(self.island_report.ROOT)

        if self.verbose:
            _log(f"islands: {ncomp} components, {len(isl)} arcs "
                 f"({self.L[isl].sum()/1000:.2f} km) -> {int(keep.sum())} in-tree arcs, "
                 f"{int(flip.sum())} flipped, {int((~keep).sum())} become heads")
        return self

    # ---------------------------------------------------------------- 2b. one pipe leaves
    def one_pipe_leaves(self):
        """The hard rule.

        The survivor at every node is s2's own tree arc.  This stage does NOT re-choose it:
        s2 solved the branching with a slope-aware weight, swept four parameters and proved
        its solver against networkx.  Re-deciding here would be a second, worse answer to a
        question already answered.  Islands get the survivor built in `fix_islands`.

        Everything else is a HEAD, and a head does not start at the junction."""
        tree = (self.arcs.ROLE.to_numpy(object) == "tree") | self.island_tree_mask
        self.is_tree = tree

        # Flip the island arcs that had to turn round - endpoints, geometry, ground fall and
        # inlet angle together.  An inlet angle measured against a direction that no longer
        # exists is not a number, so it is set to nan and counted, never carried forward.
        if self.island_flip.any():
            from shapely.ops import substring          # noqa: F401  (kept: same module)
            fl = np.flatnonzero(self.island_flip)
            self.U[fl], self.V[fl] = self.V[fl].copy(), self.U[fl].copy()
            self.fall[fl] = -self.fall[fl]
            self.inlet[fl] = np.nan
            for e in fl:
                self.geom0[e] = self.geom0[e].reverse()

        # the exception register.  It must come out empty.
        out_seen: Dict[int, int] = {}
        exc = []
        for e in np.flatnonzero(tree):
            u = int(self.U[e])
            if u in out_seen:
                exc.append({"NODE": self.nid[u], "ARC_A": self.arcs.CID.iloc[out_seen[u]],
                            "ARC_B": self.arcs.CID.iloc[e],
                            "WHY": "two survivors at one node"})
            out_seen[u] = e
        self.exceptions_tree = pd.DataFrame(exc)

        self.head_cand = np.flatnonzero(~tree)
        # a node still carrying a pipe after the losers are detached needs the 10 m clearance
        node_has_pipe = np.zeros(self.n_nodes0, dtype=bool)
        node_has_pipe[self.U[tree]] = True
        node_has_pipe[self.V[tree]] = True
        self.node_has_pipe = node_has_pipe

        if self.verbose:
            _log(f"one pipe leaves: {int(tree.sum()):,} survivors, "
                 f"{len(self.head_cand):,} heads to set back "
                 f"({self.L[self.head_cand].sum()/1000:.1f} km)")
        return self

    # ---------------------------------------------------------------- 2c. gates
    def gates(self):
        """THE FIRST HOUSE GATE.

        For every plot: its centroid, the NEAREST corridor arc, and the along-distance of
        the foot of the perpendicular from the start of that arc.  A plot further than
        FRONTAGE_M does not front the corridor and sets no gate.

        The nearest-arc rule is s1_roads' own allocation rule, re-run here because s2's
        ridge pre-split cut 151 corridors and the along-distances have to be measured on the
        arcs that actually exist.  The reproduction of s1's total is published
        (`gate_load_check`) rather than assumed: the two allocations must agree to within
        the ridge splits or one of them is wrong."""
        from shapely import STRtree
        from shapely.ops import nearest_points

        t0 = time.time()
        geoms = self.geom0                     # already flipped for the island arcs
        tree = STRtree(geoms)
        cent = self.plots.geometry.centroid
        pts = np.array([[p.x, p.y] for p in cent])

        idx, dist = tree.query_nearest(list(cent), return_distance=True, all_matches=False)
        # shapely returns (2, n) for query_nearest on a sequence
        if idx.ndim == 2:
            nearest = idx[1]
        else:
            nearest = idx
        dist = np.asarray(dist, dtype=float).ravel()

        along = np.full(len(cent), np.nan)
        for k in range(len(cent)):
            g = geoms[int(nearest[k])]
            along[k] = g.project(cent.iloc[k])

        q = self.plots.Q_AVG_M3D.to_numpy(float)
        fronts = dist <= FRONTAGE_M

        self.plot_arc = nearest.astype(np.int64)
        self.plot_along = along
        self.plot_dist = dist
        self.plot_q = q
        self.plot_fronts = fronts

        # gates per arc, sorted along the line
        order = np.lexsort((along, nearest))
        self.gate_arc = nearest[order][fronts[order]]
        self.gate_along = along[order][fronts[order]]
        self.gate_q = q[order][fronts[order]]
        # first index of each arc in the sorted gate list
        self.gate_start: Dict[int, Tuple[int, int]] = {}
        if len(self.gate_arc):
            bounds = np.flatnonzero(np.diff(self.gate_arc)) + 1
            lo = np.concatenate([[0], bounds])
            hi = np.concatenate([bounds, [len(self.gate_arc)]])
            for i, j in zip(lo, hi):
                self.gate_start[int(self.gate_arc[i])] = (int(i), int(j))

        own_q = np.zeros(len(self.arcs))
        own_n = np.zeros(len(self.arcs))
        np.add.at(own_q, nearest.astype(np.int64), q)
        np.add.at(own_n, nearest.astype(np.int64), 1.0)
        self.own_q = own_q
        self.own_n = own_n

        self.gate_load_check = pd.DataFrame([
            {"ITEM": "plots", "MINE": int(len(self.plots)), "s1_s2": float("nan")},
            {"ITEM": "load m3/d allocated by nearest arc", "MINE": float(own_q.sum()),
             "s1_s2": float(self.arcs.Q_M3D.sum())},
            {"ITEM": "plots fronting a corridor within 40 m", "MINE": int(fronts.sum()),
             "s1_s2": float("nan")},
            {"ITEM": "load on a fronting plot", "MINE": float(q[fronts].sum()),
             "s1_s2": float("nan")},
        ])
        if self.verbose:
            _log(f"gates: {int(fronts.sum()):,} of {len(self.plots):,} plots front a "
                 f"corridor within {FRONTAGE_M:g} m; my allocation totals "
                 f"{own_q.sum():,.0f} m3/d against s2's {self.arcs.Q_M3D.sum():,.0f} "
                 f"({time.time()-t0:.1f} s)")
        return self

    def _first_gate(self, e: int, floor_m: float) -> Tuple[float, float, int]:
        """(gate distance, load stranded before it, plots stranded).  nan if no gate."""
        rng = self.gate_start.get(int(e))
        if rng is None:
            return float("nan"), 0.0, 0
        i, j = rng
        d = self.gate_along[i:j]
        qq = self.gate_q[i:j]
        ok = d >= floor_m
        if not ok.any():
            return float("nan"), float(qq.sum()), int(len(qq))
        k = int(np.argmax(ok))
        return float(d[k]), float(qq[:k].sum()), int(k)

    # ---------------------------------------------------------------- 2d. heads
    def set_heads(self):
        """Set every head back to its first gate, and prune what serves nothing.

        Two kinds of head, and they get different treatment because the physics differs:

          DETACHED  it lost the contest at a junction that keeps a chamber.  The 10 m
                    clearance applies: the setback is the FIRST GATE AT OR BEYOND 10 m, or
                    bare 10 m where the corridor has no gate at all.
          ROAD END  its upstream node ends up with nothing on it.  There is no chamber to
                    clear, so the setback is simply the first gate - which is the whole
                    content of "never at the end of a road line".

        A head that serves nothing and is shorter than FINGER_MIN_M is PRUNED.  Pruning can
        expose a new head, so it iterates; the passes are counted and published.  A head
        that serves nothing and is LONGER than 60 m survives the rule as written, and its
        length is reported as a finding rather than quietly cleaned up."""
        from shapely.ops import substring

        n_arc = len(self.arcs)
        keep = np.ones(n_arc, dtype=bool)
        keep[self.head_cand] = True                    # heads are kept unless pruned
        start_m = np.zeros(n_arc, dtype=float)
        head_by = np.array([""] * n_arc, dtype=object)
        is_head = np.zeros(n_arc, dtype=bool)
        strand_q = np.zeros(n_arc, dtype=float)
        strand_n = np.zeros(n_arc, dtype=np.int64)

        prune_rows = []
        passes = []

        for it in range(1, 9):
            # in-degree over the arcs still kept
            indeg = np.zeros(self.n_nodes0, dtype=np.int64)
            np.add.at(indeg, self.V[keep], 1)
            detached = np.zeros(n_arc, dtype=bool)
            detached[self.head_cand] = True
            detached &= keep
            roadend = keep & (~detached) & (indeg[self.U] == 0)
            heads = detached | roadend
            n_pruned = 0
            for e in np.flatnonzero(heads):
                floor = FANOUT_OFFSET_M if detached[e] else 0.0
                g, sq, sn = self._first_gate(int(e), floor)
                Lm = self.L[e]
                if not np.isfinite(g):
                    # no gate at or beyond the floor
                    if self.own_n[e] == 0 and Lm < FINGER_MIN_M:
                        keep[e] = False
                        n_pruned += 1
                        prune_rows.append({"CID": self.arcs.CID.iloc[e], "LEN_M": float(Lm),
                                           "Q_M3D": 0.0, "N_PLOT": 0, "PASS": it,
                                           "WHY": f"finger: serves nothing, under "
                                                  f"{FINGER_MIN_M:g} m"})
                        continue
                    if floor > 0.0 and Lm - floor < MH_SNAP_M:
                        keep[e] = False
                        n_pruned += 1
                        prune_rows.append({"CID": self.arcs.CID.iloc[e], "LEN_M": float(Lm),
                                           "Q_M3D": float(self.own_q[e]),
                                           "N_PLOT": int(self.own_n[e]), "PASS": it,
                                           "WHY": f"shorter than the {FANOUT_OFFSET_M:g} m "
                                                  f"clearance plus the {MH_SNAP_M:g} m "
                                                  f"minimum chamber clearance"})
                        continue
                    start_m[e] = floor
                    head_by[e] = "clearance" if floor > 0 else "road_end_no_gate"
                    strand_q[e] = sq
                    strand_n[e] = sn
                else:
                    if floor == 0.0 and g < MH_SNAP_M:
                        # A ROAD-END head whose first gate is within the chamber-merge
                        # radius.  MH_SNAP_M is the radius at which two chambers ARE one
                        # structure, so setting back by less than it does not create a new
                        # chamber - it moves the same one.  Keep the arc whole.  Without
                        # this the stage published 106 "exceptions" that were an artefact of
                        # its own check, not a defect in the layout.
                        start_m[e] = 0.0
                        head_by[e] = "gate_at_corridor_end"
                        strand_q[e] = 0.0
                        strand_n[e] = 0
                        is_head[e] = True
                        continue
                    if Lm - g < MH_SNAP_M:
                        keep[e] = False
                        n_pruned += 1
                        prune_rows.append({"CID": self.arcs.CID.iloc[e], "LEN_M": float(Lm),
                                           "Q_M3D": float(self.own_q[e]),
                                           "N_PLOT": int(self.own_n[e]), "PASS": it,
                                           "WHY": "the gate leaves less than the minimum "
                                                  "chamber clearance of pipe"})
                        continue
                    start_m[e] = g
                    head_by[e] = "gate_clear" if floor > 0 else "gate"
                    strand_q[e] = sq
                    strand_n[e] = sn
                is_head[e] = True
            passes.append({"PASS": it, "HEADS": int(heads.sum()), "PRUNED": int(n_pruned),
                           "KEPT_KM": float(self.L[keep].sum() / 1000.0)})
            if n_pruned == 0:
                break

        self.keep = keep
        self.start_m = start_m
        self.head_by = head_by
        self.is_head = is_head & keep
        self.strand_q = strand_q
        self.strand_n = strand_n
        self.prune = pd.DataFrame(prune_rows) if prune_rows else pd.DataFrame(
            columns=["CID", "LEN_M", "Q_M3D", "N_PLOT", "PASS", "WHY"])
        self.head_passes = pd.DataFrame(passes)

        # trim the geometry.  A head no longer touches the junction it was cut from - which
        # is the whole point, and it is visible in the drawing.
        geom = self.geom0
        newgeom = list(geom)
        for e in np.flatnonzero(self.is_head & (start_m > 0)):
            newgeom[e] = substring(geom[e], float(start_m[e]), float(self.L[e]))
        self.geom_out = newgeom
        self.len_out = np.array([g.length for g in newgeom])
        self.len_out[~self.is_head] = self.L[~self.is_head]

        if self.verbose:
            hb = pd.Series(head_by[self.is_head]).value_counts().to_dict()
            _log(f"heads: {int(self.is_head.sum()):,} set back, {hb}; "
                 f"{len(self.prune):,} pruned "
                 f"({self.prune.LEN_M.sum()/1000 if len(self.prune) else 0:.2f} km) over "
                 f"{len(self.head_passes)} passes")
        return self

    # ---------------------------------------------------------------- 2e. mint head nodes
    def mint_nodes(self):
        """A head that has been set back starts at a NEW chamber, and it gets a NEW node id.

        Re-using the junction's id would leave the layer claiming a connection that the
        geometry no longer has - which is exactly the class of defect H16 exists to stop
        ("topology is written down, never inferred from geometry").  The new node carries
        MADE_BY so the chamber stage knows why it is there."""
        self.node_rows = []
        Uo = self.U.copy()
        nid = list(self.nid)
        NX, NY, NZ = list(self.NX), list(self.NY), list(self.NZ)
        made_by = ["s2_orient"] * len(nid)
        parent = [""] * len(nid)

        k = 0
        for e in np.flatnonzero(self.is_head & (self.start_m > 0)):
            g = self.geom_out[e]
            x, y = g.coords[0]
            k += 1
            new = f"H{k:05d}"
            nid.append(new)
            NX.append(float(x))
            NY.append(float(y))
            NZ.append(float("nan"))            # ground comes from the terrain in stage 6;
            made_by.append("s3_head_setback")  # inventing one here would be a fabricated number
            parent.append(self.nid[int(self.U[e])])
            Uo[e] = len(nid) - 1

        # SAMPLE the ground at the new chambers, do not leave it blank and do not guess it.
        # A set-back head starts partway along its corridor, so BOTH its ground level and
        # its ground fall change - and carrying s2's untrimmed FALL_M onto a trimmed arc
        # would publish a fall the arc no longer has.  Same 5 m working grid as s2.
        self.terrain_ok = False
        if len(nid) > self.n_nodes0:
            try:
                from w12 import terrain as T
                tf = T.TerrainFlow.load("R5")
                xs = np.asarray(NX[self.n_nodes0:], dtype=float)
                ys = np.asarray(NY[self.n_nodes0:], dtype=float)
                z = np.asarray(tf.elevation(xs, ys), dtype=float).ravel()
                for i, zz in enumerate(z):
                    NZ[self.n_nodes0 + i] = float(zz)
                self.terrain_ok = True
            except Exception as ex:                             # noqa: BLE001
                _log(f"terrain sampling for the head chambers FAILED ({type(ex).__name__}: "
                     f"{ex}) - GRD_M is left blank on them and every ground fall on a "
                     f"set-back head is s2's UNTRIMMED value. Say so; do not fill it in.")

        self.Uo = Uo
        self.nid_out = nid
        self.NX_out = np.asarray(NX)
        self.NY_out = np.asarray(NY)
        self.NZ_out = np.asarray(NZ)
        self.made_by = made_by
        self.node_parent = parent
        self.n_nodes = len(nid)

        # the trimmed arc's own ground fall, from the levels it actually runs between
        self.fall_pub = self.fall.copy()
        self.fall_resampled = 0
        if self.terrain_ok:
            for e in np.flatnonzero(self.is_head & (self.start_m > 0)):
                zu = float(NZ[Uo[e]])
                zd = float(NZ[self.V[e]])
                if np.isfinite(zu) and np.isfinite(zd):
                    self.fall_pub[e] = zu - zd
                    self.fall_resampled += 1

        if self.verbose:
            _log(f"minted {k:,} head chambers; node count {self.n_nodes0:,} -> "
                 f"{self.n_nodes:,}; ground sampled {self.terrain_ok}, "
                 f"{self.fall_resampled:,} falls recomputed on the trimmed geometry")
        return self

    # ---------------------------------------------------------------- 2f. the forest
    def build_forest(self):
        """Prove it is a forest, then walk it.  `out_arc_of` RAISES on a second outlet, so
        by the time anything is measured the hard rule has already been enforced twice."""
        keep = self.keep
        self.out_arc = out_arc_of(self.n_nodes, self.Uo, keep)
        self.order = topo_order(self.out_arc, self.V, self.n_nodes)

        # The roots: outfall nodes (on the Main Pipe) and island low points.
        #
        # ONLY NODES THAT STILL CARRY A PIPE ARE ROOTS.  Pruning a finger leaves its old
        # upstream node with no arcs at all, and such a node is not a component draining
        # nowhere - it is a node that no longer exists in the design.  Counting it as an
        # orphan is how the first run of this stage reported 1,212 components draining
        # nowhere when the true number is what the table below prints.
        used = np.zeros(self.n_nodes, dtype=bool)
        used[self.Uo[keep]] = True
        used[self.V[keep]] = True
        self.used = used

        root_kind = np.array([""] * self.n_nodes, dtype=object)
        okind = dict(zip(self.onodes.NODE_ID, self.onodes.KIND))
        for i in np.flatnonzero(used & (self.out_arc == -1)):
            nm = self.nid_out[i]
            if okind.get(nm) == "outfall":
                root_kind[i] = "main_pipe"
            elif nm in getattr(self, "island_roots", set()):
                root_kind[i] = "island_low"
            else:
                root_kind[i] = "orphan"
        self.root_kind = root_kind

        self.rootof = roots_of(self.order, self.out_arc, self.V)
        rootof = self.rootof

        # H15: one outfall per component, checked on what is about to be published
        comp = pd.Series(rootof[self.Uo[keep]])
        self.components = int(comp.nunique())
        self.orphan_roots = int((root_kind == "orphan").sum())

        # accumulation
        ownq = np.zeros(self.n_nodes)
        np.add.at(ownq, self.Uo[keep], self.arcs.Q_M3D.to_numpy(float)[keep])
        lenw = np.where(keep, self.len_out, 0.0)
        ownlen = np.zeros(self.n_nodes)
        np.add.at(ownlen, self.Uo[keep], lenw[keep])

        self.acc_q = accumulate(self.order, self.out_arc, self.V, ownq)
        self.acc_len = accumulate(self.order, self.out_arc, self.V, ownlen)
        self.path_up = longest_path(self.order, self.out_arc, self.V,
                                    np.where(keep, self.len_out, 0.0))

        # per-arc: what drains THROUGH this arc = accumulation at its upstream node
        self.arc_sub_km = np.where(keep, self.acc_len[self.Uo] / 1000.0, np.nan)
        self.arc_q_up = np.where(keep, self.acc_q[self.Uo], np.nan)
        self.arc_path_up = np.where(keep, self.path_up[self.Uo] + self.len_out, np.nan)

        if self.verbose:
            _log(f"forest: {self.components} components, "
                 f"{int((root_kind=='main_pipe').sum())} on the Main Pipe, "
                 f"{int((root_kind=='island_low').sum())} island low points, "
                 f"{self.orphan_roots} orphans")
        return self

    # ---------------------------------------------------------------- 2g. runs
    def build_runs(self):
        """A RUN is a maximal chain of arcs through chambers with exactly one pipe in and
        one pipe out - `asbuilt.m_runs()`'s definition, so the median is comparable with the
        built network's 68.74 m.

        Philosophy sec 4: "Chamber spacing (H12) and run length (P3) are different rules.
        A 500 m run has five chambers at 100 m centres.  Report run length as a MAXIMUM,
        never a median."  Both are reported; the maximum is the one that governs."""
        keep = self.keep
        indeg = np.zeros(self.n_nodes, dtype=np.int64)
        np.add.at(indeg, self.V[keep], 1)
        through = (indeg == 1) & (self.out_arc != -1)

        run_id = np.full(len(self.arcs), -1, dtype=np.int64)
        r = 0
        for e in np.flatnonzero(keep):
            if run_id[e] != -1:
                continue
            if through[self.Uo[e]]:
                continue                       # not a run start; it is picked up from above
            cur, rid = e, r
            r += 1
            while cur != -1 and run_id[cur] == -1:
                run_id[cur] = rid
                v = self.V[cur]
                cur = self.out_arc[v] if through[v] else -1
        # anything left is inside a cycle-free chain whose start was already consumed
        for e in np.flatnonzero(keep & (run_id == -1)):
            run_id[e] = r
            r += 1

        self.run_id = run_id
        self.n_runs = r
        rl = np.zeros(r)
        np.add.at(rl, run_id[keep], self.len_out[keep])
        self.run_len = rl

        # the run graph: run -> the run its outlet arc flows into
        last_arc = np.full(r, -1, dtype=np.int64)
        for e in np.flatnonzero(keep):
            v = self.V[e]
            nxt = self.out_arc[v]
            if nxt == -1 or run_id[nxt] != run_id[e]:
                last_arc[run_id[e]] = e
        self.run_last = last_arc
        run_next = np.full(r, -1, dtype=np.int64)
        for rr in range(r):
            e = last_arc[rr]
            if e == -1:
                continue
            nxt = self.out_arc[self.V[e]]
            run_next[rr] = run_id[nxt] if nxt != -1 else -1
        self.run_next = run_next
        self.run_up: Dict[int, List[int]] = {}
        for rr in range(r):
            nx = run_next[rr]
            if nx != -1:
                self.run_up.setdefault(int(nx), []).append(rr)

        # run-level accumulation, on the run tree
        rorder = topo_order(run_next, np.arange(r), r) if r else np.zeros(0, dtype=np.int64)
        self.run_order = rorder
        self.run_sub_km = accumulate(rorder, run_next, np.arange(r), rl) / 1000.0
        self.run_depth = np.ones(r, dtype=float)
        for rr in rorder:
            nx = run_next[rr]
            if nx != -1:
                self.run_depth[nx] = max(self.run_depth[nx], self.run_depth[rr] + 1)
        self.run_path_m = np.zeros(r)
        for rr in rorder:
            nx = run_next[rr]
            if nx != -1:
                self.run_path_m[nx] = max(self.run_path_m[nx], self.run_path_m[rr] + rl[rr])

        if self.verbose:
            _log(f"runs: {r:,}; median {np.median(rl):.1f} m, p90 "
                 f"{np.percentile(rl,90):.1f} m, MAX {rl.max():,.0f} m "
                 f"(built median {AB.AsBuilt().m_runs()['run_between_junctions_median_m']:.1f} m)")
        return self

    # ---------------------------------------------------------------- 2h. tiers
    def tiers(self, submain_km: Optional[float] = None,
              budget_runs: Optional[int] = None,
              budget_path_m: Optional[float] = None) -> np.ndarray:
        """Tier per RUN, then written onto the arcs.

        sub main   run_sub_km >= submain_km, OR the run is the one that DISCHARGES the
                   component - the outlet governs
        main       run_depth > budget_runs  OR  run_path_m > budget_path_m
        lateral    everything else

        All three quantities are non-decreasing downstream, so the tier is monotone by
        construction and a lateral can never receive a main.  Verified anyway.

        WHY THE OUTLET CLAUSE IS EXPLICIT, AND WHY IT WAS A BUG.  This docstring has always
        said "every catchment gets one by construction, because the run at the outfall
        always drains the whole catchment" - and the code did not do it.  `run_sub_km >= sk`
        alone gives a sub-network SMALLER than SUBMAIN_KM no sub main at all, and the
        as-built calibration is explicit that "a subnetwork with 0 % sub-main FAILS even if
        the average passes" (10_ASBUILT_CALIBRATION.md sec 1).  The outfall rule multiplies
        the number of small sub-networks, so what was a rare case becomes the common one.
        The outlet run has the LARGEST run_sub_km in its component, so naming it cannot
        break the monotonicity a tier depends on."""
        sk = self.submain_km if submain_km is None else submain_km
        br = self.budget_runs if budget_runs is None else budget_runs
        bp = self.budget_path_m if budget_path_m is None else budget_path_m
        t = np.array(["lateral"] * self.n_runs, dtype=object)
        t[(self.run_depth > br) | (self.run_path_m > bp)] = "main"
        t[self.run_sub_km >= sk] = "sub main"
        t[self.run_next == -1] = "sub main"          # the outlet governs
        return t

    # ---------------------------------------------------------------- 2h(i). subnet labels
    def label_subnets(self):
        """SUBNET on EVERY published reach, taken from the component it drains through.

        s2 wrote SUBNET on the arcs it put in its tree and left it blank on the heads, the
        islands and everything the tree did not use - about a fifth of the published length.
        A blank there is not a missing label, it is a reach nobody can attribute: the
        outfall rule's whole point is that a sub-network is a catchment with ONE outlet, and
        the per-sub-network calibration (tier shares, chain depth, zone density) cannot be
        measured on a layer where a fifth of the pipe belongs to nothing.

        The authority is this stage's own forest, not s2's arc column: `rootof` says which
        root each arc drains to, and the root's own name carries the label.  An island keeps
        its island id, because "drains to a local low point with no path to the trunk" is a
        different fact from "drains to the trunk at S042" and must not be dressed up as one.
        """
        o_sub = dict(zip(self.onodes.NODE_ID, self.onodes.SUBNET.astype(str)))
        isl = {}
        if len(getattr(self, "island_report", [])):
            isl = dict(zip(self.island_report.ROOT, self.island_report.COMP))
        lab = np.array([""] * self.n_nodes, dtype=object)
        for i in np.flatnonzero(self.used):
            nm = self.nid_out[self.rootof[i]]
            s = o_sub.get(nm, "")
            if not s or s == "nan":
                s = isl.get(nm, "")
            if not s:
                s = f"ORPH-{nm}"          # a component draining nowhere: named, not blanked
            lab[i] = s
        self.node_subnet = lab
        arc = np.array([""] * len(self.arcs), dtype=object)
        arc[self.keep] = lab[self.Uo[self.keep]]
        self.arc_subnet = arc
        blank = int((arc[self.keep] == "").sum())
        if blank:
            raise AssertionError(
                f"{blank} kept reach(es) have no sub-network label. Every reach drains to "
                f"exactly one root (H15) and the root names the sub-network, so a blank "
                f"here means the forest is not what build_forest published.")
        if self.verbose:
            n_orph = int(sum(1 for s in set(arc[self.keep]) if s.startswith("ORPH-")))
            _log(f"sub-networks: {len(set(arc[self.keep])):,} labels on "
                 f"{int(self.keep.sum()):,} reaches "
                 f"(s2 left {int((self.arcs.SUBNET.astype(str).isin(['', 'nan'])).sum()):,} "
                 f"arcs blank); {n_orph} component(s) drain nowhere and are named ORPH-*")
        return self

    def _submain_routes(self, tier: np.ndarray) -> int:
        """A sub-main ROUTE is a maximal chain of sub-main runs.

        Philosophy sec 4's second measure - "one per 4-10 km of network" - counts routes,
        not runs.  Counting runs instead would make any threshold look right, because a run
        is a fragment of a route and there are always more of them."""
        n = 0
        for rr in range(self.n_runs):
            if tier[rr] != "sub main":
                continue
            ups = self.run_up.get(rr, ())
            if not any(tier[u] == "sub main" for u in ups):
                n += 1
        return n

    def apply_tiers(self):
        self.run_tier = self.tiers()
        arc_tier = np.array([""] * len(self.arcs), dtype=object)
        arc_tier[self.keep] = self.run_tier[self.run_id[self.keep]]
        self.arc_tier = arc_tier

        rank = {"lateral": 0, "main": 1, "sub main": 2, "trunk main": 3}
        inv = 0
        for rr in range(self.n_runs):
            nx = self.run_next[rr]
            if nx != -1 and rank[self.run_tier[nx]] < rank[self.run_tier[rr]]:
                inv += 1
        self.tier_inversions = inv
        if self.verbose:
            km = pd.Series(self.len_out[self.keep] / 1000.0).groupby(
                pd.Series(arc_tier[self.keep])).sum()
            _log(f"tiers: " + ", ".join(f"{k} {v:,.1f} km" for k, v in km.items())
                 + f"; inversions {inv}")
        return self

    # ---------------------------------------------------------------- 2h(ii). calibration
    def _apportion_trunk(self) -> Dict[str, float]:
        """The Main Pipe's length, shared out between the sub-networks that join it.

        A PROJECT APPORTIONMENT, and it says so: the trunk is ONE client input serving every
        sub-network, so "this sub-network's trunk length" is not a measurable quantity the
        way its own pipe is.  Without some apportionment the per-sub-network trunk share is
        not computable at all, and the as-built band for it would have to be dropped.

        The rule is nearest-join: every metre of trunk belongs to the sub-network whose join
        is closest to it.  It is well defined, it sums EXACTLY to the trunk length, and it
        needs no flow direction on the Main Pipe - which this stage does not have and must
        not invent.  Sampled at TRUNK_SAMPLE_M, the node-merge radius.
        """
        from scipy.spatial import cKDTree
        idx = np.flatnonzero(self.root_kind == "main_pipe")
        if idx.size == 0:
            return {}
        tree = cKDTree(np.c_[self.NX_out[idx], self.NY_out[idx]])
        labels = [str(self.node_subnet[i]) for i in idx]
        out: Dict[str, float] = {}
        for part in self.main_pipe.geometry:
            geoms = part.geoms if part.geom_type == "MultiLineString" else [part]
            for gm in geoms:
                if gm.length <= 0:
                    continue
                n = max(1, int(math.ceil(gm.length / TRUNK_SAMPLE_M)))
                seg = gm.length / n
                pts = np.array([[p.x, p.y] for p in
                                (gm.interpolate((k + 0.5) * seg) for k in range(n))])
                _d, j = tree.query(pts)
                for jj in np.atleast_1d(j):
                    out[labels[int(jj)]] = out.get(labels[int(jj)], 0.0) + seg
        return {k: v / 1000.0 for k, v in out.items()}

    def subnet_calibration(self):
        """THE AS-BUILT GATES, MEASURED PER SUB-NETWORK - not as a network average.

        `10_ASBUILT_CALIBRATION.md` sec 1 gives five structural gates and rule T2 says a
        package is one connected component with exactly one outlet, which is what a
        sub-network is.  So the bands measured BETWEEN NAMA'S PACKAGES are applied
        SUB-NETWORK BY SUB-NETWORK, and the file is explicit about why an average will not
        do: "a subnetwork with 0 % sub-main fails even if the average passes".

            tier length share      trunk and sub main, against the measured package bands
            chain depth            lateral -> main, median <= 2, p90 <= 4, absolute 5
            lateral-zone density   > 7 zones/km means THE MAIN TIER IS MISSING
            hierarchy ratio        lateral runs into another lateral, 60-78 %

        WHAT A ZONE IS HERE, STATED.  NAMA's zone is a DRAFTING zone (5A-1-A49); ours is the
        set of lateral runs draining through one lateral run that discharges into a
        non-lateral.  The definitions are not the same object, so the density is compared as
        a STRUCTURAL SYMPTOM - both count lateral clusters per km - and never quoted as a
        like-for-like match.  The one like-for-like row is a lateral reaching the trunk with
        nothing in between, and it is in `lateral_into`.

        Nothing here changes the design.  It measures it and names what fails, with the
        size beside it, which is the concept-stage rule.
        """
        keep = self.keep
        lab = self.arc_subnet
        L = self.len_out
        tier = self.arc_tier
        tgt = AB.AsBuilt().targets()
        band_t = (tgt["tier_share_trunk_pct"].lo, tgt["tier_share_trunk_pct"].hi)
        band_s = (tgt["tier_share_submain_pct"].lo, tgt["tier_share_submain_pct"].hi)
        self.cal_band_trunk, self.cal_band_submain = band_t, band_s
        trunk_km = self._apportion_trunk()

        # --- chain depth: hops from a lateral run to the first non-lateral ---------------
        tr_run = self.run_tier
        hops = np.zeros(self.n_runs, dtype=np.int64)
        for rr in self.run_order[::-1]:            # downstream first, so `next` is settled
            if tr_run[rr] != "lateral":
                hops[rr] = 0
                continue
            nx = self.run_next[rr]
            hops[rr] = 1 + (int(hops[nx]) if nx != -1 and tr_run[nx] == "lateral" else 0)
        self.run_hops = hops

        run_lab = np.array([""] * self.n_runs, dtype=object)
        run_lab[self.run_id[keep]] = lab[keep]
        self.run_subnet = run_lab

        # --- one row per sub-network -----------------------------------------------------
        A = pd.DataFrame(dict(SUB=lab[keep], L=L[keep], TIER=tier[keep]))
        km = A.groupby("SUB").L.sum() / 1000.0
        by_tier = (A.pivot_table(index="SUB", columns="TIER", values="L",
                                 aggfunc="sum", fill_value=0.0) / 1000.0)
        for t in ("lateral", "main", "sub main"):
            if t not in by_tier.columns:
                by_tier[t] = 0.0

        # WHAT EACH SUB-NETWORK ENDS AT.  An island or an orphan has no join onto the Main
        # Pipe, so `_apportion_trunk` gives it none and its trunk share is 0 - which the
        # band then reads as "below", a FAILURE against a gate it could not possibly meet.
        # A sub-network that does not reach the trunk is a different fact and is named as
        # one; `10_ASBUILT_CALIBRATION` rule T1 already settles that such a terminal is
        # legal where it ends at a designed station.
        # `root_kind` is "" on every node that is not a root, which is the same indexing
        # `_apportion_trunk` uses, so no extra state is needed to read it.
        root_of_sub: Dict[str, str] = {}
        for i, k in enumerate(np.asarray(self.root_kind, dtype=object)):
            if k:
                root_of_sub[str(self.node_subnet[i])] = str(k)

        rows = []
        for s in sorted(km.index):
            own = float(km[s])
            tk = float(trunk_km.get(s, 0.0))
            tot = own + tk
            sm = float(by_tier.loc[s, "sub main"])
            lat = float(by_tier.loc[s, "lateral"]) + float(by_tier.loc[s, "main"])
            rr = np.flatnonzero(run_lab == s)
            lat_runs = [int(r) for r in rr if tr_run[r] == "lateral"]
            h = np.array([hops[r] for r in lat_runs], dtype=float)
            into_lat = sum(1 for r in lat_runs
                           if self.run_next[r] != -1
                           and tr_run[self.run_next[r]] == "lateral")
            zones = len(lat_runs) - into_lat          # a zone is one that exits the tier
            small = own < SUBNET_MIN_KM_FOR_BAND
            rows.append(dict(
                SUBNET=s, KM=round(own, 3), TRUNK_KM=round(tk, 3),
                TRUNK_PCT=round(100.0 * tk / tot, 2) if tot > 0 else 0.0,
                SM_PCT=round(100.0 * sm / tot, 2) if tot > 0 else 0.0,
                LAT_PCT=round(100.0 * lat / tot, 2) if tot > 0 else 0.0,
                SM_ZERO=int(sm <= 0.0),
                N_RUNS=int(rr.size), N_LAT_RUNS=len(lat_runs),
                CHAIN_MED=float(np.median(h)) if h.size else 0.0,
                CHAIN_P90=float(np.percentile(h, 90)) if h.size else 0.0,
                CHAIN_MAX=int(h.max()) if h.size else 0,
                ZONES=int(zones),
                ZONE_PER_KM=round(zones / own, 3) if own > 0 else 0.0,
                HIER_PCT=round(100.0 * into_lat / len(lat_runs), 2) if lat_runs else 0.0,
                ENDS_AT=root_of_sub.get(s, ""),
                BANDED=int(not small)))
        cal = pd.DataFrame(rows)

        def verdict(v, lo, hi):
            if lo is None or hi is None or not np.isfinite(v):
                return "no band"
            return "in band" if lo <= v <= hi else ("below" if v < lo else "above")

        cal["V_TRUNK"] = ["no join onto the Main Pipe" if e and e != "main_pipe" else
                          (verdict(v, *band_t) if b else "too small to band")
                          for v, b, e in zip(cal.TRUNK_PCT, cal.BANDED, cal.ENDS_AT)]
        cal["V_SM"] = [verdict(v, *band_s) if b else "too small to band"
                       for v, b in zip(cal.SM_PCT, cal.BANDED)]
        # A CHECK THAT CANNOT RUN IS NOT A PASS - inheritance-ledger row 2.  Chain depth,
        # zone density and the hierarchy ratio are all measured OVER THE LATERAL RUNS, and
        # a sub-network with none of them has nothing for them to measure.  Scored the
        # arithmetic way, such a sub-network reads CHAIN_MED = 0 -> "pass" and
        # HIER_PCT = 0.0 -> "below": one silent pass and one false failure on the same
        # empty evidence.  The outfall rule multiplies small sub-networks, so this is not a
        # corner case - it is about to be a large share of the table.  They are named
        # instead and counted apart from the verdicts.
        no_lat = (cal.N_LAT_RUNS.to_numpy(int) == 0)
        cal["V_CHAIN"] = np.where(
            no_lat, "no lateral runs - cannot run",
            np.where((cal.CHAIN_MED <= CAL_CHAIN_MED_MAX) &
                     (cal.CHAIN_P90 <= CAL_CHAIN_P90_MAX) &
                     (cal.CHAIN_MAX <= CAL_CHAIN_ABS_MAX), "pass", "FAIL"))
        cal["V_ZONE"] = np.where(
            no_lat, "no lateral runs - cannot run",
            np.where(cal.ZONE_PER_KM <= CAL_ZONE_PER_KM_MAX, "pass",
                     "FAIL - the main tier is missing"))
        cal["V_HIER"] = ["no lateral runs - cannot run" if nl else
                         (verdict(v, *CAL_HIER_PCT) if b else "too small to band")
                         for v, b, nl in zip(cal.HIER_PCT, cal.BANDED, no_lat)]
        self.subnet_cal = cal.sort_values("KM", ascending=False).reset_index(drop=True)

        # --- the summary, which is what goes in the manifest -----------------------------
        b = cal[cal.BANDED == 1]
        km_all = float(cal.KM.sum())
        # `N_NA` is the third state every one of these gates needs and only some of them
        # had: the sub-networks the gate could not be measured on at all.  Without it a
        # sub-network with no lateral runs is counted as a PASS on chain depth, which is
        # inheritance-ledger row 2 in reverse - and the outfall rule is about to make that
        # the common case rather than a curiosity.
        n_nolat = int((cal.V_CHAIN == "no lateral runs - cannot run").sum())
        self.cal_summary = pd.DataFrame([
            {"GATE": "trunk share of a sub-network, %",
             "BAND": f"{band_t[0]:.2f}-{band_t[1]:.2f}",
             "N_BANDED": int((b.V_TRUNK != "no join onto the Main Pipe").sum()),
             "N_IN": int((b.V_TRUNK == "in band").sum()),
             "N_OUT": int(b.V_TRUNK.isin(["below", "above"]).sum()),
             "N_NA": int(len(cal) - len(b))
                     + int((b.V_TRUNK == "no join onto the Main Pipe").sum()),
             "KM_OUT": round(float(b.loc[b.V_TRUNK.isin(["below", "above"]), "KM"].sum()), 1),
             "SOURCE": "asbuilt.targets()['tier_share_trunk_pct'], package band. A "
                       "sub-network that does not reach the Main Pipe is NOT graded "
                       "against it - it has no trunk to take a share of"},
            {"GATE": "sub-main share of a sub-network, %",
             "BAND": f"{band_s[0]:.2f}-{band_s[1]:.2f}",
             "N_BANDED": int(len(b)), "N_IN": int((b.V_SM == "in band").sum()),
             "N_OUT": int(b.V_SM.isin(["below", "above"]).sum()),
             "N_NA": int(len(cal) - len(b)),
             "KM_OUT": round(float(b.loc[b.V_SM.isin(["below", "above"]), "KM"].sum()), 1),
             "SOURCE": "asbuilt.targets()['tier_share_submain_pct'], package band"},
            {"GATE": "sub-networks with NO sub main at all", "BAND": "0 allowed",
             "N_BANDED": int(len(cal)), "N_IN": int((cal.SM_ZERO == 0).sum()),
             "N_OUT": int(cal.SM_ZERO.sum()), "N_NA": 0,
             "KM_OUT": round(float(cal.loc[cal.SM_ZERO == 1, "KM"].sum()), 1),
             "SOURCE": "10_ASBUILT_CALIBRATION sec 1, verbatim. NOTE: the outlet clause in "
                       "tiers() makes this 0 BY CONSTRUCTION, so a 0 here is not evidence "
                       "about the layout - anything above 0 is a real defect"},
            {"GATE": "chain depth lateral->main (med<=2, p90<=4, max 5)",
             "BAND": f"{CAL_CHAIN_MED_MAX}/{CAL_CHAIN_P90_MAX}/{CAL_CHAIN_ABS_MAX}",
             "N_BANDED": int(len(cal) - n_nolat),
             "N_IN": int((cal.V_CHAIN == "pass").sum()),
             "N_OUT": int((cal.V_CHAIN == "FAIL").sum()), "N_NA": n_nolat,
             "KM_OUT": round(float(cal.loc[cal.V_CHAIN == "FAIL", "KM"].sum()), 1),
             "SOURCE": "10_ASBUILT_CALIBRATION sec 1, built median 2 / p90 3 / max 5"},
            {"GATE": "lateral-zone density, zones per km",
             "BAND": f"<= {CAL_ZONE_PER_KM_MAX:g}",
             "N_BANDED": int(len(cal) - n_nolat),
             "N_IN": int((cal.V_ZONE == "pass").sum()),
             "N_OUT": int(cal.V_ZONE.str.startswith("FAIL").sum()), "N_NA": n_nolat,
             "KM_OUT": round(float(
                 cal.loc[cal.V_ZONE.str.startswith("FAIL"), "KM"].sum()), 1),
             "SOURCE": "built 4.27/km; > 7/km means the main tier is missing"},
            {"GATE": "hierarchy ratio, lateral into lateral, %",
             "BAND": f"{CAL_HIER_PCT[0]:g}-{CAL_HIER_PCT[1]:g}",
             "N_BANDED": int((b.V_HIER != "no lateral runs - cannot run").sum()),
             "N_IN": int((b.V_HIER == "in band").sum()),
             "N_OUT": int(b.V_HIER.isin(["below", "above"]).sum()),
             "N_NA": int(len(cal) - len(b))
                     + int((b.V_HIER == "no lateral runs - cannot run").sum()),
             "KM_OUT": round(float(b.loc[b.V_HIER.isin(["below", "above"]), "KM"].sum()), 1),
             "SOURCE": f"10_ASBUILT_CALIBRATION sec 1+4: {CAL_HIER_MEASURED_PCT} % on 272 "
                       f"exits. asbuilt.py still returns "
                       f"{CAL_HIER_RETRACTED_PCT} %, RETRACTED by sec 4"},
        ])
        self.cal_km_all = km_all
        if self.verbose:
            _log(f"per-sub-network calibration on {len(cal):,} sub-networks "
                 f"({int(len(b)):,} at or above the {SUBNET_MIN_KM_FOR_BAND:g} km band "
                 f"floor):")
            for r in self.cal_summary.itertuples():
                _log(f"    {r.GATE:52s} {r.N_IN:5d} pass / {r.N_OUT:5d} out "
                     f"({r.KM_OUT:,.1f} km) / {r.N_NA:5d} cannot run")
        return self

    # ---------------------------------------------------------------- 2i. measure
    def measure(self):
        ab = AB.AsBuilt()
        tgt = ab.targets()
        m_runs = ab.m_runs()
        m_tiers = ab.m_tiers()

        keep = self.keep
        km_corr = float(self.len_out[keep].sum() / 1000.0)
        km_main = float(self.main_pipe.geometry.length.sum() / 1000.0)
        km_all = km_corr + km_main

        tier_km = {t: float(self.len_out[keep & (self.arc_tier == t)].sum() / 1000.0)
                   for t in ("lateral", "main", "sub main")}
        tier_km["trunk main"] = km_main

        # NAMA's IDs give THREE tokens.  Their "lateral" bucket is everything that is not a
        # trunk main and not a sub main - which is our lateral PLUS our main.  Comparing our
        # four-tier split against their three-tier one without saying that would be the
        # vocabulary error this stage's header is about.
        self.tier_table = pd.DataFrame([
            {"TIER": t, "KM": tier_km[t], "PCT_OF_ALL": 100.0 * tier_km[t] / km_all,
             "N_ARCS": int((keep & (self.arc_tier == t)).sum()) if t != "trunk main"
             else int(len(self.main_pipe))}
            for t in ("lateral", "main", "sub main", "trunk main")])

        nama_lateral = tier_km["lateral"] + tier_km["main"]
        self.compare_tier = pd.DataFrame([
            {"BUCKET": "trunk main", "W12_PCT": 100.0 * km_main / km_all,
             "BUILT_PCT": tgt["tier_share_trunk_pct"].value,
             "BAND_LO": tgt["tier_share_trunk_pct"].lo,
             "BAND_HI": tgt["tier_share_trunk_pct"].hi,
             "VERDICT": tgt["tier_share_trunk_pct"].verdict(100.0 * km_main / km_all)},
            {"BUCKET": "sub main", "W12_PCT": 100.0 * tier_km["sub main"] / km_all,
             "BUILT_PCT": tgt["tier_share_submain_pct"].value,
             "BAND_LO": tgt["tier_share_submain_pct"].lo,
             "BAND_HI": tgt["tier_share_submain_pct"].hi,
             "VERDICT": tgt["tier_share_submain_pct"].verdict(
                 100.0 * tier_km["sub main"] / km_all)},
            {"BUCKET": "lateral + main  (= NAMA's 'lateral' token)",
             "W12_PCT": 100.0 * nama_lateral / km_all,
             "BUILT_PCT": tgt["tier_share_lateral_pct"].value,
             "BAND_LO": tgt["tier_share_lateral_pct"].lo,
             "BAND_HI": tgt["tier_share_lateral_pct"].hi,
             "VERDICT": tgt["tier_share_lateral_pct"].verdict(
                 100.0 * nama_lateral / km_all)},
        ])

        # lateral runs discharging into another lateral -----------------------------------
        lat = np.flatnonzero(self.run_tier == "lateral")
        into = []
        for rr in lat:
            nx = self.run_next[rr]
            into.append(self.run_tier[nx] if nx != -1 else "outfall")
        into = pd.Series(into)
        pct_into_lat = 100.0 * float((into == "lateral").mean()) if len(into) else float("nan")
        n_lat = max(len(into), 1)
        pct = {k: 100.0 * float((into == k).sum()) / n_lat
               for k in ("lateral", "main", "sub main", "outfall")}

        # NAMA'S DENOMINATOR IS A DRAFTING ZONE, NOT A RUN, and the two are not the same
        # object: zone A49 holds many runs, and their 87.69 % counts only the pipe by which
        # a whole zone leaves.  Publishing our run-level share against their zone-level one
        # would be a false comparison, so the table names which row is comparable.  ONE row
        # is: a lateral reaching the trunk WITHOUT passing through a main or a sub main.
        # That row is the whole point of the target - it is the W7 failure, where every
        # catchment found its own way to the trunk.
        self.into_table = pd.DataFrame([
            {"A LATERAL RUN DISCHARGES INTO": "another lateral",
             "N": int((into == "lateral").sum()), "PCT": pct["lateral"],
             "NAMA_PCT": m_tiers["lateral_zone_into_lateral_pct"],
             "LIKE_FOR_LIKE": "no - NAMA count ZONES, we count RUNS"},
            {"A LATERAL RUN DISCHARGES INTO": "a main", "N": int((into == "main").sum()),
             "PCT": pct["main"], "NAMA_PCT": float("nan"),
             "LIKE_FOR_LIKE": "no - NAMA's IDs carry no 'main' token"},
            {"A LATERAL RUN DISCHARGES INTO": "a sub main",
             "N": int((into == "sub main").sum()), "PCT": pct["sub main"],
             "NAMA_PCT": m_tiers["lateral_zone_into_submain_pct"],
             "LIKE_FOR_LIKE": "no - zones against runs"},
            {"A LATERAL RUN DISCHARGES INTO": "the TRUNK, direct  <- THE W7 TEST",
             "N": int((into == "outfall").sum()), "PCT": pct["outfall"],
             "NAMA_PCT": m_tiers["lateral_zone_into_trunk_pct"],
             "LIKE_FOR_LIKE": "YES - both count a lateral thing touching the trunk with "
                              "nothing in between"},
        ])
        self.pct_into_lat = pct_into_lat
        self.pct_lat_to_trunk = pct["outfall"]
        self.nama_lat_to_trunk = float(m_tiers["lateral_zone_into_trunk_pct"])

        # joins onto the trunk -------------------------------------------------------------
        mp_roots = int((self.root_kind == "main_pipe").sum())
        joins_per_km = mp_roots / km_main
        self.joins = pd.DataFrame([
            {"ITEM": "outfall nodes discharging into the Main Pipe", "VALUE": mp_roots},
            {"ITEM": "Main Pipe length, km", "VALUE": km_main},
            {"ITEM": "joins per km of trunk", "VALUE": joins_per_km},
            {"ITEM": "MEASURED in NAMA's built network, joins per km of trunk",
             "VALUE": m_tiers["joins_per_km_of_trunk"]},
            {"ITEM": "MEASURED joins in NAMA's built network (count)",
             "VALUE": m_tiers["joins_onto_trunk"]},
        ])
        # the tier of the run that makes each join - a hierarchy joins its trunk with a
        # sub main, not with a lateral
        jt = []
        for i in np.flatnonzero(self.root_kind == "main_pipe"):
            ein = np.flatnonzero(self.keep & (self.V == i))
            for e in ein:
                jt.append(self.arc_tier[e])
        self.join_tier = (pd.Series(jt).value_counts().rename_axis("TIER")
                          .reset_index(name="N") if jt else pd.DataFrame(columns=["TIER", "N"]))

        # runs -----------------------------------------------------------------------------
        rl = self.run_len
        self.run_stats = pd.DataFrame([
            {"ITEM": "runs", "W12": float(self.n_runs), "BUILT": float(m_runs["runs_n"])},
            {"ITEM": "run length median, m", "W12": float(np.median(rl)),
             "BUILT": m_runs["run_between_junctions_median_m"]},
            {"ITEM": "run length p90, m", "W12": float(np.percentile(rl, 90)),
             "BUILT": m_runs["run_between_junctions_p90_m"]},
            {"ITEM": "run length MAXIMUM, m  (the governing statistic, philosophy sec 4)",
             "W12": float(rl.max()), "BUILT": float("nan")},
            {"ITEM": "junctions per km", "W12": float(
                ((np.bincount(self.V[self.keep], minlength=self.n_nodes) >= 2).sum())
                / km_corr), "BUILT": m_runs["junctions_per_km"]},
            {"ITEM": "heads per km", "W12": float(self.is_head.sum() / km_corr),
             "BUILT": m_runs["heads_per_km"]},
        ])

        # heads ----------------------------------------------------------------------------
        hb = pd.Series(self.head_by[self.is_head]).value_counts()
        self.head_table = hb.rename_axis("HEAD_BY").reset_index(name="N")
        self.head_table["KM"] = [
            float(self.len_out[self.is_head & (self.head_by == k)].sum() / 1000.0)
            for k in self.head_table.HEAD_BY]
        self.head_saving_m = float(self.start_m[self.is_head].sum())

        # stranded load --------------------------------------------------------------------
        sq = float(self.strand_q[self.is_head].sum())
        sn = int(self.strand_n[self.is_head].sum())
        pq = float(self.prune.Q_M3D.sum()) if len(self.prune) else 0.0
        pruned_idx = np.flatnonzero(~self.keep)
        pq_s2 = float(self.arcs.Q_M3D.to_numpy(float)[pruned_idx].sum())
        self.stranded = pd.DataFrame([
            {"ITEM": "plots whose gate falls inside a head setback", "N": sn, "Q_M3D": sq,
             "RESOLUTION": f"property connection to the junction chamber they were cut "
                           f"from; every one is inside the {FANOUT_OFFSET_M:g} m setback, "
                           f"far inside the {PCS_MAX_LEN:g} m PCS limit (G203-p18)"},
            {"ITEM": "plots on a pruned arc, MY nearest-arc allocation",
             "N": int(self.prune.N_PLOT.sum()) if len(self.prune) else 0, "Q_M3D": pq,
             "RESOLUTION": "connect at the chamber the pruned arc met; stage 5b sizes it"},
            {"ITEM": "the same arcs under s1/s2's OWN allocation (Q_M3D carried on the arc)",
             "N": -1, "Q_M3D": pq_s2,
             "RESOLUTION": "the two allocations disagree because s2's ridge pre-split cut "
                           "151 corridors after s1 had allocated. BOTH are published rather "
                           "than the smaller one: the gap is the honest measure of how much "
                           "this depends on which corridor a plot is tied to"},
        ])

        # UPHILL, BEFORE AND AFTER, WITH EVERY BASIS NAMED ------------------------------
        # Four rows, because three different denominators are in circulation and mixing
        # them is how a number becomes wrong without anybody editing it:
        #   * s2's headline 23.15 % divides 414.0 km by 1,788.3 km - the corridor network
        #     WITHOUT the 30.88 km of islands.  Its km is right and its denominator is
        #     narrower than its own published arc set.
        #   * s2's UPHILL flag over EVERY published arc gives 22.75 % on 1,819.45 km.
        #   * this stage repairs the island directions (38 arcs turned round), which moves
        #     the numerator, and then trims and prunes, which moves the denominator.
        # None of these is an improvement and the table does not present one.
        f0 = self.arcs.FALL_M.to_numpy(float)
        adv0 = f0 < -C.ADVERSE_MIN_M
        fi = self.fall
        advi = fi < -C.ADVERSE_MIN_M
        fall = self.fall_pub
        adv = fall < -C.ADVERSE_MIN_M
        L0, Lk = self.L, self.len_out
        S2_HEADLINE_PCT, S2_HEADLINE_KM, S2_HEADLINE_DEN_KM = 23.15, 414.0, 1788.3
        #   quoted from s2_orient's own manifest rows UPHILL_PCT_PUBLISHED /
        #   UPHILL_KM_PUBLISHED; the denominator is 414.0 / 0.2315 and it is
        #   NARROWER than s2's own published arc set by the 30.88 km of islands.
        self.uphill = pd.DataFrame([
            {"BASIS": "s2's headline, as printed in its own manifest",
             "KM": S2_HEADLINE_DEN_KM, "UPHILL_KM": S2_HEADLINE_KM,
             "UPHILL_PCT": S2_HEADLINE_PCT},
            {"BASIS": "s2's UPHILL flag over EVERY arc it published",
             "KM": float(L0.sum() / 1000.0),
             "UPHILL_KM": float(L0[adv0].sum() / 1000.0),
             "UPHILL_PCT": 100.0 * float(L0[adv0].sum() / L0.sum())},
            {"BASIS": "s3 after the island directions are repaired, before any trimming",
             "KM": float(L0.sum() / 1000.0),
             "UPHILL_KM": float(L0[advi].sum() / 1000.0),
             "UPHILL_PCT": 100.0 * float(L0[advi].sum() / L0.sum())},
            {"BASIS": "s3 AS PUBLISHED - set back, pruned, falls re-sampled on the trimmed "
                      "geometry",
             "KM": km_corr,
             "UPHILL_KM": float(Lk[self.keep & adv].sum() / 1000.0),
             "UPHILL_PCT": 100.0 * float(Lk[self.keep & adv].sum() / Lk[self.keep].sum())},
            {"BASIS": "MEASURED, NAMA's built network - CONTEXT, NOT PERMISSION",
             "KM": float(C.BENCHMARKS["ASBUILT_KM_GRAVITY"][0]),
             "UPHILL_KM": float("nan"),
             "UPHILL_PCT": float(ab.m_terrain()["uphill_length_pct"])},
            {"BASIS": "W11a, the design this replaces",
             "KM": 1731.7, "UPHILL_KM": 737.7,
             "UPHILL_PCT": 100.0 * C.BENCHMARKS["UPHILL_SHARE_W11A"][0]},
        ])

        # sub-networks that vanished entirely.  ZERO SILENT DROPS: a subnet whose whole
        # content was a finger is a real change to the scope and it is named, not absorbed.
        s2_out = set(self.onodes.loc[self.onodes.KIND == "outfall", "NODE_ID"])
        alive = {self.nid_out[i] for i in np.flatnonzero(self.root_kind == "main_pipe")}
        gone = sorted(s2_out - alive)
        rows = []
        for nm in gone:
            i = self.nix[nm]
            ein = np.flatnonzero((self.V == i) | (self.U == i))
            rows.append({"OUTFALL": nm,
                         "SUBNET": (self.onodes.loc[self.onodes.NODE_ID == nm, "SUBNET"]
                                    .iloc[0]),
                         "ARCS_WAS": int(len(ein)),
                         "KM_WAS": float(self.L[ein].sum() / 1000.0),
                         "Q_M3D_WAS": float(self.arcs.Q_M3D.to_numpy(float)[ein].sum()),
                         "WHY": "every arc in it was pruned as a finger - a dead-end reach "
                                f"under {FINGER_MIN_M:g} m serving nothing (philosophy 4)"})
        self.dropped_subnets = (pd.DataFrame(rows) if rows else
                                pd.DataFrame(columns=["OUTFALL", "SUBNET", "ARCS_WAS",
                                                      "KM_WAS", "Q_M3D_WAS", "WHY"]))

        # THE LONGEST RUNS.  Philosophy sec 4: report run length as a MAXIMUM, never a
        # median, because chamber spacing (H12) and run length (P3) are different rules and
        # a long run is a chambering job, not a defect.  Named here so the chamber stage
        # meets them on purpose: at the working 100 m split a 5.1 km run is 52 chambers.
        top = np.argsort(-self.run_len)[:15]
        self.long_runs = pd.DataFrame({
            "RUN_ID": [f"R{int(r):06d}" for r in top],
            "TIER": [self.run_tier[int(r)] for r in top],
            "LEN_M": np.round(self.run_len[top], 1),
            "CHAMBERS_AT_100M": np.ceil(self.run_len[top] / C.MH_SPLIT_LEN).astype(int),
            "SUB_KM": np.round(self.run_sub_km[top], 3),
        })

        self.km_corr, self.km_main, self.km_all = km_corr, km_main, km_all
        self.tier_km = tier_km
        return self

    # ---------------------------------------------------------------- 2j. sweeps
    def sweep(self):
        keep = self.keep
        km_main = float(self.main_pipe.geometry.length.sum() / 1000.0)
        km_all = float(self.len_out[keep].sum() / 1000.0) + km_main
        tgt = AB.AsBuilt().targets()["tier_share_submain_pct"]

        rows = []
        for sk in SUBMAIN_SWEEP:
            t = self.tiers(submain_km=sk)
            at = np.array([""] * len(self.arcs), dtype=object)
            at[keep] = t[self.run_id[keep]]
            sm = float(self.len_out[keep & (at == "sub main")].sum() / 1000.0)
            mn = float(self.len_out[keep & (at == "main")].sum() / 1000.0)
            lt = float(self.len_out[keep & (at == "lateral")].sum() / 1000.0)
            pct = 100.0 * sm / km_all
            nroute = self._submain_routes(t)
            km_net = float(self.len_out[keep].sum() / 1000.0)
            rows.append({"SUBMAIN_KM": sk, "SUBMAIN_KM_OF_NETWORK": sm,
                         "SUBMAIN_PCT": pct, "MAIN_KM": mn, "LATERAL_KM": lt,
                         "N_SUBMAIN_RUNS": int((t == "sub main").sum()),
                         "N_SUBMAIN_ROUTES": nroute,
                         "KM_NET_PER_ROUTE": km_net / nroute if nroute else float("nan"),
                         "ROUTE_IN_4_10_KM": int(nroute and 4.0 <= km_net / nroute <= 10.0),
                         "IN_BUILT_BAND": int(tgt.lo <= pct <= tgt.hi),
                         "VERDICT": tgt.verdict(pct),
                         "SHIPPED": int(abs(sk - self.submain_km) < 1e-9)})
        self.sweep_submain = pd.DataFrame(rows)

        rows = []
        for br in (2, 3, 4, 5, 6):
            for bp in (400.0, 750.0, 1200.0, 2000.0):
                t = self.tiers(budget_runs=br, budget_path_m=bp)
                at = np.array([""] * len(self.arcs), dtype=object)
                at[keep] = t[self.run_id[keep]]
                lt = float(self.len_out[keep & (at == "lateral")].sum() / 1000.0)
                mn = float(self.len_out[keep & (at == "main")].sum() / 1000.0)
                rows.append({"BUDGET_RUNS": br, "BUDGET_PATH_M": bp,
                             "LATERAL_KM": lt, "MAIN_KM": mn,
                             "LATERAL_PCT": 100.0 * lt / km_all,
                             "SHIPPED": int(br == self.budget_runs
                                            and abs(bp - self.budget_path_m) < 1e-9)})
        self.sweep_budget = pd.DataFrame(rows)
        return self

    # ---------------------------------------------------------------- 2k. publish
    def publish(self):
        import geopandas as gpd
        from shapely.geometry import Point

        os.makedirs(os.path.dirname(OUT_GPKG), exist_ok=True)
        os.makedirs(RUN, exist_ok=True)
        if os.path.exists(OUT_GPKG):
            os.remove(OUT_GPKG)

        keep = self.keep
        a = self.arcs
        idx = np.flatnonzero(keep)
        out = gpd.GeoDataFrame({
            "EDGE_UID": [f"E{i:07d}" for i in range(len(idx))],
            "CID": a.CID.to_numpy(object)[idx],
            "US_NODE": [self.nid_out[i] for i in self.Uo[idx]],
            "DS_NODE": [self.nid_out[i] for i in self.V[idx]],
            "TIER": self.arc_tier[idx],
            "RUN_ID": [f"R{r:06d}" for r in self.run_id[idx]],
            "IS_HEAD": self.is_head[idx].astype(int),
            "HEAD_BY": self.head_by[idx],
            "SETBACK_M": np.round(self.start_m[idx], 3),
            "LEN_M": np.round(self.len_out[idx], 3),
            "LEN_WAS_M": np.round(self.L[idx], 3),
            "SUB_KM": np.round(self.arc_sub_km[idx], 4),
            "Q_UP_M3D": np.round(self.arc_q_up[idx], 3),
            "Q_OWN_M3D": np.round(a.Q_M3D.to_numpy(float)[idx], 3),
            "PATH_UP_M": np.round(self.arc_path_up[idx], 1),
            "RUN_LEN_M": np.round(self.run_len[self.run_id[idx]], 1),
            "RUN_DEPTH": self.run_depth[self.run_id[idx]].astype(int),
            # hops from this run to the first non-lateral one - the as-built calibration's
            # "chain depth, lateral -> main": built median 2, p90 3, max 5.  0 on a run that
            # is not a lateral, because the chain it measures starts at a lateral.
            "CHAIN": self.run_hops[self.run_id[idx]].astype(int),
            "GND_FALL": np.round(self.fall_pub[idx], 4),
            "AGN_GRADE": (self.fall_pub[idx] < -C.ADVERSE_MIN_M).astype(int),
            "INLET_DEG": np.round(self.inlet[idx], 1),
            "DIR_CONF": a.DIR_CONF.to_numpy(object)[idx],
            # SUBNET comes from THIS stage's forest, not from s2's arc column: s2 leaves it
            # blank on every head, island and unused corridor, and a reach nobody can
            # attribute cannot be calibrated.  One column, one authority.
            "SUBNET": self.arc_subnet[idx],
            "ROOT_KIND": self.root_kind[self.rootof[self.Uo[idx]]],
            "SRC": a.SRC.to_numpy(object)[idx],
            "CONFIDENCE": a.CONFIDENCE.to_numpy(object)[idx],
            "STAGE": STAGE,
            "TAU_FLAG": TAU_FLAG,
        }, geometry=[self.geom_out[i] for i in idx], crs=f"EPSG:{CRS_EPSG}")
        out.to_file(OUT_GPKG, layer="reaches", driver="GPKG")

        ni = np.flatnonzero(self.used)
        indeg = np.zeros(self.n_nodes, dtype=np.int64)
        np.add.at(indeg, self.V[keep], 1)
        kind = np.where(self.out_arc[ni] == -1, "outfall",
                        np.where(indeg[ni] == 0, "head",
                                 np.where(indeg[ni] >= 2, "junction", "through")))
        nodes = gpd.GeoDataFrame({
            "NODE_UID": [self.nid_out[i] for i in ni],
            "X": np.round(self.NX_out[ni], 3),
            "Y": np.round(self.NY_out[ni], 3),
            "GRD_M": np.round(self.NZ_out[ni], 3),
            "KIND": kind,
            "N_IN": indeg[ni],
            "DS_NODE": [self.nid_out[self.V[self.out_arc[i]]] if self.out_arc[i] != -1
                        else "" for i in ni],
            "TIER_OUT": [self.arc_tier[self.out_arc[i]] if self.out_arc[i] != -1 else ""
                         for i in ni],
            "ROOT_KIND": self.root_kind[self.rootof[ni]],
            "SUBNET": self.node_subnet[ni],
            "MADE_BY": [self.made_by[i] for i in ni],
            "SET_BACK_FROM": [self.node_parent[i] for i in ni],
            "STAGE": STAGE,
        }, geometry=[Point(self.NX_out[i], self.NY_out[i]) for i in ni],
            crs=f"EPSG:{CRS_EPSG}")
        nodes.to_file(OUT_GPKG, layer="nodes", driver="GPKG")

        mp = self.main_pipe.copy()
        mp["TIER"] = "trunk main"
        mp["LEN_M"] = mp.geometry.length
        mp["SRC"] = "main_pipe"
        mp["CONFIDENCE"] = "drafted"
        mp["NOTE"] = ("CLIENT INPUT, not derived here. G203-p35 sec 5 defines a trunk main "
                      "by D > 800 mm, length > 1,000 m without connections, or upstream of "
                      "the STP / main pumping station; the drawn alignment satisfies the "
                      "third by construction. Diameter is stage 6's answer, not this one's.")
        mp["STAGE"] = STAGE
        mp[["TIER", "LEN_M", "SRC", "CONFIDENCE", "NOTE", "STAGE", "geometry"]].to_file(
            OUT_GPKG, layer="trunk", driver="GPKG")

        runs = pd.DataFrame({
            "RUN_ID": [f"R{r:06d}" for r in range(self.n_runs)],
            "TIER": self.run_tier,
            "LEN_M": np.round(self.run_len, 2),
            "SUB_KM": np.round(self.run_sub_km, 4),
            "DEPTH": self.run_depth.astype(int),
            "PATH_UP_M": np.round(self.run_path_m, 1),
            "NEXT_RUN": [f"R{r:06d}" if r != -1 else "" for r in self.run_next],
            "NEXT_TIER": [self.run_tier[r] if r != -1 else "outfall" for r in self.run_next],
        })
        _write_table(runs, "runs")

        _write_table(self.tier_table, "tiers")
        _write_table(self.compare_tier, "compare_tier")
        _write_table(self.subnet_cal, "subnet_calibration")
        _write_table(self.cal_summary, "calibration_gates")
        _write_table(self.head_table, "heads")
        _write_table(self.head_passes, "head_passes")
        _write_table(self.prune, "pruned")
        _write_table(self.stranded, "stranded")
        _write_table(self.dropped_subnets, "dropped_subnets")
        _write_table(self.run_stats, "run_stats")
        _write_table(self.long_runs, "long_runs")
        _write_table(self.joins, "joins")
        _write_table(self.join_tier, "join_tier")
        _write_table(self.into_table, "lateral_into")
        _write_table(self.uphill, "uphill")
        _write_table(self.sweep_submain, "sweep_submain")
        _write_table(self.sweep_budget, "sweep_budget")
        _write_table(self.gate_load_check, "gate_load_check")
        _write_table(self.island_report if len(self.island_report) else
                     pd.DataFrame([{"COMP": "", "NOTE": "no islands"}]), "islands")
        _write_table(self.exceptions(), "exceptions")
        _write_table(self.manifest(), "manifest")
        return self

    # ---------------------------------------------------------------- 2l. exceptions
    def exceptions(self) -> pd.DataFrame:
        """THE REGISTER THAT MUST BE EMPTY.

        Recomputed from the arrays about to be published, not from the arrays used to build
        them: a node with two outgoing pipes, a component with no outfall, a tier inversion,
        a head that still touches the chamber it was cut from."""
        rows = []
        keep = self.keep
        cnt = np.bincount(self.Uo[keep], minlength=self.n_nodes)
        for i in np.flatnonzero(cnt > 1):
            rows.append({"KIND": "two pipes leave one node", "WHERE": self.nid_out[i],
                         "DETAIL": f"{int(cnt[i])} outgoing"})
        for i in np.flatnonzero(self.root_kind == "orphan"):
            rows.append({"KIND": "component drains nowhere (H15)",
                         "WHERE": self.nid_out[i], "DETAIL": "root is neither the Main Pipe "
                                                             "nor an island low point"})
        if self.tier_inversions:
            rows.append({"KIND": "tier inversion", "WHERE": "-",
                         "DETAIL": f"{self.tier_inversions} runs discharge into a lower tier"})
        for e in np.flatnonzero(self.is_head & (self.start_m > 0)):
            if self.start_m[e] < MH_SNAP_M:
                rows.append({"KIND": "head set back less than the chamber clearance",
                             "WHERE": self.arcs.CID.iloc[e],
                             "DETAIL": f"{self.start_m[e]:.2f} m"})
        det = np.zeros(len(self.arcs), dtype=bool)
        det[self.head_cand] = True
        for e in np.flatnonzero(self.is_head & det & (self.start_m < FANOUT_OFFSET_M)):
            rows.append({"KIND": "detached head inside the 10 m clearance",
                         "WHERE": self.arcs.CID.iloc[e],
                         "DETAIL": f"{self.start_m[e]:.2f} m"})
        return pd.DataFrame(rows) if rows else pd.DataFrame(
            [{"KIND": "", "WHERE": "", "DETAIL": "NONE - the hard rule holds everywhere"}])

    # ---------------------------------------------------------------- 2m. manifest
    def manifest(self) -> pd.DataFrame:
        ab = AB.AsBuilt()
        mr, mt = ab.m_runs(), ab.m_tiers()
        rows = [
            ("stage", STAGE_VERSION, "", "this file"),
            ("criteria", CR.CRITERIA_VERSION if hasattr(CR, "CRITERIA_VERSION")
             else "w12/criteria.py", "", "w12/criteria.py"),
            ("run_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "", ""),
            ("orient_sha1", _sha1(ORIENT_GPKG), "", ORIENT_GPKG),
            ("main_pipe_sha1", _sha1(MAIN_PIPE), "", MAIN_PIPE),
            ("plots_sha1", _sha1(PLOT_LOADS), "", PLOT_LOADS),

            ("INLET_MIN_DEG", INLET_MIN_DEG, "deg", "G203-p30, verbatim"),
            ("DN_TRUNK_MIN", DN_TRUNK_MIN, "mm", "G203-p35 sec 5"),
            ("TRUNK_MIN_RUN_M", TRUNK_MIN_RUN_M, "m", "G203-p35 sec 5 ('1,000 mm' typo)"),
            ("LATERAL_MAX_LEN_G203", LATERAL_MAX_LEN_G203, "m",
             "G203-p22 Table 6 - READ AND NOT ENFORCED: it governs the TERTIARY lateral, "
             "not the street run this stage calls a lateral"),
            ("PCS_MAX_LEN", PCS_MAX_LEN, "m", "G203-p18 under Table 4"),
            ("MH_SNAP_M", MH_SNAP_M, "m", "criteria - the one chamber-clearance constant"),
            ("FANOUT_OFFSET_M", FANOUT_OFFSET_M, "m", "PROJECT rule, user 2026-08-18"),
            ("FINGER_MIN_M", FINGER_MIN_M, "m", "PROJECT, philosophy sec 4 ('~60 m', ours)"),
            ("FRONTAGE_M", FRONTAGE_M, "m", "PROJECT, inherited from s1_roads unchanged"),
            ("LATERAL_BUDGET_RUNS", LATERAL_BUDGET_RUNS, "", "PROJECT, philosophy sec 4"),
            ("LATERAL_BUDGET_PATH_M", LATERAL_BUDGET_PATH_M, "m",
             "PROJECT, philosophy sec 4"),
            ("SUBMAIN_KM", self.submain_km, "km",
             "CALIBRATED against the built sub-main share; sweep_submain publishes the grid"),
            ("TAU_PA", C.TAU_PA, "Pa", "ENGINEER 2026-09-03, GAP-9 open"),

            ("BUILT_TIER_TRUNK_PCT", mt["tier_share_trunk_pct"], "%",
             "MEASURED asbuilt.m_tiers, whole network"),
            ("BUILT_TIER_SUBMAIN_PCT", mt["tier_share_submain_pct"], "%",
             "MEASURED asbuilt.m_tiers, whole network"),
            ("BUILT_TIER_LATERAL_PCT", mt["tier_share_lateral_pct"], "%",
             "MEASURED asbuilt.m_tiers, whole network"),
            ("BUILT_RUN_MEDIAN_M", mr["run_between_junctions_median_m"], "m",
             "MEASURED asbuilt.m_runs"),
            ("BUILT_JOINS_PER_KM_TRUNK", mt["joins_per_km_of_trunk"], "1/km",
             "MEASURED asbuilt"),
            ("BUILT_LAT_INTO_LAT_PCT", mt["lateral_zone_into_lateral_pct"], "%",
             "MEASURED asbuilt - a design where every catchment finds its own way to the "
             "trunk is the W7 failure"),

            ("arcs_in", int(len(self.arcs)), "", "from s2_orient"),
            ("arcs_out", int(self.keep.sum()), "", "after pruning"),
            ("km_in", self.km_in, "km", "s2_orient's published corridor length"),
            ("km_corridors", self.km_corr, "km", "after setbacks and pruning"),
            ("km_trunk_input", self.km_main, "km", "client Main Pipe, an INPUT"),
            ("km_all", self.km_all, "km", "corridors + trunk"),
            ("nodes_out", int(self.n_nodes), "", "including the minted head chambers"),
            ("heads_n", int(self.is_head.sum()), "", "runs that start at a gate"),
            ("heads_set_back_n", int((self.is_head & (self.start_m > 0)).sum()), "",
             "s2 handed over 2,887 needing it"),
            ("head_setback_km", self.head_saving_m / 1000.0, "km",
             "pipe NOT laid upstream of the first customer"),
            ("pruned_n", int(len(self.prune)), "", "fingers and sub-clearance stubs"),
            ("pruned_km", float(self.prune.LEN_M.sum() / 1000.0) if len(self.prune) else 0.0,
             "km", ""),
            ("exceptions_n", int(len(self.exceptions()))
             if self.exceptions().iloc[0].KIND else 0, "",
             "EXCEPTIONS TO THE HARD RULE - must be zero"),
            ("components", int(self.components), "", "H15: each ends at exactly one outfall"),
            ("orphan_roots", int(self.orphan_roots), "", "components draining nowhere"),
            ("tier_inversions", int(self.tier_inversions), "",
             "a lateral receiving a main - must be zero"),
            ("runs_n", int(self.n_runs), "", ""),
            ("run_median_m", float(np.median(self.run_len)), "m",
             f"built {mr['run_between_junctions_median_m']:.2f}"),
            ("run_max_m", float(self.run_len.max()), "m",
             "the governing statistic (philosophy sec 4)"),
            ("lat_into_lat_pct", self.pct_into_lat, "%",
             f"built {mt['lateral_zone_into_lateral_pct']:.2f} %"),
            ("joins_per_km_trunk", float((self.root_kind == "main_pipe").sum()
                                         / self.km_main), "1/km",
             f"built {mt['joins_per_km_of_trunk']:.2f}"),
            ("submain_routes", int(self._submain_routes(self.run_tier)), "",
             "maximal chains of sub-main runs; philosophy sec 4 expects one per 4-10 km"),
            ("km_net_per_submain_route",
             self.km_corr / max(self._submain_routes(self.run_tier), 1), "km",
             "THE ONE MEASURE THIS STAGE MISSES - see sweep_submain"),
            ("uphill_pct_after", float(self.uphill.iloc[3].UPHILL_PCT), "%",
             "RE-MEASURED, not improved - a hierarchy re-labels pipe, it does not tilt "
             "ground. s2's own value is the row above it"),
        ]
        for t in ("lateral", "main", "sub main", "trunk main"):
            rows.append((f"km_{t.replace(' ', '_')}", self.tier_km[t], "km", ""))

        # --- THE PER-SUB-NETWORK CALIBRATION -------------------------------------------
        # The as-built gates are measured PER SUB-NETWORK, because a network average hides
        # exactly the failure the calibration names: "a subnetwork with 0 % sub-main fails
        # even if the average passes" (10_ASBUILT_CALIBRATION sec 1).
        cal, cs = self.subnet_cal, self.cal_summary
        b = cal[cal.BANDED == 1]
        rows += [
            ("CAL_CHAIN_MED_MAX", CAL_CHAIN_MED_MAX, "hops",
             "10_ASBUILT_CALIBRATION sec 1, built median 2 (excl. 5A-1)"),
            ("CAL_CHAIN_P90_MAX", CAL_CHAIN_P90_MAX, "hops", "built p90 3, band <= 4"),
            ("CAL_CHAIN_ABS_MAX", CAL_CHAIN_ABS_MAX, "hops", "built max 5, an absolute"),
            ("CAL_ZONE_PER_KM_MAX", CAL_ZONE_PER_KM_MAX, "1/km",
             "built 4.27/km; above 7 the MAIN TIER IS MISSING - the single best "
             "structural symptom"),
            ("CAL_HIER_PCT_LO", CAL_HIER_PCT[0], "%", "10_ASBUILT_CALIBRATION sec 1"),
            ("CAL_HIER_PCT_HI", CAL_HIER_PCT[1], "%", "10_ASBUILT_CALIBRATION sec 1"),
            ("CAL_HIER_MEASURED_PCT", CAL_HIER_MEASURED_PCT, "%",
             "MEASURED, 272 exits. asbuilt.py still returns "
             f"{CAL_HIER_RETRACTED_PCT} %, RETRACTED by 10_ASBUILT_CALIBRATION sec 4 - "
             "the retracted figure is published beside it rather than silently replaced"),
            ("CAL_TRUNK_BAND_LO", round(float(self.cal_band_trunk[0]), 3), "%",
             "asbuilt.targets()['tier_share_trunk_pct'], the spread BETWEEN packages"),
            ("CAL_TRUNK_BAND_HI", round(float(self.cal_band_trunk[1]), 3), "%", ""),
            ("CAL_SUBMAIN_BAND_LO", round(float(self.cal_band_submain[0]), 3), "%",
             "asbuilt.targets()['tier_share_submain_pct']"),
            ("CAL_SUBMAIN_BAND_HI", round(float(self.cal_band_submain[1]), 3), "%", ""),
            ("SUBNET_MIN_KM_FOR_BAND", SUBNET_MIN_KM_FOR_BAND, "km",
             "DERIVED from asbuilt.A_PKG_MIN_KM_GEOM - the floor the band itself was "
             "measured above"),
            ("TRUNK_SAMPLE_M", TRUNK_SAMPLE_M, "m",
             "NUMERICAL RESOLUTION, not a design value: the step at which the Main Pipe is "
             "sampled to apportion its length by nearest join"),
            ("subnets_n", int(len(cal)), "",
             "sub-networks on the published layer. Every reach carries one - s2 leaves the "
             "heads and islands blank and this stage takes the label from its own forest"),
            ("subnets_banded", int(len(b)), "",
             f"at or above the {SUBNET_MIN_KM_FOR_BAND:g} km band floor"),
            ("subnets_no_submain", int(cal.SM_ZERO.sum()), "",
             "sub-networks with NO sub main at all. 10_ASBUILT_CALIBRATION sec 1: this "
             "FAILS even if the average passes. The outlet clause in tiers() makes it 0 "
             "by construction, so anything above 0 is a real defect"),
            ("subnets_trunk_out_of_band", int(cs.iloc[0].N_OUT), "", str(cs.iloc[0].BAND)),
            ("subnets_submain_out_of_band", int(cs.iloc[1].N_OUT), "",
             str(cs.iloc[1].BAND)),
            ("subnets_chain_fail", int(cs.iloc[3].N_OUT), "",
             "chain depth past median 2 / p90 4 / max 5"),
            ("km_chain_fail", float(cs.iloc[3].KM_OUT), "km", ""),
            ("subnets_with_no_lateral_runs", int(cs.iloc[3].N_NA), "",
             "sub-networks the chain-depth, zone-density and hierarchy-ratio gates CANNOT "
             "BE MEASURED ON, because all three are computed over the lateral runs and "
             "these have none. Counted apart from the verdicts: scored arithmetically they "
             "read 'pass' on chain depth and 'below' on the hierarchy ratio off the same "
             "empty evidence (inheritance row 2). The outfall rule makes small "
             "sub-networks the common case, so this number is the honesty of the three "
             "gates above it"),
            ("subnets_zone_density_fail", int(cs.iloc[4].N_OUT), "",
             f"above {CAL_ZONE_PER_KM_MAX:g} lateral zones per km - the main tier is "
             f"missing there"),
            ("km_zone_density_fail", float(cs.iloc[4].KM_OUT), "km", ""),
            ("subnets_hier_out_of_band", int(cs.iloc[5].N_OUT), "",
             f"outside {CAL_HIER_PCT[0]:g}-{CAL_HIER_PCT[1]:g} %"),
            ("chain_median_all", float(np.median(cal.CHAIN_MED)) if len(cal) else 0.0,
             "hops", "median across sub-networks of their own median chain depth"),
            ("chain_max_all", int(cal.CHAIN_MAX.max()) if len(cal) else 0, "hops",
             f"the deepest lateral chain anywhere; the absolute is {CAL_CHAIN_ABS_MAX}"),
            ("zone_per_km_all",
             round(float(cal.ZONES.sum() / max(cal.KM.sum(), 1e-9)), 3), "1/km",
             "over the whole network; built 4.27"),
        ]
        return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "SOURCE"])

    # ---------------------------------------------------------------- 2n. report
    def report(self) -> str:
        ab = AB.AsBuilt()
        mt, mr = ab.m_tiers(), ab.m_runs()
        exc = self.exceptions()
        n_exc = len(exc) if exc.iloc[0].KIND else 0
        L = []
        A = L.append
        A(f"# W12 stage 3 - the hierarchy, on the oriented tree\n")
        A(f"`{STAGE_VERSION}`  ·  {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}  ·  "
          f"{TAU_FLAG}\n")
        A("## The answer\n")
        A(f"**Exceptions to the hard rule: {n_exc}.** {int(self.is_head.sum()):,} heads, "
          f"{int((self.is_head & (self.start_m > 0)).sum()):,} of them set back off a "
          f"chamber that already had an outlet - s2 handed over 2,887 needing it. "
          f"{self.head_saving_m/1000.0:,.1f} km of pipe is NOT laid, because it would have "
          f"run upstream of the first customer it serves.\n")
        A(f"{self.km_corr:,.1f} km of corridor plus the client's {self.km_main:,.2f} km "
          f"Main Pipe = **{self.km_all:,.1f} km**, in **{self.components} components, each "
          f"ending at exactly one outfall** (H15), **{self.orphan_roots} draining "
          f"nowhere**.\n")
        A("### Tier shares against the built network\n")
        A(_md(self.compare_tier, 2) + "\n")
        A("The vocabulary matters and the table says which one it uses. NAMA's manhole IDs "
          "carry three tokens - trunk main, sub main, and everything else - so their "
          "'lateral' bucket is our lateral PLUS our main. Comparing a four-tier split "
          "against a three-tier one without saying so is the error philosophy sec 4 warns "
          "about.\n")
        A(_md(self.tier_table, 2) + "\n")
        nroute = self._submain_routes(self.run_tier)
        A(f"Philosophy sec 4 says to **expect roughly 270 km of sub main** and that a design "
          f"producing 20 km is wrong on sight. This one produces "
          f"**{self.tier_km['sub main']:,.1f} km** over **{nroute} routes**, one per "
          f"{self.km_corr / max(nroute, 1):,.1f} km of network against the measured "
          f"4-10 km. **The route density is the one measure this stage does NOT hit.** The "
          f"threshold that lands the sub-main SHARE on the built network's own "
          f"{AB.AsBuilt().targets()['tier_share_submain_pct'].value:.2f} % gives fewer, "
          f"longer routes; the sweep below shows nothing in the range satisfies both "
          f"measures at once, and the share is preferred because it is the measurement the "
          f"as-built actually supports.\n")
        A(f"The trunk's **diameter is not known at this stage**, so only the third of "
          f"G203-p35 sec 5's three criteria - upstream of the STP or the main pumping "
          f"station - can be tested here. D > {DN_TRUNK_MIN:g} mm is stage 6's answer.\n")
        A(f"**G203-p22 Table 6's 45 m maximum length is NOT applied to this `lateral` "
          f"tier.** It governs the TERTIARY lateral - the pipe from a house connection "
          f"chamber to the street sewer, which stage 5b mints. NAMA's own street runs have "
          f"a median of {mr['run_between_junctions_median_m']:.1f} m and a p90 of "
          f"{mr['run_between_junctions_p90_m']:.1f} m; applying the tertiary rule to them "
          f"would condemn most of the built network.\n")
        A("### Runs\n")
        A(_md(self.run_stats, 2) + "\n")
        A(f"**Junctions per km reads low against the built network on purpose.** A junction "
          f"is a node with two or more pipes arriving, and the tertiary tier - riders and "
          f"the 45 m G203 laterals off every house connection - is not in this layer at "
          f"all; stage 5b mints it. NAMA's {mr['junctions_per_km']:.2f}/km counts a network "
          f"that already has its tertiary in place, so the two are not yet comparable and "
          f"the gap should not be read as this design being coarse.\n")
        A("The longest runs, so the chamber stage meets them on purpose rather than "
          "discovering them:\n")
        A(_md(self.long_runs, 1) + "\n")
        A("### Heads - where each one starts, and why\n")
        A(_md(self.head_table, 2) + "\n")
        A(_md(self.head_passes, 2) + "\n")
        if len(self.prune):
            A(f"Pruned: {len(self.prune):,} arcs, {self.prune.LEN_M.sum()/1000:,.2f} km.\n")
            A(_md(self.prune.groupby("WHY").agg(N=("CID", "size"),
                                                KM=("LEN_M", lambda s: s.sum()/1000.0),
                                                Q_M3D=("Q_M3D", "sum")).reset_index(), 3)
              + "\n")
        A("### Nothing is dropped silently\n")
        A(_md(self.stranded, 2) + "\n")
        if len(self.dropped_subnets):
            A(f"**{len(self.dropped_subnets)} sub-networks disappeared entirely** - every "
              f"arc in each was a dead-end reach under {FINGER_MIN_M:g} m serving nothing, "
              f"so the whole catchment was one finger. Together "
              f"{self.dropped_subnets.KM_WAS.sum():.3f} km and "
              f"{self.dropped_subnets.Q_M3D_WAS.sum():.2f} m3/d on s2's own allocation. "
              f"Named, not absorbed.\n")
            A(_md(self.dropped_subnets.drop(columns=["WHY"]), 3) + "\n")
        A("### The trunk, and what touches it\n")
        A(_md(self.joins, 2) + "\n")
        if len(self.join_tier):
            A(_md(self.join_tier, 0) + "\n")
        A("### Does a lateral find its own way to the trunk? (the W7 test)\n")
        A(f"**{self.pct_lat_to_trunk:.2f} %** of lateral runs discharge STRAIGHT into the "
          f"trunk, against NAMA's measured **{self.nama_lat_to_trunk:.2f} %** of lateral "
          f"zones. That is the one like-for-like row below, and it is the row the target "
          f"exists for: a design where every catchment finds its own way to the trunk is "
          f"the W7 failure.\n")
        A(_md(self.into_table, 2) + "\n")
        A("The other three rows are NOT comparable, and the table says so. NAMA's 87.69 % "
          "counts DRAFTING ZONES - zone A49 holds many runs and only its exit pipe is "
          "measured - while ours counts every run. Quoting our "
          f"{self.pct_into_lat:.0f} % against their 87.69 % would be comparing two "
          "different objects, which is how a number gets retracted here.\n")
        A("### The uphill share - re-measured, NOT improved\n")
        A(_md(self.uphill, 2) + "\n")
        A("A hierarchy re-labels pipe. It does not tilt ground. The two W12 rows differ "
          "only because the setbacks and the pruning changed the denominator; the direction "
          "of every surviving arc is s2's, unchanged. **60 % of this corridor network lies "
          "on ground falling more gently than the 5.00 mm/m a DN200 may be laid at "
          "(G203-p29 Tab 11), and no tree fixes that.**\n")
        A("### Calibration PER SUB-NETWORK - the gate that a network average hides\n")
        cal, cs = self.subnet_cal, self.cal_summary
        b = cal[cal.BANDED == 1]
        A(f"**{len(cal):,} sub-networks**, of which **{len(b):,}** are at or above the "
          f"{SUBNET_MIN_KM_FOR_BAND:g} km floor the as-built band was itself measured above "
          f"(`asbuilt.A_PKG_MIN_KM_GEOM`).  The unit of comparison is NAMA's PACKAGE, and "
          f"rule T2 of `10_ASBUILT_CALIBRATION.md` says a package is one connected "
          f"component with exactly one outlet - which is what a sub-network is here.  So "
          f"the band measured BETWEEN their packages is applied sub-network by "
          f"sub-network, and the reason is in that file's own words: **\"a subnetwork with "
          f"0 % sub-main fails even if the average passes\"**.\n")
        A(_md(cs, 2) + "\n")
        A(f"**Sub-networks with no sub main at all: {int(cal.SM_ZERO.sum())}.**  That is 0 "
          f"by construction now - `tiers()` names the run that DISCHARGES a component a sub "
          f"main whatever its accumulated length, which is what \"the outlet governs\" has "
          f"always meant in this file's own docstring and what the code did not do.  With "
          f"the outfall rule multiplying the number of small sub-networks, the threshold "
          f"alone would have left many of them with no collector tier at all.\n")
        A(f"**Chain depth** - hops from a lateral run to the first non-lateral - is "
          f"published per reach as `CHAIN`.  Median across sub-networks "
          f"{float(np.median(cal.CHAIN_MED)) if len(cal) else 0:.1f}, deepest anywhere "
          f"{int(cal.CHAIN_MAX.max()) if len(cal) else 0}, against the built network's "
          f"median 2, p90 3 and absolute maximum 5.\n")
        A(f"**Lateral-zone density** is the single best structural symptom in the "
          f"calibration: above {CAL_ZONE_PER_KM_MAX:g} zones per km the main tier is "
          f"missing.  Ours is "
          f"{cal.ZONES.sum() / max(cal.KM.sum(), 1e-9):.2f}/km over the whole network "
          f"against the built 4.27.  **The definitions are NOT the same object** - NAMA's "
          f"zone is a drafting zone, ours is the set of lateral runs draining through one "
          f"lateral that discharges into a non-lateral - so this is compared as a symptom, "
          f"never quoted as a like-for-like match.  The one like-for-like row is a lateral "
          f"reaching the trunk with nothing in between, and it is in the W7 test above.\n")
        A(f"**The hierarchy ratio band is 60-78 %**, measured at "
          f"{CAL_HIER_MEASURED_PCT} % on 272 exits.  `asbuilt.py` still returns "
          f"{CAL_HIER_RETRACTED_PCT} % for the same quantity and "
          f"`10_ASBUILT_CALIBRATION.md` sec 4 retracts it by name - *\"wrong twice; use "
          f"73.2 % on 272 exits, banded 60-78 %\"*.  Both numbers are printed here rather "
          f"than one being quietly swapped for the other.\n")
        A("The 25 largest sub-networks:\n")
        A(_md(cal[["SUBNET", "KM", "TRUNK_KM", "TRUNK_PCT", "SM_PCT", "LAT_PCT",
                   "CHAIN_MED", "CHAIN_P90", "CHAIN_MAX", "ZONE_PER_KM", "HIER_PCT",
                   "V_TRUNK", "V_SM", "V_CHAIN", "V_ZONE", "V_HIER"]], 2, maxrows=25))
        A("\n\n`TRUNK_KM` is a **PROJECT APPORTIONMENT and not a measurement**: the trunk "
          "is one client input serving every sub-network, so the length is shared out by "
          "nearest join, sampled at the node-merge radius. It sums exactly to the trunk "
          "length and needs no flow direction on the Main Pipe, which this stage does not "
          "have and must not invent. Without it the per-sub-network trunk band could not "
          "be applied at all.\n")
        A("### Calibration - the sub-main threshold\n")
        A(_md(self.sweep_submain, 2) + "\n")
        A("### Calibration - the lateral budget\n")
        A(_md(self.sweep_budget, 1) + "\n")
        if len(self.island_report):
            A("### The islands s2 could not place\n")
            A(_md(self.island_report.drop(columns=["OUTFALL_KIND"]), 2) + "\n")
            A("Each is given a LOCAL outfall at its own lowest node so that no component "
              "drains nowhere (H15). Whether that becomes a pumping station or a satellite "
              "works is stage 7's question and the options appraisal's, not this one's.\n")
        A("### Exceptions\n")
        A(_md(exc, 0) + "\n")
        A("### Every constant, with where it came from\n")
        A(_md(self.manifest(), 4) + "\n")
        return "\n".join(L)

    # ---------------------------------------------------------------- run it
    def build(self):
        (self.load().fix_islands().one_pipe_leaves().gates().set_heads().mint_nodes()
         .build_forest().build_runs().label_subnets())
        self.calibrate()
        self.apply_tiers().subnet_calibration().measure().sweep().publish()
        os.makedirs(RUN, exist_ok=True)
        with open(REPORT_MD, "w", encoding="utf-8") as fh:
            fh.write(self.report())
        man = self.manifest()
        with open(MANIFEST_JSON, "w", encoding="utf-8") as fh:
            json.dump({r.ITEM: r.VALUE for r in man.itertuples()}, fh, indent=1, default=str)
        self.kmz()
        return self

    def calibrate(self):
        """Pick SUBMAIN_KM by the built network's own sub-main share, not by taste.

        The band is the SPREAD BETWEEN NAMA'S OWN PACKAGES and it is wide - 5A-1 built no
        sub-main tier at all.  So the target is the band's midpoint and the whole sweep is
        published: a reader who prefers a different threshold re-grades the layer with one
        query on SUB_KM."""
        keep = self.keep
        km_main = float(self.main_pipe.geometry.length.sum() / 1000.0)
        km_all = float(self.len_out[keep].sum() / 1000.0) + km_main
        tgt = AB.AsBuilt().targets()["tier_share_submain_pct"]
        # AIM AT THE MEASURED VALUE, not at the middle of the band.  The band is the SPREAD
        # BETWEEN NAMA'S OWN PACKAGES - 5A-1 built no sub-main tier at all - so its midpoint
        # is an artefact of which packages happen to exist.  The value is the measurement.
        aim = float(tgt.value)
        best, bestd = self.submain_km, 1e9
        for sk in SUBMAIN_SWEEP:
            t = self.tiers(submain_km=sk)
            at = np.array([""] * len(self.arcs), dtype=object)
            at[keep] = t[self.run_id[keep]]
            pct = 100.0 * float(self.len_out[keep & (at == "sub main")].sum()
                                / 1000.0) / km_all
            d = abs(pct - aim)
            if d < bestd:
                best, bestd = sk, d
        self.submain_km = best
        self.submain_aim = aim
        if self.verbose:
            _log(f"calibrated SUBMAIN_KM = {best:g} km  (built band "
                 f"{tgt.lo:.2f}-{tgt.hi:.2f} %, aim {aim:.2f} %)")
        return self

    def kmz(self):
        """Google Earth, on `present.py`'s own `tier` view.

        Worth the twenty lines: present.py folds by TIER and counts the length in each
        folder itself, so its numbers are an INDEPENDENT recount of the table above rather
        than a picture of it."""
        try:
            import geopandas as gpd
            from w12 import present as P
            d = gpd.read_file(OUT_GPKG, layer="reaches")
            tr = gpd.read_file(OUT_GPKG, layer="trunk")
            tr = tr.assign(EDGE_UID=[f"T{i:04d}" for i in range(len(tr))],
                           US_NODE="", DS_NODE="", RUN_ID="", SUBNET="TRUNK")
            d = gpd.GeoDataFrame(pd.concat([d, tr], ignore_index=True),
                                 crs=d.crs)
            out = os.path.join(W12, "shp", "W12_hier_tier.kmz")
            r = P.kmz(d, P.VIEWS["tier"], out, source=f"{STAGE_VERSION}  {TAU_FLAG}")
            if self.verbose:
                _log(f"KMZ {out}: {r.summary()}")
        except Exception as e:                                   # noqa: BLE001
            _log(f"KMZ skipped: {type(e).__name__}: {e}")
        return self


# ==========================================================================================
# 3.  VERIFY - re-derive every headline FROM THE PUBLISHED LAYERS
# ==========================================================================================

def verify() -> dict:
    """Reads the GeoPackage back and recomputes the claims without touching the build code.

    Philosophy sec 8: the audit reads PUBLISHED layers, never an in-memory model."""
    import geopandas as gpd
    r = gpd.read_file(OUT_GPKG, layer="reaches")
    n = gpd.read_file(OUT_GPKG, layer="nodes")
    tr = gpd.read_file(OUT_GPKG, layer="trunk")
    man = gpd.read_file(OUT_GPKG, layer="manifest")
    mv = dict(zip(man.ITEM, man.VALUE))

    out = {}
    # 1. the hard rule, recomputed from US_NODE alone
    vc = r.US_NODE.value_counts()
    out["nodes_with_two_outlets"] = int((vc > 1).sum())

    # 2. forest: no cycles, every component ends at one outfall
    nxt = dict(zip(r.US_NODE, r.DS_NODE))
    roots = {}
    for s in r.US_NODE:
        cur, hops = s, 0
        while cur in nxt and hops <= len(r) + 5:
            cur = nxt[cur]
            hops += 1
        roots[s] = cur
        if hops > len(r):
            out["cycle_from"] = s
    out["components"] = len(set(roots.values()))

    # 3. lengths
    out["km_corridors"] = float(r.LEN_M.sum() / 1000.0)
    out["km_geometry"] = float(r.geometry.length.sum() / 1000.0)
    out["len_field_vs_geometry_max_m"] = float((r.LEN_M - r.geometry.length).abs().max())
    out["km_trunk"] = float(tr.geometry.length.sum() / 1000.0)

    # 4. tiers, recounted off the geometry not the field
    km = r.groupby("TIER").apply(lambda d: d.geometry.length.sum() / 1000.0)
    km_all = float(km.sum()) + out["km_trunk"]
    for t, v in km.items():
        out[f"pct_{t.replace(' ', '_')}"] = 100.0 * float(v) / km_all
    out["pct_trunk_main"] = 100.0 * out["km_trunk"] / km_all

    # 5. heads really are detached, and the setback really is at least 10 m
    hd = r[(r.IS_HEAD == 1) & (r.HEAD_BY.isin(["gate_clear", "clearance"]))]
    out["detached_heads"] = int(len(hd))
    out["min_setback_m"] = float(hd.SETBACK_M.min()) if len(hd) else float("nan")
    out["heads_starting_at_a_gate"] = int((r.HEAD_BY.isin(["gate", "gate_clear"])).sum())

    # 6. every head node has nothing upstream, every junction has 2+, on the NODE layer
    out["head_nodes_with_inflow"] = int(((n.KIND == "head") & (n.N_IN > 0)).sum())
    out["outfalls"] = int((n.KIND == "outfall").sum())
    out["nodes"] = int(len(n))

    # 7. tier monotone downstream
    tier_of = dict(zip(r.US_NODE, r.TIER))
    rank = {"lateral": 0, "main": 1, "sub main": 2, "trunk main": 3}
    inv = 0
    for _, row in r.iterrows():
        d = tier_of.get(row.DS_NODE)
        if d is not None and rank[d] < rank[row.TIER]:
            inv += 1
    out["tier_inversions"] = inv

    # 8. THE PER-SUB-NETWORK CALIBRATION, re-derived from the published columns.
    #    A check that cannot run is a FAILURE, not a blank (inheritance row 2), so the
    #    absence of a SUBNET column is reported as such rather than skipped.
    if "SUBNET" not in r.columns:
        out["subnet_check"] = "CANNOT RUN - the reaches layer has no SUBNET column"
        out["reaches_without_a_subnet"] = -1
        out["subnets_with_no_submain"] = -1
    else:
        s = r.SUBNET.astype(str).str.strip()
        out["reaches_without_a_subnet"] = int((s.eq("") | s.eq("nan")).sum())
        out["subnets"] = int(s[~(s.eq("") | s.eq("nan"))].nunique())
        # "a subnetwork with 0 % sub-main FAILS even if the average passes"
        has_sm = r[r.TIER == "sub main"].SUBNET.astype(str).unique()
        out["subnets_with_no_submain"] = int(
            len(set(s[~(s.eq("") | s.eq("nan"))]) - set(has_sm)))
    if "CHAIN" not in r.columns:
        out["chain_check"] = "CANNOT RUN - the reaches layer has no CHAIN column"
        out["chain_max"] = -1
    else:
        lat = r[r.TIER == "lateral"]
        out["chain_max"] = int(lat.CHAIN.max()) if len(lat) else 0
        out["chain_over_absolute"] = int((lat.CHAIN > CAL_CHAIN_ABS_MAX).sum())

    # 9. against the manifest
    out["manifest_km_corridors"] = float(mv.get("km_corridors", float("nan")))
    out["agrees_with_manifest"] = bool(
        abs(out["km_corridors"] - out["manifest_km_corridors"]) < 0.05)
    return out


# ==========================================================================================
# 4.  SELFTEST - the rules proved on graphs whose answers are known by hand
# ==========================================================================================

def selftest(verbose: bool = True) -> bool:
    ok = True

    def chk(cond, what):
        nonlocal ok
        ok = ok and bool(cond)
        if verbose:
            print(f"  [{'ok ' if cond else 'FAIL'}] {what}")

    # --- primitives -----------------------------------------------------------------------
    #   0 -> 1 -> 2 (root),  3 -> 1
    U = np.array([0, 1, 3])
    V = np.array([1, 2, 1])
    keep = np.ones(3, dtype=bool)
    oa = out_arc_of(4, U, keep)
    chk(list(oa) == [0, 1, -1, 2], "out_arc_of finds one outlet per node")
    order = topo_order(oa, V, 4)
    chk(len(order) == 4 and list(order).index(2) > list(order).index(1),
        "topo_order puts a node after its upstream")
    acc = accumulate(order, oa, V, np.array([1.0, 1.0, 1.0, 1.0]))
    chk(acc[2] == 4.0 and acc[1] == 3.0, "accumulate sums the whole subtree")
    lp = longest_path(order, oa, V, np.array([10.0, 5.0, 100.0]))
    chk(lp[2] == 105.0, "longest_path takes the longest branch, not the sum")

    # two outlets must RAISE, not be silently repaired
    try:
        out_arc_of(3, np.array([0, 0]), np.ones(2, dtype=bool))
        chk(False, "out_arc_of raises on two outlets")
    except AssertionError:
        chk(True, "out_arc_of raises on two outlets")

    # --- the tier rule on a hand-built run tree --------------------------------------------
    h = Hier.__new__(Hier)
    h.submain_km, h.budget_runs, h.budget_path_m = 2.0, 3, 750.0
    h.n_runs = 6
    #  r0 -> r1 -> r2 -> r3 -> r4 -> r5(outfall)
    h.run_next = np.array([1, 2, 3, 4, 5, -1])
    h.run_len = np.array([100.0, 100.0, 100.0, 400.0, 400.0, 400.0])
    h.run_sub_km = np.array([0.1, 0.2, 0.3, 0.7, 1.1, 1.5])
    h.run_depth = np.array([1, 2, 3, 4, 5, 6], dtype=float)
    h.run_path_m = np.array([0, 100, 200, 300, 700, 1100], dtype=float)
    t = h.tiers()
    chk(list(t[:3]) == ["lateral"] * 3, "first three runs are laterals (budget 3)")
    chk(t[3] == "main", "the fourth run is a main - the run budget is spent")
    chk(t[5] == "sub main",
        "THE OUTLET GOVERNS: the run that discharges a component is a sub main whatever "
        "its accumulated length")

    # the path budget, on a tree where NOTHING else could have promoted the run - so the
    # outlet clause cannot be what did it
    hp = Hier.__new__(Hier)
    hp.submain_km, hp.budget_runs, hp.budget_path_m = 99.0, 99, 750.0
    hp.n_runs = 3
    hp.run_next = np.array([1, 2, -1])
    hp.run_sub_km = np.array([0.1, 0.2, 0.3])
    hp.run_depth = np.array([1, 2, 3], dtype=float)
    hp.run_path_m = np.array([0.0, 800.0, 900.0])
    tp = hp.tiers()
    chk(tp[0] == "lateral" and tp[1] == "main",
        "the path budget alone promotes a mid-tree run to main")
    chk(tp[2] == "sub main", "and the outlet is a sub main regardless")

    # A SUB-NETWORK SMALLER THAN SUBMAIN_KM STILL GETS A SUB MAIN.  The outfall rule
    # multiplies the number of small sub-networks, and 10_ASBUILT_CALIBRATION sec 1 is
    # explicit: "a subnetwork with 0 % sub-main fails even if the average passes".
    hs = Hier.__new__(Hier)
    hs.submain_km, hs.budget_runs, hs.budget_path_m = 2.0, 3, 750.0
    hs.n_runs = 2
    hs.run_next = np.array([1, -1])
    hs.run_sub_km = np.array([0.05, 0.12])         # 120 m of network, against a 2 km rule
    hs.run_depth = np.array([1, 2], dtype=float)
    hs.run_path_m = np.array([0.0, 60.0])
    ts = hs.tiers()
    chk(ts[1] == "sub main",
        "a sub-network far under SUBMAIN_KM still has a collector tier")

    t2 = h.tiers(submain_km=1.0)
    chk(t2[4] == "sub main" and t2[5] == "sub main",
        "a lower threshold promotes the collector to sub main")
    rank = {"lateral": 0, "main": 1, "sub main": 2, "trunk main": 3}
    chk(all(rank[t2[h.run_next[i]]] >= rank[t2[i]] for i in range(5)),
        "the tier is monotone downstream - a lateral never receives a main")

    # --- the head setback rule --------------------------------------------------------------
    g = Hier.__new__(Hier)
    g.gate_start = {0: (0, 3), 1: (3, 4)}
    g.gate_along = np.array([4.0, 18.0, 40.0, 2.0])
    g.gate_q = np.array([1.0, 2.0, 3.0, 9.0])
    d, sq, sn = g._first_gate(0, FANOUT_OFFSET_M)
    chk(d == 18.0 and sq == 1.0 and sn == 1,
        "the setback is the first gate AT OR BEYOND 10 m, and the gate inside it is counted")
    d, sq, sn = g._first_gate(0, 0.0)
    chk(d == 4.0 and sn == 0, "with no chamber to clear, the head starts at the first gate")
    d, sq, sn = g._first_gate(1, FANOUT_OFFSET_M)
    chk(not np.isfinite(d) and sq == 9.0,
        "a corridor whose only gate is inside the clearance reports no gate and strands it")
    d, _, _ = g._first_gate(7, 0.0)
    chk(not np.isfinite(d), "a corridor with no plot at all has no gate")

    # --- a synthetic network end to end, with the answer known by hand ---------------------
    #  A junction J with one downhill outlet and three other streets.  The hard rule says
    #  ONE leaves; the other two become heads.
    n = 6
    U = np.array([0, 0, 0, 1, 2])       # three arcs leave node 0
    V = np.array([1, 2, 3, 4, 5])
    tree = np.array([True, False, False, True, True])
    keep = tree.copy()
    keep[1] = keep[2] = True            # heads are kept, just detached
    Uo = U.copy()
    Uo[1], Uo[2] = 6, 7                 # detached onto minted head nodes
    oa = out_arc_of(8, Uo, keep)
    chk(int((np.bincount(Uo[keep], minlength=8) > 1).sum()) == 0,
        "after the setback no node has two outgoing pipes")
    chk(len(topo_order(oa, V, 8)) == 8, "the result is a forest")

    if verbose:
        print(f"\nselftest: {'PASS' if ok else 'FAIL'}")
    return ok


# ==========================================================================================
# 5.  CLI
# ==========================================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "build"

    if cmd == "selftest":
        return 0 if selftest() else 1

    if cmd == "verify":
        v = verify()
        w = max(len(k) for k in v)
        for k, val in v.items():
            print(f"  {k.ljust(w)}  {val}")
        bad = (v["nodes_with_two_outlets"] or v["tier_inversions"]
               or v["head_nodes_with_inflow"] or not v["agrees_with_manifest"])
        print(f"\nverify: {'FAIL' if bad else 'PASS'}")
        return 1 if bad else 0

    if cmd == "sweep":
        h = (Hier().load().fix_islands().one_pipe_leaves().gates().set_heads()
             .mint_nodes().build_forest().build_runs())
        h.calibrate()
        h.apply_tiers().measure().sweep()
        print("\nSUB-MAIN THRESHOLD\n" + _md(h.sweep_submain, 2))
        print("\nLATERAL BUDGET\n" + _md(h.sweep_budget, 1))
        return 0

    if cmd != "build":
        print(__doc__)
        return 2

    t0 = time.time()
    if not selftest(verbose=False):
        _log("SELFTEST FAILED - refusing to build")
        return 1
    h = Hier().build()
    exc = h.exceptions()
    n_exc = len(exc) if exc.iloc[0].KIND else 0
    _log(f"published {OUT_GPKG}")
    _log(f"report    {REPORT_MD}")
    _log(f"EXCEPTIONS TO THE HARD RULE: {n_exc}")
    _log(f"done in {time.time() - t0:.1f} s")
    return 0 if n_exc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
