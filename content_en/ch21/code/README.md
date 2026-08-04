# Chapter 21 — The Process Dies, the Work Must Not

`Part 4 — Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch21/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> A four-hour batch job died at three hours fifty-one minutes.

Chapter 20 assumed the budget carries across a resume, which requires state to survive death. This chapter is that. Except storing state is not the end of it — between the point you saved and the point you died, things *already happened*.

## Sections

| # | Title |
|---|---|
| 21.1 | Checkpoints only land on boundaries |
| 21.2 | Which is why you need idempotency |
| 21.3 | When the other side will not take an idempotency key |
| 21.4 | Durability is not free |
| 21.5 | What do you store it on |
| 21.6 | You do not know it recovers until you kill it |

## The chapter in one page

- Checkpoints land only on superstep boundaries. Whatever happened between the boundary and the crash gets redone on resume.
- Splitting nodes finer narrows that window but never closes it, and the extra checkpoints slow you down. Measured, SQLite ran 2.0x to 2.8x the in-memory checkpointer, and past 32 KB it reached 4.8x.
- Instead of closing the window, make the work *safe to redo*. That is idempotency. The key has to come from the *work*, not the request, and you have to confirm in writing that the other API actually supports it.
- If it does not, use a side-effect log. The window is still there. Classify what is left as "unknown" and let a human close it out. Do not try to eliminate it; narrow it and hand it over.
- An in-memory checkpointer is a cache, not a checkpointer. It works perfectly in development and dies on the day you deploy.
- And you do not know it recovers until you kill it. One `kill -9` costs five minutes.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| checkpointer | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| durable execution | [De facto] | [docs.temporal.io/evaluate/understanding-temporal](https://docs.temporal.io/evaluate/understanding-temporal) |
| idempotency | [Standard] | [datatracker.ietf.org/doc/html/rfc9110#section-9.2.2](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2) |
| idempotency key | [De facto] | [datatracker.ietf.org/…/draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header) |
| exactly-once | [De facto] | [kafka.apache.org/documentation/#semantics](https://kafka.apache.org/documentation/#semantics) |
| thread id | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| write-ahead log | [De facto] | [sqlite.org/wal.html](https://www.sqlite.org/wal.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch21/code/`](../../../content/ch21/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch21/code
pip install "langgraph>=1.0,<2.0" "langgraph-checkpoint-sqlite<3"

bash run_crash_demo.sh          # actually kills the process, then resumes
python3 ex2_idempotency.py      # no dependencies
python3 ex3_side_effect_log.py  # no dependencies
python3 ex4_checkpointer_cost.py # measured latency per checkpointer
python3 ex5_recovery_drill.py   # no dependencies
```

Use `langgraph-checkpoint-sqlite` **below 3**. The 3.x line pulls in `langgraph-checkpoint` 4.x,
whose serialization layer does not match langgraph 1.0.1 as checked, and the import fails.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter assumed you can just redo it. Some things you cannot: mail already sent, files already deleted. Then instead of undoing, you have to *pay it back*. The next chapter is compensating transactions.

---

Previous: [Ch 20 How to End a Loop That Won't End](../../ch20/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 22 How to Pay Back What You Can't Undo](../../ch22/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
