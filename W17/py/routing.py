"""STP options S1-S7: where each subnetwork's outfall flow goes, and the transfers that follow from it.

Labels are the W17 names (O1...O24); the engineer's list used the modeller's names, kept in OLD.
A transfer is an outfall pumped to a manhole of another subnetwork (a pattern load on that manhole,
not peaked again); a plant join is an outfall pumped straight to a plant (no network pipe to size).
Flows are additive in a steady run (tested: +100 L/s in, +100.000 L/s out), so the transfer from an
outfall = its own flow with no transfers + everything transferred into its subnetwork, upstream first.
"""
import csv, collections

OLD = {"O1": "O-1", "O2": "O-21", "O3": "O-2", "O4": "O-7", "O5": "O-20", "O6": "O-13", "O7": "O-4", "O8": "O-10",
       "O9": "O-3", "O10": "O-16", "O11": "O-17", "O12": "O-9", "O13": "O-19", "O14": "O-12", "O15": "O-18",
       "O16": "O-8", "O17": "O-23", "O18": "O-24", "O19": "O-11", "O20": "O-22", "O21": "O-6", "O22": "O-14",
       "O23": "O-15", "O24": "O-5"}

# engineer's list (2026-10-01), receiving manholes by their old label
BASE_TRANSFERS = [
    ("O7", "MH-18013"), ("O6", "MH-1510"), ("O8", "MH-1355"), ("O5", "MH-21582"), ("O4", "MH-649"),
    ("O3", "MH-14793"), ("O2", "MH-8112"), ("O23", "MH-18772"), ("O22", "MH-18772"), ("O21", "MH-14400"),
    ("O24", "MH-14400"), ("O13", "MH-17581"), ("O12", "MH-10049"), ("O11", "MH-12700"), ("O10", "MH-20234"),
    ("O14", "MH-18186"), ("O9", "MH-15726"), ("O15", "MH-16127"), ("O20", "MH-2710"), ("O19", "MH-9074"),
]

# STP outfalls, extra transfers, and outfalls pumped straight to a plant, per option
SCENARIOS = {
    "S1": dict(stp=["O1"], extra=[], joins={"O16": "O1", "O17": "O1", "O18": "O1"},
               text="centralised STP at O-1"),
    "S2": dict(stp=["O16"], extra=[("O1", "MH-21598")], joins={"O17": "O16", "O18": "O16"},
               text="centralised STP at O-8"),
    "S3": dict(stp=["O1", "O4"], extra=[], joins={"O16": "O1", "O17": "O1", "O18": "O1"},
               text="two STPs at O-1 and O-7"),
    "S4": dict(stp=["O1", "O9", "O4"], extra=[], joins={"O16": "O1", "O17": "O1", "O18": "O1"},
               text="three STPs at O-1, O-3, O-7"),
    "S5": dict(stp=["O1", "O3", "O9", "O4"], extra=[], joins={"O16": "O1", "O17": "O1", "O18": "O1"},
               text="four STPs at O-1, O-2, O-3, O-7"),
    "S6": dict(stp=["O1", "O3", "O9", "O4", "O16", "O22"], extra=[], joins={"O17": "O16", "O18": "O16", "O23": "O22"},
               text="six STPs at O-1, O-2, O-3, O-7, O-8, O-14"),
    "S7": dict(stp=["O1", "O16", "O22"], extra=[], joins={"O17": "O16", "O18": "O16", "O23": "O22"},
               text="three STPs at O-1, O-8, O-14"),
}
YEARS = ["2030", "2040", "2050", "2055", "2060", "2070"]
F0 = r"D:\VBOX\bridge\out\f0"
RENAME = r"D:\VBOX\bridge\out\inv\rename_nodes.csv"


def node_maps():
    old2new, new2id = {}, {}
    for r in csv.DictReader(open(RENAME, encoding="utf-8")):
        old2new[r["old"]] = r["new"]; new2id[r["new"]] = int(r["id"])
    return old2new, new2id


def routing(name):
    """Transfers (source outfall, receiving manhole new label, receiving subnetwork) and plant joins of one option."""
    sc = SCENARIOS[name]
    old2new, _ = node_maps()
    stp = set(sc["stp"])
    out = []
    for src, mh in BASE_TRANSFERS + sc["extra"]:
        if src in stp or src in sc["joins"]:
            continue
        new = old2new[mh]
        out.append((src, new, new.split("-M")[0]))
    return out, sc["joins"], stp


def plant_of(name):
    """Which plant every subnetwork drains to."""
    tr, joins, stp = routing(name)
    nxt = {s: r for s, _, r in tr}
    nxt.update(joins)
    res = {}
    for s in [f"O{i}" for i in range(1, 25)]:
        cur, seen = s, set()
        while cur in nxt and cur not in stp:
            seen.add(cur); cur = nxt[cur]
            if cur in seen:
                raise ValueError(f"{name}: loop at {cur}")
        if cur not in stp:
            raise ValueError(f"{name}: {s} ends at {cur}, which is not a plant")
        res[s] = cur
    return res


def read_f0(year):
    return {l.split(",")[0]: float(l.split(",")[1]) for l in open(rf"{F0}\f0_{year}.csv", encoding="utf-8-sig")
            if "," in l and l.split(",")[0].startswith("O") and l.split(",")[0][1:].isdigit()}


def transfers(name, year):
    """Cumulative outfall flow (m3/d, peak) of every subnetwork, and the transfer rows, upstream first."""
    tr, joins, stp = routing(name)
    f0 = read_f0(year)
    into = collections.defaultdict(list)
    for s, mh, r in tr:
        into[r].append(s)
    total = {}

    def flow(s):
        if s not in total:
            total[s] = f0.get(s, 0.0) + sum(flow(u) for u in into[s])
        return total[s]

    for s in f0:
        flow(s)
    rows = [(year, s, mh, r, total[s]) for s, mh, r in tr]
    return rows, total


if __name__ == "__main__":
    for name in SCENARIOS:
        p = plant_of(name)
        zones = collections.defaultdict(list)
        for s, z in p.items():
            zones[z].append(s)
        print(name, SCENARIOS[name]["text"], "->", {z: len(v) for z, v in zones.items()})
