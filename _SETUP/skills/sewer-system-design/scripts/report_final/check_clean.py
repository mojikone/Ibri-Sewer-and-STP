"""The clean-room gate for client reports: nothing internal reaches the reader, and a scan proves it, not a reading.

Scans the RENDERED text of a report (a PDF through PyMuPDF, every page incl. headers, footers and footnotes; or a .docx
incl. tables, headers, footers and footnotes) against the built-in list of internal matter plus the project's own list,
blanks the project's allowed terms first, and exits 1 on any hit. Wire it into the report build so that a hit fails
the build; never issue a report that has not passed it.

    python check_clean.py <report.pdf|report.docx> [--terms forbidden_terms.txt] [--allow allowed_terms.txt] [--quiet]

Term files: one regular expression per line, '#' starts a comment, blank lines ignored. The project list EXTENDS the
built-in one; put every internal name there on day one (model and scenario names, iteration and revision tags, job codes,
working names that were later renamed, other projects used as sources of templates or text, internal parties) and add
each new one the moment it appears. Allowed terms are regexes whose matches are blanked before the scan (data-source
names the report legitimately cites, symbols that look like tags, e.g. the unit weight W1 in an equation's symbol list).
"""
import sys, re, os, zipfile

DEFAULT_TERMS = r"""
# ---- iteration and revision tags of the working folders (the client sees "Rev 00" on the cover, never W3 or R2)
\bW\d{1,2}\b
\bR\d{1,2}\b
# ---- paths, files, folders, code
[A-Za-z]:\\
\\\\[A-Za-z]
(?i)\b[\w.-]+\.(xlsx|xlsm|xls|csv|py|ipynb|qgz|qgs|qml|shp|gpkg|docx|doc|dss|tif|tiff|json|kmz|kml|dwg|dxf|rar|zip|txt|md|log|bat|ps1|exe|sqlite|basin|met|hms)\b
\bREADME\b
\bscripts?\b
\bPython\b|\bpython-docx\b|\bopenpyxl\b|\bmatplotlib\b|\bPyQGIS\b|\bgeopandas\b
\bGitHub\b|\bgithub\b|\brepo(sitory)?\b
# ---- the machine, the people, the process
\bClaude\b|\bChatGPT\b|\bLLM\b
\bwe (decided|tried|fixed|changed|noticed|realised|realized|assumed earlier|had to)\b
\bbug\b|\bworkaround\b|\bhack\b|\bincident\b|\bcrash(ed)?\b
\binternal (discussion|note|use|review|comment|matter|file|folder|name|version|revision|draft|workbook|model)s?\b|\binternally\b
\b(the|our) (engineer|modeller|modeler|hydrologist|dam team|design team|dam design team|team lead) (asked|said|requested|wants|instructed|decided|prefers)\b
\bas (requested|instructed|discussed|agreed) (by|with|in)\b
\bper (the |his |her )?(comment|instruction|request)s?\b
\b(his|her|the engineer's) comments?\b
\bnot (yet )?(provided|received|available) (by|from) the\b
# ---- unfinished matter and placeholders
\bTBD\b|\bTBC\b|\bTODO\b|\bFIXME\b|\bXXX\b|\?\?
\bplaceholder\b|\blorem\b|\bipsum\b
\bto be (provided|confirmed|added|completed|updated|checked|decided)\b
\bnext (revision|issue|version)\b|\bin (a|the) (later|next|future) (revision|issue|version)\b|\bwill be (added|provided|included) (later|in)\b
\bnil\b|\bN/A\b|\bn\.a\.\b
Table \?|Figure \?|Section \?|Appendix \?|\[\s*\]|\[(ref|cite|number|value|x+)\]
"""

def load_terms(path):
    out = []
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"): out.append(line)
    return out

def text_of(path):
    """(location, text) chunks of the rendered report"""
    if path.lower().endswith(".pdf"):
        import fitz
        doc = fitz.open(path); return [(f"p{i + 1}", doc[i].get_text()) for i in range(len(doc))]
    if path.lower().endswith(".docx"):
        z = zipfile.ZipFile(path); chunks = []
        for name in z.namelist():
            if name.startswith("word/") and name.endswith(".xml") and any(k in name for k in ("document", "header", "footer", "footnotes", "endnotes", "comments")):
                xml = z.read(name).decode("utf-8", "replace")
                paras = re.split(r"</w:p>", xml); txt = "\n".join(re.sub(r"<[^>]+>", "", p) for p in paras)
                chunks.append((name.split("/")[-1], txt))
        return chunks
    raise SystemExit("give a .pdf or a .docx")

def scan(path, terms_file=None, allow_file=None):
    terms = [t for t in DEFAULT_TERMS.splitlines() if t.strip() and not t.strip().startswith("#")] + load_terms(terms_file)
    allow = load_terms(allow_file); hits = []
    for where, txt in text_of(path):
        for a in allow: txt = re.sub(a, lambda m: " " * len(m.group(0)), txt)
        for t in terms:
            for m in re.finditer(t, txt):
                ctx = txt[max(0, m.start() - 45): m.end() + 45].replace("\n", " ")
                hits.append((where, m.group(0), ctx.strip(), t))
    return hits

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    path = a[0]; terms = a[a.index("--terms") + 1] if "--terms" in a else None; allow = a[a.index("--allow") + 1] if "--allow" in a else None
    hits = scan(path, terms, allow); enc = lambda s: s.encode("ascii", "replace").decode()
    if "--quiet" not in a:
        for where, hit, ctx, t in hits: print(f"  {where:>8}  [{enc(hit)}]  ...{enc(ctx)}...")
    print(f"clean-room gate: {'PASSED' if not hits else 'FAILED, ' + str(len(hits)) + ' hit(s)'}  ({os.path.basename(path)})")
    sys.exit(1 if hits else 0)

if __name__ == "__main__":
    main()
