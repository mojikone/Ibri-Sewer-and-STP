"""One KMZ to look at the design at a glance: subnetworks, the main pipe, the pumps.

Deliberately small and fast to open. Each subnetwork is DISSOLVED to a single line before it
is written - 56,740 reaches would make a file Google Earth struggles to pan, and at the zoom
you judge a layout from you cannot see an individual reach anyway.

    python make_kmz_overview.py
"""
import colorsys
import os
import sys
import warnings
import zipfile
from xml.sax.saxutils import escape

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
W11B = os.path.dirname(HERE)
GPKG = os.path.join(W11B, "shp", "W11b_export.gpkg")
OUT = os.path.join(W11B, "kmz", "W11b_overview.kmz")

WGS = 4326


def kml_colour(h, alpha="ff"):
    """KML is aabbggrr, not rrggbb - the bytes are reversed and alpha leads."""
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"{alpha}{b:02x}{g:02x}{r:02x}"


def palette(n):
    """n visually separated colours. Golden-ratio hue steps keep neighbours apart, which is
    the whole point when 195 subnetworks touch each other on a map."""
    out = []
    for i in range(n):
        h = (i * 0.61803398875) % 1.0
        s = 0.62 + 0.28 * ((i % 3) / 2)
        v = 0.72 + 0.24 * ((i % 2))
        r, g, b = colorsys.hsv_to_rgb(h, s, min(v, 1.0))
        out.append(f"{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}")
    return out


def coords(geom):
    """KML wants lon,lat,alt - and a MultiLineString becomes several <LineString>."""
    parts = geom.geoms if geom.geom_type.startswith("Multi") else [geom]
    return [" ".join(f"{x:.6f},{y:.6f},0" for x, y in p.coords)
            for p in parts if p.geom_type == "LineString" and len(p.coords) > 1]


def main():
    if not os.path.exists(GPKG):
        raise SystemExit("no export GeoPackage yet - run the chain first: " + GPKG)

    reaches = gpd.read_file(GPKG, layer="reaches").to_crs(WGS)
    trunk = gpd.read_file(GPKG, layer="trunk").to_crs(WGS)
    st = gpd.read_file(GPKG, layer="stations").to_crs(WGS)

    # ---- subnetworks, dissolved -------------------------------------------------------
    key = next((c for c in ("SUBNET", "SUBNET_ID", "PACKAGE") if c in reaches.columns), None)
    if key is None:
        raise SystemExit("no subnetwork column on the reach layer")
    reaches["_km"] = reaches.to_crs(32640).geometry.length / 1000.0
    grp = reaches.dissolve(by=key, aggfunc={"_km": "sum"}).reset_index()
    grp = grp.sort_values("_km", ascending=False).reset_index(drop=True)
    cols = palette(len(grp))

    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
             '<name>W11b - subnetworks, main pipe and pumps</name>',
             '<description>Each subnetwork dissolved to one line and given its own colour. '
             'The main pipe is the client-supplied alignment. Pump markers are scaled by '
             'duty flow and labelled with duty and lift.</description>']

    # styles
    for i, c in enumerate(cols):
        parts.append(f'<Style id="sn{i}"><LineStyle><color>{kml_colour(c)}</color>'
                     f'<width>2.2</width></LineStyle></Style>')
    parts.append('<Style id="trunk"><LineStyle><color>ff0000ff</color><width>6</width>'
                 '</LineStyle></Style>')
    for i, sc in enumerate((0.7, 1.0, 1.4, 1.9, 2.5)):
        parts.append(f'<Style id="pump{i}"><IconStyle><color>ff00ffff</color>'
                     f'<scale>{sc}</scale><Icon><href>http://maps.google.com/mapfiles/kml/'
                     f'shapes/donut.png</href></Icon></IconStyle>'
                     f'<LabelStyle><scale>0.8</scale></LabelStyle></Style>')

    # ---- folder 1: subnetworks --------------------------------------------------------
    parts.append('<Folder><name>Subnetworks ({:,})</name><open>0</open>'.format(len(grp)))
    for i, row in grp.iterrows():
        segs = coords(row.geometry)
        if not segs:
            continue
        parts.append(f'<Placemark><name>{escape(str(row[key]))} &#183; '
                     f'{row["_km"]:.1f} km</name><styleUrl>#sn{i}</styleUrl>'
                     f'<MultiGeometry>')
        for s in segs:
            parts.append(f'<LineString><tessellate>1</tessellate>'
                         f'<coordinates>{s}</coordinates></LineString>')
        parts.append('</MultiGeometry></Placemark>')
    parts.append('</Folder>')

    # ---- folder 2: the main pipe ------------------------------------------------------
    tk = float(trunk.to_crs(32640).geometry.length.sum() / 1000.0)
    parts.append(f'<Folder><name>Main pipe ({tk:.1f} km) - CLIENT INPUT</name><open>1</open>')
    for _, row in trunk.iterrows():
        for s in coords(row.geometry):
            parts.append(f'<Placemark><styleUrl>#trunk</styleUrl><LineString>'
                         f'<tessellate>1</tessellate><coordinates>{s}</coordinates>'
                         f'</LineString></Placemark>')
    parts.append('</Folder>')

    # ---- folder 3: pumps --------------------------------------------------------------
    q = pd.to_numeric(st.get("Q_DUTY_LS", pd.Series(0, index=st.index)),
                      errors="coerce").fillna(0.0)
    lift = pd.to_numeric(st.get("LIFT_M", pd.Series(0, index=st.index)),
                         errors="coerce").fillna(0.0)
    kw = pd.to_numeric(st.get("MOTOR_KW", pd.Series(0, index=st.index)),
                       errors="coerce").fillna(0.0)
    # five size bands by duty, so the marker says something at a glance
    bands = q.rank(pct=True).fillna(0)
    parts.append(f'<Folder><name>Pumping stations ({len(st)})</name><open>1</open>')
    for i, row in st.iterrows():
        b = min(4, int(bands.iloc[st.index.get_loc(i)] * 5))
        p = row.geometry
        if p is None or p.is_empty:
            continue
        pt = p if p.geom_type == "Point" else p.centroid
        nm = escape(str(row.get("NODE_REF") or row.get("NODE_UID") or "station"))
        desc = (f"duty {q.loc[i]:.1f} L/s &#183; lift {lift.loc[i]:.1f} m "
                f"&#183; {kw.loc[i]:.0f} kW")
        parts.append(f'<Placemark><name>{nm}</name><description>{desc}</description>'
                     f'<styleUrl>#pump{b}</styleUrl>'
                     f'<Point><coordinates>{pt.x:.6f},{pt.y:.6f},0</coordinates></Point>'
                     f'</Placemark>')
    parts.append('</Folder>')
    parts.append('</Document></kml>')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("doc.kml", "\n".join(parts))

    print(f"{OUT}")
    print(f"  {len(grp):,} subnetworks, {reaches['_km'].sum():,.1f} km of pipe")
    print(f"  main pipe {tk:.1f} km")
    print(f"  {len(st)} pumping stations, duty {q.min():.1f} to {q.max():.1f} L/s")
    print(f"  {os.path.getsize(OUT) / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
