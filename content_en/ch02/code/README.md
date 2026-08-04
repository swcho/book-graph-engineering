# Chapter 2 - From Harness Engineering to Graph Engineering

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch02/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> An agent once deleted its own working directory. It was mine.

If the last chapter compressed sixty years, this one compresses the last two. It takes the body of practice people have been stacking up under the name "harness" and gives every term in it a graph name. Once they all have one, what would otherwise be fourteen chapters folds into a single table.

## Sections

| # | Title |
|---|---|
| 2.1 | Around the model: what lives outside it |
| 2.2 | Thirty minutes is enough: two nodes |
| 2.3 | Deciding order is topological sort |
| 2.4 | Star to mesh: topology is cost |
| 2.5 | The six patterns are really six topologies |
| 2.6 | The day you have 292 nodes |
| 2.7 | A graph that builds graphs |
| 2.8 | The translation table |

## The chapter in one page

- An agent working alone cannot see its own mistakes. It is looking at the same context. Write the rule into the prompt and it gets cut on the day the context fills up. Attach it to an edge and it does not.
- An agent definition is a node, a skill is a subgraph, an orchestrator is an executor. A prerequisite is a DAG edge, and a topologically sorted batch of them is a superstep.
- Topology is cost. A star scales with the number of members; a mesh scales with the square. In exchange, the star's leader is the first thing to buckle.
- The six architecture patterns are six graph topologies, and the antipattern catalog is a list of graph smells. The translation table in this chapter doubles as the table of contents for the whole book.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| context engineering | [De facto] | [anthropic.com/.../effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| agent harness | [Experimental] | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |
| state graph, superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| AGENTS.md | [De facto] | [agents.md](https://agents.md/) |
| A2A | [Experimental] | [a2a-protocol.org](https://a2a-protocol.org/) |
| topological sort | [Standard] | [dl.acm.org/doi/10.1145/368996.369025](https://dl.acm.org/doi/10.1145/368996.369025) |
| event sourcing | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch02/code/`](../../../content/ch02/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch02/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> An agent once deleted its own working directory. It was mine.

If the last chapter compressed sixty years, this one compresses the last two. It takes the body of practice people have been stacking up under the name "harness" and gives every term in it a graph name. Once they all have one, what would otherwise be fourteen chapters folds into a single table.

## Sections

| # | Title |
|---|---|
| 2.1 | Around the model: what lives outside it |
| 2.2 | Thirty minutes is enough: two nodes |
| 2.3 | Deciding order is topological sort |
| 2.4 | Star to mesh: topology is cost |
| 2.5 | The six patterns are really six topologies |
| 2.6 | The day you have 292 nodes |
| 2.7 | A graph that builds graphs |
| 2.8 | The translation table |

## The chapter in one page

- An agent working alone cannot see its own mistakes. It is looking at the same context. Write the rule into the prompt and it gets cut on the day the context fills up. Attach it to an edge and it does not.
- An agent definition is a node, a skill is a subgraph, an orchestrator is an executor. A prerequisite is a DAG edge, and a topologically sorted batch of them is a superstep.
- Topology is cost. A star scales with the number of members; a mesh scales with the square. In exchange, the star's leader is the first thing to buckle.
- The six architecture patterns are six graph topologies, and the antipattern catalog is a list of graph smells. The translation table in this chapter doubles as the table of contents for the whole book.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| context engineering | [De facto] | [anthropic.com/.../effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| agent harness | [Experimental] | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |
| state graph, superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| AGENTS.md | [De facto] | [agents.md](https://agents.md/) |
| A2A | [Experimental] | [a2a-protocol.org](https://a2a-protocol.org/) |
| topological sort | [Standard] | [dl.acm.org/doi/10.1145/368996.369025](https://dl.acm.org/doi/10.1145/368996.369025) |
| event sourcing | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch02/code/`](../../../content/ch02/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.
Only example 2 needs LangGraph. The rest have **no dependencies**.

```bash
cd content/ch02/code
python3 ex1_one_file.py       # everything in one file - the "before" of the 30-minute exercise
python3 ex2_two_nodes.py      # a two-node graph - the "after"
python3 ex3_depends_on.py     # depends_on is a DAG edge. A sorted batch is a superstep
python3 ex4_star_vs_mesh.py   # star vs mesh, counting messages
```

## Only example 2 needs an install

```bash
pip install "langgraph>=1.0,<2.0"
```

Checked against LangGraph 1.0.1. **No API key needed.**

## How it runs without an API key

`fake_model` in `harness.py` stands in for a real language model. It is fake, but not
arbitrarily so - it imitates two behaviors real models reliably show.

1. When instructions get long, it drops the requirements near the end.
2. When you point out what it dropped, it fills them in.

Those two behaviors are the entire argument of this chapter. Swap in a real model and the
degree changes, not the behavior.

## Run examples 1 and 2 side by side

The two examples use **prompts that are identical down to the character.** Only the structure
differs. The outputs differ anyway. That is the chapter's point.

```bash
python3 ex1_one_file.py  > /tmp/before.txt
python3 ex2_two_nodes.py > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

## Change the numbers yourself

The two constants at the top of `ex4_star_vs_mesh.py` differ per team. Put your own numbers in
and you find out what one edge costs you.

```python
AVG_TOKENS_PER_MSG = 1_200      # request + response. Measure yours.
PRICE_PER_MTOK_KRW = 4_000      # KRW per million tokens. Rough figure as of August 2026.
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** so far we have used graphs as if they were an obvious tool. The next chapter looks at when the graph was actually invented, and why tables beat it for forty years. If you do not know why tables won, you will repeat the same mistake.

---

Previous: [Ch 1 Sixty Years of AI, Read as a Graph](../../ch01/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 3 Why Seven Bridges Couldn't Be Crossed, and Why Tables Won](../../ch03/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
