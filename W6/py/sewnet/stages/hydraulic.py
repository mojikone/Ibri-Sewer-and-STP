"""HydraulicDesigner — S5/S6: coupled diameter and invert design.

Re-derived clause by clause against G203 (PLAN §3b), then hardened by the adversarial
review. The rules:

  * slope band per reach: S in [Smin(DN, Qpeak), Smax(DN, Qpeak)] — Smin is the steeper
    of Table 11 and tractive force (p27, p29) plus the 40 mm construction guard
    (p29 §4.3.1); Smax caps velocity at 3 m/s (p27/p29), the surplus fall becoming a
    DROP at the chamber; Smax = INFEASIBLE means the diameter can never work at that flow;
  * uniform slope between chambers (p29) — one gradient per reach;
  * mid-span crown cover on the 0.5 m terrain profile (p33): a reach riding above dipping
    ground is shifted down bodily;
  * chamber datum (review SOLVER-1/2): the chamber invert IS the outgoing reach invert, so
    inlet drops are measured inlet-invert minus outgoing-invert and velocity-cap and cover
    shifts combine into the drop they physically are; >600 mm external backdrop, >2 m
    vortex shaft (p30 §4.4 + A9);
  * depth to the outgoing invert > 12 m (p33) -> the chamber joins an SLS pocket (rule 9),
    never a silent orphan;
  * sizing: every candidate DN judged at ITS OWN governing slope (no oversizing, p29) on
    the true bore (review HYD-2); oscillation between adjacent DNs is broken upward
    (review SOLVER-3); a final lay pass always leaves inverts consistent with diameters.
"""

import networkx as nx

from .. import hydra as H
from ..criteria import DEFAULT
from ..model import Network


class HydraulicDesigner:
    def __init__(self, sampler, crit=DEFAULT, max_iter=6, profile_step=5.0):
        self.sampler = sampler
        self.crit = crit
        self.max_iter = max_iter
        self.profile_step = profile_step
        self.report = {}

    # ---------------- one downstream sweep at the current diameters ----------------
    def _lay(self, net: Network, G, order):
        C = self.crit
        invert, drops = {}, {k: [] for k in net.chambers}

        for n in order:
            ch = net.chambers[n]
            in_r = [G[u][n]["reach"] for u in G.predecessors(n)]
            out_r = [G[n][v]["reach"] for v in G.successors(n)]

            dns = [r.dn_mm for r in in_r + out_r] or [C.DN_MIN_MAIN]
            depth_req = max(max(C.invert_depth_min(d) for d in dns), ch.min_depth_req)
            inv = min([r.inv_dn for r in in_r] + [ch.z - depth_req])

            node_inv = inv
            for r in out_r:                      # tree: at most one
                target_ch = net.chambers[r.dn]
                tgt_depth = max(C.invert_depth_min(r.dn_mm), target_ch.min_depth_req)
                target = target_ch.z - tgt_depth

                smin = max(H.smin_for(r.dn_mm, r.qpeak_m3s, C),
                           C.FALL_TOLERANCE / r.length if r.length > 0 else 0.0)
                smax = H.smax_for(r.dn_mm, r.qpeak_m3s, C)
                s_rec = (inv - target) / r.length if r.length > 0 else smin
                S = max(s_rec, smin)
                drop_up = 0.0
                if smax is not None and smax != H.INFEASIBLE and S > smax:
                    drop_up += (S - smax) * r.length     # velocity cap -> drop in the chamber
                    S = smax
                i_up = inv - drop_up

                deficit = 0.0                            # mid-span crown cover (p33)
                D = C.internal_diameter(r.dn_mm)
                for chn, _x, _y, g_ch in r.profile:
                    need = g_ch - (C.MIN_COVER_CROWN + D + C.WALL_ALLOW)
                    if i_up - S * chn > need:
                        deficit = max(deficit, (i_up - S * chn) - need)
                if deficit > 0:
                    i_up -= deficit
                    drop_up += deficit

                r.s_rec, r.slope = s_rec, S
                r.inv_up, r.inv_dn, r.drop_up = i_up, i_up - S * r.length, drop_up
                node_inv = i_up                          # chamber built to its outgoing invert

            invert[n] = node_inv
            for r in in_r:                               # drops measured to the outgoing invert
                h = r.inv_dn - node_inv
                r.drop_dn = h
                if h > C.DROP_TRIGGER:
                    drops[n].append({"pipe": r.label, "height": h,
                                     "type": "backdrop" if h <= C.BACKDROP_MAX else "vortex"})
        return invert, drops

    # ---------------- stage entry point ----------------
    def run(self, net: Network):
        C = self.crit
        G = nx.DiGraph()
        for r in net.reaches:
            G.add_edge(r.up, r.dn, reach=r)
        order = list(nx.topological_sort(G))

        for r in net.reaches:
            if not r.profile:
                r.profile = self.sampler.profile(r.geom, step=self.profile_step)

        converged, invert, drops, it = False, {}, {}, 0
        for it in range(self.max_iter):
            invert, drops = self._lay(net, G, order)
            changed = 0
            for r in net.reaches:
                pick = None
                for dn_c in C.DN_SERIES:
                    S_c = max(r.s_rec, H.smin_for(dn_c, r.qpeak_m3s, C),
                              C.FALL_TOLERANCE / r.length if r.length > 0 else 0.0)
                    smax_c = H.smax_for(dn_c, r.qpeak_m3s, C)
                    if smax_c == H.INFEASIBLE:
                        continue                     # can never satisfy v <= 3 at this flow
                    if smax_c is not None and S_c > smax_c:
                        S_c = smax_c
                    y, v = H.pipe_state(dn_c, S_c, r.qpeak_m3s, C)
                    if y is not None and y <= H.dod_limit(dn_c, C) and \
                            (v is None or v <= C.V_MAX + 0.01):
                        pick = dn_c
                        break
                if pick is None:
                    pick = C.DN_SERIES[-1]           # audit reports it — never silent
                if pick != r.dn_mm:
                    if pick in r.dn_hist:            # oscillation: break upward
                        pick = max(pick, r.dn_mm)
                    if pick != r.dn_mm:
                        r.dn_mm = pick
                        changed += 1
                r.dn_hist.add(r.dn_mm)
            if changed == 0:
                converged = True
                break
        if not converged:
            invert, drops = self._lay(net, G, order)   # leave a consistent state

        for r in net.reaches:
            r.dod, r.vel = H.pipe_state(r.dn_mm, r.slope, r.qpeak_m3s, C)
            r.material = C.material(r.dn_mm)

        for k, ch in net.chambers.items():
            ch.invert = invert.get(k)
            ch.depth = ch.z - ch.invert if ch.invert is not None else None
            ch.drops = drops.get(k, [])
            ch.sls_pocket = False

        pockets = self._pockets(net)
        self.report = {"iterations": it + 1, "converged": converged,
                       "pockets": pockets,
                       "n_failed_depth": sum(1 for c in net.chambers.values()
                                             if c.depth is not None and c.depth > C.MAX_DEPTH)}
        return self.report

    def _pockets(self, net: Network):
        """Chambers needing more than 12 m of dig cluster into non-gravity pockets ->
        SLS candidates (rule 9), never silent orphans."""
        C = self.crit
        failed = {k for k, c in net.chambers.items()
                  if c.depth is not None and c.depth > C.MAX_DEPTH}
        if not failed:
            return []
        Gf = nx.Graph()
        Gf.add_nodes_from(failed)
        for r in net.reaches:
            if r.up in failed and r.dn in failed:
                Gf.add_edge(r.up, r.dn)
        pockets = []
        for comp in nx.connected_components(Gf):
            comp = set(comp)
            props_in = sum(r.n_props for r in net.reaches if r.dn in comp and r.up not in comp)
            props_out = sum(r.n_props for r in net.reaches if r.up in comp and r.dn not in comp)
            low = min(comp, key=lambda k: net.chambers[k].z)
            n_props = max(0, props_out - props_in)
            pockets.append({"nodes": comp, "n_props": n_props, "site": low,
                            "absorb": n_props < C.SLS_MIN_PLOTS})
            for k in comp:
                net.chambers[k].sls_pocket = True
        return pockets
