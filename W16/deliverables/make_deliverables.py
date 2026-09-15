"""The data package behind the Design Basis Report, for NWS: every item as KMZ and shapefile,
and as Excel where it is a table. Nothing re-derived: every value is read from the frozen
W14 layers and the facts modules the reports use.

    python make_deliverables.py        -> Ibri_Design_Basis_Data_R0/ (five folders, README) and the zip

01_boundaries            project boundary received (Inception Report KMZ, 521 km2) and updated
                         (531 km2); the settlement polygons received (25 rows, Al Aynayn in two parts)
02_settlements           the 25 settlements: people and Q by year, saturation, OR, the peak flow
03_meters                the 33,971 electricity meters as is
04_plots                 the 77,265 plots: meters by tariff, use, people and Q for the stored years
05_identified_projects   the identified projects and special consumption, register and footprints

KMZ in WGS 84 (Google Earth), shapefiles in UTM zone 40 North (EPSG:32640), Excel in the
report's look. Styles follow the report maps: land use as the B02 map, saturation flow as B03.
"""
import datetime
import html
import math
import os
import shutil
import sys
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import xlsxwriter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
W14 = os.path.join(REPO, "W14")
SHP = os.path.join(os.path.dirname(REPO), "SHP")
DATA = os.path.join(os.path.dirname(os.path.dirname(REPO)), "Data")
sys.path.insert(0, os.path.join(REPO, "W16", "report"))
sys.path.insert(0, os.path.join(REPO, "W16", "report_basis"))
import facts_w14 as F  # noqa: E402
import facts_basis as B  # noqa: E402

PKG = "Ibri_Design_Basis_Data_R0"
OUT = os.path.join(HERE, PKG)
YEARS = [2024, 2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060, 2065, 2070]
UTM = 32640
NAVY = "#1F497D"

USE_NAME = {"Residential": "Residential", "Residential-Commercial": "Residential-Commercial", "Commercial": "Commercial",
            "Government": "Government", "Agricultural": "Agricultural", "Industrial": "Industrial", "Heritage": "Heritage",
            "Unmetered": "Empty (unmetered)"}
USE_COLOUR = {"Residential": "#FFE600", "Residential-Commercial": "#F5A742", "Commercial": "#E03C31", "Government": "#3498DB",
              "Agricultural": "#4CAF50", "Industrial": "#9B59B6", "Heritage": "#8d6e63", "Empty (unmetered)": None}
USE_ORDER = list(USE_COLOUR)
Q_CLASSES = [(0, 100, "under 100", "#eff3ff"), (100, 500, "100 to 500", "#c6dbef"), (500, 1000, "500 to 1,000", "#9ecae1"),
             (1000, 2500, "1,000 to 2,500", "#6baed6"), (2500, 5000, "2,500 to 5,000", "#3182bd"), (5000, 1e12, "over 5,000", "#08519c")]
CAT_NAME = {"domestic": "Domestic", "non_domestic": "Non-domestic", "government": "Governmental", "agricultural": "Agricultural", "special": "Special consumption"}
CAT_COLOUR = {"Domestic": "#C0504D", "Non-domestic": "#E5A32B", "Governmental": "#3498DB", "Agricultural": "#4CAF50", "Special consumption": "#9B59B6"}


# ------------------------------------------------------------------ KML
def kml_colour(hex_rgb, alpha="ff"):
    h = hex_rgb.lstrip("#")
    return alpha + h[4:6] + h[2:4] + h[0:2]


def _ring(coords):
    return " ".join(f"{c[0]:.6f},{c[1]:.6f},0" for c in coords)


def _poly(p):
    s = f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{_ring(p.exterior.coords)}</coordinates></LinearRing></outerBoundaryIs>"
    for r in p.interiors:
        s += f"<innerBoundaryIs><LinearRing><coordinates>{_ring(r.coords)}</coordinates></LinearRing></innerBoundaryIs>"
    return s + "</Polygon>"


def geom_xml(g):
    t = g.geom_type
    if t == "Polygon":
        return _poly(g)
    if t == "MultiPolygon":
        return "<MultiGeometry>" + "".join(_poly(p) for p in g.geoms) + "</MultiGeometry>"
    if t == "Point":
        return f"<Point><coordinates>{g.x:.6f},{g.y:.6f},0</coordinates></Point>"
    if t == "LineString":
        return f"<LineString><coordinates>{_ring(g.coords)}</coordinates></LineString>"
    if t == "MultiLineString":
        return "<MultiGeometry>" + "".join(f"<LineString><coordinates>{_ring(l.coords)}</coordinates></LineString>" for l in g.geoms) + "</MultiGeometry>"
    raise ValueError(t)


def esc(s):
    return html.escape("" if s is None else str(s), quote=False)


def fmtv(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}"
    if isinstance(v, (float, np.floating)):
        return f"{v:,.1f}" if abs(v - round(v)) > 1e-9 else f"{int(round(v)):,}"
    return str(v)


class KML:
    """A KMZ with styles, nested folders and placemarks whose attributes go into a Schema so
    Google Earth shows them as a table in the balloon."""

    def __init__(self, name, fields=None):
        self.name = name; self.styles = []; self.body = []; self.fields = fields or []

    def style_poly(self, sid, fill, line, width=1.0, alpha="99", label=True):
        fill_xml = f"<PolyStyle><color>{kml_colour(fill, alpha)}</color><fill>1</fill><outline>1</outline></PolyStyle>" if fill else "<PolyStyle><fill>0</fill><outline>1</outline></PolyStyle>"
        self.styles.append(f'<Style id="{sid}"><LineStyle><color>{kml_colour(line)}</color><width>{width}</width></LineStyle>{fill_xml}'
                           f'<LabelStyle><scale>{1 if label else 0}</scale></LabelStyle><BalloonStyle><text>$[name]<br/>$[description]</text></BalloonStyle></Style>')

    def style_point(self, sid, colour, scale=0.5, label=False):
        self.styles.append(f'<Style id="{sid}"><IconStyle><color>{kml_colour(colour)}</color><scale>{scale}</scale>'
                           f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle>'
                           f'<LabelStyle><scale>{1 if label else 0}</scale></LabelStyle></Style>')

    def style_label(self, sid, colour="#FFFFFF", scale=1.0):
        self.styles.append(f'<Style id="{sid}"><IconStyle><scale>0</scale></IconStyle><LabelStyle><color>{kml_colour(colour)}</color><scale>{scale}</scale></LabelStyle></Style>')

    def open_folder(self, name, visible=True):
        self.body.append(f"<Folder><name>{esc(name)}</name><open>0</open>{'' if visible else '<visibility>0</visibility>'}")

    def close_folder(self):
        self.body.append("</Folder>")

    def schema(self, sid, fields):
        """fields: (short name, display name). A Schema keeps the big layers small: each
        placemark repeats only the short names, Google Earth shows the display names."""
        self.styles.append(f'<Schema name="{sid}" id="{sid}">' + "".join(
            f'<SimpleField type="string" name="{k}"><displayName>{esc(d)}</displayName></SimpleField>' for k, d in fields) + "</Schema>")

    @staticmethod
    def placemark_xml(name, geom, sid, data=None, sdata=None, schema=None):
        d = ""
        if data:
            rows = "".join(f"<tr><td style='color:#5A5A5A;padding-right:8px'>{esc(k)}</td><td><b>{esc(fmtv(v))}</b></td></tr>" for k, v in data)
            d = f"<description><![CDATA[<table style='font-family:Calibri,Arial;font-size:12px'>{rows}</table>]]></description>"
        elif sdata:
            d = (f'<ExtendedData><SchemaData schemaUrl="#{schema}">' + "".join(f'<SimpleData name="{k}">{esc(fmtv(v))}</SimpleData>' for k, v in sdata)
                 + "</SchemaData></ExtendedData>")
        return f"<Placemark><name>{esc(name)}</name><styleUrl>#{sid}</styleUrl>{d}{geom_xml(geom)}</Placemark>"

    def placemark(self, name, geom, sid, data=None, sdata=None, schema=None):
        self.body.append(self.placemark_xml(name, geom, sid, data, sdata, schema))

    @staticmethod
    def document(name, parts):
        return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
                f"<name>{esc(name)}</name>" + "".join(parts) + "</Document></kml>")

    def save(self, path, extra=None):
        """extra: {path inside the KMZ: kml text}, for files a NetworkLink in the document loads on demand."""
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("doc.kml", self.document(self.name, self.styles + self.body).encode("utf-8"))
            for n, txt in (extra or {}).items():
                z.writestr(n, txt.encode("utf-8"))
        return path

    @staticmethod
    def network_link(name, bounds, href, min_pixels=128):
        """A NetworkLink loaded when its region shows at min_pixels or more on screen."""
        w, s, e, n = bounds
        return (f"<NetworkLink><name>{esc(name)}</name><open>0</open><Region><LatLonAltBox><north>{n:.6f}</north><south>{s:.6f}</south>"
                f"<east>{e:.6f}</east><west>{w:.6f}</west></LatLonAltBox><Lod><minLodPixels>{min_pixels}</minLodPixels><maxLodPixels>-1</maxLodPixels></Lod></Region>"
                f"<Link><href>{href}</href><viewRefreshMode>onRegion</viewRefreshMode></Link></NetworkLink>")


# ------------------------------------------------------------------ Excel, the report's look
class XL:
    def __init__(self, path):
        self.wb = xlsxwriter.Workbook(path, {"nan_inf_to_errors": True})
        self.f_title = self.wb.add_format({"bold": True, "font_color": NAVY, "font_size": 12, "font_name": "Calibri"})
        self.f_src = self.wb.add_format({"italic": True, "font_color": "#808080", "font_size": 9, "font_name": "Calibri"})
        self.f_head = self.wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": NAVY, "text_wrap": True, "valign": "vcenter", "align": "center", "font_name": "Calibri", "font_size": 10.5, "border": 1, "border_color": "#FFFFFF"})
        self.f_head_l = self.wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": NAVY, "text_wrap": True, "valign": "vcenter", "align": "left", "font_name": "Calibri", "font_size": 10.5, "border": 1, "border_color": "#FFFFFF"})
        base = {"font_name": "Calibri", "font_size": 10.5, "bottom": 1, "bottom_color": "#D9D9D9", "valign": "vcenter"}
        self.f_txt = self.wb.add_format({**base, "align": "left"})
        self.f_ctr = self.wb.add_format({**base, "align": "center"})
        self.f_int = self.wb.add_format({**base, "align": "center", "num_format": "#,##0"})
        self.f_dec = self.wb.add_format({**base, "align": "center", "num_format": "#,##0.0"})
        self.f_dec2 = self.wb.add_format({**base, "align": "center", "num_format": "0.00"})
        self.f_tot = self.wb.add_format({**base, "bold": True, "align": "center", "num_format": "#,##0", "top": 2, "top_color": NAVY})
        self.f_tot_l = self.wb.add_format({**base, "bold": True, "align": "left", "top": 2, "top_color": NAVY})
        self.f_tot_dec = self.wb.add_format({**base, "bold": True, "align": "center", "num_format": "#,##0.0", "top": 2, "top_color": NAVY})

    def sheet(self, name, title, source, headers, rows, kinds, widths, totals=None, left_cols=(0,)):
        """kinds: per column 't' text, 'c' centred text, 'i' integer, 'd' one decimal, 'f' two decimals."""
        ws = self.wb.add_worksheet(name)
        ws.hide_gridlines(2)
        ws.write(0, 0, title, self.f_title); ws.write(1, 0, source, self.f_src)
        for j, h in enumerate(headers):
            ws.write(3, j, h, self.f_head_l if j in left_cols else self.f_head)
        ws.set_row(3, 32)
        fm = {"t": self.f_txt, "c": self.f_ctr, "i": self.f_int, "d": self.f_dec, "f": self.f_dec2}
        for i, r in enumerate(rows, 4):
            for j, v in enumerate(r):
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    ws.write_blank(i, j, None, fm[kinds[j]])
                elif kinds[j] in ("i", "d", "f"):
                    ws.write_number(i, j, float(v), fm[kinds[j]])
                else:
                    ws.write(i, j, v, fm[kinds[j]])
        if totals:
            i = 4 + len(rows)
            for j, v in enumerate(totals):
                if v is None:
                    ws.write_blank(i, j, None, self.f_tot)
                elif isinstance(v, str):
                    ws.write(i, j, v, self.f_tot_l if j in left_cols else self.f_tot)
                else:
                    ws.write_number(i, j, float(v), self.f_tot_dec if kinds[j] == "d" else self.f_tot)
        for j, w in enumerate(widths):
            ws.set_column(j, j, w)
        ws.freeze_panes(4, 1)
        return ws

    def close(self):
        self.wb.close()


# ------------------------------------------------------------------ helpers
def folder(name):
    p = os.path.join(OUT, name); os.makedirs(p, exist_ok=True); return p


def write_shp(gdf, path):
    g = gdf.copy()
    if g.crs is None:
        g = g.set_crs(UTM)
    elif g.crs.to_epsg() != UTM:
        g = g.to_crs(UTM)
    g.to_file(path, driver="ESRI Shapefile")
    return path


def wgs(gdf):
    g = gdf if gdf.crs is not None else gdf.set_crs(UTM)
    return g.to_crs(4326)


def q_class(q):
    for lo, hi, label, col in Q_CLASSES:
        if lo <= q < hi:
            return label, col
    return Q_CLASSES[-1][2], Q_CLASSES[-1][3]


# ------------------------------------------------------------------ 01 boundaries
def boundaries(manifest):
    d = folder("01_boundaries")
    rec = gpd.read_file(os.path.join(DATA, "Received", "2621", "inception report - R0", "Final_Boundary_IBRI.kmz"), layer="Project_boundary")
    rec = rec.to_crs(UTM)[["geometry"]]; rec["SOURCE"] = "Inception Report R0, Final_Boundary_IBRI.kmz"; rec["AREA_KM2"] = (rec.geometry.area / 1e6).round(2)
    upd = gpd.read_file(os.path.join(SHP, "Study area", "Project Boundary.shp"))[["geometry"]]
    upd["SOURCE"] = "Project boundary updated (the report maps)"; upd["AREA_KM2"] = (upd.geometry.area / 1e6).round(2)
    towns = gpd.read_file(os.path.join(SHP, "Towns", "Towns.shp"))
    for name, g, colour, what in (("Project_boundary_received", rec, "#C0504D", f"the project boundary as received in the Inception Report package, {rec.AREA_KM2.iloc[0]:.1f} km2"),
                                  ("Project_boundary_updated", upd, NAVY, f"the project boundary as updated for the report maps, {upd.AREA_KM2.iloc[0]:.1f} km2")):
        write_shp(g, os.path.join(d, name + ".shp"))
        k = KML(name.replace("_", " ")); k.style_poly("b", None, colour, 3.0)
        for _, r in wgs(g).iterrows():
            k.placemark(name.replace("_", " "), r.geometry, "b", [("Area, km2", r.AREA_KM2), ("Source", r.SOURCE)])
        k.save(os.path.join(d, name + ".kmz"))
        manifest.append(("01_boundaries", f"{name}.kmz, .shp", what))
    write_shp(towns, os.path.join(d, "Settlement_boundaries_received.shp"))
    k = KML("Settlement boundaries received"); k.style_poly("s", None, "#C0504D", 2.0); k.style_label("lab", "#FFFFFF", 0.9)
    tw = wgs(towns)
    for _, r in tw.iterrows():
        k.placemark(r.NAME_EN, r.geometry, "s", [("Settlement", r.NAME_EN), ("Arabic", r.NAME_AR), ("Code", r.CODE), ("Area, km2", r.AREA_KM2),
                                                ("People 2024 (series)", r.Pop_2024), ("People 2055 (series)", r.Pop_2055), ("People 2100 (series)", r.Pop_2100)])
    k.open_folder("Names")
    for _, r in tw.iterrows():
        k.placemark(r.NAME_EN, r.geometry.representative_point(), "lab")
    k.close_folder()
    k.save(os.path.join(d, "Settlement_boundaries_received.kmz"))
    manifest.append(("01_boundaries", "Settlement_boundaries_received.kmz, .shp",
                     "the 25 settlement polygons as received with the Inception Report (Al Aynayn drawn as two parts, so 26 polygons), with the client's population series 2023 to 2100"))
    print("01 boundaries: received", rec.AREA_KM2.iloc[0], "km2, updated", upd.AREA_KM2.iloc[0], "km2, settlements", len(towns))


# ------------------------------------------------------------------ 02 settlements
def settlement_rows():
    s = gpd.read_file(os.path.join(W14, "shp", "Settlements_merged.shp"))
    names = {r["key"]: r["name"] for r in F.settlement_table()}
    rows = []
    for _, r in s.iterrows():
        rec = {"key": r.SETTLE, "name": names.get(r.SETTLE, r.SETTLE.title()), "area": float(r.AREA_KM2), "or": float(r.OR_S), "props": int(r.PROPS),
               "sat_year": int(r.SAT_YEAR), "sat_pop": float(r.SAT_POP), "sat_q": float(r.SAT_Q), "geometry": r.geometry}
        for y in YEARS:
            rec[f"p{y}"] = float(r[f"POP_{y}"]); rec[f"q{y}"] = float(r[f"Q_{y}"])
        for tag, q, pop in (("2055", rec["q2055"], rec["p2055"]), ("sat", rec["sat_q"], rec["sat_pop"])):
            props = pop / rec["or"]
            if props > 100:
                rec[f"pk{tag}"] = B.merrimack(q) / 86.4; rec[f"pf{tag}"] = "Merrimack"
            else:
                rec[f"pk{tag}"] = q * B.peltier_pf(q) / 86.4; rec[f"pf{tag}"] = "Peltier"
        rows.append(rec)
    rows.sort(key=lambda r: -r["p2024"])
    return rows


def settlements(manifest):
    d = folder("02_settlements")
    rows = settlement_rows()
    t = F.totals()
    # Excel
    heads = (["Settlement"] + [f"People {y}" for y in YEARS] + [f"Q {y}, m³/d" for y in YEARS]
             + ["Saturation year", "People at saturation", "Q at saturation, m³/d", "OR", "Properties 2024", "Area, km²",
                "Peak flow 2055, l/s", "Formula 2055", "Peak flow at saturation, l/s", "Formula at saturation"])
    kinds = ["t"] + ["i"] * len(YEARS) + ["d"] * len(YEARS) + ["c", "i", "d", "f", "i", "d", "d", "c", "d", "c"]
    widths = [22] + [11] * len(YEARS) + [12] * len(YEARS) + [11, 12, 12, 7, 11, 9, 12, 11, 12, 11]
    xrows = [[r["name"]] + [r[f"p{y}"] for y in YEARS] + [r[f"q{y}"] for y in YEARS]
             + [r["sat_year"], r["sat_pop"], r["sat_q"], r["or"], r["props"], r["area"], r["pk2055"], r["pf2055"], r["pksat"], r["pfsat"]] for r in rows]
    tot_q55 = sum(r["q2055"] for r in rows); tot_qs = sum(r["sat_q"] for r in rows)
    totals = (["Study area"] + [sum(r[f"p{y}"] for r in rows) for y in YEARS] + [sum(r[f"q{y}"] for r in rows) for y in YEARS]
              + [max(r["sat_year"] for r in rows), sum(r["sat_pop"] for r in rows), tot_qs, sum(r["p2024"] for r in rows) / sum(r["props"] for r in rows),
                 sum(r["props"] for r in rows), sum(r["area"] for r in rows), B.merrimack(tot_q55) / 86.4, "Merrimack", B.merrimack(tot_qs) / 86.4, "Merrimack"])
    xl = XL(os.path.join(d, "Settlements.xlsx"))
    xl.sheet("Settlements", "The 25 settlements: people and average sewage flow by year, saturation, persons per property and the peak flow",
             "Design Basis Report R0 (Sections 3, 6 and 7); W14/shp/Settlements_merged.shp. OR = persons per property adopted. Peak flow = the settlement's own average flow peaked, "
             "Merrimack (G201 p71) where the settlement has over 100 properties in that year, Peltier (p72) otherwise; no infiltration, no STP margin. "
             "The study-area peak is Merrimack on the whole flow, not the sum of the settlements' peaks.",
             heads, xrows, kinds, widths, totals=totals)
    ws = xl.wb.add_worksheet("Notes")
    ws.hide_gridlines(2); ws.set_column(0, 0, 26); ws.set_column(1, 1, 120)
    notes = [("People", "The settlement's people in the year, the series with the overflow (Decision 4): a full settlement's further growth moves to its neighbours."),
             ("Q", "Average sewage flow of the settlement's plots in the year, m³/d: domestic, non-domestic, governmental and special, after the return ratios; no infiltration."),
             ("Saturation", "The year the settlement's land is full under the overflow, and its people and flow then. The study area is full in 2070."),
             ("OR", "Persons per property adopted for the settlement: the 2024 series population divided by the domestic meters, floor 4.0, cap 6.12, 4.0 for settlements under a thousand people (Decision 2)."),
             ("Peak flow", "For a trunk carrying the settlement alone: Merrimack Qpdf = 2.65 Qadf^0.879 (Ml/d) over 100 properties, Peltier PF = 1.5 + 1/sqrt(Qm, l/s) at 100 or fewer; properties in the year = people / OR. Add 720 l/d per km of sewer upstream for infiltration."),
             ("Rounding", "Each settlement's people are whole numbers, so the study-area line is their sum and can differ from the report's plot-based total by a few people (349,031 against 349,029 in 2070)."),
             ("Source", f"Packaged {datetime.date.today().isoformat()} from the frozen W14 layers; the same figures as the report.")]
    ws.write(0, 0, "Notes", xl.f_title)
    for i, (a, b) in enumerate(notes, 2):
        ws.write(i, 0, a, xl.f_txt); ws.write(i, 1, b, xl.f_txt)
    xl.close()
    # shapefile
    g = gpd.GeoDataFrame([{**{"SETTLE": r["key"], "NAME": r["name"]}, **{f"P{y}": round(r[f"p{y}"]) for y in YEARS}, **{f"Q{y}": round(r[f"q{y}"], 1) for y in YEARS},
                           "SAT_YEAR": r["sat_year"], "SAT_POP": round(r["sat_pop"]), "SAT_Q": round(r["sat_q"], 1), "OR": round(r["or"], 4), "PROPS": r["props"],
                           "AREA_KM2": round(r["area"], 3), "PK2055_LS": round(r["pk2055"], 1), "PK2055_F": r["pf2055"], "PKSAT_LS": round(r["pksat"], 1), "PKSAT_F": r["pfsat"],
                           "geometry": r["geometry"]} for r in rows], crs=UTM)
    write_shp(g, os.path.join(d, "Settlements.shp"))
    # KMZ
    k = KML("Settlements: people, flow and the peak")
    for i, (lo, hi, label, col) in enumerate(Q_CLASSES):
        k.style_poly(f"q{i}", col, NAVY, 1.5, alpha="99")
    k.style_label("lab", "#FFFFFF", 1.0)
    gw = wgs(g)
    for cls_i, (lo, hi, label, col) in enumerate(Q_CLASSES):
        members = [r for r in rows if lo <= r["sat_q"] < hi]
        if not members:
            continue
        k.open_folder(f"Q at saturation {label} m³/d")
        for r in members:
            geom = gw.loc[gw.SETTLE == r["key"], "geometry"].iloc[0]
            data = ([("Settlement", r["name"])] + [(f"People {y}", round(r[f"p{y}"])) for y in YEARS] + [(f"Q {y}, m³/d", round(r[f"q{y}"], 1)) for y in YEARS]
                    + [("Saturation year", r["sat_year"]), ("People at saturation", round(r["sat_pop"])), ("Q at saturation, m³/d", round(r["sat_q"], 1)),
                       ("OR, persons per property", round(r["or"], 2)), ("Properties 2024", r["props"]), ("Area, km²", round(r["area"], 2)),
                       (f"Peak flow 2055, l/s ({r['pf2055']})", round(r["pk2055"], 1)), (f"Peak flow at saturation, l/s ({r['pfsat']})", round(r["pksat"], 1))])
            k.placemark(r["name"], geom, f"q{cls_i}", data)
        k.close_folder()
    k.open_folder("Names")
    for r in rows:
        geom = gw.loc[gw.SETTLE == r["key"], "geometry"].iloc[0]
        k.placemark(r["name"], geom.representative_point(), "lab")
    k.close_folder()
    k.save(os.path.join(d, "Settlements.kmz"))
    manifest.append(("02_settlements", "Settlements.xlsx, .kmz, .shp",
                     "the 25 settlements: people and average sewage flow for 2024, 2025 and every five years to 2070, the saturation year and people, OR (persons per property), the peak flow for a trunk (2055 and saturation); coloured by the flow at saturation as the report's map"))
    print("02 settlements:", len(rows), "| 2070 people", round(sum(r["p2070"] for r in rows)), "vs facts", t["pop_ult"])
    return rows


# ------------------------------------------------------------------ 03 meters
def meters(manifest, names):
    d = folder("03_meters")
    m = gpd.read_file(os.path.join(W14, "shp", "ELE_meters_on_plots.shp"))
    m["PLOT_NO"] = m.PLOT_FID.map(lambda i: int(i) + 1 if int(i) >= 0 else None)   # the plot's number in 04_plots
    m["CATEGORY"] = m.GUD.map(CAT_NAME)
    m["SETTLE_N"] = m.SETTLE.map(lambda k: names.get(k, str(k).title()))
    m["EASTING"] = m.geometry.x.round(2); m["NORTHING"] = m.geometry.y.round(2)
    for ext in ("shp", "shx", "dbf", "prj", "cpg"):
        src = os.path.join(W14, "shp", f"ELE_meters_on_plots.{ext}")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(d, f"Electricity_meters.{ext}"))
    # Excel
    heads = ["Meter", "Tariff (as received)", "NAMA category", "CRT use found", "Plot no. (04_plots)", "Settlement", "Placement", "Property", "Easting", "Northing"]
    rows = [[i + 1, r.TARIFF, r.CATEGORY, ("" if pd.isna(r.USE) else r.USE), r.PLOT_NO, r.SETTLE_N, r.PLACE, int(r.PROPERTY), float(r.EASTING), float(r.NORTHING)]
            for i, r in enumerate(m.itertuples())]
    xl = XL(os.path.join(d, "Electricity_meters.xlsx"))
    xl.sheet("Meters", "The 33,971 electricity meters (2024 accounts) with the NAMA category each tariff folds into, the plot and the settlement",
             "Design Basis Report R0, Section 3; W14/shp/ELE_meters_on_plots.shp. Placement: inside a plot, snapped to the nearest plot within 15 m, or free (no plot within 15 m, no load). "
             "Plot no. is the plot's number in 04_plots. Property = 1 for a domestic meter. Coordinates in UTM zone 40 North.",
             heads, rows, ["i", "t", "c", "c", "i", "c", "c", "i", "f", "f"], [8, 40, 16, 16, 12, 18, 10, 9, 12, 12], left_cols=(1,))
    xl.close()
    # KMZ
    k = KML("Electricity meters")
    for cat, col in CAT_COLOUR.items():
        k.style_point("c" + cat[:3].lower().replace("-", ""), col, 0.45)
    k.style_point("free", "#000000", 0.6)
    k.schema("m", [("tar", "Tariff"), ("cat", "NAMA category"), ("crt", "CRT use found"), ("plot", "Plot no. (04_plots)"), ("st", "Settlement"), ("pl", "Placement")])
    mw = wgs(m)
    for cat in CAT_COLOUR:
        sub = mw[mw.CATEGORY == cat]
        k.open_folder(f"{cat} ({len(sub):,})", visible=(cat == "Domestic"))
        sid = "c" + cat[:3].lower().replace("-", "")
        for r in sub.itertuples():
            k.placemark(r.TARIFF, r.geometry, "free" if r.PLACE == "free" else sid, schema="m",
                        sdata=[("tar", r.TARIFF), ("cat", r.CATEGORY), ("crt", "" if pd.isna(r.USE) else r.USE), ("plot", "" if pd.isna(r.PLOT_NO) else str(int(r.PLOT_NO))), ("st", r.SETTLE_N), ("pl", r.PLACE)])
        k.close_folder()
    k.save(os.path.join(d, "Electricity_meters.kmz"))
    manifest.append(("03_meters", "Electricity_meters.xlsx, .kmz, .shp",
                     "the 33,971 electricity meters as received (2024), with the tariff, the NAMA category it folds into, the plot and the settlement; the KMZ has a folder per category, only Domestic switched on, the 126 free meters in black"))
    print("03 meters:", len(m))


# ------------------------------------------------------------------ 04 plots
def plots(manifest, names):
    d = folder("04_plots")
    p = F.plots()
    p["USE"] = p.DERIVED.map(USE_NAME).fillna(p.DERIVED)
    p["SETTLE_N"] = p.SETTLE.map(lambda k: names.get(k, str(k).title()))
    p["STATUS"] = p.Buiding_St.map({"EXisting": "Existing", "Future": "Future"}).fillna(p.Buiding_St)
    cols = [("SETTLE_N", "SETTLE"), ("Classes", "CADASTRE"), ("STATUS", "STATUS"), ("AREA_M2", "AREA_M2"),
            ("N_DOM", "M_PRIMARY"), ("N_DOMADD", "M_ADDIT"), ("N_COM", "M_COMM"), ("N_GOV", "M_GOV"), ("N_AGR", "M_AGR"), ("N_CRT", "M_CRT"), ("N_IND", "M_IND"), ("N_ACC", "M_TOTAL"),
            ("USE", "USE"), ("POP", "POP_2024"), ("POP_2030", "POP_2030"), ("POP_2055", "POP_2055"), ("POP_ULT", "POP_SAT"),
            ("QADF", "Q_2024"), ("Q_2030", "Q_2030"), ("Q_2055", "Q_2055"), ("Q_ULT", "Q_SAT"), ("SAT_YEAR", "SAT_YEAR")]
    g = p[[c for c, _ in cols] + ["geometry"]].rename(columns=dict(cols))
    g["AREA_M2"] = g.AREA_M2.round(1)
    for c in ("POP_2024", "POP_2030", "POP_2055", "POP_SAT"):
        g[c] = g[c].round(1)
    for c in ("Q_2024", "Q_2030", "Q_2055", "Q_SAT"):
        g[c] = g[c].round(3)
    g.insert(0, "PLOT_NO", range(1, len(g) + 1))
    write_shp(g, os.path.join(d, "Plots.shp"))
    # Excel
    heads = ["Plot no.", "Settlement", "Cadastre class", "Status", "Area, m²", "Primary meters", "Additional meters", "Commercial meters", "Government meters",
             "Agricultural meters", "Large-consumer (CRT) meters", "Industrial meters", "Total meters", "Use", "People 2024", "People 2030", "People 2055", "People at saturation",
             "Q 2024, m³/d", "Q 2030, m³/d", "Q 2055, m³/d", "Q at saturation, m³/d", "Saturation year"]
    kinds = ["i", "t", "c", "c", "d", "i", "i", "i", "i", "i", "i", "i", "i", "c", "d", "d", "d", "d", "f", "f", "f", "f", "c"]
    widths = [8, 18, 20, 9, 10, 9, 9, 9, 9, 9, 10, 9, 9, 22, 9, 9, 9, 11, 10, 10, 10, 12, 10]
    xl = XL(os.path.join(d, "Plots.xlsx"))
    f = {"t": xl.f_txt, "c": xl.f_ctr, "i": xl.f_int, "d": xl.f_dec, "f": xl.wb.add_format({"font_name": "Calibri", "font_size": 10.5, "bottom": 1, "bottom_color": "#D9D9D9", "align": "center", "num_format": "#,##0.000"})}
    ws = xl.wb.add_worksheet("Plots"); ws.hide_gridlines(2)
    ws.write(0, 0, "The 77,265 cadastral plots: meters by tariff, the use, people and average sewage flow for 2024, 2030, 2055 and saturation", xl.f_title)
    ws.write(1, 0, "Design Basis Report R0 (Sections 3, 4 and 7); W14/shp/PLOTS_load.shp. Plot no. is the plot's row in the layer (the same number in the KMZ, the shapefile and the meters' table). "
                   "Meters counted by tariff group; CRT = the large-consumer tariffs, each resolved to a category by public data. "
                   "Use as determined from the meters and the satellite image (Decision 3); the treatment plant's compound as Government. Q in m³/d after the return ratios, no infiltration.", xl.f_src)
    for j, h in enumerate(heads):
        ws.write(3, j, h, xl.f_head_l if j == 1 else xl.f_head)
    ws.set_row(3, 32)
    vals = g.drop(columns="geometry").values
    for i, row in enumerate(vals, 4):
        for j, v in enumerate(row):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                ws.write_blank(i, j, None, f[kinds[j]])
            elif kinds[j] in ("i", "d", "f"):
                ws.write_number(i, j, float(v), f[kinds[j]])
            else:
                ws.write(i, j, str(v), f[kinds[j]])
    for j, w in enumerate(widths):
        ws.set_column(j, j, w)
    ws.freeze_panes(4, 2); ws.autofilter(3, 0, 3 + len(vals), len(heads) - 1)
    xl.close()
    # KMZ: one file; a NetworkLink per settlement that Google Earth loads when the settlement is in
    # view, each with a subfolder per use; the plot's attributes through a Schema to keep it small
    k = KML("Plots: meters, use, people and flow")
    styles = []
    for use, col in USE_COLOUR.items():
        sid = "u" + str(USE_ORDER.index(use))
        if col:
            k.style_poly(sid, col, "#4a4a4a", 0.6, alpha="99", label=False)
        else:
            k.style_poly(sid, None, "#4a4a4a", 0.8, label=False)
    short = ["no", "st", "cad", "stat", "area", "mp", "ma", "mc", "mg", "mag", "mcrt", "mi", "mt", "use", "p24", "p30", "p55", "psat", "q24", "q30", "q55", "qsat", "sat"]
    k.schema("plot", list(zip(short, heads)))
    styles, k.styles = k.styles, []   # the styles and the schema go into every settlement's file, not the index
    fields = ["PLOT_NO"] + [c for _, c in cols]
    gw = wgs(g)
    order = [r["name"] for r in sorted(({"name": n, "n": (gw.SETTLE == n).sum()} for n in gw.SETTLE.unique()), key=lambda r: -r["n"])]
    extra = {}
    for s_name in order:
        sub = gw[gw.SETTLE == s_name]
        parts = list(styles)
        for use in USE_ORDER:
            su = sub[sub.USE == use]
            if len(su) == 0:
                continue
            parts.append(f"<Folder><name>{esc(use)} ({len(su):,})</name><open>0</open>{'' if use != 'Empty (unmetered)' else '<visibility>0</visibility>'}")
            sid = "u" + str(USE_ORDER.index(use))
            for r in su.itertuples(index=False):
                rec = r._asdict()
                parts.append(KML.placemark_xml(f"Plot {rec['PLOT_NO']}", rec["geometry"], sid, sdata=[(s, str(rec[f]) if s == "no" else rec[f]) for s, f in zip(short, fields)], schema="plot"))
            parts.append("</Folder>")
        fn = "plots/" + "".join(ch if ch.isalnum() else "_" for ch in s_name) + ".kml"
        extra[fn] = KML.document(f"{s_name}: {len(sub):,} plots", parts)
        k.body.append(KML.network_link(f"{s_name} ({len(sub):,} plots)", sub.total_bounds, fn))
    k.save(os.path.join(d, "Plots.kmz"), extra=extra)
    manifest.append(("04_plots", "Plots.xlsx, .kmz, .shp",
                     "the 77,265 plots: meters by tariff group and the total, the use (eight classes), people and average sewage flow for 2024, 2030, 2055 and saturation, the saturation year; the KMZ has a folder per settlement and a subfolder per use, coloured as the report's land-use map, empty plots switched off"))
    print("04 plots:", len(g), "| uses", g.USE.value_counts().to_dict())


# ------------------------------------------------------------------ 05 identified projects
PROJECTS = [
    # site, type, where, size, metered as, treatment in the basis, load, status
    ("Al Tayyeb industrial area", "Industrial estate, identified project", "Al Araqi, north-east of the town", "93.8 ha, 205 industrial plots", "1,044 accounts on the Commercial tariff",
     "Special consumption, outside the 22 % ratio: an assumed workforce of 4,500 at 93 l/d (dry industry), spread over the industrial plots by area", "418 m³/d water, 226 m³/d sewage", "Included; workforce and water use requested"),
    ("Tanam industrial area", "Industrial estate, identified project", "Al Makhtibyah, 2.5 km east of the STP", "61.1 ha, 106 industrial plots", "410 Commercial accounts, 10 CRT, the one Industrial-tariff account",
     "Special consumption: an assumed workforce of 1,800 at 93 l/d, spread by plot area", "167 m³/d water, 90 m³/d sewage", "Included; workforce and water use requested"),
    ("Ibri industrial (town workshops)", "Workshops in the town fabric", "Hayy Al Mazra / Al Orobah", "12.3 ha", "402 Commercial and 130 additional-account meters",
     "Non-domestic through the 22 % ratio, placed on its meters", "in the ratios", "No separate treatment"),
    ("MOT Centre", "Government yard", "Bu Khabi, next to the Police HQ", "7.1 ha", "2 CRT accounts (governmental)", "Governmental through the 14 % ratio", "in the ratios", "No separate treatment"),
    ("Royal Army of Oman, Northern Frontier Regiment camp", "Military camp", "3.0 km from the STP", "296 ha", "no account in the file: self-metered",
     "Record only: no load carried; not expected to connect", "none", "Occupancy and drainage arrangement requested (data request 5)"),
    ("Ibri Regional Hospital", "Hospital", "town", "240 beds at opening", "6 CRT accounts (governmental)", "Governmental through the 14 % ratio", "in the ratios", "Bed count would allow the unit rate (data request 7)"),
    ("UTAS Ibri, College of Technology", "College", "two campuses", "-", "16 CRT accounts (governmental)", "Governmental through the 14 % ratio", "in the ratios", "Pupil count would allow the unit rate (data request 7)"),
    ("Ibri Police HQ", "Government campus", "Bu Khabi", "-", "17 CRT accounts (governmental)", "Governmental through the 14 % ratio", "in the ratios", "No separate treatment"),
    ("Hotels: Ayla Ibri, F&M Grand, Al Majd, Remal, Alnebras, Ibri Oasis", "Hotels", "town", "6 hotels, small", "Commercial tariff", "Non-domestic through the 22 % ratio", "in the ratios", "No separate treatment"),
    ("Ibri sewage treatment plant (existing)", "Treatment plant", "E444387 N2563352", "33.7 ha compound", "farm meters for its pumps", "Government site; the destination of the network, no load of its own", "none", "Records requested (data request 3)"),
    ("Ibri Landfill", "Landfill", "E449000 N2561200", "37.1 ha", "no account", "No sewage; leachate is not a network load", "none", "-"),
    ("Ibri View resort", "Planned development (OMRAN and the Governorate)", "As Sulayf, inside the boundary", "2,000,000 m² announced: hotels, shopping, housing", "not in the cadastre yet",
     "No load until the plan is issued", "none", "Development plan requested (data request 6)"),
    ("Ibri central slaughterhouse; Ibri market; youth centre and science centre", "Planned, not located", "-", "-", "-", "No load; the slaughterhouse would need pre-treatment (G203 p74)", "none", "Design or tender stage, per the press"),
    ("Madayn Ibri Industrial City", "Industrial city, outside the boundary", "8.6 km south-west of the boundary, 13 km from the STP", "10 km² gross, phase 1 3 km²", "outside the file",
     "No pipe; a candidate source of sewage by tanker to the STP", "tanker only", "Tanker records requested (data request 1)"),
    ("Ibri IPP and the solar plants' construction camp", "Power plants, outside the boundary", "7.5 to 11 km north-west of the boundary", "-", "outside the file",
     "No pipe; a candidate source of sewage by tanker to the STP", "tanker only", "Tanker records requested (data request 1)"),
]
KIND_STYLE = {"landuse=industrial": ("Industrial", "#9B59B6"), "landuse=military": ("Military", "#7F7F7F"), "man_made=wastewater_plant": ("Treatment plant", NAVY), "tourism=hotel": ("Hotel", "#F5A742")}


def projects(manifest):
    d = folder("05_identified_projects")
    # the estates' loads read from the plot layer, not typed
    pl = F.plots(); rows = list(PROJECTS)
    for i, est in ((0, "AL TAYYEB"), (1, "TANAM")):
        sub = pl[pl.ESTATE == est]
        r = list(rows[i]); r[6] = f"{sub.W_SPEC.sum():,.0f} m³/d water, {sub.S_SPEC.sum():,.0f} m³/d sewage ({sub.WORKERS.sum():,.0f} workers)"; rows[i] = tuple(r)
    g = gpd.read_file(os.path.join(W14, "shp", "Identified_projects_OSM.shp"))
    g["AREA_HA"] = (g.geometry.area / 1e4).round(1)
    g["KIND_EN"] = g.kind.map(lambda k: KIND_STYLE.get(k, (k, "#5A5A5A"))[0])
    for ext in ("shp", "shx", "dbf", "prj", "cpg"):
        src = os.path.join(W14, "shp", f"Identified_projects_OSM.{ext}")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(d, f"Identified_projects_footprints.{ext}"))
    xl = XL(os.path.join(d, "Identified_projects.xlsx"))
    xl.sheet("Register", "Identified projects and special consumption: every site found, how the basis treats it and what it carries",
             "Design Basis Report R0, Section 5.3; PAM-GUD-201 §7.3.1 (identified projects) and §7.3.4 (special consumption); W14/analysis/IDENTIFIED_PROJECTS.md. Footprints from OpenStreetMap where one exists.",
             ["Site", "Type", "Where", "Size", "Metered as", "Treatment in the basis", "Load", "Status"], [list(r) for r in rows],
             ["t", "t", "t", "t", "t", "t", "t", "t"], [44, 30, 30, 28, 34, 60, 22, 40], left_cols=tuple(range(8)))
    xl.sheet("Footprints", "The footprints held as a layer (OpenStreetMap)", "W14/shp/Identified_projects_OSM.shp; area measured in UTM zone 40 North.",
             ["OSM id", "Name", "Kind", "Area, ha"], [[str(r.osm_id), "" if pd.isna(r["name"]) else r["name"], r.KIND_EN, r.AREA_HA] for _, r in g.iterrows()],
             ["t", "t", "c", "d"], [14, 36, 18, 10], left_cols=(0, 1))
    xl.close()
    k = KML("Identified projects and special consumption")
    for kind, (label, col) in KIND_STYLE.items():
        k.style_poly("k" + label.replace(" ", ""), col, col, 2.0, alpha="80")
    k.style_label("lab", "#FFFFFF", 0.9)
    gw = wgs(g)
    for _, r in gw.iterrows():
        label, col = KIND_STYLE.get(r.kind, (r.kind, "#5A5A5A"))
        nm = r["name"] if isinstance(r["name"], str) else label
        k.placemark(nm, r.geometry, "k" + label.replace(" ", ""), [("Name", nm), ("Kind", label), ("Area, ha", r.AREA_HA), ("OSM id", r.osm_id)])
    k.open_folder("Names")
    for _, r in gw.iterrows():
        nm = r["name"] if isinstance(r["name"], str) else KIND_STYLE.get(r.kind, (r.kind, ""))[0]
        k.placemark(nm, r.geometry.representative_point(), "lab")
    k.close_folder()
    k.save(os.path.join(d, "Identified_projects_footprints.kmz"))
    manifest.append(("05_identified_projects", "Identified_projects.xlsx; Identified_projects_footprints.kmz, .shp",
                     "the register of identified projects and special consumption (the two estates, the army camp, the hospital, the college, the hotels, Ibri View, the tanker sources outside) with how each is treated; the footprints found in OpenStreetMap"))
    print("05 projects:", len(rows), "register rows,", len(g), "footprints")


# ------------------------------------------------------------------ package
def readme(manifest):
    t = F.totals()
    lines = [f"# Ibri Sewer, TE Networks and STP: the data behind the Design Basis Report, Revision 0",
             "", f"Renardet project 2621, for Nama Water Services. Packaged {datetime.date.today().isoformat()}.", "",
             "Every value is the one in the Design Basis Report R0: the settlement boundaries redrawn as a partition, the people, the use of each plot, "
             "the rates, the growth with the overflow, and the average sewage flow of every plot and settlement. Nothing here is re-derived; the report's "
             "decisions (Section 10) apply to all of it.", "",
             "| Folder | Files | What it is |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in manifest]
    lines += ["", "## Conventions", "",
              "- KMZ files are in WGS 84 for Google Earth; the balloon of every feature carries its table. Shapefiles are in UTM zone 40 North, WGS 84 (EPSG:32640).",
              "- Q is the average sewage flow in m³/d after the return ratios (85 % of domestic and tanker water, 54 % of the rest), without infiltration or the STP margin.",
              "- People by year follow the series with the overflow: a settlement grows at the series' rate until its land is full, then its further growth moves to its neighbours (Decision 4).",
              "- The plots carry the four stored years, 2024, 2030, 2055 and saturation; the settlements carry 2024, 2025 and every five years to 2070.",
              "- OR is the persons per property adopted for the settlement (Decision 2).",
              "- The peak flow of a settlement is its own average flow peaked: Merrimack (PAM-GUD-201 p71) where it has over 100 properties in that year, Peltier (p72) otherwise; "
              "add 720 l/d per km of sewer for infiltration. The study area's peak is Merrimack on the whole flow, not the sum of the settlements' peaks.",
              "- The use of a plot is the one determined from the meters and the satellite image (Decision 3); the eight classes are Residential, Residential-Commercial, Commercial, "
              "Government, Agricultural, Industrial, Heritage and Empty (unmetered).",
              "- The 126 meters more than 15 m from any plot carry no load (report Section 3.3).", "",
              f"Key figures: 2024 {t['pop_today']:,} people and {t['q_today']:,.0f} m³/d; 2055 {t['pop'][2055]:,} people and {t['q'][2055]:,.0f} m³/d; "
              f"saturation {t['ultimate']} {t['pop_ult']:,} people and {t['q_ult']:,.0f} m³/d."]
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def zip_package():
    zp = os.path.join(HERE, PKG + ".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, HERE))
    print("zip:", zp, round(os.path.getsize(zp) / 1e6, 1), "MB")


if __name__ == "__main__":
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    manifest = []
    names = {r["key"]: r["name"] for r in F.settlement_table()}
    boundaries(manifest)
    settlements(manifest)
    meters(manifest, names)
    plots(manifest, names)
    projects(manifest)
    readme(manifest)
    zip_package()
    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            print(f"  {os.path.relpath(os.path.join(root, f), OUT):60s} {os.path.getsize(os.path.join(root, f)) / 1e6:7.1f} MB")
