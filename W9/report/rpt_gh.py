"""Part G - assessment and appraisal.   Part H - delivery."""
import doc as D
import notes as N
import omml as M

UP, R = M.up, M.r


def _pending(d, text):
    D.p(d, text, italic=True, colour=D.GREY)


# ===================================================== PART G
def part_g(d):
    D.part(d, "G", "Assessment and appraisal")

    # --------------------------------------------------------------- 28
    D.h(d, 1, "28   Ground conditions")
    D.p(d, "Geophysical investigation is required for all infrastructure and "
           "geotechnical investigation for all above-ground assets. At this "
           "stage the purpose is to establish a site-wide ground model and a "
           "range of parameters sufficient to select foundation types and "
           "platform levels, and to identify the risks that the detailed "
           "investigation must resolve.")
    D.p(d, "Boreholes at the treatment plant and lifting station sites are "
           "taken to a minimum depth of fifteen metres or to a competent "
           "stratum, and are closely spaced at wet wells, valve chambers and "
           "electrical rooms. Groundwater monitoring is required, as the depth "
           "to groundwater governs both the excavation method and the "
           "infiltration allowance.")

    _pending(d, "The ground model and the concept geotechnical report will be "
                "presented in the next revision.")

    # --------------------------------------------------------------- 29
    D.h(d, 1, "29   Flood protection")
    D.p(d, "The study area is crossed by a wadi system, and flood behaviour "
           "governs both the alignment of the works and the siting of the "
           "treatment plant. The site is assessed against the twenty-five and "
           "one hundred year flood levels, and the plant is to remain "
           "operational during floods.")
    D.p(d, "Pumping station floor levels, transformers and standby generators "
           "are set not less than 300 millimetres above the one in fifty year "
           "flood level. Wadi crossings are designed with a minimum cover of "
           "1.5 metres to the crown of the pipe.")

    _pending(d, "The flood protection assessment will be presented in the next "
                "revision.")

    # --------------------------------------------------------------- 30
    D.h(d, 1, "30   Odour assessment")
    p = D.p(d, "Odour governs the buffer distance between the treatment plant "
               "and residential development, and for a plant of this size the "
               "buffer is established from dispersion modelling rather than "
               "from a fixed distance. The modelling establishes the distance "
               "to the five odour unit contour, using site meteorological "
               "records and the treatment processes proposed.")
    N.add(p, "PAM-GUD-201, Table 8, page 43; PAM-GUD-203, Table 90, page 170, "
             "which sets five odour units per cubic metre at the site boundary "
             "where the surrounding area is sensitive.")

    D.p(d, "Odour control is provided at the inlet works, the sludge "
           "facilities and the pumping stations, with the treatment train "
           "selected from the assessment. Compliance is verified by continuous "
           "monitoring at the site boundary.")

    _pending(d, "The dispersion modelling and the resulting buffer will be "
                "presented in the next revision, and precede confirmation of "
                "the plant site.")

    # --------------------------------------------------------------- 31
    D.h(d, 1, "31   Climate resilience")
    p = D.p(d, "The works are assessed for resilience to the climate "
               "conditions anticipated over their service life. The assessment "
               "considers a fifty-year horizon at two and at four degrees "
               "Celsius of warming, and addresses the effect of changes in "
               "rainfall frequency and intensity on site selection and on the "
               "design of the infrastructure.")
    N.add(p, "PAM-GUD-201, Section 4.3, page 33.")

    _pending(d, "The assessment will be presented in the next revision.")

    # --------------------------------------------------------------- 32
    D.h(d, 1, "32   Environmental and social assessment")
    D.p(d, "An environmental impact assessment is required for the treatment "
           "plant and its associated works. The Environment Authority is "
           "informed of the project, its objectives and its anticipated "
           "impact, and is consulted on the location of the facilities.")
    D.p(d, "Each option is assessed against resource use, ecosystem "
           "disruption, pollution risk, climate resilience, socio-economic "
           "impact and land use, and the assessment forms part of the "
           "comparison described in Section 38.")
    D.p(d, "The scope required at this stage is the subject of Section 5.5.")

    # --------------------------------------------------------------- 33
    D.h(d, 1, "33   Utility interfaces and approvals", page_break=True)

    D.h(d, 2, "33.1   Approach")
    D.p(d, "The proposed alignments are superimposed on the service records of "
           "each authority holding assets in the area. Where a conflict "
           "cannot be avoided by re-routing within the corridor, the cost of "
           "relocating the proposed works is compared with the cost of "
           "relocating the existing service, and the agreement of the owning "
           "authority is obtained for whichever is adopted.")

    D.h(d, 2, "33.2   Records held and required")
    D.p(d, "The potable water network is available from the dataset described "
           "in Section 7.2 and provides 647.8 kilometres of mains within the "
           "study area. Records for electricity distribution, telecommunications "
           "and, where present, gas and fuel pipelines are being requested "
           "from the respective owners.")
    p = D.p(d, "The electricity data held records the position of consumer "
               "connections. It does not record the routes of the distribution "
               "cables, which are required for clash assessment and are "
               "requested separately.")
    N.add(p, "The account dataset described in Section 7.3 comprises point "
             "locations of metered connections.")

    D.h(d, 2, "33.3   Clearances")
    D.tab_caption(d, "Separation from other services")
    D.table(d, ["Situation", "Requirement"], [
        ["Force main to water main, horizontal", "3.0 m"],
        ["Force main crossing a water main",
         "the force main passes beneath, with 450 mm vertical clearance"],
        ["Shallow sewer beneath a major road", "3.0 m horizontal clearance"],
        ["Another service in the same trench",
         "placed on a separate bench on undisturbed ground"],
    ], widths=[7.0, 9.5], font=9.5)
    D.p(d, "")
    D.p(d, "Beyond these, the clearance applied is that specified by the "
           "authority owning the service.")

    D.h(d, 2, "33.4   Trial pits")
    D.p(d, "Fifty trial pits are provided for. Their locations are selected at "
           "road intersections, along the routes of major existing services "
           "and along the expected routes of the trunk sewers and force mains. "
           "The programme is agreed with Nama Water Services and the municipal "
           "excavation approvals obtained before work begins.")

    D.h(d, 2, "33.5   Approvals register")
    D.p(d, "Approvals and no objection certificates are required from the "
           "authorities listed below. A register is maintained recording the "
           "authority, the consent required, the date of application and the "
           "current position, and is reported to Nama Water Services.")
    D.table(d, ["Authority"], [
        ["Ministry of Housing and Urban Planning"],
        ["Environment Authority"],
        ["Ministry of Agriculture, Fisheries and Water Resources"],
        ["Directorate General of Roads"],
        ["Regional electricity distribution company"],
        ["Oman Telecommunications Company"],
        ["Royal Oman Police"],
        ["Ministry of Heritage and Tourism"],
        ["Municipality of Ibri"],
    ], widths=[16.5], font=9.5)

    # --------------------------------------------------------------- 34
    D.h(d, 1, "34   Sustainability", page_break=True)
    p = D.p(d, "The carbon footprint of each option is evaluated for both "
               "construction and operation in accordance with recognised "
               "greenhouse gas accounting standards, and is expressed in "
               "tonnes of carbon dioxide equivalent per year and per cubic "
               "metre of effluent produced.")
    N.add(p, "PAM-GUD-201, Section 12.5.1, pages 98 to 100, which cites ISO "
             "14064 and the Greenhouse Gas Protocol and gives a benchmark of "
             "1.17 × 10⁻³ tonnes of carbon dioxide equivalent per cubic metre "
             "of treated effluent.")

    D.p(d, "Because the greater part of operational emissions arises from "
           "electricity consumption, the measures that reduce carbon are "
           "largely the same as those that reduce operating cost: conveying "
           "the flow by gravity wherever possible, minimising lift, selecting "
           "efficient equipment, and generating renewable energy on site. "
           "Provision for photovoltaic generation within the plant perimeter "
           "is included in the land requirement.")

    D.p(d, "Resource efficiency, in-country value and the use of nature-based "
           "solutions are assessed for each option and carried into the "
           "comparison in Section 38.")

    # --------------------------------------------------------------- 35
    D.h(d, 1, "35   Cost")

    D.h(d, 2, "35.1   Basis")
    D.table(d, ["Item", "Basis"], [
        ["Accuracy", "plus or minus twenty per cent at concept stage"],
        ["Measurement", "CESMM3"],
        ["Rates", "current market rates, from recent tender and contract "
                  "documents"],
        ["Price basis", "current prices at the date of the estimate"],
        ["Presentation", "by system element"],
    ], widths=[4.4, 12.1], font=9.5)

    D.h(d, 2, "35.2   Scope of the estimate")
    D.p(d, "The estimate covers the works, the associated costs and the "
           "provisions, as set out below.")
    D.bullet(d, "excavation by depth and by ground condition, trench support, "
                "bedding and backfill, pipework, manholes, property "
                "connections, road reinstatement, traffic management, "
                "crossings, and testing.", lead="Collection network — ")
    D.bullet(d, "land, civil structures, pumps and station pipework, "
                "electrical supply and standby generation, control and "
                "telemetry, odour control, and the force main with its "
                "chambers and valves.", lead="Lifting stations — ")
    D.bullet(d, "land, site preparation and flood protection, inlet works, "
                "tanker reception, biological treatment, clarification, "
                "tertiary treatment, disinfection, the sludge line, chemical "
                "systems, odour control, electrical and control installations, "
                "buildings, and commissioning.", lead="Treatment plant — ")
    D.bullet(d, "pipework, storage, boosting, filling stations and customer "
                "connections.", lead="Treated effluent network — ")
    D.bullet(d, "design and supervision, survey and investigation, "
                "environmental assessment, consents and land, and physical and "
                "price contingency.", lead="Associated costs — ")

    _pending(d, "The estimate will be presented with the options in the next "
                "revision.")

    # --------------------------------------------------------------- 36
    D.h(d, 1, "36   Risk")
    D.p(d, "A risk register is established at this stage and maintained "
           "through the project. Each risk carries a description, a "
           "likelihood, an impact expressed in cost or time, an owner and the "
           "mitigation adopted. Risks that fall on one option and not on "
           "another are identified as such, as they affect the comparison "
           "rather than only the total.")

    # --------------------------------------------------------------- 37
    D.h(d, 1, "37   Value engineering")
    p = D.p(d, "A formal value engineering study is required at the concept "
               "and preliminary stages for a treatment plant or pumping "
               "station above the stated threshold, carried out by an "
               "independent certified consultant. The study is arranged within "
               "the concept programme and its outcome reported.")
    N.add(p, "PAM-GUD-201, Table 27, page 93, and its accompanying note.")

    # --------------------------------------------------------------- 38
    D.h(d, 1, "38   Comparison and recommendation")
    D.p(d, "The options are compared by the method described in Section 21.3. "
           "The comparison presents, for each option, the capital cost by "
           "phase, the operating cost by year, the net present value over "
           "twenty-five years, the carbon footprint, and the assessment "
           "against each of the remaining criteria, together with the results "
           "of the sensitivity tests.")

    eq = D.next_eq()
    M.display(d, M.seq(UP("NPV"), M.EQ,
                       M.nary("∑", M.seq(R("t"), R("=0")), R("n"),
                              M.frac(M.sub(R("C"), R("t")),
                                     M.sup(M.delim(M.seq(R("1"), M.PLUS, R("i"))),
                                           R("t"))))), number=eq)
    D.table(d, ["Symbol", "Meaning", "Value"], [
        ["C t", "net cost in year t", "—"],
        ["i", "discount rate", "5 per cent"],
        ["n", "evaluation period", "25 years"],
    ], widths=[2.6, 9.4, 4.5], font=9)

    D.p(d, "")
    _pending(d, "The comparison and the recommended option will be presented "
                "in the next revision.")


# ===================================================== PART H
def part_h(d):
    D.part(d, "H", "Delivery")

    # --------------------------------------------------------------- 39
    D.h(d, 1, "39   Implementation roadmap")
    D.p(d, "An implementation roadmap is prepared for the recommended option, "
           "defining the scope of the subsequent design stages, the "
           "procurement route for each element, the phasing of construction, "
           "and the framework by which performance is monitored once the works "
           "are in service.")

    _pending(d, "The roadmap follows the selection of the recommended option "
                "and will be presented with it.")

    # --------------------------------------------------------------- 40
    D.h(d, 1, "40   Contracting strategy")
    D.p(d, "The contracting strategy establishes how the works are packaged "
           "and procured. It is developed with Nama Water Services in a "
           "dedicated workshop, and considers the division of the works into "
           "packages, the procurement route for each, and the interfaces "
           "between them.")

    # --------------------------------------------------------------- 41
    D.h(d, 1, "41   Project integration")
    p = D.p(d, "A project integration plan sets out how the water and "
               "wastewater components are coordinated through design, "
               "construction and commissioning. It also addresses the "
               "rehabilitation or replacement of the existing potable water "
               "network where its performance is found to be unsatisfactory.")
    N.add(p, "PAM-GUD-201, Section 13, page 107.")

    # --------------------------------------------------------------- 42
    D.h(d, 1, "42   Conclusions")
    D.p(d, "The design basis for the wastewater and treated effluent systems "
           "is established and is set out in Part C. The data supplied has "
           "been assessed, and the datasets that are usable, those that "
           "require correction and those that relate to areas outside the "
           "project have been identified in Part B.")
    D.p(d, "The existing wastewater assets within the study area comprise "
           "310.9 kilometres of gravity sewer, 33.2 kilometres of force main "
           "and 45.7 kilometres of treated effluent main. The potable water "
           "network within the area comprises 647.8 kilometres of mains. The "
           "number of properties on each plot and the category of use have "
           "been established from 33,970 electricity accounts, and an "
           "occupancy rate of 5.32 persons per property has been derived and "
           "checked.")
    D.p(d, "A topographic and utility survey covering the whole study area is "
           "in progress. It will establish the levels, diameters and condition "
           "that the supplied datasets do not carry, and its completion is the "
           "principal step between this revision and the next.")

    D.h(d, 2, "42.1   Recommendations")
    D.p(d, "It is recommended that Nama Water Services confirm the six matters "
           "set out in Section 5, and that the datasets identified in Section "
           "7 as requiring correction or clarification be resolved, so that "
           "the flow series, the options and the appraisal can be completed on "
           "an agreed basis.")

    # --------------------------------------------------------------- 43
    D.h(d, 1, "43   Appendices")
    D.table(d, ["Appendix", "Content"], [
        ["A", "Data register and sources"],
        ["B", "Design criteria, with references"],
        ["C", "Population and demand calculations"],
        ["D", "Drawings and figures"],
        ["E", "Register of matters requiring confirmation"],
    ], widths=[3.0, 13.5], font=9.5)
    D.p(d, "")
    _pending(d, "The appendices will be issued with the next revision.")
