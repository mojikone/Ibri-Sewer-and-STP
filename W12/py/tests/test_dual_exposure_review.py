"""The dual-carriageway exposure table, and the filter that made it read zero.

WHY THIS FILE EXISTS.  On 2026-09-06 `s1_roads.measure_dual_exposure` was introduced to
answer the as-built calibration gate - "<= 0.2 % at a 4 m buffer; PUBLISH THE BUFFER" - and
it published, on the manifest and in the run log and in the module header:

    0.0000 % of the routable length at a 4 m buffer - ZERO corridors

That was not a measurement.  The function judged a line only when at least
`IN_BAND_MIN_FRAC` (0.99) of it lay inside the band, and then charged the WHOLE line to the
answer.  That rule is correct at exactly ONE width - 6 m - because `split_at_band` cuts
every line at the 6 m band before it is judged, so an in-band piece scores 1.0 there and
nowhere else.  At 4 m and at 10 m the filter silently refused to judge, and the table
stopped moving with the buffer, which is the single thing it exists to show.

Measured on the in-band RUN instead, on the same geometry:

    4 m   0 runs /     0.0 m  ->   1 run  /    17.8 m  (0.0000 % -> 0.0010 %)
   10 m  13 runs /   788.3 m  ->  69 runs / 3,602.5 m  (0.0433 % -> 0.1981 %)

The 4 m zero was 9DF3.1 - the single largest retained H1 breach in the project, the 23.1 m
line that is the only drawn link to 285.87 km carrying 10,168 m3/d - lying 17.75 m inside
the 4 m band at 9.9 deg and being skipped because the other 5.3 m of it was outside.  A
filter that decides without measuring is the same defect `tag_dual` was corrected for on
the same day, and this one was reporting a clean pass against the project's own gate.

Every check below re-derives its number FROM THE GEOMETRY, never from the column it is
checking.  A test that reads the published answer and asserts the published answer is the
fabricated-column defect wearing a test's clothes.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from conftest import layer, layer_names, require_gpkg

ROAD_REC = (r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\SHP"
            r"\Road centerline 2\Road_Centercline.shp")


# --------------------------------------------------------------------------------------
# the geometry these checks are re-derived from
# --------------------------------------------------------------------------------------

def _manifest(key: str):
    import sqlite3
    import pandas as pd
    con = sqlite3.connect(str(require_gpkg(key)))
    try:
        return pd.read_sql("SELECT * FROM manifest", con).set_index("ITEM")["VALUE"]
    finally:
        con.close()


def _carriageways():
    """The tagged `dual = 1` centrelines, read from the client's own record."""
    import os
    import geopandas as gpd
    if not os.path.exists(ROAD_REC):
        pytest.skip(f"{ROAD_REC} not readable - the dual tag lives there and nowhere else")
    rec = gpd.read_file(ROAD_REC)
    d1 = [g for g in rec[rec["dual"] == 1].geometry.values if g is not None]
    if not d1:
        pytest.skip("the recorded centrelines tag no dual carriageway")
    return d1


def _bearing(line, at, half=2.0):
    a = line.interpolate(max(0.0, at - half))
    b = line.interpolate(min(line.length, at + half))
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x))


def _runs(lines, d1, tree, width, skew):
    """Classify every IN-BAND RUN of every line at this buffer.

    The unit is the run, not the line: a line is cut at the 6 m band and at nothing else, so
    at any other buffer only part of it lies inside and only that part may be charged to the
    answer.  Returns (along_m, along_n, xing_m, xing_n, overlap_m, worst_along).
    """
    from shapely.ops import unary_union

    band = unary_union([g.buffer(width) for g in d1])
    am = xm = ov = 0.0
    an = xn = 0
    worst = None
    for cid, s in lines:
        if s is None or s.length <= 0 or not s.intersects(band):
            continue
        inter = s.intersection(band)
        parts = ([inter] if inter.geom_type == "LineString"
                 else [p for p in getattr(inter, "geoms", []) if p.geom_type == "LineString"])
        for p in parts:
            ov += p.length
            if p.length <= 1e-3:            # the band edge at a split point, not geometry
                continue
            mid = p.interpolate(0.5, normalized=True)
            g = d1[tree.nearest(mid)]
            ang = abs((_bearing(p, p.length * 0.5)
                       - _bearing(g, g.project(mid), half=5.0) + 90.0) % 180.0 - 90.0)
            if ang >= (90.0 - skew):
                xn += 1
                xm += p.length
            else:
                an += 1
                am += p.length
                if worst is None or p.length > worst[1]:
                    worst = (cid, p.length, ang)
    return am, an, xm, xn, ov, worst


@pytest.fixture(scope="module")
def exposure():
    if "dual_exposure" not in layer_names("roads"):
        pytest.skip("W12_roads.gpkg has no `dual_exposure` table - run s1_roads.py again")
    return layer("roads", "dual_exposure")


@pytest.fixture(scope="module")
def geometry():
    from shapely.strtree import STRtree
    cor = layer("roads", "corridors")
    d1 = _carriageways()
    lines = list(zip(cor.CID.astype(str), cor.geometry.values))
    return lines, d1, STRtree(d1), float(sum(g.length for g in cor.geometry.values))


# --------------------------------------------------------------------------------------
# THE DEFECT ITSELF
# --------------------------------------------------------------------------------------

@pytest.mark.published
def test_exposure_is_measured_on_the_in_band_run_not_on_the_whole_line(exposure, geometry):
    """THE REGRESSION. Re-measure every published buffer from the geometry and compare.

    This is the check that would have caught "0.0000 % at 4 m - ZERO corridors": the whole
    disagreement was 17.75 m of 9DF3.1 lying inside the 4 m band that the whole-line filter
    refused to look at. The tolerance is 0.1 m, which is a WRITING tolerance - both sides
    are the same shapely intersection of the same geometry, so anything larger is a
    different definition, not a rounding difference.
    """
    lines, d1, tree, tot = geometry
    skew = float(_manifest("roads")["DUAL_XING_SKEW_DEG"])
    bad = []
    for _, r in exposure.iterrows():
        w = float(r.BUFFER_M)
        am, an, xm, xn, ov, worst = _runs(lines, d1, tree, w, skew)
        print(f"\n    [{w:4.1f} m] published ALONG {int(r.ALONG_N):3d} / {r.ALONG_M:8.1f} m "
              f"| re-measured {an:3d} / {am:8.1f} m "
              f"| OVERLAP published {r.OVERLAP_M:8.1f} re-measured {ov:8.1f}"
              + (f" | worst ALONG run {worst[0]} {worst[1]:.2f} m at {worst[2]:.1f} deg"
                 if worst else ""))
        if abs(am - float(r.ALONG_M)) > 0.1:
            bad.append(f"{w:g} m: ALONG_M published {r.ALONG_M} m, measured on the in-band "
                       f"run {am:.1f} m")
        if abs(ov - float(r.OVERLAP_M)) > 0.1:
            bad.append(f"{w:g} m: OVERLAP_M published {r.OVERLAP_M} m, measured {ov:.1f} m")
    assert not bad, (
        "the published exposure disagrees with the geometry it claims to measure:\n  "
        + "\n  ".join(bad)
        + "\nThis is how 0.0000 % at a 4 m buffer was published against the <= 0.2 % gate: "
          "a line was judged only when >= IN_BAND_MIN_FRAC of it lay inside the band, which "
          "is true at the 6 m split width and at no other.")


@pytest.mark.published
def test_the_answer_moves_with_the_buffer(exposure):
    """`_BRAIN/10_ASBUILT_CALIBRATION.md`: "PUBLISH THE BUFFER (1 chamber at 4 m becomes 12
    at 10 m)". A wider buffer can only ever contain more, so overlap must be monotone. The
    broken table was flat where it should have climbed - 0.0433 % at 10 m against 0.1981 %
    measured - and a monotone table that barely moves is the signature of a filter, not of
    geometry."""
    e = exposure.sort_values("BUFFER_M").reset_index(drop=True)
    ov = e.OVERLAP_M.to_numpy(float)
    assert (np.diff(ov) > 0).all(), (
        f"overlap must grow with the buffer and does not: {list(zip(e.BUFFER_M, ov))}. A "
        f"wider band contains everything the narrower one did.")
    assert (e.ALONG_M.to_numpy(float) <= ov + 1e-6).all(), (
        "ALONG_M exceeds OVERLAP_M at some buffer - the bearing-filtered subset cannot be "
        "longer than every metre inside the band. Something is charging whole lines again.")


@pytest.mark.published
def test_the_gate_is_quoted_in_the_gates_own_quantity(exposure):
    """The <= 0.2 % gate and the built network's 0.0820 % come from
    `asbuilt.dual_overlap_m`, which measures metres inside a 4 m buffer over total length
    WITH NO BEARING TEST - a crossing counts. ALONG_PCT is bearing-filtered and is a
    different measurement, so quoting it against that gate compares two things.

    This test does NOT assert the gate passes: H1 is absolute and the retained set is an
    open breach. It asserts that the number offered to the gate is the gate's own."""
    from w12.criteria import DEFAULT as C
    row = exposure[exposure.BUFFER_M == 4.0]
    if row.empty:
        pytest.skip("no 4 m row - the gate is stated at 4 m")
    row = row.iloc[0]
    built = 100.0 * C.BENCHMARKS["DUAL_SHARE_BUILT"][0]
    print(f"\n    [gate] ours {row.OVERLAP_PCT:.4f} % (overlap, 4 m) vs the built network's "
          f"0.0820 % and criteria's benchmark {built:.4f} %; gate <= 0.2 %. "
          f"Bearing-filtered ALONG at the same buffer: {row.ALONG_PCT:.4f} %")
    assert "OVERLAP_PCT" in exposure.columns, (
        "the exposure table publishes no OVERLAP_PCT, so the only number available to quote "
        "against a gate defined without a bearing test is a bearing-filtered one")
    assert float(row.OVERLAP_PCT) >= float(row.ALONG_PCT), (
        "OVERLAP_PCT is below ALONG_PCT at 4 m, which cannot happen: overlap counts every "
        "metre in the band and ALONG counts a bearing-filtered subset of it")
    assert float(row.OVERLAP_PCT) <= 0.2, (
        f"{row.OVERLAP_PCT:.4f} % of the routable length lies within 4 m of a tagged dual "
        f"carriageway, against the calibration gate of <= 0.2 % "
        f"(_BRAIN/10_ASBUILT_CALIBRATION.md) and the built 2006 network's 0.0820 %")


# --------------------------------------------------------------------------------------
# THE FIXES THAT MUST STAY FIXED
# --------------------------------------------------------------------------------------

@pytest.mark.published
def test_no_published_crossing_is_off_square(geometry):
    """The other half of the same defect, fixed the same day: `tag_dual` called any in-band
    piece shorter than XING_CONTACT_MAX_M a square crossing WITHOUT reading its bearing, and
    published 12 pieces / 84.8 m as XING = 1 at 0.1 to 63.4 deg. A row that says "crosses
    squarely - measured, not assumed" must be able to prove it."""
    from shapely.strtree import STRtree
    cor = layer("roads", "corridors")
    if "XING" not in cor.columns:
        pytest.skip("corridors publishes no XING column")
    skew = float(_manifest("roads")["DUAL_XING_SKEW_DEG"])
    d1 = _carriageways()
    tree = STRtree(d1)
    bad = []
    for cid, s, x in zip(cor.CID.astype(str), cor.geometry.values, cor.XING.astype(int)):
        if x != 1:
            continue
        mid = s.interpolate(0.5, normalized=True)
        g = d1[tree.nearest(mid)]
        ang = abs((_bearing(s, s.length * 0.5)
                   - _bearing(g, g.project(mid), half=5.0) + 90.0) % 180.0 - 90.0)
        if ang < (90.0 - skew):
            bad.append(f"{cid} {s.length:.2f} m at {ang:.1f} deg")
    print(f"\n    [XING] {int(cor.XING.astype(int).sum())} crossings published; "
          f"{len(bad)} measure off square")
    assert not bad, (
        f"{len(bad)} corridors are published as square crossings but measure below "
        f"{90 - skew:g} deg to the carriageway: " + "; ".join(bad[:10]))


@pytest.mark.published
def test_the_exclusion_takes_no_load_out_of_the_routable_layer():
    """`corridors` is the PIPE_OK = 1 rows, so a plot whose nearest line was excluded leaves
    the routable layer with it and no downstream stage reports a smaller town. Q_NEAR_M3D is
    allocated over the WHOLE drawn network before rule 7 runs, so the two totals must agree.
    It is zero on this drawing; "it is zero today" is not a reason to leave it unchecked."""
    roads = layer("roads", "roads")
    cor = layer("roads", "corridors")
    qr = float(roads.Q_NEAR_M3D.sum())
    qc = float(cor.Q_NEAR_M3D.sum())
    ex = roads[roads.PIPE_OK.astype(int) == 0]
    print(f"\n    [load] roads {qr:,.1f} m3/d, corridors {qc:,.1f} m3/d, "
          f"{len(ex)} excluded lines carrying {float(ex.Q_NEAR_M3D.sum()):,.3f} m3/d "
          f"allocated and fronting {int(ex.N_PLOT.sum())} plots")
    assert abs(qr - qc) < 1e-6, (
        f"the rule 7 exclusion dropped {qr - qc:,.3f} m3/d: it must be re-allocated to the "
        f"nearest SURVIVING corridor before the exclusion, or published as a funnel row - "
        f"never left to vanish between two layers")


@pytest.mark.published
def test_every_retained_breach_still_earns_its_retention():
    """A line runs along a carriageway and is kept only because cutting it severs what sits
    behind it. That price was measured ONE LINE AT A TIME against the un-excluded graph, and
    the restore pass then changed the graph. Re-price each retained line against the state
    actually PUBLISHED: a retained breach that now strands nothing is a breach nobody needs,
    and "anything a pass can ADD, a later pass must be able to TAKE AWAY"."""
    import networkx as nx
    from collections import defaultdict

    roads = layer("roads", "roads")
    if "H1_KEEP" not in roads.columns:
        pytest.skip("roads publishes no H1_KEEP column")
    us = list(roads.US_NODE)
    ds = list(roads.DS_NODE)
    ln = roads.LEN_M.to_numpy(float)
    q = roads.Q_NEAR_M3D.to_numpy(float)
    n = len(us)

    def off_main(drop):
        keep = [i for i in range(n) if i not in drop]
        g = nx.Graph()
        g.add_nodes_from(us)
        g.add_nodes_from(ds)
        g.add_edges_from((us[i], ds[i]) for i in keep)
        lab = {}
        for k, cc in enumerate(nx.connected_components(g)):
            for x in cc:
                lab[x] = k
        tot = defaultdict(float)
        for i in keep:
            tot[lab[us[i]]] += ln[i]
        out = np.zeros(n, bool)
        if not tot:
            return out
        m = max(tot, key=tot.get)
        for i in keep:
            out[i] = (lab[us[i]] != m)
        return out

    published = {int(i) for i in np.where(roads.PIPE_OK.to_numpy(int) == 0)[0]}
    base = off_main(published)
    idle = []
    for i in np.where(roads.H1_KEEP.to_numpy(int) == 1)[0]:
        i = int(i)
        new = off_main(published | {i}) & ~base
        new[i] = False
        for k in published:
            new[k] = False
        km = float(ln[new].sum()) / 1000.0
        print(f"\n    [H1 keep] {roads.CID.iloc[i]:10s} {ln[i]:8.2f} m -> excluding it now "
              f"strands {km:9.3f} km / {float(q[new].sum()):9.1f} m3/d")
        if km <= 0.0:
            idle.append(f"{roads.CID.iloc[i]} ({ln[i]:.2f} m)")
    assert not idle, (
        f"{len(idle)} line(s) are retained as an OPEN H1 BREACH but strand nothing in the "
        f"state actually published, so the reason for keeping them no longer holds: "
        + ", ".join(idle)
        + ". The per-line price was taken before the restore pass changed the graph.")
