# -*- coding: utf-8 -*-
"""Find the FEWEST joins onto the main pipe that still give a working design.

Every join becomes a chamber on the main pipe that will be deep once the whole town drains
through it, so they cost real money (user 2026-08-20). This runs the design with the cap
set lower and lower, and keeps the smallest cap that still holds every rule.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_test as cfg
from sewnet.criteria import DEFAULT
from sewnet.pipeline import RunConfig, SewerDesignPipeline

T0 = time.time()


def quiet(*a):
    pass


def run(cap):
    rc = RunConfig(
        roads=cfg.ROADS, plots=cfg.PLOTS_CLASS, unparceled=cfg.UNPARCELED,
        boundary=cfg.BOUNDARY, terrain=cfg.TERRAIN,
        outfall_expected=cfg.OUTFALL_EXPECTED, outfall_override=cfg.OUTFALL_OVERRIDE,
        main_pipe=cfg.MAIN_PIPE, confluence=cfg.CONFLUENCE,
        main_pipe_lead_m=cfg.MAIN_PIPE_LEAD_M,
        underpasses=tuple(getattr(cfg, "UNDERPASSES", ())),
        max_trunk_joins=cap,
        pf_formula=cfg.PF_FORMULA, clip_sliver_m=cfg.CLIP_SLIVER_M,
        dual_merge_m=cfg.DUAL_MERGE_M, corridors_out=None,
        hazard=getattr(cfg, "HAZARD", None), accounts=getattr(cfg, "ACCOUNTS", None))
    res = SewerDesignPipeline(rc, DEFAULT, quiet).run()
    net, rep = res["network"], res["reports"]
    st = rep.get("stations") or {}
    joins = [r for r in net.reaches
             if (not net.chambers[r.up].on_trunk) and net.chambers[r.dn].on_trunk]
    fails = {f.id for f in res["auditor"].failures}
    return {"cap": cap,
            "joins_built": len(joins),
            "crossings_built": sum(1 for r in net.reaches if r.is_crossing),
            "stations": st.get("count", 0),
            "max_depth_m": round(max((c.depth or 0) for c in net.chambers.values()), 2),
            "unreachable": rep["tree"].get("unreachable"),
            "net_km": round(net.summary()["length_km"], 1),
            "fails": sorted(fails)}


def ok(r):
    return (r["stations"] == 0 and r["max_depth_m"] <= 12.0
            and set(r["fails"]) <= {"C4", "C8", "D1"})


if __name__ == "__main__":
    caps = [None, 32, 30, 28, 26, 24, 20, 16]
    best, rows = None, []
    for cap in caps:
        r = run(cap)
        rows.append(r)
        good = ok(r)
        print(f"[{time.time()-T0:6.1f}s] cap {str(cap):>4}: {r['joins_built']:2d} joins, "
              f"{r['crossings_built']} crossings, {r['stations']} stations, "
              f"deepest {r['max_depth_m']:5.2f} m, unreachable {r['unreachable']:3d}, "
              f"{r['net_km']} km  -> {'OK' if good else 'REJECTED ' + str(r['fails'])}",
              flush=True)
        if good and (best is None or r["joins_built"] < best["joins_built"]):
            best = r
    print("\nFEWEST JOINS THAT STILL WORK: " + json.dumps(best, indent=1))
