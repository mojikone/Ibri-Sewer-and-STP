"""Compose the free-meter zoom panels (img/panels/panel_NN.png, rendered in QGIS by
qgis_maps_basis.render_panels) into A4 landscape pages of nine, each panel titled with
its number, settlement and meter count, with a scale bar read from the panel's width.

    python compose_panels.py        writes img/B06_panels_pNN.png
"""
import glob
import os

import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
PANELS = os.path.join(IMG, "panels")
SHP = os.path.join(HERE, "shp", "free_meter_panels.shp")

DPI = 200
PAGE_W, PAGE_H = int(297 / 25.4 * DPI), int(210 / 25.4 * DPI)     # A4 landscape
COLS, ROWS = 3, 3
MARGIN, GAP, TITLE_H = 40, 26, 40
NAVY = (31, 73, 125); GREY = (90, 90, 90); RED = (192, 80, 77); BLUE = (79, 129, 189)


def _font(size, bold=False):
    for name in (("calibrib.ttf" if bold else "calibri.ttf"), ("arialbd.ttf" if bold else "arial.ttf")):
        for d in (r"C:\Windows\Fonts", "/usr/share/fonts/truetype/msttcorefonts"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def build(keep=None, name="B06_panels_p%02d.png"):
    """keep: panel numbers to compose (all when None); name: the page file pattern."""
    panels = gpd.read_file(SHP).sort_values("PANEL")
    if keep:
        panels = panels[panels.PANEL.isin(keep)]
    per_page = COLS * ROWS
    cell_w = (PAGE_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
    cell_h = (PAGE_H - 2 * MARGIN - 34 - (ROWS - 1) * GAP) // ROWS       # 34 px for the page footer
    img_w = cell_w; img_h = cell_h - TITLE_H
    f_title, f_small, f_foot = _font(24, True), _font(20), _font(20)
    n_total = len(panels); pages = []
    rows = list(panels.itertuples())
    for p0 in range(0, n_total, per_page):
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        dr = ImageDraw.Draw(page)
        chunk = rows[p0:p0 + per_page]
        for i, r in enumerate(chunk):
            c, rw = i % COLS, i // COLS
            x0 = MARGIN + c * (cell_w + GAP); y0 = MARGIN + rw * (cell_h + GAP)
            src = os.path.join(PANELS, "panel_%02d.png" % r.PANEL)
            if not os.path.exists(src):
                dr.text((x0, y0), f"panel {r.PANEL}: not rendered", fill=RED, font=f_title); continue
            im = Image.open(src).convert("RGB")
            im = im.resize((img_w, img_h), Image.LANCZOS)
            page.paste(im, (x0, y0 + TITLE_H))
            dr.rectangle([x0, y0 + TITLE_H, x0 + img_w - 1, y0 + TITLE_H + img_h - 1], outline=(120, 120, 120), width=2)
            dwell = f", {r.N_DWELL} domestic" if r.N_DWELL else ""
            dr.text((x0 + 2, y0 + 6), f"Panel {r.PANEL}   {r.SETTLE}   {r.N} meter{'s' if r.N != 1 else ''}{dwell}", fill=NAVY, font=f_title)
            # a scale bar: the panel is WIDTH_M metres across img_w pixels
            px_per_m = img_w / float(r.WIDTH_M)
            bar_m = 200 if r.WIDTH_M >= 900 else 100
            bx, by = x0 + 14, y0 + TITLE_H + img_h - 22
            dr.rectangle([bx - 6, by - 26, bx + bar_m * px_per_m + 62, by + 8], fill=(255, 255, 255))
            dr.rectangle([bx, by - 6, bx + bar_m * px_per_m, by], fill=(40, 40, 40))
            dr.text((bx + bar_m * px_per_m + 8, by - 22), f"{bar_m} m", fill=(40, 40, 40), font=f_small)
        first, last = chunk[0].PANEL, chunk[-1].PANEL
        dr.ellipse([MARGIN, PAGE_H - MARGIN - 20, MARGIN + 16, PAGE_H - MARGIN - 4], fill=RED)
        dr.text((MARGIN + 24, PAGE_H - MARGIN - 24), "domestic meter", fill=GREY, font=f_foot)
        dr.ellipse([MARGIN + 220, PAGE_H - MARGIN - 20, MARGIN + 236, PAGE_H - MARGIN - 4], fill=BLUE)
        dr.text((MARGIN + 244, PAGE_H - MARGIN - 24), "other meter (shop, government, farm)   ·   plots outlined in yellow   ·   no plot within 15 m of any meter shown", fill=GREY, font=f_foot)
        tag = f"Panels {first} to {last} of {n_total}" if not keep else f"{len(chunk)} examples of the 126 meters"
        dr.text((PAGE_W - MARGIN - 300, PAGE_H - MARGIN - 24), tag, fill=NAVY, font=f_foot)
        out = os.path.join(IMG, name % (p0 // per_page + 1) if "%" in name else name)
        page.save(out, dpi=(DPI, DPI)); pages.append((out, first, last))
        print("   ", os.path.basename(out), first, "to", last)
    return pages


EXAMPLES = (1, 3, 15, 16, 17, 21, 26, 28, 42)     # the engineer's nine, 2026-09-14

if __name__ == "__main__":
    build(keep=EXAMPLES, name="B06_examples.png")
