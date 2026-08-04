# Chapter 28 — When the Agent Grows the Graph by Itself

`Part 5 — Where the Two Graphs Meet` | **English** | [한국어](../../../content/ch28/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I opened the graph and there were three people named Minsu Park.

Half of this chapter is about what *not* to do. Automatic expansion is attractive and the price is high. Better to know the price before you start.

## Sections

| # | Title |
|---|---|
| 28.1 | Write without validation and it is ruined in ten turns |
| 28.2 | Four gates in front of the write |
| 28.3 | Where did this fact come from |
| 28.4 | It grows in a direction nobody asked for |
| 28.5 | How far do you expand |

## The chapter in one page

- Once an agent starts writing to the graph, quality control becomes part of the system. Write without validation and ten turns ruins it.
- A graph can be wrong even when every fact you insert is correct, because a different name splits the node. Improving extraction accuracy does not fix that.
- There are four gates: confidence, normalization, schema, single-value conflict. Each catches something different, so one gate lets the rest leak. And normalization has to run before the duplicate check.
- Do not auto-overwrite on a single-value conflict. A wrong answer erases a right one. Keep both and send it to a human.
- Put provenance on every edge, and when you infer, record what you leaned on. You cannot reconstruct it later. An inference cannot be more trustworthy than the weakest thing it rests on.
- The graph grows in a direction nobody asked for. Constraints vanish by being *diluted*, not deleted. Humans adding 20% does not change the direction. Intervene on the *ratio*, not on individual facts.
- Expansion yields less and errs more the deeper it goes. Go shallow normally, deep occasionally, and put the deep results in a review queue.
- And the real danger of automatic expansion is not "wrong facts," it is "not knowing when to stop." Cap the node growth rate.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| knowledge graph completion | [Experimental] | [arxiv.org/abs/2002.00388](https://arxiv.org/abs/2002.00388) |
| provenance | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| retraction | [De facto] | [w3.org/TR/prov-o/#Invalidation](https://www.w3.org/TR/prov-o/#Invalidation) |
| truth maintenance | [Experimental] | [dl.acm.org/doi/10.1145/321978.321979](https://dl.acm.org/doi/10.1145/321978.321979) |
| schema drift | [De facto] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| self-training bias | [Experimental] | [arxiv.org/abs/2305.17493](https://arxiv.org/abs/2305.17493) |
| SHACL validation | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch28/code/`](../../../content/ch28/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch28/code
pip install kuzu

python3 ex1_write_loop.py         # what ten turns of writing without validation looks like
python3 ex2_write_gate.py         # four gates, each catching something different
python3 ex3_provenance.py         # what collapses when you retract a source
python3 ex4_drift.py              # distribution bias in a self-writing loop (no dependencies)
python3 ex5_expansion_budget.py   # how far to expand (no dependencies)
```

`ex4` fixes the seed at 3. Change it and the numbers move a few points, but the direction
(constraints shrink, events grow) does not.

The yield and accuracy figures in `ex5` are simplified from measurements in our domain. Measure
per-hop accuracy in yours and put your own numbers in.

<!-- 실행 가이드 끝 -->

---

**What comes together next chapter:** Chapter 27 read the graph and this one wrote to it. But we treated them *separately*. The next chapter joins them into one backbone. And once joined, it becomes clear that Part 6's problems were all the *same problem*.

---

Previous: [Ch 27 The Cheapest Way to Give an Agent Memory](../../ch27/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 29 One Backbone](../../ch29/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
