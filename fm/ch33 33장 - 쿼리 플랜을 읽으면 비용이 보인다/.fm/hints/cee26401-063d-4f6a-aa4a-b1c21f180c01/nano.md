Clean flat design educational infographic, 16:9 landscape, title at top center: "CROSS_PRODUCT: Build Then Filter".

Layout: two large horizontal lanes stacked vertically, split by a thin dashed divider. Eye flows left to right within each lane, and top lane compares against bottom lane. A small vertical "VS" badge sits on the divider at the left edge.

TOP LANE — red/orange accent, label chip on far left: "A. Comma-separated patterns". Show a small code chip: "MATCH (p:Person), (t:Team)" and below it a greyed chip "WHERE EXISTS { ... }" marked with a small padlock icon and tiny label "Join hidden here". Then a left-to-right operator pipeline of rounded boxes connected by thick arrows:
Box 1: "SCAN Person" with icon of 8000 tiny person dots, label under it "8,000".
Box 2: "SCAN Team" with icon of 80 small squares, label under it "80".
Box 3: big red diamond labeled "CROSS_PRODUCT", with a large multiplication symbol inside.
Then a very wide dense grid block of tiny red squares labeled "640,000 rows" — visually huge, overflowing.
Box 4: "FILTER" drawn as a funnel, with most rows falling away as scattered discarded squares.
End node: green pill "100 results".
Small red tag at lane end: "3.4x slower".

BOTTOM LANE — green/teal accent, label chip on far left: "B / C. Connected pattern". Code chip: "MATCH (p)-[:Member]->(t)". Operator pipeline:
Box 1: "SCAN Team = 팀7" with a single highlighted square, label "1".
Box 2: "EXPAND :Member" drawn as arrows following graph edges from one node to a small fan of nodes, label "100 edges".
Box 3: "FILTER city" small funnel.
End node: green pill "100 results".
Small green tag: "linear growth".

BOTTOM STRIP — full width, light background band, heading "Read the plan: 3 checks", three equal cards in a row with icons:
Card 1 magnifier icon: "CROSS_PRODUCT present?"
Card 2 table icon: "What does SCAN scan?"
Card 3 funnel icon: "FILTER before or after?"

Style: flat vector, no gradients, thick rounded strokes, generous white space, muted paper-white background, restrained palette of red-orange, teal-green, charcoal, light grey. Monospace font for code chips, clean sans-serif for labels. All labels short. No photorealism, no 3D, no shadows.
