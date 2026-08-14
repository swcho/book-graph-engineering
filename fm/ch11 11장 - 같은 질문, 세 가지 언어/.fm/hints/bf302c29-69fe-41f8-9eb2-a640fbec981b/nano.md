Create a clean flat-design educational infographic, 16:9 landscape aspect ratio, titled "Reading a Query Plan: 3 Checks".

Overall layout: a header band at the top, then three numbered vertical panels side by side across the middle (the main content), then a narrow full-width footer strip at the bottom. Reading flow goes left to right across the three panels, with a thin arrow connecting panel 1 to panel 2 to panel 3.

Header band: the title on the left, and on the right a small subtitle label "실행 계획 읽기 (Query Plan)".

Panel 1, labeled with a large circled number "1" and heading "WHERE TO START" with smaller Korean text under it "스캔 위치":
Show a small vertical plan tree read bottom-to-top: three stacked rounded boxes connected by a vertical line, with an upward arrow on the side labeled "read bottom-up". The bottom box is highlighted in green and labeled "SCAN City". Beside the tree, a side-by-side size comparison: one tiny green circle labeled "City: 12 rows" next to one large red circle labeled "Person: 20,000 rows", with a short caption "Start from the small side".

Panel 2, labeled with a large circled number "2" and heading "INDEX OR FULL SCAN" with smaller Korean text under it "색인 vs 전체":
Split this panel into a good half and a bad half, divided by a vertical dashed line. Good half tinted green with a check mark icon, a magnifying glass pointing at a single highlighted row in a small table, and the label "PRIMARY_KEY_SCAN". Bad half tinted red with an X mark icon, a small table with every row shaded and a funnel icon below it, and the labels "SCAN + FILTER" and "reads all, keeps few".

Panel 3, labeled with a large circled number "3" and heading "ESTIMATED ROWS" with smaller Korean text under it "중간 결과 행 수":
Show a simple funnel-versus-balloon contrast as two small bar sequences. The upper sequence, tinted green, has bars that shrink left to right, labeled "1 → 1,667 → 1" with the caption "narrows down". The lower sequence, tinted red, has bars that grow large in the middle then shrink, labeled "20,000 → huge → 1" with the caption "join explosion". Add a small side note box with two short lines: "EXPLAIN LOGICAL = estimate" and "PROFILE = actual".

Footer strip: a horizontal causal chain of four small pill-shaped boxes joined by arrows, reading "No index" then "Wrong start table" then "Row explosion" then "Slow query". Keep these pills in a muted red-orange tone.

Style: clean flat vector infographic, educational poster look, generous white space, soft off-white background, thin consistent line weights, rounded corners, restrained palette of teal-green for good and coral-red for bad plus dark navy for text and neutral gray for structure. Use a crisp modern sans-serif. Keep all text large and legible, all labels short. Monospace font only for the operator names like SCAN City, PRIMARY_KEY_SCAN, SCAN + FILTER, EXPLAIN LOGICAL, PROFILE. No photographic elements, no gradients, no drop shadows, no extra text beyond the labels specified.
