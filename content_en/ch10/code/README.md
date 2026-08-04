# Chapter 10 - Which Node Actually Matters

`Part 2 - The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch10/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "Pull the most important person in our org out of the graph for me."

This chapter is about those "other measures." What question each of the four centralities answers, and why finding clusters gives you a different answer every time you run it.

## Sections

| # | Title |
|---|---|
| 10.1 | Four measures, four questions |
| 10.2 | PageRank and the score that leaks |
| 10.3 | Why betweenness is expensive |
| 10.4 | Finding clusters, and getting a different answer each time |

## The chapter in one page

- Centrality measures are different definitions of "important." Degree asks how many people you know, closeness how fast something spreads from you, betweenness whether things split apart without you, eigenvector whether your neighbors have power.
- The most valuable signal is not who is first, it is *the gap in rank between measures*. A node with low degree and high betweenness is a pressure point nobody knows about.
- PageRank lets sink nodes swallow score. The ranking does not change, so you notice late - but if you are using an absolute threshold, it quietly stops meaning anything.
- Betweenness is expensive. On a graph with real structure, a 5% sample still gets the top of the list right.
- There is no correct answer in community detection. Label propagation wobbles with the seed, and modularity glues small clusters together because of the resolution limit. Decide the number of clusters from what you need them for, not from the algorithm.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| centrality measures | [De facto] | [networkx.org/.../centrality.html](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) |
| Brandes' algorithm | [De facto] | [tandfonline.com/.../0022250X.2001.9990249](https://www.tandfonline.com/doi/abs/10.1080/0022250X.2001.9990249) |
| PageRank | [De facto] | [ilpubs.stanford.edu:8090/422](http://ilpubs.stanford.edu:8090/422/) |
| modularity | [De facto] | [arxiv.org/abs/cond-mat/0308217](https://arxiv.org/abs/cond-mat/0308217) |
| Louvain method | [De facto] | [arxiv.org/abs/0803.0476](https://arxiv.org/abs/0803.0476) |
| Leiden algorithm | [De facto] | [nature.com/articles/s41598-019-41695-z](https://www.nature.com/articles/s41598-019-41695-z) |
| resolution limit | [De facto] | [pnas.org/doi/10.1073/pnas.0605965104](https://www.pnas.org/doi/10.1073/pnas.0605965104) |
| label propagation | [De facto] | [arxiv.org/abs/0709.2938](https://arxiv.org/abs/0709.2938) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch10/code/`](../../../content/ch10/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 2 - The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch10/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "Pull the most important person in our org out of the graph for me."

This chapter is about those "other measures." What question each of the four centralities answers, and why finding clusters gives you a different answer every time you run it.

## Sections

| # | Title |
|---|---|
| 10.1 | Four measures, four questions |
| 10.2 | PageRank and the score that leaks |
| 10.3 | Why betweenness is expensive |
| 10.4 | Finding clusters, and getting a different answer each time |

## The chapter in one page

- Centrality measures are different definitions of "important." Degree asks how many people you know, closeness how fast something spreads from you, betweenness whether things split apart without you, eigenvector whether your neighbors have power.
- The most valuable signal is not who is first, it is *the gap in rank between measures*. A node with low degree and high betweenness is a pressure point nobody knows about.
- PageRank lets sink nodes swallow score. The ranking does not change, so you notice late - but if you are using an absolute threshold, it quietly stops meaning anything.
- Betweenness is expensive. On a graph with real structure, a 5% sample still gets the top of the list right.
- There is no correct answer in community detection. Label propagation wobbles with the seed, and modularity glues small clusters together because of the resolution limit. Decide the number of clusters from what you need them for, not from the algorithm.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| centrality measures | [De facto] | [networkx.org/.../centrality.html](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) |
| Brandes' algorithm | [De facto] | [tandfonline.com/.../0022250X.2001.9990249](https://www.tandfonline.com/doi/abs/10.1080/0022250X.2001.9990249) |
| PageRank | [De facto] | [ilpubs.stanford.edu:8090/422](http://ilpubs.stanford.edu:8090/422/) |
| modularity | [De facto] | [arxiv.org/abs/cond-mat/0308217](https://arxiv.org/abs/cond-mat/0308217) |
| Louvain method | [De facto] | [arxiv.org/abs/0803.0476](https://arxiv.org/abs/0803.0476) |
| Leiden algorithm | [De facto] | [nature.com/articles/s41598-019-41695-z](https://www.nature.com/articles/s41598-019-41695-z) |
| resolution limit | [De facto] | [pnas.org/doi/10.1073/pnas.0605965104](https://www.pnas.org/doi/10.1073/pnas.0605965104) |
| label propagation | [De facto] | [arxiv.org/abs/0709.2938](https://arxiv.org/abs/0709.2938) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch10/code/`](../../../content/ch10/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch10/code
python3 ex1_centralities.py       # four centralities, four different winners
python3 ex2_pagerank.py           # sink nodes swallow the score
python3 ex3_betweenness_cost.py   # what betweenness costs, and how to approximate it
python3 ex4_communities.py        # label propagation vs modularity
python3 ex5_resolution.py         # the resolution limit
```

`ex3` computes exactly up to 1,600 nodes, so it takes about 10 seconds.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this is the end of Part 2. So far we handled graphs in code. The next chapter handles them in a query language. The same question in three languages, and how the one that became an international standard in 2024 differs from all three.

---

Previous: [Ch 9 Counting Degrees of Separation Killed the Server](../../ch09/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 11 One Question, Three Languages](../../ch11/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
