"""The three defects found in the levels/flows pair on 2026-09-06, each with the test that
would have caught it.

    A.  A CACHE THAT ROUNDS ITS KEY ANSWERS A QUESTION NOBODY ASKED.  `s6_levels.vmax_slope`
        was keyed on the peak flow ROUNDED TO 0.1 L/s, with the written justification that
        "0.1 L/s moves the cap by far less than one 0.05 % gradient step".  Measured on this
        network that is false: of 471 sampled (bore, 0.1 L/s) keys holding more than one
        flow, 133 - 28.2 % - give a DIFFERENT grid cap at the two ends of the same key, the
        widest by 8.50 mm/m, seventeen steps.  So the cap a reach was designed against was
        whichever value the FIRST reach into that key happened to produce, and the build
        process and the --verify process walk the reaches in a different order.  One reach,
        E0014065, was laid at 236.00 mm/m and then failed its own stage's velocity-cap check
        against a 235.50 mm/m ceiling.  Neither number was unsafe - the reach runs at 2.9992
        m/s, inside G203-p27's 3.0 - but a ceiling that moves with the call order is not a
        ceiling, and a check that fails on a design that is right trains people to ignore
        checks.

    B.  A MEMO THAT MUST NOT BECOME THE SAME DEFECT.  The stage now memoises
        `hydra.pipe_state` on the EXACT (bore, gradient, flow) so the prune's 903
        leave-one-out trials stop re-solving the same Colebrook bisection.  The moment that
        key rounds anything, defect A is back with a bigger blast radius, so the memo is
        tested for EQUALITY against hydra, not for closeness.

    C.  A FLAG COLUMN THAT COULD ONLY EVER SAY YES.  `s5_flows` published nodes.DELIVERED
        from `Forest.reaches_outfall`, which is set on every node that reaches A TERMINAL -
        and in a forest that is every node.  The column read 1 on all 10,183 rows while the
        arc column, computed correctly beside it, read 0 on 184 arcs.  This is the ANGLE_DEG
        = 90 defect in a boolean, and `test_columns.py`'s constant-column ratchet does not
        reach it because its `_MEASURED_NAME` pattern only guards names that look like
        measurements.  Reported there rather than edited - that file is not this task's own.

    D.  AND ONE COMPARISON THAT WAS NOT LIKE FOR LIKE.  The stage's drops were being read as
        4,852 over 1,485.4 km = 3.27/km against the built network's 1.91/km, i.e. we place
        more drops than NAMA did.  We do not.  NAMA's 121 are DROP STRUCTURES - a backdrop or
        a vortex shaft, which by G203-p30 exist only above a 0.60 m step - and ours counts
        every invert step of any size, including 1,023 that are the crown step at a size
        change where nothing fell at all.  On the same basis W12 publishes 82 over 0.60 m in
        1,485.4 km, 0.055/km.  `drop_reason_table` already computes PER_KM on the right
        column; this pins it there.

Nothing here weakens a check.  Every threshold is read from `w12.criteria` or `w12.contract`,
or derived from G203 with the derivation written out.

This file reads two GeoPackages `conftest.GPKGS` does not list - `W12.gpkg`, the contract
file s6 writes, and `W12_levels.gpkg`, its diagnostics - so it opens them locally rather than
editing the shared fixture table.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pytest

from conftest import SHP_DIR, layer

LEVELS_GPKG = SHP_DIR / "W12.gpkg"            # the contract file: nodes, reaches, crossings
DIAG_GPKG = SHP_DIR / "W12_levels.gpkg"       # s6's own diagnostic tables


def _read(path, name, geom: bool = True):
    """One layer out of a GeoPackage s6 owns, or a SKIP that says which stage to run."""
    import fiona
    import geopandas as gpd

    if not path.is_file():
        pytest.skip(f"{path.name} not published - run s6_levels.py first")
    if name not in fiona.listlayers(str(path)):
        pytest.skip(f"{path.name} has no layer {name!r} - run s6_levels.py again")
    return gpd.read_file(str(path), layer=name, ignore_geometry=not geom)


_CACHE = {}


def reaches_pub():
    if "reaches" not in _CACHE:
        _CACHE["reaches"] = _read(LEVELS_GPKG, "reaches", geom=False)
    return _CACHE["reaches"]


def drop_reasons_pub():
    if "drop_reasons" not in _CACHE:
        _CACHE["drop_reasons"] = _read(DIAG_GPKG, "drop_reasons", geom=False)
    return _CACHE["drop_reasons"]


def _s6():
    import s6_levels as S
    return S


# ======================================================================================
# A + B.  The velocity cap and the memo.  Pure functions, no published file needed.
# ======================================================================================

def test_pipe_state_memo_is_bit_identical_to_hydra():
    """B. The memo is a memo, not an approximation. Equality, not a tolerance."""
    S = _s6()
    import w12.hydra as HY
    from w12.criteria import DEFAULT as C

    S._STATE_CACHE.clear()
    n = 0
    for dn in C.DN_SERIES:
        for k in (1, 3, 11, 47, 199, 500):          # gradient in whole 0.05 % steps
            for q in (0.0008, 0.0115, 0.06, 0.19):
                s = k * C.SLOPE_STEP
                want = HY.pipe_state(dn, s, q, C)
                assert S.pstate(dn, s, q, C) == want, (
                    f"the memo differs from hydra at DN{dn}, S={s}, q={q}")
                assert S.pstate(dn, s, q, C) == want, "the memo moved on the second read"
                n += 1
    assert n > 100
    print(f"\n    [memo] {n} (bore, gradient, flow) states agree with hydra exactly; "
          f"cache holds {len(S._STATE_CACHE):,}")


def test_the_velocity_cap_does_not_depend_on_which_reach_asked_first():
    """A, as a unit test. The exact regression: DN200 over the 11.45-11.55 L/s key.

    `smax` is still bucketed - it is only a seed - so populating the bucket from a
    NEIGHBOURING flow must not change the answer this flow gets.
    """
    S = _s6()
    from w12.criteria import DEFAULT as C

    probe = 0.0115001836024654               # reach E0014065's own peak flow, m3/s
    answers = {}
    for first in (0.011450, 0.011470, 0.011500, 0.011520, 0.011549):
        S._SMAX_CACHE.clear()
        S._VCAP_CACHE.clear()
        S._STATE_CACHE.clear()
        S.vmax_slope(200, first, C)          # a neighbouring flow gets there first
        answers[first] = S.vmax_slope(200, probe, C)
    got = set(answers.values())
    print("\n    [cap order] " + ", ".join(
        f"seeded at {k * 1000:.4f} L/s -> {v * 1000:.2f} mm/m" for k, v in answers.items()))
    assert len(got) == 1, (
        "the velocity cap a reach is designed against depends on which flow reached the "
        f"cache key first: {sorted(round(v * 1000, 2) for v in got)} mm/m. That is how a "
        "reach came to be laid at 236.00 mm/m and then fail --verify against 235.50.")


@pytest.mark.parametrize("dn,q_ls", [(200, 11.5001836024654), (200, 6.0), (200, 5.1),
                                     (250, 30.0), (400, 120.0), (600, 400.0)])
def test_the_cap_is_the_largest_grid_step_still_inside_three_metres_a_second(dn, q_ls):
    """A, stated as what the cap MEANS. G203-p27 sec 4.2.2.2 sets 3.0 m/s.

    Two halves, and both are needed. Too high and the design breaches a hard constraint; too
    low and the design is held back by an arbitrary number - which is what the rounded key
    was doing, and it cost the failing reach half a step of gradient it was entitled to.
    """
    S = _s6()
    import w12.hydra as HY
    from w12.criteria import DEFAULT as C

    S._SMAX_CACHE.clear()
    S._VCAP_CACHE.clear()
    q = q_ls / 1000.0
    cap: Optional[float] = S.vmax_slope(dn, q, C)
    if cap is None:
        pytest.skip(f"the 3.0 m/s cap never bites on DN{dn} at {q_ls} L/s")
    assert cap > 0
    _y, v_at = HY.pipe_state(dn, cap, q, C)
    assert v_at is None or v_at <= C.V_MAX + 1e-9, (
        f"the cap itself runs at {v_at:.4f} m/s, past G203-p27's {C.V_MAX} m/s")
    if cap < S.SLOPE_HARD_MAX - 1e-12:      # a cap held by the publishing bound is not a cap
        _y, v_up = HY.pipe_state(dn, cap + C.SLOPE_STEP, q, C)
        assert v_up is not None and v_up > C.V_MAX + 1e-9, (
            f"DN{dn} at {q_ls} L/s is capped at {cap * 1000:.2f} mm/m but the next step up "
            f"runs at {v_up:.4f} m/s, still inside {C.V_MAX} - the cap is a step too low")
    print(f"\n    [cap] DN{dn} at {q_ls:g} L/s -> {cap * 1000:.2f} mm/m, v = {v_at:.4f} m/s")


# ======================================================================================
# A, against the PUBLISHED layer.
# ======================================================================================

@pytest.mark.published
def test_no_published_reach_is_laid_past_its_own_velocity_cap():
    """A, on the deliverable. Recomputed from DN, QPK_LS and SLOPE_LAID alone.

    Deliberately the stage's own check written a second time, in another file, from the
    published columns - because the failure it was written for was the stage agreeing with
    itself and disagreeing with the layer it had just written.
    """
    import w12.hydra as HY
    from w12.criteria import DEFAULT as C

    r = reaches_pub()
    over = []
    for dn, q_ls, s_pct in zip(r.DN.astype(int), r.QPK_LS.astype(float),
                               r.SLOPE_LAID.astype(float)):
        _y, v = HY.pipe_state(int(dn), s_pct / 100.0, q_ls / 1000.0, C)
        if v is not None and v > C.V_MAX + 1e-9:
            over.append((int(dn), round(q_ls, 3), round(s_pct, 3), round(v, 4)))
    print(f"\n    [H7] {len(r):,} reaches; {len(over)} run past {C.V_MAX} m/s")
    assert not over, (
        f"{len(over)} published reaches exceed G203-p27's {C.V_MAX} m/s at their own bore, "
        f"gradient and peak flow, e.g. {over[:3]}")


@pytest.mark.published
def test_the_laid_gradient_is_never_over_the_cap_the_stage_itself_computes():
    """A, the check that failed, re-run here so a regression in `vmax_slope` shows up in the
    suite and not only in `s6_levels.py --verify`."""
    S = _s6()
    from w12.criteria import DEFAULT as C

    r = reaches_pub()
    hi = np.array([S._hi_bound(int(dn), float(q) / 1000.0, C)
                   for dn, q in zip(r.DN, r.QPK_LS)])
    d = r.SLOPE_LAID.values / 100.0 - hi
    over = d > 1e-12
    print(f"\n    [cap ceiling] {int(over.sum())} of {len(r):,} reaches sit above their own "
          f"ceiling")
    assert not over.any(), (
        f"{int(over.sum())} reaches are laid past the velocity cap computed for their own "
        f"bore and flow, worst by {float(d[over].max()) * 1000:.3f} mm/m")


# ======================================================================================
# C.  DELIVERED means the same thing on both layers of one GeoPackage.
# ======================================================================================

@pytest.mark.published
def test_delivered_is_not_a_constant_on_either_layer():
    """C. The defect was a flag that could only say yes. A 0/1 column that never says 0 on a
    layer of 10,183 rows is not a finding, it is a fabricated column."""
    n = layer("flows", "nodes")
    a = layer("flows", "arcs")
    for name, g in (("nodes", n), ("arcs", a)):
        v = g.DELIVERED.astype(int)
        assert v.nunique() > 1, (
            f"flows/{name}.DELIVERED holds {int(v.iloc[0])} on all {len(g):,} rows. Either "
            "every piece of this network drains to an outfall - in which case the "
            "`undelivered` layer is wrong - or the column is not measuring anything.")
    print(f"\n    [delivered] nodes {int(n.DELIVERED.sum()):,}/{len(n):,} delivered, "
          f"arcs {int(a.DELIVERED.sum()):,}/{len(a):,}")


@pytest.mark.published
def test_a_delivered_node_reaches_an_outfall_and_an_undelivered_one_does_not():
    """C, from the graph rather than from either column. Walk DS_NODE to the terminal and
    check what kind of terminal it is - that is the whole definition."""
    n = layer("flows", "nodes")
    uid = n.NODE_UID.astype(str).to_numpy()
    pos = {k: i for i, k in enumerate(uid)}
    succ = np.array([pos.get(s, -1) for s in n.DS_NODE.fillna("").astype(str)], dtype=np.int64)
    is_of = n.IS_OUTFALL.astype(int).to_numpy().astype(bool)

    term = succ < 0
    end = np.where(term, np.arange(len(n)), -1)
    for _ in range(len(n)):                      # a forest resolves; a cycle would not
        todo = np.flatnonzero(end < 0)
        if not len(todo):
            break
        end[todo] = np.where(end[succ[todo]] >= 0, end[succ[todo]], -1)
    assert (end >= 0).all(), (
        f"{int((end < 0).sum())} nodes never reach a terminal - H15 says the network is a "
        "forest, so this is a cycle in DS_NODE, not a levelling question")

    want = is_of[end]
    got = n.DELIVERED.astype(int).to_numpy().astype(bool)
    bad = want != got
    print(f"\n    [delivered] {int(want.sum()):,} of {len(n):,} nodes end at an outfall; "
          f"{int((~want).sum()):,} end at a dead end carrying "
          f"{float(n.loc[~want, 'Q_ADF_M3D'].sum()):,.1f} m3/d")
    assert not bad.any(), (
        f"{int(bad.sum())} nodes carrying "
        f"{float(n.loc[bad, 'Q_ADF_M3D'].sum()):,.1f} m3/d publish a DELIVERED that "
        "disagrees with where the successor map actually takes them")


@pytest.mark.published
def test_the_two_delivered_columns_are_one_definition():
    """C. An arc delivers exactly where the node it discharges into does. Written as an
    identity so the two can never drift apart again (inheritance row 10)."""
    n = layer("flows", "nodes")
    a = layer("flows", "arcs")
    nd = dict(zip(n.NODE_UID.astype(str), n.DELIVERED.astype(int)))
    ds = a.DS_NODE.astype(str)
    missing = sorted(set(ds) - set(nd))
    assert not missing, (f"{len(missing)} arcs point at a node that is not in the node "
                         f"layer: {missing[:5]}")
    want = ds.map(nd).to_numpy()
    got = a.DELIVERED.astype(int).to_numpy()
    bad = want != got
    print(f"\n    [delivered] {len(a):,} arcs; {int(bad.sum())} disagree with the node they "
          "discharge into")
    assert not bad.any(), (
        f"{int(bad.sum())} arcs publish a DELIVERED that differs from the node they "
        "discharge into. The two columns are one question and must have one answer.")


# ======================================================================================
# D.  The drop rate is compared with NAMA on NAMA's own basis.
# ======================================================================================

# The as-built figures, from _BRAIN/10_ASBUILT_CALIBRATION.md and re-measured in
# w12/asbuilt.py: 121 drop structures over 0.60 m in 63.20 km of LEVELLED built network,
# of which 120 sit at a junction.
ASBUILT_DROP_STRUCTURES = 121
ASBUILT_LEVELLED_KM = 63.20
ASBUILT_DROPS_PER_KM = ASBUILT_DROP_STRUCTURES / ASBUILT_LEVELLED_KM      # 1.914 /km
ASBUILT_STRAIGHT_RUN_PER_KM = 1.0 / ASBUILT_LEVELLED_KM                   # 1 of the 121


@pytest.mark.published
def test_the_drop_rate_is_counted_on_drop_structures_not_on_every_invert_step():
    """D. G203-p30 requires a BACKDROP above a 0.60 m step and a VORTEX SHAFT above 2.00 m.
    Below 0.60 m the step is benching inside the chamber and there is no structure to count,
    which is why the as-built figure of 1.914 drops/km is 121 structures over 63.20 km of
    levelled network and not every invert step NAMA ever laid.

    So PER_KM must be computed on the over-0.60 m count. Counting every step against NAMA's
    structures compares a benching detail with a shaft, and it turns 0.055/km into 3.27/km -
    a design that beats the benchmark 35-fold read as one that misses it by 71 %.
    """
    from w12.criteria import DEFAULT as C

    t = drop_reasons_pub()
    row = t[t.DROP_WHY == "ALL"]
    assert len(row) == 1, "the drop_reasons table has no ALL row"
    row = row.iloc[0]

    km = float(reaches_pub().LEN_M.sum() / 1000.0)
    per_km_structures = float(row.N_OVER_0P60) / km
    per_km_every_step = float(row.N) / km

    assert abs(float(row.PER_KM) - per_km_structures) < 1e-9, (
        f"PER_KM is {row.PER_KM:.4f} but the over-{C.DROP_TRIGGER:g} m count over {km:,.1f} "
        f"km is {per_km_structures:.4f}. If PER_KM is ever computed on N instead of "
        f"N_OVER_0P60 it stops being comparable with the as-built "
        f"{ASBUILT_DROPS_PER_KM:.3f}/km.")
    assert per_km_every_step > per_km_structures, "the two bases should differ; check the table"
    print(f"\n    [drops] {int(row.N_OVER_0P60):,} drop STRUCTURES over {C.DROP_TRIGGER:g} m "
          f"in {km:,.1f} km = {per_km_structures:.3f}/km   (as-built "
          f"{ASBUILT_DROPS_PER_KM:.3f}/km, {ASBUILT_DROP_STRUCTURES} in "
          f"{ASBUILT_LEVELLED_KM:.2f} km)"
          f"\n    [drops] {int(row.N):,} invert steps of ANY size = {per_km_every_step:.2f}/km "
          "- NOT the same quantity and NOT comparable with the as-built")
    assert per_km_structures <= ASBUILT_DROPS_PER_KM, (
        f"{per_km_structures:.3f} drop structures/km against the built network's "
        f"{ASBUILT_DROPS_PER_KM:.3f} - the design places MORE than NAMA did, and the drop "
        "count is the diagnostic for a tree that is not following the ground "
        "(philosophy sec 4).")


@pytest.mark.published
def test_a_drop_on_a_straight_run_is_counted_and_stays_rare():
    """D, the half of the drop comparison that IS a finding. The as-built settles that 120 of
    NAMA's 121 drops over 0.60 m sit at a junction: a drop on a straight run is a design
    levelling its way out of a layout fault."""
    t = drop_reasons_pub()
    row = t[t.DROP_WHY == "ALL"].iloc[0]
    km = float(reaches_pub().LEN_M.sum() / 1000.0)
    ours = float(row.ON_A_STRAIGHT_RUN) / km
    print(f"\n    [straight-run drops] {int(row.ON_A_STRAIGHT_RUN)} in {km:,.1f} km = "
          f"{ours:.4f}/km against the built network's "
          f"{ASBUILT_STRAIGHT_RUN_PER_KM:.4f}/km (1 of {ASBUILT_DROP_STRUCTURES})")
    assert ours <= ASBUILT_STRAIGHT_RUN_PER_KM + 1e-9, (
        f"{int(row.ON_A_STRAIGHT_RUN)} drops sit on a straight run, {ours:.4f}/km, above the "
        f"built network's {ASBUILT_STRAIGHT_RUN_PER_KM:.4f}/km. Each one is a place the "
        "ground does something the chamber spacing cannot follow, and it is a layout "
        "question, not a levelling one.")
