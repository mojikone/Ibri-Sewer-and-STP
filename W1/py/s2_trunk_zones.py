"""S2 — Trunk routing, zone territories, GUD-201 flows, SLS screening, wadi crossings.
All numeric criteria per _BRAIN/02_DESIGN_CRITERIA.md (PAM-GUD-203 pXX / PAM-GUD-201 G1-pXX).
Outputs (W1/shp): trunk.shp, zone_outlets.shp, zones.shp, sls_candidates.shp, wadi_crossings.shp
        (W1/report): zone_flows.csv ; (W1/img): trunk_profile.png
"""
import os, math, csv, time
import numpy as np
import shapefile
import rasterio
import networkx as nx
from shapely.geometry import LineString, Point, MultiPoint, shape as shp_shape
from shapely.ops import unary_union
from scipy.spatial import cKDTree

W = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W1"
PRJ = open(os.path.join(W, "shp", "roads_graph.prj")).read()
STP = (444387.0, 2563352.5)                      # existing STP (BRAIN 03)
OR_ASSUMED = 6.0        # persons/housing unit  [GAP-5] pending NCSI
PROP_PER_PLOT = 1.0     # avg properties/plot   [GAP-5]
LPCD = 164.0            # l/c/d Adh Dhahirah    G1-p60
ND_RATIO, GOV_RATIO = 0.22, 0.14                 # G1-p60
RET_DOM, RET_ND = 0.85, 0.54                     # G1-p71
INFIL_L_D_KM = 720.0                             # G1-p72 (new networks)
PF_CAP = 5.0                                     # G1-p72
MAX_COVER = 12.0        # m, p33 (10-12; use upper bound for screening)
MIN_COVER_INV = 1.9     # m start invert below ground: 1.3 cover + ~0.6 pipe/bed (p33)
# Table 11 minimum gradients (p29), applied by cumulative-plots pipe-class proxy
def smin_for(plots_upstream):
    if plots_upstream < 150:   return 0.0050   # DN200
    if plots_upstream < 400:   return 0.0027   # DN315
    if plots_upstream < 1500:  return 0.00155  # DN500
    if plots_upstream < 5000:  return 0.0010   # DN700
    return 0.00075                             # DN>=900 (trunk)

t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

# ---------- graph ----------
r = shapefile.Reader(os.path.join(W, "shp", "roads_graph.shp"))
G = nx.Graph()
edge_geom = {}
for sr, rec in zip(r.iterShapes(), r.iterRecords()):
    pts = sr.points
    a, b = (round(pts[0][0], 1), round(pts[0][1], 1)), (round(pts[-1][0], 1), round(pts[-1][1], 1))
    if a == b: continue
    L, btw, dual, art = rec[0], rec[1], rec[2], rec[3]
    rf = 0.55 if dual else (0.70 if art else 1.0)   # arterial preference / straightness
    if G.has_edge(a, b) and G[a][b]["len"] <= L: continue
    G.add_edge(a, b, len=L, rf=rf, dual=dual, art=art)
    edge_geom[(a, b)] = LineString(pts)
cc = max(nx.connected_components(G), key=len)
G = G.subgraph(cc).copy()
nodes = list(G.nodes)
log(f"graph {len(nodes)} nodes / {G.number_of_edges()} edges")

# ---------- DEM z at nodes ----------
ds = rasterio.open(os.path.join(W, "temp", "DEM_study.tif"))
arr = ds.read(1)
def zval(x, y):
    try:
        rr, cc_ = ds.index(x, y)
        v = arr[rr, cc_]
        return float(v) if v > -1e30 else None
    except Exception:
        return None
Z = {}
for n in nodes:
    v = zval(*n)
    Z[n] = v
# fill missing with neighbor mean
for n in nodes:
    if Z[n] is None:
        vs = [Z[m] for m in G[n] if Z.get(m) is not None]
        Z[n] = float(np.mean(vs)) if vs else 350.0
log("DEM sampled")

# ---------- plots -> nearest node ----------
sf = shapefile.Reader(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\SHP\Landuse\Landuse.shp")
fields = [f[0] for f in sf.fields[1:]]
i_cls = fields.index("NewLUClass")
SERV = {"Residential", "Commercial", "Governmental", "Industry"}
cent, cls_l, area_l = [], [], []
for sr, rec in zip(sf.iterShapes(), sf.iterRecords()):
    if rec[i_cls] not in SERV: continue
    xs = [p[0] for p in sr.points]; ys = [p[1] for p in sr.points]
    cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
    cent.append((cx, cy)); cls_l.append(rec[i_cls])
    bb = sr.bbox; area_l.append(abs((bb[2]-bb[0])*(bb[3]-bb[1])))
cent = np.array(cent)
tree = cKDTree(np.array(nodes))
d_, idx_ = tree.query(cent, distance_upper_bound=400.0)
node_plots = {}   # node -> {class: count}
ok = 0
for k, (di, ii) in enumerate(zip(d_, idx_)):
    if not np.isfinite(di) or ii >= len(nodes): continue
    n = nodes[ii]; ok += 1
    node_plots.setdefault(n, {}).setdefault(cls_l[k], 0)
    node_plots[n][cls_l[k]] += 1
tot_by_cls = {}
for d in node_plots.values():
    for c, v in d.items(): tot_by_cls[c] = tot_by_cls.get(c, 0) + v
log(f"plots assigned {ok}/{len(cent)} -> {tot_by_cls}")
wt = {n: sum(d.values()) for n, d in node_plots.items()}

# ---------- STP node: connector edge from STP point to nearest node ----------
d0, i0 = tree.query(np.array([STP]))
near = nodes[int(i0[0])]
stp_node = (round(STP[0], 1), round(STP[1], 1))
G.add_edge(stp_node, near, len=float(d0[0]), rf=0.55, dual=0, art=1)
edge_geom[(stp_node, near)] = LineString([STP, near])
Z[stp_node] = zval(*STP) or Z[near]
log(f"STP connector {d0[0]:.0f} m to network, STP z={Z[stp_node]:.1f}")

# ---------- Dijkstra from STP (routing cost) ----------
BETA = 400.0  # m equivalent per m of adverse rise (1 m lift ~ 1000 m @1permil; conservative)
def wcost(u, v, d):
    # expanding away from STP: flow v->u; adverse when z downstream(u side, nearer STP) > z upstream
    rise = max(0.0, Z[u] - Z[v]) if False else 0.0
    return d["len"] * d["rf"]
# NOTE on adverse-grade: undirected Dijkstra cannot orient rise per-expansion here;
# handled instead by explicit profile check + SLS screening downstream.
dist, paths = nx.single_source_dijkstra(G, stp_node, weight=lambda u, v, d: d["len"] * d["rf"])
reach = set(dist)
log(f"dijkstra reach {len(reach)}/{len(nodes)}")

# ---------- seeds: 1km cells, top plot weights ----------
cellw = {}
for n, w_ in wt.items():
    if n not in reach: continue
    k = (int(n[0] // 1000), int(n[1] // 1000))
    cellw.setdefault(k, []).append((w_, n))
cands = []
for k, lst in cellw.items():
    s = sum(w for w, _ in lst)
    if s >= 20:
        lst.sort(reverse=True)
        cands.append((s, lst[0][1]))
cands.sort(reverse=True)
seeds = []
for s, n in cands:
    if all(math.dist(n, m) > 1500 for _, m in seeds):
        seeds.append((s, n))
    if len(seeds) >= 20: break
log(f"seeds: {len(seeds)}")

# ---------- trunk = union of STP->seed paths ----------
trunk_edges = {}
for s, n in seeds:
    p = paths[n]
    for a, b in zip(p[:-1], p[1:]):
        k = (a, b) if (a, b) in edge_geom else (b, a)
        trunk_edges.setdefault(k, 0)
trunk_nodes = set()
for (a, b) in trunk_edges: trunk_nodes.update((a, b))

# cumulative plots on trunk: route every node's weight down its path if path uses trunk
for n, w_ in wt.items():
    if n not in reach: continue
    p = paths[n]
    for a, b in zip(p[:-1], p[1:]):
        k = (a, b) if (a, b) in edge_geom else (b, a)
        if k in trunk_edges: trunk_edges[k] += w_
main_seed = seeds[0][1]

# ---------- zone territories: nearest seed by network distance ----------
S = [n for _, n in seeds]
md, mpaths = nx.multi_source_dijkstra(G, set(S), weight=lambda u, v, d: d["len"])
owner = {}
for n in reach:
    if n in mpaths and mpaths[n]:
        owner[n] = mpaths[n][0]
zone_id = {n: i for i, (_, n) in enumerate(seeds, start=1)}

# ---------- SLS screening: invert accumulation node->outlet->STP ----------
# acc[b] = plots whose shortest-path tree route passes through b (true junction accumulation)
acc = {n: 0 for n in G.nodes}
for n, w_ in wt.items():
    if n not in reach: continue
    for m in paths[n]:
        acc[m] += w_
sls_nodes = []
zone_len = {}
for u, v, d in G.edges(data=True):
    zn = zone_id.get(owner.get(u)) or zone_id.get(owner.get(v))
    if zn: zone_len[zn] = zone_len.get(zn, 0.0) + d["len"]
for n in reach:
    if wt.get(n, 0) == 0: continue
    p = paths[n]                       # path STP -> n ; reverse = flow route
    fl = list(reversed(p))
    inv = Z[n] - MIN_COVER_INV
    deep = None
    for a, b in zip(fl[:-1], fl[1:]):
        L = G[a][b]["len"]
        inv = min(inv - L * smin_for(max(acc[a], wt.get(n, 0))), Z[b] - MIN_COVER_INV)
        depth = Z[b] - inv
        if depth > MAX_COVER:
            deep = (b, depth); break
    if deep: sls_nodes.append((n, deep[0], deep[1]))
log(f"nodes needing lift: {len(sls_nodes)}")
# cluster SLS nodes (400 m)
sls_pts = []
for n, at, dep in sls_nodes:
    placed = False
    for c in sls_pts:
        if math.dist(n, c["xy"]) < 400:
            c["cnt"] += wt.get(n, 0); c["dep"] = max(c["dep"], dep); placed = True; break
    if not placed:
        sls_pts.append({"xy": n, "cnt": wt.get(n, 0), "dep": dep, "z": Z[n]})
sls_pts = [c for c in sls_pts if c["cnt"] >= 10]
log(f"SLS candidate clusters: {len(sls_pts)}")

# ---------- outputs ----------
def wprj(path):
    with open(path.replace(".shp", ".prj"), "w") as f: f.write(PRJ)

# trunk
w = shapefile.Writer(os.path.join(W, "shp", "trunk.shp"))
w.field("CUMPLOTS", "N", 10, 0); w.field("ROLE", "C", 10); w.field("DUAL", "N", 1, 0)
main_path = paths[main_seed]
main_set = set()
for a, b in zip(main_path[:-1], main_path[1:]):
    main_set.add((a, b) if (a, b) in edge_geom else (b, a))
for k, cum in trunk_edges.items():
    g = edge_geom[k]
    w.line([list(g.coords)])
    w.record(cum, "main" if k in main_set else "branch", G[k[0]][k[1]]["dual"])
w.close(); wprj(os.path.join(W, "shp", "trunk.shp"))

# outlets (seeds)
w = shapefile.Writer(os.path.join(W, "shp", "zone_outlets.shp"))
w.field("ZONE", "N", 4, 0); w.field("PLOTS_1KM", "N", 10, 0); w.field("Z", "N", 8, 1)
w.field("DIST_STP", "N", 10, 0); w.field("DROP_M", "N", 8, 1)
for i, (s, n) in enumerate(seeds, start=1):
    w.point(*n)
    w.record(i, s, Z[n], int(dist[n]), round(Z[n] - Z[stp_node], 1))
w.close(); wprj(os.path.join(W, "shp", "zone_outlets.shp"))

# zones: dissolve voronoi-ish via plot buffers per territory
zone_geoms = {}
for k, (cx, cy) in enumerate(cent):
    di, ii = d_[k], idx_[k]
    if not np.isfinite(di) or ii >= len(nodes): continue
    zn = zone_id.get(owner.get(nodes[ii]))
    if zn: zone_geoms.setdefault(zn, []).append(Point(cx, cy))
w = shapefile.Writer(os.path.join(W, "shp", "zones.shp"))
w.field("ZONE", "N", 4, 0); w.field("NPLOTS", "N", 10, 0); w.field("AREA_KM2", "N", 10, 3)
w.field("SEWER_KM", "N", 10, 2)
zone_stats = {}
for zn, pts in sorted(zone_geoms.items()):
    hull = unary_union([p.buffer(120) for p in pts]).buffer(-60).simplify(20)
    if hull.is_empty: continue
    polys = [hull] if hull.geom_type == "Polygon" else list(hull.geoms)
    polys = [p for p in polys if p.area > 30000]
    if not polys: continue
    for p in polys:
        w.poly([list(p.exterior.coords)])
        w.record(zn, len(pts), round(p.area / 1e6, 3), round(zone_len.get(zn, 0) / 1000, 2))
    zone_stats[zn] = {"plots": len(pts), "area": sum(p.area for p in polys) / 1e6}
w.close(); wprj(os.path.join(W, "shp", "zones.shp"))

# flows per zone (GUD-201 chain)
rows = []
for zn, (s, n) in zip(range(1, len(seeds) + 1), seeds):
    npl = zone_stats.get(zn, {}).get("plots", 0)
    # class split at territory level
    ccounts = {}
    for nd_, d in node_plots.items():
        if zone_id.get(owner.get(nd_)) == zn:
            for c, v in d.items(): ccounts[c] = ccounts.get(c, 0) + v
    res = ccounts.get("Residential", 0)
    pop = res * PROP_PER_PLOT * OR_ASSUMED
    q_dom = pop * LPCD / 1000.0                      # m3/d
    q_nd  = q_dom * ND_RATIO
    q_gov = q_dom * GOV_RATIO
    ww = q_dom * RET_DOM + (q_nd + q_gov) * RET_ND   # m3/d
    infil = INFIL_L_D_KM * zone_len.get(zn, 0) / 1000.0 / 1000.0  # m3/d
    qadf = ww + infil
    qm_ls = qadf / 86.4
    pf = min(1.5 + 1.0 / math.sqrt(qm_ls), PF_CAP) if qm_ls > 0 else PF_CAP
    rows.append([zn, npl, res, ccounts.get("Commercial", 0), ccounts.get("Governmental", 0),
                 ccounts.get("Industry", 0), int(pop), round(q_dom, 1), round(q_nd + q_gov, 1),
                 round(infil, 1), round(qadf, 1), round(pf, 2), round(qadf * pf, 1),
                 round(zone_len.get(zn, 0) / 1000, 2), round(Z[n], 1), int(dist[n])])
os.makedirs(os.path.join(W, "report"), exist_ok=True)
with open(os.path.join(W, "report", "zone_flows.csv"), "w", newline="") as f:
    cw = csv.writer(f)
    cw.writerow(["zone", "plots_all", "res", "com", "gov", "ind", "pop[GAP-5 OR=6]",
                 "Qdom_m3d", "Qnd+gov_m3d", "Qinfil_m3d", "Qadf_m3d", "PF_peltier",
                 "Qpeak_m3d", "sewer_km", "outlet_z", "netdist_stp_m"])
    cw.writerows(rows)
tot = [sum(r[i] for r in rows) for i in (10, 12)]
log(f"flows: Qadf_total={tot[0]:.0f} m3/d  Qpeak_total={tot[1]:.0f} m3/d (zones, pre-STP margin)")

# SLS candidates
w = shapefile.Writer(os.path.join(W, "shp", "sls_candidates.shp"))
w.field("PLOTS", "N", 10, 0); w.field("MAXDEPTH", "N", 8, 1); w.field("Z", "N", 8, 1)
for c in sls_pts:
    w.point(*c["xy"]); w.record(c["cnt"], round(c["dep"], 1), round(c["z"], 1))
w.close(); wprj(os.path.join(W, "shp", "sls_candidates.shp"))

# wadi crossings: trunk x streams
sfs = shapefile.Reader(os.path.join(W, "shp", "streams_study.shp"))
stream_geoms = []
for sr, rec in zip(sfs.iterShapes(), sfs.iterRecords()):
    if len(sr.points) >= 2: stream_geoms.append((LineString(sr.points), rec[0]))
trunk_union = [edge_geom[k] for k in trunk_edges]
w = shapefile.Writer(os.path.join(W, "shp", "wadi_crossings.shp"))
w.field("STRM_VAL", "N", 8, 0); w.field("ROLE", "C", 10)
ncr = 0
seen = []
for k in trunk_edges:
    g = edge_geom[k]
    role = "main" if k in main_set else "branch"
    for sg, val in stream_geoms:
        if g.distance(sg) > 0: continue
        inter = g.intersection(sg)
        pts = []
        if inter.geom_type == "Point": pts = [inter]
        elif inter.geom_type == "MultiPoint": pts = list(inter.geoms)
        for p in pts:
            if any(p.distance(q) < 100 for q in seen): continue
            seen.append(p); ncr += 1
            w.point(p.x, p.y); w.record(int(val), role)
w.close(); wprj(os.path.join(W, "shp", "wadi_crossings.shp"))
log(f"wadi crossings on trunk: {ncr}")

# trunk long profile (main path)
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ch, zz = [0.0], [Z[main_path[0]]]
    for a, b in zip(main_path[:-1], main_path[1:]):
        ch.append(ch[-1] + G[a][b]["len"]); zz.append(Z[b])
    ch = np.array(ch) / 1000.0
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(ch, zz, lw=1.2, color="#8a5a2a", label="Ground (NSA DSM — screening only)")
    ax.plot([ch[0], ch[-1]], [zz[0], zz[0] - (ch[-1] - ch[0]) * 0.75],
            "--", color="#1a5f9a", label="0.75 m/km ref. grade (Tab 11, DN>=900)")
    ax.set_xlabel("Chainage from STP (km)"); ax.set_ylabel("Elevation (m)")
    ax.set_title("Main trunk — indicative long section (STP -> main settlement)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(W, "img", "trunk_profile.png"), dpi=150)
    log("profile saved")
except Exception as e:
    log(f"profile failed: {e}")
log("S2 DONE")
