"""W11a stage 6 - LEVELS AND SIZES. The core solver.

WHAT THIS STAGE IS FOR, AND WHY IT IS SIXTH.

`_BRAIN/08_DESIGN_PHILOSOPHY.md` sec 2 puts levels and sizes SIXTH, after the corridors, the
trunk, the hierarchy and the chambers, and it says why: "Stage 3 before stage 6. A trunk that
emerges from accumulated flow is not a trunk." This module therefore chooses NOTHING about
layout. It takes a graph of chambers and reaches that stages 1-5 settled, and it answers the
two questions software is actually good at - how big is each pipe, and where does it sit -
plus the one question the philosophy insists a solver may never answer on its own: where the
ground beats us and a lifting station is required (sec 5, the cap-and-veto ladder).

THE ORDER OF OPERATIONS IS BENTLEY'S, NOT OURS.

`W10/docs/research/SEWERGEMS_DESIGN_METHOD.md` reads Bentley's published design-engine
description (SewerCAD/SewerGEMS "Design Priorities", verbatim, sources S1/S2). The circularity
of gradient and diameter - you cannot know the capacity-controlling gradient until you have a
gradient, and you cannot fix the invert until you know the rise - is resolved there by a
sequence, not by iterating to convergence:

    bracket the diameter range  ->  LEVEL A  ->  size for capacity  ->  LEVEL B
    (steps 3-4)                     (5-13)      (step 14)              (15-22)

then a second, much shorter pass from the outfall back upstream:

    1 adjust downstream STRUCTURE elevation to match the conduit downstream invert
    2 adjust conduit downstream invert to match a fixed structure
    3 adjust conduit upstream invert to match maximum slope
    4 adjust conduit upstream invert to match a fixed structure

Two details from that research carry the whole method and are implemented literally:

  * **The reverse pass is a reconciliation, not a re-solve.** Its first operation moves the
    MANHOLE to the pipe, not the pipe to the manhole. Four operations, no sizing step, no
    cover step, no minimum-slope step. It exists to fix the one thing a forward-only sweep
    cannot - a downstream decision that invalidates an upstream structure elevation.

  * **Level B translates the pipe RIGIDLY (Bentley steps 16-17 "adjust both ends").** A
    rotation would destroy the gradient step 14 was sized against, and here it would also
    destroy the round 0.05 % gradient P1 requires - the number the drawing depends on. Every
    move in this module that re-seats a pipe against cover or against a structure moves both
    ends together; only a move that is ABOUT the gradient (minimum slope, maximum slope) is
    allowed to change it.

WHAT WE REJECT FROM BENTLEY, deliberately, per that research's sec 9.2:

  * Bentley demotes maximum cover and maximum velocity as "too limiting". Maximum cover is
    our 12 m rule (G203-p33) and it is the single constraint that decides whether a pumping
    station exists; adopting the demotion would be adopting W10's exact failure. Maximum
    velocity (H7, 3.0 m/s, G203-p27) is enforced here as a real constraint - a reach that
    cannot be laid slowly enough is UPSIZED, and if the levels then demand more fall than
    v <= 3.0 m/s allows, the surplus is taken as a drop at the chamber (philosophy sec 5),
    never as a faster pipe.
  * Bentley will deepen forever and never propose a station. The ladder below does.

THE W10 FAILURES THIS MODULE EXISTS TO PREVENT, each named where it is prevented:

  | W10 shipped                          | Prevented by                                     |
  |--------------------------------------|--------------------------------------------------|
  | 2.80 km of SURCHARGED trunk          | `_size_reach` - capacity is tested at the reach's |
  |                                      | own laid gradient against its d/D limit, and the  |
  |                                      | published DOD_PK/V_PK_MS are recomputed at the    |
  |                                      | EXACT flow, not the quantised search value        |
  | 10.68 km over the d/D limit          | same test; "dod" is a recorded SIZED_BY cause     |
  | 45.92 km below 1.30 m COVER, from a  | every depth comes from `contract.min_invert_depth`|
  | hardcoded 0.30 m allowance           | and every cover from `contract.cover()` - one     |
  |                                      | definition, on the reach's OWN outside diameter   |
  | no laid gradient published, only the | SLOPE_LAID **and** SLOPE_MIN on every reach, and  |
  | minimum - so nothing was checkable   | the pair is what audit G1 tests for               |
  | no constraint provenance             | GRAD_BY and SIZED_BY on every reach (audit G2)|
  | chambers past 12 m unflagged         | the cap-and-veto ladder, PAST_CAP + CAP_EXIT +    |
  |                                      | CAP_LEN_M, and a station where no exit applies    |
  | node layer and pipe layer from       | node levels are SEATED onto the pipes in the      |
  | different solves, 10.39 m apart      | reverse pass and written in the same transaction  |

THE CAP-AND-VETO LADDER (philosophy sec 5), implemented exactly as written:

    1 CAP        cover reaches 12 m -> station, unless an exit applies
    2 VETO       a chamber that cannot be maintained -> station. Not a term in a sum
    3 ECONOMICS  only now: is a station cheaper over 25 years?

Rungs 1 and 2 can only ADD a station. This module implements rung 1 (it is the only rung that
is computable from levels alone) and leaves rungs 2 and 3 to the station stage, which is where
plant access, rescue routes and 25-year cost live. **Past the cap there are two exits, either
alone sufficient: the cover recovers within 500 m, or the run reaches the outfall within
1,000 m.** Everything past 12 m carries PAST_CAP=1, the exit that allowed it, and the distance
that proves the exit - because both exits are DISTANCE-bounded, the distance is the evidence.
Nothing past the cap is final: it waits on a manufacturer's rating for that cover and on NWS's
station establishment cost, and both are named in the register this stage writes.

THE DROP CEILING, AND WHY IT SITS INSIDE THE LADDER RATHER THAN BESIDE IT.

G203-p30 is the only clause on drops and it is quoted here in full because the rule is easy
to half-remember: "Drops are sometimes required at manholes when a branch sewer adjoins a
trunk sewer. Connections under these conditions require the use of a backdrop when the
difference in invert elevations exceeds 600 mm. Backdrops shall be constructed external to
the manhole... The maximum backdrop height should be of 2 m. Beyond this limit, specific
devices like vortex drop shafts should be used." Note what is NOT there: the guideline gives
a maximum for a BACKDROP and **no maximum at all for a vortex drop shaft**. Read literally it
would let a chamber take a drop of any height, and a run on the full area does exactly that -
measured 2026-09-02, four chambers wanted 21.5 to 35.1 m.

What forbids it is philosophy sec 5, in terms: **"Never a drop used to dodge a station."** A
35 m fall into a chamber is not a drop structure, it is the shadow of a trench nobody will
dig, and every shallow branch on that run pays for it. So the ceiling on a drop is a PROJECT
DECISION, not a guideline number, and it is read at run time from `contract.NODES.DROP_M.hi`
so the design and the validator cannot drift apart - the contract is the written artefact
that carries it, and nothing here invents a value.

The consequence is a ladder step, not a clamp. A breach that the two sec 5 exits would let
past the 12 m cap, but whose levels force a drop above that ceiling somewhere on the run, is
a breach buying its way past the cap WITH A DROP - so the exit is not available to it, and
the fourth physical resolution is taken at the head of the breach exactly as it is for a
breach that never had an exit. Nothing about the exits' distances changes; the cap does not
move; DROP_M is never rounded, clipped or capped. Where a drop above the ceiling survives
every pass, the stage REFUSES TO PUBLISH and names the chambers, because the resolutions left
are a re-route or not serving that branch (philosophy sec 3) and neither is stage 6's to take.

A note on the direction of the answer, because it is the thing that reads wrong at first: a
station is never put AT the over-deep chamber. A drop is flow going down and a station lifts
flow up, so pumping cannot resolve a fall. The station goes at the FOOT OF THE CLIMB - the
last chamber inside the cap, the head of the breach - which is where the ladder already puts
one, and it is the deep main that then never exists, not the branch that then never drops.

WHAT A STATION IS HERE, STATED PLAINLY SO IT IS NOT MISREAD. Where the cap is breached and
neither exit applies, the fourth physical resolution (philosophy sec 3) is taken: a station.
This module represents it as a LIFT INSIDE THE CHAMBER - the chamber's outgoing invert is
re-seated at minimum cover, the arriving invert stays where the gravity network put it, and
the difference is the static lift. The wet well, the duty, the rising main and the discharge
chamber are NOT designed here; they are stage 7's, and every lift is written to
`run/s6_station_demand.csv` with the evidence that no exit applied. Consequence to know: at a
station node the published DEPTH_M is the SHALLOW outgoing depth, because the contract defines
INV_M as the outgoing reach's invert. The true wet-well depth is in the register, not on the
node layer. This is declared, not hidden.

WHAT THIS STAGE DOES NOT DO. It does not move a chamber, add one, remove one, or change a
reach's geometry or its length. It does not choose a route. It does not size a rising main or
a wet well. It does not decide the served set. Every one of those was settled upstream, and a
solver that quietly re-opened them would be doing exactly what philosophy sec 7 forbids: "No
solver chooses a layout."

Sources for every number used: `_BRAIN/02_DESIGN_CRITERIA.md` via `W8/py/sewnet/criteria.py`
(cited per value there); the hydraulics are `W8/py/sewnet/hydra.py` UNMODIFIED, reached
through the contract's own re-export so there is one copy and no chance of a second; the field
names, the enums and the depth definition are `w11a.contract`.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# The contract is imported hard and its field names are used, never our own. It also
# re-exports `sewnet.hydra` and `sewnet.criteria.DEFAULT`, so the design numbers and the
# hydraulics reach this module through exactly one path - which is the point of P2.
from w11a import contract as K            # noqa: E402
from w11a.contract import ContractError   # noqa: E402

C = K.C                                   # sewnet.criteria.DEFAULT - the design basis
H = K.hydra                               # sewnet.hydra, unmodified

import geopandas as gpd                   # noqa: E402
import networkx as nx                     # noqa: E402
from shapely.geometry import LineString    # noqa: E402,F401

STAGE = "S6"
STAGE_ORDER = 6

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"
TERRAIN_VRT = os.path.join(BASE, "Data", "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt")


# ======================================================================================
# Options. Every value is either a criteria constant (cited where it is defined) or a
# philosophy number, or it is a declared method choice with its reason. Nothing is invented.
# ======================================================================================

# The ceiling on a drop STRUCTURE, read from the contract rather than written here. G203-p30
# gives 2 m for a backdrop and NO maximum for the vortex drop shaft that replaces it, so this
# number cannot be quoted from the guideline; it is a PROJECT DECISION and the contract is
# where the project already wrote it down. Reading it means the design and the validator move
# together or not at all - a hardcoded copy here is exactly how a stage ends up publishing a
# value its own contract refuses.
_DROP_CEILING_M = float(
    getattr(K.NODES.field("DROP_M"), "hi", None) or C.BACKDROP_MAX)

# The ceiling on the LAID GRADIENT, read the same way and for the same reason. G203 sets no
# maximum gradient for a gravity sewer - the only maximum it gives is H7's 3.0 m/s (p27), and
# that never binds on the pipe this matters for: a DN200 lateral carrying a fraction of a
# litre per second runs at d/D under 0.03 and reaches 0.8 m/s on a 49 % slope. So without this
# the solver lays the pipe down the cliff, which philosophy sec 5 forbids in terms: "on steep
# ground the pipe does not follow the cliff. Hold the gradient and take the difference at a
# drop chamber." PROJECT DECISION, carried by contract.REACHES.SLOPE_LAID.hi.
_SLOPE_CEILING_PCT = float(
    getattr(K.REACHES.field("SLOPE_LAID"), "hi", None) or 25.0)

# The bedding allowance below the crown is NOT the same number in the two files that use it,
# and the difference changes sign at the cap. `contract.cover()` subtracts
# AUDITOR_OD_ALLOW_M = 0.10; `audit.od()` subtracts `crit.WALL_ALLOW` = 0.05 (its own
# docstring records the change from 0.10, and contract.py's constant did not follow). At the
# MINIMUM the contract is the conservative one - the design lays 50 mm deeper than H3 asks,
# which is harmless. At the MAXIMUM it is the optimistic one: a reach the design reads at
# 11.96 m of cover the auditor reads at 12.01 m, and H4 fails it as an unflagged breach.
# Measured 2026-09-02: 44 reaches, every one within 50 mm of the cap.
#
# So the CAP is tested on the LARGER of the two covers, and the flag it sets is a superset of
# what the auditor tests - which is what `_cover_mid` already promised and could not deliver
# while it read one definition. What is PUBLISHED stays `contract.cover()` and nothing else:
# there is one published definition, and this is a test threshold, not a second one.
_CAP_OD_ALLOW_M = min(float(K.AUDITOR_OD_ALLOW_M), float(C.WALL_ALLOW))


def _cap_cover(dn: int, invert_depth: float) -> float:
    """Cover to crown for the CAP test only - the stricter of the two definitions in play."""
    return float(invert_depth) - (int(dn) / 1000.0 + _CAP_OD_ALLOW_M)


@dataclass(frozen=True)
class SolverOptions:
    # --- philosophy sec 5, the two distance-bounded exits past the cap
    max_cover_m: float = C.MAX_DEPTH          # 12.0 m of COVER (G203-p33 via criteria)
    cap_recover_m: float = 500.0              # "the cover recovers within 500 m"
    cap_outfall_m: float = 1000.0             # "reaches the outfall within 1,000 m"

    # --- the drop ceiling. PROJECT DECISION, sourced from contract.NODES.DROP_M.hi, not from
    # G203 - see the module docstring. `drop_ceiling_mints_station` is what makes it a rung of
    # the ladder rather than a bare validation bound: switched off, the stage still refuses to
    # publish an unbuildable drop, it just has no way to resolve one.
    max_drop_m: float = _DROP_CEILING_M
    drop_ceiling_mints_station: bool = True

    # --- the cliff ceiling. PROJECT DECISION, sourced from contract.REACHES.SLOPE_LAID.hi.
    max_slope_pct: float = _SLOPE_CEILING_PCT

    # --- method choices, declared
    profile_step_m: float = 10.0
    # Bentley's "Consider Cover Along Pipe Length" (research A5): cover is checked against the
    # terrain BETWEEN the chambers, not only at them. 10 m on a 0.5 m raster over reaches that
    # H12 already caps at 100-200 m. W8 used 5 m on a test area; 10 m is the full-area choice
    # and it is a stated method choice, not a criterion.

    non_decreasing_dn: bool = True
    # Bentley design priority 4 (research S1): "Designs typically avoid sizing downstream
    # pipes smaller than upstream pipes... debris that passes through the upstream pipe could
    # become caught in the connecting structure, clogging the sewer." NOT a PAM-GUD number, so
    # it is an option, it is declared, and the reaches it governs are counted separately in
    # the run report. It is NOT oversizing-for-slope (G203-p29), which stays prohibited.

    uniform_premium_steps: int = 1
    # P1: "the same gradient carried across consecutive reaches where practical, on 0.05 %
    # steps". A carry is FREE when the reach's own required gradient rounds to the upstream
    # reach's value. Beyond that a carry costs depth, so it is bounded at ONE 0.05 % step -
    # the rounding granularity itself (criteria.SLOPE_STEP), not a new number - and it is
    # refused outright if it would push the reach past the cap, because "P1 is never bought at
    # the price of a pumping station".

    max_cap_passes: int = 30
    # The ladder adds ONE station per breach per pass - never more, because a station it turns
    # out we did not need is a real cost invented by a solver, and the conservative direction
    # is to under-mint and iterate. Each station changes every level below it, which can
    # expose the next breach, so the passes are what converge it. Bounded so a pathological
    # profile (ground rising for kilometres) cannot loop forever; if the bound is hit with a
    # breach still unresolved the stage REFUSES TO PUBLISH rather than ship a design whose
    # deepest chamber carries no flag. Measured on a 25,145-reach synthetic: a normal profile
    # settles in 1-2 passes at about 0.5 s each.

    tau_pa: float = C.TAU_PA                  # GAP-9, no numeric value in G203 (OPEN-4)

    @property
    def max_slope_k(self) -> int:
        """The cliff ceiling as a whole number of 0.05 % steps. Rounded DOWN: rounding up
        would publish a gradient above the ceiling the number came from."""
        return max(1, int(math.floor(self.max_slope_pct / K.SLOPE_STEP_PCT + 1e-9)))


# ======================================================================================
# Terrain. A tiled bilinear sampler.
# ======================================================================================

class TileSampler:
    """Bilinear terrain lookup over the 0.5 m VRT, read in tiles.

    W8's `sewnet.prep.TerrainSampler` reads ONE window covering the whole area of interest.
    That is right for a test area and impossible for this one: 531 km2 at 0.5 m is about
    46,000 x 46,000 cells, ~17 GB as float64. So this reads 1,024 m tiles on demand with a
    2-cell halo (so a bilinear 2x2 block never straddles a tile edge) and keeps a bounded
    number of them.

    NODATA returns NaN rather than raising. On a full-area run a single hard failure would
    kill the stage, and the philosophy's objection is to a SILENT 0.0, not to a counted gap:
    every NaN is counted, reported in the manifest, and falls back to the node ground level
    that stage 5 already sampled - which is a measurement, not a guess.
    """

    TILE_PX = 2048
    HALO_PX = 2

    def __init__(self, vrt_path: str, max_tiles: int = 12):
        import rasterio                      # local: only needed when terrain is used
        self.ds = rasterio.open(vrt_path)
        self.tr = self.ds.transform
        self.nodata = self.ds.nodata
        self.max_tiles = max_tiles
        self._tiles: Dict[Tuple[int, int], np.ndarray] = {}
        self._order: List[Tuple[int, int]] = []
        self.n_nodata = 0
        self.n_outside = 0

    def close(self):
        try:
            self.ds.close()
        except Exception:
            pass

    def _tile(self, tr_: int, tc_: int) -> np.ndarray:
        key = (tr_, tc_)
        got = self._tiles.get(key)
        if got is not None:
            return got
        from rasterio.windows import Window
        T, Hh = self.TILE_PX, self.HALO_PX
        win = Window(tc_ * T - Hh, tr_ * T - Hh, T + 2 * Hh, T + 2 * Hh)
        fill = self.nodata if self.nodata is not None else np.nan
        arr = self.ds.read(1, window=win, boundless=True,
                           fill_value=fill).astype("float32")
        if self.nodata is not None:
            arr = np.where(arr == np.float32(self.nodata), np.nan, arr)
        arr = np.where(np.isfinite(arr), arr, np.nan)
        self._tiles[key] = arr
        self._order.append(key)
        while len(self._order) > self.max_tiles:
            self._tiles.pop(self._order.pop(0), None)
        return arr

    def z_many(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Bilinear elevation at many points. NaN where there is no data."""
        xs = np.asarray(xs, dtype=float)
        ys = np.asarray(ys, dtype=float)
        out = np.full(xs.shape, np.nan, dtype=float)
        if xs.size == 0:
            return out
        col = (xs - self.tr.c) / self.tr.a - 0.5
        row = (ys - self.tr.f) / self.tr.e - 0.5
        r0 = np.floor(row).astype(np.int64)
        c0 = np.floor(col).astype(np.int64)
        fr = row - r0
        fc = col - c0
        T, Hh = self.TILE_PX, self.HALO_PX
        tr_ = np.floor_divide(r0, T)
        tc_ = np.floor_divide(c0, T)
        # Group by tile so each tile is read once, and process the groups largest first so
        # the bounded tile cache is used where it pays.
        keys = (tr_.astype(np.int64) << 32) ^ (tc_.astype(np.int64) & 0xFFFFFFFF)
        order = np.argsort(keys, kind="stable")
        k_sorted = keys[order]
        bounds = np.flatnonzero(np.r_[True, k_sorted[1:] != k_sorted[:-1]])
        bounds = np.r_[bounds, k_sorted.size]
        for a, b in zip(bounds[:-1], bounds[1:]):
            idx = order[a:b]
            arr = self._tile(int(tr_[idx[0]]), int(tc_[idx[0]]))
            lr = r0[idx] - (int(tr_[idx[0]]) * T - Hh)
            lc = c0[idx] - (int(tc_[idx[0]]) * T - Hh)
            ok = (lr >= 0) & (lc >= 0) & (lr + 1 < arr.shape[0]) & (lc + 1 < arr.shape[1])
            if not ok.all():
                self.n_outside += int((~ok).sum())
            i = idx[ok]
            lr, lc = lr[ok], lc[ok]
            z00 = arr[lr, lc]
            z01 = arr[lr, lc + 1]
            z10 = arr[lr + 1, lc]
            z11 = arr[lr + 1, lc + 1]
            f_r = fr[i]
            f_c = fc[i]
            out[i] = (z00 * (1 - f_r) * (1 - f_c) + z01 * (1 - f_r) * f_c
                      + z10 * f_r * (1 - f_c) + z11 * f_r * f_c)
        self.n_nodata += int(np.isnan(out).sum())
        return out


# ======================================================================================
# The reach record the solver works on. Deliberately plain: the published layer is built
# from it at the end, so nothing here can drift away from the contract's field names.
# ======================================================================================

@dataclass
class Reach:
    uid: str
    us: str
    ds: str
    length: float
    q_pk_ls: float
    tier: str
    # profile: (chainage_m, ground_m) INCLUDING both ends, for mid-span cover (Bentley's
    # "Consider Cover Along Pipe Length"; research A5)
    profile: Tuple[Tuple[float, float], ...] = ()
    dn: int = 0
    k_slope: int = 0                      # gradient as an INTEGER number of 0.05 % steps
    inv_up: float = float("nan")
    inv_dn: float = float("nan")
    drop_up: float = 0.0                  # fall given up at the upstream chamber, m
    sized_by: str = "minimum"
    gradient_by: str = "table11"
    tie_type: str = "none"
    past_cap: int = 0
    cap_exit: str = ""
    cap_len_m: float = 0.0
    cover_mid: float = float("nan")       # worst (largest) cover along the reach

    @property
    def q_m3s(self) -> float:
        return self.q_pk_ls / 1000.0

    @property
    def slope_pct(self) -> float:
        return round(self.k_slope * K.SLOPE_STEP_PCT, 8)

    @property
    def slope_frac(self) -> float:
        return self.slope_pct / 100.0


# ======================================================================================
# The solver
# ======================================================================================

class LevelSolver:
    """Bracket, level, size, re-level; then reverse-reconcile; then apply the ladder.

    One instance per run. It owns no geometry and no layer - it is handed a graph and a set
    of ground levels, and it hands back inverts, diameters and provenance.
    """

    def __init__(self, nodes: pd.DataFrame, reaches: List[Reach],
                 opts: SolverOptions = SolverOptions(), crit=C):
        self.opts = opts
        self.crit = crit
        # tau is NOT an independent knob here. `hydra.smin_tractive` reads it off `crit`, so a
        # SolverOptions with a different tau publishes a TAU_PA the layer's own gradients were
        # never computed at - a published number that does not trace to the run that produced
        # it. The sensitivity run is `replace(DEFAULT, TAU_PA=2.0)` handed in as `crit`, which
        # is the mechanism criteria.py itself documents.
        if abs(float(opts.tau_pa) - float(crit.TAU_PA)) > 1e-12:
            raise ContractError(
                f"SolverOptions.tau_pa={opts.tau_pa} but criteria.TAU_PA={crit.TAU_PA}. The "
                "tractive minimum gradient is computed from the CRITERIA object, so the "
                "option would only change the number printed on the layer. For a sensitivity "
                "run pass `dataclasses.replace(criteria.DEFAULT, TAU_PA=...)` as `crit`.")
        self.nodes = nodes                                   # indexed by NODE_UID
        self.reaches: Dict[str, Reach] = {r.uid: r for r in reaches}

        self.grd: Dict[str, float] = {}
        self.kind: Dict[str, str] = {}
        self.fixed_inv: Dict[str, float] = {}                # existing structures (H14)
        for uid, row in nodes.iterrows():
            self.grd[uid] = float(row["GRD_M"])
            self.kind[uid] = str(row["NODE_KIND"])
        for col in ("FIX_INV", "INV_FIX", "TIE_INV"):
            if col in nodes.columns:
                s = pd.to_numeric(nodes[col], errors="coerce")
                for uid, v in s.items():
                    if pd.notna(v):
                        self.fixed_inv[uid] = float(v)
                break

        self.out_edge: Dict[str, str] = {}
        self.in_edges: Dict[str, List[str]] = {}
        for r in reaches:
            if r.us in self.out_edge:
                raise ContractError(
                    f"node {r.us} has two outgoing reaches ({self.out_edge[r.us]}, {r.uid}). "
                    "H15: the network is a FOREST, and the solver cannot level a graph that "
                    "is not one - the fix belongs in the stage that built it.")
            self.out_edge[r.us] = r.uid
            self.in_edges.setdefault(r.ds, []).append(r.uid)

        g = nx.DiGraph()
        g.add_nodes_from(self.grd)
        for r in reaches:
            g.add_edge(r.us, r.ds, uid=r.uid)
        if not nx.is_directed_acyclic_graph(g):
            cyc = nx.find_cycle(g)
            raise ContractError(f"the reach graph has a cycle: {cyc[:6]}. H15 is breached "
                                "upstream of this stage; levelling a loop is meaningless.")
        self.topo: List[str] = list(nx.topological_sort(g))
        self.graph = g

        # stations minted by the ladder: node uid -> the static lift, m
        self.lift: Dict[str, float] = {}
        self.station_note: Dict[str, Dict] = {}
        # reaches that cannot reach their fixed existing invert by gravity (H14). Registered
        # by name rather than rounded away - the resolutions are all physical.
        self.tie_conflicts: List[Dict] = []
        self.node_inv: Dict[str, float] = {}

        # memos. `_state` is the only expensive call; quantising the flow for the SEARCH is
        # safe because every PUBLISHED hydraulic value is recomputed at the exact flow.
        self._m_state: Dict[Tuple[int, int, float], Tuple[Optional[float], Optional[float]]] = {}
        self._m_qlim: Dict[Tuple[int, int], Tuple[float, float]] = {}
        self.counters: Dict[str, int] = {}

    # ---------------------------------------------------------------- small helpers
    def _bump(self, key: str, n: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + n

    @staticmethod
    def _q_key(q_m3s: float) -> float:
        """Quantise a flow to 4 significant figures for the SEARCH memo only."""
        if q_m3s <= 0:
            return 0.0
        e = math.floor(math.log10(q_m3s))
        return round(q_m3s, -(e - 3))

    def _state(self, dn: int, k: int, q_m3s: float):
        """(d/D, velocity) at a grid gradient. Memoised on the quantised flow."""
        key = (dn, k, self._q_key(q_m3s))
        got = self._m_state.get(key)
        if got is None:
            s = k * K.SLOPE_STEP_PCT / 100.0
            got = H.pipe_state(dn, s, key[2], self.crit)
            self._m_state[key] = got
        return got

    def _q_caps(self, dn: int, k: int) -> Tuple[float, float]:
        """(discharge at the d/D limit, discharge at the capacity peak) for this pipe and
        gradient. Two direct `q_partial` calls - no bisection - so the sizing scan is cheap.
        Separating them is what lets SIZED_BY say 'dod' rather than 'capacity' when the pipe
        would pass the flow but only by running over its Table 10 limit."""
        key = (dn, k)
        got = self._m_qlim.get(key)
        if got is None:
            D = self.crit.internal_diameter(dn)
            s = k * K.SLOPE_STEP_PCT / 100.0
            got = (H.q_partial(D, s, H.dod_limit(dn, self.crit), self.crit),
                   H.q_partial(D, s, 0.95, self.crit))
            self._m_qlim[key] = got
        return got

    @staticmethod
    def _k_up(s_frac: float) -> int:
        """Smallest number of 0.05 % steps at or above this gradient (P1). Rounding UP is
        the rule for a single pipe: rounding down would break the minimum it was derived
        from (criteria.SLOPE_STEP, user 2026-08-23)."""
        return max(1, int(math.ceil(s_frac * 100.0 / K.SLOPE_STEP_PCT - 1e-9)))

    def _min_depth(self, dn: int) -> float:
        """`contract.min_invert_depth` and nothing else. NOT `criteria.invert_depth_min`,
        which is 50 mm shallow against audit.h3 at every diameter and would fail a BLOCKING
        check on every reach (contract EXCLUDED, OPEN-3)."""
        return K.min_invert_depth(dn)

    # ---------------------------------------------------------------- candidate diameters
    def _candidates(self, tier: str) -> List[int]:
        """The catalogue. Bentley's only genuinely hard constraint is the catalogue (research
        sec 1.2), and ours is `criteria.DN_SERIES`, which starts at DN200 - the G203-p22 Tab 6
        minimum for a lateral and a main sewer.

        DN160 is deliberately absent even though audit H9 allows a rider at 160. A rider is a
        tertiary pipe and belongs on the `connections` layer, not on `reaches`; and there is a
        trap if one appears here - `criteria.TABLE11` has no DN160 row, so
        `hydra.smin_for` would fall through to `TABLE11_FLOOR` (0.75 mm/m, the >= DN900 value)
        and hand a DN160 rider a minimum gradient 6.7x too flat, silently. Any reach arriving
        tagged 'rider' is therefore sized from DN200 and COUNTED, not quietly accepted.
        """
        if str(tier).strip().lower() == "rider":
            self._bump("reach_tagged_rider")
        return list(self.crit.DN_SERIES)

    def _dn_floor(self, r: Reach) -> Tuple[int, str]:
        """The smallest diameter this reach may take, and why.

        Two floors: the tier minimum (G203-p22 Tab 6, OD200 on a main sewer and a lateral),
        and - when the option is on - the largest upstream diameter (Bentley priority 4).
        """
        floor, why = self.crit.DN_MIN_MAIN, "tier"
        if self.opts.non_decreasing_dn:
            up = [self.reaches[e].dn for e in self.in_edges.get(r.us, ())
                  if self.reaches[e].dn]
            if up and max(up) > floor:
                floor, why = max(up), "continuity"
                # counted separately because SIZED_BY records both floors as 'minimum' - the
                # auditor's enum has no token for continuity, and widening it from here is
                # refused by the contract (EXCLUDED: "SIZED_BY = 'infeasible'"). The number
                # therefore lives in the run report, not in a quietly invented field.
                self._bump("dn_floor_by_upstream_continuity")
        return floor, why

    # ---------------------------------------------------------------- levelling one reach
    def _upstream_limit(self, r: Reach, dn: int) -> Tuple[float, str]:
        """The HIGHEST the upstream invert of this reach may sit, and what fixed it.

        Three things bound it, and the tightest wins:
          * minimum cover at the upstream chamber for THIS reach's own diameter (H3, G203-p33)
          * soffit matching with every arriving reach (P5; Bentley expresses this as a NODE
            constraint - "match on Inverts or Crowns + Matchline Offset" - which is the
            cleaner formulation and the one used here). Soffit is invert + BORE.
          * the arriving inverts themselves: an outgoing invert above an arriving one is a
            step up in the pipe, which no chamber can be built to.

        At a station the arriving levels are irrelevant by construction - that is what the
        station is for - so only cover binds.
        """
        gu = self.grd[r.us]
        cover_lim = gu - self._min_depth(dn)
        if r.us in self.fixed_inv:
            return self.fixed_inv[r.us], "tie"
        if r.us in self.lift:
            return cover_lim, "station"
        lim, why = cover_lim, "cover"
        d_out = self.crit.internal_diameter(dn)
        for e in self.in_edges.get(r.us, ()):
            up = self.reaches[e]
            if not math.isfinite(up.inv_dn):
                continue
            soffit = up.inv_dn + self.crit.internal_diameter(up.dn) - d_out
            if soffit < lim:
                lim, why = soffit, "match"
            if up.inv_dn < lim:
                lim, why = up.inv_dn, "match"
        return lim, why

    def _level(self, r: Reach, dn: int,
               prev_k: Optional[int]) -> Tuple[float, float, int, str, float]:
        """One levelling block for a given diameter. Returns (inv_up, inv_dn, k, why, drop).

        This is Bentley steps 5-13 (Level A) and, with the final diameter, 16-22 (Level B).
        The two differ only in what they are given: Level A runs on the bracketed minimum
        size, Level B on the diameter step 14 chose. The moves, in order:

          5/6  upstream invert  -> minimum cover, then the upstream structure match
          7    downstream invert-> minimum cover at the downstream chamber
          8    downstream invert-> minimum slope (the steeper of Table 11 and tractive,
                                   G203-p27/p29, plus the G203-p29 sec 4.3.1 fall guard)
          9/13 downstream invert-> a fixed existing structure, if there is one (H14)
          10   upstream invert  -> maximum slope. Reducing the slope with the downstream end
                                   clamped means LOWERING the upstream invert, and the fall
                                   given up becomes a DROP at the upstream chamber. That is
                                   philosophy sec 5 exactly: "on steep ground the pipe does not
                                   follow the cliff - hold the gradient and take the
                                   difference at a drop chamber."
          16/17 both ends       -> RIGID translation for mid-span cover. Both ends together,
                                   never one, so the gradient survives (research A2).
        """
        o = self.opts
        L = r.length
        q = r.q_m3s
        gu, gv = self.grd[r.us], self.grd[r.ds]

        i_up, why_up = self._upstream_limit(r, dn)

        # ---- 8/12: the gradient floors, shared by both downstream cases
        s_hyd = H.smin_for(dn, q, self.crit)               # max(Table 11, tractive) - G203-p27
        s_fall = (self.crit.FALL_TOLERANCE / L) if L > 0 else 0.0
        # FALL_TOLERANCE = 2 x the 20 mm laying tolerance (G203-p29 sec 4.3.1): a reach with less
        # fall than that cannot be set out without risking a reverse gradient, and audit H11
        # fails anything under 20 mm. It is a G203-p29 floor like Table 11 and is reported
        # under the same GRAD_BY token, counted separately in the run report.

        # ---- 7/9: what the downstream end must do. Two different regimes, and conflating
        # them is a real error: a MINIMUM COVER target is a CEILING on the invert (lay at
        # least this deep), while an EXISTING INVERT is a FLOOR (you may discharge onto it or
        # above it and drop in, never below it - H14, the design yields to the structure).
        tie = r.ds in self.fixed_inv
        t_cover = gv - self._min_depth(dn)                 # lands exactly at minimum cover
        t_dn = t_cover
        if tie:
            # The tie BINDS only where the existing invert sits above the level minimum cover
            # would have given us. Below that, the existing structure is simply deep and the
            # new sewer drops into it - which is normal, and the drop is recorded on the node.
            t_dn = max(self.fixed_inv[r.ds], t_cover)

        s_ground = (i_up - t_dn) / L if L > 0 else 0.0
        s_req = max(s_ground, s_hyd, s_fall, 0.0)
        if s_req <= s_ground + 1e-12 and s_ground > 0:
            why = "tie" if (tie and t_dn > t_cover + 1e-9) else "ground"
        elif s_req <= s_fall + 1e-12 and s_fall >= s_hyd:
            why = "table11"
            self._bump("gradient_by_fall_guard")
        else:
            t11 = self.crit.TABLE11.get(dn, self.crit.TABLE11_FLOOR)
            why = "tractive" if H.smin_tractive(q, self.crit) >= t11 else "table11"
        k = self._k_up(s_req)

        if tie:
            fix = self.fixed_inv[r.ds]
            k_tie = (int(math.floor(((i_up - fix) / L) * 100.0 / K.SLOPE_STEP_PCT + 1e-9))
                     if L > 0 else k)
            if k > k_tie:
                # The flattest legal gradient still lands the pipe BELOW the existing invert,
                # which no chamber can be built to. That is not a levelling problem to round
                # away - it is a physical conflict, and every resolution is physical: a lift,
                # a different tie chamber, or a re-route (philosophy sec 3). Registered by name;
                # the reverse pass will raise the pipe onto the existing invert, and the cover
                # it costs is exactly the size of the problem.
                # `_level` runs TWICE per reach - Level A on the bracketed size, Level B on
                # the chosen one - so a plain append registers the same physical conflict
                # twice and the published `tie_conflicts` metric comes out doubled (measured:
                # 1 conflict, 2 rows). Level B is the pass that produced the published levels,
                # so its entry REPLACES Level A's and the counter fires once per reach.
                if not any(t["EDGE_UID"] == r.uid for t in self.tie_conflicts):
                    self._bump("tie_below_existing_invert")
                else:
                    self.tie_conflicts = [t for t in self.tie_conflicts
                                          if t["EDGE_UID"] != r.uid]
                self.tie_conflicts.append(dict(
                    EDGE_UID=r.uid, US_NODE=r.us, DS_NODE=r.ds, DN=dn,
                    FIX_INV_M=round(fix, 3),
                    WOULD_LAND_M=round(i_up - k * K.SLOPE_STEP_PCT / 100.0 * L, 3),
                    SHORTFALL_M=round((k - k_tie) * K.SLOPE_STEP_PCT / 100.0 * L, 3),
                    COVER_COST_M=round((k - k_tie) * K.SLOPE_STEP_PCT / 100.0 * L, 3),
                    NOTE="the flattest legal gradient discharges below the existing invert "
                         "(H14). Needs a lift, another tie chamber, or a re-route - not a "
                         "rounding change."))
                why = "tie"

        # ---- P1: carry the upstream gradient where it is free, or within one 0.05 % step
        if prev_k is not None and prev_k >= k:
            premium_steps = prev_k - k
            if premium_steps == 0:
                pass                                   # already uniform; the cause stands
            elif premium_steps <= o.uniform_premium_steps:
                cov_dn_after = _cap_cover(
                    dn, gv - (i_up - prev_k * K.SLOPE_STEP_PCT / 100.0 * L))
                if cov_dn_after <= o.max_cover_m:
                    # No counter here on purpose. A carry made at this point can still be
                    # overridden by the maximum-slope move below, and a counter incremented
                    # before the decision is final is how a metric ends up disagreeing with
                    # the layer it claims to describe (P2). The published GRAD_BY tally
                    # is the count, and it is taken from the rows themselves.
                    k, why = prev_k, "uniform"
                else:
                    # "P1 is never bought at the price of a pumping station" - the carry is
                    # refused because it would deepen the reach past the 12 m cap.
                    why = "cover_max"
                    self._bump("uniform_refused_by_cap")

        # ---- 10: maximum slope. TWO ceilings now, and the tighter of them wins.
        #
        #   H7      v <= 3.0 m/s (G203-p27), enforced and not demoted, as before
        #   CLIFF   the laid-gradient ceiling. Philosophy sec 5: "on steep ground the pipe does
        #           not follow the cliff. Hold the gradient and take the difference at a drop
        #           chamber." H7 does NOT do this job and cannot: on the pipe where it matters -
        #           a DN200 lateral at a fraction of a litre per second - d/D stays under 0.03
        #           and the velocity on a 49 % slope is 0.8 m/s, so H7 never binds and the
        #           solver lays the pipe straight down the cliff. Measured 2026-09-02: 20 reaches
        #           between 25.0 and 49.3 %, every one of them a near-zero-flow DN200 lateral.
        #
        # Both ceilings take the SAME action, which is why they share a branch: hold the
        # downstream end at its cover target, lower the upstream end, and let the fall we are no
        # longer allowed to use become a drop at the upstream chamber (G203-p30 sizes the
        # structure; the node layer publishes it as DROP_M/DROP_TYPE). Which ceiling bound is
        # recorded in the run report, because `contract.GRAD_BY` has one token for "flattened by
        # a maximum-gradient rule" - `vmax` - and widening that enum is the contract's decision,
        # not this stage's. See the run report counters `vmax_capped` and `cliff_capped`.
        k_max = self._k_vmax(dn, q, k)
        k_cliff = self.opts.max_slope_k
        capped_by_cliff = False
        if k_cliff < k and (k_max is None or k_cliff < k_max):
            k_max, capped_by_cliff = k_cliff, True
        drop_up = 0.0
        if k_max is not None and k_max < k:
            k_floor = max(self._k_up(s_hyd), self._k_up(s_fall), 1)
            if k_max < k_floor:
                # No gradient satisfies both the minimum and v <= 3.0 m/s at this diameter.
                # The answer is a bigger pipe, never a faster one - signalled to the caller.
                return (float("nan"), float("nan"), -1, "vmax", 0.0)
            k = k_max
            why = "vmax"
            # the fall we are no longer allowed to use is taken at the upstream chamber
            new_i_up = t_dn + k * K.SLOPE_STEP_PCT / 100.0 * L
            drop_up = max(0.0, i_up - new_i_up)
            i_up = min(i_up, new_i_up)
            self._bump("cliff_capped" if capped_by_cliff else "vmax_capped")

        s = k * K.SLOPE_STEP_PCT / 100.0
        i_dn = i_up - s * L

        # ---- 16/17: mid-span cover, as a RIGID translation of both ends
        deficit = 0.0
        for chn, z in r.profile:
            if not math.isfinite(z):
                continue
            need = z - self._min_depth(dn)
            here = i_up - s * chn
            if here > need:
                deficit = max(deficit, here - need)
        if deficit > 1e-9:
            i_up -= deficit
            i_dn -= deficit
            drop_up += deficit
            why = "cover_min"
            self._bump("midspan_cover_translations")

        return i_up, i_dn, k, why, drop_up

    def _k_vmax(self, dn: int, q_m3s: float, k_hi: int) -> Optional[int]:
        """Largest grid gradient at or below `k_hi` that keeps velocity within H7's 3.0 m/s.

        None where the cap never binds. Bisection on the grid index rather than
        `hydra.smax_for`, which runs 120 bisections of its own - the answer is the same
        (velocity rises monotonically with slope on the feasible branch) and this costs about
        nine evaluations instead of ten thousand. `smax_for` is still the reference and is
        used in the final exact check.
        """
        y, v = self._state(dn, k_hi, q_m3s)
        if y is not None and v is not None and v <= self.crit.V_MAX:
            return None
        lo, hi = 1, k_hi
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            y, v = self._state(dn, mid, q_m3s)
            if y is None:
                lo = mid + 1                 # cannot carry the flow: needs MORE slope
            elif v is not None and v <= self.crit.V_MAX:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return best

    # ---------------------------------------------------------------- sizing
    def _size_reach(self, r: Reach, k_levels: int, dn_floor: int,
                    floor_why: str) -> Tuple[int, str]:
        """Bentley step 14 - "adjust conduit size for capacity to match discharge".

        Each candidate is judged at ITS OWN governing gradient, never at a flatter one:
        G203-p29 and Ten States sec 33.43 both prohibit oversizing a pipe to lay it flatter, so
        the gradient a bigger pipe is tested at is the steeper of what the LEVELS demand and
        what that diameter's own Table-11/tractive minimum demands.

        The cause is recorded, and the enum is `contract.SIZED_BY`, pinned to audit H8's own
        allowed set: 'depth' and 'cover' are prohibited answers for a diameter (H8, G203-p29).
        """
        q = r.q_m3s
        cause = "minimum" if floor_why == "tier" else "minimum"
        prev_fail = None
        for dn in self._candidates(r.tier):
            if dn < dn_floor:
                continue
            k_hyd = max(self._k_up(H.smin_for(dn, q, self.crit)), 1)
            k = max(k_levels, k_hyd,
                    self._k_up(self.crit.FALL_TOLERANCE / r.length) if r.length > 0 else 1)

            # Capacity FIRST, because it is two direct `q_partial` calls memoised on
            # (dn, gradient) and therefore nearly free after the first few reaches, while the
            # velocity test needs a bisection. Ordering the cheap discriminator first is what
            # keeps a full-area run in minutes rather than hours; it changes no answer,
            # because a candidate that fails capacity fails whatever the velocity does.
            q_lim, q_peak_cap = self._q_caps(dn, k)
            if q > q_peak_cap:
                prev_fail = "capacity"           # surcharged - W10 shipped 2.80 km of this
                continue
            if q > q_lim:
                prev_fail = "dod"                # passes, but over the Table 10 limit
                continue

            k_max = self._k_vmax(dn, q, k)
            if k_max is not None:
                if k_max < k_hyd:
                    prev_fail = "velocity"       # no legal gradient is slow enough
                    continue
                k = min(k, k_max)
                # a flatter pipe carries less: the capacity test has to be re-put at the
                # gradient the velocity cap actually allows, not the one we hoped for
                q_lim, q_peak_cap = self._q_caps(dn, k)
                if q > q_peak_cap:
                    prev_fail = "capacity"
                    continue
                if q > q_lim:
                    prev_fail = "dod"
                    continue

            y, v = self._state(dn, k, q)
            if y is None:
                prev_fail = "capacity"
                continue
            if v is not None and v > self.crit.V_MAX + 1e-9:
                prev_fail = "velocity"
                continue
            return dn, (prev_fail or cause)
        # Nothing in the catalogue works. Bentley takes "the largest available size" and
        # reports it; so do we, and the auditor will fail it loudly rather than us hiding it.
        self._bump("no_catalogue_size")
        return self.crit.DN_SERIES[-1], (prev_fail or "capacity")

    # ---------------------------------------------------------------- the forward pass
    def forward(self) -> None:
        """Every reach, upstream to downstream: bracket, Level A, size, Level B.

        Node topological order, and each node's OUTGOING reach is levelled after every reach
        arriving at it - so the soffit match at a chamber is made against arrivals that are
        already settled, and the reverse pass has nothing to undo there.
        """
        for r in self.reaches.values():
            r.drop_up = 0.0
        # Counters and the tie register describe the pass that is PUBLISHED, not the sum of
        # every attempt. W10's optimisation study quoted a baseline of 219 breaches against a
        # shipped design with 239 because a number outlived the run that produced it.
        self.counters.clear()
        self.tie_conflicts.clear()
        prev_k: Dict[str, int] = {}

        for u in self.topo:
            e = self.out_edge.get(u)
            if e is None:
                continue                                  # a terminal: nothing leaves it
            r = self.reaches[e]

            dn_floor, floor_why = self._dn_floor(r)

            # ---- 3/4 BRACKET. Not the diameter - the range. Level A runs on the bottom of
            # it, exactly as Bentley's steps 3-4 precede steps 5-13.
            dn_bracket = dn_floor

            # ---- LEVEL A (5-13) on the bracketed size
            i_up, i_dn, k, why, drop = self._level(r, dn_bracket, prev_k.get(u))
            if k < 0:
                k = max(self._k_up(H.smin_for(dn_bracket, r.q_m3s, self.crit)), 1)

            # ---- 14 SIZE for capacity at the gradient the levels produced
            dn, sized_by = self._size_reach(r, k, dn_floor, floor_why)
            if dn == dn_floor and sized_by not in ("capacity", "dod", "velocity"):
                sized_by = "minimum"

            # ---- 15-22 LEVEL B on the chosen diameter. Re-seat, do not re-solve.
            i_up, i_dn, k, why, drop = self._level(r, dn, prev_k.get(u))
            if k < 0:
                # v <= 3.0 m/s unreachable at this diameter even after re-levelling: go up
                # one catalogue step and re-level. This is the one place Level B may change
                # the diameter, and it is recorded as 'velocity'.
                bigger = [d for d in self._candidates(r.tier) if d > dn]
                if bigger:
                    dn, sized_by = bigger[0], "velocity"
                    i_up, i_dn, k, why, drop = self._level(r, dn, prev_k.get(u))
                if k < 0:
                    k = max(self._k_up(H.smin_for(dn, r.q_m3s, self.crit)), 1)
                    s = k * K.SLOPE_STEP_PCT / 100.0
                    i_up, _w = self._upstream_limit(r, dn)
                    i_dn, drop, why = i_up - s * r.length, 0.0, "vmax"
                    self._bump("vmax_unsatisfiable")

            # ---- CAPACITY, RE-PUT AT THE GRADIENT THE REACH IS ACTUALLY LAID AT.
            # Step 14 judges each candidate at LEVEL A's gradient, because that is the only
            # gradient that exists when the diameter is chosen. Level B then re-levels on the
            # chosen diameter and can land FLATTER - a bigger pipe sits deeper, which shortens
            # the fall available to it, and the vmax and cliff ceilings only ever reduce k. A
            # capacity test made at a gradient the pipe was not laid at is exactly the W10
            # defect this module's own header claims to prevent, and it shipped 4 reaches over
            # their d/D limit (measured 2026-09-02: DN600 at 0.15 %, y = 0.527 against a 0.50
            # limit; the next size passes at 0.416 on the same gradient).
            #
            # The answer is a bigger pipe, never a flatter one and never a relaxed limit -
            # G203-p29 forbids oversizing to lay flatter, and this is its converse: the
            # gradient is already fixed, and the pipe follows the flow. Bounded by the
            # catalogue; where the catalogue runs out the cause is recorded and the auditor
            # fails it loudly, which is the same policy `_size_reach` already takes.
            for _ in range(len(self.crit.DN_SERIES)):
                q_lim, q_peak = self._q_caps(dn, k)
                if r.q_m3s <= q_lim + 1e-12:
                    break
                cause = "capacity" if r.q_m3s > q_peak else "dod"
                bigger = [d for d in self._candidates(r.tier) if d > dn]
                if not bigger:
                    sized_by = cause
                    self._bump("no_catalogue_size_at_laid_gradient")
                    break
                dn, sized_by = bigger[0], cause
                self._bump("upsized_at_laid_gradient")
                i_up, i_dn, k, why, drop = self._level(r, dn, prev_k.get(u))
                if k < 0:
                    k = max(self._k_up(H.smin_for(dn, r.q_m3s, self.crit)), 1)
                    s = k * K.SLOPE_STEP_PCT / 100.0
                    i_up, _w = self._upstream_limit(r, dn)
                    i_dn, drop, why = i_up - s * r.length, 0.0, "vmax"
                    self._bump("vmax_unsatisfiable")

            r.dn = dn
            r.sized_by = sized_by
            r.gradient_by = why
            r.k_slope = k
            r.inv_up = i_up
            r.inv_dn = i_dn
            r.drop_up = drop
            r.tie_type = "soffit" if (r.ds in self.fixed_inv or r.us in self.fixed_inv) \
                else "none"
            prev_k[r.ds] = k

    # ---------------------------------------------------------------- the reverse pass
    def reverse(self) -> Dict[str, int]:
        """Downstream to upstream. FOUR operations, not a re-solve (research sec 3.2).

        Bentley's own list, in order, and the first one is the important one: "adjust
        downstream STRUCTURE elevation to match conduit downstream invert" - the manhole
        yields to the pipe, once the pipe is settled. That is the correct direction of
        authority, and it is why the node layer and the reach layer here cannot disagree the
        way W10's did by up to 10.39 m.

        There is no sizing step, no cover step and no minimum-slope step in this pass, by
        design. If it had those it would be a second solve, and a second solve would undo the
        first one's gradient decisions - the thing rigid translation exists to protect.
        """
        n = {"seated": 0, "ds_fixed": 0, "maxslope": 0, "us_fixed": 0}
        self.node_inv = {}

        for u in reversed(self.topo):
            e = self.out_edge.get(u)
            if e is None:
                continue
            r = self.reaches[e]

            # ---- 2. downstream invert to a fixed structure (H14).
            # A fixed invert is a FLOOR, not a target. Landing above it is legal and normal -
            # the new sewer drops into the existing chamber, and that drop is recorded on the
            # node. Landing BELOW it is impossible, so that is the only case this corrects,
            # and it corrects it by translating the pipe RIGIDLY so the gradient survives
            # (Bentley steps 16-17; a rotation here would put the laid value off the 0.05 %
            # grid the drawing depends on).
            if r.ds in self.fixed_inv:
                want = self.fixed_inv[r.ds]
                if r.inv_dn < want - 1e-9:
                    shift = want - r.inv_dn
                    r.inv_up += shift
                    r.inv_dn = want
                    r.gradient_by = "tie"
                    n["ds_fixed"] += 1

            # ---- 3. upstream invert to maximum slope. BOTH ceilings, as in the forward pass:
            # operations 2 and 4 move an invert, so a reach that was inside the cliff ceiling
            # on the way down can be outside it on the way back up, and a reverse pass that
            # only checked H7 would let exactly that through to the layer.
            if r.length > 0:
                s_now = (r.inv_up - r.inv_dn) / r.length
                k_now = int(round(s_now * 100.0 / K.SLOPE_STEP_PCT))
                k_max = self._k_vmax(r.dn, r.q_m3s, max(k_now, 1))
                k_cliff = self.opts.max_slope_k
                k_max = k_cliff if k_max is None else min(k_max, k_cliff)
                if k_max is not None and k_max < k_now:
                    new_up = r.inv_dn + k_max * K.SLOPE_STEP_PCT / 100.0 * r.length
                    r.drop_up += max(0.0, r.inv_up - new_up)
                    r.inv_up = new_up
                    r.k_slope = k_max
                    r.gradient_by = "vmax"
                    n["maxslope"] += 1
                else:
                    r.k_slope = max(k_now, 1)

            # ---- 4. upstream invert to a fixed structure
            if r.us in self.fixed_inv:
                want = self.fixed_inv[r.us]
                if abs(want - r.inv_up) > 1e-9:
                    r.inv_up = want
                    r.inv_dn = want - r.slope_frac * r.length
                    n["us_fixed"] += 1

        # ---- 1. THE STRUCTURES TAKE THE INVERTS OF THE PIPES. Bentley lists this first for
        # each conduit; it is run here as one sweep at the end for a reason that is arithmetic
        # rather than doctrinal - operations 2 and 4 above can still move an invert, so a
        # structure seated before them would be seated onto a level that no longer exists.
        # The DIRECTION of authority is what matters and it is unchanged: the manhole yields
        # to the pipe, never the other way round.
        for u in self.topo:
            e = self.out_edge.get(u)
            if e is not None:
                self.node_inv[u] = self.reaches[e].inv_up
            else:
                arr = [self.reaches[x].inv_dn for x in self.in_edges.get(u, ())
                       if math.isfinite(self.reaches[x].inv_dn)]
                self.node_inv[u] = (min(arr) if arr else
                                    self.grd[u] - self._min_depth(self.crit.DN_MIN_MAIN))
            n["seated"] += 1
        return n

    # ---------------------------------------------------------------- the ladder
    def _cover_us(self, r: Reach) -> float:
        return _cap_cover(r.dn, self.grd[r.us] - r.inv_up)

    def _cover_dn(self, r: Reach) -> float:
        return _cap_cover(r.dn, self.grd[r.ds] - r.inv_dn)

    def _cover_mid(self, r: Reach) -> float:
        """Worst cover along the reach, from the terrain profile.

        audit.h4 looks only at the two ends. A reach that dives under a rise between its
        chambers is past the cap whether or not the auditor can see it, so the LADDER uses
        this and the flag it sets is therefore a superset of what the auditor tests."""
        worst = max(self._cover_us(r), self._cover_dn(r))
        s = r.slope_frac
        for chn, z in r.profile:
            if not math.isfinite(z):
                continue
            worst = max(worst, _cap_cover(r.dn, z - (r.inv_up - s * chn)))
        return worst

    def apply_ladder(self) -> List[Dict]:
        """Rung 1 of philosophy sec 5: cover reaches 12 m -> station, unless an exit applies.

        A breach is a run of consecutive reaches along one flow path whose cover exceeds the
        cap. For each breach, both exits are tested and either alone is sufficient:

            recovers_500m   cover is back within the cap within 500 m of where it was lost
            outfall_1000m   the run reaches a terminal - works, tie or an existing station -
                            within 1,000 m of where the cap was lost

        Where one applies, every reach in the breach carries PAST_CAP=1, that exit, and the
        DISTANCE that proves it. Where neither applies, the fourth physical resolution is
        taken: a station at the last chamber inside the cap. The economics do not appear
        anywhere in this function, and that is deliberate - rung 3 can only make you pump
        EARLIER, never later, so it cannot rescue a breach and has no business here.
        """
        o = self.opts
        breaches: List[Dict] = []
        cov = {uid: self._cover_mid(r) for uid, r in self.reaches.items()}
        over = {uid for uid, c in cov.items() if c > o.max_cover_m + 1e-6}
        if not over:
            return breaches

        # heads of breaches: an over-cap reach whose upstream reach is not over-cap
        heads = []
        for uid in over:
            r = self.reaches[uid]
            ups = [e for e in self.in_edges.get(r.us, ()) if e in over]
            if not ups:
                heads.append(uid)

        for head in heads:
            # Walk the flow path from where the cap was lost and test BOTH exits. The walk
            # does not stop at the recovery: a breach whose cover comes back at 600 m has
            # failed the 500 m exit but may still reach the outfall inside 1,000 m, and the
            # philosophy says either exit alone is sufficient. Stopping at the first one
            # tested would silently deny the second.
            chain: List[str] = []
            uid, dist = head, 0.0
            recover_at = None
            outfall_at = None
            in_breach = True
            while uid is not None:
                r = self.reaches[uid]
                if in_breach:
                    if uid in over:
                        chain.append(uid)
                    else:
                        recover_at = dist
                        in_breach = False
                elif dist > o.cap_outfall_m + 1e-6:
                    break          # out of the breach and past both exits: nothing left to test
                dist += r.length
                nxt = self.out_edge.get(r.ds)
                if nxt is None:
                    if self.kind.get(r.ds) in ("outfall", "tie", "station"):
                        outfall_at = dist
                    break
                uid = nxt
            seg_len = sum(self.reaches[x].length for x in chain)

            exit_name, exit_len = "", 0.0
            if recover_at is not None and recover_at <= o.cap_recover_m + 1e-6:
                exit_name, exit_len = "recovers_500m", recover_at
            elif outfall_at is not None and outfall_at <= o.cap_outfall_m + 1e-6:
                exit_name, exit_len = "outfall_1000m", outfall_at

            rec = dict(head=head, chain=tuple(chain), seg_len_m=round(seg_len, 1),
                       recover_m=(None if recover_at is None else round(recover_at, 1)),
                       outfall_m=(None if outfall_at is None else round(outfall_at, 1)),
                       exit=exit_name, exit_len_m=round(exit_len, 1),
                       worst_cover_m=round(max(cov[x] for x in chain), 2))
            breaches.append(rec)

            if exit_name:
                for x in chain:
                    rr = self.reaches[x]
                    rr.past_cap = 1
                    rr.cap_exit = exit_name
                    rr.cap_len_m = round(exit_len, 2)
            else:
                # No exit. A station goes at the LAST chamber still inside the cap, which is
                # the upstream node of the head reach.
                self._mint_station(rec, why="cap")
        return breaches

    def _mint_station(self, rec: Dict, why: str = "cap") -> bool:
        """Rung 1's physical resolution: a station at the head of a breach.

        Split out of `apply_ladder` so the drop ceiling below resolves a breach the SAME way
        rather than with a second, subtly different copy - the one-function rule the
        philosophy's provenance checks exist for. Returns False when the chamber is already a
        station, which is not a no-op to swallow: it means the breach survived being pumped
        and the caller has to register it rather than mint a duplicate.
        """
        head = rec["head"]
        u = self.reaches[head].us
        if u in self.lift:
            return False
        arr = [self.reaches[e].inv_dn for e in self.in_edges.get(u, ())
               if math.isfinite(self.reaches[e].inv_dn)]
        arrive = min(arr) if arr else self.reaches[head].inv_up
        lift = max(0.0, (self.grd[u] - self._min_depth(self.reaches[head].dn)) - arrive)
        self.lift[u] = lift
        self.station_note[u] = dict(
            NODE_UID=u, X=float(self.nodes.at[u, "X"]),
            Y=float(self.nodes.at[u, "Y"]), GRD_M=round(self.grd[u], 3),
            ARRIVE_INV_M=round(arrive, 3),
            ARRIVE_DEPTH_M=round(self.grd[u] - arrive, 2),
            LIFT_M=round(lift, 2),
            Q_PK_LS=round(self.reaches[head].q_pk_ls, 2),
            WHY=why,
            BREACH_LEN_M=rec["seg_len_m"],
            WORST_COVER_M=rec["worst_cover_m"],
            RECOVERS_IN_M=rec["recover_m"],
            OUTFALL_IN_M=rec["outfall_m"],
            WAITS_ON=("a manufacturer's rating for this cover, and NWS's station "
                      "establishment cost (philosophy sec 5)"))
        return True

    # ---------------------------------------------------------------- drops at a chamber
    def node_drops(self) -> Dict[str, Tuple[float, str]]:
        """The fall INTO each chamber, and the arriving reach that sets it.

        G203-p30 defines a drop as "the difference in invert elevations" where a branch
        adjoins the sewer it discharges to, so the structure at a chamber is sized on the
        TALLEST arriving difference. That is what this returns, and it is the ONLY place the
        number is computed - `write_back` publishes it, the ceiling below tests it and the
        register prints it, so the layer and the register cannot disagree.

        The arriving invert is taken as `inv_up - SLOPE_LAID/100 x LEN_M`, which is the
        expression `write_back` publishes as INV_DN, not the solver's own `inv_dn`. The two
        agree to float noise today; using the published one means they agree by construction
        even if a later pass stops being exact.

        A chamber's own invert is its OUTGOING reach's upstream invert. At a terminal there is
        no outgoing reach and the reverse pass seats the chamber on the LOWEST arrival, so the
        drop there is the spread between arrivals - which is a real benching problem and is
        reported as one, not hidden behind a zero.
        """
        out: Dict[str, Tuple[float, str]] = {}
        for u, iv in self.node_inv.items():
            d, who = 0.0, ""
            for x in self.in_edges.get(u, ()):
                r = self.reaches[x]
                dd = (r.inv_up - r.slope_frac * r.length) - iv
                if dd > d:
                    d, who = dd, x
            out[u] = (max(0.0, d), who)
        return out

    def _withdraw_exits_forcing_unbuildable_drop(
            self, breaches: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Philosophy sec 5: "Never a drop used to dodge a station."

        A sec 5 exit is granted on DISTANCE alone - the cover recovers within 500 m, or the
        run reaches the outfall within 1,000 m - and nothing in it bounds how deep the
        excursion goes on the way. Applied to a ridge rather than the hump it was written for,
        it authorises a trench whose every shallow branch must then fall tens of metres into
        it. That fall is a drop, and it is buying the run its way past the 12 m cap: exactly
        what the sentence above forbids. So the exit is not available to that breach, and the
        breach takes the fourth physical resolution at the foot of the climb.

        Returns (withdrawn, unresolved). An `unresolved` row is a chamber whose drop is past
        the ceiling and that this stage cannot resolve - the head is already a station, or no
        breach owns the deep arrival at all. Those are registered and the stage refuses to
        publish; a re-route or a change of served set is philosophy sec 3's answer and is not
        stage 6's to take.
        """
        if not self.opts.drop_ceiling_mints_station:
            return [], []
        ceil = self.opts.max_drop_m
        drops = self.node_drops()
        bad = sorted(((d, u, who) for u, (d, who) in drops.items() if d > ceil + 1e-9),
                     reverse=True)
        if not bad:
            return [], []

        owner: Dict[str, Dict] = {}
        for b in breaches:
            for x in b["chain"]:
                owner[x] = b

        withdrawn: List[Dict] = []
        unresolved: List[Dict] = []
        done: set = set()
        for d, u, who in bad:
            # WHICH SIDE OF THE JUNCTION TO LOOK AT, because getting this wrong makes the
            # whole rung silently useless. `who` is the arrival that SETS the drop, and that
            # is the SHALLOW one - a 1.7 m deep street lateral falling into a 36.8 m deep
            # main. The shallow branch is not in any breach and never will be; the run that
            # is over the cap is the one the chamber sits ON. So the breach is looked for on
            # the DEEP side: the reach leaving the chamber first, then the deepest arrival,
            # then upstream along the deepest arrivals, bounded so a pathological graph
            # cannot spin.
            b = None
            probe = []
            e_out = self.out_edge.get(u)
            if e_out is not None:
                probe.append(e_out)
            deep = [e for e in self.in_edges.get(u, ())
                    if math.isfinite(self.reaches[e].inv_dn)]
            if deep:
                probe.append(min(deep, key=lambda e: self.reaches[e].inv_dn))
            for x in probe:
                b = owner.get(x)
                if b is not None:
                    break
            x = probe[-1] if probe else who
            for _ in range(400):
                if b is not None:
                    break
                ups = [e for e in self.in_edges.get(self.reaches[x].us, ())
                       if math.isfinite(self.reaches[e].inv_dn)]
                if not ups:
                    break
                x = min(ups, key=lambda e: self.reaches[e].inv_dn)
                b = owner.get(x)
            row = dict(NODE_UID=u, DROP_M=round(d, 3), CEILING_M=ceil,
                       ARRIVING_EDGE=who, GRD_M=round(self.grd[u], 3),
                       NODE_INV_M=round(self.node_inv.get(u, float("nan")), 3),
                       NODE_KIND=self.kind.get(u, ""),
                       BREACH_HEAD=("" if b is None else b["head"]),
                       BREACH_EXIT=("" if b is None else (b["exit"] or "")))
            if b is None:
                row["WHY_UNRESOLVED"] = (
                    "no over-cap run owns the arriving reach, so there is no head to put a "
                    "station at. The chamber is deep for a reason this stage did not level - "
                    "look upstream of stage 6 (philosophy sec 3: re-route, or do not serve)")
                unresolved.append(row)
                continue
            if id(b) in done:
                continue                       # this breach is already being resolved
            if not b["exit"]:
                row["WHY_UNRESOLVED"] = (
                    "the run already has no exit and a station at its head did not bring the "
                    "drop under the ceiling. The resolutions left are physical and none is "
                    "stage 6's: a re-route, a different outlet, or not serving that branch")
                unresolved.append(row)
                continue
            was = b["exit"]
            if not self._mint_station(b, why="drop_ceiling"):
                row["WHY_UNRESOLVED"] = (
                    f"the head of this run ({self.reaches[b['head']].us}) is ALREADY a "
                    "station and the drop is still past the ceiling - pumping at the foot of "
                    "the climb did not resolve it")
                unresolved.append(row)
                continue
            done.add(id(b))
            for e in b["chain"]:
                rr = self.reaches[e]
                rr.past_cap, rr.cap_exit, rr.cap_len_m = 0, "", 0.0
            b["exit"], b["exit_len_m"] = "", 0.0
            b["exit_withdrawn"] = (
                f"{was}: withdrawn because chamber {u} on this run would need a "
                f"{d:.2f} m drop, past the {ceil:.1f} m project ceiling. Philosophy sec 5: "
                "never a drop used to dodge a station")
            withdrawn.append(dict(row, WITHDRAWN_EXIT=was,
                                  STATION_AT=self.reaches[b["head"]].us))
            self._bump("exit_withdrawn_by_drop_ceiling")
        return withdrawn, unresolved

    # ---------------------------------------------------------------- run
    def solve(self) -> Dict:
        """forward -> reverse -> ladder, repeated only while the ladder adds a station.

        The reverse pass sits INSIDE the loop deliberately. It can move an invert (a fixed
        structure, or a maximum-slope correction on the way back up), so a ladder run before
        it would be flagging levels that no longer exist - and PAST_CAP is a published claim
        about the FINAL levels, not about an intermediate state. Getting this order wrong is
        the same class of mistake as W10 recording depth after the reset instead of before.

        The loop ends when a whole pass adds no station, which is the only stable state: a
        station changes every level below it, which can expose the next breach.
        """
        rep: Dict = {"passes": 0, "breaches": [], "stations": 0,
                     "drop_withdrawn": [], "drop_unresolved": []}
        for p in range(1, self.opts.max_cap_passes + 1):
            rep["passes"] = p
            for r in self.reaches.values():
                r.past_cap, r.cap_exit, r.cap_len_m = 0, "", 0.0
            self.forward()
            rep["reverse"] = self.reverse()
            before = len(self.lift)
            rep["breaches"] = self.apply_ladder()
            # The drop ceiling is tested AFTER the ladder and INSIDE the loop, for the same
            # reason the ladder is inside it: withdrawing an exit mints a station, a station
            # changes every level below it, and a drop measured before that is a drop that no
            # longer exists. `drop_withdrawn` accumulates across passes because `counters` is
            # cleared by `forward()` and the final pass, by definition, withdraws nothing.
            wd, un = self._withdraw_exits_forcing_unbuildable_drop(rep["breaches"])
            rep["drop_withdrawn"].extend(wd)
            rep["drop_unresolved"] = un
            if len(self.lift) == before:
                break
        else:
            rep["cap_loop_exhausted"] = True

        # The drop the LAYER will carry, measured on the levels that will be published.
        drops = self.node_drops()
        rep["drops"] = drops
        rep["n_backdrop"] = sum(1 for d, _ in drops.values()
                                if self.crit.DROP_TRIGGER + 1e-9 < d
                                <= self.crit.BACKDROP_MAX + 1e-9)
        rep["n_vortex"] = sum(1 for d, _ in drops.values()
                              if d > self.crit.BACKDROP_MAX + 1e-9)
        rep["drop_over_ceiling"] = sorted(
            (dict(NODE_UID=u, DROP_M=round(d, 3), ARRIVING_EDGE=who,
                  GRD_M=round(self.grd[u], 3), NODE_KIND=self.kind.get(u, ""),
                  DEPTH_M=round(self.grd[u] - self.node_inv[u], 2))
             for u, (d, who) in drops.items() if d > self.opts.max_drop_m + 1e-9),
            key=lambda r: -r["DROP_M"])

        # A breach that no exit justifies and no station has yet resolved is the exact W10
        # failure - a chamber past the cap carrying no flag. It cannot be published: the
        # contract refuses PAST_CAP=1 without an exit, and publishing PAST_CAP=0 on a reach
        # under 15 m of cover would be a lie. So it is counted here and the caller refuses.
        rep["unexited"] = [b for b in rep["breaches"] if not b["exit"]]
        rep["km_unexited"] = round(sum(b["seg_len_m"] for b in rep["unexited"]) / 1000.0, 3)
        rep["stations"] = rep["stations_final"] = len(self.lift)
        rep["counters"] = dict(self.counters)
        return rep


# ======================================================================================
# Reading the upstream layers, and saying plainly what is missing
# ======================================================================================

# Fields this stage OWNS - it computes them, so they need not arrive from stage 5.
OWNED_REACH = {"DN", "MATERIAL", "SLOPE_LAID", "SLOPE_MIN", "GRAD_BY", "SIZED_BY",
               "CLEAN_BY", "TAU_PA", "INV_UP", "INV_DN", "US_DEPTH", "DS_DEPTH",
               "COVER_US", "COVER_DN", "V_PK_MS", "DOD_PK", "RET_MIN", "PAST_CAP",
               "CAP_EXIT", "CAP_LEN_M", "TIE_TYPE"}
OWNED_NODE = {"INV_M", "DEPTH_M", "COVER_M", "DROP_M", "DROP_TYPE", "VORTEX",
              "PAST_CAP", "CAP_EXIT"}

# Fields this stage READS and cannot compute. A missing one is not a defect to work around:
# it means the stage that owns it has not run, and the honest answer is to wait.
NEEDED_REACH = ("EDGE_UID", "US_NODE", "DS_NODE", "TIER", "LEN_M", "QPK_LS")
NEEDED_NODE = ("NODE_UID", "X", "Y", "GRD_M", "NODE_KIND")


def _missing(gdf, spec: K.LayerSpec, owned: set, extra: Sequence[str]) -> List[str]:
    have = set(gdf.columns)
    out = [f for f in extra if f not in have]
    out += [f for f in spec.required_names if f not in have and f not in owned
            and f not in out]
    return out


def load_inputs(gpkg: str):
    """Read the published `nodes` and `reaches`. Returns (nodes, reaches, waiting_for)."""
    waiting: List[str] = []
    if not os.path.exists(gpkg):
        return None, None, [f"{gpkg} does not exist - stages 1-5 have not published yet"]
    # "Has stage 5 published yet?" is the first question this stage asks, so it is not hung on
    # a private geopandas attribute. pyogrio is the reader geopandas uses by default here;
    # fiona is the fallback. If neither can list, the layer reads below still answer the
    # question - just with a less helpful message.
    layers = None
    for probe in (lambda: {str(x[0]) for x in __import__("pyogrio").list_layers(gpkg)},
                  lambda: set(__import__("fiona").listlayers(gpkg))):
        try:
            layers = probe()
            break
        except Exception:
            continue

    def _read(name):
        try:
            return gpd.read_file(gpkg, layer=name)
        except Exception as exc:
            waiting.append(f"layer '{name}' in {os.path.basename(gpkg)} ({exc})")
            return None

    if layers is not None:
        for name in ("nodes", "reaches"):
            if name not in layers:
                waiting.append(f"layer '{name}' in {os.path.basename(gpkg)} "
                               f"(present: {sorted(layers) or 'none'})")
        if waiting:
            return None, None, waiting
    nodes = _read("nodes")
    reaches = _read("reaches")
    if nodes is None or reaches is None:
        return None, None, waiting
    return nodes, reaches, waiting


def build_reaches(reaches_gdf, opts: SolverOptions,
                  sampler: Optional[TileSampler],
                  node_grd: Dict[str, float]) -> Tuple[List[Reach], Dict[str, int]]:
    """Turn the published reach layer into solver records, and sample every profile once.

    The profile is sampled in ONE batched terrain call for the whole network rather than per
    reach: on a 0.5 m VRT covering 531 km2 a per-point read is the difference between seconds
    and an afternoon. Where the terrain has no data the profile point falls back to a linear
    interpolation between the two chamber ground levels - which are measurements stage 5 made,
    not a guess - and every fallback is counted.
    """
    stats = {"profile_points": 0, "profile_nodata": 0, "no_terrain": 0}
    out: List[Reach] = []
    geoms = list(reaches_gdf.geometry)
    xs: List[float] = []
    ys: List[float] = []
    spans: List[Tuple[int, int, List[float]]] = []

    for i, (_, row) in enumerate(reaches_gdf.iterrows()):
        g = geoms[i]
        L = float(row["LEN_M"])
        n = max(2, int(math.ceil(L / opts.profile_step_m)) + 1)
        chn = [min(L, j * opts.profile_step_m) if j < n - 1 else L for j in range(n)]
        a = len(xs)
        if sampler is not None and g is not None and not g.is_empty:
            for d in chn:
                p = g.interpolate(d)
                xs.append(p.x)
                ys.append(p.y)
        spans.append((a, len(xs), chn))

    zs = (sampler.z_many(np.array(xs), np.array(ys)) if (sampler is not None and xs)
          else np.zeros(0))

    for i, (_, row) in enumerate(reaches_gdf.iterrows()):
        a, b, chn = spans[i]
        us, ds = str(row["US_NODE"]), str(row["DS_NODE"])
        L = float(row["LEN_M"])
        gu, gv = node_grd.get(us, float("nan")), node_grd.get(ds, float("nan"))
        if b > a:
            z = list(zs[a:b])
            stats["profile_points"] += (b - a)
        else:
            z = [float("nan")] * len(chn)
            stats["no_terrain"] += 1
        prof = []
        for d, zz in zip(chn, z):
            if not math.isfinite(zz):
                stats["profile_nodata"] += 1
                zz = gu + (gv - gu) * (d / L if L > 0 else 0.0)
            prof.append((float(d), float(zz)))
        out.append(Reach(uid=str(row["EDGE_UID"]), us=us, ds=ds, length=L,
                         q_pk_ls=float(row["QPK_LS"]), tier=str(row["TIER"]),
                         profile=tuple(prof)))
    return out, stats


# ======================================================================================
# Writing the answer back onto the layers
# ======================================================================================

def write_back(nodes_gdf, reaches_gdf, solver: LevelSolver) -> Tuple:
    """Put the solved levels onto the two published layers.

    Every hydraulic number published here is recomputed at the EXACT flow and the EXACT laid
    gradient - never at the quantised value the search used - because the auditor recomputes
    H2, H5, H6 and H7 from DN, SLOPE_LAID and QPK_LS on the row, and a row that cannot
    reproduce its own state is a row nobody can check.
    """
    C_ = solver.crit
    R = solver.reaches
    idx = {str(u): i for i, u in enumerate(reaches_gdf["EDGE_UID"].astype(str))}
    n = len(reaches_gdf)

    dn = np.zeros(n, dtype=int)
    slope_laid = np.zeros(n)
    slope_min = np.zeros(n)
    inv_up = np.zeros(n)
    inv_dn = np.zeros(n)
    us_depth = np.zeros(n)
    ds_depth = np.zeros(n)
    cov_us = np.zeros(n)
    cov_dn = np.zeros(n)
    vel = np.zeros(n)
    dod = np.zeros(n)
    ret = np.zeros(n)
    grad_by = np.empty(n, dtype=object)
    sized_by = np.empty(n, dtype=object)
    clean_by = np.empty(n, dtype=object)
    tie_type = np.empty(n, dtype=object)
    material = np.empty(n, dtype=object)
    past_cap = np.zeros(n, dtype=int)
    cap_exit = np.empty(n, dtype=object)
    cap_len = np.zeros(n)
    n_material_fix = 0

    for uid, r in R.items():
        i = idx[uid]
        q = r.q_m3s
        s = r.slope_frac
        y, v = H.pipe_state(r.dn, s, q, C_)                 # exact, unmemoised
        dn[i] = r.dn
        slope_laid[i] = r.slope_pct
        slope_min[i] = round(H.smin_for(r.dn, q, C_) * 100.0, 6)
        # SLOPE_MIN can only ever round ABOVE SLOPE_LAID by float noise; the contract's own
        # cross-check treats that as the row contradicting itself, so clamp the printed
        # minimum to the laid value rather than publish an impossible pair.
        if slope_min[i] > slope_laid[i]:
            slope_min[i] = slope_laid[i]
        inv_up[i] = r.inv_up
        inv_dn[i] = r.inv_up - s * r.length                 # exactly LEN_M x SLOPE_LAID/100
        us_depth[i] = solver.grd[r.us] - inv_up[i]
        ds_depth[i] = solver.grd[r.ds] - inv_dn[i]
        cov_us[i] = K.cover(r.dn, us_depth[i])
        cov_dn[i] = K.cover(r.dn, ds_depth[i])
        vel[i] = 0.0 if v is None else v
        dod[i] = 1.0 if y is None else min(y, 1.0)          # surcharged reads as full: H2 fails
        ret[i] = (r.length / (vel[i] * 60.0)) if vel[i] > 1e-6 else 0.0
        grad_by[i] = r.gradient_by
        sized_by[i] = r.sized_by
        if v is not None and v >= C_.V_SELF_CLEANSING:
            clean_by[i] = "velocity"
        elif s >= H.smin_tractive(q, C_) - 1e-12:
            clean_by[i] = "tractive"
        else:
            clean_by[i] = "neither"                         # H5 fails it, loudly
        tie_type[i] = r.tie_type
        m = C_.material(r.dn)
        if K.material_conflict(r.tier, r.dn, m) is not None:
            # G203-p22 Tab 6 permits PVC-U on a MAIN sewer only to 250 mm even though the
            # product runs to OD315 (Tab 7). The conservative default until NWS answers
            # OPEN-2 is HDPE - chosen here so the count is known rather than zero.
            m = "HDPE"
            n_material_fix += 1
        material[i] = m
        past_cap[i] = r.past_cap
        cap_exit[i] = r.cap_exit
        cap_len[i] = r.cap_len_m

    rg = reaches_gdf.copy()
    rg["DN"] = dn
    rg["MATERIAL"] = material
    rg["SLOPE_LAID"] = slope_laid
    rg["SLOPE_MIN"] = slope_min
    rg["GRAD_BY"] = grad_by
    rg["SIZED_BY"] = sized_by
    rg["CLEAN_BY"] = clean_by
    # the tau the tractive gradients were ACTUALLY computed at - `hydra.smin_tractive` reads
    # it off the criteria object, not off SolverOptions (see LevelSolver.__init__)
    rg["TAU_PA"] = float(C_.TAU_PA)
    rg["INV_UP"] = inv_up
    rg["INV_DN"] = inv_dn
    rg["US_DEPTH"] = us_depth
    rg["DS_DEPTH"] = ds_depth
    rg["COVER_US"] = cov_us
    rg["COVER_DN"] = cov_dn
    rg["V_PK_MS"] = vel
    rg["DOD_PK"] = dod
    rg["RET_MIN"] = ret
    rg["PAST_CAP"] = past_cap
    rg["CAP_EXIT"] = cap_exit
    rg["CAP_LEN_M"] = cap_len
    rg["TIE_TYPE"] = tie_type
    rg["STAGE"] = STAGE

    # ---- nodes. Seated onto the pipes by the reverse pass, in the same transaction.
    # `reset_index` because the solver holds this frame indexed by NODE_UID for lookup, and a
    # GeoPackage write would try to materialise that index as a second column of the same
    # name. Identity lives in the COLUMN; the index is a convenience and never travels.
    ng = nodes_gdf.copy().reset_index(drop=True)
    uids = ng["NODE_UID"].astype(str).tolist()
    inv_m = np.zeros(len(ng))
    depth_m = np.zeros(len(ng))
    cover_m = np.zeros(len(ng))
    drop_m = np.zeros(len(ng))
    drop_t = np.empty(len(ng), dtype=object)
    vortex = np.zeros(len(ng), dtype=int)
    npc = np.zeros(len(ng), dtype=int)
    nce = np.empty(len(ng), dtype=object)
    kinds = ng["NODE_KIND"].astype(str).tolist()
    tiers = ng["TIER"].astype(str).tolist() if "TIER" in ng.columns else [""] * len(ng)
    # ONE function computes the drop - `LevelSolver.node_drops` - and this publishes what it
    # returns. Recomputing it here is how the layer and the register end up disagreeing.
    drops = solver.node_drops()

    for i, u in enumerate(uids):
        iv = solver.node_inv.get(u)
        if iv is None:
            iv = solver.grd[u] - K.min_invert_depth(C_.DN_MIN_MAIN)
        inv_m[i] = iv
        depth_m[i] = solver.grd[u] - iv
        # COVER_M is the cover to the crown of the SHALLOWEST connected pipe, on that pipe's
        # OWN outside diameter - one definition, `contract.cover()`, for the schedule, the
        # drawing and the audit alike.
        covers, strict = [], []
        e = solver.out_edge.get(u)
        if e is not None:
            rr = solver.reaches[e]
            covers.append(K.cover(rr.dn, solver.grd[u] - rr.inv_up))
            strict.append(_cap_cover(rr.dn, solver.grd[u] - rr.inv_up))
        for x in solver.in_edges.get(u, ()):
            rr = solver.reaches[x]
            covers.append(K.cover(rr.dn, solver.grd[u] - rr.inv_dn))
            strict.append(_cap_cover(rr.dn, solver.grd[u] - rr.inv_dn))
        cover_m[i] = min(covers) if covers else 0.0
        cover_strict = min(strict) if strict else 0.0

        # the drop INSIDE the chamber: arrivals against what leaves it (G203-p30)
        d = drops.get(u, (0.0, ""))[0]
        drop_m[i] = d
        drop_t[i] = ("none" if d <= C_.DROP_TRIGGER + 1e-9
                     else ("backdrop" if d <= C_.BACKDROP_MAX + 1e-9 else "vortex"))
        vortex[i] = 1 if d > C_.BACKDROP_MAX + 1e-9 else 0
        if d > solver.opts.max_drop_m + 1e-9:
            # Never clipped. A drop this stage could not resolve reaches `write_back` only
            # when `run()` has already decided to refuse, and it is published as measured so
            # the register and the refusal describe the same number. Clamping it to the
            # contract's ceiling would satisfy the validator by lying, which is the exact
            # class of defect the validator exists to catch.
            solver._bump("drop_over_ceiling_published")

        if u in solver.lift:
            kinds[i] = "station"
        pc, ce = 0, ""
        if e is not None:
            rr = solver.reaches[e]
            if rr.past_cap:
                pc, ce = 1, rr.cap_exit
        for x in solver.in_edges.get(u, ()):
            rr = solver.reaches[x]
            if rr.past_cap:
                pc, ce = 1, (ce or rr.cap_exit)
        if cover_strict > solver.opts.max_cover_m + 1e-6 and not pc:
            # A chamber past the cap that no reach flagged. The contract's node cross-check
            # refuses PAST_CAP=1 with a blank CAP_EXIT, and naming an exit here to get past
            # that check would be inventing the evidence philosophy sec 5 demands ("flagged,
            # with its depth, its length, WHICH EXIT ALLOWED IT"). The ladder is what tests
            # the exits; if it did not reach this chamber, the honest answer is to stop the
            # write, not to guess `recovers_500m`.
            raise ContractError(
                f"chamber {u} sits at {cover_strict:.2f} m of cover, past the "
                f"{solver.opts.max_cover_m:.0f} m cap, and no reach at it carries PAST_CAP. "
                "The cap-and-veto ladder did not see it, so no exit has been tested and none "
                "may be named (philosophy sec 5). This is a solver defect, not a data "
                "condition - the ladder must cover every over-cap reach.")
        npc[i], nce[i] = pc, ce

    ng["INV_M"] = inv_m
    ng["DEPTH_M"] = depth_m
    ng["COVER_M"] = cover_m
    ng["DROP_M"] = drop_m
    ng["DROP_TYPE"] = drop_t
    ng["VORTEX"] = vortex
    ng["PAST_CAP"] = npc
    ng["CAP_EXIT"] = nce
    ng["NODE_KIND"] = kinds
    ng["STAGE"] = STAGE
    if "TIER" in ng.columns:
        # the node's TIER is the tier of the reach LEAVING it (contract NODES.TIER)
        t = list(ng["TIER"].astype(str))
        for i, u in enumerate(uids):
            e = solver.out_edge.get(u)
            if e is not None:
                t[i] = solver.reaches[e].tier
        ng["TIER"] = t
    return ng, rg, n_material_fix


# ======================================================================================
# Reporting
# ======================================================================================

def summary(rg, ng, solver: LevelSolver, rep: Dict) -> str:
    L = rg["LEN_M"].sum() / 1000.0
    lines = [
        f"reaches            {len(rg):,}   {L:,.1f} km",
        f"chambers           {len(ng):,}",
        f"diameters          " + ", ".join(
            f"DN{int(d)} {int(c)}" for d, c in rg["DN"].value_counts().sort_index().items()),
        f"gradient set by    " + ", ".join(
            f"{k} {int(v)}" for k, v in rg["GRAD_BY"].value_counts().items()),
        f"diameter set by    " + ", ".join(
            f"{k} {int(v)}" for k, v in rg["SIZED_BY"].value_counts().items()),
        f"self-cleansing by  " + ", ".join(
            f"{k} {int(v)}" for k, v in rg["CLEAN_BY"].value_counts().items())
        + f"   (tractive rests on tau = {solver.opts.tau_pa} Pa, GAP-9/OPEN-4)",
        f"cover              min {rg[['COVER_US', 'COVER_DN']].min().min():.2f} m, "
        f"max {rg[['COVER_US', 'COVER_DN']].max().max():.2f} m "
        f"(H3 floor 1.30, H4 cap {solver.opts.max_cover_m:.0f})",
        f"deepest chamber    {ng['DEPTH_M'].max():.2f} m to invert",
        f"past the cap       {int(rg['PAST_CAP'].sum()):,} reaches, "
        f"{rg.loc[rg['PAST_CAP'] == 1, 'LEN_M'].sum() / 1000.0:.2f} km"
        + ("" if not rep["breaches"] else
           "   exits: " + ", ".join(
               f"{b['exit'] or 'NONE -> station'} {b['exit_len_m']:.0f} m"
               for b in rep["breaches"][:6])),
        f"lifting stations   {rep.get('stations_final', 0)} demanded by the cap "
        f"(rung 1 only; veto and economics are stage 7's)",
        f"drops              {int((ng['DROP_TYPE'] == 'backdrop').sum()):,} backdrops, "
        f"{int(ng['VORTEX'].sum()):,} vortex shafts (G203-p30: > 0.60 m, > 2.0 m); "
        f"tallest {ng['DROP_M'].max():.2f} m against the {solver.opts.max_drop_m:.1f} m "
        f"project ceiling (contract.NODES.DROP_M.hi)"
        + ("" if not rep["drop_withdrawn"] else
           f"\n                   {len(rep['drop_withdrawn'])} sec 5 exit(s) WITHDRAWN and "
           "pumped instead - 'never a drop used to dodge a station'"),
        f"solver             {rep['passes']} cap pass(es), reverse "
        + ", ".join(f"{k}={v}" for k, v in rep["reverse"].items()),
        f"fixed structures   {len(solver.fixed_inv)} existing inverts the design yields to "
        f"(H14); {len(solver.tie_conflicts)} could not be reached by gravity at the flattest "
        f"legal gradient"
        + ("" if solver.fixed_inv else
           "  <- reverse operations 2 and 4 therefore had nothing to clamp, which is why "
           "their counts are zero. Declared, not silent."),
    ]
    if rep["counters"]:
        lines.append("counters           "
                     + ", ".join(f"{k}={v}" for k, v in sorted(rep["counters"].items())))
    return "\n".join(lines)


# ======================================================================================
# Entry point
# ======================================================================================

def run(root: str = K.W11A_ROOT, gpkg_name: str = "W11a.gpkg",
        terrain: Optional[str] = TERRAIN_VRT, opts: SolverOptions = SolverOptions(),
        publish: bool = True) -> int:
    """Solve levels and sizes on the published graph. Returns a process exit code.

    Degrades gracefully and on purpose: if the layers stages 1-5 own are not there, this
    prints exactly what it is waiting for and returns 0. A stage that crashed would look the
    same in a log as a stage that failed for a real reason, and the whole point of the W11a
    manifest is that the two are never confused.
    """
    t0 = time.time()
    gpkg = K.gpkg_path(root, gpkg_name)
    print(f"W11a stage 6 - levels and sizes\n  reading {gpkg}")

    nodes, reaches, waiting = load_inputs(gpkg)
    if waiting or nodes is None or reaches is None:
        print("\nWAITING ON AN UPSTREAM STAGE - nothing solved, nothing written.")
        for w in waiting:
            print(f"  needs: {w}")
        print("\n  Stage 6 levels and sizes a graph that stages 1-5 produce:")
        print("    stage 2 corridors -> 3 hierarchy -> 4/5 chambers, flows and the trunk")
        print("    then this stage writes DN, SLOPE_LAID/SLOPE_MIN, inverts, cover and the")
        print("    cap-and-veto flags onto `nodes` and `reaches` in the same GeoPackage.")
        print("  Run `python s6_levels.py --self-test` to exercise the solver meanwhile.")
        return 0

    miss_r = _missing(reaches, K.REACHES, OWNED_REACH, NEEDED_REACH)
    miss_n = _missing(nodes, K.NODES, OWNED_NODE, NEEDED_NODE)
    if miss_r or miss_n:
        print("\nWAITING ON AN UPSTREAM STAGE - the layers exist but do not carry the fields")
        print("this stage reads and does not own. Nothing solved, nothing written.")
        if miss_r:
            print(f"  reaches missing: {', '.join(miss_r)}")
        if miss_n:
            print(f"  nodes missing:   {', '.join(miss_n)}")
        print("  (a field this stage OWNS is not listed - it is computed here, not read)")
        return 0

    nodes = nodes.set_index(nodes["NODE_UID"].astype(str), drop=False)
    node_grd = {str(u): float(z) for u, z in zip(nodes["NODE_UID"], nodes["GRD_M"])}

    sampler = None
    if terrain and os.path.exists(terrain):
        sampler = TileSampler(terrain)
    else:
        print(f"  NOTE: terrain {terrain} not found - mid-span cover will be checked on a "
              "straight ground line between chambers, not on the 0.5 m VRT. Declared, "
              "not silent (Bentley 'Consider Cover Along Pipe Length'; research A5).")

    # A stage-specific manifest, NOT the shared `run/manifest.json`. `Manifest.records` is a
    # per-process list, so every stage that takes the default path rewrites that file with
    # only its own record and silently erases the others'. Writing to our own path is the
    # convention S1, S4, S7, S8 and S9 already follow, and it is the only one that lets the
    # run be reconstructed from what is on disk (P2, invariant 10).
    man = os.path.join(root, "run", "manifest_s6_levels.json")
    with K.Manifest.stage("S6 levels and sizes", STAGE_ORDER, path=man) as rec:
        rec.read("nodes", gpkg, len(nodes))
        rec.read("reaches", gpkg, len(reaches))
        if sampler is not None:
            rec.read("terrain", terrain)

        rlist, pstats = build_reaches(reaches, opts, sampler, node_grd)
        f = rec.funnel("reaches into the solver", len(reaches))
        f.close(len(rlist))

        solver = LevelSolver(nodes, rlist, opts)
        report = solver.solve()
        ng, rg, n_mat = write_back(nodes, reaches, solver)

        rec.metric("pipe_km", round(float(rg["LEN_M"].sum()) / 1000.0, 2))
        rec.metric("stations_demanded_by_cap", report.get("stations_final", 0))
        rec.metric("reaches_past_cap", int(rg["PAST_CAP"].sum()))
        rec.metric("km_past_cap", round(
            float(rg.loc[rg["PAST_CAP"] == 1, "LEN_M"].sum()) / 1000.0, 3))
        rec.metric("deepest_chamber_m", round(float(ng["DEPTH_M"].max()), 2))
        rec.metric("min_cover_m", round(float(rg[["COVER_US", "COVER_DN"]].min().min()), 3))
        rec.metric("tractive_share_pct", round(
            100.0 * float((rg["CLEAN_BY"] == "tractive").sum()) / max(len(rg), 1), 1))
        rec.metric("material_downgraded_to_HDPE", n_mat)
        # Two different facts, reported separately because conflating them would hide which
        # one happened: a hole in the VRT under a sample point, versus no VRT at all.
        rec.metric("profile_points_nodata", pstats["profile_nodata"])
        rec.metric("reaches_with_no_terrain_read", pstats["no_terrain"])
        for k, v in report["counters"].items():
            rec.metric(f"counter_{k}", v)
        rec.note("Order of operations is Bentley's published sequence: bracket (3-4), "
                 "Level A (5-13), size for capacity (14), Level B (15-22), then a four-"
                 "operation reverse reconciliation in which the manhole yields to the pipe "
                 "(W10/docs/research/SEWERGEMS_DESIGN_METHOD.md).")
        rec.note("A station here is a LIFT INSIDE THE CHAMBER: the arriving invert stays, the "
                 "outgoing invert is re-seated at minimum cover, and the difference is the "
                 "static lift. Wet well, duty, rising main and discharge chamber are stage "
                 "7's. Published DEPTH_M at a station node is therefore the SHALLOW outgoing "
                 "depth; the true wet-well depth is in run/s6_station_demand.csv.")
        if report.get("cap_loop_exhausted"):
            rec.note(f"the cap loop hit its {opts.max_cap_passes}-pass bound - the last pass "
                     "still added a station, so the levels are not settled. Investigate "
                     "before publishing anything downstream of this.")

        os.makedirs(os.path.join(root, "run"), exist_ok=True)
        st_csv = os.path.join(root, "run", "s6_station_demand.csv")
        st = pd.DataFrame(list(solver.station_note.values()))
        st.to_csv(st_csv, index=False)
        rec.wrote("station demand register", st_csv, len(st))

        br_csv = os.path.join(root, "run", "s6_cap_breaches.csv")
        br = pd.DataFrame([{k: v for k, v in b.items() if k != "chain"}
                           for b in report["breaches"]])
        br.to_csv(br_csv, index=False)
        rec.wrote("cap breach register", br_csv, len(br))

        tc_csv = os.path.join(root, "run", "s6_tie_conflicts.csv")
        tc = pd.DataFrame(solver.tie_conflicts)
        tc.to_csv(tc_csv, index=False)
        rec.wrote("tie conflict register", tc_csv, len(tc))
        rec.metric("tie_conflicts", len(tc))

        # ---- the drop schedule. G203-p30 makes every drop over 600 mm a STRUCTURE with a
        # cost and a maintenance regime, so it is a schedule the take-off reads, not a column
        # on the node layer that nobody opens.
        dr_csv = os.path.join(root, "run", "s6_drop_structures.csv")
        _dcols = [c for c in ("NODE_UID", "NODE_KIND", "TIER", "GRD_M", "INV_M", "DEPTH_M",
                              "DROP_M", "DROP_TYPE", "VORTEX", "MH_DIA")
                  if c in ng.columns]
        dr = ng.loc[ng["DROP_TYPE"] != "none", _dcols].copy()
        if len(dr):
            dr["ARRIVING_EDGE"] = [report["drops"].get(str(u), (0.0, ""))[1]
                                   for u in dr["NODE_UID"]]
            dr = dr.sort_values("DROP_M", ascending=False)
        dr.to_csv(dr_csv, index=False)
        rec.wrote("drop structure schedule", dr_csv, len(dr))
        rec.metric("backdrops_0p6_to_2m", report["n_backdrop"])
        rec.metric("vortex_drop_shafts_over_2m", report["n_vortex"])
        rec.metric("exits_withdrawn_by_drop_ceiling", len(report["drop_withdrawn"]))
        rec.metric("drop_ceiling_m", opts.max_drop_m)
        if report["drop_withdrawn"]:
            wd_csv = os.path.join(root, "run", "s6_drop_ceiling_withdrawals.csv")
            pd.DataFrame(report["drop_withdrawn"]).to_csv(wd_csv, index=False)
            rec.wrote("exits withdrawn by the drop ceiling", wd_csv,
                      len(report["drop_withdrawn"]))
            rec.note(f"{len(report['drop_withdrawn'])} philosophy sec 5 exit(s) were "
                     "WITHDRAWN because the run they let past the cap would have forced a "
                     f"drop above the {opts.max_drop_m:.1f} m project ceiling "
                     "(contract.NODES.DROP_M.hi; G203-p30 sets 2 m for a backdrop and no "
                     "maximum for the vortex shaft that replaces it). Each was resolved by a "
                     "station at the foot of the climb - philosophy sec 5, 'never a drop used "
                     "to dodge a station'. This is a PROJECT DECISION, not a guideline value.")

        if report["drop_over_ceiling"] or report["drop_unresolved"]:
            publish = False
            uc_csv = os.path.join(root, "run", "s6_drops_unbuildable.csv")
            # the measured drops, each carrying the reason the last pass could not resolve it
            why = {r["NODE_UID"]: r.get("WHY_UNRESOLVED", "")
                   for r in report["drop_unresolved"]}
            pd.DataFrame([dict(r, WHY_UNRESOLVED=why.get(r["NODE_UID"], ""))
                          for r in report["drop_over_ceiling"]]
                         or report["drop_unresolved"]).to_csv(uc_csv, index=False)
            rec.wrote("chambers whose drop cannot be built", uc_csv,
                      len(report["drop_over_ceiling"]))
            rec.note(f"REFUSED TO PUBLISH: {len(report['drop_over_ceiling'])} chamber(s) need "
                     f"a drop above the {opts.max_drop_m:.1f} m ceiling that this stage could "
                     "not resolve. The resolutions left are physical and none is stage 6's - "
                     "a re-route, a different outlet, or not serving that branch "
                     "(philosophy sec 3).")

        if report["unexited"]:
            # Rung 1 of the ladder could not be discharged. Every resolution left is physical
            # (philosophy sec 3) and none of them is this stage's to take: more stations than the
            # pass bound allowed, a re-route, a different tie point, or not serving that
            # branch by this network. Publishing anything here would put a chamber past the
            # cap onto a layer with PAST_CAP=0, which is the W10 defect verbatim.
            publish = False
            rec.note(f"REFUSED TO PUBLISH: {len(report['unexited'])} cap breaches "
                     f"({report['km_unexited']:.2f} km) are past 12 m of cover with neither "
                     "philosophy sec 5 exit and no station resolving them within "
                     f"{opts.max_cap_passes} passes. The registers name every one.")

        if publish:
            p = K.publish(ng, "nodes", root, stage=STAGE)
            rec.wrote("nodes", p, len(ng))
            p = K.publish(rg, "reaches", root, stage=STAGE)
            rec.wrote("reaches", p, len(rg))
            K.Network.assert_round_trip(ng, rg)
            K.Network.assert_degrees(ng, rg)
            ready = K.audit_readiness(reaches=rg, nodes=ng,
                                      external=("roads", "hazard", "existing"))
            rec.metric("audit_checks_ready",
                       f"{int(ready.can_run.sum())}/{len(ready)}")
            not_ready = ready[~ready.can_run]
            if len(not_ready):
                rec.note("checks that still cannot run: "
                         + "; ".join(f"{r.check} needs {r.missing}"
                                     for r in not_ready.itertuples()))

    if sampler is not None:
        sampler.close()
    print()
    print(summary(rg, ng, solver, report))
    print(f"\n  station demand -> {st_csv}")
    print(f"  cap breaches   -> {br_csv}")
    print(f"  tie conflicts  -> {tc_csv}")
    print(f"  drop schedule  -> {dr_csv}")
    print(f"  manifest       -> {man}")
    print(f"  {time.time() - t0:.1f} s")
    if report["drop_over_ceiling"] or report["drop_unresolved"]:
        print(f"\nNOTHING PUBLISHED. {len(report['drop_over_ceiling'])} chamber(s) need a "
              f"drop above the {opts.max_drop_m:.1f} m ceiling this stage could not resolve "
              f"(worst {report['drop_over_ceiling'][0]['DROP_M'] if report['drop_over_ceiling'] else 0:.2f} m).")
        print("G203-p30 gives 2 m for a backdrop and no maximum for the vortex shaft that "
              "replaces it, so\nthe ceiling is a PROJECT DECISION read from "
              "contract.NODES.DROP_M.hi. Philosophy sec 5:\n'never a drop used to dodge a "
              "station'. The resolutions left are a re-route, a different\noutlet, or not "
              "serving that branch - none of them stage 6's.")
        print(f"Read {os.path.join(root, 'run', 's6_drops_unbuildable.csv')}.")
        return 1
    if report["unexited"]:
        print(f"\nNOTHING PUBLISHED. {len(report['unexited'])} cap breaches "
              f"({report['km_unexited']:.2f} km) sit past {opts.max_cover_m:.0f} m of cover "
              "with neither\nphilosophy sec 5 exit, and no station resolved them within "
              f"{opts.max_cap_passes} passes.")
        print("Every resolution left is physical and none is this stage's to take: more "
              "stations,\na re-route, a different tie point, or not serving that branch by "
              "this network.")
        print(f"Read {br_csv} - the rows with an empty `exit` are the ones to answer.")
        return 1
    return 0


# ======================================================================================
# Self-test - the solver exercised end to end on a synthetic graph
# ======================================================================================

def self_test(root: Optional[str] = None) -> int:
    """Build a small network with the contract's own Network, solve it, publish it, audit it.

    The point is not a unit test. It is that this module can be proved to run end to end -
    forward pass, sizing, reverse pass, ladder, contract validation and the auditor's own
    checks - before stages 1-5 exist, so that when they do land the only new thing is their
    data.

    The profile is built to bite every branch, because a self-test that only walks the easy
    path is the thing that let W10 ship:

      A  1.2 km almost dead flat, flatter than any legal gradient  -> the pipe digs itself
         down, which is how a sewer arrives at a pumping station
      B  a short hump, then back down                              -> past the cap, cover
         RECOVERS within 500 m: exit `recovers_500m`, flagged, no station
      C  a long rise that never comes back                         -> past the cap with NO
         exit: the fourth physical resolution, a station
      D  a cliff at ~7.5 % carrying a trunk flow                   -> the 3.0 m/s velocity
         cap (H7) binds, the surplus fall is taken as drops at the chambers, and above 2 m
         those drops become vortex shafts (G203-p30)
      E  the last chamber is a TIE with a fixed invert             -> the reverse pass's
         operations 2 and 4 have something real to clamp

    Flows rise along the run so the diameter series is actually exercised rather than every
    reach landing on the DN200 floor.
    """
    import tempfile
    root = root or os.path.join(tempfile.gettempdir(), "w11a_s6_selftest")
    os.makedirs(os.path.join(root, "shp"), exist_ok=True)
    os.makedirs(os.path.join(root, "run"), exist_ok=True)

    net = K.Network()
    n, SP = 70, 80.0                      # 70 chambers at 80 m centres = 5.5 km
    ground, z = [], 330.0
    for i in range(n):
        if i < 15:
            dz = -0.02                    # A: 0.025 % - flatter than the DN200 minimum
        elif i < 19:
            dz = +1.7                     # B: up
        elif i < 23:
            dz = -1.7                     # B: and back down, inside 500 m
        elif i < 32:
            dz = -0.05
        elif i < 45:
            dz = +1.1                     # C: a rise that never recovers
        else:
            dz = -6.0                     # D: ~7.5 % cliff
        z += dz
        ground.append(z)

    uids = []
    for i in range(n):
        kind = "head" if i == 0 else ("tie" if i == n - 1 else "chamber")
        uids.append(net.node(1000.0 + SP * i, 2000.0, kind=kind, tier="trunk main",
                             grd_m=ground[i], inv_m=ground[i] - 2.0, stage="T5"))
    for i in range(n - 1):
        net.add_edge(uids[i], uids[i + 1], stage="T5", tier="trunk main")

    ng = net.to_nodes_gdf()
    rg = net.to_edges_gdf()

    # everything stage 5 owns, fabricated so the contract can validate the pair
    def _qadf(i):                          # m3/d accumulated - up to a trunk-sized flow
        return round(120.0 * (i + 1), 2)

    # IS_OUTFALL arrived in the contract on 2026-09-02 and neither `Network.to_nodes_gdf` nor
    # stage 5 writes it yet, so the self-test fabricates it here along with everything else
    # stage 5 owns. H15 reads it: exactly one per connected component, and this run is one
    # chain, so it is the last chamber. When stage 5 starts publishing it this block becomes
    # a no-op, which is why it is written as a fill rather than an overwrite.
    if "IS_OUTFALL" not in ng.columns:
        ng["IS_OUTFALL"] = [0] * (len(ng) - 1) + [1]
    ng["INLET_DEG"] = 180.0
    ng["INLET_FLAG"] = 0
    ng["Q_ADF_M3D"] = [_qadf(i) for i in range(len(ng))]
    ng["Q_PK_LS"] = [round(_qadf(i) * 1000.0 / 86400.0 * 2.2, 3) for i in range(len(ng))]
    ng["N_PROP"] = [float(20 * (i + 1)) for i in range(len(ng))]
    ng["MH_DIA"] = 1.5
    ng["SRC"] = "draft"
    ng["CONFIDENCE"] = "drafted"
    # E: the run ends on an existing structure whose invert is FIXED (H14). The design yields
    # to it, soffit to soffit - it does not move the existing sewer to suit us.
    fix = [np.nan] * len(ng)
    fix[-1] = round(ground[-1] - 3.4, 3)
    ng["FIX_INV"] = fix

    m = {str(u): i for i, u in enumerate(ng["NODE_UID"])}
    rg["QADF_M3D"] = [_qadf(m[str(u)]) for u in rg["US_NODE"]]
    rg["QINF_LS"] = [round(720.0 * (l / 1000.0) / 86400.0, 6) for l in rg["LEN_M"]]
    rg["PF"] = 2.2
    rg["PF_METH"] = "merrimack"
    rg["QPK_LS"] = [round(q * 1000.0 / 86400.0 * 2.2 + inf, 6)
                    for q, inf in zip(rg["QADF_M3D"], rg["QINF_LS"])]
    rg["N_PROP"] = 400.0
    rg["ON_DUAL_M"] = 0.0
    rg["ON_WADI_M"] = 0.0
    rg["CROSS_ID"] = ""
    rg["SRC"] = "draft"
    rg["CONFIDENCE"] = "drafted"

    p = os.path.join(root, "shp", "W11a.gpkg")
    if os.path.exists(p):
        os.remove(p)
    ng.to_file(p, layer="nodes", driver="GPKG")
    rg.to_file(p, layer="reaches", driver="GPKG")
    print(f"self-test: synthetic graph of {len(ng)} chambers / {len(rg)} reaches at {p}")

    rc = run(root=root, terrain=None, publish=True)

    # and let the auditor speak for itself on what this stage produced
    try:
        from w11a import audit
        pipes = gpd.read_file(p, layer="reaches")
        nds = gpd.read_file(p, layer="nodes")
        ctx = audit.Ctx(pipes=pipes, nodes=nds, crit=C)
        res = audit.run(ctx)
        keep = {"H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H11", "H12",
                "H13", "H15", "R1", "R2", "G1", "G2", "G3"}
        print("\nauditor on the self-test design "
              "(H1/H10/H14/R3/R4 need layers this stage does not own):")
        print(audit.report([r for r in res if r.id in keep]))
    except Exception as exc:                                     # pragma: no cover
        print(f"  auditor could not run on the self-test: {exc}")
    return rc


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=K.W11A_ROOT)
    ap.add_argument("--gpkg", default="W11a.gpkg")
    ap.add_argument("--terrain", default=TERRAIN_VRT)
    ap.add_argument("--no-terrain", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--profile-step", type=float, default=SolverOptions.profile_step_m)
    ap.add_argument("--allow-smaller-downstream", action="store_true",
                    help="switch off Bentley priority 4 (downstream never smaller than "
                         "upstream); it is a declared method choice, not a PAM-GUD rule")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    opts = SolverOptions(profile_step_m=a.profile_step,
                         non_decreasing_dn=not a.allow_smaller_downstream)
    return run(root=a.root, gpkg_name=a.gpkg,
               terrain=(None if a.no_terrain else a.terrain), opts=opts)


if __name__ == "__main__":
    sys.exit(main())
