# 33장 - 쿼리 플랜을 읽으면 비용이 보인다

`7부 - 운영` | **한국어** | [English](../../../content_en/ch33/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 3주 동안 쿼리를 튜닝했습니다. 평균 지연이 9ms에서 4ms로 줄었어요.

7부가 시작됩니다. 6부가 백본을 만드는 얘기였다면 여기서부터는 운영하는 얘기예요. 그리고 운영의 첫 규칙은 *재고 나서 고치기*입니다. 이 장은 두 가지를 다룹니다. 쿼리 플랜을 읽는 법과, 그 플랜이 청구서에서 차지하는 자리를 아는 법이요. 후자가 더 중요합니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 33.1 | 플랜에서 볼 것은 세 가지다 |
| 33.2 | 인덱스는 언제 안 듣나 |
| 33.3 | 제일 느린 것과 제일 아픈 것은 다르다 |
| 33.4 | 청구서의 큰 칸은 대개 다른 곳이다 |
| 33.5 | 어디를 먼저 볼 것인가 |

## 한 장 요약

- 플랜에서 볼 것은 셋입니다. `CROSS_PRODUCT`가 있나, `SCAN`이 무엇을 훑나, `FILTER`가 앞인가 뒤인가.
- 「작은 쪽에서 시작하라」는 요즘 엔진에서는 대개 상관없습니다. 플래너가 알아서 정해요. 순서를 고민하기 전에 플랜을 보세요.
- 인덱스 효과를 재려면 규모를 충분히 키워야 합니다. 수천 개에서는 파싱 값이 지배해서 아무것도 안 보입니다.
- 인덱스는 찾는 방식에 맞아야 듭니다. 그리고 그래프에서는 관계를 따라가는 데 인덱스가 필요 없어요. 시작점 하나만 인덱스로 찾으면 그다음은 공짜입니다.
- 한 건씩 넣지 마세요. 일괄 적재가 수십 배 빠릅니다. 「그래프 DB가 느리다」는 결론의 상당수가 여기서 나옵니다.
- 「제일 느린 것」과 「제일 아픈 것」은 다릅니다. 총 시간(1회 지연 × 호출 수)으로 줄 세우세요. 느린 쿼리 로그는 제일 아픈 것을 못 잡습니다.
- 청구서의 큰 칸은 대개 토큰입니다. 쿼리를 *빠르게* 해도 비용은 거의 그대로예요. 다만 쿼리를 *정확하게* 하면 토큰이 크게 줍니다. 둘은 다른 작업입니다.
- 그리고 성능 작업 전에 구간별로 쪼개 보세요. 95%를 차지하는 구간이 있으면 나머지를 전부 최적화해도 3%입니다. 60년 된 암달의 법칙이 지금도 그대로 적용됩니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 쿼리 플랜 | [사실상 표준] | [query plan](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/) |
| 실행 계획 설명 | [사실상 표준] | [EXPLAIN](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| 곱집합 | [표준] | [cartesian product](https://www.postgresql.org/docs/current/queries-table-expressions.html) |
| 인덱스 | [사실상 표준] | [index](https://neo4j.com/docs/cypher-manual/current/indexes/) |
| 느린 쿼리 로그 | [사실상 표준] | [slow query log](https://dev.mysql.com/doc/refman/8.0/en/slow-query-log.html) |
| 암달의 법칙 | [표준] | [Amdahl's law](https://dl.acm.org/doi/10.1145/1465482.1465560) |
| 일괄 적재 | [사실상 표준] | [bulk load](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch33/code
pip install kuzu

python3 ex1_read_plan.py        # 진짜 EXPLAIN 출력을 읽는다
python3 ex2_index_effect.py     # 인덱스가 언제 듣고 언제 안 듣나
python3 ex3_cost_model.py       # 월 비용을 항목별로 (의존성 없음)
python3 ex4_hot_query.py        # 제일 느린 것과 제일 아픈 것 (의존성 없음)
python3 ex5_where_time_goes.py  # 한 요청의 시간 분해 (의존성 없음)
```

`ex1`, `ex2` 는 데이터를 만드는 데 몇 초 걸립니다. `COPY` 로 일괄 적재해서
한 건씩 넣는 것보다 훨씬 빠릅니다. 그 자체가 33장에서 다루는 얘기이기도 합니다.

`ex2` 의 결과는 「인덱스가 별 효과 없다」처럼 보이는데, 그건 규모가 작아서입니다.
`SIZES` 를 백만 단위로 키우면 갈라집니다. 다만 실행이 오래 걸립니다.

`ex3`~`ex5` 의 숫자는 저자 환경의 실측을 단순화한 "예시 워크로드"입니다.
여러분 시스템의 값을 넣어서 다시 돌려 보세요. 구조가 요점이지 숫자가 요점이 아닙니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 "빠르게, 싸게"였습니다. 다음 장은 "지워 주세요"입니다. 그래프에서 무언가를 지운다는 게 무슨 뜻인지, 그리고 왜 관계형 DB보다 훨씬 어려운지요.

---

이전 [32장 스키마를 바꾸는 날](../../ch32/code/README.md) | [전체 목차](../../../README.md) | 다음 [34장 그래프에서 개인정보를 지운다는 것](../../ch34/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
