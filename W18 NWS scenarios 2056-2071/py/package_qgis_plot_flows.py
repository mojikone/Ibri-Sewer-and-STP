"""Package the QGIS project of the plot flows with its layers in one zip (engineer, 2026-11-17), so it opens anywhere:
gis/W18_plot_flows_QGIS.zip -> W18_plot_flows/W18_plot_flows.qgz + layers/ (plot layer 2026-2100, settlement
boundaries) + the field list. The project's layer paths are rewritten to ./layers/; the satellite basemap is a web
layer and needs no file. Run after py/qgis_plot_flows_project.py."""
import os, io, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
QGZ = os.path.join(W18, "qgis", "W18_plot_flows.qgz")
OUT = os.path.join(W18, "gis", "W18_plot_flows_QGIS.zip")
TOP = "W18_plot_flows/"
LAYERS = {"../gis/W18_plots_2026_2100.shp": os.path.join(W18, "gis", "W18_plots_2026_2100"),
          "../../W14/shp/Settlements_merged.shp": os.path.join(W18, "..", "W14", "shp", "Settlements_merged")}

src = zipfile.ZipFile(QGZ)
qgs_name = next(n for n in src.namelist() if n.endswith(".qgs"))
qgs = src.read(qgs_name).decode("utf-8")
for old, base in LAYERS.items():
    n = qgs.count(old); assert n, old
    qgs = qgs.replace(old, "./layers/" + os.path.basename(base) + ".shp")
for old in LAYERS: assert old not in qgs
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
    z.writestr(TOP + "README.txt",
               "Open W18_plot_flows.qgz in QGIS 3.x (layers load from ./layers).\n"
               "Plots filled by average flow (m3/d per plot) in a blue gradient, darker = more; one year at a time (2031, 2056, 2071, 2100).\n"
               "Plots with no flow are empty. Existing plots outlined by land use; proposed plots outlined light grey.\n"
               "Fields of the plot layer: W18_plots_2026_2100_fields.md. Basemap: Google satellite hybrid (web, needs internet).\n")
print(OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB")
for i in zipfile.ZipFile(OUT).infolist(): print(f"  {i.filename}  {i.file_size / 1e6:.2f} MB")
