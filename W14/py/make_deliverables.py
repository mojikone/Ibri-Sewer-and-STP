"""Copy the final outputs of W14 into W14/deliverables/ with a manifest, so the
client package can be picked up from one folder. Re-runnable; overwrites."""
import os, shutil, glob, datetime
W14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(W14, "deliverables")
ITEMS = [
    ("report/R2/Ibri_Concept_Design_Report_R2.docx", "01_report", "Concept Design Report, Revision 2, Word"),
    ("report/R2/Ibri_Concept_Design_Report_R2.pdf", "01_report", "Concept Design Report, Revision 2, PDF"),
    ("analysis/W14_growth_by_settlement.xlsx", "02_tables", "Population and sewage per settlement per year to 2100; five-year tables to saturation; occupancy; overflow routes; the rules"),
    ("analysis/occupancy_by_settlement.csv", "02_tables", "Occupancy per settlement, derived and adopted"),
    ("analysis/settlements_today.csv", "02_tables", "Per settlement: people 2024, occupancy, properties per home plot, home share, capacity"),
    ("analysis/CRT_accounts_identified.csv", "02_tables", "The 499 large-consumer accounts with the use found, the evidence and a confidence"),
    ("shp/PLOTS_load.*", "03_gis", "Every plot: meters by category, use, people, water and sewage by stream, 2024 and 2030 / 2055 / saturation"),
    ("shp/ELE_meters_on_plots.*", "03_gis", "Every electricity meter with its category, its plot and its settlement"),
    ("shp/Settlements_merged.*", "03_gis", "The 25 settlements as a partition, with people, occupancy, capacity and fill year"),
    ("shp/Identified_projects_OSM.*", "03_gis", "Footprints of the identified sites: the two estates, the army camp, the treatment plant, hotels"),
    ("report/img/M0*.png", "04_figures", "Report maps"),
    ("report/img/C*.png", "04_figures", "Report charts"),
    ("report/img/D*.png", "04_figures", "Report flowcharts"),
    ("img/W14_ndvi_contact_sheet_T1000.png", "04_figures", "The satellite calibration sheet for the farm test"),
    ("docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md", "05_method", "The method note behind Part D of the report"),
    ("docs/W14_LOAD_AND_GROWTH.md", "05_method", "Rules and results of the load and growth chain"),
    ("analysis/IDENTIFIED_PROJECTS.md", "05_method", "Register of identified projects and special consumption, with the decisions"),
]
if os.path.exists(OUT):
    shutil.rmtree(OUT)
rows = []
for pattern, sub, what in ITEMS:
    dst = os.path.join(OUT, sub); os.makedirs(dst, exist_ok=True)
    files = sorted(glob.glob(os.path.join(W14, pattern)))
    for f in files:
        shutil.copy2(f, dst)
    names = ", ".join(os.path.basename(f) for f in files) if len(files) <= 4 else f"{len(files)} files ({os.path.basename(files[0])} …)"
    rows.append((sub, names, what))
with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fh:
    fh.write(f"# Ibri Sewer, TE Networks and STP — deliverables of the concept stage, Revision 2\n\nRenardet project 2621. Packaged {datetime.date.today().isoformat()} from W14.\n\n")
    fh.write("| Folder | Files | What it is |\n|---|---|---|\n")
    for sub, names, what in rows:
        fh.write(f"| {sub} | {names} | {what} |\n")
    fh.write("\nAll layers are in UTM zone 40 North, WGS 84 (EPSG:32640). The plot layer's fields are described in Appendix A4 of the report.\n")
print("deliverables:", OUT, "|", sum(len(glob.glob(os.path.join(W14, p))) for p, _, _ in ITEMS), "files")
