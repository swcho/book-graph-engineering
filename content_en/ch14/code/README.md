# Chapter 14 — The Same Person, Sitting There as Four Nodes

`Part 3 — Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch14/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I let two company records merge automatically. Same business number, same address, same representative.

This chapter is what I learned from those three days. How to find candidates, how to score them, when to ask a human, and how to undo it when you are wrong. The last one matters most.

## Sections

| # | Title |
|---|---|
| 14.1 | You cannot compare everything |
| 14.2 | Score it, and set two thresholds |
| 14.3 | Merge reversibly |
| 14.4 | Where do you put the threshold |
| 14.5 | Which value survives |

## The chapter in one page

- You cannot compare everything, so blocking narrows the candidates. Recall decides whether it works. If a pair never makes the candidate list they never meet, so run three or four strategies and take the union.
- Set two thresholds. Above, automatic. Below, ignore. In between, a human. The job of automation is not to get everything right, it is to sort out the ambiguous cases.
- Do not delete the originals. Point them at a representative node and undoing becomes fixing one pointer. And once it is reversible you can automate far more aggressively.
- Put veto rules above the score. Different business number means different legal entity, no matter how much else matches.
- Survivorship rules differ per field. And never let an empty value or a placeholder win. That is one line and it prevents half your incidents.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| entity resolution | [De facto] | [vldb.org/pvldb/vol11/p1454-mudgal.pdf](https://www.vldb.org/pvldb/vol11/p1454-mudgal.pdf) |
| blocking | [De facto] | [dl.acm.org/doi/10.1145/3355491.3355496](https://dl.acm.org/doi/10.1145/3355491.3355496) |
| Fellegi-Sunter model | [De facto] | [tandfonline.com/…/01621459.1969.10501049](https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049) |
| owl:sameAs | [Standard] | [w3.org/TR/owl2-syntax/#Individual_Equality](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| skos:closeMatch | [Standard] | [w3.org/TR/skos-reference/#mapping](https://www.w3.org/TR/skos-reference/#mapping) |
| survivorship rules | [Experimental] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| PROV-O | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch14/code/`](../../../content/ch14/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch14/code
python3 ex1_blocking.py           # blocking instead of all-pairs, and what it misses
python3 ex2_scoring.py            # scores, thresholds, transitivity, and human review
python3 ex3_reversible_merge.py   # a merge you can undo
python3 ex4_threshold_tuning.py   # what one threshold changes
python3 ex5_survivorship.py       # which value survives
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** so far we assumed the data already existed. The next chapter is about pulling triples out of documents. It starts with what happened when I pulled them out of ten thousand and half were false.

---

Previous: [Ch 13 An Unvalidated Graph Is Just a Pile of Links](../../ch13/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 15 I Pulled Triples from 10,000 Documents and Half Were False](../../ch15/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
