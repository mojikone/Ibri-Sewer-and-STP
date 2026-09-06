"""DEFECT CLASS 2 - NO-DATA TREATED AS SAFE.

The bug, twice. A flood grid's no-data is -9999, and -9999 IS FINITE, so a guard written
as `np.isfinite(v)` passed it as a real reading. It came back a second time through a
probe that searched outwards for dry ground, found none inside its cap, and returned the
cap as a distance - an unfound riverbank published as an 800 m wide channel.

The engineer settled the policy on 2026-09-03: NO DATA IS DRY HIGH GROUND. Water runs in
the wadis; ground the model never wetted is ground above the flood. That ruling makes the
first failure harmless AND the second one worse, because a "dry" answer is now always
available and a caller cannot tell a surveyed dry cell from an unmodelled one.

Every test here runs against a raster this file builds - deliberately gappy, with -9999
holes in known places - so the checks do not depend on the client's 822-million-cell
grids being present, and so the failure cases can be constructed rather than hoped for.
The one test that does read the shipped grids is marked and skips cleanly.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin                      # noqa: E402

from w12 import hazard as H                                    # noqa: E402


# ======================================================================================
# a synthetic hazard grid, built to be gappy
# ======================================================================================

RES = 3.0                # m, matching the shipped 10/25/50/500-year grids
X0, Y0 = 400_000.0, 2_600_000.0     # top-left corner, EPSG:32640
NX = NY = 80             # 240 m square


def _write_grid(path: Path, arr: np.ndarray) -> None:
    with rasterio.open(
        path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
        dtype="float32", crs=H.CRS, nodata=H.NODATA,
        transform=from_origin(X0, Y0, RES, RES),
    ) as dst:
        dst.write(arr.astype("float32"), 1)


def _xy(col: float, row: float):
    """Centre of cell (row, col) in world coordinates."""
    return X0 + (col + 0.5) * RES, Y0 - (row + 0.5) * RES


@pytest.fixture(scope="module")
def gappy_dir(tmp_path_factory):
    """A 240 m square with a class-6 channel down the middle, class 2 shoulders, and
    everything else -9999. That is the real shape of these grids: they hold no class-0
    cell, so 'dry' and 'not modelled' are the same set of cells."""
    d = tmp_path_factory.mktemp("hazard_gappy")
    a = np.full((NY, NX), H.NODATA, dtype="float32")
    a[:, 38:42] = 6.0                      # the channel, 12 m wide
    a[:, 36:38] = 2.0                      # left shoulder, modelled but shallow
    a[:, 42:44] = 2.0                      # right shoulder
    for rp in H.RETURN_PERIODS:
        _write_grid(d / H.GRID_FILES[rp], a)
    return d


@pytest.fixture(scope="module")
def all_wet_dir(tmp_path_factory):
    """No dry cell anywhere and no no-data either - the case where a search for dry ground
    must FAIL rather than return its own search radius."""
    d = tmp_path_factory.mktemp("hazard_allwet")
    a = np.full((NY, NX), 6.0, dtype="float32")
    for rp in H.RETURN_PERIODS:
        _write_grid(d / H.GRID_FILES[rp], a)
    return d


# ======================================================================================
# 1. -9999 is finite. That is the whole bug, so state it first.
# ======================================================================================

def test_the_nodata_value_is_finite_which_is_why_a_finiteness_guard_failed():
    """Not a test of our code - a test of the premise. If this ever stops being true the
    rest of this file is testing the wrong thing."""
    assert math.isfinite(H.NODATA)
    assert np.isfinite(np.float32(H.NODATA))
    assert H.NODATA == -9999.0


def test_class_conversion_maps_nodata_to_dry_not_to_a_class():
    """`_to_classes` is the one place a raw float becomes a hazard class. -9999 must come
    out as 0 (dry), never as a negative class and never as a finite reading."""
    a = np.array([[H.NODATA, 1.0, 6.0], [-9999.0, 3.0, H.NODATA]], dtype="float32")
    cls = H.HazardGrids._to_classes(a, "unit test")
    assert cls.dtype == np.int8
    assert cls.tolist() == [[0, 1, 6], [0, 3, 0]]
    assert (cls >= 0).all(), "a no-data cell became a negative class"


def test_class_conversion_refuses_a_resampled_read():
    """These GeoTIFFs carry AVERAGE-built overviews, so a decimated read returns fractional
    classes like 1.0046 and every `== 5` test in the pipeline silently fails. That must
    raise, not round."""
    a = np.array([[1.0046296, 5.0]], dtype="float32")
    with pytest.raises(H.HazardDataError, match="non-integer hazard classes"):
        H.HazardGrids._to_classes(a, "unit test")


def test_a_gappy_grid_reads_as_dry_and_the_channel_still_reads_wet(gappy_dir):
    """The point of the gappy fixture: two thirds of it has no model result, and that
    ground must sample as DRY while the modelled channel still samples as class 6."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        x, y = _xy(39, 40)                        # mid-channel
        assert hg.sample(x, y, rp=50).hazard_class == 6
        assert hg.in_channel(x, y, rp=50)
        assert hg.scour_risk(x, y, rp=50)         # class 6 is in HAZARD_WADI_CLASSES

        x, y = _xy(5, 40)                         # deep in the no-data field
        s = hg.sample(x, y, rp=50)
        assert s.hazard_class == 0 and not s.is_wet
        assert not hg.in_channel(x, y, rp=50)
        row = s.as_row()
        assert "DRY" in str(row.get("HAZ_ND", "")).upper(), (
            "the sample must SAY that its dryness came from the no-data rule, not just "
            "report a clean 0 - that is the difference between a measurement and a policy")


def test_outside_the_footprint_is_dry_and_says_so(gappy_dir):
    """A point off the raster is dry under the same rule, but `in_extent` must be able to
    tell the two apart - a check that silently scores off-grid points as dry is how a wadi
    result gets reported on ground the model never covered."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        far_x, far_y = X0 + 10_000.0, Y0 - 10_000.0
        assert int(hg.sample_many([far_x], [far_y], rp=50)[0]) == 0
        assert not bool(hg.in_extent_many([far_x], [far_y], rp=50)[0])
        assert bool(hg.in_extent_many([_xy(39, 40)[0]], [_xy(39, 40)[1]], rp=50)[0])


# ======================================================================================
# 2. THE PROBE. The cap is never returned as a distance.
# ======================================================================================

def test_dry_search_never_returns_its_own_cap_as_a_distance(all_wet_dir):
    """The second occurrence of the bug: nothing dry inside the search radius, so the
    radius itself was published as a channel width. The contract is found=False and
    distance_m=None."""
    with H.HazardGrids(hazard_dir=all_wet_dir) as hg:
        x, y = _xy(40, 40)
        dg = hg.distance_to_dry(x, y, rp=50, max_search_m=30.0)
        assert dg.found is False
        assert dg.distance_m is None, (
            f"distance_m came back {dg.distance_m} with found=False - a cap reported as a "
            "measurement is exactly the 800 m channel defect")
        assert "NOT a measurement" in dg.reason
        assert dg.searched_m == 30.0          # what was searched IS reported, separately


def test_dry_search_flags_a_no_data_target_as_such(gappy_dir):
    """A hit on unmodelled ground is a legitimate answer under the engineer's ruling and it
    is NOT the same statement as surveyed dry ground. Every answer must say which."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        x, y = _xy(40, 40)                    # mid-channel, class 6
        dg = hg.distance_to_dry(x, y, rp=50, max_search_m=200.0)
        assert dg.found and dg.distance_m is not None
        assert dg.target_is_nodata is True
        assert dg.target_class == 0
        assert "NO MODEL RESULT" in dg.reason
        assert dg.target_is_modelled_dry is False


def test_asking_for_the_bank_lands_on_modelled_ground(gappy_dir):
    """`dry_below_class=channel_class` asks for the nearest ground OUTSIDE the running
    channel - the bank - which is what a router actually wants, and it can land on
    modelled H1/H2 ground instead of on the edge of the modelled domain."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        x, y = _xy(40, 40)
        dg = hg.distance_to_dry(x, y, rp=50, max_search_m=100.0,
                                dry_below_class=hg.channel_class)
        assert dg.found and dg.target_is_nodata is False
        assert dg.target_class is not None and 0 < dg.target_class < hg.channel_class
        assert dg.target_is_modelled_dry is True
        # the shoulder is two cells away from cell 40; centres 3 m apart
        assert 3.0 <= dg.distance_m <= 12.0, dg.distance_m


def test_require_modelled_refuses_a_no_data_answer(gappy_dir):
    """With `require_modelled=True` and no modelled dry cell in range, the honest answer is
    'the model reported nothing dry near this point' - not a distance."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        x, y = _xy(40, 40)
        dg = hg.distance_to_dry(x, y, rp=50, max_search_m=4.0,
                                dry_below_class=hg.channel_class, require_modelled=True)
        assert dg.found is False and dg.distance_m is None
        assert "require_modelled" in dg.reason


def test_require_modelled_at_the_default_threshold_is_refused_up_front(gappy_dir):
    """These grids hold no class-0 cell, so 'modelled AND below class 1' is empty by
    construction. Asking for it must raise rather than silently return found=False for a
    reason the caller will misread as 'there is no dry ground here'."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        with pytest.raises(ValueError, match="no class-0 cell"):
            hg.distance_to_dry(*_xy(40, 40), rp=50, require_modelled=True)


def test_a_start_point_already_dry_returns_zero_not_a_search(gappy_dir):
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        dg = hg.distance_to_dry(*_xy(5, 40), rp=50, max_search_m=100.0)
        assert dg.found and dg.distance_m == 0.0 and dg.start_was_dry


def test_a_search_running_off_the_grid_is_flagged(gappy_dir):
    """Ground beyond the footprint is dry under the no-data rule, but it cannot be
    measured. The answer stays valid; the flag lets a caller decide."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        dg = hg.distance_to_dry(*_xy(40, 2), rp=50, max_search_m=200.0)
        assert dg.clipped_by_extent is True


# ======================================================================================
# 3. Along a line - the wadi test the design actually runs
# ======================================================================================

def test_a_line_crossing_the_channel_measures_a_crossing_not_a_run(gappy_dir):
    """H1a: a crossing is legal, running ALONG a wadi is not. The profile must be able to
    tell them apart, and a line over mostly-unmodelled ground must not report itself as
    mostly wet."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        y = Y0 - 40 * RES
        across = [(X0 + 10.0, y), (X0 + 230.0, y)]              # west to east, crosses
        lh = hg.profile(across, rp=50, step_m=1.0)
        assert lh.length_m > 200.0
        assert 0.0 < lh.channel_length_m < 30.0, lh.channel_length_m
        assert lh.dry_length_m > lh.wet_length_m
        assert not lh.runs_along_channel

        x = X0 + 39.5 * RES
        along = [(x, Y0 - 10.0), (x, Y0 - 230.0)]               # straight down the channel
        lh2 = hg.profile(along, rp=50, step_m=1.0)
        assert lh2.channel_length_m > 0.8 * lh2.length_m
        assert lh2.runs_along_channel


def test_wadi_classes_come_from_the_criteria_not_from_this_module(gappy_dir):
    """philosophy sec 3: HAZARD_WADI_CLASSES = (4, 5, 6) is a PROJECT ASSUMPTION standing
    in for G203's 'areas subject to washout'. Move it and the sampler must move."""
    from w12.criteria import DEFAULT, replace
    strict = replace(DEFAULT, HAZARD_WADI_CLASSES=(6,))
    with H.HazardGrids(hazard_dir=gappy_dir) as base, \
         H.HazardGrids(hazard_dir=gappy_dir, crit=strict) as alt:
        assert alt.scour_class >= base.scour_class
        x, y = _xy(36, 40)                                       # the class-2 shoulder
        assert not base.scour_risk(x, y, rp=50)
        assert not alt.scour_risk(x, y, rp=50)
        assert base.scour_class == min(DEFAULT.HAZARD_WADI_CLASSES)


def test_the_nodata_ruling_cannot_be_silently_reversed(gappy_dir):
    """Reversing 'no data is dry' changes every wadi statement in the design. The module
    refuses rather than quietly producing a different answer."""
    with pytest.raises(ValueError, match="not implemented"):
        H.HazardGrids(hazard_dir=gappy_dir, nodata_is_dry=False)


def test_a_grid_in_the_wrong_crs_is_refused(tmp_path):
    """Every W12 coordinate is EPSG:32640 and this module does not reproject. A grid in
    another CRS would sample the wrong cells and report a clean answer."""
    a = np.full((10, 10), 3.0, dtype="float32")
    with rasterio.open(tmp_path / H.GRID_FILES[50], "w", driver="GTiff", height=10,
                       width=10, count=1, dtype="float32", crs="EPSG:4326",
                       nodata=H.NODATA,
                       transform=from_origin(56.0, 23.5, 0.001, 0.001)) as dst:
        dst.write(a, 1)
    with H.HazardGrids(hazard_dir=tmp_path) as hg:
        with pytest.raises(H.HazardDataError, match="EPSG:32640"):
            hg.src(50)


def test_an_unheld_return_period_names_the_substitution(gappy_dir):
    """G201-p85 asks for a 1-in-20 at a wadi crossing and we do not hold one. Asking for 20
    must fail with the substitution named, not fall back to the nearest grid."""
    with H.HazardGrids(hazard_dir=gappy_dir) as hg:
        with pytest.raises(ValueError, match="SUBST-HAZ-1"):
            hg.sample(*_xy(40, 40), rp=20)


# ======================================================================================
# 4. The shipped grids, if they are on this machine
# ======================================================================================

@pytest.mark.slow
def test_shipped_grids_carry_only_nodata_and_classes_1_to_6():
    """EVIDENCE_NO_CLASS_ZERO, re-checked on a sample rather than taken on trust: the
    whole 'dry == not modelled' argument rests on there being no class-0 cell."""
    try:
        hg = H.HazardGrids()
    except Exception as e:                                    # noqa: BLE001
        pytest.skip(f"shipped hazard grids not available here: {e}")
    with hg:
        try:
            s = hg.src(50)
        except FileNotFoundError as e:
            pytest.skip(str(e))
        assert float(s.nodata) == H.NODATA
        from rasterio.windows import Window
        seen = set()
        for r0, c0 in ((20000, 30000), (30000, 40000), (40000, 20000)):
            block = s.read(1, window=Window(c0, r0, 512, 512))
            seen.update(np.unique(block).tolist())
        assert seen <= {H.NODATA, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0}, sorted(seen)
        print(f"\n    [shipped grid] 3 x 512x512 windows hold only {sorted(seen)}")
