# -*- coding: utf-8 -*-
"""TEMPORARY: what does laying pipes at a ROUND gradient cost?

A gradient of 6.911 mm/m is not something anyone sets out on site. The fix is to design at
a round value, not to print a rounded number while the inverts still come from 6.911 — that
would make the drawing lie (user 2026-08-23).

Rounding can only go UP on an individual pipe, because rounding down would breach the
minimum gradient. Up means steeper, steeper means the trench falls away faster, and depth is
what buys pumping stations. So the question is what it costs.

Writes nothing into W8.
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


def run(step):
    crit = replace(DEFAULT, SLOPE_STEP=step)
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
    d = np.array([c.depth for c in net.chambers.values() if c.depth])
    sl = np.array([r.slope for r in net.reaches if r.slope])

    # trench volume proxy: length x average end depth x 1 m wide
    vol = sum(r.length * ((net.chambers[r.up].depth or 0) +
                          (net.chambers[r.dn].depth or 0)) / 2 for r in net.reaches)
    # how many gradients are actually round at this step?
    if step > 0:
        off = np.abs(sl / step - np.round(sl / step))
        rounded = float((off < 1e-6).mean())
    else:
        rounded = float((np.abs(sl * 1000 - np.round(sl * 1000, 1)) < 1e-9).mean())
    return {
        "step_pct": round(step * 100, 3),
        "distinct_gradients": int(len(np.unique(np.round(sl, 6)))),
        "share_on_a_round_value": round(rounded * 100, 1),
        "depth_median": round(float(np.median(d)), 2),
        "depth_mean": round(float(d.mean()), 2),
        "depth_90": round(float(np.percentile(d, 90)), 2),
        "depth_max": round(float(d.max()), 2),
        "pct_over_6m": round(float((d > 6).mean() * 100), 1),
        "trench_m3_per_m_width": round(vol),
        "stations": (rep.get("stations") or {}).get("count", 0),
        "net_km": round(net.summary()["length_km"], 1),
        "chambers": len(net.chambers),
        "fails": sorted({f.id for f in res["auditor"].failures}),
    }


if __name__ == "__main__":
    out = []
    for step in (0.0, 0.0005, 0.001):
        r = run(step)
        out.append(r)
        lbl = "as now (no rounding)" if step == 0 else f"{r['step_pct']} % steps"
        print(f"[{time.time()-T0:6.1f}s] {lbl:22s} "
              f"gradients {r['distinct_gradients']:4d} distinct, "
              f"{r['share_on_a_round_value']:5.1f}% on a round value | "
              f"depth med {r['depth_median']:4.2f} mean {r['depth_mean']:4.2f} "
              f"max {r['depth_max']:5.2f}, over 6 m {r['pct_over_6m']:4.1f}% | "
              f"trench {r['trench_m3_per_m_width']:,} m3 | "
              f"{r['stations']} stations", flush=True)
    base = out[0]
    print("\nCOST OF ROUNDING, against the design as it stands")
    for r in out[1:]:
        dv = (r["trench_m3_per_m_width"] - base["trench_m3_per_m_width"])
        print(f"   {r['step_pct']:.2f} % steps: "
              f"trench {dv:+,} m3 ({dv/base['trench_m3_per_m_width']*100:+.1f} %), "
              f"deepest {r['depth_max']-base['depth_max']:+.2f} m, "
              f"stations {r['stations']-base['stations']:+d}")
    print("\n" + json.dumps(out, indent=1))
