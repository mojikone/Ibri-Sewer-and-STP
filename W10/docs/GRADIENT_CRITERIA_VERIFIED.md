# Gradient, velocity and depth criteria — verified against the source

**Purpose.** W10 phase 3 (`W10/py/p3_optimise.py`) proposes to remove sewage lifting stations by
upsizing pipes so they can be laid at a flatter gradient. This note verifies every criterion that
optimisation rests on, read directly out of the guideline PDFs, before the run is trusted.

**Verified 2026-09-01.** Sources read as text and as rendered images:

| Source | File | Pages |
|---|---|---|
| G203 | `Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf` | 201 pp, Revision 01 |
| G201 | `Data/PAM-GUD-201 - General Design Guidelines v1.0.pdf` | 152 pp, Revision 01 |

PDF page number = printed page number in both documents (checked: PDF page 29 carries the footer
"Page 29 of 201"). All page references below are that number.

Method: PyMuPDF text extraction for the whole document, then the pages carrying Table 11 and the
formulas re-rendered at 200 dpi and read as images, because the two hydraulic equations are
**embedded pictures with no text layer**. Table 10, Table 11 and Table 12 are real text tables and
extracted cleanly; both readings agree.

---

## 1. The headline

> **"Sewers shall not be oversized to facilitate flatter slopes."**
> — G203 p29, section 4.3.1, verbatim, one sentence, no qualification anywhere in the document.

[Certain] The move W10 phase 3 is built on is named and prohibited in the governing guideline, in
almost the same words the code uses to describe itself. `p3_optimise.py` lines 17-21 say
*"a run that is digging itself into the ground can be UPSIZED to be laid flatter ... This is not a
relaxation of anything."* It is a direct breach of G203 section 4.3.1.

---

## 2. Table 11 — cell by cell against the code

**Verbatim caption:** `Table 11 Minimum Sewer Line Gradient`

**Verbatim column headings:** `Sewer Diameter (mm)` | `Minimum Gradient (mm/m)`

**Page:** G203 **p29**, under section 4.3.1 "Pipe Gradients based on Self-Cleansing Velocity".
(The code comment `G203-p29 Tab 11` is correct. The section spans p28-29; the table is on p29.)

**Stated basis, verbatim:** *"The minimum sewer line gradient based on the Colebrook-White equation
and acceptable self-cleansing velocity of 0.75 m/s is given in Table 11."* No design flow, no d/D
and no depth of flow is stated with the table.

| G203 p29 Sewer Diameter (mm) | G203 Minimum Gradient (mm/m) | = m/m | `criteria.TABLE11` | Match |
|---|---|---|---|---|
| 200 | 5.00 | 0.00500 | 0.00500 | exact |
| 250 | 3.75 | 0.00375 | 0.00375 | exact |
| 315 | 2.70 | 0.00270 | 0.00270 | exact |
| 400 | 2.05 | 0.00205 | 0.00205 | exact |
| 500 | 1.55 | 0.00155 | 0.00155 | exact |
| 600 | 1.25 | 0.00125 | 0.00125 | exact |
| 700 | 1.00 | 0.00100 | 0.00100 | exact |
| 800 | 0.85 | 0.00085 | 0.00085 | exact |
| **900 and above** | 0.75 | 0.00075 | `900: 0.00075` + `TABLE11_FLOOR = 0.00075` | exact |

[Certain] **Zero discrepancy in the numbers.** All nine rows match to the last digit, and the
"and above" wording is correctly implemented as a floor, so DN1000 and DN1200 in `DN_SERIES`
correctly take 0.00075.

Note the table has **no DN350 row**, although Table 10 (p27) and Table 12 (p30) both use 350 as a
break. `DN_SERIES` steps 315 to 400 and never lands on 350, so nothing is affected.

### 2.1 What basis the table actually reproduces

[Certain] Reproducing the table from Colebrook-White with ks = 1.5 mm, nu = 1.141e-6 m2/s,
**flowing full**, and taking the tabulated diameter as the **internal bore**:

| DN | table S (mm/m) | V full-bore at that S | S for exactly 0.75 m/s |
|---|---|---|---|
| 200 | 5.00 | 0.748 | 5.02 |
| 250 | 3.75 | 0.751 | 3.74 |
| 315 | 2.70 | 0.741 | 2.77 |
| 400 | 2.05 | 0.754 | 2.03 |
| 500 | 1.55 | 0.756 | 1.52 |
| 600 | 1.25 | 0.763 | 1.21 |
| 700 | 1.00 | 0.753 | 0.99 |
| 800 | 0.85 | 0.755 | 0.84 |
| 900 | 0.75 | 0.764 | 0.72 |

So [Certain] Table 11 is the **full-bore** gradient for 0.75 m/s, with the nominal size treated as
the bore. Largest deviation is DN900 at +3.7 %, all others within 2 %.

**Consequence that matters, and the guideline does not say it out loud:** laying a pipe at its
Table 11 gradient does **not** deliver 0.75 m/s at the design peak flow, because the pipe is not
running full at peak — Table 10 caps it at d/D 0.65 or 0.50. Table 11 compliance and the p26
requirement of *"above 0.75 m/s at peak flow"* are two different tests, and Table 11 is the weaker
one. This is why section 4.2.2.1 provides the tractive-force route as well.

[Certain] The code handles the OD/ID question correctly and deliberately: `hydra.py` keeps
D = DN/1000 when reproducing the guideline table in the +/-5 % gate, and uses the true SDR34 bore via
`criteria.internal_diameter()` for actual design hydraulics. Recorded here only so it is not
"found" again: at DN200's tabulated 5.00 mm/m the **true** PVC-U bore (188.2 mm) gives 0.719 m/s
full-bore, not 0.750. The shortfall is in the guideline's table, not in the code.

---

## 3. Every verified value, with its page and the sentence it came from

| Item | Value | Page | Verbatim source |
|---|---|---|---|
| Minimum self-cleansing velocity | **0.75 m/s at peak flow**, preferred 0.90 m/s | G203 **p26** s.4.2.2.1 | "To provide a self-cleansing regime within gravity sewers, the minimum velocity in the pipe shall be above 0.75 m/s at peak flow, with preferred velocity at 0.90m/s." |
| Two approaches mandated | self-cleansing velocity AND minimum tractive force | G203 **p25-26** s.4.2.2.1 | "To ensure the suspended sediment carrying capacity of the sewer, two approaches shall be used: 1. Self-cleansing velocity ... 2. Minimum Tractive force" |
| Which governs | the steeper | G203 **p27** | "Steeper gradient calculated based on self-cleansing velocity and minimum tractive force methodology shall be adopted as minimum pipe gradient." |
| When tractive force takes over | at the head of the system | G203 **p27** | "At the head of the sewerage systems, the flow velocity based on the minimum self-cleansing may not be attainable. In these circumstances, the minimum pipe gradient for the sewer shall be calculated based on the hydraulic design approach of minimum tractive force." |
| Tractive-force formula | Smin = K x tau^1.23 x Q^-0.461 | G203 **p27** (image, read at 200 dpi) | "Mara, Sleigh, and Taylor (2000) developed the following relationship for minimum slope based on the assumption of d/D = 0.2 and n = 0.013" |
| Tractive constant K | **2.33 x 10-4** (Q in m3/s) or **5.5 x 10-3** (Q in L/s) | G203 **p27** | "Q = Flow (m3/s) and K = 2.33 x 10-4 or Q = Flow (L/s) and K = 5.5 x 10-3" |
| Tractive tension tau | **defined, never valued** | G203 **p26, p27** | "tau = Tractive Tension (Pa)" — the units, and nothing else |
| Maximum velocity | **3 m/s at the design depth of flow** | G203 **p27** s.4.2.2.2 | "To reduce pipe erosion, manhole nuisance, and safety issues, in general, the maximum velocity shall not exceed 3 m/s at the design depth of flow." |
| Maximum gradient | whatever complies with 3.0 m/s | G203 **p29** s.4.3.2 | "The maximum gradient should be determined to comply the maximum velocity of 3.0 m/s" |
| Depth of flow at peak | d/D **0.65** up to 350 mm, **0.50** over 350 mm | G203 **p27** Table 10 | Caption: "Table 10 Recommended Depth of Flow at peak flow"; "d/D being the ratio of flow depth to nominal diameter of pipe" |
| Roughness | **ks = 1.5 mm, all sizes and materials** | G203 **p28** s.4.2.4 | "Gravity sewerage systems shall be designed using a ks value of 1.5 mm for all pipe sizes and materials." |
| Kinematic viscosity | **1.141 x 10-6 m2/s** at 15 C | G203 **p25** Table 9 | "For basic design purposes, the conservative value of 15oC should be used." |
| Uniform slope | required between manholes | G203 **p29** s.4.3.1 | "Uniform slopes must be maintained between successive manholes." |
| Line and level tolerance | **20 mm**, no reverse gradient | G203 **p29** s.4.3.1 | "The lines and level of any pipeline shall not deviate from that described in the contract by more than 20mm and combination of such deviation shall not create a reverse gradient." |
| Minimum cover | **1.3 m to the crown** | G203 **p33** s.4.6.3 | "The minimum depth for sewer pipes shall be 1.3 m to the crown of the pipe. This is required to provide pipe protection from external loads and to avoid interference with other utilities." |
| Cover below 1.3 m | concrete protection, 0.5 m over it | G203 **p33** s.4.6.3 | "If circumstances require installation of a pipe with depth less than 1.3 m above the crown, then concrete protection is required. The minimum cover above the pipe and its protection shall be 0.5 m" |
| Maximum cover | **"approximately 10 - 12m", recommended** | G203 **p33** s.4.6.3 | see section 5 below, quoted in full |
| Property connection cover | 600 mm min, up to 1.50 m | G203 **p19** | "For Property Connection Sewer a minimum cover of 600 mm is required and can go up to 1.50 m" |
| Minimum main sewer size | OD 200 mm | G203 **p22** Table 6 | "Main sewer — OD 200 mm (minimal) to 300 mm" |
| Maximum lateral length | 45 m | G203 **p22** Table 6 | "Lateral Sewer / Maximum Length 45 m / OD 200 mm (minimal)" |
| Backdrop trigger | invert difference exceeding **600 mm** | G203 **p30** | "Connections under these conditions require the use of a backdrop when the difference in invert elevations exceeds 600 mm." |
| Backdrop maximum | **2 m**, then vortex drop shaft | G203 **p30** | "The maximum backdrop height should be of 2 m. Beyond this limit, specific devices like vortex drop shafts should be used." |
| Manhole spacing | 200-315 = 100 m; 350-900 = 120 m; 1000-1400 = 150 m; >1400 = 200 m | G203 **p30** Table 12 | Caption: "Table 12 Maximum Spacing between Manholes" |
| Inlet angle | **not less than 90 degrees** | G203 **p30** | "No inlet pipe at manholes shall have an angle less than 90 to the direction of flow." |

### 3.1 Tractive force — GAP-9 confirmed

[Certain] **PAM-GUD-203 gives no numeric value for tau anywhere.** Searched the full 201-page text
for the tau symbol, `Pa`, `Pascal`, `N/m2`, `tractive`. The symbol appears exactly twice (p26, p27),
both times as the definition line "tau = Tractive Tension (Pa)". Every other hit on "Pa" in the
document is kPa in the vacuum-sewer, odour-control or air-handling chapters and is unrelated.

[Certain] **PAM-GUD-201 gives no numeric tau either, and no tractive-force method at all.** The word
"tractive" does not occur in G201. G201's only wastewater gradient content is a one-line bullet on
p47: *"Velocity and slopes - maintain self-cleaning requirements."* — it defers entirely to G203.
G201's velocity figures on p73 are potable water and refer the reader to PAM-GUD-202.

**GAP-9 stands as recorded.** `TAU_PA = 1.0` is a project assumption with no guideline backing and
must keep being declared as one in every deliverable. Note the formula is derived at
**d/D = 0.2 and n = 0.013** (G203 p27), which is the only flow condition the guideline attaches to
a gradient anywhere in the document.

### 3.2 The flow condition each velocity test is checked at

| Test | Flow condition | Page |
|---|---|---|
| Self-cleansing 0.75 m/s | **peak flow** | G203 p26, verbatim |
| Maximum 3 m/s | **design depth of flow** | G203 p27, verbatim |
| Table 11 gradients | full bore (derived, not stated) | G203 p29 + reproduction in 2.1 |
| Tractive force | the actual Q, at d/D = 0.2 | G203 p27 |
| First-year / low flow | **no design requirement — handed to O&M** | G203 p28 |

[Certain] G203 section 4.2.6 "Low-flow conditions during early periods", p28, in full: *"During
early development phases, the actual flow will usually be below the flow of design inducing risk of
clogging due to low velocity. The operator should proceed to more frequent inspections and
cleansings during this period."* The guideline explicitly does **not** require the network to
self-cleanse in year one; it accepts the risk and puts the burden on operations.

[Certain] G201 p73 section 7.4.4 adds one related instruction: *"The yellow tankers do however need
to be considered by the designer at the initial stage of operations to ensure self-cleaning
velocities at all times."*

---

## 4. Constraints on oversizing — the decisive question

Everything found, and everything looked for and not found.

### 4.1 Found — the explicit prohibition

[Certain] **G203 p29, section 4.3.1, second paragraph, complete and verbatim:**

> "Sewers shall not be oversized to facilitate flatter slopes. Uniform slopes must be maintained
> between successive manholes."

This sentence occurs **once** in the document. It is not qualified, not caveated, carries no
"unless approved by NWS", and no exception is granted anywhere else. It uses "shall not", the
guideline's mandatory-prohibition form.

### 4.2 Found — oversizing named as a cause of septicity

[Certain] G203 **p167**, in the H2S chapter, listing the conditions that generate hydrogen sulphide:

> "a. Oversized lateral sewers and mains resulting in low sewage velocity in sewers causing solids
> deposition and long retention times, promoting anaerobic conditions"
>
> "b. Low sewer gradients resulting in low velocity, promoting anaerobic conditions"

So the guideline names both halves of the proposed move — the bigger pipe **and** the flatter
gradient — as independent causes of septicity. This is the engineering reason behind the p29 rule,
and it is a real one for Ibri: long runs, low flows, high temperature.

### 4.3 Not found — searched for and absent

[Certain] The following do **not** exist in G203 and must not be quoted as if they did:

- **No maximum diameter for a given flow.** Nothing caps how large a pipe may be for its duty.
- **No minimum d/D.** "d/D" occurs six times in the whole document: the Mara derivation assumption
  (0.2, p27), the Table 10 maxima and their surrounding text (p27), the Figure 2 caption (p28), and
  a marine outfall storm figure (91 %, p194). **Table 10 gives maxima only — there is no minimum
  depth-of-flow ratio anywhere.**
- **No "smallest pipe that carries the flow" rule.** The word "smallest" does not appear in a
  sizing context. Table 6 (p22) sets *minimum* sizes — OD 160 rider/PCS, OD 200 lateral and main —
  never a maximum, and never an instruction to minimise.
- **No relief in the Trunk Mains chapter.** Section 5 (p35-36) defines trunk mains (>800 mm, >1000 m
  without connections, upstream of the STP or main pumping station) and covers materials and
  corridor widths only. It sets no gradient, velocity or depth criteria of its own, so section 4
  governs trunk mains too.

[Likely] The absence of a maximum diameter is not permission. The p29 sentence regulates the
**purpose** of the oversizing, not the size reached: a pipe may legitimately be large because the
flow, the d/D cap or the 3 m/s velocity cap requires it. It may not be large *in order to* be laid
flatter. That is exactly, and only, what `p3_optimise.py` does.

---

## 5. Maximum depth — verified verbatim, and it is not what the code implements

[Certain] G203 **p33**, section 4.6.3 "Pipe Laying", complete and verbatim:

> "The recommended maximum cover for sewer pipes is approximately 10 - 12m. Depths with cover
> greater than this shall be investigated with pipe manufacturers to identify any special
> requirements that may be necessary. Where the cost of excavation becomes prohibitive the Engineer
> shall incorporate pumping stations into the design."

The project record is **confirmed on all three points**:

1. **It is a recommendation, not a limit.** "recommended maximum". Going deeper is not prohibited —
   what is required is that it "shall be investigated with pipe manufacturers".
2. **It is a range, not a number.** "approximately 10 - 12m". Choosing 12 is a project decision and
   must be stated as one.
3. **The trigger for pumping is cost, not depth.** "Where the cost of excavation becomes
   prohibitive the Engineer shall incorporate pumping stations into the design." Depth is the
   symptom; the decision the guideline actually describes is economic.

And it is **COVER** — measured to the crown. Depth to invert is greater by the outside diameter.

---

## 6. Discrepancies between the PDF and the code

| # | Item | Guideline | Code | Assessment |
|---|---|---|---|---|
| 1 | `TABLE11`, all 9 rows | Table 11, p29 | identical | **No discrepancy** |
| 2 | `TABLE11_FLOOR` | "900 and above = 0.75" | 0.00075 | **No discrepancy** |
| 3 | `TRACTIVE_K`, exponents | K = 2.33e-4, tau^1.23, Q^-0.461, p27 | identical | **No discrepancy** |
| 4 | `TAU_PA = 1.0` | **no value given in G203 or G201** | 1.0 Pa assumed | **Assumption, correctly flagged GAP-9.** Confirmed, not correctable from the standards |
| 5 | `V_SELF_CLEANSING`, `V_PREFERRED`, `V_MAX`, `DOD_MAX_*`, `KS`, `NU`, `DN_MIN_MAIN`, `LATERAL_MAX_LEN`, `DROP_TRIGGER`, `BACKDROP_MAX`, `mh_max_spacing`, `MIN_COVER_CROWN`, `FALL_TOLERANCE` | pp. 22, 25-30, 33 | all match | **No discrepancy** |
| 6 | `MAX_DEPTH = 12.0` labelled "m cover" | "approximately 10 - 12 m" **cover**, recommended | code computes `depth = ground - INVERT` (`p3_optimise.lay`, `hydraulic.py`, `audit.py`) and enforces it as a **hard** limit | **Discrepancy, conservative.** Applied to invert not crown, so about one OD stricter than the text; and a recommendation range is implemented as a hard trigger. Defensible, but the comment "m cover" mislabels what the code measures — fix the comment |
| 7 | `INLET_MIN_DEG = 85.0` | "No inlet pipe at manholes shall have an angle less than **90** to the direction of flow" (p30) | 85 | **Discrepancy, non-conservative.** The code permits inlets the guideline forbids. Outside this note's scope, but it is a real non-compliance — raise separately |
| 8 | `p3_optimise.py` premise | "Sewers shall not be oversized to facilitate flatter slopes" (p29) | upsizes specifically to flatten | **Direct breach.** See section 7 |

Incidental: `criteria.py` cites the tractive formula as "G203-p27 4.2.2.1" — the formula is on p27,
the section starts on p25. Harmless.

---

## 7. What this means for upsizing to lay flatter

### The direct answer: **NO. It is prohibited, in those words.**

[Certain] PAM-GUD-203 p29, section 4.3.1: *"Sewers shall not be oversized to facilitate flatter
slopes."* The optimisation as currently written in `W10/py/p3_optimise.py` cannot be presented to
NWS as a compliant design. Its own docstring — *"a run that is digging itself into the ground can be
UPSIZED to be laid flatter ... This is not a relaxation of anything"* — is the thing the guideline
forbids, and the claim that it is not a relaxation is wrong: it relaxes section 4.3.1.

The engineering reason is in the same document. G203 p167 lists *"Oversized lateral sewers and mains
resulting in low sewage velocity"* and *"Low sewer gradients resulting in low velocity"* as
independent causes of H2S generation. The move triggers both at once. In Ibri — long runs, low
early-phase flows, high wastewater temperature — that is not a theoretical concern.

### What is still permitted

The prohibition is on the **purpose**, not on the diameter. A pipe may legitimately end up large:

1. **Because the flow requires it** under Table 10's d/D cap (0.65 up to 350 mm, 0.50 above).
   Sizing to the d/D limit rather than to full-bore capacity is the guideline's own rule and gives
   a bigger pipe — and therefore a flatter Table 11 minimum — legitimately.
2. **Because the 3 m/s cap requires it** (p27, p29). On steep ground the pipe must be large enough
   that velocity at the design depth stays under 3 m/s.
3. **Because the design horizon requires it.** Sizing on ultimate saturated flow, not year-1 flow,
   is required by the scope and gives larger pipes than current demand. G203 p28 section 4.2.6
   explicitly accepts the low-velocity consequence of that in early phases and assigns it to O&M.

In all three the diameter is set by a requirement other than gradient, and the flatter Table 11
minimum follows as a **consequence**. That is compliant. Choosing the diameter *from* the gradient
you want is not. The distinction is real and an NWS reviewer will apply it: the audit question is
"what set this diameter?", and if the answer is "the depth we wanted", the design fails.

### Where the genuine headroom is instead

[Likely] The depth rule, not the gradient rule, is where this project has room — and it is the
better target because the guideline's own wording invites the argument:

- **12 m is a project choice inside a range.** The guideline says "approximately 10 - 12m", and
  says it as a **recommendation**. The code currently hard-limits at 12.
- **The code measures to the invert, the guideline to the crown.** Restating the limit as
  12 m *cover* recovers one outside diameter of depth on every reach — 0.2 m on a DN200, 0.9 m on a
  DN900 — with no change to the rule, only to how it is measured. On a long trunk that is real.
- **"Depths with cover greater than this shall be investigated with pipe manufacturers"** is a
  procedure, not a refusal. A manufacturer's confirmation for the pipe class at, say, 14 m converts
  a breach into a documented design decision.
- **The stated trigger is "where the cost of excavation becomes prohibitive"**, which is an
  economic test. Deep trench versus a lifting station over 25 years at 5 % is exactly the NPV
  comparison the project's settled financial method already performs. That comparison is the
  guideline's own criterion, and running it is compliance, not a workaround.

[Guessing] Whether this recovers enough depth to remove a useful number of stations is unknown
until it is run — it depends on how many of the 220 breaches sit between 12 and roughly 14 m rather
than far beyond. That is the next thing to measure.

### Recommended course

1. **Do not run the current phase 3 as the design.** Its premise breaches G203 p29.
2. **Re-aim the optimiser at the depth rule**: measure depth as cover to crown, treat 12 m as the
   point where a manufacturer check and an NPV comparison are triggered rather than a hard stop,
   and let the station/no-station decision fall out of the cost comparison the guideline names.
3. **Keep diameter selection driven by d/D, velocity and horizon only** — never by target gradient.
   Every reach should be able to answer "what set this diameter?" without mentioning depth.
4. **If flatter gradients are genuinely needed on specific long runs**, that is a written
   derogation request to NWS against section 4.3.1 with the septicity case addressed (G203 p167),
   not a silent design choice. NWS pre-approval is the mechanism the guideline uses elsewhere for
   departures (e.g. manhole spacing, p30).
5. **Correct two code items** regardless: the `MAX_DEPTH` comment says "m cover" but the code
   measures to the invert; and `INLET_MIN_DEG = 85.0` is looser than the guideline's 90.

---

## 8. Cross-check against `TUTORIALS/T02`

`TUTORIALS/T02/t02_content.py` was read and compared line by line.

[Certain] **T02 is correct on every point checked, and disagrees with the code, not with this note.**

| T02 statement | Verified? |
|---|---|
| 6.3 quotes "Sewers shall not be oversized to facilitate flatter slopes" at G203 p29 | Correct, page correct |
| 6.3: "upsizing is the obvious trick for keeping a sewer shallow on flat ground. The guideline forbids it. On flat ground the design has no choice but to accept the depth, and pump when the depth runs out" | Correct reading |
| 7.1 Table 11 reproduced, all 9 rows, mm/m and m/m | Correct, all cells |
| 7.2 tractive formula, K values, "The guideline gives no value for tau" | Correct |
| 8.1 minimum cover 1.3 m to crown, 0.5 m over concrete protection, p33 | Correct |
| 8.2 max cover quoted in full, p33, with four qualifications: recommendation not prohibition; a range not a number; COVER not invert; trigger is cost not depth | Correct on all four |
| Max velocity 3.0 m/s cited at both p27 and p29 | Correct — p27 s.4.2.2.2 and p29 s.4.3.2 |
| Table 10 d/D 0.65 / 0.50 at p27 | Correct |

**T02 has no errors.** It already carries the p29 prohibition and already warns that the invert
reading of the 12 m limit is the stricter one. The disagreement is between T02 and
`W10/py/p3_optimise.py`, which was written as if section 6.3 of T02 did not exist. T02 needs no
change; the optimiser does.

One addition worth making to T02 when it is next rebuilt: 7.1 should record that Table 11 is a
**full-bore** derivation, so meeting it does not by itself meet the p26 requirement of 0.75 m/s at
peak flow (see section 2.1 above).
