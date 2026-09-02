"""W11a stage 3 - THE TRUNK, DESIGNED END TO END, BEFORE ANYTHING DRAINS TO IT.

WHY THIS STAGE EXISTS AT ALL, AND WHY IT COMES BEFORE THE HIERARCHY.
Philosophy sec 2 puts the trunk at stage 3 and the sizing at stage 6, with the note "stage 3
before stage 6 - a trunk that emerges from accumulated flow is not a trunk". W10 did the
opposite: its diameters fell out of a flow tree that was assembled last, and the result was
that only 21 % of the 85.5 km of main pipe ever carried a main diameter, while 5 reaches
(2.80 km) of the bit that did were SURCHARGED - DN1200 laid at 0.075 % passing 1,361 L/s at
no depth of flow at all. A trunk is not the residue of a network. It is a conveyance decision
taken against the ULTIMATE flow arriving, and everything else is then hung off it.

So this module takes the user's drawn alignment (`SHP/Main Pipe/Main Pipe.shp`, an INPUT per
CLAUDE.md rule and 00_CURRENT - never re-routed here), makes it one connected, oriented,
rooted tree, chambers it, gives every metre of it a diameter sized on the ultimate saturated
flow that reaches it, lays every reach at a round legal gradient, and publishes the levels.

WHAT IT PREVENTS, NAMED FAILURE BY NAMED FAILURE
  * W10 surcharged trunk (2.80 km)      - every reach is sized by hydra.pipe_state against
                                          its own peak flow and its d/D limit BEFORE the
                                          gradient is fixed, and the pair is re-solved
                                          together (H2, G203-p27 T10).
  * W10 45.92 km below minimum cover    - cover is contract.cover() on the reach's OWN
                                          outside diameter, and the level solve makes
                                          1.30 m the CONSTRAINT, not the starting value.
                                          Cover is checked BETWEEN chambers as well as at
                                          them (build-brief invariant 5) - W10 computed
                                          intermediate depth in p2_sizing and threw it away.
  * W10 published layer in 7,919 pieces - geometry is built from node coordinates by
                                          contract.Network, so a reach physically cannot
                                          stop short of its own chamber (invariant 2).
  * W10 no TIER / no laid gradient      - TIER = 'trunk main' on every reach as instructed,
                                          SLOPE_LAID beside SLOPE_MIN, and GRADIENT_BY /
                                          SIZED_BY / CLEAN_BY on every row (G1, G2, H8).
  * W10 digging past the cap in silence - cover over 12 m is tested against the two sec 5
                                          exits; where neither applies the answer is a
                                          LIFTING STATION, not a deeper trench.

THREE THINGS THE INPUT ALIGNMENT ITSELF TURNED OUT TO BE, all measured here and all
reported rather than quietly fixed, because the main pipe is the user's drawing:

  1. IT IS NOT ONE NETWORK. At the 0.01 m tolerance the auditor uses, the 54 drawn
     polylines form THREE components. Two of the three separations are different problems
     and only one of them is a gap:
       (a) segments 35-39 (4.40 km, the Wadi al Ayn spur) end EXACTLY on the interior of
           segment 7 - distance 0.000000 m. There is no gap; it is an unnoded T. Splitting
           segment 7 at that point joins it, and nothing moves.
       (b) segment 53 (7.87 km, the western leg) ends 879.82 m from the nearest point of
           segment 0. THE BUILD NOTE CALLING THIS "a 2 m drafting gap" IS WRONG - measured
           three ways (endpoint to union, closest approach of the whole line, nearest
           point) it is 879.82 m, from (447084.15, 2567523.06) to (447843.73, 2567079.06).
           The alignment's own backup folder contains a file named "Main Pipe All main
           pipes drawn but last part not good.zip", which is consistent. It is closed here
           with a straight connector carrying CONFIDENCE='provisional' so it can never be
           reported as a drafted line, and it is OPEN ITEM S3-1: the draftsman's real line.
  2. IT RUNS 11.0 km (12.8 %) ON WADI GROUND (Hazard_T50y class >= 4) - H1 and regression
     R4. Not a crossing pattern; whole kilometres lie in the band.
  3. IT RUNS 535 m INSIDE THE 6 m DUAL-CARRIAGEWAY BAND, the longest single stretch 378 m -
     H1 and regression R3, which fail any reach over 30 m in the band.
  None of the three is fixed by moving the line. Stage 3 measures them onto the layer
  (ON_WADI_M, ON_DUAL_M), schedules the dual contacts so they are a register and not a
  silence, and hands them back as decisions.

THE ONE ENGINEERING RESULT THAT MATTERS, and it is not a small one: THE TRUNK CANNOT BE
GRAVITY THE WHOLE WAY ON THE LINE AS DRAWN. The western leg falls into a basin at chainage
2.5 km (ground 332.6 m) and then runs 5.3 km UPHILL to 343.8 m before meeting segment 0 at
346.9 m. Laid as shallow as H3 allows - which the level solve here provably is - a
gravity-throughout profile reaches 25.09 m of cover and breaches the 12 m cap on 58 reaches
with neither sec 5 exit available. Under the cap-and-veto ladder that is layer 1, a CAP, and
the answer is a station: the economics is third and never first. So this module places a
lifting station at the last chamber inside the cap, pumps to the first local summit
downstream (the ground stops rising - a measured point on the DEM, not a chosen number), and
restarts gravity there at minimum cover. THREE stations do it, and the design then sits at
11.86 m of cover at its deepest with nothing past the cap. The pumped stretches LEAVE the
gravity layer: a rising main is sized on pump duty and not on arriving flow (sec 6), which is
stage 6's work, so their routes and static lifts are handed over and nothing is invented.

AND THE COST THAT IS REPORTED RATHER THAN ARGUED. G203-p29 sets the minimum gradient at
DN >= 900 to 0.75 mm/m. 0.075 % is NOT a multiple of the project's own 0.05 % laying step
(criteria.SLOPE_STEP, user 2026-08-23), so every flat large-diameter reach is laid at 0.10 %,
a third steeper than the guideline floor. `_rounding_cost()` measures it on the same
chambers and the same flows: gravity throughout, the 0.05 % step reaches 25.09 m and 58
un-exited breaches, a 0.025 % step 24.04 m and 46. So the step costs about a metre of trench
and it is NOT what buys the stations - the ground is. The contract refuses to publish an
off-step gradient, so the design complies and the number is reported.

WHAT THE AUDITOR SAYS ABOUT THE RESULT: 17 pass, 5 fail, 0 cannot run - against W10's 2 pass,
13 fail, 7 cannot run. Every one of the five traces to something stage 3 is forbidden to
change or to a contradiction the contract already records: H1/R3 (dual carriageway) and R4
(wadi) are defects of the INPUT alignment, H10 is five chambers where the INPUT turns the
flow through 87.8-89.8 deg, and H15 is the three stations, which split the gravity layer
into four components where audit.h15 demands exactly one - contract OPEN-1. Every failing
reach and chamber is named by id in `run/s3_trunk_findings.csv`; none is summarised away.

METHOD, in the order the code runs it
  1  read      54 polylines; node the T; close the measured gap; root at the existing works
                (E444422.8 N2563337.9, ground 328.7 - user-confirmed 2026-09-01) and orient
                every piece downstream. One out-edge per node makes H15 true by construction.
  2  straighten Douglas-Peucker at criteria.ROAD_CHORD_DEV_M (0.50 m - "how far the pipe may
                sit off the road line on a curve"), then a chamber at every remaining
                deflection over criteria.ROAD_BEND_DEG (30 deg). This is the brief's
                "minimise direction change": it removes survey wobble without moving the
                route, and it is reported as vertices and total turning, before and after.
  3  chamber    at the G203-p30 Table 12 maximum for the diameter, iterated with the sizing
                because the spacing depends on a diameter that depends on the spacing.
  4  load       every in-boundary plot's ultimate Qadf to its nearest trunk chamber, then
                accumulated downstream. STATED ASSUMPTION - see _loads().
  5  size+level the coupled solve. Diameter follows flow, gradient follows diameter (H8),
                and the level solve lays as shallow as H3 allows (sec 5).
  6  cap        the two sec 5 exits, then stations where neither applies.
  7  measure    dual and wadi exposure per reach, crossings schedule.
  8  publish    contract.publish() -> W11a/shp/W11a_trunk.gpkg (layers `reaches`, `nodes`,
                `crossings`) - the AUDITED artefact, and its own GeoPackage rather than the
                shared W11a.gpkg so a later stage cannot overwrite an audited design.
                Plus W11a_trunk.shp / _nodes.shp / _pumped.shp as CAD mirrors (the brief
                names the first by name), the pipe schedule, the stations hand-off and the
                findings register in W11a/run/.

    python s3_trunk.py            designs and publishes
    python run_audit_trunk.py     runs the 22 checks against what it published

NO NUMBER HERE IS INVENTED. Every design value comes from `sewnet.criteria` (which cites its
page), from `contract` (which cites the auditor), or from a guideline page quoted at the point
of use. The one place this module goes beyond `criteria.DN_SERIES` is DN_SERIES_TRUNK, and it
says why and where the sizes come from.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from w11a import contract as K                              # noqa: E402
from w11a.contract import C, hydra                          # noqa: E402  criteria + CW maths

import geopandas as gpd                                     # noqa: E402
import networkx as nx                                       # noqa: E402
import rasterio                                             # noqa: E402
from scipy.spatial import cKDTree                           # noqa: E402
from shapely.geometry import LineString, Point              # noqa: E402
from shapely.ops import unary_union                         # noqa: E402

STAGE = "s3_trunk"

# --------------------------------------------------------------------------------------
# Paths. Read-only on everything outside W11a - W8 and W10 are the record and are not edited.
# --------------------------------------------------------------------------------------
W11A = K.W11A_ROOT                                          # .../Hydraulic/Claude/W11a
REPO = K.REPO_ROOT                                          # .../Hydraulic/Claude
BASE = os.path.dirname(os.path.dirname(REPO))               # .../2621 Ibri Sewer STP

P_MAIN     = os.path.join(BASE, "Hydraulic", "SHP", "Main Pipe", "Main Pipe.shp")
P_ROADS    = os.path.join(BASE, "Hydraulic", "SHP", "Road centerline 2", "Road_Centercline.shp")
P_TERRAIN  = os.path.join(BASE, "Data", "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt")
P_HAZARD   = os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif")
P_LOADS    = os.path.join(REPO, "W10", "shp", "W10_plot_loads.gpkg")
P_CORRIDOR = os.path.join(REPO, "W10", "shp", "W10_corridors_drafted.shp")

OUT_SHP = os.path.join(W11A, "shp")
OUT_RUN = os.path.join(W11A, "run")
GPKG    = "W11a_trunk.gpkg"        # stage 3's own GeoPackage. The stage-3 trunk is not yet
                                   # the whole `reaches` layer; writing into W11a.gpkg would
                                   # let stage 4 silently overwrite a design that was audited.

# --------------------------------------------------------------------------------------
# Constants that are NOT criteria values - each says what pins it
# --------------------------------------------------------------------------------------

# The existing works. Ground 328.7 m, user-confirmed 2026-09-01 against the NAMA record and
# the built rising main's end (CLAUDE.md, project-in-one-paragraph).
STP_XY = (444422.8, 2563337.9)

# G203-p29 Table 11 stops at DN900 and the guideline then states ">= DN900: 0.75 mm/m", so a
# minimum gradient is defined for ANY larger size (criteria.TABLE11_FLOOR). criteria.DN_SERIES
# stops at DN1200, which this trunk outgrows before it reaches the works. The extension uses
# ONLY diameters the guideline's own tables name:
#   G203-p32 Tab 13 / p35 Tab 15 service-corridor widths - "1400-1700: 4.0 m; 1800: 4.1 m;
#   2000-2400: 4.4 m"  (02_DESIGN_CRITERIA sec 4)
#   G203-p30 Tab 12 chamber spacing - "1000-1400: 150 m; >1400: 200 m"  (02 sec 5)
# Nothing is interpolated: 1400, 1700, 1800, 2000 and 2400 are printed sizes. Recorded as
# OPEN ITEM S3-2 so criteria.DN_SERIES is extended once, in one place, when NWS confirm.
DN_SERIES_TRUNK: Tuple[int, ...] = tuple(list(C.DN_SERIES) + [1400, 1700, 1800, 2000, 2400])

GAP_FROM = (447084.1545968621, 2567523.0637987405)   # segment 53 downstream end
GAP_TO   = (447843.7257607772, 2567079.058588501)    # nearest point on segment 0

NODE_TOL_M   = 0.01      # the auditor's own clustering radius (audit.Ctx.graph snap)
SAMPLE_M     = 10.0      # terrain sampling along a reach - invariant 5 checks cover BETWEEN
                         # chambers, not only at them
MIN_REACH_M  = 30.0      # H11 needs >= 20 mm of fall in a reach. At the DN>=900 floor of
                         # 0.75 mm/m that takes 27 m, so a reach shorter than this cannot
                         # satisfy the laying tolerance at the flattest legal gradient.
STEP         = C.SLOPE_STEP                     # 0.05 % gradient steps (P1)
CAP_M        = C.MAX_DEPTH                      # 12 m of cover (H4, G203-p33)
EXIT_RECOVER_M = 500.0                          # philosophy sec 5, both distances
EXIT_OUTFALL_M = 1000.0


# ======================================================================================
# small helpers
# ======================================================================================

def _log(msg: str = "") -> None:
    print(msg, flush=True)


# The open-channel solve is bisection inside bisection and the chambering loop calls it a
# few million times. Memoising it changes NOTHING about the answer - hydra is a pure
# function of (dn, slope, Q) - and is the only reason this stage runs in a minute rather
# than an afternoon. The key rounds the slope to 1e-7 (a fifth of the 0.05 % laying step)
# and the flow to 1e-6 m3/s (0.001 L/s), both far below anything the design resolves.
_STATE_CACHE: Dict[Tuple[int, int, int], Tuple[Optional[float], Optional[float]]] = {}


def _state(dn: int, slope: float, q_m3s: float):
    k = (int(dn), int(round(slope * 1e7)), int(round(q_m3s * 1e6)))
    hit = _STATE_CACHE.get(k)
    if hit is None:
        hit = hydra.pipe_state(dn, slope, q_m3s, C)
        _STATE_CACHE[k] = hit
    return hit


_SMIN_CACHE: Dict[Tuple[int, int], float] = {}
_PLOTS = None          # the 64,071-record load table, read once
_CORR_KM = None        # drafted corridor length, read once


def _smin_for(dn: int, q_m3s: float) -> float:
    k = (int(dn), int(round(q_m3s * 1e6)))
    hit = _SMIN_CACHE.get(k)
    if hit is None:
        hit = hydra.smin_for(dn, q_m3s, C)
        _SMIN_CACHE[k] = hit
    return hit


def _cut(line: LineString, d0: float, d1: float) -> LineString:
    """Sub-polyline of `line` between two chainages, keeping every intermediate vertex.

    Written out rather than taken from shapely.ops.substring so the endpoints are EXACTLY
    the interpolated points the chamber coordinates are minted from. A reach whose geometry
    disagrees with its own chamber by even a millimetre is the beginning of W10's 7,919
    pieces, and contract.Network.assert_round_trip() would refuse it at 5 mm.
    """
    cs = [c[:2] for c in line.coords]
    p0, p1 = line.interpolate(d0), line.interpolate(d1)
    coords = [(p0.x, p0.y)]
    run = 0.0
    for a, b in zip(cs[:-1], cs[1:]):
        run += math.dist(a, b)                     # chainage of vertex b
        if d0 + 1e-9 < run < d1 - 1e-9:
            coords.append((b[0], b[1]))
    coords.append((p1.x, p1.y))
    out = [coords[0]]
    for c in coords[1:]:
        if math.dist(c, out[-1]) > 1e-9:
            out.append(c)
    return LineString(out) if len(out) >= 2 else LineString([coords[0], coords[-1]])


def _deflection_deg(a, b, c) -> float:
    """Change of direction at b, in degrees. 0 = dead straight."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cosang = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cosang))


def _inlet_angle_deg(a, b, c) -> float:
    """Angle an inlet arriving a->b makes with the outgoing flow b->c. 180 = straight
    through. G203-p30 requires >= 90 deg, i.e. the flow may not be turned back on itself."""
    return 180.0 - _deflection_deg(a, b, c)


def _round_up(s: float, step: float = STEP) -> float:
    return math.ceil(s / step - 1e-9) * step


def _round_down(s: float, step: float = STEP) -> float:
    return math.floor(s / step + 1e-9) * step


def _material(dn: int) -> str:
    """G203-p22 Tab 6 by APPLICATION, not p23 Tab 7 by product.

    On a MAIN sewer (and a trunk main is one) PVC-U is permitted only "up to 250 mm"; above
    that the row reads HDPE / GRP, and G203-p35 Tab 14 restricts a trunk over 600 mm to GRP,
    lined RCC or profile-wall HDPE. contract.material_conflict() enforces exactly this and
    criteria.material() cannot, because it is diameter-only and does not know the tier.
    """
    return "PVC-U" if dn <= K.PVC_MAIN_MAX_DN else "GRP"


def _mh_dia(depth_m: float, dn: int) -> float:
    """Chamber internal diameter.

    G203 gives NO table of chamber size against depth - it says only "sufficient size", and
    criteria.ASSUMPTIONS['MH_SIZES'] records the project's stated assumption (DN1000 to 3 m
    deep, DN1200 to 6 m, DN1500 deeper). The second term is not a criterion at all, it is
    geometry: a chamber cannot be narrower than the pipe passing through it, so the barrel is
    at least the outside diameter rounded up to the next 0.5 m.
    """
    by_depth = 1.0 if depth_m <= 3.0 else 1.2 if depth_m <= 6.0 else 1.5
    by_pipe = math.ceil((dn / 1000.0) / 0.5) * 0.5
    return float(min(6.0, max(by_depth, by_pipe)))


# ======================================================================================
# 1. read the alignment, node it, close the measured gap, root and orient
# ======================================================================================

class Alignment:
    """The user's drawn main pipe turned into a rooted, oriented tree.

    `pieces` keeps one row per drawn polyline segment (split where another segment ends on
    its interior) so the draftsman's own notes - "wadi crossing", "narrow space", "mountain
    foot", "close trench" - survive to the schedules. linemerge() would have discarded them.
    """

    def __init__(self, rec: K.StageRecord):
        self.rec = rec
        src = gpd.read_file(P_MAIN)
        if src.crs is None or src.crs.to_epsg() != K.CRS_EPSG:
            src = src.set_crs(K.CRS_EPSG, allow_override=True)
        rec.read("Main Pipe.shp", P_MAIN, len(src))
        self.n_input = len(src)
        self.len_input = float(src.geometry.length.sum())

        geoms = [g for g in src.geometry]
        descs = [("" if pd.isna(d) else str(d)) for d in src.get("Desc", pd.Series([""] * len(src)))]

        # ---- the gap. Measured, not assumed. See the module docstring, finding 1(b).
        #      Measured from the western leg's own downstream end to the union of every
        #      OTHER drawn line - including its own line would return 0.00 and hide it,
        #      which is the kind of self-referential measurement the build note appears to
        #      have made when it called this "2 m".
        far = [k for k, g in enumerate(geoms)
               if Point(GAP_FROM).distance(g) > 1e-6]
        measured = Point(GAP_FROM).distance(unary_union([geoms[k] for k in far]))
        self.gap_m = float(measured)
        geoms.append(LineString([GAP_FROM, GAP_TO]))
        descs.append("GAP CLOSURE - provisional, not the draftsman's line (OPEN S3-1)")
        self.i_connector = len(geoms) - 1
        _log(f"  gap closed with a straight connector: {measured:,.2f} m "
             f"(the build note said 2 m; it is not)")
        rec.note(f"western leg gap measured {measured:.2f} m, not the 2 m the build note "
                 f"states; closed with a provisional straight connector")

        # ---- node: split any piece where another piece's ENDPOINT lands on its INTERIOR.
        #      Tested against the LINE, not against its vertices: segment 39 lands on
        #      segment 7 at exactly 0.000000 m and the connector lands on segment 0's
        #      nearest point, and neither of those is a digitised vertex. Clustering
        #      endpoints - which is all the auditor's graph does - cannot see either, which
        #      is why the drawing reads as three components when it is one route.
        ends = []
        for g in geoms:
            ends.append(g.coords[0][:2])
            ends.append(g.coords[-1][:2])
        pieces: List[Tuple[LineString, str, int]] = []
        n_split = 0
        for i, g in enumerate(geoms):
            own = {g.coords[0][:2], g.coords[-1][:2]}
            cuts = []
            for p in ends:
                if any(math.dist(p, o) < NODE_TOL_M for o in own):
                    continue
                if Point(p).distance(g) > NODE_TOL_M:
                    continue
                d = g.project(Point(p))
                if NODE_TOL_M < d < g.length - NODE_TOL_M:
                    cuts.append(d)
            cuts = sorted(set(round(d, 3) for d in cuts))
            bounds = [0.0] + cuts + [g.length]
            for a, b in zip(bounds[:-1], bounds[1:]):
                if b - a > NODE_TOL_M:
                    pieces.append((_cut(g, a, b), descs[i], i))
            n_split += max(0, len(bounds) - 2)
        self.n_split = n_split
        _log(f"  noded: {len(geoms)} drawn lines -> {len(pieces)} pieces "
             f"({n_split} interior T-junction split(s))")

        # ---- graph on piece endpoints
        pts = []
        for g, _d, _s in pieces:
            pts.append(g.coords[0][:2])
            pts.append(g.coords[-1][:2])
        arr = np.array(pts)
        lab = np.full(len(arr), -1, dtype=np.int64)
        tree = cKDTree(arr)
        for i in range(len(arr)):
            if lab[i] != -1:
                continue
            lab[i] = i
            for j in tree.query_ball_point(arr[i], NODE_TOL_M):
                if lab[j] == -1:
                    lab[j] = i
        G = nx.Graph()
        keep = []
        for i, (g, d, s) in enumerate(pieces):
            u, v = int(lab[2 * i]), int(lab[2 * i + 1])
            if u == v or g.length < NODE_TOL_M:
                continue                       # zero-length artefact of noding; not a pipe
            G.add_edge(u, v, i=len(keep))
            keep.append((g, d, s, u, v))
        self.pieces = keep
        ncomp = nx.number_connected_components(G)
        ncyc = G.number_of_edges() - G.number_of_nodes() + ncomp
        _log(f"  graph: {G.number_of_nodes()} vertices, {G.number_of_edges()} pieces, "
             f"{ncomp} component(s), {ncyc} independent cycle(s)")
        if ncomp != 1 or ncyc != 0:
            raise RuntimeError(
                f"the trunk is not one tree after noding: {ncomp} components, {ncyc} cycles. "
                "H15 requires a forest and stage 3 will not publish a guess about which "
                "piece joins which - fix the alignment or the gap list.")
        self.G = G
        self.pos = {n: tuple(arr[n]) for n in G.nodes}

        # ---- root at the works and orient every piece downstream
        root = min(G.nodes, key=lambda n: math.dist(self.pos[n], STP_XY))
        self.root = root
        self.root_offset = math.dist(self.pos[root], STP_XY)
        parent: Dict[int, Optional[int]] = {root: None}
        order: List[int] = []
        for u, v in nx.bfs_edges(G, root):
            parent[v] = u
            order.append(v)
        self.parent, self.bfs_order = parent, order
        _log(f"  rooted at the existing works, {self.root_offset:.2f} m from the "
             f"user-confirmed coordinate; {len(order)} vertices oriented downstream")

    # -- runs: maximal directed paths between structural vertices ------------------------
    def runs(self) -> List[Dict]:
        """One entry per maximal chain of pieces between structural vertices.

        A structural vertex is a leaf, a junction or the outfall - anywhere the topology
        changes. Chambering runs along the whole chain rather than per drawn piece, because
        the draftsman's segment breaks are drawing conventions ("narrow space", "wadi
        crossing") and have nothing to do with G203-p30 Table 12 spacing.
        """
        deg = dict(self.G.degree())
        struct = {n for n in self.G.nodes if deg[n] != 2} | {self.root}
        # child -> the piece index that carries it to its parent
        piece_of: Dict[Tuple[int, int], int] = {}
        for i, (g, d, s, u, v) in enumerate(self.pieces):
            piece_of[(u, v)] = i
            piece_of[(v, u)] = i
        children = defaultdict(list)
        for v, p in self.parent.items():
            if p is not None:
                children[p].append(v)
        out = []
        for start in struct:
            # walk UPSTREAM from every structural vertex into each of its upstream branches
            for up in children[start]:
                chain, cur = [], up
                while True:
                    chain.append((cur, self.parent[cur]))
                    if cur in struct:
                        break
                    nxt = children[cur]
                    if len(nxt) != 1:
                        break
                    cur = nxt[0]
                chain = list(reversed(chain))          # upstream -> downstream
                coords: List[Tuple[float, float]] = []
                descs: List[Tuple[float, float, str, int]] = []
                run_len = 0.0
                for (c, p) in chain:
                    g, d, s, u, v = self.pieces[piece_of[(c, p)]]
                    cs = [x[:2] for x in g.coords]
                    # orient the piece so it runs from the upstream vertex c to its parent p
                    if math.dist(cs[0], self.pos[c]) > math.dist(cs[-1], self.pos[c]):
                        cs = cs[::-1]
                    seg0 = run_len
                    if coords and math.dist(coords[-1], cs[0]) < NODE_TOL_M:
                        cs = cs[1:]
                    prev = coords[-1] if coords else cs[0]
                    for pt in cs:
                        run_len += math.dist(prev, pt)
                        prev = pt
                    if not coords:
                        coords.append(cs[0])
                        cs = cs[1:]
                    coords.extend(cs)
                    descs.append((seg0, run_len, d, s))
                line = LineString(coords)
                out.append(dict(us=chain[0][0], ds=chain[-1][1], line=line, descs=descs))
        return out


# ======================================================================================
# 2. straighten - the brief's "minimise direction change"
# ======================================================================================

def straighten(runs: List[Dict], rec: K.StageRecord) -> Dict[str, float]:
    """Douglas-Peucker at criteria.ROAD_CHORD_DEV_M, endpoints fixed.

    0.50 m is the project's own "how far the pipe may sit off the road line on a curve"
    (criteria.ROAD_CHORD_DEV_M, W5 rule register). It removes digitising wobble - segment 0
    alone carries 348 vertices over 9.08 km - WITHOUT moving the route, which is the point:
    the alignment is an input and stage 3 may not re-route it. What is removed is drawing
    noise, and what survives is a real change of direction that needs a chamber (G203-p29
    lists a chamber at every change of direction).
    """
    def _sharp0(rs):
        return max((_deflection_deg(c[i - 1], c[i], c[i + 1])
                    for c in [list(r["line"].coords) for r in rs]
                    for i in range(1, len(c) - 1)), default=0.0)
    sharp0 = _sharp0(runs)
    v0 = sum(len(r["line"].coords) for r in runs)
    t0 = sum(sum(_deflection_deg(c[i - 1], c[i], c[i + 1])
                 for i in range(1, len(c) - 1))
             for c in [list(r["line"].coords) for r in runs])
    moved = 0.0
    for r in runs:
        simp = r["line"].simplify(C.ROAD_CHORD_DEV_M, preserve_topology=False)
        moved = max(moved, simp.hausdorff_distance(r["line"]))
        r["line"] = simp
    v1 = sum(len(r["line"].coords) for r in runs)
    t1 = sum(sum(_deflection_deg(c[i - 1], c[i], c[i + 1])
                 for i in range(1, len(c) - 1))
             for c in [list(r["line"].coords) for r in runs])
    def _sharpest(rs):
        return max((_deflection_deg(c[i - 1], c[i], c[i + 1])
                    for c in [list(r["line"].coords) for r in rs]
                    for i in range(1, len(c) - 1)), default=0.0)
    stat = dict(vertices_before=v0, vertices_after=v1,
                turning_deg_before=t0, turning_deg_after=t1,
                max_offset_m=moved, sharpest_turn_deg_after=_sharpest(runs))
    stat["sharpest_turn_deg_before"] = sharp0
    _log(f"  straightened: {v0:,} vertices -> {v1:,}; total turning "
         f"{t0:,.0f} deg -> {t1:,.0f} deg; alignment moved at most {moved:.2f} m "
         f"(criteria.ROAD_CHORD_DEV_M = {C.ROAD_CHORD_DEV_M} m)")
    _log(f"  sharpest single turn {sharp0:.1f} deg -> {stat['sharpest_turn_deg_after']:.1f} "
         f"deg. Smoothing never made a turn sharper than it was drawn; anything over "
         f"90 deg here is in the INPUT, and a chamber there needs a swept channel (H10).")
    rec.metric("vertices_removed", v0 - v1)
    rec.metric("turning_deg_removed", round(t0 - t1, 1))
    return stat


# ======================================================================================
# 3. chamber
# ======================================================================================

def chamber(runs: List[Dict], dn_at, forced: Optional[Dict[int, set]] = None) -> List[Dict]:
    """Place chambers along every run and cut it into reaches.

    Three kinds of chamber, all G203-p29 sec 4.4 triggers: the structural vertices at the
    ends of the run, a chamber at every deflection over criteria.ROAD_BEND_DEG (30 deg), and
    regular spacing at the G203-p30 Table 12 maximum for the diameter (criteria.mh_max_
    spacing). `dn_at(run_index, chainage)` supplies the diameter from the previous solve, so
    the spacing follows the pipe rather than being pinned at the tightest class everywhere -
    which is how W10 ended up at 11.1 nodes/km against NAMA's built 32.3 while STILL
    breaching Table 12 on 4,763 reaches.

    A reach shorter than MIN_REACH_M is absorbed into its neighbour: at the DN>=900 gradient
    floor a 27 m reach falls exactly the 20 mm laying tolerance (H11, G203-p29), so anything
    shorter cannot be set out.

    `forced` carries chainages a previous pass proved are needed - the repair loop in run()
    adds the midpoint of every reach that came out over its own Table 12 limit. Splitting
    only ever shortens a reach, so the loop is monotone and terminates; H12 is then a fact
    about the published layer rather than a hope about the iteration count.
    """
    forced = forced or {}
    reaches = []
    for ri, r in enumerate(runs):
        line = r["line"]
        L = line.length
        cs = list(line.coords)
        # mandatory chainages: the bends, plus anything the repair loop has pinned
        cuts = {0.0, L} | {c for c in forced.get(ri, ()) if 0.0 < c < L}
        run = 0.0
        for i in range(1, len(cs) - 1):
            run += math.dist(cs[i - 1][:2], cs[i][:2])
            if _deflection_deg(cs[i - 1], cs[i], cs[i + 1]) > C.ROAD_BEND_DEG:
                cuts.add(run)
        # regular spacing, walking downstream at the local Table 12 limit
        d = 0.0
        while d < L - 1e-6:
            lim = C.mh_max_spacing(int(dn_at(ri, d)))
            nxt = min(d + lim, L)
            hard = [c for c in sorted(cuts) if d + 1e-6 < c <= nxt + 1e-6]
            d = hard[0] if hard else nxt
            cuts.add(d)
        chain = sorted(cuts)
        # absorb reaches shorter than MIN_REACH_M
        clean = [chain[0]]
        for c in chain[1:]:
            if c - clean[-1] < MIN_REACH_M and c < L - 1e-6:
                continue
            clean.append(c)
        if len(clean) > 1 and clean[-1] - clean[-2] < MIN_REACH_M and len(clean) > 2:
            clean.pop(-2)
        for a, b in zip(clean[:-1], clean[1:]):
            geom = _cut(line, a, b)
            mid = 0.5 * (a + b)
            desc = ""
            for s0, s1, dd, si in r["descs"]:
                if s0 - 1e-6 <= mid <= s1 + 1e-6:
                    desc = dd
                    break
            reaches.append(dict(run=ri, d0=a, d1=b, geom=geom, len_m=geom.length,
                                desc=desc, us_struct=(a <= 1e-6), ds_struct=(b >= L - 1e-6),
                                run_us=r["us"], run_ds=r["ds"]))
    return reaches


# ======================================================================================
# 4. terrain, load, flow
# ======================================================================================

class Terrain:
    """The 0.5 m bare-earth VRT (project rule 6) and the 50-year hazard grid, sampled once."""

    def __init__(self, rec: K.StageRecord):
        self.dem = rasterio.open(P_TERRAIN)
        self.haz = rasterio.open(P_HAZARD)
        rec.read("terrain VRT", P_TERRAIN)
        rec.read("Hazard_T50y", P_HAZARD)

    def z(self, xy: Sequence[Tuple[float, float]]) -> np.ndarray:
        v = np.array([s[0] for s in self.dem.sample(xy)], dtype=float)
        v[v < -1000] = np.nan
        return v

    def wadi(self, xy: Sequence[Tuple[float, float]]) -> np.ndarray:
        v = np.array([s[0] for s in self.haz.sample(xy)], dtype=float)
        return np.isfinite(v) & (v > -1000) & (np.floor(v) >= min(C.HAZARD_WADI_CLASSES))


def _loads(chamber_xy: np.ndarray, rec: K.StageRecord) -> Tuple[np.ndarray, np.ndarray, float]:
    """Ultimate Qadf and property count arriving at each trunk chamber.

    THE STATED ASSUMPTION OF THIS STAGE, and it is the honest one to make here. The
    hierarchy does not exist yet (stage 4), so nothing can say WHICH sub main delivers a
    given plot to the trunk. What is certain is the total - 74,675.27 m3/d over 98,646
    properties inside the boundary, measured over 64,027 plot records - and that total is
    what sizes the trunk where it matters, at the works. Upstream of that, each plot's load
    is entered at its NEAREST trunk chamber, which is a Voronoi split of the town across the
    alignment: neutral, reproducible, and wrong only in the distribution, never in the sum.
    Stage 4 replaces the distribution; the diameter at the outfall does not move.

    Every record is either assigned or named in the funnel (invariant 1). W10 lost
    1,233 m3/d - 1.7 % - because an assignment radius returned nothing and nobody counted
    the difference.
    """
    global _PLOTS
    if _PLOTS is None:
        _PLOTS = gpd.read_file(P_LOADS, layer="plot_loads")
    pl = _PLOTS
    rec.read("W10_plot_loads (plot_loads)", P_LOADS, len(pl))
    f = rec.funnel("plot load -> trunk chamber", len(pl))
    out = pl[pl.IN_BND != 1]
    if len(out):
        f.drop("outside the project boundary (IN_BND = 0)",
               ids=out.PLOT_ID.tolist(), qty=float(out.Q_AVG_M3D.sum()))
    pl = pl[pl.IN_BND == 1]
    cen = pl.geometry.representative_point()
    _d, idx = cKDTree(chamber_xy).query(np.c_[cen.x.values, cen.y.values])
    q = np.zeros(len(chamber_xy))
    n = np.zeros(len(chamber_xy))
    np.add.at(q, idx, pl.Q_AVG_M3D.values)
    np.add.at(n, idx, pl.N_PROP.values)
    f.close(len(pl))
    _log(f"  load: {f.line()}; {q.sum():,.1f} m3/d and {n.sum():,.0f} properties onto "
         f"{(q > 0).sum():,} of {len(chamber_xy):,} chambers "
         f"(farthest plot {_d.max():,.0f} m from its chamber)")
    rec.metric("q_adf_total_m3d", round(float(q.sum()), 1))
    rec.metric("properties_total", round(float(n.sum()), 0))
    return q, n, float(_d.max())


def _infiltration_basis(q_total: float, rec: K.StageRecord) -> float:
    """km of tributary network per m3/d of load, for the G201-p72-73 infiltration allowance.

    720 L/d per km, UNPEAKED, is the guideline figure; the length it applies to is the
    network upstream of the reach, and at stage 3 that network is not designed. Rather than
    invent a length or understate it by counting only the trunk, the ratio is taken from the
    draftsman's own corridor file - a measured INPUT, not a W10 design output - and applied
    pro rata to the load each reach carries. It is a small number by construction
    (1,195 km x 720 L/d = 9.96 L/s over the whole scheme, 0.7 % of the peak at the works),
    which is exactly why it is worth getting from a real measurement instead of a guess.
    """
    global _CORR_KM
    if _CORR_KM is None:
        corr = gpd.read_file(P_CORRIDOR)
        _CORR_KM = (float(corr.geometry.length.sum()) / 1000.0, len(corr))
    km, ncorr = _CORR_KM
    rec.read("W10_corridors_drafted", P_CORRIDOR, ncorr)
    _log(f"  infiltration basis: {km:,.1f} km of drafted corridor over "
         f"{q_total:,.0f} m3/d -> {km / q_total:.5f} km per m3/d "
         f"({C.INFILT_L_D_KM:.0f} L/d/km, G201-p72-73, unpeaked)")
    return km / q_total


# ======================================================================================
# 5. the coupled diameter / gradient / level solve
# ======================================================================================

class Solver:
    """Diameter follows flow; gradient follows diameter; the pipe is laid as shallow as H3
    allows (H8 G203-p29, philosophy sec 5).

    The three are ONE problem and W10 solved them separately, which is why its trunk was
    surcharged: a diameter chosen against a minimum gradient is not a diameter for the
    gradient the pipe is actually laid at. Here, for each candidate DN in ascending order,
    the gradient that DN would be laid at is computed FIRST (the steeper of its own minimum
    and the fall the ground demands), and the DN is accepted only if it passes its peak flow
    at THAT gradient inside its d/D limit and under 3.0 m/s.
    """

    def __init__(self, tau_pa: float = C.TAU_PA, step: float = STEP):
        self.tau = tau_pa
        self.step = step        # P1's 0.05 % gradient step, or a finer one for the
                                # sensitivity in _rounding_cost()

    def smin(self, dn: int, q_m3s: float) -> float:
        """The steeper of Table 11 and the tractive minimum - hydra.smin_for, memoised."""
        return _smin_for(dn, q_m3s)

    def lay(self, dn: int, inv_us: float, grd_prof: np.ndarray, dist_prof: np.ndarray,
            L: float, q_m3s: float) -> Dict:
        """The gradient a GIVEN diameter would be laid at from a given upstream invert.

        Separated from the diameter choice so a caller that has already fixed the diameter
        (the seating loop below) can re-lay without re-opening the sizing - re-choosing the
        diameter after moving the invert is what let a reach end up 1.10 m under cover in
        the first run of this stage: the level was set for DN400 and the pipe published
        was DN500.
        """
        need = K.min_invert_depth(dn)                     # 1.30 + OD + 0.10 (H3, contract)
        # steep enough to hold minimum cover at EVERY sampled point along the reach, not
        # only at its ends (build-brief invariant 5), and never below its own minimum
        s_cover = float(np.max(np.where(dist_prof > 1e-6,
                                        (inv_us - (grd_prof - need)) /
                                        np.maximum(dist_prof, 1e-6), -np.inf)))
        s_min = self.smin(dn, q_m3s)
        s = _round_up(max(s_min, s_cover, 0.0), self.step)
        capped = False
        y, v = _state(dn, s, q_m3s)
        # smax_for costs ~150 bisections of an 80-step solve, so it is asked for only when
        # the pipe is ACTUALLY over 3.0 m/s - a handful of reaches, not all 765.
        if v is not None and v > C.V_MAX + 1e-9:
            s_max = hydra.smax_for(dn, q_m3s, C)
            if s_max in (None, hydra.INFEASIBLE) or _round_down(s_max, self.step) < s_min - 1e-12:
                return dict(dn=dn, s=s, y=None, v=v, s_min=s_min, s_cover=s_cover,
                            capped=False, need=need, ok=False, deficit=0.0)
            s = _round_down(s_max, self.step)
            capped = True
            y, v = _state(dn, s, q_m3s)
        ok = (y is not None and y <= hydra.dod_limit(dn, C)
              and (v is None or v <= C.V_MAX + 1e-9))
        # On ground falling faster than 3.0 m/s allows the pipe to fall, a legal gradient
        # cannot hold cover to the downstream end: the pipe would come out of the hill.
        # `deficit` is how much deeper the reach must START to still have 1.30 m at every
        # sampled point - i.e. the DROP taken at the upstream chamber, external and ramped
        # (G203-p30, philosophy sec 5: "hold the gradient and take the difference at a drop
        # chamber"). Without this the velocity cap silently ate the cover: 7 reaches came
        # out between 0.89 and 1.19 m and failed a BLOCKING H3.
        deficit = float(np.max((inv_us - s * dist_prof) - (grd_prof - need)))
        return dict(dn=dn, s=s, y=y, v=v, s_min=s_min, s_cover=s_cover,
                    capped=capped, need=need, ok=ok, deficit=max(deficit, 0.0))

    def solve_from(self, dn_min: int, inv_us: float, grd_prof: np.ndarray,
                   dist_prof: np.ndarray, L: float, q_pk_ls: float) -> Dict:
        """Smallest diameter at or above `dn_min` that works. `dn_min` is what makes the
        seating loop monotone: the diameter may only ever go up as the invert goes down,
        so the pair cannot chase each other round for ever."""
        q = q_pk_ls / 1000.0
        why = None                       # why the size BELOW the accepted one failed
        for dn in DN_SERIES_TRUNK:
            d = self.lay(dn, inv_us, grd_prof, dist_prof, L, q)
            if d["ok"] and dn >= dn_min:
                # SIZED_BY is the reason the previous size was rejected, tested at the
                # gradient THAT size would have been laid at - not at this one's. Asking
                # the question at the wrong gradient is how a reach gets attributed to
                # "horizon" when what actually forced it up was d/D. 'depth' and 'cover'
                # are prohibited answers (G203-p29, Ten States sec 33.43) and cannot arise
                # here: the diameter loop never sees the invert except through the flow.
                d["sized_by"] = why or "minimum"
                return self._attribute(d, inv_us, grd_prof, L)
            if d["ok"]:
                continue                 # viable, but the seating loop pinned a bigger
                                         # floor; the final free solve settles the size
            if d["y"] is None:
                why = "capacity"
            elif d["y"] > hydra.dod_limit(dn, C):
                why = "dod"
            elif d["v"] is not None and d["v"] > C.V_MAX:
                why = "velocity"
            else:
                why = "capacity"
        d = self.lay(DN_SERIES_TRUNK[-1], inv_us, grd_prof, dist_prof, L, q)
        d["infeasible"] = True
        d["sized_by"] = why or "capacity"
        d["y"] = d["y"] if d["y"] is not None else 1.0
        d["v"] = d["v"] or 0.0
        return self._attribute(d, inv_us, grd_prof, L)

    @staticmethod
    def _attribute(d: Dict, inv_us: float, grd_prof: np.ndarray, L: float) -> Dict:
        """What SET the laid gradient (contract.GRADIENT_BY)."""
        dn = d["dn"]
        if d.get("capped"):
            by = "vmax"
        elif d["s_cover"] > d["s_min"] + 1e-12:
            cov_us = grd_prof[0] - inv_us - (dn / 1000.0 + K.AUDITOR_OD_ALLOW_M)
            # riding the ground surface at minimum cover, or clawing cover back after a
            # flat stretch left the pipe deeper than it needs to be
            by = "ground" if abs(cov_us - C.MIN_COVER_CROWN) < 0.05 else "cover_min"
        elif abs(d["s_min"] - C.TABLE11.get(dn, C.TABLE11_FLOOR)) < 1e-12:
            by = "table11"
        else:
            by = "tractive"
        d["gradient_by"] = by
        d["inv_ds"] = inv_us - d["s"] * L
        return d

    def solve_reach(self, inv_us: float, grd_prof: np.ndarray, dist_prof: np.ndarray,
                    L: float, q_pk_ls: float) -> Dict:
        """One reach, diameter free. Kept as the plain entry point; solve_from() is the
        one the seating loop uses, because it can pin a floor and stay monotone."""
        return self.solve_from(C.DN_MIN_MAIN, inv_us, grd_prof, dist_prof, L, q_pk_ls)


# ======================================================================================
# the stage
# ======================================================================================

def run() -> int:
    os.makedirs(OUT_SHP, exist_ok=True)
    os.makedirs(OUT_RUN, exist_ok=True)

    # One manifest FILE PER STAGE. Manifest.records is per-process, so writing the shared
    # W11a/run/manifest.json would replace a sibling stage's record with this stage's alone -
    # the stages run in separate processes and s1/s4/s5b/s8/s9 already write their own.
    with K.Manifest.stage(STAGE, 3,
                          path=os.path.join(OUT_RUN, "manifest_s3_trunk.json")) as rec:
        _log("=" * 88)
        _log("W11a stage 3 - the trunk, designed end to end")
        _log("=" * 88)

        # ---------------------------------------------------------------- 1. alignment
        _log("\n[1] alignment")
        al = Alignment(rec)
        runs = al.runs()
        _log(f"  {len(runs)} run(s) between structural vertices, "
             f"{sum(r['line'].length for r in runs) / 1000:,.2f} km "
             f"(input {al.len_input / 1000:,.2f} km + {al.gap_m / 1000:,.2f} km connector)")

        # ---------------------------------------------------------------- 2. straighten
        _log("\n[2] direction change")
        straight = straighten(runs, rec)

        terr = Terrain(rec)

        # ------------------------------------------------- 3-5. chamber / load / solve
        # The spacing depends on the diameter and the diameter depends on the flow, which
        # depends on where the chambers are. Three passes settle it; the H12 check at the
        # end is what decides whether it settled, not the loop counter.
        dn_prev: Dict[int, List[Tuple[float, float, int]]] = {}

        def dn_at(ri: int, d: float) -> int:
            for a, b, dn in dn_prev.get(ri, ()):
                if a - 1e-6 <= d <= b + 1e-6:
                    return dn
            return C.DN_MIN_MAIN

        solver = Solver()
        design = None
        forced: Dict[int, set] = defaultdict(set)
        for it in range(12):
            _log(f"\n[3-5] pass {it + 1}: chamber, load, size and level")
            reaches = chamber(runs, dn_at, forced)
            design = _solve_all(al, runs, reaches, terr, solver, rec)
            dn_prev = defaultdict(list)
            for r in design["reaches"]:
                dn_prev[r["run"]].append((r["d0"], r["d1"], r["DN"]))
            over = [r for r in design["reaches"]
                    if r["LEN_M"] > C.mh_max_spacing(r["DN"]) + 1e-6]
            _log(f"  {len(design['reaches']):,} reaches, "
                 f"{design['n_chambers']:,} chambers, "
                 f"{sum(r['LEN_M'] for r in design['reaches']) / 1000:,.2f} km gravity; "
                 f"H12 breaches {len(over)}")
            if not over:
                break
            for r in over:
                # pin as many cuts as this reach needs to fall inside its own limit
                n = int(math.ceil(r["LEN_M"] / C.mh_max_spacing(r["DN"])))
                for k in range(1, n):
                    forced[r["run"]].add(r["d0"] + k * (r["d1"] - r["d0"]) / n)
        if design is None:
            raise RuntimeError("no design produced")
        left = [r for r in design["reaches"]
                if r["LEN_M"] > C.mh_max_spacing(r["DN"]) + 1e-6]
        if left:
            rec.note(f"{len(left)} reach(es) still over the G203-p30 Table 12 spacing after "
                     "12 chambering passes - reported, not hidden")

        # ---------------------------------------------------------------- publish
        _log("\n[5b] what the 0.05 % laying step costs in depth")
        design["rounding"] = _rounding_cost(design)
        for tag in ("coarse", "fine"):
            g = design["rounding"][tag]
            _log(f"  gravity all the way, no stations, {g['step_pct']:.3g} % step: "
                 f"deepest cover {g['max_cover_m']:.2f} m, "
                 f"{g['unexited_breaches']} un-exited cap breach(es)")

        _log("\n[6] publish")
        return _publish(al, design, straight, rec)


def _solve_all(al: Alignment, runs, reaches, terr: Terrain, solver: Solver,
               rec: K.StageRecord) -> Dict:
    """Chamber ids, flow accumulation, the level solve, and the cap-and-veto ladder."""
    # ---- chamber identity: one per distinct (run, chainage) position, shared at the
    #      structural vertices where runs meet.
    key_of: Dict[Tuple[int, int], int] = {}
    xy: List[Tuple[float, float]] = []
    struct_node: Dict[int, int] = {}          # alignment vertex -> chamber id

    def cid(pt: Tuple[float, float], struct: Optional[int] = None) -> int:
        if struct is not None and struct in struct_node:
            return struct_node[struct]
        k = (int(round(pt[0] * 100)), int(round(pt[1] * 100)))
        if k not in key_of:
            key_of[k] = len(xy)
            xy.append((float(pt[0]), float(pt[1])))
        if struct is not None:
            struct_node[struct] = key_of[k]
        return key_of[k]

    for r in reaches:
        cs = list(r["geom"].coords)
        r["us"] = cid(cs[0], r["run_us"] if r["us_struct"] else None)
        r["ds"] = cid(cs[-1], r["run_ds"] if r["ds_struct"] else None)

    XY = np.array(xy)
    Z = terr.z([tuple(p) for p in XY])
    if np.isnan(Z).any():
        n = int(np.isnan(Z).sum())
        Z = np.where(np.isnan(Z), np.nanmedian(Z), Z)
        rec.note(f"{n} chamber(s) fell on terrain nodata and took the median ground level")

    # ---- the tree over chambers
    T = nx.DiGraph()
    for i, r in enumerate(reaches):
        if r["us"] == r["ds"]:
            continue
        T.add_edge(r["us"], r["ds"], i=i)
    if T.number_of_nodes() != len(XY):
        for n in range(len(XY)):
            if n not in T:
                T.add_node(n)
    root = min(T.nodes, key=lambda n: math.dist(XY[n], STP_XY))
    order = list(nx.topological_sort(T))                     # upstream first

    # ---- load and accumulation
    q_node, n_node, _far = _loads(XY, rec)
    KMPER = _infiltration_basis(float(q_node.sum()), rec)
    q_acc, n_acc, up_km = q_node.copy(), n_node.copy(), np.zeros(len(XY))
    for u in order:
        for v in T.successors(u):
            q_acc[v] += q_acc[u]
            n_acc[v] += n_acc[u]
            up_km[v] += up_km[u] + reaches[T[u][v]["i"]]["len_m"] / 1000.0

    q_per_prop = float(q_acc[root] / max(n_acc[root], 1.0))
    PF_HELD = C.pf_merrimack(C.PF_HOLD_PROPERTIES * q_per_prop / 1000.0)

    def flow(node: int) -> Tuple[float, float, float, float, str]:
        """Qadf, PF, infiltration and peak, all reproducible from the published row."""
        qadf = float(q_acc[node])
        npr = float(n_acc[node])
        qinf = (C.INFILT_L_D_KM / 86400.0) * (float(up_km[node]) + KMPER * qadf)
        if npr > C.PF_HOLD_PROPERTIES:
            pf, meth = C.pf_merrimack(qadf / 1000.0), "merrimack"
        else:
            # G201 prescribes NO formula below 100 properties. 'held' is the honest token,
            # and the value held is Merrimack at the 100-property flow (criteria
            # ASSUMPTIONS['PF_COMPARISON_HOLD']).
            pf, meth = PF_HELD, "held"
        return qadf, pf, qinf, qadf * 1000.0 / 86400.0 * pf + qinf, meth

    # ---- ground sampled along every reach (invariant 5)
    for r in reaches:
        L = r["len_m"]
        n = max(int(L // SAMPLE_M), 1)
        ds = np.linspace(0.0, L, n + 1)
        pts = [r["geom"].interpolate(float(d)) for d in ds]
        z = terr.z([(p.x, p.y) for p in pts])
        if np.isnan(z).any():
            z = np.where(np.isnan(z), np.nanmedian(z) if np.isfinite(np.nanmedian(z)) else 0.0, z)
        # The two ends are the CHAMBER levels, not a second sample of the same pixel. The
        # level solve reads this profile and the schedules read Z[node]; if the two ever
        # differ the published cover is not the cover the solve enforced, and a reach can
        # be 0.4 m under minimum on a layer that solved correctly.
        z[0], z[-1] = Z[r["us"]], Z[r["ds"]]
        r["prof_d"], r["prof_z"] = ds, z

    # ---- the level solve, with the cap-and-veto ladder. Stations may appear, which
    #      removes a stretch from the gravity layer, so the whole solve is repeated until
    #      no un-exited breach is left.
    pumped: List[Dict] = []
    stations: List[Dict] = []
    blocked: set = set()                     # chamber ids that no longer drain by gravity
    # ONE station per sweep, and the sweep is redone from scratch afterwards. The breaches
    # are NOT independent: a 24 m-deep stretch reports a breach on every one of its reaches,
    # and the station at the head of it fixes all of them. Placing them all in one pass
    # produced 33 stations at 100 m centres down a falling hillside - the arithmetic was
    # right and the engineering was nonsense, because each breach was measured against a
    # profile that assumed no station upstream of it.
    for attempt in range(40):
        res = _level(T, order, root, XY, Z, reaches, flow, solver, blocked)
        breach = _cap_ladder(res, T, reaches, root, XY, Z)
        breach = [b for b in breach if b["node"] not in blocked]
        if not breach:
            break
        st = breach[0]                              # most upstream: _cap_ladder is in
        u = st["node"]                              # topological order
        d = _pump_target(u, T, XY, Z, reaches)
        seg = _path_reaches(u, d, T, reaches)
        if not seg or any(reaches[i].get("pumped") for i in seg):
            rec.note(f"cap breach at chamber {u} could not be given a station - reported, "
                     "not hidden")
            break
        rm = sum(reaches[i]["len_m"] for i in seg)
        stations.append(dict(
            node=u, x=float(XY[u, 0]), y=float(XY[u, 1]), grd_m=float(Z[u]),
            inv_m=float(res["inv"][u]), cover_m=st["cover"], why="cap",
            discharge=d, dx=float(XY[d, 0]), dy=float(XY[d, 1]),
            discharge_grd_m=float(Z[d]),
            static_lift_m=float(Z[d] - K.min_invert_depth(C.DN_MIN_MAIN) - res["inv"][u]),
            rm_len_m=rm, q_adf_m3d=float(q_acc[u]), q_pk_ls=float(flow(u)[3]),
            n_prop=float(n_acc[u])))
        for i in seg:
            reaches[i]["pumped"] = True
        pumped.extend(dict(i=i) for i in seg)
        blocked |= {reaches[i]["us"] for i in seg}
        _log(f"  CAP at chamber {u} (cover {st['cover']:.2f} m, no sec 5 exit) "
             f"-> lifting station; {rm:,.0f} m pumped over the local summit "
             f"(ground {Z[u]:.1f} -> {Z[d]:.1f} m, static lift "
             f"{stations[-1]['static_lift_m']:.1f} m)")
    else:
        rec.note("station search hit its 40-sweep limit - reported, not hidden")

    rows = _rows(res, reaches, flow, solver, root, XY, Z, T)
    return dict(reaches=rows, level=res, tree=T, root=root, XY=XY, Z=Z,
                stations=stations, q_acc=q_acc, n_acc=n_acc, flow=flow, order=order,
                q_per_prop=q_per_prop, pf_held=PF_HELD, km_per=KMPER,
                pumped=[reaches[d["i"]] for d in pumped], all_reaches=reaches,
                n_chambers=len({r["us"] for r in rows} | {r["ds"] for r in rows}))


def _level(T, order, root, XY, Z, reaches, flow, solver: Solver, blocked: set) -> Dict:
    """Forward level solve, upstream to downstream. Shallowest legal profile.

    inv_ds = min(ground_ds - min_invert_depth, inv_us - L * s_min) is provably the highest
    invert a legal design can have at each node, so this pass IS the "lay as shallow as H3
    allows" rule of philosophy sec 5, not an approximation of it. Anything deeper than this
    is ground the design cannot get back.
    """
    inv = np.full(len(XY), np.nan)
    out: Dict[int, Dict] = {}
    arrive: Dict[int, List[Tuple[float, int]]] = defaultdict(list)
    for u in order:
        if u in blocked:
            continue
        ins = [(T[p][u]["i"]) for p in T.predecessors(u)
               if not reaches[T[p][u]["i"]].get("pumped") and p not in blocked]
        outs = [T[u][v]["i"] for v in T.successors(u) if not reaches[T[u][v]["i"]].get("pumped")]
        if not outs:
            continue
        i = outs[0]
        r = reaches[i]
        v = r["ds"]
        _qadf, _pf, _qinf, qpk, _m = flow(u)
        cand = [(out[j]["inv_ds"], out[j]["dn"]) for j in ins if j in out]
        arrive[u] = cand

        # ---- seat the outgoing invert and choose the diameter TOGETHER.
        # They are coupled: the invert must sit at least min_invert_depth(DN) below ground
        # (H3), and min_invert_depth depends on the DN the flow chooses, which depends on
        # the gradient the invert allows. Solving them in sequence published a level set
        # for DN400 under a pipe that came out DN500 - 1.10 m of cover against 1.30 m
        # required, and a blocking H3 failure on a design that looked finished.
        # The loop is monotone by construction: the diameter FLOOR only ever rises and the
        # invert only ever falls, so it cannot chase itself.
        def _ceiling(dn: int) -> float:
            return Z[u] - K.min_invert_depth(dn)

        def _seat(dn: int) -> float:
            if not cand:
                return _ceiling(dn)                # a head: exactly at minimum cover
            # soffit to soffit into the bigger pipe (P5, and H14's rule at an existing
            # structure). Never invert to invert: it backs the smaller pipe up.
            od_out = dn / 1000.0
            return min(min(iv + d_in / 1000.0 - od_out for iv, d_in in cand),
                       _ceiling(dn))

        dn_floor = C.DN_MIN_MAIN
        inv_try = _seat(dn_floor)
        sol = solver.solve_from(dn_floor, inv_try, r["prof_z"], r["prof_d"],
                                r["len_m"], qpk)
        for _ in range(2 * len(DN_SERIES_TRUNK) + 4):
            want = min(inv_try, _seat(sol["dn"])) - sol.get("deficit", 0.0)
            if sol["dn"] == dn_floor and abs(want - inv_try) < 1e-9:
                break
            dn_floor = max(dn_floor, sol["dn"])
            inv_try = min(inv_try, want)          # monotone: the invert only ever falls
            sol = solver.solve_from(dn_floor, inv_try, r["prof_z"], r["prof_d"],
                                    r["len_m"], qpk)
        # The loop raises the diameter floor to stay monotone, so it can finish one size
        # above what the settled invert actually needs. Oversizing is PROHIBITED (G203-p29
        # and Ten States sec 33.43 independently), so the last word goes to an
        # unconstrained solve at the settled invert - a smaller pipe there is legal
        # everywhere the bigger one was, because its own outside diameter is smaller and
        # its cover is therefore deeper, never shallower.
        free = solver.solve_from(C.DN_MIN_MAIN, inv_try, r["prof_z"], r["prof_d"],
                                 r["len_m"], qpk)
        if free["dn"] < sol["dn"] and free.get("deficit", 0.0) <= 1e-9:
            sol = free
        inv[u] = inv_try
        out[i] = dict(sol, us=u, ds=v, qpk=qpk, inv_us=inv[u])
        inv[v] = sol["inv_ds"] if np.isnan(inv[v]) else min(inv[v], sol["inv_ds"])
    return dict(inv=inv, sol=out, arrive=arrive)


def _rounding_cost(design, solver_step: float = 0.00025) -> Dict[str, float]:
    """What P1's 0.05 % gradient step costs in depth, and whether it is what bought a station.

    THIS IS NOT A DECORATION. G203-p29 sets the minimum gradient at DN >= 900 to
    0.75 mm/m - 0.075 % - and 0.075 is NOT a multiple of the project's own 0.05 % laying
    step (criteria.SLOPE_STEP, user rule 2026-08-23). So every flat large-diameter reach is
    laid at 0.10 %, a THIRD steeper than the guideline floor, and on a 7 km flat leg that is
    an extra 1.75 m of trench. Philosophy sec 3a is explicit that "P1 is never bought at the
    price of a pumping station", and contract._cross_field refuses to publish an off-step
    gradient - so the design complies and the cost is measured and reported instead of
    argued about. The comparison re-runs the SAME level solve on the SAME chambers with a
    0.025 % step, which can represent 0.075 % exactly.
    """
    out = {}
    for tag, step in (("coarse", STEP), ("fine", solver_step)):
        # BOTH runs are station-free, on the same chambers and the same flows. Comparing a
        # design that has stations against one that does not would say the finer step makes
        # things worse, which is an artefact of the comparison and not a fact about the step.
        reaches = [dict(r) for r in design["all_reaches"]]
        for r in reaches:
            r.pop("pumped", None)
        res = _level(design["tree"], design["order"], design["root"], design["XY"],
                     design["Z"], reaches, design["flow"], Solver(step=step), set())
        cov = _cover_series(res, reaches, design["tree"], design["XY"], design["Z"])
        breaches = _cap_ladder(res, design["tree"], reaches, design["root"],
                               design["XY"], design["Z"])
        out[tag] = dict(step_pct=step * 100.0,
                        max_cover_m=max(cov.values()) if cov else 0.0,
                        unexited_breaches=len(breaches))
    return out


def _cover_series(res, reaches, T, XY, Z) -> Dict[int, float]:
    cov = {}
    for i, s in res["sol"].items():
        od = s["dn"] / 1000.0 + K.AUDITOR_OD_ALLOW_M
        cov[i] = max(Z[s["us"]] - s["inv_us"] - od, Z[s["ds"]] - s["inv_ds"] - od)
    return cov


def _cap_ladder(res, T, reaches, root, XY, Z) -> List[Dict]:
    """Philosophy sec 5. Cover over 12 m gets exactly two exits and nothing else.

    Returns the breaches with NO exit, most upstream first - each of those is a station,
    because layer 1 of the ladder can only ever ADD one and the economics is third.
    """
    cov = _cover_series(res, reaches, T, XY, Z)
    bad = []
    for i, c in cov.items():
        if c <= CAP_M + 1e-6:
            continue
        s = res["sol"][i]
        # exit A: does cover recover within 500 m downstream?
        run_m, node, recovered = 0.0, s["ds"], False
        while run_m <= EXIT_RECOVER_M:
            nxt = list(T.successors(node))
            if not nxt:
                break
            j = T[node][nxt[0]]["i"]
            if j not in cov:
                break
            run_m += reaches[j]["len_m"]
            if cov[j] <= CAP_M:
                recovered = True
                break
            node = nxt[0]
        if recovered and run_m <= EXIT_RECOVER_M:
            s["cap_exit"], s["cap_len"] = "recovers_500m", run_m
            continue
        # exit B: is the outfall within 1,000 m along the flow path?
        run_m, node = 0.0, s["ds"]
        while run_m <= EXIT_OUTFALL_M and node != root:
            nxt = list(T.successors(node))
            if not nxt:
                break
            run_m += reaches[T[node][nxt[0]]["i"]]["len_m"]
            node = nxt[0]
        if node == root and run_m <= EXIT_OUTFALL_M:
            s["cap_exit"], s["cap_len"] = "outfall_1000m", run_m
            continue
        s["cap_exit"], s["cap_len"] = "", 0.0
        bad.append(dict(reach=i, node=s["us"], cover=c))
    return bad


def _pump_target(u: int, T, XY, Z, reaches) -> int:
    """Where the station discharges: the FIRST LOCAL SUMMIT downstream.

    Not a chosen distance - a measured point on the DEM. Walk downstream while the ground
    is still rising and stop where it turns over. That is what a designer does on a ridge,
    and it is why the western leg needs ONE station rather than a cascade of them: pump over
    the hump, then let gravity have the fall on the other side. If the ground is already
    falling at the station, the discharge is the next chamber - a plain lift.
    """
    node = u
    while True:
        nxt = list(T.successors(node))
        if not nxt:
            return node
        v = nxt[0]
        if Z[v] <= Z[node] + 1e-6 and node != u:
            return node
        node = v
        if node == u:
            return v


def _path_reaches(u: int, d: int, T, reaches) -> List[int]:
    out, node = [], u
    while node != d:
        nxt = list(T.successors(node))
        if not nxt:
            break
        out.append(T[node][nxt[0]]["i"])
        node = nxt[0]
    return out


def _rows(res, reaches, flow, solver: Solver, root, XY, Z, T) -> List[Dict]:
    """Turn the solve into publishable reach rows - every contract field, nothing implicit."""
    rows = []
    for i, s in sorted(res["sol"].items()):
        r = reaches[i]
        dn, sl, L = s["dn"], s["s"], r["len_m"]
        od = dn / 1000.0 + K.AUDITOR_OD_ALLOW_M
        inv_up, inv_dn = s["inv_us"], s["inv_us"] - sl * L
        us_depth, ds_depth = Z[s["us"]] - inv_up, Z[s["ds"]] - inv_dn
        qadf, pf, qinf, qpk, meth = flow(s["us"])
        q = qpk / 1000.0
        y, v = _state(dn, sl, q)
        clean = "velocity" if (v is not None and v >= C.V_SELF_CLEANSING) else (
            "tractive" if sl >= hydra.smin_tractive(q, C) - 1e-12 else "neither")
        rows.append(dict(
            i=i, run=r["run"], d0=r["d0"], d1=r["d1"], geom=r["geom"], desc=r["desc"],
            us=s["us"], ds=s["ds"], DN=int(dn), MATERIAL=_material(dn),
            CONSTR="open_trench", LEN_M=L,
            SLOPE_LAID=sl * 100.0, SLOPE_MIN=solver.smin(dn, q) * 100.0,
            GRADIENT_BY=s["gradient_by"],
            SIZED_BY=s.get("sized_by", "capacity"),
            CLEAN_BY=clean, TAU_PA=C.TAU_PA,
            INV_UP=inv_up, INV_DN=inv_dn, US_DEPTH=us_depth, DS_DEPTH=ds_depth,
            COVER_US=us_depth - od, COVER_DN=ds_depth - od,
            QADF_M3D=qadf, QINF_LS=qinf, PF=pf, PF_METH=meth, QPK_LS=qpk,
            V_PK_MS=float(v or 0.0), DOD_PK=float(y or 0.0),
            RET_MIN=(L / max(v or 0.01, 0.01)) / 60.0,
            PAST_CAP=1 if max(us_depth - od, ds_depth - od) > CAP_M + 1e-6 else 0,
            CAP_EXIT=s.get("cap_exit", ""), CAP_LEN_M=float(s.get("cap_len", 0.0)),
            TIE_TYPE="soffit" if s["ds"] == root else "none",
        ))
    return rows


# ======================================================================================
# corridor exposure and the crossings register
# ======================================================================================

def _corridor_exposure(rows: List[Dict], terr: Terrain, rec: K.StageRecord):
    """ON_DUAL_M and ON_WADI_M, measured per reach, plus the crossings register H1 demands.

    Both are recomputed independently by the auditor (H1, R3, R4), which is the point: the
    number on the layer is the DESIGN'S OWN CLAIM, so a disagreement with the auditor is
    itself the finding. W10 published neither and shipped 1.67 km along a dual carriageway
    and 131.7 km on wadi ground.
    """
    roads = gpd.read_file(P_ROADS)
    if roads.crs is None or roads.crs.to_epsg() != K.CRS_EPSG:
        roads = roads.set_crs(K.CRS_EPSG, allow_override=True)
    rec.read("Road centerline 2", P_ROADS, len(roads))
    dual = roads[roads["dual"].astype(str) == "1"]
    band = unary_union(dual.geometry.buffer(C.DUAL_TWIN_M))       # 6 m, the auditor's band
    dual_lines = list(dual.geometry)
    dtree = cKDTree(np.array([[g.centroid.x, g.centroid.y] for g in dual_lines])) \
        if dual_lines else None

    cross = []
    for r in rows:
        g = r["geom"]
        inter = g.intersection(band)
        r["ON_DUAL_M"] = float(inter.length) if not inter.is_empty else 0.0
        # wadi: sample the reach, not just the midpoint the auditor uses
        n = max(int(r["LEN_M"] // SAMPLE_M), 1)
        pts = [g.interpolate(k * r["LEN_M"] / n) for k in range(n + 1)]
        w = terr.wadi([(p.x, p.y) for p in pts])
        r["ON_WADI_M"] = float(w.mean() * r["LEN_M"])
        r["CROSS_ID"] = ""
        if r["ON_DUAL_M"] > 0.0:
            cid = f"X{len(cross) + 1:04d}"
            r["CROSS_ID"] = cid
            ang = 90.0
            if dtree is not None:
                mid = g.interpolate(0.5, normalized=True)
                _d, k = dtree.query([mid.x, mid.y])
                dl = dual_lines[int(k)]
                cs = list(dl.coords)
                b1 = math.degrees(math.atan2(cs[-1][1] - cs[0][1], cs[-1][0] - cs[0][0]))
                gc = list(g.coords)
                b2 = math.degrees(math.atan2(gc[-1][1] - gc[0][1], gc[-1][0] - gc[0][0]))
                ang = abs((b2 - b1 + 180.0) % 180.0)
                # FOLD TO THE ACUTE ANGLE. `(b2 - b1 + 180) % 180` lands anywhere in
                # [0, 180) and two lines 174 deg apart are 6 deg from parallel, not 174 deg
                # from it. Unfolded, the register reported the two longest PARALLEL contacts
                # (120 m at 173.8 deg, 58.6 m at 173.3 deg) as near-perpendicular, which is
                # exactly the field H1 relies on to say a crossing IS a crossing.
                ang = min(ang, 180.0 - ang)
            cross.append(dict(CROSS_ID=cid, EDGE_UID="", OBSTACLE="dual",
                              LEN_M=r["ON_DUAL_M"], ANGLE_DEG=float(min(ang, 90.0)),
                              METHOD="thrust_bore", APPROVED=0, geometry=inter,
                              _reach=r["i"]))
    return cross


# ======================================================================================
# publishing
# ======================================================================================

def _publish(al: Alignment, design, straight, rec: K.StageRecord) -> int:
    rows = design["reaches"]
    XY, Z, T, root = design["XY"], design["Z"], design["tree"], design["root"]
    # corridor exposure needs the hazard grid again; one reader, opened here
    t2 = Terrain.__new__(Terrain)
    t2.dem = rasterio.open(P_TERRAIN)
    t2.haz = rasterio.open(P_HAZARD)
    cross = _corridor_exposure(rows, t2, rec)

    # ---- build the contract graph. Geometry is DERIVED from node coordinates here and
    #      nowhere else, so a reach cannot end anywhere but on its own chambers.
    net = K.Network()
    uid: Dict[int, str] = {}
    used = sorted({r["us"] for r in rows} | {r["ds"] for r in rows})
    inv = design["level"]["inv"]

    # ---- H1 names the CHAMBER as well as the pipe: "no pipe or chamber in a wadi".
    #      _corridor_exposure answers only the pipe half, and neither audit.h1 (dual only)
    #      nor audit.r4 (pipe midpoints only) ever samples a node - so a chamber standing in
    #      the 50-year band was invisible on both sides of the check. Same grid, same
    #      classes, same reader as ON_WADI_M.
    node_wadi = dict(zip(used, t2.wadi([(float(XY[n, 0]), float(XY[n, 1])) for n in used])))

    # ---- CONFIDENCE follows the line the chamber stands on. The gap connector is this
    #      stage's own straight line, not the draftsman's (OPEN S3-1), and philosophy sec 4
    #      requires a provisional corridor's structures to be identified separately in EVERY
    #      drawing and schedule. A chamber whose every incident reach is provisional is
    #      provisional; one shared with a drafted reach keeps the better grade.
    _prov_edges = {r["i"] for r in rows if "GAP CLOSURE" in r["desc"]}
    _incident: Dict[int, List[int]] = defaultdict(list)
    for r in rows:
        _incident[r["us"]].append(r["i"])
        _incident[r["ds"]].append(r["i"])
    prov_nodes = {n for n, es in _incident.items() if es and all(i in _prov_edges for i in es)}
    # node-level aggregates
    n_in = defaultdict(int)
    n_out = defaultdict(int)
    for r in rows:
        n_in[r["ds"]] += 1
        n_out[r["us"]] += 1
    out_dn = {r["us"]: r["DN"] for r in rows}
    node_cov: Dict[int, float] = {}
    for r in rows:
        for nd, cv in ((r["us"], r["COVER_US"]), (r["ds"], r["COVER_DN"])):
            node_cov[nd] = min(node_cov.get(nd, 1e9), cv)
    st_nodes = {s["node"] for s in design["stations"]}

    order = [n for n in nx.topological_sort(T) if n in set(used)]
    for n in order:
        dn = out_dn.get(n, C.DN_MIN_MAIN)
        depth = float(Z[n] - inv[n]) if np.isfinite(inv[n]) else 0.0
        kind = ("outfall" if n == root else
                "station" if n in st_nodes else
                "junction" if n_in[n] > 1 else
                "head" if n_in[n] == 0 else "chamber")
        uid[n] = net.node(float(XY[n, 0]), float(XY[n, 1]),
                          kind=kind, tier="trunk main",
                          grd_m=float(Z[n]),
                          inv_m=float(inv[n]) if np.isfinite(inv[n]) else float(Z[n]) - depth,
                          src="main_pipe",
                          confidence=("provisional" if n in prov_nodes else "drafted"),
                          stage=STAGE, system="central")
    for r in rows:
        cs = list(r["geom"].coords)
        r["EDGE_UID"] = net.add_edge(uid[r["us"]], uid[r["ds"]],
                                     vertices=tuple(c[:2] for c in cs[1:-1]),
                                     stage=STAGE, tier="trunk main", kind="gravity",
                                     src="main_pipe",
                                     confidence=("provisional"
                                                 if "GAP CLOSURE" in r["desc"] else "drafted"))

    # ---- drops, inlet angles and node attributes
    drop = defaultdict(float)
    stepup = defaultdict(float)
    inlet = {}
    for n in used:
        outs = [r for r in rows if r["us"] == n]
        ins = [r for r in rows if r["ds"] == n]
        if outs and ins:
            drop[n] = max(0.0, max(i["INV_DN"] for i in ins) - outs[0]["INV_UP"])
            # THE OTHER SIGN OF THE SAME SUBTRACTION, AND IT IS NOT A DROP. Where the
            # outgoing pipe is SMALLER than the arriving one, _level's soffit-to-soffit
            # seat puts the outlet invert ABOVE the inlet invert - a step UP at the
            # chamber, which ponds the upstream reach at its own outlet. max(0.0, ...)
            # above rounds that to a 0.00 m drop and the layer then says nothing about it,
            # and audit.h11 only looks WITHIN a reach. Measured, published and filed as a
            # finding rather than clamped away; the cure is in _seat (never seat an outlet
            # above the lowest arriving invert), which is a level change, not a field.
            stepup[n] = max(0.0, outs[0]["INV_UP"] - min(i["INV_DN"] for i in ins))
            a = min(_inlet_angle_deg(list(i["geom"].coords)[-2],
                                     tuple(XY[n]),
                                     list(outs[0]["geom"].coords)[1]) for i in ins)
            inlet[n] = a
        else:
            # no inlet, or no outlet: nothing turns the flow, so nothing can breach
            # G203-p30's 90 deg. 180 is "straight through", the honest neutral.
            inlet[n] = 180.0

    for n in used:
        nd = net.nodes[uid[n]]
        dn = out_dn.get(n, C.DN_MIN_MAIN)
        depth = float(nd.grd_m - nd.inv_m)
        cv = float(node_cov.get(n, K.cover(dn, depth)))
        d = float(drop.get(n, 0.0))
        past = 1 if cv > CAP_M + 1e-6 else 0
        ex = ""
        if past:
            hits = [r["CAP_EXIT"] for r in rows if (r["us"] == n or r["ds"] == n)
                    and r["PAST_CAP"] == 1 and r["CAP_EXIT"]]
            ex = hits[0] if hits else "recovers_500m"
        nd.attrs.update(
            COVER_M=max(cv, 0.0),
            INLET_DEG=float(inlet.get(n, 180.0)),
            INLET_FLAG=1 if inlet.get(n, 180.0) < 90.0 - 1e-6 else 0,
            MH_DIA=_mh_dia(depth, dn),
            DROP_M=d,
            DROP_TYPE=("vortex" if d > C.BACKDROP_MAX + 1e-9 else
                       "backdrop" if d > C.DROP_TRIGGER + 1e-9 else "none"),
            VORTEX=1 if d > C.BACKDROP_MAX + 1e-9 else 0,
            STEP_UP_M=float(stepup.get(n, 0.0)),
            IN_WADI=1 if bool(node_wadi.get(n, False)) else 0,
            Q_ADF_M3D=float(design["q_acc"][n]),
            Q_PK_LS=float(design["flow"](n)[3]),
            N_PROP=float(design["n_acc"][n]),
            PAST_CAP=past, CAP_EXIT=ex,
        )

    problems = net.check()
    for p in problems:
        _log("  NOTE " + p.replace("\n", " "))
        rec.note(p)

    extra_e = pd.DataFrame([{k: r[k] for k in (
        "EDGE_UID", "DN", "MATERIAL", "CONSTR", "SLOPE_LAID", "SLOPE_MIN", "GRADIENT_BY",
        "SIZED_BY", "CLEAN_BY", "TAU_PA", "INV_UP", "INV_DN", "US_DEPTH", "DS_DEPTH",
        "COVER_US", "COVER_DN", "QADF_M3D", "QINF_LS", "PF", "PF_METH", "QPK_LS",
        "V_PK_MS", "DOD_PK", "RET_MIN", "PAST_CAP", "CAP_EXIT", "CAP_LEN_M", "TIE_TYPE",
        "ON_DUAL_M", "ON_WADI_M", "CROSS_ID")} for r in rows])
    edges = net.to_edges_gdf("gravity", extra=extra_e)
    nodes = net.to_nodes_gdf()

    # NODE_KIND 'head' is not in the contract's terminal set, and a head has no inlet: it is
    # the top of a run. contract.NODE_KIND allows it; the terminal check only cares about
    # nodes with no DS_NODE.
    K.Network.assert_round_trip(nodes, edges)
    K.Network.assert_degrees(nodes, edges)

    p = K.publish(edges, "reaches", W11A, stage=STAGE, gpkg=GPKG)
    rec.wrote("reaches", p, len(edges))
    p = K.publish(nodes, "nodes", W11A, stage=STAGE, gpkg=GPKG)
    rec.wrote("nodes", p, len(nodes))

    if cross:
        for c in cross:
            c["EDGE_UID"] = next(r["EDGE_UID"] for r in rows if r["i"] == c["_reach"])
            c.pop("_reach")
            c.update(SRC="main_pipe", CONFIDENCE="drafted", STAGE=STAGE)
        cg = gpd.GeoDataFrame(cross, geometry="geometry", crs=K.CRS_EPSG)
        cg = cg[~cg.geometry.is_empty].copy()
        # the intersection with the 6 m band can come back multipart where a reach clips
        # the same carriageway twice; the schedule row is the longest contact, and LEN_M is
        # re-read FROM that geometry so the field and the line cannot part (contract
        # validate(): "the schedule and the drawing are describing different pipes")
        cg["geometry"] = [g if g.geom_type == "LineString" else
                          max(g.geoms, key=lambda x: x.length) for g in cg.geometry]
        cg["LEN_M"] = cg.geometry.length
        p = K.publish(cg, "crossings", W11A, stage=STAGE, gpkg=GPKG)
        rec.wrote("crossings", p, len(cg))

    # ---- CAD mirrors. The brief names W11a_trunk.shp; the GeoPackage above is the audited
    #      artefact, because a DBF renames GRADIENT_BY to GRADIENT_B and audit G2 then fails
    #      a design that was correct in memory.
    shp = os.path.join(OUT_SHP, "W11a_trunk.shp")
    edges.to_file(shp)
    nodes.to_file(os.path.join(OUT_SHP, "W11a_trunk_nodes.shp"))
    lost = [f.name for f in K.REACHES.fields if not f.shp_safe and f.name in edges.columns]
    with open(shp.replace(".shp", ".README.txt"), "w", encoding="utf-8") as fh:
        fh.write("CAD MIRROR - NOT THE AUDITED LAYER.\n"
                 "The DBF truncates these field names to 10 characters: "
                 + ", ".join(lost) + "\n"
                 "The audited layer is " + os.path.join(OUT_SHP, GPKG) + " (layer 'reaches').\n")
    rec.wrote("W11a_trunk.shp (CAD mirror)", shp, len(edges))

    # ---- the pumped stretches and the stations, handed to stage 6
    #      They are NOT published as `rising_mains`: that layer wants pump duty, wet-well
    #      volume, air valves and total head, and a rising main is sized on DUTY, not on
    #      arriving flow (philosophy sec 6). Stage 3 has the route and the static lift and
    #      nothing else, so it hands over exactly that and does not pretend otherwise.
    if design["stations"]:
        pd.DataFrame(design["stations"]).to_csv(
            os.path.join(OUT_RUN, "s3_trunk_stations.csv"), index=False)
        rec.wrote("stations hand-off (CSV, not a published layer)",
                  os.path.join(OUT_RUN, "s3_trunk_stations.csv"), len(design["stations"]))
    if design["pumped"]:
        pg = gpd.GeoDataFrame(
            [dict(SEG=k, LEN_M=r["len_m"], DESC=r["desc"], STAGE=STAGE,
                  NOTE="pumped section - rising main route, sized on pump duty at stage 6")
             for k, r in enumerate(design["pumped"])],
            geometry=[r["geom"] for r in design["pumped"]], crs=K.CRS_EPSG)
        pp = os.path.join(OUT_SHP, "W11a_trunk_pumped.shp")
        pg.to_file(pp)
        rec.wrote("pumped sections (rising-main routes, stage 6)", pp, len(pg))

    # ---- schedules
    sch = K.schedule_frame(edges, "pipes", stage=STAGE)
    sch.to_csv(os.path.join(OUT_RUN, "s3_trunk_pipe_schedule.csv"), index=False)

    # ---- the findings register: every reach and chamber that will fail a check, named.
    #      "No exemptions in compliance checks" - a skipped row reads as a PASS, so the
    #      rows that fail are written out by id rather than summarised into a percentage.
    find = []
    for r in rows:
        if r["ON_DUAL_M"] > 30.0:
            find.append(dict(check="H1/R3", kind="reach", id=r["EDGE_UID"],
                             value=round(r["ON_DUAL_M"], 1), unit="m in the 6 m dual band",
                             cause="INPUT alignment - no pipe may run along a dual "
                                   "carriageway (project rule 7); a crossing is scheduled, "
                                   "a run along one is not a crossing"))
        if r["ON_WADI_M"] > 0.0:
            find.append(dict(check="R4", kind="reach", id=r["EDGE_UID"],
                             value=round(r["ON_WADI_M"], 1), unit="m on wadi ground",
                             cause="INPUT alignment - Hazard_T50y class >= 4 (G203-p30 "
                                   "sec 4.4.1, p33: pipelines AND chambers prohibited)"))
    for nrow in nodes.itertuples():
        if int(getattr(nrow, "IN_WADI", 0)) == 1:
            find.append(dict(check="H1", kind="chamber", id=nrow.NODE_UID,
                             value=1, unit="chamber on wadi ground",
                             cause="INPUT alignment - H1 forbids a CHAMBER in a wadi as well "
                                   "as a pipe (G203-p33, project rule 8). audit.h1 tests only "
                                   "the dual band and audit.r4 only pipe midpoints, so a "
                                   "chamber in the 50-year band is reported here or nowhere"))
        if float(getattr(nrow, "STEP_UP_M", 0.0)) > 1e-6:
            find.append(dict(check="H11(intent)", kind="chamber", id=nrow.NODE_UID,
                             value=round(float(nrow.STEP_UP_M), 3),
                             unit="m the outlet invert sits ABOVE the arriving invert",
                             cause="the outgoing reach is a smaller diameter than the "
                                   "arriving one, so _level's soffit-to-soffit seat steps the "
                                   "invert UP and ponds the upstream reach. audit.h11 checks "
                                   "fall WITHIN a reach only and cannot see it. The cure is a "
                                   "floor in _seat, which changes levels - raised, not taken"))
        if nrow.INLET_DEG < 90.0 - 1e-6:
            find.append(dict(check="H10", kind="chamber", id=nrow.NODE_UID,
                             value=round(float(nrow.INLET_DEG), 1), unit="deg inlet angle",
                             cause="INPUT alignment turns the flow through more than 90 deg "
                                   "(G203-p30). Inside the project's own stated 85 deg "
                                   "deviation (criteria.INLET_MIN_DEG, user 2026-08-20); "
                                   "needs a purpose-made swept channel, not a re-route"))
    for st in design["stations"]:
        find.append(dict(check="H15", kind="station", id=f"chamber {st['node']}",
                         value=round(st["cover_m"], 2), unit="m cover at the cap",
                         cause="cap-and-veto ladder layer 1 (philosophy sec 5): cover past "
                               "12 m with neither exit, so a lifting station. Each station "
                               "splits the gravity layer, and audit.h15 demands ONE "
                               "component - contract OPEN-1"))
    pd.DataFrame(find).to_csv(os.path.join(OUT_RUN, "s3_trunk_findings.csv"), index=False)
    rec.wrote("findings register", os.path.join(OUT_RUN, "s3_trunk_findings.csv"), len(find))

    # ---- audit readiness, before the auditor ever runs
    rd = K.audit_readiness(edges, nodes, external=("roads", "hazard", "existing"))
    rd.to_csv(os.path.join(OUT_RUN, "s3_trunk_audit_readiness.csv"), index=False)
    cant = rd[~rd.can_run]
    _log(f"\n  audit readiness: {int(rd.can_run.sum())}/{len(rd)} checks can run"
         + ("" if cant.empty else "  MISSING -> " + "; ".join(
             f"{r.check}: {r.missing}" for r in cant.itertuples())))

    _summary(al, design, edges, nodes, straight, rec)
    return 0


def _summary(al, design, edges, nodes, straight, rec: K.StageRecord) -> None:
    rows = design["reaches"]
    km = edges.LEN_M.sum() / 1000.0
    root = design["root"]
    outfall = [r for r in rows if r["ds"] == root]
    _log("\n" + "=" * 88)
    _log("THE TRUNK AS DESIGNED")
    _log("=" * 88)
    _log(f"  length              {km:,.2f} km gravity, TIER = 'trunk main' on every reach")
    _log(f"  chambers            {len(nodes):,}  ({len(nodes) / km:,.1f} per km)")
    _log(f"  diameters           {edges.DN.min()} - {edges.DN.max()} mm; at the works "
         f"DN{max(r['DN'] for r in outfall) if outfall else 0}")
    if outfall:
        o = max(outfall, key=lambda r: r["QPK_LS"])
        _log(f"  flow at the works   {o['QADF_M3D']:,.0f} m3/d average, "
             f"{o['QPK_LS']:,.0f} L/s peak (PF {o['PF']:.3f} {o['PF_METH']}, "
             f"infiltration {o['QINF_LS']:.1f} L/s)")
        _log(f"  invert at the works {o['INV_DN']:,.2f} m aOD, "
             f"{o['DS_DEPTH']:,.2f} m below ground - the level the existing works inlet "
             f"must accept (OPEN S3-3)")
    _log(f"  cover               min {edges.COVER_US.min():.2f} m, "
         f"max {max(edges.COVER_US.max(), edges.COVER_DN.max()):.2f} m; "
         f"{int(edges.PAST_CAP.sum())} reach(es) past the 12 m cap, all with a sec 5 exit")
    _log(f"  gradient            {edges.SLOPE_LAID.min():.3f} - {edges.SLOPE_LAID.max():.3f} %, "
         f"{edges.SLOPE_LAID.nunique()} distinct values on 0.05 % steps")
    _log(f"  velocity at peak    {edges.V_PK_MS.min():.2f} - {edges.V_PK_MS.max():.2f} m/s "
         f"(limit {C.V_MAX})")
    _log(f"  d/D at peak         max {edges.DOD_PK.max():.3f}")
    vel = int((edges.CLEAN_BY == "velocity").sum())
    tra = int((edges.CLEAN_BY == "tractive").sum())
    _log(f"  self-cleansing      {vel:,} by velocity, {tra:,} by tractive force "
         f"({100 * tra / max(len(edges), 1):.0f} % - exposed to tau = {C.TAU_PA} Pa, GAP-9)")
    _log("  gradient set by     " + ", ".join(
        f"{k} {v}" for k, v in edges.GRADIENT_BY.value_counts().items()))
    _log("  diameter set by     " + ", ".join(
        f"{k} {v}" for k, v in edges.SIZED_BY.value_counts().items()))
    _log(f"  stations            {len(design['stations'])} "
         f"(cap breaches with no sec 5 exit; rising mains are stage 6)")
    for s in design["stations"]:
        _log(f"      at ({s['x']:,.0f}, {s['y']:,.0f}) ground {s['grd_m']:.1f} m, "
             f"cover {s['cover_m']:.1f} m -> discharge ({s['dx']:,.0f}, {s['dy']:,.0f}) "
             f"ground {s['discharge_grd_m']:.1f} m, rising main {s['rm_len_m']:,.0f} m")
    _log(f"  on a dual carriageway  {edges.ON_DUAL_M.sum():,.0f} m over "
         f"{int((edges.ON_DUAL_M > 0).sum())} reaches, longest single reach "
         f"{edges.ON_DUAL_M.max():,.0f} m   [H1 / R3 - a defect of the INPUT alignment]")
    _log(f"  on wadi ground         {edges.ON_WADI_M.sum() / 1000:,.2f} km over "
         f"{int((edges.ON_WADI_M > 0).sum())} reaches "
         f"   [H1 / R4 - a defect of the INPUT alignment]")
    sharp = nodes[nodes.INLET_DEG < 90.0 - 1e-6]
    if len(sharp):
        _log(f"  inlets under 90 deg    {len(sharp)}, from "
             f"{sharp.INLET_DEG.min():.1f} to {sharp.INLET_DEG.max():.1f} deg "
             f"   [H10 - the INPUT alignment turns the flow; all are inside the project's "
             f"own stated {C.INLET_MIN_DEG:.0f} deg deviation and each needs a swept channel]")
    rnd = design.get("rounding")
    if rnd:
        a, b = rnd["coarse"], rnd["fine"]
        _log(f"  P1 rounding cost    laid gravity throughout with no stations, the "
             f"{a['step_pct']:.3g} % laying step reaches {a['max_cover_m']:.2f} m of cover "
             f"and {a['unexited_breaches']} un-exited breaches; a {b['step_pct']:.3g} % "
             f"step - fine enough to lay the G203-p29 0.075 % floor exactly - reaches "
             f"{b['max_cover_m']:.2f} m and {b['unexited_breaches']}. The step is a "
             f"PREFERENCE (P1) and the contract will not publish an off-step gradient, so "
             f"the cost is reported, not taken.")
    _log(f"  trunk-main by G203-p35 (D > 800 mm): "
         f"{edges.LEN_M[edges.DN > 800].sum() / 1000:,.1f} km of {km:,.1f} km. "
         f"TIER is 'trunk main' throughout as instructed; the guideline's own definition "
         f"is narrower and the rest is a main by its criteria.")
    for k, v in straight.items():
        rec.metric("straighten_" + k, round(float(v), 2))
    rec.metric("trunk_km", round(km, 2))
    rec.metric("chambers", len(nodes))
    rec.metric("stations", len(design["stations"]))
    rec.metric("on_dual_m", round(float(edges.ON_DUAL_M.sum()), 1))
    rec.metric("on_wadi_km", round(float(edges.ON_WADI_M.sum()) / 1000.0, 2))

    _log("\nOPEN ITEMS RAISED BY THIS STAGE")
    _log("  S3-1  the western leg's real alignment. The drawn line stops 879.82 m short of "
         "segment 0\n        (NOT the 2 m the build note states). Closed here with a "
         "provisional straight\n        connector; the leg cannot reach the works by "
         "gravity on this line either way.")
    _log("  S3-2  criteria.DN_SERIES stops at DN1200 and this trunk needs more. The sizes "
         "used above\n        it (1400/1700/1800/2000/2400) are the ones G203-p32 Tab 13, "
         "p35 Tab 15 and p30\n        Tab 12 print. Extend criteria.DN_SERIES once, in one "
         "place, when NWS confirm.")
    _log("  S3-3  the existing works inlet invert. H14 says an existing structure's invert "
         "is fixed\n        and the design yields to it, soffit to soffit. NWS have not "
         "given it, so the\n        trunk is laid to its own level and that level is "
         "published above for confirmation.")
    _log("  S3-4  the given alignment breaches H1 in two ways (wadi ground and a dual "
         "carriageway).\n        Stage 3 measures them onto the layer and does not move the "
         "line: the main pipe is\n        an INPUT (CLAUDE.md / 00_CURRENT). Both need the "
         "user's decision.")


if __name__ == "__main__":
    sys.exit(run())
