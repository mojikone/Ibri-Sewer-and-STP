"""W18 final design: the SewerGEMS model of a case (build_final, jobs 080 on) against the own design, pipe by pipe, by
the new labels: flows at the design year, velocity at the 2031 peak, depth of flow against the limit (0.65 to DN355,
0.50 above), and the pipes SewerGEMS flags. Writes results/final_0.75pc_SC1-SC4/<case>/sewergems/COMPARE.md.
Usage: python final_sg_compare.py SC1-2056"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
CASE = sys.argv[1]; R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4", CASE)
SG = rf"D:\VBOX\bridge\out\w18\final\{CASE}"
own = pd.read_csv(os.path.join(R, "named", "links.csv")).set_index("new")
q_own = pd.read_csv(os.path.join(R, "exports", f"conduits_{CASE}a.csv")).set_index("label").flow_m3d
own["q_own"] = own.old.map(q_own)
sg = pd.read_csv(os.path.join(SG, f"conduits_{CASE}.csv")); sg = sg[sg.active == True].set_index("label")
s31 = pd.read_csv(os.path.join(SG, f"conduits_{CASE}-at-2031.csv")); s31 = s31[s31.active == True].set_index("label")
j = own.join(sg[["flow_m3d", "velocity_ms", "depth_in_m", "depth_out_m", "diameter_mm"]], how="inner").join(s31[["velocity_ms"]].rename(columns={"velocity_ms": "v31_sg"}))
j["dq"] = (j.flow_m3d - j.q_own) / j.q_own * 100
j["dD"] = j[["depth_in_m", "depth_out_m"]].max(axis=1) / (j.diameter_mm / 1000); j["lim"] = np.where(j.dn_mm <= 355, 0.65, 0.50)
big = j[j.dn_mm > 200]
L = [f"# {CASE}: SewerGEMS model against the own design", "",
     f"- Pipes compared by label: {len(j):,} of {len(own):,} (model: {len(sg):,} active conduits, the 5 lift stubs and the force mains are not in the own network).",
     f"- Design-year flow, model minus own: within 0.1 % on {(j.dq.abs() < 0.1).mean() * 100:.1f} % of pipes, within 1 % on {(j.dq.abs() < 1).mean() * 100:.1f} %; "
     f"largest {j.dq.abs().max():.1f} % ({j.dq.abs().idxmax()}); below the gravity joins the model re-peaks the joined flow, so it is lower there "
     f"(median of the pipes more than 1 % off: {j.dq[j.dq.abs() >= 1].median():+.1f} %).",
     f"- Depth of flow over the limit (0.65 to DN355, 0.50 above) at the design year: {(j.dD > j.lim + 0.005).sum()} pipes, "
     f"{j.length_m[j.dD > j.lim + 0.005].sum() / 1000:.2f} km; largest d/D {j.dD.max():.2f} ({j.dD.idxmax()}, DN{int(j.dn_mm[j.dD.idxmax()])}).",
     f"- Above DN200, velocity at the 2031 peak, model minus own: median {(big.v31_sg - big.v2031_ms).median():+.3f} m/s, 5-95 % "
     f"{(big.v31_sg - big.v2031_ms).quantile(.05):+.3f} to {(big.v31_sg - big.v2031_ms).quantile(.95):+.3f}; under 0.75 m/s at two decimals: model "
     f"{big.length_m[big.v31_sg.round(2) < 0.75].sum() / 1000:.1f} km, own {big.length_m[big.v2031_ms.round(2) < 0.75].sum() / 1000:.1f} km "
     f"(the steepened pipes are laid to reach 0.75 m/s exactly; the model gives 0.749-0.750 on "
     f"{((big.v31_sg < 0.75) & (big.v31_sg.round(2) >= 0.75)).sum()} of them).",
     f"- Highest velocity at the design year: model {j.velocity_ms.max():.2f} m/s ({j.velocity_ms.idxmax()})."]
over = j[j.dD > j.lim + 0.005].sort_values("dD", ascending=False).head(10)
if len(over): L += ["", "Pipes over the depth-of-flow limit (largest 10): " + ", ".join(f"{k} DN{int(r.dn_mm)} d/D {r.dD:.2f} (own flow {r.q_own / 86.4:.1f}, model {r.flow_m3d / 86.4:.1f} L/s)" for k, r in over.iterrows())]
extra = sg[~sg.index.isin(own.index)]
L += ["", "Model conduits not in the own network: " + ", ".join(f"{k} DN{str(r.size_label).split()[0]} v {r.velocity_ms:.2f} m/s, d/D {max(r.depth_in_m, r.depth_out_m) / (r.diameter_mm / 1000):.2f}" for k, r in extra.iterrows())]
os.makedirs(os.path.join(R, "sewergems"), exist_ok=True)
open(os.path.join(R, "sewergems", "COMPARE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
