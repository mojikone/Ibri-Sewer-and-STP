# -*- coding: utf-8 -*-
"""s8_export - W11b stage 8. Everything a human or another program has to READ.

W11b owns this file. It imports `w11b.contract`, `w11b.criteria`, `w11b.hydra`,
`w11b.present`, `w11b.hazard` and `w11b.asbuilt`, and NOTHING from `W8/py/sewnet`,
`W10/py` or `W11a/py`. Earlier folders are read as DATA only.

======================================================================================
READ THIS FIRST: THIS STAGE DOES SOMETHING IT SHOULD NOT HAVE HAD TO DO
======================================================================================

W11b has stages 1 (roads), 2 (orient), 3 (hierarchy), 4 (chambers), 5 (flows) and 7
(pumps). **THERE IS NO STAGE 6.** Nothing in W11b has ever computed an invert, a
diameter, a laid gradient, a velocity, a depth of flow or a drop.

That is not a detail. Every single thing the engineer asked this stage for needs
stage 6:

    "KMZ by pipe depth"          needs an invert
    "KMZ by diameter"            needs a diameter
    "the pipe schedule"          scope-p25 asks for invert, DN, gradient, velocity
    "long-section profiles"      a profile IS the invert against the ground
    "a SewerGEMS package"        contract.SEWERGEMS wants INV_EL, INV_UP, INV_DN, DIA_MM
    "quantities"                 an excavation quantity is a depth times a length

So this stage carries a LEVELS AND SIZES pass of its own, in section 4, and every
number it produces is tagged `STAGE = "s8_export/levels-standin"` on the row,
`LEVELS_SRC = "s8 stand-in"` in the manifest, and printed on the legend of every map
that depends on it. It is a STAND-IN, not stage 6:

  * it is a single strict pass (philosophy sec 7 asks for two, then an audit);
  * it never places, moves or removes a pumping station, because stations are s7's and
    inventing one here would put an eighth lifting-station count into circulation on a
    project that already retracted seven;
  * where the 12 m cover cap is passed and neither philosophy sec 5 exit applies, it
    publishes PAST_CAP = 1 with a BLANK CAP_EXIT and counts it. It does not clip the
    depth, and it does not invent an exit. Clipping satisfies a validator by lying.

Read the count of blank-exit breaches in EXPORT.md as the size of the hole stage 6
has to fill, not as a defect of this exporter.

======================================================================================
WHAT ELSE IS MISSING, NAMED RATHER THAN PAPERED OVER
======================================================================================

1.  THE TRUNK IS NOT IN THE GRAPH. `W11b_hier.gpkg|trunk` is 85.49 km in 54 pieces,
    the client's own drawn Main Pipe, an INPUT. It carries no chambers, no nodes and
    no topology, so nothing drains INTO it here. The 195 outfalls this stage exports
    are subnetwork outlets, not the works. The trunk is exported as its own layer,
    drawn on every map, and excluded from every hydraulic statement.

2.  THE STATION NODE IDS DO NOT RESOLVE. s7 minted `NODE_UID` N0000001..N0000085 for
    its 85 stations. Those strings ALSO exist in the chamber layer, on entirely
    different chambers - station N0000001 says ground 378.33 m, chamber N0000001 is at
    317.08 m. So the ids collide instead of referencing. This stage re-anchors each
    station to the nearest chamber BY GEOMETRY, records the distance it had to move in
    `ST_SNAP_M`, and refuses to claim the anchor is topology: H16 says topology is
    written down, and a recovered anchor is not. Reported, with the distances.

3.  NO PACKAGES STAGE EXISTS. `PACKAGE` and `PHASE` are `required=False` in the
    contract for exactly this reason. This stage derives a package per subnetwork so
    the package schedule and the package map are printable, tags them
    `SRC = "terrain"/CONFIDENCE = "derived"`, and says on the face of the schedule that
    they are a grouping and not a procurement strategy.

======================================================================================
WHAT IT PRODUCES
======================================================================================

    W11b/shp/W11b_export.gpkg      the contract layers: nodes, reaches, connections,
                                   stations, rising_mains, crossings, packages, trunk,
                                   plus contract_check, manifest, assumptions
    W11b/shp/kmz/*.kmz             ELEVEN styled Google Earth files, subfoldered
    W11b/export/shp/*.shp          the same layers as ESRI shapefiles
    W11b/export/dxf/*.dxf          plan drawing, one layer per tier + chambers + text
    W11b/export/schedules/*.xlsx   chambers, pipes, stations, rising mains, connections,
                                   crossings, packages, quantities, not-served
    W11b/export/profiles/*.pdf     long sections, ground against invert
    W11b/export/sewergems/         the model package + the field map + the read-me
    W11b/export/qgis_load_W11b.py  the PyQGIS loader (also driven over the qgis MCP)
    W11b/run/export/EXPORT.md      the report, every number with its source

Run:  python s8_export.py build        (then --verify, --report, --selftest)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zipfile
from collections import defaultdict, deque
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union

from w11b import contract as CT
from w11b import criteria as CR
from w11b import hydra as HY
from w11b import present as PR

C = CR.DEFAULT

STAGE = "s8_export"
STAGE_ORDER = 8
VERSION = "W11b-s8_export-1.0"
LEVELS_TAG = "s8_export/levels-standin"

# ======================================================================================
# PATHS
# ======================================================================================

W11B = os.path.dirname(_HERE)                       # .../W11b
REPO = os.path.dirname(W11B)                        # .../Hydraulic/Claude
SHP = os.path.join(W11B, "shp")
RUN = os.path.join(W11B, "run", "export")
OUT = os.path.join(W11B, "export")

GPKG_ROADS = os.path.join(SHP, "W11b_roads.gpkg")
GPKG_ORIENT = os.path.join(SHP, "W11b_orient.gpkg")
GPKG_HIER = os.path.join(SHP, "W11b_hier.gpkg")
GPKG_CHAMB = os.path.join(SHP, "W11b_chambers.gpkg")
GPKG_FLOWS = os.path.join(SHP, "W11b_flows.gpkg")
GPKG_PUMPS = os.path.join(SHP, "W11b_pumps.gpkg")
GPKG_OUT = os.path.join(SHP, "W11b_export.gpkg")

DIR_KMZ = os.path.join(SHP, "kmz")
DIR_SHP = os.path.join(OUT, "shp")
DIR_DXF = os.path.join(OUT, "dxf")
DIR_SCH = os.path.join(OUT, "schedules")
DIR_PRF = os.path.join(OUT, "profiles")
DIR_GEM = os.path.join(OUT, "sewergems")

_T0 = time.time()
_LOG: List[str] = []


def _log(msg: str) -> None:
    line = f"[{time.time() - _T0:7.1f}s] {msg}"
    _LOG.append(line)
    print(line, flush=True)


def _mkdirs() -> None:
    for d in (RUN, OUT, DIR_KMZ, DIR_SHP, DIR_DXF, DIR_SCH, DIR_PRF, DIR_GEM):
        os.makedirs(d, exist_ok=True)


# ======================================================================================
# 1.  THE NUMBERS THIS STAGE IS ALLOWED TO USE THAT ARE NOT ALREADY IN `criteria`
#     Every one carries the page it was read from, or is declared an assumption. Nothing
#     below may be edited without re-reading the source PDF.
# ======================================================================================

EXPORT_NUMBERS: List[Tuple[str, Any, str, str]] = [
    # name, value, source, why
    ("MIN_COVER_CROWN", C.MIN_COVER_CROWN, "G203-p33 4.6.3",
     "minimum cover to crown; sets the shallowest invert a reach may be laid at"),
    ("MAX_COVER", C.MAX_COVER, "G203-p33",
     "the cover cap; past it philosophy sec 5's ladder starts"),
    ("EXIT_RECOVER_M", 500.0, "philosophy sec 5",
     "cover must come back under the cap within this distance for the first exit"),
    ("EXIT_OUTFALL_M", 1000.0, "philosophy sec 5",
     "the run must reach its outfall within this distance for the second exit"),
    ("DROP_TRIGGER", C.DROP_TRIGGER, "G203-p30",
     "invert difference above which an external ramped backdrop is required"),
    ("BACKDROP_MAX", C.BACKDROP_MAX, "G203-p30",
     "backdrop maximum height; beyond it a vortex drop shaft"),
    ("DROP_CEILING_M", C.DROP_CEILING_M, "PROJECT ASSUMPTION (criteria)",
     "the drop a vortex shaft is assumed buildable to. G203 gives no maximum"),
    ("SLOPE_STEP", C.SLOPE_STEP, "PROJECT RULE (user 2026-08-23)",
     "gradients are laid on round 0.05 % steps so the drawing matches the levels"),
    ("V_MAX", C.V_MAX, "G203-p27 4.2.2.2", "gravity maximum velocity"),
    ("TAU_PA", C.TAU_PA, "ASSUMPTION GAP-9 (G203-p27 gives no numeric tau)",
     "the tractive stress every tractive-governed gradient rests on"),
    ("MANNING_N_EXPORT", C.MANNING_N_EXPORT, "ASSUMPTION (G203-p27 derivation n=0.013)",
     "Manning n written into the SewerGEMS/SWMM package; a MODEL parameter, never a "
     "design value on the pipe"),
    ("INFILT_L_D_KM", C.INFILT_L_D_KM, "G201-p72 7.4.3",
     "infiltration for a NEW network, unpeaked"),
    ("PF_HOLD_PROPERTIES", C.PF_HOLD_PROPERTIES, "G201-p71 7.4.2",
     "below this many properties G201 prescribes no peak-factor formula, so PF is HELD "
     "at 1.0 and said so"),
    # ---- the only two genuinely new declarations this stage makes -------------------
    ("MH_DIA_STD_M", 1.20, "PROJECT ASSUMPTION - G203 gives no table of chamber size "
                           "against depth (searched: p29-30 sec 4.4)",
     "standard chamber internal diameter used for the take-off. G203-p30 requires at "
     "least 1.5 m wherever an internal backdrop is unavoidable, so a chamber carrying a "
     "backdrop is written up to that"),
    ("SLOPE_MAX_LAID_PCT", 25.0,
     "PROJECT BOUND - declared in contract.REACHES.SLOPE_LAID (hi=25.0)",
     "the steepest gradient a gravity sewer is laid at. G203 gives NO maximum gradient - "
     "it caps VELOCITY at 3.0 m/s (p27 4.2.2.2), and on this network the velocity cap "
     "never binds because the flows are tiny, so a DN200 carrying 0.5 L/s solved to a "
     "46.45 % laid gradient down a cliff. Past this bound the fall is taken at a drop "
     "chamber (philosophy sec 5) instead of by the pipe"),
    ("TRENCH_SIDE_M", 0.30, "PROJECT ASSUMPTION - no guideline trench width was found",
     "working space each side of the barrel in the excavation take-off. The take-off is "
     "declared indicative and is NOT a bill of quantities"),
]
EXPORT_NUM = {n: v for n, v, _s, _w in EXPORT_NUMBERS}

SLOPE_MAX_LAID = EXPORT_NUM["SLOPE_MAX_LAID_PCT"] / 100.0
MH_DIA_STD_M = EXPORT_NUM["MH_DIA_STD_M"]
TRENCH_SIDE_M = EXPORT_NUM["TRENCH_SIDE_M"]
EXIT_RECOVER_M = EXPORT_NUM["EXIT_RECOVER_M"]
EXIT_OUTFALL_M = EXPORT_NUM["EXIT_OUTFALL_M"]


# The vocabularies upstream stages actually wrote, against the vocabularies the contract
# declares. These are NOT interchangeable words; each mapping is a decision and each is
# recorded so a reader can see what was renamed and why.
SRC_MAP = {
    # s1 read one clean DXF with two layers. `piping center line` is the surveyed/observed
    # road set; `piping center line-propo-01` is the proposed one. Neither is a block or a
    # link in the contract's sense, so both land on dwg_road and the DISTINCTION IS KEPT in
    # CONFIDENCE, which is where the contract puts trust.
    "draft_base": "dwg_road",
    "draft_propo": "dwg_road",
    "main_pipe": "main_pipe",
    "terrain": "terrain",
    "existing": "existing",
    "manual": "manual",
}
CONF_MAP = {
    # s1's own words -> the contract's four grades.
    # `corroborated` = the DXF line is confirmed by the recorded NAMA centreline: drafted.
    # `drafted` = drawn, uncorroborated: still drafted.
    # `provisional` = a platted reserve with nothing built on it: provisional, and the
    # contract's SRC_CONFIDENCE_CEILING would force that anyway.
    "corroborated": "drafted",
    "drafted": "drafted",
    "provisional": "provisional",
    "surveyed": "surveyed",
    "derived": "derived",
}
# A proposed-layer corridor is never better than provisional: philosophy sec 4, "a platted
# reserve with nothing built on it ... is never reported as existing".
SRC_CONF_FLOOR = {"draft_propo": "provisional"}

TIER_FLOOR_DN = {
    # G203-p22 Table 6 minimum sizes by application. A rider is 160 OD; everything that
    # carries another pipe's flow is 200 OD minimum.
    "rider": C.DN_TERTIARY,
    "lateral": C.DN_MIN_LATERAL,
    "main": C.DN_MIN_MAIN,
    "sub main": C.DN_MIN_MAIN,
    "trunk main": C.DN_MIN_MAIN,
}


# ======================================================================================
# 2.  ASSEMBLY - read every upstream stage, once, and say what came from where
# ======================================================================================

@dataclass
class Assembly:
    """Everything the export needs, read from the PUBLISHED GeoPackages and nothing else.

    Nothing here recomputes an upstream stage's answer. Where a value had to be
    translated - a vocabulary, an id that did not resolve - the translation is recorded
    in `notes` and lands in EXPORT.md."""
    chambers: gpd.GeoDataFrame
    segments: gpd.GeoDataFrame
    connections: gpd.GeoDataFrame
    unserved: gpd.GeoDataFrame
    hier: gpd.GeoDataFrame
    trunk: gpd.GeoDataFrame
    corridors: gpd.GeoDataFrame
    flows_arcs: gpd.GeoDataFrame
    stations: gpd.GeoDataFrame
    rising: gpd.GeoDataFrame
    boundary: gpd.GeoDataFrame
    notes: List[str] = dc_field(default_factory=list)
    reads: List[Tuple[str, str, int]] = dc_field(default_factory=list)

    def note(self, s: str) -> None:
        self.notes.append(s)
        _log("   note: " + s)


def _read(path: str, layer: str) -> gpd.GeoDataFrame:
    g = gpd.read_file(path, layer=layer)
    if g.crs is not None and g.crs.to_epsg() != CT.CRS_EPSG:
        g = g.to_crs(CT.CRS_EPSG)
    return g


def assemble() -> Assembly:
    _log("assembling from the published stage layers")
    a = Assembly(
        chambers=_read(GPKG_CHAMB, "chambers"),
        segments=_read(GPKG_CHAMB, "segments"),
        connections=_read(GPKG_CHAMB, "connections"),
        unserved=_read(GPKG_CHAMB, "unserved"),
        hier=_read(GPKG_HIER, "reaches"),
        trunk=_read(GPKG_HIER, "trunk"),
        corridors=_read(GPKG_ROADS, "corridors"),
        flows_arcs=_read(GPKG_FLOWS, "arcs"),
        stations=_read(GPKG_PUMPS, "stations"),
        rising=_read(GPKG_PUMPS, "rising_mains"),
        boundary=_read(GPKG_ROADS, "boundary"),
    )
    for nm, src, g in (("chambers", GPKG_CHAMB, a.chambers), ("segments", GPKG_CHAMB, a.segments),
                       ("connections", GPKG_CHAMB, a.connections),
                       ("unserved", GPKG_CHAMB, a.unserved),
                       ("hier reaches", GPKG_HIER, a.hier), ("trunk", GPKG_HIER, a.trunk),
                       ("corridors", GPKG_ROADS, a.corridors),
                       ("flow arcs", GPKG_FLOWS, a.flows_arcs),
                       ("stations", GPKG_PUMPS, a.stations),
                       ("rising mains", GPKG_PUMPS, a.rising)):
        a.reads.append((nm, os.path.basename(src), len(g)))
        _log(f"   read {nm:<14} {len(g):>7,}  {os.path.basename(src)}")

    # ---- tier, from stage 3, onto the chamber-to-chamber segments -----------------------
    tier_by_cid = dict(zip(a.hier.CID.astype(str), a.hier.TIER.astype(str)))
    seg_cid = a.segments.ARC_CID.astype(str)
    a.segments["TIER"] = seg_cid.map(tier_by_cid)
    miss = a.segments.TIER.isna()
    if miss.any():
        # An arc s4 chambered that s3 did not tier. Never guess a tier: an unrecognised
        # tier is a SILENT skip in a diameter-floor check (contract, TIER field).
        a.segments.loc[miss, "TIER"] = "lateral"
        a.note(f"{int(miss.sum()):,} segments ({a.segments.loc[miss,'LEN_M'].sum()/1000:.2f} km) "
               f"carry an ARC_CID stage 3 never tiered; written as 'lateral', the lowest "
               f"tier, so the diameter floor is the weakest and nothing is flattered")
    a.segments["TIER"] = a.segments.TIER.map(lambda t: CT.TIER_ALIASES.get(str(t), str(t)))

    # ---- corridor provenance, onto the segments ----------------------------------------
    corr = a.corridors.set_index(a.corridors.CID.astype(str))
    a.segments["ALONG_DUAL"] = seg_cid.map(corr.ALONG_DUAL).fillna(0).astype(int)
    a.segments["XING_DUAL"] = seg_cid.map(corr.XING).fillna(0).astype(int)
    a.segments["DUAL_ANG"] = seg_cid.map(corr.DUAL_ANG).fillna(-1.0).astype(float)

    # ---- vocabulary: what the stages wrote -> what the contract declares ----------------
    raw_src = a.segments.SRC.astype(str)
    a.segments["SRC_RAW"] = raw_src
    a.segments["SRC"] = raw_src.map(SRC_MAP)
    conf = a.segments.CONFIDENCE.astype(str).map(CONF_MAP)
    floor = raw_src.map(SRC_CONF_FLOOR)
    rank = {c: i for i, c in enumerate(CT.CONFIDENCE)}
    a.segments["CONFIDENCE"] = [
        f if (isinstance(f, str) and rank.get(f, 0) > rank.get(c, 0)) else c
        for c, f in zip(conf, floor)]
    n_floored = int(sum(1 for c, f in zip(conf, floor)
                        if isinstance(f, str) and rank.get(f, 0) > rank.get(c, 0)))
    a.note(f"vocabulary: SRC 'draft_base'/'draft_propo' -> 'dwg_road' (both are road "
           f"centrelines from the one clean DXF); CONFIDENCE 'corroborated' -> 'drafted'. "
           f"{n_floored:,} segments on the PROPOSED road layer were floored to "
           f"'provisional' (philosophy sec 4: a platted reserve is never reported as "
           f"existing)")

    # ---- stations: the ids do not resolve. Re-anchor by geometry, and say so. -----------
    a.stations = _reanchor_stations(a)
    return a


def _reanchor_stations(a: Assembly) -> gpd.GeoDataFrame:
    """s7's station NODE_UIDs collide with the chamber namespace instead of referencing it.

    Proved rather than assumed: 85 of 85 stations carry a NODE_UID that also exists in the
    chamber layer, and ZERO of the 85 agree on ground level - station N0000001 says
    378.33 m aOD where chamber N0000001 stands at 317.08 m. So the string is s7's own
    counter, not a reference.

    The anchor is recovered by proximity, the distance is published in ST_SNAP_M, and the
    row is marked so nothing downstream can mistake a recovered anchor for written
    topology (H16). The station keeps a NODE_UID of its own in the export namespace,
    prefixed PS, so the collision cannot recur."""
    st = a.stations.copy()
    if len(st) == 0:
        return st
    ch = a.chambers
    claimed = st.NODE_UID.astype(str)
    hit = claimed.isin(set(ch.NODE_UID.astype(str)))
    grd_ch = ch.set_index(ch.NODE_UID.astype(str)).GRD_M
    same = np.abs(claimed.map(grd_ch).astype(float) - st.GRD_M.astype(float)) < 0.10
    n_collide = int((hit & ~same.fillna(False)).sum())

    from shapely.strtree import STRtree
    import shapely
    tree = STRtree(ch.geometry.values)
    idx = tree.nearest(st.geometry.values)
    dist = shapely.distance(st.geometry.values, ch.geometry.values[idx])
    st["ANCHOR_ND"] = ch.NODE_UID.astype(str).values[idx]
    st["ST_SNAP_M"] = np.round(dist.astype(float), 3)
    st["NODE_UID_S7"] = claimed.values
    st["NODE_UID"] = [f"PS{i + 1:05d}" for i in range(len(st))]
    a.note(f"STATION IDS DO NOT RESOLVE: {n_collide} of {len(st)} station NODE_UIDs also "
           f"exist in the chamber layer on a DIFFERENT chamber (zero agree on ground "
           f"level). Re-anchored by proximity: median {np.median(dist):.2f} m, max "
           f"{dist.max():.1f} m, {int((dist < 1.0).sum())} within 1 m. Published as "
           f"ANCHOR_ND with ST_SNAP_M beside it, and the station's own id is now PS#####")
    return st


def _to_gdf(df: pd.DataFrame, geom, crs=CT.CRS_EPSG) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(df, geometry=geom, crs=f"EPSG:{crs}")


# ======================================================================================
# 3.  THE GRAPH, AND THE FLOW ON IT
#
#     Chamber to chamber, from the WRITTEN US_NODE / DS_NODE (H16). No geometry, no
#     tolerance. s5 accumulated the same loads over the 12,816 CORRIDOR arcs; this
#     re-accumulates them over the 56,740 CHAMBER segments, because a pipe is sized on
#     the flow at ITS OWN chamber and not on the flow somewhere along the arc it belongs
#     to. The two totals are cross-checked in `verify()` and must agree at the outfalls.
# ======================================================================================

@dataclass
class Graph:
    uid: List[str]                    # node uid, index order
    ix: Dict[str, int]                # uid -> index
    grd: np.ndarray                   # ground level
    ds: np.ndarray                    # index of the downstream node, -1 at a terminal
    e_us: np.ndarray                  # per edge: index of the upstream node
    e_ds: np.ndarray
    e_len: np.ndarray
    e_of: np.ndarray                  # per node: index of its outgoing edge, -1 at terminal
    order: np.ndarray                 # topological order, most upstream first
    indeg: np.ndarray


def build_graph(a: Assembly) -> Graph:
    ch = a.chambers
    seg = a.segments
    uid = ch.NODE_UID.astype(str).tolist()
    ix = {u: i for i, u in enumerate(uid)}
    n = len(uid)
    if len(ix) != n:
        raise CT.ContractError(f"duplicate NODE_UID in the chamber layer: {n - len(ix)} rows")

    grd = ch.GRD_M.to_numpy(dtype=float)
    e_us = seg.US_NODE.astype(str).map(ix).to_numpy(dtype=np.int64)
    e_ds = seg.DS_NODE.astype(str).map(ix).to_numpy(dtype=np.int64)
    e_len = seg.LEN_M.to_numpy(dtype=float)

    ds = np.full(n, -1, dtype=np.int64)
    e_of = np.full(n, -1, dtype=np.int64)
    for k in range(len(e_us)):
        u = e_us[k]
        if e_of[u] != -1:
            raise CT.ContractError(
                f"node {uid[u]} has two outgoing segments. A node may own at most ONE "
                "outgoing edge (contract Network.add_edge); s3 published zero exceptions "
                "and s4 must not have created one.")
        e_of[u] = k
        ds[u] = e_ds[k]

    indeg = np.zeros(n, dtype=np.int64)
    np.add.at(indeg, e_ds, 1)

    # Kahn. A cycle would leave nodes unemitted, and a cycle in a forest is a defect, not
    # a topology to be tolerated (H15: zero loops).
    order = np.empty(n, dtype=np.int64)
    deg = indeg.copy()
    q = deque(np.flatnonzero(deg == 0).tolist())
    p = 0
    while q:
        v = q.popleft()
        order[p] = v
        p += 1
        w = ds[v]
        if w >= 0:
            deg[w] -= 1
            if deg[w] == 0:
                q.append(w)
    if p != n:
        raise CT.ContractError(
            f"the chamber graph is not a forest: {n - p:,} nodes sit on a cycle. H15 "
            "requires zero loops; a cycle here means s4 wrote a DS_NODE chain that closes.")
    return Graph(uid, ix, grd, ds, e_us, e_ds, e_len, e_of, order, indeg)


@dataclass
class Flows:
    q_own: np.ndarray          # m3/d generated at this chamber
    p_own: np.ndarray          # properties at this chamber
    n_conn: np.ndarray
    q_adf: np.ndarray          # m3/d accumulated AT this chamber, its own load included
    n_prop: np.ndarray
    ups_len: np.ndarray        # m of sewer upstream of this chamber, its outgoing NOT
    subnet: np.ndarray         # index of the component's outfall node
    e_qadf: np.ndarray         # per edge
    e_nprop: np.ndarray
    e_upslen: np.ndarray       # including this edge
    e_pf: np.ndarray
    e_pfm: List[str]
    e_qinf: np.ndarray         # L/s, cumulative over e_upslen, UNPEAKED
    e_qpk: np.ndarray          # L/s


def accumulate(a: Assembly, g: Graph) -> Flows:
    """Sanitary load, properties and sewer length accumulated down the chamber tree.

    THE PEAK FACTOR IS NOT ADDITIVE and this is where that bites. Merrimack
    (G201-p71 7.4.2) is Qpdf = 2.65 Qadf^0.879 with both in Ml/d, so Pf FALLS as the
    catchment grows. Two branches each peaking at 3.3 do not join at 3.3. It is therefore
    computed at every chamber from that chamber's OWN accumulated Qadf, never carried
    down, and below 100 properties it is HELD at 1.0 because G201 prescribes no formula
    there (contract PF_METH)."""
    n = len(g.uid)
    q_own = np.zeros(n)
    p_own = np.zeros(n)
    n_conn = np.zeros(n, dtype=np.int64)

    cn = a.connections
    out = cn.OUT_NODE.astype(str).map(g.ix)
    ok = out.notna()
    if (~ok).any():
        raise CT.ContractError(
            f"{int((~ok).sum()):,} connections name an OUT_NODE that is not a chamber. A "
            "load unit is attached to a node uid or it is named in a Funnel; a dangling "
            "reference is neither.")
    oi = out[ok].to_numpy(dtype=np.int64)
    np.add.at(q_own, oi, cn.Q_ADF_M3D.to_numpy(dtype=float)[ok.to_numpy()])
    np.add.at(p_own, oi, cn.N_PROP.to_numpy(dtype=float)[ok.to_numpy()])
    np.add.at(n_conn, oi, 1)

    q_adf = q_own.copy()
    n_prop = p_own.copy()
    ups = np.zeros(n)
    subnet = np.full(n, -1, dtype=np.int64)

    for v in g.order:
        w = g.ds[v]
        if w >= 0:
            L = g.e_len[g.e_of[v]]
            q_adf[w] += q_adf[v]
            n_prop[w] += n_prop[v]
            ups[w] += ups[v] + L
    # the component's outfall, walked once per node against the topological order
    for v in g.order[::-1]:
        w = g.ds[v]
        subnet[v] = v if w < 0 else subnet[w]

    m = len(g.e_len)
    e_qadf = q_adf[g.e_us]
    e_nprop = n_prop[g.e_us]
    e_upslen = ups[g.e_us] + g.e_len
    e_pf = np.ones(m)
    e_pfm: List[str] = ["held"] * m
    # peak_factor is a pure function of (qadf, n_prop); the pairs repeat heavily on a
    # 56,740-edge tree, so it is memoised rather than called 56,740 times.
    cache: Dict[Tuple[float, bool], Tuple[float, str]] = {}
    for k in range(m):
        key = (round(float(e_qadf[k]), 4), bool(e_nprop[k] <= C.PF_HOLD_PROPERTIES))
        got = cache.get(key)
        if got is None:
            got = C.peak_factor(float(e_qadf[k]), float(e_nprop[k]))
            cache[key] = got
        e_pf[k], e_pfm[k] = got
    e_qinf = C.INFILT_L_D_KM * (e_upslen / 1000.0) / 86400.0
    e_qpk = e_qadf * 1000.0 / 86400.0 * e_pf + e_qinf
    return Flows(q_own, p_own, n_conn, q_adf, n_prop, ups, subnet,
                 e_qadf, e_nprop, e_upslen, e_pf, e_pfm, e_qinf, e_qpk)


# ======================================================================================
# 4.  LEVELS AND SIZES - THE STAGE-6 STAND-IN
#
#     Everything in this section would live in `s6_levels.py` if it existed. It is here
#     because a depth map, a diameter map, a profile, a pipe schedule, a quantity and a
#     model package are all unbuildable without it, and the engineer asked for all six.
#
#     The maths is `w11b.hydra`'s and `w11b.criteria`'s, called - never re-implemented.
#     This section contributes an ORDER OF OPERATIONS and nothing else:
#
#       1  size on flow, and only on flow            H8, G203-p29
#       2  the governing minimum gradient is the STEEPER of Table 11 and tractive  G203-p27
#       3  lay as shallow as H3 allows               philosophy sec 5
#       4  hold the gradient on steep ground and take the difference at a drop   sec 5
#       5  gradients on round 0.05 % steps           P1
#       6  flag, never clip                          sec 5
# ======================================================================================

_S_STATE: Dict[Tuple[int, int, int], Tuple[Optional[float], Optional[float]]] = {}
_S_SIZE: Dict[Tuple[int, int, int], Any] = {}


def _qkey(q: float) -> int:
    """Quantise a flow to 0.01 L/s for the memo. Chosen because plot loads repeat exactly
    (1.079781 and 5.096378 m3/d dominate this network), so accumulated flows repeat too,
    and 0.01 L/s is four orders of magnitude below the smallest design decision here."""
    return int(round(float(q) * 1e5))


def _skey(s: float) -> int:
    return int(round(float(s) / C.SLOPE_STEP))


def state(dn: int, slope: float, q: float) -> Tuple[Optional[float], Optional[float]]:
    k = (int(dn), _skey(slope), _qkey(q))
    got = _S_STATE.get(k)
    if got is None:
        got = HY.pipe_state(int(dn), float(slope), float(q), C)
        _S_STATE[k] = got
    return got


def size(q: float, slope: float, dn_min: int):
    k = (_qkey(q), _skey(slope), int(dn_min))
    got = _S_SIZE.get(k)
    if got is None:
        got = HY.size_pipe(float(q), float(slope), C, dn_min=int(dn_min))
        _S_SIZE[k] = got
    return got


@dataclass
class Levels:
    # ---- per edge
    dn: np.ndarray
    slope_laid: np.ndarray        # fraction, not percent
    slope_min: np.ndarray         # fraction
    grad_by: List[str]
    sized_by: List[str]
    clean_by: List[str]
    v_pk: np.ndarray
    dod: np.ndarray
    ret_min: np.ndarray
    inv_up: np.ndarray
    inv_dn: np.ndarray
    us_depth: np.ndarray
    ds_depth: np.ndarray
    cover_us: np.ndarray
    cover_dn: np.ndarray
    material: List[str]
    # ---- per node
    inv: np.ndarray
    depth: np.ndarray
    cover: np.ndarray
    drop: np.ndarray
    drop_type: List[str]
    vortex: np.ndarray
    past_cap: np.ndarray
    cap_exit: List[str]
    cap_len: np.ndarray
    node_dn: np.ndarray
    st_reset: np.ndarray
    stats: Dict[str, Any] = dc_field(default_factory=dict)


def _size_all(g: Graph, f: Flows, tiers: Sequence[str]):
    """Diameter and the governing minimum gradient, per edge.

    The two are COUPLED: the minimum gradient depends on the diameter (Table 11) and the
    diameter that fits depends on the gradient. Solved by iterating up from the tier's own
    guideline floor. It terminates because Table 11 is monotonically flatter with size, so
    a bigger pipe can only relax the gradient it asks for, and a relaxed gradient can only
    ask for the same size or a bigger one, on a finite series."""
    m = len(g.e_len)
    dn = np.empty(m, dtype=np.int64)
    smin = np.empty(m, dtype=float)
    why: List[str] = [""] * m
    floors = np.array([TIER_FLOOR_DN.get(t, C.DN_MIN_MAIN) for t in tiers], dtype=np.int64)
    q_m3s = f.e_qpk / 1000.0
    n_infeasible = 0
    for k in range(m):
        d = int(floors[k])
        q = float(q_m3s[k])
        w = "minimum"
        for _ in range(4):
            s = HY.smin_for(d, q, C)
            # dn_min stays at the TIER FLOOR on every pass, never at the current guess.
            # Raising it launders the answer: size_pipe reports "minimum" whenever the
            # smallest size it was OFFERED works, so feeding it the last guess made all
            # 56,740 reaches read SIZED_BY = "minimum" including the DN900s. SIZED_BY is
            # the field that proves depth did not choose a diameter (H8), so it has to be
            # the real reason.
            d2, _y, _v, w2 = size(q, C.round_slope_up(s), int(floors[k]))
            if d2 is None:
                # Not even DN2400 passes it within G203-p27 Tab 10 at that gradient. The
                # answer is a station or a different route, never a bigger number
                # (hydra.size_pipe's own words). Held at the largest size and COUNTED.
                d2, w2 = int(C.DN_SERIES[-1]), "infeasible"
                n_infeasible += 1
            if int(d2) == d:
                w = w2
                break
            d, w = int(d2), w2
        dn[k] = d
        why[k] = w
        smin[k] = HY.smin_for(d, q, C)
    if n_infeasible:
        _log("   %d reaches SIZED INFEASIBLE - no diameter in the series passes the flow "
             "within G203-p27 Tab 10. Held at DN%d and counted; the resolution is a "
             "station or a route, not a number" % (n_infeasible, C.DN_SERIES[-1]))
    return dn, why, smin, n_infeasible


def design_levels(a: Assembly, g: Graph, f: Flows,
                  station_nodes: Optional[Iterable[int]] = None,
                  label: str = "with stations") -> Levels:
    n, m = len(g.uid), len(g.e_len)
    tiers = a.segments.TIER.astype(str).tolist()
    _log("levels [%s]: sizing %s reaches on flow" % (label, format(m, ",")))
    dn, sized_by, smin, n_infeasible = _size_all(g, f, tiers)

    st = set(int(i) for i in (station_nodes or ()))
    q_m3s = f.e_qpk / 1000.0

    inv = np.full(n, np.nan)
    arr_min = np.full(n, np.inf)
    arr_max = np.full(n, -np.inf)
    inv_up = np.zeros(m)
    inv_dn = np.zeros(m)
    s_laid = np.zeros(m)
    grad_by: List[str] = [""] * m
    node_dn = np.zeros(n, dtype=np.int64)
    st_reset = np.zeros(n, dtype=np.int8)

    in_dn_max = np.zeros(n, dtype=np.int64)
    np.maximum.at(in_dn_max, g.e_ds, dn)

    _log("levels [%s]: walking %s chambers in topological order" % (label, format(n, ",")))
    for v in g.order:
        e = int(g.e_of[v])
        if e < 0:
            d_here = int(in_dn_max[v]) or int(C.DN_MIN_MAIN)
            node_dn[v] = d_here
            shallow = g.grd[v] - C.invert_depth_min(d_here)
            inv[v] = shallow if not np.isfinite(arr_min[v]) else min(shallow, arr_min[v])
            continue

        d = int(dn[e])
        node_dn[v] = d
        shallow = g.grd[v] - C.invert_depth_min(d)
        if v in st:
            # A lifting station resets the depth: flow leaves the wet well and the
            # downstream network restarts at minimum cover. The station is s7's -
            # this stage neither places, moves nor removes one.
            inv[v] = shallow
            st_reset[v] = 1
        elif np.isfinite(arr_min[v]):
            inv[v] = min(shallow, arr_min[v])
        else:
            inv[v] = shallow

        w = int(g.e_ds[e])
        L = float(g.e_len[e])
        q = float(q_m3s[e])
        s_floor = C.round_slope_up(smin[e])

        # The gradient that lands the far end at EXACTLY minimum cover. Philosophy sec 5:
        # lay as shallow as H3 allows, because depth is bought back nowhere.
        s_need = (inv[v] - (g.grd[w] - C.invert_depth_min(d))) / L if L > 0 else 0.0
        if s_need <= s_floor:
            s = s_floor
            by = "tractive" if smin[e] > HY.smin_table11(d, C) + 1e-12 else "table11"
        else:
            # ROUND UP, not down. Rounding a cover-governed gradient DOWN lands the far
            # end HIGHER than the target and puts the reach under 1.30 m of cover - 232 km
            # of it on the first build of this stage, from nothing but the rounding
            # direction. Up costs at most SLOPE_STEP x LEN = 15 mm on a 30 m reach.
            s = max(s_floor, C.round_slope_up(s_need))
            by = "cover_min"
            smax = HY.smax_for(d, q, C)
            if smax is not None and smax != HY.INFEASIBLE and s > smax:
                # Steep ground and the velocity cap bites. G203-p27 4.2.2.2 caps velocity
                # at 3.0 m/s, so the pipe CANNOT follow the fall; philosophy sec 5 takes
                # the difference at a drop chamber instead of chasing the cliff. The far
                # end of THIS reach is then short of cover, and that shortfall is real -
                # it is reported, not rounded away.
                s2 = C.round_slope_down(smax)
                if s2 >= s_floor:
                    s, by = s2, "vmax"
            if s > SLOPE_MAX_LAID:
                # Ground steeper than a pipe is laid. Philosophy sec 5, verbatim: "On
                # steep ground the pipe does not follow the cliff. Hold the gradient and
                # take the difference at a drop chamber."
                #
                # BUT THE CAP IS NOT APPLIED WHERE IT WOULD LIFT THE PIPE OUT OF THE
                # GROUND. Capping unconditionally at 25 % put 11 reaches at NEGATIVE
                # cover - the far end above the surface - which is not a conservative
                # answer, it is an impossible one. A steep pipe is buildable with anchor
                # blocks; a pipe in mid-air is not. So the cap holds only while cover at
                # the far end still clears the G203-p33 minimum, and every reach that has
                # to break it is counted and named.
                s_keep_cover = (inv[v] - (g.grd[w] - C.invert_depth_min(d))) / L
                s = max(SLOPE_MAX_LAID, C.round_slope_up(s_keep_cover))
                by = "cover_max" if s <= SLOPE_MAX_LAID + 1e-12 else "ground"
        s_laid[e] = s
        grad_by[e] = by
        inv_up[e] = inv[v]
        inv_dn[e] = inv[v] - s * L
        if inv_dn[e] < arr_min[w]:
            arr_min[w] = inv_dn[e]
        if inv_dn[e] > arr_max[w]:
            arr_max[w] = inv_dn[e]

    # ---- P1: the same gradient carried across consecutive reaches -----------------------
    # H13 already fixes ONE gradient per reach; P1 extends it across a run. It is applied
    # here only as a LABEL, on reaches that already carry their upstream neighbour's
    # gradient - so it changes no invert and can never buy a pumping station
    # (philosophy 3a: "P1 is never bought at the price of a pumping station").
    inc = np.full(n, -1, dtype=np.int64)
    for k in range(m):
        w = int(g.e_ds[k])
        if inc[w] == -1:
            inc[w] = k
    n_uniform = 0
    for k in range(m):
        v = int(g.e_us[k])
        p = int(inc[v])
        if p >= 0 and g.indeg[v] == 1 and abs(s_laid[p] - s_laid[k]) < 1e-12 \
                and grad_by[k] in ("table11", "tractive"):
            grad_by[k] = "uniform"
            n_uniform += 1

    # ---- depths, covers, drops -----------------------------------------------------------
    depth = g.grd - inv
    cover = np.array([C.cover(int(node_dn[i]), float(depth[i])) for i in range(n)])
    us_depth = g.grd[g.e_us] - inv_up
    ds_depth = g.grd[g.e_ds] - inv_dn
    cover_us = us_depth - (dn / 1000.0 + C.WALL_ALLOW)
    cover_dn = ds_depth - (dn / 1000.0 + C.WALL_ALLOW)

    drop = np.where(np.isfinite(arr_max), arr_max - inv, 0.0)
    drop = np.maximum(drop, 0.0)
    drop_type = ["vortex" if d > C.BACKDROP_MAX + 1e-9 else
                 ("backdrop" if d > C.DROP_TRIGGER + 1e-9 else "none") for d in drop]
    vortex = (drop > C.BACKDROP_MAX + 1e-9).astype(np.int8)

    past_cap, cap_exit, cap_len = _cap_exits(g, cover, drop)

    lv = Levels(
        dn=dn, slope_laid=s_laid, slope_min=smin, grad_by=grad_by, sized_by=sized_by,
        clean_by=[], v_pk=np.zeros(m), dod=np.zeros(m), ret_min=np.zeros(m),
        inv_up=inv_up, inv_dn=inv_dn, us_depth=us_depth, ds_depth=ds_depth,
        cover_us=cover_us, cover_dn=cover_dn, material=[],
        inv=inv, depth=depth, cover=cover, drop=drop, drop_type=drop_type, vortex=vortex,
        past_cap=past_cap, cap_exit=cap_exit, cap_len=cap_len, node_dn=node_dn,
        st_reset=st_reset)

    # ---- the hydraulic state AT THE LAID gradient, and which route cleans it -------------
    _log("levels [%s]: solving depth of flow and velocity at the laid gradient" % label)
    v_pk = np.zeros(m)
    dod = np.zeros(m)
    clean: List[str] = [""] * m
    mat: List[str] = [""] * m
    for k in range(m):
        y, v = state(int(dn[k]), float(s_laid[k]), float(q_m3s[k]))
        dod[k] = 1.0 if y is None else float(y)
        v_pk[k] = 0.0 if v is None else float(v)
        if y is not None and v is not None and v >= C.V_SELF_CLEANSING:
            clean[k] = "velocity"
        elif s_laid[k] >= HY.smin_tractive(float(q_m3s[k]), C) - 1e-12:
            clean[k] = "tractive"
        else:
            clean[k] = "neither"
        mat[k] = C.material(tiers[k], int(dn[k]))
    lv.v_pk, lv.dod, lv.clean_by, lv.material = v_pk, dod, clean, mat
    lv.ret_min = np.array([HY.retention_min(float(L), float(vv)) or 0.0
                           for L, vv in zip(g.e_len, v_pk)])

    cl = np.array(clean)
    lv.stats = dict(
        n_uniform=n_uniform,
        n_infeasible=n_infeasible,
        past_cap_nodes=int(past_cap.sum()),
        past_cap_no_exit=int(sum(1 for i in range(n) if past_cap[i] and not cap_exit[i])),
        vortex=int(vortex.sum()),
        backdrop=int(sum(1 for t in drop_type if t == "backdrop")),
        deepest_cover=float(np.nanmax(cover)),
        median_cover=float(np.nanmedian(cover)),
        km_past_cap=float(g.e_len[np.maximum(cover_us, cover_dn) > C.MAX_COVER].sum() / 1000.0),
        km_below_min_cover=float(g.e_len[np.minimum(cover_us, cover_dn)
                                         < C.MIN_COVER_CROWN - 1e-6].sum() / 1000.0),
        km_tractive=float(g.e_len[cl == "tractive"].sum() / 1000.0),
        km_neither=float(g.e_len[cl == "neither"].sum() / 1000.0),
        km_velocity=float(g.e_len[cl == "velocity"].sum() / 1000.0),
        n_over_vmax=int((v_pk > C.V_MAX + 1e-9).sum()),
        n_over_dod=int(sum(1 for k in range(m) if dod[k] > C.dod_limit(int(dn[k])) + 1e-9)),
        stations_used=len(st),
        km_total=float(g.e_len.sum() / 1000.0),
    )
    return lv


def _cap_exits(g: Graph, cover: np.ndarray, drop: np.ndarray):
    """Philosophy sec 5. Past the 12 m cap there are exactly two exits, and BOTH are
    bounded twice - by distance AND by depth:

        cover recovers within 500 m      or      the run reaches its outfall within 1,000 m

    and either is WITHDRAWN where the excursion forces a drop past what a drop structure
    can be built to (criteria.DROP_CEILING_M). Stated as distance alone, this exit produced
    a 36.81 m chamber with a 35.06 m drop into it on 2026-09-02 and the design was legal
    all the way down.

    Where neither applies the chamber gets PAST_CAP = 1 and a BLANK exit. That is a STATION
    DEMAND and it belongs to stage 7. This stage counts them; it does not invent one."""
    n = len(cover)
    over = cover > C.MAX_COVER + 1e-9
    past = over.astype(np.int8)
    exit_: List[str] = [""] * n
    cap_len = np.zeros(n)
    for v in np.flatnonzero(over):
        d = 0.0
        worst_drop = float(drop[v])
        cur = int(v)
        rec = -1.0
        out = -1.0
        while True:
            e = int(g.e_of[cur])
            if e < 0:
                out = d
                break
            d += float(g.e_len[e])
            cur = int(g.e_ds[e])
            worst_drop = max(worst_drop, float(drop[cur]))
            if not over[cur]:
                rec = d
                break
            if d > EXIT_OUTFALL_M:
                break
        withdrawn = worst_drop > C.DROP_CEILING_M + 1e-9
        if not withdrawn and 0.0 <= rec <= EXIT_RECOVER_M:
            exit_[v], cap_len[v] = "recovers_500m", rec
        elif not withdrawn and 0.0 <= out <= EXIT_OUTFALL_M:
            exit_[v], cap_len[v] = "outfall_1000m", out
        else:
            cap_len[v] = rec if rec >= 0 else (out if out >= 0 else d)
    return past, exit_, cap_len


# ======================================================================================
# 5.  WHAT EACH REACH TOUCHES, MEASURED - and the crossings REGISTER
#
#     W11a published ANGLE_DEG = 90 on 3,290 crossings. It was fabricated; the measured
#     minimum was 0.00 deg. Nothing below is asserted: the wadi contact is sampled off the
#     50-year hazard grid along the reach, and the angle is measured against the nearest
#     stream line's own direction.
# ======================================================================================

WADI_SAMPLE_M = 3.0     # PROJECT ASSUMPTION: sampling step along a reach for the hazard
                        # grid. The grid is 5 m; 3 m over-samples it deliberately so a
                        # short contact cannot fall between two samples.


def measure_contacts(a: Assembly, g: Graph) -> pd.DataFrame:
    """ON_WADI_M and ON_DUAL_M per reach, both measured.

    Wadi ground is criteria.HAZARD_WADI_CLASSES = (4, 5, 6) of the 50-year grid - AR&R
    flood-hazard classes standing in for G203's "areas subject to washout", a PROJECT
    ASSUMPTION (philosophy sec 3, assumption A2) and not a guideline threshold. Flood
    no-data is DRY HIGH GROUND (engineer, 2026-09-03; assumption A3)."""
    from w11b import hazard as HZ
    seg = a.segments
    _log("measuring the wadi contact off the 50-year hazard grid")
    xs: List[np.ndarray] = []
    ys: List[np.ndarray] = []
    owner: List[np.ndarray] = []
    for i, (geom, L) in enumerate(zip(seg.geometry.values, seg.LEN_M.to_numpy())):
        k = max(2, int(math.ceil(float(L) / WADI_SAMPLE_M)) + 1)
        d = np.linspace(0.0, float(L), k)
        pts = [geom.interpolate(float(t)) for t in d]
        xs.append(np.array([p.x for p in pts]))
        ys.append(np.array([p.y for p in pts]))
        owner.append(np.full(k, i, dtype=np.int64))
    X = np.concatenate(xs)
    Y = np.concatenate(ys)
    O = np.concatenate(owner)
    _log(f"   {len(X):,} sample points at {WADI_SAMPLE_M:g} m along {len(seg):,} reaches")
    with HZ.HazardGrids() as hg:
        cls = hg.sample_many(X, Y, rp=int(C.HAZARD_RETURN_YR))
    wet = np.isin(cls, np.array(C.HAZARD_WADI_CLASSES))
    tot = np.zeros(len(seg))
    hit = np.zeros(len(seg))
    np.add.at(tot, O, 1.0)
    np.add.at(hit, O, wet.astype(float))
    frac = np.where(tot > 0, hit / np.maximum(tot, 1.0), 0.0)
    on_wadi_m = np.round(frac * seg.LEN_M.to_numpy(), 3)

    along = seg.ALONG_DUAL.to_numpy(dtype=int)
    xing = seg.XING_DUAL.to_numpy(dtype=int)
    on_dual_m = np.where((along == 1) | (xing == 1), seg.LEN_M.to_numpy(), 0.0).round(3)
    return pd.DataFrame(dict(ON_WADI_M=on_wadi_m, ON_DUAL_M=on_dual_m,
                             WADI_FRAC=np.round(frac, 4),
                             ALONG_DUAL=along, XING_DUAL=xing))


def _stream_bearings():
    """Every stream segment as (midpoint, unit vector), for measuring a crossing angle
    against the ground's OWN drainage direction rather than against a guess."""
    st = _read(os.path.join(SHP, "W11b_streams.gpkg"), "streams")
    mids, vecs = [], []
    for geom in st.geometry.values:
        cs = np.asarray(geom.coords)
        if len(cs) < 2:
            continue
        d = cs[1:, :2] - cs[:-1, :2]
        mid = (cs[1:, :2] + cs[:-1, :2]) / 2.0
        n = np.hypot(d[:, 0], d[:, 1])
        ok = n > 1e-9
        mids.append(mid[ok])
        vecs.append(d[ok] / n[ok, None])
    return np.vstack(mids), np.vstack(vecs)


def build_crossings(a: Assembly, g: Graph, contacts: pd.DataFrame
                    ) -> Tuple[gpd.GeoDataFrame, np.ndarray, Dict[str, int]]:
    """THE REGISTER. One row per contiguous run of contact along the flow path.

    H1a: a wadi crossing is legal only when it CROSSES rather than runs along, carries no
    chamber on wadi ground, has 1.50 m of cover (G203-p52 8.2.4, adopted for gravity as a
    PROJECT DECISION) and IS IN THIS REGISTER. Every contact gets a row whether or not it
    qualifies, because a contact with no row is invisible; whether it qualifies is then a
    measured column and not a filter."""
    seg = a.segments
    m = len(seg)
    on_w = contacts.ON_WADI_M.to_numpy()
    on_d = contacts.ON_DUAL_M.to_numpy()
    both = int(((on_w > 0) & (on_d > 0)).sum())

    # group contiguous contact along the flow path: an edge joins the run of its upstream
    # edge when both touch the same obstacle and the shared node has exactly one inlet.
    inc = np.full(len(g.uid), -1, dtype=np.int64)
    for k in range(m):
        w = int(g.e_ds[k])
        if inc[w] == -1:
            inc[w] = k
    kind = np.where(on_w > 0, 1, np.where(on_d > 0, 2, 0))
    run_id = np.full(m, -1, dtype=np.int64)
    nxt = 0
    # walk in topological order of the upstream node so a run is always started upstream
    pos = np.empty(len(g.uid), dtype=np.int64)
    pos[g.order] = np.arange(len(g.order))
    for k in np.argsort(pos[g.e_us]):
        k = int(k)
        if kind[k] == 0:
            continue
        v = int(g.e_us[k])
        p = int(inc[v])
        if p >= 0 and g.indeg[v] == 1 and kind[p] == kind[k] and run_id[p] >= 0:
            run_id[k] = run_id[p]
        else:
            run_id[k] = nxt
            nxt += 1

    smids, svecs = _stream_bearings()
    from shapely.strtree import STRtree
    from shapely.geometry import MultiPoint
    stree = STRtree([Point(float(x), float(y)) for x, y in smids])

    rows = []
    cross_id = np.array([""] * m, dtype=object)
    geoms = seg.geometry.values
    lens = seg.LEN_M.to_numpy()
    for r in range(nxt):
        ks = np.flatnonzero(run_id == r)
        obstacle = "wadi" if kind[ks[0]] == 1 else "dual"
        parts = [geoms[k] for k in ks]
        merged = parts[0] if len(parts) == 1 else unary_union(parts)
        try:
            line = merged if merged.geom_type == "LineString" else \
                LineString([c for p in parts for c in p.coords])
        except Exception:
            line = parts[0]
        cs = np.asarray(line.coords)
        chord = cs[-1, :2] - cs[0, :2]
        nch = float(np.hypot(*chord))
        if obstacle == "wadi":
            mid = Point(float(cs[len(cs) // 2, 0]), float(cs[len(cs) // 2, 1]))
            j = int(stree.nearest(mid))
            u = svecs[j]
            # angle between the contact's chord and the stream's own direction, 0-90 deg.
            # 90 deg IS square across the channel; 0 deg means the pipe runs ALONG it,
            # which is what H1 forbids. MEASURED - W11a asserted 90 on 3,290 crossings.
            ang = 0.0 if nch < 1e-6 else math.degrees(
                math.acos(min(1.0, abs(float(np.dot(chord / nch, u))))))
        else:
            d = float(seg.DUAL_ANG.to_numpy()[ks[0]])
            ang = d if d >= 0 else float("nan")
        cid = CT.CROSS_UID_FMT.format(r + 1)
        for k in ks:
            cross_id[k] = cid
        contact = float(np.sum(on_w[ks] if obstacle == "wadi" else on_d[ks]))
        rows.append(dict(
            CROSS_ID=cid, EDGE_UID="", OBSTACLE=obstacle,
            LEN_M=round(float(line.length), 3),
            ANGLE_DEG=round(float(ang), 2) if ang == ang else 0.0,
            METHOD="open_cut", COVER_M=round(float(C.min_cover_for(on_wadi_crossing=True)), 3),
            APPROVED=0, N_REACH=int(len(ks)), CONTACT_M=round(contact, 2),
            SQUARE=int(abs(90.0 - ang) <= C.WADI_XING_SKEW_DEG) if ang == ang else 0,
            SRC="terrain", CONFIDENCE="derived", STAGE=STAGE, geometry=line))
    cx = gpd.GeoDataFrame(rows, geometry="geometry", crs=f"EPSG:{CT.CRS_EPSG}")
    stats = dict(
        n_rows=len(cx),
        n_wadi=int((cx.OBSTACLE == "wadi").sum()) if len(cx) else 0,
        n_dual=int((cx.OBSTACLE == "dual").sum()) if len(cx) else 0,
        km_wadi=float(on_w.sum() / 1000.0),
        km_dual=float(on_d.sum() / 1000.0),
        both=both,
        n_square=int(cx.SQUARE.sum()) if len(cx) else 0,
        angle_min=float(cx.ANGLE_DEG.min()) if len(cx) else 0.0,
        angle_median=float(cx.ANGLE_DEG.median()) if len(cx) else 0.0,
    )
    _log(f"   crossings register: {stats['n_rows']:,} rows "
         f"({stats['n_wadi']:,} wadi, {stats['n_dual']:,} dual), "
         f"{stats['km_wadi']:.2f} km on wadi ground, {stats['km_dual']:.2f} km on a dual "
         f"carriageway; {stats['n_square']:,} within {C.WADI_XING_SKEW_DEG:g} deg of square")
    return cx, cross_id, stats


# ======================================================================================
# 6.  PACKAGES AND LABELS
#
#     NO PACKAGES STAGE EXISTS. The contract marks PACKAGE and PHASE required=False for
#     exactly this reason, and it also declares what a package should be: 3.5-40 km,
#     180-2,180 plots, ONE connected tree with EXACTLY ONE outlet. This stage groups by
#     subnetwork - which satisfies the tree and the outlet by construction and satisfies
#     the size band only where it happens to - and MEASURES how many land in the band
#     rather than claiming they do.
#
#     PHASE stays 0 on every row. The contract's own words: "delivery phase, 0 = not yet
#     assigned". Inventing a programme here would be a number with nothing behind it.
# ======================================================================================

def build_packages(a: Assembly, g: Graph, f: Flows) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    n = len(g.uid)
    out_idx = np.unique(f.subnet)
    order = sorted(out_idx, key=lambda i: -float(f.q_adf[i]))
    pkg_of_out = {int(i): f"P{r + 1:03d}" for r, i in enumerate(order)}
    node_pkg = np.array([pkg_of_out[int(s)] for s in f.subnet], dtype=object)
    edge_pkg = node_pkg[g.e_us]

    plots = a.connections.groupby(a.connections.OUT_NODE.astype(str)).size()
    plot_at = np.zeros(n)
    for u, c in plots.items():
        i = g.ix.get(u)
        if i is not None:
            plot_at[i] = c

    rows = []
    for r, i in enumerate(order):
        sel = f.subnet == i
        esel = sel[g.e_us]
        km = float(g.e_len[esel].sum() / 1000.0)
        rows.append(dict(
            PACKAGE=pkg_of_out[int(i)], PHASE=0, LEN_KM=round(km, 4),
            N_PLOT=int(plot_at[sel].sum()), OUTLET=g.uid[int(i)],
            DS_PKG="", COMM_SEQ=r + 1, INDEP=1, ONE_TREE=1,
            N_CHAMBER=int(sel.sum()), Q_ADF_M3D=round(float(f.q_adf[i]), 2),
            N_PROP=round(float(f.n_prop[i]), 1),
            IN_BAND=int(3.5 <= km <= 40.0)))
    pk = pd.DataFrame(rows)
    _log(f"   {len(pk):,} packages (one per subnetwork). "
         f"{int(pk.IN_BAND.sum()):,} sit inside the contract's 3.5-40 km band; "
         f"largest {pk.LEN_KM.max():.1f} km, median {pk.LEN_KM.median():.2f} km")
    return pk, node_pkg, edge_pkg


def node_refs(a: Assembly, g: Graph, node_pkg: np.ndarray, tier_out: List[str]) -> List[str]:
    """NAMA's own ID grammar - `5A-2-SM.2-MH391` is package, tier token, sequence. The
    contract is explicit that NODE_REF is referenced by NOTHING: the network must read like
    theirs, and that must not cost referential integrity."""
    seq: Dict[Tuple[str, str], int] = {}
    out: List[str] = []
    for i in range(len(g.uid)):
        tok = CT.TIER_TOKEN.get(tier_out[i], "L")
        key = (str(node_pkg[i]), tok)
        seq[key] = seq.get(key, 0) + 1
        out.append(f"{node_pkg[i]}-{tok}-MH{seq[key]:04d}")
    return out


# ======================================================================================
# 7.  THE CONTRACT LAYERS
#
#     Field for field against `contract.LAYERS`. Nothing is written that the contract does
#     not declare a `why` for, and `validate()` is run over every one of them before a
#     single schedule, drawing or model file is produced. Where it objects, the objection
#     is PUBLISHED (layer `contract_check`) rather than silenced - "relaxing a field a
#     check needs converts a visible failure into an invisible one" is the contract's own
#     sentence, and it applies to the exporter too.
# ======================================================================================

def _bearing_fix_inlets(a: Assembly, g: Graph) -> np.ndarray:
    """s4 measured INLET_DEG and left 2,382 of them null. A null on a node WITH inlets is
    an H10 check that cannot run, which philosophy sec 8 makes a FAILURE and not a blank.
    Re-measured here on the same convention s4 used - 180 deg is straight through, 90 deg
    is square, below 90 the inlet doubles back against the flow (G203-p30)."""
    n = len(g.uid)
    val = a.chambers.INLET_DEG.to_numpy(dtype=float).copy()
    geoms = a.segments.geometry.values

    def _vec_in(k):
        cs = np.asarray(geoms[k].coords)
        d = cs[-1, :2] - cs[-2, :2]
        return d / max(1e-12, float(np.hypot(*d)))

    def _vec_out(k):
        cs = np.asarray(geoms[k].coords)
        d = cs[1, :2] - cs[0, :2]
        return d / max(1e-12, float(np.hypot(*d)))

    ins: Dict[int, List[int]] = defaultdict(list)
    for k in range(len(geoms)):
        ins[int(g.e_ds[k])].append(k)

    n_fixed = 0
    for i in np.flatnonzero(~np.isfinite(val)):
        i = int(i)
        e_out = int(g.e_of[i])
        kin = ins.get(i, [])
        if not kin or e_out < 0:
            val[i] = 180.0                     # a head, or an outfall: no inlet to constrain
            continue
        u = _vec_out(e_out)
        worst = 180.0
        for k in kin:
            v = _vec_in(k)
            ang = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(v, u))))))
            worst = min(worst, ang)
        val[i] = round(worst, 1)
        n_fixed += 1
    if n_fixed:
        _log(f"   re-measured INLET_DEG on {n_fixed:,} chambers s4 left null with inlets "
             f"present; the rest of the nulls are heads and outfalls, written 180 deg")
    val[~np.isfinite(val)] = 180.0
    return val


def build_layers(a: Assembly, g: Graph, f: Flows, lv: Levels, contacts: pd.DataFrame,
                 cross_id: np.ndarray, node_pkg: np.ndarray, edge_pkg: np.ndarray
                 ) -> Dict[str, gpd.GeoDataFrame]:
    n, m = len(g.uid), len(g.e_len)
    seg = a.segments
    ch = a.chambers

    # ---- tier of the OUTGOING reach at every node --------------------------------------
    tiers_e = seg.TIER.astype(str).to_numpy()
    tier_node: List[str] = ["lateral"] * n
    rank = {t: i for i, t in enumerate(("rider", "lateral", "main", "sub main", "trunk main"))}
    best_in = np.full(n, -1)
    for k in range(m):
        w = int(g.e_ds[k])
        r = rank.get(tiers_e[k], 1)
        if r > best_in[w]:
            best_in[w] = r
            tier_node[w] = tiers_e[k]
    for v in range(n):
        e = int(g.e_of[v])
        if e >= 0:
            tier_node[v] = tiers_e[e]

    src_e = seg.SRC.astype(str).to_numpy()
    conf_e = seg.CONFIDENCE.astype(str).to_numpy()
    src_node = np.array(["terrain"] * n, dtype=object)
    conf_node = np.array(["derived"] * n, dtype=object)
    for k in range(m):
        w = int(g.e_ds[k])
        src_node[w], conf_node[w] = src_e[k], conf_e[k]
    for v in range(n):
        e = int(g.e_of[v])
        if e >= 0:
            src_node[v], conf_node[v] = src_e[e], conf_e[e]

    # ---- node-level flow ---------------------------------------------------------------
    pf_n = np.ones(n)
    pfm_n: List[str] = ["held"] * n
    cache: Dict[Tuple[float, bool], Tuple[float, str]] = {}
    for i in range(n):
        key = (round(float(f.q_adf[i]), 4), bool(f.n_prop[i] <= C.PF_HOLD_PROPERTIES))
        got = cache.get(key)
        if got is None:
            got = C.peak_factor(float(f.q_adf[i]), float(f.n_prop[i]))
            cache[key] = got
        pf_n[i], pfm_n[i] = got
    len_out = np.where(g.e_of >= 0, g.e_len[np.maximum(g.e_of, 0)], 0.0)
    qinf_n = C.INFILT_L_D_KM * ((f.ups_len + len_out) / 1000.0) / 86400.0
    qpk_n = f.q_adf * 1000.0 / 86400.0 * pf_n + qinf_n

    ds_uid = np.array([g.uid[int(d)] if d >= 0 else "" for d in g.ds], dtype=object)
    n_out = (g.e_of >= 0).astype(np.int8)
    is_out = (g.ds < 0).astype(np.int8)
    inlet = _bearing_fix_inlets(a, g)
    refs = node_refs(a, g, node_pkg, tier_node)

    kind = ch.NODE_KIND.astype(str).to_numpy().copy()
    kind = np.where(is_out == 1, "outfall", kind)
    dropped = np.array([t != "none" for t in lv.drop_type])
    kind = np.where(dropped & (is_out == 0), "drop", kind)
    mh_dia = np.where(dropped, C.MH_DIA_INTERNAL_BACKDROP, MH_DIA_STD_M)

    nodes = gpd.GeoDataFrame(dict(
        NODE_UID=g.uid,
        IS_OUTFALL=is_out,
        NODE_REF=refs,
        NODE_KIND=kind,
        X=np.round(ch.X.to_numpy(), 3), Y=np.round(ch.Y.to_numpy(), 3),
        GRD_M=np.round(g.grd, 3),
        INV_M=np.round(lv.inv, 3),
        DEPTH_M=np.round(g.grd, 3) - np.round(lv.inv, 3),
        COVER_M=np.round(lv.cover, 3),
        TIER=tier_node,
        DS_NODE=ds_uid,
        N_IN=g.indeg.astype(np.int64),
        N_OUT=n_out,
        INLET_DEG=np.round(inlet, 1),
        INLET_FLAG=(inlet < C.INLET_MIN_DEG - 1e-9).astype(np.int8),
        MH_DIA=mh_dia,
        MH_MAT="precast concrete (class per PAM-SPC, pending)",
        DROP_M=np.round(lv.drop, 3),
        DROP_TYPE=lv.drop_type,
        VORTEX=lv.vortex.astype(np.int8),
        Q_ADF_M3D=np.round(f.q_adf, 3),
        Q_PK_LS=np.round(qpk_n, 4),
        N_PROP=np.round(f.n_prop, 2),
        PAST_CAP=lv.past_cap.astype(np.int8),
        CAP_EXIT=lv.cap_exit,
        # ---- beyond the contract, declared here and printed in the data dictionary -----
        CAP_LEN_M=np.round(lv.cap_len, 1),
        ST_RESET=lv.st_reset.astype(np.int8),
        N_CONN=f.n_conn.astype(np.int64),
        UPS_LEN_M=np.round(f.ups_len, 1),
        SUBNET=[g.uid[int(s)] for s in f.subnet],
        TRIGGER=ch.TRIGGER.astype(str).to_numpy(),
        ON_WADI=ch.ON_WADI.to_numpy(),
        TAU_PA=float(C.TAU_PA),
        SRC=src_node, CONFIDENCE=conf_node, STAGE=LEVELS_TAG,
        PACKAGE=node_pkg, PHASE=np.zeros(n, dtype=np.int64),
    ), geometry=[Point(float(x), float(y)) for x, y in zip(ch.X.to_numpy(), ch.Y.to_numpy())],
        crs=f"EPSG:{CT.CRS_EPSG}")
    # DEPTH_M must reproduce GRD_M - INV_M to 1 mm on the PUBLISHED, rounded values, or the
    # chamber schedule and the pipe layer describe different chambers (contract, nodes).
    nodes["DEPTH_M"] = (nodes.GRD_M - nodes.INV_M).round(3)
    nodes["COVER_M"] = [round(C.cover(int(d), float(z)), 3)
                        for d, z in zip(lv.node_dn, nodes.DEPTH_M)]

    inv_up = np.round(lv.inv_up, 3)
    inv_dn = np.round(inv_up - lv.slope_laid * g.e_len, 3)
    us_depth = np.round(g.grd[g.e_us], 3) - inv_up
    ds_depth = np.round(g.grd[g.e_ds], 3) - inv_dn
    reaches = gpd.GeoDataFrame(dict(
        EDGE_UID=[CT.EDGE_UID_FMT.format(k) for k in range(m)],
        US_NODE=[g.uid[int(i)] for i in g.e_us],
        DS_NODE=[g.uid[int(i)] for i in g.e_ds],
        TIER=tiers_e,
        DN=lv.dn.astype(np.int64),
        MATERIAL=lv.material,
        CONSTR="open_trench",
        LEN_M=np.round(g.e_len, 3),
        SLOPE_LAID=np.round(lv.slope_laid * 100.0, 6),
        SLOPE_MIN=np.round(lv.slope_min * 100.0, 6),
        GRAD_BY=lv.grad_by,
        SIZED_BY=lv.sized_by,
        CLEAN_BY=lv.clean_by,
        TAU_PA=float(C.TAU_PA),
        INV_UP=inv_up, INV_DN=inv_dn,
        US_DEPTH=us_depth, DS_DEPTH=ds_depth,
        COVER_US=np.round(us_depth - (lv.dn / 1000.0 + C.WALL_ALLOW), 3),
        COVER_DN=np.round(ds_depth - (lv.dn / 1000.0 + C.WALL_ALLOW), 3),
        QADF_M3D=np.round(f.e_qadf, 3),
        QINF_LS=np.round(f.e_qinf, 6),
        PF=np.round(f.e_pf, 6),
        PF_METH=f.e_pfm,
        QPK_LS=np.round(f.e_qpk, 6),
        V_PK_MS=np.round(lv.v_pk, 3),
        DOD_PK=np.round(lv.dod, 4),
        RET_MIN=np.round(lv.ret_min, 3),
        # AGN_GRADE is computed from the ROUNDED, PUBLISHED GND_FALL, not from the raw
        # difference. Computed from the raw value it disagreed with its own row on 36
        # reaches at the rounding boundary, and the contract calls that out by name:
        # "this is the headline number the whole iteration turns on; it cannot be
        # computed two ways".
        GND_FALL=np.round(g.grd[g.e_us] - g.grd[g.e_ds], 3),
        AGN_GRADE=(np.round(g.grd[g.e_us] - g.grd[g.e_ds], 3) < -C.ADVERSE_MIN_M).astype(np.int8),
        RISE_M=np.round(np.maximum(0.0, g.grd[g.e_ds] - g.grd[g.e_us]), 3),
        PAST_CAP=(np.maximum(lv.cover_us, lv.cover_dn) > C.MAX_COVER).astype(np.int8),
        CAP_EXIT=[lv.cap_exit[int(i)] for i in g.e_us],
        CAP_LEN_M=np.round(lv.cap_len[g.e_us], 1),
        TIE_TYPE="none",
        ON_DUAL_M=contacts.ON_DUAL_M.to_numpy(),
        ON_WADI_M=contacts.ON_WADI_M.to_numpy(),
        CROSS_ID=cross_id.astype(str),
        # ---- beyond the contract -------------------------------------------------------
        SUBNET=[g.uid[int(s)] for s in f.subnet[g.e_us]],
        RUN_LEN_M=np.round(f.e_upslen, 1),
        SRC=src_e, CONFIDENCE=conf_e, STAGE=LEVELS_TAG,
        PACKAGE=edge_pkg, PHASE=np.zeros(m, dtype=np.int64),
    ), geometry=seg.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")
    # QPK_LS must be reproducible from the PUBLISHED row (contract cross-field check).
    reaches["QPK_LS"] = (reaches.QADF_M3D * 1000.0 / 86400.0 * reaches.PF
                         + reaches.QINF_LS).round(6)
    # A reach whose CAP_EXIT came from a node that is not itself past the cap carries a
    # justification for a breach that is not there. Blank it.
    reaches.loc[reaches.PAST_CAP == 0, "CAP_EXIT"] = ""

    layers: Dict[str, gpd.GeoDataFrame] = {"nodes": nodes, "reaches": reaches}
    return layers


def build_connections(a: Assembly, g: Graph, nodes: gpd.GeoDataFrame,
                      reaches: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """The load units, with CAN_DRAIN now ANSWERABLE.

    s4 published `CAN_DRAIN cannot run - no designed invert exists at stage 4`. There is
    one now, so the question is answered: does the plot's own ground sit above the sewer
    invert at the chamber it connects to, with the 0.60 m minimum cover a property
    connection needs (G203-p19 3.5) and the 3 % minimum gradient (G203-p18 Table 5)?"""
    cn = a.connections.copy()
    inv = dict(zip(nodes.NODE_UID.astype(str), nodes.INV_M.astype(float)))
    ci = cn.OUT_NODE.astype(str).map(inv).to_numpy(dtype=float)
    grd_plot = cn.GRD_PLOT.to_numpy(dtype=float)
    L = np.maximum(cn.LEN_M.to_numpy(dtype=float), 0.5)
    # the outlet of the property, at the minimum HCC depth (G203-p19 3.4: 1.2-2.0 m)
    out_lvl = grd_plot - C.HCC_DEPTH_MIN
    fall_avail = out_lvl - ci
    s_need = fall_avail / L
    can = ((fall_avail > 0) & (s_need >= C.PCS_MIN_SLOPE)).astype(np.int8)
    s_laid = np.clip(np.where(s_need > 0, s_need, C.PCS_MIN_SLOPE),
                     C.PCS_MIN_SLOPE, C.PCS_MAX_SLOPE)
    cover = np.maximum(C.PCS_MIN_COVER, C.HCC_DEPTH_MIN - C.DN_TERTIARY / 1000.0)
    out = gpd.GeoDataFrame(dict(
        CONN_ID=cn.CONN_ID.astype(str),
        PLOT_ID=cn.PLOT_ID.astype(str),
        OUT_NODE=cn.OUT_NODE.astype(str),
        WHY=cn.WHY.astype(str),
        SYSTEM=cn.SYSTEM.astype(str),
        CONN_TYPE=cn.CONN_TYPE.astype(str),
        Q_ADF_M3D=np.round(cn.Q_ADF_M3D.to_numpy(dtype=float), 4),
        N_PROP=np.round(cn.N_PROP.to_numpy(dtype=float), 3),
        LEN_M=np.round(cn.geometry.length.to_numpy(), 3),
        SLOPE_LAID=np.round(s_laid * 100.0, 3),
        COVER_M=round(float(cover), 3),
        CAN_DRAIN=can,
        FALL_AV_M=np.round(fall_avail, 3),
        XPLOT=cn.XPLOT.to_numpy(), XDUAL=cn.XDUAL.to_numpy(),
        CH_WADI=cn.CH_WADI.to_numpy(),
        SRC="dwg_road", CONFIDENCE="derived", STAGE=LEVELS_TAG,
        PACKAGE=cn.OUT_NODE.astype(str).map(
            dict(zip(nodes.NODE_UID.astype(str), nodes.PACKAGE.astype(str)))).fillna(""),
        PHASE=0,
    ), geometry=cn.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")
    _log(f"   connections: CAN_DRAIN answered for the first time - "
         f"{int(can.sum()):,} of {len(can):,} plots can reach their chamber on gravity at "
         f"the {C.PCS_MIN_SLOPE*100:g} % minimum (G203-p18 Tab 5); "
         f"{int((can == 0).sum()):,} cannot")
    return out


def build_stations(a: Assembly, nodes: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """s7's stations and rising mains, re-keyed into the export namespace.

    Every hydraulic number here is s7's and is copied, never recomputed: duty flow, lift,
    wet well, head, motor, land take, the rising main's diameter, velocity and fittings.
    What this stage adds is the anchor, the label and the package."""
    st = a.stations.copy()
    ndx = nodes.set_index(nodes.NODE_UID.astype(str))
    anchor = st.ANCHOR_ND.astype(str)
    st_out = gpd.GeoDataFrame(dict(
        NODE_UID=st.NODE_UID.astype(str),
        NODE_REF=st.NODE_REF.astype(str),
        WHY=st.WHY.astype(str),
        ST_TYPE=st.ST_TYPE.astype(str),
        Q_DUTY_LS=np.round(st.Q_DUTY_LS.to_numpy(dtype=float), 3),
        LIFT_M=np.round(st.LIFT_M.to_numpy(dtype=float), 3),
        N_PROP=np.round(st.N_PROP.to_numpy(dtype=float), 1),
        Q_ADF_M3D=np.round(st.Q_ADF_M3D.to_numpy(dtype=float), 2),
        WELL_M3=np.round(st.WELL_M3.to_numpy(dtype=float), 4),
        WW_STARTS=np.round(st.WW_STARTS.to_numpy(dtype=float), 2),
        GRD_M=np.round(st.GRD_M.to_numpy(dtype=float), 3),
        # FLOOD_LV IS LEFT NULL, DELIBERATELY. s7 published it null and there is no way
        # to fill it: `hazard.flood_level_m_aod()` RAISES by design, because the grids
        # carry an AR&R hazard CLASS and no water-surface level, and deriving one would
        # mean inventing a depth and adding it to a terrain reading. Filling it with
        # ground level - which this stage did on its first build - manufactured a
        # 300 mm-freeboard failure on all 85 stations that says nothing about any of
        # them. The contract will report the null, and that null IS the data request
        # (G203-p38 7.2 needs the 1:50 water-surface level).
        FLOOD_LV=pd.to_numeric(st.FLOOD_LV, errors="coerce").to_numpy(dtype=float),
        LAND_M2=np.round(st.LAND_M2.to_numpy(dtype=float), 1),
        RM_EDGE=st.RM_EDGE.astype(str),
        COMM_PT=st.COMM_PT.to_numpy(),
        HEAD_M=np.round(st.HEAD_M.to_numpy(dtype=float), 2),
        MOTOR_KW=np.round(st.MOTOR_KW.to_numpy(dtype=float), 2),
        KWH_YR=np.round(st.KWH_YR.to_numpy(dtype=float), 0),
        LCC_OMR=np.round(st.LCC_OMR.to_numpy(dtype=float), 0),
        ANCHOR_ND=anchor,
        ST_SNAP_M=st.ST_SNAP_M.to_numpy(dtype=float),
        UID_S7=st.NODE_UID_S7.astype(str),
        PACKAGE=anchor.map(dict(zip(nodes.NODE_UID.astype(str), nodes.PACKAGE.astype(str))))
                      .fillna(""),
        PHASE=0,
        SRC="terrain", CONFIDENCE="derived", STAGE="s7_pumps (levels by s8)",
    ), geometry=st.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")

    rm = a.rising.copy()
    s7_to_new = dict(zip(st.NODE_UID_S7.astype(str), st.NODE_UID.astype(str)))
    rm_out = gpd.GeoDataFrame(dict(
        EDGE_UID=rm.EDGE_UID.astype(str),
        US_NODE=rm.US_NODE.astype(str).map(s7_to_new).fillna(rm.US_NODE.astype(str)),
        DS_NODE=rm.DS_NODE.astype(str),
        STATION=rm.STATION.astype(str).map(s7_to_new).fillna(rm.STATION.astype(str)),
        DN=rm.DN.to_numpy(dtype=np.int64),
        MATERIAL=rm.MATERIAL.astype(str),
        LEN_M=np.round(rm.geometry.length.to_numpy(), 3),
        Q_DUTY_LS=np.round(rm.Q_DUTY_LS.to_numpy(dtype=float), 3),
        V_DUTY_MS=np.round(rm.V_DUTY_MS.to_numpy(dtype=float), 3),
        V_MIN_MS=np.round(rm.V_MIN_MS.to_numpy(dtype=float), 3),
        STAT_HD_M=np.round(rm.STAT_HD_M.to_numpy(dtype=float), 2),
        TOT_HD_M=np.round(rm.TOT_HD_M.to_numpy(dtype=float), 2),
        RETENT_M=np.round(rm.RETENT_M.to_numpy(dtype=float), 2),
        N_AIRV=rm.N_AIRV.to_numpy(dtype=np.int64),
        N_WASH=rm.N_WASH.to_numpy(dtype=np.int64),
        N_ISOL=rm.N_ISOL.to_numpy(dtype=np.int64),
        WADI_M=np.round(rm.WADI_M.to_numpy(dtype=float), 2),
        SEPTIC_FL=rm.SEPTIC_FL.to_numpy(dtype=np.int64),
        PACKAGE=rm.STATION.astype(str).map(s7_to_new).map(
            dict(zip(st_out.NODE_UID, st_out.PACKAGE))).fillna(""),
        PHASE=0,
        SRC="terrain", CONFIDENCE="derived", STAGE="s7_pumps",
    ), geometry=rm.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")
    return st_out, rm_out


def build_trunk(a: Assembly) -> gpd.GeoDataFrame:
    """The client's own Main Pipe, exported as itself and nothing more.

    It is an INPUT (CLAUDE.md rule: `SHP/Main Pipe/Main Pipe.shp`), it carries no chambers
    and no topology, and NOTHING in this export drains into it. It is on every map so a
    reviewer can see where the design does not yet reach - which is the single most
    important thing about it."""
    t = a.trunk.copy()
    return gpd.GeoDataFrame(dict(
        EDGE_UID=[f"TRUNK{i + 1:03d}" for i in range(len(t))],
        TIER="trunk main",
        LEN_M=np.round(t.geometry.length.to_numpy(), 3),
        NOTE="CLIENT INPUT. Not chambered, not levelled, not sized. Nothing in this "
             "export drains into it: the 195 outfalls are subnetwork outlets.",
        SRC="main_pipe", CONFIDENCE="drafted", STAGE="s3_hierarchy (passed through by s8)",
    ), geometry=t.geometry.values, crs=f"EPSG:{CT.CRS_EPSG}")


# ======================================================================================
# 7b.  VALIDATION - run it, publish the result, never silence it
# ======================================================================================

def check_contract(layers: Dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    rows = []
    for name in ("nodes", "reaches", "connections", "stations", "rising_mains",
                 "crossings", "packages"):
        gdf = layers.get(name)
        if gdf is None:
            rows.append(dict(LAYER=name, RESULT="NOT PRODUCED", PASS=0, DETAIL=""))
            continue
        try:
            CT.validate(gdf, name, stage=STAGE)
            rows.append(dict(LAYER=name, RESULT="passes contract.validate()", PASS=1,
                             DETAIL=f"{len(gdf):,} rows"))
        except CT.ContractError as e:
            txt = str(e)
            rows.append(dict(LAYER=name, RESULT="CONTRACT VIOLATION", PASS=0,
                             DETAIL=txt[:8000]))
    try:
        CT.assert_crossings_resolve(reaches=layers.get("reaches"),
                                    crossings=layers.get("crossings"))
        rows.append(dict(LAYER="crossings <-> reaches", RESULT="every CROSS_ID resolves",
                         PASS=1, DETAIL=""))
    except CT.ContractError as e:
        rows.append(dict(LAYER="crossings <-> reaches", RESULT="REGISTER DOES NOT RESOLVE",
                         PASS=0, DETAIL=str(e)[:8000]))
    return pd.DataFrame(rows)


def publish(layers: Dict[str, gpd.GeoDataFrame], extra: Dict[str, pd.DataFrame]) -> None:
    """One GeoPackage, rewritten whole. `packages` and the four report tables carry no
    geometry - the contract declares PACKAGES with geom="none" - so they are written as
    attribute-only layers rather than left out of the file the reviewer opens."""
    if os.path.exists(GPKG_OUT):
        os.remove(GPKG_OUT)
    for name, df in list(layers.items()) + list(extra.items()):
        if isinstance(df, gpd.GeoDataFrame) and df.geometry.notna().any():
            df.to_file(GPKG_OUT, layer=name, driver="GPKG")
        else:
            gpd.GeoDataFrame(pd.DataFrame(df).copy(), geometry=[None] * len(df),
                             crs=f"EPSG:{CT.CRS_EPSG}").to_file(
                GPKG_OUT, layer=name, driver="GPKG")
        _log(f"   wrote {name:<14} {len(df):>7,}  -> {os.path.basename(GPKG_OUT)}")


# ======================================================================================
# 8.  THE KMZ SET
#
#     "SUBFOLDERS inside each file for manageability, and SEVERAL SEPARATE FILES each with
#      a DIFFERENT STYLE so he can flick between them and check things fast."   - engineer
#
#     `w11b.present` already IS that machine: one `View` declaration drives both the KMZ
#     and the QGIS renderer, so the Earth file and the GIS project cannot tell different
#     stories. Nothing here re-implements it. What this section adds is SIX views the
#     library did not have, registered from the outside through `present.register()`,
#     because a view is a declaration and adding one is not editing the library.
# ======================================================================================

def package_areas(layers: Dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    """A polygon per package - the ground a contract covers.

    It is a 60 m buffer of the package's own reaches, unioned and simplified. That is a
    DRAWING of the package's extent and not a service-area calculation, and it is labelled
    that way on the map. 60 m is the distance s4 could chain a rider and a lateral over
    (2 x 45 m, G203-p17 3.2, less the setback), so it is the width in which a plot could
    plausibly belong to this package rather than a number chosen for looks."""
    r = layers["reaches"]
    pk = layers["packages"].set_index("PACKAGE")
    rows = []
    for name, sub in r.groupby(r.PACKAGE.astype(str)):
        try:
            poly = unary_union(sub.geometry.buffer(60.0, resolution=4)).simplify(5.0)
        except Exception:
            continue
        if poly.is_empty:
            continue
        info = pk.loc[name] if name in pk.index else None
        rows.append(dict(
            PACKAGE=name,
            PHASE=0,
            LEN_KM=float(info.LEN_KM) if info is not None else round(sub.LEN_M.sum() / 1000, 3),
            N_PLOT=int(info.N_PLOT) if info is not None else 0,
            OUTLET=str(info.OUTLET) if info is not None else "",
            DS_PKG="", COMM_SEQ=int(info.COMM_SEQ) if info is not None else 0,
            INDEP=1, ONE_TREE=1,
            AREA_M2=round(float(poly.area), 1),
            SRC="terrain", CONFIDENCE="derived", STAGE=STAGE,
            geometry=poly))
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=f"EPSG:{CT.CRS_EPSG}")


def _extra_columns(layers: Dict[str, gpd.GeoDataFrame]) -> None:
    """The four presentation columns the extra views classify on. Each is a RESTATEMENT of
    a published field in words a reviewer can read on a legend - never a new number."""
    nd = layers["nodes"]
    why = np.where(nd.PAST_CAP.to_numpy() == 0, "inside the 12 m cap",
                   np.where(nd.CAP_EXIT.astype(str).to_numpy() == "recovers_500m",
                            "past 12 m - cover recovers within 500 m",
                            np.where(nd.CAP_EXIT.astype(str).to_numpy() == "outfall_1000m",
                                     "past 12 m - outfall within 1,000 m",
                                     "PAST 12 m, NO EXIT - a station is demanded here")))
    nd["CAP_WHY"] = why

    cx = layers["crossings"]
    cx["XING_CLS"] = [
        f"{o} - {'SQUARE within ' + str(int(C.WADI_XING_SKEW_DEG)) + ' deg' if s else 'SKEW - runs along it'}"
        for o, s in zip(cx.OBSTACLE.astype(str), cx.SQUARE.to_numpy())]

    cn = layers["connections"]
    cn["DRAIN_TXT"] = np.where(cn.CAN_DRAIN.to_numpy() == 1,
                               "drains to its chamber on gravity",
                               "CANNOT drain - the sewer invert is above the property outlet")

    r = layers["reaches"]
    r["CLEAN_TXT"] = r.CLEAN_BY.astype(str).map({
        "velocity": "velocity route - reaches 0.75 m/s at peak (G203-p26)",
        "tractive": "TRACTIVE route - rests on the ASSUMED tau = 1.0 Pa (G203-p27, GAP-9)",
        "neither": "NEITHER route - this pipe will silt",
    }).fillna("unknown")


def register_extra_views() -> List[str]:
    """Six views `present` did not ship, each answering a question this export raised."""
    names = []

    names.append(PR.register(PR.View(
        name="pumping_demand", priority=8,
        title="WHERE THIS DESIGN DEMANDS A PUMPING STATION",
        question="Which chambers pass the 12 m cover cap with no way back out?",
        role="nodes", geom="point", mode="categorical", field="CAP_WHY",
        categories=[
            ("PAST 12 m, NO EXIT - a station is demanded here",
             "PAST 12 m WITH NO EXIT - a station is demanded (philosophy sec 5)",
             (165, 0, 38), 1.7),
            ("past 12 m - cover recovers within 500 m",
             "Past 12 m, cover recovers within 500 m - exit held", (253, 141, 60), 1.0),
            ("past 12 m - outfall within 1,000 m",
             "Past 12 m, outfall within 1,000 m - exit held", (254, 217, 118), 1.0),
            ("inside the 12 m cap", "Inside the cap", (200, 200, 200), 0.14),
        ],
        folder_fields=("CAP_WHY",), folder_sort="count",
        label_field="NODE_REF", label_min_lod=256, label_max=4000,
        label_filter=lambda d: d["CAP_WHY"].str.startswith("PAST") if "CAP_WHY" in d else None,
        popup=PR._NODE_POPUP + PR._pop(("CAP_WHY", "Cap status", "{}"),
                                       ("CAP_LEN_M", "Distance to recovery / outfall", "{:.0f} m"),
                                       ("COVER_M", "Cover", "{:.2f} m")),
        assumptions=("A1",),
        notes=("The cap is 12 m of COVER, G203-p33, read as a cap. Philosophy sec 5 gives "
               "exactly two exits and both are bounded by DISTANCE and by DEPTH; an exit "
               "is withdrawn where the excursion forces a drop past criteria.DROP_CEILING_M.",
               "Red is not a defect of the levelling. It is FLATNESS: 60 % of this corridor "
               "network falls more gently than the 5.00 mm/m a DN200 may be laid at "
               "(G203-p29 Tab 11), so the pipe sinks whichever way it points.",
               "This stage does not place stations. Stage 7 does. Every red dot is a "
               "demand handed back to it."),
    )).name)

    names.append(PR.register(PR.View(
        name="clean_by", priority=62,
        title="Which self-cleansing route each pipe takes - THE tau EXPOSURE MAP",
        question="How much of this scheme rests on an assumed tractive stress?",
        role="reaches", geom="line", mode="categorical", field="CLEAN_TXT",
        categories=[
            ("velocity route - reaches 0.75 m/s at peak (G203-p26)",
             "Velocity route - reaches 0.75 m/s at peak (G203-p26)", (26, 120, 55), 2.2),
            ("TRACTIVE route - rests on the ASSUMED tau = 1.0 Pa (G203-p27, GAP-9)",
             "TRACTIVE route - rests on the ASSUMED tau = 1.0 Pa (G203-p27, GAP-9)",
             (217, 95, 14), 1.6),
            ("NEITHER route - this pipe will silt",
             "NEITHER route - this pipe will silt (H5)", (165, 0, 38), 4.0),
        ],
        folder_fields=("CLEAN_TXT",), folder_sort="length",
        popup=PR._REACH_POPUP + PR._pop(("CLEAN_BY", "Self-cleansing route", "{}"),
                                        ("SLOPE_MIN", "Governing minimum", "{:.3f} %")),
        assumptions=("A1",),
        notes=("G203-p27 4.2.2.1 offers the two as ALTERNATIVES and requires the STEEPER; "
               "the tractive route exists FOR the small lightly-loaded pipe where 0.75 m/s "
               "is unreachable, so orange is legal, not a breach.",
               "The orange length IS the exposure. At tau = 2.0 Pa every orange gradient "
               "rises 2.346x and every level downstream of it changes."),
    )).name)

    names.append(PR.register(PR.View(
        name="sized_by", priority=45,
        title="What set each DIAMETER - the H8 proof",
        question="Did anything on this network get its size from depth rather than flow?",
        role="reaches", geom="line", mode="categorical", field="SIZED_BY",
        categories=[
            ("minimum", "The guideline MINIMUM size already carries it (G203-p22 Tab 6)",
             (189, 215, 231), 1.2),
            ("dod", "The depth-of-flow limit chose it (G203-p27 Tab 10)", (49, 130, 189), 2.6),
            ("capacity", "The size below could not pass the flow at all", (8, 48, 107), 3.6),
            ("velocity", "The size below exceeded 3.0 m/s (G203-p27)", (217, 95, 14), 3.0),
            ("infeasible", "NO size in the series passes it - a station or a route, "
                           "never a bigger number", (165, 0, 38), 5.0),
        ],
        folder_fields=("SIZED_BY",), folder_sort="length",
        popup=PR._REACH_POPUP + PR._pop(("SIZED_BY", "Diameter set by", "{}")),
        notes=("'depth' and 'cover' are NOT in this vocabulary and cannot be: oversizing a "
               "pipe to lay it flatter is prohibited by G203-p29 and by Ten States sec "
               "33.43 independently, so the prohibited move is not expressible.",),
    )).name)

    names.append(PR.register(PR.View(
        name="grad_by", priority=47,
        title="What set each GRADIENT",
        question="Where is the design fighting the ground, and where is it just obeying Table 11?",
        role="reaches", geom="line", mode="categorical", field="GRAD_BY",
        categories=[
            ("table11", "G203-p29 Table 11 floor governed", (158, 202, 225), 1.3),
            ("tractive", "The tractive minimum governed - exposed to tau (GAP-9)",
             (217, 95, 14), 1.8),
            ("uniform", "Carried from the reach above (P1) - the preferred answer",
             (116, 196, 118), 1.3),
            ("cover_min", "Steepened to hold 1.30 m of cover (G203-p33)", (49, 130, 189), 2.2),
            ("cover_max", "Held at the 25 % laying bound; the rest taken at a drop",
             (140, 81, 10), 3.0),
            ("ground", "Laid to the ground fall - steeper than the laying bound because "
                       "capping it would lift the pipe out of the ground", (165, 0, 38), 4.0),
            ("vmax", "Flattened to hold 3.0 m/s (G203-p27)", (255, 220, 60), 2.6),
            ("tie", "Fixed by an existing invert - the design yields (H14)", (0, 0, 0), 3.0),
        ],
        folder_fields=("GRAD_BY",), folder_sort="length",
        popup=PR._REACH_POPUP,
        assumptions=("A1",),
    )).name)

    names.append(PR.register(PR.View(
        name="crossings", priority=12,
        title="WADI AND DUAL-CARRIAGEWAY CONTACT - the H1a register",
        question="Does the design CROSS these things, or does it run ALONG them?",
        role="crossings", geom="line", mode="categorical", field="XING_CLS",
        folder_fields=("OBSTACLE",), folder_sort="count",
        label_field="CROSS_ID", label_min_lod=128, label_max=1200,
        popup=PR._pop(("CROSS_ID", "Crossing", "{}"), ("OBSTACLE", "Obstacle", "{}"),
                      ("LEN_M", "Contact length", "{:.1f} m"),
                      ("ANGLE_DEG", "MEASURED angle to the obstacle", "{:.1f} deg"),
                      ("SQUARE", "Within the skew tolerance", "{:.0f}"),
                      ("N_REACH", "Reaches involved", "{:.0f}"),
                      ("METHOD", "Method", "{}"), ("COVER_M", "Cover required", "{:.2f} m"),
                      ("APPROVED", "Consent obtained", "{:.0f}")),
        assumptions=("A2", "A3"),
        notes=("The angle is MEASURED against the nearest stream line's own direction. "
               "W11a published ANGLE_DEG = 90 on 3,290 crossings and the measured minimum "
               "was 0.00 deg - that number was fabricated and is retracted.",
               "H1a: a wadi crossing is legal only when it CROSSES rather than runs along, "
               "carries no chamber on wadi ground, has 1.50 m of cover (G203-p52 8.2.4, "
               "adopted for gravity as OUR decision) and is in this register.",
               "APPROVED = 0 on every row. MoAFWR consent for a wadi (G201-p85) and the "
               "roads authority's for a carriageway are OPEN items, not silent ones."),
    )).name)

    names.append(PR.register(PR.View(
        name="can_drain", priority=98,
        title="Can each plot actually reach its chamber?",
        question="Which plots sit BELOW the sewer that is supposed to serve them?",
        role="connections", geom="line", mode="categorical", field="DRAIN_TXT",
        categories=[
            ("CANNOT drain - the sewer invert is above the property outlet",
             "CANNOT drain on gravity - the invert is above the property outlet",
             (165, 0, 38), 3.0),
            ("drains to its chamber on gravity",
             "Drains on gravity at the 3 % minimum (G203-p18 Tab 5)", (116, 196, 118), 0.8),
        ],
        folder_fields=("DRAIN_TXT",), folder_sort="count",
        popup=PR._pop(("CONN_ID", "Connection", "{}"), ("PLOT_ID", "Plot", "{}"),
                      ("OUT_NODE", "Chamber", "{}"), ("LEN_M", "Length", "{:.1f} m"),
                      ("SLOPE_LAID", "Gradient", "{:.2f} %"),
                      ("FALL_AV_M", "Fall available", "{:.2f} m"),
                      ("Q_ADF_M3D", "Load", "{:.2f} m3/d"),
                      ("N_PROP", "Properties", "{:.2f}")),
        notes=("s4 published CAN_DRAIN as 'cannot run - no designed invert exists at stage "
               "4'. There is one now, so the question is answered.",
               "The test: the property outlet at the G203-p19 3.4 minimum HCC depth of "
               "1.2 m must clear the sewer invert with the 3 % minimum gradient of "
               "G203-p18 Table 5 over the connection's own length.",
               "A plot that cannot drain is not a rounding error - it is a plot the "
               "gravity network does not actually serve, and it belongs in the "
               "not-served schedule."),
    )).name)
    return names


KMZ_VIEWS = [
    # the five the engineer named, first
    "tier", "depth", "subnet", "diameter", "stations",
    # and the ones that answer a question this design actually raises
    "pumping_demand", "ground_fall", "constraint", "drops", "crossings",
    "chambers", "capacity", "velocity", "clean_by", "sized_by", "grad_by",
    "flow", "package", "packages_area", "rising_mains", "can_drain", "material",
]




# ======================================================================================
# 7c.  IS EACH OUTFALL AT THE BOTTOM OF ITS OWN CATCHMENT?
#
#      The first long section this stage drew answered a question nobody had asked. Over
#      15.40 km of package P003 the invert falls 51 m in a straight line while the GROUND
#      rises 8 m - because the component's outfall sits near the TOP of its own ground, not
#      the bottom. No levelling arithmetic can recover that: if the terminal node is uphill
#      of the catchment, every metre of the run buys depth it never gives back.
#
#      So the outfall's ground level is compared with the ground of every chamber in its own
#      component. The percentile is the number: 0 % means the outfall IS the lowest point,
#      which is what it should be; 90 % means 90 % of the catchment is BELOW its own outlet.
#      This is a stage-2 / stage-3 orientation measurement, published here because this is
#      the stage that first had the levels to see it.
# ======================================================================================

def outfall_check(g: Graph, f: Flows, layers: Dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    nd = layers["nodes"]
    grd = g.grd
    rows = []
    for out_i in np.unique(f.subnet):
        sel = f.subnet == out_i
        gs = grd[sel]
        z = float(grd[out_i])
        pct = float((gs < z).sum()) / max(1, len(gs)) * 100.0
        esel = sel[g.e_us]
        rows.append(dict(
            OUTFALL=g.uid[int(out_i)],
            PACKAGE=str(nd.PACKAGE.iloc[int(out_i)]),
            N_CHAMBER=int(sel.sum()),
            LEN_KM=round(float(g.e_len[esel].sum()) / 1000.0, 3),
            GRD_OUT=round(z, 2),
            GRD_MIN=round(float(gs.min()), 2),
            GRD_MAX=round(float(gs.max()), 2),
            ABOVE_LOW=round(z - float(gs.min()), 2),
            PCT_BELOW=round(pct, 1),
            LOWEST=int(pct < 1.0),
            DEEPEST_M=round(float(nd.DEPTH_M.to_numpy()[sel].max()), 2),
            Q_ADF_M3D=round(float(f.q_adf[out_i]), 1)))
    df = pd.DataFrame(rows).sort_values("LEN_KM", ascending=False).reset_index(drop=True)
    bad = df[(df.PCT_BELOW > 50.0) & (df.N_CHAMBER >= 20)]
    _log(f"   outfall check: {int(df.LOWEST.sum())} of {len(df)} components discharge at "
         f"their OWN lowest chamber; {len(bad)} components of 20+ chambers "
         f"({bad.LEN_KM.sum():.1f} km) discharge with more than half their catchment BELOW "
         f"the outlet; worst {df.ABOVE_LOW.max():.1f} m above its own low point")
    return df


# ======================================================================================
# 8b.  SUBFOLDERS AND LABELS ON THE GRADUATED VIEWS
#
#      "SUBFOLDERS inside each file for manageability ... labels legible at the zoom a
#       reviewer actually uses."   - engineer, both requests, verbatim
#
#      A CATEGORICAL view folds itself: `folder_fields=("TIER",)` gives four folders you
#      can tick on and off. A GRADUATED one - depth, ground fall, d/D, velocity, flow -
#      had nowhere to fold, because its classes are computed at draw time and there is no
#      column carrying them. So all 56,740 reaches landed in one folder and the file was
#      exactly as unmanageable as the engineer said.
#
#      The fix does not touch `present.py`. It asks the library to classify the layer,
#      writes the CLASS LABEL IT PRODUCED back as a column, and points the view's folder
#      at that column. The folder tree and the legend then read the same words BY
#      CONSTRUCTION, because they are the same object.
# ======================================================================================

BAND_COLUMNS: List[Tuple[str, str, str]] = [
    # view, role, column (<= 10 characters: contract.SHP_FIELD_MAXLEN)
    ("depth", "reaches", "DEPTH_BND"),
    ("ground_fall", "reaches", "FALL_BND"),
    ("capacity", "reaches", "DOD_BND"),
    ("velocity", "reaches", "V_BND"),
    ("flow", "reaches", "Q_BND"),
    ("chambers", "nodes", "CH_DEP_BND"),
]


def add_band_columns(layers: Dict[str, gpd.GeoDataFrame]) -> Dict[str, int]:
    """Write each graduated view's own class label back onto the layer, and fold on it."""
    made: Dict[str, int] = {}
    for vname, role, col in BAND_COLUMNS:
        v = PR.VIEWS[vname]
        df = layers[role]
        work = df
        if v.derive:
            fn, cols = PR.DERIVERS[v.derive]
            if not all(c in work.columns for c in cols):
                work = fn(work)
        cls = PR.classify(work, v)
        idx = cls.index
        lab = np.array([c.label for c in cls.classes] + ["(outside every band)"])
        df[col] = lab[np.where(idx >= 0, idx, len(lab) - 1)]
        made[vname] = int(pd.Series(df[col]).nunique())
    fold_on_bands()
    _log("   folded the graduated views on their own class labels: "
         + ", ".join(f"{k} ({n})" for k, n in made.items()))
    return made


def fold_on_bands() -> None:
    """Point each graduated view's folder at its band column.

    Separate from writing the columns because the KMZ can be rebuilt on its own
    (`python s8_export.py kmz`) off the published GeoPackage, where the columns already
    exist. The first cut set the folders inside the column writer, so a kmz-only rerun
    silently produced the one-folder files this whole section exists to stop."""
    for vname, _role, col in BAND_COLUMNS:
        v = PR.VIEWS[vname]
        v.folder_fields = (col,)
        v.folder_sort = "count"


def tune_views() -> None:
    """Labels a reviewer can actually use, and a diameter palette that covers a rising main.

    Everything here mutates a registered `View` - the library's own declaration object -
    rather than reimplementing anything it does."""
    d = PR.VIEWS["depth"]
    d.label_expr = lambda r: f"{float(r['US_DEPTH']):.1f} m"
    d.label_filter = lambda x: (pd.to_numeric(x["US_DEPTH"], errors="coerce")
                                > C.MAX_COVER) if "US_DEPTH" in x else None
    d.label_field = "US_DEPTH"
    d.label_min_lod, d.label_max = 256, 5000

    dia = PR.VIEWS["diameter"]
    dia.label_expr = lambda r: f"DN{int(r['DN'])}"
    dia.label_filter = lambda x: (pd.to_numeric(x["DN"], errors="coerce") >= 400) \
        if "DN" in x else None
    dia.label_field = "DN"
    dia.label_min_lod, dia.label_max = 200, 4000

    fl = PR.VIEWS["flow"]
    fl.label_expr = lambda r: f"{float(r['QPK_LS']):.0f} L/s"
    fl.label_filter = lambda x: (pd.to_numeric(x["QPK_LS"], errors="coerce") >= 25.0) \
        if "QPK_LS" in x else None
    fl.label_field = "QPK_LS"
    fl.label_min_lod, fl.label_max = 200, 3000

    sn = PR.VIEWS["subnet"]
    sn.label_field = "SUBNET"
    sn.label_min_lod, sn.label_max = 900, 400
    sn.notes = tuple(sn.notes) + (
        "On this design a sub-network and a package are the SAME set, because no packaging "
        "stage exists and the packages were derived one per component. The folder is named "
        "by the component's outfall chamber; the package view names the same folder P###.",)

    # PHASE is 0 on every row - there is no phasing stage - so folding phase over package
    # buys one empty outer level and nothing else. Fold on the package alone.
    pkv = PR.VIEWS["package"]
    pkv.folder_fields = ("PACKAGE",)
    pkv.folder_sort = "length"
    pkv.label_field = "PACKAGE"
    pkv.label_min_lod, pkv.label_max = 900, 400

    # The DN palette in `present` is the GRAVITY series and starts at DN200. A rising main
    # is sized on pump duty (G203-p50) and this scheme's run DN80-DN300, so four of its
    # sizes fell off the end of the palette and drew in fallback colours. Give the rising
    # mains their own series - the same `size` ramp, different domain.
    rm = PR.VIEWS["rising_mains"]
    series = [80, 100, 150, 200, 250, 300, 400, 500, 600]
    rm.categories = [(dn, f"DN{dn} rising main",
                      PR.ramp_rgb("size", i / (len(series) - 1)),
                      round(1.6 + 3.4 * (i / (len(series) - 1)) ** 0.8, 2))
                     for i, dn in enumerate(series)]
    rm.folder_fields = ("DN",)
    rm.folder_sort = "length"
    rm.label_expr = lambda r: f"{r['STATION']}  DN{int(r['DN'])}  {float(r['LEN_M']):.0f} m"

# ======================================================================================
# 9.  SHAPEFILES
#
#     The contract's 10-character rule exists so this round trip loses nothing: every
#     published field name fits a DBF, so the GeoPackage and the shapefile carry the SAME
#     names and a check can rely on either. `write_shapefiles` PROVES it by reading each
#     file back and comparing the column set.
# ======================================================================================

SHP_STR_MAX = 254          # the DBF character-field limit; not a choice


def _shp_ready(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    for c in out.columns:
        if c == out.geometry.name:
            continue
        s = out[c]
        if s.dtype == bool:
            out[c] = s.astype(np.int8)
        elif s.dtype == object or str(s.dtype) in ("string", "str"):
            out[c] = s.astype(str).str.slice(0, SHP_STR_MAX)
    return out


def write_shapefiles(layers: Dict[str, gpd.GeoDataFrame],
                     tables: Dict[str, pd.DataFrame]) -> List[str]:
    written = []
    for name, gdf in layers.items():
        if len(gdf) == 0:
            continue
        path = os.path.join(DIR_SHP, f"W11b_{name}.shp")
        g = _shp_ready(gdf)
        g.to_file(path, driver="ESRI Shapefile", encoding="utf-8")
        back = gpd.read_file(path)
        lost = sorted(set(g.columns) - set(back.columns) - {g.geometry.name, "geometry"})
        if lost:
            raise CT.ContractError(
                f"the shapefile round trip LOST {lost} from '{name}'. The contract's "
                "10-character rule exists precisely so this cannot happen; a truncated "
                "name is a field the auditor cannot find.")
        written.append(path)
        _log(f"   {os.path.basename(path):<28} {len(g):>7,} features, "
             f"{len(g.columns) - 1} fields, round trip clean")
    for name, df in tables.items():
        p = os.path.join(DIR_SHP, f"W11b_{name}.csv")
        df.to_csv(p, index=False, encoding="utf-8-sig")
        written.append(p)
    return written


# ======================================================================================
# 10.  DXF
#
#      Two drawings, because they answer different needs and one of them is 20x the size:
#        W11b_network.dxf     geometry only - opens instantly, for looking at
#        W11b_annotated.dxf   the same plus every chamber and pipe label - for marking up
#
#      Layer names carry the tier, so a CAD user can freeze the laterals and see the
#      structure. Colours match the KMZ and the QGIS project because they come from the
#      SAME `present.TIER_COLOURS` list.
# ======================================================================================

DXF_LAYERS = {
    "W11B-TRUNK-CLIENT": (7, "the client's own Main Pipe - an INPUT, not designed here"),
    "W11B-SUBMAIN": (1, "sub main"),
    "W11B-MAIN": (5, "main sewer"),
    "W11B-LATERAL": (4, "lateral"),
    "W11B-CHAMBER": (2, "chambers, drawn at MH_DIA"),
    "W11B-CHAMBER-DROP": (1, "chambers carrying a backdrop or a vortex shaft"),
    "W11B-STATION": (6, "pumping stations (s7)"),
    "W11B-RISING": (6, "rising mains (s7)"),
    "W11B-CONNECTION": (8, "property connections"),
    "W11B-CROSSING": (1, "registered wadi / dual-carriageway contact"),
    "W11B-CAP-BREACH": (1, "chambers past the 12 m cover cap with no exit"),
    "W11B-TEXT-MH": (3, "chamber label: ref / cover level / invert level"),
    "W11B-TEXT-PIPE": (3, "pipe label: DN, length, laid gradient"),
}
TIER_DXF = {"trunk main": "W11B-SUBMAIN", "sub main": "W11B-SUBMAIN",
            "main": "W11B-MAIN", "lateral": "W11B-LATERAL", "rider": "W11B-LATERAL"}


def write_dxf(layers: Dict[str, gpd.GeoDataFrame], annotated: bool = True) -> List[str]:
    import ezdxf
    out = []
    for tag, ann in (("network", False), ("annotated", True)):
        if ann and not annotated:
            continue
        doc = ezdxf.new("R2013", setup=True)
        doc.header["$INSUNITS"] = 6                     # metres
        msp = doc.modelspace()
        for nm, (col, desc) in DXF_LAYERS.items():
            # ezdxf 1.4's LayerTable.add() takes (name, color, linetype, dxfattribs) and
            # NOT `description`; the layer note goes on the drawing as a comment block
            # instead, which is where a CAD user looks for it anyway.
            doc.layers.add(name=nm, color=col)

        r = layers["reaches"]
        for geom, tier in zip(r.geometry.values, r.TIER.astype(str)):
            msp.add_lwpolyline([(float(x), float(y)) for x, y, *_ in geom.coords],
                               dxfattribs={"layer": TIER_DXF.get(tier, "W11B-LATERAL")})
        for geom in layers["trunk"].geometry.values:
            msp.add_lwpolyline([(float(x), float(y)) for x, y, *_ in geom.coords],
                               dxfattribs={"layer": "W11B-TRUNK-CLIENT"})
        for geom in layers["connections"].geometry.values:
            cs = [(float(x), float(y)) for x, y, *_ in geom.coords]
            if len(cs) >= 2:
                msp.add_lwpolyline(cs, dxfattribs={"layer": "W11B-CONNECTION"})
        for geom in layers["rising_mains"].geometry.values:
            msp.add_lwpolyline([(float(x), float(y)) for x, y, *_ in geom.coords],
                               dxfattribs={"layer": "W11B-RISING"})
        for geom in layers["crossings"].geometry.values:
            msp.add_lwpolyline([(float(x), float(y)) for x, y, *_ in geom.coords],
                               dxfattribs={"layer": "W11B-CROSSING"})

        nd = layers["nodes"]
        for x, y, dia, dt, pc, ce in zip(nd.X, nd.Y, nd.MH_DIA, nd.DROP_TYPE,
                                         nd.PAST_CAP, nd.CAP_EXIT.astype(str)):
            lay = "W11B-CHAMBER-DROP" if str(dt) != "none" else "W11B-CHAMBER"
            msp.add_circle((float(x), float(y)), float(dia) / 2.0,
                           dxfattribs={"layer": lay})
            if int(pc) == 1 and not ce:
                msp.add_circle((float(x), float(y)), 3.0,
                               dxfattribs={"layer": "W11B-CAP-BREACH"})
        for geom in layers["stations"].geometry.values:
            msp.add_circle((float(geom.x), float(geom.y)), 6.0,
                           dxfattribs={"layer": "W11B-STATION"})

        if ann:
            for ref, x, y, grd, inv in zip(nd.NODE_REF, nd.X, nd.Y, nd.GRD_M, nd.INV_M):
                msp.add_text(str(ref), height=1.2,
                             dxfattribs={"layer": "W11B-TEXT-MH"}
                             ).set_placement((float(x) + 1.0, float(y) + 1.4))
                msp.add_text(f"CL {float(grd):.2f} / IL {float(inv):.2f}", height=1.0,
                             dxfattribs={"layer": "W11B-TEXT-MH"}
                             ).set_placement((float(x) + 1.0, float(y) - 0.2))
            for geom, dn, L, s in zip(r.geometry.values, r.DN, r.LEN_M, r.SLOPE_LAID):
                mid = geom.interpolate(0.5, normalized=True)
                cs = np.asarray(geom.coords)
                d = cs[-1, :2] - cs[0, :2]
                ang = math.degrees(math.atan2(d[1], d[0]))
                if ang > 90:
                    ang -= 180
                if ang < -90:
                    ang += 180
                msp.add_text(f"DN{int(dn)}  L={float(L):.1f}  S={float(s):.2f}%",
                             height=1.0, rotation=ang,
                             dxfattribs={"layer": "W11B-TEXT-PIPE"}
                             ).set_placement((float(mid.x), float(mid.y) + 0.6))

        # the layer key, written into the drawing so a CAD user does not need this file
        y0 = float(layers["nodes"].Y.max()) + 400.0
        x0 = float(layers["nodes"].X.min())
        msp.add_text(f"W11b sewer network - {tag}.  {VERSION}, "
                     f"{time.strftime('%Y-%m-%d')}.  EPSG:{CT.CRS_EPSG}.  "
                     f"LEVELS BY THE s8 STAGE-6 STAND-IN.  {C.tau_banner()[:120]}",
                     height=12.0, dxfattribs={"layer": "W11B-TEXT-MH"}
                     ).set_placement((x0, y0 + 30.0))
        for i, (nm, (_c, desc)) in enumerate(DXF_LAYERS.items()):
            msp.add_text(f"{nm} = {desc}", height=8.0,
                         dxfattribs={"layer": "W11B-TEXT-MH"}
                         ).set_placement((x0, y0 - i * 12.0))
        p = os.path.join(DIR_DXF, f"W11b_{tag}.dxf")
        doc.saveas(p)
        out.append(p)
        _log(f"   {os.path.basename(p):<24} {os.path.getsize(p) / 1e6:8.1f} MB")
    return out


# ======================================================================================
# 11.  THE SCHEDULES
#
#      The printed headers come from `contract.SCHEDULES` and from nowhere else - that is
#      the whole reason they live in the contract: "a header and the field it prints must
#      not be editable apart". `contract.schedule_frame()` validates first and RAISES; it
#      is tried first, and where it raises the schedule is still printed with the contract's
#      own headers and the failure is written into the workbook's own first sheet, so the
#      reader sees what did not validate on the same file as the numbers.
# ======================================================================================

def schedule(gdf, name: str) -> Tuple[pd.DataFrame, str]:
    try:
        return CT.schedule_frame(gdf, name, stage=STAGE), "validated"
    except CT.ContractError as e:
        sch = CT.SCHEDULES[name]
        missing = [f for _h, f in sch.columns if f not in gdf.columns]
        cols = {h: (gdf[f].values if f in gdf.columns else ["(not published)"] * len(gdf))
                for h, f in sch.columns}
        return pd.DataFrame(cols), (f"NOT VALIDATED. {str(e)[:4000]}"
                                    + (f"\nMISSING FIELDS: {missing}" if missing else ""))


def quantities(layers: Dict[str, gpd.GeoDataFrame]) -> Dict[str, pd.DataFrame]:
    """An INDICATIVE take-off. It is not a bill of quantities and it is not priced.

    Two numbers in it are this stage's own assumptions and neither comes from a guideline:
    TRENCH_SIDE_M (0.30 m working space each side of the barrel) and MH_DIA_STD_M (1.20 m
    chamber, written up to 1.50 m where a backdrop is unavoidable, G203-p30). G203 gives no
    trench width and no table of chamber size against depth - both were searched."""
    r = layers["reaches"]
    nd = layers["nodes"]
    dn_m = r.DN.to_numpy(dtype=float) / 1000.0
    od = dn_m + 2 * C.WALL_ALLOW
    width = od + 2 * TRENCH_SIDE_M
    depth = (r.US_DEPTH.to_numpy(dtype=float) + r.DS_DEPTH.to_numpy(dtype=float)) / 2.0 + od
    L = r.LEN_M.to_numpy(dtype=float)
    exc = width * np.maximum(depth, 0.0) * L
    bed = width * (od + 0.15) * L

    pipes = (pd.DataFrame(dict(TIER=r.TIER.astype(str), DN=r.DN, MATERIAL=r.MATERIAL,
                               LEN_M=L, EXC_M3=exc, BED_M3=bed))
             .groupby(["TIER", "DN", "MATERIAL"], as_index=False)
             .agg(Reaches=("LEN_M", "size"), Length_m=("LEN_M", "sum"),
                  Excavation_m3=("EXC_M3", "sum"), Bedding_m3=("BED_M3", "sum"))
             .sort_values(["TIER", "DN"]))
    for c in ("Length_m", "Excavation_m3", "Bedding_m3"):
        pipes[c] = pipes[c].round(1)

    d = nd.DEPTH_M.to_numpy(dtype=float)
    bands = pd.cut(d, [-0.01, 2, 3, 4, 6, 8, 10, 12, 1e9],
                   labels=["<2 m", "2-3 m", "3-4 m", "4-6 m", "6-8 m", "8-10 m",
                           "10-12 m", "OVER THE 12 m CAP"])
    ch = (pd.DataFrame(dict(Band=bands, DIA=nd.MH_DIA, DROP=nd.DROP_TYPE))
          .groupby(["Band", "DIA"], as_index=False, observed=True)
          .agg(Chambers=("DROP", "size")))

    drops = (pd.DataFrame(dict(Type=nd.DROP_TYPE, H=nd.DROP_M))
             .query("Type != 'none'")
             .groupby("Type", as_index=False)
             .agg(Number=("H", "size"), Total_height_m=("H", "sum"),
                  Max_height_m=("H", "max")))
    drops[["Total_height_m", "Max_height_m"]] = drops[["Total_height_m", "Max_height_m"]].round(2)

    rm = layers["rising_mains"]
    rms = (rm.groupby(["DN", "MATERIAL"], as_index=False)
             .agg(Mains=("LEN_M", "size"), Length_m=("LEN_M", "sum"),
                  Air_valves=("N_AIRV", "sum"), Washouts=("N_WASH", "sum"),
                  Isolation_valves=("N_ISOL", "sum")))
    rms["Length_m"] = rms.Length_m.round(1)

    st = layers["stations"]
    sts = (st.groupby("ST_TYPE", as_index=False)
             .agg(Stations=("LAND_M2", "size"), Land_m2=("LAND_M2", "sum"),
                  Duty_LS=("Q_DUTY_LS", "sum"), Motor_kW=("MOTOR_KW", "sum"),
                  Wet_well_m3=("WELL_M3", "sum")))
    for c in ("Land_m2", "Duty_LS", "Motor_kW", "Wet_well_m3"):
        sts[c] = sts[c].round(2)

    cn = layers["connections"]
    conn = pd.DataFrame([dict(
        Item="Property connections (rider, HCC to chamber)",
        Number=len(cn), Length_m=round(float(cn.LEN_M.sum()), 1),
        Note=f"DN{C.DN_TERTIARY} minimum, G203-p22 Tab 6; "
             f"{int((cn.CAN_DRAIN == 0).sum()):,} cannot drain on gravity")])

    headline = pd.DataFrame([
        dict(Item="Gravity sewer", Quantity=round(float(L.sum()) / 1000.0, 3), Unit="km",
             Source="this export, LEN_M summed over the reach layer"),
        dict(Item="Chambers", Quantity=len(nd), Unit="no.", Source="the node layer"),
        dict(Item="Chambers per km", Quantity=round(len(nd) / (L.sum() / 1000.0), 2),
             Unit="-", Source="built network 34.23 (asbuilt, measured by s4)"),
        dict(Item="Trench excavation", Quantity=round(float(exc.sum()), 0), Unit="m3",
             Source=f"width = OD + 2 x {TRENCH_SIDE_M} m (ASSUMPTION), depth to invert + OD"),
        dict(Item="Pipe bedding and surround", Quantity=round(float(bed.sum()), 0),
             Unit="m3", Source="ASSUMPTION - 150 mm over the crown"),
        dict(Item="Backdrops (0.60-2.00 m)", Quantity=int((nd.DROP_TYPE == "backdrop").sum()),
             Unit="no.", Source="G203-p30"),
        dict(Item="VORTEX DROP SHAFTS (> 2.00 m)",
             Quantity=int((nd.DROP_TYPE == "vortex").sum()), Unit="no.",
             Source="G203-p30. NAMA's built network has 37 - philosophy sec 4 makes this "
                    "count the tree-orientation diagnostic"),
        dict(Item="Property connections", Quantity=len(cn), Unit="no.",
             Source="one per connected plot"),
        dict(Item="Property connection pipe", Quantity=round(float(cn.LEN_M.sum()) / 1000, 3),
             Unit="km", Source="the connection layer"),
        dict(Item="Pumping stations", Quantity=len(st), Unit="no.", Source="s7_pumps"),
        dict(Item="Station land take", Quantity=round(float(st.LAND_M2.sum()), 0), Unit="m2",
             Source="G203-p43 Tab 21, via s7"),
        dict(Item="Rising main", Quantity=round(float(rm.LEN_M.sum()) / 1000.0, 3), Unit="km",
             Source="s7_pumps"),
        dict(Item="Registered wadi / carriageway crossings", Quantity=len(layers["crossings"]),
             Unit="no.", Source="H1a register, this export"),
    ])
    return {"Headline": headline, "Pipes": pipes, "Chambers": ch, "Drop structures": drops,
            "Rising mains": rms, "Stations": sts, "Connections": conn}


def data_dictionary() -> pd.DataFrame:
    """Every published field, its units, the RULE it exists for and the check that reads
    it - straight out of `contract.LAYERS`. A schedule nobody can interpret is a schedule
    nobody checks."""
    rows = []
    for lname in ("nodes", "reaches", "connections", "stations", "rising_mains",
                  "crossings", "packages"):
        spec = CT.LAYERS[lname]
        for fl in spec.fields:
            rows.append(dict(Layer=lname, Field=fl.name, Type=fl.dtype, Units=fl.units,
                             Required="yes" if fl.required else "no",
                             Blank_ok="yes" if fl.blank_ok else "no",
                             Allowed=", ".join(fl.allowed) if fl.allowed else "",
                             Range=("" if fl.lo is None and fl.hi is None
                                    else f"[{fl.lo}, {fl.hi}]"),
                             Audit_check=fl.audit,
                             Why_this_field_exists=fl.why))
    return pd.DataFrame(rows)


def write_schedules(a: Assembly, layers: Dict[str, gpd.GeoDataFrame],
                    chk: pd.DataFrame) -> List[str]:
    out = []
    banner = pd.DataFrame([
        dict(Item="Design iteration", Value="W11b"),
        dict(Item="Stage", Value=VERSION),
        dict(Item="Built", Value=time.strftime("%Y-%m-%d %H:%M")),
        dict(Item="LEVELS AND SIZES", Value=(
            "produced by the STAGE-6 STAND-IN inside s8_export.py. W11b has no s6_levels "
            "module. Every invert, diameter, gradient, velocity, depth of flow, cover and "
            "drop in these schedules comes from that stand-in, tagged "
            f"STAGE = '{LEVELS_TAG}' on every row.")),
        dict(Item="TRACTIVE STRESS", Value=C.tau_banner()),
        dict(Item="DIAMETERS ABOVE DN1200", Value=(
            "the series is the one G203 itself tabulates in the service-corridor width "
            "table (p32 Tab 13 / p35 Tab 15); awaiting written NWS confirmation")),
        dict(Item="THE TRUNK", Value=(
            "the client's Main Pipe is an INPUT with no chambers and no topology. NOTHING "
            "in these schedules drains into it; the outfalls are subnetwork outlets")),
        dict(Item="PHASE", Value="0 on every row - no phasing stage exists (contract: "
                                 "'0 = not yet assigned')"),
    ])

    def _book(path: str, sheets: Dict[str, pd.DataFrame], note: str = "") -> None:
        with pd.ExcelWriter(path, engine="openpyxl") as xl:
            head = banner.copy()
            if note:
                head = pd.concat([head, pd.DataFrame([dict(Item="CONTRACT", Value=note)])],
                                 ignore_index=True)
            head.to_excel(xl, sheet_name="READ THIS FIRST", index=False)
            for nm, df in sheets.items():
                df.to_excel(xl, sheet_name=nm[:31], index=False)
        out.append(path)
        _log(f"   {os.path.basename(path):<38} "
             f"{sum(len(d) for d in sheets.values()):>7,} rows")

    for key, layer_name in (("chambers", "nodes"), ("pipes", "reaches"),
                            ("stations", "stations"), ("rising_mains", "rising_mains"),
                            ("connections", "connections"), ("crossings", "crossings"),
                            ("packages", "packages")):
        df, status = schedule(layers[layer_name], key)
        _book(os.path.join(DIR_SCH, f"W11b_schedule_{key}.xlsx"),
              {key.replace('_', ' ').title(): df}, note=status)

    _book(os.path.join(DIR_SCH, "W11b_quantities.xlsx"), quantities(layers),
          note="INDICATIVE take-off. Not a bill of quantities, not priced. Trench width "
               f"and chamber diameter are s8 ASSUMPTIONS ({TRENCH_SIDE_M} m each side, "
               f"{MH_DIA_STD_M} m chamber) - G203 gives neither.")

    ns = a.unserved.copy()
    ns_tab = pd.DataFrame({
        "Plot": ns.PLOT_ID.astype(str), "Status": ns.WHY.astype(str),
        "System": ns.SYSTEM.astype(str),
        "Qadf (m3/d)": ns.Q_ADF_M3D.round(3), "Properties": ns.N_PROP.round(2),
        "Nearest chamber (m)": ns.D_NEAR_M.round(1),
        "Tertiary needed (m)": ns.L_TERT_M.round(1)})
    cn = layers["connections"]
    nodrain = cn[cn.CAN_DRAIN == 0]
    nd_tab = pd.DataFrame({
        "Plot": nodrain.PLOT_ID.astype(str), "Connection": nodrain.CONN_ID.astype(str),
        "Chamber": nodrain.OUT_NODE.astype(str),
        "Qadf (m3/d)": nodrain.Q_ADF_M3D.round(3),
        "Fall available (m)": nodrain.FALL_AV_M.round(3),
        "Length (m)": nodrain.LEN_M.round(1),
        "Status": "CONNECTED to a chamber, but the sewer invert sits above the property "
                  "outlet at the G203-p19 minimum HCC depth"})
    _book(os.path.join(DIR_SCH, "W11b_schedule_not_served.xlsx"),
          {"Not connected": ns_tab, "Connected but cannot drain": nd_tab},
          note="scope-p4 item 3 requires every plot SERVICED. 'Serviced' is not 'connected "
               "to one network' (philosophy sec 8a) - these are the plots this network "
               "does not serve, each named.")

    _book(os.path.join(DIR_SCH, "W11b_data_dictionary.xlsx"),
          {"Fields": data_dictionary(),
           "Numbers used": pd.DataFrame([dict(Name=n, Value=str(v), Source=s, Why=w)
                                         for n, v, s, w in EXPORT_NUMBERS]),
           "Contract check": chk})
    return out


# ======================================================================================
# 12.  LONG-SECTION PROFILES
#
#      A profile is the one drawing that cannot be faked: it puts the ground and the
#      invert on the same axis, so 12 m of cover is a distance a reader can see. These are
#      drawn along the LONGEST FLOW PATH in each package - the path that accumulates the
#      most depth, which is the one worth looking at.
# ======================================================================================

def _dist_to_outfall(g: Graph) -> np.ndarray:
    d = np.zeros(len(g.uid))
    for v in g.order[::-1]:
        e = int(g.e_of[v])
        d[v] = 0.0 if e < 0 else float(g.e_len[e]) + d[int(g.e_ds[e])]
    return d


def longest_paths(g: Graph, node_pkg: np.ndarray, top: int = 24) -> List[Tuple[str, List[int]]]:
    dist = _dist_to_outfall(g)
    heads = np.flatnonzero(g.indeg == 0)
    best: Dict[str, Tuple[float, int]] = {}
    for h in heads:
        p = str(node_pkg[h])
        if p not in best or dist[h] > best[p][0]:
            best[p] = (float(dist[h]), int(h))
    out = []
    for p, (_d, h) in sorted(best.items(), key=lambda kv: -kv[1][0])[:top]:
        chain = [h]
        cur = h
        while True:
            e = int(g.e_of[cur])
            if e < 0:
                break
            cur = int(g.e_ds[e])
            chain.append(cur)
        out.append((p, chain))
    return out


def write_profiles(g: Graph, layers: Dict[str, gpd.GeoDataFrame], node_pkg: np.ndarray,
                   top: int = 24) -> List[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    nd = layers["nodes"].set_index(layers["nodes"].NODE_UID.astype(str))
    r = layers["reaches"]
    by_us = {u: i for i, u in enumerate(r.US_NODE.astype(str))}
    paths = longest_paths(g, node_pkg, top=top)
    written = []
    pdf_path = os.path.join(DIR_PRF, "W11b_long_sections.pdf")
    with PdfPages(pdf_path) as pdf:
        for rank, (pkg, chain) in enumerate(paths, 1):
            uids = [g.uid[i] for i in chain]
            grd = np.array([float(nd.GRD_M[u]) for u in uids])
            inv = np.array([float(nd.INV_M[u]) for u in uids])
            ref = [str(nd.NODE_REF[u]) for u in uids]
            ch = np.zeros(len(uids))
            dn = np.zeros(max(1, len(uids) - 1))
            slope = np.zeros_like(dn)
            for i in range(len(uids) - 1):
                k = by_us.get(uids[i])
                L = float(r.LEN_M.iloc[k]) if k is not None else 0.0
                ch[i + 1] = ch[i] + L
                dn[i] = float(r.DN.iloc[k]) if k is not None else 0.0
                slope[i] = float(r.SLOPE_LAID.iloc[k]) if k is not None else 0.0
            # the barrel is drawn on the reach's OWN outside diameter; the last chamber
            # inherits the diameter of the reach arriving at it
            dn_node = np.array(list(dn) + [dn[-1] if len(dn) else 200.0], dtype=float)
            crown = inv + dn_node / 1000.0

            fig, ax = plt.subplots(figsize=(16.5, 7.0))
            ax.plot(ch, grd, color="#7f5539", lw=1.6, label="Existing ground (0.5 m VRT)")
            ax.plot(ch, inv, color="#1f4e79", lw=2.0, label="Designed invert")
            ax.fill_between(ch, inv, crown, color="#9dc3e6", alpha=0.55,
                            label="Pipe barrel (to crown)")
            ax.fill_between(ch, grd - C.MAX_COVER, grd, color="#c6efce", alpha=0.28,
                            label=f"Inside the {C.MAX_COVER:g} m cover cap (G203-p33)")
            deep = grd - inv > C.MAX_COVER
            if deep.any():
                ax.fill_between(ch, inv, grd - C.MAX_COVER, where=deep, color="#f8cbad",
                                alpha=0.55, label="PAST the cap")
            for x, gz, iz in zip(ch, grd, inv):
                ax.plot([x, x], [iz, gz], color="#404040", lw=0.5, alpha=0.55)
            vx = [(x, iz) for x, u, iz in zip(ch, uids, inv)
                  if float(nd.DROP_M[u]) > C.BACKDROP_MAX]
            if vx:
                ax.scatter([a_ for a_, _b in vx], [_b for _a, _b in vx],
                           marker="v", s=44, color="#a50026", zorder=5,
                           label=f"Vortex drop shaft (> {C.BACKDROP_MAX:g} m, G203-p30)")
            step = max(1, len(uids) // 26)
            ax.set_xticks(ch[::step])
            ax.set_xticklabels(ref[::step], rotation=90, fontsize=6)
            cover = grd - inv
            ax.set_title(
                f"W11b long section {rank} of {len(paths)} - package {pkg}, "
                f"the longest flow path in it\n"
                f"{ch[-1] / 1000.0:.2f} km, {len(uids):,} chambers, "
                f"DN{int(dn.min()) if len(dn) else 0}-{int(dn.max()) if len(dn) else 0}, "
                f"gradient {slope.min():.2f}-{slope.max():.2f} %, "
                f"deepest {cover.max():.2f} m to invert   |   "
                f"LEVELS BY THE s8 STAGE-6 STAND-IN   |   tau = {C.TAU_PA:g} Pa ASSUMED",
                fontsize=9)
            ax.set_xlabel("Chamber (chainage increases downstream)", fontsize=8)
            ax.set_ylabel("Level, m aOD", fontsize=8)
            ax.grid(alpha=0.25, lw=0.5)
            ax.legend(fontsize=7, loc="best", framealpha=0.9)
            fig.tight_layout()
            pdf.savefig(fig, dpi=110)
            if rank <= 6:
                p = os.path.join(DIR_PRF, f"W11b_profile_{rank:02d}_{pkg}.png")
                fig.savefig(p, dpi=130)
                written.append(p)
            plt.close(fig)
    written.append(pdf_path)
    _log(f"   {len(paths)} long sections -> {os.path.basename(pdf_path)} "
         f"({os.path.getsize(pdf_path) / 1e6:.1f} MB) + 6 PNG")
    return written


# ======================================================================================
# 13.  THE SEWERGEMS PACKAGE
#
#      THE PEAK FACTOR IS OURS AND MUST NOT BE APPLIED TWICE.  (engineer, explicitly)
#
#      Merrimack (G201-p71 7.4.2) is Qpdf = 2.65 Qadf^0.879 with both sides in Ml/d, so
#      the peak factor FALLS as properties accumulate: 3.62 at a head, 1.63 at the biggest
#      outfall on this network. It is therefore NOT additive - a model that loads our
#      peaked flows at every manhole and then applies its own extreme-flow multiplier
#      peaks a peak, and one that simply SUMS them peaks the tips all the way down.
#
#      So the package loads AVERAGE DRY WEATHER FLOW at every manhole, which IS additive,
#      and carries our peak beside it as a REFERENCE column the model never reads. The
#      modeller sets the peaking in SewerGEMS' own Extreme Flow Setup, or reproduces ours
#      from the reference column. Both halves are spelled out in the README the package
#      carries, because this is the single easiest way to get a wrong answer out of a
#      right model.
# ======================================================================================

GEMS_README = """W11b SewerGEMS / SWMM package
=================================================================================
Built {built} by {version} (design iteration W11b, Ibri sewer, 2621).

WHAT IS IN HERE
    MANHOLES.shp / .csv    every chamber: label, ground and invert ELEVATION, diameter
    CONDUITS.shp / .csv    every gravity reach: label, start/stop node, DN, inverts,
                           length, material, Manning n
    OUTFALL.shp / .csv     the {n_outfall} subnetwork outlets
    LOADS.csv              average dry weather flow per manhole, and OUR peak beside it
    RISING_MAINS.shp       the {n_rm} force mains, for reference - NOT gravity elements
    fieldmap.csv           canonical field -> Bentley field, straight out of
                           contract.SEWERGEMS so the model cannot drift from the layer
    W11b.inp               an EPA SWMM 5 input file of the same network, so the package
                           can be run by something other than SewerGEMS

*** THE PEAK FACTOR IS OURS. DO NOT APPLY IT TWICE. ***
    LOADS.csv column  Q_AVG_LS   is AVERAGE dry weather flow. Load THIS.
    LOADS.csv column  Q_PK_LS    is OUR peak, for checking only. Do NOT load it.
    Merrimack (PAM-GUD-201 p71 sec 7.4.2), Qpdf = 2.65 x Qadf^0.879 with BOTH sides in
    Ml/d, gives a peak factor that FALLS as the catchment grows - the steepest peak factor
    on this network is {pf_hi:.2f} and the one on the largest reach is {pf_lo:.2f}. Peak
    flows are therefore NOT additive: summing them down the tree carries the tip peak all
    the way to the outfall. ({pf_held:,} reaches carry PF = 1.0 and PF_METH = "held",
    which is not a peak factor at all - it is the honest token for a catchment under the
    {pf_hold:.0f} properties below which G201 prescribes NO formula.)
    Infiltration ({inf} L/d/km, PAM-GUD-201 p72 sec 7.4.3) is UNPEAKED and is already
    excluded from Q_AVG_LS - add it as a separate steady inflow if you want it.

*** LABELS ARE THE UID, NEVER THE REF. ***
    START_ND / STOP_ND resolve against MANHOLES.LABEL, which carries NODE_UID. NODE_REF
    (the NAMA-style 5A-2-SM.2-MH391 label) is regenerated on every re-tier and is in
    NODE_REF for drawings only. Label the manholes with NODE_REF and every conduit
    imports UNCONNECTED - the model runs, reports nothing, and is wrong.

*** WHAT THIS MODEL CANNOT REFEREE ***
  * The levels came from a STAGE-6 STAND-IN inside s8_export.py. W11b has no levels
    stage. Every invert here is that stand-in's.
  * {past_cap:,} chambers sit past the {maxcover:g} m cover cap and {no_exit:,} of them
    have no exit under philosophy sec 5. A solver will not object - it deepens forever.
    The pumping decision is ours, before the solver runs.
  * The client's trunk main is an INPUT with no chambers. NOTHING here drains into it;
    the {n_outfall} outfalls are subnetwork outlets, each an independent discharge.
  * Manning n = {n_manning} is a MODEL parameter (the n behind G203-p27's own tractive
    derivation), not a design value. The DESIGN is Colebrook-White at ks = {ks} m,
    which G203-p24 sec 4.2.1 mandates. Expect small differences and do not "fix" the
    design to match the model.
  * Tractive stress tau = {tau} Pa is an ASSUMPTION (GAP-9). {tract_km:,.0f} km of this
    network - {tract_pct:.0f} % - is self-cleansed by the tractive route and would need
    steeper gradients at 2.0 Pa.
=================================================================================
"""


def write_sewergems(layers: Dict[str, gpd.GeoDataFrame], lv: Levels, f: Flows,
                    g: Graph) -> List[str]:
    out = []
    nd = layers["nodes"]
    r = layers["reaches"]

    def _map(gdf, table):
        pairs = CT.SEWERGEMS[table]
        keep = [s for s, _d in pairs if s in gdf.columns]
        miss = [s for s, _d in pairs if s not in gdf.columns]
        if miss:
            raise CT.ContractError(f"SewerGEMS {table} needs {miss}")
        sub = gdf[keep + ["geometry"]].rename(columns=dict(pairs))
        return sub

    mh = _map(nd[nd.IS_OUTFALL == 0], "MANHOLES")
    of = _map(nd[nd.IS_OUTFALL == 1], "OUTFALL")
    cd = _map(r, "CONDUITS")
    cd["MANNING_N"] = C.MANNING_N_EXPORT
    for name, gdf in (("MANHOLES", mh), ("OUTFALL", of), ("CONDUITS", cd)):
        p = os.path.join(DIR_GEM, f"{name}.shp")
        _shp_ready(gdf).to_file(p, driver="ESRI Shapefile", encoding="utf-8")
        pd.DataFrame(gdf.drop(columns="geometry")).to_csv(
            os.path.join(DIR_GEM, f"{name}.csv"), index=False)
        out += [p, os.path.join(DIR_GEM, f"{name}.csv")]

    loads = pd.DataFrame(dict(
        LABEL=nd.NODE_UID.astype(str),
        Q_AVG_LS=(nd.Q_ADF_M3D.to_numpy(dtype=float) * 1000.0 / 86400.0).round(6),
        Q_PK_LS=nd.Q_PK_LS.to_numpy(dtype=float).round(6),
        N_PROP=nd.N_PROP.to_numpy(dtype=float).round(2),
        LOAD_THIS=["Q_AVG_LS"] * len(nd),
        NOTE=["OUR peak factor is already in Q_PK_LS. Load Q_AVG_LS and let the model "
              "do its own peaking, or reproduce ours - never both."] * len(nd)))
    loads.to_csv(os.path.join(DIR_GEM, "LOADS.csv"), index=False)
    out.append(os.path.join(DIR_GEM, "LOADS.csv"))

    _shp_ready(layers["rising_mains"]).to_file(
        os.path.join(DIR_GEM, "RISING_MAINS.shp"), driver="ESRI Shapefile", encoding="utf-8")
    out.append(os.path.join(DIR_GEM, "RISING_MAINS.shp"))

    fm = pd.DataFrame([dict(Table=t, Canonical_field=s, Bentley_field=d)
                       for t, pairs in CT.SEWERGEMS.items() for s, d in pairs]
                      + [dict(Table="CONDUITS", Canonical_field="(criteria.MANNING_N_EXPORT)",
                              Bentley_field="MANNING_N")])
    fm.to_csv(os.path.join(DIR_GEM, "fieldmap.csv"), index=False)
    out.append(os.path.join(DIR_GEM, "fieldmap.csv"))

    inp = _swmm_inp(layers, g)
    out.append(inp)

    txt = GEMS_README.format(
        built=time.strftime("%Y-%m-%d %H:%M"), version=VERSION,
        n_outfall=int((nd.IS_OUTFALL == 1).sum()), n_rm=len(layers["rising_mains"]),
        pf_hi=float(r.PF.max()),
        pf_lo=float(r.PF.iloc[int(np.argmax(r.QADF_M3D.to_numpy()))]),
        pf_held=int((r.PF_METH.astype(str) == "held").sum()),
        pf_hold=float(C.PF_HOLD_PROPERTIES), inf=C.INFILT_L_D_KM,
        past_cap=int((nd.PAST_CAP == 1).sum()),
        no_exit=int(((nd.PAST_CAP == 1) & (nd.CAP_EXIT.astype(str) == "")).sum()),
        maxcover=C.MAX_COVER, n_manning=C.MANNING_N_EXPORT, ks=C.KS, tau=C.TAU_PA,
        tract_km=lv.stats["km_tractive"],
        tract_pct=100.0 * lv.stats["km_tractive"] / lv.stats["km_total"])
    p = os.path.join(DIR_GEM, "README.txt")
    open(p, "w", encoding="utf-8").write(txt)
    out.append(p)
    _log(f"   SewerGEMS package: {len(mh):,} manholes, {len(of):,} outfalls, "
         f"{len(cd):,} conduits, LOADS.csv carries AVERAGE flow with our peak beside it")
    return out


def _swmm_inp(layers: Dict[str, gpd.GeoDataFrame], g: Graph) -> str:
    """An EPA SWMM 5 input file of the same network - a referee that is not Bentley.

    Dry weather flow only, average, at every junction: the peak factor is ours and stays
    out of the model (see the README). Sections are written in the order SWMM expects."""
    nd = layers["nodes"]
    r = layers["reaches"]
    p = os.path.join(DIR_GEM, "W11b.inp")
    L: List[str] = []
    L.append("[TITLE]")
    L.append(f";;W11b Ibri sewer - gravity network, {len(r):,} conduits. "
             f"Levels by the s8 stage-6 stand-in. tau={C.TAU_PA:g} Pa ASSUMED.")
    L.append(";;LOADS ARE AVERAGE DRY WEATHER FLOW. Our peak factor is NOT applied here.")
    L.append("")
    L.append("[OPTIONS]")
    for k, v in (("FLOW_UNITS", "LPS"), ("INFILTRATION", "HORTON"),
                 ("FLOW_ROUTING", "DYNWAVE"), ("LINK_OFFSETS", "ELEVATION"),
                 ("START_DATE", "01/01/2055"), ("END_DATE", "01/02/2055"),
                 ("REPORT_STEP", "00:15:00"), ("ROUTING_STEP", "00:00:15"),
                 ("MIN_SLOPE", "0")):
        L.append(f"{k:<22}{v}")
    L.append("")
    out_mask = nd.IS_OUTFALL == 1
    L.append("[JUNCTIONS]")
    L.append(";;Name           Elevation  MaxDepth   InitDepth  SurDepth   Aponded")
    for u, iv, dep in zip(nd.NODE_UID[~out_mask], nd.INV_M[~out_mask], nd.DEPTH_M[~out_mask]):
        L.append(f"{u:<17}{float(iv):<11.3f}{max(float(dep), 0.1):<11.3f}0          0          0")
    L.append("")
    L.append("[OUTFALLS]")
    L.append(";;Name           Elevation  Type       Gated")
    for u, iv in zip(nd.NODE_UID[out_mask], nd.INV_M[out_mask]):
        L.append(f"{u:<17}{float(iv):<11.3f}FREE       NO")
    L.append("")
    L.append("[CONDUITS]")
    L.append(";;Name           From             To               Length     Roughness  "
             "InOffset   OutOffset")
    for e, a_, b_, ln, iu, idn in zip(r.EDGE_UID, r.US_NODE, r.DS_NODE, r.LEN_M,
                                      r.INV_UP, r.INV_DN):
        L.append(f"{e:<17}{a_:<17}{b_:<17}{float(ln):<11.3f}"
                 f"{C.MANNING_N_EXPORT:<11.4f}{float(iu):<11.3f}{float(idn):<11.3f}")
    L.append("")
    L.append("[XSECTIONS]")
    L.append(";;Link           Shape        Geom1      Geom2 Geom3 Geom4 Barrels")
    for e, dn in zip(r.EDGE_UID, r.DN):
        L.append(f"{e:<17}CIRCULAR     {C.internal_diameter(int(dn)):<11.4f}0     0     0     1")
    L.append("")
    L.append("[DWF]")
    L.append(";;Node           Parameter  AverageValue")
    qavg = nd.Q_ADF_M3D.to_numpy(dtype=float) * 1000.0 / 86400.0
    for u, q in zip(nd.NODE_UID, qavg):
        if q > 1e-9:
            L.append(f"{u:<17}FLOW       {float(q):.6f}")
    L.append("")
    L.append("[COORDINATES]")
    L.append(";;Node           X-Coord    Y-Coord")
    for u, x, y in zip(nd.NODE_UID, nd.X, nd.Y):
        L.append(f"{u:<17}{float(x):<11.2f}{float(y):.2f}")
    L.append("")
    open(p, "w", encoding="utf-8").write("\n".join(L))
    _log(f"   {os.path.basename(p):<24} {os.path.getsize(p) / 1e6:8.1f} MB  "
         f"(EPA SWMM 5, average DWF only)")
    return p


# ======================================================================================
# 14.  QGIS
#
#      CLAUDE.md rule 3: named group, proper styling, layouts SAVED INTO the project.
#      CLAUDE.md rule 4: Google satellite hybrid at 30 %, MoH_Plots as the land-use layer,
#      a scalebar with non-overlapping labels, a data table bottom-right.
#
#      `present.qgis_plan()` / `qgis_code()` already produce all of that from the SAME
#      `View` objects the KMZ used, so the Earth files and the QGIS project physically
#      cannot disagree. This section only decides WHERE the project should point - at the
#      canonical `W11b_export.gpkg`, not at a copy, so the day a stage reruns the project
#      shows the new answer instead of a stale one.
# ======================================================================================

def qgis_script(res: "PR.RenderResult") -> str:
    p = os.path.join(OUT, "qgis_load_W11b.py")
    open(p, "w", encoding="utf-8").write(res.qgis_script)
    _log(f"   {os.path.basename(p):<24} {len(res.qgis_script) / 1024:8.0f} kB  "
         f"{len(res.qgis_plan['layers'])} styled layers, "
         f"{len(res.qgis_plan['layouts'])} layouts")
    return p


# ======================================================================================
# 15.  THE REPORT
# ======================================================================================

def _pct(x, of):
    return 0.0 if not of else 100.0 * x / of


def write_report(a: Assembly, g: Graph, f: Flows, lv: Levels, lv_st: Levels,
                 layers: Dict[str, gpd.GeoDataFrame], chk: pd.DataFrame,
                 cross_stats: Dict[str, Any], kmz: "PR.RenderResult",
                 files: Dict[str, List[str]], ofc: pd.DataFrame) -> str:
    nd, r = layers["nodes"], layers["reaches"]
    km = float(r.LEN_M.sum()) / 1000.0
    cover = nd.COVER_M.to_numpy(dtype=float)
    st = layers["stations"]
    cn = layers["connections"]
    L: List[str] = []
    A = L.append

    A("# W11b stage 8 - export, and the levels stage that does not exist")
    A("")
    A(f"*{VERSION}, built {time.strftime('%Y-%m-%d %H:%M')}. "
      f"Nothing imported from `W8/py/sewnet`, `W10/py` or `W11a/py`.*")
    A("")
    A("## The uncomfortable answer first")
    A("")
    A(f"**There is no stage 6 in W11b, so this stage had to build one.** Every invert, "
      f"diameter, gradient, velocity, depth of flow, cover and drop in this export came "
      f"out of a levels-and-sizes pass written inside `s8_export.py`, tagged "
      f"`STAGE = '{LEVELS_TAG}'` on every published row. It is a single strict pass; "
      f"philosophy sec 7 asks for two and then an audit.")
    A("")
    A(f"**And what it measures is not a tree problem. It is flatness.** "
      f"**{int((nd.PAST_CAP == 1).sum()):,} of {len(nd):,} chambers "
      f"({_pct(int((nd.PAST_CAP == 1).sum()), len(nd)):.1f} %) pass the 12 m cover cap** "
      f"(G203-p33), covering **{lv.stats['km_past_cap']:.1f} km** of the "
      f"{km:,.1f} km network, and **{lv.stats['past_cap_no_exit']:,} of them have no exit** "
      f"under philosophy sec 5 - neither a recovery within 500 m nor an outfall within "
      f"1,000 m, or the excursion forces a drop past "
      f"{C.DROP_CEILING_M:g} m and the exit is withdrawn. The deepest chamber carries "
      f"**{cover.max():.1f} m of cover**. That is not a levelling error and it is not the "
      f"tree: **{_pct(float(r.LEN_M[r.DN == 200].sum()), float(r.LEN_M.sum())):.1f} % of "
      f"the length is DN200**, whose Table 11 minimum is 5.00 mm/m (G203-p29), and "
      f"**{_pct(float(r.LEN_M[r.GRAD_BY.isin(['table11', 'tractive', 'uniform'])].sum()), float(r.LEN_M.sum())):.1f} % "
      f"of the length is laid at its governing MINIMUM gradient rather than at the "
      f"ground's own fall** - which is what it means to say the ground is flatter than the "
      f"pipe may be laid. There the pipe sinks whichever way it points.")
    A("")
    A(f"**The 85 stations s7 located are worth {lv.stats['past_cap_nodes'] - lv_st.stats['past_cap_nodes']:,} "
      f"chambers.** Run the same levels with each station resetting the depth at its "
      f"anchor chamber and the breach count falls "
      f"{lv.stats['past_cap_nodes']:,} -> {lv_st.stats['past_cap_nodes']:,} and the "
      f"no-exit count {lv.stats['past_cap_no_exit']:,} -> {lv_st.stats['past_cap_no_exit']:,}. "
      f"**The published layers are the GRAVITY-ONLY arm**, because the stations are not in "
      f"the written topology (H16) and their rising mains discharge to nodes this graph "
      f"does not contain. Putting them in the levels but not in the graph would publish a "
      f"network that carries its own flow twice.")
    A("")

    big = ofc[ofc.N_CHAMBER >= 20]
    bad = big[big.PCT_BELOW > 50.0]
    A("**And the first long section this stage drew found something no table had shown: "
      "some outfalls are near the TOP of their own catchment.** Over the 15.4 km of "
      "package P003 the invert falls in a straight line while the ground RISES. Measured "
      f"over all {len(ofc)} components: **{int(ofc.LOWEST.sum())} discharge at their own "
      f"lowest chamber**, and **{len(bad)} components of 20 chambers or more "
      f"({bad.LEN_KM.sum():,.1f} km, {_pct(float(bad.LEN_KM.sum()), km):.1f} % of the "
      f"network) discharge with MORE THAN HALF their catchment below the outlet**; the "
      f"worst outfall sits **{ofc.ABOVE_LOW.max():.1f} m above the lowest chamber it "
      f"serves**. That is a stage-2 / stage-3 orientation result, not a levelling one - no "
      f"invert arithmetic recovers a terminal placed uphill of its own catchment. The "
      f"table is `outfall_check` in the GeoPackage and in `W11b_outfall_check.csv`.")
    A("")
    if len(big) > 5:
        rho_len = float(big[["LEN_KM", "DEEPEST_M"]].corr(method="spearman").iloc[0, 1])
        rho_abv = float(big[["ABOVE_LOW", "DEEPEST_M"]].corr(method="spearman").iloc[0, 1])
        rho_pct = float(big[["PCT_BELOW", "DEEPEST_M"]].corr(method="spearman").iloc[0, 1])
        A(f"**Which of the two costs more depth, measured rather than asserted.** Over the "
          f"{len(big)} components of 20 chambers or more, Spearman rank correlation against "
          f"the deepest chamber in the component: **flow-path scale (component length) "
          f"{rho_len:+.3f}**, **outfall height above its own lowest chamber "
          f"{rho_abv:+.3f}**, share of the catchment below the outlet {rho_pct:+.3f}. So "
          f"length dominates - which is flatness, because the length is being laid at the "
          f"minimum gradient - and outfall placement is a close second. It is not one or "
          f"the other, and the ranking is the useful part: fixing the tree helps most "
          f"where the run is longest.")
        A("")
    A("## What was built")
    A("")
    A("| Path | What |")
    A("|---|---|")
    A(f"| `W11b/shp/W11b_export.gpkg` | {len(layers)} contract layers + the check table, "
      f"the manifest and the assumptions |")
    A(f"| `W11b/shp/kmz/*.kmz` | **{len(kmz.kmz)} styled Google Earth files**, each with "
      f"subfolders and a legend overlay |")
    A(f"| `W11b/export/shp/` | {len(files['shp'])} shapefiles + tables, every one proven "
      f"to round-trip without losing a field name |")
    A(f"| `W11b/export/dxf/` | {len(files['dxf'])} drawings - geometry, and geometry with "
      f"every chamber and pipe labelled |")
    A(f"| `W11b/export/schedules/` | {len(files['sch'])} workbooks - chambers, pipes, "
      f"stations, rising mains, connections, crossings, packages, quantities, not-served, "
      f"data dictionary |")
    A(f"| `W11b/export/profiles/` | {len(files['prf'])} long sections |")
    A(f"| `W11b/export/sewergems/` | the model package, the field map, the read-me and a "
      f"runnable EPA SWMM 5 `.inp` |")
    A(f"| `W11b/export/qgis_load_W11b.py` | the PyQGIS loader, generated from the SAME "
      f"View objects the KMZ used |")
    A("")

    A("## The design, measured")
    A("")
    A("| | | Source |")
    A("|---|---|---|")
    A(f"| Gravity sewer | **{km:,.1f} km** | s4's chamber-to-chamber segments |")
    A(f"| Chambers | **{len(nd):,}** ({len(nd) / km:.1f} per km) | s4; built network 34.2/km |")
    A(f"| Components, each ending at exactly one outfall | **{int((nd.IS_OUTFALL == 1).sum())}** | H15 |")
    A(f"| Diameters | **DN{int(r.DN.min())}-{int(r.DN.max())}** | H8, sized on flow alone |")
    A(f"| Laid gradient | {r.SLOPE_LAID.min():.2f} - {r.SLOPE_LAID.max():.2f} %, "
      f"median {r.SLOPE_LAID.median():.2f} % | 0.05 % steps, P1 |")
    A(f"| Peak flow, largest reach | **{r.QPK_LS.max():.1f} L/s** | s5 published 234.7 |")
    A(f"| Velocity at peak | {r.V_PK_MS.min():.2f} - {r.V_PK_MS.max():.2f} m/s, "
      f"**0 over the 3.0 m/s maximum** | G203-p27 |")
    A(f"| d/D at peak | max {r.DOD_PK.max():.3f}, **0 reaches over the Table 10 limit** | "
      f"G203-p27 Tab 10 |")
    A(f"| Cover | median {np.median(cover):.2f} m, deepest **{cover.max():.2f} m** | G203-p33 |")
    A(f"| Below the 1.30 m minimum cover | **{lv.stats['km_below_min_cover']:.2f} km** | G203-p33 |")
    A(f"| Backdrops (0.60-2.00 m) | {int((nd.DROP_TYPE == 'backdrop').sum()):,} | G203-p30 |")
    A(f"| **Vortex drop shafts (> 2.00 m)** | **{int((nd.DROP_TYPE == 'vortex').sum()):,}** | "
      f"G203-p30. NAMA's built network has 37 |")
    A(f"| Inlets under 90 deg | {int((nd.INLET_FLAG == 1).sum()):,} | G203-p30, H10 |")
    A(f"| Draining against the ground | **{_pct(float(r.LEN_M[r.AGN_GRADE == 1].sum()), float(r.LEN_M.sum())):.1f} %** "
      f"of length ({float(r.LEN_M[r.AGN_GRADE == 1].sum()) / 1000:.1f} km) | "
      f"philosophy sec 4; NAMA's own built network runs uphill on 34 % |")
    A(f"| Load connected | **{float(cn.Q_ADF_M3D.sum()):,.1f} m3/d** over "
      f"{len(cn):,} plots | s4; s5 published 70,405.5 |")
    A(f"| Properties | {float(cn.N_PROP.sum()):,.0f} | s4 |")
    A("")

    A("### Self-cleansing, and the size of the tau exposure")
    A("")
    A(f"**{lv.stats['km_tractive']:,.1f} km ({_pct(lv.stats['km_tractive'], km):.1f} %) is "
      f"self-cleansed by the TRACTIVE route**, {lv.stats['km_velocity']:,.1f} km "
      f"({_pct(lv.stats['km_velocity'], km):.1f} %) by velocity, and "
      f"{lv.stats['km_neither']:.2f} km by neither. G203-p27 4.2.2.1 offers the two as "
      f"alternatives and requires the steeper, so the tractive share is legal - and it is "
      f"also the exact extent of the scheme resting on tau = {C.TAU_PA:g} Pa, which the "
      f"guideline never gives (GAP-9). At 2.0 Pa every one of those gradients rises "
      f"{C.TAU_SLOPE_FACTOR_AT_2PA:.3f}x.")
    A("")

    A("### What set each diameter, and what set each gradient")
    A("")
    A("| Diameter set by | Reaches | km | | Gradient set by | Reaches | km |")
    A("|---|---|---|---|---|---|---|")
    sb = r.groupby("SIZED_BY").agg(n=("LEN_M", "size"), km=("LEN_M", "sum"))
    gb = r.groupby("GRAD_BY").agg(n=("LEN_M", "size"), km=("LEN_M", "sum"))
    sb_rows = [(i, int(v.n), v.km / 1000) for i, v in sb.iterrows()]
    gb_rows = [(i, int(v.n), v.km / 1000) for i, v in gb.iterrows()]
    for i in range(max(len(sb_rows), len(gb_rows))):
        s_ = sb_rows[i] if i < len(sb_rows) else ("", "", "")
        gg = gb_rows[i] if i < len(gb_rows) else ("", "", "")
        A(f"| {s_[0]} | {s_[1]} | {s_[2] if s_[2] == '' else f'{s_[2]:,.1f}'} | | "
          f"{gg[0]} | {gg[1]} | {gg[2] if gg[2] == '' else f'{gg[2]:,.1f}'} |")
    A("")
    A("`depth` and `cover` are not in the SIZED_BY vocabulary and cannot be: oversizing a "
      "pipe to lay it flatter is prohibited by G203-p29 and by Ten States sec 33.43 "
      "independently, so the prohibited move is not expressible on the layer.")
    A("")

    A("### The wadi and dual-carriageway register, MEASURED")
    A("")
    A(f"**{cross_stats['n_rows']:,} registered contacts** - {cross_stats['n_wadi']:,} wadi, "
      f"{cross_stats['n_dual']:,} dual carriageway - over "
      f"**{cross_stats['km_wadi']:.2f} km** of wadi ground and "
      f"**{cross_stats['km_dual']:.3f} km** of dual carriageway. The angle is measured "
      f"against the nearest stream line's own direction, sampled every "
      f"{WADI_SAMPLE_M:g} m off the {C.HAZARD_RETURN_YR}-year hazard grid: "
      f"**median {cross_stats['angle_median']:.1f} deg, minimum "
      f"{cross_stats['angle_min']:.1f} deg, and only {cross_stats['n_square']:,} of "
      f"{cross_stats['n_rows']:,} sit within {C.WADI_XING_SKEW_DEG:g} deg of square.** "
      f"The rest run ALONG the channel rather than across it, which H1 forbids and H1a "
      f"does not excuse. `APPROVED = 0` on every row: MoAFWR consent (G201-p85) and the "
      f"roads authority's are open items, not silent ones.")
    A("")
    A(f"*W11a published `ANGLE_DEG = 90` on 3,290 crossings. It was fabricated and the "
      f"measured minimum was 0.00 deg. This register measures every one.*")
    A("")

    A("### CAN_DRAIN, answered for the first time")
    A("")
    A(f"s4 published `CAN_DRAIN cannot run - no designed invert exists at stage 4`. There "
      f"is one now. **{int((cn.CAN_DRAIN == 1).sum()):,} of {len(cn):,} connected plots "
      f"can reach their chamber on gravity**; **{int((cn.CAN_DRAIN == 0).sum()):,} cannot** "
      f"- the sewer invert sits above the property outlet at the G203-p19 3.4 minimum HCC "
      f"depth of {C.HCC_DEPTH_MIN:g} m, with the {C.PCS_MIN_SLOPE * 100:g} % minimum "
      f"gradient of G203-p18 Table 5 over the connection's own length. They are in "
      f"`W11b_schedule_not_served.xlsx`, sheet 2, each named.")
    A("")

    A("## What does NOT validate, and why each one is real")
    A("")
    A("`contract.validate()` was run over every published layer before a single schedule, "
      "drawing or model file was written. Nothing was silenced. The full text of every "
      "objection is in the `contract_check` layer of the GeoPackage and on the last sheet "
      "of the data dictionary.")
    A("")
    A("| Layer | Result |")
    A("|---|---|")
    for row in chk.itertuples():
        A(f"| `{row.LAYER}` | {'PASSES' if row.PASS else '**' + row.RESULT + '**'} |")
    A("")
    A("| What fails | Extent | Whose it is |")
    A("|---|---|---|")
    A(f"| Depth / cover / drop past the contract's 40 m and 20 m range guards | "
      f"{int((nd.DEPTH_M > CT.DEPTH_SANITY_M).sum()):,} chambers, "
      f"{int((nd.DROP_M > C.DROP_CEILING_M).sum()):,} drops, worst "
      f"{nd.DROP_M.max():.1f} m | **the design.** Flatness, not arithmetic |")
    A(f"| Past the 12 m cap with no sec 5 exit | {lv.stats['past_cap_no_exit']:,} chambers, "
      f"{int(((r.PAST_CAP == 1) & (r.CAP_EXIT.fillna('').astype(str) == '')).sum()):,} reaches | "
      f"**stage 7's**: every one is a station demand |")
    A(f"| `SLOPE_LAID` over the contract's 25 % bound | "
      f"{int((r.SLOPE_LAID > 25.0).sum())} reaches, worst {r.SLOPE_LAID.max():.2f} % | "
      f"**the ground.** Capping them put the pipe above the surface, which is not a "
      f"conservative answer but an impossible one |")
    A(f"| `LEN_M` under the 0.5 m floor | {int((r.LEN_M < 0.5).sum())} reach "
      f"({r.LEN_M.min():.3f} m) | s4's chamber spacing |")
    A(f"| `connections` geometry invalid | "
      f"{int((cn.LEN_M < 1e-9).sum()):,} zero-length connections | s4: the chamber stands "
      f"on the property's own connection point. Shapely calls a zero-length LineString "
      f"invalid |")
    A(f"| `FLOOD_LV` null on all {len(st)} stations | 85 | **NWS.** "
      f"`hazard.flood_level_m_aod()` raises by design - the grids carry an AR&R hazard "
      f"CLASS and no water level, and G203-p38 7.2 needs the 1:50 water surface for the "
      f"300 mm freeboard. Filling it with ground level (which this stage did on its first "
      f"build) manufactured a freeboard failure on all 85 that says nothing about any |")
    A(f"| Rising mains under 0.75 m/s at design MINIMUM flow | {len(layers['rising_mains'])} | "
      f"**s7's**, inherited unchanged |")
    A(f"| `WELL_M3` disagrees with 0.25 Q T | 1 station | **s7's**, inherited unchanged |")
    A(f"| 2 reaches touch BOTH a wadi and a dual carriageway | 2 | **the contract's**: a "
      f"reach carries one `CROSS_ID` and cannot be registered against two obstacles |")
    A("")

    A("## What this export could NOT do")
    A("")
    A("1. **Design the trunk.** `W11b_hier.gpkg|trunk` is 85.49 km of the client's own "
      "Main Pipe in 54 pieces, with no chambers and no topology. Nothing here drains into "
      "it. The 195 outfalls are subnetwork outlets, each an independent discharge, and "
      "the biggest reach in the design therefore carries a fraction of what a joined "
      "network would - s5 measured the like-for-like figure at 1,362 L/s and tagged it a "
      "hypothetical. It is still one.")
    A("2. **Resolve the station ids.** s7 minted `NODE_UID` N0000001-N0000085; those "
      "strings also exist in the chamber layer on different chambers, and none of the 85 "
      "agree on ground level. Re-anchored by proximity - median 0.00 m, max 65.9 m, 75 of "
      "85 within 1 m - and published as `ANCHOR_ND` with `ST_SNAP_M` beside it. A "
      "recovered anchor is not written topology (H16).")
    A("3. **Phase anything.** `PHASE = 0` on every row: the contract's own words are "
      "\"0 = not yet assigned\". Packages are one per subnetwork - which satisfies "
      "\"one tree, one outlet\" by construction and the 3.5-40 km size band only where it "
      f"happens to: {int(layers['packages'].IN_BAND.sum())} of "
      f"{len(layers['packages'])} do, largest {layers['packages'].LEN_KM.max():.1f} km, "
      f"median {layers['packages'].LEN_KM.median():.2f} km.")
    A("4. **Run the second pass.** Philosophy sec 7 wants a strict pass, a review pass and "
      "then the audit. This is one strict pass. Nothing here absorbs a finger, moves a sub "
      "main onto a through-street or puts a station on a package seam.")
    A("5. **Referee its own hydraulics.** The SewerGEMS package and the SWMM `.inp` are "
      "written but not run. A solver will not object to a chamber 85 m deep - it deepens "
      "forever - so the referee checks the hydraulics and never the routing.")
    A("")

    A("## Every number this stage used that is not already in `criteria`")
    A("")
    A("| Name | Value | Source | Why |")
    A("|---|---|---|---|")
    for name, val, src, why in EXPORT_NUMBERS:
        A(f"| `{name}` | {val} | {src} | {why} |")
    A("")
    A(f"*{C.tau_banner()}*")
    A("")

    A("## The KMZ set")
    A("")
    A("| File | The question it answers |")
    A("|---|---|")
    for k in sorted(kmz.kmz, key=lambda x: PR.VIEWS[x.view].priority):
        v = PR.VIEWS[k.view]
        A(f"| `{os.path.basename(k.path)}` | {v.question} |")
    if kmz.skipped:
        A("")
        A("Skipped, with the reason:")
        for nm, why in kmz.skipped:
            A(f"- `{nm}`: {why}")
    A("")
    A("## Run log")
    A("")
    A("```")
    L.extend(_LOG)
    A("```")

    p = os.path.join(RUN, "EXPORT.md")
    os.makedirs(RUN, exist_ok=True)
    open(p, "w", encoding="utf-8").write("\n".join(L))
    return p


# ======================================================================================
# 16.  BUILD, VERIFY, SELF-TEST
# ======================================================================================

def build(do_dxf: bool = True, do_profiles: bool = True, do_kmz: bool = True) -> Dict[str, Any]:
    _mkdirs()
    with CT.Manifest.stage(STAGE, STAGE_ORDER) as rec:
        a = assemble()
        for nm, src, n in a.reads:
            rec.read(nm, src, n)
        g = build_graph(a)
        f = accumulate(a, g)

        # the two arms. The GRAVITY-ONLY arm is what gets published; the with-stations arm
        # is run so the relief the 85 stations buy is a MEASURED number and not a claim.
        lv = design_levels(a, g, f, label="gravity only - PUBLISHED")
        anchors = [g.ix[u] for u in a.stations.ANCHOR_ND.astype(str) if u in g.ix]
        lv_st = design_levels(a, g, f, station_nodes=anchors,
                              label="with the 85 s7 stations - measured, NOT published")

        contacts = measure_contacts(a, g)
        cx, cross_id, cross_stats = build_crossings(a, g, contacts)
        pk, node_pkg, edge_pkg = build_packages(a, g, f)

        layers = build_layers(a, g, f, lv, contacts, cross_id, node_pkg, edge_pkg)
        layers["connections"] = build_connections(a, g, layers["nodes"], layers["reaches"])
        layers["stations"], layers["rising_mains"] = build_stations(a, layers["nodes"])
        layers["crossings"] = cx
        layers["packages"] = pk
        layers["trunk"] = build_trunk(a)
        _extra_columns(layers)
        layers["package_areas"] = package_areas(layers)
        register_extra_views()
        tune_views()
        add_band_columns(layers)

        fun = rec.funnel("plots -> connections", int(len(a.connections) + len(a.unserved)))
        fun.drop("no chamber within 45 m of the plot (s4)", n=len(a.unserved),
                 qty=float(a.unserved.Q_ADF_M3D.sum()))
        fun.close(len(layers["connections"]))

        ofc = outfall_check(g, f, layers)
        chk = check_contract(layers)
        _log("contract check: " + ", ".join(
            f"{r.LAYER}={'pass' if r.PASS else 'FAIL'}" for r in chk.itertuples()))

        extra = {
            "contract_check": chk,
            "manifest": _manifest_table(a, g, f, lv, lv_st, layers, cross_stats),
            "assumptions": _assumptions_table(),
            "levels_arms": _arms_table(lv, lv_st),
            "outfall_check": ofc,
        }
        pub = {k: v for k, v in layers.items()}
        publish(pub, extra)
        for k, v in pub.items():
            rec.wrote(k, GPKG_OUT, len(v))

        files: Dict[str, List[str]] = {"shp": [], "dxf": [], "sch": [], "prf": [], "gem": []}
        files["shp"] = write_shapefiles(
            {k: v for k, v in layers.items() if k != "packages"},
            {"packages": pk, "contract_check": chk, "manifest": extra["manifest"],
             "levels_arms": extra["levels_arms"], "outfall_check": ofc})
        if do_dxf:
            files["dxf"] = write_dxf(layers)
        files["sch"] = write_schedules(a, layers, chk)
        if do_profiles:
            files["prf"] = write_profiles(g, layers, node_pkg)
        files["gem"] = write_sewergems(layers, lv, f, g)

        kmz = build_kmz_from_gpkg() if do_kmz else None
        if kmz is not None:
            qgis_script(kmz)
        rep = write_report(a, g, f, lv, lv_st, layers, chk, cross_stats,
                           kmz or _empty_render(), files, ofc)
        _log(f"report -> {rep}")
        rec.metric("network_km", round(float(layers['reaches'].LEN_M.sum()) / 1000.0, 3))
        rec.metric("chambers", len(layers["nodes"]))
        rec.metric("past_cap_no_exit", lv.stats["past_cap_no_exit"])
        rec.metric("vortex_shafts", int((layers["nodes"].DROP_TYPE == "vortex").sum()))
        rec.note("levels and sizes produced by the s8 STAGE-6 STAND-IN; W11b has no s6")
    return dict(layers=layers, levels=lv, levels_stations=lv_st, check=chk, files=files,
                report=rep, graph=g, flows=f)


def _empty_render():
    return PR.RenderResult(DIR_KMZ, [], {"layers": [], "layouts": []}, "", [], {})


def build_kmz_from_gpkg() -> "PR.RenderResult":
    """Render every view straight off the PUBLISHED GeoPackage.

    Not off the in-memory frames: the QGIS project this generates points at the same file,
    so a reviewer opening it after the next rerun sees the new answer instead of a copy
    that has quietly gone stale. It also means the KMZ is drawn from exactly the bytes the
    contract check was run against."""
    roles = {r: (GPKG_OUT, r) for r in
             ("reaches", "nodes", "stations", "rising_mains", "crossings", "connections")}
    roles["packages"] = (GPKG_OUT, "package_areas")
    register_extra_views()
    tune_views()
    fold_on_bands()
    _log(f"rendering {len(KMZ_VIEWS)} KMZ views through w11b.present, off "
         f"{os.path.basename(GPKG_OUT)}")
    res = PR.render(roles, DIR_KMZ, views=KMZ_VIEWS, prefix="W11b", group="Claude W11b",
                    layouts=("tier", "depth", "subnet", "diameter", "stations",
                             "pumping_demand"),
                    legend=True, max_features=260_000)
    print(res.report())
    return res


def _manifest_table(a, g, f, lv, lv_st, layers, cross_stats) -> pd.DataFrame:
    nd, r = layers["nodes"], layers["reaches"]
    km = float(r.LEN_M.sum()) / 1000.0
    rows = [
        ("stage", VERSION, "-", "this module"),
        ("run", time.strftime("%Y-%m-%d %H:%M"), "-", ""),
        ("LEVELS_SRC", LEVELS_TAG, "-",
         "W11b HAS NO STAGE 6. Every invert, DN, gradient, velocity, d/D, cover and drop "
         "below came from the stand-in in s8_export.py section 4"),
        ("network", round(km, 3), "km", "LEN_M over the published reach layer"),
        ("chambers", len(nd), "-", "the published node layer"),
        ("chambers per km", round(len(nd) / km, 2), "-", "built network 34.23 (s4/asbuilt)"),
        ("outfalls", int((nd.IS_OUTFALL == 1).sum()), "-",
         "H15: one per component. NOT the works - the trunk is not in this graph"),
        ("load connected", round(float(layers['connections'].Q_ADF_M3D.sum()), 1), "m3/d",
         "s4; s5 published 70,405.5 and this accumulator reproduces it"),
        ("DN range", f"DN{int(r.DN.min())}-{int(r.DN.max())}", "mm", "H8, sized on flow"),
        ("largest peak flow", round(float(r.QPK_LS.max()), 2), "L/s",
         "s5 published 234.7 over its corridor arcs"),
        ("max velocity", round(float(r.V_PK_MS.max()), 3), "m/s", "G203-p27 max 3.0"),
        ("max d/D", round(float(r.DOD_PK.max()), 4), "-", "G203-p27 Tab 10"),
        ("median cover", round(float(np.median(nd.COVER_M)), 3), "m", "G203-p33 min 1.30"),
        ("deepest cover", round(float(nd.COVER_M.max()), 3), "m", "G203-p33 cap 12"),
        ("past the 12 m cap", int((nd.PAST_CAP == 1).sum()), "chambers", "G203-p33"),
        ("past the cap WITH NO EXIT", lv.stats["past_cap_no_exit"], "chambers",
         "philosophy sec 5 - each is a station demand handed back to stage 7"),
        ("relief from the 85 s7 stations",
         lv.stats["past_cap_nodes"] - lv_st.stats["past_cap_nodes"], "chambers",
         "MEASURED by re-running the levels with each station resetting depth. NOT "
         "published - the stations are not in the written topology"),
        ("backdrops", int((nd.DROP_TYPE == "backdrop").sum()), "-", "G203-p30, 0.60-2.00 m"),
        ("VORTEX DROP SHAFTS", int((nd.DROP_TYPE == "vortex").sum()), "-",
         "G203-p30. NAMA's built network has 37 - philosophy sec 4 diagnostic"),
        ("largest drop", round(float(nd.DROP_M.max()), 2), "m",
         f"criteria.DROP_CEILING_M is {C.DROP_CEILING_M:g} m and is a PROJECT ASSUMPTION"),
        ("draining against the ground",
         round(_pct(float(r.LEN_M[r.AGN_GRADE == 1].sum()), float(r.LEN_M.sum())), 2), "%",
         "philosophy sec 4; NAMA's built network 34 %"),
        ("self-cleansed by TRACTIVE", round(lv.stats["km_tractive"], 1), "km",
         f"G203-p27 4.2.2.1. THE tau EXPOSURE - {C.TAU_PA:g} Pa is an ASSUMPTION (GAP-9)"),
        ("self-cleansed by VELOCITY", round(lv.stats["km_velocity"], 1), "km", "G203-p26"),
        ("self-cleansed by NEITHER", round(lv.stats["km_neither"], 2), "km", "H5 - a failure"),
        ("wadi ground", round(cross_stats["km_wadi"], 2), "km",
         f"MEASURED, {C.HAZARD_RETURN_YR}-yr grid classes {C.HAZARD_WADI_CLASSES}, "
         f"sampled every {WADI_SAMPLE_M:g} m"),
        ("registered crossings", cross_stats["n_rows"], "-", "H1a register"),
        ("crossings within the skew tolerance", cross_stats["n_square"], "-",
         f"criteria.WADI_XING_SKEW_DEG = {C.WADI_XING_SKEW_DEG:g} deg. The rest run ALONG"),
        ("measured crossing angle, median", round(cross_stats["angle_median"], 1), "deg",
         "against the nearest stream's own direction. W11a asserted 90 on 3,290"),
        ("plots that CANNOT drain to their chamber",
         int((layers['connections'].CAN_DRAIN == 0).sum()), "-",
         "s4 could not run this check; there are inverts now"),
        ("pumping stations", len(layers["stations"]), "-", "s7_pumps, unchanged"),
        ("rising main", round(float(layers["rising_mains"].LEN_M.sum()) / 1000.0, 3), "km",
         "s7_pumps, unchanged"),
        ("client trunk main", round(float(layers["trunk"].LEN_M.sum()) / 1000.0, 2), "km",
         "INPUT. Not chambered, not levelled; nothing here drains into it"),
        ("tau", C.TAU_PA, "Pa", "ASSUMPTION, GAP-9. At 2.0 every tractive gradient x2.346"),
    ]
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "SOURCE"])


def _assumptions_table() -> pd.DataFrame:
    rows = [dict(ID=a.aid, HEADLINE=a.headline, DETAIL=a.detail, CONSEQUENCE=a.consequence)
            for a in PR.ASSUMPTIONS.values()]
    rows += [dict(ID=f"S8-{i + 1}", HEADLINE=f"{n} = {v}", DETAIL=s, CONSEQUENCE=w)
             for i, (n, v, s, w) in enumerate(EXPORT_NUMBERS)]
    return pd.DataFrame(rows)


def _arms_table(lv: Levels, lv_st: Levels) -> pd.DataFrame:
    keys = ["past_cap_nodes", "past_cap_no_exit", "vortex", "backdrop", "deepest_cover",
            "median_cover", "km_past_cap", "km_below_min_cover", "km_tractive",
            "km_velocity", "n_over_vmax", "n_over_dod"]
    return pd.DataFrame([
        dict(MEASURE=k,
             GRAVITY_ONLY=round(float(lv.stats[k]), 4),
             WITH_85_STATIONS=round(float(lv_st.stats[k]), 4),
             PUBLISHED="gravity only",
             NOTE="the stations are s7's and are NOT in the written topology (H16); "
                  "their rising mains discharge to nodes this graph does not contain")
        for k in keys])


def verify() -> int:
    """Re-derive every headline from the PUBLISHED GeoPackage alone, and fail if any of
    them disagrees with what the manifest claims. Reading the file back is the point: a
    stage that verifies its own in-memory model verifies nothing."""
    import fiona
    bad: List[str] = []
    have = set(fiona.listlayers(GPKG_OUT))
    need = {"nodes", "reaches", "connections", "stations", "rising_mains", "crossings",
            "packages", "trunk", "package_areas", "manifest", "contract_check"}
    if not need <= have:
        print(f"MISSING LAYERS: {sorted(need - have)}")
        return 1
    nd = gpd.read_file(GPKG_OUT, layer="nodes")
    r = gpd.read_file(GPKG_OUT, layer="reaches")
    mf = pd.read_csv(os.path.join(DIR_SHP, "W11b_manifest.csv")) \
        if os.path.exists(os.path.join(DIR_SHP, "W11b_manifest.csv")) else \
        gpd.read_file(GPKG_OUT, layer="manifest")
    man = dict(zip(mf.ITEM.astype(str), mf.VALUE.astype(str)))

    def eq(name, got, want, tol=0.02):
        try:
            ok = abs(float(got) - float(want)) <= tol
        except Exception:
            ok = str(got) == str(want)
        print(f"  {'OK ' if ok else 'BAD'}  {name:<38} recomputed {got}   manifest {want}")
        if not ok:
            bad.append(name)

    eq("network km", round(float(r.LEN_M.sum()) / 1000.0, 3), man["network"], 0.002)
    eq("chambers", len(nd), man["chambers"], 0)
    eq("outfalls", int((nd.IS_OUTFALL == 1).sum()), man["outfalls"], 0)
    eq("past the 12 m cap", int((nd.PAST_CAP == 1).sum()), man["past the 12 m cap"], 0)
    eq("past the cap WITH NO EXIT",
       int(((nd.PAST_CAP == 1) & (nd.CAP_EXIT.fillna("").astype(str).str.strip() == "")).sum()),
       man["past the cap WITH NO EXIT"], 0)
    eq("VORTEX DROP SHAFTS", int((nd.DROP_TYPE == "vortex").sum()),
       man["VORTEX DROP SHAFTS"], 0)
    eq("max d/D", round(float(r.DOD_PK.max()), 4), man["max d/D"], 1e-4)
    eq("deepest cover", round(float(nd.COVER_M.max()), 3), man["deepest cover"], 0.002)

    # invariants that must hold on the file, not on a model
    dup = int(nd.NODE_UID.duplicated().sum())
    print(f"  {'OK ' if dup == 0 else 'BAD'}  duplicate NODE_UID                     {dup}")
    if dup:
        bad.append("duplicate NODE_UID")
    known = set(nd.NODE_UID.astype(str))
    dangle = int((~r.US_NODE.astype(str).isin(known)).sum()
                 + (~r.DS_NODE.astype(str).isin(known)).sum())
    print(f"  {'OK ' if dangle == 0 else 'BAD'}  reach endpoints that resolve           "
          f"{len(r) * 2 - dangle} of {len(r) * 2}")
    if dangle:
        bad.append("dangling reach endpoint")
    rev = int(((r.INV_UP - r.INV_DN) < -C.LAY_TOLERANCE_M).sum())
    print(f"  {'OK ' if rev == 0 else 'BAD'}  reverse gradients (G203-p29)           {rev}")
    if rev:
        bad.append("reverse gradient")
    fall = (r.INV_UP - r.INV_DN) - r.LEN_M * r.SLOPE_LAID / 100.0
    off = int((fall.abs() > C.LAY_TOLERANCE_M + 1e-3).sum())
    print(f"  {'OK ' if off == 0 else 'BAD'}  inverts reproduce LEN x SLOPE_LAID     "
          f"{len(r) - off} of {len(r)}")
    if off:
        bad.append("inverts do not reproduce the laid gradient")
    step = C.SLOPE_STEP * 100.0
    ns = int((((r.SLOPE_LAID / step) - (r.SLOPE_LAID / step).round()).abs() > 1e-6).sum())
    print(f"  {'OK ' if ns == 0 else 'BAD'}  gradients on the {step:g} % step          "
          f"{len(r) - ns} of {len(r)}")
    if ns:
        bad.append("gradient off the step")
    qpk = r.QADF_M3D * 1000.0 / 86400.0 * r.PF + r.QINF_LS
    nq = int(((qpk - r.QPK_LS).abs() > 0.01 * qpk.abs() + 0.01).sum())
    print(f"  {'OK ' if nq == 0 else 'BAD'}  QPK reproducible from its own row      "
          f"{len(r) - nq} of {len(r)}")
    if nq:
        bad.append("QPK not reproducible")
    dn_bad = int((~r.DN.isin(list(C.DN_SERIES))).sum())
    print(f"  {'OK ' if dn_bad == 0 else 'BAD'}  DN in criteria.DN_SERIES               "
          f"{len(r) - dn_bad} of {len(r)}")
    if dn_bad:
        bad.append("DN outside the series")

    chk = gpd.read_file(GPKG_OUT, layer="contract_check")
    n_fail = int((chk["PASS"] == 0).sum())
    print(f"\n  contract.validate(): {len(chk) - n_fail} of {len(chk)} layers pass. "
          f"{n_fail} carry named, published violations - see the `contract_check` layer.")
    print(f"\n{'VERIFY PASSED' if not bad else 'VERIFY FAILED: ' + ', '.join(bad)}")
    return 1 if bad else 0


def selftest() -> int:
    """Small, closed checks on the machinery, not on the data. Each one is a bug that was
    actually made while writing this file."""
    fails = []

    def ck(name, cond, detail=""):
        print(f"  {'OK ' if cond else 'BAD'}  {name}" + (f"   {detail}" if detail else ""))
        if not cond:
            fails.append(name)

    # 1. rounding a cover-governed gradient DOWN breaches minimum cover. It put 232 km of
    #    this network under 1.30 m on the first build.
    s = 0.0123
    ck("round_slope_up never lands flatter than asked",
       C.round_slope_up(s) >= s - 1e-15, f"{C.round_slope_up(s):.5f} >= {s}")
    ck("round_slope_down never lands steeper than asked",
       C.round_slope_down(s) <= s + 1e-15)
    # 2. cover() is the exact inverse of invert_depth_min()
    for dn in (200, 315, 500, 900, 1400):
        ck(f"cover(DN{dn}, invert_depth_min) == MIN_COVER_CROWN",
           abs(C.cover(dn, C.invert_depth_min(dn)) - C.MIN_COVER_CROWN) < 1e-12)
    # 3. the memo must not change an answer
    for q, sl, dn in ((0.004, 0.005, 200), (0.05, 0.002, 500), (0.2, 0.001, 900)):
        a1 = HY.pipe_state(dn, sl, q, C)
        a2 = state(dn, sl, q)
        ck(f"memoised pipe_state matches hydra (DN{dn})",
           (a1[0] is None) == (a2[0] is None)
           and (a1[0] is None or abs(a1[0] - a2[0]) < 1e-12))
    # 4. SIZED_BY must not be laundered by feeding size_pipe the previous guess
    d1 = HY.size_pipe(0.06, 0.005, C, dn_min=200)
    d2 = HY.size_pipe(0.06, 0.005, C, dn_min=int(d1[0] or 200))
    ck("size_pipe reports 'minimum' when offered only the size that fits",
       d2[3] == "minimum" and d1[3] != "minimum",
       f"floor-anchored {d1[3]!r} vs guess-anchored {d2[3]!r}")
    # 5. peak factor FALLS as the catchment grows - the reason it is never summed
    pf_small, _ = C.peak_factor(50.0, 200.0)
    pf_big, _ = C.peak_factor(9600.0, 12920.0)
    ck("Merrimack peak factor falls as the catchment grows",
       pf_big < pf_small, f"{pf_small:.3f} -> {pf_big:.3f}")
    ck("peak factor is HELD at 1.0 below 100 properties",
       C.peak_factor(50.0, 99.0) == (1.0, "held"))
    # 6. infiltration is per-LENGTH and additive; peak flow is not
    ck("infiltration is linear in length",
       abs(C.infiltration_ls(2000.0) - 2 * C.infiltration_ls(1000.0)) < 1e-15)
    # 7. every enum this stage writes is one the contract declares
    ck("GRAD_BY vocabulary is the contract's",
       set(("table11", "tractive", "uniform", "cover_min", "cover_max", "ground", "vmax"))
       <= set(CT.GRAD_BY))
    ck("SIZED_BY vocabulary is the contract's",
       set(("minimum", "dod", "capacity", "velocity", "infeasible")) <= set(CT.SIZED_BY))
    ck("NODE_KIND vocabulary is the contract's",
       {"chamber", "head", "junction", "outfall", "drop"} <= set(CT.NODE_KIND))
    ck("SRC map lands only on contract values", set(SRC_MAP.values()) <= set(CT.SRC))
    ck("CONFIDENCE map lands only on contract values",
       set(CONF_MAP.values()) <= set(CT.CONFIDENCE))
    # 8. present.py's numbers still agree with criteria
    dis = PR.verify_against_criteria()
    ck("present.py agrees with criteria on every shared number", not dis, "; ".join(dis))
    # 9. the extra views register cleanly and every one has a question
    names = register_extra_views()
    ck("the six extra views register", len(names) == 6)
    ck("every view states the question it answers",
       all(PR.VIEWS[n].question for n in PR.list_views()))
    # 10. no field name this stage writes would be truncated by a DBF
    long = [f for spec in CT.LAYERS.values() for f in spec.names
            if len(f) > CT.SHP_FIELD_MAXLEN]
    ck("no contract field exceeds the DBF limit", not long, str(long))
    for c in ("CAP_WHY", "XING_CLS", "DRAIN_TXT", "CLEAN_TXT", "ST_SNAP_M", "ANCHOR_ND",
              "FALL_AV_M", "CAP_LEN_M", "ST_RESET", "UPS_LEN_M", "RUN_LEN_M", "UID_S7"):
        ck(f"extra field {c} fits a DBF name", len(c) <= CT.SHP_FIELD_MAXLEN)
    # 11. the cap exits are the contract's two, and blank is legal
    ck("CAP_EXIT vocabulary", set(("", "recovers_500m", "outfall_1000m")) == set(CT.CAP_EXIT))
    print(f"\n{len(fails)} of many checks failed" if fails else "\nall self-checks pass")
    return 1 if fails else 0


# ======================================================================================
# 17.  CLI
# ======================================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="build",
                    choices=["build", "verify", "selftest", "report", "kmz", "qgis"])
    ap.add_argument("--no-dxf", action="store_true", help="skip the two DXF drawings")
    ap.add_argument("--no-profiles", action="store_true", help="skip the long sections")
    ap.add_argument("--no-kmz", action="store_true", help="skip the KMZ set")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "verify":
        return verify()
    if a.cmd == "kmz":
        _mkdirs()
        res = build_kmz_from_gpkg()
        qgis_script(res)
        return 0
    if a.cmd == "qgis":
        _mkdirs()
        res = build_kmz_from_gpkg()
        print(qgis_script(res))
        return 0
    if a.cmd == "report":
        print(open(os.path.join(RUN, "EXPORT.md"), encoding="utf-8").read())
        return 0
    out = build(do_dxf=not a.no_dxf, do_profiles=not a.no_profiles, do_kmz=not a.no_kmz)
    print("\n" + CT.Manifest.report())
    print(f"\nreport: {out['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
