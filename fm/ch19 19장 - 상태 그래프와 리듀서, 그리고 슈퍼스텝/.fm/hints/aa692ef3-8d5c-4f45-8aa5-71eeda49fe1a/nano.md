Create a clean, flat-design educational infographic with a strong left-vs-right contrast layout, 16:9 landscape aspect ratio.

TITLE (top center, large bold sans-serif):
"Logs vs Checkpoints — Debugging a Graph Agent"
Small subtitle underneath in lighter gray: "What survives, and what you can rewind"

OVERALL LAYOUT:
Two large vertical panels side by side, separated by a thin vertical divider line down the middle. Left panel has a cool gray/slate color scheme. Right panel has a vivid teal and amber color scheme, visually richer. Reading flow: title at top, then eyes sweep left panel top-to-bottom, cross the divider, then right panel top-to-bottom, ending at a comparison strip along the bottom.

LEFT PANEL — label at its top in bold: "LOGS (로그)"
Sub-label in small gray text: "Write-once, forward only"
Visual content:
- A vertical stack of 5 plain text lines rendered like terminal output in a monospace font, inside a dark flat rectangle. Lines read exactly:
  "spent 30"
  "spent 65"
  "spent 95"
  "spent 115"
  "BUDGET EXCEEDED"
- The last line "BUDGET EXCEEDED" is highlighted in red.
- A single thick gray arrow running straight down the left edge, one direction only, with a small label "time, one way".
- Three small ghosted/faded gray text lines below the terminal box, drawn semi-transparent with dashed outlines, labeled with a small tag: "Not printed = gone forever". These faded lines read "round = ?", "next node = ?", "why = ?".
- A small icon of a padlock over a printer, with the caption "Only what you chose to print".

RIGHT PANEL — label at its top in bold: "CHECKPOINTS (체크포인트)"
Sub-label in small gray text: "Full state, every superstep"
Visual content:
- A horizontal row of 4 rounded square snapshot cards, evenly spaced, each labeled below as "step 0", "step 1", "step 2", "step 3".
- Each card contains three tiny colored data rows to suggest a full state object, with small field labels: "spent", "round", "next".
- Card "step 2" is highlighted with a bright amber glow border and a callout bubble pointing at it that reads "Just before it broke".
- A curved rewind arrow sweeping backward from card "step 3" to card "step 2", drawn in bold teal, labeled "rewind / 되감기".
- From card "step 2", a branching fork: two arrows diverge to the right. The upper branch is faded gray, labeled "original run". The lower branch is bold amber, labeled "re-run, changed value", and ends at a new card drawn with a dashed amber outline labeled "what if?".
- A small code chip badge near the fork with monospace text: "update_state()".

BOTTOM STRIP (spanning full width, light background band):
Three small side-by-side comparison items, each an icon plus a very short label:
1. magnifying glass icon — "Logs: where it broke"
2. clock-rewind icon — "Checkpoints: what it was doing"
3. two puzzle pieces joining icon — "Use both, not either"

A short warning line at the very bottom in small red text with a caution triangle icon:
"State-free data is not saved"

STYLE:
Clean flat vector design, educational infographic aesthetic, generous white space, light neutral background (#F7F8FA). Limited palette: slate gray for the logs side, teal (#0F9B8E) and amber (#F2A63B) for the checkpoint side, red (#E5484D) only for warnings. Bold geometric sans-serif typography, crisp thin connector lines, subtle soft shadows on cards, no gradients, no photorealism, no 3D. All text must be rendered accurately and legibly. Korean terms appear only where specified in parentheses.
