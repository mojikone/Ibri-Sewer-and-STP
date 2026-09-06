"""Stage 4's two published defects, written as tests so they cannot come back.

BOTH OF THESE SHIPPED IN THE FIRST FULL RUN.

  1. THE CLEARANCE CONTRADICTION.  `criteria.MH_SNAP_M` = 3.0 m is one constant wearing two
     hats: the radius at which `s1_roads` merged positions into a single node ("noding at
     MH_SNAP_M = 3 m") and the minimum clear distance between two chambers.  Stage 4 then
     published three pairs of chambers 0.46, 1.86 and 2.02 m apart - closer than the radius
     that declares two positions to be one node - and its own `verify()` failed on them.
     Every one was the two ends of a corridor SHORTER than the clearance: `split_positions`
     keeps every interior chamber 3 m clear within an arc but always keeps both arc ends, so
     an arc under 3 m long gets a chamber at each end.  Eight arcs of 13,102 are like that
     and there is no such pair that is not one of them.

  2. THE INLET ANGLE MEASURED ON THE WRONG NETWORK.  G203-p30, verbatim: "No inlet pipe at
     manholes shall have an angle less than 90 deg to the direction of flow."  Stage 4
     measured it BEFORE the prune, so 2,324 chambers carried an angle derived from a pipe
     that is not in the published layer and 145 carried a SWEPT_CH flag - a priced chamber
     detail each - for an inlet the prune had deleted.  Separately, INLET_DEG was rounded to
     1 decimal while INLET_FLAG was computed from the raw value, so 85 chambers published
     "90.0" beside a raised flag: the number said compliant and the flag said not.

These tests read the PUBLISHED GeoPackage and re-derive both from it, because the whole
architecture of this project's auditing is that a claim is checked against the artefact
anybody else will open, never against something held in memory.

WHAT THEY DO NOT ASSERT.  They do NOT assert that the inlet-angle count is zero.  It is not
zero and it will not be: not one of the breaches can be designed away by moving a chamber -
the angle is the angle at which two mapped streets meet, or one corridor turning back on
itself, and a chamber can only be moved ALONG the corridor it stands on.  What is asserted
is that the number is HONEST: measured on the published pipes, split by cause, consistent
between the column and the flag, and priced.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from conftest import layer, layer_names


# ==========================================================================================
# 1.  THE MINIMUM CLEARANCE
# ==========================================================================================

@pytest.mark.published
def test_no_two_chambers_stand_inside_the_minimum_clearance(chambers, crit):
    """The defect itself. Two chambers closer than the node-merge radius ARE one structure.

    This is deliberately the same test stage 4's own `verify()` makes, run from outside it,
    because the failure mode this project keeps paying for is a stage that agrees with
    itself and with nothing else.
    """
    import shapely
    from shapely import STRtree

    pts = shapely.points(chambers.X.values, chambers.Y.values)
    a, b = STRtree(pts).query(pts, predicate="dwithin", distance=crit.MH_SNAP_M - 1e-6)
    m = a < b
    n = int(m.sum())
    if n:
        d = np.hypot(chambers.X.values[a[m]] - chambers.X.values[b[m]],
                     chambers.Y.values[a[m]] - chambers.Y.values[b[m]])
        worst = pd.DataFrame({"A": chambers.NODE_UID.values[a[m]],
                              "B": chambers.NODE_UID.values[b[m]],
                              "gap_m": d.round(3)}).nsmallest(5, "gap_m")
        print(f"\n    [clearance] worst pairs:\n{worst.to_string(index=False)}")
    assert n == 0, (
        f"{n} pair(s) of chambers stand closer than criteria.MH_SNAP_M = "
        f"{crit.MH_SNAP_M:g} m, which is the radius at which s1_roads merged two positions "
        f"into ONE node. Two chambers inside it are one structure - contract them in the "
        f"placement, do not widen the check")


@pytest.mark.published
def test_no_reach_is_shorter_than_the_clearance_between_its_two_chambers(segments, crit):
    """The CAUSE, not the symptom: a pipe shorter than the clearance joins two chambers
    that are one structure. Catching it here says WHY the pair exists."""
    short = segments[segments.LEN_M < crit.MH_SNAP_M]
    if len(short):
        print(f"\n    [clearance] {len(short)} reach(es) under {crit.MH_SNAP_M:g} m, "
              f"shortest {short.LEN_M.min():.3f} m")
    assert len(short) == 0, (
        f"{len(short)} reach(es) are shorter than the {crit.MH_SNAP_M:g} m minimum chamber "
        f"clearance (shortest {short.LEN_M.min():.3f} m). Their two chambers are one "
        f"structure and the reach between them does not exist")


@pytest.mark.published
def test_every_contracted_chamber_is_on_the_record(crit):
    """Removing a chamber is allowed; removing it silently is not.

    Philosophy: anything a pass can ADD, a later pass must be able to TAKE AWAY, and the
    stage publishes how many it removed. `close_pairs` is that record.
    """
    if "close_pairs" not in layer_names("chambers"):
        pytest.skip("no close_pairs layer")
    cp = layer("chambers", "close_pairs")
    if not len(cp):
        pytest.skip("nothing was inside the clearance - nothing to record")
    for col in ("A", "B", "GAP_M", "STATUS"):
        assert col in cp.columns, f"close_pairs has no {col} - the record is incomplete"
    assert (cp.GAP_M.astype(float) < crit.MH_SNAP_M).all(), (
        "close_pairs lists a pair that was never inside the clearance")
    blank = int((cp.STATUS.astype(str).str.strip() == "").sum())
    assert blank == 0, f"{blank} contracted pair(s) carry no STATUS saying what was done"
    print(f"\n    [clearance] {len(cp)} pair(s) recorded; "
          f"{int((cp.JOINED_BY_A_PIPE == 1).sum())} contracted, "
          f"{int((cp.JOINED_BY_A_PIPE == 0).sum())} left as a layout decision")


@pytest.mark.published
def test_contracting_a_pair_did_not_push_a_reach_over_the_spacing(chambers, segments):
    """Absorbing a stub lengthens the reach above it. That must not quietly break the
    spacing rule the stage ships - the reach is re-divided instead."""
    man = layer("chambers", "manifest")
    row = man[man.ITEM.astype(str) == "split length"]
    if not len(row):
        pytest.skip("no split length in the manifest")
    split = float(row.VALUE.iloc[0])
    over = segments[segments.LEN_M > split + 0.01]
    print(f"\n    [spacing] longest reach {segments.LEN_M.max():.2f} m against the "
          f"{split:g} m split length; {len(over)} over it")
    assert len(over) == 0, (
        f"{len(over)} reach(es) exceed the shipped {split:g} m split length, longest "
        f"{over.LEN_M.max():.2f} m. A contraction absorbs a stub into the reach above; "
        f"re-divide that reach rather than widening the check")


# ==========================================================================================
# 2.  THE INLET ANGLE
# ==========================================================================================

def _bearing(ax, ay, bx, by) -> float:
    return math.degrees(math.atan2(bx - ax, by - ay)) % 360.0


def _inlet(arr: float, dep: float) -> float:
    """180 deg is straight on, 90 deg a right-angle inlet, 0 deg flow doubling back."""
    return 180.0 - abs(((dep - arr + 180.0) % 360.0) - 180.0)


def _measure(segments):
    """Re-derive every inlet angle from the PUBLISHED reaches alone.

    The direction of flow is the reach's CHORD. That is not a convenience: a pipe is laid
    straight between two chambers - 98.1 % of NAMA's built pipes are a two-point line and
    99.36 % lie inside 0.5 m of their own chord - and `substring` leaves duplicated
    vertices, so a bearing taken from a reach's first two coordinates can come off a
    sub-millimetre sliver instead of off the 25 m pipe.
    """
    import shapely

    out = {}
    ins = {}
    for u, d, cid, g in zip(segments.US_NODE.values, segments.DS_NODE.values,
                            segments.ARC_CID.values, segments.geometry.values):
        c = shapely.get_coordinates(g)
        if len(c) < 2 or math.hypot(c[-1][0] - c[0][0], c[-1][1] - c[0][1]) < 1e-6:
            continue
        b = _bearing(c[0][0], c[0][1], c[-1][0], c[-1][1])
        out[u] = (b, str(cid))
        ins.setdefault(d, []).append((b, str(cid)))
    rows = []
    for uid, arr in ins.items():
        if uid not in out:
            continue
        ob, ocid = out[uid]
        for b, icid in arr:
            rows.append({"CH": uid, "DEG": _inlet(b, ob), "N_IN": len(arr),
                         "SAME_ARC": int(icid == ocid)})
    return pd.DataFrame(rows)


@pytest.mark.published
def test_inlet_angles_are_measured_on_the_pipes_that_were_published(chambers, segments):
    """The defect: the angle was measured before the prune, on pipes that were then deleted.

    Nothing here says the count must be zero. It says the count must describe the network in
    the file. A priced swept-channel chamber for an inlet that does not exist is a defect
    whichever way it leans, and pruning can only REMOVE inlets, so every stale flag was an
    over-count.
    """
    got = _measure(segments)
    mn = got.groupby("CH").DEG.min()
    pub = pd.to_numeric(chambers.INLET_DEG, errors="coerce")
    here = chambers.NODE_UID.map(mn).astype(float)

    ghost = int((np.isfinite(pub) & ~np.isfinite(here)).sum())
    missing = int((~np.isfinite(pub) & np.isfinite(here)).sum())
    both = np.isfinite(pub) & np.isfinite(here)
    # the published value is floored to 2 dp so it can never overstate compliance
    floored = np.floor(here[both].values * 100.0) / 100.0
    worst = float(np.abs(floored - pub[both].values).max()) if both.any() else 0.0
    print(f"\n    [H10] {int(both.sum()):,} chambers re-measured off the published reaches; "
          f"{ghost} carry an angle no published pipe can produce, {missing} have a "
          f"measurable inlet and no published angle, worst disagreement {worst:.4f} deg")
    assert ghost == 0, (
        f"{ghost} chambers publish an INLET_DEG that no reach in the published layer can "
        f"produce. The angle was measured before the prune - move `angles()` after it")
    assert missing == 0, (
        f"{missing} chambers have an inlet in the published layer and no published angle")
    assert worst <= 1e-6, (
        f"the published inlet angle disagrees with the published geometry by up to "
        f"{worst:.4f} deg")


@pytest.mark.published
def test_the_published_angle_and_the_published_flag_tell_the_same_story(chambers, crit):
    """85 chambers published INLET_DEG = 90.0 with INLET_FLAG = 1. A reader who re-derives
    the flag from the number must get the flag that is there."""
    deg = pd.to_numeric(chambers.INLET_DEG, errors="coerce")
    flag = chambers.INLET_FLAG.astype(int)
    derived = ((deg < crit.INLET_MIN_DEG) & np.isfinite(deg)).astype(int)
    bad = int((derived != flag).sum())
    if bad:
        s = chambers.loc[derived != flag, ["NODE_UID", "INLET_DEG", "INLET_FLAG"]].head()
        print(f"\n    [H10] disagreeing rows:\n{s.to_string(index=False)}")
    assert bad == 0, (
        f"{bad} chambers where INLET_DEG and INLET_FLAG disagree at the "
        f"{crit.INLET_MIN_DEG:g} deg limit. Round the published angle DOWN and take the "
        f"flag from it, so an angle can never be printed as compliant while it is flagged")


@pytest.mark.published
def test_the_swept_channel_flag_is_exactly_the_breaches(chambers):
    """SWEPT_CH prices a purpose-made chamber. It must be one per breach - no more, and
    no fewer."""
    assert "SWEPT_CH" in chambers.columns, "no SWEPT_CH column - the breaches are not priced"
    n_flag = int(chambers.INLET_FLAG.sum())
    n_swept = int(chambers.SWEPT_CH.sum())
    print(f"\n    [H10] {n_flag:,} breaches, {n_swept:,} swept-channel chambers priced")
    assert n_flag == n_swept, (
        f"{n_flag:,} inlets breach 90 deg but {n_swept:,} chambers are priced for a swept "
        f"channel. Every breach is a priced item or the cost is not in the estimate")


@pytest.mark.published
def test_the_breaches_are_split_by_cause_because_one_rule_does_not_fix_two_defects():
    """The as-built calibration (ASBUILT_STUDY N10) found NAMA's own breaches split into 240
    BRANCH inlets clustered just under 90 deg and 122 PASS-THROUGH HAIRPINS at chambers with
    a single inflow and no branch at all, which the 95 deg target does not touch. Ours must
    be published the same way, or the count is a number with no action attached to it."""
    if "inlet_split" not in layer_names("chambers"):
        pytest.fail("stage 4 publishes no `inlet_split` - the breaches are one undivided "
                    "count, and a branch inlet and a pass-through hairpin are different "
                    "defects with different resolutions")
    sp = layer("chambers", "inlet_split")
    txt = " | ".join(sp.CLASS.astype(str))
    assert "BRANCH" in txt.upper(), "no BRANCH class in inlet_split"
    assert "HAIRPIN" in txt.upper(), "no PASS-THROUGH HAIRPIN class in inlet_split"
    for c in ("inlets", "of_that_kind", "pct"):
        assert c in sp.columns, f"inlet_split has no {c} - a count without a denominator"
    print(f"\n    [H10 split]\n{sp.to_string(index=False)}")


@pytest.mark.published
def test_the_split_reproduces_from_the_published_geometry(segments, crit):
    """And the split must be a measurement, not a label: re-derive it from the reaches."""
    if "inlet_split" not in layer_names("chambers"):
        pytest.skip("no inlet_split layer")
    got = _measure(segments)
    got["DEG"] = np.floor(got.DEG.values * 100.0) / 100.0
    lo = got[got.DEG < crit.INLET_MIN_DEG]
    br = int((lo.N_IN >= 2).sum())
    hp = int((lo.N_IN == 1).sum())
    sp = layer("chambers", "inlet_split")
    pub_br = int(sp.loc[sp.CLASS.astype(str).str.startswith("BRANCH"), "inlets"].iloc[0])
    pub_hp = int(sp.loc[sp.CLASS.astype(str).str.startswith("PASS-THROUGH"),
                        "inlets"].iloc[0])
    print(f"\n    [H10 split] re-derived branch {br:,} / hairpin {hp:,}; "
          f"published branch {pub_br:,} / hairpin {pub_hp:,}")
    assert (br, hp) == (pub_br, pub_hp), (
        f"the published split (branch {pub_br:,}, hairpin {pub_hp:,}) does not reproduce "
        f"from the published reaches (branch {br:,}, hairpin {hp:,})")


@pytest.mark.published
def test_the_bearing_is_never_taken_from_two_coincident_points(segments):
    """`substring` leaves duplicated vertices: 1,936 of 56,696 reaches began with a leg
    shorter than one millimetre. A bearing from two identical points is `atan2(0, 0)` = 0.0,
    a due-north direction manufactured out of nothing, and taking the direction of flow off
    such a sliver hid 171 breaches by reporting them as 179.9 deg - straight through."""
    import shapely

    n_sliver = 0
    n_dead = 0
    for g in segments.geometry.values:
        c = shapely.get_coordinates(g)
        if len(c) < 2:
            n_dead += 1
            continue
        if math.hypot(c[-1][0] - c[0][0], c[-1][1] - c[0][1]) < 1e-6:
            n_dead += 1
        if math.hypot(c[1][0] - c[0][0], c[1][1] - c[0][1]) < 1e-3:
            n_sliver += 1
    print(f"\n    [H10] {n_sliver:,} reaches begin with a leg under 1 mm - which is why the "
          f"direction of flow is taken from the chord; {n_dead} reaches have no direction "
          f"at all")
    assert n_dead == 0, (
        f"{n_dead} reach(es) start and end at the same point, so they have no direction of "
        f"flow and any inlet angle measured against them is fabricated")


@pytest.mark.published
def test_a_chamber_with_no_inlet_pipe_publishes_no_angle_rather_than_a_number(chambers):
    """G203-p30 governs an INLET PIPE. A head has none and an outfall has no outgoing pipe
    to measure against, so the rule does not apply and the honest publication is a blank.

    This is the guard against the defect that started the whole column: a crossing angle
    published as 90 on all 3,290 rows. Filling a not-applicable with 90 or with 180 makes it
    look measured, and 180 would read as a perfectly straight inlet at a chamber that has no
    inlet at all.
    """
    deg = pd.to_numeric(chambers.INLET_DEG, errors="coerce")
    na = ~np.isfinite(deg)
    heads = int((chambers.loc[na, "NODE_KIND"] == "head").sum())
    outs = int((chambers.loc[na, "NODE_KIND"] == "outfall").sum())
    other = int(na.sum()) - heads - outs
    print(f"\n    [H10] {int(na.sum()):,} chambers carry no angle: {heads:,} heads (no "
          f"inlet pipe), {outs:,} outfalls (no outgoing pipe), {other:,} other")
    assert other == 0, (
        f"{other} chambers carry no inlet angle and are neither a head nor an outfall, so "
        f"the measurement failed rather than not applying")
    assert deg.dropna().nunique() > 1, (
        "INLET_DEG is constant - this is the fabricated-angle defect again")
