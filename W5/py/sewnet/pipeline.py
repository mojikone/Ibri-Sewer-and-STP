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

    def run(self):
        cfg, C = self.cfg, self.crit

        self.log("S1 inputs: boundary, roads, terrain, flood grid ...")
        segs, attrs, boundary, sampler, hazard, s1 = prep.prepare(
            cfg.roads, cfg.boundary, cfg.terrain, cfg.clip_sliver_m, cfg.dual_merge_m,
            hazard_path=cfg.hazard)
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
            rt = RoadTreatment(sampler, C, attrs=attrs)
            segs = rt.run(segs, units, out_path=cfg.corridors_out, protect={raw_of})
            self.reports["road_treatment"] = rt.report
            self.log(f"   {rt.report}")
            self.log(f"   outfall candidate protected at ({raw_rep['x']:.1f}, "
                     f"{raw_rep['y']:.1f}) z={raw_rep['z']:.2f}")

        self.log("S2 topology: tree to the outfall ...")
        tb = TreeBuilder(sampler, C, cfg.outfall_expected, cfg.outfall_override)
        Gd, outfall, of_rep = tb.run(segs, boundary, units)
        self.reports["tree"] = tb.report
        self.log(f"   outfall ({of_rep['x']:.1f}, {of_rep['y']:.1f}) z={of_rep['z']:.2f}; "
                 f"{tb.report['nodes']} nodes, {tb.report['edges']} edges, "
                 f"unreachable {tb.report['unreachable']}")
        self.log(f"   cross-street augmentation: {tb.report['augmentation']}")

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
                                  "pockets": len(hyd["pockets"])}
        self.log(f"   {self.reports['solver']}")

        self.log("S6b can every house drain into it? ...")
        conn, deepen = conn_stage.check(net, per_chamber)
        n_low = sum(1 for r in conn if not r["ok"])
        if deepen:
            conn_stage.apply_deepening(net, deepen)
            hyd = designer.run(net)
            still = conn_stage.recheck(conn, net, C)
        else:
            still = []
        spurs, riders, stubs = conn_stage.connections(net, per_chamber)
        self.reports["lowplots"] = {"checked": len(conn), "flagged": n_low,
                                    "deepened_mh": len(deepen), "residual": len(still)}
        self.reports["tertiary"] = {"spurs": len(spurs), "riders": len(riders),
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

        return {"network": net, "units": units, "per_chamber": per_chamber, "conn": conn,
                "still_low": still, "riders": riders, "spurs": spurs, "stubs": stubs,
                "hazard": self.hazard, "pockets": hyd["pockets"],
                "boundary": boundary, "of_rep": of_rep, "sampler": sampler,
                "auditor": auditor, "sy_flags": sy, "reports": self.reports}
