"""Appendix C (the design criteria, with the guideline page of each) and Appendix D (the drawings).

The criteria are the guideline values the design applies, taken from the page-cited criteria document of W13
(W13/docs/design_criteria/build.py, each value read from the PDFs), keeping the guideline column only: the values that
are this design's own choices are in Section 1.5 and the departures in Section 3.1.1. References: G201, G202, G203 are
PAM-GUD-201, -202 and -203, revision 01; ToR is the Terms of Reference.
"""
import os

import doc as D
import facts_w17 as F

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

# (group, [(criterion, value, reference)])
CRITERIA = [
    ("Gravity sewers: hydraulics", [
        ("Design method", "Colebrook-White or Manning, in licensed software approved by Nama Water Services", "G203 p. 24"),
        ("Roughness, Colebrook-White", "1.5 mm for all pipe sizes and materials", "G203 pp. 24, 28"),
        ("Kinematic viscosity", "1.141 × 10⁻⁶ m²/s at 15 °C", "G203 p. 25"),
        ("Self-cleansing velocity", "0.75 m/s at peak flow; 0.90 m/s preferred", "G203 p. 26"),
        ("Maximum velocity", "3.0 m/s at the design depth of flow", "G203 pp. 27, 29"),
        ("Proportional depth at peak flow", "0.65 for diameters up to 350 mm; 0.50 above", "G203 p. 27, Table 10"),
        ("Minimum gradient", "The steeper of the self-cleansing and the minimum tractive force gradients",
         "G203 p. 27, §4.2.2.1"),
        ("Minimum gradient by diameter", "Table 11 of the guideline, secondary network", "G203 p. 29, Table 11"),
        ("Maximum gradient", "Governed by the maximum velocity of 3.0 m/s", "G203 p. 29"),
        ("Oversizing", "No pipe oversized to obtain a flatter gradient; uniform gradient between manholes", "G203 p. 29"),
        ("Construction tolerance", "Line and level within 20 mm of the contract, with no reverse gradient",
         "G203 p. 29, §4.3.1"),
        ("Early-development flows", "Flows below the design flow in the early years; more frequent inspection and "
         "cleansing in that period", "G203 p. 28, §4.2.6"),
    ]),
    ("Gravity sewers: pipes, cover and manholes", [
        ("Tertiary gradients", "Property connection sewer 3 % to 10 %; rider and lateral sewers 1 % to 10 %",
         "G203 p. 18, Table 5"),
        ("Minimum diameters", "Property connection OD 160 mm; lateral sewer OD 200 mm, at most 45 m long; main sewer "
         "OD 200 mm", "G203 p. 22, Table 6"),
        ("Materials, 350 mm and larger", "GRP, HDPE or lined reinforced concrete in open trench; GRP or HDPE trenchless",
         "G203 p. 22"),
        ("Trunk main", "Diameter over 800 mm and over 1,000 m without connections, upstream of the plant or a main "
         "pumping station", "G203 p. 35"),
        ("Trunk material above 600 mm", "GRP, lined reinforced concrete or profile-wall HDPE", "G203 p. 35, Table 14"),
        ("Minimum cover", "1.3 m to the crown", "G203 p. 33, §4.6.3"),
        ("Reduced cover", "Less than 1.3 m only with concrete protection; at least 0.5 m above the pipe and its "
         "protection", "G203 p. 33, §4.6.3"),
        ("Property connection cover", "600 mm minimum", "G203 p. 19"),
        ("Maximum cover", "About 10 to 12 m recommended; a pumping station where the cost of excavation becomes "
         "prohibitive", "G203 p. 33, §4.6.3"),
        ("Clearance to other utilities", "3 m horizontal", "G203 p. 33"),
        ("Service corridor width", "DN 200 to 500: 2.0 m; 600 to 900: 2.8 m; 1,000 to 1,200: 3.2 m; 1,400 to 1,700: "
         "4.0 m; 1,800: 4.1 m; 2,000 to 2,400: 4.4 m", "G203 p. 32, Table 13; p. 35, Table 15"),
        ("Manhole spacing", "DN 200 to 315: 100 m; 350 to 900: 120 m; 1,000 to 1,400: 150 m; above 1,400: 200 m",
         "G203 p. 30, Table 12"),
        ("Manhole locations", "Changes of gradient or diameter, junctions, ends of laterals, and at the spacing above",
         "G203 p. 29"),
        ("Backdrops", "Where the drop exceeds 600 mm, external; a vortex drop shaft above 2 m; internal only in a "
         "manhole of 1.5 m diameter or more", "G203 p. 30"),
        ("Inlet angle", "At least 90° to the direction of flow", "G203 p. 30"),
    ]),
    ("Wadi and road crossings", [
        ("Pipelines and manholes in wadis", "To be avoided, as are areas subject to washout", "G203 p. 30, §4.4.1; p. 33"),
        ("Cover at a wadi crossing", "1.5 m to the crown, gravity sewer and force main", "G203 p. 52, §8.2.4"),
        ("Cover in soft soil", "2.0 m minimum", "G201 p. 86"),
        ("Pipe material at a crossing", "Ductile iron over the crossing and 15 m each side, with mechanical or "
         "detachable joints", "G201 p. 86"),
        ("Protection", "Nama Water Services standard drawing PAM-STD-404; anti-flotation check with the pipe empty",
         "G201 p. 86"),
        ("Valves", "Isolation and air valves on both sides of an active or major crossing; a washout at the low point; "
         "no manholes or markers in the wadi bed or its embankments", "G201 p. 86"),
        ("Data and approvals", "Wadi profiles, flood frequency at 1 in 20, 50 and 100 years, bed material; approval of "
         "the Ministry of Agriculture, Fisheries and Water Resources", "G201 p. 85"),
        ("Inverted siphons", "Not allowed", "G203 p. 182, §11.5.3.1"),
        ("Twin pipelines at a crossing", "Allowed with a hydraulic justification: 0.75 m/s in all modes",
         "G203 p. 52, §8.2.3"),
        ("Road crossings", "Trenchless preferred; reinstatement to the Oman Highway Design Manual", "G201 p. 85"),
    ]),
    ("Pumping stations", [
        ("Siting", "Determined by the hydraulics, with flooded suction preferred; the site approved by Nama Water "
         "Services at the concept or preliminary stage", "G203 p. 38, §7.2"),
        ("Flood protection", "Pump floors, transformers and generators above the maximum flood level and at least "
         "300 mm above the 1 in 50 year flood level", "G203 p. 38, §7.2"),
        ("Station type", "Type 1 up to 100 l/s, one duty and one standby; Type 2 over 100 to 300 l/s, two duty and one "
         "standby; Type 3 over 300 l/s, three duty and one standby", "G203 pp. 40 to 41, Table 17"),
        ("Land area", "Type 1: 50 to 100 m²; Type 2: 200 to 400 m²; Type 3: 900 m² or more", "G203 p. 43, Table 21"),
        ("Minimum flow", "The average flow times 0.25 at 50 l/s, 0.35 at 500 l/s, 0.45 at 2,500 l/s and 0.50 at "
         "5,000 l/s", "G203 p. 40, Table 16"),
        ("Emergency overflow", "At every station, with the approval of the Environment Authority",
         "G203 pp. 46 to 47, §7.5"),
        ("Hydrogen sulphide", "Where expected without field data, designed for 50 to 100 ppm average and 200 ppm peak "
         "at the force main termination", "G203 p. 47, §7.7; p. 55, §8.5"),
        ("Design life, mechanical", "20 years", "G203 p. 38"),
    ]),
    ("Force mains", [
        ("Velocity", "At least 0.75 m/s at the minimum flow (1.0 m/s intermittent, 1.2 m/s vertical); at most 2.5 m/s",
         "G203 p. 50, §8.1"),
        ("Minimum diameter", "75 mm bore; 50 mm with grinder pumps", "G203 p. 50, §8.1"),
        ("Gradients", "At least 1 in 500 rising and 1 in 300 falling; never flatter than 1 in 750",
         "G203 p. 50, §8.2.1"),
        ("Retention time", "Ideally 30 minutes or less", "G203 p. 50"),
        ("Valves", "Isolation valves at about 500 m and never more than 800 m; washouts at low points; air valves at "
         "high points", "G203 pp. 53 to 54, §8.4"),
        ("Separation from water mains", "3.0 m horizontal; passing under a water main with 450 mm vertical clearance",
         "G203 p. 51, §8.2.2"),
        ("Material", "Ductile iron and HDPE", "G203 p. 53, §8.3"),
        ("Termination", "At a manhole, not more than 300 mm above the receiving flow line", "G203 p. 55, §8.5"),
        ("Surge analysis", "Transient analysis in software approved by Nama Water Services", "G201 pp. 146 to 147"),
    ]),
    ("Population and flows", [
        ("Population source", "Population and housing data of the National Centre for Statistics and Information",
         "G201 p. 58, §7.2.1"),
        ("Below settlement level", "Pro rata to the electricity accounts supplied by Nama Water Services", "G201 p. 58"),
        ("Extrapolation", "Not more than ten years beyond the available forecast", "G201 p. 58"),
        ("Occupancy rate", "Population divided by housing units", "G201 pp. 58 to 59, §7.2.2"),
        ("Domestic consumption, Adh Dhahirah", "164 l per person per day, to be validated by Nama Water Services",
         "G201 pp. 59 to 60, Table 11"),
        ("Non-domestic consumption", "22 % of domestic consumption, or the unit rates of Table 12", "G201 pp. 60 to 61"),
        ("Governmental consumption", "14 % of domestic consumption as the planning value", "G201 pp. 60 to 61, §7.3.3"),
        ("Special consumption", "Labour camps and water-intensive industry, provided by the developer",
         "G201 p. 61, §7.3.4"),
        ("Return to sewer", "85 % of domestic and tanker supply; 54 % of non-domestic, governmental and commercial",
         "G201 pp. 70 to 71, Table 19"),
        ("Other water sources", "Private wells and other abstractions to be assessed", "G201 p. 70, §7.4"),
        ("Peak factor", "Merrimack for over 100 properties; Peltier for fewer", "G201 pp. 71 to 72, §7.4.2"),
        ("Peak factor limit", "Recommended not to exceed 5.0", "G201 p. 72"),
        ("Infiltration", "720 l a day per km of new sewer", "G201 p. 72, §7.4.3"),
        ("Plant margin", "10 % for a new plant, over and above its redundancy", "G201 p. 73, §7.4.5; G203 p. 65"),
        ("Planning life", "25 years, also the period of the net present value", "G201 p. 57, §7.1"),
        ("Asset lifetimes", "Civil works and pipework 50 years; mechanical 20; electrical 15 to 50; control and "
         "instrumentation 15", "G201 p. 57, Table 10"),
        ("Design horizon", "Completion plus 25 years, or the saturation of the area", "ToR pp. 3, 14 to 15"),
    ]),
    ("Treatment plant", [
        ("Design horizon", "At least 15 years", "G203 p. 65"),
        ("Size category", "Small under 500 m³/d; medium 500 to 20,000 m³/d; large 20,000 m³/d and above", "G203 p. 65"),
        ("Site selection", "Access, land and phasing, winds, geology and hydrology, topography, groundwater and flood "
         "protection, buffer, life-cycle cost", "G203 pp. 63 to 64, Table 27"),
        ("Flood criteria", "25 and 100 year flood levels; fully operational during floods", "G203 p. 63, Table 27"),
        ("Land per process", "Membrane bioreactor 0.45 to 0.9 m² per m³/d; moving bed and sequencing batch 0.9 to 1.8; "
         "integrated fixed film 1.2 to 2.5; conventional and extended aeration 1.8 to 3.6", "G203 p. 64, Table 28"),
        ("Built footprint", "At most 35 % of the allocated land; setbacks at least 5 m", "G201 p. 50, §6.4.2"),
        ("Buffer distance", "500 m for small and medium plants; 300 to 1,000 m for large plants, from odour modelling "
         "to the 5 odour unit contour; 30 m from a pumping station to housing", "G201 pp. 43 to 44, Table 8"),
        ("Process lines", "Several lines, allowing capacity to be added in phases", "G201 p. 53, §6.6.2"),
        ("Redundancy", "N+1 at site level", "G201 p. 33, §4.3"),
        ("Organic loads", "At least 60 g BOD5 and 80 g suspended solids per person per day", "G203 p. 74, §10.3.1"),
        ("Existing plant records", "The measured strength from the laboratory records of the existing plant",
         "G203 p. 74, §10.3.1"),
        ("Tanker reception", "A dedicated discharge station with screening and grease removal, equalisation and "
         "sampling before acceptance", "G203 p. 73; G201 p. 55, §6.8"),
        ("Emergency lagoon", "48 to 72 hours of plant capacity where Nama Water Services requires", "G203 p. 73"),
        ("Effluent quality", "At least Class A of Ministerial Decision 145/1993 for discharge to a wadi",
         "G203 pp. 72 to 73, §10.2.4.3"),
        ("Total nitrogen", "Below 15 mg/l as nitrogen", "G203 p. 71, §10.2.4.1"),
        ("Nature-based treatment", "Constructed wetlands for works of about 500 m³/d", "G203 p. 101"),
        ("Sludge production", "0.25 kg of dry solids per m³ treated, a general guideline", "G201 p. 78, §7.4.7"),
        ("Climatic design", "Peak shade temperature 55 °C; equipment rated for continuous operation",
         "G201 pp. 78 to 79, Table 24"),
        ("Climate resilience", "A 50-year horizon at +2 °C and +4 °C", "G201 p. 33, §4.4"),
    ]),
    ("Treated effluent", [
        ("Production", "95 % of the plant inflow", "G201 p. 73"),
        ("Network loss", "10 % of the treated effluent produced", "G201 p. 76, §7.4.6.3"),
        ("Sizing", "The summer peak demand; 50 % of it from December to February and 75 % in spring and autumn",
         "G201 p. 76, Table 23"),
        ("Large consumers", "Above 500 m³/d, studied individually", "G201 p. 76, §7.4.6.4"),
        ("Transmission velocity", "1.0 to 2.0 m/s", "G202 pp. 103 to 104"),
        ("Distribution velocity", "0.4 to 1.5 m/s", "G202 p. 136"),
        ("Distribution pressure", "1.5 to 4 bar", "G202 p. 137"),
        ("Head loss", "Below 5.0 m/km in transmission and 3.0 m/km in distribution", "G202 pp. 105, 136"),
    ]),
    ("Options, cost and models", [
        ("Options", "At least three, equal in function and reliability; as a guidance, one sustainability-led, one of "
         "international best practice and one of established local practice", "G201 p. 95, §12"),
        ("Evaluation", "25 years at a 5 % discount rate; weights set by Nama Water Services; within 10 % on total cost, "
         "sustainability decides", "G201 pp. 95 to 96, p. 106"),
        ("Cost accuracy", "Plus or minus 20 % at the concept stage", "G201 pp. 17 to 20, Table 2"),
        ("Value engineering", "An independent certified study at the concept and preliminary stages above the "
         "threshold", "G201 p. 93, Table 27"),
        ("Hydraulic models", "To the WaPUG and CIWEM code of practice; static, extended-period and surge models after "
         "each design phase", "G201 p. 144; p. 109, §13.4.2"),
        ("Model calibration", "Peak flow within 10 to 15 %, volume within 15 %", "G201 p. 145, Table 32"),
    ]),
    ("Surveys and investigation", [
        ("Survey accuracy, concept stage", "0.25 to 1.0 m horizontal and 0.05 to 0.5 m vertical", "G201 p. 36, Table 5"),
        ("Underground services", "Trial pits, probes, ground radar and electro-location", "G203 p. 198, §13.3"),
        ("Existing assets", "Closed-circuit television survey to NF EN 13508-2", "G203 pp. 197 to 198"),
        ("Geotechnical", "Boreholes to 5.0 m below the invert; a trial trench or borehole every 100 m on secondary "
         "sewers and every 500 m on primary sewers and force mains", "G203 p. 199, §13.4; G201 pp. 40 to 41, Table 7"),
    ]),
]

_REF = {"G201": "PAM-GUD-201", "G202": "PAM-GUD-202", "G203": "PAM-GUD-203", "ToR": "Terms of Reference"}


def _ref(r):
    for k, v in _REF.items():
        r = r.replace(k + " ", v + ", ")
    return r


def appendix_c(d):
    D.chapter(d, "Appendix C.   Design criteria, with references")
    D.p(d, "This appendix lists the design criteria of the Nama Water Services guidelines that the design applies, with "
           "the page of each. The values this design adopts where the guidelines leave a choice are set out in Section "
           "1.5, and the departures from the guidelines in Section 3.1.1. PAM-GUD-201, -202 and -203 are the General, "
           "the Water and TSE, and the Wastewater Design Guidelines, revision 01.")
    for group, rows in CRITERIA:
        D.tab_caption(d, f"Design criteria: {group[0].lower() + group[1:]}")
        D.table(d, ["Criterion", "Value", "Reference"], [[a, b, _ref(c)] for a, b, c in rows],
                widths=[3.6, 8.6, 4.3], font=8.5, keep_together=False)
        D.p(d, "")


def appendix_d(d):
    D.chapter(d, "Appendix D.   Drawings")
    rec = F.RECOMMENDED
    D.p(d, "This appendix gathers the concept drawings: the twenty-four subnetworks of the sewer network, and the network "
           f"of each recommended option, {', '.join(rec[:-1])} and {rec[-1]}, with its pumping stations and rising mains. "
           "The drawings of every option are in Section 6.2.6 and Appendix B.")

    def _map(name):
        p = os.path.join(IMG, name + ".png")
        return p if os.path.exists(p) else os.path.join(F.W17, "Options 2026-10", "Maps", name + ".png")

    items = [(_map("W17_overview_subnetworks"), "The twenty-four subnetworks of the sewer network, each with its outfall.")]
    for i, o in enumerate(rec):
        items.append((_map(f"W17_{o}_network"),
                      f"Option {o}, recommended {('first', 'second', 'third')[i]}: the sewers by plant and size, the "
                      "pumping stations and the rising mains."))
    D.wide_figures(d, items, size="A4", last=True)
