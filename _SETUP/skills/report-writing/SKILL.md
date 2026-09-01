---
name: report-writing
description: "Build client-facing engineering reports as Word documents from Python, with native OMML equations, real footnotes, proper figure and table captions, QGIS map figures, process flowcharts and data charts. Use for any deliverable report, design report, concept report, inception report, technical note or study that a client will read. Triggers on: write the report, build the report, concept report, design report, deliverable, report revision, add a section to the report."
metadata:
  version: "2.0.0"
  project: "2621 Ibri Sewer, TE Networks and STP"
---

# Report writing

A client-facing report is a deliverable, not a transcript of the work. This
skill covers how to build one so it is accurate, readable and defensible, and
so that a reader cannot tell it was written with a machine's help.

## Non-negotiables

1. **Every number traces to a source.** A figure appears in the report only if
   it came from a named guideline page, a measurement you can reproduce, or a
   tagged assumption. Never carry a number from memory, and never round in one
   place and not another — derive it once, in a `data_facts.py` style module,
   and read it everywhere else.
2. **Never write to the client about the work.** No internal reasoning, no
   apologies for what is missing, no "we should consider". State what has been
   established, what is outstanding, and what confirmation is requested.
3. **Nothing invented.** If the data does not support a statement, the
   statement does not go in. Say the item is being surveyed or requested.
4. **Check the render, not the exit code.** A build that succeeds can still
   produce a clipped table, an invisible layer or an overlapping label. Open
   the PDF pages as images and look at them.

## Structure of the build

Keep the document in Python so it rebuilds from source on every run:

```
report/
  build.py          orchestration; REV constant drives the output folder
  doc.py            furniture: headings, parts, tables, captions, footers
  notes.py          real Word footnotes, injected into the .docx package
  omml.py           native Word equations
  flow.py           process flowcharts
  charts.py         data charts
  qgis_maps.py      map figures cloned from a saved QGIS layout
  data_facts.py     every measured figure, with how it was measured
  rpt_*.py          the sections themselves
  R0/ R1/ ...       issued revisions, never overwritten
  img/              figures, rebuilt by flow.py, charts.py and qgis_maps.py
```

Version by folder. A revision that has been issued is frozen; the next
revision writes to its own folder and the build's `REV` constant selects it.

## Equations

Use native OMML so the client can edit the equation in Word. An image of an
equation is not acceptable in a deliverable.

The one trap: content appended to `doc.element.body` lands *after* the
trailing `<w:sectPr>` and Word collects it at the end of the document. Insert
before it:

```python
sect = body.find(qn("w:sectPr"))
sect.addprevious(element) if sect is not None else body.append(element)
```

Number every equation, and follow it with a parameter table giving each
symbol, its meaning and its unit. A reader must be able to use the equation
without leaving the page.

## Footnotes

python-docx has no footnote support; write `word/footnotes.xml`, the content
type override and the relationship into the package on save. Restart numbering
on each page through `<w:footnotePr><w:numRestart w:val="eachPage"/>` in the
section properties, so a footnote marker is never a three-digit number.

Footnotes carry the reference, the page, the caveat and the derivation — the
things a reviewer needs and a reader does not. If it belongs in the argument,
it belongs in the body text.

## Flowcharts

Draw process flowcharts on a stated grid, sized to the text column. Figma can
produce them, and for a diagram that is genuinely a diagram — a system sketch,
an org chart, a spatial arrangement — it is the right tool: use the Figma MCP,
lay the nodes out explicitly, and export PNG into `img/`.

For a **page-shaped process chart**, auto-layout will not give you a usable
aspect ratio. Left-to-right runs about 6:1, top-down about 0.3:1, and neither
fits a portrait text column. Place nodes on an explicit grid instead, at the
column width, and have the renderer report the aspect ratio and flag anything
that will not fit.

Two rasteriser traps:

- **Arrowheads.** SVG `marker-end` is ignored by most rasterisers. Draw the
  arrowhead as an explicit polygon.
- **Fonts.** A comma-separated stack (`"Helvetica, Arial, sans-serif"`) matches
  nothing as a single family name and silently falls back to a serif. Use one
  family name, and set it on every `<text>` element — `font-family` on the root
  `<svg>` is not inherited by the rasteriser.

## Data visualisation

A report that only tabulates is harder to read than it needs to be. Chart
anything where the shape of the data is the point: a distribution, a
concentration, a comparison between two populations, a check that two
independent measures agree, the state of a register.

Rules that hold in every chart:

- **Draw from the same source as the text.** Put the data at the top of the
  chart function with the source named. If the text and the chart can disagree,
  they eventually will.
- **Label so the small values survive.** In a distribution where one category
  holds most of the total, the small bars vanish. Put the number at the end of
  every bar; the invisible bar plus a readable number tells the truth.
- **Never let a label collide.** Put value labels in fixed columns clear of the
  longest bar rather than at each bar's end, so a short bar cannot crowd its
  own text. Then look at the exported PNG.
- **Say what the colour means in the legend, not in the caption.** A category
  the reader has to decode twice is a category they will misread.
- **The chart states, the caption interprets.** Keep explanatory sentences out
  of the plot area; they collide with axis labels and read as clutter.
- **Show status honestly.** If a value is flagged, under review, or proposed
  rather than built, colour it distinctly and say so in the legend. A chart
  that averages away a caveat is worse than no chart.

## Maps as figures

Clone a saved layout per figure rather than building one from scratch, so
every map carries the same furniture. Then:

- **Filter the legend to the map's own layers.** Clear the legend model root
  and add only the layers the map draws; otherwise the legend lists the whole
  project.
- **Suppress the layer title on a categorised layer,** whose class labels
  already name it (`node.setCustomProperty("legend/title-style", "hidden")`).
- **Do not let the map number itself.** The caption in the document carries
  "Figure N"; a number baked into the layout drifts the moment a figure is
  added ahead of it.
- **Fill the data box from the same facts module** the text uses. A layout
  template carries the previous project's numbers until you overwrite them.
- **Check the exported image, always.** A layer whose `renderState()` is False
  exports successfully and draws nothing.

Maps are figures: they take figure numbers in the same sequence as charts and
diagrams, not a separate one.

## Writing so it reads as human

The failure mode is not bad grammar; it is uniformity. Watch for:

- **The rule of three.** Three adjectives, three clauses, three examples,
  every time. Vary it — two, or five, or one.
- **Hedging as a reflex.** "It should be noted that", "it is important to
  consider", "a range of factors". Delete and state the thing.
- **The summarising last sentence.** A paragraph that ends by restating its
  own first sentence. Cut it; the paragraph already made the point.
- **Symmetry that the content does not have.** Sections of equal length
  regardless of how much there is to say. Let a short section be short.
- **Elegant variation.** Calling the same thing a network, a system, a scheme
  and an asset in one paragraph. Pick the term and keep it.
- **Empty transitions.** "Furthermore", "Moreover", "In addition" carrying no
  logical work. If the next sentence follows, it does not need announcing.
- **Grand openers.** "In the modern era of water infrastructure". Start with
  the substance.
- **Em-dashes and colons as a tic.** One per paragraph at most.

Prefer the plain word: use, not utilise; about, not approximately, unless the
tolerance matters; build, not construct, unless it is a contract term. Write
in complete sentences and let sentence length vary. Say what a thing is before
saying what follows from it.

A useful check: read a page aloud. Where you would not say it that way to a
colleague, rewrite it.

## Sequence for a revision

1. Correct `data_facts.py` first. Every downstream number follows from it.
2. Rebuild the figures: `flow.py`, `charts.py`, then the maps in QGIS.
3. Rebuild the document, then render the changed pages to PNG and look.
4. Update the live documents — the project state and the README — in the same
   change, so the next reader starts from current truth.
5. One logical change per commit.
