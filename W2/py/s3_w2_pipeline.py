"""S3 (W2) — Collapsed-dual graph, DTM elevations, full-coverage trunk, structured zones,
consolidated SLS, GUD-201 flows, wadi crossings.
Per _BRAIN/02 (criteria), _BRAIN/06 (W2 feedback constraints).
"""
import os, math, csv, time
import numpy as np
import shapefile
import rasterio
import networkx as nx
from shapely.geometry import LineString, Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union
from scipy.spatial import cKDTree, Voronoi

W1 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W1"
W2 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W2"
DTM = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Terrain\DTM_terrain_mask.tif"
PRJ = open(os.path.join(W1, "shp", "roads_graph.prj")).read()
STP = (444387.0, 2563352.5)
OR_ASSUMED, PROP_PER_PLOT = 6.0, 1.0            # pending NCSI (data request)
LPCD, ND_RATIO, GOV_RATIO = 164.0, 0.22, 0.14   # G1-p60
RET_DOM, RET_ND = 0.85, 0.54                    # G1-p71
INFIL_L_D_KM, PF_CAP = 720.0, 5.0               # G1-p72
MAX_COVER, MIN_COVER_INV = 12.0, 1.9            # p33
SLS_MIN_PLOTS = 50                              # consolidation: absorb smaller pockets
def smin_for(plots):
    if plots < 150: return 0.0050
    if plots < 400: return 0.0027
    if plots < 1500: return 0.00155
    if plots < 5000: return 0.0010
    return 0.00075                              # Table 11 p29

t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)
def wprj(p_):
    with open(p_.replace(".shp", ".prj"), "w") as f: f.write(PRJ)

# ---------- load W1 noded edges (with DUAL flags) ----------
r = shapefile.Reader(os.path.join(W1, "shp", "roads_graph.shp"))
E = []  # (a,b,len,dual,art,geom)
for sr, rec in zip(r.iterShapes(), r.iterRecords()):
    pts = sr.points
    a, b = (round(pts[0][0], 1), round(pts[0][1], 1)), (round(pts[-1][0], 1), round(pts[-1][1], 1))
    if a == b: continue
    E.append([a, b, rec[0], rec[2], rec[3], pts])
log(f"edges in: {len(E)}")

# ---------- collapse dual carriageways: merge nodes of dual edges within 35 m ----------
dual_nodes = set()
for a, b, L, dual, art, pts in E:
    if dual: dual_nodes.update((a, b))
dn = list(dual_nodes)
tree = cKDTree(np.array(dn))
pairs = tree.query_pairs(35.0)
parent = {n: n for n in dn}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for i, j in pairs:
    a, b = find(dn[i]), find(dn[j])
    if a != b: parent[a] = b
groups = {}
for n in dn: groups.setdefault(find(n), []).append(n)
remap = {}
for rep, mem in groups.items():
    cx = round(sum(m[0] for m in mem) / len(mem), 1)
    cy = round(sum(m[1] for m in mem) / len(mem), 1)
    for m in mem: remap[m] = (cx, cy)
log(f"dual nodes {len(dn)}, merged into {len(groups)} reps")

G = nx.Graph()
edge_geom = {}
for a, b, L, dual, art, pts in E:
    a2, b2 = remap.get(a, a), remap.get(b, b)
    if a2 == b2: continue                       # twin cross-links vanish
    rf = 0.55 if dual else (0.70 if art else 1.0)
    if G.has_edge(a2, b2) and G[a2][b2]["len"] <= L: continue  # parallel twin collapses
    G.add_edge(a2, b2, len=L, rf=rf, dual=dual)
    edge_geom[(a2, b2)] = LineString(pts)
cc = max(nx.connected_components(G), key=len)
G = G.subgraph(cc).copy()
nodes = list(G.nodes)
log(f"collapsed graph {len(nodes)} nodes / {G.number_of_edges()} edges")

# ---------- DTM z ----------
ds = rasterio.open(DTM)
band = ds.read(1)
def zval(x, y):
    try:
        rr, cc_ = ds.index(x, y)
        v = band[rr, cc_]
        return float(v) if v != ds.nodata and v > -1000 else None
    except Exception:
        return None
Z = {n: zval(*n) for n in nodes}
miss = [n for n in nodes if Z[n] is None]
for n in miss:
    vs = [Z[m] for m in G[n] if Z.get(m) is not None]
    Z[n] = float(np.mean(vs)) if vs else 350.0
log(f"DTM sampled ({len(miss)} filled)")

# ---------- plots ----------
sf = shapefile.Reader(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\SHP\Landuse\Landuse.shp")
fields = [f[0] for f in sf.fields[1:]]
i_cls = fields.index("NewLUClass")
SERV = {"Residential", "Commercial", "Governmental", "Industry"}
cent, cls_l = [], []
for sr, rec in zip(sf.iterShapes(), sf.iterRecords()):
    if rec[i_cls] not in SERV: continue
    xs = [p[0] for p in sr.points]; ys = [p[1] for p in sr.points]
    cent.append((sum(xs) / len(xs), sum(ys) / len(ys))); cls_l.append(rec[i_cls])
cent = np.array(cent)
ntree = cKDTree(np.array(nodes))
d_, idx_ = ntree.query(cent, distance_upper_bound=400.0)
node_plots, wt = {}, {}
for k, (di, ii) in enumerate(zip(d_, idx_)):
    if not np.isfinite(di) or ii >= len(nodes): continue
    n = nodes[ii]
    node_plots.setdefault(n, {}).setdefault(cls_l[k], 0)
    node_plots[n][cls_l[k]] += 1
wt = {n: sum(d.values()) for n, d in node_plots.items()}
log(f"plots assigned {sum(wt.values())}")

# ---------- STP connector ----------
d0, i0 = ntree.query(np.array([STP]))
near = nodes[int(i0[0])]
stp_node = (STP[0], STP[1])
G.add_edge(stp_node, near, len=float(d0[0]), rf=0.55, dual=0)
edge_geom[(stp_node, near)] = LineString([STP, near])
Z[stp_node] = zval(*STP) or Z[near]
log(f"STP z(DTM)={Z[stp_node]:.1f}")

# ---------- routing tree from STP (aesthetic: arterial-discounted) ----------
dist, paths = nx.single_source_dijkstra(G, stp_node, weight=lambda u, v, d: d["len"] * d["rf"])
reach = set(dist)
# ---------- hydraulic tree (for gravity screening): penalize sewage climbing ----------
DG = nx.DiGraph()
KCLIMB = 300.0
for u, v, d in G.edges(data=True):
    DG.add_edge(u, v, w=d["len"] + KCLIMB * max(0.0, Z[u] - Z[v]), len=d["len"])
    DG.add_edge(v, u, w=d["len"] + KCLIMB * max(0.0, Z[v] - Z[u]), len=d["len"])
hdist, hpaths = nx.single_source_dijkstra(DG, stp_node, weight="w")
# ---------- seeds: full coverage ----------
cellw = {}
for n, w_ in wt.items():
    if n not in reach: continue
    k = (int(n[0] // 1000), int(n[1] // 1000))
    cellw.setdefault(k, [0, None])
    cellw[k][0] += w_
    if cellw[k][1] is None or w_ > wt.get(cellw[k][1], 0): cellw[k][1] = n
cands = sorted(([s, n] for s, n in cellw.values() if s >= 60 and n), reverse=True)
seeds = []
for s, n in cands:
    if all(math.dist(n, m) > 2500 for _, m in seeds):
        seeds.append((s, n))
log(f"seeds/zone outlets: {len(seeds)}")

# ---------- trunk ----------
trunk_edges = {}
for s, n in seeds:
    for a, b in zip(paths[n][:-1], paths[n][1:]):
        k = (a, b) if (a, b) in edge_geom else (b, a)
        trunk_edges.setdefault(k, 0)
for n, w_ in wt.items():
    if n not in reach: continue
    for a, b in zip(paths[n][:-1], paths[n][1:]):
        k = (a, b) if (a, b) in edge_geom else (b, a)
        if k in trunk_edges: trunk_edges[k] += w_
main_seed = seeds[0][1]
main_set = set()
for a, b in zip(paths[main_seed][:-1], paths[main_seed][1:]):
    main_set.add((a, b) if (a, b) in edge_geom else (b, a))
log(f"trunk edges {len(trunk_edges)}")

# ---------- territories ----------
S = [n for _, n in seeds]
md, mpaths = nx.multi_source_dijkstra(G, set(S), weight=lambda u, v, d: d["len"])
owner = {n: mpaths[n][0] for n in reach if n in mpaths and mpaths[n]}
zone_id = {n: i for i, (_, n) in enumerate(seeds, start=1)}

# ---------- SLS: profile fail -> connected components -> one SLS each ----------
acc = {n: 0 for n in G.nodes}
for n, w_ in wt.items():
    if n not in hdist: continue
    for m in hpaths[n]: acc[m] += w_
fail = set()
for n in reach:
    if wt.get(n, 0) == 0 or n not in hpaths: continue
    fl = list(reversed(hpaths[n]))
    inv = Z[n] - MIN_COVER_INV
    for a, b in zip(fl[:-1], fl[1:]):
        L = G[a][b]["len"]
        inv = min(inv - L * smin_for(max(acc[a], wt.get(n, 0))), Z[b] - MIN_COVER_INV)
        if Z[b] - inv > MAX_COVER:
            fail.add(n); break
log(f"gravity-fail nodes: {len(fail)} ({100*sum(wt.get(n,0) for n in fail)/max(1,sum(wt.values())):.1f}% of plots)")
FG = G.subgraph(fail)
sls = []
for comp in nx.connected_components(FG):
    plots = sum(wt.get(n, 0) for n in comp)
    if plots < SLS_MIN_PLOTS: continue
    low = min(comp, key=lambda n: Z[n])
    # force main target: nearest non-fail reachable node
    tgt = None; best = 1e18
    for n in comp:
        for m in G[n]:
            if m not in fail and m in reach:
                dd = math.dist(low, m)
                if dd < best: best, tgt = dd, m
    zone = zone_id.get(owner.get(low))
    pop = plots * PROP_PER_PLOT * OR_ASSUMED
    qd = pop * LPCD / 1000.0
    ww = qd * RET_DOM * (1 + (ND_RATIO + GOV_RATIO) * RET_ND / RET_DOM)
    qm = ww / 86.4
    pf = min(1.5 + 1 / math.sqrt(qm), PF_CAP) if qm > 0 else PF_CAP
    sls.append({"xy": low, "plots": plots, "zone": zone or 0, "z": Z[low],
                "qpeak_ls": ww * pf / 86.4, "fm_m": best if tgt else -1})
sls.sort(key=lambda c: -c["plots"])
# cascade consolidation: absorb stations within 1500 m of a larger kept station
kept = []
for c in sls:
    host = next((k for k in kept if math.dist(c["xy"], k["xy"]) < 1500), None)
    if host:
        host["plots"] += c["plots"]; host["qpeak_ls"] += c["qpeak_ls"]
        host["z"] = min(host["z"], c["z"])
    else:
        kept.append(c)
sls = kept
sls.sort(key=lambda c: -c["plots"])
absorbed = sum(1 for c in nx.connected_components(FG) if sum(wt.get(n, 0) for n in c) < SLS_MIN_PLOTS)
log(f"SLS consolidated: {len(sls)} stations (+{absorbed} minor pockets absorbed)")

# ---------- zones: voronoi of nodes dissolved by owner, clipped to built envelope ----------
pts = np.array(nodes)
vor_pts = np.vstack([pts, np.array([[pts[:,0].min()-5e4, pts[:,1].min()-5e4],
                                    [pts[:,0].min()-5e4, pts[:,1].max()+5e4],
                                    [pts[:,0].max()+5e4, pts[:,1].min()-5e4],
                                    [pts[:,0].max()+5e4, pts[:,1].max()+5e4]])])
vor = Voronoi(vor_pts)
zone_cells = {}
for i, n in enumerate(nodes):
    zn = zone_id.get(owner.get(n))
    if not zn: continue
    reg = vor.regions[vor.point_region[i]]
    if -1 in reg or len(reg) < 3: continue
    poly = Polygon(vor.vertices[reg])
    if poly.is_valid and poly.area < 4e6:
        zone_cells.setdefault(zn, []).append(poly)
log("voronoi done")
# built envelope
env = unary_union([Point(x, y).buffer(200) for x, y in cent[::3]])
env = env.buffer(120).buffer(-120).simplify(40)
zone_polys = {}
for zn, cells in zone_cells.items():
    u = unary_union(cells).buffer(1)
    g = u.intersection(env)
    g = g.buffer(80).buffer(-80).simplify(30)
    if g.is_empty: continue
    parts = [g] if g.geom_type == "Polygon" else [p for p in g.geoms if p.area > 5e4]
    if parts: zone_polys[zn] = parts
log(f"zones built: {len(zone_polys)}")

# ---------- zone stats & flows ----------
zone_len, zc = {}, {}
for u, v, d in G.edges(data=True):
    zn = zone_id.get(owner.get(u)) or zone_id.get(owner.get(v))
    if zn: zone_len[zn] = zone_len.get(zn, 0.0) + d["len"]
for nd_, dcl in node_plots.items():
    zn = zone_id.get(owner.get(nd_))
    if not zn: continue
    for c, v in dcl.items():
        zc.setdefault(zn, {}).setdefault(c, 0)
        zc[zn][c] += v
rows = []
for i, (s, n) in enumerate(seeds, start=1):
    cc_ = zc.get(i, {})
    res = cc_.get("Residential", 0); allp = sum(cc_.values())
    pop = res * PROP_PER_PLOT * OR_ASSUMED
    qd = pop * LPCD / 1000.0
    qndg = qd * (ND_RATIO + GOV_RATIO)
    ww = qd * RET_DOM + qndg * RET_ND
    infil = INFIL_L_D_KM * zone_len.get(i, 0) / 1e6
    qadf = ww + infil
    qm = qadf / 86.4
    pf = min(1.5 + 1 / math.sqrt(qm), PF_CAP) if qm > 0 else PF_CAP
    rows.append([i, allp, res, cc_.get("Commercial", 0), cc_.get("Governmental", 0), cc_.get("Industry", 0),
                 int(pop), round(qadf, 1), round(pf, 2), round(qadf * pf, 1),
                 round(zone_len.get(i, 0) / 1000, 2), round(Z[n], 1), int(dist[n])])
with open(os.path.join(W2, "report", "zone_flows.csv"), "w", newline="") as f:
    cw = csv.writer(f)
    cw.writerow(["zone", "plots", "res", "com", "gov", "ind", "pop", "Qadf_m3d", "PF", "Qpeak_m3d", "sewer_km", "outlet_z", "dist_stp_m"])
    cw.writerows(rows)
log(f"flows: Qadf {sum(r[7] for r in rows):.0f} m3/d, peak {sum(r[9] for r in rows):.0f}")

# ---------- write shapefiles ----------
w = shapefile.Writer(os.path.join(W2, "shp", "trunk.shp"))
w.field("CUMPLOTS", "N", 10, 0); w.field("ROLE", "C", 10)
for k, cum in trunk_edges.items():
    w.line([list(edge_geom[k].coords)]); w.record(cum, "main" if k in main_set else "branch")
w.close(); wprj(os.path.join(W2, "shp", "trunk.shp"))

w = shapefile.Writer(os.path.join(W2, "shp", "zone_outlets.shp"))
w.field("ZONE", "N", 4, 0); w.field("PLOTS", "N", 10, 0); w.field("Z", "N", 8, 1)
for i, (s, n) in enumerate(seeds, start=1):
    w.point(*n); w.record(i, zc.get(i, {}) and sum(zc[i].values()) or 0, round(Z[n], 1))
w.close(); wprj(os.path.join(W2, "shp", "zone_outlets.shp"))

w = shapefile.Writer(os.path.join(W2, "shp", "zones.shp"))
w.field("ZONE", "N", 4, 0); w.field("PLOTS", "N", 10, 0); w.field("QADF", "N", 12, 1); w.field("QPEAK", "N", 12, 1)
for zn, parts in sorted(zone_polys.items()):
    row = rows[zn - 1]
    for p in parts:
        w.poly([list(p.exterior.coords)] + [list(i.coords) for i in p.interiors])
        w.record(zn, row[1], row[7], row[9])
w.close(); wprj(os.path.join(W2, "shp", "zones.shp"))

w = shapefile.Writer(os.path.join(W2, "shp", "sls_stations.shp"))
w.field("SLS_ID", "N", 4, 0); w.field("ZONE", "N", 4, 0); w.field("PLOTS", "N", 10, 0)
w.field("Z", "N", 8, 1); w.field("QPEAK_LS", "N", 10, 1); w.field("FM_LEN_M", "N", 10, 0)
for i, c in enumerate(sls, start=1):
    w.point(*c["xy"]); w.record(i, c["zone"], c["plots"], round(c["z"], 1), round(c["qpeak_ls"], 1), int(c["fm_m"]))
w.close(); wprj(os.path.join(W2, "shp", "sls_stations.shp"))

sfs = shapefile.Reader(os.path.join(W1, "shp", "streams_study.shp"))
streams = [(LineString(sr.points), rec[0]) for sr, rec in zip(sfs.iterShapes(), sfs.iterRecords()) if len(sr.points) >= 2]
w = shapefile.Writer(os.path.join(W2, "shp", "wadi_crossings.shp"))
w.field("XING_ID", "N", 6, 0); w.field("STRM_VAL", "N", 8, 0); w.field("ROLE", "C", 10)
seen, nid = [], 0
for k in trunk_edges:
    g = edge_geom[k]; role = "main" if k in main_set else "branch"
    for sg, val in streams:
        if g.distance(sg) > 0: continue
        inter = g.intersection(sg)
        ps = [inter] if inter.geom_type == "Point" else (list(inter.geoms) if inter.geom_type == "MultiPoint" else [])
        for p in ps:
            if any(p.distance(q) < 100 for q in seen): continue
            seen.append(p); nid += 1
            w.point(p.x, p.y); w.record(nid, int(val), role)
w.close(); wprj(os.path.join(W2, "shp", "wadi_crossings.shp"))
log(f"wadi crossings: {nid}")

# ---------- profile ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
mp = paths[main_seed]
ch, zz = [0.0], [Z[mp[0]]]
for a, b in zip(mp[:-1], mp[1:]):
    ch.append(ch[-1] + G[a][b]["len"]); zz.append(Z[b])
ch = np.array(ch) / 1000.0
fig, ax = plt.subplots(figsize=(11, 3.8))
ax.plot(ch, zz, lw=1.3, color="#7a4a1a", label="Ground along main trunk (DTM)")
ax.fill_between(ch, zz, min(zz) - 5, color="#e8d8bf", alpha=0.5)
ax.set_xlabel("Chainage from STP (km)"); ax.set_ylabel("Elevation (m)")
ax.set_title("Main trunk corridor — ground long section (DTM)")
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(W2, "img", "trunk_profile.png"), dpi=150)
log("S3 DONE")
