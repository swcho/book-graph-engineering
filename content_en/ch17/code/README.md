# Chapter 17 — Questions Vectors Alone Can't Answer

`Part 3 — Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch17/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I attached GraphRAG and user satisfaction went down.

The weighted average went from 0.833 to 0.862, a 3% gain. For that 3% the index cost rose, latency gained 340 ms, and I had to build a new update pipeline. This chapter is about doing that arithmetic first.

## Sections

| # | Title |
|---|---|
| 17.1 | The question distribution flips the conclusion |
| 17.2 | A wrong router produces a plausible wrong answer |
| 17.3 | The real cost is updating, not indexing |
| 17.4 | Four approaches, viewed as update cost |

## The chapter in one page

- Count your questions before you pick a tool. Multiply the same benchmark table by a different distribution and the conclusion reverses. A hundred entries from your query log answers this in half a day.
- Attaching a graph makes plain fact lookup slightly worse. About 0.02. But fact lookup is frequent, so it is felt. Multiply the metric change by the frequency.
- When the router is wrong you do not get an empty answer, you get a plausible wrong one. Filter with rules first, send only the ambiguous ones to a model, and cache the result so the same question lands in the same place.
- The real cost is updating, not indexing. The share of affected communities decides everything, and you only learn it by measuring. I expected 5%; the measurement said 34%.
- Plans to bolt on incremental updates later usually do not happen. Design it first, then build the full index.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Microsoft GraphRAG | [De facto] | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |
| LightRAG | [Experimental] | [arxiv.org/abs/2410.05779](https://arxiv.org/abs/2410.05779) |
| HippoRAG | [Experimental] | [arxiv.org/abs/2405.14831](https://arxiv.org/abs/2405.14831) |
| Graphiti | [Experimental] | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) |
| reciprocal rank fusion | [De facto] | [dl.acm.org/doi/10.1145/1571941.1572114](https://dl.acm.org/doi/10.1145/1571941.1572114) |
| RAG | [De facto] | [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) |
| hybrid search | [De facto] | [elastic.co/what-is/hybrid-search](https://www.elastic.co/what-is/hybrid-search) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch17/code/`](../../../content/ch17/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch17/code
python3 ex1_routing.py            # routing by question type, and mis-routing
python3 ex2_incremental_cost.py   # GraphRAG's real cost is the update
python3 ex3_compare_approaches.py # four approaches viewed as update cost
python3 ex4_hybrid_fusion.py      # rank fusion, and when it loses
python3 ex5_eval_harness.py       # the question distribution flips the conclusion
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** Part 3 ends here. So far it was "what the model knows." Part 4 is "what the model does." And the first chapter looks at where a chain breaks.

---

Previous: [Ch 16 True Yesterday, Wrong Today](../../ch16/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 18 Where Does a Chain Break](../../ch18/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
