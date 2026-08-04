# Primary Sources

**English** | [한국어](SOURCES.md) | [Back to the table of contents](README.en.md)

Every keyword box in the book opens a chapter with its primary sources. This page collects all of them: 172 links across 228 keywords, checked as of August 2026.

Only official specifications, vendor documentation, RFCs, papers, official vendor engineering blogs, and official repositories are here. No blog summaries, no secondary sources. A keyword with no primary source was either dropped from the box or demoted to [Experimental].

If you find a dead link, that keyword needs another look. A source disappearing can mean the ground under the concept has shifted.

## What the status labels mean

| Label | Meaning | Count |
|---|---|---|
| **[Standard]** | An official specification exists — ISO/IEC, W3C, RFC | 62 |
| **[De facto]** | No specification, but the industry uses it widely | 142 |
| **[Experimental]** | Still finding its footing | 24 |

The maturity gap between Track 1 (knowledge graphs) and Track 2 (agent graphs) shows up right here. [Standard] clusters in Part 3; [Experimental] clusters in Part 4. That gap is roughly twenty years, and it is why those two parts are written in different registers.

## Sources by chapter

Chapter titles link to that chapter's summary page. Those pages are in Korean for now — the source tables below are not.

### Part 1 — Roots: Where the Graph Was All Along

#### Chapter 1 — [Sixty Years of AI, Read as a Graph](content/ch01/code/README.md)

| Term | Status | Source |
|---|---|---|
| Transformer | [De facto] | [arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762) |
| scaling laws | [Experimental] | [arxiv.org/abs/2001.08361](https://arxiv.org/abs/2001.08361) |
| ReAct | [De facto] | [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629) |
| knowledge graph | [De facto] | [blog.google/…/introducing-knowledge-graph-things-not](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| state graph, superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| harness | [Experimental] | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |

#### Chapter 2 — [From Harness Engineering to Graph Engineering](content/ch02/code/README.md)

| Term | Status | Source |
|---|---|---|
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| context engineering | [De facto] | [anthropic.com/…/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| agent harness | [Experimental] | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |
| state graph, superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| AGENTS.md | [De facto] | [agents.md](https://agents.md/) |
| A2A | [Experimental] | [a2a-protocol.org](https://a2a-protocol.org/) |
| topological sort | [Standard] | [dl.acm.org/doi/10.1145/368996.369025](https://dl.acm.org/doi/10.1145/368996.369025) |
| event sourcing | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |

#### Chapter 3 — [Why Seven Bridges Couldn't Be Crossed, and Why Tables Won](content/ch03/code/README.md)

| Term | Status | Source |
|---|---|---|
| Seven Bridges of Königsberg | [Standard] | [scholarlycommons.pacific.edu/euler-works/53](https://scholarlycommons.pacific.edu/euler-works/53/) |
| degree | [Standard] | [scholarlycommons.pacific.edu/euler-works/53](https://scholarlycommons.pacific.edu/euler-works/53/) |
| relational model | [Standard] | [dl.acm.org/doi/10.1145/362384.362685](https://dl.acm.org/doi/10.1145/362384.362685) |
| recursive CTE | [Standard] | [sqlite.org/lang_with.html](https://www.sqlite.org/lang_with.html) |
| transaction, ACID | [Standard] | [sqlite.org/transactional.html](https://www.sqlite.org/transactional.html) |
| ISO/IEC 9075-16:2023 | [Standard] | [iso.org/standard/79473.html](https://www.iso.org/standard/79473.html) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |

#### Chapter 4 — [Why the Semantic Web Looked Like a Failure](content/ch04/code/README.md)

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

#### Chapter 5 — [Things, Not Strings](content/ch05/code/README.md)

| Term | Status | Source |
|---|---|---|
| things, not strings | [De facto] | [blog.google/…/introducing-knowledge-graph-things-not](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| Cypher Manual | [De facto] | [neo4j.com/docs/cypher-manual/current](https://neo4j.com/docs/cypher-manual/current/) |
| RDF 1.2 triple terms | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| RDF Datasets | [Standard] | [w3.org/TR/rdf11-datasets](https://www.w3.org/TR/rdf11-datasets/) |
| Kuzu | [De facto] | [github.com/kuzudb/kuzu](https://github.com/kuzudb/kuzu) |

#### Chapter 6 — [It Took Ten Years to Get Back What We Dissolved into Vectors](content/ch06/code/README.md)

| Term | Status | Source |
|---|---|---|
| Graph Neural Networks: A Review | [De facto] | [arxiv.org/abs/1812.08434](https://arxiv.org/abs/1812.08434) |
| Neural Message Passing | [De facto] | [arxiv.org/abs/1704.01212](https://arxiv.org/abs/1704.01212) |
| GCN | [De facto] | [arxiv.org/abs/1609.02907](https://arxiv.org/abs/1609.02907) |
| TransE | [De facto] | [papers.nips.cc/…/5071-translating-embeddings-for-modeling-multi-](https://papers.nips.cc/paper/5071-translating-embeddings-for-modeling-multi-relational-data) |
| RAG | [De facto] | [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) |
| Microsoft GraphRAG | [De facto] | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |
| LightRAG | [Experimental] | [arxiv.org/abs/2410.05779](https://arxiv.org/abs/2410.05779) |
| HippoRAG | [Experimental] | [arxiv.org/abs/2405.14831](https://arxiv.org/abs/2405.14831) |

### Part 2 — The Basic Grammar of Graphs

#### Chapter 7 — [One Node Drawn Wrong Cost Me Three Weeks](content/ch07/code/README.md)

| Term | Status | Source |
|---|---|---|
| ISO/IEC 39075:2024 GQL | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| RDF 1.2 Concepts | [Standard] | [w3.org/TR/rdf12-concepts](https://www.w3.org/TR/rdf12-concepts/) |
| Cypher: patterns | [De facto] | [neo4j.com/docs/cypher-manual/current/patterns](https://neo4j.com/docs/cypher-manual/current/patterns/) |
| reification | [Standard] | [w3.org/TR/rdf12-schema](https://www.w3.org/TR/rdf12-schema/) |
| bipartite graph | [De facto] | [networkx.org/…/bipartite.html](https://networkx.org/documentation/stable/reference/algorithms/bipartite.html) |
| multigraph, self-loop | [De facto] | [networkx.org/…/multigraph.html](https://networkx.org/documentation/stable/reference/classes/multigraph.html) |

#### Chapter 8 — [What a Graph Actually Looks Like in Memory](content/ch08/code/README.md)

| Term | Status | Source |
|---|---|---|
| CSR, Compressed Sparse Row | [De facto] | [docs.scipy.org/…/scipy.sparse.csr_matrix.html](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.html) |
| index-free adjacency | [De facto] | [neo4j.com/…/graphdb-concepts](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/) |
| adjacency matrix / list | [De facto] | [networkx.org/…/convert.html](https://networkx.org/documentation/stable/reference/convert.html) |
| super node | [De facto] | [neo4j.com/…/planning-and-tuning](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| graph reordering | [Experimental] | [arxiv.org/abs/1602.08820](https://arxiv.org/abs/1602.08820) |
| locality of reference | [De facto] | [kernel.org/doc/html/latest/admin-guide/mm/index.html](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html) |

#### Chapter 9 — [Counting Degrees of Separation Killed the Server](content/ch09/code/README.md)

| Term | Status | Source |
|---|---|---|
| BFS | [De facto] | [networkx.org/…/traversal.html](https://networkx.org/documentation/stable/reference/algorithms/traversal.html) |
| bidirectional search | [De facto] | [networkx.org/…/networkx.algorithms.shortest_paths.unweighted.bid](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.unweighted.bidirectional_shortest_path.html) |
| Dijkstra's algorithm | [Standard] | [link.springer.com/article/10.1007/BF01386390](https://link.springer.com/article/10.1007/BF01386390) |
| Bellman-Ford | [De facto] | [networkx.org/…/networkx.algorithms.shortest_paths.weighted.bellm](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.bellman_ford_path.html) |
| A* | [De facto] | [ieeexplore.ieee.org/document/4082128](https://ieeexplore.ieee.org/document/4082128) |
| topological sort | [Standard] | [dl.acm.org/doi/10.1145/368996.369025](https://dl.acm.org/doi/10.1145/368996.369025) |
| Cypher variable-length patterns | [De facto] | [neo4j.com/…/variable-length-patterns](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-patterns/) |

#### Chapter 10 — [Which Node Actually Matters](content/ch10/code/README.md)

| Term | Status | Source |
|---|---|---|
| centrality measures | [De facto] | [networkx.org/…/centrality.html](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) |
| Brandes' algorithm | [De facto] | [tandfonline.com/…/0022250X.2001.9990249](https://www.tandfonline.com/doi/abs/10.1080/0022250X.2001.9990249) |
| PageRank | [De facto] | [ilpubs.stanford.edu:8090/422](http://ilpubs.stanford.edu:8090/422/) |
| modularity | [De facto] | [arxiv.org/abs/cond-mat/0308217](https://arxiv.org/abs/cond-mat/0308217) |
| Louvain method | [De facto] | [arxiv.org/abs/0803.0476](https://arxiv.org/abs/0803.0476) |
| Leiden algorithm | [De facto] | [nature.com/articles/s41598-019-41695-z](https://www.nature.com/articles/s41598-019-41695-z) |
| resolution limit | [De facto] | [pnas.org/doi/10.1073/pnas.0605965104](https://www.pnas.org/doi/10.1073/pnas.0605965104) |
| label propagation | [De facto] | [arxiv.org/abs/0709.2938](https://arxiv.org/abs/0709.2938) |

#### Chapter 11 — [One Question, Three Languages](content/ch11/code/README.md)

| Term | Status | Source |
|---|---|---|
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| ISO/IEC 9075-16:2023 | [Standard] | [iso.org/standard/79473.html](https://www.iso.org/standard/79473.html) |
| Cypher Manual | [De facto] | [neo4j.com/docs/cypher-manual/current](https://neo4j.com/docs/cypher-manual/current/) |
| SPARQL 1.1 Query Language | [Standard] | [w3.org/TR/sparql11-query](https://www.w3.org/TR/sparql11-query/) |
| property paths | [Standard] | [w3.org/TR/sparql11-query/#propertypaths](https://www.w3.org/TR/sparql11-query/#propertypaths) |
| Apache TinkerPop | [De facto] | [tinkerpop.apache.org/docs/current/reference](https://tinkerpop.apache.org/docs/current/reference/) |
| GQL Standards | [De facto] | [gqlstandards.org](https://www.gqlstandards.org/) |

### Part 3 — Knowledge Graph Engineering (Track 1)

#### Chapter 12 — [How I Tore Down an Ontology in Three Weeks](content/ch12/code/README.md)

| Term | Status | Source |
|---|---|---|
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| OWL 2 Profiles | [Standard] | [w3.org/TR/owl2-profiles](https://www.w3.org/TR/owl2-profiles/) |
| RDF Schema 1.1 | [Standard] | [w3.org/TR/rdf11-schema](https://www.w3.org/TR/rdf11-schema/) |
| schema.org | [De facto] | [schema.org/docs/schemas.html](https://schema.org/docs/schemas.html) |
| SKOS | [Standard] | [w3.org/TR/skos-reference](https://www.w3.org/TR/skos-reference/) |
| competency question | [De facto] | [protege.stanford.edu/…/ontology101.pdf](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |
| ISO/IEC 39075:2024 GQL | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |

#### Chapter 13 — [An Unvalidated Graph Is Just a Pile of Links](content/ch13/code/README.md)

| Term | Status | Source |
|---|---|---|
| Shapes Constraint Language | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| sh:severity | [Standard] | [w3.org/TR/shacl/#severity](https://www.w3.org/TR/shacl/#severity) |
| SHACL Advanced Features | [Standard] | [w3.org/TR/shacl-af](https://www.w3.org/TR/shacl-af/) |
| OWL 2 Profiles | [Standard] | [w3.org/TR/owl2-profiles](https://www.w3.org/TR/owl2-profiles/) |
| ISO/IEC 25012 | [Standard] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| graph smell | [Experimental] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| competency question regression | [Experimental] | [protege.stanford.edu/…/ontology101.pdf](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |

#### Chapter 14 — [The Same Person, Sitting There as Four Nodes](content/ch14/code/README.md)

| Term | Status | Source |
|---|---|---|
| entity resolution | [De facto] | [vldb.org/pvldb/vol11/p1454-mudgal.pdf](https://www.vldb.org/pvldb/vol11/p1454-mudgal.pdf) |
| blocking | [De facto] | [dl.acm.org/doi/10.1145/3355491.3355496](https://dl.acm.org/doi/10.1145/3355491.3355496) |
| Fellegi-Sunter model | [De facto] | [tandfonline.com/…/01621459.1969.10501049](https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049) |
| owl:sameAs | [Standard] | [w3.org/TR/owl2-syntax/#Individual_Equality](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| skos:closeMatch | [Standard] | [w3.org/TR/skos-reference/#mapping](https://www.w3.org/TR/skos-reference/#mapping) |
| survivorship rules | [Experimental] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| PROV-O | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |

#### Chapter 15 — [I Pulled Triples from 10,000 Documents and Half Were False](content/ch15/code/README.md)

| Term | Status | Source |
|---|---|---|
| information extraction | [De facto] | [aclanthology.org/D19-1522](https://aclanthology.org/D19-1522/) |
| grounded generation | [De facto] | [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) |
| self-consistency | [De facto] | [arxiv.org/abs/2203.11171](https://arxiv.org/abs/2203.11171) |
| PROV-O | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| precision, recall | [Standard] | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) |
| structured output | [De facto] | [docs.claude.com/…/overview](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview) |
| Microsoft GraphRAG indexing | [De facto] | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |

#### Chapter 16 — [True Yesterday, Wrong Today](content/ch16/code/README.md)

| Term | Status | Source |
|---|---|---|
| bitemporal | [De facto] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |
| valid time | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |
| transaction time | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |
| Graphiti / Zep | [Experimental] | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) |
| ISO 8601 | [Standard] | [iso.org/iso-8601-date-and-time-format.html](https://www.iso.org/iso-8601-date-and-time-format.html) |
| OWL-Time | [Standard] | [w3.org/TR/owl-time](https://www.w3.org/TR/owl-time/) |
| slowly changing dimension | [De facto] | [kimballgroup.com/…/dimensional-modeling-techniques](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) |

#### Chapter 17 — [Questions Vectors Alone Can't Answer](content/ch17/code/README.md)

| Term | Status | Source |
|---|---|---|
| Microsoft GraphRAG | [De facto] | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) |
| LightRAG | [Experimental] | [arxiv.org/abs/2410.05779](https://arxiv.org/abs/2410.05779) |
| HippoRAG | [Experimental] | [arxiv.org/abs/2405.14831](https://arxiv.org/abs/2405.14831) |
| Graphiti | [Experimental] | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) |
| reciprocal rank fusion | [De facto] | [dl.acm.org/doi/10.1145/1571941.1572114](https://dl.acm.org/doi/10.1145/1571941.1572114) |
| RAG | [De facto] | [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) |
| hybrid search | [De facto] | [elastic.co/what-is/hybrid-search](https://www.elastic.co/what-is/hybrid-search) |

### Part 4 — Agent Graph Engineering (Track 2)

#### Chapter 18 — [Where Does a Chain Break](content/ch18/code/README.md)

| Term | Status | Source |
|---|---|---|
| agent workflow patterns | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| StateGraph | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| checkpointer | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| prompt chaining | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| cyclomatic complexity | [Standard] | [ieeexplore.ieee.org/document/1702388](https://ieeexplore.ieee.org/document/1702388) |
| durable execution | [De facto] | [docs.temporal.io/temporal](https://docs.temporal.io/temporal) |
| ReAct | [De facto] | [arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629) |

#### Chapter 19 — [State Graphs, Reducers, and Supersteps](content/ch19/code/README.md)

| Term | Status | Source |
|---|---|---|
| StateGraph | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| reducer | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| superstep | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| Pregel | [De facto] | [dl.acm.org/doi/10.1145/1807167.1807184](https://dl.acm.org/doi/10.1145/1807167.1807184) |
| Bulk Synchronous Parallel | [De facto] | [dl.acm.org/doi/10.1145/79173.79181](https://dl.acm.org/doi/10.1145/79173.79181) |
| persistence | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| lost update | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |

#### Chapter 20 — [How to End a Loop That Won't End](content/ch20/code/README.md)

| Term | Status | Source |
|---|---|---|
| termination condition | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| recursion limit | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| evaluator-optimizer | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| usage tracking | [De facto] | [docs.claude.com/…/token-counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |
| early stopping | [De facto] | [deeplearningbook.org/contents/regularization.html](https://www.deeplearningbook.org/contents/regularization.html) |
| circuit breaker | [De facto] | [martinfowler.com/bliki/CircuitBreaker.html](https://martinfowler.com/bliki/CircuitBreaker.html) |
| rate limiting | [De facto] | [datatracker.ietf.org/doc/html/rfc6585](https://datatracker.ietf.org/doc/html/rfc6585) |

#### Chapter 21 — [The Process Dies, the Work Must Not](content/ch21/code/README.md)

| Term | Status | Source |
|---|---|---|
| checkpointer | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| durable execution | [De facto] | [docs.temporal.io/evaluate/understanding-temporal](https://docs.temporal.io/evaluate/understanding-temporal) |
| idempotency | [Standard] | [datatracker.ietf.org/doc/html/rfc9110#section-9.2.2](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2) |
| idempotency key | [De facto] | [datatracker.ietf.org/…/draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header) |
| exactly-once | [De facto] | [kafka.apache.org/documentation/#semantics](https://kafka.apache.org/documentation/#semantics) |
| thread id | [De facto] | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| write-ahead log | [De facto] | [sqlite.org/wal.html](https://www.sqlite.org/wal.html) |

#### Chapter 22 — [How to Pay Back What You Can't Undo](content/ch22/code/README.md)

| Term | Status | Source |
|---|---|---|
| exponential backoff | [De facto] | [aws.amazon.com/…/timeouts-retries-and-backoff-with-jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| jitter | [De facto] | [aws.amazon.com/…/timeouts-retries-and-backoff-with-jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| retry storm | [De facto] | [sre.google/sre-book/handling-overload](https://sre.google/sre-book/handling-overload/) |
| circuit breaker | [De facto] | [martinfowler.com/bliki/CircuitBreaker.html](https://martinfowler.com/bliki/CircuitBreaker.html) |
| saga | [De facto] | [cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) |
| compensating transaction | [De facto] | [learn.microsoft.com/…/compensating-transaction](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) |
| dead letter queue | [De facto] | [docs.aws.amazon.com/…/sqs-dead-letter-queues.html](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) |
| Retry-After | [Standard] | [datatracker.ietf.org/…/rfc9110#field.retry-after](https://datatracker.ietf.org/doc/html/rfc9110#field.retry-after) |

#### Chapter 23 — [Where the Human Steps In](content/ch23/code/README.md)

| Term | Status | Source |
|---|---|---|
| human in the loop | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| interrupt | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| Command(resume) | [De facto] | [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| approval gate | [De facto] | [learn.microsoft.com/…/gatekeeper](https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper) |
| escalation | [De facto] | [sre.google/workbook/incident-response](https://sre.google/workbook/incident-response/) |
| audit trail | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| four-eyes principle | [De facto] | [bis.org/publ/bcbs230.pdf](https://www.bis.org/publ/bcbs230.pdf) |

#### Chapter 24 — [Your Context Is Full](content/ch24/code/README.md)

| Term | Status | Source |
|---|---|---|
| context window | [De facto] | [docs.claude.com/…/context-windows](https://docs.claude.com/en/docs/build-with-claude/context-windows) |
| context engineering | [Experimental] | [anthropic.com/…/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| compaction | [Experimental] | [anthropic.com/…/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| offloading | [Experimental] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| prompt caching | [De facto] | [docs.claude.com/…/prompt-caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) |
| long-term memory store | [De facto] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| token counting | [De facto] | [docs.claude.com/…/token-counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |

#### Chapter 25 — [Six Topologies, and the Sockets You Plug Tools Into](content/ch25/code/README.md)

| Term | Status | Source |
|---|---|---|
| orchestrator-workers | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| fan-out/fan-in | [De facto] | [learn.microsoft.com/…/durable-functions-cloud-backup](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-cloud-backup) |
| routing | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| evaluator-optimizer | [De facto] | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| tail latency | [De facto] | [research.google/pubs/the-tail-at-scale](https://research.google/pubs/the-tail-at-scale/) |
| Model Context Protocol | [De facto] | [modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18) |
| tool schema | [De facto] | [modelcontextprotocol.io/…/tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) |
| Send | [De facto] | [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api) |

#### Chapter 26 — [What Will You Forbid](content/ch26/code/README.md)

| Term | Status | Source |
|---|---|---|
| least privilege | [De facto] | [csrc.nist.gov/glossary/term/least_privilege](https://csrc.nist.gov/glossary/term/least_privilege) |
| allowlist | [De facto] | [cheatsheetseries.owasp.org/…/Input_Validation_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) |
| prompt injection | [De facto] | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| indirect prompt injection | [De facto] | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| blast radius | [De facto] | [sre.google/sre-book/addressing-cascading-failures](https://sre.google/sre-book/addressing-cascading-failures/) |
| privilege escalation | [Standard] | [attack.mitre.org/tactics/TA0004](https://attack.mitre.org/tactics/TA0004/) |
| sandbox | [De facto] | [gvisor.dev/docs](https://gvisor.dev/docs/) |
| audit log | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

### Part 5 — Where the Two Graphs Meet

#### Chapter 27 — [The Cheapest Way to Give an Agent Memory](content/ch27/code/README.md)

| Term | Status | Source |
|---|---|---|
| long-term memory | [De facto] | [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| episodic memory | [Experimental] | [arxiv.org/abs/2404.13501](https://arxiv.org/abs/2404.13501) |
| temporal knowledge graph | [Experimental] | [arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956) |
| hybrid retrieval | [De facto] | [neo4j.com/…/vector-indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) |
| decay policy | [Experimental] | [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560) |
| entity resolution | [De facto] | [w3.org/TR/owl2-syntax/#Individual_Equality](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| valid time | [Standard] | [iso.org/standard/76583.html](https://www.iso.org/standard/76583.html) |

#### Chapter 28 — [When the Agent Grows the Graph by Itself](content/ch28/code/README.md)

| Term | Status | Source |
|---|---|---|
| knowledge graph completion | [Experimental] | [arxiv.org/abs/2002.00388](https://arxiv.org/abs/2002.00388) |
| provenance | [Standard] | [w3.org/TR/prov-o](https://www.w3.org/TR/prov-o/) |
| retraction | [De facto] | [w3.org/TR/prov-o/#Invalidation](https://www.w3.org/TR/prov-o/#Invalidation) |
| truth maintenance | [Experimental] | [dl.acm.org/doi/10.1145/321978.321979](https://dl.acm.org/doi/10.1145/321978.321979) |
| schema drift | [De facto] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| self-training bias | [Experimental] | [arxiv.org/abs/2305.17493](https://arxiv.org/abs/2305.17493) |
| SHACL validation | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |

#### Chapter 29 — [One Backbone](content/ch29/code/README.md)

| Term | Status | Source |
|---|---|---|
| reference architecture | [De facto] | [learn.microsoft.com/en-us/azure/architecture/guide](https://learn.microsoft.com/en-us/azure/architecture/guide/) |
| data lineage | [Standard] | [w3.org/TR/prov-o/#Derivation](https://www.w3.org/TR/prov-o/#Derivation) |
| read timestamp | [De facto] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |
| polyglot persistence | [De facto] | [martinfowler.com/bliki/PolyglotPersistence.html](https://martinfowler.com/bliki/PolyglotPersistence.html) |
| bounded context | [De facto] | [martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html) |
| fitness function | [De facto] | [thoughtworks.com/…/fitness-function-driven-development](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development) |
| write path separation | [De facto] | [neo4j.com/docs/operations-manual/current/performance](https://neo4j.com/docs/operations-manual/current/performance/) |

### Part 6 — The Backbone: State Management Engine

#### Chapter 30 — [Nobody Knows What Changed, or When](content/ch30/code/README.md)

| Term | Status | Source |
|---|---|---|
| event sourcing | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |
| append-only log | [De facto] | [kafka.apache.org/documentation/#design](https://kafka.apache.org/documentation/#design) |
| replay | [De facto] | [martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html) |
| snapshot | [De facto] | [sqlite.org/wal.html](https://www.sqlite.org/wal.html) |
| write-ahead log | [De facto] | [postgresql.org/docs/current/wal-intro.html](https://www.postgresql.org/docs/current/wal-intro.html) |
| CQRS | [De facto] | [martinfowler.com/bliki/CQRS.html](https://martinfowler.com/bliki/CQRS.html) |
| hash chain | [Standard] | [datatracker.ietf.org/doc/html/rfc6962](https://datatracker.ietf.org/doc/html/rfc6962) |
| audit trail | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

#### Chapter 31 — [Two Agents Edited the Same Node at Once](content/ch31/code/README.md)

| Term | Status | Source |
|---|---|---|
| lost update | [Standard] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |
| optimistic locking | [De facto] | [martinfowler.com/…/optimisticOfflineLock.html](https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html) |
| pessimistic locking | [De facto] | [martinfowler.com/…/pessimisticOfflineLock.html](https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html) |
| compare-and-swap | [Standard] | [en.cppreference.com/…/compare_exchange](https://en.cppreference.com/w/cpp/atomic/atomic/compare_exchange) |
| serializable | [Standard] | [postgresql.org/…/transaction-iso.html#XACT-SERIALIZABLE](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE) |
| CRDT | [Experimental] | [inria.hal.science/inria-00555588](https://inria.hal.science/inria-00555588) |
| deadlock | [Standard] | [postgresql.org/…/explicit-locking.html#LOCKING-DEADLOCKS](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS) |
| write skew | [Standard] | [postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html) |

#### Chapter 32 — [The Day You Change the Schema](content/ch32/code/README.md)

| Term | Status | Source |
|---|---|---|
| expand and contract | [De facto] | [martinfowler.com/bliki/ParallelChange.html](https://martinfowler.com/bliki/ParallelChange.html) |
| zero-downtime deployment | [De facto] | [martinfowler.com/bliki/BlueGreenDeployment.html](https://martinfowler.com/bliki/BlueGreenDeployment.html) |
| dual write | [De facto] | [martinfowler.com/bliki/ParallelChange.html](https://martinfowler.com/bliki/ParallelChange.html) |
| backfill | [De facto] | [cloud.google.com/…/database-migration-concepts-principles-part-1](https://cloud.google.com/architecture/database-migration-concepts-principles-part-1) |
| schema evolution | [De facto] | [avro.apache.org/…/#schema-resolution](https://avro.apache.org/docs/current/specification/#schema-resolution) |
| SHACL | [Standard] | [w3.org/TR/shacl](https://www.w3.org/TR/shacl/) |
| backward compatibility | [De facto] | [protobuf.dev/programming-guides/proto3/#updating](https://protobuf.dev/programming-guides/proto3/#updating) |

### Part 7 — Operations

#### Chapter 33 — [Read the Query Plan and You See the Bill](content/ch33/code/README.md)

| Term | Status | Source |
|---|---|---|
| query plan | [De facto] | [neo4j.com/…/execution-plans](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/) |
| EXPLAIN | [De facto] | [neo4j.com/…/planning-and-tuning](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| cartesian product | [Standard] | [postgresql.org/…/queries-table-expressions.html](https://www.postgresql.org/docs/current/queries-table-expressions.html) |
| index | [De facto] | [neo4j.com/docs/cypher-manual/current/indexes](https://neo4j.com/docs/cypher-manual/current/indexes/) |
| slow query log | [De facto] | [dev.mysql.com/doc/refman/8.0/en/slow-query-log.html](https://dev.mysql.com/doc/refman/8.0/en/slow-query-log.html) |
| Amdahl's law | [Standard] | [dl.acm.org/doi/10.1145/1465482.1465560](https://dl.acm.org/doi/10.1145/1465482.1465560) |
| bulk load | [De facto] | [neo4j.com/…/neo4j-admin-import](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/) |

#### Chapter 34 — [What It Means to Erase Personal Data from a Graph](content/ch34/code/README.md)

| Term | Status | Source |
|---|---|---|
| right to erasure | [Standard] | [gdpr-info.eu/art-17-gdpr](https://gdpr-info.eu/art-17-gdpr/) |
| pseudonymisation | [Standard] | [gdpr-info.eu/art-4-gdpr](https://gdpr-info.eu/art-4-gdpr/) |
| re-identification | [De facto] | [nist.gov/…/de-identification-personal-information](https://www.nist.gov/publications/de-identification-personal-information) |
| k-anonymity | [De facto] | [dataprivacylab.org/…/kanonymity.pdf](https://dataprivacylab.org/dataprivacy/projects/kanonymity/kanonymity.pdf) |
| differential privacy | [De facto] | [microsoft.com/…/differential-privacy](https://www.microsoft.com/en-us/research/publication/differential-privacy/) |
| data minimisation | [Standard] | [gdpr-info.eu/art-5-gdpr](https://gdpr-info.eu/art-5-gdpr/) |
| retention period | [Standard] | [csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

### Part 8 — What Comes Next

#### Chapter 35 — [Five Claims Most Likely to Be Wrong in Three Years](content/ch35/code/README.md)

| Term | Status | Source |
|---|---|---|
| falsifiability | [De facto] | [plato.stanford.edu/entries/popper](https://plato.stanford.edu/entries/popper/) |
| ISO/IEC 39075 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| SPARQL 1.2 | [Standard] | [w3.org/TR/sparql12-query](https://www.w3.org/TR/sparql12-query/) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18) |
| agent interoperability | [Experimental] | [a2a-protocol.org](https://a2a-protocol.org/) |
| world model | [Experimental] | [openreview.net/forum?id=BZ5a1r-kVsf](https://openreview.net/forum?id=BZ5a1r-kVsf) |
| self-refining ontology | [Experimental] | [arxiv.org/abs/2404.13501](https://arxiv.org/abs/2404.13501) |

## Sources cited in more than one chapter

37 links are cited by two or more chapters. Treat these as the skeleton of the book.

| Source | Chapters |
|---|---|
| [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) | 1, 3, 5, 7, 11, 12, 35 |
| [state graph, superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) | 1, 2, 18, 19, 20, 25 |
| [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) | 1, 2, 18, 20, 25 |
| [Shapes Constraint Language](https://www.w3.org/TR/shacl/) | 4, 12, 13, 28, 32 |
| [PROV-O](https://www.w3.org/TR/prov-o/) | 14, 15, 23, 28 |
| [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) | 1, 4, 5, 7 |
| [RAG](https://arxiv.org/abs/2005.11401) | 6, 15, 17 |
| [audit log](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | 26, 30, 34 |
| [checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) | 18, 19, 21 |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | 6, 15, 17 |
| [ISO/IEC 25012](https://www.iso.org/standard/35736.html) | 13, 14, 15 |
| [bitemporal](https://www.iso.org/standard/76583.html) | 16, 19, 27 |
| [A2A](https://a2a-protocol.org/) | 2, 35 |
| [ReAct](https://arxiv.org/abs/2210.03629) | 1, 18 |
| [episodic memory](https://arxiv.org/abs/2404.13501) | 27, 35 |
| [HippoRAG](https://arxiv.org/abs/2405.14831) | 6, 17 |
| [LightRAG](https://arxiv.org/abs/2410.05779) | 6, 17 |
| [knowledge graph](https://blog.google/products/search/introducing-knowledge-graph-things-not/) | 1, 5 |
| [topological sort](https://dl.acm.org/doi/10.1145/368996.369025) | 2, 9 |
| [usage tracking](https://docs.claude.com/en/docs/build-with-claude/token-counting) | 20, 24 |
| [offloading](https://docs.langchain.com/oss/python/langgraph/memory) | 24, 27 |
| [Graphiti / Zep](https://github.com/getzep/graphiti) | 16, 17 |
| [harness](https://github.com/langchain-ai/deepagents) | 1, 2 |
| [circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html) | 20, 22 |
| [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) | 2, 30 |
| [Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18) | 25, 35 |
| [MCP](https://modelcontextprotocol.io/specification/2026-07-28) | 1, 2 |
| [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) | 5, 11 |
| [super node](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) | 8, 33 |
| [competency question](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) | 12, 13 |
| [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 2, 24 |
| [ISO/IEC 9075-16:2023](https://www.iso.org/standard/79473.html) | 3, 11 |
| [read timestamp](https://www.postgresql.org/docs/current/transaction-iso.html) | 29, 31 |
| [write-ahead log](https://www.sqlite.org/wal.html) | 21, 30 |
| [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) | 12, 13 |
| [owl:sameAs](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) | 14, 27 |
| [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) | 4, 11 |

---

Found a dead link, or think a status label is wrong? [Open a label objection](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) — English is fine. [Experimental] becoming [De facto], and [De facto] becoming [Standard], is going to happen. Missing those moves is the most common way this book goes stale.

[Table of contents](README.en.md)
