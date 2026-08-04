# Chapter 15 - I Pulled Triples from 10,000 Documents and Half Were False

`Part 3 - Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch15/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I pulled triples out of 12,000 internal wiki pages. It took four days and produced 470,000 of them.

I threw all of it away and built it again. This chapter is what I learned on the second attempt.

## Sections

| # | Title |
|---|---|
| 15.1 | If you do not measure it you cannot tell whether you improved it |
| 15.2 | Make it show its evidence |
| 15.3 | The holding queue is the heart of the pipeline |
| 15.4 | The confidence a model reports is not worth trusting |
| 15.5 | What do you delete when the document changes |

## The chapter in one page

- Measure first. The two days it takes to hand-build 40 gold answers save everything else. And split the errors by kind. "Precision 0.64" alone does not tell you what to fix.
- Make it output the supporting sentence and check it against the source. It is string comparison, so it is cheap and deterministic. When you check, look for the *object* in the supporting sentence, not the subject.
- Do not discard predicates outside your vocabulary; put them in a holding queue. Reviewing the top ten by frequency once a week is enough. And the hold rate is your measure of how far your vocabulary has drifted from reality.
- A model's self-reported confidence gives high values to false statements too. Sampling several runs and counting votes works better, and since it is expensive, use it only on the ambiguous ones.
- If you replace whole documents on re-extraction, the corrections a human made get wiped. Store provenance per triple: document, position, who, when. Four fields is enough.
- And do not make triple count a KPI. My second run produced 33% fewer than the first, and more usable ones.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| information extraction | [De facto] | [aclanthology.org/D19-1522](https://aclanthology.org/D19-1522/) |
| grounded generation | [De facto] | [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) |
| self-consistency | [De facto] | [arxiv.org/abs/2203.11171](https://arxiv.org/abs/2203.11171) |
| PROV-O | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| precision, recall | [Standard] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| structured output | [De facto] | [docs.claude.com/.../overview](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview) |
| Microsoft GraphRAG indexing | [De facto] | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch15/code/`](../../../content/ch15/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 3 - Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch15/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I pulled triples out of 12,000 internal wiki pages. It took four days and produced 470,000 of them.

I threw all of it away and built it again. This chapter is what I learned on the second attempt.

## Sections

| # | Title |
|---|---|
| 15.1 | If you do not measure it you cannot tell whether you improved it |
| 15.2 | Make it show its evidence |
| 15.3 | The holding queue is the heart of the pipeline |
| 15.4 | The confidence a model reports is not worth trusting |
| 15.5 | What do you delete when the document changes |

## The chapter in one page

- Measure first. The two days it takes to hand-build 40 gold answers save everything else. And split the errors by kind. "Precision 0.64" alone does not tell you what to fix.
- Make it output the supporting sentence and check it against the source. It is string comparison, so it is cheap and deterministic. When you check, look for the *object* in the supporting sentence, not the subject.
- Do not discard predicates outside your vocabulary; put them in a holding queue. Reviewing the top ten by frequency once a week is enough. And the hold rate is your measure of how far your vocabulary has drifted from reality.
- A model's self-reported confidence gives high values to false statements too. Sampling several runs and counting votes works better, and since it is expensive, use it only on the ambiguous ones.
- If you replace whole documents on re-extraction, the corrections a human made get wiped. Store provenance per triple: document, position, who, when. Four fields is enough.
- And do not make triple count a KPI. My second run produced 33% fewer than the first, and more usable ones.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| information extraction | [De facto] | [aclanthology.org/D19-1522](https://aclanthology.org/D19-1522/) |
| grounded generation | [De facto] | [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) |
| self-consistency | [De facto] | [arxiv.org/abs/2203.11171](https://arxiv.org/abs/2203.11171) |
| PROV-O | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| precision, recall | [Standard] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| structured output | [De facto] | [docs.claude.com/.../overview](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview) |
| Microsoft GraphRAG indexing | [De facto] | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch15/code/`](../../../content/ch15/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies.**

```bash
cd content/ch15/code
python3 ex1_measure.py       # measure precision and recall first
python3 ex2_grounding.py     # filtering fabrications with an evidence check
python3 ex3_normalize.py     # vocabulary normalization and the holding queue
python3 ex4_confidence.py    # self-report vs counting votes over several runs
python3 ex5_incremental.py   # what to delete when the document changes
```

`extractor.py` is a **fake extractor** built so this runs without an API key. It imitates four
failure modes real models show: fabricating, going outside the vocabulary, promoting a guess to
a fact, and omission.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter kept mentioning "mark it inactive" and `valid_to`. The next one is the main feature: how to put a fact that was right yesterday and wrong today into a graph.

---

Previous: [Ch 14 The Same Person, Sitting There as Four Nodes](../../ch14/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 16 True Yesterday, Wrong Today](../../ch16/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
