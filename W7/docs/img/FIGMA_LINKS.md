# W7 design flowcharts — editable FigJam boards

Both are drawn from the code as it actually runs, with numbers from the 20 August 2026 run.

| Diagram | What it answers | FigJam (editable) | In repo |
|---|---|---|---|
| How the sewer design decides | Where a pipe may go, where a subnetwork joins the main pipe, and what forces a pumping station | https://www.figma.com/board/l3b3gptqTtRvCJBEstozD8 | `fig_design_decisions.svg` / `.png` |
| Measured against the built network | How W7 compares with the 188.6 km NAMA already built, and the one assumption that was tested and rejected | https://www.figma.com/board/zF2PFdS3hUkiPokfY6Fh2N | `fig_vs_asbuilt.svg` / `.png` |

The SVG is the master (vector, stays sharp in Word). The PNG is a convenience copy.

## The group titles

FigJam keeps a group's name on the small tab at its top-left corner. Figma treats that name
as interface furniture, so **no export ever draws it** — in a picture the tab looks empty.
`add_group_titles.py` therefore paints the name onto the frame as a title bar. Re-run it
after regenerating a board:

    python add_group_titles.py fig_design_decisions.svg fig_vs_asbuilt.svg

then re-render the PNG from the SVG.

## Superseded — W6 boards, do not use
They show a trunk the design guessed for itself, a bend-chamber stage that has since been
deleted, and a 75-degree inlet rule that is now 85.

- https://www.figma.com/board/fjU9QS6c6h3TCxTlkxWsaO (W6 decisions)
- https://www.figma.com/board/YI9ZwOAxEj2phCXkC1w6rj (W6 efficiency)
