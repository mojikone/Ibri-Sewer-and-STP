"""Which settlements are worth sewering, which are not, and which need the economics.

r5 measured every settlement's exclusive pipe - the metres that exist only to serve it,
internal streets plus the spur out to where its flow first mixes with somebody else's.
This turns that into a recommendation by applying the guideline's own tests:

  G201 p80 sec 8.1  a Remote Area is a settlement under 500 residents OR under 100 plots at
                    the end of the design period, or 25 km or more from the centralised
                    network, or separated from it by a geographical barrier.
  G201 p83 sec 8.4  Remote Areas are served by septic tanks (OPSDC), holding tanks emptied
                    by vacuum tanker, or a package plant for 50 - 5,000 inhabitants.
  G203 p96         package plants "typically serve populations up to 5,000 inhabitants
                    (approx. 750 m3/day)".
  G201 p96 sec 12.4 what settles a marginal case: NPV over 25 years at 5 %.

Nothing here prices anything - the unit rates are not in the project yet. It sorts the
settlements into the three groups where the answer is already clear, is already clear the
other way, or genuinely turns on a cost the project does not hold.

Run:  python r6_tranches.py
"""
import os
import sys
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")
OUT_RUN = os.path.join(C.OUT, "run")

BREAK_M_PER_PROP = 20.0     # set by the distribution, see the printed gap table
PKG_MAX_POP = 5000          # G201 p83 / G203 p96
PKG_MIN_POP = 50            # G201 p83
G201_MAX_POP = 500
G201_MAX_PLOTS = 100
SETTLE_M = 60.0


def main():
    st = pd.read_csv(os.path.join(OUT_RUN, "r5_settlements.csv"))
    st = st.sort_values("m_per_property").reset_index(drop=True)

    # ---- where the break is, read off the data rather than chosen ----------
    print("the gap in the distribution (settlements ordered by m of exclusive pipe "
          "per property):")
    v = st.m_per_property.to_numpy()
    jump = np.diff(v)
    k = np.argsort(-jump)[:8]
    for i in sorted(k):
        print(f"   {v[i]:8.1f} -> {v[i+1]:8.1f} m/property : a gap of {jump[i]:7.1f}, "
              f"{i+1} settlements below it holding "
              f"{st.props[:i+1].sum():,.0f} of {st.props.sum():,.0f} properties "
              f"({100*st.props[:i+1].sum()/st.props.sum():.2f} %)")

    # ---- distance to the core: the conveyance a connection actually needs --
    allp = gpd.read_file(os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg"),
                         layer="plot_loads")
    blob = gpd.GeoDataFrame(
        geometry=[unary_union(allp.geometry.buffer(SETTLE_M))], crs=C.EPSG)
    blob = blob.explode(index_parts=False).reset_index(drop=True)
    blob["SID"] = blob.index
    core_sid = int(st.loc[st.props.idxmax(), "SID"])
    core = blob.loc[blob.SID == core_sid, "geometry"].iloc[0]
    blob["km_to_core"] = (blob.geometry.distance(core) / 1000).round(2)
    st["km_to_core"] = st.SID.map(
        blob.set_index("SID").km_to_core).round(2)

    # ---- classification ----------------------------------------------------
    st["G201_remote"] = (st.people < G201_MAX_POP) | (st.plots < G201_MAX_PLOTS)
    st["pkg_eligible"] = (st.people >= PKG_MIN_POP) & (st.people <= PKG_MAX_POP)

    # The test is the COST OF SERVING, not the size. A one-plot "settlement" sitting on a
    # street the core network already runs down has zero exclusive pipe and should
    # obviously be connected; sorting it into "do not sewer" because it is small was the
    # first version's mistake and it put 60 free connections in the wrong tranche.
    def tranche(r):
        if r.props <= 0.01:
            return "0 - no load to collect"
        if r.SID == core_sid:
            return "1 - sewer (core)"
        if r.m_per_property < BREAK_M_PER_PROP:
            return "1 - sewer"
        if r.m_per_property >= 150:
            return "3 - do not sewer"
        if r.G201_remote and r.m_per_property >= 80:
            return "3 - do not sewer"
        return "2 - economics decide"

    st["TRANCHE"] = st.apply(tranche, axis=1)

    def solution(r):
        if r.TRANCHE.startswith("0"):
            return "nothing to collect - no property on it"
        if r.TRANCHE.startswith("1"):
            return "connect to the network"
        if r.people < PKG_MIN_POP:
            return "septic / holding tank + tanker (G201 p83)"
        if r.pkg_eligible:
            return "package plant 50-5,000 pe (G201 p83, G203 p96)"
        return "local works - above the package-plant range"

    st["SOLUTION"] = st.apply(solution, axis=1)

    cols = ["SID", "village", "plots", "props", "people", "q", "pipe_km_exclusive",
            "m_per_property", "m_per_m3d", "km_to_core", "km_to_built_net",
            "G201_remote", "pkg_eligible", "TRANCHE", "SOLUTION"]
    st[cols].round(2).to_csv(os.path.join(OUT_RUN, "r6_tranches.csv"), index=False)

    print("\nTRANCHES")
    g = st.groupby("TRANCHE").agg(
        settlements=("SID", "size"), plots=("plots", "sum"),
        properties=("props", "sum"), people=("people", "sum"),
        flow_m3d=("q", "sum"), exclusive_km=("pipe_km_exclusive", "sum"))
    g["pct_of_flow"] = (100 * g.flow_m3d / st.q.sum()).round(2)
    g["pct_of_pipe"] = (100 * g.exclusive_km / st.pipe_km_exclusive.sum()).round(1)
    g["m_per_property"] = (g.exclusive_km * 1000 / g.properties).round(1)
    print(g.round(1).to_string())

    print("\nTRANCHE 2 and 3 in full - every settlement not clearly worth connecting:")
    sub = st[~st.TRANCHE.str.startswith("1")].sort_values("m_per_property",
                                                          ascending=False)
    print(sub[["SID", "village", "plots", "props", "people", "q",
               "pipe_km_exclusive", "m_per_property", "km_to_core",
               "TRANCHE", "SOLUTION"]].round(1).to_string(index=False))

    print("\nthe settlements that are NOT remote by the G201 p80 size test "
          "but still cost more than the break:")
    odd = st[(~st.G201_remote) & (st.m_per_property >= BREAK_M_PER_PROP)]
    print(odd[["SID", "village", "plots", "props", "people", "q",
               "pipe_km_exclusive", "m_per_property", "km_to_core"]]
          .round(1).to_string(index=False) if len(odd) else "   none")

    print("\nthe large outlying settlements - too big for a package plant, far from the "
          "core, so the choice is conveyance against a satellite works:")
    big = st[(st.people > PKG_MAX_POP) & (st.km_to_core > 2.0)]
    print(big[["SID", "village", "plots", "props", "people", "q",
               "pipe_km_exclusive", "m_per_property", "km_to_core",
               "km_to_built_net"]].round(1).to_string(index=False)
          if len(big) else "   none")


if __name__ == "__main__":
    main()
