"""W18 (engineer, 2026-11-17): steepen the pipes above DN200 to reach 0.75 m/s at their 2031 peak flow, up to 1 %; where
that leaves a subnetwork more than 12 m deep FOR GOOD (no manhole between there and its outfall comes back to 12 m or
less), CUT it: the last manhole at 12 m or less becomes a pumping station (a new outfall) and its flow is lifted to the
next manhole, which starts again as a head at minimum cover. Dips that come back to 12 m or less are left alone.
Where an outfall (an existing station, any subnetwork) ends at 12 m or less and the manhole its flow is pumped to lies
within one standard manhole spacing (PAM-GUD-203 Table 12, p30: DN200-315 100 m, 350-900 120 m, 1000-1400 150 m,
over 1400 200 m), JOIN it by gravity instead; that re-lays the receiving subnetwork from the join down, which may call
for a new cut - a join is kept only if the stations in all go down. Repeat until nothing changes. Fewest stations.

Re-lay (reproduces the SewerGEMS design, checked on every pipe): a pipe's upstream invert = the lowest of the lowest
invert arriving at its upstream manhole and the shallowest invert its cover allows (1.3 m over the soffit at both ends,
the design's minimum cover: every one of the 3,612 head pipes of SC1-2056 sits exactly there); downstream invert =
upstream - gradient x length. Depth = ground - invert at a manhole. Outfalls are not in the manhole export: an
outfall takes the ground of the manhole above it. A cut keeps the pipe's length as the station's rising main.
Velocity: Colebrook-White, ks 1.5 mm, nu 1.141e-6 (as py/selfcleansing_slope.py, checked against SewerGEMS).

Engineer, 2026-11-18:
- An OUTFALL IS NEVER MOVED: a cut is a split of the network, so no cut is made on the last pipe into an outfall that
  is still an outfall (a pumping station or the plant inlet); such an outfall keeps its depth and is listed.
- SUCCESSIVE PIPES IN A STREET KEEP ONE GRADIENT. A street run follows, at each manhole, the arriving pipe of the same
  size that continues the leaving pipe's line within 30 degrees; it breaks where the line turns or the size changes.
  A run's gradient is the steepest that any of its pipes needs to reach 0.75 m/s at the 2031 peak, within the limit
  (a pipe that needs more than the limit does not set it); each pipe above DN200 in the run takes the steeper of that
  gradient and its laid one (a pipe laid steeper by the ground keeps its own).
- MAXIMUM VELOCITY 3.0 m/s at the design flow (PAM-GUD-203 p27): every pipe's 2056 velocity is checked.
Velocities reported: SewerGEMS's own (2031 and 2056 analyses), scaled by the Colebrook-White ratio where the gradient
changed. Pipe lines and the outfalls' ground and position come from the model's own geometry (the W17 option
GeoPackage S1.gpkg, same labels).

Usage: python split_deep_subnetworks.py <tag, e.g. SC1-2056> <export dir> <out dir> [threshold gradient, default 0.01]
       [--design]   (condition 0: the network as designed - no steepening, no cuts - for the velocity map)
Writes <out>/cuts_<tag>.csv, joins_<tag>.csv, nodes_<tag>.csv, pipes_<tag>.csv, SUMMARY.md, summary_<tag>.json,
map_<tag>.png and split_<tag>.gpkg (layers pipes, outfalls, rising_mains_new, deep_before_split, manholes_deep)."""
import sys, os, math, re, json
import numpy as np, pandas as pd

G, NU, KS, V_SC, V_MAX = 9.81, 1.141e-6, 1.5e-3, 0.75, 3.0
COVER, DMAX, TURN = 1.3, 12.0, 30.0
# outfalls the engineer keeps deep rather than cut next to them (2026-11-18): the cut left one 62 m pipe (O14) or 365 m
# with one branch (O11) between the new station and the outfall - in effect the outfall moved, not the network split.
# No cut is made in these subnetworks; the outfall keeps its depth (O14 12.73 m, O11 12.13 m as designed).
KEEP_DEEP = {"O14", "O11"}
# the engineer's station decisions (2026-11-18, on the SC1-2056 map at 0.50 %; py/whatif_merge_stations.py): a subnetwork
# listed here is not searched for cuts - its new stations are exactly these manholes (none: the outfall is kept deep).
# O12: neither O12-M26 nor O12-M193, outfall 14.6 m accepted. O9: O9-M103 and O9-M89 as one station at O9-M101 (12.6 m
# accepted), O9-M728 removed and O9-M773 kept (O9 outfall 14.3 m accepted). A gravity join may not deepen these outfalls.
FIXED = {("SC1-2056", 0.005): {"O12": [], "O9": ["O9-M773", "O9-M166", "O9-M101"]},
         # his logic learnt and applied to every subnetwork at 0.75 % and 1.00 % (engineer: "learn from my logic",
         # 2026-11-18; py/reduce_stations.py: drop or merge while a new station <= 12.65 m, an outfall <= 14.65 m and no
         # manhole > 16.5 m); O12 kept deep as he decided at 0.50 % although its outfall is 14.71 m there (8 cm over)
         ("SC1-2056", 0.0075): {"O12": [], "O9": ["O9-M101", "O9-M166", "O9-M72", "O9-M773"]},
         ("SC1-2056", 0.01): {"O12": [], "O9": ["O9-M101", "O9-M166", "O9-M2805", "O9-M69", "O9-M773"]}}
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
DESIGN = "--design" in sys.argv
tag, src, out = ARGS[0], ARGS[1], ARGS[2]
T = 0.0 if DESIGN else (float(ARGS[3]) if len(ARGS) > 3 else 0.01)
FIX = {} if DESIGN or "--no-fixed" in sys.argv else FIXED.get((tag, round(T, 4)), {})   # --no-fixed: the split as searched
_FX = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--fixed=")]          # --fixed=<json>: {tag: {sub: [stations]}}
if _FX and not DESIGN: FIX = json.load(open(_FX[0], encoding="utf-8")).get(tag, {})   # (the final designs, 2026-11-18)
os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.environ["W19_CASE_ROOT"]   # W19: a work root, never W18
GEO = os.path.join(W18, "geo", "S1.gpkg")


def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)


def v_cw(R, S):
    a = math.sqrt(8 * G * R * S); return -2 * a * math.log10(KS / (14.8 * R) + 2.51 * NU / (4 * R * a))


def velocity(Q, D, S):
    if Q <= 0 or S <= 0: return 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2; A, R = section(D, y)
        if A * v_cw(R, S) > Q: hi = y
        else: lo = y
    A, R = section(D, (lo + hi) / 2); return Q / A


def slope_for(Q, D, vt=V_SC):
    """The gradient at which the Colebrook-White velocity reaches vt."""
    if Q <= 0 or velocity(Q, D, 1.0) < vt: return np.nan
    lo, hi = 1e-6, 1.0
    for _ in range(45):
        s = math.sqrt(lo * hi)
        if velocity(Q, D, s) < vt: lo = s
        else: hi = s
    return hi


def spacing(nominal_mm):                              # PAM-GUD-203 Table 12 (p30), maximum manhole spacing
    return 100.0 if nominal_mm <= 315 else 120.0 if nominal_mm <= 900 else 150.0 if nominal_mm <= 1400 else 200.0


# ------------------------------------------------------------------ the designed network
dy = pd.read_csv(os.path.join(src, f"conduits_{tag}a.csv")); dy = dy[dy.active == True].copy()
d31 = pd.read_csv(os.path.join(src, f"conduits_{tag}-at-2031.csv")).set_index("label")
mh = pd.read_csv(os.path.join(src, f"manholes_{tag}a.csv")).set_index("id")
tr_all = pd.read_csv(os.path.join(src, f"transfers_{tag}.csv"))
tr = tr_all[tr_all.year == int(tag.split("-")[1])]
tr31 = tr_all[tr_all.year == 2031].set_index("source").flow_m3d
rm = pd.read_csv(os.path.join(W18, "results", "rising_mains.csv"))
dy["UP"] = np.where(dy.start_inv >= dy.stop_inv, dy.start, dy.stop); dy["DN"] = np.where(dy.start_inv >= dy.stop_inv, dy.stop, dy.start)
dy["UPI"] = dy[["start_inv", "stop_inv"]].max(axis=1); dy["DNI"] = dy[["start_inv", "stop_inv"]].min(axis=1)
dy["S_LAID"] = (dy.UPI - dy.DNI) / dy.length_m; dy["D"] = dy.diameter_mm / 1000.0
dy["NOM"] = dy.size_label.str.extract(r"(\d+)")[0].astype(float)
dy["Q31"] = d31.flow_m3d.reindex(dy.label).values / 86400.0
dy["SUB"] = dy.label.str.split("-").str[0]
dy["Q56"] = dy.flow_m3d / 86400.0
dy["V56_SG"] = dy.velocity_ms; dy["V31_SG"] = d31.velocity_ms.reindex(dy.label).values
big = (dy.NOM > 200).values
# the gradient at which SewerGEMS's own 2031 velocity reaches 0.75 m/s: SewerGEMS's velocity scales with the
# Colebrook-White ratio, so the Colebrook-White target is 0.75 x (Colebrook-White / SewerGEMS) at the laid gradient
def _target(q, d, s0, v_sg):
    v_cw = velocity(q, d, s0)
    return V_SC * v_cw / v_sg if v_sg > 0 and v_cw > 0 else V_SC
dy["S_REQ"] = [slope_for(q, d, _target(q, d, s0, v)) if b else np.nan
               for q, d, s0, v, b in zip(dy.Q31, dy.D, dy.S_LAID, dy.V31_SG, big)]
lab = mh.label.to_dict(); xy = {i: (r.x, r.y) for i, r in mh.iterrows()}

# street runs: at each manhole the leaving pipe continues the arriving pipe of the same size closest to its line,
# if within 30 degrees (the network is a tree, so each pipe has at most one continuation downstream)
def _az(u, d):
    a, b = xy.get(u), xy.get(d)
    if a is None or b is None or a == b: return np.nan
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
dy["AZ"] = [_az(u, d) for u, d in zip(dy.UP, dy.DN)]
leaving = dict(zip(dy.UP, dy.index)); pred = {}
for n, grp in dy.groupby("DN"):
    k = leaving.get(n)
    if k is None or np.isnan(dy.at[k, "AZ"]): continue
    best_j = None
    for j in grp.index:
        if dy.at[j, "NOM"] != dy.at[k, "NOM"] or np.isnan(dy.at[j, "AZ"]): continue
        dfl = abs((dy.at[k, "AZ"] - dy.at[j, "AZ"] + 180) % 360 - 180)
        if dfl <= TURN and (best_j is None or dfl < best_j[0]): best_j = (dfl, j)
    if best_j: pred[k] = best_j[1]
succ = {j: k for k, j in pred.items()}; run_of = {}
for h in dy.index:
    if h in pred: continue
    k = h
    while k is not None: run_of[k] = h; k = succ.get(k)
dy["RUN"] = pd.Series(run_of)
assert dy.RUN.notna().all()
reach_ok = big & np.isfinite(dy.S_REQ.values) & (dy.S_REQ.values <= T)
need = reach_ok & (dy.S_REQ.values > dy.S_LAID.values)
s_run = dy.S_REQ.where(need).groupby(dy.RUN).max()   # the steepest need within the limit sets the run's gradient
dy["S_RUN"] = dy.RUN.map(s_run)
steep = big & dy.S_RUN.notna().values & (dy.S_RUN.values > dy.S_LAID.values + 1e-9)
dy["S_NEW"] = np.where(steep, dy.S_RUN, dy.S_LAID)
dy["STEEP"] = steep


def _scaled(v_sg, q, d, s0, s1):
    if not (s1 > s0 + 1e-12) or q <= 0: return v_sg
    return v_sg * velocity(q, d, s1) / velocity(q, d, s0)
dy["V31"] = [_scaled(v, q, d, s0, s1) for v, q, d, s0, s1 in zip(dy.V31_SG, dy.Q31, dy.D, dy.S_LAID, dy.S_NEW)]
dy["V56"] = [_scaled(v, q, d, s0, s1) for v, q, d, s0, s1 in zip(dy.V56_SG, dy.Q56, dy.D, dy.S_LAID, dy.S_NEW)]

ground = mh.ground.where(mh.ground > 100).to_dict()
import geopandas as gpd
from shapely.geometry import Point, LineString
geo_pipes = gpd.read_file(GEO, layer="pipes").set_index("label").geometry
geo_out = gpd.read_file(GEO, layer="outfalls").set_index("label")
terminals = sorted(set(dy.DN) - set(dy.UP))
above = dy.groupby("DN").UP.first()
for t in terminals:                                  # an outfall's ground and position: the model's own outfall
    lab[t] = dy.loc[dy.DN == t, "SUB"].iloc[0]
    if lab[t] in geo_out.index:
        o = geo_out.loc[lab[t]]; ground[t] = float(o.ground); xy[t] = (o.geometry.x, o.geometry.y)
    else:                                            # else the ground and position of the manhole above it
        u = above[t]; ground[t] = ground.get(u, np.nan); xy[t] = xy.get(u, (np.nan, np.nan))
sub_terminal = {lab[t]: t for t in terminals}

links = {}                                            # id -> dict(up, dn, L, D, S, nom, sub, kind)
for r in dy.itertuples():
    links[r.Index] = dict(up=r.UP, dn=r.DN, L=r.length_m, D=r.D, S=r.S_NEW, S0=r.S_LAID, nom=r.NOM, sub=r.SUB, kind="pipe", label=r.label)


def cover_limit(k):                                   # shallowest upstream invert the cover allows on link k
    l = links[k]; gu, gd = ground.get(l["up"], np.nan), ground.get(l["dn"], np.nan)
    c = [x for x in (gu - (COVER + l["D"]), gd - (COVER + l["D"]) + l["S"] * l["L"]) if not np.isnan(x)]
    return min(c) if c else np.inf


def relay(active):
    """Re-lay the network made of the active links; returns node inverts and, per link, (up, dn) inverts."""
    out_of, indeg = {}, {}
    for k in active:
        l = links[k]; out_of.setdefault(l["up"], []).append(k); indeg[l["dn"]] = indeg.get(l["dn"], 0) + 1
    nodes = {links[k]["up"] for k in active} | {links[k]["dn"] for k in active}
    stack = [n for n in nodes if indeg.get(n, 0) == 0]; arr, crown, inv, li = {}, {}, {}, {}
    while stack:
        n = stack.pop()
        for k in out_of.get(n, []):
            l = links[k]
            # crowns matched: the outgoing soffit is never above an incoming soffit (nor its invert above an incoming invert)
            u = min(arr.get(n, np.inf), crown.get(n, np.inf) - l["D"], cover_limit(k))
            d = u - l["S"] * l["L"]; li[k] = (u, d)
            inv[n] = min(inv.get(n, np.inf), u, arr.get(n, np.inf))
            arr[l["dn"]] = min(arr.get(l["dn"], np.inf), d)
            crown[l["dn"]] = min(crown.get(l["dn"], np.inf), d + l["D"])
            indeg[l["dn"]] -= 1
            if indeg[l["dn"]] == 0: stack.append(l["dn"])
    for n, a in arr.items(): inv[n] = min(inv.get(n, np.inf), a)
    assert len(li) == len(active), "not a tree"
    return inv, li


def depths(inv):
    return {n: ground[n] - v for n, v in inv.items() if not np.isnan(ground.get(n, np.nan))}


# check: with the laid gradients the cover rule reproduces the designed inverts
for k, r in zip(dy.index, dy.itertuples()): links[k]["UP0"] = r.UPI
_save = {k: links[k]["S"] for k in links}
for k in links: links[k]["S"] = links[k]["S0"]
inv_chk, li_chk = relay(list(links))
err = np.array([abs(li_chk[k][0] - links[k]["UP0"]) for k in links])
for k in links: links[k]["S"] = _save[k]
base_inv = inv_chk; base_depth = depths(base_inv)

# ------------------------------------------------------------------ cuts and joins
def downstream_map(active):
    return {links[k]["up"]: k for k in active}


def regions(active, inv):
    """Nodes more than 12 m deep for good (every node from there to the outfall deeper than 12 m), per terminal."""
    dep = depths(inv); nxt = downstream_map(active)
    order = []; out_of, indeg = {}, {}
    for k in active:
        l = links[k]; out_of.setdefault(l["up"], []).append(k); indeg[l["dn"]] = indeg.get(l["dn"], 0) + 1
    nodes = {links[k]["up"] for k in active} | {links[k]["dn"] for k in active}
    stack = [n for n in nodes if indeg.get(n, 0) == 0]
    while stack:
        n = stack.pop(); order.append(n)
        for k in out_of.get(n, []):
            indeg[links[k]["dn"]] -= 1
            if indeg[links[k]["dn"]] == 0: stack.append(links[k]["dn"])
    mind = {}
    for n in reversed(order):
        d = dep.get(n, np.inf)
        # a deep stretch must come back within its OWN subnetwork: the walk stops at a subnetwork's outfall even when
        # that outfall now joins the next subnetwork by gravity (else a join could leave kilometres of 25 m sewer)
        mind[n] = min(d, mind[links[nxt[n]]["dn"]]) if n in nxt and n not in orig_terminals else d
    return {n for n, v in mind.items() if v > DMAX and v != np.inf}, dep, nxt


def governing_cut(active, inv, li, R, terminal):
    """Walk up from a deep outfall along the link that sets each node's invert; cut where the walk leaves the region."""
    # an outfall kept deep, or any outfall of a subnetwork whose stations the engineer fixed (its own outfall or one of
    # the fixed stations, labelled e.g. O9-M101): no cut is searched above it
    if lab.get(terminal) in KEEP_DEEP or str(lab.get(terminal)).split("-")[0] in FIX: return None
    into = {}
    for k in active: into.setdefault(links[k]["dn"], []).append(k)
    ups = {links[k]["up"] for k in active}
    n = terminal
    while True:
        cands = into.get(n, [])
        if not cands: return None
        k = min(cands, key=lambda c: li[c][1])                 # the arriving link with the lowest invert sets the depth
        u = links[k]["up"]
        if u not in R:                                         # u is at 12 m or less: the station goes here ...
            # ... unless the pipe ends in an outfall that is still one: that would move the outfall, not split
            # the network (engineer, 2026-11-18) - the outfall keeps its depth
            if links[k]["dn"] in orig_terminals and links[k]["dn"] not in ups: return None
            return k
        n = u


def solve(active, pumps_in):
    """Cut until no node is deeper than 12 m for good. Returns the active links, the cuts and the final inverts."""
    active = set(active); cuts = []
    if FIX:                                                # the engineer's stations first (round 0), then the search elsewhere
        inv, li = relay(active); dep = depths(inv); nxt = downstream_map(active); node_of = {v: n for n, v in lab.items()}
        for s in (s for st in FIX.values() for s in st):
            n = node_of[s]; k = nxt[n]
            active.discard(k); cuts.append(dict(round=0, link=k, station=n, receiver=links[k]["dn"],
                                                depth_station=dep.get(n), depth_receiver_before=dep.get(links[k]["dn"])))
    for rnd in range(1, 500):
        inv, li = relay(active)
        R, dep, nxt = regions(active, inv)
        if not R: return active, cuts, inv, li
        ends = [n for n in R if n not in nxt or n in orig_terminals]   # outfalls (joined or not) deeper than 12 m
        k = next((c for c in (governing_cut(active, inv, li, R, t) for t in sorted(ends, key=lambda n: -dep.get(n, 0))) if c is not None), None)
        if k is None: return active, cuts, inv, li
        # one cut per round, then re-lay: a second walk on the same (stale) levels can cut a lateral head
        active.discard(k); cuts.append(dict(round=rnd, link=k, station=links[k]["up"], receiver=links[k]["dn"],
                                            depth_station=dep.get(links[k]["up"]), depth_receiver_before=dep.get(links[k]["dn"])))
    raise RuntimeError("cuts did not converge")


pipes = set(links)
PLANTS = {"SC1": ["O1"], "SC2": ["O16"], "SC3": ["O1", "O4"], "SC4": ["O16", "O4"]}[tag.split("-")[0]]
plants = {sub_terminal[s] for s in PLANTS}
orig_terminals = set(terminals)


def n_stations(active):
    """Pumping stations = outfalls of the network as it stands (a subnetwork outfall pumps, the plant inlet does not)."""
    ups = {links[k]["up"] for k in active}; dns = {links[k]["dn"] for k in active}
    return len((dns - ups) - plants)


transfers = []
for r in tr.itertuples():
    t = sub_terminal.get(r.source)
    if t is None: continue
    m = rm[(rm.source == r.source) & (rm.dest == r.receiver_label)]
    last = dy[dy.DN == t].iloc[0]
    transfers.append(dict(source=r.source, terminal=t, receiver=int(r.receiver_id), receiver_label=r.receiver_label,
                          length=float(m.length_m.iloc[0]) if len(m) else np.nan, nom=last.NOM, D=last.D,
                          S=last.S_NEW, flow_m3d=r.flow_m3d, flow31_m3d=float(tr31.get(r.source, np.nan))))
if DESIGN:                                           # condition 0: the network as designed, nothing cut or joined
    inv0, li0 = relay(pipes); active0, cuts0 = set(pipes), []
else:
    active0, cuts0, inv0, li0 = solve(pipes, len(transfers))
best = dict(active=active0, cuts=cuts0, inv=inv0, li=li0, joins=[])
joins_log = []
changed = not DESIGN
while changed:
    changed = False
    joined = {j["source"] for j in best["joins"]}
    dep_now = depths(best["inv"])
    for t in sorted(transfers, key=lambda x: -dep_now.get(x["terminal"], 0)):
        if t["source"] in joined: continue
        d_out = dep_now.get(t["terminal"], np.nan)
        lim = spacing(t["nom"])
        why = None
        if np.isnan(t["length"]): why = "no rising-main length"
        elif t["length"] > lim: why = f"rising main {t['length']:.0f} m > {lim:.0f} m (Table 12, DN{t['nom']:.0f})"
        elif not (d_out <= DMAX): why = f"outfall {d_out:.1f} m deep"
        if why:
            joins_log.append(dict(source=t["source"], receiver=t["receiver_label"], length_m=t["length"], outfall_depth_m=d_out, result="kept as a station", why=why))
            continue
        k = ("join", t["source"])
        links[k] = dict(up=t["terminal"], dn=t["receiver"], L=t["length"], D=t["D"], S=t["S"], S0=t["S"], nom=t["nom"],
                        sub=t["source"], kind="join", label=f"{t['source']}->{t['receiver_label']}")
        # every trial starts again from the whole network with the joins so far: earlier cuts are not carried over
        trial = pipes | {("join", j["source"]) for j in best["joins"]} | {k}
        act, cts, inv, li = solve(trial, 0)
        n_before, n_after = n_stations(best["active"]), n_stations(act)
        # a subnetwork the engineer keeps uncut cannot be relieved by a cut, so a join may not deepen its outfall
        # (2026-11-18: O12 joined into O11 took the O11 outfall from 12.4 to 15.0 m)
        d_try = depths(inv)
        deepened = [f"{lab[x]} {dep_now.get(x, 0):.1f} -> {d_try.get(x, 0):.1f} m" for x in orig_terminals
                    if (lab.get(x) in KEEP_DEEP or lab.get(x) in FIX) and d_try.get(x, 0) > dep_now.get(x, 0) + 0.01]
        if deepened:
            joins_log.append(dict(source=t["source"], receiver=t["receiver_label"], length_m=t["length"], outfall_depth_m=d_out,
                                  result="kept as a station", why="the join deepens an outfall kept uncut: " + ", ".join(deepened)))
            del links[k]
            continue
        if n_after < n_before:
            best = dict(active=act, cuts=cts, inv=inv, li=li, joins=best["joins"] + [t]); changed = True
            joins_log.append(dict(source=t["source"], receiver=t["receiver_label"], length_m=t["length"], outfall_depth_m=d_out,
                                  result="joined by gravity", why=f"stations {n_before} -> {n_after}"))
            break
        joins_log.append(dict(source=t["source"], receiver=t["receiver_label"], length_m=t["length"], outfall_depth_m=d_out,
                              result="kept as a station", why=f"joining leaves {n_after} stations against {n_before}"))
        del links[k]
    if changed: joins_log = [j for j in joins_log if j["result"] == "joined by gravity"]

# ------------------------------------------------------------------ outputs
inv, li, active = best["inv"], best["li"], best["active"]
dep = depths(inv); R_end, _, _ = regions(active, inv)
ups_f = {links[k]["up"] for k in active}
outf_now = {links[k]["dn"] for k in active} - ups_f              # the outfalls of the network as it stands
cut_ids = {c["station"] for c in best["cuts"]}
cuts = pd.DataFrame(best["cuts"])
if len(cuts):
    cuts["subnetwork"] = [links[k]["sub"] for k in cuts.link]
    cuts["kind"] = "new station"                                  # an outfall is never moved (2026-11-18)
    cuts["depth_station_final"] = [dep.get(n) for n in cuts.station]
    cuts["station"] = [lab.get(n) for n in cuts.station]; cuts["receiver"] = [lab.get(n) for n in cuts.receiver]
    cuts["rising_main_m"] = [links[k]["L"] for k in cuts.link]
    cuts["pipe"] = [links[k]["label"] for k in cuts.link]; cuts["size"] = [f"DN{links[k]['nom']:.0f}" for k in cuts.link]
    cuts["flow_2056_ls"] = [dy.flow_m3d.get(k, np.nan) / 86.4 for k in cuts.link]
    cuts["x"] = [xy[links[k]["up"]][0] for k in cuts.link]; cuts["y"] = [xy[links[k]["up"]][1] for k in cuts.link]
    cut_links = list(cuts.link)
    cuts = cuts.drop(columns=["link"]).sort_values(["subnetwork", "round"])
else:
    cut_links = []
cuts.to_csv(os.path.join(out, f"cuts_{tag}.csv"), index=False, float_format="%.2f")
pd.DataFrame(joins_log).to_csv(os.path.join(out, f"joins_{tag}.csv"), index=False, float_format="%.1f")
steep_inv, steep_li = relay(pipes)                    # steepened, no cut: the deep case the cuts answer
dsteep = depths(steep_inv)
nodes = pd.DataFrame({"label": pd.Series(lab), "ground": pd.Series(ground), "depth_design": pd.Series(base_depth),
                      "depth_steepened": pd.Series(dsteep), "depth_after": pd.Series(dep)})
nodes.to_csv(os.path.join(out, f"nodes_{tag}.csv"), index_label="id", float_format="%.3f")

BANDS = [(0.0, 0.0030, "up to 0.30 %"), (0.0030, 0.0050, "0.30 to 0.50 %"), (0.0050, 0.0075, "0.50 to 0.75 %"),
         (0.0075, 0.0100 + 1e-9, "0.75 to 1.00 %")]
band = lambda s: next((b for lo, hi, b in BANDS if lo < s <= hi), "over 1.00 %")


def geom(k):
    l = links[k]
    if l["kind"] == "pipe" and l["label"] in geo_pipes.index: return geo_pipes[l["label"]]
    return LineString([xy[l["up"]], xy[l["dn"]]])


rows = []
for k in active:
    l = links[k]; u, d = li[k]
    du, dd = ground.get(l["up"], np.nan) - u, ground.get(l["dn"], np.nan) - d
    if l["kind"] == "pipe":
        r = dy.loc[k]; v31, v56, s0, s1, st, run = r.V31, r.V56, r.S_LAID, r.S_NEW, bool(r.STEEP), int(r.RUN)
    else:
        t = next(j for j in best["joins"] if ("join", j["source"]) == k)
        v31, v56 = velocity(t["flow31_m3d"] / 86400.0, l["D"], l["S"]), velocity(t["flow_m3d"] / 86400.0, l["D"], l["S"])
        s0 = s1 = l["S"]; st, run = False, -1
    is_big = l["nom"] > 200
    if l["kind"] == "join": cls = "Gravity join (was a rising main)"
    elif not is_big: cls = "DN200 (not steepened)"
    elif v31 < V_SC: cls = "Above DN200, under 0.75 m/s"
    elif st: cls = "Steepened " + band(s1)
    else: cls = "Above DN200, 0.75 m/s as laid"
    rows.append(dict(label=l["label"], sub=l["sub"], kind=l["kind"], dn_mm=int(l["nom"]), length_m=round(l["L"], 1),
                     s_laid_pc=round(s0 * 100, 3), s_new_pc=round(s1 * 100, 3), steepened=int(st),
                     s_band=band(s1) if st else "", run=run, v2031_ms=round(v31, 3), v2056_ms=round(v56, 3),
                     under075=int(v31 < V_SC), over3=int(v56 > V_MAX), depth_up_m=round(du, 2), depth_dn_m=round(dd, 2),
                     depth_max_m=round(max(du, dd), 2), deep12=int(max(du, dd) > DMAX), map_class=cls, _k=k))
P = pd.DataFrame(rows)
P.drop(columns=["_k"]).to_csv(os.path.join(out, f"pipes_{tag}.csv"), index=False)

orow = []
for n in sorted(outf_now, key=lambda n: str(lab.get(n))):
    kind = "Plant inlet" if n in plants else "New station" if n in cut_ids else "Existing station"
    orow.append(dict(name=lab.get(n), kind=kind, depth_m=round(dep.get(n, np.nan), 2), x=xy[n][0], y=xy[n][1]))
for j in best["joins"]:
    n = j["terminal"]
    orow.append(dict(name=lab.get(n), kind="Joined by gravity", depth_m=round(dep.get(n, np.nan), 2), x=xy[n][0], y=xy[n][1]))
O = pd.DataFrame(orow); O["map_label"] = [f"{a} {b:.1f} m" for a, b in zip(O.name, O.depth_m)]

pipes_only = P[P.kind == "pipe"]; bigP = pipes_only[pipes_only.dn_mm > 200]
km = lambda df: df.length_m.sum() / 1000
mh_dep = {n: v for n, v in dep.items() if n in mh.index}
mh_steep = {n: v for n, v in dsteep.items() if n in mh.index}
mh_base = {n: v for n, v in base_depth.items() if n in mh.index}
S = dict(tag=tag, condition="as designed" if DESIGN else f"steepened up to {T*100:.2f} %, split", limit_pc=T * 100,
         km_total=km(pipes_only), km_dn200=km(pipes_only[pipes_only.dn_mm <= 200]), km_big=km(bigP),
         km_big_under075=km(bigP[bigP.under075 == 1]),
         km_dn200_under075=km(pipes_only[(pipes_only.dn_mm <= 200) & (pipes_only.under075 == 1)]),
         n_steepened=int(pipes_only.steepened.sum()), km_steepened=km(pipes_only[pipes_only.steepened == 1]),
         n_runs_steepened=int(pipes_only[pipes_only.steepened == 1].run.nunique()),
         km_by_band={b: km(pipes_only[(pipes_only.steepened == 1) & (pipes_only.s_band == b)]) for _, _, b in BANDS},
         n_over3=int(P.over3.sum()), v2056_max=float(P.v2056_ms.max()), v2031_max=float(P.v2031_ms.max()),
         stations=n_stations(active), stations_existing=int((O.kind == "Existing station").sum()),
         stations_new=int((O.kind == "New station").sum()), joined=len(best["joins"]), stations_design=n_stations(pipes),
         outfalls_over12=[dict(name=a, depth_m=b) for a, b, c in zip(O.name, O.depth_m, O.kind)
                          if b > DMAX and c != "Joined by gravity"],
         mh_over12=sum(1 for v in mh_dep.values() if v > DMAX), mh_deepest=max(mh_dep.values()),
         mh_over12_design=sum(1 for v in mh_base.values() if v > DMAX), mh_deepest_design=max(mh_base.values()),
         mh_over12_steepened_no_cut=sum(1 for v in mh_steep.values() if v > DMAX),
         mh_deepest_steepened_no_cut=max(mh_steep.values()),
         km_pipes_over12=km(pipes_only[pipes_only.deep12 == 1]),
         relay_check_p99_m=float(np.percentile(err, 99)), relay_check_max_m=float(err.max()),
         engineer_stations={s: v for s, v in FIX.items()})
json.dump(S, open(os.path.join(out, f"summary_{tag}.json"), "w"), indent=1)

L = [f"# {tag}: {S['condition']}", "",
     f"Re-lay check (cover {COVER} m over the soffit, laid gradients): upstream inverts reproduce the design to "
     f"{S['relay_check_p99_m']:.3f} m for 99 % of {len(err):,} pipes (largest {S['relay_check_max_m']:.3f} m).", "",
     f"Pipes: {S['km_total']:.1f} km ({S['km_dn200']:.1f} km DN200, {S['km_big']:.1f} km above DN200).",
     f"Under 0.75 m/s at the 2031 peak: DN200 {S['km_dn200_under075']:.1f} km; above DN200 {S['km_big_under075']:.1f} km "
     f"({100 * S['km_big_under075'] / S['km_big']:.1f} % of its length).",
     f"Steepened (one gradient per street run, within {T * 100:.2f} %): {S['n_steepened']:,} pipes, {S['km_steepened']:.1f} km, "
     f"{S['n_runs_steepened']:,} street runs; " + ", ".join(f"{b} {v:.1f} km" for b, v in S["km_by_band"].items()) + ".",
     f"Highest velocity at the 2056 design flow {S['v2056_max']:.2f} m/s; pipes over 3.0 m/s (G203 p27): {S['n_over3']}.", "",
     "| | design | steepened, no cut | this condition |", "|---|---|---|---|",
     f"| manholes deeper than 12 m | {S['mh_over12_design']:,} | {S['mh_over12_steepened_no_cut']:,} | {S['mh_over12']:,} |",
     f"| deepest manhole | {S['mh_deepest_design']:.2f} m | {S['mh_deepest_steepened_no_cut']:.2f} m | {S['mh_deepest']:.2f} m |",
     f"| pumping stations (the plant inlet not counted) | {S['stations_design']} | {S['stations_design']} | {S['stations']} "
     f"({S['stations_new']} new, {S['joined']} existing joined by gravity) |", "",
     "Outfalls deeper than 12 m, kept where they are (an outfall is never moved): "
     + (", ".join(f"{o['name']} {o['depth_m']:.2f} m" for o in S["outfalls_over12"]) or "none") + ".", ""]
if FIX:
    L += ["Engineer's station decisions (2026-11-18), no cut searched in these subnetworks: "
          + "; ".join(f"{s}: " + (", ".join(v) if v else "no new station, outfall kept deep") for s, v in FIX.items()) + ".", ""]
L += ["New stations:"]
for r in (cuts.itertuples() if len(cuts) else []):
    L.append(f"- {r.subnetwork}: at {r.station} ({r.depth_station_final:.1f} m deep), {r.flow_2056_ls:.1f} L/s in 2056, "
             f"to {r.receiver} over {r.rising_main_m:.0f} m (pipe {r.pipe}, {r.size}); "
             + ("engineer's decision" if r.round == 0 else f"round {r.round}"))
if not DESIGN:
    L += ["", "Existing stations, gravity join tested (outfall at 12 m or less and the receiving manhole within Table 12 spacing):"]
    for j in joins_log:
        L.append(f"- {j['source']} -> {j['receiver']} ({j['length_m']:.0f} m, outfall {j['outfall_depth_m']:.1f} m): {j['result']} - {j['why']}")
open(os.path.join(out, "SUMMARY.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))

# GeoPackage for QGIS
GP = os.path.join(out, f"split_{tag}.gpkg")
if os.path.exists(GP): os.remove(GP)
gpd.GeoDataFrame(P.drop(columns=["_k"]), geometry=[geom(k) for k in P._k], crs="EPSG:32640").to_file(GP, layer="pipes", driver="GPKG")
gpd.GeoDataFrame(O, geometry=[Point(a, b) for a, b in zip(O.x, O.y)], crs="EPSG:32640").to_file(GP, layer="outfalls", driver="GPKG")
if cut_links:
    rmn = pd.DataFrame(dict(pipe=[links[k]["label"] for k in cut_links], station=[lab.get(links[k]["up"]) for k in cut_links],
                            to=[lab.get(links[k]["dn"]) for k in cut_links], length_m=[round(links[k]["L"], 1) for k in cut_links]))
    gpd.GeoDataFrame(rmn, geometry=[geom(k) for k in cut_links], crs="EPSG:32640").to_file(GP, layer="rising_mains_new", driver="GPKG")
dbs = []
for k in pipes:
    l = links[k]; u, d = steep_li[k]; dm = max(ground.get(l["up"], np.nan) - u, ground.get(l["dn"], np.nan) - d)
    if dm > DMAX: dbs.append(dict(label=l["label"], sub=l["sub"], depth_max_m=round(dm, 2), _k=k))
if dbs:
    D_ = pd.DataFrame(dbs)
    gpd.GeoDataFrame(D_.drop(columns=["_k"]), geometry=[geom(k) for k in D_._k], crs="EPSG:32640").to_file(GP, layer="deep_before_split", driver="GPKG")
md = [dict(label=lab[n], depth_m=round(v, 2), x=xy[n][0], y=xy[n][1]) for n, v in mh_dep.items() if v > DMAX]
if md:
    M_ = pd.DataFrame(md)
    gpd.GeoDataFrame(M_, geometry=[Point(a, b) for a, b in zip(M_.x, M_.y)], crs="EPSG:32640").to_file(GP, layer="manholes_deep", driver="GPKG")
# every manhole, its depth as designed and after this condition (the engineer's working layer, 2026-11-18)
MA = pd.DataFrame([dict(label=lab[n], ground=round(ground.get(n, np.nan), 3), depth_design=round(base_depth.get(n, np.nan), 3),
                        depth_after=round(v, 3)) for n, v in mh_dep.items()])
gpd.GeoDataFrame(MA, geometry=[Point(*xy[n]) for n in mh_dep], crs="EPSG:32640").to_file(GP, layer="manholes", driver="GPKG")
print("written", GP)

# quick-look map
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
segs, cols = [], []
for k in active:
    a, b = xy.get(links[k]["up"]), xy.get(links[k]["dn"])
    if a is None or b is None or np.isnan(a[0]) or np.isnan(b[0]): continue
    segs.append([a, b]); d = max(dep.get(links[k]["up"], 0), dep.get(links[k]["dn"], 0))
    cols.append("#d62728" if d > DMAX else "#ff7f0e" if d > 8 else "#9e9e9e")
fig, ax = plt.subplots(figsize=(16.5, 11.7), dpi=150)
ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.5))
for kind, mk, c in (("Existing station", "s", "#7b2cbf"), ("New station", "^", "#1f3fff"),
                    ("Joined by gravity", "o", "#2ca02c"), ("Plant inlet", "*", "#1F3B63")):
    o = O[O.kind == kind]
    if len(o): ax.scatter(o.x, o.y, marker=mk, s=60, c=c, edgecolors="k", linewidths=0.4, zorder=6, label=f"{kind} ({len(o)})")
ax.plot([], [], c="#d62728", label="pipe end deeper than 12 m"); ax.plot([], [], c="#ff7f0e", label="8 to 12 m")
ax.plot([], [], c="#9e9e9e", label="up to 8 m")
ax.set_aspect("equal"); ax.autoscale(); ax.legend(loc="lower left", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
ax.set_title(f"{tag}: {S['condition']}", fontsize=11)
fig.savefig(os.path.join(out, f"map_{tag}.png"), bbox_inches="tight"); plt.close(fig)
