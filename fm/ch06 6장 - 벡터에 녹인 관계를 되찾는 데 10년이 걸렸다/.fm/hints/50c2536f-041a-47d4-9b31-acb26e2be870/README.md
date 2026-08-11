# GraphRAG 방식의 대가는 무엇인가?

**답**: 색인이 비싸고 갱신이 어렵다. 문서가 바뀌면 다시 접어야 하므로 자주 바뀌는 데이터에는 맞지 않는다.

---

## 1. 먼저, GraphRAG가 무엇을 바꿨는지

6장의 논지는 한 줄로 요약된다.

> **풀이는 「세는 시점」을 옮기는 것이다.**

조각 검색(일반 RAG)은 **질의 시점**에 top-k개만 본다. 그래서 「전부 몇 건인가」 같은 전역 질문에 구조적으로 답할 수 없다. `ex1_rag_limits.py`가 보여 주는 벽이 그것이다.

```
전체 12건 중 4건만 봤다. 나머지 8건에 무엇이 있는지 모른다.
k를 12로 올리면? 이 예제에서는 된다. 문서가 12건이니까.
문서가 12만 건이면 못 넣는다. 그게 이 한계의 실체다.
```

GraphRAG는 이 벽을 **세는 시점을 앞으로 당겨서** 넘는다.

| | 조각 검색 (RAG) | GraphRAG |
|---|---|---|
| 전체를 훑는 시점 | 없음 | **색인 시점** (한 번) |
| 질의 시점에 하는 일 | k개 조각 검색 | 접어 둔 요약을 편다 |
| 전역 질문 | 못 넘는 벽 | 답이 나온다 |
| **대가** | 색인 저렴 | **색인이 비싸고 갱신이 어렵다** |

`ex2_graphrag_lite.py`의 마지막 출력이 이 카드의 답 그대로다.

```
달라진 건 «언제 세느냐»이다.
조각 검색은 질의 시점에 k개만 본다. 전체를 셀 기회가 없다.
GraphRAG 는 색인 시점에 전부 훑어 접어 두고, 질의 시점에는 접어 둔 것만 편다.

대가도 분명하다. 색인이 비싸고, 문서가 바뀌면 다시 접어야 한다.
그래서 자주 바뀌는 데이터에는 안 맞는다.
```

---

## 2. 대가 (1) — 색인이 비싸다

### 왜 비싼가: 색인 파이프라인이 전부 LLM 호출이다

Microsoft GraphRAG의 표준 색인 파이프라인은 네 단계다.

1. **엔티티·관계·주장 추출** — 모든 청크마다 LLM 호출
2. **커뮤니티 탐지** — Leiden 알고리즘 (여기는 LLM 없이 그래프 연산)
3. **커뮤니티 요약·리포트 생성** — 계층(level)마다, 커뮤니티마다 LLM 호출
4. **임베딩** — 텍스트를 벡터 공간에 넣기

일반 RAG의 색인은 4번 하나뿐이다. GraphRAG는 여기에 **1번과 3번이라는 대규모 LLM 호출 두 덩어리**를 얹는다. 문서 수에 비례해 호출이 늘고, 3번은 커뮤니티 수에 비례해 또 늘어난다.

`ex2_graphrag_lite.py`가 규칙 기반 `summarize()`로 대체한 부분이 정확히 3번이다. 예제 주석이 이 점을 짚어 둔다.

```python
def summarize(community, triples):
    """커뮤니티 요약. 규칙 기반이라 매번 같은 결과가 나온다."""
```

> `ex2` 의 요약문은 규칙으로 만듭니다. 진짜 GraphRAG 는 모델이 씁니다.

즉 예제에서 공짜로 지나간 그 한 줄이, 실제 시스템에서는 **비용의 몸통**이다.

### 실제 숫자

- **2024년 초, 단일 데이터셋 색인에 약 $33,000**이 들었다는 사례가 널리 인용된다. ([Graph Praxis, "The GraphRAG Cost Cliff"](https://medium.com/graph-praxis/the-graphrag-cost-cliff-how-33-000-became-33-in-eighteen-months-be1b0fbe37e4))
- 학술 벤치마크 측정: GraphRAG 색인에 **프롬프트 토큰 3,000만 개 + 완성 토큰 780만 개**. HotpotQA에서는 커뮤니티가 **57,384개** 생기고, 그 하나하나에 리포트를 써야 하므로 토큰이 폭증한다. ([arXiv:2503.04338, *In-depth Analysis of Graph-based RAG in a Unified Framework*](https://arxiv.org/abs/2503.04338))
- 초기에는 색인을 돌리기 전에 비용을 미리 볼 방법조차 없어서, 커뮤니티 기여로 `--estimate-cost` 플래그가 붙었다. ([microsoft/graphrag Discussion #440](https://github.com/microsoft/graphrag/discussions/440))
- 범용 RAG를 무작정 GraphRAG로 업그레이드한 팀들이 **색인 비용을 100배** 더 썼다는 보고도 있다.

### Microsoft 자신의 대응: LazyGraphRAG

이 대가가 실재한다는 가장 강한 증거는, 만든 쪽이 그것을 없애려고 새 방식을 내놨다는 사실이다.

**LazyGraphRAG**는 LLM 요약을 **전부 질의 시점으로 미루고**, 색인 시점에는 가벼운 그래프 구성만 한다. Microsoft의 주장은 이렇다.

- 색인 비용이 **일반 벡터 RAG와 동일**하며, 이는 **full GraphRAG의 0.1%**
- 전역 질의 품질은 GraphRAG Global Search와 비슷하면서 **질의 비용은 700배 이상 낮음**

([Microsoft Research, "LazyGraphRAG: setting a new standard for quality and cost"](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/))

이 이름이 좋은 힌트다. **Lazy** — 접는 일을 미룬다. 6장의 표현으로 바꾸면 **「세는 시점을 다시 뒤로 미룬 것」**이다. 색인 시점에 접는 대가가 너무 컸기 때문이다.

---

## 3. 대가 (2) — 갱신이 어렵다

### 왜 어려운가: 커뮤니티는 전역 구조라서

문서 하나가 바뀌면 이론상 그 문서만 다시 처리하면 될 것 같다. 하지만 GraphRAG에서는 그렇지 않다.

`ex2_graphrag_lite.py`의 `label_propagation()`을 보면 이유가 보인다.

```python
def label_propagation(adj, rounds=12):
    """이웃에서 제일 흔한 라벨을 가져온다. 몇 바퀴 돌면 뭉친다."""
```

이웃의 라벨이 내 라벨을 바꾸고, 바뀐 내 라벨이 다시 이웃을 바꾼다. **한 노드의 변경이 그래프 전체로 번질 수 있다.** 실제 GraphRAG가 쓰는 Leiden도 성질은 같다 — 커뮤니티 분할은 그래프 전역 구조의 함수다.

그리고 커뮤니티가 달라지면 그 커뮤니티의 **요약(LLM 리포트)도 다시 써야** 한다. 즉 갱신 비용은 그래프 재계산에서 끝나지 않고 **2절의 비싼 LLM 호출로 되돌아간다.**

> 문서가 바뀌면 **다시 접어야 한다.** 접는 게 비쌌으므로, 다시 접는 것도 비싸다.

### 실제 현황

- 초창기 GraphRAG에는 증분 갱신이 아예 없어서 **전체 재색인**뿐이었다. 이슈 [#741 Incremental indexing](https://github.com/microsoft/graphrag/issues/741)이 그 논의의 출발점이다.
- 지금은 CLI에 `graphrag update` 명령이 있다. 기존 색인과 새 콘텐츠 사이의 **델타를 계산해 병합**하고, 결과를 `update_output`에 쓴다. `standard-update` / `fast-update` 방식을 고를 수 있다. ([GraphRAG CLI 문서](https://microsoft.github.io/graphrag/cli/))
- 설계 목표는 **커뮤니티 재계산을 최소화**하는 것 — 새 엔티티를 기존 커뮤니티에 끼워 넣어 요약을 다시 쓰지 않으려 한다. 하지만 이슈 #741의 설계 노트가 한계를 명시한다.

  > "The append command will try to minimize community recomputes so that summarization is not performed again. **If certain thresholds are met, recompute may be required, so the worst case degrades to the same performance as a normal indexing.**"

  즉 미배치 엔티티 수나 모듈성 변화가 임계치를 넘으면 **최악의 경우 전체 색인과 같은 비용으로 되돌아간다.**
- 범위 제한도 크다. 설계상 **추가(append)만** 다루고, **문서 삭제**, 수동 그래프 편집 등은 명시적으로 out of scope다. 자주 바뀌는 데이터는 추가만 일어나지 않는다 — 수정과 삭제가 섞인다.
- 자주 바뀌는 데이터 소스를 어떻게 다루냐는 질문([Discussion #1313](https://github.com/microsoft/graphrag/discussions/1313), [Discussion #511](https://github.com/microsoft/graphrag/discussions/511))에는 유지보수자의 공식 답변이 사실상 없다. 이 대가가 아직 열려 있는 문제라는 뜻이다.

---

## 4. 그래서 언제 쓰면 안 되는가

이 카드의 마지막 문장이 실무 판단 기준이다: **자주 바뀌는 데이터에는 맞지 않는다.**

| 상황 | 판단 |
|---|---|
| 사내 장애 회고 아카이브, 논문 코퍼스, 계약서 더미 — 한 번 쌓이면 잘 안 바뀜 | GraphRAG가 맞다. 색인 비용을 **한 번** 내고 계속 쓴다 |
| 실시간 로그, 상품 카탈로그, 뉴스 피드 — 분/시 단위로 바뀜 | 안 맞는다. 접는 비용을 계속 다시 낸다 |
| 전역 질문 비율이 5% 미만 | 아예 붙이지 마라 (6장의 다른 논지) |

6장 요약이 덧붙인 정직한 한 줄도 같이 기억할 만하다.

> 그리고 정직하게 말하면, 사실 조회에서는 그래프를 붙인 쪽이 살짝 집니다. 전역 질문 비율이 5%도 안 되면 안 붙이는 게 맞습니다.

즉 GraphRAG의 대가는 두 겹이다.
1. **비용 축**: 색인이 비싸고, 갱신 때 그 비용이 되돌아온다 (이 카드)
2. **성능 축**: 단순 사실 조회에서는 오히려 손해다

둘 다 「전역 질문이 충분히 많은가」로 정당화되어야 한다.

---

## 5. 한 줄 정리

> **GraphRAG는 「세는 일」을 질의 시점에서 색인 시점으로 옮긴 것이다. 전역 질문에 답할 수 있게 되지만, 옮긴 그 일이 비싼 LLM 작업이라 색인이 비싸진다. 그리고 커뮤니티는 전역 구조라서 문서 하나가 바뀌어도 다시 접어야 할 수 있다 — 그래서 자주 바뀌는 데이터에는 안 맞는다.**

---

## 참고 자료

- [Microsoft GraphRAG (GitHub)](https://github.com/microsoft/graphrag)
- [GraphRAG 색인 파이프라인 개요](https://microsoft.github.io/graphrag/index/overview/)
- [GraphRAG CLI — `update` 명령](https://microsoft.github.io/graphrag/cli/)
- [Issue #741 — Incremental indexing (adding new content)](https://github.com/microsoft/graphrag/issues/741)
- [Discussion #1313 — Best Practices for Updating GraphRAG Index with Frequently Changing Data Sources?](https://github.com/microsoft/graphrag/discussions/1313)
- [Discussion #511 — How to Handle Incremental Updates to Indexed Data?](https://github.com/microsoft/graphrag/discussions/511)
- [Discussion #440 — How much did each run cost you?](https://github.com/microsoft/graphrag/discussions/440)
- [Microsoft Research — LazyGraphRAG: setting a new standard for quality and cost](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- [arXiv:2503.04338 — In-depth Analysis of Graph-based RAG in a Unified Framework](https://arxiv.org/abs/2503.04338)
- [Graph Praxis — The GraphRAG Cost Cliff: How $33,000 Became $33 in Eighteen Months](https://medium.com/graph-praxis/the-graphrag-cost-cliff-how-33-000-became-33-in-eighteen-months-be1b0fbe37e4)
- 원 자료: 6장 예제 `code/ex1_rag_limits.py`, `code/ex2_graphrag_lite.py`
