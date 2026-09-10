"""Part A - project, scope and process.   Part B - data."""
import os

import data_facts as F
import doc as D
import notes as N

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def _fig(d, name, caption, w=16.0):
    """A map goes on its own A3 landscape page. At 16 cm in a portrait
    column the legend and the data box are not readable."""
    D.wide_figure(d, os.path.join(IMG, name + ".png"), caption, size="A3")


# ===================================================== PART A
def part_a(d):
    D.part(d, "A", "Project, scope and process")

    # ---------------------------------------------------------------- 1
    D.h(d, 1, "1   Introduction and background")
    D.p(d, "Nama Water Services is developing wastewater collection, treated "
           "effluent distribution and sewage treatment for the Wilayat of "
           "Ibri. Renardet S.A. & Partners has been appointed to provide "
           "consultancy services for the design and supervision of these "
           "works.")
    D.p(d, "This report is the concept design deliverable. It establishes the "
           "design basis, records and assesses the data collected, and sets "
           "out the framework within which options for the sewer network, the "
           "treated effluent network and the treatment plant are developed.")

    D.h(d, 2, "1.1   Objectives")
    D.p(d, "The Terms of Reference set three objectives for the work: to "
           "verify the Regional Master Plan, to establish the ultimate "
           "expected sewage flow in the Ibri catchment, and to develop the "
           "concept, preliminary and detailed designs together with the tender "
           "documentation.")

    D.h(d, 2, "1.2   Structure of this report")
    D.p(d, "The report follows the structure approved for the concept stage. "
           "Part A records the project and its process. Part B presents the "
           "data and the assessment of it. Part C sets out the design basis. "
           "Part D establishes demand and flow. Part E assesses the existing "
           "system. Part F presents the options. Part G carries the technical "
           "and financial appraisal, and Part H the delivery arrangements.")

    # ---------------------------------------------------------------- 2
    D.h(d, 1, "2   Scope and boundaries", page_break=True)

    D.h(d, 2, "2.1   The study area")
    p = D.p(d, "The study area covers 531.4 square kilometres and contains "
               "twenty-five named settlements. Ibri is the principal "
               "settlement; the remainder are distributed along the wadi "
               "system and the main road corridors.")
    N.add(p, "Area measured in the project geographic information system from "
             "the boundary supplied with the Inception Report, computed in "
             "UTM zone 40 North.")

    _fig(d, "M01_location",
         "Project location and study area boundary, showing the twenty-five "
         "settlements within the Wilayat of Ibri.")

    D.h(d, 2, "2.2   Boundary")
    p = D.p(d, "Two boundary datasets were issued with the Inception Report. "
               "The two differ in extent. The larger of the two has been "
               "adopted for the work presented here so that no part of the "
               "area is omitted, and confirmation of the approved boundary is "
               "requested.")
    N.add(p, "Project_Boundary.kmz and Final_Boundary_IBRI.kmz, both supplied "
             "in the Inception Report package.")

    D.h(d, 2, "2.3   Coordinate system")
    D.p(d, "All spatial data is held and all measurements are made in "
           "Universal Transverse Mercator zone 40 North on the WGS 84 datum. "
           "Datasets supplied in geographic coordinates have been "
           "reprojected. Levels are referenced to the terrain model described "
           "in Section 8.")

    # ---------------------------------------------------------------- 3
    D.h(d, 1, "3   Programme and design stages")
    D.p(d, "The design comprises four stages: concept design, preliminary "
           "design, detailed design and the preparation of tender documents. "
           "Each stage is submitted for review and approval before the "
           "following stage begins.")
    p = D.p(d, "The Terms of Reference allow sixty days for the concept design "
               "and a further twenty-one days for review. The preliminary "
               "design stage begins on approval of the concept design for the "
               "treatment plant.")
    N.add(p, "Appendix to the Form of Bid, page 147, restated as a contract "
             "term at page 177 of the tender document.")
    D.p(d, "Two programmes have been issued during mobilisation, in the "
           "kick-off presentation and in the Inception Report. Confirmation of "
           "the governing programme is requested.")

    D.h(d, 2, "3.1   Deliverables at the concept stage")
    p = D.p(d, "The Terms of Reference set out forty numbered deliverables for "
               "the concept stage. They are grouped below by subject. Those "
               "marked as issued form part of this report or accompany it; the "
               "remainder follow in the next revision as the survey and the "
               "options are completed.")
    N.add(p, "Scope of Work, pages 63 and 64 of the tender document.")

    D.tab_caption(d, "Concept stage deliverables")
    D.table(d, ["Deliverable", "Position"], [
        ["Executive summary and project schedule", "Issued"],
        ["Data collection report and assessment of the data", "Issued"],
        ["Design criteria and design basis", "Issued"],
        ["Population forecasting and flow projection at five-year intervals",
         "Basis issued; series follows confirmation of the design horizon"],
        ["Topographic survey and geotechnical investigation",
         "Survey in progress"],
        ["As-built records and GIS for the existing systems",
         "Follows the survey"],
        ["Hydraulic assessment of the existing systems", "Follows the survey"],
        ["Wastewater network options, not fewer than three", "Next revision"],
        ["Treated effluent network options, not fewer than three",
         "Next revision"],
        ["Treatment plant options, not fewer than three, with siting and phasing",
         "Next revision"],
        ["Pumping and lifting station concept design", "Next revision"],
        ["Treated effluent and sludge management strategy",
         "Framework issued; strategy in the next revision"],
        ["Excess effluent and emergency overflow provisions", "Next revision"],
        ["Environmental impact assessment for the plant location",
         "Follows confirmation of scope"],
        ["Cost estimates and life cycle cost", "Next revision"],
        ["Risk analysis and value engineering", "Next revision"],
        ["Multi-criteria comparison and recommended option", "Next revision"],
        ["Hydraulic models in SewerGEMS and WaterGEMS",
         "Follows confirmation of the software"],
        ["Contracting strategy and implementation plan", "Next revision"],
        ["Register of approvals and no objection certificates", "Maintained"],
    ], widths=[10.5, 6.0], font=9)

    D.h(d, 2, "3.2   Deliverables of the following stages")
    D.p(d, "The preliminary design develops the approved concept to an "
           "estimate within ten per cent, with full survey, hazard and "
           "operability study, and preliminary bills of quantities. The "
           "detailed design completes the engineering, the drawings and the "
           "priced bills. Tender documentation follows the approved detailed "
           "design.")

    # ---------------------------------------------------------------- 4
    D.h(d, 1, "4   Consultation record")
    D.p(d, "The following meetings have been held with Nama Water Services to "
           "the date of this report.")
    D.tab_caption(d, "Meetings held")
    D.table(d, ["Meeting", "Date", "Outcome"], [
        ["Kick-off meeting", "15 July 2026",
         "Project scope, approach, programme and organisation presented"],
        ["Inception Report submission", "August 2026",
         "Design basis, methodology and programme submitted"],
    ], widths=[5.0, 3.4, 8.1], font=9.5)
    D.p(d, "")
    D.p(d, "Coordination with the authorities holding assets in the project "
           "area is described in Section 33, together with the register of "
           "approvals and no objection certificates.")

    # ---------------------------------------------------------------- 5
    D.h(d, 1, "5   Matters requiring confirmation", page_break=True)
    D.p(d, "The following matters require confirmation from Nama Water "
           "Services. Each affects work that would otherwise be carried out "
           "twice, and confirmation is therefore requested at the earliest "
           "opportunity.")

    D.h(d, 2, "5.1   Design horizon")
    p = D.p(d, "The Terms of Reference define the design horizon as the year "
               "of project completion plus twenty-five years, or the ultimate "
               "saturated flow. The Inception Report states that the planning "
               "and demand assessment extends to the year 2100. The two are "
               "different bases and produce different results. Confirmation of "
               "the horizon to be adopted is requested.")
    N.add(p, "Terms of Reference, page 51 of the tender document; Inception "
             "Report Revision 0, Section 6.2.")

    D.h(d, 2, "5.2   Project boundary")
    D.p(d, "Two boundary datasets were issued with the Inception Report, "
           "differing in extent. Confirmation of the approved boundary is "
           "requested, together with the extent to be surveyed.")

    D.h(d, 2, "5.3   Project figures")
    D.p(d, "Figures 1, 2 and 3 of the tender define the project location, the "
           "areas requiring as-built records, and the areas subject to each "
           "design stage. They are supplied as images without coordinates. "
           "Georeferenced versions are requested so that the design areas can "
           "be established without ambiguity.")

    D.h(d, 2, "5.4   Hydraulic modelling software")
    p = D.p(d, "The Scope of Work requires the wastewater network to be "
               "modelled in SewerGEMS and the treated effluent network in "
               "WaterGEMS. The staffing schedule in the tender refers to a "
               "different package. Confirmation of the software to be used for "
               "the deliverable models is requested.")
    N.add(p, "Scope of Work, pages 56, 57, 62, 65 and 73; Bidding Form 24, "
             "page 123 of the tender document.")

    D.h(d, 2, "5.5   Environmental impact assessment")
    p = D.p(d, "The design guidelines place environmental impact assessment "
               "scoping at the preliminary design stage in one clause and the "
               "full assessment at the concept and preliminary stages in "
               "another. Confirmation of the scope required at this stage is "
               "requested.")
    N.add(p, "PAM-GUD-201, Table 2, pages 19 to 22, and Section 6.1.4.3, "
             "page 44.")

    D.h(d, 2, "5.6   Terminology")
    D.p(d, "Confirmation is requested that the term TE, as used in the Terms "
           "of Reference and in this report, is understood to mean treated "
           "effluent.")

    D.h(d, 2, "5.7   Design manual reference")
    p = D.p(d, "The Terms of Reference require the treatment plant location "
               "report to follow item 2.1 of Section 05 of the Wastewater "
               "Design Manual. The current revision of PAM-GUD-203 consolidated "
               "and renumbered the former manuals, and the corresponding "
               "content is now Section 10.1, Site Selection. The report follows "
               "Section 10.1, and confirmation is requested.")
    N.add(p, "PAM-GUD-203 Revision 01, page 2, records the consolidation of "
             "the former manuals. Site selection is at pages 63 and 64.")


# ===================================================== PART B
def part_b(d):
    D.part(d, "B", "Data")

    # ---------------------------------------------------------------- 6
    D.h(d, 1, "6   Data collection")
    D.p(d, "Data has been requested from Nama Water Services and from the "
           "authorities holding assets in the project area. The table below "
           "records what has been requested and the position at the date of "
           "this report.")

    D.chart(d, "C06_register", 14.0)
    D.fig_caption(d, "Position of the data register at the date of issue.")

    D.tab_caption(d, "Data register")
    D.table(d, ["Dataset", "Received", "Position"], F.REGISTER,
            widths=[5.2, 2.2, 9.1], font=9)

    D.p(d, "")
    D.p(d, "A topographic and utility survey covering the whole study area is "
           "in progress. It will establish cover and invert levels, diameters, "
           "materials and condition for the existing sewer, force main and "
           "treated effluent networks, together with the lifting stations, the "
           "topography and the cadastral boundaries including plot gates. The "
           "results will be incorporated in the next revision of this report.")

    # ---------------------------------------------------------------- 7
    D.h(d, 1, "7   Assessment of the data", page_break=True)
    D.p(d, "Each dataset has been loaded into the project geographic "
           "information system, reprojected where necessary, and checked "
           "against the project boundary. This section records the quantity of "
           "each dataset, the proportion falling within the study area, and "
           "the limitations identified.")

    D.picture(d, os.path.join(IMG, "D2_data.png"), 15.5)
    D.fig_caption(d, "The assessment applied to each dataset supplied.")

    D.h(d, 2, "7.1   Wastewater assets")
    p = D.p(d, "The wastewater dataset supplied by Nama Water Services holds "
               "two networks, not one. They are distinguished by the "
               "operational status field, and the distinction is confirmed by "
               "four further fields that agree with it on every record.")
    N.add(p, "Field OP_STATUE on SEWERLINE_IBRI, FORCEMAIN_IBRI and "
             "TE_LINE_IBRI. Value 1 denotes the constructed network and value "
             "0 the proposed network.")

    D.tab_caption(d, "The two networks and how they are distinguished")
    D.table(d, ["", "Constructed network", "Proposed network"], [
        ["Operational status", "1", "0"],
        ["Installation date", "1 January 2006", "not recorded"],
        ["Source", "drawings, and closed-circuit television",
         "asset planning"],
        ["Project code", "5A-1 to 5A-5", "SUREKHA"],
        ["Remark", "reference data",
         "large urban area gravity, pumping main and treated effluent "
         "networks"],
    ], widths=[3.4, 6.6, 6.5], font=8.5)

    D.p(d, "")
    D.p(d, "On that basis the assets within the study area are as follows.")
    D.tab_caption(d, "Wastewater assets within the study area, by status")
    D.table(d, ["Asset", "Constructed features", "Constructed length",
                "Proposed features", "Proposed length"], F.WASTEWATER,
            widths=[3.4, 2.6, 2.6, 2.4, 5.5], font=8.5)

    D.p(d, "")
    p = D.p(d, "The distinction is material to the design. The constructed "
               "network extends to 111.6 kilometres of gravity sewer and 10.0 "
               "kilometres of force main, serving the central part of the "
               "town, and discharges through a single lifting station to the "
               "existing treatment plant. It is twenty years old and its "
               "condition is not recorded. The remaining 199.3 kilometres of "
               "gravity sewer, 23.2 kilometres of pumping main and the whole "
               "of the 45.7 kilometre treated effluent main shown in the "
               "dataset are proposed, not built. No treated effluent asset has "
               "been constructed.")
    N.add(p, "Lengths measured within the approved project boundary in "
             "EPSG:32640. The proposed alignments are recorded in the dataset "
             "as an earlier planning proposal and are not adopted as design "
             "input; they are shown for reference and to identify any "
             "commitment already made by the client.")

    p = D.p(d, "Two limitations apply to the constructed network. Neither "
               "diameter nor invert level is recorded on any constructed "
               "gravity segment, so the hydraulic capacity of the existing "
               "system cannot be established from the data supplied. The "
               "client's own records carry a remark that the data is not "
               "reliable and is to be used for reference only. The survey now "
               "in progress will establish diameters, levels and condition, "
               "and until it reports, the capacity of the existing network to "
               "accept additional flow is treated as unknown.")
    N.add(p, "Field REMARKS on the constructed records. The tender records "
             "that the existing network layout is based on available "
             "information, and that the preparation of complete as-built "
             "records and GIS forms part of the consultant's scope.")

    _fig(d, "M02_wastewater",
         "Wastewater assets within the study area. The constructed network, "
         "dated 2006, is shown distinctly from the alignments recorded in the "
         "dataset as proposed.")

    D.chart(d, "C05_assets", 13.0)
    D.fig_caption(d, "Length of wastewater asset within the study area, "
                     "separated into constructed and proposed.")

    D.h(d, 2, "7.2   Potable water network")
    D.p(d, "Two datasets describing potable water assets were supplied. They "
           "differ substantially in coverage.")

    D.tab_caption(d, "Potable water datasets")
    D.table(d, ["Dataset", "Features", "Quantity", "Within the study area",
                "Observation"], F.WATER,
            widths=[3.2, 1.6, 2.0, 2.8, 6.9], font=8.5)

    D.p(d, "")
    p = D.p(d, "The PAEW dataset provides 647.8 kilometres of water mains "
               "within the study area and is adopted as the source for utility "
               "interfaces. The second dataset, supplied under an Ibri file "
               "name, contains 3.5 kilometres of mains located approximately "
               "130 kilometres north-west of the project area; none of it "
               "falls within the study area. Confirmation is requested that "
               "the PAEW dataset is the current record for Ibri.")
    N.add(p, "The extent of the second dataset is 55.802 to 55.814 degrees "
             "east and 24.269 to 24.292 degrees north, in the vicinity of Al "
             "Buraymi.")

    _fig(d, "M03_water",
         "Potable water network within the study area, from the PAEW dataset.")

    D.h(d, 2, "7.3   Electricity accounts")
    p = D.p(d, "The electricity account dataset contains 33,970 records. Each "
               "record carries a tariff name and a coordinate. The dataset "
               "does not record land use, floor area or consumption, and the "
               "wilayat field is empty on every record. It therefore "
               "establishes the number and category of connections at a "
               "location, and is used for that purpose in Section 14.")
    N.add(p, "Fields present: identifier, tariff, coordinates in projected and "
             "geographic form, governorate and wilayat. The governorate is "
             "recorded as Dahira on all records; the wilayat field is empty on "
             "all records.")

    D.tab_caption(d, "Electricity accounts by tariff")
    D.table(d, ["Tariff", "Accounts", "Category adopted"], [
        ["Primary Account", "10,972", "Domestic"],
        ["Primary Account with National Subsidy", "5,272", "Domestic"],
        ["Additional Account", "6,344", "Domestic, additional dwelling"],
        ["Commercial", "9,385", "Non-domestic"],
        ["Government", "966", "Governmental"],
        ["Agricultural", "523", "Agricultural"],
        ["Cost Reflective Tariff", "499", "Large consumer, category to be confirmed"],
        ["Fisheries, Tourism, Industrial, Defence", "9", "Non-domestic and governmental"],
        ["**Total**", "**33,970**", ""],
    ], widths=[6.8, 2.6, 7.1], font=9)

    D.p(d, "")
    p = D.p(d, "The Cost Reflective Tariff is applied to consumers above a "
               "consumption threshold and is therefore a measure of size "
               "rather than of use. The 499 accounts carrying it are being "
               "resolved against the plot layer and by inspection.")
    N.add(p, "The tariff comprises three variants in the dataset: fixed rate "
             "(9 accounts), seasonal (298) and time of use (192).")

    D.chart(d, "C01_accounts", 14.5)
    D.fig_caption(d, "Electricity accounts by the category adopted for each "
                     "tariff. Domestic connections, including additional "
                     "dwellings on the same plot, account for two thirds of "
                     "the total.")

    _fig(d, "M04_electricity",
         "Electricity accounts by consumption category. The pattern of "
         "connections defines the developed extent of each settlement.")

    D.h(d, 2, "7.4   Cadastral and settlement data")
    D.p(d, "The cadastral plot layer supplied by the Ministry of Housing and "
           "Urban Planning provides plot geometry. It does not distinguish "
           "developed from undeveloped plots, does not record land use, and "
           "does not record the number of dwellings on a plot. Plots present "
           "on the ground are absent from the layer in places. A corrected "
           "layer is in preparation and the survey now in progress will "
           "establish the cadastral boundaries including plot gates.")

    _fig(d, "M05_settlements",
         "Settlements and cadastral plots within the study area.")

    D.h(d, 2, "7.5   Other datasets supplied")
    D.tab_caption(d, "Further datasets received")
    D.table(d, ["Dataset", "Extent", "Observation"], F.OTHER,
            widths=[3.6, 3.0, 9.9], font=9)

    D.p(d, "")
    D.p(d, "Five of the datasets supplied relate to areas outside the project "
           "boundary and have not been used. They are recorded here for "
           "completeness.")
    D.tab_caption(d, "Datasets relating to areas outside the project")
    D.table(d, ["Dataset", "Extent", "Location"], F.NOT_APPLICABLE,
            widths=[4.4, 3.6, 8.5], font=9)

    # ---------------------------------------------------------------- 8
    D.h(d, 1, "8   Survey and investigation", page_break=True)

    D.h(d, 2, "8.1   Topographic and utility survey")
    D.p(d, "A survey team is mobilised and working across the study area. The "
           "survey covers the existing sewer network, lifting stations, force "
           "mains and treated effluent network as built; the topography; and "
           "the cadastral boundaries including plot gates. Its outputs will "
           "establish the levels, diameters and condition that the supplied "
           "datasets do not carry, and will be incorporated in the next "
           "revision of this report.")

    D.h(d, 2, "8.2   Terrain model")
    p = D.p(d, "A bare-earth terrain model at 0.5 metre resolution covering "
               "the study area is in use for the work presented here. It will "
               "be superseded by the topographic survey for design purposes.")
    N.add(p, "The model excludes buildings and is held in UTM zone 40 North.")

    D.h(d, 2, "8.3   Geotechnical investigation and trial pits")
    D.p(d, "Geotechnical investigation and trial pits form part of the scope. "
           "Fifty trial pits are to be carried out at critical locations "
           "proposed by the consultant and approved by Nama Water Services. "
           "The programme of pits will be set out following the desk study of "
           "utility records described in Section 33.")

    # ---------------------------------------------------------------- 9
    D.h(d, 1, "9   Existing systems: as-built records and GIS")
    D.p(d, "The preparation of as-built records and geographic information for "
           "the existing sewer and treated effluent systems forms part of the "
           "scope of work. The datasets supplied provide the geometry of those "
           "systems; the survey in progress will establish the levels, "
           "diameters, materials and condition required to complete the "
           "records.")
    D.p(d, "The records will be prepared to the Nama Water Services "
           "specification and uploaded to the client's geographic information "
           "system for acceptance. Progress will be reported in the next "
           "revision.")
