# The design report

**For how to write and build a client report, use the report-writing skill.** It covers:
- the clean-room gate;
- native equations and footnotes;
- captions and figures;
- page sizes;
- writing that reads as human.

This file adds what a sewer design report needed on top of that, when the build edits a team's own Word file instead of
building from a template. Reference scripts are in `scripts/report_final/`. The Ibri build scripts (`build_report.py`,
`r10_edits.py`, `r11_edits.py`) are in the toolkit zip, as examples.

## 1. What the report must carry from the design

Every number comes from the results files the design wrote. None are typed:
- the loads, the not-carried flow, the plant inflows per design year;
- the network per scenario and design year: length by size, stations and lifts, depth, self-cleansing at the opening year;
- the study behind each decision (gradient limit, design years) as a table;
- costs per design year and the whole-life comparison;
- the risks: the not-carried flow, the depth exceptions, the decisions still open with the client.

## 2. Structure that worked (Ibri R12, on the team's R8-MH)

- **Executive summary in ten parts:**
  - A Purpose · B Project area · C Data and surveys · D Design basis · E Population and flows;
  - F Decisions requested from the client · G Scenarios and appraisal · H Recommendation;
  - I Treatment plant, treated effluent and sludge · J Matters requiring attention in every scenario.
- **Network chapter:**
  - methodology: basis, network configuration and modelling, gradient limit, design year and self-cleansing, pumping and
    lift stations, treatment locations, TE demands;
  - then one section per scenario: an introduction with the zones map, then "SCn Network Design by Flow of yyyy" for each
    design year, each with a flow schematic, a network map and a self-cleansing map, then the scenario's options comparison;
  - then the comparison of scenarios.
- **Costs** by design year in the financial chapter, and the whole-life cost of every design in the appraisal chapter.
- **Appendices:** compliance matrix, decisions and adopted values, population and flow calculations, network quantities with
  station flows and depth, design criteria, cost basis, meeting records, drawing register.

## 3. Editing a team's Word file (python-docx)

- **Copy the team's document and edit it in place.** Never retype their chapters.
  - Write one module per revision, each with an `apply()` run after the main build.
  - A `REV` constant picks the output folder; an issued revision is never overwritten.
- **Insert content with a writer that inserts before a given element.** It needs:
  - paragraphs, headings, tables, captions and figures;
  - A3 landscape pages for maps, sized by the image's aspect so the caption fits;
  - section breaks.
- **Find a paragraph by its text and style, skipping the TOC and table-of-figures styles.** A TOC entry once matched a
  heading and the cut destroyed the table of contents.
- **`set_text` / `sub`:** rewrite a paragraph keeping the first run's format, the footnote references and the bookmarks.
  `sub` asserts that the old text exists, so a silent no-op cannot happen.
- **Captions:** native SEQ fields, with the chapter part written as text. STYLEREF gave wrong chapter numbers.
- **Cross-references:**
  - write REF fields as their current numbers, and unlink the dead ones to text;
  - check every hand-typed "Section n.n" against the TOC twice: once that it exists, and once that it is on the right topic.
- **Layout pass:**
  - **Tables:** centred and sized by content: never below the longest word, never past the page. Skip cells with rotated
    text and tables that hold a picture (a resized cover table cropped the logo).
  - **Chapters:** start with page-break-before on the heading.
  - **Blank pages:** remove empty paragraphs before a section or page break.
  - **Different first page:** only the cover keeps it. Copied sections inherited the cover's blank header, so pages after
    landscape pages lost their header and footer.
  - **Highlighting:** strip the team's yellow highlighting before issue.

## 4. Finishing in Word (COM, `word_finish.py`)

- **Order:**
  1. open hidden (`DispatchEx`);
  2. switch background pagination off and `Repaginate` once;
  3. update SEQ/STYLEREF, then the TOC and TOF, twice;
  4. unlink REF fields with no bookmark;
  5. `SaveAs2` to `_finished.docx`;
  6. switch pagination back on;
  7. export the PDF to a temporary name;
  8. swap both into place after Word quits.
- **Retries:** retry every Word call 4 times, 15 s apart, on "Command failed". On a 160–190 MB report, Save and the TOF update
  fail while Word is still laying out pages.
- **Export with pagination off writes nothing,** without any error.
- **Killed runs:** a killed run leaves a hidden automation Word and a `~$` lock file, and the next run hangs. Kill only
  automation instances (check the command line) and delete the lock.
- **Resiliency dialog:** after a failed run, Word may show a "serious error, open it anyway?" dialog on another screen. Find
  it in the process windows and answer Yes.
- **Locked files:** `Move-Item -Force` onto a file Word still holds deletes the target.
- **Field updates on export:** Word refreshes cross-references when it exports a PDF. Updating the team's fields exposed dead
  references as "Error!". Unlink them first, and export with UpdateFieldsAtPrint off.

## 5. QA before issue (`qa_report.py`, `check_clean.py`)

- **Clean-room gate:** `check_clean.py <pdf> --terms forbidden_terms.txt --allow allowed_terms.txt`.
  - The term lists are case-sensitive regexes; use `\b` where a short code could match inside another.
  - Pass the files with their flags: positional arguments were ignored.
- **`qa_report.py <pdf> --docx <docx> [--topics] [--sheets DIR]`** checks:
  - near-empty pages;
  - captions with no figure above them;
  - header and footer on every page but the cover;
  - unbroken caption sequences;
  - every cited table, figure and section exists;
  - stale wording.
  It exits 1 on any failure.
- **Look at the render:** contact sheets of every page, close renders of each changed page, every map and chart opened.
- **One term everywhere:** use the client's agreed wording (Ibri: "property", never "dwelling"), enforced through the gate.
