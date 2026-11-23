"""The assistant's link to the engineer's open QGIS (2026-11-23 v5), through the QGIS MCP plugin already installed
there (it listens on this computer only, port 9876, length-prefixed JSON; the token, if the engineer set one, is read
from QGIS_MCP_TOKEN).

Read-only by design: only the commands in READ below are ever sent, plus ADD (a layer from a registered folder into
the "W19" group, the engineer's project left unsaved). The plugin's code execution, Processing, editing, saving and
settings commands are never sent, whatever the model asks; and nothing reaches QGIS from a request that came over
the shared web link (agent.CTX["remote"])."""
import json, os, socket, struct

HOST, PORT = "127.0.0.1", int(os.environ.get("QGIS_PORT", 9876))
HEADER = struct.Struct(">I")
READ = {"ping", "get_qgis_info", "get_project_info", "get_layers", "get_layer_tree", "get_layer_info", "get_layer_schema", "get_layer_crs",
        "get_layer_extent", "get_layer_features", "get_selection", "get_unique_values", "get_field_statistics", "get_canvas_extent", "find_layer",
        "get_active_layer", "identify_features"}
ADD = {"add_vector_layer", "add_raster_layer", "create_layer_group", "move_layer_to_group", "find_layer"}
GROUP = "W19"


def call(cmd, params=None, timeout=60.0):
    if cmd not in READ | ADD: raise ValueError(f"{cmd} is not a command the app sends to QGIS")
    msg = {"type": cmd, "params": params or {}}
    tok = os.environ.get("QGIS_MCP_TOKEN", "").strip()
    if tok: msg["token"] = tok
    try: s = socket.create_connection((HOST, PORT), timeout=timeout)
    except OSError:
        raise ValueError("QGIS is not reachable: open QGIS with the QGIS MCP plugin running (Plugins > QGIS MCP > Start server)")
    try:
        body = json.dumps(msg).encode("utf-8"); s.sendall(HEADER.pack(len(body)) + body)
        head = b""
        while len(head) < 4:
            c = s.recv(4 - len(head))
            if not c: raise ValueError("QGIS closed the connection")
            head += c
        n = HEADER.unpack(head)[0]
        if n > 50_000_000: raise ValueError("QGIS sent a reply too large to use")
        buf = bytearray()
        while len(buf) < n:
            c = s.recv(min(65536, n - len(buf)))
            if not c: raise ValueError("QGIS closed the connection mid-reply")
            buf.extend(c)
    finally:
        s.close()
    r = json.loads(bytes(buf).decode("utf-8"))
    if isinstance(r, dict) and r.get("status") == "error": raise ValueError(f"QGIS: {r.get('message')}")
    return r.get("result", r) if isinstance(r, dict) else r


def _obj(props, req):
    return dict(type="object", properties=props, required=req, additionalProperties=False)


LID = dict(type="string", description="the layer id from qgis_layers")


def definitions():
    return [
        dict(name="qgis_project", description="The engineer's open QGIS: version, project file, CRS, layer count, map extent. Read only.", input_schema=_obj({}, [])),
        dict(name="qgis_layers", description="The layers of the open QGIS project (id, name, type, feature count, visibility) and its layer tree. Read only.",
             input_schema=_obj(dict(limit=dict(type="integer"), offset=dict(type="integer")), ["limit", "offset"])),
        dict(name="qgis_layer", description="One QGIS layer: its fields with types, CRS, extent, source and feature count. Read only.", input_schema=_obj(dict(layer_id=LID), ["layer_id"])),
        dict(name="qgis_features", description="Attribute rows of a QGIS layer, at most 200 (geometry as WKT only when asked, at most 50 rows then), optionally filtered by a QGIS expression such as \"DN\" > 300. Read only.",
             input_schema=_obj(dict(layer_id=LID, limit=dict(type="integer"), offset=dict(type="integer"), expression=dict(type="string", description="QGIS filter expression or ''"),
                                    include_geometry=dict(type="boolean")), ["layer_id", "limit", "offset", "expression", "include_geometry"])),
        dict(name="qgis_selection", description="The features the engineer has selected in a QGIS layer. Read only.", input_schema=_obj(dict(layer_id=LID), ["layer_id"])),
        dict(name="qgis_field", description="A field of a QGIS layer: its distinct values (at most 200) and, for numbers, statistics. Read only.",
             input_schema=_obj(dict(layer_id=LID, field=dict(type="string")), ["layer_id", "field"])),
        dict(name="qgis_add_layer", description="Add a layer from a registered folder (GeoPackage, shapefile, GeoJSON, GeoTIFF) to the engineer's QGIS, in the group 'W19'. Only when the engineer asks; the QGIS project is not saved.",
             input_schema=_obj(dict(path=dict(type="string", description="a path inside a registered folder"), name=dict(type="string")), ["path", "name"])),
    ]


NAMES = {d["name"] for d in definitions()}


def run(name, a, resolve):
    """One tool call; resolve() is the agent's registered-folder check (it also refuses the shared link)."""
    from sewerapp.assistant import agent
    if agent.CTX.get("remote"): raise ValueError("QGIS is reached only from the engineer's own computer, not over the shared web link")
    if name == "qgis_project":
        info = call("get_qgis_info"); proj = call("get_project_info")
        try: ext = call("get_canvas_extent")
        except ValueError: ext = None
        return dict(qgis=info, project=proj, canvas_extent=ext)
    if name == "qgis_layers":
        lim, off = max(1, min(int(a.get("limit") or 50), 200)), max(0, int(a.get("offset") or 0))
        return dict(layers=call("get_layers", dict(limit=lim, offset=off)), tree=call("get_layer_tree"))
    if name == "qgis_layer":
        lid = a["layer_id"]; out = dict(info=call("get_layer_info", dict(layer_id=lid)))
        for k, cmd in (("schema", "get_layer_schema"), ("crs", "get_layer_crs"), ("extent", "get_layer_extent")):
            try: out[k] = call(cmd, dict(layer_id=lid))
            except ValueError as x: out[k] = dict(error=str(x))
        return out
    if name == "qgis_features":
        geom = bool(a.get("include_geometry")); lim = max(1, min(int(a.get("limit") or 50), 50 if geom else 200))
        p = dict(layer_id=a["layer_id"], limit=lim, offset=max(0, int(a.get("offset") or 0)), include_geometry=geom)
        if (a.get("expression") or "").strip(): p["expression"] = a["expression"]
        return call("get_layer_features", p)
    if name == "qgis_selection":
        return call("get_selection", dict(layer_id=a["layer_id"]))
    if name == "qgis_field":
        out = dict(values=call("get_unique_values", dict(layer_id=a["layer_id"], field=a["field"], limit=200)))
        try: out["statistics"] = call("get_field_statistics", dict(layer_id=a["layer_id"], field_name=a["field"]))
        except ValueError: pass
        return out
    if name == "qgis_add_layer":
        p = resolve(a["path"]); ext = os.path.splitext(p)[1].lower()
        raster = ext in (".tif", ".tiff")
        if not raster and ext not in (".gpkg", ".shp", ".geojson", ".json", ".kml"): raise ValueError("a layer is a GeoPackage, shapefile, GeoJSON, KML or GeoTIFF")
        lay = call("add_raster_layer" if raster else "add_vector_layer", dict(path=p, name=a.get("name") or os.path.splitext(os.path.basename(p))[0]))
        try:
            call("create_layer_group", dict(name=GROUP))
        except ValueError: pass                                         # it exists already
        try: call("move_layer_to_group", dict(layer_id=lay.get("id"), group_name=GROUP))
        except ValueError: pass
        return dict(added=lay, group=GROUP, note="added to the open QGIS project, which is not saved")
    raise ValueError(f"unknown tool {name}")
