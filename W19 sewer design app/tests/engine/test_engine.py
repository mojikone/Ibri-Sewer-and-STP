"""The in-process engine against W18: scalar oracle, guideline checks, and every pipe of all 12 cases."""
import json, math
import numpy as np, pytest
from sewerapp import fixtures
from sewerapp.engine import analysis, design, flows, hydraulics as h, peaking
from sewerapp.io import w18csv
from sewerapp.model.network import Network

CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]
NET = Network.from_w18(fixtures.read_csv("inputs/conduits_network.csv"), fixtures.read_csv("inputs/manholes_network.csv"))
LOADS = fixtures.read_csv("inputs/manhole_loads.csv", index_col="manhole_id")
CAT = fixtures.read_csv("inputs/catalogue.csv").sort_values("nominal_mm")
PK = peaking.PeakingTable(peaking.IBRI_PELTIER100_MERRIMACK)


# ---- W18's scalar functions (final_design.py lines 52-71), the oracle
def _section(D, y):
    th = 2 * math.acos(1 - 2 * y / D); A = D * D / 8 * (th - math.sin(th)); return A, A / (D * th / 2)


def _vcw(R, S):
    a = math.sqrt(8 * 9.81 * R * S); return -2 * a * math.log10(1.5e-3 / (14.8 * R) + 2.51 * 1.141e-6 / (4 * R * a))


def _normal(Q, D, S):
    if Q <= 0: return 0.0, 0.0
    lo, hi = 1e-6 * D, 0.999 * D
    for _ in range(50):
        y = (lo + hi) / 2; A, R = _section(D, y)
        if A * _vcw(R, S) > Q: hi = y
        else: lo = y
    y = (lo + hi) / 2; A, R = _section(D, y); return y / D, Q / A


def test_hydraulics_equal_w18_scalar():
    rng = np.random.default_rng(7)
    D = rng.choice([0.1764, 0.2206, 0.278, 0.4412, 0.7058, 1.0588, 1.4118], 2000); S = rng.uniform(5e-4, 0.02, 2000)
    Q = rng.uniform(0.0, 0.8, 2000) * h.q_capacity(D, S, 0.95)
    for r in (0.5, 0.65):
        np.testing.assert_allclose(h.q_capacity(D, S, r), [_vcw(_section(d, r * d)[1], s) * _section(d, r * d)[0] for d, s in zip(D, S)], rtol=1e-12)
    ratio, v = h.normal_depth(Q, D, S); ref = np.array([_normal(q, d, s) for q, d, s in zip(Q, D, S)])
    np.testing.assert_allclose(ratio, ref[:, 0], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(v, ref[:, 1], rtol=1e-9, atol=1e-12)


def test_peaking_table_is_peltier_then_merrimack():
    # G201 p72 Peltier to 1 L/s, G201 p71 Merrimack above; the table's step at 1.001 L/s
    assert PK.factor(1.0) == 2.5 and PK.factor(1.001) == 3.56
    for q, f in peaking.IBRI_PELTIER100_MERRIMACK:
        assert abs(f - (peaking.peltier(q) if q <= 1 else peaking.merrimack(q))) < 0.006, q


def test_network_is_a_tree():
    assert len(NET.pipes) == 19083 and NET.pipes.up.is_unique
    pos = np.empty(len(NET.order), int); pos[NET.order] = np.arange(len(NET.order))
    leaving = dict(zip(NET.pipes.up, NET.pipes.index))
    assert all(leaving.get(d) is None or pos[k] < pos[leaving[d]] for k, d in zip(NET.pipes.index, NET.pipes.dn))


def _case(case):
    y = int(case.split("-")[1])
    tr = fixtures.read_csv(f"golden/{case}/exports/transfers_{case}.csv")
    tr = tr[tr.year == y].groupby("receiver_id").flow_m3d.sum().to_dict()
    cut = set(np.flatnonzero(NET.pipes.label.isin(fixtures.read_csv(f"golden/{case}/split/cuts_{case}.csv")["pipe"]).values))
    gold = fixtures.read_csv(f"golden/{case}/exports/conduits_{case}a.csv").set_index("label").reindex(NET.pipes.label)
    return y, tr, cut, gold


@pytest.mark.gate_p1a
@pytest.mark.parametrize("case", CASES)
def test_flows_sizes_velocities_equal_w18(case):
    y, tr, cut, gold = _case(case)
    q, _ = flows.accumulate(NET, LOADS[f"Q_{y}"].to_dict(), tr, PK, 0.72, cut)
    np.testing.assert_allclose(q, gold.flow_m3d.values, rtol=1e-9)                          # flows
    slope_of = design.table11_slopes(NET, CAT.nominal_mm.values)
    start = w18csv.start_sizes(fixtures.path("inputs/conduits_start_sizes.csv"), NET.pipes.label)
    nom, passes = design.size_passes(q / 86400.0, start, CAT.nominal_mm.values, CAT.inside_mm.values / 1000.0, slope_of)
    expect = gold.size_label.str.extract(r"(\d+)")[0].astype(int).values
    assert (nom == expect).all(), f"{(nom != expect).sum()} pipes differ in size"           # sizes
    assert passes == json.load(open(fixtures.path(f"golden/{case}/design.json")))["passes"]
    a = analysis.analyse(q, gold.diameter_mm.values / 1000.0, np.array([slope_of[n] for n in nom]), nom)
    np.testing.assert_allclose(a.velocity_ms, gold.velocity_ms.values, rtol=1e-9, atol=1e-12)  # velocity
    assert not a.over_limit.any() and not a.over_3ms.any()
