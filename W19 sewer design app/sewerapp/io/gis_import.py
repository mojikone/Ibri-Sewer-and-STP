"""A network from GIS layers (GeoPackage, GeoJSON, or a zipped shapefile) with a field mapping, in the manner of
SewerGEMS's ModelBuilder: a point layer of nodes and a line layer of links. Fields not mapped get defaults (ground 0,
invert ground - 1.5 m, the smallest catalogue size); a link without from/to fields is attached to the nearest node at
each end of its line, within a snapping tolerance. Exports of any project: DXF (links by size, nodes, labels) and
results as CSV."""
import io, os, tempfile, zipfile
import geopandas as gpd
import numpy as np, pandas as pd
from shapely.geometry import Point
from sewerapp.model.general import Project, NODE_COLS, LINK_COLS

NODE_FIELDS = ["id", "kind", "ground", "invert"]
LINK_FIELDS = ["id", "kind", "from_node", "to_node", "dn_mm", "inside_mm", "up_inv", "dn_inv", "length_m"]


def read_layer(path):
    if path.lower().endswith(".zip"):
        d = tempfile.mkdtemp(); zipfile.ZipFile(path).extractall(d)
        shp = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.lower().endswith(".shp")]
        if not shp: raise ValueError("the zip holds no .shp")
        return gpd.read_file(shp[0])
    return gpd.read_file(path)


def fields(path):
    g = read_layer(path); return dict(fields=[c for c in g.columns if c != "geometry"], rows=len(g),
                                      geometry=str(g.geom_type.iloc[0]) if len(g) else None, crs=g.crs.to_epsg() if g.crs else None)


def _get(g, mapping, key, default=None):
    f = (mapping or {}).get(key)
    return g[f] if f and f in g.columns else default


def import_layers(nodes_path, links_path, node_map=None, link_map=None, name="Imported network", snap_m=1.0, crs=None):
    gn, gl = read_layer(nodes_path), read_layer(links_path)
    epsg = crs or (gn.crs.to_epsg() if gn.crs else None)
    if gl.crs and gn.crs and gl.crs != gn.crs: gl = gl.to_crs(gn.crs)
    p = Project(name=name, crs=epsg); p.load_sets = {"design": {}}; p.settings["design_load"] = "design"
    ids = _get(gn, node_map, "id"); ids = ids.astype(str) if ids is not None else pd.Series([f"MH-{i + 1}" for i in range(len(gn))])
    ground = pd.to_numeric(_get(gn, node_map, "ground", pd.Series(0.0, index=gn.index)), errors="coerce").fillna(0.0)
    inv = pd.to_numeric(_get(gn, node_map, "invert", ground - 1.5), errors="coerce")
    kind = _get(gn, node_map, "kind", pd.Series("manhole", index=gn.index)).astype(str).str.lower()
    kind = kind.where(kind.isin(["manhole", "wetwell", "outfall", "storage", "junction"]), "manhole")
    if ids.duplicated().any(): raise ValueError(f"duplicate node ids: {ids[ids.duplicated()].head(3).tolist()}")
    p.nodes = pd.DataFrame(dict(kind=kind.values, x=gn.geometry.x.values, y=gn.geometry.y.values, ground=ground.values,
                                invert=inv.fillna(ground - 1.5).values, inflow_m3d=0.0), index=pd.Index(ids.values, name="id"))
    xy = p.nodes[["x", "y"]].to_numpy()

    def nearest(pt):
        d = np.hypot(xy[:, 0] - pt[0], xy[:, 1] - pt[1]); k = int(d.argmin())
        if d[k] > snap_m: raise ValueError(f"a link end at ({pt[0]:.2f}, {pt[1]:.2f}) is {d[k]:.2f} m from the nearest node (tolerance {snap_m} m)")
        return p.nodes.index[k]
    lid = _get(gl, link_map, "id"); lid = lid.astype(str) if lid is not None else pd.Series([f"P-{i + 1}" for i in range(len(gl))])
    fr, to = _get(gl, link_map, "from_node"), _get(gl, link_map, "to_node")
    dn = pd.to_numeric(_get(gl, link_map, "dn_mm", pd.Series(p.catalogue().nominal_mm.iloc[0], index=gl.index)), errors="coerce")
    rows = []
    for k, (i, geom) in enumerate(zip(lid.values, gl.geometry)):
        line = geom.geoms[0] if geom.geom_type == "MultiLineString" else geom
        c = list(line.coords)
        a = str(fr.iloc[k]) if fr is not None else nearest(c[0]); b = str(to.iloc[k]) if to is not None else nearest(c[-1])
        d = int(dn.iloc[k]) if dn.iloc[k] == dn.iloc[k] else int(p.catalogue().nominal_mm.iloc[0])
        ins = _get(gl, link_map, "inside_mm"); ins = float(ins.iloc[k]) if ins is not None else p.inside_of(d)
        ui = _get(gl, link_map, "up_inv"); di = _get(gl, link_map, "dn_inv"); ln = _get(gl, link_map, "length_m")
        rows.append(dict(id=i, kind="conduit", from_node=a, to_node=b, length_m=float(ln.iloc[k]) if ln is not None else line.length,
                         dn_mm=d, inside_mm=ins if ins == ins else float(d),
                         up_inv=float(ui.iloc[k]) if ui is not None else p.nodes.invert[a],
                         dn_inv=float(di.iloc[k]) if di is not None else p.nodes.invert[b], transfer=False,
                         coords=[list(map(float, xy_[:2])) for xy_ in c] if len(c) > 2 else None))
    p.links = pd.DataFrame(rows, columns=["id"] + LINK_COLS).set_index("id")
    if p.links.index.duplicated().any(): raise ValueError("duplicate link ids")
    return p


def dxf_bytes(project, results=None):
    import ezdxf
    doc = ezdxf.new("R2010"); msp = doc.modelspace(); n = project.nodes
    for i, r in project.links.iterrows():
        layer = f"{r.kind.upper()}_DN{int(r.dn_mm) if r.dn_mm == r.dn_mm else 0}"
        if layer not in doc.layers: doc.layers.add(layer)
        pts = r.coords if isinstance(r.coords, list) and len(r.coords) >= 2 else [(n.x[r.from_node], n.y[r.from_node]), (n.x[r.to_node], n.y[r.to_node])]
        msp.add_lwpolyline([tuple(map(float, q[:2])) for q in pts], dxfattribs={"layer": layer})
        m = pts[len(pts) // 2]
        msp.add_text(f"{i} DN{int(r.dn_mm) if r.dn_mm == r.dn_mm else ''}", dxfattribs={"layer": "LABEL_LINK", "height": 0.8}).set_placement(tuple(map(float, m[:2])))
    for layer in ("NODE", "LABEL_NODE", "LABEL_LINK"):
        if layer not in doc.layers: doc.layers.add(layer)
    for i, r in n.iterrows():
        msp.add_point((float(r.x), float(r.y)), dxfattribs={"layer": "NODE"})
        msp.add_text(str(i), dxfattribs={"layer": "LABEL_NODE", "height": 0.8}).set_placement((float(r.x), float(r.y)))
    s = io.StringIO(); doc.write(s); return s.getvalue().encode("utf-8")
