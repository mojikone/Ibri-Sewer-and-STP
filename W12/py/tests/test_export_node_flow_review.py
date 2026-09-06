"""ADVERSARIAL REVIEW of the export's levels rewire, 2026-09-06.

The rewire moved every invert, gradient and diameter onto s6_levels' published answer and
proved it, per row, with LEVELS_BY and a verify() that re-opens s6's own GeoPackage. What
it did NOT move was the flow at a CHAMBER, and that is where the two-answers defect it
existed to kill survived one layer over.

MEASURED on the 12:00 export, from the published files:

  * s6's NODE layer has NO PF and NO PF_METH column. `read_s6_levels()` read
    `NC("PF", 1.0)`, which returns the DEFAULT, so the export published PF = 1.0 and
    PF_METH = 'held' on ALL 56,943 chambers - a constant column dressed as the leveller's
    answer - while the reach leaving the same chamber carried s6's merrimack factor of
    about 3.62.
  * the outgoing reach's QPK_LS disagreed with its own chamber's Q_PK_LS on 26,482 of
    26,579 pairs, median ratio 3.50. contract.NODES defines Q_PK_LS as "the number the
    outgoing reach is sized on".
  * 21,221 of 56,943 chambers published a Q_PK_LS SMALLER than their own
    QADF x 1000/86400 x PF, which no non-negative infiltration can produce - because the
    peak was built from s6's accumulation while the row published this stage's.
  * tests/test_columns.py runs the constant-column rule over every stage's GeoPackage
    EXCEPT the deliverable: conftest.GPKGS lists neither W12_export.gpkg nor W12.gpkg. The
    published file was the one place that rule could not fire.

Every test below fails if any of those comes back. They read the PUBLISHED file, not the
in-memory model - a stage that verifies its own model verifies nothing.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.published

geopandas = pytest.importorskip("geopandas")
import geopandas as gpd                                              # noqa: E402

import s8_export as EX                                               # noqa: E402
from w12 import contract as CT                                       # noqa: E402


def _need(path: str, what: str):
    if not os.path.exists(path):
        pytest.skip(f"{what} has not been published ({os.path.basename(path)}) - run the "
                    f"pipeline first. A skip is visible; a silent pass is not.")


@pytest.fixture(scope="module")
def pub():
    _need(EX.GPKG_OUT, "the export")
    return (gpd.read_file(EX.GPKG_OUT, layer="nodes", ignore_geometry=True),
            gpd.read_file(EX.GPKG_OUT, layer="reaches", ignore_geometry=True))


def test_a_chambers_peak_flow_is_the_peak_flow_of_the_pipe_leaving_it(pub):
    """contract.NODES: Q_PK_LS is 'the number the outgoing reach is sized on'.

    Two layers of one file answering one question differently is inheritance row 10, and
    a factor of 3.5 on the flow every chamber is scheduled against is not a rounding."""
    nd, r = pub
    j = nd[["NODE_UID", "Q_PK_LS"]].merge(
        r[["US_NODE", "QPK_LS"]], left_on="NODE_UID", right_on="US_NODE", how="inner")
    want = pd.to_numeric(j.QPK_LS, errors="coerce")
    got = pd.to_numeric(j.Q_PK_LS, errors="coerce")
    off = (got - want).abs() > 0.01 * want.abs() + 0.01
    print(f"\n    [chamber vs pipe] {len(j):,} chambers have a published outgoing reach; "
          f"{int(off.sum()):,} disagree with it about the peak flow")
    assert not off.any(), (
        f"{int(off.sum()):,} of {len(j):,} chambers publish a peak flow their own outgoing "
        f"reach contradicts - median ratio "
        f"{float((got[off] / want[off].replace(0, np.nan)).median()):.2f}. The chamber and "
        f"the pipe leaving it are sized on ONE flow.")


def test_no_peak_factor_is_the_default_of_a_column_the_leveller_does_not_publish(pub):
    """s6 has no PF column on its nodes. A default read through a `.get(col, 1.0)` looks
    exactly like an answer, and PF = 1.0 on every row turns a peak flow into an average."""
    nd, _r = pub
    pf = pd.to_numeric(nd.PF, errors="coerce").dropna()
    if len(pf) < CT.VARY_MIN_ROWS:
        pytest.skip(f"only {len(pf)} chambers carry a peak factor at all")
    print(f"\n    [node PF] {pf.nunique():,} distinct factors over {len(pf):,} chambers, "
          f"{int(pd.to_numeric(nd.PF, errors='coerce').isna().sum()):,} NULL")
    assert pf.nunique() > 1, (
        f"every chamber carries PF = {pf.iloc[0]!r}. If that came from a default rather "
        f"than from a measurement it is a fabrication (inheritance row 22); if it is "
        f"genuinely constant, say so where a reader can see it.")
    meth = nd.PF_METH.fillna("").astype(str)
    assert set(meth.unique()) <= set(CT.PF_METH) | {""}, (
        f"PF_METH holds {sorted(set(meth.unique()) - set(CT.PF_METH) - {''})}, which is "
        f"outside contract.PF_METH")
    held_wrong = int(((meth == "held")
                      & (pd.to_numeric(nd.PF, errors="coerce").fillna(1.0) != 1.0)).sum())
    assert held_wrong == 0, f"{held_wrong} chambers say PF is HELD and carry PF != 1.0"


def test_a_published_peak_is_reproducible_from_the_row_it_sits_on(pub):
    """QPK = QADF x PF + QINF, and QINF is never negative. A row whose own peak is BELOW
    its own average times its own factor was assembled from two different accumulations."""
    nd, _r = pub
    q = pd.to_numeric(nd.Q_ADF_M3D, errors="coerce") * 1000.0 / 86400.0 \
        * pd.to_numeric(nd.PF, errors="coerce")
    pk = pd.to_numeric(nd.Q_PK_LS, errors="coerce")
    short = (q - pk) > 0.001                      # 1 mL/s - well above the 4-dp rounding
    print(f"\n    [reproducible] {int(short.sum()):,} of {len(nd):,} chambers publish a "
          f"peak below their own QADF x PF")
    assert not short.any(), (
        f"{int(short.sum()):,} chambers publish Q_PK_LS below QADF x PF, worst "
        f"{float((q - pk).max()):.3f} L/s. Infiltration cannot be negative, so the peak "
        f"and the average on those rows came from different accumulations.")


def test_the_deliverable_is_inside_the_constant_column_rule(pub):
    """tests/test_columns.py runs this rule over every stage EXCEPT the one that ships.

    conftest.GPKGS lists roads, orient, hier, chambers, flows, pumps and streams - not
    W12_export.gpkg and not W12.gpkg. That is why PF = 1.0 on 56,943 rows of the client's
    own file went unseen. Until conftest carries them, the rule runs here."""
    nd, r = pub
    bad = []
    for name, g, cols in (("nodes", nd, ("PF", "Q_PK_LS", "Q_ADF_M3D", "DEPTH_M",
                                         "COVER_M", "GRD_M", "INV_M")),
                          ("reaches", r, ("PF", "QPK_LS", "QADF_M3D", "SLOPE_LAID", "DN",
                                          "LEN_M", "V_PK_MS", "DOD_PK"))):
        for c in cols:
            if c not in g.columns:
                continue
            s = pd.to_numeric(g[c], errors="coerce").dropna()
            if len(s) >= CT.VARY_MIN_ROWS and s.nunique() == 1:
                bad.append(f"{name}.{c} = {s.iloc[0]!r} on all {len(s):,} rows")
    print(f"\n    [constants] {len(bad)} measured columns hold one value on every row")
    assert not bad, (
        "a column that should carry a measurement holds one value on every row of the "
        "DELIVERABLE. That is how ANGLE_DEG = 90 shipped on 3,290 crossings:\n  "
        + "\n  ".join(bad))


def test_no_headline_on_the_manifest_is_a_blank(pub):
    """`np.median` over a column with one NULL returns nan, and the 12:00 export shipped
    'median cover | nan | m' as a headline - on the manifest, the manifest CSV, and the
    DXF and KMZ banners that read them. A headline destroyed by a blank is as wrong as a
    headline that is false, and it is harder to notice."""
    _need(EX.GPKG_OUT, "the export")
    mf = gpd.read_file(EX.GPKG_OUT, layer="manifest", ignore_geometry=True)
    v = mf.VALUE.astype(str).str.strip().str.lower()
    blank = mf[v.isin(("nan", "none", "", "inf", "-inf"))]
    print(f"\n    [manifest] {len(mf):,} headline rows, {len(blank)} blank")
    assert not len(blank), (
        "the manifest publishes a blank where a number belongs: "
        + ", ".join(f"{r.ITEM!r}" for r in blank.itertuples()))


def test_what_the_stage_removed_is_on_the_manifest_and_not_only_in_a_log(pub):
    """Inheritance row 4: anything a pass can ADD, a later pass must be able to TAKE AWAY,
    AND THE STAGE PUBLISHES HOW MANY IT REMOVED. `withdraw_orphan_crossings()` took 316
    rows off the crossings register on the 12:00 export and the manifest still quoted the
    register as built - 828 - with no row anywhere saying 316 had gone."""
    _need(EX.GPKG_OUT, "the export")
    import fiona
    have = set(fiona.listlayers(EX.GPKG_OUT))
    mf = gpd.read_file(EX.GPKG_OUT, layer="manifest", ignore_geometry=True)
    items = dict(zip(mf.ITEM.astype(str), mf.VALUE.astype(str)))
    if "crossings" in have:
        cx = gpd.read_file(EX.GPKG_OUT, layer="crossings", ignore_geometry=True)
        got = items.get("registered crossings")
        assert got is not None and int(float(got)) == len(cx), (
            f"the manifest says {got} registered crossings and the published layer holds "
            f"{len(cx):,}. The headline and the layer under it must be the same file.")
    n_wd = (len(gpd.read_file(EX.GPKG_OUT, layer="crossings_withdrawn",
                              ignore_geometry=True))
            if "crossings_withdrawn" in have else 0)
    row = [k for k in items if k.startswith("crossings WITHDRAWN")]
    assert row, "the removal ledger has no row for withdrawn crossings"
    print(f"\n    [ledger] {items[row[0]]} withdrawn on the manifest, {n_wd:,} rows on the "
          f"layer")
    assert int(float(items[row[0]])) == n_wd, (
        f"the manifest says {items[row[0]]} crossings were withdrawn and the "
        f"`crossings_withdrawn` layer holds {n_wd:,}")


def test_a_check_that_could_not_run_says_so_rather_than_going_blank(pub):
    """philosophy sec 8. `outfall_check.DEEPEST_M` used a plain .max() over DEPTH_M, so one
    unlevelled chamber blanked the whole component - 219 of 276 rows on the 12:00 export,
    with nothing on the row saying why."""
    _need(EX.GPKG_OUT, "the export")
    import fiona
    if "outfall_check" not in set(fiona.listlayers(EX.GPKG_OUT)):
        pytest.skip("no outfall_check layer on this export")
    oc = gpd.read_file(EX.GPKG_OUT, layer="outfall_check", ignore_geometry=True)
    assert "NO_LEVEL" in oc.columns, (
        "outfall_check does not say how many chambers it could not read a depth for, so a "
        "blank DEEPEST_M cannot be told from a shallow one")
    blank = oc.DEEPEST_M.isna()
    print(f"\n    [outfall check] {int(blank.sum())} of {len(oc)} components have no "
          f"depth at all; {int(oc.NO_LEVEL.sum()):,} chambers unlevelled in total")
    unexplained = int((blank & (oc.NO_LEVEL.fillna(0) == 0)).sum())
    assert unexplained == 0, (
        f"{unexplained} components publish no deepest chamber and give no reason")


def test_the_drawings_name_the_solver_that_actually_levelled_them():
    """`LEVELS_SOURCE` is set only by `build()`. `make_overview.py` calls write_dxf() and
    write_themes() directly, so on the fast path the DXF title block and the KMZ
    description carried the RETIRED stand-in's tag over levels that came from s6."""
    import ast
    src = open(os.path.join(os.path.dirname(EX.__file__), "make_overview.py"),
               encoding="utf-8").read()
    assert "EX.LEVELS_SOURCE" in src, (
        "make_overview.py never sets s8_export.LEVELS_SOURCE, so every drawing it writes "
        "carries the import-time default - the retired stand-in's tag - whoever levelled "
        "the network")
    assert "LEVELS_BY" in src, (
        "the banner must be read off the rows being drawn, not asserted")
    # and it must still compute nothing of its own: no new module-level helper
    fns = {n.name for n in ast.walk(ast.parse(src))
           if isinstance(n, ast.FunctionDef)}
    assert fns <= {"load", "summary", "main", "_n", "line"}, sorted(fns)
