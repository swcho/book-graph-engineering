Create a clean, flat-design educational infographic titled "route(): Priority Order of Loop Exit Checks" with a Korean subtitle "루프 종료 판정 순서".

Aspect ratio: 3:4 (vertical portrait). White or very light gray background, generous white space, thin rounded strokes, a restrained palette of muted teal, warm amber, soft coral, slate gray, and one deep navy for text.

LAYOUT — three stacked bands, read top to bottom.

TOP BAND (about 15% height): The title, and beneath it a single horizontal entry arrow labeled "After critic node 검증" flowing into the flowchart below. A small caption on the right reads "First match wins".

MIDDLE BAND (about 60% height) — the core sequential decision flowchart, a vertical spine of four diamond decision nodes connected top to bottom, each with a "No" arrow continuing DOWN the spine and a "Yes" arrow branching RIGHT into a colored rounded outcome box. Number each diamond with a bold circled digit 1 to 4.

1. Diamond labeled "missing is empty?" with small Korean "남은 항목 없음". Yes-branch box in muted teal labeled "SUCCESS 성공" with a tiny checkmark icon and a sub-label "Use the output".
2. Diamond labeled "rounds >= MAX_ROUNDS" with sub-text "6". Yes-branch box in slate gray labeled "ROUND CAP 상한" with a tiny repeat-arrow icon and sub-label "Escalate, may retry".
3. Diamond labeled "cost >= MAX_COST" with sub-text "90". Yes-branch box in warm amber labeled "BUDGET 예산" with a tiny coin icon and sub-label "Ask to raise budget".
4. Diamond labeled "stalled(scores)?" with sub-text "window of 3". Yes-branch box in soft coral labeled "STALL 정체" with a tiny flat-line icon and sub-label "Escalate, retry won't help".

Below the fourth diamond, the final No-arrow leads to a dashed-outline box labeled "GENERATE 생성" with a curved loop-back arrow returning up to the top entry point, tagged "Loop again".

On the LEFT edge of the flowchart, a tall vertical gradient bar annotated top "Goal reached" and bottom "Fallback", with two bracket labels: an upper bracket spanning diamonds 2 and 3 reading "Certain facts", and a lower bracket on diamond 4 reading "Heuristic estimate".

BOTTOM BAND (about 25% height) — a contrast panel titled "Wrong order, wrong verdict", showing three small before/after pairs side by side, each an arrow from a red-tinted misordered label to the misreported outcome:
- "Cap before success" leads to "Finished doc marked failed"
- "Stall before cap" leads to "Retryable turns fatal"
- "Generate first" leads to "Infinite loop"

Style: modern educational infographic, flat vector, no photorealism, no 3D, no drop shadows, crisp thin outlines, clear sans-serif typography, all labels short. Ensure every text label is legible and correctly spelled.
