# Chapter 7 - One Node Drawn Wrong Cost Me Three Weeks

`Part 2 - The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch07/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I drew contracts as an edge. `(Company)-[:CONTRACT]->(Company)`. It looked lovely on the whiteboard.

This chapter is about those judgment calls. Node or edge, which way the direction goes, what the weight actually means. On a whiteboard they all look about the same. Six months later they do not.

## Sections

| # | Title |
|---|---|
| 7.1 | Node or edge |
| 7.2 | Which way does direction go |
| 7.3 | Is the weight a distance or a strength |
| 7.4 | Graphs with only two kinds, and overlapping edges |

## The chapter in one page

- Whether a relation stays an edge or gets promoted to a node is settled by three questions. Does it carry properties? Does it connect to a third thing? Do you search by that property? The last one decides it. Properties are read; nodes are found.
- Promote late, but do not put it off. The cost of moving rises in proportion to the data you have accumulated. And the slowest part of the move is not shifting data, it is unifying notation.
- Point the direction the way you ask most often. Put the meaning into the weight's name: not `weight` but `cost_minutes` or `affinity_score`.
- Projecting a bipartite graph loses information and squares the edge count. Multi-edges and self-loops are counted inconsistently, so decide what you are counting first.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| ISO/IEC 39075:2024 GQL | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| Cypher: patterns | [De facto] | [neo4j.com/docs/cypher-manual/current/patterns](https://neo4j.com/docs/cypher-manual/current/patterns/) |
| reification | [Standard] | [w3.org/TR/rdf12-schema](https://www.w3.org/TR/rdf12-schema/) |
| bipartite graph | [De facto] | [networkx.org/.../bipartite.html](https://networkx.org/documentation/stable/reference/algorithms/bipartite.html) |
| multigraph, self-loop | [De facto] | [networkx.org/.../multigraph.html](https://networkx.org/documentation/stable/reference/classes/multigraph.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch07/code/`](../../../content/ch07/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 2 - The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch07/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I drew contracts as an edge. `(Company)-[:CONTRACT]->(Company)`. It looked lovely on the whiteboard.

This chapter is about those judgment calls. Node or edge, which way the direction goes, what the weight actually means. On a whiteboard they all look about the same. Six months later they do not.

## Sections

| # | Title |
|---|---|
| 7.1 | Node or edge |
| 7.2 | Which way does direction go |
| 7.3 | Is the weight a distance or a strength |
| 7.4 | Graphs with only two kinds, and overlapping edges |

## The chapter in one page

- Whether a relation stays an edge or gets promoted to a node is settled by three questions. Does it carry properties? Does it connect to a third thing? Do you search by that property? The last one decides it. Properties are read; nodes are found.
- Promote late, but do not put it off. The cost of moving rises in proportion to the data you have accumulated. And the slowest part of the move is not shifting data, it is unifying notation.
- Point the direction the way you ask most often. Put the meaning into the weight's name: not `weight` but `cost_minutes` or `affinity_score`.
- Projecting a bipartite graph loses information and squares the edge count. Multi-edges and self-loops are counted inconsistently, so decide what you are counting first.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| ISO/IEC 39075:2024 GQL | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| Cypher: patterns | [De facto] | [neo4j.com/docs/cypher-manual/current/patterns](https://neo4j.com/docs/cypher-manual/current/patterns/) |
| reification | [Standard] | [w3.org/TR/rdf12-schema](https://www.w3.org/TR/rdf12-schema/) |
| bipartite graph | [De facto] | [networkx.org/.../bipartite.html](https://networkx.org/documentation/stable/reference/algorithms/bipartite.html) |
| multigraph, self-loop | [De facto] | [networkx.org/.../multigraph.html](https://networkx.org/documentation/stable/reference/classes/multigraph.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch07/code/`](../../../content/ch07/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch07/code
python3 ex1_node_or_edge.py   # leave it an edge, or promote it to a node
python3 ex2_direction.py      # which way to point it
python3 ex3_weights.py        # is the weight a distance or a strength
python3 ex4_bipartite.py      # bipartite graphs and projection blowup
python3 ex5_multigraph.py     # multi-edges and self-loops
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter was about *drawing* the graph. The next one looks at what that drawing actually is in memory and on disk. And why some graphs are fine at a million nodes while others die at a hundred thousand.

---

Previous: [Ch 6 It Took Ten Years to Get Back What We Dissolved into Vectors](../../ch06/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 8 What a Graph Actually Looks Like in Memory](../../ch08/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
