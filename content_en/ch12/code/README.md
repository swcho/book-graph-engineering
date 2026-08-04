# Chapter 12 — How I Tore Down an Ontology in Three Weeks

`Part 3 — Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch12/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> In Chapter 4 I told the story of a six-month ontology that nobody used. This chapter is about how I fixed it.

This chapter is about that method. Do not build top-down; derive the vocabulary backwards from your queries. And know when to nail the schema down and when to leave it loose.

## Sections

| # | Title |
|---|---|
| 12.1 | Derive it backwards from the queries |
| 12.2 | Split it, or leave it as a property |
| 12.3 | When do you nail the schema down |
| 12.4 | Should you reuse somebody else's vocabulary |
| 12.5 | Ask the data, not the document |

## The chapter in one page

- An ontology is not the truth of a domain. It is the minimum vocabulary your current queries need. Build it top-down and there is no finish condition; derive it backwards from queries and the finish condition becomes "the queries run."
- The basis for splitting a class is not "is this a different thing" but "does it carry different properties." If the kinds are many or grow often, make it a property, not a class.
- Starting without a schema is fine in exactly two cases: you are alone, or the data is disposable. And the most dangerous state is a document with no check behind it. It makes you believe you are complying.
- Judge a public vocabulary by scoring the fit, as a number. Force it and the exception clauses pile up. Make it yours and map to theirs.
- Documents lie and data does not. Run a drift audit as a batch job. Thirty lines is enough.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| OWL 2 Profiles | [Standard] | [w3.org/TR/owl2-profiles](https://www.w3.org/TR/owl2-profiles/) |
| RDF Schema 1.1 | [Standard] | [w3.org/TR/rdf11-schema](https://www.w3.org/TR/rdf11-schema/) |
| schema.org | [De facto] | [schema.org/docs/schemas.html](https://schema.org/docs/schemas.html) |
| SKOS | [Standard] | [w3.org/TR/skos-reference](https://www.w3.org/TR/skos-reference/) |
| competency question | [De facto] | [protege.stanford.edu/…/ontology101.pdf](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |
| ISO/IEC 39075:2024 GQL | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch12/code/`](../../../content/ch12/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch12/code
python3 ex1_vocab_from_questions.py   # no dependencies
pip install kuzu "rdflib>=7,<8" pyshacl
python3 ex2_deep_vs_flat.py           # deep taxonomy vs flat
python3 ex3_when_schema.py            # when to nail the schema down
python3 ex4_reuse_or_build.py         # no dependencies
python3 ex5_schema_drift.py           # no dependencies
```

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter mentioned validation twice, and the next one is that story. An unvalidated graph is just a pile of links, and the three weeks I lost trying to validate with a reasoner gets told properly.

---

Previous: [Ch 11 One Question, Three Languages](../../ch11/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 13 An Unvalidated Graph Is Just a Pile of Links](../../ch13/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
