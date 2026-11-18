"""The team's concept design report (R8-MH) brought to the final design of the sewer network (engineer, 2026-11-18):
edited on a copy, in the document's own styles, captions and page layout, the rest left as the team wrote it.
  Chapter 3  gradients and self-cleansing (the 0.75 % limit and why), depth and pumping (lift and pumping stations),
             station sizing on the design-year peak;
  Chapter 6  the seven options replaced by the four scenarios SC1-SC4: method, design year, network, plants, pumping and
             lift stations, maps, the team's treated effluent subsections of the matching options kept, comparison;
  Appendix D depth maps and quantities of the four scenarios.
Then Word updates the fields and the contents and exports the PDF, and the clean-room gate scans it.
Usage: python build_report.py      Writes R9/Ibri_Concept_Design_Report_R9.docx and .pdf"""
import os, sys, copy, shutil, re
from docx import Document
from docx.shared import Cm, Pt
from docx.oxml.ns import qn
import docx.text.paragraph as P, docx.table as Tb
from docx.enum.text import WD_BREAK
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import facts_final as F
SRC = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\temp\recent updates by the team\Ibri_Concept_Design_Report_R8-MH.docx"
REV = "R9"; OUT = os.path.join(HERE, REV); os.makedirs(OUT, exist_ok=True)
DOCX = os.path.join(OUT, f"Ibri_Concept_Design_Report_{REV}.docx"); PDF = DOCX.replace(".docx", ".pdf")
IMG = os.path.join(HERE, "img")
shutil.copy(SRC, DOCX)
d = Document(DOCX); body = d.element.body
f0 = lambda v: f"{v:,.0f}"; f1 = lambda v: f"{v:,.1f}"


# ------------------------------------------------------------------ the document's own furniture
def paras():
    return [P.Paragraph(e, d) for e in body.iterchildren() if e.tag == qn("w:p")]
def find(text, style=None, start=True):
    for p in paras():
        t = p.text.strip(); s = p.style.name if p.style is not None else ""
        if (t.startswith(text) if start else t == text) and (style is None or s.startswith(style)): return p
    raise KeyError(text)
def level(e):
    if e.tag != qn("w:p"): return 99
    s = P.Paragraph(e, d).style; n = s.name if s is not None else ""
    return int(n[-1]) if n.startswith("Heading") and n[-1].isdigit() else 99
def section(head):
    """The heading's element and everything after it up to the next heading of the same or a higher level."""
    lv = level(head._p); out = [head._p]; e = head._p.getnext()
    while e is not None and level(e) > lv and e.tag != qn("w:sectPr"): out.append(e); e = e.getnext()
    return out
caps = {k: next(copy.deepcopy(p._p) for p in paras() if p.style is not None and p.style.name == "Caption"
                and p.text.strip().startswith(k) and p._p.findall(".//" + qn("w:fldChar"))) for k in ("Figure", "Table")}
sects = [e for e in body.iter(qn("w:sectPr"))]
def pg(s): x = s.find(qn("w:pgSz")); return int(x.get(qn("w:w"))), int(x.get(qn("w:h")))
SECT_A4 = copy.deepcopy(next(s for s in sects if pg(s)[0] < pg(s)[1]))
SECT_A3 = copy.deepcopy(next(s for s in sects if pg(s)[0] > 20000))
def avail(s):
    w, h = pg(s); m = s.find(qn("w:pgMar"))
    return (w - int(m.get(qn("w:left"))) - int(m.get(qn("w:right")))) / 567.0, (h - int(m.get(qn("w:top"))) - int(m.get(qn("w:bottom")))) / 567.0
A3W, A3H = avail(SECT_A3)


class Out:
    """Collects new elements and inserts them, in order, before an anchor."""
    def __init__(self, anchor): self.anchor = anchor
    def put(self, e): self.anchor.addprevious(e); return e
    def p(self, text, style="Normal"):
        x = d.add_paragraph(text, style); return self.put(x._p)
    def h(self, text, lv): return self.p(text, f"Heading {lv}")
    def caption(self, kind, text):
        c = copy.deepcopy(caps[kind]); runs = c.findall(qn("w:r")); ends = [i for i, r in enumerate(runs) if r.find(qn("w:fldChar")) is not None
                                                                         and r.find(qn("w:fldChar")).get(qn("w:fldCharType")) == "end"]
        for r in runs[ends[-1] + 1:]: c.remove(r)
        r = copy.deepcopy(runs[0]); [r.remove(t) for t in r.findall(qn("w:t"))]
        t = r.makeelement(qn("w:t"), {}); t.text = ".   " + text; t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve"); r.append(t); c.append(r)
        for s in c.iter(qn("w:sectPr")): s.getparent().remove(s)
        return self.put(c)
    def table(self, head, rows, widths=None, caption=None):
        if caption: self.caption("Table", caption)
        t = d.add_table(rows=1, cols=len(head)); t.style = "List Table 4 Accent 1"
        for i, h in enumerate(head): t.rows[0].cells[i].text = str(h)
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r): cells[i].text = str(v)
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths): row.cells[i].width = Cm(w)
        self.put(t._tbl); self.p("")
    def sect(self, tpl):
        x = d.add_paragraph(); x._p.get_or_add_pPr().append(copy.deepcopy(tpl)); return self.put(x._p)
    def maps(self, items):
        """Maps on their own A3 landscape pages: the portrait section ends here, one map and caption a page."""
        self.sect(SECT_A4)
        for i, (path, cap) in enumerate(items):
            if isinstance(path, str):                         # a new map from file
                w = min(A3W - 0.5, (A3H - 2.2) * 2338 / 1653)
                x = d.add_paragraph(); x.alignment = 1; x.add_run().add_picture(path, width=Cm(w)); self.put(x._p)
            else: self.put(path)                              # a figure kept from the team's chapter (its image paragraph)
            self.caption("Figure", cap)
            if i < len(items) - 1:
                b = d.add_paragraph(); b.add_run().add_break(WD_BREAK.PAGE); self.put(b._p)
        self.sect(SECT_A3)


def remove(els):
    for e in els:
        if e.getparent() is not None: e.getparent().remove(e)


def replace_text(p, text):
    for r in p.runs[1:]: r._r.getparent().remove(r._r)
    if p.runs: p.runs[0].text = text
    else: p.add_run(text)


# ------------------------------------------------------------------ facts
def dest(r, plants):
    """Where a station discharges, in the report's names."""
    s = str(r.pumps_to)
    if s == "nan": return plants[r.name]["stp"]
    if s.startswith("STP at "): p = s[7:]; return f"{plants[p]['stp']} (inlet {p})"
    return s


C = {sc: F.case(sc) for sc in F.SCEN}
Y = {y: F.case("SC1", y) for y in F.YEARS}
c1 = C["SC1"]
pct = lambda a, b: f"{a / b * 100:.1f} %"

# ------------------------------------------------------------------ Chapter 3: gradients, self-cleansing, depth, stations
p = find("For concept design, sewer gradients are based on the guideline minimum")
replace_text(p, "Each sewer is laid at the minimum gradient of its size given by PAM-GUD-203 Table 11 (p. 29), summarized in the table "
             "below. A sewer larger than 200 mm is then steepened where necessary until it reaches the self-cleansing velocity of 0.75 m/s "
             "at the 2031 peak flow, the early-year flow at which deposits are most likely (p. 27). The steepening is applied as one gradient "
             "along each street run, so that successive pipes in a street fall evenly, and it is limited to 0.75 % for the reasons given "
             "below. Sewers of 200 mm, which carry the small flows of the upstream ends of the network, are laid at their minimum gradient "
             "and assessed by the tractive force criterion.")
o = Out(find("During the meeting held on 16 September 2026")._p.getnext())
o.h("Gradient limit for self-cleansing", 4)
o.p(f"Three gradient limits were assessed on the network of Scenario SC1 designed for {F.BASE}: 0.50 %, 0.75 % and 1.00 %. A steeper "
    "limit brings more sewers to the self-cleansing velocity but deepens the lower reaches of a catchment, where a lift station may "
    "then be needed. Each limit was therefore combined with the station arrangement that keeps the network within the depth criteria "
    "below with the fewest stations.")
o.table(["Gradient limit", "Pumping and lift stations", "Of which lift stations added by steepening",
         "Sewers above 200 mm reaching 0.75 m/s at the 2031 peak", "Not reaching it"],
        [[x["limit"], x["stations"], x["added"], f"{f1(x['km_big'] - x['km_under'])} km ({pct(x['km_big'] - x['km_under'], x['km_big'])})",
          f"{f1(x['km_under'])} km ({pct(x['km_under'], x['km_big'])})"] for x in F.LIMITS],
        caption=f"Gradient limits compared, Scenario SC1 designed for {F.BASE}")
a, b, c = F.LIMITS
o.p(f"A limit of 0.75 % is adopted. Compared with 0.50 %, it brings a further {f1(a['km_under'] - b['km_under'])} km of sewer to the "
    f"self-cleansing velocity in the early years for {b['stations'] - a['stations']} more stations, about "
    f"{(a['km_under'] - b['km_under']) / (b['stations'] - a['stations']):.0f} km a station. The step from 0.75 % to 1.00 % gains "
    f"{f1(b['km_under'] - c['km_under'])} km for a further {c['stations'] - b['stations']} stations, about "
    f"{(b['km_under'] - c['km_under']) / (c['stations'] - b['stations']):.0f} km a station, and places lift stations at short intervals "
    f"along the steepened runs. At 0.75 % the network needs {b['stations']} stations, the same number as when every sewer is laid at its "
    "minimum gradient, because the lift stations it adds are offset by stations that a slightly deeper outfall makes unnecessary. "
    f"The highest velocity at the design flow is {c1['v_max']:.2f} m/s, well below the maximum of 3.0 m/s (p. 27).")
u = c1["under_by_size"]
o.p(f"Of the {f1(c1['km_under31'])} km that remains below 0.75 m/s at the 2031 peak, {f1(u.get(250, 0))} km is 250 mm sewer carrying "
    f"a few litres a second. Its flow grows slowly: {f1(c1['km_under36'])} km is still below the velocity at the 2036 peak. These "
    "sewers are listed for periodic flushing in the early years of operation.")

p = find("For concept design, a cover depth of 12 m is adopted as the threshold")
replace_text(p, "For concept design, a depth to invert of 12 m is the threshold at which the flow is lifted rather than the sewer deepened "
             "further. Where a run stays deeper than 12 m all the way to its outfall, a station is placed at the last manhole of the run "
             "that is 12 m deep or less, and the flow is lifted to the next manhole, from which the sewer resumes at the minimum cover. "
             "Runs that dip below 12 m and return above it within the same catchment are retained.")
p2 = find("Localized sections exceeding 12 m cover are retained")
replace_text(p2, "Where a modest additional depth removes a station, the deeper arrangement is adopted: a station or an outfall may reach "
             "about 15 m to invert and an individual manhole about 16.5 m. A station is not placed within the last few hundred metres above "
             "an outfall, where it would duplicate that outfall's station rather than relieve the network. During preliminary design, each "
             "station and every reach deeper than 12 m will be reviewed using verified survey levels and a comparison of deep excavation "
             "costs with the capital and operating costs of pumping.")
o = Out(p2._p.getnext())
o.p("Two kinds of station result. A pumping station conveys the flow of its catchment through a force main to another catchment or to "
    "a treatment plant. A lift station raises the flow of a deep catchment to a nearby manhole, within one standard manhole spacing "
    "(PAM-GUD-203 Table 12, p. 30). The guideline treats both as pumping stations of Type 1 to 3 by design flow (pp. 40–41), and both "
    "are designed to the criteria below.")
p = find("Pumping stations are sized to accommodate the projected 2070 peak sewage flow")
replace_text(p, f"Pumping and lift stations are sized for the peak sewage flow of the design year ({F.BASE}) from their service areas, "
             "together with the infiltration allowance for the contributing sewer network. The flow a station delivers to another "
             "catchment is carried downstream at that peak.")

# ------------------------------------------------------------------ Chapter 6: from seven options to four scenarios
h1 = find("CONCEPT DESIGN OPTIONS", "Heading 1")
nxt = h1._p.getnext()
while level(nxt) != 1: nxt = nxt.getnext()
chapter = []; e = h1._p
while e is not nxt: chapter.append(e); e = e.getnext()
# kept from the team's chapter: treatment locations, the TE demands and customers, and each matching option's TE subsection
def take(head_text, lv=3, stop_at_image=True):
    hp = next(P.Paragraph(x, d) for x in chapter if x.tag == qn("w:p") and P.Paragraph(x, d).text.strip().startswith(head_text) and level(x) == lv)
    els = []
    for x in section(hp):
        if stop_at_image and x.findall(".//" + qn("a:blip")): break
        els.append(copy.deepcopy(x))
    for x in els:
        for s in list(x.iter(qn("w:sectPr"))): s.getparent().remove(s)
    return els
def figure_of(cap_text):
    """A kept figure of the team's chapter: its image paragraph and its caption."""
    for i, x in enumerate(chapter):
        if x.tag == qn("w:p") and P.Paragraph(x, d).text.strip().startswith("Figure") and cap_text in P.Paragraph(x, d).text:
            j = i - 1
            while not chapter[j].findall(".//" + qn("a:blip")): j -= 1
            img = copy.deepcopy(chapter[j])
            for s in list(img.iter(qn("w:sectPr"))): s.getparent().remove(s)
            return img, P.Paragraph(x, d).text.split(".", 1)[-1].strip() if "." in P.Paragraph(x, d).text[:12] else P.Paragraph(x, d).text
    raise KeyError(cap_text)
keep_loc = take("Treatment Locations and Service Areas")
keep_te = take("Treated Effluent Demands")
keep_te = [x for x in keep_te if not (x.tag == qn("w:p") and "Wastewater Flow by Subnetwork" in P.Paragraph(x, d).text)]
# drop the per-subnetwork flow table of the options (superseded by the plant flows below) and its notes
cut = []
for i, x in enumerate(keep_te):
    if x.tag == qn("w:tbl") and i > 0 and any("Infiltration: An allowance" in P.Paragraph(y, d).text for y in keep_te[i + 1:i + 3] if y.tag == qn("w:p")):
        cut += [x] + [y for y in keep_te[i + 1:i + 3] if y.tag == qn("w:p") and ("Infiltration: An allowance" in P.Paragraph(y, d).text or "Outside the 24" in P.Paragraph(y, d).text)]
keep_te = [x for x in keep_te if x not in cut]
te = {sc: take(f"OP {n} – TE Network Configuration") for sc, n in (("SC1", 1), ("SC2", 2), ("SC3", 3))}
te_fig = {sc: figure_of(f"OPTION {n}- TE Network General Layout") for sc, n in (("SC1", 1), ("SC2", 2), ("SC3", 3))}
stp_fig = figure_of("Locations of the Proposed Sewage Treatment Plants"); cust_fig = figure_of("Locations of the Existing and Potential TE Customers")
remove(chapter)

o = Out(nxt)
o.h("CONCEPT DESIGN SCENARIOS", 1)
o.h("Introduction", 2)
o.p("This chapter presents the four concept design scenarios for the wastewater collection network, including trunk sewers, pumping and "
    "lift stations, force mains, STPs and TE lines. It describes how the scenarios were developed, the design year, and the criteria "
    "used to compare their technical performance.")
o.h("Scenario Development Methodology", 2)
o.h("Basis of Assessment", 3)
o.p("The scenarios assess alternative arrangements for collecting, conveying and treating wastewater across the Project area. A minimum "
    "of three alternatives is required for the wastewater network, TE network and treatment facilities. PAM-GUD-201 requires alternatives "
    "to be compared on an equivalent basis for functionality, reliability and redundancy, considering environmental sustainability, "
    "international best practice and established technologies available in Oman.")
o.p("Four scenarios are assessed, built on three treatment sites: STP-1, STP-2 and STP-5. Treatment location is the principal variable "
    "because it determines the allocation of flows, trunk sewer capacities, pumping requirements and treatment capacity at each site.")
o.table(["Scenario", "Treatment", "Plant inlet stations"],
        [[sc, F.SCEN[sc][0], ", ".join(f"{v['stp']} ({k})" for k, v in C[sc]["plants"].items())] for sc in F.SCEN], caption="The four scenarios")
o.h("Network Configuration and Modelling", 3)
o.p(f"The collection network comprises about {f0(c1['sewer_km'])} km of gravity sewers and {f0(c1['manholes'])} manholes, common to the "
    f"four scenarios. The sewers drain to {len(set(c1['stations'].system))} pumping systems, each named after its pumping station, P1 to "
    f"P{len(set(c1['stations'].system))}. A pumping station conveys the flow of its system through a force main to another system or to a "
    "treatment plant; where a system ends at a treatment site, its station is the inlet pumping station of the plant. Within a system, "
    "lift stations raise the flow of a deep catchment to a nearby manhole; a lift station takes the name of its system and a sequence "
    "number, P4L1 being the first lift station of system P4. Manholes and pipes take the name of the station they drain to and are "
    "numbered from the station upstream, the main line first: P4-M12, P4L1-M3.")
o.p("The network is designed in SewerGEMS. Sewers are sized for the peak flow of the design year, with the infiltration allowance, so "
    "that the depth of flow does not exceed 0.65 of the diameter up to 355 mm and 0.50 above (PAM-GUD-203, p. 27), and laid as set out "
    "in Chapter 3. The collection sewers follow common street corridors in all scenarios; the scenarios differ in the routing of flows "
    "between systems, the diameters of the sewers carrying combined flows, the stations and force mains, and the treatment facilities.")
o.maps([(os.path.join(IMG, "map_pumping_systems.png"), "The pumping systems of the network, their pumping and lift stations")])
o.h("Design Year and Self-Cleansing", 3)
o.p("The design year is chosen so that the network is large enough for the long-term flow while its sewers still carry enough flow in "
    "the early years to keep themselves clean. Each scenario was designed for 2051, 2056 and 2061 and tested for self-cleansing at the "
    "2031 peak flow, the start of operation, and at the 2036 peak. The three designs of Scenario SC1 are compared below; the other "
    "scenarios give the same pattern.")
o.table(["Design year", "Sewers above 200 mm", "Below 0.75 m/s at the 2031 peak", "Still below at the 2036 peak", "Pumping / lift stations",
         "Manholes deeper than 12 m", "Network capital cost, million OMR"],
        [[y, f"{f1(Y[y]['km_big'])} km", f"{f1(Y[y]['km_under31'])} km ({pct(Y[y]['km_under31'], Y[y]['km_big'])})", f"{f1(Y[y]['km_under36'])} km",
          f"{Y[y]['pumps']} / {Y[y]['lifts']}", f0(Y[y]["mh_over12"]), f1(Y[y]["cost"]["total"] / 1e6)] for y in F.YEARS],
        caption="Design years compared, Scenario SC1")
d51, d56, d61 = Y["2051"], Y["2056"], Y["2061"]
o.p(f"{F.BASE} is adopted as the design year. It is 25 years after the start of operation, the design horizon of the network, and in "
    f"the {F.BASE} design {pct(d56['km_big'] - d56['km_under31'], d56['km_big'])} of the sewers larger than 200 mm reach the self-cleansing "
    f"velocity at the 2031 peak. A 2051 design self-cleanses slightly better ({pct(d51['km_big'] - d51['km_under31'], d51['km_big'])}) and "
    f"costs about {f1((d56['cost']['total'] - d51['cost']['total']) / 1e6)} million OMR less, but its sewers would run above their design "
    f"depth of flow before the end of the design horizon. A 2061 design adds about {f1((d61['cost']['total'] - d56['cost']['total']) / 1e6)} "
    f"million OMR for flows that arrive after the design horizon and leaves {pct(d61['km_under31'], d61['km_big'])} of these sewers below the "
    "self-cleansing velocity in the early years. The station arrangement is the same in the three designs.")
o.h("Pumping Stations and Lift Stations", 3)
o.p("The stations follow the depth criteria of Chapter 3: a station is introduced where a run would otherwise stay deeper than 12 m to "
    "its outfall, and stations are removed where a modest additional depth allows it. Where the outfall of a system ends within one "
    "standard manhole spacing of a manhole in the next system and at a depth of 12 m or less, it joins that system by gravity and no "
    "station is needed. Every station is typed by its design flow (PAM-GUD-203, pp. 40–41), and its force main is sized for 1.0 to 2.5 "
    "m/s (p. 50).")
for x in keep_loc: o.put(x)
for x in keep_te: o.put(x)


def kept_maps(items):
    o.sect(SECT_A4)
    for i, ((img, cap)) in enumerate(items):
        o.put(img); o.caption("Figure", cap)
        if i < len(items) - 1:
            b = d.add_paragraph(); b.add_run().add_break(WD_BREAK.PAGE); o.put(b._p)
    o.sect(SECT_A3)


kept_maps([stp_fig, cust_fig])
TITLE = {"SC1": "Treatment at STP-1 Only", "SC2": "Treatment at STP-2 Only", "SC3": "Treatment at STP-1 and STP-5", "SC4": "Treatment at STP-2 and STP-5"}
for sc in F.SCEN:
    f = C[sc]; n = sc[-1]; st = f["stations"]; net = st[st.kind != "plant inlet"]; plants = f["plants"]
    o.h(f"SCENARIO {n}: {TITLE[sc]}", 2)
    stps = [v["stp"] for v in plants.values()]
    o.p(f"Scenario {sc} conveys the wastewater of the Project area to {' and '.join(stps)}. Gravity sewers collect the wastewater within each "
        "pumping system and convey it to its station; pumping stations and force mains transfer the flows between systems, combining "
        f"them for conveyance to the treatment plant{'s' if len(stps) > 1 else ''}.")
    o.h(f"{sc} – Wastewater Network Configuration", 3)
    o.p(f"The network is sized for the {F.BASE} peak flows, including infiltration, and checked at the 2031 and 2036 peaks for self-cleansing. "
        f"It comprises {f0(f['sewer_km'])} km of sewers, {f1(f['km_big'])} km of them larger than 200 mm, of which "
        f"{pct(f['km_big'] - f['km_under31'], f['km_big'])} reach 0.75 m/s at the 2031 peak. Of the {f0(f['manholes'])} manholes, "
        f"{f0(f['mh_over12'])} are deeper than 12 m to invert; the deepest is {f['deepest']['depth']:.1f} m.")
    o.table(["Diameter (mm)", "Length (m)"], [[k, f0(v * 1000)] for k, v in sorted(f["km_by_size"].items(), key=lambda kv: int(kv[0]))]
            + [["Total", f0(f["sewer_km"] * 1000)]], caption=f"Scenario {sc} – Wastewater Network Pipes Arrangement")
    o.h(f"{sc} – Treatment Facility", 3)
    if len(plants) == 1:
        (k, v), = plants.items()
        o.p(f"{v['stp']} receives an average wastewater flow of {f0(v['avg_m3d']['2031'])} m³/d in 2031, increasing to "
            f"{f0(v['avg_m3d'][F.BASE])} m³/d in {F.BASE}. The incoming sewer reaches the plant at a depth of about {v['inlet_depth_m']:.1f} m "
            f"below ground, and the inlet pumping station {k} lifts a design peak of {f0(st.set_index('name').at[k, 'duty_ls'])} l/s.")
    else:
        o.p(f"{sc} divides treatment between {' and '.join(stps)}, with projected average inflows of "
            + " and ".join(f"{f0(v['avg_m3d'][F.BASE])} m³/d" for v in plants.values()) + f" respectively in {F.BASE}.")
        o.table(["Treatment Facility", "Inlet station", "Average inflow 2031 (m³/d)", f"Average inflow {F.BASE} (m³/d)", "Incoming sewer depth (m)"],
                [[v["stp"], k, f0(v["avg_m3d"]["2031"]), f0(v["avg_m3d"][F.BASE]), f"{v['inlet_depth_m']:.1f}"] for k, v in plants.items()],
                caption=f"Scenario {sc} – Treatment Facilities")
    o.h(f"{sc} – Pumping Stations and Lift Stations", 3)
    lg, lf = f["largest"], f["longest"]
    o.p(f"The scenario requires {f['pumps']} pumping stations and {f['lifts']} lift stations, with an aggregate duty pump power of "
        f"{f0(f['kw_network'])} kW, excluding the plant inlet station{'s' if len(plants) > 1 else ''}. The largest station, {lg['name']}, "
        f"handles {f0(lg['duty_ls'])} l/s; the longest force main extends {f1(lf['force_main_m'] / 1000)} km from {lf['name']}. Pumping "
        f"energy is about {f0(f['mwh_2031'])} MWh a year in 2031 and {f0(f['mwh_design'])} MWh in {F.BASE}.")
    o.table(["Station", "Kind", "Type", "Discharges to", "Incoming sewer depth (m)", "Duty (l/s)", "Head (m)", "Power (kW)", "Force main (mm × m)"],
            [[r.name, r.kind, r.g203_type, dest(r, plants), f"{r.outfall_depth_m:.1f}", f0(r.duty_ls),
              f0(r.head_m), f1(r.kw), f"{int(r.force_main_dn)} × {f0(r.force_main_m)}" if r.force_main_m > 0 else "-"] for r in st.itertuples()],
            caption=f"Scenario {sc} – Pumping Stations and Lift Stations")
    if sc in te:
        hd = te[sc][0]; replace_text(P.Paragraph(hd, d), f"{sc} – TE Network Configuration")
        for x in te[sc]:
            if x.tag == qn("w:p"):
                pp = P.Paragraph(x, d)
                for old, new in ((f"Option {sc[-1]}", f"Scenario {sc}"), (f"OP{sc[-1]}", sc), (f"OPTION {sc[-1]}", f"SCENARIO {sc[-1]}")):
                    if old in pp.text: replace_text(pp, pp.text.replace(old, new))
            o.put(x)
    tag = f"{sc}_{F.BASE}"
    o.maps([(os.path.join(IMG, f"map_{tag}_zones.png"), f"Scenario {sc}: the sewers by the plant they drain to"),
            (os.path.join(IMG, f"map_{tag}_network.png"), f"Scenario {sc}: sewers, pumping and lift stations and force mains"),
            (os.path.join(IMG, f"map_{tag}_selfcleansing.png"), f"Scenario {sc}: self-cleansing of the sewers at the 2031 peak")]
           + ([(te_fig[sc][0], f"Scenario {sc}: TE Network General Layout")] if sc in te_fig else []))     # one landscape run

o.h("Comparison of Scenarios", 2)
o.p(f"The four scenarios share the collection sewers and differ in where the flow is treated. The table compares the sewer network of each "
    f"scenario designed for {F.BASE}: quantities, stations, energy and the capital cost of the network at the rates of the cost estimate "
    "(sewers, manholes, force mains, pumping and lift stations). Treatment, treated effluent and operating costs are compared in the "
    "financial analysis.")
rows = [("Gravity sewers (km)", lambda f: f0(f["sewer_km"])), ("Sewers above 200 mm (km)", lambda f: f1(f["km_big"])),
        ("Above 200 mm reaching 0.75 m/s at the 2031 peak", lambda f: pct(f["km_big"] - f["km_under31"], f["km_big"])),
        ("Pumping stations / lift stations", lambda f: f"{f['pumps']} / {f['lifts']}"), ("Force mains (km)", lambda f: f1(f["force_main_km"])),
        ("Network pumping duty (kW)", lambda f: f0(f["kw_network"])), ("Plant inlet pumping duty (kW)", lambda f: f0(f["kw_plant_inlets"])),
        (f"Pumping energy 2031 / {F.BASE} (MWh/yr)", lambda f: f"{f0(f['mwh_2031'])} / {f0(f['mwh_design'])}"),
        ("Manholes deeper than 12 m", lambda f: f0(f["mh_over12"])),
        ("Sewers (million OMR)", lambda f: f1(f["cost"]["sewers"] / 1e6)), ("Manholes (million OMR)", lambda f: f1(f["cost"]["manholes"] / 1e6)),
        ("Force mains (million OMR)", lambda f: f1(f["cost"]["force_mains"] / 1e6)), ("Pumping and lift stations (million OMR)", lambda f: f1(f["cost"]["stations"] / 1e6)),
        ("Sewer network, total (million OMR)", lambda f: f1(f["cost"]["total"] / 1e6))]
o.table(["Item"] + list(F.SCEN), [[a] + [fn(C[sc]) for sc in F.SCEN] for a, fn in rows], caption=f"The sewer network of the four scenarios, {F.BASE} design")
lo = min(F.SCEN, key=lambda s: C[s]["cost"]["total"]); hi = max(F.SCEN, key=lambda s: C[s]["cost"]["total"])
o.p(f"The sewer network of {lo} costs least, {f1(C[lo]['cost']['total'] / 1e6)} million OMR, and that of {hi} most, "
    f"{f1(C[hi]['cost']['total'] / 1e6)} million OMR. A plant at STP-2 requires the flow of system P1 to be pumped to it "
    f"({f0(C['SC2']['largest']['duty_ls'])} l/s in SC2), which raises the network pumping duty from {f0(C['SC1']['kw_network'])} kW in SC1 "
    f"to {f0(C['SC2']['kw_network'])} kW. A second plant at STP-5 shortens the transfers and lowers both the duty and the cost.")

# ------------------------------------------------------------------ the glossary: the names of the network
for tb in d.tables:
    for row in tb.rows:
        if row.cells[0].text.strip() == "O1 to O24":
            replace_text(row.cells[0].paragraphs[0], f"P1 to P{len(set(c1['stations'].system))}")
            replace_text(row.cells[1].paragraphs[0], "The pumping stations of the pumping systems of the network; a plant inlet station takes "
                         "the number of the system that ends at the plant. A lift station takes the name of its system and a sequence number, "
                         "as P4L1; a manhole or a pipe takes the name of the station it drains to and its number, as P4-M12 or P4L1-P3")

# ------------------------------------------------------------------ Appendix D: depth and quantities of the four scenarios
hd = find("Appendix D.", "Heading 1"); old = section(hd)[1:]
o = Out(old[-1].getnext() if old else hd._p.getnext()); remove(old)
o.p(f"This appendix gives, for each scenario designed for {F.BASE}, the depth of the sewers to invert, the length of sewer in each depth "
    "band and the manholes in each depth band. The deepest manhole of each run deeper than 12 m is shown on the maps.")
for sc in F.SCEN:
    f = C[sc]; bands = ["up to 3 m", "3 to 6 m", "6 to 9 m", "9 to 12 m", "12 to 15 m", "over 15 m"]
    o.table(["Depth to invert", "Sewer length (km)", "Manholes"], [[b, f1(f["km_by_depth"].get(b, 0)), f0(f["manholes_by_depth"].get(b, 0))] for b in bands]
            + [["Total", f1(f["sewer_km"]), f0(f["manholes"])]], caption=f"Scenario {sc}: sewers and manholes by depth to invert")
o.maps([(os.path.join(IMG, f"map_{sc}_{F.BASE}_depth.png"), f"Scenario {sc}: depth of the sewers to invert") for sc in F.SCEN])
d.save(DOCX)
print("saved", DOCX)
