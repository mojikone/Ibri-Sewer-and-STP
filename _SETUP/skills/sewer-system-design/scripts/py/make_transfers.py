"""Write the transfer rows of one option (all years) for the SewerGEMS job, and print the plant inflows."""
import sys, csv, os
from routing import SCENARIOS, routing, plant_of, transfers, node_maps, OLD
# W18: python make_transfers.py SC1 2056 2031  (the design year first, then the check years)
name, YEARS = sys.argv[1], sys.argv[2:]
tag = f"{name}-{YEARS[0]}"
_, new2id = node_maps()
out = rf"D:\VBOX\bridge\out\w18\scen\{tag}"; os.makedirs(out, exist_ok=True)
tr, joins, stp = routing(name)
plant = plant_of(name)
with open(rf"{out}\transfers_{tag}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["year", "source", "receiver_id", "receiver_label", "flow_m3d"])
    for y in YEARS:
        rows, total = transfers(name, y)
        for year, s, mh, r, q in rows:
            w.writerow([year, s, new2id[mh], mh, f"{q:.6f}"])
print(f"{name}: {SCENARIOS[name]['text']}; {len(tr)} transfers, plant joins {joins}")
print(f"{'year':5s}" + "".join(f"{'STP '+z+' ('+OLD[z]+')':>18s}" for z in sorted(stp, key=lambda s: int(s[1:]))) + "   peak inflow, L/s")
for y in YEARS:
    rows, total = transfers(name, y)
    inflow = {z: 0.0 for z in stp}
    for s in total:
        if s in stp: inflow[s] += total[s]
    for s, z in joins.items(): inflow[z] += total[s]
    print(f"{y:5s}" + "".join(f"{inflow[z]/86.4:18.1f}" for z in sorted(stp, key=lambda s: int(s[1:]))))
print(f"transfers {YEARS[0]} (source -> receiving manhole: L/s):")
rows, total = transfers(name, YEARS[0])
print("  " + "; ".join(f"{s} ({OLD[s]}) -> {mh}: {q/86.4:.1f}" for _, s, mh, r, q in rows))
