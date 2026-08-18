"""sewnet.export_dxf — annotated CAD deliverable (ezdxf, R2010). The donor repo's
label-stack + flow-tick annotation idea, re-branded for sanitary sewers."""

import math
import ezdxf

DN_COLOR = {200: 3, 250: 4, 315: 5, 400: 6, 500: 1, 600: 2, 700: 30, 800: 40, 900: 210}


def write(path, nodes, pipes, riders, pockets, of_rep):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for name, color in [("SEW-PIPE", 3), ("SEW-MH", 7), ("SEW-LABEL", 2), ("SEW-MH-LABEL", 8),
                        ("SEW-OUTFALL", 1), ("SEW-SLS", 1), ("SEW-RIDER", 8), ("SEW-DROP", 6)]:
        doc.layers.add(name, color=color)
    for dn, col in DN_COLOR.items():
        doc.layers.add(f"SEW-PIPE-DN{dn}", color=col)

    for p in pipes:
        layer = f"SEW-PIPE-DN{p['dn_mm']}" if p["dn_mm"] in DN_COLOR else "SEW-PIPE"
        msp.add_lwpolyline(list(p["geom"].coords), dxfattribs={"layer": layer})
        # mid-pipe annotation: DN + slope, rotated along the pipe; flow chevron
        mid = p["geom"].interpolate(0.5, normalized=True)
        a = p["geom"].interpolate(max(0.0, 0.5 * p["geom"].length - 2.0))
        b = p["geom"].interpolate(min(p["geom"].length, 0.5 * p["geom"].length + 2.0))
        ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        if p["length"] > 25:
            txt = f"DN{p['dn_mm']} {p['slope']*1000:.1f}‰"
            t = msp.add_text(txt, dxfattribs={"layer": "SEW-LABEL", "height": 1.8,
                                              "rotation": ang if -90 <= ang <= 90 else ang + 180})
            t.set_placement((mid.x, mid.y + 1.2), align=ezdxf.enums.TextEntityAlignment.CENTER)
        # chevron in flow direction
        ux, uy = (b.x - a.x), (b.y - a.y)
        L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        px, py = -uy, ux
        for s in (1.0, -1.0):
            msp.add_line((mid.x - 1.5 * ux + 1.2 * px * s, mid.y - 1.5 * uy + 1.2 * py * s),
                         (mid.x + 1.5 * ux, mid.y + 1.5 * uy), dxfattribs={"layer": "SEW-LABEL"})
        if p.get("drop_dn", 0.0) > 0.6:     # backdrop structure sits at the receiving MH
            d_node = nodes[p["dn"]]
            msp.add_circle((d_node["x"], d_node["y"]), 2.5, dxfattribs={"layer": "SEW-DROP"})

    for n in nodes.values():
        if n["kind"] == "outfall":
            msp.add_circle((n["x"], n["y"]), 3.0, dxfattribs={"layer": "SEW-OUTFALL"})
            msp.add_circle((n["x"], n["y"]), 4.5, dxfattribs={"layer": "SEW-OUTFALL"})
        else:
            msp.add_circle((n["x"], n["y"]), 1.2, dxfattribs={"layer": "SEW-MH"})
        if n.get("invert") is None:
            continue
        stack = [n["label"], f"G:{n['z']:.2f}", f"I:{n['invert']:.2f}", f"D:{n['depth']:.2f}"]
        for i, s in enumerate(stack):
            t = msp.add_text(s, dxfattribs={"layer": "SEW-MH-LABEL", "height": 1.2})
            t.set_placement((n["x"] + 2.0, n["y"] - 1.6 * i),
                            align=ezdxf.enums.TextEntityAlignment.LEFT)

    for r in riders:
        msp.add_lwpolyline(list(r["geom"].coords), dxfattribs={"layer": "SEW-RIDER"})

    for pk in pockets:
        s = nodes[pk["site"]]
        msp.add_circle((s["x"], s["y"]), 8.0, dxfattribs={"layer": "SEW-SLS"})
        t = msp.add_text(f"SLS candidate ({pk['n_props']} props)",
                         dxfattribs={"layer": "SEW-SLS", "height": 3.0})
        t.set_placement((s["x"] + 10, s["y"]), align=ezdxf.enums.TextEntityAlignment.LEFT)

    doc.saveas(path)
