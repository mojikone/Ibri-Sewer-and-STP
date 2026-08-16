"""
Build Hydraulic/SHP/Towns/Towns.shp from Data/Received/2621/inception report - R0/Final_Boundary_IBRI.kmz

Source KMZ contents (ArcGIS "Layer to KML" export):
  - 26 Point placemarks  : NCSI settlement points, description table holds
                           'الرمز الوطني المميز للمعلم' (national feature code),
                           'الاسم' (Arabic name), 'Name' (English name)
  - 26 Polygon placemarks: IMP_Settlement_Pop settlement boundaries, nested
                           PopupInfo table holds NAMEEN, TOWN (census town code),
                           Pop_2023 .. Pop_2050
  -  1 Polygon placemark : name '0', Type='Proposed Utilities' -> project boundary,
                           NOT a town; written separately for reference.

Output: EPSG:32640 (WGS84 / UTM 40N) to match every other project layer.
DBF written UTF-8 with a .cpg sidecar so the Arabic names survive.
"""
import html
import re
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

ROOT = Path(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP")
KMZ = ROOT / "Data/Received/2621/inception report - R0/Final_Boundary_IBRI.kmz"
OUTDIR = ROOT / "Hydraulic/SHP/Towns"
EPSG_OUT = 32640

AR_CODE = "الرمز الوطني المميز للمعلم"
AR_NAME = "الاسم"


# ---------------------------------------------------------------- parsing ---
def kml_text(kmz: Path) -> str:
    with zipfile.ZipFile(kmz) as z:
        return z.read("doc.kml").decode("utf-8")


# <td>key</td><td>value</td>, but neither cell may wrap a nested <table> --
# the popup header cell is followed by a cell holding the whole inner table,
# and a naive non-greedy pair swallows the first real data row with it.
CELL = r"((?:(?!</?td|<table).)*?)"
KV = re.compile(rf"<td>{CELL}</td>\s*<td>{CELL}</td>", re.S)


def kv_table(desc: str) -> dict:
    """Flatten every <td>key</td><td>value</td> pair in a description blob."""
    d = html.unescape(html.unescape(desc))
    out = {}
    for k, v in KV.findall(d):
        k = re.sub(r"<[^>]+>", "", k).strip()
        v = re.sub(r"<[^>]+>", "", v).strip()
        if k and k not in out:
            out[k] = None if v in ("<Null>", "") else v
    return out


def rings(block: str, tag: str):
    """Coordinate rings of one <outerBoundaryIs>/<innerBoundaryIs> tag."""
    for m in re.findall(rf"<{tag}>\s*<LinearRing>.*?<coordinates>(.*?)</coordinates>",
                        block, re.S):
        pts = [tuple(float(c) for c in p.split(",")[:2]) for p in m.split()]
        if len(pts) >= 4:
            yield pts


def polygons(pm: str):
    """All <Polygon> of a placemark, holes included."""
    for pb in re.findall(r"<Polygon>.*?</Polygon>", pm, re.S):
        outer = list(rings(pb, "outerBoundaryIs"))
        inner = list(rings(pb, "innerBoundaryIs"))
        for o in outer:
            yield Polygon(o, inner)


def main():
    kml = kml_text(KMZ)
    pms = re.findall(r"<Placemark.*?</Placemark>", kml, re.S)

    pts, polys, boundary = [], [], []
    for pm in pms:
        name = re.search(r"<name>(.*?)</name>", pm, re.S).group(1).strip()
        desc = re.search(r"<description>(.*?)</description>", pm, re.S)
        att = kv_table(desc.group(1)) if desc else {}
        if "<Point>" in pm:
            lon, lat = [float(c) for c in
                        re.search(r"<coordinates>(.*?)</coordinates>", pm, re.S)
                        .group(1).strip().split(",")[:2]]
            pts.append(dict(NAME_EN=att.get("Name") or name,
                            NAME_AR=att.get(AR_NAME),
                            CODE=att.get(AR_CODE),
                            lon=lon, lat=lat))
        elif "<Polygon>" in pm:
            geoms = list(polygons(pm))
            if not geoms:
                continue
            g = MultiPolygon(geoms) if len(geoms) > 1 else geoms[0]
            rec = dict(name=name, geometry=g, **att)
            (boundary if att.get("Type") == "Proposed Utilities" else polys).append(rec)

    pt = pd.DataFrame(pts)
    pg = pd.DataFrame(polys)
    print(f"parsed: {len(pt)} points, {len(pg)} town polygons, {len(boundary)} boundary polygons")

    # --------------------------------------------------- dissolve by town ---
    pg["NAME_EN"] = pg["NAMEEN"].fillna(pg["name"])
    popcols = sorted([c for c in pg.columns if re.fullmatch(r"Pop_\d{4}", c)])
    agg = {c: "first" for c in ["TOWN"] + popcols}
    diss = (gpd.GeoDataFrame(pg, geometry="geometry", crs="EPSG:4326")
            .dissolve(by="NAME_EN", aggfunc=agg, as_index=False))
    diss["geometry"] = diss.geometry.apply(
        lambda g: g if g.is_valid else g.buffer(0))
    print(f"dissolved to {len(diss)} town polygons "
          f"(multipart merges: {len(pg) - len(diss)})")

    # ------------------------------------------- attach point attributes ---
    ptg = gpd.GeoDataFrame(pt, geometry=gpd.points_from_xy(pt.lon, pt.lat),
                           crs="EPSG:4326")
    # 1) name join, 2) verify/recover by point-in-polygon
    m = diss.merge(ptg.drop(columns="geometry"), on="NAME_EN", how="left")
    sj = gpd.sjoin(ptg, diss[["NAME_EN", "geometry"]], how="inner",
                   predicate="within").rename(columns={"NAME_EN_right": "POLY_NAME"})
    mismatch = sj[sj["NAME_EN_left"] != sj["POLY_NAME"]]
    if len(mismatch):
        print("WARNING: point falls inside a differently-named polygon:")
        print(mismatch[["NAME_EN_left", "POLY_NAME"]].to_string(index=False))
    outside = set(ptg.NAME_EN) - set(sj.NAME_EN_left)
    if outside:
        print(f"NOTE: {len(outside)} point(s) not inside any town polygon: "
              f"{sorted(outside)}")
    nopoly = sorted(set(ptg.NAME_EN) - set(diss.NAME_EN))
    nopoint = sorted(set(diss.NAME_EN) - set(ptg.NAME_EN))
    if nopoly:
        print(f"NOTE: point(s) with no polygon (not in output): {nopoly}")
    if nopoint:
        print(f"NOTE: polygon(s) with no point (NAME_AR/CODE null): {nopoint}")

    # ------------------------------------------------------------ output ---
    out = m.to_crs(EPSG_OUT)
    out["AREA_KM2"] = (out.geometry.area / 1e6).round(4)
    for c in popcols:
        out[c] = pd.to_numeric(out[c], errors="coerce").astype("Int64")
    out = out[["NAME_EN", "NAME_AR", "CODE", "TOWN", "AREA_KM2"] + popcols
              + ["geometry"]].sort_values("NAME_EN").reset_index(drop=True)
    out.insert(0, "TOWN_ID", range(1, len(out) + 1))

    OUTDIR.mkdir(parents=True, exist_ok=True)
    shp = OUTDIR / "Towns.shp"
    out.to_file(shp, driver="ESRI Shapefile", encoding="utf-8")
    (OUTDIR / "Towns.cpg").write_text("UTF-8")
    out.to_file(OUTDIR / "Towns.geojson", driver="GeoJSON")

    if boundary:
        bg = gpd.GeoDataFrame(boundary, geometry="geometry", crs="EPSG:4326") \
                .to_crs(EPSG_OUT)
        bg["AREA_KM2"] = (bg.geometry.area / 1e6).round(3)
        bg[["Type", "Area", "AREA_KM2", "geometry"]].to_file(
            OUTDIR / "Project_Boundary_kmz.shp", driver="ESRI Shapefile",
            encoding="utf-8")
        print(f"boundary polygon written, area {bg.AREA_KM2.iloc[0]} km2 "
              f"(KMZ attribute Area = {bg.Area.iloc[0]})")

    print(f"\nwrote {shp} : {len(out)} features, {len(out.columns)-1} fields")
    print(out[["TOWN_ID", "NAME_EN", "NAME_AR", "CODE", "TOWN", "AREA_KM2",
               "Pop_2025", "Pop_2050"]].to_string(index=False))


if __name__ == "__main__":
    main()
