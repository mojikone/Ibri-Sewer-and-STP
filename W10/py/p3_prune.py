"""What does the network cost to serve its emptiest branches?

Many breaches sit on long corridors through open ground carrying almost no flow - the
scattered settlements the skeletoniser reached. Sewering them at all is a design decision,
not a hydraulic necessity: the guideline's own economic trigger and the project's options
doctrine both allow a decentralised answer for outlying settlements. This measures what
each tranche of them costs in pumping.

A branch is pruned when the flow ACCUMULATING through it is below the threshold, working
from the heads down, so pruning never cuts off anything larger downstream.
"""
import os, sys, warnings
from collections import defaultdict
import geopandas as gpd, networkx as nx, numpy as np, pandas as pd
from shapely.geometry import Point
sys.path.insert(0, '.'); sys.path.insert(0, r'D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W8\py')
import config as C, netlib as N
from p1_subnetworks import flow_tree
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH
from p2_sizing import assign_loads, accumulate
from p3_optimise import size_network, lay, od
from p3_variants import stations, Q50
warnings.filterwarnings('ignore')

G, xy, lines, z = N.load_network()
comps = sorted(nx.connected_components(G), key=len, reverse=True); G = G.subgraph(comps[0]).copy()
sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
cost, nxt, D = flow_tree(G, z, sink)
q_node, _, _ = assign_loads(xy, list(G.nodes))
qacc0, lacc0, order0 = accumulate(G, nxt, q_node)
plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)

rows = []
for thr in (0.0, 1.0, 3.0, 5.0, 10.0, 20.0):
    keep = {n for n in order0 if qacc0[n] >= thr}
    keep.add(sink)
    nxt2 = {n: m for n, m in nxt.items() if n in keep and m in keep}
    order2 = [n for n in order0 if n in keep]
    qacc, lacc, _ = accumulate(G, nxt2, {k: v for k, v in q_node.items() if k in keep})
    pipes = size_network(G, nxt2, qacc, lacc, {})
    inv, dep, lifts, cov, pre = lay(G, z, nxt2, order2, pipes)
    cl, real, lift = stations(lifts, qacc, lacc, xy) if lifts else (0, 0, 0.0)
    km = sum(G[n][m]['len'] for n, m in pipes) / 1000
    served = sum(qacc0[n] for n in keep if n not in nxt2 or True)
    arriving = qacc[sink] if sink in qacc else 0
    dropped_km = 1883.6 - km
    rows.append({'threshold_m3d': thr, 'pipe_km': round(km, 1),
                 'km_dropped': round(dropped_km, 1),
                 'flow_at_works': round(arriving), 'breaches': len(lifts),
                 'clusters': cl, 'stations': real, 'lift_m': round(lift)})
    print('drop branches under %5.1f m3/d : pipe %7.1f km (-%6.1f)  flow %6d m3/d  '
          'breaches %4d  STATIONS %3d  lift %6d m'
          % (thr, km, dropped_km, arriving, len(lifts), real, round(lift)))
pd.DataFrame(rows).to_csv(os.path.join(C.OUT_RUN, 'p3_prune.csv'), index=False)
