# Traps already paid for

Each one cost a failed run, a wrong number or a review comment.

## Loads

- **Infiltration counted twice:** once in the settlement totals and again on the conduits. Keep it in one place. When
  reconciling with a team table that includes infiltration and excludes the estates, add and subtract both explicitly.
  - Ibri's reconciliation: plant inflow = the team's table + 316 (estates) − 1,099 (their infiltration) − the not-carried flow
    + 1,079 (the model's infiltration on 1,498 km).
- **Orphan plots:** a plot with no manhole carries no flow until you send it to the nearest loaded manhole.
- **A check that imports the code it checks** repeats that code's mistakes. Audit from the raw sources.
- **Growth on slivers:** with an equal share per plot, strips and slivers take as much as a house plot. Filter on shape, not
  only on area.
- **A capacity cap after the last design year** quietly flattens the flows. At Ibri, after 2064 the capacity caps the loads,
  so the report stops at 2061.

## SewerGEMS

- **Pattern loads are never peaked** by the Extreme Flow Setup. Use unit loads.
- **LoadBuilder writes 2–4 rows per manhole,** even with Override. Merge them.
- **An inherited DESIGN option** re-sized pipes in every analysis year. Set the alternatives and options LOCAL explicitly.
- **`Add(parent)` breaks the second new year alternative.** Use `Copy(<loaded id>)`.
- **The typed API's diameter is stale** for catalogue pipes. Read the size reference.
- **Text user fields are refused** by the 10.4 API. Use the element Notes.
- **Stored flows are cfs;** the typed API returns display units.
- **Join sewers built through the API** come out at 0.305 m depth and 5–7 m/s. Carry joins as transfers.
- **A conduit's start and stop need not follow the flow.** Check both end nodes.
- **Colebrook-White is about 8 times slower than Manning** (about 44 minutes per design). Run long jobs detached.
- **Paths in job files:** `\f` and `\b` in Python strings, and a heredoc that eats a backslash, corrupted `\\VBOXSVR` paths.
  Write the files with a file tool, and grep them before dropping.

## Design chain

- **A lift's flow is pumped flow.** Transfer its peak; sizing it on the uncut network undersized 99 pipes.
- **Sizing each candidate at its own gradient** is not SewerGEMS's way; it gave 63 pipes one size smaller.
- **A missing catalogue size** (DN1200) was the only difference in the blind test.
- **An "exit" around the depth limit** ("allow it within 1,000 m of an outfall") let 1,362 chambers through to 19.98 m.
  Removing it left 3 chambers and 12.79 m.
- **A guideline "lateral" is tertiary** (at most 45 m). Don't lay a street main at Table 5's 1 %.
- **Tractive force is a "shall" in G203 §4.2.2.1.** Leaving it out of the gradients at the concept stage is a departure, so
  record it for the client.
- **1.5 L/s is not in PAM-GUD-203.** It comes from the simplified-sewerage literature; don't use it as a threshold.

## Report and Word

- **A paragraph finder that doesn't skip the TOC styles** matches the TOC entry first, and the cut destroyed the contents.
- **STYLEREF caption numbers** printed the wrong chapter; write the chapter part as text.
- **The team's cross-references printed "Section 0".** Write every REF as its current number.
- **The clean gate's terms are case-sensitive regexes.** At Ibri they missed "▶ CHECK:" notes, "To be updated" and
  placeholders until they were added.
- **Resizing every table** also resized the cover's picture table and cropped the logo. Skip tables with pictures.
- **Sections copied from the cover** inherit "different first page", so pages after landscape pages lost their header and
  footer.
- **Word "Command failed"** on Save and TOF update in a 190 MB file: pagination off, repaginate, retry.
- **Export with pagination off writes nothing.**
- **`Move-Item -Force` onto a file Word holds** deletes the target.

## Maps and delivery

- **A layer with its categories switched off** exports almost nothing while its legend looks complete. Look at the PNG.
- **QGIS python exits 139** after a successful render. Check the outputs.
- **Chaining PyQGIS calls on a temporary symbol** (`renderer().categories()[i].symbol()`) crashed QGIS. Bind names first.
- **Two WhatsApp senders on one link** fail with 440. Wait; never kill the other.
- **A chat file over 30 MiB** doesn't reach the Remote Control viewer.
- **PowerPoint COM:** SaveAs then Save swapped a deck's maps for icons. Copy, open, edit, save once.
