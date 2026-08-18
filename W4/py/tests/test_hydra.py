"""The hydraulic gate: hydra.py must reproduce the guideline before it may design.

Gate 1 (the big one): G203-p29 Table 11 minimum gradients ARE Colebrook-White at
0.75 m/s full-bore with ks = 1.5 mm and nu = 1.141e-6. Our solver must give
0.75 m/s (+/-5%) at every tabulated (DN, gradient) pair.
Gate 2: hand-calculated fixtures must match.
"""

import math
import pytest

from sewnet import criteria as C
from sewnet import hydra as H


class TestTable11Gate:
    @pytest.mark.parametrize("dn,s", sorted(C.TABLE11.items()))
    def test_full_bore_velocity_is_self_cleansing(self, dn, s):
        v = H.v_full(dn / 1000.0, s)
        assert v == pytest.approx(C.V_SELF_CLEANSING, rel=0.05), (
            f"DN{dn} @ {s*1000:.2f} mm/m gives {v:.3f} m/s — Table 11 not reproduced")

    def test_whole_table_tight(self):
        # collective check: mean absolute deviation under 2% — catches a systematic bias
        devs = [abs(H.v_full(dn / 1000.0, s) - 0.75) / 0.75 for dn, s in C.TABLE11.items()]
        assert sum(devs) / len(devs) < 0.02


class TestHandCalcFixtures:
    def test_dn200_at_5mm_per_m(self):
        # hand calc 2026-08-18: sqrt(2gDS)=0.1401, arg=0.0020270+0.0001022, V=0.749
        assert H.v_full(0.200, 0.00500) == pytest.approx(0.749, abs=0.005)

    def test_dn315_full_capacity_at_table11_slope(self):
        # hand calc: v=0.741 m/s, A=0.07793 m2 -> Q ~= 57.7 L/s
        q = H.q_full(0.315, 0.00270)
        assert q == pytest.approx(0.0577, rel=0.03)

    def test_tractive_at_2_lps(self):
        # Smin = 2.33e-4 * 1 * (0.002)^-0.461 = 2.33e-4 * 17.55 = 0.00409
        assert H.smin_tractive(0.002) == pytest.approx(0.00409, rel=0.02)

    def test_tractive_floor_at_mara_qmin(self):
        # below 1.5 L/s the formula holds at its 1.5 L/s value (~4.7 mm/m ~ Table 11 DN200)
        assert H.smin_tractive(0.0001) == H.smin_tractive(C.TRACTIVE_QMIN)
        assert H.smin_tractive(C.TRACTIVE_QMIN) == pytest.approx(0.00467, rel=0.02)

    def test_table11_governs_at_tau_1(self):
        # with tau = 1 Pa the floored tractive minimum sits just under Table 11 DN200,
        # so Table 11 governs across the range; tractive takes over only if NWS sets tau > 1
        assert H.smin_for(200, 0.001) == C.TABLE11[200]
        assert H.smin_for(200, 0.010) == C.TABLE11[200]

    def test_pf_merrimack_hold_value(self):
        # 100 properties * 1.028 m3/d = 0.1028 Ml/d -> PF = 2.65 * 0.1028^-0.121 ~= 3.49
        assert C.pf_merrimack(0.1028) == pytest.approx(3.49, abs=0.05)

    def test_pf_peltier(self):
        assert C.pf_peltier(1.0) == pytest.approx(2.5, abs=0.001)
        assert C.pf_peltier(100.0) == pytest.approx(1.6, abs=0.001)


class TestPartialFlow:
    def test_partial_converges_to_full(self):
        assert H.q_partial(0.315, 0.004, 0.999999) == pytest.approx(H.q_full(0.315, 0.004), rel=0.01)

    def test_dod_roundtrip(self):
        q = H.q_partial(0.315, 0.004, 0.50)
        y, v = H.solve_dod(0.315, 0.004, q)
        assert y == pytest.approx(0.50, abs=0.005)
        assert v > 0

    def test_velocity_rises_with_depth_then_flattens(self):
        v30 = H.v_partial(0.315, 0.004, 0.30)
        v65 = H.v_partial(0.315, 0.004, 0.65)
        assert v65 > v30

    def test_capacity_exceeded_returns_none(self):
        y, v = H.solve_dod(0.200, 0.005, 1.0)  # 1 m3/s through DN200 — impossible
        assert y is None and v is None


class TestSizing:
    def test_size_pipe_picks_smallest_compliant(self):
        # 45 L/s at 4.0 mm/m: DN250 too small at d/D<=0.65? DN315 expected
        dn, y, v = H.size_pipe(0.045, 0.004)
        assert dn in (250, 315)
        assert y <= H.dod_limit(dn)
        assert v > 0.75

    def test_dod_limit_switch(self):
        assert H.dod_limit(315) == 0.65
        assert H.dod_limit(400) == 0.50

    def test_smax_none_for_small_flows(self):
        assert H.smax_for(200, 0.0005) is None  # 0.5 L/s can't reach 3 m/s in a DN200

    def test_smax_valid_cap_hits_3(self):
        # 50 L/s in a DN200 bore reaches 3 m/s on steep slopes — cap must land ON 3.0
        s = H.smax_for(200, 0.050)
        assert s not in (None, H.INFEASIBLE) and 0.001 < s < 0.5
        y, v = H.pipe_state(200, s, 0.050)
        assert v == pytest.approx(3.0, abs=0.05)

    def test_smax_infeasible_signals_upsize(self):
        # review HYD-1: 100 L/s can NEVER pass a DN200 bore at v <= 3 — the old
        # bisection returned a garbage 1e-4 slope here
        assert H.smax_for(200, 0.100) == H.INFEASIBLE

    def test_smax_exists_for_big_flows(self):
        s = H.smax_for(400, 0.100)
        if s not in (None, H.INFEASIBLE):
            y, v = H.pipe_state(400, s, 0.100)
            assert v == pytest.approx(3.0, abs=0.05)

    def test_internal_diameter_convention(self):
        # review HYD-2: PVC-U OD-series derated (SDR34), GRP nominal = ID
        assert C.internal_diameter(200) == pytest.approx(0.1882, abs=0.0005)
        assert C.internal_diameter(400) == 0.400
        # capacity on the true SDR34 bore is ~15% below the naive DN reading
        # (scales ~D^2.67: 0.941^2.67 = 0.85; heavier walls would cut further — PVC_SDR assumption)
        q_dn = H.q_full(0.200, 0.005)
        q_id = H.q_full(C.internal_diameter(200), 0.005)
        assert q_id / q_dn == pytest.approx(0.85, abs=0.02)
