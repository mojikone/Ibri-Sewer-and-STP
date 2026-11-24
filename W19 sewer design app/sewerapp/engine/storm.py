"""Stormwater and dynamic runs of a general project on EPA SWMM 5 (engine/swmm.py): the project is written as a SWMM
input file (io/swmm_inp.py), solved, and read back per element: peak flow, peak velocity, peak depth and fullness per
link; peak depth, head and flooding per node; peak runoff per catchment; the continuity errors of the report; and the
time series of any element on request."""
import os, re, shutil, tempfile
import numpy as np
from swmm.toolkit import output, shared_enum as E
from sewerapp.engine import swmm
from sewerapp.io import swmm_inp


def run(project, support_dir=None, rain=None):
    d = tempfile.mkdtemp(prefix="w19storm_")
    if support_dir:
        for f in os.listdir(support_dir):
            if os.path.isfile(os.path.join(support_dir, f)) and not f.endswith(".inp"): shutil.copy(os.path.join(support_dir, f), d)
    inp = os.path.join(d, "model.inp"); open(inp, "w", encoding="utf-8").write(swmm_inp.from_project(project, rain))
    r = swmm.run(inp, tempfile.mkdtemp(prefix="w19stormrun_"))
    res = dict(inp=inp, out=r["out"], rpt=r["rpt"], seconds=r["seconds"], **read(r["out"], r["rpt"]))
    res["inlets"] = inlets(open(inp, encoding="utf-8").read(), r["out"], r["rpt"])
    if res["inlets"]: res["summary"]["inlets"] = len(res["inlets"])
    return res


def inlets(inp_text, out_path, rpt_path):
    """Each catch basin's inlet in the storm run (v7): the approach flow in its street, what it captured (the lateral
    inflow SWMM gives its structure) and bypassed, at their peaks, with the street's spread and depth (SWMM's Street
    Flow Summary)."""
    from sewerapp.io import swmm_streets
    use = swmm_streets.usage(inp_text)
    if not use: return {}
    rep = swmm_streets.read_report(open(rpt_path, encoding="utf-8", errors="ignore").read()) if rpt_path and os.path.exists(rpt_path) else {}
    h = output.init(); output.open(h, out_path); res = {}
    try:
        nt = output.get_times(h, E.Time.NUM_PERIODS)
        ln = {output.get_elem_name(h, E.ElementType.LINK, j).strip(): j for j in range(output.get_proj_size(h)[2])}
        nn = {output.get_elem_name(h, E.ElementType.NODE, j).strip(): j for j in range(output.get_proj_size(h)[1])}
        for cb, (link, inlet) in use.items():
            if link not in ln or cb not in nn: continue
            q = np.abs(np.array(output.get_link_series(h, ln[link], E.LinkAttribute.FLOW_RATE, 0, nt - 1)))
            c = np.array(output.get_node_series(h, nn[cb], E.NodeAttribute.LATERAL_INFLOW, 0, nt - 1))
            by = np.clip(q - c, 0, None); k = int(np.argmax(q))
            r = dict(street=link, inlet=inlet, q_street_peak_ls=float(q.max()) * 1000, q_captured_peak_ls=float(c.max()) * 1000,
                     q_bypass_peak_ls=float(by.max()) * 1000, capture_at_peak_pc=float(c[k] / q[k] * 100) if q[k] > 0 else None)
            rr = rep.get(inlet)
            if rr: r.update(spread_m=rr["spread_m"], depth_m=rr["depth_m"], location=rr["location"], capture_avg_pc=rr["capture_avg_pc"])
            res[cb] = r
    finally:
        output.close(h)
    return res


def _peaks(h, kind, attrs):
    n = output.get_proj_size(h)[{"subcatch": 0, "node": 1, "link": 2}[kind]]
    nt = output.get_times(h, E.Time.NUM_PERIODS)
    get = {"link": output.get_link_series, "node": output.get_node_series, "subcatch": output.get_subcatch_series}[kind]
    et = {"subcatch": E.ElementType.SUBCATCH, "node": E.ElementType.NODE, "link": E.ElementType.LINK}[kind]
    out = {}
    for j in range(n):
        name = output.get_elem_name(h, et, j)
        out[name] = {k: float(np.max(np.abs(get(h, j, a, 0, nt - 1)))) for k, a in attrs.items()}
    return out


def read(out_path, rpt_path=None):
    h = output.init(); output.open(h, out_path)
    try:
        links = _peaks(h, "link", dict(q_peak=E.LinkAttribute.FLOW_RATE, v_peak=E.LinkAttribute.FLOW_VELOCITY,
                                       depth_peak=E.LinkAttribute.FLOW_DEPTH, capacity_peak=E.LinkAttribute.CAPACITY))
        nodes = _peaks(h, "node", dict(depth_peak=E.NodeAttribute.INVERT_DEPTH, head_peak=E.NodeAttribute.HYDRAULIC_HEAD,
                                       flooding_peak=E.NodeAttribute.FLOODING_LOSSES))
        subs = _peaks(h, "subcatch", dict(runoff_peak=E.SubcatchAttribute.RUNOFF_RATE, rain_peak=E.SubcatchAttribute.RAINFALL))
        periods = int(output.get_times(h, E.Time.NUM_PERIODS)); step = int(output.get_times(h, E.Time.REPORT_STEP))
    finally:
        output.close(h)
    cont = {}
    if rpt_path and os.path.exists(rpt_path):
        txt = open(rpt_path, encoding="utf-8", errors="ignore").read()
        for title in ("Runoff Quantity Continuity", "Flow Routing Continuity"):
            m = re.search(title + r".*?Continuity Error \(%\) \.+\s+(-?[\d.]+)", txt, re.S)
            if m: cont[title] = float(m.group(1))
    summary = dict(links=len(links), nodes=len(nodes), subcatchments=len(subs), periods=periods, report_step_s=step,
                   flooded_nodes=sum(1 for v in nodes.values() if v["flooding_peak"] > 0),
                   surcharged_links=sum(1 for v in links.values() if v["capacity_peak"] >= 0.999), continuity_error_pc=cont)
    return dict(summary=summary, links=links, nodes=nodes, subcatchments=subs)


def frame(out_path, period, attr="capacity"):
    """Every link's value of one attribute at one reporting period (0-based), and every node's flooding then."""
    la = {"capacity": E.LinkAttribute.CAPACITY, "flow_rate": E.LinkAttribute.FLOW_RATE, "flow_depth": E.LinkAttribute.FLOW_DEPTH,
          "flow_velocity": E.LinkAttribute.FLOW_VELOCITY}[attr]
    h = output.init(); output.open(h, out_path)
    try:
        nt = output.get_times(h, E.Time.NUM_PERIODS); step = output.get_times(h, E.Time.REPORT_STEP); k = max(0, min(int(period), nt - 1))
        nl, nn = output.get_proj_size(h)[2], output.get_proj_size(h)[1]
        lv = output.get_link_attribute(h, k, la); nv = output.get_node_attribute(h, k, E.NodeAttribute.FLOODING_LOSSES)
        links = {output.get_elem_name(h, E.ElementType.LINK, j): float(lv[j]) for j in range(nl)}
        nodes = {output.get_elem_name(h, E.ElementType.NODE, j): float(nv[j]) for j in range(nn) if nv[j] > 0}
        return dict(period=k, periods=int(nt), t_s=float((k + 1) * step), attr=attr, links=links, flooding=nodes)
    finally:
        output.close(h)


def series(out_path, kind, name, attr):
    """Time series (seconds from the start, value) of one element's attribute."""
    enum = {"link": E.LinkAttribute, "node": E.NodeAttribute, "subcatch": E.SubcatchAttribute}[kind]
    et = {"subcatch": E.ElementType.SUBCATCH, "node": E.ElementType.NODE, "link": E.ElementType.LINK}[kind]
    h = output.init(); output.open(h, out_path)
    try:
        n = output.get_proj_size(h)[{"subcatch": 0, "node": 1, "link": 2}[kind]]
        j = next(k for k in range(n) if output.get_elem_name(h, et, k) == name)
        nt = output.get_times(h, E.Time.NUM_PERIODS); step = output.get_times(h, E.Time.REPORT_STEP)
        get = {"link": output.get_link_series, "node": output.get_node_series, "subcatch": output.get_subcatch_series}[kind]
        v = get(h, j, getattr(enum, attr.upper()), 0, nt - 1)
        return [(float((k + 1) * step), float(x)) for k, x in enumerate(v)]
    finally:
        output.close(h)
