# -*- coding: utf-8 -*-
"""Draw each group's name onto its own frame in a FigJam-exported SVG.

WHY THIS EXISTS
FigJam draws each group as a *section*, and a section carries its name on the small tab at
its top-left corner. Inside Figma you can see that name. But Figma treats a section name as
interface furniture rather than as something on the canvas, so **no export draws it** —
neither the PNG nor the SVG, and not the full-resolution render either (checked 20 Aug 2026
against a real render, not just the thumbnail). The tab comes out as an empty box.

Putting the title in a node inside the group is not the same thing: it sits in the flow and
reads as a step. So this script takes the name Figma already stores on the group and paints
it on the frame as a proper title bar, which is what a reader expects.

HOW
Each section is a top-level `<g id="NAME">` whose first child is the frame: a plain
rectangle path of the form `M x0 y0 H x1 V y1 H x0 V y0 Z`. The script reads those corners,
then inserts a filled bar with the name across the top edge of that frame.

Run it after downloading a fresh SVG from the Figma MCP:
    python add_group_titles.py <file.svg> [<file2.svg> ...]
It rewrites the file in place and reports what it titled.
"""

import io
import re
import sys

BAR_H = 52.0          # height of the title bar
PAD_X = 22.0          # text inset from the left edge of the frame
FONT = 26.0
CHAR_W = 0.60         # rough width per character at that size, for the bar width

# a section whose name starts with one of these gets the warning colour
WARN = ("THE 12 m TEST", "WHERE THE REMAINING GAIN")
NAVY, DARKRED, TEXT = "#1F3864", "#7B2D26", "#FFFFFF"

FRAME = re.compile(
    r'M(-?[\d.]+) (-?[\d.]+)H(-?[\d.]+)V(-?[\d.]+)H(-?[\d.]+)V(-?[\d.]+)Z')
GROUP = re.compile(r'<g id="([^"]+)">\n<path d="(M[^"]+Z)" fill="white"/>')


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def title_svg(name, x0, y0, x1):
    w = min(len(name) * FONT * CHAR_W + 2 * PAD_X, (x1 - x0) - 8)
    fill = DARKRED if name.startswith(WARN) else NAVY
    return (
        f'<g id="group-title">'
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{BAR_H:.1f}" '
        f'rx="8" fill="{fill}"/>'
        f'<text x="{x0 + PAD_X:.1f}" y="{y0 + BAR_H * 0.68:.1f}" fill="{TEXT}" '
        f'font-family="Inter, Segoe UI, Arial, sans-serif" font-size="{FONT:.0f}" '
        f'font-weight="700" letter-spacing="0.6">{esc(name)}</text>'
        f'</g>\n')


def process(path):
    src = io.open(path, encoding="utf-8").read()
    done, out, pos = [], [], 0
    for m in GROUP.finditer(src):
        name, d = m.group(1), m.group(2)
        f = FRAME.match(d)
        if not f:
            continue
        x0, y0, x1 = float(f.group(1)), float(f.group(2)), float(f.group(3))
        if (x1 - x0) < 200:                     # not a section frame, just a shape
            continue
        out.append(src[pos:m.end()])
        out.append("\n" + title_svg(name, x0, y0, x1))
        pos = m.end()
        done.append(name)
    out.append(src[pos:])
    if done:
        io.open(path, "w", encoding="utf-8").write("".join(out))
    return done


if __name__ == "__main__":
    for p in sys.argv[1:]:
        named = process(p)
        print(f"{p}: titled {len(named)} groups")
        for n in named:
            print(f"    {n}")
