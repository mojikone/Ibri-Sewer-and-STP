# Design flowcharts — editable FigJam boards

Both are drawn from the code as it actually runs, not from intent. Numbers in them come
from the 20 August 2026 run of the test area.

| Diagram | What it answers | FigJam (editable) | In repo |
|---|---|---|---|
| Gravity network and lift decisions | Where does a pipe connect, and what forces a pumping station? | https://www.figma.com/board/PsAsa5zrG6ansKon4HI71I | `fig_gravity_and_lifts.svg` / `.png` |
| What makes the design efficient | What drives fewer lifts, shallower manholes and smaller pipes — and which of those is still a real lever | https://www.figma.com/board/4hhOZCLaU64eWF4TQLXqg2 | `fig_efficiency.svg` / `.png` |

The SVG is the master (vector, scales into Word or a drawing without going fuzzy). The PNG
is a convenience copy.

## About the titles on each group

FigJam draws each group as a *section*, and a section carries its name on the small tab at
its top-left corner. That name is real and shows on the board and in Figma's layers panel,
but **an exported PNG or SVG never draws it** — Figma treats a section name as interface
furniture, not as something on the canvas. Nothing in the diagram can change that.

So each group carries its title TWICE, on purpose:

1. as the section name on the tab, which is what you see and navigate by inside Figma;
2. as a dark title box, the first item inside the group, which survives export into a
   picture, a Word report or a drawing.

If a title ever looks missing from a tab, check whether the group label was left blank in
the diagram source — that is the only way it can actually be empty.

## Superseded boards from the same session
Earlier attempts, left only so a link in an old message still resolves. Do not use them:
the labels truncate mid-word, or the layout runs off the page.

- https://www.figma.com/board/ncT8fJD9jCGcrcrH1zSZV1 (v1, 6.4:1 strip)
- https://www.figma.com/board/AaBYitsrADyTVsJOAi9Orl (v2, truncated diamonds)
- https://www.figma.com/board/kgSV6zGsNEJeOJQfWpdgGa (v3, 0.14:1 ribbon)
- https://www.figma.com/board/FGoYX0JOFlHxaBPc4YTMgz (v4, 5.4:1 strip)
- https://www.figma.com/board/FHwIE8AZ11j2L3e83zWNos (v5, one word broke mid-word)
- https://www.figma.com/board/JBkNnTWGuZDqeADmcDj26B (v6, title only on the tab, so exports showed none)
- https://www.figma.com/board/99qJzyEQvXAOKCdsfVgkLC (v7, title box added but the tab was blanked)
- https://www.figma.com/board/S465osqFVZW425alonbVNp (efficiency v1, title only on the tab)
- https://www.figma.com/board/Trqc2hqL0gbyCyQHRe1Ao9 (efficiency v2, title box added but the tab was blanked)
- https://www.figma.com/board/xPp7V2f5JeTtAq0Y03adFR (cost v1, edge label printed through a node)
- https://www.figma.com/board/9sEco28kIHDuzKSYpl8D40 (cost v2, before you clarified that cost means engineering efficiency, not money)
