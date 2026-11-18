"""W18 (engineer, 2026-11-18, on the SC1-2056 map at 0.50 %): "if you do not add O12-M26 and O12-M193, how deep will O12
be? can they merge? what would the depth be? O9-M103 and O9-M89 are very close, one after another and both go deep."

Runs py/split_deep_subnetworks.py unchanged on SC1-2056 at 0.50 % (its own outputs go to a temporary folder), checks it
gives the C1 result (25 stations), then, on its final network (all other cuts and joins kept):
  - NONE: the pair's stations removed (their pipes restored): the depth of the subnetwork's outfall and its manholes;
  - ONE station: every manhole on the line from the upper station down to the outfall tried as the single station of
    the pair (its leaving pipe becomes the rising main, the next manhole restarts at minimum cover, as the tool cuts):
    the station's depth, the deepest manhole and whether anything is still deeper than 12 m for good (another cut).
Usage: python whatif_merge_stations.py      Writes results/sc1_conditions/whatif_C1_O12_O9/WHATIF.md and *.csv"""
import os, sys, tempfile, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
OUT = os.path.join(W18, "results", "sc1_conditions", "whatif_C1_O12_O9"); os.makedirs(OUT, exist_ok=True)
sys.argv = ["split_deep_subnetworks.py", "SC1-2056", os.path.join(W18, "results", "SC1-2056_R5"),
            os.path.join(tempfile.gettempdir(), "w18_whatif_split"), "0.005"]
sys.path.insert(0, HERE)
import split_deep_subnetworks as T                    # runs the split exactly as for C1

PAIRS = [("O12", ["O12-M26", "O12-M193"]), ("O9", ["O9-M103", "O9-M89"]), ("O9", ["O9-M773", "O9-M728"])]
assert T.S["stations"] == 25 and abs(T.S["km_big_under075"] - 26.4) < 0.05, (T.S["stations"], T.S["km_big_under075"])
base = set(T.best["active"]); cut_of = {T.lab[T.links[c["link"]]["up"]]: c["link"] for c in T.best["cuts"]}
term = T.sub_terminal
base0 = base


def merged(start, pair, site):
    """The network with a pair's two stations replaced by one station at site."""
    full = start | {cut_of[s] for s in pair}; nx = T.downstream_map(full)
    return full - {nx[next(n for n, l in T.lab.items() if l == site)]}


# every pair on the network as mapped; the second O9 pair again with the first O9 pair merged (both drain to O9)
CASES = [(s, p, base0, "") for s, p in PAIRS] + \
        [("O9", ["O9-M773", "O9-M728"], merged(base0, ["O9-M103", "O9-M89"], "O9-M101"), ", with O9-M103 and O9-M89 merged at O9-M101")]


def state(active, sub):
    inv, li = T.relay(active); R, dep, nxt = T.regions(active, inv)
    mine = [n for n in dep if n in T.mh.index and T.lab[n].split("-")[0] == sub]
    deep_for_good = [n for n in R if n in mine or n == term[sub]]
    km12 = sum(T.links[k]["L"] for k in active if T.links[k]["sub"] == sub and T.links[k]["kind"] == "pipe"
               and max(T.ground.get(T.links[k]["up"], np.nan) - li[k][0], T.ground.get(T.links[k]["dn"], np.nan) - li[k][1]) > T.DMAX) / 1000
    deepest = max(mine, key=lambda n: dep[n])
    return dict(outfall_m=dep.get(term[sub]), deepest=T.lab[deepest], deepest_m=dep[deepest],
                mh_over12=sum(1 for n in mine if dep[n] > T.DMAX), km_over12=km12, deep_for_good=len(deep_for_good),
                stations=T.n_stations(active)), dep


L = ["# SC1-2056 at 0.50 %: fewer stations in O12 and O9 (engineer, 2026-11-18)", "",
     f"Base: the C1 split as mapped, {T.S['stations']} stations, {T.S['km_big_under075']:.1f} km above DN200 under 0.75 m/s at 2031. "
     "Every case keeps all other cuts and joins; depths are the re-lay's (ground minus invert), the outfall's ground is the model's.", ""]
rows = []
for sub, pair, base, note in CASES:
    links = [cut_of[s] for s in pair]
    full = base | set(links)                                     # both stations removed
    nxt = T.downstream_map(full)
    # which is upstream: walk down from each station
    def path(n):
        p = [n]
        while p[-1] in nxt: p.append(T.links[nxt[p[-1]]]["dn"])
        return p
    ids = {s: T.links[cut_of[s]]["up"] for s in pair}
    pa, pb = path(ids[pair[0]]), path(ids[pair[1]])
    conf = next(x for x in pa if x in pb)                        # where the two lines meet (the lower station if in series)
    down = lambda p, x: sum(T.links[nxt[y]]["L"] for y in p[:p.index(x)])
    series = conf in (ids[pair[0]], ids[pair[1]])
    if series:
        up_s = pair[0] if conf == ids[pair[1]] else pair[1]
        line = path(ids[up_s]); where = f"in series: {down(line, conf):.0f} m of sewer from {up_s} down to the other station"
    else:
        up_s = None; line = path(conf)
        where = (f"on two branches that meet at {T.lab[conf]}: {pair[0]} {down(pa, conf):.0f} m and {pair[1]} {down(pb, conf):.0f} m "
                 f"of sewer above it; crow-fly between the stations {math.dist(T.xy[ids[pair[0]]], T.xy[ids[pair[1]]]):.0f} m")
    b, dep_b = state(base, sub)
    n, dep_n = state(full, sub)
    L += [f"## {sub}: {', '.join(pair)}{note} ({where})", "",
          "| case | stations in total | station depth | outfall depth | deepest manhole in the subnetwork | manholes > 12 m | pipe > 12 m | still deep for good |",
          "|---|---|---|---|---|---|---|---|",
          f"| {'as mapped' if not note else 'start' + note} (two stations) | {b['stations']} | " + " / ".join(f"{s} {dep_b[ids[s]]:.2f} m" for s in pair) +
          f" | {b['outfall_m']:.2f} m | {b['deepest']} {b['deepest_m']:.2f} m | {b['mh_over12']} | {b['km_over12']:.2f} km | {b['deep_for_good']} |",
          f"| none of the two | {n['stations']} | - | **{n['outfall_m']:.2f} m** | {n['deepest']} {n['deepest_m']:.2f} m | {n['mh_over12']} | {n['km_over12']:.2f} km | {n['deep_for_good']} |"]
    def one(x, case):                                            # a single station at x (its leaving pipe = rising main)
        s1, dep1 = state(full - {nxt[x]}, sub)
        return dict(sub=sub, case=case, station=T.lab[x], below_m=down(line, x) if x in line else np.nan,
                    station_m=dep1[x], ground=T.ground[x], flow_2056_ls=T.dy.flow_m3d.get(nxt[x], np.nan) / 86.4, **s1)
    keep = [one(ids[s], f"only {s}") for s in pair]              # keep one of the two as mapped
    R = pd.DataFrame([one(x, "one site") for x in line[:-1]])    # one station anywhere both flows pass
    rows += keep + R.to_dict("records")
    ok = R[R.deep_for_good == 0]
    pick = ok.loc[ok.station_m.idxmin()] if len(ok) else R.loc[(R[["station_m", "deepest_m"]].max(axis=1)).idxmin()]
    for r in map(pd.Series, keep):
        L.append(f"| {r.case} | {r.stations} | {r.station} {r.station_m:.2f} m | {r.outfall_m:.2f} m | {r.deepest} {r.deepest_m:.2f} m | "
                 f"{r.mh_over12} | {r.km_over12:.2f} km | {r.deep_for_good} |")
    L.append(f"| **one station at {pick.station}** ({pick.below_m:.0f} m below {up_s or T.lab[conf]}, {pick.flow_2056_ls:.1f} L/s) | {pick.stations} | "
             f"**{pick.station} {pick.station_m:.2f} m** | {pick.outfall_m:.2f} m | {pick.deepest} {pick.deepest_m:.2f} m | {pick.mh_over12} | "
             f"{pick.km_over12:.2f} km | {pick.deep_for_good} |")
    # what makes the line deep: the design itself, or the steepening below the stations
    below = {nxt[y] for s in pair for y in path(ids[s])[:-1]}
    st = [k for k in below if T.links[k]["kind"] == "pipe" and T.links[k]["S"] > T.links[k]["S0"] + 1e-9]
    keep_s = {k: T.links[k]["S"] for k in st}
    for k in st: T.links[k]["S"] = T.links[k]["S0"]
    r0, _ = state(full, sub)
    for k in st: T.links[k]["S"] = keep_s[k]
    under = [k for k in st if T.dy.at[k, "V31_SG"] < T.V_SC]
    L.append(f"| none of the two, the {len(st)} steepened pipes below them ({sum(T.links[k]['L'] for k in st) / 1000:.2f} km) left at the "
             f"design gradient | {r0['stations']} | - | {r0['outfall_m']:.2f} m | {r0['deepest']} {r0['deepest_m']:.2f} m | {r0['mh_over12']} | "
             f"{r0['km_over12']:.2f} km | {r0['deep_for_good']} |")
    L += ["", f"As designed (SewerGEMS, no steepening, no cut) the {sub} outfall is {T.base_depth[term[sub]]:.2f} m deep; steepened to 0.50 % "
          f"with no cut, {T.dsteep[term[sub]]:.2f} m. Below the two stations {len(st)} pipes are steepened; left at the design gradient, "
          f"{len(under)} of them ({sum(T.links[k]['L'] for k in under) / 1000:.2f} km) stay under 0.75 m/s at the 2031 peak."]
    first = up_s or T.lab[conf]
    L += ["", (f"One station tried at every manhole from {first} to the outfall ({len(R)} sites): {len(ok)} leave nothing deeper "
               f"than 12 m for good; the shallowest such station is {pick.station} at {pick.station_m:.2f} m.") if len(ok) else
              (f"One station tried at every manhole from {first} to the outfall ({len(R)} sites): none leaves the subnetwork clear "
               f"of 12 m; the least deep is {pick.station} (station {pick.station_m:.2f} m, deepest {pick.deepest_m:.2f} m)."), ""]
def unsteepen_to_drop(start, keep_st, drop_st, sub, note):
    """drop_st removed; the fewest steepened pipes below keep_st's lift, from the top down, put back to the design
    gradient until nothing in the subnetwork is deeper than 12 m for good."""
    act = start | {cut_of[drop_st]}; nx = T.downstream_map(act)
    p = [T.links[cut_of[keep_st]]["dn"]]
    while p[-1] in nx: p.append(T.links[nx[p[-1]]]["dn"])
    steep = [nx[y] for y in p[:-1] if T.links[nx[y]]["S"] > T.links[nx[y]]["S0"] + 1e-9]
    accepted = state(start, sub)[0]["deep_for_good"]    # what the start already accepts (the O9-M101 merge: 2 manholes)
    for n in range(len(steep) + 1):
        old = {k: T.links[k]["S"] for k in steep[:n]}
        for k in steep[:n]: T.links[k]["S"] = T.links[k]["S0"]
        r, _ = state(act, sub)
        for k, s in old.items(): T.links[k]["S"] = s
        if r["deep_for_good"] <= accepted:
            km = sum(T.links[k]["L"] for k in steep[:n]) / 1000
            ku = sum(T.links[k]["L"] for k in steep[:n] if T.dy.at[k, "V31_SG"] < T.V_SC) / 1000
            return (f"| {drop_st} dropped{note} | {n} pipes, {km:.2f} km (to {T.links[steep[n - 1]]['label'] if n else '-'}) | {ku:.2f} km | "
                    f"{r['stations']} | {r['outfall_m']:.2f} m | {r['deepest']} {r['deepest_m']:.2f} m | {r['mh_over12']} | {r['km_over12']:.2f} km |")
    return f"| {drop_st} dropped{note} | no stretch clears it | | | | | | |"


L += ["## O9-M728 without a station: the steepened run below it left at the design gradient", "",
      "None of the pipes between O9-M773 and O9-M728 is steepened; O9-M728 is needed because the steepened run below it goes deep. "
      "Steepened pipes below O9-M773's lift, from the top down, put back to the design gradient until nothing in O9 is deeper than 12 m for good:", "",
      "| case | left at the design gradient | of it under 0.75 m/s at 2031 | stations in total | outfall depth | deepest manhole | manholes > 12 m | pipe > 12 m |",
      "|---|---|---|---|---|---|---|---|",
      unsteepen_to_drop(base0, "O9-M773", "O9-M728", "O9", ""),
      unsteepen_to_drop(merged(base0, ["O9-M103", "O9-M89"], "O9-M101"), "O9-M773", "O9-M728", "O9", ", O9-M103 and O9-M89 merged at O9-M101"), ""]
# ------------------------------------------------------------------ the engineer's choice (2026-11-18)
# O12 without its two new stations (outfall 14.6 m accepted); O9-M103 and O9-M89 as one station at O9-M101 (12.6 m
# accepted); O9-M728 removed and O9-M773 kept (station 12.0 m, O9 outfall 14.3 m accepted). All else as C1.
choice = merged(base0, ["O9-M103", "O9-M89"], "O9-M101") | {cut_of[s] for s in ("O12-M26", "O12-M193", "O9-M728")}
inv_c, li_c = T.relay(choice); R_c, dep_c, _ = T.regions(choice, inv_c)
ups_c = {T.links[k]["up"] for k in choice}; outs_c = {T.links[k]["dn"] for k in choice} - ups_c - T.plants
new_c = sorted((T.lab[n], dep_c[n]) for n in outs_c if n not in T.orig_terminals)
mh_c = {n: v for n, v in dep_c.items() if n in T.mh.index}
pk = [k for k in choice if T.links[k]["kind"] == "pipe"]
km12_c = sum(T.links[k]["L"] for k in pk if max(T.ground.get(T.links[k]["up"], np.nan) - li_c[k][0],
                                                 T.ground.get(T.links[k]["dn"], np.nan) - li_c[k][1]) > T.DMAX) / 1000
d = T.dy.loc[pk].copy(); d["under"] = d.V31 < T.V_SC; big_c = d[d.NOM > 200]; und = big_c[big_c.under]
assert len(set(T.best["active"]) ^ set(choice)) <= 8                       # only the pair links differ from C1
L += ["## The engineer's choice (2026-11-18): O12 kept deep, O9-M103 + O9-M89 at O9-M101, O9-M728 removed", "",
      f"- **Stations: {T.n_stations(choice)}** (C1 as mapped 25); new stations left: " + ", ".join(f"{a} {b:.2f} m" for a, b in new_c) + ".",
      f"- Outfalls: O12 {dep_c[term['O12']]:.2f} m, O9 {dep_c[term['O9']]:.2f} m, O11 {dep_c[term['O11']]:.2f} m, O14 {dep_c[term['O14']]:.2f} m "
      f"(accepted deep); deeper than 12 m for good: " + ", ".join(f"{s} {sum(1 for n in R_c if str(T.lab.get(n, '')).split('-')[0] == s)} manholes"
                                                       for s in ("O12", "O9")) + ".",
      f"- Manholes deeper than 12 m: {sum(v > T.DMAX for v in mh_c.values())} (C1 {T.S['mh_over12']}); deepest {max(mh_c.values()):.2f} m; "
      f"pipe deeper than 12 m {km12_c:.1f} km (C1 {T.S['km_pipes_over12']:.1f} km).",
      f"- **Self-cleansing (gradients are set before the split, so the station choice does not change them):** above DN200 "
      f"{und.length_m.sum() / 1000:.1f} of {big_c.length_m.sum() / 1000:.1f} km under 0.75 m/s at the 2031 peak "
      f"({und.length_m.sum() / big_c.length_m.sum() * 100:.1f} %), {len(und)} pipes; DN200 not checked (rule), "
      f"{d[(d.NOM <= 200) & d.under].length_m.sum() / 1000:.0f} of {d[d.NOM <= 200].length_m.sum() / 1000:.0f} km under 0.75 m/s.", ""]
need = und.S_REQ * 100
bands = [("needs 0.50 to 0.75 %", (need > 0.5) & (need <= 0.75)), ("needs 0.75 to 1.00 %", (need > 0.75) & (need <= 1.0)),
         ("needs 1.00 to 2.00 %", (need > 1.0) & (need <= 2.0)), ("needs over 2.00 %", need > 2.0),
         ("cannot reach 0.75 m/s at any gradient", need.isna())]
vb = [("0.60 to 0.75 m/s", und.V31 >= 0.60), ("0.45 to 0.60 m/s", (und.V31 >= 0.45) & (und.V31 < 0.60)),
      ("0.30 to 0.45 m/s", (und.V31 >= 0.30) & (und.V31 < 0.45)), ("under 0.30 m/s", und.V31 < 0.30)]
L += ["| pipes above DN200 under 0.75 m/s at 2031 | pipes | km |", "|---|---|---|"]
L += [f"| {a} | {int(m.sum())} | {und.length_m[m].sum() / 1000:.1f} |" for a, m in bands]
L += [f"| velocity {a} | {int(m.sum())} | {und.length_m[m].sum() / 1000:.1f} |" for a, m in vb]
L += ["", "| subnetwork | under 0.75 m/s | of above DN200 | share | 2031 velocity, median | 2031 flow, median |", "|---|---|---|---|---|---|"]
for s, g in sorted(big_c.groupby("SUB"), key=lambda x: -x[1][x[1].under].length_m.sum()):
    u = g[g.under]
    if len(u): L.append(f"| {s} | {u.length_m.sum() / 1000:.2f} km | {g.length_m.sum() / 1000:.2f} km | {u.length_m.sum() / g.length_m.sum() * 100:.0f} % | "
                        f"{u.V31.median():.2f} m/s | {u.Q31.median() * 1000:.1f} L/s |")
L += ["", "| size | under 0.75 m/s | of the size | share |", "|---|---|---|---|"]
for n, g in big_c.groupby("NOM"):
    u = g[g.under]
    if len(u): L.append(f"| DN{n:.0f} | {u.length_m.sum() / 1000:.2f} km | {g.length_m.sum() / 1000:.2f} km | {u.length_m.sum() / g.length_m.sum() * 100:.0f} % |")
L.append("")
und.assign(dn_mm=und.NOM.astype(int), s_laid_pc=und.S_LAID * 100, s_new_pc=und.S_NEW * 100, s_needed_pc=need,
           q2031_ls=und.Q31 * 1000, v2031_ms=und.V31, v2056_ms=und.V56)[
    ["label", "SUB", "dn_mm", "length_m", "s_laid_pc", "s_new_pc", "s_needed_pc", "q2031_ls", "v2031_ms", "v2056_ms"]].rename(
    columns={"SUB": "sub"}).sort_values(["sub", "label"]).to_csv(os.path.join(OUT, "under_075_engineer_choice.csv"), index=False, float_format="%.3f")
pd.DataFrame(rows).to_csv(os.path.join(OUT, "single_station_sites.csv"), index=False, float_format="%.2f")
open(os.path.join(OUT, "WHATIF.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
