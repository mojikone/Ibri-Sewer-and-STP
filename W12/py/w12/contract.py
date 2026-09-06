"""w12.contract - the shared data contract. Written before any design stage runs.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
or W11a.

THE ONE IDEA: THE GRAPH IS THE DESIGN. EVERY LAYER IS A VIEW OF IT.

W10's fatal defect was not a wrong number. It was that the thing actually issued was 7,919
disconnected components at 0.01 m tolerance, largest holding 5.9 %. The flow tree that sized
those pipes was real and lived entirely inside a sizing script; the shapefile inherited only
its geometry. 91.4 % of the stitch links stopped at exactly 1.000 m from what they joined.
Nobody could have known, because there was nothing on the layer to know it from.

So `Network` - nodes with identity, edges that reference node identity - is the primary
object and geometry is DERIVED: an edge's LineString is built as
`[node[US].xy] + vertices + [node[DS].xy]`, so a published reach physically cannot end
anywhere but on its own chambers. Four W10 failure modes stop being possible by construction:

    disconnected layer   an edge endpoint IS the node coordinate; there is no gap to leave
    loops                a node may own at most ONE outgoing edge - enforced in add_edge
    orphan flow          every edge references two registered nodes; a dangling id raises
    silent load drops    a load unit is attached to a node uid, or it is named in a Funnel

WHAT THIS FILE IS FOR. Six things every stage agrees on and nothing else is negotiable:
    1. LAYERS      the published schemas, field by field, with the rule each field feeds
    2. Network     node identity, edge identity, and the invariants held while building
    3. Manifest    how a stage declares what it read, what it wrote and what it dropped
    4. validate()  the gate every stage calls before it writes and after it reads
    5. SCHEDULES   the printed header declared BESIDE the stored field
    6. EXCLUDED    what was proposed and refused - the only defence against schema regrowth

----------------------------------------------------------------------------------------
THE SIX FIXES BAKED IN HERE. Each was a real defect and each cost hours.

1  ONE WALL/BEDDING ALLOWANCE. `min_invert_depth()` and `cover()` below are thin wrappers
   over `criteria.invert_depth_min()` and `criteria.cover()`; there is no second constant
   anywhere in W12. W11a carried WALL_ALLOW = 0.05 in criteria and AUDITOR_OD_ALLOW_M in
   the contract, and when they were 0.05 and 0.10 the auditor demanded 50 mm more cover than
   the design laid at EVERY diameter and a BLOCKING check failed on EVERY reach. The
   self-test proves the round trip is exact rather than asserting it.

2  DEPTH OF FLOW IS DIAMETER-DEPENDENT, from `criteria.dod_limit()` - 0.65 to DN350, 0.50
   above (G203-p27 Table 10, re-read from the PDF 2026-09-03: "Pipe Diameter up to 350 mm
   0.65 / Pipe Diameter > 350 mm 0.50"). One function, so no caller can reach for the wrong
   constant.

3  THE DIAMETER SERIES REACHES THE SIZES THE GUIDELINE ITSELF TABULATES. G203-p32 Table 13
   and p35 Table 15 print corridor widths for 1400-1700, 1800 and 2000-2400; p30 Table 12
   prints chamber spacing for "More than 1 400". Stopping at DN1200 caused 168 d/D failures
   on the trunk. `DN` on the reach layer is range-checked against `criteria.DN_SERIES`
   itself, so the layer and the sizing function cannot disagree about what sizes exist.

4  NO FIELD NAME OVER 10 CHARACTERS, ENFORCED AT IMPORT. Not a note, not a README - the
   module refuses to load. The ESRI DBF truncates at 10, and a truncated name is a field the
   auditor cannot find, which philosophy sec 8 makes a blocking failure. W11a justified
   publishing to GeoPackage on the grounds that `GRAD_BY` was 11 characters; it is 7, no
   field in W11a's contract exceeds 10, and the guard it built computed an empty list. Here
   the rule is real and mechanical: every published layer round-trips through a shapefile
   without losing a single name.

5  IS_OUTFALL IS DERIVED FROM THE GRAPH, NEVER ASSERTED. `to_nodes_gdf()` writes
   `IS_OUTFALL = 1` exactly where a node has no outgoing edge, and `validate()` REJECTS a
   node layer where IS_OUTFALL disagrees with DS_NODE. An outfall is a topological fact, and
   a design that has to be told where its outfalls are does not know where its flow goes.

6  A CROSSINGS REGISTER, AND A CROSS_ID THAT MEANS NOTHING WITHOUT A ROW BEHIND IT.
   `assert_crossings_resolve()` requires every CROSS_ID on a reach or corridor to resolve to
   a `crossings` row whose OBSTACLE matches what the reach claims to cross. W10 shipped 47
   unscheduled crossings; W11a could publish an id with no row and nothing noticed.

   Plus the seventh, which is not on the engineer's list but belongs with them:
   EVERY PUBLISHED LENGTH AGREES WITH ITS OWN GEOMETRY. `LEN_M` is checked against the line
   it sits on to LEN_TOL_M on every LineString layer. Every published length reads the
   FIELD, not the geometry; a merge, a clip or a hand edit parts them silently and then the
   schedule and the drawing describe different pipes.

----------------------------------------------------------------------------------------
NEW IN W12: THE TERRAIN-FIRST BLOCK.

W11a built its layout on ROAD CONNECTIVITY and used the terrain only to CHECK the answer.
42.5 % of its length - 737.7 km - then drained UPHILL, and it wanted 2,449 vortex drop
shafts where NAMA's built network has 37. W12 derives flow direction from the ground first,
so the against-the-grade quantities philosophy sec 4 demands are first-class fields with a
report function behind them: `GND_FALL`, `AGN_GRADE`, `RISE_M` on every reach, and
`terrain_report()`, which prints the share of length draining against the ground, the
cumulative climb, the worst single rise and the drop-structure count beside the as-built 37.

The `streams` and `basins` layers are here for the terrain stage. Their REQUIRED core is
deliberately tiny - an id, a length, provenance - because a contract that demands fields a
stage has not invented yet blocks the stage instead of protecting it. Add fields HERE when
they exist, never at the point of writing.

----------------------------------------------------------------------------------------
NEW IN W12, SECOND PASS: THE CONCEPT-STAGE FIELDS (engineer, 2026-09-05/06).

Philosophy sec 9 sets the concept-stage rules, and five of them need a place on the layer or
they are opinions. Each field below exists because a rule would otherwise be unprovable:

    NAME TOWN SUBNET      rule 8. One grammar - I-S03-SM-M012 - built by concept_name(),
                          checked against NAME_RE, and cross-checked against the row's own
                          TOWN / SUBNET / TIER columns. Blank is legal on the layer and
                          illegal at publication (assert_named), because naming runs AFTER
                          connectivity: an element outside a town takes the letter of the
                          first town DOWNSTREAM of it.
    DROP_WHY              rule 1. The laid slope is a clamp and the surplus fall becomes a
                          DROP, so every drop carries the reason it exists. A drop with no
                          reason cannot be told from a levelling error.
    JOIN_MAIN JOIN_OFF_M  rule 2. A subnetwork joins the main pipe at the LOWEST POINT WHERE
    JOIN_WHY              IT MEETS IT. Where it cannot, the distance from the true low point
                          is RECORDED. W11b had 42 components discharging with more than half
                          their catchment below the outlet - 389.5 km - and nothing on the
                          layer said so.
    CAN_CONN CONN_WHY     rule 5. One gravity check per plot, and the failures named with
    CONN_NEED             their size. W11b published DRAIN_SHALLOW and recorded CAN_DRAIN as
                          "cannot run", and a check that cannot run is a FAILURE.
    N_SUBNET CATCH_KM     rule 6. A station's POSITION IS CHOSEN, NOT TRIGGERED - so the
    DS_TYPE               layer carries what it captures, and its main says whether it lifts
                          to the nearest point where gravity resumes or all the way to the
                          works.

And six proposed field names were REFUSED as synonyms of fields already here - HEAD_M, Q_LS,
STOR_M3, DIA_MM, V_MS, US_PUMP. They are in BANNED_FIELDS, so a stage that reaches for one is
told the existing name instead of quietly adding a second column for the same quantity. Two
names for one quantity is this project's most expensive recurring defect.

WHY validate() RAISES INSTEAD OF WARNING. A missing field is not a slightly incomplete
layer - it is an unauditable one, and philosophy sec 8 makes any check that cannot run
blocking. Thirteen of W10's 22 checks were unanswerable for exactly this reason. Failing at
the writing stage costs a minute; failing at the audit costs a rebuild.

Sources: `_BRAIN/08_DESIGN_PHILOSOPHY.md` (H1-H16, P1-P6, sec 5 cap-and-veto, sec 8 audit),
`_BRAIN/02_DESIGN_CRITERIA.md` and the guideline PDFs via `w12.criteria` (every number).
NO DESIGN NUMBER IS DEFINED HERE. Values live in `w12.criteria`; this file names fields,
fixes vocabulary and holds shape. Where a threshold appears below it is a STRUCTURAL
tolerance - a geometry snap, an id width, a range guard - and it says so.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

# Imported hard, not in a try/except. A contract that degrades quietly when a dependency is
# missing is how W10's road treatment ran with `units=None, sampler=None` and three of its
# steps became no-ops nobody noticed.
import geopandas as gpd
from shapely.geometry import LineString, Point

from .criteria import DEFAULT as C
from . import hydra                              # noqa: F401  re-exported, never reimplemented

CONTRACT_VERSION = "W12-contract-1.0"

_HERE = os.path.dirname(os.path.abspath(__file__))       # .../W12/py/w12
W12_ROOT = os.path.dirname(os.path.dirname(_HERE))      # .../W12
REPO_ROOT = os.path.dirname(W12_ROOT)                   # .../Hydraulic/Claude
GPKG_NAME = "W12.gpkg"


class ContractError(Exception):
    """Raised by validate(), Network, Manifest and the publish helpers. Never caught inside
    a stage - the whole point is that it stops the write."""


# ======================================================================================
# Structural constants. NOT design values - those are in w12.criteria and are cited there.
# ======================================================================================

CRS_EPSG = 32640                 # project rule; every layer, no exceptions

GRAPH_SNAP_M = 0.01              # the radius at which an auditor clusters endpoints into
                                 # graph vertices. Never used as OUR tolerance - see below.

ENDPOINT_TOL_M = 0.005           # HALF the clustering radius, PER ENDPOINT. Two reaches
                                 # meeting at one chamber, each allowed the full 0.01, can
                                 # sit 0.02 m apart - twice the snap - and the component
                                 # count then reports a disconnected piece on a design whose
                                 # every endpoint was "within tolerance". The tolerance has
                                 # to be per-end and half, or it does not compose.

LEN_TOL_M = 0.05                 # LEN_M against the geometry it claims to measure.

NODE_MERGE_M = C.MH_SNAP_M       # 3.0 m. Node identity uses the same radius as the chamber
                                 # clearance, so the graph cannot hold two chambers a
                                 # contractor would build as one.

SHP_FIELD_MAXLEN = 10            # ESRI DBF limit. ENFORCED AT IMPORT over every LayerSpec.

DEPTH_SANITY_M = 40.0            # a RANGE GUARD on depth fields, not a rule. The rule is
                                 # criteria.MAX_COVER (12 m) with philosophy sec 5's two
                                 # exits, and it is carried by PAST_CAP / CAP_EXIT. This
                                 # number exists only so a units error or a sign flip raises
                                 # instead of publishing a 400 m chamber.

NODE_UID_FMT = "N{:07d}"         # dumb, stable, sortable. Meaning lives in NODE_REF.
EDGE_UID_FMT = "E{:07d}"
CROSS_UID_FMT = "X{:06d}"

VARY_MIN_ROWS = 30               # a STRUCTURAL threshold, not a design value. Below this
                                 # many rows, one repeated value in a column that should vary
                                 # is a small sample; at or above it, it is the fabrication
                                 # inheritance row 22 names - ANGLE_DEG = 90 on all 3,290
                                 # crossings, called a declaration, measured minimum 0.00 deg.
                                 # The number bounds a CLAIM about evidence, not a pipe.


# ======================================================================================
# Depth. Thin wrappers over the criteria - THE fix, and the reason they are wrappers.
# ======================================================================================

def min_invert_depth(dn: int) -> float:
    """Minimum depth of invert below ground, m. Delegates to `criteria.invert_depth_min()`.

    A WRAPPER, NOT A COPY, and deliberately so. W11a defined this expression here with a
    0.10 allowance while the criteria file defined it with 0.05, and a design laid to one
    sat 50 mm shallow against the other at every diameter. There is exactly one allowance in
    W12 (`criteria.WALL_ALLOW`) and exactly one function that adds it."""
    return C.invert_depth_min(dn)


def cover(dn: int, invert_depth_m: float) -> float:
    """Cover to crown, m, on the reach's OWN outside diameter. Delegates to
    `criteria.cover()`. THE single definition every published depth statistic goes through -
    W10 used a hardcoded 0.30 m regardless of diameter and shipped 45.92 km below minimum."""
    return C.cover(dn, invert_depth_m)


# ======================================================================================
# Vocabulary. Every enum is pinned by the philosophy, the guideline or the as-built.
# ======================================================================================

# Philosophy sec 4 governing set: "rider, lateral, main, sub main, trunk main". The SPACED
# forms are canonical; underscore forms are rejected by validate() because a checker that
# does `floor.get(tier)` skips an unrecognised tier SILENTLY, and a silent skip reads as a
# pass. This is the same spelling `criteria.materials_allowed()` keys on.
TIERS: Tuple[str, ...] = ("rider", "lateral", "main", "sub main", "trunk main")
TIER_TOKEN = {"rider": "R", "lateral": "L", "main": "M",
              "sub main": "SM", "trunk main": "TM"}        # NAMA's own ID grammar
TIER_ALIASES = {"sub_main": "sub main", "submain": "sub main", "sub-main": "sub main",
                "trunk_main": "trunk main", "trunkmain": "trunk main",
                "trunk-main": "trunk main"}

# What set the DIAMETER. "depth" and "cover" are PROHIBITED answers - G203-p29 ("Sewers
# shall not be oversized to facilitate flatter slopes") and Ten States sec 33.43
# independently. This set is exactly what `hydra.size_pipe()` can return, so a value here
# that the sizing function cannot produce is unreachable by construction.
SIZED_BY: Tuple[str, ...] = ("minimum", "dod", "capacity", "velocity", "infeasible")

# What set the LAID gradient. Depth IS admissible here - the philosophy prohibits it as an
# answer for a diameter, not for a gradient.
GRAD_BY: Tuple[str, ...] = (
    "table11",     # G203-p29 Table 11 floor governed
    "tractive",    # the tractive route governed - EXPOSED TO tau (GAP-9)
    "ground",      # laid to the ground fall, both minima already satisfied
    "cover_min",   # steepened or flattened to hold 1.30 m cover (G203-p33)
    "cover_max",   # flattened to stay under the 12 m cap (philosophy sec 5)
    "uniform",     # carried from the upstream reach (P1) - the preferred answer
    "vmax",        # flattened to hold v <= 3.0 m/s (G203-p27)
    "tie",         # fixed by an existing invert - the design yields (H14)
)

# Which self-cleansing route the LAID reach satisfies. Exactly `hydra.clean_route()`'s
# return set. G203-p27 offers the two as ALTERNATIVES; philosophy H5 requires the route
# recorded, because the tractive share is the share resting on an assumed tau.
CLEAN_BY: Tuple[str, ...] = ("velocity", "tractive", "neither")

# H14: tie in soffit to soffit, never invert to invert. "invert" exists in this enum only so
# a violation can be RECORDED rather than hidden.
TIE_TYPE: Tuple[str, ...] = ("none", "soffit", "invert")

# Philosophy sec 5: everything past the 12 m cap is flagged with WHICH exit allowed it, and
# both exits are bounded by distance AND by depth.
CAP_EXIT: Tuple[str, ...] = ("", "recovers_500m", "outfall_1000m")

DROP_TYPE: Tuple[str, ...] = ("none", "backdrop", "vortex")   # G203-p30: >0.60 m / >2.0 m

NODE_KIND: Tuple[str, ...] = (
    "head",        # philosophy sec 4: "a head starts at the gate"
    "chamber",     # a spacing chamber (G203-p30 Table 12) or a bend chamber
    "junction",    # two or more incoming reaches
    "drop",        # carries an external backdrop or a vortex shaft
    "station",     # lifting station - a package seam as much as a depth device
    "outfall",     # works inlet or an existing structure; the only node with no DS_NODE
    "tie",         # tie-in to the existing built network (H14)
)

# Philosophy P6: corridor provenance is carried to the end and never laundered.
SRC: Tuple[str, ...] = ("dwg_road", "dwg_block", "dwg_link", "main_pipe", "existing",
                        "terrain", "manual")
CONFIDENCE: Tuple[str, ...] = ("surveyed", "drafted", "derived", "provisional")

# A platted reserve on bare desert is a legal corridor at a saturation horizon and is NEVER
# an observed street. It can never be graded better than provisional, and the contract
# enforces it so a later stage cannot quietly promote hundreds of km of desert to "drafted".
SRC_CONFIDENCE_CEILING = {"dwg_block": "provisional", "dwg_link": "provisional",
                          "terrain": "derived"}
_CONF_RANK = {c: i for i, c in enumerate(CONFIDENCE)}       # surveyed 0 ... provisional 3

EDGE_KIND: Tuple[str, ...] = ("gravity", "rising", "crossing")

# G201-p71-72. "held" is not a formula - it is the honest token for a catchment below
# criteria.PF_HOLD_PROPERTIES (100), where G201 PRESCRIBES NO FORMULA. W10 published PF with
# no record of which method produced it, so no peak factor could be reproduced from its row.
PF_METH: Tuple[str, ...] = ("merrimack", "peltier", "held")

# G203-p22 Table 6 (by application), p23 Table 7 (by product), p35 Table 14 (trunk). The
# permitted set for a given tier and diameter is criteria.materials_allowed(); this enum is
# only the vocabulary.
MATERIAL: Tuple[str, ...] = ("PVC-U", "HDPE", "GRP", "GRP/PVC", "lined RCC", "DI", "SS")

CONSTR: Tuple[str, ...] = ("open_trench", "trenchless")

OBSTACLE: Tuple[str, ...] = ("dual", "wadi", "road", "utility", "falaj", "rail")

XING_METHOD: Tuple[str, ...] = ("open_cut", "thrust_bore", "microtunnel",
                                "existing_underpass", "existing_culvert")

ST_TYPE: Tuple[str, ...] = ("Type 1", "Type 2", "Type 3")   # G203-p40: <=100/100-300/>300

STATION_WHY: Tuple[str, ...] = ("cap", "veto", "economics", "commissioning")

SYSTEM: Tuple[str, ...] = ("central", "satellite", "onsite", "unserved")


# ======================================================================================
# CONCEPT-STAGE VOCABULARY (engineer 2026-09-05/06; philosophy sec 9)
# ======================================================================================

# WHY A DROP EXISTS. Concept rule 1: the laid slope is a clamp, and where the ground outruns
# the pipe the surplus fall is taken as a DROP at a manhole - "EVERY DROP CARRIES THE REASON
# IT EXISTS". A drop with no reason is indistinguishable from a levelling error, and the drop
# count is the diagnostic for a tree that is not following the ground (philosophy sec 4).
#
# The empty string is the value where there is no drop; it is in the enum so a blank is a
# legal VALUE rather than a null the validator has to be told to forgive.
DROP_WHY: Tuple[str, ...] = (
    "",                  # DROP_M = 0: nothing to explain
    "velocity_cap",      # the ground falls faster than 3.0 m/s allows (G203-p27) - the pipe
                         # is laid at the slope that meets the cap and the surplus is dropped
    "tier_step",         # a smaller pipe arrives above a larger one; the soffits are matched
                         # and the invert difference becomes a drop (G203-p30)
    "cover_recovery",    # the run has gone deep and the drop hands the depth back rather
                         # than carrying it (philosophy sec 5 - never used to dodge a station)
    "obstruction",       # a crossing, a utility or an existing structure fixes the level
)

# WHERE A RISING MAIN DISCHARGES. Concept rule 6: "a rising main LIFTS TO THE NEAREST POINT
# WHERE GRAVITY RESUMES, NOT TO THE WORKS". The two values are the two legal answers, and the
# split between them is the number that says whether the rule was obeyed: the built network's
# one 10.0 km main straight to the works is explained by there being no gravity network to
# receive it in 2006, not by it being right (philosophy sec 6).
DS_TYPE: Tuple[str, ...] = ("manhole", "stp")

# ======================================================================================
# NAMING (engineer 2026-09-05/06). ONE grammar, one formatter, one regex.
# ======================================================================================
#
#     I-S03            subnetwork 3 in Ibri
#     I-S03-SM-M012    manhole 12, sub main tier
#     I-S03-C012       conduit, named for its UPSTREAM manhole (no tier token)
#     I-PMP02          pump - NOT inside a subnetwork, because a station is a SEAM
#     I-P02            force main, numbered with its pump
#
# The town letter comes from the settlement name with the Arabic definite article dropped.
# ARTICLES ARE A PROJECT DECISION, not a guideline: "Al Aqar" and "Ad Dariz" would otherwise
# both be "A" and every town in the wilayat would collide on one letter.
TOWN_ARTICLES: Tuple[str, ...] = ("al ", "ad ", "ash ", "as ", "at ", "an ", "ar ", "az ",
                                  "el ", "ath ", "adh ")

# Element tokens. TIER_TOKEN above supplies TM / SM / L for the tiered elements.
ELEMENT_TOKEN = {"manhole": "M", "conduit": "C", "pump": "PMP", "main": "P"}

# The grammar as a regex, so a NAME can be CHECKED and not merely stored. Zero-padding is a
# MINIMUM width, not a fixed one: S03 and S147 are both legal, M012 and M1234 both legal, and
# a network that outgrows its padding must not be renamed into an unparseable state.
# PMP is matched before P so "I-PMP02" is a pump and never a force main numbered "MP02".
NAME_RE = re.compile(
    r"^(?P<town>[A-Z]{1,3})-"
    r"(?:"
    r"(?P<sub>S\d{2,})(?:-(?:(?P<tier>TM|SM|L)-M(?P<mh>\d{3,}))|-C(?P<cd>\d{3,}))?"
    r"|PMP(?P<pmp>\d{2,})"
    r"|P(?P<fm>\d{2,})"
    r")$")

SUBNET_RE = re.compile(r"^S\d{2,}$")
TOWN_RE = re.compile(r"^[A-Z]{1,3}$")


def town_letter(name: str, n: int = 1) -> str:
    """The first `n` letters of a settlement name with the article dropped, upper-cased.

    "Al Aqar" -> "A" / "AQ" / "AQA".  Spaces and punctuation are skipped so a two-letter
    extension of "Al Aqar" is "AQ" and not "A " - a field value with a space in it is a
    value that will come back from a DBF differently from a GeoPackage."""
    s = str(name).strip().lower()
    for art in TOWN_ARTICLES:
        if s.startswith(art):
            s = s[len(art):]
            break
    letters = [c for c in s if c.isalnum()]
    if not letters:
        raise ContractError(f"settlement name {name!r} has no letters to take a code from")
    return "".join(letters[:max(1, int(n))]).upper()


def town_letters(names: Sequence[str]) -> Dict[str, str]:
    """Settlement name -> its unique code. THE ONE resolver, so two stages cannot disagree
    about which town is 'A'.

    THE CLASH RULE IS THE ENGINEER'S, AND IT IS DELIBERATELY SYMMETRIC (2026-09-05/06): on a
    clash BOTH towns extend to two letters, then three, until unique - "the town with more
    served plots is not favoured". Favouring the larger town would make the code of the small
    one depend on a LOAD, so a plot count moving would rename half a network.

    Two settlements whose de-articled names are genuinely identical cannot be separated by
    letters at all; they take a numeric suffix and the pair is reported in the code itself
    rather than being silently merged into one town."""
    out: Dict[str, str] = {}
    width: Dict[str, int] = {str(n): 1 for n in names}
    for _round in range(24):                      # bounded: no name is 24 letters of clash
        out = {n: town_letter(n, w) for n, w in width.items()}
        clashes: Dict[str, List[str]] = {}
        for n, code in out.items():
            clashes.setdefault(code, []).append(n)
        stuck = False
        for code, group in clashes.items():
            if len(group) < 2:
                continue
            # extend BOTH (all) members of the clash - never just the smaller one
            grew = False
            for n in group:
                if width[n] < len([c for c in str(n) if c.isalnum()]):
                    width[n] += 1
                    grew = True
            if not grew:
                stuck = True
        if all(len(g) < 2 for g in clashes.values()):
            return out
        if stuck:
            break
    # identical de-articled names: separate them by index, visibly
    seen: Dict[str, int] = {}
    final: Dict[str, str] = {}
    for n in sorted(out):
        code = out[n]
        seen[code] = seen.get(code, 0) + 1
        final[n] = code if seen[code] == 1 else f"{code}{seen[code]}"
    return final


def concept_name(town: str, kind: str, *, subnet: Optional[str] = None,
                 tier: Optional[str] = None, seq: Optional[int] = None) -> str:
    """THE ONE formatter for a concept-stage name. `node_ref()` below builds NAMA's own
    5A-2-SM.2-MH391 grammar for the drawings; this builds ours.

    Both exist because they answer different questions - NODE_REF makes our network read like
    the one NAMA operate, NAME makes it navigable in this design's own terms - and NEITHER is
    referenced by anything, so both can be regenerated after a retier without orphaning a
    single US_NODE. Identity is NODE_UID and stays NODE_UID.

        concept_name("I", "subnet",  subnet="S03")                     -> I-S03
        concept_name("I", "manhole", subnet="S03", tier="sub main", seq=12)
                                                                       -> I-S03-SM-M012
        concept_name("I", "conduit", subnet="S03", seq=12)             -> I-S03-C012
        concept_name("I", "pump", seq=2)                               -> I-PMP02
        concept_name("I", "main", seq=2)                               -> I-P02
    """
    t = str(town).strip().upper()
    if not TOWN_RE.match(t):
        raise ContractError(
            f"town code {town!r} is not 1-3 upper-case letters. Codes come from "
            "town_letters(), which drops the article and extends BOTH towns on a clash.")
    k = str(kind).strip().lower()
    sn = (str(subnet).strip().upper() if subnet else "")
    if k in ("manhole", "conduit", "subnet") and not SUBNET_RE.match(sn):
        raise ContractError(
            f"{k} {seq!r} in town {t}: subnet {subnet!r} is not S## - a gravity element is "
            "always inside a subnetwork. A station and its force main are the exception, "
            "because a station is a SEAM between subnetworks, not a member of one.")
    if k == "subnet":
        return f"{t}-{sn}"
    if seq is None:
        raise ContractError(f"a {k} name needs a sequence number")
    n = int(seq)
    if k == "manhole":
        tok = TIER_TOKEN.get(str(tier).strip().lower() if tier else "")
        if tok is None:
            raise ContractError(
                f"manhole {n} in {t}-{sn}: tier {tier!r} is not one of {list(TIERS)}. The "
                "tier token is IN the name, so an unknown tier cannot be defaulted - it "
                "would put a lateral's label on a trunk chamber.")
        return f"{t}-{sn}-{tok}-M{n:03d}"
    if k == "conduit":
        return f"{t}-{sn}-C{n:03d}"
    if k in ("pump", "main"):
        return f"{t}-{ELEMENT_TOKEN[k]}{n:02d}"
    raise ContractError(f"unknown element kind {kind!r}. Known: "
                        f"{', '.join(sorted(ELEMENT_TOKEN) + ['subnet'])}")


def parse_name(name: str) -> Optional[Dict[str, str]]:
    """The inverse: the parts of a NAME, or None if it does not fit the grammar.

    Used by validate() to check that a row's NAME agrees with its own TOWN, SUBNET and TIER
    columns. A name that says one thing and a column that says another is a layer nobody can
    filter, and the drawing and the schedule would disagree about which subnetwork a chamber
    is in."""
    m = NAME_RE.match(str(name).strip())
    if not m:
        return None
    d = {k: (v or "") for k, v in m.groupdict().items()}
    if d["pmp"]:
        d["kind"] = "pump"
    elif d["fm"]:
        d["kind"] = "main"
    elif d["mh"]:
        d["kind"] = "manhole"
    elif d["cd"]:
        d["kind"] = "conduit"
    else:
        d["kind"] = "subnet"
    return d


# ======================================================================================
# BANNED_FIELDS - names that mean two things, or that a checker will not find
# ======================================================================================

BANNED_FIELDS: Dict[str, str] = {
    "SLOPE_PCT": ("meant 'the minimum' in one W10 file and 'the laid gradient' in another - "
                  "one name, two meanings, and the layer could not say which. Use "
                  "SLOPE_LAID and SLOPE_MIN, BOTH, on every layer with a gradient"),
    "SLOPE": "ambiguous units and ambiguous meaning. Use SLOPE_LAID / SLOPE_MIN, in percent",
    "DN_MM": "the sizing function and every check read DN",
    "US_MH": "topology is US_NODE / DS_NODE (H16). US_MH predates the graph",
    "DS_MH": "topology is US_NODE / DS_NODE (H16)",
    "MH_ID": "identity is NODE_UID (referenced) and NODE_REF (printed); MH_ID conflates them",
    "DEPTH": "to invert or to crown? Use DEPTH_M (to invert) and COVER_M (to crown)",
    "COVER": "same ambiguity. Use COVER_M, computed by cover() and nowhere else",
    "MAT": "the schedules and the SewerGEMS map read MATERIAL",
    "GRADIENT_B": ("the DBF truncation of an 11-character gradient field. If this name is "
                   "on a layer the layer came back from a shapefile round trip that lost a "
                   "name - which W12's 10-character rule exists to make impossible"),
    "ELEV": "ground or invert? Use GRD_M and INV_M",
    "UPHILL": "the measured quantity is AGN_GRADE (0/1) with RISE_M beside it",

    # --- the concept-stage synonyms. Each of these is a SECOND NAME for a quantity the
    # --- contract already carries, and two names for one quantity is the defect that has
    # --- cost this project the most: a wall allowance of 0.05 and 0.10 failed a blocking
    # --- cover check on every reach, and seven station counts reached circulation because
    # --- each was computed where it was printed. Banning the synonym is how the stage that
    # --- reaches for it is told the existing name instead of quietly adding a column.
    "HEAD_M": ("a station's head is LIFT_M (static lift, stations layer); a rising main's "
               "are STAT_HD_M and TOT_HD_M. HEAD_M would be a third name for one of the "
               "three and no row could say which"),
    "Q_LS": ("flow at what? Use Q_DUTY_LS on a station and its rising main (pump duty, from "
             "the wet-well cycle), QPK_LS on a gravity reach (peak design flow), Q_PK_LS on "
             "a node. A bare Q_LS is the ambiguity SLOPE_PCT already cost us once"),
    "STOR_M3": "wet-well live volume is WELL_M3, and it is tied to Q_DUTY_LS and WW_STARTS "
               "by G203-p48 sec 7.8 (V = 0.25 Q T). A second volume field would not be",
    "DIA_MM": "the sizing function and every check read DN, on the reach AND the rising main",
    "V_MS": "velocity at what flow? A rising main carries V_DUTY_MS (at duty) and V_MIN_MS "
            "(at the design MINIMUM flow, where G203-p50 holds the 0.75 m/s floor). The "
            "difference between them is the whole reason a main silts in year one",
    "US_PUMP": "the station upstream of a rising main is US_NODE (the graph) and STATION "
               "(the station whose duty sized it). Both already exist and both are checked",
    "JOIN_OFFS_M": ("11 characters - the DBF truncates it and no check would find it "
                    "afterwards. The field is JOIN_OFF_M"),
    "MOTOR_KW": "motor selection is SWITCHED OFF at concept - criteria.CONCEPT_OFF["
                "'motor_selection']. It comes back when the station positions are fixed",
    "LCC_OMR": "life-cycle costing is SWITCHED OFF at concept - criteria.CONCEPT_OFF["
               "'life_cycle_cost']. It comes back when the priced BoQs arrive",
}


# ======================================================================================
# EXCLUDED - the register against schema regrowth over ten stages
# ======================================================================================

@dataclass(frozen=True)
class Excluded:
    """What was proposed for the contract, refused, and what would let it in. Without this
    the schema grows a field per stage and nothing can ever be removed, because nobody
    remembers whether it was load-bearing."""
    name: str
    why_refused: str
    would_admit: str


EXCLUDED: Tuple[Excluded, ...] = (
    Excluded("SLOPE_PCT",
             "one name for two different gradients. See BANNED_FIELDS.",
             "never - the pair SLOPE_LAID / SLOPE_MIN says both things unambiguously"),
    Excluded("a per-stage schema",
             "inventing a schema at the point of writing is how W10's pipe layer grew nine "
             "fields with no provenance and no check behind any of them.",
             "add a LayerSpec HERE, with a `why` naming the rule the field feeds"),
    Excluded("SIZED_BY = 'depth' / 'cover'",
             "G203-p29 prohibits oversizing to lay flatter, and Ten States sec 33.43 says the "
             "same independently. A diameter chosen to buy a gradient is the prohibited "
             "move, and an enum that can express it invites it.",
             "never. The resolution for a depth problem is a station, a drop, a re-route or "
             "not serving the plot - the four in philosophy sec 3"),
    Excluded("a second wall/bedding allowance in this file",
             "TWO CONSTANTS FOR ONE QUANTITY. W11a had 0.05 in criteria and 0.10 here; the "
             "auditor demanded 50 mm more cover than the design laid at every diameter and "
             "a blocking check failed on every reach.",
             "never. min_invert_depth() and cover() are wrappers over the criteria and the "
             "self-test proves the round trip is exact"),
    Excluded("IS_OUTFALL as an input",
             "an outfall is a node with no outgoing edge. A design that has to be TOLD where "
             "its outfalls are does not know where its flow goes, and an asserted flag "
             "cannot disagree with the graph loudly enough to be caught.",
             "never. It is derived in to_nodes_gdf() and cross-checked in validate()"),
    Excluded("a bare CROSS_ID with no register",
             "an id with no row behind it schedules nothing. W10 shipped 47 unscheduled "
             "crossings and every one of them had somewhere to put an id.",
             "never. assert_crossings_resolve() is called before publication"),
    Excluded("field names over 10 characters",
             "the DBF truncates at 10 and a truncated name is a field the auditor cannot "
             "find, which philosophy sec 8 makes blocking.",
             "never. _assert_shp_safe() runs at import and the module refuses to load"),
    Excluded("a 'confidence' grade improved by a later stage",
             "P6: provenance is carried to the end and never laundered. A cadastral reserve "
             "on bare desert does not become an observed street because a pipe was laid on "
             "it.",
             "surveyed data. Change SRC as well, and record where the survey came from"),
    Excluded("MULTI-part geometry on a published layer",
             "a graph builder that reads geoms[0] of a multipart reach drops the rest, so "
             "the component count describes a network only half read - and the check that "
             "exists to catch silent corruption is the one corrupted.",
             "never. Explode in the stage that reads it and account for the extra parts in "
             "a Funnel; a part silently discarded is a reach nobody designed"),
    Excluded("HEAD_M / Q_LS / STOR_M3 / DIA_MM / V_MS / US_PUMP on the pump layers",
             "all six were proposed for the concept-stage station and rising-main schema on "
             "2026-09-06 and all six are SECOND NAMES for fields the contract already "
             "carries: LIFT_M, Q_DUTY_LS, WELL_M3, DN, V_DUTY_MS, US_NODE/STATION. The "
             "brief that proposed them was writing a fresh list, not reading the existing "
             "one. Two names for one quantity is this project's most expensive recurring "
             "defect - it cost a blocking cover failure on every reach once and seven "
             "circulating station counts another time.",
             "never as synonyms. A genuinely NEW quantity gets a new name and a `why` - "
             "which is exactly how N_SUBNET, CATCH_KM and DS_TYPE got in on the same day"),
    Excluded("motor size and life-cycle cost on the stations layer",
             "SWITCHED OFF at concept (philosophy sec 9, criteria.CONCEPT_OFF). A station's "
             "POSITION is the concept question; its motor is not, and neither changes the "
             "other. Publishing an empty or guessed kW would read as a designed one.",
             "criteria.CONCEPT_STAGE = False, once the positions are fixed and the priced "
             "BoQs arrive. The field names are BANNED meanwhile so the column cannot appear "
             "quietly as an undeclared extra"),
    Excluded("a per-plot house connection design at concept",
             "concept rule 5: PLOT CONNECTIONS ARE NOT DESIGNED. One gravity check per plot - "
             "leaves BELOW ground, runs to a CHAMBER, loses fall over its own route length - "
             "and the answer is CAN_CONN / CONN_WHY / CONN_NEED. W11b published DRAIN_SHALLOW "
             "and admitted CAN_DRAIN 'cannot run', which is a check that cannot run and "
             "therefore a FAILURE (inheritance row 2).",
             "detailed design. The riders, laterals, PCC and HCC fields belong to it"),
    Excluded("an 'uphill is acceptable here' exemption flag",
             "philosophy sec 4 does not forbid uphill drainage - it BOUNDS AND REPORTS it. "
             "A per-reach exemption converts a reported quantity into a hidden one, which "
             "is exactly how 42.5 % of W11a's length came to drain uphill without anyone "
             "deciding that it should.",
             "never. AGN_GRADE and RISE_M are measurements; terrain_report() is the bound"),
)


# ======================================================================================
# Field and layer specification
# ======================================================================================

@dataclass(frozen=True)
class Field:
    """`required` and `blank_ok` are deliberately two different things.

    `required` means THE COLUMN MUST EXIST - the one a checker cares about, because a
    missing column cannot be evaluated and philosophy sec 8 makes an unevaluable check
    blocking. `blank_ok` means a ROW may legitimately hold no value: an outfall has no
    downstream node, a reach inside the cap has no cap exit. Conflating the two either
    forces a lie into an empty cell or lets a whole column go missing."""
    name: str
    dtype: str                       # "str" | "int" | "float"
    units: str
    why: str                         # WHY this field exists - the rule or check it feeds
    audit: str = ""                  # the check id(s) that read it, comma separated
    required: bool = True
    blank_ok: bool = False
    allowed: Optional[Tuple[str, ...]] = None
    lo: Optional[float] = None
    hi: Optional[float] = None

    @property
    def checks(self) -> Tuple[str, ...]:
        return tuple(c.strip() for c in self.audit.split(",") if c.strip())


F = Field


@dataclass(frozen=True)
class LayerSpec:
    name: str
    geom: str                        # "Point" | "LineString" | "Polygon" | "none"
    key: Optional[str]
    purpose: str
    fields: Tuple[Field, ...]
    audited: bool = False            # True == a check reads this layer directly
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
# Philosophy P6: SRC and a CONFIDENCE grade travel on every feature to the drawings and the
# schedules. STAGE makes "no stage silently no-ops" checkable after the fact.

_PROV = (
    F("SRC", "str", "-", "which source this came from. Corridor sources differ in trust by "
      "more than an order of magnitude and W10 merged them into one layer with the "
      "differences lost (P6)", allowed=SRC, audit="G5"),
    F("CONFIDENCE", "str", "-", "how far the thing under this feature can be trusted. A "
      "platted reserve with nothing built on it is a legal corridor at a saturation horizon "
      "but is never reported as existing (philosophy sec 4)",
      allowed=CONFIDENCE, audit="G5"),
    F("STAGE", "str", "-", "the stage that last wrote this row", audit="G4"),
    F("PACKAGE", "str", "-", "commissionable contract package; a station is a package seam",
      required=False),
    F("PHASE", "int", "-", "delivery phase, 0 = not yet assigned", required=False),
)


# ---- the naming group. Engineer's rule, 2026-09-06 ----------------------------------
#
# `required=True, blank_ok=True` and the pair is deliberate. The COLUMN must exist from the
# first stage that publishes the layer, because a column that appears late is one every
# earlier artefact cannot be checked against. The ROW may be blank until naming has run -
# and it must be allowed to, because ELEMENTS OUTSIDE A TOWN TAKE THE LETTER OF THE FIRST
# TOWN DOWNSTREAM OF THEM, so naming runs AFTER connectivity is known and cannot be done at
# the point a chamber is first minted.
#
# What stops a layer shipping with the column empty is not this spec: it is assert_named(),
# which the publishing stage calls, and which requires every row named, unique and
# grammatical. Two mechanisms, because they answer two different questions - "can this be
# checked?" and "was it actually done?".
_NAMING = (
    F("NAME", "str", "-", "the human name: I-S03-SM-M012 (manhole), I-S03-C012 (conduit, "
      "named for its UPSTREAM manhole), I-PMP02 (pump), I-P02 (force main). Built by "
      "concept_name() and checked against NAME_RE - a stored name that cannot be parsed is "
      "a label, not an identifier. NOTHING references it; identity is NODE_UID/EDGE_UID, so "
      "a retier can rewrite every name without orphaning a reference. (The 10-character "
      "limit is on the FIELD NAME, which is 4; the VALUE is a DBF string field and has room)",
      required=True, blank_ok=True),
    F("TOWN", "str", "-", "the town letter, from town_letters(): the settlement name with "
      "the Arabic article dropped, and on a clash BOTH towns extend - the town with more "
      "served plots is not favoured, because a code that depended on a plot count would "
      "move when the count did", required=True, blank_ok=True),
    F("SUBNET", "str", "-", "the subnetwork, S03. Blank on a station and its force main, "
      "and that blank is the rule rather than a gap: A STATION IS A SEAM BETWEEN "
      "subnetworks, not a member of one. Concept rule 2 makes the subnetwork the unit that "
      "joins the main pipe at its own lowest point, so this is the field every outfall "
      "question is grouped by", required=True, blank_ok=True),
)


# ---- the two primary layers ----------------------------------------------------------

NODES = LayerSpec(
    name="nodes",
    geom="Point",
    key="NODE_UID",
    audited=True,
    purpose=(
        "The chamber schedule AND the graph's vertex set. A chamber is the unit of design: "
        "without chambers there is no schedule, no profile, no take-off, no model and no "
        "package. W10 ran 11.1 nodes/km against the built network's 32.3."
    ),
    fields=(
        F("NODE_UID", "str", "-", "immutable identity, minted once by NodeIndex and never "
          "reassigned. Everything that references a chamber references THIS, so a pass-2 "
          "relabel cannot orphan a reference", audit="G3"),
        F("IS_OUTFALL", "int", "0/1", "1 where this chamber is where its system discharges. "
          "DERIVED from the graph - a node with no outgoing edge - and NEVER asserted; "
          "validate() rejects a value that disagrees with DS_NODE. H15 requires exactly one "
          "per connected component: not one network, because satellite works are legal, but "
          "never a piece that drains nowhere", audit="H15", lo=0, hi=1),
        F("NODE_REF", "str", "-", "the human/NAMA-style label (5A-2-SM.2-MH391). Derived "
          "from tier, package and sequence, recomputed freely, referenced by NOTHING - the "
          "network must read like theirs, and that must not cost referential integrity"),
        F("NODE_KIND", "str", "-", "what the structure is; drives the schedule and the "
          "drawing symbol. G203-p29 sec 4.4 lists the triggers a chamber may exist for",
          allowed=NODE_KIND),
        F("X", "float", "m", "authoritative easting. The Point geometry is BUILT from X/Y, "
          "not the other way round - geometry is a view of the graph"),
        F("Y", "float", "m", "authoritative northing"),
        F("GRD_M", "float", "m aOD", "ground level sampled from the 0.5 m bare-earth VRT "
          "(project rule 6). Named separately from the terrain so a check can resample and "
          "compare rather than trust", lo=-50.0, hi=1200.0),
        F("INV_M", "float", "m aOD", "invert of the OUTGOING reach - the governing level at "
          "this structure", lo=-50.0, hi=1200.0),
        F("DEPTH_M", "float", "m", "GRD_M - INV_M. Published rather than derived so the "
          "chamber schedule and the pipe layer cannot disagree; validate() checks the "
          "subtraction", lo=0.0, hi=DEPTH_SANITY_M),
        F("COVER_M", "float", "m", "cover to the crown of the shallowest connected pipe, on "
          "that pipe's OWN outside diameter, via cover(). G203-p33 minimum 1.30 m. W10 used "
          "a hardcoded 0.30 m and shipped 45.92 km below minimum", audit="H3",
          lo=0.0, hi=DEPTH_SANITY_M),
        F("TIER", "str", "-", "tier of the outgoing reach", allowed=TIERS, audit="H9"),
        F("DS_NODE", "str", "-", "THE forest invariant, STORED not computed: every node has "
          "exactly one downstream node, empty only at a terminal. H15 becomes true by "
          "construction instead of by audit, and H16 requires topology written down rather "
          "than inferred from geometry", audit="H15,H16", blank_ok=True),
        F("N_IN", "int", "-", "incoming reaches; >1 makes it a junction, and junction count "
          "is how the hierarchy is measured (philosophy sec 4)", lo=0, hi=20),
        F("N_OUT", "int", "-", "outgoing reaches - 0 at a terminal, 1 everywhere else, "
          "never more. Published so it can be cross-checked against the REACH layer's own "
          "out-degree: two independently computed numbers agreeing is what catches the W10 "
          "defect where the node and pipe layers came from different solves and disagreed "
          "by up to 10.39 m of depth", audit="H15", lo=0, hi=1),
        F("INLET_DEG", "float", "deg", "smallest angle any inlet makes with the outgoing "
          "flow. G203-p30, verbatim: 'No inlet pipe at manholes shall have an angle less "
          "than 90 deg to the direction of flow'", audit="H10", lo=0.0, hi=360.0),
        F("INLET_FLAG", "int", "0/1", "1 where INLET_DEG is short of 90 deg and a "
          "purpose-made swept channel is required. It distinguishes a KNOWN, PRICED problem "
          "from an unnoticed one - the resolution for a sharp inlet is a chamber detail, "
          "not a softer number", audit="H10", lo=0, hi=1),
        F("MH_DIA", "float", "m", "internal chamber diameter. G203-p30 requires >= 1.5 m "
          "wherever an internal backdrop is unavoidable; G203 gives no table of size against "
          "depth (searched), so this is the contractor's number and the take-off's and it is "
          "stored, not inferred at print time", required=False, lo=0.5, hi=6.0),
        F("MH_MAT", "str", "-", "chamber material. G203 says only 'sufficient size', so this "
          "is a stated assumption per PAM-SPC, not a criterion",
          required=False, blank_ok=True),
        F("DROP_M", "float", "m", "external backdrop height. G203-p30: a backdrop is required "
          "above 0.60 m and a vortex drop shaft above 2.0 m. The upper bound on this field "
          "IS criteria.DROP_CEILING_M - one constant, so the design and the validator cannot "
          "drift, and an over-cap exit is WITHDRAWN rather than clipped (philosophy sec 5)",
          lo=0.0, hi=C.DROP_CEILING_M),
        F("DROP_TYPE", "str", "-", "none / backdrop / vortex - ramped and EXTERNAL to the "
          "manhole (G203-p30). Never used to dodge a station", allowed=DROP_TYPE),
        F("DROP_WHY", "str", "-", "WHY THIS DROP EXISTS - velocity_cap / tier_step / "
          "cover_recovery / obstruction, blank where there is no drop. Concept rule 1: the "
          "laid slope is a clamp, and where the ground outruns the pipe the surplus fall is "
          "taken as a drop - so a drop is a DECISION and it carries its reason. Without it a "
          "drop cannot be told from a levelling error, and the drop count is the diagnostic "
          "for a tree that is not following the ground. validate() requires it wherever "
          "DROP_M > 0 and REFUSES a column that is constant across every drop on a network "
          "of any size (inheritance row 22: ANGLE_DEG = 90 on all 3,290 crossings)",
          allowed=DROP_WHY, audit="C1", blank_ok=True),
        F("JOIN_MAIN", "int", "0/1", "1 where this chamber is where its subnetwork MEETS the "
          "main pipe. Concept rule 2: a subnetwork joins the main pipe at the LOWEST POINT "
          "WHERE IT MEETS IT, and no subnetwork crosses the main pipe and grows past it. In "
          "W11b two subnetworks held a quarter of the whole network - 7,871 and 6,271 "
          "chambers - each touching the main pipe at 1.1 m and 3.1 m and discharging "
          "somewhere else entirely", audit="C2", lo=0, hi=1),
        F("JOIN_OFF_M", "float", "m", "metres from the subnetwork's TRUE low point to where "
          "it actually connects; 0.0 when it connects AT the low point. NOT a tolerance and "
          "not a defect on its own - if there is no street at the low point the connection "
          "goes to the nearest usable place and THE DISTANCE IS RECORDED, which is the whole "
          "of concept rule 2's second half. A design that cannot say how far off it is "
          "cannot be argued with. (Named JOIN_OFF_M, not JOIN_OFFS_M: 11 characters would be "
          "truncated by the DBF and no check would find it afterwards)",
          audit="C2", lo=0.0, blank_ok=True),
        F("JOIN_WHY", "str", "-", "why the join is not at the true low point - free text, "
          "because the reasons are situational ('no street at the low point, nearest "
          "crossing 210 m north'). Required wherever JOIN_OFF_M > 0; blank where the join "
          "IS at the low point. An offset with no reason is an unexplained outfall, and 42 "
          "of W11b's discharged with more than half their catchment below them",
          audit="C2", blank_ok=True),
        F("VORTEX", "int", "0/1", "1 where DROP_M > 2.0 m and a vortex drop shaft is "
          "required (G203-p30). Its own flag because it is a DIFFERENT STRUCTURE with a "
          "different cost, not a deeper backdrop - and because the count of these is the "
          "diagnostic for a tree that is not following the ground. The built network has 37",
          audit="H4c", lo=0, hi=1),
        F("Q_ADF_M3D", "float", "m3/d", "accumulated sanitary average dry weather flow, "
          "infiltration EXCLUDED", lo=0.0),
        F("Q_PK_LS", "float", "L/s", "accumulated peak flow including unpeaked infiltration; "
          "the number the outgoing reach is sized on", lo=0.0),
        F("N_PROP", "float", "-", "properties served at or above this node - the unit the "
          "options appraisal costs per (metres per property)", lo=0.0),
        F("PAST_CAP", "int", "0/1", "1 where cover exceeds the 12 m cap (criteria.MAX_COVER, "
          "G203-p33 read as a cap)", audit="H4", lo=0, hi=1),
        F("CAP_EXIT", "str", "-", "which philosophy sec 5 exit allowed it: cover recovers "
          "within 500 m, or the run reaches the outfall within 1,000 m. Blank when "
          "PAST_CAP = 0. Nothing past the cap is final until a manufacturer's rating and "
          "NWS's station cost arrive", allowed=CAP_EXIT, audit="H4b", blank_ok=True),
    ) + _NAMING + _PROV,
    refs=(("DS_NODE", "nodes", "NODE_UID"),),
)


REACHES = LayerSpec(
    name="reaches",
    geom="LineString",
    key="EDGE_UID",
    audited=True,
    purpose=(
        "GRAVITY reaches only - chamber to chamber, one gradient each (G203-p29: 'Uniform "
        "slopes must be maintained between successive manholes'). Rising mains are NOT here: "
        "the open-channel checks would return nonsense for a pressure pipe, and G203-p50 "
        "caps a rising main at 2.5 m/s against the gravity 3.0 m/s."
    ),
    fields=(
        F("EDGE_UID", "str", "-", "immutable reach identity"),
        F("US_NODE", "str", "-", "upstream chamber, written FROM the graph. W10 had neither "
          "this nor DS_NODE, so connectivity could only be guessed by a tolerance - which is "
          "how it published 7,919 pieces (H16)", audit="G3,H16"),
        F("DS_NODE", "str", "-", "downstream chamber", audit="G3,H16"),
        F("TIER", "str", "-", "rider / lateral / main / sub main / trunk main. Target shares "
          "near the as-built: lateral 66 %, sub main 18 %, trunk 5 % (philosophy sec 4). The "
          "SPACED spelling is canonical - an unrecognised tier is a SILENT skip in a "
          "diameter-floor check, so validate() rejects the underscore forms",
          allowed=TIERS, audit="H9"),
        F("DN", "int", "mm", "nominal diameter, and it MUST be a member of "
          "criteria.DN_SERIES - validate() checks membership, not just a range, so the layer "
          "and the sizing function cannot disagree about what sizes exist. OD-designated to "
          "DN315 (G203-p22 Table 6)", audit="H2,H3,H4,H9,H12", lo=100, hi=2400),
        F("MATERIAL", "str", "-", "checked against criteria.materials_allowed(TIER, DN), "
          "which honours G203-p22 Table 6 (by application), p23 Table 7 (by product) and "
          "p35 Table 14 (trunk) together. PVC-U is a permitted product to OD315 but a "
          "permitted MAIN SEWER only to 250 mm", allowed=MATERIAL, audit="H9"),
        F("CONSTR", "str", "-", "open trench or trenchless. The permitted material set "
          "differs between them (G203-p22 Table 6) and a crossing is priced, not assumed",
          allowed=CONSTR, required=False),
        F("LEN_M", "float", "m", "laid length. Checked against the geometry it sits on to "
          "LEN_TOL_M, because every published length reads this FIELD and not the line. "
          "G203-p30 Table 12 caps chamber spacing by diameter and W10 had 4,763 reaches over "
          "the limit, longest 6,541 m", audit="H12", lo=0.5, hi=250.0),
        F("SLOPE_LAID", "float", "%", "THE LAID GRADIENT, on criteria.SLOPE_STEP (0.05 %) "
          "steps. Publishing only the minimum, as W10 did, makes velocity, fall and drop all "
          "uncheckable", audit="G1,H2,H5,H6,H7,H13", lo=0.0, hi=25.0),
        F("SLOPE_MIN", "float", "%", "the governing minimum beside it: the STEEPER of "
          "G203-p29 Table 11 and the tractive minimum at this reach's own peak flow "
          "(hydra.smin_for). G203-p27 says the steeper governs. A layer carrying only the "
          "minimum cannot be checked; one carrying only the laid value cannot be justified",
          audit="G1,H6", lo=0.0, hi=25.0),
        F("GRAD_BY", "str", "-", "what SET the laid gradient", allowed=GRAD_BY, audit="G2"),
        F("SIZED_BY", "str", "-", "what set the diameter. This enum is exactly what "
          "hydra.size_pipe() can return, and 'depth' and 'cover' are PROHIBITED answers "
          "(G203-p29; Ten States sec 33.43 independently) - so the prohibited move is not "
          "expressible", allowed=SIZED_BY, audit="H8,G2"),
        F("CLEAN_BY", "str", "-", "which self-cleansing route this LAID reach satisfies - "
          "velocity, tractive, or neither (hydra.clean_route). H5 requires it recorded, "
          "because the tractive share is a REPORTED number: it rests on tau = 1.0 Pa, which "
          "G203 never gives (GAP-9), and at 2.0 Pa the requirement rises 2.346x",
          allowed=CLEAN_BY, audit="H5"),
        F("TAU_PA", "float", "Pa", "the tractive assumption this reach was checked at, "
          "carried ON THE ROW so a sensitivity run is visible in the layer and not only in a "
          "note. The engineer asked on 2026-09-03 for tau flagged on every output; this is "
          "the machine-readable half of that flag", lo=0.1, hi=10.0),
        F("INV_UP", "float", "m aOD", "upstream invert. H11 tests INV_UP - INV_DN against "
          "the 20 mm laying tolerance for reverse gradient (G203-p29)", audit="H11"),
        F("INV_DN", "float", "m aOD", "downstream invert", audit="H11"),
        F("US_DEPTH", "float", "m", "ground to INVERT at the upstream node - must equal the "
          "upstream node's DEPTH_M exactly", audit="H3,H4", lo=0.0, hi=DEPTH_SANITY_M),
        F("DS_DEPTH", "float", "m", "ground to invert at the downstream node",
          audit="H3,H4", lo=0.0, hi=DEPTH_SANITY_M),
        F("COVER_US", "float", "m", "cover to crown upstream, from cover(), published so an "
          "independent recomputation has something to disagree with. G203-p33 minimum 1.30 m",
          audit="H3", lo=0.0, hi=DEPTH_SANITY_M),
        F("COVER_DN", "float", "m", "cover to crown downstream", audit="H3",
          lo=0.0, hi=DEPTH_SANITY_M),
        F("QADF_M3D", "float", "m3/d", "sanitary average dry weather flow, infiltration "
          "EXCLUDED, at the ultimate horizon (philosophy sec 6: size on ultimate, check "
          "self-cleansing at start-year)", lo=0.0),
        F("QINF_LS", "float", "L/s", "infiltration on THIS reach, UNPEAKED - 720 L/d/km of "
          "sewer, G201-p72 sec 7.4.3, for NEW networks. Kept separate from QADF so QPK_LS is "
          "reproducible from the row. Summing a cumulative per-reach value counts every "
          "kilometre once per downstream reach, which is how 14.5 L/s was published as 1,259",
          lo=0.0),
        F("PF", "float", "-", "peak factor, applied to the sanitary component ONLY", lo=1.0,
          hi=8.0),
        F("PF_METH", "str", "-", "which formula produced PF: merrimack (G201-p71, 'is to be "
          "used' above 100 properties), peltier (the stated alternative), or HELD - the "
          "honest token for a catchment below the threshold where G201 prescribes no formula "
          "at all", allowed=PF_METH),
        F("QPK_LS", "float", "L/s", "peak design flow = QADF x PF + QINF. The flow every "
          "hydraulic check solves against; validate() reproduces it from the row",
          audit="H2,H5,H6,H7", lo=0.0),
        F("V_PK_MS", "float", "m/s", "velocity at peak, against the 3.0 m/s gravity maximum "
          "(G203-p27 sec 4.2.2.2)", audit="H7", lo=0.0, hi=10.0),
        F("DOD_PK", "float", "-", "d/D at peak. G203-p27 Table 10: 0.65 up to DN350, 0.50 "
          "above - validate() applies criteria.dod_limit(DN), so the limit cannot be applied "
          "at the wrong threshold. W10 shipped 5 surcharged reaches and 66 over the limit",
          audit="H2", lo=0.0, hi=1.0),
        F("RET_MIN", "float", "min", "retention time in this reach. Philosophy sec 6: "
          "septicity is a design driver, and long flat lightly-loaded runs at Omani "
          "temperatures are the H2S combination", lo=0.0),
        F("GND_FALL", "float", "m", "GROUND fall along this reach, upstream ground minus "
          "downstream ground. NEGATIVE means the ground RISES along the direction of flow. "
          "NEW IN W12 and the whole point of it: W11a used the terrain only to check the "
          "answer, and 42.5 % of its length ended up draining uphill. A number cannot be "
          "reported if it was never carried"),
        F("AGN_GRADE", "int", "0/1", "1 where this reach carries flow AGAINST the ground - "
          "GND_FALL below -criteria.ADVERSE_MIN_M. Philosophy sec 4: uphill drainage is not "
          "forbidden, it is BOUNDED AND REPORTED. terrain_report() is the bound",
          audit="H17", lo=0, hi=1),
        F("RISE_M", "float", "m", "how much the ground rises along this reach - 0 where it "
          "falls. The reach buys this rise in depth at the minimum gradient for its whole "
          "length, and pays for it again giving the depth back", lo=0.0),
        F("PAST_CAP", "int", "0/1", "1 where cover exceeds 12 m", audit="H4", lo=0, hi=1),
        F("CAP_EXIT", "str", "-", "which sec 5 exit allowed it; blank inside the cap",
          allowed=CAP_EXIT, audit="H4,H4b", blank_ok=True),
        F("CAP_LEN_M", "float", "m", "length past the cap, and the distance to the recovery "
          "or to the outfall - the exits are DISTANCE-bounded, so the distance is the "
          "evidence", audit="H4b", lo=0.0),
        F("TIE_TYPE", "str", "-", "none / soffit / invert. H14: an existing structure's "
          "invert is fixed and the design yields to it; tie SOFFIT to soffit. The check "
          "cannot run at all without this field", allowed=TIE_TYPE, audit="H14"),
        F("ON_DUAL_M", "float", "m", "metres of this reach inside the dual-carriageway band. "
          "Expected 0 (project rule 7: no pipe of any kind runs ALONG a dual carriageway, "
          "trunk included, because it cannot be dug up). A check recomputes it independently, "
          "so a disagreement is itself the finding", audit="H1,R3", lo=0.0),
        F("ON_WADI_M", "float", "m", "metres on wadi ground - flood-hazard classes 4/5/6 of "
          "the 50-year grid (criteria.HAZARD_WADI_CLASSES, a PROJECT ASSUMPTION standing in "
          "for G203's 'areas subject to washout'). Expected 0 except on a SCHEDULED "
          "perpendicular crossing", audit="R4", lo=0.0),
        F("CROSS_ID", "str", "-", "links to the crossings REGISTER where this reach IS a "
          "crossing. A crossing is legal only if it is scheduled, and an id with no register "
          "row behind it schedules nothing - assert_crossings_resolve() enforces both",
          audit="H1,H1a,R4", blank_ok=True),
    ) + _NAMING + _PROV,
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
        "DUTY and not on arriving flow, runs 0.75-2.5 m/s (G203-p50, not the gravity 3.0), "
        "and is anaerobic by definition - so its discharge chamber is a septicity problem, "
        "not a pipe end. Same node identity, same graph."
    ),
    fields=(
        F("EDGE_UID", "str", "-", "identity"),
        F("US_NODE", "str", "-", "the station"),
        F("DS_NODE", "str", "-", "the discharge chamber"),
        F("STATION", "str", "-", "NODE_UID of the station whose duty sized this"),
        F("DN", "int", "mm", "sized on DUTY flow, never on arriving flow. G203-p50 sec 8.1: "
          "minimum 75 mm INSIDE diameter for non-clog pumps, 50 mm for grinder pumps",
          lo=50, hi=2400),
        F("MATERIAL", "str", "-", "G203-p53 sec 8.3: 'The recommended material for the pipes "
          "and fittings within the pumping station shall be Ductile Iron. For small capacity "
          "pumping stations (less than 100 L/s), pipe material shall be stainless steel.' "
          "Pressure class per PAM-SPC-207, pending", allowed=MATERIAL),
        F("LEN_M", "float", "m", "length, checked against the geometry", lo=0.0),
        F("Q_DUTY_LS", "float", "L/s", "pump duty from the wet-well cycle", lo=0.0),
        F("V_DUTY_MS", "float", "m/s", "velocity at duty. G203-p50: maximum 2.5 m/s",
          lo=0.0, hi=5.0),
        F("V_MIN_MS", "float", "m/s", "velocity at the DESIGN MINIMUM flow. G203-p50 sec 8.1 "
          "is explicit that the 0.75 m/s floor is held THERE, not at average flow, and "
          "G203-p40 Table 16 supplies that flow. Sizing on duty alone silts the main in "
          "year one", required=False, lo=0.0, hi=5.0),
        F("STAT_HD_M", "float", "m", "static lift", lo=0.0),
        F("TOT_HD_M", "float", "m", "total head at duty", lo=0.0),
        F("RETENT_M", "float", "min", "retention time. G203-p50 wants it under 30 min; beyond "
          "that the discharge chamber is a septicity design, not a note",
          required=False, lo=0.0),
        F("N_AIRV", "int", "-", "double-orifice air valves at summits (G203-p53-54 sec 8.4)",
          lo=0),
        F("N_WASH", "int", "-", "washouts at low points, sized for 3-4 h section emptying "
          "(G203-p53-54 sec 8.4)", lo=0),
        F("SEPTIC_FL", "int", "0/1", "1 where the discharge chamber needs septicity "
          "treatment - always 1 in practice, and recorded so it is DESIGNED rather than "
          "assumed away (G203-p55 sec 8.5: water seal, forced venting, corrosion-resistant "
          "receiving manhole)", lo=0, hi=1),
        F("DS_TYPE", "str", "-", "WHAT this main discharges into: 'manhole' (gravity resumes "
          "here) or 'stp' (it runs to the works). Concept rule 6: A RISING MAIN LIFTS TO THE "
          "NEAREST POINT WHERE GRAVITY RESUMES, NOT TO THE WORKS - long force mains go "
          "anaerobic, need an air valve at every summit and a washout at every low point, "
          "and are a single point of failure for everything upstream. The built network's "
          "10.0 km main straight to the works is explained by there being no gravity network "
          "to receive it in 2006, not by it being right. Stored so the share of mains ending "
          "at 'stp' is a number on the deliverable rather than a claim in a paragraph",
          allowed=DS_TYPE, audit="C5"),
    ) + _NAMING + _PROV,
    refs=(("US_NODE", "nodes", "NODE_UID"), ("DS_NODE", "nodes", "NODE_UID"),
          ("STATION", "stations", "NODE_UID")),
)


STATIONS = LayerSpec(
    name="stations",
    geom="Point",
    key="NODE_UID",
    purpose=(
        "Lifting stations, each one a node in the same graph. A station is a COMMISSIONING "
        "device as much as a depth device: in NAMA's own network one station plus one force "
        "main is what let 60.8 km and about 5,963 properties be commissioned without first "
        "building 7 km of deep gravity trunk. WHY records which rung of the cap-and-veto "
        "ladder put it here, because economics is the third rung and never the first."
    ),
    fields=(
        F("NODE_UID", "str", "-", "the same identity the node carries in `nodes`"),
        F("NODE_REF", "str", "-", "label"),
        F("WHY", "str", "-", "cap / veto / economics / commissioning. Layers 1 and 2 can only "
          "ADD a station; economics can only make you pump EARLIER, never later "
          "(philosophy sec 5)", allowed=STATION_WHY),
        F("ST_TYPE", "str", "-", "G203-p40: Type 1 up to 100 l/s (1 duty + 1 standby), "
          "Type 2 >100-300 (2+1), Type 3 >300 (3+1). Stored because it is the key to the "
          "p43 Table 21 land band and the pump count, and re-deriving it at print time is "
          "how seven different station counts got into circulation on this project",
          allowed=ST_TYPE),
        F("Q_DUTY_LS", "float", "L/s", "duty flow. ZERO IS NOT A VALID DESIGN VALUE - W11a "
          "published 226 stations with Q_DUTY_LS = 0 on every one, which is a located "
          "station, not a designed one", lo=0.0),
        F("LIFT_M", "float", "m", "static lift - the number that matters more than the "
          "station COUNT, because distance-clustering only measures breach density", lo=0.0),
        F("N_PROP", "float", "-", "properties upstream", lo=0.0),
        F("Q_ADF_M3D", "float", "m3/d", "average flow through it", lo=0.0),
        F("WELL_M3", "float", "m3", "wet-well live volume. G203-p48 sec 7.8: V = 0.25 Q T, "
          "T = 3600 / starts per hour", lo=0.0),
        F("WW_STARTS", "float", "1/h", "the assumed starts per hour, DECLARED. G203-p48 sets "
          "a minimum of 10/h for motors up to 30 kW, and it is the only thing that turns "
          "WELL_M3 into a number - a wet-well volume with no start rate behind it cannot be "
          "checked or costed", lo=1.0, hi=60.0),
        F("GRD_M", "float", "m aOD", "ground level at the station", required=False,
          lo=-50.0, hi=1200.0),
        F("FLOOD_LV", "float", "m aOD", "the 1:50-yr flood level here. G203-p38 sec 7.2: "
          "floors and every electrical item sit at least 300 mm above it. A station in a wadi "
          "margin is a siting failure that costs the whole asset, and it is invisible unless "
          "the level is on the row", lo=-50.0, hi=1200.0),
        F("LAND_M2", "float", "m2", "indicative land take. G203-p43 Table 21: Type 1 "
          "50-100 m2, Type 2 200-400, Type 3 >=900, plus a 6 m turning circle. This is a land "
          "RESERVATION the client has to make, so it belongs in the concept output", lo=0.0),
        F("INV_M", "float", "m aOD", "incoming invert at the station - the level gravity "
          "arrives at, and the bottom end of LIFT_M. Denormalised from the node of the same "
          "NODE_UID (as GRD_M already is) so the station schedule is readable on its own; it "
          "MUST equal nodes.INV_M for that uid, and a station whose two layers disagree "
          "about its invert is the W10 defect where the node and pipe layers came out of "
          "different solves", required=False, lo=-50.0, hi=1200.0),
        F("N_SUBNET", "int", "-", "how many subnetworks drain into this station. ZERO IS A "
          "FINDING, NOT A VALUE: 15 of W11b's 47 stations had nothing draining into them. "
          "Concept rule 6 - a station's POSITION IS CHOSEN, NOT TRIGGERED - and this is half "
          "the evidence that it was chosen: a site is scored by how much it CAPTURES",
          audit="C5", lo=0),
        F("CATCH_KM", "float", "km", "kilometres of network captured upstream of this "
          "station - the other half of the same evidence. Station cost correlates 0.99 with "
          "power and 0.72 with head, and 86 % of life-cycle cost is MANNING, so twenty small "
          "stations cost about twenty times one large one however little each lifts. The "
          "2006 designer put ONE station in 95.45 km. A station with a large lift and a small "
          "catchment is the one to argue about, and neither number alone shows it",
          audit="C5", lo=0.0),
        F("RM_EDGE", "str", "-", "EDGE_UID of its rising main", required=False,
          blank_ok=True),
        F("COMM_PT", "int", "0/1", "1 where this station makes its package commissionable on "
          "its own", required=False, lo=0, hi=1),
    ) + _NAMING + _PROV,
    refs=(("NODE_UID", "nodes", "NODE_UID"),),
)


CONNECTIONS = LayerSpec(
    name="connections",
    geom="LineString",
    key="CONN_ID",
    purpose=(
        "One row per LOAD UNIT, and the direct answer to 'every load unit is assigned to "
        "exactly one chamber, or listed by name'. W10 dropped 1,233 m3/d - 1.7 % - silently, "
        "because an assignment radius failed quietly. A load with no OUT_NODE must carry a "
        "WHY, and the Funnel that produced it must name the ids."
    ),
    fields=(
        F("CONN_ID", "str", "-", "identity"),
        F("PLOT_ID", "str", "-", "the plot this load belongs to"),
        F("OUT_NODE", "str", "-", "the chamber this load enters the network at. Blank ONLY "
          "when WHY says why, and then the plot appears in the not-served schedule - the "
          "scope requires every plot SERVED, though not necessarily by this network",
          blank_ok=True),
        F("WHY", "str", "-", "why it is unassigned, or 'assigned'. Never blank"),
        F("SYSTEM", "str", "-", "which system serves it: the central network, a satellite "
          "works, or on-site. 'Serviced' is not 'connected to one network', and that "
          "distinction is the whole design question (philosophy sec 8a)", allowed=SYSTEM),
        F("CONN_TYPE", "str", "-", "PCS / rider / lateral. G203-p17 sec 3.2 fixes the chain "
          "PCC -> PC sewer -> HCC -> rider -> lateral, and the limits differ per link",
          required=False),
        F("Q_ADF_M3D", "float", "m3/d", "the load", lo=0.0),
        F("N_PROP", "float", "-", "properties on the plot, counted from electricity accounts",
          lo=0.0),
        F("LEN_M", "float", "m", "connection length. G203-p18: the PCS 'should not exceed "
          "50 m in order to allow maintenance'; G203-p22 Table 6 caps a lateral at 45 m",
          lo=0.0),
        F("SLOPE_LAID", "float", "%", "G203-p18 Table 5: 3-10 % for a property connection, "
          "1-10 % for a rider or a lateral. Named SLOPE_LAID, not SLOPE_PCT - the same name "
          "meant two different gradients in two W10 files", lo=0.0, hi=30.0),
        F("COVER_M", "float", "m", "G203-p19 sec 3.5: minimum 600 mm on a property connection",
          lo=0.0),
        F("CAN_DRAIN", "int", "0/1", "does the plot outlet sit above the sewer invert where it "
          "joins. 0 is not a rounding error - it is a plot the gravity network does not "
          "actually serve, and it must reach the not-served schedule. SUPERSEDED AT CONCEPT "
          "BY CAN_CONN, which asks the same question in a form that can actually be computed "
          "- kept because s8 writes it and the two must agree",
          required=False, lo=0, hi=1),
        F("CAN_CONN", "int", "0/1", "CAN THIS PLOT CONNECT, on gravity, to a CHAMBER. Concept "
          "rule 5: one simple check per plot - the connection leaves BELOW ground level (not "
          "at it), runs to a CHAMBER (not to the nearest point on a pipe), and loses fall "
          "over its OWN ROUTE LENGTH. This is the field that closes the gap W11b left open: "
          "it published DRAIN_SHALLOW - a bound at minimum cover - and recorded CAN_DRAIN as "
          "'cannot run', and a check that cannot run is a FAILURE, not a blank "
          "(inheritance row 2)", audit="C3", lo=0, hi=1),
        F("CONN_WHY", "str", "-", "why it cannot connect; blank where it can. Free text, "
          "kept short and reusable so the not-served schedule groups - e.g. 'sewer above the "
          "plot outlet', 'no chamber within reach', 'route rises'. Concept rule 7 is FLAG, "
          "DO NOT SOLVE: anything unresolvable at concept is named with its REASON and its "
          "SIZE, never silently dropped. This is the reason; CONN_NEED is the size",
          audit="C3", blank_ok=True),
        F("CONN_NEED", "float", "m", "WHAT IT WOULD TAKE, in metres - how much deeper the "
          "sewer on this run would have to be for the plot to reach it on gravity. 0.0 where "
          "it already connects. A named gap with no size cannot be priced, cannot be ranked "
          "and cannot be argued about, and 5,521 plots is a number nobody can act on until "
          "it is 5,521 plots needing this much depth on these runs", audit="C3", lo=0.0),
    ) + _NAMING + _PROV,
    refs=(("OUT_NODE", "nodes", "NODE_UID"),),
)


CORRIDORS = LayerSpec(
    name="corridors",
    geom="LineString",
    key="CORR_ID",
    purpose=(
        "The legal routes, with the wadi and dual-carriageway exclusions already applied AT "
        "SOURCE (philosophy sec 2 - exclusions apply HERE, not in the router). The perverse "
        "W10 result this exists to stop: the sources trusted LEAST were used MOST."
    ),
    fields=(
        F("CORR_ID", "str", "-", "identity"),
        F("LEN_M", "float", "m", "length, checked against the geometry", lo=0.0),
        F("WIDTH_M", "float", "m", "public reserve width. Philosophy sec 4 requires a reserve "
          "of STATED width, and G203-p33 requires 3 m clearance to other utilities. The "
          "corridor widths themselves are G203-p32 Table 13 / p35 Table 15 by diameter",
          lo=0.0),
        F("ON_DUAL_M", "float", "m", "expected 0 after the exclusion", lo=0.0),
        F("ON_WADI_M", "float", "m", "expected 0 after the exclusion, except on a scheduled "
          "crossing", lo=0.0),
        F("IS_STREET", "int", "0/1", "1 = an observed built street; 0 = a platted reserve "
          "with nothing built on it, which is a legitimate corridor at a saturation horizon "
          "but is NEVER reported as existing (philosophy sec 4)", lo=0, hi=1),
        F("N_PLOT", "int", "-", "load-bearing plots fronting it. 117.3 km of W10 had none "
          "within 60 m and carried under 1 m3/d - it neither collected nor conveyed", lo=0),
        F("USED", "int", "0/1", "1 where a reach was laid on it. The conversion rate per SRC "
          "is the number that exposed the W10 inversion", lo=0, hi=1),
        F("GND_FALL", "float", "m", "ground fall end to end. NEW IN W12: a corridor knows "
          "which way the ground goes BEFORE anything is routed along it. That is the whole "
          "change of method"),
        F("CROSS_ID", "str", "-", "links to the crossings register where this corridor "
          "CROSSES a wadi or a dual carriageway. A corridor with ON_WADI_M > 0 and no "
          "CROSS_ID is a defect, not a rounding residue", blank_ok=True),
    ) + _PROV,
    refs=(("CROSS_ID", "crossings", "CROSS_ID"),),
)


CROSSINGS = LayerSpec(
    name="crossings",
    geom="LineString",
    key="CROSS_ID",
    purpose=(
        "THE REGISTER. A crossing that is not on this layer is not a crossing; it is a pipe "
        "in a place it may not be. H1a makes a wadi crossing legal only when it crosses "
        "rather than runs along, carries no chamber on wadi ground, has 1.5 m of cover, and "
        "IS IN THIS REGISTER. W10 shipped 47 unscheduled crossings."
    ),
    fields=(
        F("CROSS_ID", "str", "-", "identity, referenced by the reach or the corridor"),
        F("EDGE_UID", "str", "-", "the reach that crosses. Blank while the register is a "
          "corridor-stage product and no reach exists yet", blank_ok=True),
        F("OBSTACLE", "str", "-", "WHAT is crossed. The single most important field on this "
          "layer: a CROSS_ID that resolves to a row is not enough - the row must say the "
          "obstacle the reach claims to cross, or the register schedules something else",
          allowed=OBSTACLE, audit="H1,H1a,R4"),
        F("LEN_M", "float", "m", "crossing length, checked against the geometry. "
          "criteria.DUAL_XING_MAX_M caps a dual-carriageway crossing at 70 m", lo=0.0),
        F("ANGLE_DEG", "float", "deg", "MEASURED angle to the obstacle - never asserted. A "
          "constant 90 was published on 3,290 crossings once and the measured minimum was "
          "0.00 deg. criteria.WADI_XING_SKEW_DEG (25 deg) is how far off square is tolerated",
          lo=0.0, hi=180.0),
        F("METHOD", "str", "-", "open cut / thrust bore / microtunnel / an existing underpass "
          "or culvert. G203-p35 and p21: trenchless is used where trenching is not feasible, "
          "subject to NWS approval, and it is PRICED, not assumed",
          allowed=XING_METHOD),
        F("COVER_M", "float", "m", "cover at the crossing. G203-p52 sec 8.2.4 gives 1.5 m to "
          "crown at a wadi crossing against 1.30 m normal - the one place the ordinary "
          "minimum is not the governing one. Adopting the force-main figure for gravity is "
          "OUR decision (criteria.MIN_COVER_WADI_XING)", required=False, lo=0.0),
        F("APPROVED", "int", "0/1", "1 once a third-party consent exists - MoAFWR for a wadi "
          "(G201-p85), the roads authority for a carriageway. 0 is an OPEN item, not a "
          "silent one", lo=0, hi=1),
    ) + _PROV,
)


PACKAGES = LayerSpec(
    name="packages",
    geom="none",
    key="PACKAGE",
    purpose=(
        "One row per commissionable contract package: 3.5-40 km serving 180-2,180 plots, ONE "
        "connected tree with EXACTLY ONE outlet. W10's 206 subnetworks were unusable as "
        "packages - median 1.16 km, largest 265.8 km."
    ),
    fields=(
        F("PACKAGE", "str", "-", "identity"),
        F("PHASE", "int", "-", "delivery phase", lo=0),
        F("LEN_KM", "float", "km", "3.5-40 km", lo=0.0),
        F("N_PLOT", "int", "-", "180-2,180 plots", lo=0),
        F("OUTLET", "str", "-", "the single NODE_UID it discharges at"),
        F("DS_PKG", "str", "-", "the package downstream. NAMA's own chain is 5A-3 -> 5A-2 -> "
          "5A-4 -> 5A-1 -> station -> force main -> STP, so no package commissions before "
          "its downstream neighbour exists", required=False, blank_ok=True),
        F("COMM_SEQ", "int", "-", "commissioning order", required=False, lo=0),
        F("INDEP", "int", "0/1", "1 where it can be commissioned WITHOUT its downstream "
          "neighbour - it ends at a station, at the works, or at the existing network. This "
          "is the property a station buys", required=False, lo=0, hi=1),
        F("ONE_TREE", "int", "0/1", "1 = one connected tree with one outlet. 0 is a FAILED "
          "package, not a note", lo=0, hi=1),
    ),
    refs=(("OUTLET", "nodes", "NODE_UID"),),
)


# ---- the terrain layers. W12's own, and the reason it exists. -----------------------
#
# THE REQUIRED CORE IS DELIBERATELY SMALL. A contract that demands fields the terrain stage
# has not invented yet blocks the stage instead of protecting it, and `validate()` allows
# extra columns by default. Add a field HERE when it exists - never at the point of writing,
# which is how a layer grows nine fields with no provenance and no check behind any of them.

STREAMS = LayerSpec(
    name="streams",
    geom="LineString",
    key="STREAM_ID",
    purpose=(
        "THE GROUND'S OWN ANSWER: the drainage network derived from the terrain by flow "
        "direction and accumulation, before any road, plot or pipe is considered. W11a built "
        "its tree on road connectivity and checked it against the terrain afterwards; 42.5 % "
        "of the length then drained uphill. This layer is what the design follows instead. "
        "It is NOT a pipe layer and nothing is ever laid IN a stream - G203-p30 sec 4.4.1 "
        "prohibits pipes and chambers in wadis. It is the direction field the layout obeys."
    ),
    fields=(
        F("STREAM_ID", "str", "-", "identity"),
        F("LEN_M", "float", "m", "length, checked against the geometry", lo=0.0),
        F("ORDER_", "int", "-", "Strahler order, or 0 where not computed. Named with the "
          "trailing underscore because ORDER is a reserved word in the SQL a GeoPackage is "
          "queried with", required=False, lo=0),
        F("ACC_CELLS", "float", "-", "flow accumulation at the downstream end, in DEM cells. "
          "Published rather than a derived area so the threshold that made this a stream can "
          "be reproduced from the row", required=False, lo=0.0),
        F("GND_FALL", "float", "m", "ground fall along it, upstream minus downstream. A "
          "stream with a negative fall means the flow direction was written the wrong way "
          "round, which is a bug and not a landform", required=False),
        F("IS_WADI", "int", "0/1", "1 where this stream coincides with wadi ground - "
          "flood-hazard classes 4/5/6 of the 50-year grid. The prohibition attaches to the "
          "HAZARD GRID, not to this layer; this flag is how the two are related",
          required=False, lo=0, hi=1),
    ) + _PROV,
)


BASINS = LayerSpec(
    name="basins",
    geom="Polygon",
    key="BASIN_ID",
    purpose=(
        "Terrain catchments - the area draining to each stream outlet. The natural unit for "
        "deciding where a sewer catchment's ONE way out should be, which philosophy sec 4 "
        "says is what defines a sub main: 'a sub main exists because a catchment needs one "
        "way out, not because a ratio was met'."
    ),
    fields=(
        F("BASIN_ID", "str", "-", "identity"),
        F("AREA_M2", "float", "m2", "area", lo=0.0),
        F("OUT_X", "float", "m", "easting of the basin's lowest point - its pour point"),
        F("OUT_Y", "float", "m", "northing of the pour point"),
        F("OUT_Z", "float", "m aOD", "ground level at the pour point", required=False,
          lo=-50.0, hi=1200.0),
        F("DS_BASIN", "str", "-", "the basin this one drains into; blank at the bottom of the "
          "system. Terrain topology, written down for the same reason pipe topology is (H16)",
          required=False, blank_ok=True),
        F("N_PLOT", "int", "-", "load-bearing plots inside it", required=False, lo=0),
        F("Q_ADF_M3D", "float", "m3/d", "load generated inside it", required=False, lo=0.0),
    ) + _PROV,
)


LAYERS: Dict[str, LayerSpec] = {s.name: s for s in (
    NODES, REACHES, RISING_MAINS, STATIONS, CONNECTIONS, CORRIDORS, CROSSINGS, PACKAGES,
    STREAMS, BASINS)}

LAYER_ALIASES = {"pipes": "reaches", "manholes": "nodes", "chambers": "nodes",
                 "W12_pipes": "reaches", "W12_nodes": "nodes",
                 "W12_reaches": "reaches", "W12_manholes": "nodes"}


def _spec(layer_name: str) -> LayerSpec:
    key = layer_name if layer_name in LAYERS else LAYER_ALIASES.get(layer_name, layer_name)
    spec = LAYERS.get(key)
    if spec is None:
        raise ContractError(
            f"no contract for layer '{layer_name}'. Known layers: "
            + ", ".join(sorted(LAYERS)) + ". Add a LayerSpec before publishing it - an "
            "unspecified layer is one nothing will ever check, and inventing a schema at the "
            "point of writing is EXCLUDED ('a per-stage schema').")
    return spec


# ======================================================================================
# THE IMPORT-TIME GUARDS. These run when the module loads, and the module refuses to load
# if either fails. A rule enforced by a README is a rule nobody enforces.
# ======================================================================================

def _assert_shp_safe() -> None:
    """FIX 4: no field name over 10 characters, anywhere, on any layer.

    The ESRI DBF truncates at 10 and a truncated name is a field a check cannot find, which
    philosophy sec 8 makes blocking. Enforcing it here rather than warning at write time
    means every published layer round-trips through a shapefile without losing a name - so
    the CAD mirror and the audited GeoPackage carry identical schemas, and the whole class
    of bug where a design that was correct in memory fails its own audit disappears."""
    bad = [(s.name, f.name, len(f.name))
           for s in LAYERS.values() for f in s.fields if len(f.name) > SHP_FIELD_MAXLEN]
    if bad:
        raise ContractError(
            f"{len(bad)} field name(s) exceed the {SHP_FIELD_MAXLEN}-character DBF limit and "
            "would be silently renamed on the way into a shapefile:\n  "
            + "\n  ".join(f"{ly}.{fl} ({n} chars)" for ly, fl, n in bad)
            + "\nRename the FIELD. Publishing to GeoPackage only is not a fix - the CAD "
              "mirror is a deliverable too, and a name that differs between the two formats "
              "is a name no check can rely on.")


def _assert_no_banned() -> None:
    """A spec may not declare a field this contract has banned by name."""
    bad = [(s.name, f.name) for s in LAYERS.values() for f in s.fields
           if f.name in BANNED_FIELDS]
    if bad:
        raise ContractError("banned field names declared in a LayerSpec: "
                            + ", ".join(f"{ly}.{fl}" for ly, fl in bad))


def _assert_refs_resolve() -> None:
    """Every declared cross-layer reference must point at a layer and a key that exist."""
    bad = []
    for s in LAYERS.values():
        for col, target, tkey in s.refs:
            if s.field(col) is None:
                bad.append(f"{s.name}.{col} is referenced but not declared")
            t = LAYERS.get(target)
            if t is None:
                bad.append(f"{s.name}.{col} -> unknown layer '{target}'")
            elif t.field(tkey) is None:
                bad.append(f"{s.name}.{col} -> {target}.{tkey}, which does not exist")
    if bad:
        raise ContractError("broken references in the layer specs:\n  " + "\n  ".join(bad))


_assert_shp_safe()
_assert_no_banned()
_assert_refs_resolve()


# ======================================================================================
# validate() - the gate. Every stage calls it before it writes and after it reads.
# ======================================================================================

def _kind(s: pd.Series) -> str:
    return "num" if pd.api.types.is_numeric_dtype(s) else "str"


def _missing_mask(s: pd.Series, dtype: str = "str"):
    if dtype in ("int", "float") or pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").isna()
    return s.isna() | (s.astype(str).str.strip() == "")


def _blank(s: pd.Series):
    return s.isna() | (s.astype(str).str.strip() == "")


def _fmt_rows(idx, n: int = 5) -> str:
    head = list(idx[:n])
    return ", ".join(str(i) for i in head) + (" ..." if len(idx) > n else "")


def validate(gdf, layer_name: str, *, stage: str = "", strict: bool = True,
             allow_extra: bool = True):
    """Check a layer against its spec. Raise ContractError listing EVERY problem at once.

    Returns the frame, so it composes: `gdf = validate(gdf, "reaches", stage="s5")`.

    Why it RAISES rather than warns: a missing field is not a slightly incomplete layer, it
    is an UNAUDITABLE one, and philosophy sec 8 makes any check that cannot run blocking.
    Thirteen of W10's 22 checks died exactly there. Failing at the writing stage costs a
    minute; failing at the audit costs a rebuild.

    `strict=False` relaxes the VALUE checks (enums, ranges, cross-field consistency) but
    never the missing-field check, because that is the one nothing downstream can recover
    from. Use it while a stage is still filling a layer in; never to publish.
    """
    spec = _spec(layer_name)

    if not isinstance(gdf, pd.DataFrame):
        raise ContractError(f"layer '{spec.name}': expected a (Geo)DataFrame, got "
                            f"{type(gdf).__name__}")

    problems: List[str] = []
    cols = set(gdf.columns)
    n = len(gdf)

    # ---- 1. missing required fields. The headline, and the only check strict=False keeps.
    missing = [f for f in spec.fields if f.required and f.name not in cols]
    if missing:
        w = max(len(f.name) for f in missing)
        lines = [f"  {f.name:<{w}}  {f.dtype:<5} {f.units:<6} {f.why.split('.')[0][:76]}"
                 + (f"   -> check {f.audit}" if f.audit else "") for f in missing]
        problems.append("MISSING REQUIRED FIELDS (a missing field cannot be checked, and a "
                        "check that cannot run is a FAILURE, not a blank):\n" + "\n".join(lines))

    # ---- 2. banned names. A name that means two things is worse than a missing one.
    banned = sorted(cols & set(BANNED_FIELDS))
    if banned:
        problems.append("BANNED FIELD NAMES:\n" + "\n".join(
            f"  {b}: {BANNED_FIELDS[b]}" for b in banned))

    # ---- 2b. anything that WOULD be truncated by a DBF, including an undeclared extra
    long_extra = sorted(c for c in cols
                        if c != "geometry" and len(str(c)) > SHP_FIELD_MAXLEN)
    if long_extra:
        problems.append(
            f"FIELD NAMES OVER {SHP_FIELD_MAXLEN} CHARACTERS: {long_extra}. The DBF "
            "truncates them and the shapefile mirror then carries different names from the "
            "GeoPackage, so no check can rely on either.")

    if not allow_extra:
        extra = sorted(cols - set(spec.names) - set(BANNED_FIELDS) - {"geometry"})
        if extra:
            problems.append("UNDECLARED FIELDS (declare them in the LayerSpec with a `why`, "
                            "or drop them - an undeclared field is one nothing checks and "
                            "nothing prints): " + ", ".join(extra))

    present = [f for f in spec.fields if f.name in cols]

    if strict and n:
        # ---- 3. nulls in required fields
        for f in present:
            if not f.required or f.blank_ok:
                continue
            m = _missing_mask(gdf[f.name], f.dtype)
            if m.any():
                problems.append(f"NULL in required field {f.name}: {int(m.sum()):,} of "
                                f"{n:,} rows (rows {_fmt_rows(gdf.index[m])}). "
                                f"{f.why.split('.')[0]}")

        # ---- 4. enum membership
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
                        hint = ("  <- these are the UNDERSCORE forms. A tier-keyed check "
                                "does floor.get(tier) and skips an unrecognised tier "
                                "SILENTLY, so this would pass an audit UNCHECKED. Use: "
                                + ", ".join(TIER_ALIASES[v.lower()] for v in alias))
                problems.append(f"ILLEGAL VALUE in {f.name}: {int(bad.sum()):,} rows carry "
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
            problems.append(f"layer '{spec.name}' must be a GeoDataFrame with {spec.geom} "
                            "geometry")
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
                    problems.append(
                        f"MULTIPART GEOMETRY on '{spec.name}': {sorted(multi)}. A graph "
                        "builder that reads geoms[0] DROPS every other part, so the "
                        "component count would describe a network only half read - and the "
                        "check that exists to catch silent corruption is the one corrupted. "
                        "Explode in the stage that reads it and account for the extra parts "
                        "in a Funnel: a part silently discarded is a reach nobody designed.")
                other = gt - {spec.geom} - multi
                if other:
                    problems.append(f"layer '{spec.name}' holds geometry {sorted(other)}, "
                                    f"expected {spec.geom}")
                if gdf.geometry.isna().any() or (~gdf.geometry.is_valid).any():
                    problems.append(f"layer '{spec.name}' has null or invalid geometry")

                # ---- FIX 7: every published length agrees with its own geometry.
                if spec.geom in ("LineString", "Polygon") and "LEN_M" in cols and not multi:
                    claim = pd.to_numeric(gdf["LEN_M"], errors="coerce")
                    real = gdf.geometry.length
                    d = (claim - real).abs()
                    bad = (d > LEN_TOL_M) & claim.notna()
                    if bad.any():
                        problems.append(
                            f"LEN_M disagrees with its own geometry on {int(bad.sum()):,} "
                            f"rows by more than {LEN_TOL_M} m, worst {d[bad].max():.3f} m "
                            f"(rows {_fmt_rows(gdf.index[bad])}). Every published length "
                            "reads the FIELD, not the line; if the two have parted, the "
                            "schedule and the drawing are describing different pipes.")
                if spec.geom == "Polygon" and "AREA_M2" in cols and not multi:
                    claim = pd.to_numeric(gdf["AREA_M2"], errors="coerce")
                    real = gdf.geometry.area
                    bad = ((claim - real).abs() > (0.001 * real.abs() + 1.0)) & claim.notna()
                    if bad.any():
                        problems.append(f"AREA_M2 disagrees with its own geometry on "
                                        f"{int(bad.sum()):,} rows")

    if problems:
        head = (f"CONTRACT VIOLATION - layer '{spec.name}', {n:,} rows"
                + (f", written by {stage}" if stage else "") + f"\n{spec.purpose}\n")
        tail = ("\n\nFix this in the stage that WRITES the layer. Relaxing a field a check "
                "needs is not a fix; it converts a visible failure into an invisible one.")
        raise ContractError(head + "\n" + "\n\n".join(problems) + tail)
    return gdf


def constant_column_problem(gdf, col: str, mask=None, *, what: str = "",
                            min_rows: int = VARY_MIN_ROWS) -> Optional[str]:
    """One line describing a column that is CONSTANT where it should VARY, or None.

    INHERITANCE ROW 22, and it is the only defect class in this project no result-based check
    could ever find: `ANGLE_DEG = 90` was published on all 3,290 crossings and called a
    declaration, while the measured minimum was 0.00 deg with 23 crossings under 45. The
    layer was internally consistent, every range check passed, and the number was invented.

    `mask` restricts the test to the rows where the quantity is supposed to exist - the drop
    reasons on the chambers that actually drop, the failure reasons on the plots that
    actually fail. Constancy over a filtered set is the evidence; constancy over a column
    that is mostly blank is not.

    `min_rows` is VARY_MIN_ROWS, a STRUCTURAL threshold: below it, one repeated value is a
    small sample rather than a fabrication, and calling a five-drop test network a fabrication
    would train everyone to switch the check off.
    """
    if col not in gdf.columns:
        return None
    s = gdf[col]
    if mask is not None:
        s = s[mask]
    s = s[~_blank(s)] if not pd.api.types.is_numeric_dtype(s) else s[s.notna()]
    n = len(s)
    if n < min_rows:
        return None
    vals = set(s.astype(str))
    if len(vals) > 1:
        return None
    return (f"{col} is CONSTANT at {list(vals)[0]!r} across all {n:,} rows where it applies"
            + (f" ({what})" if what else "")
            + ". A published column that is constant where it should vary is a FABRICATION, "
              "not a declaration - a crossing angle was published as 90 deg on 3,290 rows "
              "here and the measured minimum was 0.00. If every one of these genuinely has "
              "the same value, the computation is not reading its own input.")


def _name_problems(gdf, spec: LayerSpec, cols) -> List[str]:
    """NAME / TOWN / SUBNET / TIER must agree with each other and with the grammar.

    A name that says one thing and a column that says another is a layer nobody can filter:
    the drawing groups by NAME, the schedule groups by SUBNET, and the two then describe
    different networks. Blank rows are skipped - naming runs after connectivity is known
    (an element outside a town takes the letter of the first town DOWNSTREAM of it), so a
    layer published before it is legitimately unnamed. assert_named() is what requires the
    work to have actually happened."""
    out: List[str] = []
    if "NAME" not in cols:
        return out

    def _norm(col):
        """A blank is a blank whichever format it came back from. A shapefile DBF returns
        None where the GeoPackage stored an empty string, and `astype(str)` would turn that
        into the literal 'nan' - which then 'disagrees' with a station's legitimately blank
        SUBNET. The publish round trip in _self_test() caught exactly that."""
        s = gdf[col]
        return s.where(~_blank(s), "").astype(str).str.strip()

    nm = _norm("NAME")
    named = ~_blank(gdf["NAME"])
    if not named.any():
        return out

    parsed = {v: parse_name(v) for v in set(nm[named])}
    bad = [v for v in sorted(parsed) if parsed[v] is None]
    if bad:
        out.append(
            f"{len(bad):,} NAME values do not fit the grammar (e.g. {bad[:4]}). The forms "
            "are I-S03 / I-S03-SM-M012 / I-S03-C012 / I-PMP02 / I-P02 - town letter, "
            "subnetwork, tier, element, zero-padded. Build them with concept_name(); a "
            "stored name that cannot be parsed is a label, not an identifier.")

    dup = nm[named].duplicated(keep=False)
    if dup.any():
        out.append(f"DUPLICATE NAME on {int(dup.sum()):,} rows of '{spec.name}' "
                   f"({sorted(set(nm[named][dup]))[:4]}). A name that identifies two things "
                   "identifies neither, and the drawing and the schedule would each pick a "
                   "different one.")

    # The three comparisons below are VECTORISED and format ONE example, not one string per
    # bad row. On a 56,930-chamber layer whose TOWN column is stale, a list comprehension
    # would build 56,930 messages to print four of them.
    parseable = named & nm.map(lambda v: parsed.get(v) is not None)

    def _first(mask, a, b, alab):
        i = mask.idxmax()
        return f"{a[i]} vs {alab}={b[i]!r}"

    if "TOWN" in cols:
        t = _norm("TOWN")
        want = nm.map(lambda v: (parsed.get(v) or {}).get("town", ""))
        mism = parseable & (want != t)
        if mism.any():
            out.append(f"NAME and TOWN disagree on {int(mism.sum()):,} rows (e.g. "
                       f"{_first(mism, nm, t, 'TOWN')}). The town letter is IN the name; two "
                       "sources for it means one of them is stale after the next retown.")
    if "SUBNET" in cols:
        sn = _norm("SUBNET")
        want = nm.map(lambda v: (parsed.get(v) or {}).get("sub", ""))
        mism = parseable & (want != sn)
        if mism.any():
            out.append(
                f"NAME and SUBNET disagree on {int(mism.sum()):,} rows (e.g. "
                f"{_first(mism, nm, sn, 'SUBNET')}). A pump and its force main carry a BLANK "
                "subnet and a name with no S-token - a station is a SEAM between "
                "subnetworks, not a member of one - and every gravity element carries both.")
    if "TIER" in cols:
        tr = _norm("TIER").str.lower()
        is_mh = nm.map(lambda v: (parsed.get(v) or {}).get("kind", "") == "manhole")
        want = nm.map(lambda v: (parsed.get(v) or {}).get("tier", ""))
        got = tr.map(lambda v: TIER_TOKEN.get(v, ""))
        mism = parseable & is_mh & (want != got)
        if mism.any():
            out.append(f"NAME and TIER disagree on {int(mism.sum()):,} chambers (e.g. "
                       f"{_first(mism, nm, tr, 'TIER')}). The tier token is in the name: "
                       f"{TIER_TOKEN}.")
    return out


def _cross_field(gdf, spec: LayerSpec, cols) -> List[str]:
    """Consistency rules BETWEEN fields of one row. Each is a rule an auditor cannot see,
    because an auditor recomputes from geometry and terrain rather than from the row - so a
    row that contradicts itself would sail past it."""
    out: List[str] = []

    def has(*c):
        return all(x in cols for x in c)

    # ---------------------------------------------------------------- naming, shared
    out += _name_problems(gdf, spec, cols)

    # ---------------------------------------------------------------- nodes
    if spec.name == "nodes":
        if has("GRD_M", "INV_M", "DEPTH_M"):
            d = (pd.to_numeric(gdf.GRD_M, errors="coerce")
                 - pd.to_numeric(gdf.INV_M, errors="coerce")
                 - pd.to_numeric(gdf.DEPTH_M, errors="coerce")).abs()
            if (d > 0.001).any():
                out.append(f"DEPTH_M != GRD_M - INV_M on {int((d > 0.001).sum()):,} nodes, "
                           f"worst {d[d > 0.001].max():.3f} m. A chamber schedule and a pipe "
                           "layer that disagree on depth is how a design gets built to the "
                           "wrong invert.")

        # FIX 5: IS_OUTFALL is DERIVED, never asserted - so it must agree with the graph.
        if has("IS_OUTFALL", "DS_NODE"):
            claimed = pd.to_numeric(gdf.IS_OUTFALL, errors="coerce").fillna(-1) == 1
            terminal = _blank(gdf.DS_NODE)
            bad = claimed != terminal
            if bad.any():
                out.append(
                    f"IS_OUTFALL contradicts DS_NODE on {int(bad.sum()):,} nodes "
                    f"(rows {_fmt_rows(gdf.index[bad])}). An outfall is a node with NO "
                    "OUTGOING EDGE - it is a topological fact and it is DERIVED in "
                    "to_nodes_gdf(), never asserted. A design that has to be told where its "
                    "outfalls are does not know where its flow goes.")

        if has("DS_NODE", "NODE_KIND"):
            term = _blank(gdf.DS_NODE)
            bad = term & ~gdf.NODE_KIND.astype(str).isin(["outfall", "station", "tie"])
            if bad.any():
                out.append(f"{int(bad.sum()):,} nodes have no DS_NODE but are not an "
                           "outfall, a station or a tie. A terminal node is where flow LEAVES "
                           "the network; anything else with no downstream is a dead end the "
                           "design forgot.")

        if has("N_OUT", "DS_NODE"):
            nout = pd.to_numeric(gdf.N_OUT, errors="coerce").fillna(-1)
            term = _blank(gdf.DS_NODE)
            bad = (term & (nout != 0)) | ((~term) & (nout != 1))
            if bad.any():
                out.append(f"N_OUT contradicts DS_NODE on {int(bad.sum()):,} nodes: a node "
                           "with a downstream has exactly one outgoing reach, a terminal has "
                           "none.")

        if has("PAST_CAP", "CAP_EXIT"):
            pc = pd.to_numeric(gdf.PAST_CAP, errors="coerce").fillna(0) == 1
            if (pc & _blank(gdf.CAP_EXIT)).any():
                out.append(f"{int((pc & _blank(gdf.CAP_EXIT)).sum()):,} chambers past the "
                           f"{C.MAX_COVER:g} m cap with no exit named (philosophy sec 5 gives "
                           "exactly two, and both are bounded by distance AND by depth).")

        # G203-p30: backdrop above 0.60 m, vortex shaft above 2.0 m.
        if has("DROP_M", "DROP_TYPE"):
            d = pd.to_numeric(gdf.DROP_M, errors="coerce").fillna(0.0)
            t = gdf.DROP_TYPE.astype(str).str.lower()
            bad = (d > C.DROP_TRIGGER + 1e-9) & (t == "none")
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers drop more than {C.DROP_TRIGGER} m "
                           "with DROP_TYPE='none'. G203-p30 requires a backdrop above that, "
                           "external and ramped.")
            bad = (d > C.BACKDROP_MAX + 1e-9) & (t != "vortex")
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers drop more than {C.BACKDROP_MAX} m "
                           "without a vortex shaft (G203-p30). The as-built has 37 of these "
                           "BUILT AS BACKDROPS; that is the calibration reference being "
                           "wrong, not a precedent.")
        if has("DROP_M", "VORTEX"):
            d = pd.to_numeric(gdf.DROP_M, errors="coerce").fillna(0.0)
            v = pd.to_numeric(gdf.VORTEX, errors="coerce").fillna(0) == 1
            bad = v != (d > C.BACKDROP_MAX + 1e-9)
            if bad.any():
                out.append(f"VORTEX disagrees with DROP_M on {int(bad.sum()):,} chambers "
                           f"(the trigger is {C.BACKDROP_MAX} m, G203-p30). The vortex count "
                           "is the diagnostic for a tree that is not following the ground, "
                           "so it must be exactly right.")
        # CONCEPT RULE 1: every drop carries the reason it exists.
        if has("DROP_M", "DROP_WHY"):
            d = pd.to_numeric(gdf.DROP_M, errors="coerce").fillna(0.0)
            drops = d > 0.0
            noreason = drops & _blank(gdf.DROP_WHY)
            if noreason.any():
                out.append(
                    f"{int(noreason.sum()):,} chambers drop with no DROP_WHY (rows "
                    f"{_fmt_rows(gdf.index[noreason])}). Concept rule 1: the laid slope is a "
                    "clamp and the surplus fall is taken as a DROP - so a drop is a decision "
                    f"and it names itself. Allowed: {[v for v in DROP_WHY if v]}.")
            spurious = (~drops) & (~_blank(gdf.DROP_WHY))
            if spurious.any():
                out.append(f"{int(spurious.sum()):,} chambers carry a DROP_WHY with DROP_M = "
                           "0 - a reason for a drop that is not there.")
            prob = constant_column_problem(
                gdf, "DROP_WHY", drops,
                what="every drop on this network was given the same reason")
            if prob:
                out.append(prob + " Four causes are declared - a velocity cap, a tier step, "
                           "a cover recovery and an obstruction - and a network large enough "
                           "to have this many drops meets more than one of them.")

        # CONCEPT RULE 2: the subnetwork joins the main pipe at its LOWEST POINT, and where
        # it cannot, the distance from that low point is recorded.
        if has("JOIN_MAIN", "JOIN_OFF_M"):
            jm = pd.to_numeric(gdf.JOIN_MAIN, errors="coerce").fillna(0) == 1
            off = pd.to_numeric(gdf.JOIN_OFF_M, errors="coerce").fillna(0.0)
            bad = (~jm) & (off > 0)
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers carry a JOIN_OFF_M without "
                           "JOIN_MAIN = 1 - an offset from a low point they do not join at.")
        if has("JOIN_OFF_M", "JOIN_WHY"):
            off = pd.to_numeric(gdf.JOIN_OFF_M, errors="coerce").fillna(0.0)
            bad = (off > 0) & _blank(gdf.JOIN_WHY)
            if bad.any():
                out.append(
                    f"{int(bad.sum()):,} subnetworks join the main pipe away from their own "
                    f"low point (worst {off[bad].max():,.0f} m) with no JOIN_WHY. Concept "
                    "rule 2 allows the join to move when there is no street at the low point "
                    "- it requires the distance AND the reason. W11b had 42 components "
                    "discharging with more than half their catchment BELOW the outlet, "
                    "389.5 km of it, and nothing on the layer said so.")
            bad = (off <= 0) & (~_blank(gdf.JOIN_WHY))
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers explain an offset of zero.")

        if has("MH_DIA", "DROP_TYPE"):
            dia = pd.to_numeric(gdf.MH_DIA, errors="coerce")
            internal = gdf.DROP_TYPE.astype(str).str.lower() == "backdrop"
            bad = internal & dia.notna() & (dia < C.MH_DIA_INTERNAL_BACKDROP - 1e-9)
            # reported, not blocking: G203-p30 bans an INTERNAL backdrop below 1.5 m and the
            # contract requires backdrops external, so this only bites if a stage builds one
            # internally. Kept because "shall only be used ... where external connections are
            # not practicable" means it will happen at a tie-in.
            if bad.any():
                out.append(f"{int(bad.sum()):,} chambers under "
                           f"{C.MH_DIA_INTERNAL_BACKDROP} m diameter carry a backdrop. "
                           "G203-p30 permits an INTERNAL backdrop only on chambers of at "
                           "least that diameter; if these are external, say so in MH_MAT.")

    # ---------------------------------------------------------------- reaches
    if spec.name == "reaches":
        # FIX 3: DN must be a MEMBER of the series, not merely inside a range.
        if has("DN"):
            dn = pd.to_numeric(gdf.DN, errors="coerce")
            bad = dn.notna() & ~dn.astype("Int64").isin(list(C.DN_SERIES))
            if bad.any():
                out.append(
                    f"{int(bad.sum()):,} reaches carry a DN that is not in "
                    f"criteria.DN_SERIES ({sorted(set(dn[bad].dropna().astype(int)))[:8]}). "
                    "The series is the sizes G203 itself tabulates - membership is checked, "
                    "not a range, so the layer and hydra.size_pipe() cannot disagree about "
                    "what sizes exist.")

        if has("SLOPE_LAID", "SLOPE_MIN"):
            bad = (pd.to_numeric(gdf.SLOPE_LAID, errors="coerce")
                   < pd.to_numeric(gdf.SLOPE_MIN, errors="coerce") - 1e-9)
            if bad.any():
                out.append(f"SLOPE_LAID below SLOPE_MIN on {int(bad.sum()):,} reaches - the "
                           "row contradicts itself before any auditor runs (G203-p27: the "
                           "steeper of the two routes governs).")

        if has("SLOPE_LAID"):
            step = C.SLOPE_STEP * 100.0
            s = pd.to_numeric(gdf.SLOPE_LAID, errors="coerce")
            off = (((s / step) - (s / step).round()).abs() > 1e-6) & s.notna()
            if off.any():
                out.append(f"SLOPE_LAID off the {step:g} % step on {int(off.sum()):,} "
                           "reaches (P1: pipes are laid at a round gradient so the number on "
                           "the drawing is the number the levels came from). If rounding a "
                           "run created a pumping station, relax the rounding ON THAT RUN and "
                           "say so - P1 is never bought at the price of a station.")

        if has("INV_UP", "INV_DN", "LEN_M", "SLOPE_LAID"):
            fall = (pd.to_numeric(gdf.INV_UP, errors="coerce")
                    - pd.to_numeric(gdf.INV_DN, errors="coerce"))
            want = (pd.to_numeric(gdf.LEN_M, errors="coerce")
                    * pd.to_numeric(gdf.SLOPE_LAID, errors="coerce") / 100.0)
            bad = ((fall - want).abs() > C.LAY_TOLERANCE_M + 1e-3) & fall.notna() & want.notna()
            if bad.any():
                out.append(f"INV_UP - INV_DN disagrees with LEN_M x SLOPE_LAID by more than "
                           f"the {C.LAY_TOLERANCE_M * 1000:.0f} mm laying tolerance on "
                           f"{int(bad.sum()):,} reaches (G203-p29). The levels are then "
                           "decoration.")
            rev = fall < -C.LAY_TOLERANCE_M
            if rev.any():
                out.append(f"{int(rev.sum()):,} reaches have a REVERSE GRADIENT - the "
                           "downstream invert is above the upstream one by more than the "
                           "laying tolerance (G203-p29: 'combination of such deviation shall "
                           "not create a reverse gradient').")

        # FIX 1: cover is cover() and nothing else, on the reach's OWN outside diameter.
        for depth_c, cov_c in (("US_DEPTH", "COVER_US"), ("DS_DEPTH", "COVER_DN")):
            if has("DN", depth_c, cov_c):
                dnv = pd.to_numeric(gdf.DN, errors="coerce")
                want = pd.to_numeric(gdf[depth_c], errors="coerce") - (
                    dnv / 1000.0 + C.WALL_ALLOW)
                got = pd.to_numeric(gdf[cov_c], errors="coerce")
                bad = ((got - want).abs() > 0.001) & got.notna() & want.notna()
                if bad.any():
                    out.append(
                        f"{cov_c} != {depth_c} - (DN/1000 + criteria.WALL_ALLOW) on "
                        f"{int(bad.sum()):,} reaches, worst {(got - want).abs().max():.3f} m. "
                        "That subtraction is criteria.cover() and it is THE ONLY definition. "
                        "W11a carried two allowances for this one quantity and a blocking "
                        "cover check failed on every reach; W10 used a hardcoded 0.30 m "
                        "regardless of diameter and shipped 45.92 km below minimum.")

        # FIX 2: the d/D limit is the criteria's, at the criteria's threshold.
        if has("DN", "DOD_PK"):
            dnv = pd.to_numeric(gdf.DN, errors="coerce")
            lim = dnv.map(lambda d: C.dod_limit(int(d)) if pd.notna(d) else float("nan"))
            got = pd.to_numeric(gdf.DOD_PK, errors="coerce")
            bad = got.notna() & lim.notna() & (got > lim + 1e-9)
            if bad.any():
                out.append(
                    f"{int(bad.sum()):,} reaches exceed the G203-p27 Table 10 depth of flow "
                    f"for their own diameter (0.65 up to DN350, 0.50 above), worst "
                    f"{got[bad].max():.3f}. W10 shipped 5 surcharged reaches and 66 over the "
                    "limit; W11a shipped 168 because the diameter series stopped at DN1200.")

        # QPK_LS must be reproducible from its own row: sanitary peaked, infiltration not.
        if has("QADF_M3D", "PF", "QINF_LS", "QPK_LS"):
            want = (pd.to_numeric(gdf.QADF_M3D, errors="coerce") * 1000.0 / 86400.0
                    * pd.to_numeric(gdf.PF, errors="coerce")
                    + pd.to_numeric(gdf.QINF_LS, errors="coerce"))
            got = pd.to_numeric(gdf.QPK_LS, errors="coerce")
            bad = ((got - want).abs() > (0.01 * want.abs() + 0.01)) & got.notna() & want.notna()
            if bad.any():
                out.append(f"QPK_LS != QADF_M3D x PF + QINF_LS on {int(bad.sum()):,} reaches. "
                           "Infiltration is UNPEAKED (G201-p72), so the peak flow must be "
                           "reproducible from its own row.")

        if has("PF_METH", "PF"):
            held = gdf.PF_METH.astype(str).str.lower() == "held"
            bad = held & (pd.to_numeric(gdf.PF, errors="coerce").fillna(1.0) != 1.0)
            if bad.any():
                out.append(f"{int(bad.sum()):,} reaches carry PF_METH='held' with a peak "
                           "factor other than 1.0. 'held' means G201 prescribes no formula "
                           "below 100 properties - it is not a label for a number somebody "
                           "picked.")

        if has("TAU_PA"):
            t = pd.to_numeric(gdf.TAU_PA, errors="coerce")
            bad = t.notna() & (t != C.TAU_PA)
            if bad.any():
                out.append(f"{int(bad.sum()):,} reaches were checked at a tractive stress "
                           f"other than the design {C.TAU_PA:g} Pa ({sorted(set(t[bad]))[:5]}). "
                           "A sensitivity run is a WHOLE RUN with a different Criteria object, "
                           "not a mixture inside one layer.")

        if has("CLEAN_BY"):
            neither = gdf.CLEAN_BY.astype(str).str.lower() == "neither"
            if neither.any():
                out.append(f"{int(neither.sum()):,} reaches satisfy NEITHER self-cleansing "
                           "route (H5). G203-p27 offers two alternatives and the steeper "
                           "governs; a reach meeting neither will silt, and the resolution is "
                           "a steeper gradient, a smaller pipe or a station - never a note.")

        if has("PAST_CAP", "CAP_EXIT"):
            pc = pd.to_numeric(gdf.PAST_CAP, errors="coerce").fillna(0) == 1
            # _blank(), NOT astype(str) == "": a shapefile DBF returns None where
            # the GeoPackage stored an empty string, so a string comparison sees
            # "None" and reports a justification that is not there. Caught by the
            # publish round-trip in _self_test(), which is what that test is for.
            noex = _blank(gdf.CAP_EXIT)
            if (pc & noex).any():
                out.append(f"{int((pc & noex).sum()):,} reaches PAST_CAP=1 with no CAP_EXIT. "
                           "Philosophy sec 5 gives exactly two exits - cover recovers within "
                           "500 m, or the run reaches the outfall within 1,000 m. Neither "
                           "means A STATION, not a flag.")
            if ((~pc) & (~noex)).any():
                out.append(f"{int(((~pc) & (~noex)).sum()):,} reaches carry a CAP_EXIT with "
                           "PAST_CAP=0 - a justification for a breach that is not there.")

        if has("CAP_EXIT", "CAP_LEN_M"):
            ex = gdf.CAP_EXIT.fillna("").astype(str).str.strip()
            L = pd.to_numeric(gdf.CAP_LEN_M, errors="coerce").fillna(0.0)
            for token, bound in (("recovers_500m", 500.0), ("outfall_1000m", 1000.0)):
                bad = (ex == token) & (L > bound + 1e-6)
                if bad.any():
                    out.append(f"{int(bad.sum()):,} reaches claim '{token}' with CAP_LEN_M "
                               f"over {bound:g} m - the exit is bounded by that distance and "
                               "the row disproves itself (philosophy sec 5).")

        # FIX 6, half one: a reach that touches an obstacle must carry a CROSS_ID. The other
        # half - that the id resolves to a register row of the right OBSTACLE - needs both
        # layers and lives in assert_crossings_resolve().
        for col, what in (("ON_DUAL_M", "a dual carriageway"), ("ON_WADI_M", "wadi ground")):
            if has(col, "CROSS_ID"):
                on = pd.to_numeric(gdf[col], errors="coerce").fillna(0) > 0
                uns = _blank(gdf.CROSS_ID)
                if (on & uns).any():
                    out.append(
                        f"{int((on & uns).sum()):,} reaches touch {what} with no CROSS_ID. "
                        "W10 shipped 47 unscheduled crossings. A crossing is legal only as a "
                        "SCHEDULED, near-perpendicular one (H1/H1a); an unscheduled contact "
                        "is a pipe in a place it may not be.")

        if has("TIE_TYPE"):
            bad = gdf.TIE_TYPE.astype(str).str.lower() == "invert"
            if bad.any():
                out.append(f"{int(bad.sum()):,} tie-ins made INVERT to invert. H14: tie "
                           "SOFFIT to soffit - an existing structure's invert is fixed and "
                           "the design yields to it.")

        # materials: G203-p22 Table 6 by application AND p23 Table 7 by product, together.
        if has("TIER", "DN", "MATERIAL"):
            hits = []
            for t, d, m in zip(gdf.TIER, pd.to_numeric(gdf.DN, errors="coerce"), gdf.MATERIAL):
                if pd.isna(d):
                    continue
                try:
                    ok = C.materials_allowed(str(t), int(d))
                except Exception:
                    continue                       # the TIER enum check already reported it
                if str(m) not in ok:
                    hits.append(f"{t} DN{int(d)} = {m!r}, permitted {list(ok)}")
            if hits:
                out.append(f"{len(hits):,} reaches carry a material G203 does not permit for "
                           f"their tier and size - e.g. {hits[0]}. G203-p22 Table 6 is by "
                           "APPLICATION and p23 Table 7 by PRODUCT, and both are in force: "
                           "PVC-U is a permitted product to OD315 but a permitted MAIN SEWER "
                           "only to 250 mm.")

        # the terrain-first block: the three fields must agree with each other.
        if has("GND_FALL", "AGN_GRADE"):
            gf = pd.to_numeric(gdf.GND_FALL, errors="coerce")
            ag = pd.to_numeric(gdf.AGN_GRADE, errors="coerce").fillna(-1) == 1
            want = gf < -C.ADVERSE_MIN_M
            bad = (ag != want) & gf.notna()
            if bad.any():
                out.append(f"AGN_GRADE contradicts GND_FALL on {int(bad.sum()):,} reaches. "
                           f"A reach drains against the ground when GND_FALL < "
                           f"-{C.ADVERSE_MIN_M:g} m (criteria.ADVERSE_MIN_M). This is the "
                           "headline number the whole iteration turns on; it cannot be "
                           "computed two ways.")
        if has("GND_FALL", "RISE_M"):
            gf = pd.to_numeric(gdf.GND_FALL, errors="coerce")
            want = (-gf).clip(lower=0.0)
            got = pd.to_numeric(gdf.RISE_M, errors="coerce")
            bad = ((got - want).abs() > 0.001) & got.notna() & want.notna()
            if bad.any():
                out.append(f"RISE_M != max(0, -GND_FALL) on {int(bad.sum()):,} reaches.")

    # ---------------------------------------------------------------- provenance, shared
    if spec.name in ("reaches", "nodes", "corridors", "connections", "crossings",
                     "streams", "basins"):
        if has("SRC", "CONFIDENCE"):
            for src, ceiling in SRC_CONFIDENCE_CEILING.items():
                m = (gdf.SRC.astype(str) == src) & gdf.CONFIDENCE.astype(str).map(
                    lambda c: _CONF_RANK.get(c, 99) < _CONF_RANK[ceiling])
                if m.any():
                    out.append(f"{int(m.sum()):,} rows grade SRC='{src}' better than "
                               f"'{ceiling}'. Provenance is carried to the end and NEVER "
                               "laundered (P6): a cadastral reserve on bare desert does not "
                               "become an observed street because a pipe was laid on it.")

    # ---------------------------------------------------------------- connections
    if spec.name == "connections":
        if has("OUT_NODE", "WHY"):
            unassigned = _missing_mask(gdf.OUT_NODE, "str")
            if (unassigned & _blank(gdf.WHY)).any():
                out.append(f"{int((unassigned & _blank(gdf.WHY)).sum()):,} load units have no "
                           "OUT_NODE and no WHY. W10 lost 1,233 m3/d (1.7 %) exactly this "
                           "way - assigned to one chamber, or LISTED BY NAME.")
        if has("OUT_NODE", "SYSTEM"):
            unassigned = _missing_mask(gdf.OUT_NODE, "str")
            central = gdf.SYSTEM.astype(str) == "central"
            if (unassigned & central).any():
                out.append(f"{int((unassigned & central).sum()):,} load units are marked "
                           "SYSTEM='central' with no chamber to enter at. Say which system "
                           "serves them, or the plot is silently unserved.")

        # CONCEPT RULE 5 and RULE 7: a plot that cannot connect is named, with its size.
        if has("CAN_CONN", "CONN_WHY"):
            cc = pd.to_numeric(gdf.CAN_CONN, errors="coerce").fillna(-1)
            cannot = cc == 0
            bad = cannot & _blank(gdf.CONN_WHY)
            if bad.any():
                out.append(
                    f"{int(bad.sum()):,} plots are marked CAN_CONN = 0 with no CONN_WHY "
                    f"(rows {_fmt_rows(gdf.index[bad])}). FLAG, DO NOT SOLVE means named "
                    "with its reason and its size - an unexplained count is the same "
                    "unusable finding as W11b's '5,521 plots cannot drain'.")
            bad = (cc == 1) & (~_blank(gdf.CONN_WHY))
            if bad.any():
                out.append(f"{int(bad.sum()):,} plots that CAN connect carry a reason why "
                           "they cannot.")
            prob = constant_column_problem(
                gdf, "CONN_WHY", cannot,
                what="every plot that cannot connect was given the same reason")
            if prob:
                out.append(prob)
        if has("CAN_CONN", "CONN_NEED"):
            cc = pd.to_numeric(gdf.CAN_CONN, errors="coerce").fillna(-1)
            need = pd.to_numeric(gdf.CONN_NEED, errors="coerce").fillna(0.0)
            bad = (cc == 1) & (need > 0.0)
            if bad.any():
                out.append(f"{int(bad.sum()):,} plots connect and still ask for "
                           f"{need[bad].max():.2f} m more depth. CONN_NEED is what it would "
                           "TAKE, so it is zero wherever nothing is needed.")
        if has("CAN_CONN", "CAN_DRAIN"):
            cc = pd.to_numeric(gdf.CAN_CONN, errors="coerce")
            cd = pd.to_numeric(gdf.CAN_DRAIN, errors="coerce")
            bad = cc.notna() & cd.notna() & (cc != cd)
            if bad.any():
                out.append(
                    f"CAN_CONN and CAN_DRAIN disagree on {int(bad.sum()):,} plots. They ask "
                    "the same question - can this plot reach the network on gravity - and "
                    "CAN_CONN is the concept-stage form that can actually be computed. Two "
                    "answers to one question is the defect that has cost this project most; "
                    "write CAN_DRAIN from CAN_CONN or stop writing it.")

    # ---------------------------------------------------------------- stations
    if spec.name == "stations":
        if has("ST_TYPE", "Q_DUTY_LS"):
            q = pd.to_numeric(gdf.Q_DUTY_LS, errors="coerce")
            want = q.map(lambda v: C.ps_type(v) if pd.notna(v) else None)
            bad = (gdf.ST_TYPE.astype(str) != want) & q.notna()
            if bad.any():
                out.append(f"ST_TYPE contradicts Q_DUTY_LS on {int(bad.sum()):,} stations. "
                           "G203-p40: Type 1 up to 100 l/s, Type 2 >100-300, Type 3 >300 - "
                           "the type sets the pump count AND the land band.")
        if has("Q_DUTY_LS"):
            zero = pd.to_numeric(gdf.Q_DUTY_LS, errors="coerce").fillna(0) <= 0
            if zero.any():
                out.append(f"{int(zero.sum()):,} stations have Q_DUTY_LS = 0. W11a published "
                           "226 of these. A station with no duty flow is LOCATED, not "
                           "designed: it has no pump, no rising main and no land band.")
        if has("ST_TYPE", "LAND_M2"):
            need = gdf.ST_TYPE.astype(str).map(
                lambda t: C.ps_land_m2(t)[0] if t in ("Type 1", "Type 2", "Type 3") else None)
            got = pd.to_numeric(gdf.LAND_M2, errors="coerce")
            bad = got.notna() & need.notna() & (got < need - 1e-6)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations reserve less land than the G203-p43 "
                           "Table 21 minimum for their type (50 / 200 / 900 m2, plus a 6 m "
                           "turning circle). A reservation the client cannot build in is "
                           "worse than none.")
        if has("WELL_M3", "WW_STARTS", "Q_DUTY_LS"):
            q = pd.to_numeric(gdf.Q_DUTY_LS, errors="coerce") / 1000.0
            st = pd.to_numeric(gdf.WW_STARTS, errors="coerce")
            want = C.WELL_K * q * (3600.0 / st)
            got = pd.to_numeric(gdf.WELL_M3, errors="coerce")
            bad = ((got - want).abs() > (0.05 * want.abs() + 0.05)) & got.notna() & want.notna()
            if bad.any():
                out.append(f"WELL_M3 != 0.25 x Q x (3600/starts) on {int(bad.sum()):,} "
                           "stations (G203-p48 sec 7.8). The volume, the duty and the start "
                           "rate are ONE equation; publishing them so they disagree means one "
                           "of the three was never computed.")
        if has("WW_STARTS"):
            st = pd.to_numeric(gdf.WW_STARTS, errors="coerce")
            bad = st.notna() & (st < C.WELL_STARTS_MIN)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations assume fewer than "
                           f"{C.WELL_STARTS_MIN:g} starts/h. G203-p48 sets that as the "
                           "MINIMUM for motors up to 30 kW; a lower rate buys a smaller wet "
                           "well by breaching the cycle rule.")
        # CONCEPT RULE 6: a station's POSITION IS CHOSEN, NOT TRIGGERED. These two fields are
        # the evidence that it was chosen, and W11b is the reason they are required.
        if has("N_SUBNET"):
            ns = pd.to_numeric(gdf.N_SUBNET, errors="coerce").fillna(-1)
            bad = ns == 0
            if bad.any():
                out.append(
                    f"{int(bad.sum()):,} stations have N_SUBNET = 0 - NOTHING DRAINS INTO "
                    f"THEM (rows {_fmt_rows(gdf.index[bad])}). 15 of W11b's 47 were like "
                    "this, and they were leftovers from a pass that could only ever ADD. "
                    "Anything a pass can add, a later pass must be able to TAKE AWAY, and "
                    "the stage publishes how many it removed (inheritance row 4).")
        if has("N_SUBNET", "CATCH_KM"):
            ns = pd.to_numeric(gdf.N_SUBNET, errors="coerce").fillna(0)
            ck = pd.to_numeric(gdf.CATCH_KM, errors="coerce").fillna(0.0)
            bad = (ns > 0) & (ck <= 0.0)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations claim upstream subnetworks and zero "
                           "captured network length. A station that captures no kilometres "
                           "cannot be scored against its lift, which is the whole of the "
                           "'position is chosen' test.")
            prob = constant_column_problem(gdf, "CATCH_KM", what="every station captures "
                                           "exactly the same length of network")
            if prob:
                out.append(prob)

        if has("GRD_M", "FLOOD_LV"):
            g = pd.to_numeric(gdf.GRD_M, errors="coerce")
            f_ = pd.to_numeric(gdf.FLOOD_LV, errors="coerce")
            bad = g.notna() & f_.notna() & (g < f_ + C.PS_FLOOR_ABOVE_FLOOD_M - 1e-6)
            if bad.any():
                out.append(f"{int(bad.sum()):,} stations sit less than "
                           f"{C.PS_FLOOR_ABOVE_FLOOD_M:g} m above the 1:{C.PS_FLOOD_ARI_YR}-yr "
                           "flood level (G203-p38 sec 7.2). The floor, the transformers and "
                           "the generator all sit above it - this is a SITING failure, and "
                           "the fix is the site, not the level.")

    # ---------------------------------------------------------------- rising mains
    if spec.name == "rising_mains":
        if has("V_DUTY_MS"):
            v = pd.to_numeric(gdf.V_DUTY_MS, errors="coerce")
            bad = v.notna() & (v > C.FM_V_MAX + 1e-9)
            if bad.any():
                out.append(f"{int(bad.sum()):,} rising mains over {C.FM_V_MAX:g} m/s. That is "
                           f"G203-p50; the {C.V_MAX:g} m/s is the GRAVITY maximum from p27 and "
                           "the two were conflated once already.")
        if has("V_MIN_MS"):
            v = pd.to_numeric(gdf.V_MIN_MS, errors="coerce")
            bad = v.notna() & (v < C.FM_V_MIN - 1e-9)
            if bad.any():
                out.append(f"{int(bad.sum()):,} rising mains fall below {C.FM_V_MIN:g} m/s at "
                           "the DESIGN MINIMUM flow (G203-p50 sec 8.1, with the p40 Table 16 "
                           "factors). That is where the floor is held, not at duty - sizing "
                           "on duty alone silts the main in year one.")

    # ---------------------------------------------------------------- packages
    if spec.name == "packages":
        if has("ONE_TREE"):
            bad = pd.to_numeric(gdf.ONE_TREE, errors="coerce").fillna(0) != 1
            if bad.any():
                out.append(f"{int(bad.sum()):,} packages are not one connected tree with one "
                           "outlet. That is a FAILED package, not a note.")

    # ---------------------------------------------------------------- streams
    if spec.name == "streams":
        if has("GND_FALL"):
            gf = pd.to_numeric(gdf.GND_FALL, errors="coerce")
            bad = gf.notna() & (gf < -0.001)
            if bad.any():
                out.append(f"{int(bad.sum()):,} streams have a NEGATIVE ground fall - the "
                           "flow direction was written the wrong way round. Water does not "
                           "run uphill; a pipe can be made to, a stream cannot. This is a bug "
                           "in the flow-direction derivation and everything built on it is "
                           "wrong.")
    return out


def assert_crossings_resolve(reaches=None, corridors=None, crossings=None) -> None:
    """FIX 6, in full: a CROSS_ID means nothing unless a REGISTER ROW backs it, and the row
    must name the obstacle the feature claims to cross.

    Three failures, all of which have happened on this project:
      * a reach on wadi ground with no CROSS_ID          (W10: 47 unscheduled crossings)
      * a CROSS_ID with no row behind it                 (nothing in W11a could catch this)
      * a row whose OBSTACLE is not what the reach crosses - a dual-carriageway crossing
        registered against a wadi row schedules the wrong consent from the wrong authority

    Call it after publishing the crossings register and before publishing the reaches."""
    if crossings is None:
        raise ContractError(
            "assert_crossings_resolve() was called with no crossings register. A design with "
            "no crossings publishes an EMPTY register (publish(..., allow_empty=True)) - it "
            "does not publish none, because 'no register' and 'no crossings' look identical "
            "afterwards and only one of them is a design decision.")
    if "CROSS_ID" not in crossings.columns:
        raise ContractError("the crossings register has no CROSS_ID column")
    # .fillna("") everywhere: a shapefile DBF returns None for an empty string, and
    # astype(str) would then turn a blank into the literal id "None" - which resolves to no
    # register row and reports a dangling crossing on a design that has none.
    known = set(crossings["CROSS_ID"].fillna("").astype(str).str.strip()) - {""}
    obst = {}
    if "OBSTACLE" in crossings.columns:
        obst = dict(zip(crossings["CROSS_ID"].fillna("").astype(str).str.strip(),
                        crossings["OBSTACLE"].fillna("").astype(str).str.strip()))

    problems: List[str] = []
    for name, gdf in (("reaches", reaches), ("corridors", corridors)):
        if gdf is None or "CROSS_ID" not in gdf.columns:
            continue
        ids = gdf["CROSS_ID"].fillna("").astype(str).str.strip()
        used = ids[ids != ""]
        dangling = sorted(set(used) - known)
        if dangling:
            problems.append(
                f"{name}: {len(dangling):,} CROSS_ID values resolve to NO register row "
                f"({dangling[:6]}). An id with no row behind it schedules nothing - it is "
                "the appearance of a crossings schedule without one.")
        # the obstacle the feature claims to cross must be the obstacle the row names
        for col, want in (("ON_DUAL_M", "dual"), ("ON_WADI_M", "wadi")):
            if col not in gdf.columns:
                continue
            touching = pd.to_numeric(gdf[col], errors="coerce").fillna(0) > 0
            bad = [i for i, t in zip(ids[touching], touching[touching])
                   if i in obst and obst[i] != want]
            if bad:
                problems.append(
                    f"{name}: {len(bad):,} features touch {want} ground but their register "
                    f"row names a different obstacle (e.g. {bad[0]} -> {obst[bad[0]]!r}). "
                    "The obstacle decides which authority's consent is needed - MoAFWR for a "
                    "wadi (G201-p85), the roads authority for a carriageway.")
    # a register row that nothing references is an unbuilt crossing, and also a finding
    if reaches is not None and "CROSS_ID" in reaches.columns:
        used = set(reaches["CROSS_ID"].fillna("").astype(str).str.strip()) - {""}
        if corridors is not None and "CROSS_ID" in corridors.columns:
            used |= set(corridors["CROSS_ID"].fillna("").astype(str).str.strip()) - {""}
        orphan = sorted(known - used)
        if orphan:
            problems.append(
                f"crossings: {len(orphan):,} register rows are referenced by nothing "
                f"({orphan[:6]}). Either the crossing was designed out and the row should go, "
                "or a reach that crosses lost its link - both are findings.")
    if problems:
        raise ContractError("CROSSINGS REGISTER DOES NOT RESOLVE:\n  " + "\n  ".join(problems))


def assert_named(gdf, layer_name: str, *, stage: str = "") -> None:
    """Every row on this layer is NAMED - the gate the FINAL publish calls.

    The LayerSpec makes NAME/TOWN/SUBNET `required` (the column must exist) and `blank_ok`
    (a row may be blank), because naming runs AFTER connectivity is known: an element outside
    a town takes the letter of the first town DOWNSTREAM of it, which is not knowable when a
    chamber is first minted. So the spec answers 'can this be checked?' and this answers 'was
    it actually done?'.

    Two mechanisms rather than one, deliberately. A single `blank_ok=False` would block every
    intermediate stage; a single gate with no column requirement would let a layer reach the
    audit with no naming column at all, and a check that cannot run is a failure."""
    spec = _spec(layer_name)
    if spec.field("NAME") is None:
        raise ContractError(f"layer '{spec.name}' has no NAME field to check - assert_named() "
                            "was pointed at a layer the naming rule does not cover.")
    problems = []
    for col in ("NAME", "TOWN"):
        if col not in gdf.columns:
            problems.append(f"no {col} column at all")
            continue
        blank = _blank(gdf[col])
        if blank.any():
            problems.append(f"{int(blank.sum()):,} of {len(gdf):,} rows have no {col} "
                            f"(rows {_fmt_rows(gdf.index[blank])})")
    # SUBNET is legitimately blank on a station and its force main - a station is a SEAM
    # between subnetworks, not a member of one - so it is required only where the grammar
    # says the name carries one.
    if "SUBNET" in gdf.columns and "NAME" in gdf.columns:
        want = gdf["NAME"].astype(str).map(
            lambda v: bool((parse_name(v) or {}).get("sub")))
        blank = _blank(gdf["SUBNET"]) & want
        if blank.any():
            problems.append(f"{int(blank.sum()):,} rows carry a name with an S-token and no "
                            "SUBNET value")
    if problems:
        raise ContractError(
            f"LAYER '{spec.name}' IS NOT FULLY NAMED"
            + (f" (stage {stage})" if stage else "") + ":\n  " + "\n  ".join(problems)
            + "\nNaming runs after connectivity is known, so an unnamed layer mid-pipeline is "
              "expected - an unnamed layer at publication is not. Build the names with "
              "concept_name() and the town codes with town_letters().")


# ======================================================================================
# THE GRAPH. The primary object; every layer above is a view of it.
# ======================================================================================

@dataclass
class Node:
    uid: str
    x: float
    y: float
    kind: str = "chamber"
    tier: str = "lateral"
    grd_m: float = float("nan")
    inv_m: float = float("nan")
    src: str = "dwg_road"
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
    vertices: Tuple[Tuple[float, float], ...] = ()   # INTERMEDIATE vertices ONLY.
    # The endpoints are deliberately absent. An edge's geometry is built as
    # [node[us].xy] + vertices + [node[ds].xy], so it is structurally impossible for a
    # published reach to stop 1.000 m short of the chamber it joins - which is what 91.4 %
    # of W10's stitch links did, in a layer that shipped in 7,919 pieces.
    src: str = "dwg_road"
    confidence: str = "drafted"
    stage: str = ""
    attrs: Dict = field(default_factory=dict)


class NodeIndex:
    """The ONLY place a node identity is minted.

    Identity is SPATIAL, at criteria.MH_SNAP_M (3.0 m): closer than the chamber clearance
    means ONE structure. A caller asking for a node within 3 m of an existing one gets the
    EXISTING uid back, so two stages that independently decide a chamber belongs at a street
    corner produce one chamber - not two 0.4 m apart with a 0.4 m pipe between them.

    A uniform grid at the merge radius does the lookup: no scipy, O(1) per insert, and the
    ids are deterministic for a given insertion order. Meaning is NOT in the uid; it is in
    NODE_REF, which can be recomputed after a pass-2 relabel without orphaning a reference.
    """

    def __init__(self, merge_m: float = NODE_MERGE_M):
        self.merge_m = float(merge_m)
        self._cells: Dict[Tuple[int, int], List[str]] = {}
        self.nodes: Dict[str, Node] = {}
        self._n = 0

    def _cell(self, x: float, y: float) -> Tuple[int, int]:
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
            for k, v in kw.items():            # fill blanks; never overwrite a real value
                if not hasattr(nd, k):
                    continue
                cur = getattr(nd, k)
                if cur in ("", 0, None) or (isinstance(cur, float) and math.isnan(cur)):
                    setattr(nd, k, v)
            return uid
        self._n += 1
        uid = NODE_UID_FMT.format(self._n)
        self.nodes[uid] = Node(uid=uid, x=float(x), y=float(y), **kw)
        self._cells.setdefault(self._cell(x, y), []).append(uid)
        return uid


class Network:
    """Nodes, edges, and the invariants held WHILE BUILDING rather than checked afterwards.

    Three things are impossible here, not merely audited:

      no loops           add_edge refuses a SECOND outgoing edge from a node. A forest is a
                         graph where every node has at most one parent; enforcing that at
                         insertion makes a cycle unreachable (H15)
      dangling reference an edge whose us or ds is not a registered node raises (H16)
      geometry drift     to_edges_gdf() builds the LineString FROM node coordinates

    What is still checked afterwards, because it is global rather than local: how many
    components exist, which SYSTEM each belongs to, and whether each ends at exactly one
    outfall.
    """

    def __init__(self, index: Optional[NodeIndex] = None):
        self.index = index or NodeIndex()
        self.edges: Dict[str, Edge] = {}
        self.out_edge: Dict[str, str] = {}         # node uid -> its ONE outgoing edge
        self.in_edges: Dict[str, List[str]] = {}
        self._n = 0

    # ---- nodes
    @property
    def nodes(self) -> Dict[str, Node]:
        return self.index.nodes

    def node(self, x: float, y: float, **kw) -> str:
        return self.index.get_or_create(x, y, **kw)

    # ---- edges
    def add_edge(self, us: str, ds: str, *, vertices: Iterable = (), stage: str = "",
                 **kw) -> str:
        for role, uid in (("us", us), ("ds", ds)):
            if uid not in self.nodes:
                raise ContractError(
                    f"edge {role}={uid!r} is not a registered node. Every edge references two "
                    "nodes minted by NodeIndex - an id invented at the call site is how a "
                    "layer stops being a network.")
        if us == ds:
            raise ContractError(f"self-loop at {us}")
        if us in self.out_edge:
            prev = self.edges[self.out_edge[us]]
            raise ContractError(
                f"node {us} already drains to {prev.ds} via {prev.uid}; refusing a second "
                f"outgoing edge to {ds}. The network is a FOREST (H15). One parent per node "
                "makes a loop unreachable - if this reach is real, the upstream chamber is in "
                "the wrong place, or the two runs must meet at a junction downstream.")
        self._n += 1
        uid = EDGE_UID_FMT.format(self._n)
        self.edges[uid] = Edge(uid=uid, us=us, ds=ds,
                               vertices=tuple((float(a), float(b)) for a, b in vertices),
                               stage=stage, **kw)
        self.out_edge[us] = uid
        self.in_edges.setdefault(ds, []).append(uid)
        return uid

    # ---- traversal
    def downstream_path(self, uid: str, limit: int = 200000) -> List[str]:
        """Node uids from here to the terminal. Also the cycle detector: a forest cannot
        revisit, so a repeat means the invariant was bypassed outside add_edge()."""
        seen, out, cur = set(), [], uid
        while cur is not None and len(out) < limit:
            if cur in seen:
                raise ContractError(f"cycle through {cur} - H15 breached. Nothing in this "
                                    "module can create one, so it came from an edit to "
                                    "out_edge outside add_edge().")
            seen.add(cur)
            out.append(cur)
            e = self.out_edge.get(cur)
            cur = self.edges[e].ds if e else None
        return out

    def outfalls(self) -> List[str]:
        """DERIVED, never asserted: a node with no outgoing edge is where its system
        discharges. This is the only definition of an outfall in W12."""
        return [u for u in self.nodes if u not in self.out_edge]

    def components(self) -> Dict[str, str]:
        """node uid -> the terminal it reaches. One dict, and every question about
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

    def ground_fall(self, edge_uid: str) -> float:
        """GROUND fall along an edge: upstream ground minus downstream ground. NEGATIVE
        means the ground RISES along the direction of flow.

        On the Network rather than in a stage because it is the quantity W12 exists to
        control, and a quantity computed in three places gets three answers."""
        e = self.edges[edge_uid]
        return self.nodes[e.us].grd_m - self.nodes[e.ds].grd_m

    def against_grade(self, edge_uid: str) -> bool:
        """True where this edge carries flow against the ground by more than
        criteria.ADVERSE_MIN_M - below which a 'rise' is DEM noise on a short reach."""
        gf = self.ground_fall(edge_uid)
        return bool(gf == gf and gf < -C.ADVERSE_MIN_M)      # gf == gf excludes NaN

    def check(self) -> List[str]:
        """Global invariants. The local ones already raised at insertion.

        The COMPONENT COUNT is reported, not condemned: philosophy sec 8a contemplates a
        central network plus satellites plus on-site systems, so more than one component is
        legal. What is enforced is the property H15 is actually reaching for - EVERY
        component terminates at exactly one outfall, and that outfall is a real terminal kind.
        """
        bad: List[str] = []
        roots = self.components()
        comps = (pd.Series(list(roots.values())).value_counts()
                 if roots else pd.Series(dtype=int))
        if len(comps) > 1:
            systems = sorted({self.nodes[u].system for u in roots})
            bad.append(
                f"{len(comps)} components (W10 published 7,919). Largest {comps.iloc[0]:,} "
                f"nodes, smallest {comps.iloc[-1]:,}; systems present: {systems}. More than "
                "one component is LEGAL - a satellite works is legal - but each must end at "
                "exactly one outfall, and any that drains nowhere is listed below.")
        orphan = [u for u, nd in self.nodes.items()
                  if u not in self.out_edge and not self.in_edges.get(u)]
        if orphan:
            bad.append(f"{len(orphan):,} isolated nodes with no reach at all: {orphan[:5]}")
        for u in self.outfalls():
            k = self.nodes[u].kind
            if k not in ("outfall", "station", "tie"):
                bad.append(f"node {u} has no downstream edge but is kind={k!r}. A terminal "
                           "node is an outfall, a station or a tie to the existing network - "
                           "nothing else terminates.")
        return bad

    # ---- views. Geometry is generated HERE and nowhere else.
    def edge_geom(self, uid: str) -> LineString:
        e = self.edges[uid]
        return LineString([self.nodes[e.us].xy] + list(e.vertices) + [self.nodes[e.ds].xy])

    def to_nodes_gdf(self, extra: Optional[pd.DataFrame] = None) -> gpd.GeoDataFrame:
        rows = []
        for u, nd in self.nodes.items():
            r = dict(
                NODE_UID=u, NODE_REF=nd.ref or node_ref(nd, u), NODE_KIND=nd.kind,
                X=nd.x, Y=nd.y, GRD_M=nd.grd_m, INV_M=nd.inv_m,
                DEPTH_M=nd.grd_m - nd.inv_m, TIER=nd.tier,
                DS_NODE=self.edges[self.out_edge[u]].ds if u in self.out_edge else "",
                N_IN=len(self.in_edges.get(u, ())),
                N_OUT=1 if u in self.out_edge else 0,
                # FIX 5. IS_OUTFALL is DERIVED HERE and nowhere else: a node with no outgoing
                # edge is where its system discharges, and the graph is the only thing that
                # knows. validate() rejects any value that disagrees with DS_NODE.
                IS_OUTFALL=0 if u in self.out_edge else 1,
                SRC=nd.src, CONFIDENCE=nd.confidence, STAGE=nd.stage,
                PACKAGE=nd.package, PHASE=nd.phase)
            r.update(nd.attrs)
            rows.append(r)
        g = gpd.GeoDataFrame(rows,
                             geometry=[Point(self.nodes[r["NODE_UID"]].xy) for r in rows],
                             crs=CRS_EPSG)
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
            gf = self.ground_fall(uid)
            r = dict(EDGE_UID=uid, US_NODE=e.us, DS_NODE=e.ds, TIER=e.tier,
                     LEN_M=geom.length,
                     # the terrain-first block, generated with the geometry so it cannot be
                     # forgotten and cannot be computed twice
                     GND_FALL=gf,
                     AGN_GRADE=int(self.against_grade(uid)),
                     RISE_M=max(0.0, -gf) if gf == gf else float("nan"),
                     TAU_PA=C.TAU_PA,
                     SRC=e.src, CONFIDENCE=e.confidence, STAGE=e.stage,
                     PACKAGE=self.nodes[e.us].package, PHASE=self.nodes[e.us].phase)
            r.update(e.attrs)
            rows.append(r)
            geoms.append(geom)
        g = gpd.GeoDataFrame(rows, geometry=geoms, crs=CRS_EPSG)
        if extra is not None:
            g = g.merge(extra, on="EDGE_UID", how="left")
        return g

    # ---- the round trip: reloading the PUBLISHED layers must reproduce the graph
    @staticmethod
    def assert_round_trip(nodes_gdf, edges_gdf, tol: float = ENDPOINT_TOL_M) -> None:
        """Re-read the PUBLISHED layers and prove they still ARE the graph.

        Four things: every US_NODE/DS_NODE resolves; every edge endpoint sits on its own
        node's coordinate within `tol`; no edge is multipart; no node has two outgoing edges.
        Run it on what was WRITTEN, not on what is in memory - the whole point is that the
        published artefact is the thing anybody else will read.

        `tol` is HALF the graph clustering radius, PER ENDPOINT, because two reaches arriving
        at one chamber each spend their own allowance and the errors add."""
        problems = []
        if "NODE_UID" not in nodes_gdf.columns:
            raise ContractError("node layer has no NODE_UID - nothing to resolve against")
        pos = {r.NODE_UID: (r.geometry.x, r.geometry.y) for r in nodes_gdf.itertuples()}
        seen_out: Dict[str, str] = {}
        for r in edges_gdf.itertuples():
            for role in ("US_NODE", "DS_NODE"):
                uid = getattr(r, role)
                if uid not in pos:
                    problems.append(f"{r.EDGE_UID}.{role} = {uid!r} resolves to no node")
            if r.US_NODE in seen_out:
                problems.append(f"node {r.US_NODE} drains through both {seen_out[r.US_NODE]} "
                                f"and {r.EDGE_UID} - not a forest")
            seen_out[r.US_NODE] = r.EDGE_UID
            g = r.geometry
            if g is None or g.is_empty:
                problems.append(f"{r.EDGE_UID} has no geometry")
                continue
            if g.geom_type != "LineString":
                problems.append(f"{r.EDGE_UID} is {g.geom_type}, not a single LineString - a "
                                "graph builder would read only its first part and silently "
                                "drop the rest")
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
                            "1.000 m and the layer shipped in 7,919 pieces. Geometry is BUILT "
                            "from node coordinates, so this gap means something bypassed "
                            "to_edges_gdf().")
            if len(problems) > 40:
                problems.append("... stopping at 40")
                break
        if problems:
            raise ContractError("THE PUBLISHED LAYERS ARE NOT THE GRAPH:\n  "
                                + "\n  ".join(problems))

    @staticmethod
    def assert_degrees(nodes_gdf, edges_gdf) -> None:
        """N_OUT / N_IN on the node layer against the out- and in-degree of the pipe layer.

        Two INDEPENDENTLY COMPUTED numbers agreeing is the only cheap defence against the W10
        defect where the node layer and the pipe layer came out of different solves and
        disagreed by up to 10.39 m of depth. Neither layer alone can reveal it."""
        if "N_OUT" not in nodes_gdf.columns and "N_IN" not in nodes_gdf.columns:
            raise ContractError("the node layer publishes neither N_OUT nor N_IN - the pipe "
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
                "THE NODE AND REACH LAYERS DISAGREE ON TOPOLOGY:\n  " + "\n  ".join(bad)
                + "\nThey were written from the same graph or they were not. In W10 they were "
                "not, and the depth difference reached 10.39 m.")


def node_ref(nd: Node, uid: str, branch: str = "", seq: Optional[int] = None) -> str:
    """NAMA's own ID grammar: 5A-2-TM-MH185, 5A-2-SM.2-MH391.

    The network must read like theirs - they run it for fifty years. This label is for humans
    and drawings; NOTHING references it, so a pass-2 retier can rewrite every label without
    touching a single US_NODE. NWS's real numbering system is issued to the successful
    consultant and is not in our hands."""
    tok = TIER_TOKEN.get(nd.tier, "L") + (f".{branch}" if branch else "")
    pkg = nd.package or "P0"
    n = seq if seq is not None else int(uid[1:])
    return f"{pkg}-{tok}-MH{n:04d}"


# ======================================================================================
# THE TERRAIN REPORT - the quantities philosophy sec 4 requires, in one function
# ======================================================================================

def terrain_report(reaches, nodes=None) -> Dict[str, float]:
    """The against-the-grade quantities, measured off the PUBLISHED layers.

    Philosophy sec 4: "Uphill drainage is not forbidden ... but it is bounded and reported:
    the share of length draining against the ground, the cumulative climb along the flow
    path, and the worst single rise. THE DIAGNOSTIC IS THE DROP-STRUCTURE COUNT. A design
    generating vortex shafts by the thousand where the as-built has tens is not describing
    the same ground; it is describing its own tree."

    W11a measured 42.5 % of 1,731.7 km draining uphill, 7,061 m of cumulative climb, and
    2,449 vortex shafts against 37 built. Those are in criteria.BENCHMARKS and are printed
    beside our own, because a share with nothing to compare it to is not a finding.

    THE ONE FUNCTION for all of these. Seven different lifting-station counts got into
    circulation on this project because each was computed ad hoc at the point of reporting.
    """
    L = pd.to_numeric(reaches["LEN_M"], errors="coerce").fillna(0.0)
    total = float(L.sum())
    out: Dict[str, float] = {"length_m": total, "n_reach": int(len(reaches))}

    if "AGN_GRADE" in reaches.columns:
        ag = pd.to_numeric(reaches["AGN_GRADE"], errors="coerce").fillna(0) == 1
        out["against_len_m"] = float(L[ag].sum())
        out["against_share"] = (out["against_len_m"] / total) if total else 0.0
        out["n_against"] = int(ag.sum())
    if "RISE_M" in reaches.columns:
        r = pd.to_numeric(reaches["RISE_M"], errors="coerce").fillna(0.0)
        out["climb_m"] = float(r.sum())
        out["worst_rise_m"] = float(r.max()) if len(r) else 0.0
    if "GND_FALL" in reaches.columns:
        gf = pd.to_numeric(reaches["GND_FALL"], errors="coerce").fillna(0.0)
        out["descent_m"] = float(gf.clip(lower=0.0).sum())
    if nodes is not None and "VORTEX" in nodes.columns:
        out["n_vortex"] = int((pd.to_numeric(nodes["VORTEX"], errors="coerce")
                               .fillna(0) == 1).sum())
    if nodes is not None and "DROP_M" in nodes.columns:
        d = pd.to_numeric(nodes["DROP_M"], errors="coerce").fillna(0.0)
        out["n_backdrop"] = int((d > C.DROP_TRIGGER).sum())
        out["drop_total_m"] = float(d.sum())
    return out


def terrain_banner(reaches, nodes=None) -> str:
    """The terrain report as text, with the W11a and as-built benchmarks beside it. Printed
    on every deliverable that shows a network."""
    m = terrain_report(reaches, nodes)
    b = C.BENCHMARKS
    lines = ["THE TREE AGAINST THE GROUND (philosophy sec 4 - bounded and REPORTED)"]
    if "against_share" in m:
        lines.append(f"  draining against the ground   {m['against_share'] * 100:6.1f} % of "
                     f"{m['length_m'] / 1000:,.1f} km   ({m['against_len_m'] / 1000:,.1f} km, "
                     f"{m['n_against']:,} reaches)")
        lines.append(f"    W11a, the defect being fixed  "
                     f"{b['UPHILL_SHARE_W11A'][0] * 100:6.1f} % of 1,731.7 km")
    if "climb_m" in m:
        lines.append(f"  cumulative climb              {m['climb_m']:10,.0f} m"
                     + (f"  against {m.get('descent_m', 0):,.0f} m of descent"
                        if "descent_m" in m else ""))
        lines.append(f"    W11a                        {b['CLIMB_W11A_M'][0]:10,.0f} m")
        lines.append(f"  worst single rise             {m['worst_rise_m']:10,.2f} m")
    if "n_vortex" in m:
        lines.append(f"  VORTEX DROP SHAFTS            {m['n_vortex']:10,d}   "
                     "<- THE DIAGNOSTIC")
        lines.append(f"    built by NAMA at Ibri       {b['VORTEX_BUILT'][0]:10,d}")
        lines.append(f"    W11a wanted                     2,449   (philosophy sec 4 says "
                     "2,254 - the two live documents disagree, and that is itself a finding)")
    if "n_backdrop" in m:
        lines.append(f"  backdrops over "
                     f"{C.DROP_TRIGGER:.2f} m            {m['n_backdrop']:10,d}   "
                     f"total drop {m.get('drop_total_m', 0):,.0f} m")
    return "\n".join(lines)


# ======================================================================================
# How a stage declares what it read, what it wrote and what it dropped
# ======================================================================================

@dataclass
class Funnel:
    """N0 -> N1 -> N2, with a named reason and retrievable ids for every loss.

    Any metric with a filter chain prints its own funnel, so a second filter cannot be
    applied to an already-filtered set without it being visible. W10's 1,233 m3/d vanished
    because a radius test returned nothing and nobody counted the difference."""
    name: str
    n0: int
    steps: List[Dict] = field(default_factory=list)

    def drop(self, reason: str, ids: Optional[Sequence] = None, n: Optional[int] = None,
             qty: float = 0.0) -> "Funnel":
        if ids is None and n is None:
            raise ContractError(f"funnel '{self.name}': a drop must carry ids or a count. An "
                                "uncounted drop is a silent one.")
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
                f"funnel '{self.name}' does not close: {self.line()} predicts {self.n:,} but "
                f"the stage produced {n_final:,}. The {abs(self.n - n_final):,} difference is "
                "a SILENT DROP - name it with .drop(reason, ids).")


@dataclass
class StageRecord:
    stage: str
    order: int
    reads: List[Dict] = field(default_factory=list)
    writes: List[Dict] = field(default_factory=list)
    funnels: List[Funnel] = field(default_factory=list)
    metrics: Dict[str, object] = field(default_factory=dict)
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

    def metric(self, name: str, value, unit: str = "") -> None:
        self.metrics[name] = value if not unit else f"{value} {unit}"

    def note(self, text: str) -> None:
        self.notes.append(text)

    def did_nothing(self, reason: str) -> None:
        """Declare a DELIBERATE no-op. W10's road treatment ran with `units=None,
        sampler=None` and three of its steps silently did nothing; 34 collapsed roundabout
        rings ended up intersecting a registered plot. A stage may do nothing. It may not do
        nothing QUIETLY."""
        self.no_change_reason = reason

    def to_dict(self) -> Dict:
        return dict(stage=self.stage, order=self.order, seconds=round(self.seconds, 2),
                    reads=self.reads, writes=self.writes, metrics=self.metrics,
                    notes=self.notes, no_change_reason=self.no_change_reason,
                    funnels=[dict(name=f.name, n0=f.n0, n=f.n, line=f.line(), steps=f.steps)
                             for f in self.funnels])


class Manifest:
    """The run's record. One JSON, appended by every stage, read by the report and the audit.

    Answers mechanically: what did stage 5 read? did stage 3 change anything? where did the
    131 missing plots go? which number came from which function?"""
    path = os.path.join(W12_ROOT, "run", "manifest.json")
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
                    "rec.wrote(layer, path, n) or rec.did_nothing(reason) - no stage silently "
                    "no-ops.")
            cls.records.append(rec)
            cls.save(path or cls.path)

    @classmethod
    def save(cls, path: Optional[str] = None) -> str:
        p = path or cls.path
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(dict(contract=CONTRACT_VERSION, criteria=C.__class__.__module__,
                           tau_pa=C.TAU_PA,
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


# ======================================================================================
# One function per published number
# ======================================================================================

_METRICS: Dict[str, Dict] = {}


def published(name: str, unit: str = "", source: str = ""):
    """Register THE ONE function allowed to produce a published quantity.

    Seven different lifting-station counts are in circulation from this project - 19, 21, 25,
    37, 140, 184, 239 - each computed ad hoc at the point of reporting. The count moved
    11 -> 21 -> 19 not because the design changed but because the definition did. A second
    definition of the same name raises HERE rather than in a client meeting."""
    def deco(fn):
        prior = _METRICS.get(name)
        if prior and prior["qualname"] != fn.__qualname__:
            raise ContractError(
                f"published metric '{name}' is already defined by {prior['qualname']}; "
                f"{fn.__qualname__} would be a second definition. Every published number "
                "comes from exactly one function - call the existing one.")
        _METRICS[name] = dict(fn=fn, unit=unit, source=source, qualname=fn.__qualname__)
        return fn
    return deco


def value(name: str, *a, **kw):
    if name not in _METRICS:
        known = ", ".join(sorted(_METRICS)) or "(none registered)"
        raise ContractError(f"no published function for '{name}'. Known: {known}")
    return _METRICS[name]["fn"](*a, **kw)


def metrics_register() -> pd.DataFrame:
    return pd.DataFrame([dict(metric=k, unit=v["unit"], source=v["source"],
                              function=v["qualname"]) for k, v in sorted(_METRICS.items())])


# ======================================================================================
# Publishing
# ======================================================================================

def gpkg_path(root: str, name: str = GPKG_NAME) -> str:
    return os.path.join(root, "shp", name)


def publish(gdf, layer_name: str, root: str, *, stage: str = "", gpkg: str = GPKG_NAME,
            allow_empty: bool = False, mirror: bool = True) -> str:
    """Validate, then write. THE ONLY sanctioned way a layer leaves a stage.

    Validation is not optional and not skippable, because the failure it prevents - an
    unauditable layer - is invisible until the audit.

    Both formats are written by default, and they carry IDENTICAL schemas: every field name
    is 10 characters or fewer (enforced at import), so the shapefile mirror loses nothing.
    That is the point of FIX 4 - W11a had to argue that the GeoPackage was the only audited
    artefact because a field name would be truncated; here neither format is privileged and
    a check can be pointed at either.

    An empty layer needs `allow_empty=True`. Publishing nothing is a legitimate answer for,
    say, a crossings register on a design with no crossings - and it is EXACTLY what a stage
    that silently did nothing also produces. The flag makes the caller say which."""
    if len(gdf) == 0 and not allow_empty:
        raise ContractError(
            f"stage {stage or '?'} is publishing an EMPTY '{layer_name}'. If that is the "
            "right answer say so with allow_empty=True; otherwise the stage no-opped, which "
            "is how W10's road treatment ran with units=None and three of its steps quietly "
            "did nothing.")
    validate(gdf, layer_name, stage=stage)
    spec = _spec(layer_name)
    p = gpkg_path(root, gpkg)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    gdf.to_file(p, layer=spec.name, driver="GPKG")
    if mirror and spec.geom != "none" and len(gdf):
        mirror_shapefile(gdf, layer_name, root)
    return p


def mirror_shapefile(gdf, layer_name: str, root: str) -> str:
    """The CAD/QGIS mirror. NOT a lossy copy: every field name fits the DBF by construction,
    so this file carries the same schema as the GeoPackage.

    It is still written second and named as a mirror, because the GeoPackage is the one with
    the layer NAMES in it and a shapefile directory is a pile of files with no relationships
    between them."""
    spec = _spec(layer_name)
    lost = [f.name for f in spec.fields
            if len(f.name) > SHP_FIELD_MAXLEN and f.name in gdf.columns]
    if lost:                                       # unreachable while _assert_shp_safe holds
        raise ContractError(f"cannot mirror '{spec.name}': {lost} exceed the DBF limit")
    p = os.path.join(root, "shp", f"W12_{spec.name}.shp")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    gdf.to_file(p)
    return p


def read_layer(root: str, layer_name: str, *, gpkg: str = GPKG_NAME, validate_it: bool = True,
               stage: str = ""):
    """Read a published layer back and RE-VALIDATE it. A stage validates before it writes
    AND after it reads: the second is what catches a layer edited by hand, round-tripped
    through another tool, or written by a stage running an older contract."""
    spec = _spec(layer_name)
    gdf = gpd.read_file(gpkg_path(root, gpkg), layer=spec.name)
    return validate(gdf, layer_name, stage=stage) if validate_it else gdf


def run_banner(reaches=None, nodes=None) -> str:
    """EVERY DELIVERABLE OPENS WITH THIS. The engineer's instruction of 2026-09-03: keep
    tau = 1.0 Pa, and FLAG it on every output; use the pipe sizes the guideline tabulates
    above DN1200, and FLAG them. Plus the terrain quantities, because a design that is not
    following the ground must say so on its own front page."""
    parts = [f"{CONTRACT_VERSION} | criteria {C.__module__} | EPSG:{CRS_EPSG}",
             "", C.tau_banner(), "", C.concept_banner()]
    if reaches is not None and "DN" in reaches.columns:
        big = C.large_dn_banner(pd.to_numeric(reaches["DN"], errors="coerce").dropna())
        if big:
            parts += ["", big]
    if reaches is not None:
        parts += ["", terrain_banner(reaches, nodes)]
    return "\n".join(parts)


# ======================================================================================
# Will the checks be able to run? Ask BEFORE publishing, not after.
# ======================================================================================

# What each check needs, transcribed from the philosophy's own H/P tables. The auditor is
# another module and it must implement EXACTLY these ids: philosophy sec 8 requires one check
# per rule, "generated from the tables above so a rule cannot exist without its check".
AUDIT_NEEDS: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "H1":  {"reaches": ("ON_DUAL_M", "ON_WADI_M", "CROSS_ID"), "external": ("roads",)},
    "H1a": {"reaches": ("ON_WADI_M", "CROSS_ID"), "external": ("hazard", "crossings")},
    "H2":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID", "DOD_PK")},
    "H3":  {"reaches": ("DN", "US_DEPTH", "DS_DEPTH", "COVER_US", "COVER_DN")},
    "H4":  {"reaches": ("DN", "US_DEPTH", "DS_DEPTH", "PAST_CAP")},
    "H4b": {"reaches": ("PAST_CAP", "CAP_EXIT", "CAP_LEN_M")},
    "H4c": {"nodes": ("DROP_M", "DROP_TYPE", "VORTEX")},
    "H5":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID", "CLEAN_BY", "TAU_PA")},
    "H6":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID", "SLOPE_MIN")},
    "H7":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID", "V_PK_MS")},
    "H8":  {"reaches": ("SIZED_BY",)},
    "H9":  {"reaches": ("TIER", "DN", "MATERIAL")},
    "H10": {"nodes": ("INLET_DEG", "INLET_FLAG")},
    "H11": {"reaches": ("INV_UP", "INV_DN")},
    "H12": {"reaches": ("DN", "LEN_M")},
    "H13": {"reaches": ("SLOPE_LAID",)},
    "H14": {"reaches": ("TIE_TYPE",), "external": ("existing",)},
    "H15": {"reaches": ("US_NODE", "DS_NODE"), "nodes": ("IS_OUTFALL", "NODE_UID")},
    "H16": {"reaches": ("US_NODE", "DS_NODE")},
    # H17 is W12's own, and it is the reason W12 exists. Philosophy sec 4 requires the
    # against-the-grade quantities REPORTED; a rule with no check is a claim nothing verifies.
    "H17": {"reaches": ("GND_FALL", "AGN_GRADE", "RISE_M"), "nodes": ("VORTEX",)},
    "R1":  {"reaches": ("DN", "QPK_LS", "SLOPE_LAID")},          # surcharge regression
    "R2":  {"reaches": ("DN", "US_DEPTH", "DS_DEPTH")},          # cover regression
    "R3":  {"reaches": ("ON_DUAL_M",), "external": ("roads",)},  # dual-carriageway regression
    "R4":  {"reaches": ("ON_WADI_M", "CROSS_ID"), "external": ("hazard", "crossings")},
    "G1":  {"reaches": ("SLOPE_LAID", "SLOPE_MIN")},
    "G2":  {"reaches": ("SIZED_BY", "GRAD_BY")},
    "G3":  {"reaches": ("US_NODE", "DS_NODE"), "nodes": ("NODE_UID",)},
    "G4":  {"external": ("manifest",)},                          # no stage silently no-ops
    "G5":  {"reaches": ("SRC", "CONFIDENCE"), "nodes": ("SRC", "CONFIDENCE")},
    # C1-C5 are the CONCEPT-STAGE rules (engineer 2026-09-05/06, philosophy sec 9). Each is
    # a rule the engineer stated, so each gets a check - "a rule that cannot be checked is
    # decoration, and a finding that is not checked is a finding waiting to be lost twice".
    "C1":  {"nodes": ("DROP_M", "DROP_WHY", "DROP_TYPE")},       # every drop names its cause
    "C2":  {"nodes": ("JOIN_MAIN", "JOIN_OFF_M", "JOIN_WHY")},   # outfall at the low point
    "C3":  {"connections": ("CAN_CONN", "CONN_WHY", "CONN_NEED")},   # plot connectability
    "C4":  {"nodes": ("NAME", "TOWN", "SUBNET"),                 # the naming grammar
            "reaches": ("NAME", "TOWN", "SUBNET")},
    "C5":  {"stations": ("N_SUBNET", "CATCH_KM", "WHY"),         # position chosen, not
            "rising_mains": ("DS_TYPE", "LEN_M")},               # triggered; shortest main
}


def audit_readiness(reaches=None, nodes=None, external: Sequence[str] = (), *,
                    connections=None, stations=None, rising_mains=None) -> pd.DataFrame:
    """Which checks can run against these layers, and what is missing from each.

    Call it at the END OF EVERY STAGE that touches a published layer. A check that cannot run
    is a FAILURE, so discovering one here - while the writing code is still open - is the
    whole point. W10 shipped with 7 of 22 unanswerable.

    The three keyword layers were added with the concept-stage checks C3 and C5, which read
    the connections, stations and rising-main layers. They are keyword-only and default to
    None so every existing two-layer caller keeps working - and a caller that passes neither
    is TOLD its C3/C5 cannot run rather than being scored as if they had passed."""
    have = {"reaches": set(reaches.columns) if reaches is not None else set(),
            "nodes": set(nodes.columns) if nodes is not None else set(),
            "connections": set(connections.columns) if connections is not None else set(),
            "stations": set(stations.columns) if stations is not None else set(),
            "rising_mains": (set(rising_mains.columns) if rising_mains is not None
                             else set()),
            "external": set(external)}
    rows = []
    for cid, need in AUDIT_NEEDS.items():
        miss = [f"{layer}.{f}" for layer, fields in need.items() for f in fields
                if f not in have.get(layer, set())]
        rows.append(dict(check=cid, can_run=not miss, missing=", ".join(miss)))
    return pd.DataFrame(rows)


def field_table(layer_name: str) -> pd.DataFrame:
    """The spec as a table - for the report, the data dictionary and the drawing legend."""
    spec = _spec(layer_name)
    return pd.DataFrame([dict(field=f.name, type=f.dtype, units=f.units,
                              required=f.required, blank_ok=f.blank_ok, check=f.audit,
                              allowed="|".join(f.allowed) if f.allowed else "", why=f.why)
                         for f in spec.fields])


def data_dictionary() -> pd.DataFrame:
    """Every field on every layer, one table. A deliverable in its own right."""
    return pd.concat([field_table(n).assign(layer=n) for n in sorted(LAYERS)],
                     ignore_index=True)[["layer", "field", "type", "units", "required",
                                         "blank_ok", "check", "allowed", "why"]]


# ======================================================================================
# SCHEDULES - the printed header declared BESIDE the stored field
# ======================================================================================

@dataclass(frozen=True)
class Schedule:
    """A deliverable table, with its printed headers bound to the fields behind them.

    They live here rather than in a reporting script for one reason: a header and the field
    it prints must not be editable apart. Rename a field in the layer and this file stops
    importing; change a header here and the field it reads is one line away. A schedule built
    by a separate script drifts from the layer the first time either changes, and the drift
    is invisible because both halves still run."""
    name: str
    layer: str
    key: str
    columns: Tuple[Tuple[str, str], ...]      # (printed header, stored field)
    required_by: str


SCHEDULES: Dict[str, Schedule] = {s.name: s for s in (
    Schedule(
        "chambers", "nodes", "NODE_REF",
        (("Name", "NAME"), ("Subnetwork", "SUBNET"),
         ("Manhole", "NODE_REF"), ("Easting", "X"), ("Northing", "Y"),
         ("Type", "NODE_KIND"), ("Cover level (m)", "GRD_M"), ("Invert level (m)", "INV_M"),
         ("Depth (m)", "DEPTH_M"), ("Cover to crown (m)", "COVER_M"),
         ("Chamber dia. (m)", "MH_DIA"), ("Inlets", "N_IN"),
         ("Min inlet angle (deg)", "INLET_DEG"), ("Swept channel", "INLET_FLAG"),
         ("Max drop (m)", "DROP_M"), ("Drop type", "DROP_TYPE"),
         ("Drop reason", "DROP_WHY"),
         ("Vortex shaft", "VORTEX"), ("Joins main pipe", "JOIN_MAIN"),
         ("Offset from low point (m)", "JOIN_OFF_M"), ("Offset reason", "JOIN_WHY"),
         ("Tier", "TIER"), ("Package", "PACKAGE"),
         ("Phase", "PHASE"), ("Confidence", "CONFIDENCE")),
        "scope-p25 chamber schedule; G203-p29-30 sec 4.4; concept rules 1 and 2"),
    Schedule(
        "pipes", "reaches", "EDGE_UID",
        (("Name", "NAME"), ("Subnetwork", "SUBNET"),
         ("Pipe", "EDGE_UID"), ("US manhole", "US_NODE"), ("DS manhole", "DS_NODE"),
         ("US invert (m)", "INV_UP"), ("DS invert (m)", "INV_DN"),
         ("US depth (m)", "US_DEPTH"), ("DS depth (m)", "DS_DEPTH"),
         ("Length (m)", "LEN_M"), ("DN (mm)", "DN"), ("Material", "MATERIAL"),
         ("Laid gradient (%)", "SLOPE_LAID"), ("Minimum gradient (%)", "SLOPE_MIN"),
         ("Gradient set by", "GRAD_BY"), ("Diameter set by", "SIZED_BY"),
         ("Peak factor", "PF"), ("PF method", "PF_METH"), ("Qadf (m3/d)", "QADF_M3D"),
         ("Infiltration (L/s)", "QINF_LS"), ("Qpeak (L/s)", "QPK_LS"),
         ("Velocity (m/s)", "V_PK_MS"), ("d/D", "DOD_PK"),
         ("Self-cleansing by", "CLEAN_BY"), ("Tractive stress (Pa)", "TAU_PA"),
         ("Ground fall (m)", "GND_FALL"), ("Against grade", "AGN_GRADE"),
         ("Tier", "TIER"), ("Package", "PACKAGE"), ("Confidence", "CONFIDENCE")),
        "scope-p25 pipe schedule; scope-p16 item 36"),
    Schedule(
        "stations", "stations", "NODE_REF",
        (("Name", "NAME"),
         ("Station", "NODE_REF"), ("Chamber", "NODE_UID"), ("Type", "ST_TYPE"),
         ("Reason", "WHY"), ("Duty flow (L/s)", "Q_DUTY_LS"), ("Qadf (m3/d)", "Q_ADF_M3D"),
         ("Static lift (m)", "LIFT_M"), ("Wet well (m3)", "WELL_M3"),
         ("Starts per hour", "WW_STARTS"), ("Ground level (m)", "GRD_M"),
         ("Subnetworks served", "N_SUBNET"), ("Network captured (km)", "CATCH_KM"),
         ("1:50-yr flood level (m)", "FLOOD_LV"), ("Land take (m2)", "LAND_M2"),
         ("Properties", "N_PROP"), ("Package", "PACKAGE"), ("Phase", "PHASE")),
        "scope-p15 item 19; G203-p40 Tab 17, p43 Tab 21, p48 sec 7.8; concept rule 6"),
    Schedule(
        "rising_mains", "rising_mains", "EDGE_UID",
        (("Name", "NAME"),
         ("Rising main", "EDGE_UID"), ("Station", "STATION"), ("DN (mm)", "DN"),
         ("Material", "MATERIAL"), ("Length (m)", "LEN_M"),
         ("Duty flow (L/s)", "Q_DUTY_LS"), ("Velocity at duty (m/s)", "V_DUTY_MS"),
         ("Static head (m)", "STAT_HD_M"), ("Total head (m)", "TOT_HD_M"),
         ("Discharges into", "DS_TYPE"), ("Discharge chamber", "DS_NODE"),
         ("Air valves", "N_AIRV"), ("Washouts", "N_WASH"),
         ("Septicity treatment", "SEPTIC_FL"), ("Package", "PACKAGE")),
        "scope-p13; G203-pp50-55 sec 8; concept rule 6 - the shortest main gravity allows"),
    Schedule(
        "connections", "connections", "PLOT_ID",
        (("Plot", "PLOT_ID"), ("Connection", "CONN_ID"), ("Chamber", "OUT_NODE"),
         ("Subnetwork", "SUBNET"),
         ("Served by", "SYSTEM"), ("Status", "WHY"), ("Properties", "N_PROP"),
         ("Qadf (m3/d)", "Q_ADF_M3D"), ("Length (m)", "LEN_M"),
         ("Gradient (%)", "SLOPE_LAID"), ("Cover (m)", "COVER_M"),
         ("Can connect", "CAN_CONN"), ("If not, why", "CONN_WHY"),
         ("Extra sewer depth needed (m)", "CONN_NEED"), ("Package", "PACKAGE")),
        "scope-p12 list of customer / house connections; concept rules 5 and 7"),
    Schedule(
        "crossings", "crossings", "CROSS_ID",
        (("Crossing", "CROSS_ID"), ("Pipe", "EDGE_UID"), ("Obstacle", "OBSTACLE"),
         ("Length (m)", "LEN_M"), ("Angle (deg)", "ANGLE_DEG"), ("Method", "METHOD"),
         ("Cover (m)", "COVER_M"), ("Consent obtained", "APPROVED")),
        "H1/H1a - a crossing is legal only if it is scheduled; G201-p85-86 sec 9.3"),
    Schedule(
        "packages", "packages", "PACKAGE",
        (("Package", "PACKAGE"), ("Phase", "PHASE"), ("Length (km)", "LEN_KM"),
         ("Plots", "N_PLOT"), ("Outlet chamber", "OUTLET"), ("Discharges into", "DS_PKG"),
         ("Commissioning order", "COMM_SEQ"), ("Independent", "INDEP"),
         ("One tree, one outlet", "ONE_TREE")),
        "scope-p16 item 39; G201-p21 Tab 2"),
)}


def schedule_frame(gdf, name: str, *, stage: str = "") -> pd.DataFrame:
    """Validate the layer, THEN render the schedule with its printed headers.

    Validating first is the point: a schedule is what the client reads, and printing one from
    an unvalidated layer is how a number that failed the contract reaches a document nobody
    re-checks. A schedule may demand fields the LayerSpec marks `required=False` - MH_DIA,
    PACKAGE, PHASE. That split is deliberate: the layer is publishable early, the schedule is
    printable only once the design is finished."""
    if name not in SCHEDULES:
        raise ContractError(f"no schedule '{name}'. Known: {', '.join(sorted(SCHEDULES))}")
    sch = SCHEDULES[name]
    validate(gdf, sch.layer, stage=stage)
    missing = [f for _h, f in sch.columns if f not in gdf.columns]
    if missing:
        raise ContractError(
            f"schedule '{name}' cannot be printed: the layer has no {missing}. Required by "
            f"{sch.required_by}. These are the columns the client's own scope asks for, so an "
            "absent one is a deliverable gap, not a formatting choice.")
    return pd.DataFrame({h: gdf[f].values for h, f in sch.columns})


# ======================================================================================
# SewerGEMS - canonical field -> Bentley field, so the model cannot drift from the layer
# ======================================================================================

# THE TRAP, and why LABEL is the uid and never the ref: START_ND and STOP_ND must resolve
# against MANHOLES.LABEL. Label the manholes with NODE_REF (regenerated on every retier)
# while the conduits carry NODE_UID, and every conduit imports UNCONNECTED - the model runs,
# reports nothing, and is wrong. Identity in the model is the uid; NODE_REF is for drawings.
SEWERGEMS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "MANHOLES": (("NODE_UID", "LABEL"), ("GRD_M", "GRD_EL"), ("INV_M", "INV_EL"),
                 ("MH_DIA", "MH_DIA")),
    "CONDUITS": (("EDGE_UID", "LABEL"), ("US_NODE", "START_ND"), ("DS_NODE", "STOP_ND"),
                 ("DN", "DIA_MM"), ("MATERIAL", "MATERIAL"), ("INV_UP", "INV_UP"),
                 ("INV_DN", "INV_DN"), ("LEN_M", "LEN_M")),
    "OUTFALL":  (("NODE_UID", "LABEL"), ("GRD_M", "GRD_EL"), ("INV_M", "INV_EL")),
}
SEWERGEMS_LAYER = {"MANHOLES": "nodes", "CONDUITS": "reaches", "OUTFALL": "nodes"}
# MANNING_N is added by the exporter from criteria.MANNING_N_EXPORT - it is a MODEL
# parameter, not a design value on the pipe, and does not live on the layer.


def gems_frame(gdf, table: str, *, stage: str = ""):
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
                            "carry. The model is a REFEREE for our hydraulics; a referee "
                            "given half the levels referees nothing.")
    keep = [src for src, _ in pairs] + (["geometry"] if "geometry" in gdf.columns else [])
    return gdf[keep].rename(columns=dict(pairs))


# ======================================================================================
# Self-test. `python -m w12.contract` - PROVES the invariants bite rather than asserting it.
# ======================================================================================

def _demo_network() -> "Network":
    net = Network()
    a = net.node(0.0, 0.0, kind="head", tier="lateral", grd_m=330.00, inv_m=328.35,
                 stage="T", src="dwg_road", confidence="drafted")
    b = net.node(100.0, 0.0, kind="chamber", tier="lateral", grd_m=329.50, inv_m=327.85,
                 stage="T", src="dwg_road", confidence="drafted")
    c = net.node(200.0, 0.0, kind="outfall", tier="lateral", grd_m=329.00, inv_m=327.35,
                 stage="T", src="dwg_road", confidence="drafted")
    net.add_edge(a, b, stage="T", src="dwg_road", confidence="drafted")
    net.add_edge(b, c, stage="T", src="dwg_road", confidence="drafted")
    return net


def _demo_reaches(net: "Network"):
    """A tiny, fully-populated, CONTRACT-COMPLIANT reach layer, built the way a stage would
    build one: the graph makes the geometry and the topology, the hydraulics make the rest."""
    g = net.to_edges_gdf()
    dn, slope, q = 200, 0.0050, 0.004               # DN200 at Table 11's own 5.00 mm/m
    y, v = hydra.pipe_state(dn, slope, q)
    rows = []
    for r in g.itertuples():
        us, ds = net.nodes[r.US_NODE], net.nodes[r.DS_NODE]
        us_d, ds_d = us.grd_m - us.inv_m, ds.grd_m - ds.inv_m
        rows.append(dict(
            DN=dn, MATERIAL=C.material("lateral", dn), CONSTR="open_trench",
            SLOPE_LAID=slope * 100.0,
            SLOPE_MIN=round(hydra.smin_for(dn, q) * 100.0, 6),
            GRAD_BY="table11", SIZED_BY="minimum",
            CLEAN_BY=hydra.clean_route(dn, slope, q),
            INV_UP=us.inv_m, INV_DN=ds.inv_m,
            US_DEPTH=us_d, DS_DEPTH=ds_d,
            COVER_US=cover(dn, us_d), COVER_DN=cover(dn, ds_d),
            QADF_M3D=q * 86400.0 * 0.9, QINF_LS=C.infiltration_ls(r.LEN_M),
            PF=1.0, PF_METH="held",
            V_PK_MS=v, DOD_PK=y, RET_MIN=hydra.retention_min(r.LEN_M, v) or 0.0,
            PAST_CAP=0, CAP_EXIT="", CAP_LEN_M=0.0, TIE_TYPE="none",
            ON_DUAL_M=0.0, ON_WADI_M=0.0, CROSS_ID="",
            TOWN="I", SUBNET="S01"))
    ex = pd.DataFrame(rows)
    # a conduit is named for its UPSTREAM manhole (concept rule 8)
    ex["NAME"] = [concept_name("I", "conduit", subnet="S01", seq=i + 1)
                  for i in range(len(ex))]
    ex["QPK_LS"] = ex.QADF_M3D * 1000.0 / 86400.0 * ex.PF + ex.QINF_LS
    out = g.join(ex)
    # the laid gradient has to reproduce the inverts, or the contract will say so
    out["INV_DN"] = out.INV_UP - out.LEN_M * out.SLOPE_LAID / 100.0
    out["DS_DEPTH"] = [net.nodes[u].grd_m - iv for u, iv in zip(out.DS_NODE, out.INV_DN)]
    out["COVER_DN"] = [cover(int(d), z) for d, z in zip(out.DN, out.DS_DEPTH)]
    return out


def _demo_nodes(net: "Network"):
    n = net.to_nodes_gdf()
    n["COVER_M"] = [cover(200, d) for d in n.DEPTH_M]
    for col, val in (("INLET_DEG", 180.0), ("INLET_FLAG", 0), ("MH_DIA", 1.0),
                     ("MH_MAT", "concrete"), ("DROP_M", 0.0), ("DROP_TYPE", "none"),
                     ("DROP_WHY", ""), ("VORTEX", 0), ("Q_ADF_M3D", 10.0), ("Q_PK_LS", 0.5),
                     ("N_PROP", 12.0), ("PAST_CAP", 0), ("CAP_EXIT", ""),
                     ("JOIN_MAIN", 0), ("JOIN_OFF_M", 0.0), ("JOIN_WHY", ""),
                     ("TOWN", "I"), ("SUBNET", "S01")):
        n[col] = val
    n["NAME"] = [concept_name("I", "manhole", subnet="S01", tier=t, seq=i + 1)
                 for i, t in enumerate(n.TIER)]
    # the subnetwork meets the main pipe at its outfall, and here it does so AT its own low
    # point - so the offset is 0.0 and there is nothing to explain (concept rule 2)
    n.loc[n.IS_OUTFALL == 1, "JOIN_MAIN"] = 1
    return n


def _demo_connections(net: "Network"):
    """Two load units - one that connects, one that cannot and says why and by how much."""
    uids = list(net.nodes)
    rows, geoms = [], []
    for i, (can, why, need) in enumerate(((1, "", 0.0),
                                          (0, "sewer above the plot outlet", 0.80))):
        geoms.append(LineString([(i * 20.0, 30.0), (i * 20.0, 20.0)]))
        rows.append(dict(
            CONN_ID=f"C{i + 1:05d}", PLOT_ID=f"PLOT{i + 1:05d}", OUT_NODE=uids[i],
            WHY="assigned", SYSTEM="central", CONN_TYPE="PCS",
            Q_ADF_M3D=round(C.PLOT_QADF_M3D * C.PROPS_PER_PLOT, 4),
            N_PROP=C.PROPS_PER_PLOT, LEN_M=10.0,
            SLOPE_LAID=C.PCS_MIN_SLOPE * 100.0,        # G203-p18 Table 5, PCS 3 % minimum
            COVER_M=C.PCS_MIN_COVER,                   # G203-p19 sec 3.5, 600 mm
            CAN_CONN=can, CONN_WHY=why, CONN_NEED=need,
            NAME=concept_name("I", "manhole", subnet="S01", tier="lateral", seq=i + 1),
            TOWN="I", SUBNET="S01",
            SRC="dwg_road", CONFIDENCE="drafted", STAGE="T", PACKAGE="", PHASE=0))
    g = gpd.GeoDataFrame(rows, geometry=geoms, crs=CRS_EPSG)
    # a connection is named for the CHAMBER it enters, so two plots on one chamber would
    # share a name - here they do not, and the uniqueness check is live
    g["LEN_M"] = g.geometry.length
    return g


def _demo_stations():
    """One station, designed rather than located: duty, lift, wet well, and the two fields
    that say its position was CHOSEN - what it captures, and from how many subnetworks."""
    q_ls, starts = 50.0, 10.0
    return gpd.GeoDataFrame(
        [dict(NODE_UID="N0000003", NODE_REF="P0-L-MH0003", NAME="I-PMP01", TOWN="I",
              SUBNET="", WHY="cap", ST_TYPE=C.ps_type(q_ls), Q_DUTY_LS=q_ls, LIFT_M=6.20,
              N_PROP=430.0, Q_ADF_M3D=1830.0,
              WELL_M3=C.well_volume_m3(q_ls / 1000.0, starts), WW_STARTS=starts,
              GRD_M=330.0, INV_M=323.8, FLOOD_LV=328.0, LAND_M2=60.0,
              N_SUBNET=2, CATCH_KM=7.4, RM_EDGE="E9000001", COMM_PT=1,
              SRC="dwg_road", CONFIDENCE="derived", STAGE="T", PACKAGE="", PHASE=0)],
        geometry=[Point(200.0, 0.0)], crs=CRS_EPSG)


def _demo_rising_mains():
    """One rising main that lifts to the NEAREST point where gravity resumes - DS_TYPE
    'manhole', not 'stp' (concept rule 6)."""
    dn, q_ls = 200, 50.0
    v = (q_ls / 1000.0) / (math.pi * (C.internal_diameter(dn) / 2.0) ** 2)
    line = LineString([(200.0, 0.0), (200.0, 180.0)])
    return gpd.GeoDataFrame(
        [dict(EDGE_UID="E9000001", US_NODE="N0000003", DS_NODE="N0000002",
              STATION="N0000003", NAME="I-P01", TOWN="I", SUBNET="",
              DN=dn, MATERIAL="DI", LEN_M=line.length, Q_DUTY_LS=q_ls,
              V_DUTY_MS=round(v, 3), V_MIN_MS=round(v * 0.45, 3),
              STAT_HD_M=6.20, TOT_HD_M=8.10, RETENT_M=3.0, N_AIRV=1, N_WASH=1,
              SEPTIC_FL=1, DS_TYPE="manhole",
              SRC="dwg_road", CONFIDENCE="derived", STAGE="T", PACKAGE="", PHASE=0)],
        geometry=[line], crs=CRS_EPSG)


def _raises(fn, needle: str, what: str) -> None:
    try:
        fn()
    except ContractError as e:
        if needle.lower() not in str(e).lower():
            raise AssertionError(f"{what}: raised, but not about {needle!r}:\n{e}")
        return
    raise AssertionError(f"{what}: DID NOT RAISE - the guard does not bite")


def _self_test(verbose: bool = True) -> None:
    # ------------------------------------------------------------- FIX 1: one allowance
    for dn in C.DN_SERIES + (160,):
        d = min_invert_depth(dn)
        assert abs(cover(dn, d) - C.MIN_COVER_CROWN) < 1e-12, dn
        # the contract's helpers ARE the criteria's - not a second implementation
        assert min_invert_depth(dn) == C.invert_depth_min(dn)
        assert cover(dn, 3.0) == C.cover(dn, 3.0)
    # ... and there is no second crown-to-invert expression in this module's SOURCE. Read
    # by text rather than by value, because a numeric scan finds any unrelated constant that
    # happens to equal 0.05 (LEN_TOL_M does) and would either fire falsely or be turned off.
    # Every "DN/1000 + something" in this file must add C.WALL_ALLOW and nothing else; the
    # one exception is the negative test below, which deliberately writes 0.10 to prove the
    # validator catches it.
    with open(os.path.abspath(__file__), encoding="utf-8") as _fh:
        _src = _fh.readlines()
    strays = [(i + 1, ln.strip()) for i, ln in enumerate(_src)
              if "/ 1000.0 + " in ln and "C.WALL_ALLOW" not in ln
              and "the OTHER allowance" not in ln]
    assert not strays, ("a second crown-to-invert allowance exists in contract.py at "
                        f"{strays}. W11a had two and a blocking cover check failed on every "
                        "reach - there is ONE, in criteria.WALL_ALLOW.")

    # ------------------------------------------------------------- FIX 4: DBF-safe names
    assert max(len(f.name) for s in LAYERS.values() for f in s.fields) <= SHP_FIELD_MAXLEN

    # ------------------------------------------------------------- the graph invariants
    net = _demo_network()
    assert net.node(1.0, 0.5) == "N0000001", "the 3 m merge must return the EXISTING node"
    a, b, c = "N0000001", "N0000002", "N0000003"
    _raises(lambda: net.add_edge(a, c), "already drains", "a second outgoing edge")
    _raises(lambda: net.add_edge(a, "N9999999"), "not a registered node", "a dangling ds")
    _raises(lambda: net.add_edge(a, a), "self-loop", "a self-loop")
    assert net.outfalls() == [c] and net.check() == []

    reaches, nodes = _demo_reaches(net), _demo_nodes(net)
    conns, stns, rmains = _demo_connections(net), _demo_stations(), _demo_rising_mains()
    validate(nodes, "nodes", stage="selftest")
    validate(reaches, "reaches", stage="selftest")
    Network.assert_round_trip(nodes, reaches)
    Network.assert_degrees(nodes, reaches)

    # ------------------------------------------------------------- FIX 5: IS_OUTFALL derived
    bad = nodes.copy()
    bad.loc[bad.index[0], "IS_OUTFALL"] = 1                # assert one that is not one
    _raises(lambda: validate(bad, "nodes"), "IS_OUTFALL contradicts DS_NODE",
            "an asserted outfall")

    # ------------------------------------------------------------- FIX 2: d/D by diameter
    bad = reaches.copy()
    bad["DN"] = 400
    bad["DOD_PK"] = 0.60                                   # legal at DN315, illegal at DN400
    bad["MATERIAL"] = "GRP"
    _raises(lambda: validate(bad, "reaches"), "depth of flow", "d/D at the wrong threshold")

    # ------------------------------------------------------------- FIX 3: DN in the series
    bad = reaches.copy()
    bad["DN"] = 375                                        # a real product, not in G203
    _raises(lambda: validate(bad, "reaches"), "not in criteria.DN_SERIES", "an off-series DN")
    # and the series reaches the sizes G203 tabulates
    for dn in (1400, 1700, 1800, 2000, 2400):
        assert dn in C.DN_SERIES

    # ------------------------------------------------------------- FIX 1 again, on the layer
    bad = reaches.copy()
    bad["COVER_US"] = bad.US_DEPTH - (bad.DN / 1000.0 + 0.10)   # the OTHER allowance
    _raises(lambda: validate(bad, "reaches"), "criteria.WALL_ALLOW",
            "a second wall allowance on the layer")

    # ------------------------------------------------------------- geometry vs LEN_M
    bad = reaches.copy()
    bad["LEN_M"] = bad.LEN_M + 1.0
    _raises(lambda: validate(bad, "reaches"), "disagrees with its own geometry",
            "a published length that does not measure its own line")

    # ------------------------------------------------------------- tier spelling
    bad = reaches.copy()
    bad["TIER"] = "sub_main"
    _raises(lambda: validate(bad, "reaches"), "UNDERSCORE", "the underscore tier spelling")

    # ------------------------------------------------------------- material by tier AND size
    bad = reaches.copy()
    bad["TIER"] = "main"
    bad["DN"] = 315
    bad["MATERIAL"] = "PVC-U"                # legal PRODUCT, illegal MAIN SEWER over 250 mm
    bad["DOD_PK"] = 0.40
    _raises(lambda: validate(bad, "reaches"), "does not permit",
            "PVC-U on a DN315 main (G203-p22 Table 6)")

    # ------------------------------------------------------------- reverse gradient
    bad = reaches.copy()
    bad["INV_DN"] = bad.INV_UP + 0.50
    _raises(lambda: validate(bad, "reaches"), "reverse gradient", "a reverse gradient")

    # ------------------------------------------------------------- the terrain-first block
    bad = reaches.copy()
    bad["AGN_GRADE"] = 1 - bad.AGN_GRADE
    _raises(lambda: validate(bad, "reaches"), "AGN_GRADE contradicts GND_FALL",
            "an against-grade flag that disagrees with the ground")
    rep = terrain_report(reaches, nodes)
    assert rep["against_share"] == 0.0 and rep["n_vortex"] == 0
    # ... and a network that DOES drain uphill is reported, not refused
    up = Network()
    p = up.node(0.0, 0.0, kind="head", grd_m=100.0, inv_m=98.4, stage="T")
    q_ = up.node(50.0, 0.0, kind="outfall", grd_m=101.0, inv_m=98.0, stage="T")
    up.add_edge(p, q_, stage="T")
    e = up.to_edges_gdf()
    assert e.AGN_GRADE.iloc[0] == 1 and abs(e.RISE_M.iloc[0] - 1.0) < 1e-9
    assert terrain_report(e)["against_share"] == 1.0

    # ------------------------------------------------------------- FIX 6: the register
    xing = gpd.GeoDataFrame(
        [dict(CROSS_ID="X000001", EDGE_UID="E0000001", OBSTACLE="wadi", LEN_M=30.0,
              ANGLE_DEG=88.0, METHOD="thrust_bore", COVER_M=1.6, APPROVED=0,
              SRC="dwg_road", CONFIDENCE="drafted", STAGE="T")],
        geometry=[LineString([(0, -15), (0, 15)])], crs=CRS_EPSG)
    xing["LEN_M"] = xing.geometry.length
    validate(xing, "crossings", stage="selftest")

    r2 = reaches.copy()
    r2.loc[r2.index[0], "ON_WADI_M"] = 12.0                # touches a wadi ...
    _raises(lambda: validate(r2, "reaches"), "no CROSS_ID", "an unscheduled wadi contact")

    r2.loc[r2.index[0], "CROSS_ID"] = "X000009"            # ... with an id nothing backs
    validate(r2, "reaches")                                # the row itself is now consistent
    _raises(lambda: assert_crossings_resolve(reaches=r2, crossings=xing),
            "resolve to NO register row", "a CROSS_ID with no register row")

    r2.loc[r2.index[0], "CROSS_ID"] = "X000001"            # the right id, wrong obstacle
    r2.loc[r2.index[0], "ON_WADI_M"] = 0.0
    r2.loc[r2.index[0], "ON_DUAL_M"] = 12.0
    _raises(lambda: assert_crossings_resolve(reaches=r2, crossings=xing),
            "different obstacle", "a crossing registered against the wrong obstacle")

    r2.loc[r2.index[0], "ON_DUAL_M"] = 0.0
    r2.loc[r2.index[0], "ON_WADI_M"] = 12.0
    assert_crossings_resolve(reaches=r2, crossings=xing)   # now it resolves
    _raises(lambda: assert_crossings_resolve(reaches=reaches, crossings=xing),
            "referenced by nothing", "a register row nothing uses")
    _raises(lambda: assert_crossings_resolve(reaches=r2, crossings=None),
            "no crossings register", "calling the check with no register at all")

    # ------------------------------------------------------------- multipart is refused
    from shapely.geometry import MultiLineString
    mp = reaches.copy()
    mp.loc[mp.index[0], "geometry"] = MultiLineString([[(0, 0), (50, 0)], [(60, 0), (100, 0)]])
    _raises(lambda: validate(mp, "reaches"), "MULTIPART", "multipart geometry")

    # ------------------------------------------------------------- CRS
    import warnings
    with warnings.catch_warnings():                 # the length check warns before the CRS
        warnings.simplefilter("ignore")             # check has finished reporting - expected
        _raises(lambda: validate(reaches.to_crs(4326), "reaches"), "EPSG", "the wrong CRS")

    # ---------------------------- FIX 4, proved on disk: the two formats carry ONE schema.
    # The claim is that no field name is lost on the way into a DBF, so a check can be
    # pointed at either artefact. Proving it means writing both and reading both back.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        publish(nodes, "nodes", tmp, stage="selftest")
        publish(reaches, "reaches", tmp, stage="selftest")
        gp_n = gpd.read_file(gpkg_path(tmp), layer="nodes")
        gp_r = gpd.read_file(gpkg_path(tmp), layer="reaches")
        sh_n = gpd.read_file(os.path.join(tmp, "shp", "W12_nodes.shp"))
        sh_r = gpd.read_file(os.path.join(tmp, "shp", "W12_reaches.shp"))
        for gp, sh, what in ((gp_n, sh_n, "nodes"), (gp_r, sh_r, "reaches")):
            lost = set(gp.columns) - set(sh.columns)
            assert not lost, (f"the shapefile mirror of '{what}' lost {sorted(lost)} - the "
                              "10-character rule is not holding, and a check pointed at the "
                              "mirror would report a field as missing on a correct design")
        # and both round-trip through validate(), which is the only claim that matters
        validate(gp_n, "nodes", stage="roundtrip")
        validate(gp_r, "reaches", stage="roundtrip")
        Network.assert_round_trip(gp_n, gp_r)
        validate(sh_n, "nodes", stage="roundtrip-shp")
        validate(sh_r, "reaches", stage="roundtrip-shp")

    # ------------------------------------------------------------- an unknown layer
    _raises(lambda: validate(reaches, "pipe_layer_v2"), "no contract for layer",
            "an unspecified layer")

    # ------------------------------------------------------------- an empty publish
    _raises(lambda: publish(reaches.iloc[0:0], "reaches", W12_ROOT, stage="T"),
            "EMPTY", "publishing an empty layer without saying so")

    # ------------------------------------------------------------- funnels close
    f = Funnel("plots", 100)
    f.drop("no corridor within 60 m", n=7)
    _raises(lambda: f.close(90), "does not close", "a funnel with a silent drop")
    f.drop("outside the study boundary", ids=["p1", "p2", "p3"])
    f.close(90)
    _raises(lambda: Funnel("x", 10).drop("because"), "ids or a count", "an uncounted drop")

    # ------------------------------------------------------------- one function per number
    @published("test_len_km", "km", "selftest")
    def _len_km(g):
        return float(pd.to_numeric(g.LEN_M).sum()) / 1000.0
    assert abs(value("test_len_km", reaches) - 0.2) < 1e-9

    def _other(g):
        return 0.0
    _raises(lambda: published("test_len_km")(_other), "already defined",
            "a second definition of a published number")

    # ------------------------------------------------------------- schedules and the model
    ch = schedule_frame(nodes, "chambers", stage="selftest")
    pi = schedule_frame(reaches, "pipes", stage="selftest")
    assert list(ch.columns)[0] == "Name" and "Manhole" in ch.columns
    assert "Tractive stress (Pa)" in pi.columns
    # the concept-stage flags reach the tables the client actually reads. A flag that lives
    # only in a GeoPackage column is a flag nobody outside this pipeline will ever see.
    assert {"Drop reason", "Joins main pipe", "Offset from low point (m)"} <= set(ch.columns)
    st_sch = schedule_frame(stns, "stations", stage="selftest")
    rm_sch = schedule_frame(rmains, "rising_mains", stage="selftest")
    cn_sch = schedule_frame(conns, "connections", stage="selftest")
    assert {"Subnetworks served", "Network captured (km)"} <= set(st_sch.columns)
    assert "Discharges into" in rm_sch.columns
    assert {"Can connect", "If not, why",
            "Extra sewer depth needed (m)"} <= set(cn_sch.columns)
    gems = gems_frame(reaches, "CONDUITS", stage="selftest")
    assert {"LABEL", "START_ND", "STOP_ND"} <= set(gems.columns)

    # =========================================================== THE CONCEPT-STAGE RULES
    # Engineer, 2026-09-05/06; philosophy sec 9. Each rule gets a demonstration that its
    # guard BITES - a check nobody has seen fail is a check nobody knows is wired in.

    validate(conns, "connections", stage="selftest")
    validate(stns, "stations", stage="selftest")
    validate(rmains, "rising_mains", stage="selftest")

    # ---- rule 8: the naming grammar, and the town letters --------------------------------
    assert concept_name("I", "subnet", subnet="S03") == "I-S03"
    assert concept_name("I", "manhole", subnet="S03", tier="sub main", seq=12) == \
        "I-S03-SM-M012"
    assert concept_name("I", "conduit", subnet="S03", seq=12) == "I-S03-C012"
    assert concept_name("I", "pump", seq=2) == "I-PMP02"
    assert concept_name("I", "main", seq=2) == "I-P02"
    # PMP is matched before P, so a pump is never read as force main "MP02"
    assert parse_name("I-PMP02")["kind"] == "pump"
    assert parse_name("I-P02")["kind"] == "main"
    assert parse_name("I-S03-SM-M012")["tier"] == "SM"
    assert parse_name("I-S03-C012")["sub"] == "S03"
    assert parse_name("I-S03-XX-M012") is None and parse_name("S03-M012") is None
    _raises(lambda: concept_name("I", "manhole", subnet="S03", tier="lane", seq=1),
            "not one of", "an unknown tier in a name")
    _raises(lambda: concept_name("I", "manhole", subnet="", tier="lateral", seq=1),
            "not S##", "a gravity element with no subnetwork")
    _raises(lambda: concept_name("Ibri", "pump", seq=1), "1-3 upper-case",
            "a town name used where a town CODE belongs")
    # the article is dropped, and a clash extends BOTH towns - not the smaller one
    assert town_letter("Al Aqar") == "A" and town_letter("Ad Dariz") == "D"
    codes = town_letters(["Al Aqar", "Al Ayn", "Ibri"])
    assert codes["Ibri"] == "I", codes
    assert codes["Al Aqar"] != codes["Al Ayn"], codes
    assert len(codes["Al Aqar"]) == len(codes["Al Ayn"]) == 2, (
        "both towns extend on a clash - the town with more served plots is not favoured, "
        f"got {codes}")
    assert len(set(town_letters(["Al Aqar", "Aqar", "Ibri"]).values())) == 3

    bad = nodes.copy()
    bad.loc[bad.index[0], "NAME"] = "I-S01-TM-M001"        # says trunk, TIER says lateral
    _raises(lambda: validate(bad, "nodes"), "NAME and TIER disagree", "a name against its tier")
    bad = nodes.copy()
    bad["NAME"] = "I-S01-L-M001"                            # one name for every chamber
    _raises(lambda: validate(bad, "nodes"), "DUPLICATE NAME", "one name on three chambers")
    bad = nodes.copy()
    bad.loc[bad.index[0], "NAME"] = "MH-1"
    _raises(lambda: validate(bad, "nodes"), "do not fit the grammar", "an unparseable name")
    bad = nodes.copy()
    bad.loc[bad.index[0], "SUBNET"] = "S09"
    _raises(lambda: validate(bad, "nodes"), "NAME and SUBNET disagree",
            "a subnet column that contradicts the name")
    # blank names pass validate() - naming runs after connectivity - but not assert_named()
    blank = nodes.copy()
    blank["NAME"] = ""
    blank["TOWN"] = ""
    validate(blank, "nodes")
    _raises(lambda: assert_named(blank, "nodes"), "NOT FULLY NAMED", "an unnamed publish")
    assert_named(nodes, "nodes")
    assert_named(reaches, "reaches")
    assert_named(stns, "stations")       # SUBNET blank on a station is legal - it is a SEAM

    # ---- rule 1: every drop carries the reason it exists ---------------------------------
    bad = nodes.copy()
    bad["DROP_M"] = 1.20
    bad["DROP_TYPE"] = "backdrop"
    bad["MH_DIA"] = C.MH_DIA_INTERNAL_BACKDROP      # G203-p30, so only DROP_WHY is at issue
    _raises(lambda: validate(bad, "nodes"), "no DROP_WHY", "a drop with no reason")
    bad["DROP_WHY"] = "velocity_cap"
    validate(bad, "nodes")                                  # ... and now it is explained
    bad["DROP_WHY"] = "because_it_is"
    _raises(lambda: validate(bad, "nodes"), "ILLEGAL VALUE in DROP_WHY", "a free-text reason")
    bad = nodes.copy()
    bad["DROP_WHY"] = "velocity_cap"                        # a reason with no drop
    _raises(lambda: validate(bad, "nodes"), "DROP_M = 0", "a reason for a drop that is not there")
    # and a whole network of drops given ONE reason is a fabrication, not a finding
    many = pd.concat([nodes.assign(DROP_M=1.2, DROP_TYPE="backdrop",
                                   DROP_WHY="velocity_cap")] * VARY_MIN_ROWS,
                     ignore_index=True)
    prob = constant_column_problem(many, "DROP_WHY", many.DROP_M > 0)
    assert prob and "FABRICATION" in prob, prob
    many["DROP_WHY"] = ["velocity_cap" if i else "cover_recovery"
                        for i in range(len(many))]
    assert constant_column_problem(many, "DROP_WHY", many.DROP_M > 0) is None

    # ---- rule 2: the outfall sits at the low point, or says how far off it is ------------
    bad = nodes.copy()
    bad.loc[bad.IS_OUTFALL == 1, "JOIN_OFF_M"] = 210.0
    _raises(lambda: validate(bad, "nodes"), "no JOIN_WHY", "an outfall moved with no reason")
    bad.loc[bad.IS_OUTFALL == 1, "JOIN_WHY"] = "no street at the low point"
    validate(bad, "nodes")
    bad = nodes.copy()
    bad.loc[bad.index[0], "JOIN_OFF_M"] = 5.0               # offset without joining at all
    bad.loc[bad.index[0], "JOIN_WHY"] = "x"
    _raises(lambda: validate(bad, "nodes"), "without JOIN_MAIN", "an offset from nothing")

    # ---- rule 5: a plot that cannot connect is named, with its size ----------------------
    bad = conns.copy()
    bad["CONN_WHY"] = ""
    _raises(lambda: validate(bad, "connections"), "no CONN_WHY",
            "a plot that cannot connect and does not say why")
    bad = conns.copy()
    bad["CAN_CONN"] = 1                                     # says it connects ...
    _raises(lambda: validate(bad, "connections"), "carry a reason why they cannot",
            "a connectable plot with a failure reason")
    bad = conns.copy()
    bad["CAN_CONN"] = 1
    bad["CONN_WHY"] = ""
    _raises(lambda: validate(bad, "connections"), "still ask for",
            "a connectable plot that needs more depth anyway")
    bad = conns.copy()
    bad["CAN_DRAIN"] = 1 - pd.to_numeric(bad.CAN_CONN)
    _raises(lambda: validate(bad, "connections"), "CAN_CONN and CAN_DRAIN disagree",
            "two answers to one drainability question")

    # ---- rule 6: a station's position is CHOSEN, and its main is the shortest one --------
    bad = stns.copy()
    bad["N_SUBNET"] = 0
    _raises(lambda: validate(bad, "stations"), "NOTHING DRAINS INTO THEM",
            "a station with nothing draining into it")
    bad = stns.copy()
    bad["CATCH_KM"] = 0.0
    _raises(lambda: validate(bad, "stations"), "captures no kilometres",
            "a station that captures nothing")
    bad = rmains.copy()
    bad["DS_TYPE"] = "works"
    _raises(lambda: validate(bad, "rising_mains"), "ILLEGAL VALUE in DS_TYPE",
            "an invented discharge type")
    bad = rmains.copy()
    bad["V_DUTY_MS"] = 2.9                                  # legal for GRAVITY, not for this
    _raises(lambda: validate(bad, "rising_mains"), "G203-p50",
            "the gravity 3.0 m/s applied to a rising main")

    # ---- the banned synonyms bite before they become a second column --------------------
    for col, needle in (("HEAD_M", "LIFT_M"), ("Q_LS", "Q_DUTY_LS"), ("STOR_M3", "WELL_M3")):
        bad = stns.copy()
        bad[col] = 1.0
        _raises(lambda b=bad: validate(b, "stations"), needle, f"the synonym {col}")
    bad = nodes.copy()
    bad["JOIN_OFFS_M"] = 0.0
    _raises(lambda: validate(bad, "nodes"), "JOIN_OFF_M",
            "the 11-character spelling of the join offset")

    # ------------------------------------------------------------- audit readiness
    rd = audit_readiness(reaches, nodes, external=("roads", "hazard", "crossings",
                                                   "existing", "manifest"),
                         connections=conns, stations=stns, rising_mains=rmains)
    cannot = rd[~rd.can_run]
    assert cannot.empty, ("a fully-populated pair of layers must make every check runnable; "
                          f"these cannot run: {cannot.to_dict('records')}")
    # ... and a caller that passes no connections layer is TOLD C3 cannot run, rather than
    # being scored as though it passed. A check that cannot run is a FAILURE, not a blank.
    partial = audit_readiness(reaches, nodes, external=("roads", "hazard", "crossings",
                                                        "existing", "manifest"))
    assert set(partial[~partial.can_run].check) == {"C3", "C5"}, \
        partial[~partial.can_run].to_dict("records")

    if verbose:
        print(f"{CONTRACT_VERSION}: self-test PASSED")
        print(f"  {len(LAYERS)} layers, "
              f"{sum(len(s.fields) for s in LAYERS.values())} fields, "
              f"longest name {max(len(f.name) for s in LAYERS.values() for f in s.fields)} "
              f"chars (DBF limit {SHP_FIELD_MAXLEN})")
        print(f"  {len(SCHEDULES)} schedules, {len(AUDIT_NEEDS)} checks declared, "
              f"{len(EXCLUDED)} entries in the exclusion register")
        print(f"  every check runnable against a fully-populated layer pair: "
              f"{int(rd.can_run.sum())}/{len(rd)}")
        print()
        print(run_banner(reaches, nodes))


if __name__ == "__main__":          # pragma: no cover
    _self_test()
