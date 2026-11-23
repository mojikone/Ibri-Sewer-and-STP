"""Steady pressure hydraulics of pump stations and their force mains (2026-11-23, v3), the part of a sewer model that
SewerGEMS solves with its pressure engine.

A pump (a link from a wet well) delivers, in the steady run, the flow that reaches its wet well (the sanitary engine's
pumped transfer). Downstream of it a chain of pressure pipes and pressure junctions carries that flow to the gravity
structure where the main discharges. For each pump the main is walked back from that structure:

- the main ends at the higher of the last pipe's crown at the receiving structure (a main discharging full) and the
  water level in that structure (its invert plus the flow depth of the pipe leaving it, from the gravity solve);
- each pipe loses friction (Hazen-Williams, Darcy-Weisbach with Colebrook-White, or Manning, by the project's pressure
  friction method or the pipe's own) plus minor losses K v2/2g;
- the pump's total dynamic head is the hydraulic grade at its outlet less the wet well level (its stop level: the
  lowest level and the largest static lift, unless the project says otherwise);
- with a pump definition, the pump's own head at that flow is compared with the head needed, and the operating point
  where the pump curve meets the main's system curve is found, from the stop level and from the start level;
  `count` identical pumps in parallel share the flow (H = A - B (Q/n)^C); a pump whose shutoff head is below the static
  lift delivers nothing (its check valve holds) and is flagged;
- the pressure head along the main is the grade less the pipe's invert; a negative one (a high point) is flagged.

Pump definitions (project.settings.libraries.pumps, by name): design point (EPANET's single-point convention:
H = 4/3 Hd - (1/3 Hd / Qd^2) Q^2, cut off at 2 Qd), standard three-point (H = A - B Q^C through shutoff, design and
maximum points), multiple point (straight lines between the points) and constant flow."""
import math
import numpy as np, pandas as pd

G = 9.80665
PRESSURE_DEFAULT = dict(method="hazen", C=130.0, e_mm=0.1, n=0.012, suction="off")


def curve(defn):
    """A pump definition as a function H(Q) (Q m3/s, H m) and its maximum flow; None for a constant-flow pump."""
    t = defn.get("type")
    if t == "design_point":
        Q, H = float(defn["q_ls"]) / 1000.0, float(defn["h_m"])
        A, B = 4.0 / 3.0 * H, H / 3.0 / Q ** 2
        return (lambda q: np.maximum(A - B * np.asarray(q, float) ** 2, 0.0)), 2.0 * Q
    if t == "three_point":
        H0 = float(defn["shutoff_h_m"]); Q1, H1 = float(defn["q_ls"]) / 1000.0, float(defn["h_m"]); Q2, H2 = float(defn["max_q_ls"]) / 1000.0, float(defn["max_h_m"])
        if not (H0 > H1 > H2 >= 0 and Q2 > Q1 > 0): raise ValueError(f"pump {defn.get('name')}: needs shutoff > design > maximum head and maximum flow > design flow")
        C = math.log((H0 - H2) / (H0 - H1)) / math.log(Q2 / Q1); B = (H0 - H1) / Q1 ** C
        qmax = (H0 / B) ** (1.0 / C)
        return (lambda q: np.maximum(H0 - B * np.asarray(q, float) ** C, 0.0)), qmax
    if t == "multi_point":
        pts = sorted((float(a) / 1000.0, float(b)) for a, b in defn["points"])
        if len(pts) < 2: raise ValueError(f"pump {defn.get('name')}: a multiple-point curve needs two points or more")
        qs, hs = [p[0] for p in pts], [p[1] for p in pts]
        return (lambda q: np.interp(np.asarray(q, float), qs, hs, right=0.0)), qs[-1]
    if t == "constant_flow": return None, float(defn["q_ls"]) / 1000.0
    raise ValueError(f"pump definition type must be design_point, three_point, multi_point or constant_flow, not {t}")


def headloss(method, Q, D, L, C=130.0, e_mm=0.1, n=0.012, nu=1.141e-6):
    """Friction loss (m) in a full pipe: Hazen-Williams (SI, 10.67), Darcy-Weisbach (Colebrook-White f) or Manning."""
    Q = abs(float(Q))
    if Q == 0 or not D > 0: return 0.0
    if method == "hazen": return 10.67 * L * Q ** 1.852 / (C ** 1.852 * D ** 4.8704)
    A = math.pi * D * D / 4; v = Q / A
    if method == "darcy":
        Re = v * D / nu
        if Re < 2000: f = 64.0 / Re
        else:                                                         # Colebrook-White, iterated from Swamee-Jain
            f = 0.25 / math.log10(e_mm / 1000.0 / (3.7 * D) + 5.74 / Re ** 0.9) ** 2
            for _ in range(30):
                f1 = (-2.0 * math.log10(e_mm / 1000.0 / (3.7 * D) + 2.51 / (Re * math.sqrt(f)))) ** -2
                if abs(f1 - f) < 1e-12: break
                f = f1
        return f * L / D * v * v / (2 * G)
    if method == "manning": return L * (n * v) ** 2 / (D / 4) ** (4.0 / 3.0)
    raise ValueError(f"pressure friction method must be hazen, darcy or manning, not {method}")


def solve(project, q_m3d, depth_at=None):
    """Per pressure pipe and per pump: flow, velocity, losses, hydraulic grade; per pump: head needed, the pump's head
    at that flow and the operating point. Returns (rows by link id, summary)."""
    L, N = project.links, project.nodes; s = dict(PRESSURE_DEFAULT, **(project.settings.get("pressure") or {}))
    nu = float(project.settings.get("friction", {}).get("nu", 1.141e-6))
    own = getattr(project, "ppipes", None) or {}; pumps = getattr(project, "pumps", None) or {}
    lib = {d["name"]: d for d in ((project.settings.get("libraries") or {}).get("pumps") or [])}
    leaving = {}
    for i, r in L.iterrows(): leaving.setdefault(r.from_node, []).append(i)
    out, summ = {}, dict(pumps=0, pumps_short=0, mains=0, km_mains=0.0)

    def pipe_loss(lid, Q):
        r = L.loc[lid]; o = own.get(lid, {}); D = float(r.inside_mm) / 1000.0 if r.inside_mm == r.inside_mm else 0.0
        meth = o.get("method", s["method"])
        hf = headloss(meth, Q, D, float(r.length_m), C=float(o.get("C", s["C"])), e_mm=float(o.get("e_mm", s["e_mm"])), n=float(o.get("n", s["n"])), nu=nu)
        v = abs(Q) / (math.pi * D * D / 4) if D > 0 else 0.0
        return hf, float(o.get("K", 0.0)) * v * v / (2 * G), v, D

    for pid in L.index[L.kind == "pump"]:
        pr = L.loc[pid]; Q = float(q_m3d.get(pid, 0.0)) / 86400.0
        main, n = [], pr.to_node                                          # the force main: pressure pipes from the pump on
        while n in leaving and len(main) < 10000:
            nxt = [l for l in leaving[n] if L.kind[l] == "pressure_pipe"]
            if not nxt: break
            main.append(nxt[0]); n = L.to_node[nxt[0]]
        end = n
        crown = (float(L.dn_inv[main[-1]]) + pipe_loss(main[-1], 0)[3]) if main else float(N.invert[end])
        level = float(N.invert[end]) + float((depth_at or {}).get(end, 0.0))     # the water in the receiving structure
        out_level = max(crown, level)
        def system(Qx):                                                   # hydraulic grade at the pump's outlet for a flow
            h = out_level
            for lid in reversed(main): hf, hm, _, _ = pipe_loss(lid, Qx); h += hf + hm
            return h
        pu = pumps.get(pid, {}); ww = pr.from_node; npump = max(1, int(pu.get("count") or 1))
        lvl = {"off": pu.get("off_m"), "on": pu.get("on_m")}.get(s.get("suction", "off"))
        suction = float(N.invert[ww]) + float(lvl or 0.0)
        h_out = system(Q); tdh = h_out - suction
        row = dict(kind="pump", q_ls=Q * 1000.0, tdh_m=tdh, static_m=out_level - suction, hgl_out=h_out, suction_m=suction,
                   main=",".join(main), discharges_to=end, pumps_running=npump)
        d = lib.get(pu.get("definition")) if pu.get("definition") else None
        if d:
            H1, qmax1 = curve(d)
            if H1 is None: row.update(pump_q_ls=qmax1 * 1000.0 * npump, short=Q > qmax1 * npump * 1.0001)
            else:
                Hf = lambda q, H1=H1: H1(np.asarray(q, float) / npump); qmax = qmax1 * npump   # n identical pumps in parallel
                hp = float(Hf(Q)); row.update(pump_head_m=hp, short=hp + 1e-6 < tdh)
                def op(suct):                                             # operating point: pump curve meets system curve
                    if float(Hf(0.0)) <= system(0.0) - suct: return 0.0, float(Hf(0.0)), True
                    lo, hi = 0.0, qmax
                    for _ in range(80):
                        mid = (lo + hi) / 2
                        if float(Hf(mid)) > system(mid) - suct: lo = mid
                        else: hi = mid
                    return lo, float(Hf(lo)), False
                q0, h0, cl = op(suction); row.update(op_q_ls=q0 * 1000.0, op_h_m=h0, cannot_lift=cl)
                if cl: row["short"] = True
                for name, dep in (("off", pu.get("off_m")), ("on", pu.get("on_m"))):     # at the stop and start levels
                    if dep is not None:
                        qx, hx, _ = op(float(N.invert[ww]) + float(dep)); row[f"op_q_{name}_ls"] = qx * 1000.0; row[f"op_h_{name}_m"] = hx
            summ["pumps_short"] += int(bool(row.get("short")))
        out[pid] = row; summ["pumps"] += 1
        h = system(Q)                                                     # the grade along the main at the duty flow
        for lid in main:
            hf, hm, v, D = pipe_loss(lid, Q); r = L.loc[lid]
            z0, z1 = float(r.up_inv), float(r.dn_inv)
            out[lid] = dict(kind="pressure_pipe", q_ls=Q * 1000.0, v_ms=v, hf_m=hf, hm_m=hm, hgl_up=h, hgl_dn=h - hf - hm,
                            p_up_m=h - z0, p_dn_m=h - hf - hm - z1, s_f_m_per_km=hf / float(r.length_m) * 1000.0 if r.length_m else 0.0,
                            negative_pressure=bool(Q > 0 and min(h - z0, h - hf - hm - z1) < 0))
            summ["negative_pressure"] = summ.get("negative_pressure", 0) + int(out[lid]["negative_pressure"])
            h -= hf + hm
        summ["mains"] += int(bool(main)); summ["km_mains"] += float(L.length_m[main].sum()) / 1000.0 if main else 0.0
    summ["km_mains"] = round(summ["km_mains"], 3)
    return out, summ


def system_curve(project, pid, q_ls_points, q_m3d=None):
    """Head needed by pump `pid` at each flow (L/s): its main's system curve, for the pump-definition graph."""
    res = []
    for qls in q_ls_points:
        qq = pd.Series({pid: qls * 86.4}); r, _ = solve(project, qq.to_dict()); res.append(r[pid]["tdh_m"])
    return res
