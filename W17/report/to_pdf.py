"""Render a .docx to PDF through Word itself.

Word is the only renderer that draws OMML the way the reader will see it, so
this doubles as the check that every equation in the document is correct.
Also refreshes fields, which is what fills the table of contents.
"""
import os
import sys


def convert(docx_path, pdf_path=None, update_fields=True):
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
            # twice: the lists of figures and tables grow by pages when first filled, which moves
            # every page number after them. Fields.Update alone does not always fill those lists,
            # so they are updated by name.
            for _ in range(2):
                for i in range(doc.TablesOfFigures.Count):
                    doc.TablesOfFigures(i + 1).Update()
                for i in range(doc.TablesOfContents.Count):
                    doc.TablesOfContents(i + 1).Update()
                doc.Fields.Update()
            doc.Save()                       # the Word file opens with its contents and lists filled
        # to a temporary name first: with alerts off Word skips a PDF that a viewer holds open and
        # says nothing, which leaves the old PDF in place beside a new Word file
        tmp = pdf_path + ".tmp.pdf"
        if os.path.exists(tmp):
            os.remove(tmp)
        doc.SaveAs(tmp, FileFormat=17)       # wdFormatPDF
        pages = doc.ComputeStatistics(2)     # wdStatisticPages
        if not os.path.exists(tmp):
            raise RuntimeError(f"Word did not write the PDF: {tmp}")
        os.replace(tmp, pdf_path)            # raises if the old PDF is open in a viewer
        return pdf_path, pages
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        word.Quit()


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "_omml_test.docx"
    out, pages = convert(src)
    print(f"wrote {out}  ({pages} pages)")
