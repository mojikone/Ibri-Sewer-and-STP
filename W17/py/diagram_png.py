"""Draw the transfer diagrams of the STP options as PNG, locally, from results/diagrams.json: the same layout, the same
boxes, arrows, labels and legend as the Figma code of diagram_js.py, for when Figma cannot be reached.

    python diagram_png.py            all options
    python diagram_png.py S2 S5      only these
Writes W17/report/img/W17_S#_transfer_diagram.png at twice the layout's pixel size (the Figma 2x export), font Calibri
(the report's body font). Every text is measured after drawing and checked against its box, the frame, the arrows'
vertical runs and every other text; the problems are printed, none expected.
"""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
SRC = os.path.join(W17, "results", "diagrams.json")
IMG = os.path.join(W17, "report", "img")
ZONE = {"O1": "#2E75B6", "O4": "#C0504D", "O9": "#70AD47", "O3": "#7030A0", "O16": "#ED7D31", "O22": "#00A6D6"}
RED, NAVY, GREY = "#A61B1B", "#1F3B63", "#5A5A5A"
PT = 0.72            # 1 layout px = 0.72 pt at 100 px per inch
FONT = "Calibri"


def draw(d):
    F = d["font"]; W = d["width"]
    pos = {n["id"]: n for n in d["nodes"]}
    plants = [n for n in d["nodes"] if n["kind"] == "plant"]
    H = d["height"] + 40                       # provisional; trimmed after the legend is laid out
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    texts, buses, issues = [], [], []

    def text(s, x, y, size, color=NAVY, bold=False, ha="left", va="top"):
        t = ax.text(x, y, s, fontsize=size * PT, color=color, fontweight="bold" if bold else "normal", family=FONT,
                    ha=ha, va=va, zorder=5)
        texts.append(t); return t

    def line(pts, col, w):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=w * PT, solid_joinstyle="miter",
                solid_capstyle="butt", zorder=2)

    def head(x, y, col, h):
        ax.add_patch(Polygon([(x - h, y - h / 2), (x, y), (x - h, y + h / 2)], closed=True, color=col, lw=0, zorder=3))

    entry = {}
    for n in d["nodes"]:
        kids = sorted([e for e in d["edges"] if e["dst"] == n["id"]], key=lambda e: pos[e["src"]]["y"])
        for i, e in enumerate(kids):
            entry[e["src"]] = n["y"] + n["h"] * (i + 1) / (len(kids) + 1) if n["kind"] == "plant" else n["y"] + n["h"] / 2
    labels = []
    for e in d["edges"]:
        a, b = pos[e["src"]], pos[e["dst"]]
        grav = e["kind"] == "gravity"; col = NAVY if grav else RED; w = 3 if grav else 2; hh = 15 if grav else 13
        x1, y1, x2, y2 = a["x"] + a["w"], a["y"] + a["h"] / 2, b["x"], entry[e["src"]]
        xm = x2 - 30
        line([(x1, y1), (xm, y1), (xm, y2), (x2 - hh + 1, y2)], col, w); head(x2, y2, col, hh)
        buses.append(xm)
        labels.append((text(e["label"], x1 + 8, y1 - 3, F["edge"], col, bold=grav, va="bottom"), xm))
    for n in d["nodes"]:
        c = ZONE.get(n["zone"], "#555555")
        if n["kind"] == "plant":
            ax.add_patch(FancyBboxPatch((n["x"], n["y"]), n["w"], n["h"], boxstyle="round,pad=0,rounding_size=6",
                                        fc=NAVY, ec="none", zorder=4))
            ax.add_patch(Rectangle((n["x"] + 3, n["y"]), n["w"] - 6, 6, fc=c, ec="none", zorder=4.5))
            cx = n["x"] + n["w"] / 2
            text(n["lines"][0], cx, n["y"] + 10, F["plant_title"], "#FFFFFF", bold=True, ha="center")
            text(n["lines"][1], cx, n["y"] + 36, F["plant"], "#C9D6EA", ha="center")
            for k, top in ((2, 56), (3, 76), (4, 96)):
                if len(n["lines"]) > k and n["lines"][k]:
                    text(n["lines"][k], cx, n["y"] + top, F["plant"], "#FFFFFF", ha="center")
        else:
            ax.add_patch(FancyBboxPatch((n["x"], n["y"]), n["w"], n["h"], boxstyle="round,pad=0,rounding_size=6",
                                        fc=matplotlib.colors.to_rgba(c, 0.14), ec=c, lw=1.6 * PT, zorder=4))
            text(n["lines"][0], n["x"] + n["w"] / 2, n["y"] + n["h"] / 2, F["name"], NAVY, bold=True, ha="center", va="center")
    # legend, left to right, wrapping when the row is full
    zc = ZONE.get(plants[0]["zone"], "#555555")
    items = [("box", "Subnetwork, named after its outfall" + (", coloured by its STP" if len(plants) > 1 else "")),
             ("pumped", "Pumping station at the outfall and its rising main, 2070 peak flow"),
             ("gravity", "Gravity: the STP sits at this subnetwork's own outfall"),
             ("plant", "STP: flows 2030 → 2070 and the depth of the incoming sewer")]
    fig.canvas.draw(); rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    def width_of(t):
        bb = t.get_window_extent(renderer=rend); (x0, _), (x1, _) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        return abs(x1 - x0)

    lx, ly, sw = 40, d["body"] + 10, 62
    for kind, s in items:
        t = text(s, 0, 0, F["legend"], GREY, va="center")
        fig.canvas.draw(); need = sw + 10 + width_of(t)
        if lx + need > W - 40:
            lx = 40; ly += 40
        cy = ly + 10
        if kind in ("box", "plant"):
            if kind == "plant":
                ax.add_patch(FancyBboxPatch((lx, cy - 14), sw, 28, boxstyle="round,pad=0,rounding_size=4", fc=NAVY, ec="none"))
            else:
                ax.add_patch(FancyBboxPatch((lx, cy - 14), sw, 28, boxstyle="round,pad=0,rounding_size=4",
                                            fc=matplotlib.colors.to_rgba(zc, 0.14), ec=zc, lw=1.6 * PT))
        else:
            col = NAVY if kind == "gravity" else RED; hh = 15 if kind == "gravity" else 13
            line([(lx, cy), (lx + sw - hh + 1, cy)], col, 3 if kind == "gravity" else 2); head(lx + sw, cy, col, hh)
        t.set_position((lx + sw + 10, cy)); lx += need + 44
    Hf = ly + 50
    fig.set_size_inches(W / 100, Hf / 100); ax.set_ylim(Hf, 0)
    # checks
    fig.canvas.draw(); rend = fig.canvas.get_renderer(); inv = ax.transData.inverted()
    boxes = []
    for t in texts:
        bb = t.get_window_extent(renderer=rend); (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        boxes.append((t, min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    for t, x0, y0, x1, y1 in boxes:
        if x0 < 0 or y0 < 0 or x1 > W + 0.5 or y1 > Hf + 0.5:
            issues.append(f"outside frame: {t.get_text()}")
    for n in d["nodes"]:
        for t, x0, y0, x1, y1 in boxes:
            if n["x"] <= (x0 + x1) / 2 <= n["x"] + n["w"] and n["y"] <= (y0 + y1) / 2 <= n["y"] + n["h"]:
                if x0 < n["x"] + 3 or x1 > n["x"] + n["w"] - 3 or y1 > n["y"] + n["h"] + 0.5:
                    issues.append(f"spills out of box {n['id']}: {t.get_text()}")
    for t, xm in labels:
        b = next(bx for bx in boxes if bx[0] is t)
        if b[3] > xm - 4:
            issues.append(f"label crosses the bus: {t.get_text()}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                issues.append(f"overlap: {a[0].get_text()!r} / {b[0].get_text()!r}")
    out = os.path.join(IMG, f"W17_{d['option']}_transfer_diagram.png")
    fig.savefig(out, dpi=200, facecolor="white"); plt.close(fig)
    print(f"{d['option']}: {out}  {W * 2} x {Hf * 2} px  issues: {issues or 'none'}")


if __name__ == "__main__":
    want = sys.argv[1:]
    for d in json.load(open(SRC, encoding="utf-8")):
        if not want or d["option"] in want:
            draw(d)
