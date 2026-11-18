"""W18 (engineer, 2026-11-18): fewer pumping stations, by the logic the engineer applied himself at 0.50 % - O12 kept deep
(outfall 14.6 m) instead of two stations; O9-M103 and O9-M89 as one station at O9-M101 (12.6 m, "at the verge");
O9-M728 removed and O9-M773 kept (O9 outfall 14.3 m) - for any gradient limit.

On the split as searched (py/split_deep_subnetworks.py --no-fixed), per subnetwork with new stations, repeatedly take
the change that removes one station: drop one, or replace two by one station at any manhole both flows pass (from the
upper one, or from where their lines meet, down to the outfall); a change is allowed while every new station of the
subnetwork is at most CAP_STATION deep and its outfall at most CAP_OUTFALL deep - the deepest the engineer accepted.
Among the allowed changes: the shallowest outfall, then the shallowest deepest station. Stop when none is allowed.
Usage: python reduce_stations.py <gradient limit, e.g. 0.0075> [<tag> <export dir> <out dir>]
Writes <out dir>/REDUCE.md (default results/sc1_conditions/reduce_<limit>pc/, SC1-2056 from R5) and fewer.json.
Caps since the final design brief (engineer, 2026-11-18): "we are trying to stick to 12 m depth, but at times a bit deeper
can help reducing a pump or lift ... i accepted up to 14.65 (~15 m) either for stations you add, or outfalls ... some
manholes go as deep as 16.5 m". (The 0.50/0.75/1.00 % SC1 reports of the same day used 12.65 m for an added station.)"""
import os, sys, tempfile, itertools, io, contextlib, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
LIM = sys.argv[1]
TAG = sys.argv[2] if len(sys.argv) > 2 else "SC1-2056"
SRC = sys.argv[3] if len(sys.argv) > 3 else os.path.join(W18, "results", "SC1-2056_R5")
CAP_STATION, CAP_OUTFALL = 14.65, 14.65                 # a pump, a lift or an added station: up to about 15 m
CAP_DEEPEST = 16.50                                     # and no manhole deeper than 16.5 m; without it, dropping O9-M72
                                                        # (0.75 %) or O9-M69 (1 %) left a 21 m manhole
MIN_REACH = 400.0                                       # m of sewer a station's flow must still travel to its outfall
DECIDED = {"O12": []}                                   # engineer 2026-11-18: O12 kept deep, no station (14.6 m at 0.50 %)
OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(W18, "results", "sc1_conditions", f"reduce_{float(LIM) * 100:.2f}pc")
os.makedirs(OUT, exist_ok=True)
sys.argv = ["split_deep_subnetworks.py", TAG, SRC, os.path.join(tempfile.gettempdir(), f"w18_reduce_{TAG}_{LIM}"), LIM, "--no-fixed"]
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import split_deep_subnetworks as T
base = set(T.best["active"]); term = T.sub_terminal; lab = T.lab
cuts = [(T.links[c["link"]]["sub"], T.links[c["link"]]["up"], c["link"]) for c in T.best["cuts"]]
L = [f"# {TAG} at {float(LIM) * 100:.2f} %: fewer stations by the engineer's logic", "",
     f"Split as searched: {T.S['stations']} stations ({T.S['stations_new']} new, {T.S['joined']} joined by gravity), "
     f"{T.S['mh_over12']} manholes deeper than 12 m. Caps: new station <= {CAP_STATION} m, outfall <= {CAP_OUTFALL} m, "
     f"no manhole deeper than {CAP_DEEPEST} m.", ""]
FIX = {}
for sub in sorted({s for s, _, _ in cuts}, key=lambda s: int(s[1:])):
    full = base | {k for s, _, k in cuts if s == sub}
    nxt = T.downstream_map(full); into = {}
    for k in full: into.setdefault(T.links[k]["dn"], []).append(k)
    tree, stack = set(), [term[sub]]                           # every link draining to this outfall
    while stack:
        n = stack.pop()
        for k in into.get(n, []):
            if k not in tree: tree.add(k); stack.append(T.links[k]["up"])

    def path(n):
        p = [n]
        while p[-1] in nxt and nxt[p[-1]] in tree: p.append(T.links[nxt[p[-1]]]["dn"])
        return p

    def reach(n):                                              # gravity sewer from n down to the outfall, m
        return sum(T.links[nxt[x]]["L"] for x in path(n)[:-1])

    def evaluate(C):
        inv, li = T.relay(tree - {nxt[n] for n in C}); dep = T.depths(inv)
        mh = [n for n in dep if n in T.mh.index]
        # a station whose only inflow is pumped (no gravity pipe left into it) starts at minimum cover, as the re-lay does
        st = {n: dep.get(n, T.ground[n] - T.cover_limit(nxt[n])) for n in C}
        if term[sub] not in dep: return dict(n=len(C), outfall=np.inf, st=st, deepest=np.nan, over12=0)
        return dict(n=len(C), outfall=dep[term[sub]], st=st, deepest=max(dep[n] for n in mh),
                    over12=sum(dep[n] > T.DMAX for n in mh))

    ok = lambda e: (e["outfall"] <= CAP_OUTFALL and e["deepest"] <= CAP_DEEPEST
                    and all(v <= CAP_STATION for v in e["st"].values()))
    show = lambda e: (f"{e['n']} new | " + (", ".join(f"{lab[n]} {v:.2f}" for n, v in sorted(e["st"].items(), key=lambda x: lab[x[0]])) or "-")
                      + f" | {e['outfall']:.2f} m | {e['deepest']:.2f} m | {e['over12']} |")
    C = frozenset(n for s, n, _ in cuts if s == sub); e = evaluate(C)
    L += [f"## {sub}", "", "| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |", "|---|---|---|---|---|---|",
          f"| as searched | {show(e)}"]
    if sub in DECIDED:                                         # the engineer's own decision for this subnetwork
        C = frozenset(n for n in T.lab if T.lab[n] in DECIDED[sub]); L.append(f"| engineer's decision | {show(evaluate(C))}")
    while C and sub not in DECIDED:
        cands = [(f"drop {lab[s]}", C - {s}) for s in C]
        for a, b in itertools.combinations(sorted(C), 2):
            pa, pb = path(a), path(b); conf = next(x for x in pa if x in pb)
            line = path(a if conf == b else b) if conf in (a, b) else path(conf)
            # an outfall is never moved (2026-11-18): no station whose flow lands on less than MIN_REACH of sewer above
            # the outfall (his O11 case: a station 365 m above it, one branch between, was the outfall moved)
            cands += [(f"{lab[a]} + {lab[b]} as one at {lab[x]}", (C - {a, b}) | {x}) for x in line[:-1]
                      if x not in C - {a, b} and reach(T.links[nxt[x]]["dn"]) >= MIN_REACH]
        best = None
        for desc, C2 in cands:
            e2 = evaluate(C2)
            if ok(e2):
                key = (e2["n"], round(e2["outfall"], 3), round(max(e2["st"].values(), default=0), 3))
                if best is None or key < best[0]: best = (key, desc, C2, e2)
        if best is None: break
        C = best[2]; L.append(f"| {best[1]} | {show(best[3])}")
    if C:                                                      # for information: every new station of the subnetwork removed
        L.append(f"| (all new stations removed, not allowed) | {show(evaluate(frozenset()))}")
    L.append("")
    orig = frozenset(n for s, n, _ in cuts if s == sub)
    if C != orig: FIX[sub] = sorted(lab[n] for n in C)
L += ["Stations for split_deep_subnetworks.FIXED: " + json.dumps(FIX), ""]
open(os.path.join(OUT, "REDUCE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump({TAG: FIX}, open(os.path.join(OUT, "fewer.json"), "w", encoding="utf-8"), indent=1)
print("\n".join(L))
