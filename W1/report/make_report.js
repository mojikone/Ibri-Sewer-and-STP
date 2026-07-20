// W1 Concept Screening Report R0 — neutral styling (GAP-4: sample report pending)
const fs = require("fs");
const path = require("path");
const csvP = { parse: (buf) => String(buf).trim().split(/\r?\n/).map((l) => l.split(",")) };
const D = require("docx");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow,
  TableCell, WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, TableOfContents,
  Footer, Header, PageNumber, LevelFormat, PageOrientation,
} = D;

const W = "D:\\Mojtaba\\Renardet\\2621 Ibri Sewer STP\\Hydraulic\\Claude\\W1";
const img = (n) => fs.readFileSync(path.join(W, "img", n));
const map = (n) => fs.readFileSync(path.join(W, "img", "maps", n));

const BLUE = "1F4E79", GREY = "D9D9D9", LGREY = "F2F2F2";
const cell = (t, { b = false, sh = null, w = 1500, size = 18 } = {}) =>
  new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: sh ? { type: ShadingType.CLEAR, fill: sh } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ children: [new TextRun({ text: String(t), bold: b, size })] })],
  });
const tbl = (headers, rows, widths) =>
  new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, { b: true, sh: GREY, w: widths[i] })) }),
      ...rows.map((r, k) => new TableRow({ children: r.map((c, i) => cell(c, { w: widths[i], sh: k % 2 ? LGREY : null })) })),
    ],
  });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 120 }, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 }, children: [new TextRun(t)] });
const P = (t, opts = {}) => new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.JUSTIFIED, children: [new TextRun({ text: t, size: 20, ...opts })] });
const B = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: t, size: 20 })] });
const CAP = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const IMG = (buf, wpx, hpx) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ data: buf, type: "png", transformation: { width: wpx, height: hpx } })] });
const MAPIMG = (n) => IMG(map(n), 640, 452); // A4 landscape maps scaled to text width

// zone flows
const zf = csvP.parse(fs.readFileSync(path.join(W, "report", "zone_flows.csv")), { columns: false, skip_empty_lines: true });
const zrows = zf.slice(1).map((r) => [r[0], r[1], r[6], r[10], r[11], r[12], r[13]]);

const doc = new Document({
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", style: { paragraph: { indent: { left: 360, hanging: 200 } } } }] }] },
  styles: {
    default: { document: { run: { font: "Calibri", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, color: BLUE }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: BLUE }, paragraph: { outlineLevel: 1 } },
    ],
  },
  features: { updateFields: true },
  sections: [
    { // cover
      properties: {},
      children: [
        new Paragraph({ spacing: { before: 2500 } }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri", bold: true, size: 40, color: BLUE })] }),
        new Paragraph({ spacing: { before: 300 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Client: Nama Water Services (NWS / OWWSC)", size: 24 })] }),
        new Paragraph({ spacing: { before: 1200 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "CONCEPT SCREENING REPORT", bold: true, size: 56 })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Pre-Kickoff GIS Assessment — Working Set W1, Revision R0", size: 26 })] }),
        new Paragraph({ spacing: { before: 2200 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Renardet S.A. & Partners  |  Project 2621", size: 22 })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "20 July 2026", size: 22 })] }),
        new Paragraph({ spacing: { before: 700 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Screening-grade outputs based on uncontrolled data (TOR §H.14). Not for design. Report styling provisional pending sample report (GAP-4).", italics: true, size: 16, color: "990000" })] }),
      ],
    },
    {
      properties: {},
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "Ibri Sewer, TE & STP — Concept Screening (W1/R0)", size: 14, color: "777777" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 14, color: "777777" })] })] }) },
      children: [
        H1("Table of Contents"),
        new TableOfContents("TOC", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({ children: [new PageBreak()] }),

        H1("1. Introduction"),
        P("Nama Water Services (NWS/OWWSC) intends to design and construct wastewater, treated-effluent (TE) networks and STP capacity for Ibri Wilayat (Tender T/2719110/2025). The objective is to verify the RG Masterplan, determine the ultimate sewage flow for a design horizon of project completion + 25 years (or saturation), and deliver concept, preliminary and detailed designs and tenders (TOR §3)."),
        P("This report is a pre-kickoff concept screening prepared from the client-provided information folder. Per TOR §H.14 such data is indicative only; every result herein is screening-grade and will be superseded by topographic survey, data collection and hydraulic modelling (SewerGEMS) during the concept stage. The terrain model used is a coarse DSM (surface model, includes buildings/vegetation); design-grade conclusions are expressly excluded."),
        H2("1.1 Design basis documents"),
        B("PAM-GUD-203 Wastewater Design Guidelines v1.0 (Rev 01) — primary standard, cited as p##."),
        B("PAM-GUD-201 General Design Guidelines v1.0 (Rev 01) — planning parameters, cited as G1-p##."),
        B("TOR Section 03 (Scope of Work), Tender T/2719110/2025."),

        H1("2. Scope Highlights Binding This Work"),
        tbl(["Item", "Requirement", "Ref"], [
          ["Gravity preference", "Gravity connection preferred; pumping only where gravity not realistic or too costly; both options to be considered", "TOR p10"],
          ["Topography", "Layout shall avoid pumping and utilise gravity as much as practicable using contour mapping", "TOR p12"],
          ["Coverage", "All plots within boundary (built, open, under construction) to be serviced", "TOR §H.2"],
          ["Options", "Minimum three options for WW network, TE network and each STP", "TOR p13, §H.18"],
          ["STP threshold", "STP preliminary design + EPC tender in consultant scope only if Phase I < 20,000 m3/d", "TOR p3, p5"],
          ["Model years", "Start (TBA), 2030, 2055 and ultimate; SewerGEMS/WaterGEMS deliverables", "TOR p14"],
          ["Inverted siphons", "To be avoided; last resort only", "TOR p12"],
        ], [1800, 6100, 1400]),

        H1("3. Design Criteria Applied (Standards Extract)"),
        H2("3.1 Gravity network hydraulics (PAM-GUD-203)"),
        tbl(["Criterion", "Value", "Ref"], [
          ["Design formula", "Colebrook-White (ks = 1.5 mm) or Manning; approved software", "p24"],
          ["Min self-cleansing velocity", "0.75 m/s at peak flow (0.90 preferred); tractive-force check at heads", "p26-27"],
          ["Max velocity", "3.0 m/s", "p27"],
          ["Depth of flow at peak", "d/D <= 0.65 (D<=350 mm); d/D <= 0.50 (D>350 mm)", "p27"],
          ["Min gradient (Table 11)", "DN200: 5.0 | DN315: 2.7 | DN500: 1.55 | DN700: 1.0 | DN>=900: 0.75 mm/m", "p29"],
          ["Cover", "Min 1.3 m to crown (0.5 m w/ concrete protection); max ~10-12 m, beyond -> pumping", "p33"],
          ["Manhole spacing", "100 m (DN200-315) to 200 m (>DN1400)", "p30"],
          ["Trunk main definition", "D > 800 mm, > 1,000 m without connections, upstream of STP/main PS", "p35"],
          ["Wadis", "Pipelines and chambers in wadis / washout areas to be avoided", "p30, p33"],
        ], [2600, 5300, 1400]),
        H2("3.2 Flow estimation parameters (PAM-GUD-201)"),
        tbl(["Parameter", "Value", "Ref"], [
          ["Population from plots", "plots x properties/plot x occupancy rate (NCSI)", "G1-p58"],
          ["Domestic consumption, Adh Dhahirah", "164 l/c/d (IMP 2024 baseline)", "G1-p60"],
          ["Non-domestic / governmental", "+22% / +14% of domestic LPCD", "G1-p60"],
          ["Return to sewer", "85% domestic & tanker; 54% non-domestic/governmental", "G1-p71"],
          ["Peak factor", "Peltier PfWW = 1.5 + 1/sqrt(Qm[l/s]) (cap 5.0); Merrimack alternative", "G1-p71-72"],
          ["Infiltration (new networks)", "720 L/d per km of sewer", "G1-p72"],
          ["STP design margin", "+10% operational safety allowance", "G1-p73"],
          ["STP organic load", ">= 60 g BOD5 and 80 g TSS /cap/day", "GUD-203 p74"],
        ], [2600, 5300, 1400]),

        H1("4. Study Area and Data"),
        P("Project boundary: 439.8 km2, single polygon (EPSG:32640). Within it, serviceable land use concentrates in one principal agglomeration around Ibri town plus satellite settlements. The existing Ibri STP lies at the south-west edge of town at ~327.6 m."),
        tbl(["Land use (in boundary)", "Plots", "Area (km2)"], [
          ["Residential", "43,722", "32.2"], ["Agriculture", "4,310", "36.8"], ["Governmental", "2,976", "16.3"],
          ["Commercial", "3,057", "2.4"], ["Industry", "466", "0.9"], ["Not classified", "3,991", "7.5"],
        ], [3600, 1900, 1900]),
        P("Data quality flags: NSA DEM is a coarse 4 m DSM (survey ongoing) — screening only. Road centreline dataset is regional (57,584 segments) with no functional-class attributes; dual carriageways are represented as two parallel polylines. Existing sewer as-built extents (Figure F2) are pending georeferencing."),
        MAPIMG("M1_study_area_landuse.png"),
        CAP("Map M1 — Study area, land use and existing STP (layout per project template)"),

        H1("5. Topography and Gravity Feasibility"),
        P("Ground elevations at 43,297 serviceable plots of the main agglomeration were sampled against the existing STP inlet area (327.6 m). The main town (median 374.3 m) commands a median straight-line available grade of 3.6 m/km towards the STP — several times the DN>=900 trunk minimum of 0.75 mm/m (p29). The main-trunk long section is monotonic with only 2-4 m local dips."),
        tbl(["Indicator", "Value"], [
          ["STP ground level", "327.6 m"],
          ["Main cluster median elevation", "374.3 m"],
          ["Median available grade to STP", "3.6 m/km (p25: 3.2)"],
          ["Plots with < 1.0 m/km available", "2.8%"],
          ["Plots below STP + 5 m", "5.4%"],
        ], [4700, 4700]),
        P("Conclusion: Ibri is a gravity town. The concept should target gravity conveyance to the existing STP location for ~95% of demand, with lifting confined to identified low or distant pockets (Section 8). This aligns with the TOR gravity preference and GUD-203 topography-driven siting."),
        IMG(img("trunk_profile.png"), 620, 225),
        CAP("Figure — Main trunk indicative long section (DSM ground; screening)"),
        MAPIMG("M2_slope.png"),
        CAP("Map M2 — Terrain slope classes (DSM)"),

        H1("6. Road Network Analysis"),
        P("The road dataset holds no hierarchy attributes, so arterials were derived: (i) edge betweenness centrality on the routed graph (top decile), and (ii) geometric detection of dual-carriageway pairs (parallel polylines 6-45 m apart, bearing within 12 deg) gated by centrality to reject residential grid false positives. Result: 3,375 arterial edges of 17,862, forming a connected skeleton of the dual-carriageway corridors and central links."),
        MAPIMG("M3_road_hierarchy.png"),
        CAP("Map M3 — Derived road hierarchy"),

        H1("7. Concept Trunk and Sewer Zones"),
        P("Trunk routing used least-cost paths on the road graph with arterial discounting (dual 0.55, arterial 0.70, local 1.00), which keeps the trunk on near-straight main-road corridors per the routing preference, dropping to internal roads only where connectivity requires. The trunk tree connects 20 zone outlets to the STP: main trunk 21.0 km, branches 114.3 km (135.3 km total)."),
        P("Zones are road-network territories: every network node is assigned to its nearest outlet by in-network distance, weighted by plot density — not by DEM watershed — so zone boundaries follow the road fabric and plot clusters as instructed, with terrain applied afterwards as the SLS screening constraint. Each zone drains to exactly one outlet on the trunk."),
        MAPIMG("M4_trunk_zones.png"),
        CAP("Map M4 — Concept trunk, zones, outlets and SLS candidates"),

        H1("8. Flow Estimation (Ultimate / Saturated)"),
        P("Flows follow the GUD-201 chain of Section 3.2 applied to all serviceable plots (TOR requires all plots serviced). Occupancy is a tagged assumption of 6.0 persons/housing unit and 1 property/plot pending NCSI figures [GAP-5]; totals scale linearly with it."),
        tbl(["Zone", "Plots", "Pop*", "Qadf (m3/d)", "PF", "Qpeak (m3/d)", "Sewer (km)"],
          zrows, [900, 1100, 1300, 1600, 900, 1600, 1300]),
        CAP("* Population at OR = 6.0 [GAP-5]. Qadf includes 720 L/d/km infiltration; PF = Peltier."),
        P("Totals: Qadf ~ 49,700 m3/d ultimate saturated (+10% STP margin -> ~54,700 m3/d); peak ~ 83,700 m3/d. Commercial implication: ultimate capacity far exceeds the 20,000 m3/d threshold of TOR p3 — STP Phase I sizing and phasing become the pivotal concept decision. A phased build-out (development-percentage per GUD-201 G1-p59) for 2030/2055 model years is required before any Phase I capacity is fixed; present-day connected flow will be a fraction of saturation."),

        H1("9. Lifting Stations vs New/Satellite STP"),
        H2("9.1 Screening method and results"),
        P("For every populated node, the invert profile to the STP was accumulated along the routing tree at Table 11 minimum gradients (diameter class from cumulative upstream plots), riding at minimum cover (1.3 m + pipe) where ground falls. Nodes whose route exceeds the 12 m maximum cover (p33) cannot reach the STP by gravity: 1,087 nodes (~8% of load), clustering into 125 candidate pockets; the ten largest hold 160-270 plots each at 13-22 m required depth."),
        H2("9.2 Criteria — when does a pocket justify an SLS, and when a satellite STP?"),
        tbl(["Trigger", "Criterion", "Source"], [
          ["SLS becomes necessary", "Excavation cost prohibitive / cover > 10-12 m", "GUD-203 p33"],
          ["SLS siting", "Hydraulics-driven; force-main energy-economic study; flooded suction", "GUD-203 p38"],
          ["Avoid SLS where possible", "Topography considerations to limit pumping (STP siting criterion f)", "GUD-203 p63"],
          ["Satellite/new STP candidate", "Remote cluster where trunk length and lift render conveyance LCC above local treatment LCC; STP >= Small category 500 m3/d viable", "GUD-203 p65; TOR 3-options"],
          ["Decentralised threshold (remote areas)", "Compact decentralised units allowed for remote areas per GUD-201 §8", "G1-p80-83"],
          ["Comparison metric", "Whole-life cost (CAPEX+OPEX/LCCA) across >= 3 options", "G1-p95-97; TOR p13"],
        ], [2600, 5300, 1400]),
        P("Applied to Ibri: the eastern satellite cluster (~1,144 plots at 31.7 km network distance, +164 m above STP) is the prime satellite-STP/decentralised candidate — conveyance there is a Small-STP-scale flow over a trunk longer than the whole main town system. The 125 in-town pockets are SLS-scale questions, to be rationalised (merged/eliminated) during concept design as local sewers re-route; screening deliberately over-detects."),

        H1("10. Wadi Crossings"),
        P("The concept trunk crosses mapped stream lines 108 times (7 on the main trunk). Binding criteria: DI pipe across crossing +15 m each side with restrained joints (G1-p86); min cover 2.0 m in soft soil (G1-p86) / 1.5 m at force-main crossings (p52); isolation + air valves both sides, washout at low point; no chambers or markers in wadi bed or embankments (G1-p86, p30); protection per PAM-STD-404; flood data (1:20/50/100) and MoAFWR approvals (G1-p85). Stream lines derive from the DSM and are indicative; crossing inventory to be re-based on survey."),
        MAPIMG("M5_wadi_crossings.png"),
        CAP("Map M5 — Trunk wadi crossings vs stream network"),

        H1("11. Open Gaps and Kickoff Questions"),
        B("GAP-4: sample report styling file empty — this report uses provisional styling."),
        B("GAP-5: NCSI occupancy rate and properties/plot — flows scale with it; request via NWS."),
        B("GAP-6: existing sewer as-built (Fig. F2) extents to be georeferenced; zones overlapping served areas to be verified."),
        B("GAP-7: existing Ibri STP capacity, headworks invert and spare capacity; integration old-new STP intent."),
        B("Model start year confirmation; 2030/2055/ultimate horizons; per-capita validation vs IMP (G1-p59)."),
        B("MoHUP land bank for new STP / SLS sites; F3 redesign-vs-new boundaries."),

        H1("12. Next Steps (W2)"),
        B("Rationalise SLS pockets and re-route local networks; derive 3 concept options (all-gravity-max, hybrid, satellite-STP east)."),
        B("Phased flow projection 2030/2055/ultimate once NCSI/IMP figures received; SewerGEMS model seed."),
        B("Georeference F2/F3; integrate existing network; STP phasing and land-take check (GUD-203 Tab 28 footprints)."),
        B("Restyle report per sample; populate NWS-format deliverable structure."),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(path.join(W, "report", "Ibri_Concept_Screening_W1_R0.docx"), b);
  console.log("written", b.length);
});
