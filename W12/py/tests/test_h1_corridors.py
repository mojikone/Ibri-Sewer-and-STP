"""H1 / project rule 7 AT THE CORRIDOR - the checks written against the bugs that were
actually found on 2026-09-06, not against the rule in the abstract.

THE RULE.  Engineer, 2026-08-19, project rule 7: no pipe of any kind runs ALONG a dual
carriageway, trunk included, because it cannot be dug up.  A crossing is legal; running along
one is not.  Philosophy sec 3 makes it H1, a hard constraint that never yields, and sec 2
stage 2 says where it is applied: "wadi and dual-carriageway exclusions apply HERE, not in
the router."  So `corridors` - the routable set - is where this is enforced and where it is
tested.

WHAT WAS WRONG, AND WHAT EACH TEST HERE HOLDS SHUT.

  1. THE RULE LIVED IN THE SCHEMA, NOT IN THE DATA.  `PIPE_OK` was 1 on all 12,665 rows and
     `EXCL_RSN` was blank on all of them, so `corridors` was `roads` and every line the
     measurement flagged was still pipeable.
       -> test_the_routable_layer_is_exactly_the_pipeable_rows
       -> test_every_exclusion_carries_a_reason_and_a_flag

  2. THE MEASUREMENT UNDER-REPORTED ITSELF.  `tag_dual` called any in-band piece shorter
     than XING_CONTACT_MAX_M (13.24 m) a crossing WITHOUT reading its bearing.  The argument
     behind that shortcut - "a short contact IS a square crossing, by geometry" - is only
     valid for a piece that TRAVERSES the band; a piece clipping the band edge has a short
     contact at any bearing.  It published 12 pieces / 84.8 m as XING = 1, a column whose
     own field meaning says "measured, not assumed", at 0.1 to 63.4 deg.  The worst was
     6.78 m at 0.1 deg - exactly parallel - whose distance to the carriageway varied by
     0.16 m over its whole length.  Same family as the ANGLE_DEG = 90 defect.
       -> test_no_corridor_is_published_as_a_square_crossing_at_a_shallow_angle

  3. A BLANKET EXCLUSION WOULD HAVE SEVERED THE TOWN, so what survives must be DECLARED.
     Excluding every ALONG run strands 329.62 km carrying 12,105 m3/d.  What is retained is
     retained on purpose, and must say so on its own row and carry its price.
       -> test_every_surviving_breach_is_declared_and_priced

  4. THE PER-LINE PRICE CANNOT SEE A CUT SET.  Three lines that each strand nothing stranded
     0.433 km carrying 47.2 m3/d between them.
       -> test_the_exclusion_islands_nothing_that_carries_load

  5. STAGE 2 CUTS AND RENAMES, AND STAGE 8 RECOVERS THE FLAG BY A CID LOOKUP WHOSE MISS
     FILLS IN AS ZERO.  814 arcs / 109.67 km carry a CID `corridors` does not hold, and on
     every one of them `map(...).fillna(0)` published a zero that means "the lookup missed",
     not "this pipe is nowhere near a carriageway".  Same family as the no-data-read-as-safe
     defect in tests/test_nodata.py.
       -> test_the_arcs_layer_carries_the_dual_flag_at_all
       -> test_the_arcs_agree_with_the_corridors_they_came_from

  6. TWO VALUES FOR ONE QUANTITY.  Stage 2 re-measures H1 on the pieces it cuts, so it holds
     a band half-width and a skew tolerance of its own.  If they drift from stage 1's the
     two layers disagree about which pipes are legal and nothing says so.
       -> test_both_stages_judge_on_the_same_band_and_the_same_skew

NO THRESHOLD HERE IS INVENTED.  The band and the skew are read from the published manifests;
the as-built gate is quoted from `_BRAIN/10_ASBUILT_CALIBRATION.md` with its buffer, because
the answer moves with the buffer - on the built network 1 chamber within 4 m becomes 12
within 10 m.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict

import numpy as np
import pandas as pd
import pytest

from conftest import gpkg_path, layer, layer_names               # type: ignore

pytestmark = pytest.mark.published


# ======================================================================================
# helpers
# ======================================================================================

def _manifest(key: str) -> pd.Series:
    """A stage's published manifest, read off the GeoPackage rather than from memory."""
    path = gpkg_path(key)
    if not path.exists():
        pytest.skip(f"{path.name} has not been published")
    con = sqlite3.connect(path)
    try:
        m = pd.read_sql("SELECT * FROM manifest", con)
    except Exception:                                            # pragma: no cover - IO
        pytest.skip(f"{path.name} carries no manifest table")
    finally:
        con.close()
    return m.set_index("ITEM")["VALUE"]


def _num(man: pd.Series, item: str):
    if item not in man.index:
        pytest.skip(f"the manifest does not publish {item}")
    return float(man[item])


@pytest.fixture(scope="module")
def roads():
    if "roads" not in layer_names("roads"):
        pytest.skip("stage 1 has not published `roads`")
    return layer("roads", "roads")


@pytest.fixture(scope="module")
def cors():
    return layer("roads", "corridors")


@pytest.fixture(scope="module")
def arcs():
    if "arcs" not in layer_names("orient"):
        pytest.skip("stage 2 has not published `arcs`")
    return layer("orient", "arcs")


# ======================================================================================
# 1. THE RULE IS IN THE DATA
# ======================================================================================

def test_the_routable_layer_is_exactly_the_pipeable_rows(roads, cors):
    """`corridors` is defined as the PIPE_OK = 1 rows of `roads`. If the two ever drift, a
    line a pipe may not be laid along is one a router can still see - which is how a pipe
    ended up on a dual carriageway in W10."""
    assert {"PIPE_OK", "EXCL_RSN"} <= set(roads.columns), (
        "`roads` publishes no PIPE_OK / EXCL_RSN - rule 7 has nowhere to live in the data")
    keep = set(roads.loc[roads.PIPE_OK.astype(int) == 1, "CID"].astype(str))
    got = set(cors.CID.astype(str))
    print(f"\n    [rule7] roads {len(roads):,} | corridors {len(cors):,} | excluded "
          f"{len(roads) - len(cors):,} "
          f"({roads.loc[roads.PIPE_OK.astype(int) == 0, 'LEN_M'].sum():,.1f} m)")
    assert keep == got, (
        f"`corridors` is not the PIPE_OK = 1 rows of `roads`: "
        f"{len(keep - got)} pipeable rows are missing from it and {len(got - keep)} rows in "
        f"it are not pipeable")
    assert (cors.PIPE_OK.astype(int) == 1).all()


def test_every_exclusion_carries_a_reason_and_a_flag(roads):
    """A silent drop is the worst defect in this project's history. Every excluded line says
    WHY on its own row, and every one of them is a line the measurement flagged - this stage
    excludes on that measurement and on nothing else."""
    excl = roads[roads.PIPE_OK.astype(int) == 0]
    if not len(excl):
        pytest.skip("nothing is excluded, so there is no reason to check")
    blank = excl.EXCL_RSN.fillna("").astype(str).str.strip() == ""
    unflagged = excl.ALONG_DUAL.astype(int) != 1
    print(f"\n    [rule7] {len(excl):,} excluded, {excl.LEN_M.sum():,.1f} m; "
          f"{int(blank.sum())} with no reason, {int(unflagged.sum())} not flagged "
          f"ALONG_DUAL")
    assert not blank.any(), f"{int(blank.sum())} rows are excluded with no reason written on"
    assert not unflagged.any(), (
        f"{int(unflagged.sum())} rows are excluded without being flagged ALONG_DUAL")
    # and the reverse: a reason without an exclusion is a row that says it was dropped and
    # was not
    has_reason = roads.EXCL_RSN.fillna("").astype(str).str.strip() != ""
    assert (has_reason == (roads.PIPE_OK.astype(int) == 0)).all(), (
        "EXCL_RSN and PIPE_OK disagree on at least one row")


# ======================================================================================
# 2. THE MEASUREMENT DOES NOT UNDER-REPORT ITSELF
# ======================================================================================

def test_no_corridor_is_published_as_a_square_crossing_at_a_shallow_angle(cors):
    """THE FABRICATED-CROSSING REGRESSION.

    `XING` means, in its own field meaning, "this line crosses a tagged dual carriageway
    SQUARELY - measured, not assumed". A row carrying XING = 1 at a bearing below the skew
    tolerance is a crossing nobody measured, and every one of those rows is a length H1
    never got to look at. The tolerance is read from the manifest, not typed here.
    """
    if "XING" not in cors.columns:
        pytest.skip("stage 1 does not publish XING")
    man = _manifest("roads")
    skew = _num(man, "DUAL_XING_SKEW_DEG")
    square = 90.0 - skew
    x = cors[cors.XING.astype(int) == 1]
    ang = pd.to_numeric(x.DUAL_ANG, errors="coerce")
    bad = x[(ang >= 0.0) & (ang < square - 1e-9)]
    unmeasured = x[ang < 0.0]
    print(f"\n    [XING] {len(x):,} corridors published as crossing a dual carriageway; "
          f"measured bearings {ang[ang >= 0].min():.1f} to {ang[ang >= 0].max():.1f} deg "
          f"against the >= {square:.0f} deg that 'square' means "
          f"(skew {skew:.0f} deg). {len(bad)} below it, {len(unmeasured)} with no "
          f"measurement at all.")
    assert bad.empty, (
        f"{len(bad)} corridors ({bad.LEN_M.sum():.1f} m) are published as crossing a dual "
        f"carriageway SQUARELY at a measured {ang.loc[bad.index].min():.1f}-"
        f"{ang.loc[bad.index].max():.1f} deg. That is a crossing nobody measured, and it "
        f"hides that length from H1: worst offenders "
        f"{list(bad.sort_values('LEN_M', ascending=False).CID[:4])}")
    assert unmeasured.empty, (
        f"{len(unmeasured)} corridors claim to cross a dual carriageway with DUAL_ANG = -1, "
        f"the not-applicable sentinel. A check that cannot run is a FAILURE, not a blank")


# ======================================================================================
# 3. WHAT SURVIVES IS DECLARED AND PRICED
# ======================================================================================

def test_every_surviving_breach_is_declared_and_priced(cors):
    """A line still running ALONG a carriageway after the exclusion is retained on purpose -
    because cutting it severs what sits behind it - and it must say so.

    This does NOT assert the breach is empty. It cannot be: three of the survivors are the
    only drawn link across a carriageway reserve, and excluding them islands a town. The
    audit's own `test_H1_no_corridor_carries_a_pipe_along_a_dual_carriageway` is the check
    that reports the breach and it is expected to fail while any survives. What this test
    holds shut is the thing that would be worse - a breach nobody declared.
    """
    along = cors[cors.ALONG_DUAL.astype(int) == 1]
    print(f"\n    [H1 survivors] {len(along)} corridors, {along.LEN_M.sum():,.1f} m "
          f"({100 * along.LEN_M.sum() / cors.LEN_M.sum():.4f} % of the routable length)")
    if not len(along):
        return
    assert "H1_KEEP" in cors.columns, (
        f"{len(along)} corridors run ALONG a dual carriageway and the layer carries no "
        f"H1_KEEP column to declare them - an undeclared breach of a hard constraint")
    undeclared = along[along.H1_KEEP.astype(int) != 1]
    assert undeclared.empty, (
        f"{len(undeclared)} corridors run ALONG a dual carriageway without H1_KEEP = 1: "
        f"{list(undeclared.CID)}")

    # every survivor is priced, and the price is what justifies keeping it
    if "dual_exclusion" not in layer_names("roads"):
        pytest.fail("no `dual_exclusion` table - the survivors carry no price")
    ex = layer("roads", "dual_exclusion")
    kept = ex[ex.DISPOSITION.astype(str) == "retained"]
    assert set(along.CID.astype(str)) <= set(kept.CID.astype(str)), (
        "a surviving H1 breach has no row in `dual_exclusion`")
    zero = kept[pd.to_numeric(kept.STRANDS_KM, errors="coerce").fillna(0) <= 0]
    for _, r in kept.sort_values("STRANDS_KM", ascending=False).iterrows():
        print(f"      {r.CID:>10s} {float(r.LEN_M):7.1f} m at {float(r.DUAL_ANG):5.1f} deg "
              f"holds {float(r.STRANDS_KM):8.2f} km / {float(r.STRANDS_Q_M3D):8.1f} m3/d")
    assert zero.empty, (
        f"{len(zero)} retained breaches strand NOTHING, so nothing justifies keeping them: "
        f"{list(zero.CID)}")
    assert (kept.REASON.fillna("").astype(str).str.strip() != "").all(), (
        "a retained breach carries no reason")


# ======================================================================================
# 4. THE EXCLUSION CANNOT ISLAND ANYTHING THAT CARRIES LOAD
# ======================================================================================

def test_the_exclusion_islands_nothing_that_carries_load(roads, cors):
    """THE CUT-SET REGRESSION.

    The strand behind each flagged line was priced ONE LINE AT A TIME, and three lines that
    each stranded nothing stranded 0.433 km carrying 47.2 m3/d together. H15: "what is never
    legal is a piece that drains nowhere."

    Componented from the WRITTEN node id strings on both sides (H16), never from geometry.
    """
    import networkx as nx

    def off_main_load(df):
        g = nx.Graph()
        g.add_nodes_from(df.US_NODE.astype(str))
        g.add_nodes_from(df.DS_NODE.astype(str))
        g.add_edges_from(zip(df.US_NODE.astype(str), df.DS_NODE.astype(str)))
        lab = {}
        for k, cc in enumerate(nx.connected_components(g)):
            for x in cc:
                lab[x] = k
        km = defaultdict(float)
        for u, L in zip(df.US_NODE.astype(str), df.LEN_M.astype(float)):
            km[lab[u]] += L
        m = max(km, key=km.get)
        off = np.array([lab[u] != m for u in df.US_NODE.astype(str)])
        return (float(df.LEN_M.to_numpy(float)[off].sum()) / 1000.0,
                float(df.Q_NEAR_M3D.to_numpy(float)[off].sum()))

    before_km, before_q = off_main_load(roads)
    after_km, after_q = off_main_load(cors)
    print(f"\n    [islands] off the main component BEFORE the exclusion "
          f"{before_km:,.3f} km / {before_q:,.1f} m3/d; AFTER {after_km:,.3f} km / "
          f"{after_q:,.1f} m3/d")
    assert after_q <= before_q + 1e-6, (
        f"the rule 7 exclusion islanded {after_q - before_q:,.1f} m3/d that had a path to "
        f"the main component before it. A load with nowhere to drain is what H15 forbids, "
        f"and a per-line strand price cannot see a cut set - the exclusion has to be able "
        f"to take itself back")


# ======================================================================================
# 5. THE FLAG SURVIVES THE STAGE THAT CUTS
# ======================================================================================

def test_the_arcs_layer_carries_the_dual_flag_at_all(arcs):
    """`s8_export` recovers the dual flag with `map(corridor CID).fillna(0)`. A missing
    column here, or a CID the corridors layer does not hold, publishes a zero that means
    "the lookup missed" and reads as "this pipe is nowhere near a carriageway"."""
    missing = [c for c in ("ALONG_DUAL", "DUAL_ANG", "H1_KEEP") if c not in arcs.columns]
    assert not missing, (
        f"`arcs` publishes no {', '.join(missing)}. Stage 2 renames every piece it cuts, so "
        f"a downstream CID lookup misses on those rows and fills in as 0")
    al = arcs[arcs.ALONG_DUAL.astype(int) == 1]
    print(f"\n    [arcs] {len(al)} arcs / {al.LEN_M.sum():,.1f} m run ALONG a dual "
          f"carriageway; {int(arcs.H1_KEEP.astype(int).sum())} carry H1_KEEP = 1")
    bad = al[al.H1_KEEP.astype(int) != 1]
    assert bad.empty, (
        f"{len(bad)} arcs run ALONG a dual carriageway without H1_KEEP = 1 - if this "
        f"stage's CUT created them they belong back in stage 1's exclusion")


def test_the_arcs_agree_with_the_corridors_they_came_from(arcs, cors):
    """The cut must not CREATE a breach.

    Stage 2 cuts corridors at a crest and where they meet the Main Pipe, and every cut piece
    gets a new CID. The published ALONG length on `arcs` must therefore equal the ALONG
    length on `corridors` - a longer one means a cut put a piece along a carriageway that
    the whole corridor was not, and stage 2's `h1_cut_newly_along` should have said so.
    """
    a_m = float(arcs.loc[arcs.ALONG_DUAL.astype(int) == 1, "LEN_M"].sum())
    c_m = float(cors.loc[cors.ALONG_DUAL.astype(int) == 1, "LEN_M"].sum())
    man = _manifest("orient")
    newly = int(float(man["h1_cut_newly_along"])) if "h1_cut_newly_along" in man.index else -1
    cut = int(float(man["h1_cut_arcs"])) if "h1_cut_arcs" in man.index else -1
    print(f"\n    [cut] {cut:,} arcs carry a CID `corridors` does not hold and were "
          f"RE-MEASURED; {newly} of them newly ALONG. corridors {c_m:,.1f} m vs arcs "
          f"{a_m:,.1f} m")
    assert newly == 0, (
        f"stage 2's outfall/crest cut put {newly} piece(s) ALONG a dual carriageway that "
        f"the whole corridor was not. That is an H1 breach this stage CREATED")
    assert abs(a_m - c_m) <= 0.5, (
        f"the ALONG length on `arcs` ({a_m:.1f} m) differs from `corridors` ({c_m:.1f} m) "
        f"by {abs(a_m - c_m):.1f} m")


# ======================================================================================
# 6. ONE VALUE FOR ONE QUANTITY
# ======================================================================================

def test_both_stages_judge_on_the_same_band_and_the_same_skew():
    """A wall/bedding allowance was 0.10 in one module and 0.05 in another and every reach
    failed a blocking cover check by exactly 50 mm. Stage 2 re-measures H1 on the pieces it
    cuts, so it holds these three numbers too - and they have to be the same three."""
    s1 = _manifest("roads")
    s2 = _manifest("orient")
    pairs = (("DUAL_BAND_M", "h1_band_m"), ("DUAL_XING_SKEW_DEG", "h1_skew_deg"))
    bad = []
    for a, b in pairs:
        if a not in s1.index or b not in s2.index:
            continue
        va, vb = float(s1[a]), float(s2[b])
        print(f"\n    [constants] {a} = {va:g} (stage 1) | {b} = {vb:g} (stage 2)")
        if abs(va - vb) > 1e-9:
            bad.append(f"{a} = {va:g} in stage 1 but {vb:g} in stage 2")
    assert not bad, "TWO VALUES FOR ONE QUANTITY:\n  " + "\n  ".join(bad)


# ======================================================================================
# 7. THE AS-BUILT GATE, QUOTED WITH ITS BUFFER
# ======================================================================================

def test_the_along_share_is_published_at_more_than_one_buffer():
    """`_BRAIN/10_ASBUILT_CALIBRATION.md` sec 1: the built 2006 network runs along a dual
    carriageway on 0.0820 % of its length and puts 1 chamber of 3,267 within 4 m, and the
    gate is "<= 0.2 % at a 4 m buffer; PUBLISH THE BUFFER (1 chamber at 4 m becomes 12 at
    10 m)". A share quoted without its buffer says nothing, so the stage must publish more
    than one - and the 4 m figure must sit inside the gate."""
    if "dual_exposure" not in layer_names("roads"):
        pytest.skip("stage 1 does not publish `dual_exposure`")
    e = layer("roads", "dual_exposure")
    assert len(e) >= 2, "the ALONG share is published at one buffer only"
    print("")
    for _, r in e.iterrows():
        print(f"    [exposure] +/-{float(r.BUFFER_M):4.1f} m : {int(r.ALONG_N):3d} corridors "
              f"{float(r.ALONG_M):8.1f} m = {float(r.ALONG_PCT):7.4f} %")
    at4 = e[np.isclose(e.BUFFER_M.astype(float), 4.0)]
    if not len(at4):
        pytest.skip("the 4 m buffer the as-built gate is stated at is not published")
    got = float(at4.ALONG_PCT.iloc[0])
    print(f"    [gate] {got:.4f} % at a 4 m buffer, against the built network's 0.0820 % "
          f"and the <= 0.2 % gate (_BRAIN/10_ASBUILT_CALIBRATION.md sec 1)")
    assert got <= 0.2, (
        f"{got:.4f} % of the routable length runs along a dual carriageway at a 4 m buffer, "
        f"past the 0.2 % as-built gate. The built network manages 0.0820 %")
