# 17장 — 벡터만으로 답이 안 나오는 질문들

`3부 — 지식 그래프 엔지니어링 (트랙 1)` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> GraphRAG를 붙였는데 사용자 만족도가 떨어졌습니다.

가중 평균을 내 보니 0.833에서 0.862. 3% 올랐습니다. 그 3%를 위해 색인 값이 월 30만 원 늘고, 지연이 340밀리초 붙고, 갱신 파이프라인을 새로 만들었습니다. 이 장은 그 계산을 먼저 하는 방법입니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 17.1 | 질문 분포가 결론을 뒤집는다 |
| 17.2 | 라우터가 틀리면 그럴듯한 오답이 나온다 |
| 17.3 | 진짜 비용은 색인이 아니라 갱신이다 |
| 17.4 | 네 가지 방식을 갱신 관점으로 |

## 한 장 요약

- 도구를 고르기 전에 질문을 세세요. 같은 성능표에 다른 분포를 곱하면 결론이 반대가 됩니다. 질문 로그 100건이면 반나절에 답이 나와요.
- 그래프를 붙이면 사실 조회가 조금 나빠집니다. 0.02쯤요. 그런데 사실 조회는 빈도가 높아서 체감이 큽니다. 지표 변화에 빈도를 곱해서 보세요.
- 라우터가 틀리면 빈 답이 아니라 그럴듯한 오답이 나옵니다. 규칙으로 먼저 거르고, 애매한 것만 모델에게 보내고, 결과를 캐시해서 같은 질문이 같은 곳으로 가게 하세요.
- 진짜 비용은 색인이 아니라 갱신입니다. 영향 커뮤니티 비율이 전부를 정하고, 그건 재 봐야 압니다. 제 기대는 5%였고 실측은 34%였어요.
- 증분 갱신을 나중에 붙이겠다는 계획은 대개 안 지켜집니다. 설계를 먼저 하고 전체 색인을 만드세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 그래프 기반 RAG | [사실상 표준] | [Microsoft GraphRAG](https://github.com/microsoft/graphrag) |
| 경량 그래프 RAG | [실험] | [LightRAG](https://arxiv.org/abs/2410.05779) |
| 연상 기억형 RAG | [실험] | [HippoRAG](https://arxiv.org/abs/2405.14831) |
| 시간 인식 메모리 그래프 | [실험] | [Graphiti](https://github.com/getzep/graphiti) |
| 순위 융합 | [사실상 표준] | [reciprocal rank fusion](https://dl.acm.org/doi/10.1145/1571941.1572114) |
| 검색 증강 생성 | [사실상 표준] | [RAG](https://arxiv.org/abs/2005.11401) |
| 하이브리드 검색 | [사실상 표준] | [hybrid search](https://www.elastic.co/what-is/hybrid-search) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch17/code
python3 ex1_routing.py            # 질문 유형별 라우팅과 오라우팅
python3 ex2_incremental_cost.py   # GraphRAG 의 진짜 비용은 갱신
python3 ex3_compare_approaches.py # 네 가지 방식을 «갱신 관점»으로
python3 ex4_hybrid_fusion.py      # 순위 융합, 그리고 언제 손해인가
python3 ex5_eval_harness.py       # 질문 분포가 결론을 뒤집는다
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 3부가 여기서 끝납니다. 지금까지는 「모델이 무엇을 아는가」였어요. 4부는 「모델이 무엇을 하는가」입니다. 그리고 첫 장은 체인이 어디서 부러지는지부터 봅니다.

---

이전 [16장 어제는 맞았고 오늘은 틀리다](../../ch16/code/README.md) | [전체 목차](../../../README.md) | 다음 [18장 체인은 어디서 부러지는가](../../ch18/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
