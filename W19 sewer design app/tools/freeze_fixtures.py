"""Copies, READ ONLY, everything phases 0-1 compare against into tests/fixtures/, gzipped where it saves space, with
MANIFEST.json (source, bytes, sha256 of the uncompressed file). Run once; re-running overwrites the fixtures."""
import glob, gzip, hashlib, json, os
import geopandas as gpd

W19 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(W19)
W18 = os.path.join(REPO, "W18 NWS scenarios 2056-2071")
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
BRIDGE = r"D:\VBOX\bridge\out"
GEO = os.path.join(REPO, "W17", "Options 2026-10", "11_Network_options", "S1.gpkg")
FIX = os.path.join(W19, "tests", "fixtures")
CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]
files = {}


def put(src, rel, gz=True):
    raw = open(src, "rb").read()
    dest = os.path.join(FIX, rel + (".gz" if gz else ""))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(gzip.compress(raw, 9, mtime=0) if gz else raw)
    files[rel + (".gz" if gz else "")] = dict(source=src, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


inp = os.path.join(R, "inputs")
for f in ("catalogue.csv", "conduits_network.csv", "conduits_start_sizes.csv", "manholes_network.csv"):
    put(os.path.join(inp, f), f"inputs/{f}", gz=f != "catalogue.csv")
put(os.path.join(R, "fixed_stations.json"), "inputs/fixed_stations.json", gz=False)
put(os.path.join(W18, "results", "loads", "manhole_loads.csv"), "inputs/manhole_loads.csv")
put(os.path.join(W18, "results", "rising_mains.csv"), "inputs/rising_mains.csv", gz=False)
put(os.path.join(W18, "results", "rising_mains.gpkg"), "inputs/rising_mains.gpkg")
for f in sorted(glob.glob(os.path.join(BRIDGE, "w18", "f0", "f0_*.csv"))):
    put(f, f"bridge/f0/{os.path.basename(f)}", gz=False)
put(os.path.join(BRIDGE, "inv", "rename_nodes.csv"), "bridge/inv/rename_nodes.csv")

# W17's option GeoPackage: only the two layers the split reads (pipe lines by label; outfalls with their ground)
tmp = os.path.join(W19, "work", "S1_pipes_outfalls.gpkg"); os.makedirs(os.path.dirname(tmp), exist_ok=True)
if os.path.exists(tmp): os.remove(tmp)
gpd.read_file(GEO, layer="pipes")[["label", "geometry"]].to_file(tmp, layer="pipes", driver="GPKG")
gpd.read_file(GEO, layer="outfalls")[["label", "ground", "geometry"]].to_file(tmp, layer="outfalls", driver="GPKG")
put(tmp, "geo/S1.gpkg")

for c in CASES:
    C = os.path.join(R, c)
    for rel in ("design.json", "selfcleansing_pipes.csv", "named/links.csv", "named/nodes.csv", "named/stations.csv",
                "named/naming.json", "products/stations.csv", "products/plants.csv", "products/quantities.json",
                f"split/cuts_{c}.csv", f"split/joins_{c}.csv", f"split/summary_{c}.json",
                f"exports/conduits_{c}a.csv",
                f"exports/transfers_{c}.csv", f"exports/lift_transfers_{c}.csv"):
        put(os.path.join(C, rel), f"golden/{c}/{rel}", gz=rel.endswith(".csv"))
C = os.path.join(R, "SC1-2056")
for rel in ("exports/conduits_SC1-2056-at-2031.csv", "exports/conduits_SC1-2056-at-2036.csv", "split/pipes_SC1-2056.csv", "split/nodes_SC1-2056.csv"):
    put(os.path.join(C, rel), f"golden/SC1-2056/{rel}")
for rel in ("conduits_SC1-2056.csv", "conduits_SC1-2056-at-2031.csv"):
    put(os.path.join(BRIDGE, "w18", "final", "SC1-2056", rel), f"sewergems/SC1-2056/{rel}")

json.dump(dict(frozen_from="W18 NWS scenarios 2056-2071 and D:/VBOX/bridge/out, read only", files=files),
          open(os.path.join(FIX, "MANIFEST.json"), "w", encoding="utf-8"), indent=1)
total = sum(os.path.getsize(os.path.join(FIX, r)) for r in files)
print(f"{len(files)} fixtures, {total / 1e6:.1f} MB on disk")
