"""sewnet.pumps — stage B's pump candidates (engineer's answers of 2026-09-12, tmp4 logic rule 16).

Every pocket (a SINK or LOW outlet of stage A) is a pump candidate:

- the station sits at the pocket's low junction, its own network laid to it by gravity;
- the pump rate is the pocket's design peak with its infiltration (Merrimack or Peltier on the
  pocket's Q_ULT and properties), plus whatever another pocket pumps into it;
- it discharges into the lowest header chamber (a junction on a sub main) of a neighbouring
  network that is not a pocket, within PUMP_MAIN_MAX_M by street, or into the chamber the
  engineer names in PUMP_DISCHARGE;
- the pumping main runs along the streets, shortest path, uphill allowed; its high points
  are counted for air valves (G203 p54);
- the main is sized to run between 1.0 m/s (start-stop pumping, G203 p50) and 2.5 m/s, the
  smallest standard size that does, never under 75 mm; friction by Colebrook-White at the
  gravity ks of 1.5 mm plus 10 % for fittings, both stated assumptions; kW at 65 % overall
  efficiency, a stated assumption.

Stage C may move, merge or drop any of these: they are candidates.
"""
import collections
import heapq
import math

from shapely.geometry import LineString, Point
from shapely.ops import linemerge

from . import hydraulics as H
from .ground import profile
from .quicklay import peak_flow_ls

G = 9.81


def _key(c):
    return (round(float(c[0]), 2), round(float(c[1]), 2))


def _graph(reaches, runs):
    """The streets as a graph whose nodes are the chambers: every stage B reach is an edge
    between its two chambers, and every stage A street with no pipe on it is an edge too, so
    a pumping main can reach any chamber along the streets."""
    adj = collections.defaultdict(list)
    edges = []
    for r in reaches:
        a, b = _key(r["geom"].coords[0]), _key(r["geom"].coords[-1])
        edges.append(r["geom"]); i = len(edges) - 1
        adj[a].append((b, r["len"], i)); adj[b].append((a, r["len"], i))
    for r in runs:                       # every street, piped or not
        a, b = _key(r["up"]), _key(r["dn"])
        edges.append(r["geom"]); i = len(edges) - 1
        adj[a].append((b, r["len"], i)); adj[b].append((a, r["len"], i))
    return adj, edges


def _dijkstra(adj, start, cutoff):
    dist, prev = {start: 0.0}, {}
    heap = [(0.0, start)]
    while heap:
        d, n = heapq.heappop(heap)
        if d > dist.get(n, float("inf")) or d > cutoff:
            continue
        for m, L, i in adj.get(n, []):
            nd = d + L
            if nd <= cutoff and nd < dist.get(m, float("inf")):
                dist[m] = nd
                prev[m] = (n, i)
                heapq.heappush(heap, (nd, m))
    return dist, prev


def _path(prev, start, end, edges_geom):
    nodes, edges = [end], []
    n = end
    while n != start:
        p, i = prev[n]
        edges.append(i)
        nodes.append(p)
        n = p
    nodes.reverse(); edges.reverse()
    parts = []
    for a, i in zip(nodes[:-1], edges):
        g = edges_geom[i]
        parts.append(g if math.dist(g.coords[0], a) <= math.dist(g.coords[-1], a) else LineString(g.coords[::-1]))
    merged = linemerge(parts) if len(parts) > 1 else parts[0]
    if merged.geom_type != "LineString":
        coords = [c for p in parts for c in p.coords]
        merged = LineString(coords)
    return nodes, merged


def size_main(q_m3s, sizes, v_min, v_max, ks_m, max_grad=0.01):
    """The smallest standard inside diameter that keeps the pump rate under v_max and the
    friction under max_grad (10 m per km, a stated concept assumption); the velocity it runs
    at; whether it reaches v_min."""
    for dn in sizes:
        D = dn / 1000.0
        v = q_m3s / (math.pi * D * D / 4.0)
        if v <= v_max and friction_head(q_m3s, dn, 1000.0, ks_m) / 1000.0 <= max_grad:
            return dn, v, v >= v_min
    D = sizes[-1] / 1000.0
    return sizes[-1], q_m3s / (math.pi * D * D / 4.0), True


def friction_head(q_m3s, dn, L, ks_m):
    """Head lost in a full pipe, Colebrook-White, by the gradient that carries q full bore."""
    D = dn / 1000.0
    lo, hi = 1e-6, 5.0
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if H.flow(D, mid, 1.0, ks_m) < q_m3s:
            lo = mid
        else:
            hi = mid
    return hi * L


def plan(pipes, reaches, chambers, runs, znode, ground, catch_info, cfg, log=print):
    max_m = float(getattr(cfg, "PUMP_MAIN_MAX_M", 1000.0))
    v_min = float(getattr(cfg, "PUMP_V_MIN_MS", 1.0))
    v_max = float(getattr(cfg, "PUMP_V_MAX_MS", 2.5))
    sizes = tuple(getattr(cfg, "PUMP_MAIN_SIZES_MM", (80, 100, 150, 200, 250, 300)))
    ks = float(getattr(cfg, "PUMP_KS_MM", 1.5)) / 1000.0
    minor = float(getattr(cfg, "PUMP_MINOR_LOSS", 0.10))
    eff = float(getattr(cfg, "PUMP_EFFICIENCY", 0.65))
    sump = float(getattr(cfg, "PUMP_SUMP_M", 1.0))
    infil = float(getattr(cfg, "INFIL_L_D_KM", 720.0))
    overrides = dict(getattr(cfg, "PUMP_DISCHARGE", {}) or {})
    pocket_types = ("SINK", "LOW")
    pockets = {c: i for c, i in catch_info.items() if i["type"] in pocket_types}
    if not pockets:
        return [], [], {}, {"stations": 0}
    adj, edges_geom = _graph(reaches, runs)
    # every header chamber of a network that is not a pocket, by its position: a chamber on a
    # sub main or trunk (an interior one on such a pipe, or a junction one of them ends at)
    header_pipes = {i for i, q in enumerate(pipes) if q.get("tier") in ("sub main", "trunk") and not q.get("dropped")}
    hdr = {}
    for c in chambers:
        p = c.get("pipe")
        on_header = p in header_pipes
        node = c.get("node")
        if not on_header and node is not None:
            on_header = any(i in header_pipes and pipes[i]["dn"] == node for i in header_pipes)
        if on_header and catch_info.get(c["catch"], {}).get("type") not in pocket_types:
            hdr[_key((c["x"], c["y"]))] = c
    # each pocket's own flow: the pipes that end at its outlet
    own = {}
    for cid, info in pockets.items():
        out = info["outlet"]
        ins = [q for q in pipes if q["dn"] == out and not q.get("dropped")]
        q_ult = sum(q.get("q_ult_up", 0.0) for q in ins)
        props = sum(q.get("props_up", 0.0) for q in ins)
        km = info.get("km", 0.0)
        own[cid] = (q_ult, props, km)
    stations, mains, extra = [], [], {}
    # a pocket may pump into another pocket: the order follows the discharges
    disch = {}
    for cid, info in pockets.items():
        out = info["outlet"]
        forced = overrides.get(cid) or next((v for k, v in overrides.items() if isinstance(k, tuple) and math.dist(k, out) < 5.0), None)
        # the search goes as far as the streets go; a main longer than max_m is flagged, not refused
        dist, prev = _dijkstra(adj, _key(out), float(getattr(cfg, "PUMP_MAIN_SEARCH_M", 1e9)))
        cand = []
        if forced is not None:
            tgt = min(hdr, key=lambda n: math.dist(n, forced), default=None) if hdr else None
            if tgt is not None and math.dist(tgt, forced) < 5.0 and tgt in dist:
                cand = [(hdr[tgt]["invert"], dist[tgt], tgt)]
        else:
            # the lowest header chamber within the cap; when none lies within it, within the
            # nearest header's distance and a tenth more, and the main is flagged as long
            reach_ = [(dist[n], n) for n in dist if n in hdr and hdr[n]["catch"] != cid]
            radius = max_m if any(d_ <= max_m for d_, _ in reach_) else (min(d_ for d_, _ in reach_) * 1.1 if reach_ else 0.0)
            cand = [(hdr[n]["invert"], dist[n], n) for d_, n in reach_ if d_ <= radius]
        disch[cid] = (min(cand) if cand else None, dist, prev, forced)
        log(f"      {cid}: {len(dist)} chambers reachable by street, {sum(1 for n in dist if n in hdr)} of them on a header"
            + (f"; nearest header {min(dist[n] for n in dist if n in hdr):.0f} m away" if any(n in hdr for n in dist) else ""))
    # rates in order: a pocket that receives another's flow is rated after it
    receives = collections.defaultdict(float)
    order = list(pockets)
    done = set()
    rates = {}
    guard = 0
    while order and guard < 50:
        guard += 1
        rest = []
        for cid in order:
            best, dist, prev, forced = disch[cid]
            feeders = [k for k, v in disch.items() if v[0] is not None and hdr.get(v[0][2], {}).get("catch") == cid]
            if any(f not in done for f in feeders):
                rest.append(cid); continue
            q_ult, props, km = own[cid]
            peak, pf = peak_flow_ls(q_ult, props, km, infil)
            rate = peak + receives[cid]
            rates[cid] = (rate, pf, peak)
            if best is not None:
                receives[hdr[best[2]]["catch"]] += rate
            done.add(cid)
        order = rest
    for cid, info in pockets.items():
        best, dist, prev, forced = disch[cid]
        out = info["outlet"]
        rate, pf, own_peak = rates.get(cid, (0.0, 0.0, 0.0))
        q = rate / 1000.0
        well = next((c["invert"] for c in chambers if c.get("node") == out), znode.get(out, 0.0) - 2.0) - sump
        st = {"catch": cid, "x": out[0], "y": out[1], "z": znode.get(out, float("nan")), "q_ls": rate, "own_peak_ls": own_peak,
              "pf": pf, "q_ult_m3d": own[cid][0], "props": own[cid][1], "well_inv": well, "plots": info.get("plots", 0)}
        if best is None:
            island = len(adj.get(_key(out), [])) <= 1 or len(disch[cid][1]) < 3
            st.update({"disch_catch": "", "note": ("an island: no street path to any other network" if island else
                                                   "no header chamber reachable by street") if forced is None else "the named chamber is not reachable by street"})
            stations.append(st); continue
        inv_d, L, node = best
        nodes, geom = _path(prev, _key(out), node, edges_geom)
        dn, v, ok_min = size_main(q, sizes, v_min, v_max, ks, float(getattr(cfg, "PUMP_MAX_FRICTION", 0.01)))
        hf = friction_head(q, dn, geom.length, ks) * (1.0 + minor)
        static = inv_d - well
        head = max(static, 0.0) + hf
        kw = 1000.0 * G * q * head / eff / 1000.0 if q > 0 else 0.0
        ch, zg = profile(ground, geom, 10.0)
        highs = sum(1 for k in range(1, len(zg) - 1) if zg[k] > zg[k - 1] + 0.3 and zg[k] > zg[k + 1] + 0.3)
        st.update({"disch_catch": hdr[node]["catch"], "disch_x": node[0], "disch_y": node[1], "disch_inv": inv_d,
                   "static_m": static, "friction_m": hf, "head_m": head, "main_dn": dn, "main_len": geom.length,
                   "v_ms": v, "kw": kw, "high_points": highs, "forced": forced is not None,
                   "note": ("" if ok_min else f"under {v_min} m/s even at the smallest size; ")
                           + (f"main longer than {max_m:.0f} m" if geom.length > max_m else "")})
        stations.append(st)
        mains.append({"catch": cid, "geom": geom, "dn": dn, "len": geom.length, "q_ls": rate, "v_ms": v,
                      "disch_catch": hdr[node]["catch"], "high_points": highs})
        # the pumped flow enters the receiving network at that chamber: at its node when it is a
        # junction, else at the downstream node of the reach it sits on
        c_ = hdr[node]
        n_in = c_.get("node")
        if n_in is None and c_.get("pipe") is not None:
            n_in = pipes[c_["pipe"]]["dn"]
        if n_in is not None:
            extra[n_in] = extra.get(n_in, 0.0) + q
    rep = {"stations": len(stations), "routed": len(mains), "unrouted": [s["catch"] for s in stations if not s.get("disch_catch")],
           "total_q_ls": round(float(sum(s["q_ls"] for s in stations)), 1), "total_kw": round(float(sum(s.get("kw", 0.0) for s in stations)), 1),
           "main_km": round(sum(m["len"] for m in mains) / 1000.0, 2),
           "assumptions": {"ks_mm_pumping_main": ks * 1000, "minor_losses": minor, "efficiency": eff, "sump_below_invert_m": sump,
                           "max_friction_m_per_km": float(getattr(cfg, "PUMP_MAX_FRICTION", 0.01)) * 1000},
           "stations_list": [{k: (round(float(v), 2) if isinstance(v, (float, int)) and not isinstance(v, bool) else v)
                              for k, v in s.items() if k not in ("x", "y")} for s in stations]}
    return stations, mains, extra, rep


def write_shapes(out_dir, prefix, stations, mains, epsg=32640):
    import os
    import geopandas as gpd
    crs = f"EPSG:{epsg}"
    if stations:
        gpd.GeoDataFrame({
            "CATCH": [s["catch"] for s in stations], "Q_LS": [round(s["q_ls"], 2) for s in stations],
            "PF": [round(s["pf"], 2) for s in stations], "Q_ULT_M3D": [round(s["q_ult_m3d"], 1) for s in stations],
            "PROPS": [round(s["props"], 0) for s in stations], "Z_GROUND": [round(s["z"], 2) for s in stations],
            "WELL_INV": [round(s["well_inv"], 2) for s in stations],
            "TO_CATCH": [s.get("disch_catch", "") for s in stations], "DISCH_INV": [round(s.get("disch_inv", 0.0), 2) for s in stations],
            "STATIC_M": [round(s.get("static_m", 0.0), 2) for s in stations], "FRICT_M": [round(s.get("friction_m", 0.0), 2) for s in stations],
            "HEAD_M": [round(s.get("head_m", 0.0), 2) for s in stations], "MAIN_DN": [int(s.get("main_dn", 0)) for s in stations],
            "MAIN_L_M": [round(s.get("main_len", 0.0), 0) for s in stations], "V_MS": [round(s.get("v_ms", 0.0), 2) for s in stations],
            "KW": [round(s.get("kw", 0.0), 2) for s in stations], "HIGH_PTS": [int(s.get("high_points", 0)) for s in stations],
            "FORCED": [int(s.get("forced", False)) for s in stations], "NOTE": [s.get("note", "") for s in stations],
        }, geometry=[Point(s["x"], s["y"]) for s in stations], crs=crs).to_file(os.path.join(out_dir, f"{prefix}_pumps.shp"))
    if mains:
        gpd.GeoDataFrame({
            "CATCH": [m["catch"] for m in mains], "TO_CATCH": [m["disch_catch"] for m in mains], "DN_MM": [m["dn"] for m in mains],
            "LEN_M": [round(m["len"], 0) for m in mains], "Q_LS": [round(m["q_ls"], 2) for m in mains],
            "V_MS": [round(m["v_ms"], 2) for m in mains], "HIGH_PTS": [m["high_points"] for m in mains],
        }, geometry=[m["geom"] for m in mains], crs=crs).to_file(os.path.join(out_dir, f"{prefix}_pmains.shp"))
