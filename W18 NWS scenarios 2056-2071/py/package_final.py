"""W18 final design: one zip with everything the team receives (current names only):
  Report/         the concept design report (Word and PDF) of revision REV, and the workbook of its tables and charts
  Drawings/       the design drawings of the four scenarios (DWG, 2056 design, UTM 40N)
  BOQ/            the bill of quantities and network capital cost workbook; treatment, TE and financial workbook
  Maps/           the report maps (2056 design)
  QGIS/           the project of the four scenarios and three design years, with its layers (paths made relative)
  SewerGEMS/      the models of the four scenarios designed for 2051, 2056 and 2061 (with results)
Usage: python package_final.py      Writes deliverables/Ibri_Sewer_Final_Design_SC1-SC4_<REV>_<date>.zip"""
import os, zipfile, re, glob, datetime, io
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); RF = os.path.join(W18, "report_final")
DATE = datetime.date.today().isoformat(); REV = "R11"
OUT = os.path.join(W18, "deliverables", f"Ibri_Sewer_Final_Design_SC1-SC4_{REV}_{DATE}.zip"); os.makedirs(os.path.dirname(OUT), exist_ok=True)
TOP = "Ibri_Sewer_Final_Design_SC1-SC4/"
QGZ = os.path.join(R, "qgis", "Ibri_sewer_concept_design.qgz")
BND = os.path.join(W18, "..", "W17", "Options 2026-10", "01_Boundaries", "Project_boundary_updated")
STL = os.path.join(W18, "gis", "W18_settlements_2026_2100")
MODELS = r"D:\VBOX\bridge\out\w18\final_models"
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
    for f in glob.glob(os.path.join(RF, REV, "*.docx")) + glob.glob(os.path.join(RF, REV, "*.pdf")): z.write(f, TOP + "Report/" + os.path.basename(f))
    for f in glob.glob(os.path.join(RF, "deliverables", "*.xlsx")):
        z.write(f, TOP + ("Report/" if "Tables_and_Charts" in f else "BOQ/") + os.path.basename(f))
    for f in glob.glob(os.path.join(RF, "deliverables", "dwg", "*.dwg")): z.write(f, TOP + "Drawings/" + os.path.basename(f))
    for f in glob.glob(os.path.join(RF, "img", "*.png")): z.write(f, TOP + "Maps/" + os.path.basename(f))
    # the QGIS project: every layer source rewritten to ./layers/
    q = zipfile.ZipFile(QGZ); name = [n for n in q.namelist() if n.endswith(".qgs")][0]; qgs = q.read(name).decode("utf-8")
    cases = sorted({m for m in re.findall(r"(SC\d-20\d\d)/products/map\.gpkg", qgs)})
    for c in cases:
        qgs = re.sub(rf"[^\"<>|]*?{c}/products/map\.gpkg", f"./layers/{c}.gpkg", qgs)
        z.write(os.path.join(R, c, "products", "map.gpkg"), TOP + f"QGIS/layers/{c}.gpkg")
    qgs = re.sub(r"[^\"<>|]*?Project_boundary_updated\.shp", "./layers/Project_boundary.shp", qgs)
    qgs = re.sub(r"[^\"<>|]*?W18_settlements_2026_2100\.shp", "./layers/Settlements.shp", qgs)
    for src, dst in ((BND, "Project_boundary"), (STL, "Settlements")):
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            if os.path.exists(src + ext): z.write(src + ext, TOP + f"QGIS/layers/{dst}{ext}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as qz:
        qz.writestr(os.path.basename(name), qgs)
        for n in q.namelist():
            if n != name: qz.writestr(n, q.read(n))
    z.writestr(TOP + "QGIS/Ibri_sewer_concept_design.qgz", buf.getvalue())
    # the model, its database and the results of its three final scenarios (2056 design 279818, at the 2031 peak 279829,
    # at the 2036 peak 279830); the results the source model kept for its earlier scenarios are left out
    for f in glob.glob(os.path.join(MODELS, "*")):
        b = os.path.basename(f)
        if b.endswith((".stsw", ".stsw.sqlite")) or any(f"_{s}" in b for s in ("279818", "279829", "279830")):
            z.write(f, TOP + "SewerGEMS/" + b)
    z.writestr(TOP + "READ ME.txt",
               "Ibri sewer network, concept design of scenarios SC1 to SC4 (gradient limit 0.75 %, design year 2056; QGIS also 2051 and 2061)\n"
               "Report: the concept design report, every chapter on the four scenarios and the 2056 design (Word and PDF), and the workbook of "
               "its tables and charts (live formulas; each chart is built in Excel from its table).\n"
               "Drawings: one DWG per scenario, designed for 2056, in UTM zone 40N metres. Layers by family (gravity sewers by size, "
               "manholes, deep and drop manholes, rising mains, stations, plants), their text on separate TXT- layers: stations and "
               "plants read zoomed out; zoomed in, every pipe carries its size, length, gradient, design flow, velocity and inverts, "
               "and every manhole its ground level, invert, depth and drop.\n"
               "BOQ: quantities by bill and the network capital cost at the rates of the options cost estimate (formulas); treatment modules, "
               "treated effluent supply and the CAPEX/OPEX of the four scenarios.\n"
               "Maps: the report maps. QGIS: open Ibri_sewer_concept_design.qgz; one group per scenario and design year.\n"
               "SewerGEMS: one model per scenario and design year (2051, 2056, 2061); open the scenario 'SC#-<year> design' for the design year and "
               "'... at the 2031 peak' / '... at the 2036 peak' for the self-cleansing checks (the other scenarios are the source model's). "
               "Gravity joins between systems are carried as flow transfers to the receiving manhole.\n"
               "Names: pumping stations P1 to P15, lift stations P#L#, manholes and pipes by the station they drain to (P4-M12, P4L1-P3).\n")
print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:,.0f} MB")
