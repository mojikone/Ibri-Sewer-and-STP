"""Adversarial review of stage 4's clearance-and-inlet fix: what the fix itself left behind.

THE FIX BEING REVIEWED was right about the two defects it names. Chambers inside
`criteria.MH_SNAP_M` were contracted at the placement instead of excused, the inlet angle
moved to after the prune so no priced swept channel is bought for a deleted pipe, and the
published angle was floored so the column and the flag can never tell different stories.
All three reproduce from the published GeoPackage.

WHAT IT DID NOT CLOSE, AND WHAT THIS FILE HOLDS IT TO:

  1. THE CHORD IS THE RIGHT BASIS ONLY WHERE THE REACH IS STRAIGHT, AND THAT WAS NEVER
     MEASURED ON THE STAGE'S OWN OUTPUT.  The direction of flow was moved off a
     sub-millimetre `substring` sliver and onto the reach's CHORD, justified by the built
     network's straightness.  On the 52,610 published reaches that are a two-point line the
     chord IS the leg, so the change is exact.  On the ones that BEND it is not: six
     published reaches depart from their own chord by more than STRAIGHT_TOL_M = 0.5 m - a
     bend with no chamber at it, which is the one thing the stage's straightness rule
     forbids - and on those the chord runs straight through a turn the pipe actually makes.
     Eleven chambers change side of the 90 deg rule depending on which basis is used, four
     of them from BREACH to compliant, so four swept-channel chambers are not priced.

     The evidence offered for the chord was taken on the 172 same-corridor hairpins alone,
     where the two bases do agree.  Over the whole layer they differ by up to 91 deg.

  2. THE WORST OF THOSE SIX BENDS IS CREATED BY THE CONTRACTION ITSELF.  Absorbing a
     sub-clearance stub hands a dog-leg to the reach above; `_resplit_over_split_length`
     re-divides such a reach for LENGTH but never for STRAIGHTNESS, so the bend stays with
     no chamber at it (1.77 m off its own chord on a 6.45 m reach, and its inlet bearing is
     60.8 deg away from the chord's).  It cannot simply be chambered: a chamber at that bend
     would stand inside the very 3 m clearance the contraction exists to honour.  That is a
     genuine conflict between two project rules on this geometry, and it is the engineer's
     call, not a check to be quietly widened.

  3. A NUMBER THAT COULD NOT BE FOUND IN THE DELIVERABLE.  `n_resplit` is counted before
     the prune, and the prune can delete the very reach that was re-divided.  On the first
     run with that code the manifest published "chambers put back after contraction = 1"
     and the published layer held none - the same "measured on a network that was then
     thrown away" defect the fix had just removed from the inlet angles, reintroduced in its
     own new counter.

TESTS THAT FAIL TODAY DO SO BECAUSE THE DEFECT IS REAL AND UNRESOLVED, NOT BECAUSE THEY ARE
STRICT.  None of them is marked xfail and none has a tolerance in it: a green suite over a
bend with no chamber at it is the failure mode this project keeps paying for.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from conftest import layer, layer_names

STRAIGHT_TOL_M = 0.5          # s4_chambers.STRAIGHT_TOL_M - PROJECT, calibrated on the
#                               built network: 99.36 % of NAMA's pipes lie inside 0.5 m of
#                               their own chord. Restated here rather than imported so the
#                               test does not agree with the code by construction.
LEG_SWEEP_M = (0.5, 1.0, 2.0)  # s4_chambers.BEARING_LEG_SWEEP_M - a sweep, not a value.


# ------------------------------------------------------------------ geometry primitives
def _coords(g) -> np.ndarray:
    import shapely
    return shapely.get_coordinates(g)


def _chord_offset(c: np.ndarray) -> float:
    """How far a polyline departs from its own chord. Written out rather than imported."""
    ax, ay = float(c[0][0]), float(c[0][1])
    bx, by = float(c[-1][0]), float(c[-1][1])
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L < 1e-12 or len(c) < 3:
        return 0.0
    return float(max(abs((px - ax) * dy - (py - ay) * dx) / L for px, py in c))


def _bearing(ax, ay, bx, by) -> float:
    return math.degrees(math.atan2(bx - ax, by - ay)) % 360.0


def _inlet(arr: float, dep: float) -> float:
    return 180.0 - abs(((dep - arr + 180.0) % 360.0) - 180.0)


def _ends(c: np.ndarray, min_leg: float):
    """(departure at the first point, arrival at the last). min_leg <= 0 gives the chord."""
    if min_leg <= 0.0:
        b = _bearing(c[0][0], c[0][1], c[-1][0], c[-1][1])
        return b, b
    k = 1
    while k < len(c) - 1 and math.hypot(c[k][0] - c[0][0], c[k][1] - c[0][1]) < min_leg:
        k += 1
    j = len(c) - 2
    while j > 0 and math.hypot(c[-1][0] - c[j][0], c[-1][1] - c[j][1]) < min_leg:
        j -= 1
    return (_bearing(c[0][0], c[0][1], c[k][0], c[k][1]),
            _bearing(c[j][0], c[j][1], c[-1][0], c[-1][1]))


def _flags(segments, chambers, min_leg: float) -> np.ndarray:
    """The H10 verdict at every chamber, on one basis. True = breach."""
    out, ins = {}, {}
    for u, d, g in zip(segments.US_NODE.values, segments.DS_NODE.values,
                       segments.geometry.values):
        c = _coords(g)
        if len(c) < 2 or math.hypot(c[-1][0] - c[0][0], c[-1][1] - c[0][1]) < 1e-6:
            continue
        b0, b1 = _ends(c, min_leg)
        out[u] = b0
        ins.setdefault(d, []).append(b1)
    a = np.array([min((_inlet(b, out[u]) for b in ins[u]), default=np.nan)
                  if (u in ins and u in out) else np.nan
                  for u in chambers.NODE_UID.values])
    a = np.floor(a * 100.0) / 100.0
    return (a < 90.0) & np.isfinite(a)


# ==========================================================================================
# 1.  THE STRAIGHTNESS THE WHOLE STAGE RESTS ON
# ==========================================================================================

@pytest.mark.published
def test_no_published_reach_bends_past_the_straightness_the_stage_rests_on(segments):
    """A bend with no chamber at it.

    STRAIGHT_TOL_M is not a reporting statistic in this stage - two separate decisions rest
    on it. It is the trigger that puts a chamber at every bend ("a pipe is laid straight
    between chambers"), and it is the justification for reading the direction of flow off
    the reach's chord. The stage asserted it from the first line of its docstring and never
    once measured it on what it published.
    """
    off = np.array([_chord_offset(_coords(g)) for g in segments.geometry.values])
    bad = int((off > STRAIGHT_TOL_M).sum())
    if bad:
        w = pd.DataFrame({"US_NODE": segments.US_NODE.values,
                          "DS_NODE": segments.DS_NODE.values,
                          "LEN_M": segments.LEN_M.values.round(2),
                          "off_m": off.round(3)}).nlargest(bad, "off_m")
        print(f"\n    [straight] {bad} of {len(segments):,} reaches past "
              f"{STRAIGHT_TOL_M:g} m:\n{w.to_string(index=False)}")
    assert bad == 0, (
        f"{bad} published reach(es) depart from their own chord by more than "
        f"STRAIGHT_TOL_M = {STRAIGHT_TOL_M:g} m (worst {off.max():.2f} m) - a bend with no "
        f"chamber at it. Two causes, both in this stage: `split_positions` drops a bend cut "
        f"that lands within the 3 m minimum clearance of a neighbour, and `contract_pairs` "
        f"re-divides an absorbed reach for LENGTH but never for straightness. Do NOT widen "
        f"the tolerance - the bend trigger and the inlet-angle basis both rest on it")


@pytest.mark.published
def test_contracting_a_pair_did_not_leave_a_bend_with_no_chamber_at_it(segments):
    """The absorbed stub is a dog-leg handed to the reach above.

    `_resplit_over_split_length` puts a chamber back when the reach goes over the split
    LENGTH. It does not look at straightness, and the worst-bent reach in the whole
    published layer is one of these.
    """
    if "close_pairs" not in layer_names("chambers"):
        pytest.skip("no close_pairs layer")
    cp = layer("chambers", "close_pairs")
    cp = cp[cp.JOINED_BY_A_PIPE == 1] if len(cp) else cp
    if not len(cp):
        pytest.skip("nothing was contracted - nothing could have been left bent")
    survivors = set(cp.B.astype(str))
    absorbed = segments[segments.DS_NODE.astype(str).isin(survivors)]
    off = np.array([_chord_offset(_coords(g)) for g in absorbed.geometry.values]) \
        if len(absorbed) else np.zeros(0)
    bad = int((off > STRAIGHT_TOL_M).sum())
    print(f"\n    [contract] {len(absorbed)} reach(es) end at a contracted structure; "
          f"worst chord offset {off.max() if len(off) else 0:.3f} m")
    assert bad == 0, (
        f"{bad} reach(es) that absorbed a sub-clearance stub now bend past "
        f"{STRAIGHT_TOL_M:g} m with no chamber at the bend (worst {off.max():.2f} m). "
        f"Chambering it is NOT available - the chamber would stand inside the same 3 m "
        f"clearance the contraction exists to honour - so this is a real conflict between "
        f"two project rules and belongs to the engineer, not to a widened tolerance")


# ==========================================================================================
# 2.  DOES THE 90 DEG VERDICT SURVIVE THE BASIS IT IS MEASURED ON?
# ==========================================================================================

@pytest.mark.published
def test_the_ninety_degree_verdict_does_not_depend_on_where_the_bearing_is_taken(
        chambers, segments):
    """The published direction of flow is the reach's CHORD. Read it instead from the pipe's
    own direction where it meets the chamber and eleven chambers change side.

    Only the ones the chord calls COMPLIANT are asserted here, because those are the ones
    that cost money: each is a swept-channel chamber that G203-p30 requires and that the
    estimate does not carry. The reverse direction - a breach the local reading clears - is
    printed, not asserted, since publishing it as a breach is the safe way to be wrong.
    """
    chord = _flags(segments, chambers, 0.0)
    unpriced = np.zeros(len(chambers), bool)
    both_ways = np.zeros(len(chambers), bool)
    for m in LEG_SWEEP_M:
        local = _flags(segments, chambers, m)
        unpriced |= local & ~chord
        both_ways |= local != chord
    n_up, n_bw = int(unpriced.sum()), int(both_ways.sum())
    print(f"\n    [basis] {n_bw} chambers change side over the "
          f"{'/'.join(f'{m:g}' for m in LEG_SWEEP_M)} m sweep; {n_up} of them are published "
          f"COMPLIANT and would be a breach read locally: "
          f"{list(chambers.NODE_UID.values[unpriced])[:10]}")
    assert n_up == 0, (
        f"{n_up} chamber(s) are published as meeting G203-p30's 90 deg rule on the reach's "
        f"chord and breach it on the pipe's local direction at the chamber. Each is an "
        f"unpriced swept-channel chamber. Every one sits on a reach that bends past "
        f"STRAIGHT_TOL_M, where the chord is not the pipe - fix the geometry or price them, "
        f"but do not choose the basis that gives the smaller number")


@pytest.mark.published
def test_the_two_bases_agree_wherever_the_reach_is_actually_straight(segments):
    """The control on the test above, and the reason it is a narrow finding rather than a
    rejection of the chord: on a two-point reach the chord IS the leg, and 52,610 of the
    published reaches are two-point lines. The chord change was exact everywhere the stage's
    own straightness rule holds."""
    n2 = 0
    agree = 0
    for g in segments.geometry.values:
        c = _coords(g)
        if len(c) != 2:
            continue
        n2 += 1
        b0c, b1c = _ends(c, 0.0)
        b0l, b1l = _ends(c, 1.0)
        if abs(b0c - b0l) < 1e-9 and abs(b1c - b1l) < 1e-9:
            agree += 1
    print(f"\n    [basis] {n2:,} of {len(segments):,} reaches are a two-point line; the "
          f"chord and the local leg are the same bearing on {agree:,} of them")
    assert n2 == agree, (
        f"{n2 - agree} two-point reaches give a different bearing on the chord and on the "
        f"leg, which is impossible - the measurement itself is wrong")


# ==========================================================================================
# 3.  THE COUNTS THE STAGE PUBLISHES ABOUT ITS OWN EDITS
# ==========================================================================================

@pytest.mark.published
def test_the_movable_breaches_are_measured_from_the_geometry_not_written_down(
        chambers, segments):
    """`inlet_split` publishes "fixable by MOVING A CHAMBER". It must be derived.

    Derivation: a chamber standing on a stage-2 graph node cannot be moved at all - the node
    IS where the corridors meet - and one that is not can only slide ALONG its own corridor,
    which keeps whatever bend it stands on. So a breach is movable here only if the chamber
    carries no ORIENT_ND and its inlet arrives on a different corridor from the one its
    outlet leaves on.
    """
    if "inlet_split" not in layer_names("chambers"):
        pytest.skip("no inlet_split layer")
    sp = layer("chambers", "inlet_split")
    row = sp[sp.CLASS.astype(str).str.contains("MOVING A CHAMBER")]
    if not len(row):
        pytest.fail("inlet_split does not publish how many breaches are fixable by moving "
                    "a chamber - the claim is made in the report and nowhere in the data")
    published = int(row.inlets.iloc[0])

    on_node = dict(zip(chambers.NODE_UID.astype(str),
                       chambers.ORIENT_ND.astype(str).values != ""))
    out, ins = {}, {}
    for u, d, cid, g in zip(segments.US_NODE.values, segments.DS_NODE.values,
                            segments.ARC_CID.astype(str).values, segments.geometry.values):
        c = _coords(g)
        if len(c) < 2 or math.hypot(c[-1][0] - c[0][0], c[-1][1] - c[0][1]) < 1e-6:
            continue
        b = _bearing(c[0][0], c[0][1], c[-1][0], c[-1][1])
        out[u] = (b, cid)
        ins.setdefault(d, []).append((b, cid))
    movable = 0
    for u, arr in ins.items():
        if u not in out:
            continue
        ob, ocid = out[u]
        for b, icid in arr:
            if math.floor(_inlet(b, ob) * 100.0) / 100.0 < 90.0:
                if not on_node.get(str(u), True) and icid != ocid:
                    movable += 1
    print(f"\n    [movable] published {published}, re-derived {movable}")
    assert published == movable, (
        f"`inlet_split` publishes {published} breaches fixable by moving a chamber and the "
        f"published geometry gives {movable}. A nought written into a table is not a "
        f"measurement, and this is the row the whole 'not one of them is fixable' argument "
        f"rests on")


@pytest.mark.published
def test_a_contracted_chamber_is_gone_and_the_one_it_merged_into_is_there(chambers):
    """`close_pairs` is the record of a REMOVAL. Both halves of it must be true in the
    layer: the chamber named A must not be in it, and the structure named B must be."""
    if "close_pairs" not in layer_names("chambers"):
        pytest.skip("no close_pairs layer")
    cp = layer("chambers", "close_pairs")
    cp = cp[cp.JOINED_BY_A_PIPE == 1] if len(cp) else cp
    if not len(cp):
        pytest.skip("nothing was contracted")
    live = set(chambers.NODE_UID.astype(str))
    still_there = sorted(set(cp.A.astype(str)) & live)
    missing = sorted(set(cp.B.astype(str)) - live)
    print(f"\n    [contract] {len(cp)} pair(s): {len(still_there)} removed chambers are "
          f"still published, {len(missing)} surviving structures are absent")
    assert not still_there, (
        f"close_pairs says {still_there} were contracted away and they are still in the "
        f"chambers layer - the record and the layer disagree")
    # B may legitimately be pruned later, so its absence is reported, not asserted, unless
    # its own removal would leave the record naming nothing at all.
    assert len(missing) < len(cp), (
        "every structure a pair was contracted INTO has been pruned away, so `close_pairs` "
        "records seven merges into nothing - the record no longer describes the deliverable")


@pytest.mark.published
def test_the_reach_that_absorbed_a_stub_carries_the_length_it_actually_has(segments):
    """Contraction lengthens the reach above. LEN_M must be re-measured off the geometry,
    not left as the old position-along-the-corridor difference - it is the length every
    downstream quantity is billed against."""
    err = (segments.LEN_M.values - segments.geometry.length.values)
    worst = float(np.abs(err).max())
    print(f"\n    [contract] worst LEN_M vs geometry {worst * 1000:.3f} mm over "
          f"{len(segments):,} reaches")
    assert worst < 0.05, (
        f"LEN_M and the published shape disagree by up to {worst:.3f} m. A contraction that "
        f"extends a reach and does not re-measure it bills the wrong length")


@pytest.mark.published
def test_the_stage_does_not_publish_an_edit_that_is_not_in_the_layer(chambers):
    """"chambers put back after contraction" is counted BEFORE the prune, and the prune can
    delete the very reach that was re-divided. The first run with that code published 1 and
    the layer held none.

    A re-split chamber is the only kind that carries a corridor (`ARC_CID`) and no position
    along it (`S_ALONG`), so it can be counted from the file directly.
    """
    man = layer("chambers", "manifest")
    live = man[man.ITEM.astype(str).str.strip()
               == "of those, still in the published layer"]
    if not len(live):
        pytest.fail(
            "the manifest reports how many chambers were put back after a contraction but "
            "not how many survive the prune, so the number cannot be found in the "
            "deliverable. Publish both - a pre-prune count standing alone is the defect "
            "this stage just removed from the inlet angles")
    claimed = int(float(live.VALUE.iloc[0]))
    sig = int(((chambers.ARC_CID.astype(str) != "")
               & (~np.isfinite(pd.to_numeric(chambers.S_ALONG, errors="coerce")))).sum())
    print(f"\n    [resplit] manifest {claimed}, layer {sig}")
    assert claimed == sig, (
        f"the manifest says {claimed} re-split chamber(s) survive the prune and the layer "
        f"holds {sig}")


@pytest.mark.published
def test_the_inlet_denominator_only_counts_inlets_the_rule_can_be_applied_to(segments):
    """G203-p30 measures an inlet AGAINST the outgoing pipe. An inlet at an outfall has no
    outgoing pipe, so it can never breach; counting it dilutes the breach rate, and the
    dilution runs in the flattering direction - it took the branch rate from 26.44 % to
    25.96 %, which is the difference between matching NAMA's own 26.46 % and beating it."""
    if "inlet_split" not in layer_names("chambers"):
        pytest.skip("no inlet_split layer")
    sp = layer("chambers", "inlet_split")
    row = sp[sp.CLASS.astype(str).str.startswith("BRANCH")]
    if not len(row):
        pytest.skip("no BRANCH row")
    published = int(row.of_that_kind.iloc[0])
    has_out = set(segments.US_NODE.astype(str))
    ins = {}
    for d in segments.DS_NODE.astype(str).values:
        ins[d] = ins.get(d, 0) + 1
    honest = sum(n for u, n in ins.items() if u in has_out and n >= 2)
    print(f"\n    [denominator] branch inlets published {published:,}, "
          f"measurable {honest:,}")
    assert published == honest, (
        f"the BRANCH denominator is {published:,} inlets but only {honest:,} of them are at "
        f"a chamber with an outgoing pipe to be measured against. The rest cannot breach, "
        f"so including them understates the breach rate against the operator's own network")
