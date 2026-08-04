# Chapter 1 - Sixty Years of AI, Read as a Graph

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch01/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> Last autumn I met two teams in the same week. Both were bolting a language model onto internal document search. Same model, same API key, same price list. One opened it to the company in three weeks. The other was nine weeks in, still holding meetings about how "the model keeps making things up."

This chapter stretches that story across sixty years. Early AI had graphs. Deep learning dissolved them into vectors. And now we are drawing graphs again. Three sentences are the whole chapter; the rest is evidence.

## Sections

| # | Title |
|---|---|
| 1.1 | When we had the graph |
| 1.2 | When we dissolved the graph into vectors |
| 1.3 | Which knob moves what |
| 1.4 | Getting the graph back |
| 1.5 | The harness: the wiring around the model |
| 1.6 | Two tracks |

## The chapter in one page

- Early AI wrote knowledge down as nodes and edges. It collapsed because people had to fill it in by hand.
- Deep learning melted those relations into distances between coordinates. Nobody has to fill it in anymore, but nothing stores the relation. It gets recomputed and thrown away, every time.
- In the agent era we are drawing graphs again. State graphs, checkpoints, termination conditions, provenance. New names, all of them nodes and edges.
- The bundle of wiring outside the model is called the harness. The harness is a graph. So harness engineering is graph engineering.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Transformer | [De facto] | [arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762) |
| scaling laws | [Experimental] | [arxiv.org/abs/2001.08361](https://arxiv.org/abs/2001.08361) |
| ReAct | [De facto] | [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629) |
| knowledge graph | [De facto] | [blog.google/.../introducing-knowledge-graph-things-not](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| state graph, superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| harness | [Experimental] | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch01/code/`](../../../content/ch01/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch01/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> Last autumn I met two teams in the same week. Both were bolting a language model onto internal document search. Same model, same API key, same price list. One opened it to the company in three weeks. The other was nine weeks in, still holding meetings about how "the model keeps making things up."

This chapter stretches that story across sixty years. Early AI had graphs. Deep learning dissolved them into vectors. And now we are drawing graphs again. Three sentences are the whole chapter; the rest is evidence.

## Sections

| # | Title |
|---|---|
| 1.1 | When we had the graph |
| 1.2 | When we dissolved the graph into vectors |
| 1.3 | Which knob moves what |
| 1.4 | Getting the graph back |
| 1.5 | The harness: the wiring around the model |
| 1.6 | Two tracks |

## The chapter in one page

- Early AI wrote knowledge down as nodes and edges. It collapsed because people had to fill it in by hand.
- Deep learning melted those relations into distances between coordinates. Nobody has to fill it in anymore, but nothing stores the relation. It gets recomputed and thrown away, every time.
- In the agent era we are drawing graphs again. State graphs, checkpoints, termination conditions, provenance. New names, all of them nodes and edges.
- The bundle of wiring outside the model is called the harness. The harness is a graph. So harness engineering is graph engineering.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Transformer | [De facto] | [arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762) |
| scaling laws | [Experimental] | [arxiv.org/abs/2001.08361](https://arxiv.org/abs/2001.08361) |
| ReAct | [De facto] | [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629) |
| knowledge graph | [De facto] | [blog.google/.../introducing-knowledge-graph-things-not](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| state graph, superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| harness | [Experimental] | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch01/code/`](../../../content/ch01/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch01/code

# Examples 1 and 2 - no dependencies
python3 ex1_vector_only.py
python3 ex2_graph_grounded.py

# Example 3 - needs LangGraph (no API key)
pip install "langgraph>=1.0,<2.0"
python3 ex3_agent_loop.py
```

| File | What it shows | What you should see |
|---|---|---|
| `notes.py` | The same facts written twice: as 8 lines of prose and as 7 triples | - |
| `ex1_vector_only.py` | Trying to answer a 2-hop question with vector search alone | Wrong answer. An unrelated company gets dragged in |
| `ex2_graph_grounded.py` | The same question, walked as a graph path | Correct, and the supporting path is printed with it |
| `ex3_agent_loop.py` | A state-graph loop with a termination condition and checkpoints | Correct. One retry, then it stops. 8 checkpoints |

`ex1` is not wrong because the embedding model is small. It is wrong because the relation was
never stored. Swap in a bigger model and you get the same answer. Try it.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter only got as far as "the harness matters." The next one takes an entire body of harness practice from the last two years and gives every term in it a graph name. Once they all have one, fourteen chapters' worth of material folds into a single table.

---

[Contents](../../../README.en.md) | Next: [Ch 2 From Harness Engineering to Graph Engineering](../../ch02/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
