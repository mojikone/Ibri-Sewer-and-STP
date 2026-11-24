"""Steady sanitary solve of a general project: flows (the W18 rule) and gravity hydraulics on every conduit.

Flow in a conduit = PF(cumulative unit load, L/s) x cumulative unit load + cumulative infiltration (see `infiltration`) +
transfers and inflows arriving upstream (not re-peaked). A pump, or a conduit marked `transfer`, passes downstream the
SUM of the peaked flows arriving at its upstream node plus that node's own inflow and own load (peaked alone), as an
unpeaked transfer: the rule SewerGEMS applies to an outfall flow (checked 2026-11-22: within 0.0007 % of its outfall
flows for all 24 Ibri subnetworks in 2031-2061, where peaking the summed load once is up to 24 % off).
Hydraulics: normal depth, Colebrook-White (ks) or Manning (n), slope from the inverts."""
import time
import numpy as np, pandas as pd
from sewerapp.engine.hydraulics import section, v_colebrook


POPULATION_METHODS = ("harmon", "ten_states", "babbitt")
STORM_ONLY = ("orifice", "weir")


def _without_storm_only(project):
    q = project.copy(); q.links = q.links[~q.links.kind.isin(STORM_ONLY)]; return q


def engine_view(project):
    """The network the engines solve (v7, model/kinds.py): a catch basin, transition, cross section or property connection
    is a gravity structure (a manhole); a headwall is its network's outfall when nothing leaves it, else a structure; an
    air valve is a pressure junction; a channel or a lateral is a conduit; a gutter (surface flow between catch basins)
    is left out; a link ending on a tap joins the tapped conduit's upstream structure, and the tap is left out. A project
    that has none of these is returned as it is (no copy)."""
    import copy as _copy
    from sewerapp.model import kinds as K
    N, L = project.nodes, project.links
    nk = N.kind if len(N) else pd.Series([], dtype=object); lk = L.kind if len(L) else pd.Series([], dtype=object)
    special_n = nk.isin(K.GRAVITY_AS_MANHOLE + K.PRESSURE_AS_JUNCTION + ("headwall", "tap"))
    special_l = lk.isin(K.LINKS_AS_CONDUIT + K.SURFACE_LINKS)
    if not special_n.any() and not special_l.any(): return project
    q = _copy.copy(project); N = N.copy(); L = L[~lk.isin(K.SURFACE_LINKS)].copy()
    taps = {i: ((getattr(project, "props", None) or {}).get("nodes", {}).get(i) or {}).get("link") for i in N.index[N.kind == "tap"]}
    for t, host in taps.items():
        m = L.to_node == t
        if m.any() and host in L.index:
            up = L.from_node[host]; L.loc[m, "to_node"] = up
            if up in N.index and N.invert[up] == N.invert[up]: L.loc[m, "dn_inv"] = L.loc[m, "dn_inv"].astype(float).clip(lower=float(N.invert[up]))
    N = N[N.kind != "tap"]
    leaves = set(L.from_node)
    hw = N.index[N.kind == "headwall"]
    N.loc[[i for i in hw if i in leaves], "kind"] = "manhole"; N.loc[[i for i in hw if i not in leaves], "kind"] = "outfall"
    N.loc[N.kind.isin(K.GRAVITY_AS_MANHOLE), "kind"] = "manhole"; N.loc[N.kind.isin(K.PRESSURE_AS_JUNCTION), "kind"] = "pressure_junction"
    L.loc[L.kind.isin(K.LINKS_AS_CONDUIT), "kind"] = "conduit"
    L = L[L.from_node.isin(N.index) & L.to_node.isin(N.index)]
    q.nodes, q.links = N, L
    return q


def peaking_factor(settings, q_ls, pop=None):
    f = _peaking_factor(settings, q_ls, pop); c = (settings.get("peaking") or {}).get("cutoff")
    return np.minimum(f, float(c)) if c else f


def _peaking_factor(settings, q_ls, pop=None):
    """The peaking (extreme flow) factor of an average unit load q (L/s) carrying a population pop (people). Flow-based:
    the project's table, Peltier, Merrimack (G201 p71-72), Federov (2.69 / Q^0.121, Q in L/s), a constant. Population-
    based (P in thousands): Harmon 1 + 14 / (4 + sqrt P), Ten States (18 + sqrt P) / (4 + sqrt P) (the same function),
    Babbitt 5 / P^0.2; with no population they give 1. An optional cutoff caps the factor (SewerGEMS's Cutoff Value)."""
    p = settings["peaking"]; q = np.asarray(q_ls, float)
    m = p.get("method", "table")
    if m in POPULATION_METHODS:
        P = np.asarray(0.0 if pop is None else pop, float) / 1000.0
        with np.errstate(divide="ignore", invalid="ignore"):
            f = {"harmon": lambda: 1 + 14 / (4 + np.sqrt(P)), "ten_states": lambda: (18 + np.sqrt(P)) / (4 + np.sqrt(P)),
                 "babbitt": lambda: 5 / P ** 0.2}[m]()
        f = np.where(P > 0, f, 1.0)
        return np.minimum(f, float(p["cutoff"])) if p.get("cutoff") else f
    if m == "federov":
        f = np.where(q > 0, 2.69 / np.maximum(q, 1e-12) ** 0.121, 1.0)
        return np.minimum(f, float(p["cutoff"])) if p.get("cutoff") else f
    if m == "table":
        t = sorted(p["table"]); return np.interp(q, [r[0] for r in t], [r[1] for r in t])
    if m == "peltier":   # G201 p72
        return np.where(q > 0, 1.5 + 1.0 / np.sqrt(np.maximum(q, 1e-12)), 1.0)
    if m == "merrimack":  # G201 p71: Qpdf = 2.65 Qadf^0.879 in Ml/d
        return np.where(q > 0, 2.65 * np.maximum(q * 0.0864, 1e-12) ** -0.121, 1.0)
    if m == "constant": return np.full(q.shape, float(p.get("constant", 1.0)))
    return np.ones(q.shape)


INFIL_METHODS = ("length", "length_diameter", "surface_area", "count")


def infiltration(project):
    """Each conduit's own infiltration, m3/d (SewerGEMS's conduit infiltration): by length at the project's
    infiltration_m3d_per_km (the default, G201 p72), or by length x inside diameter, inside surface or per conduit at
    settings.infiltration.rate; a conduit's own rate (project.infil) replaces the project's. Pumps take none."""
    L = project.links; s = project.settings; meth = (s.get("infiltration") or {}).get("method", "length")
    if meth not in INFIL_METHODS: raise ValueError(f"infiltration method must be one of {INFIL_METHODS}")
    rate0 = float(s["infiltration_m3d_per_km"]) if meth == "length" else float((s.get("infiltration") or {}).get("rate") or 0.0)
    own = getattr(project, "infil", None) or {}
    r = np.array([float(own[i]) if i in own and own[i] is not None else rate0 for i in L.index]) if own else np.full(len(L), rate0)
    length = L.length_m.fillna(0).astype(float).to_numpy()
    if meth == "length": q = length / 1000.0 * r
    else:
        D = L.inside_mm.astype(float).to_numpy() / 1000.0
        secs = getattr(project, "sections", None) or {}
        if secs:                                                       # a box or channel: its rise stands for the bore
            D = np.where(np.isfinite(D), D, [float(secs[i].get("rise_m", 0)) if i in secs else np.nan for i in L.index])
        D = np.nan_to_num(D)
        q = {"length_diameter": length / 1000.0 * D * r, "surface_area": np.pi * D * length * r, "count": r}[meth]
    return np.where((L.kind == "conduit").to_numpy(), q, 0.0)


def order(links):
    """Links in topological order (every link after all links arriving at its upstream node)."""
    fr, to = links.from_node.to_numpy(), links.to_node.to_numpy(); ids = links.index.to_numpy()
    arriving = pd.Series(to).value_counts().to_dict(); leaving = {u: i for i, u in enumerate(fr)}
    ready = [i for i, u in enumerate(fr) if u not in arriving]; left = dict(arriving); out = []
    while ready:
        i = ready.pop(); out.append(i); n = to[i]
        if n in left:
            left[n] -= 1
            if left[n] == 0 and n in leaving: ready.append(leaving[n])
    if len(out) != len(fr): raise ValueError(f"the network has a loop or a node with two leaving links ({len(fr) - len(out)} links unordered)")
    return np.array(out, int)


def flows(project, load_set):
    """Design flow in every link, m3/d, for one load set. Orifices and weirs (pond outlets) belong to the storm run: the
    steady sanitary run leaves them out (they carry 0). Every element kind is solved through engine_view: a gutter carries
    0 here (its flow is the rational run's bypass)."""
    view = engine_view(project)
    if view is not project:
        q = pd.Series(0.0, index=project.links.index); f = flows(view, load_set); q[f.index] = f.values; return q
    L = project.links; s = project.settings
    if L.kind.isin(STORM_ONLY).any():
        q = pd.Series(0.0, index=L.index); keep = ~L.kind.isin(STORM_ONLY)
        q[keep] = flows(_without_storm_only(project), load_set); return q
    base = project.load_sets.get(load_set, {}); inflow = project.nodes.inflow_m3d.fillna(0).to_dict()
    for n_, q_ in (getattr(project, "inflow_sets", {}) or {}).get(load_set, {}).items(): inflow[n_] = inflow.get(n_, 0.0) + q_
    fixed = project.fixed_flows.get(load_set, {}); ids = L.index.to_numpy()
    # unit-load rows (unit, count) add to a node's load; their population (people, or a type's population equivalent)
    # feeds the population-based methods; a plain load counts pe_per_m3d people per m3/d when the project gives one
    units = {u["name"]: u for u in ((s.get("libraries") or {}).get("unit_loads") or [])}
    pe_plain = float((s.get("peaking") or {}).get("pe_per_m3d") or 0.0)
    base = dict(base); popn = {n_: v * pe_plain for n_, v in base.items()} if pe_plain else {}
    UR = getattr(project, "unit_rows", None) or {}
    for n_, rows in {**(UR.get("*") or {}), **(UR.get(load_set) or {})}.items():
        for name, count in rows:
            u = units.get(name)
            if not u: continue
            base[n_] = base.get(n_, 0.0) + float(count) * float(u["rate_m3d"])
            popn[n_] = popn.get(n_, 0.0) + float(count) * (1.0 if u.get("type") == "population" else float(u.get("pe") or 0.0))
    own_inf = infiltration(project)
    fr, to = L.from_node.to_numpy(), L.to_node.to_numpy()
    kind = L.kind.to_numpy(); transfer = L.transfer.fillna(False).astype(bool).to_numpy()
    length = L.length_m.fillna(0).astype(float).to_numpy()
    n = len(L); cb = np.zeros(n); cl = np.zeros(n); ct = np.zeros(n); q = np.zeros(n)
    # per node: unit load, length, transfers carried by arriving gravity links (acc_t), their peaked flows (acc_q), and
    # flows pumped or transferred straight into the node (acc_p, part of acc_t too)
    acc_b, acc_i, acc_t, acc_q, acc_p, acc_n = {}, {}, {}, {}, {}, {}
    pf = lambda x, pop=0.0: float(peaking_factor(s, np.array([x / 86.4]), np.array([pop]))[0])
    for i in order(L):
        u, d = fr[i], to[i]
        if kind[i] in ("pump", "pressure_pipe", "orifice", "weir") or transfer[i]:          # pumped and pressurised flow is carried, not re-peaked
            own = base.get(u, 0.0)          # a conduit's flow already holds the transfers above it: add only direct ones
            q[i] = acc_q.get(u, 0.0) + acc_p.get(u, 0.0) + inflow.get(u, 0.0) + own * pf(own, popn.get(u, 0.0))
            if ids[i] in fixed: q[i] = float(fixed[ids[i]])    # a pump held at a fixed flow for this load set
            acc_t[d] = acc_t.get(d, 0.0) + q[i]; acc_p[d] = acc_p.get(d, 0.0) + q[i]
            ct[i] = q[i]
        else:
            cb[i] = base.get(u, 0.0) + acc_b.get(u, 0.0)
            cn = popn.get(u, 0.0) + acc_n.get(u, 0.0)                   # the population carried down with the load
            ct[i] = acc_t.get(u, 0.0) + inflow.get(u, 0.0)
            cl[i] = own_inf[i] + acc_i.get(u, 0.0)                  # infiltration carried down, m3/d (not peaked)
            q[i] = cb[i] * pf(cb[i], cn) + cl[i] + ct[i]
            acc_b[d] = acc_b.get(d, 0.0) + cb[i]; acc_i[d] = acc_i.get(d, 0.0) + cl[i]; acc_t[d] = acc_t.get(d, 0.0) + ct[i]
            acc_n[d] = acc_n.get(d, 0.0) + cn
            acc_q[d] = acc_q.get(d, 0.0) + q[i]
    return pd.Series(q, index=L.index)


def _velocity_manning(R, S, n):
    return (1.0 / n) * R ** (2.0 / 3.0) * np.sqrt(S)


def normal_depth(project, Q, D, S, iters=50):
    """y/D and velocity at normal depth by bisection; friction from the project's settings."""
    f = project.settings["friction"]
    Q, D, S = np.broadcast_arrays(np.asarray(Q, float), np.asarray(D, float), np.asarray(S, float))
    vel = (lambda R, S_: v_colebrook(R, S_, f["ks_mm"] / 1000.0, f["nu"])) if f["method"] == "colebrook" \
        else (lambda R, S_: _velocity_manning(R, S_, f["manning_n"]))
    lo, hi = 1e-6 * D, 0.999 * D
    with np.errstate(invalid="ignore", divide="ignore"):
        for _ in range(iters):
            y = (lo + hi) / 2; A, R = section(D, y)
            over = A * vel(R, S) > Q
            hi = np.where(over, y, hi); lo = np.where(over, lo, y)
        y = (lo + hi) / 2; A, R = section(D, y)
        Af, Rf = section(D, 0.999999 * D); full = Af * vel(Rf, S) < Q
    pos = (Q > 0) & (S > 0) & np.isfinite(D) & (D > 0)
    return np.where(pos, np.where(full, 1.0, y / D), 0.0), np.where(pos, Q / np.where(pos, A, 1.0), 0.0), pos & full


def solve(project, load_set=None, check_set=None):
    """Flows and hydraulics; returns a DataFrame indexed by link id and a summary."""
    project = engine_view(project)                                        # every element kind as the engine's own (v7)
    if project.links.kind.isin(STORM_ONLY).any(): project = _without_storm_only(project)     # pond outlets: storm run only
    ps = project.settings.get("pressure") or {}
    if ps.get("use_pumped_flows") and (project.links.kind == "pump").any() and not getattr(project, "_pumped_pass", False):
        # SewerGEMS's "use pumped flows": downstream of a pump the flow is what the pump delivers on its curve, not its inflow
        first = project.copy(); first._pumped_pass = True
        res0, _ = solve(first, load_set, check_set)
        q2 = project.copy(); q2._pumped_pass = True; ls = load_set or project.settings["design_load"]
        ff = dict(q2.fixed_flows.get(ls, {}))
        if "op_q_ls" in res0.columns:
            for pid, v in res0.op_q_ls.dropna().items():
                if pid not in ff: ff[pid] = float(v) * 86.4                  # a flow the engineer fixed on a pump stays
        q2.fixed_flows = dict(q2.fixed_flows); q2.fixed_flows[ls] = ff
        res, summ = solve(q2, load_set, check_set); summ["pumped_flows"] = True
        # whether each pump copes is judged on its inflow (the first pass), not on the flow it is then given
        for c in ("short", "cannot_lift", "pump_head_m", "tdh_m", "off_curve"):
            if c in res0.columns:
                pumps = res0.index[(project.links.kind == "pump").reindex(res0.index).fillna(False).to_numpy()]
                res.loc[pumps, c + ("_at_inflow" if c in ("pump_head_m", "tdh_m") else "")] = res0.loc[pumps, c]
        if "short" in res0.columns and "pressure" in summ: summ["pressure"]["pumps_short"] = int(res0.short.fillna(False).astype(bool).sum())
        return res, summ
    t0 = time.perf_counter(); s = project.settings; L = project.links
    load_set = load_set or s["design_load"]; check_set = check_set if check_set is not None else s.get("check_load")
    q = flows(project, load_set)
    D = L.inside_mm.astype(float).to_numpy() / 1000.0
    secs = getattr(project, "sections", None) or {}
    isec = L.index.isin(list(secs))                                        # a box or channel with its section given: solved below
    noD = (L.kind == "conduit").to_numpy() & ~(np.nan_to_num(D) > 0) & ~isec   # no bore and no section: not analysed
    cond = (L.kind == "conduit").to_numpy() & ~noD
    S = ((L.up_inv.astype(float) - L.dn_inv.astype(float)) / L.length_m.astype(float)).to_numpy()
    ratio, v, full = normal_depth(project, q.to_numpy() / 86400.0, D, S)
    dn = L.dn_mm.astype(float).to_numpy(); lim = project.dd_limit(dn)
    d = s["design"]
    res = pd.DataFrame(dict(kind=L.kind, dn_mm=L.dn_mm, length_m=L.length_m, s_pc=S * 100, q_ls=q / 86.4, v_ms=v,
                            d_over_D=ratio, limit=lim, surcharged=full), index=L.index)
    res["over_limit"] = cond & (ratio >= lim + 0.005)
    res["over_vmax"] = cond & (v > d["v_max"])
    res["negative_slope"] = cond & (S <= 0)
    if check_set:
        qc = flows(project, check_set); rc, vc, _ = normal_depth(project, qc.to_numpy() / 86400.0, D, S)
        res["q_check_ls"] = qc / 86.4; res["v_check_ms"] = vc
        res["under_vmin"] = cond & (dn > s.get("self_cleansing_min_dn", 0)) & (np.round(vc, 2) < d["v_min"])
    res.loc[~cond, ["v_ms", "d_over_D", "s_pc", "limit"]] = np.nan
    res["surcharged"] = res.surcharged & cond
    if isec.any():                                                         # boxes and channels: Manning with their own n
        from sewerapp.engine import sections as X
        sel = L.index[isec & (L.kind == "conduit").to_numpy()]
        code, rise, bottom, zl, zr, n = X.unpack([secs[i] for i in sel]); nb = X.barrels([secs[i] for i in sel])
        Ssec = pd.Series(S, index=L.index)[sel].to_numpy(); qs = (q[sel] / 86400.0).to_numpy() / nb   # per barrel
        with np.errstate(invalid="ignore", divide="ignore"):
            y, A, full = X.normal_depth(qs, Ssec, code, rise, bottom, zl, zr, n)
            yc = X.critical_depth(qs, code, rise, bottom, zl, zr)
            cap = X.full_capacity(code, rise, bottom, zl, zr, n, Ssec)
        res.loc[sel, "v_ms"] = np.where(A > 0, qs / np.where(A > 0, A, 1), 0.0)
        res.loc[sel, "d_over_D"] = y / rise; res.loc[sel, "limit"] = np.nan; res.loc[sel, "s_pc"] = Ssec * 100
        res.loc[sel, "depth_m"] = y; res.loc[sel, "yc_m"] = yc; res.loc[sel, "q_full_ls"] = cap * nb * 1000.0
        res.loc[sel, "surcharged"] = full | ((code > 0) & (np.nan_to_num(y) > rise))   # a box full, an open channel over its bank
        res.loc[sel, "over_limit"] = False; res.loc[sel, "over_vmax"] = False      # the sewer's d/D and v max are not a channel's
        res.loc[sel, "negative_slope"] = Ssec <= 0
        if "under_vmin" in res: res.loc[sel, "under_vmin"] = False
        cond = cond | isec & (L.kind == "conduit").to_numpy()
    if (L.kind != "conduit").any():                                       # pump stations and force mains (engine/pressure.py)
        from sewerapp.engine import pressure
        # the water depth in each structure: its leaving conduit's flow depth (vectorised: 19,000 pipes in milliseconds)
        cm = (L.kind == "conduit").to_numpy()
        y = res.d_over_D.to_numpy(float) * L.inside_mm.astype(float).to_numpy() / 1000.0
        if "depth_m" in res.columns: y = np.where(np.isfinite(res.depth_m.to_numpy(float)), res.depth_m.to_numpy(float), y)
        ok = cm & np.isfinite(y)
        dep = dict(zip(L.from_node.to_numpy()[ok], y[ok]))
        prow, psum = pressure.solve(project, q.to_dict(), dep)
        for lid, r in prow.items():
            for k, v in r.items():
                if k in ("main", "discharges_to", "kind"): continue
                if k not in res.columns: res[k] = np.nan if not isinstance(v, bool) else False
                res.at[lid, k] = v
    else: psum = None
    gsum = None
    if s.get("flow_profile") == "gvf":                                    # the gradually varied water profile (engine/gvf.py)
        from sewerapp.engine import gvf
        res, nh, gsum, flood = gvf.solve(project, res, q.to_dict())
        res.attrs["node_hgl"] = {k: float(v) for k, v in nh.items()}; res.attrs["flooding"] = flood
    summ = dict(links=int(len(L)), conduits=int(cond.sum()), not_analysed=int(noD.sum()), km=round(float(L.length_m[cond | noD].sum()) / 1000, 3),
                over_limit=int(res.over_limit.sum()), over_vmax=int(res.over_vmax.sum()),
                surcharged=int((res.surcharged & cond).sum()), negative_slope=int(res.negative_slope.sum()),
                km_under_vmin=round(float(L.length_m[res.get("under_vmin", pd.Series(False, index=L.index))].sum()) / 1000, 3)
                if check_set else None, load_set=load_set, check_set=check_set, seconds=round(time.perf_counter() - t0, 3))
    if psum: summ["pressure"] = psum
    if gsum: summ["gvf"] = gsum
    return res, summ
