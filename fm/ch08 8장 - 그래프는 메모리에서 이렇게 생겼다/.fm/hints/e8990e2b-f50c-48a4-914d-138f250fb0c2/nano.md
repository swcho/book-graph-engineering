Create a clean flat-design educational infographic titled "Three Containers for a Graph / 그래프를 담는 세 가지 그릇", 16:9 landscape aspect ratio.

Layout: a small shared source panel across the top, then three equal vertical columns below it, then one comparison bar strip at the bottom. Eye flow goes top (one graph) → down into three parallel columns (three storage forms) → bottom (memory cost verdict).

TOP STRIP — a small node-link diagram of one tiny graph with 4 circular nodes labeled 0, 1, 2, 3 connected by lines (0-1, 0-2, 1-3, 2-3). Caption under it: "Same graph, three containers". A downward arrow splits into three arrows pointing into the three columns.

COLUMN 1 (left, blue accent) — Header: "Adjacency Matrix / 인접 행렬". Visual: a 4x4 grid of small squares, filled squares dark blue for 1s and pale for 0s, with row and column indices 0-3. Below, three short bullet labels: "Size = N x N", "O(1) edge lookup", "Dies past a few thousand".

COLUMN 2 (middle, amber accent) — Header: "Adjacency List / 인접 리스트". Visual: four rounded key boxes labeled 0, 1, 2, 3 stacked vertically on the left, each with an arrow pointing right to a small scattered chain of neighbor bubbles placed at irregular horizontal offsets, with faint dashed pointer arrows to suggest scattered memory. Below, three short bullet labels: "Size = edge count", "Easy to edit", "Object overhead, cache misses".

COLUMN 3 (right, green accent) — Header: "CSR / 압축 희소 행". Visual: two horizontal contiguous arrays drawn as tight adjoining cells. Top array labeled "offset" with cells 0, 2, 4, 6, 8. Bottom array labeled "nbr" with cells 1, 2, 0, 3, 0, 3, 1, 2, and colored brackets under the nbr array grouping each pair labeled "node 0", "node 1", "node 2", "node 3". Draw thin arrows from offset cells down to the group starts. Below, three short bullet labels: "Two integer arrays", "Neighbors are contiguous", "Immutable once built".

BOTTOM STRIP — a horizontal bar chart comparing memory for 20,000 nodes and 120,000 edges. Three bars, same colors as the columns: longest blue bar labeled "Matrix 48x", medium amber bar labeled "List 7.8x", tiny green bar labeled "CSR 1.0x". To the right of the bars, a bold callout box: "4.1 GB vs 380 MB — same graph".

Style: clean flat vector infographic, generous white background, soft rounded panels with thin borders, muted blue / amber / green accent palette, crisp sans-serif type, strong visual contrast between the dense grid (column 1), the scattered pointers (column 2), and the tight contiguous arrays (column 3). All labels short, 3 to 5 words maximum, legible, no paragraphs of text, no watermark.
