"""Pack the W18 deliverables toolkit (the inventory, every script, template, style and tool it names) into one zip for building skills.

    python make_toolkit_zip.py        writes W18 NWS scenarios 2056-2071/deliverables/Toolkit_W18_deliverables_<date>.zip

The zip holds the team's R8-MH Word file and the firm's sample template, so it stays out of git (deliverables/ is ignored) and goes
only to the engineer. The WhatsApp sender goes without its auth folder. A missing file fails the run; nothing is skipped quietly."""
import datetime, glob, os, sys, zipfile

C = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))          # Hydraulic/Claude
W = os.path.join(C, "W18 NWS scenarios 2056-2071"); HY = os.path.dirname(C); PR = os.path.dirname(HY)
HOME = os.path.expanduser("~"); MEM = os.path.join(HOME, ".claude", "projects", "D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude", "memory")
TOP = f"Toolkit_W18_deliverables_{datetime.date.today().isoformat()}/"
OUT = os.path.join(W, "deliverables", TOP.rstrip("/") + ".zip")

FILES = [  # (path in the zip, source, what it is)
    ("TOOLKIT_W18_deliverables.md", os.path.join(C, "_SETUP", "TOOLKIT_W18_deliverables.md"), "the inventory: techniques, tools, scripts, templates, traps"),
    *[(f"report/{f}", os.path.join(W, "report_final", f), d) for f, d in [
        ("build_report.py", "report build on the team's Word file (Out writer, finders, Chapter 6 per design year)"),
        ("r10_edits.py", "R10 whole-report rewrite (helpers set_text/sub/para, literal refs, Chapters 8 and 14)"),
        ("r11_edits.py", "R11-R12 layout and review pass (tables, captions, blank pages, sections, references, cover)"),
        ("facts_final.py", "one source of the design numbers per scenario and design year"),
        ("word_finish.py", "Word COM finishing: fields, TOC/TOF, save-and-swap, PDF, retries"),
        ("check_clean.py", "clean-room gate on the PDF"), ("forbidden_terms.txt", "gate: forbidden regexes"), ("allowed_terms.txt", "gate: allowed regexes"),
        ("qa_report.py", "QA: blank pages, captions, footer, references, narrow columns, contact sheets"),
        ("report_workbook.py", "Excel workbook with live formulas and Excel-built charts"),
        ("flow_diagram.py", "flow schematic per scenario and design year (drives diagram_png.py)")]],
    *[(f"design/{f}", os.path.join(W, "py", f), d) for f, d in [
        ("final_design.py", "the design engine run for the 12 designs"), ("routing.py", "scenario routing used by the engine"),
        ("split_deep_subnetworks.py", "splitting deep subnetworks: steepen, cut, lift, gravity joins"),
        ("final_financial.py", "treatment, TE and CAPEX/OPEX by the team's method, per design year"),
        ("final_station_flows.py", "people and flow at every station 2026-2061"), ("final_sg_inputs.py", "SewerGEMS inputs of a design"),
        ("final_dwg.py", "DXF with ezdxf, DWG through AutoCAD accoreconsole"), ("package_final.py", "the deliverable package zip"),
        ("diagram_png.py", "R7 transfer-diagram drawer (matplotlib)"), ("diagram_layout.py", "R7 diagram layout rules"),
        ("diagram_js.py", "R7 diagram for Figma (plugin code)")]],
    *[(f"gis/{f}", os.path.join(W, "gis", f), d) for f, d in [
        ("final_maps.py", "report maps and the QGIS project (make_map: clone, legend, extent, data box)"),
        ("make_w17_project.py", "map helpers imported as M: layout clone, styles, labels, Google background"),
        ("team_maps_redraw.py", "the team's STP-sites and TE-customer maps on the final network"), ("te_map_sc4.py", "SC4 TE network map")]],
    *[(f"studies/drops over 2 m/{f}", os.path.join(W, "studies", "drops over 2 m", f), d) for f, d in [
        ("drops_engine.py", "drops-over-2-m study engine"), ("drops_map.py", "its map"), ("README.md", "its findings and the decision")]],
    ("templates/qgis/template_report_A3.qpt", os.path.join(W, "gis", "template_report_A3.qpt"), "QGIS A3 layout template of every report map"),
    ("templates/qgis/styles/manholes_depth.qml", os.path.join(W, "qgis", "styles", "manholes_depth.qml"), "QML: manholes by depth"),
    ("templates/qgis/styles/Road_Centercline.qml", os.path.join(C, "W17", "Options 2026-10", "_styles", "Road_Centercline.qml"), "QML: road centreline"),
    ("templates/qgis/Ibri_sewer_concept_design.qgz", os.path.join(W, "results", "final_0.75pc_SC1-SC4", "qgis", "Ibri_sewer_concept_design.qgz"),
     "QGIS project of the final design (layer paths are local; the package copy has relative ones)"),
    ("templates/word/Sample.docx", os.path.join(PR, "Data", "sample report", "Sample.docx"), "the firm's report template"),
    ("templates/word/Ibri_Concept_Design_Report_R8-MH.docx", os.path.join(HY, "temp", "recent updates by the team", "Ibri_Concept_Design_Report_R8-MH.docx"),
     "the team's report the build edits (styles, cover, chapters)"),
    ("tools/read_msg.py", os.path.join(C, "_SETUP", "tools", "read_msg.py"), "read an Outlook .msg without Outlook"),
    ("tools/make_toolkit_zip.py", os.path.abspath(__file__), "this packer"),
    ("tools/check_live_docs.py", os.path.join(C, "_SETUP", "check_live_docs.py"), "live-docs check (README and state files behind the work)"),
    ("tools/wa_link/wa.js", os.path.join(HOME, "wa_link", "wa.js"), "WhatsApp linked-device sender (Baileys); auth folder not included"),
    ("tools/wa_link/package.json", os.path.join(HOME, "wa_link", "package.json"), "its dependencies"),
    ("reference/global-CLAUDE.md", os.path.join(C, "_SETUP", "global-CLAUDE.md"), "the engineer's global instructions (SewerGEMS bridge, WhatsApp, report rules)"),
    ("reference/project-CLAUDE.md", os.path.join(C, "CLAUDE.md"), "the project's rules"),
]
import ast


def doc1(p):                                               # what a script is: the first line of its own docstring
    try: d = ast.get_docstring(ast.parse(open(p, encoding="utf-8").read())) or ""
    except Exception: d = ""
    return d.strip().splitlines()[0][:150] if d.strip() else "(no docstring)"


have = {os.path.normcase(os.path.abspath(s)) for _, s, _ in FILES}
for folder, arcdir in (("py", "design"), ("gis", "gis"), ("report_final", "report")):    # every script of the W18 folders, so nothing upstream is missed
    for f in sorted(glob.glob(os.path.join(W, folder, "*.py"))):
        if os.path.normcase(os.path.abspath(f)) not in have: FILES.append((f"{arcdir}/{os.path.basename(f)}", f, doc1(f)))
for arc, src, what in (("w17_report/facts_w17.py", os.path.join(C, "W17", "report", "facts_w17.py"), "W17 report facts, imported by design/boq_workbook.py"),
                       ("w17_report/flow.py", os.path.join(C, "W17", "report", "flow.py"), "W17 flowchart drawer, imported by design/make_appraisal_figure.py"),
                       ("data/catalogue.csv", os.path.join(W, "results", "final_0.75pc_SC1-SC4", "inputs", "catalogue.csv"), "pipe catalogue: nominal and inside diameters"),
                       ("data/fixed_stations.json", os.path.join(W, "results", "final_0.75pc_SC1-SC4", "fixed_stations.json"), "the engineer's station decisions used by the split"),
                       ("data/te_customers.csv", os.path.join(W, "results", "final_0.75pc_SC1-SC4", "te", "te_customers.csv"),
                        "TE customers consolidated from the team's register (team data: not for the public repo)")):
    FILES.append((arc, src, what))
for f in sorted(glob.glob(os.path.join(W, "sewergems_api", "**", "*"), recursive=True)):
    if os.path.isfile(f): FILES.append(("sewergems_api/" + os.path.relpath(f, os.path.join(W, "sewergems_api")).replace("\\", "/"), f, "SewerGEMS API bridge: C# helpers, jobs, watcher"))
for f in sorted(glob.glob(os.path.join(HOME, ".claude", "skills", "report-writing", "**", "*"), recursive=True)):
    if os.path.isfile(f): FILES.append(("skills/report-writing/" + os.path.relpath(f, os.path.join(HOME, ".claude", "skills", "report-writing")).replace("\\", "/"), f, "the report-writing skill"))
for f in sorted(glob.glob(os.path.join(MEM, "*.md"))):
    FILES.append(("memory/" + os.path.basename(f), f, "project memory: preferences and traps"))

missing = [s for _, s, _ in FILES if not os.path.isfile(s)]
if missing: sys.exit("missing: " + "; ".join(missing))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    rows = []
    for arc, src, what in FILES:
        z.write(src, TOP + arc); rows.append(f"{arc}\t{os.path.getsize(src):,} B\t{what}\t<- {src}")
    z.writestr(TOP + "MANIFEST.txt", "Path in the zip\tSize\tWhat it is\tSource\n" + "\n".join(rows) + "\n")
print(f"wrote {OUT}  {len(FILES) + 1} files  {os.path.getsize(OUT) / 1e6:,.1f} MB")
