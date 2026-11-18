"""One zip with everything the engineer asked for on 2026-11-17: the QGIS project of the plot flows with its layers
(plot and settlement shapefiles), the team's MH workbook with the capacity and WW Generation updated, and the SewerGEMS
model. 2026-11-18 (engineer: "include the SewerGEMS model" with the QGIS project, the plot layers and the SC1
conditions and maps): the model is the SC1 design IBRI_W18_R5_SC1_2056 (job 074; it holds R4's loads every 5 years
2031-2091 as well), copied out of the VM by job 075, with the results of its 3 SC1 and 13 year scenarios; the QGIS
part now carries the SC1 conditions. (The 2026-11-17 package carried R4: deliverables/W18_package_2026-11-17.zip.)
Writes deliverables/W18_package_SC1_<date>.zip (not in git: the model is 300 MB).
Run after py/package_qgis_plot_flows.py, py/mh_workbook_capacity.py and job 075.  Usage: python package_w18_deliverable.py"""
import os, zipfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
QZ = os.path.join(W18, "gis", "W18_plot_flows_QGIS.zip")
XL = os.path.join(W18, "results", "New Calculation MH - capacity.xlsx")
MODEL = r"D:\VBOX\bridge\out\w18\model_R5"
NAME = "IBRI_W18_R5_SC1_2056"
W18_SCEN = [str(i) for i in list(range(279794, 279800)) + list(range(279807, 279814))]   # W18-2031 ... W18-2091
SC1_SCEN = ["279817", "279818", "279819"]            # SC1-2056 (design), SC1-2056A, SC1-2056-at-2031 (job 074)
OUT = os.path.join(W18, "deliverables", f"W18_package_SC1_{datetime.date.today():%Y-%m-%d}.zip")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

model = [f"{NAME}.stsw", f"{NAME}.stsw.sqlite"] + [f for f in sorted(os.listdir(MODEL))
         if any(f.startswith(f"{NAME}.stsw_1_{s}") for s in W18_SCEN + SC1_SCEN)]
assert len(model) == 2 + 2 * len(W18_SCEN + SC1_SCEN), model
README = f"""W18 package with the SC1 conditions ({datetime.date.today():%Y-%m-%d})

QGIS/       Open W18_plot_flows.qgz in QGIS 3.x. Plots filled by average flow (m3/d per plot), one year at a time
            (2031, 2056, 2071, 2100); existing plots outlined by land use, proposed plots light grey, plots with no flow
            empty. Layers in QGIS/layers: the plot shapefile (77,265 plots, people and flow every year 2026-2100) and
            the settlement boundaries (25 settlements). Field lists: the two _fields.md files.
            Group 'SC1 sewer conditions' (one at a time; layouts SC1 C0 ... C3 under Project > Layouts): SC1 re-laid
            from the SewerGEMS design below - C0 as designed (velocity at the 2031 peak); C1-C3 pipes above DN200
            steepened to reach 0.75 m/s at the 2031 peak, gradient up to 0.50 / 0.75 / 1.00 %, one gradient per street
            run, split where a subnetwork stays deeper than 12 m (O14 and O11 kept deep, uncut). Layers in
            QGIS/layers/sc1_conditions, exported maps in QGIS/sc1_conditions/maps, each condition's numbers in
            QGIS/sc1_conditions/*_SUMMARY.md.
Excel/      New Calculation MH - capacity.xlsx: the team's workbook with 'MOHUP DATA - NA' and 'WW Generation' updated
            (capacity = 2026 population + growth plots x properties per plot x 4.8; WW Generation capped at it, plus the
            industrial estates). Every other sheet as received; what changed is on sheet 'Notes (W18)'.
SewerGEMS/  IBRI_W18_R5_SC1_2056.stsw (+ .sqlite and results). SC1 scenarios: SC1-2056 (STP at O1, pipes designed for
            2056, flows between subnetworks as loads at the receiving manholes), SC1-2056A (analysis of the designed
            pipes in 2056), SC1-2056-at-2031 (the same pipes with the 2031 loads). The four conditions in QGIS are
            re-laid from this design; their cuts and joins are not in the model yet.
            Year scenarios W18-2031, W18-2036 ... W18-2091 (results as computed before the SC1 scenarios were added;
            rerun any of them if SewerGEMS marks it out of date): each its own sanitary loading alternative of the
            same name. Every manhole load is a UNIT load
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
