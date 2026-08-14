# GQL이 2024년에 국제 표준이 된 것의 실제 효과

> **질문** GQL이 2024년에 국제 표준이 된 것의 실제 효과는 무엇인가?
>
> **답** 표준 전용 문법은 아직 엔진들이 받지 않는다. 효과는 "지금 코드가 바뀐다"가 아니라 "방향이 정해진다"다.

## 한 줄로

표준 문서가 나온 날과 내 엔진이 그 문서대로 도는 날은 다른 날이다. 2024년의 GQL이 실무에 준 것은 **새 문법**이 아니라 **정렬된 목표점**이다.

## 무슨 일이 있었나

**ISO/IEC 39075:2024** — 「Information technology — Database languages — GQL」이 2024년 4월에 발행됐다. SQL(ISO/IEC 9075) 이후 ISO가 **독립된 데이터베이스 질의 언어**로 승인한 두 번째 언어다. 즉 그래프 질의는 이제 "벤더마다 다른 것"이 아니라 "표준이 있는데 벤더가 아직 다 안 따라온 것"이 됐다.

- 1차 출처: [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html)
- 표준화 경과: [gqlstandards.org](https://www.gqlstandards.org/)

GQL은 Cypher에서 크게 영향을 받았지만 **Cypher = GQL은 아니다**. GQL에는 Cypher에 없는 절이 들어가 있고, 반대로 Cypher에 있는 절이 GQL 표준에는 없다.

| 기능 | GQL 표준 | Cypher 방언 |
|---|---|---|
| 변수 정의 | `LET nm = p.name` — 기존 바인딩을 건드리지 않고 컬럼만 추가 | `WITH p, p.name AS nm` — **차단형**. 유지하려는 변수를 전부 다시 나열해야 한다 |
| 문장 합성 | `... NEXT RETURN n` — 앞 문장의 작업 테이블을 다음 문장이 받는다 | `WITH`로 파이프라인을 잇는다 |
| 조건 | `FILTER p.age > 30` — 앞 문장 **결과에** 적용 | `WHERE` — 자기가 속한 절의 일부로 평가 |
| 가변 길이 경로 | 표준화된 양적 경로 패턴 | `-[:Knows*1..2]->` (방언 표기) |

## 그래서 실제로 도나 — 예제 3이 세어 본 결과

`code/ex3_gql_dialects.py`는 이 말을 문장으로 주장하지 않고 **엔진에 그대로 넣어 보고 성공/실패를 센다**. 확인 시점 2026년 8월, Kuzu 0.11.3.

| 항목 | 계열 | 기대 결과 |
|---|---|---|
| `MATCH (p:Person) RETURN p.name` | GQL/Cypher 공통 | 성공 |
| `WHERE p.age > 30` | GQL/Cypher 공통 | 성공 |
| `-[:Knows*1..2]->` | Cypher 방언 | 성공 |
| `MATCH (p:Person) LET nm = p.name RETURN nm` | **GQL 표준** | 실패 |
| `... RETURN p.name AS n NEXT RETURN n` | **GQL 표준** | 실패 |
| `MATCH (p:Person) FILTER p.age > 30 RETURN p.name` | **GQL 표준** | 실패 |
| `MATCH (p:Person) WITH p WHERE ... RETURN p.name` | Cypher 방언 | 성공 |

읽는 법이 중요하다. **표준 전용 절만 골라서 실패하고, 방언 절은 성공한다.** 이게 이 예제가 만들려는 결과다. 실패하는 질의가 버그가 아니라 관측값이다.

## 엔진 지원 현황 (2026년 8월 기준)

- **Neo4j**: GQL 상태 코드/오류 체계를 5.23(notification)·5.25(error)부터 도입했고, Cypher가 GQL의 **필수(mandatory) 기능 대부분과 선택 기능 상당수**를 지원한다고 문서에 명시한다([GQL conformance](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/)). 단 "GQL 준수"는 곧 "`LET`/`NEXT`/`FILTER`를 쓸 수 있다"와 같은 말이 아니다. 준수 항목이 기능 단위로 쪼개져 표로 관리되고 있다는 사실 자체가 이행이 진행 중임을 보여 준다.
- **Kuzu 0.11.3**: 표준 전용 절 미지원 (위 예제 결과).
- **새로 나오는 제품들**: Microsoft Fabric graph, Google Spanner Graph/BigQuery graph 질의, Drasi, PuppyGraph 등은 처음부터 "GQL"을 간판으로 걸고 나온다. **방향이 정해진다**의 실체는 여기에 있다. 기존 엔진이 문법을 갈아엎는 게 아니라, **새로 설계되는 것들의 기본값이 GQL이 된다**.

## SQL이 이미 걸어 본 길

SQL-92가 나온 뒤에도 벤더 방언은 10년 넘게 남았다. 문자열 결합, 날짜 함수, 페이지네이션(`LIMIT` vs `TOP` vs `ROWNUM`)은 지금도 갈린다. 그래도 SQL 표준은 값을 했다. **"어느 쪽이 맞는 것인가"에 대한 다툼을 끝냈기 때문**이다. GQL도 같다. 지금 당장 코드를 바꾸진 않지만, 3년 뒤 어디로 수렴할지가 정해졌다.

## 그럼 지금 뭘 해야 하나 — 이식 대비 4가지

예제 3과 이 장 요약이 권하는 실무 지침. **문법을 미리 GQL로 바꾸라는 게 아니다.** 나중에 바꿀 수 있는 모양으로 두라는 것이다.

1. **질의문을 한곳에 모은다.** 코드 곳곳에 문자열로 흩어져 있으면 옮길 때 무엇을 옮길지부터 모른다.
2. **`ORDER BY`를 강제한다.** 엔진이 바뀌면 정렬 없는 결과의 행 순서가 바뀐다. 순서에 기대던 테스트와 로직이 조용히 깨진다.
3. **엔진 고유 함수를 별도 파일로 격리한다.** 방언이 어디에 몇 개 있는지가 이식 견적서가 된다.
4. **"이 질의가 어떤 질문에 답하는가"를 주석으로 남긴다.** 다른 언어로 **다시 쓸 때** 필요한 건 옛 문법이 아니라 의도다. `ex1`이 보여 주듯 같은 질문의 답은 세 언어에서 같지만, 문장 모양은 옮겨 쓸 수 없다.

## 옆에 놓고 볼 것 — SQL/PGQ도 같은 병을 앓는다

**SQL/PGQ**(ISO/IEC 9075-16:2023)는 테이블을 옮기지 않고 그래프 시각만 얹는 표준이다. `CREATE PROPERTY GRAPH` + `GRAPH_TABLE (...)` 문법이 아름다운데, `ex4_sql_pgq.py`는 **표준 문법은 출력만 하고 실제 실행은 같은 뜻의 평범한 SQL로 한다**. 이유가 같다. 구현이 아직 덜 퍼졌다. 표준이 둘 다 있고, 둘 다 "아직"이다.

## 자주 틀리는 곳

- ❌ "2024년에 표준이 됐으니 이제 GQL로 쓰면 어디서나 돈다" → 표준 전용 절은 대부분 엔진에서 파싱조차 안 된다.
- ❌ "Cypher가 GQL이다" → GQL이 Cypher에서 영향을 받았을 뿐. `LET`/`NEXT`/`FILTER`는 GQL 쪽, `WITH`는 Cypher 쪽이다.
- ❌ "표준이 없어서 안 된 일이니, 표준이 나오면 SPARQL의 경로 상한 문제 같은 것도 해결된다" → 표준에도 구멍이 있다(`ex2`: SPARQL 속성 경로에 최대 홉 표기 자체가 없다). 표준의 존재가 완전성을 뜻하지 않는다.
- ❌ "표준이 안 돌아가니 의미 없다" → 의미는 **수렴 방향**이다. 새 제품의 기본값과 팀의 학습 투자 대상이 정해졌다.

## 관련 예제

- `content/ch11/code/ex3_gql_dialects.py` — 표준 절 vs 방언 절 성공/실패 카운트 (이 카드의 근거)
- `content/ch11/code/ex1_three_languages.py` — 같은 질문, 세 언어
- `content/ch11/code/ex2_path_queries.py` — 경로 표기에서 갈리는 자리
- `content/ch11/code/ex4_sql_pgq.py` — 표준은 있는데 구현이 없는 또 하나의 사례
