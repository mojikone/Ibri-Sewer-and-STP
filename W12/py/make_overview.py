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
    a = ap.parse_args(argv)

    layers, missing = load()
    for m in missing:
        print("  ! " + m)
    if a.check:
        for name, g in layers.items():
            print(f"  {name:<20} {len(g):>8,} features, {len(g.columns) - 1} fields")
        summary(layers)
        return 1 if missing else 0
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
