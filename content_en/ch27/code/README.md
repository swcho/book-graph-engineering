# Chapter 27 — The Cheapest Way to Give an Agent Memory

`Part 5 — Where the Two Graphs Meet` | **English** | [한국어](../../../content/ch27/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "I told you this last time."

One thing up front: the conclusion of this chapter is not "use a graph." Half of it is about *when a graph starts to be worth it*, and what to get by with until then.

## Sections

| # | Title |
|---|---|
| 27.1 | Decide which questions the shape can answer |
| 27.2 | Vectors and graphs are strong on different questions |
| 27.3 | Memory needs a timestamp |
| 27.4 | When does a graph start paying off |
| 27.5 | What will you forget |

## The chapter in one page

- The shape of memory decides which questions it can answer. Flat text cannot connect several lines, key-value answers only in the slots you made in advance, and a graph follows paths you did not know about when you stored it.
- The reason to use a graph as memory is one sentence: *you do not have to know the question at write time.*
- But a graph cannot hold the ambiguous. Put what the user said into the graph and what you inferred into the raw text.
- Vectors and graphs are strong on different questions. Similar things go to vectors; connected things, "all of them," and "none" go to the graph. In practice you find the starting point with a vector and widen with the graph.
- Memory needs valid times. Do not delete what is old, write down when it ended. And when you insert a new fact, close the old one. A list of single-valued relations in code is enough.
- Do not start with a graph. It starts paying off around a thousand facts. Below that, a flat list is cheaper, and moving takes two days.
- Do not design the schema from above; let it grow from below. Query-first is right for domains where you know the queries, but for conversational memory the data accumulates first and the schema follows.
- Decide what to forget by kind, not age. One-offs last a week, preferences and relationships a year, constraints effectively forever. One policy for all of them is wrong in one direction or the other.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| long-term memory | [De facto] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| episodic memory | [Experimental] | [arxiv.org/abs/2404.13501](https://arxiv.org/abs/2404.13501) |
| temporal knowledge graph | [Experimental] | [arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956) |
| hybrid retrieval | [De facto] | [neo4j.com/…/vector-indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) |
| decay policy | [Experimental] | [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560) |
| entity resolution | [De facto] | [w3.org/TR/owl2-syntax/#Individual_Equality](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| valid time | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch27/code/`](../../../content/ch27/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch27/code
pip install kuzu

python3 ex1_memory_shapes.py     # the same memory in three shapes
python3 ex2_graph_vs_vector.py   # vectors and graphs are strong on different questions
python3 ex3_temporal_memory.py   # "true from when to when"
python3 ex4_memory_cost.py       # daily cost of both approaches by fact count
python3 ex5_forgetting.py        # three forgetting policies (no dependencies)
```

The "embeddings" in `ex2` are hand-written 3-dimensional coordinates. With a real embedding
model the numbers change, but what vectors *cannot* do (count everything, confirm absence) does
not.

`ex4` gives slightly different lookup times on every run. At this scale measurement noise
dominates, and that is itself the point of the example.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter was about remembering what a person said. The next one has the agent start *writing what it worked out itself* into the graph. Once the thing that only read starts writing, Chapter 26's permission story carries entirely different weight.

---

Previous: [Ch 26 What Will You Forbid](../../ch26/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 28 When the Agent Grows the Graph by Itself](../../ch28/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
