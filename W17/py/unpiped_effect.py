"""What the plots far from any laid pipe add, per year: load on inactive manholes (drops out) and plots far from active manholes."""
import csv, collections
import geopandas as gpd, numpy as np
from scipy.spatial import cKDTree
PL = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W16\Meeting 2026-09-16\03_Plots_meters\Plots.shp"
INV, R4 = r"D:\VBOX\bridge\out\inv_w17", r"D:\VBOX\bridge\out\r4\diag"
nodes = [r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8')) if r['type'] == 'MH' and r['active'] == 'True']
xy = np.array([[float(r['x']), float(r['y'])] for r in nodes])
g = gpd.read_file(PL); c = g.geometry.representative_point(); P = np.c_[c.x, c.y]
d, _ = cKDTree(xy).query(P)
years = {'2030': 'Q_2030', '2040': 'Q_2040', '2050': 'Q_2050', '2055': 'Q_2055', '2060': 'Q_2060', '2070': 'Q_SAT'}
print(f"{'year':5s} {'total':>9s} {'on inactive MH':>15s} {'plots >150 m':>13s} {'plots >500 m':>13s} {'plots >1 km':>12s}   m3/d")
for y, col in years.items():
    inact = sum(float(r['base_m3d']) for r in csv.DictReader(open(R4 + rf"\rows_{y}.csv", encoding='utf-8')) if not r['label'].startswith('O'))
    q = g[col].astype(float).values
    print(f"{y:5s} {q.sum():9.1f} {inact:15.1f} {q[d>150].sum():13.1f} {q[d>500].sum():13.1f} {q[d>1000].sum():12.1f}")
far = d > 500
print("\nplots > 500 m from an active manhole:", int(far.sum()), "; by status:", g.loc[far].groupby('STATUS')['Q_SAT'].sum().round(1).to_dict(),
      "; by settlement (top):", g.loc[far].groupby('SETTLE')['Q_SAT'].sum().sort_values(ascending=False).head(6).round(1).to_dict())
