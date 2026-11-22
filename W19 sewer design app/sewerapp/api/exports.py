"""Exports of a scenario: GeoPackage (pipes and manholes with results, EPSG:32640, opens in QGIS) and DXF (pipes on
one layer per size, manholes as points, labels)."""
import io, os, tempfile
import numpy as np


def _pipes_gdf(case, res, s1_path):
    import geopandas as gpd
    from shapely.geometry import LineString
    k = case.links; n = case.nodes
    lines = gpd.read_file(s1_path, layer="pipes").set_index("label").geometry
    xy = {lab: (r.x, r.y) for lab, r in n.iterrows()}
    geom = [lines.get(o) if o in lines.index else LineString([xy[a], xy[b]]) for o, a, b in zip(k.old, k.from_mh, k.to_mh)]
    cols = res.drop(columns=[]).copy()
    for c in cols.columns:
        if cols[c].dtype == bool: cols[c] = cols[c].astype(int)
    return gpd.GeoDataFrame(cols, geometry=geom, crs=32640)


def gpkg_bytes(case, res, s1_path):
    import geopandas as gpd
    from shapely.geometry import Point
    p = _pipes_gdf(case, res, s1_path); n = case.nodes
    m = gpd.GeoDataFrame(dict(label=n.index, kind=n.kind, ground=n.ground, depth=n.depth),
                         geometry=[Point(x, y) for x, y in zip(n.x, n.y)], crs=32640)
    f = os.path.join(tempfile.mkdtemp(), "export.gpkg")
    p.to_file(f, layer="pipes", driver="GPKG"); m.to_file(f, layer="manholes", driver="GPKG")
    return open(f, "rb").read()


def dxf_bytes(case, res):
    import ezdxf
    doc = ezdxf.new("R2010"); msp = doc.modelspace()
    n = case.nodes
    for dn, grp in res.groupby("dn_mm"):
        layer = f"PIPE_DN{int(dn)}"
        if layer not in doc.layers: doc.layers.add(layer)
        for r in grp.itertuples():
            a, b = n.loc[r.from_mh], n.loc[r.to_mh]
            msp.add_line((a.x, a.y), (b.x, b.y), dxfattribs={"layer": layer})
    doc.layers.add("MANHOLE")
    for lab, r in n.iterrows():
        msp.add_point((r.x, r.y), dxfattribs={"layer": "MANHOLE"})
    s = io.StringIO(); doc.write(s)
    return s.getvalue().encode("utf-8")
