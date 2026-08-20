# -*- coding: utf-8 -*-
"""Does tighter manhole spacing keep the trench shallower?

The as-built Ibri network puts manholes about 30 m apart and almost never digs past 6 m.
My design uses up to 100 m and digs past 6 m four times as often. The suspicion is that
these are the same fact: a pipe laid straight between distant chambers cannot follow the
ground, so it dives under every rise. This runs the design at several spacings and reports
what actually happens. Nothing is written into W7.
"""
import json
import os
import sys
import time
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import config_test as cfg
from sewnet.criteria import DEFAULT
from sewnet.pipeline import RunConfig, SewerDesignPipeline

T0 = time.time()


def quiet(*a):
    pass


def run(split_len):
    crit = replace(DEFAULT, MH_SPLIT_LEN=split_len)
    rc = RunConfig(
        roads=cfg.ROADS, plots=cfg.PLOTS_CLASS, unparceled=cfg.UNPARCELED,
        boundary=cfg.BOUNDARY, terrain=cfg.TERRAIN,
        outfall_expected=cfg.OUTFALL_EXPECTED, outfall_override=cfg.OUTFALL_OVERRIDE,
        main_pipe=cfg.MAIN_PIPE, confluence=cfg.CONFLUENCE,
        main_pipe_lead_m=cfg.MAIN_PIPE_LEAD_M,
        underpasses=tuple(getattr(cfg, "UNDERPASSES", ())),
        max_trunk_joins=getattr(cfg, "MAX_TRUNK_JOINS", None),
        pf_formula=cfg.PF_FORMULA, clip_sliver_m=cfg.CLIP_SLIVER_M,
        dual_merge_m=cfg.DUAL_MERGE_M, corridors_out=None,
        hazard=getattr(cfg, "HAZARD", None), accounts=getattr(cfg, "ACCOUNTS", None))
    res = SewerDesignPipeline(rc, crit, quiet).run()
    net, rep = res["network"], res["reports"]
    d = [c.depth for c in net.chambers.values() if c.depth]
    ln = [r.length for r in net.reaches]
    st = (rep.get("stations") or {}).get("count", 0)
    return {"cap_m": split_len,
            "chambers": len(net.chambers),
            "net_km": round(net.summary()["length_km"], 1),
            "spacing_median": round(float(np.median(ln)), 1),
            "depth_median": round(float(np.median(d)), 2),
            "depth_90": round(float(np.percentile(d, 90)), 2),
            "depth_max": round(max(d), 2),
            "pct_over_6m": round(sum(1 for x in d if x > 6) / len(d) * 100, 1),
            "stations": st,
            "fails": sorted({f.id for f in res["auditor"].failures})}


if __name__ == "__main__":
    print("as-built Ibri: spacing 29.8 m | depth median 1.92 | 90th 4.58 | max 8.85 "
          "| over 6 m 1.4% | 0 stations in the gravity net")
    for cap in (100.0, 70.0, 50.0, 40.0, 30.0):
        r = run(cap)
        print(f"[{time.time()-T0:6.1f}s] cap {cap:5.0f} m: {r['chambers']:5d} chambers, "
              f"spacing {r['spacing_median']:5.1f} m, depth med {r['depth_median']:4.2f} "
              f"90th {r['depth_90']:5.2f} max {r['depth_max']:5.2f}, "
              f"over 6 m {r['pct_over_6m']:4.1f}%, {r['stations']} stations", flush=True)
