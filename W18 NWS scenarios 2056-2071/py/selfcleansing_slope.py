"""W18 check run (engineer, 2026-11-16): at what gradient does each pipe above DN200 reach 0.75 m/s at its 2031 peak
flow, and how deep does the network go if pipes are steepened up to a threshold gradient?

Input: one SewerGEMS scenario's exports (the design-year analysis and the 2031 analysis on the same pipes).
Hydraulics: Colebrook-White, ks 1.5 mm, nu 1.141e-6 m2/s, normal depth in a part-full circular pipe (G203 p24, p25),
the functions of W17/py/selfcleansing_info.py; checked against SewerGEMS's own 2031 velocities at the laid gradient.
Depth: steepening pipe i lowers every invert downstream of it by (S_new - S_laid) x L; at a junction the larger
lowering is carried on (an upper estimate: the design could flatten nothing, and the ground is not re-read).
Usage: python selfcleansing_slope.py <scenario tag, e.g. SC1-2056> <export dir> <out dir>
"""
import sys, os, math
import numpy as np, pandas as pd

G, NU, KS = 9.81, 1.141e-6, 1.5e-3
V_SC = 0.75
THRESHOLDS = [0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.04]


def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D)
    A = D * D / 8 * (th - math.sin(th)); P = D * th / 2
    return A, A / P


def v_cw(R, S):
    a = math.sqrt(8 * G * R * S)
    return -2 * a * math.log10(KS / (14.8 * R) + 2.51 * NU / (4 * R * a))


def velocity(Q, D, S):
    if Q <= 0 or S <= 0:
        return 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2
        A, R = section(D, y)
        if A * v_cw(R, S) > Q: hi = y
        else: lo = y
    A, R = section(D, (lo + hi) / 2)
    return Q / A


def slope_for(Q, D, v=V_SC):
    if Q <= 0:
        return np.nan
    lo, hi = 1e-6, 1.0
    if velocity(Q, D, hi) < v:
        return np.nan
    for _ in range(45):
        s = math.sqrt(lo * hi)
        if velocity(Q, D, s) < v: lo = s
        else: hi = s
    return hi


tag, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
dy = pd.read_csv(os.path.join(src, f"conduits_{tag}a.csv"))
d31 = pd.read_csv(os.path.join(src, f"conduits_{tag}-at-2031.csv")).set_index("label")
mh = pd.read_csv(os.path.join(src, f"manholes_{tag}a.csv")).set_index("id")
dy = dy[dy.active == True].copy()
dy["Q31"] = d31.flow_m3d.reindex(dy.label).values / 86400.0
dy["V31_MODEL"] = d31.velocity_ms.reindex(dy.label).values
dy["D"] = dy.diameter_mm / 1000.0
dy["S_LAID"] = (dy.start_inv - dy.stop_inv).abs() / dy.length_m
dy["UP"] = np.where(dy.start_inv >= dy.stop_inv, dy.start, dy.stop)
dy["DN"] = np.where(dy.start_inv >= dy.stop_inv, dy.stop, dy.start)
big = dy.diameter_mm > 177
dy["V31_CALC"] = [velocity(q, d, s) if b else np.nan for q, d, s, b in zip(dy.Q31, dy.D, dy.S_LAID, big)]
dy["S_REQ"] = [slope_for(q, d) if b else np.nan for q, d, b in zip(dy.Q31, dy.D, big)]
b = dy[big]
ratio = (b.V31_CALC / b.V31_MODEL).replace([np.inf, -np.inf], np.nan).dropna()

# topological order, upstream first
down = dict(zip(dy.index, dy.DN)); up = dict(zip(dy.index, dy.UP))
indeg = {}
for i in dy.index: indeg[dy.at[i, "DN"]] = indeg.get(dy.at[i, "DN"], 0) + 1
out_of = {}
for i in dy.index: out_of.setdefault(dy.at[i, "UP"], []).append(i)
nodes = set(dy.UP) | set(dy.DN)
queue = [n for n in nodes if indeg.get(n, 0) == 0]; order = []
while queue:
    n = queue.pop()
    for i in out_of.get(n, []):
        order.append(i); m = dy.at[i, "DN"]; indeg[m] -= 1
        if indeg[m] == 0: queue.append(m)
assert len(order) == len(dy), "the network is not a tree"

# --- depth. The design lays every pipe at its Table 11 floor (checked 2026-11-16: within 3 % for all 19,083 pipes,
# DN200 at 0.51 %) and keeps cover over falling ground with DROPS at the manholes. Re-lay, upstream first: a pipe's
# upstream invert = min(lowest incoming invert, its designed upstream invert); downstream invert = upstream - S x L.
# So a pipe made deeper upstream first uses up the drop below it, and only the excess is carried on. With the laid
# gradients this reproduces the design exactly (checked in the summary).
mhv = mh[(mh.active == True) & (mh.invert > 100) & (mh.ground > 100)]
terminal = sorted(set(dy.DN) - set(dy.UP))
pos = {i: k for k, i in enumerate(dy.index)}
dy["UP_INV0"] = np.where(dy.start_inv >= dy.stop_inv, dy.start_inv, dy.stop_inv)
dy["DN_INV0"] = np.where(dy.start_inv >= dy.stop_inv, dy.stop_inv, dy.start_inv)


def relay(s):
    node = {}
    for i in order:
        k = pos[i]; u = up[i]
        upi = min(node[u], dy.at[i, "UP_INV0"]) if u in node else dy.at[i, "UP_INV0"]
        dni = upi - s[k] * dy.at[i, "length_m"]
        node[down[i]] = min(node.get(down[i], np.inf), dni)
    return pd.Series(node)


inv0 = relay(dy.S_LAID.values)
lowin0 = dy.groupby("DN").DN_INV0.min()
chk = (inv0 - lowin0.reindex(inv0.index)).abs()
gnd = mhv.ground
base_depth = (gnd - inv0.reindex(mhv.index)).dropna()


def depth_for(s_new):
    inv = relay(s_new)
    added = (inv0 - inv)
    nd = (gnd - inv.reindex(mhv.index)).dropna()
    return added, nd


rows = []
dy["PASS_LAID"] = big & (dy.V31_MODEL >= V_SC)
L_big = b.length_m.sum()
for T in THRESHOLDS:
    s_new = np.where(big & (dy.S_REQ > dy.S_LAID) & (dy.S_REQ <= T), dy.S_REQ, dy.S_LAID)
    added_all, new_depth = depth_for(s_new)
    added = added_all.reindex(mhv.index).fillna(0.0)
    passing = big & ((dy.V31_MODEL >= V_SC) | ((dy.S_REQ <= T) & dy.S_REQ.notna()))
    steep = big & (dy.S_REQ > dy.S_LAID) & (dy.S_REQ <= T)
    at_out = added_all.reindex(terminal).fillna(0.0)
    rows.append(dict(threshold_pct=T * 100,
                     pass_len_pct=100 * dy.length_m[passing].sum() / L_big, pass_n=int(passing.sum()),
                     steepened_n=int(steep.sum()), steepened_km=dy.length_m[steep].sum() / 1000,
                     max_added_m=added.max(), mh_added_over_1m=int((added > 1).sum()),
                     mh_over_12m=int((new_depth > 12).sum()), mh_over_12m_before=int((base_depth > 12).sum()),
                     deepest_m=new_depth.max(), max_added_at_outfall_m=at_out.max(),
                     outfalls_added_over_1m=int((at_out > 1).sum())))
tab = pd.DataFrame(rows)

never = big & dy.S_REQ.isna()
q = b.S_REQ[b.S_REQ > b.S_LAID].dropna()
dy[["label", "size_label", "diameter_mm", "length_m", "S_LAID", "Q31", "V31_MODEL", "V31_CALC", "S_REQ"]][big].to_csv(
    os.path.join(out, f"pipes_{tag}.csv"), index=False, float_format="%.6g")
tab.to_csv(os.path.join(out, f"thresholds_{tag}.csv"), index=False, float_format="%.3f")
L = [f"# Gradient for 0.75 m/s at the 2031 peak flow - {tag}", "",
     f"Pipes above DN200: {len(b):,} ({L_big/1000:.1f} km). Check of the calculation against SewerGEMS at the laid gradient (2031): "
     f"calc/model velocity median {ratio.median():.3f}, 90 % within {np.percentile(np.abs(ratio - 1), 90)*100:.1f} %.", "",
     f"Already at 0.75 m/s at the laid gradient: {int(dy.PASS_LAID.sum()):,} pipes ({100*dy.length_m[dy.PASS_LAID].sum()/L_big:.1f} % of length). "
     f"Cannot reach it at any gradient below 100 % (no flow or too little): {int(never.sum())}.", "",
     "Required gradient of the pipes that fail at the laid gradient, percentiles 10/25/50/75/90: "
     + " / ".join(f"{v*100:.2f} %" for v in np.percentile(q, [10, 25, 50, 75, 90])) if len(q) else "none", "",
     f"Re-lay check with the laid gradients: largest difference from the designed inverts {chk.max():.4f} m. Added depth uses up the manhole drops before it is carried on.", "",
     "| threshold gradient | length reaching 0.75 m/s | pipes steepened | km steepened | largest added depth | added depth at an outfall | manholes deepened > 1 m | manholes > 12 m (now) | deepest manhole |",
     "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['threshold_pct']:.2f} % | {r['pass_len_pct']:.1f} % | {r['steepened_n']:,} | {r['steepened_km']:.1f} | {r['max_added_m']:.2f} m | {r['max_added_at_outfall_m']:.2f} m | {r['mh_added_over_1m']:,} | {r['mh_over_12m']:,} ({r['mh_over_12m_before']:,}) | {r['deepest_m']:.2f} m |")
L += ["", "By size, median gradient required (failing pipes):"]
for sz, gq in b[b.S_REQ > b.S_LAID].groupby("size_label"):
    L.append(f"- {sz}: {len(gq)} pipes, median {gq.S_REQ.median()*100:.2f} %, laid median {gq.S_LAID.median()*100:.2f} %")
open(os.path.join(out, "SUMMARY.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
