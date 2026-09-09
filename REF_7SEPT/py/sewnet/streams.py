"""sewnet.streams — the guide picture: terrain streams with Strahler order, and wadi ground.

The streams are derived from the terrain blend at a coarse cell with pysheds (pit fill,
depression fill, flats resolved, D8 direction, accumulation). They are a picture of where
the valleys are, which is where the sub-main streets are (rule 1); they never carry a
design value. Wadi ground is the flood hazard grid, classes 4 to 6.
"""
import os

import numpy as np
if not hasattr(np, "in1d"):          # numpy 2 removed it; pysheds still calls it
    np.in1d = np.isin
import rasterio
from rasterio import features
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage
from shapely.geometry import LineString, shape


def derive_streams(vrt_path, bounds, res, threshold_cells, scratch_dir, pad=1000.0):
    ds = rasterio.open(vrt_path)
    l, b, r, t = bounds
    l, b, r, t = l - pad, b - pad, r + pad, t + pad
    w = from_bounds(l, b, r, t, ds.transform)
    f = res / ds.res[0]
    h, wd = int(w.height / f), int(w.width / f)
    arr = ds.read(1, window=w, out_shape=(h, wd), resampling=Resampling.average).astype("float32")
    nod = ~np.isfinite(arr) | (arr < -1000)
    if ds.nodata is not None:
        nod |= arr == ds.nodata
    if nod.any():
        idx = ndimage.distance_transform_edt(nod, return_distances=False, return_indices=True)
        arr = arr[tuple(idx)]
    x0, y0 = ds.transform * (w.col_off, w.row_off)
    tr = rasterio.transform.from_origin(x0, y0, (w.width / wd) * ds.res[0],
                                        (w.height / h) * ds.res[1])
    os.makedirs(scratch_dir, exist_ok=True)
    tmp = os.path.join(scratch_dir, f"ground_{int(res)}m.tif")
    with rasterio.open(tmp, "w", driver="GTiff", height=h, width=wd, count=1, dtype="float32",
                       crs=ds.crs, transform=tr, nodata=-9999.0) as dst:
        dst.write(arr, 1)

    from pysheds.grid import Grid
    grid = Grid.from_raster(tmp)
    dem = grid.read_raster(tmp)
    pit = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit)
    inflated = grid.resolve_flats(flooded)
    fdir = grid.flowdir(inflated)
    acc = grid.accumulation(fdir)
    mask = acc > threshold_cells
    order = None
    try:
        order = grid.stream_order(fdir, mask)
    except Exception:
        pass
    net = grid.extract_river_network(fdir, mask)
    feats = []
    for ft in net["features"]:
        coords = ft["geometry"]["coordinates"]
        if len(coords) < 2:
            continue
        ls = LineString(coords)
        o = 1
        if order is not None:
            x, y = coords[len(coords) // 2]
            try:
                col, row = grid.nearest_cell(x, y)
                o = int(order[row, col])
            except Exception:
                o = 1
        feats.append((ls, max(o, 1)))
    return feats, {"cells": int(h * wd), "res_m": res, "threshold_cells": threshold_cells,
                   "branches": len(feats), "max_order": max((o for _, o in feats), default=0)}


def wadi_polygons(hazard_path, bounds, classes=(4, 5, 6), min_area=500.0):
    ds = rasterio.open(hazard_path)
    w = from_bounds(*bounds, ds.transform)
    arr = ds.read(1, window=w)
    mask = np.isin(np.round(arr), classes).astype("uint8")
    tr = ds.window_transform(w)
    polys = [shape(g) for g, v in features.shapes(mask, mask=mask.astype(bool), transform=tr)
             if v == 1]
    return [p.simplify(3.0) for p in polys if p.area > min_area]
