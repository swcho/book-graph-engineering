Infographic, clean flat vector style, soft off-white background, 16:9 landscape.

Title at top center, bold: "Idempotency Key: Retry Without Double Charge" with Korean subtitle "멱등 키 (idempotency key)".

Layout: a small setup banner under the title, then three equal vertical columns side by side, eye flow left to right, then a verdict strip at the bottom.

Setup banner: a small client icon labeled "Process crashes, retries 3x" with three arrows pointing toward a payment server icon labeled "Payment API". Each arrow tagged "charge 50,000 KRW".

Column 1, header "No Key" (한국어: 키 없음), light red tint: client sends 3 plain requests, server icon with no key slot, below it 3 stacked receipt cards labeled "R-001", "R-002", "R-003". Big result badge in red: "3 charges, 150,000 KRW". Small caption "Server cannot dedupe".

Column 2, header "Key Sent, Ignored" (한국어: 서버 미지원), light red tint: client sends 3 requests each carrying a small key icon, but the server has a crossed-out key slot (key icon with X). Again 3 stacked receipts "R-001", "R-002", "R-003". Big result badge in red: "3 charges, 150,000 KRW". Small caption "Key useless if unsupported".

Column 3, header "Key Sent, Honored" (한국어: 서버 지원), light green tint, slightly glowing border to mark it as the correct case: client sends 3 requests with key icons, server shows a key-value store box labeled "seen_keys". Only 1 receipt card "R-001"; the 2nd and 3rd arrows loop back with a small cache icon labeled "cached result". Big result badge in green with a checkmark: "1 charge, 50,000 KRW".

Bottom verdict strip, dark band with white text: "Safe = client sends key AND server checks it" with two small checkboxes labeled "Send key?" and "Server honors it?".

Style: minimal geometric icons, generous whitespace, red/green accents only for outcomes, all labels short (3-5 words), sans-serif typography, no photorealism.
