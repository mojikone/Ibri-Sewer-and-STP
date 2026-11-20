"""SC1 designed without SewerGEMS, to test whether the two give the same answer (engineer, 2026-11-18: "do you design
yourself as well without SewerGEMS? ... if you do yourself for 2051 and with SewerGEMS, the results will be the same?").
Run BEFORE SewerGEMS's SC1-2051 design (job 076) had finished, so the comparison is blind.

The rules, each read from SewerGEMS's SC1-2056 design (job 074) and checked on it here first:
- Flow in a pipe = PF x (unit loads upstream, the pipe's upstream manhole included) + 720 L/km/day on the conduits
  upstream + the transfers from upstream outfalls (not re-peaked, R2 test). PF = 'Peltier100-Merriamck', linear between
  rows, on the cumulative base in L/s, with the R3 step row 1.001 L/s -> 3.56.
- Gradient = the Table 11 minimum of the pipe's size (all 19,083 pipes of SC1-2056 sit on it).
- Size = the smallest catalogue size whose Colebrook-White capacity (ks 1.5 mm, nu 1.141e-6) at the d/D limit (0.65 up
  to DN355, 0.50 above, the largest d/D found per size in SC1-2056) carries the flow at the Table 11 gradient of the
  pipe's CURRENT size, repeated pass after pass from the modeller's sizes (R4, the flow-check export) until no size
  changes - SewerGEMS's own way: on 2056 it gives SewerGEMS's size on every pipe in 3 passes, where sizing each
  candidate at its own gradient gives 63 pipes one size smaller (DN315->280, 450->355, 500->450).
- Inverts: re-laid by py/split_deep_subnetworks.py from these sizes and gradients (crowns matched, 1.3 m cover).
The network (pipes, manholes, ground) is SC1-2056's: a different design year changes sizes, gradients and inverts, not
the layout. Writes, in SewerGEMS's export format so py/split_deep_subnetworks.py reads it unchanged,
results/sc1_2051/own_design/exports/ (conduits_<tag>a.csv, conduits_<tag>-at-2031.csv, manholes_<tag>a.csv,
transfers_<tag>.csv) and check_2056.md (the rules against SewerGEMS's own 2056 design).
Usage: python own_design.py 2051"""
import sys, os, math, shutil
import numpy as np, pandas as pd

G, NU, KS = 9.81, 1.141e-6, 1.5e-3
YEAR = sys.argv[1] if len(sys.argv) > 1 else "2051"
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
SG = r"D:\VBOX\bridge\out\w18\scen"
OUT = os.path.join(W18, "results", f"sc1_{YEAR}", "own_design"); EXP = os.path.join(OUT, "exports")
os.makedirs(EXP, exist_ok=True)
TAB = [(0.1, 4.66), (0.15, 4.08), (0.2, 3.74), (0.3, 3.33), (0.5, 2.91), (0.75, 2.65), (1, 2.5), (1.001, 3.56), (1.5, 3.39),
       (2, 3.28), (3, 3.12), (5, 2.93), (7.5, 2.79), (10, 2.7), (15, 2.57), (20, 2.48), (30, 2.36), (50, 2.22), (75, 2.11),
       (100, 2.04), (150, 1.94), (200, 1.88), (300, 1.79), (500, 1.68), (750, 1.6), (1000, 1.54)]
pf = lambda q: float(np.interp(q, [t[0] for t in TAB], [t[1] for t in TAB]))
INF = 0.72                                             # m3/day per km of conduit

d = pd.read_csv(os.path.join(SG, "SC1-2056", "conduits_SC1-2056.csv")); d = d[d.active == True].copy().reset_index(drop=True)
d["NOM"] = d.size_label.str.extract(r"(\d+)")[0].astype(int)
d["UP"] = np.where(d.start_inv >= d.stop_inv, d.start, d.stop); d["DN"] = np.where(d.start_inv >= d.stop_inv, d.stop, d.start)
d["S"] = (d[["start_inv", "stop_inv"]].max(axis=1) - d[["start_inv", "stop_inv"]].min(axis=1)) / d.length_m
CAT = d.groupby("NOM").diameter_mm.first().sort_index() / 1000.0          # catalogue sizes in use, internal diameter
SLOPE = d.groupby("NOM").S.agg(lambda s: s.round(6).mode().iloc[0])      # Table 11 gradient per size
LIM = lambda nom: 0.65 if nom <= 355 else 0.50
loads = pd.read_csv(os.path.join(W18, "results", "loads", "manhole_loads.csv"), index_col="manhole_id")
trs = {y: pd.read_csv(os.path.join(SG, f"SC1-{y}", f"transfers_SC1-{y}.csv")) for y in ("2056", YEAR)}


def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)


def v_cw(R, S):
    a = math.sqrt(8 * G * R * S); return -2 * a * math.log10(KS / (14.8 * R) + 2.51 * NU / (4 * R * a))


def qcap(D, S, r):
    A, R = section(D, r * D); return A * v_cw(R, S)


def normal(Q, D, S):                                   # depth ratio and velocity at normal depth
    if Q <= 0: return 0.0, 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2; A, R = section(D, y)
        if A * v_cw(R, S) > Q: hi = y
        else: lo = y
    y = (lo + hi) / 2; A, R = section(D, y); return y / D, Q / A


def size_for(Q):
    for nom, D in CAT.items():
        if qcap(D, SLOPE[nom], LIM(nom)) >= Q: return nom
    return CAT.index[-1]


START = pd.read_csv(os.path.join(SG, "SC1-2056", "conduits_check2056.csv")).set_index("label").size_label           .reindex(d.label).str.extract(r"(\d+)")[0].astype(int).values        # the modeller's sizes (R4)


def design(Q):
    """SewerGEMS's passes: each pipe sized at the gradient of its current size, until no size changes."""
    nom = START.copy()
    for p in range(1, 21):
        new = np.array([next((s for s, D in CAT.items() if qcap(D, SLOPE.get(n, SLOPE[CAT.index[0]]), LIM(s)) >= q),
                             CAT.index[-1]) for q, n in zip(Q, nom)])
        changed = int((new != nom).sum()); nom = new
        if changed == 0: return pd.Series(nom), p
    raise RuntimeError("design did not settle in 20 passes")


# order the tree from the heads down
into = d.groupby("DN").groups; order, seen = [], set()
lead = {u: k for k, u in zip(d.index, d.UP)}
indeg = d.DN.value_counts().to_dict()
stack = [k for k, u in zip(d.index, d.UP) if u not in indeg]
pending = {n: c for n, c in indeg.items()}
while stack:
    k = stack.pop(); order.append(k); n = d.at[k, "DN"]
    if n in pending:
        pending[n] -= 1
        if pending[n] == 0 and n in lead: stack.append(lead[n])
assert len(order) == len(d), (len(order), len(d))


def flows(year, own_length=True):
    base = loads[f"Q_{year}"].to_dict(); t = trs[year if year in trs else "2056"]
    tr = t[t.year == int(year)].groupby("receiver_id").flow_m3d.sum().to_dict()
    cb, cl, ct = {}, {}, {}
    for k in order:
        u = d.at[k, "UP"]; ks = into.get(u, [])
        cb[k] = base.get(u, 0.0) + sum(cb[j] for j in ks)
        cl[k] = d.at[k, "length_m"] * own_length + sum(cl[j] + d.at[j, "length_m"] * (not own_length) for j in ks)
        ct[k] = tr.get(u, 0.0) + sum(ct[j] for j in ks)
    b = pd.Series(cb); return (b * [pf(x / 86.4) for x in b] + pd.Series(cl) / 1000 * INF + pd.Series(ct)).sort_index()


# ------------------------------------------------------------------ the rules against SewerGEMS's 2056 design
rep = [f"# Own design of SC1 against SewerGEMS (rules checked on SC1-2056, then applied to {YEAR})", ""]
q56 = flows("2056"); err = (q56 - d.flow_m3d) / d.flow_m3d * 100
q56b = flows("2056", own_length=False); errb = (q56b - d.flow_m3d) / d.flow_m3d * 100
use_own = err.abs().median() <= errb.abs().median()
e = err if use_own else errb; Q56 = q56 if use_own else q56b
rep.append(f"- **Flows 2056** (infiltration {'including' if use_own else 'excluding'} the pipe's own length): "
           f"within 0.1 % on {(e.abs() < 0.1).mean() * 100:.1f} % of {len(d):,} pipes, within 1 % on {(e.abs() < 1).mean() * 100:.1f} %, "
           f"largest {e.abs().max():.2f} % ({d.label[e.abs().idxmax()]}).")
mine56, p56 = design(d.flow_m3d.values / 86400.0)
mine56o, _ = design(Q56.values / 86400.0)
big = d.NOM > 200
for name, m in (("on SewerGEMS's flows", mine56), ("on my flows", mine56o)):
    same = m == d.NOM
    rep.append(f"- **Sizes 2056 {name}:** same as SewerGEMS on {same.sum():,} of {len(d):,} pipes ({same.mean() * 100:.2f} %), "
               f"above DN200 {same[big].sum():,} of {big.sum():,}; mine smaller on {(m < d.NOM).sum()}, larger on {(m > d.NOM).sum()}.")
gs = ((d.S - d.NOM.map(SLOPE)).abs() < 1e-5).mean() * 100
rep.append(f"- **Gradients:** {gs:.2f} % of pipes at the Table 11 gradient of their size: "
           + ", ".join(f"DN{n} {s * 100:.3f} %" for n, s in SLOPE.items()) + ".")

# ------------------------------------------------------------------ the design for YEAR, written as SewerGEMS exports
QY, Q31 = flows(YEAR) / 86400.0, flows("2031") / 86400.0
nom, pY = design(QY.values)
rep.append(f"- **{YEAR} design** ({pY} passes): {(nom != d.NOM).sum():,} pipes change size against 2056 "
           f"({(nom < d.NOM).sum():,} smaller, {(nom > d.NOM).sum()} larger), "
           f"{d.length_m[nom != d.NOM].sum() / 1000:.1f} km; above DN200 {(nom > 200).sum():,} pipes, "
           f"{d.length_m[nom > 200].sum() / 1000:.1f} km (2056: {big.sum():,}, {d.length_m[big].sum() / 1000:.1f} km).")
tag = f"SC1-{YEAR}"
e2 = d[["id", "label", "start", "stop", "active", "length_m"]].copy()
e2["diameter_mm"] = nom.map(CAT).values * 1000; e2["size_label"] = nom.astype(str) + " mm"
s_new = nom.map(SLOPE).values; drop = s_new * d.length_m.values
up_is_start = (d.UP == d.start).values
e2["start_inv"] = np.where(up_is_start, 1000.0, 1000.0 - drop); e2["stop_inv"] = np.where(up_is_start, 1000.0 - drop, 1000.0)
for f, Q in ((f"conduits_{tag}a.csv", QY), (f"conduits_{tag}-at-2031.csv", Q31)):
    x = e2.copy(); x["flow_m3d"] = Q.values * 86400.0
    nv = [normal(q, D / 1000, s) for q, D, s in zip(Q.values, x.diameter_mm, s_new)]
    x["velocity_ms"] = [v for _, v in nv]; x["depth_in_m"] = x["depth_out_m"] = [r * D / 1000 for (r, _), D in zip(nv, x.diameter_mm)]
    x.to_csv(os.path.join(EXP, f), index=False)
shutil.copy(os.path.join(SG, "SC1-2056", "manholes_SC1-2056a.csv"), os.path.join(EXP, f"manholes_{tag}a.csv"))
shutil.copy(os.path.join(SG, tag, f"transfers_{tag}.csv"), os.path.join(EXP, f"transfers_{tag}.csv"))
pd.DataFrame({"label": d.label, "nom_2056_sg": d.NOM, f"nom_{YEAR}_own": nom, f"q_{YEAR}_own_ls": QY.values * 1000,
              "q_2031_own_ls": Q31.values * 1000}).to_csv(os.path.join(OUT, f"pipes_own_{YEAR}.csv"), index=False)
open(os.path.join(OUT, "check_2056.md"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
print("\n".join(rep))
