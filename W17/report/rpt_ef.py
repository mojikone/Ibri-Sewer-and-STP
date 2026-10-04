"""Chapter 5 - the existing system.   Chapter 6 - options."""
import os

import doc as D
import notes as N

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")



def existing_not_relied_on(d):
    """Section 5.1.2: the concept design is laid as if the existing networks were absent (engineer, 2026-10-04)."""
    import json
    import facts_w17 as FW
    ov = json.load(open(os.path.join(FW.RES, "existing_overlap.json"), encoding="utf-8"))
    near = ov["within_m"]["15"]["new_km_along_existing"]
    D.p(d, "Until the survey reports, the concept design does not rely on the existing networks. The areas they serve are "
           "designed as if they had no sewer, so that the network of Section 6.2 carries all their sewage to the "
           "treatment plants, and the existing lifting station and treatment plant are not counted on: the new plants "
           "carry the full flow.")
    D.p(d, f"About {FW.fmt(near)} km of the new sewer, {100 * near / ov['new_km']:.0f} per cent of the "
           f"{FW.fmt(ov['new_km'])} km, lies within 15 metres of an existing sewer. Where the survey shows that an "
           "existing sewer can be kept, the new pipe in that street is not needed, so the design and its cost err on "
           "the safe side.")


def plant_phasing(d):
    """Section 6.5.1: the average flow at each plant of the recommended options, by model year, and the 2070 design
    capacity with the 10 per cent margin."""
    import facts_w17 as FW
    rows = []
    for o in FW.RECOMMENDED:
        for z, v in FW.plants(o).items():
            rows.append([o, FW.name(z)] + [FW.fmt(v["avg"][y]) for y in FW.YEARS] + [FW.fmt(v["avg"]["2070"] * FW.MARGIN)])
    D.tab_caption(d, "Average flow at each plant of the recommended options, m³/d, and the design capacity in 2070")
    D.table(d, ["Option", "Plant"] + FW.YEARS + ["Design 2070, with 10 %"], rows,
            widths=[1.4, 1.4] + [1.8] * len(FW.YEARS) + [2.6], font=8.5)
    D.p(d, "")


def sludge_quantities(d):
    """Section 6.7: dry solids at the guideline's general rate, the same in every option."""
    import facts_w17 as FW
    q = {y: FW.flow_chain(y)["at_plants"] for y in ("2030", "2055", "2070")}
    t = {y: 0.25 * v / 1000 for y, v in q.items()}
    p = D.p(d, f"At the guideline's general rate of 0.25 kilograms of dry solids for each cubic metre treated, the plants "
               f"produce about {t['2030']:.1f} tonnes of dry solids a day in 2030, {t['2055']:.1f} in 2055 and "
               f"{t['2070']:.1f} in 2070, {FW.fmt(t['2070'] * 365)} tonnes a year, whichever option is chosen, since "
               "the flow treated is the same. The rate depends on the process, and the quantities are refined with "
               "the process at the preliminary design.")
    N.add(p, "PAM-GUD-201, Section 7.4.7, page 78, which gives 0.25 kilograms per cubic metre as a general guideline.")
    D.p(d, "Sludge is dewatered on site at each plant and taken to composting at the sludge treatment centre the Oman "
           "Sludge Management Plan places at Ibri, which is the disposal route for every option.")


# ===================================================== PART E
def part_e(d):
    D.chapter(d, "5.   The existing system")
    D.p(d, "This chapter covers the existing wastewater and treated effluent systems: "
           "their hydraulic assessment, their rehabilitation, and the verification of "
           "the Regional Master Plan. The assessment of the existing networks "
           "follows the as-built survey now in progress; until it reports, the "
           "concept design does not rely on them (Section 5.1.2).")

    # --------------------------------------------------------------- 18
    D.h(d, 2, "5.1.   Hydraulic assessment of the existing networks")

    D.h(d, 3, "5.1.1.   Purpose")
    D.p(d, "The existing sewer, force main and treated effluent networks are "
           "assessed against the flows arising across the design period, to "
           "establish which assets have capacity for the future flow, which "
           "require upgrading, and where the new works connect to them.")

    D.h(d, 3, "5.1.2.   Approach")
    D.p(d, "The assessment is carried out by hydraulic model. The existing "
           "network is verified before it is modelled: the datasets supplied "
           "provide geometry but not levels, and the diameter is recorded on "
           "part of the network only. The survey now in progress establishes "
           "both, and the model will be built on the surveyed data.")
    existing_not_relied_on(d)
    D.p(d, "Each asset is then classified as having capacity for the design "
           "flow, requiring upgrading, or requiring replacement. Where an "
           "asset is retained, the point and manner of connection to the new "
           "works is designed.")

    D.h(d, 3, "5.1.3.   Model")
    p = D.p(d, "The wastewater network is modelled in SewerGEMS and the "
               "treated effluent network in WaterGEMS. Models are submitted in "
               "native editable format with the calculations and assumptions, "
               "and are updated following construction.")
    N.add(p, "The software to be used is the subject of Section 1.5.4.")
    D.p(d, "The model is run for the design year at peak flow, for the "
           "ultimate condition, and for the opening years at low flow. The "
           "last of these establishes the period during which the network "
           "requires assisted cleansing, described in Section 6.2.4.")


    # --------------------------------------------------------------- 19
    D.h(d, 2, "5.2.   Rehabilitation and upgrading")
    D.p(d, "Rehabilitation of the existing systems forms part of the concept "
           "scope. The extent of it follows from the assessment in Section 5.1 "
           "and from the condition established by survey and closed-circuit "
           "television inspection.")
    D.p(d, "Rehabilitation work received to date comprises contractor "
           "submissions for completed work orders at Al Sad, Khadil, Yanqul, "
           "Dhank and Hay Al Aqabah. These have been reviewed and recorded; "
           "they describe work already carried out rather than work required.")


    # --------------------------------------------------------------- 20
    D.h(d, 2, "5.3.   Verification of the Regional Master Plan")
    D.p(d, "The Terms of Reference require the Regional Master Plan to be "
           "verified. The verification compares the flows established in Chapter "
           "4 against those on which the master plan was based, and identifies "
           "and explains any difference.")

    p = D.p(d, "The master plan has not been provided. It is requested (Section "
               "1.5.5), and the verification is made when it is received, on the "
               "flow series of Section 4.2.7 and the design horizon decided in "
               "Section 1.5.2. The only master plan figure held is a treatment "
               "plant record in the asset data, a design case of 29,038 cubic "
               "metres a day annotated as arising from the master plan concept "
               "design and not approved.")
    N.add(p, "The treatment plant record in the asset data supplied, with the "
             "status Design and the source Asset Planning.")

    D.p(d, "The data required by Nama Water Services Asset Management Planning "
           "for the updating of the master plan will be provided in the format "
           "the client specifies.")


# ===================================================== PART F
def part_f(d):
    D.chapter(d, "6.   Options")
    D.p(d, "This chapter sets out how the options are developed and compared, presents "
           "the seven options of the sewer network with their pumping stations, and sets "
           "the framework for the options of the treated effluent network, the treatment "
           "plant, the excess effluent and the sludge.")

    # --------------------------------------------------------------- 21
    D.h(d, 2, "6.1.   Options methodology")

    D.picture(d, os.path.join(IMG, "D5_options.png"), 13.0)
    D.fig_caption(d, "Development and selection of the options: every option costed on one basis, those within ten "
                     "per cent of the lowest whole-life cost compared on sustainability and operability, and the "
                     "characters costed at the preliminary design.")

    D.h(d, 3, "6.1.1.   Number and character of the options")
    p = D.p(d, "Not fewer than three options are developed for each of the "
               "sewer network, the treated effluent network and the treatment "
               "plant. The guidelines indicate the character the options "
               "should take: one advancing environmental sustainability "
               "including nature-based solutions, one representing "
               "international best practice, and one based on established "
               "practice and technology available in the Sultanate.")
    N.add(p, "PAM-GUD-201, Section 12.1, page 95.")
    D.p(d, "For the sewer network, seven options have been modelled for where the "
           "flow is treated (Section 6.2), from one plant to six, and further "
           "options can be added on the same model. They are compared on "
           "whole-life cost, and those within ten per cent of the lowest on "
           "sustainability and operability (Section 7.11). The characters are "
           "not tied to an option: they change the treatment process, the energy "
           "supply and the reuse, not the network, and are costed at the "
           "preliminary design, where the treatment process of the recommended "
           "option is selected.")

    D.p(d, "Each option is developed to equivalent functional requirements "
           "with comparable reliability and redundancy, so that the comparison "
           "between them is not influenced by differences in scope.")

    D.h(d, 3, "6.1.2.   The approach proposed for each option")
    D.p(d, "The guidelines describe the three characters but do not prescribe "
           "what distinguishes them in design terms. The following approach is "
           "proposed and is offered for comment. The network of an option, its "
           "pipes, pumping stations and plant sites, is the same in all three "
           "characters; what changes is the treatment process, the energy supply, "
           "solar generation included, the reuse and the materials. The "
           "characters are costed on that basis at the preliminary design.")

    D.tab_caption(d, "Proposed approach for each character")
    D.table(d,
            ["", "Sustainability-led", "International best practice",
             "Established local practice"],
            [["Treatment process",
              "Lower-energy process, with nature-based polishing where the "
              "scale permits",
              "Highest-performing process, smallest footprint",
              "Process already established in Oman, simple to operate and "
              "maintain"],
             ["Energy",
              "Solar generation on site, with a self-sufficiency target",
              "High-efficiency plant and advanced process control",
              "Grid supply with standby generation"],
             ["Reuse",
              "Reuse maximised, discharge to wadi minimised",
              "High reuse at high effluent quality",
              "Reuse to the demand identified, surplus discharged"],
             ["Materials",
              "Low-carbon and locally sourced where performance permits",
              "Specified for performance and durability",
              "Standard specification"],
             ["Consequence",
              "Higher capital cost, lowest carbon and operating cost",
              "Highest capital cost, least land, best effluent quality",
              "Lowest capital cost, most land, highest operating cost"]],
            widths=[2.6, 4.7, 4.7, 4.5], font=8.5)

    D.p(d, "")
    p = D.p(d, "Two constraints apply across all three characters. Nature-based treatment "
               "is limited by the guidelines to small plants, so it is "
               "available for outlying settlements or for polishing rather "
               "than for the main plant. And every option is developed to the "
               "same functional requirement and the same effluent standard, so "
               "that the difference between them lies in how the result is "
               "achieved and not in what is achieved.")
    N.add(p, "PAM-GUD-203, Section 10.5, page 101, limits constructed wetlands "
             "to plants of approximately 500 cubic metres per day.")

    D.h(d, 3, "6.1.3.   Basis of comparison")
    D.p(d, "The options are compared on their capital and operating cost and "
           "their whole-life cost over twenty-five years (Section 7.8), on the "
           "energy they use, and on how they are operated. Carbon footprint, "
           "resource efficiency, in-country value and the use of nature-based "
           "solutions are compared with the characters at the preliminary "
           "design. The weighting applied to each criterion is set by Nama "
           "Water Services. The figure on the following page shows how each "
           "option is costed and compared.")

    D.wide_figure(d, os.path.join(IMG, "appraisal_method.png"),
                  "How each option is costed and compared: the capital and "
                  "operating cost of every option on one basis, discounted "
                  "together to its whole-life cost; the options within ten per "
                  "cent of the lowest are then compared on sustainability and "
                  "operability.", size="A4")

    D.h(d, 3, "6.1.4.   Selection")
    p = D.p(d, "The guidelines compare options by a weighted multi-criteria "
               "analysis against total lifetime cost, sustainability, social "
               "development and in-country value, adaptability and resilience, "
               "operability, constructability and environmental impact, with "
               "sensitivity tests on the weighting, the discount rate and the "
               "input design criteria; of two options within ten per cent of "
               "one another on total lifetime cost, the more sustainable is "
               "adopted.")
    N.add(p, "PAM-GUD-201, Sections 12.6 to 12.9, pages 104 to 106.")
    p = D.p(d, "At the concept stage the options are ranked on whole-life cost. "
               "Those within ten per cent of the lowest are compared on "
               "sustainability and, where they are equal within the accuracy of "
               "the estimate, on operability (Section 7.11). The sensitivity to "
               "the discounting basis is given in Section 7.8.4. The weights set "
               "by Nama Water Services complete the analysis at the preliminary "
               "design, with the characters.")
    N.add(p, "PAM-GUD-201, Sections 12.6 to 12.9, pages 104 to 106.")

    # --------------------------------------------------------------- 22
    D.h(d, 2, "6.2.   Sewer network options")

    D.picture(d, os.path.join(IMG, "D4_network.png"), 15.5)
    D.fig_caption(d, "The network design approach, and the point at which a lifting station becomes necessary.")

    D.h(d, 3, "6.2.1.   Principles")
    D.p(d, "The network is laid out to convey the flow by gravity wherever "
           "that is feasible and cost effective, and to keep pumping to the "
           "minimum that the topography requires. The layout follows the road "
           "corridors, and each part of the network drains to its lowest point. "
           "The existing treatment plant site lies low relative to the developed "
           "areas; the options differ in whether the flow is treated there or "
           "at plants nearer the outlying settlements (Section 6.2.6).")

    D.h(d, 3, "6.2.2.   Corridor constraints")
    D.p(d, "Dual carriageways are excluded as sewer corridors, as they cannot "
           "be taken out of service for construction or maintenance. Crossings "
           "of a dual carriageway are made perpendicular and, where available, "
           "through an existing underpass. Wadi crossings are designed to the "
           "cover required by the guideline.")

    D.h(d, 3, "6.2.3.   Network hierarchy")
    D.p(d, "The network is arranged in three tiers, following the arrangement "
           "of the existing network in Ibri: laterals collecting from "
           "properties, sub-mains collecting from laterals, and a trunk main "
           "conveying the collected flow to the plant. Arranging the network "
           "this way limits the number of connections made directly to the "
           "trunk main and keeps each tier to a manageable size.")

    D.h(d, 3, "6.2.4.   Early-year operation")
    D.p(d, "In the years following commissioning the connected population is a "
           "fraction of the design population, and the flow in the network is "
           "correspondingly lower. Velocities in that period may fall below "
           "the self-cleansing value, and the network requires assisted "
           "cleansing until the flow is sufficient to scour the pipes.")
    D.p(d, "The period during which this applies is established for each pipe "
           "from the flow series and the connection ratio, and is presented as "
           "a schedule of the pipes affected and the years concerned, so that "
           "the operating requirement is known before the network is handed "
           "over. Section 6.2.8 sets out the year from which each pipe of the "
           "network reaches the self-cleansing velocity.")

    import rpt_options             # Revision 4: the options S1 to S7, from the SewerGEMS results of W17
    rpt_options.network_options(d)

    # --------------------------------------------------------------- 23
    D.h(d, 2, "6.3.   Pumping and lifting stations")
    D.p(d, "A lifting station is provided where the cost of excavation to "
           "maintain gravity flow becomes prohibitive. Each station lifts the "
           "flow to a level from which gravity conveyance resumes, discharging "
           "through a force main to a receiving manhole or to the treatment "
           "plant. The pumping stations of the seven options, with their duty, "
           "rising main, head and power, are listed in Appendix B.")

    D.tab_caption(d, "Force main design criteria")
    D.table(d, ["Criterion", "Value"], [
        ["Minimum velocity, raw sewage", "0.75 m/s at minimum flow"],
        ["Minimum velocity, intermittent flow", "1.0 m/s"],
        ["Minimum velocity, vertical mains", "1.2 m/s"],
        ["Maximum velocity", "2.5 m/s"],
        ["Minimum internal diameter", "75 mm"],
        ["Gradient, rising", "1 in 500"],
        ["Gradient, falling", "1 in 300"],
        ["Retention time", "30 minutes or less, ideally"],
    ], widths=[9.0, 7.5], font=9.5)

    D.p(d, "")
    p = D.p(d, "Retention in a force main allows sulphide to form, which is "
               "both a corrosion and an odour risk in this climate. Alignments "
               "are therefore kept short, discharges are submerged to limit "
               "turbulence, and the need for dosing is assessed for each "
               "station.")
    N.add(p, "PAM-GUD-203, Sections 8.2.1 and 11.5.3, pages 50 and 181.")

    D.p(d, "Surge analysis is carried out for each force main in approved "
           "software, and the protection required is established from it.")

    # --------------------------------------------------------------- 24
    D.h(d, 2, "6.4.   Treated effluent network options")
    D.p(d, "The treated effluent network conveys the product of the treatment "
           "plant to the customers identified in Section 4.4. The network is "
           "sized for the summer peak demand, with storage of not less than "
           "twenty-four hours.")
    D.p(d, "Where demand is below the volume produced, provision is made for "
           "the disposal of the excess, described in Section 6.6.")
    D.p(d, "At the concept stage the customers are not yet defined. The "
           "potential customers identified at the stakeholder meeting held in "
           "Ibri on 23 September 2026 are listed in Section 4.4 with the demand "
           "each indicated, and each has been asked for its demand and its "
           "plans for 2030, 2040 and 2050. The network options are developed "
           "on that demand, from the plant locations of the option taken "
           "forward, at the preliminary design.")


    # --------------------------------------------------------------- 25
    D.h(d, 2, "6.5.   Treatment plant options")

    D.h(d, 3, "6.5.1.   Capacity and phasing")
    D.p(d, "Each plant is sized on the flow arriving at it in the option chosen, "
           "given for every model year in Section 6.2.7, with the ten per cent "
           "design margin applied, and is built in phases so that capacity "
           "follows demand. The flows of the three recommended options are "
           "given below; the size of each phase follows from the design "
           "horizon decided in Section 1.5.2.")
    plant_phasing(d)

    D.h(d, 3, "6.5.2.   Process selection")
    D.p(d, "Process selection is governed by the effluent standard. The total "
           "nitrogen limit described in Section 3.4 requires full nitrification "
           "and denitrification, which narrows the technologies that can be "
           "considered. Land area, energy consumption, operating complexity "
           "and whole life cost distinguish the remaining options.")

    D.tab_caption(d, "Indicative land requirement by process")
    D.table(d, ["Process", "Area, m² per m³/d"], [
        ["Membrane bioreactor", "0.45 to 0.9"],
        ["Sequencing batch reactor", "0.9 to 1.8"],
        ["Moving bed biofilm reactor", "0.9 to 1.8"],
        ["Integrated fixed film activated sludge", "1.2 to 2.5"],
        ["Conventional activated sludge and extended aeration", "1.8 to 3.6"],
    ], widths=[10.5, 6.0], font=9.5)
    D.p(d, "")
    p = D.p(d, "The areas are indicative and are used for planning. The land "
               "required includes the process units, the sludge facilities, "
               "the buffer zone and provision for the energy-efficiency "
               "measures described in Section 7.7.")
    N.add(p, "PAM-GUD-203, Table 28, page 64.")

    D.h(d, 3, "6.5.3.   Siting")
    D.p(d, "The site is assessed against the criteria in the wastewater "
           "guideline, covering access, physical characteristics, "
           "environmental and climatic impact, social impact and cost. Two "
           "criteria carry stated requirements: the site is assessed against "
           "the twenty-five and one hundred year flood levels, and the plant "
           "is to remain operational during floods.")
    p = D.p(d, "The buffer distance to residential areas for a plant of this "
               "size is established from odour dispersion modelling rather "
               "than from a fixed figure, and lies between 300 and 1,000 "
               "metres measured to the five odour unit contour. The modelling "
               "is described in Section 7.3 and precedes the confirmation of "
               "the site.")
    D.p(d, "The plant sites of the options, at the outfalls named in Section "
           "6.2.6, are tentative at the concept stage. Each is assessed against "
           "these criteria, and checked for flood, ground and odour (Sections "
           "7.1 to 7.3), as soon as it is decided.")
    N.add(p, "PAM-GUD-201, Table 8, pages 43 and 44.")


    # --------------------------------------------------------------- 26
    D.h(d, 2, "6.6.   Excess effluent, emergency provisions and tankers")

    D.h(d, 3, "6.6.1.   Tanker reception")
    D.p(d, "A proportion of the wastewater arising in the area is collected by "
           "tanker and delivered to the treatment plant. Sewage delivered this "
           "way is stronger than sewage arriving through the network, and its "
           "arrival is concentrated in the working day. A dedicated reception "
           "facility is provided, with screening, grease removal, sampling "
           "before acceptance and flow equalisation. The volumes delivered from "
           "outside the study area, and their sources, are requested from Nama "
           "Water Services (Section 1.5.5), so that the reception facility and "
           "the plant are designed for them.")

    D.h(d, 3, "6.6.2.   Excess treated effluent")
    p = D.p(d, "Where the effluent produced exceeds the demand, provision is "
               "made for its disposal. Discharge to a wadi requires the "
               "effluent to meet Class A of Ministerial Decision 145/1993, and "
               "where the wadi discharges to the sea the limits for ammonia, "
               "nitrogen and phosphorus of Ministerial Decision 159/2005 apply "
               "in addition. Any such discharge is subject to the approval of "
               "the Environment Authority and the Authority for Public "
               "Services Regulation.")
    N.add(p, "PAM-GUD-203, Section 10.2.4.3, pages 72 and 73. The substituted "
             "limits are materially tighter than Class A for phosphorus and "
             "ammoniacal nitrogen.")

    D.h(d, 3, "6.6.3.   Emergency provisions")
    D.p(d, "Provision is made for the diversion of raw sewage in the event "
           "that the plant is out of operation, and for emergency storage. "
           "Every pumping station is provided with an emergency overflow to "
           "prevent flooding of the station or of connected properties; "
           "overflows are subject to the approval of the Environment "
           "Authority.")

    # --------------------------------------------------------------- 27
    D.h(d, 2, "6.7.   Sludge management strategy")
    p = D.p(d, "The Oman Sludge Management Plan, as reproduced in the "
               "wastewater design guideline, identifies a sludge treatment "
               "centre performing composting at Ibri as the solution for the "
               "Governorate of Adh Dhahirah. The plant is therefore to be "
               "designed to receive and process sludge arising beyond its own "
               "catchment, and the land area, buffer distance and vehicle "
               "access are established accordingly.")
    N.add(p, "PAM-GUD-203, Table 67, page 136.")

    D.p(d, "Sludge is to be reused unless no form of reuse is possible, and "
           "its quality is to comply with the heavy metal limits of "
           "Ministerial Decision 145/1993. Where disposal to landfill is "
           "required, the receiving authority sets acceptance criteria "
           "including a minimum solids content of eighty per cent. That "
           "content is above what mechanical dewatering alone achieves, and "
           "drying or composting is therefore required.")

    sludge_quantities(d)
