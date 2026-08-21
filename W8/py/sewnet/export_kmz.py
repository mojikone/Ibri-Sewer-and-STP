# -*- coding: utf-8 -*-
"""sewnet.export_kmz — the design as a KMZ you can open in Google Earth.

Asked for on 20 August 2026 so the design can be checked outside GIS. Same look as the
QGIS styling, so the two do not tell different stories:

  * every subnetwork gets its own colour, spaced by the golden angle so two neighbours
    never come out looking alike;
  * the line gets thicker with the pipe size, so the mains stand out from the branches;
  * the main pipe is black and heavier still, because everything drains into it.

Google Earth wants longitude and latitude, so the coordinates are converted out of UTM 40N
on the way. Colours in KML are aabbggrr, NOT rrggbb — easy to get backwards.
"""

import colorsys
import os
import zipfile

from pyproj import Transformer

TO_WGS = Transformer.from_crs(32640, 4326, always_xy=True)


def _hue(i):
    """A colour per subnetwork, far from its neighbours'."""
    h = (i * 0.61803398875) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.62 + 0.18 * ((i % 3) / 2.0), 0.95 - 0.25 * (i % 2))
    return int(r * 255), int(g * 255), int(b * 255)


def _abgr(rgb, alpha="ff"):
    r, g, b = rgb
    return f"{alpha}{b:02x}{g:02x}{r:02x}"


def _width(dn_mm):
    """Thicker for bigger pipes, on the same scale the QGIS styling uses."""
    lo, hi = 200.0, 500.0
    t = max(0.0, min(1.0, (float(dn_mm) - lo) / (hi - lo)))
    return round(1.2 + t * 4.8, 2)


def _coords(geom):
    out = []
    for x, y in geom.coords:
        lon, lat = TO_WGS.transform(x, y)
        out.append(f"{lon:.8f},{lat:.8f},0")
    return " ".join(out)


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def write(path, net, catchments=None, of_rep=None):
    """Write the sewer network to `path` (.kmz). Returns a short report."""
    props = {c["cid"]: c for c in (catchments or [])}
    subs = sorted({r.subnet for r in net.reaches if r.subnet})
    order = {s: i for i, s in enumerate(subs)}

    styles, folders = [], []
    widths = sorted({r.dn_mm for r in net.reaches})

    # one style per subnetwork per pipe size, so colour AND thickness both carry meaning
    for s in subs:
        rgb = _hue(order[s])
        for dn in widths:
            styles.append(
                f'<Style id="s{s}_{dn}"><LineStyle>'
                f'<color>{_abgr(rgb)}</color><width>{_width(dn)}</width>'
                f'</LineStyle></Style>')
    for dn in widths:
        styles.append(f'<Style id="trunk_{dn}"><LineStyle>'
                      f'<color>ff000000</color><width>{_width(dn) + 2.0}</width>'
                      f'</LineStyle></Style>')

    by_sub = {}
    trunk = []
    for r in net.reaches:
        (trunk if r.on_trunk else by_sub.setdefault(r.subnet, [])).append(r)

    def placemark(r, style):
        cat = props.get(r.subnet)
        rows = [("Pipe", r.label), ("Size", f"DN{r.dn_mm}"),
                ("Length", f"{r.length:.1f} m"),
                ("Gradient", f"{r.slope*1000:.2f} mm/m"),
                ("Invert up / down", f"{r.inv_up:.2f} / {r.inv_dn:.2f} m"
                 if r.inv_up is not None else "-"),
                ("Peak flow", f"{r.qpeak_ls:.2f} L/s"),
                ("Properties upstream", f"{r.n_props:.0f}"),
                ("Subnetwork", "main pipe" if r.on_trunk else f"S{r.subnet}")]
        if cat:
            rows.append(("Subnetwork serves", f"{cat['n_props']:.0f} properties"))
        html = "".join(f"<tr><td><b>{_esc(k)}</b></td><td>{_esc(v)}</td></tr>"
                       for k, v in rows)
        return (f'<Placemark><name>{_esc(r.label)}</name>'
                f'<description><![CDATA[<table>{html}</table>]]></description>'
                f'<styleUrl>#{style}</styleUrl>'
                f'<LineString><tessellate>1</tessellate>'
                f'<coordinates>{_coords(r.geom)}</coordinates></LineString></Placemark>')

    if trunk:
        body = "".join(placemark(r, f"trunk_{r.dn_mm}") for r in trunk)
        folders.append(f'<Folder><name>MAIN PIPE — everything drains here '
                       f'({sum(r.length for r in trunk)/1000:.2f} km)</name>'
                       f'<open>1</open>{body}</Folder>')
    for s in subs:
        rs = by_sub.get(s, [])
        if not rs:
            continue
        cat = props.get(s)
        served = f" — {cat['n_props']:.0f} properties" if cat else ""
        body = "".join(placemark(r, f"s{s}_{r.dn_mm}") for r in rs)
        folders.append(f'<Folder><name>Subnetwork S{s}{served} '
                       f'({sum(r.length for r in rs)/1000:.2f} km)</name>'
                       f'<visibility>1</visibility>{body}</Folder>')

    if of_rep:
        lon, lat = TO_WGS.transform(of_rep["x"], of_rep["y"])
        folders.append(
            '<Style id="of"><IconStyle><scale>1.3</scale><Icon><href>'
            'http://maps.google.com/mapfiles/kml/paddle/blu-stars.png</href></Icon>'
            '</IconStyle></Style>'
            f'<Placemark><name>Outfall</name><styleUrl>#of</styleUrl>'
            f'<Point><coordinates>{lon:.8f},{lat:.8f},0</coordinates></Point></Placemark>')

    kml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>Ibri 2621 — W8 sewer design</name>'
           + "".join(styles) + "".join(folders) +
           '</Document></kml>')

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("doc.kml", kml)
    return {"file": os.path.basename(path), "subnetworks": len(subs),
            "pipes": len(net.reaches), "sizes": [int(d) for d in widths],
            "kb": round(os.path.getsize(path) / 1024)}
