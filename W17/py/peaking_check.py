"""Outfall flow from the 2030 analysis run against the sum of 2030 base loads in each subnetwork."""
import csv, collections, bisect
INV, PK = r"D:\VBOX\bridge\out\inv_w17", r"D:\VBOX\bridge\out\peak"
nodes = {int(r['id']): r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8'))}
sub = {i: (r['label'].split('-M')[0] if r['type'] == 'MH' else r['label']) for i, r in nodes.items()}
base = collections.defaultdict(float)
for r in csv.DictReader(open(PK + r"\base_2030.csv", encoding='utf-8')):
    base[sub.get(int(r['id']), '?')] += float(r['base_flow_m3s'])
outq = collections.defaultdict(float)
for r in csv.DictReader(open(PK + r"\flows_2030.csv", encoding='utf-8')):
    for end in ('start', 'stop'):
        n = nodes.get(int(r[end]))
        if n and n['type'] == 'OF' and r['flow_m3s']:
            outq[n['label']] += float(r['flow_m3s'])
# Peltier100-Merrimack table (first rows read from the model; base load m3/s -> factor)
print(f"{'sub':5s} {'base L/s':>9s} {'outfall L/s':>11s} {'ratio':>6s}")
for k in sorted(outq, key=lambda s: int(s[1:]) if s[1:].isdigit() else 999):
    b = base.get(k, 0) * 1000; q = outq[k] * 1000
    print(f"{k:5s} {b:9.1f} {q:11.1f} {q/b if b else float('nan'):6.2f}")
print("total base L/s", round(sum(base.values())*1000, 1), " total outfall L/s", round(sum(outq.values())*1000, 1))
