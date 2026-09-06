"""The half of the velocity ceiling the 2026-09-06 fix did not reach, and the exemption a
check was hiding.  Adversarial review of `s6_levels.py`, 2026-09-06.

WHAT THE FIX GOT RIGHT, RE-MEASURED HERE RATHER THAN TAKEN ON TRUST.  Stage 6's check
"SLOPE_LAID never past the velocity cap" was failing on one reach (E0014065, DN200,
23.6 %, 11.5002 L/s).  The claim was that the DESIGN was right and the CEILING was wrong,
because `vmax_slope` was keyed on the flow rounded to 0.1 L/s and the cap moves inside a
bucket.  Verified independently: that reach runs at 2.9992 m/s, every one of the 56,525
published reaches is inside G203-p27's 3.0 m/s recomputed straight from `hydra`, and not
one of them is laid above the exact grid cap found by a binary search written here rather
than borrowed from the stage.  So it was a false alarm and the fix removed it honestly.

WHAT IT DID NOT REACH.  `vmax_slope` still asks the BUCKETED seed `smax` first, and when
that seed says None - "no cap anywhere" - it returns None without ever looking at the
reach's own flow.  81 % of the network's distinct (bore, flow) keys come down that branch,
and one live bucket (DN200, 4.85-4.95 L/s, 109 reaches) holds a None at one end and a real
cap at the other.  The value branch was made order-independent; the None branch was not.
It has no numeric consequence on this design - the None boundary sits at a 50 % gradient,
twice the 25 % publishing bound - which is exactly why it needs a test rather than a
paragraph: nothing else in the suite would notice it coming back.

AND ONE CHECK THAT WAS EXCUSING MORE THAN ITS TITLE SAID.  Check 28 was called "no drop
over 0.60 m on a straight run without the velocity-cap exemption" and its code also
excused 'tier_step', printing "0 chambers" beside a WANT of "MEASURED (NAMA 1 of 121)"
while 5 chambers were being excused out of the count.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

import s6_levels as S6
from w12 import hydra as HY
from w12.criteria import DEFAULT as C

from conftest import SHP_DIR  # noqa: E402

_READ = {}


def _design(name: str):
    """Read one layer of stage 6's own publication.  `conftest.GPKGS` has no key for
    W12.gpkg - it is not a file this reviewer owns - so it is opened here and a missing
    file SKIPS with the stage named, never passes quietly."""
    import fiona
    import geopandas as gpd
    p = SHP_DIR / "W12.gpkg"
    if not p.is_file():
        pytest.skip(f"{p.name} not published - run s6_levels.py first")
    if name not in _READ:
        if name not in fiona.listlayers(str(p)):
            pytest.skip(f"{p.name} has no layer '{name}' - run s6_levels.py again")
        _READ[name] = gpd.read_file(str(p), layer=name)
    return _READ[name]

STEP = S6._STEP
TOP = int(round(S6.SLOPE_HARD_MAX / STEP))


def _clear() -> None:
    S6._SMAX_CACHE.clear()
    S6._VCAP_CACHE.clear()
    S6._STATE_CACHE.clear()


def _true_grid_cap(dn: int, q: float) -> float:
    """The largest gradient on the 0.05 % grid, at or below the publishing bound, at which
    this bore carries this flow inside 3.0 m/s.  Written here from scratch - a binary
    search on a monotone predicate - so it is not the stage's own answer restated.  A
    surcharged state counts as inside the cap, because surcharge is a capacity failure at
    a gradient that is too FLAT and it is check 10's business, not this one's."""
    lo, hi, best = 1, TOP, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        _y, v = HY.pipe_state(dn, mid * STEP, q, C)
        if v is None or v <= C.V_MAX + 1e-9:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best * STEP


# ======================================================================================
# 1.  The ceiling is the reach's own, in BOTH branches
# ======================================================================================

# The live bucket, measured off the published layer on 2026-09-06: DN200, 0.1 L/s bucket
# 49, holds 109 reaches spanning 4.8503 - 4.9479 L/s, and `hydra.smax_for` is None below
# 4.9267 L/s and a real cap above it.  These are the two ends of that one bucket.
_AMBIGUOUS_DN = 200
_BELOW = 0.0048503          # m3/s - smax_for -> None
_ABOVE = 0.0049479          # m3/s - smax_for -> a real cap, same 0.1 L/s bucket


def test_the_live_bucket_really_does_straddle_the_none_boundary():
    """If this stops being true the test above it is no longer testing anything, so it is
    asserted rather than assumed."""
    assert int(round(_BELOW * 10000.0)) == int(round(_ABOVE * 10000.0)), \
        "the two probe flows are no longer in the same 0.1 L/s smax bucket"
    assert HY.smax_for(_AMBIGUOUS_DN, _BELOW, C) is None
    assert HY.smax_for(_AMBIGUOUS_DN, _ABOVE, C) is not None


@pytest.mark.parametrize("probe,other", [(_ABOVE, _BELOW), (_BELOW, _ABOVE)])
def test_vmax_slope_does_not_depend_on_who_populated_the_bucket(probe, other):
    """THE DEFECT, IN ONE ASSERTION.  Ask for `other` first, then `probe`; then ask for
    `probe` on cold caches.  The answers must agree.  Before the None branch was guarded
    the first call put a None in the bucket and the second read it back, so a reach with a
    real velocity cap was told it had none - the same order-dependence the value branch
    was fixed for on 2026-09-06, surviving in the branch 81 % of the network takes."""
    _clear()
    S6.vmax_slope(_AMBIGUOUS_DN, other, C)
    primed = S6.vmax_slope(_AMBIGUOUS_DN, probe, C)
    _clear()
    cold = S6.vmax_slope(_AMBIGUOUS_DN, probe, C)
    assert primed == cold, (
        f"vmax_slope(DN{_AMBIGUOUS_DN}, {probe}) = {primed} when the bucket was populated "
        f"by {other} and {cold} on cold caches - the ceiling moves with the call order")


@pytest.mark.parametrize("q", [_BELOW, _ABOVE, 0.0115001836024654, 0.0060, 0.030, 0.12])
def test_the_answer_is_the_true_grid_cap_whichever_branch_it_comes_down(q):
    """Whatever branch it comes down, the answer is checked against a cap computed here -
    including the branch where the bucketed seed says "no cap anywhere", which used to
    return None without ever looking at this reach's flow."""
    for dn in (200, 315, 500):
        _clear()
        got = S6.vmax_slope(dn, q, C)
        want = _true_grid_cap(dn, q)
        assert got is not None, (
            f"vmax_slope(DN{dn}, {q}) returned None; the ceiling is a number - the "
            f"publishing bound where no velocity cap bites")
        assert abs(got - want) < 1e-12, (
            f"vmax_slope(DN{dn}, {q}) = {got * 1000:.2f} mm/m against a true grid cap "
            f"of {want * 1000:.2f} mm/m")


def test_the_ceiling_the_stage_actually_applies_is_never_over_three_metres_per_second():
    """`_hi_bound` is what every caller uses, and it is the thing that must be safe: at the
    gradient it permits, the reach is inside G203-p27's 3.0 m/s."""
    for dn in (200, 250, 315, 400, 500, 600, 700, 800):
        for q in (0.0015, _BELOW, _ABOVE, 0.011, 0.05, 0.15):
            _clear()
            hi = S6._hi_bound(dn, q, C)
            _y, v = HY.pipe_state(dn, hi, q, C)
            assert v is None or v <= C.V_MAX + 1e-9, (
                f"_hi_bound(DN{dn}, {q}) = {hi} runs at {v:.4f} m/s")


# ======================================================================================
# 2.  The published design, measured rather than read back
# ======================================================================================

@pytest.mark.published
def test_no_published_reach_is_above_its_own_exact_velocity_cap():
    """The check the 2026-09-06 fix turned green, re-derived from the rows themselves with
    a cap function written in this file.  It is the one assertion that says the fix was a
    correction and not a relaxation: if the design had really been over the cap, this fails
    whatever `vmax_slope` says."""
    r = _design("reaches")
    cols = set(r.columns)
    dn_col = "DN"
    s_col = "SLOPE_LAID" if "SLOPE_LAID" in cols else "S_LAID_MM"
    q_col = "QPK_LS"
    assert {dn_col, s_col, q_col} <= cols, f"columns missing: {sorted(cols)[:20]}"
    dn = r[dn_col].to_numpy().astype(int)
    S = r[s_col].to_numpy(float) / (100.0 if s_col == "SLOPE_LAID" else 1000.0)
    q = r[q_col].to_numpy(float) / 1000.0
    # velocity first - the hard constraint - then the ceiling, on a sample, because the
    # exact cap costs a binary search per row.
    worst_v, n_over = 0.0, 0
    for i in range(len(r)):
        _y, v = HY.pipe_state(int(dn[i]), float(S[i]), float(q[i]), C)
        if v is not None:
            worst_v = max(worst_v, v)
            if v > C.V_MAX + 1e-9:
                n_over += 1
    print(f"\n    max velocity on {len(r):,} published reaches: {worst_v:.4f} m/s")
    assert n_over == 0, f"{n_over} published reaches run past {C.V_MAX} m/s (G203-p27)"
    rng = np.random.default_rng(20260906)
    for i in rng.choice(len(r), size=min(400, len(r)), replace=False):
        cap = _true_grid_cap(int(dn[i]), float(q[i]))
        assert S[i] <= cap + 1e-12, (
            f"row {i}: laid {S[i] * 1000:.2f} mm/m against an exact grid cap of "
            f"{cap * 1000:.2f} mm/m")


# ======================================================================================
# 3.  A check may not excuse a row its own title does not name
# ======================================================================================

def test_the_straight_run_drop_check_names_every_reason_it_excuses():
    """A RATCHET ON THE CHECK'S OWN WORDS.  Check 28 excused 'velocity_cap' AND 'tier_step'
    under a title that named only the velocity cap, and printed "0 chambers" while 5 were
    excused.  A reader of the verify table could not see it.  This asserts that whatever
    the code excuses, the title says so and the excused count is on the line - so the next
    exemption cannot be added invisibly."""
    src = Path(S6.__file__).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"excused = straight & why\.isin\(\(([^)]*)\)\)", src)
    assert m, "check 28 no longer has an `excused = straight & why.isin(...)` line"
    reasons = re.findall(r"\"([a-z_]+)\"|'([a-z_]+)'", m.group(1))
    reasons = [a or b for a, b in reasons]
    assert reasons, "the exemption tuple is empty - check 28 has been restructured"
    blk = src[m.end():m.end() + 1200]
    title = re.search(r'chk\(\s*("(?:[^"\\]|\\.)*"(?:\s*"(?:[^"\\]|\\.)*")*)', blk)
    assert title, "no chk() call follows the exemption tuple"
    words = title.group(1).lower()
    for reason in reasons:
        # 'velocity_cap' -> "velocity cap", 'tier_step' -> "bore step" / "tier step"
        head = reason.split("_")[0]
        assert head in words or reason in words or (head == "tier" and "bore" in words), (
            f"check 28 excuses '{reason}' and its title does not say so: {words}")
    assert "excused" in blk[:900], \
        "check 28 no longer reports how many chambers its exemptions excuse"


@pytest.mark.published
def test_the_excused_straight_run_drops_are_still_there_to_be_excused():
    """The exemption is not hypothetical: 5 chambers take a drop over 0.60 m on a straight
    run because the 3.0 m/s cap would not let the pipe spend the fall, and 3 of them are
    deep enough to need a vortex shaft (G203-p30).  The built network has none on a
    straight run.  If this ever reaches zero the check's wording can be simplified; until
    then the number belongs on the verify line, which is what the sibling test pins."""
    nd = _design("nodes")
    import pandas as pd
    d = pd.to_numeric(nd.DROP_M, errors="coerce").fillna(0.0)
    why = nd.DROP_WHY.astype(str).str.strip()
    straight = (d > 0.60) & (nd.N_IN < 2)
    print(f"\n    straight-run drops over 0.60 m: {int(straight.sum())} "
          f"({why[straight].value_counts().to_dict()}), of which over 2.00 m: "
          f"{int((straight & (d > 2.00)).sum())}")
    assert set(why[straight]) <= {"velocity_cap", "tier_step"}, (
        "a straight-run drop has appeared with a reason the check does not excuse - that "
        "is a layout fault the check is meant to catch, not a levelling one")
