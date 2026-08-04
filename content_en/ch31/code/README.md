# Chapter 31 — Two Agents Edited the Same Node at Once

`Part 6 — The Backbone: State Management Engine` | **English** | [한국어](../../../content/ch31/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "I definitely fixed that."

Chapter 30 assumed changes arrive *in order*. This chapter is what happens when that assumption breaks: two changes arriving at once have no order. And in a graph this is harder than in a relational database, because *what the unit of conflict even is* is unclear.

## Sections

| # | Title |
|---|---|
| 31.1 | Changes disappear without an error |
| 31.2 | Check right before you write |
| 31.3 | In a graph the unit of conflict is ambiguous |
| 31.4 | Detecting it is the easy half |

## The chapter in one page

- When two jobs do read, decide, write-the-whole-thing, changes disappear. Without an error. The log shows two successes.
- This happens often in agent systems for three reasons: thinking takes a long time, concurrency is the default, and it is easy to write code that rewrites everything.
- Transactions do not solve it. A model call ends up inside the transaction, and workflows stay alive across process boundaries.
- The fix is to check "has it changed" right before writing. A conflict arrives not as an error but as *zero rows updated*, so you have to look at `rowcount`.
- Optimistic and pessimistic split on the conflict rate. The crossover is somewhere around 15% to 30%, and *pulling the thinking out of the lock pushes the crossover to the right*.
- In a graph you have to decide the unit of conflict first. Node versions create false conflicts; edge versions lose single-value updates. Use "subject plus relation type" as the logical unit and put an idempotency check in front of it.
- Detecting conflicts is an engineering problem; resolving them is a domain problem. Each kind of field merges differently, and free text cannot be merged automatically at all.
- And measure the error rate of your automatic merges. If you do not, you see "less human work" and miss "quietly wrong."

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| lost update | [Standard] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |
| optimistic locking | [De facto] | [martinfowler.com/…/optimisticOfflineLock.html](https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html) |
| pessimistic locking | [De facto] | [martinfowler.com/…/pessimisticOfflineLock.html](https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html) |
| compare-and-swap | [Standard] | [en.cppreference.com/…/compare_exchange](https://en.cppreference.com/w/cpp/atomic/atomic/compare_exchange) |
| serializable | [Standard] | [postgresql.org/…/transaction-iso.html#XACT-SERIALIZABLE](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE) |
| CRDT | [Experimental] | [inria.hal.science/inria-00555588](https://inria.hal.science/inria-00555588) |
| deadlock | [Standard] | [postgresql.org/…/explicit-locking.html#LOCKING-DEADLOCKS](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS) |
| write skew | [Standard] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch31/code/`](../../../content/ch31/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch31/code
pip install kuzu

python3 ex1_lost_update.py       # racing with real threads (no dependencies)
python3 ex2_optimistic.py        # three approaches compared (no dependencies)
python3 ex3_lock_contention.py   # where optimistic and pessimistic swap places (no dependencies)
python3 ex4_conflict_shape.py    # where to put the unit of conflict in a graph
python3 ex5_merge_strategy.py    # what to do after you detect one (no dependencies)
```

`ex1` and `ex2` use real threads. Ordering shifts slightly between runs, but the result — one of
them disappears — does not. If it does not disappear, raise `delay` and run it again.

The figures in `ex3` (12 ms to decide, 2.2 ms to acquire the lock) are simplified from our
environment. The crossover moves with those values. Measure and substitute your own.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter assumed the schema stays put. It was about fighting over the same field. But what if the field itself changes? The next chapter is about changing the structure of a running system.

---

Previous: [Ch 30 Nobody Knows What Changed, or When](../../ch30/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 32 The Day You Change the Schema](../../ch32/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
