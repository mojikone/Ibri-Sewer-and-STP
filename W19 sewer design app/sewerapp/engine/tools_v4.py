"""W19 v4 (2026-11-23): SewerGEMS's remaining tools in the app.

- LoadBuilder: loads from a GIS layer (points, or polygons by their centre) to the nearest structure that takes a load
  (a manhole, wet well or storage), summed, as typed loads of a load set or as unit-load rows (a count of a unit load);
- TRex: ground levels of the structures from a terrain GeoTIFF (reprojected when its CRS differs), the inverts moved
  with the ground when asked (depths kept); cells with no data are reported, not used;
- Rational method (a steady storm run): Q = C i A / 360 (m3/s with i in mm/h and A in ha) on every conduit, with the
  catchments' C and time of concentration (both given by the engineer, Project.hydrology), the travel time down the
  pipes (at the pipe's normal-depth velocity, iterated) and the intensity from the project's IDF table at the critical
  duration (log-log interpolation, as the design storm);
- Batch run: the steady summary of several scenarios in one table."""
import math
import numpy as np, pandas as pd

LOAD_NODES = ("manhole", "wetwell", "storage", "junction")


def nearest_nodes(project, xs, ys, kinds=LOAD_NODES):
    from scipy.spatial import cKDTree
    N = project.nodes[project.nodes.kind.isin(kinds)]
    if not len(N): raise ValueError("no structure that takes a load")
    t = cKDTree(np.c_[N.x.to_numpy(float), N.y.to_numpy(float)]); d, k = t.query(np.c_[xs, ys])
    return N.index.to_numpy()[k], d


def loadbuilder(project, gdf, field, scale=1.0, max_dist=None):
    """Per structure: the sum of `field` x scale over the features nearest to it; and what was left out."""
    if field not in gdf.columns: raise ValueError(f"the layer has no field {field}")
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]               # features with no shape are left out
    no_crs = gdf.crs is None
    if project.crs and not no_crs:
        gdf = gdf.to_crs(epsg=int(project.crs))
    g = gdf.geometry
    pts = g.where(g.geom_type.isin(["Point"]), g.representative_point())
    v = pd.to_numeric(gdf[field], errors="coerce").to_numpy(float) * float(scale)
    ok = np.isfinite(v) & ~pts.is_empty.to_numpy()
    ids, d = nearest_nodes(project, pts.x.to_numpy()[ok], pts.y.to_numpy()[ok])
    far = (d > float(max_dist)) if max_dist else np.zeros(len(d), bool)
    s = pd.Series(v[ok][~far], index=ids[~far]).groupby(level=0).sum()
    return s, dict(features=int(len(gdf)), used=int((~far).sum()), no_value=int((~ok).sum()), too_far=int(far.sum()), no_crs=bool(no_crs),
                   structures=int(len(s)), total=float(s.sum()), max_distance_m=float(d.max()) if len(d) else 0.0)


def trex(project, tif_path, ids=None):
    """Ground level at each structure from a terrain raster: {id: level}, and the structures on no-data cells."""
    import rasterio
    from pyproj import Transformer
    N = project.nodes if not ids else project.nodes.loc[[i for i in ids if i in project.nodes.index]]
    with rasterio.open(tif_path) as r:
        x, y = N.x.to_numpy(float), N.y.to_numpy(float)
        if r.crs is not None and project.crs and r.crs.to_epsg() != int(project.crs):
            x, y = Transformer.from_crs(int(project.crs), r.crs, always_xy=True).transform(x, y)
        b = r.bounds; inside = (x >= b.left) & (x <= b.right) & (y >= b.bottom) & (y <= b.top)   # off the raster: no value
        vals = np.full(len(x), np.nan)
        if inside.any(): vals[inside] = np.array([v[0] for v in r.sample(zip(x[inside], y[inside]))], float)
        nod = r.nodata
    bad = ~np.isfinite(vals) | ((vals == nod) if nod is not None else False)
    out = {i: float(v) for i, v, b in zip(N.index, vals, bad) if not b}
    return out, [i for i, b in zip(N.index, bad) if b]


def idf_intensity(idf, minutes):
    d = np.array(idf["durations_min"], float); i = np.array(idf["intensities"], float)
    return float(np.exp(np.interp(math.log(max(minutes, d.min())), np.log(d), np.log(i))))


def rational(project, inlet_rows=None):
    """The rational method on every conduit: a steady storm run. Returns (rows by link id, summary). A catch basin's
    inlet takes what it captures of its surface flow into the pipes (engine/inlets.py, HEC-22): its catchments' C A in
    that proportion, and the captured part of the flow its gutter brings as a known flow; the rest goes down its gutter
    (v7). inlet_rows: a dict that receives each catch basin's row."""
    from sewerapp.engine import steady, inlets
    raw = project
    p = steady.engine_view(project)
    p = steady._without_storm_only(p) if p.links.kind.isin(steady.STORM_ONLY).any() else p
    L = p.links; s = p.settings
    idf = (p.rain or {}).get("idf")
    if not idf: raise ValueError("the rational method needs an IDF table (Settings > Rain, defined by IDF table)")
    hyd = getattr(p, "hydrology", None) or {}
    missing = [c for c in p.catchments.index if (hyd.get(c) or {}).get("C") is None or (hyd.get(c) or {}).get("tc_min") is None]
    if missing: raise ValueError(f"no runoff coefficient C or time of concentration on {len(missing)} catchment(s), e.g. {missing[0]}: set them in the catchment's Properties")
    CA, TC = {}, {}
    for c, r in p.catchments.iterrows():
        h = hyd[c]; CA[r.outlet] = CA.get(r.outlet, 0.0) + float(h["C"]) * float(r.area_ha)
        TC[r.outlet] = max(TC.get(r.outlet, 0.0), float(h["tc_min"]))
    KNOWN = {}                                                             # flows that enter as they are (m3/s)
    if (raw.nodes.kind == "catch_basin").any():
        local = {n: CA[n] * idf_intensity(idf, TC[n]) / 360.0 for n in CA if n in raw.nodes.index and raw.nodes.kind[n] == "catch_basin"}
        rows_in = inlets.route(raw, local)
        for n, r in rows_in.items():
            f = r["q_captured_ls"] / r["q_gutter_ls"] if r["q_gutter_ls"] > 0 else 1.0
            if n in CA: CA[n] *= f
            if r["q_carry_in_ls"] > 0: KNOWN[n] = r["q_carry_in_ls"] / 1000.0 * f
        if inlet_rows is not None: inlet_rows.update(rows_in)
    secs = getattr(p, "sections", None) or {}
    cond = L[(L.kind == "conduit") & ~L.index.isin(list(secs))]; order = steady.order(L)      # boxes and channels: flow only
    vel = pd.Series(1.0, index=L.index)                                    # m/s, refined by the hydraulics below
    for _ in range(3):
        acc_ca, acc_tc, acc_k = dict(CA), dict(TC), dict(KNOWN); q, tc_l, i_l, ca_l = {}, {}, {}, {}
        for k in order:
            lid = L.index[k]; u, d = L.from_node.iat[k], L.to_node.iat[k]
            ca, tc = acc_ca.get(u, 0.0), acc_tc.get(u, 0.0)
            i = idf_intensity(idf, tc) if ca > 0 else 0.0
            q[lid] = ca * i / 360.0 + acc_k.get(u, 0.0); tc_l[lid], i_l[lid], ca_l[lid] = tc, i, ca
            tt = float(L.length_m.iat[k]) / max(float(vel.get(lid, 1.0)), 0.1) / 60.0 if L.kind.iat[k] == "conduit" else 0.0
            acc_ca[d] = acc_ca.get(d, 0.0) + ca; acc_k[d] = acc_k.get(d, 0.0) + acc_k.get(u, 0.0)
            if ca > 0: acc_tc[d] = max(acc_tc.get(d, 0.0), tc + tt)          # a dry branch adds no travel time
        D = cond.inside_mm.astype(float).to_numpy() / 1000.0
        S = ((cond.up_inv - cond.dn_inv) / cond.length_m).astype(float).to_numpy()
        Qa = np.array([q[i] for i in cond.index])
        ratio, v, full = steady.normal_depth(p, Qa, D, S)
        vel = pd.Series(np.where(v > 0, v, 1.0), index=cond.index)
    rows = {lid: dict(q_rational_ls=q[lid] * 1000.0, tc_min=tc_l[lid], i_mm_h=i_l[lid], ca_ha=ca_l[lid]) for lid in L.index}
    for k, lid in enumerate(cond.index):
        rows[lid].update(v_ms=float(v[k]), d_over_D=float(ratio[k]), surcharged=bool(full[k]))
    summ = dict(conduits=int(len(cond)), surcharged=int(full.sum()), peak_ls=float(max([r["q_rational_ls"] for r in rows.values()] or [0])),
                catchments=int(len(p.catchments)))
    return rows, summ


def batch(session, sids):
    rows = []
    for sid in sids:
        res, summ = session.solve(sid)
        pr = summ.get("pressure") or {}; gv = summ.get("gvf") or {}
        rows.append(dict(id=sid, scenario=session.scenarios[sid].name, conduits=summ.get("conduits"), km=summ.get("km"),
                         over_limit=summ.get("over_limit"), over_vmax=summ.get("over_vmax"), surcharged=summ.get("surcharged"),
                         km_under_vmin=summ.get("km_under_vmin"), pumps_short=pr.get("pumps_short"), flooding_nodes=gv.get("flooding_nodes"),
                         problems=len(summ.get("problems") or []), seconds=summ.get("seconds")))
    return rows
