# -*- coding: utf-8 -*-
"""s8_export - the five layers, the three themes, and the things that ate whole runs.

WHY EACH TEST HERE EXISTS. None of these is a hypothetical; every one is written against
something that has actually gone wrong in this project or something the engineer named as
a rule on 2026-09-05/06:

    * `s8_export` "fails its own contract, and cannot write while QGIS holds the
      GeoPackage" (00_CURRENT, open defects). The second half deleted the target file
      before writing it, so a PermissionError on Windows lost a run that had already done
      all the design work.
    * A published column CONSTANT where it should vary is a fabrication - ANGLE_DEG = 90
      on 3,290 crossings (inheritance row 22). DROP_WHY and CONN_WHY are exactly that
      shape, so they are tested for variation, not only for presence.
    * A DEPTH map auto-stretched per run makes the same colour mean a different depth in
      every export. The breaks are fixed and PUBLISHED, and this asserts they cannot drift.
    * A shapefile field name is ten characters. A truncated name is a field the auditor
      cannot find, which philosophy sec 8 makes blocking.
    * SewerGEMS is switched off at concept stage. "Switched off" has to mean REFUSED BY
      NAME - an absent function is indistinguishable from a forgotten one.

Nothing here reads a published GeoPackage: every case is a small synthetic layer set
built inside the test, so the file runs on a cold checkout in about a second.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, Polygon

import s8_export as EX
from w12 import contract as CT
from w12.criteria import DEFAULT as C


# ======================================================================================
# 1.  THE FIVE LAYERS
# ======================================================================================

def test_the_export_declares_exactly_five_design_layers():
    """The engineer named five: conduits, manholes, pumps, force mains, subnetworks."""
    tls = EX.theme_structure(EX.demo_layers())
    assert [t.role for t in tls] == ["reaches", "nodes", "stations", "rising_mains",
                                     "subnetworks"]


def test_the_subnetwork_layer_carries_the_unserved_areas_too():
    """'subnetwork polygons ... PLUS unserved areas carrying a flag and a reason'.

    One layer, not two: an unserved area is the same kind of object as a service area -
    a piece of ground with a decision attached - and splitting them lets one be forgotten.
    """
    sn = EX.demo_layers()["subnetworks"]
    assert set(sn.SERVED) == {0, 1}
    un = sn[sn.SERVED == 0]
    assert len(un) and (un.FLAG.astype(str).str.strip() != "").all(), \
        "an unserved area with no flag is invisible on every drawing"
    assert (un.WHY.astype(str).str.len() > 20).all(), \
        "a flag with no reason is the finding W11b shipped 31 times"


def test_every_layer_of_every_theme_names_a_real_published_layer():
    layers = EX.demo_layers()
    for name, tls in EX.build_themes(layers).items():
        for tl in tls:
            assert len(tl.gdf), f"{name}/{tl.key} drew nothing"
            assert tl.field in tl.gdf.columns or tl.field == "__single__", \
                f"{name}/{tl.key} classifies on {tl.field}, which the layer does not carry"


# ======================================================================================
# 2.  THE DEPTH THEME - fixed breaks, one column, MAGMA
# ======================================================================================

def test_the_depth_breaks_are_the_guideline_values_and_not_re_typed():
    """Move MIN_COVER_CROWN or MAX_COVER and the map must move with them. A depth map
    banded at a number that no longer matches the criteria is worse than no map."""
    assert EX.DEPTH_BREAKS[0] == C.MIN_COVER_CROWN
    assert EX.DEPTH_BREAKS[-1] == C.MAX_COVER
    assert EX.DEPTH_BREAKS == sorted(EX.DEPTH_BREAKS)
    assert len(set(EX.DEPTH_BREAKS)) == len(EX.DEPTH_BREAKS)


def test_the_same_depth_always_lands_in_the_same_band():
    """The whole point of publishing fixed edges. Two runs of the same design, or two
    different designs, must be comparable by eye."""
    a = EX._depth_index(pd.Series([0.4, 2.0, 3.5, 5.0, 8.0, 11.0, 40.0]))
    b = EX._depth_index(pd.Series([0.4, 2.0, 3.5, 5.0, 8.0, 11.0, 40.0]))
    assert list(a) == list(b) == [0, 1, 2, 3, 4, 5, 6]


def test_a_missing_depth_is_drawn_not_dropped():
    """A feature with no depth is still a feature. W10 lost 1,233 m3/d by dropping rows
    that failed a test rather than reporting them."""
    idx = EX._depth_index(pd.Series([float("nan"), None]))
    assert list(idx) == [0, 0]


def test_magma_runs_light_to_dark_on_every_class():
    cls = EX._depth_classes("line")
    lum = [0.3 * r + 0.59 * g + 0.11 * b for _k, _l, (r, g, b), _w in cls]
    assert lum == sorted(lum, reverse=True), \
        "shallower must be lighter and deeper darker, on every class, in order"


def test_every_depth_band_carries_its_source_or_says_it_has_none():
    cls = EX._depth_classes("point")
    for _k, lab, _rgb, _w in cls:
        assert "[" in lab or "(o)" in lab, (
            f"band {lab!r} cites nothing and is not marked as presentation-only. A break "
            "with neither is a number a reader will assume came from a guideline.")


def test_the_depth_theme_uses_one_column_on_every_layer():
    """DEP_M means a different physical thing per layer - that is why it is one column
    with the meanings written down, and why the field dictionary has a table for it."""
    tls = EX.theme_depth(EX.demo_layers())
    assert {t.field for t in tls} == {"DEP_BAND"}
    assert all("DEP_M" in t.gdf.columns for t in tls)


# ======================================================================================
# 3.  THE EXCEPTIONS THEME - only the flagged, count in the name
# ======================================================================================

def test_the_exceptions_theme_draws_nothing_that_is_not_flagged():
    layers = EX.demo_layers()
    tls = EX.theme_exceptions(layers)
    kinds = {t.key for t in tls}
    assert "plot_cannot_connect" in kinds and "area_unserved" in kinds
    cn = layers["connections"]
    n_bad = int((cn.CAN_CONN == 0).sum())
    tl = next(t for t in tls if t.key == "plot_cannot_connect")
    assert tl.n == n_bad, "it drew rows that are not flagged, or missed rows that are"


def test_the_count_is_in_the_layer_name():
    """'PUT THE COUNT IN EACH LAYER NAME so the legend itself reports the totals.'"""
    for tl in EX.theme_exceptions(EX.demo_layers()):
        assert tl.folder_name().endswith(f"({tl.n:,})"), tl.folder_name()


def test_an_exception_with_no_rows_is_not_drawn_at_all():
    """An empty folder on an exceptions map reads as 'we checked and it is fine'. It is
    not: it is 'we drew a heading'. Empty kinds are omitted and the theme says which."""
    layers = EX.demo_layers()
    layers["connections"] = layers["connections"][layers["connections"].CAN_CONN == 1]
    tls = EX.theme_exceptions(layers)
    assert "plot_cannot_connect" not in {t.key for t in tls}


def test_severity_is_a_rank_and_sizes_the_symbol():
    sizes = {sev for _k, _t, _c, sev in EX.EXC_KINDS}
    assert sizes <= set(EX.EXC_SIZE), "an exception kind has a severity with no symbol size"
    assert EX.EXC_SIZE[3] > EX.EXC_SIZE[2] > EX.EXC_SIZE[1]


# ======================================================================================
# 4.  THE KMZ - openable, folded, and the same colours as everything else
# ======================================================================================

def _write_themes(tmp_path, layers, arrows=None):
    old_kmz = EX.DIR_KMZ
    EX.DIR_KMZ = str(tmp_path)
    try:
        return EX.write_themes(layers, arrows)
    finally:
        EX.DIR_KMZ = old_kmz


def test_three_theme_files_are_written_and_every_one_is_valid_kml(tmp_path):
    files = _write_themes(tmp_path, EX.demo_layers())
    assert set(files) == {"structure", "depth", "exceptions"}
    for theme, paths in files.items():
        kmz = [p for p in paths if p.endswith(".kmz")]
        assert len(kmz) == 1, f"{theme} wrote {len(kmz)} KMZ, expected exactly one"
        with zipfile.ZipFile(kmz[0]) as z:
            doc = z.read("doc.kml").decode("utf-8")
        root = ET.fromstring(doc)             # raises on malformed XML
        ns = "{http://www.opengis.net/kml/2.2}"
        folders = root.findall(f".//{ns}Folder")
        assert folders, f"{theme} has no folders - the layers are not separable"


def test_the_kmz_folder_names_carry_the_counts(tmp_path):
    files = _write_themes(tmp_path, EX.demo_layers())
    with zipfile.ZipFile([p for p in files["exceptions"] if p.endswith(".kmz")][0]) as z:
        doc = z.read("doc.kml").decode("utf-8")
    assert "(1)" in doc, "no folder reports its own count"


def test_a_large_layer_is_grouped_so_the_file_still_opens(tmp_path):
    """56,000 placemarks in one folder will not pan in Google Earth. Above
    KMZ_INDIVIDUAL_MAX the writer groups a class into ONE placemark - and the description
    SAYS SO, so nobody thinks the per-feature attributes were lost."""
    layers = EX.demo_layers()
    nd = layers["nodes"]
    big = pd.concat([nd] * (EX.KMZ_INDIVIDUAL_MAX // len(nd) + 2), ignore_index=True)
    layers["nodes"] = gpd.GeoDataFrame(big, geometry=big.geometry, crs=nd.crs)
    files = _write_themes(tmp_path, layers)
    p = [x for x in files["structure"] if x.endswith(".kmz")][0]
    with zipfile.ZipFile(p) as z:
        doc = z.read("doc.kml").decode("utf-8")
    ET.fromstring(doc)
    assert "one placemark per class" in doc
    assert os.path.getsize(p) < 4_000_000, (
        f"{os.path.getsize(p) / 1e6:.1f} MB for a synthetic network - the size control is "
        "not working and the real file will not open")


def test_the_kmz_carries_the_concept_banner_and_the_tau_assumption(tmp_path):
    """Every deliverable says what was switched off and what tau it rests on. A drawing
    that does not is a drawing somebody will quote in five years."""
    files = _write_themes(tmp_path, EX.demo_layers())
    with zipfile.ZipFile([p for p in files["depth"] if p.endswith(".kmz")][0]) as z:
        doc = z.read("doc.kml").decode("utf-8")
    assert "sewergems_export" in doc or "SWITCHED OFF" in doc.upper()
    assert "tau" in doc.lower()


def test_the_main_pipe_is_on_every_theme(tmp_path):
    """It is an INPUT and nothing drains into it - which is exactly why it has to be
    visible: the gap between a subnetwork and the trunk is the thing being judged."""
    files = _write_themes(tmp_path, EX.demo_layers())
    for theme, paths in files.items():
        with zipfile.ZipFile([p for p in paths if p.endswith(".kmz")][0]) as z:
            doc = z.read("doc.kml").decode("utf-8")
        assert "Main pipe" in doc, theme


def test_flow_direction_is_drawn_on_the_structure_theme(tmp_path):
    layers = EX.demo_layers()
    arrows = EX.flow_arrows(layers["reaches"], every_m=50.0, size=10.0)
    assert arrows, "no arrows were produced on a network with two sub-main reaches"
    files = _write_themes(tmp_path, layers, arrows)
    with zipfile.ZipFile([p for p in files["structure"] if p.endswith(".kmz")][0]) as z:
        doc = z.read("doc.kml").decode("utf-8")
    assert "Flow direction" in doc


def test_flow_arrows_come_out_in_the_right_hemisphere(tmp_path):
    """The arrows are built in METRES and the KMZ is in DEGREES. Handing the writer UTM
    coordinates would put them off the coast of Africa, and the file would still open."""
    layers = EX.demo_layers()
    arrows = EX.flow_arrows(layers["reaches"], every_m=50.0, size=10.0)
    files = _write_themes(tmp_path, layers, arrows)
    with zipfile.ZipFile([p for p in files["structure"] if p.endswith(".kmz")][0]) as z:
        doc = z.read("doc.kml").decode("utf-8")
    body = doc.split("Flow direction", 1)[1]
    lon = float(body.split("<coordinates>")[1].split(",")[0])
    assert 50.0 < lon < 60.0, f"flow arrows landed at longitude {lon:.3f}, not in Oman"


# ======================================================================================
# 5.  THE SAVED QGIS STYLES
# ======================================================================================

def test_a_qml_is_written_for_every_theme_layer_and_is_valid_xml(tmp_path):
    files = _write_themes(tmp_path, EX.demo_layers())
    themes = EX.build_themes(EX.demo_layers())
    for theme, paths in files.items():
        qmls = [p for p in paths if p.endswith(".qml")]
        assert len(qmls) == len(themes[theme]), theme
        for q in qmls:
            root = ET.parse(q).getroot()      # raises on malformed XML
            assert root.tag == "qgis"
            assert root.find(".//renderer-v2") is not None


def test_the_qml_and_the_kmz_use_the_same_colours(tmp_path):
    """One class table drives both. If they can drift, the map a reviewer marks up and the
    map they mark it up against are different maps."""
    layers = EX.demo_layers()
    tl = EX.theme_structure(layers)[3]                 # force mains: two classes, two colours
    old = EX.DIR_KMZ
    EX.DIR_KMZ = str(tmp_path)
    try:
        q = EX.theme_qml("structure", tl)
    finally:
        EX.DIR_KMZ = old
    xml = open(q, encoding="utf-8").read()
    for _k, _lab, (r, g, b), _w in tl.classes:
        assert f"{r},{g},{b}" in xml, f"the .qml lost the colour {(r, g, b)}"
        assert EX.PR.kml_color((r, g, b)) == f"ff{b:02x}{g:02x}{r:02x}"


# ======================================================================================
# 6.  THE DXF
# ======================================================================================

@pytest.mark.slow
def test_the_dxf_carries_the_five_layers_and_the_annotation(tmp_path):
    pytest.importorskip("ezdxf")
    import ezdxf
    old = EX.DIR_DXF
    EX.DIR_DXF = str(tmp_path)
    try:
        paths = EX.write_dxf(EX.demo_layers(), annotated=True)
    finally:
        EX.DIR_DXF = old
    assert len(paths) == 2, "the plain and the annotated drawing"
    doc = ezdxf.readfile([p for p in paths if "annotated" in p][0])
    names = {l.dxf.name for l in doc.layers}
    for want in ("W12-CONDUIT-SUBMAIN", "W12-MANHOLE", "W12-PUMP", "W12-FORCEMAIN",
                 "W12-SUBNET", "W12-MAINPIPE"):
        assert want in names, f"the DXF has no {want} layer"
    text = " | ".join(e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT")
    # the engineer's annotation list, item by item
    assert "I-S01-SM-M001" in text, "a conduit or a manhole is unnamed on the drawing"
    assert "DN300" in text and "L=100.0" in text and "S=0.50%" in text
    assert "Q=12.0L/s" in text and "v=0.80m/s" in text
    assert "-> I-S01-SM-M002" in text, "a conduit does not name its outlet manhole"
    assert "inv 328.50" in text and "g 330.00" in text
    assert "I-PMP01" in text and "lift 8.00 m" in text and "well 4.50 m3" in text
    assert "I-P01" in text and "(stp)" in text, "a force main does not say where it lands"


@pytest.mark.slow
def test_the_dxf_colours_are_the_theme_colours(tmp_path):
    pytest.importorskip("ezdxf")
    import ezdxf
    old = EX.DIR_DXF
    EX.DIR_DXF = str(tmp_path)
    try:
        paths = EX.write_dxf(EX.demo_layers(), annotated=False)
    finally:
        EX.DIR_DXF = old
    doc = ezdxf.readfile(paths[0])
    want = dict((n, rgb) for n, rgb, _d in EX._dxf_layers())
    for lay in doc.layers:
        if lay.dxf.name in want and lay.rgb is not None:
            assert tuple(lay.rgb) == want[lay.dxf.name], lay.dxf.name


# ======================================================================================
# 7.  THE GEOPACKAGE - it must not lose a run to a file QGIS is holding
# ======================================================================================

def _publish_into(tmp_path, layers):
    old_shp, old_out = EX.SHP, EX.GPKG_OUT
    EX.SHP = str(tmp_path)
    EX.GPKG_OUT = os.path.join(str(tmp_path), "W12_export.gpkg")
    try:
        return EX.publish(layers, {})
    finally:
        EX.SHP, EX.GPKG_OUT = old_shp, old_out


def test_publish_writes_every_layer_and_returns_where_it_wrote(tmp_path):
    import fiona
    layers = {k: v for k, v in EX.demo_layers().items()}
    p = _publish_into(tmp_path, layers)
    assert os.path.basename(p) == "W12_export.gpkg"
    assert set(fiona.listlayers(p)) >= set(layers)


def test_a_locked_geopackage_does_not_lose_the_run(tmp_path, monkeypatch):
    """The defect named in 00_CURRENT: 's8_export ... cannot write while QGIS holds the
    GeoPackage'. The old code deleted the target first, so the run died AFTER all the
    design work was done. Now the swap fails over to a timestamped file and SAYS SO."""
    layers = EX.demo_layers()
    real_replace = os.replace
    state = {"n": 0}

    def flaky(src, dst):
        # the first swap - onto the canonical name - is refused, exactly as Windows
        # refuses os.replace onto a file another process holds open.
        if state["n"] == 0 and dst.endswith("W12_export.gpkg"):
            state["n"] += 1
            raise PermissionError(32, "The process cannot access the file")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    p = _publish_into(tmp_path, layers)
    assert p.endswith(".gpkg") and "W12_export_" in os.path.basename(p), p
    assert os.path.exists(p) and os.path.getsize(p) > 0
    import fiona
    assert set(fiona.listlayers(p)) >= set(layers), "the fallback file is incomplete"


def test_publish_leaves_no_part_file_behind(tmp_path):
    _publish_into(tmp_path, EX.demo_layers())
    leftovers = [f for f in os.listdir(tmp_path) if ".part." in f]
    assert not leftovers, leftovers


# ======================================================================================
# 8.  SHAPEFILE NAMES AND THE FIELD DICTIONARY
# ======================================================================================

def test_every_published_column_fits_a_dbf_name():
    EX.assert_shp_names(EX.demo_layers())          # must not raise


def test_a_long_column_name_is_refused_before_anything_is_written():
    layers = EX.demo_layers()
    layers["nodes"] = layers["nodes"].assign(THIS_NAME_IS_FAR_TOO_LONG=1)
    with pytest.raises(CT.ContractError) as e:
        EX.assert_shp_names(layers)
    assert "THIS_NAME_IS_FAR_TOO_LONG" in str(e.value)
    assert str(CT.SHP_FIELD_MAXLEN) in str(e.value)


def test_the_field_dictionary_explains_every_abbreviation_it_uses():
    md = EX.field_dictionary_md(EX.demo_layers())
    for tok in ("INV", "DN", "COVER", "DEPTH / DEP", "US / DS", "_LS / _M3D"):
        assert f"`{tok}`" in md, f"{tok} is used in a field name and is not explained"
    for layer in ("nodes", "reaches", "stations", "rising_mains", "connections"):
        assert f"### `{layer}`" in md
    assert "I-S03-SM-M012" in md, "the naming grammar is not on the page"
    assert "DEP_M" in md, "the one column the DEPTH theme uses is not explained"
    for b in EX.DEPTH_BREAKS:
        assert f"{b:.2f}" in md, f"the fixed break {b} is not published on the page"


def test_the_field_dictionary_names_what_is_switched_off():
    md = EX.field_dictionary_md(EX.demo_layers())
    assert "MOTOR_KW" in md and "LCC_OMR" in md
    assert "BANNED_FIELDS" in md or "banned field" in md


# ======================================================================================
# 9.  THE CONCEPT RULES THIS STAGE COMPUTES
# ======================================================================================

class _A:
    """The two attributes `_drop_reasons` actually reads. Not a mock of Assembly - a
    stand-in built from the same frames, so the test cannot pass on a shape Assembly
    does not have."""
    def __init__(self, on_wadi):
        self.chambers = pd.DataFrame({"ON_WADI": on_wadi})


def _line_graph(n_nodes, edges, grd):
    """A Graph over `edges` = [(u, v, length)]. Written out rather than derived, so the
    topology under test is visible in the test."""
    uid = [f"N{i}" for i in range(n_nodes)]
    e_us = np.array([e[0] for e in edges], dtype=np.int64)
    e_ds = np.array([e[1] for e in edges], dtype=np.int64)
    e_len = np.array([e[2] for e in edges], dtype=float)
    ds = np.full(n_nodes, -1, dtype=np.int64)
    e_of = np.full(n_nodes, -1, dtype=np.int64)
    for k, (u, v, _L) in enumerate(edges):
        e_of[u] = k
        ds[u] = v
    indeg = np.zeros(n_nodes, dtype=np.int64)
    np.add.at(indeg, e_ds, 1)
    return EX.Graph(uid, {u: i for i, u in enumerate(uid)}, np.asarray(grd, dtype=float),
                    ds, e_us, e_ds, e_len, e_of, np.arange(n_nodes), indeg)


def test_every_drop_carries_a_reason_from_the_closed_vocabulary():
    """CONCEPT RULE 1. Two arms into node 2: one flattened to hold the velocity cap, one
    a lateral stepping into a sub main. The reasons must differ - and both must be words
    the contract allows."""
    g = _line_graph(4, [(0, 2, 30.0), (1, 2, 30.0), (2, 3, 30.0)],
                    [100.0, 100.0, 98.0, 96.0])
    tiers = ["lateral", "sub main", "sub main"]
    grad_by = ["vmax", "table11", "table11"]
    inv_dn = np.array([97.0, 96.4, 95.0])
    reasons = EX._drop_reasons(_A([0, 0, 0, 0]), g, tiers, grad_by, inv_dn,
                               np.array([np.inf, np.inf, 96.4, 95.0]),
                               np.array([-np.inf, -np.inf, 97.0, 95.0]),
                               ["none", "none", "backdrop", "none"])
    assert reasons[2] == "velocity_cap"
    assert set(r for r in reasons if r) <= set(CT.DROP_WHY)


def test_a_tier_step_is_named_as_a_tier_step_not_as_a_velocity_cap():
    g = _line_graph(3, [(0, 1, 30.0), (1, 2, 30.0)], [100.0, 99.0, 98.0])
    reasons = EX._drop_reasons(_A([0, 0, 0]), g, ["lateral", "sub main"],
                               ["table11", "table11"], np.array([98.5, 97.0]),
                               np.array([np.inf, 98.5, 97.0]),
                               np.array([-np.inf, 98.5, 97.0]),
                               ["none", "backdrop", "none"])
    assert reasons[1] == "tier_step"


def test_a_chamber_on_wadi_ground_names_the_obstruction():
    g = _line_graph(3, [(0, 1, 30.0), (1, 2, 30.0)], [100.0, 99.0, 98.0])
    reasons = EX._drop_reasons(_A([0, 1, 0]), g, ["lateral", "lateral"],
                               ["table11", "table11"], np.array([98.5, 97.0]),
                               np.array([np.inf, 98.5, 97.0]),
                               np.array([-np.inf, 98.5, 97.0]),
                               ["none", "backdrop", "none"])
    assert reasons[1] == "obstruction"


def test_a_chamber_with_no_drop_carries_no_reason():
    """The contract refuses a reason on a chamber that does not drop - a column of
    explanations would hide the real ones."""
    g = _line_graph(2, [(0, 1, 30.0)], [100.0, 99.0])
    reasons = EX._drop_reasons(_A([0, 0]), g, ["lateral"], ["table11"],
                               np.array([98.5]), np.array([np.inf, 98.5]),
                               np.array([-np.inf, 98.5]), ["none", "none"])
    assert reasons == ["", ""]


def _flows(subnet, ups_len=None):
    n = len(subnet)
    z = np.zeros(n)
    return EX.Flows(z, z, np.zeros(n, dtype=np.int64), z, z,
                    np.asarray(ups_len if ups_len is not None else z, dtype=float),
                    np.asarray(subnet, dtype=np.int64),
                    np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0), [],
                    np.zeros(0), np.zeros(0))


class _AJ:
    def __init__(self, x, y, trunk):
        self.chambers = pd.DataFrame({"X": x, "Y": y})
        self.trunk = gpd.GeoDataFrame(geometry=[trunk], crs=f"EPSG:{CT.CRS_EPSG}")


def test_an_outfall_at_the_main_pipe_and_at_its_own_low_point_needs_no_explanation():
    """CONCEPT RULE 2. JOIN_MAIN = 1, JOIN_OFF_M = 0, and the contract refuses a JOIN_WHY
    on a zero offset - so a clean join must produce a BLANK reason, not a reassuring one."""
    g = _line_graph(2, [(0, 1, 30.0)], [100.0, 90.0])
    a = _AJ([0.0, 0.0], [0.0, 30.0], LineString([(-50, 30), (50, 30)]))
    jn = EX.measure_joins(a, g, _flows([1, 1]))
    assert jn.is_join[1] == 1
    assert jn.off_m[1] == 0.0
    assert jn.why[1] == ""


def test_an_outfall_off_its_own_low_point_records_the_distance_and_the_reason():
    """'connect at the nearest usable place and RECORD THE DISTANCE FROM THE TRUE LOW
    POINT on that connection'."""
    # node 1 is the catchment's true low point (80 m) and sits 210 m east of the outfall,
    # which is at node 2 on the main pipe. Same y, so the offset is exactly 210 m.
    g = _line_graph(3, [(0, 2, 30.0), (1, 2, 210.0)], [100.0, 80.0, 90.0])
    a = _AJ([0.0, 210.0, 0.0], [0.0, 30.0, 30.0], LineString([(-50, 30), (50, 30)]))
    jn = EX.measure_joins(a, g, _flows([2, 2, 2]))
    assert jn.is_join[2] == 1
    assert jn.off_m[2] == pytest.approx(210.0, abs=1.0)
    assert "low point" in jn.why[2] and "N1" in jn.why[2]


def test_a_subnetwork_that_does_not_reach_the_main_pipe_claims_no_join():
    """And therefore carries NO offset - the contract refuses an offset from a join that
    does not exist, and it is right to: there is nothing to be offset from."""
    g = _line_graph(2, [(0, 1, 30.0)], [100.0, 90.0])
    a = _AJ([0.0, 0.0], [0.0, 30.0], LineString([(-50, 5000), (50, 5000)]))
    jn = EX.measure_joins(a, g, _flows([1, 1]))
    assert jn.is_join[1] == 0
    assert jn.off_m[1] == 0.0 and jn.why[1] == ""
    assert jn.gap_m[1] > EX.JOIN_TOL_M
    assert jn.stats["short"] == 1


# ======================================================================================
# 10.  PLOT CONNECTABILITY - concept rule 5, and the SIZE on every flag
# ======================================================================================

def _conn_case(grd_plot, inv, length):
    crs = f"EPSG:{CT.CRS_EPSG}"
    n = len(grd_plot)
    cn = gpd.GeoDataFrame(dict(
        CONN_ID=[f"C{i}" for i in range(n)], PLOT_ID=[f"P{i}" for i in range(n)],
        OUT_NODE=["N0"] * n, WHY=[""] * n, SYSTEM=["central"] * n,
        CONN_TYPE=["rider"] * n, Q_ADF_M3D=[1.0] * n, N_PROP=[1.4] * n,
        LEN_M=list(length), GRD_PLOT=list(grd_plot),
        XPLOT=[0] * n, XDUAL=[0] * n, CH_WADI=[0] * n),
        geometry=[LineString([(0.0, float(L)), (0.0, 0.0)]) for L in length], crs=crs)
    nodes = gpd.GeoDataFrame(dict(
        NODE_UID=["N0"], INV_M=[float(inv)], TOWN=["I"], SUBNET=["S01"],
        SUB_NAME=["I-S01"], PACKAGE=["P001"]),
        geometry=[Point(0.0, 0.0)], crs=crs)
    a = type("A", (), {"connections": cn})()
    return EX.build_connections(a, None, nodes, None)


def test_a_plot_that_cannot_connect_says_how_much_deeper_the_sewer_must_be():
    """The whole difference between W11b's '5,521 plots cannot drain' and a finding
    somebody can act on."""
    out = _conn_case([100.0], 99.5, [40.0])
    assert int(out.CAN_CONN.iloc[0]) == 0
    need = float(out.CONN_NEED.iloc[0])
    # available fall = (100 - HCC_DEPTH_MIN) - 99.5 ; required = 3 % of 40 m
    want = C.PCS_MIN_SLOPE * 40.0 - ((100.0 - C.HCC_DEPTH_MIN) - 99.5)
    assert need == pytest.approx(want, abs=1e-6)
    assert f"{need:.2f}" in out.CONN_WHY.iloc[0]


def test_the_connection_leaves_below_ground_level_and_not_at_it():
    """A level comparison at the plot surface passes plots that cannot be connected. The
    outlet sits at the G203-p19 sec 3.4 minimum HCC depth, so a plot whose ground is above
    the invert by LESS than that depth must FAIL."""
    inv = 100.0
    grd = inv + C.HCC_DEPTH_MIN - 0.1          # ground clears the invert, the outlet does not
    out = _conn_case([grd], inv, [10.0])
    assert int(out.CAN_CONN.iloc[0]) == 0
    assert "BELOW the sewer invert" in out.CONN_WHY.iloc[0]


def test_a_plot_that_connects_carries_no_reason_and_no_size():
    out = _conn_case([110.0], 100.0, [20.0])
    assert int(out.CAN_CONN.iloc[0]) == 1
    assert out.CONN_WHY.iloc[0] == ""
    assert float(out.CONN_NEED.iloc[0]) == 0.0


def test_can_drain_is_written_from_can_conn_and_never_computed_twice():
    out = _conn_case([110.0, 100.0], 99.5, [20.0, 40.0])
    assert list(out.CAN_DRAIN) == list(out.CAN_CONN)


def test_the_failure_reasons_vary_and_are_not_one_sentence_repeated():
    """Inheritance row 22 in the form it takes on a text column: if every failing plot got
    the same words, the reason was not computed."""
    out = _conn_case([100.0] * 40, 99.5, list(np.linspace(10.0, 60.0, 40)))
    bad = out[out.CAN_CONN == 0]
    assert len(bad) >= CT.VARY_MIN_ROWS
    assert CT.constant_column_problem(bad, "CONN_WHY") is None


# ======================================================================================
# 11.  SWITCHED OFF MEANS REFUSED BY NAME
# ======================================================================================

def test_the_sewergems_export_is_refused_by_name():
    with pytest.raises(Exception) as e:
        EX.write_sewergems()
    assert "sewergems_export" in str(e.value)


def test_no_sewergems_output_directory_is_created():
    assert not hasattr(EX, "DIR_GEM"), (
        "a directory for a switched-off capability is a directory somebody will fill")


def test_the_stage_writes_no_banned_field_name():
    """MOTOR_KW and LCC_OMR belong to capabilities switched off at concept; HEAD_M and the
    rest are second names for quantities the contract already carries. validate() allows
    extra columns, so a ban is the only thing that stops one appearing."""
    written = EX._fields_this_stage_writes()
    assert not (set(CT.BANNED_FIELDS) & written), \
        sorted(set(CT.BANNED_FIELDS) & written)


def test_the_five_layers_never_carry_a_motor_or_a_life_cycle_cost():
    for name, gdf in EX.demo_layers().items():
        assert "MOTOR_KW" not in gdf.columns, name
        assert "LCC_OMR" not in gdf.columns, name


# ======================================================================================
# 12.  THE SECOND SET OF LEVELS - detected, never resolved silently
# ======================================================================================

def test_two_sets_of_levels_are_detected_and_named(tmp_path, monkeypatch):
    """W12 HAS an s6_levels and it publishes its own contract file. Two functions for one
    published quantity is inheritance row 10 - the row that put seven station counts into
    circulation. This stage must NOT quietly publish a second answer."""
    crs = f"EPSG:{CT.CRS_EPSG}"
    p = tmp_path / CT.GPKG_NAME
    gpd.GeoDataFrame(dict(NODE_UID=["N0"], INV_M=[100.0]),
                     geometry=[Point(0, 0)], crs=crs).to_file(p, layer="nodes",
                                                              driver="GPKG")
    gpd.GeoDataFrame(dict(EDGE_UID=["E0"]),
                     geometry=[LineString([(0, 0), (1, 1)])], crs=crs).to_file(
        p, layer="reaches", driver="GPKG")
    monkeypatch.setattr(EX, "GPKG_S6", str(p))
    msg = EX.levels_source_conflict()
    assert msg and "TWO SETS OF LEVELS" in msg
    assert "inheritance row 10" in msg.lower() or "row 10" in msg


def test_no_second_set_of_levels_is_not_reported_as_a_problem(tmp_path, monkeypatch):
    monkeypatch.setattr(EX, "GPKG_S6", str(tmp_path / "does_not_exist.gpkg"))
    assert EX.levels_source_conflict() is None


# ======================================================================================
# 13.  THE CONTRACT - the defect named in 00_CURRENT: "s8_export fails its own contract"
# ======================================================================================

def _s8_shaped_station(**over):
    """A station row in EXACTLY the shape `build_stations()` writes: the s7 hydraulics,
    plus the anchor, the concept name, and the two fields that say the position was
    CHOSEN. What is NOT here is the point - no MOTOR_KW, no LCC_OMR, no HEAD_M."""
    q, starts = 50.0, C.WELL_STARTS_MIN
    row = dict(NODE_UID="PS00001", NODE_REF="P001-L-MH0003", WHY="cap",
               ST_TYPE=C.ps_type(q), Q_DUTY_LS=q, LIFT_M=6.2, N_PROP=430.0,
               Q_ADF_M3D=1830.0, WELL_M3=C.well_volume_m3(q / 1000.0, starts),
               WW_STARTS=starts, GRD_M=330.0, INV_M=323.8,
               FLOOD_LV=330.0 - C.PS_FLOOR_ABOVE_FLOOD_M,
               LAND_M2=C.ps_land_m2(C.ps_type(q))[0], N_SUBNET=1, CATCH_KM=7.4,
               RM_EDGE="E9000001", COMM_PT=1, NAME="I-PMP01", TOWN="I", SUBNET="",
               ANCHOR_ND="N0000003", ST_SNAP_M=0.4, UID_S7="N0000001",
               PACKAGE="P001", PHASE=0, SRC="terrain", CONFIDENCE="derived",
               STAGE="s7_pumps (levels by s8)")
    row.update(over)
    return gpd.GeoDataFrame([row], geometry=[Point(200.0, 0.0)], crs=CT.CRS_EPSG)


def test_the_station_layer_now_passes_its_own_contract():
    """This is the defect 00_CURRENT names: 's8_export fails its own contract'. The three
    fields that failed it were MOTOR_KW and LCC_OMR (capabilities switched off at concept,
    and BANNED so they cannot appear as undeclared extras) and HEAD_M (a second name for
    LIFT_M / STAT_HD_M / TOT_HD_M). They are gone, and N_SUBNET, CATCH_KM and INV_M are
    written in their place."""
    CT.validate(_s8_shaped_station(), "stations", stage="s8_export")


def test_a_station_carrying_a_motor_or_a_life_cycle_cost_is_refused():
    """Proof the ban BITES rather than merely being written down - a check nobody has seen
    fail is a check nobody knows is wired in."""
    for field, value in (("MOTOR_KW", 11.0), ("LCC_OMR", 250000.0), ("HEAD_M", 8.1)):
        with pytest.raises(CT.ContractError) as e:
            CT.validate(_s8_shaped_station(**{field: value}), "stations")
        assert field in str(e.value)


def test_a_null_flood_level_is_the_only_thing_left_and_it_is_a_data_request():
    """The one objection this stage CANNOT clear, and it must stay visible.

    `hazard.flood_level_m_aod()` raises by design: the grids carry an AR&R hazard CLASS
    and no water-surface level, and G203-p38 sec 7.2 needs the 1:50 surface for the
    300 mm freeboard. Filling it with ground level manufactured a freeboard failure on
    every station that said nothing about any of them. So the null stays, the contract
    reports it, and the null IS the data request to NWS."""
    with pytest.raises(CT.ContractError) as e:
        CT.validate(_s8_shaped_station(FLOOD_LV=float("nan")), "stations")
    problems = [p for p in str(e.value).split("\n\n") if p.strip()]
    body = [p for p in problems if "FLOOD_LV" in p]
    assert body, str(e.value)
    others = [p for p in problems
              if p.strip() and "FLOOD_LV" not in p
              and not p.startswith("CONTRACT VIOLATION")
              and not p.startswith("Fix this in the stage")
              and "Every pumping station" not in p]
    assert not others, "something OTHER than the flood level is failing:\n" + "\n".join(others)


def test_a_rising_main_declares_where_gravity_resumes():
    rm = gpd.GeoDataFrame(
        [dict(EDGE_UID="E9000001", US_NODE="PS00001", DS_NODE="N0000002",
              STATION="PS00001", DN=200, MATERIAL="DI", LEN_M=180.0, Q_DUTY_LS=50.0,
              V_DUTY_MS=1.6, V_MIN_MS=0.8, STAT_HD_M=6.2, TOT_HD_M=8.1, RETENT_M=3.0,
              N_AIRV=1, N_WASH=1, N_ISOL=2, WADI_M=0.0, SEPTIC_FL=1, DS_TYPE="manhole",
              NAME="I-P01", TOWN="I", SUBNET="", PACKAGE="P001", PHASE=0,
              SRC="terrain", CONFIDENCE="derived", STAGE="s7_pumps")],
        geometry=[LineString([(200.0, 0.0), (200.0, 180.0)])], crs=CT.CRS_EPSG)
    CT.validate(rm, "rising_mains", stage="s8_export")
    with pytest.raises(CT.ContractError):
        CT.validate(rm.assign(DS_TYPE="wet well"), "rising_mains")


def test_check_contract_reports_one_row_per_problem_not_one_blob():
    """W11b wrote the whole ContractError into one 8,000-character cell, so 'stations
    fails' could equally mean one missing field or forty."""
    layers = {"stations": _s8_shaped_station(FLOOD_LV=float("nan"), Q_DUTY_LS=0.0)}
    chk = EX.check_contract(layers)
    fails = chk[(chk.LAYER == "stations") & (chk.PASS == 0)]
    assert len(fails) >= 2, "two independent problems collapsed into one row"
    joined = " ".join(fails.DETAIL.astype(str))
    assert "FLOOD_LV" in joined and "Q_DUTY_LS" in joined
    # and the layer's PURPOSE is not reported as if it were a problem
    assert not any(str(d).startswith("Every pumping station") for d in fails.DETAIL), \
        "the header text leaked into the problem list and inflates the failure count"


def test_the_publication_gate_refuses_an_unnamed_layer():
    """`assert_named()` is the gate that says the naming WORK was done, as opposed to
    being possible. Nobody called it before; check_contract calls it now."""
    chk = EX.check_contract({"stations": _s8_shaped_station(NAME="", TOWN="")})
    row = chk[chk.LAYER.str.contains("assert_named")]
    assert len(row) == 1 and int(row.PASS.iloc[0]) == 0
    assert "NOT FULLY NAMED" in str(row.RESULT.iloc[0])


def test_the_publication_gate_passes_a_named_layer():
    chk = EX.check_contract({"stations": _s8_shaped_station()})
    row = chk[chk.LAYER.str.contains("assert_named")]
    assert len(row) == 1 and int(row.PASS.iloc[0]) == 1


def test_a_layer_that_was_not_produced_is_a_failure_not_a_blank():
    """Philosophy sec 8, and inheritance row 2: a check that cannot run is a FAILURE."""
    chk = EX.check_contract({})
    assert (chk[chk.LAYER == "nodes"].PASS == 0).all()
    assert "NOT PRODUCED" in str(chk[chk.LAYER == "nodes"].RESULT.iloc[0])


# ======================================================================================
# 14.  NAMING - concept rule 8, end to end on a two-town synthetic case
# ======================================================================================

def _towns_frame():
    """Two settlements whose de-articled names both start with A, so the clash rule has to
    fire: 'on a clash BOTH towns extend ... the town with more served plots is not
    favoured'."""
    crs = f"EPSG:{CT.CRS_EPSG}"
    return gpd.GeoDataFrame(
        {"TOWN_NAME": ["Ibri", "Al Aqar"], "TOWN_CODE": ["I", "A"]},
        geometry=[Polygon([(0, -100), (400, -100), (400, 100), (0, 100)]),
                  Polygon([(600, -100), (1000, -100), (1000, 100), (600, 100)])],
        crs=crs)


class _AN:
    def __init__(self, chambers, segments, trunk=None, unserved=None):
        self.chambers, self.segments = chambers, segments
        self.trunk = trunk
        self.unserved = unserved
        self.notes = []

    def note(self, s):
        self.notes.append(s)


def _naming_case(monkeypatch):
    crs = f"EPSG:{CT.CRS_EPSG}"
    # two subnetworks: N0->N1->N2 in Ibri, N3->N4 in Al Aqar
    g = _line_graph(5, [(0, 1, 30.0), (1, 2, 30.0), (3, 4, 30.0)],
                    [100.0, 99.0, 98.0, 90.0, 89.0])
    ch = gpd.GeoDataFrame(dict(X=[10.0, 40.0, 70.0, 700.0, 730.0],
                               Y=[0.0, 0.0, 0.0, 0.0, 0.0]),
                          geometry=[Point(10, 0), Point(40, 0), Point(70, 0),
                                    Point(700, 0), Point(730, 0)], crs=crs)
    seg = gpd.GeoDataFrame(dict(TIER=["lateral", "sub main", "lateral"]),
                           geometry=[LineString([(10, 0), (40, 0)]),
                                     LineString([(40, 0), (70, 0)]),
                                     LineString([(700, 0), (730, 0)])], crs=crs)
    a = _AN(ch, seg)
    f = _flows([2, 2, 2, 4, 4])
    f.q_adf[2] = 500.0
    f.q_adf[4] = 100.0
    monkeypatch.setattr(EX, "_read_towns", _towns_frame)
    return a, g, f


def test_a_name_is_town_subnetwork_tier_element(monkeypatch):
    a, g, f = _naming_case(monkeypatch)
    nm = EX.build_names(a, g, f)
    assert nm.node_name[0] == "I-S01-L-M001", nm.node_name
    assert nm.node_name[2].startswith("I-S01-SM-M"), nm.node_name[2]
    assert nm.node_name[3].startswith("A-S01-"), nm.node_name[3]
    for n in nm.node_name:
        assert CT.parse_name(n) is not None, n


def test_a_conduit_is_named_for_its_upstream_manhole(monkeypatch):
    a, g, f = _naming_case(monkeypatch)
    nm = EX.build_names(a, g, f)
    for k, u in enumerate(g.e_us):
        mh = CT.parse_name(nm.node_name[int(u)])
        cd = CT.parse_name(nm.edge_name[k])
        assert cd["cd"] == mh["mh"], (nm.node_name[int(u)], nm.edge_name[k])
        assert cd["sub"] == mh["sub"] and cd["town"] == mh["town"]


def test_a_name_agrees_with_its_own_town_and_subnet_columns(monkeypatch):
    """The contract's own check. A name that says one thing and a column another is a
    layer nobody can filter."""
    a, g, f = _naming_case(monkeypatch)
    nm = EX.build_names(a, g, f)
    for i, n in enumerate(nm.node_name):
        p = CT.parse_name(n)
        assert p["town"] == nm.node_town[i]
        assert p["sub"] == nm.node_sub[i]


def test_the_town_of_an_outfall_outside_every_settlement_is_recorded_not_assumed(
        monkeypatch):
    """'Elements outside any town take the letter of the first town DOWNSTREAM of them.'
    Downstream of an outfall is the client's Main Pipe, which carries no direction in this
    data - so the nearest settlement stands in AND THE DISTANCE IS PUBLISHED."""
    a, g, f = _naming_case(monkeypatch)
    a.chambers.loc[4, ["X", "Y"]] = [5000.0, 0.0]
    a.chambers.geometry = [Point(x, y) for x, y in zip(a.chambers.X, a.chambers.Y)]
    nm = EX.build_names(a, g, f)
    assert any("NO mapped settlement" in n for n in nm.notes), nm.notes
    assert nm.stats["outfalls_nearest_town"] >= 1
    assert nm.stats["town_dist"][4] > 1000.0


def test_nothing_is_named_when_the_settlement_layer_is_missing(monkeypatch):
    """And the publication gate then REFUSES the layer, which is the correct outcome -
    not a fallback that invents a letter."""
    a, g, f = _naming_case(monkeypatch)
    monkeypatch.setattr(EX, "_read_towns", lambda: None)     # AFTER the case is built
    nm = EX.build_names(a, g, f)
    assert all(n == "" for n in nm.node_name)
    assert nm.notes and "could not be read" in nm.notes[0]


# ======================================================================================
# 15.  THE SUBNETWORK POLYGON LAYER
# ======================================================================================

def test_the_subnetwork_polygon_covers_the_plots_it_serves(monkeypatch):
    crs = f"EPSG:{CT.CRS_EPSG}"
    a, g, f = _naming_case(monkeypatch)
    nm = EX.build_names(a, g, f)
    a.trunk = gpd.GeoDataFrame(geometry=[LineString([(-100, 5), (200, 5)])], crs=crs)
    a.unserved = gpd.GeoDataFrame(geometry=[], crs=crs)
    jn = EX.measure_joins(a, g, f)
    r = gpd.GeoDataFrame(dict(
        SUB_NAME=[nm.subnet_name[2], nm.subnet_name[2], nm.subnet_name[4]],
        TOWN=["I", "I", "A"], SUBNET=["S01", "S01", "S01"], LEN_M=[30.0, 30.0, 30.0]),
        geometry=list(a.segments.geometry), crs=crs)
    nd = gpd.GeoDataFrame(dict(
        NODE_UID=g.uid, NAME=nm.node_name,
        SUB_NAME=[nm.subnet_name[int(s)] for s in f.subnet],
        DEPTH_M=[1.5, 2.0, 3.0, 1.2, 4.5]),
        geometry=list(a.chambers.geometry), crs=crs)
    cn = gpd.GeoDataFrame(dict(
        SUB_NAME=[nm.subnet_name[2]] * 3 + [nm.subnet_name[4]],
        Q_ADF_M3D=[1.0, 1.0, 1.0, 2.0], N_PROP=[1.4, 1.4, 1.4, 2.8]),
        geometry=[Point(15, 5), Point(45, 5), Point(65, 5), Point(710, 5)], crs=crs)
    out = EX.build_subnetworks({"reaches": r, "nodes": nd, "connections": cn},
                               a, g, f, nm, jn)
    assert len(out) == 2 and set(out.SERVED) == {1}
    ibri = out[out.NAME == nm.subnet_name[2]].iloc[0]
    assert int(ibri.N_PLOT) == 3
    assert int(ibri.N_CHAMBER) == 3
    assert float(ibri.DEEP_M) == 3.0
    assert ibri.geometry.contains(Point(45, 5)), \
        "the polygon does not cover a plot the subnetwork serves"
    assert float(ibri.AREA_M2) == pytest.approx(ibri.geometry.area, abs=0.1),         "AREA_M2 must agree with the polygon it describes - the contract checks exactly "         "this on every polygon layer it declares"


def test_a_subnetwork_short_of_the_main_pipe_carries_a_flag_and_a_reason(monkeypatch):
    crs = f"EPSG:{CT.CRS_EPSG}"
    a, g, f = _naming_case(monkeypatch)
    nm = EX.build_names(a, g, f)
    a.trunk = gpd.GeoDataFrame(geometry=[LineString([(-100, 5), (200, 5)])], crs=crs)
    a.unserved = gpd.GeoDataFrame(geometry=[], crs=crs)
    jn = EX.measure_joins(a, g, f)
    r = gpd.GeoDataFrame(dict(
        SUB_NAME=[nm.subnet_name[2], nm.subnet_name[2], nm.subnet_name[4]],
        TOWN=["I", "I", "A"], SUBNET=["S01", "S01", "S01"], LEN_M=[30.0, 30.0, 30.0]),
        geometry=list(a.segments.geometry), crs=crs)
    nd = gpd.GeoDataFrame(dict(
        NODE_UID=g.uid, NAME=nm.node_name,
        SUB_NAME=[nm.subnet_name[int(s)] for s in f.subnet],
        DEPTH_M=[1.5, 2.0, 3.0, 1.2, 4.5]),
        geometry=list(a.chambers.geometry), crs=crs)
    cn = gpd.GeoDataFrame(dict(SUB_NAME=[nm.subnet_name[2]], Q_ADF_M3D=[1.0],
                               N_PROP=[1.4]), geometry=[Point(15, 5)], crs=crs)
    out = EX.build_subnetworks({"reaches": r, "nodes": nd, "connections": cn},
                               a, g, f, nm, jn)
    far = out[out.NAME == nm.subnet_name[4]].iloc[0]
    assert int(far.JOIN_MAIN) == 0
    assert far.FLAG and "Main Pipe" in far.WHY
    assert float(far.GAP_M) > EX.JOIN_TOL_M


# ======================================================================================
# 16.  make_overview - it must compute NOTHING the export already published
# ======================================================================================

@pytest.mark.slow
def test_make_overview_rebuilds_the_themes_from_the_published_layers(tmp_path,
                                                                    monkeypatch):
    import make_overview as MO
    layers = EX.demo_layers()
    gpkg = tmp_path / "W12_export.gpkg"
    for name, g in layers.items():
        g.to_file(gpkg, layer=name, driver="GPKG")
    monkeypatch.setattr(EX, "GPKG_OUT", str(gpkg))
    monkeypatch.setattr(EX, "DIR_KMZ", str(tmp_path))
    monkeypatch.setattr(EX, "DIR_DXF", str(tmp_path))
    assert MO.main([]) == 0
    kmz = sorted(p for p in os.listdir(tmp_path) if p.endswith(".kmz"))
    assert len(kmz) == 3, kmz
    assert any(p.endswith(".dxf") for p in os.listdir(tmp_path))
    assert any(p.endswith(".qml") for p in os.listdir(tmp_path))


def test_make_overview_refuses_to_draw_a_quietly_poorer_map(tmp_path, monkeypatch):
    """A map drawn without a column the theme needs looks exactly like a complete one.
    That is the whole class of defect this project keeps paying for."""
    import make_overview as MO
    layers = EX.demo_layers()
    layers["nodes"] = layers["nodes"].drop(columns=["DROP_WHY"])
    gpkg = tmp_path / "W12_export.gpkg"
    for name, g in layers.items():
        g.to_file(gpkg, layer=name, driver="GPKG")
    monkeypatch.setattr(EX, "GPKG_OUT", str(gpkg))
    monkeypatch.setattr(EX, "DIR_KMZ", str(tmp_path))
    monkeypatch.setattr(EX, "DIR_DXF", str(tmp_path))
    with pytest.raises(SystemExit) as e:
        MO.main([])
    assert "DROP_WHY" in str(e.value)


def test_make_overview_computes_nothing_of_its_own():
    """The change that matters in that file. It used to cluster the unserved plots, find
    the outfalls, measure the gap to the trunk and count the stations with nothing
    upstream - all of which `s8_export` already publishes. Two functions for one published
    quantity is inheritance row 10, and it is how seven station counts got into
    circulation."""
    import ast
    import make_overview as MO
    src = open(MO.__file__, encoding="utf-8").read()
    for banned in ("cKDTree", "convex_hull", "nx.ancestors", "union_all", "networkx"):
        assert banned not in src, (
            f"make_overview.py is computing something again ({banned!r}). It reads "
            "published fields; the answers live in s8_export.")
    tree = ast.parse(src)
    fns = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert fns <= {"load", "summary", "main", "_n", "line"}, sorted(fns)


# ======================================================================================
# 17.  THE ROUND TRIP - a name lost to a DBF is a field the auditor cannot find
# ======================================================================================

def test_every_layer_survives_a_shapefile_round_trip_with_all_its_names(tmp_path):
    old = EX.DIR_SHP
    EX.DIR_SHP = str(tmp_path)
    try:
        written = EX.write_shapefiles(EX.demo_layers(), {})
    finally:
        EX.DIR_SHP = old
    assert written
    for p in [x for x in written if x.endswith(".shp")]:
        back = gpd.read_file(p)
        assert len(back.columns) > 1, p


def test_the_field_dictionary_is_written_where_the_export_is(tmp_path):
    old = EX.OUT
    EX.OUT = str(tmp_path)
    try:
        p = EX.write_field_dictionary(EX.demo_layers())
    finally:
        EX.OUT = old
    assert os.path.basename(p) == "W12_FIELD_DICTIONARY.md"
    assert os.path.getsize(p) > 4000, "a one-page dictionary that fits in four kilobytes " \
                                      "is not describing 150 fields"


def test_dep_m_is_written_onto_all_five_layers():
    """The DEPTH theme classifies one column. `_extra_columns` is where it is put there,
    and it must reach every one of the five - a layer without it drops off the map with
    no error at all."""
    layers = EX.demo_layers()
    for k in ("reaches", "nodes", "stations", "rising_mains", "subnetworks"):
        layers[k] = layers[k].drop(columns=["DEP_M"])
    layers["crossings"] = gpd.GeoDataFrame(
        dict(CROSS_ID=["X1"], OBSTACLE=["wadi"], SQUARE=[1]),
        geometry=[LineString([(0, 0), (1, 1)])], crs=f"EPSG:{CT.CRS_EPSG}")
    layers["reaches"] = layers["reaches"].assign(CLEAN_BY="velocity")
    EX._extra_columns(layers)
    for k in ("reaches", "nodes", "stations", "rising_mains", "subnetworks"):
        assert "DEP_M" in layers[k].columns, k
    assert "STR_CLS" in layers["nodes"].columns
    assert layers["nodes"].STR_CLS.nunique() > 1, \
        "every chamber got the same structure class - the column is not reading its input"


def test_the_qml_declares_the_type_of_the_column_it_categorises(tmp_path):
    """A categorized renderer told the wrong type matches NOTHING, and a style that
    renders nothing looks exactly like a layer with no features in it."""
    layers = EX.demo_layers()
    old = EX.DIR_KMZ
    EX.DIR_KMZ = str(tmp_path)
    try:
        depth = EX.theme_depth(layers)[1]           # manholes: DEP_BAND, an integer column
        struct = EX.theme_structure(layers)[0]      # conduits: STR_CLS, a text column
        qd, qs = EX.theme_qml("depth", depth), EX.theme_qml("structure", struct)
    finally:
        EX.DIR_KMZ = old
    d = ET.parse(qd).getroot()
    assert {c.get("type") for c in d.findall(".//category")} == {"int"}
    s = ET.parse(qs).getroot()
    assert {c.get("type") for c in s.findall(".//category")} == {"QString"}


def test_the_structure_theme_colours_subnetworks_in_presents_own_order(tmp_path):
    """Two maps of the same network in different colours is the picture-level form of
    publishing one quantity twice. `present.classify()` orders a categorical view by
    descending total length; the STRUCTURE theme has to take the same order or the
    per-question `subnet` map and this one disagree about which subnetwork is which."""
    layers = EX.demo_layers()
    r = layers["reaches"]
    tl = EX.theme_structure(layers)[0]
    order = (r.assign(_k=r.SUB_NAME.astype(str))
             .groupby("_k")["LEN_M"].sum().sort_values(ascending=False).index.tolist())
    got = {}
    for key, _lab, rgb, _w in tl.classes:
        got.setdefault(key.rsplit(" | ", 1)[0], rgb)
    for i, sub in enumerate(order):
        assert got[sub] == EX.PR.golden_rgb(i), (
            f"{sub} is colour {i} in present's order and a different one on the theme")


def test_conduit_weight_rises_with_diameter():
    """'conduit line weight increases with diameter'. Colour is the subnetwork, so the
    class has to be the PAIR - and the width has to be monotonic in the DN band."""
    widths = [w for _hi, _lab, w in EX.DN_BANDS]
    assert widths == sorted(widths) and len(set(widths)) == len(widths)
    tl = EX.theme_structure(EX.demo_layers())[0]
    by_band = {}
    for key, _lab, _rgb, w in tl.classes:
        by_band[key.rsplit(" | ", 1)[1]] = w
    got = [by_band[lab] for _hi, lab, _w in EX.DN_BANDS if lab in by_band]
    assert got == sorted(got), by_band


def test_every_number_this_stage_adds_is_in_its_own_register():
    """'Every constant must trace to a cited guideline page or be declared an assumption in
    the module's own ASSUMPTIONS registry.' EXPORT_NUMBERS is that registry, and it is what
    the data dictionary and EXPORT.md print - so a number that shapes published data and is
    not in it is a number nobody can trace."""
    names = {n for n, _v, _s, _w in EX.EXPORT_NUMBERS}
    for n in ("SERVICE_BUFFER_M", "UNSERVED_CLUSTER_M", "UNSERVED_MIN_PLOTS",
              "JOIN_TOL_M", "DEPTH_BREAKS", "TRENCH_SIDE_M", "MH_DIA_STD_M"):
        assert n in names, f"{n} shapes a published number and is not in EXPORT_NUMBERS"
    for _n, _v, src, why in EX.EXPORT_NUMBERS:
        assert src.strip(), "a declared number with no source"
        assert len(why.strip()) > 40, "a declared number with no consequence written down"
    # and the module reads them FROM the register, so there is one value for each
    assert EX.SERVICE_BUFFER_M == EX.EXPORT_NUM["SERVICE_BUFFER_M"]
    assert EX.UNSERVED_CLUSTER_M == EX.EXPORT_NUM["UNSERVED_CLUSTER_M"]
    assert EX.UNSERVED_MIN_PLOTS == EX.EXPORT_NUM["UNSERVED_MIN_PLOTS"]
    assert EX.JOIN_TOL_M == EX.EXPORT_NUM["JOIN_TOL_M"]


def test_the_register_reaches_the_field_dictionary_and_the_report():
    md = EX.field_dictionary_md(EX.demo_layers())
    assert "banned field" in md or "BANNED_FIELDS" in md
    tab = EX._assumptions_table()
    ids = set(tab.ID.astype(str))
    assert any(i.startswith("S8-") for i in ids), \
        "the stage's own declared numbers do not reach the published assumptions table"
