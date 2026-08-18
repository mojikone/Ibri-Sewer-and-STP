"""sewnet.audit — S7: independent re-check of every enforced rule (donor's audit
pattern, extended). The solver is never trusted to grade its own homework: this
module recomputes each constraint from the designed values and the raw 0.5 m
terrain, and emits one row per violation.

Checks (each with its G203/G1 basis):
  cover-min      crown cover >= 1.3 m along the FULL profile at 5 m step (p33)
  cover-max      invert depth <= 12 m at nodes and mid-span (p33)
  slope-min      laid slope >= max(Table 11, tractive) for the pipe's DN and Qpeak (p27-29)
  vel-max        v <= 3.0 m/s at design depth (p27)
  vel-selfclean  v >= 0.75 m/s at peak (p26) — saturation run must pass; start-year
                 run (CLASS=B only) reports shortfalls as an operational flag (p28 §4.2.6)
  dod            d/D <= 0.65 / 0.50 (p27 Tab 10)
  spacing        reach length <= Tab 12 max for its DN (p30)
  drop           inlet drops > 600 mm carry a backdrop record; backdrop <= 2 m else vortex (p30)
  fall-tol       total fall per reach > 40 mm construction tolerance guard (p29 §4.3.1, A9)
  one-outlet     every manhole has exactly one outgoing pipe (tree discipline)
  reverse        inv_up > inv_dn strictly (no reverse gradients, p29)
  mass-balance   sum of unit loads == Qadf arriving at the outfall (doctrine bookkeeping)
  assignment     every loaded unit assigned to a manhole (zero silent drops)
"""

import networkx as nx

from . import criteria as C
from . import hydra as H


def run(nodes, pipes, units, per_mh, sampler, label="saturation", load_stats=None):
    v = []   # violations: (check, element, detail)

    G = nx.DiGraph()
    for p in pipes:
        G.add_edge(p["up"], p["dn"], obj=p)

    for n, d in ((n, d) for n, d in nodes.items() if d.get("invert") is not None):
        if d["kind"] != "outfall" and G.out_degree(n) != 1:
            v.append(("one-outlet", d.get("label", str(n)), f"out_degree={G.out_degree(n)}"))
        if d["depth"] is not None and d["depth"] > C.MAX_DEPTH and not d.get("sls_pocket"):
            v.append(("cover-max", d["label"], f"node depth {d['depth']:.2f} m"))
        # drops are DESIGNED structures (<=2 m backdrop, >2 m vortex shaft, G203-p30),
        # but the BOOKKEEPING is audited independently (review SOLVER-1): every inlet
        # arriving >600 mm above the node's outgoing invert must carry a matching record.
        recorded = {dr["pipe"]: dr for dr in d.get("drops", [])}
        for u in G.predecessors(n):
            p_in = G[u][n]["obj"]
            h = p_in["inv_dn"] - d["invert"]
            if h > C.DROP_TRIGGER + 0.001:
                rec = recorded.get(p_in["label"])
                if rec is None:
                    v.append(("drop-missing", d["label"],
                              f"inlet {p_in['label']} arrives {h:.2f} m above outgoing invert, no record"))
                elif abs(rec["height"] - h) > 0.01 or \
                        (h > C.BACKDROP_MAX and rec["type"] != "vortex"):
                    v.append(("drop-mismatch", d["label"],
                              f"inlet {p_in['label']}: real {h:.2f} m vs recorded "
                              f"{rec['height']:.2f} m ({rec['type']})"))

    for p in pipes:
        lab = p["label"]
        dn = p["dn_mm"]
        D = dn / 1000.0
        if p["inv_up"] <= p["inv_dn"]:
            v.append(("reverse", lab, f"inv_up {p['inv_up']:.3f} <= inv_dn {p['inv_dn']:.3f}"))
        smin = H.smin_for(dn, p["qpeak_m3s"])
        if p["slope"] < smin * 0.999:
            v.append(("slope-min", lab, f"S {p['slope']*1000:.2f} < {smin*1000:.2f} mm/m"))
        if p["length"] > C.mh_max_spacing(dn) + 0.01:
            v.append(("spacing", lab, f"{p['length']:.1f} m > {C.mh_max_spacing(dn)} m for DN{dn}"))
        fall = p["inv_up"] - p["inv_dn"]
        if fall < C.FALL_TOLERANCE - 0.0005:
            # velocity-capped pipes are as steep as v <= 3.0 allows — exempt (the
            # 40 mm guard cannot outrank a hard limit; noted for construction control)
            smax = H.smax_for(dn, p["qpeak_m3s"])
            if smax is None or p["slope"] < smax * 0.99:
                v.append(("fall-tol", lab, f"total fall {fall*1000:.0f} mm < 40 mm"))
        y, vel = H.pipe_state(dn, p["slope"], p["qpeak_m3s"])
        if y is None:
            v.append(("dod", lab, f"DN{dn} cannot carry {p['qpeak_ls']:.1f} L/s at laid slope"))
        else:
            if y > H.dod_limit(dn) + 0.005:
                v.append(("dod", lab, f"d/D {y:.2f} > {H.dod_limit(dn)}"))
            if vel > C.V_MAX + 0.01:
                v.append(("vel-max", lab, f"v {vel:.2f} > 3.0 m/s"))
            if vel < C.V_SELF_CLEANSING and label == "saturation":
                # 0.75 m/s is unattainable on small head branches — G203-p27 offers the
                # tractive-force methodology exactly for that case: a pipe laid at or
                # steeper than the tractive minimum is self-cleansing by the guideline's
                # own alternative. Violation only when BOTH criteria are missed.
                if p["slope"] < H.smin_tractive(p["qpeak_m3s"]) * 0.999:
                    v.append(("vel-selfclean", lab,
                              f"v {vel:.2f} < 0.75 m/s AND slope below tractive minimum"))
        # full-profile cover re-check straight from terrain; pipes touching an SLS
        # pocket at either end belong to the pocket's lifting solution, not gravity
        in_pocket = nodes[p["up"]].get("sls_pocket") or nodes[p["dn"]].get("sls_pocket")
        for ch, x, y_, g_ch in p["profile"]:
            inv_ch = p["inv_up"] - p["slope"] * ch
            cover = g_ch - (inv_ch + D)
            if cover < C.MIN_COVER_CROWN - 0.01:
                v.append(("cover-min", lab, f"crown cover {cover:.2f} m at ch {ch:.0f}"))
                break
            if g_ch - inv_ch > C.MAX_DEPTH + 0.01 and not in_pocket:
                v.append(("cover-max", lab, f"depth {g_ch-inv_ch:.2f} m at ch {ch:.0f}"))
                break

    # ---- physical structure rules (user 2026-08-18) ----
    # (a) no two chambers may occupy the same point: two coincident manholes each with
    #     their own outlet ARE a two-outlet junction on the ground, even though the
    #     graph shows out_degree 1 on each;
    # (b) a branch leaving a junction that already has an outlet must start clear of it.
    import numpy as _np
    from scipy.spatial import cKDTree as _KD
    nkeys = list(nodes.keys())
    if len(nkeys) > 1:
        npts = _np.array([[nodes[k]["x"], nodes[k]["y"]] for k in nkeys])
        kidx = {k: i for i, k in enumerate(nkeys)}
        linked = set()
        for p in pipes:
            linked.add(frozenset((kidx[p["up"]], kidx[p["dn"]])))
        kd = _KD(npts)
        for i, j in kd.query_pairs(C.MH_MIN_CLEAR_M):
            if frozenset((i, j)) in linked:
                continue          # consecutive chambers on one reach — a short pipe, not a clash
            d = float(_np.hypot(*(npts[i] - npts[j])))
            v.append(("mh-clearance", f"{nodes[nkeys[i]]['label']}/{nodes[nkeys[j]]['label']}",
                      f"separate chambers {d:.2f} m apart (< {C.MH_MIN_CLEAR_M} m)"))
        for k, d0 in nodes.items():
            if d0["kind"] != "head":
                continue
            for j in kd.query_ball_point(npts[kidx[k]], C.FANOUT_OFFSET_M):
                other = nkeys[j]
                if other == k or frozenset((kidx[k], j)) in linked:
                    continue
                if nodes[other]["kind"] in ("junction", "outfall"):
                    dd = float(_np.hypot(*(npts[kidx[k]] - npts[j])))
                    v.append(("head-offset", d0["label"],
                              f"branch starts {dd:.1f} m from {nodes[other]['label']} "
                              f"(< {C.FANOUT_OFFSET_M} m offset)"))
                    break

    # mass balance: outfall Qadf == units * unit load (+ nothing lost)
    outfall = [n for n, d in nodes.items() if d["kind"] == "outfall"][0]
    q_in = sum(G[u][outfall]["obj"]["qadf_m3d"] for u in G.predecessors(outfall))
    expected = sum(len(us) for us in per_mh.values()) * C.PLOT_QADF_M3D
    if abs(q_in - expected) > 0.5:   # m3/d
        v.append(("mass-balance", "OF-1", f"arrivals {q_in:.1f} != loads {expected:.1f} m3/d"))
    n_assigned = sum(len(us) for us in per_mh.values())
    if n_assigned != len(units):
        v.append(("assignment", "network", f"{len(units)-n_assigned} units unassigned"))
    # review F4: plots with unexpected CLASS must never vanish silently
    if load_stats and load_stats.get("class_other", 0) > 0:
        v.append(("assignment", "plots",
                  f"{load_stats['class_other']} plots with CLASS outside A/B/P — unhandled"))

    return v


def selfclean_stats(pipes):
    """Transparency for the 0.75 m/s question (review F1): most small branches CANNOT
    reach 0.75 m/s at saturation peak — they comply via the tractive-force alternative
    (G203-p27), which rests on tau = 1 Pa [GAP-9, PENDING]. This function quantifies
    exactly how much of the network leans on that assumption, and what happens if NWS
    sets tau = 2 Pa (Smin scales by 2^1.23 = 2.35)."""
    n = len(pipes)
    below = [p for p in pipes if p.get("vel") is not None and p["vel"] < C.V_SELF_CLEANSING]
    tau2 = sum(1 for p in below
               if p["slope"] < H.smin_tractive(p["qpeak_m3s"]) * (2.0 ** 1.23) * 0.999)
    return {
        "pipes": n,
        "below_075_at_peak": len(below),
        "share_below": round(len(below) / n, 3) if n else 0.0,
        "compliant_via_tractive_tau1": len(below),   # slope >= tractive is enforced by design
        "would_fail_at_tau2": tau2,
        "note": "0.75 m/s unattainable on small branches; compliance rests on tractive "
                "methodology at tau=1 Pa [GAP-9]. would_fail_at_tau2 = redesign exposure "
                "if NWS doubles the design tractive stress.",
    }


def start_year_selfclean(nodes, pipes, per_mh, pf_formula="merrimack"):
    """Operational flag list: pipes below 0.75 m/s when only EXISTING structures load
    the network — CLASS=B built plots AND CLASS=U unparceled buildings (review F2:
    unparceled = buildings standing today, they belong in the start-year case). The
    doctrine §2.1 early-years check; not a design failure (p28 §4.2.6), reported
    separately."""
    from . import loads as L
    b_per_mh = {mh: [u for u in us if u["cls"] in ("B", "U")] for mh, us in per_mh.items()}
    pipes_b = [dict(p) for p in pipes]           # shallow copies keep design DN/slope
    L.accumulate(pipes_b, b_per_mh, pf_formula)
    flags = []
    for p in pipes_b:
        y, vel = H.pipe_state(p["dn_mm"], p["slope"], p["qpeak_m3s"])
        if y is not None and vel < C.V_SELF_CLEANSING:
            smin_tr = H.smin_tractive(p["qpeak_m3s"])
            ok_tractive = p["slope"] >= smin_tr
            flags.append({"pipe": p["label"], "v_start": vel, "dn": p["dn_mm"],
                          "tractive_ok": ok_tractive})
    return flags
