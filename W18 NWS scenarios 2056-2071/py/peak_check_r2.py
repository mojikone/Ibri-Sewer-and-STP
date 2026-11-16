"""R2 check: SewerGEMS outfall flow against PF(Peltier100-Merrimack, linear) x base + 720 L/day/km infiltration."""
import csv, collections, sys, numpy as np
INV, DG, R2 = r"D:\VBOX\bridge\out\inv_w17", r"D:\VBOX\bridge\out\diag", r"D:\VBOX\bridge\out\r2"
TAB = [(0.1,4.66),(0.15,4.08),(0.2,3.74),(0.3,3.33),(0.5,2.91),(0.75,2.65),(1,2.5),(1.5,3.39),(2,3.28),(3,3.12),(5,2.93),(7.5,2.79),(10,2.7),(15,2.57),(20,2.48),(30,2.36),(50,2.22),(75,2.11),(100,2.04),(150,1.94),(200,1.88),(300,1.79),(500,1.68),(750,1.6),(1000,1.54)]
pf = lambda q: float(np.interp(q, [t[0] for t in TAB], [t[1] for t in TAB]))
nodes = {int(r['id']): r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8'))}
sub = lambda l: l.split('-')[0] if l.startswith('O') and ('-M' in l or '-P' in l) else None
length = collections.defaultdict(float)
for r in csv.DictReader(open(INV + r"\links.csv", encoding='utf-8')):
    s = sub(r['label'])
    if s and r['active'] == 'True' and r['length']: length[s] += float(r['length'])
def check(year, flows_file):
    base = collections.defaultdict(float)
    for r in csv.DictReader(open(DG + rf"\rows_{year}.csv", encoding='utf-8')):
        s = sub(r['label']); 
        if s: base[s] += float(r['base_m3d'])
    got = {}
    for line in open(R2 + "\\" + flows_file, encoding='utf-8-sig'):
        k, v = line.strip().split(','); got[k] = float(v) / 86.4
    print(f"\n{year}: {'sub':4s} {'base L/s':>9s} {'PF':>5s} {'infil':>6s} {'predicted':>9s} {'SewerGEMS':>9s} {'diff %':>7s}")
    for s in sorted(got, key=lambda s: int(s[1:]) if s[1:].isdigit() else 999):
        b = base[s] / 86.4; inf = length[s] / 1000 * 0.72 / 86.4
        p = pf(b) * b + inf
        print(f"      {s:4s} {b:9.2f} {pf(b):5.2f} {inf:6.2f} {p:9.2f} {got[s]:9.2f} {100*(got[s]-p)/p if p else 0:7.1f}")
check('2030', 'outfalls_2030.csv'); check('2070', 'outfalls_2070_analysis.csv')
a = {l.split(',')[0]: float(l.split(',')[1]) for l in open(R2 + r"\outfalls_2030.csv", encoding='utf-8-sig') if ',' in l}
b = {l.split(',')[0]: float(l.split(',')[1]) for l in open(R2 + r"\outfalls_2030_plus100_O13.csv", encoding='utf-8-sig') if ',' in l}
print("\ntransfer test, +100 L/s pattern load at O13-M1 (2030): change at each outfall, L/s")
print("  " + ", ".join(f"{k} {(b[k]-a[k])/86.4:+.3f}" for k in sorted(a, key=lambda s: int(s[1:]) if s[1:].isdigit() else 999) if abs(b[k]-a[k]) > 1e-6) or "  none")
