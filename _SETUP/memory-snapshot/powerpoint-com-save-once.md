---
name: powerpoint-com-save-once
description: "Editing the engineer's decks through PowerPoint COM - copy the file, open it, edit, save ONCE; SaveAs then Save swaps his maps for logos and icons"
metadata:
  node_type: memory
  type: project
  originSessionId: dacc1452-7243-4d99-a7ca-492275e413da
  modified: 2026-10-02T09:23:04.652Z
---

When a deck is edited through PowerPoint COM (pywin32), never `Open(src)` → `SaveAs(out)` → edit → `Save()`.
PowerPoint loads pictures lazily; on the second save it re-reads them by their OLD part names from the NEW file,
and pictures on untouched slides come out swapped (found 2026-10-02 on the engineer's design-basis deck: the
land-use map, growth chart and Mara chart became logos/icons, the end slide lost its logo).

**Why:** a plain single SaveAs is clean and an in-place open-edit-save is clean (both tested pixel by pixel);
only SaveAs followed by a further save corrupts. Missing SVG fallback images in his deck were a red herring.

**How to apply:** `shutil.copy2(base, out)`, `Presentations.Open(out)`, duplicate/edit, `Save()` once; then
python-pptx edits on the closed file are safe. Always compare his slides against a render of the base
(COM `Slide.Export`) before delivering. Pattern: `W17/presentation/build_deck_w17.py`. See [[report-format-preferences]].
