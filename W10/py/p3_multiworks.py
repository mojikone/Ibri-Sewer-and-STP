"""Does more than one works remove the pumping?

A lifting station exists because sewage has to travel further than the ground will carry
it. A second works closer to the load does the same job as a station, and it also treats.
This measures the trade directly: every candidate site from the Phase 4.3 siting study is
made an outlet, the network drains to whichever it can reach, and the stations are counted.

The sites are already screened for land, odour buffer, flood and access, so these are not
arbitrary points on a map.
"""
import os, sys, warnings, itertools
from collections import defaultdict
import geopandas as gpd, networkx as nx, numpy as np, pandas as pd
from shapely.geometry import Point
sys.path.insert(0, '.'); sys.path.insert(0, r'D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W8\py')
import config as C, netlib as N
from p2_depths import MIN_COVER_CROWN
from p2_sizing import assign_loads, accumulate
from p3_optimise import size_network, lay
from p3_variants import stations, Q50
warnings.filterwarnings('ignore')

G, xy, lines, z = N.load_network()
comps = sorted(nx.connected_components(G), key=len, reverse=True); G = G.subgraph(comps[0]).copy()
q_node, _, _ = assign_loads(xy, list(G.nodes))
D = N.sewer_cost(G, z)
R = D.reverse(copy=False)

cand = gpd.read_file(os.path.join(C.OUT_SHP, 'W10_stp_candidates.shp'))
site_node = {}
for _, r in cand.iterrows():
    n, _d = N.nearest_node(xy, (r.X, r.Y), nodes=comps[0])
    site_node[r.SITE] = n
site_node['WEST'] = N.nearest_node(xy, (442091.75, 2569063.87), nodes=comps[0])[0]

def solve(sinks):
    """Multi-sink: a super-sink joined to every works at zero cost."""
    Rx = R.copy()
    SUPER = ('SUPER',)
    for s in sinks:
        Rx.add_edge(SUPER, s, w=0.0)
    cost, paths = nx.single_source_dijkstra(Rx, SUPER, weight='w')
    nxt = {}
    for n, p in paths.items():
        if n == SUPER or len(p) < 3:
            continue
        nxt[n] = p[-2]
    qacc, lacc, order = accumulate(G, nxt, q_node)
    pipes = size_network(G, nxt, qacc, lacc, {})
    inv, dep, lifts, cov, pre = lay(G, z, nxt, order, pipes)
    cl, real, lift = stations(lifts, qacc, lacc, xy) if lifts else (0, 0, 0.0)
    flows = {s: round(qacc.get(s, 0)) for s in sinks}
    return len(lifts), cl, real, round(lift), flows

combos = [
    ('existing works only', ['EXISTING']),
    ('southern site only', ['SOUTH']),
    ('S1 only', ['S1']),
    ('existing + west satellite', ['EXISTING', 'WEST']),
    ('existing + S6 (east)', ['EXISTING', 'S6']),
    ('existing + west + S6', ['EXISTING', 'WEST', 'S6']),
    ('south + west + S6', ['SOUTH', 'WEST', 'S6']),
    ('S1 + west + S6', ['S1', 'WEST', 'S6']),
    ('existing + west + S6 + S10', ['EXISTING', 'WEST', 'S6', 'S10']),
    ('five works', ['EXISTING', 'WEST', 'S6', 'S10', 'S8']),
]
rows = []
for tag, sites in combos:
    sinks = [site_node[s] for s in sites if s in site_node]
    b, cl, real, lift, flows = solve(sinks)
    rows.append({'scheme': tag, 'works': len(sinks), 'breaches': b,
                 'clusters': cl, 'stations': real, 'lift_m': lift})
    fl = '  '.join('%s %s' % (s, f'{v:,}') for s, v in zip(sites, flows.values()))
    print('%-30s works %d  breaches %4d  STATIONS %3d  lift %6d m   | %s'
          % (tag, len(sinks), b, real, lift, fl))
pd.DataFrame(rows).to_csv(os.path.join(C.OUT_RUN, 'p3_multiworks.csv'), index=False)
