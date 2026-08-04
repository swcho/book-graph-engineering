# Chapter 34 - What It Means to Erase Personal Data from a Graph

`Part 7 - Operations` | **English** | [한국어](../../../content/ch34/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> Three weeks after I answered "it is deleted," they got in touch again.

One thing first. This chapter is *not legal advice.* How far you must delete is decided by jurisdiction and industry, and that is legal's call. The engineer's job is to count, in advance, what breaks when you pick a given level.

## Sections

| # | Title |
|---|---|
| 34.1 | What is left after you delete the node |
| 34.2 | "Delete" is not one thing |
| 34.3 | Remove the name and they are still identified |
| 34.4 | What collapses along with it |
| 34.5 | Making the procedure checkable |

## The chapter in one page

- Five places survive deleting a node: incoming edges, names inside free text, the event log, backups, and the search index.
- "Delete" is not one thing. Hide, sever the identifier, pseudonymize, erase completely. None of them satisfies every criterion. Complete erasure looks strongest and satisfies the fewest criteria.
- Removing the name does not stop identification. Combine four attributes and 66% become unique. And there is a cliff between three and four.
- In a graph, *the relationships themselves are an identifier*. Strip every attribute and a unique neighborhood shape still identifies. There is no proper solution to this yet.
- Count the blast radius before deleting, but "delete everything connected" is not the answer. Aggregates and decisions are not personal data, and you must not break someone else's history.
- The boundary is whether it points at an individual. Keep the document and change only who wrote it.
- Build a policy table per node type, and stop when a type shows up with no policy. Telling you that you do not know is what that table is worth.
- You cannot delete the event log, so do not put personal data in it directly. Put only an identifier, and delete from the table that identifier points to.
- And define "done" in writing. The deletion itself takes seconds; the whole thing takes days.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| right to erasure | [Standard] | [gdpr-info.eu/art-17-gdpr](https://gdpr-info.eu/art-17-gdpr/) |
| pseudonymisation | [Standard] | [gdpr-info.eu/art-4-gdpr](https://gdpr-info.eu/art-4-gdpr/) |
| re-identification | [De facto] | [nist.gov/.../de-identification-personal-information](https://www.nist.gov/publications/de-identification-personal-information) |
| k-anonymity | [De facto] | [dataprivacylab.org/.../kanonymity.pdf](https://dataprivacylab.org/dataprivacy/projects/kanonymity/kanonymity.pdf) |
| differential privacy | [De facto] | [microsoft.com/.../differential-privacy](https://www.microsoft.com/en-us/research/publication/differential-privacy/) |
| data minimisation | [Standard] | [gdpr-info.eu/art-5-gdpr](https://gdpr-info.eu/art-5-gdpr/) |
| retention period | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch34/code/`](../../../content/ch34/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 7 - Operations` | **English** | [한국어](../../../content/ch34/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> Three weeks after I answered "it is deleted," they got in touch again.

One thing first. This chapter is *not legal advice.* How far you must delete is decided by jurisdiction and industry, and that is legal's call. The engineer's job is to count, in advance, what breaks when you pick a given level.

## Sections

| # | Title |
|---|---|
| 34.1 | What is left after you delete the node |
| 34.2 | "Delete" is not one thing |
| 34.3 | Remove the name and they are still identified |
| 34.4 | What collapses along with it |
| 34.5 | Making the procedure checkable |

## The chapter in one page

- Five places survive deleting a node: incoming edges, names inside free text, the event log, backups, and the search index.
- "Delete" is not one thing. Hide, sever the identifier, pseudonymize, erase completely. None of them satisfies every criterion. Complete erasure looks strongest and satisfies the fewest criteria.
- Removing the name does not stop identification. Combine four attributes and 66% become unique. And there is a cliff between three and four.
- In a graph, *the relationships themselves are an identifier*. Strip every attribute and a unique neighborhood shape still identifies. There is no proper solution to this yet.
- Count the blast radius before deleting, but "delete everything connected" is not the answer. Aggregates and decisions are not personal data, and you must not break someone else's history.
- The boundary is whether it points at an individual. Keep the document and change only who wrote it.
- Build a policy table per node type, and stop when a type shows up with no policy. Telling you that you do not know is what that table is worth.
- You cannot delete the event log, so do not put personal data in it directly. Put only an identifier, and delete from the table that identifier points to.
- And define "done" in writing. The deletion itself takes seconds; the whole thing takes days.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| right to erasure | [Standard] | [gdpr-info.eu/art-17-gdpr](https://gdpr-info.eu/art-17-gdpr/) |
| pseudonymisation | [Standard] | [gdpr-info.eu/art-4-gdpr](https://gdpr-info.eu/art-4-gdpr/) |
| re-identification | [De facto] | [nist.gov/.../de-identification-personal-information](https://www.nist.gov/publications/de-identification-personal-information) |
| k-anonymity | [De facto] | [dataprivacylab.org/.../kanonymity.pdf](https://dataprivacylab.org/dataprivacy/projects/kanonymity/kanonymity.pdf) |
| differential privacy | [De facto] | [microsoft.com/.../differential-privacy](https://www.microsoft.com/en-us/research/publication/differential-privacy/) |
| data minimisation | [Standard] | [gdpr-info.eu/art-5-gdpr](https://gdpr-info.eu/art-5-gdpr/) |
| retention period | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch34/code/`](../../../content/ch34/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch34/code
pip install kuzu

python3 ex1_delete_scope.py     # what is left if you delete only the node
python3 ex2_delete_levels.py    # the four levels of "delete" (no dependencies)
python3 ex3_reidentify.py       # removing the name does not stop identification (no dependencies)
python3 ex4_cascade.py          # what collapses along with it
python3 ex5_deletion_plan.py    # the deletion procedure as something checkable (no dependencies)
```

The examples in this chapter show *structure*; they are not legal advice. Which level you must
delete to depends on jurisdiction and industry, and legal decides that. The engineer's job is to
count in advance what breaks at each level.

`ex5` is deliberately stuck on the `Photo` type. Add one line to `POLICY` and it passes.

<!-- 실행 가이드 끝 -->

---

**What you meet in the next part:** that was everything you can do today. The last part is about *what comes next*. And in that chapter I point at the five claims in this book most likely to be wrong in three years.

---

Previous: [Ch 33 Read the Query Plan and You See the Bill](../../ch33/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 35 Five Claims Most Likely to Be Wrong in Three Years](../../ch35/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
