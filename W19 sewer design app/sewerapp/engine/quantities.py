"""Quantities of a scenario, in the structure of the team's bill of quantities (W18 `py/final_boq.py`):

- pipes by size, and by size and depth band, the depth of a pipe being the deeper of its two ends (ground minus the
  pipe's own invert there), in the BOQ's bands: up to 1.5 m, then every 0.5 m to 15 m, then over 15 m;
- manholes by depth band (ground minus invert) and by type, the type set by the largest conduit at the manhole:
  up to DN355 Type 1 (1,200 mm), up to DN560 Type 2 (1,500 mm), above Type 3 (1,800 mm);
- pumps, wet wells and outfalls counted.
Quantities only: the team's rates stay in their workbook and are not read here."""
import math
import numpy as np, pandas as pd

MH_TYPES = [(355, "Type 1 - 1200 mm"), (560, "Type 2 - 1500 mm"), (float("inf"), "Type 3 - 1800 mm")]


def band(d):
    """The BOQ's depth band of a depth in metres (W18 final_boq.band, upper edge inclusive)."""
    if d is None or d != d: return "no level"
    if d <= 1.5: return "Up to 1.5"
    if d > 15: return "Over 15.0"
    a = math.floor(d * 2) / 2 if (d * 2) % 1 else d - 0.5
    return f"{a:.1f} - {a + 0.5:.1f}"


def _band_key(b):
    if b == "Up to 1.5": return -1.0
    if b == "Over 15.0": return 99.0
    if b == "no level": return 999.0
    return float(b.split(" - ")[0])


def mh_type(dn):
    for upto, name in MH_TYPES:
        if dn <= upto: return name


def quantities(p):
    L, N = p.links, p.nodes
    cond = L[L.kind == "conduit"].copy()
    g = N.ground.astype(float)
    cond["depth_max_m"] = np.fmax(g.reindex(cond.from_node).to_numpy() - cond.up_inv.astype(float).to_numpy(),
                                  g.reindex(cond.to_node).to_numpy() - cond.dn_inv.astype(float).to_numpy())
    cond["band"] = cond.depth_max_m.map(band)
    by_dn = cond.groupby("dn_mm").agg(count=("length_m", "size"), length_m=("length_m", "sum")).reset_index()
    by_band = cond.groupby(["dn_mm", "band"]).length_m.sum().reset_index()
    by_band["k"] = by_band.band.map(_band_key); by_band = by_band.sort_values(["dn_mm", "k"]).drop(columns="k")
    on = set(cond.from_node) | set(cond.to_node)
    mh = N[(N.kind == "manhole") & N.index.isin(list(on))].copy()          # manholes on a pipe: a lone one is not built
    mh["depth_m"] = (mh.ground - mh.invert).astype(float); mh["band"] = mh.depth_m.map(band)
    big = pd.concat([cond[["from_node", "dn_mm"]].rename(columns={"from_node": "n"}), cond[["to_node", "dn_mm"]].rename(columns={"to_node": "n"})])
    largest = big.groupby("n").dn_mm.max()
    mh["type"] = [mh_type(float(largest.get(i, 0) or 0)) for i in mh.index]
    by_mh = mh.groupby(["type", "band"]).size().rename("count").reset_index()
    by_mh["k"] = by_mh.band.map(_band_key); by_mh = by_mh.sort_values(["type", "k"]).drop(columns="k")
    pumps = L[L.kind == "pump"]
    totals = dict(pipes_km=round(float(cond.length_m.sum()) / 1000, 3), pipes=int(len(cond)), manholes=int(len(mh)),
                  wetwells=int((N.kind == "wetwell").sum()), outfalls=int((N.kind == "outfall").sum()), pumps=int(len(pumps)),
                  deepest_manhole=None if mh.depth_m.dropna().empty else str(mh.depth_m.idxmax()),
                  deepest_m=None if mh.depth_m.dropna().empty else round(float(mh.depth_m.max()), 2))
    rows = [dict(item=f"Pipe DN{int(r.dn_mm)}", band="all", unit="m", qty=round(float(r.length_m), 1), count=int(r["count"])) for _, r in by_dn.iterrows()]
    rows += [dict(item=f"Pipe DN{int(r.dn_mm)}", band=r.band, unit="m", qty=round(float(r.length_m), 1), count=None) for _, r in by_band.iterrows()]
    rows += [dict(item=f"Manhole {r.type}", band=r.band, unit="no", qty=int(r["count"]), count=None) for _, r in by_mh.iterrows()]
    rows += [dict(item=k, band="all", unit="no", qty=totals[k], count=None) for k in ("wetwells", "outfalls", "pumps") if totals[k]]
    return dict(totals=totals, rows=rows)
