# Chapter 5 - Things, Not Strings

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch05/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I once started on RDF and switched to a property graph four months in.

This chapter looks at two things: how property graphs took over practice, and what the 2012 declaration "things, not strings" actually meant. The second one keeps coming back for the rest of the book.

## Sections

| # | Title |
|---|---|
| 5.1 | What the 2012 declaration actually meant |
| 5.2 | Two models, different units of counting |
| 5.3 | When you have to hang a property on an edge |
| 5.4 | The same question in two languages |
| 5.5 | So which do you pick |

## The chapter in one page

- The heart of "things, not strings" is not volume, it is distinction. Different nodes sit behind the same name, and each node carries a different set of predicates. The predicate list *is* the thing's identity.
- Property graphs and RDF count in different units. One puts properties in a pocket, the other flattens them into triples, and the difference shows up in one question: can you point a finger at a single property?
- To hang a property on an edge, LPG takes one line and RDF makes you pick one of three approaches. Once more than 30% of your relations carry properties, LPG is the easier side.
- Pick the model on your situation, not on expressive power. And before you pick, write five of your real queries in both languages. That half day saves four months.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| things, not strings | [De facto] | [blog.google/.../introducing-knowledge-graph-things-not](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| Cypher Manual | [De facto] | [neo4j.com/docs/cypher-manual/current](https://neo4j.com/docs/cypher-manual/current/) |
| RDF 1.2 triple terms | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| RDF Datasets | [Standard] | [w3.org/TR/rdf11-datasets](https://www.w3.org/TR/rdf11-datasets/) |
| Kuzu | [De facto] | [github.com/kuzudb/kuzu](https://github.com/kuzudb/kuzu) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch05/code/`](../../../content/ch05/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

`Part 1 - Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch05/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I once started on RDF and switched to a property graph four months in.

This chapter looks at two things: how property graphs took over practice, and what the 2012 declaration "things, not strings" actually meant. The second one keeps coming back for the rest of the book.

## Sections

| # | Title |
|---|---|
| 5.1 | What the 2012 declaration actually meant |
| 5.2 | Two models, different units of counting |
| 5.3 | When you have to hang a property on an edge |
| 5.4 | The same question in two languages |
| 5.5 | So which do you pick |

## The chapter in one page

- The heart of "things, not strings" is not volume, it is distinction. Different nodes sit behind the same name, and each node carries a different set of predicates. The predicate list *is* the thing's identity.
- Property graphs and RDF count in different units. One puts properties in a pocket, the other flattens them into triples, and the difference shows up in one question: can you point a finger at a single property?
- To hang a property on an edge, LPG takes one line and RDF makes you pick one of three approaches. Once more than 30% of your relations carry properties, LPG is the easier side.
- Pick the model on your situation, not on expressive power. And before you pick, write five of your real queries in both languages. That half day saves four months.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| things, not strings | [De facto] | [blog.google/.../introducing-knowledge-graph-things-not](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| Cypher Manual | [De facto] | [neo4j.com/docs/cypher-manual/current](https://neo4j.com/docs/cypher-manual/current/) |
| RDF 1.2 triple terms | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| RDF Datasets | [Standard] | [w3.org/TR/rdf11-datasets](https://www.w3.org/TR/rdf11-datasets/) |
| Kuzu | [De facto] | [github.com/kuzudb/kuzu](https://github.com/kuzudb/kuzu) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch05/code/`](../../../content/ch05/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch05/code
python3 ex1_two_models.py          # no dependencies
python3 ex2_edge_properties.py     # no dependencies
pip install kuzu "rdflib>=7,<8"
python3 ex3_cypher_vs_sparql.py    # one question, two languages
python3 ex4_things_not_strings.py  # no dependencies
```

| File | What it shows |
|---|---|
| `model.py` | The same six facts written twice, as LPG and as RDF |
| `ex1_two_models.py` | The *unit* of counting differs. 3 nodes vs 12 triples |
| `ex2_edge_properties.py` | Three ways to write edge properties in RDF, and what each costs |
| `ex3_cypher_vs_sparql.py` | Same question, same answer, different shape of sentence |
| `ex4_things_not_strings.py` | The predicate list is the thing's identity |

Cypher runs on the embedded engine **Kuzu 0.11.3** so you do not need a server. Where the syntax
diverges from Neo4j 5.x (node table declarations and so on), the code comments say so.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** so far this has been about *writing relations down*. The next chapter looks at the camp that melted them into numeric vectors. Melting lets you predict new relations, and costs you the ability to say why.

---

Previous: [Ch 4 Why the Semantic Web Looked Like a Failure](../../ch04/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 6 It Took Ten Years to Get Back What We Dissolved into Vectors](../../ch06/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
