"""The 12 m limit measured as the guideline states it: COVER to the crown.

G203 p33 verbatim: "The recommended maximum cover for sewer pipes is approximately 10 -
12m ... Where the cost of excavation becomes prohibitive the Engineer shall incorporate
pumping stations into the design."

The W10 code tested ground minus INVERT against 12.00 m. Cover is ground minus CROWN, which
is one outside diameter shallower. So every reach has been held to a limit stricter than
the guideline by its own diameter - 0.30 m at DN200, 1.30 m at DN1200. Correcting it is not
a relaxation of anything; it is measuring the quantity the guideline names.

Reported alongside: how many breaches sit in the 12-14 m cover band, because the project
rule is a HARD 12 m with no exemption (settled after 21.3 m chambers passed an audit) while
the guideline's own wording is a recommendation with an economic trigger. That number is
for the user to decide on, not for this script to assume.
"""
import os, sys, warnings
from collections import defaultdict
import geopandas as gpd, networkx as nx, numpy as np, pandas as pd
from shapely.geometry import Point
sys.path.insert(0, '.'); sys.path.insert(0, r'D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W8\py')
import config as C, netlib as N
from p1_subnetworks import flow_tree
from p2_depths import MIN_COVER_CROWN
from p2_sizing import assign_loads, accumulate
from p3_optimise import size_network, od
from p3_variants import stations, Q50
warnings.filterwarnings('ignore')

G, xy, lines, z = N.load_network()
comps = sorted(nx.connected_components(G), key=len, reverse=True); G = G.subgraph(comps[0]).copy()
sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
cost, nxt, D = flow_tree(G, z, sink)
q_node, _, _ = assign_loads(xy, list(G.nodes))
qacc, lacc, order = accumulate(G, nxt, q_node)
ups = defaultdict(list)
for n, m in nxt.items(): ups[m].append(n)
pipes = size_network(G, nxt, qacc, lacc, {})

def solve(limit, measure):
    """measure='invert' -> ground-invert;  measure='cover' -> ground-crown."""
    invert, lifts, cover_at = {}, {}, {}
    for n in order:
        zn = z.get(n, np.nan)
        if not np.isfinite(zn): continue
        dns = [pipes[(u, n)]['DN'] for u in ups.get(n, ()) if (u, n) in pipes]
        if n in nxt and (n, nxt[n]) in pipes: dns.append(pipes[(n, nxt[n])]['DN'])
        dn_here = max(dns) if dns else 200
        shallow = zn - MIN_COVER_CROWN - od(dn_here)
        cand = [shallow]
        for u in ups.get(n, ()):
            p = pipes.get((u, n))
            if u in invert and p is not None and G.has_edge(u, n):
                cand.append(invert[u] - p['S'] * G[u][n]['len'])
        iv = min(cand)
        d_inv = zn - iv
        d_cov = d_inv - od(dn_here)
        d = d_inv if measure == 'invert' else d_cov
        cover_at[n] = d_cov
        if d > limit:
            lifts[n] = d - (zn - shallow if measure == 'invert' else zn - shallow - od(dn_here))
            iv = shallow
        invert[n] = iv
    return lifts, cover_at

rows = []
for label, limit, measure in [('12.0 m to INVERT  (as coded)', 12.0, 'invert'),
                              ('12.0 m COVER      (as G203 p33 states)', 12.0, 'cover'),
                              ('10.0 m COVER      (lower end of the range)', 10.0, 'cover'),
                              ('14.0 m COVER      (information only)', 14.0, 'cover')]:
    lifts, cov = solve(limit, measure)
    cl, real, lift = stations(lifts, qacc, lacc, xy) if lifts else (0, 0, 0.0)
    rows.append({'rule': label, 'breaches': len(lifts), 'clusters': cl,
                 'stations': real, 'total_lift_m': round(lift)})
    print('%-42s breaches %4d  clusters %3d  STATIONS %3d  lift %6d m'
          % (label, len(lifts), cl, real, round(lift)))

# how marginal are the breaches, in COVER terms
lifts, cov = solve(12.0, 'invert')
c = np.array([cov[n] for n in lifts])
print('\nthe 219 breaches, measured as COVER:')
for lo, hi in [(0, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 99)]:
    print('   cover %4.1f - %-4.1f m : %4d' % (lo, hi, int(((c >= lo) & (c < hi)).sum())))
pd.DataFrame(rows).to_csv(os.path.join(C.OUT_RUN, 'p3_cover_rule.csv'), index=False)
