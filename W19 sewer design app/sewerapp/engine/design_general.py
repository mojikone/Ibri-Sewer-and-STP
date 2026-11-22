"""Automated design of any project, the way SewerGEMS's constraint-based design runs (rules proved on Ibri, W18):

1. Flows at the design load set (they do not depend on the sizes).
2. Sizes: each conduit takes the smallest catalogue size whose capacity at the d/D limit (G203 p27 Table 10) carries
   its flow at the minimum gradient of its CURRENT size, pass after pass from the current sizes until no size changes.
3. Gradient of a size: the project's minimum-gradient table (G203 p29 Table 11 by default); a size not in the table
   takes the gradient of the largest tabled size not above it (W18: DN280 as DN250, DN355 as DN315, DN450 as DN400 ...).
4. Re-lay, from the heads down: a conduit's upstream invert is the lowest of (a) the lowest invert arriving at its
   upstream node, (b) the lowest arriving crown minus its own diameter (crowns matched), (c) the shallowest invert the
   minimum cover allows at either end (G203 p33); its downstream invert = upstream - gradient x length.
Pumps and transfer conduits keep their own data. Fixed conduits (locked in the project's settings `design.locked`, or
outside the chosen selection) keep their size and both inverts; the re-lay of the free ones starts from them. Returns
a new project and a report (passes, sizes changed, depth, cover breaches)."""
import numpy as np, pandas as pd
from sewerapp.engine import steady
from sewerapp.engine.hydraulics import section, v_colebrook


def slope_for(settings, dn):
    table = {int(k): float(v) for k, v in settings["design"]["slope_min"].items()}
    keys = sorted(table); below = [k for k in keys if k <= int(dn)]
    return table[below[-1]] if below else table[keys[0]]


def _capacity(project, D, S, ratio):
    f = project.settings["friction"]
    A, R = section(D, ratio * D)
    if f["method"] == "colebrook": return A * v_colebrook(R, S, f["ks_mm"] / 1000.0, f["nu"])
    return A * (1.0 / f["manning_n"]) * R ** (2.0 / 3.0) * np.sqrt(S)


def size(project, q_m3s, start, max_passes=20, fixed=None):
    cat = project.catalogue(); nom = cat.nominal_mm.to_numpy(int); D = cat.inside_mm.to_numpy(float)[None, :] / 1000.0
    lim = project.dd_limit(nom)[None, :]; q = np.asarray(q_m3s, float)[:, None]
    cur = np.asarray(start, int).copy(); keep = np.zeros(len(cur), bool) if fixed is None else np.asarray(fixed, bool)
    for p in range(1, max_passes + 1):
        S = np.array([slope_for(project.settings, n) for n in cur])[:, None]
        ok = _capacity(project, D, S, lim) >= q
        new = nom[np.where(ok.any(axis=1), ok.argmax(axis=1), len(nom) - 1)]
        new[keep] = np.asarray(start, int)[keep]
        changed = int((new != cur).sum()); cur = new
        if changed == 0: return cur, p
    raise RuntimeError(f"sizing did not settle in {max_passes} passes")


def relay(project, links, slope, fixed=frozenset()):
    """Inverts of every gravity conduit from the heads down; returns (up_inv, dn_inv) Series and node inverts. A fixed
    conduit keeps its own inverts, and the conduits below it are laid from them."""
    cover = float(project.settings["design"]["cover_min"]); ground = project.nodes.ground.astype(float)
    grav = links[(links.kind == "conduit")]
    D = grav.inside_mm.astype(float) / 1000.0; L = grav.length_m.astype(float); S = slope.reindex(grav.index)
    out_of = {}; indeg = {}
    for i, a, b in zip(grav.index, grav.from_node, grav.to_node):
        out_of.setdefault(a, []).append(i); indeg[b] = indeg.get(b, 0) + 1
    nodes = set(grav.from_node) | set(grav.to_node)
    stack = [n for n in nodes if indeg.get(n, 0) == 0]
    arr, crown, inv, up, dn = {}, {}, {}, {}, {}
    while stack:
        n = stack.pop()
        for i in out_of.get(n, []):
            a, b = grav.from_node[i], grav.to_node[i]
            lim = [x for x in (ground.get(a, np.nan) - (cover + D[i]), ground.get(b, np.nan) - (cover + D[i]) + S[i] * L[i])
                   if x == x]
            if i in fixed:
                u, d = float(grav.up_inv[i]), float(grav.dn_inv[i])
            else:
                u = min(arr.get(n, np.inf), crown.get(n, np.inf) - D[i], min(lim) if lim else np.inf)
                if not np.isfinite(u):                     # no ground and nothing arriving: keep the drawn invert
                    u = float(grav.up_inv[i])
                d = u - S[i] * L[i]
            up[i], dn[i] = u, d
            inv[n] = min(inv.get(n, np.inf), u, arr.get(n, np.inf))
            arr[b] = min(arr.get(b, np.inf), d); crown[b] = min(crown.get(b, np.inf), d + D[i])
            indeg[b] -= 1
            if indeg[b] == 0: stack.append(b)
    for n, a in arr.items(): inv[n] = min(inv.get(n, np.inf), a)
    return pd.Series(up), pd.Series(dn), pd.Series(inv)


def design(project, load_set=None, only=None):
    """`only`: design these conduits and keep every other one as it is; locked conduits are always kept."""
    p = project.copy(); s = p.settings; load_set = load_set or s["design_load"]
    L = p.links; cond = (L.kind == "conduit")
    fixed = set(map(str, s["design"].get("locked", [])))
    if only is not None: fixed |= set(L.index[cond]) - set(map(str, only))
    fixed &= set(L.index[cond])
    q = steady.flows(p, load_set)
    start = L.dn_mm.fillna(p.catalogue().nominal_mm.iloc[0]).astype(int)
    new, passes = size(p, (q[cond] / 86400.0).to_numpy(), start[cond].to_numpy(), fixed=L.index[cond].isin(fixed))
    changed = int((new != start[cond].to_numpy()).sum())
    L.loc[cond, "dn_mm"] = new
    L.loc[cond, "inside_mm"] = [p.inside_of(n) for n in new]
    slope = pd.Series([slope_for(s, n) for n in L.dn_mm[cond]], index=L.index[cond])
    up, dn, inv = relay(p, L, slope, fixed)
    L.loc[up.index, "up_inv"] = up; L.loc[dn.index, "dn_inv"] = dn
    free = L[cond & ~L.index.isin(fixed)]                          # a node's invert moves only where a free pipe meets it
    touch = set(free.from_node) | set(free.to_node)
    nid = inv.index.intersection(p.nodes.index); nid = nid[nid.isin(list(touch))]
    p.nodes.loc[nid, "invert"] = inv[nid]
    on = list(set(L.from_node[cond]) | set(L.to_node[cond]))       # nodes on a conduit: a lone node's placeholder levels are not a depth
    depth = (p.nodes.ground - p.nodes.invert).astype(float).reindex(on).dropna()
    cmax = float(s["design"]["cover_max"])
    report = dict(load_set=load_set, passes=passes, sizes_changed=changed, conduits=int(cond.sum()), kept=len(fixed),
                  deepest_node=None if depth.dropna().empty else str(depth.idxmax()),
                  deepest_m=None if depth.dropna().empty else round(float(depth.max()), 3),
                  nodes_deeper_than_cover_max=int((depth > cmax).sum()),
                  sizes={int(k): int(v) for k, v in pd.Series(new).value_counts().sort_index().items()})
    return p, report
