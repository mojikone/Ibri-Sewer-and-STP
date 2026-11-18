"""Drops over 2 m (engineer, 2026-11-18): how many of the junction drops higher than 2 m can be removed, by what, at what
cost, and what to do with the rest. A temporary study on the final design; the design, the models and the report are
not changed. Builds on W17/assessment/junction_drops (October: reroute the deep sewer, step the branch down, a parallel
shallow sewer).

PAM-GUD-203 p30: a backdrop is required when the invert drop exceeds 0.6 m, at most 2 m high; beyond 2 m a vortex drop
shaft. A drop here = the invert of an incoming pipe above the invert of the outgoing pipe at the same manhole.

The engine re-lays each case the way the design engine does (split_deep_subnetworks.relay: from the heads down, the
upstream invert the shallowest of the arrival, the crown match and the cover at both ends, cover 1.3 m over the soffit),
and checks that with the laid gradients it reproduces the design's depths. The fixes:
  F1 regrade   a pipe on ground that falls faster than its gradient may steepen until its downstream end has cover, up to a
               maximum gradient (4 %, the limit indicated by NWS on 16 Sep 2026; or the gradient at which the design-year
               peak reaches 3.0 m/s, capped at 15 %). The design lays every pipe at its Table 11 (or self-cleansing)
               gradient from the cover at its low end, so on steep ground its high end hangs deep and the pipe above
               drops into it.
  F2 lower     a branch still arriving more than 2 m above the outgoing invert is lowered from the junction upstream: its
               last pipe steepened (same maximum), then its upstream manhole lowered and the pipes above it in turn,
               either without any new backdrop (F2a, steepening only) or with new backdrops of 2 m at most at the
               branch's own manholes (F2b, steepen and step down). Manholes may reach 16.5 m (the design's cap).
  F3 parallel  the engineer's idea, for what is left: the drops on one deep sewer collected by a shallow sewer beside it
               that joins it once (counted per deep stretch, with the ground fall along it).
  F4 reconnect a branch joined by gravity to another nearby manhole (within one manhole spacing, 100 m) that is low enough
               for a drop of 2 m or less and not upstream of it (a candidate: the route is checked on the street plan).
Costs: sewers and manholes at the rates of the BOQ (team's options cost estimate, by size and 0.5 m depth band); a
vortex drop shaft has no rate in the estimate, so a fix is called economic where it costs less than a 1,800 mm manhole
as deep as the receiving manhole (a floor for a drop shaft structure).
Usage: python drops_engine.py SC1-2056        Writes <case>/ drops.csv, variants.csv, summary.json, drops_<case>.gpkg"""
import os, sys, json, math, collections, copy
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(os.path.dirname(HERE))
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
CASE = sys.argv[1] if len(sys.argv) > 1 else "SC1-2056"
OUT = os.path.join(HERE, CASE); os.makedirs(OUT, exist_ok=True)
COVER, VMAX, BD, NOBD, MH_CAP, S_CLIENT, S_CAP = 1.3, 3.0, 2.0, 0.6, 16.5, 0.04, 0.15
G, NU, KS = 9.81, 1.141e-6, 1.5e-3

# ------------------------------------------------------------------ hydraulics (the design's Colebrook-White, ks 1.5 mm)
def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)
def v_cw(Rh, S):
    a = math.sqrt(8 * G * Rh * S); return -2 * a * math.log10(KS / (14.8 * Rh) + 2.51 * NU / (4 * Rh * a))
def velocity(Q, D, S):
    if Q <= 0 or S <= 0: return 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2; A, Rh = section(D, y)
        if A * v_cw(Rh, S) > Q: hi = y
        else: lo = y
    A, Rh = section(D, (lo + hi) / 2); return Q / A
def slope_for(Q, D, vt):
    if Q <= 0 or velocity(Q, D, S_CAP) < vt: return S_CAP
    lo, hi = 1e-5, S_CAP
    for _ in range(40):
        s = math.sqrt(lo * hi)
        if velocity(Q, D, s) < vt: lo = s
        else: hi = s
    return lo

# ------------------------------------------------------------------ the case
K = pd.read_csv(os.path.join(R, CASE, "named", "links.csv")); N = pd.read_csv(os.path.join(R, CASE, "named", "nodes.csv")).set_index("new")
X = pd.read_csv(os.path.join(R, CASE, "exports", f"conduits_{CASE}a.csv")).set_index("label")
X31 = pd.read_csv(os.path.join(R, CASE, "exports", f"conduits_{CASE}-at-2031.csv")).set_index("label")
K = K[K.kind.isin(["pipe", "gravity join"])].copy()
K["D"] = K.old.map(X.diameter_mm).fillna(K.dn_mm) / 1000.0
K["Q"] = K.old.map(X.flow_m3d).fillna(0) / 86400.0; K["Q31"] = K.old.map(X31.flow_m3d).fillna(0) / 86400.0
K["S0"] = K.s_new_pc / 100.0
P = {r.new: dict(up=r.from_mh, dn=r.to_mh, L=float(r.length_m), D=float(r.D), dn_mm=int(r.dn_mm), S0=float(r.S0), Q=float(r.Q), Q31=float(r.Q31),
                 du=float(r.depth_up_m), dd=float(r.depth_dn_m)) for r in K.itertuples()}
ground = N.ground.to_dict()
out_of, into = collections.defaultdict(list), collections.defaultdict(list)
for k, p in P.items(): out_of[p["up"]].append(k); into[p["dn"]].append(k)
order = []                                                            # pipes from the heads down
indeg = collections.Counter(p["dn"] for p in P.values()); stack = [n for n in set(p["up"] for p in P.values()) if indeg[n] == 0]
while stack:
    n = stack.pop()
    for k in out_of[n]:
        order.append(k); indeg[P[k]["dn"]] -= 1
        if indeg[P[k]["dn"]] == 0: stack.append(P[k]["dn"])
assert len(order) == len(P), (len(order), len(P))
SMAX_V = {k: slope_for(p["Q"], p["D"], VMAX) for k, p in P.items()}


def relay(smax=None):
    """Inverts {pipe: (up, dn)} and gradients; smax None = the design's rule (gradients fixed)."""
    arr, crown, inv, S = {}, {}, {}, {}
    for k in order:
        p = P[k]; n = p["up"]; gu, gd = ground[n], ground[p["dn"]]
        u_nat = min(arr.get(n, np.inf), crown.get(n, np.inf) - p["D"], gu - (COVER + p["D"]))
        d_cov = gd - (COVER + p["D"]); s = p["S0"]
        if smax is not None:
            need = (u_nat - d_cov) / p["L"]
            if need > s: s = max(s, min(need, smax(k)))
        u = min(u_nat, d_cov + s * p["L"]); d = u - s * p["L"]
        inv[k] = (u, d); S[k] = s
        arr[p["dn"]] = min(arr.get(p["dn"], np.inf), d); crown[p["dn"]] = min(crown.get(p["dn"], np.inf), d + p["D"])
    return inv, S


def drops(inv):
    """(manhole, incoming pipe) -> drop, m."""
    out = {}
    for n, ks in into.items():
        if n not in out_of or not out_of[n]: continue
        u = inv[out_of[n][0]][0]
        for k in ks: out[(n, k)] = inv[k][1] - u
    return out


def node_depth(inv):
    z = collections.defaultdict(lambda: np.inf)
    for k, (u, d) in inv.items(): z[P[k]["up"]] = min(z[P[k]["up"]], u); z[P[k]["dn"]] = min(z[P[k]["dn"]], d)
    return {n: ground[n] - v for n, v in z.items()}


# ------------------------------------------------------------------ check the re-lay against the design
base, S_base = relay(None)
err = np.array([abs((ground[P[k]["up"]] - base[k][0]) - P[k]["du"]) for k in P] + [abs((ground[P[k]["dn"]] - base[k][1]) - P[k]["dd"]) for k in P])
print(f"{CASE}: re-lay reproduces the design depths: 95 % within {np.percentile(err, 95):.3f} m, max {err.max():.3f} m")


def lower_branches(inv, S, smax, allow):
    """F2: lower every branch arriving more than 2 m above its outgoing invert. allow(n, old_drop) = the highest drop a
    manhole of the branch may take after lowering (0.6 / its existing drop for F2a; 2.0 for F2b)."""
    inv, S = dict(inv), dict(S); fails = set()

    def lower(k, target, log):
        u, d = inv[k]
        if d <= target + 1e-9: return True
        p = P[k]; sm = max(S[k], smax(k))
        if (u - target) / p["L"] <= sm:
            log.append(k); inv[k] = (u, target); S[k] = (u - target) / p["L"]; return True
        nu = target + sm * p["L"]; U = p["up"]
        if ground[U] - nu > MH_CAP: return False
        log.append(k); inv[k] = (nu, target); S[k] = sm
        for j in into.get(U, []):
            old = inv[j][1] - u; new = inv[j][1] - nu
            if new > allow(U, old) + 1e-9:
                if not lower(j, nu + allow(U, old), log): return False
        return True

    for n in [P[k]["dn"] for k in order]:
        if n not in out_of or not out_of[n]: continue
        u = inv[out_of[n][0]][0]
        for k in list(into[n]):
            if inv[k][1] - u > BD + 1e-9:
                snap_i, snap_s, log = dict(inv), dict(S), []
                if not lower(k, u + BD, log):
                    inv, S = snap_i, snap_s; fails.add((n, k))
    return inv, S, fails


def lower_branches_one(inv, S, smax, n0, k0):
    """F2b for one drop only (to cost it alone)."""
    inv, S = dict(inv), dict(S)
    def lower(k, target):
        u, d = inv[k]
        if d <= target + 1e-9: return True
        p = P[k]; sm = max(S[k], smax(k))
        if (u - target) / p["L"] <= sm: inv[k] = (u, target); S[k] = (u - target) / p["L"]; return True
        nu = target + sm * p["L"]; U = p["up"]
        if ground[U] - nu > MH_CAP: return False
        inv[k] = (nu, target); S[k] = sm
        return all(lower(j, nu + BD) for j in into.get(U, []) if inv[j][1] - nu > BD + 1e-9)
    u = inv[out_of[n0][0]][0]; snap = dict(inv)
    ok = lower(k0, u + BD)
    return (inv, S, ok) if ok else (snap, S, ok)


# ------------------------------------------------------------------ costs at the BOQ rates
RATES = r"W:\2621 Design and Supervision for STP, Sewer & TE Networks System in Ibri_NAMA\06-WORKING\04-Hydraulic\11_Finacial\2621 - Options Cost Estimation-MH 14-10-2026.xlsx"
wb = load_workbook(RATES, data_only=True); ws = wb["Pipe Rate"]; hdr = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
pipe_rate, sec = {}, "sewer"
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == "Force/TSE Pipes": sec = "force"; continue
    if sec == "sewer" and isinstance(row[0], (int, float)): pipe_rate[int(row[0])] = {hdr[i]: row[i] for i in range(1, len(hdr)) if hdr[i] and isinstance(row[i], (int, float))}
ws = wb["Manhole Rate"]; mh_hdr = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
mh_rate = {row[0]: {mh_hdr[i]: row[i] for i in range(1, len(mh_hdr)) if mh_hdr[i] and isinstance(row[i], (int, float))} for row in ws.iter_rows(min_row=2, max_row=4, values_only=True)}
def band(d):
    if d <= 1.5: return "Up to 1.5"
    if d > 15: return "Over 15.0"
    a = math.floor(d * 2) / 2 if (d * 2) % 1 else d - 0.5
    return f"{a:.1f} - {a + 0.5:.1f}"
def rp(dn, d):
    r = pipe_rate[min(pipe_rate, key=lambda x: (x < dn, x))] if dn not in pipe_rate else pipe_rate[dn]; b = band(d)
    return r[b] if b in r else r["14.5 - 15.0"] * 1.11
def rm(t, d):
    r = mh_rate[t]; b = band(d); return r[b] if b in r else r["14.5 - 15.0"] * 1.11
big_dn = collections.defaultdict(int)
for p in P.values(): big_dn[p["up"]] = max(big_dn[p["up"]], p["dn_mm"]); big_dn[p["dn"]] = max(big_dn[p["dn"]], p["dn_mm"])
mh_t = lambda n: "Type 1 - 1200 mm" if big_dn[n] <= 355 else "Type 2 - 1500 mm" if big_dn[n] <= 560 else "Type 3 - 1800 mm"


def cost(inv):
    c = sum(P[k]["L"] * rp(P[k]["dn_mm"], ((ground[P[k]["up"]] - u) + (ground[P[k]["dn"]] - d)) / 2) for k, (u, d) in inv.items())
    nd = node_depth(inv)
    return c + sum(rm(mh_t(n), dd) for n, dd in nd.items() if N.at[n, "kind"] == "manhole")


def under075(S):
    km = 0.0
    for k, s in S.items():
        p = P[k]
        if p["dn_mm"] > 200 and round(velocity(p["Q31"], p["D"], s), 2) < 0.75: km += p["L"]   # two decimals, as the design
    return km / 1000


# ------------------------------------------------------------------ the variants
smax4 = lambda k: min(S_CLIENT, SMAX_V[k])                          # 4 %, never past 3 m/s
smaxv = lambda k: max(P[k]["S0"], SMAX_V[k])
V = collections.OrderedDict()
V["0 design as laid"] = (base, S_base, set())
inv1, S1 = relay(smax4); V["F1 regrade, 4 %"] = (inv1, S1, set())
inv1v, S1v = relay(smaxv); V["F1 regrade, 3 m/s"] = (inv1v, S1v, set())
d0 = drops(base)
keep_or = lambda limit: (lambda n, old: max(limit, old))
V["F1+F2a steepen only, 4 %"] = lower_branches(inv1, S1, smax4, keep_or(NOBD))
V["F1+F2b steepen and step down, 4 %"] = lower_branches(inv1, S1, smax4, lambda n, old: BD)
V["F1+F2b steepen and step down, 3 m/s"] = lower_branches(inv1v, S1v, smaxv, lambda n, old: BD)
c0 = cost(base); rows = []
for name, (inv, S, fails) in V.items():
    dr = drops(inv); nd = node_depth(inv); mh = {n: v for n, v in nd.items() if N.at[n, "kind"] == "manhole"}
    st = {n: v for n, v in nd.items() if N.at[n, "kind"] != "manhole"}
    n2 = sum(1 for v in dr.values() if v > BD + 1e-6); m2 = len({n for (n, k), v in dr.items() if v > BD + 1e-6})
    rows.append(dict(variant=name, drops_over_2m=n2, manholes_with_drop_over_2m=m2, backdrops_06_2m=sum(1 for v in dr.values() if NOBD + 1e-6 < v <= BD + 1e-6),
                     manholes_deeper_12m=sum(1 for v in mh.values() if v > 12), deepest_manhole_m=round(max(mh.values()), 2),
                     deepest_station_m=round(max(st.values()), 2), pipes_regraded=sum(1 for k in S if S[k] > P[k]["S0"] + 1e-9),
                     max_velocity_ms=round(max(velocity(P[k]["Q"], P[k]["D"], S[k]) for k in S if S[k] > P[k]["S0"] + 1e-9) if any(S[k] > P[k]["S0"] + 1e-9 for k in S) else 0, 2),
                     km_under_075_2031=round(under075(S), 2), cost_change_MOMR=round((cost(inv) - c0) / 1e6, 2), failed_lowerings=len(fails)))
    print(rows[-1])
VT = pd.DataFrame(rows); VT.to_csv(os.path.join(OUT, "variants.csv"), index=False)

# ------------------------------------------------------------------ every drop over 2 m of the design, and what removes it
best = "F1+F2b steepen and step down, 4 %"
inv_b, S_b, _ = V[best]; d_f1 = drops(inv1); d_b = drops(inv_b); d_a = drops(V["F1+F2a steepen only, 4 %"][0]); d_v = drops(V["F1+F2b steepen and step down, 3 m/s"][0])
main_of = {n: max(ks, key=lambda k: P[k]["Q"]) for n, ks in into.items()}
nd0 = node_depth(base); ndb = node_depth(inv_b)
rec = []
for (n, k), v in d0.items():
    if v <= BD + 1e-6: continue
    # the ground along the outgoing deep sewer, 300 m downstream: falls (>= 0.5 %), flat, or rises somewhere
    path, m, L = [], n, 0.0
    while m in out_of and out_of[m] and L < 300: kk = out_of[m][0]; path.append(kk); L += P[kk]["L"]; m = P[kk]["dn"]
    gl = [ground[n]] + [ground[P[kk]["dn"]] for kk in path]
    trend = "falls" if L > 0 and (gl[0] - gl[-1]) / L >= 0.005 and max(gl) <= gl[0] + 0.5 else ("rises" if max(gl) > gl[0] + 0.5 else "flat")
    # the branch: pipes above the junction until the next junction or head
    blen, b = 0.0, k
    while True:
        blen += P[b]["L"]; ins = into.get(P[b]["up"], [])
        if len(ins) != 1: break
        b = ins[0]
    xb = 0.0
    fix = ("F1 regrade" if d_f1[(n, k)] <= BD + 1e-6 else "F2a steepen" if d_a[(n, k)] <= BD + 1e-6 else "F2b steepen and step down"
           if d_b[(n, k)] <= BD + 1e-6 else "F2b at 3 m/s only" if d_v[(n, k)] <= BD + 1e-6 else "not by F1/F2")
    rec.append(dict(manhole=n, pipe=k, role="main line" if main_of[n] == k else "branch", drop_m=round(v, 2), drop_after_m=round(d_b[(n, k)], 2),
                    fix=fix, receiving_depth_m=round(nd0[n], 2), depth_after_m=round(ndb[n], 2), branch_m=round(blen, 0), ground_downstream=trend,
                    x=N.at[n, "x"], y=N.at[n, "y"], dn_in=P[k]["dn_mm"], dn_out=P[out_of[n][0]]["dn_mm"]))
DR = pd.DataFrame(rec)


def local_cost(inv_a, inv_b, ks):
    nodes = {P[k]["up"] for k in ks} | {P[k]["dn"] for k in ks}
    def pc(inv, k):
        u, d = inv[k]; return P[k]["L"] * rp(P[k]["dn_mm"], ((ground[P[k]["up"]] - u) + (ground[P[k]["dn"]] - d)) / 2)
    def nz(inv, n):
        z = min([inv[k][0] for k in out_of.get(n, [])] + [inv[k][1] for k in into.get(n, [])]); return ground[n] - z
    c = sum(pc(inv_b, k) - pc(inv_a, k) for k in ks)
    return c + sum(rm(mh_t(n), nz(inv_b, n)) - rm(mh_t(n), nz(inv_a, n)) for n in nodes if N.at[n, "kind"] == "manhole")


def cost_alone(base_inv, base_S, smax, n, k):
    i2, s2, ok = lower_branches_one(base_inv, base_S, smax, n, k)
    if not ok: return np.nan
    ch = [j for j in P if i2[j] != base_inv[j]]
    return local_cost(base_inv, i2, ch) if ch else 0.0


c4, c3 = [], []
d_f1v = drops(inv1v)
for r in DR.itertuples():
    c4.append(0.0 if d_f1[(r.manhole, r.pipe)] <= BD + 1e-6 else cost_alone(inv1, S1, smax4, r.manhole, r.pipe))
    c3.append(0.0 if d_f1v[(r.manhole, r.pipe)] <= BD + 1e-6 else cost_alone(inv1v, S1v, smaxv, r.manhole, r.pipe))
DR["cost_4pc_OMR"] = np.round(c4, 0); DR["cost_3ms_OMR"] = np.round(c3, 0)
DR["vortex_floor_OMR"] = [round(rm("Type 3 - 1800 mm", d), 0) for d in DR.receiving_depth_m]
hard = ~((DR.cost_4pc_OMR <= DR.vortex_floor_OMR) | (DR.cost_3ms_OMR <= DR.vortex_floor_OMR))

# F4 reconnect, for the hard ones: another manhole within 100 m of the branch's last manhole, not upstream of it,
# low enough for a gravity pipe at 0.5 % and a drop of 2 m or less
xy = N[["x", "y"]]; nd1 = node_depth(inv1); inv_node = {n: ground[n] - d for n, d in nd1.items()}
DR["reconnect_to"], DR["reconnect_m"] = None, np.nan
for i, r in DR[hard].iterrows():
    b_up = P[r["pipe"]]["up"]; zb = inv1[r["pipe"]][0]
    up_set, stack = {b_up}, [b_up]
    while stack:
        m = stack.pop()
        for j in into.get(m, []): up_set.add(P[j]["up"]); stack.append(P[j]["up"])
    dx = np.hypot(xy.x - xy.at[b_up, "x"], xy.y - xy.at[b_up, "y"]); best_c = None
    for m in dx[(dx > 1) & (dx <= 100)].index:
        if m in up_set or m == r.manhole or m not in inv_node or N.at[m, "kind"] != "manhole": continue
        dc = zb - 0.005 * dx[m] - inv_node[m]
        if 0 <= dc <= BD and (best_c is None or dx[m] < best_c[1]): best_c = (m, dx[m])
    if best_c: DR.at[i, "reconnect_to"], DR.at[i, "reconnect_m"] = best_c[0], round(best_c[1], 0)

# F3 parallel shallow sewer: the hard drops left, grouped by the deep sewer they join (downstream paths within 300 m meet)
left = DR[hard & DR.reconnect_to.isna()]
grp, path_of = {}, {}
for i, r in left.iterrows():
    s, m, L = set(), r.manhole, 0.0
    while m in out_of and out_of[m] and L < 300: kk = out_of[m][0]; L += P[kk]["L"]; m = P[kk]["dn"]; s.add(m)
    path_of[i] = s | {r.manhole}
ids = list(path_of); parent = {i: i for i in ids}
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
for a in range(len(ids)):
    for b in range(a + 1, len(ids)):
        if path_of[ids[a]] & path_of[ids[b]]: parent[find(ids[a])] = find(ids[b])
DR["stretch"] = None
for i in ids: DR.at[i, "stretch"] = find(i)
size = DR.groupby("stretch").size()

def recommend(r):
    if r.fix == "F1 regrade": return "F1 regrade"
    if r.cost_4pc_OMR <= r.vortex_floor_OMR: return "F2 lower the branch, 4 %"
    if r.cost_3ms_OMR <= r.vortex_floor_OMR: return "F2 lower the branch, steeper than 4 % (to 3 m/s)"
    if r.reconnect_to is not None: return "F4 reconnect (candidate)"
    if r.stretch is not None and size.get(r.stretch, 1) > 1 and r.ground_downstream == "falls": return "F3 parallel shallow sewer"
    return "vortex drop shaft"
DR["recommended"] = DR.apply(recommend, axis=1)
DR.to_csv(os.path.join(OUT, "drops.csv"), index=False)
gpd.GeoDataFrame(DR.drop(columns=["x", "y"]), geometry=[Point(a, b) for a, b in zip(DR.x, DR.y)], crs="EPSG:32640").to_file(
    os.path.join(OUT, f"drops_{CASE}.gpkg"), layer="drops_over_2m", driver="GPKG")
rec_ct = DR.recommended.value_counts().to_dict()
shafts = int((DR.recommended == "vortex drop shaft").sum() + DR[DR.recommended == "F3 parallel shallow sewer"].stretch.nunique())
S = dict(case=CASE, drops_over_2m=int(len(DR)), manholes=int(DR.manhole.nunique()), by_role=DR.role.value_counts().to_dict(),
         recommended=rec_ct, vortex_shafts_left=shafts,
         cost_4pc_total_OMR=float(DR.loc[DR.recommended == "F2 lower the branch, 4 %", "cost_4pc_OMR"].sum()),
         cost_3ms_total_OMR=float(DR.loc[DR.recommended == "F2 lower the branch, steeper than 4 % (to 3 m/s)", "cost_3ms_OMR"].sum()),
         by_ground=DR.ground_downstream.value_counts().to_dict(), variants=VT.to_dict(orient="records"))
json.dump(S, open(os.path.join(OUT, "summary.json"), "w"), indent=1, default=str)
print(json.dumps({k: S[k] for k in ("drops_over_2m", "manholes", "by_role", "recommended", "vortex_shafts_left", "cost_4pc_total_OMR", "cost_3ms_total_OMR")}, indent=1))
