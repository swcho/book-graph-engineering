# Chapter 11 — One Question, Three Languages

`Part 2 — The Basic Grammar of Graphs` | **English** | [한국어](../../../content/ch11/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I was once asked this in an interview. "Which do you think is better, Cypher or SPARQL?"

This chapter is those two hours, compressed. The same question written in three languages, and how the one that became an international standard in 2024 differs from all three. Plus how many years sit between "a standard exists" and "it runs as specified."

## Sections

| # | Title |
|---|---|
| 11.1 | A picture, a sentence, a walk |
| 11.2 | Where they diverge: path expressions |
| 11.3 | It became a standard in 2024. However |
| 11.4 | Leave the tables alone and look at them as a graph |

## The chapter in one page

- The three languages think about graphs differently. Cypher is a picture, SPARQL is a sentence, Gremlin is a walk. The first two are declarative; the third is closer to imperative.
- The gap opens widest at path expressions. Cypher lets you write an upper bound, SPARQL has no upper-bound notation in the standard, and SQL turns into twenty lines of recursive CTE.
- GQL became an international standard in 2024. But engines do not accept the standard-only syntax yet. The effect of a standard is not "your code changes today," it is "the direction is now settled."
- SQL/PGQ lays a graph view over data without moving it. Attractive, but implementations are still thin on the ground, and the join blowup is still there.
- To prepare for a port: collect your queries in one place, force `ORDER BY`, isolate engine-specific functions, and leave a comment on each query saying which question it answers.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| ISO/IEC 9075-16:2023 | [Standard] | [iso.org/standard/79473.html](https://www.iso.org/standard/79473.html) |
| Cypher Manual | [De facto] | [neo4j.com/docs/cypher-manual/current](https://neo4j.com/docs/cypher-manual/current/) |
| SPARQL 1.1 Query Language | [Standard] | [w3.org/TR/sparql11-query](https://www.w3.org/TR/sparql11-query/) |
| property paths | [Standard] | [w3.org/TR/sparql11-query/#propertypaths](https://www.w3.org/TR/sparql11-query/#propertypaths) |
| Apache TinkerPop | [De facto] | [tinkerpop.apache.org/docs/current/reference](https://tinkerpop.apache.org/docs/current/reference/) |
| GQL Standards | [De facto] | [gqlstandards.org](https://www.gqlstandards.org/) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch11/code/`](../../../content/ch11/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+.

```bash
cd content/ch11/code
pip install kuzu "rdflib>=7,<8"
python3 ex1_three_languages.py   # one question, three languages
python3 ex2_path_queries.py      # variable-length path notation compared
python3 ex3_gql_dialects.py      # whether standard GQL syntax actually runs
python3 ex4_sql_pgq.py           # SQL/PGQ (no dependencies)
python3 ex5_read_plan.py         # reading an execution plan
```

Cypher runs on the embedded engine **Kuzu 0.11.3** so you do not need a server.
`ex3` deliberately includes **queries that fail**. That is the result of the example.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** Part 2 is done. Up to here was how to *handle* a graph. Part 3 is how to *build* one. And the first chapter opens with how I tore down an ontology in three weeks.

---

Previous: [Ch 10 Which Node Actually Matters](../../ch10/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 12 How I Tore Down an Ontology in Three Weeks](../../ch12/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
