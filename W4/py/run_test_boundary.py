"""W4 end-to-end design run on the test boundary. Stages S1-S7; saves everything
export/report modules need to W4/run/. Re-runnable; paths in config_test.py only."""

import json
import os
import pickle
import sys
import time

import config_test as cfg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sewnet import criteria as C, prep, topo, manholes, loads, solver, tertiary, audit

T0 = time.time()


def log(msg):
    print(f"[{time.time()-T0:7.1f}s] {msg}", flush=True)


def main():
    os.makedirs(cfg.OUT_RUN, exist_ok=True)

    # ---- S1 prep
    log("S1 prep: boundary, clip, node, dual collapse ...")
    segs, boundary, sampler, s1 = prep.prepare(cfg.ROADS, cfg.BOUNDARY, cfg.TERRAIN,
                                               cfg.CLIP_SLIVER_M, cfg.DUAL_MERGE_M)
    log(f"  boundary {s1['boundary_ha']:.1f} ha, segs {s1['segs_raw']}->{s1['segs_final']}, "
        f"dual-flagged {s1['dual_flagged']}, {s1['len_km']:.1f} km")

    # ---- S4a load units (needed by the cross-street augmentation)
    log("S4a load units ...")
    units, lstats = loads.load_plots(cfg.PLOTS_CLASS, cfg.UNPARCELED, boundary)
    log(f"  {lstats}")

    # ---- S2 topology
    log("S2 topology: graph, arterials, outfall, tree ...")
    Gu = topo.build_undirected(segs, sampler)
    topo.mark_arterials(Gu)
    outfall, of_rep = topo.pick_outfall(Gu, boundary, expected=cfg.OUTFALL_EXPECTED,
                                        override=cfg.OUTFALL_OVERRIDE)
    log(f"  outfall at ({of_rep['x']:.1f}, {of_rep['y']:.1f}) z={of_rep['z']:.2f} | "
        f"dist to user expectation {of_rep.get('dist_to_expected_m', -1):.0f} m "
        f"({'agrees' if of_rep.get('agrees') else 'DIFFERS — reported, not stopping'})")
    Gd, unreachable = topo.build_tree(Gu, outfall)
    log(f"  tree: {Gd.number_of_nodes()} nodes, {Gd.number_of_edges()} edges, "
        f"unreachable {len(unreachable)}")
    aug = topo.augment_cross_streets(Gu, Gd, sampler, units)
    log(f"  cross-street augmentation: +{aug['added']} branches ({aug['added_km']} km); "
        f"unloaded streets left unsewered: {aug['skipped_empty']} ({aug['skipped_km']} km)")

    # ---- S3 manholes
    log("S3 manholes ...")
    nodes, pipes = manholes.place(Gd, outfall, sampler)
    log(f"  {len(nodes)} manholes, {len(pipes)} pipe reaches, "
        f"{sum(p['length'] for p in pipes)/1000:.1f} km")

    # ---- S4 assignment
    log("S4 assignment ...")
    per_mh, maxdist = loads.assign_to_manholes(units, nodes)
    log(f"  all {len(units)} units assigned; max plot->MH distance {maxdist:.0f} m")
    loads.accumulate(pipes, per_mh, cfg.PF_FORMULA)

    # ---- S5/S6 solve
    log("S5/S6 sizing + inverts ...")
    rep = solver.solve(nodes, pipes, sampler)
    log(f"  converged={rep['converged']} in {rep['iterations']} iterations; "
        f"pockets={len(rep['pockets'])} failed-depth nodes={rep['n_failed_depth']}")

    # ---- S3b/S6b tertiary connectability + deepening + re-solve
    log("Tertiary connectability check ...")
    conn, deepen = tertiary.connectability(per_mh, nodes, sampler)
    n_low = sum(1 for r in conn if not r["ok"])
    log(f"  {len(conn)} units checked, {n_low} LOW_PLOT, deepening at {len(deepen)} manholes")
    if deepen:
        rep = solver.solve(nodes, pipes, sampler, node_min_depth=deepen)
        still = tertiary.recheck(conn, nodes)
        log(f"  after deepening: {len(still)} still failing -> local-solution candidates")
    else:
        still = []
    riders = tertiary.riders(per_mh, nodes)

    # ---- S7 audit
    log("S7 audit (saturation) ...")
    violations = audit.run(nodes, pipes, units, per_mh, sampler, label="saturation",
                           load_stats=lstats)
    log(f"  {len(violations)} violations")
    for v in violations[:20]:
        log(f"    {v}")
    sc = audit.selfclean_stats(pipes)
    log(f"  self-cleansing transparency: {sc['below_075_at_peak']}/{sc['pipes']} pipes "
        f"below 0.75 m/s at saturation peak (tractive-compliant at tau=1 Pa); "
        f"{sc['would_fail_at_tau2']} would need redesign at tau=2 Pa [GAP-9]")
    log("S7 audit (start-year self-cleansing, built + unparceled) ...")
    sy_flags = audit.start_year_selfclean(nodes, pipes, per_mh, cfg.PF_FORMULA)
    n_tr_ok = sum(1 for f in sy_flags if f["tractive_ok"])
    log(f"  {len(sy_flags)} pipes below 0.75 m/s at start-year; "
        f"{n_tr_ok} of them satisfy the tractive minimum (operational flag only)")

    # ---- summary numbers
    out_pipe = [p for p in pipes if p["dn"] == outfall]
    q_out_adf = sum(p["qadf_m3d"] for p in out_pipe)
    q_out_peak = sum(p["qpeak_m3s"] for p in out_pipe) * 1000.0
    dn_hist = {}
    for p in pipes:
        dn_hist[p["dn_mm"]] = dn_hist.get(p["dn_mm"], 0) + p["length"]
    summary = {
        "s1": s1, "outfall": of_rep, "n_nodes": len(nodes), "n_pipes": len(pipes),
        "net_km": sum(p["length"] for p in pipes) / 1000.0,
        "loads": lstats, "max_assign_dist_m": maxdist,
        "solver": {"converged": rep["converged"], "iterations": rep["iterations"],
                   "pockets": len(rep["pockets"])},
        "lowplots": {"checked": len(conn), "flagged": n_low,
                     "deepened_mh": len(deepen), "residual": len(still)},
        "qadf_outfall_m3d": q_out_adf, "qpeak_outfall_ls": q_out_peak,
        "dn_km": {str(k): round(v / 1000.0, 3) for k, v in sorted(dn_hist.items())},
        "violations": len(violations), "startyear_flags": len(sy_flags),
        "selfclean": sc, "augmentation": aug,
        "max_depth_m": max(n["depth"] for n in nodes.values() if n["depth"] is not None),
        "drops": sum(len(n["drops"]) for n in nodes.values()),
        "vortex_sites": sum(1 for n in nodes.values()
                            for d in n.get("drops", []) if d["type"] == "vortex"),
        "pf_formula": cfg.PF_FORMULA,
    }
    log(f"SUMMARY {json.dumps(summary, indent=2, default=str)[:1500]}")

    # ---- persist for exports/report
    with open(os.path.join(cfg.OUT_RUN, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    with open(os.path.join(cfg.OUT_RUN, "violations.json"), "w") as f:
        json.dump(violations, f, indent=2, default=str)
    with open(os.path.join(cfg.OUT_RUN, "state.pkl"), "wb") as f:
        pickle.dump({"nodes": nodes, "pipes": pipes, "units": units,
                     "per_mh_labels": {str(k): [u["id"] for u in v] for k, v in per_mh.items()},
                     "conn": conn, "still_low": still, "riders": riders,
                     "outfall": outfall, "of_rep": of_rep, "boundary_wkt": boundary.wkt,
                     "sy_flags": sy_flags, "violations": violations,
                     "pockets": rep["pockets"], "summary": summary}, f)
    log("state saved to W4/run/")
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
