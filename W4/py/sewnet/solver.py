"""sewnet.solver — S5⇄S6: coupled pipe sizing and invert design.

Re-derived from first principles against G203 (PLAN §3b), then hardened by the
adversarial review (2026-08-18). The rules, each tied to a clause:

  * slope band per pipe: S in [Smin(DN, Qpeak), Smax(DN, Qpeak)] — Smin is the
    steeper of Table 11 and tractive force (p27, p29) plus the 40 mm total-fall
    construction guard (p29 §4.3.1); Smax caps velocity at 3 m/s (p27/p29), the
    surplus fall becoming a DROP at the manhole; Smax = INFEASIBLE -> upsize;
  * uniform slope between manholes (p29) — one S per reach;
  * mid-span crown cover on the 0.5 m terrain profile (p33): a reach riding above
    dipping ground is shifted down bodily;
  * manhole datum (review SOLVER-1/2): the chamber invert IS the outgoing pipe
    invert; inlet drops are measured inlet inv_dn minus OUTGOING invert, so
    velocity-cap and cover shifts combine into the drop they physically are;
    >600 mm -> external backdrop, >2 m -> vortex shaft (p30 §4.4 + A9);
  * depth (to the outgoing invert) > 12 m (p33) -> node joins an SLS pocket
    (rule 9) — never a silent orphan;
  * sizing: every DN candidate judged at ITS OWN governing slope (no-oversizing,
    p29; kills the big-pipe/flat-slope ratchet); oscillation between adjacent DNs
    is broken upward (review SOLVER-3); hydraulics on the TRUE internal bore
    (review HYD-2); a final lay pass always leaves inverts consistent with the
    final diameters.

Requires loads.accumulate() to have run (pipes carry qpeak_m3s).
"""

import networkx as nx

from . import criteria as C
from . import hydra as H


def _pipe_graph(pipes):
    G = nx.DiGraph()
    for p in pipes:
        G.add_edge(p["up"], p["dn"], obj=p)
    return G


def _lay(nodes, pipes, G, order, node_min_depth):
    """One downstream sweep: slopes, inverts, drops — at the CURRENT diameters."""
    invert = {}
    drops = {n: [] for n in nodes}

    for n in order:
        gnd = nodes[n]["z"]
        in_pipes = [G[u][n]["obj"] for u in G.predecessors(n)]
        out_pipes = [G[n][v]["obj"] for v in G.successors(n)]

        dns = [p["dn_mm"] for p in in_pipes + out_pipes] or [C.DN_MIN_MAIN]
        depth_req = max(max(C.invert_depth_min(d) for d in dns),
                        node_min_depth.get(n, 0.0))
        shallow_limit = gnd - depth_req

        arrivals = [p["inv_dn"] for p in in_pipes]
        inv = min(arrivals + [shallow_limit])

        node_inv = inv                      # provisional; out-pipe may push it down
        for p in out_pipes:                 # tree: at most one
            dn = p["dn_mm"]
            L = p["length"]
            q = p["qpeak_m3s"]
            gnd_dn = nodes[p["dn"]]["z"]
            tgt_depth = max(C.invert_depth_min(dn), node_min_depth.get(p["dn"], 0.0))
            target = gnd_dn - tgt_depth

            smin = max(H.smin_for(dn, q), C.FALL_TOLERANCE / L if L > 0 else 0.0)
            smax = H.smax_for(dn, q)
            s_rec = (inv - target) / L if L > 0 else smin
            S = max(s_rec, smin)
            drop_up = 0.0
            if smax is not None and smax != H.INFEASIBLE and S > smax:
                drop_up += (S - smax) * L   # velocity cap: surplus fall drops in the MH
                S = smax
            i_up = inv - drop_up

            # mid-span crown cover on the real terrain profile (p33)
            deficit = 0.0
            D = C.internal_diameter(dn)
            for ch, _x, _y, g_ch in p["profile"]:
                pipe_inv = i_up - S * ch
                need = g_ch - (C.MIN_COVER_CROWN + D + C.WALL_ALLOW)
                if pipe_inv > need:
                    deficit = max(deficit, pipe_inv - need)
            if deficit > 0:
                i_up -= deficit
                drop_up += deficit

            p["s_rec"] = s_rec
            p["slope"] = S
            p["inv_up"] = i_up
            p["inv_dn"] = i_up - S * L
            p["drop_up"] = drop_up
            node_inv = i_up                 # the chamber is built to its outgoing invert

        invert[n] = node_inv
        for p in in_pipes:                  # drops measured to the OUTGOING invert
            h = p["inv_dn"] - node_inv
            p["drop_dn"] = h
            if h > C.DROP_TRIGGER:
                drops[n].append({"pipe": p["label"], "height": h,
                                 "type": "backdrop" if h <= C.BACKDROP_MAX else "vortex"})
    return invert, drops


def solve(nodes, pipes, sampler, node_min_depth=None, max_iter=6, profile_step=5.0):
    """Design DN, slope and inverts for every pipe. Mutates pipes/nodes; returns report."""
    node_min_depth = dict(node_min_depth or {})
    G = _pipe_graph(pipes)
    order = list(nx.topological_sort(G))

    for p in pipes:
        p.setdefault("dn_mm", C.DN_MIN_MAIN)
        p.setdefault("dn_hist", set())
        if "profile" not in p:
            p["profile"] = sampler.profile(p["geom"], step=profile_step)

    converged = False
    invert, drops = {}, {}
    for it in range(max_iter):
        invert, drops = _lay(nodes, pipes, G, order, node_min_depth)

        # resize: judge every candidate DN at the slope THAT DN would be laid at
        changed = 0
        for p in pipes:
            q = p["qpeak_m3s"]
            L = p["length"]
            s_rec = p.get("s_rec", p["slope"])
            pick = None
            for dn_c in C.DN_SERIES:
                S_c = max(s_rec, H.smin_for(dn_c, q),
                          C.FALL_TOLERANCE / L if L > 0 else 0.0)
                smax_c = H.smax_for(dn_c, q)
                if smax_c == H.INFEASIBLE:
                    continue                # this DN can never satisfy v <= 3 at q
                if smax_c is not None and S_c > smax_c:
                    S_c = smax_c
                y, v = H.pipe_state(dn_c, S_c, q)
                if y is not None and y <= H.dod_limit(dn_c) and (v is None or v <= C.V_MAX + 0.01):
                    pick = dn_c
                    break
            if pick is None:
                pick = C.DN_SERIES[-1]      # audit will report it — never silent
            if pick != p["dn_mm"]:
                if pick in p["dn_hist"]:    # oscillation: break the cycle upward
                    pick = max(pick, p["dn_mm"])
                if pick != p["dn_mm"]:
                    p["dn_mm"] = pick
                    changed += 1
            p["dn_hist"].add(p["dn_mm"])
        if changed == 0:
            converged = True
            break

    if not converged:
        invert, drops = _lay(nodes, pipes, G, order, node_min_depth)   # consistent state

    # final hydraulic state on the true bore at the laid slope
    for p in pipes:
        y, v = H.pipe_state(p["dn_mm"], p["slope"], p["qpeak_m3s"])
        p["dod"], p["vel"] = y, v
        p["material"] = C.material(p["dn_mm"])

    for n in nodes:
        nodes[n]["invert"] = invert.get(n)
        nodes[n]["depth"] = nodes[n]["z"] - invert[n] if n in invert else None
        nodes[n]["drops"] = drops.get(n, [])
        nodes[n].pop("sls_pocket", None)

    # non-gravity pockets (depth to the OUTGOING invert > 12 m) -> SLS (rule 9)
    failed = {n for n in nodes if nodes[n]["depth"] is not None and nodes[n]["depth"] > C.MAX_DEPTH}
    pockets = []
    if failed:
        Gf = nx.Graph()
        Gf.add_nodes_from(failed)
        for p in pipes:
            if p["up"] in failed and p["dn"] in failed:
                Gf.add_edge(p["up"], p["dn"])
        for comp in nx.connected_components(Gf):
            comp = set(comp)
            props_in = sum(p["n_props"] for p in pipes if p["dn"] in comp and p["up"] not in comp)
            props_out = sum(p["n_props"] for p in pipes if p["up"] in comp and p["dn"] not in comp)
            n_props = max(0, props_out - props_in)
            low = min(comp, key=lambda n: nodes[n]["z"])
            pockets.append({"nodes": comp, "n_props": n_props, "site": low,
                            "absorb": n_props < C.SLS_MIN_PLOTS})
        for pk in pockets:
            for n in pk["nodes"]:
                nodes[n]["sls_pocket"] = True

    return {"iterations": it + 1, "converged": converged,
            "pockets": pockets, "n_failed_depth": len(failed)}
