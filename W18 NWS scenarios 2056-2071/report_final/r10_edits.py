"""Revision R10 of the concept design report: every part of the team's text that still described the seven options or
the 2030-2070 flows is brought to the four scenarios and the 2056 design (engineer, 2026-11-18: "review the entire report
and update all parts"; the team's chapters rewritten; STP, TE and operating costs updated from the flows; TE customers
checked for each scenario; SC4's TE network written like SC1-SC3).
  Executive summary   rewritten on the current basis (population of Chapter 4, plant inflows, decisions, scenarios,
                      appraisal, recommendation);
  Chapters 5, 7, 8    existing plant and master plan, STP inflows and module phasing, financial analysis of SC1-SC4 by the
                      team's method (py/final_financial.py -> financial.json);
  Chapters 9 to 17    the option references, numbers and internal review notes; Chapter 14 (life-cycle cost and
                      appraisal) and Chapter 17 (conclusions, recommendations, decisions) rewritten;
  Appendices          compliance matrix references, adopted values, settlement tables, cost basis, drawing register;
  Captions            the chapter part of every caption number written as text (Word's STYLEREF gave 1 and 7 in places;
                      appendix letters A-H, ES in the executive summary), the typed TE captions made real captions.
apply(globals()) is called by build_report.py after its own edits."""
import os, json, copy, math, re
import pandas as pd, geopandas as gpd
from docx.oxml.ns import qn
import docx.text.paragraph as P

XS = "{http://www.w3.org/XML/1998/namespace}space"


def apply(g):
    d = g["d"]; body = d.element.body; Out = g["Out"]; F = g["F"]; C = g["C"]; Y = g["Y"]
    f0, f1 = g["f0"], g["f1"]; remove, section, level = g["remove"], g["section"], g["level"]
    IMG, SECT_A4, SECT_A3 = g["IMG"], g["SECT_A4"], g["SECT_A3"]
    fin = json.load(open(os.path.join(F.R, "financial.json")))
    SC = list(F.SCEN); M = lambda v: f"{v / 1e6:,.1f}"; M2 = lambda v: f"{v / 1e6:,.2f}"

    # ------------------------------------------------------------------ helpers
    Pp = lambda e: P.Paragraph(e, d)
    norm = lambda s: re.sub(r"\s+", " ", s.replace("‎", "").replace(" ", " ")).strip()
    def is_list(e):                                                   # an entry of the contents or of a list of figures/tables
        s = Pp(e).style; n = (s.name if s is not None else "").lower().replace(" ", "")
        return n.startswith("toc") or n.startswith("tableoffigures")
    top = lambda: [Pp(e) for e in body.iterchildren() if e.tag == qn("w:p") and not is_list(e)]

    def para(start, nth=0, style=None, within=None):
        src = within if within is not None else top()
        hits = [p for p in src if norm(p.text).startswith(norm(start)) and (style is None or (p.style is not None and p.style.name.startswith(style)))]
        if len(hits) <= nth: raise KeyError(f"paragraph not found: {start!r}")
        return hits[nth]

    def has(text, nth=0):
        hits = [p for p in (Pp(e) for e in body.iter(qn("w:p")) if not is_list(e)) if norm(text) in norm(p.text)]
        if len(hits) <= nth: raise KeyError(f"no paragraph contains: {text!r}")
        return hits[nth]

    def number_map():
        """Bookmark -> (heading number, heading text) and bookmark -> caption label, in the document's present order."""
        heads, capl = {}, {}; h = [0, 0, 0, 0]; started = False; appendix = None; seq = {}; label = "ES"
        for e in body.iterchildren():
            if e.tag != qn("w:p"): continue
            p = Pp(e); s = p.style.name if p.style is not None else ""; t = norm(p.text)
            marks = [b.get(qn("w:name")) for b in e.iter(qn("w:bookmarkStart"))]
            m = re.match(r"Heading (\d)$", s)
            if m:
                lv = int(m.group(1)); num = None
                if lv == 1:
                    seq = {}
                    if t.startswith("Appendix"): appendix = label = t.split()[1].rstrip(".")
                    elif t.upper().startswith("INTRODUCTION") or started:
                        started = True; h = [h[0] + 1, 0, 0, 0]; label = num = str(h[0])
                elif started and appendix is None:
                    h[lv - 1] += 1; h[lv:] = [0] * (4 - lv); num = ".".join(str(x) for x in h[:lv])
                for b in marks: heads[b] = (num, t)
            elif s == "Caption":
                instr = " ".join(x.text or "" for x in e.iter(qn("w:instrText"))) + " ".join(x.get(qn("w:instr")) or "" for x in e.iter(qn("w:fldSimple")))
                k = re.search(r"SEQ (\w+)", instr)
                if k:
                    seq[k.group(1)] = seq.get(k.group(1), 0) + 1
                    for b in marks: capl[b] = f"{k.group(1)} {label}-{seq[k.group(1)]}"
        return heads, capl

    def literal_refs():
        """Every REF field written as the current number of its target heading or caption (or its last text if the target is gone)."""
        heads, capl = number_map(); n = 0
        for e in list(body.iter(qn("w:p"))):
            runs = list(e.iter(qn("w:r"))); i = 0
            while i < len(runs):
                fc = runs[i].find(qn("w:fldChar"))
                if fc is not None and fc.get(qn("w:fldCharType")) == "begin":
                    j = i + 1; instr = ""; depth = 1; sep = None
                    while j < len(runs):
                        f2 = runs[j].find(qn("w:fldChar"))
                        if f2 is not None:
                            ty = f2.get(qn("w:fldCharType"))
                            if ty == "begin": depth += 1
                            elif ty == "separate" and depth == 1: sep = j
                            elif ty == "end":
                                depth -= 1
                                if depth == 0: break
                        elif depth == 1 and sep is None: instr += "".join(x.text or "" for x in runs[j].iter(qn("w:instrText")))
                        j += 1
                    parts = instr.split()
                    if parts and parts[0] == "REF" and len(parts) > 1 and j < len(runs):
                        bm = parts[1]; res = runs[(sep if sep is not None else j) + 1:j]
                        cached = "".join(x.text or "" for r in res for x in r.iter(qn("w:t")))
                        if bm in heads and heads[bm][0]: txt = heads[bm][0] if any(s_ in parts for s_ in ("\\r", "\\n", "\\w")) else heads[bm][1]
                        elif bm in capl: txt = capl[bm]
                        else: txt = cached
                        src = next((r for r in res if r.find(qn("w:t")) is not None), runs[i])
                        new = copy.deepcopy(src); [new.remove(x) for x in list(new) if x.tag != qn("w:rPr")]
                        tt = new.makeelement(qn("w:t"), {}); tt.text = txt; tt.set(XS, "preserve"); new.append(tt)
                        runs[i].addprevious(new)
                        for r in runs[i:j + 1]: r.getparent().remove(r)
                        runs = list(e.iter(qn("w:r"))); i = runs.index(new) + 1; n += 1; continue
                i += 1
        return n

    def set_text(p, text):
        pp = p._p; rpr = None
        for r in pp.iter(qn("w:r")):
            if r.find(qn("w:t")) is not None and r.find(qn("w:fldChar")) is None and r.find(qn("w:instrText")) is None and r.find(qn("w:rPr")) is not None:
                rpr = copy.deepcopy(r.find(qn("w:rPr"))); break
        notes = [copy.deepcopy(r) for r in pp.iter(qn("w:r")) if r.find(qn("w:footnoteReference")) is not None]
        for ch in list(pp):
            if ch.tag not in (qn("w:pPr"), qn("w:bookmarkStart"), qn("w:bookmarkEnd")): pp.remove(ch)
        r = pp.makeelement(qn("w:r"), {})
        if rpr is not None:
            for v in rpr.findall(qn("w:vertAlign")): rpr.remove(v)
            r.append(rpr)
        t = r.makeelement(qn("w:t"), {}); t.text = text; t.set(XS, "preserve"); r.append(t); pp.append(r)
        for n in notes: pp.append(n)
        return p

    def set_lead(p, lead, rest):
        set_text(p, lead); r0 = p._p.findall(qn("w:r"))[0]; r = copy.deepcopy(r0)
        rp = r.find(qn("w:rPr"))
        if rp is not None:
            for b in rp.findall(qn("w:b")) + rp.findall(qn("w:bCs")): rp.remove(b)
        r.find(qn("w:t")).text = " " + rest; r0.addnext(r)

    def sub(p, *pairs):
        t = norm(p.text)
        for a, b in pairs:
            if a not in t: raise KeyError(f"{a!r} not in: {t[:150]!r}")
            t = t.replace(a, b)
        return set_text(p, t)

    def chap(title):
        """The top-level elements of a chapter (Heading 1 to the next Heading 1)."""
        h = para(title, style="Heading 1"); out = [h._p]; e = h._p.getnext()
        while e is not None and level(e) != 1 and e.tag != qn("w:sectPr"): out.append(e); e = e.getnext()
        return out

    def in_chap(title):
        return [Pp(e) for e in chap(title) if e.tag == qn("w:p")]

    def head(title, text, style="Heading"):
        return para(text, style=style, within=in_chap(title))

    def clear_after(hp):
        """Remove a heading's body (to the next heading of the same or higher level) and return an Out before what follows."""
        els = section(hp)[1:]; nxt = (els[-1] if els else hp._p).getnext(); remove(els); return Out(nxt)

    def next_tbl(p):
        e = p._p.getnext()
        while e is not None and e.tag != qn("w:tbl"): e = e.getnext()
        return e

    def replace_table(cap, head_row, rows, widths=None):
        t = next_tbl(cap); o = Out(t); o.table(head_row, rows, widths); remove([t])

    def caption_text(p, text):
        runs = p._p.findall(qn("w:r")); ends = [i for i, r in enumerate(runs) if r.find(qn("w:fldChar")) is not None and r.find(qn("w:fldChar")).get(qn("w:fldCharType")) == "end"]
        for r in runs[ends[-1] + 1:]: p._p.remove(r)
        r = copy.deepcopy(runs[0]); [r.remove(x) for x in list(r) if x.tag != qn("w:rPr")]
        t = r.makeelement(qn("w:t"), {}); t.text = ".   " + text; t.set(XS, "preserve"); r.append(t); p._p.append(r)

    def cell_set(tb, first, col, text):
        for row in tb.rows:
            if norm(row.cells[0].text) == first:
                c = row.cells[col]; set_text(c.paragraphs[0], text)
                for q in c.paragraphs[1:]: q._p.getparent().remove(q._p)
                return
        raise KeyError(first)

    def table_with(text):
        for tb in d.tables:
            if any(norm(text) in norm(c.text) for c in tb.rows[0].cells): return tb
        raise KeyError(text)

    print("cross-references written as their current numbers:", literal_refs())

    # ------------------------------------------------------------------ facts of this revision
    POP = {2026: 119259, 2031: 133121, 2036: 148512, 2041: 165698, 2046: 183599, 2051: 203866, 2056: 226301, 2061: 251204, 2071: 309535}  # Table 4-8
    T413 = {2031: 23867, 2036: 26499, 2041: 29438, 2046: 32500, 2051: 35966, 2056: 39803, 2061: 44062, 2071: 54038}             # Table 4-13
    loads = pd.read_csv(os.path.join(F.W18, "results", "loads", "manhole_loads.csv"))
    carried = {y: float(loads[f"Q_{y}"].sum()) for y in T413 if f"Q_{y}" in loads}
    EST, INF_T, INF_N = 316.0, 1099.0, 1078.6                         # estates; Table 4-13's allowance (1,520 km); modelled 1,498 km
    notc = {y: T413[y] + EST - INF_T - carried[y] for y in (2031, 2036, 2041, 2046, 2051, 2056, 2061)}
    inflow = {int(y): v for y, v in fin["SC1"]["inflow"].items()}
    for y in notc:                                                    # the reconciliation closes on the plant inflow
        assert notc[y] > 0 and abs(carried[y] + INF_N - inflow[y]) < 2, (y, carried[y], inflow[y])
    TEdel = {y: 0.855 * inflow[y] for y in inflow}
    ten = lambda v: f"{round(v, -2):,.0f}"
    s1 = fin["SC1"]; pv = {sc: fin[sc]["pv_total"] for sc in SC}; lo_pv = min(pv, key=pv.get)
    tot = {sc: fin[sc]["total_2055"] for sc in SC}; lo_t = min(tot, key=tot.get)
    above = lambda dct, sc: "–" if sc == min(dct, key=dct.get) else f"+{(dct[sc] / min(dct.values()) - 1) * 100:.1f} %"
    cap_txt = lambda sc: " and ".join(f"{p} {f0(m['total'])} m³/d" for p, m in fin[sc]["plants"].items())
    mwh = {sc: C[sc]["mwh_design"] for sc in SC}
    plant_km = {}
    for sc in SC:
        pk = gpd.read_file(os.path.join(F.R, f"{sc}-{F.BASE}", "products", "map.gpkg"), layer="pipes")
        plant_km[sc] = (pk.groupby("stp").geometry.apply(lambda s: s.length.sum()) / 1000).to_dict()
    deep6 = {sc: sum(v for b, v in C[sc]["km_by_depth"].items() if b in ("6 to 9 m", "9 to 12 m", "12 to 15 m", "over 15 m")) for sc in SC}
    p14 = C["SC1"]["stations"].set_index("name").loc["P14"]
    te_out = 1020                                                     # six customers beyond the mains, 2070 demand (te_customers.csv)

    # ================================================================== EXECUTIVE SUMMARY
    sub(para("This report presents the concept design for the wastewater collection"),
        ("develops and appraises the options, and recommends the option to be taken forward", "develops and appraises four scenarios, and recommends the scenario to be taken forward"))
    set_text(para("Wastewater generation is derived from water demand in accordance with PAM-GUD-201"),
             "Wastewater generation is derived from water demand in accordance with PAM-GUD-201. For Adh Dhahirah, domestic consumption is "
             "164 L/capita/day, with 22 per cent added for non-domestic and 14 per cent for governmental consumption; return-to-sewer ratios "
             "are 85 per cent for domestic supply and 54 per cent for other categories (PAM-GUD-201, Table 11, p. 60; Table 19, p. 71), about "
             "171 L per person per day. The population is the arithmetic mean of three projections, from the NCSI forecasts, the electricity "
             "accounts and the APSR-approved Master Plan, with 4.8 persons per residential property. Sewers are laid at the minimum gradients of "
             "PAM-GUD-203 and steepened, up to 0.75 per cent, until those larger than 200 mm reach 0.75 m/s at the 2031 peak flow. The adopted "
             "values are set out in Chapter 3 and Appendix B.")
    set_text(para("Every plot carries a population and an average sewage flow"),
             f"The Project area holds {f0(POP[2026])} people in 2026, {f0(POP[2031])} in 2031, when operation starts, and {f0(POP[2056])} in "
             f"2056, the design year; the average wastewater flow rises from {f0(T413[2031])} m³/d in 2031 to {f0(T413[2056])} m³/d in 2056 "
             f"(Chapter 4). Ibri reaches the residential capacity of its plots in 2064, and with the five settlements that receive its further "
             f"growth in 2071, when the Project area holds {f0(POP[2071])} people.")
    p = para("Table", style=None, within=[x for x in top() if "reconciles the flow generated by the plots" in x.text])
    set_text(p, "The table below follows the flow from the population to the treatment plant(s). The plant inflow is the flow of Chapter 4 "
                f"with the industrial estates ({f0(EST)} m³/d), less the flow of the plots not yet conveyed by the network at this stage, and "
                f"with the infiltration of the {f0(C['SC1']['sewer_km'])} km of modelled sewer ({f0(INF_N)} m³/d) in place of the allowance "
                f"for the whole network.")
    cap = para("Table", within=[x for x in top() if x.style is not None and x.style.name == "Caption" and "Population and flows in the design years" in x.text])
    caption_text(cap, "Population and flows in the design years, from the plots to the treatment plant(s)")
    YR = [2031, 2036, 2046, 2051, 2056, 2061]
    lab = {2031: "2031 (opening)", 2056: "2056 (design year)"}
    replace_table(cap, ["Year", "People", "Average flow, Chapter 4, m³/d", "Plots not yet conveyed, m³/d", "Average flow at the plant(s), m³/d",
                        "Plant design average with 10 % margin, m³/d"],
                  [[lab.get(y, y), f0(POP[y]), f0(T413[y]), f0(notc[y]), f0(inflow[y]), f0(inflow[y] * 1.1)] for y in YR])
    set_text(para("If the flow not yet carried is brought into the network"),
             f"The plots not yet conveyed lie in planted areas whose ground levels are unreliable until the survey, or more than 200 m from a "
             f"sewer; they are connected at the preliminary design, adding about {f0(notc[2056])} m³/d in 2056. "
             f"At the guideline minimum loads of 60 g BOD and 80 g TSS per person per day, the population of the design year generates "
             f"{f0(POP[2056] * 0.06)} kg BOD/d and {f0(POP[2056] * 0.08)} kg TSS/d, before any allowance for tankered sewage.")
    set_text(para("Only what the guidelines do not settle is put to Nama Water Services"),
             "Only what the guidelines do not settle is put to Nama Water Services for approval: six decisions, listed below with the "
             "Consultant's recommendation and the section in which each is explained. Nine further values are the guidelines' own, methods of "
             "this design or stated assumptions; they are adopted and reported in Appendix B. No decision had been taken at the date of this report.")
    set_text(para("Only matters that the guidelines do not settle are submitted for decision. Each decision carries"),
             "Each decision can be confirmed or amended; Section 17.3 sets out the reason each is required.")
    DEC = [("D1", "Settlement boundaries", "The guidelines do not address settlement boundaries; the polygons received leave land unassigned",
            "Approve the redrawn boundaries, which assign every plot to one settlement without gaps", "1.3.3"),
           ("D2", "Occupancy rate", "PAM-GUD-201 derives occupancy from housing units (Section 7.2, p. 59), which are not published by settlement",
            "Approve 4.8 persons per residential property, the rate of the APSR-approved Master Plan, for every settlement", "4.3.3"),
           ("D3", "Growth beyond residential capacity", "The guidelines do not state where growth goes once a settlement is full",
            "Approve the allocation of Ibri's growth after 2064 to Al Akheedar, Hijar, Al Jahli, Al Qali and Al Qurayn", "4.7.4"),
           ("D4", "Design year", "The Terms of Reference name both completion plus 25 years and saturation",
            "Design the network for 2056 (2031 plus 25 years) and phase the treatment modules to 2056; check self-cleansing at the 2031 and 2036 peaks", "6.2.3"),
           ("D5", "Growth rate beyond 2040", "PAM-GUD-201 permits ten years of extrapolation beyond a forecast (p. 58); the series extends further",
            "Approve the 2035–2040 NCSI rate of 2.11 per cent a year as the planning series, reviewed at each master plan update", "4.2.4"),
           ("D6", "Gradients and self-cleansing", "The guidelines set minimum gradients and the self-cleansing velocity, not a limit on steepening",
            "Approve steepening up to 0.75 per cent so that sewers above 200 mm reach 0.75 m/s at the 2031 peak, the tractive force criterion "
            "for 200 mm sewers, and periodic flushing of the sewers below the velocity", "3.4.2")]
    cap = para("Table", within=[x for x in top() if x.style is not None and x.style.name == "Caption" and "Decisions requested from NWS and the Consultant" in x.text])
    replace_table(cap, ["No.", "Decision", "Consultant's recommendation", "Section"], [[a, b, dd, e] for a, b, c, dd, e in DEC])
    set_text(para("The overflow decision (D3) has the greatest effect"),
             "The design year (D4) and the gradient rule (D6) shape the network: together they set the pipe sizes, the depth, the number of "
             "pumping and lift stations and the length of sewer that cleans itself from the start of operation.")
    sub(para("Options and Appraisal"), ("Options and Appraisal", "Scenarios and Appraisal"))
    f = C["SC1"]
    set_text(para("Seven sewer network options (S1 to S7) have been modelled in SewerGEMS"),
             f"Four scenarios have been designed and modelled in SewerGEMS. They share the same {f0(f['sewer_km'])} km of sewer and "
             f"{f0(f['manholes'])} manholes and differ in where the flow is treated: SC1 at STP-1 only, SC2 at STP-2 only, SC3 at STP-1 and "
             f"STP-5, SC4 at STP-2 and STP-5. The network of each is designed for 2056, with {f['pumps']} pumping stations and {f['lifts']} lift "
             f"stations in SC1 and SC2 and {C['SC3']['pumps']} and {C['SC3']['lifts']} in SC3 and SC4; {f1(f['km_big'] - f['km_under31'])} km of the "
             f"{f1(f['km_big'])} km of sewer larger than 200 mm reach the self-cleansing velocity at the 2031 peak. No pipe exceeds 3.0 m/s or the "
             "maximum proportional depth of flow in any scenario.")
    set_text(para("The options are appraised on whole-life cost over 25 years"),
             "The scenarios are appraised on whole-life cost over 25 years, 2031 to 2055, at a 5 per cent discount rate and constant prices "
             "(PAM-GUD-201, pp. 95 to 96), with the cumulative expenditure escalated at 5 per cent a year reported alongside (Chapter 8). Where "
             "scenarios lie within 10 per cent of the lowest whole-life cost, the more sustainable is preferred (PAM-GUD-201, p. 106).")
    # the figure of the seven options goes; the table at a glance is rebuilt
    fc = para("Figure", within=[x for x in top() if x.style is not None and x.style.name == "Caption" and "The seven options in 2070" in x.text])
    e = fc._p.getprevious()
    while e is not None and not e.findall(".//" + qn("a:blip")): e = e.getprevious()
    remove([e, fc._p])
    cap = para("Table", within=[x for x in top() if x.style is not None and x.style.name == "Caption" and "Sewer network options at a glance" in x.text])
    caption_text(cap, "The four scenarios at a glance (2056 design) and their cost over 25 years")
    replace_table(cap, ["Scenario", "Plants and design capacity, m³/d", "Pumping / lift stations", "Sewage pumping energy, MWh/yr", "Capital cost, M OMR",
                        "Whole-life cost, constant prices, M OMR", "Cumulative cost, escalated, M OMR"],
                  [[sc, cap_txt(sc), f"{C[sc]['pumps']} / {C[sc]['lifts']}", f0(mwh[sc]), M(fin[sc]["capex_base"]),
                    f"{M(pv[sc])} ({above(pv, sc)})", f"{M(tot[sc])} ({above(tot, sc)})"] for sc in SC])
    set_text(para("Three options are recommended, in order of priority"), "Two scenarios are recommended, in order of priority:")
    REC1 = ("SC1, one plant at STP-1.", f"The lowest cumulative cost over 25 years ({M(tot['SC1'])} M OMR escalated) and within "
            f"{(pv['SC1'] / pv[lo_pv] - 1) * 100:.1f} per cent of the lowest whole-life cost. A single plant on the existing treatment site, with "
            "one sludge line, one discharge consent, one odour buffer and one source of treated effluent. Its main sewers are the largest and "
            f"the plant inlet is {C['SC1']['plants']['P1']['inlet_depth_m']:.1f} m deep.")
    REC2 = ("SC3, plants at STP-1 and STP-5.", f"The lowest whole-life cost at constant prices ({M(pv['SC3'])} M OMR) and the least pumping: "
            f"{f0(mwh['SC3'])} MWh a year in 2056 against {f0(mwh['SC1'])} for SC1, and {f0(fin['SC3']['te']['kw'])} kW of treated effluent boosting "
            f"against {f0(fin['SC1']['te']['kw'])} kW. It requires a second plant and a footprint at STP-5 that meets the 500 m separation.")
    set_lead(para("S1, one plant at O1. Lowest whole-life cost in both cases"), *REC1)
    set_lead(para("S3, two plants at O1 and O4."), *REC2)
    remove([para("S7, three plants at O1, O16 and O22.")._p])
    set_text(para("S1, S3 and S7 lie within the 10 per cent band"),
             f"All four scenarios lie within the 10 per cent band on whole-life cost, and SC1 and SC3 within {abs(pv['SC1'] / pv['SC3'] - 1) * 100:.1f} "
             "per cent of each other, which is well inside the ±20 per cent accuracy of a concept estimate. SC1 is placed first because its plant "
             "uses the existing site and its cumulative cost is the lowest; SC3 saves pumping energy but depends on a second site whose current "
             "footprint does not meet the separation requirement. SC2 and SC4 treat the flow at STP-2, outside the Project boundary: they pump "
             f"the flow of system P1 to it, using {f0(mwh['SC2'])} and {f0(mwh['SC4'])} MWh a year in 2056, and cost more on both bases. They are "
             "not recommended.")
    set_text(para("The ranking is sensitive to the assumptions for land cost"),
             "The order of SC1 and SC3 depends on the cost basis: at constant prices SC3 is the lower, and with costs escalated SC1 is the lower, "
             "because the second plant of SC3 adds staff and land rent every year (Sections 8.8 and 14.5). NWS confirmation of the land-cost basis "
             "and of the criteria weights is requested before the scenario is finalised at the Concept Design Workshop.")
    set_text(para("The design capacity of the main plant exceeds 20,000 m³/d in every option"),
             f"The design capacity of the main plant exceeds 20,000 m³/d in every scenario ({f0(fin['SC1']['plants']['STP-1']['total'])} m³/d in "
             f"SC1, built in four modules, three of them in 2031). Under the Terms of Reference, the Consultant's STP scope is then limited to the "
             "concept stage unless the Phase I design capacity is below 20,000 m³/d or NWS instructs otherwise (ToR Section 03, pp. 51, 53). Site "
             "selection, capacity and phasing are set out in Chapter 7. Every plant meets the demand of the 31 registered treated effluent "
             f"customers it supplies from the start of operation, with about {ten(TEdel[2056] - 22508)} m³/d to spare in 2056 (Section 6.2.6); the "
             "provisions for excess effluent, emergency overflow and tankered sewage are set out in Chapter 10.")
    sub(para("Matters Requiring Attention in Every Option"), ("Every Option", "Every Scenario"))
    set_text(para("Long rising mains carrying small early-year flows"),
             "Long force mains carrying small early-year flows retain sewage for long periods; hydrogen sulphide control is required at their "
             "pumping stations.")
    set_text(para("The O23 station lifts about 5 L/s"),
             f"Pumping station P14 lifts about {f0(p14.duty_ls)} L/s through {f1(p14.force_main_m / 1000)} km of force main against "
             f"{f0(p14.head_m)} m of head; a shorter connection or local treatment is assessed at the preliminary design.")
    set_text(para("Head-of-system pipes do not attain the self-cleansing velocity"),
             f"{f1(f['km_under31'])} km of sewer larger than 200 mm stays below 0.75 m/s at the 2031 peak, {f1(f['km_under36'])} km of it still at "
             "the 2036 peak; these sewers are listed for periodic flushing in the early years.")
    set_text(para("Forty manholes exceed the 12 m depth trigger"),
             f"{f0(f['mh_over12'])} manholes are deeper than 12 m to invert, the deepest {f['deepest']['depth']:.1f} m; each is reviewed on the "
             "surveyed levels at the preliminary design (Section 3.4.3).")
    # the footnote of the boundary paragraph
    for rel in d.part.rels.values():
        if rel.reltype.endswith("/footnotes"):
            fp = rel.target_part
            if hasattr(fp, "_element"):
                for t in fp._element.iter(qn("w:t")):
                    if t.text and "Section 1.5.4" in t.text: t.text = t.text.replace("Section 1.5.4", "Section 1.3.2")
            else:
                fp._blob = fp.blob.replace(b"Section 1.5.4", b"Section 1.3.2")

    # ------------------------------------------------------------------ glossary
    for tb in d.tables:
        for row in tb.rows:
            k = norm(row.cells[0].text)
            if k == "S1 to S7":
                set_text(row.cells[0].paragraphs[0], "SC1 to SC4")
                set_text(row.cells[1].paragraphs[0], "The four concept design scenarios, by where the flow is treated (Section 6.2.1)")
            elif k == "H1 to H6": set_text(row.cells[1].paragraphs[0], norm(row.cells[1].text).replace("Section 1.2.7", "Section 1.3.8"))
            elif k == "NASA POWER": set_text(row.cells[1].paragraphs[0], norm(row.cells[1].text).replace("Section 1.2.5", "Section 1.3.6"))

    # ================================================================== CHAPTER 5
    sub(para("The existing STP is recorded with a nominal capacity of 1,800"),
        ("against an average flow of 24,756 m³/d at the new plant(s) in 2030 and 60,456 m³/d in 2070",
         f"against an average inflow of {f0(inflow[2031])} m³/d to the new plant(s) in 2031 and {f0(inflow[2056])} m³/d in 2056"))
    set_text(para("In every option the main plant is located at outfall O1"),
             "In Scenarios SC1 and SC3 the main plant is STP-1, at the existing treatment site and the low point of the Project area; in SC2 and "
             "SC4 the main plant is STP-2, and the existing site is decommissioned or used for the transfer of flow. For STP-1, three integration "
             "approaches are considered:")
    sub(para("Given that the existing plant represents less than 3 per cent of the 2070 capacity"),
        ("less than 3 per cent of the 2070 capacity", f"about {1800 / fin['SC1']['plants']['STP-1']['total'] * 100:.0f} per cent of the design capacity of STP-1"))
    set_text(para("The master plan report has not been provided and has been requested"),
             "The master plan report has not been provided and has been requested (Section 2.5). The only master plan value held is the plant "
             f"design case of 29,038 m³/d recorded in the asset data (Section 5.4). Against this, the present study establishes an average inflow "
             f"of {f0(inflow[2056])} m³/d at the plant(s) in 2056, the design year (Section 7.3.1). The verification is completed on receipt of "
             "the master plan, on the flow series of Section 4.8.3 and the design year of Decision D4. The data required by NWS Asset Management "
             "Planning for updating the master plan is supplied in the format specified by NWS.")

    # ================================================================== CHAPTER 6: locations, TE demand and supply, typed captions
    sub(para("Six potential treatment locations are identified as STP-1 to STP-6"),
        ("These identifiers remain consistent across all options, irrespective of the number of treatment facilities included.",
         "The identifiers are kept in every scenario; the four scenarios use STP-1, STP-2 and STP-5."))
    p = para("The treated effluent available for delivery to customers across the Project area")
    set_text(p, f"The treated effluent available for delivery to customers across the Project area is estimated at {ten(TEdel[2031])} m³/d in "
                f"2031, increasing to {ten(TEdel[2056])} m³/d in 2056, after 5 per cent for process use and 10 per cent for network losses "
                "(Section 4.10). A total of 31 existing and potential public and private customers have been verified, and their demands have "
                "been estimated up to 2070.")
    sub(para("A treated effluent hydraulic model has been developed for each proposed option"), ("for each proposed option", "for each scenario"))
    p = para("The verified demand is below the projected treated effluent production")
    set_text(p, "The table below compares, for each plant, the treated effluent delivered with the demand of the customers it supplies; demands "
                "between the years of the register are interpolated linearly. Every plant meets the demand of its customers from the start of "
                "operation, and the surplus is managed as set out in Section 10.1. Further reuse opportunities are assessed at the next design "
                "stage with local stakeholders.")
    o = Out(p._p.getnext())
    rows = []
    for sc in SC:
        for pl, s in fin[sc]["supply"].items():
            rows.append([sc, pl, s["customers"], f"{f0(s['2031']['delivered'])} / {f0(s['2031']['demand'])}",
                         f"{f0(s['2056']['delivered'])} / {f0(s['2056']['demand'])}", f0(s["2056"]["delivered"] - s["2056"]["demand"])])
    o.table(["Scenario", "Plant", "Customers", "Delivered / demand 2031, m³/d", "Delivered / demand 2056, m³/d", "Surplus 2056, m³/d"], rows,
            caption="Treated effluent delivered and customer demand, by plant")
    for x in [q for q in top() if norm(q.text).startswith("Table 6-4 Scenario SC") and "TE Network Pipes Arrangement" in q.text]:
        sc = re.search(r"SC\d", x.text).group(0); Out(x._p).caption("Table", f"Scenario {sc} – TE Network Pipes Arrangement"); remove([x._p])

    # ================================================================== CHAPTER 7
    T7 = "Sewage Treatment Plant"
    sub(para("This chapter presents the site selection, capacity, development phasing and land requirements"),
        ("under the seven concept design options", "under the four concept design scenarios"))
    sub(para("The six candidate STP locations are assessed against their suitability"), ("associated with each option.", "associated with each scenario."))
    sub(para("STP-3 and STP-5 are excluded in their current positions"),
        ("Any option relying on these sites requires a compliant alternative footprint before it can be carried forward as a feasible arrangement.",
         "Scenarios SC3 and SC4 rely on STP-5 and therefore require a compliant alternative footprint for it before either can be carried "
         "forward; STP-3, STP-4 and STP-6 are not used in the scenarios."))
    h = head(T7, "Projected Inflows"); o = clear_after(h)
    o.p(f"The table below presents the projected average daily inflow to each STP under SC1 to SC4 at five-year intervals from 2031 to 2061. "
        f"Flows are the wastewater generated within the pumping systems assigned to each plant, with their infiltration allowance of 0.72 m³/d "
        f"per km of sewer and the industrial estates. The combined average inflow is the same in every scenario, increasing from "
        f"{f0(inflow[2031])} m³/d in 2031 to {f0(inflow[2056])} m³/d in 2056, the design year; the scenarios differ in how it is divided "
        "among the treatment facilities.")
    o.p(f"The inflow excludes the plots not yet conveyed by the network: plots in planted areas, where ground levels are unreliable until the "
        f"survey, and plots more than 200 m from a sewer, {f0(notc[2031])} m³/d in 2031 and {f0(notc[2056])} m³/d in 2056. They are connected "
        "at the preliminary design and are within the 10 per cent margin of the design capacity.")
    rows = []
    for sc in SC:
        for pl, m in fin[sc]["plants"].items():
            rows.append([sc, pl, f0(plant_km[sc][pl] * 0.72)] + [f0(m["q"][str(y)]) for y in (2031, 2036, 2041, 2046, 2051, 2056, 2061)])
    o.table(["Scenario", "Treatment facility", "Infiltration"] + [str(y) for y in (2031, 2036, 2041, 2046, 2051, 2056, 2061)], rows,
            caption="Projected Inflows to the Treatment Facilities, m³/d")
    h = head(T7, "Phasing"); o = clear_after(h)
    o.p("The treatment facilities are developed in four equal modules each, with sufficient modules installed for the opening-year duty in "
        "2031. A further module is commissioned as the projected inflow increases towards the design year, 2056.")
    o.p("The required number of operating modules is calculated from the average inflow, including infiltration, with a 10 per cent design "
        "margin. The module sizes are concept-stage capacities, subject to the treatment process selection and equipment configuration. The "
        "stated year is the first five-year assessment year requiring the additional capacity; the module is commissioned before that year's "
        "demand is reached.")
    rows = []
    for sc in SC:
        for pl, m in fin[sc]["plants"].items():
            n0 = m["plan"]["2031"]; add = "; ".join(f"by {y}: +{k} module" for y, k in m["plan"].items() if y != "2031") or "-"
            rows.append([sc, pl, f0(m["size"]), n0, f0(n0 * m["size"]), add, m["n"], f0(m["total"]), f0(m["q"]["2056"] * 1.1)])
    o.table(["Scenario", "Facility", "Module capacity (m³/d)", "2031 modules", "2031 capacity (m³/d)", "Additional modules", "Modules",
             "Design capacity (m³/d)", "2056 inflow + margin (m³/d)"], rows, caption="STP Phasing")
    o.p("Fixed module sizes provide some spare capacity above the calculated requirement. Module capacities and construction packages are "
        "refined during the process design to balance initial investment, expansion frequency and capacity utilization, and the phasing is "
        "reviewed against actual sewer connections, measured flows and pollutant loads. Land is reserved for growth beyond the design year.")

    # ================================================================== CHAPTER 8
    T8 = "FINANCIAL ANALYSIS"
    sub(para("The financial analysis compares OP1–OP7 on a common basis"),
        ("compares OP1–OP7 on a common basis", "compares the four scenarios, SC1 to SC4, on a common basis"),
        ("Each option is assessed", "Each scenario is assessed"))
    sub(para("CAPEX is estimated from the concept quantities and the proposed development stages"), ("broadly common to the options", "common to the scenarios"))
    sub(para("Pumping energy is calculated from the operating profile of each station"),
        ("so an option with lower pumping power", "so a scenario with lower pumping power"))
    sub(para("An annual inflation rate of 5 per cent is adopted for the financial assessment"),
        ("Future CAPEX and OPEX are escalated from the base-year prices", "Future CAPEX and OPEX are escalated from the base-year prices of 2031, the start of operation,"),
        ("applied consistently across all options", "applied consistently across all scenarios"))
    h = head(T8, "Options CAPEX", "Heading 2")
    els = []; e = h._p
    while e is not None and level(e) != 1 and e.tag != qn("w:sectPr"): els.append(e); e = e.getnext()
    o = Out(e); remove(els)
    COMP = [("sewers", "Sewer pipes"), ("manholes", "Manholes"), ("stations", "Pumping and lift stations"), ("force_mains", "Force mains"),
            ("stp", "STP"), ("te_mains", "TE mains"), ("te_boosters", "TE booster stations")]
    o.h("Scenarios CAPEX", 2)
    o.p("The CAPEX of each scenario is derived from its hydraulic model quantities: pipe lengths, diameters and installation depths, manholes, "
        "the power of the pumping and lift stations and of the treated effluent boosters, the force mains and treated effluent mains, and the "
        "capacity of the treatment modules. The network and the first treatment modules are built for 2031; later modules are allocated to "
        "their commissioning years and escalated from 2031 prices at the adopted inflation rate.")
    rows = []
    for sc in SC:
        cy = fin[sc]["capex_by_year"]; yrs = sorted(cy, key=int)
        for k, lab_ in COMP:
            vals = {y: cy[y].get(k, 0) * 1.05 ** (int(y) - 2031) for y in yrs}
            rows.append([sc if k == "sewers" else "", lab_] + [M(vals.get(y, 0)) if vals.get(y, 0) else "" for y in ("2031", "2046", "2051")] + [M(sum(vals.values()))])
        rows.append(["", "Total", "", "", "", M(fin[sc]["capex_nominal"])])
    o.table(["Scenario", "Component", "2031 (M OMR)", "2046 (M OMR)", "2051 (M OMR)", "Total CAPEX (M OMR)"], rows, caption="Scenarios Components CAPEX")
    YC = ["2031", "2036", "2041", "2046", "2051", "2055"]
    o.table(["Year"] + [f"{sc} (M OMR)" for sc in SC], [[y] + [M(fin[sc]["capex_nominal_by"][y]) for sc in SC] for y in YC], caption="Scenarios Total CAPEX, cumulative")
    o.h("Scenarios OPEX", 2); o.h("Operation Requirements", 3)
    o.p("The operational requirements of each scenario, grouped by cost category, are summarized below. Power is the installed duty of the "
        "treated effluent boosters, the sewage pumping and lift stations and the treatment plants (0.025 kW per m³/d of capacity); land covers "
        "the plants (by capacity band, Section 8.2) and the stations; staff number twenty for one plant and twenty-eight for two, plus two for "
        "every five stations; chemicals are proportional to the treatment capacity.")
    RQ = [("TE booster power (kW)", "te_kw", f0), ("Sewage pumping and lift stations, power (kW)", "sewage_kw", f0), ("STP power (kW)", "stp_kw", f0),
          ("Required plot area (m²)", "land_m2", f0), ("No. of pumping and lift stations", "stations", str), ("No. of STPs", "plants", str),
          ("No. of staff", "staff", str), ("Chlorine (kg/d)", "chlorine", f0), ("NaHCO3 (kg/d)", "nahco3", f0), ("Polymer (kg/d)", "polymer", f0)]
    o.table(["Description"] + SC, [[a] + [fn(fin[sc]["requirements"][k]) for sc in SC] for a, k, fn in RQ], caption="Scenarios Operation Requirements")
    o.h("Scenarios OPEX", 3)
    o.p("OPEX is calculated from the operational requirements and the adopted unit rates for each year of operation from 2031: maintenance and "
        "operation at 1 per cent a year of the capital in service, power and chemicals in proportion to the year's flow as a share of the "
        "design flow, and land rent and staff in full from the start. Costs are escalated from 2031 prices at 5 per cent a year; the tables "
        "give the cumulative cost from 2031 to the end of each year shown, 2055 completing 25 years of operation.")
    OC = [("mo", "Maintenance & Operation"), ("power", "Power"), ("land", "Plot Rent"), ("staff", "Staff"), ("chemicals", "Chemicals")]
    rows = []
    for sc in SC:
        for i, (k, lab_) in enumerate(OC):
            rows.append([sc if i == 0 else "", lab_] + [M(fin[sc]["opex_cum"][k][y]) for y in YC])
    o.table(["Scenario", "Component"] + [f"{y} (M OMR)" for y in YC], rows, caption="Scenarios Operation Components Cumulative Cost")
    o.table(["Year"] + [f"{sc} (M OMR)" for sc in SC], [[y] + [M(fin[sc]["opex_cum"]["opex_nominal"][y]) for sc in SC] for y in YC], caption="Scenarios Total Cumulative OPEX")
    o.h("Scenarios CAPEX and OPEX", 2)
    o.p("The total CAPEX and cumulative OPEX of each scenario are summarized below.")
    rows = []
    for y in ("2041", "2055"):
        cx = {sc: fin[sc]["capex_nominal_by"][y] for sc in SC}; ox = {sc: fin[sc]["opex_cum"]["opex_nominal"][y] for sc in SC}
        rows += [[y, "CAPEX"] + [M(cx[sc]) for sc in SC], ["", "OPEX"] + [M(ox[sc]) for sc in SC], ["", "TOTAL"] + [M(cx[sc] + ox[sc]) for sc in SC]]
    o.table(["Year", ""] + [f"{sc} (M OMR)" for sc in SC], rows, caption="Scenarios Total CAPEX and Cumulative OPEX")
    o.h("Conclusion", 2)
    order = sorted(SC, key=lambda s: tot[s]); lo_cx = min(SC, key=lambda s: fin[s]["capex_base"])
    pw = lambda sc: f"{(tot[sc] / tot[order[0]] - 1) * 100:.1f} per cent higher"
    o.p(f"{order[0]} has the lowest combined CAPEX and cumulative OPEX over the 25 years to 2055, {M(tot[order[0]])} million OMR. "
        f"{order[1]} follows at {M(tot[order[1]])} million OMR, {pw(order[1])}, then {order[2]} ({pw(order[2])}) and {order[3]} ({pw(order[3])}).")
    o.p(f"{lo_cx} has the lowest CAPEX, {M(fin[lo_cx]['capex_base'])} million OMR at 2031 prices, because its second plant shortens the sewers "
        f"and transfers to the main plant; its second plant adds staff and land, so its cumulative OPEX is the higher, "
        f"{M(fin[lo_cx]['opex_cum']['opex_nominal']['2055'])} million OMR against {M(fin['SC1']['opex_cum']['opex_nominal']['2055'])} million "
        "OMR for SC1. A plant at STP-2 requires the flow of system P1 to be pumped to it, which raises both the CAPEX and the power of SC2 and SC4.")
    o.p(f"OPEX accounts for about {fin['SC1']['opex_cum']['opex_nominal']['2055'] / tot['SC1'] * 100:.0f} per cent of the cumulative expenditure of "
        "SC1 over 25 years, so operating costs weigh as much as construction in the choice. The figures are cumulative expenditure including "
        "inflation; the present value at constant prices required by PAM-GUD-201 is given in Chapter 14.")

    # ================================================================== CHAPTER 9
    set_text(para("Six candidate locations are assessed across seven treatment options"),
             "Six candidate locations were assessed. The four scenarios use three of them, STP-1, STP-2 and STP-5; the assessment of all six is "
             "retained so that the selection of the plant site rests on a common basis.")
    sub(has("The applicable activity class for the works is to be confirmed with the Authority"),
        ("The applicable activity class for the works is to be confirmed with the Authority.", "The applicable activity class for the works is agreed with the Authority at the permit application."))

    # ================================================================== CHAPTER 10
    set_text(para("Where production exceeds demand, provision is made for the disposal of the excess"),
             f"Where production exceeds demand, provision is made for the disposal of the excess. On the demand of the registered customers, the "
             f"treated effluent delivered exceeds demand by about {ten(TEdel[2031] - 15012)} m³/d in 2031 and {ten(TEdel[2056] - 22508)} m³/d in "
             "2056 (Section 6.2.6). The alternatives evaluated are:")
    cap1 = fin["SC1"]["plants"]["STP-1"]
    set_text(para("At the 2070 design average of 66,502 m³/d"),
             f"At the design capacity of {f0(cap1['total'])} m³/d of the main plant in SC1, 5 days of storage corresponds to about "
             f"{f0(cap1['total'] * 5)} m³, which at 3 m operating depth requires about {cap1['total'] * 5 / 3 / 10000:.1f} ha of lagoon area, in "
             "addition to embankments and access. It is proposed that the storage be provided in stages with the plant modules, sized on the "
             f"capacity of each stage (about {f0(cap1['plan']['2031'] * cap1['size'] * 5)} m³ for the {cap1['plan']['2031']} modules of 2031), "
             "with flow pumped back to the inlet works when capacity becomes available. Confirmation of this basis is requested (Section 17.4).")
    set_text(para("Until delivery records are received, the tanker reception facility"),
             "Until delivery records are received, the tanker reception facility is planned for a capacity agreed with NWS, and the biological "
             "process is provided with the equalisation required to accept the high-strength tanker load (Section 3.6.2) without exceeding its "
             "design load.")

    # ================================================================== CHAPTERS 11 TO 13, and the review notes everywhere
    for q in [q for q in top() if norm(q.text).startswith("▶ CHECK")]: remove([q._p])
    sub(para("Treatment plant: plant-wide PLC and SCADA"), ("for the sustainability-led option, ", "where adopted, "))
    sub(para("Each option is assessed against resource use"), ("Each option is assessed", "Each scenario is assessed"))
    sub(para("PAM-GUD-203 requires sewers and manholes to be kept out of wadis"),
        ("to be confirmed by a scour assessment at the preliminary design", "subject to a scour assessment at the preliminary design"),
        ("in every option, so their exposure is independent of the option", "in every scenario, so their exposure is independent of the scenario"))
    kwh = {sc: (C[sc]["kw_network"] + C[sc]["kw_plant_inlets"]) for sc in SC}
    lo_e, hi_e = min(SC, key=lambda s: mwh[s]), max(SC, key=lambda s: mwh[s])
    set_text(para("As most operational emissions arise from electricity"),
             f"As most operational emissions arise from electricity, the measures that reduce carbon are largely those that reduce operating cost: "
             f"gravity conveyance wherever possible, minimum lift, efficient equipment and on-site renewable generation. At the concept stage, energy "
             f"is the measurable component of operating carbon. Sewage pumping energy in 2056, including the plant inlets, ranges from "
             f"{f0(mwh[lo_e])} MWh/yr in {lo_e} to {f0(mwh[hi_e])} MWh/yr in {hi_e} (Chapter 6), and the treated effluent boosters have a duty of "
             f"{f0(fin[lo_e]['te']['kw'])} to {f0(max(fin[s]['te']['kw'] for s in SC))} kW. The plants use about "
             f"{0.025 * cap1['total'] * 8760 / 1000:,.0f} MWh/yr at full load (0.025 kW per m³/d of capacity), almost the same in every scenario "
             "because the flow treated is the same; pumping is therefore the component that distinguishes the scenarios. Resource efficiency, "
             "in-country value and nature-based solutions are assessed with the treatment process at the preliminary design.")
    sub(has("Deep sewers of more than 6 m (about 199 km in option S1"),
        ("(about 199 km in option S1, Appendix D)", f"(about {f0(deep6['SC1'])} km in Scenario SC1, Appendix D)"))
    p = para("The Consultant is responsible for land acquisition for the plant(s)")
    set_text(p, re.sub(r"follows from the selected process and phasing \(Section [\d.]+\)", "follows from the selected process and phasing (Section 7.3.2)", norm(p.text)))

    # ================================================================== CHAPTER 14
    T14 = "Cost Estimate, Life-cycle Cost"
    h = head(T14, "Basis of the Estimate"); o = clear_after(h)
    o.p("Each scenario is priced on its own quantities, from the network model of its design year (Appendix D) and the treatment and treated "
        "effluent arrangements of Chapters 6 and 7, at the rates of Chapter 8. The estimate is made at concept-stage accuracy and compares the "
        "scenarios on a common basis. PAM-GUD-201 gives accuracies of ±30 per cent at feasibility, ±20 per cent at the preliminary (concept) "
        "stage and ±10 per cent at the detailed stage (pp. 17 to 18); an accuracy of ±20 per cent is adopted.")
    o.table(["Item", "Basis"], [["Accuracy", "±20 per cent (PAM-GUD-201, pp. 17 to 18)"],
                                ["Quantities", "Network model of each scenario: sewers, manholes, pumping and lift stations, force mains; treatment modules; treated effluent mains and boosters"],
                                ["Rates", "The rates of Sections 8.2 and 8.3, from recent and ongoing projects (PAM-GUD-201, Section 12.2, p. 95)"],
                                ["Price basis", "Prices of 2031, the start of operation"],
                                ["Presentation", "By system element"],
                                ["Excluded", "House connections, and road and wadi crossings, which are common to all scenarios; land acquisition (land is rented, Section 8.3); contingencies and design fees"]],
            caption="Basis of the cost estimate")
    h = head(T14, "Capital Cost"); o = clear_after(h)
    o.p("The capital cost of each scenario is built from the elements below, at 2031 prices. The treatment plants are costed on their four "
        "modules at the rate of their design capacity band; the modules added after 2031 are included at 2031 prices.")
    rows = [[lab_] + [M(sum(c.get(k, 0) for c in fin[sc]["capex_by_year"].values())) for sc in SC] for k, lab_ in COMP]
    rows.append(["Total"] + [M(fin[sc]["capex_base"]) for sc in SC])
    o.table(["Element"] + SC, rows, caption="Capital cost of the scenarios by element, M OMR (2031 prices)")
    o.p(f"The capital cost ranges from {M(fin[lo_cx]['capex_base'])} M OMR ({lo_cx}) to {M(max(fin[s]['capex_base'] for s in SC))} M OMR "
        f"({max(SC, key=lambda s: fin[s]['capex_base'])}). A second plant at STP-5 shortens the transfers to the main plant; a main plant at "
        "STP-2 adds the force main and pumping that carry the flow of system P1 to it.")
    h = head(T14, "Operating Cost"); o = clear_after(h)
    o.p("The operating cost of each scenario in its first year, 2031, is built from five items at the rates of Section 8.3: maintenance and "
        "operation at 1 per cent of the capital cost a year; power for the installed duty of the boosters, stations and plants at 0.020 OMR/kWh "
        "in proportion to the year's flow; land at 1 OMR/m² a month; staff at 2,500 OMR a month for thirteen months a year; and chemicals.")
    OI = [("mo", "Maintenance and operation"), ("power", "Power"), ("land", "Land rent"), ("staff", "Staff"), ("chemicals", "Chemicals")]
    rows = [[lab_] + [M2(fin[sc]["opex_first"][k]) for sc in SC] for k, lab_ in OI]
    rows += [["Total"] + [M2(fin[sc]["opex_first"]["total"]) for sc in SC], ["Staff, number"] + [str(fin[sc]["requirements"]["staff"]) for sc in SC],
             ["Land, thousand m²"] + [f"{fin[sc]['requirements']['land_m2'] / 1000:,.0f}" for sc in SC]]
    o.table(["Item"] + SC, rows, caption="Operating cost of the scenarios in the first year, M OMR")
    o.p("Staff and land increase with the number of plants and are the items that distinguish the scenarios with two plants; power and "
        "maintenance differ with the pumping. The replacement of mechanical and electrical equipment within the 25 years (asset lives of 15 to "
        "20 years; PAM-GUD-201, Table 10, p. 57) is broadly proportional to the plant capacity, which is the same in every scenario.")
    sub(para("PAM-GUD-201 requires the life-cycle cost to be calculated from the start of construction"),
        ("The basis of comparison is therefore the constant-price case, in which the present value of the operating cost is 14.8 times the first-year cost. For reference, the case in which the operating cost is escalated at 5 per cent a year and discounted at 5 per cent, so that the present value is 25 times the first-year cost, is also reported. The phasing of the plant capital cost is incorporated at the preliminary design.",
         "The basis of comparison is therefore the constant-price case, with the treatment modules entering in the year they are commissioned "
         "(Section 7.3.2). For reference, the cumulative expenditure with capital and operating costs escalated at 5 per cent a year, the basis "
         "of Chapter 8, is also reported."))

    def pv_variant(sc, land=True, staff_rate=2500, years=25, rate=0.05):
        a = pd.DataFrame(fin[sc]["annual"]); a = a[a.year < 2031 + years]; e = 1.05 ** (a.year - 2031)
        opex = a.mo / e + a.power / e + a.chemicals / e + (a.land / e if land else 0) + a.staff / e * staff_rate / 2500
        return float(((a.capex_base + opex) * (1 + rate) ** -(a.year - 2031)).sum())
    h = head(T14, "Whole-life Cost and Sensitivity"); o = clear_after(h)
    o.table(["Scenario", "Plants", "Capital cost", "Present value of capital", "Present value of operation", "Whole-life cost, constant prices (basis)",
             "Above lowest", "Cumulative cost, escalated (Chapter 8)", "Above lowest"],
            [[sc, len(fin[sc]["plants"]), M(fin[sc]["capex_base"]), M(fin[sc]["pv_capex"]), M(fin[sc]["pv_opex"]), M(pv[sc]), above(pv, sc),
              M(tot[sc]), above(tot, sc)] for sc in sorted(SC, key=lambda s: pv[s])], caption="Whole-life cost of the scenarios over 25 years, M OMR")
    o.p(f"At constant prices, the basis required by PAM-GUD-201, {lo_pv} has the lowest whole-life cost and SC1 lies "
        f"{(pv['SC1'] / pv[lo_pv] - 1) * 100:.1f} per cent above it; with costs escalated, SC1 is the lowest and SC3 lies "
        f"{(tot['SC3'] / tot['SC1'] - 1) * 100:.1f} per cent above it. All four scenarios lie within 10 per cent of the "
        "lowest on both bases. The two bases differ because the second plant of SC3 and SC4 adds staff and land rent every year, which weigh "
        "more when operating costs are escalated and not discounted.")
    o.p("PAM-GUD-201 requires sensitivity tests on the discount rate and on the input design criteria (p. 106). The table below tests the "
        "constant-price result against the evaluation basis and the two operating cost assumptions that most distinguish the scenarios.")
    cases = [("Basis: 25 years, 5 per cent", {}), ("Land allocated, no land rent", dict(land=False)), ("Staff at 1,200 OMR a month", dict(staff_rate=1200)),
             ("20 years at 10 per cent (former Wastewater Design Manual)", dict(years=20, rate=0.10))]
    rows = []
    for lab_, kw in cases:
        v = {sc: pv_variant(sc, **kw) for sc in SC}; rows.append([lab_] + [above(v, sc) for sc in SC])
    o.table(["Case"] + SC, rows, caption="Sensitivity of the whole-life cost (constant prices), per cent above the lowest scenario")
    o.p("SC1 and SC3 remain within a few per cent of each other in every case, and SC2 and SC4 remain above both. NWS confirmation of the land "
        "cost basis, the staff cost basis and the evaluation basis is requested before the scenario is finalised (Section 17.4).")
    h = head(T14, "Multi-criteria Analysis"); o = clear_after(h)
    o.p("PAM-GUD-201 compares alternatives by a weighted multi-criteria analysis, with weights set by NWS (pp. 95 and 104 to 106). The criteria "
        "and the Consultant's assessment of the four scenarios are set out below; the weights are agreed at the Concept Design Workshop, after "
        "which the weighted scores and their sensitivity to the weights are reported.")
    MC = [("Total lifetime cost", [f"{above(pv, sc)} at constant prices; {above(tot, sc)} escalated" for sc in SC]),
          ("Sustainability: energy and carbon", [f"{f0(mwh[sc])} MWh/yr sewage pumping (2056); {f0(fin[sc]['te']['kw'])} kW boosting" for sc in SC]),
          ("Sustainability: resource efficiency and reuse", ["One treated effluent source at the existing site", "One source, at STP-2",
                                                              "Second source at STP-5, nearer north-eastern demand", "Sources at STP-2 and STP-5"]),
          ("Adaptability and resilience", ["Single point of failure for treatment", "Single point of failure for treatment", "Two plants", "Two plants"]),
          ("Operability", ["One plant, one sludge line, one consent", "One plant; long transfer from system P1", "Two of each", "Two of each; long transfer from system P1"]),
          ("Constructability", [f"Largest main sewers; plant inlet {C[sc]['plants'][next(iter(C[sc]['plants']))]['inlet_depth_m']:.1f} m deep" if sc == "SC1" else
                                ("Force main of system P1 to STP-2" if sc in ("SC2", "SC4") else "Smaller main sewers to STP-1") for sc in SC]),
          ("Site and environment", ["Existing site; flood protection required", "Greenfield site outside the Project boundary",
                                    "Existing site and STP-5, whose footprint needs a compliant position",
                                    "STP-2 outside the boundary and STP-5, whose footprint needs a compliant position"])]
    o.table(["Criterion"] + SC, [[a] + v for a, v in MC], caption="Multi-criteria assessment of the scenarios (weights set by NWS)")
    h = head(T14, "Appraisal and Recommendation"); o = clear_after(h)
    o.p("The four scenarios have been compared on their technical results (Chapter 6) and on their whole-life cost. The depth of the network "
        "does not distinguish them; the main sewers, the pumping, the treated effluent boosting and the number and position of the plants do.")
    o.p(f"SC3 has the lowest whole-life cost at constant prices and SC1 the lowest cumulative cost escalated; they lie within "
        f"{abs(pv['SC1'] / pv['SC3'] - 1) * 100:.1f} and {abs(tot['SC3'] / tot['SC1'] - 1) * 100:.1f} per cent of each other, well inside the accuracy "
        f"of a concept estimate. SC3 uses less energy: {f0(mwh['SC1'] - mwh['SC3'])} MWh a year less sewage pumping in 2056 and "
        f"{f0(fin['SC1']['te']['kw'] - fin['SC3']['te']['kw'])} kW less treated effluent boosting. SC1 uses one plant on the existing site, with "
        "one sludge line, one consent and one odour buffer, while SC3 depends on a second plant at STP-5, whose current footprint does not meet "
        "the 500 m separation. SC2 and SC4 cost more on both bases and pump the flow of system P1 to STP-2, outside the Project boundary.")
    o.p("SC1 is therefore recommended, with SC3 as the alternative should a compliant STP-5 site be secured and the weights favour energy. The "
        "order is the Consultant's assessment, subject to the weights set by NWS and to the cost bases of Section 14.5; the final selection is "
        "made at the Concept Design Workshop (ToR Section 03, p. 62).")
    RT = [("Priority", lambda sc: {"SC1": "First", "SC3": "Second"}[sc]), ("Plants", lambda sc: ", ".join(fin[sc]["plants"])),
          ("Design capacity, m³/d", lambda sc: " / ".join(f0(m["total"]) for m in fin[sc]["plants"].values())),
          ("Pumping / lift stations", lambda sc: f"{C[sc]['pumps']} / {C[sc]['lifts']}"), ("Force mains, km", lambda sc: f1(C[sc]["force_main_km"])),
          ("Sewage pumping energy 2031 / 2056, MWh/yr", lambda sc: f"{f0(C[sc]['mwh_2031'])} / {f0(mwh[sc])}"),
          ("TE booster duty, kW", lambda sc: f0(fin[sc]["te"]["kw"])), ("Capital cost, M OMR", lambda sc: M(fin[sc]["capex_base"])),
          ("Operating cost, first year, M OMR", lambda sc: M2(fin[sc]["opex_first"]["total"])),
          ("Whole-life cost, constant prices, M OMR", lambda sc: f"{M(pv[sc])} ({above(pv, sc)})"),
          ("Cumulative cost, escalated, M OMR", lambda sc: f"{M(tot[sc])} ({above(tot, sc)})")]
    o.table(["Item", "SC1", "SC3"], [[a, fn("SC1"), fn("SC3")] for a, fn in RT], caption="The recommended scenarios")

    sub(para("Cost Estimate, Life-cycle Cost and Options Appraisal", style="Heading 1"), ("and Options Appraisal", "and Appraisal of the Scenarios"))
    sub(para("Scope Implications of the Recommended Option", style="Heading"), ("Recommended Option", "Recommended Scenario"))
    sub(has("The carbon footprint of each option is evaluated"), ("of each option is evaluated", "of each scenario is evaluated"))
    sub(has("Risks affecting one option and not another"), ("Risks affecting one option and not another", "Risks affecting one scenario and not another"), ("the comparison of options", "the comparison of scenarios"))
    sub(has("is presented with the STP Location Report in Volume 3"), ("is presented with the STP Location Report in Volume 3", "is presented in Chapter 9"))
    fc = para("Figure", within=[x for x in top() if x.style is not None and x.style.name == "Caption" and "Concept design process" in x.text])
    caption_text(fc, "Concept design process, from data collection to the recommended scenario")
    # ================================================================== CHAPTER 15
    rr = table_with("Mitigation")
    set_text(rr.rows[0].cells[6].paragraphs[0], "Scenarios"); cell_set(rr, "R12", 2, "Scenario ranking changes (Section 14.5)")
    cell_set(rr, "R04", 6, "SC2 to SC4 higher (new sites)"); cell_set(rr, "R09", 6, "All"); cell_set(rr, "R12", 6, "All")
    cell_set(rr, "R07", 7, "Existing plant and tanker records (Section 2.5); characterisation programme (Section 3.6.2)")
    cell_set(rr, "R09", 7, "Hydrogen sulphide evaluation; dosing or shorter routes (Chapter 6)")
    cell_set(rr, "R10", 7, "Decision D6; flushing regime (Section 3.4.2)")
    cell_set(rr, "R14", 1, f"Plots not yet conveyed ({f0(notc[2056])} m³/d in 2056) require sewers")
    cell_set(rr, "R14", 7, "Connect them at the preliminary design (Section 7.3.1)")
    sub(para("The Terms of Reference require three value engineering workshops"),
        ("with an estimated capital cost of 136 to 153 M OMR excluding the treated effluent network",
         f"with an estimated capital cost of {M(fin[lo_cx]['capex_base'])} to {M(max(fin[s]['capex_base'] for s in SC))} M OMR"))
    sub(para("The concept-stage workshop is held following the Concept Design Workshop"),
        ("on the selected option", "on the selected scenario"), ("the O23 connection; the treated effluent network option;", "the P14 connection; the treated effluent network;"))

    # ================================================================== CHAPTER 16
    sub(para("The roadmap sets out, for the recommended option"), ("for the recommended option", "for the recommended scenario"))
    tb = table_with("Prerequisites"); cell_set(tb, "Concept approval", 1, "Recommended scenario, design basis and plant site approved")
    m1 = fin["SC1"]["plants"]["STP-1"]
    set_text(para("The sewers are laid once, for the 2070 flow"),
             f"The sewers are laid once, for the 2056 flow. The plant is built in modules following the flow: in Scenario SC1 it receives "
             f"{f0(m1['q']['2031'])} m³/d in 2031, {f0(m1['q']['2041'])} m³/d in 2041 and {f0(m1['q']['2056'])} m³/d in 2056 (Section 7.3). Once "
             "the works are in service, performance is monitored against the flows and loads of Chapter 4.")
    set_text(para("Under the recommended option S1, the main plant exceeds the 20,000 m³/d threshold"),
             f"Under the recommended scenario SC1, the main plant exceeds the 20,000 m³/d threshold in its first phase "
             f"({f0(m1['plan']['2031'] * m1['size'])} m³/d in 2031, Section 7.3.2), and the preliminary design and EPC tender of the plant fall "
             "outside the Consultant's scope unless NWS instructs otherwise. NWS is requested to confirm how the plant is to be taken forward: by "
             "instruction to the Consultant under the optional scope, by a separate procurement, or by an alternative delivery model. The network "
             "packages and the treated effluent network continue through all design stages within the Consultant's scope. Under SC3, the plant at "
             f"STP-5 ({f0(fin['SC3']['plants']['STP-5']['total'])} m³/d) is below the threshold and within the Consultant's scope.")
    for q in [q for q in top() if norm(q.text).startswith("effluent network continue through all design stages")]: remove([q._p])
    sub(para("The Consultant supports NWS in preparing the Pre-Investment Appraisal Document"),
        ("the options and their appraisal", "the scenarios and their appraisal"), ("of the recommended option", "of the recommended scenario"))

    # ================================================================== CHAPTER 17
    T17 = "Technical and Financial Appraisal"
    h = head(T17, "Conclusions"); o = clear_after(h)
    o.p("The design basis for the wastewater and treated effluent systems is established (Chapter 3). The data supplied has been validated, and "
        "the usable datasets, those requiring correction and those relating to areas outside the project have been identified (Chapter 2).")
    o.p("The existing wastewater assets within the Project area comprise 111.6 km of constructed gravity sewer and 10.0 km of constructed force "
        "main; a further 268.2 km of gravity sewer, pumping main and treated effluent main is recorded as proposed only. The population is "
        f"projected by three methods and their mean adopted: {f0(POP[2031])} people in 2031 and {f0(POP[2056])} in 2056, generating "
        f"{f0(T413[2031])} and {f0(T413[2056])} m³/d (Chapter 4).")
    o.p(f"The sewer network has been designed over the whole Project area for 2056: {f0(f['sewer_km'])} km of sewer and {f0(f['manholes'])} "
        f"manholes in {len(set(C['SC1']['stations'].system))} pumping systems, within the guideline limits on maximum velocity and depth of flow in "
        f"every scenario, and modelled in SewerGEMS. In every scenario the plant(s) receive {f0(inflow[2031])} m³/d in 2031 and "
        f"{f0(inflow[2056])} m³/d in 2056, including infiltration, and are built in modules to {f0(m1['total'])} m³/d. Steepening up to 0.75 "
        f"per cent brings {f1(f['km_big'] - f['km_under31'])} km of the {f1(f['km_big'])} km of sewer larger than 200 mm to the self-cleansing "
        "velocity from the start of operation.")
    o.p(f"On whole-life cost all four scenarios lie within 10 per cent of the lowest. SC1 (one plant at STP-1) and SC3 (plants at STP-1 and "
        "STP-5) are within a few per cent of each other on both cost bases; SC1 is recommended and SC3 is the alternative. Every plant meets "
        "the demand of its treated effluent customers from the start of operation.")
    o.p(f"In every scenario some long force mains retain sewage and require hydrogen sulphide control; the P14 connection requires an "
        f"alternative; {f1(f['km_under31'])} km of sewer requires periodic flushing in the early years; and {f0(f['mh_over12'])} manholes exceed "
        "12 m in depth. The topographic and utility survey covering the whole Project area is in progress; it establishes the levels, diameters "
        "and condition not carried by the supplied datasets, on which the assessment of the existing network depends.")
    h = head(T17, "Recommendations"); items = [Pp(x) for x in section(h)[1:] if x.tag == qn("w:p") and norm(Pp(x).text) and not norm(Pp(x).text).startswith("It is recommended")]
    assert len(items) == 6, [norm(i.text)[:40] for i in items]
    for p_, t in zip(items, ["Scenario SC1 is taken forward to the preliminary design as the recommended scenario, with SC3 as the alternative, subject to the "
              "weights and cost bases confirmed by NWS at the Concept Design Workshop;",
              "NWS takes the six decisions of Section 17.3, the design year and the gradient rule first among them;",
              "NWS confirms the matters of Section 17.4 and supplies the data requested in Section 2.5, so that the preliminary design proceeds on an agreed basis;",
              "the P14 connection and the long force mains that retain sewage are resolved at the preliminary design by a shorter route, a nearer "
              "receiving system, local treatment or dosing;",
              "NWS confirms how the main treatment plant is to be taken forward beyond the concept stage (Section 16.3);",
              "applications for land, route approval and power supply are made immediately following the Concept Design Workshop."]):
        set_text(p_, t)
    cap = para("Table", within=[x for x in top() if x.style is not None and x.style.name == "Caption" and "Decisions requested from NWS" in x.text and "recommendation" not in x.text])
    replace_table(cap, ["No.", "Decision", "Why a decision is required", "Consultant's recommendation", "Section"], [list(x) for x in DEC])
    tb = table_with("To be confirmed"); set_text(tb.rows[0].cells[1].paragraphs[0], "Confirmation requested")
    for k, v, s_ in [("Maximum gradient", "The steepening limit of 0.75 per cent, applied to sewers larger than 200 mm", "Section 3.4.2"),
                     ("Plant margin", "The 10 per cent margin applied to the peak hourly flow as well as the average annual flow", "Section 4.9"),
                     ("Unserved catchments", "On-site solution for three small outlying catchments, and the connection of the plots not yet conveyed", "Section 7.3.1")]:
        cell_set(tb, k, 1, v); cell_set(tb, k, 2, s_)
    row = tb.add_row().cells
    for i, v in enumerate(["STP-5 site", "A footprint at STP-5 that meets the 500 m separation, for Scenarios SC3 and SC4", "Section 7.2.4"]):
        set_text(row[i].paragraphs[0], v)

    sub(has("allowing capacity to be added in phases"), ("allowing capacity to be added in phases", "so that capacity can be added in phases"))

    # ================================================================== APPENDICES
    tb = table_with("ToR deliverable")
    for k, col, v in [("4", 2, "Inception Report"), ("4", 3, "Addressed"), ("10", 2, "Section 3.6.2"), ("11", 2, "Chapter 7"), ("12", 2, "Sections 4.2 to 4.6"),
                      ("13", 2, "Section 6.2.6"), ("14", 2, "Section 4.3"), ("15", 2, "Sections 4.8 and 6.2"), ("16", 2, "Section 6.2.6"),
                      ("17", 2, "Sections 5.2 and 5.5"), ("18", 2, "Section 5.3; TE network of each scenario, Chapter 6"), ("19", 2, "Sections 3.5 and 6.3 to 6.6; Appendix D"),
                      ("20", 2, "Chapter 7"), ("21", 2, "Section 6.2.6; Chapter 10"), ("22", 2, "Section 7.2; Chapter 9"),
                      ("23", 2, "Chapter 8; Sections 14.2 and 14.7"), ("23", 3, "Addressed (concept estimate)"), ("24", 2, "Chapter 6, TE network of each scenario"),
                      ("34", 2, "Chapters 8 and 14"), ("34", 3, "Addressed"), ("36", 2, "Chapter 6; Appendix D")]:
        cell_set(tb, k, col, v)
    for row in tb.rows:
        a, b = norm(row.cells[1].text), norm(row.cells[2].text)
        if a.startswith("Integration between the existing and new plants"): set_text(row.cells[2].paragraphs[0], "Section 5.4")
        if a.startswith("Tanker discharge facilities"): set_text(row.cells[2].paragraphs[0], "Section 10.4")
        if a.startswith("Hydraulic assessment for 2030, 2055"): set_text(row.cells[2].paragraphs[0], "Sections 6.2.3 and 6.3 to 6.6")
        if a.startswith("Sulphide indicator"): set_text(row.cells[2].paragraphs[0], "Chapter 6")
    tb = table_with("Value adopted")
    AV = {"A7": ("Meters more than 15 m from any plot", "126 meters excluded from plot loads", "Design choice: no plot within 15 m", "4.3.2"),
          "A8": ("Land-use layer", "Use of each plot determined from its meters and satellite imagery", "Design method: cadastral land-use field not usable", "4.3.1"),
          "A10": ("Industrial estates", f"4,500 workers (At Tayyib) and 1,800 (Tanam) at 93 L/day, {f0(EST)} m³/d", "Stated assumption; rate from PAM-GUD-201, Table 12, p. 61", "7.3.1"),
          "A11": ("Future plots receiving growth", "Plots of 200 to 3,000 m², not agricultural, heritage or industrial, sharing each settlement's growth equally",
                  "Design method: planning zoning of future plots not relied on", "6.2.2"),
          "A12": ("Infiltration and peak flow", "720 L/day/km of sewer; Merrimack above 100 properties, Peltier at 100 or fewer", "PAM-GUD-201, Sections 7.4.2 and 7.4.3, pp. 71 to 72", "4.8.2, 4.8.4"),
          "A13": ("Depth", "12 m as the trigger for a station; stations to about 15 m and manholes to 16.5 m where a station is saved", "PAM-GUD-203, Section 4.6.3, p. 33", "3.4.3"),
          "A14": ("Plant flows and loads", "Average annual and peak hourly flows with 10 per cent margin; 60 g BOD and 80 g TSS per person per day",
                  "PAM-GUD-201, Section 7.4.5, p. 73; PAM-GUD-203, Table 29, p. 65, and Section 10.3.1, p. 74", "3.6.2, 4.9"),
          "A15": ("Treated effluent", "Production 95 per cent of inflow; network loss 10 per cent of production", "PAM-GUD-201, Section 7.4.6, pp. 73 and 76", "4.10, 6.2.6")}
    for k, vals in AV.items():
        for i, v in enumerate(vals, 1): cell_set(tb, k, i, v)
    cell_set(tb, "A9", 4, "4.8.1")
    p = para("Each tariff in the electricity dataset is assigned to one of the guideline categories")
    set_text(p, re.sub(r"carry no load \(Section [\d.]+\)", "carry no load (Section 4.3.2)", norm(p.text)))
    # C.3 and C.4: the settlement parameters and overflow routes of the earlier basis give way to the plots and flows of this design
    h3 = para("C.3 Settlement Parameters", style="Heading")
    els = []; e = h3._p
    while e is not None and level(e) > 1 and e.tag != qn("w:sectPr"): els.append(e); e = e.getnext()
    o = Out(e); remove(els)
    hc = copy.deepcopy(para("C.2 Large-consumer Accounts")._p); o.put(hc); set_text(Pp(hc), "C.3 Future Plots and Flow Not Yet Conveyed")
    o.p("For each settlement, the table gives the future plots that receive its growth (Section 6.2.2), the average flow of its plots in 2056 "
        "and the part of it not yet conveyed by the network (Section 7.3.1).")
    stl = gpd.read_file(os.path.join(F.W18, "gis", "W18_settlements_2026_2100.shp"))
    cn, cg, cq, cnc = "SETTLE", "N_GROWTH", "Q_2056", "QNC_2056"      # gis/W18_settlements_2026_2100_fields.md
    t = stl[[cn, cg, cq, cnc]].sort_values(cq, ascending=False)
    assert abs(t[cq].sum() - carried[2056] - notc[2056]) < 2, (t[cq].sum(), carried[2056], notc[2056])
    o.table(["Settlement", "Future plots receiving growth", "Average flow 2056, m³/d", "Not yet conveyed 2056, m³/d"],
            [[r[cn], f0(r[cg]), f0(r[cq]), f0(r[cnc])] for _, r in t.iterrows()] + [["Total", f0(t[cg].sum()), f0(t[cq].sum()), f0(t[cnc].sum())]],
            caption="Future plots and flow not yet conveyed, by settlement")
    # F: the rates of Chapter 8
    hf = para("Appendix F.", style="Heading 1"); o = clear_after(hf)
    o.p("This appendix records the unit rates of the estimate of Chapters 8 and 14, from recent and ongoing projects and representative market "
        "prices (PAM-GUD-201, Section 12.2, pp. 95 to 96); the sewer and manhole rates vary with depth, in 0.5 m bands from 1.5 m to 15 m.")
    o.table(["Element", "Unit", "Rate"], [["Gravity sewers, 200 to 2,200 mm, by depth", "OMR/m", "11 to 14,125 (Table 8-2)"],
                                          ["Manholes, 1,200 to 1,800 mm, by depth", "OMR/no.", "705 to 26,100 (Table 8-3)"],
                                          ["Force mains and treated effluent mains, 100 to 1,200 mm", "OMR/m", "10 to 273 (Table 8-4)"],
                                          ["Pumping and lift stations up to 10 kW", "OMR/kW", "25,000"], ["Stations above 10 kW, plant inlet and booster stations", "OMR/kW", "5,000"],
                                          ["Treatment plants, by design capacity", "OMR per m³/d", "1,000 (up to 1,000 m³/d) to 500 (up to 100,000 m³/d)"],
                                          ["Power tariff", "OMR/kWh", "0.020"], ["Land", "OMR/m² per month", "1.0"], ["Staff", "OMR per person per month", "2,500, thirteen months a year"],
                                          ["Chlorine, NaHCO3, polymer", "OMR/kg", "0.3, 0.3, 1.0"], ["Inflation and discount rate", "per cent a year", "5"]],
            caption="Unit rates of the concept estimate")
    # H: the drawings of the four scenarios
    hh = para("Appendix H.", style="Heading 1"); o = clear_after(hh)
    o.p("This appendix gathers the concept drawings: the pumping systems of the sewer network, and the network of each scenario with its pumping "
        "and lift stations and force mains.")
    o.maps([(os.path.join(IMG, "map_pumping_systems.png"), "The pumping systems of the network, their pumping and lift stations")]
           + [(os.path.join(IMG, f"map_{sc}_{F.BASE}_network.png"), f"Scenario {sc}: sewers, pumping and lift stations and force mains") for sc in SC])
    # the maps end the document: their landscape section is the last one, so no empty section follows them
    last = body.find(qn("w:sectPr")); lp = last.getprevious()
    if lp is not None and lp.find(qn("w:pPr")) is not None and lp.find(qn("w:pPr")).find(qn("w:sectPr")) is not None:
        body.replace(last, copy.deepcopy(lp.find(qn("w:pPr")).find(qn("w:sectPr")))); body.remove(lp)

    # ================================================================== caption numbers as text
    chap_no, label = 0, "ES"
    for e in list(body.iterchildren()):
        if e.tag != qn("w:p"): continue
        p = Pp(e); s = p.style.name if p.style is not None else ""
        if s == "Heading 1":
            t = norm(p.text)
            if t.startswith("Appendix"): label = t.split()[1].rstrip(".")
            elif t.upper().startswith("INTRODUCTION") or chap_no: chap_no += 1; label = str(chap_no)
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
                    t = new.makeelement(qn("w:t"), {}); t.text = label; new.append(t)
                    runs[i].addprevious(new)
                    for r in runs[i:j + 1]: r.getparent().remove(r)
                    runs = list(e.iter(qn("w:r"))); i = runs.index(new) + 1; continue
            i += 1
        for fs in list(e.iter(qn("w:fldSimple"))):
            if "STYLEREF" in (fs.get(qn("w:instr")) or ""):
                r = fs.makeelement(qn("w:r"), {}); t = r.makeelement(qn("w:t"), {}); t.text = label; r.append(t); fs.addprevious(r); fs.getparent().remove(fs)
    hl = [x for x in body.iter(qn("w:highlight"))]
    for x in hl: x.getparent().remove(x)
    print("R10 edits applied; chapters counted:", chap_no, "| highlights removed:", len(hl))
