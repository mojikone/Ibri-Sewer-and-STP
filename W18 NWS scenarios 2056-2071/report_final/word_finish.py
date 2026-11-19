"""Open the built report in a separate, hidden Word instance (never the user's own Word), update the caption numbers (not the team's
cross-references) and every table of contents and figures, save, and export the PDF.
Usage: python word_finish.py <docx>"""
import os, sys, time
import win32com.client as W
import pywintypes
docx = os.path.abspath(sys.argv[1]); pdf = docx[:-5] + ".pdf"


def retry(fn, what, n=4, wait=15):
    """Word answers 'Command failed' on a 190 MB report while it is still laying out pages; wait and try again."""
    for k in range(n):
        try: return fn()
        except pywintypes.com_error as e:
            if k == n - 1: raise
            print(f"  {what}: Word busy ({e.excinfo[2] if e.excinfo else e}), retry {k + 1} in {wait} s", flush=True); time.sleep(wait)


app = W.DispatchEx("Word.Application"); app.Visible = False; app.DisplayAlerts = 0
try:
    doc = retry(lambda: app.Documents.Open(docx, ReadOnly=False, AddToRecentFiles=False), "open")
    keep_pg = app.Options.Pagination; app.Options.Pagination = False        # no background repagination during the updates
    retry(doc.Repaginate, "repaginate")
    for _ in range(2):                                      # twice: page numbers settle after the captions renumber
        for fld in doc.Fields:                              # caption numbers only (SEQ, STYLEREF): the team's cross-
            if fld.Type in (12, 63): retry(fld.Update, "caption field")   # references keep their text (several point to removed matter)
        for t in doc.TablesOfContents: retry(t.Update, "table of contents")
        for t in doc.TablesOfFigures: retry(t.Update, "table of figures")
    gone = []                                               # a cross-reference whose target no longer exists keeps its
    for fld in list(doc.Fields):                            # text as plain text, so it can never show 'Error!'
        if fld.Type == 3:
            parts = fld.Code.Text.split()
            if len(parts) > 1 and not doc.Bookmarks.Exists(parts[1]): gone.append(fld.Result.Text.strip()); fld.Unlink()
    print('cross-references to removed targets kept as text:', len(gone), gone[:30])
    tmpd = docx[:-5] + "_finished.docx"                     # saved under a new name and swapped in after Word closes it: a Save
    if os.path.exists(tmpd): os.remove(tmpd)                # over the open 160 MB file failed with 'Command failed' (R12)
    retry(lambda: doc.SaveAs2(tmpd, FileFormat=16), "save")
    app.Options.Pagination = keep_pg                        # the PDF export needs the page layout: with it off it wrote nothing
    keep = app.Options.UpdateFieldsAtPrint; app.Options.UpdateFieldsAtPrint = False
    tmp = pdf[:-4] + "_export.pdf"                          # exported under a new name and swapped in: an export over the
    if os.path.exists(tmp): os.remove(tmp)                  # old file once left the old PDF in place without an error
    try: retry(lambda: doc.ExportAsFixedFormat(OutputFileName=tmp, ExportFormat=17, OpenAfterExport=False, OptimizeFor=0, CreateBookmarks=1), "pdf export")
    finally: app.Options.UpdateFieldsAtPrint = keep; app.Options.Pagination = keep_pg
    if not os.path.exists(tmp): raise SystemExit("PDF export wrote nothing")
    os.replace(tmp, pdf)
    print("pages", doc.ComputeStatistics(2), "| saved", docx, "| pdf", pdf)
    doc.Close(False)
finally:
    app.Quit()
if os.path.exists(docx[:-5] + "_finished.docx"): os.replace(docx[:-5] + "_finished.docx", docx)
