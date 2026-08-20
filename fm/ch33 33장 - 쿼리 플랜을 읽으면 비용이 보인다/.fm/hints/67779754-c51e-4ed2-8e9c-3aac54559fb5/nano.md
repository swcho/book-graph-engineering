A clean flat-design educational infographic, 16:9 landscape, titled "Index Works Only If It Matches the Lookup".

Layout: a wide title bar at top, then three equal vertical columns side by side (left to right reading flow), then one full-width strip at the bottom. Thin dividers between columns. Light neutral background, three distinct accent colors, one per column.

COLUMN 1 — header "Hash Index" (blue accent).
Diagram: a key box labeled "id = 42" with an arrow into a rounded box labeled "hash()", then an arrow into a grid of small buckets where one bucket glows and points to a row. Small caption chip: "O(1) direct jump".
Operator list below with marks:
- "= equality" green check
- "IN list" green check
- "> < range" red cross
- "STARTS WITH" red cross
- "CONTAINS" red cross
Bottom note chip: "Hash destroys order".

COLUMN 2 — header "Sorted B-Tree Index" (green accent).
Diagram: a small three-level tree, its leaf row drawn as sorted keys A B C D E F linked left to right by arrows, with a highlighted contiguous span bracket under the leaves labeled "range = one span".
Operator list with marks:
- "= equality" green check
- "> < range" green check
- "ORDER BY, MIN MAX" green check
- "STARTS WITH prefix" green check
- "CONTAINS" red cross
Bottom note chip: "Prefix becomes a range".

COLUMN 3 — header "Full-Text Index" (orange accent).
Diagram: a text line broken into token chips, arrows flipping into an inverted list "word to doc ids", plus a small row of trigram chips "gra rap ape".
Operator list with marks:
- "CONTAINS substring" green check
- "word search" green check
- "fuzzy similarity" green check
- "= equality" gray dash
Bottom note chip: "Cut text, match exactly".

BOTTOM STRIP — a single wide banner with a graph motif: two node circles joined by an arrow labeled "relationship", one node marked with a small index icon and a star labeled "start point". Banner text, short: "Graph: index the start, traverse for free".

Style: clean flat vector, educational infographic, generous white space, rounded rectangles, thin consistent line weights, bold short sans-serif labels, subtle drop shadows, muted pastel fills with saturated accents, green checks and red crosses as simple flat icons. All labels 3 to 5 words maximum. No paragraphs, no long sentences. Aspect ratio 16:9.
