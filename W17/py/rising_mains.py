"""Rising main routes along the road network, for every pumped link of the seven options.

Rule (engineer, 2026-10-01): a rising main may cross a dual carriageway if needed. A dual carriageway (dual = 1 in
SHP/Road centerline 2) is therefore usable but costed at 5x its length, so it is crossed rather than followed.
The graph is the road centrelines plus the sewer pipes themselves (they follow the streets the network was laid on,
which the road layer does not always carry); road pieces are joined where ends or vertices lie within 2 m, and every
manhole is tied to the nearest road vertex within 50 m. Where the route is still more than 1.6 x the straight line,
the main goes cross-country (G203 p51 provides for cross-country rising mains): straight line x 1.1, flagged.
Output: W17/results/rising_mains.csv and .gpkg (one row per distinct link: source outfall -> destination).
"""
import csv, math, os
import geopandas as gpd, networkx as nx, numpy as np
from shapely.geometry import LineString, Point
from scipy.spatial import cKDTree
from routing import SCENARIOS, routing

ROADS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\SHP\Road centerline 2\Road_Centercline.shp"
NODES = r"D:\VBOX\bridge\out\inv_w17\nodes.csv"
OUT = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results"
DUAL_COST, SNAP = 5.0, 2.0

roads = gpd.read_file(ROADS).explode(index_parts=False)
pts, edges = [], []
for geom, dual in zip(roads.geometry, roads["dual"]):
    if geom is None or geom.is_empty:
        continue
    c = list(geom.coords)
    for a, b in zip(c[:-1], c[1:]):
        pts += [a[:2], b[:2]]
        edges.append((a[:2], b[:2], dual))
P = np.array(pts)
tree = cKDTree(P)
# merge points within SNAP metres into one graph node
groups = tree.query_ball_point(P, SNAP)
rep = {}
for i, g in enumerate(groups):
    root = min(g)
    rep[i] = rep.get(root, root)
key = lambda xy, i: rep[i]
G = nx.Graph()
for k, (a, b, dual) in enumerate(edges):
    ia, ib = rep[2 * k], rep[2 * k + 1]
    if ia == ib:
        continue
    L = math.dist(a, b)
    w = L * (DUAL_COST if dual == 1 else 1.0)
    if not G.has_edge(ia, ib) or G[ia][ib]["w"] > w:
        G.add_edge(ia, ib, w=w, L=L, dual=int(dual == 1))
print(f"road graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges, {nx.number_connected_components(G)} pieces")
xy = {r["label"]: (float(r["x"]), float(r["y"])) for r in csv.DictReader(open(NODES, encoding="utf-8"))}
# sewer pipes as edges (node ids offset beyond the road points), tied to roads within 50 m
LINKS = NODES.replace("nodes.csv", "links.csv")
nid = {r["id"]: (float(r["x"]), float(r["y"])) for r in csv.DictReader(open(NODES, encoding="utf-8"))}
lab2id = {r["label"]: r["id"] for r in csv.DictReader(open(NODES, encoding="utf-8"))}
OFF = 10_000_000
sew = lambda i: OFF + int(i)
for r in csv.DictReader(open(LINKS, encoding="utf-8")):
    if r["type"] != "CO" or r["start"] not in nid or r["stop"] not in nid:
        continue
    L = math.dist(nid[r["start"]], nid[r["stop"]])
    G.add_edge(sew(r["start"]), sew(r["stop"]), w=L, L=L, dual=0)
road_nodes = np.array(sorted(n for n in G.nodes() if n < OFF))
rtree = cKDTree(P[road_nodes])
for i, (x, y) in nid.items():
    if sew(i) in G:
        d, k = rtree.query((x, y))
        if d <= 50:
            G.add_edge(sew(i), int(road_nodes[k]), w=d, L=d, dual=0)
coord = lambda n: tuple(P[n]) if n < OFF else nid[str(n - OFF)]
gn = np.array(sorted(n for n in G.nodes() if n < OFF))
gtree = cKDTree(P[gn])
links = set()
for name in SCENARIOS:
    tr, joins, stp = routing(name)
    links |= {(s, mh) for s, mh, r in tr} | {(s, z) for s, z in joins.items()}

rows, geoms = [], []
for src, dst in sorted(links):
    a, b = xy[src], xy[dst]
    straight = math.dist(a, b)
    # start and end on the sewer graph when the node is a manhole/outfall, otherwise at the nearest road vertex
    na = sew(lab2id[src]) if sew(lab2id[src]) in G else int(gn[gtree.query(a)[1]])
    nb = sew(lab2id[dst]) if sew(lab2id[dst]) in G else int(gn[gtree.query(b)[1]])
    da, db = math.dist(a, coord(na)), math.dist(b, coord(nb))
    try:
        path = nx.shortest_path(G, na, nb, weight="w")
        line = [a] + [coord(n) for n in path] + [b]
        L = da + db + sum(G[u][v]["L"] for u, v in zip(path[:-1], path[1:]))
        dual_m = sum(G[u][v]["L"] for u, v in zip(path[:-1], path[1:]) if G[u][v]["dual"])
        how = "roads and streets"
        if straight > 0 and L > 1.6 * straight:
            line, L, dual_m, how = [a, b], straight * 1.1, 0.0, "cross-country, straight x 1.1"
    except nx.NetworkXNoPath:
        line, L, dual_m, how = [a, b], straight * 1.1, 0.0, "cross-country, straight x 1.1 (no street path)"
    rows.append(dict(source=src, dest=dst, length_m=round(L, 1), straight_m=round(straight, 1),
                     ratio=round(L / straight, 2) if straight else 0, along_dual_m=round(dual_m, 1),
                     snap_src_m=round(da, 1), snap_dst_m=round(db, 1), method=how))
    geoms.append(LineString(line))

os.makedirs(OUT, exist_ok=True)
with open(rf"{OUT}\rising_mains.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
gpd.GeoDataFrame(rows, geometry=geoms, crs=roads.crs).to_file(rf"{OUT}\rising_mains.gpkg", driver="GPKG")
for r in rows:
    print(f"  {r['source']:4s} -> {r['dest']:10s} {r['length_m']:8,.0f} m  (straight {r['straight_m']:7,.0f}, x{r['ratio']:.2f}; along dual {r['along_dual_m']:5,.0f} m; snaps {r['snap_src_m']:.0f}/{r['snap_dst_m']:.0f} m) {r['method']}")
