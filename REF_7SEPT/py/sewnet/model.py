"""sewnet.model — the domain objects the whole pipeline passes around.

Before this module the network lived in raw dictionaries (a dict keyed by coordinate
tuples holding more dicts, and a list of pipe dicts). Every access was a string key,
every typo was silent, and no object owned the layout rules — which is exactly how
"two chambers at one physical point, each with its own outlet" stayed hidden.

Now:
  Chamber  — a manhole/structure: position, ground, invert, drops, role
  Reach    — one pipe between two chambers: geometry, diameter, slope, inverts, flow
  Network  — the collection plus the INVARIANTS (tree, one outlet per chamber)

Attribute names match the old dict keys on purpose, so stage code reads the same way.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

Key = Tuple[float, float]          # chamber identity = rounded (x, y)


def key_of(x: float, y: float) -> Key:
    """Chamber identity: coordinates rounded to the centimetre."""
    return (round(x, 2), round(y, 2))


@dataclass(eq=False)
class Chamber:
    x: float
    y: float
    z: float                        # ground level (m)
    kind: str = "junction"          # outfall | head | junction | spacing
    label: str = ""
    invert: Optional[float] = None  # designed invert = the OUTGOING pipe invert
    depth: Optional[float] = None   # ground - invert (construction depth)
    drops: List[dict] = field(default_factory=list)
    sls_pocket: bool = False
    is_station: bool = False        # a pumping station sits here
    on_trunk: bool = False          # this chamber sits on the main pipe
    subnet: int = 0                 # which subnetwork it drains through
    sharp_inlet: bool = False       # a pipe arrives under the inlet-angle rule
    lift_m: float = 0.0             # how far the pump must raise the sewage
    min_depth_req: float = 0.0      # raised by the connectability stage

    @property
    def key(self) -> Key:
        return key_of(self.x, self.y)

    @property
    def xy(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass(eq=False)
class Reach:
    up: Key
    dn: Key
    geom: Any                       # shapely LineString, digitised up -> dn
    length: float
    label: str = ""
    dn_mm: int = 200                # designed diameter
    material: str = ""
    slope: float = 0.0              # laid gradient (m/m)
    inv_up: Optional[float] = None
    inv_dn: Optional[float] = None
    drop_up: float = 0.0            # fall taken at the upstream chamber
    drop_dn: float = 0.0            # arrival above the downstream chamber invert
    s_rec: float = 0.0              # terrain recovery slope (diagnostic)
    n_props: float = 0.0            # accumulated properties
    qadf_m3d: float = 0.0
    infil_m3d: float = 0.0
    uplen_m: float = 0.0            # upstream network length (drives infiltration)
    pf: float = 1.0
    pf_merrimack: float = 1.0
    pf_peltier: float = 1.0
    qpeak_m3s: float = 0.0
    qpeak_ls: float = 0.0
    dod: Optional[float] = None     # proportional depth at design flow
    vel: Optional[float] = None
    profile: List[tuple] = field(default_factory=list)   # (chainage, x, y, ground)
    dn_hist: set = field(default_factory=set)            # oscillation guard
    is_rising_main: bool = False    # pumped, not gravity
    q_duty_m3s: float = 0.0         # pump duty flow (rising mains only)
    on_trunk: bool = False          # this pipe IS the main pipe
    subnet: int = 0                 # which subnetwork it belongs to
    tier: str = "lateral"           # trunk main / sub main / lateral
    is_connector: bool = False      # joins a side network onto the main pipe
    is_crossing: bool = False       # crosses a dual carriageway

    @property
    def fall(self) -> float:
        if self.inv_up is None or self.inv_dn is None:
            return 0.0
        return self.inv_up - self.inv_dn


@dataclass(eq=False)
class LoadUnit:
    """A plot or unparceled building that discharges into the network."""
    id: Any
    x: float
    y: float
    cls: str                        # B built | P planned | U unparceled
    src: str
    chamber: Optional[Key] = None   # assigned chamber
    dist: float = 0.0               # distance to that chamber
    n_props: float = 1.0            # properties on this plot, counted from electricity accounts
    n_dom: float = 1.0              # of which homes
    n_nondom: float = 0.0           # of which shops, offices, government
    conn_x: float = 0.0             # where it joins the sewer (on the road, not in the plot)
    conn_y: float = 0.0
    conn_reach: Optional[int] = None
    conn_chainage: float = 0.0
    geom: Any = None                # the plot outline, so the spur starts at its edge


class Network:
    """Chambers + reaches, and the rules that must always hold."""

    def __init__(self, chambers: Dict[Key, Chamber] = None, reaches: List[Reach] = None,
                 outfall: Key = None):
        self.chambers: Dict[Key, Chamber] = chambers or {}
        self.reaches: List[Reach] = reaches or []
        self.outfall: Key = outfall

    # ---------------- construction ----------------
    def add_chamber(self, x, y, z, kind="junction") -> Key:
        k = key_of(x, y)
        if k not in self.chambers:
            self.chambers[k] = Chamber(x=x, y=y, z=z, kind=kind)
        return k

    def add_reach(self, up: Key, dn: Key, geom, length=None) -> Reach:
        r = Reach(up=up, dn=dn, geom=geom,
                  length=geom.length if length is None else length)
        self.reaches.append(r)
        return r

    def remove_reach(self, r: Reach) -> None:
        self.reaches.remove(r)

    # ---------------- views ----------------
    def digraph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for k in self.chambers:
            G.add_node(k)
        for r in self.reaches:
            G.add_edge(r.up, r.dn, reach=r)
        return G

    def outgoing(self) -> Dict[Key, List[Reach]]:
        out: Dict[Key, List[Reach]] = {}
        for r in self.reaches:
            out.setdefault(r.up, []).append(r)
        return out

    def incoming(self) -> Dict[Key, List[Reach]]:
        inc: Dict[Key, List[Reach]] = {}
        for r in self.reaches:
            inc.setdefault(r.dn, []).append(r)
        return inc

    def degrees(self) -> Tuple[Dict[Key, int], Dict[Key, int]]:
        ind: Dict[Key, int] = {k: 0 for k in self.chambers}
        outd: Dict[Key, int] = {k: 0 for k in self.chambers}
        for r in self.reaches:
            outd[r.up] = outd.get(r.up, 0) + 1
            ind[r.dn] = ind.get(r.dn, 0) + 1
        return ind, outd

    def heads(self) -> List[Key]:
        ind, outd = self.degrees()
        return [k for k in self.chambers
                if ind.get(k, 0) == 0 and outd.get(k, 0) == 1
                and self.chambers[k].kind != "outfall"]

    def refresh_kinds(self) -> None:
        ind, _ = self.degrees()
        for k, c in self.chambers.items():
            if c.kind == "outfall":
                continue
            if ind.get(k, 0) == 0:
                c.kind = "head"
            elif c.kind != "spacing":
                c.kind = "junction"

    def drop_orphans(self) -> int:
        used = set()
        for r in self.reaches:
            used.add(r.up)
            used.add(r.dn)
        gone = [k for k in self.chambers
                if k not in used and self.chambers[k].kind != "outfall"]
        for k in gone:
            del self.chambers[k]
        return len(gone)

    # ---------------- invariants (the two binding layout rules) ----------------
    def assert_one_outlet(self) -> None:
        _, outd = self.degrees()
        bad = [k for k, d in outd.items() if d > 1]
        if bad:
            raise AssertionError(f"{len(bad)} chambers have more than one outlet "
                                 f"(first: {self.chambers[bad[0]].label or bad[0]})")

    def assert_tree(self) -> None:
        G = self.digraph()
        if not nx.is_directed_acyclic_graph(G):
            raise AssertionError("network contains a loop")
        self.assert_one_outlet()

    def check(self) -> None:
        self.assert_tree()

    # ---------------- convenience ----------------
    def __len__(self) -> int:
        return len(self.reaches)

    def summary(self) -> dict:
        return {"chambers": len(self.chambers), "reaches": len(self.reaches),
                "length_km": sum(r.length for r in self.reaches) / 1000.0}

    def fingerprint(self) -> list:
        """Canonical, order-independent signature of the DESIGN — used by the
        refactor equality gate. Label- and order-agnostic on purpose."""
        out = []
        for r in self.reaches:
            out.append((round(r.up[0], 2), round(r.up[1], 2),
                        round(r.dn[0], 2), round(r.dn[1], 2),
                        int(r.dn_mm), round(r.slope, 6),
                        round(r.inv_up, 3) if r.inv_up is not None else None,
                        round(r.inv_dn, 3) if r.inv_dn is not None else None))
        return sorted(out)
