Create a clean, educational flat-design infographic, 16:9 landscape, titled "Three Answers to the Lost Update" with a small Korean subtitle "잃어버린 갱신 (Lost Update)".

Overall layout: a slim problem strip across the top, then three equal vertical comparison columns filling the middle, then a single conclusion bar across the bottom. Reading flow goes top-down, then left-to-right across the three columns.

TOP STRIP — "The Problem 문제":
A small horizontal timeline with two parallel agent lanes labeled "Agent A" and "Agent B". Both lanes start with a blue "READ" dot pointing at the same shared box labeled "팀장=박민수 · 인원=3". Both lanes then show a long "THINK" bar, then an orange "WRITE" dot. Agent B writes first, Agent A writes last. An arrow from A's write lands on the final state box labeled "인원=3" marked with a red X and the caption "B's change vanished". A small red tag beside it reads "No error. Log says OK."

MIDDLE — three columns, each a rounded card with a colored header band, an icon, a mechanism diagram, and two short bullet rows labeled "GOOD" (green check) and "BAD" (red cross):

Column 1 — red/grey header "1. LOCKING 잠금".
Icon: a closed padlock over a node.
Diagram: Agent A holds a lock around a shaded band covering READ-THINK-WRITE; Agent B is a greyed-out queue box labeled "waiting".
GOOD: "Always correct".
BAD: "Slow · deadlocks".

Column 2 — blue header "2. OPTIMISTIC LOCK 낙관적 잠금".
Icon: a magnifying glass over a version tag "v3".
Diagram: READ (v3) — THINK outside any lock — then a small gate labeled "WHERE version = 3". Two outcomes branch from the gate: green "rowcount 1 → OK" and red "rowcount 0 → retry", with a curved retry arrow looping back to READ.
GOOD: "No cost when no conflict".
BAD: "Retries pile up".

Column 3 — green header "3. FIELD-LEVEL WRITE 필드 단위 변경".
Icon: a node split into separate small field chips.
Diagram: one node box divided into chips "팀장" and "인원"; Agent A's arrow enters only the "팀장" chip, Agent B's arrow only the "인원" chip, no overlap, both green checks. A tiny crossed-out label reads "no read-modify-write window".
GOOD: "No conflict at all".
BAD: "Cannot read-then-decide".

BOTTOM BAR — a wide highlighted band. On the left, a large formula "2 + 3 = the practical answer" with "실무의 답" underneath. On the right, a small horizontal gauge labeled "Conflict rate 충돌률" running 0% to 70%, shaded blue on the left half labeled "Optimistic wins" and red on the right labeled "Locking wins", with a marker at the 15–30% zone labeled "tipping point".

Style: clean flat vector infographic, generous white space, off-white background, muted palette of slate grey, blue, green, warm red, thin 2px outlines, rounded corners, subtle drop shadows, crisp sans-serif labels, all labels short (3-5 words maximum), no photorealism, no clutter. Aspect ratio 16:9.
