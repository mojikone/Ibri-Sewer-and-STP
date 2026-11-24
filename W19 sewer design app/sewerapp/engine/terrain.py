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


# ---------------------------------------------------------------------------------------------------------------------
# Contours and spot levels (F28, 2026-11-23): a TIN of every vertex near the network, linear inside each triangle.
# Sources: a GIS layer (shapefile, GeoPackage, GeoJSON) with an elevation field or Z, a DXF (contours carry their
# elevation as Z; spot levels as points with Z, or as numbers written in TEXT), a DWG through the free ODA File
# Converter when it is installed on this computer. A DXF or DWG has no coordinate system: it is taken as the project's.
# Contours make flat triangles along ridges and valleys (three vertices on one contour); a structure there gets that
# contour's level. Outside the TIN (beyond the data) a structure gets no value.
VECTOR_EXT = (".shp", ".gpkg", ".geojson", ".json", ".dxf", ".dwg")
MAX_VERTICES = 3_000_000
Z_FIELD = "(Z of the lines or points)"
TEXT_FIELD = "(numbers written in the drawing's text)"


def dwg_to_dxf(path):
    """A DWG converted to a DXF beside it by the ODA File Converter, if this computer has it; otherwise a clear refusal."""
    from ezdxf.addons import odafc
    if not odafc.is_installed():
        raise ValueError("a DWG cannot be read without the free ODA File Converter on this computer "
                         "(opendesign.com, File Converter): install it, or save the drawing as DXF (AutoCAD: Save As > DXF)")
    out = path[:-4] + ".dxf"; odafc.convert(path, out, version="R2018", audit=True, replace=True); return out


def _frame(path, layer=None):
    import geopandas as gpd
    if path.lower().endswith(".dwg"): path = dwg_to_dxf(path)
    g = gpd.read_file(path, layer=layer) if layer else gpd.read_file(path)
    return g[g.geometry.notna() & ~g.geometry.is_empty], path.lower().endswith(".dxf")


def _num(s):
    import pandas as pd
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False).str.extract(r"(-?\d+(?:\.\d+)?)")[0], errors="coerce")


def vector_inspect(path):
    """What a contour or spot-level file offers: its layers; for the chosen (first) one the geometry types, the count,
    the fields that can carry a level, whether the geometry has non-zero Z, its CRS and (a DXF) its drawing layers."""
    import pyogrio
    if path.lower().endswith(".dwg"): path = dwg_to_dxf(path)
    layers = [str(l[0]) for l in pyogrio.list_layers(path)]
    g, dxf = _frame(path, layers[0] if len(layers) > 1 else None)
    import numpy as np
    from shapely import get_coordinates
    xyz = get_coordinates(g.geometry.values, include_z=True)
    hasz = xyz.shape[1] == 3 and np.isfinite(xyz[:, 2]).any() and bool((np.nan_to_num(xyz[:, 2]) != 0).any())
    fields = [c for c in g.columns if c != "geometry" and c not in ("Layer", "SubClasses", "EntityHandle", "Linetype", "PaperSpace", "Text")
              and _num(g[c]).notna().mean() > 0.5]
    if hasz: fields = [Z_FIELD] + fields
    if dxf and "Text" in g.columns and _num(g["Text"]).notna().sum() > 0: fields.append(TEXT_FIELD)
    return dict(layers=layers, count=int(len(g)), geometry=sorted(set(g.geom_type)), fields=fields, has_z=bool(hasz),
                crs=(g.crs.to_string() if g.crs else None), dxf_layers=sorted(set(g["Layer"].astype(str))) if dxf and "Layer" in g.columns else [])


def vector_levels(project, path, field, layer=None, dxf_layer=None, ids=None):
    """Ground levels {id: level} at the structures from a TIN of the file's vertices, the structures outside it, and the
    number of vertices used."""
    import numpy as np
    from scipy.interpolate import LinearNDInterpolator
    from shapely import get_coordinates
    g, dxf = _frame(path, layer)
    if dxf_layer and "Layer" in g.columns: g = g[g["Layer"].astype(str) == str(dxf_layer)]
    if not len(g): raise ValueError("no lines or points in that selection")
    crs = g.crs.to_wkt() if g.crs is not None else None
    nid, x, y = points_in(project, crs, ids)
    if not nid: return {}, [], 0
    X, Y = np.asarray(x), np.asarray(y)
    span = max(X.max() - X.min(), Y.max() - Y.min(), 1.0); geo = g.crs is not None and g.crs.is_geographic
    buf = max(span * 0.1, 0.005 if geo else 300.0)            # the data around the network, not a whole country's contours
    g = g.cx[X.min() - buf:X.max() + buf, Y.min() - buf:Y.max() + buf]
    if field == TEXT_FIELD:
        g = g.assign(_z=_num(g["Text"])); g = g[g._z.notna()]
        pts = np.column_stack([get_coordinates(g.geometry.values)[:, :2], g._z.to_numpy(float)]) if len(g) else np.empty((0, 3))
    elif field == Z_FIELD:
        pts = get_coordinates(g.geometry.values, include_z=True)
    else:
        if field not in g.columns: raise ValueError(f"no field {field}")
        z = _num(g[field]).to_numpy(float); parts = []
        for geom, zz in zip(g.geometry.values, z):
            if np.isfinite(zz): c = get_coordinates(geom); parts.append(np.column_stack([c[:, :2], np.full(len(c), zz)]))
        pts = np.vstack(parts) if parts else np.empty((0, 3))
    pts = pts[np.isfinite(pts).all(axis=1)] if len(pts) else pts
    if field == Z_FIELD and dxf and len(pts) and (pts[:, 2] != 0).any(): pts = pts[pts[:, 2] != 0]   # DXF entities drawn with no elevation
    if len(pts) < 3: raise ValueError("fewer than three levelled vertices near the network: check the elevation field and the coordinate system")
    _, keep = np.unique(np.round(pts[:, :2], 3), axis=0, return_index=True); pts = pts[np.sort(keep)]
    if len(pts) > MAX_VERTICES: pts = pts[np.linspace(0, len(pts) - 1, MAX_VERTICES).astype(int)]
    v = LinearNDInterpolator(pts[:, :2], pts[:, 2])(X, Y)
    out = {i: float(z) for i, z in zip(nid, v) if np.isfinite(z)}
    return out, [i for i, z in zip(nid, v) if not np.isfinite(z)], int(len(pts))
