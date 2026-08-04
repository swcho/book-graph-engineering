# Chapter 30 - Nobody Knows What Changed, or When

`Part 6 - The Backbone: State Management Engine` | **English** | [한국어](../../../content/ch30/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "Was this always like this?"

Part 6 starts here. Part 5 joined the two graphs into one backbone, and once joined, the operational problems remain. And they all wear the same face: *questions you cannot answer from "the current state" alone*.

## Sections

| # | Title |
|---|---|
| 30.1 | Questions you cannot answer with current state alone |
| 30.2 | Events are the original, state is derived |
| 30.3 | Two ways to bring back the graph as it was |
| 30.4 | How you fold decides the answer |
| 30.5 | What a log needs to become an audit log |

## The chapter in one page

- With only current state you can answer "what is it now" and nothing else. Audits, incident investigations, quality metrics all require history.
- "Let us log things properly" does not work, because nothing happens when you skip a log line. You have to flip it: *not "we also record" but "the record is the write."*
- Events are the original and state is derived. A read view has to be rebuildable at any time, and you only know it is by actually deleting it and replaying.
- Put *what changed* in the event. Put "the whole state afterward" in it and you do not know what changed and cannot merge concurrent changes.
- Replay time is decided by snapshot interval, not data volume. Compute the interval backwards from your recovery time objective.
- Stacking events settles nothing on its own. *How you fold them* decides the actual behavior, and that is a domain decision. Default to "last write wins" and agents will overwrite humans.
- To be an audit log it has to be able to show that it was *not* altered. A hash chain does not prevent tampering, it makes tampering visible. Whether that is enough depends on what you are protecting.
- And do not put personal data directly in events. You end up putting what must be deleted somewhere you cannot delete.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| event sourcing | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |
| append-only log | [De facto] | [kafka.apache.org/documentation/#design](https://kafka.apache.org/documentation/#design) |
| replay | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |
| snapshot | [De facto] | [sqlite.org/wal.html](https://www.sqlite.org/wal.html) |
| write-ahead log | [De facto] | [postgresql.org/docs/current/wal-intro.html](https://www.postgresql.org/docs/current/wal-intro.html) |
| CQRS | [De facto] | [martinfowler.com/bliki/CQRS.html](https://martinfowler.com/bliki/CQRS.html) |
| hash chain | [Standard] | [datatracker.ietf.org/doc/html/rfc6962](https://datatracker.ietf.org/doc/html/rfc6962) |
| audit trail | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch30/code/`](../../../content/ch30/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 6 - The Backbone: State Management Engine` | **English** | [한국어](../../../content/ch30/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> "Was this always like this?"

Part 6 starts here. Part 5 joined the two graphs into one backbone, and once joined, the operational problems remain. And they all wear the same face: *questions you cannot answer from "the current state" alone*.

## Sections

| # | Title |
|---|---|
| 30.1 | Questions you cannot answer with current state alone |
| 30.2 | Events are the original, state is derived |
| 30.3 | Two ways to bring back the graph as it was |
| 30.4 | How you fold decides the answer |
| 30.5 | What a log needs to become an audit log |

## The chapter in one page

- With only current state you can answer "what is it now" and nothing else. Audits, incident investigations, quality metrics all require history.
- "Let us log things properly" does not work, because nothing happens when you skip a log line. You have to flip it: *not "we also record" but "the record is the write."*
- Events are the original and state is derived. A read view has to be rebuildable at any time, and you only know it is by actually deleting it and replaying.
- Put *what changed* in the event. Put "the whole state afterward" in it and you do not know what changed and cannot merge concurrent changes.
- Replay time is decided by snapshot interval, not data volume. Compute the interval backwards from your recovery time objective.
- Stacking events settles nothing on its own. *How you fold them* decides the actual behavior, and that is a domain decision. Default to "last write wins" and agents will overwrite humans.
- To be an audit log it has to be able to show that it was *not* altered. A hash chain does not prevent tampering, it makes tampering visible. Whether that is enough depends on what you are protecting.
- And do not put personal data directly in events. You end up putting what must be deleted somewhere you cannot delete.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| event sourcing | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |
| append-only log | [De facto] | [kafka.apache.org/documentation/#design](https://kafka.apache.org/documentation/#design) |
| replay | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |
| snapshot | [De facto] | [sqlite.org/wal.html](https://www.sqlite.org/wal.html) |
| write-ahead log | [De facto] | [postgresql.org/docs/current/wal-intro.html](https://www.postgresql.org/docs/current/wal-intro.html) |
| CQRS | [De facto] | [martinfowler.com/bliki/CQRS.html](https://martinfowler.com/bliki/CQRS.html) |
| hash chain | [Standard] | [datatracker.ietf.org/doc/html/rfc6962](https://datatracker.ietf.org/doc/html/rfc6962) |
| audit trail | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch30/code/`](../../../content/ch30/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch30/code
pip install kuzu

python3 ex1_no_history.py        # questions you cannot answer with current state alone
python3 ex2_replay_cost.py       # replay cost and snapshots (no dependencies)
python3 ex3_temporal_query.py    # two ways to bring back "the graph as it was"
python3 ex4_reducer_conflict.py  # the reducer decides the answer (no dependencies)
python3 ex5_audit_trail.py       # a hash chain makes tampering visible (no dependencies)
```

`ex2` times slightly differently on every run. On the first row (10,000) a ratio near or below 1
is normal, because no snapshot has been taken yet.

The lookup comparison in `ex3` is at toy scale, nine events. Do not conclude "replay is fast"
from that number.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter assumed changes arrive *in order*. Event 1, then event 2. But when two agents edit *at the same time*, there is no order. That is the next chapter.

---

Previous: [Ch 29 One Backbone](../../ch29/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 31 Two Agents Edited the Same Node at Once](../../ch31/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
