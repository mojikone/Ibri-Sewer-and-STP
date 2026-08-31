"""Real Word footnotes.

python-docx has no footnote support, so the reference marks are written into
the document as it is built and the footnotes part is injected into the .docx
package on save. The result is a genuine Word footnote: numbered
automatically, sitting at the foot of its own page, and editable.
"""
import os
import shutil
import zipfile

from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Pt

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = f'xmlns:w="{W}"'

_notes = []          # footnote texts, in order
_FIRST_ID = 2        # 0 and 1 are the separator footnotes Word reserves


def reset():
    _notes.clear()


def add(paragraph, text):
    """Attach a footnote to the end of `paragraph`."""
    _notes.append(text)
    fid = _FIRST_ID + len(_notes) - 1
    xml = (f'<w:r {NS}><w:rPr><w:rStyle w:val="FootnoteReference"/>'
           f'<w:vertAlign w:val="superscript"/></w:rPr>'
           f'<w:footnoteReference w:id="{fid}"/></w:r>')
    paragraph._p.append(parse_xml(xml))
    return fid


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _footnotes_xml():
    parts = [f'<w:footnotes {NS}>']
    for i, kind in ((0, "separator"), (1, "continuationSeparator")):
        parts.append(
            f'<w:footnote w:type="{kind}" w:id="{i}"><w:p><w:pPr>'
            f'<w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
            f'<w:r><w:{kind}/></w:r></w:p></w:footnote>')
    for n, text in enumerate(_notes):
        parts.append(
            f'<w:footnote w:id="{_FIRST_ID + n}"><w:p><w:pPr>'
            f'<w:spacing w:after="40"/>'
            f'<w:rPr><w:sz w:val="16"/></w:rPr></w:pPr>'
            f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>'
            f'<w:vertAlign w:val="superscript"/></w:rPr>'
            f'<w:footnoteRef/></w:r>'
            f'<w:r><w:rPr><w:sz w:val="16"/></w:rPr>'
            f'<w:t xml:space="preserve"> {_esc(text)}</w:t></w:r>'
            f'</w:p></w:footnote>')
    parts.append("</w:footnotes>")
    return "".join(parts)


def save(doc, path):
    """Save the document and inject the footnotes part."""
    doc.save(path)
    if not _notes:
        return path

    tmp = path + ".tmp"
    REL = ("http://schemas.openxmlformats.org/officeDocument/2006/"
           "relationships/footnotes")
    CT = ("application/vnd.openxmlformats-officedocument."
          "wordprocessingml.footnotes+xml")

    with zipfile.ZipFile(path) as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                s = data.decode("utf-8")
                if "footnotes+xml" not in s:
                    s = s.replace(
                        "</Types>",
                        f'<Override PartName="/word/footnotes.xml" '
                        f'ContentType="{CT}"/></Types>')
                data = s.encode("utf-8")
            elif item.filename == "word/_rels/document.xml.rels":
                s = data.decode("utf-8")
                if "footnotes.xml" not in s:
                    s = s.replace(
                        "</Relationships>",
                        f'<Relationship Id="rIdFootnotes" Type="{REL}" '
                        f'Target="footnotes.xml"/></Relationships>')
                data = s.encode("utf-8")
            zout.writestr(item, data)
        zout.writestr("word/footnotes.xml", _footnotes_xml())

    os.replace(tmp, path)
    return path


def ensure_style(doc):
    """A footnote-reference character style, so Word renders the mark small."""
    styles = doc.styles.element
    existing = [s for s in styles.findall(qn("w:style"))
                if s.get(qn("w:styleId")) == "FootnoteReference"]
    if not existing:
        styles.append(parse_xml(
            f'<w:style {NS} w:type="character" w:styleId="FootnoteReference">'
            f'<w:name w:val="footnote reference"/>'
            f'<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'))
