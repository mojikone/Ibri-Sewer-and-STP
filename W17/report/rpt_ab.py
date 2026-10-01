"""Chapter 1 - project, scope and process.   Chapter 2 - data."""
import os

import data_facts as F
import doc as D
import notes as N
import facts_w14 as FW
from basis_items import APPROVALS, INFORMED, DATA_REQUESTS, BASIS, SECTION
from deliverables import DELIVERABLES

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def _fig(d, name, caption, w=16.0):
    """A map goes on its own A4 landscape page. At 16 cm in a portrait
    column the legend and the data box are not readable."""
    D.wide_figure(d, os.path.join(IMG, name + ".png"), caption, size="A4")


# ===================================================== PART A
def part_a(d):
    D.chapter(d, "1.   Project, scope and process")
    D.p(d, "This chapter records the project and its scope, the study area and its "
           "boundary, the programme and the deliverables, the consultation held, and "
           "what is asked of Nama Water Services.")

    # ---------------------------------------------------------------- 1
    D.h(d, 2, "1.1.   Introduction and background")
    D.p(d, "Nama Water Services is developing wastewater collection, treated "
           "effluent distribution and sewage treatment for the Wilayat of "
           "Ibri. Renardet S.A. & Partners has been appointed to provide "
           "consultancy services for the design and supervision of these "
           "works.")
    D.p(d, "This report is the concept design deliverable. It establishes the "
           "design basis, records and assesses the data collected, and sets "
           "out the framework within which options for the sewer network, the "
           "treated effluent network and the treatment plant are developed.")

    D.h(d, 3, "1.1.1.   Objectives")
    D.p(d, "The Terms of Reference set three objectives for the work: to "
           "verify the Regional Master Plan, to establish the ultimate "
           "expected sewage flow in the Ibri catchment, and to develop the "
           "concept, preliminary and detailed designs together with the tender "
           "documentation.")

    D.h(d, 3, "1.1.2.   Structure of this report")
    D.p(d, "The report follows the structure approved for the concept stage. "
           "Chapter 1 records the project and its process. Chapter 2 presents "
           "the data and the assessment of it. Chapter 3 sets out the design "
           "basis. Chapter 4 establishes demand and flow. Chapter 5 assesses the "
           "existing system. Chapter 6 presents the options. Chapter 7 carries "
           "the technical and financial appraisal, and Chapter 8 the delivery "
           "arrangements. Appendix A holds the working behind Chapter 4.")

    # ---------------------------------------------------------------- 2
    D.h(d, 2, "1.2.   The study area")
    D.p(d, "This section describes the study area: where it lies and what it "
           "contains, its boundary, its ground and drainage, its climate, its "
           "roads and the flood hazard across it. The map on the next page shows "
           "the study area, its settlements as received and its place in Oman.")
    # the map sits here, ahead of 1.2.1: after it the subsections run on without a part-empty page
    _fig(d, "M01_location",
         "Project location and study area boundary, with the boundaries of the "
         "twenty-five settlements as received with the Inception Report. The inset "
         "places the study area in the Wilayat of Ibri and in Oman.")

    D.h(d, 3, "1.2.1.   Location and settlements")
    p = D.p(d, "The study area lies in the Wilayat of Ibri, in Adh Dhahirah "
               "Governorate in the north-west of Oman. It covers 531.4 square "
               "kilometres and contains twenty-five named settlements. Ibri is "
               "the principal settlement; the remainder are distributed along "
               "the wadi system and the main road corridors.")
    N.add(p, "Area of the updated project boundary (Section 1.2.2), measured in "
             "the project geographic information system in UTM zone 40 North.")

    D.h(d, 3, "1.2.2.   Boundary")
    p = D.p(d, "The project boundary received covers 439.8 square kilometres. "
               "The cadastral plots of the twenty-five settlements, the planned "
               "ones included, reach beyond it in several places. The boundary "
               "has therefore been updated to take in every plot of those "
               "settlements, and covers 531.4 square kilometres. All the work "
               "presented here is on the updated boundary, and confirmation of "
               "it is requested (Section 1.5.4).")
    N.add(p, "Project_Boundary.kmz, received in July 2026. A second boundary, "
             "Final_Boundary_IBRI.kmz of 521.1 square kilometres, was issued "
             "with the Inception Report package; the updated boundary contains "
             "both.")

    D.h(d, 3, "1.2.3.   Coordinate system")
    D.p(d, "All spatial data is held and all measurements are made in "
           "Universal Transverse Mercator zone 40 North on the WGS 84 datum. "
           "Datasets supplied in geographic coordinates have been "
           "reprojected. Levels are referenced to the terrain model described "
           "in Section 2.3.")

    import rpt_area
    rpt_area.study_area(d)          # 1.2.4 topography, 1.2.5 climate, 1.2.6 roads, 1.2.7 flood hazard

    # ---------------------------------------------------------------- 3
    D.h(d, 2, "1.3.   Programme and design stages")
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

    D.h(d, 3, "1.3.1.   Deliverables at the concept stage")
    p = D.p(d, "The Terms of Reference set out forty numbered deliverables for "
               "the concept stage. They are grouped below by subject. Those "
               "marked as issued form part of this report or accompany it; the "
               "remainder follow in the next revision as the survey and the "
               "options are completed.")
    N.add(p, "Scope of Work, pages 63 and 64 of the tender document.")

    D.tab_caption(d, "Concept stage deliverables")
    D.table(d, ["Deliverable", "Position"], [[a, b] for a, b, _ in DELIVERABLES], widths=[10.5, 6.0], font=9)
    D.p(d, "")
    D.chart(d, "R08_deliverables", 14.5)
    D.fig_caption(d, "Position of the concept-stage deliverables at the date of issue.")

    D.h(d, 3, "1.3.2.   Deliverables of the following stages")
    D.p(d, "The preliminary design develops the approved concept to an "
           "estimate within ten per cent, with full survey, hazard and "
           "operability study, and preliminary bills of quantities. The "
           "detailed design completes the engineering, the drawings and the "
           "priced bills. Tender documentation follows the approved detailed "
           "design.")

    # ---------------------------------------------------------------- 4
    D.h(d, 2, "1.4.   Consultation record")
    D.p(d, "The following meetings have been held with Nama Water Services to "
           "the date of this report.")
    D.tab_caption(d, "Meetings held")
    D.table(d, ["Meeting", "Date", "Outcome"], [
        ["Kick-off meeting", "15 July 2026",
         "Project scope, approach, programme and organisation presented"],
        ["Inception Report submission", "August 2026",
         "Design basis, methodology and programme submitted"],
        ["Design basis meeting", "16 September 2026",
         "Progress reported; the Design Basis Report presented; seven "
         "decisions put to Nama Water Services, none taken at the meeting; a "
         "maximum gradient of 4 per cent from the tractive-force method at "
         "head pipes indicated by Nama Water Services"],
    ], widths=[5.0, 3.4, 8.1], font=9.5)
    D.p(d, "")
    D.p(d, "Coordination with the authorities holding assets in the project "
           "area is described in Section 7.6, together with the register of "
           "approvals and no objection certificates.")

    # ---------------------------------------------------------------- 5
    D.h(d, 2, "1.5.   Decisions requested and matters requiring confirmation", page_break=True)
    D.p(d, f"Only what the guidelines do not settle is put to Nama Water Services "
           f"for a decision. Everything else is adopted and reported: a value the "
           f"guidelines give, a value of the Inception Report, or an assumption "
           f"stated as such. Section 1.5.1 lists all {len(APPROVALS) + len(INFORMED)} "
           f"items with the status of each. Section 1.5.2 gives the "
           f"{len(APPROVALS)} decisions in full; each can be answered with a yes, a "
           f"no, or one figure, and a no returns the design to the section named. "
           f"Section 1.5.3 gives the {len(INFORMED)} adopted values in full. Section "
           f"1.5.4 lists the other matters that await confirmation, and Section 1.5.5 "
           f"the data requested. No decision had been taken at the date of this report.")

    D.h(d, 3, "1.5.1.   What is asked of Nama Water Services, and what is adopted")
    D.tab_caption(d, "Status of every item: a decision requested from Nama Water Services, or a value adopted and its basis")
    rows = []
    for i, (_, _g, title, _w) in enumerate(APPROVALS + INFORMED, 1):
        status, basis = BASIS[title]
        rows.append([str(i), title, f"**{status}**" if i <= len(APPROVALS) else status, basis, SECTION[title]])
    D.table(d, ["", "Item", "Status", "Why a decision is needed, or the basis of the adopted value", "Section"], rows,
            widths=[0.8, 3.9, 3.3, 6.6, 1.9], font=8.5, keep_together=False)

    D.h(d, 3, "1.5.2.   The decisions requested from Nama Water Services")
    grp = None
    for i, (_, g, title, what) in enumerate(APPROVALS):
        if g != grp:
            D.p(d, g, bold=True, colour=D.MID, size=11, space_after=3)
            grp = g
        D.numbered(d, what, lead=f"{title}.  ", restart=(i == 0))
        d.paragraphs[-1].paragraph_format.space_after = D.Pt(6)

    D.h(d, 3, "1.5.3.   The values adopted, for information")
    D.p(d, "These are not put to approval. They are the guidelines' own values, a "
           "value of the Inception Report, or assumptions stated as such, and the "
           "table of Section 1.5.1 says which.")
    D._step["n"] = len(APPROVALS)          # the numbering continues from the decisions
    grp = None
    for i, (_, g, title, what) in enumerate(INFORMED):
        if g != grp:
            D.p(d, g, bold=True, colour=D.MID, size=11, space_after=3)
            grp = g
        D.numbered(d, what, lead=f"{title}.  ")
        d.paragraphs[-1].paragraph_format.space_after = D.Pt(6)

    D.h(d, 3, "1.5.4.   Other matters requiring confirmation")
    D.p(d, "Each of the matters below affects work that would otherwise be "
           "carried out twice, and confirmation is requested at the earliest "
           "opportunity.")
    D.tab_caption(d, "Other matters requiring confirmation")
    D.table(d, ["Matter", "What is to be confirmed", "Reference"], [
        ["Project boundary", "The updated project boundary of 531.4 square "
         "kilometres, which takes in every plot of the twenty-five settlements, "
         "and the extent to be surveyed", "Section 1.2.2"],
        ["Project figures", "Georeferenced versions of Figures 1, 2 and 3 of the "
         "tender, which define the project location, the areas requiring as-built "
         "records and the areas subject to each design stage; they are supplied "
         "as images without coordinates", "Scope of Work"],
        ["Hydraulic modelling software", "The software for the deliverable "
         "models: the Scope of Work requires SewerGEMS and WaterGEMS, and the "
         "staffing schedule of the tender refers to a different package",
         "Scope of Work, pages 56, 57, 62, 65 and 73; Bidding Form 24, page 123"],
        ["Environmental impact assessment", "The scope required at this stage: "
         "the guidelines place the scoping at the preliminary design in one "
         "clause and the full assessment at the concept and preliminary stages "
         "in another", "PAM-GUD-201, Table 2, pages 19 to 22, and Section 6.1.4.3, page 44"],
        ["Terminology", "That TE, as used in the Terms of Reference and in this "
         "report, means treated effluent", "Abbreviations"],
        ["Design manual reference", "That the treatment plant location report "
         "follows Section 10.1 of PAM-GUD-203, Site Selection, which replaced "
         "item 2.1 of Section 05 of the former Wastewater Design Manual",
         "PAM-GUD-203 Revision 01, pages 2, 63 and 64"],
        ["Governing programme", "Which of the two programmes issued during "
         "mobilisation governs", "Section 1.3"],
        ["Maximum gradient by tractive force", "How the limit of 4 per cent at "
         "head pipes, indicated by Nama Water Services on 16 September 2026, is "
         "to be applied", "Section 3.3.2"],
        ["Margin and peak at the treatment plant", "That the 10 per cent margin "
         "is applied to the peak hourly flow as to the average annual flow",
         "Section 3.4.1"],
        ["Potable water record", "That the PAEW dataset is the current record "
         "for Ibri", "Section 2.2.2"],
    ], widths=[3.6, 8.6, 4.3], font=8.8, keep_together=False)

    D.h(d, 3, "1.5.5.   Data requested")
    D.p(d, f"{len(DATA_REQUESTS)} items would improve or confirm the numbers in "
           f"this report. None of them stops the concept design; each replaces "
           f"an assumption with a record.")
    D.tab_caption(d, "Data requests")
    D.table(d, ["Item", "What is asked for", "Why"], [[a, b, c] for a, b, c in DATA_REQUESTS],
            widths=[3.6, 6.6, 6.3], font=9)


# ===================================================== PART B
def part_b(d):
    D.chapter(d, "2.   Data")
    D.p(d, "This chapter records the data collected, the checks applied to each dataset "
           "and what they found, and the surveys in progress.")

    # ---------------------------------------------------------------- 6
    D.h(d, 2, "2.1.   Data collection")
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
    D.h(d, 2, "2.2.   Assessment of the data", page_break=True)
    D.p(d, "Each dataset has been loaded into the project geographic "
           "information system, reprojected where necessary, and checked "
           "against the project boundary. This section records the quantity of "
           "each dataset, the proportion falling within the study area, and "
           "the limitations identified.")

    D.picture(d, os.path.join(IMG, "D2_data.png"), 15.5)
    D.fig_caption(d, "The assessment applied to each dataset supplied.")

    D.h(d, 3, "2.2.1.   Wastewater assets")
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

    D.h(d, 3, "2.2.2.   Potable water network")
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

    D.h(d, 3, "2.2.3.   Electricity accounts")
    p = D.p(d, "The electricity account dataset contains 33,971 records, each "
               "carrying a tariff name and a coordinate. It records neither "
               "land use, floor area nor consumption, and the wilayat field is "
               "empty on every record. It establishes the number and category "
               "of connections at a location, and is used for that purpose in "
               "Section 4.1. The data is of 2024, which is the base year of "
               "this report.")
    N.add(p, "Fields present: identifier, tariff, coordinates in projected and "
             "geographic form, governorate and wilayat. The governorate is "
             "recorded as Dahira on all records; the wilayat field is empty on "
             "all records. The positions were adjusted onto the cadastre by "
             "the client before issue.")

    D.tab_caption(d, "Electricity accounts by tariff and the category adopted")
    D.table(d, ["Tariff", "Accounts", "Category adopted"], [
        ["Primary Account", "10,973", "Domestic: one property"],
        ["Primary Account with National Subsidy", "5,272", "Domestic: one property"],
        ["Additional Account", "6,344", "Domestic: one property, a further one on the same plot"],
        ["Commercial, Fisheries, Tourism", "9,392", "Non-domestic"],
        ["Government, Defence", "967", "Governmental"],
        ["Agricultural", "523", "Agricultural: an irrigation pump, no sewage"],
        ["Industrial", "1", "Special consumption"],
        ["Cost Reflective Tariff", "499", "Large consumer; use established in Section 4.3"],
        ["**Total**", "**33,971**", ""],
    ], widths=[6.8, 2.6, 7.1], font=9)

    D.p(d, "")
    p = D.p(d, "The Cost Reflective Tariff is applied to consumers above a "
               "consumption threshold and is therefore a measure of size "
               "rather than of use. The 499 accounts carrying it have been "
               "placed one by one against public records, and each carries "
               "the use found and the evidence for it. Section 4.3.1 gives the "
               "result.")
    N.add(p, "The tariff comprises three variants in the dataset: fixed rate "
             "(9 accounts), seasonal (298) and time of use (192).")

    D.chart(d, "C01_accounts", 14.5)
    D.fig_caption(d, "Electricity meters by the category adopted, after the "
                     "large consumers were placed. Domestic connections, "
                     "including further properties on the same plot, are two "
                     "thirds of the total.")

    _fig(d, "M04_electricity",
         "Electricity meters by category, placed on the plots. The pattern "
         "of connections defines the developed extent of each settlement.")

    D.h(d, 3, "2.2.4.   Cadastral and settlement data")
    D.p(d, "The cadastral plot layer supplied by the Ministry of Housing and "
           "Urban Planning, in the issue of September 2026, holds 77,265 "
           "plots with a built-or-future flag and a land-use class. The "
           "flag follows the electricity meters and is reliable. The class "
           "is not: it carries no government category, records whole "
           "districts under codes that mean unclassified, and disagrees with "
           f"the meters on {FW.fmt(FW.cadastre_disagreement() * 100)} per cent of the built plots. The use of each plot is "
           "therefore determined from the meters and the satellite image, as "
           "Section 4.1.5 sets out. The survey now in progress will establish the "
           "cadastral boundaries including plot gates.")
    D.p(d, "The settlement boundaries supplied with the Inception Report are "
           "twenty-six polygons for twenty-five settlements, Al Aynayn being "
           "drawn as two. They outline the built cores and leave the land "
           "between them unassigned. Section 4.1.2 describes how every plot has "
           "been assigned to a settlement and the boundaries redrawn to meet.")

    D.h(d, 3, "2.2.5.   Other datasets supplied")
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
    D.h(d, 2, "2.3.   Survey and investigation")

    D.h(d, 3, "2.3.1.   Topographic and utility survey")
    D.p(d, "A survey team is mobilised and working across the study area. The "
           "survey covers the existing sewer network, lifting stations, force "
           "mains and treated effluent network as built; the topography; and "
           "the cadastral boundaries including plot gates. Its outputs will "
           "establish the levels, diameters and condition that the supplied "
           "datasets do not carry, and will be incorporated in the next "
           "revision of this report.")

    D.h(d, 3, "2.3.2.   Terrain model")
    p = D.p(d, "A bare-earth terrain model at 0.5 metre resolution covering "
               "the study area is in use for the work presented here. It will "
               "be superseded by the topographic survey for design purposes.")
    N.add(p, "The model excludes buildings and is held in UTM zone 40 North.")

    D.h(d, 3, "2.3.3.   Geotechnical investigation and trial pits")
    D.p(d, "Geotechnical investigation and trial pits form part of the scope. "
           "Fifty trial pits are to be carried out at critical locations "
           "proposed by the consultant and approved by Nama Water Services. "
           "The programme of pits will be set out following the desk study of "
           "utility records described in Section 7.6.")

    # ---------------------------------------------------------------- 9
    D.h(d, 2, "2.4.   Existing systems: as-built records and GIS")
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
