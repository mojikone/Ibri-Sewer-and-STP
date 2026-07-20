"""S1 — Road graph, betweenness centrality, dual-carriageway detection, arterial skeleton.
Inputs : W1/shp/roads_study.shp
Outputs: W1/shp/roads_graph.shp  (LEN, BTW, DUAL, ARTERIAL)
Basis  : BRAIN 04 — no hierarchy attributes in source; arterials derived geometrically.
"""
import math, os, sys, time
import numpy as np
import shapefile
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union, linemerge
from shapely.strtree import STRtree
import networkx as nx

W = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W1"
SRC = os.path.join(W, "shp", "roads_study.shp")
OUT = os.path.join(W, "shp", "roads_graph.shp")
SNAP = 0.5  # m — node snap tolerance

t0 = time.time()
r = shapefile.Reader(SRC)
lines = []
for sr in r.iterShapes():
    pts = sr.points
    if len(pts) < 2:
        continue
    parts = list(sr.parts) + [len(pts)]
    for a, b in zip(parts[:-1], parts[1:]):
        seg = pts[a:b]
        if len(seg) >= 2:
            lines.append(LineString(seg))
print(f"input parts: {len(lines)}  ({time.time()-t0:.0f}s)")

# node at all intersections
merged = unary_union(lines)
if isinstance(merged, LineString):
    merged = MultiLineString([merged])
edges = [g for g in merged.geoms if g.length > 0.1]
print(f"noded edges: {len(edges)}  ({time.time()-t0:.0f}s)")

def nkey(p):
    return (round(p[0] / SNAP) * SNAP, round(p[1] / SNAP) * SNAP)

G = nx.Graph()
for i, g in enumerate(edges):
    a, b = nkey(g.coords[0]), nkey(g.coords[-1])
    if a == b:
        continue
    # keep shortest parallel edge if duplicate node pair
    if G.has_edge(a, b) and G[a][b]["len"] <= g.length:
        continue
    G.add_edge(a, b, len=g.length, idx=i)
print(f"graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# largest connected component only
cc = max(nx.connected_components(G), key=len)
G = G.subgraph(cc).copy()
print(f"main component: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# approximate edge betweenness (k-sample)
k = min(600, G.number_of_nodes())
btw = nx.edge_betweenness_centrality(G, k=k, weight="len", seed=42)
print(f"betweenness done ({time.time()-t0:.0f}s)")

# dual-carriageway: near-parallel edge of similar bearing within 8–45 m
geoms = {d["idx"]: edges[d["idx"]] for _, _, d in G.edges(data=True)}
idx_list = list(geoms.keys())
tree = STRtree([geoms[i] for i in idx_list])
pos = {id(geoms[i]): i for i in idx_list}

def bearing(g):
    (x1, y1), (x2, y2) = g.coords[0], g.coords[-1]
    return math.atan2(y2 - y1, x2 - x1) % math.pi

dual = set()
for i in idx_list:
    g = geoms[i]
    if g.length < 40:
        continue
    b1 = bearing(g)
    mid = g.interpolate(0.5, normalized=True)
    cands = tree.query(g.buffer(45))
    for c in cands:
        j = idx_list[c] if isinstance(c, (int, np.integer)) else pos.get(id(c))
        if j is None or j == i:
            continue
        h = geoms[j]
        if h.length < 40:
            continue
        db = abs(b1 - bearing(h))
        db = min(db, math.pi - db)
        if db > math.radians(12):
            continue
        d = mid.distance(h)
        if 6 <= d <= 45:
            dual.add(i); dual.add(j)
            break
print(f"dual-flagged edges: {len(dual)}  ({time.time()-t0:.0f}s)")

vals = np.array(list(btw.values()))
thr = np.quantile(vals, 0.90)  # top 10% betweenness
wtr = shapefile.Writer(OUT)
wtr.field("LEN", "N", 12, 1)
wtr.field("BTW", "N", 18, 8)
wtr.field("DUAL", "N", 1, 0)
wtr.field("ARTERIAL", "N", 1, 0)
n_art = 0
for u, v, d in G.edges(data=True):
    g = edges[d["idx"]]
    b = btw[(u, v)] if (u, v) in btw else btw.get((v, u), 0.0)
    isd = 1 if d["idx"] in dual else 0
    art = 1 if (b >= thr or isd) else 0
    n_art += art
    wtr.line([list(g.coords)])
    wtr.record(round(g.length, 1), b, isd, art)
wtr.close()
with open(OUT.replace(".shp", ".prj"), "w") as f:
    f.write('PROJCS["WGS_1984_UTM_Zone_40N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",57.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]')
print(f"arterial edges: {n_art}/{G.number_of_edges()}  -> {OUT}  ({time.time()-t0:.0f}s)")
