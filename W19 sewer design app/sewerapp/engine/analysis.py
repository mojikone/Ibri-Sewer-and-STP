"""Analysis of a given design: velocity and depth at normal depth (Colebrook-White), d/D against Table 10, 3.0 m/s
(PAM-GUD-203 p27). A pipe is over its limit when d/D >= limit + 0.005 (judged at two decimals, W18's rule)."""
import pandas as pd
from sewerapp.engine.hydraulics import normal_depth
from sewerapp.engine.design import dd_limit


def analyse(q_m3d, inside_m, slope, nominal):
    ratio, v = normal_depth(q_m3d / 86400.0, inside_m, slope)
    lim = dd_limit(nominal)
    return pd.DataFrame(dict(flow_m3d=q_m3d, velocity_ms=v, depth_m=ratio * inside_m, d_over_D=ratio, limit=lim,
                             over_limit=ratio >= lim + 0.005, over_3ms=v > 3.0))
