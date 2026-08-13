Create a clean flat-design educational infographic, 16:9 landscape, titled "Why CSR Is Fast: Memory, Not Algorithm (알고리즘이 아니라 메모리)".

Layout: a slim header band with the title. Below it, a large two-column comparison area taking most of the canvas, split by a thin vertical divider with a small "VS" badge in the middle. Beneath the two columns, one full-width footer strip. Reading flow is left column top-to-bottom, then right column, then footer.

LEFT COLUMN, header chip in green: "CSR — contiguous neighbors". Stack three rows vertically.
Row 1: two small labeled arrays. Top array is a thin strip of 5 cells labeled "offset" with values 0, 3, 5, 9, 14, and a downward arrow from cell "3" pointing into the second array. Bottom array is a long horizontal strip of 16 small square cells labeled "nbr (neighbors)", filled with numbers 7, 8, 9, 11, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25, 27, 28. Draw one bold green rounded rectangle enclosing the FIRST 16 cells, labeled above it "1 cache line = 64 bytes = 16 ints (캐시 한 줄)".
Row 2: a single wide green arrow pointing right, labeled "sequential read — prefetcher works".
Row 3: a green score chip reading "1 memory trip" next to a small green check mark.

RIGHT COLUMN, header chip in soft red: "dict of list — pointer chasing". Stack three rows vertically.
Row 1: a scattered memory field — a light grid of many empty cells with only 6 filled cells placed far apart at irregular positions, each a small red square holding a number (7, 41, 88, 12, 63, 20). Draw thin red curved arrows hopping from one filled cell to the next in a zigzag, and label the chain "dict → list → PyObject".
Row 2: draw 6 separate small red rounded rectangles, each enclosing just one filled cell, with the shared label "6 cache lines fetched, 1 useful int each (한 줄에 하나만 쓸모)".
Row 3: a red score chip reading "12+ memory trips" next to a small red cross mark.

Under the two columns, a narrow horizontal latency bar chart spanning both columns, four bars of increasing length, labeled "L1 ~1ns", "L2 ~4ns", "L3 ~15ns", "DRAM ~100ns". Color the first three teal and the last one red, with a small caption "1 cache miss = 100 instructions".

FOOTER STRIP, centered, two short lines:
Line 1 bold: "Same algorithm. Same O(V+E). Different memory."
Line 2 smaller: "Contiguity is not free — reorder node IDs (그래프 재배치)".

Style: clean flat vector infographic, educational textbook feel, off-white background, generous white space, muted palette of teal, navy, green and soft red accents, thin 2px strokes, simple sans-serif typography, rounded panel cards with light borders, no gradients, no photographic texture, no clutter. All labels short and legible. Aspect ratio 16:9.
