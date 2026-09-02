"""W11a - the shared data contract. Stage 0b, written after the auditor and before any design.

THE ONE IDEA: THE GRAPH IS THE DESIGN. EVERY LAYER IS A VIEW OF IT.

W10's fatal defect was not a wrong number. It was that `W10_pipes.shp` - the thing actually
issued - was **7,919 disconnected components at 0.01 m tolerance**, largest holding 5.9 %.
The flow tree that sized those pipes was real, correct and lived entirely inside
`p2_sizing.py`; the shapefile inherited only its geometry. 91.4 % of the stitch links stopped
at exactly 1.000 m from what they joined, because a 1.0 m buffer was taken before the nearest
points and a 2.5 m snap downstream hid it from the graph while the layer kept the gaps.
Nobody could have known, because there was nothing on the layer to know it from.

So this module inverts the dependency. `Network` - nodes with identity, edges that reference
node identity - is the primary object. Geometry is DERIVED: an edge's LineString is built as
`[node[US_NODE].xy] + vertices + [node[DS_NODE].xy]`, so a published reach physically cannot
end anywhere but on its own chambers. `US_NODE`/`DS_NODE` are written from the graph, never
re-derived by a tolerance. Four W10 failure modes stop being possible by construction rather
than by audit:

    disconnected layer   an edge endpoint IS the node coordinate; there is no gap to leave
    loops (H15)          a node may own at most ONE outgoing edge - enforced in add_edge
    orphan flow          every edge references two registered nodes; a dangling id raises
    silent load drops    a load unit is attached to a node uid or it is named in a Funnel

WHAT THIS FILE IS FOR, PRACTICALLY. Ten stages are being written separately. They agree on
six things and nothing else is negotiable:

    1. LAYERS          the published layer schemas, field by field, with the audit check
                       each field exists to feed
    2. Network         node identity, edge identity, and the invariants held while building
    3. Manifest        how a stage declares what it read, what it wrote, and what it dropped
    4. validate()      the gate every stage calls before it writes, and after it reads
    5. SCHEDULES       the printed header declared BESIDE the stored field, so a schedule
                       column and the field behind it cannot be edited apart
    6. EXCLUDED        what was proposed and refused, and what would let it in - the only
                       defence a contract has against schema regrowth over ten stages

WHY validate() RAISES INSTEAD OF WARNING. `audit.py` scores a missing field as
NOT_CHECKABLE, and the philosophy (sec 8) makes "any check that cannot run" blocking. So a
stage that omits `GRAD_BY` has not published a slightly incomplete layer - it has
published an unauditable one. Thirteen of W10's 22 checks were unanswerable for exactly this
reason. Failing loudly at the writing stage costs a minute; failing at the audit costs a
rebuild.

FIVE THINGS FOUND WHILE WRITING THIS, all verified against the real source, all live:

  * **`criteria.invert_depth_min()` is 50 mm too shallow to pass the auditor.** It returns
    `MIN_COVER_CROWN + OD + WALL_ALLOW` with `WALL_ALLOW = 0.05`; `audit.h3` requires
    `US_DEPTH - (DN/1000 + 0.10) >= 1.30`. Measured at every DN in the series: 160 -> 1.510
    against 1.560 needed, 200 -> 1.550 / 1.600, 250 -> 1.600 / 1.650, 315 -> 1.665 / 1.715,
    400 -> 1.750 / 1.800. A design laid to the criteria helper fails a BLOCKING check on
    EVERY REACH. `min_invert_depth()` below is the contract's own definition, and `cover()`
    is the single definition every published depth statistic goes through.

  * `audit.py` H9 keys its diameter floors `"sub main"` / `"trunk main"` (space), but
    `W10_existing_built.shp` carries `sub_main` / `trunk_main`. `floor.get()` returns None
    for an unrecognised tier and the pipe is skipped - a SILENT PASS. Verified: a layer of
    DN100 pipes tagged `sub_main` returns H9 = PASS; the same layer tagged `sub main`
    returns FAIL. The auditor cannot be edited from here, so TIERS below is pinned to the
    auditor's spelling and validate() rejects the underscore forms.

  * **MultiLineString is refused outright, not tolerated.** `audit.Ctx.graph()` takes
    `g.geoms[0]` of a multipart geometry and drops the rest, so a multipart reach corrupts
    H15's component count without failing anything. C's own round-trip check had the same
    blind spot. A reach is one part or it is not a reach.

  * `GRAD_BY` is 11 characters. An ESRI Shapefile DBF truncates field names at 10, so
    writing the audited layer to .shp silently renames it `GRADIENT_B` and audit G2 fails on
    a layer that was correct in memory. **GeoPackage is the published, audited format.**
    Shapefile and DXF are mirrors for CAD; `assert_audited_path()` refuses to hand a .shp to
    the auditor at all, because a README warning is a note nobody opens.

  * `SLOPE_PCT` means "the minimum" in W10's `p2_sizing.py` and "the laid gradient" in
    `DELIVERABLE_SPEC.md` D.1.2. One name, two meanings, and the layer cannot say which. It
    is in BANNED_FIELDS; the pair is `SLOPE_LAID` and `SLOPE_MIN`, on every layer that has a
    gradient including the connections.

ONE CONTRADICTION THIS FILE CANNOT RESOLVE, recorded rather than papered over: `audit.h15`
requires `nx.number_connected_components(G) == 1`, but philosophy sec 8a explicitly contemplates
satellite works and on-site systems - more than one network. A compliant multi-system design
FAILS H15 as the auditor is written. See OPEN_ITEMS; `Network.check()` reports the component
count and its systems so the contradiction is visible rather than discovered at the audit.

Sources: `_BRAIN/08_DESIGN_PHILOSOPHY.md` (H1-H15, P1-P6, sec 5 cap-and-veto, sec 8 audit),
`_BRAIN/02_DESIGN_CRITERIA.md` via `W8/py/sewnet/criteria.py` (every number),
`W11a/py/w11a/audit.py` (the 22 checks this feeds),
`W10/docs/research/W11a_BUILD_BRIEF.md` (P1-P10 and the ten invariants),
`W10/docs/research/DELIVERABLE_SPEC.md` (the scope-p25 schedule columns and the Bentley map).

No design number is defined here. Values live in `sewnet.criteria`; this file names fields,
fixes vocabulary and holds shape. Where a threshold appears below it is a STRUCTURAL
tolerance (geometry snapping, id width), a restatement of a criteria constant with its
citation, or - in exactly one case, `min_invert_depth()` - a value the AUDITOR imposes and
the criteria file does not yet match.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

# Imported hard, not in a try/except. A contract that degrades quietly when a dependency is
# missing is how W10's RoadTreatment ran with `units=None, sampler=None` and three of its
# steps became no-ops nobody noticed (invariant 10).
import geopandas as gpd
from shapely.geometry import LineString, Point

# `sewnet` lives in W8 and is the ONLY source of design numbers (CLAUDE.md: no invented
# metrics). The path is resolved from this file rather than left to the caller, so importing
# the contract cannot succeed with the criteria missing - which would be a contract with no
# numbers behind it.
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py/w11a
W11A_ROOT = os.path.dirname(os.path.dirname(_HERE))         # .../W11a
REPO_ROOT = os.path.dirname(W11A_ROOT)                      # .../Hydraulic/Claude
_W8_PY = os.path.join(REPO_ROOT, "W8", "py")
if _W8_PY not in sys.path:
    sys.path.insert(0, _W8_PY)

from sewnet.criteria import DEFAULT as C          # noqa: E402  the design basis
from sewnet import hydra                          # noqa: E402,F401  re-exported, never reimplemented

CONTRACT_VERSION = "W11a-contract-1.1"

# --------------------------------------------------------------------------------------
# Structural constants. Not design values - those are in sewnet.criteria and are cited.
# --------------------------------------------------------------------------------------

CRS_EPSG = 32640                 # project rule; every layer, no exceptions

GEOM_TOL_M = 0.01                # the auditor's graph clustering radius (audit.Ctx.graph
                                 # snap=0.01). Never used as OUR tolerance - see below.

ENDPOINT_TOL_M = 0.005           # HALF the auditor's radius, per endpoint. Two reaches
                                 # meeting at one chamber, each allowed the full 0.01, can
                                 # sit 0.02 m apart - twice the auditor's snap - and H15
                                 # then reports a disconnected piece on a design whose every
                                 # endpoint was "within tolerance". The tolerance has to be
                                 # per-end and half, or it does not compose.

LEN_TOL_M = 0.05                 # LEN_M against the geometry it claims to measure. H12 and
                                 # every published length read LEN_M, not the geometry;
                                 # to_edges_gdf generates them together, but a later merge or
                                 # a hand edit can part them and nothing else would notice.

NODE_MERGE_M = C.MH_SNAP_M       # 3.0 m - "closer than the clearance => ONE structure,
                                 # merge". Node identity uses the same radius, so the graph
                                 # cannot hold two chambers the design would build as one.

SLOPE_STEP_PCT = C.SLOPE_STEP * 100.0    # 0.05 %. P1: gradients are laid on round steps so
                                         # the drawing matches the levels.

SHP_FIELD_MAXLEN = 10            # ESRI DBF limit. Enforced against the mirror, not the GPKG.

AUDITOR_OD_ALLOW_M = C.WALL_ALLOW  # THE AUDITOR'S allowance for wall and bedding below the
                                 # crown, and it must BE the auditor's: audit.od() reads
                                 # crit.WALL_ALLOW (0.05). This was hard-coded at 0.10, and
                                 # the 50 mm gap ran both ways. At the MINIMUM the contract
                                 # was conservative and harmless; at the MAXIMUM it was
                                 # optimistic, and stage 6 shipped 44 of 633 reaches past the
                                 # 12 m cap unflagged - every one of them inside that 50 mm.
                                 # Two constants for one quantity is the defect; there is now
                                 # one, and it is the one the auditor uses.

NODE_UID_FMT = "N{:07d}"         # dumb, stable, sortable. Meaning lives in NODE_REF.
EDGE_UID_FMT = "E{:07d}"


class ContractError(Exception):
    """Raised by validate(), Network, Manifest and the schedule/export helpers. Never caught
    inside a stage - the whole point is that it stops the write."""


# --------------------------------------------------------------------------------------
# Depth. The one place the contract overrides a criteria helper, and it says why.
# --------------------------------------------------------------------------------------

def min_invert_depth(dn: int) -> float:
    """Minimum invert depth below ground for a reach of this diameter, in metres.

    `MIN_COVER_CROWN (1.30, G203-p33) + OD (DN/1000) + 0.10`.

    DO NOT use `criteria.invert_depth_min()`. It adds `WALL_ALLOW = 0.05` where `audit.h3`
    subtracts `DN/1000 + 0.10`, so a design laid to the criteria helper sits 50 mm shallow at
    EVERY diameter and fails a BLOCKING check on EVERY REACH. Measured: DN160 1.510 vs 1.560,
    DN200 1.550 vs 1.600, DN250 1.600 vs 1.650, DN315 1.665 vs 1.715, DN400 1.750 vs 1.800.

    The 0.10 is the AUDITOR's allowance, not a guideline value - G203-p33 gives cover to
    crown and says nothing about bedding. If 0.10 is the wrong allowance the fix belongs in
    `audit.py` and in `criteria.WALL_ALLOW` together, NEVER in a shallower design: laying
    45 km at 1.55 m to satisfy a helper is how W10 shipped 45.92 km below minimum cover.
    """
    return C.MIN_COVER_CROWN + dn / 1000.0 + AUDITOR_OD_ALLOW_M


def cover(dn: int, invert_depth: float) -> float:
    """Cover to crown, on the reach's OWN outside diameter (H3, G203-p33).

    THE single definition. Every published depth or cover statistic goes through this, so a
    schedule, a drawing and the audit cannot each carry their own arithmetic. W10 used a
    hardcoded 0.30 m here regardless of diameter and shipped 45.92 km below minimum.
    """
    return float(invert_depth) - (dn / 1000.0 + AUDITOR_OD_ALLOW_M)


# --------------------------------------------------------------------------------------
# Vocabulary. Every one of these is pinned by something outside this file.
# --------------------------------------------------------------------------------------

# audit.py H9 floor keys, verbatim, plus the philosophy sec 4 governing set
# ("rider, lateral, main, sub main, trunk main"). Underscore forms are REJECTED: H9 skips
# an unrecognised tier silently, so the contract is the only thing standing between a typo
# and an unchecked diameter.
TIERS: Tuple[str, ...] = ("rider", "lateral", "main", "sub main", "trunk main")
TIER_TOKEN = {"rider": "R", "lateral": "L", "main": "M",
              "sub main": "SM", "trunk main": "TM"}          # NAMA's own ID grammar
TIER_ALIASES = {"sub_main": "sub main", "submain": "sub main",
                "trunk_main": "trunk main", "trunkmain": "trunk main",
                "sub-main": "sub main", "trunk-main": "trunk main"}

# audit.py H8 `allowed` set, verbatim. Extending this REQUIRES editing audit.py, which is
# the point: "depth" and "cover" are prohibited answers for a diameter (G203-p29, philosophy
# H8), and the auditor is the enforcement. "infeasible" was proposed and refused - EXCLUDED.
SIZED_BY: Tuple[str, ...] = ("capacity", "dod", "velocity", "horizon", "minimum")

# What set the LAID gradient. Depth IS admissible here - the philosophy prohibits it as an
# answer for a diameter, not for a gradient ("'Depth' is not an admissible answer for a
# diameter", sec 3). Nothing in audit.py constrains this set, so the contract does.
GRAD_BY: Tuple[str, ...] = (
    "table11",     # H6, G203-p29 T11 floor governed
    "tractive",    # H5 tractive route governed (exposed to tau, GAP-9)
    "ground",      # laid to the ground fall, both minima already satisfied
    "cover_min",   # steepened/flattened to hold 1.30 m cover (H3, G203-p33)
    "cover_max",   # flattened to stay under the 12 m cap (H4, philosophy sec 5)
    "uniform",     # carried from the upstream reach (P1) - the preferred answer
    "vmax",        # flattened to hold v <= 3.0 m/s (H7, G203-p27)
    "tie",         # fixed by an existing invert (H14) - the design yields
)

# H5: "Record which route each pipe takes. They are alternatives, not cumulative."
CLEAN_BY: Tuple[str, ...] = ("velocity", "tractive", "neither")

# H14: tie in soffit to soffit, never invert to invert. audit.py H14 FAILS on "invert",
# so "invert" exists in this enum only so a violation can be recorded rather than hidden.
TIE_TYPE: Tuple[str, ...] = ("none", "soffit", "invert")

# philosophy sec 5: everything past the 12 m cap is flagged with WHICH exit allowed it.
CAP_EXIT: Tuple[str, ...] = ("", "recovers_500m", "outfall_1000m")

DROP_TYPE: Tuple[str, ...] = ("none", "backdrop", "vortex")   # G203-p30, >0.60 m / >2.0 m

NODE_KIND: Tuple[str, ...] = (
    "head",        # philosophy sec 4: "a head starts at the gate"
    "chamber",     # a spacing chamber (H12) or a bend chamber
    "junction",    # two or more incoming reaches
    "drop",        # carries an external backdrop or vortex shaft
    "station",     # lifting station - a package seam as much as a depth device (P8)
    "outfall",     # works inlet or an existing structure; the only node with no DS_NODE
    "tie",         # tie-in to the existing built network (H14)
)

# P6: corridor provenance is carried to the end and never laundered. Trust levels measured
# in W10/docs/research/CORRIDOR_QUALITY.md.
SRC: Tuple[str, ...] = ("draft", "auto_road", "auto_block", "auto_link",
                        "main_pipe", "existing")

# philosophy sec 4: "A platted reserve with nothing built on it ... carries CONFIDENCE =
# provisional, its pipes are identified separately in every drawing and schedule, and it is
# never reported as existing."
CONFIDENCE: Tuple[str, ...] = ("surveyed", "drafted", "derived", "provisional")

# auto_block IS a cadastral reserve on bare desert - 45 % fronts plots of which not one is
# built. It can never be graded better than provisional, and the contract enforces it so a
# later stage cannot quietly promote 320 km of desert to "drafted".
SRC_CONFIDENCE_CEILING = {"auto_block": "provisional", "auto_link": "provisional"}
_CONF_RANK = {c: i for i, c in enumerate(CONFIDENCE)}   # surveyed 0 ... provisional 3

EDGE_KIND: Tuple[str, ...] = ("gravity", "rising", "crossing")

# G201-p71-72 via DELIVERABLE_SPEC D.1.2. "held" is not a formula - it is the honest token
# for a catchment below PF_HOLD_PROPERTIES (100), where G201 PRESCRIBES NO FORMULA. W10
# published PF with no record of which method produced it, so a peak factor could not be
# reproduced from its own row.
PF_METH: Tuple[str, ...] = ("merrimack", "peltier", "held")

# G203-p22 Tab 6 (application) and p23 Tab 7 (product matrix, read as an image by A9).
# The two tables are about DIFFERENT things and both are in force - see material_conflict().
MATERIAL: Tuple[str, ...] = ("PVC-U", "HDPE", "GRP", "GRP/PVC", "lined RCC", "DI")
PVC_MAIN_MAX_DN = 250            # G203-p22 Tab 6, main sewer, open trench: "PVC-U (up to
                                 # 250 mm)". NOT a contract invention - quoted.
PVC_PRODUCT_MAX_DN = 315         # G203-p23 Tab 7 matrix: U-PVC SN4-SN8 permitted OD 160-315,
                                 # prohibited above. This is what criteria.material() encodes.

CONSTR: Tuple[str, ...] = ("open_trench", "trenchless")

# G203-p40-41 Tab 17. Drives the Tab 21 land bands, so it is stored rather than re-derived.
ST_TYPE: Tuple[str, ...] = ("Type 1", "Type 2", "Type 3")     # <=100 / 100-300 / >300 L/s

STATION_WHY: Tuple[str, ...] = ("cap", "veto", "economics", "commissioning")

SYSTEM: Tuple[str, ...] = ("central", "satellite", "onsite", "unserved")


# --------------------------------------------------------------------------------------
# BANNED_FIELDS - names that mean two things, or that the auditor will not find
# --------------------------------------------------------------------------------------

BANNED_FIELDS: Dict[str, str] = {
    "SLOPE_PCT": ("means 'the minimum' in W10 p2_sizing and 'the laid gradient' in "
                  "DELIVERABLE_SPEC D.1.2 - one name, two meanings, and the layer cannot "
                  "say which. Use SLOPE_LAID and SLOPE_MIN, both, on every layer with a "
                  "gradient (audit G1 requires the pair)"),
    "SLOPE": "ambiguous units and ambiguous meaning. Use SLOPE_LAID / SLOPE_MIN, in percent",
    "DN_MM": "audit.py reads DN. A field the auditor cannot find is NOT_CHECKABLE",
    "US_MH": "audit.py G3 reads US_NODE. DELIVERABLE_SPEC's US_MH predates the graph",
    "DS_MH": "audit.py G3 reads DS_NODE",
    "MH_ID": "identity is NODE_UID (referenced) and NODE_REF (printed); MH_ID conflates them",
    "DEPTH": "to invert or to crown? Use DEPTH_M (to invert) and COVER_M (to crown)",
    "COVER": "same ambiguity. Use COVER_M, computed by cover() and nowhere else",
    "MAT": "the schedules and the SewerGEMS map read MATERIAL",
    "GRADIENT_B": ("the DBF truncation of GRAD_BY. If this name is on a layer, the "
                   "layer came back from a shapefile round trip and audit G2 will fail on "
                   "a design that was correct in memory. Republish from the GeoPackage"),
}


# --------------------------------------------------------------------------------------
# EXCLUDED - the register against schema regrowth
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Excluded:
    """What was proposed for the contract, refused, and what would let it in.

    A contract that survives ten stages does not fail by being wrong on day one. It fails by
    growing: each stage adds the one field it needs, nobody records why the last stage's
    field was refused, and by stage 8 the layer carries nine fields no check reads and no
    schedule prints - which is precisely how W10's pipe layer ended up with no provenance.
    Refusing is cheap. Refusing WITHOUT A RECORD is what costs, because the next stage
    proposes the same thing and nobody remembers the answer.
    """
    name: str
    proposed_for: str
    refused_because: str
    admitted_if: str


EXCLUDED: Tuple[Excluded, ...] = (
    Excluded(
        "SIZED_BY = 'infeasible'",
        "recording a reach no diameter in the series can carry within its d/D limit",
        "validate() would ACCEPT it and audit.h8 counts it as an unrecognised cause and "
        "FAILS. A contract that passes what the auditor blocks has inverted its own purpose "
        "- the contract exists so the audit holds no surprises",
        "audit.h8's `allowed` set is widened in the same commit. Until then an infeasible "
        "reach is not a sized reach: it is a station, a re-route, or a plot not served "
        "(philosophy sec 3, the four physical resolutions)"),
    Excluded(
        "SLOPE_PCT",
        "the laid gradient, per DELIVERABLE_SPEC D.1.2",
        "W10's p2_sizing used the same name for the MINIMUM. The ambiguity is the defect",
        "never. The pair SLOPE_LAID + SLOPE_MIN is what audit G1 checks for"),
    Excluded(
        "CAP_EXIT folded into the integer value of PAST_CAP",
        "one field instead of two; it matches audit.h4's `fillna(0) == 0` test exactly",
        "it cannot express the REVERSE error - a justification carried on a reach that is "
        "not past the cap, which means either the flag or the exit is wrong and neither is "
        "visible. Two fields with a cross-check catch both directions",
        "never; the pair costs one column and buys a second failure mode"),
    Excluded(
        "MultiLineString geometry on any line layer",
        "tolerated by GeoPandas on read, and W10's layers are full of it",
        "audit.Ctx.graph() takes g.geoms[0] and DISCARDS the rest, so a multipart reach "
        "corrupts H15's component count without failing any check. Silent corruption of the "
        "one check that exists to catch silent corruption",
        "never. Explode it in the stage that reads it, and account for the parts in a Funnel"),
    Excluded(
        "criteria.invert_depth_min() as the depth basis",
        "it is the existing helper and every W8 stage used it",
        "it is 50 mm shallow against audit.h3 at every DN - a BLOCKING failure on every "
        "reach. Verified across the whole DN series",
        "criteria.WALL_ALLOW and audit.h3's 0.10 allowance are reconciled. Use "
        "min_invert_depth() until they are"),
    Excluded(
        "TIER values 'sub_main' / 'trunk_main'",
        "they are what W10_existing_built.shp carries, so reading it is one line shorter",
        "audit.h9 keys its floors with a SPACE and floor.get() returns None for anything "
        "else - the pipe is skipped and the check reports PASS. A silent pass is worse than "
        "a fail",
        "audit.h9 accepts both spellings. Until then, normalise on read via TIER_ALIASES"),
    Excluded(
        "a per-stage schema (each stage declares only what its own checks read)",
        "the smallest possible contract, and every field justified by a check",
        "'a field exists because a check reads it' is the right rule for the AUDITED layer "
        "and the wrong rule for the contract. Stages 6-8 produce stations, rising mains, "
        "packages and schedules; with no declared home they invent one, which is how W10's "
        "pipe layer regrew to nine undeclared fields with no provenance",
        "never. A layer with no LayerSpec is one the auditor will never read"),
    Excluded(
        "MATERIAL chosen by criteria.material() alone",
        "it is the single source for materials and it cites its page",
        "it is application-blind: it returns PVC-U for any DN<=315, but G203-p22 Tab 6 "
        "permits PVC-U on a MAIN SEWER only up to 250 mm. Both tables are in force and they "
        "govern different things (see material_conflict())",
        "already admitted, but WITH the tier test in _cross_field. The DN315 main is an "
        "open item for NWS, not something this file decides"),
    Excluded(
        "a shapefile as the audited deliverable",
        "every downstream tool reads .shp and the client asked for shapefiles",
        "the DBF truncates GRAD_BY to GRADIENT_B and audit G2 then fails a correct "
        "design. mirror_shapefile() still writes one; assert_audited_path() stops it being "
        "handed to the auditor",
        "never for the audit. Always for CAD"),
)


# --------------------------------------------------------------------------------------
# OPEN_ITEMS - questions this file is not entitled to settle
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class OpenItem:
    id: str
    question: str
    why_open: str
    blocks: str
    resolutions: str


OPEN_ITEMS: Tuple[OpenItem, ...] = (
    OpenItem(
        "OPEN-1  [CLOSED 2026-09-02]",
        "audit.h15 required exactly ONE connected component. Philosophy sec 8a contemplates "
        "a central network, satellite works and on-site systems - more than one.",
        "CLOSED by resolution (a): H15 now reads 'zero loops, and each component terminates "
        "at exactly ONE outfall'. That is the property that actually matters - a satellite "
        "works is legal, a piece that drains NOWHERE never was. Amended in "
        "_BRAIN/08_DESIGN_PHILOSOPHY.md and in audit.h15 together, so the rule and the "
        "check say the same thing.",
        "nothing - closed",
        "n/a"),
    OpenItem(
        "OPEN-2",
        "May a MAIN sewer be PVC-U at DN315?",
        "G203-p22 Tab 6 permits PVC-U on a main sewer only 'up to 250 mm' and has rows for "
        "'up to 300 mm' and '350 mm and above' - DN315 falls in the gap between them. "
        "G203-p23 Tab 7 permits the U-PVC PRODUCT to OD315. A9 recorded the conservative "
        "reading (250 on mains) and 'confirm with NWS'; nobody has.",
        "the material column of the pipe schedule, and any DN315 main",
        "conservative default until NWS answers: HDPE or GRP on a main above DN250. "
        "_cross_field flags PVC-U on a main above 250 so the count is known, not zero."),
    OpenItem(
        "OPEN-3",
        "Is the auditor's 0.10 m bedding allowance right, or is criteria's 0.05 m?",
        "They differ by 50 mm at every diameter, and the difference is the whole margin "
        "between passing and failing H3. G203-p33 gives cover to crown and no allowance.",
        "every invert level in the design",
        "the contract uses the AUDITOR's 0.10, because designing to the shallower number "
        "fails a blocking check. If 0.05 is correct, audit.h3 and criteria.WALL_ALLOW change "
        "together and min_invert_depth() follows - never the design alone."),
    OpenItem(
        "OPEN-4",
        "tau for the tractive-force route.",
        "GUD-203 sec 4.2.2 gives NO numeric design value (GAP-9). Carried at 1.0 Pa; at 2.0 Pa "
        "the required gradient rises 2.35x, and 97 % of W10 sat on this route.",
        "the reported self-cleansing split, and any flat reach",
        "TAU_PA travels on every reach so a sensitivity run is visible in the layer itself "
        "and not only in a note. Confirm with NWS."),
)


def open_items_report() -> str:
    return "\n\n".join(
        f"{o.id}  {o.question}\n  why open : {o.why_open}\n  blocks   : {o.blocks}\n"
        f"  options  : {o.resolutions}" for o in OPEN_ITEMS)


def material_conflict(tier: str, dn: int, material: str) -> Optional[str]:
    """Is this (tier, DN, material) combination outside G203-p22 Table 6?

    The two tables are NOT in conflict - they govern different things, and reading them as a
    contradiction is what produced two different rules in two files:

      Table 7 (p23), a product matrix : U-PVC SN4-SN8 exists and is permitted OD 160-315.
                                        This is what criteria.material() encodes, correctly.
      Table 6 (p22), an application    : on a MAIN SEWER, open trench, 'PVC-U (up to
                                        250 mm), HDPE, GRP'. A tighter rule for a harder job.

    So a DN315 PVC-U lateral is fine and a DN315 PVC-U main is not, and no single
    diameter-only function can express that. Returns a message or None.
    """
    t, m = str(tier).strip().lower(), str(material).strip()
    if t in ("main", "sub main", "trunk main") and m == "PVC-U" and int(dn) > PVC_MAIN_MAX_DN:
        return (f"PVC-U on a '{tier}' at DN{int(dn)} - G203-p22 Tab 6 permits PVC-U on a "
                f"main sewer only up to {PVC_MAIN_MAX_DN} mm (HDPE or GRP above). "
                f"criteria.material() is product-based (Tab 7, OD160-315) and does not know "
                f"the tier. See OPEN-2")
    return None


# --------------------------------------------------------------------------------------
# Field and layer specification
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Field:
    """`required` and `blank_ok` are deliberately two different things.

    `required` means THE COLUMN MUST EXIST. That is the one the auditor cares about: a
    missing column is NOT_CHECKABLE, and philosophy sec 8 makes a check that cannot run
    blocking. `blank_ok` means a row may legitimately hold no value - an outfall has no
    downstream node, a reach inside the cap has no cap exit. Conflating the two either
    forces a lie into an empty cell or lets a whole column go missing.
    """
    name: str
    dtype: str                       # "str" | "int" | "float"
    units: str
    why: str                         # WHY this field exists - the rule or check it feeds
    audit: str = ""                  # the audit.py check id(s) that read it, comma separated
    required: bool = True            # the column must exist
    blank_ok: bool = False           # ... but a row may legitimately be empty
    allowed: Optional[Tuple[str, ...]] = None
    lo: Optional[float] = None
    hi: Optional[float] = None

    @property
    def shp_safe(self) -> bool:
        return len(self.name) <= SHP_FIELD_MAXLEN

    @property
    def checks(self) -> Tuple[str, ...]:
        return tuple(c.strip() for c in self.audit.split(",") if c.strip())


F = Field


@dataclass(frozen=True)
class LayerSpec:
    name: str
    geom: str                        # "Point" | "LineString" | "Polygon" | "none"
    key: Optional[str]               # the unique identifier column
    purpose: str
    fields: Tuple[Field, ...]
    audited: bool = False            # True == audit.py reads this layer directly
    refs: Tuple[Tuple[str, str, str], ...] = ()   # (column, target layer, target key)

    def field(self, name: str) -> Optional[Field]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @property
    def required_names(self) -> List[str]:
        return [f.name for f in self.fields if f.required]

    @property
    def names(self) -> List[str]:
        return [f.name for f in self.fields]


# ---- shared field groups -------------------------------------------------------------
# Provenance travels on EVERY published feature. P6: "SRC and a CONFIDENCE grade travel on
# every pipe to the drawings and the schedules."

_PROV = (
    F("SRC", "str", "-", "which corridor source this came from; trust levels differ by 20x "
      "and W10 merged them into one layer with the differences lost (P6)",
      allowed=SRC, audit="G5"),
    F("CONFIDENCE", "str", "-", "how much the corridor under this feature can be trusted; "
      "a cadastral reserve on bare desert is a legal corridor at saturation but is never "
      "reported as existing (philosophy sec 4)", allowed=CONFIDENCE, audit="G5"),
    F("STAGE", "str", "-", "the stage that last wrote this row; makes invariant 10 (no "
      "stage silently no-ops) checkable after the fact", audit="G4"),
    F("PACKAGE", "str", "-", "commissionable contract package; a station is a package seam "
      "(P8, objective 4)", required=False),
    F("PHASE", "int", "-", "delivery phase, 0 = not yet assigned", required=False),
)


# ---- the two primary layers ----------------------------------------------------------

NODES = LayerSpec(
    name="nodes",
    geom="Point",
    key="NODE_UID",
    audited=True,
    purpose=(
        "The chamber schedule AND the graph's vertex set. P4: a chamber is the unit of "
        "design. W10 ran 11.1 nodes/km against NAMA's built 32.3, and without chambers "
        "there is no schedule, no profile, no take-off, no model and no package."
    ),
    fields=(
        F("NODE_UID", "str", "-", "immutable identity, minted once by NodeIndex and never "
          "reassigned. Everything that references a chamber references THIS, so a pass-2 "
          "relabel cannot orphan a reference", audit="G3"),
        F("IS_OUTFALL", "int", "0/1", "1 where this chamber is where its system discharges. "
          "H15 requires EXACTLY ONE per connected component - not one network, because sec 8a "
          "allows satellite works, but never a piece that drains nowhere. It lives on the "
          "NODE because an outfall is a property of a chamber; audit.h15 looked for it on the "
          "PIPE layer and returned a blocking FALSE failure against a design that had one per "
          "component", audit="H15", lo=0, hi=1),
        F("NODE_REF", "str", "-", "the human/NAMA-style label (5A-2-SM.2-MH391). Derived "
          "from tier+package+sequence, recomputed freely, referenced by NOTHING - "
          "objective 3 says it must read like their network, and that must not cost "
          "referential integrity"),
        F("NODE_KIND", "str", "-", "what the structure is; drives the schedule and the "
          "drawing symbol. G203-p29 sec 4.4 lists the triggers a chamber may exist for",
          allowed=NODE_KIND),
        F("X", "float", "m", "authoritative easting. The Point geometry is BUILT from X/Y, "
          "not the other way round - geometry is a view"),
        F("Y", "float", "m", "authoritative northing"),
        F("GRD_M", "float", "m aOD", "ground level sampled from the 0.5 m VRT (rule 6). "
          "Named separately from the terrain so the audit can resample and compare"),
        F("INV_M", "float", "m aOD", "invert of the OUTGOING reach - the governing level at "
          "this structure", lo=-50.0, hi=1200.0),
        F("DEPTH_M", "float", "m", "GRD_M - INV_M. Published rather than derived so the "
          "chamber schedule and the pipe layer cannot disagree", lo=0.0, hi=40.0),
        F("COVER_M", "float", "m", "cover to the crown of the shallowest connected pipe, on "
          "that pipe's OWN outside diameter, via cover(). W10 used a hardcoded 0.30 m and "
          "shipped 45.92 km below minimum (H3, G203-p33)", audit="H3", lo=0.0, hi=40.0),
        F("TIER", "str", "-", "tier of the outgoing reach", allowed=TIERS, audit="H9"),
        F("DS_NODE", "str", "-", "THE forest invariant, stored not computed: every node has "
          "exactly one downstream node, empty only at a terminal. H15 becomes true by "
          "construction instead of by audit", audit="H15", blank_ok=True),
        F("N_IN", "int", "-", "incoming reaches; >1 makes it a junction, and junction count "
          "is how the hierarchy is measured (philosophy sec 4)", lo=0, hi=20),
        F("N_OUT", "int", "-", "outgoing reaches - 0 at a terminal, 1 everywhere else, "
          "never more. Published so it can be cross-checked against the REACH layer's own "
          "out-degree: two independently computed numbers agreeing is what catches the W10 "
          "defect where the node and pipe layers came from different solves and disagreed "
          "by up to 10.39 m of depth", audit="H15", lo=0, hi=1),
        F("INLET_DEG", "float", "deg", "smallest angle any inlet makes with the outgoing "
          "flow; G203-p30 requires >= 90 deg", audit="H10", lo=0.0, hi=360.0),
        F("INLET_FLAG", "int", "0/1", "1 where INLET_DEG is short of the minimum and a "
          "purpose-made swept channel is required. audit H10 reads this to distinguish a "
          "known, priced problem from an unnoticed one", audit="H10", lo=0, hi=1),
        F("MH_DIA", "float", "m", "internal chamber diameter. 1.0 m default; G203-p30 "
          "requires >= 1.5 m wherever an internal backdrop is unavoidable. No table exists "
          "in G203 for size against depth (verified) - this is the contractor's number and "
          "the take-off's, so it is stored, not inferred at print time",
          required=False, lo=0.5, hi=6.0),
        F("MH_MAT", "str", "-", "chamber material. G203 gives no table (it says only "
          "'sufficient size'), so this is a stated assumption per PAM-SPC, not a criterion",
          required=False, blank_ok=True),
        F("DROP_M", "float", "m", "external backdrop height; G203-p30 requires one above "
          "0.60 m and a vortex shaft above 2.0 m", lo=0.0, hi=20.0),
        F("DROP_TYPE", "str", "-", "none/backdrop/vortex - ramped and EXTERNAL to the "
          "manhole (philosophy sec 5). Never used to dodge a station", allowed=DROP_TYPE),
        F("VORTEX", "int", "0/1", "1 where DROP_M > 2.0 m and a vortex drop shaft is "
          "required (G203-p30). Its own flag because it is a different STRUCTURE with a "
          "different cost, not a deeper backdrop - the as-built has 37 that were built as "
          "backdrops anyway (P10)", lo=0, hi=1),
        F("Q_ADF_M3D", "float", "m3/d", "accumulated sanitary average dry weather flow, "
          "infiltration EXCLUDED", lo=0.0),
        F("Q_PK_LS", "float", "L/s", "accumulated peak flow including unpeaked "
          "infiltration; the number the outgoing reach is sized on", lo=0.0),
        F("N_PROP", "float", "-", "properties served at or above this node; the unit the "
          "options appraisal costs per (m per property)", lo=0.0),
        F("PAST_CAP", "int", "0/1", "1 where cover exceeds the 12 m cap", audit="H4",
          lo=0, hi=1),
        F("CAP_EXIT", "str", "-", "which philosophy sec 5 exit allowed it: recovers within "
          "500 m, or reaches the outfall within 1,000 m. Empty when PAST_CAP = 0. Nothing "
          "past the cap is final until a manufacturer's rating and NWS's station cost "
          "arrive", allowed=CAP_EXIT, audit="H4b", blank_ok=True),
    ) + _PROV,
    refs=(("DS_NODE", "nodes", "NODE_UID"),),
)


REACHES = LayerSpec(
    name="reaches",
    geom="LineString",
    key="EDGE_UID",
    audited=True,
    purpose=(
        "GRAVITY reaches only - chamber to chamber, one gradient each. This is the layer "
        "`audit.py` is pointed at as `ctx.pipes`, and every field below exists because a "
        "check reads it, a schedule prints it, or the philosophy names it. Rising mains are "
        "NOT here: H2/H5/H6/H7 solve open-channel flow and would return nonsense for a "
        "pressure pipe, and G203-p50 caps a rising main at 2.5 m/s against H7's 3.0 m/s."
    ),
    fields=(
        F("EDGE_UID", "str", "-", "immutable reach identity"),
        F("US_NODE", "str", "-", "upstream chamber. Written FROM the graph. W10 had neither "
          "field, so connectivity could only be guessed by a tolerance - which is how it "
          "published 7,919 pieces", audit="G3"),
        F("DS_NODE", "str", "-", "downstream chamber", audit="G3"),
        F("TIER", "str", "-", "rider/lateral/main/sub main/trunk main. Target shares near "
          "the as-built: lateral 66 %, sub main 18 %, trunk 5 % (philosophy sec 4). NOTE the "
          "spelling is the auditor's: H9 skips an unrecognised tier SILENTLY",
          allowed=TIERS, audit="H9"),
        F("DN", "int", "mm", "nominal diameter from the DN_SERIES; OD-designated to 315 "
          "(G203-p22 T6)", audit="H2,H3,H4,H9,H12", lo=100, hi=2000),
        F("MATERIAL", "str", "-", "G203-p22 Tab 6 by APPLICATION and p23 Tab 7 by PRODUCT. "
          "PVC-U on a main sewer only to 250 mm even though the product runs to OD315 - "
          "checked by material_conflict(), open item OPEN-2", allowed=MATERIAL),
        F("CONSTR", "str", "-", "open trench or trenchless; the material set differs "
          "(G203-p22 T6) and a crossing is priced, not assumed", allowed=CONSTR,
          required=False),
        F("LEN_M", "float", "m", "laid length; H12 tests it against the Table 12 spacing "
          "for the diameter. W10 had 4,763 reaches over the limit, longest 6,541 m. Checked "
          "against the geometry to 50 mm - every published length reads this field, not the "
          "line", audit="H12", lo=0.5, hi=250.0),
        F("SLOPE_LAID", "float", "%", "THE LAID GRADIENT, on 0.05 % steps (P1). Publishing "
          "only the minimum, as W10 did, makes velocity, fall and drop all uncheckable "
          "(philosophy sec 5, audit G1)", audit="G1,H2,H5,H6,H7,H13", lo=0.0, hi=25.0),
        F("SLOPE_MIN", "float", "%", "the governing minimum beside it - the steeper of "
          "Table 11 and the tractive minimum at this reach's own peak flow "
          "(hydra.smin_for). A layer carrying only the minimum cannot be checked; one "
          "carrying only the laid value cannot be justified", audit="G1", lo=0.0, hi=25.0),
        F("GRAD_BY", "str", "-", "what SET the laid gradient. 11 characters: this field "
          "is why the audited format is GeoPackage - a shapefile DBF truncates it to "
          "GRADIENT_B and audit G2 then fails on a correct design",
          allowed=GRAD_BY, audit="G2"),
        F("SIZED_BY", "str", "-", "what set the diameter. 'depth' and 'cover' are "
          "PROHIBITED answers (G203-p29 and Ten States sec 33.43 independently); this enum is "
          "pinned to audit.py H8's own allowed set and cannot be widened from here",
          allowed=SIZED_BY, audit="H8,G2"),
        F("CLEAN_BY", "str", "-", "which self-cleansing route this reach takes - velocity "
          "or tractive. H5 requires the route recorded, because the tractive share is a "
          "REPORTED number: it rests on tau = 1.0 Pa which G203 never gives (GAP-9), and "
          "at 2.0 Pa the requirement rises 2.35x. 97 % of W10 sat on it",
          allowed=CLEAN_BY, audit="H5"),
        F("TAU_PA", "float", "Pa", "the tractive assumption this reach was checked at, "
          "carried on the row so a sensitivity run is visible in the layer and not only in "
          "a note", lo=0.5, hi=5.0),
        F("INV_UP", "float", "m aOD", "upstream invert; H11 tests INV_UP - INV_DN against "
          "the 20 mm laying tolerance for reverse gradient", audit="H11"),
        F("INV_DN", "float", "m aOD", "downstream invert", audit="H11"),
        F("US_DEPTH", "float", "m", "ground to INVERT at the upstream node. H3/H4 subtract "
          "the reach's OWN outside diameter from this to get cover - must equal the "
          "upstream node's DEPTH_M exactly", audit="H3,H4", lo=0.0, hi=40.0),
        F("DS_DEPTH", "float", "m", "ground to invert at the downstream node",
          audit="H3,H4", lo=0.0, hi=40.0),
        F("COVER_US", "float", "m", "cover to crown upstream, from cover(), published so "
          "H3's independent recomputation has something to disagree with. G203-p33 minimum "
          "1.30 m", audit="H3", lo=0.0, hi=40.0),
        F("COVER_DN", "float", "m", "cover to crown downstream", audit="H3",
          lo=0.0, hi=40.0),
        F("QADF_M3D", "float", "m3/d", "sanitary average dry weather flow, infiltration "
          "EXCLUDED, at the ultimate horizon (philosophy sec 6: size on ultimate, check "
          "self-cleansing at start-year)", lo=0.0),
        F("QINF_LS", "float", "L/s", "infiltration, UNPEAKED (G201-p72-73, 720 L/d/km). "
          "Separate from QADF so QPK_LS is reproducible from the row", lo=0.0),
        F("PF", "float", "-", "peak factor applied to the sanitary component only", lo=1.0,
          hi=8.0),
        F("PF_METH", "str", "-", "which formula produced PF: merrimack (G201-p71, mandatory "
          "above 100 properties), peltier (comparison), or HELD - the honest token for a "
          "catchment below PF_HOLD_PROPERTIES where G201 prescribes no formula at all. W10 "
          "published PF with no method, so no peak factor could be reproduced",
          allowed=PF_METH),
        F("QPK_LS", "float", "L/s", "peak design flow = QADF x PF + QINF. The flow H2, H5, "
          "H6 and H7 all solve against", audit="H2,H5,H6,H7", lo=0.0),
        F("V_PK_MS", "float", "m/s", "velocity at peak, recomputed by H7 against the 3.0 m/s "
          "gravity maximum (G203-p27)", audit="H7", lo=0.0, hi=10.0),
        F("DOD_PK", "float", "-", "d/D at peak; 0.65 to DN350, 0.50 above (G203-p27 T10). "
          "W10 shipped 5 surcharged reaches and 66 over the limit", audit="H2",
          lo=0.0, hi=1.0),
        F("RET_MIN", "float", "min", "retention time in this reach. Philosophy sec 6: "
          "septicity is a design driver, and long flat lightly-loaded runs at Omani "
          "temperatures are the H2S combination", lo=0.0),
        F("PAST_CAP", "int", "0/1", "1 where cover exceeds 12 m. audit H4 fails outright if "
          "any reach is past the cap and this field does not exist", audit="H4",
          lo=0, hi=1),
        F("CAP_EXIT", "str", "-", "which sec 5 exit allowed it; blank inside the cap",
          allowed=CAP_EXIT, audit="H4,H4b", blank_ok=True),
        F("CAP_LEN_M", "float", "m", "length past the cap, and the distance to the recovery "
          "or the outfall - the exits are DISTANCE-bounded, so the distance is the evidence",
          audit="H4b", lo=0.0),
        F("TIE_TYPE", "str", "-", "none/soffit/invert. H14: an existing structure's invert "
          "is fixed and the design yields to it; tie SOFFIT to soffit. audit H14 cannot run "
          "at all without this field", allowed=TIE_TYPE, audit="H14"),
        F("ON_DUAL_M", "float", "m", "metres of this reach inside the dual-carriageway band. "
          "Expected 0. H1 recomputes it independently - this is the design's own claim, so "
          "a disagreement is itself the finding", audit="H1,R3", lo=0.0),
        F("ON_WADI_M", "float", "m", "metres on wadi ground (Hazard_T50y classes 4/5/6). "
          "Expected 0 except on a scheduled perpendicular crossing", audit="R4", lo=0.0),
        F("CROSS_ID", "str", "-", "links to the crossings schedule where this reach IS a "
          "crossing. H1 allows a crossing only if it is scheduled; without the link there "
          "is no schedule", blank_ok=True),
    ) + _PROV,
    refs=(("US_NODE", "nodes", "NODE_UID"),
          ("DS_NODE", "nodes", "NODE_UID"),
          ("CROSS_ID", "crossings", "CROSS_ID")),
)


# ---- derived layers ------------------------------------------------------------------

RISING_MAINS = LayerSpec(
    name="rising_mains",
    geom="LineString",
    key="EDGE_UID",
    purpose=(
        "Pressure edges, kept OUT of `reaches` on purpose. A rising main is sized on PUMP "
        "DUTY and not on arriving flow (philosophy sec 6), runs 0.75-2.5 m/s (G203-p50, not "
        "H7's 3.0), and is anaerobic by definition - so its discharge chamber is a "
        "septicity problem, not a pipe end. Same node identity, same graph."
    ),
    fields=(
        F("EDGE_UID", "str", "-", "identity"),
        F("US_NODE", "str", "-", "the station"),
        F("DS_NODE", "str", "-", "the discharge chamber"),
        F("STATION", "str", "-", "NODE_UID of the station whose duty sized this"),
        F("DN", "int", "mm", "sized on duty flow, never on arriving flow. Minimum 75 mm ID "
          "for non-clog pumps (G203-p50 sec 8.1)", lo=50, hi=2000),
        F("MATERIAL", "str", "-", "G203-p53 sec 8.3: 'the recommended pipe material for the "
          "pressure main is Ductile Iron and HDPE'; pressure class per PAM-SPC-207 (pending)",
          allowed=MATERIAL),
        F("LEN_M", "float", "m", "length", lo=0.0),
        F("Q_DUTY_LS", "float", "L/s", "pump duty from the wet-well cycle", lo=0.0),
        F("V_DUTY_MS", "float", "m/s", "0.75 to 2.5 m/s (G203-p50)", lo=0.0, hi=5.0),
        F("V_MIN_MS", "float", "m/s", "velocity at the DESIGN MINIMUM flow - G203-p50 sec 8.1 "
          "with the Tab 16 factors is explicit that the 0.75 m/s floor is held there, not "
          "at average flow. Sizing on duty alone silts the main in year one",
          required=False, lo=0.0, hi=5.0),
        F("STAT_HD_M", "float", "m", "static lift", lo=0.0),
        F("TOT_HD_M", "float", "m", "total head at duty", lo=0.0),
        F("RETENT_M", "float", "min", "retention time; G203-p50 wants it under 30 min, and "
          "beyond that the discharge chamber is a septicity design, not a note",
          required=False, lo=0.0),
        F("N_AIRV", "int", "-", "double-orifice air valves at summits (G203-p53-54 sec 8.4)",
          lo=0),
        F("N_WASH", "int", "-", "washouts at low points (G203-p53-54 sec 8.4)", lo=0),
        F("SEPTIC_FL", "int", "0/1", "1 where the discharge chamber needs septicity "
          "treatment - always 1 in practice, and recorded so it is designed rather than "
          "assumed away (G203-p55 sec 8.5)", lo=0, hi=1),
    ) + _PROV,
    refs=(("US_NODE", "nodes", "NODE_UID"), ("DS_NODE", "nodes", "NODE_UID"),
          ("STATION", "stations", "NODE_UID")),
)


STATIONS = LayerSpec(
    name="stations",
    geom="Point",
    key="NODE_UID",
    purpose=(
        "Lifting stations, each one a node in the same graph. P8: a station is a "
        "COMMISSIONING device as much as a depth device - 5A-1's station plus the one built "
        "force main is what let 60.8 km and ~5,963 properties be commissioned without first "
        "building 7 km of deep gravity trunk. WHY records which rung of the cap-and-veto "
        "ladder put it here, because economics is the third rung and never the first."
    ),
    fields=(
        F("NODE_UID", "str", "-", "the same identity the node carries in `nodes`"),
        F("NODE_REF", "str", "-", "label"),
        F("WHY", "str", "-", "cap / veto / economics / commissioning. Layers 1 and 2 can "
          "only ADD a station; economics can only make you pump EARLIER, never later "
          "(philosophy sec 5)", allowed=STATION_WHY),
        F("ST_TYPE", "str", "-", "Type 1 <=100 L/s (1 duty + 1 standby), Type 2 100-300 "
          "(2+1), Type 3 >300 (3+1) - G203-p40-41 Tab 17. Stored because it is the key to "
          "the Tab 21 land band and the pump count, and re-deriving it at print time is how "
          "seven different station counts got into circulation", allowed=ST_TYPE),
        F("Q_DUTY_LS", "float", "L/s", "duty flow", lo=0.0),
        F("LIFT_M", "float", "m", "static lift - the number that matters more than the "
          "station count, because distance-clustering only measures breach density", lo=0.0),
        F("N_PROP", "float", "-", "properties upstream", lo=0.0),
        F("Q_ADF_M3D", "float", "m3/d", "average flow through it", lo=0.0),
        F("WELL_M3", "float", "m3", "wet-well working volume. G203-p48 sec 7.8: "
          "V = 0.25 x Q x T, T = 3600 / starts-per-hour", lo=0.0),
        F("WW_STARTS", "float", "1/h", "the assumed starts per hour, DECLARED. G203-p48 "
          "sets a minimum of 10/h for motors to 30 kW, and it is the only thing that turns "
          "WELL_M3 into a number - a wet-well volume with no start rate behind it cannot be "
          "checked or costed", lo=1.0, hi=60.0),
        F("GRD_M", "float", "m aOD", "ground level at the station", required=False),
        F("FLOOD_LV", "float", "m aOD", "the 1:50-yr flood level here. G203-p38 sec 7.2: floors "
          "and every electrical item sit at least 300 mm above it. A station in a wadi "
          "margin is a siting failure that costs the whole asset, and it is invisible "
          "unless the level is on the row", lo=-50.0, hi=1200.0),
        F("LAND_M2", "float", "m2", "indicative land take. G203-p43 Tab 21 bands: Type 1 "
          "50-100, Type 2 200-400, Type 3 >=900 m2, plus a 6 m turning circle. This is a "
          "land RESERVATION the client has to make, so it belongs in the concept output",
          lo=0.0),
        F("RM_EDGE", "str", "-", "EDGE_UID of its rising main", required=False),
        F("COMM_PT", "int", "0/1", "1 where this station makes its package commissionable "
          "on its own - the P8 case where objective 4 beats objective 5", required=False,
          lo=0, hi=1),
    ) + _PROV,
    refs=(("NODE_UID", "nodes", "NODE_UID"),),
)


CONNECTIONS = LayerSpec(
    name="connections",
    geom="LineString",
    key="CONN_ID",
    purpose=(
        "One row per LOAD UNIT, and the direct answer to invariant 1: every load unit is "
        "assigned to exactly one chamber, or listed by name. W10 dropped 1,233 m3/d - 1.7 % "
        "- silently, because an assignment radius failed quietly. A load with no OUT_NODE "
        "must carry a WHY, and the Funnel that produced it must name the ids."
    ),
    fields=(
        F("CONN_ID", "str", "-", "identity"),
        F("PLOT_ID", "str", "-", "the plot from W10_plot_loads.gpkg (64,071 records, "
          "74,675 m3/d)"),
        F("OUT_NODE", "str", "-", "the chamber this load enters the network at. Empty ONLY "
          "when WHY says why, and then the plot appears in the not-served schedule - the "
          "TOR (scope p4 item 3) requires every plot SERVED, though not necessarily by this "
          "network", blank_ok=True),
        F("WHY", "str", "-", "why it is unassigned, or 'assigned'. Never blank"),
        F("SYSTEM", "str", "-", "which system serves it: the central network, a satellite "
          "works, or on-site. Philosophy sec 8a - 'serviced' is not 'connected to one network', "
          "and that distinction is the whole design question", allowed=SYSTEM),
        F("CONN_TYPE", "str", "-", "PCS / rider / lateral. G203-p17 sec 3.2 fixes the chain "
          "PCC -> PC sewer -> HCC -> rider -> lateral, and the limits differ per link",
          required=False),
        F("Q_ADF_M3D", "float", "m3/d", "the load", lo=0.0),
        F("N_PROP", "float", "-", "properties on the plot (electricity accounts, 1.456 "
          "average)", lo=0.0),
        F("LEN_M", "float", "m", "connection length; G203-p18 T4 note caps a property "
          "connection at 50 m", lo=0.0),
        F("SLOPE_LAID", "float", "%", "3-10 % for a property connection, 1-10 % for a rider "
          "or lateral (G203-p18 T5). Named SLOPE_LAID, not SLOPE_PCT: the same name meant "
          "two different gradients in two W10 files and the layer could not say which",
          lo=0.0, hi=30.0),
        F("COVER_M", "float", "m", "0.60 m minimum on a property connection (G203-p19 3.5)",
          lo=0.0),
        F("CAN_DRAIN", "int", "0/1", "does the plot outlet sit above the sewer invert where "
          "it joins. 0 is not a rounding error - it is a plot the gravity network does not "
          "actually serve, and it must reach the not-served schedule", required=False,
          lo=0, hi=1),
    ) + _PROV,
    refs=(("OUT_NODE", "nodes", "NODE_UID"),),
)


CORRIDORS = LayerSpec(
    name="corridors",
    geom="LineString",
    key="CORR_ID",
    purpose=(
        "Stage 2 output: the legal routes, with the wadi and dual-carriageway exclusions "
        "already applied AT SOURCE (philosophy sec 2 - 'exclusions apply HERE, not in the "
        "router'). The perverse W10 result this exists to stop: the sources trusted least "
        "were used most - auto_block 97.4 % converted to pipe against draft's 76.3 %."
    ),
    fields=(
        F("CORR_ID", "str", "-", "identity"),
        F("LEN_M", "float", "m", "length", lo=0.0),
        F("WIDTH_M", "float", "m", "public reserve width; philosophy sec 4 requires a reserve "
          "of STATED width and 3 m clearance to other utilities (G203-p33). The corridor "
          "widths themselves are G203-p32 Tab 13 by diameter", lo=0.0),
        F("ON_DUAL_M", "float", "m", "expected 0 after the exclusion", lo=0.0),
        F("ON_WADI_M", "float", "m", "expected 0 after the exclusion", lo=0.0),
        F("IS_STREET", "int", "0/1", "1 = an observed built street; 0 = a platted reserve "
          "with nothing built on it, which is a legitimate corridor at a saturation horizon "
          "but is NEVER reported as existing (philosophy sec 4)", lo=0, hi=1),
        F("N_PLOT", "int", "-", "load-bearing plots fronting it. P7: 117.3 km of W10 had "
          "none within 60 m and carried under 1 m3/d - it neither collected nor conveyed",
          lo=0),
        F("USED", "int", "0/1", "1 where a reach was laid on it; the conversion rate per "
          "SRC is the number that exposed the W10 inversion", lo=0, hi=1),
        F("CROSS_ID", "str", "-", "links to the crossings schedule where this corridor "
          "CROSSES a wadi. H1a makes a crossing legal and an unscheduled one is not, so a "
          "corridor with ON_WADI_M > 0 and no CROSS_ID is a defect, not a rounding residue",
          blank_ok=True),
    ) + _PROV,
)


CROSSINGS = LayerSpec(
    name="crossings",
    geom="LineString",
    key="CROSS_ID",
    purpose=(
        "The schedule H1 demands. 'Crossings perpendicular and scheduled' - W10 had 47 "
        "unscheduled ones. A crossing that is not on this layer is not a crossing; it is a "
        "pipe in a place it may not be."
    ),
    fields=(
        F("CROSS_ID", "str", "-", "identity, referenced by the reach"),
        F("EDGE_UID", "str", "-", "the reach that crosses"),
        F("OBSTACLE", "str", "-", "dual / wadi / road / utility",
          allowed=("dual", "wadi", "road", "utility")),
        F("LEN_M", "float", "m", "crossing length; criteria.DUAL_CROSS_MAX_M caps a dual "
          "crossing at 70 m", lo=0.0),
        F("ANGLE_DEG", "float", "deg", "angle to the obstacle; must be near square "
          "(criteria.DUAL_CROSS_SQUARE_DEG = 25 deg off)", lo=0.0, hi=180.0),
        F("METHOD", "str", "-", "open cut / thrust bore / microtunnel - a crossing needs "
          "trenchless work and it is priced, not assumed",
          allowed=("open_cut", "thrust_bore", "microtunnel", "existing_underpass")),
        F("COVER_M", "float", "m", "cover at the crossing. G203-p52 sec 8.2.4 requires 1.5 m "
          "to crown at a wadi crossing against 1.30 m normal - the one place H3's number "
          "is not the governing one", required=False, lo=0.0),
        F("APPROVED", "int", "0/1", "1 once a third-party consent exists; 0 is an open item, "
          "not a silent one", lo=0, hi=1),
    ) + _PROV,
)


PACKAGES = LayerSpec(
    name="packages",
    geom="none",
    key="PACKAGE",
    purpose=(
        "One row per commissionable contract package. P8: a package is 3.5-40 km serving "
        "180-2,180 plots, ONE connected tree with EXACTLY ONE outlet. W10's 206 subnetworks "
        "were unusable as packages - median 1.16 km, largest 265.8 km."
    ),
    fields=(
        F("PACKAGE", "str", "-", "identity"),
        F("PHASE", "int", "-", "delivery phase", lo=0),
        F("LEN_KM", "float", "km", "3.5-40 km", lo=0.0),
        F("N_PLOT", "int", "-", "180-2,180 plots", lo=0),
        F("OUTLET", "str", "-", "the single NODE_UID it discharges at"),
        F("DS_PKG", "str", "-", "the package downstream; NAMA's own chain is "
          "5A-3 -> 5A-2 -> 5A-4 -> 5A-1 -> station -> force main -> STP, so no package "
          "commissions before its downstream neighbour exists", required=False),
        F("COMM_SEQ", "int", "-", "commissioning order", required=False, lo=0),
        F("INDEP", "int", "0/1", "1 where it can be commissioned WITHOUT its downstream "
          "neighbour - it ends at a station, at the works, or at the existing network. This "
          "is the P8 property a station buys", required=False, lo=0, hi=1),
        F("ONE_TREE", "int", "0/1", "1 = one connected tree with one outlet. 0 is a failed "
          "package, not a note", lo=0, hi=1),
    ),
    refs=(("OUTLET", "nodes", "NODE_UID"),),
)


LAYERS: Dict[str, LayerSpec] = {s.name: s for s in (
    NODES, REACHES, RISING_MAINS, STATIONS, CONNECTIONS, CORRIDORS, CROSSINGS, PACKAGES)}

# audit.py names its two layers `pipes` and `nodes`; run_audit.py loads them by filename.
LAYER_ALIASES = {"pipes": "reaches", "W11a_pipes": "reaches", "W11a_nodes": "nodes",
                 "manholes": "nodes", "W11a_manholes": "nodes"}


def _spec(layer_name: str) -> LayerSpec:
    key = layer_name if layer_name in LAYERS else LAYER_ALIASES.get(layer_name, layer_name)
    spec = LAYERS.get(key)
    if spec is None:
        raise ContractError(
            f"no contract for layer '{layer_name}'. Known layers: "
            + ", ".join(sorted(LAYERS)) + ". Add a LayerSpec before publishing it - an "
            "unspecified layer is one the auditor will never read, and inventing a schema "
            "at the point of writing is how W10's pipe layer grew nine fields with no "
            "provenance (EXCLUDED: 'a per-stage schema').")
    return spec


# --------------------------------------------------------------------------------------
# validate() - the gate. Every stage calls it before it writes and after it reads.
# --------------------------------------------------------------------------------------

def _kind(s: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(s):
        return "num"
    return "str"


def _missing_mask(s: pd.Series, dtype: str = "str"):
    """A shapefile round-trip turns a null string into '' and a null int into 0. Both read
    as present and both are absent. Treat '' as missing for a string; only true NaN for a
    number, because 0 is a legitimate depth, flow or flag."""
    if dtype == "str":
        return s.isna() | (s.astype(str).str.strip().isin(["", "nan", "None", "<NA>"]))
    return s.isna()


def _blank(s: pd.Series):
    return _missing_mask(s, "str")


def _fmt_rows(idx, n=5) -> str:
    ids = list(idx[:n])
    more = "" if len(idx) <= n else f" ... (+{len(idx) - n} more)"
    return ", ".join(str(i) for i in ids) + more


def validate(gdf, layer_name: str, *, stage: str = "", strict: bool = True,
             allow_extra: bool = True):
    """Check a layer against its spec. Raise ContractError listing EVERY problem at once.

    Returns the frame, so it composes: `gdf = validate(gdf, "reaches", stage="S5")`.

    Why it raises rather than warns: `audit.py` scores a missing field as NOT_CHECKABLE, and
    the philosophy (sec 8) makes any check that cannot run BLOCKING. A stage that writes a
    layer without `GRAD_BY` has not published a slightly incomplete layer - it has
    published an unauditable one, and thirteen of W10's 22 checks died exactly there.

    `strict=False` relaxes the value checks (enums, ranges, cross-field consistency) but
    NEVER the missing-field check, because that is the one the auditor cannot recover from.
    """
    spec = _spec(layer_name)

    if not isinstance(gdf, pd.DataFrame):
        raise ContractError(f"layer '{spec.name}': expected a (Geo)DataFrame, got "
                            f"{type(gdf).__name__}")

    problems: List[str] = []
    notes: List[str] = []
    cols = set(gdf.columns)
    n = len(gdf)

    # ---- 1. missing required fields. The headline, and the only check strict=False keeps.
    missing = [f for f in spec.fields if f.required and f.name not in cols]
    if missing:
        w = max(len(f.name) for f in missing)
        lines = [f"  {f.name:<{w}}  {f.dtype:<5} {f.units:<6} {f.why.split('.')[0][:78]}"
                 + (f"   -> audit {f.audit}" if f.audit else "")
                 for f in missing]
        problems.append(
            "MISSING REQUIRED FIELDS (audit.py scores a missing field as NOT_CHECKABLE, "
            "which philosophy sec 8 makes blocking - not a blank):\n" + "\n".join(lines))

    # ---- 2. banned names. A name that means two things is worse than a missing one.
    banned = sorted(cols & set(BANNED_FIELDS))
    if banned:
        problems.append("BANNED FIELD NAMES:\n" + "\n".join(
            f"  {b}: {BANNED_FIELDS[b]}" for b in banned))

    if not allow_extra:
        extra = sorted(cols - set(spec.names) - set(BANNED_FIELDS) - {"geometry"})
        if extra:
            problems.append("UNDECLARED FIELDS (add them to the LayerSpec with a `why`, or "
                            "drop them; an undeclared field is one nothing checks and "
                            "nothing prints): " + ", ".join(extra))

    present = [f for f in spec.fields if f.name in cols]

    if strict and n:
        # ---- 3. nulls in required fields
        for f in present:
            if not f.required or f.blank_ok:
                continue
            m = _missing_mask(gdf[f.name], f.dtype)
            if m.any():
                problems.append(
                    f"NULL in required field {f.name}: {int(m.sum()):,} of {n:,} rows "
                    f"(rows {_fmt_rows(gdf.index[m])}). {f.why.split('.')[0]}")

        # ---- 4. enum membership. Lowercase exact - the auditor lowercases before matching,
        #        and an unrecognised value is a SILENT PASS in H9, not a failure.
        for f in present:
            if not f.allowed:
                continue
            vals = gdf[f.name].astype(str).str.strip()
            bad = ~vals.isin(f.allowed)
            if f.required or f.blank_ok:
                bad &= ~_missing_mask(gdf[f.name], f.dtype)
            if bad.any():
                seen = sorted(set(vals[bad]))[:8]
                hint = ""
                if f.name == "TIER":
                    alias = [v for v in seen if v.lower() in TIER_ALIASES]
                    if alias:
                        hint = ("  <- these are the UNDERSCORE forms. audit.py H9 does "
                                "floor.get(tier) and skips an unrecognised tier SILENTLY, "
                                "so this would have passed the audit unchecked. Use: "
                                + ", ".join(TIER_ALIASES[v.lower()] for v in alias))
                problems.append(
                    f"ILLEGAL VALUE in {f.name}: {int(bad.sum()):,} rows carry "
                    f"{seen}; allowed are {list(f.allowed)}.{hint}")

        # ---- 5. ranges
        for f in present:
            if f.lo is None and f.hi is None:
                continue
            if _kind(gdf[f.name]) != "num":
                continue
            s = pd.to_numeric(gdf[f.name], errors="coerce")
            bad = pd.Series(False, index=gdf.index)
            if f.lo is not None:
                bad |= s < f.lo
            if f.hi is not None:
                bad |= s > f.hi
            bad &= s.notna()
            if bad.any():
                problems.append(
                    f"OUT OF RANGE in {f.name} [{f.lo}, {f.hi}] {f.units}: "
                    f"{int(bad.sum()):,} rows, worst {s[bad].min():g} / {s[bad].max():g} "
                    f"(rows {_fmt_rows(gdf.index[bad])})")

        # ---- 6. key uniqueness. Duplicate identity is how a graph turns into a pile.
        if spec.key and spec.key in cols:
            dup = gdf[spec.key].duplicated(keep=False)
            if dup.any():
                problems.append(
                    f"DUPLICATE {spec.key}: {int(dup.sum()):,} rows share "
                    f"{gdf[spec.key][dup].nunique():,} identifiers. Identity is minted once "
                    "by NodeIndex/Network and never reused.")

        problems += _cross_field(gdf, spec, cols)

    # ---- 7. geometry and CRS
    if spec.geom != "none":
        if not isinstance(gdf, gpd.GeoDataFrame) or "geometry" not in cols:
            problems.append(f"layer '{spec.name}' must be a GeoDataFrame with "
                            f"{spec.geom} geometry")
        else:
            if gdf.crs is None:
                problems.append(f"layer '{spec.name}' has no CRS; every layer is "
                                f"EPSG:{CRS_EPSG} (project rule)")
            elif gdf.crs.to_epsg() != CRS_EPSG:
                problems.append(f"layer '{spec.name}' is EPSG:{gdf.crs.to_epsg()}, must be "
                                f"EPSG:{CRS_EPSG}")
            if n:
                gt = set(gdf.geom_type.dropna().unique())
                multi = {g for g in gt if str(g).startswith("Multi")}
                if multi:
                    # NOT tolerated. audit.Ctx.graph() takes g.geoms[0] and discards the
                    # rest, so a multipart reach silently corrupts the component count of
                    # the one check that exists to catch silent corruption.
                    problems.append(
                        f"MULTIPART GEOMETRY on '{spec.name}': {sorted(multi)}. "
                        "audit.Ctx.graph() reads g.geoms[0] and DROPS every other part, so "
                        "H15 would report a component count for a network it only half "
                        "read. Explode in the stage that reads it and account for the extra "
                        "parts in a Funnel - a part silently discarded is a reach nobody "
                        "designed.")
                other = gt - {spec.geom} - multi
                if other:
                    problems.append(f"layer '{spec.name}' holds geometry {sorted(other)}, "
                                    f"expected {spec.geom}")
                if gdf.geometry.isna().any() or (~gdf.geometry.is_valid).any():
                    problems.append(f"layer '{spec.name}' has null or invalid geometry")

                # ---- LEN_M must measure the line it sits on. H12 and every published
                #      length read the FIELD, not the geometry; to_edges_gdf writes them
                #      together but a merge, a clip or a hand edit parts them silently.
                if spec.geom == "LineString" and "LEN_M" in cols and not multi:
                    claim = pd.to_numeric(gdf["LEN_M"], errors="coerce")
                    real = gdf.geometry.length
                    d = (claim - real).abs()
                    bad = d > LEN_TOL_M
                    bad &= claim.notna()
                    if bad.any():
                        problems.append(
                            f"LEN_M disagrees with its own geometry on {int(bad.sum()):,} "
                            f"rows by more than {LEN_TOL_M} m, worst {d[bad].max():.3f} m. "
                            "H12 and every published length read the FIELD; if the two have "
                            "parted, the schedule and the drawing are describing different "
                            "pipes.")

    # ---- 8. shapefile-safety NOTE, never an error. GPKG is the audited format.
    unsafe = [f.name for f in spec.fields if not f.shp_safe]
    if unsafe:
        notes.append("not shapefile-safe (>10 char DBF names): " + ", ".join(unsafe)
                     + " - publish this layer as GeoPackage; mirror_shapefile() is for CAD "
                       "only and assert_audited_path() refuses to hand a .shp to the auditor")

    if problems:
        head = (f"CONTRACT VIOLATION - layer '{spec.name}', {n:,} rows"
                + (f", written by {stage}" if stage else "")
                + f"\n{spec.purpose}\n")
        body = "\n\n".join(problems)
        tail = ("\n\nFix this in the stage that WRITES the layer. The auditor is not the "
                "place to relax a field it needs.")
        if notes:
            tail += "\n\nNote: " + "\n      ".join(notes)
        raise ContractError(head + "\n" + body + tail)
    return gdf


def _cross_field(gdf, spec: LayerSpec, cols) -> List[str]:
    """Consistency rules between fields of one row. Each is a rule the auditor cannot see,
    because it recomputes from geometry and terrain rather than from the row."""
    out: List[str] = []

    def has(*c):
        return all(x in cols for x in c)

    if spec.name == "nodes":
        # DEPTH_M is published rather than derived, so it must agree with the levels it
        # was derived from. A chamber schedule and a pipe layer that disagree on depth is
        # how a design gets built to the wrong invert.
        if has("GRD_M", "INV_M", "DEPTH_M"):
            d = (pd.to_numeric(gdf.GRD_M, errors="coerce")
                 - pd.to_numeric(gdf.INV_M, errors="coerce")
                 - pd.to_numeric(gdf.DEPTH_M, errors="coerce")).abs()
            bad = d > 0.001
            if bad.any():
                out.append(f"DEPTH_M != GRD_M - INV_M on {int(bad.sum()):,} nodes, worst "
                           f"{d[bad].max():.3f} m")
        # The forest, stated on the node: exactly one terminal kind per empty DS_NODE.
        if has("DS_NODE", "NODE_KIND"):
            term = _blank(gdf.DS_NODE)
            kinds = gdf.NODE_KIND.astype(str)
            bad = term & ~kinds.isin(["outfall", "station", "tie"])
            if bad.any():
                out.append(f"{int(bad.sum()):,} nodes have no DS_NODE but are not an "
                           "outfall, a station or a tie. A terminal node is where flow "
                           "LEAVES the network; anything else with no downstream is a "
                           "dead end the design forgot")
        # N_OUT is 1 everywhere but a terminal. The value of publishing it is that it is
        # computed from the NODE side and checked against the REACH side (assert_degrees):
        # two independent numbers agreeing is what would have caught the W10 defect where
        # the node and pipe layers came from different solves.
        if has("N_OUT", "DS_NODE"):
            nout = pd.to_numeric(gdf.N_OUT, errors="coerce").fillna(-1)
            term = _blank(gdf.DS_NODE)
            bad = (term & (nout != 0)) | ((~term) & (nout != 1))
            if bad.any():
                out.append(f"N_OUT contradicts DS_NODE on {int(bad.sum()):,} "
                           "nodes: a node with a downstream has exactly one outgoing reach, "
                           "and a terminal has none")
        if has("PAST_CAP", "CAP_EXIT"):
            pc = pd.to_numeric(gdf.PAST_CAP, errors="coerce").fillna(0) == 1
            if (pc & _blank(gdf.CAP_EXIT)).any():
                out.append(f"{int((pc & _blank(gdf.CAP_EXIT)).sum()):,} chambers past the "
                           "12 m cap with no exit named (philosophy sec 5)")
        # G203-p30: backdrop above 0.60 m, vortex shaft above 2.0 m. The as-built has 37
        # drops over 2 m built as plain backdrops (P10) - copy the shape, not the sizing.
        if has("DROP_M", "DROP_TYPE"):
            d = pd.to_numeric(gdf.DROP_M, errors="coerce").fillna(0.0)
            t = gdf.DROP_TYPE.astype(str).str.lower()
            bad = (d > C.DROP_TRIGGER + 1e-9) & (t == "none")
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers drop more than "
                           f"{C.DROP_TRIGGER} m with DROP_TYPE='none'. G203-p30 requires a "
                           "backdrop above that, external and ramped")
            bad = (d > C.BACKDROP_MAX + 1e-9) & (t != "vortex")
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers drop more than "
                           f"{C.BACKDROP_MAX} m without a vortex shaft (G203-p30). The "
                           "as-built has 37 of these built as backdrops; that is the "
                           "calibration reference being wrong, not a precedent")
        if has("DROP_M", "VORTEX"):
            d = pd.to_numeric(gdf.DROP_M, errors="coerce").fillna(0.0)
            v = pd.to_numeric(gdf.VORTEX, errors="coerce").fillna(0) == 1
            bad = v != (d > C.BACKDROP_MAX + 1e-9)
            if bad.any():
                out.append(f"VORTEX disagrees with DROP_M on {int(bad.sum()):,} chambers "
                           f"(the trigger is {C.BACKDROP_MAX} m, G203-p30)")

    if spec.name == "reaches":
        # The laid gradient is never below the minimum it publishes beside itself (H6).
        if has("SLOPE_LAID", "SLOPE_MIN"):
            bad = pd.to_numeric(gdf.SLOPE_LAID, errors="coerce") < \
                  pd.to_numeric(gdf.SLOPE_MIN, errors="coerce") - 1e-9
            if bad.any():
                out.append(f"SLOPE_LAID below SLOPE_MIN on {int(bad.sum()):,} reaches - the "
                           "row contradicts itself before the auditor even runs (H6, "
                           "G203-p29 T11)")
        # P1: laid on round 0.05 % steps so the drawing matches the levels.
        if has("SLOPE_LAID"):
            s = pd.to_numeric(gdf.SLOPE_LAID, errors="coerce")
            off = ((s / SLOPE_STEP_PCT) - (s / SLOPE_STEP_PCT).round()).abs() > 1e-6
            off &= s.notna()
            if off.any():
                out.append(f"SLOPE_LAID off the {SLOPE_STEP_PCT} % step on "
                           f"{int(off.sum()):,} reaches (P1). If rounding a run created a "
                           "pumping station, relax the rounding on that run and say so - "
                           "P1 is never bought at the price of a station")
        # Fall must agree with gradient and length, or the levels are decoration.
        if has("INV_UP", "INV_DN", "LEN_M", "SLOPE_LAID"):
            fall = pd.to_numeric(gdf.INV_UP, errors="coerce") - \
                   pd.to_numeric(gdf.INV_DN, errors="coerce")
            want = pd.to_numeric(gdf.LEN_M, errors="coerce") * \
                   pd.to_numeric(gdf.SLOPE_LAID, errors="coerce") / 100.0
            bad = (fall - want).abs() > 0.021          # the 20 mm laying tolerance (H11)
            bad &= fall.notna() & want.notna()
            if bad.any():
                out.append(f"INV_UP - INV_DN disagrees with LEN_M x SLOPE_LAID by more than "
                           f"the 20 mm laying tolerance on {int(bad.sum()):,} reaches "
                           "(H11, G203-p29)")
        # Cover is cover() and nothing else, on the reach's OWN outside diameter.
        for depth_c, cov_c in (("US_DEPTH", "COVER_US"), ("DS_DEPTH", "COVER_DN")):
            if has("DN", depth_c, cov_c):
                want = pd.to_numeric(gdf[depth_c], errors="coerce") - (
                    pd.to_numeric(gdf.DN, errors="coerce") / 1000.0 + AUDITOR_OD_ALLOW_M)
                got = pd.to_numeric(gdf[cov_c], errors="coerce")
                bad = (got - want).abs() > 0.001
                bad &= got.notna() & want.notna()
                if bad.any():
                    out.append(
                        f"{cov_c} != {depth_c} - (DN/1000 + {AUDITOR_OD_ALLOW_M}) on "
                        f"{int(bad.sum()):,} reaches. That subtraction is cover() and it is "
                        "the ONLY definition - W10 used a hardcoded 0.30 m regardless of "
                        "diameter and shipped 45.92 km below minimum cover (H3, G203-p33)")
        # QPK_LS must be reproducible from the row: sanitary peaked, infiltration not.
        if has("QADF_M3D", "PF", "QINF_LS", "QPK_LS"):
            want = (pd.to_numeric(gdf.QADF_M3D, errors="coerce") * 1000.0 / 86400.0
                    * pd.to_numeric(gdf.PF, errors="coerce")
                    + pd.to_numeric(gdf.QINF_LS, errors="coerce"))
            got = pd.to_numeric(gdf.QPK_LS, errors="coerce")
            bad = (got - want).abs() > (0.01 * want.abs() + 0.01)
            bad &= got.notna() & want.notna()
            if bad.any():
                out.append(
                    f"QPK_LS != QADF_M3D x PF + QINF_LS on {int(bad.sum()):,} reaches - "
                    "infiltration is UNPEAKED (G201-p72-73), so the peak flow must be "
                    "reproducible from its own row")
        # Past the cap without an exit is a breach, not a flag.
        if has("PAST_CAP", "CAP_EXIT"):
            pc = pd.to_numeric(gdf.PAST_CAP, errors="coerce").fillna(0) == 1
            noex = gdf.CAP_EXIT.astype(str).str.strip() == ""
            if (pc & noex).any():
                out.append(f"{int((pc & noex).sum()):,} reaches PAST_CAP=1 with no CAP_EXIT. "
                           "Philosophy sec 5 gives exactly two exits - cover recovers within "
                           "500 m, or the run reaches the outfall within 1,000 m. Neither "
                           "means a station, not a flag")
            if ((~pc) & (~noex)).any():
                out.append(f"{int(((~pc) & (~noex)).sum()):,} reaches carry a CAP_EXIT but "
                           "PAST_CAP=0 - a justification for a breach that is not there")
        # The exits are DISTANCE-bounded, so the distance has to be on the row (H4b).
        if has("CAP_EXIT", "CAP_LEN_M"):
            ex = gdf.CAP_EXIT.astype(str).str.strip()
            L = pd.to_numeric(gdf.CAP_LEN_M, errors="coerce").fillna(0.0)
            bad = (ex == "recovers_500m") & (L > 500.0 + 1e-6)
            if bad.any():
                out.append(f"{int(bad.sum()):,} reaches claim "
                           "'recovers_500m' with CAP_LEN_M over 500 m - the exit is bounded "
                           "by that distance and the row disproves itself (philosophy sec 5)")
            bad = (ex == "outfall_1000m") & (L > 1000.0 + 1e-6)
            if bad.any():
                out.append(f"{int(bad.sum()):,} reaches claim 'outfall_1000m' with "
                           "CAP_LEN_M over 1,000 m (philosophy sec 5)")
        # A crossing must be scheduled to be legal (H1).
        if has("ON_DUAL_M", "CROSS_ID"):
            on = pd.to_numeric(gdf.ON_DUAL_M, errors="coerce").fillna(0) > 0
            uns = gdf.CROSS_ID.astype(str).str.strip() == ""
            if (on & uns).any():
                out.append(f"{int((on & uns).sum()):,} reaches touch a dual carriageway with "
                           "no CROSS_ID. W10 shipped 47 unscheduled crossings; H1 permits a "
                           "crossing only as a scheduled perpendicular one")
        # H14: soffit to soffit, never invert to invert.
        if has("TIE_TYPE"):
            bad = gdf.TIE_TYPE.astype(str).str.lower() == "invert"
            if bad.any():
                out.append(f"{int(bad.sum()):,} tie-ins made INVERT to invert. H14: tie "
                           "soffit to soffit - an existing structure's invert is fixed and "
                           "the design yields to it")
        # G203-p22 Tab 6 by application, not p23 Tab 7 by product. See OPEN-2.
        if has("TIER", "DN", "MATERIAL"):
            msgs = [material_conflict(t, d, m) for t, d, m in
                    zip(gdf.TIER, pd.to_numeric(gdf.DN, errors="coerce").fillna(0).astype(int),
                        gdf.MATERIAL)]
            hits = [m for m in msgs if m]
            if hits:
                out.append(f"{len(hits):,} reaches: {hits[0]}")
        # PF_METH 'held' is only honest below the threshold G201 sets it for.
        if has("PF_METH", "PF"):
            held = gdf.PF_METH.astype(str).str.lower() == "held"
            if held.any() and "N_PROP" in cols:
                np_ = pd.to_numeric(gdf.N_PROP, errors="coerce").fillna(0)
                bad = held & (np_ > C.PF_HOLD_PROPERTIES)
                if bad.any():
                    out.append(f"{int(bad.sum()):,} reaches carry PF_METH='held' above "
                               f"{C.PF_HOLD_PROPERTIES} properties, where G201-p71 makes "
                               "Merrimack mandatory. 'held' is for the catchment G201 gives "
                               "no formula for, not for one nobody computed")

    if spec.name in ("reaches", "nodes", "corridors", "connections", "crossings"):
        # P6: provenance is never laundered. auto_block is a cadastral reserve on bare
        # desert and can never be graded better than provisional.
        if has("SRC", "CONFIDENCE"):
            for src, ceiling in SRC_CONFIDENCE_CEILING.items():
                m = (gdf.SRC.astype(str) == src) & \
                    gdf.CONFIDENCE.astype(str).map(
                        lambda c: _CONF_RANK.get(c, 99) < _CONF_RANK[ceiling])
                if m.any():
                    out.append(f"{int(m.sum()):,} rows grade SRC='{src}' better than "
                               f"'{ceiling}'. It is a cadastral reserve, not an observed "
                               "street - 45 % of it fronts plots of which not one is built. "
                               "Provenance is carried to the end, never laundered (P6)")

    if spec.name == "connections":
        if has("OUT_NODE", "WHY"):
            unassigned = _missing_mask(gdf.OUT_NODE, "str")
            blank = _blank(gdf.WHY)
            if (unassigned & blank).any():
                out.append(f"{int((unassigned & blank).sum()):,} load units have no "
                           "OUT_NODE and no WHY. W10 lost 1,233 m3/d (1.7 %) exactly this "
                           "way - invariant 1: assigned to one chamber, or listed by name")
        if has("OUT_NODE", "SYSTEM"):
            unassigned = _missing_mask(gdf.OUT_NODE, "str")
            central = gdf.SYSTEM.astype(str) == "central"
            if (unassigned & central).any():
                out.append(f"{int((unassigned & central).sum()):,} load units are marked "
                           "SYSTEM='central' with no chamber to enter at. 'Serviced' is not "
                           "'connected to one network' (sec 8a) - say which system, or the "
                           "plot is silently unserved against scope p4 item 3")

    if spec.name == "stations":
        # G203-p40-41 Tab 17 sets the type by duty flow; p43 Tab 21 sets the land by type.
        if has("ST_TYPE", "Q_DUTY_LS"):
            q = pd.to_numeric(gdf.Q_DUTY_LS, errors="coerce")
            t = gdf.ST_TYPE.astype(str)
            want = pd.Series(["Type 1"] * len(gdf), index=gdf.index)
            want[q > 100.0] = "Type 2"
            want[q > 300.0] = "Type 3"
            bad = (t != want) & q.notna()
            if bad.any():
                out.append(f"ST_TYPE contradicts Q_DUTY_LS on {int(bad.sum()):,} stations. "
                           "G203-p40-41 Tab 17: Type 1 <= 100 L/s, Type 2 100-300, "
                           "Type 3 > 300 - the type sets the pump count AND the land band")
        if has("ST_TYPE", "LAND_M2"):
            floor = {"Type 1": 50.0, "Type 2": 200.0, "Type 3": 900.0}
            need = gdf.ST_TYPE.astype(str).map(floor)
            got = pd.to_numeric(gdf.LAND_M2, errors="coerce")
            bad = got.notna() & need.notna() & (got < need - 1e-6)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations reserve less land than the "
                           "G203-p43 Tab 21 minimum for their type (50 / 200 / 900 m2, plus "
                           "a 6 m turning circle). A reservation the client cannot build in "
                           "is worse than none")
        if has("WELL_M3", "WW_STARTS", "Q_DUTY_LS"):
            q = pd.to_numeric(gdf.Q_DUTY_LS, errors="coerce") / 1000.0     # m3/s
            st = pd.to_numeric(gdf.WW_STARTS, errors="coerce")
            want = 0.25 * q * (3600.0 / st)
            got = pd.to_numeric(gdf.WELL_M3, errors="coerce")
            bad = (got - want).abs() > (0.05 * want.abs() + 0.05)
            bad &= got.notna() & want.notna()
            if bad.any():
                out.append(f"WELL_M3 != 0.25 x Q x (3600/starts) on {int(bad.sum()):,} "
                           "stations (G203-p48 sec 7.8). The volume, the duty and the start "
                           "rate are one equation; publishing them so they disagree means "
                           "one of the three was never computed")
        if has("WW_STARTS"):
            st = pd.to_numeric(gdf.WW_STARTS, errors="coerce")
            bad = st.notna() & (st < 10.0)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations assume fewer than 10 starts/h. "
                           "G203-p48 sets 10/h as the MINIMUM for motors to 30 kW; a lower "
                           "rate buys a smaller wet well by breaching the cycle rule")
        if has("GRD_M", "FLOOD_LV"):
            g = pd.to_numeric(gdf.GRD_M, errors="coerce")
            f_ = pd.to_numeric(gdf.FLOOD_LV, errors="coerce")
            bad = g.notna() & f_.notna() & (g < f_ + 0.30 - 1e-6)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations sit less than 0.30 m above the "
                           "1:50-yr flood level (G203-p38 sec 7.2). The floor, the "
                           "transformers and the generator all sit above it - this is a "
                           "siting failure, and the fix is the site, not the level")

    if spec.name == "rising_mains":
        # G203-p50: 2.5 m/s maximum on a PRESSURE main, against H7's 3.0 m/s gravity limit.
        # A9 conflated the two and carried 3.0 for both (build brief P9).
        if has("V_DUTY_MS"):
            v = pd.to_numeric(gdf.V_DUTY_MS, errors="coerce")
            bad = v.notna() & (v > 2.5 + 1e-9)
            if bad.any():
                out.append(f"{int(bad.sum()):,} rising mains "
                           "over 2.5 m/s. That is G203-p50; the 3.0 m/s in H7 is the GRAVITY "
                           "maximum from p27 and the two were conflated once already")
            bad = v.notna() & (v < 0.75 - 1e-9)
            if bad.any():
                out.append(f"{int(bad.sum()):,} rising mains below 0.75 m/s at duty "
                           "(G203-p50)")

    if spec.name == "packages":
        if has("ONE_TREE"):
            bad = pd.to_numeric(gdf.ONE_TREE, errors="coerce").fillna(0) != 1
            if bad.any():
                out.append(f"{int(bad.sum()):,} packages are not one connected tree with one "
                           "outlet. That is a failed package, not a note (P8)")
    return out


# --------------------------------------------------------------------------------------
# The graph. The primary object; every layer above is a view of it.
# --------------------------------------------------------------------------------------

@dataclass
class Node:
    uid: str
    x: float
    y: float
    kind: str = "chamber"
    tier: str = "lateral"
    grd_m: float = float("nan")
    inv_m: float = float("nan")
    src: str = "draft"
    confidence: str = "drafted"
    stage: str = ""
    ref: str = ""
    package: str = ""
    phase: int = 0
    system: str = "central"
    attrs: Dict = field(default_factory=dict)

    @property
    def xy(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Edge:
    uid: str
    us: str
    ds: str
    kind: str = "gravity"
    tier: str = "lateral"
    vertices: Tuple[Tuple[float, float], ...] = ()   # INTERMEDIATE vertices only.
    # The endpoints are deliberately absent. An edge's geometry is built as
    # [node[us].xy] + vertices + [node[ds].xy], so it is structurally impossible for a
    # published reach to stop 1.000 m short of the chamber it joins - which is what
    # 91.4 % of W10's stitch links did.
    src: str = "draft"
    confidence: str = "drafted"
    stage: str = ""
    attrs: Dict = field(default_factory=dict)


class NodeIndex:
    """The ONLY place a node identity is minted.

    Identity is spatial, at criteria.MH_SNAP_M (3.0 m): "closer than the clearance => ONE
    structure, merge". A caller asking for a node within 3 m of an existing one gets the
    EXISTING uid back, so two stages that independently decide a chamber belongs at a street
    corner produce one chamber, not two 0.4 m apart with a 0.4 m pipe between them.

    A uniform grid at the merge radius does the lookup - no scipy, and O(1) per insert. The
    ids are deterministic for a given insertion order, and the stage order is fixed, so a
    re-run reproduces them. Meaning is NOT in the uid: it is in NODE_REF, which can be
    recomputed after a pass-2 relabel without orphaning a single reference.
    """

    def __init__(self, merge_m: float = NODE_MERGE_M):
        self.merge_m = merge_m
        self._cells: Dict[Tuple[int, int], List[str]] = {}
        self.nodes: Dict[str, Node] = {}
        self._n = 0

    def _cell(self, x, y):
        return (int(math.floor(x / self.merge_m)), int(math.floor(y / self.merge_m)))

    def find(self, x: float, y: float) -> Optional[str]:
        cx, cy = self._cell(x, y)
        best, bestd = None, self.merge_m
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for uid in self._cells.get((i, j), ()):
                    nd = self.nodes[uid]
                    d = math.hypot(nd.x - x, nd.y - y)
                    if d <= bestd:
                        best, bestd = uid, d
        return best

    def get_or_create(self, x: float, y: float, **kw) -> str:
        uid = self.find(x, y)
        if uid is not None:
            nd = self.nodes[uid]
            for k, v in kw.items():                     # fill blanks, never overwrite
                if hasattr(nd, k) and (getattr(nd, k) in ("", 0, None)
                                       or (isinstance(getattr(nd, k), float)
                                           and math.isnan(getattr(nd, k)))):
                    setattr(nd, k, v)
            return uid
        self._n += 1
        uid = NODE_UID_FMT.format(self._n)
        self.nodes[uid] = Node(uid=uid, x=float(x), y=float(y), **kw)
        self._cells.setdefault(self._cell(x, y), []).append(uid)
        return uid


class Network:
    """Nodes, edges, and the invariants held WHILE building rather than checked afterwards.

    Three things are impossible here, not merely audited:

      H15, no loops        add_edge refuses a second outgoing edge from a node. A forest is
                           a graph where every node has at most one parent, so enforcing
                           that at insertion makes cycles unreachable.
      dangling reference   an edge whose us or ds is not a registered node raises.
      geometry drift       to_edges_gdf builds the LineString from node coordinates.

    What is still checked afterwards, because it is global rather than local: how many
    components exist, which SYSTEM each belongs to, and how many outfalls each has.
    """

    def __init__(self, index: Optional[NodeIndex] = None):
        self.index = index or NodeIndex()
        self.edges: Dict[str, Edge] = {}
        self.out_edge: Dict[str, str] = {}     # node uid -> its ONE outgoing edge
        self.in_edges: Dict[str, List[str]] = {}
        self._n = 0

    # ---- nodes
    @property
    def nodes(self) -> Dict[str, Node]:
        return self.index.nodes

    def node(self, x: float, y: float, **kw) -> str:
        return self.index.get_or_create(x, y, **kw)

    # ---- edges
    def add_edge(self, us: str, ds: str, *, vertices=(), stage: str = "", **kw) -> str:
        for role, uid in (("us", us), ("ds", ds)):
            if uid not in self.nodes:
                raise ContractError(
                    f"edge {role}={uid!r} is not a registered node. Every edge references "
                    "two nodes minted by NodeIndex - an id invented at the call site is how "
                    "a layer stops being a network.")
        if us == ds:
            raise ContractError(f"self-loop at {us}")
        if us in self.out_edge:
            prev = self.edges[self.out_edge[us]]
            raise ContractError(
                f"node {us} already drains to {prev.ds} via {prev.uid}; refusing a second "
                f"outgoing edge to {ds}. H15: the network is a FOREST. One parent per node "
                "makes a loop unreachable - if this reach is real, the upstream chamber is "
                "in the wrong place or the two runs must meet at a junction downstream.")
        self._n += 1
        uid = EDGE_UID_FMT.format(self._n)
        self.edges[uid] = Edge(uid=uid, us=us, ds=ds, vertices=tuple(
            (float(a), float(b)) for a, b in vertices), stage=stage, **kw)
        self.out_edge[us] = uid
        self.in_edges.setdefault(ds, []).append(uid)
        return uid

    # ---- traversal
    def downstream_path(self, uid: str, limit: int = 100000) -> List[str]:
        """Node uids from here to the outfall. Also the cycle detector: a forest cannot
        revisit, so a repeat means the invariant was bypassed."""
        seen, out, cur = set(), [], uid
        while cur is not None and len(out) < limit:
            if cur in seen:
                raise ContractError(f"cycle through {cur} - H15 breached. Nothing in this "
                                    "module can create one, so it came from an edit to "
                                    "out_edge outside add_edge()")
            seen.add(cur)
            out.append(cur)
            e = self.out_edge.get(cur)
            cur = self.edges[e].ds if e else None
        return out

    def outfalls(self) -> List[str]:
        return [u for u in self.nodes if u not in self.out_edge]

    def components(self) -> Dict[str, str]:
        """node uid -> the outfall it reaches. One dict, and every question about
        connectedness answered from it."""
        root: Dict[str, str] = {}
        for u in self.nodes:
            if u in root:
                continue
            path = self.downstream_path(u)
            r = path[-1]
            for v in path:
                root[v] = r
        return root

    def check(self) -> List[str]:
        """Global invariants. Local ones already raised at insertion.

        The component count is REPORTED, not condemned. audit.h15 demands exactly one
        component, but philosophy sec 8a contemplates a central network plus satellites plus
        on-site systems - see OPEN-1. What matters and is enforced here is the property H15
        was reaching for: every component terminates at exactly one outfall, and that
        outfall is a real terminal kind.
        """
        bad: List[str] = []
        roots = self.components()
        comps = pd.Series(list(roots.values())).value_counts() if roots else pd.Series(dtype=int)
        n_comp = len(comps)
        if n_comp > 1:
            systems = sorted({self.nodes[u].system for u in roots})
            bad.append(
                f"{n_comp} components (W10 published 7,919). Largest {comps.iloc[0]:,} "
                f"nodes, smallest {comps.iloc[-1]:,}; systems present: {systems}. "
                "H15 permits more than one component (OPEN-1 closed): a satellite works "
                "is legal. What it requires is that EACH component ends at exactly one "
                "outfall - so this is a finding only for components that drain nowhere, "
                "and those are listed below.")
        orphan = [u for u, nd in self.nodes.items()
                  if u not in self.out_edge and not self.in_edges.get(u)]
        if orphan:
            bad.append(f"{len(orphan):,} isolated nodes with no reach at all: "
                       f"{orphan[:5]}")
        for u in self.outfalls():
            k = self.nodes[u].kind
            if k not in ("outfall", "station", "tie"):
                bad.append(f"node {u} has no downstream edge but is kind={k!r}. A terminal "
                           "node is an outfall, a station or a tie to the existing network "
                           "- nothing else terminates")
        return bad

    # ---- views. Geometry is generated here and nowhere else.
    def edge_geom(self, uid: str) -> LineString:
        e = self.edges[uid]
        us, ds = self.nodes[e.us], self.nodes[e.ds]
        return LineString([us.xy] + list(e.vertices) + [ds.xy])

    def to_nodes_gdf(self, extra: Optional[pd.DataFrame] = None) -> gpd.GeoDataFrame:
        rows = []
        for u, nd in self.nodes.items():
            r = dict(NODE_UID=u, NODE_REF=nd.ref or node_ref(nd, u),
                     NODE_KIND=nd.kind, X=nd.x, Y=nd.y,
                     GRD_M=nd.grd_m, INV_M=nd.inv_m,
                     DEPTH_M=nd.grd_m - nd.inv_m,
                     TIER=nd.tier,
                     DS_NODE=self.edges[self.out_edge[u]].ds if u in self.out_edge else "",
                     N_IN=len(self.in_edges.get(u, ())),
                     N_OUT=1 if u in self.out_edge else 0,
                     SRC=nd.src, CONFIDENCE=nd.confidence, STAGE=nd.stage,
                     PACKAGE=nd.package, PHASE=nd.phase)
            r.update(nd.attrs)
            rows.append(r)
        g = gpd.GeoDataFrame(rows, geometry=[Point(self.nodes[r["NODE_UID"]].xy)
                                             for r in rows], crs=CRS_EPSG)
        if extra is not None:
            g = g.merge(extra, on="NODE_UID", how="left")
        return g

    def to_edges_gdf(self, kind: str = "gravity",
                     extra: Optional[pd.DataFrame] = None) -> gpd.GeoDataFrame:
        rows, geoms = [], []
        for uid, e in self.edges.items():
            if e.kind != kind:
                continue
            geom = self.edge_geom(uid)
            r = dict(EDGE_UID=uid, US_NODE=e.us, DS_NODE=e.ds, TIER=e.tier,
                     LEN_M=geom.length, SRC=e.src, CONFIDENCE=e.confidence, STAGE=e.stage,
                     PACKAGE=self.nodes[e.us].package, PHASE=self.nodes[e.us].phase)
            r.update(e.attrs)
            rows.append(r)
            geoms.append(geom)
        g = gpd.GeoDataFrame(rows, geometry=geoms, crs=CRS_EPSG)
        if extra is not None:
            g = g.merge(extra, on="EDGE_UID", how="left")
        return g

    # ---- the round trip. Invariant 2: reloading the published layers reproduces the graph.
    @staticmethod
    def assert_round_trip(nodes_gdf, edges_gdf, tol: float = ENDPOINT_TOL_M) -> None:
        """Re-read the PUBLISHED layers and prove they still are the graph.

        This is the check W10 could not have written. It asserts four things: every
        US_NODE/DS_NODE resolves; every edge endpoint sits on its own node's coordinate
        within `tol`; no edge is multipart; and no node has two outgoing edges. Run it after
        writing, on what was written - not on what is in memory.

        `tol` is HALF the auditor's 0.01 m clustering radius, per endpoint, because two
        reaches arriving at one chamber each spend their own allowance and the errors add.
        """
        problems = []
        if "NODE_UID" not in nodes_gdf.columns:
            raise ContractError("node layer has no NODE_UID - nothing to resolve against")
        pos = {r.NODE_UID: (r.geometry.x, r.geometry.y)
               for r in nodes_gdf.itertuples()}
        seen_out = {}
        for r in edges_gdf.itertuples():
            for role in ("US_NODE", "DS_NODE"):
                uid = getattr(r, role)
                if uid not in pos:
                    problems.append(f"{r.EDGE_UID}.{role} = {uid!r} resolves to no node")
            if r.US_NODE in seen_out:
                problems.append(f"node {r.US_NODE} drains through both "
                                f"{seen_out[r.US_NODE]} and {r.EDGE_UID} - not a forest")
            seen_out[r.US_NODE] = r.EDGE_UID
            g = r.geometry
            if g is None or g.is_empty:
                problems.append(f"{r.EDGE_UID} has no geometry")
                continue
            if g.geom_type != "LineString":
                problems.append(
                    f"{r.EDGE_UID} is {g.geom_type}, not a single LineString. "
                    "audit.Ctx.graph() would read only its first part and silently drop the "
                    "rest - the component count would then describe a network nobody built")
                continue
            c = list(g.coords)
            for role, pt in (("US_NODE", c[0]), ("DS_NODE", c[-1])):
                uid = getattr(r, role)
                if uid in pos:
                    d = math.hypot(pos[uid][0] - pt[0], pos[uid][1] - pt[1])
                    if d > tol:
                        problems.append(
                            f"{r.EDGE_UID} {role} endpoint is {d:.4f} m from node {uid} "
                            f"(tolerance {tol} m). W10's stitch links stopped at exactly "
                            "1.000 m and the layer shipped in 7,919 pieces. Geometry is "
                            "BUILT from node coordinates; this gap means something bypassed "
                            "to_edges_gdf")
            if len(problems) > 40:
                problems.append("... stopping at 40")
                break
        if problems:
            raise ContractError("PUBLISHED LAYERS ARE NOT THE GRAPH (invariant 2):\n  "
                                + "\n  ".join(problems))

    @staticmethod
    def assert_degrees(nodes_gdf, edges_gdf) -> None:
        """N_OUT / N_IN on the node layer against the out- and in-degree of the pipe layer.

        Two independently computed numbers agreeing is the only cheap defence against the
        W10 defect where the node layer and the pipe layer came out of different solves and
        disagreed by up to 10.39 m of depth. Neither layer alone can reveal it.
        """
        if "N_OUT" not in nodes_gdf.columns and "N_IN" not in nodes_gdf.columns:
            raise ContractError("node layer publishes neither N_OUT nor N_IN - the pipe "
                                "layer's own topology has nothing to be checked against")
        out_deg = edges_gdf.groupby("US_NODE").size()
        in_deg = edges_gdf.groupby("DS_NODE").size()
        bad = []
        for col, deg in (("N_OUT", out_deg), ("N_IN", in_deg)):
            if col not in nodes_gdf.columns:
                continue
            claim = pd.to_numeric(nodes_gdf.set_index("NODE_UID")[col], errors="coerce")
            real = deg.reindex(claim.index).fillna(0)
            diff = (claim.fillna(-1) - real).abs()
            n = int((diff > 0).sum())
            if n:
                worst = diff.idxmax()
                bad.append(f"{col} disagrees with the reach layer on {n:,} nodes; worst at "
                           f"{worst} (node says {claim[worst]:g}, reaches say {real[worst]:g})")
        if bad:
            raise ContractError(
                "NODE AND REACH LAYERS DISAGREE ON TOPOLOGY:\n  " + "\n  ".join(bad)
                + "\nThey were written from the same graph or they were not. In W10 they "
                "were not, and the depth difference reached 10.39 m.")


def node_ref(nd: Node, uid: str, branch: str = "", seq: Optional[int] = None) -> str:
    """NAMA's own ID grammar: 5A-2-TM-MH185, 5A-2-SM.2-MH391.

    Objective 3 - NAMA runs this for fifty years and it must read like their own network.
    This label is for humans and drawings. NOTHING references it, so a pass-2 retier can
    rewrite every label without touching a single US_NODE. NWS's real numbering system is
    issued to the successful consultant (scope-p25) and is not in our hands.
    """
    tok = TIER_TOKEN.get(nd.tier, "L") + (f".{branch}" if branch else "")
    pkg = nd.package or "P0"
    n = seq if seq is not None else int(uid[1:])
    return f"{pkg}-{tok}-MH{n:04d}"


# --------------------------------------------------------------------------------------
# How a stage declares what it read and what it wrote
# --------------------------------------------------------------------------------------

@dataclass
class Funnel:
    """N0 -> N1 -> N2, with a named reason and retrievable ids for every loss.

    P2: "any metric with a filter chain prints its own funnel so a second filter cannot be
    applied to an already-filtered set without it being visible." Invariant 1: every load
    unit is assigned to exactly one chamber, OR LISTED BY NAME. W10's 1,233 m3/d vanished
    because a radius test returned nothing and nobody counted the difference.
    """
    name: str
    n0: int
    steps: List[Dict] = field(default_factory=list)

    def drop(self, reason: str, ids: Optional[Sequence] = None, n: Optional[int] = None,
             qty: float = 0.0) -> "Funnel":
        if ids is None and n is None:
            raise ContractError(f"funnel '{self.name}': a drop must carry ids or a count. "
                                "An uncounted drop is a silent one.")
        cnt = len(ids) if ids is not None else int(n)
        self.steps.append(dict(reason=reason, n=cnt, qty=qty,
                               ids=[str(i) for i in (ids or [])][:200],
                               ids_truncated=bool(ids is not None and len(ids) > 200)))
        return self

    @property
    def n(self) -> int:
        return self.n0 - sum(s["n"] for s in self.steps)

    def line(self) -> str:
        seq = [self.n0]
        for s in self.steps:
            seq.append(seq[-1] - s["n"])
        return f"{self.name}: " + " -> ".join(f"{v:,}" for v in seq)

    def close(self, n_final: int) -> None:
        if n_final != self.n:
            raise ContractError(
                f"funnel '{self.name}' does not close: {self.line()} predicts {self.n:,} "
                f"but the stage produced {n_final:,}. The {abs(self.n - n_final):,} "
                "difference is a silent drop - name it with .drop(reason, ids).")


@dataclass
class StageRecord:
    stage: str
    order: int
    reads: List[Dict] = field(default_factory=list)
    writes: List[Dict] = field(default_factory=list)
    funnels: List[Funnel] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    no_change_reason: str = ""
    t0: float = field(default_factory=time.time)
    seconds: float = 0.0

    def read(self, name: str, path: str = "", n: Optional[int] = None) -> "StageRecord":
        self.reads.append(dict(name=name, path=str(path), n=n))
        return self

    def wrote(self, name: str, path: str = "", n: Optional[int] = None) -> "StageRecord":
        self.writes.append(dict(name=name, path=str(path), n=n))
        return self

    def funnel(self, name: str, n0: int) -> Funnel:
        f = Funnel(name, n0)
        self.funnels.append(f)
        return f

    def metric(self, name: str, value: float, unit: str = "") -> None:
        self.metrics[name] = value if not unit else f"{value} {unit}"

    def note(self, text: str) -> None:
        self.notes.append(text)

    def did_nothing(self, reason: str) -> None:
        """Declare a deliberate no-op. Invariant 10 exists because RoadTreatment ran with
        `units=None, sampler=None` and three of its steps silently did nothing - 34
        collapsed roundabout rings ended up intersecting a registered plot. A stage may do
        nothing; it may not do nothing QUIETLY."""
        self.no_change_reason = reason

    def to_dict(self) -> Dict:
        return dict(stage=self.stage, order=self.order, seconds=round(self.seconds, 2),
                    reads=self.reads, writes=self.writes, metrics=self.metrics,
                    notes=self.notes, no_change_reason=self.no_change_reason,
                    funnels=[dict(name=f.name, n0=f.n0, n=f.n, line=f.line(),
                                  steps=f.steps) for f in self.funnels])


class Manifest:
    """The run's record. One JSON, appended by every stage, read by the report and the audit.

    Answers, mechanically: what did stage 5 read? did stage 3 actually change anything?
    where did the 131 missing plots go? which number came from which function?
    """
    path = os.path.join(W11A_ROOT, "run", "manifest.json")
    records: List[StageRecord] = []

    @classmethod
    @contextmanager
    def stage(cls, name: str, order: int, *, path: Optional[str] = None):
        rec = StageRecord(name, order)
        try:
            yield rec
        finally:
            rec.seconds = time.time() - rec.t0
            if not rec.writes and not rec.no_change_reason:
                raise ContractError(
                    f"stage '{name}' wrote nothing and did not say why. Call "
                    "rec.wrote(layer, path, n) or rec.did_nothing(reason) - invariant 10, "
                    "no stage silently no-ops.")
            cls.records.append(rec)
            cls.save(path or cls.path)

    @classmethod
    def save(cls, path: Optional[str] = None) -> str:
        p = path or cls.path
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(dict(contract=CONTRACT_VERSION,
                           written=time.strftime("%Y-%m-%d %H:%M:%S"),
                           stages=[r.to_dict() for r in cls.records]), fh, indent=2)
        return p

    @classmethod
    def report(cls) -> str:
        out = []

        def _n(x):
            return "" if x["n"] is None else f"{x['n']:>10,}"
        for r in cls.records:
            out.append(f"{r.order}. {r.stage}  ({r.seconds:.1f} s)")
            for x in r.reads:
                out.append(f"     read  {x['name']:<16}{_n(x)}   {x['path']}")
            for x in r.writes:
                out.append(f"     wrote {x['name']:<16}{_n(x)}   {x['path']}")
            for f in r.funnels:
                out.append(f"     {f.line()}")
                for s in f.steps:
                    out.append(f"        -{s['n']:,}  {s['reason']}")
            if r.no_change_reason:
                out.append(f"     NO CHANGE: {r.no_change_reason}")
        return "\n".join(out)


# --------------------------------------------------------------------------------------
# One function per published number (P2)
# --------------------------------------------------------------------------------------

_METRICS: Dict[str, Dict] = {}


def published(name: str, unit: str = "", source: str = ""):
    """Register the ONE function allowed to produce a published quantity.

    Seven different lifting-station counts are in circulation from this project - 19, 21,
    25, 37, 140, 184, 239 - each computed ad hoc at the point of reporting. The count moved
    11 -> 21 -> 19 not because the design changed but because the definition did. A second
    definition of the same name raises here rather than in a client meeting.
    """
    def deco(fn):
        prior = _METRICS.get(name)
        if prior and prior["qualname"] != fn.__qualname__:
            raise ContractError(
                f"published metric '{name}' is already defined by {prior['qualname']}; "
                f"{fn.__qualname__} would be a second definition. Every published number "
                "comes from exactly one function (P2) - call the existing one.")
        _METRICS[name] = dict(fn=fn, unit=unit, source=source, qualname=fn.__qualname__)
        return fn
    return deco


def value(name: str, *a, **kw):
    if name not in _METRICS:
        known = ", ".join(sorted(_METRICS)) or "(none registered)"
        raise ContractError(f"no published function for '{name}'. Known: {known}")
    return _METRICS[name]["fn"](*a, **kw)


# --------------------------------------------------------------------------------------
# Publishing
# --------------------------------------------------------------------------------------

def gpkg_path(root: str, name: str = "W11a.gpkg") -> str:
    return os.path.join(root, "shp", name)


def assert_audited_path(path: str, layer_name: Optional[str] = None) -> str:
    """Refuse to hand the auditor anything a DBF would mangle.

    `mirror_shapefile()` writes a README beside the .shp saying it is not the deliverable.
    A raise is better than a note nobody opens: `GRAD_BY` becomes `GRADIENT_B` on the
    way into a shapefile, audit G2 then reports 'missing GRAD_BY', and the design that
    fails its own audit was correct in memory the whole time.
    """
    ext = os.path.splitext(str(path))[1].lower()
    if ext == ".gpkg":
        return path
    if ext in (".shp", ".dbf"):
        specs = [LAYERS[layer_name]] if layer_name in LAYERS else list(LAYERS.values())
        lost = sorted({f.name for s in specs for f in s.fields if not f.shp_safe})
        raise ContractError(
            f"{path} is a shapefile and cannot be the audited artefact. The DBF truncates "
            f"field names at {SHP_FIELD_MAXLEN} characters, so {lost} arrive renamed and "
            "audit G2 fails a design that was correct in memory. Point the auditor at the "
            "GeoPackage; the shapefile is a CAD mirror.")
    raise ContractError(f"{path}: the audited artefact is a GeoPackage (.gpkg), not {ext!r}")


def publish(gdf, layer_name: str, root: str, *, stage: str = "",
            gpkg: str = "W11a.gpkg", allow_empty: bool = False) -> str:
    """Validate, then write to the GeoPackage. The ONLY sanctioned way a layer leaves a
    stage - validation is not optional and not skippable, because the failure it prevents
    (an unauditable layer) is invisible until the audit.

    An empty layer needs `allow_empty=True`. Publishing nothing is a legitimate answer for,
    say, a crossings schedule on a design with no crossings, and it is exactly what a stage
    that silently did nothing also produces. The flag makes the caller say which."""
    if len(gdf) == 0 and not allow_empty:
        raise ContractError(
            f"stage {stage or '?'} is publishing an EMPTY '{layer_name}'. If that is the "
            "right answer say so with allow_empty=True; otherwise the stage no-opped "
            "(invariant 10 - W10's RoadTreatment ran with units=None and three of its "
            "steps quietly did nothing).")
    validate(gdf, layer_name, stage=stage)
    p = gpkg_path(root, gpkg)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    gdf.to_file(p, layer=_spec(layer_name).name, driver="GPKG")
    return p


def mirror_shapefile(gdf, layer_name: str, root: str) -> str:
    """A CAD/QGIS convenience mirror. NOT the audited artefact, and it says so twice -
    in a README beside the file and in assert_audited_path(), which will not let this path
    reach the auditor at all."""
    spec = _spec(layer_name)
    lost = [f.name for f in spec.fields if not f.shp_safe and f.name in gdf.columns]
    p = os.path.join(root, "shp", f"W11a_{spec.name}.shp")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    gdf.to_file(p)
    if lost:
        with open(p.replace(".shp", ".README.txt"), "w", encoding="utf-8") as fh:
            fh.write("CAD MIRROR - NOT THE AUDITED LAYER.\n"
                     "The DBF truncates these field names to 10 characters: "
                     + ", ".join(lost) + "\n"
                     "The audited layer is the GeoPackage. Point run_audit.py at that.\n")
    return p


# --------------------------------------------------------------------------------------
# Will the auditor be able to run? Ask before publishing, not after.
# --------------------------------------------------------------------------------------

# Exactly what each audit.py check reads. Transcribed from the checks themselves, not from
# their docstrings - H7 for example insists on SLOPE_LAID and will not fall back to
# SLOPE_PCT, while H2/H5/H6 will.
AUDIT_NEEDS: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "H1":  {"external": ("roads",)},
    "H2":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID")},
    "H3":  {"reaches": ("DN", "US_DEPTH", "DS_DEPTH")},
    "H4":  {"reaches": ("DN", "US_DEPTH", "DS_DEPTH", "PAST_CAP")},
    "H5":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID")},
    "H6":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID")},
    "H7":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID")},
    "H8":  {"reaches": ("SIZED_BY",)},
    "H9":  {"reaches": ("TIER", "DN")},
    "H10": {"nodes": ("INLET_DEG", "INLET_FLAG")},
    "H11": {"reaches": ("INV_UP", "INV_DN")},
    "H12": {"reaches": ("DN", "LEN_M")},
    "H13": {"reaches": ("SLOPE_LAID",)},
    "H14": {"reaches": ("TIE_TYPE",), "external": ("existing",)},
    # H15 reads IS_OUTFALL from the NODES - an outfall is a property of a chamber - and needs
    # the declared node ids to attribute one to a component.
    "H15": {"reaches": ("US_NODE", "DS_NODE"), "nodes": ("IS_OUTFALL", "NODE_UID")},
    "H16": {"reaches": ("US_NODE", "DS_NODE")},
    "R1":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID")},
    "R2":  {"reaches": ("DN", "US_DEPTH", "DS_DEPTH")},
    "R3":  {"external": ("roads",)},
    # R4 needs the crossings REGISTER as well as the grid: a CROSS_ID with no OBSTACLE='wadi'
    # row behind it schedules nothing, so without the register every crossing reads unscheduled.
    "R4":  {"external": ("hazard", "crossings")},
    "G1":  {"reaches": ("SLOPE_LAID", "SLOPE_MIN")},
    "G2":  {"reaches": ("SIZED_BY", "GRAD_BY")},
    "G3":  {"reaches": ("US_NODE", "DS_NODE")},
}

# Checks the CONTRACT names on a field but audit.py does not yet implement. This is a
# to-do list with a deadline, not a wish: philosophy sec 8 requires one check per rule, and a
# field carrying provenance nothing verifies is decoration.
PLANNED_CHECKS: Dict[str, str] = {
    "G4": ("no stage silently no-ops - read Manifest.records and fail any stage with no "
           "writes and no did_nothing() reason (philosophy sec 8, invariant 10). STAGE on "
           "every row is what makes it checkable after the fact"),
    "G5": ("SRC and CONFIDENCE present on every published feature and never laundered - "
           "auto_block/auto_link may not be graded better than provisional (P6)"),
    "H4b": ("the cap exits are REAL and distance-bounded: 'recovers_500m' proved by cover "
            "recovering within 500 m of the breach, 'outfall_1000m' by an outfall within "
            "1,000 m. audit.h4 today accepts any non-empty flag (philosophy sec 5)"),
}


def audit_readiness(reaches=None, nodes=None, external: Sequence[str] = ()) -> pd.DataFrame:
    """Which of the 22 checks can run against these layers, and what is missing from each.

    Call it at the end of every stage that touches a published layer. A NOT_CHECKABLE in
    the audit is a FAILURE (philosophy sec 8), so discovering one here - while the writing code
    is still open - is the whole point. W10 shipped with 7 of 22 unanswerable.
    """
    have = {"reaches": set(reaches.columns) if reaches is not None else set(),
            "nodes": set(nodes.columns) if nodes is not None else set(),
            "external": set(external)}
    rows = []
    for cid, need in AUDIT_NEEDS.items():
        miss = []
        for layer, fields in need.items():
            for f in fields:
                if f not in have.get(layer, set()):
                    miss.append(f"{layer}.{f}")
        rows.append(dict(check=cid, can_run=not miss, missing=", ".join(miss)))
    return pd.DataFrame(rows)


def unchecked_fields() -> pd.DataFrame:
    """Every contract field whose named check does not exist in audit.REGISTRY yet.

    AUDIT_NEEDS above is a static transcription and cannot notice drift; this reads the
    auditor's own registry at call time. A field that names a check nobody has written is
    a field carrying a claim nothing verifies - which is how W10 ended up with thirteen
    hard constraints and a checklist naming none of them.
    """
    from w11a import audit                       # local: the auditor imports scipy/networkx
    have = {c.id for c in audit.REGISTRY}
    rows = []
    for lname, spec in LAYERS.items():
        for f in spec.fields:
            for cid in f.checks:
                if cid not in have:
                    rows.append(dict(layer=lname, field=f.name, check=cid,
                                     to_write=PLANNED_CHECKS.get(
                                         cid, "NOT PLANNED - either write the check or "
                                              "drop the claim from the field")))
    return pd.DataFrame(rows).drop_duplicates()


def field_table(layer_name: str) -> pd.DataFrame:
    """The spec as a table - for the report, the data dictionary and the drawing legend."""
    spec = _spec(layer_name)
    return pd.DataFrame([dict(field=f.name, type=f.dtype, units=f.units,
                              required=f.required, blank_ok=f.blank_ok, audit=f.audit,
                              allowed="|".join(f.allowed) if f.allowed else "",
                              why=f.why) for f in spec.fields])


# --------------------------------------------------------------------------------------
# SCHEDULES - the printed header declared BESIDE the stored field
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Schedule:
    """A deliverable table, with its printed headers bound to the fields behind them.

    They live here rather than in a reporting script for one reason: a header and the field
    it prints must not be editable apart. Rename `SLOPE_LAID` in the layer and this file
    stops importing; change a header here and the field it reads is one line away. A
    schedule built by a separate script drifts from the layer the first time either changes,
    and the drift is invisible because both halves still run.

    Columns are the scope-p25 lists via `W10/docs/research/DELIVERABLE_SPEC.md` D.2.
    """
    name: str
    layer: str
    key: str
    columns: Tuple[Tuple[str, str], ...]      # (printed header, stored field)
    required_by: str


SCHEDULES: Dict[str, Schedule] = {s.name: s for s in (
    Schedule(
        "chambers", "nodes", "NODE_REF",
        (("Manhole", "NODE_REF"), ("Easting", "X"), ("Northing", "Y"),
         ("Type", "NODE_KIND"), ("Cover level (m)", "GRD_M"),
         ("Invert level (m)", "INV_M"), ("Depth (m)", "DEPTH_M"),
         ("Cover to crown (m)", "COVER_M"), ("Chamber dia. (m)", "MH_DIA"),
         ("Inlets", "N_IN"), ("Max drop (m)", "DROP_M"), ("Drop type", "DROP_TYPE"),
         ("Vortex shaft", "VORTEX"), ("Tier", "TIER"), ("Package", "PACKAGE"),
         ("Phase", "PHASE"), ("Confidence", "CONFIDENCE")),
        "scope-p25 (the detailed-stage column list, produced here at concept precision)"),
    Schedule(
        "pipes", "reaches", "EDGE_UID",
        (("Pipe", "EDGE_UID"), ("US manhole", "US_NODE"), ("DS manhole", "DS_NODE"),
         ("US invert (m)", "INV_UP"), ("DS invert (m)", "INV_DN"),
         ("US depth (m)", "US_DEPTH"), ("DS depth (m)", "DS_DEPTH"),
         ("Length (m)", "LEN_M"), ("DN (mm)", "DN"), ("Material", "MATERIAL"),
         ("Laid gradient (%)", "SLOPE_LAID"), ("Minimum gradient (%)", "SLOPE_MIN"),
         ("Gradient set by", "GRAD_BY"), ("Diameter set by", "SIZED_BY"),
         ("Peak factor", "PF"), ("PF method", "PF_METH"),
         ("Qadf (m3/d)", "QADF_M3D"), ("Qpeak (L/s)", "QPK_LS"),
         ("Velocity (m/s)", "V_PK_MS"), ("d/D", "DOD_PK"),
         ("Self-cleansing by", "CLEAN_BY"), ("Tier", "TIER"), ("Package", "PACKAGE"),
         ("Confidence", "CONFIDENCE")),
        "scope-p25 verbatim column list; scope-p16 item 36"),
    Schedule(
        "stations", "stations", "NODE_REF",
        (("Station", "NODE_REF"), ("Chamber", "NODE_UID"), ("Type", "ST_TYPE"),
         ("Reason", "WHY"), ("Duty flow (L/s)", "Q_DUTY_LS"),
         ("Qadf (m3/d)", "Q_ADF_M3D"), ("Static lift (m)", "LIFT_M"),
         ("Wet well (m3)", "WELL_M3"), ("Starts per hour", "WW_STARTS"),
         ("Flood level (m)", "FLOOD_LV"), ("Land take (m2)", "LAND_M2"),
         ("Properties", "N_PROP"), ("Package", "PACKAGE"), ("Phase", "PHASE")),
        "scope-p15 item 19; G203-p40 Tab 17, p43 Tab 21, p48 sec 7.8"),
    Schedule(
        "rising_mains", "rising_mains", "EDGE_UID",
        (("Rising main", "EDGE_UID"), ("Station", "STATION"), ("DN (mm)", "DN"),
         ("Material", "MATERIAL"), ("Length (m)", "LEN_M"),
         ("Duty flow (L/s)", "Q_DUTY_LS"), ("Velocity at duty (m/s)", "V_DUTY_MS"),
         ("Static head (m)", "STAT_HD_M"), ("Total head (m)", "TOT_HD_M"),
         ("Air valves", "N_AIRV"), ("Washouts", "N_WASH"),
         ("Septicity treatment", "SEPTIC_FL"), ("Package", "PACKAGE")),
        "scope-p13; G203-pp50-55 sec 8"),
    Schedule(
        "connections", "connections", "PLOT_ID",
        (("Plot", "PLOT_ID"), ("Connection", "CONN_ID"), ("Chamber", "OUT_NODE"),
         ("Served by", "SYSTEM"), ("Status", "WHY"), ("Properties", "N_PROP"),
         ("Qadf (m3/d)", "Q_ADF_M3D"), ("Length (m)", "LEN_M"),
         ("Gradient (%)", "SLOPE_LAID"), ("Cover (m)", "COVER_M"),
         ("Package", "PACKAGE")),
        "scope-p12 ('List of Customer / house connection Excel list')"),
    Schedule(
        "packages", "packages", "PACKAGE",
        (("Package", "PACKAGE"), ("Phase", "PHASE"), ("Length (km)", "LEN_KM"),
         ("Plots", "N_PLOT"), ("Outlet chamber", "OUTLET"),
         ("Discharges into", "DS_PKG"), ("Commissioning order", "COMM_SEQ"),
         ("Independent", "INDEP"), ("One tree, one outlet", "ONE_TREE")),
        "scope-p16 item 39; G201-p21 Tab 2"),
)}


def schedule_frame(gdf, name: str, *, stage: str = "") -> pd.DataFrame:
    """Validate the layer, then render the schedule with its printed headers.

    Validating first is the point. A schedule is what the client reads, and printing one
    from an unvalidated layer is how a number that failed the contract reaches a document
    that nobody re-checks. Note that a schedule may demand fields the LayerSpec marks
    `required=False` - MH_DIA, PACKAGE, PHASE. That split is deliberate: the layer is
    publishable at stage 4, the schedule is printable only after stage 6.
    """
    if name not in SCHEDULES:
        raise ContractError(f"no schedule '{name}'. Known: {', '.join(sorted(SCHEDULES))}")
    sch = SCHEDULES[name]
    validate(gdf, sch.layer, stage=stage)
    missing = [f for _h, f in sch.columns if f not in gdf.columns]
    if missing:
        raise ContractError(
            f"schedule '{name}' cannot be printed: the layer has no {missing}. "
            f"Required by {sch.required_by}. These are the columns the client's own scope "
            "asks for, so an absent one is a deliverable gap, not a formatting choice.")
    return pd.DataFrame({h: gdf[f].values for h, f in sch.columns})


# --------------------------------------------------------------------------------------
# SewerGEMS - canonical field -> Bentley field, so the model cannot drift from the layer
# --------------------------------------------------------------------------------------

# `W8/py/sewnet/export_gems.py` was written to the Bentley ModelBuilder schema and is reused
# unchanged. This map is the CONTRACT half of it: the layer names on the left, Bentley's on
# the right, so a rename in the layer breaks the export loudly instead of producing a model
# that imports with orphan conduits.
#
# THE TRAP, and why LABEL is the uid and never the ref: START_ND and STOP_ND must resolve
# against MANHOLES.LABEL. Label the manholes with NODE_REF (which is regenerated on every
# retier) while the conduits carry NODE_UID and every conduit imports unconnected - the
# model runs, reports nothing, and is wrong. Identity in the model is the uid; NODE_REF is
# for drawings.
SEWERGEMS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "MANHOLES": (("NODE_UID", "LABEL"), ("GRD_M", "GRD_EL"), ("INV_M", "INV_EL"),
                 ("MH_DIA", "MH_DIA")),
    "CONDUITS": (("EDGE_UID", "LABEL"), ("US_NODE", "START_ND"), ("DS_NODE", "STOP_ND"),
                 ("DN", "DIA_MM"), ("MATERIAL", "MATERIAL"), ("INV_UP", "INV_UP"),
                 ("INV_DN", "INV_DN"), ("LEN_M", "LEN_M")),
    "OUTFALL":  (("NODE_UID", "LABEL"), ("GRD_M", "GRD_EL"), ("INV_M", "INV_EL")),
}
SEWERGEMS_LAYER = {"MANHOLES": "nodes", "CONDUITS": "reaches", "OUTFALL": "nodes"}
# MANNING_N is added by the exporter from criteria.MANNING_N_EXPORT (0.013, review HYD-3) -
# it is a model parameter, not a design value on the pipe, and does not live on the layer.


def gems_frame(gdf, table: str, *, stage: str = "") -> gpd.GeoDataFrame:
    """Validate the source layer, then rename to Bentley's schema. Elevations, never depths;
    single-part polylines digitised upstream to downstream (G201-p140)."""
    if table not in SEWERGEMS:
        raise ContractError(f"no SewerGEMS table '{table}'. Known: "
                            f"{', '.join(sorted(SEWERGEMS))}")
    validate(gdf, SEWERGEMS_LAYER[table], stage=stage)
    pairs = SEWERGEMS[table]
    missing = [src for src, _dst in pairs if src not in gdf.columns]
    if missing:
        raise ContractError(f"SewerGEMS {table} needs {missing}, which the layer does not "
                            "carry. The model is a referee for our hydraulics (philosophy "
                            "sec 7); a referee given half the levels referees nothing.")
    out = gdf[[src for src, _ in pairs] + (["geometry"] if "geometry" in gdf.columns else [])]
    return out.rename(columns=dict(pairs))


# --------------------------------------------------------------------------------------
# Self-test. `python -m w11a.contract` - proves the invariants bite.
# --------------------------------------------------------------------------------------

def _self_test() -> None:
    from shapely.geometry import MultiLineString

    # ---- the depth claim, proved against the criteria file rather than asserted
    for dn in (160, 200, 250, 315, 400):
        assert abs(min_invert_depth(dn) - (1.30 + dn / 1000.0 + 0.10)) < 1e-12
        gap = min_invert_depth(dn) - C.invert_depth_min(dn)
        assert abs(gap - 0.05) < 1e-12, (dn, gap)
        # and the resulting cover is exactly the H3 minimum, by construction
        assert abs(cover(dn, min_invert_depth(dn)) - C.MIN_COVER_CROWN) < 1e-12
        # while the criteria helper lands 50 mm short of it - a blocking H3 failure
        assert cover(dn, C.invert_depth_min(dn)) < C.MIN_COVER_CROWN - 1e-9

    net = Network()
    a = net.node(100.0, 100.0, kind="head", tier="lateral", grd_m=330.0, inv_m=328.5,
                 stage="T")
    b = net.node(200.0, 100.0, kind="chamber", tier="lateral", grd_m=329.5, inv_m=328.0,
                 stage="T")
    c = net.node(300.0, 100.0, kind="outfall", tier="lateral", grd_m=329.0, inv_m=327.5,
                 stage="T")
    assert net.node(101.0, 100.5) == a, "3 m merge must return the existing node"
    net.add_edge(a, b, stage="T")
    net.add_edge(b, c, stage="T")

    try:
        net.add_edge(a, c)
        raise AssertionError("H15 not enforced")
    except ContractError as e:
        assert "FOREST" in str(e)

    try:
        net.add_edge(a, "N9999999")
        raise AssertionError("dangling reference not caught")
    except ContractError as e:
        assert "not a registered node" in str(e)

    assert net.check() == [], net.check()

    ng = net.to_nodes_gdf()
    eg = net.to_edges_gdf()
    Network.assert_round_trip(ng, eg)
    Network.assert_degrees(ng, eg)
    assert abs(eg.LEN_M.sum() - 200.0) < 1e-6

    # a layer missing the field the auditor needs must not get out of the stage
    try:
        validate(eg, "reaches", stage="T")
        raise AssertionError("validate let an unauditable layer through")
    except ContractError as e:
        assert "GRAD_BY" in str(e) and "NOT_CHECKABLE" in str(e)

    # the underscore tier that audit.py H9 would skip in silence
    bad = eg.copy()
    bad["TIER"] = "sub_main"
    try:
        validate(bad, "reaches")
        raise AssertionError("underscore tier accepted")
    except ContractError as e:
        assert "SILENTLY" in str(e)

    # a name that means two things is refused outright
    bad = eg.copy()
    bad["SLOPE_PCT"] = 0.5
    try:
        validate(bad, "reaches")
        raise AssertionError("banned field accepted")
    except ContractError as e:
        assert "BANNED FIELD NAMES" in str(e)

    # LEN_M must keep measuring the line it sits on
    bad = eg.copy()
    bad.loc[bad.index[0], "LEN_M"] = float(bad.LEN_M.iloc[0]) + 0.2
    try:
        validate(bad, "reaches")
        raise AssertionError("LEN_M drift accepted")
    except ContractError as e:
        assert "disagrees with its own geometry" in str(e)

    # multipart geometry is refused, not tolerated - audit.Ctx.graph() drops the extra parts
    bad = eg.copy()
    bad.loc[bad.index[0], "geometry"] = MultiLineString(
        [[(0.0, 0.0), (1.0, 0.0)], [(5.0, 0.0), (6.0, 0.0)]])
    try:
        validate(bad, "reaches")
        raise AssertionError("multipart geometry accepted")
    except ContractError as e:
        assert "MULTIPART" in str(e)
    try:
        Network.assert_round_trip(ng, bad)
        raise AssertionError("round trip accepted a multipart reach")
    except ContractError as e:
        assert "single LineString" in str(e)

    # the tolerance is per-endpoint and half the auditor's clustering radius
    bad = eg.copy()
    coords = list(bad.geometry.iloc[0].coords)
    coords[0] = (coords[0][0] + 0.008, coords[0][1])       # inside 0.01, outside 0.005
    bad.loc[bad.index[0], "geometry"] = LineString(coords)
    try:
        Network.assert_round_trip(ng, bad)
        raise AssertionError("an 8 mm endpoint gap slipped through")
    except ContractError as e:
        assert "NOT THE GRAPH" in str(e)

    # G203-p22 Tab 6 by application, not p23 Tab 7 by product
    assert material_conflict("lateral", 315, "PVC-U") is None
    assert material_conflict("main", 250, "PVC-U") is None
    assert "250" in (material_conflict("sub main", 315, "PVC-U") or "")

    # a shapefile is never the audited artefact
    try:
        assert_audited_path("W11a/shp/W11a_reaches.shp", "reaches")
        raise AssertionError("a .shp was accepted as the audited artefact")
    except ContractError as e:
        assert "GRAD_BY" in str(e)
    assert assert_audited_path("W11a/shp/W11a.gpkg").endswith(".gpkg")

    # funnels must close
    f = Funnel("plot loads", 64071)
    f.drop("no corridor within 60 m", ids=list(range(131)))
    assert f.n == 63940
    try:
        f.close(63900)
        raise AssertionError("funnel closure not enforced")
    except ContractError as e:
        assert "silent drop" in str(e)
    f.close(63940)

    # one function per published number
    @published("pipe_km", "km")
    def _pipe_km(g):
        return float(g.LEN_M.sum()) / 1000.0
    assert abs(value("pipe_km", eg) - 0.2) < 1e-9
    try:
        @published("pipe_km", "km")
        def _pipe_km_2(g):
            return 0.0
        raise AssertionError("duplicate metric definition allowed")
    except ContractError as e:
        assert "exactly one function" in str(e)

    # a schedule cannot be printed from a layer that does not validate
    try:
        schedule_frame(ng, "chambers")
        raise AssertionError("schedule printed from an incomplete layer")
    except ContractError:
        pass
    # every schedule column names a field its own layer declares
    for s in SCHEDULES.values():
        names = set(LAYERS[s.layer].names)
        unknown = [f for _h, f in s.columns if f not in names]
        assert not unknown, f"schedule {s.name} prints undeclared {unknown}"
    # and the SewerGEMS map likewise
    for t, pairs in SEWERGEMS.items():
        names = set(LAYERS[SEWERGEMS_LAYER[t]].names)
        unknown = [src for src, _ in pairs if src not in names]
        assert not unknown, f"SewerGEMS {t} reads undeclared {unknown}"

    r = audit_readiness(reaches=eg, nodes=ng)
    assert not r.can_run.all(), "a bare graph should not be audit-ready"

    u = unchecked_fields()
    assert set(u.check) == {"G4", "G5", "H4b"}, sorted(set(u.check))

    print("contract self-test OK -", len(net.nodes), "nodes,", len(net.edges), "edges,",
          f"{int(r.can_run.sum())}/{len(r)} audit checks ready on a bare graph,",
          f"{len(LAYERS)} layers, {sum(len(s.fields) for s in LAYERS.values())} fields,",
          f"{len(SCHEDULES)} schedules, {len(EXCLUDED)} refusals on record")
    print()
    print(r.to_string(index=False))
    print()
    print("checks this contract names but audit.py does not yet implement:")
    print(u.to_string(index=False))
    print()
    print(open_items_report())


if __name__ == "__main__":
    _self_test()
