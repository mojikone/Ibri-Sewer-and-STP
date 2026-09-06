"""ADVERSARIAL REVIEW OF THE LEVELS STAGE - the cases the clamp revision did not cover.

Every test here is written against something measured in `s6_levels.py` on 2026-09-06, not
against a hypothesis:

  * **A size change was published as a velocity cap.** `pass1` sinks a chamber whenever its
    invert sits above the level the outgoing reach needs. TWO different causes do that: the
    3.0 m/s cap (concept rule 1's own drop) and a BIGGER OUTGOING BORE, whose minimum-cover
    datum is deeper by the crown step. Both were recorded in `des.cliff`, and `drop_reasons`
    tests the cliff first - so an ordinary DN200 -> DN400 step on FLAT ground, with nothing
    capped anywhere near it, published DROP_WHY = 'velocity_cap'. The revision's own test for
    'tier_step' hand-builds a `Design` and never runs `pass1`, which is why it passed.
  * **Pass 2 was silently switched off on those runs.** `relay` skips any run containing a
    cliff. Measured on 300 random branched networks: 47 runs dropped from pass 2 with NO cap
    anywhere in them. Pass 2 is the pass that takes the vortex-shaft count from 1,781 to 196.
  * **The sinking moves no level**, so neither effect bought anything: re-running pass 1 and
    the crown sweep with the size-step sinking removed gives identical inverts to 0.0e+00 m.
  * **Rounding the ground arm UP accumulates without bound.** The cover-recovery term that
    used to reclaim it is gone, so on a 10 km path at 5.01 mm/m the pipe is laid at
    5.50 mm/m and arrives 4.9 m deeper than the ground it is following. That is not fixed
    here - it is a rule change the engineer has to make - and this file PINS the number so
    it cannot be lost.

NO TEST HERE INVENTS A DESIGN NUMBER. Every threshold comes from `w12.criteria`.
"""
from __future__ import annotations

import numpy as np
import pytest

import s6_levels as S
from w12.criteria import DEFAULT as C


# ======================================================================================
# The same synthetic-network shape the clamp tests use, rebuilt here rather than imported,
# so a change to the other file cannot silently change what these tests are levelling.
# ======================================================================================

def make_net(grd, links):
    n = len(grd)
    eu = np.array([a for a, _b, _L in links], dtype=np.int64)
    ev = np.array([b for _a, b, _L in links], dtype=np.int64)
    elen = np.array([L for _a, _b, L in links], dtype=float)
    edge_of = np.full(n, -1, dtype=np.int64)
    for k, (a, _b, _L) in enumerate(links):
        assert edge_of[a] < 0, "one outgoing reach per node (H15) - the test graph is wrong"
        edge_of[a] = k
    grd = np.asarray(grd, dtype=float)
    net = S.Net(uid=np.array([f"N{i:03d}" for i in range(n)], dtype=object),
                x=np.arange(n, dtype=float), y=np.zeros(n), grd=grd,
                eu=eu, ev=ev, elen=elen,
                egnd_fall=np.array([grd[a] - grd[b] for a, b, _L in links]),
                edge_of=edge_of,
                etier=np.array(["lateral"] * len(links), dtype=object),
                subnet=np.array(["S01"] * n, dtype=object), order=None)
    net.order = S._topo(edge_of, ev, n)
    return net


def level(net, qpk, crit=C):
    des = S.pass1(net, qpk, np.zeros(net.n, dtype=bool), crit)
    S.enforce_crowns(net, des)
    S.set_drops(net, des)
    des.drop_why = S.drop_reasons(net, des, crit)
    return des


def _branched(seed, n_main=30):
    """A chain with three branches and a flow that grows downstream, so the bore steps up
    and there are real junctions to classify."""
    rng = np.random.default_rng(seed)
    grd = np.concatenate([[100.0], 100.0 - np.cumsum(rng.normal(0.3, 1.6, n_main))])
    links = [(i, i + 1, float(rng.uniform(25.0, 120.0))) for i in range(len(grd) - 1)]
    base = len(grd)
    grd = np.concatenate([grd, grd[[3, 7, 11]] + rng.uniform(0.5, 3.0, 3)])
    links += [(base, 3, 60.0), (base + 1, 7, 60.0), (base + 2, 11, 60.0)]
    net = make_net(grd, links)
    qpk = np.linspace(4.0, 600.0, net.n)          # L/s - the bore has to step up
    return net, qpk


# ======================================================================================
# 1. A SIZE CHANGE IS NOT A VELOCITY CAP - through the REAL pass 1, not a hand-built Design
# ======================================================================================

def test_a_bore_step_on_flat_ground_is_tier_step_and_not_velocity_cap():
    """THE REGRESSION. Ground 5.00 mm/m, pipe laid at 5.00 mm/m, nothing capped - and the
    chamber still has to go down because a DN700 needs more cover than a DN200. The drop IS
    the crown step (A-LEV-4) and the word for it is 'tier_step'."""
    net = make_net([400.0, 399.5, 399.0, 398.5],
                   [(0, 1, 100.0), (1, 2, 100.0), (2, 3, 100.0)])
    qpk = np.array([4.0, 300.0, 900.0, 900.0])          # L/s: the bore steps 200 -> 700 -> 1200
    des = level(net, qpk)

    assert int(des.dn[0]) == 200 and int(des.dn[1]) > 200, "the bore must step up"
    for i in (1, 2):
        assert str(des.clamp_by[i]) == "ground", "the clamp took the ground's own fall"
        assert not bool(des.capped[i]), "nothing is capped - 5 mm/m is nowhere near 3.0 m/s"
        assert des.cliff[i] == 0.0, "a cliff is the CAP's drop, and the cap did not bite"
        assert des.step_sink[i] > 0.0, "the bore step sinking is recorded, not discarded"
        step = C.outside_diameter(int(des.dn[i])) - C.outside_diameter(int(des.dn[i - 1]))
        assert des.drop[i] == pytest.approx(step, abs=1e-9), \
            "the drop is exactly the crown step - nothing fell, the pipe grew"
        assert str(des.drop_why[i]) == "tier_step"


def test_the_size_step_sinking_is_never_larger_than_the_crown_step_it_comes_from():
    """The bound that makes the reclassification safe: for an uncapped reach the sinking is
    `L(s_ground - S) + (OD_out - OD_in) + (1.30 - cover_in)`, and with S >= s_ground and
    cover_in >= 1.30 that is at most the crown step. If it ever exceeded it, the drop would
    no longer be the crown step and 'tier_step' would be the wrong word."""
    seen = 0
    for seed in range(40):
        net, qpk = _branched(seed)
        des = level(net, qpk)
        for i in range(net.n):
            if des.step_sink[i] <= 0.0:
                continue
            seen += 1
            k = int(net.edge_of[i])
            d_out = int(des.dn[i])
            # the pipe arriving at i, if there is one
            ins = [int(net.eu[e]) for e in range(net.m) if int(net.ev[e]) == i]
            d_in = max([int(des.dn[u]) for u in ins], default=d_out)
            step = C.outside_diameter(d_out) - C.outside_diameter(d_in)
            assert des.step_sink[i] <= step + 1e-9, (
                f"node {i}: sunk {des.step_sink[i]:.4f} m for a crown step of {step:.4f} m")
            assert not bool(des.capped[i]), "a capped reach records a cliff, not a step sink"
    assert seen > 0, "the case did not occur - the test proves nothing"


def test_removing_the_size_step_sinking_changes_no_invert():
    """WHY THE RECLASSIFICATION COSTS NOTHING. `enforce_crowns` puts the chamber at the
    crown-matched level, which is at or below the level the sinking produced - so the sinking
    is subsumed and the design is bit-identical without it. This is the evidence that mixing
    it into `cliff` bought nothing and cost pass 2."""
    worst = 0.0
    for seed in range(40):
        net, qpk = _branched(seed)
        a = S.pass1(net, qpk, np.zeros(net.n, dtype=bool), C)
        S.enforce_crowns(net, a)
        b = S.pass1(net, qpk, np.zeros(net.n, dtype=bool), C)
        for i in range(net.n):                       # undo the sinking by hand
            if b.step_sink[i] > 0.0:
                b.inv[i] += b.step_sink[i]
                b.step_sink[i] = 0.0
        S.enforce_crowns(net, b)
        worst = max(worst, float(np.nanmax(np.abs(a.inv - b.inv))))
    assert worst == pytest.approx(0.0, abs=1e-12), \
        f"the size-step sinking moves a level by {worst:.3e} m - the reclassification is NOT free"


def test_pass_2_is_not_switched_off_by_a_bore_step():
    """`relay` skips any run containing a cliff, and that is right for a CAP cliff - re-laying
    would raise the sunk chamber back up. A bore step is different: `_walk` reproduces the
    crown match exactly, so there is nothing to undo. Counting it as a cliff dropped 47 of
    300 synthetic runs out of pass 2 with no cap anywhere in them."""
    # main run 0->4 on 4 mm/m ground with the bore stepping 200 -> 800 at chamber 2, plus a
    # long flat branch 5->4 that buries itself at the guideline minimum and so pulls the
    # junction deep. Pass 2 then has real fall to spend along the main run.
    grd = [100.0, 99.60, 99.20, 98.80, 98.40, 98.45]
    links = [(0, 1, 100.0), (1, 2, 100.0), (2, 3, 100.0), (3, 4, 100.0), (5, 4, 1400.0)]
    net = make_net(grd, links)
    qpk = np.array([4.0, 4.0, 400.0, 400.0, 400.0, 4.0])
    des = level(net, qpk)
    assert des.step_sink[2] > 0.0, "the bore step has to sink a chamber for the test"
    assert not des.capped[:5].any() and not (des.cliff[:5] > 0).any(), \
        "nothing may be capped, or skipping the run would be legitimate"

    rl = S.relay(net, des, qpk, C)
    assert rl["skipped_capped"] == 0, "the run was dropped from pass 2 for a bore step"
    assert des.absorbed[:4].all(), "every reach of the run was relaid steeper"
    assert rl["fall_recovered_m"] > 5.0, "the fall was spent ALONG the run (P1), not dropped"

    # THE COUNTERFACTUAL, so the test measures the mechanism and not a coincidence: put the
    # size-step sinking back into `cliff`, which is what the code did until 2026-09-06, and
    # the whole run leaves pass 2.
    des2 = level(net, qpk)
    des2.cliff[2] = des2.step_sink[2]
    rl2 = S.relay(net, des2, qpk, C)
    assert rl2["skipped_capped"] == 1 and not des2.absorbed[:4].any(), \
        "the counterfactual does not reproduce the defect - the test proves nothing"


# ======================================================================================
# 2. WHAT PASS 2 DID NOT DO IS A PUBLISHED ZERO, NOT AN ABSENT ROW
# ======================================================================================

def test_relay_reports_its_skips_and_fallbacks_even_when_there_are_none():
    """`skipped_capped` and `fallback_vmax` used to be created only when they fired, so the
    report carried no row at all on a clean run - and an absent row reads as *not measured*.
    That is the same argument the removal ledger makes about a blank table."""
    net = make_net([100.0, 99.5, 99.0], [(0, 1, 100.0), (1, 2, 100.0)])
    rl = S.relay(net, level(net, np.full(3, 4.0)), np.full(3, 4.0), C)
    for key in ("runs", "uniform", "late", "untouched", "skipped_capped", "fallback_cap",
                "fallback_vmax", "reaches_absorbed", "fall_recovered_m"):
        assert key in rl, f"{key} is absent, which reads as 'not measured'"


# ======================================================================================
# 3. THE REMOVAL LEDGER MUST DESCRIBE THE DESIGN THAT IS PUBLISHED
# ======================================================================================

def test_the_removal_ledger_is_read_off_the_published_design_not_the_pass_trace():
    """The prune REPLACES `des` with a design built inside `_breaches`. A ledger that read
    `trace[-1]` reported the drops of a design that was thrown away, so on any run with a
    pruned station `added - removed` did not equal `published`. Now both come from the
    design's own `drop_ledger`, and the identity holds by construction."""
    net, qpk = _branched(3)
    des, trace, _sites = S.solve(net, qpk, C, verbose=False)
    r = des.notes["removed"]
    assert "drop_ledger" in des.notes, "the published design carries its own counts"
    assert r["drops_added_pass1"] - r["drops_removed_pass2"] == r["drops_published"]
    assert r["vortex_added_pass1"] - r["vortex_removed_pass2"] == r["vortex_published"]
    assert r["drops_published"] == int((des.drop > C.DROP_TRIGGER).sum())
    assert r["stations_added"] - r["stations_pruned"] == r["stations_published"]
    assert len(trace), "the pass trace still exists - the ledger does not replace it"


def test_the_published_station_sites_say_which_of_them_survived_the_prune():
    """`station_sites` is the PRE-PRUNE list - every site the cap passes ever proposed. It is
    published beside a station count taken AFTER the prune, and a stage reading the wrong one
    is exactly how W11b came to have two station counts: 14 demanded and 47 designed
    (inheritance row 10). Every row now says whether it survived."""
    n = 40
    grd = [100.0 - 0.001 * i for i in range(n + 1)]      # flat: the pipe buries itself at
    net = make_net(grd, [(i, i + 1, 100.0) for i in range(n)])   # the guideline minimum
    qpk = np.full(net.n, 4.0)
    des, _trace, sites = S.solve(net, qpk, C, verbose=False)

    assert len(sites), "the 12 m cap has to be breached for this test to mean anything"
    for col in ("PUBLISHED", "PRUNED"):
        assert col in sites.columns, f"{col} missing - the pre-prune list ships unlabelled"
    named = sites[sites.NODE != ""]
    assert ((named.PUBLISHED + named.PRUNED) == 1).all(), "the funnel must partition"
    assert int(named.PUBLISHED.sum()) == des.notes["removed"]["stations_published"], \
        "the surviving sites and the published station count must be ONE number"
    assert int(named.PRUNED.sum()) == des.notes["removed"]["stations_pruned"]


# ======================================================================================
# 4. NOT FIXED - PINNED. Rounding the ground arm UP accumulates and nothing takes it back.
# ======================================================================================

def test_rounding_the_ground_arm_up_accumulates_with_no_mechanism_to_recover_it():
    """AN OPEN DEFECT, MEASURED AND PINNED so it cannot be lost.

    The ground arm lays `ceil_step(s_ground)`, which is up to half a 0.05 % step - 0.25 mm/m
    - steeper than the ground it claims to follow. The rounding is justified by H3: rounding
    DOWN would put a reach that starts at exactly 1.30 m of cover below it at the far end.
    But the cover-recovery term that used to give the depth back was removed in the same
    change, so nothing ever reclaims it: cover is now MONOTONE NON-DECREASING and the excess
    integrates along the whole path at about 0.25 m per kilometre.

    On a 10 km path on 5.01 mm/m ground the pipe is laid at 5.50 mm/m and arrives 4.9 m
    deeper than the ground it is following, for no engineering reason at all. That is depth
    that pushes chambers towards the 12 m cap, and the cap buys pumping stations.

    THE FIX IS A RULE CHANGE, NOT A BUG FIX - lay the nearest step and step up only where the
    downstream end would otherwise lose cover - and it belongs to the engineer, so this test
    asserts the CURRENT behaviour and will fail the day somebody changes it."""
    n_reach, L, sg = 100, 100.0, 0.00501            # just past the 5.00 mm/m grid point
    grd = [400.0 - sg * L * i for i in range(n_reach + 1)]
    net = make_net(grd, [(i, i + 1, L) for i in range(n_reach)])
    qpk = np.full(net.n, 4.0)
    des = level(net, qpk)

    assert str(des.clamp_by[0]) == "ground", "the ground arm is the one under test"
    assert des.slope[0] == pytest.approx(S.ceil_step(sg)) == pytest.approx(0.0055)
    head = C.cover(int(des.dn[0]), float(net.grd[0] - des.inv[0]))
    tail_inv = des.inv[n_reach - 1] - L * des.slope[n_reach - 1]
    tail = C.cover(int(des.dn[n_reach - 1]), float(net.grd[n_reach] - tail_inv))
    assert head == pytest.approx(C.MIN_COVER_CROWN), "the head starts at minimum cover"
    gratuitous = tail - head
    assert gratuitous == pytest.approx((S.ceil_step(sg) - sg) * L * n_reach, abs=1e-6)
    assert gratuitous > 4.5, (
        f"10 km of 5.01 mm/m ground buys {gratuitous:.2f} m of depth from ROUNDING alone")
    # and nothing takes it back: cover never decreases anywhere along the chain
    covs = [C.cover(int(des.dn[i]), float(net.grd[i] - des.inv[i]))
            for i in range(n_reach)]
    assert all(covs[i + 1] >= covs[i] - 1e-9 for i in range(len(covs) - 1)), \
        "cover is monotone non-decreasing - there is no recovery mechanism left"
