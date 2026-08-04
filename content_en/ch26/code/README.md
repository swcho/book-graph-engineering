# Chapter 26 - What Will You Forbid

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch26/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I spent thirty minutes in a permissions review confirming that "read-only is safe, right?"

If the last chapter was about what to allow, this one is the reverse. And this side is much harder. Allowing is additive; forbidding means looking at *combinations*.

## Sections

| # | Title |
|---|---|
| 26.1 | A permission is a path, not a list |
| 26.2 | A deny list always leaks |
| 26.3 | There are instructions inside the text you fetched |
| 26.4 | How far does it go when one thing falls |
| 26.5 | Record what you blocked, too |

## The chapter in one page

- A permission is a path, not a list. Individually harmless permissions combine into an exfiltration path. Do not look at tools one at a time; ask which permission is a door out. Usually there are three: outbound network, arbitrary execution, write.
- And when you count the ways out, do not look only at the network. Logs, error messages, and the response itself are ways out.
- A deny list always leaks. You can only block what you can enumerate, and the workarounds are not enumerable. An allow list keeps costing you attention and does not leak. But allowing command names is not enough; you have to inspect arguments, and compare the normalized form rather than the string.
- You cannot stop prompt injection with a prompt. Delimiters and input checks lower the probability; only removing the permission removes the possibility. First priority is making the agent structurally unable to do it.
- Assume it gets breached eventually and measure the blast radius. Least privilege is not "only what you need for your job," it is "no single principal holds a lethal combination."
- "Reads are safe" is wrong. Reads cost money, leave traces, and hurt the other side.
- Record what you blocked. The share that humans overturn is your policy quality metric. A rule overturned 100% of the time is spending human attention and nothing else.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| least privilege | [De facto] | [csrc.nist.gov/glossary/term/least_privilege](https://csrc.nist.gov/glossary/term/least_privilege) |
| allowlist | [De facto] | [cheatsheetseries.owasp.org/.../Input_Validation_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) |
| prompt injection | [De facto] | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| indirect prompt injection | [De facto] | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| blast radius | [De facto] | [sre.google/sre-book/addressing-cascading-failures](https://sre.google/sre-book/addressing-cascading-failures/) |
| privilege escalation | [Standard] | [attack.mitre.org/tactics/TA0004](https://attack.mitre.org/tactics/TA0004/) |
| sandbox | [De facto] | [gvisor.dev/docs](https://gvisor.dev/docs/) |
| audit log | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch26/code/`](../../../content/ch26/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch26/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I spent thirty minutes in a permissions review confirming that "read-only is safe, right?"

If the last chapter was about what to allow, this one is the reverse. And this side is much harder. Allowing is additive; forbidding means looking at *combinations*.

## Sections

| # | Title |
|---|---|
| 26.1 | A permission is a path, not a list |
| 26.2 | A deny list always leaks |
| 26.3 | There are instructions inside the text you fetched |
| 26.4 | How far does it go when one thing falls |
| 26.5 | Record what you blocked, too |

## The chapter in one page

- A permission is a path, not a list. Individually harmless permissions combine into an exfiltration path. Do not look at tools one at a time; ask which permission is a door out. Usually there are three: outbound network, arbitrary execution, write.
- And when you count the ways out, do not look only at the network. Logs, error messages, and the response itself are ways out.
- A deny list always leaks. You can only block what you can enumerate, and the workarounds are not enumerable. An allow list keeps costing you attention and does not leak. But allowing command names is not enough; you have to inspect arguments, and compare the normalized form rather than the string.
- You cannot stop prompt injection with a prompt. Delimiters and input checks lower the probability; only removing the permission removes the possibility. First priority is making the agent structurally unable to do it.
- Assume it gets breached eventually and measure the blast radius. Least privilege is not "only what you need for your job," it is "no single principal holds a lethal combination."
- "Reads are safe" is wrong. Reads cost money, leave traces, and hurt the other side.
- Record what you blocked. The share that humans overturn is your policy quality metric. A rule overturned 100% of the time is spending human attention and nothing else.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| least privilege | [De facto] | [csrc.nist.gov/glossary/term/least_privilege](https://csrc.nist.gov/glossary/term/least_privilege) |
| allowlist | [De facto] | [cheatsheetseries.owasp.org/.../Input_Validation_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) |
| prompt injection | [De facto] | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| indirect prompt injection | [De facto] | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| blast radius | [De facto] | [sre.google/sre-book/addressing-cascading-failures](https://sre.google/sre-book/addressing-cascading-failures/) |
| privilege escalation | [Standard] | [attack.mitre.org/tactics/TA0004](https://attack.mitre.org/tactics/TA0004/) |
| sandbox | [De facto] | [gvisor.dev/docs](https://gvisor.dev/docs/) |
| audit log | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch26/code/`](../../../content/ch26/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. No external dependencies.

```bash
cd content/ch26/code
python3 ex1_permission_graph.py   # permissions as reachable paths, not lists
python3 ex2_deny_vs_allow.py      # why a deny list always leaks
python3 ex3_injection.py          # instructions embedded in a document
python3 ex4_blast_radius.py       # how far it goes when one thing falls
python3 ex5_audit_trail.py        # block logs are what fix the policy
```

`ex3` does not call a model. Measuring a real injection success rate needs one, and that
experiment would mean printing attack strings in the book, so only the *structure* is shown here.

<!-- 실행 가이드 끝 -->

---

**What you meet in the next part:** that was the agent graph. In the next part the two tracks converge. Part 3's knowledge graph becomes the agent's memory, and the agent starts *expanding that graph itself*. At which point this chapter's permission story gets much heavier, because reading and writing now happen on the same graph.

---

Previous: [Ch 25 Six Topologies, and the Sockets You Plug Tools Into](../../ch25/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 27 The Cheapest Way to Give an Agent Memory](../../ch27/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
