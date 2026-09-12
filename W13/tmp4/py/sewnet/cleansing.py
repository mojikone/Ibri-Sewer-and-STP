"""sewnet.cleansing — the self-cleansing audit on the low case (W13 temp 3, 2026-09-11).

The engineer's ruling (W14/docs/DESIGN_FLOWS_FOR_NETWORK.md, sections 3.4, 4 and 8): the
flow is Q_2030 x 0.61 of the plots upstream, peaked with the properties counted connected
(2030 x 0.61) to choose Merrimack or Peltier, and no infiltration. Each pipe takes one
class, and the audit changes no size and no gradient:

- velocity: at least 0.75 m/s at the low-case peak (G203-p26);
- tractive: the laid gradient at least Mara's Smin = K tau^1.23 Q^-0.461, tau = 1 Pa,
  K = 2.33e-4 with Q in m3/s, on the true flow with no floor (G203-p27);
- washing: everything else, the flushing list (G203 4.2.6, p28).

No regrade class and no low-flow threshold: a pipe laid to the guideline gradient that
still carries too little flow needs washing, not a steeper pipe.
"""
import collections
import math

from .quicklay import MANNING_N, bore, peak_flow_ls

V_MIN = 0.75          # m/s at the low-case peak (G203-p26)
MARA_K = 2.33e-4      # Q in m3/s (engineer, 2026-09-11)
TAU_PA = 1.0          # concept-stage value, NWS to confirm (GAP-9)
CLASSES = ("velocity", "tractive", "washing")


def _flow(D, S, theta, n=MANNING_N):
    A = D * D / 8.0 * (theta - math.sin(theta))
    P = D * theta / 2.0
    return A * (1.0 / n) * (A / P) ** (2.0 / 3.0) * math.sqrt(S), A


def part_full(D, S, q_m3s):
    """Depth ratio and velocity of a flow in a circular pipe at gradient S, by Manning.
    The flow rises with depth up to 0.938 D; a flow above that maximum is returned at it."""
    if q_m3s <= 0.0 or S <= 0.0:
        return 0.0, 0.0
    th_max = 5.278
    q_max, a_max = _flow(D, S, th_max)
    if q_m3s >= q_max:
        return (1.0 - math.cos(th_max / 2.0)) / 2.0, q_m3s / a_max
    lo, hi = 1e-6, th_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if _flow(D, S, mid)[0] < q_m3s:
            lo = mid
        else:
            hi = mid
    th = 0.5 * (lo + hi)
    _, A = _flow(D, S, th)
    return (1.0 - math.cos(th / 2.0)) / 2.0, q_m3s / A


def mara_slope(q_m3s, tau=TAU_PA, k=MARA_K):
    """Mara's minimum slope for the tractive tension tau (m/m); infinite with no flow."""
    return k * tau ** 1.23 * q_m3s ** -0.461 if q_m3s > 0.0 else float("inf")


def audit(pipes, connected=0.61, v_min=V_MIN, tau=TAU_PA, k=MARA_K):
    """Classes every pipe on the low case and writes q_low_ls, v_low, yd_low, s_mara and
    cleanse onto it. Returns the counts and lengths by class and by tier."""
    for q in pipes:
        qadf = q.get("q_2030_up", 0.0) * connected
        props = q.get("props_2030_up", 0.0) * connected
        peak, pf = peak_flow_ls(qadf, props, 0.0, 0.0)
        q_m3s = peak / 1000.0
        S = q.get("grad_laid", 0.0)
        yd, v = part_full(bore(q["dn_mm"]), S, q_m3s)
        sm = mara_slope(q_m3s, tau, k)
        q["q_low_ls"], q["pf_low"], q["v_low"], q["yd_low"] = peak, pf, v, yd
        q["s_mara"] = sm
        q["cleanse"] = ("velocity" if v >= v_min else "tractive" if S >= sm else "washing")
    from .export_tree import TIER_NAME
    rep = {"flow": f"Q_2030 x {connected}, properties connected, no infiltration",
           "v_min_ms": v_min, "tau_pa": tau, "mara_k": k, "by_class": {}, "by_tier": {},
           "by_role": {}}
    by = collections.defaultdict(lambda: [0, 0.0])
    byt = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0]))
    byr = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0]))
    for q in pipes:
        by[q["cleanse"]][0] += 1
        by[q["cleanse"]][1] += q["len"]
        r = q.get("tier", "?")
        for d, key in ((byt, TIER_NAME.get(r, r)), (byr, r)):
            d[key][q["cleanse"]][0] += 1
            d[key][q["cleanse"]][1] += q["len"]
    total = sum(v[1] for v in by.values()) or 1.0
    for c in CLASSES:
        n, L = by.get(c, [0, 0.0])
        rep["by_class"][c] = {"pipes": n, "km": round(L / 1000.0, 1),
                              "pct_length": round(100.0 * L / total, 1)}
    for name, src in (("by_tier", byt), ("by_role", byr)):
        for t, d in src.items():
            rep[name][t] = {c: {"pipes": d[c][0], "km": round(d[c][1] / 1000.0, 1)}
                            for c in CLASSES}
    return rep


def write_tables(pipes, rep, out_dir, connected=0.61):
    """The audit's table (pipes and km by class and by tier, and by role) as markdown and
    CSV, and the washing list: every pipe on it with why. PIPE_ID matches the shapefile."""
    import csv
    import os
    from .export_tree import TIER_NAME
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for key in ("by_tier", "by_role"):
        for t, d in rep[key].items():
            rows.append([key[3:], t] + [x for c in CLASSES for x in (d[c]["pipes"], d[c]["km"])])
    with open(os.path.join(out_dir, "cleansing_table.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["by", "name"] + [f"{c}_{u}" for c in CLASSES for u in ("pipes", "km")])
        w.writerows(rows)
        w.writerow(["all", "all"] + [x for c in CLASSES
                                     for x in (rep["by_class"][c]["pipes"], rep["by_class"][c]["km"])])
    lines = ["# Self-cleansing audit, W13 temp 3", "",
             f"Low case: {rep['flow']}. Velocity pass at {rep['v_min_ms']} m/s; tractive pass at "
             f"Mara's slope, tau {rep['tau_pa']} Pa, K {rep['mara_k']} (Q in m3/s), no floor. "
             "Nothing is regraded or upsized.", "",
             "| By | Name | Velocity pipes | km | Tractive pipes | km | Washing pipes | km |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    a = rep["by_class"]
    lines.append("| **all** | | " + " | ".join(f"**{a[c]['pipes']}** | **{a[c]['km']}**" for c in CLASSES) + " |")
    lines += ["", "Share of length: " + ", ".join(f"{c} {a[c]['pct_length']} %" for c in CLASSES)]
    open(os.path.join(out_dir, "cleansing_table.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, "washing_list.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["PIPE_ID", "CATCH", "TIER", "ROLE", "DN_MM", "LEN_M", "SLOPE_PCT",
                    "Q_LOW_LS", "V_LOW_MS", "S_MARA_PCT", "CONNECTED_2030", "WHY"])
        n = 0
        for i, q in enumerate(pipes):
            if q.get("cleanse") != "washing":
                continue
            n += 1
            sm = q["s_mara"]
            w.writerow([f"P{i + 1:05d}", q.get("catch", ""), TIER_NAME.get(q["tier"], q["tier"]),
                         q["tier"], q["dn_mm"], round(q["len"], 1),
                         round(q["grad_laid"] * 100, 3), round(q["q_low_ls"], 3),
                         round(q["v_low"], 3), "" if sm == float("inf") else round(sm * 100, 3),
                         round(q.get("props_2030_up", 0.0) * connected, 1),
                         "no flow in 2030" if q["q_low_ls"] <= 0 else "below Mara's slope"])
    return n
