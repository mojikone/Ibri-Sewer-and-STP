"""Synthetic-fixture tests for prep, RoadTreatment, TreeBuilder, ChamberPlacer,
StructureResolver — the geometry half of the pipeline."""

import math

import geopandas as gpd
import networkx as nx
import numpy as np
import pytest
from shapely.geometry import LineString, Polygon

from sewnet import prep
from sewnet.criteria import DEFAULT as C
from sewnet.model import Network, key_of
from sewnet.stages.chambers import ChamberPlacer, Labeller
from sewnet.stages.road_treatment import RoadTreatment
from sewnet.stages.structures import StructureResolver
from sewnet.stages.tree import TreeBuilder


class FakeSampler:
    """Deterministic tilted plane falling toward the south-west corner (0,0)."""

    def z(self, x, y):
        return 350.0 + 0.01 * (x + y)

    def profile(self, line, step=5.0):
        n = max(2, int(math.ceil(line.length / step)) + 1)
        out = []
        for i in range(n):
            d = min(line.length, i * step) if i < n - 1 else line.length
            p = line.interpolate(d)
            out.append((d, p.x, p.y, self.z(p.x, p.y)))
        return out


def grid_lines(n=5, spacing=100.0):
    lines = []
    for i in range(n):
        lines.append(LineString([(0, i * spacing), ((n - 1) * spacing, i * spacing)]))
        lines.append(LineString([(i * spacing, 0), (i * spacing, (n - 1) * spacing)]))
    return lines


def build(segs, sampler):
    tb = TreeBuilder(sampler, C)
    Gu = tb.build_undirected(segs)
    tb.mark_arterials(Gu)
    outfall = key_of(0.0, 0.0)
    Gd, unreachable = tb.build_tree(Gu, outfall)
    return Gd, outfall, unreachable


# ---------------------------------------------------------------- prep
def test_node_roads_splits_crossings():
    segs = prep.node_roads(gpd.GeoSeries(grid_lines()))
    assert len(segs) == 40                      # 10 lines x 4 pieces
    assert all(s.geom_type == "LineString" for s in segs)


def test_dual_detect_and_collapse():
    a = LineString([(0, 0), (300, 0)])
    b = LineString([(0, 10), (300, 10)])
    dual = prep.detect_duals([a, b])
    assert dual == {0, 1}
    merged = prep.collapse_duals([a, b], dual, merge_m=35.0)
    assert len(merged) == 1
    assert 0.0 <= merged[0].interpolate(0.5, normalized=True).y <= 10.0


def test_boundary_repair(tmp_path):
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    gpd.GeoDataFrame(geometry=[poly], crs="EPSG:32640").to_file(tmp_path / "b.shp")
    b = prep.load_boundary(str(tmp_path / "b.shp"))
    assert b.is_valid and b.area == pytest.approx(10000.0)


# ---------------------------------------------------------------- road treatment
def test_collinear_breaks_are_dissolved():
    """A straight street broken into three pieces becomes ONE corridor, so no chamber
    is placed at the breaks (user rule 2026-08-18)."""
    segs = [LineString([(0, 0), (100, 0)]),
            LineString([(100, 0), (220, 0)]),
            LineString([(220, 0), (330, 0)])]
    rt = RoadTreatment(FakeSampler(), C)
    out = rt.run(segs, units=[])
    assert len(out) == 1
    assert out[0].length == pytest.approx(330.0, abs=0.01)
    assert rt.report["collinear_joins"] == 2


def test_real_corner_is_not_dissolved():
    segs = [LineString([(0, 0), (100, 0)]), LineString([(100, 0), (100, 100)])]
    rt = RoadTreatment(FakeSampler(), C)
    out = rt.run(segs, units=[])
    assert len(out) == 2                        # a 90 deg corner is a real junction


def test_duplicate_vertices_removed():
    segs = [LineString([(0, 0), (50, 0), (50.001, 0), (100, 0)])]
    rt = RoadTreatment(FakeSampler(), C)
    out = rt.run(segs, units=[])
    assert rt.report["duplicate_vertices_removed"] >= 1
    assert len(out[0].coords) == 2              # collapses to a straight line


def test_roundabout_collapsed():
    """A small ring is not a sewer corridor: it collapses to its centre, legs reattach."""
    r, cx, cy = 15.0, 200.0, 200.0
    ring = [(cx + r * math.cos(t), cy + r * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, 9)]
    segs = [LineString([ring[i], ring[i + 1]]) for i in range(8)]
    segs.append(LineString([(cx - 120, cy), ring[4]]))     # west leg
    segs.append(LineString([ring[0], (cx + 120, cy)]))     # east leg
    rt = RoadTreatment(FakeSampler(), C)
    out = rt.run(segs, units=[])
    assert rt.report["roundabouts_collapsed"] == 1
    assert sum(g.length for g in out) < sum(g.length for g in segs)
    assert all(g.length > 50 for g in out)                 # only the legs survive


# ---------------------------------------------------------------- tree
def test_tree_orients_to_outfall_and_breaks_loops():
    segs = prep.node_roads(gpd.GeoSeries(grid_lines()))
    Gd, outfall, unreachable = build(segs, FakeSampler())
    assert not unreachable
    assert nx.is_directed_acyclic_graph(Gd)
    assert all(Gd.out_degree(n) <= 1 for n in Gd.nodes)
    assert Gd.out_degree(outfall) == 0
    assert Gd.number_of_edges() == 24           # spanning tree over 25 nodes
    for n in Gd.nodes:
        if n != outfall:
            assert outfall in nx.descendants(Gd, n)


# ---------------------------------------------------------------- chambers
def test_spacing_is_rounded_not_equally_divided():
    """User rule: 330 m at a 100 m maximum -> 80/80/80/90, not 4 x 82.5, not 100/100/100/30."""
    placer = ChamberPlacer(FakeSampler(), C, round_spacing=True)
    lens = placer.split_lengths(330.0, 100.0)
    assert sorted(lens) == [80.0, 80.0, 80.0, 90.0]
    assert sum(lens) == pytest.approx(330.0)


@pytest.mark.parametrize("L,expect", [
    (250.0, [80.0, 80.0, 90.0]),
    (180.0, [90.0, 90.0]),
    (95.0, [95.0]),                              # under the maximum: one reach, no split
])
def test_spacing_examples(L, expect):
    placer = ChamberPlacer(FakeSampler(), C, round_spacing=True)
    assert sorted(placer.split_lengths(L, 100.0)) == sorted(expect)


def test_spacing_never_exceeds_the_maximum():
    placer = ChamberPlacer(FakeSampler(), C, round_spacing=True)
    for L in (37.0, 101.0, 205.0, 333.0, 499.0, 1000.0):
        lens = placer.split_lengths(L, 100.0)
        assert sum(lens) == pytest.approx(L)
        assert max(lens) <= 100.0 + 1e-6
        assert min(lens) > 0


def test_chamber_placement_and_labels():
    segs = [LineString([(0, 0), (450, 0)])]
    s = FakeSampler()
    Gd, outfall, _ = build(segs, s)
    net = ChamberPlacer(s, C, round_spacing=False).run(Gd, outfall)
    Labeller.run(net)
    assert all(r.length <= C.MH_SPLIT_LEN + 0.01 for r in net.reaches)
    labels = [c.label for c in net.chambers.values()]
    assert len(labels) == len(set(labels))
    assert "OF-1" in labels
    assert sum(r.length for r in net.reaches) == pytest.approx(450.0, abs=0.1)


def test_bend_splits_the_reach():
    segs = [LineString([(0, 0), (80, 0), (80, 80)])]
    s = FakeSampler()
    Gd, outfall, _ = build(segs, s)
    net = ChamberPlacer(s, C, round_spacing=False).run(Gd, outfall)
    assert len(net.reaches) >= 2


# ---------------------------------------------------------------- structures
def test_one_physical_outlet_per_structure():
    """Two chambers at one point, each with an outlet, IS a two-outlet junction: they
    merge, and the losing branch restarts clear of the chamber."""
    s = FakeSampler()
    net = Network(outfall=key_of(0.0, 0.0))
    net.add_chamber(0.0, 0.0, 350.0, "outfall")
    net.add_chamber(100.0, 0.0, 351.0, "junction")
    net.add_chamber(100.05, 0.0, 351.0, "junction")      # same point, second chamber
    net.add_chamber(100.0, 60.0, 352.0, "head")
    net.add_chamber(160.0, 0.0, 352.5, "head")
    net.add_reach(key_of(100, 0), key_of(0, 0), LineString([(100, 0), (0, 0)]))
    net.add_reach(key_of(100.05, 0), key_of(0, 0), LineString([(100.05, 0), (0, 0)]))
    net.add_reach(key_of(100, 60), key_of(100, 0), LineString([(100, 60), (100, 0)]))
    net.add_reach(key_of(160, 0), key_of(100.05, 0), LineString([(160, 0), (100.05, 0)]))

    res = StructureResolver(s, C)
    res.run(net, units=[])
    net.assert_tree()                                    # both binding rules hold
    assert res.report["merged"] == 1
    merged = [k for k, c in net.chambers.items()
              if abs(c.x - 100.0) < 0.2 and abs(c.y) < 0.2]
    assert len(merged) == 1
    mx, my = net.chambers[merged[0]].xy
    for r in net.reaches:
        if r.up == merged[0] or r.dn == merged[0]:
            continue
        d = math.dist(r.geom.coords[0], (mx, my))
        assert d >= C.FANOUT_OFFSET_M - 0.01 or r.dn == merged[0]


def test_network_invariant_catches_a_second_outlet():
    net = Network(outfall=key_of(0, 0))
    net.add_chamber(0, 0, 350, "outfall")
    net.add_chamber(50, 0, 351)
    net.add_chamber(100, 0, 352)
    net.add_reach(key_of(50, 0), key_of(0, 0), LineString([(50, 0), (0, 0)]))
    net.add_reach(key_of(50, 0), key_of(100, 0), LineString([(50, 0), (100, 0)]))
    with pytest.raises(AssertionError):
        net.assert_one_outlet()
