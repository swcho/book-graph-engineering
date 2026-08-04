# Chapter 23 - Where the Human Steps In

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch23/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> An approval sat pending for two weeks.

Chapter 22 kept saying "hand it to a human" without defining how. This chapter is that: putting the human *inside* the graph as a node rather than outside it as an exception.

## Sections

| # | Title |
|---|---|
| 23.1 | Stopping is not an exception |
| 23.2 | Do not put side effects before an interrupt |
| 23.3 | Where do you install the gate |
| 23.4 | When the human does not answer |
| 23.5 | Record what you showed them |

## The chapter in one page

- Put the human inside the graph as a node, not outside it as an exception. An interrupt is a normal stop, and where it stopped lives in the checkpointer. You do not have to hold the process open.
- Do not put side effects before an interrupt. On resume, that node runs again from the top. If a side effect has to come first, split the node in two to create a boundary.
- Set the threshold from capacity, not taste. The lowest threshold at which review time stays under 70% of capacity. A policy where humans review everything becomes a policy where nobody reviews anything.
- With no no-answer policy, the default is "wait forever." Handle it differently as time passes. Escalation is a device for getting attention, not for raising the decision.
- An approval record needs what was shown and a fingerprint of the state. If the fingerprint differs, ask again. But hash only the fields that affect the decision. Ask every time and people start clicking without reading.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| human in the loop | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| interrupt | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| Command(resume) | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| approval gate | [De facto] | [learn.microsoft.com/.../gatekeeper](https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper) |
| escalation | [De facto] | [sre.google/workbook/incident-response](https://sre.google/workbook/incident-response/) |
| audit trail | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| four-eyes principle | [De facto] | [bis.org/publ/bcbs230.pdf](https://www.bis.org/publ/bcbs230.pdf) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch23/code/`](../../../content/ch23/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch23/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> An approval sat pending for two weeks.

Chapter 22 kept saying "hand it to a human" without defining how. This chapter is that: putting the human *inside* the graph as a node rather than outside it as an exception.

## Sections

| # | Title |
|---|---|
| 23.1 | Stopping is not an exception |
| 23.2 | Do not put side effects before an interrupt |
| 23.3 | Where do you install the gate |
| 23.4 | When the human does not answer |
| 23.5 | Record what you showed them |

## The chapter in one page

- Put the human inside the graph as a node, not outside it as an exception. An interrupt is a normal stop, and where it stopped lives in the checkpointer. You do not have to hold the process open.
- Do not put side effects before an interrupt. On resume, that node runs again from the top. If a side effect has to come first, split the node in two to create a boundary.
- Set the threshold from capacity, not taste. The lowest threshold at which review time stays under 70% of capacity. A policy where humans review everything becomes a policy where nobody reviews anything.
- With no no-answer policy, the default is "wait forever." Handle it differently as time passes. Escalation is a device for getting attention, not for raising the decision.
- An approval record needs what was shown and a fingerprint of the state. If the fingerprint differs, ask again. But hash only the fields that affect the decision. Ask every time and people start clicking without reading.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| human in the loop | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| interrupt | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| Command(resume) | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| approval gate | [De facto] | [learn.microsoft.com/.../gatekeeper](https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper) |
| escalation | [De facto] | [sre.google/workbook/incident-response](https://sre.google/workbook/incident-response/) |
| audit trail | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| four-eyes principle | [De facto] | [bis.org/publ/bcbs230.pdf](https://www.bis.org/publ/bcbs230.pdf) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch23/code/`](../../../content/ch23/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch23/code
pip install "langgraph>=1.0,<2.0"

python3 ex1_interrupt.py     # stop, take an answer, carry on
python3 ex2_node_reruns.py   # a side effect before the interrupt runs twice
python3 ex3_gate_policy.py   # setting the approval threshold from capacity (no dependencies)
python3 ex4_no_answer.py     # when the human does not answer (no dependencies)
python3 ex5_audit.py         # approval audit records (no dependencies)
```

`ex1` and `ex2` use the in-memory checkpointer. In production, use a disk-backed one as covered
in Chapter 21, so it still resumes when a person answers three days later.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter said to store the whole content of the moment you asked. Pile that up and state explodes. The next chapter is what to throw away when the context is full.

---

Previous: [Ch 22 How to Pay Back What You Can't Undo](../../ch22/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 24 Your Context Is Full](../../ch24/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
