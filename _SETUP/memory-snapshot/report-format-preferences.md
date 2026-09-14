---
name: report-format-preferences
description: "How the engineer wants client reports built (set 2026-09-14 for the Design Basis Report): firm's template, Word-native captions, symbol lines not tables, 50 % imagery, no worked examples, plain words, decisions register"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 14df62fa-82b1-4684-b552-13279f047038
  modified: 2026-09-14T09:36:32.294Z
---

For any client report from 2026-09-14 on: build on the firm's template (cover, header, footer,
Century Gothic navy headings, **no indent**), captions as Word-native SEQ fields so a figure added
in Word renumbers, the symbols under an equation as one line each (`symbol; description, unit`),
tables with a navy header and no banding, satellite backgrounds at **50 %** opacity, coloured
land-use plots **without outlines** (only empty plots outlined), **no worked examples**, every
assumption in one table with its reason, plain words, and a numbered register of decisions at the
end, each a yes/no. Every map layout is kept saved in the QGIS project.

**Why:** the report goes to NWS for approval, where "any word may attract a comment"; hard
vocabulary and worked examples invite comment rounds. Native captions because the engineer edits
in Word. The sample's blue table banding and parameter tables he found ugly.

**How to apply:** use `W16/report/doc.py` (template, `fig_caption`, `tab_caption`, `symbols`,
`wide_figures`) and the pattern of `W16/report_basis/rpt_basis.py`; the register in
`decisions.py` feeds both the front summary and the last section. Read the exported pages, not
the exit code. See [[plain-wording-not-literary]] and [[report-exec-summary-priority]].
