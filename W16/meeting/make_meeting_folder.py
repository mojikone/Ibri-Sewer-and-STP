"""Fill W16/Meeting 2026-09-16 with the latest useful data, reports and tables, then build
its QGIS project. The record of how the folder of 15 September 2026 was made; re-runnable.

    python make_meeting_folder.py            copies, raster clips, the style export, then the project

Needs: QGIS 3.44 open with stp2.qgz (the styles are exported from the running project through
the plugin's socket, W16/report_basis/qgis_direct.py), the QGIS bin on disk for gdalwarp and
the standalone python, and the 2331 flood-hazard file server reachable. The folder is not in
git (rasters and the client's own data); this script and make_meeting_project.py are.
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W16 = os.path.dirname(HERE)
REPO = os.path.dirname(W16)
HYD = os.path.dirname(REPO)
DATA = os.path.join(os.path.dirname(HYD), "Data")
M = os.path.join(W16, "Meeting 2026-09-16")
QGIS_BIN = r"C:\Program Files\QGIS 3.44.8\bin"
HAZARD = (r"\\fileserver-\Works\2331 Flood Hazard Maps for Muscat-Dhofar-Musandam_MWR\06-WORKING\04-Hydraulic\05-Hazard_Risk"
          r"\FloodHazard_OM_20260608\Project2\2.3-Area3\04 Lekhuwair")
PKG = os.path.join(W16, "deliverables", "Ibri_Design_Basis_Data_R0")
GDAL_ENV = {**os.environ, "PROJ_LIB": os.path.join(os.path.dirname(QGIS_BIN), "share", "proj"), "GDAL_DATA": os.path.join(os.path.dirname(QGIS_BIN), "share", "gdal")}
SHP_EXT = ("shp", "shx", "dbf", "prj", "cpg")

# the layers whose stp2 style is exported (the QML name is the layer name made safe)
STYLE_LAYERS = ['Use of the plot', 'Average sewage flow of the plot at saturation', 'Capacity taken by overflow', 'Overflow, people',
                'Identified site', 'Identified project', 'Meter more than 15 m from any plot', 'Settlement boundary, redrawn as a partition',
                'Average sewage flow at saturation (2070), m\u00b3/d', 'Settlement boundary as received (Inception Report)', 'Settlement boundary',
                'Cadastral plot', 'Project Boundary updated', 'Hazard_T50y', 'Hazard_T500y', 'GHS POP 2025 IBRI', 'IBRI_0p5_clip', 'Road_Centercline',
                'Streams NSA 2m project boundary', 'Main Pipe', 'IBRI STP', 'W15 pipes', 'W15 outlets', 'W15 catchments by group', 'Towns', 'Upstream Catchments',
                'Existing gravity sewer', 'Existing force mains', 'Existing treated effluent main', 'Existing pumping station', 'STP location', 'STP structures',
                'Al Raybah 110 mm', 'Al Raybah 180 mm', 'Al Raybah 225 mm', 'PAEW water mains', 'PAEW water laterals', 'PAEW water services',
                'PAEW system valves', 'PAEW hydrants', 'PAEW facilities', 'PAEW facility boundaries', 'Sub Main Pipe guide', 'Google Satellite',
                'Identified projects, OSM footprints (W13)', 'Landuse']

EXPORT_CODE = r'''
import os, re
from qgis.core import QgsProject, QgsVectorFileWriter, QgsCoordinateTransformContext
OUT = r"%OUT%"; proj = QgsProject.instance(); root = proj.layerTreeRoot()
def safe(n): return re.sub(r"[^A-Za-z0-9]+", "_", n).strip("_")
for name in %NAMES%:
    lays = proj.mapLayersByName(name)
    if not lays: print("MISSING", name); continue
    pick = next((l for l in lays if root.findLayer(l.id()) is not None and root.findLayer(l.id()).isVisible()), None) \
        or next((l for l in lays if root.findLayer(l.id()) is not None), lays[0])
    pick.saveNamedStyle(os.path.join(OUT, safe(name) + ".qml"))
    if pick.providerType() == "memory":
        opts = QgsVectorFileWriter.SaveVectorOptions(); opts.driverName = "ESRI Shapefile"; opts.fileEncoding = "UTF-8"
        QgsVectorFileWriter.writeAsVectorFormatV3(pick, os.path.join(OUT, safe(name) + ".shp"), QgsCoordinateTransformContext(), opts)
print("styles exported")
'''


def cp_shp(src_base, dst_dir, dst_base=None):
    for e in SHP_EXT:
        s = src_base + "." + e
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(dst_dir, (dst_base or os.path.basename(src_base)) + "." + e))


def d(*parts):
    p = os.path.join(M, *parts); os.makedirs(p, exist_ok=True); return p


def copies():
    b = d("01_Boundaries")
    for f in glob.glob(os.path.join(PKG, "01_boundaries", "SHP", "*")):
        shutil.copy2(f, b)
    s = d("02_Settlements")
    for f in glob.glob(os.path.join(PKG, "02_settlements", "SHP", "*")):
        shutil.copy2(f, s)
    cp_shp(os.path.join(REPO, "W14", "shp", "Settlements_merged"), s, "Settlements_full_W14")
    p = d("03_Plots_meters")
    for f in glob.glob(os.path.join(PKG, "03_meters", "SHP", "*")) + glob.glob(os.path.join(PKG, "04_plots", "SHP", "*")):
        shutil.copy2(f, p)
    cp_shp(os.path.join(W16, "report_basis", "shp", "free_meters"), p)
    cp_shp(os.path.join(REPO, "W14", "shp", "PLOTS_load"), p, "Plots_full_W14")
    h = d("04_Hydrology")
    cp_shp(os.path.join(HYD, "SHP", "Streams", "Streams NSA 2m project boundary"), h)
    cp_shp(os.path.join(HYD, "SHP", "Upstream Catchments", "Upstream Catchments"), h)
    cp_shp(os.path.join(HYD, "SHP", "Road centerline 2", "Road_Centercline"), d("05_Roads"))
    shutil.copy2(os.path.join(HYD, "Raster", "GHS POP 2025 IBRI.tif"), d("06_Population"))
    e = d("08_Existing_network")
    for n in ("Main Pipe", "Sub Main Pipe guide"):
        cp_shp(os.path.join(HYD, "SHP", "Main Pipe", n), e)
    cp_shp(os.path.join(HYD, "SHP", "IBRI STP", "IBRI STP"), e)
    nw = d("08_Existing_network", "NAMA_wastewater")
    for n in ("SEWERLINE_IBRI", "FORCELINE_IBRI", "TE_LINE_IBRI", "GR_TEPS_IBRI", "STP_PT_IBRI", "STP_BUILDING_IBRI"):
        cp_shp(os.path.join(DATA, "Received", "09-RECEIVED", "NAMA", "IBRI", "WW", "SHIP", n), nw)
    pw = d("09_PAEW"); kmz = os.path.join(DATA, "Received", "09-RECEIVED", "KMZ")
    shutil.copy2(os.path.join(kmz, "PAEW_MAIN.kmz"), pw)
    for tag, dst in (("110", "Al_Raybah_110.kmz"), ("180", "Al_Raybah_180.kmz"), ("225t", "Al_Raybah_225.kmz")):
        shutil.copy2(glob.glob(os.path.join(kmz, f"*{tag}.kmz"))[0], os.path.join(pw, dst))
    ip = d("10_Identified_projects")
    for f in glob.glob(os.path.join(PKG, "05_identified_projects", "SHP", "*")):
        shutil.copy2(f, ip)
    w = d("11_Network_design_W15")
    for n in ("W13_A_tree_pipes", "W13_A_tree_outlets", "W15_A_groups"):
        cp_shp(os.path.join(REPO, "W15", "shp", n), w)
    shutil.copy2(os.path.join(REPO, "W15", "kmz", "IBRI subnetwroks W15.kmz"), w)
    r = d("Reports")
    for f in ("report_basis/R0/Ibri_Design_Basis_Report_R0.docx", "report_basis/R0/Ibri_Design_Basis_Report_R0.pdf"):
        shutil.copy2(os.path.join(W16, f), r)
    for f in ("report/R2/Ibri_Concept_Design_Report_R2.docx", "report/R2/Ibri_Concept_Design_Report_R2.pdf"):
        shutil.copy2(os.path.join(REPO, "W14", f), r)
    shutil.copy2(os.path.join(W16, "report_basis", "deck", "Ibri_Design_Basis_Meeting_2026-09-16 - 2.pptx"), os.path.join(r, "Ibri_Design_Basis_Meeting_2026-09-16.pptx"))
    t = d("Tables")
    shutil.copy2(os.path.join(W16, "analysis", "meter_tariff_to_nama_category.xlsx"), t)
    shutil.copy2(os.path.join(REPO, "W14", "analysis", "W14_growth_by_settlement.xlsx"), t)
    dl = d("Delivered")
    shutil.copy2(os.path.join(W16, "deliverables", "Ibri_Design_Basis_Data_R0.zip"), dl)
    shutil.copytree(PKG, os.path.join(dl, "unpacked"), dirs_exist_ok=True)
    print("copies done")


def rasters():
    """The 0.5 m terrain resampled to 2 m with a hillshade; the five flood-hazard rasters of the
    2331 study clipped to the project boundary plus 2 km."""
    t = d("07_Terrain"); h = d("04_Hydrology")
    warp = os.path.join(QGIS_BIN, "gdalwarp.exe"); dem = os.path.join(QGIS_BIN, "gdaldem.exe")
    src = os.path.join(HYD, "Terrain", "Sat_0p5m", "IBRI_0p5_clip.tif")
    out = os.path.join(t, "IBRI_terrain_2m.tif")
    if not os.path.exists(out):
        subprocess.run([warp, "-q", "-tr", "2", "2", "-r", "average", "-multi", "-wo", "NUM_THREADS=ALL_CPUS", "-co", "COMPRESS=DEFLATE", "-co", "PREDICTOR=3",
                        "-co", "TILED=YES", "-co", "BIGTIFF=IF_SAFER", src, out], check=True, env=GDAL_ENV)
        subprocess.run([dem, "hillshade", "-q", "-z", "1.5", "-compute_edges", "-co", "COMPRESS=DEFLATE", "-co", "TILED=YES", out,
                        os.path.join(t, "IBRI_terrain_2m_hillshade.tif")], check=True, env=GDAL_ENV)
    for T in (10, 25, 50, 100, 500):
        out = os.path.join(h, f"Hazard_T{T}y.tif")
        if not os.path.exists(out):
            subprocess.run([warp, "-q", "-te", "429568", "2554439", "480010", "2583936", "-multi", "-wo", "NUM_THREADS=ALL_CPUS", "-co", "COMPRESS=DEFLATE",
                            "-co", "TILED=YES", os.path.join(HAZARD, f"Hazard_T{T}y.tif"), out], check=True, env=GDAL_ENV)
    print("rasters done")


def styles():
    """Export the styles from the running stp2.qgz through the plugin's socket."""
    sys.path.insert(0, os.path.join(W16, "report_basis"))
    import qgis_direct
    out = d("_styles")
    code = EXPORT_CODE.replace("%OUT%", out).replace("%NAMES%", repr(STYLE_LAYERS))
    qgis_direct.exec_code(code)
    # the identified-project points drawn by the report script, exported from the memory layer
    cp_shp(os.path.join(out, "Identified_project"), os.path.join(M, "10_Identified_projects"), "Identified_project_sites")


def project():
    bat = os.path.join(QGIS_BIN, "python-qgis-ltr.bat")
    subprocess.run(["cmd", "/c", bat, os.path.join(HERE, "make_meeting_project.py")], check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})


if __name__ == "__main__":
    os.makedirs(M, exist_ok=True)
    copies()
    rasters()
    styles()
    project()
