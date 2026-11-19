"""Revision R11 of the concept design report (engineer, 2026-11-19: read it as the reader and the client would): the
charts of the tables-and-charts workbook placed where their tables are (Chapters 7, 8, 14), Appendix D renamed for what
it now holds, and every table and figure of the report tidied: tables centred, their cells centred, their header row
repeated on every page, wide tables in a smaller font; figures centred and kept on the page of their caption.
apply(globals()) is called by build_report.py after r10_edits."""
import os, copy, re
from docx.oxml.ns import qn
from docx.shared import Pt, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
import docx.text.paragraph as P


def apply(g):
    d = g["d"]; body = d.element.body; Out = g["Out"]; IMG = g["IMG"]
    norm = lambda s: re.sub(r"\s+", " ", s.replace("‎", "")).strip()
    Pp = lambda e: P.Paragraph(e, d)

    def caption_para(text):
        hits = [Pp(e) for e in body.iterchildren() if e.tag == qn("w:p") and Pp(e).style is not None and Pp(e).style.name == "Caption" and text in Pp(e).text]
        if not hits: raise KeyError(text)
        return hits[0]

    def after_table(cap_text):
        """An Out placed after the table that follows the caption (and its trailing empty paragraph)."""
        e = caption_para(cap_text)._p.getnext()
        while e is not None and e.tag != qn("w:tbl"): e = e.getnext()
        nxt = e.getnext()
        if nxt is not None and nxt.tag == qn("w:p") and not norm(Pp(nxt).text): nxt = nxt.getnext()
        return Out(nxt)

    after_table("STP Phasing").figure(os.path.join(IMG, "chart_plant_capacity.png"), "Treatment capacity: installed modules and the inflow with its 10 per cent margin")
    after_table("Scenarios Total CAPEX and Cumulative OPEX").figure(os.path.join(IMG, "chart_cost_by_year.png"), "Cumulative CAPEX and OPEX of the scenarios, escalated")
    after_table("Whole-life cost of the scenarios over 25 years").figure(os.path.join(IMG, "chart_whole_life_cost.png"),
                                                                         "Whole-life cost of the scenarios over 25 years, with the line 10 per cent above the lowest")
    for e in body.iterchildren():
        if e.tag == qn("w:p") and Pp(e).style is not None and Pp(e).style.name == "Heading 1" and norm(Pp(e).text).startswith("Appendix D."):
            p = Pp(e); r0 = p.runs[0]
            for r in p.runs[1:]: r._r.getparent().remove(r._r)
            r0.text = "Appendix D. Network Quantities, Station Flows and Depth"; break     # R12: self-cleansing maps moved to Chapter 6

    # ---- every table: centred, cells centred, header repeated; wide tables in a smaller font
    n_t = 0
    for tb in d.tables:
        first = norm(tb.rows[0].cells[0].text) if tb.rows and tb.rows[0].cells else ""
        if not first and len(tb.rows) < 3: continue                       # layout tables of the cover
        tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        tr = tb.rows[0]._tr; trPr = tr.get_or_add_trPr()
        if trPr.find(qn("w:tblHeader")) is None: trPr.append(trPr.makeelement(qn("w:tblHeader"), {}))
        for row in tb.rows:
            rp = row._tr.get_or_add_trPr()
            if rp.find(qn("w:cantSplit")) is None: rp.append(rp.makeelement(qn("w:cantSplit"), {}))
        wide = len(tb.columns) >= 7
        for row in tb.rows:
            for c in row.cells:
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for q in c.paragraphs:
                    q.alignment = 1; q.paragraph_format.space_before = Pt(1); q.paragraph_format.space_after = Pt(1)
                    if wide:
                        for r in q.runs: r.font.size = Pt(8.5)
        tblPr = tb._tbl.tblPr                                              # fit the page width, columns by content
        w = tblPr.find(qn("w:tblW"))
        if w is None: w = tblPr.makeelement(qn("w:tblW"), {}); tblPr.append(w)
        w.set(qn("w:type"), "pct"); w.set(qn("w:w"), "5000")
        lay = tblPr.find(qn("w:tblLayout"))
        if lay is None: lay = tblPr.makeelement(qn("w:tblLayout"), {}); tblPr.append(lay)
        lay.set(qn("w:type"), "autofit")
        n_t += 1
    # ---- a chapter starts on a new page by its own heading, not by a page-break paragraph that can leave a blank page
    n_b = 0
    for e in list(body.iterchildren()):
        if e.tag != qn("w:p") or Pp(e).style is None or Pp(e).style.name != "Heading 1": continue
        prev = e.getprevious()
        if prev is None or prev.tag != qn("w:p") or norm(Pp(prev).text): continue
        brs = [b_ for b_ in prev.iter(qn("w:br")) if b_.get(qn("w:type")) == "page"]
        if not brs: continue
        for b_ in brs:
            r_ = b_.getparent(); r_.remove(b_)
            if not len([x for x in r_ if x.tag != qn("w:rPr")]): r_.getparent().remove(r_)
        has_sect = prev.find(qn("w:pPr")) is not None and prev.find(qn("w:pPr")).find(qn("w:sectPr")) is not None
        if not has_sect: body.remove(prev)
        Pp(e).paragraph_format.page_break_before = True; n_b += 1
    print("chapter page breaks moved to their headings:", n_b)
    # ---- every figure: centred and kept with its caption
    n_f = 0
    for e in body.iter(qn("w:p")):
        if e.findall(".//" + qn("a:blip")) and e.getparent() is body:
            p = Pp(e); p.alignment = 1; p.paragraph_format.keep_with_next = True; n_f += 1
    # ---- the chapter part of the captions added here written as text, as r10_edits does for the rest
    chap_no, label, n_c = 0, "ES", 0
    for e in list(body.iterchildren()):
        if e.tag != qn("w:p"): continue
        p = Pp(e); s = p.style.name if p.style is not None else ""
        if s == "Heading 1":
            t_ = norm(p.text)
            if t_.startswith("Appendix"): label = t_.split()[1].rstrip(".")
            elif t_.upper().startswith("INTRODUCTION") or chap_no: chap_no += 1; label = str(chap_no)
            continue
        if s != "Caption": continue
        runs = list(e.iter(qn("w:r"))); i = 0
        while i < len(runs):
            fc = runs[i].find(qn("w:fldChar"))
            if fc is not None and fc.get(qn("w:fldCharType")) == "begin":
                j = i; instr = ""
                while j < len(runs):
                    instr += "".join(x.text or "" for x in runs[j].iter(qn("w:instrText")))
                    fe = runs[j].find(qn("w:fldChar"))
                    if j > i and fe is not None and fe.get(qn("w:fldCharType")) == "end": break
                    j += 1
                if "STYLEREF" in instr:
                    new = copy.deepcopy(runs[i]); [new.remove(x) for x in list(new) if x.tag != qn("w:rPr")]
                    tt = new.makeelement(qn("w:t"), {}); tt.text = label; new.append(tt); runs[i].addprevious(new)
                    for r in runs[i:j + 1]: r.getparent().remove(r)
                    runs = list(e.iter(qn("w:r"))); i = runs.index(new) + 1; n_c += 1; continue
            i += 1
    # ---- every chapter starts on a new page, its title in the same case as the others
    SMALL = {"and", "of", "the", "for", "to", "in", "on", "at", "a", "an", "or", "by"}
    for p in d.paragraphs:
        if p.style is None or p.style.name != "Heading 1": continue
        p.paragraph_format.page_break_before = True
        t_ = norm(p.text)
        if t_ and t_ == t_.upper() and any(ch.isalpha() for ch in t_) and p.runs:
            words = t_.lower().split()
            p.runs[0].text = " ".join(w if (i and w in SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))
            for r in p.runs[1:]: r.text = ""
    # ---- body text flush with the headings everywhere: the chapters carried two different left indents (0.95 and 1.27 cm)
    n_i = 0
    for p in d.paragraphs:
        if p.style is None or p.style.name != "Normal": continue
        pPr = p._p.find(qn("w:pPr")); ind = pPr.find(qn("w:ind")) if pPr is not None else None
        if ind is None or ind.get(qn("w:hanging")) or ind.get(qn("w:firstLine")): continue
        if (ind.get(qn("w:left")) or ind.get(qn("w:start"))) in ("540", "720"): pPr.remove(ind); n_i += 1
    # ---- table columns sized by their content across the full text width of the page they sit on
    def text_width(sp):
        pg, mg = sp.find(qn("w:pgSz")), sp.find(qn("w:pgMar"))
        return int(pg.get(qn("w:w"))) - int(mg.get(qn("w:left"))) - int(mg.get(qn("w:right")))
    pending, n_w = [], 0
    def size_table(tbl, tw):
        grid = tbl.find(qn("w:tblGrid")); cols = grid.findall(qn("w:gridCol")) if grid is not None else []
        nc = len(cols)
        if nc < 2: return False
        head, data = [""] * nc, [[] for _ in range(nc)]
        for ri, tr in enumerate(tbl.findall(qn("w:tr"))):
            pos = 0
            for tc in tr.findall(qn("w:tc")):
                gs = tc.find(qn("w:tcPr") + "/" + qn("w:gridSpan")); span = int(gs.get(qn("w:val"))) if gs is not None else 1
                tx = norm("".join(x.text or "" for x in tc.iter(qn("w:t"))))
                if tc.find(qn("w:tcPr") + "/" + qn("w:textDirection")) is not None: tx = ""   # rotated text needs height, not width
                if span == 1 and pos < nc:
                    if ri == 0: head[pos] = tx
                    else: data[pos].append(tx)
                pos += span
        wt = []
        for j in range(nc):
            hw = max(max((len(w) for w in head[j].split()), default=0) * 1.1, len(head[j]) / 3.2)   # a header wraps to three lines at most
            dw = max((min(len(x), 36) for x in data[j]), default=0)
            wt.append(max(hw, dw, 5))
        # no column narrower than its longest word (a word never breaks): about 95 twips a character at 8.5 pt, 115 at
        # 10 pt, plus the cell margins; the rest of the width shared by content
        cw = 100 if nc >= 7 else 120
        need = [max((len(w) for x in [head[j]] + data[j] for w in x.split()), default=1) * cw + 250 for j in range(nc)]
        if sum(need) > 0.9 * tw: need = [int(x * 0.9 * tw / sum(need)) for x in need]    # never more than the page holds
        fixed = set()
        while True:
            free = tw - sum(need[j] for j in fixed); rest = [j for j in range(nc) if j not in fixed]
            ws_ = [need[j] if j in fixed else int(free * wt[j] / sum(wt[k] for k in rest)) for j in range(nc)]
            short = [j for j in rest if ws_[j] < need[j]]
            if not short or len(fixed) + len(short) >= nc: break
            fixed |= set(short)
        assert min(ws_) > 0, ('negative column width', ws_)
        for c, w_ in zip(cols, ws_): c.set(qn("w:w"), str(w_))
        for tr in tbl.findall(qn("w:tr")):
            pos = 0
            for tc in tr.findall(qn("w:tc")):
                tcPr = tc.find(qn("w:tcPr"))
                if tcPr is None: tcPr = tc.makeelement(qn("w:tcPr"), {}); tc.insert(0, tcPr)
                gs = tcPr.find(qn("w:gridSpan")); span = int(gs.get(qn("w:val"))) if gs is not None else 1
                tcW = tcPr.find(qn("w:tcW"))
                if tcW is None: tcW = tcPr.makeelement(qn("w:tcW"), {}); tcPr.insert(0, tcW)
                tcW.set(qn("w:w"), str(sum(ws_[pos:pos + span]))); tcW.set(qn("w:type"), "dxa"); pos += span
        tblPr = tbl.find(qn("w:tblPr"))
        for tag in ("w:tblW", "w:tblLayout"):
            if tblPr.find(qn(tag)) is None: tblPr.append(tblPr.makeelement(qn(tag), {}))
        w = tblPr.find(qn("w:tblW")); w.set(qn("w:type"), "dxa"); w.set(qn("w:w"), str(sum(ws_)))
        tblPr.find(qn("w:tblLayout")).set(qn("w:type"), "fixed")
        return True
    for e in body.iterchildren():
        if e.tag == qn("w:tbl"):
            first = norm("".join(x.text or "" for x in e.find(qn("w:tr")).iter(qn("w:t")))) if e.find(qn("w:tr")) is not None else ""
            has_pic = next(e.iter(qn("w:drawing")), None) is not None     # a layout table (the cover's logo and address) keeps its widths:
            if (first or len(e.findall(qn("w:tr"))) >= 3) and not has_pic: pending.append(e)   # resizing it clipped the logo to its cell
            continue
        sp = e.find(qn("w:pPr") + "/" + qn("w:sectPr")) if e.tag == qn("w:p") else (e if e.tag == qn("w:sectPr") else None)
        if sp is not None:
            tw = text_width(sp)
            for tbl in pending: n_w += size_table(tbl, tw)
            pending = []
    print(f"chapters on a new page; {n_i} body paragraphs made flush; {n_w} tables sized by content")
    # ---- every caption in one form, "Table 8-1. Title" in the caption style: 36 carried a bare space and their own font size
    n_k = 0
    for p in d.paragraphs:
        if p.style is None or p.style.name != "Caption": continue
        runs = p._p.findall(qn("w:r")); ends = [i for i, r in enumerate(runs) if r.find(qn("w:fldChar")) is not None and r.find(qn("w:fldChar")).get(qn("w:fldCharType")) == "end"]
        if not ends: continue
        tail = runs[ends[0] + 1:]
        if not tail or any(r.find(qn("w:fldChar")) is not None or r.find(qn("w:footnoteReference")) is not None for r in tail): continue
        txt = "".join(x.text or "" for r in tail for x in r.iter(qn("w:t")))
        if txt.startswith(". ") and not any(r.find(qn("w:rPr")) is not None and r.find(qn("w:rPr")).find(qn("w:sz")) is not None for r in tail): continue
        keep = tail[0]
        for r in tail[1:]: r.getparent().remove(r)
        for x in list(keep):
            if x.tag != qn("w:t"): keep.remove(x)
        ts = keep.findall(qn("w:t"))
        if not ts: ts = [keep.makeelement(qn("w:t"), {})]; keep.append(ts[0])
        for x in ts[1:]: keep.remove(x)
        ts[0].text = ". " + re.sub(r"\s+", " ", txt.lstrip(" .:-–\t")).strip(); ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        n_k += 1
    print("captions made uniform:", n_k)
    # ---- typed cross-references that point at the wrong place (checked against the table of contents, 2026-11-19)
    cells = [q for tb in d.tables for row in tb.rows for c in row.cells for q in c.paragraphs]
    FIX = [(lambda t: "Merrimack peak of the average flow" in t, "4.2.6", "4.8.4"),               # 4.8.4 Peak Flow
           (lambda t: "Hydrogen sulphide control: dosing" in t, "6.6.3", "3.5"),                 # 3.5 force main criteria
           (lambda t: norm(t) == "Section 7.5", "Section 7.5", "Sections 3.5 and 11.1")]         # power supply, App A
    for test, old, new in FIX:
        hit = 0
        for q in list(d.paragraphs) + cells:
            if not test(q.text): continue
            for r in q.runs:
                if old in r.text: r.text = r.text.replace(old, new); hit += 1; break
        assert hit >= 1, ("reference not found", old)
    print("cross-references corrected:", len(FIX))
    # ---- R12 review (2026-11-19): references whose target moved, and two statements the twelve designs made incomplete
    XS_ = "{http://www.w3.org/XML/1998/namespace}space"

    def set_text(p, text):                                     # as in r10_edits: first run's format kept, footnote references kept
        pp = p._p; rpr = None
        for r in pp.iter(qn("w:r")):
            if r.find(qn("w:t")) is not None and r.find(qn("w:fldChar")) is None and r.find(qn("w:rPr")) is not None:
                rpr = copy.deepcopy(r.find(qn("w:rPr"))); break
        notes = [copy.deepcopy(r) for r in pp.iter(qn("w:r")) if r.find(qn("w:footnoteReference")) is not None]
        for ch in list(pp):
            if ch.tag not in (qn("w:pPr"), qn("w:bookmarkStart"), qn("w:bookmarkEnd")): pp.remove(ch)
        r = pp.makeelement(qn("w:r"), {})
        if rpr is not None: r.append(rpr)
        t = r.makeelement(qn("w:t"), {}); t.text = text; t.set(XS_, "preserve"); r.append(t); pp.append(r)
        for nn in notes: pp.append(nn)

    def sub_text(pred, pairs, n=1):
        hit = 0
        for q in list(d.paragraphs) + cells:
            if q.style is not None and q.style.name.upper().startswith(("TOC", "TABLE OF")): continue
            t = norm(q.text)
            if not pred(t): continue
            for a, b in pairs:
                assert a in t, (a, t[:140]); t = t.replace(a, b)
            set_text(q, t); hit += 1
        assert hit == n, (pairs[0], hit, n)
    import json as _j
    DYC_ = _j.load(open(os.path.join(g["F"].R, "design_year_check_2056.json")))
    po = [DYC_[f"{s}-2051"]["pipes_over"] for s in ("SC1", "SC2", "SC3", "SC4")]
    sub_text(lambda t: "to spare in 2056 (Section 6.2.6)" in t, [("(Section 6.2.6)", "(Section 6.2.7)")])         # TE demands moved to 6.2.7 in R11
    sub_text(lambda t: "exceeds demand by about" in t and "(Section 6.2.6)" in t, [("(Section 6.2.6)", "(Section 6.2.7)")])
    sub_text(lambda t: t in ("Section 6.2.6", "Section 6.2.6; Chapter 10"), [("6.2.6", "6.2.7")], n=3)              # Appendix A items 13, 16, 21
    sub_text(lambda t: t == "4.10, 6.2.6", [("6.2.6", "6.2.7")])                                                     # Appendix B item A15
    sub_text(lambda t: t.startswith("The prevailing winds described in Section 1.3.5"), [("Section 1.3.5", "Section 1.3.6")])   # winds: 1.3.6 Climate
    sub_text(lambda t: "adds staff and land rent every year (Sections 8.8 and 14.5)" in t, [("Sections 8.8 and 14.5", "Sections 8.9 and 14.5")])  # 8.8 inserted in R12
    sub_text(lambda t: "and are built in modules to 44,000 m³/d." in t,
             [("and are built in modules to 44,000 m³/d.", "and are built in modules to 44,000 m³/d in one plant or 45,000 m³/d in two.")])
    sub_text(lambda t: t.startswith("Four scenarios have been designed and modelled in SewerGEMS.") and "The network of each is designed for 2056, with" in t,
             [("The network of each is designed for 2056, with",
               f"Each scenario has been designed for the flows of 2051, 2056 and 2061 (Chapter 6), and the 2056 design is adopted in all four: a "
               f"2051 design leaves {min(po)} to {max(po)} pipes above their depth limit by 2056, and a 2061 design costs more and leaves more sewer "
               "below the self-cleansing velocity in the early years. The 2056 designs have")])
    es_ref = next(q for q in d.paragraphs if norm(q.text) == "Matters Requiring Attention in Every Scenario")
    es_bad = next(q for q in d.paragraphs if norm(q.text) == "Treatment Plant, Treated Effluent and Sludge" and q.style.name == "List Paragraph")
    old_pPr = es_bad._p.find(qn("w:pPr")); new_pPr = copy.deepcopy(es_ref._p.find(qn("w:pPr")))
    if old_pPr is not None: es_bad._p.remove(old_pPr)
    es_bad._p.insert(0, new_pPr)                               # the executive summary subheading in the style of its neighbours
    # the flow the network does not yet carry, said where a reader of the network looks for it (engineer, 2026-11-19); the figures are
    # read from Section 7.3.1, which the reconciliation of r10_edits writes, so the two cannot differ
    p731 = next(norm(q.text) for q in d.paragraphs if norm(q.text).startswith("The inflow excludes the plots not yet conveyed by the network"))
    q31, q56 = re.search(r"([\d,]+) m³/d in 2031 and ([\d,]+) m³/d in 2056", p731).groups()
    sub_text(lambda t: t.startswith("Each plot carries the flow of its population and use in each year.") and t.endswith("enters the network at its nearest manhole."),
             [("enters the network at its nearest manhole.",
               "enters the network at its nearest manhole. Two groups of plots are not yet conveyed: plots in planted areas, where the ground "
               "levels of the terrain model are unreliable under the trees until the survey, and plots more than 200 m from a sewer. They "
               f"generate {q31} m³/d in 2031 and {q56} m³/d in 2056 (Section 7.3.1; by settlement in Appendix C.3) and are connected at the "
               "preliminary design, within the 10 per cent margin of the plant capacity.")])
    n_dt = 0                                                   # the cover carries the month of this revision
    for t_ in list(body)[0].iter(qn("w:t")):
        if "October 2026" in (t_.text or ""): t_.text = t_.text.replace("October 2026", "November 2026"); n_dt += 1
    assert n_dt in (1, 2), ("cover date", n_dt)                # the text box and its fallback copy for older readers
    print("R12 review fixes applied: 6 references, 2 statements, 1 subheading, cover date")
    # ---- the team's agreed term is property, never dwelling (engineer, 2026-11-19); the clean gate now rejects it
    n_d = 0
    for q in list(d.paragraphs) + cells:
        for r in q.runs:
            if re.search(r"[Dd]welling", r.text):
                t0 = r.text.replace("to dwellings, mosques", "to residential properties, mosques")
                t0 = re.sub(r"([Dd])wellings", lambda m: "Properties" if m.group(1) == "D" else "properties", t0)
                r.text = re.sub(r"([Dd])welling", lambda m: "Property" if m.group(1) == "D" else "property", t0); n_d += 1
    print("dwelling -> property:", n_d)
    # ---- no blank pages: an empty paragraph after a full page (a long table, the end of a chapter) is pushed onto a page
    # of its own, before the section break or the heading that starts the next page. Drop those empty paragraphs and
    # make the paragraph that carries a section break 1 pt high so it always fits on the page above it.
    def bare(e):
        if e is None or e.tag != qn("w:p"): return False
        if norm("".join(x.text or "" for x in e.iter(qn("w:t")))): return False
        if e.findall(".//" + qn("a:blip")) or list(e.iter(qn("w:br"))) or list(e.iter(qn("w:fldChar"))): return False
        pPr = e.find(qn("w:pPr"))
        return not (pPr is not None and (pPr.find(qn("w:sectPr")) is not None or pPr.find(qn("w:pageBreakBefore")) is not None))
    n_e = n_s = 0
    for e in list(body.iterchildren()):
        if e.tag != qn("w:p"): continue
        pPr = e.find(qn("w:pPr"))
        if pPr is None: continue
        is_sect = pPr.find(qn("w:sectPr")) is not None
        if not (is_sect or pPr.find(qn("w:pageBreakBefore")) is not None): continue
        while bare(e.getprevious()): body.remove(e.getprevious()); n_e += 1
        if is_sect and not norm(Pp(e).text) and not e.findall(".//" + qn("a:blip")):
            pf = Pp(e).paragraph_format; pf.space_before = Pt(0); pf.space_after = Pt(0); pf.line_spacing = Pt(1)
            rPr = pPr.find(qn("w:rPr"))
            if rPr is None: rPr = pPr.makeelement(qn("w:rPr"), {}); pPr.append(rPr)
            for tag in ("w:sz", "w:szCs"):
                s_ = rPr.find(qn(tag))
                if s_ is None: s_ = rPr.makeelement(qn(tag), {}); rPr.append(s_)
                s_.set(qn("w:val"), "2")
            n_s += 1
    print(f"blank-page guard: {n_e} empty paragraphs removed, {n_s} section breaks made 1 pt")
    print(f"R11 edits applied: {n_t} tables tidied, {n_f} figures centred, {n_c} new captions numbered")
