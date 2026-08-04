# Chapter 8 — What a Graph Actually Looks Like in Memory

`Part 2 — The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch08/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I loaded the same graph into two libraries. One took 4.1 GB. The other took 380 MB.

This chapter is about the container. Why some graphs are fine at a million nodes while others die at a hundred thousand — the answer is here, and it is usually not "node count."

## Sections

| # | Title |
|---|---|
| 8.1 | Three containers |
| 8.2 | Why contiguous is fast |
| 8.3 | Why a million is fine and a hundred thousand dies |
| 8.4 | Index-free adjacency |

## The chapter in one page

- There are three containers. An adjacency matrix is the square of the node count, so it is only usable below a few thousand. An adjacency list is convenient. CSR is the densest, two integer arrays. The same graph can come out at 4.1 GB or 380 MB.
- CSR is fast because of how memory is read, not because of the algorithm. When neighbors sit contiguously, one cache line brings several of them along.
- Node count explains very little about performance. The sum of squared degrees explains it. Two graphs with the same average degree can differ 200x on two-hop cost.
- Index-free adjacency pays off from the second hop onward. You still need an index to find the starting node.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| CSR, Compressed Sparse Row | [De facto] | [docs.scipy.org/…/scipy.sparse.csr_matrix.html](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.html) |
| index-free adjacency | [De facto] | [neo4j.com/…/graphdb-concepts](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/) |
| adjacency matrix / list | [De facto] | [networkx.org/…/convert.html](https://networkx.org/documentation/stable/reference/convert.html) |
| super node | [De facto] | [neo4j.com/…/planning-and-tuning](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| graph reordering | [Experimental] | [arxiv.org/abs/1602.08820](https://arxiv.org/abs/1602.08820) |
| locality of reference | [De facto] | [kernel.org/doc/html/latest/admin-guide/mm/index.html](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch08/code/`](../../../content/ch08/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch08/code
python3 graphgen.py        # sample graph statistics
python3 ex1_three_forms.py # memory: adjacency matrix vs adjacency list vs CSR
python3 ex2_csr_walk.py    # BFS over CSR
python3 ex3_degree_skew.py # same average, 200x the cost
python3 ex4_relabel.py     # renumbering improves locality
python3 ex5_index_free.py  # index-free adjacency
```

Absolute timings differ per machine. Read the **ratios** only.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** now that you know how a graph sits in memory, we walk on it. The next chapter is traversal and shortest paths, and it opens with how counting degrees of separation killed a server.

---

Previous: [Ch 7 One Node Drawn Wrong Cost Me Three Weeks](../../ch07/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 9 Counting Degrees of Separation Killed the Server](../../ch09/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
