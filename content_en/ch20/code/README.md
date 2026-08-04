# Chapter 20 - How to End a Loop That Won't End

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch20/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I had a cap on every layer and it still went around 240 times.

This chapter is that story. What you stop on, where you put the stop, and why one condition is not enough.

## Sections

| # | Title |
|---|---|
| 20.1 | Four conditions, each catching something different |
| 20.2 | What do you measure progress with |
| 20.3 | Split the budget or the back end starves |
| 20.4 | A loop with all four attached |
| 20.5 | Nobody does the multiplication |

## The chapter in one page

- There are four termination conditions: count, budget, time, and no-progress. Use only one and the cases the other three catch stay open.
- A progress measure must not be something the model can raise on its own. Length and confidence are both things a model will happily inflate. Use a value counted by rules.
- Do not ask the model "are you done?" Ask only "what is left," and let code decide whether it is done. Then the remaining list doubles as your progress measure.
- Split the budget or the later steps starve. And the later steps are usually the ones protecting quality. Set aside their minimum first.
- Caps per layer still multiply. Add one global budget and let every layer see it. And keep that budget in *state*, not in a global variable, or it resets on resume.
- Record why it ended. "Hit the cap" and "stalled" call for different responses.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| termination condition | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| recursion limit | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| evaluator-optimizer | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| usage tracking | [De facto] | [docs.claude.com/.../token-counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |
| early stopping | [De facto] | [deeplearningbook.org/contents/regularization.html](https://www.deeplearningbook.org/contents/regularization.html) |
| circuit breaker | [De facto] | [martinfowler.com/bliki/CircuitBreaker.html](https://martinfowler.com/bliki/CircuitBreaker.html) |
| rate limiting | [De facto] | [datatracker.ietf.org/doc/html/rfc6585](https://datatracker.ietf.org/doc/html/rfc6585) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch20/code/`](../../../content/ch20/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch20/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I had a cap on every layer and it still went around 240 times.

This chapter is that story. What you stop on, where you put the stop, and why one condition is not enough.

## Sections

| # | Title |
|---|---|
| 20.1 | Four conditions, each catching something different |
| 20.2 | What do you measure progress with |
| 20.3 | Split the budget or the back end starves |
| 20.4 | A loop with all four attached |
| 20.5 | Nobody does the multiplication |

## The chapter in one page

- There are four termination conditions: count, budget, time, and no-progress. Use only one and the cases the other three catch stay open.
- A progress measure must not be something the model can raise on its own. Length and confidence are both things a model will happily inflate. Use a value counted by rules.
- Do not ask the model "are you done?" Ask only "what is left," and let code decide whether it is done. Then the remaining list doubles as your progress measure.
- Split the budget or the later steps starve. And the later steps are usually the ones protecting quality. Set aside their minimum first.
- Caps per layer still multiply. Add one global budget and let every layer see it. And keep that budget in *state*, not in a global variable, or it resets on resume.
- Record why it ended. "Hit the cap" and "stalled" call for different responses.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| termination condition | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| recursion limit | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| evaluator-optimizer | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| usage tracking | [De facto] | [docs.claude.com/.../token-counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |
| early stopping | [De facto] | [deeplearningbook.org/contents/regularization.html](https://www.deeplearningbook.org/contents/regularization.html) |
| circuit breaker | [De facto] | [martinfowler.com/bliki/CircuitBreaker.html](https://martinfowler.com/bliki/CircuitBreaker.html) |
| rate limiting | [De facto] | [datatracker.ietf.org/doc/html/rfc6585](https://datatracker.ietf.org/doc/html/rfc6585) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch20/code/`](../../../content/ch20/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch20/code
python3 ex1_four_guards.py        # no dependencies
python3 ex2_stall_detection.py    # no dependencies
python3 ex3_budget_split.py       # no dependencies
pip install "langgraph>=1.0,<2.0"
python3 ex4_generator_critic.py   # a loop with all four conditions attached
python3 ex5_nested_loops.py       # no dependencies
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter assumed the budget carries across a resume. For that, state has to survive the process dying. That is the next chapter.

---

Previous: [Ch 19 State Graphs, Reducers, and Supersteps](../../ch19/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 21 The Process Dies, the Work Must Not](../../ch21/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
