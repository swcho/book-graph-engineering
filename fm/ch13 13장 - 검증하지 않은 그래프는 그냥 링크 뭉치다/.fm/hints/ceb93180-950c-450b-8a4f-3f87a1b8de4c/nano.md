A clean flat-design educational infographic titled "Two-Layer Graph Validation / 두 겹 검증" explaining a two-layer data quality pipeline. 16:9 landscape aspect ratio. Left-to-right flow with a large downward-branching decision structure. White background, thin dark gray outlines, muted palette: layer 1 in deep blue, layer 2 in amber/orange, the third gate in teal, blocked items in red, warnings in yellow, info in light gray.

LAYOUT: one narrow entry strip on the far left, then two large stacked horizontal panels in the middle (Layer 1 on top, Layer 2 below), then one narrow panel on the far right. A vertical dashed divider separates the middle panels from the right panel.

FAR LEFT ENTRY STRIP: a small stack-of-documents icon with an arrow pointing right. Label under it: "Incoming graph data". Above the arrow, a small diamond-shaped decision node labeled "True/false decidable?" with two arrows: one pointing up-right to Panel 1, one pointing down-right to Panel 2.

PANEL 1 (top middle, deep blue header bar) titled "Layer 1 — SHACL shapes / 1층". Inside, left half shows a shield icon over a small node-and-edge diagram with a ruler overlay, labeled "Local, deterministic check". Right half shows a vertical three-row traffic-light column, each row a colored chip with an icon:
- red chip, stop-hand icon, label "BLOCK — irreversible"
- yellow chip, warning-triangle icon, label "WARN — query breaks"
- gray chip, notepad icon, label "INFO — cosmetic only"
Below the three chips, a small caption in italic: "Gate rule: irreversible?"

PANEL 2 (bottom middle, amber header bar) titled "Layer 2 — Graph smells / 2층". Inside, left half shows a small graph drawing with five callout markers, each with a tiny icon and short label placed around the graph:
- a hugely oversized hub node, label "Super node"
- a lone disconnected dot, label "Orphan node"
- three nodes in a circular arrow loop, label "Cycle"
- two near-identical nodes side by side with a fuzzy equals sign between them, label "Duplicate suspect"
- one node with two parent arrows, label "Multi-parent"
Right half of Panel 2 shows a magnifying glass over a counting tally, an arrow to a clipboard checklist icon, then an arrow to a person icon. Labels along that chain: "Count globally", "Review list only", "Human decides". A prominent red circle-slash badge stamped near the clipboard with the label "No auto-fix".

RIGHT PANEL (teal header bar) titled "Ch 13.4 — Query regression". Show three small stacked test rows with pass/fail marks: green check "Shape check: pass", green check "Node count: pass", red cross "Competency query: FAIL". Below them a small before/after pair of boxes with an arrow between: left box "before: [P3]", right box "after: [ ]". Caption at the bottom of this panel: "Runs at schema-change gate", and a smaller line: "Golden set 30-50 rows".

CONNECTOR: draw a dashed arrow from the right edge of both middle panels toward the right panel, with a small label on the dashed line reading "Both layers pass, answer still shifts".

BOTTOM STRIP across the full width: a thin summary bar with three short segments separated by dots: "Layer 1 blocks" · "Layer 2 lists" · "Regression guards meaning".

Style: modern educational infographic, flat vector icons, generous white space, consistent 2px stroke weight, rounded rectangles, sans-serif typography, all labels short and crisp, no photorealism, no gradients, no clutter.
