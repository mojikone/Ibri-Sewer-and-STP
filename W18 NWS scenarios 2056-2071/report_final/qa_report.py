"""Quality checks of a built report, run after word_finish.py and check_clean.py (R11-R12, 2026-11-19). Every check here found
a real fault in this report at least once; none of them replaces looking at the rendered pages.

    python qa_report.py R12/Ibri_Concept_Design_Report_R12.pdf [--docx R12/...docx] [--topics] [--sheets OUTDIR]

PDF checks:
  - near-empty pages (under 40 characters of body text and no image): blank pages from a spilled empty paragraph or section break
  - a figure caption at the top of a page with no image on it: caption separated from its figure
  - footer missing on any page but the cover ('Concept Design Report' in the bottom 12 %): a section that took the cover's blank
    first-page footer
  - stale wording: option names, 'Error!', TBD, dwelling and anything added to STALE below
Word checks (--docx):
  - caption sequences broken (Table 6-1, 6-2, ... with no gap or repeat)
  - 'Table x-y' / 'Figure x-y' cited in the text with no such caption
  - 'Section n.n' cited with no such heading (guideline and ToR sections skipped); with --topics, every reference is listed with the
    title of its target so a reader can see whether it points at the right subject
  - table columns narrower than 0.8 cm or negative (letter-by-letter text)
--sheets OUTDIR writes contact sheets of every page (40 a sheet) to look at the layout by eye.
Exit code 1 when any check fails."""
import argparse, collections, os, re, sys
import fitz

STALE = [r"\bOP\s?\d\b", r"\bOption\s\d\b", r"Error!", r"\bTBD\b", r"[Dd]welling"]


def pdf_checks(pdf, sheets=None):
    doc = fitz.open(pdf); bad = 0; empty, capnext, nofoot = [], [], []
    for i, pg in enumerate(doc):
        h = pg.rect.height
        body = [b for b in pg.get_text("blocks") if b[1] > 0.09 * h and b[3] < 0.90 * h]
        txt = " ".join(b[4] for b in body).strip(); imgs = pg.get_images()
        if len(txt) < 40 and not imgs: empty.append(i + 1)
        first = sorted(body, key=lambda b: b[1])[:1]
        if first and re.match(r"Figure [A-Z0-9]+-\d+", first[0][4].strip()) and not imgs: capnext.append(i + 1)
        if i and "Concept Design Report" not in " ".join(b[4] for b in pg.get_text("blocks") if b[1] > 0.88 * h): nofoot.append(i + 1)
    print(f"pages {len(doc)} | near-empty {empty} | figure caption without its figure {capnext} | footer missing {nofoot}")
    bad += bool(empty) + bool(capnext) + bool(nofoot)
    text = re.sub(r"\s+", " ", " ".join(p.get_text() for p in doc))
    for pat in STALE:
        hits = [text[max(0, m.start() - 50):m.end() + 40] for m in re.finditer(pat, text)]
        if hits: print(f"stale wording {pat}: {len(hits)}", hits[:3]); bad += 1
    if sheets:
        from PIL import Image
        os.makedirs(sheets, exist_ok=True); W, H = 230, 325
        for s in range(0, len(doc), 40):
            pages = list(range(s, min(s + 40, len(doc)))); rows = (len(pages) + 7) // 8
            sheet = Image.new("RGB", (8 * W, rows * H), "white")
            for k, i in enumerate(pages):
                pg = doc[i]; z = min(W / pg.rect.width, H / pg.rect.height); pm = pg.get_pixmap(matrix=fitz.Matrix(z, z))
                sheet.paste(Image.frombytes("RGB", (pm.width, pm.height), pm.samples), ((k % 8) * W, (k // 8) * H))
            out = os.path.join(sheets, f"sheet_{s + 1:03d}.png"); sheet.save(out); print("contact sheet", out)
    return bad


def docx_checks(path, topics=False):
    import docx
    from docx.oxml.ns import qn
    d = docx.Document(path); bad = 0
    toc = {}
    for p in d.paragraphs:
        if p.style.name.upper().startswith("TOC"):
            parts = [x for x in p.text.split("\t") if x.strip()]
            if len(parts) >= 2: toc[parts[0].strip().rstrip(".")] = parts[1].strip()
    caps = collections.OrderedDict()
    for p in d.paragraphs:
        if p.style.name == "Caption":
            m = re.match(r"^(Table|Figure)\s+([A-Z0-9]+)-(\d+)\.", p.text.strip())
            if m: caps.setdefault((m.group(1), m.group(2)), []).append(int(m.group(3)))
    broken = {k: v for k, v in caps.items() if v != list(range(1, len(v) + 1))}
    print("caption sequences broken:", broken or "none"); bad += bool(broken)
    have = {(k[0], f"{k[1]}-{n}") for k, v in caps.items() for n in v}
    src = [p.text for p in d.paragraphs if not p.style.name.upper().startswith(("TOC", "TABLE OF")) and p.style.name != "Caption"]
    src += [c.text for t in d.tables for r in t.rows for c in r.cells]
    text = "\n".join(src)
    miss = sorted({m.group(0) for m in re.finditer(r"\b(Table|Figure)s?\s+([A-Z0-9]+-\d+)", text) if (m.group(1), m.group(2)) not in have})
    print("tables/figures cited with no caption:", miss or "none"); bad += bool(miss)
    secmiss, listed = collections.Counter(), set()
    for t in src:
        for m in re.finditer(r"Sections?\s+((?:\d+|[A-H])(?:\.\d+)+)", t):
            pre = t[max(0, m.start() - 30):m.start()]
            if re.search(r"GUD|PAM|ToR|BS |EN |ISO|\b20[13]\s*$", pre) or re.match(r"^, pp?\.", t[m.end():m.end() + 5]): continue
            n = m.group(1)
            if n not in toc and n.count(".") < 3: secmiss[n] += 1
            if topics and (n, t[:60]) not in listed:
                listed.add((n, t[:60])); print(f"  {n:<9} -> {toc.get(n, '?')[:45]:<45} || ...{t[max(0, m.start() - 80):m.start()]}")
    print("sections cited with no such heading:", dict(secmiss) or "none"); bad += bool(secmiss)
    narrow = []
    for i, tb in enumerate(d.tables):
        g = tb._tbl.find(qn("w:tblGrid"))
        if g is None: continue
        w = [int(x.get(qn("w:w"))) for x in g.findall(qn("w:gridCol"))]
        if w and min(w) < 340: narrow.append((i, [c.text.strip()[:12] for c in tb.rows[0].cells][:3], min(w)))
    print("tables with a column under 0.6 cm or negative:", narrow or "none"); bad += bool(narrow)
    return bad


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("pdf"); a.add_argument("--docx"); a.add_argument("--topics", action="store_true"); a.add_argument("--sheets")
    o = a.parse_args()
    n = pdf_checks(o.pdf, o.sheets) + (docx_checks(o.docx, o.topics) if o.docx else 0)
    print("QA:", "PASSED" if not n else f"{n} check(s) failed"); sys.exit(1 if n else 0)
