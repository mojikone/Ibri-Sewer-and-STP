"""Automated sizing as SewerGEMS does it (proved blind on Ibri SC1-2051, then on 2056): each pipe takes the smallest
catalogue size whose Colebrook-White capacity at the d/D limit carries its flow at the gradient of its CURRENT size,
pass after pass from the modeller's sizes until no size changes. Gradient = the Table 11 minimum of the size."""
import numpy as np
from sewerapp.engine.hydraulics import q_capacity


def dd_limit(nominal):
    """PAM-GUD-203 p27 Table 10: d/D at peak <= 0.65 up to DN355 (inside 313 mm), <= 0.50 above."""
    return np.where(np.asarray(nominal) <= 355, 0.65, 0.50)


def table11_slopes(net, cat_nominal):
    """The gradient per size of the network as designed (every Ibri pipe sits on PAM-GUD-203 p29 Table 11); sizes it
    does not use: 0.075 % from DN900, 0.205 % for DN400 (Table 11). W18 final_design.py lines 41-45."""
    s = net.pipes.groupby("nominal_mm").slope.agg(lambda x: x.round(6).mode().iloc[0]).to_dict()
    for n in cat_nominal:
        if n not in s: s[n] = 0.00075 if n >= 900 else {400: 0.00205}.get(n, np.nan)
    missing = [n for n in cat_nominal if np.isnan(s[n])]
    if missing: raise ValueError(f"no Table 11 gradient for DN{missing}")
    return {int(k): float(v) for k, v in s.items()}


def size_passes(q_m3s, start_nominal, cat_nominal, cat_inside_m, slope_of, max_passes=20):
    cat_nominal = np.asarray(cat_nominal, int); D = np.asarray(cat_inside_m, float)[None, :]
    lim = dd_limit(cat_nominal)[None, :]; q = np.asarray(q_m3s, float)[:, None]
    nom = np.asarray(start_nominal, int).copy()
    for p in range(1, max_passes + 1):
        S = np.array([slope_of[int(n)] for n in nom])[:, None]
        ok = q_capacity(D, S, lim) >= q
        new = cat_nominal[np.where(ok.any(axis=1), ok.argmax(axis=1), len(cat_nominal) - 1)]
        changed = int((new != nom).sum()); nom = new
        if changed == 0: return nom, p
    raise RuntimeError(f"sizing did not settle in {max_passes} passes")
