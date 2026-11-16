"""Nearest-manhole re-assignment of the plot flows, compared with the loads in the model, per year."""
import csv, collections
import geopandas as gpd, numpy as np
from scipy.spatial import cKDTree
PL = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W16\Meeting 2026-09-16\03_Plots_meters\Plots.shp"
INV, DG = r"D:\VBOX\bridge\out\inv_w17", r"D:\VBOX\bridge\out\diag"
nodes = [r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8')) if r['type'] == 'MH']
act = [r for r in nodes if r['active'] == 'True']
xy_all = np.array([[float(r['x']), float(r['y'])] for r in nodes]); lab_all = [r['label'] for r in nodes]
xy_act = np.array([[float(r['x']), float(r['y'])] for r in act]); lab_act = [r['label'] for r in act]
g = gpd.read_file(PL); c = g.geometry.representative_point()
P = np.c_[c.x, c.y]
d_all, i_all = cKDTree(xy_all).query(P); d_act, i_act = cKDTree(xy_act).query(P)
print(f"plots {len(g)}; nearest-manhole distance median {np.median(d_all):.0f} m, 95% {np.percentile(d_all,95):.0f} m, max {d_all.max():.0f} m")
inactive_share = sum(1 for k in i_all if not lab_all[k].startswith('O'))
print("plots whose nearest manhole is inactive (absorption-well areas):", inactive_share)
years = {'2030': 'Q_2030', '2040': 'Q_2040', '2050': 'Q_2050', '2055': 'Q_2055', '2060': 'Q_2060', '2070': 'Q_SAT'}
for y, col in years.items():
    q = g[col].astype(float).values
    model = collections.defaultdict(float)
    for r in csv.DictReader(open(DG + rf"\rows_{y}.csv", encoding='utf-8')):
        model[r['label']] += float(r['base_m3d'])
    mine = collections.defaultdict(float)
    for k, v in zip(i_all, q): mine[lab_all[k]] += v
    labs = set(model) | set(mine)
    diff = sorted(((model[l] - mine[l], l) for l in labs), key=lambda t: t[0])
    within = sum(1 for l in labs if abs(model[l] - mine[l]) <= 0.01 * max(mine[l], 0.01) + 0.01)
    far = d_all > 300
    print(f"{y}: plots {q.sum():9.1f}  model {sum(model.values()):9.1f}  diff {sum(model.values())-q.sum():8.1f} m3/d | manholes matching within 1%: {within}/{len(labs)} | flow of plots >300 m from any manhole: {q[far].sum():7.1f}")
    print("     largest shortfalls (model - nearest-plot sum):", ", ".join(f"{l} {d:.1f}" for d, l in diff[:5]))

# --- where is the year shortfall? model minus nearest-manhole sum, by subnetwork and by settlement
sub = lambda l: l.split('-M')[0] if l.startswith('O') and '-M' in l else 'inactive'
res = {}
for y, col in years.items():
    q = g[col].astype(float).values
    model = collections.defaultdict(float)
    for r in csv.DictReader(open(DG + rf"\rows_{y}.csv", encoding='utf-8')):
        model[sub(r['label'])] += float(r['base_m3d'])
    mine = collections.defaultdict(float)
    for k, v in zip(i_all, q): mine[sub(lab_all[k])] += v
    res[y] = {s: model[s] - mine[s] for s in set(model) | set(mine)}
print("\nmodel - plots by subnetwork, m3/d (2070 shows the assignment noise)")
print(f"{'sub':9s}" + "".join(f"{y:>9s}" for y in years))
for s in sorted(res['2070'], key=lambda s: res['2060'].get(s, 0)):
    print(f"{s:9s}" + "".join(f"{res[y].get(s,0):9.1f}" for y in years))
# by settlement
settle = g['SETTLE'] if 'SETTLE' in g.columns else None
if settle is not None:
    print("\nshare of each settlement's plots that sit near loaded manholes is not testable here; settlement totals of plots:")
