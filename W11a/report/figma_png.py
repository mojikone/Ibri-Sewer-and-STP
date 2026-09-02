"""Turn a Figma/FigJam diagram thumbnail into a report-ready PNG.

Why this exists. `generate_diagram` returns a THUMBNAIL URL that serves an SVG, and
`download_assets` refuses FigJam files, so there is no direct PNG route. python-docx cannot
place an SVG, so the report needs a raster. On this machine cairo is absent, which rules out
cairosvg and reportlab's renderPM backend; `@resvg/resvg-js` is a self-contained Rust
rasteriser with no system dependency and does the job.

It also enforces the thing that actually matters for a report figure: ASPECT RATIO. A mermaid
LR flowchart with a feedback edge came back at 4849 x 573 - an 8.5:1 strip that is unreadable
at A4 width. Anything wider than about 2.2:1 is flagged here rather than discovered on the
page, because the fix is to change the DIAGRAM, not to shrink the image.

    python figma_png.py FC02_ladder "<thumbnail url>"
"""
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")

# An A4 portrait text column is about 16.6 cm. Past this ratio a diagram either sets its own
# type too small to read or has to go on a landscape page of its own.
MAX_RATIO = 2.2
# And the other way. A full A4 portrait figure area is about 16.6 x 24 cm = 0.69:1, so
# anything much taller than that shrinks to fit the HEIGHT and wastes the width: FC04 came
# back at 0.30:1 and would have set 7 cm wide on the page. Guarding one direction only
# invited exactly this overcorrection.
# 0.40, not 0.55. A tall diagram whose nodes carry SHORT lines still sets large type at
# about 10 cm wide on a full page and reads perfectly; what fails is a tall diagram whose
# nodes wrap long lines, which is the real driver of height in FigJam. The ratio is a proxy
# for that, so the bound is set where it catches the bad case without rejecting the good one.
MIN_RATIO = 0.40

RASTER = r"""
const {Resvg} = require('@resvg/resvg-js');
const fs = require('fs');
// argv[2], not argv[1]. With `node script.js a b c` argv[1] is the SCRIPT - so this
// handed resvg its own JavaScript and it reported "unknown token at 2:1", which reads
// exactly like a corrupt SVG and sent me looking at encodings, BOMs and line endings.
// Read as a Buffer while we are here; resvg takes either.
const svg = fs.readFileSync(process.argv[2]);
const r = new Resvg(svg, {fitTo: {mode: 'width', value: parseInt(process.argv[4], 10)}});
fs.writeFileSync(process.argv[3], r.render().asPng());
"""


def fetch(url: str, name: str, width: int = 3200):
    os.makedirs(IMG, exist_ok=True)
    svg = os.path.join(IMG, name + ".svg")
    png = os.path.join(IMG, name + ".png")
    urllib.request.urlretrieve(url, svg)

    head = open(svg, encoding="utf-8").read(400)
    if not head.lstrip().startswith("<svg"):
        raise SystemExit(f"{name}: the URL did not serve an SVG - got {head[:80]!r}")

    js = os.path.join(HERE, "_raster.js")
    with open(js, "w", encoding="utf-8") as fh:
        fh.write(RASTER)
    subprocess.run(["node", js, svg, png, str(width)], check=True, cwd=HERE)
    os.remove(js)

    from PIL import Image
    with Image.open(png) as im:
        w, h = im.size
    ratio = w / max(h, 1)
    flag = ""
    if ratio > MAX_RATIO:
        flag = (f"   <-- {ratio:.2f}:1 is too WIDE for A4. Redraw TB, or group into "
                f"subgraphs. Do not shrink the image.")
    elif ratio < MIN_RATIO:
        flag = (f"   <-- {ratio:.2f}:1 is too TALL for A4; it would set about "
                f"{16.6 * ratio / 0.69:.0f} cm wide on a full page. Redraw with fewer, "
                f"denser nodes, or put detail inside a node instead of after it.")
    print(f"{name}: {w} x {h}  ratio {ratio:.2f}:1{flag}")
    return png, ratio


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    fetch(sys.argv[2], sys.argv[1],
          int(sys.argv[3]) if len(sys.argv) > 3 else 3200)
