"""The assistant as an agent (2026-11-23 v5, F21): it reads the engineer's own folders, builds a model from them and
runs it. Three guards:
- Folders: only the ones the engineer has registered on this computer (a JSON list, W19_AGENT_FOLDERS or
  ~/.w19/agent_folders.json); a path outside them, or any folder request that arrives over the shared web link, is
  refused. Registering a folder is refused over the shared link too.
- Changes: only to projects and scenarios the agent made itself (a new project, an import, or a scenario copied by
  make_scenario / design_scenario); the engineer's own scenarios are never touched.
- Undo: every change is one edit of the scenario, so Undo in the editor takes it back."""
import json, os

FOLDERS_FILE = os.environ.get("W19_AGENT_FOLDERS") or os.path.join(os.path.expanduser("~"), ".w19", "agent_folders.json")
CTX = dict(remote=False)                     # set by the endpoint for each request: True when it came over the shared link
MADE: set = set()                            # (project, scenario) the agent made; (project, "*") for a whole project
TEXT_EXT = {".csv", ".txt", ".md", ".inp", ".json", ".geojson", ".tsv", ".prj", ".rpt", ".ini", ".yaml", ".yml", ".xml"}
GIS_EXT = {".gpkg", ".geojson", ".shp", ".zip", ".json", ".kml"}


# ---- folders
def folders():
    try:
        with open(FOLDERS_FILE, encoding="utf-8") as f: return [x for x in json.load(f) if isinstance(x, str)]
    except (OSError, ValueError): return []


def _save(lst):
    os.makedirs(os.path.dirname(FOLDERS_FILE), exist_ok=True)
    with open(FOLDERS_FILE, "w", encoding="utf-8") as f: json.dump(lst, f, indent=1)


def add_folder(path):
    p = os.path.realpath(os.path.expanduser(path.strip().strip('"')))
    if not os.path.isdir(p): raise ValueError(f"no folder {path}")
    lst = folders()
    if p not in lst: lst.append(p); _save(lst)
    return lst


def remove_folder(path):
    lst = [x for x in folders() if os.path.normcase(x) != os.path.normcase(os.path.realpath(path))]
    _save(lst); return lst


def resolve(path):
    """A path inside a registered folder (relative paths are taken from the first folder); else ValueError."""
    if CTX.get("remote"): raise ValueError("folder access works only on the engineer's own computer, not over the shared web link")
    fs = folders()
    if not fs: raise ValueError("no folder is registered: the engineer adds one with Assistant > Folders")
    p = path.strip().strip('"')
    p = os.path.realpath(p if os.path.isabs(p) else os.path.join(fs[0], p))
    for f in fs:
        try:
            if os.path.commonpath([os.path.normcase(p), os.path.normcase(f)]) == os.path.normcase(f): return p
        except ValueError: pass                                  # another drive
    raise ValueError(f"{path} is outside the registered folders ({'; '.join(fs)})")


def own(pid, sid, sessions=None):
    if not ((pid, "*") in MADE or (pid, sid) in MADE):
        raise ValueError(f"scenario {sid} of project {pid} is the engineer's: copy it with make_scenario and work in the copy")
    if sessions and (pid, "*") not in MADE:                      # an alternative it shares with the engineer's scenarios would
        s = sessions[pid]; mine = s.alts_of(sid)                 # carry its edits into them
        for o in s.scenarios:
            if (pid, o) in MADE: continue
            shared = [c for c, a in s.alts_of(o).items() if mine.get(c) == a]
            if shared: raise ValueError(f"scenario {sid} shares the {', '.join(shared)} alternative with the engineer's scenario {o}: make a new copy with make_scenario")


# ---- tool definitions (strict: every field required, "" or 0 for unused)
def _obj(props, req):
    return dict(type="object", properties=props, required=req, additionalProperties=False)


Str = lambda d: dict(type="string", description=d)
P = Str("open project id, e.g. p1"); S = Str("scenario id, e.g. base or S1"); PATH = Str("a path inside a registered folder (absolute, or relative to the first folder)")
EDIT_OPS = ["set", "set_many", "set_values", "add_node", "add_link", "add_catchment", "add_run", "delete", "move_node", "split_link", "reconnect", "reverse",
            "set_loads", "set_unit_rows", "set_infiltration", "set_setting", "set_rain", "set_pump", "set_ppipe", "set_storage", "set_outlet", "set_tailwater",
            "set_hydrology", "set_controls", "set_inverts", "set_prototype"]


def definitions():
    return [
        dict(name="list_folders", description="The folders the engineer has registered for you to read.", input_schema=_obj({}, [])),
        dict(name="list_files", description="Files and sub-folders in a registered folder (name, kind, size in kB), at most 500, optionally filtered by extension (e.g. '.gpkg', '' for all).",
             input_schema=_obj(dict(path=PATH, ext=Str("extension filter or ''")), ["path", "ext"])),
        dict(name="read_text_file", description="Lines of a text file (CSV, TXT, INP, JSON, MD...) in a registered folder: from start_line (1-based), at most 400 lines.",
             input_schema=_obj(dict(path=PATH, start_line=dict(type="integer"), max_lines=dict(type="integer")), ["path", "start_line", "max_lines"])),
        dict(name="inspect_layer", description="A GIS layer in a registered folder (GeoPackage, shapefile, GeoJSON, zipped shapefile): CRS, geometry types, feature count, bounds, fields with type and numeric range, the first 5 rows.",
             input_schema=_obj(dict(path=PATH), ["path"])),
        dict(name="new_project", description="A NEW empty project (yours to build): name and EPSG code of the coordinates. Returns its id; then add elements with edit_model on scenario 'base'.",
             input_schema=_obj(dict(name=Str("project name"), crs=dict(type="integer", description="EPSG code, e.g. 32640")), ["name", "crs"])),
        dict(name="import_network", description="A NEW project from a node layer and a link layer in the registered folders. node_map / link_map: JSON object strings mapping this app's fields to the layer's fields, "
             "nodes {id, kind, ground, invert} and links {id, dn_mm}; a field left out takes the default (ids numbered, ground 0, invert ground - 1.5, the smallest catalogue size), so read the fields with inspect_layer first and set the terrain afterwards if the layer has no levels. Link ends are snapped to nodes within snap_m.",
             input_schema=_obj(dict(nodes_path=PATH, links_path=PATH, node_map=Str("JSON object string"), link_map=Str("JSON object string"), name=Str("project name"), snap_m=dict(type="number")),
                               ["nodes_path", "links_path", "node_map", "link_map", "name", "snap_m"])),
        dict(name="import_swmm", description="A NEW project from an EPA SWMM 5 input file (.inp) in the registered folders.", input_schema=_obj(dict(path=PATH), ["path"])),
        dict(name="edit_model", description="Apply edits to a project or scenario YOU made (new_project, import_*, make_scenario, design_scenario), as ONE undo step, then solve. Each edit is {op, args}: op one of "
             + ", ".join(EDIT_OPS) + "; args a JSON object string with that op's fields, e.g. add_node '{\"id\":\"MH1\",\"kind\":\"manhole\",\"x\":500000,\"y\":2600000,\"ground\":110,\"invert\":108}' (kind manhole, outfall, wet_well, pond, pressure_junction), "
             "add_link '{\"id\":\"P1\",\"from_node\":\"MH1\",\"to_node\":\"O1\",\"dn_mm\":250}' (kind conduit, pump, pressure_pipe, orifice, weir), set_loads '{\"set\":\"design\",\"values\":{\"MH1\":50}}' (m3/d), "
             "set '{\"table\":\"links\",\"ids\":[\"P1\"],\"field\":\"dn_mm\",\"value\":300}', set_setting '{\"path\":\"design.v_min\",\"value\":0.75}'. At most 5,000 edits.",
             input_schema=_obj(dict(project=P, scenario=S, edits=dict(type="array", items=_obj(dict(op=dict(type="string", enum=EDIT_OPS), args=dict(type="string")), ["op", "args"]))),
                               ["project", "scenario", "edits"])),
        dict(name="loads_from_layer", description="LoadBuilder on a layer in the registered folders: each feature's field value x scale to the nearest structure. apply false previews; apply true writes it (only on your own scenario). "
             "target 'load' (m3/d into the design load set) or 'unit' (counts of the unit load named in unit).",
             input_schema=_obj(dict(project=P, scenario=S, path=PATH, field=Str("numeric field"), scale=dict(type="number"), target=dict(type="string", enum=["load", "unit"]), unit=Str("unit load name or ''"), apply=dict(type="boolean")),
                               ["project", "scenario", "path", "field", "scale", "target", "unit", "apply"])),
        dict(name="terrain_from_file", description="TRex on a GeoTIFF or VRT in the registered folders: ground levels of every structure; keep_depth moves the inverts with the ground. Only on your own scenario.",
             input_schema=_obj(dict(project=P, scenario=S, path=PATH, keep_depth=dict(type="boolean")), ["project", "scenario", "path", "keep_depth"])),
        dict(name="run_analysis", description="Run a check on a scenario: 'steady' (the solved summary), 'validate' (the notification list: errors and warnings per element, at most 200), 'rational' (rational-method peaks, needs C and Tc on the catchments and an IDF table).",
             input_schema=_obj(dict(project=P, scenario=S, kind=dict(type="string", enum=["steady", "validate", "rational"])), ["project", "scenario", "kind"])),
    ]


NAMES = {d["name"] for d in definitions()}


def _layer(path):
    """A vector layer of a known type (a GDAL .vrt could point at files outside the registered folders: not opened)."""
    from sewerapp.io import gis_import
    if os.path.splitext(path)[1].lower() not in GIS_EXT: raise ValueError(f"not a layer type this tool opens ({', '.join(sorted(GIS_EXT))})")
    return gis_import.read_layer(path)


TERRAIN_EXT = {".tif", ".tiff", ".vrt"}


def call(name, a, sessions, open_project, clean, actions):
    if name == "list_folders":
        if CTX.get("remote"): raise ValueError("folder access works only on the engineer's own computer, not over the shared web link")
        return dict(folders=folders())
    if name == "list_files":
        p = resolve(a["path"])
        if not os.path.isdir(p): raise ValueError(f"not a folder: {p}")
        ext = (a.get("ext") or "").lower(); rows = []
        for e in sorted(os.scandir(p), key=lambda e: (not e.is_dir(), e.name.lower())):
            if ext and not e.is_dir() and not e.name.lower().endswith(ext): continue
            rows.append(dict(name=e.name, kind="folder" if e.is_dir() else "file", kb=None if e.is_dir() else round(e.stat().st_size / 1024, 1)))
            if len(rows) >= 500: break
        return dict(folder=p, entries=rows)
    if name == "read_text_file":
        p = resolve(a["path"])
        if os.path.splitext(p)[1].lower() not in TEXT_EXT: raise ValueError(f"not a text file this tool reads ({', '.join(sorted(TEXT_EXT))})")
        s0, n = max(1, int(a["start_line"] or 1)), max(1, min(int(a["max_lines"] or 200), 400)); out = []; total = 0
        with open(p, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                total = i
                if s0 <= i < s0 + n: out.append(line.rstrip("\n")[:2000])
        return dict(path=p, from_line=s0, lines=out, total_lines=total)
    if name == "inspect_layer":
        import pandas as pd
        p = resolve(a["path"]); g = _layer(p)
        fields = []
        for c in g.columns:
            if c == "geometry": continue
            col = g[c]; d = dict(name=c, type=str(col.dtype), nulls=int(col.isna().sum()))
            if pd.api.types.is_numeric_dtype(col) and col.notna().any(): d.update(min=float(col.min()), max=float(col.max()))
            fields.append(d)
        try: b = [float(x) for x in g.total_bounds] if len(g) and "geometry" in g else None
        except Exception: b = None                                # a table with no geometry
        return clean(dict(path=p, crs=str(g.crs) if g.crs else None, features=int(len(g)), geometry=sorted(set(g.geom_type.dropna())), bounds=b, fields=fields,
                          head=g.drop(columns="geometry").head(5).to_dict("records")))
    if name == "new_project":
        from sewerapp.model.general import Project
        pr = Project(name=a["name"], crs=int(a["crs"])); pr.load_sets = {"design": {}}; pr.settings["design_load"] = "design"
        pid = open_project(pr); MADE.add((pid, "*")); actions.append(dict(kind="open_project", project=pid))
        return dict(project=pid, scenario="base", note="empty: add structures and conduits with edit_model")
    if name == "import_network":
        from sewerapp.io import gis_import
        fn, fl = resolve(a["nodes_path"]), resolve(a["links_path"])
        pr = gis_import.import_layers(fn, fl, json.loads(a["node_map"] or "{}") or None, json.loads(a["link_map"] or "{}") or None,
                                      name=a["name"] or "Imported network", snap_m=float(a["snap_m"] or 1.0))
        pid = open_project(pr); MADE.add((pid, "*")); actions.append(dict(kind="open_project", project=pid))
        _, summ = sessions[pid].solve("base")
        return clean(dict(project=pid, scenario="base", nodes=len(pr.nodes), links=len(pr.links), summary=summ))
    if name == "import_swmm":
        from sewerapp.io import swmm_inp
        p = resolve(a["path"])
        with open(p, encoding="utf-8", errors="ignore") as f: pr = swmm_inp.to_project(f.read(), os.path.splitext(os.path.basename(p))[0])
        pid = open_project(pr); MADE.add((pid, "*")); actions.append(dict(kind="open_project", project=pid))
        return dict(project=pid, scenario="base", nodes=len(pr.nodes), links=len(pr.links))
    if name in ("edit_model", "loads_from_layer", "terrain_from_file", "run_analysis"):
        if a["project"] not in sessions: raise ValueError(f"no open project {a['project']}")
        s = sessions[a["project"]]
        if a["scenario"] not in s.scenarios: raise ValueError(f"no scenario {a['scenario']}")
    if name == "edit_model":
        own(a["project"], a["scenario"], sessions)
        if len(a["edits"]) > 5000: raise ValueError("at most 5,000 edits in one call")
        ops = [dict(json.loads(e["args"]), op=e["op"]) for e in a["edits"]]
        s.edit(a["scenario"], ops[0] if len(ops) == 1 else dict(op="batch", ops=ops))
        _, summ = s.solve(a["scenario"]); actions.append(dict(kind="refresh", project=a["project"]))
        return clean(dict(applied=len(ops), undo="one step", summary=summ))
    if name == "loads_from_layer":
        from sewerapp.engine import tools_v4
        p = s.model(a["scenario"]); g = _layer(resolve(a["path"]))
        per, rep = tools_v4.loadbuilder(p, g, a["field"], float(a["scale"] or 1.0))
        top = per.sort_values(ascending=False).head(10)
        out = dict(report=rep, top=[dict(id=k, value=float(v)) for k, v in top.items()])
        if a["apply"]:
            own(a["project"], a["scenario"], sessions); ls = p.settings["design_load"]
            if a["target"] == "unit":
                if not a["unit"]: raise ValueError("name the unit load the counts are of")
                cur = (getattr(p, "unit_rows", {}) or {}).get(ls, {})
                e = dict(op="batch", ops=[dict(op="set_unit_rows", set=ls, ids=[n], rows=[r for r in cur.get(n, []) if r[0] != a["unit"]] + [[a["unit"], float(v)]]) for n, v in per.items()])
            else: e = dict(op="set_loads", set=ls, values={n: float(v) for n, v in per.items()})
            s.edit(a["scenario"], e); _, out["summary"] = s.solve(a["scenario"]); out["applied"] = True; actions.append(dict(kind="refresh", project=a["project"]))
        return clean(out)
    if name == "terrain_from_file":
        from sewerapp.engine import tools_v4
        own(a["project"], a["scenario"], sessions); p = s.model(a["scenario"]); tp = resolve(a["path"])
        if os.path.splitext(tp)[1].lower() not in TERRAIN_EXT: raise ValueError("a terrain is a GeoTIFF (.tif) or a VRT (.vrt)")
        lv, bad = tools_v4.trex(p, tp)
        if not lv: raise ValueError("no structure lies on the terrain's cells")
        ops = [dict(op="set_values", table="nodes", field="ground", values=lv)]
        if a["keep_depth"]:
            g0, i0 = p.nodes.ground.astype(float), p.nodes.invert.astype(float)
            inv = {n: lv[n] - float(g0[n] - i0[n]) for n in lv if g0[n] == g0[n] and i0[n] == i0[n]}
            if inv: ops.append(dict(op="set_inverts", values=inv))
        s.edit(a["scenario"], dict(op="batch", ops=ops)); _, summ = s.solve(a["scenario"]); actions.append(dict(kind="refresh", project=a["project"]))
        return clean(dict(updated=len(lv), off_terrain=bad[:50], off_terrain_count=len(bad), summary=summ))
    if name == "run_analysis":
        if a["kind"] == "steady": _, summ = s.solve(a["scenario"]); return clean(dict(summary=summ))
        if a["kind"] == "validate":
            from sewerapp.engine import validate as V
            res, _ = s.solve(a["scenario"]); items = V.run(s.model(a["scenario"]), res)
            return clean(dict(count=len(items), items=items[:200]))
        from sewerapp.engine import tools_v4
        rows, summ = tools_v4.rational(s.model(a["scenario"]))
        top = sorted(rows.items(), key=lambda kv: -kv[1]["q_rational_ls"])[:30]
        return clean(dict(report=summ, top=[dict(id=k, **v) for k, v in top]))
    raise ValueError(f"unknown tool {name}")
