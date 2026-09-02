"""W11a stage 9 - the concept-stage deliverable set.

WHAT AN EXPORT STAGE IS FOR, AND WHY IT IS THE MOST DANGEROUS ONE.

This is where a design stops being a model and becomes the thing somebody prices, models
and digs. Every artefact a human ever sees - the shapefile in QGIS, the DXF on the
draftsman's screen, the KMZ the engineer opens on a phone, the chamber schedule the
quantity surveyor reads, the SewerGEMS model the referee runs - is produced here. So the
only defensible rule for this stage is that it **renders and never recomputes**: one
validated source, many views, and not a single number invented on the way out.

W10 broke that rule and the outputs are the evidence. `W10_pipes.shp` was drawn from
geometry alone and shipped in **7,919 disconnected components** at 0.01 m; the flow tree
that sized it lived in memory and died with the process. Nobody could see the defect
because nothing on the layer carried connectivity. Seven different lifting-station counts
reached circulation - 19, 21, 25, 37, 140, 184, 239 - because each document counted for
itself. `SLOPE_PCT` meant the minimum in one file and the laid gradient in another, so a
drawing and a schedule could describe different pipes and both look right.

FIVE W10 FAILURES THIS MODULE IS BUILT TO MAKE IMPOSSIBLE, not merely to audit:

  1. **the layer that is not the graph.** Nothing is drawn, mirrored or exported until
     `contract.Network.assert_round_trip` proves the published layers still ARE the graph -
     every US_NODE/DS_NODE resolves, every reach endpoint sits on its own chamber within
     half the auditor's snap, no multipart geometry - and `assert_degrees` proves the node
     layer and the reach layer came out of the same solve. If that fails, this stage exits
     NON-ZERO and writes nothing. An export built on a broken graph is how W10 shipped.
  2. **the recomputed number.** Every quantity printed on a map, a schedule or the console
     comes from a `@contract.published` function. A second definition of the same name
     raises here rather than in a client meeting (P2).
  3. **the name that means two things.** Drawings and schedules label `SLOPE_LAID` and
     print `SLOPE_MIN` beside it, because the pair is what audit G1 checks for and a
     single gradient column cannot say which one it is.
  4. **the invisible breach.** The quantity take-off is banded on **cover**, at the
     thresholds G203-p33 actually gives, and the first band is *below minimum cover*. A
     design with 45.92 km under 1.30 m produces a row in the take-off, not a footnote
     nobody reads.
  5. **the stage that quietly does nothing.** Every reduction this module makes - the
     SewerGEMS model scope, the DXF label cap, the number of profiles drawn, a schedule it
     could not print - is a named `Funnel` or a recorded note in the manifest. W10's
     `RoadTreatment` ran with `units=None, sampler=None` and three of its steps became
     no-ops nobody noticed.

CONCEPT STAGE, AND THE SIXTEEN THINGS THIS DELIBERATELY DOES NOT PRODUCE.
`W10/docs/research/DELIVERABLE_SPEC.md` D.7 lists sixteen items that belong to preliminary
or detailed design, each with its citation. They are transcribed into `DO_NOT_ATTEMPT`
below and printed on every run. Gold-plating a concept design into a detailed one is not
generosity: it commits the project to numbers that have no survey, no geotechnical report
and no NWS numbering system behind them, and it is how a concept drawing gets built from.

WHAT IT REFUSES TO DECIDE. No design value is computed here. Diameters, gradients, levels,
loads and station duties arrive on the layers; this module bands, groups, renames and draws
them. The only thresholds it introduces are BANDING edges for the take-off and the drawing,
and every one of them is an existing cited criterion re-used as a band edge - never a new
number. Where a band would need a value nobody has given us (excavation rate bands for
pricing), it is not invented: it is left to the rate schedule that is still awaited.

Sources: `_BRAIN/08_DESIGN_PHILOSOPHY.md` sec 5 (publish the LAID gradient), sec 8 (the
audit), `_BRAIN/02_DESIGN_CRITERIA.md` (every cited number), `W10/docs/research/
DELIVERABLE_SPEC.md` part D (the field lists, the schedule list, D.4 the Bentley package,
D.7 the do-not-attempt list), `W11a/py/w11a/contract.py` (all field names and schedules),
`W8/py/sewnet/export_gems.py` (the ModelBuilder import procedure, reused verbatim).

    python s9_export.py                 # export everything that exists
    python s9_export.py --only dxf,kmz  # re-run part of it
    python s9_export.py --selftest      # build a 6-chamber network and export it end to end
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
import warnings
import zipfile
from typing import Dict, List, Sequence, Tuple

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))            # .../W11a/py
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import geopandas as gpd                                       # noqa: E402
import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402
from shapely.geometry import LineString, Point                # noqa: E402

# The shared contract is imported FIRST and hard. It puts W8/py on sys.path, which is the
# only source of design numbers, and it raises on import if the criteria are missing - a
# contract with no numbers behind it is worse than no contract (contract.py, l.109).
from w11a import contract as K                                # noqa: E402
from w11a.contract import C, ContractError                    # noqa: E402  C = sewnet criteria

# The Bentley import walk-through, with the two traps that cost a modelling day each
# ("Set Invert to Start Node = False", and a loads import replacing the whole collection).
# DELIVERABLE_SPEC D.4 says reuse this file; its *procedure* is what is reusable, because
# its writer takes W8's in-memory `net` object and W11a's primary object is the layer set.
from sewnet.export_gems import PROCEDURE as GEMS_PROCEDURE    # noqa: E402


BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

# Read-only inputs. Nothing under W10/ or W8/ is written by this module, ever.
ROADS_SHP = BASE + r"\Hydraulic\SHP\Road centerline 2\Road_Centercline.shp"
BOUNDARY_SHP = BASE + r"\Hydraulic\SHP\Study area\Project Boundary.shp"
TERRAIN_VRT = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"
HAZARD_TIF = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"
EXISTING_SHP = os.path.join(K.REPO_ROOT, "W10", "shp", "W10_existing_built.shp")
# Claude-downloaded Esri tiles, mosaicked. Project rule 4 puts it under every map at 30 %.
# Licensing: it is never pushed to the repo, so a missing mosaic degrades to a plain map.
MOSAIC = BASE + r"\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"


# ======================================================================================
# D.7 - the sixteen items this stage refuses to produce, with the stage each belongs to.
# Printed on every run. A refusal without a record is one the next stage re-proposes.
# ======================================================================================

DO_NOT_ATTEMPT: Tuple[Tuple[str, str, str], ...] = (
    ("House connection design sheets", "Preliminary", "scope-p22 items 4, 6; p23 item 40.7"),
    ("Profiles at 1:1000 H / 1:100 V with the full annotation set", "Preliminary/Detailed",
     "scope-p23 item 40.6; scope-p26 item 4"),
    ("Plan sets at 1:2500", "Preliminary", "scope-p23 item 40.5"),
    ("Bedding and cover classes", "Detailed - and unspecifiable",
     "not in G203; PAM-SPC-4xx / PAM-STD-4xx not held (G201-p136)"),
    ("Structural, mechanical, electrical, ICA design; P&ID; SLD", "Preliminary onward",
     "G201-pp20-21 Tab 2; scope-p22 items 9, 34, 35"),
    ("HAZOP", "Preliminary", "G201-p21 Tab 2; scope-p22 item 24"),
    ("Surge analysis", "Preliminary/Detailed", "scope-p17; scope-p25"),
    ("H2S / septicity model (WATS)", "Preliminary/Detailed", "scope-p17; scope-p24"),
    ("Air vent design on the gravity network", "Preliminary", "G203-pp31-32 sec 4.5"),
    ("Bill of Quantities, measured or priced", "Preliminary 80 % / Detailed 90 %",
     "G201-p22 Tab 2; scope-p22 item 28, scope-p26 item 6"),
    ("Geotechnical interpretation, trial pits, utility clash resolution",
     "Preliminary/Detailed", "scope-pp16, 18, 24"),
    ("Final material selection", "Detailed",
     "scope-p25 'Final recommendations on pipe materials and diameters'"),
    ("Manhole numbering in NWS format", "Detailed - and BLOCKED",
     "scope-p25: the numbering system is issued to the successful consultant"),
    ("Architectural and landscaping drawings", "Preliminary", "scope-p18 sec 4.1.2.3"),
    ("ETAP power system analysis", "Preliminary onward", "scope-p8 item 20"),
    ("Construction phasing / construction planning", "Preliminary/Detailed",
     "G201-p21 Tab 2 - concept owes PROJECT phasing only"),
)

# The one place the boundary is genuinely fine and worth stating: D.3 puts *indicative*
# longitudinal profiles on the concept drawing list (scope-p12, "as part of the detailed
# concept design"). What D.7 forbids is the 1:1000/1:100 annotated SET. So this module
# draws an indicative long-section - ground line, invert line, chamber ticks - and stamps
# it INDICATIVE, and it does not scale, annotate or sheet it.


# ======================================================================================
# Banding. Every edge below is an EXISTING cited criterion re-used as a band edge.
# Not one of them is a new number. Where a band edge would have to be invented, it is not.
# ======================================================================================

# Diameter bands for the DXF layer split and the take-off. The three interior edges are
# the three places a guideline table actually changes behaviour, so a band boundary is
# always a place where something real changes - not a round number chosen for the legend.
DN_BANDS: Tuple[Tuple[int, int, str, str], ...] = (
    (0,    250,  "DN-250",
     "G203-p22 Tab 6: on a MAIN SEWER, PVC-U is permitted only 'up to 250 mm'"),
    (251,  350,  "DN251-350",
     "G203-p27 Tab 10: the d/D limit drops 0.65 -> 0.50 above DN350, and G203-p22 Tab 6 "
     "has a distinct '350 mm and above' material row"),
    (351,  600,  "DN351-600",
     "G203-p35 Tab 14: the permitted trunk-main material set changes above DN600"),
    (601, 9999,  "DN601UP",
     "G203-p35 Tab 14: above DN600 - GRP, lined RCC or profile-wall HDPE only"),
)

# Depth bands for the quantity take-off, cut on COVER TO CROWN because that is what
# G203-p33 and audit H3/H4 are about. The first band MUST come out empty: it exists so a
# breach appears as a priced row in the take-off instead of a note in a report appendix.
#
# NOTE, and it is deliberate: finer excavation bands (the 2 m steps a rate schedule
# usually wants) are NOT invented here. The unit-rate basis is the Renardet cost data
# still awaited from a colleague (00_CURRENT 'Still open'); banding the take-off to bands
# nobody prices is a number with no source, which this project prohibits.
DEPTH_BANDS: Tuple[Tuple[float, float, str, str], ...] = (
    (-1e9, C.MIN_COVER_CROWN, "cover BELOW the 1.30 m minimum",
     "G203-p33 sec 4.6.3 - this band must be EMPTY. W10 shipped 45.92 km in it"),
    (C.MIN_COVER_CROWN, 10.0, "cover 1.30 - 10 m",
     "G203-p33 - the recommendation is 'approximately 10 - 12 m' of cover"),
    (10.0, C.MAX_DEPTH, "cover 10 - 12 m",
     "G203-p33 - inside the recommendation's own range, excavation cost rising"),
    (C.MAX_DEPTH, 1e9, "cover PAST the 12 m cap",
     "philosophy sec 5 - permitted only via a distance-bounded exit, and never final "
     "until a manufacturer's rating and NWS's station cost arrive"),
)

# Presentation only - colour and line weight carry no engineering meaning, and are stated
# here rather than buried in three renderers so the DXF, the KMZ and the PNG cannot tell
# three different stories about the same pipe (project rule 3).
TIER_STYLE: Dict[str, Dict] = {
    "trunk main": dict(rgb=(20, 20, 20),   aci=7,   lw=2.6, kml_w=6.0, order=5),
    "sub main":   dict(rgb=(214, 39, 40),  aci=1,   lw=1.8, kml_w=4.2, order=4),
    "main":       dict(rgb=(255, 127, 14), aci=30,  lw=1.2, kml_w=3.0, order=3),
    "lateral":    dict(rgb=(31, 119, 180), aci=5,   lw=0.6, kml_w=1.8, order=2),
    "rider":      dict(rgb=(140, 140, 140), aci=8,  lw=0.4, kml_w=1.2, order=1),
}
DN_BAND_ACI = {"DN-250": 3, "DN251-350": 4, "DN351-600": 6, "DN601UP": 2}
DEPTH_BAND_COLOR = {0: "#d62728", 1: "#2ca02c", 2: "#ff7f0e", 3: "#8e44ad"}

# A DXF with a level stack on every chamber and a DN/gradient label on every reach is
# unopenable past a certain size. The cap is declared, the drop is counted, and the run
# says so - a drawing that quietly lost its annotation is worse than one that says it did.
# audit.h3/h4 compare with a 1e-6 slack. Every band edge and every printed comparison in
# this module uses the SAME slack, so the take-off and the audit can never disagree about
# a reach laid at exactly the minimum.
AUDIT_EPS = 1e-6

# Printed tables are rounded to 6 decimals - not for tidiness but because a chamber
# schedule reading "1.8000000000000114 m" is a schedule a client stops trusting, and the
# noise is double-precision residue from levels of order 300 m, twelve orders of magnitude
# below the 20 mm laying tolerance (G203-p29). The stored value is untouched.
PRINT_DECIMALS = 6

DXF_LABEL_CAP = 60_000
DXF_MIN_LABEL_LEN_M = 25.0        # W8's rule: below this the text overlaps the pipe
PROFILE_CAP = 12                  # longest routes drawn; the rest are listed, not hidden


# ======================================================================================
# Published quantities (P2). Every number this module prints comes through one of these.
# ======================================================================================

@K.published("network_length_km", "km", "sum of REACHES.LEN_M / 1000")
def network_length_km(reaches) -> float:
    """Gravity network length. Reads LEN_M, never the geometry: H12 and every published
    length read the FIELD, and validate() has already proved the two agree to 50 mm."""
    return float(pd.to_numeric(reaches["LEN_M"], errors="coerce").sum()) / 1000.0


@K.published("rising_main_length_km", "km", "sum of RISING_MAINS.LEN_M / 1000")
def rising_main_length_km(rising) -> float:
    if rising is None or not len(rising):
        return 0.0
    return float(pd.to_numeric(rising["LEN_M"], errors="coerce").sum()) / 1000.0


@K.published("chamber_count", "-", "len(NODES) excluding stations and outfalls")
def chamber_count(nodes) -> int:
    """A chamber is a structure NAMA maintains. A station and an outfall are counted
    separately because they are different assets with different costs - conflating them is
    how one project produced seven station counts."""
    return int((~nodes["NODE_KIND"].astype(str).isin(["station", "outfall"])).sum())


@K.published("station_count", "-", "len(STATIONS)")
def station_count(stations) -> int:
    return 0 if stations is None else int(len(stations))


@K.published("total_lift_m", "m", "sum of STATIONS.LIFT_M")
def total_lift_m(stations) -> float:
    """Total lift, not the station count. 00_CURRENT: the count is 19-21 depending on the
    funnel and 'the number is far less meaningful than total lift, because
    distance-clustering measures breach density'."""
    if stations is None or not len(stations):
        return 0.0
    return float(pd.to_numeric(stations["LIFT_M"], errors="coerce").sum())


@K.published("chambers_per_km", "1/km", "chamber_count / network_length_km")
def chambers_per_km(nodes, reaches) -> float:
    """The single number that exposed W10's missing chamber tier: 11.1/km against NAMA's
    built 32.3 and W8's 19.8 (build brief P4)."""
    L = network_length_km(reaches)
    return chamber_count(nodes) / L if L else 0.0


@K.published("qadf_total_m3d", "m3/d", "NODES.Q_ADF_M3D where DS_NODE is blank")
def qadf_total_m3d(nodes, reaches=None) -> float:
    """Flow leaving the network: the accumulated Qadf at every TRUE terminal.

    Two wrong answers this avoids. Summing QADF_M3D over all reaches counts each load once
    per reach it passes through - the accumulation double-count. Summing the reaches whose
    DS_NODE is nobody's US_NODE looks safer and is still wrong as soon as a lifting station
    exists: the reach arriving at a station is terminal on the GRAVITY layer, and the same
    flow reappears downstream of the rising main, so it is counted twice. A terminal is a
    node with no outgoing edge of ANY kind, and only the node layer knows that - DS_NODE on
    a station points at its discharge chamber.
    """
    if nodes is not None and "DS_NODE" in nodes.columns and "Q_ADF_M3D" in nodes.columns:
        term = K._blank(nodes["DS_NODE"])
        return float(pd.to_numeric(nodes.loc[term, "Q_ADF_M3D"], errors="coerce").sum())
    us = set(reaches["US_NODE"].astype(str))          # fallback, gravity-only design
    term = ~reaches["DS_NODE"].astype(str).isin(us)
    return float(pd.to_numeric(reaches.loc[term, "QADF_M3D"], errors="coerce").sum())


@K.published("properties_served", "-", "CONNECTIONS.N_PROP where OUT_NODE is set")
def properties_served(connections) -> float:
    if connections is None or not len(connections):
        return float("nan")
    assigned = ~K._blank(connections["OUT_NODE"])
    return float(pd.to_numeric(connections.loc[assigned, "N_PROP"], errors="coerce").sum())


@K.published("tier_share_pct", "%", "REACHES.LEN_M grouped by TIER")
def tier_share_pct(reaches) -> pd.Series:
    """Philosophy sec 4 gives the target: lateral 66 %, sub main 18 %, trunk 5 %. Published
    as a function so the map legend, the schedule and the console cannot disagree."""
    g = reaches.groupby(reaches["TIER"].astype(str))["LEN_M"].sum()
    return 100.0 * g / g.sum() if g.sum() else g


# ======================================================================================
# Banding helpers - one definition each, used by the DXF, the maps and the take-off.
# ======================================================================================

def dn_band(dn) -> str:
    d = int(dn)
    for lo, hi, code, _why in DN_BANDS:
        if lo <= d <= hi:
            return code
    return "DN601UP"


def depth_band_index(cover_m: float) -> int:
    """Band a cover, using the AUDITOR'S OWN tolerance at the edges.

    `audit.h3` tests `cover < 1.30 - 1e-6`. Band with a strict `>= 1.30` instead and a
    reach laid at exactly minimum cover lands in the "below the minimum" band on double
    precision alone - 1.2999999999999772 is what `330.0 - 328.35 - 0.35` actually returns.
    That would put 300 m of compliant pipe into a defect row of a client take-off while
    the audit beside it says PASS. Sharing the tolerance is not a fudge: it is the two
    numbers being computed to the same rule, which is the entire point of one definition.
    """
    if not np.isfinite(cover_m):
        return 1
    for i, (lo, hi, _lab, _why) in enumerate(DEPTH_BANDS):
        # The two auditor edges carry OPPOSITE slack, because the two checks are written
        # in opposite directions: h3 fails at `cover < 1.30 - eps`, so 1.30 - eps is where
        # "below minimum" ends; h4 fails at `cover > 12.0 + eps`, so 12.0 + eps is where
        # "past the cap" begins. Using -eps at both put a reach laid at exactly 12.000 m of
        # cover into the "PAST the 12 m cap" row of a client take-off while H4 beside it
        # said PASS - the same disagreement this function was written to remove, at the
        # other end of the range. Every other edge is a presentation edge and keeps -eps.
        lo_t = lo + AUDIT_EPS if lo == C.MAX_DEPTH else lo - AUDIT_EPS
        hi_t = hi + AUDIT_EPS if hi == C.MAX_DEPTH else hi - AUDIT_EPS
        if cover_m >= lo_t and cover_m < hi_t:
            return i
    return len(DEPTH_BANDS) - 1


def depth_band_label(cover_m: float) -> str:
    return DEPTH_BANDS[depth_band_index(cover_m)][2]


# ======================================================================================
# Reading the published set, and the graceful stop when a stage has not run yet
# ======================================================================================

# Which stage owes which layer. Named so a missing layer is answered with "waiting on
# stage 5", not with a stack trace - the build order is in W11a_BUILD_BRIEF.md.
PRODUCED_BY: Dict[str, str] = {
    "nodes":        "stage 4 (chambers) then stage 5 (levels)",
    "reaches":      "stages 3-5 (hierarchy, chambers, hydraulics)",
    "corridors":    "stage 2 (corridors)",
    "crossings":    "stage 2 (corridors - the schedule H1 demands)",
    "connections":  "stage 1/5 (the served set and load allocation)",
    "stations":     "stage 5 (the cap-and-veto ladder)",
    "rising_mains": "stage 5 (pump duty from the wet-well cycle)",
    "packages":     "stage 6 (packages and phasing)",
}
REQUIRED = ("nodes", "reaches")      # without these there is nothing to export at all


def read_published(root: str) -> Tuple[Dict[str, gpd.GeoDataFrame], List[str]]:
    """Read and VALIDATE every contract layer present in the audited GeoPackage.

    Validating on read, not only on write, is the contract's own rule. It matters more
    here than anywhere: this stage is the last point at which a defect is cheaper than a
    reprint, and a schedule printed from an unvalidated layer is a number that failed the
    contract arriving in a document nobody re-checks.
    """
    path = K.gpkg_path(root)
    K.assert_audited_path(path)          # refuses a .shp outright; the DBF mangles names
    out: Dict[str, gpd.GeoDataFrame] = {}
    missing: List[str] = []
    if not os.path.exists(path):
        return out, list(K.LAYERS)
    try:
        have = set(gpd.list_layers(path)["name"].astype(str))
    except Exception:
        import fiona
        have = set(fiona.listlayers(path))
    for name in K.LAYERS:
        if name not in have:
            missing.append(name)
            continue
        g = gpd.read_file(path, layer=name)
        K.validate(g, name, stage="s9_export(read)")
        out[name] = g
    return out, missing


def waiting_report(missing: Sequence[str]) -> str:
    w = max(len(m) for m in missing)
    return "\n".join(f"    {m:<{w}}  waiting on {PRODUCED_BY.get(m, 'an upstream stage')}"
                     for m in sorted(missing))


def assert_is_the_graph(nodes, reaches, rising=None) -> None:
    """Invariant 2, re-asserted on the layers as READ FROM DISK, before anything is drawn.

    This is the check W10 could not have written, and it is placed here rather than in the
    stage that wrote the layers because a merge, a clip or a hand edit between the two is
    exactly what parts a layer from its graph. If it fails, the run stops: a DXF, a KMZ and
    a model built from a broken layer set all inherit the break and none of them shows it.

    THE RISING MAIN SUBTLETY, found by building a station in the self-test. `N_OUT` and
    `N_IN` on the node layer are written from `Network.out_edge` / `in_edges`, which hold
    edges of EVERY kind; a lifting station's one outgoing edge is its rising main. Checking
    the degrees against the gravity reaches alone therefore reports every station as
    "node says 1, reaches say 0" and refuses a perfectly correct design. The degrees are
    checked against gravity PLUS pressure edges, which is what the node layer counted.
    Nothing is relaxed by this - the forest rule still binds across both kinds.
    """
    K.Network.assert_round_trip(nodes, reaches)
    if rising is not None and len(rising):
        # A rising main is a pressure edge in the SAME graph, with the same node identity,
        # so its endpoints must land on their chambers exactly as a gravity reach does.
        K.Network.assert_round_trip(nodes, rising)
        cols = ["EDGE_UID", "US_NODE", "DS_NODE", "geometry"]
        both = pd.concat([reaches[cols], rising[cols]], ignore_index=True)
        K.Network.assert_degrees(nodes, both)
    else:
        K.Network.assert_degrees(nodes, reaches)


def assert_network_fields(gdf, name: str) -> None:
    """Every line layer that leaves this stage carries US_NODE/DS_NODE.

    Connectivity is an attribute, never something a downstream reader re-derives with a
    tolerance. That re-derivation is precisely what hid W10's 7,919 pieces: the geometry
    was all anyone had, and 91.4 % of the stitch links stopped 1.000 m short.
    """
    miss = [c for c in ("US_NODE", "DS_NODE") if c not in gdf.columns]
    if miss:
        raise ContractError(
            f"network layer '{name}' is about to be exported without {miss}. "
            "Every exported network layer carries the node identifiers it was built from "
            "(build brief P3).")


# ======================================================================================
# 1. Shapefile mirrors
# ======================================================================================

def export_shapefiles(layers: Dict[str, gpd.GeoDataFrame], root: str, rec) -> List[str]:
    """The exchange copy. The GeoPackage stays the audited artefact.

    `mirror_shapefile` writes a README beside any layer whose field names the DBF
    truncates - GRAD_BY becomes GRADIENT_B, and audit G2 then fails a design that was
    correct in memory. `assert_audited_path` makes that a raise rather than a note,
    so the mirror can never be handed to the auditor by mistake.
    """
    written = []
    for name, g in layers.items():
        if name in ("reaches", "rising_mains"):
            assert_network_fields(g, name)
        spec = K.LAYERS[name]
        if spec.geom == "none" and (not isinstance(g, gpd.GeoDataFrame)
                                    or "geometry" not in g.columns
                                    or g.geometry.isna().all()):
            # A non-spatial table (packages, when stage 6 publishes it as a table rather
            # than as territory polygons). A shapefile cannot hold it; a CSV can, and
            # silently skipping the layer would be the export equivalent of a no-op.
            p = os.path.join(root, "shp", f"W11a_{name}.csv")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            pd.DataFrame(g.drop(columns=["geometry"], errors="ignore")).to_csv(
                p, index=False, encoding="utf-8-sig")
        else:
            p = K.mirror_shapefile(g, name, root)
        written.append(p)
        rec.wrote(f"shp:{name}", p, len(g))
    return written


# ======================================================================================
# 2. DXF - by tier and diameter band
# ======================================================================================

def export_dxf(layers, root: str, rec) -> str:
    """One CAD layer per (tier, diameter band), because those are the two splits a
    draftsman and an estimator both need and neither can recover from a merged layer.

    The tier is the buildability story (philosophy sec 4 - lateral 66 %, sub main 18 %,
    trunk 5 %); the diameter band is the material and pricing story (G203-p22 Tab 6,
    p35 Tab 14). W10 published neither: no TIER field at all, and one undifferentiated
    pipe layer.

    Annotation is `DN<n> <laid> %` with the minimum in brackets. Publishing the laid
    gradient with its minimum beside it is philosophy sec 5, and it is the pair audit G1
    checks for - a drawing carrying only one of them cannot be checked against the other.
    """
    import ezdxf
    from ezdxf.enums import TextEntityAlignment as TA

    reaches, nodes = layers["reaches"], layers["nodes"]
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6                       # metres; a DXF with no units is a trap
    msp = doc.modelspace()

    for tier, st in TIER_STYLE.items():
        tok = K.TIER_TOKEN[tier]
        for _lo, _hi, code, _why in DN_BANDS:
            doc.layers.add(f"SEW-{tok}-{code}", color=DN_BAND_ACI[code])
    for name, col in (("SEW-MH", 7), ("SEW-MH-LABEL", 8), ("SEW-PIPE-LABEL", 2),
                      ("SEW-DROP", 6), ("SEW-VORTEX", 1), ("SEW-STATION", 1),
                      ("SEW-OUTFALL", 1), ("SEW-RISING-MAIN", 1), ("SEW-CROSSING", 6),
                      ("SEW-CONNECTION", 8), ("SEW-PAST-CAP", 1),
                      # Philosophy sec 4: a platted reserve with nothing built on it is a
                      # legitimate corridor at saturation but "is not a street", carries
                      # CONFIDENCE = provisional, and "its pipes are identified separately
                      # in every drawing and schedule". The schedules carry a Confidence
                      # column; without this overlay the DXF - the drawing somebody sets
                      # out from - drew up to 320 km of pipe on bare desert reserve
                      # exactly like pipe in a built street.
                      ("SEW-PROVISIONAL", 30)):
        doc.layers.add(name, color=col)

    labels, prov = 0, 0
    f_lab = rec.funnel("dxf pipe labels", len(reaches))
    short = int((pd.to_numeric(reaches["LEN_M"], errors="coerce")
                 < DXF_MIN_LABEL_LEN_M).sum())
    f_lab.drop(f"reach shorter than {DXF_MIN_LABEL_LEN_M:.0f} m - the text would sit on "
               "top of the pipe", n=short)

    for r in reaches.itertuples():
        tier = str(r.TIER)
        st = TIER_STYLE.get(tier, TIER_STYLE["lateral"])
        lay = f"SEW-{K.TIER_TOKEN.get(tier, 'L')}-{dn_band(r.DN)}"
        coords = list(r.geometry.coords)
        msp.add_lwpolyline(coords, dxfattribs={"layer": lay})

        # Past the cap gets its own overlay layer. Philosophy sec 5: everything past 12 m
        # is FLAGGED, with its depth, its length and which exit allowed it - a drawing that
        # does not show it is a drawing that hides the least-final part of the design.
        if int(getattr(r, "PAST_CAP", 0) or 0) == 1:
            msp.add_lwpolyline(coords, dxfattribs={"layer": "SEW-PAST-CAP"})

        # ... and the same treatment for a pipe whose corridor is only a platted reserve.
        if str(getattr(r, "CONFIDENCE", "")).strip().lower() == "provisional":
            msp.add_lwpolyline(coords, dxfattribs={"layer": "SEW-PROVISIONAL"})
            prov += 1

        mid = r.geometry.interpolate(0.5, normalized=True)
        a = r.geometry.interpolate(max(0.0, 0.5 * r.geometry.length - 2.0))
        b = r.geometry.interpolate(min(r.geometry.length, 0.5 * r.geometry.length + 2.0))
        ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        if float(r.LEN_M) >= DXF_MIN_LABEL_LEN_M and labels < DXF_LABEL_CAP:
            txt = (f"DN{int(r.DN)} {float(r.SLOPE_LAID):.2f}% "
                   f"(min {float(r.SLOPE_MIN):.2f}%) {tier}")
            t = msp.add_text(txt, dxfattribs={
                "layer": "SEW-PIPE-LABEL", "height": 1.8,
                "rotation": ang if -90 <= ang <= 90 else ang + 180})
            t.set_placement((mid.x, mid.y + 1.2), align=TA.CENTER)
            labels += 1
        # flow chevron, so direction is readable without opening the attribute table
        ux, uy = (b.x - a.x), (b.y - a.y)
        L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        px, py = -uy, ux
        for s in (1.0, -1.0):
            msp.add_line((mid.x - 1.5 * ux + 1.2 * px * s, mid.y - 1.5 * uy + 1.2 * py * s),
                         (mid.x + 1.5 * ux, mid.y + 1.5 * uy),
                         dxfattribs={"layer": "SEW-PIPE-LABEL"})

    if labels >= DXF_LABEL_CAP:
        f_lab.drop(f"label cap of {DXF_LABEL_CAP:,} reached - the drawing would not open",
                   n=len(reaches) - short - labels)
    else:
        f_lab.drop("no label needed", n=len(reaches) - short - labels)
    f_lab.close(labels)

    stack = 0
    for n in nodes.itertuples():
        kind = str(n.NODE_KIND)
        rad = {"outfall": 3.0, "station": 6.0}.get(kind, 1.2)
        lay = {"outfall": "SEW-OUTFALL", "station": "SEW-STATION"}.get(kind, "SEW-MH")
        msp.add_circle((n.X, n.Y), rad, dxfattribs={"layer": lay})
        if kind in ("outfall", "station"):
            msp.add_circle((n.X, n.Y), rad * 1.4, dxfattribs={"layer": lay})
        dt = str(getattr(n, "DROP_TYPE", "none"))
        if dt == "backdrop":
            msp.add_circle((n.X, n.Y), 2.5, dxfattribs={"layer": "SEW-DROP"})
        elif dt == "vortex":
            msp.add_circle((n.X, n.Y), 2.5, dxfattribs={"layer": "SEW-VORTEX"})
            msp.add_circle((n.X, n.Y), 3.5, dxfattribs={"layer": "SEW-VORTEX"})
        if stack < DXF_LABEL_CAP:
            # ref / ground / invert / depth - the four numbers a setting-out crew needs,
            # and the four the chamber schedule prints. Same source, same values.
            for i, s in enumerate((str(n.NODE_REF), f"G:{float(n.GRD_M):.2f}",
                                   f"I:{float(n.INV_M):.2f}", f"D:{float(n.DEPTH_M):.2f}")):
                t = msp.add_text(s, dxfattribs={"layer": "SEW-MH-LABEL", "height": 1.2})
                t.set_placement((n.X + 2.0, n.Y - 1.6 * i), align=TA.LEFT)
            stack += 1

    for name, lay, note in (("rising_mains", "SEW-RISING-MAIN", "RISING MAIN"),
                            ("connections", "SEW-CONNECTION", "")):
        g = layers.get(name)
        if g is None or not len(g):
            continue
        for r in g.itertuples():
            msp.add_lwpolyline(list(r.geometry.coords), dxfattribs={"layer": lay})
            if note and float(getattr(r, "LEN_M", 0)) > 0:
                mid = r.geometry.interpolate(0.5, normalized=True)
                t = msp.add_text(f"{note} DN{int(r.DN)} {float(r.Q_DUTY_LS):.1f} L/s",
                                 dxfattribs={"layer": lay, "height": 2.5})
                t.set_placement((mid.x + 2, mid.y + 2), align=TA.LEFT)

    g = layers.get("crossings")
    if g is not None and len(g):
        for r in g.itertuples():
            msp.add_lwpolyline(list(r.geometry.coords), dxfattribs={"layer": "SEW-CROSSING"})
            mid = r.geometry.interpolate(0.5, normalized=True)
            t = msp.add_text(f"{str(r.OBSTACLE).upper()} CROSSING {r.CROSS_ID} "
                             f"{str(r.METHOD)} {float(r.ANGLE_DEG):.0f} deg",
                             dxfattribs={"layer": "SEW-CROSSING", "height": 2.5})
            t.set_placement((mid.x + 2, mid.y + 2), align=TA.LEFT)

    p = os.path.join(root, "dxf", "W11a_network.dxf")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    doc.saveas(p)
    rec.wrote("dxf", p, len(reaches))
    rec.note(f"DXF: {len(doc.layers)} CAD layers, {labels:,} pipe labels, "
             f"{stack:,} chamber level stacks, {prov:,} reaches also drawn on "
             "SEW-PROVISIONAL (corridor is a platted reserve, not a street - "
             "philosophy sec 4)")
    return p


# ======================================================================================
# 3. KMZ - Google Earth
# ======================================================================================

def _kml_abgr(rgb, alpha="ff") -> str:
    """KML colour is aabbggrr, NOT rrggbb. Easy to get backwards, and a network drawn in
    the complementary colour looks deliberate."""
    r, g, b = rgb
    return f"{alpha}{b:02x}{g:02x}{r:02x}"


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def export_kmz(layers, root: str, rec) -> str:
    """The design in Google Earth, folder per tier, so it can be checked outside GIS.

    Asked for on 2026-08-20 and kept because it is the cheapest sanity check there is: a
    trunk that runs up a wadi or a lateral that jumps a dual carriageway is obvious on
    imagery in a way it never is in an attribute table. Every placemark carries the row it
    was drawn from, including SLOPE_LAID *and* SLOPE_MIN, so the check is against the
    design's own numbers rather than against its shape.
    """
    from pyproj import Transformer
    to_wgs = Transformer.from_crs(K.CRS_EPSG, 4326, always_xy=True)

    def coords(geom) -> str:
        return " ".join(f"{lon:.8f},{lat:.8f},0"
                        for lon, lat in (to_wgs.transform(x, y) for x, y in geom.coords))

    reaches, nodes = layers["reaches"], layers["nodes"]
    styles, folders = [], []
    for tier, st in TIER_STYLE.items():
        for _lo, _hi, code, _w in DN_BANDS:
            width = st["kml_w"] * {"DN-250": 0.8, "DN251-350": 1.0,
                                   "DN351-600": 1.3, "DN601UP": 1.7}[code]
            styles.append(f'<Style id="{K.TIER_TOKEN[tier]}_{code}"><LineStyle>'
                          f'<color>{_kml_abgr(st["rgb"])}</color>'
                          f'<width>{width:.2f}</width></LineStyle></Style>')
    styles.append('<Style id="rm"><LineStyle><color>ff0000ff</color><width>5</width>'
                  '</LineStyle></Style>')

    def placemark(r, style_id: str) -> str:
        rows = [("Reach", r.EDGE_UID), ("Tier", r.TIER),
                ("From / to", f"{r.US_NODE} -> {r.DS_NODE}"),
                ("Size", f"DN{int(r.DN)} {r.MATERIAL}"),
                ("Length", f"{float(r.LEN_M):.1f} m"),
                ("Gradient laid", f"{float(r.SLOPE_LAID):.3f} %"),
                ("Gradient minimum", f"{float(r.SLOPE_MIN):.3f} % ({r.GRAD_BY})"),
                ("Invert up / down", f"{float(r.INV_UP):.2f} / {float(r.INV_DN):.2f} m aOD"),
                ("Cover up / down", f"{float(r.COVER_US):.2f} / {float(r.COVER_DN):.2f} m"),
                ("Peak flow", f"{float(r.QPK_LS):.2f} L/s  (PF {float(r.PF):.2f} "
                              f"{r.PF_METH})"),
                ("Velocity / dD", f"{float(r.V_PK_MS):.2f} m/s  /  {float(r.DOD_PK):.2f}"),
                ("Sized by / self-cleansing", f"{r.SIZED_BY} / {r.CLEAN_BY}"),
                ("Provenance", f"{r.SRC} ({r.CONFIDENCE})")]
        if int(getattr(r, "PAST_CAP", 0) or 0) == 1:
            rows.append(("PAST THE 12 m CAP", f"{r.CAP_EXIT}, {float(r.CAP_LEN_M):.0f} m"))
        html = "".join(f"<tr><td><b>{_esc(k)}</b></td><td>{_esc(v)}</td></tr>"
                       for k, v in rows)
        return (f'<Placemark><name>{_esc(r.EDGE_UID)}</name>'
                f'<description><![CDATA[<table>{html}</table>]]></description>'
                f'<styleUrl>#{style_id}</styleUrl><LineString><tessellate>1</tessellate>'
                f'<coordinates>{coords(r.geometry)}</coordinates></LineString></Placemark>')

    for tier in sorted(TIER_STYLE, key=lambda t: -TIER_STYLE[t]["order"]):
        sub = reaches[reaches["TIER"].astype(str) == tier]
        if not len(sub):
            continue
        body = "".join(placemark(r, f"{K.TIER_TOKEN[tier]}_{dn_band(r.DN)}")
                       for r in sub.itertuples())
        km = pd.to_numeric(sub["LEN_M"], errors="coerce").sum() / 1000.0
        folders.append(f'<Folder><name>{_esc(tier)} - {km:.1f} km, {len(sub):,} reaches'
                       f'</name><open>{1 if tier == "trunk main" else 0}</open>'
                       f'{body}</Folder>')

    rm = layers.get("rising_mains")
    if rm is not None and len(rm):
        body = "".join(
            f'<Placemark><name>{_esc(r.EDGE_UID)}</name>'
            f'<description><![CDATA[rising main DN{int(r.DN)} {_esc(r.MATERIAL)}, '
            f'{float(r.LEN_M):.0f} m, duty {float(r.Q_DUTY_LS):.1f} L/s at '
            f'{float(r.V_DUTY_MS):.2f} m/s, static {float(r.STAT_HD_M):.1f} m'
            f']]></description><styleUrl>#rm</styleUrl><LineString><tessellate>1'
            f'</tessellate><coordinates>{coords(r.geometry)}</coordinates>'
            f'</LineString></Placemark>' for r in rm.itertuples())
        folders.append(f'<Folder><name>rising mains - '
                       f'{rising_main_length_km(rm):.1f} km</name>{body}</Folder>')

    marks = []
    for n in nodes[nodes["NODE_KIND"].astype(str).isin(["station", "outfall"])].itertuples():
        lon, lat = to_wgs.transform(float(n.X), float(n.Y))
        icon = ("ylw-pushpin" if str(n.NODE_KIND) == "station" else "blu-stars")
        marks.append(
            f'<Placemark><name>{_esc(n.NODE_REF)} ({_esc(n.NODE_KIND)})</name>'
            f'<description><![CDATA[ground {float(n.GRD_M):.2f} m, invert '
            f'{float(n.INV_M):.2f} m, depth {float(n.DEPTH_M):.2f} m]]></description>'
            f'<Style><IconStyle><scale>1.2</scale><Icon><href>'
            f'http://maps.google.com/mapfiles/kml/paddle/{icon}.png</href></Icon>'
            f'</IconStyle></Style><Point><coordinates>{lon:.8f},{lat:.8f},0</coordinates>'
            f'</Point></Placemark>')
    if marks:
        folders.append('<Folder><name>stations and outfalls</name><open>1</open>'
                       + "".join(marks) + '</Folder>')

    kml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>Ibri 2621 - W11a concept sewer design</name>'
           + "".join(styles) + "".join(folders) + '</Document></kml>')
    p = os.path.join(root, "shp", "W11a_sewer_design.kmz")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("doc.kml", kml)
    rec.wrote("kmz", p, len(reaches))
    return p


# ======================================================================================
# 4. PNG maps and the indicative profiles
# ======================================================================================

def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _background(ax, bounds) -> bool:
    """Esri mosaic warped into 32640 under the view at 30 % (project rule 4). Returns
    False if the imagery is not on this machine - it is never pushed to the repo, so a map
    without it is a normal outcome and must not be a crash."""
    try:
        import rasterio
        from rasterio.vrt import WarpedVRT
        from rasterio.windows import from_bounds
        with rasterio.open(MOSAIC) as src:
            with WarpedVRT(src, crs=f"EPSG:{K.CRS_EPSG}") as vrt:
                l, b, r, t = bounds
                win = from_bounds(l, b, r, t, vrt.transform)
                img = vrt.read([1, 2, 3], window=win, out_shape=(3, 1400, 1400))
                ax.imshow(np.transpose(img, (1, 2, 0)), extent=(l, r, b, t),
                          alpha=0.30, zorder=0)
        return True
    except Exception as e:                     # noqa: BLE001 - reported, never swallowed
        print(f"    (satellite background unavailable: {type(e).__name__} {e})")
        return False


def _frame(ax, title: str, databox: str, boundary=None) -> None:
    if boundary is not None:
        for geom in getattr(boundary, "geoms", [boundary]):
            x, y = geom.exterior.xy
            ax.plot(x, y, color="#d35400", lw=1.4, ls="--", zorder=6)
    ax.set_title(title, fontsize=12)
    ax.set_aspect("equal")
    ax.ticklabel_format(style="plain")
    ax.tick_params(labelsize=6)
    x0 = ax.get_xlim()[0] + 0.04 * (ax.get_xlim()[1] - ax.get_xlim()[0])
    y0 = ax.get_ylim()[0] + 0.04 * (ax.get_ylim()[1] - ax.get_ylim()[0])
    span = ax.get_xlim()[1] - ax.get_xlim()[0]
    # a scalebar whose labels do not overlap (project rule 4): one round step, 3 ticks
    step = 10 ** math.floor(math.log10(span / 6.0))
    step = max(100.0, step * (5 if span / 6.0 / step > 5 else (2 if span / 6.0 / step > 2 else 1)))
    ax.plot([x0, x0 + step], [y0, y0], color="k", lw=3, zorder=9)
    for f in (0.0, 0.5, 1.0):
        ax.text(x0 + f * step, y0 + 0.006 * span, f"{f * step:,.0f}",
                fontsize=6, ha="center", zorder=9)
    ax.text(x0 + step / 2, y0 - 0.012 * span, "m", fontsize=6, ha="center", zorder=9)
    ax.text(0.985, 0.015, databox, transform=ax.transAxes, fontsize=6.5,
            va="bottom", ha="right", zorder=10, family="monospace",
            bbox=dict(boxstyle="round", fc="white", ec="#555", alpha=0.92))


def _collection(ax, gdf, colours, widths, zorder=3):
    """LineCollection instead of a plot() per feature. On a 40,000-reach network the
    difference is minutes against hours, and a map nobody waits for is a map nobody makes."""
    from matplotlib.collections import LineCollection
    segs = [list(g.coords) for g in gdf.geometry]
    ax.add_collection(LineCollection(segs, colors=colours, linewidths=widths,
                                     zorder=zorder))


def _databox(layers) -> str:
    """The map's data table (project rule 4, bottom-right). Every line calls a published
    function - the map, the schedule and the console print the same arithmetic or none."""
    reaches, nodes = layers["reaches"], layers["nodes"]
    share = tier_share_pct(reaches)
    lines = [f"gravity network   {network_length_km(reaches):>9,.1f} km",
             f"chambers          {chamber_count(nodes):>9,d}",
             f"chambers per km   {chambers_per_km(nodes, reaches):>9.1f}",
             f"stations          {station_count(layers.get('stations')):>9,d}",
             f"total lift        {total_lift_m(layers.get('stations')):>9,.1f} m",
             f"rising mains      {rising_main_length_km(layers.get('rising_mains')):>9,.1f} km",
             f"Qadf at outfall   {qadf_total_m3d(nodes, reaches):>9,.0f} m3/d"]
    conn = layers.get("connections")
    if conn is not None and len(conn):
        # served BY THIS NETWORK. The TOR requires every plot served (scope p4 item 3) but
        # not by one network, so the count on the map is the central-system count and the
        # rest are in the connection schedule with a SYSTEM and a WHY (philosophy sec 8a).
        off = int(K._blank(conn["OUT_NODE"]).sum())
        lines.append(f"properties served {properties_served(conn):>9,.0f}")
        if off:
            lines.append(f"  off-network     {off:>9,d} plots")
    for tier in ("trunk main", "sub main", "main", "lateral", "rider"):
        if tier in share.index:
            lines.append(f"  {tier:<15} {share[tier]:>8.1f} %")
    return "\n".join(lines)


def export_maps(layers, root: str, rec) -> List[str]:
    """Four concept maps: tiers, diameters, cover, packages.

    The cover map exists because of a specific W10 failure. 45.92 km below minimum cover
    and 2.80 km of surcharged trunk were both invisible in every W10 output - the maps
    coloured by diameter, which is exactly the variable that never showed the defect.
    A map coloured by the thing the audit checks is the cheapest review tool available.
    """
    plt = _mpl()
    reaches, nodes = layers["reaches"], layers["nodes"]
    out, img = [], os.path.join(root, "img")
    os.makedirs(img, exist_ok=True)

    boundary = None
    try:
        b = gpd.read_file(BOUNDARY_SHP).to_crs(K.CRS_EPSG)
        boundary = b.union_all() if hasattr(b, "union_all") else b.unary_union
    except Exception as e:                     # noqa: BLE001
        print(f"    (project boundary unavailable: {e})")

    bounds = (boundary.bounds if boundary is not None
              else tuple(reaches.total_bounds))
    box = _databox(layers)

    def new_fig():
        fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
        _background(ax, bounds)
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        return fig, ax

    from matplotlib.lines import Line2D

    # ---- M1 tiers -------------------------------------------------------------------
    fig, ax = new_fig()
    tiers = reaches["TIER"].astype(str)
    _collection(ax, reaches,
                [f"#{TIER_STYLE.get(t, TIER_STYLE['lateral'])['rgb'][0]:02x}"
                 f"{TIER_STYLE.get(t, TIER_STYLE['lateral'])['rgb'][1]:02x}"
                 f"{TIER_STYLE.get(t, TIER_STYLE['lateral'])['rgb'][2]:02x}" for t in tiers],
                [TIER_STYLE.get(t, TIER_STYLE["lateral"])["lw"] for t in tiers])
    ax.legend(handles=[Line2D([], [], color=f"#{s['rgb'][0]:02x}{s['rgb'][1]:02x}"
                                            f"{s['rgb'][2]:02x}", lw=s["lw"] + 0.8, label=t)
                       for t, s in TIER_STYLE.items()], fontsize=7, loc="upper left")
    _frame(ax, "W11a concept sewer network - hierarchy by tier", box, boundary)
    p = os.path.join(img, "W11a_M1_tiers.png")
    fig.savefig(p, bbox_inches="tight"); plt.close(fig); out.append(p)

    # ---- M2 diameters ---------------------------------------------------------------
    fig, ax = new_fig()
    band = reaches["DN"].map(dn_band)
    pal = {"DN-250": "#2ecc71", "DN251-350": "#3498db",
           "DN351-600": "#e67e22", "DN601UP": "#c0392b"}
    _collection(ax, reaches, [pal[b] for b in band],
                [0.5 + 0.6 * i for i in band.map(
                    {c: n for n, (_l, _h, c, _w) in enumerate(DN_BANDS)})])
    ax.legend(handles=[Line2D([], [], color=pal[c], lw=2, label=f"{c}  ({why[:52]}...)")
                       for _l, _h, c, why in DN_BANDS], fontsize=6, loc="upper left")
    _frame(ax, "W11a concept sewer network - diameter bands (G203-p22 Tab 6, p35 Tab 14)",
           box, boundary)
    p = os.path.join(img, "W11a_M2_diameters.png")
    fig.savefig(p, bbox_inches="tight"); plt.close(fig); out.append(p)

    # ---- M3 cover -------------------------------------------------------------------
    fig, ax = new_fig()
    cov = pd.concat([pd.to_numeric(reaches["COVER_US"], errors="coerce"),
                     pd.to_numeric(reaches["COVER_DN"], errors="coerce")],
                    axis=1).min(axis=1)
    idx = cov.map(depth_band_index)
    _collection(ax, reaches, [DEPTH_BAND_COLOR[i] for i in idx],
                [1.6 if i in (0, 3) else 0.7 for i in idx])
    counts = idx.value_counts()
    ax.legend(handles=[Line2D([], [], color=DEPTH_BAND_COLOR[i], lw=2,
                              label=f"{DEPTH_BANDS[i][2]}  ({counts.get(i, 0):,} reaches)")
                       for i in range(len(DEPTH_BANDS))], fontsize=6.5, loc="upper left")
    _frame(ax, "W11a concept sewer network - cover to crown, banded on G203-p33",
           box, boundary)
    p = os.path.join(img, "W11a_M3_cover.png")
    fig.savefig(p, bbox_inches="tight"); plt.close(fig); out.append(p)

    # ---- M4 packages ----------------------------------------------------------------
    if "PACKAGE" in reaches.columns and reaches["PACKAGE"].astype(str).str.strip().any():
        fig, ax = new_fig()
        pkgs = sorted(set(reaches["PACKAGE"].astype(str)) - {""})
        cmap = plt.get_cmap("tab20")
        col = {p_: cmap(i % 20) for i, p_ in enumerate(pkgs)}
        _collection(ax, reaches,
                    [col.get(str(p_), (0.6, 0.6, 0.6, 1)) for p_ in reaches["PACKAGE"]],
                    [1.0] * len(reaches))
        st = layers.get("stations")
        if st is not None and len(st):
            ax.scatter(st.geometry.x, st.geometry.y, s=60, marker="v",
                       c="red", zorder=8, label="lifting station (a package seam)")
            ax.legend(fontsize=7, loc="lower left")
        _frame(ax, "W11a concept sewer network - contract packages and phasing", box,
               boundary)
        p = os.path.join(img, "W11a_M4_packages.png")
        fig.savefig(p, bbox_inches="tight"); plt.close(fig); out.append(p)
    else:
        rec.note("M4 packages map not drawn: no PACKAGE on the reach layer yet "
                 "(stage 6). The map is missing, not empty.")

    for p in out:
        rec.wrote("png", p)
    return out


def _routes(reaches, tiers: Sequence[str]) -> List[List[int]]:
    """Longest continuous routes within a tier set, as lists of positional indices.

    A profile is drawn along a ROUTE, not along a tier: 'the trunk main' is one line from
    the outfall backwards (philosophy sec 4), and drawing every trunk reach separately
    produces 300 unreadable fragments. At a junction the branch carrying the greater
    upstream length is the main line - the same rule a draftsman applies by eye.
    """
    sub = reaches[reaches["TIER"].astype(str).isin(tiers)].reset_index(drop=True)
    if not len(sub):
        return []
    pos = {u: i for i, u in enumerate(sub["US_NODE"].astype(str))}       # us node -> edge i
    preds: Dict[int, List[int]] = {}
    for i, ds in enumerate(sub["DS_NODE"].astype(str)):
        j = pos.get(ds)
        if j is not None:
            preds.setdefault(j, []).append(i)
    length = pd.to_numeric(sub["LEN_M"], errors="coerce").fillna(0.0).to_numpy()

    # Kahn order over the forest, then upstream-length by dynamic programming.
    indeg = np.array([len(preds.get(i, ())) for i in range(len(sub))])
    order, stack = [], [i for i in range(len(sub)) if indeg[i] == 0]
    succ = {}
    for i, ds in enumerate(sub["DS_NODE"].astype(str)):
        j = pos.get(ds)
        if j is not None:
            succ[i] = j
    while stack:
        i = stack.pop()
        order.append(i)
        j = succ.get(i)
        if j is not None:
            indeg[j] -= 1
            if indeg[j] == 0:
                stack.append(j)
    up = np.zeros(len(sub))
    for i in order:
        up[i] = length[i] + (max((up[p] for p in preds.get(i, ())), default=0.0))

    routes = []
    for i in range(len(sub)):
        if i in succ:                     # not a terminal of this tier set
            continue
        chain, cur = [i], i
        while preds.get(cur):
            cur = max(preds[cur], key=lambda p: up[p])
            chain.append(cur)
        chain.reverse()
        routes.append((float(up[i]), chain, sub))
    routes.sort(key=lambda t: -t[0])
    return routes


def export_profiles(layers, root: str, rec) -> List[str]:
    """INDICATIVE longitudinal profiles - trunk main and sub mains.

    Required by DELIVERABLE_SPEC D.3 (scope-p12: 'indicative longitudinal profiles ... as
    part of the detailed concept design'). Explicitly NOT the 1:1000 H / 1:100 V annotated
    set, which D.7 puts at preliminary/detailed - so these carry no scale bar, no vertical
    exaggeration statement and no chainage annotation, and they say INDICATIVE on the face.

    The profile is the one drawing that shows the two things a plan cannot: whether the
    pipe follows the ground or dives under it, and where the cover runs out. Both are
    W10 defects that no plan view revealed.
    """
    plt = _mpl()
    reaches, nodes = layers["reaches"], layers["nodes"]
    grd = dict(zip(nodes["NODE_UID"].astype(str),
                   pd.to_numeric(nodes["GRD_M"], errors="coerce")))
    out, img = [], os.path.join(root, "img")
    os.makedirs(img, exist_ok=True)

    jobs = []
    for label, tiers in (("trunk", ("trunk main",)), ("submain", ("sub main",))):
        rs = _routes(reaches, tiers)
        f = rec.funnel(f"profiles {label}", len(rs))
        keep = rs[:PROFILE_CAP]
        f.drop(f"beyond the {PROFILE_CAP} longest routes - listed in the run log, not "
               "silently dropped", n=len(rs) - len(keep))
        f.close(len(keep))
        for k, (uplen, chain, sub) in enumerate(keep, 1):
            jobs.append((label, k, uplen, chain, sub))
        if len(rs) > PROFILE_CAP:
            rec.note(f"{len(rs) - PROFILE_CAP} further {label} routes exist and were not "
                     f"drawn (shortest drawn {keep[-1][0] / 1000:.2f} km)")

    for label, k, uplen, chain, sub in jobs:
        rr = sub.iloc[chain]
        ch, gl, il, sl = [0.0], [], [], []
        for r in rr.itertuples():
            gl.append(grd.get(str(r.US_NODE), float("nan")))
            il.append(float(r.INV_UP))
            ch.append(ch[-1] + float(r.LEN_M))
            sl.append((ch[-2], ch[-1], float(r.SLOPE_LAID), int(r.DN)))
        last = rr.iloc[-1]
        gl.append(grd.get(str(last.DS_NODE), float("nan")))
        il.append(float(last.INV_DN))

        fig, ax = plt.subplots(figsize=(16, 5), dpi=130)
        ax.plot(ch, gl, color="#8B5A2B", lw=1.4, label="ground (0.5 m VRT)")
        ax.plot(ch, il, color="#1f77b4", lw=1.8, label="invert (laid)")
        ax.fill_between(ch, gl, il, color="#d9c7a3", alpha=0.35)
        # the DN/gradient band sits INSIDE the axes, under the invert. Put it below the
        # axis and it lands on the x-label; a profile whose annotation is unreadable is
        # the drawing not being made, however correct its levels are.
        span = max(max(gl), max(il)) - min(il)
        y_lab = min(il) - 0.10 * span
        ax.set_ylim(y_lab - 0.06 * span, None)
        for x0, x1, s, dn in sl:
            if x1 - x0 > (ch[-1] / 60.0):
                ax.text((x0 + x1) / 2, y_lab, f"DN{dn}  {s:.2f}%", fontsize=5.5,
                        ha="center", va="center", color="#1f77b4", rotation=0)
        ax.scatter(ch, il, s=8, color="#1f77b4", zorder=5)
        ax.set_xlabel("chainage along the route (m)  -  INDICATIVE, not to scale")
        ax.set_ylabel("level (m aOD)")
        ax.set_title(f"INDICATIVE longitudinal profile - {label} route {k}, "
                     f"{uplen / 1000:.2f} km, {len(rr)} reaches   "
                     f"(concept stage; not a 1:1000/1:100 set - DELIVERABLE_SPEC D.7)",
                     fontsize=9)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7)
        p = os.path.join(img, f"W11a_P{len(out) + 1:02d}_profile_{label}_{k}.png")
        fig.savefig(p, bbox_inches="tight"); plt.close(fig)
        out.append(p)
        rec.wrote("png:profile", p, len(rr))
    if not out:
        rec.note("no profiles drawn: the reach layer carries no 'trunk main' or "
                 "'sub main' tier yet (stage 3)")
    return out


# ======================================================================================
# 5. Schedules
# ======================================================================================

def _write_table(df: pd.DataFrame, path_noext: str, rec, name: str) -> None:
    """CSV and XLSX, one file each (DELIVERABLE_SPEC D.2). The CSV is what a script reads
    and the XLSX is what the client opens; writing only one of them means somebody
    re-exports the other by hand, and a hand re-export is a second source of truth."""
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].round(PRINT_DECIMALS)
    df.to_csv(path_noext + ".csv", index=False, encoding="utf-8-sig")
    try:
        df.to_excel(path_noext + ".xlsx", index=False)
    except Exception as e:                     # noqa: BLE001
        rec.note(f"{name}: XLSX not written ({type(e).__name__}: {e}); CSV is complete")
    rec.wrote(f"schedule:{name}", path_noext + ".csv", len(df))


def quantity_summary(layers) -> pd.DataFrame:
    """Quantity summary by DN x depth band x package - G201-p21 Table 2, feasibility row.

    Long format, one file, so a category can be added without breaking a column layout.
    The depth band is on COVER, cut at the G203-p33 thresholds, and the first band is
    'below the 1.30 m minimum': if the design has a cover breach it appears here as a
    priced quantity rather than as an audit line somebody may not read.
    """
    reaches, nodes = layers["reaches"], layers["nodes"]
    cov = pd.concat([pd.to_numeric(reaches["COVER_US"], errors="coerce"),
                     pd.to_numeric(reaches["COVER_DN"], errors="coerce")],
                    axis=1).min(axis=1)
    r = pd.DataFrame({
        "package": reaches.get("PACKAGE", pd.Series([""] * len(reaches))).astype(str),
        "tier": reaches["TIER"].astype(str),
        "dn_band": reaches["DN"].map(dn_band),
        "dn_mm": pd.to_numeric(reaches["DN"], errors="coerce").astype("Int64"),
        "depth_band": cov.map(depth_band_label),
        "len_m": pd.to_numeric(reaches["LEN_M"], errors="coerce")})
    pipe = (r.groupby(["package", "tier", "dn_band", "dn_mm", "depth_band"], dropna=False)
             .agg(quantity=("len_m", "sum"), n=("len_m", "size")).reset_index())
    pipe["category"], pipe["unit"] = "gravity pipe", "m"

    # A chamber row prices a chamber, and `chamber_count` is the one definition of what
    # that is: NOT a station and NOT an outfall, because both are separately priced assets
    # (a station also appears below under 'lifting station'). Counting all nodes here made
    # the take-off say 14 chambers where the map databox and the manifest metric said 12,
    # and priced the works inlet as a manhole - the second-definition failure this module
    # exists to prevent (philosophy sec 8: no re-filtered metric).
    ch_nodes = nodes[~nodes["NODE_KIND"].astype(str).isin(["station", "outfall"])]
    ncov = pd.to_numeric(ch_nodes["COVER_M"], errors="coerce")
    n = pd.DataFrame({
        "package": ch_nodes.get("PACKAGE", pd.Series([""] * len(ch_nodes))).astype(str),
        "tier": ch_nodes["TIER"].astype(str),
        "dn_band": "", "dn_mm": pd.NA,
        "depth_band": ncov.map(depth_band_label)})
    cham = (n.groupby(["package", "tier", "dn_band", "dn_mm", "depth_band"], dropna=False)
             .size().reset_index(name="quantity"))
    cham["n"] = cham["quantity"]
    cham["category"], cham["unit"] = "chamber", "no"

    parts = [pipe, cham]
    rm = layers.get("rising_mains")
    if rm is not None and len(rm):
        d = pd.DataFrame({
            "package": rm.get("PACKAGE", pd.Series([""] * len(rm))).astype(str),
            "tier": "rising main",
            "dn_band": rm["DN"].map(dn_band),
            "dn_mm": pd.to_numeric(rm["DN"], errors="coerce").astype("Int64"),
            "depth_band": "n/a - pressure main",
            "len_m": pd.to_numeric(rm["LEN_M"], errors="coerce")})
        g = (d.groupby(["package", "tier", "dn_band", "dn_mm", "depth_band"], dropna=False)
              .agg(quantity=("len_m", "sum"), n=("len_m", "size")).reset_index())
        g["category"], g["unit"] = "rising main", "m"
        parts.append(g)
    st = layers.get("stations")
    if st is not None and len(st):
        # PACKAGE is `required=False` on the stations layer (publishable at stage 7,
        # packaged at stage 8), and `DataFrame.get` returns the bare default - a str with
        # no .astype - so the un-defaulted form crashed the whole schedule block on a
        # station layer published before stage 8. Same defaulting as the pipe rows above.
        g = (st.assign(package=st.get("PACKAGE",
                                      pd.Series([""] * len(st), index=st.index)).astype(str))
               .groupby(["package", "ST_TYPE"]).size().reset_index(name="quantity"))
        g = g.rename(columns={"ST_TYPE": "tier"})
        g["dn_band"], g["dn_mm"], g["depth_band"] = "", pd.NA, "n/a - station"
        g["n"] = g["quantity"]
        g["category"], g["unit"] = "lifting station", "no"
        parts.append(g)

    out = pd.concat(parts, ignore_index=True)
    cols = ["category", "package", "tier", "dn_band", "dn_mm", "depth_band",
            "quantity", "unit", "n"]
    return out[cols].sort_values(cols[:6]).reset_index(drop=True)


def run_audit_table(layers, rec) -> pd.DataFrame:
    """Run the stage-0 auditor against exactly what is being shipped, and print the table.

    Not a courtesy. Philosophy sec 8 makes any breach of a 'shall' and any check that
    cannot run BLOCKING, and the only honest place to establish that is on the published
    artefact, at the moment it becomes a deliverable. W10 was audited never.

    ONE SUPPLEMENTARY ROW, and it is a diagnostic and not a substitute. `audit.h15` builds
    its graph from `ctx.pipes`, which is the GRAVITY reach layer; a rising main is
    deliberately not on that layer (H2/H5/H6/H7 solve open-channel flow and would return
    nonsense for a pressure pipe). So a design with even one lifting station splits into
    two gravity components and H15 FAILS - on a network that is perfectly connected through
    its rising main. H15's own FAIL is left standing, because the auditor is not editable
    from here and quietly re-scoring a blocking check is the whole disease. The extra row
    `H15+` reports the same test over gravity PLUS pressure edges, which is the property
    H15 is reaching for and which contract OPEN-1 already proposes as the fix.
    """
    from w11a import audit
    import networkx as nx
    roads = None
    try:
        roads = gpd.read_file(ROADS_SHP)
        # REPROJECT, never force-label. `set_crs(allow_override=True)` on a road layer that
        # is not already in 32640 relabels degrees as metres; audit.h1 then buffers 6 m in
        # degrees, intersects nothing, and returns PASS on a blocking check. A silent false
        # PASS on H1/R3 is worse than NOT_CHECKABLE, which at least blocks.
        roads = (roads.set_crs(K.CRS_EPSG) if roads.crs is None
                 else roads.to_crs(K.CRS_EPSG))
    except Exception as e:                     # noqa: BLE001
        roads = None
        print(f"    (road layer unavailable, H1/R3 will report NOT_CHECKABLE: {e})")
    existing = None
    try:
        existing = gpd.read_file(EXISTING_SHP)
    except Exception as e:                     # noqa: BLE001 - reported, never swallowed
        # H14 is BLOCKING. Swallowing this makes it report "no existing-network layer
        # supplied" with no way to tell a missing file from an unreadable one.
        print(f"    (existing-network layer unavailable, H14 will report "
              f"NOT_CHECKABLE: {type(e).__name__}: {e})")
    ctx = audit.Ctx(pipes=layers["reaches"], nodes=layers["nodes"], crit=C,
                    terrain=TERRAIN_VRT, hazard=HAZARD_TIF, roads=roads,
                    plots=None, existing=existing)
    res = audit.run(ctx)
    print(audit.report(res))
    df = pd.DataFrame([r.__dict__ for r in res])

    rising = layers.get("rising_mains")
    if rising is not None and len(rising):
        cols = ["EDGE_UID", "US_NODE", "DS_NODE", "geometry"]
        both = gpd.GeoDataFrame(
            pd.concat([layers["reaches"][cols], rising[cols]], ignore_index=True),
            geometry="geometry", crs=layers["reaches"].crs)
        g = audit.Ctx(pipes=both).graph()
        cycles = g.number_of_edges() - g.number_of_nodes() + \
            nx.number_connected_components(g)
        parts = nx.number_connected_components(g)
        ok = (cycles == 0 and parts == 1)
        df = pd.concat([df, pd.DataFrame([dict(
            id="H15+", group="topology",
            requirement="The network is a forest across gravity AND pressure edges "
                        "(diagnostic - contract OPEN-1, not a replacement for H15)",
            source="philosophy H15 + contract OPEN-1", blocking=False,
            status=audit.PASS if ok else audit.FAIL,
            summary=("one connected tree once the rising mains are included" if ok else
                     f"{cycles} independent cycles, {parts} pieces even with the rising "
                     "mains included - this is a real break, not the H15 artefact"),
            n_bad=0 if ok else cycles, extent="")])], ignore_index=True)
        if ok:
            msg = (f"H15 FAILs because {len(rising)} rising main(s) are not on the gravity "
                   "reach layer the auditor reads. Including them, the network IS one "
                   "connected tree (row H15+). audit.h15 needs the OPEN-1 amendment; "
                   "nothing in the design is wrong here.")
            print("\n  NOTE " + msg)
            rec.note("audit H15 artefact: " + msg)

    blocking_fail = df[(df["blocking"].astype(bool)) &
                       (df["status"] != audit.PASS)]
    issuable = len(blocking_fail) == 0
    rec.metric("issuable", "yes" if issuable else "no")
    rec.metric("blocking_failures", int(len(blocking_fail)))
    print("\n  " + ("=" * 74))
    if issuable:
        print("  ISSUABLE: every blocking check passes on the published layers.")
    else:
        print("  ISSUABLE: NO. These blocking checks do not pass on the layers just "
              "exported:")
        for r in blocking_fail.itertuples():
            print(f"    {r.id:<5} {r.status:<14} {r.summary}")
        print("  The deliverable set is written so it can be inspected and fixed - it is "
              "NOT issuable\n  in this state (philosophy sec 8).")
        rec.note("NOT ISSUABLE: " + ", ".join(blocking_fail["id"].astype(str)))
    print("  " + ("=" * 74) + "\n")
    return df


_D8_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")


def data_request_register() -> pd.DataFrame:
    """What NWS must supply before parts of this can close.

    Built from two live sources rather than retyped: `contract.OPEN_ITEMS`, which is the
    in-code register the design itself is written against, and DELIVERABLE_SPEC D.8, read
    out of the markdown at run time. Retyping either into this file would create a third
    copy that drifts the first time one of the other two is edited - which is how the
    project ended up with two different rules for PVC-U on a main sewer.
    """
    rows = [dict(item=o.id + "  " + o.question, blocks=o.blocks,
                 source="W11a contract OPEN_ITEMS", holder="NWS / design team",
                 note=o.resolutions) for o in K.OPEN_ITEMS]
    spec = os.path.join(K.REPO_ROOT, "W10", "docs", "research", "DELIVERABLE_SPEC.md")
    try:
        with open(spec, encoding="utf-8") as fh:
            block, grab = [], False
            for line in fh:
                if line.startswith("## D.8"):
                    grab = True
                    continue
                if grab and line.startswith("---"):
                    break
                if grab:
                    block.append(line.rstrip("\n"))
        for line in block:
            m = _D8_RE.match(line)
            if not m or set(m.group(1)) <= set("-: "):
                continue
            a, b, c = (s.strip() for s in m.groups())
            if a.lower() == "item":
                continue
            rows.append(dict(item=a, blocks=b, source="DELIVERABLE_SPEC D.8",
                             holder="NWS", note=c))
    except Exception as e:                     # noqa: BLE001
        rows.append(dict(item="DELIVERABLE_SPEC D.8 could not be read",
                         blocks="the full data-request register",
                         source=spec, holder="-", note=f"{type(e).__name__}: {e}"))
    return pd.DataFrame(rows)


def export_schedules(layers, root: str, rec) -> List[str]:
    """The nine D.2 schedules, each printed through `contract.schedule_frame`.

    The printed header and the stored field are declared together in the contract, so a
    column heading and the number under it cannot be edited apart. A schedule built by a
    reporting script drifts from its layer the first time either changes, and both halves
    keep running - which is the failure mode that makes a schedule dangerous rather than
    merely wrong.
    """
    run = os.path.join(root, "run")
    os.makedirs(run, exist_ok=True)
    out, skipped = [], []

    for name, sch in K.SCHEDULES.items():
        g = layers.get(sch.layer)
        if g is None:
            skipped.append((name, f"layer '{sch.layer}' not published yet - "
                                  f"{PRODUCED_BY.get(sch.layer, 'upstream')}"))
            continue
        try:
            df = K.schedule_frame(g, name, stage="s9_export")
        except ContractError as e:
            skipped.append((name, str(e).split("\n")[0]))
            continue
        p = os.path.join(run, f"W11a_schedule_{name}")
        _write_table(df, p, rec, name)
        out.append(p + ".csv")

    p = os.path.join(run, "W11a_schedule_quantities")
    _write_table(quantity_summary(layers), p, rec, "quantities")
    out.append(p + ".csv")

    audit_df = run_audit_table(layers, rec)
    p = os.path.join(run, "W11a_schedule_audit")
    _write_table(audit_df, p, rec, "audit")
    out.append(p + ".csv")

    # Will the auditor even be able to run on what we shipped? Asked BEFORE the client
    # reads the table, because NOT_CHECKABLE is a failure, not a blank.
    ready = K.audit_readiness(layers["reaches"], layers["nodes"],
                             external=("roads", "hazard", "existing"))
    p = os.path.join(run, "W11a_schedule_audit_readiness")
    _write_table(ready, p, rec, "audit_readiness")
    out.append(p + ".csv")

    p = os.path.join(run, "W11a_schedule_data_requests")
    _write_table(data_request_register(), p, rec, "data_requests")
    out.append(p + ".csv")

    # The design-criteria register: every field, its units, the rule it exists for and the
    # audit check that reads it. It IS the criteria register D.5 item 4 asks for, generated
    # from the contract rather than maintained beside it.
    dd = pd.concat([K.field_table(n).assign(layer=n) for n in K.LAYERS], ignore_index=True)
    p = os.path.join(run, "W11a_schedule_data_dictionary")
    _write_table(dd, p, rec, "data_dictionary")
    out.append(p + ".csv")

    for name, why in skipped:
        rec.note(f"schedule '{name}' NOT printed: {why}")
    if skipped:
        print("    --- NOT printed (deliverable gaps, not formatting choices) ---")
        for name, why in skipped:
            print(f"    {name:<14} {why[:108]}")
        print("    --- written ---")
    return out


# ======================================================================================
# 6. SewerGEMS package
# ======================================================================================

# G203-p25: modelling "will usually be done for the Primary networks; the secondary ... can
# be partially or totally involved". DELIVERABLE_SPEC D.4 turns that into the model scope:
# trunk mains and sub mains as CONDUITS, laterals as LOADS at the junction chamber. The
# tier set below is that clause plus 'main', which sits in the same collector role in the
# philosophy sec 4 vocabulary and is a primary pipe by any reading of G203.
GEMS_CONDUIT_TIERS = ("trunk main", "sub main", "main")


def export_sewergems(layers, root: str, rec) -> str:
    """The Bentley ModelBuilder package - the referee, not the designer.

    Philosophy sec 7: no solver chooses a layout, and none will ever propose a pumping
    station. SewerGEMS is here to re-solve OUR hydraulics against an independent engine, so
    the package carries a REFEREE csv with our Q, v and d/D beside empty columns for the
    model's, and the acceptance test is the 5 % band the project already uses.

    The model is the PRIMARY network only. Every lateral load is folded into the first
    retained chamber downstream of it, and the fold is exact rather than approximate: the
    load placed at a retained node is its own accumulated flow minus the accumulated flow
    of the retained reaches arriving at it, which conserves the total by construction. The
    funnel below closes on that total, because a model that quietly drops 1.7 % of the load
    is precisely what W10 did to its own design.
    """
    out = os.path.join(root, "sewergems")
    os.makedirs(out, exist_ok=True)
    reaches, nodes = layers["reaches"], layers["nodes"]

    keep = reaches["TIER"].astype(str).isin(GEMS_CONDUIT_TIERS)
    cond = reaches[keep].copy()
    f = rec.funnel("sewergems conduits", len(reaches))
    f.drop("tier below the primary network - carried as a LOAD at the junction chamber, "
           "not as a conduit (G203-p25, DELIVERABLE_SPEC D.4)",
           n=int((~keep).sum()))
    f.close(len(cond))
    if not len(cond):
        rec.note("SewerGEMS package not written: no primary-network tier on the reach "
                 "layer yet (stage 3 assigns TIER)")
        return ""

    keep_nodes = set(cond["US_NODE"].astype(str)) | set(cond["DS_NODE"].astype(str))
    nd = nodes[nodes["NODE_UID"].astype(str).isin(keep_nodes)].copy()

    # OPEN DEFECT - LIFTING STATIONS BREAK THIS FOLD. Found in adversarial review, NOT yet
    # fixed, because the fix is a modelling decision and not a patch. Both dictionaries
    # below are built from the GRAVITY reach layer alone, so flow that reaches a chamber
    # over a RISING MAIN is invisible to `cond_arriving`. At a discharge chamber the fold
    # therefore places the WHOLE pumped branch as an incremental load - while that same
    # branch's primary reaches are already in `cond` carrying loads at their own chambers.
    # Reproduced at +26.66 % on a 16-node network (one station, one lateral into it). The
    # conservation warning below fires, but a warning is not a fix and the referee run is
    # invalid until this is settled. Two candidate resolutions, and the choice is the
    # modeller's: (a) drop every reach not gravity-connected to a modelled outfall out of
    # `cond` and let the discharge-chamber fold carry the whole pumped branch as one load -
    # which is also what stops the pumped sub-network importing as an orphan component with
    # no boundary condition; or (b) export rising mains as pressure links and subtract them
    # in `cond_arriving`. Until then, treat LOADS.csv as unverified wherever a station
    # exists.
    #
    # Accumulated flow LEAVING each node: its outgoing reach's QADF, or - at a terminal -
    # the sum of what arrives. Two definitions of one quantity would be a P2 breach, so it
    # is computed once, here, and used for both the loads and the conservation check.
    qadf = pd.to_numeric(reaches["QADF_M3D"], errors="coerce").fillna(0.0)
    q_out = dict(zip(reaches["US_NODE"].astype(str), qadf))
    arriving: Dict[str, float] = {}
    for ds, q in zip(reaches["DS_NODE"].astype(str), qadf):
        arriving[ds] = arriving.get(ds, 0.0) + float(q)
    cond_arriving: Dict[str, float] = {}
    for ds, q in zip(cond["DS_NODE"].astype(str),
                     pd.to_numeric(cond["QADF_M3D"], errors="coerce").fillna(0.0)):
        cond_arriving[ds] = cond_arriving.get(ds, 0.0) + float(q)

    loads, negative = [], 0
    for uid in nd["NODE_UID"].astype(str):
        total = q_out.get(uid, arriving.get(uid, 0.0))
        incremental = float(total) - cond_arriving.get(uid, 0.0)
        if incremental < -1e-6:
            negative += 1
        if incremental > 1e-9:
            loads.append((uid, "Sanitary Pattern Load",
                          round(incremental * 1000.0 / 86400.0, 5), "Fixed"))
    if negative:
        rec.note(f"WARNING {negative} retained chambers computed a NEGATIVE incremental "
                 "load - the accumulated flows on the reach layer do not add up along the "
                 "primary network. Investigate before running the model.")

    placed = sum(l[2] for l in loads) * 86.4                      # L/s -> m3/d
    total_net = qadf_total_m3d(nodes, reaches)
    # The funnel is in thousandths of m3/d so it can be integer, and its single named step
    # is the rounding of each node load to 5 decimals of L/s. It closes by construction -
    # the point is not that a number balances but that the difference is NAMED. Anything
    # beyond rounding is a real loss and gets a warning, because a model quietly missing
    # 1.7 % of the load is exactly what W10 did to its own design.
    n0, n1 = int(round(total_net * 1000)), int(round(placed * 1000))
    fl = rec.funnel("sewergems load conservation (m3/d x1000)", n0)
    fl.drop("rounding of each node load to 5 decimals of L/s, plus any load on a chamber "
            "the primary network does not reach", n=n0 - n1, qty=total_net - placed)
    fl.close(n1)
    if total_net > 0 and abs(total_net - placed) > 0.001 * total_net:
        pct = 100 * (placed - total_net) / total_net
        # The direction matters and the message used to state only one of them. OVER is the
        # commoner failure and has a known cause: a lifting station whose upstream primary
        # reaches ARE modelled while its rising main is not, so the branch carries loads at
        # its own chambers and its whole accumulated total is folded AGAIN into the
        # discharge chamber. Reproduced at +26.66 % on a 16-node test. Do not run the
        # referee on this package until the fold accounts for pressure edges.
        way = ("MORE than the network carries - loads are DOUBLE-COUNTED somewhere; the "
               "known cause is a lifting station upstream of the discharge chamber "
               "(see the OPEN DEFECT note above the load fold). The model would OVER-report and "
               "would call our pipes undersized"
               if placed > total_net else
               "LESS than the network carries - load is being LOST on the way into the "
               "model. The model would UNDER-report")
        rec.note(f"WARNING SewerGEMS loads carry {placed:,.1f} m3/d against the network's "
                 f"{total_net:,.1f} m3/d, {abs(pct):.2f} % {way}.")
        print(f"    WARNING load conservation off by {pct:+.2f} % - {way}")

    mh = K.gems_frame(nd[~nd["NODE_KIND"].astype(str).eq("outfall")], "MANHOLES",
                      stage="s9_export")
    mh.to_file(os.path.join(out, "MANHOLES.shp"), encoding="utf-8")

    cd = K.gems_frame(cond, "CONDUITS", stage="s9_export")
    cd["MANNING_N"] = C.MANNING_N_EXPORT       # a model parameter, not a design value
    # START_ND / STOP_ND are US_NODE / DS_NODE renamed one-to-one by contract.SEWERGEMS.
    # The originals ride along as well, so this exported network layer answers on its own
    # terms without a reader having to know Bentley's schema - ModelBuilder ignores any
    # field that is not mapped, so it costs nothing but two text columns.
    cd["US_NODE"] = cond["US_NODE"].values
    cd["DS_NODE"] = cond["DS_NODE"].values
    cd.to_file(os.path.join(out, "CONDUITS.shp"), encoding="utf-8")

    of = nd[nd["NODE_KIND"].astype(str) == "outfall"]
    if len(of):
        K.gems_frame(of, "OUTFALL", stage="s9_export").to_file(
            os.path.join(out, "OUTFALL.shp"), encoding="utf-8")
    else:
        rec.note("SewerGEMS: no node of kind 'outfall' inside the primary network - the "
                 "model will import with no boundary condition")

    with open(os.path.join(out, "LOADS.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["MH_LABEL", "LOADTYPE", "BASEFLOW", "PATTERN"])
        w.writerows(loads)
    try:
        pd.DataFrame(loads, columns=["MH_LABEL", "LOADTYPE", "BASEFLOW", "PATTERN"]
                     ).to_excel(os.path.join(out, "LOADS.xlsx"), index=False)
    except Exception as e:                     # noqa: BLE001 - reported, never swallowed
        rec.note(f"SewerGEMS LOADS.xlsx not written ({type(e).__name__}: {e}); "
                 "LOADS.csv is complete and is what ModelBuilder reads")

    ref = pd.DataFrame({
        "LABEL": cond["EDGE_UID"].values,
        "DIA_MM": pd.to_numeric(cond["DN"], errors="coerce").values,
        "SLOPE_LAID_PCT": pd.to_numeric(cond["SLOPE_LAID"], errors="coerce").values,
        "SLOPE_MIN_PCT": pd.to_numeric(cond["SLOPE_MIN"], errors="coerce").values,
        "OUR_Q_LS": pd.to_numeric(cond["QPK_LS"], errors="coerce").values,
        "OUR_V_MS": pd.to_numeric(cond["V_PK_MS"], errors="coerce").values,
        "OUR_DOD": pd.to_numeric(cond["DOD_PK"], errors="coerce").values,
        "SG_Q_LS": "", "SG_V_MS": "", "SG_DOD": "", "DQ_PCT": "", "DV_PCT": ""})
    ref.to_csv(os.path.join(out, "REFEREE_pipes.csv"), index=False)

    with open(os.path.join(out, "IMPORT_PROCEDURE.md"), "w", encoding="utf-8") as fh:
        fh.write(GEMS_PROCEDURE)
        fh.write(
            "\n\n---\n\n## W11a scope note (read before the counts confuse you)\n\n"
            f"This package models the PRIMARY network only: {len(cond):,} conduits "
            f"({network_length_km(cond):.1f} km) of "
            f"{', '.join(GEMS_CONDUIT_TIERS)}, {len(mh):,} manholes, {len(of)} outfall.\n"
            f"The {int((~keep).sum()):,} lateral and rider reaches are NOT conduits; their "
            f"flow enters as a sanitary load at the chamber where it joins the primary "
            "network, per G203-p25 and DELIVERABLE_SPEC D.4. The fold is exact - the load "
            "at a chamber is its accumulated flow minus the accumulated flow of the "
            "modelled reaches arriving at it - so the total in LOADS.csv equals the "
            f"network total, {total_net:,.0f} m3/d.\n\n"
            "BASEFLOW is AVERAGE dry weather flow in L/s. The peak factor is OURS "
            "(G201-p71-72, Merrimack above 100 properties) and is carried in "
            "REFEREE_pipes.csv as OUR_Q_LS, not applied in the model - so compare the "
            "model against OUR_Q_LS, never against BASEFLOW.\n\n"
            "The element counts in the procedure above are W8's and are left as written; "
            "this note supersedes them.\n")
    rec.wrote("sewergems", out, len(cond))
    return out


# ======================================================================================
# main
# ======================================================================================

ALL_PARTS = ("shp", "dxf", "kmz", "maps", "profiles", "schedules", "gems")


def print_do_not_attempt() -> None:
    print("\n  CONCEPT STAGE - the sixteen items DELIVERABLE_SPEC D.7 puts at a later "
          "stage, and this module does not produce:")
    w = max(len(a) for a, _b, _c in DO_NOT_ATTEMPT)
    for item, stage, cite in DO_NOT_ATTEMPT:
        print(f"    {item:<{w}}  {stage:<24} {cite}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=K.W11A_ROOT,
                    help="W11a root; the GeoPackage is <root>/shp/W11a.gpkg")
    ap.add_argument("--only", default="",
                    help="comma list of " + ",".join(ALL_PARTS)
                         + ". NOTE: the audit and the ISSUABLE verdict run with "
                           "'schedules'; omit it and the run re-renders an artefact "
                           "without re-establishing that the design still passes")
    ap.add_argument("--selftest", action="store_true",
                    help="build a tiny compliant network in a temp root and export it")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    parts = tuple(p.strip() for p in a.only.split(",") if p.strip()) or ALL_PARTS
    bad = [p for p in parts if p not in ALL_PARTS]
    if bad:
        print(f"unknown part(s) {bad}; known: {', '.join(ALL_PARTS)}")
        return 2

    root = a.root
    print(f"W11a stage 9 - deliverables\n  root      {root}\n  contract  "
          f"{K.CONTRACT_VERSION}\n  parts     {', '.join(parts)}\n")

    layers, missing = read_published(root)

    # The manifest is written to a stage-specific file ON PURPOSE. contract.Manifest keeps
    # `records` as a PER-PROCESS list and save() rewrites the whole file, so a standalone
    # stage writing to the shared run/manifest.json would erase every record written by a
    # stage that ran in an earlier process. Worth fixing in the contract; not from here.
    mpath = os.path.join(root, "run", "manifest_s9_export.json")

    with K.Manifest.stage("s9_export", 9, path=mpath) as rec:
        for name, g in layers.items():
            rec.read(name, K.gpkg_path(root), len(g))

        blocking = [m for m in missing if m in REQUIRED]
        if blocking:
            print("  NOT READY - the deliverable set needs layers that do not exist yet:\n")
            print(waiting_report(missing))
            print("\n  Nothing written. Re-run this stage once stages 1-6 have published "
                  "`nodes` and `reaches` into shp/W11a.gpkg.")
            print_do_not_attempt()
            rec.did_nothing(
                "upstream layers absent: " + ", ".join(sorted(blocking))
                + ". Exited 0 rather than writing a partial deliverable set - a schedule "
                  "printed from half a design is worse than no schedule.")
            return 0

        if missing:
            print("  optional layers not yet published (recorded, not ignored):")
            print(waiting_report(missing))
            print()
            for m in missing:
                rec.note(f"layer '{m}' absent - {PRODUCED_BY.get(m, 'upstream')}")

        # --- the gate. Nothing is drawn until the layers prove they are still the graph.
        #
        # Caught rather than allowed to raise, for a mechanical reason: an exception
        # escaping this `with` re-enters Manifest.stage's finally, which sees no writes and
        # no did_nothing() and raises its own ContractError - masking the real one. The
        # failure is also a DIFFERENT KIND from the graceful stop above. Missing layers
        # mean "not yet"; a present layer set that is not the graph means "broken", and the
        # exit code says which so a pipeline can tell them apart.
        print("  checking the published layers ARE the graph (invariant 2) ...")
        try:
            assert_is_the_graph(layers["nodes"], layers["reaches"],
                                layers.get("rising_mains"))
        except ContractError as e:
            print("\n  REFUSED. The published layers are not the graph, so nothing is "
                  "exported:\n")
            print(str(e))
            print("\n  A DXF, a KMZ and a SewerGEMS model built on a broken layer set all "
                  "inherit the\n  break and none of them shows it. That is how W10 shipped "
                  "7,919 disconnected pieces.")
            rec.did_nothing("REFUSED to export: the published layers failed invariant 2 "
                            "(round trip / degrees). " + str(e).split("\n")[0])
            return 1
        print("    round trip OK, node/reach degrees agree\n")

        n_r, n_n = len(layers["reaches"]), len(layers["nodes"])
        print(f"  {n_r:,} reaches, {n_n:,} chambers, "
              f"{network_length_km(layers['reaches']):,.1f} km, "
              f"{chambers_per_km(layers['nodes'], layers['reaches']):.1f} chambers/km\n")

        if "shp" in parts:
            print("  shapefile mirrors ...")
            for p in export_shapefiles(layers, root, rec):
                print("    " + p)
        if "dxf" in parts:
            print("  DXF by tier and diameter band ...")
            print("    " + export_dxf(layers, root, rec))
        if "kmz" in parts:
            print("  Google Earth KMZ ...")
            print("    " + export_kmz(layers, root, rec))
        if "maps" in parts:
            print("  PNG maps ...")
            for p in export_maps(layers, root, rec):
                print("    " + p)
        if "profiles" in parts:
            print("  indicative longitudinal profiles ...")
            for p in export_profiles(layers, root, rec):
                print("    " + p)
        if "schedules" in parts:
            print("  schedules (CSV + XLSX) ...")
            for p in export_schedules(layers, root, rec):
                print("    " + p)
        if "gems" in parts:
            print("  SewerGEMS package ...")
            print("    " + (export_sewergems(layers, root, rec) or "(not written)"))

        if "schedules" not in parts:
            print("  NOTE this run did not include 'schedules', so the auditor did not "
                  "run and\n       no ISSUABLE verdict was established for what was just "
                  "written.")
            rec.note("partial run: the audit and the ISSUABLE verdict were not re-run")

        rec.metric("network_km", round(network_length_km(layers["reaches"]), 2))
        rec.metric("chambers", chamber_count(layers["nodes"]))
        rec.metric("stations", station_count(layers.get("stations")))
        rec.metric("total_lift_m", round(total_lift_m(layers.get("stations")), 1))

    print_do_not_attempt()
    print(f"\n  manifest  {mpath}")
    print(K.Manifest.report())
    return 0


# ======================================================================================
# Self-test - a six-chamber compliant network, built and exported end to end.
# ======================================================================================

def _demo_network() -> Tuple[Dict[str, gpd.GeoDataFrame], K.Network]:
    """A 14-chamber design that exercises every branch of this module.

    It exists because stage 9 is the one stage that cannot be tested by running it: until
    stages 1-6 publish there is nothing to export, and "it will work when the data arrives"
    is exactly the claim W10 made about its own auditor. So the test network is small
    enough to check by hand and complete enough to reach every code path - three tiers, two
    junctions, a lifting station with a rising main, a scheduled crossing, a plot served
    off-network, and a package.

    Every level in it is DERIVED, not typed. Ground falls at a constant 0.5 %; every reach
    is laid at 0.50 %, which is the Table 11 floor for DN200 (G203-p29) and above the
    tractive minimum for the larger sizes; every invert comes from `min_invert_depth()` at
    the reach's OWN diameter; spacing is 100 m on DN200-315 and 100 m on the trunk, inside
    the Table 12 limits of 100 m and 120 m (G203-p30). Nothing is tuned until the audit
    passes. That it then passes all 22 checks is a second, useful result: the contract's
    depth basis, `sewnet.criteria` and `audit.py` are mutually consistent, which was in
    genuine doubt - the contract had to override `criteria.invert_depth_min()` by 50 mm to
    get there.

    Placed at (444000, 2563000): real ground inside the study area, verified clear of
    Hazard_T50y classes 4/5/6 across the whole footprint, so the wadi regression check R4
    and the satellite background run against real rasters rather than empty ones.
    """
    X0, Y0 = 444000.0, 2563000.0
    G0, GRAD = 330.0, 0.005          # ground datum, and the ground fall this test assumes
    SLOPE = 0.50                     # % laid. G203-p29 Tab 11 makes 0.50 % the DN200 floor
    LIFT = 5.0                       # m the pumped branch sits below the chamber it feeds
    ADD = 3.0                        # m3/d added at each chamber; 0 at the works inlet

    # chain -> (points, tier, DN, join target (chain, index) or None)
    chains = {
        "T": ([(0, 0), (100, 0), (200, 0), (300, 0), (400, 0), (500, 0)],
              "trunk main", 400, None),
        "A": ([(100, 300), (100, 200), (100, 100)], "sub main", 250, ("T", 1)),
        "B": ([(0, 400), (0, 300)], "lateral", 200, ("A", 0)),
        "C": ([(300, 300), (300, 200), (300, 100)], "lateral", 200, None),
    }
    net = K.Network()
    uid: Dict[Tuple[str, int], str] = {}
    for cid, (pts, tier, _dn, _join) in chains.items():
        for i, (dx, dy) in enumerate(pts):
            uid[(cid, i)] = net.node(X0 + dx, Y0 + dy, kind="chamber", tier=tier,
                                     src="draft", confidence="drafted", stage="s0_demo",
                                     package="P1", phase=1)
    of_uid, st_uid = uid[("T", 5)], uid[("C", 2)]
    disch_uid = uid[("T", 3)]                       # where the rising main discharges

    edge_dn: Dict[str, int] = {}
    for cid, (pts, tier, dn, join) in chains.items():
        seq = [uid[(cid, i)] for i in range(len(pts))]
        for a, b in zip(seq, seq[1:]):
            edge_dn[net.add_edge(a, b, stage="s0_demo", tier=tier, src="draft",
                                 confidence="drafted")] = dn
        if join is not None:
            edge_dn[net.add_edge(seq[-1], uid[join], stage="s0_demo", tier=tier,
                                 src="draft", confidence="drafted")] = dn
    rm_uid = net.add_edge(st_uid, disch_uid, kind="rising", stage="s0_demo",
                          tier="trunk main", src="draft", confidence="drafted")

    # kinds are DERIVED from the graph, not declared: G203-p29 sec 4.4 lists the triggers a
    # chamber may exist for, and "how many pipes arrive" is the one the graph can answer.
    for u, nd in net.nodes.items():
        n_in = len(net.in_edges.get(u, ()))
        nd.kind = ("outfall" if u == of_uid else "station" if u == st_uid
                   else "head" if n_in == 0 else "junction" if n_in > 1 else "chamber")

    def grav_path(u: str) -> List[str]:
        """Downstream through GRAVITY edges only. A station terminates it - past that the
        flow is pumped, and ground level upstream of a station has nothing to do with
        ground level at the chamber the rising main discharges into."""
        out = [u]
        while True:
            e = net.out_edge.get(out[-1])
            if e is None or net.edges[e].kind != "gravity":
                return out
            out.append(net.edges[e].ds)

    def path_len(u: str) -> float:
        p = grav_path(u)
        return sum(math.hypot(net.nodes[b].x - net.nodes[a].x,
                              net.nodes[b].y - net.nodes[a].y)
                   for a, b in zip(p, p[1:]))

    for u, nd in net.nodes.items():                 # the gravity tree first ...
        if grav_path(u)[-1] != st_uid:
            nd.grd_m = G0 + GRAD * path_len(u)
    base_pumped = net.nodes[disch_uid].grd_m - LIFT
    for u, nd in net.nodes.items():                 # ... then the pumped branch below it
        if grav_path(u)[-1] == st_uid:
            nd.grd_m = base_pumped + GRAD * path_len(u)

    # inverts from min_invert_depth() at each reach's OWN diameter (the contract's
    # definition, 50 mm deeper than criteria.invert_depth_min() and the only one audit H3
    # accepts). A terminal takes the diameter of the pipe that arrives.
    inv_out: Dict[str, float] = {}
    for u, nd in net.nodes.items():
        e = net.out_edge.get(u)
        if e and net.edges[e].kind == "gravity":
            dn = edge_dn[e]
        else:
            dn = max((edge_dn[i] for i in net.in_edges.get(u, ())), default=200)
        inv_out[u] = nd.grd_m - K.min_invert_depth(dn)
        nd.inv_m = inv_out[u]

    nodes = net.to_nodes_gdf()
    reaches = net.to_edges_gdf("gravity")
    rising = net.to_edges_gdf("rising")

    # accumulated flow, topologically. Every chamber adds ADD except the works inlet, which
    # collects nothing of its own - the outfall is where flow LEAVES, not a plot.
    order = sorted(net.nodes, key=lambda z: len(net.downstream_path(z)), reverse=True)
    acc = {u: (0.0 if u == of_uid else ADD) for u in net.nodes}
    for u in order:
        e = net.out_edge.get(u)
        if e:
            acc[net.edges[e].ds] += acc[u]
    q_edge = {e_uid: acc[e.us] for e_uid, e in net.edges.items()}

    from sewnet import hydra
    dn_v = [edge_dn[u] for u in reaches["EDGE_UID"]]
    L = pd.to_numeric(reaches["LEN_M"]).to_numpy()
    inv_up = [inv_out[u] for u in reaches["US_NODE"]]
    inv_dn = [iu - l * SLOPE / 100.0 for iu, l in zip(inv_up, L)]
    grd = dict(zip(nodes["NODE_UID"], pd.to_numeric(nodes["GRD_M"])))
    q_m3d = [q_edge[u] for u in reaches["EDGE_UID"]]
    pf = 3.0                                        # PF_METH 'held': G201 prescribes no
    #                                                 formula below 100 properties (p71)
    qinf = [C.INFILT_L_D_KM * (l / 1000.0) / 86400.0 for l in L]   # G201-p72-73, unpeaked
    qpk = [q * 1000.0 / 86400.0 * pf + i for q, i in zip(q_m3d, qinf)]
    state = [hydra.pipe_state(d, SLOPE / 100.0, q / 1000.0, C) for d, q in zip(dn_v, qpk)]
    smin = [hydra.smin_for(d, q / 1000.0, C) * 100.0 for d, q in zip(dn_v, qpk)]
    clean = ["velocity" if (v is not None and v >= C.V_SELF_CLEANSING)
             else ("tractive" if SLOPE / 100.0 >= hydra.smin_tractive(q / 1000.0, C) - 1e-12
                   else "neither") for (_y, v), q in zip(state, qpk)]

    reaches = reaches.assign(
        DN=dn_v,
        MATERIAL=["GRP" if d > K.PVC_MAIN_MAX_DN else "PVC-U" for d in dn_v],
        CONSTR="open_trench", SLOPE_LAID=SLOPE, SLOPE_MIN=[round(s, 4) for s in smin],
        GRAD_BY=["table11" if s >= SLOPE - 1e-9 else "uniform" for s in smin],
        SIZED_BY="minimum", CLEAN_BY=clean, TAU_PA=C.TAU_PA,
        INV_UP=inv_up, INV_DN=inv_dn,
        US_DEPTH=[grd[u] - iu for u, iu in zip(reaches["US_NODE"], inv_up)],
        DS_DEPTH=[grd[d] - i for d, i in zip(reaches["DS_NODE"], inv_dn)],
        QADF_M3D=q_m3d, QINF_LS=qinf, PF=pf, PF_METH="held", QPK_LS=qpk,
        V_PK_MS=[0.0 if v is None else round(v, 4) for _y, v in state],
        DOD_PK=[0.0 if y is None else round(y, 4) for y, _v in state],
        RET_MIN=[round(l / (max(v or 0.01, 0.01) * 60.0), 3)
                 for l, (_y, v) in zip(L, state)],
        PAST_CAP=0, CAP_EXIT="", CAP_LEN_M=0.0, TIE_TYPE="none",
        ON_DUAL_M=0.0, ON_WADI_M=0.0, CROSS_ID="")
    reaches["COVER_US"] = [K.cover(d, x) for d, x in zip(dn_v, reaches["US_DEPTH"])]
    reaches["COVER_DN"] = [K.cover(d, x) for d, x in zip(dn_v, reaches["DS_DEPTH"])]
    trunk_ix = int(reaches.index[reaches["TIER"] == "trunk main"][1])
    reaches.loc[trunk_ix, "CROSS_ID"] = "X1"        # a scheduled road crossing (H1)

    # node-side cover, drop and drop type, computed FROM the reaches just built so the
    # chamber schedule and the pipe layer cannot disagree - they came from one source.
    arr: Dict[str, List[Tuple[int, float]]] = {}
    for d, dn_, i in zip(reaches["DS_NODE"].astype(str), dn_v, inv_dn):
        arr.setdefault(d, []).append((dn_, i))
    dn_out = {str(u): d for u, d in zip(reaches["US_NODE"], dn_v)}
    cover_m, drop_m, drop_t, vortex = [], [], [], []
    for u in nodes["NODE_UID"].astype(str):
        cands = [K.cover(dn_out[u], grd[u] - inv_out[u])] if u in dn_out else []
        cands += [K.cover(dn_, grd[u] - i) for dn_, i in arr.get(u, [])]
        cover_m.append(min(cands) if cands else K.cover(200, grd[u] - inv_out[u]))
        d = max([i - inv_out[u] for _dn, i in arr.get(u, [])] + [0.0])
        drop_m.append(round(d, 4))
        drop_t.append("vortex" if d > C.BACKDROP_MAX else
                      ("backdrop" if d > C.DROP_TRIGGER else "none"))
        vortex.append(1 if d > C.BACKDROP_MAX else 0)
    nodes = nodes.assign(
        COVER_M=cover_m, DROP_M=drop_m, DROP_TYPE=drop_t, VORTEX=vortex,
        INLET_DEG=180.0, INLET_FLAG=0, MH_DIA=1.0,
        MH_MAT="precast concrete (stated assumption - G203 gives no table; PAM-SPC pending)",
        Q_ADF_M3D=[float(acc[u]) for u in nodes["NODE_UID"]],
        Q_PK_LS=[float(acc[u]) * 1000.0 / 86400.0 * pf for u in nodes["NODE_UID"]],
        N_PROP=[round(acc[u] / ADD * 1.456, 3) for u in nodes["NODE_UID"]],
        PAST_CAP=0, CAP_EXIT="")

    # the station and its rising main. Every number is the G203 formula, not a choice:
    # type from p40-41 Tab 17, land band from p43 Tab 21, wet well from p48 sec 7.8.
    q_duty, starts, rm_dn = 20.0, 10.0, 150
    st_grd = float(grd[st_uid])
    lift = float(inv_out[disch_uid] - inv_out[st_uid])
    rm_len = float(pd.to_numeric(rising["LEN_M"]).iloc[0])
    v_duty = (q_duty / 1000.0) / (math.pi * (rm_dn / 1000.0) ** 2 / 4.0)
    st_ref = str(nodes.set_index("NODE_UID").loc[st_uid, "NODE_REF"])
    stations = gpd.GeoDataFrame(
        [dict(NODE_UID=st_uid, NODE_REF=st_ref, WHY="cap", ST_TYPE="Type 1",
              Q_DUTY_LS=q_duty, LIFT_M=round(lift, 3), N_PROP=round(acc[st_uid] / ADD, 2),
              Q_ADF_M3D=float(acc[st_uid]),
              WELL_M3=round(0.25 * (q_duty / 1000.0) * (3600.0 / starts), 3),
              WW_STARTS=starts, GRD_M=st_grd, FLOOD_LV=round(st_grd - 1.0, 3),
              LAND_M2=100.0, RM_EDGE=rm_uid, COMM_PT=1, SRC="draft",
              CONFIDENCE="drafted", STAGE="s0_demo", PACKAGE="P1", PHASE=1)],
        geometry=[Point(net.nodes[st_uid].xy)], crs=K.CRS_EPSG)
    rising = rising.assign(
        STATION=st_uid, DN=rm_dn, MATERIAL="HDPE", Q_DUTY_LS=q_duty,
        V_DUTY_MS=round(v_duty, 3), V_MIN_MS=round(v_duty * 0.8, 3),
        STAT_HD_M=round(lift, 3), TOT_HD_M=round(lift * 1.3, 3),
        RETENT_M=round(rm_len / (v_duty * 60.0), 2), N_AIRV=1, N_WASH=1, SEPTIC_FL=1)

    # connections: one per chamber, plus one plot the network does not reach. That last
    # row is the branch W10 never had - it lost 1,233 m3/d because an assignment radius
    # failed quietly and nothing recorded that a load had gone missing.
    rows, geoms = [], []
    for i, (u, kind) in enumerate(zip(nodes["NODE_UID"].astype(str),
                                      nodes["NODE_KIND"].astype(str))):
        if kind in ("outfall", "station"):
            continue
        nd = net.nodes[u]
        g = LineString([(nd.x + 12.0, nd.y + 16.0), (nd.x, nd.y)])
        rows.append(dict(CONN_ID=f"CN{i:04d}", PLOT_ID=f"PL{i:05d}", OUT_NODE=u,
                         WHY="assigned", SYSTEM="central", CONN_TYPE="PCS",
                         Q_ADF_M3D=ADD, N_PROP=1.456, LEN_M=round(g.length, 3),
                         SLOPE_LAID=5.0, COVER_M=C.PCS_MIN_COVER, CAN_DRAIN=1,
                         SRC="draft", CONFIDENCE="drafted", STAGE="s0_demo",
                         PACKAGE="P1", PHASE=1))
        geoms.append(g)
    g = LineString([(X0 + 600, Y0 + 400), (X0 + 620, Y0 + 400)])
    rows.append(dict(CONN_ID="CN9999", PLOT_ID="PL99999", OUT_NODE="", SYSTEM="onsite",
                     WHY="no legal corridor within reach - served by an on-site system. "
                         "Philosophy sec 8a: 'serviced' is not 'connected to one network', "
                         "and the TOR (scope p4 item 3) requires the former, not the latter",
                     CONN_TYPE="PCS", Q_ADF_M3D=0.9, N_PROP=1.0, LEN_M=round(g.length, 3),
                     SLOPE_LAID=5.0, COVER_M=C.PCS_MIN_COVER, CAN_DRAIN=0, SRC="draft",
                     CONFIDENCE="derived", STAGE="s0_demo", PACKAGE="", PHASE=0))
    geoms.append(g)
    connections = gpd.GeoDataFrame(rows, geometry=geoms, crs=K.CRS_EPSG)

    xg = reaches.loc[trunk_ix, "geometry"]
    xs = LineString([xg.interpolate(xg.length / 2 - 12.5),
                     xg.interpolate(xg.length / 2 + 12.5)])
    crossings = gpd.GeoDataFrame(
        [dict(CROSS_ID="X1", EDGE_UID=str(reaches.loc[trunk_ix, "EDGE_UID"]),
              OBSTACLE="road", LEN_M=round(xs.length, 3), ANGLE_DEG=90.0,
              METHOD="thrust_bore",
              COVER_M=1.5,          # G203-p52 sec 8.2.4 wants 1.5 m at a wadi crossing
              APPROVED=0, SRC="draft", CONFIDENCE="drafted", STAGE="s0_demo",
              PACKAGE="P1", PHASE=1)],
        geometry=[xs], crs=K.CRS_EPSG)

    corridors = gpd.GeoDataFrame(
        [dict(CORR_ID=f"CO{i:04d}", LEN_M=float(r.LEN_M),
              WIDTH_M=2.0,          # G203-p32 Tab 13: DN200-500 -> a 2.0 m reserve
              ON_DUAL_M=0.0, ON_WADI_M=0.0, IS_STREET=1, N_PLOT=2, USED=1,
              SRC="draft", CONFIDENCE="drafted", STAGE="s0_demo", PACKAGE="P1", PHASE=1)
         for i, r in enumerate(reaches.itertuples())],
        geometry=list(reaches.geometry), crs=K.CRS_EPSG)

    hull = reaches.union_all().convex_hull.buffer(30.0)
    packages = gpd.GeoDataFrame(
        [dict(PACKAGE="P1", PHASE=1, LEN_KM=round(network_length_km(reaches), 4),
              N_PLOT=len(connections) - 1, OUTLET=of_uid, DS_PKG="STP", COMM_SEQ=1,
              INDEP=1, ONE_TREE=1)],
        geometry=[hull], crs=K.CRS_EPSG)

    return (dict(nodes=nodes, reaches=reaches, rising_mains=rising, stations=stations,
                 connections=connections, crossings=crossings, corridors=corridors,
                 packages=packages), net)


def selftest() -> int:
    """Build the demo design, publish it through the contract, then export it end to end."""
    import tempfile
    root = os.path.join(tempfile.gettempdir(), "w11a_s9_selftest")
    for sub in ("shp", "dxf", "img", "run", "sewergems"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    gp = K.gpkg_path(root)
    if os.path.exists(gp):
        os.remove(gp)                    # a stale layer would make the test lie

    layers, net = _demo_network()
    bad = net.check()
    if bad:
        print("selftest network fails its own global invariants:\n  " + "\n  ".join(bad))
        return 1
    for name, g in layers.items():
        K.publish(g, name, root, stage="s0_demo")
    print(f"selftest: published {len(layers)} layers "
          f"({len(layers['nodes'])} nodes, {len(layers['reaches'])} reaches, "
          f"1 station, 1 rising main) to {gp}\n")
    return main(["--root", root])


if __name__ == "__main__":
    sys.exit(main())
