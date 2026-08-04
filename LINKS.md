# 바깥 읽을거리

[책 전체 목차로 돌아가기](README.md)

이 책에 **쓰지 않은** 자료만 모았습니다. 본문 키워드 상자에 걸린 1차 출처는 [출처 링크 모음](SOURCES.md)에 따로 있고, 여기 있는 것은 그 172개와 겹치지 않습니다.

기준은 하나입니다. 책을 읽다가 "이건 더 파고 싶은데"가 생겼을 때 다음으로 열 만한 것. 그래서 소개 글은 안 쓰고 표만 뒀습니다.

"관련 장"은 그 자료가 도움이 되는 장입니다. 책에서 다루지 않은 주제면 "없음"으로 적었습니다. 없음이 부실하다는 뜻은 아니고, 이 책의 범위 밖이라는 뜻입니다.

날짜 규칙은 이렇습니다. 논문은 최초 공개일, 책은 출간 연도, 계속 갱신되는 사이트와 문서는 확인일입니다. 확인일은 전부 2026-08-05입니다.

---

## 1. 그래프 이론과 네트워크 과학

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [Networks, Crowds, and Markets](https://www.cs.cornell.edu/home/kleinber/networks-book/) | Easley, Kleinberg. 네트워크를 경제학과 사회학까지 끌고 가는 교과서. 초고 무료 | 9장, 10장 | 2010 |
| [Network Science](https://networksciencebook.com/) | Barabasi. 척도 없는 네트워크와 차수 분포를 그림으로. 전문 무료 공개 | 8장, 10장 | 확인 2026-08-05 |
| [Graph Representation Learning](https://www.cs.mcgill.ca/~wlh/grl_book/) | Hamilton. 임베딩부터 GNN까지 한 권. 초고 PDF 무료 | 6장 | 2020 |
| [Graph Databases](https://neo4j.com/graph-databases-book/) | Robinson, Webber, Eifrem. 그래프 DB 실무 입문서 | 5장, 8장 | 확인 2026-08-05 |
| [Designing Data-Intensive Applications](https://dataintensive.net/) | Kleppmann. 6부에서 다룬 문제들의 원류가 대부분 여기 있습니다 | 30장, 31장, 32장 | 확인 2026-08-05 |

## 2. 그래프 표현학습과 GNN

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [DeepWalk](https://arxiv.org/abs/1403.6652) | 무작위 걸음을 문장처럼 다뤄 노드를 벡터로 | 6장 | 2014-03-26 |
| [node2vec](https://arxiv.org/abs/1607.00653) | 걸음의 편향을 두 손잡이로 조절 | 6장 | 2016-07-03 |
| [GraphSAGE](https://arxiv.org/abs/1706.02216) | 처음 보는 노드도 임베딩하는 귀납적 방법 | 6장 | 2017-06-07 |
| [Graph Attention Networks](https://arxiv.org/abs/1710.10903) | 이웃마다 다른 가중치를 학습 | 6장 | 2017-10-30 |
| [A Comprehensive Survey on Graph Neural Networks](https://arxiv.org/abs/1901.00596) | GNN 계열 전체 지도. 어디서 시작할지 모를 때 | 6장 | 2019-01-03 |
| [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/) | GNN 구현 라이브러리. 문서 | 6장 | 확인 2026-08-05 |
| [DGL](https://www.dgl.ai/) | 또 하나의 GNN 라이브러리. 대규모 학습 쪽이 강함 | 6장 | 확인 2026-08-05 |
| [Open Graph Benchmark](https://arxiv.org/abs/2005.00687) | 그래프 학습 표준 벤치마크. 논문 | 6장 | 2020-05-02 |
| [OGB 사이트](https://ogb.stanford.edu/) | 위 벤치마크의 데이터셋과 순위표 | 6장 | 확인 2026-08-05 |
| [CS224W](https://web.stanford.edu/class/cs224w/) | 스탠퍼드 그래프 머신러닝 강의. 슬라이드 공개 | 6장, 10장 | 확인 2026-08-05 |

## 3. 지식 그래프

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [Knowledge Graphs](https://arxiv.org/abs/2003.02320) | Hogan 외. 이 분야 종합 정리. 길지만 목차만 봐도 값어치 있음 | 12장, 13장 | 2020-03-04 |
| [A Review of Relational Machine Learning for Knowledge Graphs](https://arxiv.org/abs/1503.00759) | 지식 그래프 임베딩 계열의 초기 정리 | 6장 | 2015-03-02 |
| [RotatE](https://arxiv.org/abs/1902.10197) | 관계를 복소평면의 회전으로. TransE 다음으로 읽을 것 | 6장 | 2019-02-26 |
| [Unifying LLMs and Knowledge Graphs: A Roadmap](https://arxiv.org/abs/2306.08302) | 5부가 다룬 합류 지점의 지도 | 27장, 29장 | 2023-06-14 |
| [CS520](https://web.stanford.edu/class/cs520/) | 스탠퍼드 지식 그래프 강의 | 12장 | 확인 2026-08-05 |

## 4. RAG와 에이전트 논문

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) | 생각을 늘어놓게 하면 답이 좋아진다 | 없음 | 2022-01-28 |
| [Toolformer](https://arxiv.org/abs/2302.04761) | 모델이 스스로 도구 호출 자리를 배운다 | 25장 | 2023-02-09 |
| [Reflexion](https://arxiv.org/abs/2303.11366) | 말로 하는 자기 비판을 루프에 넣기 | 20장 | 2023-03-20 |
| [Generative Agents](https://arxiv.org/abs/2304.03442) | 기억, 반성, 계획을 갖춘 에이전트 25명 | 27장 | 2023-04-07 |
| [Tree of Thoughts](https://arxiv.org/abs/2305.10601) | 한 줄로 생각하지 말고 갈래를 치자 | 없음 | 2023-05-17 |
| [Lost in the Middle](https://arxiv.org/abs/2307.03172) | 긴 컨텍스트의 가운데를 모델이 잘 못 본다 | 24장 | 2023-07-06 |
| [AutoGen](https://arxiv.org/abs/2308.08155) | 대화로 협업하는 멀티 에이전트 | 25장 | 2023-08-16 |
| [Self-RAG](https://arxiv.org/abs/2310.11511) | 검색할지 말지를 모델이 정하게 | 17장 | 2023-10-17 |
| [RAG for LLMs: A Survey](https://arxiv.org/abs/2312.10997) | RAG 계열 전체 정리 | 17장 | 2023-12-18 |
| [Agentic RAG: A Survey](https://arxiv.org/abs/2501.09136) | 검색을 에이전트 루프에 넣은 흐름 정리 | 17장, 25장 | 2025-01-15 |

## 5. 분산 시스템과 상태 관리

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [Raft](https://raft.github.io/raft.pdf) | 이해할 수 있게 만든 합의 알고리즘 | 31장 | 확인 2026-08-05 |
| [Dynamo](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) | 결과적 일관성과 충돌 해결의 고전 | 31장 | 2007 |
| [Spanner](https://research.google/pubs/spanner-googles-globally-distributed-database/) | 시계를 믿고 분산 트랜잭션을 하는 법 | 31장 | 2012 |
| [Restate](https://restate.dev/) | 내구성 있는 실행 엔진. 문서 | 21장, 22장 | 확인 2026-08-05 |
| [Inngest](https://www.inngest.com/) | 이벤트 기반 잡 실행기. 문서 | 21장, 22장 | 확인 2026-08-05 |

## 6. 벤치마크와 공개 데이터

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [LDBC](https://ldbcouncil.org/) | 그래프 DB 표준 벤치마크 단체. SNB가 사실상 기준 | 33장 | 확인 2026-08-05 |
| [Wikidata](https://www.wikidata.org/) | 제일 큰 공개 지식 그래프. 스키마 설계 참고용으로도 좋음 | 12장, 14장 | 확인 2026-08-05 |
| [DBpedia](https://www.dbpedia.org/) | 위키백과를 RDF로 편 것 | 12장 | 확인 2026-08-05 |
| [YAGO](https://yago-knowledge.org/) | 위키데이터에 schema.org 어휘를 입힌 것 | 12장 | 확인 2026-08-05 |
| [ConceptNet](https://conceptnet.io/) | 상식 관계 그래프 | 없음 | 확인 2026-08-05 |

## 7. 엔진과 라이브러리

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [igraph](https://igraph.org/) | C 기반 그래프 분석 라이브러리. 파이썬과 R 바인딩 | 9장, 10장 | 확인 2026-08-05 |
| [graph-tool](https://graph-tool.skewed.de/) | 통계 쪽이 강한 파이썬 그래프 라이브러리 | 10장 | 확인 2026-08-05 |
| [cuGraph](https://github.com/rapidsai/cugraph) | GPU로 도는 그래프 알고리즘 | 없음 | 확인 2026-08-05 |
| [Neo4j GDS](https://neo4j.com/docs/graph-data-science/current/) | 중심성과 커뮤니티 알고리즘을 엔진 안에서 | 10장 | 확인 2026-08-05 |
| [Apache Jena](https://jena.apache.org/) | 자바 RDF 스택. 추론기와 SPARQL 엔진 포함 | 4장, 13장 | 확인 2026-08-05 |
| [Oxigraph](https://github.com/oxigraph/oxigraph) | 러스트로 쓴 가벼운 RDF 저장소 | 4장 | 확인 2026-08-05 |
| [RDFLib](https://rdflib.readthedocs.io/) | 파이썬 RDF 라이브러리. 예제에서 쓰는 것 | 4장, 13장 | 확인 2026-08-05 |
| [DuckPGQ](https://duckpgq.org/) | DuckDB에 SQL/PGQ를 얹은 확장 | 11장 | 확인 2026-08-05 |
| [Apache AGE](https://age.apache.org/) | PostgreSQL에 Cypher를 얹은 확장 | 11장 | 확인 2026-08-05 |
| [Memgraph](https://memgraph.com/docs) | 메모리 기반 그래프 DB | 없음 | 확인 2026-08-05 |
| [FalkorDB](https://www.falkordb.com/) | 희소 행렬로 도는 그래프 DB | 없음 | 확인 2026-08-05 |
| [NebulaGraph](https://www.nebula-graph.io/) | 분산 그래프 DB | 없음 | 확인 2026-08-05 |
| [ArangoDB](https://arangodb.com/) | 문서와 그래프를 같이 다루는 DB | 없음 | 확인 2026-08-05 |

## 8. 에이전트 프레임워크

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [AutoGen 문서](https://microsoft.github.io/autogen/) | 위 논문의 구현체 | 25장 | 확인 2026-08-05 |
| [CrewAI](https://docs.crewai.com/) | 역할을 나눈 팀 형태의 에이전트 | 25장 | 확인 2026-08-05 |
| [LlamaIndex](https://docs.llamaindex.ai/) | 색인과 검색 쪽이 두꺼운 프레임워크 | 17장 | 확인 2026-08-05 |
| [Haystack](https://haystack.deepset.ai/) | 검색 파이프라인 중심 | 17장 | 확인 2026-08-05 |
| [DSPy](https://dspy.ai/) | 프롬프트를 손으로 안 쓰고 컴파일한다는 접근 | 없음 | 확인 2026-08-05 |
| [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/) | 마이크로소프트 쪽 에이전트 SDK | 없음 | 확인 2026-08-05 |

## 9. 표준과 어휘

| 자료 | 무엇 | 관련 장 | 날짜 |
|---|---|---|---|
| [openCypher](https://opencypher.org/) | Cypher 문법 명세와 참조 구현 | 11장 | 확인 2026-08-05 |
| [PGQL](https://pgql-lang.org/) | 오라클 쪽 프로퍼티 그래프 질의 언어 | 11장 | 확인 2026-08-05 |
| [DCAT 3](https://www.w3.org/TR/vocab-dcat-3/) | 데이터 카탈로그 어휘. 메타데이터를 그래프로 적을 때 | 없음 | 확인 2026-08-05 |
| [Dublin Core](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) | 가장 오래 살아남은 메타데이터 어휘 | 없음 | 확인 2026-08-05 |

---

링크가 죽었거나 여기 있으면 좋겠는 자료를 아시면 [이슈로 알려 주세요](../../issues/new). 다만 이 페이지의 기준은 하나입니다. 1차 출처일 것, 그리고 책에 이미 쓴 것이 아닐 것.

[책 전체 목차](README.md)
