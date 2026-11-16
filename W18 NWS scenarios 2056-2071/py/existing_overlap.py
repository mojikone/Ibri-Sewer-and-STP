"""How much of the new network runs along streets the constructed 2006 network already serves.

The concept design does not rely on the existing network (its levels and diameters are not recorded): the areas it
serves are designed as if unsewered, and the new network carries all their flow (engineer, 2026-10-04). Where the
as-built survey shows an existing sewer can be kept, the new pipe in that street is not needed; this measures that
length, so the report can say how far the estimate errs on the safe side. The pipes are the same in every option.

    python existing_overlap.py        writes W17/results/existing_overlap.json
"""
import json
import os

import fiona
from shapely.geometry import shape
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
EXISTING = os.path.join(os.path.dirname(W17), "W7", "shp", "EXISTING_SEWERLINE.shp")     # OP_STATUE 1 = constructed
PIPES = os.path.join(W17, "Options 2026-10", "11_Network_options", "S1.gpkg")
OUT = os.path.join(W17, "results", "existing_overlap.json")
BUFFERS = (10, 15, 20)


def main():
    with fiona.open(EXISTING) as c:
        ex = unary_union([shape(f["geometry"]) for f in c if str(f["properties"].get("OP_STATUE")) == "1"])
    with fiona.open(PIPES, layer="pipes") as c:
        new = unary_union([shape(f["geometry"]) for f in c])
    res = {"existing_km": ex.length / 1000, "new_km": new.length / 1000, "within_m": {}}
    for b in BUFFERS:
        res["within_m"][str(b)] = {"new_km_along_existing": new.intersection(ex.buffer(b)).length / 1000,
                                   "existing_km_with_new_alongside": ex.intersection(new.buffer(b)).length / 1000}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
