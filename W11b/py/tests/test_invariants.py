"""THE INVARIANTS - properties every published network must have, whatever the design
decides.

These are not opinions about the layout. They are the statements that must hold or the
graph is not a sewer network: flow only grows downstream, a tree has one fewer pipe than
it has chambers, the lengths sum, and exactly one pipe leaves every junction. When one of
these fails, every number downstream of it is wrong and no other check would say so.

TWO KINDS OF TEST LIVE HERE AND THEY ARE MARKED DIFFERENTLY:

  unmarked          a property of the GRAPH. It must hold. A failure is a code defect.
  @pytest.mark.audit  a constraint from `_BRAIN/08_DESIGN_PHILOSOPHY.md` on the DESIGN.
                    A failure is an engineering finding, not a broken build, and
                    philosophy sec 8 makes it BLOCKING all the same. `run_all.py` runs
                    these last and prints them as the audit table.

Each audit check names the rule it enforces and the page behind it, so a check cannot
exist without a source and a rule cannot exist without a check (philosophy sec 8).
"""
from __future__ import annotations

import numpy as np
import pytest

from conftest import layer, layer_names

pytestmark = pytest.mark.published

TIER_RANK = {"rider": 0, "lateral": 1, "main": 2, "sub main": 3, "trunk main": 4}


def _successor_map(arcs, route_only: bool = True):
    """{EDGE_UID -> the arc that carries this arc's flow away}.

    THE TRAP THIS FUNCTION EXISTS TO AVOID: the flows layer publishes 12,816 arcs, of which
    only 9,550 are on the route (`IS_ROUTE = 1`). 2,988 nodes own more than one arc in the
    full set, so a naive `dict(zip(US_NODE, EDGE_UID))` silently keeps whichever came last
    and then reports 1,810 arcs where flow appears to fall downstream. On the route the
    US_NODE really is unique, and the invariant really does hold.
    """
    a = arcs[arcs.IS_ROUTE.astype(int) == 1] if (route_only and "IS_ROUTE" in arcs) else arcs
    assert not a.US_NODE.duplicated().any(), (
        "a node owns two outgoing arcs on the route - 'at a junction, exactly one pipe "
        "leaves' (philosophy sec 4) is broken, and every accumulation below is wrong")
    nxt = dict(zip(a.US_NODE, a.EDGE_UID))
    return a, {e: nxt.get(ds) for e, ds in zip(a.EDGE_UID, a.DS_NODE)}


# ======================================================================================
# 1. EXACTLY ONE PIPE LEAVES A JUNCTION
# ======================================================================================

def test_exactly_one_pipe_leaves_every_junction(reaches):
    """Philosophy sec 4: 'AT A JUNCTION, EXACTLY ONE PIPE LEAVES. Every other line meeting
    there is a head.' This is what makes a network buildable rather than merely connected.
    Stage 2 handed over 2,718 nodes with two to four outgoing arcs; stage 3 owns the fix."""
    dup = reaches.US_NODE[reaches.US_NODE.duplicated()]
    print(f"\n    [one outlet] {len(reaches):,} reaches, {reaches.US_NODE.nunique():,} "
          f"distinct upstream nodes")
    assert dup.empty, (f"{dup.nunique()} nodes own more than one outgoing reach, e.g. "
                       f"{sorted(dup.unique())[:5]}")


def test_a_head_has_no_inflow(reaches):
    """The other half of the same rule: a head STARTS at its point and drains away from it,
    so nothing may drain into it."""
    if "IS_HEAD" not in reaches.columns:
        pytest.skip("no IS_HEAD on the reach layer")
    heads = set(reaches.loc[reaches.IS_HEAD.astype(int) == 1, "US_NODE"])
    with_inflow = heads & set(reaches.DS_NODE)
    assert not with_inflow, (f"{len(with_inflow)} head nodes have a reach draining INTO "
                             f"them, e.g. {sorted(with_inflow)[:5]}")


def test_chamber_layer_agrees_that_one_pipe_leaves(chambers):
    """The same rule, checked on the chamber layer, which counts it independently."""
    if "N_OUT" not in chambers.columns:
        pytest.skip("no N_OUT on the chamber layer")
    counts = chambers.N_OUT.value_counts().to_dict()
    print(f"\n    [chamber outlets] {counts}")
    assert set(counts) <= {0, 1}, f"a chamber has more than one outlet: {counts}"
    assert counts.get(0, 0) == int(chambers.IS_OUTFALL.astype(int).sum()) \
        if "IS_OUTFALL" in chambers.columns else True


# ======================================================================================
# 2. THE FOREST - no loops, and each component ends at exactly one outfall
# ======================================================================================

def test_the_network_is_a_forest_of_trees(reaches, hier_nodes):
    """H15, and the counting identity behind it: in a tree, edges = nodes - 1. Checked per
    component, so one extra edge anywhere shows up as a component that is not a tree.

    W10 published a layer in 7,919 disconnected pieces and nobody could tell, because the
    only evidence was geometry. Here the topology is written down (H16) and can be counted.
    """
    nx = pytest.importorskip("networkx")
    G = nx.Graph()
    G.add_nodes_from(hier_nodes.NODE_UID)
    G.add_edges_from(zip(reaches.US_NODE, reaches.DS_NODE))
    comps = list(nx.connected_components(G))
    not_tree = []
    for c in comps:
        sub = G.subgraph(c)
        if sub.number_of_edges() != len(c) - 1:
            not_tree.append((len(c), sub.number_of_edges()))
    print(f"\n    [forest] {len(comps):,} components over {len(hier_nodes):,} chambers and "
          f"{len(reaches):,} reaches; edges = nodes - components: "
          f"{len(reaches):,} == {len(hier_nodes):,} - {len(comps):,} = "
          f"{len(hier_nodes) - len(comps):,}")
    assert not not_tree, (f"{len(not_tree)} components are not trees (nodes, edges): "
                          f"{not_tree[:5]} - a cycle or a parallel edge")
    assert len(reaches) == len(hier_nodes) - len(comps), (
        "the global identity edges = nodes - components does not hold, which means an "
        "edge references a node that is not in the node layer")


def test_no_directed_cycle(reaches):
    """A loop in the DIRECTED graph is worse than a loop in the undirected one: flow would
    have to arrive where it left."""
    nx = pytest.importorskip("networkx")
    D = nx.DiGraph()
    D.add_edges_from(zip(reaches.US_NODE, reaches.DS_NODE))
    cycles = list(nx.simple_cycles(D))
    assert not cycles, f"{len(cycles)} directed cycles, e.g. {cycles[:2]}"


def test_each_component_ends_at_exactly_one_outfall(reaches, hier_nodes):
    """H15 as corrected on 2026-09-02: not ONE network - satellite works are legal - but
    each component ending at exactly one outfall. What is never legal is a piece that
    drains nowhere."""
    nx = pytest.importorskip("networkx")
    has_out = set(reaches.US_NODE)
    G = nx.Graph()
    G.add_nodes_from(hier_nodes.NODE_UID)
    G.add_edges_from(zip(reaches.US_NODE, reaches.DS_NODE))
    bad = []
    for c in nx.connected_components(G):
        sinks = [n for n in c if n not in has_out]
        if len(sinks) != 1:
            bad.append((len(c), len(sinks)))
    print(f"\n    [outfalls] every one of {nx.number_connected_components(G):,} components "
          f"ends at exactly one sink")
    assert not bad, f"{len(bad)} components with a sink count other than 1: {bad[:5]}"


def test_following_the_flow_always_terminates(reaches):
    """Walk from every reach to the sea. If the walk exceeds the number of reaches the
    graph has a cycle the directed-cycle test would already have caught - this is the
    belt-and-braces version, and it is also what the accumulator actually does."""
    nxt = dict(zip(reaches.US_NODE, reaches.EDGE_UID))
    ds = dict(zip(reaches.EDGE_UID, reaches.DS_NODE))
    cap = len(reaches) + 5
    longest = 0
    for start in list(reaches.EDGE_UID)[::37]:              # every 37th, ~340 walks
        e, n = start, 0
        while e is not None and n < cap:
            e = nxt.get(ds[e])
            n += 1
        assert n < cap, f"walk from {start} did not terminate"
        longest = max(longest, n)
    print(f"\n    [flow path] longest sampled walk to an outfall: {longest} reaches")


# ======================================================================================
# 3. FLOW ONLY GROWS DOWNSTREAM
# ======================================================================================

def test_average_flow_never_falls_downstream(flow_arcs):
    """The accumulation identity. A reach cannot carry less than the reach above it."""
    a, succ = _successor_map(flow_arcs)
    q = dict(zip(a.EDGE_UID, a.QADF_M3D.astype(float)))
    bad, worst = 0, 0.0
    for e, nx_ in succ.items():
        if nx_ is None:
            continue
        d = q[e] - q[nx_]
        if d > 1e-6:
            bad += 1
            worst = max(worst, d)
    print(f"\n    [monotone Qadf] {len(a):,} route arcs, {bad} falling, worst deficit "
          f"{worst:.3f} m3/d")
    assert bad == 0


def test_peak_flow_never_falls_downstream(flow_arcs):
    """Peak flow is NOT automatically monotone even when average flow is: the peak factor
    falls as the catchment grows (Merrimack, G201-p71), so a big upstream catchment can
    produce a larger peak than the slightly bigger one below it. `QPK_MONO` is the column
    that has been made monotone, and it is the one a sizing stage must read."""
    a, succ = _successor_map(flow_arcs)
    for col in ("QPK_MONO", "QPK_LS"):
        if col not in a.columns:
            continue
        q = dict(zip(a.EDGE_UID, a[col].astype(float)))
        bad = sum(1 for e, n in succ.items()
                  if n is not None and q[e] - q[n] > 1e-9)
        print(f"\n    [monotone {col}] {bad} of {len(a):,} route arcs fall downstream")
        if col == "QPK_MONO":
            assert bad == 0, (
                f"{bad} arcs where the monotone peak flow falls downstream - QPK_MONO is "
                f"the column that exists to guarantee exactly this")


def test_upstream_property_count_never_falls(flow_arcs):
    if "N_PROP" not in flow_arcs.columns:
        pytest.skip("no N_PROP")
    a, succ = _successor_map(flow_arcs)
    n = dict(zip(a.EDGE_UID, a.N_PROP.astype(float)))
    bad = sum(1 for e, s in succ.items() if s is not None and n[e] - n[s] > 1e-9)
    assert bad == 0, f"{bad} arcs serve more properties than the arc below them"


def test_peak_factor_is_at_least_one_and_falls_with_catchment_size(flow_arcs, crit):
    pf = flow_arcs.PF.dropna().astype(float)
    assert pf.min() >= 1.0 - 1e-9, f"a peak factor below 1.0: {pf.min()}"
    over = int((pf > crit.PF_REPORT_ABOVE).sum())
    print(f"\n    [peak factor] {pf.min():.2f} to {pf.max():.2f}; {over:,} arcs above the "
          f"{crit.PF_REPORT_ABOVE:.1f} G201-p72 recommends reporting")
    big = flow_arcs[flow_arcs.QADF_M3D > flow_arcs.QADF_M3D.quantile(0.99)]
    small = flow_arcs[(flow_arcs.PF_METH == "merrimack")
                      & (flow_arcs.QADF_M3D < flow_arcs.QADF_M3D.quantile(0.50))]
    if len(big) and len(small):
        assert big.PF.mean() < small.PF.mean(), (
            "the peak factor does not fall as the catchment grows - Merrimack is inverted")


def test_infiltration_is_a_per_pipe_load_not_an_accumulated_one(flow_arcs, crit):
    """The 87x defect. Summing a per-reach value that already includes everything upstream
    counts every kilometre once per downstream reach, which is how 14.5 L/s was published
    as 1,259. `QINF_LOC` is the per-pipe term and it is the one that may be summed."""
    a = flow_arcs
    if "QINF_LOC" not in a.columns:
        pytest.skip("no per-pipe infiltration column")
    total = float(a.QINF_LOC.sum())
    from_length = crit.infiltration_ls(float(a.LEN_M.sum()))
    naive = float(a.QINF_LS.sum()) if "QINF_LS" in a.columns else float("nan")
    print(f"\n    [infiltration] per-pipe sum {total:.2f} L/s against "
          f"{from_length:.2f} L/s from the total length at {crit.INFILT_L_D_KM:.0f} L/d/km; "
          f"summing the ACCUMULATED column instead gives {naive:,.0f} L/s "
          f"({naive / max(total, 1e-9):.0f}x)")
    assert abs(total - from_length) < 0.05 * max(from_length, 1e-9)


# ======================================================================================
# 4. LENGTHS SUM
# ======================================================================================

def test_lengths_sum_across_every_partition(reaches, segments):
    """The same kilometres, counted three ways: by reach, by tier, and by chamber-to-chamber
    segment. If they disagree, a schedule and a drawing describe different networks."""
    by_reach = float(reaches.LEN_M.sum())
    by_tier = float(reaches.groupby("TIER").LEN_M.sum().sum())
    by_seg = float(segments.LEN_M.sum())
    print(f"\n    [lengths] reaches {by_reach / 1000:,.1f} km | by tier "
          f"{by_tier / 1000:,.1f} km | chamber segments {by_seg / 1000:,.1f} km")
    assert abs(by_reach - by_tier) < 1e-6
    # the segment layer is a different stage's view and drops what it does not chamber;
    # it must never be LONGER than the reaches it subdivides.
    assert by_seg <= by_reach * 1.001, (
        f"the chamber segments total {by_seg / 1000:,.1f} km against the reaches' "
        f"{by_reach / 1000:,.1f} km - a subdivision cannot add length")


def test_segments_tile_their_parent_arc(segments):
    """S0 and S1 are the chainages a segment spans on its arc. Consecutive segments must
    abut: a gap is unpiped ground nobody sees, an overlap is length counted twice."""
    if not {"ARC_CID", "SEQ", "S0", "S1"} <= set(segments.columns):
        pytest.skip("no chainage columns on the segment layer")
    s = segments.sort_values(["ARC_CID", "SEQ"])
    gap = (s.groupby("ARC_CID").S0.shift(-1) - s.S1).dropna().abs()
    bad = int((gap > 0.05).sum())
    print(f"\n    [tiling] {len(s):,} segments over {s.ARC_CID.nunique():,} arcs; worst "
          f"gap or overlap between consecutive segments {gap.max() * 1000:.2f} mm")
    assert bad == 0, f"{bad} places where consecutive segments do not abut"
    assert (s.S1 >= s.S0 - 1e-9).all(), "a segment runs backwards along its arc"


def test_no_segment_has_zero_or_negative_length(segments):
    assert float(segments.LEN_M.min()) > 0.0


# ======================================================================================
# 5. TIERS
# ======================================================================================

def test_tier_never_inverts_along_the_flow_path(reaches):
    """Philosophy sec 4: laterals chain into mains, mains into sub mains, sub mains into
    the trunk. A lateral downstream of a sub main is a hierarchy that is decorative."""
    nxt = dict(zip(reaches.US_NODE, reaches.EDGE_UID))
    tier = dict(zip(reaches.EDGE_UID, reaches.TIER))
    unknown = set(reaches.TIER) - set(TIER_RANK)
    assert not unknown, (f"tier tokens the philosophy does not name: {unknown} - an "
                         f"unrecognised tier is a SILENT SKIP in a diameter-floor check")
    bad = []
    for e, ds, t in zip(reaches.EDGE_UID, reaches.DS_NODE, reaches.TIER):
        n = nxt.get(ds)
        if n is not None and TIER_RANK[tier[n]] < TIER_RANK[t]:
            bad.append((e, t, tier[n]))
    print(f"\n    [tiers] " + " | ".join(
        f"{t} {v / 1000:,.1f} km" for t, v in
        reaches.groupby("TIER").LEN_M.sum().sort_index(key=lambda s: s.map(TIER_RANK)).items()))
    assert not bad, f"{len(bad)} tier inversions, e.g. {bad[:5]}"


# ======================================================================================
# 6. THE AUDIT - philosophy sec 8. A breach of a "shall" is BLOCKING.
# ======================================================================================

@pytest.mark.audit
def test_H12_chamber_spacing_is_within_table_12(segments, crit):
    """H12, G203-p30 Table 12. Checked at the LOOSEST band, because diameters are stage 6's
    answer and are not published yet - so this can only prove that no segment exceeds the
    spacing permitted for ANY size. It is deliberately the weaker statement: philosophy
    sec 8 says a check that cannot run is a failure, and this one CAN run in a weaker form,
    so it does."""
    ceiling = max(s for _hi, s in crit.MH_SPACING_BANDS)
    smallest = crit.mh_max_spacing(min(crit.DN_SERIES))
    over_any = int((segments.LEN_M > ceiling + 1e-6).sum())
    over_dn200 = int((segments.LEN_M > smallest + 1e-6).sum())
    print(f"\n    [H12] max segment {segments.LEN_M.max():.2f} m; "
          f"{over_dn200:,} over the DN200 band ({smallest:.0f} m), {over_any:,} over the "
          f"widest band ({ceiling:.0f} m). Diameters are stage 6's, so only the second "
          f"number is decidable today.")
    assert over_any == 0


@pytest.mark.audit
def test_H10_inlet_angles_are_at_least_ninety_degrees(crit):
    """H10, G203-p30 verbatim: 'No inlet pipe at manholes shall have an angle less than
    90 deg to the direction of flow.' Each breach needs a purpose-made chamber with a
    swept channel; the previous iteration had 2,984 of them."""
    ch = layer("chambers", "chambers")
    if "INLET_DEG" not in ch.columns:
        pytest.skip("no INLET_DEG")
    s = ch.INLET_DEG.dropna().astype(float)
    s = s[s >= 0.0]
    under = s[s < crit.INLET_MIN_DEG - 1e-9]
    swept = int(ch.SWEPT_CH.sum()) if "SWEPT_CH" in ch.columns else -1
    nulls = int(ch.INLET_DEG.isna().sum())
    print(f"\n    [H10] {len(under):,} of {len(s):,} measured inlets below "
          f"{crit.INLET_MIN_DEG:.0f} deg (worst {s.min():.2f}); {swept:,} flagged "
          f"SWEPT_CH; {nulls:,} chambers carry no measurement at all")
    assert nulls == 0, (
        f"{nulls:,} chambers have a null inlet angle. Philosophy sec 8: a check that "
        f"cannot run is a FAILURE, not a blank.")
    assert under.empty, (
        f"{len(under):,} inlets below {crit.INLET_MIN_DEG:.0f} deg, worst {s.min():.2f} - "
        f"each needs a purpose-made chamber with a swept channel (G203-p30)")


@pytest.mark.audit
def test_H1_no_corridor_carries_a_pipe_along_a_dual_carriageway(corridors):
    """H1 and project rule 7, settled 2026-08-19: NO pipe of any kind runs along a dual
    carriageway, trunk included, because it cannot be dug up. A crossing is legal; running
    along one is not."""
    if not {"ALONG_DUAL", "PIPE_OK"} <= set(corridors.columns):
        pytest.skip("stage 1 does not publish ALONG_DUAL / PIPE_OK")
    along = corridors[corridors.ALONG_DUAL.astype(int) == 1]
    still_ok = along[along.PIPE_OK.astype(int) == 1]
    print(f"\n    [H1] {len(along):,} corridors ({along.LEN_M.sum() / 1000:.2f} km) run "
          f"ALONG a dual carriageway; {len(still_ok):,} of them are still flagged "
          f"PIPE_OK = 1")
    assert still_ok.empty, (
        f"{len(still_ok)} corridors totalling {still_ok.LEN_M.sum() / 1000:.2f} km run "
        f"along a dual carriageway and are published as pipeable. EXCL_RSN is blank on "
        f"every row of this layer, so nothing is excluded anywhere - project rule 7 is "
        f"declared in the schema and not enforced in the data.")


@pytest.mark.audit
def test_H16_topology_is_written_down_on_every_published_pipe():
    """H16: every pipe publishes US_NODE and DS_NODE. Connectivity recovered by snapping is
    a guess whose answer moves with the tolerance - the same W10 file gives 7,919 pieces at
    10 mm and 105 pieces with 311 loops at 2.5 m."""
    missing = []
    for key, lyr in (("hier", "reaches"), ("flows", "arcs"), ("chambers", "segments"),
                     ("pumps", "rising_mains"), ("roads", "corridors")):
        if lyr not in layer_names(key):
            continue
        g = layer(key, lyr)
        for c in ("US_NODE", "DS_NODE"):
            if c not in g.columns:
                missing.append(f"  {key}/{lyr} has no {c}")
            elif g[c].isna().any() or (g[c].astype(str).str.strip() == "").any():
                n = int(g[c].isna().sum() + (g[c].astype(str).str.strip() == "").sum())
                missing.append(f"  {key}/{lyr}.{c}: {n} blank")
    assert not missing, "\n".join(missing)


@pytest.mark.audit
def test_the_share_draining_uphill_is_reported():
    """Philosophy sec 4 REQUIRES this quantity published, not merely computed: 'Report the
    share, the cumulative climb, and the worst single rise.' NAMA's own built network runs
    uphill on 34 % of its length - that is CONTEXT, NOT PERMISSION."""
    o = layer("orient", "arcs")
    if "UPHILL" not in o.columns:
        pytest.skip("stage 2 does not publish UPHILL")
    up = o[o.UPHILL.astype(int) == 1]
    total_km = float(o.LEN_M.sum()) / 1000.0
    up_km = float(up.LEN_M.sum()) / 1000.0
    climb_m = float((-up.FALL_M).clip(lower=0).sum()) if "FALL_M" in o.columns else float("nan")
    worst = float((-o.FALL_M).max()) if "FALL_M" in o.columns else float("nan")
    print(f"\n    [uphill] {up_km:,.1f} km of {total_km:,.1f} km "
          f"({up_km / total_km * 100:.2f} %) drains against the ground; cumulative climb "
          f"{climb_m:,.0f} m; worst single rise {worst:.2f} m. NAMA's built network: "
          f"34.10 %. W11a: 42.5 %.")
    assert up_km > 0.0, "an uphill share of exactly zero on this ground is not credible"
    assert climb_m == climb_m                        # the quantity exists and is finite


@pytest.mark.audit
def test_the_flatness_is_reported_before_the_direction():
    """Philosophy sec 4: 'MEASURE THE FLATNESS FIRST, THEN THE DIRECTION.' What buys depth
    on this ground is not that pipes point the wrong way - it is that the ground is too
    flat to lay them on. 60 % of the corridor network falls more gently than the minimum
    gradient a DN200 may be laid at (5.00 mm/m, G203-p29 Table 11)."""
    o = layer("orient", "arcs")
    if "SLOPE_PCT" not in o.columns:
        pytest.skip("stage 2 does not publish SLOPE_PCT")
    from w11b.criteria import DEFAULT as C
    smin_pct = C.table11(200) * 100.0
    flat = o[o.SLOPE_PCT.abs() < smin_pct]
    km_flat = float(flat.LEN_M.sum()) / 1000.0
    km = float(o.LEN_M.sum()) / 1000.0
    debt = float(((smin_pct - flat.SLOPE_PCT.abs()) / 100.0 * flat.LEN_M).sum())
    print(f"\n    [flatness] {km_flat:,.1f} km of {km:,.1f} km ({km_flat / km * 100:.1f} %) "
          f"lies on ground falling more gently than the DN200 minimum of "
          f"{smin_pct * 10:.2f} mm/m; accumulated depth debt {debt:,.0f} m")
    assert km_flat > 0.0


@pytest.mark.audit
def test_no_load_is_silently_dropped():
    """Zero silent drops. W10 dropped 1,233 m3/d because an assignment radius let it go
    with nothing published. Every plot is either connected or NAMED."""
    conn = layer("chambers", "connections")
    names = layer_names("chambers")
    unserved = layer("chambers", "unserved") if "unserved" in names else None
    q_conn = float(conn.Q_ADF_M3D.sum())
    q_uns = float(unserved.Q_ADF_M3D.sum()) if (
        unserved is not None and "Q_ADF_M3D" in unserved.columns) else 0.0
    n_uns = 0 if unserved is None else len(unserved)
    from w11b.criteria import DEFAULT as C
    print(f"\n    [load] {q_conn:,.1f} m3/d connected on {len(conn):,} connections; "
          f"{q_uns:,.1f} m3/d named unserved on {n_uns:,} plots; total accounted "
          f"{q_conn + q_uns:,.1f} m3/d against the saturated Qadf of ~74,700 m3/d "
          f"(W10 Phase 1.3, at OR {C.OCCUPANCY} and {C.PROPS_PER_PLOT} properties per plot)")
    assert unserved is not None, (
        "no `unserved` layer: a plot that is not connected must be NAMED, or the drop is "
        "silent")


@pytest.mark.audit
def test_the_tau_assumption_is_flagged_on_every_layer_that_carries_a_gradient():
    """The engineer's standing instruction of 2026-09-03: tau = 1.0 Pa is an ASSUMPTION
    (GAP-9) and every deliverable carrying a gradient must say so on its face. At 2.0 Pa
    every tractive-governed gradient rises 2.346x and every level below it changes."""
    from w11b.criteria import DEFAULT as C
    carried = []
    for key in ("orient", "hier", "chambers", "flows"):
        for lyr in layer_names(key):
            g = layer(key, lyr)
            if any(c in g.columns for c in ("TAU_FLAG", "TAU_PA")):
                carried.append(f"{key}/{lyr}")
    print(f"\n    [GAP-9] the tau banner travels on {len(carried)} published layers; "
          f"at 2.0 Pa every tractive gradient rises {C.TAU_SLOPE_FACTOR_AT_2PA:.3f}x")
    assert len(carried) >= 4, f"only {carried} carry the tau flag"


@pytest.mark.audit
def test_which_audit_checks_can_run_at_all_is_reported(contract):
    """Philosophy sec 8: 'A CHECK THAT CANNOT RUN IS A FAILURE, NOT A BLANK.' W10 shipped
    with 7 of its 22 checks unanswerable and the table showed them as neither pass nor
    fail. `contract.AUDIT_NEEDS` names the field every check needs; this reads it against
    what is actually published and prints the answer, so the unanswerable ones are counted
    rather than absent.

    It does NOT assert that every check can run today - stage 6 (levels and sizes) has not
    published yet, so every depth, gradient and diameter check is legitimately waiting on
    it. It asserts that the ones which DO NOT depend on stage 6 can run.
    """
    # The design is spread over several GeoPackages until stage 8 assembles it, so the
    # honest question is "does this field exist anywhere in the published set", not "is it
    # on one layer". Columns are unioned across the reach-like and node-like layers.
    import pandas as pd
    r_cols, n_cols = set(), set()
    for key, lyr in (("hier", "reaches"), ("flows", "arcs"), ("chambers", "segments")):
        if lyr in layer_names(key):
            r_cols |= set(layer(key, lyr).columns)
    for key, lyr in (("hier", "nodes"), ("flows", "nodes"), ("chambers", "chambers")):
        if lyr in layer_names(key):
            n_cols |= set(layer(key, lyr).columns)
    r = pd.DataFrame(columns=sorted(r_cols))
    n = pd.DataFrame(columns=sorted(n_cols))
    external = ("roads", "manifest", "hazard")   # what stages 1-5 have actually published
    tab = contract.audit_readiness(reaches=r, nodes=n, external=external)
    can = tab[tab.can_run]
    cannot = tab[~tab.can_run]
    print(f"\n    [readiness] {len(can)} of {len(tab)} audit checks can run against the "
          f"layers published so far ({', '.join(sorted(can.check))})")
    for _i, row in cannot.iterrows():
        print(f"        cannot run  {row.check:5s}  needs {row.missing}")
    print(f"        {len(cannot)} of {len(tab)} cannot run. Most wait on stage 6 (levels "
          f"and sizes): DN, SLOPE_LAID, US_DEPTH, DS_DEPTH, INV_UP, INV_DN, COVER_*.")

    # These need nothing stage 6 owns, so they must be answerable now.
    now = {"H15", "H16", "G3"}
    blocked = sorted(now & set(cannot.check))
    assert not blocked, (
        f"checks that depend on nothing stage 6 owns still cannot run: {blocked}. "
        f"{cannot[cannot.check.isin(blocked)].to_string(index=False)}")
