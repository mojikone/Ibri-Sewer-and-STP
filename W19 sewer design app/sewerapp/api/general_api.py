"""The general app's API (/api/g): projects (new, sample, open, save), scenarios (copy, undo, redo), edits by element
id with instant re-solve, the model and results for the map, the profile. Positions from the map arrive as lon/lat
and are converted at this one boundary (api/coords.py)."""
import io, math, os, tempfile, threading, itertools
import numpy as np, pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from sewerapp.api import coords
from sewerapp.io import gpkg_project, ibri_sample
from sewerapp.model.general import Project, NODE_KINDS, LINK_KINDS
from sewerapp.model.workspace import Session

router = APIRouter(prefix="/api/g")
SESSIONS: dict[str, Session] = {}
_lock = threading.RLock()
_ids = itertools.count(1)


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, np.generic): x = x.item()
    if isinstance(x, float) and not math.isfinite(x): return None
    return x


def _s(pid):
    if pid not in SESSIONS: raise HTTPException(404, f"no open project {pid}")
    return SESSIONS[pid]


def _open(project):
    pid = f"p{next(_ids)}"; SESSIONS[pid] = Session(pid, project); return pid


def _info(pid):
    s = SESSIONS[pid]; p = s.base
    return dict(id=pid, name=p.name, crs=p.crs, basemap=bool(p.crs), scenarios=[c.to_dict() for c in s.scenarios.values()],
                load_sets=sorted(p.load_sets), node_kinds=NODE_KINDS, link_kinds=LINK_KINDS,
                catalogue=p.catalogue().nominal_mm.tolist())


class New(BaseModel):
    name: str = "New project"
    crs: int | None = None


@router.get("/projects")
def projects():
    return [dict(id=k, name=s.base.name) for k, s in SESSIONS.items()]


@router.post("/projects/new")
def new(b: New):
    p = Project(name=b.name, crs=b.crs); p.load_sets = {"design": {}}; p.settings["design_load"] = "design"
    with _lock: pid = _open(p)
    return _info(pid)


@router.get("/samples")
def samples():
    return [dict(id=c, name=f"Ibri {c} (W18 final design)") for c in ibri_sample.CASES]


@router.post("/projects/sample/{case}")
def sample(case: str):
    if case not in ibri_sample.CASES: raise HTTPException(404, case)
    with _lock: pid = _open(ibri_sample.build(case))
    return _info(pid)


@router.post("/projects/open")
async def open_file(file: UploadFile = File(...)):
    d = tempfile.mkdtemp(); f = os.path.join(d, "upload.gpkg"); open(f, "wb").write(await file.read())
    try: p, _ = gpkg_project.load(f)
    except Exception as e: raise HTTPException(400, f"not a project file: {e}")
    with _lock: pid = _open(p)
    return _info(pid)


@router.post("/projects/import")
async def import_inp(file: UploadFile = File(...)):
    """An EPA SWMM 5 input file (.inp) as a project (SWMM's own sections kept; values in the file's units)."""
    text = (await file.read()).decode("utf-8", errors="ignore")
    try:
        from sewerapp.io import swmm_inp
        p = swmm_inp.to_project(text, os.path.splitext(file.filename or "SWMM model")[0])
    except Exception as e: raise HTTPException(400, f"not a SWMM input file: {e}")
    with _lock: pid = _open(p)
    return _info(pid)


@router.post("/gis/fields")
async def gis_fields(file: UploadFile = File(...)):
    """The fields of an uploaded layer (GeoPackage, GeoJSON or zipped shapefile), for the field-mapping dialog."""
    from sewerapp.io import gis_import
    f = os.path.join(tempfile.mkdtemp(), file.filename or "layer"); open(f, "wb").write(await file.read())
    try: return gis_import.fields(f)
    except Exception as e: raise HTTPException(400, f"not a readable layer: {e}")


@router.post("/projects/import_gis")
async def import_gis(nodes: UploadFile = File(...), links: UploadFile = File(...), mapping: str = "{}", name: str = "Imported network",
                     snap_m: float = 1.0):
    """A network from a node layer and a link layer with a field mapping {"nodes": {...}, "links": {...}}."""
    import json as _json
    from sewerapp.io import gis_import
    d = tempfile.mkdtemp(); fn = os.path.join(d, "n_" + (nodes.filename or "n")); fl = os.path.join(d, "l_" + (links.filename or "l"))
    open(fn, "wb").write(await nodes.read()); open(fl, "wb").write(await links.read())
    try:
        m = _json.loads(mapping or "{}")
        p = gis_import.import_layers(fn, fl, m.get("nodes"), m.get("links"), name=name, snap_m=snap_m)
    except Exception as e: raise HTTPException(400, str(e))
    with _lock: pid = _open(p)
    return _info(pid)


@router.get("/projects/{pid}/export.dxf")
def export_dxf(pid: str, sid: str = "base"):
    from sewerapp.io import gis_import
    s = _s(pid)
    return Response(gis_import.dxf_bytes(s.model(sid)), media_type="application/dxf", headers={"Content-Disposition": 'attachment; filename="network.dxf"'})


@router.get("/projects/{pid}/export.csv")
def export_csv(pid: str, sid: str = "base"):
    s = _s(pid)
    with _lock: res, _ = s.solve(sid)
    p = s.model(sid); t = p.links.drop(columns=["coords"]).join(res.drop(columns=[c for c in ("kind", "dn_mm", "length_m") if c in res.columns]), how="left") if res is not None else p.links.drop(columns=["coords"])
    return Response(t.to_csv(index_label="id"), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="links.csv"'})


@router.get("/projects/{pid}/export.inp")
def export_inp(pid: str, sid: str = "base"):
    from sewerapp.io import swmm_inp
    s = _s(pid)
    try: text = swmm_inp.from_project(s.model(sid))
    except ValueError as e: raise HTTPException(400, str(e))
    return Response(text, media_type="text/plain", headers={"Content-Disposition": 'attachment; filename="model.inp"'})


STORM = {}


@router.post("/projects/{pid}/scenarios/{sid}/storm")
def storm_run(pid: str, sid: str):
    """Run the scenario on EPA SWMM 5: peaks per link, node and catchment, flooding, continuity."""
    from sewerapp.engine import storm
    s = _s(pid)
    with _lock:
        try: r = storm.run(s.model(sid))
        except (ValueError, KeyError) as e: raise HTTPException(400, str(e))
        except Exception as e: raise HTTPException(400, f"SWMM could not run the model: {e}")
        STORM[(pid, sid)] = r
    return clean(dict(summary=r["summary"], seconds=r["seconds"], links=r["links"], nodes=r["nodes"], subcatchments=r["subcatchments"]))


@router.get("/projects/{pid}/scenarios/{sid}/storm/series")
def storm_series(pid: str, sid: str, kind: str, id: str, attr: str):
    from sewerapp.engine import storm
    r = STORM.get((pid, sid))
    if not r: raise HTTPException(400, "run the storm first")
    try: return dict(kind=kind, id=id, attr=attr, series=storm.series(r["out"], kind, id, attr))
    except StopIteration: raise HTTPException(404, f"no {kind} {id}")
    except AttributeError: raise HTTPException(400, f"no attribute {attr}")


@router.get("/projects/{pid}")
def info(pid: str):
    _s(pid); return _info(pid)


@router.get("/projects/{pid}/save")
def save(pid: str, sid: str = "base"):
    s = _s(pid); p = s.model(sid)
    f = os.path.join(tempfile.mkdtemp(), "project.gpkg"); gpkg_project.save(p, f)
    name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in p.name).strip() or "project"
    return Response(open(f, "rb").read(), media_type="application/geopackage+sqlite3",
                    headers={"Content-Disposition": f'attachment; filename="{name}.gpkg"'})


class CopyS(BaseModel):
    name: str | None = None


@router.post("/projects/{pid}/scenarios/{sid}/copy")
def copy_scenario(pid: str, sid: str, b: CopyS):
    s = _s(pid)
    with _lock: c = s.copy_scenario(sid, b.name)
    return _info(pid) | dict(created=c.id)


@router.get("/projects/{pid}/scenarios/{sid}/model")
def model(pid: str, sid: str):
    """Nodes, links and catchments as GeoJSON in lon/lat, every attribute included, keyed by id."""
    s = _s(pid)
    with _lock: p = s.model(sid)
    n = p.nodes; lon, lat = coords.to_display(p.crs, n.x.values, n.y.values); ll = dict(zip(n.index, zip(lon, lat)))
    nodes = [dict(type="Feature", id=i, geometry=dict(type="Point", coordinates=[float(ll[i][0]), float(ll[i][1])]),
                  properties=clean(dict(id=i, **r))) for i, r in zip(n.index, n.to_dict("records"))]
    links = []
    for i, r in zip(p.links.index, p.links.to_dict("records")):
        c = r.pop("coords")
        if isinstance(c, list) and len(c) >= 2:
            a = np.array(c); x, y = coords.to_display(p.crs, a[:, 0], a[:, 1]); line = [[float(u), float(v)] for u, v in zip(x, y)]
        else:
            line = [list(map(float, ll[r["from_node"]])), list(map(float, ll[r["to_node"]]))]
        links.append(dict(type="Feature", id=i, geometry=dict(type="LineString", coordinates=line), properties=clean(dict(id=i, **r))))
    catch = []
    for i, r in zip(p.catchments.index, p.catchments.to_dict("records")):
        c = r.pop("coords")
        if isinstance(c, list) and len(c) >= 3:
            a = np.array(c); x, y = coords.to_display(p.crs, a[:, 0], a[:, 1])
            catch.append(dict(type="Feature", id=i, geometry=dict(type="Polygon", coordinates=[[[float(u), float(v)] for u, v in zip(x, y)]]),
                              properties=clean(dict(id=i, **r))))
    return dict(nodes=dict(type="FeatureCollection", features=nodes), links=dict(type="FeatureCollection", features=links),
                catchments=dict(type="FeatureCollection", features=catch), settings=clean(p.settings),
                loads=clean({k: v for k, v in p.load_sets.items()}))


@router.get("/projects/{pid}/scenarios/{sid}/results")
def results(pid: str, sid: str):
    s = _s(pid)
    with _lock: res, summ = s.solve(sid)
    if res is None: return dict(summary=clean(summ), links={})
    cols = [c for c in ["dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "s_pc", "over_limit", "over_vmax", "surcharged",
                        "negative_slope", "q_check_ls", "v_check_ms", "under_vmin"] if c in res.columns]
    out = res[cols].copy()
    for c in out.columns:
        if out[c].dtype.kind == "f": out[c] = out[c].round(4)
    return dict(summary=clean(summ), links=clean({i: r for i, r in zip(out.index, out.to_dict("records"))}))


class Edit(BaseModel):
    op: str
    model_config = dict(extra="allow")


def _from_map(p, e):
    """Positions drawn on the map (lon/lat) into project coordinates."""
    if "lon" in e and "lat" in e:
        x, y = coords.from_display(p.crs, e.pop("lon"), e.pop("lat")); e["x"], e["y"] = float(x), float(y)
    if e.get("coords_ll"):
        a = np.array(e.pop("coords_ll")); x, y = coords.from_display(p.crs, a[:, 0], a[:, 1])
        e["coords"] = [[float(u), float(v)] for u, v in zip(x, y)]
    return e


@router.post("/projects/{pid}/scenarios/{sid}/edit")
def edit(pid: str, sid: str, e: Edit):
    s = _s(pid)
    with _lock:
        try:
            ev = _from_map(s.model(sid), e.model_dump())
            structural = s.edit(sid, ev)
        except (ValueError, KeyError) as x:
            raise HTTPException(400, str(x))
        _, summ = s.solve(sid)
    return dict(summary=clean(summ), structural=structural, scenario=s.scenarios[sid].to_dict())


@router.post("/projects/{pid}/scenarios/{sid}/design")
def run_design(pid: str, sid: str, load_set: str | None = None):
    """Automated design into the scenario (undoable): sizes by the d/D limit at the size's minimum gradient, then the
    re-lay with crowns matched and minimum cover."""
    s = _s(pid)
    with _lock:
        e = dict(op="design", load_set=load_set)
        try: s.edit(sid, e)
        except (ValueError, KeyError, RuntimeError) as x: raise HTTPException(400, str(x))
        _, summ = s.solve(sid)
    return dict(summary=clean(summ), report=clean(s.scenarios[sid].edits[-1].get("report", {})), structural=True,
                scenario=s.scenarios[sid].to_dict())


@router.get("/tools")
def g_tools():
    return GTOOLS


GTOOLS = [
    dict(name="design", menu="Design", label="Design: size every conduit and lay it (crowns matched, minimum cover)",
         endpoint="POST /api/g/projects/{pid}/scenarios/{sid}/design", script="engine/design_general.py"),
    dict(name="storm", menu="Stormwater", label="Run on EPA SWMM 5 (rain, catchments, dynamic routing)",
         endpoint="POST /api/g/projects/{pid}/scenarios/{sid}/storm", script="engine/storm.py"),
    dict(name="export_inp", menu="File", label="Export as an EPA SWMM 5 input file (.inp)",
         endpoint="GET /api/g/projects/{pid}/export.inp?sid={sid}", script="io/swmm_inp.py"),
    dict(name="import_gis", menu="File", label="Import a network from GIS layers (nodes + links, field mapping)",
         endpoint="POST /api/g/projects/import_gis", script="io/gis_import.py"),
    dict(name="export_dxf", menu="File", label="Export a DXF drawing (links by size, nodes, labels)",
         endpoint="GET /api/g/projects/{pid}/export.dxf?sid={sid}", script="io/gis_import.py"),
    dict(name="export_csv", menu="File", label="Export links and results as CSV",
         endpoint="GET /api/g/projects/{pid}/export.csv?sid={sid}", script="api/general_api.py"),
    dict(name="checks", menu="Checks", label="Failing links: over the d/D limit, over v max, surcharged, flat or adverse",
         endpoint="GET /api/g/projects/{pid}/scenarios/{sid}/checks", script="engine/steady.py"),
]


@router.get("/projects/{pid}/scenarios/{sid}/checks")
def checks(pid: str, sid: str):
    s = _s(pid)
    with _lock: res, summ = s.solve(sid)
    if res is None: return dict(summary=clean(summ), rows=[])
    flags = [c for c in ("over_limit", "over_vmax", "surcharged", "negative_slope", "under_vmin") if c in res.columns]
    bad = res[res[flags].any(axis=1)]
    return dict(summary=clean(summ), rows=clean([dict(id=i, **r) for i, r in zip(bad.index, bad[["dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "s_pc"] + flags].round(4).to_dict("records"))]))


@router.post("/projects/{pid}/scenarios/{sid}/undo")
def undo(pid: str, sid: str):
    s = _s(pid)
    with _lock: s.undo(sid); _, summ = s.solve(sid)
    return dict(summary=clean(summ), scenario=s.scenarios[sid].to_dict())


@router.post("/projects/{pid}/scenarios/{sid}/redo")
def redo(pid: str, sid: str):
    s = _s(pid)
    with _lock: s.redo_(sid); _, summ = s.solve(sid)
    return dict(summary=clean(summ), scenario=s.scenarios[sid].to_dict())


@router.get("/projects/{pid}/scenarios/{sid}/profile")
def profile(pid: str, sid: str, start: str, end: str | None = None):
    """From node `start` down to `end` or the last node: chainage, ground, invert, crown, water surface per link."""
    s = _s(pid)
    with _lock: p = s.model(sid); res, _ = s.solve(sid)
    leave = {f: i for i, f in zip(p.links.index, p.links.from_node)}
    if start not in leave: raise HTTPException(400, f"no link leaves {start}")
    rows, ch, i, seen = [], 0.0, leave[start], set()
    while i is not None and i not in seen:
        seen.add(i); L = p.links.loc[i]
        if L.kind == "pump": break                         # a gravity long section ends at the station
        D = (L.inside_mm or 0) / 1000.0
        r = res.loc[i] if res is not None and i in res.index else None
        dd = float(r.d_over_D) if r is not None and r.d_over_D == r.d_over_D else 0.0
        rows.append(clean(dict(link=i, kind=L.kind, from_node=L.from_node, to_node=L.to_node, ch0=ch, ch1=ch + float(L.length_m),
                               ground0=p.nodes.ground[L.from_node], ground1=p.nodes.ground[L.to_node],
                               inv0=L.up_inv, inv1=L.dn_inv, crown0=L.up_inv + D, crown1=L.dn_inv + D,
                               water0=L.up_inv + dd * D, water1=L.dn_inv + dd * D, dn_mm=L.dn_mm,
                               v_ms=None if r is None else r.v_ms)))
        ch += float(L.length_m)
        if L.to_node == end: break
        i = leave.get(L.to_node)
    return rows
