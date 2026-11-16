"""In which year can every pipe reach 0.75 m/s at its peak flow (G203 p26), if pipes may be laid as steep as the
client's 4 % maximum? For information; the self-cleansing audit itself waits for the client's decision.

For each pipe and year: the gradient at which that year's peak flow reaches 0.75 m/s in the pipe's own diameter
(Colebrook-White, ks 1.5 mm, nu 1.141e-6 m2/s, G203 p24-p25). A pipe is "self-cleansing within 4 %" in a year if that
gradient is 4 % or less (or its laid gradient already gives 0.75 m/s). Its first such year is its self-cleansing year.
Flows: S1 runs (local pipe flows are the same in every option; only the trunks that receive transfers differ).
"""
import csv, math, collections, json
import numpy as np
from selfcleansing_info import rows, slope_for, velocity, TAGS

YEARS = [y for y, _ in TAGS]
CAP = 0.04
first, res = {}, collections.defaultdict(lambda: collections.Counter())
for lab, d in rows.items():
    fy = None
    for y in YEARS:
        q = d["q"].get(y, 0.0)
        laid_ok = d["S"] > 0 and velocity(q, d["D"], d["S"]) >= 0.75
        s = slope_for(q, d["D"])
        ok = laid_ok or (s is not None and s <= CAP)
        if ok and fy is None:
            fy = y
    first[lab] = fy or "never by 2070"

n = len(rows); L = sum(d["L"] for d in rows.values())
cum_n, cum_L = 0, 0.0
print("Pipes that can carry their peak at 0.75 m/s with a gradient of 4 % or less, by year (cumulative)")
print("| year | pipes | share | length km | share of length | head pipes |")
print("|---|---|---|---|---|---|")
heads = {l for l, d in rows.items() if d["head"]}
OUT = dict(pipes=n, km=round(L / 1000, 1), head_pipes=len(heads), years={})
for y in YEARS:
    sel = [l for l, f in first.items() if f != "never by 2070" and YEARS.index(f) <= YEARS.index(y)]
    ln = sum(rows[l]["L"] for l in sel)
    print(f"| {y} | {len(sel):,} | {100*len(sel)/n:.1f} % | {ln/1000:,.0f} | {100*ln/L:.1f} % | {sum(1 for l in sel if l in heads):,} of {len(heads):,} |")
    OUT["years"][y] = dict(pipes=len(sel), share=round(len(sel) / n, 4), km=round(ln / 1000, 1),
                           share_length=round(ln / L, 4), head_pipes=sum(1 for l in sel if l in heads))
never = [l for l, f in first.items() if f == "never by 2070"]
print(f"\nNever within 4 % by 2070: {len(never):,} pipes ({100*len(never)/n:.1f} %), {sum(rows[l]['L'] for l in never)/1000:,.0f} km; "
      f"head pipes among them: {sum(1 for l in never if l in heads):,}")
q70 = np.array([rows[l]["q"]["2070"] * 1000 for l in never])
print(f"  their 2070 peak flow: median {np.median(q70):.2f} L/s, 90 % below {np.percentile(q70, 90):.2f} L/s")
sizes = collections.Counter(round(rows[l]["D"] * 1000, 1) for l in never)
print("  by inside diameter (mm):", ", ".join(f"{k}: {v:,}" for k, v in sizes.most_common(6)))

# how many houses does a DN200 head pipe need? (peak 0.93 L/s at 4 %; Peltier PF = 1.5 + 1/sqrt(Qavg L/s), G1-p72)
q_need = 0.93
lo, hi = 0.01, 5.0
for _ in range(60):
    m = (lo + hi) / 2
    if m * (1.5 + 1 / math.sqrt(m)) < q_need: lo = m
    else: hi = m
house = 0.85 * 164 * 5.32 / 86400          # L/s per domestic property at the average occupancy (W14 rule, OR 5.32)
print(f"\nA DN200 needs {q_need} L/s of peak flow to reach 0.75 m/s at 4 %: an average flow of {hi:.2f} L/s by Peltier,"
      f" about {hi/house:.0f} houses at the average occupancy")
OUT.update(never=dict(pipes=len(never), share=round(len(never) / n, 4), km=round(sum(rows[l]["L"] for l in never) / 1000, 1),
                      head_pipes=sum(1 for l in never if l in heads), median_q2070_ls=round(float(np.median(q70)), 2),
                      sizes_mm=sorted(sizes)),
           dn200_q_need_ls=q_need, dn200_avg_need_ls=round(hi, 2), houses=round(hi / house))
json.dump(OUT, open(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results\S1\selfcleansing_year.json", "w", encoding="utf-8"), indent=1)

with open(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results\S1\selfcleansing_year_by_pipe.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["label", "inside_diameter_mm", "length_m", "head_pipe", "first_year_within_4pc"])
    for l, d in rows.items():
        w.writerow([l, round(d["D"] * 1000, 1), round(d["L"], 1), d["head"], first[l]])
