# Chapter 22 — How to Pay Back What You Can't Undo

`Part 4 — Agent Graph Engineering (Track 2)` | **English** | [한국어](../../../content/ch22/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> The outage lasted three minutes. Recovery took forty.

Chapter 21 assumed you can just redo it. This chapter looks at the two places that assumption betrays you: when redoing makes the problem worse, and when you cannot redo at all.

## Sections

| # | Title |
|---|---|
| 22.1 | Everyone fails together, so everyone retries together |
| 22.2 | A timeout is a budget, not a layer |
| 22.3 | If you cannot undo it, pay it back |
| 22.4 | When the payback fails |
| 22.5 | You need somewhere to pile things up |

## The chapter in one page

- Retries are fine until everyone does them at once, which amplifies the outage. Exponential backoff alone does not flatten the spike. What scatters "all at once" is jitter.
- The moment an outage ends is the most dangerous. In the circuit breaker's half-open state, send *one* scout.
- If the sum of your per-layer timeouts exceeds the outer timeout, that configuration is lying. Treat it as a budget, not layers, and set aside the minimum the later steps need.
- Anything that left the building cannot be rolled back. Pair each step with its payback action and run them in reverse. Push irreversible steps as late as you can. Reordering alone removes the risk, with no code change.
- When the payback fails, write it to a queue. That is inside your own database, so it stops there. It does not recurse forever.
- A dead letter queue has to be replayable from the entry alone. Always include the idempotency key. And reduce alerts rather than adding them. An alert nobody reads does not exist.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| exponential backoff | [De facto] | [aws.amazon.com/…/timeouts-retries-and-backoff-with-jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| jitter | [De facto] | [aws.amazon.com/…/timeouts-retries-and-backoff-with-jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| retry storm | [De facto] | [sre.google/sre-book/handling-overload](https://sre.google/sre-book/handling-overload/) |
| circuit breaker | [De facto] | [martinfowler.com/bliki/CircuitBreaker.html](https://martinfowler.com/bliki/CircuitBreaker.html) |
| saga | [De facto] | [cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) |
| compensating transaction | [De facto] | [learn.microsoft.com/…/compensating-transaction](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) |
| dead letter queue | [De facto] | [docs.aws.amazon.com/…/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) |
| Retry-After | [Standard] | [datatracker.ietf.org/…/rfc9110#field.retry-after](https://datatracker.ietf.org/doc/html/rfc9110#field.retry-after) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch22/code/`](../../../content/ch22/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. No external dependencies.

```bash
cd content/ch22/code
python3 ex1_backoff.py          # load spike per retry strategy
python3 ex2_timeout_budget.py   # per-layer timeouts and budget allocation
python3 ex3_saga.py             # compensating transactions and step order
python3 ex4_undo_fails.py       # when the payback itself fails
python3 ex5_dlq.py              # dead letter queue and cause classification
```

`ex1` uses randomness with the seed fixed at 42. Change the seed and the numbers shift a little,
but the ranking of the three strategies does not.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter kept saying "hand it to a human" without defining how. Not a Slack ping. The next chapter puts the human into the graph as a *node*.

---

Previous: [Ch 21 The Process Dies, the Work Must Not](../../ch21/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 23 Where the Human Steps In](../../ch23/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
