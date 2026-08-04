# Chapter 18 — Where Does a Chain Break

`Part 4 — Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch18/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I sent "please try again" to a user who had waited 51 seconds.

This is the start of Part 4, and from here on it is about what the model *does*. The first question: where does a pipeline strung together in one line break?

## Sections

| # | Title |
|---|---|
| 18.1 | What do you throw away when it fails |
| 18.2 | Once you pass five if statements |
| 18.3 | It ran in parallel and only one branch failed |
| 18.4 | The same job, two structures |
| 18.5 | When do you switch |

## The chapter in one page

- The difference between a chain and a state graph is *what you throw away on failure*. A chain throws away the earlier results; a graph redoes only the step that failed. The more often the later steps fail, and the more steps there are, the wider the gap.
- As conditions accumulate, the number of `if` cases grows exponentially and the graph's edges grow linearly. Around five, a human stops being able to see them all.
- When one parallel task fails you have three choices, and a chain has nowhere to express that decision. The join node is what carries it.
- That does not mean starting with a graph. With two or three steps and rare failures, a chain is cheaper. Just be ready to switch: separate steps into functions and standardize the data as a dict, and the switch is half a day later.
- And changing the structure does not lower the failure rate. It lowers the *cost* of failure. Explain that distinction to your team first.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| StateGraph | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| checkpointer | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| prompt chaining | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| cyclomatic complexity | [Standard] | [ieeexplore.ieee.org/document/1702388](https://ieeexplore.ieee.org/document/1702388) |
| durable execution | [De facto] | [docs.temporal.io/temporal](https://docs.temporal.io/temporal) |
| ReAct | [De facto] | [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch18/code/`](../../../content/ch18/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch18/code
python3 ex1_chain_vs_graph.py       # no dependencies
python3 ex2_if_explosion.py         # no dependencies
python3 ex3_partial_failure.py      # no dependencies
pip install "langgraph>=1.0,<2.0"
python3 ex4_same_task_two_ways.py   # the same job, two structures
python3 ex5_when_to_switch.py       # no dependencies
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter kept saying "state graph" without ever defining what state is. The next one does, starting with what happens when two nodes edit the same state at once.

---

Previous: [Ch 17 Questions Vectors Alone Can't Answer](../../ch17/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 19 State Graphs, Reducers, and Supersteps](../../ch19/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
