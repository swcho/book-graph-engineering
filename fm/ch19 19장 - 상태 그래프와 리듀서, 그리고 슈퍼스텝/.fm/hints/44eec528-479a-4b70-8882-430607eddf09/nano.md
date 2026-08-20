Create a clean, flat-design educational infographic in 16:9 landscape aspect ratio.

Title at the top center, large bold sans-serif: "Nodes Return Deltas, Not State"
Small subtitle under the title: "부분 갱신 + 리듀서"

Layout: three horizontal panels of equal width, side by side, separated by thin vertical divider lines. A left-to-right reading flow with arrows carrying the eye across all three panels.

PANEL 1 (left) — header label "1. Node Returns a Delta"
Show a large rounded rectangle labeled "STATE" containing four small stacked field chips labeled "logs", "count", "step", "tags". To its right, a rounded box labeled "NODE" with an arrow going in from STATE and an arrow going out. The outgoing arrow carries a small tag containing only two chips: "logs" and "count", labeled below in small text "only changed fields". Grey out the untouched chips "step" and "tags" inside STATE to show they are not returned. Add a small red crossed-out ghost box labeled "NOT whole state".

PANEL 2 (center) — header label "2. Same Superstep, Parallel"
Show three rounded node boxes stacked vertically, labeled "재무 Finance", "법무 Legal", "영업 Sales". A single arrow fans out from a small dot labeled "START" into all three. Each node emits an arrow to the right carrying a small chip labeled "+1 log". Beneath the three nodes add a short caption "same copy, blind to each other". Draw a bold vertical dashed line at the right edge of this panel labeled vertically "SUPERSTEP BOUNDARY".

PANEL 3 (right) — header label "3. Reducer Merges"
Show the three incoming arrows from panel 2 converging into a single funnel-shaped element labeled "REDUCER" with a small code chip under it reading "Annotated[list, add]". Below the funnel, one merged result box labeled "logs: 3 items / count: 3" with a green checkmark, captioned "merged".
Directly under it, a contrasting smaller box outlined in red with a warning triangle, labeled "NO REDUCER" and two short outcomes listed: "error (lucky)" and "lost update (unlucky)".

Bottom strip spanning the full width: a thin horizontal band with one short rule in bold, centered: "Reducer must be commutative: f(a,b) = f(b,a)" and to its right a tiny chip row "use time / source / confidence".

Style: modern educational infographic, clean flat vector design, generous white background, muted palette of navy blue, teal, warm amber accent, and a single red for the warning element. Rounded corners, consistent 2px line weight arrows, clear sans-serif typography, no photographic elements, no clutter. All labels short and crisply rendered.
