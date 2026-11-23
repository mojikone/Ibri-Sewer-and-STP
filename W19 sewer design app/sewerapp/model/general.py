"""The general project: any sewer or stormwater network, the way SewerGEMS holds one. Elements are addressed by stable
string ids, never by row. Loads live only in the load sets.

nodes      id, kind (manhole, wetwell, outfall, storage, junction), x, y, ground, invert, inflow_m3d (added unpeaked)
links      id, kind (conduit, pump), from_node, to_node, length_m, dn_mm, inside_mm, up_inv, dn_inv, transfer
           (a conduit that carries its upstream flow as a transfer, unpeaked: W18's gravity joins), coords (vertices)
catchments id, outlet, area_ha, imperv_pc, width_m, slope_pc, n_imperv, n_perv, gauge, coords (polygon)
settings   see DEFAULT_SETTINGS; load_sets {name: {node id: m3/d}}; rain {gauges, timeseries}; passthrough {section: text}
sections   {link id: {shape box|rect_open|trapezoid, rise_m, span_m, bottom_m, z_left, z_right, n}}: a conduit that is not a
           circle (engine/sections.py); its dn_mm is 0 and inside_mm empty
storage    {node id: {area_m2} or {curve: [[depth m, area m2], ...]}}: a pond, tank or wet well's plan area for the storm
           run (SWMM STORAGE); none given: SWMM's default
pumps      {link id: {q_ls, on_m, off_m, definition}}: a pump's capacity (or its definition, by name, from
           settings.libraries.pumps) and the inlet depths at which it starts and stops
outlets    {link id: {...}}: an orifice (shape circular|rect, d_m or h_m and w_m, cd, offset_m, gated) or a weir (type
           transverse|v_notch, crest_m above the inlet invert, length_m or top_m, height_m, cd) for the storm run
tailwater  {outfall id: level m}: a fixed water level at an outfall (SWMM FIXED)
ppipes     {link id: {method, C, e_mm, n, K, check}}: a pressure pipe's own friction and minor loss (engine/pressure.py)
infil      {link id: rate}: a conduit's own infiltration rate, in the basis of settings.infiltration.method (the project
           rate when absent)"""
import copy, json
from dataclasses import dataclass, field
import numpy as np, pandas as pd

NODE_COLS = ["kind", "x", "y", "ground", "invert", "inflow_m3d"]
LINK_COLS = ["kind", "from_node", "to_node", "length_m", "dn_mm", "inside_mm", "up_inv", "dn_inv", "transfer", "coords"]
CATCH_COLS = ["outlet", "area_ha", "imperv_pc", "width_m", "slope_pc", "n_imperv", "n_perv", "gauge", "coords"]
NODE_KINDS = ("manhole", "wetwell", "outfall", "storage", "junction", "pressure_junction")
LINK_KINDS = ("conduit", "pump", "pressure_pipe", "orifice", "weir")

# PE pressure-pipe sizes, inside diameters of the Ibri model's catalogue (the user may replace them per project)
DEFAULT_CATALOGUE = [[200, 176.4], [250, 220.6], [280, 247.0], [315, 278.0], [355, 313.2], [400, 353.0], [450, 397.0],
                     [500, 441.2], [560, 494.2], [630, 555.8], [710, 626.4], [800, 705.8], [900, 794.2], [1000, 882.4],
                     [1100, 970.6], [1200, 1058.8], [1400, 1235.2], [1600, 1411.8], [1800, 1588.2], [2000, 1764.8]]
DEFAULT_SETTINGS = dict(
    units="SI",
    friction=dict(method="colebrook", ks_mm=1.5, manning_n=0.013, nu=1.141e-6),       # PAM-GUD-203 p24-25, p28
    peaking=dict(method="table", table=[[0.1, 4.66], [0.15, 4.08], [0.2, 3.74], [0.3, 3.33], [0.5, 2.91], [0.75, 2.65],
                                        [1, 2.5], [1.001, 3.56], [1.5, 3.39], [2, 3.28], [3, 3.12], [5, 2.93], [7.5, 2.79],
                                        [10, 2.7], [15, 2.57], [20, 2.48], [30, 2.36], [50, 2.22], [75, 2.11], [100, 2.04],
                                        [150, 1.94], [200, 1.88], [300, 1.79], [500, 1.68], [750, 1.6], [1000, 1.54]],
                 constant=1.0, cutoff=None, pe_per_m3d=None),                          # G201 p71-72 (Peltier, Merrimack)
    infiltration_m3d_per_km=0.72,                                                      # G201 p72
    # how a conduit's infiltration is counted (SewerGEMS's conduit infiltration): "length" uses infiltration_m3d_per_km;
    # the others use `rate`, in m3/d per km per m of inside diameter (length_diameter), per m2 of inside surface
    # (surface_area) or per conduit (count)
    infiltration=dict(method="length", rate=0.0),
    # what a new element gets when it is drawn (SewerGEMS's prototypes); depth = ground - invert
    prototypes=dict(manhole=dict(ground=0.0, depth=1.5), outfall=dict(ground=0.0, depth=1.5), wetwell=dict(ground=0.0, depth=3.0),
                    pressure_junction=dict(ground=0.0, depth=1.5),
                    conduit=dict(dn_mm=None, section=None),
                    catchment=dict(imperv_pc=50.0, width_m=100.0, slope_pc=1.0, n_imperv=0.013, n_perv=0.15)),
    # the project's engineering libraries beyond the size catalogue: named cross-sections a conduit can take
    # unit_loads: [{name, type population|area|discharge|count, rate_m3d per unit, unit, pe people per unit}]
    # patterns: [{name, hourly: 24 multipliers}] for dry-weather runs on SWMM
    libraries=dict(sections=[], pumps=[], unit_loads=[], patterns=[]),
    # the dry-weather flow in the SWMM run: off (a storm run alone) or on with a load set and an hourly pattern
    swmm_dwf=dict(on=False, load_set=None, pattern=None, hours=48),
    # named selections kept with the project (SewerGEMS's selection sets): {name: {table, ids}}
    selection_sets={},
    # the force mains' friction (SewerGEMS's pressure friction method) and the wet-well level the pump lifts from
    pressure=dict(method="hazen", C=130.0, e_mm=0.1, n=0.012, suction="off", use_pumped_flows=False),
    # the steady water profile: "normal" (normal depth in each pipe, the W18 basis) or "gvf" (gradually varied flow from
    # the outfalls up, engine/gvf.py) with a structure loss K v^2/2g at each structure (0: none unless set)
    flow_profile="normal", structure_loss=dict(method="standard", K=0.0),
    # the storm run's infiltration: Horton (SWMM's typical values) or SCS curve number (each catchment's CN)
    storm_infiltration="horton",
    # named sets of calculation options, kept with the project: {name: {setting path: value}}
    calc_option_sets={},
    design=dict(v_min=0.75, v_max=3.0, cover_min=1.3, cover_max=12.0,                  # G203 p26, p27, p33
                dd_limits=[[355, 0.65], [99999, 0.50]],                                # G203 p27 Table 10
                slope_min={"200": 0.005, "250": 0.00375, "315": 0.0027, "400": 0.00205, "500": 0.00155, "600": 0.00125,
                           "700": 0.001, "800": 0.00085, "900": 0.00075},             # G203 p29 Table 11 (mm/m / 1000)
                match="crowns", catalogue=DEFAULT_CATALOGUE),
    design_load="design", check_load=None, self_cleansing_min_dn=200,
)


@dataclass
class Project:
    name: str
    crs: int | None = None                                   # EPSG code, or None for local metres
    nodes: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=NODE_COLS, index=pd.Index([], name="id")))
    links: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=LINK_COLS, index=pd.Index([], name="id")))
    catchments: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=CATCH_COLS, index=pd.Index([], name="id")))
    settings: dict = field(default_factory=lambda: copy.deepcopy(DEFAULT_SETTINGS))
    load_sets: dict = field(default_factory=dict)
    inflow_sets: dict = field(default_factory=dict)   # {load set: {node id: m3/d}} added unpeaked (pattern loads, transfers)
    fixed_flows: dict = field(default_factory=dict)   # {load set: {pump or transfer link id: m3/d}}, held fixed
    rain: dict = field(default_factory=dict)
    passthrough: dict = field(default_factory=dict)
    sections: dict = field(default_factory=dict)
    infil: dict = field(default_factory=dict)
    storage: dict = field(default_factory=dict)
    pumps: dict = field(default_factory=dict)
    ppipes: dict = field(default_factory=dict)
    unit_rows: dict = field(default_factory=dict)   # {load set: {node id: [[unit load name, count], ...]}}
    outlets: dict = field(default_factory=dict)
    tailwater: dict = field(default_factory=dict)
    hydrology: dict = field(default_factory=dict)   # {catchment id: {C, tc_min, cn}}: the rational method and SCS curve number
    controls: list = field(default_factory=list)    # SWMM control rules (pumps, orifices, weirs) for the storm run

    def __setstate__(self, d):                            # a project pickled before a field existed gets its default
        self.__dict__.update(d)
        for k in ("sections", "infil", "storage", "pumps", "ppipes", "unit_rows", "outlets", "tailwater", "hydrology"): self.__dict__.setdefault(k, {})
        self.__dict__.setdefault("controls", [])

    def setting(self, key):
        """A top-level setting, the default filled in for a project made before the key existed."""
        if key not in self.settings and key in DEFAULT_SETTINGS: self.settings[key] = copy.deepcopy(DEFAULT_SETTINGS[key])
        return self.settings.get(key)

    def prototype(self, kind):
        d = copy.deepcopy(DEFAULT_SETTINGS["prototypes"].get(kind, {}))
        d.update((self.settings.get("prototypes") or {}).get(kind) or {})
        return d

    def copy(self):
        return copy.deepcopy(self)

    def catalogue(self):
        c = pd.DataFrame(self.settings["design"]["catalogue"], columns=["nominal_mm", "inside_mm"]).sort_values("nominal_mm")
        return c.reset_index(drop=True)

    def inside_of(self, dn):
        c = self.catalogue().set_index("nominal_mm").inside_mm
        return float(c.get(int(dn), np.nan))

    def dd_limit(self, dn):
        dn = np.asarray(dn, float); out = np.full(dn.shape, np.nan)
        for upto, lim in sorted(self.settings["design"]["dd_limits"], reverse=True):
            out = np.where(dn <= upto, lim, out)
        return out

    def check(self):
        """Structural problems that stop a solve: unknown end nodes, a node with two leaving links, loops."""
        msgs = []
        n = set(self.nodes.index)
        for lid, r in self.links.iterrows():
            for end in (r.from_node, r.to_node):
                if end not in n: msgs.append(f"link {lid}: node {end} does not exist")
        lv = self.links[~self.links.kind.isin(["orifice", "weir"])].from_node.value_counts()     # pond outlets may share a pond
        msgs += [f"node {k} has {v} leaving links (a sewer network is a tree)" for k, v in lv[lv > 1].items()]
        return msgs

    def to_json(self):
        return dict(name=self.name, crs=self.crs, settings=self.settings, load_sets=self.load_sets, inflow_sets=self.inflow_sets, fixed_flows=self.fixed_flows, rain=self.rain,
                    passthrough=self.passthrough, sections=self.sections, infil=self.infil, storage=self.storage, pumps=self.pumps, ppipes=self.ppipes, unit_rows=self.unit_rows, outlets=self.outlets, tailwater=self.tailwater, hydrology=self.hydrology, controls=self.controls)
