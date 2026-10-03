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
from routing import SCENARIOS, YEARS, OLD, routing, plant_of, option_label  # noqa: E402,F401

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
    """A subnetwork or plant site by its current name only: the report never shows the earlier outfall numbers."""
    return s


def text(o):
    """The option in current names: 'two STPs, at O1 and O4'."""
    return option_label(o)


def plants(o):
    """{site: {"avg": {year: m3/d}, "peak": {year: L/s}, "inlet": m}} in the order of the plant list; inlet is the
    depth below ground of the gravity sewer arriving at the plant site."""
    s = summary(o)
    return {z: {"avg": s["plants"][z]["avg_m3d"], "peak": s["plants"][z]["peak_ls"],
                "inlet": s["plants"][z].get("inlet_depth_m")} for z in s["stp"]}


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
        largest_plant_2070=max(v["avg"]["2070"] for v in plants(o).values()),
        inlet_depths=" / ".join(f"{v['inlet']:.1f}" for v in plants(o).values()))


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


def od_lengths_m(o):
    """Pipe length by outside diameter, metres, from the model's unrounded pipe lengths (results/S#/S#_pipes.csv): the
    rows and the total of the quantity table, and the same source as the bill of quantities."""
    key = ("od_m", o)
    if key not in _cache:
        out = {}
        for r in csv.DictReader(open(os.path.join(RES, o, f"{o}_pipes.csv"), encoding="utf-8")):
            od = int(float(r["od"])); out[od] = out.get(od, 0.0) + float(r["length"])
        _cache[key] = out
    return _cache[key]


def km_od_at_least(o, od=1000):
    """Length of sewer of outside diameter od and over, km: the trunk sewers the options differ in."""
    return sum(v for k, v in od_classes(o).items() if k >= od)


def largest_od(o):
    return max(k for k, v in od_classes(o).items() if v > 0)


# The engineer's priority (2026-10-02): the three options taken to the appraisal, first to third; together they span
# the choice, one plant, three or six. The guidelines' three characters (PAM-GUD-201 Section 12.1, p95) are not tied
# to an option (engineer, 2026-10-03): each of the three is designed and costed under every character on the same
# network model, nine cases in all. The treated effluent network is designed on them.
RECOMMENDED = ["S1", "S4", "S6"]
CHARACTERS = ["established local practice", "international best practice", "sustainability-led"]

# The lift at a plant's inlet works, on the pumping stations' own concept values (py/scenario_results.py): the wet well
# 1.5 m below the arriving sewer, the inlet works 3.0 m above the ground, 65 per cent wire-to-water, no main.
WET_WELL_M, INLET_ABOVE_GROUND_M, EFFICIENCY = 1.5, 3.0, 0.65
MARGIN = 1.10      # the design margin of a new plant, PAM-GUD-201 Section 7.4.5, p73


def inlet_lift(o):
    """Energy to lift the flow at every plant's inlet works, MWh a year by model year, and the power at the 2070
    peak, kW: 9.81 x head x average volume / efficiency, the stations' rule with the static lift only."""
    out = {"plants": {}, "mwh": {y: 0.0 for y in YEARS}, "kw_2070": 0.0}
    for z, v in plants(o).items():
        head = v["inlet"] + WET_WELL_M + INLET_ABOVE_GROUND_M
        mwh = {y: 9.81 * head * v["avg"][y] / EFFICIENCY / 3600 * 365 / 1000 for y in YEARS}
        kw = 9.81 * head * v["peak"]["2070"] / 1000 / EFFICIENCY
        out["plants"][z] = dict(head=head, mwh=mwh, kw=kw)
        for y in YEARS:
            out["mwh"][y] += mwh[y]
        out["kw_2070"] += kw
    return out


def energy_total(o, year):
    """Pumping energy of the stations and the plant inlets together, MWh a year."""
    return summary(o)[f"mwh_{year}"] + inlet_lift(o)["mwh"][year]


def flood():
    """Flood exposure of the gravity sewers and the manholes, the same in every option (py/flood_exposure.py):
    length and count by hazard class, H1 to H6 and not flooded, for the 10, 25, 50 and 100-year floods."""
    return _json(os.path.join(RES, "flood_exposure.json"))


def flow_chain(year):
    """From the plots to the plants in one model year, m3/d. The same in every option: the pipes and their
    infiltration are; only the split between the plants differs."""
    L = loads(); y = L["years"][year]
    at = sum(v["avg"][year] for v in plants(available()[0]).values())
    return dict(plots=y["plot_load_m3d"], carried=y["carried_m3d"], outside=y["outside_m3d"],
                infiltration=L["infiltration_m3d"], at_plants=at, design=at * MARGIN)


if __name__ == "__main__":
    print("available:", available())
    for o in available():
        r = option_row(o)
        print(o, r["text"], "| plants", r["n_plants"], "| km", r["pipe_km"], "| >12 m", r["mh_over_12"],
              "| PS", r["n_ps"], "| kW", r["kw"], "| MWh", r["mwh_2030"], r["mwh_2070"], "| clean", checks_clean(o))
    print(loads())
