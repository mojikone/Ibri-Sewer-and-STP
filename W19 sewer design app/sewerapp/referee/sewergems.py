"""A case against SewerGEMS's own run of it (the referee build of W18, jobs 080 on, export saved in the fixtures), pipe
by pipe, by the new labels; the checks of W18 py/final_sg_compare.py, returned as numbers so a gate can assert them.
No SewerGEMS run is made: the saved export is the referee for gravity."""
import os
import numpy as np, pandas as pd
from sewerapp import fixtures


def compare(case_dir, case="SC1-2056"):
    own = pd.read_csv(os.path.join(case_dir, "named", "links.csv")).set_index("new")
    q_own = pd.read_csv(os.path.join(case_dir, "exports", f"conduits_{case}a.csv")).set_index("label").flow_m3d
    own["q_own"] = own.old.map(q_own)
    sg = fixtures.read_csv(f"sewergems/{case}/conduits_{case}.csv"); sg = sg[sg.active == True].set_index("label")
    s31 = fixtures.read_csv(f"sewergems/{case}/conduits_{case}-at-2031.csv"); s31 = s31[s31.active == True].set_index("label")
    j = own.join(sg[["flow_m3d", "depth_in_m", "depth_out_m", "diameter_mm"]], how="inner") \
           .join(s31[["velocity_ms"]].rename(columns={"velocity_ms": "v31_sg"}))
    dq = (j.flow_m3d - j.q_own) / j.q_own * 100
    dD = j[["depth_in_m", "depth_out_m"]].max(axis=1) / (j.diameter_mm / 1000)
    lim = np.where(j.dn_mm <= 355, 0.65, 0.50)
    big = j[j.dn_mm > 200]; dv = big.v31_sg - big.v2031_ms
    return dict(pipes_compared=int(len(j)), pc_within_0_1=round(float((dq.abs() < 0.1).mean() * 100), 3),
                largest_dq_pc=round(float(dq.abs().max()), 4), over_limit=int((dD > lim + 0.005).sum()),
                dv_p05=round(float(dv.quantile(.05)), 4), dv_p95=round(float(dv.quantile(.95)), 4),
                km_under_model=round(float(big.length_m[big.v31_sg.round(2) < 0.75].sum() / 1000), 2),
                km_under_own=round(float(big.length_m[big.v2031_ms.round(2) < 0.75].sum() / 1000), 2))
