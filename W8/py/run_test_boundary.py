"""W4 end-to-end design run on the test boundary.

Composition only — every stage lives in sewnet/stages/. Feature switches:
    --raw-roads       skip road treatment (raw centrelines, as before treatment existed)
    --equal-spacing   exact equal division instead of rounded spacing
Both off-switches together reproduce the pre-refactor design exactly (the equality gate).
"""

import json
import os
import pickle
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config_test as cfg                                            # noqa: E402
from sewnet.criteria import DEFAULT                                  # noqa: E402
from sewnet.pipeline import RunConfig, SewerDesignPipeline           # noqa: E402

T0 = time.time()


def log(msg):
    print(f"[{time.time()-T0:7.1f}s] {msg}", flush=True)


def main(argv, max_joins=None):
    max_joins = max_joins if max_joins is not None else getattr(cfg, "MAX_TRUNK_JOINS", None)
    os.makedirs(cfg.OUT_RUN, exist_ok=True)
    rc = RunConfig(
        roads=cfg.ROADS, plots=cfg.PLOTS_CLASS, unparceled=cfg.UNPARCELED,
        boundary=cfg.BOUNDARY, terrain=cfg.TERRAIN,
        outfall_expected=cfg.OUTFALL_EXPECTED, outfall_override=cfg.OUTFALL_OVERRIDE,
        main_pipe=cfg.MAIN_PIPE, confluence=cfg.CONFLUENCE,
        main_pipe_lead_m=cfg.MAIN_PIPE_LEAD_M,
        underpasses=tuple(getattr(cfg, "UNDERPASSES", ())),
        max_trunk_joins=max_joins,
        pf_formula=cfg.PF_FORMULA, clip_sliver_m=cfg.CLIP_SLIVER_M,
        dual_merge_m=cfg.DUAL_MERGE_M,
        treat_roads="--raw-roads" not in argv,
        round_spacing="--equal-spacing" not in argv,
        corridors_out=os.path.join(cfg.OUT_SHP, "W8_corridors.shp"),
        hazard=getattr(cfg, "HAZARD", None), accounts=getattr(cfg, "ACCOUNTS", None),
    )
    res = SewerDesignPipeline(rc, DEFAULT, log).run()
    net, reports, auditor = res["network"], res["reports"], res["auditor"]

    out_reaches = [r for r in net.reaches if r.dn == net.outfall]
    dn_km = {}
    for r in net.reaches:
        dn_km[r.dn_mm] = dn_km.get(r.dn_mm, 0.0) + r.length
    summary = {
        "s1": reports["inputs"], "outfall": res["of_rep"],
        "n_nodes": len(net.chambers), "n_pipes": len(net.reaches),
        "net_km": net.summary()["length_km"],
        "loads": reports["loads"], "solver": reports["solver"],
        "structures": reports["structures"], "lowplots": reports["lowplots"],
        "road_treatment": reports.get("road_treatment"),
        "stations": reports.get("stations"), "sweep": reports.get("sweep"),
        "trunk": reports.get("trunk"),
        "tertiary": reports.get("tertiary"),
        "augmentation": reports["tree"]["augmentation"],
        # the outfall may receive several reaches; each PIPE is sized for its own peak,
        # but the peak the outfall/STP sees is the peak factor applied to the COMBINED
        # average flow — summing individually-peaked arrivals would over-count
        "qadf_outfall_m3d": sum(r.qadf_m3d for r in out_reaches),
        "qpeak_outfall_ls": round(
            (DEFAULT.pf_merrimack(max(sum(r.qadf_m3d for r in out_reaches) / 1000.0,
                                      DEFAULT.PF_HOLD_PROPERTIES * DEFAULT.PLOT_QADF_M3D / 1000.0))
             * sum(r.qadf_m3d for r in out_reaches)
             + sum(r.infil_m3d for r in out_reaches)) * 1000.0 / 86400.0, 2),
        "qpeak_sum_of_arrivals_ls": round(sum(r.qpeak_ls for r in out_reaches), 2),
        "n_outfall_reaches": len(out_reaches),
        "dn_km": {str(k): round(v / 1000.0, 3) for k, v in sorted(dn_km.items())},
        "violations": len(auditor.failures),
        "selfclean": reports["selfclean"], "startyear_flags": reports["startyear_flags"],
        "max_depth_m": max((c.depth or 0) for c in net.chambers.values()),
        "drops": sum(len(c.drops) for c in net.chambers.values()),
        "vortex_sites": sum(1 for c in net.chambers.values()
                            for d in c.drops if d["type"] == "vortex"),
        "pf_formula": cfg.PF_FORMULA,
        "features": {"road_treatment": rc.treat_roads, "rounded_spacing": rc.round_spacing},
    }
    log("SUMMARY " + json.dumps({k: summary[k] for k in
                                 ("n_nodes", "n_pipes", "net_km", "qpeak_outfall_ls",
                                  "violations", "max_depth_m", "drops")}, default=str))
    st = summary.get("stations") or {}
    log(f"PUMPING STATIONS {st.get('count', 0)} | {st.get('properties_pumped', 0)} properties "
        f"| lift {st.get('total_lift_m', 0)} m | rising mains {st.get('rising_main_m', 0)} m")

    with open(os.path.join(cfg.OUT_RUN, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    with open(os.path.join(cfg.OUT_RUN, "audit.json"), "w") as f:
        json.dump(reports["audit"], f, indent=2, default=str)
    with open(os.path.join(cfg.OUT_RUN, "audit_table.txt"), "w", encoding="utf-8") as f:
        f.write(auditor.table())
    with open(os.path.join(cfg.OUT_RUN, "state.pkl"), "wb") as f:
        pickle.dump({"network": net, "units": res["units"],
                     "per_chamber": res["per_chamber"], "conn": res["conn"],
                     "still_low": res["still_low"], "riders": res["riders"],
                     "spurs": res["spurs"], "stubs": res["stubs"],
                     "pockets": res["pockets"], "of_rep": res["of_rep"],
                     "trunk_keys": res.get("trunk_keys", []),
                     "trunk_wkt": [g.wkt for g in res.get("trunk_segs", [])],
                     "boundary_wkt": res["boundary"].wkt, "sy_flags": res["sy_flags"],
                     "summary": summary}, f)
    log(f"state saved to {cfg.OUT_RUN}")
    return 0 if not auditor.failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
