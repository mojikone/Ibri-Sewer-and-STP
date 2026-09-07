"""Native Word (OMML) equation builders.

Produces real Office Math markup, so every equation in the output document is
editable in Word's equation editor rather than a pasted picture.

Compose with the primitives below and hand the result to `display()` for a
centred numbered equation, or `inline()` for one that sits inside a sentence.
"""
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn

NSDECL = ('xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
          'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')

_ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def esc(t):
    return "".join(_ESC.get(c, c) for c in str(t))


# ---------------------------------------------------------------- primitives
def r(t, sty=None):
    """A math run. sty: 'p' upright (roman), 'i' italic, 'b' bold, 'bi'."""
    rpr = '<m:rPr><m:sty m:val="%s"/></m:rPr>' % sty if sty else ""
    return (f'<m:r>{rpr}<w:rPr><w:rFonts w:ascii="Cambria Math" '
            f'w:hAnsi="Cambria Math"/></w:rPr>'
            f'<m:t xml:space="preserve">{esc(t)}</m:t></m:r>')


def up(t):
    """Upright text inside an equation - use for multi-letter names and units."""
    return r(t, "p")


def frac(num, den):
    return f'<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>'


def sqrt(e):
    return ('<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr>'
            f'<m:deg/><m:e>{e}</m:e></m:rad>')


def root(deg, e):
    return f'<m:rad><m:radPr/><m:deg>{deg}</m:deg><m:e>{e}</m:e></m:rad>'


def sub(base, s):
    return f'<m:sSub><m:e>{base}</m:e><m:sub>{s}</m:sub></m:sSub>'


def sup(base, s):
    return f'<m:sSup><m:e>{base}</m:e><m:sup>{s}</m:sup></m:sSup>'


def subsup(base, s, p):
    return (f'<m:sSubSup><m:e>{base}</m:e><m:sub>{s}</m:sub>'
            f'<m:sup>{p}</m:sup></m:sSubSup>')


def delim(e, left="(", right=")"):
    """Auto-sizing brackets."""
    return (f'<m:d><m:dPr><m:begChr m:val="{esc(left)}"/>'
            f'<m:endChr m:val="{esc(right)}"/></m:dPr><m:e>{e}</m:e></m:d>')


def nary(op, lo, hi, e, hide_lo=False, hide_hi=False):
    """Summation / product / integral. op is the operator character."""
    pr = (f'<m:naryPr><m:chr m:val="{esc(op)}"/>'
          f'<m:limLoc m:val="undOvr"/>'
          f'<m:subHide m:val="{1 if hide_lo else 0}"/>'
          f'<m:supHide m:val="{1 if hide_hi else 0}"/></m:naryPr>')
    return f'<m:nary>{pr}<m:sub>{lo}</m:sub><m:sup>{hi}</m:sup><m:e>{e}</m:e></m:nary>'


def bar(e):
    """Overbar - a mean value."""
    return ('<m:bar><m:barPr><m:pos m:val="top"/></m:barPr>'
            f'<m:e>{e}</m:e></m:bar>')


def func(name, arg):
    """A named function such as log or exp."""
    return f'<m:func><m:fName>{up(name)}</m:fName><m:e>{arg}</m:e></m:func>'


def seq(*parts):
    return "".join(parts)


# ------------------------------------------------------------------ emitters
def _append_body(doc, element):
    """Append in document flow - i.e. before the trailing <w:sectPr>.

    Appending straight to the body puts the element after the section
    properties, which makes Word render every such paragraph at the end of the
    document instead of where it was written.
    """
    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    if sect is not None:
        sect.addprevious(element)
    else:
        body.append(element)
    return element


def display(doc, inner, number=None, anchor=None):
    """Centred display equation. `number` prints right-aligned as (n)."""
    if number is None:
        xml = (f'<w:p {NSDECL}><w:pPr><w:jc w:val="center"/>'
               f'<w:spacing w:before="120" w:after="120"/></w:pPr>'
               f'<m:oMathPara><m:oMath>{inner}</m:oMath></m:oMathPara></w:p>')
    else:
        # tab-stopped so the equation centres and the number sits at the margin
        xml = (f'<w:p {NSDECL}><w:pPr><w:tabs>'
               f'<w:tab w:val="center" w:pos="4320"/>'
               f'<w:tab w:val="right" w:pos="8640"/></w:tabs>'
               f'<w:spacing w:before="120" w:after="120"/></w:pPr>'
               f'<w:r><w:tab/></w:r>'
               f'<m:oMath>{inner}</m:oMath>'
               f'<w:r><w:tab/><w:t>({esc(number)})</w:t></w:r></w:p>')
    return _append_body(doc, parse_xml(xml))


def inline(paragraph, inner):
    """Append an equation inside an existing paragraph."""
    xml = f'<m:oMath {NSDECL}>{inner}</m:oMath>'
    paragraph._p.append(parse_xml(xml))
    return paragraph


# ---------------------------------------------------------- common shorthand
def Q(s):
    return sub(r("Q"), up(s))


def P(s):
    return sub(r("P"), up(s))


EQ = r(" = ")
PLUS = r(" + ")
MINUS = r(" − ")
TIMES = r(" × ")
CDOT = r(" ⋅ ")
