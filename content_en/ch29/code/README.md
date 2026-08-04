# Chapter 29 - One Backbone

`Part 5 - Where the Two Graphs Meet` | **English** | [한국어](../../../content/ch29/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "I sent the report to the team lead."

This is the last chapter of Part 5. Chapter 27 read the graph and Chapter 28 wrote to it, and we treated them *separately*. Here we join them. And up front: joining them completely does not work. Why not, and how far you should join, is half this chapter.

## Sections

| # | Title |
|---|---|
| 29.1 | Keep them apart and they diverge |
| 29.2 | Knowledge and execution in one graph |
| 29.3 | From the answer to the source, and back the other way |
| 29.4 | What gets worse when you join them |
| 29.5 | Making the architecture checkable |

## The chapter in one page

- Keep knowledge and execution state apart and they diverge. And they diverge without errors. Both sides do their job correctly and the result is wrong.
- "Read the latest every time" is not the answer. If a value changes mid-workflow, the reasoning stops being self-consistent. Holding it in state is not laziness, it is a deliberate snapshot.
- The answer is: hold it, but verify right before you write. Which requires a *read timestamp* attached to it.
- Putting knowledge and execution in one graph creates *an edge you had nowhere to draw when they were apart*: this execution read that fact. That edge builds lineage, and lineage gets used in both directions. "Why did this answer come out" and "if this is wrong, what falls over."
- But joining them completely multiplies write load by ten, because execution-state writes vastly outnumber knowledge writes. So compromise: state bodies in the fast store, links only in the graph.
- And I think that is correct design, not a compromise, because knowledge and execution have different lifetimes. The question is not "what goes in the same graph" but *"what has to be joined by an edge."*
- Write the reference architecture as something checkable, not as a picture. A picture diverges from the code in six months.
- And do not build all of it up front. Build what hurts, but put in the things that are *hard to add later*. The `Reads` edge is one of those.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| reference architecture | [De facto] | [learn.microsoft.com/en-us/azure/architecture/guide](https://learn.microsoft.com/en-us/azure/architecture/guide/) |
| data lineage | [Standard] | [w3.org/TR/prov-o/#Derivation](https://www.w3.org/TR/prov-o/#Derivation) |
| read timestamp | [De facto] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |
| polyglot persistence | [De facto] | [martinfowler.com/bliki/PolyglotPersistence.html](https://martinfowler.com/bliki/PolyglotPersistence.html) |
| bounded context | [De facto] | [martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html) |
| fitness function | [De facto] | [thoughtworks.com/.../fitness-function-driven-development](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development) |
| write path separation | [De facto] | [neo4j.com/docs/operations-manual/current/performance](https://neo4j.com/docs/operations-manual/current/performance/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch29/code/`](../../../content/ch29/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 5 - Where the Two Graphs Meet` | **English** | [한국어](../../../content/ch29/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "I sent the report to the team lead."

This is the last chapter of Part 5. Chapter 27 read the graph and Chapter 28 wrote to it, and we treated them *separately*. Here we join them. And up front: joining them completely does not work. Why not, and how far you should join, is half this chapter.

## Sections

| # | Title |
|---|---|
| 29.1 | Keep them apart and they diverge |
| 29.2 | Knowledge and execution in one graph |
| 29.3 | From the answer to the source, and back the other way |
| 29.4 | What gets worse when you join them |
| 29.5 | Making the architecture checkable |

## The chapter in one page

- Keep knowledge and execution state apart and they diverge. And they diverge without errors. Both sides do their job correctly and the result is wrong.
- "Read the latest every time" is not the answer. If a value changes mid-workflow, the reasoning stops being self-consistent. Holding it in state is not laziness, it is a deliberate snapshot.
- The answer is: hold it, but verify right before you write. Which requires a *read timestamp* attached to it.
- Putting knowledge and execution in one graph creates *an edge you had nowhere to draw when they were apart*: this execution read that fact. That edge builds lineage, and lineage gets used in both directions. "Why did this answer come out" and "if this is wrong, what falls over."
- But joining them completely multiplies write load by ten, because execution-state writes vastly outnumber knowledge writes. So compromise: state bodies in the fast store, links only in the graph.
- And I think that is correct design, not a compromise, because knowledge and execution have different lifetimes. The question is not "what goes in the same graph" but *"what has to be joined by an edge."*
- Write the reference architecture as something checkable, not as a picture. A picture diverges from the code in six months.
- And do not build all of it up front. Build what hurts, but put in the things that are *hard to add later*. The `Reads` edge is one of those.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| reference architecture | [De facto] | [learn.microsoft.com/en-us/azure/architecture/guide](https://learn.microsoft.com/en-us/azure/architecture/guide/) |
| data lineage | [Standard] | [w3.org/TR/prov-o/#Derivation](https://www.w3.org/TR/prov-o/#Derivation) |
| read timestamp | [De facto] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |
| polyglot persistence | [De facto] | [martinfowler.com/bliki/PolyglotPersistence.html](https://martinfowler.com/bliki/PolyglotPersistence.html) |
| bounded context | [De facto] | [martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html) |
| fitness function | [De facto] | [thoughtworks.com/.../fitness-function-driven-development](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development) |
| write path separation | [De facto] | [neo4j.com/docs/operations-manual/current/performance](https://neo4j.com/docs/operations-manual/current/performance/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch29/code/`](../../../content/ch29/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch29/code
pip install kuzu

python3 ex1_two_stores.py        # keep them apart and they diverge
python3 ex2_one_backbone.py      # knowledge and execution in one graph
python3 ex3_lineage.py           # from the answer to the source, and back
python3 ex4_split_cost.py        # what gets worse when you join (no dependencies)
python3 ex5_reference_arch.py    # the architecture as something checkable (no dependencies)
```

The latencies in `ex4` (graph write 4.2 ms, key-value 0.35 ms) are simplified from Chapter 21's
measurements. Measure your own. The ratio is what matters, not the absolute value.

`ex5` deliberately contains one rule violation. Put it in CI and it fails right there.

<!-- 실행 가이드 끝 -->

---

**What you meet in the next part:** Part 5 joined the two graphs. Once joined, the remaining problems all wear the same face. What changed when, what happens when two things edit at once, how to change the structure without breaking what is running. Part 6 is about *operating* that backbone.

---

Previous: [Ch 28 When the Agent Grows the Graph by Itself](../../ch28/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 30 Nobody Knows What Changed, or When](../../ch30/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
