"""Design flow in every pipe (W18's rule, proved against SewerGEMS on all 19,083 Ibri pipes, flows within 0.004 %):
  q = PF(cumulative unit load, L/s) x cumulative unit load (the pipe's upstream manhole included)
      + infiltration x cumulative conduit length (the pipe's own length included)   (G201 p72: 720 L/day per km)
      + transfers pumped in upstream, not re-peaked.
A cut pipe (a lift station) does not pass its loads on: its peaked flow lands on its downstream manhole as a transfer."""
import numpy as np


def accumulate(net, base_m3d, transfer_m3d, peaking, inf_m3d_per_km=0.72, cut=frozenset()):
    p = net.pipes; up = p.up.to_numpy(); dn = p.dn.to_numpy(); L = p.length_m.to_numpy(float)
    n = len(p); cb = np.zeros(n); cl = np.zeros(n); ct = np.zeros(n)
    acc_b, acc_l, acc_t = {}, {}, dict(transfer_m3d)
    lifts = []
    for k in net.order:
        u = up[k]
        cb[k] = base_m3d.get(u, 0.0) + acc_b.get(u, 0.0)
        cl[k] = L[k] + acc_l.get(u, 0.0)
        ct[k] = acc_t.get(u, 0.0)
        d = dn[k]
        if k in cut:
            qk = cb[k] * peaking.factor(cb[k] / 86.4) + cl[k] / 1000.0 * inf_m3d_per_km + ct[k]
            acc_t[d] = acc_t.get(d, 0.0) + qk; lifts.append((int(k), int(d), float(qk)))
        else:
            acc_b[d] = acc_b.get(d, 0.0) + cb[k]; acc_l[d] = acc_l.get(d, 0.0) + cl[k]; acc_t[d] = acc_t.get(d, 0.0) + ct[k]
    q = cb * peaking.factor(cb / 86.4) + cl / 1000.0 * inf_m3d_per_km + ct
    return q, lifts
