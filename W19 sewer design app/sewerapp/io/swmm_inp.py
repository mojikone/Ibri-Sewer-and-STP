"""EPA SWMM 5 input files (.inp, a public, documented text format) to and from the general project.

Modelled (editable in the app): JUNCTIONS, OUTFALLS, STORAGE (nodes), CONDUITS, PUMPS (links), XSECTIONS (the
diameter of a conduit; RECT_CLOSED, RECT_OPEN and TRAPEZOIDAL as box and open-channel sections, n from CONDUITS), SUBCATCHMENTS, SUBAREAS (catchments), COORDINATES, VERTICES, Polygons. Each modelled element
keeps its other SWMM fields as written, so an imported model is written back as SWMM's own; every other section is kept
verbatim. Values stay in the file's units (US: ft, acres; SI: m, ha); the project records which.
A project with no SWMM origin gets generated sections: options, a rain gauge with its time series (or a design storm
by the alternating-block method from an IDF table, Chow, Maidment and Mays 1988), Horton infiltration defaults, and the
report section."""
import re
from collections import OrderedDict
import numpy as np, pandas as pd
from sewerapp.model.general import Project, NODE_COLS, LINK_COLS, CATCH_COLS

MODELLED = ["JUNCTIONS", "OUTFALLS", "STORAGE", "CONDUITS", "PUMPS", "XSECTIONS", "SUBCATCHMENTS", "SUBAREAS",
            "COORDINATES", "VERTICES", "POLYGONS"]
US_UNITS = {"CFS", "GPM", "MGD"}


def parse(text):
    """Sections in order: {NAME: {"head": [comment lines], "rows": [token lists], "raw": [lines], "title": original}}."""
    secs, cur = OrderedDict(), None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^\[([A-Za-z_]+)\]", s)
        if m:
            cur = m.group(1).upper(); secs[cur] = dict(head=[], rows=[], raw=[], title=m.group(1)); continue
        if cur is None: continue
        secs[cur]["raw"].append(line)
        if not s: continue
        if s.startswith(";"):
            if not secs[cur]["rows"]: secs[cur]["head"].append(line)
            continue
        secs[cur]["rows"].append(s.split(";")[0].split())
    return secs


def _option(secs, key, default=None):
    for r in secs.get("OPTIONS", {}).get("rows", []):
        if r and r[0].upper() == key: return r[1]
    return default


def to_project(text, name="SWMM model"):
    secs = parse(text)
    units = "US" if (_option(secs, "FLOW_UNITS", "CFS") or "CFS").upper() in US_UNITS else "SI"
    mm = 304.8 if units == "US" else 1000.0
    p = Project(name=name); p.settings["units"] = units
    rows = {}                                              # "SECTION|id" -> full token list (the SWMM fields)
    xy = {r[0]: (float(r[1]), float(r[2])) for r in secs.get("COORDINATES", {}).get("rows", []) if len(r) >= 3}
    nodes = []
    for sec, kind in (("JUNCTIONS", "junction"), ("OUTFALLS", "outfall"), ("STORAGE", "storage")):
        for r in secs.get(sec, {}).get("rows", []):
            rows[f"{sec}|{r[0]}"] = r; inv = float(r[1])
            depth = float(r[2]) if sec in ("JUNCTIONS", "STORAGE") and len(r) > 2 else 0.0
            x, y = xy.get(r[0], (np.nan, np.nan))
            nodes.append(dict(id=r[0], kind=kind, x=x, y=y, ground=inv + depth, invert=inv, inflow_m3d=0.0))
    p.nodes = pd.DataFrame(nodes, columns=["id"] + NODE_COLS).set_index("id")
    vert = {}
    for r in secs.get("VERTICES", {}).get("rows", []): vert.setdefault(r[0], []).append([float(r[1]), float(r[2])])
    xs = {r[0]: r for r in secs.get("XSECTIONS", {}).get("rows", [])}
    elev = (_option(secs, "LINK_OFFSETS", "DEPTH") or "DEPTH").upper() == "ELEVATION"
    off = lambda v, node: (p.nodes.invert.get(node, np.nan) if v == "*" else float(v)) if elev else         p.nodes.invert.get(node, np.nan) + (0.0 if v == "*" else float(v))
    links = []; sections = {}
    for r in secs.get("CONDUITS", {}).get("rows", []):
        rows[f"CONDUITS|{r[0]}"] = r; a, b = r[1], r[2]
        x = xs.get(r[0]); rows[f"XSECTIONS|{r[0]}"] = x; D = float(x[2]) * mm if x else np.nan
        shp = SECTION_SHAPES.get(str(x[1]).upper()) if x else None
        if shp:                                            # a box or an open channel: its own section, no bore
            g = [float(v) for v in (list(x[2:6]) + [0, 0, 0, 0])[:4]]; m = mm / 1000.0
            s = dict(shape=shp, rise_m=g[0] * m, n=float(r[4]))
            if shp == "trapezoid": s.update(bottom_m=g[1] * m, z_left=g[2], z_right=g[3])
            else: s["span_m"] = g[1] * m
            nb = int(float(x[6])) if len(x) > 6 else 1
            if nb > 1: s["barrels"] = nb
            sections[r[0]] = s; D = np.nan
        ui, di = off(r[5], a), off(r[6], b)
        c = [list(xy[a])] + vert.get(r[0], []) + [list(xy[b])] if a in xy and b in xy else None
        links.append(dict(id=r[0], kind="conduit", from_node=a, to_node=b, length_m=float(r[3]), dn_mm=int(round(D)) if D == D else 0,
                          inside_mm=D, up_inv=ui, dn_inv=di, transfer=False, coords=c if vert.get(r[0]) else None))
    for r in secs.get("PUMPS", {}).get("rows", []):
        rows[f"PUMPS|{r[0]}"] = r
        links.append(dict(id=r[0], kind="pump", from_node=r[1], to_node=r[2], length_m=0.0, dn_mm=0, inside_mm=np.nan,
                          up_inv=np.nan, dn_inv=np.nan, transfer=False, coords=None))
    p.links = pd.DataFrame(links, columns=["id"] + LINK_COLS).set_index("id")
    p.sections = sections
    sub = {r[0]: r for r in secs.get("SUBAREAS", {}).get("rows", [])}
    poly = {}
    for r in secs.get("POLYGONS", {}).get("rows", []): poly.setdefault(r[0], []).append([float(r[1]), float(r[2])])
    cat = []
    for r in secs.get("SUBCATCHMENTS", {}).get("rows", []):
        rows[f"SUBCATCHMENTS|{r[0]}"] = r; s = sub.get(r[0]); rows[f"SUBAREAS|{r[0]}"] = s
        cat.append(dict(id=r[0], outlet=r[2], area_ha=float(r[3]), imperv_pc=float(r[4]), width_m=float(r[5]), slope_pc=float(r[6]),
                        n_imperv=float(s[1]) if s else 0.013, n_perv=float(s[2]) if s else 0.1, gauge=r[1], coords=poly.get(r[0])))
    p.catchments = pd.DataFrame(cat, columns=["id"] + CATCH_COLS).set_index("id")
    p.load_sets = {"design": {}}
    p.settings["link_offsets"] = "ELEVATION" if elev else "DEPTH"
    p.passthrough = dict(order=list(secs), titles={k: v["title"] for k, v in secs.items()},
                         sections={k: "\n".join(v["raw"]) for k, v in secs.items() if k not in MODELLED},
                         heads={k: v["head"] for k, v in secs.items() if k in MODELLED},
                         rows=rows, xs_other={k: v for k, v in xs.items() if k not in set(p.links.index)})
    return p


SECTION_SHAPES = {"RECT_CLOSED": "box", "RECT_OPEN": "rect_open", "TRAPEZOIDAL": "trapezoid"}
SWMM_SHAPE = {v: k for k, v in SECTION_SHAPES.items()}


def _fmt(tokens):
    return " ".join(f"{t:<16}" if i < 3 else f"{t:<10}" for i, t in enumerate(map(str, tokens))).rstrip()


def _num(v):
    return f"{float(v):.12g}"


def from_project(p, rain=None):
    pt = p.passthrough or {}; rows = pt.get("rows", {}); units = p.settings.get("units", "SI")
    mm = 304.8 if units == "US" else 1000.0
    n, L, C = p.nodes, p.links, p.catchments
    out = OrderedDict()
    def node_row(sec, i, r):
        old = list(rows.get(f"{sec}|{i}", []))
        if sec == "JUNCTIONS":
            base = old or [i, 0, 0, 0, 0, 0]; base[0], base[1], base[2] = i, _num(r.invert), _num(max(r.ground - r.invert, 0)); return base
        if sec == "OUTFALLS":
            base = old or [i, 0, "FREE", "NO"]; base[0], base[1] = i, _num(r.invert); return base
        base = old or [i, 0, 0, 0, "FUNCTIONAL", 1000, 0, 0, 0]
        base[0], base[1], base[2] = i, _num(r.invert), _num(max(r.ground - r.invert, 0)); return base
    kind_sec = {"junction": "JUNCTIONS", "manhole": "JUNCTIONS", "wetwell": "STORAGE", "storage": "STORAGE", "outfall": "OUTFALLS"}
    for sec in ("JUNCTIONS", "OUTFALLS", "STORAGE"):
        out[sec] = [node_row(sec, i, r) for i, r in n.iterrows() if kind_sec.get(r.kind) == sec]
    cond = L[L.kind == "conduit"]
    out["CONDUITS"] = []; out["XSECTIONS"] = []
    for i, r in cond.iterrows():
        old = list(rows.get(f"CONDUITS|{i}", [])) or [i, r.from_node, r.to_node, 0, 0.013 if units == "SI" else 0.013, 0, 0, 0, 0]
        elev = p.settings.get("link_offsets", "DEPTH") == "ELEVATION"
        o1 = r.up_inv if elev else r.up_inv - n.invert[r.from_node]; o2 = r.dn_inv if elev else r.dn_inv - n.invert[r.to_node]
        s = (p.sections or {}).get(i)
        old[:7] = [i, r.from_node, r.to_node, _num(r.length_m), _num(s["n"]) if s else old[4], _num(o1), _num(o2)]
        out["CONDUITS"].append(old)
        x = list(rows.get(f"XSECTIONS|{i}") or []) or [i, "CIRCULAR", 0, 0, 0, 0, 1]
        x[0] = i
        if s:                                              # a box or an open channel, in the file's length unit
            m = 1000.0 / mm
            g = [s["rise_m"], s.get("bottom_m", 0), s.get("z_left", 0), s.get("z_right", 0)] if s["shape"] == "trapezoid"                 else [s["rise_m"], s.get("span_m", 0), 0, 0]
            x = [i, SWMM_SHAPE[s["shape"]], _num(g[0] * m), _num(g[1] * m), _num(g[2]), _num(g[3]), int(s.get("barrels") or 1)]
        elif str(x[1]).upper() in SECTION_SHAPES:           # a section removed in the app: a circle again
            x = [i, "CIRCULAR", _num(r.inside_mm / mm), 0, 0, 0, 1]
        if str(x[1]).upper() in ("CIRCULAR", "FORCE_MAIN"): x[2] = _num(r.inside_mm / mm)
        out["XSECTIONS"].append(x)
    out["XSECTIONS"] += [list(v) for v in (pt.get("xs_other") or {}).values()]
    out["PUMPS"] = []
    for i, r in L[L.kind == "pump"].iterrows():
        old = list(rows.get(f"PUMPS|{i}") or [i, r.from_node, r.to_node, "*", "ON", 0, 0]); old[0:3] = [i, r.from_node, r.to_node]
        out["PUMPS"].append(old)
    out["SUBCATCHMENTS"], out["SUBAREAS"] = [], []
    for i, r in C.iterrows():
        old = list(rows.get(f"SUBCATCHMENTS|{i}", [])) or [i, r.gauge, r.outlet, 0, 0, 0, 0, 0]
        old[:7] = [i, r.gauge, r.outlet, _num(r.area_ha), _num(r.imperv_pc), _num(r.width_m), _num(r.slope_pc)]
        out["SUBCATCHMENTS"].append(old)
        s = list(rows.get(f"SUBAREAS|{i}") or []) or [i, 0, 0, 1.27, 5.08, 25, "OUTLET"]
        s[0], s[1], s[2] = i, _num(r.n_imperv), _num(r.n_perv); out["SUBAREAS"].append(s)
    out["COORDINATES"] = [[i, _num(r.x), _num(r.y)] for i, r in n.iterrows()]
    out["VERTICES"] = [[i, _num(x), _num(y)] for i, r in L.iterrows() if isinstance(r.coords, list) and len(r.coords) > 2 for x, y in r.coords[1:-1]]
    out["POLYGONS"] = [[i, _num(x), _num(y)] for i, r in C.iterrows() if isinstance(r.coords, list) for x, y in r.coords]
    order = list(pt.get("order") or [])
    if not order: order, extra = _generated(p, rain)
    else: extra = {}
    for k in MODELLED:
        if k not in order and out.get(k): order.insert(order.index("REPORT") if "REPORT" in order else len(order), k)
    lines = []
    titles = pt.get("titles", {})
    for k in order:
        lines.append(f"[{titles.get(k, 'Polygons' if k == 'POLYGONS' else k)}]")
        if k in out:
            lines += (pt.get("heads", {}) or {}).get(k, [])
            lines += [_fmt(r) for r in out[k]]
            lines.append("")
        elif k in extra: lines += extra[k] + [""]
        else: lines.append(pt["sections"].get(k, ""))
    return "\n".join(lines) + "\n"


def design_storm(idf, duration_min, step_min):
    """Alternating-block hyetograph from an IDF table {durations_min: [...], intensities: [... per h]}: the depth of
    every duration k x step from the curve (log-log interpolation), its increments ranked and placed alternately right
    and left of the centre. Returns [(minutes from start, intensity)]."""
    d = np.array(idf["durations_min"], float); i = np.array(idf["intensities"], float)
    n = int(round(duration_min / step_min)); t = step_min * np.arange(1, n + 1)
    it = np.exp(np.interp(np.log(t), np.log(d), np.log(i)))
    depth = it * t / 60.0; inc = np.diff(np.r_[0.0, depth])
    order = np.argsort(-inc); blocks = np.zeros(n); c = (n - 1) // 2
    for k, j in enumerate(order):
        pos = c + ((k + 1) // 2) * (1 if k % 2 else -1) if k else c
        blocks[min(max(pos, 0), n - 1)] = inc[j]
    return [(float(step_min * k), float(blocks[k] * 60.0 / step_min)) for k in range(n)]


def _generated(p, rain):
    """Sections for a project with no SWMM origin (SI: CMS, m, ha, mm/h)."""
    rain = rain or p.rain or {}
    step = int(rain.get("step_min", 5)); series = rain.get("series")
    if not series and rain.get("idf"): series = design_storm(rain["idf"], rain.get("duration_min", 60), step)
    if not series: raise ValueError("no rain: give the project a rain series or an IDF table (Settings → Rain)")
    dur = series[-1][0] + step
    end_h = int(dur // 60) + 3
    extra = OrderedDict()
    extra["TITLE"] = [p.name]
    extra["OPTIONS"] = ["FLOW_UNITS CMS", "INFILTRATION HORTON", "FLOW_ROUTING DYNWAVE", "LINK_OFFSETS DEPTH",
                        "START_DATE 01/01/2026", "START_TIME 00:00:00", "REPORT_START_DATE 01/01/2026", "REPORT_START_TIME 00:00:00",
                        "END_DATE 01/01/2026", f"END_TIME {end_h:02d}:00:00", "REPORT_STEP 00:01:00", "WET_STEP 00:01:00",
                        "DRY_STEP 01:00:00", "ROUTING_STEP 0:00:05", "ALLOW_PONDING NO", "INERTIAL_DAMPING PARTIAL",
                        "NORMAL_FLOW_LIMITED BOTH", "MIN_SURFAREA 1.167", "HEAD_TOLERANCE 0.0015"]
    gauges = sorted(set(p.catchments.gauge.astype(str))) or ["RG1"]
    extra["RAINGAGES"] = [f"{g} INTENSITY 0:{step:02d} 1.0 TIMESERIES TS1" for g in gauges]
    extra["INFILTRATION"] = [f"{i} 76.2 3.81 4 7 0" for i in p.catchments.index]     # Horton, the SWMM manual's typical values (mm/h)
    extra["TIMESERIES"] = [f"TS1 {int(t // 60)}:{int(t % 60):02d} {v:.4f}" for t, v in series]
    extra["REPORT"] = ["SUBCATCHMENTS ALL", "NODES ALL", "LINKS ALL"]
    order = ["TITLE", "OPTIONS", "RAINGAGES", "SUBCATCHMENTS", "SUBAREAS", "INFILTRATION", "JUNCTIONS", "OUTFALLS",
             "STORAGE", "CONDUITS", "PUMPS", "XSECTIONS", "TIMESERIES", "REPORT", "COORDINATES", "VERTICES", "POLYGONS"]
    return order, extra
