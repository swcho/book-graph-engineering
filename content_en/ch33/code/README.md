# Chapter 33 — Read the Query Plan and You See the Bill

`Part 7 — Operations` | **English** | [한국어](../../../content/ch33/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I spent three weeks tuning queries. Average latency went from 9 ms to 4 ms.

This chapter covers two things: how to read a query plan, and how to know what share of the bill that plan is responsible for. The second matters more.

## Sections

| # | Title |
|---|---|
| 33.1 | Three things to look for in a plan |
| 33.2 | When does an index not help |
| 33.3 | The slowest and the most painful are different |
| 33.4 | The big line on the bill is usually somewhere else |
| 33.5 | Where do you look first |

## The chapter in one page

- Three things to look for in a plan: is there a `CROSS_PRODUCT`, what is the `SCAN` scanning, and is the `FILTER` before or after.
- "Start from the smaller side" mostly does not matter on modern engines. The planner decides. Look at the plan before you agonize over ordering.
- To measure index effect you need enough scale. At a few thousand rows, parse time dominates and you see nothing.
- An index helps only if it matches how you look things up. And in a graph you do not need an index to follow relationships. Find the one starting node with an index and the rest is free.
- Do not insert one row at a time. Bulk load is tens of times faster. A good share of "graph databases are slow" conclusions come from here.
- "Slowest" and "most painful" are different. Rank by total time (latency per call times number of calls). A slow query log will not catch the most painful one.
- The big line on the bill is usually tokens. Making a query *faster* barely changes cost. Making a query *more accurate* cuts tokens a lot. Those are different jobs.
- And before any performance work, break the request into segments. If one segment is 95%, optimizing everything else gets you 3%. Amdahl's law is sixty years old and still applies exactly.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| query plan | [De facto] | [neo4j.com/…/execution-plans](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/) |
| EXPLAIN | [De facto] | [neo4j.com/…/planning-and-tuning](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| cartesian product | [Standard] | [postgresql.org/…/queries-table-expressions.html](https://www.postgresql.org/docs/current/queries-table-expressions.html) |
| index | [De facto] | [neo4j.com/docs/cypher-manual/current/indexes](https://neo4j.com/docs/cypher-manual/current/indexes/) |
| slow query log | [De facto] | [dev.mysql.com/doc/refman/8.0/en/slow-query-log.html](https://dev.mysql.com/doc/refman/8.0/en/slow-query-log.html) |
| Amdahl's law | [Standard] | [dl.acm.org/doi/10.1145/1465482.1465560](https://dl.acm.org/doi/10.1145/1465482.1465560) |
| bulk load | [De facto] | [neo4j.com/…/neo4j-admin-import](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch33/code/`](../../../content/ch33/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch33/code
pip install kuzu

python3 ex1_read_plan.py        # reading real EXPLAIN output
python3 ex2_index_effect.py     # when an index helps and when it does not
python3 ex3_cost_model.py       # monthly cost broken out by line (no dependencies)
python3 ex4_hot_query.py        # the slowest and the most painful (no dependencies)
python3 ex5_where_time_goes.py  # decomposing one request's time (no dependencies)
```

`ex1` and `ex2` take a few seconds to build data. They use `COPY` for bulk loading, which is far
faster than one row at a time. That is itself part of what Chapter 33 is about.

The result of `ex2` looks like "the index barely helps," and that is because the scale is small.
Raise `SIZES` into the millions and they separate. It just takes a while to run.

The numbers in `ex3` through `ex5` are an *example workload* simplified from measurements in the
author's environment. Put your system's values in and run it again. The structure is the point,
not the numbers.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter was *fast and cheap*. The next one is *please delete me*. What deleting something from a graph actually means, and why it is much harder than in a relational database.

---

Previous: [Ch 32 The Day You Change the Schema](../../ch32/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 34 What It Means to Erase Personal Data from a Graph](../../ch34/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
