# Chapter 16 — True Yesterday, Wrong Today

`Part 3 — Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch16/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> Audit asked me to reproduce the contract status report as of June 30.

I could not do it. Our system only had "what we know now"; "what we knew on June 30" was nowhere. This chapter is how to hold both.

## Sections

| # | Title |
|---|---|
| 16.1 | There is more than one time axis |
| 16.2 | Expiry and correction are different |
| 16.3 | Store a date as a string and it goes quietly wrong |
| 16.4 | Attach time and a relation becomes an event |
| 16.5 | So how much bigger does it get |

## The chapter in one page

- There are two time axes. Valid time is the period something was true in the world; transaction time is the period we believed it. "Who owned this in March" and "who did we think owned it in March" are different questions.
- Expiry and correction are different. Expiry means it was right then; correction means it was wrong then too. Mix them and past reports change retroactively. Ask on the input screen.
- Compare dates as strings and it goes quietly wrong. No exception, just reversed ordering. Parse at load time and raise parse failure to blocking severity.
- Attach time and a relation becomes an event. Any relation that will carry time is cheaper as an event node from the start than promoted later.
- Make everything bitemporal and it grows 139x. Pick by asking "could somebody complain about this value later" and it drops to 12x. And you cannot manufacture the past retroactively, so decide before you need it.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| bitemporal | [De facto] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |
| valid time | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |
| transaction time | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |
| Graphiti / Zep | [Experimental] | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) |
| ISO 8601 | [Standard] | [iso.org/iso-8601-date-and-time-format.html](https://www.iso.org/iso-8601-date-and-time-format.html) |
| OWL-Time | [Standard] | [w3.org/TR/owl-time](https://www.w3.org/TR/owl-time/) |
| slowly changing dimension | [De facto] | [kimballgroup.com/…/dimensional-modeling-techniques](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch16/code/`](../../../content/ch16/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch16/code
python3 ex1_two_axes.py       # no dependencies
python3 ex2_correction.py     # no dependencies
python3 ex3_string_dates.py   # no dependencies
pip install kuzu "rdflib>=7,<8"
python3 ex4_temporal_query.py # point-in-time queries in Cypher and SPARQL
python3 ex5_storage_cost.py   # no dependencies
```

| File | What it shows |
|---|---|
| `bitemporal.py` | A bitemporal store in 100 lines |
| `ex1` | Four point-in-time questions against the same store |
| `ex2` | Mixing expiry and correction breaks reproducing the past |
| `ex3` | Comparing dates as strings gets 5 of 6 wrong |
| `ex4` | LPG uses edge properties; RDF uses event nodes |
| `ex5` | The storage cost of bitemporality and where to draw the line |

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this is the end of Part 3. So far we built the graph and kept it honest. The next chapter is about producing answers from it: how to attach a graph to questions vectors cannot handle, and when that combination is a net loss.

---

Previous: [Ch 15 I Pulled Triples from 10,000 Documents and Half Were False](../../ch15/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 17 Questions Vectors Alone Can't Answer](../../ch17/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
