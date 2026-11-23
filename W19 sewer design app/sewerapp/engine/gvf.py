"""Gradually varied flow in a gravity network (2026-11-23, v3), the steady water profile SewerGEMS's GVF solvers give.

From every outfall upstream, each conduit carries its steady flow under the water level at its downstream end:

- the level at an outfall is its fixed tailwater, or none (a free outfall: the pipe's critical depth controls);
- in a mild pipe (normal depth above critical) the downstream depth is at least critical; above normal depth the
  profile is a backwater (M1), below it a drawdown (M2); both are integrated upstream by the direct step method in
  depth (24 steps between the downstream depth and normal depth) until the pipe's length is used or normal depth is
  reached;
- in a steep pipe (normal depth below critical) the flow is supercritical and the entrance controls: critical depth at
  the upstream end, unless the downstream level drowns it (then that level, horizontal);
- a pipe whose downstream level is at or over its crown runs full: the grade rises by the full-pipe friction slope; if
  it stays over the crown at the upstream end the pipe is surcharged throughout;
- flat or adverse pipes take the downstream level plus the friction over their length less their fall;
- at a structure the water level is the level at the upstream end of the pipe leaving it plus a structure loss
  K v^2 / 2g on that pipe's velocity (settings.structure_loss.K, 0 by default: no loss unless the engineer sets one).

Friction is the project's (Colebrook-White with ks, or Manning n). Boxes and channels, pumps, force mains and pond
outlets keep their own results; the structures at their ends take the level the network gives them.
The work is vectorised by level (all pipes the same number of pipes from an outfall together)."""
import numpy as np, pandas as pd
from sewerapp.engine.hydraulics import section, v_colebrook

G = 9.81
STEPS = 24


def _top(D, y):
    return 2.0 * np.sqrt(np.clip(y * (D - y), 0.0, None))


def critical_depth(Q, D, iters=40):
    """Critical depth in a circular pipe: Q^2 T / (g A^3) = 1, by bisection (capped at 0.999 D)."""
    Q, D = np.broadcast_arrays(np.asarray(Q, float), np.asarray(D, float))
    lo, hi = 1e-6 * D, 0.999 * D
    with np.errstate(invalid="ignore", divide="ignore"):
        for _ in range(iters):
            y = (lo + hi) / 2; A, _ = section(D, y); F = Q * Q * _top(D, y) / (G * A ** 3)
            sub = F < 1.0                                                   # subcritical at y: critical depth below
            hi = np.where(sub, y, hi); lo = np.where(sub, lo, y)
    return np.where(Q > 0, (lo + hi) / 2, 0.0)


def friction_slope(Q, D, y, fr):
    """The friction slope carrying Q at depth y (full when y >= D)."""
    y = np.minimum(y, D * 0.999999)
    A, R = section(D, y)
    if fr["method"] == "manning":
        return (fr["manning_n"] * Q / (A * R ** (2.0 / 3.0))) ** 2
    ks, nu = fr["ks_mm"] / 1000.0, fr["nu"]
    S = (0.012 * Q / (A * R ** (2.0 / 3.0))) ** 2 + 1e-12               # Manning-like start, then fixed point on CW
    with np.errstate(invalid="ignore", divide="ignore"):
        for _ in range(6):
            v = v_colebrook(R, S, ks, nu); S = S * (Q / (A * np.where(v > 0, v, 1e-9))) ** 2
    return S


def solve(project, res, q_m3d):
    """Water levels at both ends of every circular conduit and at every structure; adds hgl_up, hgl_dn, y_up_m,
    y_dn_m, regime and surcharged_gvf to res and returns (res, node levels, summary)."""
    L, N = project.links, project.nodes; fr = project.settings["friction"]
    K = float((project.settings.get("structure_loss") or {}).get("K") or 0.0)
    tail = getattr(project, "tailwater", None) or {}
    secs = getattr(project, "sections", None) or {}
    cond = (L.kind == "conduit").to_numpy() & ~L.index.isin(list(secs)) & np.isfinite(L.inside_mm.astype(float).to_numpy())
    ids = L.index.to_numpy(); fr_, to_ = L.from_node.to_numpy(), L.to_node.to_numpy()
    out_of = {}
    for i in range(len(L)):
        if L.kind.iat[i] not in ("orifice", "weir"): out_of.setdefault(fr_[i], i)
    # level of each link: 0 for a link into a node with nothing leaving it, else one more than the link leaving its end
    rank = np.full(len(L), -1)
    for i in range(len(L)):
        k, path = i, []
        while True:
            if rank[k] >= 0: base = rank[k]; break
            j = out_of.get(to_[k])
            if j is None or j == k: rank[k] = 0; base = 0; break
            path.append(k); k = j
            if len(path) > len(L): raise ValueError("a loop in the network")
        for m in reversed(path): base += 1; rank[m] = base
    Q = np.array([float(q_m3d.get(i, 0.0)) / 86400.0 for i in ids])
    D = L.inside_mm.astype(float).to_numpy() / 1000.0
    up, dn, ln = L.up_inv.astype(float).to_numpy(), L.dn_inv.astype(float).to_numpy(), L.length_m.astype(float).to_numpy()
    S0 = np.where(ln > 0, (up - dn) / np.where(ln > 0, ln, 1), 0.0)
    yn = np.where(cond, res.d_over_D.reindex(ids).to_numpy(float) * D, np.nan)
    full_n = res.surcharged.reindex(ids).fillna(False).to_numpy(bool) if "surcharged" in res.columns else np.zeros(len(L), bool)
    node_h = {n: float(tail[n]) for n in tail}                              # outfalls held at a level
    if "suction_m" in res.columns:                                          # a wet well stands at its pump's lift level
        for lid, sv in res.suction_m.dropna().items(): node_h[L.from_node[lid]] = max(node_h.get(L.from_node[lid], -np.inf), float(sv))
    if "depth_m" in res.columns:                                            # a box or channel upstream end: its own level
        for lid in L.index[L.index.isin(list(secs))]:
            dm = res.depth_m.get(lid)
            if dm == dm and dm is not None: node_h[L.from_node[lid]] = max(node_h.get(L.from_node[lid], -np.inf), float(L.up_inv[lid]) + float(dm))
    h_up, h_dn, y_up, y_dn = (np.full(len(L), np.nan) for _ in range(4)); regime = np.array([""] * len(L), dtype=object)

    def step(q, d, s0, l, y0, target):
        """Direct step upstream from depth y0 towards `target`: the depth at the pipe's upstream end, and the length the
        steps covered (less than l when the target is reached inside the pipe). dE/dx = S0 - Sf, x pointing downstream,
        so a step upstream of length dx changes E by -(S0 - Sf) dx."""
        ys = y0[:, None] + (target - y0)[:, None] * np.linspace(0.0, 1.0, STEPS + 1)[None, :]
        A, _ = section(d[:, None], ys); E = ys + (q[:, None] / A) ** 2 / (2 * G)
        Sf = friction_slope(np.repeat(q[:, None], STEPS + 1, 1), np.repeat(d[:, None], STEPS + 1, 1), ys, fr)
        dx = (E[:, :-1] - E[:, 1:]) / (s0[:, None] - (Sf[:, 1:] + Sf[:, :-1]) / 2)
        dx = np.where(np.isfinite(dx) & (dx > 0), dx, 0.0); x = np.concatenate([np.zeros((len(q), 1)), np.cumsum(dx, 1)], 1)
        yu = np.array([np.interp(l[k], x[k], ys[k]) if x[k, -1] > l[k] else target[k] for k in range(len(q))])
        return yu, x[:, -1]

    with np.errstate(invalid="ignore", divide="ignore"):
        for lv in range(int(rank.max()) + 1 if len(L) else 0):
            sel = np.where((rank == lv) & cond & (Q > 0) & (D > 0))[0]
            if not len(sel): continue
            q, d, s0, l = Q[sel], D[sel], S0[sel], ln[sel]
            yc = np.minimum(critical_depth(q, d), 0.999 * d)
            over = full_n[sel]                                                 # the slope cannot carry the flow part-full
            ynn = np.where(np.isfinite(yn[sel]) & (yn[sel] > 0) & ~over, yn[sel], d)
            hd = np.array([node_h.get(to_[k], -np.inf) for k in sel])        # the level at the downstream end
            yd = np.maximum(hd - dn[sel], 0.0)
            mild = (s0 > 0) & (ynn > yc) & ~over
            steep = (s0 > 0) & (ynn <= yc) & ~over
            fa = (s0 <= 0) & ~over
            ydm = np.select([mild, steep, fa], [np.maximum(yd, yc), np.maximum(yd, ynn), np.maximum(yd, yc)], np.maximum(yd, d))
            yu = np.full(len(sel), np.nan); reg = np.array([""] * len(sel), dtype=object)
            # full at the downstream end (or an overloaded pipe): the grade rises by the full-pipe friction slope; where it
            # falls below the crown upstream the pipe runs part-full there (normal depth, or critical on a steep pipe)
            fullm = (ydm >= 0.999 * d) | over
            if fullm.any():
                sf = friction_slope(q[fullm], d[fullm], d[fullm], fr)
                hu = dn[sel][fullm] + ydm[fullm] + sf * l[fullm]
                floor = np.where(mild[fullm], np.minimum(ynn[fullm], 0.999 * d[fullm]), yc[fullm])
                yu[fullm] = np.maximum(hu - up[sel][fullm], floor)
                reg[fullm] = np.where(yu[fullm] >= 0.999 * d[fullm], "full", "part full upstream")
            # mild, part full: direct step towards normal depth (M1 above it, M2 below it)
            mm = mild & ~fullm
            if mm.any():
                y0, yN = ydm[mm], np.minimum(ynn[mm], 0.999 * d[mm])
                target = np.where(y0 > yN, yN * 1.0005, yN * 0.9995)
                yu[mm], _ = step(q[mm], d[mm], s0[mm], l[mm], y0, target)
                reg[mm] = np.where(y0 > yN * 1.0005, "M1 backwater", np.where(y0 < yN * 0.9995, "M2 drawdown", "normal"))
            # steep: the entrance controls (critical depth) unless the downstream level drowns the upstream end
            st = steep & ~fullm
            if st.any():
                drown = (dn[sel][st] + yd[st]) > (up[sel][st] + yc[st])
                yu[st] = np.where(drown, dn[sel][st] + yd[st] - up[sel][st], yc[st]); reg[st] = np.where(drown, "S1 drowned", "supercritical")
            # flat or adverse: the depth rises upstream (H2/A2) by the step; full over the rest when it reaches the crown
            fm = fa & ~fullm
            if fm.any():
                y0 = ydm[fm]; tgt = 0.999 * d[fm]
                yy, xe = step(q[fm], d[fm], s0[fm], l[fm], y0, tgt)
                sfull = friction_slope(q[fm], d[fm], d[fm], fr)
                yu[fm] = np.where(xe >= l[fm], yy, d[fm] + (sfull - s0[fm]) * (l[fm] - xe)); reg[fm] = "adverse or flat"
            h_up[sel] = up[sel] + yu; h_dn[sel] = dn[sel] + ydm; y_up[sel] = yu; y_dn[sel] = ydm; regime[sel] = reg
            # the structure at each pipe's upstream end: its level plus the structure loss on the pipe's velocity
            A, _ = section(d, np.minimum(np.maximum(yu, 0.02 * d), 0.999 * d)); v = q / A
            for k, hk, vk in zip(sel, h_up[sel], v):
                node_h[fr_[k]] = max(node_h.get(fr_[k], -np.inf), hk + K * vk * vk / (2 * G))
    res = res.copy()
    for col, val in (("hgl_up", h_up), ("hgl_dn", h_dn), ("y_up_m", y_up), ("y_dn_m", y_dn)):      # force mains keep theirs
        old = res[col].to_numpy(float) if col in res.columns else np.full(len(L), np.nan)
        res[col] = np.where(np.isfinite(val), val, old)
    res["regime"] = regime
    crown_up = up + D
    res["surcharged_gvf"] = cond & np.isfinite(h_up) & (h_up > crown_up + 1e-6)
    gnd = N.ground.astype(float)
    nh = pd.Series({n: h for n, h in node_h.items() if np.isfinite(h)}, dtype=float)
    flood = [n for n, h in nh.items() if n in gnd.index and h > gnd[n] + 1e-6 and N.kind[n] != "outfall"]
    summ = dict(profile="gvf", surcharged=int(res.surcharged_gvf.sum()), flooding_nodes=len(flood), structure_loss_K=K,
                backwater=int((regime == "M1 backwater").sum()), full=int((regime == "full").sum()))
    return res, nh, summ, flood
