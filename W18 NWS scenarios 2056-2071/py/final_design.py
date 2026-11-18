"""W18 final design (engineer, 2026-11-18): every scenario (SC1 STP 1 only, SC2 STP 16 only, SC3 STP 1 + STP 5, SC4
STP 16 + STP 5) designed for 2051, 2056 and 2061 without SewerGEMS, by the rules py/own_design.py proved against
SewerGEMS's own SC1 design (flows to 0.004 %, every size, checked blind on 2051):
- flow in a pipe = PF ('Peltier100-Merriamck' on the cumulative unit load, L/s) x the unit load upstream + 720 L/km/day
  on the conduits upstream (its own length included) + the flows pumped in from upstream subnetworks (not re-peaked);
- gradient = the PAM-GUD-203 Table 11 minimum of the pipe's size;
- size = the smallest catalogue size whose Colebrook-White capacity (ks 1.5 mm) at the d/D limit (0.65 up to DN355,
  0.50 above) carries the flow at the gradient of the pipe's current size, pass after pass from the modeller's sizes.
The gravity network is the same in every scenario; the scenario sets which outfalls are plant inlets and where every
other outfall pumps to (py/routing.py). Writes, in SewerGEMS's export format so py/split_deep_subnetworks.py reads it
unchanged, results/final_0.75pc_SC1-SC4/<SC>-<year>/exports/: conduits_<tag>a.csv (design year), conduits_<tag>-at-2031
.csv and -at-2036.csv (the check years, velocity at normal depth), manholes_<tag>a.csv, transfers_<tag>.csv.
Usage: python final_design.py SC2 2056"""
import sys, os, math, shutil, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from routing import transfers, node_maps, SCENARIOS

G, NU, KS = 9.81, 1.141e-6, 1.5e-3
NAME, YEAR = sys.argv[1], sys.argv[2]
CHECKS = ["2031", "2036"]
TAG = f"{NAME}-{YEAR}"
ROOT = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); INP = os.path.join(ROOT, "inputs")
EXP = os.path.join(ROOT, TAG, "exports"); os.makedirs(EXP, exist_ok=True)
TAB = [(0.1, 4.66), (0.15, 4.08), (0.2, 3.74), (0.3, 3.33), (0.5, 2.91), (0.75, 2.65), (1, 2.5), (1.001, 3.56), (1.5, 3.39),
       (2, 3.28), (3, 3.12), (5, 2.93), (7.5, 2.79), (10, 2.7), (15, 2.57), (20, 2.48), (30, 2.36), (50, 2.22), (75, 2.11),
       (100, 2.04), (150, 1.94), (200, 1.88), (300, 1.79), (500, 1.68), (750, 1.6), (1000, 1.54)]
pf = lambda q: float(np.interp(q, [t[0] for t in TAB], [t[1] for t in TAB]))
INF = 0.72                                             # m3/day per km of conduit
LIM = lambda nom: 0.65 if nom <= 355 else 0.50

# the network (SewerGEMS SC1-2056 design export, R5) and the modeller's starting sizes (R4 flow check), kept in inputs/
d = pd.read_csv(os.path.join(INP, "conduits_network.csv")); d = d[d.active == True].copy().reset_index(drop=True)
d["NOM"] = d.size_label.str.extract(r"(\d+)")[0].astype(int)
d["UP"] = np.where(d.start_inv >= d.stop_inv, d.start, d.stop); d["DN"] = np.where(d.start_inv >= d.stop_inv, d.stop, d.start)
cat = pd.read_csv(os.path.join(INP, "catalogue.csv")).sort_values("nominal_mm")          # nominal_mm, inside_mm
CAT = pd.Series(cat.inside_mm.values / 1000.0, index=cat.nominal_mm.values)
# Table 11 minimum gradient per size (PAM-GUD-203; the design sits on it): from SewerGEMS's design per size in use,
# 0.075 % for DN900 and above
S_DES = d.assign(S=(d[["start_inv", "stop_inv"]].max(axis=1) - d[["start_inv", "stop_inv"]].min(axis=1)) / d.length_m)
SLOPE = S_DES.groupby("NOM").S.agg(lambda s: s.round(6).mode().iloc[0]).to_dict()
for n in CAT.index:
    if n not in SLOPE: SLOPE[n] = 0.00075 if n >= 900 else {400: 0.00205}.get(n, np.nan)   # Table 11, p29
assert not any(np.isnan(SLOPE[n]) for n in CAT.index), {n: SLOPE[n] for n in CAT.index if np.isnan(SLOPE[n])}
START = pd.read_csv(os.path.join(INP, "conduits_start_sizes.csv")).set_index("label").size_label \
    .reindex(d.label).str.extract(r"(\d+)")[0].astype(int).values
loads = pd.read_csv(os.path.join(W18, "results", "loads", "manhole_loads.csv"), index_col="manhole_id")
_, new2id = node_maps()


def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)


def v_cw(R, S):
    a = math.sqrt(8 * G * R * S); return -2 * a * math.log10(KS / (14.8 * R) + 2.51 * NU / (4 * R * a))


def qcap(D, S, r):
    A, R = section(D, r * D); return A * v_cw(R, S)


def normal(Q, D, S):
    if Q <= 0: return 0.0, 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2; A, R = section(D, y)
        if A * v_cw(R, S) > Q: hi = y
        else: lo = y
    y = (lo + hi) / 2; A, R = section(D, y); return y / D, Q / A


def design(Q):
    nom = START.copy()
    for p in range(1, 21):
        new = np.array([next((s for s, D in CAT.items() if qcap(D, SLOPE[n], LIM(s)) >= q), CAT.index[-1]) for q, n in zip(Q, nom)])
        changed = int((new != nom).sum()); nom = new
        if changed == 0: return pd.Series(nom), p
    raise RuntimeError("design did not settle in 20 passes")


into = d.groupby("DN").groups; order = []
lead = {u: k for k, u in zip(d.index, d.UP)}
pending = d.DN.value_counts().to_dict()
stack = [k for k, u in zip(d.index, d.UP) if u not in pending]
while stack:
    k = stack.pop(); order.append(k); n = d.at[k, "DN"]
    if n in pending:
        pending[n] -= 1
        if pending[n] == 0 and n in lead: stack.append(lead[n])
assert len(order) == len(d)

TR = {}                                                  # year -> {receiver manhole id: m3/d}; rows for the export
rows_out = []
for y in [YEAR] + CHECKS:
    rows, _ = transfers(NAME, y); TR[y] = {}
    for year, s, mh, r, q in rows:
        TR[y][new2id[mh]] = TR[y].get(new2id[mh], 0.0) + q; rows_out.append([int(year), s, new2id[mh], mh, q])


# --lifts (2026-11-18): the lift stations of the case's last split (split/cuts_<case>.csv) pump their flow to the next
# manhole as a transfer of its peak, not re-peaked - the project's rule for anything pumped (R2 test) - so the sewers
# below a lift are sized for what the model will carry
CUT = set()
if "--lifts" in sys.argv:
    cuts_csv = os.path.join(ROOT, TAG, "split", f"cuts_{TAG}.csv")
    CUT = set(d.index[d.label.isin(pd.read_csv(cuts_csv)["pipe"])]) if os.path.exists(cuts_csv) else set()
LIFT_TR = {}                                             # year -> [(station label, receiver id, m3/d)]


def flows(year):
    base = loads[f"Q_{year}"].to_dict(); tr = dict(TR[year]); cb, cl, ct, q = {}, {}, {}, {}
    LIFT_TR[year] = []
    for k in order:
        u = d.at[k, "UP"]; ks = [j for j in into.get(u, []) if j not in CUT]
        cb[k] = base.get(u, 0.0) + sum(cb[j] for j in ks)
        cl[k] = d.at[k, "length_m"] + sum(cl[j] for j in ks)
        ct[k] = tr.get(u, 0.0) + sum(ct[j] for j in ks)
        q[k] = cb[k] * pf(cb[k] / 86.4) + cl[k] / 1000 * INF + ct[k]
        if k in CUT:                                     # the lift's peak lands on the next manhole
            dn = d.at[k, "DN"]; tr[dn] = tr.get(dn, 0.0) + q[k]; LIFT_TR[year].append((d.at[k, "label"], int(dn), q[k]))
    return pd.Series(q).sort_index()


Q = {y: flows(y) / 86400.0 for y in [YEAR] + CHECKS}
nom, passes = design(Q[YEAR].values)
over = Q[YEAR].values > np.array([qcap(CAT[n], SLOPE[n], LIM(n)) for n in nom]) * 1.0001
e2 = d[["id", "label", "start", "stop", "active", "length_m"]].copy()
e2["diameter_mm"] = nom.map(CAT).values * 1000; e2["size_label"] = nom.astype(str) + " mm"
s_new = nom.map(SLOPE).values; drop = s_new * d.length_m.values
up_is_start = (d.UP == d.start).values                     # inverts only carry the direction and the gradient: the
e2["start_inv"] = np.where(up_is_start, 1000.0, 1000.0 - drop)  # split re-lays them from the ground and the cover
e2["stop_inv"] = np.where(up_is_start, 1000.0 - drop, 1000.0)
for f, y in ((f"conduits_{TAG}a.csv", YEAR),) + tuple((f"conduits_{TAG}-at-{c}.csv", c) for c in CHECKS):
    x = e2.copy(); x["flow_m3d"] = Q[y].values * 86400.0
    nv = [normal(q, D / 1000, s) for q, D, s in zip(Q[y].values, x.diameter_mm, s_new)]
    x["velocity_ms"] = [v for _, v in nv]; x["depth_in_m"] = x["depth_out_m"] = [r * D / 1000 for (r, _), D in zip(nv, x.diameter_mm)]
    x.to_csv(os.path.join(EXP, f), index=False)
shutil.copy(os.path.join(INP, "manholes_network.csv"), os.path.join(EXP, f"manholes_{TAG}a.csv"))
pd.DataFrame(rows_out, columns=["year", "source", "receiver_id", "receiver_label", "flow_m3d"]).to_csv(
    os.path.join(EXP, f"transfers_{TAG}.csv"), index=False)
S = dict(tag=TAG, scenario=SCENARIOS[NAME]["text"], passes=passes, pipes=len(d), over_largest_size=int(over.sum()),
         sizes={int(k): int(v) for k, v in nom.value_counts().sort_index().items()},
         km_above_dn200=round(float(d.length_m[nom.values > 200].sum()) / 1000, 2),
         largest=int(nom.max()), q_design_max_ls=round(float(Q[YEAR].max()) * 1000, 1))
json.dump(S, open(os.path.join(ROOT, TAG, "design.json"), "w"), indent=1)
print(json.dumps(S))
