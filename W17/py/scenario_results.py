"""Results of one STP option from the SewerGEMS exports: flow check, design changes, quantities, checks, plants, pumps.

Usage: python scenario_results.py S1
Guideline values: G203 p27 (v <= 3.0 m/s; d/D <= 0.65 to DN350, <= 0.50 above), p26 (0.75 m/s), p33 (cover 1.3 m;
12 m hard limit, standing decision), p40 Tab 17 (PS types), p43 Tab 21 (land), p48 (wet well V = 0.25 Q T, 10 starts/h),
p50 (force main 1.0 m/s intermittent, 2.5 m/s max, >= 75 mm ID, retention ideally <= 30 min), p55 (discharge <= 300 mm
above the receiving flow line); G202 p104 Tab 21 (Hazen-Williams C).
PROJECT ASSUMPTIONS (tagged in every output): rising main length = straight line x 1.25; Hazen-Williams C = 120;
minor losses +10 %; wet well 1.5 m below the incoming invert; pump wire-to-water efficiency 0.65; a plant inlet 3.0 m
above the ground at the plant outfall.
"""
import sys, os, csv, math, collections
import numpy as np
from routing import SCENARIOS, YEARS, routing, plant_of, transfers, OLD

NAME = sys.argv[1] if len(sys.argv) > 1 else "S1"
D = rf"D:\VBOX\bridge\out\scen\{NAME}"
DIAG = r"D:\VBOX\bridge\out\r4\diag"
FT = 0.3048
SUB = lambda lab: lab.split("-")[0] if lab.startswith("O") and ("-M" in lab or "-P" in lab) else None
OUT = rf"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results\{NAME}"
os.makedirs(OUT, exist_ok=True)
REPORT = []


def say(s=""):
    print(s); REPORT.append(s)


def rd(tag, kind):
    p = rf"{D}\{kind}_{tag}.csv"
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def outfalls(tag):
    p = rf"{D}\outfalls_{tag}.csv"
    return {l.split(",")[0]: float(l.split(",")[1]) for l in open(p, encoding="utf-8-sig") if "," in l} if os.path.exists(p) else {}


OD = lambda id_mm: int(round(id_mm / 0.882353 / 5.0) * 5)    # catalogue: inside diameter = 0.882 x OD (SDR-type series)

# ---------------------------------------------------------------- 1. flow check: SewerGEMS outfall flows vs transfers
say(f"# {NAME} — {SCENARIOS[NAME]['text']}")
rows, total = transfers(NAME, "2070")
chk = outfalls("check2070")
if chk:
    worst = max((abs(chk.get(s, 0) - total[s]) / max(total[s], 1e-9), s) for s in total if total[s] > 0)
    say(f"\nFlow check 2070 (transfers in place, run as analysis): largest difference {100*worst[0]:.4f} % at {worst[1]}")

# ---------------------------------------------------------------- 2. design: what changed
base = {r["label"]: r for r in rd("base2070_inputs", "conduits")}
des = {r["label"]: r for r in rd(f"{NAME}-2070", "conduits")}
mh_base = {r["label"]: r for r in rd("base2070_inputs", "manholes")}
mh_des = {r["label"]: r for r in rd(f"{NAME}-2070", "manholes")}
act = [l for l, r in des.items() if r["active"] == "True" and SUB(l)]
ch_d = sum(1 for l in act if abs(float(des[l]["diameter_mm"]) - float(base[l]["diameter_mm"])) > 1e-6)
ch_i = sum(1 for l in act if abs(float(des[l]["start_inv"]) - float(base[l]["start_inv"])) > 1e-4 or abs(float(des[l]["stop_inv"]) - float(base[l]["stop_inv"])) > 1e-4)
say(f"\nDesign 2070: {len(act)} active pipes; diameter changed on {ch_d}, inverts changed on {ch_i} (against the modeller's design)")

# ---------------------------------------------------------------- 3. quantities
def depth_mh(r):
    return float(r["rim"]) - float(r["invert"])

nodes = {r["id"]: r for r in rd(f"{NAME}-2070", "manholes")}
qty_len = collections.defaultdict(float)                 # (OD, band) -> m
BANDS = [(0, 1.5), (1.5, 3), (3, 4.5), (4.5, 6), (6, 9), (9, 12), (12, 99)]
band = lambda d: next(f"{a:g}-{b:g} m" if b < 99 else f">{a:g} m" for a, b in BANDS if a <= d < b)
pipe_rows = []
for l in act:
    r = des[l]; s, e = nodes.get(r["start"]), nodes.get(r["stop"])
    if not s or not e:
        continue
    dia = float(r["diameter_mm"])
    d_in = (float(s["ground"]) - float(r["start_inv"]) + float(e["ground"]) - float(r["stop_inv"])) / 2
    cover_min = min(float(s["ground"]) - float(r["start_inv"]), float(e["ground"]) - float(r["stop_inv"])) - dia / 1000
    L = float(r["length_m"])
    od = int(r["size_label"].split()[0]) if r["size_label"].split()[0].isdigit() else OD(dia)
    qty_len[(od, band(d_in))] += L
    pipe_rows.append(dict(label=l, sub=SUB(l), od=od, id_mm=round(dia, 1), length=L, depth_avg=d_in, cover_min=cover_min,
                          slope=(float(r["start_inv"]) - float(r["stop_inv"])) / L if L > 0 else 0))
ods = sorted({k[0] for k in qty_len}); bands = [band((a + min(b, a + 1)) / 2) for a, b in BANDS]
say("\nPipe length by size (OD, mm) and depth to invert (m), 2070 design, metres")
say("| OD | " + " | ".join(bands) + " | total |"); say("|---|" + "---|" * (len(bands) + 1))
for od in ods:
    vals = [qty_len.get((od, b), 0) for b in bands]
    say(f"| {od} | " + " | ".join(f"{v:,.0f}" if v else "" for v in vals) + f" | {sum(vals):,.0f} |")
say(f"| total | " + " | ".join(f"{sum(qty_len.get((od, b), 0) for od in ods):,.0f}" for b in bands) + f" | {sum(qty_len.values()):,.0f} |")

mhs = [r for l, r in mh_des.items() if r["active"] == "True" and SUB(l)]
mb = collections.Counter(band(depth_mh(r)) for r in mhs)
say("\nManholes by depth (rim to invert), 2070 design")
say("| " + " | ".join(bands) + " | total |"); say("|" + "---|" * (len(bands) + 1))
say("| " + " | ".join(str(mb.get(b, 0)) for b in bands) + f" | {len(mhs)} |")
deep = sorted(((depth_mh(r), r["label"]) for r in mhs), reverse=True)
say(f"Deepest manholes: " + ", ".join(f"{l} {d:.2f} m" for d, l in deep[:8]))
base_mhs = [r for l, r in mh_base.items() if r["active"] == "True" and SUB(l)]
say(f"Manholes deeper than 12 m: {sum(1 for d, _ in deep if d > 12)} (modeller's design: {sum(1 for r in base_mhs if depth_mh(r) > 12)})")

# ---------------------------------------------------------------- 4. checks
def checks(tag, design):
    rr = {r["label"]: r for r in rd(tag, "conduits")}
    vmax = dd = vlow = n = 0
    for p in pipe_rows:
        r = rr.get(p["label"])
        if not r or not r["velocity_ms"]:
            continue
        n += 1
        v = float(r["velocity_ms"])                                # the API returns display units: m/s, m, mm, m3/d
        q = float(r["flow_m3d"]) if r["flow_m3d"] else 0
        dmax = max(float(r["depth_in_m"] or 0), float(r["depth_out_m"] or 0)) * 1000
        lim = 0.65 if p["id_mm"] <= 350 else 0.50
        if dmax / p["id_mm"] > lim + 1e-6: dd += 1
        if v > 3.0: vmax += 1
        if q > 0 and v < 0.75: vlow += 1
    return n, vmax, dd, vlow

say("\nChecks (active pipes; G203 p27 v <= 3.0 m/s, d/D <= 0.65 to 350 mm ID and 0.50 above; p26 0.75 m/s at peak)")
say("| run | pipes with results | v > 3.0 | d/D over limit | v < 0.75 with flow |")
say("|---|---|---|---|---|")
for y in ['2070a'] + YEARS[:-1]:
    tag = f"{NAME}-{y}"   # 2070a = 2070 run as an analysis on the designed pipes
    n, vmax, dd, vlow = checks(tag, y == '2070')
    if n: say(f"| {tag} | {n} | {vmax} | {dd} | {vlow} |")
say("(2030 here is the full 2030 load; the self-cleansing audit of the project rule uses 2030 x 0.61 with no infiltration — run separately)")

# ---------------------------------------------------------------- 5. plants
tr, joins, stp = routing(NAME)
plant = plant_of(NAME)
base_sub = {y: collections.defaultdict(float) for y in YEARS}
for y in YEARS:
    for r in csv.DictReader(open(rf"{DIAG}\rows_{y}.csv", encoding="utf-8")):
        s = SUB(r["label"])
        if s: base_sub[y][s] += float(r["base_m3d"])
infil = collections.defaultdict(float)
for p in pipe_rows:
    infil[p["sub"]] += p["length"] / 1000 * 0.72                 # 720 L/day/km, m3/d
say("\nPlants: average dry-weather flow + infiltration (m3/d) and peak inflow (L/s, sum of the outfall peaks)")
say("| plant | " + " | ".join(YEARS) + " |"); say("|---|" + "---|" * len(YEARS))
plant_rows = []
for z in sorted(stp, key=lambda s: int(s[1:])):
    avg = [sum(base_sub[y][s] + infil[s] for s in plant if plant[s] == z) for y in YEARS]
    pk = []
    for y in YEARS:
        rws, tot = transfers(NAME, y)
        pk.append((tot[z] + sum(tot[s] for s, t in joins.items() if t == z)) / 86.4)
    say(f"| {z} ({OLD[z]}) avg m3/d | " + " | ".join(f"{a:,.0f}" for a in avg) + " |")
    say(f"| {z} ({OLD[z]}) peak L/s | " + " | ".join(f"{p:,.1f}" for p in pk) + " |")
    plant_rows.append((z, avg, pk))

# ---------------------------------------------------------------- 6. pumping stations
say("\nPumping stations (one per outfall that is pumped). Duty = 2070 peak (raised to the 75 mm / 1.0 m/s floor where smaller).")
say("ASSUMED: main = straight line x 1.25; HW C = 120; minor losses +10 %; wet well 1.5 m below the outfall invert; efficiency 0.65; plant inlet = ground + 3.0 m.")
allmh = {r["label"]: r for r in rd(f"{NAME}-2070", "manholes")}
DN = [75, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200]
ps = []
links = [(s, mh, "manhole") for s, mh, r in tr] + [(s, z, "plant") for s, z in joins.items()]
for s, dest, kind in links:
    o = allmh[s]
    if kind == "manhole":
        t = allmh[dest]; z_out = float(t["invert"]) + 0.3
    else:
        t = allmh[dest]; z_out = float(t["ground"]) + 3.0
    z_in = float(o["invert"]) - 1.5
    L = math.hypot(float(t["x"]) - float(o["x"]), float(t["y"]) - float(o["y"])) * 1.25
    q70 = transfers(NAME, "2070")[1][s] / 86400
    qmin_floor = math.pi / 4 * 0.075 ** 2 * 1.0
    # main size and duty: every DN from 75 mm with v <= 2.5 m/s; the duty is raised where needed so the main keeps
    # 1.0 m/s (G203 p50, intermittent); the one needing the least power is kept
    best = None
    for d in DN:
        a = math.pi / 4 * (d / 1000) ** 2
        q_try = max(q70, a * 1.0, qmin_floor)
        if q_try / a > 2.5:
            continue
        hf_try = 1.1 * 10.67 * L * q_try ** 1.852 / (120 ** 1.852 * (d / 1000) ** 4.87)
        kw_try = 9.81 * q_try * (max(z_out - z_in, 0) + hf_try) / 0.65
        if best is None or kw_try < best[0]:
            best = (kw_try, d, q_try, hf_try)
    kw, dn, qd, hf = best
    v = qd / (math.pi / 4 * (dn / 1000) ** 2)
    H = max(z_out - z_in, 0) + hf
    typ = 1 if qd <= 0.100 else 2 if qd <= 0.300 else 3
    up = [u for u in plant if u == s or any(True for _ in [0])]
    # average volume through the station = every subnetwork that drains through it (itself + its upstream)
    nxt = {a: r for a, _, r in tr}
    def drains_through(u):
        while u in nxt:
            if u == s: return True
            u = nxt[u]
        return u == s
    ups = [u for u in plant if drains_through(u)]
    e = {}
    for y in YEARS:
        vol = sum(base_sub[y][u] + infil[u] for u in ups)          # m3/d average
        hours = vol / (qd * 3600) if qd > 0 else 0
        e[y] = kw * hours * 365
    ret = (math.pi / 4 * (dn / 1000) ** 2 * L) / (sum(base_sub["2030"][u] + infil[u] for u in ups) / 86400) / 60
    ww_depth = float(o["ground"]) - float(o["invert"]) + 1.5
    ps.append(dict(ps=s, old=OLD[s], to=dest, kind=kind, type=typ, wet_well_depth=ww_depth, q70=q70 * 1000, duty=qd * 1000, dn=dn, v=v, L=L,
                   static=z_out - z_in, H=H, kw=kw, kwh2030=e["2030"], kwh2070=e["2070"], ret2030=ret,
                   live_m3=90 * qd / (1 if typ == 1 else 2 if typ == 2 else 3)))
say("| PS (old) | to | type | wet well depth m | Q2070 L/s | duty L/s | DN | v m/s | main m | static m | total head m | kW | MWh/yr 2030 | MWh/yr 2070 | retention 2030 min | live vol m3 |")
say("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for p in sorted(ps, key=lambda p: -p["duty"]):
    say(f"| {p['ps']} ({p['old']}) | {p['to']} | {p['type']} | {p['wet_well_depth']:.1f} | {p['q70']:.1f} | {p['duty']:.1f} | {p['dn']} | {p['v']:.2f} | {p['L']:,.0f} | {p['static']:.1f} | {p['H']:.1f} | {p['kw']:.0f} | {p['kwh2030']/1000:,.0f} | {p['kwh2070']/1000:,.0f} | {p['ret2030']:.0f} | {p['live_m3']:.1f} |")
say(f"Total: {len(ps)} stations, {sum(p['kw'] for p in ps):,.0f} kW installed duty, {sum(p['kwh2030'] for p in ps)/1e6:,.2f} GWh/yr in 2030, {sum(p['kwh2070'] for p in ps)/1e6:,.2f} GWh/yr in 2070")

with open(rf"{OUT}\{NAME}_summary.md", "w", encoding="utf-8") as f:
    f.write("\n".join(REPORT) + "\n")
for nm, data in (("pipes", pipe_rows), ("pumps", ps)):
    if data:
        with open(rf"{OUT}\{NAME}_{nm}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
