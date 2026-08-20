"""SewerDesignPipeline — the stages in order, with the reports they produce.

Each stage is a class in sewnet/stages/ with one job; this file is only the composition,
so "where do I change X" is answered by the stage name:

    inputs        prep.prepare        boundary repair, clip, node, dual collapse, terrain
    RoadTreatment road_treatment      raw centrelines -> reviewable sewer corridors
    TreeBuilder   tree                loop-free collection tree to the outfall
    ChamberPlacer chambers            chambers + reaches, rounded spacing
    StructureResolver structures      one physical outlet per structure
    LoadAllocator loads               saturation loads, assignment, accumulation
    HydraulicDesigner hydraulic       diameters and inverts (coupled)
    ConnectabilityStage connectability house connections, chamber deepening
    Auditor       audit               independent re-check of every rule
"""

import networkx as nx
import math
from dataclasses import dataclass, field
from typing import Optional

from . import prep
from .criteria import DEFAULT
from .model import Network
from .stages.audit import Auditor, selfclean_stats, start_year_selfclean
from .stages.chambers import ChamberPlacer, Labeller
from .stages.connectability import ConnectabilityStage
from .stages.hydraulic import HydraulicDesigner
from .stages.loads import LoadAllocator
from .stages.road_treatment import RoadTreatment
from .stages.structures import StructureResolver
from .stages.tree import TreeBuilder
from .stages.trunk import MainPipe, attach_to_roads, tree_to_trunk


@dataclass
class RunConfig:
    roads: str
    plots: str
    unparceled: str
    boundary: str
    terrain: str
    outfall_expected: Optional[tuple] = None
    outfall_override: Optional[tuple] = None
    pf_formula: str = "merrimack"
    clip_sliver_m: float = 0.5
    dual_merge_m: float = 35.0
    # feature switches — off reproduces the pre-refactor design exactly (equality gate)
    main_pipe: str = ""                      # the drawn trunk (user 2026-08-20)
    confluence: tuple = ()                   # where its legs meet = the outfall
    main_pipe_lead_m: float = 1200.0
    trunk_dn_seed: int = 400                 # first guess at trunk size, refined by the solver
    underpasses: tuple = ()                  # crossings here need no trenchless work
    max_trunk_joins: Optional[int] = None    # cap on joins onto the main pipe (None = all)
    trunk_sides: tuple = ("west", "south")   # superseded, kept so old configs still load
    use_trunk: bool = True
    reroute_passes: int = 6      # try again round deep spots before accepting a pump
    treat_roads: bool = True
    round_spacing: bool = True
    corridors_out: Optional[str] = None      # where RoadTreatment writes its review layer
    hazard: Optional[str] = None             # 50-year flood grid
    accounts: Optional[str] = None           # electricity accounts = counted properties


class SewerDesignPipeline:
    def __init__(self, cfg: RunConfig, crit=DEFAULT, log=print):
        self.cfg = cfg
        self.crit = crit
        self.log = log
        self.reports = {}

    def _station_report(self, hyd):
        """Rule 9 read-out: the stations as designed, which sit close enough to feed one
        another, and which are small enough that detail design may absorb them."""
        C = self.crit
        sl = hyd["station_list"]
        pairs = []
        for i, a in enumerate(sl):
            for b in sl[i + 1:]:
                d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                if d <= C.SLS_CASCADE_M:
                    pairs.append({"a": a["label"], "b": b["label"], "apart_m": round(d)})
        self.reports["stations"] = {
            "count": len(sl), "list": sl,
            "properties_pumped": round(sum(s["n_props"] for s in sl)),
            "total_lift_m": round(sum(s["lift_m"] for s in sl), 1),
            "rising_main_m": round(sum(s["rising_main_m"] for s in sl), 1),
            "small_enough_to_absorb": [s["label"] for s in sl
                                       if s["n_props"] < C.SLS_MIN_PLOTS],
            "close_enough_to_cascade": pairs}
        return self.reports["stations"]

    def run(self):
        cfg, C = self.cfg, self.crit

        self.log("S1 inputs: boundary, roads, terrain, flood grid ...")
        segs, attrs, boundary, sampler, hazard, s1 = prep.prepare(
            cfg.roads, cfg.boundary, cfg.terrain, cfg.clip_sliver_m, cfg.dual_merge_m,
            hazard_path=cfg.hazard,
                                    terrain_pad=200.0 + cfg.main_pipe_lead_m)
        self.hazard = hazard
        self.reports["inputs"] = s1
        self.log(f"   {s1['boundary_ha']:.1f} ha, {s1['segs_raw']} road lines, "
                 f"{s1['len_km']:.1f} km (dual carriageway {s1['dual_1']}, "
                 f"two-lane {s1['dual_2']})")

        self.log("S4a properties (plots + counted electricity accounts) ...")
        alloc = LoadAllocator(C, cfg.pf_formula)
        units, lstats = alloc.load_units(cfg.plots, cfg.unparceled, boundary,
                                         accounts_path=cfg.accounts)
        self.reports["loads"] = lstats
        self.log(f"   {lstats}")

        if cfg.treat_roads:
            self.log("S1b road treatment -> sewer corridors ...")
            # the outfall is chosen on the RAW graph and its node protected through
            # treatment: dissolving degree-2 nodes would otherwise delete the true low
            # point and move the outfall uphill (review RT-7)
            probe = TreeBuilder(sampler, C, cfg.outfall_expected, cfg.outfall_override)
            raw_of, raw_rep = probe.pick_outfall(probe.build_undirected(segs), boundary)
            rt = RoadTreatment(sampler, C, attrs=attrs, underpasses=cfg.underpasses)
            segs = rt.run(segs, units, out_path=cfg.corridors_out, protect={raw_of})
            self.reports["road_treatment"] = rt.report
            self.log(f"   {rt.report}")
            self.log(f"   outfall candidate protected at ({raw_rep['x']:.1f}, "
                     f"{raw_rep['y']:.1f}) z={raw_rep['z']:.2f}")

        self.log("S2 topology ...")
        tb = TreeBuilder(sampler, C, cfg.outfall_expected, cfg.outfall_override)
        Gu = tb.build_undirected(segs)
        tb.mark_arterials(Gu)
        if cfg.treat_roads and getattr(rt, "crossings", None):
            from .model import key_of as _kf
            marked = 0
            for g, free in rt.crossings:
                a, b = _kf(*g.coords[0][:2]), _kf(*g.coords[-1][:2])
                if Gu.has_edge(a, b):
                    Gu[a][b]["crossing"] = True
                    Gu[a][b]["free_crossing"] = bool(free)
                    marked += 1
            self.reports["road_treatment"]["crossings_on_graph"] = marked
        if cfg.use_trunk:
            # The main pipe is GIVEN (user 2026-08-20): read the drawing, keep the part
            # this area needs, and hang the streets off it at right angles.
            mp = MainPipe(cfg.main_pipe, C, cfg.main_pipe_lead_m)
            segs_mp, of_xy, trep = mp.build(boundary, cfg.confluence)
            if not segs_mp:
                raise RuntimeError(f"main pipe not usable: {trep}")
            self.log(f"   main pipe from the drawing: {trep['trunk_km']} km "
                     f"({trep['inside_boundary_km']} km inside the boundary, "
                     f"{trep['lead_to_outfall_km']} km of lead to the outfall)")
            trunk_path, arep = attach_to_roads(Gu, segs_mp, of_xy, sampler, C,
                                               dn_mm=cfg.trunk_dn_seed,
                                               units=units, keep_k=cfg.max_trunk_joins)
            trep.update(arep)
            self.reports["trunk"] = trep
            self.log(f"   {arep['trunk_chambers']} chambers on it; "
                     f"{arep['connection_points']} streets connect at right angles "
                     f"(median connector {arep['median_connector_m']} m); "
                     f"{arep['too_far_to_connect']} too far")
            outfall = min(trunk_path, key=lambda k: (Gu.nodes[k]["x"] - of_xy[0]) ** 2
                          + (Gu.nodes[k]["y"] - of_xy[1]) ** 2)
            Gd, unreachable = tree_to_trunk(Gu, trunk_path, outfall, C)
            self.trunk_nodes = set(trunk_path)
            self.trunk_segs = segs_mp
        else:
            outfall, _ = tb.pick_outfall(Gu, boundary)
            Gd, unreachable = tb.build_tree(Gu, outfall)
            self.trunk_nodes = set()
        of_rep = {"x": Gd.nodes[outfall]["x"], "y": Gd.nodes[outfall]["y"],
                  "z": Gd.nodes[outfall]["z"], "node": outfall}
        if cfg.outfall_expected:
            of_rep["dist_to_expected_m"] = math.hypot(of_rep["x"] - cfg.outfall_expected[0],
                                                      of_rep["y"] - cfg.outfall_expected[1])
        aug = tb.augment_cross_streets(Gu, Gd, units)
        self.reports["tree"] = {"nodes": Gd.number_of_nodes(), "edges": Gd.number_of_edges(),
                                "unreachable": len(unreachable), "augmentation": aug,
                                "outfall": of_rep}
        self.log(f"   outfall ({of_rep['x']:.1f}, {of_rep['y']:.1f}) z={of_rep['z']:.2f}; "
                 f"{Gd.number_of_nodes()} nodes, unreachable {len(unreachable)}")
        self.log(f"   cross-street additions: {aug}")

        best = None
        avoid = []
        for attempt in range(cfg.reroute_passes + 1):
            if attempt:
                # alternate the two ways of pricing a route — "uphill is expensive" and
                # "gaining trench depth is expensive". They pick different ways round the
                # ridge, and which one wins is not predictable, so try both.
                cost = "depth" if attempt % 2 else "climb"
                Gd, unreachable = tree_to_trunk(Gu, trunk_path, outfall, C, avoid=avoid,
                                                cost=cost)                     if cfg.use_trunk else tb.build_tree(Gu, outfall)
                tb.augment_cross_streets(Gu, Gd, units)
            self.log("S3 chambers ...")
            plot_shapes = [u.geom for u in units if getattr(u, "geom", None) is not None]
            placer = ChamberPlacer(sampler, C, round_spacing=cfg.round_spacing, plots=plot_shapes)
            net = placer.run(Gd, outfall)

            self.log("S3b one outlet per structure ...")
            resolver = StructureResolver(sampler, C)
            net = resolver.run(net, units)
            # merging chambers can lengthen a reach or bring a bend back, and a re-split
            # piece can still be too long, so repeat until nothing needs splitting
            respaced = 0
            for _ in range(4):
                n = placer.enforce_spacing(net)
                respaced += n
                if n == 0:
                    break
            if respaced:
                self.log(f"   {respaced} reaches re-split after chamber merging")
            if placer.tight_corners:
                self.log(f"   {len(placer.tight_corners)} corner chambers sit under "
                         f"{C.BEND_CORNER_CLEAR_M} m from a plot — flagged for the drawing")
            self.reports["tight_corners"] = len(placer.tight_corners)
            Labeller.run(net)
            self.reports["structures"] = {k: v for k, v in resolver.report.items()
                                          if k != "offsets_m"}
            self.log(f"   {self.reports['structures']}")
            self.log(f"   {len(net.chambers)} chambers, {len(net.reaches)} reaches, "
                     f"{net.summary()['length_km']:.1f} km")

            self.log("S4 join each plot to the pipe it faces ...")
            conn_stage = ConnectabilityStage(sampler, C)
            per_chamber, worst_spur = conn_stage.attach(net, units)
            joined = sum(len(v) for v in per_chamber.values())
            alloc.accumulate(net, per_chamber)
            self.log(f"   {joined} of {len(units)} properties joined; longest spur "
                     f"{worst_spur:.0f} m")

            self.log("S5/S6 diameters + inverts ...")
            designer = HydraulicDesigner(sampler, C)
            hyd = designer.run(net)
            self.reports["solver"] = {"converged": hyd["converged"], "iterations": hyd["iterations"],
                                      "smoothing": hyd.get("smoothing"),
                                      "pockets": len(hyd["pockets"])}
            self.log(f"   {self.reports['solver']}")


            # a pumping station is now a REAL thing in the design: the point where the
            # pipe would have passed 12 m deep, so it is lifted and restarts shallow.
            stations = hyd["stations"]
            pumped = sum(s["n_props"] for s in hyd["station_list"])
            deepest = max((c.depth or 0) for c in net.chambers.values())
            self.log(f"   pass {attempt}: {stations} pumping stations, {pumped:.0f} properties "
                     f"pumped, deepest chamber {deepest:.1f} m")
            if best is None or (stations, pumped) < best[0]:
                best = ((stations, pumped), net, per_chamber, hyd, placer, resolver,
                        designer, conn_stage)
            if stations == 0:
                break
            # remember where it dug too deep, so the next pass routes around it
            # try again round the streets that forced a pump, and round the deep runs.
            # The spots come from the BEST design so far, not the last one, so the search
            # keeps working on the problem that is actually left.
            ref = best[1]
            avoid = [(c.x, c.y) for c in ref.chambers.values()
                     if c.is_station or (c.depth or 0) > 9.0]
            if not avoid:
                break
        (_, net, per_chamber, hyd, placer, resolver, designer, conn_stage) = best
        # Every pass writes which pipe a plot joins onto the plot object itself, so after the
        # search those notes describe the LAST pass, not the one we kept. Re-do the joining
        # on the design we kept, or the house-connection checks would be looking at pipes
        # that no longer exist. (Found 19 Aug: the connection check silently saw nothing.)
        per_chamber, _ = conn_stage.attach(net, units)
        self._station_report(hyd)
        self.log(f"   kept the pass with {best[0][0]} pumping stations "
                 f"({best[0][1]:.0f} properties pumped)")

        self.log("S6b can every house drain into it? ...")
        conn, deepen = conn_stage.check(net, per_chamber)
        n_low = sum(1 for r in conn if not r["ok"])
        if deepen:
            conn_stage.apply_deepening(net, deepen)
            hyd = designer.run(net)
            # deepening chambers for low houses re-solves the whole network, and a deeper
            # network can need another pump — so the station schedule has to be rebuilt
            # here or the report would describe the design before the deepening.
            self._station_report(hyd)
            if self.reports["stations"]["count"] != best[0][0]:
                self.log(f"   deepening {len(deepen)} chambers for low houses changed the "
                         f"pumping stations to {self.reports['stations']['count']}")
            still = conn_stage.recheck(conn, net, C)
        else:
            still = []
        # The drawn house connections were not good enough (user 2026-08-20), so this
        # iteration does not produce them. The check that a house can actually drain into
        # the sewer — and the chamber deepening it triggers — is untouched above.
        spurs, riders, stubs = [], [], []
        self.reports["lowplots"] = {"checked": len(conn), "flagged": n_low,
                                    "deepened_mh": len(deepen), "residual": len(still)}
        self.reports["tertiary"] = {"parked": "house connections not drawn (user 2026-08-20)",
                                    "spurs": len(spurs), "riders": len(riders),
                                    "stub_outs": len(stubs),
                                    "longest_spur_m": round(worst_spur, 1)}
        self.log(f"   {self.reports['lowplots']}")

        self.log("S7 audit ...")
        auditor = Auditor(C)
        auditor.run(net, units, per_chamber, sampler, lstats, conn)
        self.reports["audit"] = auditor.as_dicts()
        self.reports["selfclean"] = selfclean_stats(net, C)
        sy = start_year_selfclean(net, per_chamber, C, cfg.pf_formula)
        self.reports["startyear_flags"] = len(sy)
        self.log(f"   {len(auditor.failures)} failing checks of {len(auditor.results)}")
        for r in auditor.failures:
            self.log(f"     FAIL {r.id} {r.title}: {r.summary}")

        return {"network": net, "units": units,
                "trunk_keys": sorted(getattr(self, "trunk_nodes", set())),
                "trunk_segs": getattr(self, "trunk_segs", []), "per_chamber": per_chamber, "conn": conn,
                "still_low": still, "riders": riders, "spurs": spurs, "stubs": stubs,
                "hazard": self.hazard, "pockets": hyd["pockets"],
                "boundary": boundary, "of_rep": of_rep, "sampler": sampler,
                "auditor": auditor, "sy_flags": sy, "reports": self.reports}
