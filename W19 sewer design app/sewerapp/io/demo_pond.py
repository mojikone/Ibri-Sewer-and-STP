"""A pond that takes rain, a pump that starts at a set depth and lifts it to an outfall: laid out on the positions of the
engineer's SewerGEMS model Pond_Mouj (2026-11-23: pond outlet, pump, the junction at the end of the 463 m rising main),
read through the API. That model holds no levels, no pump curve and no rain (every one is 0 and SewerGEMS's own run gives
no results), so the levels, the pond's depth-area table, the pump and the storm below are DEMONSTRATION values, to be
replaced by the engineer's."""
from sewerapp.model.general import Project
from sewerapp.model import workspace as W

NAME = "Pond and pump (demo, Pond_Mouj layout)"
# positions read from the model through the API (EPSG:32640 assumed: the model holds no coordinate system)
POS = dict(outlet=(632717.810, 2612041.917), pump=(632708.904, 2612052.847), junction=(632626.467, 2612167.670))


def build():
    p = Project(NAME, crs=32640)
    (xo, yo), (xp, yp), (xj, yj) = POS["outlet"], POS["pump"], POS["junction"]
    W.apply(p, dict(op="add_node", id="BO-1", kind="storage", x=xo, y=yo, ground=103.0, invert=100.0))        # demo levels
    W.apply(p, dict(op="add_node", id="WW-1", kind="wetwell", x=xp, y=yp, ground=103.0, invert=99.5))
    W.apply(p, dict(op="add_node", id="J-1", kind="outfall", x=xj, y=yj, ground=106.0, invert=105.0))
    W.apply(p, dict(op="add_link", id="POS-1", kind="conduit", from_node="BO-1", to_node="WW-1", dn_mm=500, up_inv=100.0, dn_inv=99.5))
    W.apply(p, dict(op="add_link", id="PMP-1", kind="pump", from_node="WW-1", to_node="J-1"))
    s = 160.0                                                                     # a 160 m square catchment over the pond
    W.apply(p, dict(op="add_catchment", id="CM-1", outlet="BO-1", area_ha=s * s / 1e4, imperv_pc=100.0, width_m=s, slope_pc=0.5,
                    coords=[[xo - s, yo - s / 2], [xo, yo - s / 2], [xo, yo + s / 2], [xo - s, yo + s / 2]]))
    W.apply(p, dict(op="set_storage", ids=["BO-1"], curve=[[0, 1500.0], [1, 1800.0], [2, 2200.0], [3, 2600.0]]))
    W.apply(p, dict(op="set_storage", ids=["WW-1"], area_m2=20.0))
    W.apply(p, dict(op="set_pump", ids=["PMP-1"], q_ls=120.0, on_m=1.0, off_m=0.3))
    p.rain = dict(step_min=5, duration_min=60, idf=dict(durations_min=[5, 10, 15, 30, 60], intensities=[180.0, 140.0, 115.0, 80.0, 50.0]))
    p.load_sets["design"] = {}
    return p
