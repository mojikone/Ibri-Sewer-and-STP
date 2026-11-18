"""SC1-2051 (engineer, 2026-11-18): my own design (py/own_design.py, run blind before SewerGEMS finished) against
SewerGEMS's design (job 076), both through py/split_deep_subnetworks.py at 0.50 %; and what the 2051 pipes carry in 2056.
Usage: python compare_own_sewergems.py   (after own_design.py 2051, job 076 and the split runs)
Writes results/sc1_2051/COMPARISON.md"""
import os, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "sc1_2051"); SG = r"D:\VBOX\bridge\out\w18\scen\SC1-2051"
R56 = os.path.join(W18, "results", "sc1_conditions")
LIM = lambda nom: 0.65 if nom <= 355 else 0.50
out = ["# SC1 designed for 2051: SewerGEMS against my own design, and the 2051 pipes in 2056", ""]

# ---------------------------------------------------------------- pipe by pipe, the design (as designed, C0)
own = pd.read_csv(os.path.join(R, "own_design", "pipes_own_2051.csv")).set_index("label")
sg = pd.read_csv(os.path.join(SG, "conduits_SC1-2051.csv")); sg = sg[sg.active == True].set_index("label")
sg["NOM"] = sg.size_label.str.extract(r"(\d+)")[0].astype(int)
same = own["nom_2051_own"] == sg.NOM.reindex(own.index)
L = sg.length_m.reindex(own.index)
out.append(f"- **Sizes:** same on {same.sum():,} of {len(own):,} pipes ({same.mean() * 100:.2f} %); "
           f"different on {(~same).sum()} ({L[~same].sum() / 1000:.2f} km).")
if (~same).any():
    x = own[~same].join(sg.NOM.rename("sg"))
    out.append("  " + ", ".join(f"{k} own DN{a} / SewerGEMS DN{b}" for k, a, b in zip(x.index[:12], x.nom_2051_own, x.sg)))
    new_sizes = sorted(set(x.sg) - set(x.nom_2051_own))
    out.append(f"  SewerGEMS used DN{', DN'.join(map(str, new_sizes))}, in its catalogue but on no 2056 pipe, so missing from the "
               "catalogue the own design read off the 2056 design. Rerun with it added (not blind):")
    import own_design as od
    for n in new_sizes:
        y = sg[sg.NOM == n]; s = ((y[["start_inv", "stop_inv"]].max(axis=1) - y[["start_inv", "stop_inv"]].min(axis=1)) / y.length_m).median()
        od.CAT[n] = y.diameter_mm.iloc[0] / 1000; od.SLOPE[n] = round(s, 6)
    od.CAT = od.CAT.sort_index()
    for yr, ref in (("2051", sg.NOM.reindex(od.d.label).values), ("2056", od.d.NOM.values)):
        nm, p = od.design(od.flows(yr).values / 86400.0)
        out.append(f"  {yr}: same size on {(nm.values == ref).sum():,} of {len(ref):,} pipes ({p} passes).")
d56 = pd.read_csv(os.path.join(r"D:\VBOX\bridge\out\w18\scen\SC1-2056", "conduits_SC1-2056.csv")); d56 = d56[d56.active == True].set_index("label")
n56 = d56.size_label.str.extract(r"(\d+)")[0].astype(int).reindex(sg.index)
ch = sg.NOM != n56
out.append(f"- **SewerGEMS 2051 against its 2056 design:** {ch.sum():,} pipes change size ({(sg.NOM < n56).sum():,} smaller, "
           f"{(sg.NOM > n56).sum()} larger), {sg.length_m[ch].sum() / 1000:.1f} km; above DN200 {(sg.NOM > 200).sum():,} pipes, "
           f"{sg.length_m[sg.NOM > 200].sum() / 1000:.1f} km (2056: {(n56 > 200).sum():,}, {sg.length_m[n56 > 200].sum() / 1000:.1f} km).")
q = sg.flow_m3d.reindex(own.index) / 86.4; e = (own.q_2051_own_ls - q) / q * 100
out.append(f"- **Design flows 2051:** within 0.1 % on {(e.abs() < 0.1).mean() * 100:.1f} % of pipes, largest {e.abs().max():.3f} %.")

# ---------------------------------------------------------------- the two through the same 0.50 % split
rows = []
for name, sub in (("SewerGEMS design", "sewergems"), ("own design", "own_design")):
    for cond in ("C0_as_designed", "C1_limit_0.50pc"):
        p = os.path.join(R, sub, cond, "summary_SC1-2051.json")
        if os.path.exists(p): rows.append((name, cond, json.load(open(p, encoding="utf-8"))))
p56 = os.path.join(R56, "C1_limit_0.50pc", "summary_SC1-2056.json")
if os.path.exists(p56): rows.append(("SewerGEMS design 2056 (for reference)", "C1_limit_0.50pc", json.load(open(p56, encoding="utf-8"))))
out += ["", "| design | condition | stations | new | joined by gravity | above DN200 under 0.75 m/s at 2031 | manholes > 12 m | deepest |",
        "|---|---|---|---|---|---|---|---|"]
for name, cond, S in rows:
    out.append(f"| {name} | {cond} | {S.get('stations')} | {S.get('stations_new', '-')} | {S.get('joined', '-')} | "
               f"{S['km_big_under075']:.1f} of {S['km_big']:.1f} km ({S['km_big_under075'] / S['km_big'] * 100:.1f} %) | "
               f"{S.get('mh_over12')} | {S.get('mh_deepest'):.2f} m |")
for cond in ("C0_as_designed", "C1_limit_0.50pc"):
    a = os.path.join(R, "sewergems", cond, "pipes_SC1-2051.csv"); b = os.path.join(R, "own_design", cond, "pipes_SC1-2051.csv")
    if os.path.exists(a) and os.path.exists(b):
        A = pd.read_csv(a).set_index("label"); B = pd.read_csv(b).set_index("label").reindex(A.index)
        big = A.dn_mm > 200
        dv = (B.v2031_ms - A.v2031_ms)[big]
        flip = (A.under075 != B.under075)[big]
        out.append(f"- {cond}: 2031 velocity above DN200, own (Colebrook-White at normal depth) minus SewerGEMS: median "
                   f"{dv.median():+.3f}, 5-95 % {dv.quantile(.05):+.3f} to {dv.quantile(.95):+.3f} m/s; the 0.75 m/s verdict "
                   f"differs on {flip.sum()} pipes, {A.length_m[big & flip].sum() / 1000:.1f} km.")

# ---------------------------------------------------------------- the 2051 pipes in 2056
f = os.path.join(SG, "conduits_SC1-2051-at-2056.csv")
if os.path.exists(f):
    a = pd.read_csv(f); a = a[a.active == True].set_index("label")
    a["NOM"] = a.size_label.str.extract(r"(\d+)")[0].astype(int); a["D"] = a.diameter_mm / 1000
    a["dD"] = a[["depth_in_m", "depth_out_m"]].max(axis=1) / a.D; a["LIM"] = a.NOM.map(LIM)
    over = a.dD > a.LIM + 0.0005; full = a.dD >= 0.999
    smaller = (sg.NOM < n56).reindex(a.index)
    out += ["", f"**The 2051 pipes in 2056** (SewerGEMS analysis SC1-2051-at-2056, as designed, no steepening): "
            f"{over.sum():,} pipes, {a.length_m[over].sum() / 1000:.1f} km over the d/D limit (0.65 up to DN355, 0.50 above), "
            f"{over[smaller].sum():,} of them among the {smaller.sum():,} pipes that came out smaller than the 2056 design; "
            f"{full.sum()} running full; largest d/D {a.dD.max():.2f} ({a.dD.idxmax()}, DN{a.NOM[a.dD.idxmax()]}); "
            f"highest velocity {a.velocity_ms.max():.2f} m/s."]
    if over.any():
        g = a[over].groupby("NOM").agg(pipes=("NOM", "size"), km=("length_m", lambda s: s.sum() / 1000), dD_max=("dD", "max"))
        out.append("  By size: " + "; ".join(f"DN{n} {r.pipes} pipes {r.km:.1f} km (d/D up to {r.dD_max:.2f})" for n, r in g.iterrows()))
open(os.path.join(R, "COMPARISON.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
