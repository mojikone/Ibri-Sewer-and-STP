"""A small flowchart drawer with explicit layout.

Auto-layout tools choose the shape of the diagram for you, which is why they
produce figures six times wider than a page. Here the grid is stated, so every
figure is drawn to fit the text column and stays legible at print size.

Nodes sit on a column/row grid. Edges are routed orthogonally between anchor
points on the node edges.
"""
import math
import os
import textwrap

# document palette
INK = "#1F3B63"
MID = "#2E629E"
GREY = "#5A5A5A"
LINE = "#8A9BB0"
FILL = "#FFFFFF"
TINT = "#EAF1F8"
WARN = "#FFF4E5"
WARN_LINE = "#D9A441"

# A single family name, not a stack: the renderer matches the whole string as
# one name, so "Helvetica, Arial, sans-serif" matches nothing and falls back to
# a serif. "Helvetica", "Arial" and "sans-serif" each resolve correctly alone.
FONT = "Helvetica"


class Chart:
    def __init__(self, cols, rows, cw=250, rh=104, gx=44, gy=40,
                 pad=26, title=None):
        self.cols, self.rows = cols, rows
        self.cw, self.rh, self.gx, self.gy, self.pad = cw, rh, gx, gy, pad
        self.title = title
        self.title_h = 48 if title else 0
        self.nodes = {}
        self.edges = []
        self.notes = []

    # ------------------------------------------------------------- geometry
    @property
    def width(self):
        return self.pad * 2 + self.cols * self.cw + (self.cols - 1) * self.gx

    @property
    def height(self):
        return (self.pad * 2 + self.title_h + self.rows * self.rh
                + (self.rows - 1) * self.gy)

    def _x(self, col):
        return self.pad + col * (self.cw + self.gx)

    def _y(self, row):
        return self.pad + self.title_h + row * (self.rh + self.gy)

    # ---------------------------------------------------------------- build
    def node(self, key, col, row, text, kind="plain", span=1, height=1):
        self.nodes[key] = dict(col=col, row=row, text=text, kind=kind,
                               span=span, height=height)
        return key

    def edge(self, a, b, label=None, side=None):
        self.edges.append((a, b, label, side))

    def note(self, col, row, text, span=2):
        self.notes.append((col, row, text, span))

    # ---------------------------------------------------------------- boxes
    def _box(self, key):
        n = self.nodes[key]
        x = self._x(n["col"])
        y = self._y(n["row"])
        w = n["span"] * self.cw + (n["span"] - 1) * self.gx
        h = n["height"] * self.rh + (n["height"] - 1) * self.gy
        return x, y, w, h

    def _anchor(self, key, where):
        x, y, w, h = self._box(key)
        return {"t": (x + w / 2, y), "b": (x + w / 2, y + h),
                "l": (x, y + h / 2), "r": (x + w, y + h / 2)}[where]

    # ----------------------------------------------------------------- draw
    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
               f'height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
               f'font-family="{FONT}">',
               f'<rect width="{self.width}" height="{self.height}" fill="#FFFFFF"/>',
               ]

        if self.title:
            out.append(
                f'<text x="{self.pad}" y="{self.pad + 26}" '
                f'font-family="{FONT}" font-size="27" '
                f'font-weight="600" fill="{INK}">{_esc(self.title)}</text>')

        for a, b, label, side in self.edges:
            out.append(self._edge_svg(a, b, label, side))

        for key in self.nodes:
            out.append(self._node_svg(key))

        for col, row, text, span in self.notes:
            x, y = self._x(col), self._y(row)
            w = span * self.cw + (span - 1) * self.gx
            out.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{self.rh}" rx="6" '
                f'fill="{WARN}" stroke="{WARN_LINE}" stroke-width="1.4"/>')
            out.append(_wrapped(text, x + w / 2, y + self.rh / 2, w - 26,
                                18.5, "#7A5200", weight="400"))

        out.append("</svg>")
        return "\n".join(out)

    def _node_svg(self, key):
        n = self.nodes[key]
        x, y, w, h = self._box(key)
        kind = n["kind"]
        fill, stroke, colour, weight, size = FILL, LINE, "#1A1A1A", "400", 20.5
        if kind == "accent":
            fill, stroke, colour, weight = INK, INK, "#FFFFFF", "600"
        elif kind == "tint":
            fill, stroke = TINT, MID
        elif kind == "start":
            stroke, weight, colour = MID, "600", INK
        elif kind == "warn":
            fill, stroke, colour = WARN, WARN_LINE, "#7A5416"

        rx = h / 2 if kind == "pill" else 9
        if kind == "pill":
            fill, stroke, weight = TINT, MID, "600"

        s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
             f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>']
        s.append(_wrapped(n["text"], x + w / 2, y + h / 2, w - 28, size,
                          colour, weight=weight))
        return "".join(s)

    def _edge_svg(self, a, b, label, side):
        na, nb = self.nodes[a], self.nodes[b]
        if side:
            sa, sb = side
        elif nb["row"] > na["row"]:
            sa, sb = "b", "t"
        elif nb["row"] < na["row"]:
            sa, sb = "t", "b"
        elif nb["col"] > na["col"]:
            sa, sb = "r", "l"
        else:
            sa, sb = "l", "r"

        x1, y1 = self._anchor(a, sa)
        x2, y2 = self._anchor(b, sb)

        if sa in "tb" and sb in "tb" and abs(x1 - x2) > 2:
            my = (y1 + y2) / 2
            pts = [(x1, y1), (x1, my), (x2, my), (x2, y2)]
        elif sa in "lr" and sb in "lr" and abs(y1 - y2) > 2:
            mx = (x1 + x2) / 2
            pts = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
        else:
            pts = [(x1, y1), (x2, y2)]

        # stop the line short so it meets the base of the arrowhead
        head = 11.0
        (px, py), (qx, qy) = pts[-2], pts[-1]
        seg = math.hypot(qx - px, qy - py) or 1.0
        ux, uy = (qx - px) / seg, (qy - py) / seg
        pts[-1] = (qx - ux * head, qy - uy * head)

        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out = (f'<path d="{d}" fill="none" stroke="{LINE}" '
               f'stroke-width="1.8" stroke-linejoin="round"/>')
        out += _arrowhead(qx, qy, ux, uy, head)
        if label:
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
            tw = len(label) * 9.4 + 14
            out += (f'<rect x="{lx - tw/2}" y="{ly - 13}" width="{tw}" '
                    f'height="26" rx="4" fill="#FFFFFF" opacity="0.95"/>'
                    f'<text x="{lx}" y="{ly + 6}" font-family="{FONT}" '
                    f'font-size="17" fill="{GREY}" '
                    f'text-anchor="middle">{_esc(label)}</text>')
        return out


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _wrapped(text, cx, cy, maxw, size, colour, weight="400"):
    chars = max(8, int(maxw / (size * 0.48)))
    lines = []
    for para in str(text).split("|"):
        lines.extend(textwrap.wrap(para, chars) or [""])
    lh = size * 1.25
    y0 = cy - (len(lines) - 1) * lh / 2 + size * 0.35
    out = ""
    for i, ln in enumerate(lines):
        out += (f'<text x="{cx}" y="{y0 + i * lh}" font-family="{FONT}" '
                f'font-size="{size}" font-weight="{weight}" fill="{colour}" '
                f'text-anchor="middle">{_esc(ln)}</text>')
    return out


# ------------------------------------------------------------------ render
def render(chart, name, outdir, dpi=200, max_aspect=2.6, min_aspect=0.55):
    os.makedirs(outdir, exist_ok=True)
    svg_path = os.path.join(outdir, name + ".svg")
    png_path = os.path.join(outdir, name + ".png")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(chart.svg())

    import fitz
    doc = fitz.open(svg_path)
    pdf = fitz.open("pdf", doc.convert_to_pdf())
    pix = pdf[0].get_pixmap(dpi=dpi)
    pix.save(png_path)

    aspect = pix.width / pix.height
    if aspect > max_aspect:
        verdict = "TOO WIDE"
    elif aspect < min_aspect:
        verdict = "TOO TALL"
    else:
        verdict = "ok"
    print(f"{name:26s} {pix.width:5d} x {pix.height:5d}  "
          f"aspect {aspect:5.2f}  {verdict}")
    return png_path, aspect


def _arrowhead(x, y, ux, uy, size):
    """Solid triangle at (x, y) pointing along the unit vector (ux, uy)."""
    bx, by = x - ux * size, y - uy * size
    px, py = -uy, ux
    w = size * 0.42
    return (f'<polygon points="{x:.1f},{y:.1f} '
            f'{bx + px * w:.1f},{by + py * w:.1f} '
            f'{bx - px * w:.1f},{by - py * w:.1f}" fill="{LINE}"/>')
