# 6장 - 벡터에 녹인 관계를 되찾는 데 10년이 걸렸다

`1부 - 뿌리: 그래프는 어디에 있었나` | **한국어** | [English](../../../content_en/ch06/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 추천 모델이 잘 돌던 어느 날, 법무팀에서 연락이 왔습니다. "이 사용자한테 왜 이 상품을 추천했는지 설명해 주실 수 있나요."

이 장은 그 녹임과 되찾음의 이야기입니다. 그래프를 벡터로 누른 쪽(임베딩과 그래프 신경망), 문서를 벡터로 누른 쪽(RAG), 그리고 양쪽 다 벽에 부딪히고 나서 다시 그래프를 꺼낸 쪽(GraphRAG 계열)을 봅니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 6.1 | 구조를 값에 녹이는 방법 |
| 6.2 | 문서를 벡터로 눌렀을 때 생기는 벽 |
| 6.3 | 그래서 다시 그래프를 꺼냈다 |

## 한 장 요약

- 그래프 신경망은 이웃 값을 뭉쳐 자기 값에 섞습니다. 층을 돌 때마다 구조가 값에 녹아들고, 그 대가로 되짚기가 어려워집니다. 2~3층에서 멈추는 관행에는 과평활이라는 이유가 있습니다.
- 조각 검색은 답이 한 조각에 들어 있을 때 잘 돕니다. 「전부 몇 건인가」 같은 전역 질문에는 벽이 있고, 그 벽은 조각을 더 넣어도 안 넘어집니다.
- 풀이는 세는 시점을 옮기는 것입니다. 색인 시점에 그래프를 만들고 뭉치마다 요약을 접어 두면, 질의 시점에는 펴기만 하면 됩니다. 대신 색인이 비싸고 갱신이 어렵습니다.
- 그리고 정직하게 말하면, 사실 조회에서는 그래프를 붙인 쪽이 살짝 집니다. 전역 질문 비율이 5%도 안 되면 안 붙이는 게 맞습니다.

## 키워드와 1차 출처

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

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch06/code
python3 ex1_rag_limits.py        # 조각 검색으로 전역 질문 시도, 실패한다
python3 ex2_graphrag_lite.py     # 색인 시점에 접어 두기, 성공한다
python3 ex3_message_passing.py   # GNN 한 층이 하는 일
python3 ex4_link_prediction.py   # 이웃만 세도 되는 예측, 임베딩이 필요해지는 지점
```

| 파일 | 보여 주는 것 |
|---|---|
| `corpus.py` | 장애 회고 12건과 거기서 뽑은 트리플 |
| `ex1_rag_limits.py` | 「전부 몇 건인가」는 top-k 로 못 센다 |
| `ex2_graphrag_lite.py` | 라벨 전파로 커뮤니티를 찾고 요약을 접어 둔다 |
| `ex3_message_passing.py` | 층을 돌 때마다 구조가 값에 녹아든다 |
| `ex4_link_prediction.py` | 되짚을 수 있는 예측과 없는 예측의 갈림길 |

`ex2` 의 요약문은 규칙으로 만듭니다. 진짜 GraphRAG 는 모델이 씁니다.
여기서 보여 주려는 건 요약 품질이 아니라 **언제 접느냐**입니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 1부가 여기서 끝납니다. 지금까지 「그래프가 왜 필요한가」를 봤다면, 다음 부는 「그래프가 정확히 무엇인가」로 내려갑니다. 노드 하나를 잘못 그려서 3주를 날린 이야기부터 시작합니다.

---

이전 [5장 문자열이 아니라 사물](../../ch05/code/README.md) | [전체 목차](../../../README.md) | 다음 [7장 노드 하나 잘못 그려서 3주를 날렸다](../../ch07/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
