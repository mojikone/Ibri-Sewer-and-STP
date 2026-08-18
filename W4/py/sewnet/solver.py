"""sewnet.solver — S5⇄S6: coupled pipe sizing and invert design.

Re-derived from first principles against G203 (PLAN §3b) — the donor's single
downstream sweep survives review ONLY with these additions, each tied to a clause:

  * slope band per pipe: S in [Smin(DN, Qpeak), Smax(DN, Qpeak)] — Smin is the
    steeper of Table 11 and tractive force (p27, p29); Smax caps velocity at 3 m/s
    (p27/p29) with the surplus fall taken as a DROP at the upstream manhole (p30);
  * uniform slope between manholes (p29) — one S per reach, never a kinked profile;
  * mid-span cover enforcement on the 0.5 m terrain profile (p33): a reach that
    violates crown cover under a dipping ground is shifted down bodily, the shift
    surfacing as an explicit backdrop record at its upstream manhole — the donor
    only ever checked endpoints;
  * drop/backdrop bookkeeping per inlet (>600 mm -> external backdrop, >2 m ->
    vortex flag, p30 §4.4 + A9);
  * depth > 12 m (p33) -> node joins a non-gravity POCKET -> SLS candidate per
    rule 9 — never a silent orphan;
  * sizing iterates with the laid slopes until no DN changes (<=5 passes).

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


def solve(nodes, pipes, sampler, node_min_depth=None, max_iter=5, profile_step=5.0):
    """Design DN, slope and inverts for every pipe. Mutates pipes/nodes; returns report.

    node_min_depth: {node_key: minimum invert depth below ground} — the tertiary
    connectability pass raises these where houses sit below road level."""
    node_min_depth = dict(node_min_depth or {})
    G = _pipe_graph(pipes)
    order = list(nx.topological_sort(G))

    for p in pipes:
        p.setdefault("dn_mm", C.DN_MIN_MAIN)

    # cache terrain profiles once (0.5 m VRT, 5 m step)
    for p in pipes:
        if "profile" not in p:
            p["profile"] = sampler.profile(p["geom"], step=profile_step)

    converged = False
    for it in range(max_iter):
        invert = {}
        drops = {n: [] for n in nodes}

        for n in order:
            gnd = nodes[n]["z"]
            in_pipes = [G[u][n]["obj"] for u in G.predecessors(n)]
            out_pipes = [G[n][v]["obj"] for v in G.successors(n)]

            # minimum node invert depth: deepest requirement among connected pipes
            dns = [p["dn_mm"] for p in in_pipes + out_pipes] or [C.DN_MIN_MAIN]
            depth_req = max(max(C.invert_depth_min(d) for d in dns),
                            node_min_depth.get(n, 0.0))
            shallow_limit = gnd - depth_req            # invert may not be above this

            arrivals = [p["inv_dn"] for p in in_pipes]
            inv = min(arrivals + [shallow_limit])
            invert[n] = inv
            for p in in_pipes:
                h = p["inv_dn"] - inv
                if h > C.DROP_TRIGGER:
                    drops[n].append({"pipe": p["label"], "height": h,
                                     "type": "backdrop" if h <= C.BACKDROP_MAX else "vortex"})
                p["drop_dn"] = h

            for p in out_pipes:
                dn = p["dn_mm"]
                L = p["length"]
                q = p["qpeak_m3s"]
                gnd_dn = nodes[p["dn"]]["z"]
                tgt_depth = max(C.invert_depth_min(dn), node_min_depth.get(p["dn"], 0.0))
                target = gnd_dn - tgt_depth

                smin = H.smin_for(dn, q)
                smax = H.smax_for(dn, q)
                s_rec = (inv - target) / L if L > 0 else smin
                # governing slope: recovery toward min cover, but never below the DN's
                # hydraulic minimum NOR below the 40 mm total-fall construction guard
                # (2 x 20 mm line/level tolerance, G203-p29 §4.3.1 — short reaches)
                S = max(s_rec, smin, C.FALL_TOLERANCE / L if L > 0 else smin)
                p["s_rec"] = s_rec
                drop_up = 0.0
                if smax is not None and S > smax:
                    # velocity cap: lay at Smax, take the surplus as a drop at the
                    # upstream manhole (G203-p29 max gradient / p30 drops)
                    surplus = (S - smax) * L
                    S = smax
                    drop_up += surplus
                i_up = inv - drop_up

                # mid-span cover on the real terrain profile (crown cover 1.3, p33)
                deficit = 0.0
                D = dn / 1000.0
                for ch, _x, _y, g_ch in p["profile"]:
                    pipe_inv = i_up - S * ch
                    need = g_ch - (C.MIN_COVER_CROWN + D + C.WALL_ALLOW)
                    if pipe_inv > need:
                        deficit = max(deficit, pipe_inv - need)
                if deficit > 0:
                    i_up -= deficit
                    drop_up += deficit

                p["slope"] = S
                p["inv_up"] = i_up
                p["inv_dn"] = i_up - S * L
                p["drop_up"] = drop_up
                if drop_up > C.DROP_TRIGGER:
                    drops[n].append({"pipe": p["label"], "height": drop_up,
                                     "type": "backdrop" if drop_up <= C.BACKDROP_MAX else "vortex"})

        # ---- resize: evaluate each candidate DN at the slope THAT DN would be laid at
        # (recovery slope if the terrain gives it, else the DN's own minimum). Sizing a
        # big pipe at its own flat minimum and then re-checking an even bigger pipe at a
        # still flatter minimum is a ratchet to absurd diameters — and violates the
        # no-oversizing rule (G203-p29). Smallest compliant DN wins each iteration.
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
                if smax_c is not None and S_c > smax_c:
                    S_c = smax_c
                y, v = H.solve_dod(dn_c / 1000.0, S_c, q)
                if y is not None and y <= H.dod_limit(dn_c) and (v is None or v <= C.V_MAX + 0.01):
                    pick = (dn_c, y, v)
                    break
            if pick is None:                          # even DN1200 fails — keep max, audit reports
                pick = (C.DN_SERIES[-1], None, None)
            dn_new, y, v = pick
            if dn_new != p["dn_mm"]:
                p["dn_mm"] = dn_new
                changed += 1
            p["dod"] = y
            p["vel"] = v
        if changed == 0:
            converged = True
            break

    # final hydraulic state per pipe at the designed DN and slope
    for p in pipes:
        y, v = H.solve_dod(p["dn_mm"] / 1000.0, p["slope"], p["qpeak_m3s"])
        p["dod"], p["vel"] = y, v
        p["material"] = C.material(p["dn_mm"])

    for n in nodes:
        nodes[n]["invert"] = invert.get(n)
        nodes[n]["depth"] = nodes[n]["z"] - invert[n] if n in invert else None
        nodes[n]["drops"] = drops.get(n, [])

    # ---- non-gravity pockets (depth > 12 m) -> SLS candidates (rule 9)
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
            n_props = max(0, props_out - props_in)   # properties landing inside the pocket
            low = min(comp, key=lambda n: nodes[n]["z"])
            pockets.append({"nodes": comp, "n_props": n_props, "site": low,
                            "absorb": n_props < C.SLS_MIN_PLOTS})
        for pk in pockets:
            for n in pk["nodes"]:
                nodes[n]["sls_pocket"] = True

    return {"iterations": it + 1, "converged": converged,
            "pockets": pockets, "n_failed_depth": len(failed)}
