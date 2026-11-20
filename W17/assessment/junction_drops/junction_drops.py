"""Junction drops grouped by the deep stretch of sewer they join, and whether the ground falls along each stretch.

AN EXPERIMENT (engineer, 2026-10-03). Nothing here is used by the design, the model or the report.

    python junction_drops.py [S1]

Source: the option's 2070 design in the SewerGEMS model R9, as exported by the bridge
(D:\\VBOX\\bridge\\out\\scen\\<S>\\conduits_<S>-2070.csv and manholes_<S>-2070.csv). Writes into ./<S>/.

Guideline values:
  G203 p30  a backdrop where the inverts differ by more than 600 mm; "The maximum backdrop height should be
            of 2 m. Beyond this limit, specific devices like vortex drop shafts should be used."
  G203 p29  Table 11, 200 mm minimum gradient 5.00 mm/m
  G203 p33  minimum cover 1.3 m to the crown

How it reads the network:
  - flow runs to the lower invert end of every pipe (all 24 subnetworks are trees);
  - at a manhole the incoming pipe with the largest 2070 flow is the THROUGH pipe, every other incoming pipe is a
    BRANCH; a RUN is a chain of through pipes, so a branch starts a run of its own;
  - a drop is the arriving invert of an incoming pipe minus the leaving invert of the outgoing pipe.

ASSUMPTIONS of this experiment (not guideline values):
  - DEEP = 3.5 m: a run is deep at a manhole where its leaving invert is 3.5 m or more below the ground (a 200 mm
    branch at 1.3 m cover arrives about 1.5 m down, so only there can it drop more than 2 m); a manhole with a branch
    drop over 2 m is deep whatever its depth. Contiguous deep manholes on one run make one STRETCH.
  - RISE_TOL = 0.5 m: a stretch "rises" when the ground climbs 0.5 m or more anywhere along it in the direction of
    flow, or does not fall at all from end to end.
  - The shallow parallel sewer tried along each stretch is 200 mm, starts with its invert 1.5 m below the ground,
    falls at 5.00 mm/m, and steepens only where needed to keep that 1.5 m (so it follows ground that falls faster).
  - Stepping a branch down (idea 3): backdrops of at most 2 m at the junction and the branch's own manholes upstream;
    the branch's last reach goes (drop - 2 m) deeper.
"""
import csv, collections, json, math, os, sys
import geopandas as gpd
from shapely.geometry import LineString, Point

S = sys.argv[1] if len(sys.argv) > 1 else "S1"
SRC = rf"D:\VBOX\bridge\out\scen\{S}"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), S)
os.makedirs(OUT, exist_ok=True)
SUB = lambda lab: lab.split("-")[0] if lab.startswith("O") and ("-M" in lab or "-P" in lab) else None

BACKDROP, MAX_BACKDROP = 0.6, 2.0          # G203 p30
SMIN = 0.005                                # G203 p29 Table 11, 200 mm
MAX_DEPTH = 12.0                            # standing project rule (hard limit at concept)
DEEP, RISE_TOL, COLLECTOR_DEPTH = 3.5, 0.5, 1.5   # this experiment's assumptions

rd = lambda kind: list(csv.DictReader(open(rf"{SRC}\{kind}_{S}-2070.csv", encoding="utf-8")))
mh = {r["id"]: r for r in rd("manholes")}
num = lambda v: float(v) if v not in ("", "NaN", None) else 0.0

# ------------------------------------------------------------------ the tree
P = {}
for r in rd("conduits"):
    if r["active"] != "True" or not SUB(r["label"]):
        continue
    si, ti = float(r["start_inv"]), float(r["stop_inv"])
    up, dn, ui, di = (r["start"], r["stop"], si, ti) if si >= ti else (r["stop"], r["start"], ti, si)
    P[r["label"]] = dict(label=r["label"], sub=SUB(r["label"]), up=up, dn=dn, ui=ui, di=di,
                         L=float(r["length_m"]), id_mm=float(r["diameter_mm"]), q=num(r["flow_m3d"]))
out_of, into = {}, collections.defaultdict(list)
for p in P.values():
    if p["up"] in out_of:
        sys.exit(f"two pipes leave node {p['up']}: {out_of[p['up']]}, {p['label']}")
    out_of[p["up"]] = p["label"]
    into[p["dn"]].append(p["label"])
main_in = {n: max(ls, key=lambda l: (P[l]["q"], -P[l]["di"])) for n, ls in into.items()}

def chain(last):
    """The run that ends with pipe `last`, upstream to downstream."""
    c = [last]
    while P[c[-1]]["up"] in main_in:
        c.append(main_in[P[c[-1]]["up"]])
    return c[::-1]

run_of = {}
for last in [l for l, p in P.items() if p["dn"] not in out_of or main_in.get(p["dn"]) != l]:
    for l in chain(last):
        run_of[l] = last
runs = collections.defaultdict(list)
for last in set(run_of.values()):
    runs[last] = chain(last)

ground = lambda n: float(mh[n]["ground"]) if n in mh else None
lab = lambda n: mh[n]["label"] if n in mh else f"node {n}"

# ------------------------------------------------------------------ the drops
drops = []
for n, ins in into.items():
    if n not in out_of or n not in mh:
        continue
    o = P[out_of[n]]
    for l in ins:
        H = P[l]["di"] - o["ui"]
        if H <= BACKDROP:
            continue
        b = P[l]
        kind = "through" if l == main_in[n] else "branch"
        d = dict(manhole=lab(n), node=n, kind=kind, drop_m=round(H, 3), incoming=l, incoming_id_mm=round(b["id_mm"]),
                 manhole_depth_m=round(float(mh[n]["rim"]) - float(mh[n]["invert"]), 2),
                 receiving_depth_m=round(ground(n) - o["ui"], 2), receiving_run=run_of[o["label"]], sub=o["sub"])
        if kind == "branch":                                    # idea 3: step the branch down in backdrops of <= 2 m
            bd_up = ground(b["up"]) - b["ui"] if b["up"] in mh else None
            d.update(steps_le_2m=math.ceil(H / MAX_BACKDROP), branch_pipes=len(runs[run_of[l]]),
                     branch_last_reach_deeper_m=round(max(H - MAX_BACKDROP, 0), 2),
                     branch_new_depth_upstream_m=round(bd_up + max(H - MAX_BACKDROP, 0), 2) if bd_up is not None else None)
        drops.append(d)
branch_big = collections.defaultdict(list)              # node -> branch drops over 2 m
branch_small = collections.Counter()                    # node -> branch drops of 0.6 to 2 m
for d in drops:
    if d["kind"] == "branch" and d["drop_m"] > MAX_BACKDROP:
        branch_big[d["node"]].append(d)
    elif d["kind"] == "branch":
        branch_small[d["node"]] += 1

# ------------------------------------------------------------------ deep stretches along each run
stretches, sid_of_node = [], {}
for last, c in runs.items():
    flags = [(ground(P[l]["up"]) - P[l]["ui"] >= DEEP) or (P[l]["up"] in branch_big) if P[l]["up"] in mh else False
             for l in c]
    i = 0
    while i < len(c):
        if not flags[i]:
            i += 1; continue
        j = i
        while j + 1 < len(c) and flags[j + 1]:
            j += 1
        seg = c[i:j + 1]
        nodes = [P[l]["up"] for l in seg] + [P[seg[-1]]["dn"]]
        g = [ground(n) for n in nodes]
        if g[-1] is None:                                    # ends at an outfall: no ground on record there
            nodes, g = nodes[:-1], g[:-1]
        L = sum(P[l]["L"] for l in seg[:len(nodes) - 1]) if len(nodes) > 1 else P[seg[0]]["L"]
        fall = g[0] - g[-1] if len(g) > 1 else ground(P[seg[0]]["up"]) - (ground(P[seg[0]]["dn"]) or ground(P[seg[0]]["up"]))
        rise, low = 0.0, g[0]
        for x in g:
            low = min(low, x); rise = max(rise, x - low)
        ok_len = sum(P[l]["L"] for l in seg if P[l]["dn"] in mh and ground(P[l]["up"]) - ground(P[l]["dn"]) >= SMIN * P[l]["L"])
        # the shallow parallel sewer along the stretch
        inv = {nodes[0]: g[0] - COLLECTOR_DEPTH}
        for l in seg:
            if P[l]["up"] in inv and P[l]["dn"] in mh:
                inv[P[l]["dn"]] = min(inv[P[l]["up"]] - SMIN * P[l]["L"], ground(P[l]["dn"]) - COLLECTOR_DEPTH)
        cdepth = max(ground(n) - v for n, v in inv.items())
        end = max(inv, key=lambda n: nodes.index(n) if n in nodes else -1)
        deep_at_end = P[out_of[end]]["ui"] if end in out_of else P[seg[-1]]["di"]
        final_drop = inv[end] - deep_at_end
        big = [d for n in nodes for d in branch_big.get(n, [])]
        onto = [d for d in big if d["node"] in inv]
        still_big = [d for d in onto if P[d["incoming"]]["di"] - inv[d["node"]] > MAX_BACKDROP]
        below = [d for d in onto if P[d["incoming"]]["di"] - inv[d["node"]] < 0]
        if len(g) == 1:
            cls = "one manhole at an outfall"
        elif rise >= RISE_TOL or fall <= 0:
            cls = "rises: reroute"
        elif L > 0 and fall / L >= SMIN:
            cls = "falls >= 0.5 %"
        else:
            cls = "falls < 0.5 %"
        sid = len(stretches) + 1
        for n in nodes:
            sid_of_node.setdefault(n, sid)
        dep = [ground(P[l]["up"]) - P[l]["ui"] for l in seg if P[l]["up"] in mh]
        stretches.append(dict(
            stretch=sid, sub=P[seg[0]]["sub"], run=last, from_mh=lab(nodes[0]), to_mh=lab(nodes[-1]), pipes=len(seg),
            length_m=round(L, 1), sewer_id_mm=f"{min(P[l]['id_mm'] for l in seg):.0f}-{max(P[l]['id_mm'] for l in seg):.0f}",
            depth_start_m=round(dep[0], 2), depth_max_m=round(max(dep), 2), depth_end_m=round(dep[-1], 2),
            branch_drops_over_2m=len(big), max_branch_drop_m=round(max([d["drop_m"] for d in big], default=0), 2),
            branch_drops_06_2m=sum(branch_small[n] for n in nodes),
            ground_start=round(g[0], 2), ground_end=round(g[-1], 2), ground_fall_m=round(fall, 2),
            ground_slope_pc=round(100 * fall / L, 3) if L > 0 else None, max_rise_m=round(rise, 2),
            share_falling_ge_05pc=round(ok_len / L, 2) if L > 0 else None, ground_class=cls,
            parallel_max_depth_m=round(cdepth, 2), parallel_final_drop_m=round(final_drop, 2),
            parallel_drops_still_over_2m=len(still_big), parallel_branch_below_it=len(below)))
        i = j + 1
for d in drops:
    d["stretch"] = sid_of_node.get(d["node"])

# ------------------------------------------------------------------ write
def write(name, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list({k: 0 for r in rows for k in r})); w.writeheader(); w.writerows(rows)

write("drops.csv", drops)
active = [s for s in stretches if s["branch_drops_over_2m"]]
write("stretches.csv", sorted(active, key=lambda s: -s["branch_drops_over_2m"]))

xy = lambda n: (float(mh[n]["x"]), float(mh[n]["y"]))
lines = []
for s in active:
    seg = runs[s["run"]]
    nodes = [P[l]["up"] for l in seg] + [P[seg[-1]]["dn"]]
    a, b = nodes.index(next(n for n in nodes if lab(n) == s["from_mh"])), nodes.index(next(n for n in nodes if lab(n) == s["to_mh"]))
    pts = [xy(n) for n in nodes[a:b + 1] if n in mh]
    lines.append(LineString(pts if len(pts) > 1 else pts * 2))
gpkg = os.path.join(OUT, f"junction_drops_{S}.gpkg")
gpd.GeoDataFrame(active, geometry=lines, crs="EPSG:32640").to_file(gpkg, layer="deep_stretches", driver="GPKG")
gpd.GeoDataFrame(drops, geometry=[Point(xy(d["node"])) for d in drops], crs="EPSG:32640").to_file(gpkg, layer="drops", driver="GPKG")

# ------------------------------------------------------------------ summary
br = [d for d in drops if d["kind"] == "branch"]; big = [d for d in br if d["drop_m"] > MAX_BACKDROP]
by_cls = collections.defaultdict(lambda: [0, 0, 0.0])
for s in active:
    by_cls[s["ground_class"]][0] += 1; by_cls[s["ground_class"]][1] += s["branch_drops_over_2m"]; by_cls[s["ground_class"]][2] += s["length_m"]
fixed = sum(s["branch_drops_over_2m"] - s["parallel_drops_still_over_2m"] - s["parallel_branch_below_it"] for s in active
            if s["ground_class"] != "rises: reroute")
size = collections.Counter(s["branch_drops_over_2m"] for s in active)
summary = dict(
    option=S, drops_over_06=len(drops), branch_drops_over_06=len(br), through_drops_over_06=len(drops) - len(br),
    branch_drops_over_2m=len(big), stretches_with_branch_drops_over_2m=len(active),
    stretches_by_number_of_drops={k: size[k] for k in sorted(size)},
    by_ground_class={k: dict(stretches=v[0], drops_over_2m=v[1], length_km=round(v[2] / 1000, 2)) for k, v in by_cls.items()},
    parallel_sewer_on_falling_stretches=dict(
        drops_over_2m_removed=fixed,
        final_drops_over_2m=sum(1 for s in active if s["ground_class"] != "rises: reroute" and s["parallel_final_drop_m"] > MAX_BACKDROP),
        parallel_deeper_than_3m=sum(1 for s in active if s["ground_class"] != "rises: reroute" and s["parallel_max_depth_m"] > 3)),
    step_down=dict(steps_by_drop={k: v for k, v in sorted(collections.Counter(d["steps_le_2m"] for d in big).items())},
                   branch_too_short=sum(1 for d in big if d["branch_pipes"] < d["steps_le_2m"] - 1),
                   new_depth_over_12m=sum(1 for d in big if d["branch_new_depth_upstream_m"] is not None and d["branch_new_depth_upstream_m"] > MAX_DEPTH)))
json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(summary, indent=1))
