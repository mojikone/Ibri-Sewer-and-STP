"""Layout of the transfer diagram of every STP option, for Figma (drawn by explicit coordinates, no auto-layout).

Each option is a forest that ends in its plants: a subnetwork box, an arrow to the subnetwork that receives its pumped
flow (label: the 2070 peak, L/s), or to a plant ("pumped" when a rising main runs to the plant, "gravity" when the plant
sits at the subnetwork's own outfall). Columns count the steps to the plant, so every option reads left to right into
its plants. Plant averages = the plot loads of the zone + the network's infiltration (720 L/day/km), as in
scenario_results.py; peaks = the sum of the outfall peaks.
Output: W17/results/diagrams.json (read by the Figma drawing code).
"""
import csv, json, os, collections
from routing import SCENARIOS, YEARS, routing, plant_of, transfers, OLD

DIAG = r"D:\VBOX\bridge\out\r4\diag"
S1 = r"D:\VBOX\bridge\out\scen\S1"
OUT = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results\diagrams.json"
SUB = lambda lab: lab.split("-")[0] if lab.startswith("O") and ("-M" in lab or "-P" in lab) else None
BOX_W, BOX_H, PLANT_W, PLANT_H = 128, 50, 280, 100
COL, ROW, TREE_GAP, MARGIN, LEGEND_H = 260, 62, 40, 40, 110
# text sizes (px), read by diagram_js.py; legibility is checked on an A3 landscape page (380 x 235 mm of figure)
FONT = dict(name=20, old=16, edge=17, plant_title=19, plant=16, legend=16)
PAGE_MM = (380, 235)

base = {y: collections.defaultdict(float) for y in YEARS}
for y in YEARS:
    for r in csv.DictReader(open(rf"{DIAG}\rows_{y}.csv", encoding="utf-8")):
        s = SUB(r["label"])
        if s: base[y][s] += float(r["base_m3d"])
infil = collections.defaultdict(float)
for r in csv.DictReader(open(rf"{S1}\conduits_base2070_inputs.csv", encoding="utf-8")):
    s = SUB(r["label"])
    if s and r["active"] == "True": infil[s] += float(r["length_m"]) / 1000 * 0.72


def layout(name):
    tr, joins, stp = routing(name)
    plant = plant_of(name)
    _, q70 = transfers(name, "2070")
    _, q30 = transfers(name, "2030")
    parent = {s: r for s, _, r in tr}
    parent.update({s: "P:" + z for s, z in joins.items()})
    for z in stp:
        parent[z] = "P:" + z
    kids = collections.defaultdict(list)
    for c, p in parent.items():
        kids[p].append(c)
    depth = {}

    def dep(n):
        if n.startswith("P:"):
            return 0
        if n not in depth:
            depth[n] = dep(parent[n]) + 1
        return depth[n]

    for n in parent:
        dep(n)
    maxd = max(depth.values())
    nodes, edges, y_of = [], [], {}
    row = [0.0]

    def place(n):
        ch = sorted(kids.get(n, []), key=lambda c: (-(len(kids.get(c, [])) > 0), -q70.get(c, 0)))
        if not ch:
            y_of[n] = row[0]; row[0] += 1
        else:
            for c in ch:
                place(c)
            y_of[n] = sum(y_of[c] for c in ch) / len(ch)

    plants = sorted(stp, key=lambda z: -(sum(1 for s in plant if plant[s] == z)))
    for z in plants:
        place("P:" + z)
        row[0] += TREE_GAP / ROW
    for n, y in y_of.items():
        col = maxd - (0 if n.startswith("P:") else depth[n])
        x = MARGIN + col * COL
        if n.startswith("P:"):
            z = n[2:]
            avg = [sum(base[yy][s] + infil[s] for s in plant if plant[s] == z) for yy in ("2030", "2070")]
            pk = [(transfers(name, yy)[1][z] + sum(transfers(name, yy)[1][s] for s, t in joins.items() if t == z)) / 86.4 for yy in ("2030", "2070")]
            nodes.append(dict(id=n, kind="plant", zone=z, x=x, y=MARGIN + y * ROW - (PLANT_H - BOX_H) / 2, w=PLANT_W, h=PLANT_H,
                              lines=[f"STP at {z} ({OLD[z]})", "2030 → 2070",
                                     f"average {avg[0]:,.0f} → {avg[1]:,.0f} m³/d", f"peak {pk[0]:,.0f} → {pk[1]:,.0f} L/s"]))
        else:
            nodes.append(dict(id=n, kind="sub", zone=plant[n], x=x, y=MARGIN + y * ROW, w=BOX_W, h=BOX_H,
                              lines=[n, f"({OLD[n]})"]))
    for c, p in parent.items():
        # every outfall is a pumping station whose rising main ends at the receiving subnetwork or at the plant,
        # except the subnetwork whose own outfall is the plant (gravity)
        grav = p.startswith("P:") and c == p[2:]
        edges.append(dict(src=c, dst=p, kind="gravity" if grav else "pumped",
                          label="gravity" if grav else f"{q70[c] / 86.4:,.0f} L/s"))
    width = MARGIN * 2 + maxd * COL + PLANT_W
    body = max(n["y"] + n["h"] for n in nodes) + 36
    return dict(option=name, title=SCENARIOS[name]["text"], width=width, body=body, height=body + LEGEND_H,
                nodes=nodes, edges=edges, font=FONT, box=dict(w=BOX_W, h=BOX_H, col=COL))


def a3_check(d):
    """Scale of the figure fitted to the A3 landscape figure area, and the smallest text in points at that scale."""
    s = min(PAGE_MM[0] / d["width"], PAGE_MM[1] / d["height"])  # mm per px
    return s, min(d["font"].values()) * s / 0.3528


if __name__ == "__main__":
    out = [layout(n) for n in SCENARIOS]
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for d in out:
        s, pt = a3_check(d)
        print(f"{d['option']}: {len(d['nodes'])} boxes, {len(d['edges'])} arrows, {d['width']:.0f} x {d['height']:.0f} px "
              f"(aspect {d['width'] / d['height']:.2f}); on A3 {d['width'] * s:.0f} x {d['height'] * s:.0f} mm, "
              f"smallest text {pt:.1f} pt{'  <-- below 7 pt' if pt < 7 else ''}")
