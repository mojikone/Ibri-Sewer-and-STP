"""The general app's API (/api/g): projects (new, sample, open, save), scenarios (copy, undo, redo), edits by element
id with instant re-solve, the model and results for the map, the profile. Positions from the map arrive as lon/lat
and are converted at this one boundary (api/coords.py)."""
import io, json, math, os, pickle, re, tempfile, threading, itertools, time
import numpy as np, pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sewerapp.api import coords
from sewerapp.io import gpkg_project, ibri_sample
from sewerapp.model.general import Project, NODE_KINDS, LINK_KINDS
from sewerapp.model.workspace import Session

router = APIRouter(prefix="/api/g")
SESSIONS: dict[str, Session] = {}
_lock = threading.RLock()
_alock = threading.Lock()                     # the assistant: one answer at a time
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
    if not AUTOSAVE or not re.fullmatch(PID_RE, pid) or not os.path.exists(_snap(pid)): return None
    with open(_snap(pid), "rb") as f: st = pickle.load(f)
    SESSIONS[pid] = Session.from_state(st); return SESSIONS[pid]


def _init_autosave():
    """Drop snapshots older than KEEP_DAYS or beyond the newest KEEP_N, and number new projects after the kept ones."""
    global _ids
    if not AUTOSAVE or not os.path.isdir(AUTOSAVE): return
    fs = sorted((f for f in os.listdir(AUTOSAVE) if re.fullmatch(PID_RE + r"\.pkl", f)), key=lambda f: -os.path.getmtime(os.path.join(AUTOSAVE, f)))
    for k, f in enumerate(fs):
        if k >= KEEP_N or time.time() - os.path.getmtime(os.path.join(AUTOSAVE, f)) > KEEP_DAYS * 86400: os.remove(os.path.join(AUTOSAVE, f))
    left = [int(f[1:-4]) for f in os.listdir(AUTOSAVE) if re.fullmatch(r"p\d+\.pkl", f)]
    if left: _ids = itertools.count(max(left) + 1)


def _s(pid):
    if pid not in SESSIONS:
        with _lock:
            if pid not in SESSIONS and _restore(pid) is None: raise HTTPException(404, f"no open project {pid}")
    return SESSIONS[pid]


PID_RE = r"p[0-9a-f]{1,32}"                       # p40 (before 2026-11-24) or p + 16 random hex digits


def _open(project):
    # the id is the model's link (?p=...): random, so a link cannot be guessed from another (accounts come later)
    import secrets
    pid = "p" + secrets.token_hex(8)
    while pid in SESSIONS: pid = "p" + secrets.token_hex(8)
    SESSIONS[pid] = Session(pid, project); schedule(pid, 0.5); return pid


def _kinds_schema():
    from sewerapp.model.kinds import schema
    from sewerapp.io import swmm_lid as LD
    s = schema()
    s["_lid"] = dict(types=LD.TYPES, layers={k: [list(x) for x in v] for k, v in LD.LAYERS.items()}, needs=LD.NEEDS, optional=LD.OPTIONAL)
    return s


def _info(pid):
    s = SESSIONS[pid]; p = s.base
    return dict(id=pid, name=p.name, crs=p.crs, basemap=bool(p.crs), scenarios=[c.to_dict() for c in s.scenarios.values()],
                load_sets=sorted(p.load_sets), node_kinds=NODE_KINDS, link_kinds=LINK_KINDS, kind_fields=_kinds_schema(),
                catalogue=p.catalogue().nominal_mm.tolist())


class New(BaseModel):
    name: str = "New project"
    crs: int | None = None


@router.get("/projects")
def projects(request: Request):
    """The open projects, for this computer only: over a shared link each visitor sees the projects of their own
    browser (kept there) and opens others' only by their link."""
    if _remote(request): return []
    return [dict(id=k, name=s.base.name) for k, s in SESSIONS.items()]


@router.get("/env")
def env(request: Request):
    """What this installation offers the page: tools that read this computer's files only when the page is opened on
    it, and whether the SewerGEMS link (the virtual machine's bridge) is running."""
    local = not _remote(request); alive = None
    try:
        from sewerapp.io import sg_bridge
        alive = bool(sg_bridge.alive()) if hasattr(sg_bridge, "alive") else None
    except Exception: alive = None
    return dict(local=local, sewergems=alive)


@router.post("/projects/new")
def new(b: New):
    p = Project(name=b.name, crs=b.crs); p.load_sets = {"design": {}}; p.settings["design_load"] = "design"
    with _lock: pid = _open(p)
    return _info(pid)


@router.get("/samples")
def samples():
    from sewerapp.io import demo_pond
    return [dict(id=c, name=f"Ibri {c} (W18 final design)") for c in ibri_sample.CASES] + [dict(id="pond", name=demo_pond.NAME)]


@router.post("/projects/sample/{case}")
def sample(case: str):
    if case == "pond":                                          # a pond, rain and a pump with start/stop depths (storm run)
        from sewerapp.io import demo_pond
        with _lock: pid = _open(demo_pond.build())
        return _info(pid)
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
            s.routes = ss.get("routes", []); s.symbology = ss.get("symbology"); s.alternatives = ss.get("alternatives", {}) or {}
            for c in ss["scenarios"]:
                if c.get("alts"): s.scenarios[c["id"]].alts = dict(c["alts"])
            s._alt_n = int(ss.get("alt_n", 0) or 0); s._rescan()
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


def _safe_name(name, default):
    """An uploaded file's name without any folder part (a visitor's name must never choose where the file is written)."""
    b = os.path.basename((name or "").replace("\\", "/"))
    return b if b not in ("", ".", "..") else default


@router.post("/gis/fields")
async def gis_fields(file: UploadFile = File(...)):
    """The fields of an uploaded layer (GeoPackage, GeoJSON or zipped shapefile), for the field-mapping dialog."""
    from sewerapp.io import gis_import
    f = os.path.join(tempfile.mkdtemp(), _safe_name(file.filename, "layer")); open(f, "wb").write(await file.read())
    try: return gis_import.fields(f)
    except Exception as e: raise HTTPException(400, f"not a readable layer: {e}")


@router.post("/projects/import_gis")
async def import_gis(nodes: UploadFile = File(...), links: UploadFile = File(...), mapping: str = "{}", name: str = "Imported network",
                     snap_m: float = 1.0):
    """A network from a node layer and a link layer with a field mapping {"nodes": {...}, "links": {...}}."""
    import json as _json
    from sewerapp.io import gis_import
    d = tempfile.mkdtemp(); fn = os.path.join(d, "n_" + _safe_name(nodes.filename, "n")); fl = os.path.join(d, "l_" + _safe_name(links.filename, "l"))
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
    return clean(dict(summary=r["summary"], seconds=r["seconds"], links=r["links"], nodes=r["nodes"], subcatchments=r["subcatchments"], inlets=r.get("inlets") or {}))


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
                  alternatives=clean(getattr(s, "alternatives", {}) or {}), alt_n=getattr(s, "_alt_n", 0),
                  scenarios=[dict(id=c.id, name=c.name, parent=c.parent, edits=clean(c.edits), fixed=c.fixed, alts=dict(getattr(c, "alts", {}) or {})) for c in s.scenarios.values()])
    f = os.path.join(tempfile.mkdtemp(), "project.gpkg"); gpkg_project.save(p, f, extra=dict(session=ss))
    name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in p.name).strip() or "project"
    return Response(open(f, "rb").read(), media_type="application/geopackage+sqlite3",
                    headers={"Content-Disposition": f'attachment; filename="{name}.gpkg"'})


class CopyS(BaseModel):
    name: str | None = None


# ---- alternatives (F14), as SewerGEMS's: named per-category edit sets with parents, taken by scenarios
@router.get("/projects/{pid}/alternatives")
def alternatives(pid: str):
    from sewerapp.model.workspace import CATEGORIES
    s = _s(pid); A = getattr(s, "alternatives", {}) or {}
    with _lock:
        used = {sid: s.alts_of(sid) for sid in s.scenarios}
        own = {}
        from sewerapp.model.workspace import split_by_category
        for sid, sc in s.scenarios.items():
            n = {}
            for e in sc.edits:
                mine = e.get("own") if e.get("op") == "_alt" else e
                if not mine: continue
                for c, _ in split_by_category(mine): n[c] = n.get(c, 0) + 1
            own[sid] = n
    return clean(dict(categories=[dict(id=c, name=n) for c, n in CATEGORIES],
                      alternatives={c: [dict(id=k, name=v["name"], parent=v.get("parent"), edits=len(v["edits"]),
                                             used_by=[sid for sid, a in used.items() if a.get(c) == k]) for k, v in A.get(c, {}).items()] for c, _ in CATEGORIES},
                      scenarios={sid: dict(name=sc.name, alts=used[sid], own_edits=own[sid]) for sid, sc in s.scenarios.items()}))


class AltB(BaseModel):
    cat: str
    name: str | None = None
    parent: str | None = None
    from_scenario: str | None = None
    id: str | None = None


@router.post("/projects/{pid}/alternatives/new")
def alternative_new(pid: str, b: AltB):
    """A new alternative: empty, a child of another, or holding a scenario's own edits of that category."""
    from sewerapp.model.workspace import CAT_ORDER, split_by_category, CATEGORIES as CATEGORIES_
    s = _s(pid)
    if b.cat not in CAT_ORDER: raise HTTPException(400, f"no category {b.cat}")
    with _lock:
        A = s.alternatives.setdefault(b.cat, {})
        if b.parent and b.parent not in A: raise HTTPException(404, f"no alternative {b.parent}")
        edits = []
        if b.from_scenario:
            if b.from_scenario not in s.scenarios: raise HTTPException(404, f"no scenario {b.from_scenario}")
            chain, c = [], s.scenarios[b.from_scenario]
            while c: chain.append(c); c = s.scenarios.get(c.parent) if c.parent else None
            edits = [x for c in reversed(chain) for e in c.edits for own in [e.get("own") if e.get("op") == "_alt" else e] if own
                     for k, x in split_by_category(own) if k == b.cat]
        name = (b.name or "").strip() or f"{dict(CATEGORIES_)[b.cat]} {len(A) + 1}"
        aid = s.new_alternative(b.cat, name, parent=b.parent, edits=[dict(x) for x in edits])
    return alternatives(pid) | dict(created=aid)


@router.post("/projects/{pid}/alternatives/rename")
def alternative_rename(pid: str, b: AltB):
    s = _s(pid); A = s.alternatives.get(b.cat, {})
    if b.id not in A: raise HTTPException(404, f"no alternative {b.id}")
    A[b.id]["name"] = (b.name or A[b.id]["name"]).strip(); return alternatives(pid)


@router.post("/projects/{pid}/alternatives/delete")
def alternative_delete(pid: str, b: AltB):
    s = _s(pid); A = s.alternatives.get(b.cat, {})
    if b.id not in A: raise HTTPException(404, f"no alternative {b.id}")
    if any(s.alts_of(sid).get(b.cat) == b.id for sid in s.scenarios): raise HTTPException(400, "a scenario takes this alternative: give it another first")
    if any(v.get("parent") == b.id for v in A.values()): raise HTTPException(400, "this alternative has children")
    with _lock: A.pop(b.id); s._cache = {}
    return alternatives(pid)


class UseAltB(BaseModel):
    cat: str
    aid: str | None = None


@router.post("/projects/{pid}/scenarios/{sid}/alts")
def scenario_alts(pid: str, sid: str, b: UseAltB):
    """The alternative a scenario takes for a category (None: its own edits, as before)."""
    s = _s(pid)
    if sid not in s.scenarios: raise HTTPException(404, f"no scenario {sid}")
    if b.aid and b.aid not in s.alternatives.get(b.cat, {}): raise HTTPException(404, f"no alternative {b.aid}")
    with _lock:
        sc = s.scenarios[sid]; sc.alts = dict(getattr(sc, "alts", {}) or {})
        sc.alts[b.cat] = b.aid or ""                               # "" : its own edits, even when a parent takes one
        s._cache = {}
        try: _, summ = s.solve(sid)
        except Exception as x: raise HTTPException(400, f"the scenario cannot be built with it: {x}")
        skipped = (getattr(s.model(sid), "meta", {}) or {}).get("alternatives_skipped", 0)
    schedule(pid)
    return clean(dict(summary=summ, scenario=sc.to_dict(), skipped=skipped))


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
    PN, PL = (getattr(p, "props", None) or {}).get("nodes", {}), (getattr(p, "props", None) or {}).get("links", {})
    PCa = (getattr(p, "props", None) or {}).get("catchments", {}) or {}
    nodes = [dict(type="Feature", id=i, geometry=dict(type="Point", coordinates=[float(ll[i][0]), float(ll[i][1])]),
                  properties=clean(dict(id=i, **r, **({"storage": p.storage[i]} if i in getattr(p, "storage", {}) else {}),
                                        **({"tailwater": p.tailwater[i]} if i in getattr(p, "tailwater", {}) else {}),
                                        **({"ground_src": p.ground_src[i]} if i in getattr(p, "ground_src", {}) else {}),
                                        **({"props": PN[i]} if i in PN else {}))))
             for i, r in zip(n.index, n.to_dict("records"))]
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
        if i in p.infil: r["infil"] = p.infil[i]                          # the conduit's own infiltration rate
        if i in getattr(p, "pumps", {}): r["pump"] = p.pumps[i]           # a pump's capacity and start/stop depths
        if i in getattr(p, "ppipes", {}): r["ppipe"] = p.ppipes[i]        # a pressure pipe's own friction and minor loss
        if i in getattr(p, "outlets", {}): r["outlet"] = p.outlets[i]     # an orifice's or a weir's geometry
        if i in PL: r["props"] = PL[i]                                    # the kind's own fields (model/kinds.py)
        links.append(dict(type="Feature", id=i, geometry=dict(type="LineString", coordinates=line), properties=clean(dict(id=i, **r))))
    catch = []
    for i, r in zip(p.catchments.index, p.catchments.to_dict("records")):
        c = r.pop("coords")
        if isinstance(c, list) and len(c) >= 3:
            a = np.array(c); x, y = coords.to_display(p.crs, a[:, 0], a[:, 1])
            catch.append(dict(type="Feature", id=i, geometry=dict(type="Polygon", coordinates=[[[float(u), float(v)] for u, v in zip(x, y)]]),
                              properties=clean(dict(id=i, **r, **({"hydro": p.hydrology[i]} if i in getattr(p, "hydrology", {}) else {}),
                                                    **({"props": PCa[i]} if i in PCa else {})))))
    return dict(nodes=dict(type="FeatureCollection", features=nodes), links=dict(type="FeatureCollection", features=links),
                catchments=dict(type="FeatureCollection", features=catch), settings=clean(p.settings), rain=clean(p.rain),
                loads=clean({k: v for k, v in p.load_sets.items()}), unit_rows=clean(getattr(p, "unit_rows", {}) or {}), controls=clean(getattr(p, "controls", []) or []))


@router.get("/projects/{pid}/scenarios/{sid}/results")
def results(pid: str, sid: str):
    s = _s(pid)
    with _lock: res, summ = s.solve(sid)
    if res is None: return dict(summary=clean(summ), links={})
    cols = [c for c in ["dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "s_pc", "over_limit", "over_vmax", "surcharged",
                        "negative_slope", "q_check_ls", "v_check_ms", "under_vmin", "depth_m", "yc_m", "q_full_ls",
                        "hw_m", "hw_inlet_m", "hw_outlet_m", "culvert_control", "hw_over"] if c in res.columns]
    out = res[cols].copy()
    for c in out.columns:
        if out[c].dtype.kind == "f": out[c] = out[c].round(4)
    links = clean({i: r for i, r in zip(out.index, out.to_dict("records"))})
    # pumps and force mains (engine/pressure.py): their own values, on their rows only
    pcols = [c for c in ["tdh_m", "static_m", "hgl_out", "suction_m", "pump_head_m", "pump_q_ls", "op_q_ls", "op_h_m", "op_q_off_ls", "op_h_off_m",
                         "op_q_on_ls", "op_h_on_m", "pumps_running", "short", "cannot_lift", "hf_m", "hm_m", "hgl_up", "hgl_dn", "p_up_m", "p_dn_m",
                         "s_f_m_per_km", "negative_pressure"] if c in res.columns]
    if pcols:
        sub_ = res.loc[res.kind.isin(["pump", "pressure_pipe"]), pcols]
        for i, r in zip(sub_.index, sub_.to_dict("records")):
            links.setdefault(i, {}).update(clean({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if v == v and v is not None}))
    nodes = {}
    if res.attrs.get("node_hgl"):                                         # the GVF run's water level at each structure
        fl = set(res.attrs.get("flooding") or [])
        nodes = {n: dict(hgl=round(h, 4), **({"flooding": True} if n in fl else {})) for n, h in res.attrs["node_hgl"].items()}
    gcols = [c for c in ["hgl_up", "hgl_dn", "y_up_m", "y_dn_m", "regime", "surcharged_gvf"] if c in res.columns]
    if gcols:
        sub_ = res.loc[res.hgl_up.notna(), gcols] if "hgl_up" in res.columns else res.iloc[0:0]
        for i, r in zip(sub_.index, sub_.to_dict("records")):
            links.setdefault(i, {}).update(clean({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if v == v and v is not None and v != ""}))
    return dict(summary=clean(summ), links=links, **({"nodes": nodes} if nodes else {}))


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
    if e.get("via_ll"):                                               # a layout run's bends
        a = np.array(e.pop("via_ll")); x, y = coords.from_display(p.crs, a[:, 0], a[:, 1])
        e["via"] = [[float(u), float(v)] for u, v in zip(x, y)]
    if e.get("op") == "batch": e["ops"] = [_from_map(p, dict(x)) for x in (e.get("ops") or [])]
    return e


@router.post("/projects/{pid}/scenarios/{sid}/edit")
def edit(pid: str, sid: str, e: Edit, want_model: bool = Query(False, alias="model"), want_results: bool = Query(False, alias="results")):
    """One edit, solved at once. ?model=1 and ?results=1 carry the model and the results in the answer, so a drawing
    click is one round trip on a slow link (v7)."""
    s = _s(pid)
    with _lock:
        try:
            ev = _from_map(s.model(sid), e.model_dump())
            structural = s.edit(sid, ev)
        except (ValueError, KeyError) as x:
            raise HTTPException(400, str(x))
        try: _, summ = s.solve(sid)
        except Exception as x:                                            # the edit cannot be solved: it is taken back
            s.undo(sid); s.scenarios[sid].redo.pop(); s.solve(sid)
            raise HTTPException(400, f"not applied: the model could not be solved with it ({type(x).__name__}: {x})")
    made = {k: ev[k] for k in ("end_id", "mid_ids", "link_ids") if k in ev}       # what a layout run created
    if ev.get("op") == "design_inlets": made["inlets"] = ev.get("report") or {}
    out = dict(summary=clean(summ), structural=structural, scenario=s.scenarios[sid].to_dict(), **({"created": made} if made else {}))
    if want_model or structural: out["model"] = model(pid, sid)
    if want_results: out["results"] = results(pid, sid)
    return out


@router.post("/projects/{pid}/scenarios/{sid}/loadbuilder")
async def loadbuilder(pid: str, sid: str, file: UploadFile = File(...), field: str = "", scale: float = 1.0, target: str = "load",
                      unit: str = "", load_set: str = "", max_dist: float = 0.0, apply: bool = False):
    """LoadBuilder: a layer's values to the nearest structures; a preview, or applied as one undoable edit."""
    import tempfile
    from sewerapp.engine import tools_v4
    from sewerapp.io import gis_import
    s = _s(pid); d = tempfile.mkdtemp(prefix="w19lb_"); path = os.path.join(d, _safe_name(file.filename, "layer.gpkg"))
    open(path, "wb").write(await file.read())
    try: g = gis_import.read_layer(path)
    except Exception as x: raise HTTPException(400, f"not a GIS layer: {x}")
    if not field:
        return dict(fields=[c for c in g.columns if c != "geometry" and pd.api.types.is_numeric_dtype(g[c])], features=int(len(g)), geometry=sorted(set(g.geom_type.dropna())))
    with _lock:
        p = s.model(sid)
        try: per, rep = tools_v4.loadbuilder(p, g, field, scale, max_dist or None)
        except (ValueError, KeyError) as x: raise HTTPException(400, str(x))
        ls = load_set or p.settings["design_load"]
        if apply:
            if target == "unit":
                if not unit: raise HTTPException(400, "choose the unit load the counts are of")
                cur = (getattr(p, "unit_rows", {}) or {}).get(ls, {})              # the node's other units' rows stay
                ops = [dict(op="set_unit_rows", set=ls, ids=[n], rows=[r for r in cur.get(n, []) if r[0] != unit] + [[unit, float(v)]]) for n, v in per.items()]
                e = dict(op="batch", ops=ops)
            else: e = dict(op="set_loads", set=ls, values={n: float(v) for n, v in per.items()})
            try: s.edit(sid, e)
            except (ValueError, KeyError) as x: raise HTTPException(400, str(x))
            _, summ = s.solve(sid); rep["applied"] = True
    import shutil; shutil.rmtree(d, ignore_errors=True)
    top = per.sort_values(ascending=False).head(15)
    return clean(dict(report=rep, top=[dict(id=k, value=float(v)) for k, v in top.items()], target=target, load_set=ls, scenario=s.scenarios[sid].to_dict()))


@router.post("/projects/{pid}/scenarios/{sid}/trex")
async def trex(pid: str, sid: str, request: Request, file: UploadFile | None = File(None), path: str = "", keep_depth: bool = True, ids: str = ""):
    """TRex: ground levels from a terrain GeoTIFF or VRT (an upload, or a path on this computer, e.g. the project's
    0.5 m VRT); one undoable edit; the inverts follow when depths are kept (where the old depth is known)."""
    import tempfile, shutil
    from sewerapp.engine import tools_v4
    s = _s(pid); d = None
    if path:
        if _remote(request): raise HTTPException(403, "a path on this computer can be read only from the computer itself, not over the shared web link: upload the file instead")
        if path.startswith(("\\\\", "//")): raise HTTPException(400, "a network path is not read: copy the terrain to this computer or upload it")
        if not os.path.exists(path): raise HTTPException(400, f"no file {path}")
        src = path
    elif file is not None:
        d = tempfile.mkdtemp(prefix="w19tx_"); src = os.path.join(d, "dem.tif"); open(src, "wb").write(await file.read())
    else: raise HTTPException(400, "give a terrain file or its path")
    try:
        with _lock:
            p = s.model(sid)
            try: lv, bad = tools_v4.trex(p, src, [i for i in ids.split(",") if i] or None)
            except Exception as x: raise HTTPException(400, f"the terrain could not be read: {x}")
            name = os.path.basename(path) if path else _safe_name(getattr(file, "filename", ""), "terrain.tif")
            return _apply_levels(s, sid, lv, bad, keep_depth, f"file {name}")
    finally:
        if d: shutil.rmtree(d, ignore_errors=True)


def _apply_levels(s, sid, lv, bad, keep_depth, source):
    """TRex's one undoable edit (under _lock): the ground levels with their source, and the inverts when depths are kept."""
    p = s.model(sid)
    lv = {n: float(v) for n, v in lv.items() if n in p.nodes.index and v == v}       # structures deleted meanwhile drop out
    if not lv: raise HTTPException(400, "no structure lies on the terrain's cells")
    ops = [dict(op="set_values", table="nodes", field="ground", values=lv, source=source)]
    if keep_depth:
        g0, i0 = p.nodes.ground.astype(float), p.nodes.invert.astype(float)
        inv = {n: lv[n] - float(g0[n] - i0[n]) for n in lv if g0[n] == g0[n] and i0[n] == i0[n]}
        if inv: ops.append(dict(op="set_inverts", values=inv))
    dz = [lv[n] - float(p.nodes.ground[n]) for n in lv if p.nodes.ground[n] == p.nodes.ground[n]] or [0.0]
    try: s.edit(sid, dict(op="batch", ops=ops)); _, summ = s.solve(sid)
    except (ValueError, KeyError) as x: raise HTTPException(400, str(x))
    return clean(dict(updated=len(lv), no_data=list(bad)[:50], no_data_count=len(bad), mean_change_m=float(np.mean(dz)), max_change_m=float(np.max(np.abs(dz))),
                      source=source, summary=summ, scenario=s.scenarios[sid].to_dict()))


class TerrainPts(BaseModel):
    crs: str | None = None                       # the terrain's CRS: "EPSG:32640" or a WKT (a VRT's SRS)
    ids: list[str] | None = None


@router.post("/projects/{pid}/scenarios/{sid}/trex/points")
def trex_points(pid: str, sid: str, b: TerrainPts):
    """The structures in the terrain's own CRS: the browser reads the engineer's GeoTIFF or VRT where it is (nothing is
    uploaded) and sends back only the levels (trex/levels)."""
    from sewerapp.engine import terrain
    s = _s(pid)
    with _lock: p = s.model(sid)
    if b.crs is not None and len(b.crs) > 20000: raise HTTPException(400, "the coordinate system text is too long")
    try: ids, x, y = terrain.points_in(p, b.crs, b.ids)
    except ValueError as x: raise HTTPException(400, str(x))
    return dict(ids=ids, x=x, y=y, project_crs=p.crs)


class TerrainLevels(BaseModel):
    levels: dict[str, float | None]
    keep_depth: bool = True
    name: str = "terrain"                        # the file's name, for the record of where the levels came from
    res_m: float | None = None


@router.post("/projects/{pid}/scenarios/{sid}/trex/levels")
def trex_levels(pid: str, sid: str, b: TerrainLevels):
    s = _s(pid)
    lv = {str(k): v for k, v in b.levels.items() if v is not None and np.isfinite(v) and -500 < v < 9000}
    bad = [str(k) for k in b.levels if str(k) not in lv]
    name = _safe_name(b.name, "terrain")[:120]
    src = f"file {name}" + (f", {b.res_m:g} m cells" if b.res_m and b.res_m > 0 else "")
    with _lock: return _apply_levels(s, sid, lv, bad, b.keep_depth, src)


_VEC: dict = {}                                   # token -> (folder, main file, time): a contour or spot-level upload kept between inspect and apply
_VEC_EXT = (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix", ".sbn", ".sbx", ".gpkg", ".geojson", ".json", ".dxf", ".dwg")


def _vec_main(folder):
    from sewerapp.engine import terrain
    fs = sorted(os.listdir(folder))
    for ext in terrain.VECTOR_EXT:                    # the shapefile before its sidecars, and so on
        m = [f for f in fs if f.lower().endswith(ext)]
        if m: return os.path.join(folder, m[0])
    raise HTTPException(400, "no contour or spot-level file among them (a shapefile with its .shx and .dbf, a GeoPackage, GeoJSON, DXF or DWG)")


@router.post("/projects/{pid}/scenarios/{sid}/trex/vector/inspect")
async def trex_vector_inspect(pid: str, sid: str, request: Request, files: list[UploadFile] | None = File(None), path: str = ""):
    """Contours or spot levels: the files (a shapefile with its sidecars, a zip of them, a GeoPackage, GeoJSON, DXF or
    DWG) are kept under a token; what they offer is returned so the engineer picks the layer and the level field."""
    import zipfile, shutil, uuid
    from sewerapp.engine import terrain
    _s(pid)
    for k, (d, _, t0) in list(_VEC.items()):
        if time.time() - t0 > 7200: shutil.rmtree(d, ignore_errors=True); _VEC.pop(k, None)
    d = tempfile.mkdtemp(prefix="w19vec_")
    try:
        if path:
            if _remote(request): raise HTTPException(403, "a path on this computer can be read only from the computer itself, not over the shared web link: pick the files instead")
            if path.startswith(("\\\\", "//")): raise HTTPException(400, "a network path is not read: copy the file to this computer or pick it")
            if not os.path.isfile(path): raise HTTPException(400, f"no file {path}")
            base = os.path.splitext(path)[0]
            for f in os.listdir(os.path.dirname(path) or "."):                  # a shapefile's sidecars come with it
                full = os.path.join(os.path.dirname(path), f)
                if os.path.splitext(full)[0].lower() == base.lower() and f.lower().endswith(_VEC_EXT): shutil.copy(full, d)
            main = os.path.join(d, os.path.basename(path))
        else:
            if not files: raise HTTPException(400, "pick the contour or spot-level files")
            for f in files:
                name = _safe_name(f.filename, "layer"); data = await f.read()
                if name.lower().endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(data)) as z:
                        for m in z.infolist():
                            n = _safe_name(m.filename, "")
                            if n and n.lower().endswith(_VEC_EXT) and m.file_size < 2_000_000_000:
                                with z.open(m) as src, open(os.path.join(d, n), "wb") as dst: shutil.copyfileobj(src, dst)
                elif name.lower().endswith(_VEC_EXT): open(os.path.join(d, name), "wb").write(data)
            main = _vec_main(d)
        try: info = terrain.vector_inspect(main)
        except ValueError as x: raise HTTPException(400, str(x))
        except Exception as x: raise HTTPException(400, f"the file could not be read: {str(x)[:300]}")
    except HTTPException:
        shutil.rmtree(d, ignore_errors=True); raise
    tok = uuid.uuid4().hex; _VEC[tok] = (d, main, time.time())
    return dict(info, token=tok, name=os.path.basename(main))


class TerrainVec(BaseModel):
    token: str
    field: str
    layer: str | None = None
    dxf_layer: str | None = None
    keep_depth: bool = True
    ids: list[str] | None = None


@router.post("/projects/{pid}/scenarios/{sid}/trex/vector")
def trex_vector(pid: str, sid: str, b: TerrainVec):
    """Ground levels from the contours or spot levels kept under `token`: a TIN of their vertices near the network."""
    from sewerapp.engine import terrain
    s = _s(pid)
    if b.token not in _VEC: raise HTTPException(400, "pick the contour or spot-level files again (they are kept for two hours)")
    d, main, _ = _VEC[b.token]
    with _lock:
        p = s.model(sid)
        from sewerapp.model.general import Project
        q = Project(name="t", crs=p.crs); q.nodes = p.nodes[["x", "y"]].copy()
    try: lv, bad, nv = terrain.vector_levels(q, main, b.field, b.layer, b.dxf_layer, b.ids)
    except ValueError as x: raise HTTPException(400, str(x))
    except Exception as x: raise HTTPException(400, f"the file could not be read: {str(x)[:300]}")
    if not lv: raise HTTPException(400, "no structure lies inside the contours or spot levels (check the coordinate system: a DXF or DWG is taken to be in the project's)")
    what = "spot levels" if b.field == terrain.TEXT_FIELD else "contours or spot levels"
    src = f"{what} {_safe_name(os.path.basename(main), 'file')[:80]}" + (f", layer {b.dxf_layer[:40]}" if b.dxf_layer else "") +           (f", field {b.field[:40]}" if b.field not in (terrain.Z_FIELD, terrain.TEXT_FIELD) else "") + f", TIN of {nv:,} vertices"
    with _lock: out = _apply_levels(s, sid, lv, bad, b.keep_depth, src)
    return out | dict(vertices=nv)


class TerrainCop(BaseModel):
    keep_depth: bool = True
    ids: list[str] | None = None


@router.post("/projects/{pid}/scenarios/{sid}/trex/copernicus")
def trex_copernicus(pid: str, sid: str, b: TerrainCop):
    """Ground levels from the Copernicus GLO-30 surface model, fetched a window at a time from its public tiles (only
    the cells around the network). Read outside the app lock; applied under it."""
    from sewerapp.engine import terrain
    s = _s(pid)
    with _lock:
        p = s.model(sid)
        from sewerapp.model.general import Project
        q = Project(name="t", crs=p.crs); q.nodes = p.nodes[["x", "y"]].copy()     # what the read needs, nothing shared
    try: lv, bad, read = terrain.copernicus(q, b.ids)
    except ValueError as x: raise HTTPException(400, str(x))
    if not lv: raise HTTPException(400, "Copernicus has no level at these structures (sea, or no tile there)")
    with _lock: out = _apply_levels(s, sid, lv, bad, b.keep_depth, terrain.COPERNICUS_SRC)
    return out | dict(tiles=read, notice=terrain.COPERNICUS_NOTICE, liability=terrain.COPERNICUS_LIABILITY)


@router.get("/projects/{pid}/scenarios/{sid}/rational")
def rational(pid: str, sid: str):
    """The rational method on every conduit (a steady storm run)."""
    from sewerapp.engine import tools_v4
    s = _s(pid)
    with _lock:
        inl = {}
        try: rows, summ = tools_v4.rational(s.model(sid), inl)
        except (ValueError, KeyError) as x: raise HTTPException(400, str(x))
    if inl:                                                                 # catch basins: capture, bypass, spread (v7)
        summ = dict(summ, inlets=len(inl), captured_ls=round(sum(r["q_captured_ls"] for r in inl.values()), 3),
                    bypass_lost_ls=round(sum(r["q_bypass_ls"] for r in inl.values() if r["bypass_to"] == "lost"), 3),
                    spread_over=sum(1 for r in inl.values() if r.get("spread_over")), depth_over=sum(1 for r in inl.values() if r.get("depth_over")),
                    sag_floods=sum(1 for r in inl.values() if r.get("floods")))
    return clean(dict(rows=[dict(id=k, **v) for k, v in sorted(rows.items(), key=lambda kv: -kv[1]["q_rational_ls"])], report=summ,
                      inlets=[dict(id=k, **v) for k, v in inl.items()]))


class BatchB(BaseModel):
    sids: list[str]


@router.post("/projects/{pid}/batch")
def batch_run(pid: str, b: BatchB):
    """The steady run of several scenarios, side by side."""
    from sewerapp.engine import tools_v4
    s = _s(pid)
    bad = [x for x in b.sids if x not in s.scenarios]
    if bad: raise HTTPException(404, f"no scenario {bad[0]}")
    with _lock: rows = tools_v4.batch(s, b.sids)
    return clean(dict(rows=rows))


@router.get("/projects/{pid}/scenarios/{sid}/validate")
def validate(pid: str, sid: str):
    """User notifications: errors and warnings per element (engine/validate.py)."""
    from sewerapp.engine import validate as V
    s = _s(pid)
    with _lock:
        p = s.model(sid); res, _ = s.solve(sid)
        return clean(dict(items=V.run(p, res)))


@router.get("/projects/{pid}/scenarios/{sid}/pump_system")
def pump_system(pid: str, sid: str, id: str, qmax: float):
    """A pump's force main as a system curve (head needed at 0..qmax L/s) and its steady duty, for the pump-definition graph."""
    from sewerapp.engine import pressure
    s = _s(pid)
    with _lock:
        p = s.model(sid)
        if id not in p.links.index or p.links.kind[id] != "pump": raise HTTPException(404, f"no pump {id}")
        qs = [float(qmax) * k / 24 for k in range(25)]
        res, _ = s.solve(sid)
        from sewerapp.engine import steady
        try:
            qd = steady.flows(p, p.settings["design_load"]).to_dict()
            dep = {}
            if res is not None:
                for lid in p.links.index[(p.links.kind == "conduit").to_numpy()]:
                    if lid in res.index and res.d_over_D[lid] == res.d_over_D[lid] and p.links.inside_mm[lid] == p.links.inside_mm[lid]:
                        dep[p.links.from_node[lid]] = float(res.d_over_D[lid]) * float(p.links.inside_mm[lid]) / 1000.0
            h = pressure.system_curve(p, id, qs, qd, dep)
        except (ValueError, KeyError) as x: raise HTTPException(400, str(x))
    duty = res.loc[id] if res is not None and id in res.index and "tdh_m" in res.columns else None
    return clean(dict(q=qs, h=h, duty_q=float(duty.q_ls) if duty is not None else None, duty_h=float(duty.tdh_m) if duty is not None else None))


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
_REF_EXT = (".shp", ".shx", ".dbf", ".prj", ".cpg", ".gpkg", ".geojson", ".json", ".dxf", ".kml", ".zip", ".gml", ".tab", ".map", ".id", ".dat")


@router.post("/projects/{pid}/reference")
def add_reference(pid: str, file: UploadFile | None = File(None), files: list[UploadFile] | None = File(None)):
    """A background layer: one GIS file, a zip, or a shapefile with its sidecars picked together (`files`)."""
    from sewerapp.io import gis_import
    import shapely
    s = _s(pid); crs = s.base.crs
    up = ([file] if file is not None else []) + list(files or [])
    if not up: raise HTTPException(400, "pick a GIS file")
    with tempfile.TemporaryDirectory() as d:
        names = []
        for u in up:
            n = _safe_name(u.filename, "layer")
            if len(up) > 1 and not n.lower().endswith(_REF_EXT): continue
            open(os.path.join(d, n), "wb").write(u.file.read()); names.append(n)
        main = next((n for ext in (".shp", ".gpkg", ".geojson", ".json", ".dxf", ".kml", ".zip", ".gml", ".tab") for n in names if n.lower().endswith(ext)), names[0] if names else None)
        if not main: raise HTTPException(400, "pick a GIS file")
        f = os.path.join(d, main); file = next(u for u in up if _safe_name(u.filename, "layer") == main)
        if main.lower().endswith(".shp") and not any(n.lower() == main[:-4].lower() + ".dbf" for n in names) and len(up) == 1:
            raise HTTPException(400, f"{main} needs its .shx and .dbf (and .prj): pick them together, or zip them")
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


class RefStyle(BaseModel):
    color: str | None = None
    opacity: float | None = None
    visible: bool | None = None
    name: str | None = None


@router.post("/projects/{pid}/reference/{rid}/style")
def style_reference(pid: str, rid: str, b: RefStyle):
    """A background layer's colour, opacity, visibility or name, kept with the project."""
    s = _s(pid)
    with _lock:
        r = next((r for r in getattr(s, "refs", []) if r["id"] == rid), None)
        if r is None: raise HTTPException(404, f"no layer {rid}")
        if b.color is not None:
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", b.color): raise HTTPException(400, "a colour is #rrggbb")
            r["color"] = b.color
        if b.opacity is not None: r["opacity"] = max(0.0, min(1.0, float(b.opacity)))
        if b.visible is not None: r["visible"] = bool(b.visible)
        if b.name: r["name"] = b.name.strip()[:80]
    schedule(pid); return dict(ok=True)


class RefOrder(BaseModel):
    ids: list[str]


@router.post("/projects/{pid}/reference/order")
def order_references(pid: str, b: RefOrder):
    """The drawing order of the background layers (first: at the bottom)."""
    s = _s(pid)
    with _lock:
        R = {r["id"]: r for r in getattr(s, "refs", [])}
        s.refs = [R[i] for i in b.ids if i in R] + [r for i, r in R.items() if i not in b.ids]
    schedule(pid); return dict(ok=True)


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
        gh = (float(r.hgl_up), float(r.hgl_dn)) if r is not None and "hgl_up" in r and r.hgl_up == r.hgl_up else None
        up, dn = (L.up_inv, L.dn_inv) if L.kind != "pump" else (p.nodes.invert[L.from_node], p.nodes.invert[L.to_node])
        i0, i1 = (dn, up) if rev else (up, dn)
        ln = float(L.length_m) if L.length_m == L.length_m else 0.0
        g = lambda k: None if r is None or k not in r else r[k]
        rows.append(clean(dict(link=i, kind=L.kind, reversed=bool(rev), from_node=n0, to_node=n1, ch0=ch, ch1=ch + ln, length_m=ln,
                               ground0=p.nodes.ground[n0], ground1=p.nodes.ground[n1], inv0=i0, inv1=i1, crown0=i0 + D, crown1=i1 + D,
                               water0=(gh[1] if rev else gh[0]) if gh else i0 + dd * D, water1=(gh[0] if rev else gh[1]) if gh else i1 + dd * D, dn_mm=L.dn_mm, section=_seclab(secs[i]) if i in secs else None,
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


def _remote(request) -> bool:
    """True when the request came through the shared web link (Cloudflare adds cf-connecting-ip) or from another computer."""
    h = request.headers
    if h.get("cf-connecting-ip") or h.get("x-forwarded-for"): return True
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost", "testclient"): return True
    name = (h.get("host") or "").rsplit(":", 1)[0].strip("[]").lower()     # a page elsewhere reaching this computer's port
    return name not in ("127.0.0.1", "localhost", "::1", "testserver")       # (DNS rebinding) carries its own host name


class FolderB(BaseModel):
    path: str


def _client_key(request) -> str:
    """Who spends: this computer, or one visitor of the shared link (by the address Cloudflare reports)."""
    if not _remote(request): return "local"
    h = request.headers
    return "web:" + (h.get("cf-connecting-ip") or (h.get("x-forwarded-for") or "").split(",")[0].strip() or (request.client.host if request.client else "?"))


@router.get("/assistant/usage")
def assistant_usage(request: Request):
    from sewerapp.assistant import budget
    return budget.status(_client_key(request))


class LimitsB(BaseModel):
    local_daily_usd: float | None = None
    web_daily_usd: float | None = None
    web_all_daily_usd: float | None = None


@router.post("/assistant/limits")
def assistant_limits(b: LimitsB, request: Request):
    from sewerapp.assistant import budget
    if _remote(request): raise HTTPException(403, "the assistant's limits are set only on the engineer's own computer")
    try: budget.set_limits({k: v for k, v in b.model_dump().items() if v is not None})
    except ValueError as x: raise HTTPException(400, str(x))
    return budget.status("local")


@router.get("/assistant/folders")
def assistant_folders(request: Request):
    from sewerapp.assistant import agent
    if _remote(request): return dict(folders=[], remote=True, note="folders are managed on the engineer's own computer only")
    return dict(folders=agent.folders(), remote=False)


@router.post("/assistant/folders")
def assistant_folder_add(b: FolderB, request: Request):
    from sewerapp.assistant import agent
    if _remote(request): raise HTTPException(403, "folders can be registered only on the engineer's own computer, not over the shared web link")
    try: return dict(folders=agent.add_folder(b.path), remote=False)
    except ValueError as x: raise HTTPException(400, str(x))


@router.post("/assistant/folders/remove")
def assistant_folder_remove(b: FolderB, request: Request):
    from sewerapp.assistant import agent
    if _remote(request): raise HTTPException(403, "folders can be changed only on the engineer's own computer")
    return dict(folders=agent.remove_folder(b.path), remote=False)


@router.post("/assistant")
def assistant(q: Ask, request: Request):
    """The assistant on an open project: reads results, explains checks with guideline pages, works in new scenarios."""
    return _assistant_run(q, _client_key(request), _remote(request))


_AJOBS: dict = {}                                  # an answer being written: its steps so far, then the answer


@router.post("/assistant/start")
def assistant_start(q: Ask, request: Request):
    """The same answer, started in the background: the page polls /assistant/job/{id} and shows each step as it runs."""
    import secrets
    who, remote = _client_key(request), _remote(request)
    from sewerapp.assistant import runner, budget
    st = runner.available()
    if not st["available"]: raise HTTPException(503, st["reason"])
    _s(q.project)
    if budget.remaining(who) < budget.MIN_START_USD: return _assistant_run(q, who, remote)        # the 429 with its reason
    for k, j in list(_AJOBS.items()):
        if time.time() - j["t"] > 3600: _AJOBS.pop(k, None)
    jid = secrets.token_hex(8); job = _AJOBS[jid] = dict(state="running", steps=[], out=None, error=None, t=time.time(), who=who)

    def step(s):                                   # the step and the few inputs that name what it looks at
        keep = {k: v for k, v in (s.get("input") or {}).items() if k in ("table", "ids", "start", "end", "query", "name", "path")}
        job["steps"].append(clean(dict({k: v for k, v in s.items() if k != "input"}, **({"input": keep} if keep else {}))))

    def work():
        try: job["out"] = _assistant_run(q, who, remote, on_step=step)
        except HTTPException as e: job["error"] = e.detail
        except Exception as e: job["error"] = f"{type(e).__name__}: {e}"
        finally: job["state"] = "done"
    threading.Thread(target=work, daemon=True).start()
    return dict(job=jid)


@router.get("/assistant/job/{jid}")
def assistant_job(jid: str, request: Request):
    j = _AJOBS.get(jid)
    if not j or j["who"] != _client_key(request): raise HTTPException(404, "no such answer")
    out = dict(state=j["state"], steps=j["steps"], seconds=round(time.time() - j["t"]))
    if j["state"] == "done":
        out.update(out=j["out"], error=j["error"]); _AJOBS.pop(jid, None)
    return out


def _assistant_run(q, who, remote, on_step=None):
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
    from sewerapp.assistant import agent, budget
    left = budget.remaining(who)
    if left < budget.MIN_START_USD:
        raise HTTPException(429, f"today's spending limit for the assistant is reached ({budget.status(who)['limit_today_usd']:.2f} USD a day for {budget.status(who)['client']}); it resets at midnight")
    with _alock:                                     # one answer at a time; the model's turns run outside the app lock, each
        gtools.ACTIONS.clear(); agent.CTX["remote"] = remote                    # tool call takes it (gtools.call)
        try: out = runner.ask(None, q.scenario, q.message, q.history, q.model, toolset=gtools, system=runner.SYSTEM_GENERAL, context=ctx, max_turns=30, max_usd=left, on_step=on_step)
        finally: agent.CTX["remote"] = False
        budget.charge(who, out["usage"].get("usd", 0.0)); out["budget"] = budget.status(who)
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
def sewergems_models(request: Request, mine: str = ""):
    """What can be opened (exports), what can be exported (SewerGEMS models in the shared folders), the VM watcher, and
    the export jobs the app has written. Over the shared link: only the visitor's own uploads (`mine`, their tags)."""
    from sewerapp.io import bridge_jobs as B
    if _remote(request):
        tags = {t for t in mine.split(",") if t}
        return dict(watcher=B.watcher(), exports=[e for e in sewergems_exports() if e["name"] in tags], models=[],
                    jobs=_sg_jobs(tags) + [j for j in B.jobs() if j["tag"] in tags], shares=[], remote=True)
    return dict(watcher=B.watcher(), exports=sewergems_exports(), models=B.models(), jobs=_sg_jobs() + B.jobs(), shares=[g for _, g in B.SHARES], remote=False)


_SGJOBS: dict = {}                                 # direct readings of SewerGEMS models (no SewerGEMS): job -> state


def _sg_direct(src, tag, cleanup=None):
    """Read a .stsw.sqlite directly into the exports folder (io/sewergems_db.py) in the background; the job's state is
    read like a bridge job's. The uploaded copy is deleted once read (cleanup)."""
    import secrets, shutil
    from sewerapp.io import sewergems_db
    name = f"w19d_{time.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(2)}_{tag}"
    job = _SGJOBS[name] = dict(job=name, tag=tag, state="running", exit=None, scenarios_done=0, ready=False, error=None, t0=time.time(), direct=True)
    dst = os.path.join(SG_EXPORTS, tag)

    def step(s):
        if s.startswith("  scenarios "): job["scenarios_total"] = int(s.split()[1])
        elif s.startswith("  scenario "): job["scenarios_done"] += 1

    def work():
        try:
            if os.path.isdir(dst): shutil.rmtree(dst, ignore_errors=True)
            sewergems_db.export(src, dst, log=step); job.update(state="ready", ready=True)
        except Exception as e:
            job.update(state="failed", error=f"the model could not be read: {type(e).__name__}: {str(e)[:300]}")
        finally:
            if cleanup: shutil.rmtree(cleanup, ignore_errors=True)
    threading.Thread(target=work, daemon=True).start()
    return job


def _sg_jobs(tags=None):
    out = []
    for j in list(_SGJOBS.values()):
        if tags is not None and j["tag"] not in tags: continue
        out.append({k: v for k, v in j.items() if k != "t0"} | dict(seconds=round(time.time() - j["t0"])))
    return sorted(out, key=lambda j: j["job"], reverse=True)


_UPL: dict = {}                                     # a model arriving in pieces: upload id -> folder, declared files, time
UPL_CHUNK = 32 * 1024 * 1024


class UplStart(BaseModel):
    files: list[dict]                                # [{name, size}]


@router.post("/sewergems/upload/start")
def sewergems_upload_start(b: UplStart):
    """Start a model sent in pieces (each under the 100 MB a request may carry through Cloudflare)."""
    import secrets, shutil
    for k, u in list(_UPL.items()):
        if time.time() - u["t"] > 7200: shutil.rmtree(u["dir"], ignore_errors=True); _UPL.pop(k, None)
    live = {u["dir"] for u in _UPL.values()}
    for d0 in os.listdir(tempfile.gettempdir()):                          # pieces left by a stopped upload or reading
        full = os.path.join(tempfile.gettempdir(), d0)
        if d0.startswith("w19sg_") and full not in live and time.time() - os.path.getmtime(full) > 7200: shutil.rmtree(full, ignore_errors=True)
    files = {}
    for f in b.files:
        n = _safe_name(str(f.get("name", "")), "")
        if not n.lower().endswith((".stsw", ".stsw.sqlite", ".zip")): raise HTTPException(400, f"{n or 'a file'}: a SewerGEMS model is its .stsw and .stsw.sqlite (or a zip)")
        files[n] = int(f.get("size") or 0)
    if not files or sum(files.values()) > 8 * 1024 ** 3: raise HTTPException(400, "pick the model's files (8 GB at most)")
    uid = secrets.token_hex(8); _UPL[uid] = dict(dir=tempfile.mkdtemp(prefix="w19sg_"), files=files, t=time.time())
    for n in files: open(os.path.join(_UPL[uid]["dir"], n), "wb").close()
    return dict(uid=uid, chunk=UPL_CHUNK)


@router.post("/sewergems/upload/{uid}/chunk")
async def sewergems_upload_chunk(uid: str, request: Request, name: str, offset: int, gz: bool = False):
    """One piece of a file, written at its offset (a piece sent twice is written twice to the same place)."""
    import gzip
    u = _UPL.get(uid); n = _safe_name(name, "")
    if not u or n not in u["files"]: raise HTTPException(404, "no such upload (start it again)")
    data = await request.body()
    if gz:
        try: data = gzip.decompress(data)
        except Exception: raise HTTPException(400, "a piece arrived damaged: send the model again")
    if offset < 0 or offset + len(data) > u["files"][n]: raise HTTPException(400, "a piece beyond the file's size")
    with open(os.path.join(u["dir"], n), "r+b") as fh: fh.seek(offset); fh.write(data)
    u["t"] = time.time()
    return dict(ok=True, received=len(data))


@router.post("/sewergems/upload/{uid}/finish")
def sewergems_upload_finish(uid: str, run: bool = False):
    """All pieces in: read the model directly (or, with run, give it to SewerGEMS in the VM), as a one-piece upload."""
    import zipfile, secrets, shutil
    from sewerapp.io import bridge_jobs as B
    u = _UPL.pop(uid, None)
    if not u: raise HTTPException(404, "no such upload (start it again)")
    d = u["dir"]
    for n, size in u["files"].items():
        if os.path.getsize(os.path.join(d, n)) != size: shutil.rmtree(d, ignore_errors=True); raise HTTPException(400, f"{n} did not arrive whole: send the model again")
    for n in [n for n in u["files"] if n.lower().endswith(".zip")]:
        with zipfile.ZipFile(os.path.join(d, n)) as z:
            for m in z.infolist():
                k = _safe_name(m.filename, "")
                if k and k.lower().endswith((".stsw", ".stsw.sqlite")):
                    with z.open(m) as src, open(os.path.join(d, k), "wb") as dst: shutil.copyfileobj(src, dst)
        os.remove(os.path.join(d, n))
    names = os.listdir(d); stsw = [k for k in names if k.lower().endswith(".stsw")]
    sq = [k for k in names if stsw and k.lower() == stsw[0].lower() + ".sqlite"]
    if len(stsw) != 1 or not sq: shutil.rmtree(d, ignore_errors=True); raise HTTPException(400, "pick one model: its .stsw and its .stsw.sqlite (or both in one zip)")
    tag = f"{B.tag_of(stsw[0])}_{secrets.token_hex(3)}"; mb = round(sum(os.path.getsize(os.path.join(d, k)) for k in names if k in stsw + sq) / 1e6, 1)
    if not run:
        j = _sg_direct(os.path.join(d, sq[0]), tag, cleanup=d)
        return dict(job=j["job"], tag=tag, name=stsw[0], mb=mb, direct=True)
    root = os.path.join(B.BRIDGE, "models", "uploads")
    if not B.guest_path(root): shutil.rmtree(d, ignore_errors=True); raise HTTPException(400, "this installation has no SewerGEMS to compute the scenarios with: untick it to open the model as it is")
    dst = os.path.join(root, f"{time.strftime('%Y%m%d_%H%M%S')}_{tag}"); os.makedirs(dst)
    for k in stsw + sq: shutil.move(os.path.join(d, k), os.path.join(dst, k))
    shutil.rmtree(d, ignore_errors=True)
    try: r = B.submit(B.guest_path(os.path.join(dst, stsw[0])), tag, run)
    except ValueError as e: raise HTTPException(400, str(e))
    return dict(r, name=stsw[0], mb=mb)


class SgRead(BaseModel):
    host: str


@router.post("/sewergems/read")
def sewergems_read(b: SgRead, request: Request):
    """A model in this computer's folders, read directly (no SewerGEMS, nothing written beside it)."""
    from sewerapp.io import bridge_jobs as B
    if _remote(request): raise HTTPException(403, "a model in this computer's folders is opened from this computer; over the shared link, pick the model's files")
    if not b.host.lower().endswith(".stsw") or not os.path.isfile(b.host + ".sqlite"): raise HTTPException(400, f"no {os.path.basename(b.host)}.sqlite beside the model")
    return _sg_direct(b.host + ".sqlite", B.tag_of(b.host))


@router.post("/sewergems/upload")
async def sewergems_upload(files: list[UploadFile] = File(...), run: bool = False):
    """A SewerGEMS model picked on the visitor's device: its .stsw and .stsw.sqlite (or both zipped). Read directly
    (io/sewergems_db.py, no SewerGEMS; the files are deleted once read); with `run`, copied into a new folder of the
    bridge's models share for SewerGEMS to compute every scenario on a copy in the VM."""
    import zipfile, secrets, shutil
    from sewerapp.io import bridge_jobs as B
    root = os.path.join(B.BRIDGE, "models", "uploads")
    if run and not B.guest_path(root): raise HTTPException(400, "this installation has no SewerGEMS to compute the scenarios with: untick it to open the model as it is")
    stamp = time.strftime("%Y%m%d_%H%M%S"); d = None
    try:
        got = {}
        for f in files:
            n = _safe_name(f.filename, "model"); data = await f.read()
            if n.lower().endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for m in z.infolist():
                        k = _safe_name(m.filename, "")
                        if k and k.lower().endswith((".stsw", ".stsw.sqlite")): got[k] = z.read(m)
            elif n.lower().endswith((".stsw", ".stsw.sqlite")): got[n] = data
        stsw = [k for k in got if k.lower().endswith(".stsw")]
        if len(stsw) != 1: raise HTTPException(400, "pick one model: its .stsw file and its .stsw.sqlite (or both in one zip)")
        if stsw[0] + ".sqlite" not in got and not any(k.lower() == stsw[0].lower() + ".sqlite" for k in got):
            raise HTTPException(400, f"{stsw[0]} needs its {stsw[0]}.sqlite beside it: pick both (or zip them)")
        tag = f"{B.tag_of(stsw[0])}_{secrets.token_hex(3)}"
        if not run:                                   # read directly: no SewerGEMS, and the files are deleted once read
            d = tempfile.mkdtemp(prefix="w19sg_")
            for k, v in got.items(): open(os.path.join(d, k), "wb").write(v)
            sq = next(k for k in got if k.lower() == stsw[0].lower() + ".sqlite")
            j = _sg_direct(os.path.join(d, sq), tag, cleanup=d); d = None
            return dict(job=j["job"], tag=tag, name=stsw[0], mb=round(sum(len(v) for v in got.values()) / 1e6, 1), direct=True)
        d = os.path.join(root, f"{stamp}_{tag}"); os.makedirs(d)
        for k, v in got.items(): open(os.path.join(d, k), "wb").write(v)
        r = B.submit(B.guest_path(os.path.join(d, stsw[0])), tag, run)
        return dict(r, name=stsw[0], mb=round(sum(len(v) for v in got.values()) / 1e6, 1))
    except HTTPException:
        if d: shutil.rmtree(d, ignore_errors=True)
        raise
    except ValueError as e:
        if d: shutil.rmtree(d, ignore_errors=True)
        raise HTTPException(400, str(e))


class SgExport(BaseModel):
    guest: str
    tag: str | None = None
    run: bool = False                                      # compute every scenario on the copy before exporting


@router.post("/sewergems/export")
def sewergems_export_job(b: SgExport, request: Request):
    """Write the bridge job that exports a SewerGEMS model (every scenario, results and loads) from a copy, in the VM.
    A path in the VM is this computer's: not over the shared link (a visitor uploads the model instead)."""
    from sewerapp.io import bridge_jobs as B
    if _remote(request): raise HTTPException(403, "a model in this computer's folders is opened from this computer; over the shared link, pick the model's files")
    try: return B.submit(b.guest, b.tag, b.run)
    except ValueError as e: raise HTTPException(400, str(e))


@router.get("/sewergems/jobs/{name}")
def sewergems_job(name: str):
    from sewerapp.io import bridge_jobs as B
    if name in _SGJOBS: return _sg_jobs({_SGJOBS[name]["tag"]})[0]
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
def open_sewergems(name: str, request: Request, crs: int | None = 32640):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", name): raise HTTPException(404, f"no export {name}")
    if _remote(request) and not re.fullmatch(r".+_[0-9a-f]{6}", name):          # over the shared link: an upload's own export
        raise HTTPException(403, "over the shared link, a SewerGEMS model is opened from its files (Open a SewerGEMS model > Choose the model's files)")
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
