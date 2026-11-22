"""A light KMZ of a scenario for Google Earth: pipes coloured by size with their data in the balloon, outfalls and wet
wells as pins, and the manholes in a folder that starts hidden (thousands of pins are slow to draw)."""
import io, zipfile
from xml.sax.saxutils import escape
import numpy as np
from sewerapp.api import coords

# size classes and colours (as the map's size legend), KML colours are aabbggrr
DN_CLASSES = [(250, "up to 250", "9ecae1"), (315, "280-315", "6baed6"), (400, "355-400", "4292c6"), (500, "450-500", "2171b5"),
              (630, "560-630", "6a51a3"), (800, "710-800", "8c2d8c"), (1000, "900-1000", "b0307a"), (1e9, "over 1000", "7a0e3a")]


def f2(v, d=2):
    try: return "-" if v is None or v != v else f"{float(v):.{d}f}"
    except (TypeError, ValueError): return "-"


def _kml_colour(hex6, alpha="ff"): return alpha + hex6[4:6] + hex6[2:4] + hex6[0:2]


def _cls(dn):
    for k, (upto, name, col) in enumerate(DN_CLASSES):
        if (dn or 0) <= upto: return k
    return len(DN_CLASSES) - 1


def kmz_bytes(p, results=None, name=None):
    if not p.crs: raise ValueError("a project in local metres has no place on the earth: give it a CRS first")
    n = p.nodes; lon, lat = coords.to_display(p.crs, n.x.values, n.y.values); ll = dict(zip(n.index, zip(lon, lat)))
    out = [f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{escape(name or p.name)}</name>']
    for k, (upto, cname, col) in enumerate(DN_CLASSES):
        out.append(f'<Style id="dn{k}"><LineStyle><color>{_kml_colour(col)}</color><width>{2 + k * 0.6:.1f}</width></LineStyle></Style>')
    out.append('<Style id="pump"><LineStyle><color>ffa03f7b</color><width>3</width></LineStyle></Style>')
    out.append('<Style id="mh"><IconStyle><scale>0.5</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle><LabelStyle><scale>0</scale></LabelStyle></Style>')
    out.append('<Style id="out"><IconStyle><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/blu-circle.png</href></Icon></IconStyle></Style>')
    out.append('<Style id="ww"><IconStyle><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/purple-square.png</href></Icon></IconStyle></Style>')
    folders = {k: [] for k in range(len(DN_CLASSES))}; pumps = []
    for i, r in zip(p.links.index, p.links.to_dict("records")):
        c = r.get("coords")
        if isinstance(c, list) and len(c) >= 2:
            a = np.array(c); x, y = coords.to_display(p.crs, a[:, 0], a[:, 1]); line = list(zip(x, y))
        else:
            line = [ll[r["from_node"]], ll[r["to_node"]]]
        res = results.loc[i] if results is not None and i in results.index else None
        desc = f"DN{r['dn_mm']} &#183; {f2(r['length_m'], 1)} m &#183; inverts {f2(r['up_inv'])} / {f2(r['dn_inv'])}" if r["kind"] != "pump" else "pump"
        if res is not None and "v_ms" in res and res.v_ms == res.v_ms: desc += f" &#183; {f2(res.q_ls)} L/s &#183; v {f2(res.v_ms)} m/s &#183; d/D {f2(res.d_over_D)}"
        pm = (f'<Placemark><name>{escape(str(i))}</name><description>{desc}</description><styleUrl>#{"pump" if r["kind"] == "pump" else "dn" + str(_cls(r["dn_mm"]))}</styleUrl>'
              f'<LineString><tessellate>1</tessellate><coordinates>{" ".join(f"{u:.7f},{v:.7f},0" for u, v in line)}</coordinates></LineString></Placemark>')
        (pumps if r["kind"] == "pump" else folders[_cls(r["dn_mm"])]).append(pm)
    out.append("<Folder><name>Pipes by size</name>")
    for k, pms in folders.items():
        if pms: out.append(f"<Folder><name>DN {DN_CLASSES[k][1]} ({len(pms)})</name>{''.join(pms)}</Folder>")
    out.append("</Folder>")
    if pumps: out.append(f"<Folder><name>Pumps ({len(pumps)})</name>{''.join(pumps)}</Folder>")
    pins = {"outfall": [], "wetwell": [], "manhole": []}
    for i, r in zip(n.index, n.to_dict("records")):
        if r["kind"] not in pins: continue
        ok = lambda v: v is not None and v == v
        dep = (r["ground"] - r["invert"]) if ok(r["ground"]) and ok(r["invert"]) else None
        desc = f"{r['kind']} &#183; ground {f2(r['ground'])} &#183; invert {f2(r['invert'])}" + (f" &#183; depth {f2(dep)} m" if dep is not None else "")
        st = {"outfall": "out", "wetwell": "ww", "manhole": "mh"}[r["kind"]]
        pins[r["kind"]].append(f'<Placemark><name>{escape(str(i))}</name><description>{desc}</description><styleUrl>#{st}</styleUrl><Point><coordinates>{ll[i][0]:.7f},{ll[i][1]:.7f},0</coordinates></Point></Placemark>')
    for kind, title, vis in (("outfall", "Outfalls", 1), ("wetwell", "Wet wells", 1), ("manhole", "Manholes (switch on to see)", 0)):
        if pins[kind]: out.append(f"<Folder><name>{title} ({len(pins[kind])})</name><visibility>{vis}</visibility>{''.join(pins[kind]).replace('<Placemark>', f'<Placemark><visibility>{vis}</visibility>' if not vis else '<Placemark>')}</Folder>")
    out.append("</Document></kml>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("doc.kml", "".join(out))
    return buf.getvalue()
