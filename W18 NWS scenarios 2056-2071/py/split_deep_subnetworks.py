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

Usage: python split_deep_subnetworks.py <tag, e.g. SC1-2056> <export dir> <out dir> [threshold gradient, default 0.01]
Writes <out>/cuts_<tag>.csv, joins_<tag>.csv, nodes_<tag>.csv, SUMMARY.md, map_<tag>.png and split_<tag>.gpkg."""
import sys, os, math, re
import numpy as np, pandas as pd

G, NU, KS, V_SC = 9.81, 1.141e-6, 1.5e-3, 0.75
COVER, DMAX = 1.3, 12.0
tag, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
T = float(sys.argv[4]) if len(sys.argv) > 4 else 0.01
os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)


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


def slope_for(Q, D):
    if Q <= 0 or velocity(Q, D, 1.0) < V_SC: return np.nan
    lo, hi = 1e-6, 1.0
    for _ in range(45):
        s = math.sqrt(lo * hi)
        if velocity(Q, D, s) < V_SC: lo = s
        else: hi = s
    return hi


def spacing(nominal_mm):                              # PAM-GUD-203 Table 12 (p30), maximum manhole spacing
    return 100.0 if nominal_mm <= 315 else 120.0 if nominal_mm <= 900 else 150.0 if nominal_mm <= 1400 else 200.0


# ------------------------------------------------------------------ the designed network
dy = pd.read_csv(os.path.join(src, f"conduits_{tag}a.csv")); dy = dy[dy.active == True].copy()
d31 = pd.read_csv(os.path.join(src, f"conduits_{tag}-at-2031.csv")).set_index("label")
mh = pd.read_csv(os.path.join(src, f"manholes_{tag}a.csv")).set_index("id")
tr = pd.read_csv(os.path.join(src, f"transfers_{tag}.csv"))
tr = tr[tr.year == int(tag.split("-")[1])]
rm = pd.read_csv(os.path.join(W18, "results", "rising_mains.csv"))
dy["UP"] = np.where(dy.start_inv >= dy.stop_inv, dy.start, dy.stop); dy["DN"] = np.where(dy.start_inv >= dy.stop_inv, dy.stop, dy.start)
dy["UPI"] = dy[["start_inv", "stop_inv"]].max(axis=1); dy["DNI"] = dy[["start_inv", "stop_inv"]].min(axis=1)
dy["S_LAID"] = (dy.UPI - dy.DNI) / dy.length_m; dy["D"] = dy.diameter_mm / 1000.0
dy["NOM"] = dy.size_label.str.extract(r"(\d+)")[0].astype(float)
dy["Q31"] = d31.flow_m3d.reindex(dy.label).values / 86400.0
dy["SUB"] = dy.label.str.split("-").str[0]
big = (dy.NOM > 200).values
dy["S_REQ"] = [slope_for(q, d) if b else np.nan for q, d, b in zip(dy.Q31, dy.D, big)]
steep = big & (dy.S_REQ > dy.S_LAID).values & (dy.S_REQ <= T).values
dy["S_NEW"] = np.where(steep, dy.S_REQ, dy.S_LAID)
ground = mh.ground.where(mh.ground > 100).to_dict()
lab = mh.label.to_dict(); xy = {i: (r.x, r.y) for i, r in mh.iterrows()}
terminals = sorted(set(dy.DN) - set(dy.UP))
above = dy.groupby("DN").UP.first()
for t in terminals:                                  # an outfall takes the ground and position of the manhole above it
    u = above[t]; ground[t] = ground.get(u, np.nan); xy[t] = xy.get(u, (np.nan, np.nan))
    lab[t] = dy.loc[dy.DN == t, "SUB"].iloc[0]
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
    into = {}
    for k in active: into.setdefault(links[k]["dn"], []).append(k)
    n = terminal
    while True:
        cands = into.get(n, [])
        if not cands: return None
        k = min(cands, key=lambda c: li[c][1])                 # the arriving link with the lowest invert sets the depth
        u = links[k]["up"]
        if u not in R: return k                                # u is at 12 m or less: the station goes here
        n = u


def solve(active, pumps_in):
    """Cut until no node is deeper than 12 m for good. Returns the active links, the cuts and the final inverts."""
    active = set(active); cuts = []
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
                          S=last.S_NEW, flow_m3d=r.flow_m3d))
active0, cuts0, inv0, li0 = solve(pipes, len(transfers))
best = dict(active=active0, cuts=cuts0, inv=inv0, li=li0, joins=[])
joins_log = []
changed = True
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
cuts = pd.DataFrame(best["cuts"])
if len(cuts):
    cuts["subnetwork"] = [links[k]["sub"] for k in cuts.link]
    # a cut on the last pipe into a pumped outfall moves that station one manhole up; anywhere else it is a new station
    cuts["kind"] = ["existing station moved up" if links[k]["dn"] in orig_terminals - plants else "new station" for k in cuts.link]
    cuts["station"] = [lab.get(n) for n in cuts.station]; cuts["receiver"] = [lab.get(n) for n in cuts.receiver]
    cuts["rising_main_m"] = [links[k]["L"] for k in cuts.link]
    cuts["pipe"] = [links[k]["label"] for k in cuts.link]; cuts["size"] = [f"DN{links[k]['nom']:.0f}" for k in cuts.link]
    q56 = dy.set_index(dy.index).flow_m3d
    cuts["flow_2056_ls"] = [q56.get(k, np.nan) / 86.4 for k in cuts.link]
    cuts["x"] = [xy[links[k]["up"]][0] for k in cuts.link]; cuts["y"] = [xy[links[k]["up"]][1] for k in cuts.link]
    cuts = cuts.drop(columns=["link"]).sort_values(["subnetwork", "round"])
cuts.to_csv(os.path.join(out, f"cuts_{tag}.csv"), index=False, float_format="%.2f")
pd.DataFrame(joins_log).to_csv(os.path.join(out, f"joins_{tag}.csv"), index=False, float_format="%.1f")
steep_inv, _ = relay(pipes)                           # steepened, no cut: the deep case the cuts answer
dsteep = depths(steep_inv)
nodes = pd.DataFrame({"label": pd.Series(lab), "ground": pd.Series(ground), "depth_design": pd.Series(base_depth),
                      "depth_steepened": pd.Series(dsteep), "depth_after": pd.Series(dep)})
nodes.to_csv(os.path.join(out, f"nodes_{tag}.csv"), index_label="id", float_format="%.3f")

stations = n_stations(active); n_new = int((cuts.kind == "new station").sum()) if len(cuts) else 0
n_moved = len(cuts) - n_new
n12 = lambda d: sum(1 for n, v in d.items() if v > DMAX and n in mh.index)
Rs, _, _ = regions(pipes, steep_inv)
L = [f"# Splitting the deep subnetworks - {tag}, gradients up to {T*100:.2f} %", "",
     f"Re-lay check (cover {COVER} m over the soffit, laid gradients): upstream inverts reproduce the design to {np.percentile(err, 99):.3f} m for 99 % of {len(err):,} pipes (largest {err.max():.3f} m).", "",
     f"Pipes above DN200 steepened to reach {V_SC} m/s at the 2031 peak: {int(steep.sum()):,} ({dy.length_m[steep].sum()/1000:.1f} km); "
     f"above DN200 that cannot reach it within {T*100:.2f} %: {int((big & ~steep & (dy.S_REQ > dy.S_LAID).values).sum()):,}.", "",
     "| | design | steepened, no cut | steepened, cut and joined |", "|---|---|---|---|",
     f"| manholes deeper than 12 m | {n12(base_depth):,} | {n12(dsteep):,} | {n12(dep):,} |",
     f"| of which deeper than 12 m for good (to the outfall) | {len([n for n in regions(pipes, base_inv)[0] if n in mh.index]):,} | {len([n for n in Rs if n in mh.index]):,} | {len([n for n in R_end if n in mh.index]):,} |",
     f"| deepest manhole | {max(v for n, v in base_depth.items() if n in mh.index):.2f} m | {max(v for n, v in dsteep.items() if n in mh.index):.2f} m | {max(v for n, v in dep.items() if n in mh.index):.2f} m |",
     f"| pumping stations (the plant inlet not counted) | {n_stations(pipes)} | {n_stations(pipes)} | {stations} ({n_new} new, {n_moved} moved one manhole up, {len(best['joins'])} joined by gravity) |", "",
     f"Deepest manhole left: a dip that comes back to 12 m or less before its outfall (allowed). Manholes deeper than 12 m after: {n12(dep):,}.", "",
     "Cuts:"]
for r in (cuts.itertuples() if len(cuts) else []):
    L.append(f"- {r.subnetwork}: {r.kind} at {r.station} ({r.depth_station:.1f} m deep), {r.flow_2056_ls:.1f} L/s in 2056, to {r.receiver} over {r.rising_main_m:.0f} m (pipe {r.pipe}, {r.size}); round {r.round}")
L += ["", "Existing stations, gravity join tested (outfall at 12 m or less and the receiving manhole within Table 12 spacing):"]
for j in joins_log: L.append(f"- {j['source']} -> {j['receiver']} ({j['length_m']:.0f} m, outfall {j['outfall_depth_m']:.1f} m): {j['result']} - {j['why']}")
open(os.path.join(out, "SUMMARY.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))

# map and GeoPackage
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
nc = cuts[cuts.kind == "new station"] if len(cuts) else cuts
mv = cuts[cuts.kind != "new station"] if len(cuts) else cuts
if len(nc): ax.scatter(nc.x, nc.y, marker="^", s=70, c="#1f3fff", edgecolors="k", linewidths=0.4, zorder=6, label=f"new station ({len(nc)})")
if len(mv): ax.scatter(mv.x, mv.y, marker="v", s=60, c="#00bcd4", edgecolors="k", linewidths=0.4, zorder=6, label=f"existing station moved one manhole up ({len(mv)})")
for j in best["joins"]:
    a = xy[j["terminal"]]; ax.scatter([a[0]], [a[1]], marker="o", s=50, c="#2ca02c", edgecolors="k", zorder=5)
ups_f = {links[k]["up"] for k in active}; fin = ({links[k]["dn"] for k in active} - ups_f) - plants
cut_st = {links[k]["up"] for k in [c["link"] for c in best["cuts"]]}
kept = [n for n in fin if n not in cut_st]
ax.scatter([xy[n][0] for n in kept], [xy[n][1] for n in kept], marker="s", s=40, c="#7b2cbf", edgecolors="k", zorder=5, label=f"existing station kept ({len(kept)})")
ax.scatter([], [], marker="o", c="#2ca02c", label=f"existing station joined by gravity ({len(best['joins'])})")
ax.plot([], [], c="#d62728", label="pipe end deeper than 12 m"); ax.plot([], [], c="#ff7f0e", label="8 to 12 m"); ax.plot([], [], c="#9e9e9e", label="up to 8 m")
ax.set_aspect("equal"); ax.autoscale(); ax.legend(loc="lower left", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
ax.set_title(f"{tag}: pipes above DN200 steepened to 0.75 m/s at 2031 (up to {T*100:.0f} %), subnetworks cut where they stay deeper than 12 m", fontsize=11)
fig.savefig(os.path.join(out, f"map_{tag}.png"), bbox_inches="tight"); plt.close(fig)
try:
    import geopandas as gpd
    from shapely.geometry import Point, LineString
    gl = gpd.GeoDataFrame({"link": [links[k]["label"] for k in active if not np.isnan(xy[links[k]['up']][0]) and not np.isnan(xy[links[k]['dn']][0])],
                           "depth_max": [max(dep.get(links[k]["up"], 0), dep.get(links[k]["dn"], 0)) for k in active if not np.isnan(xy[links[k]['up']][0]) and not np.isnan(xy[links[k]['dn']][0])]},
                          geometry=[LineString([xy[links[k]["up"]], xy[links[k]["dn"]]]) for k in active if not np.isnan(xy[links[k]['up']][0]) and not np.isnan(xy[links[k]['dn']][0])], crs="EPSG:32640")
    gl.to_file(os.path.join(out, f"split_{tag}.gpkg"), layer="pipes_after", driver="GPKG")
    if len(cuts):
        gpd.GeoDataFrame(cuts, geometry=[Point(a, b) for a, b in zip(cuts.x, cuts.y)], crs="EPSG:32640").to_file(os.path.join(out, f"split_{tag}.gpkg"), layer="new_stations", driver="GPKG")
except Exception as e:
    print("gpkg not written:", e)
