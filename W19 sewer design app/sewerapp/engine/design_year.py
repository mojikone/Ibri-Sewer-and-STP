"""Does a design carry the flow of its design life? Ports W18 py/design_year_check.py: the 2051 and 2061 designs of a
scenario, on their own sizes and laid (steepened) gradients, at the 2056 peak of the same scenario; a pipe is over when
d/D at normal depth (Colebrook-White) >= the Table 10 limit + 0.005 (PAM-GUD-203 p27, judged at two decimals);
surcharged when it cannot carry the flow part-full."""
import numpy as np
from sewerapp import fixtures
from sewerapp.engine.design import dd_limit
from sewerapp.engine.hydraulics import normal_depth, q_capacity


def check(case, peak_case):
    c = fixtures.read_csv(f"golden/{case}/exports/conduits_{case}a.csv").set_index("label")
    k = fixtures.read_csv(f"golden/{case}/named/links.csv")
    k = k[k.old.isin(c.index)].set_index("old")
    q = fixtures.read_csv(f"golden/{peak_case}/exports/conduits_{peak_case}a.csv").set_index("label").flow_m3d / 86400.0
    nom = c.loc[k.index, "size_label"].str.extract(r"(\d+)")[0].astype(int).values
    D = c.loc[k.index, "diameter_mm"].values / 1000; S = k.s_new_pc.values / 100; Q = q.reindex(k.index).fillna(0).values
    full = q_capacity(D, S, 0.999) < Q
    r, _ = normal_depth(Q, D, S); r = np.where(full, 1.0, r)
    over = r >= dd_limit(nom) + 0.005
    return dict(pipes_over=int(over.sum()), km_over=round(float(k.length_m.values[over].sum()) / 1000, 1),
                surcharged=int(full.sum()), max_dD=round(float(r[over].max()), 2) if over.any() else 0)
