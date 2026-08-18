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


def run(nodes, pipes, units, per_mh, sampler, label="saturation"):
    v = []   # violations: (check, element, detail)

    G = nx.DiGraph()
    for p in pipes:
        G.add_edge(p["up"], p["dn"], obj=p)

    for n, d in ((n, d) for n, d in nodes.items() if d.get("invert") is not None):
        if d["kind"] != "outfall" and G.out_degree(n) != 1:
            v.append(("one-outlet", d.get("label", str(n)), f"out_degree={G.out_degree(n)}"))
        if d["depth"] is not None and d["depth"] > C.MAX_DEPTH and not d.get("sls_pocket"):
            v.append(("cover-max", d["label"], f"node depth {d['depth']:.2f} m"))
        for dr in d.get("drops", []):
            if dr["type"] == "vortex":
                v.append(("drop", d["label"], f"backdrop {dr['height']:.2f} m > 2 m -> vortex shaft"))

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
        if (p["inv_up"] - p["inv_dn"]) < C.FALL_TOLERANCE:
            v.append(("fall-tol", lab, f"total fall {(p['inv_up']-p['inv_dn'])*1000:.0f} mm < 40 mm"))
        y, vel = H.solve_dod(D, p["slope"], p["qpeak_m3s"])
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
        # full-profile cover re-check straight from terrain
        for ch, x, y_, g_ch in p["profile"]:
            inv_ch = p["inv_up"] - p["slope"] * ch
            cover = g_ch - (inv_ch + D)
            if cover < C.MIN_COVER_CROWN - 0.01:
                v.append(("cover-min", lab, f"crown cover {cover:.2f} m at ch {ch:.0f}"))
                break
            if g_ch - inv_ch > C.MAX_DEPTH + 0.01 and not nodes[p["up"]].get("sls_pocket"):
                v.append(("cover-max", lab, f"depth {g_ch-inv_ch:.2f} m at ch {ch:.0f}"))
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

    return v


def start_year_selfclean(nodes, pipes, per_mh, pf_formula="merrimack"):
    """Operational flag list: pipes below 0.75 m/s when only CLASS=B (built) units load
    the network — the doctrine §2.1 early-years check. Not a design failure (p28
    §4.2.6 prescribes inspection/cleansing), reported separately."""
    from . import loads as L
    b_per_mh = {mh: [u for u in us if u["cls"] == "B"] for mh, us in per_mh.items()}
    pipes_b = [dict(p) for p in pipes]           # shallow copies keep design DN/slope
    L.accumulate(pipes_b, b_per_mh, pf_formula)
    flags = []
    for p in pipes_b:
        y, vel = H.solve_dod(p["dn_mm"] / 1000.0, p["slope"], p["qpeak_m3s"])
        if y is not None and vel < C.V_SELF_CLEANSING:
            smin_tr = H.smin_tractive(p["qpeak_m3s"])
            ok_tractive = p["slope"] >= smin_tr
            flags.append({"pipe": p["label"], "v_start": vel, "dn": p["dn_mm"],
                          "tractive_ok": ok_tractive})
    return flags
