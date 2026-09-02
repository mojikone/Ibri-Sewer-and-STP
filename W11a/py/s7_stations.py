"""s7_stations - lifting stations and their rising mains.  W11a stage 7.

WHAT THIS STAGE IS FOR
----------------------
A gravity sewer that keeps going gets deeper. At some point the trench costs more than a
station, or the chamber stops being maintainable, or the cover simply passes the cap. This
stage decides WHERE that happens, sizes what goes there, and designs the pressure pipe that
takes the flow forward. It publishes `stations` and `rising_mains`; it does not touch
`nodes` or `reaches` (see THE STAGE IS A DECISION, below).

THE FOUR W10 FAILURES THIS PREVENTS, EACH BY CONSTRUCTION
---------------------------------------------------------
1.  **An 85 kW station where a node breached the cap by 3 mm while carrying 36,974 plots.**
    Two independent defects in one number. First, the trigger: W10 pumped on a bare depth
    test, so a 3 mm exceedance bought a station. Here the trigger is the cap-and-veto
    ladder of philosophy sec 5, and rung 1 is `cover > 12 m` **unless** one of the two
    distance-bounded exits applies - the cover recovers within 500 m, or the run reaches an
    outfall within 1,000 m. A chamber that is 3 mm over recovers almost immediately, so the
    exit disposes of it and no tolerance had to be invented to make that happen. Second, the
    position: W10 put the station at the breach, which on a trunk is where the flow is
    largest. Station cost correlates 0.99 with installed power and power is Q x H, so a
    station belongs at the **head of the breach run** - the most upstream chamber whose
    cover is over the cap, where the accumulated flow is smallest. Pumping there also stops
    the depth accumulating at all, so the breach downstream of it never forms.

2.  **17 of W10's 25 rising mains ran below 0.75 m/s, because the duty was taken as the
    arriving peak flow.** The arriving flow tells you what the pump must keep up with; it
    does not tell you what the main should carry. Sizing a bore to the flow that happens to
    arrive gives a main that silts - 5 L/s in a DN200 is 0.16 m/s. Here the bore is chosen
    from the duty so the velocity lands inside G203-p50's window, and where even the
    smallest permitted bore cannot reach the floor the answer is **not a bigger pipe**: it
    is a higher duty. The wet well is what makes that legal - it decouples the pump rate
    from the inflow rate, and G203-p48 sec 7.8 sizes it for exactly that
    (V = 0.25 x Q x T). That is what "duty from the wet-well cycle, not arriving flow" means
    in arithmetic. Within the window the LARGEST such bore is taken, not the smallest:
    velocity squared is friction, friction is head, head is power, and power is what a
    station costs over 25 years. The first draft of this module took the smallest and
    produced DN80 with 122 m of friction against a 4.7 m lift - legal, and ruinous.

3.  **The window is 1.0 to 2.5 m/s, not 0.75 to 3.0.** Two halves of one clause, and both
    were being read wrong. G203-p50: *"The maximum allowable velocity ... shall be not
    greater than 2.5 m/s"* - the 3.0 m/s in H7 is the GRAVITY maximum from p27, and criteria
    audit A9 conflated the two once already (build brief P9). At the other end the same page
    gives *"0.75 m/s (continuous); 1.0 m/s intermittent"*, and a main fed from a
    level-controlled wet well runs only while a pump runs, so **1.0 m/s is the design
    minimum here**. 0.75 is the floor below which the row is refused, not the target.

    This module never imports `C.V_MAX`.

4.  **A rising main is anaerobic by definition.** Its discharge chamber is a septicity
    design, not a pipe end: G203-p55 sec 8.5 requires the main to enter the receiving
    manhole not more than 300 mm above the flow line, with a water seal, forced venting
    through odour control where the entry is turbulent, and a corrosion-resistant or lined
    chamber. `SEPTIC_FL` is 1 on every row, published so it is designed rather than assumed
    away, and the retention time is published beside it because retention is what turns a
    long flat main into an H2S problem (G203-p50 wants it under 30 min).

THE STAGE IS A DECISION, NOT A RE-SOLVE
---------------------------------------
Placing a station changes every level downstream of it: the gravity line restarts at
minimum cover at the discharge chamber and the deep run that triggered the station is never
built. Re-computing those levels is the levels stage's algorithm, not this one's. Rewriting
another stage's audited layer from here is precisely the coupling that let W10's node layer
and pipe layer come out of different solves and disagree by up to 10.39 m of depth.

So this stage reads the levels stage's frame, decides, publishes its own two layers, and
writes a re-solve directive into the manifest. The loop is:

    levels (no stations)  ->  s7  ->  levels (stations as terminals, discharge chambers as
    minimum-cover heads)  ->  s7 again  ->  converged when s7 places no new station.

It follows that s7's normal input is an INTERIM levels frame that still carries unexcused
cap breaches - a frame `contract.validate(strict=True)` would rightly refuse, because a
published design may not carry a breach with no exit. That is why inputs are read at
`strict=False`: the missing-field gate still bites (a field s7 reads must exist), but s7
does not re-litigate value rules on a frame that is mid-solve by design.

WHAT IS NOT DECIDED HERE, AND SAYS SO
--------------------------------------
Rung 2 of the ladder (VETO - a chamber that cannot be maintained) and rung 3 (ECONOMICS -
is a station cheaper over 25 years than digging on) both need inputs nobody has. The veto
rung needs an access/maintainability assessment; the economics rung needs NWS's station
establishment cost, which philosophy sec 5 names as an open item and 00_CURRENT still lists
as open. Neither is guessed. Each is recorded in the manifest as having contributed zero
stations BECAUSE ITS INPUT IS ABSENT - invariant 10, no stage no-ops quietly.

    python s7_stations.py                 run against the published/interim W11a layers
    python s7_stations.py --self-test     synthetic network, proves the arithmetic and the
                                          contract round trip without touching W11a/shp
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point

from w11a import contract
from w11a.contract import C          # sewnet.criteria.DEFAULT - the design basis

hydra = contract.hydra               # W8's Colebrook-White. Re-exported, never reimplemented

W11A = contract.W11A_ROOT
REPO = contract.REPO_ROOT
BASE = os.path.dirname(os.path.dirname(REPO))          # ...\2621 Ibri Sewer STP
TERRAIN = os.path.join(BASE, "Data", "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt")
HAZARD = os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif")

STAGE = "s7_stations"

# ======================================================================================
# The numbers. Every one traces to _BRAIN/02_DESIGN_CRITERIA.md and through it to a page,
# or is DERIVED from two such numbers and says which two. Nothing here is chosen.
# ======================================================================================

CAP_COVER_M = C.MAX_DEPTH               # 12.0 m of cover (G203-p33; philosophy H4)
CAP_EPS_M = 1e-6                        # audit.h4 compares `cov > 12.0 + 1e-6`. Matched
                                        # exactly so the auditor and this stage cannot
                                        # disagree about what a breach is. It is a float
                                        # guard, not a tolerance on the cap.
EXIT_RECOVER_M = 500.0                  # philosophy sec 5 exit 1: cover recovers within 500 m
EXIT_OUTFALL_M = 1000.0                 # philosophy sec 5 exit 2: outfall within 1,000 m

V_RM_MIN = 0.75                         # m/s, force main minimum for CONTINUOUS flow
                                        # (G203-p50). The contract's own floor, and the
                                        # absolute one.
V_RM_MIN_INTERMITTENT = 1.0             # m/s (G203-p50, same row: "0.75 m/s continuous;
                                        # 1.0 m/s intermittent; 1.2 m/s vertical"). A main
                                        # fed from a level-controlled wet well IS
                                        # intermittent - it runs only while a pump runs -
                                        # so 1.0 is the design minimum here and 0.75 is
                                        # only the floor below which the contract refuses
                                        # the row. Designing to 0.75 on a cycling station
                                        # is reading the wrong half of the clause.
V_RM_MAX = 2.5                          # m/s, force main maximum (G203-p50). NOT C.V_MAX
RM_MIN_ID_MM = 75.0                     # non-clog pumps (G203-p50 sec 8.1)
RETENT_MAX_MIN = 30.0                   # "ideally <= 30 min" (G203-p50) - a preference,
                                        # used as a soft constraint and reported when missed
RM_GRADE_RISE = 1.0 / 500.0             # minimum rising gradient (G203-p50 sec 8.2.1)
VALVE_SPACING_M = 500.0                 # in-line isolation valves ~500 m (G203-p53-54 sec 8.4)
VALVE_SPACING_MAX_M = 800.0             # "never exceeding 800 m" (same clause)
RM_ENTRY_ABOVE_FLOWLINE_M = 0.30        # maximum entry above the receiving flow line
                                        # (G203-p55 sec 8.5). A ceiling, so the design
                                        # discharges AT the flow line and keeps the margin.

WW_STARTS_PER_H = 10.0                  # minimum starts/h for motors to 30 kW
                                        # (G203-p48 sec 7.8). Also the contract's floor.
WELL_K = 0.25                           # V = 0.25 x Q x T (G203-p48 sec 7.8)

ST_TYPE_Q = ((100.0, "Type 1"), (300.0, "Type 2"), (float("inf"), "Type 3"))
                                        # Tab 17, G203-p40-41. Thresholds transcribed to
                                        # match contract._cross_field exactly: > 100 is
                                        # Type 2, > 300 is Type 3.
LAND_M2 = {"Type 1": 100.0, "Type 2": 400.0, "Type 3": 900.0}
                                        # Tab 21, G203-p43: 50-100 / 200-400 / >=900 m2 plus
                                        # a 6 m turning circle. The BAND TOP is reserved, not
                                        # the band floor - a land reservation the client
                                        # cannot build in is worse than none, and Type 3 has
                                        # no published top so 900 is a floor there (PENDING).

FLOOD_FREEBOARD_M = 0.30                # floors 300 mm above the 1:50-yr level
                                        # (G203-p38 sec 7.2)

# Tab 16, G203-p40 sec 7.4 - initial MINIMUM flow as a factor on AVERAGE flow. The criteria
# file marks this row: "This flow - not the average - sizes the force main against
# deposition." Four points; read between them in log10(Q) and say so.
TAB16 = ((50.0, 0.25), (500.0, 0.35), (2500.0, 0.45), (5000.0, 0.50))

# ---- derived, not chosen. Each is the product of two cited numbers ---------------------

# How far downstream a discharge chamber may be looked for. Retention = L / v, so the
# 30 min retention limit (G203-p50) at the two velocity bounds (G203-p50) IS the distance
# bound: 1.0 m/s x 1800 s = 1,800 m preferred (the intermittent minimum, which is the one a
# cycling station holds), 2.5 m/s x 1800 s = 4,500 m absolute.
RM_SEARCH_PREF_M = V_RM_MIN_INTERMITTENT * RETENT_MAX_MIN * 60.0   # 1,800 m
RM_SEARCH_MAX_M = V_RM_MAX * RETENT_MAX_MIN * 60.0         # 4,500 m

# A summit is a grade reversal a valve has to sit on, not a wobble in a 0.5 m DEM. The
# guideline's own two numbers bound it: the main is laid no flatter than 1:500 rising
# (G203-p50 sec 8.2.1) and valves sit at ~500 m centres (G203-p53-54 sec 8.4), so a real
# summit stands at least 500 x 1/500 = 1.0 m clear of its neighbours.
SUMMIT_PROM_M = VALVE_SPACING_M * RM_GRADE_RISE            # 1.0 m
PROFILE_STEP_M = 10.0                   # terrain sampling interval along the main

SLS_MIN_PLOTS = C.SLS_MIN_PLOTS         # 50 - CLAUDE.md rule 9, reporting only here
SLS_CASCADE_M = C.SLS_CASCADE_M         # 1,500 m - CLAUDE.md rule 9, reporting only here

WADI_CLASSES = C.HAZARD_WADI_CLASSES    # (4, 5, 6) on Hazard_T50y

# ======================================================================================
# PENDING - assumptions this stage had to make because no cited number exists. Printed on
# every run and written into the manifest. The rule is "do not guess"; where a number was
# unavoidable it is named here rather than buried in a constant.
# ======================================================================================

PENDING = (
    ("RM-1", "Rising-main nominal size series",
     "G203 fixes only the 75 mm ID floor (p50 sec 8.1) and implies 400/500/800/900/1200 "
     "exist in the washout table (p53-54 sec 8.4). The series below is the commercial DI "
     "range. Pressure class is PAM-SPC-207, still an open item in 00_CURRENT."),
    ("RM-2", "Minor and station losses excluded from TOT_HD_M",
     "No guideline value exists for valve, bend and station-pipework losses at concept "
     "stage, and none is invented. TOT_HD_M = static lift + Colebrook-White friction on the "
     "main only, so it is a LOWER BOUND. Pump selection closes it."),
    ("RM-3", "Wet-well sump depth below the arriving invert",
     "Static lift is measured from the arriving invert. The sump sits lower by the pump "
     "submergence and the NPSH margin (G203-p47 sec 7.6 gives the 1 m margin but not a "
     "depth), so LIFT_M is a lower bound until the pump is selected."),
    ("ST-1", "FLOOD_LV is a proxy, not a flood model",
     "G203-p38 sec 7.2 requires 300 mm above the 1:50-yr flood level. No 1:50 water-surface "
     "model exists in the project data. FLOOD_LV is derived from Hazard_T50y: the highest "
     "GROUND level among T50 hazard cells within the search radius (water reaching a cell "
     "stands at least at that cell's ground), and where no hazard cell is within the radius, "
     "the LOWEST ground within it (dry ground bounds the surface from above). Search radius "
     "100 m is a stated assumption, not a guideline value."),
    ("ST-2", "Starts per hour above 30 kW",
     "G203-p48 sec 7.8 sets 10 starts/h as the minimum for motors TO 30 kW and gives no "
     "figure above it. 10/h is carried on every station; a larger motor usually permits "
     "fewer starts, which makes the wet well LARGER, so the published WELL_M3 is a lower "
     "bound on any station whose motor exceeds 30 kW."),
    ("ST-3", "Single duty pump at 100 % of design flow",
     "G203-p39 states it for a small station and Tab 17 (p40-41) gives 2+1 and 3+1 for "
     "Types 2 and 3. Q_DUTY_LS is published as the STATION design flow carried by one duty "
     "pump, which is what the contract's ST_TYPE and WELL_M3 cross-checks both read. "
     "Splitting the duty at detail design REDUCES the required well volume, so this is the "
     "conservative reading."),
    ("LD-1", "Land take for a Type 3 station",
     "G203-p43 Tab 21 gives '>= 900 m2' with no upper bound. 900 m2 is reserved and is a "
     "floor, not a figure."),
)

# The commercial DI range - see PENDING RM-1. 80 mm is the smallest that clears the 75 mm ID
# floor of G203-p50 sec 8.1. DI is ID-designated so DN is the bore, which is why DI and not
# HDPE is carried at concept: HDPE's bore needs the pressure class, and PAM-SPC-207 has not
# arrived. G203-p53 sec 8.3 permits both - "the recommended pipe material for the pressure
# main is Ductile Iron and HDPE".
RM_DN_SERIES = (80, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900,
                1000, 1200)
RM_MATERIAL = "DI"

FLOOD_SEARCH_M = 100.0                  # stated assumption - see PENDING ST-1


# ======================================================================================
# Small physics helpers. Everything hydraulic goes through W8's hydra.
# ======================================================================================

def rm_bore_m(dn: int) -> float:
    """Internal bore of a rising main, m. DI is ID-designated, so the bore IS the DN.

    `criteria.internal_diameter()` is deliberately NOT used: it applies the PVC-U SDR34 wall
    below DN315 (G203-p23 Tab 7), which is a gravity-sewer product rule and would shrink a
    ductile-iron pressure main by 6 % for no reason.
    """
    return dn / 1000.0


def v_at(dn: int, q_ls: float) -> float:
    """Full-bore mean velocity, m/s. A rising main runs full and stays full (G203-p51
    sec 8.2.1), so there is no partial-flow geometry here - that is the gravity case."""
    d = rm_bore_m(dn)
    return (q_ls / 1000.0) / (math.pi * d * d / 4.0)


def q_for_v(dn: int, v: float) -> float:
    """The flow that produces velocity v in this bore, L/s. Used to RAISE a duty that the
    smallest permitted bore cannot scour - the wet well is what makes that legal."""
    d = rm_bore_m(dn)
    return v * math.pi * d * d / 4.0 * 1000.0


def friction_slope(dn: int, q_ls: float) -> float:
    """Hydraulic gradient (m/m) of a full pressure pipe, by Colebrook-White.

    Same law, same roughness as the gravity design - G203-p24 mandates CW and gives
    ks = 1.5 mm for all sizes (p24, p28), nu = 1.141e-6 m2/s (p25). `hydra.v_full` is
    monotone in S and has no closed inverse, so bisect. Bisection over 60 halvings of
    [1e-9, 1] resolves S to better than 1e-18, which is far past anything that matters.

    On ks: 1.5 mm is a slimed-sewer roughness and a new ductile-iron main is nearer
    0.03-0.1 mm, so this over-states friction by roughly a factor of three. That is
    deliberate. The guideline gives no separate pressure-main roughness, a foul rising main
    does slime, and inventing a smoother number to flatter the head would be exactly the
    kind of unsourced constant this project bans. The consequence - published heads are
    conservative - is stated rather than corrected.
    """
    if q_ls <= 0:
        return 0.0
    d = rm_bore_m(dn)
    v = v_at(dn, q_ls)
    lo, hi = 1e-9, 1.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if hydra.v_full(d, mid, C) < v:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def tab16_factor(q_avg_ls: float) -> float:
    """G203-p40 sec 7.4 Tab 16 - initial minimum flow as a factor on average flow.

    Four tabulated points; read between them linearly in log10(Q), flat outside. Stated
    rather than silent: the table is a curve sampled at four decadal-ish flows and any
    reading between them is an interpolation, not a value.
    """
    if q_avg_ls <= TAB16[0][0]:
        return TAB16[0][1]
    if q_avg_ls >= TAB16[-1][0]:
        return TAB16[-1][1]
    for (q0, f0), (q1, f1) in zip(TAB16, TAB16[1:]):
        if q0 <= q_avg_ls <= q1:
            t = (math.log10(q_avg_ls) - math.log10(q0)) / (math.log10(q1) - math.log10(q0))
            return f0 + t * (f1 - f0)
    return TAB16[-1][1]


def station_type(q_duty_ls: float) -> str:
    """G203-p40-41 Tab 17. Transcribed to match contract._cross_field's own boundaries."""
    for cap, name in ST_TYPE_Q:
        if q_duty_ls <= cap:
            return name
    return "Type 3"


def well_volume_m3(q_duty_ls: float, starts_per_h: float) -> float:
    """G203-p48 sec 7.8: minimum live volume V = 0.25 x Q x T, Q in m3/s, T = 3600/starts.

    The 0.25 is not a safety factor. The cycle is longest-per-start when the inflow is half
    the pump capacity, and at that inflow the cycle time is 4V/Q - so V = Q x T / 4 is the
    volume that holds the start rate at its worst inflow, not at its design one.
    """
    return WELL_K * (q_duty_ls / 1000.0) * (3600.0 / starts_per_h)


# ======================================================================================
# Raster sampling. The elevation source is the 0.5 m VRT (project rule 6); the hazard grid
# is Hazard_T50y read exactly as audit.r4 reads it - np.floor(v) >= 4.
# ======================================================================================

class Rasters:
    """Terrain and hazard, opened once. Absent rasters degrade to None and say so - a
    sampler that silently returns nothing is how W10's RoadTreatment no-opped."""

    def __init__(self, terrain=TERRAIN, hazard=HAZARD):
        import rasterio
        self._rio = rasterio
        self.terrain = rasterio.open(terrain) if os.path.exists(terrain) else None
        self.hazard = rasterio.open(hazard) if os.path.exists(hazard) else None
        self.missing = [n for n, p in (("terrain", terrain), ("hazard", hazard))
                        if not os.path.exists(p)]

    def ground(self, xy):
        """Ground level at a sequence of (x, y). NaN where nodata or off-grid."""
        if self.terrain is None:
            return np.full(len(xy), np.nan)
        v = np.array([s[0] for s in self.terrain.sample(xy)], dtype=float)
        nod = self.terrain.nodata
        if nod is not None:
            v[v == nod] = np.nan
        return v

    def on_wadi(self, xy):
        if self.hazard is None:
            return np.zeros(len(xy), dtype=bool)
        v = np.array([s[0] for s in self.hazard.sample(xy)], dtype=float)
        return np.isfinite(v) & (np.floor(v) >= min(WADI_CLASSES))

    def _hazard_ground(self, x, y, r):
        """Ground levels of the T50 hazard cells within r of (x, y). Decimated read - the
        grid is 3 m and 68,000 cells wide, and a flood level does not need every cell."""
        if self.hazard is None:
            return np.array([])
        try:
            hw = self._rio.windows.from_bounds(x - r, y - r, x + r, y + r,
                                               transform=self.hazard.transform)
            side = min(int(2 * r / self.hazard.res[0]) + 1, 300)
            h = self.hazard.read(1, window=hw, boundless=True, fill_value=-9999.0,
                                 out_shape=(side, side)).astype(float)
        except Exception:
            return np.array([])
        rows, cols = np.where(np.floor(h) >= min(WADI_CLASSES))
        if not len(rows):
            return np.array([])
        xs = x - r + (cols + 0.5) * (2 * r / side)
        ys = y + r - (rows + 0.5) * (2 * r / side)
        keep = np.hypot(xs - x, ys - y) <= r
        xs, ys = xs[keep], ys[keep]
        if not len(xs):
            return np.array([])
        if len(xs) > 2000:                     # cap the terrain sampling, keep it spread
            step = len(xs) // 2000 + 1
            xs, ys = xs[::step], ys[::step]
        g = self.ground(list(zip(xs, ys)))
        return g[np.isfinite(g)]

    def flood_level(self, x, y):
        """The FLOOD_LV proxy of PENDING ST-1, in m aOD, with the evidence behind it.

        Returns (level, hazard_found, radius_m). No 1:50 water-surface model exists in the
        project data, so the level is read off the T50 hazard grid in the only two ways the
        grid can honestly be read:

          hazard within r   the HIGHEST GROUND level among the T50 hazard cells found. A
                            cell the model floods has water standing at least at that cell's
                            own ground, so this is a LOWER BOUND on the local surface. The
                            radius widens 100 -> 300 -> 1,000 m and stops at the first hit,
                            so the level comes from the NEAREST flooding, not the worst
                            within a kilometre.
          none within 1 km  the LOWEST ground inside 1 km. The grid says the 1:50 flood does
                            not reach here at all; wherever it is, its surface cannot exceed
                            that point without inundating it first. A station that fails the
                            300 mm rule against this number is sitting in a closed local
                            sump, which is a siting problem in its own right.

        Neither reading is a flood model, and it is not offered as one. It is enough to make
        G203-p38 sec 7.2 bite on a station placed in a wadi margin - the failure it exists
        to catch, because a flooded station is the whole asset lost.
        """
        if self.terrain is None:
            return float("nan"), False, 0.0
        for r in (FLOOD_SEARCH_M, 3.0 * FLOOD_SEARCH_M, 10.0 * FLOOD_SEARCH_M):
            g = self._hazard_ground(x, y, r)
            if g.size:
                return float(np.max(g)), True, r
        r = 10.0 * FLOOD_SEARCH_M
        try:
            win = self._rio.windows.from_bounds(x - r, y - r, x + r, y + r,
                                                transform=self.terrain.transform)
            side = min(int(2 * r / self.terrain.res[0]) + 1, 400)
            z = self.terrain.read(1, window=win, boundless=True,
                                  fill_value=self.terrain.nodata or -9999.0,
                                  out_shape=(side, side)).astype(float)
        except Exception:
            return float("nan"), False, 0.0
        nod = self.terrain.nodata
        if nod is not None:
            z[z == nod] = np.nan
        if not np.isfinite(z).any():
            return float("nan"), False, 0.0
        return float(np.nanmin(z)), False, r

    def close(self):
        for ds in (self.terrain, self.hazard):
            if ds is not None:
                ds.close()


# ======================================================================================
# The flow tree, rebuilt from the published layers. Never from a tolerance.
# ======================================================================================

class Tree:
    """US_NODE / DS_NODE as published, with the node table beside it.

    Two things are computed here that a single layer cannot show on its own: the out-edge
    map from the REACH side, and the same map from the NODE side (`DS_NODE`). They are
    compared, and a disagreement is reported rather than resolved - two independently
    computed numbers agreeing is the only cheap defence against the W10 defect where the
    node and pipe layers came out of different solves.
    """

    def __init__(self, nodes: gpd.GeoDataFrame, reaches: gpd.GeoDataFrame):
        self.nodes = nodes
        self.reaches = reaches.reset_index(drop=True)
        self.N = {}
        for r in nodes.itertuples():
            self.N[str(r.NODE_UID)] = dict(
                uid=str(r.NODE_UID),
                ref=str(getattr(r, "NODE_REF", "") or ""),
                kind=str(getattr(r, "NODE_KIND", "chamber") or "chamber"),
                x=float(r.geometry.x), y=float(r.geometry.y),
                grd=_f(getattr(r, "GRD_M", np.nan)),
                inv=_f(getattr(r, "INV_M", np.nan)),
                nprop=_f(getattr(r, "N_PROP", np.nan)),
                qadf=_f(getattr(r, "Q_ADF_M3D", np.nan)),
                qpk=_f(getattr(r, "Q_PK_LS", np.nan)),
                src=str(getattr(r, "SRC", "draft") or "draft"),
                conf=str(getattr(r, "CONFIDENCE", "derived") or "derived"),
                pkg=str(getattr(r, "PACKAGE", "") or ""),
                phase=int(_f(getattr(r, "PHASE", 0)) or 0),
                ds_claim=str(getattr(r, "DS_NODE", "") or ""),
            )
        self.out = {}          # node uid -> reach row index
        self.inn = {}          # node uid -> [reach row index]
        for i, r in enumerate(self.reaches.itertuples()):
            us, ds = str(r.US_NODE), str(r.DS_NODE)
            self.out.setdefault(us, i)
            self.inn.setdefault(ds, []).append(i)
        # the two independent out-maps, compared
        self.ds_disagree = [u for u, nd in self.N.items()
                            if nd["ds_claim"] != (str(self.reaches.DS_NODE[self.out[u]])
                                                  if u in self.out else "")]

    def ds_of(self, uid):
        i = self.out.get(uid)
        return None if i is None else str(self.reaches.DS_NODE[i])

    def reach(self, uid):
        """The reach LEAVING this node, as a row, or None at a terminal."""
        i = self.out.get(uid)
        return None if i is None else self.reaches.iloc[i]

    def cover_out(self, uid):
        """Cover on the OUTGOING reach at this chamber, recomputed the way audit.h4
        recomputes it - `depth - (DN/1000 + 0.10)`, on the reach's OWN outside diameter.
        Recomputed rather than read from COVER_US so this stage and the auditor cannot
        disagree about what a breach is; W10 used a hardcoded 0.30 m regardless of diameter
        and shipped 45.92 km below minimum cover on the same arithmetic."""
        i = self.out.get(uid)
        if i is None:
            return float("nan")
        r = self.reaches.iloc[i]
        return contract.cover(int(r.DN), _f(r.US_DEPTH))

    def walk(self, uid, max_m=float("inf")):
        """Nodes downstream of `uid`, with the cumulative length to each. Stops at a
        terminal or at `max_m`. Cycle-safe: a forest cannot revisit."""
        out, seen, cur, d = [], {uid}, uid, 0.0
        while True:
            i = self.out.get(cur)
            if i is None:
                return out
            r = self.reaches.iloc[i]
            d += _f(r.LEN_M)
            nxt = str(r.DS_NODE)
            if nxt in seen or nxt not in self.N:
                return out
            out.append((nxt, d, i))
            if d >= max_m:
                return out
            seen.add(nxt)
            cur = nxt

    def is_terminal(self, uid):
        return uid not in self.out

    def upstream_uids(self, uid):
        return [str(self.reaches.US_NODE[i]) for i in self.inn.get(uid, [])]


def _f(v, default=float("nan")):
    try:
        x = float(v)
        return x
    except (TypeError, ValueError):
        return default


# ======================================================================================
# Rung 1 of the ladder - the CAP, with its two distance-bounded exits
# ======================================================================================

def breach_heads(tree: Tree):
    """The most upstream chamber of every run whose cover is over the 12 m cap.

    A chamber is a run HEAD when it breaches and no reach arriving at it comes from a
    chamber that also breaches. That is the point where the depth first became
    uneconomic on this flow path, and it is the point with the smallest accumulated flow
    on the run - which is where a station belongs, because cost tracks power and power is
    Q x H. W10 put its station at the breach itself, on a trunk carrying 36,974 plots.
    """
    breached = {u for u in tree.N
                if tree.cover_out(u) > CAP_COVER_M + CAP_EPS_M}
    heads = []
    for u in breached:
        if not any(p in breached for p in tree.upstream_uids(u)):
            heads.append(u)
    return sorted(heads), breached


def cap_exit(tree: Tree, head: str, breached: set):
    """Which philosophy sec 5 exit lets this run past the cap without a station, if any.

    Returns (exit_token, distance_m) or (None, distance_walked). The exits are alternatives
    and either alone is sufficient:

        recovers_500m   the cover falls back to or below 12 m within 500 m
        outfall_1000m   the run reaches an outfall, an existing station or a tie within
                        1,000 m

    This is also what disposes of W10's 3 mm breach without any tolerance being invented:
    a chamber 3 mm over the cap recovers almost at once, so the first exit takes it.
    """
    walked = 0.0
    for uid, dist, _i in tree.walk(head, max_m=max(EXIT_RECOVER_M, EXIT_OUTFALL_M)):
        walked = dist
        if dist <= EXIT_OUTFALL_M and (
                tree.is_terminal(uid)
                or tree.N[uid]["kind"] in ("outfall", "station", "tie")):
            return "outfall_1000m", dist
        # Recovery is a COVER statement, so it needs a cover. A terminal chamber has no
        # outgoing reach and therefore no cover on one; reading its NaN as "recovered"
        # would let the 500 m exit swallow every run that happens to end nearby, which is
        # the 1,000 m exit's job and is bounded differently on purpose.
        if dist <= EXIT_RECOVER_M and uid not in breached:
            cov = tree.cover_out(uid)
            if np.isfinite(cov) and cov <= CAP_COVER_M + CAP_EPS_M:
                return "recovers_500m", dist
    if tree.is_terminal(head):
        return "outfall_1000m", walked
    return None, walked


# ======================================================================================
# The discharge chamber, the duty and the main
# ======================================================================================

def pick_discharge(tree: Tree, station_uid: str, q_arrive_ls: float, q_avg_ls: float,
                   onward_dn_default: int = 200):
    """Where the rising main lets go, and what that costs. Chosen on TOTAL head.

    The gravity line restarts at MINIMUM COVER at the discharge chamber - that is the whole
    point of pumping - so the delivery level is `ground - min_invert_depth(DN)`, not the
    deep invert the interim levels frame happens to carry there. Candidates are the nodes
    downstream of the station along its own flow path.

    The objective is TOTAL head, not static lift. An earlier version minimised lift alone
    and walked 960 m downhill to save 4.7 m of lift while buying 37 m of friction - it had
    optimised the smaller half of Q x H. Every candidate is therefore sized with
    `size_main()` on its own path length and scored on `static + friction`, which is the
    head the pump actually works against and the number power is proportional to.

    Two bounds, both derived from G203-p50 rather than chosen: retention at the minimum
    permitted velocity puts the preferred search at 1.0 x 1800 = 1,800 m, and at the maximum
    permitted velocity the absolute search ends at 2.5 x 1800 = 4,500 m. A candidate whose
    retention exceeds 30 min is set aside unless nothing else exists, because retention is
    what turns a main into an H2S problem (philosophy sec 6, G203-p50).
    """
    st = tree.N[station_uid]
    good, any_, deepest = None, None, None
    for uid, dist, ri in tree.walk(station_uid, max_m=RM_SEARCH_MAX_M):
        nd = tree.N[uid]
        if not np.isfinite(nd["grd"]):
            continue
        onward = tree.reach(uid)
        dn = int(onward.DN) if onward is not None else onward_dn_default
        deliver = nd["grd"] - contract.min_invert_depth(dn)
        lift = deliver - st["inv"]
        m = size_main(q_arrive_ls, dist, lift, q_avg_ls)
        cand = dict(uid=uid, dist=dist, deliver=deliver, lift=lift, ri=ri,
                    head=m["total"], main=m, beyond_pref=dist > RM_SEARCH_PREF_M)
        if any_ is None or cand["head"] < any_["head"] - 1e-9:
            any_ = cand
        if m["retent_min"] <= RETENT_MAX_MIN and (good is None
                                                  or cand["head"] < good["head"] - 1e-9):
            good = cand
        # The alternative nobody can price yet, carried so the trade is visible. Least head
        # per station tends to pick the NEAREST chamber and therefore to multiply stations,
        # and manning is 86 % of a station's life-cycle cost (W10 DEPTH_VS_PUMPING.md). The
        # candidate on the lowest ground buys the longest gravity restart downstream and so
        # the fewest stations - at more head. Neither can be chosen without NWS's station
        # establishment and manning costs, both open items, so the second is REPORTED.
        if deepest is None or nd["grd"] < tree.N[deepest["uid"]]["grd"] - 1e-9:
            deepest = cand
    pick = good or any_
    if pick is not None and deepest is not None and deepest["uid"] != pick["uid"]:
        pick = dict(pick, alt=deepest)
    return pick


def size_main(q_arrive_ls: float, length_m: float, lift_m: float, q_avg_ls: float):
    """Bore, duty and heads. THE function W10 got wrong, so it is written to be read.

    Four steps, and the second one is the one that matters:

      1. The duty must at least keep up with what arrives.
      2. Of the bores whose velocity at that duty falls inside G203-p50's window
         (1.0 m/s intermittent to 2.5 m/s), take the LARGEST. Largest, because velocity
         squared is friction and friction is head and head is power - and power is what a
         station costs over 25 years (0.99 correlation, W10 research; philosophy objective
         5 is life-cycle, not capital). The first version of this function took the
         smallest bore in the window and produced DN80 with 122 m of friction head against
         a 4.7 m static lift on the self-test. That is a legal design and a ruinous one.
      3. If no bore reaches the minimum velocity at that duty, RAISE THE DUTY to the scour
         flow of the smallest permitted bore. This is the wet-well cycle doing its job: the
         well stores, so the pump rate is not the inflow rate, and G203-p48 sec 7.8 sizes
         the well for exactly that. It is also the fix for W10's actual defect - 17 of its
         25 mains sat under 0.75 m/s because the bore was matched to the arriving gravity
         pipe rather than to a duty. The alternative, accepting 0.16 m/s, builds a main
         that silts in year one.
      4. Re-check, because raising the duty moves the whole window.

    WHAT IS NOT DECIDED HERE. Both ends of the velocity window are legal, and choosing
    between them is a capital-versus-energy trade the project's own cost data will settle
    (Renardet unit rates and the energy tariff are both still open items in 00_CURRENT).
    Least head is the defensible default until they arrive, and V_DUTY_MS travels on the
    row so the trade can be re-run without re-deriving anything.

    `V_MIN_MS` is the Tab 16 deposition check the criteria file marks with a star: the
    velocity floor is held at the DESIGN MINIMUM flow (G203-p50 sec 8.1 with the p40 Tab 16
    factors), which bites on a variable-speed station where the duty can fall.
    """
    q = max(float(q_arrive_ls), 0.0)
    usable = [d for d in RM_DN_SERIES if d >= RM_MIN_ID_MM]
    dn = usable[-1]
    for _ in range(6):
        window = [d for d in usable
                  if v_at(d, q) <= V_RM_MAX + 1e-9
                  and v_at(d, q) >= V_RM_MIN_INTERMITTENT - 1e-9]
        if window:
            dn = max(window)                 # least friction inside the legal window
            break
        if v_at(usable[-1], q) > V_RM_MAX:   # past the largest bore this series carries
            dn = usable[-1]
            break
        dn = usable[0]                       # too slow even at the smallest bore ...
        q_new = q_for_v(dn, V_RM_MIN_INTERMITTENT)   # ... so raise the duty, not the pipe
        if q_new <= q + 1e-9:
            break
        q = q_new
    v = v_at(dn, q)
    s_f = friction_slope(dn, q)
    hf = s_f * float(length_m)
    q_min = tab16_factor(max(q_avg_ls, 1e-9)) * max(q_avg_ls, 0.0)
    bore = rm_bore_m(dn)
    vol = math.pi * bore * bore / 4.0 * float(length_m)
    return dict(
        dn=int(dn),
        q_duty_ls=q,
        duty_raised=q > float(q_arrive_ls) + 1e-9,
        v_duty=v,
        v_min=v_at(dn, q_min) if q_min > 0 else 0.0,
        q_min_ls=q_min,
        hf=hf,
        stat=max(float(lift_m), 0.0),
        total=max(float(lift_m), 0.0) + hf,
        retent_min=(vol / (q / 1000.0) / 60.0) if q > 0 else float("inf"),
        v_window_ok=(V_RM_MIN - 1e-9) <= v <= (V_RM_MAX + 1e-9),
        v_intermittent_ok=v >= V_RM_MIN_INTERMITTENT - 1e-9,
    )


def alignment(tree: Tree, station_uid: str, discharge_uid: str):
    """The rising main follows the corridor the gravity line already occupies.

    No routing engine, and that is deliberate: the reaches between the station and the
    discharge chamber were placed by stage 2 with the wadi and dual-carriageway exclusions
    already applied AT SOURCE (philosophy sec 2), so their corridor is legal by
    construction. Routing a pressure main independently would re-open every exclusion H1
    exists to close.

    Returns (LineString, worst_confidence, src_of_that_reach) or None.
    """
    pts, worst, worst_src, rank = [], None, "draft", -1
    cur = station_uid
    guard = 0
    while cur != discharge_uid and guard < 100000:
        guard += 1
        i = tree.out.get(cur)
        if i is None:
            return None
        r = tree.reaches.iloc[i]
        g = r.geometry
        if g is None or g.is_empty:
            return None
        cs = list(g.coords)
        if pts and math.hypot(pts[-1][0] - cs[0][0], pts[-1][1] - cs[0][1]) < 1e-6:
            cs = cs[1:]
        pts.extend([(c[0], c[1]) for c in cs])
        cf = str(getattr(r, "CONFIDENCE", "derived") or "derived")
        k = contract._CONF_RANK.get(cf, 99)
        if k > rank:
            rank, worst, worst_src = k, cf, str(getattr(r, "SRC", "draft") or "draft")
        cur = str(r.DS_NODE)
    if len(pts) < 2:
        return None
    return LineString(pts), (worst or "derived"), worst_src


def valve_counts(rasters: Rasters, line: LineString):
    """Air valves at summits, washouts at low points (G203-p53-54 sec 8.4).

    The main sits at constant cover under the ground, so its profile IS the ground profile.
    A turning point counts only when it stands SUMMIT_PROM_M clear of its neighbours - 1.0 m,
    which is the guideline's own flattest rising grade over its own valve spacing, not a
    number picked to quiet a noisy DEM. Ends are excluded: the wet well and the discharge
    chamber are structures, not valve chambers.

    Also returned: the in-line isolation valve count at the 500 m spacing of the same
    clause, capped at 800 m, so the schedule does not have to re-derive it.
    """
    L = line.length
    n = max(int(L // PROFILE_STEP_M) + 1, 2)
    ds = np.linspace(0.0, L, n)
    xy = [(p.x, p.y) for p in (line.interpolate(d) for d in ds)]
    z = rasters.ground(xy)
    ok = np.isfinite(z)
    if ok.sum() < 3:
        return 0, 0, 0, 0.0
    z, ds = z[ok], ds[ok]
    n_air = n_wash = 0
    i = 1
    last_ext = z[0]
    while i < len(z) - 1:
        if z[i] >= z[i - 1] and z[i] >= z[i + 1] and (z[i] - last_ext) >= SUMMIT_PROM_M:
            n_air += 1
            last_ext = z[i]
        elif z[i] <= z[i - 1] and z[i] <= z[i + 1] and (last_ext - z[i]) >= SUMMIT_PROM_M:
            n_wash += 1
            last_ext = z[i]
        i += 1
    n_iso = int(math.ceil(L / VALVE_SPACING_M)) - 1 if L > VALVE_SPACING_M else 0
    return n_air, n_wash, max(n_iso, 0), float(np.nanmax(z) - np.nanmin(z))


# ======================================================================================
# Published numbers - one function each (P2). Seven station counts are in circulation from
# this project (19, 21, 25, 37, 140, 184, 239) because each was computed at the point of
# reporting. A second definition of either name raises here instead of in a meeting.
# ======================================================================================

@contract.published("station_count", "-", "s7_stations, cap-and-veto ladder")
def station_count(stations: pd.DataFrame) -> int:
    return int(len(stations))


@contract.published("station_total_lift_m", "m", "s7_stations, sum of LIFT_M")
def station_total_lift(stations: pd.DataFrame) -> float:
    """Total lift, not the count. 00_CURRENT: the count moves 19-21 with the funnel while
    the lift does not, because distance-clustering measures breach density, not pumping."""
    return float(pd.to_numeric(stations["LIFT_M"], errors="coerce").fillna(0.0).sum())


@contract.published("rising_main_km", "km", "s7_stations, sum of LEN_M")
def rising_main_km(rms: pd.DataFrame) -> float:
    return float(pd.to_numeric(rms["LEN_M"], errors="coerce").fillna(0.0).sum()) / 1000.0


@contract.published("duty_x_lift_ls_m", "L/s.m", "s7_stations, sum of Q_DUTY_LS x LIFT_M")
def duty_x_lift(stations: pd.DataFrame) -> float:
    """Q x H - the quantity station cost tracks at 0.99 (W10 DEPTH_VS_PUMPING.md).

    Not kW: that needs a pump efficiency and a density, and neither is a guideline value.
    But it is the right thing to compare two layouts on, and it is the reason a station
    belongs at the HEAD of a breach run where Q is smallest. It goes through `published`
    like every other number this stage reports - a metric computed inline at the point of
    reporting is precisely how seven station counts got into circulation.
    """
    q = pd.to_numeric(stations["Q_DUTY_LS"], errors="coerce").fillna(0.0)
    h = pd.to_numeric(stations["LIFT_M"], errors="coerce").fillna(0.0)
    return float((q * h).sum())


# ======================================================================================
# The stage
# ======================================================================================

def load_layers(root: str, gpkg: str = "W11a.gpkg", nodes_path=None, reaches_path=None):
    """Read the levels stage's frame. Missing input is reported, never worked around."""
    waiting = []
    p = contract.gpkg_path(root, gpkg)
    have = set()
    if os.path.exists(p):
        try:
            have = set(gpd.list_layers(p)["name"].tolist())
        except Exception:
            have = set()

    def rd(name, override):
        if override:
            return gpd.read_file(override) if os.path.exists(override) else None
        if name in have:
            return gpd.read_file(p, layer=name)
        return None

    nodes = rd("nodes", nodes_path)
    reaches = rd("reaches", reaches_path)
    if nodes is None:
        waiting.append(f"layer 'nodes'   - s5_chambers publishes it, s6_levels re-publishes "
                       f"it with INV_M and DEPTH_M. Looked in {p}")
    if reaches is None:
        waiting.append(f"layer 'reaches' - s6_levels publishes it. Looked in {p}")
    return nodes, reaches, waiting


def run(root: str, nodes: gpd.GeoDataFrame, reaches: gpd.GeoDataFrame,
        rasters: Rasters, manifest_path=None, mirror=True):
    """Place the stations, design the mains, publish both layers."""
    with contract.Manifest.stage(STAGE, 7, path=manifest_path) as rec:
        rec.read("nodes", "", len(nodes))
        rec.read("reaches", "", len(reaches))
        if rasters.missing:
            rec.note("rasters absent: " + ", ".join(rasters.missing)
                     + " - FLOOD_LV and the valve counts degrade to blanks and every "
                       "affected station is reported, not dropped")

        # Inputs are validated for PRESENCE, not for value. s7's normal input is an interim
        # levels frame that legitimately still carries unexcused cap breaches - that is the
        # thing it exists to consume - and a strict re-validation here would refuse the one
        # frame the stage is for. The missing-field gate still bites.
        contract.validate(nodes, "nodes", stage=STAGE, strict=False)
        contract.validate(reaches, "reaches", stage=STAGE, strict=False)

        tree = Tree(nodes, reaches)
        if tree.ds_disagree:
            rec.note(f"{len(tree.ds_disagree):,} nodes: DS_NODE on the node layer disagrees "
                     "with the reach layer's own out-edge. Two independently computed "
                     "numbers were meant to agree; in W10 they did not and the depth "
                     "difference reached 10.39 m. Reported, not resolved here.")

        heads, breached = breach_heads(tree)
        fun = rec.funnel("cap breaches -> stations", len(heads))

        # ---- rung 1: the cap, with its exits ------------------------------------------
        placed, exits = [], {"recovers_500m": [], "outfall_1000m": []}
        for h in heads:
            tok, dist = cap_exit(tree, h, breached)
            if tok:
                exits[tok].append(h)
            else:
                placed.append(h)
        for tok, ids in exits.items():
            if ids:
                fun.drop(f"philosophy sec 5 exit '{tok}' applies", ids=ids)

        # ---- consolidation: a station removes the depth on everything below it ---------
        # A run head that lies downstream of a station already placed will not be deep once
        # the levels re-solve runs, so it is not a second station. It is suppressed here and
        # COUNTED, and the re-solve either confirms it or hands it back on the next pass.
        #
        # WHICH station relieves it is recorded rather than just the fact of relief, because
        # the relief is only real if that station is actually BUILT - and the build loop
        # below can still withhold it on siting (flood, no corridor, no arriving flow). A
        # relief attributed to a station that was then withheld is an unresolved H4 breach
        # wearing a funnel reason, which is the W10 class of failure exactly. So the funnel
        # drop is deferred until the build loop has said which stations survived.
        relieved_by = {}
        placed_set = set(placed)
        for s in placed:
            for uid, _d, _i in tree.walk(s, max_m=float("inf")):
                if uid in placed_set and uid not in relieved_by:
                    relieved_by[uid] = s
        placed = [s for s in placed if s not in relieved_by]

        # ---- rung 2 (VETO) and rung 3 (ECONOMICS): declared, never faked ---------------
        rec.note("ladder rung 2 (VETO - a chamber that cannot be maintained: no plant "
                 "access, confined space with no rescue route, under a live carriageway) "
                 "contributed 0 stations BECAUSE ITS INPUT IS ABSENT. No access or "
                 "maintainability assessment exists in the project data. Invariant 10: a "
                 "stage may do nothing, it may not do nothing quietly.")
        rec.note("ladder rung 3 (ECONOMICS - is a station cheaper over 25 years than "
                 "digging on) contributed 0 stations BECAUSE ITS INPUT IS ABSENT. NWS's "
                 "station establishment cost is an open item in philosophy sec 5 and in "
                 "00_CURRENT. Rungs 1 and 2 can only ADD a station; the economics can only "
                 "make you pump EARLIER, never later, so its absence cannot have removed "
                 "one - it can only have left one un-brought-forward.")
        rec.note("WHY='commissioning' (P8, a station that makes its package independently "
                 "buildable) is not decided here. Package seams are stage 8's; this stage "
                 "would be inventing them.")

        # ---- build each station and its main -------------------------------------------
        st_rows, rm_rows, findings = [], [], []
        dropped_flood, dropped_wadi, dropped_geom = [], [], []
        for k, uid in enumerate(sorted(placed), start=1):
            nd = tree.N[uid]
            q_arr0 = nd["qpk"]
            if not np.isfinite(q_arr0):
                r_in0 = tree.reach(uid)
                q_arr0 = _f(getattr(r_in0, "QPK_LS", np.nan)) if r_in0 is not None else np.nan
            q_avg0 = nd["qadf"] * 1000.0 / 86400.0 if np.isfinite(nd["qadf"]) else 0.0
            if not np.isfinite(q_arr0):
                dropped_geom.append(uid)
                findings.append(f"{uid}: no peak flow on the node or its outgoing reach - "
                                "a duty cannot be derived and will not be assumed.")
                continue
            disc = pick_discharge(tree, uid, q_arr0, q_avg0)
            if disc is None:
                dropped_geom.append(uid)
                findings.append(f"{uid}: no downstream chamber inside "
                                f"{RM_SEARCH_MAX_M:,.0f} m with a usable ground level - "
                                "the run has nowhere to discharge to. Philosophy sec 3: the "
                                "answer is a re-route or a plot not served, not a longer main.")
                continue
            al = alignment(tree, uid, disc["uid"])
            if al is None:
                dropped_geom.append(uid)
                findings.append(f"{uid}: the gravity path to {disc['uid']} has a broken or "
                                "empty geometry, so no corridor exists to lay the main in.")
                continue
            line, conf, src = al

            # Re-sized on the ALIGNMENT length, not the cumulative LEN_M the search scored
            # on. The two differ by the geometry's own sinuosity, and every published
            # length, head and retention has to describe the line that was actually drawn.
            m = size_main(q_arr0, line.length, disc["lift"], q_avg0)
            q_arr = q_arr0
            typ = station_type(m["q_duty_ls"])
            well = well_volume_m3(m["q_duty_ls"], WW_STARTS_PER_H)

            flood, hz, fr = rasters.flood_level(nd["x"], nd["y"])
            grd = nd["grd"]
            if not np.isfinite(grd):
                grd = float(rasters.ground([(nd["x"], nd["y"])])[0])
            if not np.isfinite(flood) or not np.isfinite(grd):
                dropped_flood.append(uid)
                findings.append(
                    f"BLOCKING {uid}: no terrain or hazard cover here, so neither the "
                    "ground level nor the 1:50 flood proxy can be derived. G203-p38 sec 7.2 "
                    "is a mandatory siting check and a station is not published with an "
                    "invented level beside it.")
                continue
            if grd < flood + FLOOD_FREEBOARD_M:
                dropped_flood.append(uid)
                findings.append(
                    f"BLOCKING {uid}: ground {grd:.2f} m is less than "
                    f"{FLOOD_FREEBOARD_M:.2f} m above the 1:50 flood proxy {flood:.2f} m "
                    + (f"(T50 hazard ground within {fr:.0f} m)" if hz
                       else f"(no T50 hazard within {fr:.0f} m; the proxy is the local low "
                            "point, so this chamber sits in a sump)")
                    + ". G203-p38 sec 7.2 puts the floor, the transformers and the "
                    "generator above that level. This is a SITING failure and the fix is "
                    "the site, not the level - the station is withheld from the layer, so "
                    "the cap breach it was to resolve stands and H4 will report it.")
                continue

            # H1 is "no pipe or CHAMBER in a wadi", and a wet well is the largest chamber on
            # the network. The flood check above catches most wadi sites incidentally, but
            # not all - a hazard cell whose own ground sits below the station's still passes
            # the 300 mm freeboard - and H1 is a hard constraint with no exit, so it is
            # tested directly rather than left to a proxy. Same resolution as the flood
            # failure: withhold, name it, and let the breach stand.
            if bool(rasters.on_wadi([(nd["x"], nd["y"])])[0]):
                dropped_wadi.append(uid)
                findings.append(
                    f"BLOCKING {uid}: the station chamber falls on wadi ground "
                    f"(Hazard_T50y class >= {min(WADI_CLASSES)}). H1 admits no pipe or "
                    "chamber in a wadi and has no exit, so this is a SITING failure, not a "
                    "level to raise. The station is withheld and the cap breach it was to "
                    "resolve stands.")
                continue

            n_air, n_wash, n_iso, relief = valve_counts(rasters, line)
            rm_uid = f"RM{k:04d}"

            st_rows.append(dict(
                NODE_UID=uid,
                NODE_REF=nd["ref"] or f"{nd['pkg'] or 'P0'}-PS-{k:03d}",
                WHY="cap",
                ST_TYPE=typ,
                Q_DUTY_LS=round(m["q_duty_ls"], 3),
                LIFT_M=round(m["stat"], 3),
                N_PROP=nd["nprop"] if np.isfinite(nd["nprop"]) else 0.0,
                Q_ADF_M3D=nd["qadf"] if np.isfinite(nd["qadf"]) else 0.0,
                WELL_M3=round(well, 3),
                WW_STARTS=WW_STARTS_PER_H,
                GRD_M=round(grd, 3),
                FLOOD_LV=round(flood, 3),
                LAND_M2=LAND_M2[typ],
                RM_EDGE=rm_uid,
                SRC=nd["src"], CONFIDENCE=nd["conf"], STAGE=STAGE,
                PACKAGE=nd["pkg"], PHASE=nd["phase"],
                geometry=Point(nd["x"], nd["y"]),
            ))
            rm_rows.append(dict(
                EDGE_UID=rm_uid, US_NODE=uid, DS_NODE=disc["uid"], STATION=uid,
                DN=m["dn"], MATERIAL=RM_MATERIAL,
                LEN_M=round(line.length, 3),
                Q_DUTY_LS=round(m["q_duty_ls"], 3),
                V_DUTY_MS=round(m["v_duty"], 3),
                V_MIN_MS=round(m["v_min"], 3),
                STAT_HD_M=round(m["stat"], 3),
                TOT_HD_M=round(m["total"], 3),
                RETENT_M=round(m["retent_min"], 2),
                N_AIRV=int(n_air), N_WASH=int(n_wash),
                SEPTIC_FL=1,
                SRC=src, CONFIDENCE=conf, STAGE=STAGE,
                PACKAGE=nd["pkg"], PHASE=nd["phase"],
                geometry=line,
            ))

            if disc["lift"] < -1e-6:
                findings.append(
                    f"{uid}: the minimum-cover restart at {disc['uid']} sits "
                    f"{-disc['lift']:.2f} m BELOW the arriving invert, so the static lift "
                    "is zero and the main works against friction alone. Gravity would do "
                    f"this if the run could be dug, but {disc['dist']:,.0f} m is past the "
                    f"{EXIT_RECOVER_M:,.0f} m the sec 5 recovery exit allows. Check the "
                    "re-route before accepting a pumped bypass (philosophy sec 3: a "
                    "station, a drop, a re-route, or not serving).")
            if m["duty_raised"]:
                findings.append(
                    f"{uid}: duty raised from the arriving {q_arr:,.2f} to "
                    f"{m['q_duty_ls']:,.2f} L/s so DN{m['dn']} scours at "
                    f"{m['v_duty']:.2f} m/s. The wet well carries the difference "
                    "(G203-p48 sec 7.8) - this is the W10 failure, inverted.")
            if not m["v_window_ok"]:
                findings.append(
                    f"BLOCKING {uid}: DN{m['dn']} runs at {m['v_duty']:.2f} m/s at duty, "
                    f"outside the {V_RM_MIN}-{V_RM_MAX} m/s window of G203-p50. No bore in "
                    "the series and no duty the wet well can carry puts it inside; that is "
                    "a layout answer, not a pipe answer.")
            elif not m["v_intermittent_ok"]:
                findings.append(
                    f"{uid}: DN{m['dn']} runs at {m['v_duty']:.2f} m/s - above the 0.75 m/s "
                    f"continuous floor but below the {V_RM_MIN_INTERMITTENT:.2f} m/s "
                    "G203-p50 gives for INTERMITTENT flow, which is what a level-controlled "
                    "wet well produces.")
            if m["hf"] > m["stat"] and m["stat"] >= 0.0:
                findings.append(
                    f"{uid}: friction {m['hf']:.1f} m against a static lift of "
                    f"{m['stat']:.1f} m over {line.length:,.0f} m - the MAIN is the cost "
                    "here, not the lift. Two computed numbers, no threshold: it is worth "
                    "testing a shorter main to a nearer discharge chamber, or a second "
                    "station, before this is priced. Pipe cost and the energy tariff are "
                    "both open items, so the trade cannot be closed here.")
            if m["retent_min"] > RETENT_MAX_MIN:
                findings.append(
                    f"{uid}: retention {m['retent_min']:.1f} min exceeds the 30 min of "
                    "G203-p50. Septicity is a design driver (philosophy sec 6); the "
                    "discharge chamber at "
                    f"{disc['uid']} needs the p55 sec 8.5 treatment sized, not noted.")
            if m["v_min"] < V_RM_MIN and m["q_min_ls"] > 0:
                findings.append(
                    f"{uid}: at the Tab 16 design minimum flow ({m['q_min_ls']:.2f} L/s) "
                    f"the main runs at {m['v_min']:.2f} m/s. Fixed-speed pumping holds "
                    f"{m['v_duty']:.2f} m/s whenever the pump runs, so this bites only if "
                    "the station is variable-speed (G203-p50 sec 8.1 with p40 Tab 16).")
            alt = disc.get("alt")
            if alt is not None:
                findings.append(
                    f"{uid}: least-head discharge is {disc['uid']} at "
                    f"{disc['dist']:,.0f} m and {disc['head']:.1f} m of head. The lowest "
                    f"ground in range is {alt['uid']} at {alt['dist']:,.0f} m and "
                    f"{alt['head']:.1f} m - more head, but a deeper restart, so gravity "
                    "runs further before the next station. Least head is the default "
                    "because it is the half that can be computed; manning is 86 % of a "
                    "station's life-cycle cost and NWS's establishment cost is still an "
                    "open item, so the count-versus-head trade is not closed here.")
            if disc["beyond_pref"]:
                findings.append(
                    f"{uid}: discharge chamber {disc['uid']} is {disc['dist']:,.0f} m away, "
                    f"beyond the {RM_SEARCH_PREF_M:,.0f} m that 30 min retention at "
                    f"{V_RM_MIN_INTERMITTENT:.2f} m/s allows.")
            if np.isfinite(nd["nprop"]) and nd["nprop"] < SLS_MIN_PLOTS:
                findings.append(
                    f"{uid}: {nd['nprop']:.0f} properties upstream, under the "
                    f"{SLS_MIN_PLOTS:.0f} of CLAUDE.md rule 9. Reported only - the breach is "
                    "real, so the pocket is a candidate for absorption at detail design, "
                    "not a station to delete here.")

        if dropped_flood:
            fun.drop("no site clear of the 1:50 flood proxy (G203-p38 sec 7.2) - siting "
                     "decision required", ids=dropped_flood)
        if dropped_wadi:
            fun.drop("station chamber falls on wadi ground, Hazard_T50y classes "
                     f"{WADI_CLASSES} (H1) - siting decision required", ids=dropped_wadi)
        if dropped_geom:
            fun.drop("no usable discharge chamber, corridor or arriving flow",
                     ids=dropped_geom)

        # The deferred relief drop, now that the build loop has said which stations exist.
        built = {r["NODE_UID"] for r in st_rows}
        kept = sorted(u for u, s in relieved_by.items() if s in built)
        orphan = sorted(u for u, s in relieved_by.items() if s not in built)
        if kept:
            fun.drop("relieved by a station further upstream on the same flow path "
                     "(confirmed or reinstated by the levels re-solve)", ids=kept)
        if orphan:
            fun.drop("suppressed as relieved, but the relieving station was WITHHELD - the "
                     "cap breach stands and nothing resolves it", ids=orphan)
            for u in orphan:
                findings.append(
                    f"BLOCKING {u}: this cap breach run was suppressed because a station at "
                    f"{relieved_by[u]} would have relieved it, and {relieved_by[u]} was then "
                    "withheld (see the funnel). So nothing resolves this run: an H4 breach "
                    "with no philosophy sec 5 exit and no station. The answer is one of the "
                    f"four physical ones (sec 3) - a site for {relieved_by[u]}, a re-route, "
                    "a drop, or not serving the run - never a relaxation.")
        fun.close(len(st_rows))

        # ---- cascade, reported (CLAUDE.md rule 9) -------------------------------------
        cascades = []
        for a in st_rows:
            for uid, d, _i in tree.walk(a["NODE_UID"], max_m=SLS_CASCADE_M):
                if any(b["NODE_UID"] == uid for b in st_rows):
                    cascades.append((a["NODE_UID"], uid, round(d)))
        if cascades:
            rec.note(f"{len(cascades)} station pairs sit within {SLS_CASCADE_M:,.0f} m along "
                     "the network - CLAUDE.md rule 9 lets detail design cascade one into "
                     f"the other: {cascades[:6]}")

        # ---- publish ------------------------------------------------------------------
        st = rm = None
        if not st_rows:
            # A legitimate answer, and one that has to be SAID. `did_nothing` is the
            # contract's only way of saying it - a stage that writes nothing and stays
            # silent raises, because that is what W10's RoadTreatment did.
            rec.did_nothing(
                f"{len(heads):,} cap breach runs found and every one was disposed of by a "
                "philosophy sec 5 exit or withheld for a named reason - see the funnel. No "
                "station is a legitimate answer here and it is being stated, not implied.")
        else:
            st = gpd.GeoDataFrame(st_rows, geometry="geometry", crs=contract.CRS_EPSG)
            rm = gpd.GeoDataFrame(rm_rows, geometry="geometry", crs=contract.CRS_EPSG)

            p1 = contract.publish(st, "stations", root, stage=STAGE)
            p2 = contract.publish(rm, "rising_mains", root, stage=STAGE)
            rec.wrote("stations", p1, len(st))
            rec.wrote("rising_mains", p2, len(rm))
            if mirror:
                contract.mirror_shapefile(st, "stations", root)
                contract.mirror_shapefile(rm, "rising_mains", root)

            rec.metric("station_count", contract.value("station_count", st))
            rec.metric("station_total_lift_m",
                       round(contract.value("station_total_lift_m", st), 2))
            rec.metric("rising_main_km", round(contract.value("rising_main_km", rm), 3))
            rec.metric("duty_x_lift_ls_m", round(contract.value("duty_x_lift_ls_m", st), 1))

            # The directive. Without it the next reader assumes the levels on disk account
            # for these stations, and they do not.
            rec.note("RE-SOLVE REQUIRED. The levels stage must now re-run with every "
                     "station NODE_UID as a terminal (kind='station', no outgoing gravity "
                     "reach) and every rising-main DS_NODE as a head restarting at "
                     "min_invert_depth(DN) below ground. Until it does, `nodes` and "
                     "`reaches` on disk still describe the un-pumped design and H4 will "
                     "still report the breaches these stations resolve. Re-run s7 "
                     "afterwards; the loop has converged when it places no new station.")
        for pid, title, why in PENDING:
            rec.note(f"PENDING {pid} - {title}: {why}")

    # OUTSIDE the context manager on purpose: Manifest.stage appends its record in a
    # `finally`, so a report printed inside the block would omit the stage that just ran.
    print(contract.Manifest.report())
    return st, rm, findings


# ======================================================================================
# Self-test - a synthetic network, so the arithmetic and the contract round trip are
# proved without a real design existing and without writing anything into W11a/shp.
# ======================================================================================

def _synthetic(root: str, rasters: "Rasters"):
    """A chain that deepens past the cap and never recovers.

    Built through `contract.Network`, so the nodes and the reaches come from ONE graph and
    the geometry is generated from node coordinates - the same construction the real stages
    use. The chain sits in the real study area and its GROUND LEVELS ARE THE REAL TERRAIN,
    sampled from the 0.5 m VRT (project rule 6). That matters: a synthetic frame carrying
    invented ground over real ground makes the flood check answer a question nobody asked,
    and the first run of this self-test failed for exactly that reason.

    The invert is then laid at a fixed 0.35 % (above Table 11's 0.205 % for DN400) from a starting
    cover of 8.6 m, so the cover walks past the 12 m cap partway along and never comes back
    - the one case the sec 5 exits do not dispose of, which is what a station is for.
    """
    net = contract.Network()
    x0, y0 = 447000.0, 2566000.0
    dn = 400                              # GRP above DN315, so no G203-p22 Tab 6 material
                                          # conflict on a sub main (contract OPEN-2)
    reach_len, n = 120.0, 26

    xy = [(x0 + reach_len * i, y0) for i in range(n)]
    g_real = rasters.ground(xy)
    if not np.isfinite(g_real).all():
        raise RuntimeError("the self-test chain falls outside the terrain VRT - move it")
    cover0 = 8.6
    uids = []
    for i in range(n):
        g = float(g_real[i])
        inv = g - (cover0 + 0.0030 * reach_len * i) - (dn / 1000.0 + 0.10)
        kind = "head" if i == 0 else ("outfall" if i == n - 1 else "chamber")
        uids.append(net.node(xy[i][0], xy[i][1], kind=kind, tier="sub main",
                             grd_m=g, inv_m=inv, stage="T", src="draft",
                             confidence="drafted"))
    for i in range(n - 1):
        net.add_edge(uids[i], uids[i + 1], stage="T", tier="sub main",
                     src="draft", confidence="drafted")

    nd = net.to_nodes_gdf()
    ed = net.to_edges_gdf()

    # node fields the levels stage would have written
    inv = nd.INV_M.to_numpy()
    grd = nd.GRD_M.to_numpy()
    nd["COVER_M"] = grd - inv - (dn / 1000.0 + 0.10)
    nd["INLET_DEG"] = 180.0
    nd["INLET_FLAG"] = 0
    nd["DROP_M"] = 0.0
    nd["DROP_TYPE"] = "none"
    nd["VORTEX"] = 0
    nd["Q_ADF_M3D"] = np.linspace(40.0, 900.0, len(nd))
    nd["N_PROP"] = np.linspace(50.0, 1100.0, len(nd))
    nd["PAST_CAP"] = (nd.COVER_M > CAP_COVER_M).astype(int)
    nd["CAP_EXIT"] = ""
    pf = 2.2
    nd["Q_PK_LS"] = nd.Q_ADF_M3D * 1000.0 / 86400.0 * pf + 0.5

    us = ed.US_NODE.map(dict(zip(nd.NODE_UID, range(len(nd)))))
    ed["DN"] = dn
    ed["MATERIAL"] = C.material(dn)
    ed["SLOPE_LAID"] = 0.35                      # 0.35 %, the gradient the inverts were laid at
    ed["SLOPE_MIN"] = round(C.TABLE11[dn] * 100.0, 4)
    ed["GRAD_BY"] = "ground"
    ed["SIZED_BY"] = "capacity"
    ed["CLEAN_BY"] = "velocity"
    ed["TAU_PA"] = C.TAU_PA
    ed["INV_UP"] = nd.INV_M.to_numpy()[us.to_numpy()]
    ed["INV_DN"] = nd.INV_M.to_numpy()[us.to_numpy() + 1]
    ed["US_DEPTH"] = (nd.GRD_M - nd.INV_M).to_numpy()[us.to_numpy()]
    ed["DS_DEPTH"] = (nd.GRD_M - nd.INV_M).to_numpy()[us.to_numpy() + 1]
    ed["COVER_US"] = ed.US_DEPTH - (dn / 1000.0 + 0.10)
    ed["COVER_DN"] = ed.DS_DEPTH - (dn / 1000.0 + 0.10)
    ed["QADF_M3D"] = nd.Q_ADF_M3D.to_numpy()[us.to_numpy()]
    ed["QINF_LS"] = 0.5
    ed["PF"] = pf
    ed["PF_METH"] = "merrimack"
    ed["QPK_LS"] = ed.QADF_M3D * 1000.0 / 86400.0 * pf + ed.QINF_LS
    ed["V_PK_MS"] = 1.0
    ed["DOD_PK"] = 0.4
    ed["RET_MIN"] = 2.0
    ed["PAST_CAP"] = (ed.COVER_US > CAP_COVER_M).astype(int)
    ed["CAP_EXIT"] = ""
    ed["CAP_LEN_M"] = 0.0
    ed["TIE_TYPE"] = "none"
    ed["ON_DUAL_M"] = 0.0
    ed["ON_WADI_M"] = 0.0
    ed["CROSS_ID"] = ""

    # presence gate only - this frame is deliberately an INTERIM one carrying unexcused
    # breaches, which is exactly what s7 exists to consume
    contract.validate(nd, "nodes", stage="synthetic", strict=False)
    contract.validate(ed, "reaches", stage="synthetic", strict=False)
    os.makedirs(os.path.join(root, "shp"), exist_ok=True)
    p = contract.gpkg_path(root)
    nd.to_file(p, layer="nodes", driver="GPKG")
    ed.to_file(p, layer="reaches", driver="GPKG")
    return nd, ed


def self_test(root: str):
    print(f"self-test root: {root}  (outside the repo - nothing here is a design artefact)")
    r = Rasters()
    try:
        nd, ed = _synthetic(root, r)
        print(f"synthetic frame: {len(nd)} nodes, {len(ed)} reaches, "
              f"{int((ed.COVER_US > CAP_COVER_M).sum())} reaches past the "
              f"{CAP_COVER_M:.0f} m cap, ground sampled from the 0.5 m VRT")
        st, rm, findings = run(root, nd, ed, r,
                               manifest_path=os.path.join(root, "run", "manifest.json"),
                               mirror=False)
    finally:
        r.close()
    if st is None:
        print("\nno station placed - see the funnel above")
        return
    print("\n--- stations ---")
    print(contract.schedule_frame(st, "stations", stage=STAGE).to_string(index=False))
    print("\n--- rising mains ---")
    print(contract.schedule_frame(rm, "rising_mains", stage=STAGE).to_string(index=False))
    # prove the published layers still resolve against the node layer
    for col in ("US_NODE", "DS_NODE", "STATION"):
        bad = ~rm[col].isin(nd.NODE_UID)
        assert not bad.any(), f"{col} does not resolve against the node layer"
    assert st.NODE_UID.isin(nd.NODE_UID).all(), "station is not a registered chamber"
    print("\nreferential integrity: every US_NODE / DS_NODE / STATION resolves to a chamber")
    # The round trip that matters: re-read what was WRITTEN and put it back through the
    # contract at full strictness. Passing in memory is not passing - W10's flow tree was
    # correct in memory and the shapefile it wrote shipped in 7,919 pieces.
    gp = contract.gpkg_path(root)
    contract.validate(gpd.read_file(gp, layer="stations"), "stations", stage="round-trip")
    contract.validate(gpd.read_file(gp, layer="rising_mains"), "rising_mains",
                      stage="round-trip")
    print("round trip: both layers re-read from the GeoPackage and re-validated at "
          "strict=True - G203-p40 Tab 17 type/duty, p43 Tab 21 land, p48 sec 7.8 wet well, "
          "p38 sec 7.2 flood and the p50 velocity window all recomputed by the contract")
    if findings:
        print("\n--- findings ---")
        for f in findings:
            print("  " + f)


# ======================================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=W11A, help="iteration root holding shp/ and run/")
    ap.add_argument("--nodes", default=None, help="override the nodes layer path")
    ap.add_argument("--reaches", default=None, help="override the reaches layer path")
    ap.add_argument("--self-test", action="store_true",
                    help="run against a synthetic network in the scratch root")
    ap.add_argument("--scratch",
                    default=os.path.join(tempfile.gettempdir(), "w11a_s7_selftest"),
                    help="where the self-test writes; deliberately outside the repo so a "
                         "synthetic frame can never be mistaken for a design output")
    a = ap.parse_args(argv)

    print(f"{STAGE}  |  contract {contract.CONTRACT_VERSION}")
    print("pending assumptions carried by this stage:")
    for pid, title, _why in PENDING:
        print(f"  {pid}  {title}")
    print()

    if a.self_test:
        self_test(a.scratch)
        return 0

    nodes, reaches, waiting = load_layers(a.root, nodes_path=a.nodes, reaches_path=a.reaches)
    if waiting:
        print("WAITING ON AN UPSTREAM STAGE - nothing written.\n")
        for w in waiting:
            print("  needs " + w)
        print("\nThis stage reads the levels stage's frame (nodes + reaches with DN, "
              "US_DEPTH/DS_DEPTH, LEN_M, QPK_LS, GRD_M/INV_M) and decides where the "
              "cap-and-veto ladder puts a lifting station. Build order: "
              "W10/docs/research/W11a_BUILD_BRIEF.md stages 2-6 come first.\n"
              "  python s7_stations.py --self-test   proves this module end to end now")
        return 0

    r = Rasters()
    try:
        st, rm, findings = run(a.root, nodes, reaches, r)
    finally:
        r.close()
    if findings:
        print("\n--- findings ---")
        for f in findings:
            print("  " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
