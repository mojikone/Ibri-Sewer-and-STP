"""The general app's API (/api/g): projects (new, sample, open, save), scenarios (copy, undo, redo), edits by element
id with instant re-solve, the model and results for the map, the profile. Positions from the map arrive as lon/lat
and are converted at this one boundary (api/coords.py)."""
import io, json, math, os, pickle, re, tempfile, threading, itertools, time
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


# ---- snapshots: each open project is written to disk a moment after it changes, so a page reload or a restart of
# the app finds it again. On when W19_AUTOSAVE_DIR is set (`python -m sewerapp.api` sets it); off in tests and imports.
AUTOSAVE = os.environ.get("W19_AUTOSAVE_DIR")
KEEP_DAYS, KEEP_N = 7, 12
_timers: dict[str, threading.Timer] = {}


def _snap(pid): return os.path.join(AUTOSAVE, f"{pid}.pkl")


def snapshot(pid):
    if not AUTOSAVE or pid not in SESSIONS: return None
    os.makedirs(AUTOSAVE, exist_ok=True)
    with _lock: st = SESSIONS[pid].state()                   # lists copied under the lock; the base is never changed in place
    tmp = _snap(pid) + ".tmp"
    with open(tmp, "wb") as f: pickle.dump(st, f, protocol=5)
    os.replace(tmp, _snap(pid)); return _snap(pid)


def schedule(pid, delay=2.0):
    if not AUTOSAVE or pid not in SESSIONS: return
    t = _timers.pop(pid, None)
    if t: t.cancel()
    t = threading.Timer(delay, snapshot, args=(pid,)); t.daemon = True; _timers[pid] = t; t.start()


def _restore(pid):
    if not AUTOSAVE or not re.fullmatch(r"p\d+", pid) or not os.path.exists(_snap(pid)): return None
    with open(_snap(pid), "rb") as f: st = pickle.load(f)
    SESSIONS[pid] = Session.from_state(st); return SESSIONS[pid]


def _init_autosave():
    """Drop snapshots older than KEEP_DAYS or beyond the newest KEEP_N, and number new projects after the kept ones."""
    global _ids
    if not AUTOSAVE or not os.path.isdir(AUTOSAVE): return
    fs = sorted((f for f in os.listdir(AUTOSAVE) if re.fullmatch(r"p\d+\.pkl", f)), key=lambda f: -os.path.getmtime(os.path.join(AUTOSAVE, f)))
    for k, f in enumerate(fs):
        if k >= KEEP_N or time.time() - os.path.getmtime(os.path.join(AUTOSAVE, f)) > KEEP_DAYS * 86400: os.remove(os.path.join(AUTOSAVE, f))
    left = [int(f[1:-4]) for f in os.listdir(AUTOSAVE) if re.fullmatch(r"p\d+\.pkl", f)]
    if left: _ids = itertools.count(max(left) + 1)


def _s(pid):
    if pid not in SESSIONS:
        with _lock:
            if pid not in SESSIONS and _restore(pid) is None: raise HTTPException(404, f"no open project {pid}")
    return SESSIONS[pid]


def _open(project):
    pid = f"p{next(_ids)}"; SESSIONS[pid] = Session(pid, project); schedule(pid, 0.5); return pid


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
    """A project file; when it carries its scenarios (saved by this app since batch 2) they all come back, opened at
    the one it was saved from."""
    d = tempfile.mkdtemp(); f = os.path.join(d, "upload.gpkg"); open(f, "wb").write(await file.read())
    try: p, extra = gpkg_project.load(f)
    except Exception as e: raise HTTPException(400, f"not a project file: {e}")
    ss = (extra or {}).get("session")
    with _lock:
        if not ss: pid = _open(p); return _info(pid)
        try:
            base = gpkg_project.project_from_dict(ss["base"])
            from sewerapp.model.workspace import Scenario
            pid = _open(base); s = SESSIONS[pid]; s.scenarios = {}
            for c in ss["scenarios"]:
                sc = Scenario(c["id"], c["name"], c.get("parent"), c["edits"]); sc.fixed = c.get("fixed", 0); s.scenarios[c["id"]] = sc
            s._n = max([int(k[1:]) for k in s.scenarios if re.fullmatch(r"S\d+", k)] or [0])
            s.routes = ss.get("routes", []); s.symbology = ss.get("symbology")
            for k in s.scenarios: s.model(k)                   # every scenario replays: a broken file fails here, not later
        except Exception as e:
            SESSIONS.pop(pid, None); raise HTTPException(400, f"the file's scenarios could not be rebuilt: {e}")
    return _info(pid) | dict(current=ss.get("current", "base") if ss.get("current") in s.scenarios else "base")


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


@router.get("/projects/{pid}/scenarios/{sid}/quantities")
def quantities(pid: str, sid: str):
    """Pipes by size and by size and depth band, manholes by type and depth band (the team's BOQ structure)."""
    from sewerapp.engine import quantities as qty
    s = _s(pid)
    with _lock: p = s.model(sid)
    return clean(qty.quantities(p))


@router.get("/projects/{pid}/export.kmz")
def export_kmz(pid: str, sid: str = "base"):
    from sewerapp.io import kmz
    s = _s(pid)
    with _lock: p = s.model(sid); res, _ = s.solve(sid)
    try: data = kmz.kmz_bytes(p, res, f"{p.name} - {s.scenarios[sid].name}")
    except ValueError as e: raise HTTPException(400, str(e))
    return Response(data, media_type="application/vnd.google-earth.kmz", headers={"Content-Disposition": 'attachment; filename="network.kmz"'})


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


@router.get("/projects/{pid}/scenarios/{sid}/storm/frame")
def storm_frame(pid: str, sid: str, period: int, attr: str = "capacity"):
    from sewerapp.engine import storm
    r = STORM.get((pid, sid))
    if not r: raise HTTPException(400, "run the storm first")
    try: return storm.frame(r["out"], period, attr)
    except KeyError: raise HTTPException(400, f"no attribute {attr}")


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
    """The GeoPackage: its layers are the scenario on screen (what QGIS shows); every scenario is kept inside it as the
    base model and each scenario's edits, so Open brings them all back."""
    s = _s(pid)
    with _lock:
        p = s.model(sid)
        ss = dict(version=1, current=sid, base=gpkg_project.project_dict(s.base), routes=getattr(s, "routes", []), symbology=getattr(s, "symbology", None),
                  scenarios=[dict(id=c.id, name=c.name, parent=c.parent, edits=clean(c.edits), fixed=c.fixed) for c in s.scenarios.values()])
    f = os.path.join(tempfile.mkdtemp(), "project.gpkg"); gpkg_project.save(p, f, extra=dict(session=ss))
    name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in p.name).strip() or "project"
    return Response(open(f, "rb").read(), media_type="application/geopackage+sqlite3",
                    headers={"Content-Disposition": f'attachment; filename="{name}.gpkg"'})


class CopyS(BaseModel):
    name: str | None = None


class Rename(BaseModel):
    name: str


@router.post("/projects/{pid}/scenarios/{sid}/rename")
def rename_scenario(pid: str, sid: str, b: Rename):
    s = _s(pid)
    if sid not in s.scenarios: raise HTTPException(404, sid)
    if not b.name.strip(): raise HTTPException(400, "a scenario needs a name")
    with _lock: s.scenarios[sid].name = b.name.strip()
    return _info(pid)


@router.post("/projects/{pid}/scenarios/{sid}/delete")
def delete_scenario(pid: str, sid: str):
    """Delete a scenario and the scenarios copied from it (the base stays)."""
    s = _s(pid)
    if sid == "base": raise HTTPException(400, "the base scenario cannot be deleted")
    if sid not in s.scenarios: raise HTTPException(404, sid)
    with _lock:
        gone, grow = {sid}, True
        while grow:
            add = {k for k, c in s.scenarios.items() if c.parent in gone and k not in gone}; grow = bool(add); gone |= add
        for k in gone:
            s.scenarios.pop(k, None); s.external.pop(k, None); STORM.pop((pid, k), None)
        s._cache = {}
    return _info(pid) | dict(deleted=sorted(gone))


@router.get("/projects/{pid}/compare")
def compare(pid: str, a: str, b: str):
    """Scenario b against scenario a, link by link: size, inverts, flow, velocity and d/D in both, and what changed
    (size, levels, flow only); links only in one of them."""
    s = _s(pid)
    for k in (a, b):
        if k not in s.scenarios: raise HTTPException(404, k)
    with _lock:
        pa = s.model(a); ra, _ = s.solve(a); pb = s.model(b); rb, _ = s.solve(b)
    A, B = pa.links, pb.links; both = A.index.intersection(B.index)
    t = pd.DataFrame(index=both)
    for k in ("dn_mm", "up_inv", "dn_inv"): t[k + "_a"] = A.loc[both, k].astype(float); t[k + "_b"] = B.loc[both, k].astype(float)
    for k in ("q_ls", "v_ms", "d_over_D"):
        t[k + "_a"] = ra[k].reindex(both).astype(float) if ra is not None and k in ra else np.nan
        t[k + "_b"] = rb[k].reindex(both).astype(float) if rb is not None and k in rb else np.nan
    size = (t.dn_mm_a != t.dn_mm_b)
    lev = ((t.up_inv_a - t.up_inv_b).abs() > 5e-4) | ((t.dn_inv_a - t.dn_inv_b).abs() > 5e-4)
    flow = ((t.q_ls_a - t.q_ls_b).abs() > 1e-3 * t.q_ls_a.abs().clip(lower=1e-6))
    t["change"] = np.where(size, "size", np.where(lev, "levels", np.where(flow, "flow", "same")))
    ch = t[t.change != "same"].copy(); ch["dv"] = ch.v_ms_b - ch.v_ms_a
    counts = t.change.value_counts().to_dict()
    added, removed = sorted(B.index.difference(A.index)), sorted(A.index.difference(B.index))
    return clean(dict(a=a, b=b, counts=dict(size=counts.get("size", 0), levels=counts.get("levels", 0), flow=counts.get("flow", 0),
                                            same=counts.get("same", 0), added=len(added), removed=len(removed)),
                      change={**{i: c for i, c in zip(t.index, t.change) if c != "same"}, **{i: "added" for i in added}},
                      removed=removed[:500],
                      rows=[dict(id=i, **r) for i, r in zip(ch.index[:2000], ch.round(4).to_dict("records")[:2000])]))


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
    links = []; sections = (getattr(p, "meta", None) or {}).get("sections", {})
    for i, r in zip(p.links.index, p.links.to_dict("records")):
        c = r.pop("coords")
        if isinstance(c, list) and len(c) >= 2:
            a = np.array(c); x, y = coords.to_display(p.crs, a[:, 0], a[:, 1]); line = [[float(u), float(v)] for u, v in zip(x, y)]
        else:
            line = [list(map(float, ll[r["from_node"]])), list(map(float, ll[r["to_node"]]))]
        if i in p.sections:
            from sewerapp.engine.sections import label as _seclabel
            r["section"] = _seclabel(p.sections[i]); r["sec"] = p.sections[i]
        elif i in sections: r["section"] = sections[i]
        links.append(dict(type="Feature", id=i, geometry=dict(type="LineString", coordinates=line), properties=clean(dict(id=i, **r))))
    catch = []
    for i, r in zip(p.catchments.index, p.catchments.to_dict("records")):
        c = r.pop("coords")
        if isinstance(c, list) and len(c) >= 3:
            a = np.array(c); x, y = coords.to_display(p.crs, a[:, 0], a[:, 1])
            catch.append(dict(type="Feature", id=i, geometry=dict(type="Polygon", coordinates=[[[float(u), float(v)] for u, v in zip(x, y)]]),
                              properties=clean(dict(id=i, **r))))
    return dict(nodes=dict(type="FeatureCollection", features=nodes), links=dict(type="FeatureCollection", features=links),
                catchments=dict(type="FeatureCollection", features=catch), settings=clean(p.settings), rain=clean(p.rain),
                loads=clean({k: v for k, v in p.load_sets.items()}))


@router.get("/projects/{pid}/scenarios/{sid}/results")
def results(pid: str, sid: str):
    s = _s(pid)
    with _lock: res, summ = s.solve(sid)
    if res is None: return dict(summary=clean(summ), links={})
    cols = [c for c in ["dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "s_pc", "over_limit", "over_vmax", "surcharged",
                        "negative_slope", "q_check_ls", "v_check_ms", "under_vmin", "depth_m", "yc_m", "q_full_ls"] if c in res.columns]
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


class DesignOpts(BaseModel):
    only: list[str] | None = None
    preview: bool = False


@router.post("/projects/{pid}/scenarios/{sid}/design")
def run_design(pid: str, sid: str, load_set: str | None = None, b: DesignOpts | None = None):
    """Automated design into the scenario (undoable): sizes by the d/D limit at the size's minimum gradient, then the
    re-lay with crowns matched and minimum cover. `only`: design those conduits and keep the rest; locked conduits are
    always kept. `preview`: what would change, with nothing recorded."""
    s = _s(pid); b = b or DesignOpts()
    if b.preview:
        from sewerapp.engine import design_general
        with _lock:
            p = s.model(sid)
            try: q, rep = design_general.design(p, load_set, b.only)
            except (ValueError, KeyError, RuntimeError) as x: raise HTTPException(400, str(x))
        L0, L1 = p.links, q.links
        d = pd.DataFrame(dict(dn_old=L0.dn_mm, dn_new=L1.dn_mm, up_old=L0.up_inv, up_new=L1.up_inv, dn_inv_old=L0.dn_inv, dn_inv_new=L1.dn_inv))
        moved = (d.dn_old != d.dn_new) | ((d.up_old - d.up_new).abs() > 5e-4) | ((d.dn_inv_old - d.dn_inv_new).abs() > 5e-4)
        ch = d[moved & (L0.kind == "conduit")].copy(); ch["d_up"] = ch.up_new - ch.up_old
        nd = (p.nodes.invert - q.nodes.invert).abs() > 5e-4
        return clean(dict(preview=True, report=rep, links_changed=int(len(ch)), sizes_changed=int((ch.dn_old != ch.dn_new).sum()),
                          nodes_moved=int(nd.sum()), rows=[dict(id=i, **r) for i, r in zip(ch.index[:3000], ch.round(4).to_dict("records")[:3000])]))
    with _lock:
        e = dict(op="design", load_set=load_set, only=b.only)
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
    dict(name="assistant", menu="Assistant", label="Ask the design assistant about this project (Claude, tool use)",
         endpoint="POST /api/g/assistant", script="assistant/gtools.py"),
    dict(name="open_sewergems", menu="File", label="Open a SewerGEMS model with all its scenarios (exported through the bridge)",
         endpoint="GET /api/g/sewergems/exports; POST /api/g/projects/open_sewergems/{name}", script="io/sewergems_export.py"),
    dict(name="checks", menu="Checks", label="Failing links: over the d/D limit, over v max, surcharged, flat or adverse",
         endpoint="GET /api/g/projects/{pid}/scenarios/{sid}/checks", script="engine/steady.py"),
    dict(name="quantities", menu="Quantities", label="Quantities: pipes by size and depth band, manholes by type and depth (the BOQ structure)",
         endpoint="GET /api/g/projects/{pid}/scenarios/{sid}/quantities", script="engine/quantities.py"),
    dict(name="export_kmz", menu="File", label="Export a KMZ for Google Earth (pipes by size, structures)",
         endpoint="GET /api/g/projects/{pid}/export.kmz?sid={sid}", script="io/kmz.py"),
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


def _downstream(p, start, end=None):
    """The links from node `start` following the flow, to `end` or the last node; a gravity section ends at a pump."""
    leave = {f: i for i, f in zip(p.links.index, p.links.from_node)}
    out, i, seen = [], leave.get(start), set()
    while i is not None and i not in seen:
        seen.add(i); L = p.links.loc[i]
        if L.kind == "pump": break
        out.append((i, False))
        if L.to_node == end: return out
        i = leave.get(L.to_node)
    return None if end else out


def _shortest(p, a, b):
    """Shortest route by length from node a to node b through the network in either direction: [(link, reversed)]."""
    import heapq
    if a == b: return []
    adj = {}
    for i, f, t, l in zip(p.links.index, p.links.from_node, p.links.to_node, p.links.length_m):
        w = float(l) if l == l and l > 0 else 1.0
        adj.setdefault(f, []).append((t, i, False, w)); adj.setdefault(t, []).append((f, i, True, w))
    dist, prev, q = {a: 0.0}, {}, [(0.0, a)]
    while q:
        d, n = heapq.heappop(q)
        if n == b: break
        if d > dist[n]: continue
        for m, i, rev, w in adj.get(n, ()):
            if d + w < dist.get(m, math.inf): dist[m] = d + w; prev[m] = (n, i, rev); heapq.heappush(q, (d + w, m))
    if b not in prev: return None
    out, n = [], b
    while n != a: n0, i, rev = prev[n]; out.append((i, rev)); n = n0
    return out[::-1]


def _ends(p, x, first):
    """A route end given as a node, or as a pipe (the route then starts or ends with that whole pipe)."""
    if x in p.nodes.index: return [(x, [])]
    if x in p.links.index:
        L = p.links.loc[x]
        # starting with a pipe: walk it from either end; ending with one: arrive at either end and walk through it
        return ([(L.to_node, [(x, False)]), (L.from_node, [(x, True)])] if first else
                [(L.from_node, [(x, False)]), (L.to_node, [(x, True)])])
    raise HTTPException(400, f"no node or pipe {x}")


def route(p, start, end=None, via=()):
    """The route of a long section: with no end, downstream to the outfall (a pump ends it); with an end (and any via
    points), the flow path when it reaches the end, otherwise the shortest path through the network."""
    if not end and not via:
        if start in p.links.index: L = p.links.loc[start]; return [(start, False)] + (_downstream(p, L.to_node) or [])
        if start not in p.nodes.index: raise HTTPException(400, f"no node or pipe {start}")
        r = _downstream(p, start)
        if not r: raise HTTPException(400, f"no pipe leaves {start}")
        return r
    stops = [start, *via, end] if end else [start, *via]
    legs, here = [], None                                   # here: (node, links so far)
    for k, x in enumerate(stops):
        opts = _ends(p, x, first=(k == 0))
        if k == 0: here = [(n, list(pre)) for n, pre in opts]; continue
        best = None
        for n0, pre0 in here:
            for n1, tail in opts:
                arrive = n1 if not tail else (p.links.loc[tail[0][0]].from_node if not tail[0][1] else p.links.loc[tail[0][0]].to_node)
                leg = _downstream(p, n0, arrive) if arrive != n0 else []
                leg = leg if leg is not None else _shortest(p, n0, arrive)
                if leg is None: continue
                cand = pre0 + leg + tail
                ln = sum(float(p.links.length_m[i]) for i, _ in cand)
                if best is None or ln < best[0]: best = (ln, n1, cand)
        if best is None: raise HTTPException(400, f"no route from {stops[k - 1]} to {x}")
        here = [(best[1], best[2])]
    return here[0][1]


# ---- reference layers: a GIS layer drawn under the network for orientation (plots, roads, a DXF); display only
@router.post("/projects/{pid}/reference")
def add_reference(pid: str, file: UploadFile = File(...)):
    from sewerapp.io import gis_import
    import shapely
    s = _s(pid); crs = s.base.crs
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, os.path.basename(file.filename or "layer")); open(f, "wb").write(file.file.read())
        try: g = gis_import.read_layer(f)
        except Exception as e: raise HTTPException(400, f"could not read {file.filename}: {e}")
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    if not len(g): raise HTTPException(400, f"{file.filename} holds no geometry")
    if len(g) > 150000: raise HTTPException(400, f"{len(g)} features: too many to draw (150,000 at most)")
    if crs and g.crs and g.crs.to_epsg() != crs: g = g.to_crs(crs)              # no CRS: taken as the project's own
    geom = shapely.simplify(g.geometry.values, 0.05)                              # 5 cm: invisible on screen, fewer vertices
    geom = shapely.transform(geom, lambda xy: np.column_stack(coords.to_display(crs, xy[:, 0], xy[:, 1])))
    cols = [c for c in g.columns if c != "geometry"][:12]
    props = g[cols].copy()
    for c in cols:
        if not pd.api.types.is_numeric_dtype(props[c]): props[c] = props[c].astype(str)
    feats = [dict(type="Feature", properties={k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in zip(cols, row)},
                  geometry=json.loads(shapely.to_geojson(gm))) for row, gm in zip(props.itertuples(index=False, name=None), geom)]
    kinds = sorted({t for t in g.geom_type.unique()})
    ref = dict(id=f"r{len(getattr(s, 'refs', [])) + 1}_{int(time.time()) % 100000}", name=os.path.splitext(os.path.basename(file.filename or "layer"))[0],
               count=len(feats), geom=kinds, fields=cols, crs=g.crs.to_epsg() if g.crs else None,
               geojson=dict(type="FeatureCollection", features=feats))
    with _lock: s.refs = getattr(s, "refs", []) + [ref]
    schedule(pid)
    return clean(ref)


@router.get("/projects/{pid}/reference")
def list_references(pid: str):
    return clean(getattr(_s(pid), "refs", []))


@router.post("/projects/{pid}/reference/{rid}/delete")
def delete_reference(pid: str, rid: str):
    s = _s(pid)
    with _lock: s.refs = [r for r in getattr(s, "refs", []) if r["id"] != rid]
    schedule(pid); return dict(ok=True)


class Route(BaseModel):
    name: str
    start: str
    end: str | None = None
    via: str | None = None


@router.get("/projects/{pid}/symbology")
def get_symbology(pid: str):
    """The project's symbology: named definitions of colour codings and labels per element type, and the active one
    (built and read by the editor, web/editor/symbology.js); null until one is saved."""
    return getattr(_s(pid), "symbology", None)


@router.post("/projects/{pid}/symbology")
def put_symbology(pid: str, b: dict):
    s = _s(pid)
    if not isinstance(b.get("defs"), dict) or not b["defs"] or b.get("active") not in b["defs"]:
        raise HTTPException(400, "symbology needs named definitions and an active one")
    if len(json.dumps(b)) > 2_000_000: raise HTTPException(400, "symbology too large")
    with _lock: s.symbology = b
    return dict(ok=True)


class KmzStyle(BaseModel):
    sid: str = "base"
    title: str | None = None
    classes: list = []                                     # [[label, "#rrggbb"], ...] in legend order
    links: dict = {}                                       # link id -> "#rrggbb"
    labels: dict = {}                                      # link id -> label text


@router.post("/projects/{pid}/export.kmz")
def export_kmz_styled(pid: str, b: KmzStyle):
    """The KMZ coloured and labelled as the map shows it (the active colouring and labels sent by the editor)."""
    from sewerapp.io import kmz
    s = _s(pid)
    if b.sid not in s.scenarios: raise HTTPException(404, f"no scenario {b.sid}")
    with _lock: p = s.model(b.sid); res, _ = s.solve(b.sid)
    try: data = kmz.kmz_bytes(p, res, f"{p.name} - {s.scenarios[b.sid].name}", style=b.model_dump())
    except ValueError as e: raise HTTPException(400, str(e))
    return Response(data, media_type="application/vnd.google-earth.kmz", headers={"Content-Disposition": 'attachment; filename="network.kmz"'})


@router.get("/projects/{pid}/routes")
def list_routes(pid: str):
    return getattr(_s(pid), "routes", [])


@router.post("/projects/{pid}/routes")
def save_route(pid: str, b: Route):
    s = _s(pid)
    if not b.name.strip() or not b.start.strip(): raise HTTPException(400, "a route needs a name and a start")
    with _lock:
        rs = [r for r in getattr(s, "routes", []) if r["name"] != b.name.strip()]
        s.routes = rs + [dict(name=b.name.strip(), start=b.start.strip(), end=(b.end or "").strip(), via=(b.via or "").strip())]
    return s.routes


@router.post("/projects/{pid}/routes/delete")
def delete_route(pid: str, b: Rename):
    s = _s(pid)
    with _lock: s.routes = [r for r in getattr(s, "routes", []) if r["name"] != b.name]
    return s.routes


@router.get("/projects/{pid}/scenarios/{sid}/profile")
def profile(pid: str, sid: str, start: str, end: str | None = None, via: str | None = None):
    """A long section along a route (see `route`): per link, in route order, the chainage, ground, invert, crown and
    water surface at both ends, with the size, gradient, flow, velocity and d/D; `reversed` marks a link walked against
    its flow."""
    s = _s(pid)
    with _lock: p = s.model(sid); res, _ = s.solve(sid)
    vias = [v.strip() for v in (via or "").split(",") if v.strip()]
    links = route(p, start.strip(), (end or "").strip() or None, vias)
    on = {i for i, _ in links}
    at = {}                                                  # node -> the links that meet it and are not on the route
    for i, f, t in zip(p.links.index, p.links.from_node, p.links.to_node):
        if i not in on: at.setdefault(f, []).append((i, "out")); at.setdefault(t, []).append((i, "in"))

    from sewerapp.engine.sections import label as _seclab
    secs = p.sections or {}
    bore = lambda i, L: secs[i]["rise_m"] * 1000.0 if i in secs else L.inside_mm      # mm: a section's rise stands for its bore
    def joins(n):
        out = []
        for i, d in at.get(n, ()):
            L = p.links.loc[i]; pump = L.kind == "pump"
            inv = p.nodes.invert[n] if pump else (L.up_inv if d == "out" else L.dn_inv)
            r = res.loc[i] if res is not None and i in res.index else None
            out.append(clean(dict(link=i, kind=L.kind, dir=d, other=L.to_node if d == "out" else L.from_node, dn_mm=L.dn_mm,
                                  inside_mm=0 if pump else bore(i, L), invert=inv, transfer=bool(L.transfer),
                                  section=_seclab(secs[i]) if i in secs else None,
                                  q_ls=None if r is None or "q_ls" not in r else r.q_ls)))
        return sorted(out, key=lambda j: (j["dir"] != "in", -(j["inside_mm"] or 0)))
    st = STORM.get((pid, sid)); sn = st["nodes"] if st else {}
    head = lambda n: sn[n]["head_peak"] if n in sn else None
    rows, ch = [], 0.0
    for i, rev in links:
        L = p.links.loc[i]; n0, n1 = (L.to_node, L.from_node) if rev else (L.from_node, L.to_node)
        D = (bore(i, L) or 0) / 1000.0 if L.kind != "pump" else 0.0
        r = res.loc[i] if res is not None and i in res.index else None
        dd = float(r.d_over_D) if r is not None and "d_over_D" in r and r.d_over_D == r.d_over_D else 0.0
        up, dn = (L.up_inv, L.dn_inv) if L.kind != "pump" else (p.nodes.invert[L.from_node], p.nodes.invert[L.to_node])
        i0, i1 = (dn, up) if rev else (up, dn)
        ln = float(L.length_m) if L.length_m == L.length_m else 0.0
        g = lambda k: None if r is None or k not in r else r[k]
        rows.append(clean(dict(link=i, kind=L.kind, reversed=bool(rev), from_node=n0, to_node=n1, ch0=ch, ch1=ch + ln, length_m=ln,
                               ground0=p.nodes.ground[n0], ground1=p.nodes.ground[n1], inv0=i0, inv1=i1, crown0=i0 + D, crown1=i1 + D,
                               water0=i0 + dd * D, water1=i1 + dd * D, dn_mm=L.dn_mm, section=_seclab(secs[i]) if i in secs else None,
                               slope_pc=(up - dn) / ln * 100 if ln > 0 and L.kind != "pump" else None,
                               q_ls=g("q_ls"), v_ms=g("v_ms"), d_over_D=g("d_over_D"),
                               fail=bool(r is not None and any(bool(g(k)) for k in ("over_limit", "over_vmax", "surcharged", "negative_slope"))),
                               node_inv1=p.nodes.invert[n1], kind1=p.nodes.kind[n1], joins1=joins(n1),
                               storm0=head(n0), storm1=head(n1))))
        if len(rows) == 1: rows[0].update(node_inv0=clean(p.nodes.invert[n0]), kind0=p.nodes.kind[n0], joins0=joins(n0))
        ch += ln
    return rows


class Ask(BaseModel):
    project: str
    scenario: str = "base"
    message: str
    history: list[dict] = []
    model: str = "opus"
    selection: dict | None = None            # {table, ids}: what the engineer has selected in the editor
    route: dict | None = None                # {start, end, via}: the profile on screen


@router.get("/assistant/status")
def assistant_status():
    from sewerapp.assistant import runner
    return runner.available()


@router.post("/assistant")
def assistant(q: Ask):
    """The assistant on an open project: reads results, explains checks with guideline pages, works in new scenarios."""
    from sewerapp.assistant import gtools, runner
    st = runner.available()
    if not st["available"]: raise HTTPException(503, st["reason"])
    s = _s(q.project)
    if q.scenario not in s.scenarios: raise HTTPException(404, q.scenario)
    ctx = f"active project: {q.project}, scenario: {q.scenario}"
    sel = q.selection or {}
    if sel.get("ids"):
        ids = [str(i) for i in sel["ids"]]
        ctx += f"; selected {sel.get('table')}: {', '.join(ids[:40])}" + (f" and {len(ids) - 40} more" if len(ids) > 40 else "")
    if q.route and q.route.get("start"):
        ctx += f"; profile on screen from {q.route['start']} to {q.route.get('end') or 'the outfall'}" + (f" via {q.route['via']}" if q.route.get("via") else "")
    with _lock:
        gtools.ACTIONS.clear()
        out = runner.ask(None, q.scenario, q.message, q.history, q.model, toolset=gtools, system=runner.SYSTEM_GENERAL, context=ctx)
        out["ui_actions"] = list(gtools.ACTIONS); gtools.ACTIONS.clear()
        return clean(out)


SG_EXPORTS = os.environ.get("W19_SG_EXPORTS", r"D:\VBOX\bridge\out\w19\export")


@router.get("/sewergems/exports")
def sewergems_exports():
    """SewerGEMS models exported through the bridge (job 100), ready to open with all their scenarios."""
    if not os.path.isdir(SG_EXPORTS): return []
    out = []
    for d in sorted(os.listdir(SG_EXPORTS)):
        f = os.path.join(SG_EXPORTS, d, "scenarios.csv")
        if os.path.exists(f): out.append(dict(name=d, scenarios=max(0, len(open(f, encoding="utf-8").read().splitlines()) - 1)))
    return out


@router.get("/sewergems/models")
def sewergems_models():
    """What can be opened (exports), what can be exported (SewerGEMS models in the shared folders), the VM watcher, and
    the export jobs the app has written."""
    from sewerapp.io import bridge_jobs as B
    return dict(watcher=B.watcher(), exports=sewergems_exports(), models=B.models(), jobs=B.jobs(), shares=[g for _, g in B.SHARES])


class SgExport(BaseModel):
    guest: str
    tag: str | None = None
    run: bool = False                                      # compute every scenario on the copy before exporting


@router.post("/sewergems/export")
def sewergems_export_job(b: SgExport):
    """Write the bridge job that exports a SewerGEMS model (every scenario, results and loads) from a copy, in the VM."""
    from sewerapp.io import bridge_jobs as B
    try: return B.submit(b.guest, b.tag, b.run)
    except ValueError as e: raise HTTPException(400, str(e))


@router.get("/sewergems/jobs/{name}")
def sewergems_job(name: str):
    from sewerapp.io import bridge_jobs as B
    if not re.fullmatch(r"w19x_[A-Za-z0-9_-]+", name): raise HTTPException(404, name)
    return B.job(name)


def open_sewergems_folder(folder, name, crs=None):
    from sewerapp.io import sewergems_export
    p, scen, res = sewergems_export.load(folder, name, crs)
    with _lock:
        pid = _open(p); s = SESSIONS[pid]
        s.scenarios["base"].name = scen[0]["label"]; s.external["base"] = res[scen[0]["label"]]
        if scen[0].get("has_loads"): p.settings["design_load"] = scen[0]["label"]
        for sc in scen[1:]:
            c = s.copy_scenario("base", sc["label"])
            own = [dict(op="set_setting", path="design_load", value=sc["label"])] if sc.get("has_loads") else []
            s.edit_many(c.id, sc["edits"] + own, fixed=True)   # each scenario solves at its own loads; not undoable
            s.external[c.id] = res[sc["label"]]
    return pid


@router.post("/projects/open_sewergems/{name}")
def open_sewergems(name: str, crs: int | None = 32640):
    folder = os.path.join(SG_EXPORTS, name)
    if not os.path.exists(os.path.join(folder, "scenarios.csv")): raise HTTPException(404, f"no export {name}")
    try: pid = open_sewergems_folder(folder, f"SewerGEMS: {name}", crs)
    except Exception as e: raise HTTPException(400, f"could not read the export: {e}")
    return _info(pid)


@router.get("/projects/{pid}/scenarios/{sid}/stored")
def stored(pid: str, sid: str):
    """The results SewerGEMS stored for this scenario, by link id (empty when the scenario has none)."""
    s = _s(pid); r = s.external.get(sid)
    if r is None: return dict(links={})
    return dict(links=clean({i: x for i, x in zip(r.index, r.round(4).to_dict("records"))}))


@router.get("/projects/{pid}/scenarios/{sid}/compare_stored")
def compare_stored(pid: str, sid: str):
    """The app's engine against SewerGEMS's stored results, link by link (flow %, velocity m/s, d/D)."""
    s = _s(pid); r = s.external.get(sid)
    if r is None: raise HTTPException(400, "this scenario holds no SewerGEMS results")
    with _lock: res, _ = s.solve(sid)
    if res is None: raise HTTPException(400, "the scenario does not solve")
    j = res[["q_ls", "v_ms", "d_over_D"]].join(r[["q_ls", "v_ms", "d_over_D"]], rsuffix="_sg", how="inner")
    dq = (j.q_ls - j.q_ls_sg) / j.q_ls_sg.where(j.q_ls_sg.abs() > 1e-9) * 100
    return clean(dict(links=int(len(j)), pc_flow_within_0_1=round(float((dq.abs() < 0.1).mean() * 100), 3),
                      largest_flow_pc=float(dq.abs().max()), dv_p05=float((j.v_ms - j.v_ms_sg).quantile(.05)),
                      dv_p95=float((j.v_ms - j.v_ms_sg).quantile(.95))))


@router.get("/projects/{pid}/scenarios/{sid}/section_check")
def section_check(pid: str, sid: str):
    """The app's box and channel hydraulics against SewerGEMS, independent of the hydrology: at SewerGEMS's own flow in
    each section conduit, the app's normal and critical depth (engine/sections.py, on the conduit's gradient) against the
    normal and critical depth SewerGEMS reports. Needs an export with sections and results (run the scenarios first)."""
    from sewerapp.engine import sections as X
    s = _s(pid); r = s.external.get(sid)
    if r is None or "yn_sg_m" not in r: raise HTTPException(400, "no SewerGEMS section results in this scenario (export it with 'run every scenario first')")
    p = s.model(sid); ids = [i for i in r.index if i in p.sections and i in p.links.index]
    t = r.loc[ids]; t = t[(t.q_ls > 0) & t.yn_sg_m.notna()]
    if not len(t): raise HTTPException(400, "no section conduit carries a flow in SewerGEMS's results")
    L = p.links.loc[t.index]; S = ((L.up_inv - L.dn_inv) / L.length_m).to_numpy()
    code, rise, bottom, zl, zr, n = X.unpack([p.sections[i] for i in t.index])
    q = t.q_ls.to_numpy() / 1000.0
    with np.errstate(invalid="ignore", divide="ignore"):
        yn, _, full = X.normal_depth(q, S, code, rise, bottom, zl, zr, n); yc = X.critical_depth(q, code, rise, bottom, zl, zr)
    d = pd.DataFrame(dict(q_ls=t.q_ls, s_pc=S * 100, yn_m=yn, yn_sg_m=t.yn_sg_m, yc_m=yc, yc_sg_m=t.yc_sg_m, full=full), index=t.index)
    free = d[~d.full & (d.s_pc > 0)]
    dyn = (free.yn_m - free.yn_sg_m).abs(); dyc = (d.yc_m - d.yc_sg_m).abs()
    pc = dyn / free.yn_sg_m.where(free.yn_sg_m > 0) * 100
    return clean(dict(conduits=int(len(d)), compared=int(len(free)), full_or_flat=int(len(d) - len(free)),
                      yn_within_1pc=round(float((pc < 1).mean() * 100), 2) if len(pc) else None,
                      yn_max_diff_m=float(dyn.max()) if len(dyn) else None, yn_max_diff_pc=float(pc.max()) if len(pc) else None,
                      yc_max_diff_m=float(dyc.max()), rows={i: x for i, x in zip(d.index, d.round(4).to_dict("records"))}))


_init_autosave()
