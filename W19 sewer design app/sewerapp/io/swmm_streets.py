"""Catch basins in the storm run as SWMM 5.2's streets and inlets (v7, 2026-11-24): dual drainage, so the storm run
captures at each inlet what the rational run does (engine/inlets.py), and the bypass runs down the street.

For a catch basin whose inlet is not full capture and whose street is given (half-width, curb, cross slope, n):
- a street node "<CB>_STR" at the catch basin's ground takes its catchments' runoff (and its additional carryover);
- its gutter to the next catch basin becomes a STREET conduit "<gutter>" from this street node to the next one (or, when
  the next catch basin takes everything, into its structure); with no gutter, a 10 m stub "<CB>_BYP" ends at "<CB>_END",
  an outfall on grade (the bypass leaves, as in the rational run) or a dead end in a sag (it ponds there);
- the inlet "IN_<CB>" sits on that street conduit (SWMM places it at the conduit's downstream end) and sends what it
  captures into the catch basin itself: SWMM's own HEC-22 grate, curb opening, slotted or combination inlet for a
  conventional gutter (checked: the same capture as engine/inlets.py within 0.3 % on HEC-22's examples), or a CUSTOM
  inlet whose curve engine/inlets.py makes (percent capture, maximum capacity, inflow-capture curve; V-shaped and ditch
  gutters, which SWMM's streets do not have).
A catch basin with full capture, or with no street given, takes all its inflow into the pipes (Validate says which).

SWMM's [STREETS] ID Tcrown Hcurb Sx(%) nRoad Hdep Wg Sides; [INLETS] ID GRATE L W type | CURB L H throat | SLOTTED L W
| CUSTOM curve; [INLET_USAGE] link inlet node n %clog Qmax aLocal wLocal placement (street.c, inlet.c, SWMM 5.2.4)."""
import numpy as np

GRATE = {"p50": "P_BAR-50", "p50x100": "P_BAR-50x100", "p30": "P_BAR-30", "curved_vane": "CURVED_VANE", "tilt_bar_45": "TILT_BAR-45",
         "tilt_bar_30": "TILT_BAR-30", "reticuline": "RETICULINE"}
STUB_M = 10.0


def street_ready(d):
    """A catch basin the storm run models with its inlet: not full capture, with its street given."""
    return (d.get("inlet_type") or "full_capture") != "full_capture" and all(d.get(k) for k in ("street_halfwidth_m", "street_curb_m", "road_cross_slope", "n_gutter"))


def _n(v): return f"{float(v):.10g}"


def add(raw, out, units="SI"):
    """Add the streets and inlets of `raw`'s catch basins to the SWMM sections `out` (rows). Returns the catch basins
    modelled (by name) and the curve rows to append to [CURVES]."""
    from sewerapp.engine import inlets as I
    if units != "SI": return {}, []
    N, L = raw.nodes, raw.links
    PN = ((getattr(raw, "props", None) or {}).get("nodes") or {}); PL = ((getattr(raw, "props", None) or {}).get("links") or {})
    cbs = {n: PN.get(n) or {} for n in N.index if N.kind[n] == "catch_basin" and street_ready(PN.get(n) or {})}
    if not cbs: return {}, []
    used = set(N.index) | set(L.index)
    nm = lambda s: s if s not in used else s + "_W19"
    gut = L[L.kind == "gutter"]; out_g = dict(zip(gut.from_node, gut.index))
    for k in ("JUNCTIONS", "OUTFALLS", "CONDUITS", "XSECTIONS", "COORDINATES"): out.setdefault(k, [])
    streets, inl, use, curves, infl = [], [], [], [], []
    xs = {r[0]: r for r in out["XSECTIONS"]}
    for cb, d in cbs.items():
        g0, x, y = float(N.ground[cb]), float(N.x[cb]), float(N.y[cb])
        s_node = nm(f"{cb}_STR"); used.add(s_node)
        out["JUNCTIONS"].append([s_node, _n(g0), _n(d["street_curb_m"]), 0, 0, 0])
        out["COORDINATES"].append([s_node, _n(x), _n(y + 0.5)])
        a = max(float(d.get("gutter_cross_slope") or d["road_cross_slope"]) - float(d["road_cross_slope"]), 0.0) * float(d.get("gutter_width_m") or 0.0)
        st = nm(f"ST_{cb}"); used.add(st)
        streets.append([st, _n(d["street_halfwidth_m"]), _n(d["street_curb_m"]), _n(float(d["road_cross_slope"]) * 100), _n(d["n_gutter"]),
                        _n(a), _n(d.get("gutter_width_m") or 0), 1])
        sag = (d.get("location") or "on_grade") == "in_sag"
        g = out_g.get(cb)
        if g is not None:                                        # the gutter to the next catch basin is the street
            nxt = L.to_node[g]; tgt = f"{nxt}_STR" if nxt in cbs else nxt
            off2 = 0.0 if nxt in cbs else max(float(N.ground[nxt]) - float(N.invert[nxt]), 0.0)
            link = g; out["CONDUITS"].append([g, s_node, tgt, _n(max(float(L.length_m[g]), 1.0)), _n((PL.get(g) or {}).get("n") or d["n_gutter"]), 0, _n(off2), 0, 0])
            out["XSECTIONS"] = [r for r in out["XSECTIONS"] if r[0] != g]
        else:                                                    # no gutter: a stub to where the bypass goes
            link = nm(f"{cb}_BYP"); end = nm(f"{cb}_END"); used.update((link, end))
            ze = g0 - STUB_M * float(d.get("long_slope") or 0.01)
            if sag: out["JUNCTIONS"].append([end, _n(ze), _n(d["street_curb_m"]), 0, 0, 0])
            else: out["OUTFALLS"].append([end, _n(ze), "FREE", "NO"])
            out["COORDINATES"].append([end, _n(x + STUB_M), _n(y + 0.5)])
            out["CONDUITS"].append([link, s_node, end, _n(STUB_M), _n(d["n_gutter"]), 0, 0, 0, 0])
        out["XSECTIONS"].append([link, "STREET", st])
        # the inlet
        iid = nm(f"IN_{cb}"); used.add(iid); t = d.get("inlet_type"); qmax = 0.0; clog = 0.0
        conv = (d.get("gutter_shape") or "conventional") == "conventional"
        if t == "catalog" and conv:
            c = d["inlet_class"]; clog = float(d.get("clogging_pc") or 0.0)
            if c in ("grate", "combination"):
                own = d.get("opening_ratio")
                if own and abs(float(own) - I.OPENING[d["grate_type"]]) > 1e-9:       # an opening ratio of its own: SWMM's generic grate
                    inl.append([iid, "GRATE", _n(d["grate_length_m"]), _n(d["grate_width_m"]), "GENERIC", _n(own), _n(I.splash_velocity(d["grate_type"], float(d["grate_length_m"])))])
                else: inl.append([iid, "GRATE", _n(d["grate_length_m"]), _n(d["grate_width_m"]), GRATE[d["grate_type"]]])
            if c in ("curb", "combination"): inl.append([iid, "CURB", _n(d["curb_length_m"]), _n(d["curb_height_m"]), (d.get("throat") or "vertical").upper()])
            if c == "slot": inl.append([iid, "SLOTTED", _n(d["slot_length_m"]), _n(d["slot_width_m"])])
        else:                                                    # a curve made here: approach flow to captured flow, or depth to capacity in a sag
            cid = nm(f"IC_{cb}"); used.add(cid)
            if t == "catalog" and sag:
                g_ = I.Gutter(d); pts = [[0.0, 0.0]] + [[h, I.sag_capacity(h, d, g_)[0] * (1 - float(d.get("clogging_pc") or 0) / 100)] for h in np.linspace(0.01, float(d["street_curb_m"]) * 2, 20)]
                typ = "RATING"
            else:
                if t == "percent_capture": f = lambda q: q * float(d.get("capture_pc", 100.0)) / 100.0
                elif t == "max_capacity": f = lambda q: q; qmax = float(d.get("q_max_ls") or 0.0) / 1000.0
                elif t == "rating_curve":
                    r = sorted(d.get("rating") or [[0, 0], [1, 1]]); f = lambda q: min(q, float(np.interp(q * 1000, [a_ for a_, b_ in r], [b_ for a_, b_ in r])) / 1000.0)
                else: f = lambda q: I.capture(q, d)[0]
                qs = [0.0] + list(np.geomspace(0.001, 20.0, 40))
                pts = [[q, f(q)] for q in qs]
                typ = "DIVERSION"
            for k_, (a_, b_) in enumerate(pts): curves.append([cid, typ if k_ == 0 else "", _n(a_), _n(b_)])
            inl.append([iid, "CUSTOM", cid])
        use.append([link, iid, cb, 1, _n(clog), _n(qmax), 0, 0, "ON_SAG" if sag else "ON_GRADE"])
        if d.get("carryover_ls"): infl.append([s_node, "FLOW", '""', "FLOW", "1.0", "1.0", _n(float(d["carryover_ls"]) / 1000.0)])
    for r in out.get("SUBCATCHMENTS") or []:                     # the catchments' runoff reaches the street
        if r[2] in cbs: r[2] = f"{r[2]}_STR"
    out["STREETS"], out["INLETS"], out["INLET_USAGE"] = streets, inl, use
    if infl: out.setdefault("INFLOWS", []).extend(infl)
    return {cb: dict(inlet=f"IN_{cb}") for cb in cbs}, curves


def usage(inp_text):
    """{catch basin: (street link, inlet)} from a written file's [INLET_USAGE]."""
    out, on = {}, False
    for line in inp_text.splitlines():
        s = line.strip()
        if s.startswith("["): on = s.upper() == "[INLET_USAGE]"; continue
        if on and s and not s.startswith(";"):
            p = s.split()
            if len(p) >= 3: out[p[2]] = (p[0], p[1])
    return out


def read_report(rpt_text):
    """SWMM's Street Flow Summary: per street conduit with an inlet, its peak flow, spread and depth, and the inlet's
    capture. Returns {inlet id: row}."""
    m = rpt_text.find("Street Flow Summary")
    if m < 0: return {}
    out = {}
    for line in rpt_text[m:].splitlines()[7:]:
        p = line.split()
        if not p: break
        if len(p) >= 12 and p[5] in ("ON-GRADE", "ON-SAG"):
            out[p[4]] = dict(street=p[0], q_peak_ls=float(p[1]) * 1000, spread_m=float(p[2]), depth_m=float(p[3]), location=p[5].lower().replace("-", "_"),
                             count=int(p[6]), capture_peak_pc=float(p[7]), capture_avg_pc=float(p[8]), bypass_freq_pc=float(p[9]),
                             capture_peak_per_inlet_ls=float(p[11]) * 1000, bypass_peak_ls=float(p[12]) * 1000 if len(p) > 12 else None)
    return out
