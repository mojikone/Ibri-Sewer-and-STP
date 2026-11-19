"""Open the built report in a separate, hidden Word instance (never the user's own Word), update the caption numbers (not the team's
cross-references) and every table of contents and figures, save, and export the PDF.
Usage: python word_finish.py <docx>"""
import os, sys
import win32com.client as W
docx = os.path.abspath(sys.argv[1]); pdf = docx[:-5] + ".pdf"
app = W.DispatchEx("Word.Application"); app.Visible = False; app.DisplayAlerts = 0
try:
    doc = app.Documents.Open(docx, ReadOnly=False, AddToRecentFiles=False)
    for _ in range(2):                                      # twice: page numbers settle after the captions renumber
        for fld in doc.Fields:                              # caption numbers only (SEQ, STYLEREF): the team's cross-
            if fld.Type in (12, 63): fld.Update()           # references keep their text (several point to removed matter)
        for t in doc.TablesOfContents: t.Update()
        for t in doc.TablesOfFigures: t.Update()
    gone = []                                               # a cross-reference whose target no longer exists keeps its
    for fld in list(doc.Fields):                            # text as plain text, so it can never show 'Error!'
        if fld.Type == 3:
            parts = fld.Code.Text.split()
            if len(parts) > 1 and not doc.Bookmarks.Exists(parts[1]): gone.append(fld.Result.Text.strip()); fld.Unlink()
    print('cross-references to removed targets kept as text:', len(gone), gone[:30])
    doc.Save()
    keep = app.Options.UpdateFieldsAtPrint; app.Options.UpdateFieldsAtPrint = False
    tmp = pdf[:-4] + "_export.pdf"                          # exported under a new name and swapped in: an export over the
    if os.path.exists(tmp): os.remove(tmp)                  # old file once left the old PDF in place without an error
    try: doc.ExportAsFixedFormat(OutputFileName=tmp, ExportFormat=17, OpenAfterExport=False, OptimizeFor=0, CreateBookmarks=1)
    finally: app.Options.UpdateFieldsAtPrint = keep
    if not os.path.exists(tmp): raise SystemExit("PDF export wrote nothing")
    os.replace(tmp, pdf)
    print("pages", doc.ComputeStatistics(2), "| saved", docx, "| pdf", pdf)
    doc.Close(False)
finally:
    app.Quit()
