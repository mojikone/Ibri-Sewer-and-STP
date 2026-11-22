"""The app's model: a case (scenario x design year) as its final named network (W18's design, as laid), and scenarios
that are a case plus a list of edits (undo/redo, copy, compare).

Instant re-run, the rule (spec section 8): flows are solved on the network as W18 designed it (the in-process engine,
equal to W18 on every pipe) with each lift's peak as a transfer; velocity and d/D are solved on each pipe at its LAID
gradient with inverts HELD. A pipe whose size or gradient is edited, and every pipe downstream of it, is flagged
needs_relay until the design chain is run again. Gravity joins carry their outfall's flow as a transfer, as W18 and
SewerGEMS do."""
import copy, json, time
import numpy as np, pandas as pd
from sewerapp import fixtures
from sewerapp.engine import analysis, flows, peaking
from sewerapp.model.network import Network

CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]
EDITABLE = {"pipe": {"dn_mm": int, "s_pc": float}, "node": {"load_factor": float}}
_NET = None


def base_network():
    global _NET
    if _NET is None:
        _NET = Network.from_w18(fixtures.read_csv("inputs/conduits_network.csv"), fixtures.read_csv("inputs/manholes_network.csv"))
    return _NET


class Case:
    """One of W18's 12 final designs, read from its frozen named outputs."""

    def __init__(self, case):
        self.case = case; self.year = case.split("-")[1]
        net = base_network(); self.net = net
        k = fixtures.read_csv(f"golden/{case}/named/links.csv")
        n = fixtures.read_csv(f"golden/{case}/named/nodes.csv")
        cat = fixtures.read_csv("inputs/catalogue.csv").set_index("nominal_mm").inside_mm / 1000.0
        self.catalogue = cat
        self.nodes = n.set_index("new")
        id_of = self.nodes.id.to_dict()
        k = k.reset_index(drop=True)
        k["up_id"] = k.from_mh.map(id_of); k["dn_id"] = k.to_mh.map(id_of)
        k["s"] = k.s_new_pc / 100.0
        k["ground_up"] = k.from_mh.map(self.nodes.ground); k["ground_dn"] = k.to_mh.map(self.nodes.ground)
        k["source"] = np.where(k.kind == "gravity join", k.old.str.split("->").str[0], "")
        pos = pd.Series(net.pipes.index, index=net.pipes.label)
        k["netpos"] = k.old.map(pos)                                   # NaN for a gravity join
        self.links = k
        nxt = dict(zip(k.from_mh, k.index))
        self.next_pipe = np.array([nxt.get(t, -1) for t in k.to_mh])   # the pipe leaving each pipe's downstream manhole
        loads = fixtures.read_csv("inputs/manhole_loads.csv", index_col="manhole_id")
        self.years = [self.year, "2031"]
        self.loads = {y: loads[f"Q_{y}"].to_dict() for y in self.years}
        tr = fixtures.read_csv(f"golden/{case}/exports/transfers_{case}.csv")
        self.transfers = {y: tr[tr.year == int(y)].groupby("receiver_id").flow_m3d.sum().to_dict() for y in self.years}
        self.source_q = {y: tr[tr.year == int(y)].set_index("source").flow_m3d.to_dict() for y in self.years}
        cuts = fixtures.read_csv(f"golden/{case}/split/cuts_{case}.csv")["pipe"]
        self.cut = set(np.flatnonzero(net.pipes.label.isin(cuts).values))
        self.stations = fixtures.read_csv(f"golden/{case}/products/stations.csv")
        self.quantities = json.load(open(fixtures.path(f"golden/{case}/products/quantities.json")))
        self.pk = peaking.PeakingTable(peaking.IBRI_PELTIER100_MERRIMACK)


class Scenario:
    def __init__(self, sid, name, case, edits=None, parent=None):
        self.id, self.name, self.case, self.parent = sid, name, case, parent
        self.edits = list(edits or []); self.redo = []

    def to_dict(self):
        return dict(id=self.id, name=self.name, case=self.case.case, parent=self.parent, edits=len(self.edits),
                    can_undo=bool(self.edits), can_redo=bool(self.redo))


def solve(case, edits):
    """Apply the edits to a copy of the case and solve; returns (results DataFrame, summary dict)."""
    t0 = time.perf_counter()
    k = case.links.copy(); factor = {}
    relay = np.zeros(len(k), bool)
    for e in edits:
        if e["target"] == "pipe":
            for i in e["ids"]:
                if e["field"] == "dn_mm": k.at[i, "dn_mm"] = int(e["value"])
                elif e["field"] == "s_pc": k.at[i, "s"] = float(e["value"]) / 100.0
                j = i
                while j >= 0 and not relay[j]: relay[j] = True; j = case.next_pipe[j]
        elif e["target"] == "node":
            for nid in e["ids"]: factor[int(nid)] = factor.get(int(nid), 1.0) * float(e["value"])
    inside = k.dn_mm.map(case.catalogue).values
    out = {}
    for y in case.years:
        base = case.loads[y]
        if factor: base = {n: q * factor.get(n, 1.0) for n, q in base.items()}
        q_net, _ = flows.accumulate(case.net, base, case.transfers[y], case.pk, 0.72, case.cut)
        q = np.where(k.netpos.notna(), q_net[k.netpos.fillna(0).astype(int).values], k.source.map(case.source_q[y]).fillna(0).values)
        a = analysis.analyse(q, inside, k.s.values, k.dn_mm.values)
        out[y] = a
    d, c = out[case.year], out["2031"]
    big = k.dn_mm.values > 200
    res = pd.DataFrame(dict(label=k.new, kind=k.kind, section=k.section, dn_mm=k.dn_mm, length_m=k.length_m,
                            s_pc=k.s * 100, q_ls=d.flow_m3d / 86.4, v_ms=d.velocity_ms, d_over_D=d.d_over_D,
                            limit=d.limit, over_limit=d.over_limit, over_3ms=d.over_3ms, q2031_ls=c.flow_m3d / 86.4,
                            v2031_ms=c.velocity_ms, under075=big & (c.velocity_ms.round(2) < 0.75),
                            depth_up_m=k.depth_up_m, depth_dn_m=k.depth_dn_m, needs_relay=relay,
                            from_mh=k.from_mh, to_mh=k.to_mh))
    summary = dict(pipes=len(res), km=round(res.length_m.sum() / 1000, 2), over_limit=int(res.over_limit.sum()),
                   over_3ms=int(res.over_3ms.sum()), km_under075_2031=round(float(res.length_m[res.under075].sum() / 1000), 2),
                   needs_relay=int(relay.sum()), seconds=round(time.perf_counter() - t0, 3), year=case.year)
    return res, summary


class Project:
    def __init__(self):
        self._cases = {}; self.scenarios = {}
        for c in CASES: self.scenarios[c] = Scenario(c, c, None)
        self._n = 0; self._cache = {}

    def case(self, name):
        if name not in self._cases: self._cases[name] = Case(name)
        return self._cases[name]

    def scenario(self, sid):
        s = self.scenarios[sid]
        if s.case is None: s.case = self.case(sid)
        return s

    def results(self, sid):
        s = self.scenario(sid); key = (sid, json.dumps(s.edits))
        if key not in self._cache: self._cache = {key: solve(s.case, s.edits), **{k: v for k, v in list(self._cache.items())[-20:]}}
        return self._cache[key]

    def edit(self, sid, target, ids, field, value):
        if field not in EDITABLE.get(target, {}): raise ValueError(f"{target}.{field} is not editable")
        s = self.scenario(sid)
        if s.parent is None and sid in CASES: raise ValueError("a W18 case is read only: copy it to a what-if first")
        s.edits.append(dict(target=target, ids=[int(i) for i in ids], field=field, value=value)); s.redo = []
        return self.results(sid)

    def undo(self, sid):
        s = self.scenario(sid)
        if s.edits: s.redo.append(s.edits.pop())
        return self.results(sid)

    def redo_(self, sid):
        s = self.scenario(sid)
        if s.redo: s.edits.append(s.redo.pop())
        return self.results(sid)

    def copy(self, sid, name=None):
        s = self.scenario(sid); self._n += 1
        new = f"W{self._n}"
        self.scenarios[new] = Scenario(new, name or f"{s.name} what-if {self._n}", s.case, copy.deepcopy(s.edits), parent=sid)
        return self.scenarios[new]

    def compare(self, a, b):
        ra, sa = self.results(a); rb, sb = self.results(b)
        d = pd.DataFrame(dict(label=ra.label, dv=rb.v_ms - ra.v_ms, d_dd=rb.d_over_D - ra.d_over_D,
                              dq=rb.q_ls - ra.q_ls, ddn=rb.dn_mm - ra.dn_mm))
        changed = d[(d.dv.abs() > 1e-9) | (d.d_dd.abs() > 1e-9) | (d.dq.abs() > 1e-9) | (d.ddn != 0)]
        return dict(a=sa, b=sb, changed=int(len(changed)), rows=changed.head(500).round(4).to_dict("records"))

    def profile(self, sid, start, end=None):
        """Pipes from manhole `start` downstream to `end` (or the outfall): chainage, ground, invert, crown, water."""
        res, _ = self.results(sid); s = self.scenario(sid); k = s.case.links; nodes = s.case.nodes
        first = k.index[k.from_mh == start]
        if not len(first): raise ValueError(f"no pipe leaves {start}")
        i = int(first[0]); rows = []; ch = 0.0
        while i >= 0:
            r = res.iloc[i]; D = s.case.catalogue[int(r.dn_mm)]
            gu, gd = nodes.ground.get(r.from_mh, np.nan), nodes.ground.get(r.to_mh, np.nan)
            iu, idn = gu - r.depth_up_m, gd - r.depth_dn_m
            rows.append(dict(pipe=r.label, from_mh=r.from_mh, to_mh=r.to_mh, ch0=round(ch, 2), ch1=round(ch + r.length_m, 2),
                             ground0=gu, ground1=gd, inv0=iu, inv1=idn, crown0=iu + D, crown1=idn + D,
                             water0=iu + r.d_over_D * D, water1=idn + r.d_over_D * D, dn_mm=int(r.dn_mm),
                             v_ms=round(float(r.v_ms), 3), needs_relay=bool(r.needs_relay)))
            ch += r.length_m
            if r.to_mh == end: break
            i = int(s.case.next_pipe[i])
        return rows
