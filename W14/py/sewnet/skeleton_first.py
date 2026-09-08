"""sewnet.skeleton_first — rule 4 in the order the engineer wrote it: sub-mains first, then
hang the rest off them, and the catchments follow the skeleton (W14 trial, 2026-09-08).

W13 chose every node's outlet first, by rule 5's cost, and picked sub-mains per outlet
afterwards; two sub-networks then interleaved street by street and the drawing read as a
maze. Here the long straight streets are attached to an outlet or to a bigger street first,
longest first, and a whole street chooses its outlet, never a node. Every other street then
drains to the nearest skeleton node, and a node's sub-network is the one its skeleton drains
to. What cannot reach any outlet within the connector reach stays as a component; its
lowest end is offered a designed trunk (rule 3) like a pocket in W13.
"""
import collections
import heapq

from . import quicklay as Q


def _adj(runs):
    adj = {}
    for i, r in enumerate(runs):
        u, v, L = r["up"], r["dn"], r["len"]
        adj.setdefault(u, []).append((v, L, i))
        adj.setdefault(v, []).append((u, L, i))
    return adj


def _route(adj, z, start, goal_set, forbid, depth_weight, smin, max_len):
    """Least-depth route (rule 5's cost) from start to the nearest node of goal_set, not
    passing through `forbid` nodes (the chain itself). Returns (nodes, run indices, length)
    or None if none within max_len of street."""
    cost, prev, length = {start: 0.0}, {}, {start: 0.0}
    heap = [(0.0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > cost[u]:
            continue
        if u in goal_set and u != start:
            path, ridx = [u], []
            while path[-1] != start:
                p, i = prev[path[-1]]
                path.append(p)
                ridx.append(i)
            return path[::-1], ridx[::-1], length[u]
        if length[u] > max_len:
            continue
        for v, L, i in adj.get(u, []):
            if v in forbid and v not in goal_set:
                continue
            w = L + depth_weight * max(0.0, smin * L - (z[u] - z[v]))
            if d + w < cost.get(v, float("inf")):
                cost[v] = d + w
                prev[v] = (u, i)
                length[v] = length[u] + L
                heapq.heappush(heap, (d + w, v))
    return None


def orient(chain, runs, filled, level_m):
    """Upstream-first node and run order, by the flood's decided runs; a level chain is left
    as drawn."""
    nodes, seq = chain["nodes"], chain["runs"]
    fwd = 0
    for k, i in enumerate(seq):
        if abs(filled.get(nodes[k], 0.0) - filled.get(nodes[k + 1], 0.0)) <= level_m:
            continue
        fwd += 1 if runs[i]["up"] == nodes[k] else -1
    if fwd < 0:
        return nodes[::-1], seq[::-1]
    return list(nodes), list(seq)


def assemble(runs, z, owner0, chains, filled, level_m, chain_min_m, link_m, depth_weight,
             smin, log=print, max_depth=None, cover=1.55):
    """Attach the long straight streets, longest first, to an outlet or to a street already
    attached. Returns stems, sub-main run set, the owner (outlet) of every skeleton node, the
    unattached chains, and a report."""
    adj = _adj(runs)
    edge = {}
    for i, r in enumerate(runs):
        edge[(r["up"], r["dn"])] = i
        edge[(r["dn"], r["up"])] = i
    S = set(owner0)
    owner = dict(owner0)
    stem, submain = {}, set()
    cands = sorted((c for c in chains if c["len"] >= chain_min_m), key=lambda c: -c["len"])
    used = set()
    pockets = []
    n_attached, n_connector_m, rounds = 0, 0.0, 0
    progress = True
    while progress:
        progress = False
        rounds += 1
        ci = -1
        while ci + 1 < len(cands):
            ci += 1
            c = cands[ci]
            if ci in used:
                continue
            nodes, seq = orient(c, runs, filled, level_m)
            # cut at the first skeleton node from the upstream end
            cut = next((k for k, n in enumerate(nodes) if n in S), None)
            if cut == 0:
                # its head is already on the skeleton: the chain would flow away from it;
                # try the other way round only if that end is free
                used.add(ci)
                continue
            if cut is None:
                hit = _route(adj, z, nodes[-1], S, set(nodes), depth_weight, smin, link_m)
                if hit is None:
                    continue                      # maybe after more streets attach
                path, ridx, Lc = hit
                part_nodes = nodes + path[1:]
                part_runs = seq + ridx
                n_connector_m += Lc
            else:
                part_nodes, part_runs = nodes[:cut + 1], seq[:cut]
            if max_depth is not None:
                # the engineer's line (kept, not yet in the logic): a sub-main crosses a
                # basin only if the basin's fill plus its own fall stays within max_depth;
                # otherwise it ends at the basin's low, which becomes a pocket for a pump,
                # and the street above it attaches to that pocket later
                inv, worst, where = z[part_nodes[0]] - cover, 0.0, None
                for k in range(1, len(part_nodes)):
                    n_ = part_nodes[k]
                    L_ = runs[part_runs[k - 1]]["len"]
                    inv = min(inv - smin * L_, z[n_] - cover)
                    if z[n_] - inv > worst:
                        worst, where = z[n_] - inv, k
                if worst > max_depth:
                    lows = [(filled.get(part_nodes[k], z[part_nodes[k]]) - z[part_nodes[k]], k)
                            for k in range(1, where)]
                    fill, kb = max(lows) if lows else (0.0, None)
                    if kb is not None and fill > 0.5:
                        pocket = part_nodes[kb]
                        owner[pocket] = pocket
                        S.add(pocket)
                        pockets.append(pocket)
                        head_part = {"nodes": part_nodes[:kb + 1], "runs": part_runs[:kb],
                                     "len": sum(runs[i]["len"] for i in part_runs[:kb])}
                        if head_part["len"] >= chain_min_m:
                            cands.append(head_part)
                        part_nodes, part_runs = part_nodes[kb:], part_runs[kb:]
            o = owner[part_nodes[-1]]
            for k in range(len(part_nodes) - 1):
                u, v = part_nodes[k], part_nodes[k + 1]
                if u not in stem:
                    stem[u] = v
                owner.setdefault(u, o)
                S.add(u)
            for i in part_runs:
                submain.add(i)
            used.add(ci)
            n_attached += 1
            progress = True
    left = [c for ci, c in enumerate(cands) if ci not in used]
    rep = {"chains_over_min": len(cands), "attached": n_attached, "rounds": rounds,
           "connector_km": round(n_connector_m / 1000, 2),
           "unattached": len(left), "unattached_km": round(sum(c["len"] for c in left) / 1000, 2),
           "submain_km": round(sum(runs[i]["len"] for i in submain) / 1000, 2),
           "pockets_cut_at_a_basin": len(pockets)}
    rep["pockets"] = pockets
    return stem, submain, owner, left, rep


def components(left, runs):
    """Unattached chains grouped by shared nodes: each group is a settlement's own skeleton
    with no way out within reach."""
    node_of = collections.defaultdict(list)
    for k, c in enumerate(left):
        for n in c["nodes"]:
            node_of[n].append(k)
    seen, groups = set(), []
    for k in range(len(left)):
        if k in seen:
            continue
        grp, stack = [], [k]
        seen.add(k)
        while stack:
            j = stack.pop()
            grp.append(j)
            for n in left[j]["nodes"]:
                for m in node_of[n]:
                    if m not in seen:
                        seen.add(m)
                        stack.append(m)
        groups.append([left[j] for j in grp])
    return groups
