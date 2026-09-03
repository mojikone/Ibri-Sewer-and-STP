"""existing_network — the brownfield assessment of NAMA's built Ibri sewerage.

W11a asked for a greenfield design FIRST, deliberately ignoring what is in the ground.
This module is the other half: it measures what is actually built, what the greenfield
design duplicates, what it could reuse, and whether the built pipes can carry the load
the design puts on them at three horizons.

    python W11a/report/existing_network.py            # every table, then the two figures
    python W11a/report/existing_network.py --tables   # tables only, no figures

WHAT THIS MODULE WILL NOT DO, and why
-------------------------------------
*   It never quotes a length without first filtering ``STATUS``.  The asset GIS holds
    NAMA's built 2006 network AND an unapproved SUREKHA concept in the same layer, and
    the concept is 2.1x longer than the built network.  Every table below states which.
*   It never reads ``N_DIAMETER``.  That field is 0 on every built record while
    ``OUT_DIAMET`` carries the real value, and reading the wrong one is how this project
    concluded for three weeks that the built network has no diameters at all.
*   It computes hydraulics with the project's own validated module (``W8/py/sewnet``),
    Colebrook-White, ks = 1.5 mm (G203-p24, p28), so the capacity numbers here are on
    exactly the same basis as the design's.  ``internal_diameter()`` returns 150.6 mm for
    an OD160 pipe and NAMA's own ``IN_DIAMETE`` field says 150 — the bore is measured,
    not assumed.
*   A pipe with no recorded diameter or level is **UNTESTED**, never a pass.  1,123 of
    3,265 built pipes are in that state and they are 33.8 % of the built network.

READ THE SOURCES, NOT THE KMZ.  ``Data/.../WW/SHIP/*.shp`` is the complete delivery;
the KMZ copies in ``W7/shp/`` lose 74 of the 129 proposed gravity features, which is why
the "188.6 km as-built" carried since W7 is 111.6 km of built pipe plus 77.0 km of
unapproved concept.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figkit as fk                                              # noqa: E402

sys.path.insert(0, str(fk.ROOT / "W8" / "py"))
from sewnet.criteria import DEFAULT as C                         # noqa: E402
from sewnet.hydra import q_full, q_partial                       # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 60)

# ---------------------------------------------------------------- sources

SHIP = fk.BASE / "Data" / "Received" / "09-RECEIVED" / "NAMA" / "IBRI" / "WW" / "SHIP"
PLOT_LOADS = fk.ROOT / "W10" / "shp" / "W10_plot_loads.gpkg"
SKELETON = fk.RUN / "s5_reach_skeleton.gpkg"
FLOWS_CSV = "s5c_reach_flows.csv"

# ---------------------------------------------------------- project rules

#: A built record whose vertices are further apart than this is a SCHEMATIC line — one
#: polyline standing for a whole run — not surveyed manhole-to-manhole pipe.  The built
#: network's real pipes average one vertex every few metres; the two records this catches
#: sit at 317 m and 565 m per vertex.  PROJECT RULE, not a guideline value.
SCHEMATIC_VERTEX_SPACING_M = 100.0

#: A plot is within reach of a sewer if its boundary is no further than this.  It is the
#: guideline's own maximum LATERAL length, G203-p22 Tab 6, used here as a service radius.
SERVICE_RADIUS_M = 45.0

#: Two alignments are "the same street" within this.  PROJECT TOLERANCE: a road reserve is
#: 2.0-4.4 m of service corridor either side of the centreline (G203-p32 Tab 13), and the
#: built pipe and our corridor are both drawn to a centreline, so 12 m absorbs the offset
#: between two independent drawings of one street without merging two parallel streets.
SAME_STREET_M = 12.0

#: Fraction of the plots undeveloped today that are developed by 2055.  PROJECT
#: ASSUMPTION, derived in :func:`horizon_fractions` from published population figures.
#: It assumes growth in the built network's catchment tracks the whole-boundary ratio,
#: which W3/A2 says is false (IBRI loses ~43k to AT TAYYIB by 2055).
_F2055_SOURCE = "W10/docs/LOAD_ALLOCATION.md sec 6 and sec 7"


def horizon_fractions() -> dict:
    """The 2055 interpolation, with its arithmetic on the page.

    Population, all from ``W10/docs/LOAD_ALLOCATION.md``: built stock today
    (CLASS B 144,325 + CLASS U 14,837) = 159,162; cadastral saturation 435,945;
    NCSI/R0 2055 projection 237,885.  The share of today's undeveloped stock that is
    developed by 2055 is therefore (237,885 - 159,162) / (435,945 - 159,162).
    """
    today, ultimate, y2055 = 159_162.0, 435_945.0, 237_885.0
    f = (y2055 - today) / (ultimate - today)
    return {"pop_today": today, "pop_2055": y2055, "pop_ultimate": ultimate,
            "f_2055": f, "source": _F2055_SOURCE}


# ------------------------------------------------------------------ load

def read_nama() -> dict:
    """Every NAMA wastewater layer, classified.  Nothing here is filtered yet."""
    import geopandas as gpd

    out = {}
    for name in ("SEWERLINE", "FORCELINE", "TE_LINE", "STP_PT"):
        p = SHIP / f"{name}_IBRI.shp"
        g = gpd.read_file(fk.snapshot(str(p)), engine="pyogrio")
        if g.crs is not None and g.crs.to_epsg() != fk.EPSG:
            raise ValueError(f"{name} is {g.crs}, not {fk.CRS}")
        g.attrs["fk_source"] = fk.Src(p, "", len(g), fk._stamp(p))
        out[name] = g
    return out


def _tier_of(mhid: str) -> str:
    """NAMA's own decomposition, read off the third token of the manhole ID.

    ``5A-2-TM-MH185`` trunk main, ``5A-2-SM.2-MH391`` sub main, ``5A-1-A49-MH3``
    lateral zone A49.  Every built ID is exactly four tokens, so this never guesses.
    """
    p = str(mhid).split("-")
    t = p[2] if len(p) >= 4 else ""
    if t.startswith("TM"):
        return "trunk main"
    if t.startswith("SM"):
        return "sub main"
    return "lateral"


def classify_gravity(sew):
    """Split the gravity layer into built pipe, schematic connectors and proposals.

    Returns the whole layer with the columns this module adds, so a caller can always
    see what was excluded and why.
    """
    g = sew.copy()
    g["LEN_M"] = g.geometry.length
    g["NPTS"] = g.geometry.map(lambda x: len(x.coords))
    g["VTX_SP"] = g.LEN_M / np.maximum(g.NPTS - 1, 1)

    built = g.STATUS.astype(str) == "Ex"
    schematic = built & (g.VTX_SP > SCHEMATIC_VERTEX_SPACING_M)
    g["KIND"] = np.where(~built, "proposed (SUREKHA)",
                         np.where(schematic, "built, schematic connector", "built pipe"))
    g["TIER"] = np.where(built, [_tier_of(v) for v in g.US_MHID], "unknown")
    g.loc[schematic, "TIER"] = "schematic"

    for a, c in (("US_INV", "US_INVERT_"), ("DS_INV", "DS_INVERT_"),
                 ("US_GRD", "US_GROUND_"), ("DS_GRD", "DS_GROUND_"),
                 ("OD_MM", "OUT_DIAMET"), ("ID_MM", "IN_DIAMETE")):
        g[a] = pd.to_numeric(g[c], errors="coerce").replace(0.0, np.nan)

    g["SLOPE"] = (g.US_INV - g.DS_INV) / g.LEN_M
    g["DEP_US"] = g.US_GRD - g.US_INV
    g["DEP_DS"] = g.DS_GRD - g.DS_INV
    g["HAS_LVL"] = g.US_INV.notna() & g.DS_INV.notna()
    g["HAS_DIA"] = g.OD_MM.notna()
    g["ASSESSABLE"] = g.HAS_LVL & g.HAS_DIA & (g.KIND == "built pipe")
    return g


# --------------------------------------------------------- 1. what is built

def table_what_is_built(g) -> pd.DataFrame:
    rows = []
    for kind, sub in g.groupby("KIND"):
        rows.append(dict(kind=kind, features=len(sub), km=sub.LEN_M.sum() / 1000.0))
    t = pd.DataFrame(rows).sort_values("km", ascending=False)
    t.loc[len(t)] = dict(kind="TOTAL in the layer", features=len(g),
                         km=g.LEN_M.sum() / 1000.0)
    return t


def table_built_by_tier(g) -> pd.DataFrame:
    b = g[g.KIND == "built pipe"]
    t = (b.groupby("TIER")
           .agg(pipes=("LEN_M", "size"), km=("LEN_M", lambda s: s.sum() / 1000.0),
                median_run_m=("LEN_M", "median"),
                od_mm=("OD_MM", lambda s: ";".join(
                    f"{int(v)}x{int(c)}" for v, c in s.value_counts().items())))
           .reset_index())
    t["share_pct"] = 100.0 * t.km / t.km.sum()
    return t.sort_values("km", ascending=False)


def table_completeness(g) -> pd.DataFrame:
    b = g[g.KIND == "built pipe"]
    rows = []
    for pkg, sub in b.groupby("PROJECTCOD"):
        rows.append(dict(package=pkg, pipes=len(sub), km=sub.LEN_M.sum() / 1000.0,
                         with_diameter=int(sub.HAS_DIA.sum()),
                         with_levels=int(sub.HAS_LVL.sum()),
                         assessable_km=sub.loc[sub.ASSESSABLE, "LEN_M"].sum() / 1000.0))
    t = pd.DataFrame(rows).sort_values("km", ascending=False)
    t.loc[len(t)] = dict(package="ALL BUILT", pipes=len(b), km=b.LEN_M.sum() / 1000.0,
                         with_diameter=int(b.HAS_DIA.sum()),
                         with_levels=int(b.HAS_LVL.sum()),
                         assessable_km=b.loc[b.ASSESSABLE, "LEN_M"].sum() / 1000.0)
    return t


# ------------------------------------------------- 2. load on the built net

def load_plots():
    """Plot loads with the class that says whether the plot is developed TODAY."""
    import geopandas as gpd
    g = gpd.read_file(fk.snapshot(str(PLOT_LOADS)), layer="plot_loads", engine="pyogrio",
                      columns=["PLOT_ID", "CLASS", "N_PROP", "Q_AVG_M3D", "IN_BND"])
    g.attrs["fk_source"] = fk.Src(PLOT_LOADS, "plot_loads", len(g),
                                  fk._stamp(PLOT_LOADS))
    return g


def allocate_and_accumulate(g, plots):
    """Put every plot within reach on the built network and route it downstream.

    The topology is NAMA's own ``US_MHID`` -> ``DS_MHID``, not geometry.  A plot's load
    enters at the upstream manhole of the nearest built pipe, so that pipe carries it.
    Three load states are accumulated separately: what is developed today (CLASS B built
    plots and CLASS U unparceled buildings), the 2055 interpolation, and saturation.
    """
    import geopandas as gpd
    import networkx as nx

    b = g[g.KIND == "built pipe"].copy().reset_index(drop=True)
    b["PIPE_IX"] = np.arange(len(b))

    # ---- which plots the built network can reach at all
    near = gpd.sjoin_nearest(plots.to_crs(fk.CRS), b[["PIPE_IX", "geometry"]],
                             how="left", max_distance=SERVICE_RADIUS_M,
                             distance_col="D_M")
    near = near.dropna(subset=["PIPE_IX"]).drop_duplicates("PLOT_ID")
    near["PIPE_IX"] = near.PIPE_IX.astype(int)

    dev = near.CLASS.astype(str).isin(["B", "U"])
    near["Q_TODAY"] = np.where(dev, near.Q_AVG_M3D, 0.0)
    near["N_TODAY"] = np.where(dev, near.N_PROP, 0.0)

    f = horizon_fractions()["f_2055"]
    near["Q_2055"] = near.Q_TODAY + f * (near.Q_AVG_M3D - near.Q_TODAY)
    near["N_2055"] = near.N_TODAY + f * (near.N_PROP - near.N_TODAY)

    at_pipe = near.groupby("PIPE_IX").agg(
        Q_ULT=("Q_AVG_M3D", "sum"), N_ULT=("N_PROP", "sum"),
        Q_TODAY=("Q_TODAY", "sum"), N_TODAY=("N_TODAY", "sum"),
        Q_2055=("Q_2055", "sum"), N_2055=("N_2055", "sum"),
        PLOTS=("PLOT_ID", "size"))

    # ---- route it, on NAMA's own manhole topology
    KEYS = ("Q_ULT", "N_ULT", "Q_TODAY", "N_TODAY", "Q_2055", "N_2055", "KM")
    b["US"] = b.US_MHID.astype(str)
    b["DS"] = b.DS_MHID.astype(str)
    b = b.join(at_pipe, on="PIPE_IX")
    for k in KEYS[:-1]:
        b[k] = b[k].fillna(0.0)
    b["KM"] = b.LEN_M / 1000.0
    b["PLOTS"] = b.PLOTS.fillna(0.0)

    G = nx.DiGraph()
    G.add_edges_from(zip(b.US, b.DS))
    if not nx.is_directed_acyclic_graph(G):
        raise RuntimeError("the built network's manhole IDs contain a cycle — "
                           "accumulation would be undefined")

    # One manhole (5A-2-30-MH235) carries two outgoing pipes whose upstream inverts differ
    # by 1.98 m — physically one chamber cannot have two outlets 2 m apart, so one of the
    # two records is mis-attributed. Flow is sent down the LOWER outlet and the node is
    # reported rather than silently averaged.
    forks = {n for n in G.nodes if G.out_degree(n) > 1}
    chosen = {}
    for n in forks:
        cand = b[b.US == n].sort_values("US_INV")
        chosen[n] = cand.DS.iloc[0]
    b.attrs["forks"] = sorted(forks)

    own = {k: b.groupby("US")[k].sum().to_dict() for k in KEYS}
    acc = {k: {n: 0.0 for n in G.nodes} for k in KEYS}
    for k in KEYS:
        for n, v in own[k].items():
            acc[k][n] = v

    for n in nx.topological_sort(G):                  # upstream strictly before downstream
        succ = list(G.successors(n))
        if not succ:
            continue
        d = chosen.get(n, succ[0])
        for k in KEYS:
            acc[k][d] += acc[k][n]

    for k in KEYS:
        b[k] = [acc[k].get(u, 0.0) for u in b.US]

    b.attrs["plots_reached"] = int(len(near))
    b.attrs["plots_total"] = int(len(plots))
    b.attrs["q_reached_ult"] = float(near.Q_AVG_M3D.sum())
    b.attrs["q_reached_today"] = float(near.Q_TODAY.sum())
    b.attrs["q_all_plots"] = float(plots.Q_AVG_M3D.sum())
    b.attrs["outfalls"] = [n for n in G.nodes if G.out_degree(n) == 0]
    return b, near


def table_outfalls(b) -> pd.DataFrame:
    """What arrives at each of the built network's three outfalls."""
    rows = []
    for out in b.attrs["outfalls"]:
        last = b[b.DS == out]
        r = dict(outfall=out, packages="+".join(sorted(set(last.PROJECTCOD))),
                 upstream_km=float(last.KM.sum()))
        for tag, k in (("today", "Q_TODAY"), ("2055", "Q_2055"), ("ultimate", "Q_ULT")):
            r[f"{tag} m3/d"] = round(float(last[k].sum()), 0)
        rows.append(r)
    t = pd.DataFrame(rows)
    t.loc[len(t)] = dict(outfall="ALL THREE", packages="-",
                         upstream_km=t.upstream_km.sum(),
                         **{c: t[c].sum() for c in t.columns if c.endswith("m3/d")})
    return t


def service_radius_sensitivity(g, plots) -> pd.DataFrame:
    """How the answer moves with the one radius this analysis has to choose."""
    import geopandas as gpd
    b = g[g.KIND == "built pipe"][["geometry"]].copy()
    rows = []
    for r in (25.0, SERVICE_RADIUS_M, 60.0, 100.0):
        near = gpd.sjoin_nearest(plots, b, how="left", max_distance=r,
                                 distance_col="D_M").dropna(subset=["index_right"])
        near = near.drop_duplicates("PLOT_ID")
        dev = near.CLASS.astype(str).isin(["B", "U"])
        rows.append(dict(radius_m=r, plots=len(near),
                         today_m3d=round(float(near.loc[dev, "Q_AVG_M3D"].sum()), 0),
                         ultimate_m3d=round(float(near.Q_AVG_M3D.sum()), 0)))
    return pd.DataFrame(rows)


#: Infiltration on an EXISTING inland network, as a share of the wastewater flow.
#: G201-p72 7.4.3 gives THREE rates and the project pipeline only uses the third:
#:   * existing network in a groundwater / coastal zone   up to 40 % of flow
#:   * existing network inland or outside groundwater      10 % of flow
#:   * newly designed network                              720 L/d/km
#: Ibri is inland at about 330 m aOD, so the 10 % rule governs the BUILT network and the
#: 720 L/d/km rule governs the new design.  ``s5c_flows.py`` applies 720 L/d/km, which is
#: right for what it is sizing and wrong for anything asked of the 2006 asset.
INFILT_EXISTING_INLAND = 0.10


def peak(qadf_m3d, nprop, upstream_km, q_per_prop, *, existing: bool = True):
    """Peak flow L/s: Merrimack (G201-p71) plus infiltration (G201-p72 7.4.3).

    G201-p71 makes Merrimack mandatory over 100 properties and gives no formula below
    it, so the factor is HELD at the value 100 properties would produce — the same rule
    ``s5c_flows.py`` applies.  ``existing=True`` charges the 10 % inland rate the
    guideline sets for an EXISTING network; ``existing=False`` charges the 720 L/d/km a
    new design gets, for comparison.
    """
    held = C.pf_merrimack(C.PF_HOLD_PROPERTIES * q_per_prop / 1000.0)
    qadf = np.asarray(qadf_m3d, dtype=float)
    nprop = np.asarray(nprop, dtype=float)
    pf = np.array([C.pf_merrimack(q / 1000.0) if (n > C.PF_HOLD_PROPERTIES and q > 0)
                   else held for q, n in zip(qadf, nprop)])
    if existing:
        qinf = INFILT_EXISTING_INLAND * qadf * 1000.0 / 86400.0
    else:
        qinf = (C.INFILT_L_D_KM / 86400.0) * np.asarray(upstream_km, dtype=float)
    return qadf * 1000.0 / 86400.0 * pf + qinf, pf


def capacity(b):
    """Design capacity (at the d/D limit) and full-bore capacity, L/s, per built pipe.

    ``q_partial(D, S, y)`` takes y as the PROPORTIONAL depth d/D, not an absolute depth.
    ``W10/py/p05_existing.py`` line 279 passes ``dod * D`` — an absolute depth read as a
    proportion — and so understates capacity by about half (DN700 at 0.10 % reads 76.7
    L/s there against 144.9 L/s at d/D 0.50).  Not fixed here: that file is not this
    module's to edit, and the defect is reported instead.
    """
    qcap, qfull, bore = [], [], []
    for od, s in zip(b.OD_MM, b.SLOPE):
        if not np.isfinite(od) or not np.isfinite(s) or s <= 0:
            qcap.append(np.nan); qfull.append(np.nan); bore.append(np.nan)
            continue
        D = C.internal_diameter(int(round(od)))
        dod = C.DOD_MAX_SMALL if od <= C.DOD_DN_THRESHOLD else C.DOD_MAX_LARGE
        qcap.append(q_partial(D, s, dod) * 1000.0)
        qfull.append(q_full(D, s) * 1000.0)
        bore.append(D * 1000.0)
    b["BORE_MM"] = bore
    b["QCAP_LS"] = qcap
    b["QFULL_LS"] = qfull
    return b


def assess(b):
    """Peak flow at three horizons against each pipe's own capacity."""
    q_per_prop = (b.Q_ULT.max() / max(b.N_ULT.max(), 1.0)) if len(b) else 0.0
    for tag, qk, nk in (("TODAY", "Q_TODAY", "N_TODAY"),
                        ("Y2055", "Q_2055", "N_2055"),
                        ("ULT", "Q_ULT", "N_ULT")):
        qpk, pf = peak(b[qk], b[nk], b["KM"], q_per_prop)
        b[f"QPK_{tag}"] = qpk
        b[f"PF_{tag}"] = pf
        over = qpk > b.QCAP_LS
        surch = qpk > b.QFULL_LS
        b[f"ST_{tag}"] = np.where(~b.ASSESSABLE, "untested",
                                  np.where(surch, "surcharged",
                                           np.where(over, "over d/D", "pass")))
    return b


def table_compliance(b) -> pd.DataFrame:
    """The built network measured against today's guideline, for information only.

    A 2006 asset is not condemned by a 2024 guideline.  These rows exist because they
    say what a survey has to measure and what an adoption case has to argue.
    """
    a = b[b.ASSESSABLE].copy()
    a["COVER_US"] = a.DEP_US - a.OD_MM / 1000.0
    a["COVER_DS"] = a.DEP_DS - a.OD_MM / 1000.0
    a["COVER_MIN"] = a[["COVER_US", "COVER_DS"]].min(axis=1)
    tot = a.LEN_M.sum() / 1000.0

    def row(name, mask, rule):
        return dict(test=name, pipes=int(mask.sum()),
                    km=round(a.loc[mask, "LEN_M"].sum() / 1000.0, 2),
                    pct=round(100 * a.loc[mask, "LEN_M"].sum() / 1000.0 / tot, 1),
                    rule=rule)

    t11 = C.TABLE11.get(200, 0.005)
    rows = [
        row("cover below 1.30 m to crown", a.COVER_MIN < C.MIN_COVER_CROWN,
            "G203-p33 4.6.3"),
        row("cover below 0.50 m (the protected-pipe floor)", a.COVER_MIN < 0.50,
            "G203-p33 4.6.3"),
        row("cover over 12 m", a.COVER_MIN > 12.0, "G203-p33, recommendation"),
        row(f"gradient flatter than the DN200 Table-11 minimum "
            f"({t11*1000:.2f} mm/m)", a.SLOPE < t11, "G203-p29 Tab 11"),
        row("laid dead flat or adverse", a.SLOPE <= 0, "G203-p29"),
        row("diameter below the OD200 lateral / main minimum", a.OD_MM < 200,
            "G203-p22 Tab 6"),
        row("run longer than the 100 m maximum chamber spacing", a.LEN_M > 100.0,
            "G203-p30 Tab 12"),
    ]
    t = pd.DataFrame(rows)
    t.attrs["tested_km"] = tot
    return t


def table_capacity(b) -> pd.DataFrame:
    rows = []
    for tag, label in (("TODAY", "today, plots developed now"),
                       ("Y2055", "2055 (interpolated)"),
                       ("ULT", "ultimate / saturation")):
        st = b[f"ST_{tag}"]
        r = dict(horizon=label)
        for s in ("pass", "over d/D", "surcharged", "untested"):
            m = st == s
            r[f"{s} n"] = int(m.sum())
            r[f"{s} km"] = round(b.loc[m, "LEN_M"].sum() / 1000.0, 2)
        k = {"TODAY": "Q_TODAY", "Y2055": "Q_2055", "ULT": "Q_ULT"}[tag]
        r["largest single reach m3/d"] = round(float(b[k].max()), 0)
        ass = b[b.ASSESSABLE]
        bad = ass[f"ST_{tag}"] != "pass"
        r["fail % of testable km"] = round(
            100 * ass.loc[bad, "LEN_M"].sum() / ass.LEN_M.sum(), 1)
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------- 3. duplication against the design

def read_design():
    """The W11a chamber-to-chamber skeleton with stage 5c's flows joined on."""
    import geopandas as gpd
    sk = gpd.read_file(fk.snapshot(str(SKELETON)), layer="s5_reach_skeleton",
                       engine="pyogrio")
    sk.attrs["fk_source"] = fk.Src(SKELETON, "s5_reach_skeleton", len(sk),
                                   fk._stamp(SKELETON))
    fl = fk.read_csv(FLOWS_CSV)
    sk = sk.merge(fl[["EDGE_UID", "QADF_M3D", "QPK_LS", "N_PROP", "UPSTR_KM"]],
                  on="EDGE_UID", how="left")
    sk["LEN_M"] = sk.geometry.length
    return sk, fl


def overlay(b, design):
    """How much of each network lies on the other's alignment, within SAME_STREET_M."""
    from shapely.ops import unary_union
    from shapely import STRtree

    built_u = unary_union(b.geometry.values).buffer(SAME_STREET_M)
    des_u = unary_union(design.geometry.values).buffer(SAME_STREET_M)

    b = b.copy()
    b["ON_DESIGN_M"] = [g.intersection(des_u).length for g in b.geometry]
    design = design.copy()
    design["ON_BUILT_M"] = [g.intersection(built_u).length for g in design.geometry]

    # nearest design reach to each built pipe, for the alignment-disagreement number
    tree = STRtree(design.geometry.values)
    idx = tree.nearest(b.geometry.values)
    b["D_TO_DESIGN_M"] = [b.geometry.iloc[i].distance(design.geometry.iloc[j])
                          for i, j in enumerate(idx)]
    b["NEAREST_TIER"] = design.TIER.values[idx]
    return b, design


def table_overlay(b, design) -> pd.DataFrame:
    bk = b.LEN_M.sum() / 1000.0
    dk = design.LEN_M.sum() / 1000.0
    dup = b.ON_DESIGN_M.sum() / 1000.0
    onb = design.ON_BUILT_M.sum() / 1000.0
    rows = [
        dict(measure=f"built pipe with a W11a reach within {SAME_STREET_M:.0f} m "
                     "(the design re-lays it)",
             km=dup, pct_of=100 * dup / bk, of="built network"),
        dict(measure=f"built pipe with NO W11a reach within {SAME_STREET_M:.0f} m",
             km=bk - dup, pct_of=100 * (bk - dup) / bk, of="built network"),
        dict(measure=f"W11a reach lying on a built pipe (reusable alignment)",
             km=onb, pct_of=100 * onb / dk, of="W11a design"),
        dict(measure="W11a design on new ground", km=dk - onb,
             pct_of=100 * (dk - onb) / dk, of="W11a design"),
    ]
    return pd.DataFrame(rows)


def trunk_coincidence(b):
    """Where the design's TRUNK runs down a street that already has a built sewer.

    This is the reuse test that matters.  Sections 5-6 ask whether a built pipe can carry
    the plots that front it; this asks whether it can carry what the DESIGN would send
    through it.  Stage 3's trunk is used and stage 5c's reach flows are not, because 5c
    accumulates only within each fragment of a network that is not yet joined up, while
    the trunk layer carries the whole 73,442 m3/d.
    """
    import geopandas as gpd
    from shapely.ops import unary_union

    tr = gpd.read_file(fk.snapshot("W11a_trunk.gpkg"), layer="reaches", engine="pyogrio")
    tr["LEN_M"] = tr.geometry.length
    band = unary_union(tr.geometry.values).buffer(SAME_STREET_M)
    b = b.copy()
    b["UNDER_TRUNK_M"] = [g.intersection(band).length for g in b.geometry]

    hit = b[b.UNDER_TRUNK_M > 0].copy()
    if len(hit):
        from shapely import STRtree
        tree = STRtree(tr.geometry.values)
        j = tree.nearest(hit.geometry.values)
        hit["TRUNK_DN"] = tr.DN.values[j]
        hit["TRUNK_QPK"] = tr.QPK_LS.values[j]
        hit["TRUNK_QADF"] = tr.QADF_M3D.values[j]
    return b, hit, tr


def table_trunk_coincidence(hit, tr) -> pd.DataFrame:
    if not len(hit):
        return pd.DataFrame([dict(note="the design trunk shares no street with a "
                                       "built sewer")])
    rows = []
    for dn, sub in hit.groupby("TRUNK_DN"):
        rows.append(dict(design_DN=int(dn), built_pipes=len(sub),
                         built_km=sub.UNDER_TRUNK_M.sum() / 1000.0,
                         built_OD=";".join(sorted({f"OD{int(v)}" for v in sub.OD_MM
                                                   if np.isfinite(v)})) or "not recorded",
                         design_QPK_LS=round(float(sub.TRUNK_QPK.max()), 1),
                         built_QCAP_LS=round(float(np.nanmax(sub.QCAP_LS.values))
                                             if sub.QCAP_LS.notna().any() else np.nan, 1)))
    t = pd.DataFrame(rows).sort_values("design_DN")
    t["design_flow / built capacity"] = (t.design_QPK_LS / t.built_QCAP_LS).round(1)
    return t


DESIGNED = "W11a_reaches.shp"          # stages 6-9 output: DN, laid gradient, flows


def design_demand(b):
    """For every built pipe, what the FINISHED design asks of that street.

    Stages 6-9 completed during this work, so ``W11a/shp/W11a_reaches.shp`` now carries a
    diameter and a peak flow on every reach.  That makes the decisive reuse test possible:
    not "can the built pipe carry the plots that front it" (section 6) but "can it carry
    what the design routes down that street".  A built pipe is matched to the co-located
    design reach with the LARGEST peak flow inside the same-street band, because a reuse
    decision is governed by the worst thing the street has to carry.
    """
    import geopandas as gpd
    from shapely import STRtree

    d = gpd.read_file(fk.snapshot(str(fk.SHP / DESIGNED)), engine="pyogrio",
                      columns=["EDGE_UID", "TIER", "DN", "QPK_LS", "QADF_M3D",
                               "SLOPE_LAID", "V_PK_MS", "DOD_PK"])
    d.attrs["fk_source"] = fk.Src(fk.SHP / DESIGNED, "", len(d),
                                  fk._stamp(fk.SHP / DESIGNED))
    tree = STRtree(d.geometry.values)
    b = b.copy()
    dn, qpk, tier, gap = [], [], [], []
    for g in b.geometry:
        hits = tree.query(g.buffer(SAME_STREET_M))
        if len(hits) == 0:
            dn.append(np.nan); qpk.append(np.nan); tier.append(None); gap.append(np.nan)
            continue
        sub = d.iloc[hits]
        k = int(sub.QPK_LS.fillna(-1).values.argmax())
        dn.append(sub.DN.iloc[k]); qpk.append(sub.QPK_LS.iloc[k])
        tier.append(sub.TIER.iloc[k])
        gap.append(float(g.distance(sub.geometry.iloc[k])))
    b["D_DN"] = dn
    b["D_QPK"] = qpk
    b["D_TIER"] = tier
    b["D_GAP_M"] = gap
    b["RATIO"] = b.D_QPK / b.QCAP_LS
    return b, d


def table_design_demand(b) -> pd.DataFrame:
    """Can the built pipe carry what the design routes down its street?"""
    m = b.D_QPK.notna()
    rows = []
    for tier, sub in b[m].groupby("D_TIER"):
        ok = sub[sub.ASSESSABLE & (sub.RATIO <= 1.0)]
        no = sub[sub.ASSESSABLE & (sub.RATIO > 1.0)]
        un = sub[~sub.ASSESSABLE]
        rows.append(dict(
            design_tier_on_that_street=tier, built_pipes=len(sub),
            built_km=sub.LEN_M.sum() / 1000.0,
            adequate_km=ok.LEN_M.sum() / 1000.0,
            short_km=no.LEN_M.sum() / 1000.0,
            untestable_km=un.LEN_M.sum() / 1000.0,
            median_shortfall_x=(float(no.RATIO.median()) if len(no) else float("nan")),
            worst_x=(float(no.RATIO.max()) if len(no) else float("nan"))))
    t = pd.DataFrame(rows)
    order = {"rider": 0, "lateral": 1, "main": 2, "sub main": 3, "trunk main": 4}
    return t.sort_values("design_tier_on_that_street",
                         key=lambda s: s.map(lambda v: order.get(v, 9)))


def table_fail_by_tier(b) -> pd.DataFrame:
    """Where the capacity failures sit.  The tier answer is the design answer."""
    rows = []
    for tier, sub in b.groupby("TIER"):
        a = sub[sub.ASSESSABLE]
        bad = a[a.ST_ULT != "pass"]
        rows.append(dict(tier=tier, pipes=len(sub), km=sub.LEN_M.sum() / 1000.0,
                         testable_km=a.LEN_M.sum() / 1000.0,
                         fail_km_ult=bad.LEN_M.sum() / 1000.0,
                         fail_pct_of_testable=(100 * bad.LEN_M.sum() / a.LEN_M.sum()
                                               if len(a) else float("nan")),
                         median_util_ult=(float((a.QPK_ULT / a.QCAP_LS).median())
                                          if len(a) else float("nan"))))
    return pd.DataFrame(rows).sort_values("km", ascending=False)


def table_coverage_by_package(b) -> pd.DataFrame:
    """Which built packages the design's corridor set actually reaches."""
    rows = []
    for pkg, sub in b.groupby("PROJECTCOD"):
        far = sub[sub.D_TO_DESIGN_M > SAME_STREET_M]
        rows.append(dict(package=pkg, km=sub.LEN_M.sum() / 1000.0,
                         km_no_design_reach=far.LEN_M.sum() / 1000.0,
                         pct=100 * far.LEN_M.sum() / sub.LEN_M.sum()))
    return pd.DataFrame(rows).sort_values("pct", ascending=False)


def table_disagreement(b) -> pd.DataFrame:
    bins = [0, 2, 5, SAME_STREET_M, 25, 50, 100, 1e9]
    lab = ["0-2 m (same line)", "2-5 m", f"5-{SAME_STREET_M:.0f} m",
           f"{SAME_STREET_M:.0f}-25 m", "25-50 m", "50-100 m", "over 100 m"]
    cut = pd.cut(b.D_TO_DESIGN_M, bins=bins, labels=lab, right=False)
    t = b.groupby(cut, observed=False).agg(pipes=("LEN_M", "size"),
                                           km=("LEN_M", lambda s: s.sum() / 1000.0))
    t["pct"] = 100 * t.km / t.km.sum()
    return t.reset_index().rename(columns={"D_TO_DESIGN_M": "distance to nearest "
                                                            "W11a reach"})


# ------------------------------------------------------------------ figures

def fig_overlay(b, design, nama, note_extra=""):
    """Map: the built network, the design on top of it, and where they disagree."""
    from matplotlib.lines import Line2D

    ext = fk.extent_of(b, pad=0.06)
    dup_m = b.ON_DESIGN_M.sum() / 1000.0
    bk = b.LEN_M.sum() / 1000.0
    far = b[b.D_TO_DESIGN_M > SAME_STREET_M]

    fig, ax, note = fk.map_frame(
        ext,
        title=(f"The greenfield design re-lays {100*dup_m/bk:.0f} % of the built "
               f"network and misses the other {100*(bk-dup_m)/bk:.0f} %"),
        subtitle=(f"NAMA's 2006 network ({bk:,.1f} km of built pipe, STATUS='Ex', the "
                  f"schematic connectors removed) against the W11a stage-5 skeleton. "
                  f"Red is built pipe whose NEAREST design reach is further than "
                  f"{SAME_STREET_M:.0f} m away — either a street our corridor set does "
                  f"not have, or a sewer that does not run down a street."),
        basemap_alpha=0.22)
    design.plot(ax=ax, color="#9e9e9e", linewidth=0.35, zorder=3)
    inb = design[design.ON_BUILT_M > 0]
    if len(inb):
        inb.plot(ax=ax, color=fk.C.LATERAL, linewidth=0.6, zorder=4)
    b.plot(ax=ax, color=fk.C.INK, linewidth=0.9, zorder=5)
    if len(far):
        far.plot(ax=ax, color=fk.C.FAIL, linewidth=1.5, zorder=6)

    prop = nama["SEWERLINE"]
    prop = prop[prop.STATUS.astype(str) == "Design"]
    prop.plot(ax=ax, color=fk.C.FLAG, linewidth=0.8, linestyle=":", zorder=3.5)

    stp = nama["STP_PT"]
    ax.scatter(stp.geometry.x, stp.geometry.y, s=55, marker="s",
               facecolor=fk.C.OUTFALL, edgecolor="white", linewidth=0.8, zorder=8)
    try:
        fk.study_boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.1, ls="--",
                                          zorder=7)
    except Exception:                                            # noqa: BLE001
        pass

    handles = [
        Line2D([], [], color=fk.C.INK, lw=1.4,
               label=f"built 2006 sewer ({bk:,.1f} km, {len(b):,} pipes)"),
        Line2D([], [], color=fk.C.FAIL, lw=1.8,
               label=f"built, nearest design reach over {SAME_STREET_M:.0f} m away "
                     f"({far.LEN_M.sum()/1000:,.1f} km, {len(far):,} pipes)"),
        Line2D([], [], color=fk.C.LATERAL, lw=1.0,
               label=f"W11a reach on a built alignment "
                     f"({design.ON_BUILT_M.sum()/1000:,.1f} km)"),
        Line2D([], [], color="#9e9e9e", lw=1.0,
               label=f"W11a reach on new ground "
                     f"({(design.LEN_M.sum()-design.ON_BUILT_M.sum())/1000:,.0f} km "
                     f"in the study area)"),
        Line2D([], [], color=fk.C.FLAG, lw=1.2, ls=":",
               label=f"SUREKHA proposal, NOT approved "
                     f"({prop.geometry.length.sum()/1000:,.0f} km)"),
        Line2D([], [], color=fk.C.OUTFALL, lw=0, marker="s", markersize=7,
               label="existing and proposed works"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.1, ls="--", label="study boundary"),
    ]
    box = (f"built pipe        {bk:>8,.1f} km\n"
           f"re-laid by W11a   {dup_m:>8,.1f} km\n"
           f"design reuses     {design.ON_BUILT_M.sum()/1000:>8,.1f} km\n"
           f"design total      {design.LEN_M.sum()/1000:>8,.0f} km\n"
           f"same-street tol.  {SAME_STREET_M:>8,.0f} m (ours)")
    fk.finish_map(fig, ax, legend_handles=handles, legend_loc="lower left",
                  databox=box, note=(note + note_extra),
                  source=fk.source_line(
                      nama["SEWERLINE"],
                      f"W11a/run/s5_reach_skeleton.gpkg [s5_reach_skeleton], "
                      f"{len(design):,} rows"))
    return fk.save(fig, "FEX1_existing_vs_design")


def fig_capacity(b):
    """Chart: what the built network can carry, at three horizons."""
    from matplotlib.patches import Patch

    order = ["pass", "over d/D", "surcharged", "untested"]
    role = {"pass": "pass", "over d/D": "flag", "surcharged": "fail",
            "untested": "untested"}
    rows = [("ultimate\n(saturation)", "ULT"), ("2055\n(interpolated)", "Y2055"),
            ("today\n(plots built now)", "TODAY")]

    ult_fail = b.loc[b.ST_ULT.isin(["over d/D", "surcharged"]), "LEN_M"].sum() / 1000
    tested = b.loc[b.ASSESSABLE, "LEN_M"].sum() / 1000
    today_fail = b.loc[b.ST_TODAY.isin(["over d/D", "surcharged"]), "LEN_M"].sum() / 1000

    fig, axes = fk.chart_frame(
        title=(f"Growth is not what breaks the built network: "
               f"{100*today_fail/tested:.0f} % of the testable {tested:,.0f} km already "
               f"fails today, {100*ult_fail/tested:.0f} % at saturation — and a third of "
               f"it cannot be tested at all"),
        subtitle=("LEFT, kilometres by outcome at three horizons. RIGHT, how much of "
                  "each pipe's own capacity the ultimate flow uses. Capacity is at the "
                  "G203-p27 Tab 10 depth-of-flow limit (d/D 0.65 at these diameters), "
                  "Colebrook-White with ks = 1.5 mm (G203-p24, p28), on the gradient "
                  "derived from NAMA's own inverts and the bore behind its own OD. Flow "
                  "is Merrimack (G201-p71) plus the 10 % infiltration G201-p72 7.4.3 "
                  "sets for an EXISTING inland network. UNTESTED is package 5A-1, which "
                  "records no diameter and no level at all — the philosophy counts that "
                  "as a failure, not a blank."),
        figsize=(12.4, 4.6), ncols=2, ygrid=False, xgrid=True)
    ax, ax2 = axes

    ypos = np.arange(len(rows))[::-1]
    for y, (_lab, tag) in zip(ypos, rows):
        left = 0.0
        for s in order:
            km = b.loc[b[f"ST_{tag}"] == s, "LEN_M"].sum() / 1000.0
            if km <= 0:
                continue
            ax.barh(y, km, left=left, height=0.55, **fk.status_style(role[s]))
            if km > 3:
                ax.text(left + km / 2, y, f"{km:,.0f}", ha="center", va="center",
                        fontsize=7.6, color=fk.label_ink(role[s]), fontweight="bold")
            left += km
    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xlabel("kilometres of built 2006 gravity sewer")
    ax.set_xlim(0, b.LEN_M.sum() / 1000.0 * 1.02)

    # ---- right panel: how much of its own capacity each pipe is using
    u = (b.QPK_ULT / b.QCAP_LS).where(b.ASSESSABLE)
    bands = [(0, 0.25, "under 25 %", "pass"), (0.25, 0.50, "25-50 %", "pass"),
             (0.50, 0.75, "50-75 %", "pass"), (0.75, 1.00, "75-100 %", "flag"),
             (1.00, 1e9, "over the d/D limit", "fail")]
    labs, kms, roles = [], [], []
    for lo, hi, lab, r in bands:
        m = (u >= lo) & (u < hi)
        labs.append(lab); kms.append(b.loc[m.fillna(False), "LEN_M"].sum() / 1000.0)
        roles.append(r)
    labs.append("UNTESTED"); roles.append("untested")
    kms.append(b.loc[~b.ASSESSABLE, "LEN_M"].sum() / 1000.0)
    yp = np.arange(len(labs))[::-1]
    for y, km, r in zip(yp, kms, roles):
        ax2.barh(y, km, height=0.62, **fk.status_style(r))
        ax2.text(km + 0.6, y, f"{km:,.1f}", va="center", fontsize=7.4, color=fk.C.INK)
    ax2.set_yticks(yp)
    ax2.set_yticklabels(labs, fontsize=8)
    ax2.set_xlabel("km, by share of its own capacity used at saturation")
    ax2.set_xlim(0, max(kms) * 1.18)

    names = {"pass": "passes — flow within the d/D limit",
             "over d/D": "over the d/D limit but not yet surcharged",
             "surcharged": "surcharged — flow exceeds the full bore",
             "untested": "UNTESTED — no diameter, no level (package 5A-1)"}
    fk.legend_below(ax, [Patch(label=names[s], **fk.status_style(role[s]))
                         for s in order], ncol=2)
    fk.finish_chart(fig, source=fk.source_line(
        str(b.attrs["src_sewer"]), str(b.attrs["src_plots"]),
        "W10/docs/LOAD_ALLOCATION.md sec 6 (the 2055 interpolation)"))
    return fk.save(fig, "FEX2_existing_capacity")


# --------------------------------------------------------------------- main

def main(tables_only: bool = False) -> None:
    def head(s):
        print("\n" + "=" * 96 + f"\n{s}\n" + "=" * 96)

    nama = read_nama()
    g = classify_gravity(nama["SEWERLINE"])

    head("1  WHAT IS IN THE GRAVITY LAYER  (STATUS filtered — the layer holds two networks)")
    print(table_what_is_built(g).to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
    sch = g[g.KIND == "built, schematic connector"]
    print(f"\nschematic connectors excluded from every 'built pipe' number below:")
    print(sch[["FEATUREID", "PROJECTCOD", "US_MHID", "DS_MHID", "LEN_M", "NPTS",
               "VTX_SP", "OD_MM"]].to_string(index=False,
                                             float_format=lambda v: f"{v:,.1f}"))

    head("2  THE BUILT NETWORK, BY NAMA'S OWN TIER TOKENS")
    print(table_built_by_tier(g).to_string(index=False,
                                           float_format=lambda v: f"{v:,.2f}"))

    head("3  WHAT IS RECORDED, BY PACKAGE")
    print(table_completeness(g).to_string(index=False,
                                          float_format=lambda v: f"{v:,.2f}"))

    head("4  FORCE MAIN, TREATED EFFLUENT AND WORKS")
    for name in ("FORCELINE", "TE_LINE"):
        h = nama[name].copy()
        h["LEN_M"] = h.geometry.length
        print(f"\n{name}:")
        print(h.groupby("STATUS").agg(features=("LEN_M", "size"),
                                      km=("LEN_M", lambda s: s.sum() / 1000.0))
              .to_string(float_format=lambda v: f"{v:,.3f}"))
    stp = nama["STP_PT"]
    print("\nSTP_PT:")
    print(stp[["STP_NAME", "CAPACITY", "TREATMENT_", "STATUS", "SOURCE",
               "HYPERLINK"]].to_string(index=False))

    head("5  LOAD ON THE BUILT NETWORK, ROUTED ON NAMA'S OWN MANHOLE TOPOLOGY")
    plots = load_plots()
    b, near = allocate_and_accumulate(g, plots)
    hf = horizon_fractions()
    print(f"plots within {SERVICE_RADIUS_M:.0f} m of a built pipe (G203-p22 Tab 6 "
          f"lateral length, used as a service radius): "
          f"{b.attrs['plots_reached']:,} of {b.attrs['plots_total']:,}")
    print(f"  their saturation load        {b.attrs['q_reached_ult']:>12,.0f} m3/d  "
          f"({100*b.attrs['q_reached_ult']/b.attrs['q_all_plots']:.1f} % of the "
          f"{b.attrs['q_all_plots']:,.0f} m3/d in the boundary)")
    print(f"  their load developed today   {b.attrs['q_reached_today']:>12,.0f} m3/d")
    print(f"  2055 interpolation fraction  {hf['f_2055']:>12.3f}   "
          f"(({hf['pop_2055']:,.0f} - {hf['pop_today']:,.0f}) / "
          f"({hf['pop_ultimate']:,.0f} - {hf['pop_today']:,.0f})), "
          f"PROJECT ASSUMPTION from {hf['source']}")
    print(f"\nservice radius is the one number this analysis has to choose "
          f"({SERVICE_RADIUS_M:.0f} m used above). Sensitivity:")
    print(service_radius_sensitivity(g, plots).to_string(index=False))
    print("\nWHAT ARRIVES AT EACH OUTFALL  (three separate systems, no gravity link "
          "between them):")
    print(table_outfalls(b).to_string(index=False, float_format=lambda v: f"{v:,.1f}"))
    print(f"the existing works is rated 1,800 m3/d (STP_PT_IBRI, STATUS='Ex').")
    if b.attrs["forks"]:
        print(f"\nTOPOLOGY ANOMALY: {len(b.attrs['forks'])} manhole(s) carry two outgoing "
              f"pipes — {', '.join(b.attrs['forks'])}. Flow is routed down the lower "
              f"outlet; the record needs checking.")

    b = capacity(b)
    b = assess(b)
    b.attrs["src_sewer"] = nama["SEWERLINE"].attrs["fk_source"]
    b.attrs["src_plots"] = plots.attrs["fk_source"]

    head("6  CAPACITY OF THE BUILT NETWORK AT THREE HORIZONS")
    print(table_capacity(b).to_string(index=False))
    ass = b[b.ASSESSABLE]
    print(f"\ntestable: {len(ass):,} pipes, {ass.LEN_M.sum()/1000:,.2f} km. "
          f"Untestable: {int((~b.ASSESSABLE).sum()):,} pipes, "
          f"{b.loc[~b.ASSESSABLE,'LEN_M'].sum()/1000:,.2f} km.")
    print("\nworst 12 pipes at the ultimate horizon:")
    cols = ["FEATUREID", "PROJECTCOD", "TIER", "OD_MM", "BORE_MM", "SLOPE", "LEN_M",
            "Q_ULT", "QPK_ULT", "QCAP_LS", "QFULL_LS", "ST_ULT"]
    print(ass.nlargest(12, "QPK_ULT")[cols].to_string(
        index=False, float_format=lambda v: f"{v:,.3f}"))
    head("6b  THE BUILT NETWORK AGAINST TODAY'S GUIDELINE  (reporting only, not a "
         "condemnation of a 2006 asset)")
    tc = table_compliance(b)
    print(f"measured on the {tc.attrs['tested_km']:,.2f} km that records both a "
          f"diameter and levels:")
    print(tc.to_string(index=False))

    print("\nWHERE THE CAPACITY FAILURES SIT, BY TIER (ultimate horizon):")
    print(table_fail_by_tier(b).to_string(index=False,
                                          float_format=lambda v: f"{v:,.2f}"))

    print("\nWHERE THE DIAMETER SITS AGAINST THE GUIDELINE MINIMUM (G203-p22 Tab 6):")
    dia = b[b.HAS_DIA]
    for od, sub in dia.groupby("OD_MM"):
        role = ("rider / property connection minimum" if od <= 160
                else "lateral and main sewer minimum")
        print(f"  OD{int(od):<4d} {len(sub):>5,} pipes  {sub.LEN_M.sum()/1000:>7.2f} km"
              f"   Tab 6 calls OD{int(od)} the {role}")
    small = dia[dia.OD_MM < 200]
    print(f"  -> {len(small):,} pipes / {small.LEN_M.sum()/1000:,.2f} km "
          f"({100*small.LEN_M.sum()/dia.LEN_M.sum():.1f} % of the dimensioned network) "
          f"are laid at a size Tab 6 allows only for a rider or a property connection.")

    print("\nSENSITIVITY — the load, and which infiltration rule (G201-p72 7.4.3):")
    q_per_prop = b.Q_ULT.max() / max(b.N_ULT.max(), 1.0)
    for lab, mult in (("half saturation", 0.5), ("saturation", 1.0)):
        for inf_lab, ex in (
                (f"existing inland, {INFILT_EXISTING_INLAND:.0%} of flow  (used above)",
                 True),
                (f"new network, {C.INFILT_L_D_KM:.0f} L/d/km (what s5c applies)", False)):
            qpk, _ = peak(b.Q_ULT * mult, b.N_ULT * mult, b.KM, q_per_prop, existing=ex)
            bad = (qpk > b.QCAP_LS) & b.ASSESSABLE
            print(f"  {lab:<16s} + {inf_lab:<52s} {int(bad.sum()):>5,} pipes / "
                  f"{b.loc[bad,'LEN_M'].sum()/1000:>6.2f} km over the d/D limit")

    head("7  THE BUILT NETWORK AGAINST THE GREENFIELD DESIGN")
    design, flows = read_design()
    b, design = overlay(b, design)
    print(table_overlay(b, design).to_string(index=False,
                                             float_format=lambda v: f"{v:,.2f}"))
    print("\nwhich built packages the design's corridors reach at all:")
    print(table_coverage_by_package(b).to_string(index=False,
                                                 float_format=lambda v: f"{v:,.2f}"))
    print("\nhow far the nearest W11a reach is from each built pipe:")
    print(table_disagreement(b).to_string(index=False,
                                          float_format=lambda v: f"{v:,.2f}"))
    tr_q = 73442.0
    print(f"\nNOTE on the design's own flow field, checked at run time: stage 5c's "
          f"largest reach carries {flows.QADF_M3D.max():,.0f} m3/d against the stage-3 "
          f"trunk's {tr_q:,.0f} m3/d — {100*flows.QADF_M3D.max()/tr_q:.0f} % of it. "
          f"Section 6 does not use 5c at all: every flow there is accumulated on NAMA's "
          f"own manhole topology from the W10 plot loads, so this assessment does not "
          f"depend on whether 5c's accumulation is whole.")

    head("8  REUSE — HOW MUCH OF THE DUPLICATED PIPE COULD ACTUALLY BE KEPT")
    on = b[b.ON_DESIGN_M > 0]
    print(f"built pipes that TOUCH a design reach   {len(on):,} pipes, "
          f"{on.LEN_M.sum()/1000:>7.2f} km of pipe "
          f"({on.ON_DESIGN_M.sum()/1000:.2f} km of it actually inside the band)")
    for tag, lab in (("TODAY", "today"), ("ULT", "at saturation")):
        ok = on[(on[f"ST_{tag}"] == "pass")]
        un = on[~on.ASSESSABLE]
        print(f"  of which capacity-adequate {lab:<14s} {ok.LEN_M.sum()/1000:>8.2f} km"
              f"   ({100*ok.LEN_M.sum()/on.LEN_M.sum():.1f} %)")
    print(f"  of which untestable (no diameter/level) {un.LEN_M.sum()/1000:>7.2f} km"
          f"   ({100*un.LEN_M.sum()/on.LEN_M.sum():.1f} %)")

    head("8b  THE DECISIVE REUSE TEST — CAN THE BUILT PIPE CARRY WHAT THE DESIGN ROUTES "
         "DOWN ITS STREET?")
    try:
        b, dsg = design_demand(b)
        print(f"finished design read from {DESIGNED}: {len(dsg):,} reaches, "
              f"{dsg.geometry.length.sum()/1000:,.1f} km, DN{int(dsg.DN.min())}-"
              f"{int(dsg.DN.max())}, {dsg.QPK_LS.max():,.0f} L/s peak")
        m = b.D_QPK.notna()
        print(f"built pipe with a design reach within {SAME_STREET_M:.0f} m: "
              f"{int(m.sum()):,} pipes, {b.loc[m,'LEN_M'].sum()/1000:,.2f} km")
        print(table_design_demand(b).to_string(index=False,
                                               float_format=lambda v: f"{v:,.2f}"))
        ok = b[b.ASSESSABLE & m & (b.RATIO <= 1.0)]
        print(f"\nREUSABLE on this test: {len(ok):,} pipes, "
              f"{ok.LEN_M.sum()/1000:,.2f} km "
              f"({100*ok.LEN_M.sum()/b.LEN_M.sum():.1f} % of the built network, "
              f"{100*ok.LEN_M.sum()/dsg.geometry.length.sum():.2f} % of the design)")
        print(ok.groupby(["TIER", "PROJECTCOD"]).agg(
            n=("LEN_M", "size"), km=("LEN_M", lambda s: s.sum() / 1000)).round(2)
            .to_string())

        # ---- the two published design layers do not agree, so say so on the page
        import geopandas as gpd
        tr2 = gpd.read_file(fk.snapshot("W11a_trunk.gpkg"), layer="reaches",
                            engine="pyogrio", columns=["EDGE_UID", "DN", "QADF_M3D"])
        j = dsg[["EDGE_UID", "DN", "QADF_M3D"]].merge(tr2, on="EDGE_UID",
                                                      suffixes=("_net", "_trunk"))
        if len(j):
            dn_diff = int((j.DN_net != j.DN_trunk).sum())
            q_diff = int((abs(j.QADF_M3D_net - j.QADF_M3D_trunk)
                          > 0.01 * j.QADF_M3D_trunk.clip(lower=1)).sum())
            print(f"\nCROSS-LAYER CHECK: {len(j):,} trunk edge ids appear in BOTH "
                  f"{DESIGNED} and W11a_trunk.gpkg. {dn_diff:,} carry a different DN and "
                  f"{q_diff:,} differ on QADF by more than 1 %. The demands in the table "
                  f"above are the NETWORK layer's, which is the smaller of the two, so "
                  f"every shortfall here is a lower bound. This is a stage-3/stage-6 "
                  f"reconciliation for the pipeline owners — reported, not fixed.")
            worst = j.nlargest(1, "QADF_M3D_trunk").iloc[0]
            print(f"  worst example: {worst.EDGE_UID} is DN{int(worst.DN_trunk)} at "
                  f"{worst.QADF_M3D_trunk:,.0f} m3/d in the trunk layer and "
                  f"DN{int(worst.DN_net)} at {worst.QADF_M3D_net:,.0f} m3/d in "
                  f"{DESIGNED}.")
    except Exception as exc:                                     # noqa: BLE001
        print(f"NOT RUN — {type(exc).__name__}: {exc}. The finished design layer "
              f"{DESIGNED} was not readable; sections 7 and 9 stand on their own.")

    head("9  THE REUSE TEST THAT MATTERS — BUILT PIPE UNDER THE DESIGN'S TRUNK")
    b, hit, tr = trunk_coincidence(b)
    print(f"design trunk: {len(tr):,} reaches, {tr.LEN_M.sum()/1000:,.2f} km, "
          f"DN{int(tr.DN.min())}-{int(tr.DN.max())}, "
          f"{tr.QADF_M3D.max():,.0f} m3/d at the works")
    print(f"built pipe inside {SAME_STREET_M:.0f} m of it: {len(hit):,} pipes, "
          f"{hit.UNDER_TRUNK_M.sum()/1000:,.2f} km")
    print(table_trunk_coincidence(hit, tr).to_string(index=False,
                                                     float_format=lambda v: f"{v:,.2f}"))

    if not tables_only:
        head("10  FIGURES")
        print("  ", fig_overlay(b, design, nama))
        print("  ", fig_capacity(b))

    return b, design, nama


if __name__ == "__main__":
    main(tables_only="--tables" in sys.argv)
