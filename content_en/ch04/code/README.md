# Chapter 4 - Why the Semantic Web Looked Like a Failure

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch04/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I spent six months building an ontology and nobody used it.

That is the semantic web's twenty years in miniature. The ambition was right: annotate everything on the web so machines can read it. But a person had to do the annotating, and people would not pay that price. What is interesting is now. Models started paying it instead, which is why a technology that was mocked for twenty years is back on the table.

## Sections

| # | Title |
|---|---|
| 4.1 | An ambition stacked in layers |
| 4.2 | Five things held it back |
| 4.3 | What survived |
| 4.4 | Why we are pulling it back out |

## The chapter in one page

- The semantic web's ambition was to attach meaning to the whole web, and it stalled because a human had to do the attaching.
- Five things held it back: the cost of tagging, the cost of agreement, the open-world assumption, heavy tooling, and federated queries that depend on somebody else's server staying up.
- Plenty survived: the RDF data model, SPARQL path queries, SHACL validation, JSON-LD and schema.org. What the survivors have in common is that they pay off immediately.
- We are pulling it back out because the first obstacle came loose. Once models do the tagging, the cost per triple drops by two orders of magnitude.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| RDF 1.1 Turtle | [Standard] | [w3.org/TR/turtle](https://www.w3.org/TR/turtle/) |
| SPARQL 1.1 Query Language | [Standard] | [w3.org/TR/sparql11-query](https://www.w3.org/TR/sparql11-query/) |
| OWL 2 Web Ontology Language | [Standard] | [w3.org/TR/owl2-overview](https://www.w3.org/TR/owl2-overview/) |
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| JSON for Linking Data | [Standard] | [w3.org/TR/json-ld11](https://www.w3.org/TR/json-ld11/) |
| schema.org | [De facto] | [schema.org/docs/documents.html](https://schema.org/docs/documents.html) |
| Linked Data | [De facto] | [w3.org/DesignIssues/LinkedData.html](https://www.w3.org/DesignIssues/LinkedData.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch04/code/`](../../../content/ch04/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch04/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I spent six months building an ontology and nobody used it.

That is the semantic web's twenty years in miniature. The ambition was right: annotate everything on the web so machines can read it. But a person had to do the annotating, and people would not pay that price. What is interesting is now. Models started paying it instead, which is why a technology that was mocked for twenty years is back on the table.

## Sections

| # | Title |
|---|---|
| 4.1 | An ambition stacked in layers |
| 4.2 | Five things held it back |
| 4.3 | What survived |
| 4.4 | Why we are pulling it back out |

## The chapter in one page

- The semantic web's ambition was to attach meaning to the whole web, and it stalled because a human had to do the attaching.
- Five things held it back: the cost of tagging, the cost of agreement, the open-world assumption, heavy tooling, and federated queries that depend on somebody else's server staying up.
- Plenty survived: the RDF data model, SPARQL path queries, SHACL validation, JSON-LD and schema.org. What the survivors have in common is that they pay off immediately.
- We are pulling it back out because the first obstacle came loose. Once models do the tagging, the cost per triple drops by two orders of magnitude.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| RDF 1.1 Turtle | [Standard] | [w3.org/TR/turtle](https://www.w3.org/TR/turtle/) |
| SPARQL 1.1 Query Language | [Standard] | [w3.org/TR/sparql11-query](https://www.w3.org/TR/sparql11-query/) |
| OWL 2 Web Ontology Language | [Standard] | [w3.org/TR/owl2-overview](https://www.w3.org/TR/owl2-overview/) |
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| JSON for Linking Data | [Standard] | [w3.org/TR/json-ld11](https://www.w3.org/TR/json-ld11/) |
| schema.org | [De facto] | [schema.org/docs/documents.html](https://schema.org/docs/documents.html) |
| Linked Data | [De facto] | [w3.org/DesignIssues/LinkedData.html](https://www.w3.org/DesignIssues/LinkedData.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch04/code/`](../../../content/ch04/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch04/code
python3 ex1_triples_by_hand.py    # no dependencies
pip install "rdflib>=7,<8"
python3 ex2_sparql.py             # reads sample.ttl
python3 ex3_open_world.py         # no dependencies
python3 ex4_jsonld.py             # no dependencies
```

| File | What it shows |
|---|---|
| `sample.ttl` | The same company data in Turtle. 38 triples |
| `ex1_triples_by_hand.py` | A triple store and transitive closure in 30 lines |
| `ex2_sparql.py` | One `+` in a SPARQL path query replaces 20 lines of recursive CTE |
| `ex3_open_world.py` | Where the open-world assumption turns into a production incident |
| `ex4_jsonld.py` | Where the semantic web actually won (schema.org / JSON-LD) |

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter was the "let us define the meaning" camp. The next one looks at the opposite camp: decide meaning later, just hang any property you like on the node now. That camp won in practice first.

---

Previous: [Ch 3 Why Seven Bridges Couldn't Be Crossed, and Why Tables Won](../../ch03/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 5 Things, Not Strings](../../ch05/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
