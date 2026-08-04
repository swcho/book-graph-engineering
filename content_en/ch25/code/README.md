# Chapter 25 — Six Topologies, and the Sockets You Plug Tools Into

`Part 4 — Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch25/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "So how many agents should we split this into?"

There is a reason both topics live in one chapter. Seen as a graph they are the same thing: *topology is how you connect nodes to each other, and a tool is an edge that connects a node to the outside*. Inside wiring and outside wiring.

## Sections

| # | Title |
|---|---|
| 25.1 | There are only six |
| 25.2 | Joining costs more than fanning out |
| 25.3 | A router is not a quality device |
| 25.4 | A tool is an edge leaving the graph |
| 25.5 | The tool description is the edge selection function |

## The chapter in one page

- There are only six topologies: path, split-join, star, cycle, dynamic edge, tree. Every structure that looks complicated is a combination of those six. Names vary by person, so talk in pictures.
- There is no "good" topology. The fastest, the cheapest, and the highest quality are three different ones. Decide what your constraint is first, and with no constraint, take the simplest path.
- Parallelism buys time, it does not save money. The tokens are the same.
- The join costs more than the fan-out, and the join is what sets the ceiling. Profile the join before you widen the fan. If there is an operation that compares branches against each other, that is quadratic.
- Widening reduces total time but lengthens one wave. The average improves and the worst case gets worse. Users mostly feel the worst case.
- A router is not a quality device, it is a trade. To calculate what you give up and what you save, you need a scored dataset first.
- A tool is an edge leaving the graph, and MCP is a way of receiving that edge list at runtime. The price is knowing nothing at compile time. Validate the list at startup.
- The tool description is the edge selection function. Write three things: what it gives you, what words to ask it with, and *when not to use it*. The third is the most often omitted and the most expensive.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| orchestrator-workers | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| fan-out/fan-in | [De facto] | [learn.microsoft.com/…/durable-functions-cloud-backup](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-cloud-backup) |
| routing | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| evaluator-optimizer | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| tail latency | [De facto] | [research.google/pubs/the-tail-at-scale](https://research.google/pubs/the-tail-at-scale/) |
| Model Context Protocol | [De facto] | [modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18) |
| tool schema | [De facto] | [modelcontextprotocol.io/…/tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) |
| Send | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch25/code/`](../../../content/ch25/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch25/code
python3 ex1_topologies.py       # the six topologies compared (no dependencies)
python3 ex2_fanout.py           # fan-out cost vs join cost (no dependencies)
python3 ex3_router.py           # router accuracy and the trade (no dependencies)

pip install mcp
python3 ex4_mcp_client.py       # connects to a real MCP server (spawns mcp_server.py)

python3 ex5_tool_selection.py   # the description decides the selection (no dependencies)
```

`ex4` spawns `mcp_server.py` as a child process. You do not need to start it separately.
As checked, the mcp Python SDK was 1.5.0 and the protocol version was 2024-11-05.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter was about what to *allow*. Attaching tools, splitting agents. The next one is the opposite: *what will you forbid*, and why forbidding is harder than allowing.

---

Previous: [Ch 24 Your Context Is Full](../../ch24/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 26 What Will You Forbid](../../ch26/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
