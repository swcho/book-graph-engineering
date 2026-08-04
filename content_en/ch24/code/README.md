# Chapter 24 - Your Context Is Full

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch24/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> A month's bill came in at 6.4x what I expected.

One thing first. At the end of Chapter 23 I said to store the whole content of the moment you asked. That is right, and if you only ever stack it up you get this chapter's problem. Two requirements collide head-on: *keep it and you can investigate, throw it away and it keeps running.* This chapter is the search for the line between them.

## Sections

| # | Title |
|---|---|
| 24.1 | What grows linearly and what grows quadratically |
| 24.2 | Four ways to cut, and what each one loses |
| 24.3 | What a summary discards first |
| 24.4 | Put references in state, not bodies |
| 24.5 | Splitting memory into tiers |

## The chapter in one page

- Conversation length grows linearly and cumulative cost grows quadratically, because you resend the whole thing every turn. Money becomes the problem long before the window fills.
- When you pick a reduction method, do not look only at the savings rate. Measure "what percentage of facts that get referenced later survive," or you measured half the problem.
- Decide what to discard by *how often it is used*, not by importance. Importance is taste, and important things are already in recent context. One exception: keep constraints the user stated, regardless of use count.
- Summaries discard reasons and constraints first. Keep the decision without the reason and the agent reverses it; drop the constraint and it retries the forbidden thing. Pin the categories to preserve in the prompt, and never summarize a summary.
- Put references in state, not bodies. Context shrinks and checkpoints get cheaper. Two problems that turn out to be the same problem.
- Split memory into tiers and scan from the top. Not making an expensive lookup beats making a fast one. But a stale upper tier makes you fast and wrong, so give each tier an expiry.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| context window | [De facto] | [docs.claude.com/.../context-windows](https://docs.claude.com/en/docs/build-with-claude/context-windows) |
| context engineering | [Experimental] | [anthropic.com/.../effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| compaction | [Experimental] | [anthropic.com/.../effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| offloading | [Experimental] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| prompt caching | [De facto] | [docs.claude.com/.../prompt-caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) |
| long-term memory store | [De facto] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| token counting | [De facto] | [docs.claude.com/.../token-counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch24/code/`](../../../content/ch24/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 4 - Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch24/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> A month's bill came in at 6.4x what I expected.

One thing first. At the end of Chapter 23 I said to store the whole content of the moment you asked. That is right, and if you only ever stack it up you get this chapter's problem. Two requirements collide head-on: *keep it and you can investigate, throw it away and it keeps running.* This chapter is the search for the line between them.

## Sections

| # | Title |
|---|---|
| 24.1 | What grows linearly and what grows quadratically |
| 24.2 | Four ways to cut, and what each one loses |
| 24.3 | What a summary discards first |
| 24.4 | Put references in state, not bodies |
| 24.5 | Splitting memory into tiers |

## The chapter in one page

- Conversation length grows linearly and cumulative cost grows quadratically, because you resend the whole thing every turn. Money becomes the problem long before the window fills.
- When you pick a reduction method, do not look only at the savings rate. Measure "what percentage of facts that get referenced later survive," or you measured half the problem.
- Decide what to discard by *how often it is used*, not by importance. Importance is taste, and important things are already in recent context. One exception: keep constraints the user stated, regardless of use count.
- Summaries discard reasons and constraints first. Keep the decision without the reason and the agent reverses it; drop the constraint and it retries the forbidden thing. Pin the categories to preserve in the prompt, and never summarize a summary.
- Put references in state, not bodies. Context shrinks and checkpoints get cheaper. Two problems that turn out to be the same problem.
- Split memory into tiers and scan from the top. Not making an expensive lookup beats making a fast one. But a stale upper tier makes you fast and wrong, so give each tier an expiry.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| context window | [De facto] | [docs.claude.com/.../context-windows](https://docs.claude.com/en/docs/build-with-claude/context-windows) |
| context engineering | [Experimental] | [anthropic.com/.../effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| compaction | [Experimental] | [anthropic.com/.../effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| offloading | [Experimental] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| prompt caching | [De facto] | [docs.claude.com/.../prompt-caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) |
| long-term memory store | [De facto] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| token counting | [De facto] | [docs.claude.com/.../token-counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch24/code/`](../../../content/ch24/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. No external dependencies.

```bash
cd content/ch24/code
python3 ex1_growth.py          # cumulative tokens growing quadratically as turns pile up
python3 ex2_strategies.py      # four reduction methods: token savings and fact retention
python3 ex3_summary_drift.py   # what disappears first when you summarize repeatedly
python3 ex4_offload.py         # putting references in state instead of bodies
python3 ex5_memory_tiers.py    # lookup cost per memory tier
```

The unit prices in `ex1` are an example based on published price lists as checked. Get current
figures from each vendor's pricing page.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter handled one agent's context. Add more agents and the context splits automatically. Does the problem disappear? The next chapter shows that it does not disappear, it *moves* into the communication between agents.

---

Previous: [Ch 23 Where the Human Steps In](../../ch23/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 25 Six Topologies, and the Sockets You Plug Tools Into](../../ch25/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
