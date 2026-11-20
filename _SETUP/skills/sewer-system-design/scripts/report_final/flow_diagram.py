"""Flow schematic of each final scenario in the form of the R7 transfer diagrams (engineer, 2026-11-19: "keep the same
as R7, later the team will check it"): one box per pumping system and lift catchment, named after its station and
coloured by the plant it drains to; a red arrow from each to the system that receives its pumped flow, or to the plant,
labelled with the design peak (L/s); the navy gravity arrow from the system whose outfall is the plant inlet; the plant
card with the 2031 and 2056 average inflow, the 2031 and 2056 peak at the inlet and the depth of the arriving sewer.
The layout rules are those of W17's diagram_layout.py (columns by steps to the plant, rows by depth-first order of the
leaves) and the drawing is W17's diagram_png.py itself, so the figure looks exactly as in R7.
Reads results/final_0.75pc_SC1-SC4/<SC>-2056/products/stations.csv, named/nodes.csv, quantities.json and financial.json.
    python flow_diagram.py          writes img/flow_diagram_SC#_2051/2056/2061.png, one per design"""
import collections, json, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W18, "py"))
import diagram_png as DP

R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); IMG = os.path.join(HERE, "img")
FIN = json.load(open(os.path.join(R, "financial.json")))
DP.ZONE = {"STP-1": "#1F6FB2", "STP-2": "#D9730D", "STP-5": "#2E8B57"}         # the plant colours of the maps
BOX_W, BOX_H, PLANT_W, PLANT_H = 128, 50, 280, 120                              # as W17 diagram_layout.py
COL, ROW, TREE_GAP, MARGIN, LEGEND_H = 260, 62, 40, 40, 110
FONT = dict(name=20, old=16, edge=17, plant_title=19, plant=16, legend=16)
TITLE = {"SC1": "Treatment at STP-1 only", "SC2": "Treatment at STP-2 only", "SC3": "Treatment at STP-1 and STP-5", "SC4": "Treatment at STP-2 and STP-5"}


def layout(sc, yr="2056"):
    st = pd.read_csv(os.path.join(R, f"{sc}-{yr}", "products", "stations.csv")); S = st.set_index("name")
    N = pd.read_csv(os.path.join(R, f"{sc}-{yr}", "named", "nodes.csv")).set_index("new")
    q = json.load(open(os.path.join(R, f"{sc}-{yr}", "products", "quantities.json")))
    stp_of = {pl: v["stp"] for pl, v in q["plants"].items()}
    parent, plant = {}, {}
    for r in st.itertuples():
        if r.kind == "plant inlet": parent[r.name] = "P:" + stp_of[r.name]
        elif str(r.pumps_to).startswith("STP at "): parent[r.name] = "P:" + stp_of[r.pumps_to.split("STP at ")[1]]
        else: parent[r.name] = N.at[r.pumps_to, "section"]
    for n in parent:
        m = n
        while not parent[m].startswith("P:"): m = parent[m]
        plant[n] = parent[m][2:]
    kids = collections.defaultdict(list)
    for c, p in parent.items(): kids[p].append(c)
    depth = {}

    def dep(n):
        if n.startswith("P:"): return 0
        if n not in depth: depth[n] = dep(parent[n]) + 1
        return depth[n]
    for n in parent: dep(n)
    maxd = max(depth.values())
    y_of, row = {}, [0.0]

    def place(n):
        ch = sorted(kids.get(n, []), key=lambda c: (-(len(kids.get(c, [])) > 0), -S.at[c, "duty_ls"]))
        if not ch: y_of[n] = row[0]; row[0] += 1
        else:
            for c in ch: place(c)
            y_of[n] = sum(y_of[c] for c in ch) / len(ch)
    plants = sorted(set(plant.values()), key=lambda z: -sum(1 for s in plant if plant[s] == z))
    for z in plants:
        place("P:" + z); row[0] += TREE_GAP / ROW
    nodes, edges = [], []
    for n, y in y_of.items():
        col = maxd - (0 if n.startswith("P:") else depth[n]); x = MARGIN + col * COL
        if n.startswith("P:"):
            z = n[2:]; inl = next(pl for pl, v in q["plants"].items() if v["stp"] == z); p = FIN["designs"][f"{sc}-{yr}"]["plants"][z]
            nodes.append(dict(id=n, kind="plant", zone=z, x=x, y=MARGIN + y * ROW - (PLANT_H - BOX_H) / 2, w=PLANT_W, h=PLANT_H,
                              lines=[z, f"2031 → {yr}", f"average {p['q']['2031']:,.0f} → {p['q'][yr]:,.0f} m³/d",
                                     f"peak {S.at[inl, 'q_2031_ls']:,.0f} → {S.at[inl, 'duty_ls']:,.0f} L/s",
                                     f"sewer arrives {q['plants'][inl]['inlet_depth_m']:.1f} m deep"]))
        else:
            nodes.append(dict(id=n, kind="sub", zone=plant[n], x=x, y=MARGIN + y * ROW, w=BOX_W, h=BOX_H, lines=[n]))
    for c, p in parent.items():
        grav = S.at[c, "kind"] == "plant inlet"
        edges.append(dict(src=c, dst=p, kind="gravity" if grav else "pumped", label="gravity" if grav else f"{S.at[c, 'duty_ls']:,.0f} L/s"))
    width = MARGIN * 2 + maxd * COL + PLANT_W
    body = max(n["y"] + n["h"] for n in nodes) + 36
    legend = [("box", "Pumping system or lift catchment, named after its station" + (", coloured by its STP" if len(plants) > 1 else "")),
              ("pumped", f"Pumping or lift station and its rising main, {yr} design peak"),
              ("gravity", "Gravity: the STP inlet sits at this system's own outfall"),
              ("plant", f"STP: flows 2031 → {yr} and the depth of the incoming sewer")]
    return dict(option=f"{sc}-{yr}", title=TITLE[sc], width=width, body=body, height=body + LEGEND_H, nodes=nodes, edges=edges, font=FONT,
                box=dict(w=BOX_W, h=BOX_H, col=COL), legend=legend, out=os.path.join(IMG, f"flow_diagram_{sc}_{yr}.png"))


if __name__ == "__main__":
    for sc in (sys.argv[1:] or ["SC1", "SC2", "SC3", "SC4"]):
        for yr in ("2051", "2056", "2061"): DP.draw(layout(sc, yr))          # one per design: the peaks change with the year
