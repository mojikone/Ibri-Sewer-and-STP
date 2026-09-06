"""CONCEPT RULE 1 - THE SLOPE CLAMP AND THE FLAGGED DROPS.

    s_laid = clamp(s_ground, s_min_guideline(own bore, own flow), s_max_velocity)

Every test here is written against a defect that either happened or would not have been
caught by anything else in the suite:

  * **The pipe did not follow the ground.** Until 2026-09-06 `s6_levels.choose_size` targeted
    `max(s_min, s_shallow)`, where `s_shallow` is the gradient that brings a deep pipe back
    to 1.30 m of cover WITHIN ONE REACH. At a head the two are identical - which is why no
    single-reach check ever caught it - and everywhere else the pipe was steepened until it
    surfaced. That flattens the tier depth spread the as-built calibration is measured on
    (lateral 1.395 / trunk 3.004 / sub main 4.010 m, `_BRAIN/10_ASBUILT_CALIBRATION.md`),
    and it is invisible to every compliance check because the result is legal.
  * **A drop with no reason.** Concept rule 1 says every drop carries the reason it exists.
    A drop that names itself can be told from a levelling error; one that does not, cannot.
  * **A drop on a straight run.** NAMA put 120 of their 121 drops over 0.60 m at a junction
    in 95.45 km. The one exemption is the drop concept rule 1 itself creates, where the
    ground falls faster than 3.0 m/s allows.
  * **A bore below DN200.** G203-p29 Table 11 prescribes NOTHING under 200 mm, and the built
    network is 61.5 % OD160 by length - laid to a minimum the guideline never printed for it.
  * **A pass that only ever ADDS.** Losing the removal ledger cost the previous iteration 69
    spurious pumping stations (inheritance ledger row 4).

NO TEST HERE INVENTS A DESIGN NUMBER. Every threshold is read from `w12.criteria` or derived
inside the test from the guideline value, with the derivation written out.
"""
from __future__ import annotations

import math

import numpy as np
import geopandas as gpd
import pandas as pd
import pytest

import s6_levels as S
from w12 import contract as K
from w12 import hydra as HY
from w12.criteria import DEFAULT as C
from w12.criteria import replace


# ======================================================================================
# A SYNTHETIC NETWORK. Arrays only - `s6_levels.Net` sets whatever it is handed, so a test
# builds exactly the fields the functions under test read and nothing else. A fixture that
# quietly filled in the rest would hide which inputs the levelling actually depends on.
# ======================================================================================

def make_net(grd, links, q=0.004, dn_floor=None):
    """`grd` is ground level per node; `links` is [(u, v, length), ...]; `q` is the peak
    flow in m3/s carried by EVERY reach, so the diameter is constant and the test is about
    levels and not about sizing."""
    n = len(grd)
    eu = np.array([a for a, _b, _L in links], dtype=np.int64)
    ev = np.array([b for _a, b, _L in links], dtype=np.int64)
    elen = np.array([L for _a, _b, L in links], dtype=float)
    edge_of = np.full(n, -1, dtype=np.int64)
    for k, (a, _b, _L) in enumerate(links):
        assert edge_of[a] < 0, "one outgoing reach per node (H15) - the test graph is wrong"
        edge_of[a] = k
    grd = np.asarray(grd, dtype=float)
    net = S.Net(
        uid=np.array([f"N{i:03d}" for i in range(n)], dtype=object),
        x=np.arange(n, dtype=float), y=np.zeros(n), grd=grd,
        eu=eu, ev=ev, elen=elen,
        egnd_fall=np.array([grd[a] - grd[b] for a, b, _L in links]),
        edge_of=edge_of,
        etier=np.array(["lateral"] * len(links), dtype=object),
        subnet=np.array(["S01"] * n, dtype=object),
        order=None)
    net.order = S._topo(edge_of, ev, n)
    qpk = np.full(n, q * 1000.0)                       # L/s, the unit `pass1` expects
    return net, qpk


def level(net, qpk, crit=C):
    """pass 1 + the crown sweep + the drops + their reasons. Pass 2 is deliberately NOT run
    here: `relay` may lay a run steeper than the clamp to land on its junction invert
    (A-LEV-17), and these tests are about the clamp itself."""
    des = S.pass1(net, qpk, np.zeros(net.n, dtype=bool), crit)
    S.enforce_crowns(net, des)
    S.set_drops(net, des)
    des.drop_why = S.drop_reasons(net, des, crit)
    return des


def cover_at(net, des, i, crit=C):
    """Cover over the pipe LEAVING node i, on its own outside diameter (G203-p33)."""
    return crit.cover(int(des.dn[i]), float(net.grd[i] - des.inv[i]))


# ======================================================================================
# 1. THE THREE ARMS OF THE CLAMP, one hand-worked case each
# ======================================================================================

Q_SMALL = 0.004          # m3/s = 4 L/s. A DN200 carries this inside its own d/D limit at
                         # every gradient used below, so the diameter never moves and the
                         # test is about the clamp.

# A FACT WORTH WRITING DOWN, because it decides how the cap has to be tested: AT 4 L/S A
# DN200 NEVER REACHES 3.0 m/s AT ANY GRADIENT the contract will publish. `hydra.smax_for`
# returns "never" for it. The flow is too small - the water runs a few centimetres deep and
# the hydraulic radius is tiny - so on a small lateral the ONLY ceiling is the contract's
# own 25 % publishing bound. The velocity cap starts to bite around 10 L/s (26.6 %) and
# closes fast: 30 L/s caps at 10.85 %, 60 L/s at 6.99 %. So a test of the cap has to carry
# a real flow, and a lateral on steep ground legitimately follows the cliff.
Q_CAP = 0.030            # m3/s = 30 L/s. `hydra.smax_for(200, 0.030)` = 10.87 %, so the cap
                         # is reachable on ground a wadi bank actually has.



def test_the_governing_minimum_at_a_small_flow_is_table_11_not_the_tractive_value():
    """Both routes are computed and THE STEEPER GOVERNS (G203-p27: *"Steeper gradient
    calculated based on self-cleansing velocity and minimum tractive force methodology shall
    be adopted as minimum pipe gradient"*). At 4 L/s they are 5.00 and 2.97 mm/m."""
    t11 = C.table11(200)
    tract = HY.smin_tractive(Q_SMALL, C)
    assert t11 == pytest.approx(0.005), "G203-p29 Table 11, DN200 row"
    assert tract < t11, "at 4 L/s the tractive route is the flatter of the two"
    assert max(t11, tract) == pytest.approx(0.005)


def test_flatter_ground_than_the_minimum_takes_the_minimum_arm_and_the_pipe_digs_in():
    """*Never flatter than the guideline minimum for its OWN bore.* Ground at 0.20 mm/m,
    minimum 5.00: the pipe is laid at 5.00 and buys 4.80 mm/m of depth for every metre - the
    flatness debt philosophy sec 4 says to measure BEFORE anything about direction."""
    dn, s, smin, _why, iv, cap, arm = S.choose_size(
        Q_SMALL, None, 100.0, 99.98, 100.0, 200, C)
    assert arm == "minimum" and dn == 200
    assert s == pytest.approx(0.005)
    assert not cap
    debt = (s - 0.02 / 100.0) * 100.0
    assert debt == pytest.approx(0.48), "0.48 m of depth bought over one 100 m reach"


def test_ground_between_the_two_bounds_is_followed_exactly():
    """*Otherwise the ground's own fall.* 12.00 mm/m sits between 5.00 and the velocity cap,
    so it is laid at 12.00 and the cover at the far end is the cover at the near end."""
    dn, s, _smin, _why, iv, cap, arm = S.choose_size(
        Q_SMALL, None, 100.0, 98.8, 100.0, 200, C)
    assert arm == "ground" and not cap
    assert s == pytest.approx(0.012)
    inv_dn = iv - 100.0 * s
    assert C.cover(dn, 100.0 - iv) == pytest.approx(C.MIN_COVER_CROWN)
    assert C.cover(dn, 98.8 - inv_dn) == pytest.approx(C.MIN_COVER_CROWN)


def test_ground_steeper_than_the_velocity_cap_takes_the_cap_and_the_surplus_is_left_over():
    """*Never steeper than the slope at which max velocity is reached* (G203-p27 4.2.2.2,
    3.0 m/s). The laid gradient is strictly flatter than the ground, and the difference is
    the fall that has to go somewhere - which is the drop."""
    dn, s, _smin, _why, _iv, cap, arm = S.choose_size(
        Q_CAP, None, 100.0, 80.0, 100.0, 200, C)         # 200 mm/m of ground
    assert arm == "vmax" and cap
    assert s < 0.200, "the pipe does not chase the cliff"
    _y, v = HY.pipe_state(dn, s, Q_CAP, C)
    assert v is not None and v <= C.V_MAX + 1e-9, "the cap must actually hold 3.0 m/s"
    surplus = (0.200 - s) * 100.0
    assert surplus > 1.0, "over 1 m of fall the pipe may not take, on one 100 m reach"


def test_a_small_lateral_on_steep_ground_follows_the_cliff_and_that_is_correct():
    """The counterpart, and it is the reason the cap has to be tested at a real flow: at
    4 L/s a DN200 never reaches 3.0 m/s, so on 10 % ground the pipe simply follows the
    ground. Capping it there would manufacture a drop structure out of nothing."""
    dn, s, _smin, _why, _iv, cap, arm = S.choose_size(
        Q_SMALL, None, 100.0, 90.0, 100.0, 200, C)       # 100 mm/m of ground
    assert arm == "ground" and not cap
    assert s == pytest.approx(0.100)
    _y, v = HY.pipe_state(dn, s, Q_SMALL, C)
    assert v < C.V_MAX, f"{v:.2f} m/s - well inside the cap, so there is nothing to cap"


@pytest.mark.parametrize("fall_m", [-0.5, 0.0, 0.02, 0.2, 0.5, 1.2, 3.0, 10.0, 40.0])
@pytest.mark.parametrize("q", [0.004, 0.05, 0.4])
def test_the_clamp_is_never_outside_its_own_bounds(fall_m, q):
    """The clamp is a claim about EVERY reach: at or above the governing minimum, at or
    below the velocity cap, on the 0.05 % grid, and on the middle arm exactly the ground."""
    dn, s, smin, _why, _iv, _cap, arm = S.choose_size(
        q, None, 100.0, 100.0 - fall_m, 100.0, 200, C)
    assert s >= smin - 1e-12, "below its own governing minimum"
    assert s <= S._hi_bound(dn, q, C) + 1e-12, "past the velocity cap"
    steps = s / C.SLOPE_STEP
    assert abs(steps - round(steps)) < 1e-6, "off the 0.05 % grid (inheritance row 17)"
    assert arm in ("ground", "minimum", "vmax", "infeasible")
    if arm == "ground":
        assert s == pytest.approx(S.ceil_step(fall_m / 100.0), abs=1e-12)


def test_rounding_is_always_up_so_cover_can_never_decrease_on_the_ground_arm():
    """Rounding to the NEAREST step would put the laid gradient up to 0.25 mm/m below the
    ground's fall - and a reach starting at exactly 1.30 m of cover would then END below
    1.30 m. An H3 breach bought by a rounding rule is the kind of defect nobody looks for."""
    # a ground fall that is NOT on the grid: 7.3 mm/m -> the grid values are 7.0 and 7.5
    dn, s, _smin, _why, iv, _cap, arm = S.choose_size(
        Q_SMALL, None, 100.0, 99.27, 100.0, 200, C)
    assert arm == "ground"
    assert s == pytest.approx(0.0075), "rounded UP, never to the nearest"
    assert s > 0.0073
    assert C.cover(dn, 99.27 - (iv - 100.0 * s)) >= C.MIN_COVER_CROWN


# ======================================================================================
# 2. THE CLAMP ON A REAL CHAIN - and the defect that had no single-reach symptom
# ======================================================================================

def test_a_deep_pipe_on_falling_ground_keeps_its_depth_instead_of_being_surfaced():
    """THE DEFECT THIS CHANGE FIXES, and it needs at least two reaches to show at all.

    Head at minimum cover -> a flat reach that buries the pipe -> a reach on ground falling
    at 12 mm/m. The old rule steepened that third reach until the pipe came back to 1.30 m
    of cover in one span. The clamp follows the ground, so the depth the flat reach cost is
    CARRIED - which is what makes a collector deeper than the branch feeding it."""
    net, qpk = make_net([100.0, 99.90, 98.70, 97.50],
                        [(0, 1, 100.0), (1, 2, 100.0), (2, 3, 100.0)])
    des = level(net, qpk)
    assert str(des.clamp_by[0]) == "minimum"      # 1.0 mm/m of ground, 5.00 minimum
    assert str(des.clamp_by[1]) == "ground"       # 12.0 mm/m
    assert str(des.clamp_by[2]) == "ground"       # 12.0 mm/m
    c0, c1, c2 = (cover_at(net, des, i) for i in (0, 1, 2))
    assert c0 == pytest.approx(C.MIN_COVER_CROWN), "a head starts at minimum cover"
    assert c1 == pytest.approx(c0 + (0.005 - 0.001) * 100.0), \
        "the flat reach buys exactly (minimum gradient - ground fall) x length of depth"
    assert c2 == pytest.approx(c1, abs=1e-9), \
        "THE POINT: on the ground arm the depth is CARRIED, not given back"
    assert c2 > C.MIN_COVER_CROWN + 0.3


def test_the_pipe_never_ends_a_reach_below_minimum_cover_while_the_cap_is_not_biting():
    """Cover is measured at min(COVER_US, COVER_DN) - the as-built study found a reach-mean
    check misses 153 reaches (`_BRAIN/10_ASBUILT_CALIBRATION.md`, 'Shallow cover')."""
    rng = np.random.default_rng(20260906)
    fall = rng.normal(0.4, 1.2, 40)                     # metres per 100 m reach, both signs
    grd = np.concatenate([[100.0], 100.0 - np.cumsum(fall)])
    links = [(i, i + 1, 100.0) for i in range(len(grd) - 1)]
    net, qpk = make_net(grd, links)
    des = level(net, qpk)
    for i in range(net.n - 1):
        if str(des.clamp_by[i]) == "vmax":
            continue                                     # the cap is the one arm that can
        dn = int(des.dn[i])                              # lose cover - by design
        up = C.cover(dn, float(net.grd[i] - des.inv[i]))
        dnn = C.cover(dn, float(net.grd[i + 1] - (des.inv[i] - 100.0 * des.slope[i])))
        assert min(up, dnn) >= C.MIN_COVER_CROWN - 1e-9, f"reach {i} below 1.30 m of cover"


# ======================================================================================
# 3. EVERY DROP CARRIES THE REASON IT EXISTS
# ======================================================================================

def test_a_cliff_makes_a_drop_and_the_drop_says_velocity_cap():
    """*Where the ground outruns the pipe, compute the slope that meets the cap, place
    chambers to it, and take the surplus fall as a DROP.* The chamber is the one at the TOP
    of the cliff, because a reach must already be deep enough at its upstream end to still
    have cover at its downstream end."""
    # head -> two ground-arm reaches at 12 mm/m (so chamber 2 sits at minimum cover) ->
    # a 130 mm/m cliff, which is past the 10.87 % cap a DN200 at 30 L/s reaches 3.0 m/s at.
    net, qpk = make_net([100.0, 98.80, 97.60, 84.60],
                        [(0, 1, 100.0), (1, 2, 100.0), (2, 3, 100.0)], q=Q_CAP)
    des = level(net, qpk)
    assert str(des.clamp_by[1]) == "ground"
    assert cover_at(net, des, 1) == pytest.approx(C.MIN_COVER_CROWN), \
        "the ground arm holds the head's cover, which is what sets up the cliff"
    assert str(des.clamp_by[2]) == "vmax" and bool(des.capped[2])
    assert des.cliff[2] > 0.0, "the chamber at the top of the cliff is sunk"
    assert des.drop[2] == pytest.approx(des.cliff[2], abs=1e-9), \
        "and the sinking IS the drop - the arriving pipe was at minimum cover"
    assert str(des.drop_why[2]) == "velocity_cap"
    assert des.slope[2] * 100.0 < 13.0 - 1.0, \
        "the laid fall is well short of the 13.0 m the ground gives - that is the surplus"
    assert des.drop[2] > C.BACKDROP_MAX, "past 2 m it is a vortex drop shaft (G203-p30)"
    # the reach below the drop is laid AS HIGH AS IT CAN BE: exactly minimum cover at its
    # far end. Anything shallower would surface the pipe; anything deeper is excavation
    # bought for nothing.
    inv_dn = des.inv[2] - 100.0 * des.slope[2]
    assert C.cover(int(des.dn[2]), 84.60 - inv_dn) == pytest.approx(C.MIN_COVER_CROWN)


def test_a_shallow_branch_meeting_a_deep_collector_drops_and_says_cover_recovery():
    """The ordinary junction drop, and where NAMA's 120 of 121 sit. The branch stayed at its
    own cover and hands the difference over at the chamber rather than carrying it - which
    is the alternative to pass 2 spending the fall along the run."""
    #   0 -> 1 -> 2 : the collector, on ground too flat to lay on, so it buries itself
    #   3 -> 2      : a branch on ground that DOES fall, arriving shallow
    grd = [100.0, 99.99, 99.98, 101.20]
    net, qpk = make_net(grd, [(0, 1, 400.0), (1, 2, 400.0), (3, 2, 100.0)])
    des = level(net, qpk)
    assert str(des.clamp_by[0]) == "minimum", "the collector is on ground flatter than 5 mm/m"
    assert str(des.clamp_by[3]) == "ground", "the branch follows its own ground"
    assert des.drop[2] > C.DROP_TRIGGER, "the branch arrives well above the collector"
    assert str(des.drop_why[2]) == "cover_recovery"
    assert des.cliff[2] == 0.0, "nothing was sunk here - the collector was simply deeper"
    # the branch kept its own minimum cover the whole way: it did NOT carry the collector's
    # depth back up its own length, which is what "hands the depth back" means.
    assert cover_at(net, des, 3) == pytest.approx(C.MIN_COVER_CROWN)


def test_a_size_change_drops_by_the_crown_step_and_says_tier_step():
    """Crown matching (A-LEV-4) puts the outgoing soffit at or below the incoming one, so a
    DN200 into a DN400 steps down by OD_out - OD_in = 0.200 m. Nothing fell; the pipe grew,
    and calling that a levelling drop would misreport the diagnostic."""
    net, _q = make_net([100.0, 99.0], [(0, 1, 100.0)])
    des = S.Design(2)
    arrival = 98.45 - 100.0 * 0.002
    des.inv = np.array([98.45, arrival + C.outside_diameter(200)
                        - C.outside_diameter(400)])          # crown-matched, A-LEV-4
    des.dn = np.array([200, 400], dtype=np.int64)
    des.slope = np.array([0.002, 0.0])
    des.drop = np.zeros(2)
    S.set_drops(net, des)
    step = C.outside_diameter(400) - C.outside_diameter(200)
    assert des.drop[1] == pytest.approx(step, abs=1e-9) == pytest.approx(0.200)
    why = S.drop_reasons(net, des, C)
    assert str(why[1]) == "tier_step"
    assert step < C.DROP_TRIGGER, "a DN200 -> DN400 step needs no backdrop (G203-p30)"


def test_no_chamber_drops_without_a_reason_and_no_reason_without_a_drop():
    """The invariant `contract.validate()` enforces on the published layer, checked here on
    the design that produces it so a failure names the arithmetic and not the schema."""
    rng = np.random.default_rng(7)
    grd = np.concatenate([[100.0], 100.0 - np.cumsum(rng.normal(0.5, 2.0, 60))])
    links = [(i, i + 1, 80.0) for i in range(len(grd) - 1)]
    # three branches into the trunk, so there are real junction drops to classify
    extra = len(grd)
    grd = np.concatenate([grd, [grd[10] + 1.0, grd[25] + 1.5, grd[40] + 0.8]])
    links += [(extra, 10, 60.0), (extra + 1, 25, 60.0), (extra + 2, 40, 60.0)]
    net, qpk = make_net(grd, links)
    des = level(net, qpk)
    drops = des.drop > 0.0
    named = np.array([bool(str(w)) for w in des.drop_why])
    assert not bool((drops & ~named).any()), "a drop with no reason"
    assert not bool((~drops & named).any()), "a reason for a drop that is not there"
    assert set(str(w) for w in des.drop_why[drops]) <= set(K.DROP_WHY)


def test_the_drop_reasons_are_not_one_word_repeated():
    """INHERITANCE LEDGER ROW 22 - a published column that is constant where it should vary
    is a fabrication. `ANGLE_DEG = 90` shipped on all 3,290 crossings and the measured
    minimum was 0.00 deg. The same helper the contract uses is run here on the design."""
    rng = np.random.default_rng(11)
    grd = np.concatenate([[120.0], 120.0 - np.cumsum(rng.normal(0.6, 2.5, 120))])
    trunk = len(grd)
    links = [(i, i + 1, 80.0) for i in range(trunk - 1)]
    joins = list(range(5, 115, 3))
    grd = np.concatenate([grd, [grd[i] + 1.0 for i in joins]])
    links += [(trunk + k, i, 60.0) for k, i in enumerate(joins)]
    net, qpk = make_net(grd, links)
    # THE FLOW GROWS DOWNSTREAM, so the bore steps up and the drops have more than one
    # cause. On a single-diameter test network every drop is a junction drop and the check
    # below would fire on a design that is perfectly correct - which is worth knowing: the
    # constancy check is evidence about a NETWORK, and a network with one bore has one cause.
    qpk[:trunk] = np.linspace(4.0, 60.0, trunk)
    des = level(net, qpk)
    d = des.drop > 0.0
    assert int(d.sum()) >= K.VARY_MIN_ROWS, "the test network must be big enough to judge"
    assert len(set(int(x) for x in des.dn[:trunk])) > 1, "the bore has to move for this test"
    frame = pd.DataFrame(dict(DROP_M=des.drop, DROP_WHY=[str(w) for w in des.drop_why]))
    assert K.constant_column_problem(frame, "DROP_WHY", d) is None, \
        "every drop on this network was given the same reason"


# ======================================================================================
# 4. A NON-JUNCTION DROP IS A HARD FAILURE - with one named exemption
# ======================================================================================

def _nodes(rows):
    return pd.DataFrame(rows, columns=["NODE_UID", "DROP_M", "DROP_WHY", "N_IN"])


def test_a_drop_on_a_straight_run_refuses_to_publish():
    bad = _nodes([("N001", 1.4, "cover_recovery", 1)])
    with pytest.raises(K.ContractError) as e:
        S.refuse_nonjunction_drops(bad, C)
    assert "STRAIGHT RUN" in str(e.value) and "N001" in str(e.value)


def test_the_velocity_cap_drop_is_the_one_exemption():
    """Concept rule 1 CREATES this drop, and it is on a straight run by definition."""
    ok = _nodes([("N001", 3.9, "velocity_cap", 1),
                 ("N002", 0.2, "tier_step", 1),
                 ("N003", 1.4, "cover_recovery", 3)])
    S.refuse_nonjunction_drops(ok, C)                    # must not raise


def test_a_crown_step_on_a_straight_run_is_not_a_failure():
    """A size change on a pass-through chamber is legitimate - the flow grew."""
    S.refuse_nonjunction_drops(_nodes([("N001", 0.70, "tier_step", 1)]), C)


def test_a_drop_below_the_backdrop_trigger_is_not_tested():
    """G203-p30 makes a structure necessary above 0.60 m. Below it there is no structure to
    put at a junction, so the rule has nothing to bite on."""
    S.refuse_nonjunction_drops(_nodes([("N001", 0.4, "cover_recovery", 1)]), C)


# ======================================================================================
# 5. NO BORE BELOW DN200 - A-LEV-16
# ======================================================================================

def test_no_published_bore_is_below_the_table_11_range():
    assert S._DN0 >= C.DN_MIN_LATERAL == 200, "G203-p22 Table 6, lateral and main rows"
    assert min(C.DN_SERIES) == 200


def test_table_11_refuses_a_bore_it_has_no_row_for():
    """G203-p29 Table 11 runs 200 to '900 and above'. Below 200 is the TERTIARY network,
    where G203-p18 Table 5 governs in percentage slopes and a DIFFERENT tier vocabulary."""
    with pytest.raises(Exception):
        C.table11(160)


def test_extending_the_series_downwards_raises_rather_than_inventing_a_floor():
    """The guard exists so that a change to the series cannot silently start laying pipe to
    a minimum gradient the guideline never printed."""
    crit = replace(C, DN_SERIES=(160,) + tuple(C.DN_SERIES))
    try:
        with pytest.raises(K.ContractError) as e:
            S._rebuild_tables(crit)
        assert "Table 11" in str(e.value) and "160" in str(e.value)
    finally:
        S._rebuild_tables(C)                             # never leave the module rebuilt
    assert S._DN0 == 200


# ======================================================================================
# 6. THE REMOVAL LEDGER - inheritance row 4
# ======================================================================================

def test_the_removal_ledger_publishes_what_was_added_and_what_was_taken_away():
    """*Anything a pass can ADD, a later pass must be able to TAKE AWAY, and the stage
    publishes how many it removed.* W8 cleared its pump flags at the top of every pass and
    said why in a comment; the rewrite lost it and published 69 spurious stations."""
    des = S.Design(3)
    des.notes["removed"] = dict(stations_added=83, stations_pruned=69,
                                stations_published=14, drops_added_pass1=1781,
                                drops_removed_pass2=1585, vortex_added_pass1=1781,
                                vortex_removed_pass2=1585, drops_published=196,
                                vortex_published=41)
    t = S.removal_table(des)
    got = dict(zip(t.WHAT, t.N))
    assert got["lifting stations ADDED by the cap passes"] == 83
    assert got["lifting stations REMOVED by the prune"] == 69
    assert got["lifting stations PUBLISHED"] == 14
    assert (got["lifting stations ADDED by the cap passes"]
            - got["lifting stations REMOVED by the prune"]
            == got["lifting stations PUBLISHED"]), "added - removed must equal published"
    assert got["vortex shafts REMOVED by pass 2"] == 1585


def test_the_ledger_reports_zero_rather_than_disappearing_when_nothing_was_removed():
    """A blank is not a number. An empty ledger reads as 'not measured'."""
    t = S.removal_table(S.Design(1))
    assert len(t) == 9 and set(t.N) == {0}


# ======================================================================================
# 7. THE PUBLISHED EVIDENCE - the clamp has to be checkable OFF THE FILE
# ======================================================================================

def _fake_layers(net, des):
    """The two frames `clamp_table` reads, built from a levelled synthetic network."""
    kk = np.arange(net.m)
    ui = net.eu[kk]
    reaches = pd.DataFrame(dict(
        EDGE_UID=[f"E{k:05d}" for k in kk],
        LEN_M=net.elen[kk], TIER=["lateral"] * net.m,
        SLOPE_LAID=des.slope[ui] * 100.0, DN=des.dn[ui],
        GND_FALL=net.egnd_fall[kk],
        US_NODE=net.uid[ui], DS_NODE=net.uid[net.ev[kk]]))
    lev = pd.DataFrame(dict(
        EDGE_UID=reaches.EDGE_UID.values,
        CLAMP_BY=[str(des.clamp_by[i]) for i in ui],
        S_GROUND_MM=net.egnd_fall[kk] / net.elen[kk] * 1000.0,
        ABSORBED=des.absorbed[ui].astype(int)))
    return reaches, lev


def test_the_clamp_table_accounts_for_every_metre_and_proves_the_ground_arm():
    rng = np.random.default_rng(3)
    grd = np.concatenate([[100.0], 100.0 - np.cumsum(rng.normal(0.5, 1.5, 80))])
    links = [(i, i + 1, 90.0) for i in range(len(grd) - 1)]
    net, qpk = make_net(grd, links)
    des = level(net, qpk)
    reaches, lev = _fake_layers(net, des)
    t = S.clamp_table(reaches, lev, C)
    arms = t[t.ARM.isin(("ground", "minimum", "vmax", "infeasible"))]
    assert float(arms.PCT_LEN.sum()) == pytest.approx(100.0, abs=1e-6), \
        "the four arms must account for the whole network - a reach with no arm is a reach " \
        "whose gradient nobody can explain"
    check = t[t.ARM.str.startswith("CHECK")].iloc[0]
    assert float(check.PCT_LEN) == pytest.approx(100.0), \
        "on the ground arm the laid gradient must BE ceil_step(ground fall / length)"
    assert float(t.loc[t.ARM == "ground", "N"].iloc[0]) > 0, \
        "concept rule 1's middle arm must actually reach the design"


def test_the_drop_reason_table_splits_at_the_junction_and_totals_correctly():
    rng = np.random.default_rng(5)
    grd = np.concatenate([[100.0], 100.0 - np.cumsum(rng.normal(0.7, 2.0, 60))])
    links = [(i, i + 1, 80.0) for i in range(len(grd) - 1)]
    base = len(grd)
    grd = np.concatenate([grd, [grd[i] + 1.2 for i in range(4, 55, 6)]])
    links += [(base + k, i, 60.0) for k, i in enumerate(range(4, 55, 6))]
    net, qpk = make_net(grd, links)
    des = level(net, qpk)
    n_in = np.zeros(net.n, dtype=int)
    np.add.at(n_in, net.ev, 1)
    nodes = pd.DataFrame(dict(NODE_UID=net.uid, DROP_M=des.drop,
                              DROP_WHY=[str(w) for w in des.drop_why], N_IN=n_in))
    reaches = pd.DataFrame(dict(LEN_M=net.elen))
    t = S.drop_reason_table(nodes, reaches, C)
    allrow = t[t.DROP_WHY == "ALL"].iloc[0]
    named = t[t.DROP_WHY != "ALL"]
    assert int(named.N.sum()) == int(allrow.N), "the reasons must partition the drops"
    assert float(named.TOTAL_M.sum()) == pytest.approx(float(allrow.TOTAL_M), abs=1e-6)
    assert int(allrow.AT_A_JUNCTION) + int(allrow.ON_A_STRAIGHT_RUN) == int(allrow.N_OVER_0P60)
    straight = named[(named.ON_A_STRAIGHT_RUN > 0)
                     & (~named.DROP_WHY.isin(("velocity_cap", "tier_step")))]
    assert straight.empty, \
        "a drop over 0.60 m on a straight run, with neither exemption - the hard failure"


def test_the_tier_table_separates_a_flatter_collector_from_the_as_built_defect():
    """The built network lays 71.7 % of its sub mains flatter than the laterals feeding
    them, and the as-built study proves the cause is capacity, NOT tau: `DIA_OUT` never
    steps up. A flatter collector on a BIGGER bore is legitimate - a bigger pipe has a
    flatter Table 11 minimum and carries more at the same slope - so the two are counted
    apart and only the second is the finding."""
    reaches = pd.DataFrame(dict(
        US_NODE=["A", "B", "C"], DS_NODE=["B", "C", "D"],
        TIER=["lateral", "sub main", "sub main"],
        SLOPE_LAID=[1.2, 0.4, 0.5], DN=[200, 400, 400], LEN_M=[100.0, 100.0, 100.0]))
    t = S.tier_gradient_table(reaches)
    row = t[t.PAIR == "lateral -> sub main"].iloc[0]
    assert int(row.N) == 1 and int(row.FLATTER) == 1
    assert int(row.FLATTER_NO_STEP_UP) == 0, "the bore stepped up, so this is legitimate"
    assert float(row.BUILT_FLATTER_PCT) == pytest.approx(71.7)
    # now the same pair WITHOUT the size step - which is the built network's own defect
    reaches.loc[1, "DN"] = 200
    row = S.tier_gradient_table(reaches)
    row = row[row.PAIR == "lateral -> sub main"].iloc[0]
    assert int(row.FLATTER_NO_STEP_UP) == 1


# ======================================================================================
# 8. THE STAGE STILL AGREES WITH ITS OWN REFERENCE IMPLEMENTATION
# ======================================================================================

def test_the_published_node_and_reach_layers_still_pass_the_contract():
    """THE ONE TEST THAT WOULD HAVE CAUGHT THE COORDINATION COST OF THIS CHANGE.

    `contract.py` now REQUIRES DROP_WHY, JOIN_MAIN, JOIN_OFF_M, JOIN_WHY, NAME, TOWN and
    SUBNET on `nodes` and NAME/TOWN/SUBNET on `reaches`. A stage that does not write them
    fails `validate()` at publish time - which on the real network is twenty minutes into a
    run. This builds the layers from a nine-chamber synthetic network and validates them,
    so the failure costs a second instead.

    The two obstacle steps are stubbed: they read the roads and streams GeoPackages, which
    are stage-1 products and not what is under test here."""
    from shapely.geometry import LineString

    rng = np.random.default_rng(19)
    grd = np.concatenate([[100.0], 100.0 - np.cumsum(rng.normal(0.5, 1.5, 8))])
    grd = np.concatenate([grd, [grd[3] + 1.2]])           # one branch, so there is a drop
    links = [(i, i + 1, 90.0) for i in range(8)] + [(9, 3, 60.0)]
    net, qpk = make_net(grd, links)
    n, m = net.n, net.m
    net.kind4 = np.array(["chamber"] * n, dtype=object)
    net.on_wadi_nd = np.zeros(n, dtype=int)
    net.haz = np.zeros(n)
    net.inlet_deg = np.full(n, 180.0)
    net.n_conn = np.zeros(n, dtype=int)
    net.esrc = np.array(["draft_base"] * m, dtype=object)
    net.econf = np.array(["corroborated"] * m, dtype=object)
    # the drawn line has to BE the published length - contract FIX 7, and the defect it was
    # written against was a LEN_M that differed from its own shape by up to 87 m.
    net.egeom = [LineString([(0.0, 10.0 * k), (float(L), 10.0 * k)])
                 for k, (_a, _b, L) in enumerate(links)]

    des = level(net, qpk)
    acc = dict(QPK=qpk, QADF=np.full(n, 10.0), NPROP=np.full(n, 4.0),
               PF=np.full(n, 3.62139), QINF=np.full(n, 0.01),
               HELD=np.ones(n, dtype=int), UPSLEN=np.full(n, 500.0))

    def _no_dual(_net, buffer_m=4.0):
        return np.zeros(_net.m)

    def _no_crossings(_net, _des, on_dual, live, crit=C):
        empty = gpd.GeoDataFrame(
            columns=[f.name for f in K.CROSSINGS.fields] + ["geometry"],
            geometry=[], crs=K.CRS_EPSG)
        return (empty, np.array([""] * _net.m, dtype=object), pd.DataFrame(),
                np.zeros(_net.m), np.zeros(_net.m), pd.DataFrame())

    old_dual, old_cross = S.dual_overlap, S.build_crossings
    try:
        S.dual_overlap, S.build_crossings = _no_dual, _no_crossings
        layers = S.build_layers(net, des, acc, 3.62139, C)
    finally:
        S.dual_overlap, S.build_crossings = old_dual, old_cross

    K.validate(layers["nodes"], "nodes", stage="test_levels_clamp")
    K.validate(layers["reaches"], "reaches", stage="test_levels_clamp")
    nd = layers["nodes"]
    for f in ("DROP_WHY", "JOIN_MAIN", "JOIN_OFF_M", "JOIN_WHY", "NAME", "TOWN", "SUBNET"):
        assert f in nd.columns, f"the node layer is missing the contract field {f}"
    for f in ("NAME", "TOWN", "SUBNET"):
        assert f in layers["reaches"].columns
    d = nd.DROP_M.values > 0
    assert d.any(), "the synthetic network must produce at least one drop to be worth it"
    assert all(str(w) for w in nd.DROP_WHY.values[d]), "a drop with no reason"
    assert (nd.JOIN_OFF_M.values == 0).all(), \
        "concept rule 2 is the outfall stage's - this stage must not invent an offset"


def test_a_reach_may_still_be_smaller_than_the_one_above_it():
    """C-LEV-5 - A NAMED GAP, HELD OPEN ON PURPOSE.

    `A-LEV-3` in the module says *"a reach is never smaller than the reach immediately
    upstream of it"* and gives the reason: a constriction in a gravity sewer is a blockage
    waiting to happen. `pass1` does not enforce it - it passes the SERIES MINIMUM as the
    diameter floor on every reach, not the upstream diameter - and the assumption cites a
    function `sizing_reason` that does not exist in the module.

    This test EXPECTS the current behaviour, so it will fail the day somebody fixes it,
    which is the point: the fix should be deliberate, and it is a sizing change across the
    whole network rather than a levelling one. Found while testing the clamp; not fixed by
    the agent that found it, and written down instead of mentioned."""
    net, qpk = make_net([100.0, 98.80, 97.60, 84.60],
                        [(0, 1, 100.0), (1, 2, 100.0), (2, 3, 100.0)], q=Q_CAP)
    des = level(net, qpk)
    assert int(des.dn[1]) > int(des.dn[2]), (
        "the gap has been closed - update C-LEV-5 and A-LEV-3, and delete this test. "
        f"upstream DN{int(des.dn[1])}, downstream DN{int(des.dn[2])}")
    # and the reason it happens: the steeper reach carries the same flow in a smaller bore
    assert S.carries(int(des.dn[2]), float(des.slope[2]), Q_CAP, C)
    assert not S.carries(int(des.dn[2]), float(des.slope[1]), Q_CAP, C), \
        "the upstream reach genuinely needs the bigger bore at ITS gradient"


def test_the_modules_own_self_test_passes():
    """`s6_levels --selftest` checks the fast paths against `hydra`'s reference functions
    and the clamp against hand-worked arithmetic. Running it here means a change to either
    breaks the suite and not only the CLI."""
    S._self_test(verbose=False)
