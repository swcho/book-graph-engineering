A clean flat-design educational infographic, 16:9 landscape, comparing two graph query languages side by side. Bold header bar across the top with the title "Same Question, Two Shapes" and a smaller subtitle underneath: "Cypher draws / SPARQL lists". Under the subtitle, a single small pill-shaped label centered: "Who re-signed after cancelling?"

The body is split into two equal vertical panels separated by a thin vertical divider line, with a convergence zone at the bottom. Reading flow: top question, then left and right panels in parallel, then two arrows curving down into one shared result box.

LEFT PANEL, tinted a soft teal. Panel heading: "Cypher — Draw the Shape" with a small pencil icon, and a short Korean gloss beneath in smaller type: "그림을 그린다". Inside, show an actual tiny node-link diagram: one rounded rectangle node labeled "Company" on the left, and two rounded rectangle nodes stacked on the right labeled "Contract" and "Contract". Draw two thick arrows from the Company node to the two Contract nodes; the upper arrow carries a small tag reading "Terminated", the lower arrow carries a tag reading "Signed". Below the diagram, a dark code chip in monospace font showing exactly two short lines:
(c)-[:Terminated]->(:Contract)
(c)-[:Signed]->(:Contract)
Beneath the code chip, three tiny bullet labels in a vertical list: "MATCH pattern", "WHERE filter", "RETURN columns".

RIGHT PANEL, tinted a soft amber. Panel heading: "SPARQL — List the Sentences" with a small list icon, and a short Korean gloss beneath in smaller type: "문장을 나열한다". Inside, show four horizontal sentence rows stacked vertically; each row is a three-slot strip with slots colored differently and separated by thin gaps, and each row ends with a bold period mark. The four rows read, in monospace:
?c   ex:terminated   ?old  .
?c   ex:signed       ?new  .
?old ex:endedOn      ?end  .
?new ex:startedOn    ?begin .
Above these rows put three tiny column captions aligned over the slots: "subject", "predicate", "object". Beneath the rows, three tiny bullet labels in a vertical list: "Graph pattern", "FILTER", "SELECT vars".

BOTTOM CONVERGENCE ZONE spanning full width. Two thick arrows, one from each panel, curve inward and merge into a single arrowhead pointing at a centered white result card. The card is a small table with a header row reading "고객 | 해지 | 재계약" and one data row reading "가온테크 | 2024-03-11 | 2025-06-02". Directly under the card, a short centered caption in medium weight: "Same answer, different shape". To the right of the card, a small muted warning box outlined in dashed grey with a warning triangle icon and a heading "Where it breaks", followed by four very short stacked lines: "variable-length paths", "shortest path", "aggregate counts", "edge properties".

Style: clean flat vector infographic, generous white space, off-white background, muted teal and amber accent palette with charcoal text, thin 2px outlines, subtle rounded corners, no gradients, no drop shadows, no photorealism, no 3D. Typography: crisp geometric sans-serif for labels and headings, true monospace for all code and query text. All text must be rendered sharply and spelled exactly as written. Aspect ratio 16:9.
