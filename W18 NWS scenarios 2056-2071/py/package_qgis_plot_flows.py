"""Package the QGIS project of the plot flows with its layers in one zip (engineer, 2026-11-17), so it opens anywhere:
gis/W18_plot_flows_QGIS.zip -> W18_plot_flows/W18_plot_flows.qgz + layers/ (plot layer 2026-2100, settlement
boundaries) + the field list. The project's layer paths are rewritten to ./layers/; the satellite basemap is a web
layer and needs no file. Run after py/qgis_plot_flows_project.py."""
import os, io, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
QGZ = os.path.join(W18, "qgis", "W18_plot_flows.qgz")
OUT = os.path.join(W18, "gis", "W18_plot_flows_QGIS.zip")
XLSX = os.path.join(W18, "results", "W18_MOHUP_DATA_NA_growth_plots.xlsx")   # py/mohup_sheet_growth_plots.py
TOP = "W18_plot_flows/"
LAYERS = {"../gis/W18_plots_2026_2100.shp": os.path.join(W18, "gis", "W18_plots_2026_2100"),
          "../gis/W18_settlements_2026_2100.shp": os.path.join(W18, "gis", "W18_settlements_2026_2100")}

SC1 = os.path.join(W18, "results", "sc1_conditions")    # py/split_deep_subnetworks.py + py/qgis_sc1_conditions.py (2026-11-18)
SC1_REL = "../results/sc1_conditions/"

src = zipfile.ZipFile(QGZ)
qgs_name = next(n for n in src.namelist() if n.endswith(".qgs"))
qgs = src.read(qgs_name).decode("utf-8")
for old, base in LAYERS.items():
    n = qgs.count(old); assert n, old
    qgs = qgs.replace(old, "./layers/" + os.path.basename(base) + ".shp")
for old in LAYERS: assert old not in qgs
has_sc1 = SC1_REL in qgs                             # the SC1 condition maps, if the project carries them
qgs = qgs.replace(SC1_REL, "./layers/sc1_conditions/")
assert "../" not in qgs, "a layer path still points outside the package"
buf = io.BytesIO()                                   # the repackaged .qgz: same members, new layer paths
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as q:
    for n in src.namelist():
        q.writestr(n, qgs.encode("utf-8") if n == qgs_name else src.read(n))

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.writestr(TOP + "W18_plot_flows.qgz", buf.getvalue())
    for base in LAYERS.values():
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            f = base + ext
            if os.path.exists(f): z.write(f, TOP + "layers/" + os.path.basename(f))
    z.write(os.path.join(W18, "gis", "W18_plots_2026_2100_fields.md"), TOP + "W18_plots_2026_2100_fields.md")
    z.write(os.path.join(W18, "gis", "W18_settlements_2026_2100_fields.md"), TOP + "W18_settlements_2026_2100_fields.md")
    z.write(XLSX, TOP + os.path.basename(XLSX))          # the team's capacity sheet with our growth plots
    sc1_text = ""
    if has_sc1:
        for d in sorted(os.listdir(SC1)):
            g = os.path.join(SC1, d, "split_SC1-2056.gpkg")
            if os.path.exists(g):
                z.write(g, TOP + f"layers/sc1_conditions/{d}/split_SC1-2056.gpkg")
                z.write(os.path.join(SC1, d, "SUMMARY.md"), TOP + f"sc1_conditions/{d}_SUMMARY.md")
        for f in sorted(os.listdir(os.path.join(SC1, "maps"))):
            if f.endswith(".png"): z.write(os.path.join(SC1, "maps", f), TOP + "sc1_conditions/maps/" + f)
        sc1_text = ("Group 'SC1 sewer conditions': SC1 (design year 2056) re-laid from the SewerGEMS design, one condition at a time;\n"
                    "a saved print layout for each (Project > Layouts: SC1 C0 ... C3), exported in sc1_conditions/maps/.\n"
                    "C0 as designed: pipes by velocity at the 2031 peak. C1-C3: pipes above DN200 steepened to reach 0.75 m/s at the\n"
                    "2031 peak with gradients up to 0.50 / 0.75 / 1.00 %, one gradient per street run, and the subnetworks split where they\n"
                    "stay deeper than 12 m (new stations, gravity joins). Every map: pipes over 3.0 m/s at the 2056 peak, outfalls with\n"
                    "name and depth. Each condition's numbers: sc1_conditions/<condition>_SUMMARY.md.\n")
    z.writestr(TOP + "README.txt",
               "Open W18_plot_flows.qgz in QGIS 3.x (layers load from ./layers).\n"
               "Plots filled by average flow (m3/d per plot) in a blue gradient, darker = more; one year at a time (2031, 2056, 2071, 2100).\n"
               "Plots with no flow are empty. Existing plots outlined by land use; proposed plots outlined light grey.\n"
               "Fields: W18_plots_2026_2100_fields.md and W18_settlements_2026_2100_fields.md. Basemap: Google satellite hybrid (web, needs internet).\n"
               "W18_MOHUP_DATA_NA_growth_plots.xlsx: the team's sheet 'MOHUP DATA - NA' with the growth plots of the plot layer in column C.\n"
               + sc1_text)
print(OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB")
for i in zipfile.ZipFile(OUT).infolist(): print(f"  {i.filename}  {i.file_size / 1e6:.2f} MB")
