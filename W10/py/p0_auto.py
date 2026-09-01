"""Phase 0.2 - fill in the corridors the draftsman has not reached yet.

He is still working and there is no time to wait for him, so everything generated here is
tagged SRC='auto' and kept beside his work rather than over it. When he delivers again,
0.1 re-runs and this script regenerates only what is still missing.

Calibrating the two possible methods against his own output in a window he HAS finished
(2 km square at 448891 2568094, 2,344 plots) showed they do different halves of the job:

    his drawing        70.96 km   30.3 m per plot   a connected network with through routes
    free-space skeleton 39.57 km  16.9 m per plot   the streets between plots, disconnected

The skeleton finds the capillaries and misses the arteries, because an artery runs through
open ground and open ground is exactly what the skeleton has to exclude to avoid wandering
across the desert. The road centre-line layer is the mirror image: it has the arteries and
is missing the internal streets of 10,823 plots. So neither alone is the answer and this
script uses both, in the order they are reliable:

    A  treat the raw road layer, then drop whatever the draftsman already covers
    B  skeletonise the free space between plots that still have nothing
    C  stitch B onto A, because a corridor that reaches no outfall is not a corridor

Run:  python p0_auto.py
"""
import os
import sys
import time
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union, linemerge
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "W8", "py"))

import config as C
import skeleton as S
from sewnet.stages.road_treatment import RoadTreatment
from sewnet.prep import load_boundary

warnings.filterwarnings("ignore")

CLUSTER_GROW_M = 40.0     # plots within this of each other are one settlement pocket
CLUSTER_MIN_PLOTS = 6     # a pocket smaller than this is left to detail design
STITCH_MAX_M = 400.0      # how far a stranded skeleton pocket may reach for a corridor
FRONTAGE_M = 40.0         # a plot is served if a corridor passes within this


def _timed(msg, t0):
    print(f"   {msg} ({time.time() - t0:.1f} s)")
    return time.time()


def unserved(plots, corridors, dist=None):
    """Plots with no corridor within reach, measured from the polygon not its centre."""
    dist = dist or C.PLOT_SERVED_M
    if len(corridors) == 0:
        return plots, np.zeros(len(plots), dtype=bool)
    near = gpd.sjoin_nearest(plots[["geometry"]], corridors[["geometry"]], how="left",
                             max_distance=dist, distance_col="D")
    near = near[~near.index.duplicated(keep="first")]
    served = near["D"].notna().values
    return plots[~served], served


def treat_roads(boundary):
    """Step A - the raw road layer put through the W8 treatment stage.

    Reused rather than re-implemented: dual carriageways dropped whole, one side kept of a
    two-lane pair, roundabouts and turning fillets removed, straight streets dissolved back
    into one line between intersections. Everything it removes is written out with its
    reason so the result can be argued with.
    """
    roads = gpd.read_file(C.ROADS).set_crs(C.EPSG, allow_override=True)
    roads = roads[roads.geometry.notna() & ~roads.geometry.is_empty]
    roads = gpd.clip(roads, boundary).explode(index_parts=False)
    roads = roads[roads.geometry.geom_type == "LineString"]
    roads = roads[roads.geometry.length > C.CLIP_SLIVER_M].reset_index(drop=True)

    segs, attrs = [], {}
    for _, r in roads.iterrows():
        g = r.geometry
        segs.append(g)
        attrs[id(g)] = {"dual": int(r.get("dual", 0) or 0),
                        "strcls": str(r.get("StrCls", "") or "")}
    rt = RoadTreatment(attrs=attrs)
    out = rt.run(segs, units=None,
                 out_path=os.path.join(C.OUT_SHP, "W10_road_treatment.shp"))
    return out, rt.report


def skeleton_pockets(plots_left):
    """Step B - street centre lines recovered from the space plots left between them."""
    if len(plots_left) == 0:
        return []
    blobs = gpd.GeoDataFrame(
        geometry=[unary_union(plots_left.geometry.buffer(CLUSTER_GROW_M))],
        crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
    tree = STRtree(list(plots_left.geometry))
    lines, done, skipped = [], 0, 0
    for i, blob in enumerate(blobs.geometry):
        idx = [int(j) for j in tree.query(blob) if plots_left.geometry.iloc[int(j)].intersects(blob)]
        if len(idx) < CLUSTER_MIN_PLOTS:
            skipped += len(idx)
            continue
        sub = [plots_left.geometry.iloc[j] for j in idx]
        try:
            raw = S.street_lines(sub, blob)
            keep = S.prune_to_cover(raw, sub, frontage_m=FRONTAGE_M)
        except Exception as e:
            print(f"      pocket {i}: {e}")
            continue
        lines.extend(keep)
        done += len(idx)
        if (i + 1) % 100 == 0:
            print(f"      {i+1}/{len(blobs)} pockets, {len(lines)} lines so far")
    print(f"   pockets used: plots covered {done:,}, "
          f"left to detail design (pocket < {CLUSTER_MIN_PLOTS} plots) {skipped:,}")
    return lines


def stitch(new_lines, existing, max_m=STITCH_MAX_M, k=10):
    """Step C - join the new corridor fragments up, and onto the existing network.

    The skeleton comes out in pieces: erasing the open ground so the skeleton does not
    wander across the desert also cuts it wherever a street crosses open ground, so 11,800
    lines arrive as ~2,300 separate islands.

    Sending each island to the nearest EXISTING corridor costs 287 km, because most islands
    are far from a mapped road and each pays the full distance on its own. Nearly all of
    them, though, sit a few tens of metres from ANOTHER island. So the islands and the
    existing network are treated as one graph and joined by a minimum spanning tree: each
    island reaches its neighbour, and only the pocket as a whole pays the long link out.

    Returns the links and the number of islands still stranded further than `max_m` from
    anything. Those are not generated - a link that long is a route a person chooses.
    """
    import networkx as nx
    from shapely.ops import nearest_points

    if not new_lines or len(existing) == 0:
        return [], 0
    groups = gpd.GeoDataFrame(geometry=[unary_union([l.buffer(1.0) for l in new_lines])],
                              crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
    geoms = list(groups.geometry)
    ex = unary_union(existing.geometry.values)
    nodes = [ex] + geoms                      # node 0 is the whole existing network
    tree = STRtree(geoms)

    G = nx.Graph()
    G.add_nodes_from(range(len(nodes)))
    for i, g in enumerate(geoms, start=1):
        # the way out to the existing network
        d0 = g.distance(ex)
        if d0 <= max_m:
            G.add_edge(0, i, w=d0)
        # and the way across to nearby islands
        for j in tree.query(g.buffer(max_m)):
            j = int(j) + 1
            if j <= i:
                continue
            d = g.distance(nodes[j])
            if d <= max_m:
                G.add_edge(i, j, w=d)

    links, stranded = [], 0
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        if 0 not in comp:
            # nothing in this group can reach the network within max_m
            stranded += len(comp)
            continue
        for u, v in nx.minimum_spanning_edges(sub, weight="w", data=False):
            a, b = nearest_points(nodes[u], nodes[v])
            if a.distance(b) > 1.5:
                links.append(LineString([a, b]))
    isolated = [n for n in G.nodes if G.degree(n) == 0]
    stranded += len(isolated)
    return links, stranded


def main():
    t0 = time.time()
    os.makedirs(C.OUT_SHP, exist_ok=True)
    os.makedirs(C.OUT_RUN, exist_ok=True)

    boundary = load_boundary(C.BOUNDARY)
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    draft = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors_drafted.shp"))
    print(f"draftsman: {len(draft):,} lines, {draft.length.sum()/1000:,.1f} km")

    # ---------------------------------------------------------------- A
    print("\nA  treating the raw road layer")
    t = time.time()
    treated, rep = treat_roads(boundary)
    t = _timed(f"{len(treated):,} corridors, {sum(g.length for g in treated)/1000:,.1f} km", t)
    for k in ("segments_in", "km_in", "km_out", "dual_excluded", "roundabouts_collapsed",
              "traffic_links_dropped", "collinear_joins", "empty_stubs_dropped"):
        if k in rep:
            print(f"      {k:<26s} {rep[k]}")

    # Coverage is DECIDED at the match distance and CUT at the tighter one, so a treated
    # road that runs beside a drafted corridor is dropped, while one that merely ends on it
    # keeps its length right up to the junction instead of stopping 25 m short.
    draft_cover = unary_union(draft.geometry.buffer(C.CORRIDOR_MATCH_M))
    draft_buf = unary_union(draft.geometry.buffer(C.CORRIDOR_CUT_M))
    keep = []
    for g in treated:
        if g.intersection(draft_cover).length > 0.75 * g.length:
            continue
        rest = g.difference(draft_buf)
        if rest.is_empty:
            continue
        parts = rest.geoms if rest.geom_type == "MultiLineString" else [rest]
        keep.extend([p for p in parts if p.length > 15.0])
    auto_road = gpd.GeoDataFrame({"SRC": ["auto_road"] * len(keep)},
                                 geometry=keep, crs=C.EPSG)
    print(f"   after removing what the draftsman already covers: "
          f"{len(auto_road):,} lines, {auto_road.length.sum()/1000:,.1f} km")

    have = gpd.GeoDataFrame(pd.concat([draft[["geometry"]], auto_road[["geometry"]]]),
                            crs=C.EPSG)
    left, served = unserved(plots, have)
    print(f"   plots served by draft + treated roads: {served.sum():,} "
          f"({100*served.mean():.1f} %)   still unserved: {len(left):,}")

    # ---------------------------------------------------------------- B
    print(f"\nB  skeletonising the free space around {len(left):,} plots with nothing")
    t = time.time()
    sk = skeleton_pockets(left)
    auto_blk = gpd.GeoDataFrame({"SRC": ["auto_block"] * len(sk)},
                                geometry=sk, crs=C.EPSG)
    t = _timed(f"{len(auto_blk):,} lines, {auto_blk.length.sum()/1000:,.1f} km", t)

    # ---------------------------------------------------------------- C
    print("\nC  stitching the new pockets onto the network")
    links, failed = stitch(sk, have)
    auto_link = gpd.GeoDataFrame({"SRC": ["auto_link"] * len(links)},
                                 geometry=links, crs=C.EPSG)
    print(f"   {len(auto_link):,} links, {auto_link.length.sum()/1000:,.2f} km; "
          f"{failed} islands further than {STITCH_MAX_M:.0f} m from anything - "
          f"these need a route chosen, not generated")

    # ---------------------------------------------------------------- out
    draft2 = draft[["geometry"]].copy()
    draft2["SRC"] = "draft"
    allc = gpd.GeoDataFrame(
        pd.concat([draft2, auto_road, auto_blk, auto_link], ignore_index=True),
        crs=C.EPSG)
    allc["LEN_M"] = allc.length
    allc["CORR_ID"] = [f"W10-{i+1:06d}" for i in range(len(allc))]
    allc.to_file(os.path.join(C.OUT_SHP, "W10_corridors.shp"))

    left2, served2 = unserved(plots, allc)
    print(f"\nFINAL  {len(allc):,} corridors, {allc.LEN_M.sum()/1000:,.1f} km")
    print(allc.groupby("SRC").agg(n=("LEN_M", "size"),
                                  km=("LEN_M", lambda s: round(s.sum()/1000, 1))))
    print(f"plots served: {served2.sum():,} of {len(plots):,} "
          f"({100*served2.mean():.1f} %)   unserved: {len(left2):,}")
    left2[["geometry"]].to_file(os.path.join(C.OUT_SHP, "W10_plots_unserved.shp"))

    pd.DataFrame([
        ("draft km", round(draft.length.sum()/1000, 1)),
        ("auto_road km", round(auto_road.length.sum()/1000, 1)),
        ("auto_block km", round(auto_blk.length.sum()/1000, 1)),
        ("auto_link km", round(auto_link.length.sum()/1000, 2)),
        ("total km", round(allc.LEN_M.sum()/1000, 1)),
        ("plots served", int(served2.sum())),
        ("plots unserved", int(len(left2))),
        ("m of corridor per served plot", round(allc.LEN_M.sum()/max(served2.sum(), 1), 1)),
        ("pockets too far to stitch", failed),
    ], columns=["item", "value"]).to_csv(os.path.join(C.OUT_RUN, "p0_auto.csv"), index=False)
    print(f"\ntotal {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
