"""W18 final design (engineer, 2026-11-18): self-cleansing of every scenario and design year at 0.75 % - pipes above
DN200 at 0.75 m/s at the 2031 peak (the rule), and, for those that do not reach it, the 2036 peak ("check for 2036 flow
at each scenario to see if the remaining pipes self clean"). Velocity: Colebrook-White at normal depth on the laid
(steepened) gradient, as the split uses. Writes results/final_0.75pc_SC1-SC4/selfcleansing.csv and .md, and per case
<case>/selfcleansing_pipes.csv (every pipe above DN200 that misses 0.75 m/s in 2031, with its 2036 velocity)."""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
sys.argv = [sys.argv[0], "SC1", "2056"]                    # final_design's rules, without re-running its design
G, NU, KS = 9.81, 1.141e-6, 1.5e-3
import math


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


rows, md = [], ["| case | above DN200 | under 0.75 m/s at 2031 | of these, still under at 2036 | pumping stations (new) |", "|---|---|---|---|---|"]
for s in ("SC1", "SC2", "SC3", "SC4"):
    for y in ("2051", "2056", "2061"):
        t = f"{s}-{y}"; P = pd.read_csv(os.path.join(R, t, "split", f"pipes_{t}.csv")); S = json.load(open(os.path.join(R, t, "split", f"summary_{t}.json")))
        q36 = pd.read_csv(os.path.join(R, t, "exports", f"conduits_{t}-at-2036.csv")).set_index("label")
        dia = q36.diameter_mm / 1000.0
        big = P[(P.kind == "pipe") & (P.dn_mm > 200)].copy(); u = big[big.under075 == 1].copy()
        u["q2036_ls"] = q36.flow_m3d.reindex(u.label).values / 86.4
        u["v2036_ms"] = [velocity(q / 1000, d, sl / 100) for q, d, sl in zip(u.q2036_ls, dia.reindex(u.label).values, u.s_new_pc)]
        u36 = u[u.v2036_ms < 0.75]
        u[["label", "sub", "dn_mm", "length_m", "s_new_pc", "v2031_ms", "q2036_ls", "v2036_ms"]].to_csv(
            os.path.join(R, t, "selfcleansing_pipes.csv"), index=False, float_format="%.3f")
        r = dict(case=t, km_big=big.length_m.sum() / 1000, km_under_2031=u.length_m.sum() / 1000, n_under_2031=len(u),
                 km_under_2036=u36.length_m.sum() / 1000, n_under_2036=len(u36), stations=S["stations"], new=S["stations_new"])
        rows.append(r)
        md.append(f"| {t} | {r['km_big']:.1f} km | {r['km_under_2031']:.1f} km ({r['km_under_2031'] / r['km_big'] * 100:.1f} %), {r['n_under_2031']} pipes | "
                  f"{r['km_under_2036']:.1f} km ({r['km_under_2036'] / r['km_big'] * 100:.1f} %), {r['n_under_2036']} pipes | {r['stations']} ({r['new']}) |")
pd.DataFrame(rows).to_csv(os.path.join(R, "selfcleansing.csv"), index=False, float_format="%.2f")
open(os.path.join(R, "selfcleansing.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
