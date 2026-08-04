# Chapter 13 - An Unvalidated Graph Is Just a Pile of Links

`Part 3 - Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch13/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I blocked bad data at load time and then no data came in.

This chapter is about finding the balance in between. What to block and what to let through, and how to catch the things validation cannot.

## Sections

| # | Title |
|---|---|
| 13.1 | A reasoner and a validator are different tools |
| 13.2 | Block everything and nothing gets in |
| 13.3 | What SHACL cannot catch |
| 13.4 | The shape is right and the meaning moved |
| 13.5 | Do not collapse quality into one number |

## The chapter in one page

- A reasoner and a validator are different tools. OWL concludes that a missing thing exists; SHACL records that a missing thing is a violation. Use a reasoner for quality checks and you lose three weeks.
- Block everything and the data stops coming, and then people route around the validation. The worst outcome is the bypass becoming the main path. Split severity into three levels and set the blocking bar on one question: is it irreversible?
- SHACL misses a lot. Super nodes, cycles, suspected duplicates, multiple membership. You have to count for those, and you must not auto-fix them. Produce a list and let a human look.
- Some changes pass every shape check and still change the answers. You only catch those by putting competency queries into regression tests. A golden dataset of 30 to 50 cases is enough; edge cases matter more than size.
- Do not collapse quality into one number. As data grows, the ratio improves and the absolute count gets worse. Write both down or you will fool yourself.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| sh:severity | [Standard] | [w3.org/TR/shacl/#severity](https://www.w3.org/TR/shacl/#severity) |
| SHACL Advanced Features | [Standard] | [w3.org/TR/shacl-af](https://www.w3.org/TR/shacl-af/) |
| OWL 2 Profiles | [Standard] | [w3.org/TR/owl2-profiles](https://www.w3.org/TR/owl2-profiles/) |
| ISO/IEC 25012 | [Standard] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| graph smell | [Experimental] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| competency question regression | [Experimental] | [protege.stanford.edu/.../ontology101.pdf](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch13/code/`](../../../content/ch13/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 3 - Knowledge Graph Engineering (Track 1)` | **English** | [한국어](../../../content/ch13/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I blocked bad data at load time and then no data came in.

This chapter is about finding the balance in between. What to block and what to let through, and how to catch the things validation cannot.

## Sections

| # | Title |
|---|---|
| 13.1 | A reasoner and a validator are different tools |
| 13.2 | Block everything and nothing gets in |
| 13.3 | What SHACL cannot catch |
| 13.4 | The shape is right and the meaning moved |
| 13.5 | Do not collapse quality into one number |

## The chapter in one page

- A reasoner and a validator are different tools. OWL concludes that a missing thing exists; SHACL records that a missing thing is a violation. Use a reasoner for quality checks and you lose three weeks.
- Block everything and the data stops coming, and then people route around the validation. The worst outcome is the bypass becoming the main path. Split severity into three levels and set the blocking bar on one question: is it irreversible?
- SHACL misses a lot. Super nodes, cycles, suspected duplicates, multiple membership. You have to count for those, and you must not auto-fix them. Produce a list and let a human look.
- Some changes pass every shape check and still change the answers. You only catch those by putting competency queries into regression tests. A golden dataset of 30 to 50 cases is enough; edge cases matter more than size.
- Do not collapse quality into one number. As data grows, the ratio improves and the absolute count gets worse. Write both down or you will fool yourself.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| sh:severity | [Standard] | [w3.org/TR/shacl/#severity](https://www.w3.org/TR/shacl/#severity) |
| SHACL Advanced Features | [Standard] | [w3.org/TR/shacl-af](https://www.w3.org/TR/shacl-af/) |
| OWL 2 Profiles | [Standard] | [w3.org/TR/owl2-profiles](https://www.w3.org/TR/owl2-profiles/) |
| ISO/IEC 25012 | [Standard] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| graph smell | [Experimental] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| competency question regression | [Experimental] | [protege.stanford.edu/.../ontology101.pdf](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch13/code/`](../../../content/ch13/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch13/code
pip install pyshacl owlrl "rdflib>=7,<8"
python3 ex1_shacl_severity.py     # three severity levels
python3 ex2_infer_vs_validate.py  # a reasoner and a validator are different tools
python3 ex3_graph_smells.py       # no dependencies
python3 ex4_regression.py         # no dependencies
python3 ex5_quality_metrics.py    # no dependencies
```

| File | What it shows |
|---|---|
| `shapes.ttl` / `data.ttl` | SHACL shapes and data that deliberately breaks them |
| `ex1` | `sh:severity` splits block / warn / record |
| `ex2` | The same rule in OWL concludes that a missing thing exists |
| `ex3` | Five graph smells SHACL cannot catch |
| `ex4` | A change that passes shape checks and changes query answers |
| `ex5` | Why you must not collapse quality into one score |

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter treated "suspected duplicates" as just a smell. The next one is the main feature. What to do when the same person is sitting there as four nodes, and why automatic merging is dangerous.

---

Previous: [Ch 12 How I Tore Down an Ontology in Three Weeks](../../ch12/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 14 The Same Person, Sitting There as Four Nodes](../../ch14/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
