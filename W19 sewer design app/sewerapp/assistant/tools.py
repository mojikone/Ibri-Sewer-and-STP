"""The assistant's tools: strict JSON schemas and their implementations over the project. Read tools never change
anything; make_whatif creates a new scenario and edits only that one."""
import os, re
import numpy as np
from sewerapp.api import tools as menu

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CRITERIA = os.path.join(REPO, "_BRAIN", "02_DESIGN_CRITERIA.md")
FLAGS = ["over_limit", "over_3ms", "under075", "needs_relay"]
# the rules explain_pipe applies, each with its source (PAM-GUD-203 pages as in _BRAIN/02_DESIGN_CRITERIA.md)
RULES = [("d/D at the design-year peak <= 0.65 to DN355, <= 0.50 above", "PAM-GUD-203 p27 Table 10"),
         ("self-cleansing: 0.75 m/s at the peak (pipes above DN200, 2031 peak, the client's rule)", "PAM-GUD-203 p26"),
         ("maximum velocity 3.0 m/s", "PAM-GUD-203 p27"),
         ("minimum gradient by size", "PAM-GUD-203 p29 Table 11"),
         ("minimum cover 1.3 m over the crown", "PAM-GUD-203 p33 4.6.3"),
         ("maximum cover approximately 10-12 m, recommended", "PAM-GUD-203 p33 4.6.3")]


def _obj(props, required):
    return dict(type="object", properties=props, required=required, additionalProperties=False)


S = dict(type="string", description="scenario id, e.g. SC1-2056 or a what-if id W1")


def definitions():
    d = [
        dict(name="list_scenarios", description="All scenarios: the 12 read-only W18 cases and any what-ifs.", input_schema=_obj({}, [])),
        dict(name="get_summary", description="Summary of a scenario's solved results: pipes, km, pipes over the d/D limit, over 3 m/s, km above DN200 under 0.75 m/s at 2031, pipes needing re-lay.",
             input_schema=_obj(dict(scenario=S), ["scenario"])),
        dict(name="query_pipes", description="Pipes of a scenario filtered by a flag and/or size range, sorted, at most `limit` rows.",
             input_schema=_obj(dict(scenario=S, flag=dict(type="string", enum=FLAGS + ["any_failing", "none"]),
                                    min_dn=dict(type="integer"), max_dn=dict(type="integer"),
                                    sort=dict(type="string", enum=["v_ms", "v2031_ms", "d_over_D", "q_ls", "dn_mm"]),
                                    limit=dict(type="integer")), ["scenario", "flag", "min_dn", "max_dn", "sort", "limit"])),
        dict(name="get_pipe", description="Every result and property of one pipe, by label (e.g. P1-P151).",
             input_schema=_obj(dict(scenario=S, label=dict(type="string")), ["scenario", "label"])),
        dict(name="explain_pipe", description="Every design check on one pipe, pass or fail, with the value, the limit and the guideline page.",
             input_schema=_obj(dict(scenario=S, label=dict(type="string")), ["scenario", "label"])),
        dict(name="make_whatif", description="Create a NEW what-if scenario from a scenario, apply edits (pipe size dn_mm or gradient s_pc in percent), re-solve, and return the edited pipes' results and the new summary.",
             input_schema=_obj(dict(scenario=S, name=dict(type="string"),
                                    edits=dict(type="array", items=_obj(dict(label=dict(type="string"),
                                                                            field=dict(type="string", enum=["dn_mm", "s_pc"]),
                                                                            value=dict(type="number")), ["label", "field", "value"]))),
                               ["scenario", "name", "edits"])),
        dict(name="compare_scenarios", description="Pipes whose size, flow, velocity or d/D differ between two scenarios.",
             input_schema=_obj(dict(a=S, b=S), ["a", "b"])),
        dict(name="run_tool", description="Run a tool of the app's Tools menu on a scenario: checks, selfcleansing, stations, quantities, compare_sewergems.",
             input_schema=_obj(dict(scenario=S, name=dict(type="string", enum=["checks", "selfcleansing", "stations", "quantities", "compare_sewergems"])),
                               ["scenario", "name"])),
        dict(name="lookup_criterion", description="Search the project's design-criteria register (every value with its guideline page) for a word or phrase.",
             input_schema=_obj(dict(query=dict(type="string")), ["query"])),
    ]
    for t in d: t["strict"] = True
    return d


def _row(res, label):
    idx = res.index[res.label == label]
    if not len(idx): raise ValueError(f"no pipe {label}")
    return int(idx[0]), res.loc[idx[0]]


def _clean(d):
    return {k: (v.item() if isinstance(v, np.generic) else v) for k, v in d.items()}


def call(project, name, a):
    if name == "list_scenarios":
        return [dict(id=s.id, name=s.name, read_only=s.parent is None, edits=len(s.edits)) for s in project.scenarios.values()]
    if name == "get_summary":
        return project.results(a["scenario"])[1]
    if name == "query_pipes":
        res, _ = project.results(a["scenario"]); r = res
        if a["flag"] == "any_failing": r = r[r.over_limit | r.over_3ms]
        elif a["flag"] in FLAGS: r = r[r[a["flag"]]]
        r = r[(r.dn_mm >= a["min_dn"]) & (r.dn_mm <= a["max_dn"])].sort_values(a["sort"])
        return dict(count=int(len(r)), rows=r.head(max(1, min(a["limit"], 200)))[
            ["label", "dn_mm", "length_m", "s_pc", "q_ls", "v_ms", "d_over_D", "v2031_ms"] + FLAGS].round(4).to_dict("records"))
    if name == "get_pipe":
        res, _ = project.results(a["scenario"]); _, r = _row(res, a["label"]); return _clean(r.round(4).to_dict()) if hasattr(r, "round") else r
    if name == "explain_pipe":
        res, _ = project.results(a["scenario"]); _, r = _row(res, a["label"])
        checks = [dict(rule=RULES[0][0], source=RULES[0][1], value=round(float(r.d_over_D), 3), limit=float(r.limit), ok=not bool(r.over_limit)),
                  dict(rule=RULES[2][0], source=RULES[2][1], value=round(float(r.v_ms), 3), limit=3.0, ok=not bool(r.over_3ms))]
        if r.dn_mm > 200:
            checks.append(dict(rule=RULES[1][0], source=RULES[1][1], value=round(float(r.v2031_ms), 3), limit=0.75, ok=not bool(r.under075)))
        checks.append(dict(rule="depth below ground, upstream / downstream", source=RULES[5][1],
                           value=[float(r.depth_up_m), float(r.depth_dn_m)], limit=12.0, ok=max(r.depth_up_m, r.depth_dn_m) <= 12.0))
        return dict(pipe=a["label"], dn_mm=int(r.dn_mm), gradient_pc=round(float(r.s_pc), 3), q_ls=round(float(r.q_ls), 2),
                    needs_relay=bool(r.needs_relay), checks=checks)
    if name == "make_whatif":
        w = project.copy(a["scenario"], a["name"]); res, _ = project.results(w.id); touched = []
        for e in a["edits"]:
            i, _ = _row(res, e["label"]); touched.append(e["label"])
            project.edit(w.id, "pipe", [i], e["field"], e["value"])
        res, summ = project.results(w.id)
        return dict(scenario=w.id, summary=summ, edited=res[res.label.isin(touched)][
            ["label", "dn_mm", "s_pc", "q_ls", "v_ms", "d_over_D", "v2031_ms"] + FLAGS].round(4).to_dict("records"))
    if name == "compare_scenarios":
        return project.compare(a["a"], a["b"])
    if name == "run_tool":
        out = menu.run(a["name"], project, project.scenario(a["scenario"]))
        if "rows" in out: out = dict(out, rows=out["rows"][:200])
        return out
    if name == "lookup_criterion":
        if not os.path.exists(CRITERIA): return dict(error="criteria register not found")
        q = a["query"].lower()
        hits = [l.strip() for l in open(CRITERIA, encoding="utf-8") if q in l.lower()]
        return dict(query=a["query"], hits=hits[:30])
    raise ValueError(f"unknown tool {name}")
