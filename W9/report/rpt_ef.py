"""Part E - the existing system.   Part F - options."""
import doc as D
import notes as N


def _pending(d, text):
    D.p(d, text, italic=True, colour=D.GREY)


# ===================================================== PART E
def part_e(d):
    D.h(d, 1, "Part E   The existing system", page_break=True)

    # --------------------------------------------------------------- 18
    D.h(d, 1, "18   Hydraulic assessment of the existing networks")

    D.h(d, 2, "18.1   Purpose")
    D.p(d, "The existing sewer, force main and treated effluent networks are "
           "assessed against the flows arising across the design period, to "
           "establish which assets have capacity for the future flow, which "
           "require upgrading, and where the new works connect to them.")

    D.h(d, 2, "18.2   Approach")
    D.p(d, "The assessment is carried out by hydraulic model. The existing "
           "network is verified before it is modelled: the datasets supplied "
           "provide geometry but not levels, and the diameter is recorded on "
           "part of the network only. The survey now in progress establishes "
           "both, and the model will be built on the surveyed data.")
    D.p(d, "Each asset is then classified as having capacity for the design "
           "flow, requiring upgrading, or requiring replacement. Where an "
           "asset is retained, the point and manner of connection to the new "
           "works is designed.")

    D.h(d, 2, "18.3   Model")
    p = D.p(d, "The wastewater network is modelled in SewerGEMS and the "
               "treated effluent network in WaterGEMS. Models are submitted in "
               "native editable format with the calculations and assumptions, "
               "and are updated following construction.")
    N.add(p, "The software to be used is the subject of Section 5.4.")
    D.p(d, "The model is run for the design year at peak flow, for the "
           "ultimate condition, and for the opening years at low flow. The "
           "last of these establishes the period during which the network "
           "requires assisted cleansing, described in Section 22.4.")

    _pending(d, "The assessment will be presented in the next revision, "
                "following completion of the survey.")

    # --------------------------------------------------------------- 19
    D.h(d, 1, "19   Rehabilitation and upgrading")
    D.p(d, "Rehabilitation of the existing systems forms part of the concept "
           "scope. The extent of it follows from the assessment in Section 18 "
           "and from the condition established by survey and closed-circuit "
           "television inspection.")
    D.p(d, "Rehabilitation work received to date comprises contractor "
           "submissions for completed work orders at Al Sad, Khadil, Yanqul, "
           "Dhank and Hay Al Aqabah. These have been reviewed and recorded; "
           "they describe work already carried out rather than work required.")

    _pending(d, "The rehabilitation schedule, with quantities and cost, will "
                "be presented in the next revision.")

    # --------------------------------------------------------------- 20
    D.h(d, 1, "20   Verification of the Regional Master Plan")
    D.p(d, "The Terms of Reference require the Regional Master Plan to be "
           "verified. The verification compares the flows established in Part "
           "D against those on which the master plan was based, and identifies "
           "and explains any difference.")

    p = D.p(d, "The asset data supplied includes a treatment plant record "
               "shown as a design case with a capacity of 29,038 cubic metres "
               "per day, annotated as arising from the Regional Master Plan "
               "concept design and not yet approved. That figure is taken as "
               "the master plan position for comparison.")
    N.add(p, "STP_PT_IBRI.shp, record identifier 10, status Design, source "
             "recorded as Asset Planning.")

    D.p(d, "The comparison depends on the design horizon, which is the subject "
           "of Section 5.1, and on the flow series described in Section 15.5. "
           "It will be presented in the next revision.")

    D.p(d, "The data required by Nama Water Services Asset Management Planning "
           "for the updating of the master plan will be provided in the format "
           "the client specifies.")


# ===================================================== PART F
def part_f(d):
    D.h(d, 1, "Part F   Options", page_break=True)

    # --------------------------------------------------------------- 21
    D.h(d, 1, "21   Options methodology")

    D.h(d, 2, "21.1   Number and character of the options")
    p = D.p(d, "Not fewer than three options are developed for each of the "
               "sewer network, the treated effluent network and the treatment "
               "plant. The guidelines indicate the character the options "
               "should take: one advancing environmental sustainability "
               "including nature-based solutions, one representing "
               "international best practice, and one based on established "
               "practice and technology available in the Sultanate.")
    N.add(p, "PAM-GUD-201, Section 12.1, page 95.")

    D.p(d, "Each option is developed to equivalent functional requirements "
           "with comparable reliability and redundancy, so that the comparison "
           "between them is not influenced by differences in scope.")

    D.h(d, 2, "21.2   Basis of comparison")
    D.p(d, "The options are compared on capital and operating cost, life cycle "
           "cost, carbon footprint over the project lifetime, resource "
           "efficiency, in-country value and the degree to which they employ "
           "nature-based solutions. The evaluation period is twenty-five "
           "years. The weighting applied to each parameter is set by Nama "
           "Water Services.")

    D.h(d, 2, "21.3   Selection")
    p = D.p(d, "A weighted multi-criteria analysis compares the options "
               "against total lifetime cost, sustainability, social "
               "development and in-country value, adaptability and resilience, "
               "operability, constructability and environmental impact. "
               "Sensitivity is tested by varying the weighting between "
               "categories, the discount rate and the input design criteria. "
               "Where options fall within ten per cent of one another on total "
               "lifetime cost, the more sustainable option is adopted.")
    N.add(p, "PAM-GUD-201, Sections 12.6 to 12.9, pages 104 to 106.")

    # --------------------------------------------------------------- 22
    D.h(d, 1, "22   Sewer network options", page_break=True)

    D.h(d, 2, "22.1   Principles")
    D.p(d, "The network is laid out to convey the flow by gravity wherever "
           "that is feasible and cost effective, and to keep pumping to the "
           "minimum that the topography requires. The layout follows the road "
           "corridors, and the flow is directed towards the existing treatment "
           "plant site, which lies at a low elevation relative to the "
           "developed areas.")

    D.h(d, 2, "22.2   Corridor constraints")
    D.p(d, "Dual carriageways are excluded as sewer corridors, as they cannot "
           "be taken out of service for construction or maintenance. Crossings "
           "of a dual carriageway are made perpendicular and, where available, "
           "through an existing underpass. Wadi crossings are designed to the "
           "cover required by the guideline.")

    D.h(d, 2, "22.3   Network hierarchy")
    D.p(d, "The network is arranged in three tiers, following the arrangement "
           "of the existing network in Ibri: laterals collecting from "
           "properties, sub-mains collecting from laterals, and a trunk main "
           "conveying the collected flow to the plant. Arranging the network "
           "this way limits the number of connections made directly to the "
           "trunk main and keeps each tier to a manageable size.")

    D.h(d, 2, "22.4   Early-year operation")
    D.p(d, "In the years following commissioning the connected population is a "
           "fraction of the design population, and the flow in the network is "
           "correspondingly lower. Velocities in that period may fall below "
           "the self-cleansing value, and the network requires assisted "
           "cleansing until the flow is sufficient to scour the pipes.")
    D.p(d, "The period during which this applies is established for each pipe "
           "from the flow series and the connection ratio, and is presented as "
           "a schedule of the pipes affected and the years concerned, so that "
           "the operating requirement is known before the network is handed "
           "over.")

    _pending(d, "The network options and the cleansing schedule will be "
                "presented in the next revision.")

    # --------------------------------------------------------------- 23
    D.h(d, 1, "23   Pumping and lifting stations")
    D.p(d, "A lifting station is provided where the cost of excavation to "
           "maintain gravity flow becomes prohibitive. Each station lifts the "
           "flow to a level from which gravity conveyance resumes, discharging "
           "through a force main to a receiving manhole or to the treatment "
           "plant.")

    D.tab_caption(d, "Force main design criteria")
    D.table(d, ["Criterion", "Value"], [
        ["Minimum velocity, raw sewage", "0.75 m/s at minimum flow"],
        ["Minimum velocity, intermittent flow", "1.0 m/s"],
        ["Minimum velocity, vertical mains", "1.2 m/s"],
        ["Maximum velocity", "2.5 m/s"],
        ["Minimum internal diameter", "75 mm"],
        ["Gradient, rising", "1 in 500"],
        ["Gradient, falling", "1 in 300"],
        ["Retention time", "as short as the alignment permits"],
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
    D.h(d, 1, "24   Treated effluent network options")
    D.p(d, "The treated effluent network conveys the product of the treatment "
           "plant to the customers identified in Section 17. The network is "
           "sized for the summer peak demand, with storage of not less than "
           "twenty-four hours.")
    D.p(d, "Where demand is below the volume produced, provision is made for "
           "the disposal of the excess, described in Section 26.")

    _pending(d, "The network options will be presented in the next revision, "
                "following confirmation of the customers and their demand.")

    # --------------------------------------------------------------- 25
    D.h(d, 1, "25   Treatment plant options", page_break=True)

    D.h(d, 2, "25.1   Capacity and phasing")
    D.p(d, "The plant is sized on the flow established in Part D with the ten "
           "per cent design margin applied, and is built in phases so that "
           "capacity follows demand. The capacity of the first phase, and the "
           "years at which subsequent phases are required, follow from the "
           "flow series and are presented with it.")

    D.h(d, 2, "25.2   Process selection")
    D.p(d, "Process selection is governed by the effluent standard. The total "
           "nitrogen limit described in Section 13 requires full nitrification "
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
               "measures described in Section 34.")
    N.add(p, "PAM-GUD-203, Table 28, page 64.")

    D.h(d, 2, "25.3   Siting")
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
               "is described in Section 30 and precedes the confirmation of "
               "the site.")
    N.add(p, "PAM-GUD-201, Table 8, pages 43 and 44.")

    _pending(d, "The plant options, the site assessment and the phasing will "
                "be presented in the next revision.")

    # --------------------------------------------------------------- 26
    D.h(d, 1, "26   Excess effluent, emergency provisions and tankers")

    D.h(d, 2, "26.1   Tanker reception")
    D.p(d, "A proportion of the wastewater arising in the area is collected by "
           "tanker and delivered to the treatment plant. Sewage delivered this "
           "way is stronger than sewage arriving through the network, and its "
           "arrival is concentrated in the working day. A dedicated reception "
           "facility is provided, with screening, grease removal, sampling "
           "before acceptance and flow equalisation.")

    D.h(d, 2, "26.2   Excess treated effluent")
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

    D.h(d, 2, "26.3   Emergency provisions")
    D.p(d, "Provision is made for the diversion of raw sewage in the event "
           "that the plant is out of operation, and for emergency storage. "
           "Every pumping station is provided with an emergency overflow to "
           "prevent flooding of the station or of connected properties; "
           "overflows are subject to the approval of the Environment "
           "Authority.")

    # --------------------------------------------------------------- 27
    D.h(d, 1, "27   Sludge management strategy")
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

    D.p(d, "Dewatering facilities are provided on site. The strategy, with the "
           "quantities arising and the disposal route for each, will be "
           "presented in the next revision.")
