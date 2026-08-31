"""Revision 01 additions: the sections the first issue did not carry."""
import os

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

import doc as D
import omml as M

UP = M.up
R = M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[2.6, 10.4, 3.5], font=9)


def _source(d, text):
    D.p(d, "Source: " + text, size=9, italic=True, colour=D.GREY, space_after=10)


def _fig(d, name, caption, w=15.5):
    D.picture(d, os.path.join(IMG, name + ".png"), w)
    D.fig_caption(d, caption)


# ============================================ 10  SELF-CLEANSING SCHEDULE
def s10_selfcleansing(d):
    D.h(d, 1, "10   Self-cleansing and the maintenance washing schedule",
        page_break=True)

    D.h(d, 2, "10.1   Purpose")
    D.p(d, "A new sewer does not carry its design flow on the day it opens. It "
           "carries whatever the connected properties generate, which for the "
           "first years is a fraction of the design figure. Below a certain "
           "velocity solids settle rather than move, and the network has to be "
           "washed until the flow can do the work itself. This section "
           "establishes for how long, and which pipes.")

    D.callout(d, "This is the one calculation where over-estimating is the "
                 "dangerous error.",
              "Everywhere else in this document, assuming too much flow is "
              "conservative. Here it is the opposite: an optimistic early-year "
              "flow declares the network self-scouring while it is silting, and "
              "the maintenance team is told to stop washing too soon. Use the "
              "low growth and low connection case.")

    _fig(d, "F10_selfcleansing",
         "Setting the washing schedule. The output is a table of pipe against "
         "year, not a single date.")

    D.h(d, 2, "10.2   Method")
    D.numbered(d, "Take the year-by-year flow series from Section 7, in its low "
                  "case rather than its design case.")
    D.numbered(d, "Apply the connection ratio for the year: only connected "
                  "properties contribute.")
    D.numbered(d, "Route those flows through the network and take the peak flow "
                  "in each pipe.")
    D.numbered(d, "Compute the velocity at that flow, part full, using the "
                  "gradient and diameter actually laid.")
    D.numbered(d, "Record, for each pipe, the first year in which it reaches "
                  "0.75 m/s at peak. Until that year it needs scheduled "
                  "washing.")

    D.h(d, 2, "10.3   Why a pipe laid to the minimum gradient still fails this")
    D.p(d, "Section 9.5 established that the guideline's minimum gradients "
           "deliver 0.75 m/s when the pipe runs full. At part-full flows the "
           "velocity is lower, and in the opening years the pipes run far below "
           "their design depth.")

    D.tab_caption(d, "Velocity at a minimum-gradient pipe, by depth of flow")
    D.table(d, ["Proportional depth d/D", "Velocity", "Status"],
            [["0.65, the design depth up to 350 mm", "0.82 m/s", "passes"],
             ["0.50, the design depth above 350 mm", "0.75 m/s", "**no margin**"],
             ["0.30", "0.58 m/s", "fails"],
             ["0.20", "0.46 m/s", "fails"],
             ["0.10", "0.31 m/s", "fails"]],
            widths=[7.4, 4.5, 4.6], font=9.5)

    D.p(d, "")
    D.p(d, "The consequence is that laying steeper than the minimum buys "
           "earlier self-cleansing, and that is a legitimate trade to make "
           "explicitly: a little more excavation now against fewer years of "
           "tankered washing later. It is a whole-life cost question, not a "
           "hydraulic one, and belongs in the appraisal.")

    D.h(d, 2, "10.4   What the guideline says, and does not say")
    D.p(d, "The guideline acknowledges the problem and declines to solve it. It "
           "states that during early development phases the actual flow will "
           "usually be below the design flow, inducing a risk of clogging, and "
           "that the operator should carry out more frequent inspections and "
           "cleansing during this period. It sets no frequency, no duration and "
           "no threshold.")

    D.callout(d, "Yellow tankers work in our favour here.",
              "Properties still discharging to tanker are not connected, so "
              "they reduce early flow. But the guideline requires the "
              "collection system to assume the same coverage as the water "
              "supply, reaching full connection by the end of the planning "
              "period. The washing schedule should be built on the connection "
              "ramp actually forecast, not on full connection.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "10.5   Output")
    D.p(d, "The deliverable is a table of pipe against year showing which runs "
           "need washing and until when, and a total washing effort by year "
           "that can be costed as an operating expense in the appraisal. That "
           "last point matters: a network laid at minimum gradients is cheaper "
           "to build and more expensive to operate for its first decade, and "
           "unless the washing appears in the operating cost the comparison "
           "between options is wrong.")
    _source(d, "G203 §4.2.6 p28 for the acknowledgement; §4.2.2.1 p26 for the "
               "velocity requirement; the part-full analysis is a project "
               "calculation.")


# ============================================ 12  SEPTICITY AND ODOUR
def s12_septicity(d):
    D.h(d, 1, "12   Septicity, hydrogen sulphide and odour in the network",
        page_break=True)

    D.h(d, 2, "12.1   Why it matters here")
    D.p(d, "Sewage that sits without oxygen turns septic. Sulphate-reducing "
           "bacteria produce hydrogen sulphide, which is toxic, smells at "
           "vanishingly low concentrations, and oxidises to sulphuric acid on "
           "the crown of the pipe, destroying concrete and corroding metal. In "
           "a hot climate the reactions run fast, which is why the guideline "
           "treats this as a design problem rather than an operating one.")

    D.h(d, 2, "12.2   The three levers")
    D.bullet(d, "long retention lets sulphide build. Force main retention "
                "should ideally stay under half an hour, and the guideline "
                "concedes this is rarely achieved.", lead="Retention time — ")
    D.bullet(d, "low velocity means both long retention and deposition. "
                "Gravity sewers at very low slopes carry the greatest risk.",
             lead="Velocity — ")
    D.bullet(d, "every drop, jump and unsubmerged discharge strips dissolved "
                "sulphide into the air, which is where the odour and the "
                "corrosion happen.", lead="Turbulence — ")

    D.h(d, 2, "12.3   Prediction")
    D.p(d, "The guideline offers a quantitative route and a qualitative one. "
           "The quantitative route is only partly usable.")

    eq = D.next_eq()
    M.display(d, M.seq(
        M.frac(R("dS"), R("dt")), M.EQ, R("3.23"), M.sub(R("M"), R("′")),
        M.delim(UP("EBOD"), "[", "]"), M.sup(R("r"), R("−1")), M.MINUS,
        R("2.1"), R("N"), M.sup(M.delim(M.seq(R("s"), R("v"))), R("0.375")),
        M.delim(R("S"), "[", "]"), M.sup(M.sub(R("d"), UP("m")), R("−1"))),
        number=eq)
    _params(d, [
        ["[S]", "sulphide concentration", "mg/l"],
        ["M′", "effective sulphide flux", "not stated in the source"],
        ["[EBOD]", "effective BOD", "mg/l"],
        ["r", "hydraulic radius", "not stated"],
        ["N", "empirical loss factor", "not stated"],
        ["s, v", "energy gradient and mean velocity", "not stated"],
        ["d m", "mean hydraulic depth, area over top width", "not stated"]])

    eq = D.next_eq()
    M.display(d, M.seq(M.delim(UP("EBOD"), "(", ")"), M.EQ,
                       M.delim(UP("BOD"), "(", ")"), M.TIMES,
                       M.sup(M.delim(R("1.07")), M.seq(R("T"), M.MINUS, R("20")))),
              number=eq)
    D.p(d, "The temperature correction converts BOD measured at 20 °C into the "
           "effective BOD at the actual sewage temperature. At 35 °C it "
           "multiplies the BOD by roughly 2.8, which is why the same network "
           "behaves very differently here than in a temperate climate.")

    D.callout(d, "The generation equation cannot be evaluated from the "
                 "guideline.",
              "Seven of its nine symbols carry no units, and no values are "
              "given for the sulphide flux or the loss factor. The force-main "
              "form is worse: its rate constant has neither a value nor a unit "
              "and its temperature function has no stated form. Both establish "
              "that sulphide rises with retention time and warm temperature; "
              "neither permits a number without going to Pomeroy and "
              "Parkhurst's original work.")

    D.p(d, "The qualitative route is usable as it stands. The guideline "
           "reproduces a scoring method against temperature, residence time, "
           "velocity and redox potential, summing to a risk band. Its bands "
           "overlap as printed, which is noted in Section 22.")

    D.h(d, 2, "12.4   Design measures, in the order the guideline prefers them")
    D.numbered(d, "Avoid pumping altogether wherever gravity is feasible.")
    D.numbered(d, "Where pumping is unavoidable, minimise retention — consider "
                  "twin mains so that low flows still move quickly.")
    D.numbered(d, "Discharge submerged, to absorb energy and avoid stripping "
                  "sulphide into the air. Inverted siphons are not permitted on "
                  "a pressure main discharge.")
    D.numbered(d, "Design gravity entries to pumping stations to minimise free "
                  "fall and turbulence.")
    D.numbered(d, "Keep air moving: vents no smaller than 150 mm and 6 m above "
                  "ground.")
    D.numbered(d, "Only then consider dosing — oxygen, nitrate, iron salts or "
                  "pH elevation. The guideline lists the methods and gives no "
                  "dose rates, so any dosing proposal is the designer's to "
                  "substantiate.")

    D.h(d, 2, "12.5   Design values where no field data exists")
    D.p(d, "At the termination of a pressure main, absent measurements, the "
           "guideline requires management and monitoring to be designed for an "
           "average hydrogen sulphide concentration between 50 and 100 ppm and "
           "a peak not exceeding 200 ppm.")
    _source(d, "G203 §7.7 p47, §11.5.3 p181-186, §11.3 p165-170; G203 Table 99 "
               "p185.")


# ============================================ 13  UTILITIES
def s13_utilities(d):
    D.h(d, 1, "13   Utility interfaces and crossings", page_break=True)

    D.h(d, 2, "13.1   Purpose")
    D.p(d, "A sewer alignment competes for the same corridor as water, "
           "electricity, telecom and, in places, gas and fuel. Clashes "
           "discovered on site are expensive; clashes discovered at concept "
           "stage are a routing decision.")

    _fig(d, "F11_utilities",
         "Handling a clash. The cost comparison runs both ways: sometimes it is "
         "cheaper to move their asset than ours.")

    D.h(d, 2, "13.2   What we hold, and what we do not")
    D.callout(d, "We have electricity meter points, not cable routes.",
              "The 33,970-point account layer locates customers. It says "
              "nothing about where the distribution cables run. The water mains "
              "in the NWS asset data total a few kilometres, which cannot serve "
              "a city of this size. Telecom and gas records are absent "
              "altogether. For clash purposes, the utility picture is close to "
              "blank and must be requested from each owner.")

    D.h(d, 2, "13.3   Method")
    D.numbered(d, "Obtain service drawings from every utility owner with assets "
                  "in the area — electricity distribution, telecom, gas and "
                  "fuel operators, the municipality and the roads authority.")
    D.numbered(d, "Superimpose the proposed alignment on each set.")
    D.numbered(d, "Identify where trial pits are needed: road intersections, "
                  "the routes of major existing services, and along the "
                  "expected routes of trunk sewers and rising mains.")
    D.numbered(d, "Agree the trial pit programme with NWS, obtain municipal "
                  "excavation approval, and notify the service owners.")
    D.numbered(d, "Where a clash is unavoidable, price moving our asset against "
                  "moving theirs, and obtain the owner's agreement for whichever "
                  "is cheaper.")

    D.p(d, "Fifty trial pits are specified in the scope, at critical locations "
           "proposed by the consultant and approved by NWS. The formal utility "
           "survey is a preliminary-stage obligation, but the concept design "
           "must already show route viability, so the desk study and the "
           "critical pits belong at this stage.")

    D.h(d, 2, "13.4   Clearances")
    D.tab_caption(d, "Separation from other services")
    D.table(d, ["Situation", "Requirement"],
            [["Sewage force main to water main, horizontal", "**3.0 m**"],
             ["Sewage force main crossing a water main",
              "**crosses under**, 450 mm minimum vertical clearance"],
             ["Shallow sewer beneath a major road or highway",
              "3 m minimum horizontal clearance, with a design check"],
             ["Another utility in the same trench",
              "placed on a separate bench on undisturbed soil"],
             ["Force main on a highway",
              "in the carriageway, at least 1 m from the kerb line"]],
            widths=[9.0, 7.5], font=9.5)

    D.p(d, "")
    D.p(d, "Beyond these, the clearance is whatever the owning authority "
           "specifies, and the guideline requires the design to respect the "
           "requirements of local municipality regulations and authorities for "
           "the separation and protection of their assets.")

    D.h(d, 2, "13.5   Crossings")
    D.p(d, "Wadi crossings take a minimum cover of 1.5 m to the pipe crown "
           "against 1.3 m elsewhere. Road and utility crossings are either open "
           "cut or trenchless, and the choice is a cost and disruption "
           "judgement rather than a rule. Dual carriageways are the exception "
           "that has already been settled for this project: no sewer runs along "
           "one, and crossing is permitted only as a short perpendicular pipe.")

    D.p(d, "Every crossing with another underground utility must be shown on "
           "the hydraulic long section, which the guideline requires to "
           "highlight them explicitly.")
    _source(d, "G203 §8.2.2 p51, §8.2.4 p52, §4.6.3 p33; TOR p55 and p59; "
               "§4.1.2.1 and §4.1.2.2 of the scope for the survey obligations.")


# ============================================ 14  MODELLING
def s14_modelling(d):
    D.h(d, 1, "14   Hydraulic modelling", page_break=True)

    D.h(d, 2, "14.1   Purpose")
    D.p(d, "The model is not a check carried out after the design; it is a "
           "contract deliverable in its own right, submitted in native editable "
           "format and updated after construction.")

    _fig(d, "F12_modelling",
         "Building and proving the model. The early-year run is as important as "
         "the design-year run.")

    D.h(d, 2, "14.2   Software")
    D.p(d, "The wastewater network is modelled in SewerGEMS and the treated "
           "effluent system in WaterGEMS, or other software approved by NWS. "
           "Note that the tender's staffing schedule names a different package, "
           "which is recorded as an unresolved conflict in Section 22.")

    D.h(d, 2, "14.3   What goes in")
    D.bullet(d, "manhole coordinates and cover levels, pipe inverts, diameters, "
                "gradients, materials and roughness", lead="Geometry — ")
    D.bullet(d, "loads applied at manholes, derived from the plot layer rather "
                "than spread uniformly", lead="Loading — ")
    D.bullet(d, "number and type of pumps, duty head and flow, pump curves, "
                "age and condition, efficiency and energy consumption",
             lead="Pumping stations — ")
    D.bullet(d, "diurnal profiles, obtained from NWS or established from data "
                "and validated by them", lead="Patterns — ")

    D.h(d, 2, "14.4   What to run")
    D.p(d, "At minimum the design year at peak flow, the ultimate case, and the "
           "opening years at low flow. The last of these is what feeds the "
           "washing schedule in Section 10 and is the run most often omitted.")

    D.h(d, 2, "14.5   Calibration")
    D.p(d, "Where measured flow exists the model is calibrated against it. The "
           "guideline sets acceptance bands.")
    D.tab_caption(d, "Wastewater model calibration acceptance")
    D.table(d, ["Parameter", "Typical acceptance"],
            [["Peak flow", "± 10 to 15 %"],
             ["Volume", "± 15 %"],
             ["Timing", "correct peak arrival"],
             ["Pump runtime", "± 10 %"]],
            widths=[8.2, 8.3], font=9.5)

    D.p(d, "")
    D.callout(d, "The existing network must be verified before it is modelled.",
              "NWS states in the tender that its own existing-network data is "
              "inaccurate, and the inception report commits to full "
              "verification before the existing system enters the model. "
              "Modelling unverified geometry produces confident numbers from "
              "unreliable inputs, which is worse than no model.")
    _source(d, "G201 Appendix III p138-145, Table 32 p145; G203 §4.2.1 p24 for "
               "the software obligation.")


# ============================================ 15  EXISTING NETWORK
def s15_existing(d):
    D.h(d, 1, "15   Assessing and rehabilitating the existing network",
        page_break=True)

    D.h(d, 2, "15.1   Purpose")
    D.p(d, "There is already sewerage in Ibri, and the concept design has to "
           "say what happens to it: what is kept, what is upgraded, what is "
           "replaced, and how the new network integrates with it. This is a "
           "separately priced deliverable, not a preface to the new design.")

    _fig(d, "F13_existing",
         "Assessing the existing network. Rehabilitation is a priced concept "
         "deliverable in its own right.")

    D.h(d, 2, "15.2   The data problem, stated plainly")
    D.p(d, "NWS's asset GIS carries the existing sewer, force main and treated "
           "effluent networks as geometry. Most of the sewer segments carry no "
           "recorded diameter. The tender itself states that the existing "
           "network layout is based on available information and is inaccurate, "
           "and makes preparing complete as-built records and GIS part of the "
           "consultant's scope.")

    D.callout(d, "That clause is protection, not a burden.",
              "Because NWS has declared its own data inaccurate in the "
              "contract, the survey and as-built exercise is a funded "
              "obligation rather than a favour, and no design conclusion needs "
              "to rest on records the client has already disowned.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "15.3   Method")
    D.numbered(d, "Survey: cover and invert levels, diameters, materials, "
                  "gradients, house connections, riders, lifting stations and "
                  "rising mains.")
    D.numbered(d, "CCTV inspection for condition, carried out early rather than "
                  "at detailed design.")
    D.numbered(d, "Build the as-built and GIS to NWS specification and upload "
                  "it to their system, subject to their acceptance.")
    D.numbered(d, "Model the existing network against future flows to find "
                  "where capacity runs out and when.")
    D.numbered(d, "Classify each asset: adequate and retained, adequate but "
                  "needing rehabilitation, or to be replaced.")
    D.numbered(d, "Design the integration points between old and new, and "
                  "between the old plant and the new one.")

    D.h(d, 2, "15.4   What the assessment must produce")
    D.p(d, "A hydraulic verdict on every existing asset against the design "
           "horizon flows; a rehabilitation and replacement schedule with "
           "quantities; the integration design; and the cost of all of it, "
           "carried into the options appraisal alongside the new works. An "
           "option that reuses more of the existing network is cheaper to build "
           "and may be more expensive to operate, and only a whole-life "
           "comparison settles it.")
    _source(d, "Tender Section 08 p201; scope of work p52 and p60-61; "
               "G203 §11 p197 for the timing of CCTV and survey.")
