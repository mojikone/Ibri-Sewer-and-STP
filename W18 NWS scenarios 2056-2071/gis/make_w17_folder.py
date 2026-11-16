"""Fill W17/Options 2026-10 (not in git) with the base layers and styles the W17 QGIS project needs, copied from the
meeting folder of 16 September 2026, and the option layers built by make_option_layers.py. Re-runnable.

    python make_w17_folder.py
"""
import glob, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
REPO = os.path.dirname(W17)
MEET = os.path.join(REPO, "W16", "Meeting 2026-09-16")
F = os.path.join(W17, "Options 2026-10")
SHP = ("shp", "shx", "dbf", "prj", "cpg", "qix")
COPIES = [("01_Boundaries", "Project_boundary_updated"), ("01_Boundaries", "Project_boundary_received"),
          ("02_Settlements", "Settlements"), ("05_Roads", "Road_Centercline")]
STYLES = ["Project_Boundary_updated", "Settlement_boundary_redrawn_as_a_partition", "Road_Centercline", "Google_Satellite"]

for sub in ("01_Boundaries", "02_Settlements", "05_Roads", "11_Network_options", "12_SewerGEMS", "Maps", "Tables", "Reports", "_styles"):
    os.makedirs(os.path.join(F, sub), exist_ok=True)
for sub, stem in COPIES:
    for ext in SHP:
        src = os.path.join(MEET, sub, f"{stem}.{ext}")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(F, sub))
for s in STYLES:
    src = os.path.join(MEET, "_styles", s + ".qml")
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(F, "_styles"))
shutil.copy2(os.path.join(HERE, "OPTIONS_FOLDER_README.md"), os.path.join(F, "README.md"))   # what the folder holds
print("folder:", F)
for root, dirs, files in os.walk(F):
    if files:
        print(f"  {os.path.relpath(root, F):22s} {len(files)} files")
