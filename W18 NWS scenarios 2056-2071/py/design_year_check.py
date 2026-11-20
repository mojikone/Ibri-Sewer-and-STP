"""Does a design carry the flow of its design life? Each scenario's 2051 and 2061 designs are run at the 2056 peak, by the design
engine's own hydraulics (final_design.py: Colebrook-White, ks 1.5 mm, part-full circular section), on their own pipe sizes and
laid gradients; a pipe fails when its depth of flow exceeds 0.65 of the diameter up to DN355 or 0.50 above (PAM-GUD-203, p. 27).

    python design_year_check.py     writes results/final_0.75pc_SC1-SC4/design_year_check_2056.json (read by the report, 6.2.4
                                    and each scenario's options comparison, and by the workbook)

Sizes from exports/conduits_<case>a.csv (nominal and inside diameter), gradients from products/map.gpkg (s_new_pc, after the
steepening and the split), the 2056 peak from the 2056 design of the same scenario (exports/conduits_<SC>-2056a.csv; the flow of a
pipe does not depend on the year its sewers are sized for). Rebuilt 2026-11-20 for the toolkit: the first version was one-off code."""
import json, math, os, sys
import geopandas as gpd, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
G, NU, KS = 9.81, 1.141e-6, 1.5e-3
LIM = lambda nom: 0.65 if nom <= 355 else 0.50
TOL = 0.005        # d/D is judged at two decimals, as the limit is stated: 0.654 is 0.65, within the limit (the report's figures)


def section(D, y):
    th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)


def v_cw(R_, S):
    a = math.sqrt(8 * G * R_ * S); return -2 * a * math.log10(KS / (14.8 * R_) + 2.51 * NU / (4 * R_ * a))


def ratio(Q, D, S):
    """Depth of flow / diameter at normal depth; 1.0 when the pipe cannot carry Q part-full."""
    if Q <= 0: return 0.0
    A, R_ = section(D, 0.999 * D)
    if A * v_cw(R_, S) < Q: return 1.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2; A, R_ = section(D, y)
        if A * v_cw(R_, S) > Q: hi = y
        else: lo = y
    return (lo + hi) / 2 / D


out = {}
for sc in ("SC1", "SC2", "SC3", "SC4"):
    q56 = pd.read_csv(os.path.join(R, f"{sc}-2056", "exports", f"conduits_{sc}-2056a.csv")).set_index("label").flow_m3d / 86400.0
    for y in ("2051", "2061"):
        case = f"{sc}-{y}"
        c = pd.read_csv(os.path.join(R, case, "exports", f"conduits_{case}a.csv")).set_index("label")
        p = gpd.read_file(os.path.join(R, case, "products", "map.gpkg"), layer="pipes").set_index("old")
        p = p[p.index.isin(c.index)]
        nom = c.loc[p.index, "size_label"].str.extract(r"(\d+)")[0].astype(int).values
        D = c.loc[p.index, "diameter_mm"].values / 1000; S = p.s_new_pc.values / 100; Q = q56.reindex(p.index).fillna(0).values
        r = np.array([ratio(q, d_, s) for q, d_, s in zip(Q, D, S)]); lim = np.array([LIM(n) for n in nom])
        over = r >= lim + TOL                                     # over the limit when d/D rounds above it at two decimals
        out[case] = dict(pipes_over=int(over.sum()), km_over=round(float(p.length_m.values[over].sum()) / 1000, 1),
                         surcharged=int((r >= 1.0).sum()), max_dD=round(float(r[over].max()), 2) if over.any() else 0)
        print(case, out[case], flush=True)
json.dump(out, open(os.path.join(R, "design_year_check_2056.json"), "w"), indent=1)   # reproduces the report's figures exactly (checked 2026-11-20)
