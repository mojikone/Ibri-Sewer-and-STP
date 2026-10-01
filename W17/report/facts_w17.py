"""Facts of the sewer network options (Section 6.2 of Revision 4). Every number the text, the tables
and the charts of the options quote is read here, once, from the results W17/py/ writes, so the
text and the figures cannot disagree. Nothing is computed here beyond sums, counts and ratios.

Sources (all under W17/results/):
    S#/S#_summary.json   quantities, checks, pumping totals and plant flows of option S#
    S#/S#_pumps.csv      one row per pumping station: duty, rising main, head, power, energy
                         (both written by py/scenario_results.py from the SewerGEMS exports)
    loads_by_year.json   the plot load of every year, carried by the network and not (py/loads_summary.py)
    rising_mains.csv     the rising main routes (py/rising_mains.py)
The hydraulic model: SewerGEMS CONNECT 10.4, model IBRI_W17_R9 (S1 to S7 on Colebrook-White).
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
RES = os.path.join(W17, "results")
sys.path.insert(0, os.path.join(W17, "py"))
from routing import SCENARIOS, YEARS, OLD, routing, plant_of  # noqa: E402,F401

OPTIONS = [f"S{i}" for i in range(1, 8)]
MODEL = "IBRI_W17_R9"
_cache = {}


def fmt(x, nd=0):
    """Thousands separated, nd decimals."""
    return f"{x:,.{nd}f}"


def _json(path):
    if path not in _cache:
        with open(path, encoding="utf-8") as f:
            _cache[path] = json.load(f)
    return _cache[path]


def available():
    """The options whose results exist."""
    return [o for o in OPTIONS if os.path.exists(os.path.join(RES, o, f"{o}_summary.json"))]


def summary(o):
    return _json(os.path.join(RES, o, f"{o}_summary.json"))


def pumps(o):
    """Pumping stations of option o, largest duty first, numbers as numbers."""
    key = ("pumps", o)
    if key not in _cache:
        rows = list(csv.DictReader(open(os.path.join(RES, o, f"{o}_pumps.csv"), encoding="utf-8")))
        for r in rows:
            for k, v in r.items():
                try:
                    r[k] = float(v) if k not in ("ps", "old", "to", "kind", "route") else v
                except ValueError:
                    pass
            r["type"] = int(r["type"]); r["dn"] = int(r["dn"])
        _cache[key] = sorted(rows, key=lambda r: -r["duty"])
    return _cache[key]


def loads():
    return _json(os.path.join(RES, "loads_by_year.json"))


def name(s):
    """A subnetwork or plant site by its W17 name, the earlier outfall number in brackets."""
    return f"{s} ({OLD[s]})"


def text(o):
    return SCENARIOS[o]["text"]


def plants(o):
    """{site: {"avg": {year: m3/d}, "peak": {year: L/s}}} in the order of the plant list."""
    s = summary(o)
    return {z: {"avg": s["plants"][z]["avg_m3d"], "peak": s["plants"][z]["peak_ls"]} for z in s["stp"]}


def option_row(o):
    """One line of the comparison table."""
    s = summary(o); ps = pumps(o)
    longest = max(ps, key=lambda r: r["L"]) if ps else None
    highest = max(ps, key=lambda r: r["H"]) if ps else None
    return dict(
        option=o, text=text(o), n_plants=len(s["stp"]), plants=", ".join(name(z) for z in s["stp"]),
        pipe_km=s["pipe_km"], manholes=s["manholes"], mh_over_12=s["manholes_over_12"],
        mh_over_9=s["manholes_by_band"].get("9-12 m", 0) + s["manholes_by_band"].get(">12 m", 0),
        deepest=s["deepest"]["depth"], deepest_at=s["deepest"]["label"],
        n_ps=s["pumping_stations"], kw=s["kw"], mwh_2030=s["mwh_2030"], mwh_2070=s["mwh_2070"],
        rm_km=s["rising_main_m"] / 1000, longest_rm=longest, highest_head=highest,
        km_over_12=s["pipe_km_deeper_12"],
        avg_2070=sum(v["avg"]["2070"] for v in plants(o).values()),
        largest_plant_2070=max(v["avg"]["2070"] for v in plants(o).values()))


def checks_clean(o):
    """True when no pipe exceeds 3.0 m/s or its depth ratio in the 2070 run or any analysed year."""
    s = summary(o)
    runs = [s["checks_2070"]] + list(s["checks_years"].values())
    return all(r["v_over_3"] == 0 and r["dd_over"] == 0 for r in runs)


def retention_flags(o, minutes=30):
    """Stations whose rising main holds the 2030 average flow longer than the guideline's ideal."""
    return [r for r in pumps(o) if r["ret2030"] > minutes]


def od_classes(o):
    """Pipe length by outside diameter, km, as the summary holds it."""
    return {int(k): v for k, v in summary(o)["pipe_km_by_od"].items()}


if __name__ == "__main__":
    print("available:", available())
    for o in available():
        r = option_row(o)
        print(o, r["text"], "| plants", r["n_plants"], "| km", r["pipe_km"], "| >12 m", r["mh_over_12"],
              "| PS", r["n_ps"], "| kW", r["kw"], "| MWh", r["mwh_2030"], r["mwh_2070"], "| clean", checks_clean(o))
    print(loads())
