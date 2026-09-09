"""Render a .docx to PDF through Word itself.

Word is the only renderer that draws OMML the way the reader will see it, so
this doubles as the check that every equation in the document is correct.
Also refreshes fields, which is what fills the table of contents, and saves the
refreshed fields back into the .docx so the Word file carries a real contents
list rather than the placeholder.
"""
import os
import sys


def convert(docx_path, pdf_path=None, update_fields=True, save_docx=True):
    import win32com.client
    docx_path = os.path.abspath(docx_path)
    pdf_path = pdf_path or os.path.splitext(docx_path)[0] + ".pdf"
    pdf_path = os.path.abspath(pdf_path)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(docx_path, ReadOnly=False)
        if update_fields:
            for i in range(doc.TablesOfContents.Count):
                doc.TablesOfContents(i + 1).Update()
            doc.Fields.Update()
            if save_docx:
                doc.Save()
        doc.SaveAs(pdf_path, FileFormat=17)  # wdFormatPDF
        pages = doc.ComputeStatistics(2)     # wdStatisticPages
        return pdf_path, pages
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        word.Quit()


if __name__ == "__main__":
    src = sys.argv[1]
    out, pages = convert(src)
    print(f"wrote {out}  ({pages} pages)")
