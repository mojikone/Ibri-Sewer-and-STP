"""The assistant's tools on ANY open project of the general app (api/general_api.SESSIONS). Read tools change nothing;
make_scenario, design_scenario and storm_scenario always work in a NEW scenario copied from the given one."""
import json
import numpy as np
from sewerapp.api.general_api import SESSIONS, clean
from sewerapp.assistant.tools import RULES, CURRENT, CRITERIA
from sewerapp.model.workspace import apply

FLAGS = ["over_limit", "over_vmax", "surcharged", "negative_slope", "under_vmin"]
ACTIONS: list = []                 # what the assistant asks the editor to show (select, zoom, profile); read by the endpoint
OPS = ["set", "add_node", "add_link", "add_catchment", "delete", "move_node", "split_link", "set_load", "set_setting", "set_rain"]


def _obj(props, req):
    return dict(type="object", properties=props, required=req, additionalProperties=False)


P = dict(type="string", description="open project id, e.g. p1"); S = dict(type="string", description="scenario id, e.g. base or S1")


def definitions():
    d = [
        dict(name="list_projects", description="Open projects with their scenarios.", input_schema=_obj({}, [])),
        dict(name="project_summary", description="Units, settings, element counts and the solved summary of a scenario (links, km, over the d/D limit, over v max, surcharged, flat or adverse, km under v min, problems).",
             input_schema=_obj(dict(project=P, scenario=S), ["project", "scenario"])),
        dict(name="query_links", description="Links filtered by a flag and a size range, sorted, at most `limit` rows, with their results.",
             input_schema=_obj(dict(project=P, scenario=S, flag=dict(type="string", enum=FLAGS + ["any_failing", "none"]),
                                    min_dn=dict(type="integer"), max_dn=dict(type="integer"),
                                    sort=dict(type="string", enum=["v_ms", "d_over_D", "q_ls", "dn_mm", "s_pc"]), limit=dict(type="integer")),
                               ["project", "scenario", "flag", "min_dn", "max_dn", "sort", "limit"])),
        dict(name="get_element", description="Every field (and result, for a link) of one node, link or catchment.",
             input_schema=_obj(dict(project=P, scenario=S, table=dict(type="string", enum=["nodes", "links", "catchments"]), id=dict(type="string")),
                               ["project", "scenario", "table", "id"])),
        dict(name="explain_link", description="Every check on one conduit, pass or fail, with value, limit and guideline page.",
             input_schema=_obj(dict(project=P, scenario=S, id=dict(type="string")), ["project", "scenario", "id"])),
        dict(name="make_scenario", description="Copy a scenario into a NEW one and apply edits to the new one, then solve. Each edit is {op, args}: op one of "
             + ", ".join(OPS) + "; args a JSON object string with that op's fields, e.g. op 'set', args '{\"table\":\"links\",\"ids\":[\"P-2\"],\"field\":\"dn_mm\",\"value\":315}'; "
             "'add_node' args '{\"id\":\"MH9\",\"kind\":\"manhole\",\"x\":10,\"y\":5,\"ground\":100}'; 'add_link' args '{\"from_node\":\"MH1\",\"to_node\":\"MH9\",\"dn_mm\":250}'.",
             input_schema=_obj(dict(project=P, scenario=S, name=dict(type="string"),
                                    edits=dict(type="array", items=_obj(dict(op=dict(type="string", enum=OPS), args=dict(type="string")), ["op", "args"]))),
                               ["project", "scenario", "name", "edits"])),
        dict(name="design_scenario", description="Copy a scenario into a NEW one and run the automated design there (sizes by the d/D limit at the size's minimum gradient, then the re-lay with crowns matched and minimum cover); returns the design report and the new summary.",
             input_schema=_obj(dict(project=P, scenario=S, name=dict(type="string")), ["project", "scenario", "name"])),
        dict(name="storm_scenario", description="Run a scenario on EPA SWMM 5 (needs rain and catchments): peaks per link, node and catchment, flooding, continuity.",
             input_schema=_obj(dict(project=P, scenario=S, top=dict(type="integer", description="how many links to return, highest peak first")),
                               ["project", "scenario", "top"])),
        dict(name="lookup_criterion", description="Search the design values with their guideline pages (current values first).",
             input_schema=_obj(dict(query=dict(type="string")), ["query"])),
        dict(name="show_on_map", description="Select elements in the engineer's editor and zoom the map to them (changes nothing in the model). Use it to point at the pipes or nodes you are talking about.",
             input_schema=_obj(dict(project=P, table=dict(type="string", enum=["nodes", "links"]), ids=dict(type="array", items=dict(type="string"))),
                               ["project", "table", "ids"])),
        dict(name="show_profile", description="Draw a long section in the engineer's editor: from a manhole or pipe to another (empty end: to the outfall), through optional via points (comma-separated). Changes nothing in the model.",
             input_schema=_obj(dict(project=P, scenario=S, start=dict(type="string"), end=dict(type="string"), via=dict(type="string")),
                               ["project", "scenario", "start", "end", "via"])),
    ]
    for t in d: t["strict"] = True
    return d


def _sess(a):
    if a["project"] not in SESSIONS: raise ValueError(f"no open project {a['project']}")
    s = SESSIONS[a["project"]]
    if a.get("scenario") and a["scenario"] not in s.scenarios: raise ValueError(f"no scenario {a['scenario']}")
    return s


def call(ctx, name, a):
    if name == "list_projects":
        return [dict(id=k, name=s.base.name, scenarios=[c.to_dict() for c in s.scenarios.values()]) for k, s in SESSIONS.items()]
    if name == "project_summary":
        s = _sess(a); p = s.model(a["scenario"]); _, summ = s.solve(a["scenario"])
        return clean(dict(name=p.name, units=p.settings.get("units", "SI"), crs=p.crs, nodes=len(p.nodes), links=len(p.links),
                          catchments=len(p.catchments), friction=p.settings["friction"], peaking=p.settings["peaking"]["method"],
                          design=p.settings["design"] | dict(catalogue="(catalogue sizes)"), load_sets=sorted(p.load_sets),
                          rain=bool(p.rain), summary=summ))
    if name == "query_links":
        s = _sess(a); res, _ = s.solve(a["scenario"])
        if res is None: return dict(count=0, rows=[], note="the scenario does not solve (see project_summary problems)")
        r = res
        if a["flag"] == "any_failing": r = r[r[[f for f in FLAGS if f in r.columns]].any(axis=1)]
        elif a["flag"] in r.columns: r = r[r[a["flag"]]]
        r = r[(r.dn_mm >= a["min_dn"]) & (r.dn_mm <= a["max_dn"])].sort_values(a["sort"])
        cols = [c for c in ["dn_mm", "length_m", "s_pc", "q_ls", "v_ms", "d_over_D", "limit", "v_check_ms"] + FLAGS if c in r.columns]
        return clean(dict(count=int(len(r)), rows=[dict(id=i, **x) for i, x in zip(r.index[:max(1, min(a["limit"], 200))], r[cols].head(max(1, min(a["limit"], 200))).round(4).to_dict("records"))]))
    if name == "get_element":
        s = _sess(a); p = s.model(a["scenario"]); t = getattr(p, a["table"])
        if a["id"] not in t.index: raise ValueError(f"no {a['table'][:-1]} {a['id']}")
        out = {k: v for k, v in t.loc[a["id"]].to_dict().items() if k != "coords"}
        if a["table"] == "links":
            res, _ = s.solve(a["scenario"])
            if res is not None: out["results"] = {k: v for k, v in res.loc[a["id"]].to_dict().items()}
        return clean(out)
    if name == "explain_link":
        s = _sess(a); p = s.model(a["scenario"]); res, _ = s.solve(a["scenario"])
        if res is None or a["id"] not in res.index: raise ValueError(f"no solved link {a['id']}")
        r = res.loc[a["id"]]; d = p.settings["design"]; L = p.links.loc[a["id"]]
        checks = [dict(rule=RULES[0][0], source=RULES[0][1], value=r.d_over_D, limit=r.limit, ok=not bool(r.over_limit)),
                  dict(rule="maximum velocity", source=RULES[2][1], value=r.v_ms, limit=d["v_max"], ok=not bool(r.over_vmax)),
                  dict(rule="gradient positive (no flat or adverse pipe)", source="G203 p29 4.3.1", value=r.s_pc, limit=0, ok=not bool(r.negative_slope))]
        if "v_check_ms" in res.columns:
            checks.append(dict(rule=f"self-cleansing {d['v_min']} m/s at the check load (above DN{p.settings.get('self_cleansing_min_dn', 0)})",
                               source=RULES[1][1], value=r.v_check_ms, limit=d["v_min"], ok=not bool(r.get("under_vmin", False))))
        cover = [p.nodes.ground[L.from_node] - (L.up_inv + L.inside_mm / 1000), p.nodes.ground[L.to_node] - (L.dn_inv + L.inside_mm / 1000)]
        checks.append(dict(rule="minimum cover over the crown, both ends", source=RULES[4][1], value=[round(float(c), 3) for c in cover],
                           limit=d["cover_min"], ok=bool(min(cover) >= d["cover_min"] - 1e-9)))
        return clean(dict(link=a["id"], dn_mm=L.dn_mm, q_ls=r.q_ls, checks=checks))
    if name == "make_scenario":
        s = _sess(a); c = s.copy_scenario(a["scenario"], a["name"]); done = []
        for e in a["edits"]:
            ev = dict(json.loads(e["args"]), op=e["op"]); s.edit(c.id, ev); done.append(e["op"])
        _, summ = s.solve(c.id)
        return clean(dict(scenario=c.id, edits=done, summary=summ))
    if name == "design_scenario":
        s = _sess(a); c = s.copy_scenario(a["scenario"], a["name"]); e = dict(op="design"); s.edit(c.id, e)
        _, summ = s.solve(c.id); return clean(dict(scenario=c.id, report=s.scenarios[c.id].edits[-1].get("report"), summary=summ))
    if name == "storm_scenario":
        from sewerapp.engine import storm
        s = _sess(a); r = storm.run(s.model(a["scenario"]))
        top = sorted(r["links"].items(), key=lambda kv: -kv[1]["q_peak"])[:max(1, min(a["top"], 100))]
        flooded = {k: v for k, v in r["nodes"].items() if v["flooding_peak"] > 0}
        return clean(dict(summary=r["summary"], links=dict(top), flooded_nodes=flooded, subcatchments=r["subcatchments"]))
    if name == "lookup_criterion":
        from sewerapp.assistant import tools as T
        return T.call(None, "lookup_criterion", a)
    if name == "show_on_map":
        s = _sess(a); p = s.base; t = getattr(p, a["table"])
        ids = [str(i) for i in a["ids"]][:5000]
        ACTIONS.append(dict(kind="select", table=a["table"], ids=ids)); return dict(shown=len(ids))
    if name == "show_profile":
        s = _sess(a); p = s.model(a["scenario"])
        for x in [a["start"], a["end"]] + [v.strip() for v in a["via"].split(",") if v.strip()]:
            if x and x not in p.nodes.index and x not in p.links.index: raise ValueError(f"no node or pipe {x}")
        ACTIONS.append(dict(kind="profile", start=a["start"], end=a["end"], via=a["via"])); return dict(drawn=True)
    raise ValueError(f"unknown tool {name}")
