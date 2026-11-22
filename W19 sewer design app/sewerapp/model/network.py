"""A gravity network as two tables and a topological order. Flow direction is from the higher invert to the lower
(W18's rule: a conduit's start and stop need not follow the flow)."""
from dataclasses import dataclass, field
import numpy as np, pandas as pd


@dataclass
class Network:
    pipes: pd.DataFrame
    nodes: pd.DataFrame
    order: np.ndarray
    terminals: set = field(default_factory=set)

    @classmethod
    def from_w18(cls, conduits, manholes):
        d = conduits[conduits.active == True].copy().reset_index(drop=True)
        hi_start = d.start_inv >= d.stop_inv
        d["up"] = np.where(hi_start, d.start, d.stop); d["dn"] = np.where(hi_start, d.stop, d.start)
        d["nominal_mm"] = d.size_label.str.extract(r"(\d+)")[0].astype(int)
        d["inside_m"] = d.diameter_mm / 1000.0
        d["slope"] = (d[["start_inv", "stop_inv"]].max(axis=1) - d[["start_inv", "stop_inv"]].min(axis=1)) / d.length_m
        d["sub"] = d.label.str.split("-").str[0]
        nodes = manholes.set_index("id")[["label", "x", "y", "ground"]]
        return cls(d, nodes, topo_order(d.up.to_numpy(), d.dn.to_numpy()), set(d.dn) - set(d.up))

    def downstream_of(self, k):
        """Positions of pipe k and every pipe below it, to the outfall."""
        leaving = dict(zip(self.pipes.up, self.pipes.index)); out = []
        while k is not None:
            out.append(int(k)); k = leaving.get(self.pipes.dn.iat[k])
        return out


def topo_order(up, dn):
    """Kahn's order: a pipe once every pipe arriving at its upstream node is placed."""
    arriving = pd.Series(dn).value_counts().to_dict()
    leaving = {u: k for k, u in enumerate(up)}
    if len(leaving) != len(up): raise ValueError("a node has more than one leaving pipe")
    ready = [k for k, u in enumerate(up) if u not in arriving]
    left = dict(arriving); order = []
    while ready:
        k = ready.pop(); order.append(k); n = dn[k]
        if n in left:
            left[n] -= 1
            if left[n] == 0 and n in leaving: ready.append(leaving[n])
    if len(order) != len(up): raise ValueError(f"not a tree: {len(up) - len(order)} pipes unordered")
    return np.array(order)
