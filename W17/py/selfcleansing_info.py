"""For information (the self-cleansing audit itself waits for the client's decision):
1. in which year does every pipe reach 0.75 m/s at its peak flow (G203 p26)?
2. what gradient would a pipe need to reach 0.75 m/s at its peak, and how many stay within the client's 4 %?
3. the tractive-force gradient at tau = 1 Pa (Mara, Sleigh & Taylor, G203 p27: S = 5.5e-3 tau^1.23 Q^-0.461, Q in L/s).
Velocity by Colebrook-White, ks = 1.5 mm, nu = 1.141e-6 m2/s (G203 p24, p25), partly full circular pipe.
Flows and velocities from the S1 runs (R7: 2070 analysis on the designed pipes, and 2030-2060).
"""
import csv, math, collections, sys
import numpy as np

S1 = r"D:\VBOX\bridge\out\scen\S1"
G, NU, KS = 9.81, 1.141e-6, 1.5e-3
TAGS = [("2030", "S1-2030"), ("2040", "S1-2040"), ("2050", "S1-2050"), ("2055", "S1-2055"), ("2060", "S1-2060"), ("2070", "S1-2070a")]


def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D)
    A = D * D / 8 * (th - math.sin(th)); P = D * th / 2
    return A, A / P


def v_cw(R, S):
    a = math.sqrt(8 * G * R * S)
    return -2 * a * math.log10(KS / (14.8 * R) + 2.51 * NU / (4 * R * a))


def velocity(Q, D, S):
    """Normal-depth velocity of flow Q (m3/s) in pipe D (m) at gradient S (Colebrook-White)."""
    if Q <= 0:
        return 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(60):
        y = (lo + hi) / 2
        A, R = section(D, y)
        if A * v_cw(R, S) > Q: hi = y
        else: lo = y
    A, R = section(D, (lo + hi) / 2)
    return Q / A


def slope_for(Q, D, v=0.75):
    """Gradient at which flow Q in pipe D reaches velocity v (None if not reached below 100 %)."""
    if Q <= 0:
        return None
    lo, hi = 1e-6, 1.0
    if velocity(Q, D, hi) < v:
        return None
    for _ in range(60):
        s = math.sqrt(lo * hi)
        if velocity(Q, D, s) < v: lo = s
        else: hi = s
    return hi


rows = {}
for y, tag in TAGS:
    for r in csv.DictReader(open(rf"{S1}\conduits_{tag}.csv", encoding="utf-8")):
        if r["active"] != "True" or not r["label"].startswith("O"):
            continue
        d = rows.setdefault(r["label"], dict(D=float(r["diameter_mm"]) / 1000, L=float(r["length_m"]),
                                             S=(float(r["start_inv"]) - float(r["stop_inv"])) / float(r["length_m"]),
                                             start=r["start"], stop=r["stop"], v={}, q={}))
        d["v"][y] = float(r["velocity_ms"]) if r["velocity_ms"] not in ("", "NaN") else 0.0
        d["q"][y] = float(r["flow_m3d"]) / 86400 if r["flow_m3d"] not in ("", "NaN") else 0.0

# head pipe: its upper end touches no other pipe
deg = collections.Counter()
for d in rows.values():
    deg[d["start"]] += 1; deg[d["stop"]] += 1
for d in rows.values():
    up = d["start"] if d["S"] >= 0 else d["stop"]
    d["head"] = deg[up] == 1

n = len(rows); Ltot = sum(d["L"] for d in rows.values())
heads = [d for d in rows.values() if d["head"]]
print(f"{n} active pipes, {Ltot/1000:,.0f} km; head pipes {len(heads)}")
print("\n1. Pipes reaching 0.75 m/s at their peak flow (SewerGEMS velocities of the S1 runs)")
print("| year | pipes | share | length km | share of length | head pipes reaching it |")
print("|---|---|---|---|---|---|")
for y, _ in TAGS:
    ok = [d for d in rows.values() if d["v"].get(y, 0) >= 0.75]
    okh = sum(1 for d in heads if d["v"].get(y, 0) >= 0.75)
    print(f"| {y} | {len(ok):,} | {100*len(ok)/n:.1f} % | {sum(d['L'] for d in ok)/1000:,.0f} | {100*sum(d['L'] for d in ok)/Ltot:.1f} % | {okh:,} of {len(heads):,} |")


def stats(vals):
    v = np.array([x for x in vals if x is not None])
    return v


print("\n2. Gradient needed to reach 0.75 m/s at the peak flow (Colebrook-White ks 1.5 mm), and 3. tractive gradient at 1 Pa")
print("| year | group | pipes | no flow at all | median flow L/s | median slope for 0.75 m/s | 75 % | within 4 % | not reached below 100 % | median tractive slope | tractive above 4 % |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for y in ("2030", "2070"):
    for name, grp in (("head pipes", heads), ("all pipes below 0.75 m/s", [d for d in rows.values() if d["v"].get(y, 0) < 0.75])):
        req = [slope_for(d["q"][y], d["D"]) for d in grp]
        qs = np.array([d["q"][y] * 1000 for d in grp])
        r = stats(req)
        within = sum(1 for x in req if x is not None and x <= 0.04)
        never = sum(1 for x in req if x is None)
        zero = int((qs <= 0).sum()); never -= zero
        tr = np.array([5.5e-3 * (q ** -0.461) for q in qs if q > 0])
        print(f"| {y} | {name} | {len(grp):,} | {zero:,} | {np.median(qs[qs > 0]):.2f} | {100*np.median(r):.1f} % | {100*np.percentile(r,75):.1f} % | {within:,} ({100*within/len(grp):.0f} %) | {never:,} | {100*np.median(tr):.2f} % | {int((tr > 0.04).sum()):,} |")

print("\nDN200 (176.4 mm ID): gradient needed for 0.75 m/s at a given peak flow")
for q in (0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0):
    s = slope_for(q / 1000, 0.1764)
    print(f"  {q:4.2f} L/s -> {100*s:5.2f} %   (tractive at 1 Pa: {100*5.5e-3*q**-0.461:.2f} %)")
lo, hi = 0.01, 50.0
for _ in range(60):
    m = math.sqrt(lo * hi)
    if slope_for(m / 1000, 0.1764) > 0.04: lo = m
    else: hi = m
print(f"  smallest peak flow a DN200 can carry at 0.75 m/s within 4 %: {hi:.2f} L/s")
print(f"  flow at which the tractive gradient reaches 4 %: {(0.04/5.5e-3)**(-1/0.461):.4f} L/s")
