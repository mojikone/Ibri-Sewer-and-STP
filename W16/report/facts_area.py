"""Facts of the study-area section (1.2): ground levels, roads, climate, wind, flood hazard classes.

Everything measured comes from analysis/study_area/study_area_stats.json, written by
analysis/study_area/study_area_stats.py; the text, the charts and the map boxes all read it here,
so they cannot disagree. Sources:

    ground    the 0.5 m terrain sampled at every plot; the built plots of each settlement
    roads     the road centrelines as supplied, clipped to the updated project boundary
    climate   NASA POWER (MERRA-2), daily, 2001-2020, at the existing STP
    wind      NASA POWER (MERRA-2), hourly at 10 m, 2015-2024, at the existing STP
    hazard    Oman Flood Mapping project, MAFWR; Australian hazard classes (AIDR Guideline 7-3, 2017)
"""
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis", "study_area", "study_area_stats.json")
_cache = {}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# AIDR (2017) Guideline 7-3, Flood hazard: the limit of each class on the
# product of depth and velocity (m2/s), on depth (m) and on velocity (m/s). Verified 2026-09-17.
HAZARD_CLASSES = [
    ("H1", "Generally safe for people, vehicles and buildings", "0.3", "0.3", "2.0"),
    ("H2", "Unsafe for small vehicles", "0.6", "0.5", "2.0"),
    ("H3", "Unsafe for vehicles, children and the elderly", "0.6", "1.2", "2.0"),
    ("H4", "Unsafe for people and vehicles", "1.0", "2.0", "2.0"),
    ("H5", "Unsafe for people and vehicles; all buildings vulnerable to structural damage, "
           "the less robust to failure", "4.0", "4.0", "4.0"),
    ("H6", "Unsafe for people and vehicles; all building types vulnerable to failure", "above 4.0", "no limit", "no limit"),
]


def stats():
    if "s" not in _cache:
        with open(_PATH, encoding="utf-8") as fh:
            _cache["s"] = json.load(fh)
    return _cache["s"]


def ground():
    return stats()["ground"]


def roads():
    return stats()["roads"]


def climate():
    return stats()["climate"]


def wind():
    return stats()["wind"]


def below_stp():
    """Settlements whose built ground lies, at the median, below the ground at the existing STP."""
    g = ground()
    return [r for r in g["settlements"] if r["z_med"] < g["stp_ground"]]


def sector_of(bearing):
    secs = wind()["sectors"]
    return secs[int(((bearing % 360.0) + 11.25) // 22.5) % 16]


def downwind(max_km=8.0):
    """For each settlement within max_km of the existing STP: the sector the wind must blow FROM to
    carry air from the STP to it, and the share of all hours and of night hours it does."""
    w = wind(); out = []
    for r in ground()["settlements"]:
        if r["dist_km"] > max_km:
            continue
        sec = sector_of(r["bearing_deg"] + 180.0)
        out.append({"name": r["name"], "dist_km": r["dist_km"], "towards": sector_of(r["bearing_deg"]), "wind_from": sec,
                    "all": w["all"]["sector_total"][sec], "night": w["night"]["sector_total"][sec]})
    return out


def top_sectors(which="all", n=3):
    st = wind()[which]["sector_total"]
    return sorted(st.items(), key=lambda kv: -kv[1])[:n]


def axis_share(which="all"):
    """Share of hours on the two prevailing quarters: north-west (WNW to N) and south-east (ESE to S)."""
    st = wind()[which]["sector_total"]
    nw = sum(st[k] for k in ("WNW", "NW", "NNW", "N")); se = sum(st[k] for k in ("ESE", "SE", "SSE", "S"))
    return nw, se
