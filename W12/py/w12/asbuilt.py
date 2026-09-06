"""
W12 — AS-BUILT TARGETS
=======================

What NAMA actually built in Ibri, measured from the asset shapefiles, turned into
numeric targets a W12 stage can check its own design against.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
not import from W8/py/sewnet, W10/py or W11a/py.  It has no w12 sibling imports
either, so it can be run before the rest of the package exists.

    from w12.asbuilt import AsBuilt, observe_design

    ab = AsBuilt()                    # loads, filters, measures (cached)
    ab.targets_frame()                # every target with band, basis and source
    obs = observe_design(reaches, nodes, fields=...)   # same observables, new design
    ab.check(obs)                     # PASS / HIGH / LOW table

    python W12/py/w12/asbuilt.py            # prints the tables
    python W12/py/w12/asbuilt.py --csv DIR  # also writes targets/evidence CSVs

EVERY NUMBER IS EITHER MEASURED OR CITED
----------------------------------------
`basis` on each target says which:

    MEASURED    computed here from NAMA's shapefile; `source` names the field
    GUIDELINE   quoted from the PDF; `source` gives the page (G203-p29 Tab 11)
    ASSUMPTION  a project decision; `source` names who decided and when

Guideline constants below were read back from the source PDFs on 2026-09-03
(`Data/PAM-GUD-203*.pdf`, `Data/PAM-GUD-201*.pdf`), not from memory.

THE DATASET, AND HOW IT LIES
----------------------------
`SEWERLINE_IBRI.shp` carries its own warning in every REMARKS cell: *"Data is not
reliable and must be used only for reference purpose"*.  Four traps, all handled here:

 1. STATUS mixes networks.  3,267 rows are `Ex` (built), 129 are `Design`
    (SUREKHA proposals, 202.7 km of them).  Filter BEFORE quoting any length.
 2. Two rows are SCHEMATIC, not pipe: L012750 (10,469 m, 317 m per vertex) and
    L012751 (5,648 m, 565 m per vertex).  Both end at `5A-1-FL-STP` — they are the
    force main drawn into the gravity layer.  Excluded by rule, and the rule is a
    measurement (m per vertex), not a hard-coded id list.
 3. `N_DIAMETER`, `UP_PIP_DEP`, `DS_PIP_DEP`, `SLOPE`, `P_CONDITIO`, `GROUND_TYP`,
    `MCLASS`, `BED_MATERI`, `LINING_TYP`, `FLOOD_PROT`, `WATER_TABL` are zero or
    null on EVERY built row.  A conclusion has already been drawn once in this
    project from a field that was always zero.  The real diameter is `OUT_DIAMET`.
 4. Levels exist on 2,142 of 3,265 built pipes (65.6 %, 63.20 of 95.45 km).  The
    split is by package: 5A-2/3/4/5 are complete, 5A-1 has none.  Every
    level-derived target here is measured on that 63.20 km and says so.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from functools import cached_property
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# PATHS.  W12 inherits W11b's layout and revises it.  Override with W12_ROOT,
# or by passing paths= to AsBuilt().
# --------------------------------------------------------------------------------------

def _project_root() -> str:
    """.../2621 Ibri Sewer STP — found by walking up from this file."""
    env = os.environ.get("W12_PROJECT_ROOT")
    if env:
        return env
    here = os.path.abspath(os.path.dirname(__file__))       # .../Hydraulic/Claude/W12/py/w12
    return os.path.abspath(os.path.join(here, "..", "..", "..", "..", ".."))


def default_paths() -> dict:
    R = _project_root()
    j = lambda *p: os.path.join(R, *p)
    return {
        "root": R,
        "sewerline": j("Data", "Received", "09-RECEIVED", "NAMA", "IBRI", "WW", "SHIP",
                       "SEWERLINE_IBRI.shp"),
        "forceline": j("Data", "Received", "09-RECEIVED", "NAMA", "IBRI", "WW", "SHIP",
                       "FORCELINE_IBRI.shp"),
        "roads": j("Hydraulic", "SHP", "Road centerline 2", "Road_Centercline.shp"),
        "hazard50": j("Data", "04 Lekhuwair", "Hazard_T50y.tif"),
        "plot_loads": j("Hydraulic", "Claude", "W10", "shp", "W10_plot_loads.gpkg"),
        "ele_accounts": j("Hydraulic", "Claude", "W4", "shp", "ELE_accounts.shp"),
    }


CRS_EPSG = 32640          # UTM 40N, the project CRS for every layer used here

# --------------------------------------------------------------------------------------
# GUIDELINE CONSTANTS — quoted from the source PDFs, page by page, 2026-09-03.
# Nothing in this block may be changed without re-reading the page it cites.
# --------------------------------------------------------------------------------------

# G203 p22 Table 6 "Material for Commonly Used non-metallic sewer pipes"
G203_P22_OD_RIDER_MIN_MM = 160        # "Rider Sewer, Property Connection  OD 160 mm (minimal)"
G203_P22_OD_LATERAL_MIN_MM = 200      # "Lateral Sewer  OD 200 mm (minimal)"
G203_P22_LATERAL_MAX_LEN_M = 45       # "Maximum Length 45 m"
G203_P22_OD_MAIN_MIN_MM = 200         # "Main sewer  OD 200 mm (minimal) to 300 mm"

# G203 p23 Table 8 "Roughness Coefficient for Commonly Used Non-Metallic Pipes"
G203_P23_MANNING_N_PVC = (0.009, 0.011)     # "Polyvinyl chloride (PVC) ... 0.009 - 0.011"

# G203 p26 4.2.2.1 self-cleansing velocity
G203_P26_V_MIN_MS = 0.75              # "shall be above 0.75 m/s at peak flow"
G203_P26_V_PREFERRED_MS = 0.90        # "with preferred velocity at 0.90m/s"

# G203 p27 4.2.2.2 / Table 10
G203_P27_V_MAX_MS = 3.0               # "shall not exceed 3 m/s at the design depth of flow"
G203_P27_TAB10_DD_LE350 = 0.65        # "Pipe Diameter up to 350 mm   0.65"
G203_P27_TAB10_DD_GT350 = 0.50        # "Pipe Diameter > 350 mm       0.50"

# G203 p27 4.2.2.1 Mara/Sleigh/Taylor  Smin = K * tau^1.23 * Q^-0.461
G203_P27_MARA_K_LS = 5.5e-3           # "Q = Flow (L/s) and K = 5.5 x 10-3"
G203_P27_MARA_K_M3S = 2.33e-4         # "Q = Flow (m3/s) and K = 2.33 x 10-4"

# G203 p28 4.2.4 Colebrook-White
G203_P28_KS_MM = 1.5                  # "using a k_s value of 1.5 mm for all pipe sizes"

# G203 p29 Table 11 "Minimum Sewer Line Gradient" (mm/m), keyed by sewer diameter (mm).
# The table starts at 200 mm; it says nothing about 150 mm.
G203_P29_TAB11_MIN_GRADIENT_MM_M = {
    200: 5.00, 250: 3.75, 315: 2.70, 400: 2.05, 500: 1.55,
    600: 1.25, 700: 1.00, 800: 0.85, 900: 0.75,
}

# G203 p30 4.4 manholes, drops, spacing
G203_P30_BACKDROP_TRIGGER_M = 0.60    # "require the use of a backdrop when the difference
                                      #  in invert elevations exceeds 600 mm"
G203_P30_BACKDROP_MAX_M = 2.00        # "The maximum backdrop height should be of 2 m.
                                      #  Beyond this limit, specific devices like vortex
                                      #  drop shafts should be used."
G203_P30_INLET_ANGLE_MIN_DEG = 90     # "No inlet pipe at manholes shall have an angle
                                      #  less than 90 deg to the direction of flow"
G203_P30_TAB12_MAX_MH_SPACING_M = [   # (dia_lo, dia_hi, max spacing m)
    (200, 315, 100), (350, 900, 120), (1000, 1400, 150), (1401, 100000, 200),
]

# G203 p30 4.4.1(i)(a) restricted locations
G203_P30_WADI_RULE = ("Locating pipelines and associated chambers in wadis or areas "
                      "subject to washout during heavy storms must be avoided")

# G203 p33 4.6.3 Pipe Laying
G203_P33_MIN_COVER_M = 1.30           # "minimum depth for sewer pipes shall be 1.3 m
                                      #  to the crown of the pipe"
G203_P33_MIN_COVER_PROTECTED_M = 0.50 # "minimum cover above the pipe and its protection
                                      #  shall be 0.5 m" (with concrete protection)
G203_P33_MAX_COVER_M = (10.0, 12.0)   # "recommended maximum cover ... approximately 10-12m"

# G201 p71 7.4.2 / p72 peaking, p72 7.4.3 infiltration
G201_P71_MERRIMACK = (2.65, 0.879)    # Qpdf = 2.65 * Qadf^0.879, both Ml/d, >100 properties
G201_P72_PELTIER = (1.5, 1.0)         # PfWW = 1.5 + 1/sqrt(Qadf in L/s)
G201_P72_PF_CAP_RECOMMENDED = 5.0     # "recommended that the hourly peak factor should
                                      #  not exceed 5.0" — a recommendation, not a limit
G201_P72_INFIL_EXISTING_INLAND = 0.10 # existing inland network: 10 % of WW flow
G201_P72_INFIL_NEW_L_D_KM = 720.0     # new networks: 720 L/d per km of sewer

# --------------------------------------------------------------------------------------
# PROJECT ASSUMPTIONS — decided here, not in a guideline.  Each carries its decision date.
# --------------------------------------------------------------------------------------

A_TAU_PA = 1.0
A_TAU_NOTE = ("tractive stress tau = 1.0 Pa. Engineer's decision 2026-09-03, GAP-9 open. "
              "SHALLOWER SLOPES, so shallower pipes and fewer pumps. If NWS return 2.0 the "
              "required gradient rises 2.35x (2^1.23) and every depth changes.")

A_WADI_CLASSES = (4, 5, 6)
A_WADI_NOTE = ("'wadi ground' = classes 4-6 of the 50-year hazard grid (AR&R hazard classes, "
               "class 4 ~ 1.2 m of water), standing in for the guideline's washout/scour "
               "criterion. PROJECT ASSUMPTION beside GAP-9, not a guideline threshold.")

A_HAZARD_NODATA_DRY = True
A_HAZARD_NODATA_NOTE = ("flood no-data is DRY HIGH GROUND, not 'untested'. Engineer's "
                        "decision 2026-09-03. Flow runs in the wadis, so the grid covers "
                        "the wadis and its absence means high ground.")

A_DUAL_BUFFER_M = 4.0
A_DUAL_NOTE = ("a pipe 'runs along a dual carriageway' if it lies within 4.0 m of a "
               "`dual`=1 centreline. 4 m ~ one lane half-width; W7 used the same figure, "
               "so the 0.1 % on record is reproducible. PROJECT ASSUMPTION.")

A_SCHEMATIC_M_PER_VERTEX = 100.0
A_SCHEMATIC_NOTE = ("a row averaging more than 100 m between vertices is SCHEMATIC, not "
                    "surveyed pipe. Two rows qualify (317 and 565 m per vertex); the next "
                    "worst real pipe is 65 m per vertex, so the rule is not marginal.")

A_LOAD_RADIUS_M = 60.0
A_LOAD_NOTE = ("a plot is served by the built network if its centroid is within 60 m of a "
               "built gravity pipe (~ half a block). PROJECT ASSUMPTION for the capacity "
               "screen only; it is not a design allocation rule.")

A_KIN_VISC_M2S = 1.0e-6
A_KIN_VISC_NOTE = "kinematic viscosity 1.0e-6 m2/s (water ~20 C). ASSUMPTION."

A_DEFAULT_DEPTH_M = 1.00
A_DEFAULT_DEPTH_NOTE = ("a recorded depth-to-invert of exactly 1.000 m is a DRAWING DEFAULT, "
                        "not a survey: 373 of 2,142 upstream ends carry it to the millimetre "
                        "and no other value comes close to that frequency. Depth statistics "
                        "are published with and without them.")

A_CLIMB_TOLERANCE = 1.25
A_CLIMB_TOLERANCE_NOTE = ("where a statistic has no meaningful package-to-package spread, the "
                          "acceptance band is the measured value + 25 %. The 25 % is a PROJECT "
                          "TOLERANCE, chosen here, not measured and not from a guideline.")

A_PKG_MIN_KM_GEOM = 3.0
A_PKG_MIN_KM_LEVEL = 5.0
A_PKG_MIN_NOTE = ("bands come from the spread between construction packages. A package must "
                  "carry 3 km of pipe to set a geometry band and 5 km of LEVELLED pipe to set "
                  "a level band, so 5A-3 (3.5 km) does not get to widen a band on its own.")

A_PVC_ID_FROM_OD = {160: 0.1504, 200: 0.1880}
A_PVC_ID_NOTE = ("internal diameter from outside diameter for PVC-U SN4: OD160 -> ID 150.4 mm "
                 "(the shapefile's own IN_DIAMETE reads 150 on every OD160 row, which "
                 "corroborates it); OD200 -> ID 188.0 mm, ASSUMED — IN_DIAMETE is 0 on every "
                 "OD200 row, so the trunk-main bore is not recorded anywhere in the dataset.")

# --------------------------------------------------------------------------------------
# Target
# --------------------------------------------------------------------------------------

BASIS_MEASURED = "MEASURED"
BASIS_GUIDELINE = "GUIDELINE"
BASIS_ASSUMPTION = "ASSUMPTION"


@dataclass
class Target:
    """One checkable number, with the band a W12 design must land in."""
    key: str
    label: str
    value: float | None
    unit: str
    basis: str                 # MEASURED | GUIDELINE | ASSUMPTION
    source: str                # field name, guideline page, or decision
    lo: float | None = None    # acceptance band, inclusive
    hi: float | None = None
    n: int | None = None       # sample size behind `value`
    km: float | None = None    # sample length behind `value`
    direction: str = "band"    # band | max | min | info
    note: str = ""

    def verdict(self, observed: float | None) -> str:
        if observed is None or (isinstance(observed, float) and math.isnan(observed)):
            return "NO DATA"
        if self.direction == "info":
            return "INFO"
        if self.direction == "max":
            return "PASS" if self.hi is None or observed <= self.hi else "HIGH"
        if self.direction == "min":
            return "PASS" if self.lo is None or observed >= self.lo else "LOW"
        if self.lo is not None and observed < self.lo:
            return "LOW"
        if self.hi is not None and observed > self.hi:
            return "HIGH"
        return "PASS"

    def band_str(self) -> str:
        if self.direction == "max":
            return f"<= {self.hi:g}"
        if self.direction == "min":
            return f">= {self.lo:g}"
        if self.direction == "info":
            return "-"
        if self.lo is None and self.hi is None:
            return "-"
        return f"{self.lo:g} .. {self.hi:g}"


# --------------------------------------------------------------------------------------
# small hydraulics — used only by the capacity screen
# --------------------------------------------------------------------------------------

def q_over_Q(dD: float) -> float:
    """Proportional discharge at relative depth d/D for a circular pipe (Manning form)."""
    theta = 2.0 * math.acos(1.0 - 2.0 * dD)
    a_ratio = (theta - math.sin(theta)) / (2.0 * math.pi)
    p_ratio = theta / (2.0 * math.pi)
    return a_ratio * (a_ratio / p_ratio) ** (2.0 / 3.0)


def colebrook_full_bore_ls(D_m: float, S: float,
                           ks_mm: float = G203_P28_KS_MM,
                           nu: float = A_KIN_VISC_M2S) -> float:
    """Full-bore discharge (L/s) by Colebrook-White, the formula G203-p28 4.2.4 mandates."""
    if D_m <= 0 or S <= 0:
        return 0.0
    g = 9.80665
    ks = ks_mm / 1000.0
    root = math.sqrt(2.0 * g * D_m * S)
    v = -2.0 * root * math.log10(ks / (3.7 * D_m) + 2.51 * nu / (D_m * root))
    return v * math.pi * D_m ** 2 / 4.0 * 1000.0


def merrimack_peak_factor(q_adf_m3d: float) -> float:
    """G201-p71 7.4.2:  Qpdf = 2.65 * Qadf^0.879, both in Ml/d.  Pf = Qpdf/Qadf."""
    if q_adf_m3d <= 0:
        return float("nan")
    a, b = G201_P71_MERRIMACK
    q_mld = q_adf_m3d / 1000.0
    return a * q_mld ** b / q_mld


def peltier_peak_factor(q_adf_ls: float) -> float:
    """G201-p72:  PfWW = 1.5 + 1/sqrt(Qadf in L/s)."""
    if q_adf_ls <= 0:
        return float("nan")
    a, b = G201_P72_PELTIER
    return a + b / math.sqrt(q_adf_ls)


def tab11_min_gradient_mm_m(dia_mm: float) -> float | None:
    """G203-p29 Table 11, stepped on the tabulated diameters. None below 200 mm —
    the table does not cover it, and inventing a value there is prohibited."""
    keys = sorted(G203_P29_TAB11_MIN_GRADIENT_MM_M)
    if dia_mm < keys[0]:
        return None
    pick = keys[0]
    for k in keys:
        if dia_mm >= k:
            pick = k
    return G203_P29_TAB11_MIN_GRADIENT_MM_M[pick]


def tab12_max_spacing_m(dia_mm: float) -> float | None:
    for lo, hi, sp in G203_P30_TAB12_MAX_MH_SPACING_M:
        if lo <= dia_mm <= hi:
            return float(sp)
    return None


# --------------------------------------------------------------------------------------
# AsBuilt
# --------------------------------------------------------------------------------------

_MH_RE = re.compile(r"^(?P<pkg>[0-9A-Z]+-[0-9A-Z]+)-(?P<zone>.+)-MH(?P<n>.*)$")


def _tier_of_zone(zone: str) -> str:
    if zone == "TM":
        return "TRUNK"
    if zone.startswith("SM"):
        return "SUBMAIN"
    if zone.startswith("FL"):
        return "FORCE"
    return "LATERAL"


class AsBuilt:
    """NAMA's built Ibri gravity network, filtered and measured."""

    def __init__(self, paths: Mapping[str, str] | None = None, verbose: bool = False):
        self.paths = dict(default_paths())
        if paths:
            self.paths.update(paths)
        self.verbose = verbose
        self._notes: list[str] = []

    # ---- loading -----------------------------------------------------------------

    @cached_property
    def raw(self):
        import geopandas as gpd
        g = gpd.read_file(self.paths["sewerline"])
        if g.crs is None or g.crs.to_epsg() != CRS_EPSG:
            g = g.set_crs(CRS_EPSG, allow_override=True)
        g["LEN_M"] = g.geometry.length
        return g

    @cached_property
    def _flagged(self):
        """raw + STATUS / schematic flags.  Nothing dropped yet."""
        g = self.raw.copy()
        g["IS_BUILT"] = g["STATUS"].astype(str).str.strip().eq("Ex")
        def _nv(geom):
            if geom is None:
                return 0
            parts = geom.geoms if geom.geom_type.startswith("Multi") else [geom]
            return sum(len(p.coords) for p in parts)
        g["N_VERT"] = g.geometry.apply(_nv)
        g["M_PER_VERT"] = g["LEN_M"] / np.maximum(g["N_VERT"] - 1, 1)
        g["IS_SCHEMATIC"] = g["M_PER_VERT"] > A_SCHEMATIC_M_PER_VERTEX
        return g

    @cached_property
    def proposed(self):
        """STATUS != 'Ex'.  The asset GIS holds proposals too — never quote these as built."""
        return self._flagged[~self._flagged.IS_BUILT].copy()

    @cached_property
    def schematic(self):
        """Built rows that are diagram, not pipe."""
        f = self._flagged
        return f[f.IS_BUILT & f.IS_SCHEMATIC].copy()

    @cached_property
    def pipes(self):
        """THE built gravity network: STATUS == 'Ex', schematic rows removed."""
        f = self._flagged
        g = f[f.IS_BUILT & ~f.IS_SCHEMATIC].copy()
        g["PKG"] = g["PROJECTCOD"].astype(str)
        z = g["US_MHID"].astype(str).map(lambda s: (_MH_RE.match(s).group("zone")
                                                    if _MH_RE.match(s) else ""))
        g["ZONE"] = z
        g["TIER"] = z.map(_tier_of_zone)
        g["OD_MM"] = pd.to_numeric(g["OUT_DIAMET"], errors="coerce").fillna(0.0)
        g["ID_M"] = g["OD_MM"].map(lambda d: A_PVC_ID_FROM_OD.get(int(d), np.nan))
        g["HAS_LEVELS"] = (pd.to_numeric(g.US_INVERT_, errors="coerce").fillna(0) > 0) & \
                          (pd.to_numeric(g.DS_INVERT_, errors="coerce").fillna(0) > 0)
        return g

    @cached_property
    def levelled(self):
        """The 65.6 % of built pipe that carries inverts and ground levels."""
        g = self.pipes[self.pipes.HAS_LEVELS].copy()
        g["FALL_M"] = g.US_INVERT_ - g.DS_INVERT_
        g["GRAD_MM_M"] = g.FALL_M / g.LEN_M * 1000.0
        g["GFALL_M"] = g.US_GROUND_ - g.DS_GROUND_        # +ve = ground falls with the flow
        g["GGRAD_MM_M"] = g.GFALL_M / g.LEN_M * 1000.0
        g["DEP_US_M"] = g.US_GROUND_ - g.US_INVERT_        # to INVERT
        g["DEP_DS_M"] = g.DS_GROUND_ - g.DS_INVERT_
        g["DEP_M"] = (g.DEP_US_M + g.DEP_DS_M) / 2.0
        g["COVER_M"] = g.DEP_M - g.OD_MM / 1000.0          # to CROWN — the guideline's datum
        g["COVER_US_M"] = g.DEP_US_M - g.OD_MM / 1000.0
        g["COVER_DS_M"] = g.DEP_DS_M - g.OD_MM / 1000.0
        # a depth recorded as exactly 1.000 m is a drawing default, not a survey
        g["DEPTH_DEFAULTED"] = (g.DEP_US_M.round(3) == A_DEFAULT_DEPTH_M) & \
                               (g.DEP_DS_M.round(3) == A_DEFAULT_DEPTH_M)
        return g

    # ---- topology ----------------------------------------------------------------

    @cached_property
    def nodes(self):
        """Manholes, from the designer's own US_MHID / DS_MHID — never inferred from
        geometry.  Degree, tier and package for each."""
        g = self.pipes
        ind = g.DS_MHID.value_counts()
        outd = g.US_MHID.value_counts()
        ids = pd.Index(pd.unique(pd.concat([g.US_MHID, g.DS_MHID]).dropna()))
        n = pd.DataFrame(index=ids)
        n["N_IN"] = ind.reindex(ids).fillna(0).astype(int)
        n["N_OUT"] = outd.reindex(ids).fillna(0).astype(int)
        m = pd.Series(ids, index=ids).map(lambda s: _MH_RE.match(str(s)))
        n["PKG"] = [mm.group("pkg") if mm else "" for mm in m]
        n["ZONE"] = [mm.group("zone") if mm else "" for mm in m]
        n["TIER"] = n["ZONE"].map(_tier_of_zone)
        n["IS_HEAD"] = n.N_IN == 0
        n["IS_JUNCTION"] = n.N_IN >= 2
        n["IS_TERMINAL"] = n.N_OUT == 0
        return n

    @cached_property
    def drops(self):
        """Every (incoming pipe -> outgoing pipe) pair at a manhole where both carry
        levels, with the invert step across the chamber.

        drop > 0.60 m  -> backdrop required        (G203-p30)
        drop > 2.00 m  -> vortex drop shaft        (G203-p30)
        """
        lv = self.levelled
        inc = lv[["DS_MHID", "FEATUREID", "DS_INVERT_", "TIER", "PKG", "LEN_M"]].rename(
            columns={"DS_MHID": "MH", "FEATUREID": "FID_IN", "DS_INVERT_": "INV_IN",
                     "TIER": "TIER_IN", "LEN_M": "LEN_IN"})
        out = lv[["US_MHID", "FEATUREID", "US_INVERT_", "TIER"]].rename(
            columns={"US_MHID": "MH", "FEATUREID": "FID_OUT", "US_INVERT_": "INV_OUT",
                     "TIER": "TIER_OUT"})
        j = inc.merge(out, on="MH", how="inner")
        j["DROP_M"] = j.INV_IN - j.INV_OUT
        j["N_IN"] = j.MH.map(self.nodes.N_IN).fillna(0).astype(int)
        j["CLASS"] = np.select(
            [j.DROP_M > G203_P30_BACKDROP_MAX_M,
             j.DROP_M > G203_P30_BACKDROP_TRIGGER_M],
            ["VORTEX", "BACKDROP"], default="NONE")
        return j

    # ---- external overlays -------------------------------------------------------

    @cached_property
    def hazard(self):
        """50-year flood hazard class at each built pipe's midpoint.
        NO-DATA is recorded as class 0 = DRY HIGH GROUND (engineer, 2026-09-03)."""
        import rasterio
        g = self.pipes
        mid = g.geometry.interpolate(0.5, normalized=True)
        pts = [(p.x, p.y) for p in mid]
        with rasterio.open(self.paths["hazard50"]) as r:
            nd = r.nodata
            v = np.array([s[0] for s in r.sample(pts)], dtype=float)
        outside = ~np.isfinite(v) | (v == nd)
        v = np.where(outside, 0.0, v)
        return pd.DataFrame({"FEATUREID": g.FEATUREID.values,
                             "HAZ": v, "OUTSIDE_GRID": outside}, index=g.index)

    @cached_property
    def dual_overlap_m(self):
        """Metres of each built pipe lying within A_DUAL_BUFFER_M of a dual carriageway."""
        import geopandas as gpd
        rd = gpd.read_file(self.paths["roads"])
        rd = rd.set_crs(CRS_EPSG, allow_override=True)
        dual = rd[pd.to_numeric(rd["dual"], errors="coerce") == 1]
        buf = dual.buffer(A_DUAL_BUFFER_M).union_all()
        return self.pipes.geometry.intersection(buf).length

    # ---- measurements ------------------------------------------------------------

    def m_inventory(self) -> dict:
        f, g, lv = self._flagged, self.pipes, self.levelled
        return {
            "rows_total": int(len(f)),
            "rows_built": int(f.IS_BUILT.sum()),
            "rows_proposed": int((~f.IS_BUILT).sum()),
            "km_proposed": float(self.proposed.LEN_M.sum() / 1000.0),
            "schematic_rows": int(len(self.schematic)),
            "km_schematic": float(self.schematic.LEN_M.sum() / 1000.0),
            "pipes": int(len(g)),
            "km_built_gravity": float(g.LEN_M.sum() / 1000.0),
            "pipes_levelled": int(len(lv)),
            "km_levelled": float(lv.LEN_M.sum() / 1000.0),
            "level_coverage_pct": float(lv.LEN_M.sum() / g.LEN_M.sum() * 100.0),
            "manholes": int(len(self.nodes)),
            "heads": int(self.nodes.IS_HEAD.sum()),
            "junctions": int(self.nodes.IS_JUNCTION.sum()),
            "terminals": int(self.nodes.IS_TERMINAL.sum()),
            "bifurcations": int((self.nodes.N_OUT >= 2).sum()),
            "km_force_built": float(self._force_built_km()),
        }

    def _force_built_km(self) -> float:
        import geopandas as gpd
        try:
            fm = gpd.read_file(self.paths["forceline"]).set_crs(CRS_EPSG, allow_override=True)
        except Exception:
            return float("nan")
        b = fm[fm["STATUS"].astype(str).str.strip() == "Ex"]
        return float(b.geometry.length.sum() / 1000.0)

    def m_spacing(self) -> dict:
        L = self.pipes.LEN_M
        return {
            "mh_spacing_median_m": float(L.median()),
            "mh_spacing_mean_m": float(L.mean()),
            "mh_spacing_p10_m": float(L.quantile(0.10)),
            "mh_spacing_p90_m": float(L.quantile(0.90)),
            "mh_spacing_max_m": float(L.max()),
            "mh_per_km": float(len(self.nodes) / (L.sum() / 1000.0)),
            "spacing_over_tab12_pct": float(
                (L > 100.0).sum() / len(L) * 100.0),     # Tab 12 row for 200-315 mm
        }

    def m_gradient(self) -> dict:
        lv = self.levelled
        out = {
            "gradient_median_mm_m": float(lv.GRAD_MM_M.median()),
            "gradient_p10_mm_m": float(lv.GRAD_MM_M.quantile(0.10)),
            "gradient_p90_mm_m": float(lv.GRAD_MM_M.quantile(0.90)),
            "gradient_max_mm_m": float(lv.GRAD_MM_M.max()),
            "adverse_gradient_n": int((lv.GRAD_MM_M < 0).sum()),
            "flat_gradient_n": int((lv.GRAD_MM_M == 0).sum()),
        }
        for od in sorted(lv.OD_MM.unique()):
            s = lv[lv.OD_MM == od].GRAD_MM_M
            out[f"gradient_median_mm_m_OD{int(od)}"] = float(s.median())
            out[f"gradient_n_OD{int(od)}"] = int(len(s))
        # against Table 11's DN200 row, the only row that touches these sizes
        s200 = lv[lv.OD_MM == 200].GRAD_MM_M
        out["below_tab11_dn200_pct_OD200"] = float((s200 < 5.0).mean() * 100.0) if len(s200) else float("nan")
        return out

    def m_depth(self) -> dict:
        lv = self.levelled
        c, w = lv.COVER_M, lv.LEN_M
        real = lv[~lv.DEPTH_DEFAULTED]
        out = {
            "cover_median_m": float(c.median()),
            "cover_p10_m": float(c.quantile(0.10)),
            "cover_p90_m": float(c.quantile(0.90)),
            "cover_p99_m": float(c.quantile(0.99)),
            "cover_max_m": float(c.max()),
            "cover_below_1p30_pct_len": float(w[c < G203_P33_MIN_COVER_M].sum() / w.sum() * 100.0),
            "cover_below_0p50_pct_len": float(w[c < G203_P33_MIN_COVER_PROTECTED_M].sum() / w.sum() * 100.0),
            "cover_over_6m_pct_len": float(w[c > 6.0].sum() / w.sum() * 100.0),
            "cover_over_12m_pct_len": float(w[c > 12.0].sum() / w.sum() * 100.0),
            "invert_depth_median_m": float(lv.DEP_M.median()),
            # the same, with the 1.000 m drawing default struck out
            "depth_defaulted_n": int(lv.DEPTH_DEFAULTED.sum()),
            "depth_defaulted_km": float(w[lv.DEPTH_DEFAULTED].sum() / 1000.0),
            "depth_us_exactly_1m_n": int((lv.DEP_US_M.round(3) == A_DEFAULT_DEPTH_M).sum()),
            "cover_median_m_nodefault": float(real.COVER_M.median()),
            "cover_below_1p30_pct_len_nodefault": float(
                real.LEN_M[real.COVER_M < G203_P33_MIN_COVER_M].sum() / real.LEN_M.sum() * 100.0),
        }
        return out

    def m_tiers(self) -> dict:
        g = self.pipes
        tot = g.LEN_M.sum()
        out = {}
        for t in ("TRUNK", "SUBMAIN", "LATERAL"):
            s = g[g.TIER == t]
            out[f"tier_share_{t.lower()}_pct"] = float(s.LEN_M.sum() / tot * 100.0)
            out[f"tier_km_{t.lower()}"] = float(s.LEN_M.sum() / 1000.0)
            out[f"tier_n_{t.lower()}"] = int(len(s))
        # how many things touch the trunk, and where each lateral zone drains
        z = self._zone_drainage()
        out.update(z)
        return out

    def _zone_drainage(self) -> dict:
        """Where each lateral zone's outlet pipe discharges — the hierarchy, read from
        the designer's own manhole IDs."""
        g = self.pipes
        zt = g.groupby(["PKG", "ZONE"])
        rows = []
        for (pkg, zone), sub in zt:
            if _tier_of_zone(zone) != "LATERAL":
                continue
            # the pipe(s) of this zone whose DS_MHID lies outside the zone
            ds = sub.DS_MHID.astype(str)
            exits = sub[~ds.map(lambda s: _zone_key(s) == (pkg, zone))]
            for _, r in exits.iterrows():
                rows.append((pkg, zone, _tier_of_zone(_zone_of(str(r.DS_MHID)))))
        d = pd.DataFrame(rows, columns=["PKG", "ZONE", "INTO"]) if rows else \
            pd.DataFrame(columns=["PKG", "ZONE", "INTO"])
        n = len(d)
        out = {"lateral_zones": int(d.groupby(['PKG','ZONE']).ngroups) if n else 0}
        for t in ("LATERAL", "SUBMAIN", "TRUNK"):
            out[f"lateral_zone_into_{t.lower()}_pct"] = float((d.INTO == t).mean() * 100.0) if n else float("nan")
            out[f"lateral_zone_into_{t.lower()}_n"] = int((d.INTO == t).sum()) if n else 0
        # things touching the trunk = distinct non-trunk zones discharging into a TM manhole
        g2 = self.pipes
        touch = g2[(g2.TIER != "TRUNK") & g2.DS_MHID.astype(str).str.contains("-TM-", na=False)]
        out["joins_onto_trunk"] = int(touch.groupby(["PKG", "ZONE"]).ngroups)
        trunk_km = g2.loc[g2.TIER == "TRUNK", "LEN_M"].sum() / 1000.0
        out["joins_per_km_of_trunk"] = float(out["joins_onto_trunk"] / trunk_km) if trunk_km else float("nan")
        return out

    def m_runs(self) -> dict:
        """Run length between junctions.  A run starts at a head or a junction and
        follows the single outgoing pipe while the next chamber is a plain pass-through
        (one in, one out).  Every built pipe belongs to exactly one run."""
        g = self.pipes
        nd = self.nodes
        nxt = dict(zip(g.US_MHID.astype(str), zip(g.DS_MHID.astype(str), g.LEN_M)))
        starts = set(nd.index[nd.N_IN != 1].astype(str))          # heads and junctions
        through = set(nd.index[(nd.N_IN == 1) & (nd.N_OUT == 1)].astype(str))
        runs, used = [], set()
        for s in starts:
            cur, acc, hops = s, 0.0, 0
            while cur in nxt and cur not in used:
                used.add(cur)
                d, L = nxt[cur]
                acc += float(L); hops += 1
                cur = d
                if cur not in through:
                    break
            if hops:
                runs.append((acc, hops))
        r = pd.DataFrame(runs, columns=["LEN_M", "HOPS"])
        return {
            "run_between_junctions_median_m": float(r.LEN_M.median()),
            "run_between_junctions_p90_m": float(r.LEN_M.quantile(0.90)),
            "run_between_junctions_mean_m": float(r.LEN_M.mean()),
            "run_between_junctions_median_hops": float(r.HOPS.median()),
            "runs_n": int(len(r)),
            "junctions_per_km": float(self.nodes.IS_JUNCTION.sum() / (g.LEN_M.sum() / 1000.0)),
            "heads_per_km": float(self.nodes.IS_HEAD.sum() / (g.LEN_M.sum() / 1000.0)),
        }

    def m_drops(self) -> dict:
        j = self.drops
        km = self.levelled.LEN_M.sum() / 1000.0
        nmh = self.drops.MH.nunique()
        bd = j[j.CLASS == "BACKDROP"]
        vx = j[j.CLASS == "VORTEX"]
        return {
            "drop_pairs_measurable": int(len(j)),
            "drop_manholes_measurable": int(nmh),
            "backdrop_n": int(len(bd)),
            "vortex_n": int(len(vx)),
            "vortex_manholes_n": int(vx.MH.nunique()),
            "backdrop_manholes_n": int(bd.MH.nunique()),
            "drop_structures_n": int(len(bd) + len(vx)),
            "backdrop_per_km": float(len(bd) / km),
            "vortex_per_km": float(len(vx) / km),
            "vortex_per_1000_chambers": float(len(vx) / nmh * 1000.0),
            "backdrop_per_1000_chambers": float(len(bd) / nmh * 1000.0),
            "drops_at_junctions_pct": float(((j.CLASS != "NONE") & (j.N_IN >= 2)).sum()
                                            / max((j.CLASS != "NONE").sum(), 1) * 100.0),
            "vortex_at_junctions_pct": float((vx.N_IN >= 2).mean() * 100.0) if len(vx) else float("nan"),
            "max_drop_m": float(j.DROP_M.max()),
            "reverse_step_n": int((j.DROP_M < -0.005).sum()),
        }

    def m_terrain(self) -> dict:
        """Does the built network drain downhill?  The W12 headline test."""
        lv = self.levelled
        L = lv.LEN_M.sum()
        up = lv.GFALL_M < 0
        flat = lv.GFALL_M == 0
        climb = float(-lv.loc[up, "GFALL_M"].sum())
        desc = float(lv.loc[~up, "GFALL_M"].sum())
        return {
            "uphill_length_pct": float(lv.loc[up, "LEN_M"].sum() / L * 100.0),
            "uphill_count_pct": float(up.mean() * 100.0),
            "flat_length_pct": float(lv.loc[flat, "LEN_M"].sum() / L * 100.0),
            "climb_m": climb,
            "descent_m": desc,
            "climb_m_per_km": float(climb / (L / 1000.0)),
            "descent_m_per_km": float(desc / (L / 1000.0)),
            "climb_to_descent_ratio": float(climb / desc) if desc else float("nan"),
            "ground_slope_median_mm_m": float(lv.GGRAD_MM_M.median()),
            "pipe_minus_ground_median_mm_m": float((lv.GRAD_MM_M - lv.GGRAD_MM_M).median()),
        }

    def m_wadi(self) -> dict:
        """Does the built network go shallower and steeper at a wadi?  Measured, not assumed."""
        g = self.pipes.join(self.hazard[["HAZ", "OUTSIDE_GRID"]])
        lv = self.levelled.join(self.hazard[["HAZ", "OUTSIDE_GRID"]])
        L = g.LEN_M.sum()
        onhaz = g.HAZ >= 1
        wadi = g.HAZ.isin(A_WADI_CLASSES)
        a = lv[lv.HAZ >= 1]
        b = lv[lv.HAZ == 0]
        w = lv[lv.HAZ.isin(A_WADI_CLASSES)]
        out = {
            "hazard_grid_coverage_pct": float((~g.OUTSIDE_GRID).sum() / len(g) * 100.0),
            "on_hazard_length_pct": float(g.loc[onhaz, "LEN_M"].sum() / L * 100.0),
            "on_wadi456_length_pct": float(g.loc[wadi, "LEN_M"].sum() / L * 100.0),
            "on_wadi456_n": int(wadi.sum()),
            "cover_median_on_hazard_m": float(a.COVER_M.median()) if len(a) else float("nan"),
            "cover_median_off_hazard_m": float(b.COVER_M.median()) if len(b) else float("nan"),
            "gradient_median_on_hazard_mm_m": float(a.GRAD_MM_M.median()) if len(a) else float("nan"),
            "gradient_median_off_hazard_mm_m": float(b.GRAD_MM_M.median()) if len(b) else float("nan"),
            "n_on_hazard": int(len(a)), "n_off_hazard": int(len(b)),
            "cover_median_wadi456_m": float(w.COVER_M.median()) if len(w) else float("nan"),
            "gradient_median_wadi456_mm_m": float(w.GRAD_MM_M.median()) if len(w) else float("nan"),
            "n_wadi456_levelled": int(len(w)),
        }
        out["wadi_shallower_by_m"] = out["cover_median_off_hazard_m"] - out["cover_median_on_hazard_m"]
        out["wadi_steeper_by_mm_m"] = out["gradient_median_on_hazard_mm_m"] - out["gradient_median_off_hazard_mm_m"]
        return out

    def m_dual(self) -> dict:
        ov = self.dual_overlap_m
        g = self.pipes
        return {
            "dual_length_pct": float(ov.sum() / g.LEN_M.sum() * 100.0),
            "dual_pipes_n": int((ov > 1.0).sum()),
            "dual_km": float(ov.sum() / 1000.0),
        }

    def m_diameters(self) -> dict:
        g = self.pipes
        L = g.LEN_M.sum()
        out = {}
        for od in sorted(g.OD_MM.unique()):
            s = g[g.OD_MM == od]
            out[f"od{int(od)}_length_pct"] = float(s.LEN_M.sum() / L * 100.0)
            out[f"od{int(od)}_n"] = int(len(s))
        known = g[g.OD_MM > 0]
        out["od_recorded_pct_len"] = float(known.LEN_M.sum() / L * 100.0)
        out["od_below_g203_lateral_min_pct_len"] = float(
            g.loc[(g.OD_MM > 0) & (g.OD_MM < G203_P22_OD_LATERAL_MIN_MM), "LEN_M"].sum() / L * 100.0)
        out["od_max_mm"] = float(g.OD_MM.max())
        return out

    # ---- capacity screen ---------------------------------------------------------

    @cached_property
    def _plot_loads(self):
        import geopandas as gpd
        pl = gpd.read_file(self.paths["plot_loads"], layer="plot_loads")
        pl = pl.set_crs(CRS_EPSG, allow_override=True)
        return pl[pd.to_numeric(pl["Q_AVG_M3D"], errors="coerce").fillna(0) > 0].copy()

    @cached_property
    def _ele_accounts(self):
        import geopandas as gpd
        return gpd.read_file(self.paths["ele_accounts"]).set_crs(CRS_EPSG, allow_override=True)

    def capacity(self, radius_m: float = A_LOAD_RADIUS_M, today: bool = False) -> pd.DataFrame:
        """Load the built network and test each levelled pipe against its own capacity.

        Not a substitute for a SewerGEMS run.  It answers one question: does the pipe
        NAMA laid still have room?  Flow is accumulated on the designer's own
        US_MHID / DS_MHID tree, peaked by Merrimack (G201-p71), with 10 % infiltration
        for an existing inland network (G201-p72), and compared with the Colebrook-White
        full-bore discharge (G203-p28) capped at the Table 10 d/D (G203-p27).
        """
        from shapely.strtree import STRtree

        g = self.pipes
        pl = self._plot_loads
        cen = pl.geometry.representative_point()

        if today:
            acc = self._ele_accounts
            n_now = acc.groupby(acc.PLOT_ID.astype("Int64")).size()
            share = pl.PLOT_ID.astype("Int64").map(n_now).fillna(0.0) / \
                    pd.to_numeric(pl["N_PROP"], errors="coerce").replace(0, np.nan)
            q_plot = pd.to_numeric(pl["Q_AVG_M3D"]) * share.fillna(0.0).clip(upper=1.0)
        else:
            q_plot = pd.to_numeric(pl["Q_AVG_M3D"])

        tree = STRtree(list(g.geometry.values))
        idx = tree.query_nearest(list(cen.values), max_distance=radius_m,
                                 return_distance=False, all_matches=False)
        idx = np.asarray(idx)
        if idx.ndim == 2:                      # (input_idx, tree_idx)
            src, tgt = idx[0], idx[1]
        else:
            src, tgt = np.arange(len(cen)), idx
        lat = pd.DataFrame({"pipe_pos": tgt, "q": q_plot.values[src]})
        local = lat.groupby("pipe_pos").q.sum()
        g = g.reset_index(drop=True)
        g["Q_LOCAL_M3D"] = local.reindex(range(len(g))).fillna(0.0).values

        # accumulate down the tree
        succ = dict(zip(g.US_MHID.astype(str), g.index))
        ds = g.DS_MHID.astype(str)
        order = self._topo_order(g)
        cum = g.Q_LOCAL_M3D.astype(float).copy()
        for i in order:
            d = ds.iloc[i]
            j = succ.get(d)
            if j is not None and j != i:
                cum.iloc[j] += cum.iloc[i]
        g["Q_ADF_M3D"] = cum.values
        g["PF"] = g.Q_ADF_M3D.map(merrimack_peak_factor)
        g["Q_PEAK_LS"] = g.Q_ADF_M3D * g.PF * (1.0 + G201_P72_INFIL_EXISTING_INLAND) / 86.4

        lv = g[g.HAS_LEVELS].copy()
        lv["S"] = ((lv.US_INVERT_ - lv.DS_INVERT_) / lv.LEN_M).clip(lower=0)
        dd = np.where(lv.OD_MM <= 350, G203_P27_TAB10_DD_LE350, G203_P27_TAB10_DD_GT350)
        lv["Q_FULL_LS"] = [colebrook_full_bore_ls(d, s) if np.isfinite(d) else np.nan
                           for d, s in zip(lv.ID_M, lv.S)]
        lv["Q_CAP_LS"] = lv.Q_FULL_LS * np.array([q_over_Q(x) for x in dd])
        # a reach laid dead flat has no capacity at all — a defect in its own right,
        # not a "utilisation of infinity" to average into the failure statistics
        lv["FLAT"] = lv.S <= 0
        lv["UTIL"] = np.where(lv.FLAT, np.nan, lv.Q_PEAK_LS / lv.Q_CAP_LS)
        lv["FAIL"] = lv.UTIL > 1.0
        lv["MARGINAL"] = (lv.UTIL > 1.0) & (lv.UTIL <= 1.25)
        return lv

    @staticmethod
    def _topo_order(g) -> list[int]:
        """Indices ordered head -> outfall (Kahn).  The graph is a tree with 1 known
        bifurcation, so a cycle is not expected; any residue is appended."""
        us = g.US_MHID.astype(str).values
        ds = g.DS_MHID.astype(str).values
        by_us = {}
        for i, u in enumerate(us):
            by_us.setdefault(u, []).append(i)
        indeg = np.zeros(len(g), dtype=int)
        for i, d in enumerate(ds):
            for j in by_us.get(d, []):
                indeg[j] += 1
        from collections import deque
        q = deque(np.where(indeg == 0)[0].tolist())
        order = []
        while q:
            i = q.popleft(); order.append(i)
            for j in by_us.get(ds[i], []):
                indeg[j] -= 1
                if indeg[j] == 0:
                    q.append(j)
        if len(order) < len(g):
            order += [i for i in range(len(g)) if i not in set(order)]
        return order

    def m_capacity(self) -> dict:
        out = {}
        for tag, today in (("sat", False), ("today", True)):
            try:
                lv = self.capacity(today=today)
            except Exception as e:                      # noqa: BLE001
                self._notes.append(f"capacity({tag}) failed: {e}")
                continue
            served = lv[(lv.Q_PEAK_LS > 0) & ~lv.FLAT]
            out[f"cap_{tag}_pipes_tested"] = int((~lv.FLAT).sum())
            out[f"cap_{tag}_pipes_loaded"] = int(len(served))
            out[f"cap_{tag}_flat_n"] = int(lv.FLAT.sum())
            out[f"cap_{tag}_fail_n"] = int(lv.FAIL.sum())
            out[f"cap_{tag}_fail_pct"] = float(lv.FAIL.sum() / (~lv.FLAT).sum() * 100.0)
            out[f"cap_{tag}_fail_km"] = float(lv.loc[lv.FAIL, "LEN_M"].sum() / 1000.0)
            out[f"cap_{tag}_marginal_n"] = int(lv.MARGINAL.sum())
            out[f"cap_{tag}_over_2x_n"] = int((lv.UTIL > 2.0).sum())
            out[f"cap_{tag}_util_median"] = float(served.UTIL.median()) if len(served) else float("nan")
            out[f"cap_{tag}_util_p90"] = float(served.UTIL.quantile(0.90)) if len(served) else float("nan")
            out[f"cap_{tag}_q_on_levelled_m3d"] = float(lv.Q_LOCAL_M3D.sum())
            for tier in ("TRUNK", "SUBMAIN", "LATERAL"):
                s = lv[lv.TIER == tier]
                out[f"cap_{tag}_fail_n_{tier.lower()}"] = int(s.FAIL.sum())
                out[f"cap_{tag}_n_{tier.lower()}"] = int(len(s))
        out.update(self.m_coverage())
        return out

    def m_coverage(self) -> dict:
        """How much of the town the 2006 network reaches at all — the number that decides
        whether W12 reuses it, laid alongside it, or ignores it."""
        pl = self._plot_loads
        cen = pl.geometry.representative_point()
        buf = self.pipes.geometry.union_all().buffer(A_LOAD_RADIUS_M)
        inb = cen.within(buf).values
        q = pd.to_numeric(pl["Q_AVG_M3D"], errors="coerce").fillna(0.0).values
        return {
            "study_area_saturated_load_m3d": float(q.sum()),
            "served_plots_n": int(inb.sum()),
            "study_area_plots_n": int(len(pl)),
            "served_load_m3d": float(q[inb].sum()),
            "served_load_pct": float(q[inb].sum() / q.sum() * 100.0),
        }

    # ---- the whole measurement ---------------------------------------------------

    @cached_property
    def measured(self) -> dict:
        m = {}
        for fn in (self.m_inventory, self.m_spacing, self.m_gradient, self.m_depth,
                   self.m_tiers, self.m_runs, self.m_drops, self.m_terrain,
                   self.m_wadi, self.m_dual, self.m_diameters, self.m_capacity):
            try:
                m.update(fn())
            except Exception as e:                      # noqa: BLE001
                self._notes.append(f"{fn.__name__} failed: {type(e).__name__}: {e}")
        return m

    # ---- per-package spread, which is where the tolerances come from -------------

    @cached_property
    def by_package(self) -> pd.DataFrame:
        """The five construction packages are five independent samples of the same
        designer's habits.  The spread between them IS the tolerance — nothing here
        is a guessed +/- band."""
        g = self.pipes
        lv = self.levelled
        rows = []
        for pkg, sub in g.groupby("PKG"):
            s = lv[lv.PKG == pkg]
            km = sub.LEN_M.sum() / 1000.0
            nmh = len(set(sub.US_MHID) | set(sub.DS_MHID))
            j = self.drops[self.drops.PKG == pkg]
            skm = s.LEN_M.sum() / 1000.0
            rows.append({
                "PKG": pkg, "pipes": len(sub), "km": km, "km_levelled": skm,
                "mh_spacing_median_m": sub.LEN_M.median(),
                "mh_per_km": nmh / km,
                "gradient_median_mm_m": s.GRAD_MM_M.median() if len(s) else np.nan,
                "cover_median_m": s.COVER_M.median() if len(s) else np.nan,
                "cover_p90_m": s.COVER_M.quantile(0.90) if len(s) else np.nan,
                "uphill_length_pct": (s.loc[s.GFALL_M < 0, "LEN_M"].sum() / s.LEN_M.sum() * 100.0)
                                     if len(s) else np.nan,
                "climb_to_descent_ratio": (-s.loc[s.GFALL_M < 0, "GFALL_M"].sum()
                                           / s.loc[s.GFALL_M >= 0, "GFALL_M"].sum())
                                          if len(s) and s.loc[s.GFALL_M >= 0, "GFALL_M"].sum() else np.nan,
                "backdrop_per_km": (j.CLASS == "BACKDROP").sum() / skm if skm else np.nan,
                "vortex_per_km": (j.CLASS == "VORTEX").sum() / skm if skm else np.nan,
                "vortex_per_1000_chambers": ((j.CLASS == "VORTEX").sum() / j.MH.nunique() * 1000.0)
                                            if len(j) else np.nan,
                "tier_share_trunk_pct": sub.loc[sub.TIER == "TRUNK", "LEN_M"].sum() / sub.LEN_M.sum() * 100.0,
                "tier_share_submain_pct": sub.loc[sub.TIER == "SUBMAIN", "LEN_M"].sum() / sub.LEN_M.sum() * 100.0,
                "tier_share_lateral_pct": sub.loc[sub.TIER == "LATERAL", "LEN_M"].sum() / sub.LEN_M.sum() * 100.0,
            })
        return pd.DataFrame(rows).set_index("PKG")

    def _pkg_band(self, col: str, levelled: bool = True,
                  only: Iterable[str] | None = None) -> tuple[float | None, float | None]:
        """min/max of a statistic across the packages big enough to mean anything.

        A level-derived statistic needs A_PKG_MIN_KM_LEVEL of levelled pipe in the
        package; a geometry-derived one needs A_PKG_MIN_KM_GEOM of pipe.  `only`
        restricts to named packages (used for the tier shares, where a package with no
        trunk tier would otherwise widen the band down to zero).
        """
        bp = self.by_package
        size = bp.km_levelled if levelled else bp.km
        floor = A_PKG_MIN_KM_LEVEL if levelled else A_PKG_MIN_KM_GEOM
        use = bp[(size >= floor) & bp[col].notna()]
        if only is not None:
            use = use[use.index.isin(list(only))]
        if len(use) < 2:
            return (None, None)
        return (float(use[col].min()), float(use[col].max()))

    @cached_property
    def _three_tier_packages(self) -> list[str]:
        """Packages that actually built all three tiers.  5A-1 has no trunk and no
        sub-main; 5A-3 has no sub-main.  Only the rest can set a tier-share band."""
        bp = self.by_package
        ok = (bp.tier_share_trunk_pct > 0) & (bp.tier_share_submain_pct > 0)
        return list(bp.index[ok])

    # ---- targets -----------------------------------------------------------------

    def targets(self) -> dict[str, Target]:
        m = self.measured
        T: dict[str, Target] = {}

        def add(t: Target):
            T[t.key] = t

        km = m.get("km_built_gravity")
        kml = m.get("km_levelled")
        n = m.get("pipes")
        nl = m.get("pipes_levelled")

        # --- the headline: does the layout follow the ground ----------------------
        lo, hi = self._pkg_band("uphill_length_pct")
        add(Target("uphill_length_pct",
                   "share of length whose GROUND rises in the direction of flow",
                   m.get("uphill_length_pct"), "%", BASIS_MEASURED,
                   "US_GROUND_ / DS_GROUND_ on 2,142 levelled built pipes",
                   lo=None, hi=(hi if hi else m.get("uphill_length_pct")), n=nl, km=kml,
                   direction="max",
                   note=("THE HEADLINE, and it is NOT zero. NAMA's own network runs uphill on "
                         "a third of its length. The band's top is the worst package, so a "
                         "W12 design above it is worse than anything NAMA built.")))

        lo, hi = self._pkg_band("climb_to_descent_ratio")
        add(Target("climb_to_descent_ratio",
                   "cumulative ground climb / cumulative ground descent along the flow path",
                   m.get("climb_to_descent_ratio"), "-", BASIS_MEASURED,
                   "US_GROUND_ / DS_GROUND_, summed along flow", lo=None,
                   hi=hi, n=nl, km=kml, direction="max",
                   note=("the sharper of the two terrain tests: it weights a long climb "
                         "properly, where the length share does not.")))

        add(Target("climb_m_per_km", "ground climb bought per km of sewer",
                   m.get("climb_m_per_km"), "m/km", BASIS_MEASURED,
                   "US_GROUND_ / DS_GROUND_", lo=None,
                   hi=m.get("climb_m_per_km", float("nan")) * A_CLIMB_TOLERANCE,
                   n=nl, km=kml, direction="max", note=A_CLIMB_TOLERANCE_NOTE))

        # --- drop structures ------------------------------------------------------
        lo, hi = self._pkg_band("vortex_per_km")
        add(Target("vortex_per_km",
                   "vortex drop shafts per km (invert step > 2.00 m)",
                   m.get("vortex_per_km"), "1/km", BASIS_MEASURED,
                   "US_INVERT_ / DS_INVERT_ across shared manholes; threshold G203-p30",
                   lo=None, hi=hi, n=m.get("vortex_n"), km=kml, direction="max",
                   note=("the sharpest single test of whether a layout follows the ground. "
                         "COMPARE PER KM, NOT AS A COUNT: 37 shafts in 63 km is 0.59/km, and a "
                         "1,700 km design is allowed ~1,000 of them at NAMA's own rate.")))

        lo, hi = self._pkg_band("backdrop_per_km")
        add(Target("backdrop_per_km", "backdrops per km (invert step 0.60-2.00 m)",
                   m.get("backdrop_per_km"), "1/km", BASIS_MEASURED,
                   "US_INVERT_ / DS_INVERT_; threshold G203-p30", lo=None, hi=hi,
                   n=m.get("backdrop_n"), km=kml, direction="max"))

        lo, hi = self._pkg_band("vortex_per_1000_chambers")
        add(Target("vortex_per_1000_chambers", "vortex drop shafts per 1,000 chambers",
                   m.get("vortex_per_1000_chambers"), "1/1000", BASIS_MEASURED,
                   "as above, normalised on chambers instead of length",
                   lo=None, hi=hi, n=m.get("vortex_n"), km=kml, direction="max",
                   note="the length-free version, for a design with different chamber spacing."))

        add(Target("vortex_at_junctions_pct",
                   "share of vortex drops that sit at a junction, not on a straight run",
                   m.get("vortex_at_junctions_pct"), "%", BASIS_MEASURED,
                   "node degree from US_MHID / DS_MHID", lo=100.0, hi=None,
                   n=m.get("vortex_n"), km=kml, direction="min",
                   note=("ALL 37 are at junctions. NAMA never uses a drop to walk a main down "
                         "a slope — only to land a branch that arrives high. A design with "
                         "drops on straight runs is levelling its way out of a layout fault.")))

        # --- chambers -------------------------------------------------------------
        lo, hi = self._pkg_band("mh_spacing_median_m", levelled=False)
        add(Target("mh_spacing_median_m", "median chamber spacing",
                   m.get("mh_spacing_median_m"), "m", BASIS_MEASURED,
                   "geometric length of each built pipe", lo=lo, hi=hi, n=n, km=km,
                   note=("INFORMATIVE, NOT A GOAL. Re-running W7's design at five spacing "
                         "caps changed depth by under 5 cm and nearly doubled the chamber "
                         "count, so copying 30 m buys nothing. G203-p30 Tab 12 allows 100 m "
                         "at these diameters; NAMA used 30 %% of it.")))

        lo, hi = self._pkg_band("mh_per_km", levelled=False)
        add(Target("mh_per_km", "chambers per km", m.get("mh_per_km"), "1/km",
                   BASIS_MEASURED, "distinct US_MHID / DS_MHID", lo=lo, hi=hi, n=n, km=km))

        add(Target("mh_spacing_max_m", "longest single reach between chambers",
                   m.get("mh_spacing_max_m"), "m", BASIS_GUIDELINE,
                   "G203-p30 Table 12, 200-315 mm row", lo=None, hi=100.0,
                   n=n, km=km, direction="max",
                   note="built max is 71.4 m — inside the 100 m the table allows."))

        # --- gradients ------------------------------------------------------------
        lo, hi = self._pkg_band("gradient_median_mm_m")
        add(Target("gradient_median_mm_m", "median laid gradient",
                   m.get("gradient_median_mm_m"), "mm/m", BASIS_MEASURED,
                   "(US_INVERT_ - DS_INVERT_) / length", lo=lo, hi=hi, n=nl, km=kml))

        add(Target("gradient_median_mm_m_OD200", "median laid gradient, OD200 (the trunk mains)",
                   m.get("gradient_median_mm_m_OD200"), "mm/m", BASIS_MEASURED,
                   "OUT_DIAMET == 200", lo=None, hi=None,
                   n=m.get("gradient_n_OD200"), km=None, direction="info",
                   note=("G203-p29 Tab 11 asks 5.00 mm/m at DN200. Built median is 5.19; "
                         f"{m.get('below_tab11_dn200_pct_OD200', float('nan')):.0f} % of OD200 "
                         "reaches are laid flatter than the table's own minimum.")))

        add(Target("adverse_gradient_n", "reaches laid against the flow (US invert below DS)",
                   m.get("adverse_gradient_n"), "count", BASIS_MEASURED,
                   "US_INVERT_ < DS_INVERT_", lo=None, hi=0, n=nl, km=kml, direction="max",
                   note="zero in the built network, and G203-p29 forbids a reverse gradient."))

        # --- depth ----------------------------------------------------------------
        lo, hi = self._pkg_band("cover_median_m")
        add(Target("cover_median_m", "median cover to crown",
                   m.get("cover_median_m"), "m", BASIS_MEASURED,
                   "ground - invert - OD, both ends averaged", lo=lo, hi=hi, n=nl, km=kml))

        lo, hi = self._pkg_band("cover_p90_m")
        add(Target("cover_p90_m", "90th-percentile cover", m.get("cover_p90_m"), "m",
                   BASIS_MEASURED, "as above", lo=lo, hi=hi, n=nl, km=kml))

        add(Target("cover_max_m", "deepest cover", m.get("cover_max_m"), "m",
                   BASIS_GUIDELINE, "G203-p33 4.6.3 'approximately 10-12 m' recommended max",
                   lo=None, hi=G203_P33_MAX_COVER_M[1], n=nl, km=kml, direction="max",
                   note=(f"built max is {m.get('cover_max_m', float('nan')):.2f} m and it PUMPS "
                         f"to stay there: {m.get('km_force_built', float('nan')):.1f} km of built "
                         f"force main against {km:.1f} km of gravity. Depth and pumping are the "
                         "same trade; this number cannot be read without the other.")))

        add(Target("cover_below_1p30_pct_len", "length below the 1.30 m minimum cover",
                   m.get("cover_below_1p30_pct_len"), "%", BASIS_GUIDELINE,
                   "G203-p33 4.6.3", lo=None, hi=0.0, n=nl, km=kml, direction="max",
                   note=("NAMA BREACHES ITS OWN RULE ON "
                         f"{m.get('cover_below_1p30_pct_len', float('nan')):.0f} % of the levelled "
                         f"length ({m.get('cover_below_1p30_pct_len_nodefault', float('nan')):.0f} % "
                         "once the 1.000 m drawing defaults are struck out). A TARGET OF ZERO for "
                         "W12, not a habit to copy. It is here so nobody cites the as-built as "
                         "authority for a shallow pipe.")))

        add(Target("depth_defaulted_km", "length whose recorded depth is the 1.000 m default",
                   m.get("depth_defaulted_km"), "km", BASIS_MEASURED,
                   "DEP_US == DEP_DS == 1.000 m exactly", direction="info",
                   n=m.get("depth_defaulted_n"),
                   note=A_DEFAULT_DEPTH_NOTE))

        # --- hierarchy ------------------------------------------------------------
        three = self._three_tier_packages
        sub3 = self.pipes[self.pipes.PKG.isin(three)]
        for t, keyname in (("trunk", "tier_share_trunk_pct"),
                           ("submain", "tier_share_submain_pct"),
                           ("lateral", "tier_share_lateral_pct")):
            lo, hi = self._pkg_band(keyname, levelled=False, only=three)
            # the target is the shape of a package that actually HAS a hierarchy; the
            # whole-network figure is dragged by 5A-1's 32 km of untiered lateral.
            v3 = float(sub3.loc[sub3.TIER == t.upper().replace("SUBMAIN", "SUBMAIN"),
                                "LEN_M"].sum() / sub3.LEN_M.sum() * 100.0)
            add(Target(keyname, f"{t} share of built length", v3, "%",
                       BASIS_MEASURED, "tier read from the designer's own manhole IDs "
                                       "(5A-2-TM-MH185 / 5A-2-SM.2-MH391 / 5A-1-A49-MH3), "
                                       f"weighted over the packages that built all three tiers: "
                                       f"{', '.join(three)}",
                       lo=lo, hi=hi, n=m.get(f"tier_n_{t}"), km=m.get(f"tier_km_{t}"),
                       note=(f"whole-network share including the untiered packages is "
                             f"{m.get(keyname, float('nan')):.1f} %. The band is the spread "
                             "between packages and it is WIDE: 5A-1 has no trunk and no "
                             "sub-main tier at all, 5A-3 has no sub-mains. The three-tier shape "
                             "is a habit of this designer, not a law.")
                       if t == "trunk" else ""))

        add(Target("lateral_zone_into_lateral_pct",
                   "lateral zones discharging into ANOTHER lateral, not a main",
                   m.get("lateral_zone_into_lateral_pct"), "%", BASIS_MEASURED,
                   "zone token of DS_MHID at each zone's exit pipe",
                   lo=m.get("lateral_zone_into_lateral_pct"), hi=None,
                   n=m.get("lateral_zone_into_lateral_n"), km=None, direction="min",
                   note="sewage crosses many laterals before it meets a main. A design where "
                        "every catchment finds its own way to the trunk is the W7 failure."))

        add(Target("joins_per_km_of_trunk", "zones discharging into the trunk, per km of trunk",
                   m.get("joins_per_km_of_trunk"), "1/km", BASIS_MEASURED,
                   "DS_MHID containing '-TM-', over the trunk length", direction="info",
                   n=m.get("joins_onto_trunk"), km=m.get("tier_km_trunk"),
                   note=(f"{m.get('joins_onto_trunk')} joins on "
                         f"{m.get('tier_km_trunk', float('nan')):.2f} km of trunk. Compare PER KM. "
                         "W7's failure was 30 joins with no sub-main tier; W8 capped it at 19.")))

        # --- runs -----------------------------------------------------------------
        add(Target("run_between_junctions_median_m", "median run length between junctions",
                   m.get("run_between_junctions_median_m"), "m", BASIS_MEASURED,
                   "chain of degree-1 chambers between heads/junctions",
                   lo=None, hi=None, n=m.get("runs_n"), km=km, direction="info"))

        add(Target("junctions_per_km", "junction chambers per km", m.get("junctions_per_km"),
                   "1/km", BASIS_MEASURED, "nodes with 2+ inflows", direction="info"))

        # --- wadi -----------------------------------------------------------------
        add(Target("on_hazard_length_pct", "length on mapped flood-hazard ground (50 yr)",
                   m.get("on_hazard_length_pct"), "%", BASIS_MEASURED,
                   "Hazard_T50y.tif sampled at each pipe midpoint; no-data = dry",
                   direction="info",
                   note=("G203-p30 4.4.1 says wadis 'must be avoided' and NAMA put a third of "
                         "its network on hazard ground anyway. The rule is about washout, and "
                         "practice reads it as a risk to manage, not an absolute bar.")))

        add(Target("on_wadi456_length_pct", "length on wadi ground, hazard classes 4-6",
                   m.get("on_wadi456_length_pct"), "%", BASIS_ASSUMPTION,
                   f"classes {A_WADI_CLASSES} of the 50-yr grid; {A_WADI_NOTE}",
                   direction="info"))

        add(Target("wadi_shallower_by_m",
                   "how much SHALLOWER the built network runs on hazard ground",
                   m.get("wadi_shallower_by_m"), "m", BASIS_MEASURED,
                   "median cover off-hazard minus median cover on-hazard", direction="info",
                   note=("REFUTES THE RECORD. It is NEGATIVE: NAMA goes "
                         f"{-m.get('wadi_shallower_by_m', float('nan')):.2f} m DEEPER on hazard "
                         f"ground and {-m.get('wadi_steeper_by_mm_m', float('nan')):.2f} mm/m "
                         "FLATTER. The 'shallower and steeper at a wadi' belief is not in this "
                         "data.")))

        # --- dual carriageway -----------------------------------------------------
        add(Target("dual_length_pct", "length running along a dual carriageway",
                   m.get("dual_length_pct"), "%", BASIS_MEASURED,
                   f"within {A_DUAL_BUFFER_M} m of a `dual`=1 centreline", lo=None,
                   hi=max(m.get("dual_length_pct", 0.0), 0.2), n=m.get("dual_pipes_n"),
                   km=km, direction="max",
                   note="project rule 7 forbids it outright; the built network is the evidence "
                        "that the rule matches practice."))

        # --- diameters ------------------------------------------------------------
        add(Target("od_below_g203_lateral_min_pct_len",
                   "length below the guideline's OD 200 minimum for a lateral",
                   m.get("od_below_g203_lateral_min_pct_len"), "%", BASIS_GUIDELINE,
                   "G203-p22 Table 6: lateral OD 200 minimal; OD 160 is a RIDER/property "
                   "connection", lo=None, hi=0.0, km=km, direction="max",
                   note=("DO NOT COPY THE BUILT DIAMETERS. "
                         f"{m.get('od_below_g203_lateral_min_pct_len', float('nan')):.0f} % of "
                         "NAMA's length is OD160, which today's Table 6 classes as a rider / "
                         "property connection, not a lateral. W12's floor is OD 200.")))

        # --- capacity -------------------------------------------------------------
        add(Target("cap_sat_fail_pct",
                   "built pipes that cannot pass the SATURATED peak flow of the plots they front",
                   m.get("cap_sat_fail_pct"), "%", BASIS_MEASURED,
                   "Colebrook-White G203-p28 at Table 10 d/D, Merrimack peak G201-p71, "
                   "10 % infiltration G201-p72", direction="info",
                   n=m.get("cap_sat_pipes_tested"),
                   note=("a screen, not a model. It answers 'has the 2006 network room' — which "
                         "decides whether W12 reuses it or lays alongside it. The built network "
                         f"fronts only {m.get('served_plots_n', 0):,} plots, "
                         f"{m.get('served_load_pct', float('nan')):.1f} % of the saturated load, "
                         "so the answer is local, not town-wide.")))

        add(Target("served_load_pct", "share of the saturated town load the 2006 network fronts",
                   m.get("served_load_pct"), "%", BASIS_ASSUMPTION,
                   f"plot centroid within {A_LOAD_RADIUS_M:g} m of a built pipe; {A_LOAD_NOTE}",
                   direction="info", n=m.get("served_plots_n")))

        add(Target("cap_today_fail_pct",
                   "built pipes that cannot pass TODAY's peak flow "
                   "(occupancy from live electricity accounts)",
                   m.get("cap_today_fail_pct"), "%", BASIS_ASSUMPTION,
                   "as above, load scaled by accounts-per-plot / N_PROP", direction="info",
                   n=m.get("cap_today_pipes_tested"),
                   note="'today' is a proxy: there is no metered flow anywhere in this project."))

        # --- the flagged assumption, carried onto every output --------------------
        add(Target("tau_pa", "design tractive stress", A_TAU_PA, "Pa", BASIS_ASSUMPTION,
                   "engineer 2026-09-03; GUD-203 4.2.2 gives no numeric tau (GAP-9)",
                   direction="info", note=A_TAU_NOTE))

        return T

    def targets_frame(self) -> pd.DataFrame:
        rows = []
        for t in self.targets().values():
            d = asdict(t)
            d["band"] = t.band_str()
            rows.append(d)
        cols = ["key", "label", "value", "unit", "band", "direction", "basis",
                "source", "n", "km", "note"]
        return pd.DataFrame(rows)[cols]

    # ---- the check a later stage calls -------------------------------------------

    def check(self, observed: Mapping[str, float]) -> pd.DataFrame:
        """Score a design's observables against the targets.  Keys it does not supply
        come back NO DATA — never blank, never a silent pass."""
        rows = []
        for k, t in self.targets().items():
            o = observed.get(k)
            rows.append({
                "key": k, "label": t.label, "unit": t.unit,
                "as_built": t.value, "band": t.band_str(), "design": o,
                "verdict": t.verdict(o), "basis": t.basis, "source": t.source,
            })
        df = pd.DataFrame(rows)
        rank = {"HIGH": 0, "LOW": 1, "NO DATA": 2, "PASS": 3, "INFO": 4}
        return df.sort_values("verdict", key=lambda s: s.map(rank)).reset_index(drop=True)

    def evidence_frame(self) -> pd.DataFrame:
        m = self.measured
        return pd.DataFrame({"key": list(m), "value": [m[k] for k in m]})

    @property
    def notes(self) -> list[str]:
        return list(self._notes)


def _zone_of(mhid: str) -> str:
    m = _MH_RE.match(str(mhid))
    return m.group("zone") if m else ""


def _zone_key(mhid: str):
    m = _MH_RE.match(str(mhid))
    return (m.group("pkg"), m.group("zone")) if m else ("", "")


# --------------------------------------------------------------------------------------
# observe_design — turn a W12 design's PUBLISHED layers into the same observables
# --------------------------------------------------------------------------------------

DEFAULT_FIELDS = {
    "length": "LEN_M",
    "grad_mm_m": "SLOPE_PCT",       # * 10 if given as %; see `slope_is_percent`
    "cover": "COVER_M",
    "tier": "TIER",
    "diameter": "DN_MM",
    "us_node": "US_NODE",
    "ds_node": "DS_NODE",
    "us_ground": "US_GL",
    "ds_ground": "DS_GL",
    "us_invert": "US_IL",
    "ds_invert": "DS_IL",
}

# The as-built has THREE tiers.  A W12 design may use more.  The mapping follows
# G203-p22 Table 6, which names four classes in order: Rider/Property Connection,
# Lateral Sewer, Main sewer, and (above them) the trunk.  So a tier called "main" is a
# MAIN SEWER — it sits with the sub-mains, NOT with the trunk.  Getting this wrong once
# put 393 km of W11a "main" into the trunk share and made a 4.9 % trunk read as 27.6 %.
# Anything not listed here is counted as UNMAPPED and reported, never binned silently.
TIER_ALIASES = {
    "TRUNK": "TRUNK", "TRUNK MAIN": "TRUNK", "TRUNK SEWER": "TRUNK", "TM": "TRUNK",
    "SUBMAIN": "SUBMAIN", "SUB MAIN": "SUBMAIN", "SUB-MAIN": "SUBMAIN", "SM": "SUBMAIN",
    "MAIN": "SUBMAIN", "MAIN SEWER": "SUBMAIN", "SECONDARY": "SUBMAIN",
    "LATERAL": "LATERAL", "LATERAL SEWER": "LATERAL", "LAT": "LATERAL",
    "TERTIARY": "LATERAL", "RIDER": "LATERAL", "RIDER SEWER": "LATERAL",
    "PROPERTY CONNECTION": "LATERAL",
}


def observe_design(reaches, nodes=None, fields: Mapping[str, str] | None = None,
                   slope_is_percent: bool = True,
                   dual_geometry=None, hazard_class=None) -> dict:
    """Compute the AsBuilt observables from a design's published reach layer.

    `reaches` is a GeoDataFrame of the design's pipes.  `fields` remaps column names.
    Anything that cannot be computed is simply absent, and `AsBuilt.check` reports it
    as NO DATA rather than passing it silently.
    """
    f = dict(DEFAULT_FIELDS)
    if fields:
        f.update(fields)
    df = pd.DataFrame(reaches.drop(columns=getattr(reaches, "geometry", pd.Series()).name
                                   if hasattr(reaches, "geometry") else [], errors="ignore"))
    obs: dict[str, float] = {}

    def col(key):
        c = f.get(key)
        return df[c] if c in df.columns else None

    L = col("length")
    if L is None and hasattr(reaches, "geometry"):
        L = reaches.geometry.length
    if L is None:
        return obs
    L = pd.to_numeric(L, errors="coerce")
    totkm = L.sum() / 1000.0

    obs["mh_spacing_median_m"] = float(L.median())
    obs["mh_spacing_max_m"] = float(L.max())

    g = col("grad_mm_m")
    if g is not None:
        g = pd.to_numeric(g, errors="coerce")
        if slope_is_percent:
            g = g * 10.0
        obs["gradient_median_mm_m"] = float(g.median())
        obs["adverse_gradient_n"] = int((g < 0).sum())
        d = col("diameter")
        if d is not None:
            sel = pd.to_numeric(d, errors="coerce") == 200
            if sel.any():
                obs["gradient_median_mm_m_OD200"] = float(g[sel].median())

    c = col("cover")
    if c is not None:
        c = pd.to_numeric(c, errors="coerce")
        obs["cover_median_m"] = float(c.median())
        obs["cover_p90_m"] = float(c.quantile(0.90))
        obs["cover_max_m"] = float(c.max())
        obs["cover_below_1p30_pct_len"] = float(L[c < G203_P33_MIN_COVER_M].sum() / L.sum() * 100.0)

    t = col("tier")
    if t is not None:
        raw = t.astype(str).str.upper().str.strip()
        tt = raw.map(lambda s: TIER_ALIASES.get(s, "UNMAPPED"))
        for name in ("TRUNK", "SUBMAIN", "LATERAL"):
            obs[f"tier_share_{name.lower()}_pct"] = float(L[tt == name].sum() / L.sum() * 100.0)
        unm = tt == "UNMAPPED"
        if unm.any():
            obs["tier_unmapped_pct"] = float(L[unm].sum() / L.sum() * 100.0)
            obs["tier_unmapped_names"] = ", ".join(sorted(raw[unm].unique()))

    ug, dg = col("us_ground"), col("ds_ground")
    if ug is not None and dg is not None:
        ug = pd.to_numeric(ug, errors="coerce"); dg = pd.to_numeric(dg, errors="coerce")
        gf = ug - dg
        up = gf < 0
        obs["uphill_length_pct"] = float(L[up].sum() / L.sum() * 100.0)
        climb = float(-gf[up].sum()); desc = float(gf[~up].sum())
        obs["climb_m_per_km"] = climb / totkm
        if desc:
            obs["climb_to_descent_ratio"] = climb / desc

    ui, di = col("us_invert"), col("ds_invert")
    un, dn = col("us_node"), col("ds_node")
    if all(x is not None for x in (ui, di, un, dn)):
        inc = pd.DataFrame({"MH": dn.astype(str), "INV_IN": pd.to_numeric(di, errors="coerce")})
        out = pd.DataFrame({"MH": un.astype(str), "INV_OUT": pd.to_numeric(ui, errors="coerce")})
        j = inc.merge(out, on="MH")
        j["DROP_M"] = j.INV_IN - j.INV_OUT
        nmh = len(set(un.astype(str)) | set(dn.astype(str)))
        vx = int((j.DROP_M > G203_P30_BACKDROP_MAX_M).sum())
        bd = int(((j.DROP_M > G203_P30_BACKDROP_TRIGGER_M) &
                  (j.DROP_M <= G203_P30_BACKDROP_MAX_M)).sum())
        obs["vortex_per_km"] = vx / totkm
        obs["backdrop_per_km"] = bd / totkm
        obs["vortex_per_1000_chambers"] = vx / nmh * 1000.0
        nin = dn.astype(str).value_counts()
        j["N_IN"] = j.MH.map(nin).fillna(0)
        big = j[j.DROP_M > G203_P30_BACKDROP_MAX_M]
        if len(big):
            obs["vortex_at_junctions_pct"] = float((big.N_IN >= 2).mean() * 100.0)
        obs["mh_per_km"] = nmh / totkm
        obs["junctions_per_km"] = float((nin >= 2).sum() / totkm)

    d = col("diameter")
    if d is not None:
        d = pd.to_numeric(d, errors="coerce")
        obs["od_below_g203_lateral_min_pct_len"] = float(
            L[(d > 0) & (d < G203_P22_OD_LATERAL_MIN_MM)].sum() / L.sum() * 100.0)

    if dual_geometry is not None and hasattr(reaches, "geometry"):
        ov = reaches.geometry.intersection(dual_geometry).length
        obs["dual_length_pct"] = float(ov.sum() / L.sum() * 100.0)

    if hazard_class is not None:
        h = pd.to_numeric(pd.Series(np.asarray(hazard_class)), errors="coerce").fillna(0)
        obs["on_hazard_length_pct"] = float(L[h.values >= 1].sum() / L.sum() * 100.0)
        obs["on_wadi456_length_pct"] = float(L[np.isin(h.values, A_WADI_CLASSES)].sum() / L.sum() * 100.0)

    obs["tau_pa"] = A_TAU_PA
    return obs


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def _fmt(v, nd=3):
    if v is None:
        return "-"
    if isinstance(v, float):
        if math.isnan(v):
            return "-"
        return f"{v:,.{nd}f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:,.0f}"
    return str(v)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="W12 as-built targets from NAMA's network")
    ap.add_argument("--csv", metavar="DIR", help="write targets/evidence/packages CSVs here")
    ap.add_argument("--json", metavar="FILE", help="write the measured dict as JSON")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    ab = AsBuilt()
    tf = ab.targets_frame()
    ev = ab.evidence_frame()
    bp = ab.by_package

    if not a.quiet:
        pd.set_option("display.width", 200)
        pd.set_option("display.max_rows", 300)
        pd.set_option("display.max_colwidth", 60)
        print("=" * 100)
        print("W12 AS-BUILT TARGETS   (NAMA Ibri, SEWERLINE_IBRI.shp, measured "
              f"{pd.Timestamp.today():%Y-%m-%d})")
        print("=" * 100)
        inv = ab.m_inventory()
        for k in ("rows_total", "rows_built", "rows_proposed", "km_proposed",
                  "schematic_rows", "km_schematic", "pipes", "km_built_gravity",
                  "pipes_levelled", "km_levelled", "level_coverage_pct",
                  "km_force_built", "manholes", "heads", "junctions", "terminals",
                  "bifurcations"):
            print(f"  {k:24s} {_fmt(inv.get(k))}")
        print()
        print(tf[["key", "value", "unit", "band", "basis", "n", "km"]].to_string(index=False))
        print()
        print("PER-PACKAGE SPREAD (the source of every band above)")
        print(bp.round(3).to_string())
        if ab.notes:
            print("\nNOTES / FAILURES")
            for s in ab.notes:
                print("  ! " + s)

    if a.csv:
        os.makedirs(a.csv, exist_ok=True)
        tf.to_csv(os.path.join(a.csv, "asbuilt_targets.csv"), index=False)
        ev.to_csv(os.path.join(a.csv, "asbuilt_evidence.csv"), index=False)
        bp.to_csv(os.path.join(a.csv, "asbuilt_by_package.csv"))
        print(f"\nwritten to {a.csv}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(ab.measured, fh, indent=2, default=float)
        print(f"written {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
