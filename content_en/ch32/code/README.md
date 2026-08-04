# Chapter 32 — The Day You Change the Schema

`Part 6 — The Backbone: State Management Engine` | **English** | [한국어](../../../content/ch32/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> Changing one relationship name took six weeks.

Chapter 31 assumed the schema stays put. This chapter is when the field itself changes. And up front: half of this chapter is not "how do you change it" but *"when is it safe to delete the old one."* That part is much harder.

## Sections

| # | Title |
|---|---|
| 32.1 | What breaks and what does not |
| 32.2 | Make a window where both work |
| 32.3 | How do you know nobody uses it |
| 32.4 | Data drifts during the transition |
| 32.5 | Write the plan as code |

## The chapter in one page

- Additive changes do not break; changing or removing does. And the risk is not in the schema, it is in *how that schema is being read*.
- Count who reads it before you change it. Code search will not find dynamic queries. Chapter 29's `Reads` edge earns its keep right here.
- Change it in one step and something dies at deploy time. Make a window where old and new both work. Move reads first, writes later.
- Run backfills in chunks, record how far you got, and make them idempotent. Then run one more time after it finishes.
- Data drifts during the transition. There is no transition that does not. Do not try to prevent it, *count it*. Do not contract until the mismatch is zero.
- The contraction criterion is not "the last 30 days," it is *the longest batch period*. Quarterly means 92 days; year-end close means 365. Parse the cron expression and compute it.
- And the more rarely a job runs, the harder you should alert on its failures. A daily job you hear about tomorrow. A job that runs once every two years you hear about in two years.
- Write the migration plan as code, not as a document. So that you cannot proceed without meeting the conditions.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| expand and contract | [De facto] | [martinfowler.com/bliki/ParallelChange.html](https://martinfowler.com/bliki/ParallelChange.html) |
| zero-downtime deployment | [De facto] | [martinfowler.com/bliki/BlueGreenDeployment.html](https://martinfowler.com/bliki/BlueGreenDeployment.html) |
| dual write | [De facto] | [martinfowler.com/bliki/ParallelChange.html](https://martinfowler.com/bliki/ParallelChange.html) |
| backfill | [De facto] | [cloud.google.com/…/database-migration-concepts-principles-part-1](https://cloud.google.com/architecture/database-migration-concepts-principles-part-1) |
| schema evolution | [De facto] | [avro.apache.org/…/#schema-resolution](https://avro.apache.org/docs/current/specification/#schema-resolution) |
| SHACL | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| backward compatibility | [De facto] | [protobuf.dev/programming-guides/proto3/#updating](https://protobuf.dev/programming-guides/proto3/#updating) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch32/code/`](../../../content/ch32/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch32/code
pip install kuzu

python3 ex1_breaking_change.py    # what breaks, and who is reading it
python3 ex2_expand_contract.py    # the six steps of expand and contract
python3 ex3_when_to_contract.py   # how to confirm "nobody uses it" (no dependencies)
python3 ex4_dual_read.py          # four read strategies during transition (no dependencies)
python3 ex5_migration_plan.py     # the migration as something checkable (no dependencies)
```

`ex1` reuses the `Reads` edge built in Chapter 29. If you have not read that chapter, take it as
"a record of what each execution read."

`ex5` is deliberately stuck at the `dual-read` step. Set `STATE["불일치_건수"]` to 0 and it moves
on.

<!-- 실행 가이드 끝 -->

---

**What you meet in the next part:** if Part 6 was about *building* the backbone, Part 7 is about *operating* it. Where to look when it slows down, where the cost comes from, and what exactly to delete from a graph when somebody says "please delete me."

---

Previous: [Ch 31 Two Agents Edited the Same Node at Once](../../ch31/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 33 Read the Query Plan and You See the Bill](../../ch33/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
