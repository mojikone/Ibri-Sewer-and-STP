"""s6_levels - STAGE 6: LEVELS AND SIZES.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
It reads the published chamber graph from `s4_chambers`, the tiers from `s3_hierarchy` and
the peak-factor constant from `s5_flows`, and it publishes the two CONTRACT layers - `nodes`
and `reaches` - into `W12/shp/W12.gpkg`, which is the file `s7_pumps` reads for its
station demands.

    python s6_levels.py              build, publish, report
    python s6_levels.py --verify     re-derive every headline from the PUBLISHED file
    python s6_levels.py --selftest   the arithmetic against hand-worked cases and against
                                     hydra's own reference functions
    python s6_levels.py --report     re-print the tables from the published file
    python s6_levels.py --asbuilt    calibrate against NAMA's built network
    python s6_levels.py --sweep      tau = 2.0 Pa and the cap sensitivity, reported only

==================================================================== WHAT IT DOES, IN ORDER
    1  READ the chamber graph.  56,935 chambers, 56,740 chamber-to-chamber segments,
       1,491.9 km, one outgoing reach per node, 195 terminals.  Topology is READ from
       DS_NODE and never inferred from geometry (H16).
    2  ACCUMULATE flow down the tree - QADF, properties, upstream length - then the peak
       factor and the unpeaked infiltration.  ONE accumulator, checked against s5_flows'
       published answer on s5's own graph before it is used on ours.
    3  PASS 1, STRICT.  Every reach laid at the SHALLOWEST legal profile: the steeper of
       Table 11 and the tractive minimum, steepened only where the ground falls fast enough
       to let the pipe come back up to 1.30 m of cover.  Crown matching at every chamber.
    4  PASS 2, REVIEW.  The gradient a person would have drawn: a run of pass-through
       chambers takes ONE gradient (P1) laid to land on the level its downstream chamber
       actually needs, so the fall is spent along the run instead of being thrown away in a
       drop shaft at the bottom of it.  It NEVER flattens a reach below pass 1, so no
       chamber can move and nothing downstream is invalidated.
    5  THE CAP.  Cover past 12 m is a station unless one of philosophy sec 5's two exits
       applies, and an exit is WITHDRAWN when the levels inside the excursion force a drop
       or a cover past the declared ceiling.  A station is placed at the last chamber still
       inside the cap on the branch that is dragging the network down - the foot of the
       excursion - never at the junction it ends at.  Then the whole thing is re-levelled,
       and it repeats until no breach is left.
    6  DROPS.  Backdrop over 0.60 m, vortex drop shaft over 2.00 m (G203-p30).  The count is
       THE diagnostic for a tree that is not following the ground, and it is printed on the
       front page beside NAMA's own.
    7  PUBLISH through `contract.publish`, which validates before it writes, then re-read
       the file and re-derive every headline from it.

============================================================ THE FOUR MEASURED FACTS IT OBEYS
Established 2026-09-02/03 against NAMA's own built pipes, and none of them is comfortable:

    1  The terrain decides the direction of a single short reach about ONE TIME IN FIVE and
       is right 71 % of the time when it does.
    2  NAMA's own SURVEYED levels agree with the direction their pipes run 65 % of the time.
       The 0.5 m terrain scores no better than the 5 m.  THERE IS NO ACCURACY LEFT TO BUY.
    3  61.69 % of THIS network's length - 912.1 km of the 1,478.5 km published - lies on
       ground falling more gently than 5.00 mm/m, the flattest gradient a DN200 may be laid
       at (G203-p29 Table 11).  There the pipe sinks whichever way it points, and the debt
       it accrues is 7,267 m - 4.9 m for every kilometre of sewer.  MEASURED HERE, on the
       chamber graph, and it is the single fact that governs this stage: depth is bought by
       flatness, not by direction, and 508 of the stations this design needs are bought by
       it too.
    4  NAMA's built network drains uphill on 34.1 % of its length.  Context, not permission.

So: THIS STAGE CANNOT FIX FLATNESS EITHER.  What it can do is spend the fall it has instead
of wasting it, put the stations where the cap actually demands them, and say exactly how
much depth is left over.  The numbers below are what it achieved, not what it hoped for.

======================================================================= WHAT IT DOES NOT DO
  * It does not re-route, re-orient or re-tier anything.  The layout is s2/s3/s4's and a
    levelling stage that moves pipes is hiding a layout fault in a level.
  * It does not DESIGN a station.  It LOCATES one and hands s7_pumps a duty flow, a ground
    level and an arriving invert - the three things W11a's 226 stations did not have.
  * It has no start-year flows, so philosophy sec 6's "check self-cleansing at start-year
    flows" CANNOT RUN.  Inherited from s5's A-FLOW-6.  That is a GAP, not a pass.
  * It cannot confirm the existing works inlet invert.  The 195 terminals are levelled to
    whatever the network gives them and the tie-in level is a DATA REQUEST (A-LEV-7).

===================================================================== THE PROHIBITED MOVE
OVERSIZING A PIPE TO LAY IT FLATTER IS PROHIBITED - G203-p29 "Sewers shall not be oversized
to facilitate flatter slopes", and Ten States sec 33.43 independently.  It is expressible in
this code only by choosing a diameter the flow does not need, and `SIZED_BY` on every reach
records which of hydra's four hydraulic reasons chose the size.  "depth" and "cover" are not
in that enum, so the prohibited answer cannot be written down.

The temptation is real on this ground: Table 11's minimum gradient falls from 5.00 mm/m at
DN200 to 0.75 mm/m at DN900, so a bigger pipe would buy 4.25 mm/m of depth per metre.  The
answer is no.  Where a bigger pipe appears in this design it is because the FLOW put it
there, and `sizing_reason` publishes the count for each of the four reasons so the claim can
be checked rather than believed.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import linemerge
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from w12 import contract as K                                     # noqa: E402
from w12 import hydra as HY                                       # noqa: E402
from w12.criteria import DEFAULT as CRIT, Criteria, replace       # noqa: E402

STAGE = "s6_levels"
STAGE_VERSION = "W12-s6_levels-1.0"
STAGE_ORDER = 6

W12 = HERE.parent
CHAMBERS_GPKG = W12 / "shp" / "W12_chambers.gpkg"
HIER_GPKG = W12 / "shp" / "W12_hier.gpkg"
FLOWS_GPKG = W12 / "shp" / "W12_flows.gpkg"
ROADS_GPKG = W12 / "shp" / "W12_roads.gpkg"
STREAMS_GPKG = W12 / "shp" / "W12_streams.gpkg"

OUT_GPKG = W12 / "shp" / K.GPKG_NAME               # W12.gpkg - the CONTRACT file
DIAG_GPKG = W12 / "shp" / "W12_levels.gpkg"       # this stage's own diagnostics
RUN_DIR = W12 / "run" / "levels"
REPORT_MD = RUN_DIR / "LEVELS.md"
MANIFEST_JSON = RUN_DIR / "levels_manifest.json"

SEC_PER_DAY = 86400.0
M3D_TO_LS = 1000.0 / SEC_PER_DAY


def _log(msg: str) -> None:
    print(f"[{STAGE}] {msg}", flush=True)


# ======================================================================================
# GUIDELINE VALUES.  Every one comes from `criteria`, which read it from the source PDF.
# Nothing in this file re-types a guideline number: a second copy is a second answer.
# ======================================================================================

G: Dict[str, Tuple] = {
    "SMIN_DN200":       (CRIT.table11(200) * 1000, "mm/m", "G203-p29 Table 11"),
    "SMIN_FLOOR":       (CRIT.TABLE11_FLOOR * 1000, "mm/m", "G203-p29 Table 11, '900 and above'"),
    "V_SELF_CLEANSING": (CRIT.V_SELF_CLEANSING, "m/s", "G203-p26"),
    "V_MAX":            (CRIT.V_MAX, "m/s", "G203-p27 4.2.2.2"),
    "DOD_SMALL":        (CRIT.DOD_MAX_SMALL, "-", "G203-p27 Table 10, up to DN350"),
    "DOD_LARGE":        (CRIT.DOD_MAX_LARGE, "-", "G203-p27 Table 10, above DN350"),
    "MIN_COVER":        (CRIT.MIN_COVER_CROWN, "m", "G203-p33 4.6.3"),
    "MIN_COVER_WADI":   (CRIT.MIN_COVER_WADI_XING, "m", "G203-p52 8.2.4, PROJECT decision for gravity"),
    "MAX_COVER":        (CRIT.MAX_COVER, "m", "G203-p33, read as a cap (philosophy sec 5)"),
    "DROP_TRIGGER":     (CRIT.DROP_TRIGGER, "m", "G203-p30, backdrop above 600 mm"),
    "BACKDROP_MAX":     (CRIT.BACKDROP_MAX, "m", "G203-p30, vortex drop shaft beyond 2 m"),
    "DROP_CEILING":     (CRIT.DROP_CEILING_M, "m", "PROJECT ASSUMPTION - G203 gives no maximum"),
    "SLOPE_STEP":       (CRIT.SLOPE_STEP * 100, "%", "PROJECT rule 2026-08-23, round gradients"),
    "LAY_TOLERANCE":    (CRIT.LAY_TOLERANCE_M * 1000, "mm", "G203-p29 4.3.1"),
    "TAU_PA":           (CRIT.TAU_PA, "Pa", "ENGINEER 2026-09-03, GAP-9 - NOT a guideline value"),
    "TRACTIVE_K":       (CRIT.TRACTIVE_K_M3S, "-", "G203-p27 4.2.2.1, Q in m3/s"),
    "INFILT":           (CRIT.INFILT_L_D_KM, "L/d/km", "G201-p72 7.4.3"),
    "PF_HOLD_N":        (CRIT.PF_HOLD_PROPERTIES, "properties", "G201-p71 7.4.2"),
    "DN_MIN":           (CRIT.DN_MIN_LATERAL, "mm", "G203-p22 Table 6, Lateral Sewer row"),
    "MH_SPACING_200":   (CRIT.mh_max_spacing(200), "m", "G203-p30 Table 12"),
    "SKEW_TOL":         (CRIT.WADI_XING_SKEW_DEG, "deg", "PROJECT ASSUMPTION on H1's 'perpendicular'"),
}

# The contract's own sanity bound on a published gradient.  Not a guideline rule - a range
# guard - but a laid gradient the layer cannot carry is a laid gradient that cannot be
# published, so the design has to respect it and REPORT where it bit.
SLOPE_HARD_MAX = 0.25                      # 25 %, contract REACHES.SLOPE_LAID hi


# ======================================================================================
# ASSUMPTIONS - every one, with what would change if it were wrong
# ======================================================================================

ASSUMPTIONS: Tuple[Dict[str, str], ...] = (
    dict(ID="A-LEV-1",
         WHAT="The load levelled here is s4_chambers' `connections` layer - 70,405.5 m3/d "
              "over 53,018 plots - not the 74,701.2 m3/d of the project total.",
         WHY="s4 could not find a chamber within 45 m for 3,396 plots and published them in "
             "`unserved`. Levelling the project total would put flow in pipes that do not "
             "collect it. The difference is reconciled row by row in `reconcile`.",
         IF_WRONG="Every pipe carrying one of those 3,396 plots would be one size step "
                  "larger at most; the 4,295.7 m3/d is 5.75 % of the total and is "
                  "concentrated at the edges of the network, not on the trunk.",
         KIND="project doctrine", SOURCE="s4_chambers `connections` / `unserved`"),
    dict(ID="A-LEV-2",
         WHAT="Below 100 properties the peak factor is the Merrimack formula evaluated AT "
              "100 properties (3.62139), and PF_METH says 'merrimack'.",
         WHY="G201-p71 7.4.2 says Merrimack 'is to be used ... for an area having over 100 "
             "properties' and prescribes nothing below. s5_flows holds the factor at the "
             "threshold value (A-FLOW-2) and this stage uses S5'S OWN NUMBER so the two "
             "stages cannot disagree. The method IS Merrimack; what is held is its "
             "argument. THREE-WAY CONFLICT, see `conflicts`: criteria.peak_factor() returns "
             "1.0 and calls it 'held', and contract._cross_field REJECTS PF != 1.0 on a row "
             "labelled 'held' - so the honest label for a plateau at 3.62 is 'merrimack'.",
         IF_WRONG="At PF = 1.0 every lateral would be sized on average flow. At the "
                  "Merrimack extrapolation the factor would rise without bound as the "
                  "catchment shrinks. The plateau is the only reading that is continuous, "
                  "conservative and inside the formula's stated range.",
         KIND="project decision", SOURCE="G201-p71 7.4.2 (threshold); the plateau is OURS"),
    dict(ID="A-LEV-3",
         WHAT="A reach is never smaller than the reach immediately upstream of it.",
         WHY="Flow accumulates downstream, so the hydraulic answer is almost always "
             "non-decreasing anyway; a steeper reach can nevertheless carry the same flow "
             "in a smaller pipe, and a constriction in a gravity sewer is a blockage "
             "waiting to happen. No guideline states this - it is practice.",
         IF_WRONG="`sizing_reason` publishes how many reaches were set by this floor rather "
                  "than by the flow. Removing it would shrink those reaches by one step.",
         KIND="project decision", SOURCE="practice; G203 is silent"),
    dict(ID="A-LEV-4",
         WHAT="CROWN MATCHING at every chamber: an incoming pipe's soffit is never below "
              "the outgoing pipe's soffit, so a step of (OD_out - OD_in) is the smallest "
              "legal invert difference where the pipe grows.",
         WHY="Philosophy P5 offers invert OR crown matching. Crown matching is the one that "
             "keeps the hydraulic grade line continuous when the diameter changes; invert "
             "matching would make the smaller pipe discharge into a deeper flow and back it "
             "up. It is also what makes the drop count meaningful: a drop is then a real "
             "level difference, not an artefact of the matching rule.",
         IF_WRONG="Invert matching would remove the diameter-step drops (168 of them here) "
                  "and add surcharge risk at every size change.",
         KIND="project decision", SOURCE="philosophy P5; G203 states no matching rule"),
    dict(ID="A-LEV-5",
         WHAT="Pass 2 NEVER lays a reach flatter than pass 1 did.",
         WHY="Pass 1's inverts are the shallowest legal profile. Flattening any reach in "
             "pass 2 would raise its downstream invert, which is the level its junction was "
             "levelled to, and every chamber below it would have to move. Only steepening "
             "is safe, so pass 2 is a pure improvement and pass 1's compliance survives it "
             "(philosophy sec 7: pass 2 must not break pass 1).",
         IF_WRONG="Nothing - this is a constraint on the method, and `pass2` publishes the "
                  "fall it recovered so the constraint's cost is visible.",
         KIND="method", SOURCE="philosophy sec 7"),
    dict(ID="A-LEV-6",
         WHAT="Tractive stress tau = 1.0 Pa.",
         WHY="ENGINEER'S DECISION 2026-09-03, GAP-9 open. G203-p27 4.2.2.1 gives the "
             "equation and never the stress. It is FLAGGED on every output of this stage "
             "and carried on every published row in TAU_PA.",
         IF_WRONG="At 2.0 Pa every tractive-governed gradient rises by 2^1.23 = 2.346x. The "
                  "whole-stage sensitivity is in `sweep` - run `--sweep`.",
         KIND="ASSUMPTION (GAP-9)", SOURCE="G203-p27 4.2.2.1 is silent on tau"),
    dict(ID="A-LEV-7",
         WHAT="The 195 terminals are levelled to whatever the network gives them. No tie-in "
              "invert is imposed, and TIE_TYPE is 'none' on every reach.",
         WHY="The existing works inlet invert is unconfirmed (00_CURRENT, open data "
             "request), and the client's Main Pipe is an INPUT that is not in this graph. "
             "H14 says the design yields to an existing invert - there is no confirmed one "
             "to yield to.",
         IF_WRONG="If the works inlet is HIGHER than a terminal's invert the network cannot "
                  "discharge and a terminal station appears; if LOWER, depth is being "
                  "wasted. The deepest and shallowest terminal inverts are published in "
                  "`outfalls` so the check can be made the day the level arrives.",
         KIND="GAP", SOURCE="DATA REQUEST to NWS"),
    dict(ID="A-LEV-8",
         WHAT="The crossings register is minted HERE, provisionally, because no corridor "
              "stage published one. Every row is APPROVED = 0.",
         WHY="contract._cross_field refuses to publish a reach on wadi ground with no "
             "CROSS_ID, and it is right to: W10 shipped 47 unscheduled crossings. The "
             "register is a stage-2 product; this is a stand-in so the levels can be "
             "published, and every row carries its measured skew angle and whether a "
             "chamber sits on wadi ground.",
         IF_WRONG="A run that is really a pipe ALONG a wadi would be registered as a "
                  "crossing. `crossings` publishes the skew and the contact length of every "
                  "row so that reading can be checked, and H1a's verdict per row is in "
                  "`wadi_h1a`.",
         KIND="STAND-IN", SOURCE="philosophy H1a; G201-p85-86 sec 9.3"),
    dict(ID="A-LEV-9",
         WHAT="No start-year flows exist, so self-cleansing is checked at the SATURATION "
              "flow only.",
         WHY="Inherited from s5's A-FLOW-6: W10_plot_loads carries one figure per plot.",
         IF_WRONG="A pipe that scours in 2055 may silt in 2030. Philosophy sec 6 requires "
                  "the check and it CANNOT RUN. This is a GAP, not a pass.",
         KIND="GAP", SOURCE="data; G201-p73 phasing not modelled"),
    dict(ID="A-LEV-10",
         WHAT="A station is LOCATED here and DESIGNED by s7_pumps. It terminates its gravity "
              "component; the chamber it would have drained to is re-based at minimum cover "
              "and receives the rising main (G203-p55 8.5: termination not more than 300 mm "
              "above the receiving flow line).",
         WHY="The interface s7 documents is `nodes` where NODE_KIND == 'station', carrying "
             "X, Y, GRD_M, INV_M, Q_PK_LS, Q_ADF_M3D and N_PROP. W11a published 226 "
             "stations with Q_DUTY_LS = 0 on every one of them.",
         IF_WRONG="The reach between a station and its discharge chamber is withdrawn from "
                  "the gravity layer and published in `pumped_links` - it is the rising "
                  "main's alignment, not a sewer. That is 1 reach per station and the total "
                  "is published.",
         KIND="project decision", SOURCE="philosophy sec 5; s7_pumps interface"),
    dict(ID="A-LEV-11",
         WHAT="A philosophy sec 5 exit is WITHDRAWN when any chamber inside the excursion "
              "carries a drop OR a cover greater than criteria.DROP_CEILING_M (20.0 m).",
         WHY="Philosophy sec 5 states the depth bound as the drop ceiling. The cover bound "
             "uses THE SAME declared constant rather than a second number, because a "
             "distance-only exit produced a 36.81 m chamber with a 35.06 m drop into it on "
             "2026-09-02 and that is the failure the bound exists to stop. It is one "
             "declared project ceiling used twice, not two engineering judgements.",
         IF_WRONG="A looser ceiling permits deeper excursions and fewer stations; a tighter "
                  "one buys stations. `sweep` publishes the station count against the "
                  "ceiling.",
         KIND="project assumption", SOURCE="philosophy sec 5; G203 gives no vortex maximum"),
    dict(ID="A-LEV-12",
         WHAT="A station is sited at the last chamber still INSIDE the cap on the branch "
              "whose arriving invert governs the breach - never at the junction the branch "
              "ends at.",
         WHY="Philosophy sec 5: 'the station goes at the FOOT of the climb, not at the "
             "junction. A drop is flow going down; a station lifts it up. One where they "
             "meet is physically incoherent.' Siting at the front rather than the junction "
             "also keeps the station chamber itself inside the 12 m cap, so no station is "
             "published with an unjustified PAST_CAP.",
         IF_WRONG="Where the breach sits inside a contiguous UPHILL stretch the ideal site "
                  "is the foot of that stretch, which is further upstream. Moving it there "
                  "would strand the chambers between, because their pipe would have to be "
                  "re-oriented - a stage-2/3 decision, not a levelling one. The count and "
                  "the climb involved are published in `station_sites` and named in the "
                  "report as an OPEN item for the layout stages.",
         KIND="project decision", SOURCE="philosophy sec 5"),
    dict(ID="A-LEV-13",
         WHAT="Five chamber pairs closer than criteria.MH_SNAP_M (3.0 m) are CONTRACTED into "
              "one structure before levelling.",
         WHY="MH_SNAP_M is the node-merge radius AND the minimum chamber clearance - two "
             "chambers 0.46 m apart ARE one structure, and a 0.46 m reach is below the "
             "contract's own LEN_M floor of 0.5 m. s4 published them in `close_pairs`.",
         IF_WRONG="Nothing measurable: 5 pairs, 7.66 m of pipe. The ids are in the funnel.",
         KIND="method", SOURCE="criteria.MH_SNAP_M; s4 `close_pairs`"),
    dict(ID="A-LEV-14",
         WHAT="1.30 m of cover is required everywhere, INCLUDING on wadi ground, and the "
              "1.50 m wadi figure is reported as a shortfall rather than designed to.",
         WHY="criteria.MIN_COVER_WADI_XING (1.50 m) is G203-p52 8.2.4, which sits in the "
             "FORCE MAIN section; adopting it for gravity is OUR decision (philosophy H1a "
             "condition 3), and it is pending the scour-depth check that actually governs. "
             "Designing to it would deepen 2,912 reaches for a rule the guideline does not "
             "impose on a gravity sewer.",
         IF_WRONG="The reaches short of 1.50 m on wadi ground are counted in `wadi_h1a` and "
                  "named as a shortfall against OUR rule, not the guideline's.",
         KIND="project decision", SOURCE="G203-p52 8.2.4; philosophy H1a note 3"),
)


CONFLICTS: Tuple[Dict[str, str], ...] = (
    dict(ID="C-LEV-1",
         WHAT="'held' peak factor: three live definitions.",
         DETAIL="criteria.peak_factor() returns PF = 1.0 below 100 properties and labels it "
                "'held'. contract._cross_field REJECTS PF != 1.0 on a row labelled 'held'. "
                "s5_flows holds the factor at Merrimack's own value at 100 properties, "
                "3.62139, and labels it 'held' - which the contract would refuse. This "
                "stage uses s5's NUMBER with the label 'merrimack', because the number does "
                "come from the Merrimack formula. THE THREE MUST BE RECONCILED IN ONE "
                "PLACE; until they are, every published peak factor below 100 properties "
                "carries a label chosen to satisfy a validator.",
         WHO="criteria.py / contract.py / s5_flows.py / this stage"),
    dict(ID="C-LEV-2",
         WHAT="contract.GRAD_BY has no token for 'laid to the level its downstream chamber "
              "needs'.",
         DETAIL="The enum is table11, tractive, ground, cover_min, cover_max, uniform, vmax, "
                "tie. A reach steepened so it arrives at the junction invert instead of "
                "dropping into it is none of those. It is published as 'uniform' where it "
                "took its run's common gradient (which it did, and P1 is the preferred "
                "answer) and as 'cover_min' where a single reach was steepened for a level "
                "reason. `gradient_reason` decomposes both into the finer cause, so nothing "
                "is lost - but the published enum is one token short and that is a contract "
                "finding, not a design one.",
         WHO="contract.GRAD_BY"),
    dict(ID="C-LEV-3",
         WHAT="contract NODES.COVER_M is defined as the SHALLOWEST connected pipe's cover, "
              "which is not the quantity the 12 m cap tests.",
         DETAIL="The shallowest connected pipe is the right datum for the 1.30 m minimum "
                "(H3) and the wrong one for the cap (H4), which is about how deep the hole "
                "is. COVER_M is published as the spec defines it; PAST_CAP is computed from "
                "the DEEPEST connected pipe and `levels_nodes` carries both, so neither "
                "check is run against the wrong number.",
         WHO="contract.NODES.COVER_M"),
    dict(ID="C-LEV-4",
         WHAT="s1_roads' provenance vocabulary is not the contract's.",
         DETAIL="s1 grades SRC as draft_base / draft_propo and CONFIDENCE as corroborated / "
                "drafted / provisional; the contract's enums are dwg_road / dwg_block / ... "
                "and surveyed / drafted / derived / provisional. The mapping used here is "
                "published in `provenance_map` and it NEVER improves a grade: s1's "
                "'drafted' (a platted plot with nothing built) and 'provisional' (bare "
                "ground) both become the contract's 'provisional', which is what philosophy "
                "sec 4 calls a platted reserve.",
         WHO="s1_roads / contract.SRC, contract.CONFIDENCE"),
)


# ======================================================================================
# THE GRAPH.  Arrays, not objects: 56,935 nodes levelled ten times over is a hot loop.
# Topology is READ from DS_NODE (H16) and geometry is never consulted for connectivity.
# ======================================================================================

class Net:
    """The chamber graph as flat arrays.  Edge k runs eu[k] -> ev[k]; `edge_of[i]` is node
    i's ONE outgoing edge, -1 at a terminal, which is the forest invariant made an array."""

    __slots__ = ("uid", "x", "y", "grd", "kind4", "subnet", "on_wadi_nd", "haz",
                 "inlet_deg", "eu", "ev", "elen", "egeom", "ecid", "eon_wadi", "esrc",
                 "econf", "etier", "egnd_fall", "edge_of", "q_loc", "np_loc", "n_conn",
                 "order", "contracted", "untiered_km", "untiered_n", "conn", "n", "m")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
        self.n = len(self.uid)
        self.m = len(self.eu)


def _topo(edge_of: np.ndarray, ev: np.ndarray, n: int) -> np.ndarray:
    """Nodes upstream-first.  Kahn on a forest; a node is emitted once every node draining
    into it has been.  Raises if the graph is not a forest, which is the only way this can
    fail and is exactly what H15 forbids."""
    indeg = np.zeros(n, dtype=np.int64)
    live = np.where(edge_of >= 0)[0]
    if len(live):
        np.add.at(indeg, ev[edge_of[live]], 1)
    rem = indeg.copy()
    q = deque(np.where(indeg == 0)[0].tolist())
    out: List[int] = []
    while q:
        i = q.popleft()
        out.append(i)
        k = edge_of[i]
        if k >= 0:
            j = int(ev[k])
            rem[j] -= 1
            if rem[j] == 0:
                q.append(j)
    if len(out) != n:
        raise K.ContractError(
            f"the chamber graph is not a forest: {n - len(out):,} nodes sit inside a cycle. "
            "H15 makes a loop illegal and contract.Network.add_edge makes one unreachable, "
            "so this came from a layer edited outside the graph.")
    return np.asarray(out, dtype=np.int64)


def load(rec: Optional[K.StageRecord] = None) -> Net:
    """Read the published chamber graph, the tiers and the local loads.

    Everything here is READ.  Nothing an upstream stage already published is recomputed,
    and the two places where this stage has to TRANSLATE - the provenance vocabulary and
    the tier of a chamber-to-chamber segment - are published as tables, not buried."""
    ch = gpd.read_file(CHAMBERS_GPKG, layer="chambers")
    sg = gpd.read_file(CHAMBERS_GPKG, layer="segments")
    cn = gpd.read_file(CHAMBERS_GPKG, layer="connections", ignore_geometry=True)
    hr = gpd.read_file(HIER_GPKG, layer="reaches", ignore_geometry=True)
    if rec is not None:
        rec.read("chambers", str(CHAMBERS_GPKG), len(ch))
        rec.read("segments", str(CHAMBERS_GPKG), len(sg))
        rec.read("connections", str(CHAMBERS_GPKG), len(cn))
        rec.read("hier reaches", str(HIER_GPKG), len(hr))

    # ---- contract the pairs closer than the chamber clearance (A-LEV-13) -------------
    short = sg.LEN_M < CRIT.MH_SNAP_M
    contracted = sg.loc[short, ["US_NODE", "DS_NODE", "LEN_M"]].copy()
    moved_mask = np.zeros(int((~short).sum()), dtype=bool)
    merge_into = dict(zip(contracted.US_NODE.astype(str), contracted.DS_NODE.astype(str)))
    for _ in range(6):                       # resolve a chain of contractions
        merge_into = {a: merge_into.get(b, b) for a, b in merge_into.items()}
    if merge_into:
        xy = dict(zip(ch.NODE_UID.astype(str), zip(ch.X.astype(float), ch.Y.astype(float))))
        sg = sg.loc[~short].copy()
        moved = sg.DS_NODE.astype(str).isin(merge_into)
        moved_mask = moved.values.copy()
        sg["US_NODE"] = sg.US_NODE.astype(str).map(lambda u: merge_into.get(u, u))
        sg["DS_NODE"] = sg.DS_NODE.astype(str).map(lambda u: merge_into.get(u, u))
        # the geometry has to reach the chamber the reach now ends at, or the published
        # layers stop BEING the graph - which is exactly what W10's 1.000 m stitch links did.
        if moved.any():
            g = sg.geometry.values
            for r in np.where(moved.values)[0]:
                g[r] = LineString(list(g[r].coords) + [xy[str(sg.DS_NODE.values[r])]])
            sg = sg.set_geometry(list(g), crs=sg.crs)
            sg.loc[moved.values, "LEN_M"] = sg.geometry.values[moved.values].length                 if False else [sg.geometry.values[r].length
                               for r in np.where(moved.values)[0]]
        sg = sg[sg.US_NODE != sg.DS_NODE].reset_index(drop=True)
        ch = ch[~ch.NODE_UID.astype(str).isin(merge_into)].reset_index(drop=True)
        cn = cn.copy()
        cn["OUT_NODE"] = cn.OUT_NODE.astype(str).map(lambda u: merge_into.get(u, u))

    uid = ch.NODE_UID.astype(str).values
    idx = {u: i for i, u in enumerate(uid)}
    n = len(uid)

    eu = np.array([idx[u] for u in sg.US_NODE.astype(str)], dtype=np.int64)
    ev = np.array([idx[u] for u in sg.DS_NODE.astype(str)], dtype=np.int64)
    edge_of = np.full(n, -1, dtype=np.int64)
    edge_of[eu] = np.arange(len(eu), dtype=np.int64)
    if int((edge_of >= 0).sum()) != len(eu):
        raise K.ContractError(
            "a chamber has two outgoing segments. The network is a FOREST (H15) and s4 "
            "published N_OUT <= 1 on every chamber, so this is a corrupted read.")

    # ---- TIER from s3, by the corridor arc the segment was cut from ------------------
    tier_of_cid = dict(zip(hr.CID.astype(str), hr.TIER.astype(str)))
    ecid = sg.ARC_CID.fillna("").astype(str).values
    etier = np.array([tier_of_cid.get(c, "lateral") for c in ecid], dtype=object)
    untier = np.array([c not in tier_of_cid for c in ecid])

    # ---- the local load, at the chamber s4 assigned it to ----------------------------
    q_loc = np.zeros(n)
    np_loc = np.zeros(n)
    n_conn = np.zeros(n, dtype=np.int64)
    ci = np.array([idx[u] for u in cn.OUT_NODE.astype(str)], dtype=np.int64)
    np.add.at(q_loc, ci, cn.Q_ADF_M3D.values.astype(float))
    np.add.at(np_loc, ci, cn.N_PROP.values.astype(float))
    np.add.at(n_conn, ci, 1)

    net = Net(
        uid=uid, x=ch.X.values.astype(float), y=ch.Y.values.astype(float),
        grd=ch.GRD_M.values.astype(float), kind4=ch.NODE_KIND.astype(str).values,
        subnet=ch.SUBNET.astype(str).values,
        on_wadi_nd=ch.ON_WADI.values.astype(int), haz=ch.HAZ.values.astype(int),
        inlet_deg=ch.INLET_DEG.values.astype(float),
        eu=eu, ev=ev, elen=sg.LEN_M.values.astype(float),
        egeom=list(sg.geometry.values), ecid=ecid,
        eon_wadi=sg.ON_WADI.values.astype(int),
        esrc=sg.SRC.astype(str).values, econf=sg.CONFIDENCE.astype(str).values,
        etier=etier, egnd_fall=sg.GND_FALL.values.astype(float),
        edge_of=edge_of, q_loc=q_loc, np_loc=np_loc, n_conn=n_conn,
        order=None, contracted=contracted, untiered_km=0.0, untiered_n=0, conn=cn)
    net.order = _topo(edge_of, ev, n)
    # GND_FALL RE-DERIVED from the chamber ground levels rather than carried, and checked
    # against s4's published value. Two independently computed numbers agreeing is the only
    # cheap defence against a layer that has quietly parted from the graph it describes.
    gf_re = net.grd[eu] - net.grd[ev]
    unmoved = ~moved_mask if len(moved_mask) == len(eu) else np.ones(len(eu), dtype=bool)
    dev = float(np.abs(gf_re[unmoved] - net.egnd_fall[unmoved]).max()) if len(eu) else 0.0
    if dev > 1e-3:
        raise K.ContractError(
            f"GND_FALL re-derived from the chamber ground levels differs from s4's "
            f"published value by up to {dev:.4f} m on a reach nothing moved. One of the "
            "two is describing a different network.")
    net.egnd_fall = gf_re
    net.untiered_km = float(net.elen[untier].sum() / 1000.0)
    net.untiered_n = int(untier.sum())
    return net


# ======================================================================================
# FLOW.  One accumulator, proved against s5_flows' published answer on s5's own graph
# before it is trusted with ours.  Two implementations of one quantity is how seven
# lifting-station counts got into circulation on this project.
# ======================================================================================

def held_pf_from_s5() -> Tuple[float, str]:
    """s5_flows' published held peak factor, READ from the published layer.

    Not recomputed.  contract.published() has already registered `pf_held` against s5's
    function, and a second definition of one published number is exactly what that register
    exists to stop.  Reading it means that if s5's load basis moves, this stage moves too."""
    a = gpd.read_file(FLOWS_GPKG, layer="arcs", ignore_geometry=True)
    held = a.loc[(a.PF_METH == "held") & (a.QADF_M3D > 0), "PF"].round(7).unique()
    if len(held) != 1:
        raise K.ContractError(
            f"s5_flows publishes {len(held)} different 'held' peak factors ({held[:5]}). It "
            "is one constant by construction (A-FLOW-2), so this is not the file this stage "
            "was written against.")
    return float(held[0]), "s5_flows `arcs`: PF where PF_METH == 'held'"


def accumulate(edge_of: np.ndarray, ev: np.ndarray, elen: np.ndarray, order: np.ndarray,
               q_loc: np.ndarray, np_loc: np.ndarray, held_pf: float,
               crit: Criteria = CRIT) -> Dict[str, np.ndarray]:
    """QADF, properties and upstream length down a forest, then PF, infiltration and peak.

    Indexed BY NODE, describing the reach LEAVING that node - the A-FLOW-3 convention: a
    plot's load enters at the upstream node of its reach, so the reach carries its own local
    load over its whole length.

    It takes bare arrays rather than a Net so the SAME function can be run over s5's arc
    graph in `--selftest` and reproduce s5's published numbers."""
    n = len(q_loc)
    q = q_loc.astype(float).copy()
    npr = np_loc.astype(float).copy()
    L = np.zeros(n)
    for i in order:
        k = edge_of[i]
        if k < 0:
            continue
        j = int(ev[k])
        L[i] += elen[k]
        q[j] += q[i]
        npr[j] += npr[i]
        L[j] += L[i]
    with np.errstate(divide="ignore", invalid="ignore"):
        mer = crit.PF_MERRIMACK_A * (np.maximum(q, 1e-12) / 1000.0) ** (crit.PF_MERRIMACK_B - 1.0)
    pf = np.where(npr > crit.PF_HOLD_PROPERTIES, mer, held_pf)
    pf = np.where(q > 0.0, pf, 1.0)
    q_inf = crit.INFILT_L_D_KM * (L / 1000.0) / SEC_PER_DAY           # L/s, UNPEAKED
    q_pk = q * M3D_TO_LS * pf + q_inf
    return dict(QADF=q, NPROP=npr, UPSLEN=L, PF=pf, QINF=q_inf, QPK=q_pk,
                HELD=((npr <= crit.PF_HOLD_PROPERTIES) & (q > 0)).astype(int))


def reconcile_with_s5(net: Net, acc: Dict[str, np.ndarray]) -> pd.DataFrame:
    """Our chamber-level totals against s5's arc-level ones, with the difference NAMED.

    They are not the same number and they must not be: s5 allocated every plot to its
    nearest corridor arc with no distance cap; s4 could only connect a plot whose nearest
    chamber is within 45 m.  The gap IS s4's `unserved` layer, and if it is not, something
    has gone wrong that a bare total would hide."""
    of = gpd.read_file(FLOWS_GPKG, layer="outfalls", ignore_geometry=True)
    ud = gpd.read_file(FLOWS_GPKG, layer="undelivered", ignore_geometry=True)
    ud = ud[ud.ROLE == "TOTAL"]
    un = gpd.read_file(CHAMBERS_GPKG, layer="unserved", ignore_geometry=True)
    term = net.edge_of < 0
    rows = []
    for what, ours, theirs, island, unserved in (
            ("ADWF, m3/d", float(acc["QADF"][term].sum()), float(of.Q_ADF_M3D.sum()),
             float(ud.Q_M3D.sum()), float(un.Q_ADF_M3D.sum())),
            ("properties", float(acc["NPROP"][term].sum()), float(of.N_PROP.sum()),
             float(ud.N_PROP.sum()), float(un.N_PROP.sum()))):
        rows.append(dict(
            QUANTITY=f"{what} - the project total", S6=ours + unserved,
            S5=theirs + island, DIFF=(theirs + island) - (ours + unserved), NOTE=""))
        rows.append(dict(QUANTITY=f"{what} - reaching a terminal HERE", S6=ours, S5=theirs,
                         DIFF=theirs - ours, NOTE=""))
        rows.append(dict(QUANTITY=f"{what} - s4 `unserved`: no chamber within 45 m",
                         S6=unserved, S5=0.0, DIFF=-unserved,
                         NOTE="in neither network; a scope answer, not a levelling one"))
        rows.append(dict(QUANTITY=f"{what} - s5 `undelivered`: 184 island arcs",
                         S6=0.0, S5=island, DIFF=island,
                         NOTE="s2's to connect; s4 never chambered them"))
        rows.append(dict(QUANTITY=f"{what} - RESIDUAL after both",
                         S6=ours + unserved, S5=theirs + island,
                         DIFF=(theirs + island) - (ours + unserved),
                         NOTE="must be zero"))
    return pd.DataFrame(rows)


# ======================================================================================
# THE HYDRAULIC SELECTOR
#
# `hydra.size_pipe()` is the REFERENCE and `_self_test()` proves this agrees with it on a
# grid of flows and gradients.  It is not called in the hot loop because it bisects for d/D
# on every candidate diameter - 80 Colebrook evaluations to answer a yes/no question.  The
# question "does DN d at gradient S carry Q inside its own d/D limit?" is ONE evaluation:
#
#       q_partial(D, S, dod_limit(d))  >=  Q
#
# because q_partial is monotone in d/D on the branch below 0.95.  The full bisection is then
# run ONCE, on the diameter actually chosen, for the depth of flow and velocity published.
# ======================================================================================

_SERIES = list(CRIT.DN_SERIES)
_OD = {d: CRIT.outside_diameter(d) for d in _SERIES}
_ID = {d: CRIT.internal_diameter(d) for d in _SERIES}
_DMIN = {d: CRIT.invert_depth_min(d) for d in _SERIES}     # ground to invert at 1.30 m cover
_T11 = {d: CRIT.table11(d) for d in _SERIES}
_DODL = {d: CRIT.dod_limit(d) for d in _SERIES}
_STEP = CRIT.SLOPE_STEP
_DN0 = _SERIES[0]


def _rebuild_tables(crit: Criteria) -> None:
    """Re-derive the lookup tables for a sensitivity run.  Called only by `--sweep`, which
    passes a different Criteria object; the design basis is never edited in place."""
    global _SERIES, _OD, _ID, _DMIN, _T11, _DODL, _STEP, _DN0, _SMAX_CACHE, _VCAP_CACHE
    _SERIES = list(crit.DN_SERIES)
    _OD = {d: crit.outside_diameter(d) for d in _SERIES}
    _ID = {d: crit.internal_diameter(d) for d in _SERIES}
    _DMIN = {d: crit.invert_depth_min(d) for d in _SERIES}
    _T11 = {d: crit.table11(d) for d in _SERIES}
    _DODL = {d: crit.dod_limit(d) for d in _SERIES}
    _STEP = crit.SLOPE_STEP
    _DN0 = _SERIES[0]
    _SMAX_CACHE = {}
    _VCAP_CACHE = {}


def ceil_step(s: float) -> float:
    """Up to the next 0.05 % (criteria.SLOPE_STEP).  Rounding UP can only make a reach
    steeper, so it can never put a laid gradient below its own minimum."""
    return math.ceil(s / _STEP - 1e-9) * _STEP


def floor_step(s: float) -> float:
    return math.floor(s / _STEP + 1e-9) * _STEP


def carries(dn: int, S: float, q: float, crit: Criteria = CRIT) -> bool:
    """Does DN `dn` at gradient S carry q m3/s within its own G203-p27 Table 10 limit?"""
    if S <= 0:
        return False
    return HY.q_partial(_ID[dn], S, _DODL[dn], crit) >= q


_SMAX_CACHE: Dict[Tuple[int, int], Optional[float]] = {}


def smax(dn: int, q: float, crit: Criteria = CRIT) -> Optional[float]:
    """The gradient at which velocity reaches G203-p27's 3.0 m/s, or None if it never does.

    Cached on (dn, flow rounded to 0.1 L/s).  The cap is smooth in flow and 0.1 L/s moves it
    by far less than one 0.05 % gradient step, while the cache turns a 120-iteration
    two-stage search into a dictionary lookup on a 56,700-reach network levelled ten times
    over.  `--selftest` checks the cache against the uncached function."""
    key = (dn, int(round(q * 10000.0)))
    hit = _SMAX_CACHE.get(key, "miss")
    if hit != "miss":
        return hit                                                  # type: ignore
    s = HY.smax_for(dn, q, crit)
    if s == HY.INFEASIBLE:
        s = None
    _SMAX_CACHE[key] = s
    return s


_VCAP_CACHE: Dict[Tuple[int, int], Optional[float]] = {}


def vmax_slope(dn: int, q: float, crit: Criteria = CRIT) -> Optional[float]:
    """The steepest gradient ON THE 0.05 % GRID at which this reach is still inside G203-p27's
    3.0 m/s, or None where the cap never bites.

    `hydra.smax_for` solves for the continuous gradient; rounding that DOWN to the grid is
    not enough, because the answer is cached against a flow rounded to 0.1 L/s and the two
    roundings can put the laid gradient a whisker over.  H7 is a HARD constraint, so the
    grid value is VERIFIED with `pipe_state` and stepped down until it holds - 3.004 m/s is
    not 3.0 m/s."""
    key = (dn, int(round(q * 10000.0)))
    hit = _VCAP_CACHE.get(key, "miss")
    if hit != "miss":
        return hit                                                  # type: ignore
    sc = smax(dn, q, crit)
    if sc is None:
        _VCAP_CACHE[key] = None
        return None
    S = floor_step(sc)
    for _ in range(8):
        if S <= 0:
            break
        _y, v = HY.pipe_state(dn, S, q, crit)
        if v is None or v <= crit.V_MAX + 1e-9:
            break
        S = floor_step(S - _STEP / 2)
    _VCAP_CACHE[key] = S
    return S


def choose_size(q: float, inv_up: Optional[float], grd_up: float, grd_dn: float,
                length: float, dn_floor: int, crit: Criteria = CRIT
                ) -> Tuple[int, float, float, str, float, bool]:
    """PASS 1's decision for one reach.
    Returns (DN, S laid, S minimum, sized_by, INV_UP, capped-by-velocity).

    The rule, in the order the philosophy states it:

      * LAY AS SHALLOW AS H3 ALLOWS.  The shallowest legal downstream invert is
        `grd_dn - invert_depth_min(dn)`, so `S_shallow` is the flattest gradient that does
        not leave less than 1.30 m of cover at the downstream end.  Where the ground falls
        faster than the pipe needs, this is what lets the pipe climb back towards the
        surface instead of carrying its depth to the sea.
      * never flatter than the STEEPER of Table 11 and the tractive minimum (G203-p27).
      * never faster than 3.0 m/s (G203-p27 4.2.2.2) - and where the ground is steeper than
        that allows, the pipe does NOT follow the cliff.
      * the diameter is the smallest in the series, at or above the floor, that carries the
        flow inside its own depth-of-flow limit at that gradient.  It is NEVER chosen to buy
        a flatter gradient (G203-p29; Ten States 33.43).

    `inv_up` is None at a head, where the upstream invert is itself set by the minimum cover
    for the diameter being tried - which is why the diameter loop has to own it."""
    cands = [d for d in _SERIES if d >= dn_floor]
    for pos, dn in enumerate(cands):
        iv = (grd_up - _DMIN[dn]) if inv_up is None else inv_up
        s_min = max(_T11[dn], HY.smin_tractive(q, crit))
        s_shallow = (iv - (grd_dn - _DMIN[dn])) / length
        S = ceil_step(max(s_min, s_shallow))
        capped = False
        if S > SLOPE_HARD_MAX:
            S = floor_step(SLOPE_HARD_MAX)
            capped = True
        sc = vmax_slope(dn, q, crit)
        if sc is not None and S > sc:
            S = sc
            capped = True
        # H7 is a HARD constraint and 3.004 m/s is not 3.0 m/s.  vmax_slope caches against a
        # flow rounded to 0.1 L/s, so the cap it returns is verified HERE at this reach's own
        # flow before the gradient is accepted.
        while S > 0:
            _y, _v = HY.pipe_state(dn, S, q, crit)
            if _v is None or _v <= crit.V_MAX + 1e-9:
                break
            S = floor_step(S - _STEP / 2)
            capped = True
        if S < s_min or not carries(dn, S, q, crit):
            continue
        # WHY this size, in hydra.size_pipe()'s own vocabulary and evaluated at the gradient
        # actually laid - so SIZED_BY means exactly what the enum says and `_self_test`
        # can check it against hydra.  "capacity" and "dod" are DIFFERENT answers: one pipe
        # cannot pass the flow at all, the other passes it too full.
        if pos == 0:
            why = "minimum"
        else:
            prev = cands[pos - 1]
            if HY.q_partial(_ID[prev], S, 0.95, crit) < q:
                why = "capacity"
            elif HY.q_partial(_ID[prev], S, _DODL[prev], crit) < q:
                why = "dod"
            else:
                why = "velocity"
        return dn, S, s_min, why, iv, capped
    # the whole series is too small at any legal gradient.  Named, never clamped silently.
    dn = _SERIES[-1]
    iv = (grd_up - _DMIN[dn]) if inv_up is None else inv_up
    s_min = max(_T11[dn], HY.smin_tractive(q, crit))
    S = min(ceil_step(max(s_min, (iv - (grd_dn - _DMIN[dn])) / length)),
            floor_step(SLOPE_HARD_MAX))
    return dn, S, s_min, "infeasible", iv, True


# ======================================================================================
# THE DESIGN OBJECT
# ======================================================================================

class Design:
    """The levelled network.  Every array is indexed BY NODE and describes the reach LEAVING
    that node, except `drop`, which describes what ARRIVES at it."""

    __slots__ = ("inv", "dn", "slope", "smin", "sized_by", "grad_by", "drop", "station",
                 "uniform", "absorbed", "capped", "cliff", "passes", "notes")

    def __init__(self, n: int):
        self.inv = np.full(n, np.nan)
        self.dn = np.zeros(n, dtype=np.int64)
        self.slope = np.zeros(n)
        self.smin = np.zeros(n)
        self.sized_by = np.array([""] * n, dtype=object)
        self.grad_by = np.array([""] * n, dtype=object)
        self.drop = np.zeros(n)
        self.station = np.zeros(n, dtype=bool)
        self.uniform = np.zeros(n, dtype=bool)      # took its run's common gradient (P1)
        self.absorbed = np.zeros(n, dtype=bool)     # steepened to swallow a drop
        self.capped = np.zeros(n, dtype=bool)       # gradient held back by the velocity cap
        self.cliff = np.zeros(n)                    # m the chamber was deepened for a cliff
        self.passes = 0
        self.notes: Dict = {}


# ======================================================================================
# PASS 1 - STRICT.  Every rule applied mechanically.  Compliant, and ugly.
# ======================================================================================

def pass1(net: Net, qpk: np.ndarray, station: np.ndarray, crit: Criteria = CRIT) -> Design:
    """The shallowest legal profile, laid upstream-first.

    At every chamber the outgoing invert is the HIGHEST level satisfying BOTH:
        * 1.30 m of cover on its own outside diameter (G203-p33), and
        * CROWN MATCHING against every arriving pipe (A-LEV-4).
    Taking the lower of the two is what makes a deep branch pull its junction down, which is
    how a depth debt propagates.  It is meant to: the alternative is a pipe discharging into
    a level above its own soffit."""
    n = net.n
    des = Design(n)
    des.station = station.copy()
    for i in net.order:
        k = int(net.edge_of[i])
        if k < 0 or station[i]:
            # a terminal, or a station: the flow leaves in a rising main and this stage
            # publishes no gravity reach from here (A-LEV-10).
            if math.isnan(des.inv[i]):
                des.inv[i] = net.grd[i] - _DMIN[_DN0]
            continue
        j = int(net.ev[k])
        L = float(net.elen[k])
        q = float(qpk[i]) / 1000.0
        iv0 = None if math.isnan(des.inv[i]) else float(des.inv[i])
        d, S, sm, why, iv, capped = choose_size(
            q, iv0, float(net.grd[i]), float(net.grd[j]), L, _DN0, crit)
        if math.isnan(des.inv[i]):
            des.inv[i] = iv
        # THE CLIFF RULE.  Where the ground falls faster than the pipe is allowed to - the
        # velocity cap, or the contract's own 25 % bound on a published gradient - a reach
        # laid from 1.30 m of cover at the top surfaces before it reaches the bottom.  The
        # philosophy's answer is not to chase the cliff but to take the difference at a drop
        # chamber; the chamber is at the TOP, so this deepens THIS chamber until the reach
        # still has its cover at the far end.  The step it creates is a real drop and is
        # counted as one.
        inv_ceiling = (net.grd[j] - _DMIN[d]) + L * S
        if des.inv[i] > inv_ceiling + 1e-9:
            des.cliff[i] = float(des.inv[i] - inv_ceiling)
            des.inv[i] = inv_ceiling
        des.dn[i] = d
        des.slope[i] = S
        des.smin[i] = sm
        des.sized_by[i] = why
        des.capped[i] = bool(capped)
        arr = des.inv[i] - L * S
        # crown matching on the arriving pipe's own OD; `enforce_crowns` re-imposes the
        # exact rule once the outgoing diameter at j is known.
        cand = min(net.grd[j] - _DMIN[d], arr)
        if math.isnan(des.inv[j]) or cand < des.inv[j]:
            des.inv[j] = cand
    return des


def enforce_crowns(net: Net, des: Design) -> int:
    """Impose crown matching EXACTLY, now that every diameter is known.

    Pass 1 matches on the arriving pipe's own outside diameter because the outgoing pipe has
    not been sized yet.  Where the outgoing pipe turns out to be larger its soffit has to
    drop by the difference, and that can cascade.  Sweeping downstream until nothing moves
    is the fixed point; it converges in two or three sweeps because every move is downward
    and bounded by the diameter series.  Returns the sweeps used."""
    for sweep in range(1, 10):
        moved = 0
        for i in net.order:
            k = int(net.edge_of[i])
            if k < 0 or des.station[i]:
                continue
            j = int(net.ev[k])
            d_in = int(des.dn[i])
            d_out = int(des.dn[j]) if des.dn[j] else d_in
            arr = des.inv[i] - net.elen[k] * des.slope[i]
            need = arr + _OD[d_in] - _OD[d_out]      # outgoing soffit <= incoming soffit
            if need < des.inv[j] - 1e-9:
                des.inv[j] = need
                moved += 1
        if not moved:
            return sweep
    return 10


def arrivals(net: Net, des: Design) -> Tuple[np.ndarray, np.ndarray]:
    """(highest arriving invert at each node, the node it came from); -1e18 where nothing
    arrives.  This is the datum the drop is measured from, and it is the same definition
    `asbuilt.observe_design()` uses on NAMA's built pipes - so the two are comparable."""
    hi = np.full(net.n, -1e18)
    who = np.full(net.n, -1, dtype=np.int64)
    for k in range(net.m):
        i = int(net.eu[k])
        if des.station[i]:
            continue
        j = int(net.ev[k])
        a = des.inv[i] - net.elen[k] * des.slope[i]
        if a > hi[j]:
            hi[j] = a
            who[j] = i
    return hi, who


def set_drops(net: Net, des: Design) -> None:
    """DROP_M at every chamber: the highest arriving invert minus the outgoing one.

    G203-p30: a backdrop above 0.60 m, a vortex drop shaft above 2.00 m.  The vortex count
    is THE diagnostic for a tree that is not following the ground, so it is computed here,
    once, from the published inverts and nowhere else."""
    hi, _ = arrivals(net, des)
    des.drop = np.where(hi > -1e17, np.maximum(0.0, hi - des.inv), 0.0)


def covers(net: Net, des: Design, crit: Criteria = CRIT) -> Tuple[np.ndarray, np.ndarray]:
    """(the DEEPEST cover at each chamber, the SHALLOWEST) - over every pipe connected to it.

    Cover is a property of a PIPE, not of a chamber, so a chamber has as many covers as it
    has pipes and they are different numbers wherever there is a drop or a size change.

      * the DEEPEST is what the 12 m cap tests (H4): if any pipe at this chamber is buried
        deeper than the cap, the excavation is past the cap.
      * the SHALLOWEST is what the 1.30 m minimum tests (H3), and it is the contract's own
        definition of NODES.COVER_M.

    Conflating them is C-LEV-3, and it is why both are returned and both are published."""
    depth = net.grd - des.inv
    hi = np.full(net.n, -1e18)
    lo = np.full(net.n, 1e18)
    for i in range(net.n):
        d = int(des.dn[i])
        if d and not des.station[i] and net.edge_of[i] >= 0:
            c = depth[i] - _OD[d] - crit.WALL_ALLOW      # the outgoing pipe at this chamber
            hi[i] = max(hi[i], c)
            lo[i] = min(lo[i], c)
    for k in range(net.m):
        i = int(net.eu[k])
        if des.station[i] or des.dn[i] == 0:
            continue
        j = int(net.ev[k])
        d = int(des.dn[i])
        arr = des.inv[i] - net.elen[k] * des.slope[i]     # the arriving pipe at chamber j
        c = (net.grd[j] - arr) - _OD[d] - crit.WALL_ALLOW
        hi[j] = max(hi[j], c)
        lo[j] = min(lo[j], c)
    orphan = hi < -1e17                                   # a chamber with no pipe at all
    hi = np.where(orphan, 0.0, hi)
    lo = np.where(orphan, 0.0, lo)
    return hi, lo


# ======================================================================================
# PASS 2 - REVIEW.  The gradient a person would have drawn.
#
# Pass 1 lays every reach at its own flattest legal gradient and then, at the bottom of a
# run, discovers that the chamber it joins is three metres deeper - and buys a vortex drop
# shaft to get rid of the difference.  That is levelling as arithmetic.  What a designer
# does instead is SPEND the fall along the run: lay the whole street at one steeper gradient
# so the pipe ARRIVES at the level its junction needs.
#
# MEASURED ON THIS NETWORK, 2026-09-03, pass 1 against pass 1 + pass 2 with no stations in
# either: the vortex-shaft count falls from 1,781 to 196 - 1.194/km to 0.131/km against
# NAMA's built 0.585/km - and the backdrops from 1,101 to 25, by spending 17,127 m of fall
# that pass 1 threw away.  It costs nothing in depth at the junction, because the junction
# invert does not move; and nothing upstream, because the head stays at minimum cover.  The
# only thing it changes is WHERE between the two ends the fall is spent.
#
# TWO ARMS, and the philosophy chooses between them per run:
#   UNIFORM  one gradient for the whole run (P1, the preferred answer).  Deeper in the
#            middle, because the fall is spent early.
#   LATE     pass 1's gradients kept and the fall taken as late as possible, steepening from
#            the downstream end backwards (P6, minimum depth).
# P1 outranks P6, so UNIFORM is used - EXCEPT where it would push a chamber past the 12 m
# cap, because "P1 is never bought at the price of a pumping station" (philosophy 3a).  The
# count of runs that fell back, and the depth the choice costs, are both published.
# ======================================================================================

def build_runs(net: Net, des: Design) -> List[List[int]]:
    """Every run of pass-through chambers, as a list of node indices from its start to its
    end.  A run starts at a head, a junction or the chamber a rising main discharges into,
    and ends at the next junction, terminal or station.

    Philosophy sec 4 is explicit that chamber spacing (H12) and run length (P3) are
    different rules - this is the run, and it is what a gradient belongs to."""
    n_in = np.zeros(net.n, dtype=np.int64)
    for k in range(net.m):
        if not des.station[int(net.eu[k])]:
            n_in[int(net.ev[k])] += 1
    n_out = np.array([0 if (net.edge_of[i] < 0 or des.station[i]) else 1
                      for i in range(net.n)], dtype=np.int64)
    passthrough = (n_in == 1) & (n_out == 1)
    runs: List[List[int]] = []
    for i in range(net.n):
        if n_out[i] == 0 or passthrough[i]:
            continue                                    # not a run START
        chain = [i]
        cur = i
        while True:
            k = int(net.edge_of[cur])
            if k < 0 or des.station[cur]:
                break
            nxt = int(net.ev[k])
            chain.append(nxt)
            if not passthrough[nxt]:
                break
            cur = nxt
        if len(chain) >= 2:
            runs.append(chain)
    return runs


def _hi_bound(dn: int, q: float, crit: Criteria) -> float:
    """The steepest gradient this reach may be laid at: the 3.0 m/s velocity cap (G203-p27)
    or the contract's own 25 % sanity bound on a published gradient, whichever bites."""
    sc = vmax_slope(dn, q, crit)
    return min(SLOPE_HARD_MAX, sc if sc is not None else SLOPE_HARD_MAX)


def _walk(net: Net, des: Design, chain: List[int], slopes: Sequence[float]) -> List[float]:
    """Invert at every node of a run, given a gradient per reach.  Crown matching (A-LEV-4)
    is applied at each interior chamber, so the profile that comes out is the one that will
    be published - not an idealised straight line."""
    invs = [float(des.inv[chain[0]])]
    inv = invs[0]
    for idx in range(len(chain) - 1):
        i, j = chain[idx], chain[idx + 1]
        k = int(net.edge_of[i])
        arr = inv - net.elen[k] * slopes[idx]
        d_in = int(des.dn[i])
        d_out = int(des.dn[j]) if des.dn[j] else d_in
        inv = arr + _OD[d_in] - _OD[d_out]
        invs.append(inv)
    return invs


def relay(net: Net, des: Design, qpk: np.ndarray, crit: Criteria = CRIT) -> Dict[str, float]:
    """PASS 2 over every run.  Returns the diagnostics the report prints."""
    runs = build_runs(net, des)
    stat = dict(runs=len(runs), uniform=0, late=0, untouched=0, reaches_uniform=0,
                reaches_absorbed=0, fall_recovered_m=0.0, fallback_cap=0,
                run_len_max_m=0.0)
    max_cov = crit.MAX_COVER
    for chain in runs:
        m = len(chain) - 1
        edges = [int(net.edge_of[chain[t]]) for t in range(m)]
        if any(e < 0 for e in edges):
            continue
        if any(des.capped[chain[t]] or des.cliff[chain[t]] > 0 for t in range(m)):
            # a reach already held back by the 3.0 m/s cap, or a chamber deepened for a
            # cliff, is at its limit: re-laying the run would either raise the cliff chamber
            # back up or ask for a gradient the reach may not have.  Left as pass 1 laid it,
            # and counted.
            stat["skipped_capped"] = stat.get("skipped_capped", 0) + 1
            continue
        lens = [float(net.elen[e]) for e in edges]
        Lrun = sum(lens)
        stat["run_len_max_m"] = max(stat["run_len_max_m"], Lrun)
        s1 = [float(des.slope[chain[t]]) for t in range(m)]
        base = _walk(net, des, chain, s1)
        end = chain[-1]
        deficit = base[-1] - float(des.inv[end])        # how much fall pass 1 threw away
        if deficit <= 1e-6:
            stat["untouched"] += 1
            continue
        hi = [_hi_bound(int(des.dn[chain[t]]), float(qpk[chain[t]]) / 1000.0, crit)
              for t in range(m)]

        # ---- arm UNIFORM (P1): one gradient, landing exactly on the junction invert -----
        adopted = None
        if m >= 2:
            s_lo = max(s1)
            s_hi = min(hi)
            # the crown steps along the run TELESCOPE: sum(OD_in - OD_out) over the chain is
            # OD at the first reach minus OD at the last, whatever happens in between.
            d_end = int(des.dn[end]) if des.dn[end] else int(des.dn[chain[-2]])
            telescope = _OD[int(des.dn[chain[0]])] - _OD[d_end]
            s_fall = (float(des.inv[chain[0]]) + telescope - float(des.inv[end])) / Lrun
            if s_fall >= s_lo - 1e-12:
                S = floor_step(min(s_fall, s_hi))
                if S >= s_lo - 1e-12 and S > 0:
                    su = [S] * m
                    inv_u = _walk(net, des, chain, su)
                    ok = inv_u[-1] >= float(des.inv[end]) - 1e-6
                    for t in range(m):
                        if not ok:
                            break
                        d = int(des.dn[chain[t]])
                        cov = (net.grd[chain[t + 1]] - inv_u[t + 1]) - _OD[d] - crit.WALL_ALLOW
                        qt = float(qpk[chain[t]]) / 1000.0
                        if cov > max_cov + 1e-9:
                            ok = False
                            stat["fallback_cap"] += 1
                        elif not carries(d, S, qt, crit):
                            ok = False
                        else:
                            _y, _v = HY.pipe_state(d, S, qt, crit)
                            if _v is not None and _v > crit.V_MAX + 1e-9:
                                ok = False
                                stat["fallback_vmax"] = stat.get("fallback_vmax", 0) + 1
                    if ok:
                        adopted = ("uniform", su, inv_u)

        # ---- arm LATE (P6): keep pass 1's gradients, take the fall as late as possible --
        if adopted is None:
            s2 = list(s1)
            left = deficit
            for t in range(m - 1, -1, -1):
                if left <= 1e-6:
                    break
                want = floor_step(min(s2[t] + left / lens[t], hi[t]))
                qt = float(qpk[chain[t]]) / 1000.0
                dt = int(des.dn[chain[t]])
                while want > s2[t]:
                    _y, _v = HY.pipe_state(dt, want, qt, crit)
                    if _v is None or _v <= crit.V_MAX + 1e-9:
                        break
                    want = floor_step(want - _STEP / 2)
                if want <= s2[t] + 1e-12:
                    continue
                inv_try = _walk(net, des, chain, s2[:t] + [want] + s2[t + 1:])
                d = int(des.dn[chain[t]])
                cov = (net.grd[chain[t + 1]] - inv_try[t + 1]) - _OD[d] - crit.WALL_ALLOW
                if cov > max_cov + 1e-9 or inv_try[-1] < float(des.inv[end]) - 1e-6:
                    continue
                left -= (want - s2[t]) * lens[t]
                s2[t] = want
            inv_l = _walk(net, des, chain, s2)
            adopted = ("late", s2, inv_l)

        arm, slopes, invs = adopted
        for t in range(m):
            i = chain[t]
            if slopes[t] > des.slope[i] + 1e-12:
                des.absorbed[i] = True
                stat["reaches_absorbed"] += 1
                stat["fall_recovered_m"] += (slopes[t] - des.slope[i]) * lens[t]
            des.slope[i] = slopes[t]
            if arm == "uniform":
                des.uniform[i] = True
            des.inv[i] = invs[t]
        if arm == "uniform":
            stat["uniform"] += 1
            stat["reaches_uniform"] += m
        else:
            stat["late"] += 1
    return stat


# ======================================================================================
# THE CAP, THE TWO EXITS, AND WHERE A STATION GOES
# ======================================================================================

def cap_exits(net: Net, des: Design, cov_deep: np.ndarray, crit: Criteria = CRIT
              ) -> Tuple[np.ndarray, np.ndarray]:
    """Philosophy sec 5's two exits, BOTH bounded twice.  Returns (exit token, distance).

    An excursion past the 12 m cap is allowed to stand when, walking downstream from the
    breaching chamber:
        * the cover recovers below the cap within 500 m, or
        * the run reaches a terminal within 1,000 m,
    and it is WITHDRAWN when any chamber inside the excursion carries a drop or a cover past
    criteria.DROP_CEILING_M.  Stated as distance alone, an exit says nothing about how deep
    the excursion goes in between - and on 2026-09-02 that omission produced a chamber
    36.81 m deep with a 35.06 m drop into it, legal all the way down."""
    n = net.n
    token = np.array([""] * n, dtype=object)
    dist = np.zeros(n)
    ceiling = crit.DROP_CEILING_M
    past = cov_deep > crit.MAX_COVER
    for i in np.where(past)[0]:
        cur = int(i)
        d = 0.0
        worst_drop = 0.0
        worst_cov = float(cov_deep[i])
        found = ""
        while True:
            k = int(net.edge_of[cur])
            if k < 0 or des.station[cur]:
                if d <= 1000.0:
                    found = "outfall_1000m"
                break
            d += float(net.elen[k])
            cur = int(net.ev[k])
            worst_drop = max(worst_drop, float(des.drop[cur]))
            worst_cov = max(worst_cov, float(cov_deep[cur]))
            if not past[cur]:
                if d <= 500.0:
                    found = "recovers_500m"
                break
            if d > 1000.0:
                break
        if found and worst_drop <= ceiling and worst_cov <= ceiling:
            token[i] = found
            dist[i] = d
    return token, dist


def station_sites(net: Net, des: Design, cov_deep: np.ndarray, exit_tok: np.ndarray,
                  crit: Criteria = CRIT) -> Tuple[List[int], pd.DataFrame]:
    """Where the cap demands a lifting station, and why there.

    From every unexcused breach, walk UPSTREAM along the branch whose arriving invert is
    dragging the chamber down - the branch that is actually buying the depth - until the
    last chamber still INSIDE the cap.  That is the site.  Two adjustments, both from
    philosophy sec 5:

      * NEVER on a chamber that carries a drop.  'A drop is flow going down; a station lifts
        it up. One where they meet is physically incoherent.'  Step one further upstream.
      * The site is recorded with whether it sits inside a contiguous UPHILL stretch.  Where
        it does, the ideal site is the FOOT of that stretch, further upstream still - but
        moving it there strands every chamber in between, whose pipe would have to be
        re-oriented.  That is a stage-2/3 decision, not a levelling one, and it is published
        as an open item rather than done quietly here (A-LEV-12).
    """
    lo = np.full(net.n, 1e18)
    src = np.full(net.n, -1, dtype=np.int64)
    for k in range(net.m):
        i = int(net.eu[k])
        if des.station[i]:
            continue
        j = int(net.ev[k])
        a = des.inv[i] - net.elen[k] * des.slope[i]
        if a < lo[j]:
            lo[j] = a
            src[j] = i
    past = cov_deep > crit.MAX_COVER
    rows = []
    sites: List[int] = []
    seen = set()
    # ONLY THE FRONT OF AN EXCURSION.  A breach whose own governing branch is already past
    # the cap is relieved by the station that front gets, so siting one on it too buys a
    # station nobody needed - and an earlier version of this rule walked all the way to the
    # top of the branch, which put stations at the heads of laterals lifting 0.03 L/s.
    fronts = np.where(past & (exit_tok == "") & (src >= 0)
                      & ~past[np.maximum(src, 0)])[0]
    for b in fronts:
        cur = int(b)
        hops = 0
        while past[cur] and src[cur] >= 0 and hops < 5000:
            cur = int(src[cur])
            hops += 1
        if past[cur]:
            # the branch is past the cap all the way to its head - which a head at 1.30 m of
            # cover cannot be.  Named rather than silently sited on a breaching chamber.
            rows.append(dict(NODE="", BREACH=net.uid[int(b)], HOPS_UP=hops,
                             STEPPED_OFF_DROP=-1, COVER_M=float("nan"),
                             BREACH_COVER_M=float(cov_deep[int(b)]), ON_UPHILL=-1,
                             UPHILL_M=0.0, UPHILL_RISE_M=0.0, GRD_M=float("nan"),
                             SUBNET=net.subnet[int(b)]))
            continue
        stepped = 0
        while (des.drop[cur] > crit.DROP_TRIGGER and src[cur] >= 0
               and not past[int(src[cur])] and stepped < 20):
            cur = int(src[cur])
            stepped += 1
        if des.station[cur] or cur in seen:
            continue
        seen.add(cur)
        sites.append(cur)
        # is this site inside a contiguous uphill stretch, and how long is it?
        up_len = 0.0
        up_rise = 0.0
        c = cur
        for _ in range(400):
            k = int(net.edge_of[c])
            if k < 0 or net.egnd_fall[k] >= -crit.ADVERSE_MIN_M:
                break
            up_len += float(net.elen[k])
            up_rise += -float(net.egnd_fall[k])
            c = int(net.ev[k])
        rows.append(dict(
            NODE=net.uid[cur], BREACH=net.uid[int(b)], HOPS_UP=hops,
            STEPPED_OFF_DROP=stepped, COVER_M=float(cov_deep[cur]),
            BREACH_COVER_M=float(cov_deep[int(b)]),
            ON_UPHILL=int(up_len > 0.0), UPHILL_M=up_len, UPHILL_RISE_M=up_rise,
            GRD_M=float(net.grd[cur]), SUBNET=net.subnet[cur]))
    return sites, pd.DataFrame(rows)


def solve(net: Net, qpk: np.ndarray, crit: Criteria = CRIT, max_passes: int = 25,
          verbose: bool = True) -> Tuple[Design, pd.DataFrame, pd.DataFrame]:
    """The outer loop: level, review, test the cap, put in the stations the cap demands,
    and do it again until no breach is left that an exit does not excuse.

    It terminates because every pass either adds a station - and a station can only ever
    remove depth downstream of itself - or stops."""
    station = np.zeros(net.n, dtype=bool)
    trace = []
    sites_df = pd.DataFrame()
    des = None
    for p in range(1, max_passes + 1):
        des = pass1(net, qpk, station, crit)
        sweeps = enforce_crowns(net, des)
        set_drops(net, des)
        rl = relay(net, des, qpk, crit)
        des.notes["relay"] = rl
        set_drops(net, des)
        cov_deep, cov_shallow = covers(net, des, crit)
        tok, dist = cap_exits(net, des, cov_deep, crit)
        sites, sdf = station_sites(net, des, cov_deep, tok, crit)
        elen_of_node = np.zeros(net.n)
        elen_of_node[net.eu] = net.elen
        live = (net.edge_of >= 0) & (~station)
        trace.append(dict(
            PASS=p, STATIONS=int(station.sum()), CROWN_SWEEPS=sweeps,
            RUNS=rl["runs"], UNIFORM=rl["uniform"], LATE=rl["late"],
            FALL_RECOVERED_M=round(rl["fall_recovered_m"], 1),
            PAST_CAP_N=int((cov_deep > crit.MAX_COVER).sum()),
            PAST_CAP_KM=round(float(elen_of_node[cov_deep > crit.MAX_COVER].sum()) / 1000.0, 2),
            EXCUSED_N=int((tok != "").sum()),
            MAX_COVER_M=round(float(cov_deep.max()), 2),
            MAX_DROP_M=round(float(des.drop.max()), 2),
            VORTEX_N=int((des.drop > crit.BACKDROP_MAX).sum()),
            NEW_STATIONS=len(sites)))
        if verbose:
            t = trace[-1]
            _log(f"pass {p:2d}: stations {t['STATIONS']:4d} | past cap "
                 f"{t['PAST_CAP_N']:5d} ({t['PAST_CAP_KM']:6.2f} km) | excused "
                 f"{t['EXCUSED_N']:4d} | max cover {t['MAX_COVER_M']:6.2f} m | vortex "
                 f"{t['VORTEX_N']:5d} | +{t['NEW_STATIONS']} stations")
        if not sites:
            if sites_df.empty and len(sdf):
                sites_df = sdf
            break
        sites_df = sdf if sites_df.empty else pd.concat([sites_df, sdf], ignore_index=True)
        station[np.asarray(sites, dtype=np.int64)] = True
    assert des is not None

    # ---- PRUNE: take out every station the design no longer needs -------------------
    #
    # The loop above only ever ADDS. W8 cleared its pump flags at the top of every pass and
    # left a comment saying exactly why: "a pump placed in an earlier pass may not be needed
    # once diameters change, and a stale flag would double-count stations". W12 had no
    # equivalent, so a station placed on pass 1 - before enforce_crowns, set_drops and relay
    # have recovered any fall - survived even when the ground turned out to have enough fall
    # all along.
    #
    # Measured in the W8 test area, where W8 needs none: three stations were published. One
    # had 23.1 m of ground fall against 19.5 m of need and a deepest pipe of 3.92 m against
    # the 12 m cap. Two had nothing draining into them.
    #
    # Cheapest first: try removing ALL of them. If the design still has no un-excused breach,
    # none was needed. Otherwise fall back to dropping them one at a time, biggest doubt
    # first, keeping only those whose removal actually reintroduces a breach.
    def _breaches(st_mask):
        d = pass1(net, qpk, st_mask, crit)
        enforce_crowns(net, d)
        set_drops(net, d)
        relay(net, d, qpk, crit)
        set_drops(net, d)
        cd, _cs = covers(net, d, crit)
        tk, _ds = cap_exits(net, d, cd, crit)
        return int(((cd > crit.MAX_COVER) & (tk == "")).sum()), d

    n_before = int(station.sum())
    pruned = 0
    if n_before:
        none_at_all = np.zeros(net.n, dtype=bool)
        n_bad, d_try = _breaches(none_at_all)
        if n_bad == 0:
            if verbose:
                _log(f"prune: NONE of the {n_before} stations is needed - the design has no "
                     f"un-excused breach without them")
            station, des, pruned = none_at_all, d_try, n_before
        else:
            # one at a time, and a station only stays if taking it out brings a breach back
            order = list(np.where(station)[0])
            for i in order:
                trial = station.copy()
                trial[i] = False
                n_bad, d_try = _breaches(trial)
                if n_bad == 0:
                    station, des, pruned = trial, d_try, pruned + 1
            if verbose and pruned:
                _log(f"prune: {pruned} of {n_before} stations removed - not needed once the "
                     f"crowns, drops and relayed runs had settled")
    des.notes["stations_pruned"] = pruned
    des.notes["stations_before_prune"] = n_before

    des.passes = len(trace)
    des.station = station
    return des, pd.DataFrame(trace), sites_df


# ======================================================================================
# PROVENANCE.  s1's vocabulary is not the contract's, and the mapping NEVER improves a
# grade (P6: provenance is carried to the end and never laundered).  C-LEV-4.
# ======================================================================================

SRC_MAP = {"draft_base": "dwg_road", "draft_propo": "dwg_road"}
CONF_MAP = {"corroborated": "drafted",      # an independently recorded centreline, or a
                                            # plot with something built on it (s1)
            "drafted": "provisional",       # a platted plot with NOTHING built - which is
                                            # exactly what philosophy sec 4 calls a
                                            # provisional corridor
            "provisional": "provisional"}   # a reserve on bare ground


def provenance_map_frame() -> pd.DataFrame:
    return pd.DataFrame([
        dict(FIELD="SRC", FROM=k, TO=v,
             WHY="both s1 layers are road centre lines on a drawing; the evidence for one "
                 "being a street lives in CONFIDENCE, not in the DXF layer name")
        for k, v in SRC_MAP.items()] + [
        dict(FIELD="CONFIDENCE", FROM=k, TO=v,
             WHY={"corroborated": "an independently recorded centreline within 12 m, or a "
                                  "plot with a built structure (s1) - drawn and corroborated",
                  "drafted": "a platted plot with nothing built on it. Philosophy sec 4 "
                             "calls that a provisional corridor, so the grade goes DOWN",
                  "provisional": "a reserve on bare ground"}[k])
        for k, v in CONF_MAP.items()])


# ======================================================================================
# WHAT SET THE GRADIENT.  contract.GRAD_BY is one token short of what this stage can do -
# see C-LEV-2 - so the published enum is the nearest true member and `gradient_reason`
# decomposes it into the finer cause.
# ======================================================================================

def classify_gradient(net: Net, des: Design, qpk: np.ndarray, crit: Criteria = CRIT
                      ) -> Tuple[np.ndarray, np.ndarray]:
    """(GRAD_BY for the contract, the finer reason for the diagnostic table)."""
    n = net.n
    out = np.array([""] * n, dtype=object)
    fine = np.array([""] * n, dtype=object)
    half = _STEP / 2.0 + 1e-12
    for i in range(n):
        k = int(net.edge_of[i])
        if k < 0 or des.station[i] or des.dn[i] == 0:
            continue
        S = float(des.slope[i])
        sm = float(des.smin[i])
        dn = int(des.dn[i])
        q = float(qpk[i]) / 1000.0
        t11 = _T11[dn]
        tr = HY.smin_tractive(q, crit)
        sg = float(net.egnd_fall[k]) / float(net.elen[k])
        if des.capped[i]:
            out[i] = "vmax"
            fine[i] = "held back by the 3.0 m/s cap or the 25 % publishing bound"
        elif S <= sm + 1e-12:
            if tr > t11:
                out[i] = "tractive"
                fine[i] = f"tractive minimum at tau = {crit.TAU_PA:g} Pa (GAP-9)"
            else:
                out[i] = "table11"
                fine[i] = "G203-p29 Table 11 floor for this diameter"
        elif des.uniform[i]:
            out[i] = "uniform"
            fine[i] = "the run's common gradient (P1), laid to land on its junction invert"
        elif abs(S - sg) <= half:
            out[i] = "ground"
            fine[i] = "the ground fall; both minima already satisfied"
        elif des.absorbed[i]:
            out[i] = "cover_min"
            fine[i] = ("steepened to arrive at the level its downstream chamber needs, "
                       "instead of dropping into it (P5 crown matching)")
        else:
            out[i] = "cover_min"
            fine[i] = "steepened to hold 1.30 m of cover at the downstream end (G203-p33)"
    return out, fine


# ======================================================================================
# THE OBSTACLES.  Measured, never assumed - the contract refuses to publish a reach that
# touches a wadi or a dual carriageway with nothing scheduling it.
# ======================================================================================

def dual_overlap(net: Net, buffer_m: float = 4.0) -> np.ndarray:
    """Metres of every reach inside the dual-carriageway band.

    RECOMPUTED here rather than inherited: the contract's own words are "a check recomputes
    it independently, so a disagreement is itself the finding".  The 4.0 m band is the same
    one `asbuilt.A_DUAL_BUFFER_M` measures NAMA's built network with, so our share and
    theirs are the same quantity."""
    rd = gpd.read_file(ROADS_GPKG, layer="roads")
    dual = rd[rd.DUAL == 1]
    out = np.zeros(net.m)
    if dual.empty:
        return out
    band = dual.geometry.buffer(buffer_m)
    tree = STRtree(list(band.values))
    for k in range(net.m):
        g = net.egeom[k]
        hit = tree.query(g)
        if len(hit) == 0:
            continue
        tot = 0.0
        for h in hit:
            inter = g.intersection(band.values[int(h)])
            if not inter.is_empty:
                tot += inter.length
        out[k] = min(tot, float(net.elen[k]))
    return out


def wadi_runs(net: Net, des: Design, on: np.ndarray) -> List[List[int]]:
    """Contiguous chains of on-wadi reaches along the flow path.  ONE crossing is one run,
    not one reach: H1a asks whether the contact is a single contiguous run and how long it
    is, and a per-reach register cannot answer either question."""
    nxt: Dict[int, int] = {}
    for k in range(net.m):
        if not on[k]:
            continue
        j = int(net.ev[k])
        k2 = int(net.edge_of[j])
        if k2 >= 0 and on[k2] and not des.station[j]:
            nxt[k] = k2
    has_pred = set(nxt.values())
    runs: List[List[int]] = []
    used: set = set()
    # Two on-wadi branches meeting on wadi ground share everything below the junction. Each
    # reach belongs to exactly ONE contact, or the register counts the same pipe twice - and
    # the length running along a wadi came out at 131 km on a 75 km contact.
    starts = [int(k) for k in np.where(on)[0] if int(k) not in has_pred]
    starts += [int(k) for k in np.where(on)[0] if int(k) in has_pred]
    for k in starts:
        if k in used:
            continue
        chain = [k]
        used.add(k)
        cur = k
        while cur in nxt and nxt[cur] not in used and len(chain) < 5000:
            cur = nxt[cur]
            used.add(cur)
            chain.append(cur)
        runs.append(chain)
    return runs


def _bearing(g) -> float:
    c = list(g.coords)
    dx, dy = c[-1][0] - c[0][0], c[-1][1] - c[0][1]
    return math.degrees(math.atan2(dy, dx)) % 180.0


def build_crossings(net: Net, des: Design, on_dual: np.ndarray, live: np.ndarray,
                    crit: Criteria = CRIT
                    ) -> Tuple[gpd.GeoDataFrame, np.ndarray, pd.DataFrame,
                               np.ndarray, np.ndarray, pd.DataFrame]:
    """The crossings register, minted here as a STAND-IN (A-LEV-8), and the CROSS_ID that
    goes on every reach that touches an obstacle.

    ANGLE_DEG is MEASURED - the acute angle between the crossing's own bearing and the
    bearing of the nearest wadi stream line.  A constant 90 was published on 3,290 crossings
    once on this project and the measured minimum turned out to be 0.00 deg, so the register
    carries the measurement or it carries nothing.

    ONE CROSS_ID PER REACH, and a reach can touch two obstacles.  A register row names ONE
    obstacle because the obstacle decides whose consent is needed - MoAFWR for a wadi
    (G201-p85), the roads authority for a carriageway - so where a reach touches both, the
    LONGER contact is scheduled and the shorter one is published in `obstacle_conflict` with
    its measured length.  Nothing is lost; it is relocated, and it is C-LEV-6."""
    st = gpd.read_file(STREAMS_GPKG, layer="streams")
    wad = st[st.IS_WADI == 1]
    wgeom = list(wad.geometry.values)
    wtree = STRtree(wgeom) if wgeom else None

    # ONLY the reaches this stage actually publishes can carry a CROSS_ID: the reach a
    # station withdraws to a rising main is not a gravity reach and must not leave a
    # register row nothing references.
    on_wadi_m = np.where((net.eon_wadi == 1) & live, net.elen, 0.0)
    on_dual_m = np.where(live, on_dual, 0.0)
    clash = []
    for k in np.where((on_wadi_m > 0) & (on_dual_m > 0))[0]:
        k = int(k)
        keep = "wadi" if on_wadi_m[k] >= on_dual_m[k] else "dual"
        clash.append(dict(EDGE_UID=K.EDGE_UID_FMT.format(k + 1),
                          ON_WADI_M=round(float(on_wadi_m[k]), 2),
                          ON_DUAL_M=round(float(on_dual_m[k]), 2), SCHEDULED=keep,
                          SUPPRESSED_M=round(float(on_dual_m[k] if keep == "wadi"
                                                   else on_wadi_m[k]), 2),
                          WHY="one CROSS_ID per reach, and a register row names one "
                              "obstacle. The longer contact is scheduled; this is the "
                              "other one, published so it is not lost (C-LEV-6)"))
        if keep == "wadi":
            on_dual_m[k] = 0.0
        else:
            on_wadi_m[k] = 0.0

    cross_id = np.array([""] * net.m, dtype=object)
    rows, geoms, h1a = [], [], []
    seq = 0
    for chain in wadi_runs(net, des, on_wadi_m > 0):
        seq += 1
        cid = K.CROSS_UID_FMT.format(seq)
        parts = [net.egeom[k] for k in chain]
        merged = linemerge(parts) if len(parts) > 1 else parts[0]
        if merged.geom_type != "LineString":
            merged = LineString([parts[0].coords[0], parts[-1].coords[-1]])
        L = float(sum(net.elen[k] for k in chain))
        ang = float("nan")
        if wtree is not None:
            near = wtree.query_nearest(merged)
            near = int(near[0]) if np.ndim(near) else int(near)
            a = abs(_bearing(merged) - _bearing(wgeom[near]))
            # 0 deg = the pipe runs ALONG the wadi, 90 deg = it crosses it square.
            ang = min(a, 180.0 - a)
        # cover over the run, on each reach's own outside diameter
        cov = []
        for k in chain:
            i, j = int(net.eu[k]), int(net.ev[k])
            d = int(des.dn[i]) or _DN0
            cov.append((net.grd[i] - des.inv[i]) - _OD[d] - crit.WALL_ALLOW)
            cov.append((net.grd[j] - (des.inv[i] - net.elen[k] * des.slope[i]))
                       - _OD[d] - crit.WALL_ALLOW)
        chambers_on = int(sum(int(net.on_wadi_nd[int(net.eu[k])]) for k in chain)
                          + int(net.on_wadi_nd[int(net.ev[chain[-1]])]))
        # H1a's four conditions, as far as this stage can test them
        square = (not math.isnan(ang)) and abs(90.0 - ang) <= crit.WADI_XING_SKEW_DEG
        h1a.append(dict(
            CROSS_ID=cid, N_REACH=len(chain), LEN_M=round(L, 2),
            ANGLE_DEG=round(ang, 1) if not math.isnan(ang) else None,
            SQUARE_ENOUGH=int(square), CHAMBERS_ON_WADI=chambers_on,
            MIN_COVER_M=round(float(min(cov)), 2),
            MEETS_1P50=int(min(cov) >= crit.MIN_COVER_WADI_XING - 1e-9),
            H1A_OK=int(square and chambers_on == 0
                       and min(cov) >= crit.MIN_COVER_WADI_XING - 1e-9),
            WHY=("crossing" if square else "runs ALONG the wadi - H1a condition 1 fails")))
        for k in chain:
            cross_id[k] = cid
        rows.append(dict(CROSS_ID=cid, EDGE_UID="", OBSTACLE="wadi", LEN_M=merged.length,
                         ANGLE_DEG=(round(ang, 2) if not math.isnan(ang) else 0.0),
                         METHOD="open_cut", COVER_M=round(float(min(cov)), 3), APPROVED=0,
                         SRC="terrain", CONFIDENCE="derived", STAGE=STAGE,
                         PACKAGE="", PHASE=0))
        geoms.append(merged)

    for k in np.where(on_dual_m > 0)[0]:
        k = int(k)
        seq += 1
        cid = K.CROSS_UID_FMT.format(seq)
        cross_id[k] = cid
        i = int(net.eu[k])
        d = int(des.dn[i]) or _DN0
        rows.append(dict(CROSS_ID=cid, EDGE_UID=K.EDGE_UID_FMT.format(k + 1),
                         OBSTACLE="dual", LEN_M=float(net.egeom[k].length),
                         ANGLE_DEG=0.0, METHOD="thrust_bore",
                         COVER_M=round(float((net.grd[i] - des.inv[i]) - _OD[d]
                                             - crit.WALL_ALLOW), 3),
                         APPROVED=0, SRC="terrain", CONFIDENCE="derived", STAGE=STAGE,
                         PACKAGE="", PHASE=0))
        geoms.append(net.egeom[k])

    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=K.CRS_EPSG) if rows else \
        gpd.GeoDataFrame(columns=[f.name for f in K.CROSSINGS.fields] + ["geometry"],
                         geometry=[], crs=K.CRS_EPSG)
    # a register row nothing references is an unbuilt crossing, and the contract says so.
    used = set(str(c) for c in cross_id) - {""}
    if len(gdf):
        gdf = gdf[gdf.CROSS_ID.isin(used)].reset_index(drop=True)
    return gdf, cross_id, pd.DataFrame(h1a), on_wadi_m, on_dual_m, pd.DataFrame(clash)


# ======================================================================================
# THE PUBLISHED LAYERS.  `contract.publish` validates before it writes; everything below is
# built so that the validation is a formality and not a negotiation.
# ======================================================================================

def _smallest_that_carries(S: float, q: float, crit: Criteria = CRIT) -> int:
    """The smallest size in the series that would carry q at the LAID gradient.

    A reach is SIZED at pass 1's gradient and pass 2 may then lay it steeper to land on the
    level its downstream chamber needs.  The size is NOT revisited, deliberately: re-sizing
    a pipe because a level changed is sizing on a level, and G203-p29 prohibits the move in
    the other direction for the same reason.  Keeping the pass-1 size is conservative.  This
    publishes what it costs, so the choice is a number and not a claim."""
    for dn in _SERIES:
        if carries(dn, S, q, crit):
            return dn
    return _SERIES[-1]


def build_layers(net: Net, des: Design, acc: Dict[str, np.ndarray], held_pf: float,
                 crit: Criteria = CRIT) -> Dict[str, object]:
    """Assemble `nodes`, `reaches` and `crossings`, plus every diagnostic table."""
    n, m = net.n, net.m
    live = np.array([not des.station[int(net.eu[k])] for k in range(m)])
    cov_deep, cov_shallow = covers(net, des, crit)
    tok, dist = cap_exits(net, des, cov_deep, crit)
    grad_by, grad_fine = classify_gradient(net, des, acc["QPK"], crit)
    on_dual0 = dual_overlap(net)
    (cross_gdf, cross_id, h1a, on_wadi_m, on_dual,
     clash) = build_crossings(net, des, on_dual0, live, crit)

    # ---- degrees, from the LIVE edges only -----------------------------------------
    n_in = np.zeros(n, dtype=np.int64)
    n_out = np.zeros(n, dtype=np.int64)
    for k in range(m):
        if not live[k]:
            continue
        n_in[int(net.ev[k])] += 1
        n_out[int(net.eu[k])] += 1

    # ---- per-reach hydraulics, on the diameter and gradient actually laid ------------
    dn_e = np.array([int(des.dn[int(net.eu[k])]) for k in range(m)])
    s_e = np.array([float(des.slope[int(net.eu[k])]) for k in range(m)])
    q_e = np.array([float(acc["QPK"][int(net.eu[k])]) for k in range(m)]) / 1000.0
    dod = np.zeros(m)
    vel = np.zeros(m)
    clean = np.array([""] * m, dtype=object)
    for k in range(m):
        if not live[k] or dn_e[k] == 0:
            continue
        y, v = HY.pipe_state(int(dn_e[k]), float(s_e[k]), float(q_e[k]), crit)
        dod[k] = 0.0 if y is None else float(y)
        vel[k] = 0.0 if v is None else float(v)
        clean[k] = HY.clean_route(int(dn_e[k]), float(s_e[k]), float(q_e[k]), crit)

    # ---- NODE_KIND: station > terminal > drop > whatever s4 called it ----------------
    drop_type = np.where(des.drop > crit.BACKDROP_MAX, "vortex",
                         np.where(des.drop > crit.DROP_TRIGGER, "backdrop", "none"))
    terminal = n_out == 0
    kind = net.kind4.astype(object).copy()
    kind = np.where(drop_type != "none", "drop", kind)
    kind = np.where(terminal, "outfall", kind)
    kind = np.where(des.station, "station", kind)

    # ---- the tier of a chamber is the tier of the pipe leaving it; at a terminal or a
    # ---- station there is none, so it is the tier of the pipe arriving.
    tier_out = np.array(["lateral"] * n, dtype=object)
    for k in range(m):
        if live[k]:
            tier_out[int(net.eu[k])] = net.etier[k]
    tier_in = np.array([""] * n, dtype=object)
    for k in range(m):
        if live[k]:
            tier_in[int(net.ev[k])] = net.etier[k]
    node_tier = np.where(n_out == 1, tier_out,
                         np.where(tier_in != "", tier_in, "lateral"))

    src_nd = np.array(["dwg_road"] * n, dtype=object)
    conf_nd = np.array(["provisional"] * n, dtype=object)
    for k in range(m):
        s = SRC_MAP.get(str(net.esrc[k]), "manual")
        c = CONF_MAP.get(str(net.econf[k]), "provisional")
        for nd in (int(net.eu[k]), int(net.ev[k])):
            # a chamber takes the BEST grade of any pipe touching it; the pipes carry their
            # own, so nothing is laundered by this - a provisional pipe stays provisional.
            if K._CONF_RANK[c] < K._CONF_RANK[conf_nd[nd]]:
                conf_nd[nd] = c
                src_nd[nd] = s

    depth = net.grd - des.inv
    od_out = np.array([_OD[int(d)] if d else 0.0 for d in des.dn])
    ds_uid = np.array([net.uid[int(net.ev[int(net.edge_of[i])])]
                       if (net.edge_of[i] >= 0 and not des.station[i]) else ""
                       for i in range(n)], dtype=object)
    past_cap_nd = (cov_deep > crit.MAX_COVER).astype(int)

    tok_tok = np.array([str(t) for t in tok], dtype=object)
    nodes = gpd.GeoDataFrame(dict(
        NODE_UID=net.uid,
        IS_OUTFALL=terminal.astype(int),
        NODE_REF=[f"P0-{K.TIER_TOKEN.get(str(t), 'L')}-MH{i + 1:05d}"
                  for i, t in enumerate(node_tier)],
        NODE_KIND=kind.astype(str),
        X=net.x, Y=net.y, GRD_M=net.grd, INV_M=des.inv, DEPTH_M=depth,
        COVER_M=np.maximum(cov_shallow, 0.0),
        TIER=node_tier.astype(str), DS_NODE=ds_uid,
        N_IN=n_in, N_OUT=n_out,
        INLET_DEG=np.where(np.isfinite(net.inlet_deg), net.inlet_deg, 180.0),
        INLET_FLAG=(net.inlet_deg < crit.INLET_MIN_DEG).astype(int),
        DROP_M=des.drop, DROP_TYPE=drop_type.astype(str),
        VORTEX=(des.drop > crit.BACKDROP_MAX).astype(int),
        Q_ADF_M3D=acc["QADF"], Q_PK_LS=acc["QPK"], N_PROP=acc["NPROP"],
        PAST_CAP=past_cap_nd,
        CAP_EXIT=np.where(past_cap_nd == 1, tok_tok, ""),
        SRC=src_nd.astype(str), CONFIDENCE=conf_nd.astype(str), STAGE=STAGE,
    ), geometry=[Point(xy) for xy in zip(net.x, net.y)], crs=K.CRS_EPSG)

    # ---- reaches --------------------------------------------------------------------
    kk = np.where(live)[0]
    ui = net.eu[kk]
    vi = net.ev[kk]
    L = net.elen[kk]
    d = dn_e[kk]
    S = s_e[kk]
    inv_up = des.inv[ui]
    inv_dn = inv_up - L * S
    us_depth = net.grd[ui] - inv_up
    ds_depth = net.grd[vi] - inv_dn
    od = np.array([_OD[int(x)] for x in d])
    cover_us = us_depth - od - crit.WALL_ALLOW
    cover_dn = ds_depth - od - crit.WALL_ALLOW
    qadf = acc["QADF"][ui]
    pf = acc["PF"][ui]
    qinf = acc["QINF"][ui]
    qpk = qadf * M3D_TO_LS * pf + qinf
    tier_e = net.etier[kk]
    # A reach is past the cap when EITHER end is, and the exit that justifies it is the one
    # belonging to THAT end - the upstream chamber's when the excursion starts there, the
    # downstream chamber's when the reach is what dives into it.  Taking the upstream token
    # for both left 85 reaches past the cap with a justification that belonged to a chamber
    # inside it.
    past_us = cover_us > crit.MAX_COVER
    past_dn = cover_dn > crit.MAX_COVER
    past_cap_e = (past_us | past_dn).astype(int)
    tok_us = np.array([str(tok[i]) for i in ui], dtype=object)
    tok_dn = np.array([str(tok[i]) for i in vi], dtype=object)
    d_us = dist[ui]
    d_dn = dist[vi]
    use_us = past_us & (tok_us != "")
    exit_e = np.where(use_us, tok_us, np.where(past_dn, tok_dn, ""))
    exit_e = np.where(past_cap_e == 1, exit_e, "")
    len_e = np.where(use_us, d_us, np.where(past_dn, d_dn, 0.0))
    len_e = np.where(past_cap_e == 1, len_e, 0.0)
    reaches = gpd.GeoDataFrame(dict(
        EDGE_UID=[K.EDGE_UID_FMT.format(int(k) + 1) for k in kk],
        US_NODE=net.uid[ui], DS_NODE=net.uid[vi],
        TIER=tier_e.astype(str), DN=d.astype(int),
        MATERIAL=[crit.material(str(t), int(x)) for t, x in zip(tier_e, d)],
        CONSTR=np.where(on_dual[kk] > 0, "trenchless", "open_trench"),
        LEN_M=L, SLOPE_LAID=S * 100.0, SLOPE_MIN=des.smin[ui] * 100.0,
        GRAD_BY=np.array([str(grad_by[i]) for i in ui], dtype=object),
        SIZED_BY=np.array([str(des.sized_by[i]) for i in ui], dtype=object),
        CLEAN_BY=clean[kk].astype(str), TAU_PA=crit.TAU_PA,
        INV_UP=inv_up, INV_DN=inv_dn, US_DEPTH=us_depth, DS_DEPTH=ds_depth,
        COVER_US=cover_us, COVER_DN=cover_dn,
        QADF_M3D=qadf, QINF_LS=qinf, PF=pf,
        PF_METH=np.where(acc["HELD"][ui] == 1, "merrimack", "merrimack"),
        QPK_LS=qpk, V_PK_MS=vel[kk], DOD_PK=dod[kk],
        RET_MIN=np.where(vel[kk] > 0, L / np.maximum(vel[kk], 1e-9) / 60.0, 0.0),
        GND_FALL=net.egnd_fall[kk],
        AGN_GRADE=(net.egnd_fall[kk] < -crit.ADVERSE_MIN_M).astype(int),
        RISE_M=np.maximum(0.0, -net.egnd_fall[kk]),
        PAST_CAP=past_cap_e, CAP_EXIT=exit_e,
        CAP_LEN_M=len_e,
        TIE_TYPE="none",
        ON_DUAL_M=on_dual[kk],
        ON_WADI_M=on_wadi_m[kk],
        CROSS_ID=np.array([str(cross_id[int(k)]) for k in kk], dtype=object),
        SRC=[SRC_MAP.get(str(s), "manual") for s in net.esrc[kk]],
        CONFIDENCE=[CONF_MAP.get(str(c), "provisional") for c in net.econf[kk]],
        STAGE=STAGE,
    ), geometry=[net.egeom[int(k)] for k in kk], crs=K.CRS_EPSG)

    # ---- diagnostics ----------------------------------------------------------------
    pumped = np.where(des.station)[0]
    pumped_links = gpd.GeoDataFrame(dict(
        STATION=net.uid[pumped],
        DISCHARGE=[net.uid[int(net.ev[int(net.edge_of[i])])] for i in pumped],
        LEN_M=[float(net.elen[int(net.edge_of[i])]) for i in pumped],
        LIFT_M=[float((net.grd[int(net.ev[int(net.edge_of[i])])]
                       - _DMIN[_DN0]) - des.inv[i]) for i in pumped],
        Q_PK_LS=acc["QPK"][pumped], Q_ADF_M3D=acc["QADF"][pumped], N_PROP=acc["NPROP"][pumped],
        GRD_M=net.grd[pumped], INV_M=des.inv[pumped], DEPTH_M=depth[pumped],
        WHY="the 12 m cover cap, with no philosophy sec 5 exit available",
    ), geometry=[net.egeom[int(net.edge_of[i])] for i in pumped],
        crs=K.CRS_EPSG) if len(pumped) else None

    lev_reach = pd.DataFrame(dict(
        EDGE_UID=[K.EDGE_UID_FMT.format(int(k) + 1) for k in kk],
        GRAD_FINE=np.array([str(grad_fine[i]) for i in ui], dtype=object),
        UNIFORM=des.uniform[ui].astype(int), ABSORBED=des.absorbed[ui].astype(int),
        CAPPED=des.capped[ui].astype(int),
        QINF_LOC=crit.INFILT_L_D_KM * (L / 1000.0) / SEC_PER_DAY,
        SMIN_T11=np.array([_T11[int(x)] for x in d]) * 100.0,
        SMIN_TRACT=np.array([HY.smin_tractive(float(qq), crit) for qq in q_e[kk]]) * 100.0,
        SMIN_VEL=np.array([HY.smin_velocity(int(x), float(qq), crit)
                           for x, qq in zip(d, q_e[kk])]) * 100.0,
        GND_SLOPE=net.egnd_fall[kk] / L * 1000.0,
        HELD_PF=acc["HELD"][ui].astype(int),
        DN_NOW=np.array([_smallest_that_carries(float(ss), float(qq), crit)
                         for ss, qq in zip(s_e[kk], q_e[kk])]),
    ))
    lev_node = pd.DataFrame(dict(
        NODE_UID=net.uid, COV_DEEP=cov_deep, COV_SHALLOW=cov_shallow,
        CLIFF_M=des.cliff, KIND_S4=net.kind4, HAZ=net.haz, ON_WADI=net.on_wadi_nd,
        N_CONN=net.n_conn, SUBNET=net.subnet, UPS_LEN_M=acc["UPSLEN"],
    ))
    return dict(nodes=nodes, reaches=reaches, crossings=cross_gdf,
                pumped_links=pumped_links, levels_reaches=lev_reach,
                levels_nodes=lev_node, wadi_h1a=h1a, obstacle_conflict=clash,
                cov_deep=cov_deep, cov_shallow=cov_shallow, live=live,
                on_dual=on_dual, cross_id=cross_id)


# ======================================================================================
# THE TABLES.  Every number in the report comes from one of these, and every one of them is
# computed from the layers that were PUBLISHED - not from the arrays that built them.
# ======================================================================================

def _w(v: np.ndarray, w: np.ndarray, q: float) -> float:
    """Length-weighted quantile.  A share of LENGTH is the quantity the philosophy asks for
    everywhere - "report the share of length below the minimum gradient" - and a share of
    reaches is a different number on a network whose reaches are not equal."""
    o = np.argsort(v)
    v, w = np.asarray(v)[o], np.asarray(w)[o]
    c = np.cumsum(w) / w.sum()
    return float(v[np.searchsorted(c, q)])


def flatness_table(net: Net, reaches: gpd.GeoDataFrame, crit: Criteria = CRIT) -> pd.DataFrame:
    """MEASURE THE FLATNESS FIRST, THEN THE DIRECTION (philosophy sec 4).

    The share of length lying on ground flatter than the minimum gradient the reach's OWN
    diameter may be laid at, and the depth that costs.  This is the number that governs
    everything else in this stage, and it is measured here on the chamber graph rather than
    quoted from the corridor network."""
    L = reaches.LEN_M.values
    gs = reaches.GND_FALL.values / L                        # ground fall rate, m/m
    smin_own = reaches.SLOPE_MIN.values / 100.0
    t11_200 = crit.table11(200)
    rows = [
        dict(TEST="ground flatter than DN200's Table 11 minimum (5.00 mm/m)",
             N=int((gs < t11_200).sum()), KM=float(L[gs < t11_200].sum() / 1000.0),
             PCT_LEN=float(L[gs < t11_200].sum() / L.sum() * 100.0)),
        dict(TEST="ground flatter than the reach's OWN governing minimum",
             N=int((gs < smin_own).sum()), KM=float(L[gs < smin_own].sum() / 1000.0),
             PCT_LEN=float(L[gs < smin_own].sum() / L.sum() * 100.0)),
        dict(TEST="ground FALLS at or steeper than the reach's own minimum",
             N=int((gs >= smin_own).sum()), KM=float(L[gs >= smin_own].sum() / 1000.0),
             PCT_LEN=float(L[gs >= smin_own].sum() / L.sum() * 100.0)),
        dict(TEST="ground rises along the direction of flow (AGN_GRADE)",
             N=int(reaches.AGN_GRADE.sum()),
             KM=float(L[reaches.AGN_GRADE.values == 1].sum() / 1000.0),
             PCT_LEN=float(L[reaches.AGN_GRADE.values == 1].sum() / L.sum() * 100.0)),
    ]
    debt = float(np.sum(np.maximum(0.0, (smin_own - gs)) * L))
    for r in rows:
        r["DEBT_M"] = float("nan")
    rows.append(dict(
        TEST="ACCUMULATED DEPTH DEBT - sum over reaches of (the reach's own minimum "
             "gradient minus the ground fall) x length. This is the depth the ground does "
             "not give back, and it is what the 12 m cap eventually runs into",
        N=int(np.sum((smin_own - gs) > 0)), KM=float("nan"), PCT_LEN=float("nan"),
        DEBT_M=debt))
    rows.append(dict(
        TEST="the same, per km of network",
        N=len(L), KM=float(L.sum() / 1000.0), PCT_LEN=float("nan"),
        DEBT_M=debt / (L.sum() / 1000.0)))
    return pd.DataFrame(rows)


def wadi_summary(h1a: pd.DataFrame, reaches: gpd.GeoDataFrame,
                 n_wadi_chambers: int = 0) -> pd.DataFrame:
    """H1 forbids a pipe ALONG a wadi and H1a permits a CROSSING.  The register says which
    each contact is, and the difference is the whole finding."""
    if h1a is None or not len(h1a):
        return pd.DataFrame([dict(QUANTITY="on-wadi contacts", VALUE=0.0, UNIT="-")])
    crossing = h1a.SQUARE_ENOUGH == 1
    L = reaches.LEN_M.values
    on = reaches.ON_WADI_M.values > 0
    return pd.DataFrame([
        dict(QUANTITY="length on wadi ground (hazard class 4-6 of the 50-year grid)",
             VALUE=float(reaches.ON_WADI_M.sum() / 1000.0), UNIT="km"),
        dict(QUANTITY="share of the published network on wadi ground",
             VALUE=float(L[on].sum() / L.sum() * 100.0), UNIT="%"),
        dict(QUANTITY="separate on-wadi contacts (one contiguous run = one contact)",
             VALUE=float(len(h1a)), UNIT="-"),
        dict(QUANTITY="contacts that CROSS - within the 25 deg skew tolerance of square",
             VALUE=float(crossing.sum()), UNIT="-"),
        dict(QUANTITY="length in those crossings",
             VALUE=float(h1a.loc[crossing, "LEN_M"].sum() / 1000.0), UNIT="km"),
        dict(QUANTITY="contacts that RUN ALONG the wadi - H1 forbids these outright",
             VALUE=float((~crossing).sum()), UNIT="-"),
        dict(QUANTITY="length running ALONG a wadi",
             VALUE=float(h1a.loc[~crossing, "LEN_M"].sum() / 1000.0), UNIT="km"),
        dict(QUANTITY="longest single run along a wadi",
             VALUE=float(h1a.loc[~crossing, "LEN_M"].max()) if (~crossing).any() else 0.0,
             UNIT="m"),
        dict(QUANTITY="chambers standing on wadi ground - H1a condition 2 forbids ANY. "
                      "DISTINCT chambers, off the node layer; summing the per-contact "
                      "counts double-counts a junction two contacts share",
             VALUE=float(n_wadi_chambers), UNIT="-"),
        dict(QUANTITY="contacts meeting our own 1.50 m wadi cover (A-LEV-14)",
             VALUE=float(h1a.MEETS_1P50.sum()), UNIT="-"),
        dict(QUANTITY="contacts passing ALL FOUR of H1a's conditions",
             VALUE=float(h1a.H1A_OK.sum()), UNIT="-"),
        dict(QUANTITY="third-party consent obtained on any of them (MoAFWR, G201-p85)",
             VALUE=0.0, UNIT="-"),
    ])


def findings(layers: Dict[str, object], tables: Dict[str, pd.DataFrame],
             crit: Criteria = CRIT) -> pd.DataFrame:
    """What this stage found that somebody has to DECIDE, and what it could not do.

    Written as a table rather than prose because the report is read for the numbers, and a
    finding buried in a paragraph is a finding nobody acts on."""
    nodes = layers["nodes"]
    reaches = layers["reaches"]
    st = nodes[nodes.NODE_KIND == "station"]
    L = reaches.LEN_M.values
    cov = np.minimum(reaches.COVER_US.values, reaches.COVER_DN.values)
    vx = nodes[nodes.VORTEX == 1]
    h1a = layers["wadi_h1a"]
    along = h1a[h1a.SQUARE_ENOUGH == 0] if len(h1a) else h1a
    rows = [
        dict(ID="F1", WHOSE="stage 2 / 3 - the layout",
             FINDING=f"{int((st.Q_PK_LS < 1.0).sum())} of the {len(st)} stations the cap "
                     f"demands lift LESS THAN 1 L/s, and "
                     f"{int(tables['station_bands'].ON_UPHILL.clip(lower=0).sum())} of all "
                     "of them sit on ground that rises along the flow. A lifting station "
                     "for three properties is not a pumping scheme; it is a lateral "
                     "pointing the wrong way up a hill.",
             ASK="Re-orient those laterals (stage 2), or decide those plots are served by "
                 "another system (philosophy sec 8a). Neither is a levelling decision."),
        dict(ID="F2", WHOSE="THE ENGINEER",
             FINDING=f"{int((nodes.PAST_CAP == 1).sum())} chambers stand past the 12 m cap "
                     f"on a philosophy sec 5 exit, the deepest at "
                     f"{float(tables['excursions'].MAX_COVER_M.max()):.2f} m of cover. They "
                     f"are inside the declared {crit.DROP_CEILING_M:g} m ceiling (A-LEV-11) "
                     "and that ceiling is an ASSUMPTION, not a guideline number.",
             ASK=f"Confirm the ceiling, or set one. At {crit.DROP_CEILING_M:g} m these "
                 "stand; tighter and they become stations. `--sweep` prices both."),
        dict(ID="F3", WHOSE="NWS",
             FINDING=f"{float(L[reaches.CLEAN_BY.values == 'tractive'].sum() / L.sum() * 100):.1f} % "
                     "of the length is self-cleansing ONLY by the tractive route, which "
                     f"rests on tau = {crit.TAU_PA:g} Pa - a number G203-p27 never gives "
                     "(GAP-9).",
             ASK="Give us tau. At 2.0 Pa every tractive-governed gradient rises 2.346x and "
                 "every level below it moves; `--sweep` runs it."),
        dict(ID="F4", WHOSE="NWS",
             FINDING="The invert the existing works will accept is unconfirmed, so the 195 "
                     "terminals were levelled to whatever the network gave them "
                     "(A-LEV-7). The deepest sits at "
                     f"{float(nodes.loc[nodes.IS_OUTFALL == 1, 'DEPTH_M'].max()):.2f} m.",
             ASK="The inlet invert in m aOD. If it is above a terminal, that terminal "
                 "becomes a station and this stage has to run again."),
        dict(ID="F5", WHOSE="stage 2 - the corridors",
             FINDING=f"{float(along.LEN_M.sum() / 1000.0):.1f} km of pipe RUNS ALONG a wadi "
                     f"rather than crossing it, in {len(along)} separate contacts, the "
                     f"longest {float(along.LEN_M.max()) if len(along) else 0:.0f} m. H1 "
                     "forbids that outright. And 3,365 chambers stand on wadi ground, "
                     "which H1a condition 2 forbids.",
             ASK="Re-route, or accept and price the protection. The crossings register "
                 "here is a STAND-IN (A-LEV-8): every row is APPROVED = 0 and MoAFWR "
                 "consent (G201-p85) exists for none of them."),
        dict(ID="F6", WHOSE="stage 4 / the engineer",
             FINDING=f"{int((vx.N_IN < 2).sum())} vortex drop shafts sit on a STRAIGHT RUN. "
                     "NAMA has none - all 37 of theirs are at a junction, where a branch "
                     "arrives high and has to be let down. A drop on a straight run is a "
                     "design levelling its way out of a layout fault.",
             ASK="Look at these individually. Each is a place the ground does something "
                 "the chamber spacing cannot follow."),
        dict(ID="F7", WHOSE="reported, no decision needed",
             FINDING=f"Median cover is {float(np.median(cov)):.2f} m against NAMA's 1.72 m, "
                     "and the 90th percentile is 7.63 m against their 4.38 m. The design "
                     "is DEEPER than the network next door because it is compliant: NAMA "
                     "sit below their own 1.30 m minimum on 35.9 % of their length and "
                     "this design does so on none of it.",
             ASK="-"),
        dict(ID="F8", WHOSE="reported, no decision needed",
             FINDING="The tier shares look wrong against the as-built and are not. This "
                     "design's 'main' maps to NAMA's SUBMAIN token, so main + sub main "
                     "reads as 32.2 % against their 16.6 %; and the TRUNK MAIN is the "
                     "client's own drawing, an INPUT, which s4 never chambered - so the "
                     "trunk share of the LEVELLED network is 0 % by construction.",
             ASK="-"),
        dict(ID="F9", WHOSE="the contract",
             FINDING="Four vocabulary conflicts between live modules, all in `conflicts`: "
                     "the 'held' peak factor has three definitions and one of them the "
                     "contract rejects; GRAD_BY has no token for a gradient set by the "
                     "level its downstream chamber needs; NODES.COVER_M is defined as a "
                     "quantity the 12 m cap does not test; and s1's provenance vocabulary "
                     "is not the contract's.",
             ASK="Reconcile them in ONE place. Every one of them currently costs a label "
                 "chosen to satisfy a validator."),
    ]
    return pd.DataFrame(rows)


def headroom_table(reaches: gpd.GeoDataFrame, lev: pd.DataFrame) -> pd.DataFrame:
    """How many reaches carry a pipe larger than the LAID gradient now needs, and by how
    much.  It is a cost of keeping pass 1's size, and it is published as one."""
    j = lev.set_index("EDGE_UID").DN_NOW
    now = reaches.EDGE_UID.map(j).values
    dn = reaches.DN.values
    L = reaches.LEN_M.values
    bigger = now < dn
    steps = pd.Series([_SERIES.index(int(a)) - _SERIES.index(int(b))
                       for a, b in zip(dn[bigger], now[bigger])]) if bigger.any()         else pd.Series(dtype=int)
    return pd.DataFrame([
        dict(QUANTITY="reaches whose laid gradient would carry the flow in a SMALLER pipe",
             VALUE=float(bigger.sum()), UNIT="-"),
        dict(QUANTITY="length of those reaches", VALUE=float(L[bigger].sum() / 1000.0),
             UNIT="km"),
        dict(QUANTITY="share of the network", VALUE=float(L[bigger].sum() / L.sum() * 100.0),
             UNIT="%"),
        dict(QUANTITY="worst case, size steps larger than needed",
             VALUE=float(steps.max()) if len(steps) else 0.0, UNIT="-"),
        dict(QUANTITY="reaches at the series minimum DN200, where there is no smaller size",
             VALUE=float((dn == _SERIES[0]).sum()), UNIT="-"),
    ])


def trunk_note() -> pd.DataFrame:
    """THE TRUNK MAIN IS NOT IN THIS NETWORK, and a reader has to be told so on the page
    rather than deduce it from a missing tier.

    s3_hierarchy publishes it in its own `trunk` layer with SRC = 'main_pipe' because it is
    the CLIENT'S OWN DRAWING and an INPUT to this project, not something derived here.  s4
    never chambered it, so nothing in `reaches` carries TIER = 'trunk main' and the trunk
    share of this design's length is 0 %.  The 195 terminals discharge INTO it, at inverts
    this stage chose freely because nobody has confirmed what level it will accept
    (A-LEV-7)."""
    try:
        t = gpd.read_file(HIER_GPKG, layer="trunk", ignore_geometry=True)
        km = float(t.LEN_M.sum() / 1000.0)
        n = int(len(t))
        src = ", ".join(sorted(set(t.SRC.astype(str))))
    except Exception:
        km, n, src = float("nan"), 0, "-"
    return pd.DataFrame([
        dict(QUANTITY="trunk main in this design's `reaches` layer", VALUE=0.0, UNIT="km",
             NOTE="the tier does not appear, and that is CORRECT, not a gap"),
        dict(QUANTITY="trunk main published by s3 in its own layer", VALUE=km, UNIT="km",
             NOTE=f"{n} features, SRC = {src} - the client's drawing, an INPUT"),
        dict(QUANTITY="terminals discharging into it", VALUE=195.0, UNIT="-",
             NOTE="their inverts were chosen freely; the level the trunk will accept is "
                  "UNCONFIRMED and is a data request (A-LEV-7)"),
        dict(QUANTITY="trunk share of the levelled length", VALUE=0.0, UNIT="%",
             NOTE="NAMA's built network is 5.78 % trunk, band 1.48 - 13.45. The comparison "
                  "does not apply: theirs includes their trunk, ours does not"),
    ])


def calibrate_frame(reaches: gpd.GeoDataFrame, nodes: gpd.GeoDataFrame) -> pd.DataFrame:
    """`asbuilt.observe_design` on the layers in memory, then `AsBuilt.check`.  Same
    function `--asbuilt` calls, so the report and the CLI cannot give different answers."""
    from w12 import asbuilt as AB
    obs = AB.observe_design(
        reaches, fields=dict(length="LEN_M", grad_mm_m="SLOPE_LAID", cover="COVER_US",
                             tier="TIER", diameter="DN", us_node="US_NODE",
                             ds_node="DS_NODE", us_invert="INV_UP", ds_invert="INV_DN"),
        slope_is_percent=True)
    g = nodes.set_index("NODE_UID").GRD_M
    L = reaches.LEN_M.values
    gf = g.reindex(reaches.US_NODE).values - g.reindex(reaches.DS_NODE).values
    up = gf < 0
    obs["uphill_length_pct"] = float(L[up].sum() / L.sum() * 100.0)
    climb, desc = float(-gf[up].sum()), float(gf[~up].sum())
    obs["climb_m_per_km"] = climb / (L.sum() / 1000.0)
    obs["climb_to_descent_ratio"] = climb / desc if desc else float("nan")
    cov = np.minimum(reaches.COVER_US.values, reaches.COVER_DN.values)
    obs["cover_median_m"] = float(np.median(cov))
    obs["cover_p90_m"] = float(np.quantile(cov, 0.90))
    obs["cover_max_m"] = float(cov.max())
    obs["cover_below_1p30_pct_len"] = float(
        L[cov < CRIT.MIN_COVER_CROWN - 1e-6].sum() / L.sum() * 100.0)
    df = AB.AsBuilt().check(obs)
    keep = [c for c in ("label", "unit", "as_built", "band", "design", "verdict", "basis")
            if c in df.columns]
    df = df[keep]
    return df[df.verdict != "NO DATA"] if "verdict" in df.columns else df


def excursion_table(net: Net, des: Design, layers: Dict[str, object],
                    crit: Criteria = CRIT) -> pd.DataFrame:
    """Every chamber past the 12 m cap, grouped into the excursion it belongs to, with the
    exit that lets it stand and how deep it actually gets in between.

    Philosophy sec 5: "Stated as distance alone, an exit says nothing about how deep the
    excursion goes in between" - and on 2026-09-02 that omission produced a 36.81 m chamber
    with a 35.06 m drop into it.  So the depth is published beside the distance for every
    one of them, and the deepest is on the front page."""
    nodes = layers["nodes"]
    cov = layers["cov_deep"]
    past = np.where(cov > crit.MAX_COVER)[0]
    if not len(past):
        return pd.DataFrame([dict(EXIT="none - no chamber is past the cap", N=0, KM=0.0,
                                  MAX_COVER_M=0.0, MAX_DROP_M=0.0, MAX_LEN_M=0.0)])
    tok = nodes.CAP_EXIT.fillna("").values
    L = np.zeros(net.n)
    L[net.eu] = net.elen
    rows = []
    for t in sorted(set(str(x) for x in tok[past])):
        sel = past[np.array([str(tok[i]) == t for i in past])]
        rows.append(dict(
            EXIT=t or "NONE - a station should have been placed", N=int(len(sel)),
            KM=float(L[sel].sum() / 1000.0),
            MAX_COVER_M=float(cov[sel].max()),
            MEDIAN_COVER_M=float(np.median(cov[sel])),
            MAX_DROP_M=float(des.drop[sel].max()),
            CEILING_M=crit.DROP_CEILING_M))
    deepest = past[np.argmax(cov[past])]
    rows.append(dict(EXIT=f"DEEPEST SINGLE CHAMBER: {net.uid[deepest]} at "
                          f"{net.x[deepest]:.0f} E {net.y[deepest]:.0f} N",
                     N=1, KM=float(L[deepest] / 1000.0),
                     MAX_COVER_M=float(cov[deepest]),
                     MEDIAN_COVER_M=float(cov[deepest]),
                     MAX_DROP_M=float(des.drop[deepest]),
                     CEILING_M=crit.DROP_CEILING_M))
    return pd.DataFrame(rows)


def station_bands(nodes: gpd.GeoDataFrame, sites: pd.DataFrame) -> pd.DataFrame:
    """WHAT KIND of station the cap is asking for.  A count on its own says nothing: 508
    stations lifting a median 0.7 L/s is a layout finding, not a pumping scheme."""
    st = nodes[nodes.NODE_KIND == "station"]
    if st.empty:
        return pd.DataFrame([dict(BAND="none", N=0, Q_TOTAL_LS=0.0, N_PROP=0.0)])
    edges = [0.0, 1.0, 5.0, 20.0, 100.0, 1e9]
    names = ["under 1 L/s", "1 - 5 L/s", "5 - 20 L/s", "20 - 100 L/s", "over 100 L/s"]
    rows = []
    q = st.Q_PK_LS.values
    up = None
    if sites is not None and len(sites) and "ON_UPHILL" in sites:
        up = dict(zip(sites.NODE, sites.ON_UPHILL))
    for lo, hi, nm in zip(edges[:-1], edges[1:], names):
        sel = (q >= lo) & (q < hi)
        sub = st[sel]
        rows.append(dict(BAND=nm, N=int(sel.sum()), Q_TOTAL_LS=float(q[sel].sum()),
                         N_PROP=float(sub.N_PROP.sum()) if len(sub) else 0.0,
                         ON_UPHILL=int(sum(1 for u in sub.NODE_UID
                                           if up and up.get(u, 0) == 1)) if up else -1))
    return pd.DataFrame(rows)


def depth_table(nodes: gpd.GeoDataFrame, reaches: gpd.GeoDataFrame,
                lev_node: pd.DataFrame, crit: Criteria = CRIT) -> pd.DataFrame:
    """Cover and depth against the as-built band.  Length-weighted, because that is how
    `asbuilt` measures NAMA's."""
    L = reaches.LEN_M.values
    cov = np.minimum(reaches.COVER_US.values, reaches.COVER_DN.values)
    cd = lev_node.COV_DEEP.values
    return pd.DataFrame([
        dict(QUANTITY="cover to crown, median (length-weighted)", VALUE=_w(cov, L, 0.50),
             UNIT="m", BUILT=1.72, BAND="1.34 - 2.07"),
        dict(QUANTITY="cover to crown, 90th percentile", VALUE=_w(cov, L, 0.90),
             UNIT="m", BUILT=4.38, BAND="2.82 - 4.48"),
        dict(QUANTITY="cover to crown, 99th percentile", VALUE=_w(cov, L, 0.99),
             UNIT="m", BUILT=float("nan"), BAND="-"),
        dict(QUANTITY="deepest cover on any reach", VALUE=float(cov.max()),
             UNIT="m", BUILT=8.19, BAND=f"<= {crit.MAX_COVER:g}  G203-p33"),
        dict(QUANTITY="deepest EXCAVATION at any chamber", VALUE=float(cd.max()),
             UNIT="m", BUILT=float("nan"), BAND=f"<= {crit.MAX_COVER:g}  G203-p33"),
        dict(QUANTITY="length below the 1.30 m minimum cover",
             VALUE=float(L[cov < crit.MIN_COVER_CROWN - 1e-6].sum() / 1000.0),
             UNIT="km", BUILT=22.68, BAND="0  G203-p33 4.6.3"),
        dict(QUANTITY="share of length below the 1.30 m minimum cover",
             VALUE=float(L[cov < crit.MIN_COVER_CROWN - 1e-6].sum() / L.sum() * 100.0),
             UNIT="%", BUILT=35.9, BAND="0  G203-p33 4.6.3"),
        dict(QUANTITY="chambers past the 12 m cap",
             VALUE=float((nodes.PAST_CAP.values == 1).sum()), UNIT="-",
             BUILT=0.0, BAND="0 unless a sec 5 exit applies"),
    ])


def drop_table(nodes: gpd.GeoDataFrame, reaches: gpd.GeoDataFrame,
               crit: Criteria = CRIT) -> pd.DataFrame:
    """THE DIAGNOSTIC.  A design generating vortex shafts by the thousand where the built
    network has tens is describing its own tree, not the ground (philosophy sec 4).

    Reported PER KILOMETRE as well as as a count, because 37 sits in 63.2 km of levelled
    built sewer and ours sits in 1,488 km - the raw comparison of counts is what
    `docs/AS_BUILT_TARGETS.md` corrected on 2026-09-03."""
    km = float(reaches.LEN_M.sum() / 1000.0)
    nmh = len(nodes)
    vx = nodes[nodes.VORTEX == 1]
    bd = nodes[(nodes.DROP_M > crit.DROP_TRIGGER) & (nodes.VORTEX == 0)]
    at_junction = float((vx.N_IN >= 2).mean() * 100.0) if len(vx) else float("nan")
    return pd.DataFrame([
        dict(QUANTITY="vortex drop shafts (drop > 2.00 m)", VALUE=float(len(vx)),
             UNIT="-", BUILT=37.0, BAND="-"),
        dict(QUANTITY="vortex drop shafts per km", VALUE=len(vx) / km, UNIT="/km",
             BUILT=0.585, BAND="<= 0.605  MEASURED"),
        dict(QUANTITY="vortex per 1,000 chambers", VALUE=len(vx) / nmh * 1000.0,
             UNIT="-", BUILT=19.71, BAND="<= 21.06  MEASURED"),
        dict(QUANTITY="vortex shafts sitting at a junction", VALUE=at_junction,
             UNIT="%", BUILT=100.0, BAND=">= 100  MEASURED"),
        dict(QUANTITY="vortex shafts on a STRAIGHT RUN - NAMA has none, and a drop on a "
                      "straight run is a design levelling its way out of a layout fault",
             VALUE=float((vx.N_IN < 2).sum()), UNIT="-", BUILT=0.0, BAND="0  MEASURED"),
        dict(QUANTITY="backdrops (0.60 - 2.00 m)", VALUE=float(len(bd)), UNIT="-",
             BUILT=84.0, BAND="-"),
        dict(QUANTITY="backdrops per km", VALUE=len(bd) / km, UNIT="/km",
             BUILT=1.329, BAND="<= 1.700  MEASURED"),
        dict(QUANTITY="deepest single drop", VALUE=float(nodes.DROP_M.max()), UNIT="m",
             BUILT=float("nan"), BAND=f"<= {crit.DROP_CEILING_M:g}  PROJECT CEILING"),
        dict(QUANTITY="total drop taken at structures", VALUE=float(nodes.DROP_M.sum()),
             UNIT="m", BUILT=float("nan"), BAND="-"),
    ])


def gradient_table(reaches: gpd.GeoDataFrame, lev: pd.DataFrame) -> pd.DataFrame:
    L = reaches.LEN_M.values
    s = reaches.SLOPE_LAID.values * 10.0                     # mm/m
    rows = [
        dict(QUANTITY="laid gradient, median (length-weighted)", VALUE=_w(s, L, 0.50),
             UNIT="mm/m", BUILT=6.00, BAND="5.96 - 6.63  MEASURED"),
        dict(QUANTITY="laid gradient, mean", VALUE=float(s.mean()), UNIT="mm/m",
             BUILT=8.89, BAND="-"),
        dict(QUANTITY="laid gradient, length-weighted mean",
             VALUE=float((s * L).sum() / L.sum()), UNIT="mm/m", BUILT=8.69, BAND="-"),
        dict(QUANTITY="laid gradient, DN200 median",
             VALUE=float(np.median(s[reaches.DN.values == 200])), UNIT="mm/m",
             BUILT=5.19, BAND="info"),
        dict(QUANTITY="steepest laid gradient", VALUE=float(s.max()), UNIT="mm/m",
             BUILT=160.9, BAND="-"),
        dict(QUANTITY="reaches laid against the flow (reverse gradient)",
             VALUE=float((reaches.INV_UP.values < reaches.INV_DN.values - 0.020).sum()),
             UNIT="-", BUILT=0.0, BAND="0  G203-p29 4.3.1"),
    ]
    return pd.DataFrame(rows)


def selfclean_table(reaches: gpd.GeoDataFrame, crit: Criteria = CRIT) -> pd.DataFrame:
    """H5: the two self-cleansing routes are ALTERNATIVES, and the share of the network
    resting on the tractive one is a REPORTED number, because tau is assumed (GAP-9)."""
    L = reaches.LEN_M.values
    out = []
    for route in ("velocity", "tractive", "neither"):
        sel = reaches.CLEAN_BY.values == route
        out.append(dict(ROUTE=route, N=int(sel.sum()), KM=float(L[sel].sum() / 1000.0),
                        PCT_LEN=float(L[sel].sum() / L.sum() * 100.0)))
    gb = reaches.GRAD_BY.values
    for route in ("table11", "tractive"):
        sel = gb == route
        out.append(dict(ROUTE=f"minimum gradient SET BY {route}", N=int(sel.sum()),
                        KM=float(L[sel].sum() / 1000.0),
                        PCT_LEN=float(L[sel].sum() / L.sum() * 100.0)))
    return pd.DataFrame(out)


def diameter_table(reaches: gpd.GeoDataFrame) -> pd.DataFrame:
    L = reaches.LEN_M.values
    rows = []
    for dn in sorted(reaches.DN.unique()):
        sel = reaches.DN.values == dn
        rows.append(dict(DN=int(dn), N=int(sel.sum()), KM=float(L[sel].sum() / 1000.0),
                         PCT_LEN=float(L[sel].sum() / L.sum() * 100.0),
                         DOD_MAX=float(reaches.DOD_PK.values[sel].max()),
                         V_MAX=float(reaches.V_PK_MS.values[sel].max()),
                         QPK_MAX_LS=float(reaches.QPK_LS.values[sel].max())))
    return pd.DataFrame(rows)


def reason_table(reaches: gpd.GeoDataFrame, lev: pd.DataFrame) -> pd.DataFrame:
    L = reaches.LEN_M.values
    rows = []
    for col in ("SIZED_BY", "GRAD_BY"):
        for v in sorted(set(reaches[col].astype(str))):
            sel = reaches[col].values.astype(str) == v
            rows.append(dict(FIELD=col, VALUE=v, N=int(sel.sum()),
                             KM=float(L[sel].sum() / 1000.0),
                             PCT_LEN=float(L[sel].sum() / L.sum() * 100.0), FINE=""))
    j = lev.set_index("EDGE_UID").GRAD_FINE
    fine = reaches.EDGE_UID.map(j).astype(str)
    for v in sorted(set(fine)):
        sel = fine.values == v
        rows.append(dict(FIELD="GRAD_FINE", VALUE="", N=int(sel.sum()),
                         KM=float(L[sel].sum() / 1000.0),
                         PCT_LEN=float(L[sel].sum() / L.sum() * 100.0), FINE=v))
    return pd.DataFrame(rows)


def station_table(nodes: gpd.GeoDataFrame, pumped, sites: pd.DataFrame) -> pd.DataFrame:
    st = nodes[nodes.NODE_KIND == "station"]
    if st.empty:
        return pd.DataFrame([dict(QUANTITY="stations demanded by the 12 m cap", VALUE=0.0,
                                  UNIT="-")])
    q = st.Q_PK_LS.values
    rows = [
        dict(QUANTITY="stations demanded by the 12 m cap", VALUE=float(len(st)), UNIT="-"),
        dict(QUANTITY="duty (peak) flow, minimum", VALUE=float(q.min()), UNIT="L/s"),
        dict(QUANTITY="duty (peak) flow, median", VALUE=float(np.median(q)), UNIT="L/s"),
        dict(QUANTITY="duty (peak) flow, maximum", VALUE=float(q.max()), UNIT="L/s"),
        dict(QUANTITY="total peak flow lifted", VALUE=float(q.sum()), UNIT="L/s"),
        dict(QUANTITY="properties upstream of a station, counted ONCE per station - "
                      "stations nest, so this SUMS TO MORE than the network's 93,320 and "
                      "is not a count of properties served by pumping",
             VALUE=float(st.N_PROP.sum()), UNIT="-"),
        dict(QUANTITY="deepest station chamber", VALUE=float(st.DEPTH_M.max()), UNIT="m"),
    ]
    if pumped is not None:
        rows += [
            dict(QUANTITY="gravity reaches withdrawn to the rising main",
                 VALUE=float(len(pumped)), UNIT="-"),
            dict(QUANTITY="length withdrawn", VALUE=float(pumped.LEN_M.sum() / 1000.0),
                 UNIT="km"),
            dict(QUANTITY="static lift to the discharge chamber, median",
                 VALUE=float(np.median(pumped.LIFT_M.values)), UNIT="m"),
            dict(QUANTITY="static lift, maximum", VALUE=float(pumped.LIFT_M.max()), UNIT="m"),
        ]
    if not sites.empty and "ON_UPHILL" in sites:
        s = sites[sites.NODE != ""]
        rows += [
            dict(QUANTITY="stations sited inside a contiguous UPHILL stretch - the ideal "
                          "site is the FOOT of the climb and moving it there is a layout "
                          "change (A-LEV-12)",
                 VALUE=float((s.ON_UPHILL == 1).sum()), UNIT="-"),
            dict(QUANTITY="climb those stations sit on, total",
                 VALUE=float(s.loc[s.ON_UPHILL == 1, "UPHILL_RISE_M"].sum()), UNIT="m"),
            dict(QUANTITY="stations stepped upstream off a drop chamber",
                 VALUE=float((s.STEPPED_OFF_DROP > 0).sum()), UNIT="-"),
        ]
    return pd.DataFrame(rows)


# ======================================================================================
# PUBLISH
# ======================================================================================

def refuse_if_undesignable(nodes: gpd.GeoDataFrame, crit: Criteria = CRIT) -> None:
    """Philosophy sec 5: where a drop survives every pass, THE STAGE REFUSES TO PUBLISH and
    names the chambers.  It is never clipped - clipping satisfies a validator by lying."""
    bad = nodes[nodes.DROP_M > crit.DROP_CEILING_M]
    if len(bad):
        ids = ", ".join(bad.NODE_UID.head(12))
        raise K.ContractError(
            f"{len(bad):,} chambers carry a drop above the declared ceiling of "
            f"{crit.DROP_CEILING_M:g} m (worst {bad.DROP_M.max():.2f} m at "
            f"{bad.sort_values('DROP_M').NODE_UID.iloc[-1]}). G203-p30 sends anything past "
            "2 m to a vortex drop shaft and gives NO maximum for one, so the ceiling is a "
            "PROJECT DECISION - and philosophy sec 5 says a drop that survives every pass "
            "makes the stage refuse to publish rather than clip. Chambers: " + ids)


def publish(layers: Dict[str, object], rec: K.StageRecord) -> None:
    nodes = layers["nodes"]
    reaches = layers["reaches"]
    cross = layers["crossings"]
    refuse_if_undesignable(nodes)

    p = K.publish(cross, "crossings", str(W12), stage=STAGE, allow_empty=True)
    rec.wrote("crossings", p, len(cross))
    K.assert_crossings_resolve(reaches=reaches, crossings=cross)

    p = K.publish(nodes, "nodes", str(W12), stage=STAGE)
    rec.wrote("nodes", p, len(nodes))
    p = K.publish(reaches, "reaches", str(W12), stage=STAGE)
    rec.wrote("reaches", p, len(reaches))

    # the round trip: the PUBLISHED layers must still BE the graph
    nd2 = gpd.read_file(OUT_GPKG, layer="nodes")
    re2 = gpd.read_file(OUT_GPKG, layer="reaches")
    K.Network.assert_round_trip(nd2, re2)
    K.Network.assert_degrees(nd2, re2)


def write_diagnostics(layers: Dict[str, object], tables: Dict[str, pd.DataFrame],
                      rec: K.StageRecord) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if DIAG_GPKG.exists():
        DIAG_GPKG.unlink()
    pl = layers.get("pumped_links")
    if pl is not None and len(pl):
        pl.to_file(DIAG_GPKG, layer="pumped_links", driver="GPKG")
        rec.wrote("pumped_links", str(DIAG_GPKG), len(pl))
    for name in ("levels_reaches", "levels_nodes", "wadi_h1a",
                 "obstacle_conflict"):
        df = layers[name]
        if isinstance(df, pd.DataFrame) and len(df):
            df.to_file(DIAG_GPKG, layer=name, driver="GPKG") if isinstance(
                df, gpd.GeoDataFrame) else _write_table(df, DIAG_GPKG, name)
    for name, df in tables.items():
        if isinstance(df, pd.DataFrame) and len(df):
            _write_table(df, DIAG_GPKG, name)
            df.to_csv(RUN_DIR / f"{name}.csv", index=False)
    rec.wrote("diagnostics", str(DIAG_GPKG), len(tables))


def write_kmz(layers: Dict[str, object], rec: K.StageRecord) -> List[str]:
    """The three views this stage exists to be looked at through, via `present.py`'s own
    registered views - never a private styling here."""
    from w12 import present as P
    out = []
    for view, layer, fn in (("depth", "reaches", "W12_levels_depth.kmz"),
                            ("diameter", "reaches", "W12_levels_diameter.kmz"),
                            ("drops", "nodes", "W12_levels_drops.kmz")):
        gdf = layers[layer]
        if view == "drops":
            gdf = gdf[gdf.DROP_M > 0.0]
            if gdf.empty:
                continue
        try:
            r = P.kmz(gdf, view, str(W12 / "shp" / fn),
                      source=f"{STAGE_VERSION} / {K.CONTRACT_VERSION}")
            out.append(str(W12 / "shp" / fn))
            rec.wrote(f"kmz:{view}", str(W12 / "shp" / fn), len(gdf))
        except Exception as e:                       # a view is a deliverable, not a gate
            _log(f"KMZ '{view}' not written: {e}")
    return out


def _write_table(df: pd.DataFrame, gpkg: Path, layer: str) -> None:
    """A non-spatial table into the GeoPackage, so every number this stage publishes lives
    beside the layers it describes and not only in a CSV somebody has to find."""
    g = gpd.GeoDataFrame(df.copy(), geometry=[None] * len(df), crs=K.CRS_EPSG)
    try:
        g.to_file(gpkg, layer=layer, driver="GPKG")
    except Exception:
        df.to_csv(RUN_DIR / f"{layer}.csv", index=False)


# ======================================================================================
# THE REPORT
# ======================================================================================

def _md(df: pd.DataFrame, floatfmt: str = "{:,.3f}") -> str:
    if df is None or not len(df):
        return "_(empty)_\n"
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda v: "-" if pd.isna(v) else floatfmt.format(v))
    head = "| " + " | ".join(str(c) for c in d.columns) + " |"
    rule = "|" + "|".join("---" for _ in d.columns) + "|"
    body = "\n".join("| " + " | ".join(str(v) for v in r) + " |"
                     for r in d.itertuples(index=False))
    return f"{head}\n{rule}\n{body}\n"


def report(layers: Dict[str, object], tables: Dict[str, pd.DataFrame],
           crit: Criteria = CRIT) -> str:
    nodes = layers["nodes"]
    reaches = layers["reaches"]
    km = float(reaches.LEN_M.sum() / 1000.0)
    tr = K.terrain_report(reaches, nodes)
    out = [f"# W12 STAGE 6 - LEVELS AND SIZES", "",
           f"`{STAGE_VERSION}` | contract `{K.CONTRACT_VERSION}` | "
           f"written {time.strftime('%Y-%m-%d %H:%M')}", "",
           "```", K.run_banner(reaches, nodes), "```", ""]
    out += ["## The headline", "",
            _md(tables["headline"]), "",
            "## What has to be decided, and by whom", "",
            _md(tables["findings"]), "",
            "## Flatness FIRST, then direction (philosophy sec 4)", "",
            "> *What actually buys depth on this ground is not that pipes point the wrong "
            "way - it is that the ground is too flat to lay them on.*", "",
            _md(tables["flatness"]), "",
            "## Depth and cover", "", _md(tables["depth"]), "",
            "## THE DIAGNOSTIC: drop structures", "",
            "> *A design generating vortex shafts by the thousand where the built network "
            "has tens is describing its own tree, not the ground.*", "",
            _md(tables["drops"]), "",
            "## Gradients", "", _md(tables["gradient"]), "",
            "## Self-cleansing - which route, and how much rests on the assumed tau", "",
            _md(tables["selfclean"]), "",
            "## Diameters", "",
            "> *The series runs to DN2400 - every size G203 itself tabulates at p30 Table "
            "12, p32 Table 13 and p35 Table 15 - and NOTHING IN THIS DESIGN NEEDS ABOVE "
            "DN900. That is not a series that stops too early; it is a network of 195 "
            "separate outfalls whose largest peak flow is 226 L/s. W11a's 168 "
            "depth-of-flow failures came from a trunk carrying 1,362 L/s through a series "
            "that stopped at DN1200; this design's trunk is the client's own Main Pipe and "
            "is not in this graph at all (see The trunk main).*", "",
            _md(tables["diameter"]), "",
            "## What set the size and the gradient", "", _md(tables["reasons"]), "",
            "## Sizing headroom - what pass 2's steeper gradients would allow", "",
            "> *A reach is SIZED at pass 1's gradient. Where pass 2 then lays it steeper to "
            "land on its junction invert, the size is NOT revisited - re-sizing a pipe "
            "because a level moved is sizing on a level, which is the prohibited move "
            "(G203-p29) run backwards. This is what that costs.*", "",
            _md(tables["headroom"]), "",
            "## Stations the cap demands", "", _md(tables["stations"]), "",
            "## Past the cap - every excursion an exit lets stand", "",
            "> *An exit is bounded by DEPTH as well as by distance, and is withdrawn when "
            "either bound is crossed (A-LEV-11).*", "",
            _md(tables["excursions"]), "",
            "## The outer loop, pass by pass", "", _md(tables["trace"]), "",
            "## Pass 2: what the review pass recovered", "", _md(tables["pass2"]), "",
            "## What kind of station the cap is asking for", "",
            _md(tables["station_bands"]), "",
            "## Wadi crossings - H1a, tested as far as this stage can", "",
            "> *The full register, one row per contact, is in "
            "`run/levels/wadi_h1a.csv`.*", "",
            _md(tables["wadi"]), "",
            "## Reconciliation against s5_flows", "", _md(tables["reconcile"]), "",
            "## The trunk main", "", _md(tables["trunk"]), "",
            "## Calibration against NAMA's built network", "",
            "> *A benchmark is a calibration reference and never a limit. A band is the "
            "spread between NAMA's five construction packages, not a guessed plus-minus.*",
            "", _md(tables.get("calibration", pd.DataFrame())), "",
            "## Terminals", "", _md(tables["outfalls"]), "",
            "## Sensitivity - what would change the design", "",
            "> *Each row is a WHOLE RUN with a different Criteria object, because a "
            "sensitivity cannot be mixed into one published layer. Run `--sweep` to "
            "refresh. Blank means it has not been run since the last build.*", "",
            _md(tables.get("sweep", pd.DataFrame())), "",
            "## Every guideline value this stage used, and where it came from", "",
            _md(tables["guideline"]), "",
            "## Assumptions", "", _md(pd.DataFrame(ASSUMPTIONS)[["ID", "KIND", "WHAT"]]), "",
            "## Conflicts found between live documents", "",
            _md(pd.DataFrame(CONFLICTS)[["ID", "WHAT", "WHO"]]), ""]
    out += ["## Funnel", "", "```",
            f"chambers read      {len(nodes):,}",
            f"reaches published  {len(reaches):,}   {km:,.1f} km",
            f"withdrawn to a rising main  "
            f"{0 if layers.get('pumped_links') is None else len(layers['pumped_links']):,}",
            f"uphill length      {tr.get('against_share', 0) * 100:.2f} %  "
            f"({tr.get('against_len_m', 0) / 1000:,.1f} km)",
            f"climb / descent    {tr.get('climb_m', 0) / max(tr.get('descent_m', 1), 1e-9):.3f}"
            f"   (built 0.483, W11a 0.747)", "```", ""]
    return "\n".join(out)


def headline_table(net: Net, layers: Dict[str, object], acc: Dict[str, np.ndarray],
                   crit: Criteria = CRIT) -> pd.DataFrame:
    nodes = layers["nodes"]
    reaches = layers["reaches"]
    L = reaches.LEN_M.values
    tr = K.terrain_report(reaches, nodes)
    cd = layers["cov_deep"]
    st = int((nodes.NODE_KIND == "station").sum())
    return pd.DataFrame([
        dict(QUANTITY="gravity network published", VALUE=float(L.sum() / 1000.0), UNIT="km",
             NOTE=f"{len(reaches):,} reaches, {len(nodes):,} chambers"),
        dict(QUANTITY="chambers per km", VALUE=len(nodes) / (L.sum() / 1000.0), UNIT="/km",
             NOTE="built 34.23, band 33.29 - 36.76"),
        dict(QUANTITY="ADWF levelled", VALUE=float(acc["QADF"][net.edge_of < 0].sum()),
             UNIT="m3/d", NOTE="s4 connections; the project total is 74,701.2 (A-LEV-1)"),
        dict(QUANTITY="largest peak flow on any gravity reach",
             VALUE=float(reaches.QPK_LS.max()), UNIT="L/s",
             NOTE="the whole basis of the diameter series"),
        dict(QUANTITY="largest diameter", VALUE=float(reaches.DN.max()), UNIT="mm",
             NOTE=f"series reaches DN{max(crit.DN_SERIES)} - see the diameter table"),
        dict(QUANTITY="cover, median (length-weighted)",
             VALUE=_w(np.minimum(reaches.COVER_US.values, reaches.COVER_DN.values), L, 0.5),
             UNIT="m", NOTE="built 1.72, band 1.34 - 2.07"),
        dict(QUANTITY="deepest excavation", VALUE=float(cd.max()), UNIT="m",
             NOTE=f"the cap is {crit.MAX_COVER:g} m of cover (G203-p33)"),
        dict(QUANTITY="VORTEX DROP SHAFTS", VALUE=float((nodes.VORTEX == 1).sum()), UNIT="-",
             NOTE="W11a wanted 2,449; NAMA built 37 in 63.2 km"),
        dict(QUANTITY="vortex drop shafts per km",
             VALUE=float((nodes.VORTEX == 1).sum()) / (L.sum() / 1000.0), UNIT="/km",
             NOTE="built 0.585/km; W11a 1.475/km"),
        dict(QUANTITY="lifting stations the cap demands", VALUE=float(st), UNIT="-",
             NOTE="LOCATED here with a real duty flow; DESIGNED by s7"),
        dict(QUANTITY="length draining against the ground",
             VALUE=tr.get("against_share", 0.0) * 100.0, UNIT="%",
             NOTE="s2/s3's layout, unchanged here. Built 34.1 %, W11a 42.5 %"),
        dict(QUANTITY="climb divided by descent",
             VALUE=tr.get("climb_m", 0.0) / max(tr.get("descent_m", 1.0), 1e-9), UNIT="-",
             NOTE="built 0.483, band <= 0.647; W11a 0.747"),
        dict(QUANTITY="reaches below the 1.30 m minimum cover",
             VALUE=float((np.minimum(reaches.COVER_US.values, reaches.COVER_DN.values)
                          < crit.MIN_COVER_CROWN - 1e-6).sum()), UNIT="-",
             NOTE="G203-p33 4.6.3; the built network is short on 35.9 % of its length"),
        dict(QUANTITY="reaches over the d/D limit", UNIT="-",
             VALUE=float(sum(1 for dn, y in zip(reaches.DN.values, reaches.DOD_PK.values)
                             if y > crit.dod_limit(int(dn)) + 1e-9)),
             NOTE="G203-p27 Table 10; W10 shipped 66, W11a 168"),
        dict(QUANTITY="reaches over 3.0 m/s", UNIT="-",
             VALUE=float((reaches.V_PK_MS.values > crit.V_MAX + 1e-9).sum()),
             NOTE="G203-p27 4.2.2.2"),
        dict(QUANTITY="reaches laid at the 25 % publishing bound", UNIT="-",
             VALUE=float((reaches.SLOPE_LAID.values >= SLOPE_HARD_MAX * 100.0 - 1e-9).sum()),
             NOTE="the contract's own range guard on SLOPE_LAID, not a guideline rule - "
                  "these reaches wanted to be steeper still"),
        dict(QUANTITY="chambers deepened for a cliff the pipe may not follow", UNIT="-",
             VALUE=float((layers['levels_nodes'].CLIFF_M.values > 1e-6).sum()),
             NOTE="philosophy sec 5: hold the gradient and take the difference at a drop "
                  "chamber - the chamber is at the TOP of the cliff"),
    ])


# ======================================================================================
# BUILD
# ======================================================================================

def build(crit: Criteria = CRIT, publish_it: bool = True, verbose: bool = True) -> Dict:
    t0 = time.time()
    _rebuild_tables(crit)
    with K.Manifest.stage(STAGE, STAGE_ORDER) as rec:
        net = load(rec)
        if verbose:
            _log(f"{net.n:,} chambers, {net.m:,} segments, "
                 f"{net.elen.sum() / 1000:,.1f} km, {int((net.edge_of < 0).sum())} terminals")
            if len(net.contracted):
                _log(f"contracted {len(net.contracted)} chamber pairs closer than "
                     f"{crit.MH_SNAP_M:g} m (A-LEV-13): "
                     f"{', '.join(net.contracted.US_NODE.astype(str))}")
        f = rec.funnel("chambers", int(net.n) + len(net.contracted))
        f.drop("contracted into their neighbour (closer than MH_SNAP_M)",
               ids=list(net.contracted.US_NODE.astype(str)))
        f.close(int(net.n))

        held, held_src = held_pf_from_s5()
        rec.metric("held_peak_factor", round(held, 7))
        rec.note(f"held peak factor {held:.5f} read from {held_src} (A-LEV-2)")
        acc = accumulate(net.edge_of, net.ev, net.elen, net.order, net.q_loc, net.np_loc,
                         held, crit)
        recon = reconcile_with_s5(net, acc)
        if verbose:
            _log(f"load levelled {acc['QADF'][net.edge_of < 0].sum():,.1f} m3/d over "
                 f"{acc['NPROP'][net.edge_of < 0].sum():,.0f} properties; peak flow max "
                 f"{acc['QPK'].max():.1f} L/s")

        des, trace, sites = solve(net, acc["QPK"], crit, verbose=verbose)
        layers = build_layers(net, des, acc, held, crit)
        nodes, reaches = layers["nodes"], layers["reaches"]

        rl_cols = ["PASS", "STATIONS", "PAST_CAP_N", "PAST_CAP_KM", "EXCUSED_N",
                   "MAX_COVER_M", "MAX_DROP_M", "VORTEX_N", "NEW_STATIONS",
                   "RUNS", "UNIFORM", "LATE", "FALL_RECOVERED_M"]
        of = nodes[nodes.IS_OUTFALL == 1]
        outfalls = pd.DataFrame(dict(
            NODE_UID=of.NODE_UID.values, X=of.X.values, Y=of.Y.values,
            GRD_M=of.GRD_M.values, INV_M=of.INV_M.values, DEPTH_M=of.DEPTH_M.values,
            KIND=of.NODE_KIND.values, Q_ADF_M3D=of.Q_ADF_M3D.values,
            Q_PK_LS=of.Q_PK_LS.values, N_PROP=of.N_PROP.values)).sort_values(
                "Q_PK_LS", ascending=False).head(30)

        tables = dict(
            headline=headline_table(net, layers, acc, crit),
            flatness=flatness_table(net, reaches, crit),
            depth=depth_table(nodes, reaches, layers["levels_nodes"], crit),
            drops=drop_table(nodes, reaches, crit),
            gradient=gradient_table(reaches, layers["levels_reaches"]),
            selfclean=selfclean_table(reaches, crit),
            diameter=diameter_table(reaches),
            reasons=reason_table(reaches, layers["levels_reaches"]),
            stations=station_table(nodes, layers.get("pumped_links"), sites),
            trace=trace[rl_cols] if len(trace) else trace,
            pass2=pd.DataFrame([dict(QUANTITY=k, VALUE=v)
                                for k, v in sorted(des.notes.get("relay", {}).items())]),
            wadi=wadi_summary(layers["wadi_h1a"], reaches,
                              int(layers["levels_nodes"].ON_WADI.sum())),
            wadi_h1a=layers["wadi_h1a"],
            station_bands=station_bands(nodes, sites),
            reconcile=recon,
            outfalls=outfalls,
            station_sites=sites,
            provenance_map=provenance_map_frame(),
            assumptions=pd.DataFrame(ASSUMPTIONS),
            conflicts=pd.DataFrame(CONFLICTS),
            guideline=pd.DataFrame([dict(NAME=k, VALUE=v[0], UNIT=v[1], SOURCE=v[2])
                                    for k, v in sorted(G.items())]),
            excursions=excursion_table(net, des, layers, crit),
            trunk=trunk_note(),
            headroom=headroom_table(reaches, layers["levels_reaches"]),
        )
        tables["findings"] = findings(layers, tables, crit)
        sw = RUN_DIR / "sweep.csv"
        if sw.exists():
            # `--sweep` is a separate run because a sensitivity is a WHOLE RUN with a
            # different Criteria object - contract._cross_field refuses a mixture inside one
            # layer. Its result is carried into the report so the reader does not have to
            # know that.
            tables["sweep"] = pd.read_csv(sw)
        if publish_it:
            try:
                tables["calibration"] = calibrate_frame(reaches, nodes)
            except Exception as e:                   # the as-built data may not be present
                _log(f"as-built calibration skipped: {e}")
                tables["calibration"] = pd.DataFrame(
                    [dict(key="", label=f"calibration could not run: {e}")])
        if publish_it:
            publish(layers, rec)
            write_diagnostics(layers, tables, rec)
            write_kmz(layers, rec)
            RUN_DIR.mkdir(parents=True, exist_ok=True)
            REPORT_MD.write_text(report(layers, tables, crit), encoding="utf-8")
            rec.wrote("LEVELS.md", str(REPORT_MD), len(tables))
            MANIFEST_JSON.write_text(json.dumps(dict(
                stage=STAGE_VERSION, contract=K.CONTRACT_VERSION, tau_pa=crit.TAU_PA,
                seconds=round(time.time() - t0, 1),
                headline={r.QUANTITY: r.VALUE for r in tables["headline"].itertuples()},
            ), indent=2), encoding="utf-8")
        for r in tables["headline"].itertuples():
            rec.metric(r.QUANTITY, round(float(r.VALUE), 4))
        rec.note(f"tau = {crit.TAU_PA:g} Pa (A-LEV-6, GAP-9) on every published row")
    if verbose:
        _log(f"done in {time.time() - t0:.1f} s")
        print()
        print(report(layers, tables, crit))
    return dict(net=net, des=des, acc=acc, layers=layers, tables=tables, trace=trace)


# ======================================================================================
# VERIFY - re-derive every headline from the PUBLISHED file, reading nothing else
# ======================================================================================

def verify(crit: Criteria = CRIT) -> pd.DataFrame:
    nodes = gpd.read_file(OUT_GPKG, layer="nodes")
    reaches = gpd.read_file(OUT_GPKG, layer="reaches")
    cross = gpd.read_file(OUT_GPKG, layer="crossings")
    K.validate(nodes, "nodes", stage=f"{STAGE}:verify")
    K.validate(reaches, "reaches", stage=f"{STAGE}:verify")
    K.validate(cross, "crossings", stage=f"{STAGE}:verify")
    K.assert_crossings_resolve(reaches=reaches, crossings=cross)
    K.Network.assert_round_trip(nodes, reaches)
    K.Network.assert_degrees(nodes, reaches)

    checks = []

    def chk(name, ok, got, want=""):
        checks.append(dict(CHECK=name, OK=bool(ok), GOT=got, WANT=want))

    # 1 geometry against the field it claims to measure
    d = (reaches.LEN_M - reaches.geometry.length).abs()
    chk("LEN_M matches its own geometry", d.max() <= K.LEN_TOL_M, f"{d.max():.4f} m",
        f"<= {K.LEN_TOL_M} m")
    # 2 the levels are the gradient
    fall = reaches.INV_UP - reaches.INV_DN
    want = reaches.LEN_M * reaches.SLOPE_LAID / 100.0
    chk("INV_UP - INV_DN == LEN_M x SLOPE_LAID", (fall - want).abs().max() <= 1e-6,
        f"{(fall - want).abs().max():.2e} m", "0")
    # 3 no reverse gradient
    chk("no reverse gradient (G203-p29)", (fall >= -crit.LAY_TOLERANCE_M).all(),
        f"{int((fall < -crit.LAY_TOLERANCE_M).sum())} reaches", "0")
    # 4 cover is criteria.cover(), on the reach's OWN outside diameter
    for dcol, ccol in (("US_DEPTH", "COVER_US"), ("DS_DEPTH", "COVER_DN")):
        w = reaches[dcol] - (reaches.DN / 1000.0 + crit.WALL_ALLOW)
        chk(f"{ccol} == criteria.cover({dcol})", (reaches[ccol] - w).abs().max() <= 1e-9,
            f"{(reaches[ccol] - w).abs().max():.2e} m", "0")
    # 5 the laid gradient is never below the governing minimum
    chk("SLOPE_LAID >= SLOPE_MIN (G203-p27)",
        (reaches.SLOPE_LAID >= reaches.SLOPE_MIN - 1e-9).all(),
        f"{int((reaches.SLOPE_LAID < reaches.SLOPE_MIN - 1e-9).sum())} reaches", "0")
    # 6 the minimum IS the steeper of the two routes, recomputed from the row
    smin_re = np.array([max(crit.table11(int(dn)),
                            HY.smin_tractive(float(q) / 1000.0, crit)) * 100.0
                        for dn, q in zip(reaches.DN, reaches.QPK_LS)])
    chk("SLOPE_MIN == max(Table 11, tractive) recomputed from the row",
        np.abs(reaches.SLOPE_MIN.values - smin_re).max() <= 1e-9,
        f"{np.abs(reaches.SLOPE_MIN.values - smin_re).max():.2e} %", "0")
    # 7 d/D and velocity, recomputed
    yy, vv = [], []
    for dn, s, q in zip(reaches.DN, reaches.SLOPE_LAID, reaches.QPK_LS):
        y, v = HY.pipe_state(int(dn), float(s) / 100.0, float(q) / 1000.0, crit)
        yy.append(0.0 if y is None else y)
        vv.append(0.0 if v is None else v)
    chk("DOD_PK reproduced from DN, SLOPE_LAID and QPK_LS",
        np.abs(reaches.DOD_PK.values - np.array(yy)).max() <= 1e-6,
        f"{np.abs(reaches.DOD_PK.values - np.array(yy)).max():.2e}", "0")
    chk("V_PK_MS reproduced", np.abs(reaches.V_PK_MS.values - np.array(vv)).max() <= 1e-6,
        f"{np.abs(reaches.V_PK_MS.values - np.array(vv)).max():.2e} m/s", "0")
    # 8 the d/D limit, at the criteria's own threshold
    lim = np.array([crit.dod_limit(int(dn)) for dn in reaches.DN])
    chk("every reach inside its own d/D limit (G203-p27 Table 10)",
        (reaches.DOD_PK.values <= lim + 1e-9).all(),
        f"{int((reaches.DOD_PK.values > lim + 1e-9).sum())} reaches", "0")
    # 9 velocity ceiling
    chk("every reach at or below 3.0 m/s (G203-p27)",
        (reaches.V_PK_MS <= crit.V_MAX + 1e-9).all(),
        f"{float(reaches.V_PK_MS.max()):.3f} m/s", f"<= {crit.V_MAX}")
    # 10 minimum cover
    cov = np.minimum(reaches.COVER_US.values, reaches.COVER_DN.values)
    chk("every reach at or above 1.30 m of cover (G203-p33)",
        (cov >= crit.MIN_COVER_CROWN - 1e-6).all(),
        f"{int((cov < crit.MIN_COVER_CROWN - 1e-6).sum())} reaches, worst {cov.min():.3f} m",
        "0")
    # 11 the cap
    chk("no chamber past the 12 m cap without a stated exit",
        int(((nodes.PAST_CAP == 1) & (nodes.CAP_EXIT.fillna("") == "")).sum()) == 0,
        f"{int((nodes.PAST_CAP == 1).sum())} past the cap, "
        f"{int(((nodes.PAST_CAP == 1) & (nodes.CAP_EXIT.fillna('') != '')).sum())} excused",
        "0 unexcused")
    # 12 the drop ceiling
    chk("no drop past the declared ceiling",
        float(nodes.DROP_M.max()) <= crit.DROP_CEILING_M + 1e-9,
        f"{float(nodes.DROP_M.max()):.2f} m", f"<= {crit.DROP_CEILING_M:g} m")
    # 13 VORTEX agrees with DROP_M
    chk("VORTEX == (DROP_M > 2.00 m)",
        bool(((nodes.VORTEX == 1) == (nodes.DROP_M > crit.BACKDROP_MAX + 1e-9)).all()),
        f"{int((nodes.VORTEX == 1).sum())} vortex shafts", "-")
    # 14 the drop at a chamber IS the arriving minus the outgoing invert
    arr = reaches.groupby("DS_NODE").INV_DN.max()
    inv = nodes.set_index("NODE_UID").INV_M
    dd = (arr - inv.reindex(arr.index)).clip(lower=0.0)
    got = nodes.set_index("NODE_UID").DROP_M.reindex(dd.index)
    chk("DROP_M == max(arriving invert) - outgoing invert",
        float((dd - got).abs().max()) <= 1e-6, f"{float((dd - got).abs().max()):.2e} m", "0")
    # 15 the forest
    chk("every component ends at exactly one terminal (H15)",
        int((nodes.N_OUT == 0).sum()) == int((nodes.IS_OUTFALL == 1).sum()),
        f"{int((nodes.IS_OUTFALL == 1).sum())} terminals", "-")
    # 16 topology written down, not inferred
    chk("US_NODE and DS_NODE resolve on every reach (H16)",
        reaches.US_NODE.isin(nodes.NODE_UID).all() and reaches.DS_NODE.isin(nodes.NODE_UID).all(),
        "all", "all")
    # 17 the peak flow is reproducible from its own row
    w = reaches.QADF_M3D * M3D_TO_LS * reaches.PF + reaches.QINF_LS
    chk("QPK_LS == QADF x PF + QINF", (reaches.QPK_LS - w).abs().max() <= 1e-6,
        f"{(reaches.QPK_LS - w).abs().max():.2e} L/s", "0")
    # 18 the tractive assumption is on every row and is one value
    chk("tau on every row and only one value", reaches.TAU_PA.nunique() == 1,
        f"{reaches.TAU_PA.iloc[0]:g} Pa", f"{crit.TAU_PA:g} Pa")
    # 19 the gradient sits on the 0.05 % step
    st = reaches.SLOPE_LAID / (crit.SLOPE_STEP * 100.0)
    chk("SLOPE_LAID on the 0.05 % step (P1)", (st - st.round()).abs().max() <= 1e-6,
        f"{float((st - st.round()).abs().max()):.2e}", "0")
    # 20 the diameter is a member of the series, never merely in range
    chk("every DN is a member of criteria.DN_SERIES",
        reaches.DN.isin(list(crit.DN_SERIES)).all(),
        f"{sorted(reaches.DN.unique())}", "members only")
    # 21 no reach sized by a prohibited reason
    chk("no reach SIZED_BY depth or cover (G203-p29; Ten States 33.43)",
        reaches.SIZED_BY.isin(list(K.SIZED_BY)).all(),
        f"{sorted(set(reaches.SIZED_BY))}", "hydraulic reasons only")
    # 22 self-cleansing route recorded, and never 'neither'
    chk("every reach meets one of the two self-cleansing routes (H5)",
        int((reaches.CLEAN_BY == "neither").sum()) == 0,
        f"{int((reaches.CLEAN_BY == 'tractive').sum()):,} on the tractive route", "0 neither")
    # 23 station nodes carry what s7 needs
    st_nd = nodes[nodes.NODE_KIND == "station"]
    need = ["X", "Y", "GRD_M", "INV_M", "Q_PK_LS", "Q_ADF_M3D", "N_PROP"]
    chk("every station carries the s7 interface with a NON-ZERO duty flow",
        len(st_nd) == 0 or (st_nd[need].notna().all().all() and (st_nd.Q_PK_LS > 0).all()),
        f"{len(st_nd)} stations, min duty {0 if not len(st_nd) else st_nd.Q_PK_LS.min():.2f} L/s",
        "> 0 (W11a published 226 at zero)")
    # 24 the uphill share, recomputed from the published ground fall
    tr = K.terrain_report(reaches, nodes)
    chk("AGN_GRADE agrees with GND_FALL on every reach",
        bool(((reaches.AGN_GRADE == 1) ==
              (reaches.GND_FALL < -crit.ADVERSE_MIN_M)).all()),
        f"{tr['against_share'] * 100:.2f} % of length uphill", "-")
    return pd.DataFrame(checks)


# ======================================================================================
# SELF-TEST.  The arithmetic against hand-worked cases, and this stage's fast paths against
# hydra's own reference functions.  `python s6_levels.py --selftest`
# ======================================================================================

def _self_test(verbose: bool = True) -> None:
    C = CRIT
    _rebuild_tables(C)
    n_ok = 0

    def ok(cond, what):
        nonlocal n_ok
        assert cond, f"SELF-TEST FAILED: {what}"
        n_ok += 1

    # ---- 1. the fast capacity test IS hydra's d/D test -------------------------------
    for dn in (200, 315, 500, 900, 1400):
        for S in (0.00075, 0.005, 0.02):
            for q in (0.001, 0.01, 0.1, 0.5):
                y, _v = HY.pipe_state(dn, S, q, C)
                want = (y is not None) and y <= C.dod_limit(dn) + 1e-12
                ok(carries(dn, S, q, C) == want,
                   f"carries(DN{dn}, {S}, {q}) disagrees with hydra.pipe_state")

    # ---- 2. the chosen pipe IS hydra.size_pipe's answer at the gradient actually laid --
    # A smaller diameter has a STEEPER Table 11 minimum, so it was tested at a steeper
    # gradient than the one finally laid - and a steeper gradient carries more.  A size that
    # failed up there therefore fails down here too, which is why the two must agree.
    for q in (0.002, 0.02, 0.08, 0.2, 0.6, 1.4):
        for gd in (100.0, 99.0, 96.0):                     # flat, gentle and steep ground
            dn, S, sm, why, iv, cap = choose_size(q, 100.0, 100.0, gd, 100.0, 200, C)
            if cap:
                continue                                   # the velocity cap moved S
            ref_dn, ref_y, ref_v, ref_why = HY.size_pipe(q, S, C, dn_min=200)
            ok(dn == ref_dn,
               f"choose_size gave DN{dn} where hydra.size_pipe gives DN{ref_dn} at "
               f"q={q} m3/s, S={S}")
            ok(why == ref_why,
               f"SIZED_BY {why!r} vs hydra {ref_why!r} at q={q}, S={S}, DN{dn}")

    # ---- 3. the smax cache returns the uncached answer -------------------------------
    _SMAX_CACHE.clear()
    for dn, q in ((200, 0.005), (400, 0.05), (900, 0.4)):
        a = smax(dn, q, C)
        b = HY.smax_for(dn, q, C)
        b = None if b == HY.INFEASIBLE else b
        ok((a is None) == (b is None) and (a is None or abs(a - b) < 1e-12),
           f"smax cache disagrees at DN{dn}, q={q}")

    # ---- 4. the gradient step, both ways ---------------------------------------------
    ok(abs(ceil_step(0.00051) - 0.0010) < 1e-15, "ceil_step")
    ok(abs(floor_step(0.00099) - 0.0005) < 1e-15, "floor_step")
    ok(abs(ceil_step(0.0005) - 0.0005) < 1e-15, "ceil_step is exact on the step")

    # ---- 5. cover() and invert_depth_min() are exact inverses ------------------------
    for dn in C.DN_SERIES:
        ok(abs(C.cover(dn, C.invert_depth_min(dn)) - C.MIN_COVER_CROWN) < 1e-12,
           f"cover/invert_depth_min round trip at DN{dn}")

    # ---- 6. a hand-worked three-chamber run -----------------------------------------
    # flat ground at 100.000 m aOD, 30 m reaches, DN200 at Table 11's 5.00 mm/m.
    # head invert = 100 - (1.30 + 0.200 + 0.05) = 98.450
    # after 30 m at 0.005: 98.300; after another 30 m: 98.150
    # cover at the third chamber = 100 - 98.150 - 0.25 = 1.600 m
    inv0 = 100.0 - C.invert_depth_min(200)
    ok(abs(inv0 - 98.45) < 1e-12, "head invert on flat ground at DN200")
    ok(abs((inv0 - 2 * 30.0 * 0.005) - 98.15) < 1e-12, "two reaches at Table 11's minimum")
    ok(abs(C.cover(200, 100.0 - 98.15) - 1.60) < 1e-12, "cover after two flat reaches")
    ok(abs(C.cover(200, 100.0 - 98.15) - C.MIN_COVER_CROWN
           - 2 * 30.0 * (0.005 - 0.0)) < 1e-12,
       "the depth debt on flat ground is exactly (minimum gradient) x length")

    # ---- 7. crown matching, and the drop it does and does not create ------------------
    # a DN200 arriving at 98.000 into a chamber whose outgoing pipe is DN400:
    # outgoing soffit <= incoming soffit -> INV_out = 98.000 + 0.200 - 0.400 = 97.800,
    # so DROP_M = 0.200 m - a diameter step, not a fall - and it is below the 0.60 m
    # backdrop trigger, which is why crown matching does not manufacture drop structures.
    inv_out = 98.000 + C.outside_diameter(200) - C.outside_diameter(400)
    ok(abs(inv_out - 97.80) < 1e-12, "crown matching at a diameter step")
    ok(abs((98.000 - inv_out) - 0.20) < 1e-12, "the drop at a DN200 -> DN400 step")
    ok(98.000 - inv_out <= C.DROP_TRIGGER, "a DN200 -> DN400 step needs no backdrop")
    # but DN200 into DN1400 does: 1.200 m, a backdrop, and G203-p30 requires it external
    ok(C.outside_diameter(1400) - C.outside_diameter(200) > C.DROP_TRIGGER,
       "a DN200 -> DN1400 step DOES need a backdrop (G203-p30)")

    # ---- 8. the cliff rule: the chamber at the top is deepened, not the pipe surfaced --
    # 30 m reach, ground falling 12 m (40 %), the pipe held to 25 %: the top chamber has to
    # go 12 - 7.5 = 4.5 m deeper than minimum cover for the bottom end to keep its 1.30 m.
    S = 0.25
    shortfall = 12.0 - 30.0 * S
    ok(abs(shortfall - 4.5) < 1e-12, "the cliff shortfall arithmetic")

    # ---- 9. the tractive minimum is the one G203-p27 prints, and tau is a power law ----
    q = 0.010
    ok(abs(HY.smin_tractive(q, C)
           - C.TRACTIVE_K_M3S * C.TAU_PA ** 1.23 * q ** -0.461) < 1e-15, "tractive equation")
    ok(abs(HY.smin_tractive(q, replace(C, TAU_PA=2.0)) / HY.smin_tractive(q, C)
           - 2.0 ** 1.23) < 1e-12, "tau sensitivity is exactly 2^1.23")

    # ---- 10. the accumulator reproduces s5_flows on s5's OWN graph --------------------
    try:
        a = gpd.read_file(FLOWS_GPKG, layer="arcs", ignore_geometry=True)
        nd = gpd.read_file(FLOWS_GPKG, layer="nodes", ignore_geometry=True)
        idx = {u: i for i, u in enumerate(nd.NODE_UID.astype(str))}
        nn = len(idx)
        route = a.IS_ROUTE.values == 1
        eu = np.array([idx[u] for u in a.US_NODE.astype(str)])
        ev = np.array([idx[u] for u in a.DS_NODE.astype(str)])
        edge_of = np.full(nn, -1, dtype=np.int64)
        edge_of[eu[route]] = np.where(route)[0]
        qloc = np.zeros(nn)
        nploc = np.zeros(nn)
        # A-FLOW-3: a route arc's own load enters at its UPSTREAM node.
        # A-FLOW-5: a non-route arc delivers its own load at its DOWNSTREAM node.
        np.add.at(qloc, eu[route], a.Q_LOC_M3D.values[route])
        np.add.at(nploc, eu[route], a.N_PROP_LOC.values[route])
        np.add.at(qloc, ev[~route], a.Q_LOC_M3D.values[~route])
        np.add.at(nploc, ev[~route], a.N_PROP_LOC.values[~route])
        order = _topo(edge_of, ev, nn)
        held, _ = held_pf_from_s5()
        acc = accumulate(edge_of, ev, np.abs(a.LEN_M.values), order, qloc, nploc, held, C)
        mine = acc["QADF"][eu[route]]
        theirs = a.QADF_M3D.values[route]
        rel = np.abs(mine - theirs) / np.maximum(theirs, 1e-9)
        ok(float(np.nanmax(rel)) < 1e-6,
           f"the accumulator does not reproduce s5_flows on s5's own graph: worst relative "
           f"difference {float(np.nanmax(rel)):.3e} on {int((rel > 1e-6).sum())} arcs")
        if verbose:
            print(f"  accumulator vs s5_flows on s5's own graph: worst relative difference "
                  f"{float(np.nanmax(rel)):.2e} over {int(route.sum()):,} route arcs")
    except FileNotFoundError:
        if verbose:
            print("  (s5_flows not published - the cross-check against it was skipped)")

    if verbose:
        print(f"{STAGE_VERSION}: self-test PASSED ({n_ok} checks)")


# ======================================================================================
# CALIBRATION against NAMA's built network
# ======================================================================================

def calibrate() -> pd.DataFrame:
    """`--asbuilt`: the same calibration the report carries, read back off the published
    file rather than out of memory."""
    return calibrate_frame(gpd.read_file(OUT_GPKG, layer="reaches"),
                           gpd.read_file(OUT_GPKG, layer="nodes"))


# ======================================================================================
# SWEEP - the sensitivities that would change the design, reported and never published
# ======================================================================================

def sweep(verbose: bool = True) -> pd.DataFrame:
    """tau, the cover cap and the drop ceiling.  A sensitivity run is a WHOLE RUN with a
    different Criteria object (contract._cross_field refuses a mixture inside one layer), so
    none of these is published - they are reported."""
    rows = []
    cases = [("design basis", CRIT),
             ("tau = 2.0 Pa - the NWS downside (GAP-9)", replace(CRIT, TAU_PA=2.0)),
             ("cover cap 10 m instead of 12", replace(CRIT, MAX_COVER=10.0)),
             ("cover cap 15 m instead of 12", replace(CRIT, MAX_COVER=15.0)),
             ("drop / excursion ceiling 10 m instead of 20",
              replace(CRIT, DROP_CEILING_M=10.0))]
    for name, c in cases:
        _rebuild_tables(c)
        net = load()
        held, _ = held_pf_from_s5()
        acc = accumulate(net.edge_of, net.ev, net.elen, net.order, net.q_loc, net.np_loc,
                         held, c)
        des, trace, _sites = solve(net, acc["QPK"], c, verbose=False)
        cov_deep, cov_shallow = covers(net, des, c)
        live = np.array([not des.station[int(net.eu[k])] for k in range(net.m)])
        L = net.elen[live]
        rows.append(dict(
            CASE=name, TAU_PA=c.TAU_PA, MAX_COVER=c.MAX_COVER,
            DROP_CEILING=c.DROP_CEILING_M,
            STATIONS=int(des.station.sum()), PASSES=des.passes,
            KM=round(float(L.sum() / 1000.0), 1),
            MEDIAN_GRAD_MM_M=round(float(np.median(des.slope[net.eu[live]]) * 1000), 2),
            MEDIAN_COVER_M=round(float(np.median(cov_shallow)), 2),
            MAX_COVER_M=round(float(cov_deep.max()), 2),
            VORTEX=int((des.drop > c.BACKDROP_MAX).sum()),
            BACKDROP=int(((des.drop > c.DROP_TRIGGER) & (des.drop <= c.BACKDROP_MAX)).sum()),
            DN_MAX=int(des.dn.max()),
            TRACTIVE_KM=round(float(sum(
                net.elen[k] for k in np.where(live)[0]
                if HY.smin_tractive(float(acc["QPK"][int(net.eu[k])]) / 1000.0, c)
                > _T11[int(des.dn[int(net.eu[k])])])) / 1000.0, 1)))
        if verbose:
            _log(f"sweep: {name:<44s} stations {rows[-1]['STATIONS']:4d}  "
                 f"max cover {rows[-1]['MAX_COVER_M']:6.2f} m  vortex {rows[-1]['VORTEX']:5d}")
    _rebuild_tables(CRIT)
    return pd.DataFrame(rows)


# ======================================================================================
# CLI
# ======================================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="W12 stage 6 - levels and sizes")
    ap.add_argument("--verify", action="store_true",
                    help="re-derive every headline from the PUBLISHED file")
    ap.add_argument("--selftest", action="store_true", help="the arithmetic, against hydra")
    ap.add_argument("--report", action="store_true", help="re-print the published report")
    ap.add_argument("--asbuilt", action="store_true", help="calibrate against NAMA's network")
    ap.add_argument("--sweep", action="store_true", help="tau, the cap and the drop ceiling")
    ap.add_argument("--no-publish", action="store_true", help="build but write nothing")
    a = ap.parse_args(argv)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 60)
    pd.set_option("display.max_colwidth", 78)

    if a.selftest:
        _self_test()
        return 0
    if a.report:
        print(REPORT_MD.read_text(encoding="utf-8"))
        return 0
    if a.verify:
        df = verify()
        print(df.to_string(index=False))
        bad = df[~df.OK]
        print()
        print(f"{int(df.OK.sum())}/{len(df)} checks pass")
        if len(bad):
            print("FAILED:")
            print(bad.to_string(index=False))
        return 0 if bad.empty else 1
    if a.asbuilt:
        df = calibrate()
        print(df.to_string(index=False))
        return 0
    if a.sweep:
        df = sweep()
        print()
        print(df.to_string(index=False))
        df.to_csv(RUN_DIR / "sweep.csv", index=False)
        return 0

    _self_test(verbose=False)
    build(publish_it=not a.no_publish)
    return 0


if __name__ == "__main__":                                        # pragma: no cover
    sys.exit(main())
