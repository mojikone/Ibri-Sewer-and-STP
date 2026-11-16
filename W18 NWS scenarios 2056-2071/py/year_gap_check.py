"""Test: are the plots missing from the year loads the ones near the deactivated (inactive-topology) manholes?"""
import csv, collections
import geopandas as gpd, numpy as np
from scipy.spatial import cKDTree
PL = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W16\Meeting 2026-09-16\03_Plots_meters\Plots.shp"
INV, DG = r"D:\VBOX\bridge\out\inv_w17", r"D:\VBOX\bridge\out\diag"
nodes = [r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8')) if r['type'] == 'MH']
xy = np.array([[float(r['x']), float(r['y'])] for r in nodes]); lab = [r['label'] for r in nodes]
act = np.array([r['active'] == 'True' for r in nodes])
g = gpd.read_file(PL); c = g.geometry.representative_point(); P = np.c_[c.x, c.y]
d_all, i_all = cKDTree(xy).query(P)
d_act, _ = cKDTree(xy[act]).query(P)
d_ina, _ = cKDTree(xy[~act]).query(P)
near_inactive = ~act[i_all]
gap = {'2030': 2427.7, '2040': 2778.0, '2050': 3139.5, '2055': 3361.8, '2060': 3488.8}
print("inactive manholes:", int((~act).sum()))
print(f"{'year':5s} {'shortfall':>9s} {'plots nearest an inactive MH':>29s} {'plots within 500 m of one':>26s}")
for y, s in gap.items():
    q = g[f'Q_{y}'].astype(float).values
    print(f"{y:5s} {s:9.1f} {q[near_inactive].sum():29.1f} {q[d_ina < 500].sum():26.1f}")
# plot-level: manholes where the model's 2070 load equals the nearest-plot sum (same plots), 2030 short by exactly one plot?
def model(y):
    m = collections.defaultdict(float)
    for r in csv.DictReader(open(DG + rf"\rows_{y}.csv", encoding='utf-8')): m[r['label']] += float(r['base_m3d'])
    return m
m70, m30 = model('2070'), model('2030')
byMH = collections.defaultdict(list)
for k, idx in enumerate(i_all): byMH[lab[idx]].append(k)
q70, q30 = g['Q_SAT'].astype(float).values, g['Q_2030'].astype(float).values
same, short_mh, single, missing_plots = 0, 0, 0, []
for l, ks in byMH.items():
    s70 = q70[ks].sum()
    if s70 <= 0 or abs(m70.get(l, 0) - s70) > 0.005 * s70: continue
    same += 1
    d = q30[ks].sum() - m30.get(l, 0)
    if d > 0.01:
        short_mh += 1
        hit = [k for k in ks if abs(q30[k] - d) <= 0.01 * max(d, 0.01)]
        if hit: single += 1; missing_plots.append(hit[0])
print(f"\nmanholes whose 2070 load equals their nearest plots: {same}; of these short in 2030: {short_mh}; short by exactly one plot: {single}")
mp = g.iloc[missing_plots]
print("the missing plots:", len(mp), " Q_2030 sum", round(mp['Q_2030'].astype(float).sum(), 1))
for col in ['SETTLE', 'STATUS', 'USE', 'FULL_YEAR']:
    print(f"  by {col}:", mp.groupby(col)['Q_2030'].agg(['count', 'sum']).round(1).sort_values('sum', ascending=False).head(6).to_dict('index'))
print("  their distance to the nearest inactive manhole: median", round(float(np.median(d_ina[missing_plots]))), "m")
print("  POP_2030 of the missing plots: zero", int((mp['POP_2030'].astype(float) == 0).sum()), " non-zero", int((mp['POP_2030'].astype(float) > 0).sum()))
print("  Q_2024 equal to Q_2030 (existing, no growth):", int((mp['Q_2024'].astype(float).round(4) == mp['Q_2030'].astype(float).round(4)).sum()))

# --- are the missing plots far from any active manhole (no pipe laid near them)?
far = lambda d: f"median {np.median(d):.0f} m, 75% {np.percentile(d,75):.0f} m, share > 150 m {100*(d>150).mean():.0f}%"
print("\ndistance to the nearest ACTIVE manhole")
print("  the 783 missing plots :", far(d_act[missing_plots]))
print("  all plots with flow in 2030:", far(d_act[q30 > 0]))
gov = g['USE'].isin(['Government'])
print("  government plots west of x=440000, Q_SAT:", round(g.loc[gov & (P[:,0] < 440000), 'Q_SAT'].astype(float).sum(), 1), "m3/d")
