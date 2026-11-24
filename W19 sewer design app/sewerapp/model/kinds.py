"""Every element kind the app draws, the way SewerGEMS holds them (v7, 2026-11-24), and each kind's own fields.

The engineer, 2026-11-24: "yes add them [catch basins], but carefully, and ensure you've assessed the properties,
attributes, calculations etc. very well from SewerGEMS. Add any other remaining elements you've missed."

SewerGEMS 10.4 declares 31 element types (docs/SEWERGEMS_INVENTORY.md). The app draws every network element among them:

  structures  manhole, catch basin, outfall, headwall, transition, cross section, wet well, pond (storage), junction,
              pressure junction, air valve, property connection, tap
  links       conduit, channel, gutter, lateral, pressure pipe, pump, orifice and weir (a pond outlet structure's parts)
  areas       catchment

How each kind takes part in the calculations (engine_view in engine/steady.py turns them into the engine's base kinds):
  catch basin, transition, cross section, property connection: a gravity structure (as a manhole); a catch basin's
      inlet captures surface flow in the rational run (engine/inlets.py, HEC-22), what it bypasses goes down its gutter
  headwall: a culvert end; the outfall of its network when nothing leaves it (its own boundary condition), else a
      gravity structure
  air valve: a pressure junction on a force main (the steady pressure run does not model air)
  tap: where a lateral joins a conduit; the lateral's flow enters that conduit (at its upstream structure)
  channel, lateral: gravity links (a channel with its open section, a lateral with its own bore); the design leaves
      both as they are
  gutter: surface flow between catch basins: the bypassed flow of the inlet at its start goes to the inlet at its end;
      no part of the pipe network (left out of the steady, pressure and SWMM runs)

Each kind's own fields (beyond the node and link tables' columns) live in Project.props[table][id], set with the
edit op set_props and checked here. Field names follow SewerGEMS's (docs/INLETS_HEC22.md); units are SI."""

NODE_KINDS = ("manhole", "wetwell", "outfall", "storage", "junction", "pressure_junction", "catch_basin", "transition",
              "cross_section", "headwall", "air_valve", "property_connection", "tap")
LINK_KINDS = ("conduit", "pump", "pressure_pipe", "orifice", "weir", "channel", "gutter", "lateral")

GRAVITY_AS_MANHOLE = ("catch_basin", "transition", "cross_section", "property_connection")
PRESSURE_AS_JUNCTION = ("air_valve",)
LINKS_AS_CONDUIT = ("channel", "lateral")
SURFACE_LINKS = ("gutter",)
NOT_DESIGNED = ("channel", "lateral", "gutter")

GRATES = ("p50", "p50x100", "p30", "curved_vane", "tilt_bar_45", "tilt_bar_30", "reticuline")

# (key, label, type, unit, options or None, group)
# types: num (a number, 0 or more unless noted), pct (0-100), choice, bool, text, table (rows of numbers)
_INLET = [
    ("inlet_type", "Inlet type", "choice", "", ("full_capture", "percent_capture", "max_capacity", "rating_curve", "catalog"), "Inlet"),
    ("capture_pc", "Capture efficiency", "pct", "%", None, "Inlet"),
    ("q_max_ls", "Flow (maximum in)", "num", "L/s", None, "Inlet"),
    ("rating", "Inflow-capture curve (inflow, captured)", "table", "L/s", None, "Inlet"),
    ("location", "Inlet location", "choice", "", ("on_grade", "in_sag"), "Inlet"),
    ("inlet_class", "Inlet (catalogue type)", "choice", "", ("grate", "curb", "combination", "slot"), "Inlet"),
    ("grate_type", "Grate type", "choice", "", GRATES, "Inlet"),
    ("grate_length_m", "Grate length", "num", "m", None, "Inlet"),
    ("grate_width_m", "Grate width", "num", "m", None, "Inlet"),
    ("opening_ratio", "Grate opening ratio", "num", "", None, "Inlet"),
    ("clogging_pc", "Clogging factor", "pct", "%", None, "Inlet"),
    ("curb_length_m", "Curb opening length", "num", "m", None, "Inlet"),
    ("curb_height_m", "Curb opening height", "num", "m", None, "Inlet"),
    ("throat", "Curb throat", "choice", "", ("vertical", "inclined", "horizontal"), "Inlet"),
    ("slot_length_m", "Slot length", "num", "m", None, "Inlet"),
    ("slot_width_m", "Slot width", "num", "m", None, "Inlet"),
    ("long_slope", "Longitudinal slope (inlet)", "num", "m/m", None, "Gutter"),
    ("n_gutter", "Manning's n (inlet)", "num", "", None, "Gutter"),
    ("gutter_shape", "Gutter shape", "choice", "", ("conventional", "v_shaped", "trapezoidal", "parabolic", "irregular"), "Gutter"),
    ("road_cross_slope", "Road cross slope", "num", "m/m", None, "Gutter"),
    ("gutter_cross_slope", "Gutter cross slope", "num", "m/m", None, "Gutter"),
    ("gutter_width_m", "Gutter width", "num", "m", None, "Gutter"),
    ("curb_cross_slope", "Curb cross slope (V-shaped)", "num", "m/m", None, "Gutter"),
    ("ditch_bottom_m", "Bottom width (ditch)", "num", "m", None, "Gutter"),
    ("side_slope_l", "Left side slope (H:1V)", "num", "", None, "Gutter"),
    ("side_slope_r", "Right side slope (H:1V)", "num", "", None, "Gutter"),
    ("parabola_height_m", "Height (parabolic gutter, curb to crown)", "num", "m", None, "Gutter"),
    ("parabola_width_m", "Width (parabolic gutter, curb to crown)", "num", "m", None, "Gutter"),
    ("gutter_section", "Irregular section (station from the curb, relative elevation)", "table", "m", None, "Gutter"),
    ("street_halfwidth_m", "Street half-width, curb to crown (storm run)", "num", "m", None, "Gutter"),
    ("street_curb_m", "Curb height (storm run)", "num", "m", None, "Gutter"),
    ("max_gutter_depth_m", "Maximum gutter depth", "num", "m", None, "Design"),
    ("max_spread_m", "Maximum spread", "num", "m", None, "Design"),
    ("design_opening", "Design inlet opening?", "bool", "", None, "Design"),
    ("design_lengths", "Design lengths (m, comma-separated)", "text", "m", None, "Design"),
    ("min_efficiency_pc", "Minimum efficiency on grade", "pct", "%", None, "Design"),
    ("carryover_ls", "Flow (additional carryover)", "num", "L/s", None, "Flows"),
]
_STRUCTURE = [
    ("structure", "Structure type", "choice", "", ("circular", "box"), "Structure"),
    ("diameter_m", "Diameter", "num", "m", None, "Structure"),
    ("box_length_m", "Length (box)", "num", "m", None, "Structure"),
    ("box_width_m", "Width (box)", "num", "m", None, "Structure"),
]
FIELDS = {
    "catch_basin": _STRUCTURE + _INLET,
    "manhole": _STRUCTURE,
    "headwall": [("boundary", "Boundary condition", "choice", "", ("free", "fixed"), "Boundary"),
                 ("tailwater_m", "Tailwater elevation (fixed)", "num", "m", None, "Boundary"),
                 ("inlet_description", "Culvert inlet description", "text", "", None, "Culvert")],
    "transition": [("transition_length_m", "Transition length", "num", "m", None, "Structure")],
    "cross_section": [("section", "Cross section", "choice", "", ("trapezoidal",), "Section"),
                      ("bottom_m", "Bottom width", "num", "m", None, "Section"), ("depth_m", "Channel depth", "num", "m", None, "Section"),
                      ("side_slope_l", "Left side slope (H:1V)", "num", "", None, "Section"), ("side_slope_r", "Right side slope (H:1V)", "num", "", None, "Section"),
                      ("n", "Manning's n", "num", "", None, "Section")],
    "air_valve": [("treat_as_junction", "Treat air valve as junction", "bool", "", None, "Air valve")],
    "tap": [("link", "Tapped conduit", "text", "", None, "Tap"), ("connects_at", "Connects at", "choice", "", ("invert_to_center", "invert_to_crown"), "Tap"),
            ("offset_m", "Elevation offset", "num", "m", None, "Tap")],
    "gutter": [("gutter_shape", "Gutter shape", "choice", "", ("from_start_inlet", "conventional", "v_shaped", "trapezoidal"), "Gutter"),
               ("n", "Manning's n", "num", "", None, "Gutter"), ("road_cross_slope", "Road cross slope", "num", "m/m", None, "Gutter"),
               ("gutter_cross_slope", "Gutter cross slope", "num", "m/m", None, "Gutter"), ("gutter_width_m", "Gutter width", "num", "m", None, "Gutter")],
    "lateral": [("material", "Material", "text", "", None, "Lateral"), ("n", "Manning's n", "num", "", None, "Lateral")],
    "channel": [("material", "Material", "text", "", None, "Channel")],
    "pump": [("station", "Pump station", "text", "", None, "Station")],
    # a culvert (SewerGEMS's Is Culvert?): its HDS-5 inlet type (SWMM's culvert code), entrance loss, allowable headwater
    "conduit": [("is_culvert", "Is culvert?", "bool", "", None, "Culvert"), ("culvert_code", "Inlet (HDS-5 type)", "choice", "", tuple(str(k) for k in range(1, 58)), "Culvert"),
                ("ke", "Entrance loss coefficient Ke", "num", "", None, "Culvert"), ("max_headwater_m", "Allowable headwater depth", "num", "m", None, "Culvert")],
}


def _labels():
    from sewerapp.engine.culverts import TABLE
    return {"culvert_code": {str(k): f"{k}: {v[5]}" for k, v in TABLE.items()}}
# a new element's values when it is drawn (SewerGEMS's defaults for a new catch basin: full capture, on grade)
DEFAULTS = {"catch_basin": dict(inlet_type="full_capture", location="on_grade", structure="circular"),
            "headwall": dict(boundary="free"), "tap": dict(connects_at="invert_to_center", offset_m=0.0),
            "gutter": dict(gutter_shape="from_start_inlet"), "air_valve": dict(treat_as_junction=True)}


def check_props(kind, values):
    """values cleaned and checked against the kind's fields; a value None removes the field. Raises ValueError."""
    spec = {f[0]: f for f in FIELDS.get(kind, [])}
    if not spec: raise ValueError(f"{kind} has no fields of its own")
    out = {}
    for k, v in (values or {}).items():
        if k not in spec: raise ValueError(f"{kind} has no field {k}; its fields: {', '.join(spec)}")
        _, label, typ, unit, opts, _g = spec[k]
        if v is None or v == "": out[k] = None; continue
        if typ in ("num", "pct"):
            try: v = float(v)
            except (TypeError, ValueError): raise ValueError(f"{label} is a number")
            if v < 0 or (typ == "pct" and v > 100): raise ValueError(f"{label} must be {'0-100' if typ == 'pct' else '0 or more'}")
            if k in ("n", "n_gutter") and not v > 0: raise ValueError(f"{label} must be above 0")
        elif typ == "choice":
            if v not in opts: raise ValueError(f"{label}: one of {', '.join(opts)}")
        elif typ == "bool": v = bool(v)
        elif typ == "text": v = str(v)[:200]
        elif typ == "table":
            try: v = [[float(a), float(b)] for a, b in v]
            except Exception: raise ValueError(f"{label}: rows of two numbers")
            if k == "rating" and any(a < 0 or b < 0 or b > a + 1e-9 for a, b in v): raise ValueError(f"{label}: the captured flow is 0 to the inflow")
            if k == "gutter_section" and (len(v) < 3 or any(a < 0 for a, _ in v)): raise ValueError(f"{label}: three rows or more, stations 0 or more")
            v = sorted(v)
        out[k] = v
    return out


def schema():
    """The fields per kind, for the editor's Properties."""
    L = _labels()
    return {k: [dict(key=f[0], label=f[1], type=f[2], unit=f[3], options=list(f[4]) if f[4] else None, group=f[5], **({"labels": L[f[0]]} if f[0] in L else {})) for f in v] for k, v in FIELDS.items()}
