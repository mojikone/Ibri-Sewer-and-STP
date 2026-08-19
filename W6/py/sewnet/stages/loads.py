"""LoadAllocator — S4: saturation loads per plot, assignment, accumulation down the tree.

Doctrine (PROJECT-STATE §2, binding): EVERY plot — built (B) + planned (P) + unparceled
buildings — carries full saturation load; CLASS=A farms carry NO sewage load (they are TE
customers). Zero silent drops: every loaded unit lands on exactly one chamber or appears
in the report.

Peak factor is applied to the ACCUMULATED flow at each reach (not per plot); infiltration
is 720 L/d per km of UPSTREAM network, added unpeaked (G1-p72-73; add-order [Likely], a
kickoff item).
"""

import geopandas as gpd
import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from ..criteria import DEFAULT
from ..model import LoadUnit, Network


class LoadAllocator:
    def __init__(self, crit=DEFAULT, pf_formula="merrimack"):
        self.crit = crit
        self.pf_formula = pf_formula
        self.report = {}

    # ---------------- inputs ----------------
    def load_units(self, plots_path, unparceled_path, boundary, accounts_path=None):
        """Build the list of things that produce sewage.

        A plot no longer counts as one property. Electricity accounts are counted instead:
        a plot with 3 accounts holds 3 properties (user 2026-08-19). Account types also
        tell us what KIND of load it is, so the non-domestic share is identified rather
        than guessed from a percentage.

        Farms: the farming itself sends nothing to the sewer, but houses on a farm plot
        do — so a farm plot with domestic accounts is loaded (doctrine narrowed
        2026-08-19)."""
        return self._load_units(plots_path, unparceled_path, boundary, accounts_path)

    def _load_units(self, plots_path, unparceled_path, boundary, accounts_path=None):
        plots = gpd.read_file(plots_path, encoding="utf-8")
        plots = plots[plots.geometry.notna()]
        inside = plots[plots.geometry.representative_point().within(boundary)].copy()
        farms = inside[inside["CLASS"] == "A"]
        loaded = inside[inside["CLASS"].isin(("B", "P"))].copy()
        n_other = len(inside) - len(farms) - len(loaded)   # review F4: never vanish

        unp = gpd.read_file(unparceled_path)
        unp = unp[unp.geometry.notna()]
        unp_in = unp[unp.geometry.representative_point().within(boundary)].copy()

        C = self.crit
        # how many properties sit on each plot, counted from electricity accounts
        acc_by_plot, acc_kind, n_acc = {}, {}, 0
        if accounts_path:
            try:
                acc = gpd.read_file(accounts_path, encoding="utf-8")
                acc = acc[acc.geometry.notna()]
                acc = acc[acc.within(boundary)]
                n_acc = len(acc)
                for _, a in acc.iterrows():
                    pid = a.get("PLOT_ID")
                    tar = str(a.get("TARIFF", ""))
                    if pid is None or (isinstance(pid, float) and pid != pid):
                        continue
                    if tar in C.ACCOUNT_TARIFF_AGRI:
                        continue                       # farming itself sends nothing
                    acc_by_plot[pid] = acc_by_plot.get(pid, 0) + 1
                    kind = "domestic" if tar in C.ACCOUNT_TARIFF_DOMESTIC else "nondom"
                    acc_kind.setdefault(pid, {"domestic": 0, "nondom": 0})[kind] += 1
            except Exception as e:
                print(f"  (accounts unavailable, falling back to 1 property per plot: {e})")

        units = []
        counted = farm_dwell = 0
        # farm plots are back in the list: their houses do produce sewage
        allplots = inside[inside["CLASS"].isin(("B", "P", "A"))]
        for i, (_, row) in enumerate(allplots.iterrows()):
            oid = row.get("OBJECTID", i)
            k = acc_kind.get(oid)
            n_props = acc_by_plot.get(oid, 0)
            if row["CLASS"] == "A" and not (k and k["domestic"]):
                continue                               # a farm with no house on it
            if row["CLASS"] == "A":
                farm_dwell += 1
            if n_props == 0:
                n_props = C.PROPS_PER_PLOT             # no account: fall back to one
            else:
                counted += 1
            p = row.geometry.representative_point()
            units.append(LoadUnit(id=oid, x=p.x, y=p.y, cls=row["CLASS"], src="plot"))
            units[-1].geom = row.geometry
            units[-1].n_props = n_props
            units[-1].n_dom = (k or {}).get("domestic", n_props)
            units[-1].n_nondom = (k or {}).get("nondom", 0)
        for i, (_, row) in enumerate(unp_in.iterrows()):
            p = row.geometry.representative_point()
            u = LoadUnit(id=f"U{i}", x=p.x, y=p.y, cls="U", src="unparceled")
            u.n_props = C.PROPS_PER_PLOT
            u.n_dom, u.n_nondom = C.PROPS_PER_PLOT, 0
            units.append(u)

        tot_props = sum(u.n_props for u in units)
        self.report = {"plots_inside": len(inside), "built": int((inside["CLASS"] == "B").sum()),
                       "planned": int((inside["CLASS"] == "P").sum()),
                       "farm_plots": len(farms), "farm_plots_with_houses": farm_dwell,
                       "class_other": n_other, "unparceled": len(unp_in),
                       "loaded_points": len(units), "accounts_used": n_acc,
                       "plots_with_counted_props": counted,
                       "total_properties": round(tot_props, 1),
                       "props_per_unit": round(tot_props / max(len(units), 1), 2)}
        return units, self.report

    # ---------------- assignment ----------------
    def assign(self, units, net: Network):
        """Nearest-chamber assignment. No distance cutoff: every unit is assigned and the
        distances are reported, so outliers surface in the audit instead of disappearing
        (this replaces the W2 400 m silent-drop shortcut)."""
        keys = [k for k, c in net.chambers.items() if c.kind != "outfall"]
        arr = np.array([[net.chambers[k].x, net.chambers[k].y] for k in keys])
        tree = cKDTree(arr)
        dists, idx = tree.query(np.array([[u.x, u.y] for u in units]))
        per_chamber = {}
        for u, d, i in zip(units, dists, idx):
            u.chamber = keys[i]
            u.dist = float(d)
            per_chamber.setdefault(keys[i], []).append(u)
        return per_chamber, float(np.max(dists)) if len(dists) else 0.0

    # ---------------- accumulation ----------------
    def accumulate(self, net: Network, per_chamber):
        C = self.crit
        G = nx.DiGraph()
        for r in net.reaches:
            G.add_edge(r.up, r.dn, reach=r)

        # each unit carries its counted number of properties
        local = {k: sum(getattr(u, "n_props", 1.0) for u in per_chamber.get(k, []))
                 for k in G.nodes}
        carry_props = {k: 0.0 for k in G.nodes}
        carry_len = {k: 0.0 for k in G.nodes}
        for n in nx.topological_sort(G):
            total = carry_props[n] + local.get(n, 0)
            for _, dn, d in G.out_edges(n, data=True):
                r = d["reach"]
                r.n_props = total
                r.uplen_m = carry_len[n] + r.length
                carry_props[dn] += total
                carry_len[dn] += r.uplen_m

        hold_mld = C.PF_HOLD_PROPERTIES * C.PLOT_QADF_M3D / 1000.0
        hold_qm = C.PF_HOLD_PROPERTIES * C.PLOT_QADF_LS
        for r in net.reaches:
            r.qadf_m3d = r.n_props * C.PLOT_QADF_M3D
            r.infil_m3d = C.INFILT_L_D_KM * (r.uplen_m / 1000.0) / 1000.0
            r.pf_merrimack = C.pf_merrimack(max(r.qadf_m3d / 1000.0, hold_mld))
            r.pf_peltier = C.pf_peltier(max(r.qadf_m3d * 1000.0 / 86400.0, hold_qm))
            r.pf = r.pf_merrimack if self.pf_formula == "merrimack" else r.pf_peltier
            r.qpeak_m3s = (r.pf * r.qadf_m3d + r.infil_m3d) / 86400.0
            r.qpeak_ls = r.qpeak_m3s * 1000.0
        return net

    def run(self, net: Network, units):
        per_chamber, maxdist = self.assign(units, net)
        self.accumulate(net, per_chamber)
        return per_chamber, maxdist
