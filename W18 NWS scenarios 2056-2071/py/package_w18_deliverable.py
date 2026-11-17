"""One zip with everything the engineer asked for on 2026-11-17: the QGIS project of the plot flows with its layers
(plot and settlement shapefiles), the team's MH workbook with the capacity and WW Generation updated, and the SewerGEMS
model holding the loads every 5 years 2031-2091 (IBRI_W18_R4, copied out of the VM by job 073) with its results.
Writes deliverables/W18_package_<date>.zip (not in git: the model is 300 MB and the workbook carries the team's raw data).
Run after py/package_qgis_plot_flows.py, py/mh_workbook_capacity.py and job 073.  Usage: python package_w18_deliverable.py"""
import os, zipfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
QZ = os.path.join(W18, "gis", "W18_plot_flows_QGIS.zip")
XL = os.path.join(W18, "results", "New Calculation MH - capacity.xlsx")
MODEL = r"D:\VBOX\bridge\out\w18\model_R4"
W18_SCEN = [str(i) for i in list(range(279794, 279800)) + list(range(279807, 279814))]   # W18-2031 ... W18-2091
OUT = os.path.join(W18, "deliverables", f"W18_package_{datetime.date.today():%Y-%m-%d}.zip")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

model = ["IBRI_W18_R4.stsw", "IBRI_W18_R4.stsw.sqlite"] + [f for f in sorted(os.listdir(MODEL))
         if any(f.startswith(f"IBRI_W18_R4.stsw_1_{s}") for s in W18_SCEN)]
assert len(model) == 2 + 2 * len(W18_SCEN), model
README = """W18 package (2026-11-17)

QGIS/       Open W18_plot_flows.qgz in QGIS 3.x. Plots filled by average flow (m3/d per plot), one year at a time
            (2031, 2056, 2071, 2100); existing plots outlined by land use, proposed plots light grey, plots with no flow
            empty. Layers in QGIS/layers: the plot shapefile (77,265 plots, people and flow every year 2026-2100) and
            the settlement boundaries (25 settlements). Field lists: the two _fields.md files.
Excel/      New Calculation MH - capacity.xlsx: the team's workbook with 'MOHUP DATA - NA' and 'WW Generation' updated
            (capacity = 2026 population + growth plots x properties per plot x 4.8; WW Generation capped at it, plus the
            industrial estates). Every other sheet as received; what changed is on sheet 'Notes (W18)'.
SewerGEMS/  IBRI_W18_R4.stsw (+ .sqlite and the results of its 13 year scenarios). Scenarios W18-2031, W18-2036 ...
            W18-2091: each its own sanitary loading alternative of the same name. Every manhole load is a UNIT load
            'Plot average flow (1 m3/d per unit)', so the Extreme Flow Setup of the calculation options (method
            'Peltier100-Merriamck') peaks it in the run; no pattern loads. Infiltration 720 L/km/day on the conduits
            (the infiltration-and-inflow alternative every W18 scenario inherits, id 11). Plots off the active network
            carry no load in the model.
"""
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    q = zipfile.ZipFile(QZ)
    for n in q.namelist():
        if n.endswith(".xlsx"): continue                    # the earlier capacity workbook: the MH copy replaces it
        b = q.read(n)
        if n.endswith("README.txt"): b = b"".join(l for l in b.splitlines(True) if b".xlsx" not in l)
        z.writestr("QGIS/" + n.split("/", 1)[1], b)
    z.write(XL, "Excel/" + os.path.basename(XL))
    for f in model: z.write(os.path.join(MODEL, f), "SewerGEMS/" + f)
    z.writestr("README.txt", README)
zi = zipfile.ZipFile(OUT)
print(OUT, f"{os.path.getsize(OUT) / 1e6:,.0f} MB, {len(zi.namelist())} files")
for n in zi.infolist():
    if n.file_size > 5e6 or n.filename.count("/") <= 1: print(f"  {n.filename}  {n.file_size / 1e6:,.1f} MB")
