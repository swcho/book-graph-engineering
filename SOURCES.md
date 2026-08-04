# 출처 링크 모음

**한국어** | [English](SOURCES.en.md) | [책 전체 목차로 돌아가기](README.md)

본문 각 장 첫머리의 키워드 상자에 걸린 1차 출처를 한곳에 모았습니다. 링크 172개, 키워드 228개이고 확인 시점은 2026년 8월입니다.

공식 명세, 제품 공식 문서, RFC, 논문, 벤더 공식 블로그, 공식 저장소만 넣었습니다. 블로그 요약글이나 2차 출처는 없습니다. 출처를 못 찾은 키워드는 상자에서 뺐거나 [실험]으로 내렸습니다.

죽은 링크를 발견하면 그 키워드는 다시 봐야 합니다. 출처가 사라졌다는 건 그 개념의 근거가 흔들렸다는 뜻일 수 있으니까요.

## 상태 표시가 뜻하는 것

| 표시 | 뜻 | 개수 |
|---|---|---|
| **[표준]** | 공식 명세가 있다. ISO/IEC, W3C, RFC | 62 |
| **[사실상 표준]** | 명세는 없지만 업계가 널리 쓴다 | 142 |
| **[실험]** | 아직 자리를 잡는 중이다 | 24 |

트랙 1(지식 그래프)과 트랙 2(에이전트 그래프)의 성숙도 차이가 이 표에 그대로 나옵니다. [표준]은 대부분 3부 쪽에, [실험]은 대부분 4부 쪽에 몰려 있습니다.

## 장별 출처

### 1부 — 뿌리: 그래프는 어디에 있었나

#### 1장 — [그래프로 다시 읽는 AI의 60년](content/ch01/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 트랜스포머 | [사실상 표준] | [Transformer](https://arxiv.org/abs/1706.03762) |
| 규모의 법칙 | [실험] | [scaling laws](https://arxiv.org/abs/2001.08361) |
| 생각과 행동의 교차 | [사실상 표준] | [ReAct](https://arxiv.org/abs/2210.03629) |
| 지식 그래프 | [사실상 표준] | [knowledge graph](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| RDF 1.2 개념과 추상 구문 | [표준] | [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) |
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| 모델 컨텍스트 프로토콜 | [사실상 표준] | [MCP](https://modelcontextprotocol.io/specification/2026-07-28) |
| 상태 그래프와 슈퍼스텝 | [사실상 표준] | [state graph, superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 에이전트 설계 패턴 | [사실상 표준] | [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) |
| 하네스 | [실험] | [harness](https://github.com/langchain-ai/deepagents) |

#### 2장 — [하네스 엔지니어링에서 그래프 엔지니어링으로](content/ch02/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 에이전트 설계 패턴 | [사실상 표준] | [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) |
| 컨텍스트 엔지니어링 | [사실상 표준] | [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 에이전트 하네스 | [실험] | [agent harness](https://github.com/langchain-ai/deepagents) |
| 상태 그래프와 슈퍼스텝 | [사실상 표준] | [state graph, superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 모델 컨텍스트 프로토콜 | [사실상 표준] | [MCP](https://modelcontextprotocol.io/specification/2026-07-28) |
| 에이전트 규약 파일 | [사실상 표준] | [AGENTS.md](https://agents.md/) |
| 에이전트 간 통신 프로토콜 | [실험] | [A2A](https://a2a-protocol.org/) |
| 위상 정렬 | [표준] | [topological sort](https://dl.acm.org/doi/10.1145/368996.369025) |
| 이벤트 소싱 | [사실상 표준] | [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) |

#### 3장 — [다리 일곱 개를 건널 수 없었던 이유, 그리고 표가 이긴 이유](content/ch03/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 쾨니히스베르크 다리 문제 | [표준] | [Seven Bridges of Königsberg](https://scholarlycommons.pacific.edu/euler-works/53/) |
| 차수 | [표준] | [degree](https://scholarlycommons.pacific.edu/euler-works/53/) |
| 관계형 모델 | [표준] | [relational model](https://dl.acm.org/doi/10.1145/362384.362685) |
| 재귀 공통 테이블 식 | [표준] | [recursive CTE](https://www.sqlite.org/lang_with.html) |
| 트랜잭션 | [표준] | [transaction, ACID](https://www.sqlite.org/transactional.html) |
| 속성 그래프 질의 SQL/PGQ | [표준] | [ISO/IEC 9075-16:2023](https://www.iso.org/standard/79473.html) |
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |

#### 4장 — [시맨틱 웹은 왜 실패한 것처럼 보였나](content/ch04/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| RDF 1.2 개념과 추상 구문 | [표준] | [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) |
| Turtle 문법 | [표준] | [RDF 1.1 Turtle](https://www.w3.org/TR/turtle/) |
| SPARQL 1.1 질의 | [표준] | [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) |
| OWL 2 개요 | [표준] | [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/) |
| SHACL 형태 제약 | [표준] | [Shapes Constraint Language](https://www.w3.org/TR/shacl/) |
| JSON-LD 1.1 | [표준] | [JSON for Linking Data](https://www.w3.org/TR/json-ld11/) |
| 공용 어휘 | [사실상 표준] | [schema.org](https://schema.org/docs/documents.html) |
| 연결 데이터 원칙 | [사실상 표준] | [Linked Data](https://www.w3.org/DesignIssues/LinkedData.html) |

#### 5장 — [문자열이 아니라 사물](content/ch05/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 지식 그래프 선언 | [사실상 표준] | [things, not strings](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| Cypher 질의 언어 | [사실상 표준] | [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) |
| RDF-star 트리플 항 | [표준] | [RDF 1.2 triple terms](https://www.w3.org/TR/rdf12-concepts/) |
| 이름 붙인 그래프 | [표준] | [RDF Datasets](https://www.w3.org/TR/rdf11-datasets/) |
| 임베디드 그래프 엔진 | [사실상 표준] | [Kuzu](https://github.com/kuzudb/kuzu) |

#### 6장 — [벡터에 녹인 관계를 되찾는 데 10년이 걸렸다](content/ch06/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 그래프 신경망 개괄 | [사실상 표준] | [Graph Neural Networks: A Review](https://arxiv.org/abs/1812.08434) |
| 메시지 패싱 | [사실상 표준] | [Neural Message Passing](https://arxiv.org/abs/1704.01212) |
| 그래프 합성곱 | [사실상 표준] | [GCN](https://arxiv.org/abs/1609.02907) |
| 지식 그래프 임베딩 | [사실상 표준] | [TransE](https://papers.nips.cc/paper/5071-translating-embeddings-for-modeling-multi-relational-data) |
| 검색 증강 생성 | [사실상 표준] | [RAG](https://arxiv.org/abs/2005.11401) |
| 그래프 기반 RAG | [사실상 표준] | [Microsoft GraphRAG](https://github.com/microsoft/graphrag) |
| 경량 그래프 RAG | [실험] | [LightRAG](https://arxiv.org/abs/2410.05779) |
| 연상 기억형 RAG | [실험] | [HippoRAG](https://arxiv.org/abs/2405.14831) |

### 2부 — 그래프의 기초 문법

#### 7장 — [노드 하나 잘못 그려서 3주를 날렸다](content/ch07/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 프로퍼티 그래프 자료 모델 | [표준] | [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/76120.html) |
| RDF 자료 모델 | [표준] | [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) |
| 노드 라벨과 관계 타입 | [사실상 표준] | [Cypher: patterns](https://neo4j.com/docs/cypher-manual/current/patterns/) |
| 관계의 구체화 | [표준] | [reification](https://www.w3.org/TR/rdf12-schema/) |
| 이분 그래프 | [사실상 표준] | [bipartite graph](https://networkx.org/documentation/stable/reference/algorithms/bipartite.html) |
| 다중 그래프와 자기 루프 | [사실상 표준] | [multigraph, self-loop](https://networkx.org/documentation/stable/reference/classes/multigraph.html) |

#### 8장 — [그래프는 메모리에서 이렇게 생겼다](content/ch08/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 압축 희소 행 형식 | [사실상 표준] | [CSR, Compressed Sparse Row](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.html) |
| 인덱스 없는 인접성 | [사실상 표준] | [index-free adjacency](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/) |
| 인접 행렬과 인접 리스트 | [사실상 표준] | [adjacency matrix / list](https://networkx.org/documentation/stable/reference/convert.html) |
| 슈퍼 노드 | [사실상 표준] | [super node](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| 그래프 재배치 | [실험] | [graph reordering](https://arxiv.org/abs/1602.08820) |
| 페이지 캐시와 지역성 | [사실상 표준] | [locality of reference](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html) |

#### 9장 — [몇 다리 건너인지 세다가 서버가 죽었다](content/ch09/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 너비 우선 탐색 | [사실상 표준] | [BFS](https://networkx.org/documentation/stable/reference/algorithms/traversal.html) |
| 양방향 탐색 | [사실상 표준] | [bidirectional search](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.unweighted.bidirectional_shortest_path.html) |
| 다익스트라 최단 경로 | [표준] | [Dijkstra's algorithm](https://link.springer.com/article/10.1007/BF01386390) |
| 벨만-포드 | [사실상 표준] | [Bellman-Ford](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.bellman_ford_path.html) |
| 휴리스틱 탐색 | [사실상 표준] | [A*](https://ieeexplore.ieee.org/document/4082128) |
| 위상 정렬 | [표준] | [topological sort](https://dl.acm.org/doi/10.1145/368996.369025) |
| 가변 길이 경로 질의 | [사실상 표준] | [Cypher variable-length patterns](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-patterns/) |

#### 10장 — [누가 중요한 노드인가](content/ch10/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 중심성 지표들 | [사실상 표준] | [centrality measures](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) |
| 매개 중심성 고속 계산 | [사실상 표준] | [Brandes' algorithm](https://www.tandfonline.com/doi/abs/10.1080/0022250X.2001.9990249) |
| 페이지랭크 | [사실상 표준] | [PageRank](http://ilpubs.stanford.edu:8090/422/) |
| 모듈러리티 | [사실상 표준] | [modularity](https://arxiv.org/abs/cond-mat/0308217) |
| 루뱅 커뮤니티 탐지 | [사실상 표준] | [Louvain method](https://arxiv.org/abs/0803.0476) |
| 라이덴 알고리즘 | [사실상 표준] | [Leiden algorithm](https://www.nature.com/articles/s41598-019-41695-z) |
| 해상도 한계 | [사실상 표준] | [resolution limit](https://www.pnas.org/doi/10.1073/pnas.0605965104) |
| 라벨 전파 | [사실상 표준] | [label propagation](https://arxiv.org/abs/0709.2938) |

#### 11장 — [같은 질문, 세 가지 언어](content/ch11/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| 속성 그래프 질의 SQL/PGQ | [표준] | [ISO/IEC 9075-16:2023](https://www.iso.org/standard/79473.html) |
| Cypher 질의 언어 | [사실상 표준] | [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) |
| SPARQL 1.1 질의 | [표준] | [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) |
| SPARQL 속성 경로 | [표준] | [property paths](https://www.w3.org/TR/sparql11-query/#propertypaths) |
| Gremlin 순회 언어 | [사실상 표준] | [Apache TinkerPop](https://tinkerpop.apache.org/docs/current/reference/) |
| GQL 표준화 경과 | [사실상 표준] | [GQL Standards](https://www.gqlstandards.org/) |

### 3부 — 지식 그래프 엔지니어링 (트랙 1)

#### 12장 — [온톨로지를 3주 만에 갈아엎은 이야기](content/ch12/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| SHACL 형태 제약 | [표준] | [Shapes Constraint Language](https://www.w3.org/TR/shacl/) |
| OWL 2 프로필 | [표준] | [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) |
| RDF 스키마 | [표준] | [RDF Schema 1.1](https://www.w3.org/TR/rdf11-schema/) |
| 공용 어휘 | [사실상 표준] | [schema.org](https://schema.org/docs/schemas.html) |
| 개념 체계 어휘 | [표준] | [SKOS](https://www.w3.org/TR/skos-reference/) |
| 역량 질문 | [사실상 표준] | [competency question](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |
| 그래프 스키마 선언 | [표준] | [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/76120.html) |

#### 13장 — [검증하지 않은 그래프는 그냥 링크 뭉치다](content/ch13/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| SHACL 형태 제약 | [표준] | [Shapes Constraint Language](https://www.w3.org/TR/shacl/) |
| 제약 위반 심각도 | [표준] | [sh:severity](https://www.w3.org/TR/shacl/#severity) |
| SHACL 고급 기능 | [표준] | [SHACL Advanced Features](https://www.w3.org/TR/shacl-af/) |
| OWL 2 프로필 | [표준] | [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) |
| 데이터 품질 차원 | [표준] | [ISO/IEC 25012](https://www.iso.org/standard/35736.html) |
| 그래프 스멜 | [실험] | [graph smell](https://www.w3.org/TR/shacl/) |
| 역량 질의 회귀 테스트 | [실험] | [competency question regression](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |

#### 14장 — [같은 사람이 노드 네 개로 앉아 있다](content/ch14/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 엔티티 해상도 | [사실상 표준] | [entity resolution](https://www.vldb.org/pvldb/vol11/p1454-mudgal.pdf) |
| 블로킹 | [사실상 표준] | [blocking](https://dl.acm.org/doi/10.1145/3355491.3355496) |
| 확률적 레코드 연결 | [사실상 표준] | [Fellegi-Sunter model](https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049) |
| 동일성 선언 | [표준] | [owl:sameAs](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| 느슨한 동일성 | [표준] | [skos:closeMatch](https://www.w3.org/TR/skos-reference/#mapping) |
| 생존 규칙 | [실험] | [survivorship rules](https://www.iso.org/standard/35736.html) |
| 출처 추적 | [표준] | [PROV-O](https://www.w3.org/TR/prov-o/) |

#### 15장 — [문서 1만 건에서 트리플을 뽑았더니 절반이 거짓이었다](content/ch15/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 정보 추출 | [사실상 표준] | [information extraction](https://aclanthology.org/D19-1522/) |
| 근거 기반 생성 | [사실상 표준] | [grounded generation](https://arxiv.org/abs/2005.11401) |
| 자기 일관성 | [사실상 표준] | [self-consistency](https://arxiv.org/abs/2203.11171) |
| 출처 표현 | [표준] | [PROV-O](https://www.w3.org/TR/prov-o/) |
| 정밀도와 재현율 | [표준] | [precision, recall](https://www.iso.org/standard/35736.html) |
| 구조화 출력 | [사실상 표준] | [structured output](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview) |
| 그래프 추출 파이프라인 | [사실상 표준] | [Microsoft GraphRAG indexing](https://github.com/microsoft/graphrag) |

#### 16장 — [어제는 맞았고 오늘은 틀리다](content/ch16/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 이중 시간 | [사실상 표준] | [bitemporal](https://www.iso.org/standard/76583.html) |
| 유효 시간 | [표준] | [valid time](https://www.iso.org/standard/76583.html) |
| 기록 시간 | [표준] | [transaction time](https://www.iso.org/standard/76583.html) |
| 시간 인식 그래프 | [실험] | [Graphiti / Zep](https://github.com/getzep/graphiti) |
| 시각 표현 표준 | [표준] | [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) |
| RDF 시간 온톨로지 | [표준] | [OWL-Time](https://www.w3.org/TR/owl-time/) |
| 느리게 변하는 차원 | [사실상 표준] | [slowly changing dimension](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) |

#### 17장 — [벡터만으로 답이 안 나오는 질문들](content/ch17/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 그래프 기반 RAG | [사실상 표준] | [Microsoft GraphRAG](https://github.com/microsoft/graphrag) |
| 경량 그래프 RAG | [실험] | [LightRAG](https://arxiv.org/abs/2410.05779) |
| 연상 기억형 RAG | [실험] | [HippoRAG](https://arxiv.org/abs/2405.14831) |
| 시간 인식 메모리 그래프 | [실험] | [Graphiti](https://github.com/getzep/graphiti) |
| 순위 융합 | [사실상 표준] | [reciprocal rank fusion](https://dl.acm.org/doi/10.1145/1571941.1572114) |
| 검색 증강 생성 | [사실상 표준] | [RAG](https://arxiv.org/abs/2005.11401) |
| 하이브리드 검색 | [사실상 표준] | [hybrid search](https://www.elastic.co/what-is/hybrid-search) |

### 4부 — 에이전트 그래프 엔지니어링 (트랙 2)

#### 18장 — [체인은 어디서 부러지는가](content/ch18/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 에이전트 설계 패턴 | [사실상 표준] | [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) |
| 상태 그래프 | [사실상 표준] | [StateGraph](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 체크포인트 | [사실상 표준] | [checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 프롬프트 연쇄 | [사실상 표준] | [prompt chaining](https://www.anthropic.com/engineering/building-effective-agents) |
| 순환 복잡도 | [표준] | [cyclomatic complexity](https://ieeexplore.ieee.org/document/1702388) |
| 내구성 있는 실행 | [사실상 표준] | [durable execution](https://docs.temporal.io/temporal) |
| 생각과 행동의 교차 | [사실상 표준] | [ReAct](https://arxiv.org/abs/2210.03629) |

#### 19장 — [상태 그래프와 리듀서, 그리고 슈퍼스텝](content/ch19/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 상태 그래프 | [사실상 표준] | [StateGraph](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 리듀서 | [사실상 표준] | [reducer](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 슈퍼스텝 | [사실상 표준] | [superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 프리겔 계산 모형 | [사실상 표준] | [Pregel](https://dl.acm.org/doi/10.1145/1807167.1807184) |
| 벌크 동기 병렬 | [사실상 표준] | [Bulk Synchronous Parallel](https://dl.acm.org/doi/10.1145/79173.79181) |
| 체크포인트와 지속성 | [사실상 표준] | [persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 갱신 유실 | [표준] | [lost update](https://www.iso.org/standard/76583.html) |

#### 20장 — [끝나지 않는 루프를 끝내는 법](content/ch20/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 종료 조건 | [사실상 표준] | [termination condition](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 재귀 한도 | [사실상 표준] | [recursion limit](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 평가자-최적화 패턴 | [사실상 표준] | [evaluator-optimizer](https://www.anthropic.com/engineering/building-effective-agents) |
| 토큰 사용량 추적 | [사실상 표준] | [usage tracking](https://docs.claude.com/en/docs/build-with-claude/token-counting) |
| 조기 종료 | [사실상 표준] | [early stopping](https://www.deeplearningbook.org/contents/regularization.html) |
| 회로 차단기 | [사실상 표준] | [circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html) |
| 속도 제한 | [사실상 표준] | [rate limiting](https://datatracker.ietf.org/doc/html/rfc6585) |

#### 21장 — [프로세스가 죽어도 작업은 살아 있어야 한다](content/ch21/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 체크포인터 | [사실상 표준] | [checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 내구성 있는 실행 | [사실상 표준] | [durable execution](https://docs.temporal.io/evaluate/understanding-temporal) |
| 멱등성 | [표준] | [idempotency](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2) |
| 멱등 키 | [사실상 표준] | [idempotency key](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header) |
| 정확히 한 번 | [사실상 표준] | [exactly-once](https://kafka.apache.org/documentation/#semantics) |
| 스레드 아이디 | [사실상 표준] | [thread id](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 쓰기 전 로그 | [사실상 표준] | [write-ahead log](https://www.sqlite.org/wal.html) |

#### 22장 — [되돌릴 수 없는 일을 되갚는 법](content/ch22/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 지수 백오프 | [사실상 표준] | [exponential backoff](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| 흔들기 | [사실상 표준] | [jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| 재시도 폭풍 | [사실상 표준] | [retry storm](https://sre.google/sre-book/handling-overload/) |
| 회로 차단기 | [사실상 표준] | [circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html) |
| 사가 패턴 | [사실상 표준] | [saga](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) |
| 보상 트랜잭션 | [사실상 표준] | [compensating transaction](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) |
| 데드레터 큐 | [사실상 표준] | [dead letter queue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) |
| 재시도 후 대기 | [표준] | [Retry-After](https://datatracker.ietf.org/doc/html/rfc9110#field.retry-after) |

#### 23장 — [사람이 끼어드는 지점](content/ch23/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 사람 개입 | [사실상 표준] | [human in the loop](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| 중단점 | [사실상 표준] | [interrupt](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| 재개 명령 | [사실상 표준] | [Command(resume)](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| 승인 관문 | [사실상 표준] | [approval gate](https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper) |
| 등급 올리기 | [사실상 표준] | [escalation](https://sre.google/workbook/incident-response/) |
| 감사 추적 | [표준] | [audit trail](https://www.w3.org/TR/prov-o/) |
| 네 눈 원칙 | [사실상 표준] | [four-eyes principle](https://www.bis.org/publ/bcbs230.pdf) |

#### 24장 — [컨텍스트가 꽉 찼습니다](content/ch24/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 컨텍스트 창 | [사실상 표준] | [context window](https://docs.claude.com/en/docs/build-with-claude/context-windows) |
| 컨텍스트 엔지니어링 | [실험] | [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 압축 | [실험] | [compaction](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 오프로딩 | [실험] | [offloading](https://docs.langchain.com/oss/python/langgraph/memory) |
| 프롬프트 캐싱 | [사실상 표준] | [prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) |
| 장기 기억 저장소 | [사실상 표준] | [long-term memory store](https://docs.langchain.com/oss/python/langgraph/memory) |
| 토큰 계산 | [사실상 표준] | [token counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |

#### 25장 — [여섯 가지 위상, 그리고 도구를 꽂는 구멍](content/ch25/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 오케스트레이터-워커 | [사실상 표준] | [orchestrator-workers](https://www.anthropic.com/engineering/building-effective-agents) |
| 팬아웃·팬인 | [사실상 표준] | [fan-out/fan-in](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-cloud-backup) |
| 라우팅 | [사실상 표준] | [routing](https://www.anthropic.com/engineering/building-effective-agents) |
| 평가자-최적화 | [사실상 표준] | [evaluator-optimizer](https://www.anthropic.com/engineering/building-effective-agents) |
| 꼬리 지연 | [사실상 표준] | [tail latency](https://research.google/pubs/the-tail-at-scale/) |
| 모델 컨텍스트 프로토콜 | [사실상 표준] | [Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18) |
| 도구 스키마 | [사실상 표준] | [tool schema](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) |
| Send API | [사실상 표준] | [Send](https://docs.langchain.com/oss/python/langgraph/graph-api) |

#### 26장 — [무엇을 못 하게 할 것인가](content/ch26/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 최소 권한 | [사실상 표준] | [least privilege](https://csrc.nist.gov/glossary/term/least_privilege) |
| 허용 목록 | [사실상 표준] | [allowlist](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) |
| 프롬프트 인젝션 | [사실상 표준] | [prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| 간접 인젝션 | [사실상 표준] | [indirect prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| 폭발 반경 | [사실상 표준] | [blast radius](https://sre.google/sre-book/addressing-cascading-failures/) |
| 권한 상승 | [표준] | [privilege escalation](https://attack.mitre.org/tactics/TA0004/) |
| 샌드박스 | [사실상 표준] | [sandbox](https://gvisor.dev/docs/) |
| 감사 로그 | [표준] | [audit log](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

### 5부 — 두 그래프가 만나는 곳

#### 27장 — [에이전트에게 기억을 주는 가장 싼 방법](content/ch27/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 장기 기억 | [사실상 표준] | [long-term memory](https://docs.langchain.com/oss/python/langgraph/memory) |
| 에피소드 기억 | [실험] | [episodic memory](https://arxiv.org/abs/2404.13501) |
| 시간 인식 지식 그래프 | [실험] | [temporal knowledge graph](https://arxiv.org/abs/2501.13956) |
| 하이브리드 검색 | [사실상 표준] | [hybrid retrieval](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) |
| 망각 곡선 | [실험] | [decay policy](https://arxiv.org/abs/2310.08560) |
| 개체 해상도 | [사실상 표준] | [entity resolution](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| 유효 시간 | [표준] | [valid time](https://www.iso.org/standard/76583.html) |

#### 28장 — [에이전트가 스스로 그래프를 넓히다](content/ch28/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 지식 그래프 완성 | [실험] | [knowledge graph completion](https://arxiv.org/abs/2002.00388) |
| 출처 기록 | [표준] | [provenance](https://www.w3.org/TR/prov-o/) |
| 철회 | [사실상 표준] | [retraction](https://www.w3.org/TR/prov-o/#Invalidation) |
| 진리 유지 시스템 | [실험] | [truth maintenance](https://dl.acm.org/doi/10.1145/321978.321979) |
| 스키마 드리프트 | [사실상 표준] | [schema drift](https://www.w3.org/TR/shacl/) |
| 자기 학습 편향 | [실험] | [self-training bias](https://arxiv.org/abs/2305.17493) |
| 제약 검증 | [표준] | [SHACL validation](https://www.w3.org/TR/shacl/) |

#### 29장 — [하나의 백본](content/ch29/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 참조 아키텍처 | [사실상 표준] | [reference architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/) |
| 계보 추적 | [표준] | [data lineage](https://www.w3.org/TR/prov-o/#Derivation) |
| 읽은 시점 기록 | [사실상 표준] | [read timestamp](https://www.postgresql.org/docs/current/transaction-iso.html) |
| 다중 저장소 | [사실상 표준] | [polyglot persistence](https://martinfowler.com/bliki/PolyglotPersistence.html) |
| 경계 컨텍스트 | [사실상 표준] | [bounded context](https://martinfowler.com/bliki/BoundedContext.html) |
| 아키텍처 적합성 함수 | [사실상 표준] | [fitness function](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development) |
| 쓰기 부하 분리 | [사실상 표준] | [write path separation](https://neo4j.com/docs/operations-manual/current/performance/) |

### 6부 — 백본: 상태 관리 엔진

#### 30장 — [무엇이 언제 바뀌었는지 아무도 모른다](content/ch30/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 이벤트 소싱 | [사실상 표준] | [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) |
| 추가 전용 로그 | [사실상 표준] | [append-only log](https://kafka.apache.org/documentation/#design) |
| 재생 | [사실상 표준] | [replay](https://martinfowler.com/eaaDev/EventSourcing.html) |
| 스냅숏 | [사실상 표준] | [snapshot](https://www.sqlite.org/wal.html) |
| 쓰기 전 로그 | [사실상 표준] | [write-ahead log](https://www.postgresql.org/docs/current/wal-intro.html) |
| 명령-조회 분리 | [사실상 표준] | [CQRS](https://martinfowler.com/bliki/CQRS.html) |
| 해시 고리 | [표준] | [hash chain](https://datatracker.ietf.org/doc/html/rfc6962) |
| 감사 추적 | [표준] | [audit trail](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

#### 31장 — [두 에이전트가 같은 노드를 동시에 고쳤다](content/ch31/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 잃어버린 갱신 | [표준] | [lost update](https://www.postgresql.org/docs/current/transaction-iso.html) |
| 낙관적 잠금 | [사실상 표준] | [optimistic locking](https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html) |
| 비관적 잠금 | [사실상 표준] | [pessimistic locking](https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html) |
| 비교 후 교체 | [표준] | [compare-and-swap](https://en.cppreference.com/w/cpp/atomic/atomic/compare_exchange) |
| 직렬화 가능 | [표준] | [serializable](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE) |
| 충돌 없는 자료형 | [실험] | [CRDT](https://inria.hal.science/inria-00555588) |
| 교착 | [표준] | [deadlock](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS) |
| 쓰기 편중 | [표준] | [write skew](https://www.postgresql.org/docs/current/transaction-iso.html) |

#### 32장 — [스키마를 바꾸는 날](content/ch32/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 확장-수축 | [사실상 표준] | [expand and contract](https://martinfowler.com/bliki/ParallelChange.html) |
| 무중단 배포 | [사실상 표준] | [zero-downtime deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html) |
| 양쪽 쓰기 | [사실상 표준] | [dual write](https://martinfowler.com/bliki/ParallelChange.html) |
| 백필 | [사실상 표준] | [backfill](https://cloud.google.com/architecture/database-migration-concepts-principles-part-1) |
| 스키마 진화 | [사실상 표준] | [schema evolution](https://avro.apache.org/docs/current/specification/#schema-resolution) |
| 제약 검증 | [표준] | [SHACL](https://www.w3.org/TR/shacl/) |
| 하위 호환 | [사실상 표준] | [backward compatibility](https://protobuf.dev/programming-guides/proto3/#updating) |

### 7부 — 운영

#### 33장 — [쿼리 플랜을 읽으면 비용이 보인다](content/ch33/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 쿼리 플랜 | [사실상 표준] | [query plan](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/) |
| 실행 계획 설명 | [사실상 표준] | [EXPLAIN](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| 곱집합 | [표준] | [cartesian product](https://www.postgresql.org/docs/current/queries-table-expressions.html) |
| 인덱스 | [사실상 표준] | [index](https://neo4j.com/docs/cypher-manual/current/indexes/) |
| 느린 쿼리 로그 | [사실상 표준] | [slow query log](https://dev.mysql.com/doc/refman/8.0/en/slow-query-log.html) |
| 암달의 법칙 | [표준] | [Amdahl's law](https://dl.acm.org/doi/10.1145/1465482.1465560) |
| 일괄 적재 | [사실상 표준] | [bulk load](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/) |

#### 34장 — [그래프에서 개인정보를 지운다는 것](content/ch34/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 삭제권 | [표준] | [right to erasure](https://gdpr-info.eu/art-17-gdpr/) |
| 가명화 | [표준] | [pseudonymisation](https://gdpr-info.eu/art-4-gdpr/) |
| 재식별 | [사실상 표준] | [re-identification](https://www.nist.gov/publications/de-identification-personal-information) |
| k-익명성 | [사실상 표준] | [k-anonymity](https://dataprivacylab.org/dataprivacy/projects/kanonymity/kanonymity.pdf) |
| 차등 정보보호 | [사실상 표준] | [differential privacy](https://www.microsoft.com/en-us/research/publication/differential-privacy/) |
| 데이터 최소화 | [표준] | [data minimisation](https://gdpr-info.eu/art-5-gdpr/) |
| 보존 기간 | [표준] | [retention period](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

### 8부 — 미래

#### 35장 — [3년 뒤 틀렸을 가능성이 가장 큰 주장 5개](content/ch35/code/README.md)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 반증 가능성 | [사실상 표준] | [falsifiability](https://plato.stanford.edu/entries/popper/) |
| ISO GQL | [표준] | [ISO/IEC 39075](https://www.iso.org/standard/76120.html) |
| SPARQL 1.2 | [표준] | [SPARQL 1.2](https://www.w3.org/TR/sparql12-query/) |
| 모델 컨텍스트 프로토콜 | [사실상 표준] | [MCP](https://modelcontextprotocol.io/specification/2025-06-18) |
| 에이전트 상호운용 | [실험] | [agent interoperability](https://a2a-protocol.org/) |
| 세계 모형 | [실험] | [world model](https://openreview.net/forum?id=BZ5a1r-kVsf) |
| 자기수정 온톨로지 | [실험] | [self-refining ontology](https://arxiv.org/abs/2404.13501) |

## 여러 장에서 함께 쓰는 출처

링크 37개가 두 장 이상에서 걸립니다. 여기 있는 것들이 이 책의 뼈대라고 봐도 됩니다.

| 출처 | 걸린 장 |
|---|---|
| [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) | 1장, 3장, 5장, 7장, 11장, 12장, 35장 |
| [state graph, superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) | 1장, 2장, 18장, 19장, 20장, 25장 |
| [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) | 1장, 2장, 18장, 20장, 25장 |
| [Shapes Constraint Language](https://www.w3.org/TR/shacl/) | 4장, 12장, 13장, 28장, 32장 |
| [PROV-O](https://www.w3.org/TR/prov-o/) | 14장, 15장, 23장, 28장 |
| [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) | 1장, 4장, 5장, 7장 |
| [RAG](https://arxiv.org/abs/2005.11401) | 6장, 15장, 17장 |
| [audit log](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | 26장, 30장, 34장 |
| [checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) | 18장, 19장, 21장 |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | 6장, 15장, 17장 |
| [ISO/IEC 25012](https://www.iso.org/standard/35736.html) | 13장, 14장, 15장 |
| [bitemporal](https://www.iso.org/standard/76583.html) | 16장, 19장, 27장 |
| [A2A](https://a2a-protocol.org/) | 2장, 35장 |
| [ReAct](https://arxiv.org/abs/2210.03629) | 1장, 18장 |
| [episodic memory](https://arxiv.org/abs/2404.13501) | 27장, 35장 |
| [HippoRAG](https://arxiv.org/abs/2405.14831) | 6장, 17장 |
| [LightRAG](https://arxiv.org/abs/2410.05779) | 6장, 17장 |
| [knowledge graph](https://blog.google/products/search/introducing-knowledge-graph-things-not/) | 1장, 5장 |
| [topological sort](https://dl.acm.org/doi/10.1145/368996.369025) | 2장, 9장 |
| [usage tracking](https://docs.claude.com/en/docs/build-with-claude/token-counting) | 20장, 24장 |
| [offloading](https://docs.langchain.com/oss/python/langgraph/memory) | 24장, 27장 |
| [Graphiti / Zep](https://github.com/getzep/graphiti) | 16장, 17장 |
| [harness](https://github.com/langchain-ai/deepagents) | 1장, 2장 |
| [circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html) | 20장, 22장 |
| [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) | 2장, 30장 |
| [Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18) | 25장, 35장 |
| [MCP](https://modelcontextprotocol.io/specification/2026-07-28) | 1장, 2장 |
| [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) | 5장, 11장 |
| [super node](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) | 8장, 33장 |
| [competency question](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) | 12장, 13장 |
| [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 2장, 24장 |
| [ISO/IEC 9075-16:2023](https://www.iso.org/standard/79473.html) | 3장, 11장 |
| [read timestamp](https://www.postgresql.org/docs/current/transaction-iso.html) | 29장, 31장 |
| [write-ahead log](https://www.sqlite.org/wal.html) | 21장, 30장 |
| [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) | 12장, 13장 |
| [owl:sameAs](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) | 14장, 27장 |
| [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) | 4장, 11장 |

---

죽은 링크를 보셨거나 상태 라벨이 틀렸다고 보시면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요. [실험]이 [사실상 표준]으로, [사실상 표준]이 [표준]으로 올라가는 일은 반드시 생기고, 그 이동을 놓치는 게 이 책이 낡는 가장 흔한 방식입니다.

[책 전체 목차](README.md)
