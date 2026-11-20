"""The design drawings of the four final scenarios as AutoCAD files (engineer, 2026-11-19: the client asks for DWG with
every scenario, subnetwork and label; pumps and lifts legible from a zoomed-out view; zoomed in, every manhole and pipe
carries its data; pumps their flow, head, rising main and velocity; each plant its capacity, inlet depth and inlet pump).

One drawing per scenario, designed for 2056, model space in UTM zone 40N metres (EPSG:32640), so it overlays any survey
or GIS layer of the Project. Text heights are in metres on the ground, in three tiers so each is read at its own zoom:
plants 40 m and pumping/lift stations 25 m (read at 1:50,000), rising mains 6 m (1:10,000), pipes and manholes 1.0 m
(1:500 to 1:1,000).

Layers (colour and line weight by layer, so the client can switch, recolour or freeze any family):
  SEW-GRAV-DN200 / -DN250-355 / -DN400-630 / -DN710-1000 / -DN1200+   gravity sewers, weight 0.25 to 1.00 mm by size
  SEW-MH            manholes (circle 1.2 m)          SEW-MH-DEEP   manholes deeper than 12 m to invert
  SEW-MH-DROP       manholes with a drop over 0.5 m (ring 2.4 m)
  SEW-RM-PUMP / SEW-RM-LIFT   rising mains of the pumping and lift stations (dashed)
  SEW-PS / SEW-LS / SEW-STP   station and plant symbols
  TXT-STP, TXT-PS, TXT-RM, TXT-PIPE, TXT-MH   the annotation of each family, separately switchable
  BND-PROJECT, BND-SETTLEMENT, SHEET-LEGEND
Pipe text (above the pipe, along it): name, DN, length, gradient, design peak flow, velocity at the design peak;
below it: invert levels at the two ends. Manhole text: name, ground level, invert level, depth to invert, and the drop
when an incoming sewer arrives more than 0.5 m above the outgoing invert (a drop manhole; the smaller steps of crown
matching at a change of size are read from the pipe inverts).

Writes report_final/deliverables/dwg/Ibri_Sewer_<SC>_2056.dxf and, through AutoCAD's console (no window), .dwg.
    python final_dwg.py [SC1 SC2 ...]"""
import json, math, os, subprocess, sys
import ezdxf
import geopandas as gpd, pandas as pd
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); OUT = os.path.join(W18, "report_final", "deliverables", "dwg")
BND = os.path.join(W18, "..", "W17", "Options 2026-10", "01_Boundaries", "Project_boundary_updated.shp")
STL = os.path.join(W18, "gis", "W18_settlements_2026_2100.shp")
FIN = json.load(open(os.path.join(R, "financial.json")))
ACC = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
SCEN = {"SC1": "Treatment at STP-1 only", "SC2": "Treatment at STP-2 only", "SC3": "Treatment at STP-1 and STP-5", "SC4": "Treatment at STP-2 and STP-5"}
BANDS = [("SEW-GRAV-DN200", 0, 200, (91, 155, 213), 25), ("SEW-GRAV-DN250-355", 201, 355, (46, 117, 182), 35),
         ("SEW-GRAV-DN400-630", 356, 630, (31, 78, 121), 50), ("SEW-GRAV-DN710-1000", 631, 1000, (112, 48, 160), 70),
         ("SEW-GRAV-DN1200+", 1001, 9999, (192, 0, 0), 100)]
LAYERS = {"SEW-MH": ((89, 89, 89), 18), "SEW-MH-DEEP": ((215, 48, 31), 35), "SEW-MH-DROP": ((217, 115, 13), 35),
          "SEW-RM-PUMP": ((215, 48, 31), 50), "SEW-RM-LIFT": ((46, 117, 182), 35), "SEW-PS": ((215, 48, 31), 50),
          "SEW-LS": ((46, 117, 182), 50), "SEW-STP": ((27, 42, 74), 70), "TXT-STP": ((27, 42, 74), 35),
          "TXT-PS": ((215, 48, 31), 35), "TXT-RM": ((166, 27, 27), 18), "TXT-PIPE": ((38, 38, 38), 13),
          "TXT-MH": ((89, 89, 89), 13), "BND-PROJECT": ((0, 0, 0), 70), "BND-SETTLEMENT": ((150, 150, 150), 18),
          "SHEET-LEGEND": ((0, 0, 0), 25)}
H_STP, H_PS, H_PS2, H_RM, H_PIPE, H_MH = 40.0, 25.0, 8.0, 6.0, 1.0, 1.0


def band(dn):
    return next(b for b in BANDS if b[1] <= dn <= b[2])


def readable(a):
    """Angle in degrees of text along a line, turned so that it never reads upside down."""
    a = math.degrees(a) % 360
    return a - 180 if 90 < a <= 270 else a


def build(sc):
    case = os.path.join(R, f"{sc}-2056"); g = os.path.join(case, "products", "map.gpkg")
    P = gpd.read_file(g, layer="pipes"); M = gpd.read_file(g, layer="manholes"); S = gpd.read_file(g, layer="stations")
    FM = gpd.read_file(g, layer="force_mains"); q = json.load(open(os.path.join(case, "products", "quantities.json")))
    C = pd.read_csv(os.path.join(case, "exports", f"conduits_{sc}-2056a.csv"))[["label", "flow_m3d"]].rename(columns={"label": "old"})
    P = P.merge(C, on="old", how="left")
    gl = M.set_index("label").ground
    P["il_up"] = P.from_mh.map(gl) - P.depth_up_m; P["il_dn"] = P.to_mh.map(gl) - P.depth_dn_m
    fall = P.length_m * P.s_new_pc / 100                          # the last pipe into a station ends at its wet well, not a manhole
    P["il_dn"] = P.il_dn.fillna(P.il_up - fall); P["il_up"] = P.il_up.fillna(P.il_dn + fall)
    M = M.set_index("label"); M["il"] = M.ground - M.depth_m
    # drops: an incoming sewer whose invert at the manhole sits above the outgoing invert
    out_il = P.set_index("from_mh").il_up
    inc = P[P.to_mh.isin(out_il.index)].copy(); inc["drop"] = inc.il_dn - inc.to_mh.map(out_il)
    drop = inc[inc["drop"] > 0.5].groupby("to_mh")["drop"].max()   # drop manholes; smaller steps (crown matching) read from the pipe inverts

    doc = ezdxf.new("R2018", setup=True); doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6; doc.header["$LWDISPLAY"] = 1
    doc.styles.add("ARIAL", font="arial.ttf")
    for name, _, _, rgb, lw in BANDS: lay = doc.layers.add(name); lay.rgb = rgb; lay.lineweight = lw
    for name, (rgb, lw) in LAYERS.items(): lay = doc.layers.add(name); lay.rgb = rgb; lay.lineweight = lw
    doc.layers.get("SEW-RM-PUMP").dxf.linetype = "DASHED"; doc.layers.get("SEW-RM-LIFT").dxf.linetype = "DASHED2"
    doc.header["$LTSCALE"] = 20.0
    msp = doc.modelspace()
    T = lambda s, p, h, lay, rot=0.0, al=TextEntityAlignment.MIDDLE_CENTER: msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": lay, "style": "ARIAL"}).set_placement(p, align=al)

    for gdf, lay in ((gpd.read_file(BND).to_crs(32640), "BND-PROJECT"), (gpd.read_file(STL).to_crs(32640), "BND-SETTLEMENT")):
        for geom in gdf.geometry:
            for poly in getattr(geom, "geoms", [geom]):
                rings = [poly.exterior] + list(poly.interiors) if poly.geom_type == "Polygon" else [poly]
                for ring in rings: msp.add_lwpolyline(list(ring.coords), close=True, dxfattribs={"layer": lay})
    # gravity sewers and their annotation
    for r in P.itertuples():
        xy = list(r.geometry.coords); lay = band(int(r.od_mm))[0]
        msp.add_lwpolyline(xy, dxfattribs={"layer": lay})
        (x0, y0), (x1, y1) = xy[0], xy[-1]; a = math.atan2(y1 - y0, x1 - x0); rot = readable(a)
        mx, my = r.geometry.interpolate(0.5, normalized=True).coords[0]; nx, ny = -math.sin(math.radians(rot)), math.cos(math.radians(rot))
        qtxt = f"{r.flow_m3d / 86.4:.1f} L/s" if pd.notna(r.flow_m3d) else "-"
        T(f"{r.label}  DN{int(r.od_mm)}  L={r.length_m:.1f} m  S={r.s_new_pc:.2f}%  Q={qtxt}  V={r.v2056_ms:.2f} m/s",
          (mx + nx * 1.3 * H_PIPE, my + ny * 1.3 * H_PIPE), H_PIPE, "TXT-PIPE", rot)
        T(f"IL {r.il_up:.2f} > {r.il_dn:.2f}", (mx - nx * 1.3 * H_PIPE, my - ny * 1.3 * H_PIPE), H_PIPE * 0.85, "TXT-PIPE", rot)
    # manholes
    for lab, r in M.iterrows():
        x, y = r.geometry.x, r.geometry.y; deep = r.depth_m > 12
        msp.add_circle((x, y), 0.6, dxfattribs={"layer": "SEW-MH-DEEP" if deep else "SEW-MH"})
        lines = [lab, f"GL {r.ground:.2f}", f"IL {r.il:.2f}", f"D {r.depth_m:.2f} m"]
        if lab in drop.index:
            msp.add_circle((x, y), 1.2, dxfattribs={"layer": "SEW-MH-DROP"}); lines.append(f"DROP {drop[lab]:.2f} m")
        mt = msp.add_mtext("\\P".join(lines), dxfattribs={"layer": "TXT-MH", "style": "ARIAL", "char_height": H_MH})
        mt.set_location((x + 1.5, y - 1.5), attachment_point=1)
    # rising mains
    st = S.set_index("name")
    for r in FM.itertuples():
        lay = "SEW-RM-LIFT" if r.kind == "lift" else "SEW-RM-PUMP"; xy = list(r.geometry.coords)
        msp.add_lwpolyline(xy, dxfattribs={"layer": lay})
        s = st.loc[r.station]; mx, my = r.geometry.interpolate(0.5, normalized=True).coords[0]
        (x0, y0), (x1, y1) = xy[0], xy[-1]; rot = readable(math.atan2(y1 - y0, x1 - x0))
        nx, ny = -math.sin(math.radians(rot)), math.cos(math.radians(rot))
        T(f"Rising main {r.station}: DN{int(s.force_main_dn)}, L={r.length_m:,.0f} m, V={s.fm_velocity_ms:.2f} m/s",
          (mx + nx * 1.2 * H_RM, my + ny * 1.2 * H_RM), H_RM, "TXT-RM", rot)
    # pumping and lift stations
    for name, s in st.iterrows():
        x, y = s.geometry.x, s.geometry.y; lift = s.kind == "lift"
        if s.kind == "plant inlet": continue
        lay = "SEW-LS" if lift else "SEW-PS"
        if lift: msp.add_lwpolyline([(x, y + 9), (x - 8, y - 5), (x + 8, y - 5)], close=True, dxfattribs={"layer": lay})
        else: msp.add_circle((x, y), 8, dxfattribs={"layer": lay}); msp.add_circle((x, y), 4, dxfattribs={"layer": lay})
        T(name, (x + 14, y + 6), H_PS, "TXT-PS", 0, TextEntityAlignment.BOTTOM_LEFT)
        info = [f"{'Lift' if lift else 'Pumping'} station, G203 type {int(s.g203_type)}",
                f"Duty {s.duty_ls:,.1f} L/s, head {s.head_m:.1f} m, {s.kw:.1f} kW",
                f"Rising main DN{int(s.force_main_dn)}, {s.force_main_m:,.0f} m, {s.fm_velocity_ms:.2f} m/s",
                f"Incoming sewer {s.outfall_depth_m:.1f} m, wet well {s.wet_well_depth_m:.1f} m deep, live {s.wet_well_live_m3:.1f} m3"]
        mt = msp.add_mtext("\\P".join(info), dxfattribs={"layer": "TXT-PS", "style": "ARIAL", "char_height": H_PS2})
        mt.set_location((x + 14, y + 2), attachment_point=1)
    # plants with their inlet pumping station
    for inl, v in q["plants"].items():
        s = st.loc[inl]; x, y = s.geometry.x, s.geometry.y; p = FIN[sc]["plants"][v["stp"]]
        msp.add_lwpolyline([(x - 60, y - 60), (x + 60, y - 60), (x + 60, y + 60), (x - 60, y + 60)], close=True, dxfattribs={"layer": "SEW-STP"})
        msp.add_circle((x, y), 8, dxfattribs={"layer": "SEW-PS"})
        T(v["stp"], (x + 70, y + 30), H_STP, "TXT-STP", 0, TextEntityAlignment.BOTTOM_LEFT)
        info = [f"Capacity {p['n']} x {p['size']:,} m3/d = {p['total']:,} m3/d (2056 inflow + 10 %: {p['design']:,.0f} m3/d)",
                f"Average inflow 2031 / 2056: {p['q']['2031']:,} / {p['q']['2056']:,} m3/d",
                f"Incoming sewer {v['inlet_depth_m']:.1f} m deep",
                f"Inlet pumping station {inl}: {s.duty_ls:,.0f} L/s, head {s.head_m:.1f} m, {s.kw:.0f} kW",
                f"Inlet wet well {s.wet_well_depth_m:.1f} m deep, live volume {s.wet_well_live_m3:.1f} m3"]
        mt = msp.add_mtext("\\P".join(info), dxfattribs={"layer": "TXT-STP", "style": "ARIAL", "char_height": 12})
        mt.set_location((x + 70, y + 24), attachment_point=1)
    # legend and title, below the lower-left corner of the Project boundary
    b = gpd.read_file(BND).to_crs(32640).total_bounds; lx, ly = b[0], b[1] - 400
    T(f"IBRI SEWERAGE - CONCEPT DESIGN - SCENARIO {sc}: {SCEN[sc].upper()} - DESIGN YEAR 2056", (lx, ly), 60, "SHEET-LEGEND", 0, TextEntityAlignment.BOTTOM_LEFT)
    T("Coordinates UTM zone 40N (WGS 84), metres; levels in metres; flows are the 2056 design peaks", (lx, ly - 90), 25, "SHEET-LEGEND", 0, TextEntityAlignment.BOTTOM_LEFT)
    rows = [(n, f"Gravity sewer {n.split('-DN')[1].replace('-', ' to ')} mm" if "DN" in n else n) for n, *_ in BANDS] + [
        ("SEW-RM-PUMP", "Rising main of a pumping station"), ("SEW-RM-LIFT", "Rising main of a lift station"),
        ("SEW-MH-DEEP", "Manhole deeper than 12 m to invert"), ("SEW-MH-DROP", "Manhole with a drop over 0.5 m")]
    for i, (lay, text) in enumerate(rows):
        yy = ly - 180 - i * 50
        msp.add_line((lx, yy), (lx + 160, yy), dxfattribs={"layer": lay}); T(text, (lx + 200, yy), 22, "SHEET-LEGEND", 0, TextEntityAlignment.MIDDLE_LEFT)
    yy = ly - 180 - len(rows) * 50
    msp.add_circle((lx + 80, yy), 8, dxfattribs={"layer": "SEW-PS"}); T("Pumping station (name, duty, head, rising main, wet well)", (lx + 200, yy), 22, "SHEET-LEGEND", 0, TextEntityAlignment.MIDDLE_LEFT)
    yy -= 50; msp.add_lwpolyline([(lx + 80, yy + 9), (lx + 72, yy - 5), (lx + 88, yy - 5)], close=True, dxfattribs={"layer": "SEW-LS"})
    T("Lift station", (lx + 200, yy), 22, "SHEET-LEGEND", 0, TextEntityAlignment.MIDDLE_LEFT)
    yy -= 50; T("Pipe: name DN length gradient design-peak flow velocity / invert levels upstream > downstream", (lx, yy), 22, "SHEET-LEGEND", 0, TextEntityAlignment.MIDDLE_LEFT)
    yy -= 40; T("Manhole: name / ground level / invert level / depth to invert / drop", (lx, yy), 22, "SHEET-LEGEND", 0, TextEntityAlignment.MIDDLE_LEFT)
    os.makedirs(OUT, exist_ok=True); dxf = os.path.join(OUT, f"Ibri_Sewer_{sc}_2056.dxf"); doc.saveas(dxf)
    print(f"{sc}: {len(P):,} pipes, {len(M):,} manholes, {len(drop):,} drops, {len(st)} stations -> {dxf}")
    return dxf


def to_dwg(dxf):
    """Open the DXF in AutoCAD's console (no window) and save it as a 2018 DWG next to it, zoomed to the extents."""
    dwg = dxf[:-4] + ".dwg"; scr = dxf[:-4] + ".scr"
    if os.path.exists(dwg): os.remove(dwg)
    open(scr, "w").write(f'_.ZOOM _E\n_.SAVEAS 2018 "{dwg}"\n_.QUIT _Y\n')
    subprocess.run([ACC, "/i", dxf, "/s", scr, "/l", "en-US"], capture_output=True, timeout=1800)
    os.remove(scr)
    print("  dwg:", dwg if os.path.exists(dwg) else "NOT WRITTEN")
    return os.path.exists(dwg)


if __name__ == "__main__":
    for sc in (sys.argv[1:] or ["SC1", "SC2", "SC3", "SC4"]): to_dwg(build(sc))
