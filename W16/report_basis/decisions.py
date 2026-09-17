"""What this report asks NWS to approve, and what it informs NWS is adopted. One list, read
by the summary at the front and by the register at the end, so the two cannot differ.

ask = "approve": a yes or a no is needed.
ask = "inform": the value is the guideline's or a stated assumption; it is adopted and
reported (engineer, 2026-09-14: do not ask for what the guideline already settles).
"""

DECISIONS = [
    # (ask, group, short title, what is asked or stated)
    ("approve", "Settlements and people", "Settlement boundaries",
     "Approve the twenty-five settlement boundaries redrawn so that every plot lies in one settlement and there are no gaps between them (Section 2)."),
    ("approve", "Settlements and people", "Persons per property",
     "Approve the persons per property calculated for each settlement, with the floor of 4.0, the cap of 6.12 and the rule for settlements under a thousand people (Section 3)."),
    ("approve", "Settlements and people", "Use of each plot",
     "Approve the use determined for each plot from the meters and the satellite image, as the basis for placing the loads (Section 4)."),
    ("approve", "Growth", "The overflow",
     "Approve the overflow: when a settlement's land is full, its further growth moves to its neighbours. Without it 75,000 people of the series have nowhere to go by 2070 (Section 6.3)."),
    ("approve", "Growth", "The design horizon",
     "Decide the design horizon: 2055, the opening year 2030 plus 25 years, with 244,914 people and 42,266 cubic metres a day; or 2070, the year the land is full, with 349,029 people and 60,099 cubic metres a day (Section 6.4)."),
    ("approve", "Growth", "The growth beyond 2050",
     "Approve the extension of the population series beyond 2050: the rise to 2.40 per cent a year by 2058 and that rate held to 2100. The series to 2050 is the client's own (Section 6.2)."),
    ("approve", "The network", "Gradients and self-cleansing at the concept stage",
     "Approve the concept-stage rule: pipes laid at the Table 11 minimum gradient; the tractive-force test at 1 pascal used only to list the pipes needing early washing, with a pipe carrying less than 1.5 l/s checked as if it carried 1.5. The guideline asks for the steeper of the two gradients; this is a departure (Section 7.3)."),
    ("inform", "Settlements and people", "The 126 meters with no plot within 15 metres",
     "They are left out of the plot loads: about 140 people (Section 3.3)."),
    ("inform", "Water and sewage rates", "Water demand and return",
     "164 litres per person per day, plus 22 per cent for shops and offices and 14 per cent for government, the values the guideline publishes for Adh Dhahirah; 85 per cent of domestic and tanker supply and 54 per cent of the rest return to the sewer. The published ratios are used in place of the unit rates per pupil, bed, employee and floor area until those quantities are held (Section 5)."),
    ("inform", "Water and sewage rates", "The industrial estates",
     "4,500 workers at Al Tayyeb and 1,800 at Tanam at 93 litres a day each, an assumption to be replaced by the estates' records when received (Section 5.3)."),
    ("inform", "Growth", "The connection ratio",
     "61 per cent of properties connected in 2030, the Inception Report's ratio, used only for the early-year self-cleansing check (Section 7.3)."),
    ("inform", "The network", "Infiltration and peak flow",
     "720 litres a day per kilometre of sewer, added to each pipe and left out of the early-year check; the Merrimack formula above 100 properties and the Peltier formula at 100 or fewer (Section 7.3)."),
    ("inform", "The network", "Depth",
     "12 metres of cover is the limit at the concept stage, with a pumping station before that point; the preliminary design looks deeper where the quantities allow the cost to be calculated (Section 7.4)."),
    ("inform", "The plant and the effluent", "STP flows and loads",
     "The average annual flow and the peak hourly flow with the 10 per cent margin as the guideline defines them; 60 grams of BOD and 80 grams of suspended solids per person per day, the guideline's minimum, until the laboratory data of the existing STP are received; the maximum day flow from that plant's records (Sections 7.5 and 7.6)."),
    ("inform", "The plant and the effluent", "Treated effluent",
     "95 per cent of the STP inflow produced as treated effluent and 10 per cent of it lost in the distribution network (Section 7.8)."),
]

APPROVALS = [d for d in DECISIONS if d[0] == "approve"]
INFORMED = [d for d in DECISIONS if d[0] == "inform"]

DATA_REQUESTS = [
    ("Tanker water and sewage tankers", "Filling-station volumes by area and sewage tanker deliveries to the STP, with their source",
     "Water supplied by tanker is not in any flow. It can only raise the loads."),
    ("Private wells", "Any record of private abstraction inside the study area",
     "The guideline requires it to be assessed. Not held."),
    ("Existing STP records", "Daily inflow and the laboratory results for the Ibri STP, three years",
     "Sets the maximum day flow and checks the per-person loads."),
    ("Industrial estates", "Workforce and water use of the Al Tayyeb and Tanam estates",
     "Replaces the assumed 4,500 and 1,800 workers."),
    ("Army camp", "Occupancy and drainage arrangement of the camp west of the town",
     "296 hectares with no meter in the dataset."),
    ("Ibri View", "The development plan of the resort at As Sulayf",
     "Two square kilometres announced; no load carried until the plan is issued."),
    ("Non-domestic quantities", "Pupils, beds, employees and floor areas by plot, where held",
     "Would allow the unit rates of the guideline in place of the ratios."),
]
