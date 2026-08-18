"""Design-core tests: loads accumulation, the sizing/invert solver, tertiary
connectability, audit — all on synthetic fixtures with hand-checkable answers."""

import math
import pytest
import networkx as nx
from shapely.geometry import LineString

from sewnet import criteria as C, hydra as H, topo, manholes, loads, solver, tertiary, audit


class PlaneSampler:
    """Ground plane falling toward (0,0) at `gx` along x and `gy` along y."""
    def __init__(self, gx=0.01, gy=0.0, z0=350.0):
        self.gx, self.gy, self.z0 = gx, gy, z0

    def z(self, x, y):
        return self.z0 + self.gx * x + self.gy * y

    def profile(self, line, step=5.0):
        n = max(2, int(math.ceil(line.length / step)) + 1)
        out = []
        for i in range(n):
            d = min(line.length, i * step) if i < n - 1 else line.length
            p = line.interpolate(d)
            out.append((d, p.x, p.y, self.z(p.x, p.y)))
        return out


class DipSampler(PlaneSampler):
    """Plane with a sharp 2 m ground dip near x=150 (10 m wide) — mid-span cover trap."""
    def z(self, x, y):
        base = super().z(x, y)
        if 145.0 <= x <= 155.0:
            return base - 2.0
        return base


def straight_network(sampler, length=400.0, units_spec=((0, 3), (200, 2))):
    """One straight street along x, outfall at (0,0); units_spec = ((x_pos, count), ...)."""
    segs = [LineString([(0, 0), (length, 0)])]
    Gu = topo.build_undirected(segs, sampler)
    topo.mark_arterials(Gu)
    outfall = topo.nkey(0.0, 0.0)
    Gd, unreach = topo.build_tree(Gu, outfall)
    assert not unreach
    nodes, pipes, _sr = manholes.place(Gd, outfall, sampler)
    units = []
    k = 0
    for x, cnt in units_spec:
        for _ in range(cnt):
            units.append({"id": f"u{k}", "x": x, "y": 8.0, "cls": "B", "src": "plot"})
            k += 1
    per_mh, maxd = loads.assign_to_manholes(units, nodes)
    loads.accumulate(pipes, per_mh)
    return nodes, pipes, units, per_mh, outfall


def test_accumulation_monotone_and_mass_balance():
    s = PlaneSampler()
    nodes, pipes, units, per_mh, outfall = straight_network(s)
    # order pipes by distance downstream; qadf must be non-decreasing toward outfall
    G = nx.DiGraph()
    for p in pipes:
        G.add_edge(p["up"], p["dn"], obj=p)
    qs = []
    n = outfall
    chain = []
    while True:
        preds = list(G.predecessors(n))
        if not preds:
            break
        p = G[preds[0]][n]["obj"]
        chain.append(p)
        n = preds[0]
    chain.reverse()  # head -> outfall
    for a, b in zip(chain[:-1], chain[1:]):
        assert b["qadf_m3d"] >= a["qadf_m3d"] - 1e-9
    assert chain[-1]["qadf_m3d"] == pytest.approx(5 * C.PLOT_QADF_M3D, rel=1e-6)


def test_solver_basic_profile():
    s = PlaneSampler(gx=0.01)
    nodes, pipes, units, per_mh, outfall = straight_network(s)
    rep = solver.solve(nodes, pipes, s)
    assert rep["converged"]
    assert not rep["pockets"]
    for p in pipes:
        assert p["inv_up"] > p["inv_dn"]                      # no reverse gradients
        assert p["slope"] >= H.smin_for(p["dn_mm"], p["qpeak_m3s"]) * 0.999
        assert p["dn_mm"] >= C.DN_MIN_MAIN
    # audit must be clean
    v = audit.run(nodes, pipes, units, per_mh, s)
    assert v == [], f"violations: {v}"


def test_solver_respects_midspan_dip():
    s = DipSampler(gx=0.01)
    nodes, pipes, units, per_mh, outfall = straight_network(s)
    rep = solver.solve(nodes, pipes, s)
    # the pipe crossing the dip must keep 1.3 m crown cover under the dip floor
    for p in pipes:
        for ch, x, y, g in p["profile"]:
            inv = p["inv_up"] - p["slope"] * ch
            cover = g - (inv + p["dn_mm"] / 1000.0)
            assert cover >= C.MIN_COVER_CROWN - 0.02, f"{p['label']} cover {cover:.2f} at ch {ch}"
    v = audit.run(nodes, pipes, units, per_mh, s)
    assert [x for x in v if x[0] == "cover-min"] == []


def test_solver_steep_terrain_creates_drops_not_speeding():
    # 8% ground fall with a big flow: velocity must cap at 3 m/s, drops absorb the rest
    s = PlaneSampler(gx=0.08)
    nodes, pipes, units, per_mh, outfall = straight_network(
        s, units_spec=((0, 2000), (200, 1000)))   # big flows -> velocity cap binds
    rep = solver.solve(nodes, pipes, s)
    v = audit.run(nodes, pipes, units, per_mh, s)
    assert [x for x in v if x[0] == "vel-max"] == [], v
    assert [x for x in v if x[0].startswith("drop")] == [], v   # bookkeeping must be exact
    total_drop = sum(d["height"] for n in nodes.values() for d in n.get("drops", []))
    assert total_drop > 0.5                        # steep ground surplus went into drops


def test_deep_pocket_becomes_sls():
    # ground RISES 5% toward the outfall for 300 m -> pipes must dig ever deeper
    s = PlaneSampler(gx=-0.05)                     # z falls away from outfall
    nodes, pipes, units, per_mh, outfall = straight_network(s, length=400.0)
    rep = solver.solve(nodes, pipes, s)
    assert rep["n_failed_depth"] > 0
    assert rep["pockets"], "adverse terrain must produce an SLS pocket, not silence"


def test_tertiary_low_plot_flag_and_deepening():
    s = PlaneSampler(gx=0.01)
    nodes, pipes, units, per_mh, outfall = straight_network(s)
    solver.solve(nodes, pipes, s)

    class LowPlotSampler(PlaneSampler):
        def z(self, x, y):
            if y > 4.0:                            # plots sit 3 m below the road
                return super().z(x, y) - 3.0
            return super().z(x, y)

    ls = LowPlotSampler(gx=0.01)
    res, deepen = tertiary.connectability(per_mh, nodes, ls)
    assert any(not r["ok"] for r in res)
    assert deepen                                   # a deepening requirement was raised
    rep = solver.solve(nodes, pipes, s, node_min_depth=deepen)
    still = tertiary.recheck(res, nodes)
    assert len(still) < sum(1 for r in res if not r["ok"]) or not still


def test_riders_grouping():
    s = PlaneSampler()
    nodes, pipes, units, per_mh, outfall = straight_network(s, units_spec=((0, 7),))
    rs = tertiary.riders(per_mh, nodes)
    assert sum(r["n_units"] for r in rs) == 7
    assert all(r["n_units"] <= C.MAX_HCC_PER_RIDER for r in rs)
    assert len(rs) == 3                             # 3+3+1


def test_start_year_flags_are_operational_not_failures():
    s = PlaneSampler(gx=0.01)
    nodes, pipes, units, per_mh, outfall = straight_network(s)
    solver.solve(nodes, pipes, s)
    flags = audit.start_year_selfclean(nodes, pipes, per_mh)
    for f in flags:
        assert "v_start" in f and "tractive_ok" in f
