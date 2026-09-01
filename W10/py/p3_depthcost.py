"""Does routing on DEPTH GAINED instead of length reduce the stations?

Depth accumulates on an edge as (pipe gradient x length) minus (ground fall). An edge
whose ground falls faster than the pipe needs costs NOTHING in depth; a flat edge costs
the full gradient. So the quantity to minimise on the way to the works is not distance and
not climb - it is depth gained. That is what puts a chamber past 12 m.
"""
import os, sys, warnings, time
from collections import defaultdict
import geopandas as gpd, networkx as nx, numpy as np, pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union
sys.path.insert(0, '.'); sys.path.insert(0, r'D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W8\py')
import config as C, netlib as N
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH
from p2_sizing import assign_loads, accumulate
from p3_optimise import size_network, lay, controlling_run, flattest_for, EPS
from p3_variants import stations, flatten_pass, Q50
from sewnet import hydra
from sewnet.criteria import DEFAULT as CRIT
warnings.filterwarnings('ignore')

G, xy, lines, z = N.load_network()
comps = sorted(nx.connected_components(G), key=len, reverse=True); G = G.subgraph(comps[0]).copy()
sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
q_node, _, _ = assign_loads(xy, list(G.nodes))

def depth_tree(sref, tie=0.02):
    """Dijkstra on depth gained. `sref` is the reference pipe gradient."""
    D = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        L = d['len']
        zu, zv = z.get(u, np.nan), z.get(v, np.nan)
        fall_uv = (zu - zv) if np.isfinite(zu) and np.isfinite(zv) else 0.0
        D.add_edge(u, v, w=max(0.0, sref * L - fall_uv) + tie * L / 1000.0, len=L)
        D.add_edge(v, u, w=max(0.0, sref * L + fall_uv) + tie * L / 1000.0, len=L)
    R = D.reverse(copy=False)
    cost, paths = nx.single_source_dijkstra(R, sink, weight='w')
    return {n: p[-2] for n, p in paths.items() if len(p) > 1}

rows = []
for label, sref in [('depth-cost @0.50%', 0.0050), ('depth-cost @0.30%', 0.0030),
                    ('depth-cost @0.20%', 0.0020), ('depth-cost @0.10%', 0.0010)]:
    for flat in (False, True):
        nxt = depth_tree(sref)
        qacc, lacc, order = accumulate(G, nxt, q_node)
        ups = defaultdict(list)
        for n, m in nxt.items(): ups[m].append(n)
        dnf = flatten_pass(G, z, nxt, order, qacc, lacc, ups) if flat else None
        pipes = size_network(G, nxt, qacc, lacc, dnf or {})
        inv, dep, lifts, cov, pre = lay(G, z, nxt, order, pipes)
        cl, real, lift = stations(lifts, qacc, lacc, xy)
        up = sum(G[n][m]['len'] for (n, m), d in pipes.items() if d['DN'] > 200) / 1000
        km = sum(G[n][m]['len'] for n, m in pipes) / 1000
        tag = label + (' + flatten' if flat else '')
        rows.append({'strategy': tag, 'breaches': len(lifts), 'clusters': cl,
                     'stations': real, 'lift_m': round(lift), 'pipe_km': round(km, 1),
                     'km_over_DN200': round(up, 1)})
        print('%-28s breaches %4d  clusters %3d  STATIONS %3d  lift %6d m  pipe %7.1f km  >DN200 %6.1f km'
              % (tag, len(lifts), cl, real, round(lift), km, up))
pd.DataFrame(rows).to_csv(os.path.join(C.OUT_RUN, 'p3_depthcost.csv'), index=False)
