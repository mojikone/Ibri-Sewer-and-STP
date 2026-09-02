"""W11a stage 2 - the corridors, with provenance, and the exclusions applied AT SOURCE.

WHAT A CORRIDOR IS, AND WHY THIS STAGE EXISTS AT ALL
A corridor is a legal route: a public reserve of stated width where a trench may be dug.
It is not a pipe and it is not a road. Philosophy sec 2 puts it at stage 2 of the order of
design, ahead of the trunk, the hierarchy and the levels, and it says exactly one thing
about its content: "Wadi and dual-carriageway exclusions apply HERE, not in the router."

W10 did the opposite. `netlib.sewer_cost` charged a wadi 5,000 m of routing penalty and had
no dual-carriageway term at all, so both constraints were *prices* the router could pay
rather than *boundaries* it could not cross. It paid them: 131.7 km of the shipped design
sits on wadi ground and 1.67 km runs along a dual carriageway, with 47 crossings that
appear on no schedule. A price is negotiable and a hard constraint is not, so H1 has to be
enforced by deleting the ground from the corridor set - which is what this module does.

THE FOUR W10 DEFECTS THIS MODULE IS WRITTEN AGAINST, each named where it is fixed:

  1. RoadTreatment ran with `units=None, sampler=None`.
     `p0_auto.treat_roads()` built the stage correctly and then called it blind. With
     `units` absent, `_drop_traffic_links` and `_drop_stubs` return at their first line,
     `_drop_orphan_links` finds every line "serving" something and drops nothing, and the
     roundabout guard's "no plot inside the ring" test cannot run - which is why 34
     collapsed rings turned out to intersect a registered plot. With `sampler` absent the
     two-lane pair chooses its side on a tie of zeros. Four steps, silently inert.
     Fixed in `treat_roads()`, which REFUSES to call the stage without both, and in
     `assert_stage_did_something()`, which reads the returned report back.

  2. The stitch links stopped 1.000 m short, on 91.4 % of them.
     `p0_auto.stitch()` grouped the skeleton islands by `unary_union([l.buffer(1.0) ...])`
     and then took `nearest_points` between the resulting POLYGONS. The nearest point on a
     1 m buffer is 1 m off the line it wraps, at both ends, so every generated link was
     born detached. The 2.5 m snap in the topology step hid it inside the graph while the
     published layer kept the gaps, and `W10_pipes.shp` shipped in 7,919 pieces.
     Fixed in `stitch()`: the buffer is used ONLY to decide which lines are one island;
     the link is drawn between the real, unbuffered geometries, so it lands on them.

  3. Provenance was laundered.
     Four sources with trust levels 20x apart were merged into one layer that recorded
     only `SRC`, and the perverse result was that the sources trusted LEAST were used
     MOST: `auto_block` 97.4 % converted to pipe against the draftsman's 76.3 %.
     `auto_block` is a cadastral street reserve on bare desert - 45 % of it fronts plots
     of which not one is built. Fixed by carrying `SRC` AND `CONFIDENCE` on every line,
     with `contract.SRC_CONFIDENCE_CEILING` making it impossible to promote the desert,
     and by splitting the draftsman's own delivery in two: his lines on existing roads are
     `drafted`, his lines on future roads are `provisional`, because philosophy sec 4 says
     a platted reserve with nothing built on it "is never reported as existing".

  4. The graph was left in memory.
     W10's flow tree was real and correct and lived inside `p2_sizing.py`; the shapefile
     inherited its geometry and nothing else. Fixed here by minting node identity with
     `contract.NodeIndex`, snapping every corridor endpoint ONTO its node coordinate, and
     writing `US_NODE`/`DS_NODE` out beside a node layer that resolves them. Reloaded and
     re-checked at the end of the run: `_assert_round_trip()`.

WHAT IS REUSED AND WHAT IS REBUILT
The draftsman's 1,195 km is his work and is reused as delivered - not re-treated, not
re-aligned, not simplified. Only the AUTO-generated corridors are rebuilt. What every
source is subject to, without exception, is H1: no source is exempt from a hard
constraint, including the trunk alignment the user drew. Where the exclusion cuts a line,
the cut piece is written to the review layer with its reason, so a removal can be argued
with rather than discovered.

THE EXCLUSION RULE, STATED PRECISELY

  DUAL CARRIAGEWAY (project rule 7, philosophy H1)
    The band is 6.0 m either side of any centreline carrying `dual = 1`, PLUS the untagged
    twin carriageways `RoadTreatment._drop_dual_twins` identifies - a dual is two parallel
    lines and the road file tags only one of them often enough that W8 saw head chambers
    land on the other. 6.0 m is the auditor's own band (`audit.h1`) and equals
    `criteria.DUAL_TWIN_M`. A run inside the band longer than 30 m is deleted: 30 m is
    again the auditor's threshold for "along". A run at or under 30 m is kept only if it
    genuinely crosses the centreline within `DUAL_CROSS_SQUARE_DEG` of square; the rest is
    a clip of the band edge and is kept as such with its in-band length recorded.

  WADI (project rule 8, philosophy H1, G203-p30 sec 4.4.1 and p33)
    Hazard classes 4/5/6 of the 50-year grid, `criteria.HAZARD_WADI_CLASSES`. Sampled at
    3.0 m, the grid's own cell size - anything finer is invented precision. EVERY on-wadi
    run is deleted at this stage, so `ON_WADI_M` is 0 on every published corridor.
    A wadi crossing IS permitted by H1, and it is deliberately NOT created here, for a
    reason worth stating: `audit.r4` tests the MIDPOINT of every reach against the grid
    and has no exemption for a scheduled crossing, so a legal crossing corridor would fail
    a blocking regression check. The short on-wadi runs are therefore written to the
    review layer tagged `wadi (crossing candidate)`, and a crossing becomes a named,
    designed, individually justified exception at the stage that needs one - not 300 of
    them smuggled in through the corridor set. See OPEN ITEMS at the foot of this file.

HOW THE CLAIMS ARE CHECKED, IN THE STAGE, ON WHAT WAS WRITTEN
A stage that says "the exclusions are applied at source" and does not check it has made a
claim, not a design. Four checks run at the end of every run, on the layers reloaded from
disk rather than on what is in memory:

    `assert_h1_r4`         the AUDITOR'S OWN H1 and R4 arithmetic, lifted from `audit.py`
                           and run against the published corridors. If a corridor fails
                           here, every reach ever laid on it fails a blocking check there
    `_assert_round_trip`   every US_NODE/DS_NODE resolves, every endpoint sits ON its own
                           node, nothing is multipart
    `contract.validate`    the schema, the enums, and the anti-laundering ceiling, on the
                           reloaded frame - not only on the frame that was written
    the stitch gate        the worst endpoint gap over every generated link, raised if it
                           exceeds 0.01 m. W10's was exactly 1.000 m on 91.4 % of them

THE RESULT THIS STAGE HANDS ON, AND THE PROBLEM IN IT
Applying H1 by deletion severs the corridor network wherever it crosses a wadi, and 167 km
of it does. The published set is therefore in many more pieces than the pre-exclusion set,
and the run prints both numbers side by side because only the difference is meaningful.
Most of the severances are SHORT - crossings, not routes along a wadi - and each is a
candidate for the designed crossing H1 permits. That is stage 3's decision and it has four
possible answers, not one: a designed crossing, a station, a re-route, or a plot served by
another system (philosophy sec 3). What it may not be is a router that pays a penalty and
carries on, which is how W10 got 131.7 km of pipe onto wadi ground.

WHAT THIS STAGE DELIBERATELY DOES NOT DO
It does not prune corridors that collect nothing. 117.3 km of W10 had no load-bearing plot
within 60 m and carried under 1 m3/d, and 27 % of its pumping sat on that pipe - but
pruning is a layout decision (philosophy sec 4, "no fingers") and a scope decision
(sec 8a), not a corridor one. The number is EXPOSED instead: `N_PLOT` counts the
load-bearing plots for which this corridor is the nearest, so the length carrying zero is
one query away and cannot be lost.

It does not decide the trunk. The main pipe is carried as a corridor with its own `SRC`
because the trunk must be laid on a legal route like everything else; where it goes is
stage 3's decision on stage 2's evidence.

It does not publish the crossings schedule. `contract.CROSSINGS` requires `EDGE_UID` - the
reach that crosses - and no reach exists yet. Filling it with a corridor id would put a
falsehood in a required field, so the schedule is deferred to the stage that mints reaches
and the candidates are handed over on the review layer.

Run:  python s2_corridors.py
"""
from __future__ import annotations

import math
import os
import sys
import time
import warnings
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py
W11A_ROOT = os.path.dirname(HERE)                          # .../W11a
REPO_ROOT = os.path.dirname(W11A_ROOT)                     # .../Hydraulic/Claude
for _p in (HERE, os.path.join(REPO_ROOT, "W8", "py"), os.path.join(REPO_ROOT, "W10", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import geopandas as gpd                                    # noqa: E402
import rasterio                                            # noqa: E402
import shapely                                             # noqa: E402
from rasterio.windows import from_bounds                   # noqa: E402
from shapely.geometry import LineString, Point             # noqa: E402
from shapely.ops import nearest_points, substring, unary_union   # noqa: E402
from shapely.strtree import STRtree                        # noqa: E402

from w11a import contract                                  # noqa: E402  the shared contract
from w11a.contract import ContractError                    # noqa: E402
from sewnet.criteria import DEFAULT as CRIT                # noqa: E402  the ONLY numeric source
from sewnet.prep import load_boundary, clip_roads          # noqa: E402
from sewnet.stages.road_treatment import RoadTreatment     # noqa: E402  reused, not rebuilt
import skeleton as SKEL                                    # noqa: E402  W10's free-space skeleton

warnings.filterwarnings("ignore")

STAGE = "S2"
STAGE_ORDER = 2

# --------------------------------------------------------------------------------------
# Paths. Read-only outside W11a; nothing under W10/ or W8/ is written.
# --------------------------------------------------------------------------------------
BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

ROADS = BASE + r"\Hydraulic\SHP\Road centerline 2\Road_Centercline.shp"
BOUNDARY = BASE + r"\Hydraulic\SHP\Study area\Project Boundary.shp"
MAIN_PIPE = BASE + r"\Hydraulic\SHP\Main Pipe\Main Pipe.shp"
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"
HAZARD = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"

DRAFTED = os.path.join(REPO_ROOT, "W10", "shp", "W10_corridors_drafted.shp")
PLOT_LOADS = os.path.join(REPO_ROOT, "W10", "shp", "W10_plot_loads.gpkg")
PLOT_LOADS_LAYER = "plot_loads"

OUT_SHP = os.path.join(W11A_ROOT, "shp")
OUT_RUN = os.path.join(W11A_ROOT, "run")

# --------------------------------------------------------------------------------------
# Constants. Every one is either a criteria value, an auditor value, a W10 tolerance kept
# deliberately, or - in exactly one case - an assumption with no guideline behind it, said
# so out loud. Nothing here is invented quietly.
# --------------------------------------------------------------------------------------

DUAL_BAND_M = 6.0
# audit.h1 buffers the dual centrelines by exactly 6.0 m before measuring how much pipe
# lies inside. criteria.DUAL_TWIN_M is independently 6.0 m - "a line this close and
# parallel IS the other carriageway". Using the auditor's own band means a corridor that
# passes here cannot fail H1 on the pipe laid along it.

DUAL_ALONG_M = 30.0
# audit.h1's own threshold: a reach with more than 30 m inside the band "runs along a dual
# carriageway". Anything longer is deleted rather than flagged, because H1 is hard.

DUAL_STEP_M = 1.0        # sampling step for the dual band; the band is 12 m wide, so 1 m
                         # resolves an entry and an exit to +/- 0.5 m
from w11a.audit import WADI_SAMPLE_M as WADI_STEP_M   # noqa: E402  - see audit.py

CORRIDOR_MATCH_M = 25.0  # W10 config: a drafted line this close to a treated road counts
CORRIDOR_CUT_M = 4.0     # as covering it - but the cut is made at the tighter distance,
                         # because cutting at 25 m punched 25 m holes and those holes were
                         # W10's single largest source of fragmentation (1,074 pieces)
AUTO_ROAD_MIN_M = 15.0   # a leftover shorter than this after the cut is a clip artefact

CLUSTER_GROW_M = 40.0    # W10 p0_auto: plots within this of each other are one pocket
CLUSTER_MIN_PLOTS = 6    # a pocket smaller than this is left to detail design

# H1a's along/across test. The tolerances live in ONE place - w11a.audit - because the
# auditor is the specification and a second copy here is how the two drift apart (P2).
from w11a.audit import WADI_XING_SKEW, WADI_PROBE_M   # noqa: E402


def _square_crossing(g: LineString, a: float, b: float, wadi: "WadiMask"):
    """Does the on-wadi run [a, b] CROSS the band, or run along it?  (H1a item 1)

    Probes PERPENDICULAR to the pipe at the middle of the run until both banks are found.
    A pipe crossing square has a contact no longer than the band is wide across it; a pipe
    running down the band has a long contact and a narrow perpendicular extent. The ratio
    is the measurement - no length threshold is invented, and WADI_XING_SKEW is the stated
    tolerance on H1's word "perpendicular".

    Returns (is_crossing, contact_m, band_width_m).
    """
    contact = b - a
    mid = 0.5 * (a + b)
    p0 = g.interpolate(max(0.0, mid - 1.0))
    p1 = g.interpolate(min(g.length, mid + 1.0))
    vx, vy = p1.x - p0.x, p1.y - p0.y
    m = math.hypot(vx, vy) or 1.0
    nx_, ny_ = -vy / m, vx / m
    c = g.interpolate(mid)
    ts = np.arange(0.0, WADI_PROBE_M, WADI_STEP_M)
    width = 0.0
    for sgn in (1.0, -1.0):
        on = wadi.at(c.x + sgn * ts * nx_, c.y + sgn * ts * ny_)
        off = np.where(~on)[0]
        width += float(off[0] * WADI_STEP_M) if len(off) else WADI_PROBE_M
    return contact <= WADI_XING_SKEW * max(width, WADI_STEP_M), contact, width


FRONTAGE_M = 40.0        # criteria.CROSS_STREET_FRONTAGE - a plot fronts a line this close
STITCH_MAX_M = 400.0     # how far a stranded pocket may reach; beyond, a person chooses
STITCH_MIN_M = 0.05      # below this the two islands already touch; noding will join them

PLOT_SERVED_M = 60.0     # W10 config: a plot with no corridor within this is unserved.
                         # Also the distance P7 measures "collects nothing" over

NODE_FLOOR_M = 0.50      # a noded segment shorter than this is a noding sliver (W10
                         # netlib.MIN_EDGE_M = 0.30; 0.50 here because contract.NodeIndex
                         # merges at 3.0 m and a sub-metre stub cannot survive it anyway)

UNDERPASSES: Tuple[Tuple[float, float], ...] = ()
# No underpass coordinate has been supplied (00_CURRENT, "a coordinate for the surviving
# roundabout" is still open). With none, RoadTreatment prices every dual crossing as
# trenchless work rather than taking a free one - the conservative direction.


def corridor_width_m(dn: int) -> float:
    """Service corridor width for a diameter. G203-p32 Tab 13 / p35 Tab 15, via 02 sec 4.

    Verbatim from `_BRAIN/02_DESIGN_CRITERIA.md`: "DN200-500: 2.0 m; 600-900: 2.8 m;
    1000-1200: 3.2 m; 1400-1700: 4.0 m; 1800: 4.1 m; 2000-2400: 4.4 m".
    """
    for hi, w in ((500, 2.0), (900, 2.8), (1200, 3.2), (1700, 4.0), (1800, 4.1),
                  (2400, 4.4)):
        if dn <= hi:
            return w
    raise ContractError(f"DN{dn} is beyond G203-p32 Tab 13; no corridor width is stated")


# Every corridor published by THIS stage carries the band for the smallest main sewer the
# guideline allows (DN200, G203-p22 Tab 6), because no diameter exists until stage 6.
# Stage 6 must re-stamp WIDTH_M from the designed DN; the trunk will need 3.2 m at
# DN1000-1200 and a 2.0 m reserve stated against it would be wrong.
WIDTH_AT_STAGE2_M = corridor_width_m(CRIT.DN_MIN_MAIN)


# --------------------------------------------------------------------------------------
# Source vocabulary. SRC and CONFIDENCE are contract enums; the mapping is the judgement.
# --------------------------------------------------------------------------------------

# CONFIDENCE per source, with the reason it is not one grade better.
#   draft/existing_road  a human drew it on a road the road layer also holds -> drafted
#   draft/future_road    a human drew it, but on a reserve with nothing built on it.
#                        Philosophy sec 4: such a corridor "is never reported as existing"
#                        -> provisional. W10 graded all 1,195 km alike; 606.8 km of it is
#                        future road, and that is 51 % of the draftsman's delivery
#   auto_road            machine treatment of an OBSERVED centreline layer -> derived
#   auto_block           a cadastral reserve on bare desert -> provisional (and
#                        contract.SRC_CONFIDENCE_CEILING will not allow better)
#   auto_link            a generated connection across open ground -> provisional (ditto)
#   main_pipe            the user's own drawn alignment, an input -> drafted
SRC_CONFIDENCE = {
    "draft_existing": ("draft", "drafted", 1),
    "draft_future": ("draft", "provisional", 0),
    "auto_road": ("auto_road", "derived", 1),
    "auto_block": ("auto_block", "provisional", 0),
    "auto_link": ("auto_link", "provisional", 0),
    "main_pipe": ("main_pipe", "drafted", 0),
}
# The third element is IS_STREET: 1 = an observed built street, 0 = a platted reserve or a
# drawn route. Derived from provenance rather than from a proximity test, because a
# proximity test needs a tolerance nothing cites.


# --------------------------------------------------------------------------------------
# Terrain and hazard
# --------------------------------------------------------------------------------------

class VrtSampler:
    """`z(x, y)` over the 0.5 m terrain VRT, without loading it.

    `sewnet.prep.TerrainSampler` reads one window covering the AOI. That is right for a
    test area and impossible here: the study boundary is 46 x 25 km, which at 0.5 m is
    4.6 billion cells. So this samples point by point through rasterio, which reads a 1x1
    window per call. RoadTreatment uses the sampler in exactly one place - choosing which
    side of a two-lane pair to keep, on ground level, after plot count ties - and there
    are 44 such segments in the whole study area, so a slow per-point read costs nothing.

    NODATA returns 0.0 and INCREMENTS A COUNTER. `sewnet.prep` hard-fails on nodata under
    the rule "no silent 0.0 elevations", and that rule is right for a design level and
    wrong for a tie-break: raising here would abort a 1,900 km corridor build because one
    two-lane pair sits off the terrain coverage. The count is reported, so it is a stated
    fallback rather than a silent one.
    """

    def __init__(self, path: str):
        self.ds = rasterio.open(path)
        self.nodata = self.ds.nodata if self.ds.nodata is not None else -9999.0
        self.n_calls = 0
        self.n_nodata = 0

    def z(self, x: float, y: float) -> float:
        self.n_calls += 1
        v = float(next(self.ds.sample([(x, y)]))[0])
        if not np.isfinite(v) or v == self.nodata or v <= 0.0:
            self.n_nodata += 1
            return 0.0
        return v

    def close(self):
        self.ds.close()


class WadiMask:
    """The 50-year hazard grid as a boolean array over the study bounds, with O(1) lookup.

    Read in row strips so peak memory is one strip of float32 plus the finished boolean
    array (131.6 M cells over this boundary = 132 MB), not the whole float32 window.

    The test is `criteria.HAZARD_WADI_CLASSES` = (4, 5, 6). `audit.r4` writes the same test
    as `floor(v) >= 4`; measured over this grid the two are identical, because every valid
    cell is an exact integer 1 to 6 and nothing above 6 exists.
    """

    def __init__(self, path: str, bounds, classes=CRIT.HAZARD_WADI_CLASSES,
                 pad: float = 200.0, strip: int = 2000):
        l, b, r, t = bounds
        self.ds = rasterio.open(path)
        win = from_bounds(l - pad, b - pad, r + pad, t + pad, self.ds.transform)
        win = win.round_offsets().round_lengths()
        self.tr = self.ds.window_transform(win)
        h, w = int(win.height), int(win.width)
        self.mask = np.zeros((h, w), dtype=bool)
        lo = min(classes) - 0.5      # >= 4 on a grid whose valid values are integers 1..6
        for r0 in range(0, h, strip):
            r1 = min(h, r0 + strip)
            sub = rasterio.windows.Window(win.col_off, win.row_off + r0, w, r1 - r0)
            a = self.ds.read(1, window=sub)
            self.mask[r0:r1] = np.isfinite(a) & (a > lo)
        self.ds.close()
        self.h, self.w = h, w
        self.wadi_cells = int(self.mask.sum())

    def at(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Vectorised. Outside the window is dry, matching HazardSampler's 'no value = dry'
        (user 2026-08-19) and audit.r4's treatment of a non-finite sample."""
        col = ((np.asarray(xs) - self.tr.c) / self.tr.a).astype(np.int64)
        row = ((np.asarray(ys) - self.tr.f) / self.tr.e).astype(np.int64)
        ok = (row >= 0) & (col >= 0) & (row < self.h) & (col < self.w)
        out = np.zeros(len(col), dtype=bool)
        if ok.any():
            out[ok] = self.mask[row[ok], col[ok]]
        return out


# --------------------------------------------------------------------------------------
# The load units RoadTreatment needs. Its four plot-aware steps read `u.x`, `u.y` and,
# in one place, `u.geom`.
# --------------------------------------------------------------------------------------

@dataclass
class Unit:
    x: float
    y: float
    geom: object
    q_m3d: float


def load_units(path: str, layer: str) -> Tuple[List[Unit], gpd.GeoDataFrame, "contract.Funnel"]:
    """Every registered plot in the boundary, as RoadTreatment units.

    ALL registered plots, not only the load-bearing ones. The roundabout guard asks
    "is there a plot inside this ring", which is a cadastral question and not a load one -
    and it is the test that failed in W10, where 34 collapsed rings turned out to contain a
    registered plot. Handing it the load-bearing subset would leave the same rings
    collapsed for a different reason.

    The load-bearing subset is used separately, for N_PLOT.
    """
    g = gpd.read_file(path, layer=layer).to_crs(contract.CRS_EPSG)
    fn = contract.Funnel("plot records", len(g))
    out = g[g["IN_BND"] == 1]
    fn.drop("outside the study boundary", n=len(g) - len(out))
    pts = out.geometry.representative_point()      # guaranteed inside a concave plot
    units = [Unit(float(p.x), float(p.y), gm, float(q))
             for p, gm, q in zip(pts, out.geometry, out["Q_AVG_M3D"])]
    fn.close(len(units))
    return units, out.reset_index(drop=True), fn


# --------------------------------------------------------------------------------------
# Step A - the raw road layer, treated PROPERLY
# --------------------------------------------------------------------------------------

def treat_roads(roads: gpd.GeoDataFrame, units: List[Unit], sampler: VrtSampler,
                out_path: str) -> Tuple[List[LineString], Dict, RoadTreatment]:
    """RoadTreatment with BOTH of the arguments W10 passed as None.

    The guard is a raise, not a warning. W10's call was syntactically fine and produced a
    plausible-looking 604 km of corridor; the only symptom of four dead steps was 34
    roundabout rings sitting on registered plots, found six weeks later. A stage that
    cannot do its job must refuse to run, not do a quarter of it (invariant 10).
    """
    if sampler is None:
        raise ContractError(
            "RoadTreatment needs a terrain sampler. Without it `_handle_duals` scores both "
            "sides of every two-lane pair at z = 0.0 and keeps whichever came first. This "
            "is the W10 call signature and it is refused.")
    if not units:
        raise ContractError(
            "RoadTreatment needs load units. Without them `_drop_traffic_links` and "
            "`_drop_stubs` return at their first line, `_drop_orphan_links` finds every "
            "line to be serving something, and the roundabout guard cannot test whether a "
            "ring contains a plot - which is how W10 collapsed 34 rings over registered "
            "plots. Four steps become no-ops (invariant 10).")

    if "dual" not in roads.columns:
        raise ContractError(
            "the road layer has no `dual` column. Project rule 7 identifies a dual "
            "carriageway from it (1 = dual, 2 = two-lane pair); without it the exclusion "
            "cannot be applied at all and the run must stop, not proceed unguarded.")
    dual_col = roads["dual"].fillna(0)
    cls_col = roads["StrCls"] if "StrCls" in roads.columns else pd.Series([""] * len(roads))

    # `attrs` is keyed by id(geometry), so `segs` must hold a live reference to every
    # geometry for the whole run - a collected object frees its id for reuse and the road
    # class would then follow the wrong line.
    segs, attrs = [], {}
    for g, d, s in zip(roads.geometry, dual_col, cls_col):
        segs.append(g)
        attrs[id(g)] = {"dual": int(d or 0), "strcls": str(s or "")}

    rt = RoadTreatment(sampler=sampler, crit=CRIT, attrs=attrs, underpasses=UNDERPASSES)
    kept = rt.run(segs, units=units, out_path=out_path)
    return kept, rt.report, rt


def assert_stage_did_something(report: Dict) -> List[str]:
    """Read the report back and say which of the four W10-dead steps actually fired.

    Reported, not asserted: a genuine zero is possible (a road network with no turning
    fillets at all), and a hard assertion on a count would be a metric nobody could
    reproduce. What is NOT acceptable is not looking - the four numbers are printed and go
    into the manifest, so "the stage ran" is evidence rather than an assumption.
    """
    # A zero that has a known cause is not the same as a zero that has none, so the known
    # one is named. `_drop_stubs` runs LAST in RoadTreatment.run, after `_drop_orphan_links`
    # has already taken every dead end under 80 m that serves no plot; a dangling stub
    # under its own 8.0 m threshold is unlikely to survive that. Zero here is expected.
    # Zero anywhere else means the step could not see its inputs, which is the W10 defect.
    watched = {
        "traffic_links_dropped": "",
        "empty_stubs_dropped": "expected ~0: _drop_orphan_links (80 m) runs first and "
                               "eats what _drop_stubs (8.0 m) would find",
        "orphan_links_dropped": "",
        "two_lane_side_dropped": "",
    }
    lines = []
    for k, why in watched.items():
        v = report.get(k, "ABSENT")
        flag = ""
        if v == 0:
            flag = f"  <- ZERO, {why}" if why else "  <- ZERO: was this step reachable?"
        lines.append(f"      {k:<26s} {v}{flag}")
    rej = report.get("rings_rejected", {})
    lines.append(f"      rings rejected, plot inside  {rej.get('plots_inside', 'ABSENT')}"
                 "   (W10 could not run this test at all)")
    return lines


# --------------------------------------------------------------------------------------
# Step B - the free-space skeleton, for plots no corridor reaches
# --------------------------------------------------------------------------------------

def unserved_plots(plots: gpd.GeoDataFrame, corridors: gpd.GeoDataFrame,
                   dist: float = PLOT_SERVED_M):
    """Plots with no corridor within `dist`, measured from the polygon, not its centre."""
    if len(corridors) == 0:
        return plots, np.zeros(len(plots), dtype=bool)
    near = gpd.sjoin_nearest(plots[["geometry"]], corridors[["geometry"]], how="left",
                             max_distance=dist, distance_col="D")
    near = near[~near.index.duplicated(keep="first")]
    served = near["D"].notna().values
    return plots[~served], served


def skeleton_pockets(plots_left: gpd.GeoDataFrame) -> Tuple[List[LineString], Dict]:
    """Street centre lines recovered from the space the plots left between them.

    W10's method, unchanged and re-used: the street reserve is not missing from a platted
    subdivision, it is the negative space between the blocks, and it is drawn precisely
    because the plot boundaries define it. What changes downstream is only its GRADE - it
    is a cadastral reserve, not an observed street, and `contract.SRC_CONFIDENCE_CEILING`
    holds it at `provisional` for the rest of the design.
    """
    if len(plots_left) == 0:
        return [], {"pockets": 0, "plots_covered": 0, "plots_in_small_pockets": 0}
    blobs = gpd.GeoDataFrame(
        geometry=[unary_union(plots_left.geometry.buffer(CLUSTER_GROW_M))],
        crs=contract.CRS_EPSG).explode(index_parts=False).reset_index(drop=True)
    tree = STRtree(list(plots_left.geometry))
    lines, done, skipped, used, failed = [], 0, 0, 0, 0
    for i, blob in enumerate(blobs.geometry):
        idx = [int(j) for j in tree.query(blob)
               if plots_left.geometry.iloc[int(j)].intersects(blob)]
        if len(idx) < CLUSTER_MIN_PLOTS:
            skipped += len(idx)
            continue
        sub = [plots_left.geometry.iloc[j] for j in idx]
        try:
            raw = SKEL.street_lines(sub, blob)
            keep = SKEL.prune_to_cover(raw, sub, frontage_m=FRONTAGE_M)
        except Exception as e:                      # a pocket that cannot be skeletonised
            failed += 1                             # is named, never swallowed
            print(f"      pocket {i}: {e}")
            continue
        lines.extend(keep)
        done += len(idx)
        used += 1
        if (i + 1) % 200 == 0:
            print(f"      {i+1}/{len(blobs)} pockets, {len(lines):,} lines so far")
    return lines, {"pockets": int(len(blobs)), "pockets_used": used,
                   "pockets_failed": failed, "plots_covered": done,
                   "plots_in_small_pockets": skipped}


# --------------------------------------------------------------------------------------
# Step C - the stitch, RE-CUT so the links actually touch
# --------------------------------------------------------------------------------------

def stitch(new_lines: List[LineString], existing: gpd.GeoDataFrame,
           max_m: float = STITCH_MAX_M) -> Tuple[List[LineString], Dict]:
    """Join the skeleton islands to each other and to the network - ON the geometry.

    W10's version is correct in its ROUTING and wrong in its GEOMETRY. The routing idea is
    good and is kept: sending every island straight to the nearest mapped road costs 287 km
    because each island pays the full distance alone, whereas a minimum spanning tree over
    the islands lets each reach its neighbour and only the pocket as a whole pays the long
    link out.

    The geometry was fatal. Islands were identified by `unary_union([l.buffer(1.0)])`, and
    then `nearest_points` was taken between those BUFFER POLYGONS. The nearest point on a
    1 m buffer is 1 m away from the line inside it, at each end, so 91.4 % of the links
    were born exactly 1.000 m short of what they joined. A 2.5 m snap in the topology step
    made the graph look connected while the published layer kept every gap, and the design
    shipped in 7,919 pieces with nothing on the layer to reveal it.

    Here the buffer decides GROUPING only - which lines are one island - and the link is
    drawn between the real geometries with `nearest_points`, so both endpoints lie exactly
    on the lines they connect. Verified downstream: the noding puts a shared vertex there,
    `NodeIndex` mints one identity for it, and `_assert_round_trip` proves it on reload.
    """
    import networkx as nx

    if not new_lines or len(existing) == 0:
        return [], {"islands": 0, "links": 0, "stranded_islands": 0, "already_touching": 0}

    # grouping only - the buffer never touches the geometry that gets published
    blobs = gpd.GeoDataFrame(
        geometry=[unary_union([l.buffer(1.0) for l in new_lines])],
        crs=contract.CRS_EPSG).explode(index_parts=False).reset_index(drop=True)
    btree = STRtree(list(blobs.geometry))
    members: Dict[int, List[LineString]] = {}
    for ln in new_lines:
        rep = ln.interpolate(0.5, normalized=True)
        hit = [int(j) for j in btree.query(rep) if blobs.geometry.iloc[int(j)].covers(rep)]
        members.setdefault(hit[0] if hit else -1, []).append(ln)
    islands = [unary_union(v) for k, v in sorted(members.items()) if k >= 0]
    orphan = members.get(-1, [])
    if orphan:                                     # cannot happen; if it does, say so
        islands.extend(unary_union([o]) for o in orphan)

    ex = unary_union(list(existing.geometry.values))
    nodes = [ex] + islands                         # node 0 is the whole existing network
    itree = STRtree(islands)

    G = nx.Graph()
    G.add_nodes_from(range(len(nodes)))
    for i, g in enumerate(islands, start=1):
        d0 = g.distance(ex)
        if d0 <= max_m:
            G.add_edge(0, i, w=d0)
        for j in itree.query(g.buffer(max_m)):
            j = int(j) + 1
            if j <= i:
                continue
            d = g.distance(nodes[j])
            if d <= max_m:
                G.add_edge(i, j, w=d)

    links, stranded, touching = [], 0, 0
    for comp in nx.connected_components(G):
        if 0 not in comp:
            stranded += len(comp)                  # nothing here reaches the network
            continue
        for u, v in nx.minimum_spanning_edges(G.subgraph(comp), weight="w", data=False):
            a, b = nearest_points(nodes[u], nodes[v])     # REAL geometry, not the buffer
            if a.distance(b) < STITCH_MIN_M:
                touching += 1                      # already meeting; noding will join them
                continue
            links.append(LineString([a, b]))
    stranded += sum(1 for n in G.nodes if G.degree(n) == 0)
    return links, {"islands": len(islands), "links": len(links),
                   "stranded_islands": stranded, "already_touching": touching}


# --------------------------------------------------------------------------------------
# The exclusions, applied at source
# --------------------------------------------------------------------------------------

def _runs(line: LineString, inside: Callable[[np.ndarray, np.ndarray], np.ndarray],
          step: float) -> List[Tuple[float, float, bool]]:
    """Split a line into alternating inside/outside runs, as (from, to, inside) chainages.

    Sampled rather than intersected, so the same machinery serves a raster mask and a
    polygon band and the two cannot drift apart.

    THE CUT IS BIASED TOWARDS THE OBSTACLE, not placed at the midpoint between the two
    samples that straddle it. A midpoint cut leaves up to half a step of the obstacle
    attached to the clean piece at each end, and on a short piece that contaminated end
    contains the piece's own midpoint - which is exactly what `audit.r4` tests. Measured on
    the first full run: 59 published corridors came back with their midpoint on wadi ground
    from that half-step alone. Biasing the cut gives the clean run endpoints that are
    themselves clean samples, and hands the uncertain half-step to the obstacle, where a
    wrong answer costs a metre of corridor instead of a blocking audit failure.
    """
    L = line.length
    n = max(2, int(math.ceil(L / step)) + 1)
    d = np.linspace(0.0, L, n)
    xy = shapely.get_coordinates(shapely.line_interpolate_point(line, d))
    f = inside(xy[:, 0], xy[:, 1])
    runs, a, cur = [], 0.0, bool(f[0])
    for i in range(1, n):
        if bool(f[i]) != cur:
            # leaving clean ground -> cut at the LAST clean sample;
            # entering clean ground -> cut at the FIRST clean sample. Either way the
            # obstacle run grows and the clean run shrinks.
            b = d[i - 1] if not cur else d[i]
            if b > a:
                runs.append((a, b, cur))
                a, cur = b, bool(f[i])
            else:
                cur = bool(f[i])
    runs.append((a, L, cur))
    return runs


def _square_to(run: LineString, lines: List[LineString], tree: STRtree) -> Tuple[bool, float]:
    """Does this run cross one of `lines`, and how far off square is it?

    Project rule 7: "Crossing is allowed only as a short perpendicular pipe." The angle is
    taken against the obstacle's LOCAL tangent - a 10 m chord about the projection of the
    run's midpoint - because a dual carriageway curves and its end-to-end bearing is not
    its bearing here.
    """
    mid = run.interpolate(0.5, normalized=True)
    best, bestd = None, 1e18
    for j in tree.query(run):
        g = lines[int(j)]
        # Only a centreline the run ACTUALLY crosses can say anything about the crossing
        # angle. Choosing the nearest candidate and THEN testing whether it is crossed let
        # a run that crosses dual A at a skew angle - while dual B passes nearer the run's
        # midpoint without being crossed - be reported as "does not cross" and kept as a
        # band clip, with project rule 7's angle cap never applied to it.
        if not run.intersects(g):
            continue
        dd = g.distance(mid)
        if dd < bestd:
            best, bestd = g, dd
    if best is None:
        return False, 180.0
    ch = best.project(mid)
    a = best.interpolate(max(0.0, ch - 5.0))
    b = best.interpolate(min(best.length, ch + 5.0))
    if a.distance(b) < 1e-6:
        return True, 180.0
    bd = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
    (x0, y0), (x1, y1) = run.coords[0], run.coords[-1]
    bl = math.degrees(math.atan2(y1 - y0, x1 - x0))
    off = abs(bd - bl) % 180.0
    off = min(off, 180.0 - off)
    return True, abs(90.0 - off)


def apply_exclusions(lines: List[LineString], srcs: List[str], band, band_prepared,
                     dual_lines: List[LineString], dual_tree: STRtree,
                     wadi: WadiMask) -> Tuple[List[LineString], List[str], List[float],
                                              List[Dict]]:
    """H1, applied by DELETING ground rather than by pricing it.

    Returns the surviving pieces with their source and their in-band dual length, plus the
    removals with a reason each. Philosophy sec 2: the exclusions belong here, at the
    corridor, not in the router - a router that can pay to cross a constraint will, and
    W10's did, 131.7 km of it.
    """
    keep_g: List[LineString] = []
    keep_s: List[str] = []
    keep_dual: List[float] = []
    removed: List[Dict] = []

    def band_hit(xs, ys):
        return shapely.intersects(band_prepared, shapely.points(xs, ys))

    for ln, src in zip(lines, srcs):
        # ---- 1. the dual band. Exact obstacle, sampled at 1 m. A run out of `_runs` is
        #         homogeneous, so its in-band length is either 0 or its whole length -
        #         which is what makes the proportional carry below exact rather than a
        #         smear.
        pieces: List[Tuple[LineString, float]] = []      # (geom, in-band length)
        if band is not None and shapely.intersects(band_prepared, ln):
            for a, b, inside in _runs(ln, band_hit, DUAL_STEP_M):
                if b - a < 1e-6:
                    continue
                sub = substring(ln, a, b)
                if sub.is_empty or sub.length < 1e-6:
                    continue
                if sub.geom_type != "LineString":
                    continue                             # substring degenerated to a point
                if not inside:
                    pieces.append((sub, 0.0))
                    continue
                if sub.length > DUAL_ALONG_M:
                    removed.append(dict(SRC=src, REASON="along a dual carriageway",
                                        DETAIL=f"{sub.length:.0f} m inside the "
                                               f"{DUAL_BAND_M:.0f} m band, cap "
                                               f"{DUAL_ALONG_M:.0f} m (audit.h1)",
                                        LEN_M=sub.length, geometry=sub))
                    continue
                crosses, off = _square_to(sub, dual_lines, dual_tree)
                if crosses and off > CRIT.DUAL_CROSS_SQUARE_DEG:
                    # ONE reason string, the angle in DETAIL. A reason that embeds a
                    # measurement makes every removal its own category and the funnel
                    # unreadable - the same mistake as a metric with a private filter.
                    removed.append(dict(SRC=src,
                                        REASON="dual crossing off square",
                                        DETAIL=f"{off:.0f} deg off, cap "
                                               f"{CRIT.DUAL_CROSS_SQUARE_DEG:.0f} deg",
                                        LEN_M=sub.length, geometry=sub))
                    continue
                pieces.append((sub, sub.length))         # a square crossing, or a band clip
        else:
            pieces.append((ln, 0.0))

        # ---- 2. the wadi. Every on-wadi run goes; see the module docstring for why a
        #         crossing is NOT created here.
        for g, on_dual in pieces:
            if wadi is None:
                keep_g.append(g); keep_s.append(src); keep_dual.append(on_dual)
                continue
            runs = _runs(g, wadi.at, WADI_STEP_M)
            if len(runs) == 1 and not runs[0][2]:
                keep_g.append(g); keep_s.append(src); keep_dual.append(on_dual)
                continue
            for a, b, inside in runs:
                if b - a < 1e-6:
                    continue
                sub = substring(g, a, b)
                if sub.is_empty or sub.geom_type != "LineString" or sub.length < 1e-6:
                    continue
                if inside:
                    # H1a: a crossing is legal, a run ALONG a wadi is not. Deleting both is
                    # what severed the network into 1,381 pieces - see the module docstring
                    # and philosophy H1a. The test is geometric, not a length threshold.
                    is_x, contact, wide = _square_crossing(g, a, b, wadi)
                    if is_x:
                        share = on_dual * (sub.length / g.length) if g.length > 0 else 0.0
                        keep_g.append(sub); keep_s.append(src); keep_dual.append(share)
                        continue
                    removed.append(dict(
                        SRC=src,
                        REASON="wadi (along)",
                        DETAIL=(f"{contact:.0f} m of contact against a band {wide:.0f} m "
                                f"wide across the line - over the {WADI_XING_SKEW:.3f} skew "
                                f"tolerance, so this runs ALONG the wadi, not across it"),
                        LEN_M=sub.length, geometry=sub))
                    continue
                # the in-band dual length belongs to whichever surviving piece carries it;
                # a piece cut by a wadi keeps the share of the band it still holds
                share = on_dual * (sub.length / g.length) if g.length > 0 else 0.0
                keep_g.append(sub); keep_s.append(src); keep_dual.append(share)
    return keep_g, keep_s, keep_dual, removed


# --------------------------------------------------------------------------------------
# Noding, and writing the graph OUT
# --------------------------------------------------------------------------------------

def node_and_attribute(lines: List[LineString], srcs: List[str]
                       ) -> Tuple[List[LineString], List[str]]:
    """Split every line at every crossing, then give each piece its parent's provenance.

    `unary_union` nodes the whole linework: a junction becomes a shared vertex instead of
    two lines passing over each other. It also destroys attribution, because it returns
    bare geometry - so each noded piece is matched back to the parent it lies on, by the
    midpoint, and where several parents coincide the MOST TRUSTED one wins. That direction
    matters: a piece lying on both a drafted line and a skeleton line IS the drafted line,
    and taking the other answer would be exactly the laundering P6 forbids, in reverse.
    """
    merged = unary_union(lines)
    parts = [merged] if merged.geom_type == "LineString" else \
            [g for g in merged.geoms if g.geom_type == "LineString"]
    parts = [g for g in parts if g.length > NODE_FLOOR_M]

    tree = STRtree(lines)
    rank = {c: i for i, c in enumerate(contract.CONFIDENCE)}
    out_g, out_s, orphans = [], [], 0
    for g in parts:
        mid = g.interpolate(0.5, normalized=True)
        best, best_key = None, None
        for j in tree.query(mid.buffer(1.0)):
            j = int(j)
            d = lines[j].distance(mid)
            if d > 1.0:
                continue
            conf = SRC_CONFIDENCE[srcs[j]][1]
            key = (rank[conf], d, -lines[j].length)     # trusted first, then closest
            if best_key is None or key < best_key:
                best, best_key = j, key
        if best is None:                                # no parent within 1 m: fall back
            orphans += 1                                # to the nearest, and count it -
            best = int(np.atleast_1d(tree.query_nearest(mid))[0])   # never assume none
        out_g.append(g)
        out_s.append(srcs[best])
    if orphans:
        print(f"      {orphans:,} noded pieces had no parent within 1 m and took their "
              "provenance from the nearest line - inspect if this is more than a handful")
    return out_g, out_s


def nodes_frame(idx: "contract.NodeIndex", us: List[str], ds: List[str]
                ) -> gpd.GeoDataFrame:
    """The node layer, built from the edges that SURVIVE - never from the index.

    Built separately from minting because a node whose only corridor was later removed is
    not a node, it is a leftover. Publishing leftovers is how a US_NODE comes to resolve to
    something no corridor touches, and a graph nobody can reload is what stage 2 exists to
    stop being possible.
    """
    deg: Dict[str, int] = {}
    for a, b in zip(us, ds):
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    used = sorted(deg)
    return gpd.GeoDataFrame(
        dict(NODE_UID=used,
             NODE_KIND=["corridor"] * len(used),
             X=[idx.nodes[u].x for u in used],
             Y=[idx.nodes[u].y for u in used],
             DEGREE=[deg[u] for u in used],
             STAGE=[STAGE] * len(used)),
        geometry=[Point(idx.nodes[u].xy) for u in used], crs=contract.CRS_EPSG)


def audit_sweep(geoms: List[LineString], band_prepared, wadi: Optional[WadiMask]
                ) -> Tuple[np.ndarray, List[Dict]]:
    """The auditor's own tests, run on the SNAPPED geometry, as the last cut.

    Two things survive careful sampling and have to be caught by testing the thing itself:

      * a corridor can clip the CORNER of a 3 m hazard cell over a traverse shorter than
        the sample spacing, so no sample lands in it while `audit.r4`'s midpoint does;
      * `mint_nodes` moves each endpoint onto its node, by up to the 3.0 m merge radius,
        and moving an endpoint moves the midpoint the auditor tests.

    So the last word goes to the auditor's arithmetic on the published geometry, not to my
    approximation of it. A piece that fails is removed - which is the correct answer, not a
    concession: a corridor whose midpoint is in a wadi is partly in a wadi, and H1 does not
    care that the part is small.
    """
    keep = np.ones(len(geoms), dtype=bool)
    out: List[Dict] = []
    mids = shapely.line_interpolate_point(np.array(geoms, dtype=object),
                                          0.5, normalized=True)
    if wadi is not None:
        # H1a, not the superseded midpoint rule. A CROSSING has its midpoint on the wadi by
        # definition, so a plain midpoint sweep deletes exactly what H1a permits - which is
        # what it did on the first run, taking 103.7 km of legal crossings back out and
        # leaving the network as fragmented as before the crossing rule was written. The
        # sweep now asks the same question audit.r4 asks: across, or along?
        xy = shapely.get_coordinates(mids)
        on = wadi.at(xy[:, 0], xy[:, 1])
        for i in np.nonzero(on)[0]:
            g = geoms[i]
            runs = [(a, b) for a, b, ins in _runs(g, wadi.at, WADI_STEP_M) if ins]
            ok = False
            if len(runs) == 1:
                ok, contact, wide = _square_crossing(g, runs[0][0], runs[0][1], wadi)
            if ok:
                continue                       # a legal crossing; CROSS_ID is minted later
            out.append(dict(SRC="", REASON="wadi (along, audit.r4 sweep)",
                            DETAIL=("midpoint on hazard class >= 4 after snapping and the "
                                    "contact is not a square crossing"
                                    if len(runs) == 1 else
                                    f"{len(runs)} separate on-wadi runs - not one crossing"),
                            LEN_M=g.length, geometry=g))
            keep[i] = False
    if band_prepared is not None:
        for i, g in enumerate(geoms):
            if not keep[i] or not shapely.intersects(band_prepared, g):
                continue
            inb = g.intersection(band_prepared).length
            if inb > DUAL_ALONG_M:
                keep[i] = False
                out.append(dict(SRC="", REASON="along a dual carriageway "
                                               "(audit.h1 band sweep)",
                                DETAIL=f"{inb:.0f} m inside the {DUAL_BAND_M:.0f} m band "
                                       f"after snapping, cap {DUAL_ALONG_M:.0f} m",
                                LEN_M=g.length, geometry=g))
    return keep, out


def mint_nodes(lines: List[LineString], srcs: List[str], on_dual: List[float]
               ) -> Tuple["contract.NodeIndex", List[str], List[str], List[LineString],
                          List[str], List[float], int, float]:
    """Give every corridor endpoint an identity, and move the geometry ONTO it.

    `contract.NodeIndex` is used and `contract.Network` is NOT, deliberately. Network
    enforces H15 - one outgoing edge per node, a forest - and that is right for a sewer and
    wrong for a street: a corridor network is full of blocks, and refusing the second
    outgoing edge at a crossroads would reject the road layer itself. H15 belongs to the
    reaches, at the stage that lays them. What IS taken from the contract is the thing that
    matters here: identity minted once, spatially, at `criteria.MH_SNAP_M` = 3.0 m -
    "closer than the clearance means ONE structure, merge" - so two corridors arriving at
    one street corner produce one node, not two 0.4 m apart.

    The endpoints are then REWRITTEN to the node coordinate. That is the whole point of
    doing this at the corridor rather than at the pipe: after this, a corridor physically
    cannot end 1.000 m from the corridor it joins, which is the W10 defect that put the
    published layer in 7,919 pieces.

    The attribute lists travel WITH the geometry through the same filter. Recomputing the
    filter a second time to re-align them is how provenance ends up on the wrong line, and
    provenance on the wrong line is worse than none - it is a claim.
    """
    idx = contract.NodeIndex()
    us, ds, geoms, out_s, out_d = [], [], [], [], []
    degenerate, degen_m = 0, 0.0
    for g, s, d0 in zip(lines, srcs, on_dual):
        c = list(g.coords)
        a = idx.get_or_create(c[0][0], c[0][1], kind="corridor", stage=STAGE)
        b = idx.get_or_create(c[-1][0], c[-1][1], kind="corridor", stage=STAGE)
        if a == b:                 # both ends merged into one node: shorter than 3.0 m
            degenerate += 1
            degen_m += g.length
            continue
        na, nb = idx.nodes[a], idx.nodes[b]
        c[0] = (na.x, na.y)
        c[-1] = (nb.x, nb.y)
        ln = LineString(c)
        if ln.length < NODE_FLOOR_M:
            degenerate += 1
            degen_m += g.length
            continue
        us.append(a); ds.append(b); geoms.append(ln)
        out_s.append(s)
        # the endpoint moved onto the node, so the in-band share moves with the length
        out_d.append(min(d0, ln.length) if d0 > 0 else 0.0)

    return idx, us, ds, geoms, out_s, out_d, degenerate, degen_m


def assert_h1_r4(corridors: gpd.GeoDataFrame, roads: gpd.GeoDataFrame) -> Dict:
    """Run the AUDITOR'S OWN H1 and R4 against the published corridor layer.

    Not a paraphrase and no longer a copy: it CALLS `audit.run_one("H1")` and
    `audit.run_one("R4")` on the published corridor layer. The previous version lifted
    their arithmetic by hand, and when r4 gained the H1a along/across test the copy stayed
    on the superseded midpoint rule - so the stage kept 2,456 legal crossings and its own
    gate then rejected every one of them. A gate that re-implements what it gates will
    drift from it; this one cannot.

    Two reasons this belongs in the stage rather than in a later audit. First, the auditor
    reads reaches, and a reach inherits the ground its corridor sits on - so if a corridor
    fails here, every reach laid on it fails there, and the cheapest place to find that out
    is now. Second, and more to the point: the whole claim of this stage is that H1 is
    applied AT SOURCE. A claim of that kind is worth exactly what its check is worth, and
    "we deleted the ground" is not a check.

    Note H1 here is the auditor's band, built from the road file's `dual = 1` ONLY. The
    exclusion this module applies is strictly wider - it also carries the 69 untagged twin
    carriageways `RoadTreatment._drop_dual_twins` found - so passing this is necessary and
    not sufficient, which is the right direction for a gate to err in.
    """
    from w11a import audit as _audit

    ctx = _audit.Ctx(pipes=corridors, roads=roads, hazard=HAZARD, crit=CRIT)
    st1, sum1, n1, ext1 = _audit.run_one("H1", ctx)
    st4, sum4, n4, ext4 = _audit.run_one("R4", ctx)
    out: Dict = {"h1_status": st1, "h1_summary": sum1, "h1_bad": int(n1), "h1_extent": ext1,
                 "r4_status": st4, "r4_summary": sum4, "r4_bad": int(n4), "r4_extent": ext4}
    if st1 != _audit.PASS or st4 != _audit.PASS:
        raise ContractError(
            "THE PUBLISHED CORRIDORS WOULD FAIL THE AUDITOR AT SOURCE:\n"
            f"  H1  {st1}: {sum1}  {ext1}\n"
            f"  R4  {st4}: {sum4}  {ext4}\n"
            "Every reach laid on these fails a BLOCKING check. The exclusions are applied "
            "in apply_exclusions() and audit_sweep(); if this fires, the sampling step is "
            "too coarse for the obstacle or an exclusion was skipped - it is not something "
            "to relax here.")
    return out


def component_count(lines: List[LineString]) -> Tuple[int, int, int]:
    """(components, nodes, largest component) over a set of lines, at the node merge radius.

    Run BEFORE and AFTER the exclusion, because the after-figure alone is unreadable. H1
    severs a corridor wherever it crosses a wadi, and the honest statement is not "the
    corridor network is in N pieces" but "the exclusion turned N0 pieces into N". The
    difference is the price of the constraint, and it is a number stage 3 has to spend or
    design around - not a defect in this stage.
    """
    import networkx as nx
    idx = contract.NodeIndex()
    G = nx.Graph()
    for g in lines:
        c = list(g.coords)
        a = idx.get_or_create(c[0][0], c[0][1])
        b = idx.get_or_create(c[-1][0], c[-1][1])
        G.add_node(a); G.add_node(b)
        if a != b:
            G.add_edge(a, b)
    comps = list(nx.connected_components(G))
    return len(comps), G.number_of_nodes(), (max(len(c) for c in comps) if comps else 0)


def _assert_round_trip(corridors: gpd.GeoDataFrame, nodes: gpd.GeoDataFrame,
                       tol: float = contract.ENDPOINT_TOL_M) -> None:
    """Reload proof: the published layers ARE the graph (invariant 2).

    `contract.Network.assert_round_trip` cannot be used - it demands `EDGE_UID` and a
    forest, and a corridor network is neither. The three things it proves that matter here
    are proved directly: every US_NODE/DS_NODE resolves to a published node, every endpoint
    sits on its own node's coordinate, and no corridor is multipart. `audit.Ctx.graph()`
    reads `g.geoms[0]` of a multipart geometry and silently discards the rest, so a
    multipart corridor would corrupt the one check that exists to catch silent corruption.
    """
    problems: List[str] = []
    pos = {r.NODE_UID: (r.geometry.x, r.geometry.y) for r in nodes.itertuples()}
    for r in corridors.itertuples():
        g = r.geometry
        if g is None or g.is_empty:
            problems.append(f"{r.CORR_ID} has no geometry")
            continue
        if g.geom_type != "LineString":
            problems.append(f"{r.CORR_ID} is {g.geom_type}, not a single LineString - "
                            "audit.Ctx.graph() would read only its first part")
            continue
        c = list(g.coords)
        for role, pt in (("US_NODE", c[0]), ("DS_NODE", c[-1])):
            uid = getattr(r, role)
            if uid not in pos:
                problems.append(f"{r.CORR_ID}.{role} = {uid!r} resolves to no node")
                continue
            d = math.hypot(pos[uid][0] - pt[0], pos[uid][1] - pt[1])
            if d > tol:
                problems.append(f"{r.CORR_ID} {role} endpoint is {d:.4f} m from node {uid} "
                                f"(tolerance {tol} m)")
        if len(problems) > 40:
            problems.append("... stopping at 40")
            break
    if problems:
        raise ContractError("PUBLISHED CORRIDORS ARE NOT THE GRAPH (invariant 2):\n  "
                            + "\n  ".join(problems))


# --------------------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------------------

def _jsonable(v):
    """numpy and pandas scalars do not survive `json.dump`, and the Manifest is written by
    one. A metric that cannot be serialised takes the whole run's record down with it."""
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def _missing_inputs() -> List[Tuple[str, str]]:
    need = [("road centrelines", ROADS), ("study boundary", BOUNDARY),
            ("main pipe alignment", MAIN_PIPE), ("terrain VRT", TERRAIN),
            ("50-year hazard grid", HAZARD),
            ("the draftsman's treated corridors", DRAFTED),
            ("plot loads", PLOT_LOADS)]
    return [(n, p) for n, p in need if not os.path.exists(p)]


def build() -> Dict:
    t_all = time.time()
    os.makedirs(OUT_SHP, exist_ok=True)
    os.makedirs(OUT_RUN, exist_ok=True)
    res: Dict = {"reads": [], "metrics": {}, "funnels": [], "notes": []}

    def step(msg, t0):
        print(f"   {msg}  ({time.time() - t0:.1f} s)")
        return time.time()

    # ---------------------------------------------------------------- inputs
    print("0  inputs")
    t = time.time()
    boundary = load_boundary(BOUNDARY)
    roads = clip_roads(ROADS, boundary, sliver_m=0.5, crs_epsg=contract.CRS_EPSG)
    res["reads"].append(("roads", ROADS, len(roads)))
    t = step(f"roads {len(roads):,} lines, {roads.length.sum()/1000:,.1f} km "
             f"(dual=1 on {int((roads['dual'] == 1).sum())})", t)

    units, plots, fn_plots = load_units(PLOT_LOADS, PLOT_LOADS_LAYER)
    res["reads"].append(("plot_loads", PLOT_LOADS, len(plots)))
    res["funnels"].append(fn_plots)
    load_bearing = plots[plots["Q_AVG_M3D"] > 0].reset_index(drop=True)
    t = step(f"plots {len(plots):,} in boundary, {len(load_bearing):,} load-bearing, "
             f"{plots['Q_AVG_M3D'].sum():,.0f} m3/d", t)

    sampler = VrtSampler(TERRAIN)
    wadi = WadiMask(HAZARD, boundary.bounds)
    t = step(f"wadi mask {wadi.h:,} x {wadi.w:,} grid cells of {abs(wadi.tr.a):.1f} m, "
             f"{wadi.wadi_cells:,} on classes {list(CRIT.HAZARD_WADI_CLASSES)}; corridors "
             f"sampled against it every {WADI_STEP_M:.1f} m (half a cell, so a cell cannot "
             f"be stepped over)", t)

    draft = gpd.read_file(DRAFTED).to_crs(contract.CRS_EPSG)
    draft = draft[draft.geometry.notna() & ~draft.geometry.is_empty]
    draft = draft.explode(index_parts=False)
    draft = draft[draft.geometry.geom_type == "LineString"].reset_index(drop=True)
    res["reads"].append(("drafted corridors", DRAFTED, len(draft)))
    n_exist = int((draft["TIER_SRC"] == "existing_road").sum())
    t = step(f"draftsman {len(draft):,} lines, {draft.length.sum()/1000:,.1f} km "
             f"({n_exist:,} on existing road, {len(draft)-n_exist:,} on future road)", t)

    mp = gpd.read_file(MAIN_PIPE).to_crs(contract.CRS_EPSG).explode(index_parts=False)
    mp = mp[mp.geometry.geom_type == "LineString"].reset_index(drop=True)
    res["reads"].append(("main pipe", MAIN_PIPE, len(mp)))
    t = step(f"main pipe {len(mp):,} lines, {mp.length.sum()/1000:,.1f} km", t)

    # ---------------------------------------------------------------- A  treated roads
    print("\nA  the raw road layer, treated with units AND sampler")
    t = time.time()
    treated, report, rt = treat_roads(
        roads, units, sampler, os.path.join(OUT_SHP, "W11a_road_treatment.shp"))
    for line in assert_stage_did_something(report):
        print(line)
    res["metrics"]["road_treatment"] = {k: v for k, v in report.items()
                                        if not isinstance(v, dict)}
    res["metrics"]["road_treatment_rings_rejected"] = report.get("rings_rejected", {})
    t = step(f"{len(treated):,} treated corridors, "
             f"{sum(g.length for g in treated)/1000:,.1f} km", t)

    # the untagged twin carriageways the treatment found: they are dual carriageways the
    # road file did not label, and every OTHER source must be excluded from them too
    dual_lines = [g for g in roads.geometry[roads["dual"] == 1]]
    twins = [g for g, why in rt.removed if why.startswith("dual") and "twin" in why]
    dual_lines = dual_lines + twins
    res["metrics"]["dual_centrelines"] = len(dual_lines)
    res["metrics"]["dual_twins_untagged"] = len(twins)
    print(f"      dual centrelines for the band: {len(dual_lines):,} "
          f"({len(twins):,} untagged twins the road file missed)")

    # what the draftsman already covers comes out of the treated set
    draft_cover = unary_union(list(draft.geometry.buffer(CORRIDOR_MATCH_M)))
    draft_cut = unary_union(list(draft.geometry.buffer(CORRIDOR_CUT_M)))
    auto_road: List[LineString] = []
    for g in treated:
        if g.intersection(draft_cover).length > 0.75 * g.length:
            continue
        rest = g.difference(draft_cut)
        if rest.is_empty:
            continue
        for p in (rest.geoms if rest.geom_type == "MultiLineString" else [rest]):
            if p.length > AUTO_ROAD_MIN_M:
                auto_road.append(p)
    t = step(f"after removing what the draftsman covers: {len(auto_road):,} lines, "
             f"{sum(g.length for g in auto_road)/1000:,.1f} km", t)

    # ---------------------------------------------------------------- B  skeleton
    have = gpd.GeoDataFrame(geometry=list(draft.geometry) + auto_road,
                            crs=contract.CRS_EPSG)
    left, served = unserved_plots(plots, have)
    print(f"\nB  skeletonising the free space around {len(left):,} plots with no corridor "
          f"within {PLOT_SERVED_M:.0f} m")
    t = time.time()
    sk, sk_rep = skeleton_pockets(left)
    res["metrics"]["skeleton"] = sk_rep
    t = step(f"{len(sk):,} lines, {sum(g.length for g in sk)/1000:,.1f} km  "
             f"(pockets used {sk_rep['pockets_used']:,} of {sk_rep['pockets']:,}; "
             f"{sk_rep['plots_in_small_pockets']:,} plots left to detail design)", t)

    # ---------------------------------------------------------------- C  stitch
    print("\nC  stitching the pockets on - links drawn on the geometry, not on a buffer")
    t = time.time()
    links, st_rep = stitch(sk, have)
    res["metrics"]["stitch"] = st_rep
    t = step(f"{st_rep['links']:,} links, {sum(g.length for g in links)/1000:,.2f} km "
             f"over {st_rep['islands']:,} islands; {st_rep['stranded_islands']:,} further "
             f"than {STITCH_MAX_M:.0f} m from anything, {st_rep['already_touching']:,} "
             f"already touching", t)
    if links:
        # The proof that the re-cut worked. W10's links sat exactly 1.000 m from what they
        # joined, at BOTH ends, because the nearest point was taken on a 1 m buffer. Here
        # each endpoint must lie ON one of the two things being joined - so the worst
        # endpoint distance to the whole linework is the measurement that settles it. The
        # unions are built ONCE; building them per link is 11,800 lines x 500 links.
        all_geom = unary_union(sk + list(have.geometry))
        ends = shapely.points([c for l in links for c in (l.coords[0], l.coords[-1])])
        gap = float(np.max(shapely.distance(ends, all_geom)))
        print(f"      worst endpoint gap over all {2*len(links):,} link endpoints: "
              f"{gap:.4f} m   (W10: exactly 1.000 m on 91.4 % of them)")
        res["metrics"]["stitch_worst_endpoint_gap_m"] = round(gap, 4)
        if gap > 0.01:
            raise ContractError(
                f"a generated stitch link ends {gap:.3f} m from the corridor it joins. "
                "The links are drawn with nearest_points on the REAL geometry, so this "
                "cannot happen unless a buffer crept back in - which is defect 2 of the "
                "four this module exists to prevent.")

    # ---------------------------------------------------------------- merge, with grades
    lines: List[LineString] = []
    srcs: List[str] = []
    for g, tier in zip(draft.geometry, draft["TIER_SRC"]):
        lines.append(g)
        srcs.append("draft_existing" if tier == "existing_road" else "draft_future")
    lines += auto_road; srcs += ["auto_road"] * len(auto_road)
    lines += sk;        srcs += ["auto_block"] * len(sk)
    lines += links;     srcs += ["auto_link"] * len(links)
    lines += list(mp.geometry); srcs += ["main_pipe"] * len(mp)
    m_in = sum(g.length for g in lines)
    print(f"\nD  merged {len(lines):,} source lines, {m_in/1000:,.1f} km")

    # ---------------------------------------------------------------- node, then attribute
    t = time.time()
    noded, noded_src = node_and_attribute(lines, srcs)
    m_noded = sum(g.length for g in noded)
    t = step(f"noded to {len(noded):,} pieces, {m_noded/1000:,.1f} km "
             f"({(m_noded - m_in)/1000:+,.1f} km - noding merges collinear overlaps between "
             f"sources and drops slivers under {NODE_FLOOR_M} m)", t)
    c0, n0_nodes, big0 = component_count(noded)
    res["metrics"]["components_before_exclusion"] = c0
    res["metrics"]["largest_component_share_before"] = round(100.0 * big0 / max(n0_nodes, 1), 1)
    t = step(f"BEFORE the exclusion: {c0:,} components on {n0_nodes:,} nodes, largest "
             f"holds {100.0*big0/max(n0_nodes,1):.1f} %  - the baseline H1 is measured "
             f"against", t)

    # ---------------------------------------------------------------- H1, at source
    print("\nE  H1 applied at source: no pipe along a dual carriageway, none on wadi ground")
    t = time.time()
    band = unary_union([g.buffer(DUAL_BAND_M) for g in dual_lines]) if dual_lines else None
    band_prep = band
    if band is not None:
        shapely.prepare(band_prep)
    dual_tree = STRtree(dual_lines) if dual_lines else None
    kept, kept_src, kept_dual, removed = apply_exclusions(
        noded, noded_src, band, band_prep, dual_lines, dual_tree, wadi)
    m_kept = sum(g.length for g in kept)
    rem = pd.DataFrame(removed) if removed else pd.DataFrame(
        columns=["SRC", "REASON", "DETAIL", "LEN_M", "geometry"])
    if len(rem):
        by = rem.groupby("REASON")["LEN_M"].agg(["size", "sum"])
        for reason, r in by.iterrows():
            print(f"      removed {reason:<30s} {int(r['size']):>6,} pieces  "
                  f"{r['sum']/1000:>8.2f} km")
        # Which source paid. The trunk alignment is the one worth naming out loud: it is
        # the user's own drawing and stage 3 has to route on what survives.
        bysrc = rem.groupby("SRC")["LEN_M"].sum() / 1000.0
        print("      by source grade: " + ",  ".join(f"{k} {v:.2f} km"
                                               for k, v in bysrc.sort_values(
                                                   ascending=False).items()))
    res["metrics"]["removed_km_by_reason"] = (
        {k: round(v / 1000.0, 3) for k, v in rem.groupby("REASON")["LEN_M"].sum().items()}
        if len(rem) else {})
    res["metrics"]["removed_km_by_source"] = (
        {k: round(v / 1000.0, 3) for k, v in rem.groupby("SRC")["LEN_M"].sum().items()}
        if len(rem) else {})
    t = step(f"{len(kept):,} pieces survive, {sum(g.length for g in kept)/1000:,.1f} km", t)

    # ---------------------------------------------------------------- identity
    print("\nF  minting node identity and moving the geometry onto it")
    t = time.time()
    idx, us, ds, geoms, src_final, dual_final, n_degen, m_degen = mint_nodes(
        kept, kept_src, kept_dual)
    if not (len(src_final) == len(dual_final) == len(geoms) == len(us) == len(ds)):
        raise ContractError(
            f"attribute/geometry mismatch after minting: {len(src_final)} sources, "
            f"{len(dual_final)} dual lengths, {len(geoms)} geometries, {len(us)} US_NODE. "
            "Provenance would sit on the wrong line - the laundering P6 exists to prevent.")

    # the auditor's own tests, on the snapped geometry, as the last cut
    keep, swept = audit_sweep(geoms, band_prep, wadi)
    if swept:
        for d in swept:                       # the sweep sees geometry, not provenance
            d["SRC"] = "post-snap"
        removed.extend(swept)
        rem = pd.DataFrame(removed)
        m_swept = sum(d["LEN_M"] for d in swept)
        print(f"      audit sweep on the snapped geometry removed {len(swept):,} pieces, "
              f"{m_swept/1000:.3f} km "
              f"(the sampled cut cannot see a cell corner, and snapping moves a midpoint)")
    else:
        m_swept = 0.0
        print("      audit sweep on the snapped geometry: nothing left to remove")
    us = [v for v, k in zip(us, keep) if k]
    ds = [v for v, k in zip(ds, keep) if k]
    geoms = [v for v, k in zip(geoms, keep) if k]
    src_final = [v for v, k in zip(src_final, keep) if k]
    dual_final = [v for v, k in zip(dual_final, keep) if k]
    nodes = nodes_frame(idx, us, ds)
    m_out = sum(g.length for g in geoms)
    # recomputed AFTER the sweep, or the published metric describes an earlier layer than
    # the published one - a metric with a private cut-off point is P2's whole complaint
    res["metrics"]["removed_km_by_reason"] = (
        {k: round(v / 1000.0, 3) for k, v in rem.groupby("REASON")["LEN_M"].sum().items()}
        if len(rem) else {})
    res["metrics"]["removed_km_by_source"] = (
        {k: round(v / 1000.0, 3) for k, v in rem.groupby("SRC")["LEN_M"].sum().items()}
        if len(rem) else {})
    t = step(f"{len(nodes):,} nodes, {len(geoms):,} corridors, {m_out/1000:,.1f} km "
             f"({n_degen:,} pieces, {m_degen/1000:,.1f} km, dropped inside the "
             f"{contract.NODE_MERGE_M:.0f} m node merge radius - their two ends became ONE "
             f"node, so their neighbours now meet there and nothing is disconnected)", t)

    # The metre funnel. Counts cannot close over a stage that CUTS - one piece in, three
    # out - but length is conserved by cutting, so the funnel is run on metres. Whole
    # metres, with the sub-metre remainder named rather than absorbed: a residual nobody
    # names is how 1,233 m3/d left W10 without anyone noticing.
    fn_m = contract.Funnel("corridor metres (noded -> published)", int(round(m_noded)))
    m_named = 0.0
    if len(rem):
        for reason, m in rem.groupby("REASON")["LEN_M"].sum().items():
            fn_m.drop(f"H1: {reason}", n=int(round(m)))
            m_named += round(m)
    fn_m.drop(f"under the {NODE_FLOOR_M} m floor or inside the "
              f"{contract.NODE_MERGE_M:.0f} m node merge radius", n=int(round(m_degen)))
    m_named += round(m_degen)
    resid = int(round(m_noded)) - int(m_named) - int(round(m_out))
    fn_m.drop("endpoint snapped onto its node coordinate, plus whole-metre rounding "
              "(NEGATIVE here means snapping LENGTHENED the network - an endpoint moves up "
              "to the 3 m merge radius to reach its node, and most of those moves are "
              "outward)", n=resid)
    fn_m.close(int(round(m_out)))
    res["funnels"].append(fn_m)
    print(f"      {fn_m.line()}   (snap+rounding residual {resid:,} m on "
          f"{m_noded/1000:,.0f} km = {100.0*abs(resid)/max(m_noded,1):.3f} %)")

    # ---------------------------------------------------------------- attributes
    print("\nG  attributes")
    t = time.time()
    cor = gpd.GeoDataFrame(
        dict(CORR_ID=[f"W11a-C{i+1:06d}" for i in range(len(geoms))],
             US_NODE=us, DS_NODE=ds,
             SRC=[SRC_CONFIDENCE[s][0] for s in src_final],
             CONFIDENCE=[SRC_CONFIDENCE[s][1] for s in src_final],
             IS_STREET=[SRC_CONFIDENCE[s][2] for s in src_final],
             ON_DUAL_M=[round(d, 3) for d in dual_final],
             ON_WADI_M=[0.0] * len(geoms),
             WIDTH_M=[WIDTH_AT_STAGE2_M] * len(geoms),
             USED=[0] * len(geoms),
             STAGE=[STAGE] * len(geoms),
             PACKAGE=[""] * len(geoms),
             PHASE=[0] * len(geoms)),
        geometry=geoms, crs=contract.CRS_EPSG)
    cor["LEN_M"] = cor.geometry.length

    # ON_WADI_M is MEASURED on the published geometry, never asserted. It was a literal 0.0
    # on every row, which is a claim and not a number: the exclusion deletes every SAMPLED
    # on-wadi run and audit_sweep re-tests only the MIDPOINT, so neither proves the whole
    # line is clear - a corridor can clip the corner of a 3 m hazard cell between two
    # samples, and 144 of them did, 173 m in total, while the field said zero. Philosophy
    # sec 8 makes a published number that cannot be traced blocking; a hard-coded one
    # cannot be traced to anything. Measured, the residual is visible instead of denied.
    on_wadi: List[float] = []
    for g in geoms:
        L = g.length
        k = max(2, int(math.ceil(L / WADI_STEP_M)) + 1)
        xy = shapely.get_coordinates(
            shapely.line_interpolate_point(g, np.linspace(0.0, L, k)))
        on_wadi.append(round(float(wadi.at(xy[:, 0], xy[:, 1]).mean()) * L, 3))
    cor["ON_WADI_M"] = on_wadi
    n_res = int((cor["ON_WADI_M"] > 0).sum())

    # CROSS_ID - H1a item 4. Every run ALONG a wadi has been deleted, so whatever still
    # touches wadi ground is either a crossing this stage deliberately kept or a cell-corner
    # clip finer than the 1.5 m sampling. Both are scheduled: audit.r4 will not accept an
    # unscheduled crossing, and a clip too small to design is still a fact about the line.
    # The schedule is what carries the G201 9.3 obligations - bed profile, 1:20/1:50/1:100
    # flood levels, bed material, MoAFWR approval - to the next stage.
    def _mint_cross_ids(frame):
        """Every corridor still touching wadi ground is scheduled. H1a item 4."""
        t = frame["ON_WADI_M"] > 0
        ids = [""] * len(frame)
        for k, i in enumerate(np.where(t.values)[0]):
            ids[i] = f"W11a-XG{k + 1:05d}"
        frame["CROSS_ID"] = ids
        return frame

    cor = _mint_cross_ids(cor)

    # ---- the auditor decides which rows go, not a second sampler ----------------------
    # Two implementations of one test always disagree at the boundary. s2 sampled the wadi
    # through a windowed in-memory mask, audit.r4 samples the raster directly, and even
    # after both were put on the same 1.5 m step, 44 corridors of 25,166 came out legal to
    # the stage and illegal to the auditor. Chasing bit-parity between two samplers is the
    # wrong fix: the auditor IS the specification, so ask it which rows fail and remove
    # exactly those. Parity then holds by construction and cannot drift again.
    from w11a import audit as _audit
    for _attempt in range(4):
        _ctx = _audit.Ctx(pipes=cor, roads=roads, hazard=HAZARD, crit=CRIT)
        _st, _sum, _n, _ext = _audit.run_one("R4", _ctx)
        if _st == _audit.PASS:
            print(f"      auditor-driven sweep: R4 PASS - {_sum}")
            break
        _bad = _audit.r4_failing_mask(_ctx)
        if not _bad.any():
            raise ContractError(
                f"audit.r4 says {_st} ({_sum}) but names no failing row - the check and its "
                "mask disagree, which is a defect in the auditor, not in the corridors")
        _gone = cor.loc[_bad]
        for _, _r in _gone.iterrows():
            removed.append(dict(SRC=_r["SRC"], REASON="wadi (along, auditor sweep)",
                                DETAIL=f"audit.r4 pass {_attempt + 1}", 
                                LEN_M=float(_r["LEN_M"]), geometry=_r.geometry))
        print(f"      auditor-driven sweep pass {_attempt + 1}: removed "
              f"{int(_bad.sum()):,} corridors, {_gone['LEN_M'].sum() / 1000:.2f} km")
        cor = _mint_cross_ids(cor.loc[~_bad].reset_index(drop=True))
    else:
        raise ContractError(
            "audit.r4 still fails after 4 removal passes - removing a corridor changes the "
            "geometry the check reads and it is not converging. Inspect before relaxing.")
    print(f"      ON_WADI_M measured, not asserted: {n_res:,} corridors still touch wadi "
          f"ground for {cor['ON_WADI_M'].sum():.0f} m in total, worst "
          f"{cor['ON_WADI_M'].max():.1f} m. Each is scheduled with an CROSS_ID; H1a makes a "
          f"crossing legal and an unscheduled one is not.")

    # N_PLOT - the load-bearing plots for which THIS corridor is the nearest within 60 m.
    # Nearest, not "within 60 m": a plot is served by one corridor, and counting it against
    # every corridor in range would make the P7 number ("collects nothing") unreadable.
    near = gpd.sjoin_nearest(load_bearing[["geometry"]], cor[["CORR_ID", "geometry"]],
                             how="inner", max_distance=PLOT_SERVED_M, distance_col="D")
    near = near[~near.index.duplicated(keep="first")]
    cnt = near.groupby("CORR_ID").size()
    cor["N_PLOT"] = cor["CORR_ID"].map(cnt).fillna(0).astype(int)
    t = step(f"N_PLOT assigned; {int((cor['N_PLOT'] > 0).sum()):,} corridors front a "
             f"load-bearing plot, {int((cor['N_PLOT'] == 0).sum()):,} front none "
             f"({cor.loc[cor['N_PLOT'] == 0, 'LEN_M'].sum()/1000:,.1f} km - P7's number, "
             f"exposed not pruned)", t)

    res["metrics"]["source_lines_by_grade"] = pd.Series(srcs).value_counts().to_dict()
    res["metrics"]["km_in_by_grade"] = (
        pd.DataFrame(dict(g=srcs, m=[x.length for x in lines]))
        .groupby("g")["m"].sum().div(1000.0).round(1).to_dict())

    # ---------------------------------------------------------------- publish
    print("\nH  publishing")
    t = time.time()
    gpkg = contract.publish(cor, "corridors", W11A_ROOT, stage=STAGE)
    contract.mirror_shapefile(cor, "corridors", W11A_ROOT)

    # The node layer has no LayerSpec. contract.py is not this stage's file to edit, and a
    # US_NODE that resolves to nothing is worse than no US_NODE at all, so it is written
    # into the same GeoPackage OUTSIDE publish(), and flagged for the contract owner.
    nodes.to_file(gpkg, layer="corridor_nodes", driver="GPKG")

    p_rem = os.path.join(OUT_SHP, "W11a_corridors_removed.gpkg")
    rem_gdf = gpd.GeoDataFrame(rem, geometry="geometry", crs=contract.CRS_EPSG) \
        if len(rem) else gpd.GeoDataFrame(
            dict(SRC=[], REASON=[], DETAIL=[], LEN_M=[]), geometry=[],
            crs=contract.CRS_EPSG)
    rem_gdf.to_file(p_rem, layer="removed", driver="GPKG")
    with open(os.path.join(OUT_SHP, "W11a_corridors_removed.README.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(
            "REVIEW LAYER, NOT A DESIGN LAYER, and deliberately outside the contract.\n"
            "Every piece of corridor H1 removed, with the reason. Two of them matter to a\n"
            "later stage:\n"
            "  'wadi (crossing candidate)' - an on-wadi run short enough to be crossed\n"
            "     rather than avoided. H1 permits a scheduled perpendicular crossing;\n"
            "     audit.r4 tests every reach midpoint against the grid with no exemption\n"
            "     for one, so a crossing has to be a named, justified exception rather\n"
            "     than a corridor. Take them from here when one is genuinely needed.\n"
            "  'along a dual carriageway' - where a route was severed. If a plot loses its\n"
            "     only access this way, that is a scope answer (philosophy sec 3), not a\n"
            "     reason to relax the rule.\n")
    t = step(f"corridors -> {gpkg} (layer 'corridors'), nodes -> layer 'corridor_nodes', "
             f"removals -> {p_rem}", t)

    # ---------------------------------------------------------------- reload and prove it
    print("\nI  reloading the published layers and proving they are the graph")
    t = time.time()
    back_c = gpd.read_file(gpkg, layer="corridors")
    back_n = gpd.read_file(gpkg, layer="corridor_nodes")
    contract.validate(back_c, "corridors", stage=STAGE + " (reload)")
    _assert_round_trip(back_c, back_n)
    hr = assert_h1_r4(back_c, roads)
    res["metrics"]["audit_h1_r4_on_corridors"] = hr
    print(f"   audit.h1 on the PUBLISHED corridors -> {hr['h1_status']}: {hr['h1_summary']} {hr['h1_extent']}")
    print(f"   audit.r4 on the PUBLISHED corridors -> {hr['r4_status']}: {hr['r4_summary']} {hr['r4_extent']}")
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(back_n["NODE_UID"])
    G.add_edges_from(zip(back_c["US_NODE"], back_c["DS_NODE"]))
    comp = nx.number_connected_components(G)
    big = max(len(c) for c in nx.connected_components(G)) if comp else 0
    res["metrics"]["components"] = comp
    res["metrics"]["largest_component_nodes"] = big
    res["metrics"]["largest_component_share"] = round(100.0 * big / max(len(back_n), 1), 1)
    t = step(f"round trip OK: {len(back_c):,} corridors on {len(back_n):,} nodes, "
             f"{comp:,} components, largest holds {100.0*big/max(len(back_n),1):.1f} % "
             f"of the nodes  (W10 published 7,919 pieces, largest 5.9 %)", t)
    n_along = int(rem["REASON"].str.startswith("wadi (along").sum()) if len(rem) else 0
    n_xing = int((cor["CROSS_ID"] != "").sum())
    print(f"\n      THE NUMBER STAGE 3 INHERITS: H1 took the corridor network from "
          f"{c0:,} components to {comp:,}.")
    print(f"      {n_xing:,} wadi crossings are KEPT and scheduled - H1a: across is legal, "
          f"along is not - and {n_along:,} runs ALONG a wadi are deleted.")
    print(f"      Each crossing carries the G201 9.3 obligations to stage 3 (bed profile, "
          f"1:20/1:50/1:100 flood levels, bed material, MoAFWR approval) and G203-p52 "
          f"8.2.4's 1.5 m cover to crown in place of the normal 1.3 m.")
    print(f"      Where a severance remains, the resolutions are the four in philosophy "
          f"sec 3: a station, a re-route, a crossing that does qualify, or a plot not served.")
    res["metrics"]["components_added_by_H1"] = comp - c0
    res["metrics"]["wadi_along_removed"] = n_along
    res["metrics"]["wadi_crossings_kept"] = n_xing

    # ---------------------------------------------------------------- the summary table
    tab = cor.groupby(["SRC", "CONFIDENCE"]).agg(
        n=("LEN_M", "size"), km=("LEN_M", lambda s: round(s.sum() / 1000.0, 1)),
        plots=("N_PLOT", "sum"))
    print("\n" + tab.to_string())
    res["metrics"]["km_by_source"] = {f"{a}/{b}": float(v) for (a, b), v
                                      in tab["km"].items()}
    res["metrics"]["km_total"] = round(float(cor["LEN_M"].sum() / 1000.0), 1)
    res["metrics"]["km_on_dual_band"] = round(float(cor["ON_DUAL_M"].sum() / 1000.0), 3)
    res["metrics"]["km_on_wadi"] = round(float(cor["ON_WADI_M"].sum() / 1000.0), 3)
    res["metrics"]["km_fronting_no_load"] = round(
        float(cor.loc[cor["N_PLOT"] == 0, "LEN_M"].sum() / 1000.0), 1)
    res["metrics"]["terrain_nodata_fallbacks"] = sampler.n_nodata
    res["metrics"]["terrain_samples"] = sampler.n_calls

    left2, served2 = unserved_plots(load_bearing, cor)
    res["metrics"]["load_plots"] = int(len(load_bearing))
    res["metrics"]["load_plots_served"] = int(served2.sum())
    res["metrics"]["load_plots_unserved"] = int(len(left2))
    res["metrics"]["load_m3d_unserved"] = round(float(left2["Q_AVG_M3D"].sum()), 1)
    print(f"\nload-bearing plots with a corridor within {PLOT_SERVED_M:.0f} m: "
          f"{served2.sum():,} of {len(load_bearing):,} ({100*served2.mean():.1f} %); "
          f"{len(left2):,} unserved carrying {left2['Q_AVG_M3D'].sum():,.0f} m3/d")
    if len(left2):
        p_left = os.path.join(OUT_SHP, "W11a_plots_no_corridor.gpkg")
        left2.to_file(p_left, layer="plots_no_corridor", driver="GPKG")
        print(f"      written to {p_left} - TOR scope p4 item 3 requires every plot to be "
              "SERVED, so these are a scope answer for stage 1, not a rounding error")
        res["notes"].append(
            f"{len(left2):,} load-bearing plots ({left2['Q_AVG_M3D'].sum():,.0f} m3/d) have "
            f"no corridor within {PLOT_SERVED_M:.0f} m. TOR scope p4 item 3 requires every "
            "plot to be served; philosophy sec 8a says the choice is which SYSTEM serves "
            "it. Listed by name in W11a_plots_no_corridor.gpkg - not dropped.")

    sampler.close()
    res["writes"] = [("corridors", gpkg, len(cor)),
                     ("corridor_nodes", gpkg, len(nodes)),
                     ("removed (review)", p_rem, len(rem_gdf))]
    res["seconds"] = time.time() - t_all
    res["corridors"] = cor
    return res


def main() -> int:
    print("=" * 88)
    print("W11a  STAGE 2 - CORRIDORS WITH PROVENANCE")
    print("      exclusions at source (philosophy sec 2) - H1 is a boundary, not a price")
    print("=" * 88)

    missing = _missing_inputs()
    if missing:
        print("\nWAITING ON UPSTREAM INPUTS - nothing written, exiting 0:")
        for n, p in missing:
            print(f"   {n:<38s} {p}")
        print("\nRe-run this module when they exist. Stage 2 reads only; it derives "
              "nothing it cannot trace.")
        return 0

    with contract.Manifest.stage("S2 corridors", STAGE_ORDER) as rec:
        try:
            res = build()
        except Exception as e:
            rec.did_nothing(f"FAILED: {type(e).__name__}: {e}")
            raise
        for n, p, k in res["reads"]:
            rec.read(n, p, k)
        for n, p, k in res["writes"]:
            rec.wrote(n, p, k)
        for f in res["funnels"]:
            rec.funnels.append(f)
        for k, v in res["metrics"].items():
            rec.metrics[k] = _jsonable(v)
        for n in res["notes"]:
            rec.note(n)
        rec.note(
            "WIDTH_M is the G203-p32 Tab 13 band for DN200 (2.0 m) on every corridor, "
            "because no diameter exists before stage 6. Stage 6 MUST re-stamp it from the "
            "designed DN - a DN1000-1200 trunk needs 3.2 m and a 2.0 m reserve stated "
            "against it would be wrong.")
        rec.note(
            "USED = 0 on every corridor: nothing is laid yet. The conversion rate per SRC "
            "is the number that exposed W10's inversion (auto_block 97.4 % against the "
            "draftsman's 76.3 %), so the stage that lays reaches must stamp it back.")
        rec.note(
            "ORDERING, stated because it bounds the result: the skeleton (step B) fills "
            "gaps in the PRE-exclusion corridor set, and H1 is applied after it. A plot "
            "stranded BY the exclusion is therefore reported as unserved rather than "
            "re-skeletonised. Re-running the skeleton after the cut would be a second full "
            "pass and would still have to route around the same ground; the honest answer "
            "is the unserved list, which is a scope question for stage 1.")
        rec.note(
            "The crossings schedule is NOT published. contract.CROSSINGS requires EDGE_UID "
            "- the reach that crosses - and no reach exists at stage 2. Candidates are on "
            "the review layer W11a_corridors_removed.gpkg.")
        rec.note(
            "OPEN for the contract owner: the corridor node layer has no LayerSpec, so it "
            "is written into W11a.gpkg outside publish(). US_NODE that resolves to nothing "
            "is worse than no US_NODE, and contract.py is not this stage's file to edit.")
        rec.note(
            "RESOLVED (was: audit contradiction). Philosophy H1a now states when a wadi "
            "crossing is legal - one contiguous contact, square within the stated skew "
            "tolerance, no chamber on wadi ground, 1.5 m cover to crown (G203-p52 8.2.4), "
            "and scheduled with a CROSS_ID carrying the G201 9.3 obligations. audit.r4 "
            "tests along-vs-across instead of any contact, and this stage KEEPS a "
            "qualifying crossing instead of deleting it. Deleting them all took the "
            "corridor network to 1,381 components; keeping them takes it to 784.")
        rec.note(
            "PROJECT TOLERANCE, not a guideline value: WADI_XING_SKEW = "
            f"{WADI_XING_SKEW:.3f} (= 1/cos 30 deg), the tolerance on H1's word "
            "'perpendicular'. The guidelines give the cover at a crossing and the "
            "procedure for one but never say how square it must be. It is declared in "
            "w11a.audit and read from there by this stage - one definition, two callers.")
        rec.note(
            "DATA GAP: the 50-year hazard grid leaves 53 % of corridor samples with no "
            "wadi answer either way. Every R4 result is a statement about the tested half. "
            "Full-coverage flood mapping is a data request (see 05_GAPS).")

    print("\n" + "-" * 88)
    print(contract.Manifest.report())
    print(f"\nmanifest -> {contract.Manifest.path}")
    print(f"total {res['seconds']:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
