"""The concept-stage deliverables and where each stands, one list for the table of Section
1.3.1 and for the chart beside it. Positions at the meeting of 16 September 2026."""

# (deliverable, position, category)
CATEGORIES = [("issued", "Issued with this report"), ("progress", "In progress"), ("survey", "Follows the survey"),
              ("confirm", "Awaits a confirmation"), ("next", "Next revision")]

DELIVERABLES = [
    ("Executive summary and project schedule", "Issued", "issued"),
    ("Data collection report and assessment of the data", "Issued", "issued"),
    ("Design criteria and design basis", "Issued", "issued"),
    ("Population forecasting and flow projection at five-year intervals",
     "Issued: population and flow per settlement at five-year intervals to saturation, and per plot", "issued"),
    ("Topographic survey and geotechnical investigation", "Survey team mobilised; in progress", "progress"),
    ("As-built records and GIS for the existing systems", "Follows the survey", "survey"),
    ("Hydraulic assessment of the existing systems", "Follows the survey", "survey"),
    ("Concept hydraulic calculations and capacities",
     "Sewer network completed on the basis of this report; treated effluent network and treatment plant begun", "progress"),
    ("Wastewater network options, not fewer than three", "Next revision", "next"),
    ("Treated effluent network options, not fewer than three", "Next revision", "next"),
    ("Treatment plant options, not fewer than three, with siting and phasing",
     "Siting and decision matrix in progress; options in the next revision", "progress"),
    ("Pumping and lifting station concept design", "Next revision", "next"),
    ("Treated effluent and sludge management strategy", "Framework issued; strategy in the next revision", "next"),
    ("Excess effluent and emergency overflow provisions", "Next revision", "next"),
    ("Environmental impact assessment for the plant location", "Follows confirmation of scope", "confirm"),
    ("Cost estimates and life cycle cost", "Method adopted, 25 years at 5 per cent; estimates in the next revision", "progress"),
    ("Risk analysis and value engineering", "Next revision", "next"),
    ("Multi-criteria comparison and recommended option", "Next revision", "next"),
    ("Hydraulic models in SewerGEMS and WaterGEMS", "Follows confirmation of the software", "confirm"),
    ("Contracting strategy and implementation plan", "Next revision", "next"),
    ("Register of approvals and no objection certificates", "Maintained", "progress"),
]
