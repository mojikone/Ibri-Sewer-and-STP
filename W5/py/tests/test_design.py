"""Design-core tests: load accumulation, the coupled sizing/invert solver, house
connectability and the audit registry — synthetic fixtures with hand-checkable answers."""

import math

import networkx as nx
import pytest
from shapely.geometry import LineString

from sewnet import hydra as H
from sewnet.criteria import DEFAULT as C
from sewnet.model import LoadUnit, key_of
from sewnet.stages.audit import Auditor, selfclean_stats, start_year_selfclean
from sewnet.stages.chambers import ChamberPlacer, Labeller
from sewnet.stages.connectability import ConnectabilityStage
from sewnet.stages.hydraulic import HydraulicDesigner
from sewnet.stages.loads import LoadAllocator
from sewnet.stages.tree import TreeBuilder


class PlaneSampler:
    """Ground plane falling toward (0,0) at `gx` along x."""

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
    """Plane with a sharp 2 m ground dip near x=150 — the mid-span cover trap."""

    def z(self, x, y):
        base = super().z(x, y)
        return base - 2.0 if 145.0 <= x <= 155.0 else base


def straight_network(sampler, length=400.0, units_spec=((0, 3), (200, 2))):
    segs = [LineString([(0, 0), (length, 0)])]
    tb = TreeBuilder(sampler, C)
    Gu = tb.build_undirected(segs)
    tb.mark_arterials(Gu)
    outfall = key_of(0.0, 0.0)
    Gd, unreach = tb.build_tree(Gu, outfall)
    assert not unreach
    net = ChamberPlacer(sampler, C, round_spacing=False).run(Gd, outfall)
    Labeller.run(net)

    units, k = [], 0
    for x, cnt in units_spec:
        for _ in range(cnt):
            units.append(LoadUnit(id=f"u{k}", x=x, y=8.0, cls="B", src="plot"))
            k += 1
    alloc = LoadAllocator(C)
    per_chamber, _ = alloc.run(net, units)
    return net, units, per_chamber, outfall


# ---------------------------------------------------------------- loads
def test_accumulation_monotone_and_mass_balance():
    net, units, per_chamber, outfall = straight_network(PlaneSampler())
    G = net.digraph()
    chain, n = [], outfall
    while True:
        preds = list(G.predecessors(n))
        if not preds:
            break
        chain.append(G[preds[0]][n]["reach"])
        n = preds[0]
    chain.reverse()
    for a, b in zip(chain[:-1], chain[1:]):
        assert b.qadf_m3d >= a.qadf_m3d - 1e-9
    assert chain[-1].qadf_m3d == pytest.approx(5 * C.PLOT_QADF_M3D, rel=1e-6)


def test_every_unit_is_assigned():
    net, units, per_chamber, _ = straight_network(PlaneSampler())
    assert sum(len(v) for v in per_chamber.values()) == len(units)
    assert all(u.chamber is not None for u in units)


# ---------------------------------------------------------------- solver
def test_solver_basic_profile_is_audit_clean():
    s = PlaneSampler(gx=0.01)
    net, units, per_chamber, _ = straight_network(s)
    rep = HydraulicDesigner(s, C).run(net)
    assert rep["converged"]
    assert not rep["pockets"]
    for r in net.reaches:
        assert r.inv_up > r.inv_dn                                  # no reverse gradient
        assert r.slope >= H.smin_for(r.dn_mm, r.qpeak_m3s, C) * 0.999
        assert r.dn_mm >= C.DN_MIN_MAIN
    auditor = Auditor(C)
    auditor.run(net, units, per_chamber, s, {}, [])
    assert auditor.failures == [], [f.title for f in auditor.failures]


def test_solver_respects_midspan_dip():
    s = DipSampler(gx=0.01)
    net, units, per_chamber, _ = straight_network(s)
    HydraulicDesigner(s, C).run(net)
    for r in net.reaches:
        for ch, x, y, g in r.profile:
            cover = g - ((r.inv_up - r.slope * ch) + C.internal_diameter(r.dn_mm))
            assert cover >= C.MIN_COVER_CROWN - 0.02


def test_steep_terrain_caps_velocity_and_books_drops():
    s = PlaneSampler(gx=0.08)
    net, units, per_chamber, _ = straight_network(s, units_spec=((0, 2000), (200, 1000)))
    HydraulicDesigner(s, C).run(net)
    auditor = Auditor(C)
    auditor.run(net, units, per_chamber, s, {}, [])
    failed = {f.id for f in auditor.failures}
    assert "A4" not in failed, "velocity cap breached"
    assert "C3" not in failed, "drop bookkeeping wrong"
    total_drop = sum(d["height"] for c in net.chambers.values() for d in c.drops)
    assert total_drop > 0.5


def test_adverse_terrain_becomes_an_sls_pocket():
    s = PlaneSampler(gx=-0.05)                    # ground falls AWAY from the outfall
    net, units, per_chamber, _ = straight_network(s, length=400.0)
    rep = HydraulicDesigner(s, C).run(net)
    assert rep["n_failed_depth"] > 0
    assert rep["pockets"], "adverse terrain must produce an SLS pocket, not silence"


# ---------------------------------------------------------------- connectability
def test_low_plots_flagged_then_recovered_by_deepening():
    s = PlaneSampler(gx=0.01)
    net, units, per_chamber, _ = straight_network(s)
    designer = HydraulicDesigner(s, C)
    designer.run(net)

    class LowPlots(PlaneSampler):
        def z(self, x, y):
            return super().z(x, y) - (3.0 if y > 4.0 else 0.0)   # houses 3 m below the road

    stage = ConnectabilityStage(LowPlots(gx=0.01), C)
    per_chamber, _ = stage.attach(net, units)          # join each plot to the pipe it faces
    res, deepen = stage.check(net, per_chamber)
    assert any(not r["ok"] for r in res)
    assert deepen
    stage.apply_deepening(net, deepen)
    designer.run(net)
    still = stage.recheck(res, net, C)
    assert len(still) < sum(1 for r in res if not r["ok"]) or not still


def test_riders_group_at_most_three_connections():
    s = PlaneSampler()
    net, units, per_chamber, _ = straight_network(s, units_spec=((0, 7),))
    stage = ConnectabilityStage(s, C)
    per_chamber, _ = stage.attach(net, units)
    spurs, riders, stubs = stage.connections(net, per_chamber)
    assert len(spurs) + len(stubs) == 7            # every property gets its own spur
    assert all(r["n_units"] <= C.MAX_HCC_PER_RIDER for r in riders)


# ---------------------------------------------------------------- audit registry
def test_audit_registry_reports_every_check():
    s = PlaneSampler(gx=0.01)
    net, units, per_chamber, _ = straight_network(s)
    HydraulicDesigner(s, C).run(net)
    auditor = Auditor(C)
    results = auditor.run(net, units, per_chamber, s, {}, [])
    assert len(results) >= 20
    assert all(r.reference for r in results)      # every check cites its source
    assert all(r.status in ("PASS", "FAIL", "NOT_CHECKABLE") for r in results)
    assert "checks:" in auditor.table()


def test_start_year_flags_are_operational_not_failures():
    s = PlaneSampler(gx=0.01)
    net, units, per_chamber, _ = straight_network(s)
    HydraulicDesigner(s, C).run(net)
    flags = start_year_selfclean(net, per_chamber, C)
    for f in flags:
        assert "v_start" in f and "tractive_ok" in f
    stats = selfclean_stats(net, C)
    assert stats["pipes"] == len(net.reaches)
    assert "would_fail_at_tau2" in stats


def test_tau_sensitivity_is_a_config_change_not_a_code_edit():
    """The criteria object exists so GAP-9 can be tested without touching code."""
    from dataclasses import replace
    tau2 = replace(C, TAU_PA=2.0)
    assert H.smin_tractive(0.002, tau2) > H.smin_tractive(0.002, C)
    assert H.smin_tractive(0.002, tau2) / H.smin_tractive(0.002, C) == pytest.approx(
        2.0 ** 1.23, rel=0.01)
