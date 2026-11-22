"""Steady sanitary solve of a general project: flows (the W18 rule) and gravity hydraulics on every conduit.

Flow in a conduit = PF(cumulative unit load, L/s) x cumulative unit load + infiltration x cumulative conduit length +
transfers and inflows arriving upstream (not re-peaked). A pump, or a conduit marked `transfer`, passes downstream the
SUM of the peaked flows arriving at its upstream node plus that node's own inflow and own load (peaked alone), as an
unpeaked transfer: the rule SewerGEMS applies to an outfall flow (checked 2026-11-22: within 0.0007 % of its outfall
flows for all 24 Ibri subnetworks in 2031-2061, where peaking the summed load once is up to 24 % off).
Hydraulics: normal depth, Colebrook-White (ks) or Manning (n), slope from the inverts."""
import time
import numpy as np, pandas as pd
from sewerapp.engine.hydraulics import section, v_colebrook


def peaking_factor(settings, q_ls):
    p = settings["peaking"]; q = np.asarray(q_ls, float)
    m = p.get("method", "table")
    if m == "table":
        t = sorted(p["table"]); return np.interp(q, [r[0] for r in t], [r[1] for r in t])
    if m == "peltier":   # G201 p72
        return np.where(q > 0, 1.5 + 1.0 / np.sqrt(np.maximum(q, 1e-12)), 1.0)
    if m == "merrimack":  # G201 p71: Qpdf = 2.65 Qadf^0.879 in Ml/d
        return np.where(q > 0, 2.65 * np.maximum(q * 0.0864, 1e-12) ** -0.121, 1.0)
    if m == "constant": return np.full(q.shape, float(p.get("constant", 1.0)))
    return np.ones(q.shape)


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
    """Design flow in every link, m3/d, for one load set."""
    L = project.links; s = project.settings
    base = project.load_sets.get(load_set, {}); inflow = project.nodes.inflow_m3d.fillna(0).to_dict()
    for n_, q_ in (getattr(project, "inflow_sets", {}) or {}).get(load_set, {}).items(): inflow[n_] = inflow.get(n_, 0.0) + q_
    fixed = project.fixed_flows.get(load_set, {}); ids = L.index.to_numpy()
    inf = float(s["infiltration_m3d_per_km"])
    fr, to = L.from_node.to_numpy(), L.to_node.to_numpy()
    kind = L.kind.to_numpy(); transfer = L.transfer.fillna(False).astype(bool).to_numpy()
    length = L.length_m.fillna(0).astype(float).to_numpy()
    n = len(L); cb = np.zeros(n); cl = np.zeros(n); ct = np.zeros(n); q = np.zeros(n)
    # per node: unit load, length, transfers carried by arriving gravity links (acc_t), their peaked flows (acc_q), and
    # flows pumped or transferred straight into the node (acc_p, part of acc_t too)
    acc_b, acc_l, acc_t, acc_q, acc_p = {}, {}, {}, {}, {}
    pf = lambda x: float(peaking_factor(s, np.array([x / 86.4]))[0])
    for i in order(L):
        u, d = fr[i], to[i]
        if kind[i] == "pump" or transfer[i]:
            own = base.get(u, 0.0)          # a conduit's flow already holds the transfers above it: add only direct ones
            q[i] = acc_q.get(u, 0.0) + acc_p.get(u, 0.0) + inflow.get(u, 0.0) + own * pf(own)
            if ids[i] in fixed: q[i] = float(fixed[ids[i]])    # a pump held at a fixed flow for this load set
            acc_t[d] = acc_t.get(d, 0.0) + q[i]; acc_p[d] = acc_p.get(d, 0.0) + q[i]
            ct[i] = q[i]
        else:
            cb[i] = base.get(u, 0.0) + acc_b.get(u, 0.0)
            cl[i] = length[i] + acc_l.get(u, 0.0)
            ct[i] = acc_t.get(u, 0.0) + inflow.get(u, 0.0)
            q[i] = cb[i] * pf(cb[i]) + cl[i] / 1000.0 * inf + ct[i]
            acc_b[d] = acc_b.get(d, 0.0) + cb[i]; acc_l[d] = acc_l.get(d, 0.0) + cl[i]; acc_t[d] = acc_t.get(d, 0.0) + ct[i]
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
    res.loc[~cond, ["v_ms", "d_over_D", "s_pc"]] = np.nan
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
    summ = dict(links=int(len(L)), conduits=int(cond.sum()), not_analysed=int(noD.sum()), km=round(float(L.length_m[cond | noD].sum()) / 1000, 3),
                over_limit=int(res.over_limit.sum()), over_vmax=int(res.over_vmax.sum()),
                surcharged=int((res.surcharged & cond).sum()), negative_slope=int(res.negative_slope.sum()),
                km_under_vmin=round(float(L.length_m[res.get("under_vmin", pd.Series(False, index=L.index))].sum()) / 1000, 3)
                if check_set else None, load_set=load_set, check_set=check_set, seconds=round(time.perf_counter() - t0, 3))
    return res, summ
