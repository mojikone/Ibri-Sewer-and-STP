"""The project file: an open GeoPackage that QGIS reads directly. Layers nodes (points), links (lines; their vertices
are the drawn route) and catchments (polygons), in the project's CRS (none for local metres), plus a plain table
`w19_project` holding the settings, load sets, rain, scenarios and SWMM passthrough as JSON."""
import json, os, sqlite3
import geopandas as gpd
import numpy as np, pandas as pd
from shapely.geometry import LineString, Point, Polygon
from sewerapp.model.general import Project, NODE_COLS, LINK_COLS, CATCH_COLS


def _crs(p):
    return f"EPSG:{p.crs}" if p.crs else None


def save(project, path, extra=None):
    if os.path.exists(path): os.remove(path)
    n = project.nodes
    gpd.GeoDataFrame(n[NODE_COLS[:1] + NODE_COLS[3:]].reset_index(), geometry=[Point(x, y) for x, y in zip(n.x, n.y)],
                     crs=_crs(project)).to_file(path, layer="nodes", driver="GPKG")
    L = project.links
    geom = []
    for r in L.itertuples():
        c = r.coords if isinstance(r.coords, list) and len(r.coords) >= 2 else None
        geom.append(LineString(c) if c else LineString([(n.x[r.from_node], n.y[r.from_node]), (n.x[r.to_node], n.y[r.to_node])]))
    lk = L.drop(columns=["coords"]).reset_index()
    lk["drawn"] = [isinstance(c, list) and len(c) >= 2 for c in L.coords]
    gpd.GeoDataFrame(lk, geometry=geom, crs=_crs(project)).to_file(path, layer="links", driver="GPKG")
    C = project.catchments
    if len(C):
        gpd.GeoDataFrame(C.drop(columns=["coords"]).reset_index(),
                         geometry=[Polygon(c) if isinstance(c, list) and len(c) >= 3 else None for c in C.coords],
                         crs=_crs(project)).to_file(path, layer="catchments", driver="GPKG")
    meta = dict(project.to_json(), meta=getattr(project, "meta", {}), extra=extra or {})
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE w19_project (key TEXT PRIMARY KEY, value TEXT)")
        db.execute("INSERT INTO w19_project VALUES ('project', ?)", (json.dumps(meta),))
    return path


def load(path):
    with sqlite3.connect(path) as db:
        meta = json.loads(db.execute("SELECT value FROM w19_project WHERE key='project'").fetchone()[0])
    import pyogrio
    layers = {l[0] for l in pyogrio.list_layers(path)}
    p = Project(name=meta["name"], crs=meta["crs"], settings=meta["settings"], load_sets=meta["load_sets"], fixed_flows=meta.get("fixed_flows", {}),
                rain=meta.get("rain", {}), passthrough=meta.get("passthrough", {}))
    n = gpd.read_file(path, layer="nodes")
    n["x"] = n.geometry.x; n["y"] = n.geometry.y
    p.nodes = pd.DataFrame(n.drop(columns="geometry")).set_index("id")[NODE_COLS]
    L = gpd.read_file(path, layer="links")
    L["coords"] = [[list(c) for c in g.coords] if d else None for g, d in zip(L.geometry, L.drawn)]
    L["transfer"] = L.transfer.astype(bool)
    p.links = pd.DataFrame(L.drop(columns=["geometry", "drawn"])).set_index("id")[LINK_COLS]
    if "catchments" in layers:
        C = gpd.read_file(path, layer="catchments")
        C["coords"] = [[list(c) for c in g.exterior.coords] if g is not None else None for g in C.geometry]
        p.catchments = pd.DataFrame(C.drop(columns="geometry")).set_index("id")[CATCH_COLS]
    p.meta = meta.get("meta", {})
    return p, meta.get("extra", {})
