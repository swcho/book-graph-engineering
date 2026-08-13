A clean flat-design educational infographic, 16:9 landscape, titled "INDEX LOOKUP vs DIRECT ADJACENCY" in bold dark sans-serif at the top center, with the subtitle "why the gap grows with every hop".

Layout: a vertical split into two large side-by-side panels of equal width, separated by a thin vertical divider line with a small circular "VS" badge at its center. A narrow full-width strip runs across the bottom beneath both panels. Reading flow goes left panel to right panel, then down to the bottom strip.

LEFT PANEL, tinted pale warm red/salmon background, header label "INDEX LOOKUP" with a small magnifying-glass icon and the caption "cost depends on total size":
Show three stacked rows labeled at their left edge "HOP 1", "HOP 2", "HOP 3". Each row contains an identical small red-orange B-tree drawn as a triangle of nodes: one root box on top, three boxes on the middle level, six small leaf boxes at the bottom. In every row, a bold arrow starts at the root and zigzags down through the middle level to one leaf, with three small numbered step dots on the path, then exits right toward a tiny neighbor-list icon. Place a repeated red badge next to each row reading "descend again". Below the three rows, a red callout box reads "3 to 5 levels every single lookup". Draw a faint stack of horizontal page-lines behind the leaf level with a small label "leaf page = cache miss".

RIGHT PANEL, tinted pale teal/green background, header label "DIRECT ADJACENCY" with a small arrow-target icon and the caption "cost depends only on degree":
Show three stacked rows labeled "HOP 1", "HOP 2", "HOP 3" aligned exactly with the left panel's rows. In each row a single teal circular node sits at the left with a tiny address tag, and one short bold straight arrow points right into a horizontal row of six contiguous small teal squares forming an array, labeled "neighbor array". No tree, no intermediate steps. Put a green badge on each row reading "one jump". Below the rows, a green callout box reads "offset[u] to offset[u+1]" in monospace, and beneath it "same steps at any data size".

BOTTOM STRIP, light neutral gray background, header "THE HONEST MATH", containing three small equal cards left to right:
Card 1, titled "log is nearly flat": a tiny bar chart with four short bars of heights 3, 3, 4, 5 labeled underneath "1M", "100M", "10B", "1T", and the note "fanout 500".
Card 2, titled "but lookups explode": a tiny upward exponential curve with four dots labeled "31", "931", "28K", "838K" and the axis label "hops 2 to 5".
Card 3, titled "gap per traversal": a single centered formula in monospace, "gap = (L-1) x N", with the small note "constant ratio, exponential total".
At the far bottom right, a small dark footnote reads "finding the start node still needs an index".

Style: clean flat vector illustration, educational textbook infographic, generous white space, thin consistent 2px strokes, rounded rectangles, muted two-tone palette of coral red and teal on off-white, dark charcoal typography, short crisp labels, subtle soft drop shadows on cards, no photorealism, no gradients, no 3D, no clutter, all text in English and correctly spelled. Aspect ratio 16:9.
