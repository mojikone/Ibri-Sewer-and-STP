"""Terrain for TRex beyond a file on this computer (the engineer, 2026-11-23):

- points_in: the structures' coordinates in a terrain's own CRS, so the browser can read a GeoTIFF or VRT the engineer
  picked on their own machine without uploading it (web/editor/features6.js samples the pixels and sends the levels);
- copernicus: ground levels from the Copernicus GLO-30 surface model, read a window at a time from its public
  Cloud-Optimised GeoTIFF tiles (AWS open data, bucket copernicus-dem-30m), bilinear between cell centres.

GLO-30 is a DIGITAL SURFACE MODEL: roofs and trees are in it, the vertical accuracy is metres and the heights are above
the EGM2008 geoid. It is for screening and a first layout, not for design levels; every level it gives is recorded as
such (Project.ground_src) and Validate says how many structures rest on it.
Licence: free, worldwide, with the notice below (Licence for the use of the Copernicus WorldDEM-30, Articles 4-6)."""
import math
import numpy as np

COPERNICUS_NOTICE = ("produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH "
                     "2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved")
COPERNICUS_LIABILITY = ("The organisations in charge of the Copernicus programme by law or by delegation do not incur any "
                        "liability for any use of the Copernicus WorldDEM-30.")
COPERNICUS_SRC = "Copernicus GLO-30 surface model (DSM), 30 m, EGM2008 heights: screening only"
BUCKET = "https://copernicus-dem-30m.s3.amazonaws.com"
MAX_TILES = 16                                   # 16 one-degree tiles: about 300 x 400 km, far beyond any one network


def _nodes(project, ids):
    N = project.nodes
    if ids: N = N.loc[[i for i in ids if i in N.index]]
    return N[np.isfinite(N.x.astype(float)) & np.isfinite(N.y.astype(float))]


def points_in(project, crs, ids=None):
    """The structures' x, y in the terrain's CRS (an EPSG code such as "EPSG:32640", or the WKT of a VRT's SRS). A project
    without a CRS gives its own coordinates (the terrain is then taken to be in the same local system)."""
    N = _nodes(project, ids); x, y = N.x.to_numpy(float), N.y.to_numpy(float)
    if project.crs and crs:
        from pyproj import CRS, Transformer
        try: dst = CRS.from_user_input(crs)
        except Exception as e: raise ValueError(f"the terrain's coordinate system is not understood ({str(e)[:120]})")
        if dst != CRS.from_epsg(int(project.crs)):
            x, y = Transformer.from_crs(int(project.crs), dst, always_xy=True).transform(x, y)
    return [str(i) for i in N.index], [float(v) for v in x], [float(v) for v in y]


def _tile(lat, lon):
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    name = f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    return f"{BUCKET}/{name}/{name}.tif"


def copernicus(project, ids=None, opener=None):
    """Ground levels {id: level} from GLO-30, the structures with no value (sea, a tile that does not exist), and the tiles
    read. Needs a project in a real CRS. `opener(url)` is rasterio.open by default (tests give a local stand-in)."""
    if not project.crs: raise ValueError("Copernicus levels need a project in a real coordinate system (this one is in local metres)")
    import rasterio
    from pyproj import Transformer
    N = _nodes(project, ids)
    if not len(N): return {}, [], []
    lon, lat = Transformer.from_crs(int(project.crs), 4326, always_xy=True).transform(N.x.to_numpy(float), N.y.to_numpy(float))
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    # a tile's edges sit half a cell off the whole degree, so a point near an edge may be in the neighbour: try both
    e = 0.001; tiles = set()
    for a, b in zip(lat, lon):
        for la in {math.floor(a - e), math.floor(a + e)}:
            for lo in {math.floor(b - e), math.floor(b + e)}: tiles.add((la, lo))
    if len(tiles) > MAX_TILES: raise ValueError(f"the network spans {len(tiles)} one-degree tiles; at most {MAX_TILES} are read at once (select a part)")
    vals = np.full(len(lon), np.nan); read = []
    opener = opener or rasterio.open
    env = dict(GDAL_HTTP_TIMEOUT="30", GDAL_HTTP_MAX_RETRY="2", GDAL_HTTP_RETRY_DELAY="1", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
               CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", VSI_CACHE="TRUE")
    with rasterio.Env(**env):
        for la, lo in sorted(tiles):
            todo = np.isnan(vals)
            if not todo.any(): break
            url = _tile(la, lo)
            try: src = opener(url)
            except Exception: continue                      # no tile here (sea, or not released): no value
            with src as r:
                b = r.bounds
                m = todo & (lon >= b.left) & (lon < b.right) & (lat > b.bottom) & (lat <= b.top)
                if not m.any(): continue
                read.append(url.rsplit("/", 1)[1])
                inv = ~r.transform
                c, rw = inv * (lon[m], lat[m])                # fractional column and row (edges of cells)
                fc, fr = np.asarray(c) - 0.5, np.asarray(rw) - 0.5   # relative to cell centres
                c0, r0 = int(max(0, math.floor(fc.min()))), int(max(0, math.floor(fr.min())))
                c1, r1 = int(min(r.width - 1, math.floor(fc.max()) + 1)), int(min(r.height - 1, math.floor(fr.max()) + 1))
                from rasterio.windows import Window
                a = r.read(1, window=Window(c0, r0, c1 - c0 + 1, r1 - r0 + 1)).astype(float)   # one window per tile
                if r.nodata is not None: a[a == r.nodata] = np.nan
                i = np.clip(np.floor(fc).astype(int) - c0, 0, a.shape[1] - 1); j = np.clip(np.floor(fr).astype(int) - r0, 0, a.shape[0] - 1)
                i1 = np.minimum(i + 1, a.shape[1] - 1); j1 = np.minimum(j + 1, a.shape[0] - 1)
                tx = np.clip(fc - np.floor(fc), 0, 1); ty = np.clip(fr - np.floor(fr), 0, 1)
                v = (a[j, i] * (1 - tx) * (1 - ty) + a[j, i1] * tx * (1 - ty) + a[j1, i] * (1 - tx) * ty + a[j1, i1] * tx * ty)
                vals[np.where(m)[0]] = v
    out = {str(k): float(v) for k, v in zip(N.index, vals) if np.isfinite(v)}
    return out, [str(k) for k, v in zip(N.index, vals) if not np.isfinite(v)], read
