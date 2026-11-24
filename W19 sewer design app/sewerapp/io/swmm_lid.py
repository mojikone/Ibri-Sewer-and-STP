"""LID: low impact development controls on catchments (v7, 2026-11-24), SewerGEMS's LID element, run on EPA SWMM 5.2.

A project's LID controls (settings.libraries.lid) are SWMM's: a type and its layers' parameters, entered by the engineer
(no value is assumed); a catchment's LID units (its props: lid_usage rows) say how many of which control, their area and
width, and what share of the catchment's runoff they treat. Format and checks: SWMM 5.2.4's lid.c (public domain):

[LID_CONTROLS]  Name Type;  Name SURFACE StorHt VegVolFrac Roughness Slope% SideSlope;  Name SOIL Thick Porosity FieldCap
WiltPt Ksat Kslope Suction;  Name PAVEMENT Thick VoidRatio FracImperv Perm ClogFactor;  Name STORAGE Thick VoidRatio Ksat
ClogFactor;  Name DRAIN Coeff Expon Offset Delay(h);  Name DRAINMAT Thick VoidFrac Roughness.  SI file: depths and
thicknesses in mm, conductivities in mm/h.
[LID_USAGE]  Subcatch LID Number Area(m2 each) Width(m) InitSat% FromImp% ToPerv(0/1) RptFile DrainTo FromPerv%."""

TYPES = {"BC": "Bio-retention cell", "RG": "Rain garden", "GR": "Green roof", "IT": "Infiltration trench", "PP": "Permeable pavement",
         "RB": "Rain barrel", "VS": "Vegetative swale", "RD": "Rooftop disconnection"}
# each layer's parameters: (key, label, unit)
LAYERS = {
    "surface": [("stor_mm", "Berm height", "mm"), ("veg_frac", "Vegetation volume fraction", ""), ("n", "Surface roughness (Manning n)", ""),
                ("slope_pc", "Surface slope", "%"), ("side_slope", "Swale side slope (run/rise)", "")],
    "soil": [("thick_mm", "Thickness", "mm"), ("porosity", "Porosity", ""), ("field_cap", "Field capacity", ""), ("wilt_pt", "Wilting point", ""),
             ("ksat_mmh", "Conductivity", "mm/h"), ("kslope", "Conductivity slope", ""), ("suction_mm", "Suction head", "mm")],
    "pavement": [("thick_mm", "Thickness", "mm"), ("void_ratio", "Void ratio", ""), ("frac_imperv", "Impervious surface fraction", ""),
                 ("perm_mmh", "Permeability", "mm/h"), ("clog", "Clogging factor", "")],
    "storage": [("thick_mm", "Thickness (barrel height)", "mm"), ("void_ratio", "Void ratio", ""), ("ksat_mmh", "Seepage rate", "mm/h"), ("clog", "Clogging factor", "")],
    "drain": [("coeff", "Flow coefficient", ""), ("expon", "Flow exponent", ""), ("offset_mm", "Offset", "mm"), ("delay_h", "Drain delay (rain barrels)", "h")],
    "drainmat": [("thick_mm", "Thickness", "mm"), ("void_frac", "Void fraction", ""), ("n", "Roughness (Manning n)", "")],
}
NEEDS = {"BC": ["surface", "soil", "storage", "drain"], "RG": ["surface", "soil"], "GR": ["surface", "soil", "drainmat"],
         "IT": ["surface", "storage", "drain"], "PP": ["surface", "pavement", "storage", "drain"], "RB": ["storage", "drain"],
         "VS": ["surface"], "RD": ["surface", "drain"]}
OPTIONAL = {"RG": ["storage"], "PP": ["soil"]}
USAGE_COLS = ["lid", "number", "area_m2", "width_m", "init_sat_pc", "from_imp_pc", "to_perv", "from_perv_pc"]


def check_library(lib):
    """The LID controls as SWMM 5.2 checks them (lid.c validateLidProc). Raises ValueError with what is wrong."""
    names = set()
    for c in lib or []:
        nm = str(c.get("name") or "").strip()
        if not nm or " " in nm: raise ValueError("each LID control needs a name without spaces")
        if nm in names: raise ValueError(f"two LID controls are called {nm}")
        names.add(nm); t = c.get("type")
        if t not in TYPES: raise ValueError(f"{nm}: the type is one of {', '.join(TYPES)}")
        for layer in NEEDS[t]:
            vals = c.get(layer) or {}
            miss = [lab for k, lab, _ in LAYERS[layer] if vals.get(k) is None and not (layer == "surface" and k == "side_slope" and t != "VS")
                    and not (layer == "drain" and k == "delay_h")]
            if miss: raise ValueError(f"{nm} ({TYPES[t]}): the {layer} layer needs {', '.join(miss)}")
            if any(v is not None and float(v) < 0 for v in vals.values()): raise ValueError(f"{nm}: the {layer} layer's values are 0 or more")
        s = c.get("soil") or {}
        if "soil" in NEEDS[t] and not (float(s.get("porosity", 0)) > float(s.get("field_cap", 0)) > float(s.get("wilt_pt", -1)) >= 0 and float(s.get("ksat_mmh", 0)) > 0):
            raise ValueError(f"{nm}: the soil needs porosity > field capacity > wilting point, and a conductivity above 0")
        if float((c.get("surface") or {}).get("veg_frac", 0) or 0) >= 1: raise ValueError(f"{nm}: the vegetation volume fraction is below 1")
        if t == "VS" and not (float((c.get("surface") or {}).get("n", 0)) * float((c.get("surface") or {}).get("slope_pc", 0)) > 0):
            raise ValueError(f"{nm}: a swale needs its roughness and slope")
        if t == "PP" and not float((c.get("pavement") or {}).get("thick_mm", 0)) > 0: raise ValueError(f"{nm}: permeable pavement needs its thickness")
        if t in ("BC", "RG", "GR") and not float((c.get("soil") or {}).get("thick_mm", 0)) > 0: raise ValueError(f"{nm}: the soil layer needs its thickness")
        if t == "GR" and not float((c.get("drainmat") or {}).get("thick_mm", 0)) > 0: raise ValueError(f"{nm}: a green roof needs its drainage mat")
        if t == "IT" and not float((c.get("storage") or {}).get("thick_mm", 0)) > 0: raise ValueError(f"{nm}: an infiltration trench needs its storage layer")
    return lib


def check_usage(rows, lib_names=None):
    out = []
    for r in rows or []:
        if len(r) < 7: raise ValueError("an LID unit row: LID, number, area each (m2), width (m), initially saturated %, % impervious treated, to pervious (0/1), % pervious treated")
        name = str(r[0]).strip()
        if lib_names is not None and name not in lib_names: raise ValueError(f"no LID control {name} (Components > LID controls)")
        try: v = [float(x) if x not in (None, "") else 0.0 for x in (list(r[1:8]) + [0.0] * 7)[:7]]
        except (TypeError, ValueError): raise ValueError("an LID unit row's values are numbers")
        if v[0] < 0 or v[0] != int(v[0]): raise ValueError("the number of LID units is a whole number")
        if any(x < 0 for x in v) or v[3] > 100 or v[4] > 100 or v[6] > 100: raise ValueError("LID unit percentages are 0-100, the rest 0 or more")
        out.append([name] + v)
    return out


def sections(p):
    """The [LID_CONTROLS] and [LID_USAGE] rows of project p (only the controls a catchment uses)."""
    lib = {c["name"]: c for c in ((p.settings.get("libraries") or {}).get("lid") or [])}
    PC = ((getattr(p, "props", None) or {}).get("catchments") or {})
    usage = [(cid, r) for cid, d in PC.items() if cid in p.catchments.index for r in (d.get("lid_usage") or []) if r[0] in lib and r[1] > 0]
    used = sorted({r[0] for _, r in usage}); ctl = []
    for nm in used:
        c = lib[nm]; t = c["type"]; ctl.append([nm, t])
        for layer in NEEDS[t] + [x for x in OPTIONAL.get(t, []) if c.get(x)]:
            vals = c.get(layer) or {}
            row = [vals.get(k) if vals.get(k) is not None else 0.0 for k, _, _ in LAYERS[layer]]
            ctl.append([nm, layer.upper()] + [f"{float(x):.10g}" for x in row])
    use = [[cid, r[0], int(r[1]), f"{r[2]:.10g}", f"{r[3]:.10g}", f"{r[4]:.10g}", f"{r[5]:.10g}", 1 if r[6] > 0 else 0, "*", "*", f"{r[7]:.10g}"] for cid, r in usage]
    return ctl, use
