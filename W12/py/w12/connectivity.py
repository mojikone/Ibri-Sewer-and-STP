"""w12.connectivity - THE PLOT CONNECTABILITY CHECK, and nothing else.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous
folder's code and edits it. Earlier folders are read as data and as lessons, never
re-derived from scratch. Superseded folders stay untouched as the record. This file is NEW
in W12 - there was no module to inherit, because in W11b the check lived inline in two
stages and disagreed with itself between them.

----------------------------------------------------------------------------------------
WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT

House connections are NOT DESIGNED at concept stage - `criteria.CONCEPT_OFF
["house_connections"]`. No rider, no lateral, no property connection chamber, no house
connection chamber, no schedule of them. What the concept stage asks of a plot is ONE
question:

    can this plot reach ITS chamber, on gravity, at all?

and the deliverable of that question is three fields on `contract.CONNECTIONS`:

    CAN_CONN   0/1   the answer
    CONN_WHY   str   why not, from a closed vocabulary so the schedule groups
    CONN_NEED  float HOW MUCH DEEPER the sewer on that run would have to be, in metres

Concept rule 7 is FLAG, DO NOT SOLVE. A flag with no size cannot be priced, cannot be
ranked and cannot be argued about - "5,521 plots cannot drain" is a number nobody can act
on until it is "5,521 plots needing this much depth on these runs".

----------------------------------------------------------------------------------------
THE NAIVE TEST IS WRONG THREE WAYS, AND THE ENGINEER SAID SO IN ONE SENTENCE

    "of course a plot will connect to the network under ground. so be careful not just
     compare the ground level at plot with the pipe level normal to plot's elevation
     normal to plot's centroid."                                (engineer, 2026-09-05/06)

The naive test - ground level at the plot centroid against the sewer invert at the nearest
perpendicular point on a pipe - is optimistic in three independent ways, and each one
passes plots that in fact cannot connect:

  1. IT LEAVES BELOW GROUND, NOT AT IT.  The connection starts at an INVERT, not at a
     surface. Comparing the plot's GROUND level against a pipe invert credits the plot
     with a metre of fall it does not have.
  2. IT RUNS TO A CHAMBER, NOT TO THE NEAREST POINT ON A PIPE.  A house drain cannot be
     hot-tapped into the barrel of a sewer at whatever point happens to be nearest. It
     runs to a manhole. The manhole is further away and is usually UPSTREAM of the nearest
     point, so it is both a longer route AND a higher invert.
  3. IT LOSES FALL OVER ITS OWN LENGTH.  A connection is a pipe with a minimum gradient of
     its own (G203-p18 Table 5). Over 40 m at 1 % that is 0.40 m of fall spent before the
     connection arrives, and the level comparison never sees it.

`naive_can_connect()` is in this file, clearly labelled, precisely so the three modes can
be demonstrated rather than asserted - `tests/test_connectivity.py` builds one plot for
each and shows the naive answer and the real answer disagree.

----------------------------------------------------------------------------------------
THE TEST THIS MODULE RUNS

    outlet_inv  =  ground at the plot        -  outlet_depth        (rule 1: below ground)
    fall        =  s_pcs * pcs_run           +  s_street * the rest (rule 3: fall is spent)
    arrive_inv  =  outlet_inv                -  fall
    req_inv     =  invert AT THE CHAMBER     +  arrival allowance   (rule 2: to a chamber)

    CAN_CONN    =  arrive_inv >= req_inv - tol
    CONN_NEED   =  max(req_inv - arrive_inv, 0)

Every term traces to a page or to this module's own ASSUMPTIONS register:

    outlet_depth   HCC_DEPTH_MIN 1.2 m       G203-p19 sec 3.4 (HCC depth 1.2 - 2.0 m)
    s_pcs          PCS_MIN_SLOPE 3 %         G203-p18 Table 5, Property Connection Sewer
    s_street       LATERAL_MIN_SLOPE 1 %     G203-p18 Table 5, Lateral / Rider Sewer
    pcs_run        HCC_OFFSET_M 2.5 m        G203-p17 sec 3.2 (HCC 2.5 m into the ROW)
    allowance      d/D limit x internal bore G203-p27 Table 10 - see ARRIVAL RULES below

THE MINIMUM GRADIENT IS THE RIGHT ONE TO USE, and it is not a shortcut. A connection laid
at its minimum legal gradient loses the LEAST fall over its route, so it is the most
generous case the guideline permits. A plot that fails at the minimum fails at every legal
gradient. The maximum (10 %, G203-p18 Table 5) is a separate matter and is flagged, not
failed: a connection with MORE fall available than 10 % of its length takes the surplus at
a drop, which is the same rule concept rule 1 applies to the sewers themselves.

----------------------------------------------------------------------------------------
ARRIVAL RULES - what "+ allowance" means, and why it is not a constant

A connection that discharges BELOW the water surface of the sewer it joins is drowned at
peak flow and backs up into the property. G203 nowhere writes "a connection shall arrive
above the design flow surface" - so the RULE is this module's assumption. The NUMBER is
not invented: it is the guideline's own depth of flow.

    "flow_depth"  (default)  allowance = dod_limit(DN) x internal_diameter(DN)
                             G203-p27 Table 10: d/D <= 0.65 to DN350, <= 0.50 above.
                             DN200 -> 0.122 m; DN1200 -> 0.600 m. IT VARIES WITH THE BORE,
                             which is the point: inheritance row 22 makes a published
                             column that is constant where it should vary a FABRICATION.
    "soffit"                 allowance = internal_diameter(DN). The strict reading - the
                             connection arrives above the crown of the bore.
    "invert"                 allowance = 0. The loosest reading, and it is what W11b's
                             s8_export did. Kept so the two iterations can be compared,
                             and it is the ONLY rule that needs no receiving bore.

Under "flow_depth" and "soffit" THE RECEIVING BORE IS REQUIRED. If it is not supplied the
module RAISES rather than substituting a default diameter, because a default diameter
would make the allowance constant across every row - the fabrication above, arrived at by
politeness.

----------------------------------------------------------------------------------------
WHAT THIS MODULE CANNOT DECIDE, STATED UP FRONT

THE DEPTH AT WHICH A CONNECTION LEAVES A PLOT IS NOT SETTLED BY THE GUIDELINE, and it
moves the answer. Two readings are both defensible:

    BASIS_HCC       (the default) the connection is at the HCC's minimum depth, 1.2 m,
                    by the time it is in the public right of way - G203-p19 sec 3.4.
    BASIS_SHALLOW   the connection leaves the plot boundary at the shallowest legal
                    property connection - 0.60 m cover on an OD160 pipe, G203-p19 sec 3.5
                    and G203-p22 Table 6 - and only then runs 2.5 m at 3 % to the HCC.

They differ by 0.44 m at the plot boundary, closing to a steady 0.390 m once the shallow
reading has spent its 3 % over the first 2.5 m. `sensitivity()` runs both and reports how
many plots CHANGE ANSWER, so the band is a published number rather than a modelling choice
nobody sees. The default is the conservative one; the engineer's own words - "of course a
plot will connect to the network UNDER GROUND" - are a warning against optimism here.

----------------------------------------------------------------------------------------
ANYTHING A PASS CAN ADD, A LATER PASS MUST BE ABLE TO TAKE AWAY

Inheritance row 4, the row whose loss cost W11b 69 spurious pumping stations. This module
ADDS a CAN_CONN = 0 flag. The levelling stage can lower a sewer and make that flag wrong,
and a flag that is only ever added is a decision that is never re-examined. `recheck()`
takes the previous result and the new one and returns HOW MANY FAILURES WERE CLEARED, by
id, so the stage can publish the removal count instead of silently carrying stale flags.

----------------------------------------------------------------------------------------
NOTHING HERE READS A FILE, PUBLISHES A LAYER OR KNOWS WHERE THE PROJECT LIVES. It takes
frames and returns frames. `python -m w12.connectivity` runs the self-test.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .criteria import DEFAULT, Criteria

CONNECTIVITY_VERSION = "W12-connectivity-1.0"


class ConnectivityError(Exception):
    """Raised when the check CANNOT RUN - a missing receiving bore under a rule that needs
    one, a dangling OUT_NODE, an unknown arrival rule. Inheritance row 2: a check that
    cannot run is a FAILURE, not a blank, and the loud form of that is an exception rather
    than a column of zeros nobody can tell from a real answer."""


# ======================================================================================
# THE CLOSED VOCABULARY OF REASONS
# ======================================================================================
#
# Short, reusable and few, so the not-served schedule GROUPS. Free text per plot is 5,521
# unique sentences and a schedule nobody can total.
#
# Two of the six are LEVEL answers and four are MISSING-INPUT answers, and they are kept
# apart on purpose: "this plot cannot be served on gravity" and "we do not know whether
# this plot can be served" are different findings with different remedies, and W11b's
# `CAN_DRAIN cannot run` is what happens when they are merged into a blank.

WHY_LEVEL = "sewer above the plot outlet"     # fails even with a zero-length route
WHY_ROUTE = "route loses the fall"            # clears the chamber, not after the route
WHY_NO_NODE = "no chamber assigned"           # OUT_NODE blank - a scope answer
WHY_NO_INV = "chamber level unknown"          # the chamber has no designed invert yet
WHY_NO_GRD = "plot level unknown"             # no ground level at the plot
WHY_NO_LEN = "route length unknown"           # no route to measure the fall over
WHY_NO_DN = "chamber bore unknown"            # flow_depth / soffit rule with no bore

CONN_WHY_VOCAB: Tuple[str, ...] = (
    WHY_LEVEL, WHY_ROUTE, WHY_NO_NODE, WHY_NO_INV, WHY_NO_GRD, WHY_NO_LEN, WHY_NO_DN)

# The two that are a LEVEL verdict. The rest say the check could not be run on that row,
# and a stage that reports "N plots cannot connect" without separating these is reporting
# its own missing inputs as an engineering finding.
WHY_IS_A_VERDICT: Tuple[str, ...] = (WHY_LEVEL, WHY_ROUTE)

ARRIVAL_RULES: Tuple[str, ...] = ("flow_depth", "soffit", "invert")

# Levelling tolerance, m. STRUCTURAL, not a design value: it exists so a plot that clears
# its chamber by a float rounding error is not published as a failure. It is deliberately
# an order of magnitude below G203-p29's 20 mm construction tolerance, which is a
# different quantity (what the CONTRACTOR may deviate by) and is not this module's to
# spend on the design's behalf.
CONN_LEVEL_TOL_M = 0.001

# Columns this module returns. The first three are contract.CONNECTIONS fields and are the
# deliverable; the rest are diagnostics, every one of them a measured quantity that varies
# row to row, and every one <= 10 characters so a shapefile mirror keeps its name.
CONTRACT_COLS: Tuple[str, ...] = ("CAN_CONN", "CONN_WHY", "CONN_NEED")
DIAG_COLS: Tuple[str, ...] = (
    "OUT_INV_M",    # invert the connection leaves the plot at
    "ARR_INV_M",    # invert it arrives at the chamber with
    "REQ_INV_M",    # invert it must arrive at or above = chamber invert + allowance
    "ALLOW_M",      # the arrival allowance actually used on this row
    "ROUTE_M",      # the route length the fall was spent over
    "FALL_M",       # the fall spent over that route at the minimum gradient
    "MARGIN_M",     # arrive - required. Negative is the shortfall; CONN_NEED is its size
    "S_AVL_PCT",    # the steepest gradient the route could be laid at, %
    "CONN_LONG",    # 0/1 route past G203-p18's 50 m maintainable PCS length
    "CONN_STEEP",   # 0/1 more fall available than the 10 % maximum - needs a drop
)


# ======================================================================================
# THE BASIS - every assumption in one frozen object, so a run can state what it assumed
# ======================================================================================

@dataclass(frozen=True)
class Basis:
    """The connectability basis: what a connection leaves the plot at, what it is laid at,
    and what it must arrive above. Frozen, and printed with every result.

    Two objects, not two code paths. A sensitivity run passes a different Basis; nothing
    in this module has a branch on "which reading are we using today"."""
    name: str
    outlet_depth_m: float       # how far below ground the connection leaves the plot
    outlet_src: str             # the page or the reasoning that set it
    pcs_run_m: float            # how much of the route is laid at the PCS gradient
    s_pcs: float                # m/m, property connection sewer minimum
    s_street: float             # m/m, rider / lateral minimum
    s_max: float                # m/m, the 10 % maximum - flagged, never failed
    arrival_rule: str           # one of ARRIVAL_RULES
    tol_m: float = CONN_LEVEL_TOL_M

    def fall(self, route_m):
        """Fall spent over a route of this length, m. The first `pcs_run_m` at the
        property-connection minimum, the remainder at the rider / lateral minimum."""
        r = np.maximum(np.asarray(route_m, dtype=float), 0.0)
        head = np.minimum(r, self.pcs_run_m)
        return self.s_pcs * head + self.s_street * (r - head)

    def outlet_invert(self, grd_m):
        """The invert the connection leaves the plot at. RULE 1: below ground, never at
        it."""
        return np.asarray(grd_m, dtype=float) - self.outlet_depth_m

    def describe(self) -> str:
        return (f"{self.name}: outlet {self.outlet_depth_m:.3f} m below ground "
                f"({self.outlet_src}); {self.pcs_run_m:g} m at {self.s_pcs * 100:g} % then "
                f"{self.s_street * 100:g} % (G203-p18 Table 5); arrival rule "
                f"'{self.arrival_rule}'; tolerance {self.tol_m * 1000:g} mm")


def _check_basis(b: Basis, crit: Criteria) -> Basis:
    """Refuse a basis that breaks a guideline value on its way in. A basis is an
    assumption set, not a licence."""
    if b.arrival_rule not in ARRIVAL_RULES:
        raise ConnectivityError(
            f"unknown arrival rule {b.arrival_rule!r}. Known: {', '.join(ARRIVAL_RULES)}. "
            "An unknown rule raises rather than falling back, because a fallback rule is "
            "one nobody chose and nobody can find afterwards.")
    floor = crit.PCS_MIN_COVER + crit.outside_diameter(crit.DN_TERTIARY)
    if b.outlet_depth_m < floor - CONN_LEVEL_TOL_M:
        raise ConnectivityError(
            f"basis {b.name!r} leaves the plot {b.outlet_depth_m:.3f} m below ground, which "
            f"is shallower than the {floor:.3f} m a property connection needs: G203-p19 sec "
            f"3.5 requires {crit.PCS_MIN_COVER:g} m of cover and G203-p22 Table 6 makes the "
            f"pipe OD{crit.DN_TERTIARY}. A basis may be conservative or generous; it may not "
            "be illegal.")
    for nm, s in (("s_pcs", b.s_pcs), ("s_street", b.s_street)):
        if not (0.0 < s <= b.s_max):
            raise ConnectivityError(
                f"basis {b.name!r} has {nm} = {s:g}, outside the G203-p18 Table 5 range "
                f"(0, {b.s_max:g}]. Table 5 is the tertiary network's own slope table and "
                "the secondary network's Table 11 is not a substitute for it - using "
                "Table 11's 0.5 % at DN200 for a lateral is the design trap the criteria "
                "file names.")
    if b.pcs_run_m < 0.0:
        raise ConnectivityError(f"basis {b.name!r} has a negative pcs_run_m")
    return b


def basis_hcc(crit: Criteria = DEFAULT, *, arrival_rule: str = "flow_depth") -> Basis:
    """THE DEFAULT. The connection is at the house connection chamber's own minimum depth
    by the time it is in the public right of way, and runs from there at the rider /
    lateral minimum.

    G203-p19 sec 3.4: the HCC depth "ranges between 1.2 m and 2.0 m depending on the size
    of the plot", so 1.2 m is the guideline's own shallowest HCC. G203-p17 sec 3.2 puts it
    2.5 m into the ROW; from there the pipe is a rider or a lateral and G203-p18 Table 5
    gives it a 1 % minimum, not the property connection's 3 %.

    `pcs_run_m` is ZERO in this basis and that is deliberate, not an omission: the datum
    IS the HCC, so the property connection sewer is already behind us. Charging the route
    3 % over its first 2.5 m as well would be spending the same fall twice."""
    return _check_basis(Basis(
        name="BASIS_HCC",
        outlet_depth_m=crit.HCC_DEPTH_MIN,
        outlet_src="G203-p19 sec 3.4, the shallowest HCC the guideline states",
        pcs_run_m=0.0,
        s_pcs=crit.PCS_MIN_SLOPE,
        s_street=crit.LATERAL_MIN_SLOPE,
        s_max=crit.PCS_MAX_SLOPE,
        arrival_rule=arrival_rule), crit)


def basis_shallow(crit: Criteria = DEFAULT, *, arrival_rule: str = "flow_depth") -> Basis:
    """THE GENEROUS READING, and the other half of the band this module cannot close.

    The connection leaves the plot boundary at the shallowest property connection the
    guideline permits - 0.60 m of cover (G203-p19 sec 3.5) over an OD160 pipe (G203-p22
    Table 6) - runs the 2.5 m to the HCC at the property connection minimum of 3 %
    (G203-p18 Table 5, G203-p17 sec 3.2), and is a rider or lateral from there.

    Against BASIS_HCC this is 0.390 m more generous from the HCC onward. Run both; report the
    number of plots that change answer. That number is the size of the thing nobody has
    decided, and it is worth more than either answer on its own."""
    return _check_basis(Basis(
        name="BASIS_SHALLOW",
        outlet_depth_m=crit.PCS_MIN_COVER + crit.outside_diameter(crit.DN_TERTIARY),
        outlet_src="G203-p19 sec 3.5 cover over the G203-p22 Table 6 OD160 pipe",
        pcs_run_m=crit.HCC_OFFSET_M,
        s_pcs=crit.PCS_MIN_SLOPE,
        s_street=crit.LATERAL_MIN_SLOPE,
        s_max=crit.PCS_MAX_SLOPE,
        arrival_rule=arrival_rule), crit)


def basis_strict(crit: Criteria = DEFAULT, *, arrival_rule: str = "flow_depth") -> Basis:
    """THE PESSIMISTIC BOUND - the whole route at the property connection's 3 % minimum.

    Not a reading anybody should design to: it charges a 40 m street run the gradient of a
    house drain. It exists as the far end of the band, so a claim that "the answer does not
    depend on the connection model" can be tested rather than asserted."""
    return _check_basis(Basis(
        name="BASIS_STRICT",
        outlet_depth_m=crit.HCC_DEPTH_MIN,
        outlet_src="G203-p19 sec 3.4, with the PCS gradient charged over the whole route",
        pcs_run_m=float("inf"),
        s_pcs=crit.PCS_MIN_SLOPE,
        s_street=crit.PCS_MIN_SLOPE,
        s_max=crit.PCS_MAX_SLOPE,
        arrival_rule=arrival_rule), crit)


# ======================================================================================
# THE ARRIVAL ALLOWANCE
# ======================================================================================

def arrival_allowance(dn, rule: str = "flow_depth", crit: Criteria = DEFAULT):
    """How far ABOVE the chamber's invert the connection must arrive, m.

    Scalar in, scalar out; array in, array out. NaN in the bore propagates to NaN, and the
    caller turns that into WHY_NO_DN rather than into a guessed diameter.

    'flow_depth' is the default and it is the one with physics behind it: G203-p27 Table 10
    caps the depth of flow at 0.65 D to DN350 and 0.50 D above, so the design water surface
    sits that far above the invert, and a connection discharging below it is drowned at
    peak. The RULE is this module's assumption - G203 does not state it - but the NUMBER is
    the guideline's own."""
    if rule not in ARRIVAL_RULES:
        raise ConnectivityError(
            f"unknown arrival rule {rule!r}. Known: {', '.join(ARRIVAL_RULES)}.")
    scalar = np.isscalar(dn)
    d = np.atleast_1d(np.asarray(dn, dtype=float))
    if rule == "invert":
        out = np.zeros_like(d)
    else:
        out = np.full(d.shape, np.nan)
        ok = np.isfinite(d) & (d > 0)
        if ok.any():
            # keyed on the bore AS GIVEN. An earlier form cast to int() to key the cache,
            # which SILENTLY TRUNCATED a fractional bore - DN 315.4 was sized as DN 315 and
            # DN 350.9 crossed the G203-p27 Table 10 threshold in the wrong direction. A
            # bore is either a number this module can size or it is not; it is never
            # quietly rounded to one that is. Reviewed and fixed 2026-09-06.
            sizes = np.unique(d[ok])
            bore = {float(s): float(crit.internal_diameter(s)) for s in sizes}
            lim = {float(s): float(crit.dod_limit(s)) for s in sizes}
            vals = np.array([bore[float(v)] * (lim[float(v)] if rule == "flow_depth" else 1.0)
                             for v in d[ok]])
            out[ok] = vals
    return float(out[0]) if scalar else out


def dn_at_node(nodes: pd.DataFrame, reaches: pd.DataFrame) -> pd.Series:
    """The bore of the sewer a connection meets at each chamber, indexed by NODE_UID.

    The OUTGOING reach, because that is the pipe the connection's flow joins and the one
    whose water surface it must clear. An outfall has no outgoing reach, so the LARGEST
    incoming bore stands in - the conservative choice, and it is the pipe physically
    present in that chamber. A node with neither is left NaN and becomes WHY_NO_DN; it is
    never filled with a default, because a default bore makes the allowance constant
    across every row, which is inheritance row 22's fabrication arrived at politely."""
    for col, frame, nm in (("NODE_UID", nodes, "nodes"), ("US_NODE", reaches, "reaches"),
                           ("DS_NODE", reaches, "reaches"), ("DN", reaches, "reaches")):
        if col not in frame.columns:
            raise ConnectivityError(
                f"dn_at_node needs {col!r} on the {nm} frame. Without the receiving bore "
                "the 'flow_depth' and 'soffit' arrival rules cannot run, and the honest "
                "answer is to say so rather than to substitute a diameter.")
    r = reaches.assign(_DN=pd.to_numeric(reaches.DN, errors="coerce"))
    out = r.groupby(r.US_NODE.astype(str))["_DN"].max()
    inc = r.groupby(r.DS_NODE.astype(str))["_DN"].max()
    uid = nodes.NODE_UID.astype(str)
    res = uid.map(out)
    res = res.where(res.notna(), uid.map(inc))
    res.index = uid.values
    res.name = "DN"
    return res


# ======================================================================================
# THE CHECK - one plot, in scalars, so it can be read and hand-checked
# ======================================================================================

@dataclass(frozen=True)
class OnePlot:
    """One plot's answer, with every intermediate level kept. A verdict whose working is
    thrown away cannot be argued with."""
    can_conn: int
    why: str
    need_m: float
    outlet_inv: float
    arrive_inv: float
    required_inv: float
    allowance_m: float
    fall_m: float
    margin_m: float


def check_one(grd_plot_m: float, chamber_inv_m: float, route_m: float,
              dn: Optional[float] = None, *, basis: Optional[Basis] = None,
              crit: Criteria = DEFAULT) -> OnePlot:
    """THE WHOLE CHECK, for one plot, in scalars.

    The vectorised `check_connections()` computes exactly this and the self-test proves the
    two agree row for row. Keeping a scalar form is not duplication: it is the version a
    reviewer can follow with a calculator, and the version a test can build a failure mode
    in without constructing a frame."""
    b = _check_basis(basis or basis_hcc(crit), crit)
    if not np.isfinite(grd_plot_m):
        return OnePlot(0, WHY_NO_GRD, 0.0, *([float("nan")] * 6))
    if not np.isfinite(chamber_inv_m):
        return OnePlot(0, WHY_NO_INV, 0.0, *([float("nan")] * 6))
    if route_m is None or not np.isfinite(route_m):
        return OnePlot(0, WHY_NO_LEN, 0.0, *([float("nan")] * 6))
    allow = arrival_allowance(float("nan") if dn is None else dn, b.arrival_rule, crit)
    if not np.isfinite(allow):
        return OnePlot(0, WHY_NO_DN, 0.0, *([float("nan")] * 6))

    out_inv = float(b.outlet_invert(grd_plot_m))
    fall = float(b.fall(route_m))
    arrive = out_inv - fall
    required = float(chamber_inv_m) + float(allow)
    margin = arrive - required
    can = int(margin >= -b.tol_m)
    need = 0.0 if can else float(-margin)
    if can:
        why = ""
    elif out_inv - required < -b.tol_m:
        why = WHY_LEVEL          # no route, however short, would clear the chamber
    else:
        why = WHY_ROUTE          # it clears the chamber and then spends the clearance
    return OnePlot(can, why, need, out_inv, arrive, required, float(allow), fall, margin)


# ======================================================================================
# THE CHECK - every plot, vectorised
# ======================================================================================

def _align(value, idx: pd.Index, what: str) -> pd.Series:
    """Attach an explicitly-passed column to the connections frame's OWN index.

    A pandas Series carries its own labels and `np.asarray()` throws them away, so a
    lookup handed in keyed by NODE_UID - which is exactly the shape `dn_at_node()`
    returns - was re-attached BY POSITION and every plot silently got another plot's
    invert. Nothing failed, nothing was logged, and every level in the deliverable was
    wrong. A labelled input is either aligned or refused; it is never re-ordered in
    silence. Reviewed and fixed 2026-09-06."""
    if isinstance(value, pd.Series):
        if value.index.equals(idx):
            return value
        raise ConnectivityError(
            f"{what} was passed as a Series whose index does not match the connections "
            f"frame's ({len(value):,} labels against {len(idx):,}). Positional alignment "
            "here is how one plot gets another plot's level with nothing to show for it. "
            "Reindex it onto the connections frame's index, or pass a plain array in that "
            "frame's own row order.")
    arr = np.asarray(value)
    if arr.ndim == 0:
        arr = np.full(len(idx), arr.item())
    if len(arr) != len(idx):
        raise ConnectivityError(
            f"{what} has {len(arr):,} values against {len(idx):,} connections rows.")
    return pd.Series(arr, index=idx)


def _series(frame: pd.DataFrame, override, names: Sequence[str], what: str):
    """Take an explicit override, else the first of `names` present on the frame. Raises
    naming what to pass rather than returning an empty column - a check that cannot run is
    a failure (inheritance row 2)."""
    if override is not None:
        s = _align(override, frame.index, what)
    else:
        found = [n for n in names if n in frame.columns]
        if not found:
            raise ConnectivityError(
                f"cannot find {what}: none of {list(names)} is on the connections frame and "
                f"no explicit value was passed. Pass it, or add the column - guessing it is "
                "how W11a rejected 5,715 plots for nothing.")
        s = frame[found[0]]
    return pd.to_numeric(s, errors="coerce")


def check_connections(conn: pd.DataFrame, nodes: Optional[pd.DataFrame] = None, *,
                      crit: Criteria = DEFAULT, basis: Optional[Basis] = None,
                      chamber_inv=None, grd_plot=None, route_m=None, dn=None,
                      reaches: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Run the check over a whole connections frame. Returns a frame on `conn`'s index
    carrying CONTRACT_COLS + DIAG_COLS, and CONN_ID / OUT_NODE for joining.

    Inputs, each of which may be given explicitly or found on a frame:
      grd_plot       ground at the plot        -> `grd_plot=`, or conn.GRD_PLOT
      route_m        the connection's route    -> `route_m=`,  or conn.LEN_M, or geometry
      chamber_inv    the invert at OUT_NODE    -> `chamber_inv=`, or nodes.INV_M
      dn             the receiving bore        -> `dn=`, or dn_at_node(nodes, reaches)

    A NON-BLANK OUT_NODE THAT IS NOT IN `nodes` RAISES. That is a dangling reference and a
    contract violation, not a property of the plot; marking it CAN_CONN = 0 would file a
    wiring bug under an engineering finding, and 5,521 of those is how a real number gets
    buried."""
    b = _check_basis(basis or basis_hcc(crit), crit)
    n = len(conn)
    idx = conn.index
    if n == 0:
        empty = pd.DataFrame({"CONN_ID": pd.Series(dtype="object"),
                              "OUT_NODE": pd.Series(dtype="object"),
                              "CAN_CONN": pd.Series(dtype="int64"),
                              "CONN_WHY": pd.Series(dtype="object"),
                              "CONN_NEED": pd.Series(dtype="float64"),
                              **{c: pd.Series(dtype="float64") for c in DIAG_COLS}})
        # the basis travels with the EMPTY answer too. Without it report() printed "basis
        # unknown" beside "nan %", which reads as a broken run rather than as "no plots
        # were passed in". Fixed 2026-09-06.
        empty.attrs["basis"] = b
        empty.attrs["arrival_rule"] = b.arrival_rule
        empty.attrs["version"] = CONNECTIVITY_VERSION
        return empty

    # ---- the chamber each load unit enters at ------------------------------------------
    if "OUT_NODE" not in conn.columns:
        raise ConnectivityError(
            "the connections frame has no OUT_NODE. Concept rule 5 is that the connection "
            "runs TO A CHAMBER - without OUT_NODE there is no chamber and the check is the "
            "naive one this module exists to replace.")
    out_node = conn.OUT_NODE.astype(str).fillna("").str.strip()
    unassigned = (out_node == "") | out_node.str.lower().isin(("nan", "none"))

    # ---- the chamber invert -------------------------------------------------------------
    if chamber_inv is not None:
        inv = pd.to_numeric(_align(chamber_inv, idx, "the chamber invert"), errors="coerce")
    else:
        if nodes is None or "NODE_UID" not in nodes.columns or "INV_M" not in nodes.columns:
            raise ConnectivityError(
                "no chamber invert: pass `chamber_inv=`, or a `nodes` frame carrying "
                "NODE_UID and INV_M. This is the field W11b did not have at stage 4, which "
                "is why it published DRAIN_SHALLOW and recorded CAN_DRAIN as 'cannot run'.")
        lut = pd.Series(pd.to_numeric(nodes.INV_M, errors="coerce").values,
                        index=nodes.NODE_UID.astype(str).values)
        if lut.index.has_duplicates:
            # collapsing a duplicated key by keeping whichever row came first is a silent
            # choice between two inverts, and the one it makes is arbitrary. recheck()
            # already refuses a duplicated CONN_ID for this reason; the chamber key gets
            # the same treatment. Identical duplicates are harmless and are collapsed;
            # duplicates that DISAGREE are a contract violation on the layer's own key
            # (contract.NODES keys on NODE_UID) and they raise. Fixed 2026-09-06.
            spread = lut.groupby(level=0).nunique(dropna=False)
            clash = sorted(spread[spread > 1].index)
            if clash:
                raise ConnectivityError(
                    f"{len(clash):,} NODE_UID values appear more than once in the nodes "
                    f"frame with DIFFERENT INV_M, e.g. {clash[:5]}. contract.NODES keys on "
                    "NODE_UID, so this is a wiring bug; picking the first row would attach "
                    "one of two inverts to every plot on that chamber with nothing on the "
                    "deliverable to say which.")
            lut = lut[~lut.index.duplicated()]
        missing = sorted(set(out_node[~unassigned]) - set(lut.index))
        if missing:
            raise ConnectivityError(
                f"{len(missing):,} OUT_NODE values are not in the nodes frame, e.g. "
                f"{missing[:5]}. A dangling reference is a contract violation (H16: "
                "topology is written down), not a plot that cannot connect. Fix the "
                "wiring; do not let it arrive in the not-served schedule.")
        inv = out_node.map(lut)
        inv.index = idx

    # ---- ground at the plot, and the route ---------------------------------------------
    grd = _series(conn, grd_plot, ("GRD_PLOT", "GRD_M"), "the ground level at the plot")
    if route_m is not None:
        rte = pd.to_numeric(_align(route_m, idx, "the route length"), errors="coerce")
    elif "ROUTE_M" in conn.columns or "LEN_M" in conn.columns:
        rte = _series(conn, None, ("ROUTE_M", "LEN_M"), "the route length")
    elif getattr(conn, "geometry", None) is not None:
        rte = pd.to_numeric(conn.geometry.length, errors="coerce")
    else:
        raise ConnectivityError(
            "cannot find the route length: pass `route_m=`, or give the frame LEN_M, or "
            "give it geometry. THE ROUTE LENGTH IS THE WHOLE OF FAILURE MODE 3 - a check "
            "run without it is the level comparison this module exists to replace.")
    rte = rte.clip(lower=0.0)

    # ---- the receiving bore, and the allowance -----------------------------------------
    needs_bore = b.arrival_rule != "invert"
    if not needs_bore:
        # the loosest rule: the connection need only reach the chamber's own invert. No
        # bore is read, so no row can be refused for wanting one.
        bore = pd.Series(np.zeros(n), index=idx)
        allow = pd.Series(np.zeros(n), index=idx)
    else:
        if dn is not None:
            bore = pd.to_numeric(_align(dn, idx, "the receiving bore"), errors="coerce")
        elif nodes is not None and reaches is not None:
            lut_dn = dn_at_node(nodes, reaches)
            bore = out_node.map(lut_dn)
            bore.index = idx
        elif "DN" in conn.columns:
            bore = pd.to_numeric(conn.DN, errors="coerce")
        else:
            raise ConnectivityError(
                f"arrival rule {b.arrival_rule!r} needs the RECEIVING BORE at each chamber "
                "and none was supplied. Pass `dn=`, or `reaches=` beside `nodes=`, or use "
                "arrival_rule='invert' and say so on the deliverable. The module refuses to "
                "substitute a default diameter: a default makes ALLOW_M the same on every "
                "row, and a published column that is constant where it should vary is a "
                "fabrication (inheritance row 22).")
        allow = pd.Series(arrival_allowance(bore.to_numpy(dtype=float), b.arrival_rule,
                                            crit), index=idx)

    # ---- the arithmetic -----------------------------------------------------------------
    out_inv = pd.Series(b.outlet_invert(grd.to_numpy(dtype=float)), index=idx)
    fall = pd.Series(b.fall(rte.to_numpy(dtype=float)), index=idx)
    arrive = out_inv - fall
    required = inv + allow
    margin = arrive - required

    can = (margin >= -b.tol_m).to_numpy()
    why = np.where(can, "", np.where((out_inv - required).to_numpy() < -b.tol_m,
                                     WHY_LEVEL, WHY_ROUTE))
    # the four missing-input answers OVERRIDE the level verdict, in a fixed order, so a row
    # missing two things reports the one furthest upstream rather than whichever test ran
    # last. Each of them is a 0 with a reason and a need of 0.0 - the contract allows that
    # pair, and it is the honest one: an unknown is not a depth.
    #
    # THE BORE TEST IS ON THE ALLOWANCE, NOT ON THE BORE. Testing `isfinite(bore)` looks
    # equivalent and is not: DN = 0 and DN < 0 are FINITE and unusable, arrival_allowance()
    # returns NaN for both, and the row then fell through to the LEVEL branch and was
    # published as `route loses the fall` with ALLOW_M = NaN and CONN_NEED = 0.0 - a
    # fabricated engineering verdict standing in for a missing input, which is the exact
    # merge this vocabulary exists to prevent, and a verdict whose CONN_NEED is not the
    # remedy. DN = 0 is not hypothetical here: NAMA's own asset GIS carries N_DIAMETER = 0
    # on every built record. It also made this path disagree with check_one(), which tests
    # the allowance. Reviewed and fixed 2026-09-06; regression in
    # tests/test_connectivity_review.py.
    for mask, reason in ((~np.isfinite(allow.to_numpy(dtype=float)), WHY_NO_DN),
                         (~np.isfinite(rte.to_numpy(dtype=float)), WHY_NO_LEN),
                         (~np.isfinite(inv.to_numpy(dtype=float)), WHY_NO_INV),
                         (~np.isfinite(grd.to_numpy(dtype=float)), WHY_NO_GRD),
                         (unassigned.to_numpy(), WHY_NO_NODE)):
        m = np.asarray(mask, dtype=bool)
        can = np.where(m, False, can)
        why = np.where(m, reason, why)

    need = np.where(can, 0.0, np.maximum(-margin.to_numpy(dtype=float), 0.0))
    need = np.where(np.isfinite(need), need, 0.0)
    need = np.where(np.isin(why, WHY_IS_A_VERDICT), need, 0.0)

    with np.errstate(divide="ignore", invalid="ignore"):
        avail = (out_inv - required).to_numpy(dtype=float)
        r = rte.to_numpy(dtype=float)
        s_avl = np.where(r > 0, avail / np.where(r > 0, r, np.nan), np.nan)

    res = pd.DataFrame({
        "CONN_ID": (conn.CONN_ID.astype(str) if "CONN_ID" in conn.columns
                    else pd.Series(idx.astype(str), index=idx)),
        "OUT_NODE": out_node.values,
        "CAN_CONN": can.astype(np.int8),
        "CONN_WHY": why,
        "CONN_NEED": np.round(need, 3),
        "OUT_INV_M": np.round(out_inv.to_numpy(dtype=float), 3),
        "ARR_INV_M": np.round(arrive.to_numpy(dtype=float), 3),
        "REQ_INV_M": np.round(required.to_numpy(dtype=float), 3),
        "ALLOW_M": np.round(allow.to_numpy(dtype=float), 4),
        "ROUTE_M": np.round(r, 3),
        "FALL_M": np.round(fall.to_numpy(dtype=float), 3),
        "MARGIN_M": np.round(margin.to_numpy(dtype=float), 3),
        "S_AVL_PCT": np.round(s_avl * 100.0, 3),
        "CONN_LONG": (r > crit.PCS_MAX_LEN).astype(np.int8),
        "CONN_STEEP": (avail > b.s_max * r + b.tol_m).astype(np.int8),
    }, index=idx)
    res.attrs["basis"] = b
    res.attrs["arrival_rule"] = b.arrival_rule
    res.attrs["version"] = CONNECTIVITY_VERSION
    return res


# ======================================================================================
# THE NAIVE TEST - kept so the three failure modes can be SHOWN, never for publication
# ======================================================================================

def naive_can_connect(grd_plot_m, pipe_inv_at_nearest_point_m):
    """THE WRONG TEST. NEVER PUBLISH THIS. It is here to be disagreed with.

    Ground level at the plot centroid against the sewer invert at the nearest perpendicular
    point on a pipe. It is wrong three ways and each way is optimistic:

      1. it starts at GROUND, where the real connection starts at an invert a metre or more
         below it (G203-p19 sec 3.4);
      2. it aims at the nearest point on a PIPE, where the real connection runs to a
         CHAMBER - further, and usually upstream, so a higher invert;
      3. it spends no fall on the way, where the real connection loses its route length
         times its own minimum gradient (G203-p18 Table 5).

    `tests/test_connectivity.py` builds one plot for each mode and asserts this function
    says yes where `check_one()` says no. That is the only reason it exists."""
    return (np.asarray(grd_plot_m, dtype=float)
            > np.asarray(pipe_inv_at_nearest_point_m, dtype=float))


# ======================================================================================
# ADD, THEN TAKE AWAY - inheritance row 4
# ======================================================================================

def recheck(before: pd.DataFrame, after: pd.DataFrame) -> Dict[str, object]:
    """What the later pass TOOK AWAY. Inheritance row 4, applied to this module's own flag.

    A CAN_CONN = 0 raised against a stage-4 sewer is not a verdict on a stage-6 sewer. If
    the levelling stage lowers a run, the flags on that run must be cleared and THE NUMBER
    CLEARED MUST BE PUBLISHED - a flag that is only ever added is a decision that is never
    re-examined, which is the exact mechanism that put 69 stations in a deliverable.

    Returns cleared / raised counts, the ids of each, and the depth actually recovered."""
    for nm, f in (("before", before), ("after", after)):
        for c in ("CONN_ID", "CAN_CONN", "CONN_NEED"):
            if c not in f.columns:
                raise ConnectivityError(f"recheck: the {nm} frame has no {c}")
    for nm, f in (("before", before), ("after", after)):
        ids = f.CONN_ID.astype(str)
        if ids.duplicated().any():
            dup = sorted(set(ids[ids.duplicated()]))
            raise ConnectivityError(
                f"recheck: the {nm} frame has {len(dup):,} duplicated CONN_ID values, e.g. "
                f"{dup[:5]}. One load unit is one row (contract.CONNECTIONS keys on "
                "CONN_ID); a duplicate makes 'how many were cleared' unanswerable, which "
                "is the whole point of this function.")
    a_all = before.set_index(before.CONN_ID.astype(str))
    z_all = after.set_index(after.CONN_ID.astype(str))
    common = a_all.index.intersection(z_all.index)
    # WHAT IS NOT IN BOTH FRAMES IS NAMED, NEVER DROPPED. Comparing only the intersection
    # and publishing "2 failing -> 1 failing" while three load units vanished between the
    # two runs is a silent drop (inheritance row 12), and it is the failure this function
    # exists to prevent, committed by the function itself. Fixed 2026-09-06.
    gone = a_all.index.difference(z_all.index)
    new = z_all.index.difference(a_all.index)
    a, z = a_all.loc[common], z_all.loc[common]
    was = pd.to_numeric(a.CAN_CONN, errors="coerce").fillna(0).astype(int)
    now = pd.to_numeric(z.CAN_CONN, errors="coerce").fillna(0).astype(int)
    cleared = common[(was == 0) & (now == 1)]
    raised = common[(was == 1) & (now == 0)]

    # A ROW THAT WAS A VERDICT AND IS NOW AN UNKNOWN HAS NOT RECOVERED ANY DEPTH; it has
    # lost an input, and its CONN_NEED went to 0.0 because an unknown is not a depth. Only
    # rows that are a LEVEL answer at both ends can contribute to the recovered depth, and
    # only where CONN_WHY is published at both ends can that be told apart at all - where
    # it is not, the figure is reported as unqualified and says so.
    def _verdictish(f: pd.DataFrame) -> pd.Series:
        if "CONN_WHY" not in f.columns:
            return pd.Series(True, index=f.index)
        w = f.CONN_WHY.astype(str)
        return (w == "") | w.isin(WHY_IS_A_VERDICT)
    qualified = bool("CONN_WHY" in a.columns and "CONN_WHY" in z.columns)
    real = _verdictish(a) & _verdictish(z)
    d_need = (pd.to_numeric(a.CONN_NEED, errors="coerce").fillna(0.0)
              - pd.to_numeric(z.CONN_NEED, errors="coerce").fillna(0.0)).where(real, 0.0)
    # a flag cleared because the MISSING INPUT ARRIVED is not a flag a later pass removed
    became_testable = int((~_verdictish(a) & (now == 1)).sum()) if qualified else 0

    line = (f"connectability: {int((was == 0).sum()):,} failing -> "
            f"{int((now == 0).sum()):,} failing "
            f"({len(cleared):,} cleared, {len(raised):,} newly raised)")
    if len(gone) or len(new):
        line += (f"; {len(gone):,} load units present before and GONE after, "
                 f"{len(new):,} new - not comparable, named in only_before_ids / "
                 "only_after_ids")
    return {
        "n_compared": int(len(common)),
        "n_before": int(len(a_all)),
        "n_after": int(len(z_all)),
        "n_only_before": int(len(gone)),
        "n_only_after": int(len(new)),
        "only_before_ids": [str(i) for i in gone[:200]],
        "only_after_ids": [str(i) for i in new[:200]],
        "n_before_fail": int((was == 0).sum()),
        "n_after_fail": int((now == 0).sum()),
        "n_cleared": int(len(cleared)),
        "n_raised": int(len(raised)),
        "n_became_testable": became_testable,
        "cleared_ids": [str(i) for i in cleared[:200]],
        "raised_ids": [str(i) for i in raised[:200]],
        "depth_recovered_m": float(d_need[d_need > 0].sum()),
        "depth_recovered_qualified": qualified,
        "line": line,
    }


# ======================================================================================
# WHAT IT WOULD TAKE - the other answer, when the answer is not "dig deeper"
# ======================================================================================

def best_of(candidates: pd.DataFrame, nodes: Optional[pd.DataFrame] = None, *,
            crit: Criteria = DEFAULT, basis: Optional[Basis] = None,
            **kw) -> pd.DataFrame:
    """Given SEVERAL candidate chambers per plot, pick the one that connects - or, if none
    does, the one that needs the least extra depth.

    `candidates` is long form: one row per (plot, candidate chamber), carrying CONN_ID,
    OUT_NODE and the route length to THAT chamber. Everything else is as
    `check_connections()`.

    This exists because "sewer 0.83 m deeper" is not always the right advice. Sometimes the
    plot is on the wrong side of a junction and the chamber 40 m the other way works today.
    A schedule that only ever says "dig deeper" costs money that a re-assignment would not.
    The spatial work of proposing candidates belongs in the stage that has the geometry;
    this only scores them."""
    scored = check_connections(candidates, nodes, crit=crit, basis=basis, **kw)
    scored = scored.assign(_ID=scored.CONN_ID.astype(str))
    scored = scored.sort_values(["_ID", "CAN_CONN", "CONN_NEED", "ROUTE_M"],
                                ascending=[True, False, True, True])
    best = scored.groupby("_ID", sort=False).head(1).drop(columns=["_ID"])
    best.attrs.update(scored.attrs)
    return best


# ======================================================================================
# REPORTING - the funnel, the band, and the schedule
# ======================================================================================

def summary(res: pd.DataFrame) -> Dict[str, object]:
    """Every number a stage should publish about connectability, computed ONCE.

    Inheritance row 10 - one published quantity, one function. Seven station counts reached
    circulation in W10 because each was computed where it was printed."""
    n = len(res)
    can = pd.to_numeric(res.CAN_CONN, errors="coerce").fillna(0).astype(int)
    why = res.CONN_WHY.astype(str)
    verdict_fail = (can == 0) & why.isin(WHY_IS_A_VERDICT)
    cannot_run = (can == 0) & ~why.isin(WHY_IS_A_VERDICT) & (why != "")
    need = pd.to_numeric(res.CONN_NEED, errors="coerce").fillna(0.0)
    out: Dict[str, object] = {
        "n": n,
        "n_can": int((can == 1).sum()),
        "n_cannot": int((can == 0).sum()),
        "n_verdict_fail": int(verdict_fail.sum()),
        "n_cannot_run": int(cannot_run.sum()),
        "pct_can": (float((can == 1).sum()) / n * 100.0) if n else float("nan"),
        "need_max_m": float(need[verdict_fail].max()) if verdict_fail.any() else 0.0,
        "need_median_m": (float(need[verdict_fail].median()) if verdict_fail.any() else 0.0),
        "need_p90_m": (float(need[verdict_fail].quantile(0.9)) if verdict_fail.any()
                       else 0.0),
        "by_reason": {k: int(v) for k, v in why[can == 0].value_counts().items()},
        "n_long": int(pd.to_numeric(res.CONN_LONG, errors="coerce").fillna(0).sum()),
        "n_steep": int(pd.to_numeric(res.CONN_STEEP, errors="coerce").fillna(0).sum()),
    }
    b = res.attrs.get("basis")
    out["basis"] = b.name if b is not None else ""
    return out


def sensitivity(conn: pd.DataFrame, nodes: Optional[pd.DataFrame] = None, *,
                bases: Optional[Sequence[Basis]] = None, crit: Criteria = DEFAULT,
                **kw) -> pd.DataFrame:
    """Run the check on several bases and report how many plots CHANGE ANSWER.

    The depth at which a connection leaves a plot is not settled by the guideline and it
    moves the answer. That movement is a published number here, not a modelling choice
    buried in a default argument. One row per basis, plus `n_flip_vs_first`."""
    bs = list(bases) if bases else [basis_hcc(crit), basis_shallow(crit),
                                    basis_strict(crit)]
    rows: List[Dict[str, object]] = []
    ref: Optional[np.ndarray] = None
    for b in bs:
        r = check_connections(conn, nodes, crit=crit, basis=b, **kw)
        s = summary(r)
        cur = pd.to_numeric(r.CAN_CONN, errors="coerce").fillna(0).astype(int).to_numpy()
        if ref is None:
            ref = cur
        rows.append({"basis": b.name, "outlet_depth_m": b.outlet_depth_m,
                     "n_can": s["n_can"], "n_cannot": s["n_cannot"],
                     "n_verdict_fail": s["n_verdict_fail"],
                     "need_max_m": s["need_max_m"],
                     "n_flip_vs_first": int((cur != ref).sum())})
    return pd.DataFrame(rows)


def schedule(res: pd.DataFrame, conn: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """The not-connectable schedule: every failing plot, its reason, its size and the
    chamber the size applies to. Sorted worst first, because a list nobody can rank is a
    list nobody acts on."""
    can = pd.to_numeric(res.CAN_CONN, errors="coerce").fillna(0).astype(int)
    bad = res[can == 0].copy()
    keep = ["CONN_ID", "OUT_NODE", "CONN_WHY", "CONN_NEED", "ROUTE_M", "MARGIN_M",
            "OUT_INV_M", "REQ_INV_M"]
    bad = bad[[c for c in keep if c in bad.columns]]
    if conn is not None and "PLOT_ID" in conn.columns and "CONN_ID" in conn.columns:
        bad = bad.merge(conn[["CONN_ID", "PLOT_ID"]].astype(str).drop_duplicates("CONN_ID"),
                        on="CONN_ID", how="left")
    return bad.sort_values(["CONN_NEED", "CONN_ID"], ascending=[False, True])


def report(res: pd.DataFrame, crit: Criteria = DEFAULT) -> str:
    """The markdown a stage pastes into its own run report. Every figure from
    `summary()`, so the report and the layer cannot disagree."""
    s = summary(res)
    b = res.attrs.get("basis")
    lines = [
        "### Plot connectability",
        "",
        f"`{CONNECTIVITY_VERSION}` - {b.describe() if b is not None else 'basis unknown'}",
        "",
        (f"**No plots were passed to the check.** An empty answer is not a result: "
         f"nothing here says anything about the network." if s["n"] == 0 else
         f"**{s['n_can']:,} of {s['n']:,} plots ({s['pct_can']:.1f} %) can reach their "
        f"chamber on gravity.** House connections are NOT designed at concept "
        f"(`criteria.CONCEPT_OFF['house_connections']`); this is the one gravity question "
        f"asked of a plot."),
        "",
        f"- **{s['n_verdict_fail']:,} cannot** - a level verdict, each with the depth it "
        f"would take. Worst {s['need_max_m']:.2f} m, median {s['need_median_m']:.2f} m, "
        f"p90 {s['need_p90_m']:.2f} m.",
        f"- **{s['n_cannot_run']:,} could not be tested** - a missing input, not a "
        f"finding. Inheritance row 2: a check that cannot run is a FAILURE, not a blank, "
        f"and it is counted separately so it is never reported as an engineering result.",
        f"- {s['n_long']:,} routes exceed the {crit.PCS_MAX_LEN:g} m G203-p18 maintainable "
        f"length and need an intermediate manhole; {s['n_steep']:,} have more fall "
        f"available than the {crit.PCS_MAX_SLOPE * 100:g} % G203-p18 Table 5 maximum and "
        f"take the surplus at a drop.",
        "",
        "| Reason | Plots |",
        "|---|---|",
    ]
    for k, v in sorted(s["by_reason"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v:,} |")
    return "\n".join(lines)


# ======================================================================================
# THE ASSUMPTIONS REGISTER - everything here with no page behind it
# ======================================================================================

ASSUMPTIONS: Dict[str, Tuple[str, str]] = {
    "OUTLET_DEPTH": (
        "The connection leaves the plot at the HCC's minimum depth, 1.2 m "
        "(criteria.HCC_DEPTH_MIN, G203-p19 sec 3.4). THE PAGE GIVES A RANGE, 1.2 - 2.0 m, "
        "'depending on the size of the plot', and does NOT say a connection may not be "
        "shallower where the sewer is shallow. Taking the bottom of the stated range is "
        "this module's choice, and it is the conservative one.",
        "PENDING: the engineer's ruling, or NWS's standard house-connection detail. "
        "basis_shallow() is the other defensible reading and sensitivity() reports how "
        "many plots move between them - do not close this without that number."),
    "ARRIVAL_ALLOWANCE_RULE": (
        "A connection must arrive ABOVE the design flow surface of the sewer it joins, "
        "which G203-p27 Table 10 puts at 0.65 D to DN350 and 0.50 D above. G203 STATES NO "
        "SUCH RULE - it gives the depth of flow as a capacity criterion, not as a "
        "connection level. The rule is ours; only the number is the guideline's. A "
        "connection arriving below it is drowned at peak flow and backs up into the plot.",
        "PENDING: NWS's standard manhole connection detail, which will say whether they "
        "bench to soffit, to the flow line, or to the invert. arrival_rule='soffit' and "
        "'invert' are the other two readings and both are one argument away."),
    "PCS_RUN_LENGTH": (
        "In basis_shallow(), the property connection's 3 % minimum is charged over the "
        "first 2.5 m of the route (criteria.HCC_OFFSET_M, G203-p17 sec 3.2) and the "
        "rider / lateral 1 % over the rest. The route as measured usually starts at the "
        "PLOT CENTROID, not at the boundary, so some of that first stretch is private "
        "drainage inside the plot, which G203 does not govern at all.",
        "PENDING: nothing external. It closes when the connection geometry starts at the "
        "plot boundary rather than the centroid, which is a stage-4 question."),
    "MINIMUM_GRADIENT_IS_THE_TEST": (
        "The check uses the MINIMUM legal gradient, which loses the least fall and is "
        "therefore the most generous case the guideline permits. This is a deliberate "
        "choice of which bound to publish, not an oversight: a plot that fails here fails "
        "at every legal gradient, so a 0 is firm. A 1 is NOT a guarantee that a "
        "constructable connection exists - it is a guarantee that no gradient rule "
        "forbids one.",
        "It does not close. It is the difference between a concept check and a design, "
        "and criteria.CONCEPT_OFF['house_connections'] is where the design lives."),
    "CONN_LEVEL_TOL_M": (
        f"{CONN_LEVEL_TOL_M} m levelling tolerance, so a plot clearing its chamber by a "
        "float rounding error is not published as a failure. STRUCTURAL, not a design "
        "value, and deliberately an order of magnitude below G203-p29's 20 mm CONSTRUCTION "
        "tolerance, which is what the contractor may deviate by and is not this module's "
        "to spend on the design's behalf.",
        "It does not close; it is a numerical guard."),
}


def assumptions_banner() -> str:
    """Printed beside criteria.tau_banner() and criteria.concept_banner() on any
    deliverable carrying CAN_CONN. A reader who does not know which reading produced the
    number cannot tell a finding from a modelling choice."""
    return ("PLOT CONNECTABILITY - " + CONNECTIVITY_VERSION + ". The check is a CONCEPT "
            "check: house connections are not designed (criteria.CONCEPT_OFF["
            "'house_connections']). " + str(len(ASSUMPTIONS)) + " assumptions carry it, "
            "and the two that move the answer are the depth a connection leaves a plot at "
            "and what it must arrive above at the chamber. Both are in "
            "connectivity.ASSUMPTIONS with what would settle them; sensitivity() reports "
            "how many plots move between the readings.")


# ======================================================================================
# SELF-TEST
# ======================================================================================

def _self_test(verbose: bool = True) -> None:      # pragma: no cover - run as __main__
    """Proves the guards BITE. A check nobody has seen fail is a check nobody knows is
    wired in."""
    C = DEFAULT
    b_hcc = basis_hcc(C)
    b_sh = basis_shallow(C)

    # ---- the basis is legal, and an illegal one is refused --------------------------
    assert b_hcc.outlet_depth_m == C.HCC_DEPTH_MIN
    assert b_sh.outlet_depth_m == C.PCS_MIN_COVER + C.outside_diameter(C.DN_TERTIARY)
    # the two readings differ by 0.390 m from the HCC on - the band nobody has closed
    at_hcc = ((b_hcc.outlet_depth_m + b_hcc.fall(C.HCC_OFFSET_M))
              - (b_sh.outlet_depth_m + b_sh.fall(C.HCC_OFFSET_M)))
    assert abs(at_hcc - 0.390) < 1e-9, at_hcc
    for bad, needle in (
            (dict(outlet_depth_m=0.10), "shallower than"),
            (dict(s_street=0.0), "outside the G203-p18 Table 5 range"),
            (dict(s_street=0.5), "outside the G203-p18 Table 5 range"),
            (dict(arrival_rule="whatever"), "unknown arrival rule")):
        try:
            _check_basis(Basis(**{**b_hcc.__dict__, **bad}), C)
        except ConnectivityError as e:
            assert needle in str(e), (bad, str(e))
        else:                                                     # pragma: no cover
            raise AssertionError(f"a basis with {bad} was accepted")

    # ---- the allowance VARIES with the bore, which is the whole point ----------------
    a200 = arrival_allowance(200, "flow_depth", C)
    a1200 = arrival_allowance(1200, "flow_depth", C)
    assert abs(a200 - C.dod_limit(200) * C.internal_diameter(200)) < 1e-12
    assert a1200 > a200 * 4, (a200, a1200)
    assert arrival_allowance(200, "invert", C) == 0.0
    assert arrival_allowance(200, "soffit", C) == C.internal_diameter(200)
    assert not np.isfinite(arrival_allowance(float("nan"), "flow_depth", C))
    arr = arrival_allowance(np.array([200.0, 1200.0, np.nan]), "flow_depth", C)
    assert len(set(np.round(arr[:2], 6))) == 2, "the allowance must not be constant"

    # =================================================================================
    # THE THREE FAILURE MODES OF THE NAIVE TEST. Each is a plot where the naive answer
    # is YES and the real answer is NO, and each fails for a DIFFERENT one of the three
    # reasons. Every level below is chosen by hand so the arithmetic can be followed.
    # =================================================================================

    # MODE 1 - IT LEAVES BELOW GROUND, NOT AT IT.
    # Ground 100.00. Chamber invert 99.20 on a DN200, allowance 0.122 -> must arrive at
    # 99.322. Route 0 m, so no fall is lost and the route plays no part. Ground 100.00 is
    # above 99.322, so the naive test says yes. The outlet is at 100.00 - 1.20 = 98.80,
    # which is 0.522 m BELOW what it must arrive at.
    m1 = check_one(100.00, 99.20, 0.0, 200, basis=b_hcc, crit=C)
    assert naive_can_connect(100.00, 99.20)
    assert m1.can_conn == 0 and m1.why == WHY_LEVEL, m1
    assert abs(m1.need_m - 0.522) < 5e-4, m1.need_m

    # MODE 2 - IT RUNS TO A CHAMBER, NOT TO THE NEAREST POINT ON A PIPE.
    # Same plot, ground 100.00. The nearest point on the sewer is 5 m away at invert
    # 97.80; the CHAMBER it must actually run to is 55 m away, UPSTREAM, at invert 98.30
    # (the sewer rises 0.50 m over the 50 m between them, about 1 %). Against the nearest
    # point the plot connects with 0.83 m to spare. Against the chamber it is 0.17 m short,
    # and BOTH halves of the difference are real: the route is 50 m longer AND the invert
    # is 0.50 m higher. This is the mode a perpendicular-distance test cannot see at all.
    near = check_one(100.00, 97.80, 5.0, 200, basis=b_hcc, crit=C)
    real = check_one(100.00, 98.30, 55.0, 200, basis=b_hcc, crit=C)
    assert naive_can_connect(100.00, 97.80)
    assert near.can_conn == 1, near
    assert real.can_conn == 0, real
    assert real.why == WHY_ROUTE, real
    assert abs(real.need_m - 0.172) < 5e-4, real.need_m

    # MODE 3 - IT LOSES FALL OVER ITS OWN LENGTH.
    # Ground 100.00, chamber invert 98.50 on a DN200 -> must arrive at 98.622. The outlet
    # at 98.80 is ABOVE that, so a pure level comparison says yes. But the route is 40 m
    # and the rider/lateral minimum is 1 %, so 0.40 m of fall is spent and the connection
    # arrives at 98.40 - 0.222 m short.
    m3 = check_one(100.00, 98.50, 40.0, 200, basis=b_hcc, crit=C)
    assert m3.outlet_inv > m3.required_inv, m3          # the level comparison says yes
    assert m3.can_conn == 0 and m3.why == WHY_ROUTE, m3
    assert abs(m3.fall_m - 0.40) < 1e-9, m3.fall_m
    assert abs(m3.need_m - 0.222) < 5e-4, m3.need_m
    # and it connects once the sewer is that much deeper - the size is the remedy
    fixed = check_one(100.00, 98.50 - m3.need_m, 40.0, 200, basis=b_hcc, crit=C)
    assert fixed.can_conn == 1, fixed

    # a plot that genuinely connects carries no reason and needs no depth
    ok = check_one(100.00, 97.00, 40.0, 200, basis=b_hcc, crit=C)
    assert ok.can_conn == 1 and ok.why == "" and ok.need_m == 0.0, ok

    # ---- every reason in the vocabulary is REACHABLE ---------------------------------
    assert check_one(float("nan"), 97.0, 10.0, 200, crit=C).why == WHY_NO_GRD
    assert check_one(100.0, float("nan"), 10.0, 200, crit=C).why == WHY_NO_INV
    assert check_one(100.0, 97.0, float("nan"), 200, crit=C).why == WHY_NO_LEN
    assert check_one(100.0, 97.0, 10.0, None, crit=C).why == WHY_NO_DN

    # =================================================================================
    # the frame version, and it must agree with the scalar version row for row
    # =================================================================================
    rng = np.random.default_rng(20260906)
    n = 400
    grd = 100.0 + rng.normal(0, 3, n)
    inv = grd - rng.uniform(0.5, 4.0, n)
    rte = rng.uniform(0, 120, n)
    dns = rng.choice([200, 300, 400, 900], n)
    conn = pd.DataFrame({
        "CONN_ID": [f"C{i:04d}" for i in range(n)],
        "PLOT_ID": [f"P{i:04d}" for i in range(n)],
        "OUT_NODE": [f"N{i % 40:03d}" for i in range(n)],
        "GRD_PLOT": grd, "LEN_M": rte, "DN": dns})
    nodes = pd.DataFrame({"NODE_UID": [f"N{i:03d}" for i in range(40)],
                          "INV_M": [0.0] * 40})
    res = check_connections(conn, chamber_inv=inv, crit=C, basis=b_hcc)
    assert list(res.columns[:5]) == ["CONN_ID", "OUT_NODE", *CONTRACT_COLS]
    for i in (0, 1, 7, 99, 250, 399):
        one = check_one(grd[i], inv[i], rte[i], dns[i], basis=b_hcc, crit=C)
        assert int(res.CAN_CONN.iloc[i]) == one.can_conn, i
        assert res.CONN_WHY.iloc[i] == one.why, i
        assert abs(float(res.CONN_NEED.iloc[i]) - round(one.need_m, 3)) < 2e-3, i
    # the allowance is not constant - inheritance row 22, on this module's own output
    assert res.ALLOW_M.nunique() > 1, "ALLOW_M is constant; the bore is not being read"
    # both verdicts occur, so CONN_WHY is not constant either
    s = summary(res)
    assert s["n_can"] + s["n_cannot"] == n
    assert s["n_verdict_fail"] > 0 and s["n_can"] > 0, s
    assert len([k for k in s["by_reason"] if k in WHY_IS_A_VERDICT]) == 2, s["by_reason"]

    # ---- the contract's own cross-field rules hold on this output --------------------
    can1 = res.CAN_CONN == 1
    assert (res.loc[can1, "CONN_WHY"] == "").all(), "a connectable plot carries a reason"
    assert (res.loc[can1, "CONN_NEED"] == 0.0).all(), "a connectable plot needs depth"
    assert (res.loc[~can1, "CONN_WHY"] != "").all(), "a failure with no reason"
    assert (res.CONN_NEED >= 0).all()

    # ---- a dangling OUT_NODE RAISES rather than becoming a not-served plot -----------
    try:
        check_connections(conn, nodes.iloc[:5], crit=C, basis=b_hcc, dn=dns)
    except ConnectivityError as e:
        assert "not in the nodes frame" in str(e)
    else:                                                          # pragma: no cover
        raise AssertionError("a dangling OUT_NODE was accepted")

    # ---- an unassigned plot is a reason, not a crash ---------------------------------
    c2 = conn.copy()
    c2.loc[c2.index[:3], "OUT_NODE"] = ""
    r2 = check_connections(c2, chamber_inv=inv, crit=C, basis=b_hcc)
    assert (r2.CONN_WHY.iloc[:3] == WHY_NO_NODE).all()
    assert (r2.CAN_CONN.iloc[:3] == 0).all()
    assert (r2.CONN_NEED.iloc[:3] == 0.0).all(), "an unknown is not a depth"

    # ---- flow_depth with no bore REFUSES rather than defaulting a diameter -----------
    try:
        check_connections(conn.drop(columns=["DN"]), chamber_inv=inv, crit=C, basis=b_hcc)
    except ConnectivityError as e:
        assert "RECEIVING BORE" in str(e) and "fabrication" in str(e)
    else:                                                          # pragma: no cover
        raise AssertionError("a missing bore was defaulted")
    # ... and 'invert' is the escape that needs none
    r3 = check_connections(conn.drop(columns=["DN"]), chamber_inv=inv, crit=C,
                           basis=basis_hcc(C, arrival_rule="invert"))
    assert (r3.ALLOW_M == 0.0).all()
    assert int(r3.CAN_CONN.sum()) >= int(res.CAN_CONN.sum()), "'invert' must be looser"

    # ---- dn_at_node reads the OUTGOING reach, and falls back to the incoming ---------
    rc = pd.DataFrame({"US_NODE": ["N000", "N001"], "DS_NODE": ["N001", "N002"],
                       "DN": [200, 300]})
    nd = pd.DataFrame({"NODE_UID": ["N000", "N001", "N002", "N003"], "INV_M": [0.0] * 4})
    got = dn_at_node(nd, rc)
    assert got["N000"] == 200 and got["N001"] == 300, dict(got)
    assert got["N002"] == 300, "an outfall takes its incoming bore"
    assert not np.isfinite(got["N003"]), "an isolated node is NaN, never a default"

    # ---- ADD, THEN TAKE AWAY: a deeper sewer clears flags, and the count is published -
    deeper = check_connections(conn, chamber_inv=inv - 2.0, crit=C, basis=b_hcc)
    rc_ = recheck(res, deeper)
    assert rc_["n_cleared"] > 0 and rc_["n_after_fail"] < rc_["n_before_fail"], rc_
    assert rc_["n_raised"] == 0
    assert rc_["depth_recovered_m"] > 0
    assert "cleared" in rc_["line"]

    # ---- the band nobody has closed is a NUMBER ---------------------------------------
    sens = sensitivity(conn, chamber_inv=inv, crit=C)
    assert list(sens.basis) == ["BASIS_HCC", "BASIS_SHALLOW", "BASIS_STRICT"]
    assert sens.n_flip_vs_first.iloc[1] > 0, "the two readings must differ on this data"
    assert sens.n_can.iloc[1] >= sens.n_can.iloc[0], "shallow must be the generous one"
    assert sens.n_can.iloc[2] <= sens.n_can.iloc[0], "strict must be the harsh one"

    # ---- best_of picks a chamber that works over one that does not --------------------
    cand = pd.DataFrame({
        "CONN_ID": ["C0", "C0", "C1", "C1"],
        "OUT_NODE": ["A", "B", "A", "B"],
        "GRD_PLOT": [100.0, 100.0, 100.0, 100.0],
        "LEN_M": [10.0, 60.0, 10.0, 60.0],
        "DN": [200, 200, 200, 200]})
    bo = best_of(cand, chamber_inv=np.array([99.5, 96.0, 99.5, 99.4]), crit=C, basis=b_hcc)
    assert len(bo) == 2
    assert bo.set_index("CONN_ID").loc["C0", "OUT_NODE"] == "B", "the working one wins"
    assert int(bo.set_index("CONN_ID").loc["C1", "CAN_CONN"]) == 0

    # ---- the schedule ranks by size, and the report reads from summary() --------------
    sch = schedule(res, conn)
    assert len(sch) == s["n_cannot"]
    assert sch.CONN_NEED.is_monotonic_decreasing
    assert "PLOT_ID" in sch.columns
    txt = report(res, C)
    assert f"{s['n_can']:,}" in txt and "cannot run is a FAILURE" in txt
    assert len(ASSUMPTIONS) >= 5 and "PENDING" in ASSUMPTIONS["OUTLET_DEPTH"][1]
    assert "house_connections" in assumptions_banner()

    # ---- an empty frame gives an empty answer with the right columns, not a crash -----
    e = check_connections(conn.iloc[:0], chamber_inv=np.array([]), crit=C, basis=b_hcc)
    assert len(e) == 0 and set(CONTRACT_COLS).issubset(e.columns)

    if verbose:
        print(f"{CONNECTIVITY_VERSION}: self-test PASSED")
        print()
        print(b_hcc.describe())
        print(b_sh.describe())
        print(f"  the two readings differ by {at_hcc:.3f} m from the HCC on - "
              f"{int(sens.n_flip_vs_first.iloc[1]):,} of {n:,} synthetic plots change "
              f"answer between them")
        print()
        print(f"  arrival allowance, 'flow_depth' (G203-p27 Table 10): "
              + ", ".join(f"DN{d} {arrival_allowance(d, 'flow_depth', C):.3f} m"
                          for d in (200, 315, 400, 900, 1200)))
        print()
        print(report(res, C))
        print()
        print(sens.to_string(index=False))
        print()
        print(assumptions_banner())


if __name__ == "__main__":          # pragma: no cover
    _self_test()
