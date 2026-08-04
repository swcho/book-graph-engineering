# Chapter 19 - State Graphs, Reducers, and Supersteps

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch19/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I ran three nodes in parallel and only one log line came out.

This chapter is that story. What state is, what happens when several things edit it at once, and where the executor draws its boundaries.

## Sections

| # | Title |
|---|---|
| 19.1 | State is not everything, it is what changed |
| 19.2 | Supersteps: where the boundary gets drawn |
| 19.3 | The merge rule is domain knowledge |
| 19.4 | What do you put in state |
| 19.5 | Checkpoints are not only for recovery |

## The chapter in one page

- A node returns only what it changed, not the whole state. When several touch the same field, a reducer merges them. Without a reducer an update vanishes (if you are unlucky) or raises (if you are lucky).
- Nodes in the same superstep cannot see what the others wrote. They got the same copy. If you need ordering, put a node in between to create a boundary.
- A reducer has to be commutative. If `f(a,b) != f(b,a)` the answer depends on execution order, and you do not control that order. Put the basis for the decision inside the value: timestamp, source, confidence.
- State is stored whole on every superstep. Filter it by asking "does the next node read this" and it shrinks by tens of times. My line is 8 KB.
- Checkpoints get used far more for debugging than for recovery. Eight times more, in my logs. And write the code that enables them and the code that deletes them in the same commit.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| StateGraph | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| reducer | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| Pregel | [De facto] | [dl.acm.org/doi/10.1145/1807167.1807184](https://dl.acm.org/doi/10.1145/1807167.1807184) |
| Bulk Synchronous Parallel | [De facto] | [dl.acm.org/doi/10.1145/79173.79181](https://dl.acm.org/doi/10.1145/79173.79181) |
| persistence | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| lost update | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch19/code/`](../../../content/ch19/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch19/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I ran three nodes in parallel and only one log line came out.

This chapter is that story. What state is, what happens when several things edit it at once, and where the executor draws its boundaries.

## Sections

| # | Title |
|---|---|
| 19.1 | State is not everything, it is what changed |
| 19.2 | Supersteps: where the boundary gets drawn |
| 19.3 | The merge rule is domain knowledge |
| 19.4 | What do you put in state |
| 19.5 | Checkpoints are not only for recovery |

## The chapter in one page

- A node returns only what it changed, not the whole state. When several touch the same field, a reducer merges them. Without a reducer an update vanishes (if you are unlucky) or raises (if you are lucky).
- Nodes in the same superstep cannot see what the others wrote. They got the same copy. If you need ordering, put a node in between to create a boundary.
- A reducer has to be commutative. If `f(a,b) != f(b,a)` the answer depends on execution order, and you do not control that order. Put the basis for the decision inside the value: timestamp, source, confidence.
- State is stored whole on every superstep. Filter it by asking "does the next node read this" and it shrinks by tens of times. My line is 8 KB.
- Checkpoints get used far more for debugging than for recovery. Eight times more, in my logs. And write the code that enables them and the code that deletes them in the same commit.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| StateGraph | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| reducer | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| Pregel | [De facto] | [dl.acm.org/doi/10.1145/1807167.1807184](https://dl.acm.org/doi/10.1145/1807167.1807184) |
| Bulk Synchronous Parallel | [De facto] | [dl.acm.org/doi/10.1145/79173.79181](https://dl.acm.org/doi/10.1145/79173.79181) |
| persistence | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| lost update | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch19/code/`](../../../content/ch19/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch19/code
pip install "langgraph>=1.0,<2.0"
python3 ex1_lost_update.py      # without a reducer, updates disappear
python3 ex2_superstep.py        # superstep boundaries, made visible
python3 ex3_custom_reducer.py   # a different merge rule per field
python3 ex4_state_size.py       # no dependencies
python3 ex5_debug_state.py      # time travel with checkpoints
```

`ex1` deliberately includes a case that **raises**. That is the result of the example.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** we have covered state and boundaries. The next chapter is *when do you stop*. Chapter 1 mentioned that one termination condition prevents a large bill; this is how you design that condition properly.

---

Previous: [Ch 18 Where Does a Chain Break](../../ch18/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 20 How to End a Loop That Won't End](../../ch20/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
