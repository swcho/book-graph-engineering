# Chapter 9 — Counting Degrees of Separation Killed the Server

`Part 2 — The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch09/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "Show me everyone connected to this person."

This chapter is about walking on a graph. How to walk, where to stop, and when not to walk at all. The last one matters most.

## Sections

| # | Title |
|---|---|
| 9.1 | Eleven times per hop |
| 9.2 | Walk from both ends and it becomes a square root |
| 9.3 | Once weights are involved |
| 9.4 | One path and every path |
| 9.5 | Graphs with an order: topological sort |

## The chapter in one page

- In a graph with average degree 12, each hop multiplies by 11. Five hops reaches 68% of everything; six reaches all of it. An unbounded traversal is a full scan wearing a hat.
- When you are looking between two points, search bidirectionally. Halving the radius makes the visited count a square root. Measured, it dropped 75x to 88x.
- Dijkstra is quietly wrong with negative weights. No exception is raised. Be especially careful anywhere you take the log of a probability.
- "One shortest path" and "all paths" are different problems. The first is polynomial, the second is exponential. When someone asks to "see them all," ask back.
- Topological sort gives you layers you can run in parallel, but layer-by-layer is slower than the critical path, because you wait for the slowest task in each layer.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| BFS | [De facto] | [networkx.org/…/traversal.html](https://networkx.org/documentation/stable/reference/algorithms/traversal.html) |
| bidirectional search | [De facto] | [networkx.org/…/networkx.algorithms.shortest_paths.unweighted.bid](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.unweighted.bidirectional_shortest_path.html) |
| Dijkstra's algorithm | [Standard] | [link.springer.com/article/10.1007/BF01386390](https://link.springer.com/article/10.1007/BF01386390) |
| Bellman-Ford | [De facto] | [networkx.org/…/networkx.algorithms.shortest_paths.weighted.bellm](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.bellman_ford_path.html) |
| A* | [De facto] | [ieeexplore.ieee.org/document/4082128](https://ieeexplore.ieee.org/document/4082128) |
| topological sort | [Standard] | [dl.acm.org/doi/10.1145/368996.369025](https://dl.acm.org/doi/10.1145/368996.369025) |
| Cypher variable-length patterns | [De facto] | [neo4j.com/…/variable-length-patterns](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-patterns/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch09/code/`](../../../content/ch09/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch09/code
python3 ex1_bfs_explosion.py        # how many times the visited count multiplies per hop
python3 ex2_bidirectional.py        # why bidirectional search cuts it 75x
python3 ex3_dijkstra_negative.py    # how a negative weight quietly returns a wrong answer
python3 ex4_path_explosion.py       # one shortest path and all paths are different problems
python3 ex5_toposort.py             # topological sort, supersteps, the critical path
```

`ex1` and `ex2` build 200,000 nodes and use about 1 GB of memory.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** so far we asked how far you can go. The next chapter asks who matters. Pick the wrong importance measure and the most important person in the company comes out as the person who empties the bins.

---

Previous: [Ch 8 What a Graph Actually Looks Like in Memory](../../ch08/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 10 Which Node Actually Matters](../../ch10/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
