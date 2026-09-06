"""THE AUDIT, WIRED UP - all 34 checks of `contract.AUDIT_NEEDS`, one test each.

WHY THIS FILE EXISTS. Run 003 published a full set of deliverables and reported:

    [readiness] 5 of 34 audit checks can run against the layers published so far
                (G3, G4, H10, H15, H16)

Philosophy sec 8 and inheritance ledger row 2 are explicit - A CHECK THAT CANNOT RUN IS A
FAILURE, NOT A BLANK - and W11a made that a founding rule after W10 shipped 45.92 km of pipe
below minimum cover with nothing looking. Five of thirty-four is therefore twenty-nine
blocking failures, not a progress bar.

WHAT THE 29 WERE ACTUALLY MISSING - and the answer is the uncomfortable one:

    NOTHING.  Every field of all 34 checks is published, today, in W12/shp.

The readiness probe in `test_invariants.py::test_which_audit_checks_can_run_at_all_is_reported`
unions columns from exactly three GeoPackages - `W12_hier`, `W12_flows`, `W12_chambers` - the
outputs of stages 3, 4 and 5. It never opens `W12.gpkg` (stage 6: every level, diameter and
gradient), `W12_export.gpkg` (stage 8), `W12_levels.gpkg` or `W12_pumps.gpkg` (stage 7).
`conftest.GPKGS` has no key for the first three of those, so no test in the suite could have
opened them. The probe was written while stage 6 was still unpublished - its own docstring
says so - and it was never revisited once the stage ran. It measured its own blind spot and
reported it as the design's.

So the 29 break down as:

    29  a readiness probe pointed at three of the eight published GeoPackages
     0  a missing layer
     0  a missing column
     0  a missing external input   (all five verified present on disk, below)
     0  a check written against a schema that no longer exists

and separately - the part that actually mattered - 22 of the 34 had NO TEST WRITTEN AT ALL,
runnable or not. A check declared in `AUDIT_NEEDS` and implemented nowhere is the same blank
by a different route. This file implements every one of them.

WHAT THIS FILE DOES NOT DO. It does not edit a stage. Where a check fails, that is a FINDING,
published with its size. Two checks - H1 and H10 - already carry a blocking assertion in
`test_invariants.py` and are being fixed in parallel; here they are MEASURED on the design
layer and cross-referenced, never re-asserted, so the fix lands in one place.

WHICH LAYER IS "THE DESIGN". `W12.gpkg` - stage 6's published reaches and nodes.

    HISTORY, because the number moved under this file. When these checks were first wired,
    `s8_export` built a SECOND set of levels from a stand-in inherited from W11b and the two
    published reach layers disagreed by a factor of four - 19.98 m deepest cover against
    85.71 m, a 10.17 m largest drop against 83.09 m. `s8` has since been repointed at
    `W12.gpkg` and they now agree to the centimetre.
    `test_the_two_published_reach_layers_are_one_design` is what measured the divergence and
    it stays as the regression that catches a second set of levels reappearing.

BUT "EVERY H-CHECK READS W12.gpkg" IS NOT TRUE, AND WAS NOT TRUE WHEN IT WAS FIRST WRITTEN
HERE. `role()` returns the first published layer carrying the fields a check asks for, so a
check whose field stage 6 does not publish moves to stage 8's output with nothing said. H1a's
condition 2 does exactly that - `W12.gpkg/nodes` has no ON_WADI, so 3,326 chambers on wadi
ground are counted off the stage-8 layer. Every resolution is now recorded in `RESOLVED`,
published by `test_which_published_layer_every_check_actually_read`, and any fall-through not
declared in `ACCEPTED_FALLTHROUGH` fails that test.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pytest

# --- paths (deliberately independent of conftest, which does not know these files) -----
TESTS_DIR = Path(__file__).resolve().parent
PY_DIR = TESTS_DIR.parent
W12_ROOT = PY_DIR.parent
SHP_DIR = W12_ROOT / "shp"
RUN_DIR = W12_ROOT / "run"
AUDIT_DIR = RUN_DIR / "audit"

if str(PY_DIR) not in sys.path:
    sys.path.insert(0, str(PY_DIR))


# ======================================================================================
# THE PUBLISHED SET - every GeoPackage the eight stages write, and which stage writes it
# ======================================================================================

GPKGS: Dict[str, Tuple[str, str]] = {
    #  key          file                       stage that writes it
    "roads":     ("W12_roads.gpkg",     "s1_roads"),
    "orient":    ("W12_orient.gpkg",    "s2_orient"),
    "hier":      ("W12_hier.gpkg",      "s3_hierarchy"),
    "chambers":  ("W12_chambers.gpkg",  "s4_chambers"),
    "flows":     ("W12_flows.gpkg",     "s5_flows"),
    "design":    ("W12.gpkg",           "s6_levels"),      # <- absent from conftest.GPKGS
    "levels":    ("W12_levels.gpkg",    "s6_levels"),      # <- absent from conftest.GPKGS
    "pumps":     ("W12_pumps.gpkg",     "s7_pumps"),
    "export":    ("W12_export.gpkg",    "s8_export"),      # <- absent from conftest.GPKGS
}

#: Role -> the layers that can supply it, BEST FIRST. The design is spread over several
#: GeoPackages until stage 8 assembles it, so "is this field published" is a question about
#: the set, not about one file.
ROLES: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "reaches":      (("design", "reaches"), ("export", "reaches"),
                     ("hier", "reaches"), ("chambers", "segments"), ("flows", "arcs")),
    "nodes":        (("design", "nodes"), ("export", "nodes"),
                     ("chambers", "chambers"), ("hier", "nodes"), ("flows", "nodes")),
    "connections":  (("export", "connections"), ("chambers", "connections")),
    "stations":     (("pumps", "stations"), ("export", "stations")),
    "rising_mains": (("pumps", "rising_mains"), ("export", "rising_mains")),
    "crossings":    (("design", "crossings"), ("export", "crossings")),
    "corridors":    (("roads", "corridors"),),
    "subnetworks":  (("export", "subnetworks"),),
}

#: The five non-layer inputs `AUDIT_NEEDS` names as `external`, and how each is PROVEN to be
#: there. An external that is only asserted is the same blank the philosophy forbids.
EXTERNALS: Dict[str, str] = {
    "roads":     "W12_roads.gpkg/corridors, from the DXF-derived centreline",
    "hazard":    "the 50-year flood-hazard grid (criteria.HAZARD_WADI_CLASSES 4/5/6)",
    "crossings": "the crossings REGISTER - W12.gpkg/crossings",
    "existing":  "NAMA's built network, SEWERLINE_IBRI.shp / FORCELINE_IBRI.shp",
    "manifest":  "run/manifest.json plus the per-GeoPackage `manifest` layers",
}


_CACHE: Dict[str, object] = {}


def gpkg(key: str) -> Path:
    return SHP_DIR / GPKGS[key][0]


def layers_of(key: str) -> List[str]:
    import fiona
    p = gpkg(key)
    if not p.is_file():
        return []
    ck = "__names__:" + key
    if ck not in _CACHE:
        _CACHE[ck] = list(fiona.listlayers(str(p)))
    return list(_CACHE[ck])                                    # type: ignore[arg-type]


def columns_of(key: str, name: str) -> set:
    """Column names WITHOUT reading the rows. Readiness must be cheap enough to run first."""
    import fiona
    p = gpkg(key)
    if not p.is_file() or name not in layers_of(key):
        return set()
    ck = "__cols__:%s:%s" % (key, name)
    if ck not in _CACHE:
        with fiona.open(str(p), layer=name) as src:
            _CACHE[ck] = set(src.schema["properties"].keys()) | {"geometry"}
    return set(_CACHE[ck])                                     # type: ignore[arg-type]


def read(key: str, name: str):
    import geopandas as gpd
    ck = "%s:%s" % (key, name)
    if ck not in _CACHE:
        p = gpkg(key)
        if not p.is_file():
            raise AssertionError(
                "%s is not published - %s has not run. Philosophy sec 8: a check that "
                "cannot run is a FAILURE, not a blank." % (p.name, GPKGS[key][1]))
        if name not in layers_of(key):
            raise AssertionError("%s has no layer '%s'; it holds %s"
                                 % (p.name, name, layers_of(key)))
        _CACHE[ck] = gpd.read_file(str(p), layer=name)
    return _CACHE[ck]


#: Every (role -> layer) resolution this session made, so the SUBSTITUTION IS PUBLISHED.
#: `role()` falls through to the next candidate when the preferred layer lacks a field, and a
#: fall-through changes WHICH DESIGN a check audited. Silent, that is the worst kind of pass:
#: H1a's COND 2 already reads the stage-8 node layer, because `W12.gpkg/nodes` carries no
#: ON_WADI, and nothing said so. Recorded here and published by
#: `test_which_published_layer_every_check_actually_read`.
RESOLVED: List[Tuple[str, Tuple[str, ...], str]] = []


def role(name: str, fields: Sequence[str] = ()):
    """The best published layer for a role that carries `fields`.

    Not "the first file that exists" - the first that actually carries the columns the check
    needs, because `W12.gpkg/nodes` and `W12_chambers.gpkg/chambers` are both node layers and
    only one of them has an invert on it.

    EVERY RESOLUTION IS RECORDED in `RESOLVED`. A check that quietly moved to another
    GeoPackage is auditing another design, and that must be visible.
    """
    for key, lyr in ROLES[name]:
        cols = columns_of(key, lyr)
        if cols and all(f in cols for f in fields):
            RESOLVED.append((name, tuple(fields), "%s/%s" % (GPKGS[key][0], lyr)))
            return read(key, lyr), "%s/%s" % (GPKGS[key][0], lyr)
    have = {}
    for key, lyr in ROLES[name]:
        cols = columns_of(key, lyr)
        if cols:
            have["%s/%s" % (GPKGS[key][0], lyr)] = sorted(set(fields) - cols)
    raise AssertionError("no published '%s' layer carries %s; missing per layer: %s"
                         % (name, list(fields), have))


def external_present(name: str) -> Tuple[bool, str]:
    """Prove an external input exists. Never assumed."""
    if name == "roads":
        return bool(columns_of("roads", "corridors")), EXTERNALS[name]
    if name == "crossings":
        ok = bool(columns_of("design", "crossings") or columns_of("export", "crossings"))
        return ok, EXTERNALS[name]
    if name == "manifest":
        return (RUN_DIR / "manifest.json").is_file(), EXTERNALS[name]
    if name in ("hazard", "existing"):
        try:
            from w12.asbuilt import default_paths
            paths = default_paths()
        except Exception as exc:                        # pragma: no cover - import guard
            return False, "%s (w12.asbuilt unimportable: %s)" % (EXTERNALS[name], exc)
        keys = ("hazard50",) if name == "hazard" else ("sewerline", "forceline")
        return all(os.path.exists(paths.get(k, "")) for k in keys), EXTERNALS[name]
    return False, EXTERNALS.get(name, name)


# ======================================================================================
# THE 34 CHECKS - id, what it enforces, its guideline page, and whether a breach blocks
# ======================================================================================

class Check:
    __slots__ = ("cid", "enforces", "source", "blocking", "wired_elsewhere")

    def __init__(self, cid: str, enforces: str, source: str, blocking: bool = True,
                 wired_elsewhere: str = ""):
        self.cid, self.enforces, self.source = cid, enforces, source
        self.blocking, self.wired_elsewhere = blocking, wired_elsewhere


CHECKS: Dict[str, Check] = {c.cid: c for c in (
    Check("H1",  "no pipe ALONG a dual carriageway or a wadi; crossing only",
          "project rules 7, 8 - G203-p30 sec 4.4.1, p33", True,
          "test_invariants.py::test_H1_no_corridor_carries_a_pipe_along_a_dual_carriageway"),
    Check("H1a", "a wadi crossing is legal only when all four conditions hold",
          "G201-p85-86 sec 9.3 - G203-p52 sec 8.2.4"),
    Check("H2",  "capacity >= discharge, within the d/D limit",
          "G203-p27 Table 10"),
    Check("H3",  "minimum cover 1.30 m to crown, on the reach's own outside diameter",
          "G203-p33"),
    Check("H4",  "maximum cover 12 m - exits only via philosophy sec 5",
          "G203-p33"),
    Check("H4b", "each past-the-cap exit is bounded by DISTANCE and by DEPTH",
          "philosophy sec 5 (500 m / 1,000 m; drop ceiling)"),
    Check("H4c", "drop structures: backdrop past 600 mm, capped at 2 m, vortex beyond",
          "G203-p30"),
    Check("H5",  "self-cleansing by velocity OR tractive force, with the route recorded",
          "G203-p26-27"),
    Check("H6",  "laid gradient >= Table 11 for the diameter",
          "G203-p29 Table 11"),
    Check("H7",  "max velocity 3.0 m/s gravity, 2.5 m/s rising main; 0.75 m/s FM floor",
          "G203-p27, p50 sec 8.1"),
    Check("H8",  "diameter set by flow, never by the depth wanted",
          "G203-p29"),
    Check("H9",  "minimum sizes and materials by tier",
          "G203-p22 Table 6"),
    Check("H10", "inlet angle >= 90 deg", "G203-p30", True,
          "test_invariants.py::test_H10_inlet_angles_are_at_least_ninety_degrees"),
    Check("H11", "no reverse gradient; laying tolerance 20 mm",
          "G203-p29"),
    Check("H12", "chamber spacing within Table 12",
          "G203-p30 Table 12"),
    Check("H13", "uniform slope between successive manholes",
          "G203-p29"),
    Check("H14", "an existing structure's invert is fixed; tie SOFFIT to soffit",
          "practice - philosophy sec 3"),
    Check("H15", "the network is a forest: zero loops, one outfall per component",
          "project rule - philosophy sec 3"),
    Check("H16", "every pipe publishes US_NODE and DS_NODE",
          "project rule - philosophy sec 3"),
    Check("H17", "the against-the-grade quantities are REPORTED, not merely computed",
          "philosophy sec 4", False),
    Check("R1",  "regression: no surcharged pipe, recomputed independently",
          "G203-p27 - philosophy sec 8"),
    Check("R2",  "regression: no reach below minimum cover, recomputed independently",
          "G203-p33 - philosophy sec 8"),
    Check("R3",  "regression: no pipe along a dual carriageway",
          "project rule 7 - philosophy sec 8"),
    Check("R4",  "regression: no pipe on wadi ground outside a scheduled crossing",
          "G203-p30 sec 4.4.1 - philosophy sec 8"),
    Check("G1",  "provenance: the laid gradient AND its governing minimum are both published",
          "philosophy sec 5, sec 8"),
    Check("G2",  "provenance: every reach records what set its diameter and its gradient",
          "philosophy sec 3, sec 8"),
    Check("G3",  "provenance: no re-filtered metric - ids resolve, nothing duplicated",
          "philosophy sec 8"),
    Check("G4",  "provenance: no stage silently doing nothing",
          "philosophy sec 8"),
    Check("G5",  "provenance: every published feature carries SRC and CONFIDENCE",
          "philosophy sec 8"),
    Check("C1",  "concept: every drop names the reason it exists",
          "philosophy sec 9 - concept rule 1"),
    Check("C2",  "concept: a subnetwork joins the main pipe at its lowest meeting point",
          "philosophy sec 9 - concept rule 2"),
    Check("C3",  "concept: one gravity check per plot, every failure flagged and sized",
          "philosophy sec 9 - concept rule 5"),
    Check("C4",  "concept: the naming grammar is applied to every element",
          "philosophy sec 9 - concept rule 8"),
    Check("C5",  "concept: a station's position is CHOSEN not triggered; shortest main",
          "philosophy sec 5, sec 9 - concept rule 6"),
)}

assert len(CHECKS) == 34, "%d checks declared here; AUDIT_NEEDS has 34" % len(CHECKS)


# ======================================================================================
# READINESS - computed against the WHOLE published set, not three files of it
# ======================================================================================

def readiness_rows() -> List[dict]:
    from w12.contract import AUDIT_NEEDS
    assert set(AUDIT_NEEDS) == set(CHECKS), (
        "this file and contract.AUDIT_NEEDS disagree about which checks exist: "
        "only in contract %s; only here %s"
        % (sorted(set(AUDIT_NEEDS) - set(CHECKS)), sorted(set(CHECKS) - set(AUDIT_NEEDS))))
    rows = []
    for cid, need in AUDIT_NEEDS.items():
        missing: List[str] = []
        supplied: List[str] = []
        for lyr_role, fields in need.items():
            if lyr_role == "external":
                for e in fields:
                    ok, _what = external_present(e)
                    (supplied if ok else missing).append("external:" + e)
                continue
            found = None
            for key, lyr in ROLES.get(lyr_role, ()):
                cols = columns_of(key, lyr)
                if cols and all(f in cols for f in fields):
                    found = "%s/%s" % (GPKGS[key][0], lyr)
                    break
            if found:
                supplied.append(found)
            else:
                union: set = set()
                for key, lyr in ROLES.get(lyr_role, ()):
                    union |= columns_of(key, lyr)
                gone = [lyr_role + "." + f for f in fields if f not in union]
                if gone:
                    missing += gone
                else:
                    missing.append("%s: the fields exist but no single layer carries all of "
                                   "%s" % (lyr_role, list(fields)))
        c = CHECKS[cid]
        rows.append(dict(
            check=cid,
            enforces=c.enforces,
            source=c.source,
            severity="blocking" if c.blocking else "reporting",
            can_run=not missing,
            reads=" + ".join(sorted(set(supplied))),
            missing="; ".join(sorted(set(missing))),
            wired_in=c.wired_elsewhere or ("test_audit_readiness.py::test_audit_check[%s]"
                                           % cid),
        ))
    return rows


# ======================================================================================
# THE MEASUREMENTS - one per check. Each returns (verdict, detail).
#   verdict True  = the constraint holds
#           False = a BREACH, and the detail sizes it
#           None  = reported here, asserted elsewhere (H1, H10) or reporting-only (H17)
# ======================================================================================

def _crit():
    from w12.criteria import DEFAULT
    return DEFAULT


def _design_reaches():
    return role("reaches", ("DN", "SLOPE_LAID", "COVER_US", "US_NODE", "DS_NODE"))


def _asbuilt(label: str, fallback: str) -> str:
    """One as-built calibration figure, READ from the published calibration table.

    `W12_levels.gpkg/calibration` carries the 2006 network's measured value beside the
    design's for every gate in `_BRAIN/10_ASBUILT_CALIBRATION.md`. Quoting one from memory
    is how "NAMA's built network has 37 vortex drops in 95.45 km = 0.39/km" got into this
    file: the measured figure is 0.585 vortex/km, the same 0.585 this file already prints
    two checks further down, so the audit contradicted itself in one deliverable.
    """
    try:
        cal = read("levels", "calibration")
        row = cal[cal.label.astype(str) == label]
        if len(row):
            r0 = row.iloc[0]
            return ("%s = %.3f %s (built), design %.3f, band %s [W12_levels.gpkg/calibration"
                    ", basis %s]" % (label, float(r0.as_built), str(r0.unit),
                                     float(r0.design), str(r0.band), str(r0.basis)))
    except Exception:                                   # pragma: no cover
        pass
    return fallback


_ASBUILT_DROP_RATES = None                              # filled lazily, see m_H4c


# ---- H1 ------------------------------------------------------------------------------
def m_H1():
    import pandas as pd
    C = _crit()
    r, src = _design_reaches()
    dual = pd.to_numeric(r.ON_DUAL_M, errors="coerce").fillna(0.0)
    wadi = pd.to_numeric(r.ON_WADI_M, errors="coerce").fillna(0.0)
    has_id = r.CROSS_ID.astype(str).str.strip() != ""
    unscheduled_dual = int(((dual > 1e-9) & ~has_id).sum())
    unscheduled_wadi = int(((wadi > 1e-9) & ~has_id).sum())
    return None, (
        "{src}: {nd} reaches touch a dual carriageway ({md:,.0f} m total, longest {ld:.1f} m "
        "against the {cap:.0f} m crossing cap) and {nw:,} touch wadi ground ({mw:,.1f} km). "
        "{ud} dual and {uw} wadi contacts carry NO CROSS_ID, so on the DESIGN layer every "
        "contact is at least REGISTERED as a crossing - whether it QUALIFIES as one is H1a, "
        "and most do not. THE BLOCKING HALF OF H1 IS ON THE CORRIDOR LAYER and is asserted "
        "in test_invariants.py; it currently FAILS on 10 corridors / 0.83 km. Not "
        "re-asserted here - one owner per fix."
        .format(src=src, nd=int((dual > 1e-9).sum()), md=dual.sum(), ld=dual.max(),
                cap=C.DUAL_XING_MAX_M, nw=int((wadi > 1e-9).sum()), mw=wadi.sum() / 1000.0,
                ud=unscheduled_dual, uw=unscheduled_wadi))


# ---- H1a -----------------------------------------------------------------------------
def m_H1a():
    import pandas as pd
    C = _crit()
    x, src = role("crossings", ("OBSTACLE", "ANGLE_DEG", "COVER_M", "APPROVED", "CROSS_ID"))
    r, _rsrc = _design_reaches()
    ch, chsrc = role("nodes", ("ON_WADI",))
    square = 90.0 - C.WADI_XING_SKEW_DEG
    wadi = x[x.OBSTACLE.astype(str) == "wadi"]
    dual = x[x.OBSTACLE.astype(str) == "dual"]

    # AN ANGLE THAT WAS NEVER MEASURED IS NOT AN ANGLE THAT FAILED.
    # `s6_levels.build_crossings` writes ANGLE_DEG = 0.0 on EVERY dual row unconditionally
    # (the `for k in np.where(on_dual_m > 0)` loop) and on any wadi row whose bearing came
    # back NaN. Folding those into the skew count reports a MEASUREMENT GAP as a geometry
    # defect and sends the engineer to the wrong file. Both are breaches - philosophy sec 8:
    # a check that cannot run is a failure, not a blank - but they are different breaches
    # with different fixes, so they are counted apart. (First written as "s1 writes"; s1
    # never touches this register.)
    def _split(sub_df):
        a = pd.to_numeric(sub_df.ANGLE_DEG, errors="coerce")
        never_measured = int((a.isna() | (a.abs() < 1e-9)).sum())
        off_square = int(((~a.isna()) & (a.abs() >= 1e-9) & (a < square)).sum())
        return never_measured, off_square

    unmeas_w, skew_w = _split(wadi)
    unmeas_d, skew_d = _split(dual)
    thin = int((pd.to_numeric(wadi.COVER_M, errors="coerce")
                < C.MIN_COVER_WADI_XING - 1e-9).sum())
    unapproved = int((pd.to_numeric(x.APPROVED, errors="coerce").fillna(0) == 0).sum())
    on_wadi_ch = int(pd.to_numeric(ch.ON_WADI, errors="coerce").fillna(0).sum())
    dangling = len(set(r.CROSS_ID.astype(str)) - {""} - set(x.CROSS_ID.astype(str)))
    bad = skew_w + skew_d + unmeas_w + unmeas_d + thin + on_wadi_ch + dangling

    # THE STAGE PUBLISHES ITS OWN FOUR-CONDITION TABLE. Read it rather than only recomputing:
    # a disagreement between the stage's verdict and ours is itself a finding, and agreement
    # is evidence the recomputation is measuring the same thing.
    stage = ""
    try:
        h = read("levels", "wadi_h1a")
        ok = int(pd.to_numeric(h.H1A_OK, errors="coerce").fillna(0).sum())
        sq_ok = int(pd.to_numeric(h.SQUARE_ENOUGH, errors="coerce").fillna(0).sum())
        theirs = len(h) - sq_ok
        stage = (" THE STAGE'S OWN VERDICT: W12_levels.gpkg/wadi_h1a is s6_levels' four-"
                 "condition table and it publishes H1A_OK = 1 on {ok} of {n} wadi crossings. "
                 "It counts {th} failing condition 1 against the {ours} measured here - {v}."
                 .format(ok=ok, n=len(h), th=theirs, ours=skew_w,
                         v=("the two agree" if theirs == skew_w
                            else "THE TWO DISAGREE, and one of them is wrong")))
    except Exception as exc:                            # pragma: no cover
        stage = " (could not read W12_levels.gpkg/wadi_h1a: %s)" % exc

    return bad == 0, (
        "{src}: {n:,} registered crossings ({w} wadi, {d} dual). "
        "COND 1 (crosses, does not run along - within {skew:.0f} deg of square, so "
        ">= {sq:.0f} deg): MEASURED AND OFF SQUARE - {sw} of {w} wadi, {sd} of {d} dual. "
        "NEVER MEASURED AT ALL - {uw} wadi and {ud} dual rows carry ANGLE_DEG = 0.00, which "
        "s6_levels.build_crossings writes unconditionally on every dual row and on any wadi "
        "row whose bearing came back NaN. That is a MEASUREMENT GAP, not a skew: counted as "
        "a breach in its own right and NOT added to the skew count, because the fix is in a "
        "different place. "
        "COND 2 (no chamber on wadi ground or on the embankment): {oc:,} of {nc:,} chambers "
        "sit on wadi ground in {chsrc} - a straight breach; the philosophy reads G203-p30 "
        "sec 4.4.1's 'avoided' as PROHIBITED. NOTE THE SOURCE: W12.gpkg/nodes carries no "
        "ON_WADI, so this ONE condition is measured on the stage-8 node layer while every "
        "other H-check in this file reads stage 6. "
        "COND 3 (1.50 m cover, OUR decision above the guideline's 1.30): {thin} wadi "
        "crossings sit at 1.30 m - short of our own rule, not of the guideline's, and it "
        "must be reported that way. "
        "COND 4 (in the register): {dang} reach CROSS_IDs resolve to nothing; {unapp} of "
        "{n:,} crossings have APPROVED = 0 - MoAFWR consent (G201-p85) is an OPEN ITEM, "
        "correctly published, not a design defect.{stage}"
        .format(src=src, n=len(x), w=len(wadi), d=len(dual), skew=C.WADI_XING_SKEW_DEG,
                sq=square, sw=skew_w, sd=skew_d, uw=unmeas_w, ud=unmeas_d, oc=on_wadi_ch,
                nc=len(ch), chsrc=chsrc, thin=thin, dang=dangling, unapp=unapproved,
                stage=stage))


# ---- H2 ------------------------------------------------------------------------------
def m_H2():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("DN", "QPK_LS", "SLOPE_LAID", "DOD_PK"))
    dn = pd.to_numeric(r.DN, errors="coerce")
    dod = pd.to_numeric(r.DOD_PK, errors="coerce")
    lim = dn.map(lambda d: C.dod_limit(int(d)))
    over = r[dod > lim + 1e-9]
    return over.empty, (
        "{src}: max d/D {mx:.4f} against a limit of {a:g} up to DN{t} and {b:g} above; "
        "{n:,} reaches over their own limit ({km:,.2f} km)."
        .format(src=src, mx=dod.max(), a=C.DOD_MAX_SMALL, t=C.DOD_DN_THRESHOLD,
                b=C.DOD_MAX_LARGE, n=len(over),
                km=(over.LEN_M.sum() / 1000.0) if len(over) else 0.0))


# ---- H3 ------------------------------------------------------------------------------
def m_H3():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("DN", "US_DEPTH", "DS_DEPTH", "COVER_US", "COVER_DN"))
    cu = pd.to_numeric(r.COVER_US, errors="coerce")
    cd = pd.to_numeric(r.COVER_DN, errors="coerce")
    under = r[(cu < C.MIN_COVER_CROWN - 1e-9) | (cd < C.MIN_COVER_CROWN - 1e-9)]
    return under.empty, (
        "{src}: shallowest cover {mn:.3f} m against the {lim:.2f} m minimum to crown; "
        "{n:,} reaches below it ({km:,.2f} km). W10 shipped 45.92 km below this with nothing "
        "looking, which is why this check exists."
        .format(src=src, mn=min(cu.min(), cd.min()), lim=C.MIN_COVER_CROWN, n=len(under),
                km=(under.LEN_M.sum() / 1000.0) if len(under) else 0.0))


# ---- H4 ------------------------------------------------------------------------------
def m_H4():
    import pandas as pd
    C = _crit()
    r, src = role("reaches",
                  ("DN", "US_DEPTH", "DS_DEPTH", "PAST_CAP", "COVER_US", "COVER_DN"))
    cov = pd.concat([pd.to_numeric(r.COVER_US, errors="coerce"),
                     pd.to_numeric(r.COVER_DN, errors="coerce")], axis=1).max(axis=1)
    past = pd.to_numeric(r.PAST_CAP, errors="coerce").fillna(0).astype(int) == 1
    over = cov > C.MAX_COVER + 1e-9
    unflagged = r[over & ~past]
    phantom = r[past & ~over]
    other = ""
    try:
        e = read("export", "reaches")
        ec = pd.concat([pd.to_numeric(e.COVER_US, errors="coerce"),
                        pd.to_numeric(e.COVER_DN, errors="coerce")], axis=1).max(axis=1)
        other = (" THE OTHER PUBLISHED REACH LAYER DISAGREES: W12_export.gpkg/reaches has "
                 "{n:,} reaches past the cap and a deepest cover of {mx:.2f} m."
                 .format(n=int((ec > C.MAX_COVER).sum()), mx=ec.max()))
    except Exception:                                   # pragma: no cover
        pass
    # BOTH DIRECTIONS COUNT. An unflagged breach hides a deep reach; a phantom flag lets a
    # reach carry a past-the-cap exit (and its 500 m / 1,000 m licence, H4b) that it never
    # earned. The phantom count was printed beside the verdict and left out of it.
    return (unflagged.empty and phantom.empty), (
        "{src}: {n:,} reaches ({km:,.2f} km) exceed the {cap:.0f} m cover cap, deepest "
        "{mx:.2f} m. {u:,} of them are NOT flagged PAST_CAP and {p:,} are flagged without "
        "exceeding it - BOTH are breaches. Nothing past the cap is final - it waits on a manufacturer's rating "
        "for that cover and NWS's station establishment cost (philosophy sec 5).{other}"
        .format(src=src, n=int(over.sum()), km=r.loc[over, "LEN_M"].sum() / 1000.0,
                cap=C.MAX_COVER, mx=cov.max(), u=len(unflagged), p=len(phantom),
                other=other))


# ---- H4b -----------------------------------------------------------------------------
def m_H4b():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("PAST_CAP", "CAP_EXIT", "CAP_LEN_M"))
    n, nsrc = role("nodes", ("DROP_M",))
    past = r[pd.to_numeric(r.PAST_CAP, errors="coerce").fillna(0).astype(int) == 1]
    ln = pd.to_numeric(past.CAP_LEN_M, errors="coerce")
    ex = past.CAP_EXIT.astype(str)
    blank = int((ex.str.strip() == "").sum())
    over500 = int(((ex == "recovers_500m") & (ln > 500 + 1e-6)).sum())
    over1000 = int(((ex == "outfall_1000m") & (ln > 1000 + 1e-6)).sum())
    drop = pd.to_numeric(n.DROP_M, errors="coerce").fillna(0.0)
    over_ceiling = int((drop > C.DROP_CEILING_M).sum())
    bad = blank + over500 + over1000 + over_ceiling
    counts = ", ".join("%s %s" % (k, format(v, ",")) for k, v in ex.value_counts().items())
    return bad == 0, (
        "{src}: {n:,} reaches past the cap take exits [{c}]; {b} take no named exit. "
        "DISTANCE bound: {a} over the 500 m recovery bound, {d} over the 1,000 m outfall "
        "bound (longest excursion {mx:,.0f} m). DEPTH bound - the exit is WITHDRAWN past the "
        "drop ceiling: worst drop in {nsrc} is {dr:.2f} m against a ceiling of {cl:.0f} m, "
        "{oc} over. The distance-only version of this rule produced a 35.06 m drop on "
        "2026-09-02, which is why the depth bound exists."
        .format(src=src, n=len(past), c=counts, b=blank, a=over500, d=over1000,
                mx=(ln.max() if len(ln) else 0.0), nsrc=nsrc, dr=drop.max(),
                cl=C.DROP_CEILING_M, oc=over_ceiling))


# ---- H4c -----------------------------------------------------------------------------
def m_H4c():
    import pandas as pd
    C = _crit()
    n, src = role("nodes", ("DROP_M", "DROP_TYPE", "VORTEX"))
    # The design's own length, MEASURED. A hand-typed 1485.4 was here; it happened to be
    # right on run 003 and is wrong the moment a stage re-runs, and the rate it divides is
    # quoted in a deliverable.
    _r, _ = role("reaches", ("LEN_M",))
    km_total = float(pd.to_numeric(_r.LEN_M, errors="coerce").sum()) / 1000.0
    global _ASBUILT_DROP_RATES
    _ASBUILT_DROP_RATES = _asbuilt(
        "vortex drop shafts per km (invert step > 2.00 m)",
        "0.585 vortex/km and 1.329 backdrop/km (_BRAIN/10_ASBUILT_CALIBRATION.md sec 1)")
    d = pd.to_numeric(n.DROP_M, errors="coerce").fillna(0.0)
    typ = n.DROP_TYPE.astype(str)
    vx = pd.to_numeric(n.VORTEX, errors="coerce").fillna(0).astype(int)
    needs = d > C.DROP_TRIGGER + 1e-9
    untyped = int((needs & (typ == "none")).sum())
    bd_over = int(((typ == "backdrop") & (d > C.BACKDROP_MAX + 1e-9)).sum())
    vx_mismatch = int(((typ == "vortex") ^ (vx == 1)).sum())
    over_ceiling = int((d > C.DROP_CEILING_M).sum())
    bad = untyped + bd_over + vx_mismatch + over_ceiling
    return bad == 0, (
        "{src}: {n:,} chambers have an invert difference over {trig:.0f} mm and so require a "
        "drop structure (G203-p30); {bd:,} are backdrops and {vx:,} vortex shafts. {ut} that "
        "need one are still typed 'none'; {bo} backdrops exceed the {cap:.2f} m cap that "
        "sends a drop to a vortex shaft; {mm} disagree between DROP_TYPE and the VORTEX flag; "
        "{oc} are past the {cl:.0f} m ceiling. Worst drop {mx:.2f} m. Against the BUILT "
        "network: {bkm}. This design has {rate} over its own measured {km:,.1f} km."
        .format(src=src, n=int(needs.sum()), bd=int((typ == "backdrop").sum()),
                vx=int((typ == "vortex").sum()), ut=untyped, bo=bd_over, cap=C.BACKDROP_MAX,
                mm=vx_mismatch, oc=over_ceiling, cl=C.DROP_CEILING_M, mx=d.max(),
                trig=C.DROP_TRIGGER * 1000.0, bkm=_ASBUILT_DROP_RATES, km=km_total,
                rate="%.3f vortex/km, %.3f backdrop/km" % (int(vx.sum()) / km_total,
                                                           int((typ == "backdrop").sum())
                                                           / km_total)))


# ---- H5 ------------------------------------------------------------------------------
def m_H5():
    import numpy as np
    import w12.hydra as H
    C = _crit()
    r, src = role("reaches", ("DN", "QPK_LS", "SLOPE_LAID", "CLEAN_BY", "TAU_PA"))
    dn = r.DN.astype(int).values
    s = r.SLOPE_LAID.astype(float).values / 100.0
    q = r.QPK_LS.astype(float).values / 1000.0
    route = np.array([H.clean_route(int(a), b, c) for a, b, c in zip(dn, s, q)], dtype=object)
    published = r.CLEAN_BY.astype(str).values
    disagree = int((route != published).sum())
    neither = int((route == "neither").sum())
    km = r.LEN_M.values / 1000.0
    tract_km = float(km[route == "tractive"].sum())
    return (neither == 0 and disagree == 0), (
        "{src}: recomputed independently with hydra.clean_route - {dis:,} reaches disagree "
        "with the published CLEAN_BY and {nei:,} satisfy NEITHER route (a failure, never a "
        "small number). {tk:,.1f} km of {tot:,.1f} km ({pc:.1f} %) rests on the TRACTIVE "
        "route and therefore on tau = {tau:g} Pa, which the guideline never gives (GAP-9). "
        "At 2.0 Pa every tractive gradient rises {f:.3f}x and every level below it changes."
        .format(src=src, dis=disagree, nei=neither, tk=tract_km, tot=km.sum(),
                pc=tract_km / km.sum() * 100.0, tau=C.TAU_PA,
                f=C.TAU_SLOPE_FACTOR_AT_2PA))


# ---- H6 ------------------------------------------------------------------------------
def m_H6():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("DN", "QPK_LS", "SLOPE_LAID", "SLOPE_MIN"))
    laid = pd.to_numeric(r.SLOPE_LAID, errors="coerce")
    t11 = pd.to_numeric(r.DN, errors="coerce").map(lambda d: C.table11(int(d)) * 100.0)
    pub = pd.to_numeric(r.SLOPE_MIN, errors="coerce")
    under_t11 = r[laid < t11 - 1e-9]
    under_pub = r[laid < pub - 1e-9]
    return (under_t11.empty and under_pub.empty), (
        "{src}: {a:,} reaches are laid flatter than G203-p29 Table 11 for their own bore "
        "(worst deficit {w:.4f} %), and {b:,} flatter than the SLOPE_MIN published beside "
        "them. Laid gradient median {m:.3f} % = {mm:.2f} mm/m, against the built network's "
        "6.00 mm/m median (10_ASBUILT_CALIBRATION)."
        .format(src=src, a=len(under_t11), b=len(under_pub), w=(t11 - laid).max(),
                m=laid.median(), mm=laid.median() * 10.0))


# ---- H7 ------------------------------------------------------------------------------
def m_H7():
    import numpy as np
    import pandas as pd
    import w12.hydra as H
    C = _crit()
    r, src = role("reaches", ("DN", "QPK_LS", "SLOPE_LAID", "V_PK_MS"))
    v = pd.to_numeric(r.V_PK_MS, errors="coerce")
    over = r[v > C.V_MAX + 1e-9]
    # RECOMPUTED, not read. R1 already re-derives d/D from the same `pipe_state` call and
    # throws the velocity away; reading V_PK_MS back would let a clipped velocity pass its
    # own cap. Seven reaches sit within 1 mm/s of the 3.0 m/s limit, which is exactly the
    # place a clip would hide.
    vr = np.array([H.pipe_state(int(a), float(b) / 100.0, float(c) / 1000.0)[1]
                   for a, b, c in zip(r.DN.astype(int).values,
                                      r.SLOPE_LAID.astype(float).values,
                                      r.QPK_LS.astype(float).values)], dtype=float)
    recomputed_over = int(np.nansum(vr > C.V_MAX + 1e-9))
    v_disagree = int(np.nansum(np.abs(vr - v.values) > 0.005))
    rm, rmsrc = role("rising_mains", ("V_DUTY_MS",))
    vd = pd.to_numeric(rm.V_DUTY_MS, errors="coerce")
    fm_over = int((vd > C.FM_V_MAX + 1e-9).sum())
    fm_under = 0
    detail_min = ""
    if "V_MIN_MS" in rm.columns:
        vm = pd.to_numeric(rm.V_MIN_MS, errors="coerce")
        fm_under = int((vm < C.FM_V_MIN - 1e-9).sum())
        detail_min = (" MINIMUM-FLOW velocity: {u} of {n} rising mains are below {f:g} m/s "
                      "(lowest {lo:.3f} m/s). G203-p50 sec 8.1 holds that floor AT DESIGN "
                      "MINIMUM FLOW, not at duty, and p40 Table 16 supplies the flow - "
                      "sizing on duty alone silts the main in year one. contract.validate() "
                      "raises on this and the layer was published anyway."
                      .format(u=fm_under, n=len(rm), f=C.FM_V_MIN, lo=vm.min()))
    ok = (over.empty and fm_over == 0 and fm_under == 0 and recomputed_over == 0
          and v_disagree == 0)
    return ok, (
        "{src}: peak velocity max {mx:.4f} m/s against the {g:g} m/s GRAVITY maximum, "
        "{n:,} over. RECOMPUTED independently with hydra.pipe_state on all {t:,} reaches: "
        "max {rmx:.4f} m/s, {ro:,} over the cap, {rd:,} disagreeing with the published "
        "V_PK_MS by more than 5 mm/s. {rmsrc}: duty velocity max {dm:.3f} m/s against the "
        "{fm:g} m/s FORCE-MAIN maximum, {fo} over - two different numbers, conflated once "
        "already.{dmin}"
        .format(src=src, mx=v.max(), g=C.V_MAX, n=len(over), t=len(r),
                rmx=float(np.nanmax(vr)), ro=recomputed_over, rd=v_disagree, rmsrc=rmsrc,
                dm=vd.max(), fm=C.FM_V_MAX, fo=fm_over, dmin=detail_min))


# ---- H8 ------------------------------------------------------------------------------
def m_H8():
    r, src = role("reaches", ("SIZED_BY",))
    vals = r.SIZED_BY.astype(str)
    allowed = {"minimum", "dod", "capacity", "velocity", "tier"}
    blank = int((vals.str.strip() == "").sum())
    by_depth = int(vals.str.contains("depth", case=False, na=False).sum())
    unknown = sorted(set(vals) - allowed - {""})
    counts = ", ".join("%s %s" % (k, format(v, ",")) for k, v in vals.value_counts().items())
    return (blank == 0 and by_depth == 0), (
        "{src}: [{c}]. {b:,} reaches do not say what set their diameter and {d:,} say DEPTH "
        "did - which G203-p29 and Ten States sec 33.43 prohibit independently. Tokens "
        "outside the expected set: {u}."
        .format(src=src, c=counts, b=blank, d=by_depth, u=(unknown or "none")))


# ---- H9 ------------------------------------------------------------------------------
def m_H9():
    C = _crit()
    r, src = role("reaches", ("TIER", "DN", "MATERIAL"))
    bad_mat, bad_dn = [], []
    for tier, dn, mat in zip(r.TIER.astype(str), r.DN.astype(int), r.MATERIAL.astype(str)):
        allowed = C.materials_allowed(tier, int(dn))
        if allowed and mat not in allowed:
            bad_mat.append((tier, int(dn), mat))
        floor = C.DN_TRUNK_MIN if tier == "trunk" else C.DN_MIN_LATERAL
        if dn < floor:
            bad_dn.append((tier, int(dn)))
    tiers = ", ".join("%s %s" % (k, format(v, ",")) for k, v in r.TIER.value_counts().items())
    mats = ", ".join("%s %s" % (k, format(v, ","))
                     for k, v in r.MATERIAL.value_counts().items())
    return (not bad_mat and not bad_dn), (
        "{src}: tiers [{t}]; materials [{m}]. {a} reaches carry a material G203-p22 Table 6 "
        "does not allow at their tier and bore (e.g. {ea}); {b} are below the minimum size "
        "for their tier (e.g. {eb})."
        .format(src=src, t=tiers, m=mats, a=len(bad_mat), ea=bad_mat[:3], b=len(bad_dn),
                eb=bad_dn[:3]))


# ---- H10 -----------------------------------------------------------------------------
def m_H10():
    import pandas as pd
    C = _crit()
    n, src = role("nodes", ("INLET_DEG", "INLET_FLAG"))
    a = pd.to_numeric(n.INLET_DEG, errors="coerce")
    measured = a[a >= 0]
    under = measured[measured < C.INLET_MIN_DEG - 1e-9]
    flagged = int(pd.to_numeric(n.INLET_FLAG, errors="coerce").fillna(0).sum())
    return None, (
        "{src}: {u:,} of {m:,} measured inlets are below {lim:.0f} deg (worst {w:.2f}); "
        "{f:,} carry INLET_FLAG = 1 and {nl:,} chambers carry no measurement at all. Each "
        "breach needs a purpose-made chamber with a swept channel (G203-p30) - the swept "
        "channel DETAIL is switched off at concept, the COUNT is not. THE BLOCKING "
        "ASSERTION is test_invariants.py::test_H10_inlet_angles_are_at_least_ninety_degrees, "
        "which currently FAILS. Not re-asserted here - one owner per fix."
        .format(src=src, u=len(under), m=len(measured), lim=C.INLET_MIN_DEG,
                w=(measured.min() if len(measured) else float("nan")), f=flagged,
                nl=int(a.isna().sum())))


# ---- H11 -----------------------------------------------------------------------------
def m_H11():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("INV_UP", "INV_DN"))
    up = pd.to_numeric(r.INV_UP, errors="coerce")
    dn = pd.to_numeric(r.INV_DN, errors="coerce")
    rise = dn - up
    bad = r[rise > C.LAY_TOLERANCE_M + 1e-9]
    return bad.empty, (
        "{src}: {n:,} reaches run uphill IN THE PIPE - downstream invert above upstream - by "
        "more than the {tol:.0f} mm laying tolerance; worst {w:+.4f} m. This is the INVERT; "
        "the ground question is H17 and they are different rules."
        .format(src=src, n=len(bad), tol=C.LAY_TOLERANCE_M * 1000.0, w=rise.max()))


# ---- H12 -----------------------------------------------------------------------------
def m_H12():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("DN", "LEN_M"))
    L = pd.to_numeric(r.LEN_M, errors="coerce")
    band = pd.to_numeric(r.DN, errors="coerce").map(lambda d: C.mh_max_spacing(int(d)))
    over = r[L > band + 1e-6]
    per_km = len(r) / (L.sum() / 1000.0)
    return over.empty, (
        "{src}: longest reach {mx:.2f} m, median {md:.2f} m; {n:,} over G203-p30 Table 12 "
        "for their OWN diameter. The weaker form of this check - against the widest band, "
        "because diameters were not published yet - is what ran before stage 6; this is the "
        "full statement. {pk:.2f} chambers per km against the built network's 34.23."
        .format(src=src, mx=L.max(), md=L.median(), n=len(over), pk=per_km))


# ---- H13 -----------------------------------------------------------------------------
def m_H13():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("SLOPE_LAID", "INV_UP", "INV_DN", "LEN_M"))
    L = pd.to_numeric(r.LEN_M, errors="coerce").clip(lower=1e-9)
    implied = (pd.to_numeric(r.INV_UP, errors="coerce")
               - pd.to_numeric(r.INV_DN, errors="coerce")) / L * 100.0
    laid = pd.to_numeric(r.SLOPE_LAID, errors="coerce")
    d = (implied - laid).abs()
    bad = r[d > 0.01]
    step = C.SLOPE_STEP * 100.0
    off_step = int(((laid / step).round() * step - laid).abs().gt(1e-9).sum())
    return bad.empty, (
        "{src}: a UNIFORM slope means the published gradient IS the invert drop over the "
        "length. Max disagreement {mx:.5f} % ({mm:.2f} mm over a median reach); {n:,} "
        "reaches disagree by more than 0.01 %. {os:,} gradients sit off the {st:.2f} % "
        "laying step - that is P1, a PREFERENCE, not a hard constraint, and P1 is never "
        "bought at the price of a pumping station."
        .format(src=src, mx=d.max(), mm=d.max() / 100.0 * L.median() * 1000.0, n=len(bad),
                os=off_step, st=step))


# ---- H14 -----------------------------------------------------------------------------
def m_H14():
    r, src = role("reaches", ("TIE_TYPE",))
    _ok_ext, what = external_present("existing")
    vals = r.TIE_TYPE.astype(str)
    counts = ", ".join("%s %s" % (k, format(v, ",")) for k, v in vals.value_counts().items())
    blank = int((vals.str.strip() == "").sum())
    invert_ties = int((vals == "invert").sum())
    return (blank == 0 and invert_ties == 0), (
        "{src}: TIE_TYPE [{c}]. {i} reaches tie INVERT to invert, which H14 forbids - the "
        "tie is soffit to soffit. {b} carry no token at all. THE HONEST READING: every reach "
        "is 'none', so this check is STRUCTURALLY VACUOUS - nothing in this design ties into "
        "an existing structure, although the built network ({w}) is present on disk and "
        "95.45 km of it exists. Tie-ins to NAMA's built sewer are a DESIGN DECISION nobody "
        "has taken yet, not a passing check."
        .format(src=src, c=counts, i=invert_ties, b=blank, w=what))


# ---- H15 -----------------------------------------------------------------------------
def m_H15():
    import collections
    r, src = role("reaches", ("US_NODE", "DS_NODE"))
    n, nsrc = role("nodes", ("IS_OUTFALL", "NODE_UID"))
    ds = dict(zip(r.US_NODE.astype(str), r.DS_NODE.astype(str)))
    known = set(n.NODE_UID.astype(str))
    outf = set(n.loc[n.IS_OUTFALL.astype(int) == 1, "NODE_UID"].astype(str))
    outdeg = collections.Counter(r.US_NODE.astype(str))
    branching = [k for k, v in outdeg.items() if v > 1]
    sinks = known - set(ds)
    orphans = sinks - outf
    false_outfalls = outf & set(ds)
    root: Dict[str, str] = {}
    loops = 0
    for u in known:
        path: List[str] = []
        seen: set = set()
        cur: Optional[str] = u
        while cur is not None and cur not in root and cur in ds:
            if cur in seen:
                loops += 1
                break
            seen.add(cur)
            path.append(cur)
            cur = ds.get(cur)
        end = root.get(cur, cur) if cur is not None else u
        for p in path:
            root[p] = end
        root.setdefault(u, end)
    comps = collections.Counter(root.values())
    unrooted = [e for e in comps if e in known and e not in outf]
    bad = len(branching) + len(orphans) + len(false_outfalls) + loops + len(unrooted)
    return bad == 0, (
        "{src} + {nsrc}: {c:,} components over {k:,} nodes; {lp} loops; {br:,} nodes with "
        "more than one outgoing arc (not a forest); {orp:,} sinks that are not marked "
        "IS_OUTFALL - by H15 they drain nowhere; {fo:,} nodes marked IS_OUTFALL that still "
        "own an outgoing arc; {ur:,} components whose root is not an outfall. NOTE: the FLOW "
        "graph (W12_flows.gpkg, stage 5) is a different and earlier graph and FAILS this - "
        "154 orphans carrying 762.6 m3/d, asserted in test_columns.py."
        .format(src=src, nsrc=nsrc, c=len(comps), k=len(known), lp=loops, br=len(branching),
                orp=len(orphans), fo=len(false_outfalls), ur=len(unrooted)))


# ---- H16 -----------------------------------------------------------------------------
def m_H16():
    missing = []
    for r_name in ("reaches", "corridors", "rising_mains"):
        for key, lyr in ROLES[r_name]:
            cols = columns_of(key, lyr)
            if not cols:
                continue
            g = read(key, lyr)
            for c in ("US_NODE", "DS_NODE"):
                if c not in g.columns:
                    missing.append("%s/%s has no %s" % (GPKGS[key][0], lyr, c))
                else:
                    blank = int(g[c].isna().sum()
                                + (g[c].astype(str).str.strip() == "").sum())
                    if blank:
                        missing.append("%s/%s.%s: %s blank"
                                       % (GPKGS[key][0], lyr, c, format(blank, ",")))
    return not missing, (
        "every published pipe layer carries US_NODE and DS_NODE: %s. Topology recovered by "
        "snapping is a guess whose answer moves with the tolerance - the same W10 file gives "
        "7,919 pieces at 10 mm and 105 pieces with 311 loops at 2.5 m."
        % ("OK" if not missing else "; ".join(missing)))


# ---- H17 -----------------------------------------------------------------------------
def m_H17():
    import pandas as pd
    r, src = role("reaches", ("GND_FALL", "AGN_GRADE", "RISE_M"))
    n, _nsrc = role("nodes", ("VORTEX",))
    agn = pd.to_numeric(r.AGN_GRADE, errors="coerce").fillna(0).astype(int) == 1
    km = pd.to_numeric(r.LEN_M, errors="coerce") / 1000.0
    rise = pd.to_numeric(r.RISE_M, errors="coerce").fillna(0.0)
    vx = int(pd.to_numeric(n.VORTEX, errors="coerce").fillna(0).sum())
    total = km.sum()
    return None, (
        "{src}: {u:,.1f} km of {t:,.1f} km ({p:.2f} %) drains AGAINST the ground; cumulative "
        "climb {c:,.0f} m; worst single rise {w:.2f} m. {v:,} vortex drop shafts = "
        "{vk:.3f} per km. CONTEXT, NOT PERMISSION: NAMA's built network drains uphill on "
        "34.10 % of its length at 0.585 vortex drops per km; W11a was 42.5 % and 1.475/km. "
        "Published per philosophy sec 4, which requires the quantity REPORTED, not merely "
        "computed."
        .format(src=src, u=km[agn].sum(), t=total, p=km[agn].sum() / total * 100.0,
                c=rise.sum(), w=rise.max(), v=vx, vk=vx / total))


# ---- R1 ------------------------------------------------------------------------------
def m_R1():
    import w12.hydra as H
    r, src = role("reaches", ("DN", "QPK_LS", "SLOPE_LAID", "DOD_PK"))
    dn = r.DN.astype(int).values
    s = r.SLOPE_LAID.astype(float).values / 100.0
    q = r.QPK_LS.astype(float).values / 1000.0
    pub = r.DOD_PK.astype(float).values
    surcharged, worst, n_off = 0, 0.0, 0
    for i in range(len(dn)):
        y, _v = H.pipe_state(int(dn[i]), float(s[i]), float(q[i]))
        if y is None:
            surcharged += 1
            continue
        d = abs(y - pub[i])
        worst = max(worst, d)
        n_off += int(d > 0.005)
    return (surcharged == 0 and n_off == 0), (
        "{src}: d/D recomputed from DN, laid gradient and peak flow with hydra.pipe_state on "
        "all {n:,} reaches. {s:,} are SURCHARGED - the bore cannot pass the flow at "
        "y/D = 0.95, which is a design failure and not a large number; W10 shipped five and "
        "nothing in it told 'full' from 'over capacity'. Worst disagreement with the "
        "published DOD_PK {w:.6f}; {o:,} reaches over 0.005."
        .format(src=src, n=len(dn), s=surcharged, w=worst, o=n_off))


# ---- R2 ------------------------------------------------------------------------------
def m_R2():
    import numpy as np
    C = _crit()
    r, src = role("reaches", ("DN", "US_DEPTH", "DS_DEPTH", "COVER_US", "COVER_DN"))
    dn = r.DN.astype(int).values
    cu = np.array([C.cover(int(d), float(z))
                   for d, z in zip(dn, r.US_DEPTH.astype(float).values)])
    cd = np.array([C.cover(int(d), float(z))
                   for d, z in zip(dn, r.DS_DEPTH.astype(float).values)])
    dU = np.abs(cu - r.COVER_US.astype(float).values)
    dD = np.abs(cd - r.COVER_DN.astype(float).values)
    under = int(((cu < C.MIN_COVER_CROWN - 1e-9) | (cd < C.MIN_COVER_CROWN - 1e-9)).sum())
    off = int(((dU > 1e-6) | (dD > 1e-6)).sum())
    return (under == 0 and off == 0), (
        "{src}: cover recomputed from the invert depth and the reach's OWN outside diameter "
        "with criteria.cover(). {u:,} reaches below the {m:.2f} m minimum on the "
        "recomputation; {o:,} disagree with the published COVER_US / COVER_DN (worst "
        "{w:.6f} m). This regression exists because a wall allowance was 0.10 in one module "
        "and 0.05 in another and failed every reach by exactly 50 mm."
        .format(src=src, u=under, m=C.MIN_COVER_CROWN, o=off, w=max(dU.max(), dD.max())))


# ---- R3 ------------------------------------------------------------------------------
def m_R3():
    import pandas as pd
    C = _crit()
    r, src = role("reaches", ("ON_DUAL_M", "CROSS_ID"))
    d = pd.to_numeric(r.ON_DUAL_M, errors="coerce").fillna(0.0)
    has_id = r.CROSS_ID.astype(str).str.strip() != ""
    unscheduled = r[(d > 1e-9) & ~has_id]
    over_cap = r[d > C.DUAL_XING_MAX_M + 1e-9]
    cor, csrc = role("corridors", ("ALONG_DUAL", "PIPE_OK", "LEN_M"))
    along = cor[pd.to_numeric(cor.ALONG_DUAL, errors="coerce").fillna(0).astype(int) == 1]
    still_ok = along[pd.to_numeric(along.PIPE_OK, errors="coerce").fillna(0).astype(int) == 1]
    ok = unscheduled.empty and over_cap.empty and still_ok.empty
    return ok, (
        "{src}: {n} reaches carry {m:,.0f} m of dual-carriageway contact; {u} are NOT in the "
        "crossings register and {c} exceed the {cap:.0f} m crossing cap. {cs}: {a:,} "
        "corridors ({ak:.2f} km) run ALONG a dual carriageway and {s:,} of them are STILL "
        "published PIPE_OK = 1 ({sk:.2f} km) - project rule 7 is declared in the schema and "
        "not enforced in the data. Owned by the corridor agent; measured here because a "
        "regression that stops being measured stops being a regression."
        .format(src=src, n=int((d > 1e-9).sum()), m=d.sum(), u=len(unscheduled),
                c=len(over_cap), cap=C.DUAL_XING_MAX_M, cs=csrc, a=len(along),
                ak=along.LEN_M.sum() / 1000.0, s=len(still_ok),
                sk=still_ok.LEN_M.sum() / 1000.0))


# ---- R4 ------------------------------------------------------------------------------
def m_R4():
    import pandas as pd
    r, src = role("reaches", ("ON_WADI_M", "CROSS_ID"))
    x, _xsrc = role("crossings", ("CROSS_ID", "OBSTACLE"))
    w = pd.to_numeric(r.ON_WADI_M, errors="coerce").fillna(0.0)
    ids = r.CROSS_ID.astype(str).str.strip()
    unscheduled = r[(w > 1e-9) & (ids == "")]
    wadi_ids = set(x.loc[x.OBSTACLE.astype(str) == "wadi", "CROSS_ID"].astype(str))
    wrong_obstacle = r[(w > 1e-9) & (ids != "") & ~ids.isin(wadi_ids)]
    haz_ok, haz_what = external_present("hazard")
    ok = unscheduled.empty and wrong_obstacle.empty
    return ok, (
        "{src}: {n:,} reaches carry {km:,.2f} km of contact with wadi ground. {u:,} have NO "
        "CROSS_ID - a pipe in a place it may not be; {b:,} carry an id whose register row "
        "names a DIFFERENT obstacle, which schedules something else. Hazard grid present: "
        "{h} ({hw}). THE UNTESTED FRACTION MUST TRAVEL WITH THIS NUMBER: the 50-year grid "
        "covers 45 % of the study area and no-data is read as DRY HIGH GROUND (engineer, "
        "2026-09-03), so this is a result about the tested half."
        .format(src=src, n=int((w > 1e-9).sum()), km=w.sum() / 1000.0, u=len(unscheduled),
                b=len(wrong_obstacle), h=haz_ok, hw=haz_what))


# ---- G1 ------------------------------------------------------------------------------
def m_G1():
    import pandas as pd
    r, src = role("reaches", ("SLOPE_LAID", "SLOPE_MIN"))
    laid = pd.to_numeric(r.SLOPE_LAID, errors="coerce")
    mn = pd.to_numeric(r.SLOPE_MIN, errors="coerce")
    missing = int(laid.isna().sum() + mn.isna().sum())
    at_min = int((laid - mn).abs().lt(1e-12).sum())
    return missing == 0, (
        "{src}: both the LAID gradient and its governing minimum are published on every "
        "reach ({m:,} blank). {a:,} of {n:,} reaches ({p:.1f} %) are laid exactly AT their "
        "minimum. A layer carrying only the minimum cannot be checked; one carrying only the "
        "laid value cannot be justified (philosophy sec 5)."
        .format(src=src, m=missing, a=at_min, n=len(r), p=at_min / len(r) * 100.0))


# ---- G2 ------------------------------------------------------------------------------
def m_G2():
    r, src = role("reaches", ("SIZED_BY", "GRAD_BY"))
    s_blank = int((r.SIZED_BY.astype(str).str.strip() == "").sum())
    g_blank = int((r.GRAD_BY.astype(str).str.strip() == "").sum())
    gcounts = ", ".join("%s %s" % (k, format(v, ","))
                        for k, v in r.GRAD_BY.value_counts().items())
    return (s_blank == 0 and g_blank == 0), (
        "{src}: every reach records what set its diameter and what set its gradient - "
        "{s:,} and {g:,} blank. GRAD_BY [{c}]."
        .format(src=src, s=s_blank, g=g_blank, c=gcounts))


# ---- G3 ------------------------------------------------------------------------------
def m_G3():
    r, src = role("reaches", ("US_NODE", "DS_NODE", "EDGE_UID"))
    n, nsrc = role("nodes", ("NODE_UID",))
    known = set(n.NODE_UID.astype(str))
    refs = set(r.US_NODE.astype(str)) | set(r.DS_NODE.astype(str))
    dangling = refs - known
    dup_n = int(n.NODE_UID.duplicated().sum())
    dup_e = int(r.EDGE_UID.duplicated().sum())
    return (not dangling and dup_n == 0 and dup_e == 0), (
        "{src} + {nsrc}: {d:,} node ids referenced by an arc do not exist in the node layer "
        "(e.g. {ex}); {dn:,} duplicated NODE_UID; {de:,} duplicated EDGE_UID. A dangling id "
        "is a silent orphan; a duplicated key means two things claim to be one thing."
        .format(src=src, nsrc=nsrc, d=len(dangling), ex=sorted(dangling)[:3], dn=dup_n,
                de=dup_e))


# ---- G4 ------------------------------------------------------------------------------
def m_G4():
    import fiona
    mf = RUN_DIR / "manifest.json"
    if not mf.is_file():
        return False, "%s does not exist - the ledger that answers G4 is absent" % mf
    m = json.loads(mf.read_text(encoding="utf-8"))
    recorded = set()
    for s in m.get("stages", []):
        recorded.add(str(s.get("stage", "?")))
    expected = {"s1_roads", "s2_orient", "s3_hierarchy", "s4_chambers", "s5_flows",
                "s6_levels", "s7_pumps", "s8_export"}
    absent = sorted(expected - recorded)
    with_layer = sorted(k for k in GPKGS if "manifest" in layers_of(k))
    without = sorted(k for k in GPKGS if gpkg(k).is_file() and "manifest" not in layers_of(k))
    empties = []
    for key in GPKGS:
        if not gpkg(key).is_file():
            continue
        for lyr in layers_of(key):
            try:
                with fiona.open(str(gpkg(key)), layer=lyr) as src:
                    if len(src) == 0:
                        empties.append("%s/%s" % (GPKGS[key][0], lyr))
            except Exception:                           # pragma: no cover
                pass
    return (not absent and not empties), (
        "run/manifest.json records {n} of 8 stages: {r}. MISSING: {a}. "
        "ROOT CAUSE, traced and reproducible: contract.Manifest.records (contract.py:3246) "
        "is a CLASS attribute holding only the records made in THIS python process, and "
        "Manifest.save (contract.py:3265) writes `stages=[r.to_dict() for r in cls.records]` "
        "over the whole file with `open(p, 'w')`. run_all.py:377 launches every stage as a "
        "SEPARATE subprocess, so cls.records starts empty each time and the file is "
        "TRUNCATED to the one stage that just ran. The class docstring says 'One JSON, "
        "APPENDED by every stage' - it does not append. The file therefore always holds the "
        "last stage to finish, and G4 - 'no stage silently doing nothing' - can never be "
        "answered by the ledger that exists to answer it. Per-GeoPackage `manifest` layers "
        "survive because they are written into their own GeoPackage: present in {w}, ABSENT "
        "from {wo}. Empty published layers: {e}."
        .format(n=len(recorded), r=sorted(recorded), a=(absent or "none"), w=with_layer,
                wo=without, e=(empties or "none")))


# ---- G5 ------------------------------------------------------------------------------
def m_G5():
    bad = []
    for r_name in ("reaches", "nodes"):
        g, src = role(r_name, ("SRC", "CONFIDENCE"))
        for c in ("SRC", "CONFIDENCE"):
            blank = int(g[c].isna().sum() + (g[c].astype(str).str.strip() == "").sum())
            if blank:
                bad.append("%s.%s: %s blank" % (src, c, format(blank, ",")))
    r, rsrc = role("reaches", ("SRC", "CONFIDENCE"))
    srcs = ", ".join("%s %s" % (k, format(v, ",")) for k, v in r.SRC.value_counts().items())
    conf = ", ".join("%s %s" % (k, format(v, ","))
                     for k, v in r.CONFIDENCE.value_counts().items())
    return not bad, (
        "{s}: SRC [{a}], CONFIDENCE [{b}]. Blank: {c}. Every published number must be "
        "traceable to what produced it and to how far it is trusted."
        .format(s=rsrc, a=srcs, b=conf, c=(bad or "none")))


# ---- C1 ------------------------------------------------------------------------------
def m_C1():
    import pandas as pd
    n, src = role("nodes", ("DROP_M", "DROP_WHY", "DROP_TYPE"))
    d = pd.to_numeric(n.DROP_M, errors="coerce").fillna(0.0)
    why = n.DROP_WHY.astype(str).str.strip()
    nameless = n[(d > 1e-9) & (why == "")]
    counts = ", ".join("%s %s" % ((k or "(blank)"), format(v, ","))
                       for k, v in why.value_counts().items())
    return nameless.empty, (
        "{src}: {n:,} chambers carry a drop and {b:,} of them name no reason. DROP_WHY "
        "[{c}]. Concept rule 1: every drop is flagged with the reason it exists - a drop "
        "with no reason cannot be told from a drop used to dodge a station, which philosophy "
        "sec 5 prohibits by name."
        .format(src=src, n=int((d > 1e-9).sum()), b=len(nameless), c=counts))


# ---- C2 ------------------------------------------------------------------------------
def m_C2():
    import pandas as pd
    n, src = role("nodes", ("JOIN_MAIN", "JOIN_OFF_M", "JOIN_WHY"))
    jm = pd.to_numeric(n.JOIN_MAIN, errors="coerce").fillna(0).astype(int)
    off = pd.to_numeric(n.JOIN_OFF_M, errors="coerce").fillna(0.0)
    why = n.JOIN_WHY.astype(str).str.strip()
    vacuous = bool(jm.sum() == 0 and off.abs().max() == 0 and (why == "").all())
    verdict = ("THESE THREE COLUMNS ARE ENTIRELY VACUOUS ON THE DESIGN LAYER - the schema "
               "declares concept rule 2 and the data does not carry it. Readiness scores the "
               "check runnable because the columns EXIST; that is exactly the blank the rule "
               "forbids, one level down." if vacuous else "populated.")
    extra = ""
    try:
        s = read("export", "subnetworks")
        oc = read("export", "outfall_check")
        gap = pd.to_numeric(s.GAP_M, errors="coerce").fillna(0.0)
        offm = pd.to_numeric(s.OFF_M, errors="coerce").fillna(0.0)
        nowhy = s[(offm > 1e-6) & (s.WHY.astype(str).str.strip() == "")]
        below = oc[pd.to_numeric(oc.PCT_BELOW, errors="coerce").fillna(0.0) > 50.0]
        extra = (" W12_export.gpkg/subnetworks: {ns:,} subnetworks; {far} do not reach the "
                 "main pipe at the 50 m tolerance (worst {gm:,.0f} m); {ol} discharge OFF "
                 "their own low point (worst {om:,.0f} m) and {nw} of those record no reason "
                 "on THIS layer - the reason is written on the node layer's JOIN_WHY "
                 "instead, so the two halves of one rule live in two files. "
                 "W12_export.gpkg/outfall_check: {nb} of {no} outfalls discharge with MORE "
                 "THAN HALF their catchment BELOW them - {bk:,.1f} km, worst outlet "
                 "{ab:.2f} m above its own low point. W11b was 42 outfalls / 389.5 km / "
                 "22.8 m: improved, not fixed."
                 .format(ns=len(s), far=int((gap > 50.0).sum()), gm=gap.max(),
                         ol=int((offm > 1e-6).sum()), om=offm.max(), nw=len(nowhy),
                         nb=len(below), no=len(oc), bk=below.LEN_KM.sum(),
                         ab=pd.to_numeric(oc.ABOVE_LOW, errors="coerce").max()))
    except Exception as exc:                            # pragma: no cover
        extra = " (could not read the subnetwork tables: %s)" % exc
    return not vacuous, (
        "{src}: JOIN_MAIN = 1 on {a:,} nodes; JOIN_OFF_M max {b:,.1f} m; JOIN_WHY populated "
        "on {c:,} of {n:,}. {v}{extra}"
        .format(src=src, a=int(jm.sum()), b=off.max(), c=int((why != "").sum()), n=len(n),
                v=verdict, extra=extra))


# ---- C3 ------------------------------------------------------------------------------
def m_C3():
    import pandas as pd
    c, src = role("connections", ("CAN_CONN", "CONN_WHY", "CONN_NEED"))
    can = pd.to_numeric(c.CAN_CONN, errors="coerce").fillna(0).astype(int)
    need = pd.to_numeric(c.CONN_NEED, errors="coerce")
    why = c.CONN_WHY.astype(str).str.strip()
    cannot = (can == 0)
    unsized = c[cannot & (need.isna() | (why == ""))]
    unserved_n, unserved_q = 0, 0.0
    try:
        u = read("chambers", "unserved")
        unserved_n = len(u)
        unserved_q = float(pd.to_numeric(u.Q_ADF_M3D, errors="coerce").sum())
    except Exception:                                   # pragma: no cover
        pass
    return unsized.empty, (
        "{src}: {n:,} of {t:,} plots CANNOT reach their chamber on gravity; {u:,} of those "
        "are flagged without a size or a reason. Deepest ask CONN_NEED = {d:.2f} m - how "
        "much deeper the sewer would have to be on that run. Separately {un:,} plots "
        "carrying {uq:,.1f} m3/d sit on the `unserved` layer and are NAMED rather than "
        "dropped. Concept rule 5 and 'flag, do not solve': a plot that is not connected must "
        "be named, or the drop is silent."
        .format(src=src, n=int(cannot.sum()), t=len(c), u=len(unsized), d=need.max(),
                un=unserved_n, uq=unserved_q))


# ---- C4 ------------------------------------------------------------------------------
def m_C4():
    from w12.contract import NAME_RE
    lines = []
    ok = True
    for r_name, what in (("reaches", "conduits"), ("nodes", "manholes")):
        g, src = role(r_name, ("NAME", "TOWN", "SUBNET"))
        nm = g.NAME.astype(str).str.strip()
        tw = g.TOWN.astype(str).str.strip()
        blank_n = int((nm == "").sum())
        blank_t = int((tw == "").sum())
        named = nm[nm != ""]
        unparsable = int(sum(1 for v in named if not NAME_RE.match(v)))
        dup = int(named.duplicated().sum())
        lines.append("{s} ({w}): {bn:,} of {t:,} carry NO NAME, {bt:,} no TOWN, {up:,} names "
                     "do not parse against contract.NAME_RE, {dp:,} names are duplicated"
                     .format(s=src, w=what, bn=blank_n, t=len(g), bt=blank_t, up=unparsable,
                             dp=dup))
        if blank_n or unparsable or dup:
            ok = False
    # MEASURED. "10,178 chambers" was hand-typed from a run-003 log line; s8 has re-run
    # since and the true figure moved. A stale number in a deliverable is the drift this
    # project keeps paying for.
    unnamed = "not readable"
    try:
        en = read("export", "nodes")
        unnamed = "%s of %s" % (format(int((en.NAME.astype(str).str.strip() == "").sum()),
                                       ","), format(len(en), ","))
    except Exception:                                   # pragma: no cover
        pass
    tail = ("Concept rule 8 declares three tier codes (TM / SM / L); this design's tier set "
            "has more, and s8 publishes the shortfall itself - {u} chambers on the export "
            "layer that the grammar has no token for, measured here rather than quoted. NO "
            "NAME IS INVENTED - which is right - and it is still an unnamed deliverable."
            .format(u=unnamed))
    return ok, "; ".join(lines) + ". " + tail


# ---- C5 ------------------------------------------------------------------------------
def m_C5():
    import pandas as pd
    st, ssrc = role("stations", ("N_SUBNET", "CATCH_KM", "WHY"))
    rm, _rsrc = role("rising_mains", ("DS_TYPE", "LEN_M"))
    why = st.WHY.astype(str).str.strip()
    no_catch = int((pd.to_numeric(st.CATCH_KM, errors="coerce").fillna(0.0) <= 0).sum())
    no_sub = int((pd.to_numeric(st.N_SUBNET, errors="coerce").fillna(0) <= 0).sum())
    blank_why = int((why == "").sum())
    to_stp = int((rm.DS_TYPE.astype(str) == "stp").sum())
    orphan_rm = 0
    if "STATION" in rm.columns and "NODE_UID" in st.columns:
        orphan_rm = len(set(rm.STATION.astype(str)) - set(st.NODE_UID.astype(str)))
    ledger = []
    counts = {}
    for lyr in ("pruned", "refused"):
        if lyr in layers_of("pumps"):
            counts[lyr] = len(read("pumps", lyr))
            ledger.append("%s %s" % (lyr, format(counts[lyr], ",")))
    searched = [l for l in ("sites", "search_sites", "search", "trades", "sensitivity")
                if l in layers_of("pumps")]
    exported = (len(read("export", "stations")) if "stations" in layers_of("export") else -1)
    rejected = (len(read("export", "stations_rejected"))
                if "stations_rejected" in layers_of("export") else -1)

    # THE FUNNEL, READ FROM THE LAYER. "151 demanded by levels, 108 pruned" was copied out of
    # a run summary; the published funnel says 171 considered -> 63 demanded -> 43. Neither
    # the number nor the label survived, and it reconciled arithmetically the whole time
    # (151 - 108 = 43), which is exactly why a hand-typed reconciliation is worthless.
    funnel, funnel_txt, funnel_bad = {}, "ABSENT", ["no `funnel` layer on W12_pumps.gpkg"]
    if "funnel" in layers_of("pumps"):
        f = read("pumps", "funnel")
        for _i, row in f.iterrows():
            try:
                funnel[str(row.STEP)] = float(row.VALUE)
            except (TypeError, ValueError):
                pass
        funnel_txt = ", ".join("%s %s" % (k, format(int(v), ","))
                               for k, v in funnel.items())
        funnel_bad = []
        n0 = funnel.get("N0_considered")
        n1 = funnel.get("N1_demanded")
        n2 = funnel.get("N2_published")
        pr = funnel.get("pruned", counts.get("pruned"))
        rf = funnel.get("refused", counts.get("refused"))
        if None in (n0, n1, n2, pr, rf):
            funnel_bad.append("the funnel does not name all of N0/N1/N2/pruned/refused")
        else:
            if abs((n0 - pr) - n1) > 1e-9:
                funnel_bad.append("N0 %g - pruned %g != N1 %g" % (n0, pr, n1))
            if abs((n1 - rf) - n2) > 1e-9:
                funnel_bad.append("N1 %g - refused %g != N2 %g" % (n1, rf, n2))
            if abs(n2 - len(st)) > 1e-9:
                funnel_bad.append("the funnel publishes N2 %g and the stations layer holds %d"
                                  % (n2, len(st)))
        for k in ("pruned", "refused"):
            if k in counts and k in funnel and abs(funnel[k] - counts[k]) > 1e-9:
                funnel_bad.append("funnel %s %g against the %s layer's %d"
                                  % (k, funnel[k], k, counts[k]))

    # THE TWO STATION COUNTS MUST RECONCILE THROUGH A NAMED LIST. W11b shipped with 14
    # demanded and 47 designed and no ledger between them; the difference here has to be
    # exactly the rows s8 publishes as rejected, or one of the two numbers is a guess.
    reconcile_bad = []
    if exported >= 0 and rejected >= 0 and len(st) - rejected != exported:
        reconcile_bad.append("s7 publishes %d stations and s8 publishes %d with %d named on "
                             "stations_rejected - the difference is not accounted for"
                             % (len(st), exported, rejected))
    elif exported >= 0 and rejected < 0:
        reconcile_bad.append("s8 publishes %d stations against s7's %d and names no rejected "
                             "list - a silent drop" % (exported, len(st)))

    ok = (blank_why == 0 and no_catch == 0 and no_sub == 0 and orphan_rm == 0
          and to_stp == 0 and bool(searched) and bool(ledger)
          and not funnel_bad and not reconcile_bad)
    return ok, (
        "{s}: {n} stations, {m} rising mains, {km:,.2f} km, longest {mx:,.0f} m. WHY [{w}] - "
        "{b} blank; {nc} carry no catchment and {ns} no subnetwork count. {stp} mains lift "
        "ALL THE WAY TO THE WORKS against concept rule 6, which wants a main to lift only to "
        "where gravity resumes - a breach whenever it is not zero. {orm} mains name a "
        "station that is not published. POSITION CHOSEN NOT TRIGGERED: the search evidence "
        "is published on {se}; the ADD / TAKE-AWAY ledger is [{ld}]. "
        "COUNT RECONCILIATION, read from W12_pumps.gpkg/funnel: [{fn}] - arithmetic {fv}. "
        "s7 publishes {n} stations; W12_export.gpkg publishes {ex} and names {rj} on "
        "stations_rejected - {rv}."
        .format(s=ssrc, n=len(st), m=len(rm), km=rm.LEN_M.sum() / 1000.0, mx=rm.LEN_M.max(),
                w=", ".join("%s %s" % (k, format(v, ","))
                            for k, v in why.value_counts().items()),
                b=blank_why, nc=no_catch, ns=no_sub, stp=to_stp, orm=orphan_rm,
                se=(searched or "NOTHING"), ld=(", ".join(ledger) or "ABSENT"),
                ex=exported, rj=rejected, fn=funnel_txt,
                fv=("reconciles" if not funnel_bad else "DOES NOT RECONCILE: "
                    + "; ".join(funnel_bad)),
                rv=("reconciles" if not reconcile_bad else "DOES NOT RECONCILE: "
                    + "; ".join(reconcile_bad))))


MEASURE: Dict[str, Callable[[], Tuple[Optional[bool], str]]] = {
    "H1": m_H1, "H1a": m_H1a, "H2": m_H2, "H3": m_H3, "H4": m_H4, "H4b": m_H4b,
    "H4c": m_H4c, "H5": m_H5, "H6": m_H6, "H7": m_H7, "H8": m_H8, "H9": m_H9,
    "H10": m_H10, "H11": m_H11, "H12": m_H12, "H13": m_H13, "H14": m_H14,
    "H15": m_H15, "H16": m_H16, "H17": m_H17,
    "R1": m_R1, "R2": m_R2, "R3": m_R3, "R4": m_R4,
    "G1": m_G1, "G2": m_G2, "G3": m_G3, "G4": m_G4, "G5": m_G5,
    "C1": m_C1, "C2": m_C2, "C3": m_C3, "C4": m_C4, "C5": m_C5,
}

assert set(MEASURE) == set(CHECKS), sorted(set(CHECKS) ^ set(MEASURE))


#: Which fall-throughs are KNOWN AND ACCEPTED, and why. `role()` picks the first published
#: layer carrying the fields a check needs, so a check can silently move to another stage's
#: output; anything not on this list is a NEW substitution and fails
#: `test_which_published_layer_every_check_actually_read`.
ACCEPTED_FALLTHROUGH: Dict[Tuple[str, str], str] = {
    ("nodes", "W12_export.gpkg/nodes"):
        "H1a COND 2 needs ON_WADI and the stage-6 node layer does not publish it; s4 writes "
        "it and s8 carries it. Declared, not silent - and it is the one condition in this "
        "file measured off a layer other than stage 6's.",
    ("connections", "W12_export.gpkg/connections"):
        "C3 needs CAN_CONN / CONN_WHY / CONN_NEED; the connection layer is a stage-8 "
        "deliverable and stage 6 publishes no connections at all.",
    ("subnetworks", "W12_export.gpkg/subnetworks"):
        "C2's subnetwork half exists only on the stage-8 layer.",
    ("crossings", "W12_export.gpkg/crossings"):
        "only if the stage-6 register disappears; the export register carries ANG_MEAS and "
        "SQUARE, which the design register does not.",
}


_RESULTS: Dict[str, Tuple[Optional[bool], str]] = {}


def measure(cid: str) -> Tuple[Optional[bool], str]:
    """Run one check ONCE per session.

    The readiness table and the per-check test both need every verdict; without this the
    34 measurements run twice, and R1's and H7's per-reach loops over 56,525 rows are the
    slow half of the suite.
    """
    if cid not in _RESULTS:
        _RESULTS[cid] = MEASURE[cid]()
    return _RESULTS[cid]


# ======================================================================================
# THE TESTS
# ======================================================================================

@pytest.mark.audit
def test_the_readiness_table_is_published_and_every_check_can_run():
    """PHILOSOPHY SEC 8: 'A CHECK THAT CANNOT RUN IS A FAILURE, NOT A BLANK.'

    This is the deliverable. It writes the table to run/audit/ and asserts what the rule
    actually says - that all 34 run - rather than printing a fraction and passing.
    """
    import pandas as pd
    tab = pd.DataFrame(readiness_rows())

    # Run every measurement so the table carries the VERDICT beside the readiness. A table
    # that says a check could have run, without saying what it said, is half an answer.
    results, details = [], []
    for cid in tab.check:
        try:
            verdict, detail = measure(cid)
            results.append({True: "PASS", False: "BREACH", None: "REPORT"}[verdict])
            details.append(detail)
        except Exception as exc:                        # a check that raises is a failure
            results.append("ERROR")
            details.append("%s: %s" % (type(exc).__name__, exc))
    tab["result"] = results
    tab["measured"] = details

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    csv = AUDIT_DIR / "W12_audit_readiness.csv"
    tab.to_csv(csv, index=False, encoding="utf-8")

    # the same table as a document, because a CSV is not something anyone reads
    md = AUDIT_DIR / "W12_audit_readiness.md"
    lines = [
        "# W12 audit readiness - all 34 checks of `contract.AUDIT_NEEDS`",
        "",
        "Philosophy sec 8: **a check that cannot run is a FAILURE, not a blank.**",
        "Run 003 reported 5 of 34 runnable. That was a probe fault, not a data gap - the",
        "probe unioned columns from three of the eight published GeoPackages and never",
        "opened stage 6's or stage 8's output. Every field of all 34 is published today.",
        "",
        "| check | enforces | source | severity | runnable | result | reads / missing "
        "| wired in |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _i, r in tab.iterrows():
        lines.append("| **%s** | %s | %s | %s | %s | %s | %s | `%s` |"
                     % (r.check, r.enforces, r.source, r.severity,
                        "yes" if r.can_run else "**NO**",
                        ("**%s**" % r.result) if r.result in ("BREACH", "ERROR")
                        else r.result,
                        (r.reads if r.can_run else r.missing).replace("|", "/"),
                        r.wired_in))
    lines += ["", "## What each check measured", ""]
    for _i, r in tab.iterrows():
        lines.append("**%s - %s**  \n%s\n" % (r.check, r.result,
                                              str(r.measured).replace("|", "/")))
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    can = tab[tab.can_run]
    cannot = tab[~tab.can_run]
    print("\n    [readiness] %d of %d audit checks can run against the PUBLISHED SET - all "
          "%d GeoPackages, not the three that stages 3-5 wrote"
          % (len(can), len(tab), len(GPKGS)))
    print("    [readiness] table written to %s and %s" % (csv, md))
    for _i, row in tab.iterrows():
        print("        %s %-6s %-4s %-9s %s | %s"
              % ("run " if row.can_run else "CANT", row.result, row.check, row.severity,
                 row.enforces[:62], row.source))
        print("             %s %s" % ("reads" if row.can_run else "MISSING",
                                      row.reads if row.can_run else row.missing))
        print("             wired in %s" % row.wired_in)
    print("    [audit] %s"
          % ", ".join("%s %d" % (k, v) for k, v in tab.result.value_counts().items()))
    print("    [readiness] the run-003 figure of 5 of 34 was a PROBE FAULT, not a data gap: "
          "test_invariants.py::test_which_audit_checks_can_run_at_all_is_reported unions "
          "columns from W12_hier, W12_flows and W12_chambers only, and conftest.GPKGS has no "
          "key for W12.gpkg, W12_levels.gpkg or W12_export.gpkg - so no test in the suite "
          "could open stage 6's or stage 8's output. Every field of all 34 checks is "
          "published today.")
    # A CHECK THAT RAISED IS A CHECK THAT DID NOT RUN. The table recorded ERROR rows and
    # this test still passed on them, which is the same green-over-a-blank the probe it
    # replaced was written to kill.
    errored = tab[tab.result == "ERROR"]
    assert cannot.empty and errored.empty, (
        "%d of %d audit checks cannot run and %d raised. Each is a BLOCKING failure:\n"
        % (len(cannot), len(tab), len(errored))
        + "\n".join("  cannot run %s: %s" % (r.check, r.missing)
                     for _i, r in cannot.iterrows())
        + "\n".join("  raised     %s: %s" % (r.check, r.measured)
                     for _i, r in errored.iterrows()))


@pytest.mark.audit
def test_which_published_layer_every_check_actually_read():
    """WHICH DESIGN DID THE AUDIT AUDIT?

    `role()` returns the first published layer carrying the fields a check asks for. When
    stage 6 does not publish a field, the check moves to stage 8's output WITHOUT SAYING SO
    and the answer is then about a different set of levels. That already happens once - H1a's
    COND 2 reads ON_WADI off the stage-8 node layer - and nothing announced it; the file's
    own header claimed every H-check read `W12.gpkg`.

    This publishes every resolution and fails on any fall-through that is not declared in
    `ACCEPTED_FALLTHROUGH` with a reason.
    """
    for cid in CHECKS:
        measure(cid)                                   # memoised; populates RESOLVED
    seen: Dict[Tuple[str, str], List[str]] = {}
    for rname, fields, srcname in RESOLVED:
        seen.setdefault((rname, srcname), []).append(",".join(fields) or "(none)")
    print("\n    [layers] every (role -> published layer) this audit resolved:")
    undeclared = []
    for (rname, srcname), uses in sorted(seen.items()):
        first = ROLES[rname][0]
        preferred = "%s/%s" % (GPKGS[first[0]][0], first[1])
        tag = "preferred" if srcname == preferred else "FELL THROUGH from " + preferred
        print("        %-12s -> %-28s  %s  (%d call sites)"
              % (rname, srcname, tag, len(uses)))
        if srcname != preferred:
            why = ACCEPTED_FALLTHROUGH.get((rname, srcname))
            print("             %s" % (why or "*** NOT DECLARED ***"))
            if not why:
                undeclared.append("%s -> %s (asked for %s)"
                                  % (rname, srcname, "; ".join(sorted(set(uses)))))
    assert not undeclared, (
        "these checks silently read a layer other than the one this file claims to audit, "
        "and the substitution is not declared in ACCEPTED_FALLTHROUGH:\n  "
        + "\n  ".join(undeclared))


@pytest.mark.audit
def test_every_external_input_the_audit_depends_on_is_present():
    """The five `external` entries in AUDIT_NEEDS are inputs, not layers. An input that is
    only assumed is the same blank the philosophy forbids."""
    missing = []
    for name in sorted(EXTERNALS):
        ok, what = external_present(name)
        print("\n    [external] %s %-10s %s" % ("OK  " if ok else "MISS", name, what))
        if not ok:
            missing.append("%s (%s)" % (name, what))
    assert not missing, "audit inputs not present: %s" % missing


@pytest.mark.audit
@pytest.mark.parametrize("cid", list(CHECKS))
def test_audit_check(cid):
    """One test per rule. `AUDIT_NEEDS` declares 34; philosophy sec 8 requires one check per
    rule, 'generated from the tables above so a rule cannot exist without its check'."""
    c = CHECKS[cid]
    verdict, detail = measure(cid)
    tag = {True: "PASS", False: "BREACH", None: "REPORT"}[verdict]
    print("\n    [%s] %s - %s" % (cid, tag, c.enforces))
    print("    [%s] source: %s" % (cid, c.source))
    print("    [%s] %s" % (cid, detail))
    if verdict is None:
        if c.wired_elsewhere:
            print("    [%s] blocking assertion lives in %s" % (cid, c.wired_elsewhere))
        return
    assert verdict, "%s BREACHED (%s): %s" % (cid, c.source, detail)


@pytest.mark.audit
def test_the_two_published_reach_layers_are_one_design():
    """NOT one of the 34 - it is what wiring them up turned up, and it decides which numbers
    every other check is about.

    `s6_levels` writes W12.gpkg. `s8_export` publishes W12_export.gpkg - the deliverable.
    For a while s8 built its OWN levels from a stand-in inherited from W11b and declared it
    ('SECOND SET OF LEVELS: yes'), which was honest and was not a resolution: the two layers
    then differed by 65.7 m of cover and 72.9 m of drop, and the export's 83.09 m drop was
    four times `criteria.DROP_CEILING_M`. Two passes that both compute an invert is
    inheritance row 10.

    s8 has since been repointed at the stage-6 levels and the two agree. THIS TEST STAYS: it
    is the regression that fails the moment a second set of levels reappears, and it is the
    only thing standing between "the client's file" and "the audited file" being different
    designs again.
    """
    import pandas as pd
    C = _crit()
    a = read("design", "reaches")
    b = read("export", "reaches")
    an = read("design", "nodes")
    bn = read("export", "nodes")
    ca = pd.concat([a.COVER_US, a.COVER_DN], axis=1).max(axis=1).max()
    cb = pd.concat([b.COVER_US, b.COVER_DN], axis=1).max(axis=1).max()
    da, db = float(an.DROP_M.max()), float(bn.DROP_M.max())
    print("\n    [two-designs] W12.gpkg (s6_levels) vs W12_export.gpkg (s8 stand-in): "
          "reaches %s / %s; km %.2f / %.2f; deepest cover %.2f / %.2f m; past the 12 m cap "
          "%s / %s; largest drop %.2f / %.2f m; vortex shafts %s / %s; max velocity "
          "%.3f / %.3f m/s"
          % (format(len(a), ","), format(len(b), ","), a.LEN_M.sum() / 1000.0,
             b.LEN_M.sum() / 1000.0, ca, cb,
             format(int((pd.concat([a.COVER_US, a.COVER_DN], axis=1).max(axis=1)
                         > C.MAX_COVER).sum()), ","),
             format(int((pd.concat([b.COVER_US, b.COVER_DN], axis=1).max(axis=1)
                         > C.MAX_COVER).sum()), ","),
             da, db, format(int(an.VORTEX.sum()), ","), format(int(bn.VORTEX.sum()), ","),
             a.V_PK_MS.max(), b.V_PK_MS.max()))
    assert abs(ca - cb) < 0.5 and abs(da - db) < 0.5, (
        "the two published reach layers describe DIFFERENT DESIGNS: deepest cover %.2f m "
        "against %.2f m, largest drop %.2f m against %.2f m - and the second is past the "
        "%.0f m drop ceiling that philosophy sec 5 says the stage must REFUSE to publish "
        "past, never clip. Every H-check in this file reads W12.gpkg (stage 6); auditing "
        "the file the client actually receives gives a different answer, and that is the "
        "finding." % (ca, cb, da, db, C.DROP_CEILING_M))
