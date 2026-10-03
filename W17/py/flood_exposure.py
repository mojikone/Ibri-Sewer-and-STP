"""Flood exposure of the gravity sewers and the manholes, for Section 7.2 of the Concept Design Report.

The pipes and the manholes lie in the same streets in every option (Section 6.2.6), so one assessment serves all
seven; the script checks that before it counts. Each pipe is sampled every metre or less along its length and each
manhole at its centre, on the four flood hazard grids of the Oman Flood Mapping project (MAFWR) for the 10, 25, 50 and
100-year floods. The grids carry the six hazard classes of AIDR Guideline 7-3 (2017), H1 to H6; a cell outside the
flood extent carries no data and counts as not flooded. The treatment plants, the pumping stations and the rising mains
are assessed once their sites are fixed (engineer, 2026-10-03).

    python flood_exposure.py          writes W17/results/flood_exposure.json
"""
import json
import math
import os

import fiona
import numpy as np
import rasterio
import shapely
from rasterio.windows import Window
from shapely.geometry import shape

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
GPKG = os.path.join(W17, "Options 2026-10", "11_Network_options", "{o}.gpkg")
HAZARD = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(W17))), "Data", "04 Lekhuwair", "Hazard_T{T}y.tif")
OUT = os.path.join(W17, "results", "flood_exposure.json")
OPTIONS = [f"S{i}" for i in range(1, 8)]
PERIODS = (10, 25, 50, 100)
STEP = 1.0              # m between samples along a pipe; the grids are 2 and 3 m
BAND = 2000             # raster rows read at a time
CLASSES = ["none", "H1", "H2", "H3", "H4", "H5", "H6"]


def _read(o, layer):
    with fiona.open(GPKG.format(o=o), layer=layer) as c:
        return [(f["properties"]["label"], shape(f["geometry"])) for f in c]


def _same_everywhere():
    """The pipes and the manholes of every option are the same: same labels, same places."""
    ref_p = {k: g.wkb for k, g in _read("S1", "pipes")}
    ref_m = {k: (round(g.x, 3), round(g.y, 3)) for k, g in _read("S1", "manholes")}
    for o in OPTIONS[1:]:
        p = {k: g.wkb for k, g in _read(o, "pipes")}
        m = {k: (round(g.x, 3), round(g.y, 3)) for k, g in _read(o, "manholes")}
        assert p == ref_p and m == ref_m, f"{o}: the pipes or the manholes differ from S1"


def _sample(path, x, y):
    """The grid value under each point; 0 where the grid has no data (outside the flood extent)."""
    out = np.zeros(len(x), dtype=np.int8)
    with rasterio.open(path) as r:
        inv = ~r.transform
        col, row = inv * (x, y)
        col = np.floor(col).astype(np.int64); row = np.floor(row).astype(np.int64)
        inside = (row >= 0) & (row < r.height) & (col >= 0) & (col < r.width)
        r0, r1 = row[inside].min(), row[inside].max()
        c0, c1 = col[inside].min(), col[inside].max()
        for start in range(r0, r1 + 1, BAND):
            sel = inside & (row >= start) & (row < start + BAND)
            if not sel.any():
                continue
            h = min(BAND, r1 + 1 - start)
            a = r.read(1, window=Window(c0, start, c1 - c0 + 1, h))
            v = a[row[sel] - start, col[sel] - c0]
            v = np.where((v == r.nodata) | ~np.isfinite(v), 0, np.rint(v)).astype(np.int8)
            out[sel] = v
    return out


def main():
    _same_everywhere()
    pipes = _read("S1", "pipes"); holes = _read("S1", "manholes")
    geoms = np.array([g for _, g in pipes], dtype=object)
    lengths = shapely.length(geoms)
    n = np.maximum(1, np.ceil(lengths / STEP)).astype(np.int64)
    idx = np.repeat(np.arange(len(geoms)), n)
    k = np.arange(len(idx)) - np.repeat(np.cumsum(n) - n, n)          # 0..n-1 within each pipe
    dist = (k + 0.5) * (lengths[idx] / n[idx])
    pts = shapely.line_interpolate_point(geoms[idx], dist)
    px, py = shapely.get_x(pts), shapely.get_y(pts)
    w = lengths[idx] / n[idx]                                          # metres each sample stands for
    mx = np.array([g.x for _, g in holes]); my = np.array([g.y for _, g in holes])

    res = {"source": "Oman Flood Mapping project, MAFWR, hazard grids T10, T25, T50, T100; classes AIDR Guideline 7-3 (2017)",
           "pipes": {"count": len(pipes), "length_m": float(lengths.sum()), "samples": int(len(idx)), "step_m": STEP},
           "manholes": {"count": len(holes)}, "periods": {}}
    for T in PERIODS:
        path = HAZARD.format(T=T)
        vp = _sample(path, px, py); vm = _sample(path, mx, my)
        length = {CLASSES[c]: float(w[vp == c].sum()) for c in range(7)}
        # a pipe is counted in the highest class anywhere along it
        top = np.zeros(len(geoms), dtype=np.int8); np.maximum.at(top, idx, vp)
        res["periods"][str(T)] = {
            "grid": os.path.basename(path),
            "pipe_length_m": length,
            "pipe_length_h4_h6_m": sum(length[c] for c in ("H4", "H5", "H6")),
            "pipes_by_highest_class": {CLASSES[c]: int((top == c).sum()) for c in range(7)},
            "manholes": {CLASSES[c]: int((vm == c).sum()) for c in range(7)},
            "manholes_h4_h6": int((vm >= 4).sum()),
        }
        p = res["periods"][str(T)]
        print(f"T{T}: pipes in H4-H6 {p['pipe_length_h4_h6_m'] / 1000:.1f} km "
              f"({100 * p['pipe_length_h4_h6_m'] / lengths.sum():.2f} %), manholes in H4-H6 {p['manholes_h4_h6']}")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
