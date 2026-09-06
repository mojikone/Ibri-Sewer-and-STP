# -*- coding: utf-8 -*-
"""make_overview - the three themes and the drawing, rebuilt in seconds off the published
layers.

    python make_overview.py              the three theme KMZ, their QGIS styles, and the DXF
    python make_overview.py --themes     only the KMZ and the .qml
    python make_overview.py --dxf        only the drawing
    python make_overview.py --check      say what is on disk and what the themes would miss

WHAT CHANGED HERE, AND WHY IT MATTERS MORE THAN IT LOOKS
========================================================================================
This file used to build its own overview: it clustered the unserved plots itself, found
the subnetwork outfalls itself, measured the gap to the main pipe itself, and counted the
stations with nothing upstream itself. Every one of those questions is ALSO answered by
`s8_export`, on the published layer, with a field name and a rule behind it.

That is inheritance row 10 - "one published quantity, one function" - and it is the row
that put seven different pumping-station counts into circulation in W10. Two files that
each compute "how far is this subnetwork from the trunk" will eventually disagree, and
the drawing a reviewer marks up will not be the drawing the schedule describes.

So this file now COMPUTES NOTHING. It reads the published layers, calls the SAME
`write_themes()` and `write_dxf()` that stage 8 calls, and prints figures read straight
off the fields - `JOIN_MAIN`, `GAP_M`, `CAN_CONN`, `N_SUBNET`, `SERVED`. What it adds is
SPEED: the full export takes minutes because it re-levels the whole network, and when the
only thing that changed is how the map looks, that is minutes for nothing.

It is also the honest fallback when the export lags. Where a layer is missing or a column
the themes need is absent, it SAYS WHICH, by name, and refuses to draw a quietly poorer
map that looks like a complete one.
"""
from __future__ import annotations

import argparse
import os
import sys
import warnings

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import s8_export as EX                                            # noqa: E402
from w12 import contract as CT                                    # noqa: E402
from w12.criteria import DEFAULT as C                             # noqa: E402

# The five design layers plus the client's main pipe. The column list per layer is what
# the THEMES need - not everything the layer carries - so a missing column is reported
# against the map it would have spoiled rather than as a vague schema complaint.
NEEDS = {
    "reaches": ("NAME", "SUB_NAME", "TIER", "DN", "LEN_M", "SLOPE_LAID", "QPK_LS",
                "V_PK_MS", "US_NAME", "DS_NAME", "DEP_M"),
    "nodes": ("NAME", "SUB_NAME", "NODE_KIND", "DROP_TYPE", "DROP_WHY", "JOIN_MAIN",
              "JOIN_OFF_M", "JOIN_WHY", "PAST_CAP", "ON_WADI", "GRD_M", "INV_M",
              "DEPTH_M", "MH_DIA", "X", "Y", "DEP_M"),
    "stations": ("NAME", "GRD_M", "INV_M", "LIFT_M", "Q_DUTY_LS", "WELL_M3",
                 "CATCH_KM", "N_SUBNET", "DEP_M"),
    "rising_mains": ("NAME", "STATION", "DS_NODE", "DS_TYPE", "DN", "LEN_M",
                     "Q_DUTY_LS", "V_DUTY_MS", "DEP_M"),
    "subnetworks": ("NAME", "TOWN", "SERVED", "N_PLOT", "LEN_KM", "JOIN_MAIN", "GAP_M",
                    "OFF_M", "FLAG", "WHY", "DEEP_M", "DEP_M"),
    "connections": ("CAN_CONN", "CONN_NEED", "CONN_WHY", "LEN_M"),
    "trunk": (),
    "stations_rejected": (),
}

# Layers the EXCEPTIONS theme draws when the export produced them, and that are simply
# ABSENT when it did not - a clean run has no unlevelled route and no withdrawn crossing.
# Kept apart from NEEDS so a missing one is not reported as a defect: theme_exceptions()
# omits an empty folder on purpose, and "we checked and it is fine" has to stay tellable
# apart from "the layer was never written".
OPTIONAL = {
    "reaches_unlevelled": ("EDGE_UID", "US_NODE", "DS_NODE", "LEN_M", "QADF_M3D",
                           "LIFT_M", "GAP_KIND", "WHY"),
    "crossings_withdrawn": ("CROSS_ID", "WD_WHY"),
}


def load() -> "tuple[dict, list[str]]":
    """Read the published layers. Report what is absent; never quietly draw less."""
    missing: list[str] = []
    layers: dict = {}
    if not os.path.exists(EX.GPKG_OUT):
        raise SystemExit(
            f"no published export at {EX.GPKG_OUT}\n"
            f"run:  python s8_export.py build\n"
            f"(this file draws the published layers; it does not design anything)")
    import fiona
    have = set(fiona.listlayers(EX.GPKG_OUT))
    for name, cols in NEEDS.items():
        if name not in have:
            missing.append(f"layer '{name}' is not in {os.path.basename(EX.GPKG_OUT)}")
            continue
        g = gpd.read_file(EX.GPKG_OUT, layer=name)
        if g.crs is not None and g.crs.to_epsg() != CT.CRS_EPSG:
            g = g.to_crs(CT.CRS_EPSG)
        gone = [c for c in cols if c not in g.columns]
        if gone:
            missing.append(f"'{name}' has no {gone} - the themes that read them will be "
                           f"wrong or empty. Re-run s8_export.py build.")
        layers[name] = g
    for name, cols in OPTIONAL.items():
        if name not in have:
            continue
        g = gpd.read_file(EX.GPKG_OUT, layer=name)
        if g.crs is not None and g.crs.to_epsg() != CT.CRS_EPSG:
            g = g.to_crs(CT.CRS_EPSG)
        gone = [c for c in cols if c not in g.columns]
        if gone:
            missing.append(f"'{name}' has no {gone} - it is on the EXCEPTIONS theme and "
                           f"its folder will be unreadable. Re-run s8_export.py build.")
        layers[name] = g
    return layers, missing


def _n(gdf, mask=None) -> int:
    if gdf is None:
        return 0
    return int(len(gdf if mask is None else gdf[mask]))


def summary(layers: dict) -> None:
    """Every figure here is READ OFF A PUBLISHED FIELD. Nothing is recomputed - that is
    the whole change in this file, and it is the reason the numbers on this print-out
    cannot disagree with the schedule."""
    r = layers.get("reaches")
    nd = layers.get("nodes")
    sn = layers.get("subnetworks")
    st = layers.get("stations")
    rm = layers.get("rising_mains")
    cn = layers.get("connections")
    rej = layers.get("stations_rejected")
    trunk = layers.get("trunk")

    def line(label, value, note=""):
        print(f"  {label:<46} {value:>14}   {note}")

    print(f"\n{C.concept_banner()}\n")
    # WHERE THE LEVELS ON THIS DRAWING CAME FROM, read off the row and not off a constant
    # in this file. Two solvers published inverts for the same chambers until 2026-09-06;
    # a drawing that does not say which one it drew is how a stale depth gets quoted.
    if r is not None and "LEVELS_BY" in r.columns:
        by = r.LEVELS_BY.astype(str).value_counts()
        line("LEVELS ON THIS DRAWING", (by.index[0] if len(by) else "(blank)"),
             "LEVELS_BY, carried per row" if len(by) == 1 else
             "MIXED: " + ", ".join(f"{k} {v:,}" for k, v in by.items()))
        # and the same string the DXF title block and the KMZ description will carry, so
        # the print-out and the drawing cannot disagree about who levelled the network
        line("  ... banner written into the drawings", str(EX.LEVELS_SOURCE)[:60],
             "s8_export.LEVELS_SOURCE, set from the rows above")
    elif r is not None:
        # NOT a refusal to draw - the map is still true - but a drawing that cannot say
        # which solver produced its depths is how a stale depth gets quoted, and that has
        # to be on the print-out rather than in a comment.
        line("LEVELS ON THIS DRAWING", "NOT STATED",
             "the reaches layer carries no LEVELS_BY - re-run s8_export.py build")
    if r is not None:
        line("gravity sewer", f"{r.LEN_M.sum() / 1000:,.1f} km", "LEN_M, published")
    if nd is not None:
        line("chambers", f"{len(nd):,}",
             f"{len(nd) / max(1e-9, r.LEN_M.sum() / 1000):.1f} per km; built network 34.2")
    if trunk is not None and len(trunk):
        line("client main pipe", f"{trunk.LEN_M.sum() / 1000:,.1f} km",
             "AN INPUT - nothing here drains into it")
    if sn is not None:
        served = sn[sn.SERVED == 1]
        line("subnetworks", f"{len(served):,}", "one per connected component")
        short = served[served.JOIN_MAIN == 0]
        if len(short):
            line("  ... NOT reaching the main pipe", f"{len(short):,}",
                 f"worst {short.GAP_M.max():,.0f} m short")
        off = served[pd.to_numeric(served.OFF_M, errors="coerce").fillna(0) > 0]
        if len(off):
            line("  ... outlet off its own low point", f"{len(off):,}",
                 f"worst {off.OFF_M.max():,.0f} m")
        un = sn[sn.SERVED == 0]
        if len(un):
            line("areas the network does not reach", f"{len(un):,}",
                 f"{int(un.N_PLOT.sum()):,} plots, each with a reason")
    if st is not None:
        line("pumping stations", f"{len(st):,}",
             f"duty {st.Q_DUTY_LS.min():.1f}-{st.Q_DUTY_LS.max():.1f} L/s"
             if len(st) else "none")
        if len(st):
            line("  ... network each one captures", f"{st.CATCH_KM.sum():,.1f} km",
                 "CATCH_KM - concept rule 6 scores on this, not on the count")
    if rej is not None and len(rej):
        line("stations REMOVED at export", f"{len(rej):,}",
             "nothing drained into them - inheritance row 4")
    if rm is not None:
        line("force mains", f"{len(rm):,}",
             f"{rm.LEN_M.sum() / 1000:,.2f} km" if len(rm) else "none published")
        n_stp = _n(rm, rm.DS_TYPE == "stp") if len(rm) else 0
        if n_stp:
            line("  ... lifting ALL THE WAY TO THE WORKS", f"{n_stp:,}",
                 "concept rule 6 asks why")
    if nd is not None:
        drops = nd[nd.DROP_TYPE.astype(str) != "none"]
        line("drop structures", f"{len(drops):,}",
             ", ".join(f"{k}={v:,}" for k, v in drops.DROP_WHY.value_counts().items())
             if len(drops) else "")
        line("chambers past the cover cap", f"{_n(nd, nd.PAST_CAP == 1):,}",
             f"G203-p33, {C.MAX_COVER:g} m")
    ul = layers.get("reaches_unlevelled")
    if ul is not None and len(ul):
        line("routes NOBODY LEVELLED", f"{len(ul):,}",
             f"{ul.LEN_M.sum() / 1000:,.2f} km, OFF the reaches layer - "
             + ", ".join(f"{k}={v:,}" for k, v in ul.GAP_KIND.value_counts().items()))
    cw = layers.get("crossings_withdrawn")
    if cw is not None and len(cw):
        line("crossings WITHDRAWN", f"{len(cw):,}",
             "nothing crosses there any more - inheritance row 4")
    if cn is not None and "CAN_CONN" in cn.columns:
        bad = cn[cn.CAN_CONN == 0]
        line("plots that CANNOT connect", f"{len(bad):,}",
             f"of {len(cn):,}; worst needs the sewer {bad.CONN_NEED.max():.2f} m deeper"
             if len(bad) else "of %d" % len(cn))
    print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--themes", action="store_true", help="only the KMZ and the .qml")
    ap.add_argument("--dxf", action="store_true", help="only the drawing")
    ap.add_argument("--check", action="store_true",
                    help="say what is on disk and what the themes would miss")
    ap.add_argument("--plain", action="store_true",
                    help="skip the annotated drawing - geometry only, opens instantly")
    ap.add_argument("--stale-ok", action="store_true",
                    help="draw anyway from an export that failed its own `levels "
                         "coverage` gate. The banner still says so, on every drawing.")
    a = ap.parse_args(argv)

    layers, missing = load()
    for m in missing:
        print("  ! " + m)

    # ---- WHAT THE EXPORT ALREADY SAID ABOUT ITSELF, READ RATHER THAN RE-DERIVED --------
    # s8_export publishes a `levels coverage` row on `contract_check` and fails its own
    # verify() on it: below the alarm the two upstream files describe different chambers
    # and nothing in the export is quotable. This file drew a full, complete-looking KMZ
    # and DXF set from exactly that export without ever reading the row - a map of less
    # than half a network looks exactly like a map of all of it, which is the class of
    # defect this file's own header says it refuses to produce. Nothing is computed here;
    # the row is s8's, published, and read.
    blocking: list = []
    import fiona
    if "contract_check" in set(fiona.listlayers(EX.GPKG_OUT)):
        _chk = gpd.read_file(EX.GPKG_OUT, layer="contract_check", ignore_geometry=True)
        _cov = _chk[_chk.LAYER.astype(str) == "levels coverage"]
        if len(_cov) and int(_cov.PASS.iloc[0]) == 0:
            blocking.append(f"{_cov.RESULT.iloc[0]} - {_cov.DETAIL.iloc[0]}")
    else:
        # NOT a refusal: a layer set assembled by hand has no contract_check and is a
        # legitimate thing to draw. But the drawing then carries no verdict at all, and
        # that has to be said rather than assumed clean.
        print("  ! the export carries no `contract_check` layer, so nothing here can say "
              "whether it is quotable - run s8_export.py build for a judged one")
    for b in blocking:
        print("  !! " + b)

    # ---- THE BANNER THE DRAWINGS WILL CARRY, TAKEN OFF THE ROWS THEY DRAW --------------
    # `s8_export.LEVELS_SOURCE` is a module global that only `build()` sets. This file
    # calls write_dxf() and write_themes() directly, so on the fast path it was still the
    # import-time default - the RETIRED stand-in's tag - and every DXF title block and KMZ
    # description written from here named the wrong solver as the source of levels that in
    # fact came from s6. That banner exists to stop precisely that lie.
    _r = layers.get("reaches")
    if _r is None or "LEVELS_BY" not in _r.columns or not len(_r):
        EX.LEVELS_SOURCE = "UNSTATED - the published reaches carry no LEVELS_BY"
    else:
        _by = _r.LEVELS_BY.astype(str).value_counts()
        EX.LEVELS_SOURCE = (str(_by.index[0]) if len(_by) == 1 else
                            "MIXED: " + ", ".join(f"{k} {v:,}" for k, v in _by.items()))
    src = EX.LEVELS_SOURCE
    if a.check:
        for name, g in layers.items():
            print(f"  {name:<20} {len(g):>8,} features, {len(g.columns) - 1} fields")
        summary(layers)
        return 1 if (missing or blocking) else 0
    if blocking and not a.stale_ok:
        raise SystemExit(
            "\nREFUSING TO DRAW:\n  " + "\n  ".join(blocking)
            + "\n\nThe export says so itself, on its own `contract_check` layer, and "
              "`python s8_export.py verify` exits 1 on the same row. A drawing of less "
              "than the whole network looks exactly like a drawing of all of it.\n"
              "  fix:      python s6_levels.py   then   python s8_export.py build\n"
              "  or force: python make_overview.py --stale-ok")
    if blocking:
        EX.LEVELS_SOURCE = src + " - EXPORT FAILED ITS OWN levels coverage GATE"
        print("  !! drawing anyway (--stale-ok). The title block and the KMZ description "
              "carry the warning.")
    if missing:
        raise SystemExit(
            "\nREFUSING TO DRAW:\n  " + "\n  ".join(missing)
            + "\n\nA map drawn without a column the theme reads looks exactly like a "
              "complete one, which is the whole class of defect this project keeps paying "
              "for. Re-run\n    python s8_export.py build\n"
              "or use --check to see the whole picture first.")

    do_both = not (a.themes or a.dxf)
    if a.themes or do_both:
        arrows = EX.flow_arrows(layers["reaches"])
        files = EX.write_themes(layers, arrows)
        for theme, paths in files.items():
            kmz = [p for p in paths if p.endswith(".kmz")]
            print(f"  {theme:<12} {os.path.basename(kmz[0]) if kmz else '-':<28} "
                  f"+ {len(paths) - len(kmz)} QGIS styles")
    if a.dxf or do_both:
        for p in EX.write_dxf(layers, annotated=not a.plain):
            print(f"  {os.path.basename(p):<28} {os.path.getsize(p) / 1e6:8.1f} MB")

    summary(layers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
