# 1장 — 그래프로 다시 읽는 AI의 60년

`1부 · 뿌리: 그래프는 어디에 있었나` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> 작년 가을에 두 팀을 같은 주에 만났습니다. 둘 다 사내 문서 검색에 언어 모델을 붙이는 일을 하고 있었어요. 같은 모델, 같은 API 키, 같은 가격표. 한 팀은 3주 만에 사내에 열었고, 다른 팀은 9주째 "모델이 자꾸 지어낸다"는 회의를 반복하고 있었습니다.

이 장은 그 이야기를 60년치로 늘려 놓은 겁니다. 초기 AI는 그래프를 갖고 있었습니다. 딥러닝이 그걸 벡터에 녹여 버렸고요. 그리고 지금 우리는 다시 그래프를 그리고 있습니다. 세 문장이 이 장의 전부이고, 나머지는 근거입니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 1.1 | 그래프를 가졌던 시절 |
| 1.2 | 그래프를 벡터에 녹인 시절 |
| 1.3 | 어느 손잡이를 돌리면 무엇이 움직이나 |
| 1.4 | 그래프를 되찾는 중 |
| 1.5 | 하네스, 모델을 둘러싼 배선 다발 |
| 1.6 | 두 트랙 |

## 한 장 요약

- 초기 AI는 지식을 노드와 엣지로 적었습니다. 사람이 손으로 채워야 해서 무너졌고요.
- 딥러닝은 그 관계를 좌표 사이 거리에 녹였습니다. 사람이 안 채워도 되는 대신, 관계를 저장하지 않게 됐습니다. 매번 다시 계산하고 버립니다.
- 에이전트 시대에 우리는 다시 그래프를 그리고 있습니다. 상태 그래프, 체크포인트, 종료 조건, 근거 추적. 이름은 새롭지만 전부 노드와 엣지예요.
- 모델 바깥의 배선 다발을 하네스라고 부릅니다. 하네스는 그래프입니다. 그래서 하네스 엔지니어링은 그래프 엔지니어링입니다.

## 키워드와 1차 출처

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

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch01/code

# 예제 1, 2 — 의존성 없음
python3 ex1_vector_only.py
python3 ex2_graph_grounded.py

# 예제 3 — LangGraph 필요 (API 키는 필요 없다)
pip install "langgraph>=1.0,<2.0"
python3 ex3_agent_loop.py
```

| 파일 | 무엇을 보여 주나 | 기대 결과 |
|---|---|---|
| `notes.py` | 같은 사실을 문장 8줄과 트리플 7개로 두 번 적은 샘플 데이터 | — |
| `ex1_vector_only.py` | 벡터 검색만으로 2홉 질문에 답하려는 시도 | 오답. 라온에너지가 딸려 나온다 |
| `ex2_graph_grounded.py` | 같은 질문을 그래프 경로로 | 정답. 근거 경로가 함께 출력된다 |
| `ex3_agent_loop.py` | 종료 조건과 체크포인트가 있는 상태 그래프 루프 | 정답. 재시도 1회 뒤 종료, 체크포인트 8개 |

`ex1`이 틀리는 건 임베딩 모델이 작아서가 아니다. 관계를 저장하지 않았기 때문이다.
모델을 바꿔도 결과는 같다. 직접 바꿔 보고 확인하기를 권한다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 "하네스가 중요하다"까지만 말했습니다. 다음 장은 최근 2년치 하네스 실무 한 벌을 통째로 가져와서, 그 안의 모든 용어에 그래프 이름을 붙입니다. 붙이고 나면 원래 책 열네 챕터 분량이 표 하나로 접힙니다.

---

[전체 목차](../../../README.md) · [2장 하네스 엔지니어링에서 그래프 엔지니어링으로](../../ch02/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
