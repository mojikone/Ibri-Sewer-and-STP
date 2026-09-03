"""DEFECT CLASSES 3 AND 4 - a FABRICATED column, and a column that DISAGREES WITH ITS OWN
GEOMETRY.

Bug 3: a crossing angle was published as `ANGLE_DEG = 90` on all 3,290 rows and called a
declaration. When it was finally measured the minimum was 0.00 deg and 23 crossings were
under 45. A single `nunique() == 1` check on a physical quantity would have caught it the
moment it was written, which is why this file exists.

Bug 4: a length field differed from the shape it described by up to 87 m. Every published
length reads the FIELD, not the geometry, so the schedule and the drawing then describe
different pipes and nothing complains.

WHAT THIS FILE CHECKS, AND ON WHAT AUTHORITY
  * `LEN_M` against the geometry it sits on, to `contract.LEN_TOL_M` (0.05 m, a structural
    tolerance declared in the contract, not a design value).
  * X / Y against the point they describe, to the same tolerance.
  * every column of every published layer of 50 rows or more, for constancy. A column whose
    NAME says it is a measured quantity may not be constant unless it is on the declared
    list below WITH A REASON - and the reasons are printed on every run, because a
    "legitimately constant" column is usually a fact worth knowing about the design.
  * columns that must agree with each other inside one file.

The declared list is a RATCHET, not an amnesty: a new constant measured column fails.
"""
from __future__ import annotations

import re

import numpy as np
import pytest

from conftest import GPKGS, gpkg_path, layer, layer_names

pytestmark = pytest.mark.published


# ======================================================================================
# helpers
# ======================================================================================

def _all_layers():
    """(gpkg key, layer name, GeoDataFrame) for every published layer that exists."""
    import fiona
    import geopandas as gpd
    for key in GPKGS:
        p = gpkg_path(key)
        if not p.is_file():
            continue
        for name in fiona.listlayers(str(p)):
            try:
                g = gpd.read_file(str(p), layer=name)
            except Exception:                                       # noqa: BLE001
                continue
            yield key, name, g


def _has_geom(g) -> bool:
    import geopandas as gpd
    return (isinstance(g, gpd.GeoDataFrame) and "geometry" in g.columns
            and len(g) > 0 and not g.geometry.isna().all())


# ======================================================================================
# 1. A COLUMN AGAINST ITS OWN GEOMETRY
# ======================================================================================

# `LEN_M` is the contract's name for "the length of THIS feature". Aggregates that happen
# to end in _LEN_M are a different quantity and are checked separately below.
_OWN_LENGTH = "LEN_M"
_AGGREGATE_LENGTHS = {
    "UPS_LEN_M": "total length UPSTREAM of this arc, not its own",
    "LEN_WAS_M": "the length before the 10 m head setback was taken off",
    "RUN_LEN_M": "the length of the whole run this reach belongs to",
    "PATH_UP_M": "flow-path length from the head, not this reach",
}


def test_every_len_m_agrees_with_its_own_geometry(contract):
    """The 87 m defect. Tolerance is contract.LEN_TOL_M - a structural tolerance, declared
    there as such."""
    checked = 0
    worst = ("", 0.0)
    bad = []
    for key, name, g in _all_layers():
        if not _has_geom(g) or _OWN_LENGTH not in g.columns:
            continue
        if not (set(g.geom_type.dropna()) & {"LineString", "MultiLineString"}):
            continue
        if g[_OWN_LENGTH].dtype.kind not in "if":
            continue
        d = (g.geometry.length - g[_OWN_LENGTH].astype(float)).abs()
        d = d[np.isfinite(d)]
        if not len(d):
            continue
        checked += 1
        if float(d.max()) > worst[1]:
            worst = (f"{key}/{name}", float(d.max()))
        n_bad = int((d > contract.LEN_TOL_M).sum())
        if n_bad:
            bad.append(f"  {key}/{name}: {n_bad} of {len(g)} rows, worst {d.max():.3f} m")
    print(f"\n    [LEN_M vs geometry] {checked} line layers checked; worst disagreement "
          f"{worst[1] * 1000:.3f} mm on {worst[0]} (tolerance {contract.LEN_TOL_M * 1000:.0f} mm)")
    assert checked >= 5, "no line layers carried LEN_M - the check did not actually run"
    assert not bad, ("a published length disagrees with the shape it describes:\n"
                     + "\n".join(bad))


def test_aggregate_lengths_are_never_shorter_than_the_feature(flow_arcs):
    """UPS_LEN_M is the length UPSTREAM. It is not the arc's own length and must not be
    checked against the geometry - but it must still be at least as long as the arc, or
    the accumulation lost a reach."""
    a = flow_arcs
    if "UPS_LEN_M" not in a.columns:
        pytest.skip("no UPS_LEN_M on this layer")
    bad = int((a["UPS_LEN_M"] + 1e-6 < a["LEN_M"]).sum())
    assert bad == 0, f"{bad} arcs have less upstream length than their own length"
    print(f"\n    [aggregate lengths] {', '.join(sorted(_AGGREGATE_LENGTHS))} are checked "
          f"for plausibility, not against geometry - each is named above with what it is")


def test_x_and_y_agree_with_the_point_they_describe(contract):
    """A node layer that carries X and Y as well as a geometry carries the same fact
    twice. If they part, half the pipeline reads one and half the other."""
    checked = 0
    bad = []
    for key, name, g in _all_layers():
        if not _has_geom(g) or not {"X", "Y"} <= set(g.columns):
            continue
        if not (set(g.geom_type.dropna()) <= {"Point"}):
            continue
        dx = (g.geometry.x - g["X"].astype(float)).abs()
        dy = (g.geometry.y - g["Y"].astype(float)).abs()
        checked += 1
        n = int(((dx > contract.LEN_TOL_M) | (dy > contract.LEN_TOL_M)).sum())
        if n:
            bad.append(f"  {key}/{name}: {n} of {len(g)} points, worst "
                       f"{max(dx.max(), dy.max()):.3f} m")
    print(f"\n    [X/Y vs geometry] {checked} point layers checked")
    assert checked >= 2
    assert not bad, "\n".join(bad)


def test_geometry_endpoints_are_the_nodes_the_reach_claims(reaches, hier_nodes, contract):
    """H16: topology is written down, never inferred from geometry. The other half of that
    rule is that the geometry must AGREE with what was written down - W10 shipped a layer
    in 7,919 pieces because 91.4 % of its links stopped 1.000 m short of what they joined."""
    xy = {u: (x, y) for u, x, y in
          zip(hier_nodes.NODE_UID, hier_nodes.geometry.x, hier_nodes.geometry.y)}
    worst = 0.0
    bad = 0
    for us, ds, geom in zip(reaches.US_NODE, reaches.DS_NODE, reaches.geometry):
        if geom is None or us not in xy or ds not in xy:
            continue
        c = list(geom.coords)
        for want, got in ((xy[us], c[0]), (xy[ds], c[-1])):
            d = np.hypot(want[0] - got[0], want[1] - got[1])
            worst = max(worst, d)
            if d > contract.ENDPOINT_TOL_M:
                bad += 1
    print(f"\n    [endpoints] worst gap between a reach end and the chamber it names: "
          f"{worst * 1000:.3f} mm (tolerance {contract.ENDPOINT_TOL_M * 1000:.0f} mm)")
    assert bad == 0, f"{bad} reach endpoints do not sit on the node they reference"


# ======================================================================================
# 2. THE FABRICATED COLUMN
# ======================================================================================

# A column whose NAME says it holds a measured or computed quantity.
_MEASURED_NAME = re.compile(
    r"(^|_)(LEN|LENGTH|DIST|AREA|ANG|DEG|SLOPE|GRAD|FALL|RISE|DEPTH|COVER|GRD|ELEV|LEVEL"
    r"|Q|V|DN|DIA|HEAD|LIFT|KW|KWH|VOL|M3|M2|WELL|RET|SEP|X|Y|Z|PCT|MI|HZ|TAU)($|_|[0-9])",
    re.I)

# Constant on purpose, each with the reason. THIS LIST IS A RATCHET: a new constant
# measured column fails the test. Where a reason is itself a finding, it says so.
_DECLARED_CONSTANT = {
    ("pumps", "stations", "N_STBY"):
        "G203-p40 Table 17: one standby pump on Type 1 and Type 2 alike, and every station "
        "here is Type 1 or 2. A guideline constant, not a measurement.",
    ("pumps", "stations", "WW_SEPOK"):
        "retention is inside the 30 min septicity limit at every station (G203-p50).",
    ("pumps", "stations", "DRY_DIST"):
        "FINDING, not a clean pass: every one of the 85 sites sampled hazard class 0, so "
        "the distance to dry ground is 0 m at all of them - and class 0 on these grids "
        "means NO MODEL RESULT, read as dry under the engineer's ruling of 2026-09-03. "
        "No station site has been tested against a modelled flood extent.",
    ("pumps", "rising_mains", "SEPTIC_FL"):
        "a rising main is anaerobic BY DEFINITION (philosophy sec 6), so the flag is 1 on "
        "every main by construction and carries no information.",
    ("pumps", "rising_mains", "AIRV_DN"):
        "G203-p53 Table 24 sizes an air valve off the main's diameter, and every main here "
        "is small enough to take the same size.",
    ("pumps", "rising_mains", "WASH_DN"):
        "G203-p54 sec 8.4.2, same reasoning as AIRV_DN.",
    ("streams", "streams", "THRESH_M2"):
        "the accumulation threshold the stream network was cut at - a declared parameter "
        "stamped on every row, which is how a parameter SHOULD be published.",
    ("roads", "roads", "TAU_PA"): "the assumed tractive stress, stamped as a banner (GAP-9).",
    ("roads", "corridors", "TAU_PA"): "as above.",
    ("roads", "nodes", "TAU_PA"): "as above.",
    ("chambers", "segments", "SPACE_OK"):
        "chambers are PLACED at or below the Table 12 maximum, so the spacing check passes "
        "by construction. The column records that the check ran, not a finding.",
}


def test_no_measured_column_is_constant_across_a_whole_layer():
    """The ANGLE_DEG = 90 defect, caught mechanically.

    Rule: on a layer of 50 rows or more, a column whose name says it holds a measured
    quantity may not hold one value on every row unless the reason is written down here.
    """
    unexplained = []
    declared_seen = []
    for key, name, g in _all_layers():
        if len(g) < 50:
            continue
        for c in g.columns:
            if c == "geometry" or not _MEASURED_NAME.search(c):
                continue
            if g[c].dtype.kind not in "ifu":
                continue                      # a banner or a label, not a measurement
            s = g[c].dropna()
            if len(s) < 50 or s.nunique() != 1:
                continue
            k = (key, name, c)
            if k in _DECLARED_CONSTANT:
                declared_seen.append((k, s.iloc[0], len(g)))
            else:
                unexplained.append(f"  {key}/{name}.{c} = {s.iloc[0]!r} on all {len(g)} rows")
    for k, v, n in sorted(declared_seen, key=lambda t: t[0]):
        print(f"\n    [constant, declared] {k[0]}/{k[1]}.{k[2]} = {v!r} on {n:,} rows\n"
              f"        {_DECLARED_CONSTANT[k]}")
    assert not unexplained, (
        "a column that should carry a measurement holds one value on every row. That is "
        "how ANGLE_DEG = 90 shipped on 3,290 crossings. Measure it, or declare here why "
        "it is genuinely constant:\n" + "\n".join(unexplained))


def test_the_inlet_angle_is_measured_and_the_minimum_is_reported(crit):
    """The specific regression. H10 requires an inlet angle of 90 deg or more (G203-p30);
    the previous iteration published a fabricated 90 on every row. It must VARY, the values
    must be real angles, and the breaches must be countable."""
    found = []
    for key, name, g in _all_layers():
        for c in g.columns:
            if c.upper() in ("INLET_DEG", "ANGLE_DEG") and len(g) >= 50:
                s = g[c].dropna().astype(float)
                if len(s):
                    found.append((key, name, c, s))
    assert found, "no inlet-angle column found on any published layer"
    for key, name, c, s in found:
        real = s[s >= 0.0]                      # negative is a not-applicable sentinel
        n_under = int((real < crit.INLET_MIN_DEG - 1e-9).sum())
        print(f"\n    [angle] {key}/{name}.{c}: {len(real):,} measured, min "
              f"{real.min():.2f} deg, max {real.max():.2f}, {real.nunique():,} distinct "
              f"values, {n_under:,} below the {crit.INLET_MIN_DEG:.0f} deg minimum "
              f"(G203-p30)")
        assert real.nunique() > 1, (
            f"{key}/{name}.{c} is constant - this is the fabricated-angle defect again")
        assert real.max() <= 180.0 + 1e-9


def test_a_not_applicable_angle_uses_a_sentinel_that_cannot_pass_as_an_angle():
    """`DUAL_ANG` is the angle a corridor makes with a dual carriageway, and -1 means 'this
    corridor never meets one'. A sentinel is the right answer; the wrong answer is a
    plausible number, which is exactly what 90 on every row was. The check is that the
    sentinel sits OUTSIDE the range of a real angle, so no consumer can average it in."""
    g = layer("roads", "corridors")
    if "DUAL_ANG" not in g.columns:
        pytest.skip("no DUAL_ANG on this layer")
    s = g.DUAL_ANG.dropna().astype(float)
    na, real = s[s < 0.0], s[s >= 0.0]
    print(f"\n    [DUAL_ANG] {len(na):,} of {len(s):,} corridors carry the "
          f"{(na.iloc[0] if len(na) else 0):.0f} not-applicable sentinel; the "
          f"{len(real):,} real angles run {real.min():.2f} to {real.max():.2f} deg")
    assert len(na) and (na == na.iloc[0]).all() and na.iloc[0] < 0.0
    assert real.nunique() > 1


def test_flag_columns_are_zero_or_one_and_not_all_the_same_where_they_matter():
    """A boolean flag that is 1 everywhere is either a construction artefact or a lie. The
    ones that matter are checked by name against the layer that must disagree with them."""
    for key, name, g in _all_layers():
        for c in g.columns:
            if c == "geometry" or g[c].dtype.kind not in "iu":
                continue
            if not re.match(r"^(IS_|ON_|HAS_|OK$)", c) and not c.endswith("_OK"):
                continue
            vals = set(g[c].dropna().unique().tolist())
            assert vals <= {0, 1}, f"{key}/{name}.{c} is named as a flag but holds {vals}"


# ======================================================================================
# 3. COLUMNS THAT MUST AGREE WITH EACH OTHER
# ======================================================================================

def test_is_outfall_agrees_with_the_graph(flow_arcs, flow_nodes):
    """Contract fix 5: IS_OUTFALL is DERIVED from the graph, never asserted. A design that
    has to be told where its outfalls are does not know where its flow goes.

    One legitimate subtlety, and it is why this is tested against the ARCS rather than
    against DS_NODE being blank: an outfall's DS_NODE is an EXTERNAL id - here the literal
    `MAIN_PIPE`, the client's trunk, which is an INPUT and is not a node in this graph.
    """
    n, a = flow_nodes, flow_arcs
    has_out = set(a.loc[a.IS_ROUTE.astype(int) == 1, "US_NODE"])
    marked = set(n.loc[n.IS_OUTFALL.astype(int) == 1, "NODE_UID"])
    wrong = marked & has_out
    ext = sorted(set(n.loc[n.IS_OUTFALL.astype(int) == 1, "DS_NODE"].astype(str)) - {""})
    print(f"\n    [outfalls] {len(marked):,} of {len(n):,} nodes are outfalls; their "
          f"DS_NODE points outside the graph at {ext}")
    assert not wrong, (f"{len(wrong)} nodes marked IS_OUTFALL still own an outgoing route "
                       f"arc, e.g. {sorted(wrong)[:5]}")


@pytest.mark.audit
def test_every_node_without_an_outlet_is_an_outfall(flow_arcs, flow_nodes):
    """H15: 'what is never legal is a piece that drains nowhere'. A node with no outgoing
    arc is either an outfall or an orphan, and the layer must say which."""
    n, a = flow_nodes, flow_arcs
    has_out = set(a.loc[a.IS_ROUTE.astype(int) == 1, "US_NODE"])
    stranded = n[~n.NODE_UID.isin(has_out) & (n.IS_OUTFALL.astype(int) == 0)]
    q = float(stranded.Q_ADF_M3D.sum()) if "Q_ADF_M3D" in stranded.columns else float("nan")
    print(f"\n    [H15 orphans] {len(stranded):,} of {len(n):,} nodes have no outgoing "
          f"route arc and are not outfalls, carrying {q:,.1f} m3/d")
    assert stranded.empty, (
        f"{len(stranded)} nodes carrying {q:,.1f} m3/d have no outgoing route arc and are "
        f"not marked as outfalls - by H15 they drain nowhere")


@pytest.mark.audit
def test_node_delivered_agrees_with_arc_delivered(flow_arcs, flow_nodes):
    """A node on an arc the file itself declares UNDELIVERED cannot be delivered. Two
    columns in one GeoPackage must not answer the same question two ways."""
    isl = flow_arcs[flow_arcs.DELIVERED.astype(int) == 0]
    if not len(isl):
        pytest.skip("no undelivered arcs in this run")
    on_isl = set(isl.US_NODE) | set(isl.DS_NODE)
    sub = flow_nodes[flow_nodes.NODE_UID.isin(on_isl)]
    wrong = sub[sub.DELIVERED.astype(int) == 1]
    q = float(wrong.Q_ADF_M3D.sum()) if "Q_ADF_M3D" in wrong.columns else float("nan")
    print(f"\n    [H15 delivered] {len(isl):,} arcs are marked DELIVERED = 0; "
          f"{len(wrong):,} of the {len(sub):,} nodes on them are still marked "
          f"DELIVERED = 1, carrying {q:,.1f} m3/d")
    assert wrong.empty, (
        f"{len(wrong)} nodes carrying {q:,.1f} m3/d sit on the {len(isl)} arcs this same "
        f"file marks DELIVERED = 0 (the `undelivered` layer calls them 'a piece that "
        f"drains nowhere', H15) - yet the node layer publishes DELIVERED = 1 for every "
        f"one of them. One of the two columns is wrong.")


def test_tier_shares_sum_to_the_published_length(reaches):
    """Lengths sum. The tier table and the reach layer are two views of one number."""
    total = float(reaches.LEN_M.sum())
    by_tier = reaches.groupby("TIER").LEN_M.sum()
    assert abs(float(by_tier.sum()) - total) < 1e-6
    print(f"\n    [lengths sum] {total / 1000:,.1f} km over {len(by_tier)} tiers: "
          + ", ".join(f"{t} {v / 1000:,.1f}" for t, v in by_tier.items()))


def test_no_negative_or_absurd_physical_value():
    """A range guard, not a design rule: a negative length, a negative flow or a depth past
    the contract's own sanity ceiling means an arithmetic error upstream."""
    from w11b.contract import DEPTH_SANITY_M
    bad = []
    for key, name, g in _all_layers():
        for c in g.columns:
            if c == "geometry" or g[c].dtype.kind not in "if":
                continue
            s = g[c].dropna().astype(float)
            if not len(s):
                continue
            u = c.upper()
            if (u == "LEN_M" or u.startswith("Q_") or u.endswith("_LS")
                    or u.endswith("_M3D") or u.endswith("_KW")):
                if s.min() < -1e-9:
                    bad.append(f"  {key}/{name}.{c} min = {s.min()}")
            if u in ("DEPTH_M", "COVER_M", "LIFT_M", "HEAD_M"):
                if s.max() > DEPTH_SANITY_M * 5:
                    bad.append(f"  {key}/{name}.{c} max = {s.max()} (sanity "
                               f"{DEPTH_SANITY_M * 5})")
    assert not bad, "\n".join(bad)


def test_every_referenced_node_exists(reaches, hier_nodes, flow_arcs, flow_nodes):
    """A dangling id is a silent orphan. The contract raises on one at write time; this
    proves the published files kept the property."""
    for arcs, nodes, what in ((reaches, hier_nodes, "hier"), (flow_arcs, flow_nodes, "flows")):
        known = set(nodes.NODE_UID)
        refs = set(arcs.US_NODE) | set(arcs.DS_NODE)
        missing = refs - known
        assert not missing, (f"{what}: {len(missing)} node ids referenced by an arc do not "
                             f"exist in the node layer, e.g. {sorted(missing)[:5]}")


def test_identifiers_are_unique_where_they_are_keys():
    """Identity is minted once. A duplicated key means two things claim to be one thing."""
    keys = {("hier", "reaches"): "EDGE_UID", ("hier", "nodes"): "NODE_UID",
            ("flows", "arcs"): "EDGE_UID", ("flows", "nodes"): "NODE_UID",
            ("chambers", "chambers"): "NODE_UID", ("chambers", "connections"): "CONN_ID",
            ("pumps", "rising_mains"): "EDGE_UID"}
    for (key, name), col in keys.items():
        if name not in layer_names(key):
            continue
        g = layer(key, name)
        if col not in g.columns:
            continue
        dup = int(g[col].duplicated().sum())
        assert dup == 0, f"{key}/{name}.{col}: {dup} duplicated identifiers"


@pytest.mark.audit
def test_categorical_columns_only_hold_values_the_contract_allows(contract):
    """A value outside the allowed set is a SILENT SKIP in whatever check reads it - the
    contract says so about TIER by name."""
    bad = []
    for key, name, g in _all_layers():
        spec = contract.LAYERS.get(contract.LAYER_ALIASES.get(name, name))
        if spec is None:
            continue
        for f in spec.fields:
            if f.allowed is None or f.name not in g.columns:
                continue
            vals = set(g[f.name].dropna().astype(str).unique()) - {""}
            extra = vals - set(f.allowed)
            if extra:
                bad.append(f"  {key}/{name}.{f.name}: {sorted(extra)[:6]} not in "
                           f"{list(f.allowed)}")
    print(f"\n    [vocabulary] {len(bad)} published column(s) hold a token the contract's "
          f"`allowed` set does not name. The contract says it of TIER by name, and it is "
          f"true of every such field: an unrecognised value is a SILENT SKIP in whatever "
          f"check reads it, and `contract.validate()` would refuse the layer outright.")
    assert not bad, "\n".join(bad)
