"""People and average sewage flow of every plot for every five-year step, on the plot layer of the
meeting folder (engineer, 2026-09-30).

    python plot_years.py            extends  W16/Meeting 2026-09-16/03_Plots_meters/Plots.shp  in place
    python plot_years.py --check    also compares the layer with the five-year tables of the concept report R3

The layer gains POP_ and Q_ for 2024, 2025, 2030, 2035 ... 2065 and saturation (2070), and
FULL_YEAR, POP_FULL, Q_FULL: the year the plot's settlement is full and the plot's values in it.
Nothing is modelled here. The rule is the one behind the 2030, 2055 and saturation columns of the
frozen W14 layer (W14/py/growth_by_settlement.py):

    a plot that takes no growth (built, or not a home plot) keeps its 2024 people and flow;
    an empty plot takes its share of the people its settlement has housed by that year, the
    overflow it received included, by plot area capped at 1,000 m2 (SPREAD_W);
    a new person adds Q_PER_CAP of average sewage flow.

The settlement series is W14/analysis/W14_growth_by_settlement.xlsx, the file the report's
five-year tables are printed from.

ROUNDING. People to 2 decimals, flow to 4 (engineer). Thousands of empty plots hold equal shares,
and rounded one by one they would all round the same way: a settlement's column would then miss
its own total by tens of people. The values are therefore rounded together, settlement by
settlement and year by year, so that every plot is within one unit of the last decimal of its
value, every settlement column sums to the settlement's figure exactly, and no plot goes down
from one year to the next.
"""
import os
import shutil
import sys

import fiona
import numpy as np
import pandas as pd
import geopandas as gpd

HERE = os.path.dirname(os.path.abspath(__file__))
W16 = os.path.dirname(HERE)
REPO = os.path.dirname(W16)
W14 = os.path.join(REPO, "W14")
LAYER = os.path.join(W16, "Meeting 2026-09-16", "03_Plots_meters", "Plots.shp")
SERIES = os.path.join(W14, "analysis", "W14_growth_by_settlement.xlsx")
REPORT = os.path.join(W16, "report", "R3", "Ibri_Concept_Design_Report_R3.docx")

LPCD, R_ND, R_GOV, RET_DOM, RET_ND = 164.0, 0.22, 0.14, 0.85, 0.54            # = growth_by_settlement.py
Q_PER_CAP = LPCD * (RET_DOM + R_ND * RET_ND + R_GOV * RET_ND) / 1000.0        # m3/d for a person on a future plot
BASE = 2024
POP_DEC, Q_DEC = 2, 4


def years(ult):
    return [BASE, 2025] + [y for y in range(2030, ult, 5)] + [ult]


def tag(y, ult):
    return "SAT" if y == ult else str(y)


def fit(true, target, prev=None):
    """Whole units for each value of `true` (already in units of the last decimal) that sum to `target`,
    each the floor or the ceiling of its value, none below `prev`. The units left over after the floors
    go to the values that must not fall, then to the largest remainders."""
    f = np.floor(true + 1e-7).astype(np.int64)
    rem = true - f
    out = f.copy()
    k = int(target - f.sum())
    if prev is not None:
        held = prev > f                       # rounded up before and still below the next unit: stays up
        out[held] += 1; k -= int(held.sum())
    else:
        held = np.zeros(len(f), bool)
    if k > 0:
        free = np.where(~held)[0]
        pick = free[np.argsort(-rem[free], kind="stable")[:k]]
        out[pick] += 1; k -= len(pick)
    elif k < 0:                                # more held up than the total allows: the smallest remainders come down
        up = np.where(out > f)[0]
        drop = up[np.argsort(rem[up], kind="stable")[:-k]]
        out[drop] -= 1; k += len(drop)
    return out, k                              # k = units that could not be placed (0 when the fit is exact)


def compute():
    """The W14 plots in their row order with the rounded year columns, and a record of the fit."""
    P = gpd.read_file(os.path.join(W14, "shp", "PLOTS_load.shp"), ignore_geometry=True)
    pt = pd.read_excel(SERIES, sheet_name="Population by year", index_col=0)
    pt.columns = [int(c) for c in pt.columns]
    ult = int(P.ULT_YEAR.iloc[0]); yrs = years(ult)
    sat = P.groupby("SETTLE").SAT_YEAR.first()
    grows = (P.SPREAD_W > 0).values
    out = pd.DataFrame(index=P.index)
    log = {"ult": ult, "years": yrs, "unplaced": 0, "max_err_pop": 0.0, "max_err_q": 0.0, "falls": 0, "full_differs": []}
    cols = {(k, y): np.zeros(len(P)) for k in ("POP", "Q") for y in yrs + ["FULL"]}

    for s, idx in P.groupby("SETTLE").indices.items():
        g = P.iloc[idx]; dyn = grows[idx]; w = g.SPREAD_W.values; W = w.sum()
        pop0 = float(g.POP.sum()); q0 = float(g.QADF.sum())
        step_years = yrs + ([int(sat[s])] if int(sat[s]) not in yrs and int(sat[s]) > 0 else [])
        for kind, base, per, dec in (("POP", g.POP.values, 1.0, POP_DEC), ("Q", g.QADF.values, Q_PER_CAP, Q_DEC)):
            u = 10 ** dec
            tot0 = pop0 if kind == "POP" else q0
            # the plots that take no growth: rounded once, the same in every year
            static_t = int(round(tot0 * u)) - int(round(base[dyn].sum() * u))
            st_units, left = fit(base[~dyn] * u, static_t)
            log["unplaced"] += abs(left)
            prev = None; res = {}
            for y in sorted(step_years):
                housed = 0.0 if y == BASE else max(float(pt.at[s, y]) - pop0, 0.0)
                true = (base[dyn] + (housed * w[dyn] / W if W > 0 else 0.0) * per) * u
                if kind == "POP":                 # the settlement's people as the series holds them, to the hundredth
                    total = int(round(pop0 * u)) if y == BASE else int(round(float(pt.at[s, y]) * u))
                else:
                    total = int(round((q0 + housed * per) * u))
                dy_units, left = fit(true, total - int(st_units.sum()), prev)
                log["unplaced"] += abs(left)
                if prev is not None:
                    log["falls"] += int((dy_units < prev).sum())
                err = float(np.abs(dy_units - true).max()) / u if len(true) else 0.0
                log["max_err_pop" if kind == "POP" else "max_err_q"] = max(log["max_err_pop" if kind == "POP" else "max_err_q"], err)
                v = np.zeros(len(g)); v[dyn] = dy_units / u; v[~dyn] = st_units / u
                res[y] = v; prev = dy_units
            for y in yrs:
                cols[(kind, y)][idx] = res[y]
            fy = int(sat[s]) if int(sat[s]) > 0 else ult
            cols[(kind, "FULL")][idx] = res[fy]
            if kind == "POP" and abs(res[fy].sum() - res[ult].sum()) > 0.005:
                log["full_differs"].append((s, fy, round(res[fy].sum(), 2), round(res[ult].sum(), 2)))

    for y in yrs:
        out[f"POP_{tag(y, ult)}"] = np.round(cols[("POP", y)], POP_DEC)
    for y in yrs:
        out[f"Q_{tag(y, ult)}"] = np.round(cols[("Q", y)], Q_DEC)
    out["SAT_YEAR"] = P.SAT_YEAR.astype(int).values
    out["FULL_YEAR"] = np.where(P.SAT_YEAR.values > 0, P.SAT_YEAR.values, ult).astype(int)
    out["POP_FULL"] = np.round(cols[("POP", "FULL")], POP_DEC)
    out["Q_FULL"] = np.round(cols[("Q", "FULL")], Q_DEC)
    # the stored design years of W14, for the check
    for y, t in ((2030, "2030"), (2055, "2055"), (ult, "ULT")):
        log[f"dev_pop_{t}"] = float(np.abs(out[f"POP_{tag(y, ult)}"].values - P[f"POP_{t}"].values).max())
        log[f"dev_q_{t}"] = float(np.abs(out[f"Q_{tag(y, ult)}"].values - P[f"Q_{t}"].values).max())
    return P, out, log


def extend(layer=LAYER):
    """Rewrite the plot layer with the year columns. The plots, their order and every other field stay."""
    P, new, log = compute()
    ult = log["ult"]
    tmp = os.path.join(os.path.dirname(layer), "_Plots_years_tmp.shp")
    year_cols = list(new.columns)
    with fiona.open(layer) as src:
        if len(src) != len(P):
            raise RuntimeError(f"{len(src)} plots in the layer, {len(P)} in W14")
        keep = [(k, v) for k, v in src.schema["properties"].items()
                if not (k.startswith("POP_") or k.startswith("Q_") or k in ("SAT_YEAR", "FULL_YEAR"))]
        props = dict(keep)
        for c in year_cols:
            props[c] = "int:4" if c.endswith("_YEAR") else (f"float:10.{POP_DEC}" if c.startswith("POP_") else f"float:11.{Q_DEC}")
        schema = {"geometry": src.schema["geometry"], "properties": props}
        area = P.AREA_M2.round(1).values
        vals = {c: new[c].values for c in year_cols}
        with fiona.open(tmp, "w", driver="ESRI Shapefile", crs=src.crs, schema=schema, encoding="UTF-8") as dst:
            for i, f in enumerate(src):
                a = f["properties"]
                if a["PLOT_NO"] != i + 1 or abs(float(a["AREA_M2"]) - area[i]) > 0.06:
                    raise RuntimeError(f"row {i + 1}: the layer and W14 are not in the same order")
                rec = {k: a[k] for k, _ in keep}
                for c in year_cols:
                    rec[c] = int(vals[c][i]) if c.endswith("_YEAR") else float(vals[c][i])
                dst.write({"type": "Feature", "geometry": f["geometry"], "properties": rec})
    base = os.path.splitext(layer)[0]; tb = os.path.splitext(tmp)[0]
    for e in ("shp", "shx", "dbf", "prj", "cpg"):
        if os.path.exists(tb + "." + e):
            os.replace(tb + "." + e, base + "." + e)       # raises if QGIS holds the layer open
    print(f"wrote {layer}: {len(P):,} plots, {len(keep) + len(year_cols)} fields; years {log['years']}")
    return log


def totals(layer=LAYER):
    g = gpd.read_file(layer, ignore_geometry=True)
    return g, g.groupby("SETTLE")[[c for c in g.columns if c.startswith("POP_") or c.startswith("Q_")]].sum()


def check_report(layer=LAYER, report=REPORT):
    """The layer against the two five-year tables of the concept report, every printed cell: the year
    columns, "Full in" (the year the settlement is full) and "At saturation" (its value when full).
    The report prints whole people and whole m3/d; a settlement's column of the layer must round to it."""
    from docx import Document
    g, by = totals(layer)
    full_year = g.groupby("SETTLE").FULL_YEAR.first()
    d = Document(report); found = 0; bad = []; twice = []
    for t in d.tables:
        head = [c.text.strip() for c in t.rows[0].cells]
        if "2025" not in head or "2030" not in head:
            continue
        found += 1
        body = [[c.text.strip() for c in r.cells] for r in t.rows[1:]]
        kind = "POP" if float(next(r for r in body if r[0] == "Ibri")[1].replace(",", "")) > 40000 else "Q"
        n = 0
        for r in body:
            name = r[0]
            if name != "Total" and name not in by.index:
                bad.append((kind, name, "settlement not in the layer")); continue
            for h, cell in zip(head[1:], r[1:]):
                if not cell:
                    continue                                  # blank after the settlement is full
                want = float(cell.replace(",", "")); n += 1
                if h.isdigit():
                    col = f"{kind}_{h}" if f"{kind}_{h}" in by.columns else f"{kind}_SAT"
                    have = float(by[col].sum() if name == "Total" else by.at[name, col])
                elif h == "Full in":
                    have = float(full_year.max() if name == "Total" else full_year[name])
                else:                                         # "At saturation"
                    have = float(by[f"{kind}_FULL"].sum() if name == "Total" else by.at[name, f"{kind}_FULL"])
                if abs(have - want) <= 0.5 + 1e-6:
                    continue
                # the report prints its flow table from the series kept to one decimal (W14, "Five-year Qadf"),
                # so a figure ending in .45 to .49 is printed one above what the unrounded figure rounds to
                one = np.floor(have * 10 + 0.5 + 1e-7) / 10
                (twice if np.floor(one + 0.5 + 1e-7) == want else bad).append((kind, name, h, cell, round(have, 4)))
        print(f"report table, {'people' if kind == 'POP' else 'flow, m3/d'}: {len(body)} rows, {n} printed cells compared")
    print(f"{found} five-year tables found in the report")
    print(f"cells the layer does not reproduce: {bad if bad else 'none'}")
    print(f"cells printed 1 above the layer because the report rounds a one-decimal figure: {len(twice)}")
    for r in twice:
        print("   ", r)
    return bad, twice


if __name__ == "__main__":
    if "--check-only" not in sys.argv:
        log = extend()
        print({k: v for k, v in log.items() if k != "years"})
    if "--check" in sys.argv or "--check-only" in sys.argv:
        check_report()
