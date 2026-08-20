# Design flowcharts — editable FigJam boards

Both are drawn from the code as it actually runs, not from intent. Numbers in them come
from the 20 August 2026 run of the test area.

| Diagram | What it answers | FigJam (editable) | In repo |
|---|---|---|---|
| Gravity network and lift decisions | Where does a pipe connect, and what forces a pumping station? | https://www.figma.com/board/fjU9QS6c6h3TCxTlkxWsaO | `fig_gravity_and_lifts.svg` / `.png` |
| What makes the design efficient | What drives fewer lifts, shallower manholes and smaller pipes — and which of those is still a real lever | https://www.figma.com/board/YI9ZwOAxEj2phCXkC1w6rj | `fig_efficiency.svg` / `.png` |

The SVG is the master (vector, scales into Word or a drawing without going fuzzy). The PNG
is a convenience copy.

## The group titles, and why there is a script

FigJam draws each group as a *section*, and a section carries its name on the small tab at
its top-left corner. Inside Figma you can see that name. But Figma treats a section name as
interface furniture rather than as part of the canvas, so **no export draws it** — not the
PNG, not the SVG, and not the full-resolution render either. Checked on 20 August 2026
against a real render, not just a thumbnail: the tab comes out as an empty box.

Putting the title in a node inside the group is not the same thing — it sits in the flow and
reads as another step.

So `add_group_titles.py` takes the name Figma already stores on each group and paints it as
a title bar across the top of that group's frame. Rerun it whenever a board is regenerated:

    python add_group_titles.py fig_gravity_and_lifts.svg fig_efficiency.svg

Then re-render the PNG from the SVG. The names come from the `subgraph` labels in the
diagram source, so the title on the frame and the name on the Figma tab can never disagree.

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
- https://www.figma.com/board/PsAsa5zrG6ansKon4HI71I (v8, title duplicated as a node in the flow)
- https://www.figma.com/board/4hhOZCLaU64eWF4TQLXqg2 (efficiency v3, same)
- https://www.figma.com/board/xPp7V2f5JeTtAq0Y03adFR (cost v1, edge label printed through a node)
- https://www.figma.com/board/9sEco28kIHDuzKSYpl8D40 (cost v2, before you clarified that cost means engineering efficiency, not money)
