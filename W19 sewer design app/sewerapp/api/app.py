"""The app's HTTP API (FastAPI), served on 127.0.0.1 only, and the web page. Start: python -m sewerapp.api"""
import io, json, math, os, threading, time
import numpy as np, pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sewerapp import fixtures
from sewerapp.model.project import Project, CASES, EDITABLE
from sewerapp.api import exports, tools

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web")
app = FastAPI(title="Sewer design app")
from sewerapp.api.general_api import router as general_router
app.include_router(general_router)
P = Project()
_geo = {}
_lock = threading.Lock()


def clean(x):
    """JSON-safe: numpy scalars to Python, NaN to None."""
    if isinstance(x, dict): return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, np.generic): x = x.item()
    if isinstance(x, float) and not math.isfinite(x): return None
    return x


def _sc(sid):
    if sid not in P.scenarios: raise HTTPException(404, f"no scenario {sid}")
    return P.scenario(sid)


@app.get("/api/scenarios")
def scenarios():
    return [dict(id=s.id, name=s.name, case=s.case.case if s.case else s.id, parent=s.parent, edits=len(s.edits),
                 can_undo=bool(s.edits), can_redo=bool(s.redo), read_only=s.id in CASES) for s in P.scenarios.values()]


class Copy(BaseModel):
    name: str | None = None


@app.post("/api/scenarios/{sid}/copy")
def copy_scenario(sid: str, body: Copy):
    _sc(sid)
    with _lock: s = P.copy(sid, body.name)
    return s.to_dict()


@app.get("/api/geometry/{case}")
def geometry(case: str):
    """Pipes and nodes as GeoJSON in WGS84; property i = the row of the results arrays."""
    if case not in CASES: raise HTTPException(404, case)
    if case not in _geo:
        import geopandas as gpd
        from shapely.geometry import LineString, Point
        c = P.case(case); k = c.links; n = c.nodes
        lines = gpd.read_file(_s1(), layer="pipes").set_index("label").geometry
        xy = {lab: (r.x, r.y) for lab, r in n.iterrows()}
        geom = [lines.get(o) if o in lines.index else LineString([xy[a], xy[b]]) for o, a, b in zip(k.old, k.from_mh, k.to_mh)]
        p = gpd.GeoDataFrame(dict(i=np.arange(len(k)), label=k.new, dn=k.dn_mm), geometry=geom, crs=32640).to_crs(4326)
        m = gpd.GeoDataFrame(dict(label=n.index, kind=n.kind, ground=n.ground, depth=n.depth),
                             geometry=[Point(x, y) for x, y in zip(n.x, n.y)], crs=32640).to_crs(4326)
        _geo[case] = dict(pipes=json.loads(p.to_json(drop_id=True)), nodes=json.loads(m.to_json(drop_id=True)),
                          bounds=list(p.total_bounds))
    return JSONResponse(_geo[case])


def _s1():
    path = os.path.join(fixtures.FIX, "..", "..", "work", "S1.gpkg")
    if not os.path.exists(path): fixtures.materialize("geo/S1.gpkg", path)
    return path


@app.get("/api/scenarios/{sid}/results")
def results(sid: str):
    _sc(sid)
    with _lock: res, summ = P.results(sid)
    cols = ["dn_mm", "q_ls", "v_ms", "d_over_D", "v2031_ms", "over_limit", "over_3ms", "under075", "needs_relay",
            "s_pc", "depth_up_m", "depth_dn_m"]
    return clean(dict(summary=summ, columns={c: res[c].round(4).tolist() if res[c].dtype.kind == "f" else res[c].tolist() for c in cols}))


@app.get("/api/scenarios/{sid}/pipes/{i}")
def pipe(sid: str, i: int):
    _sc(sid)
    res, _ = P.results(sid)
    if not 0 <= i < len(res): raise HTTPException(404, "no such pipe")
    return clean(res.iloc[i].to_dict() | dict(i=i))


class Edit(BaseModel):
    target: str
    ids: list[int]
    field: str
    value: float


@app.post("/api/scenarios/{sid}/edits")
def edit(sid: str, e: Edit):
    _sc(sid)
    try:
        with _lock: _, summ = P.edit(sid, e.target, e.ids, e.field, e.value)
    except ValueError as x:
        raise HTTPException(400, str(x))
    return clean(summ)


@app.post("/api/scenarios/{sid}/undo")
def undo(sid: str):
    _sc(sid)
    with _lock: _, summ = P.undo(sid)
    return clean(summ)


@app.post("/api/scenarios/{sid}/redo")
def redo(sid: str):
    _sc(sid)
    with _lock: _, summ = P.redo_(sid)
    return clean(summ)


@app.get("/api/editable")
def editable():
    return {t: list(f) for t, f in EDITABLE.items()}


@app.get("/api/compare")
def compare(a: str, b: str):
    _sc(a); _sc(b)
    return clean(P.compare(a, b))


@app.get("/api/scenarios/{sid}/profile")
def profile(sid: str, start: str, end: str | None = None):
    _sc(sid)
    try: return clean(P.profile(sid, start, end))
    except ValueError as x: raise HTTPException(400, str(x))


@app.get("/api/scenarios/{sid}/stations")
def stations(sid: str):
    s = _sc(sid)
    return clean(dict(stations=s.case.stations.to_dict("records"), quantities=s.case.quantities))


@app.get("/api/scenarios/{sid}/export.{fmt}")
def export(sid: str, fmt: str):
    s = _sc(sid); res, summ = P.results(sid)
    if fmt == "csv":
        return Response(res.to_csv(index=False), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{sid}_pipes.csv"'})
    if fmt == "gpkg":
        data = exports.gpkg_bytes(s.case, res, _s1())
        return Response(data, media_type="application/geopackage+sqlite3",
                        headers={"Content-Disposition": f'attachment; filename="{sid}.gpkg"'})
    if fmt == "dxf":
        data = exports.dxf_bytes(s.case, res)
        return Response(data, media_type="application/dxf", headers={"Content-Disposition": f'attachment; filename="{sid}.dxf"'})
    raise HTTPException(400, "csv, gpkg or dxf")


@app.get("/api/tools")
def tool_list():
    return tools.REGISTER


@app.post("/api/tools/{name}")
def run_tool(name: str, sid: str):
    s = _sc(sid)
    try: return clean(tools.run(name, P, s))
    except KeyError: raise HTTPException(404, f"no tool {name}")


class Ask(BaseModel):
    sid: str
    message: str
    history: list[dict] = []
    model: str = "opus"


@app.get("/api/assistant/status")
def assistant_status():
    from sewerapp.assistant import runner
    return runner.available()


@app.post("/api/assistant")
def assistant(q: Ask):
    from sewerapp.assistant import runner
    st = runner.available()
    if not st["available"]: raise HTTPException(503, st["reason"])
    _sc(q.sid)
    with _lock:
        return clean(runner.ask(P, q.sid, q.message, q.history, q.model))


if os.path.isdir(WEB):
    app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
def index():
    """The general editor (any project, sewer and stormwater)."""
    return FileResponse(os.path.join(WEB, "editor", "index.html"))


@app.get("/w18")
def w18_viewer():
    """The Ibri W18 viewer of phase 1B (the 12 frozen designs, what-ifs, tools)."""
    return FileResponse(os.path.join(WEB, "index.html"))
