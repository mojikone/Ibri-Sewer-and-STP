# -*- coding: utf-8 -*-
"""Turn the NAMA KMZ files into shapefiles we can measure and map.

The attributes live inside an HTML table in each placemark's description, so they have to
be pulled out row by row. The file itself carries the warning "Data is not reliable and
must be used only for reference purpose" — treat every number from it as indicative.
"""
import os
import re
import warnings
import zipfile

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

KMZ = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\Received\09-RECEIVED\NAMA\IBRI\WW\KMZ"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shp")
TMP = os.path.join(os.environ.get("TEMP", "."), "ibri_kmz")
ROW = re.compile(r"<tr[^>]*>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>", re.S)


def _txt(x):
    return re.sub(r"<[^>]+>", "", x).replace("&lt;Null&gt;", "").strip()


def read(name):
    os.makedirs(TMP, exist_ok=True)
    with zipfile.ZipFile(os.path.join(KMZ, name + ".kmz")) as z:
        z.extractall(os.path.join(TMP, name))
    g = gpd.read_file(os.path.join(TMP, name, "doc.kml")).to_crs(32640)
    rows = [{_txt(k): _txt(v) for k, v in ROW.findall(d)}
            for d in g["description"].fillna("")]
    a = pd.DataFrame(rows).replace("", None)
    # Drop the table's header cell from each name, then make the names unique. The KML
    # carries one attribute table per region, so "FID" and friends turn up more than once
    # and pandas hands back a DataFrame instead of a column.
    names, seen = [], {}
    for c in a.columns:
        c = c.split("\n")[-1]
        seen[c] = seen.get(c, 0) + 1
        names.append(c if seen[c] == 1 else f"{c}_{seen[c]}")
    a.columns = names
    keep = [c for c in a.columns if a[c].notna().any()][:40]   # shapefile field limit
    out = gpd.GeoDataFrame(a[keep], geometry=g.geometry.values, crs=32640)
    out["LEN_M"] = out.geometry.length if out.geom_type.iloc[0] != "Point" else 0.0
    return out


if __name__ == "__main__":
    for name in ("SEWERLINE", "FORCELINE", "STP_PT", "TE_LINE"):
        try:
            g = read(name)
        except Exception as e:
            print(f"{name}: SKIPPED ({e})")
            continue
        p = os.path.join(OUT, f"EXISTING_{name}.shp")
        g.to_file(p, encoding="utf-8")
        extra = "" if g.geom_type.iloc[0] == "Point" else \
            f", {g.geometry.length.sum()/1000:,.1f} km"
        print(f"{name}: {len(g)} features{extra} -> {os.path.basename(p)}")
