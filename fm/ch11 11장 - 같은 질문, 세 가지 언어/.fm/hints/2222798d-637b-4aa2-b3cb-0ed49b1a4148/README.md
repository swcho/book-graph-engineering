# `ex3_gql_dialects.py`의 GQL 표준 전용 절 — LET / NEXT / FILTER

## 질문과 답

**질문**: `ex3_gql_dialects.py`에서 GQL 표준 전용으로 시험하는 절은 무엇인가?

**답**: **LET 절, NEXT 절, FILTER 절**이다. Kuzu 0.11.3에서는 받지 않는다.

---

## 예제가 정확히 무엇을 하는가

`ex3_gql_dialects.py`는 «표준이 있어도 방언이 남는다»를 말이 아니라 **파서 에러**로 확인하는 예제다.
Kuzu 0.11.3 임베디드 엔진에 `CASES` 목록의 질의문을 하나씩 그대로 넣고, 성공/실패를 세어 표로 찍는다.

`CASES`는 세 계열로 나뉘어 있다.

| 계열 | 항목 | 질의문 |
|---|---|---|
| GQL/Cypher 공통 | 기본 패턴 매칭 | `MATCH (p:Person) RETURN p.name ORDER BY p.name` |
| GQL/Cypher 공통 | WHERE 절 | `MATCH (p:Person) WHERE p.age > 30 RETURN p.name ORDER BY p.name` |
| Cypher 방언 | 가변 길이 경로 | `MATCH (a:Person)-[:Knows*1..2]->(b:Person) RETURN a.name, b.name` |
| **GQL 표준** | **LET 절** | `MATCH (p:Person) LET nm = p.name RETURN nm` |
| **GQL 표준** | **NEXT 절** | `MATCH (p:Person) RETURN p.name AS n NEXT RETURN n` |
| **GQL 표준** | **FILTER 절** | `MATCH (p:Person) FILTER p.age > 30 RETURN p.name` |
| Cypher 방언 | WITH 절 | `MATCH (p:Person) WITH p WHERE p.age > 30 RETURN p.name` |

여기서 계열 표시가 `"GQL 표준"`인 것이 딱 셋 — **LET, NEXT, FILTER** — 이고, 이 셋이 답이다.
장 도입부(「예제 실행」)에도 못을 박아 뒀다. *"`ex3`은 일부러 **실패하는 질의**를 포함합니다. 그게 이 예제의 결과입니다."*

## 실제로 돌려 본 결과 (Kuzu 0.11.3, 2026-08)

같은 질의를 Kuzu 0.11.3에 직접 넣어 재현했다. 세 절 모두 실행 단계에도 못 가고 **파서 단계에서** 죽는다.

```
LET:    실패 -- Parser exception: Invalid input <MATCH (p:Person) LET>: expected rule oC_SingleQuery (line: 1, offset: 17)
NEXT:   실패 -- Parser exception: Invalid input < NEXT>: expected rule ku_Statements (line: 1, offset: 36)
FILTER: 실패 -- Parser exception: Invalid input <MATCH (p:Person) FILTER>: expected rule oC_SingleQuery (line: 1, offset: 17)
WITH:   성공 2행
```

에러 문구에서 두 가지를 읽을 수 있다.

1. `expected rule oC_SingleQuery` — 접두어 `oC_`는 **openCypher** 문법 규칙이라는 뜻이다. Kuzu의 문법은 GQL이 아니라 openCypher 문법에서 출발했고, 그 문법에는 `LET`/`FILTER`라는 절 자체가 없다.
2. 같은 뜻을 Cypher 방언(`WITH ... WHERE`)으로 쓰면 **성공 2행**이 나온다. 즉 «표현하려는 계산이 어려운 것»이 아니라 «표준이 정한 이름을 엔진이 아직 모르는 것»이다. 이게 방언 문제의 정확한 모양이다.

---

## 세 절이 GQL에서 각각 무엇을 하는가

GQL(ISO/IEC 39075:2024)의 질의는 **선형 질의문(linear query statement)** 의 파이프라인이다.
표 하나가 문(statement)을 통과하면서 열이 붙고 행이 걸러지고, 다음 문으로 넘어간다.
LET / FILTER / NEXT는 그 파이프라인을 조립하는 세 부품이다.

### 1) `LET` — 열을 하나 붙인다 (비차단 변수 정의)

```
LET <변수> = <식> [, <변수> = <식> ...]
```

입력 행마다 식을 평가해서 **새 열을 추가**한다. 기존 바인딩 흐름을 끊지 않는다.

```gql
MATCH (p:Person)
LET nm = p.name
RETURN nm
```

핵심은 **비차단(non-blocking)** 이라는 점이다. `LET nm = p.name`을 써도 `p`는 그대로 살아 있다.
같은 `LET` 문 안의 변수끼리는 서로를 참조할 수 없으므로, 의존이 있으면 `LET`을 두 번 쓴다.

### 2) `FILTER` — 행을 걸러낸다 (패턴 매칭과 분리된 술어)

```
FILTER [WHERE] <불린식>
```

앞 문이 만들어 놓은 작업 표(working table)에서 조건이 `TRUE`인 행만 남긴다. `FALSE`와 `UNKNOWN`(널 관여)은 버린다.
그래서 널을 살리고 싶으면 `IS NULL`을 명시해야 한다.

```gql
MATCH (p:Person)
FILTER p.age > 30
RETURN p.name
```

GQL이 `WHERE`와 별도로 `FILTER`를 둔 이유는 **평가 시점**이 다르기 때문이다.
`WHERE`는 패턴 매칭 **도중**에 붙는 술어이고, `FILTER`는 앞 문이 **끝난 뒤** 표에 적용하는 독립 문이다.
그래서 `MATCH ... WHERE ...`는 GQL과 Cypher가 공통이지만(예제에서 성공한다), 독립 문 `FILTER`는 GQL 전용이 된다.

### 3) `NEXT` — 표를 통째로 다음 질의문에 넘긴다 (선형 합성)

```
NEXT <선형 질의문>
```

`RETURN`으로 끝난 결과 표를 **그대로** 다음 구간의 입력으로 넘긴다.
질의를 자기 완결적인 작은 구간들의 사슬로 쪼갤 수 있다.

```gql
MATCH (p:Person) RETURN p.name AS n
NEXT
RETURN n
```

집계를 끼울 때 특히 쓸모가 있다. 앞 구간에서 `GROUP BY`로 집계한 표를 뒤 구간이 다시 매칭에 쓴다.

```gql
MATCH (:Account)-[:Transfers]->(account:Account)
RETURN account, COUNT(*) AS num_incoming
GROUP BY account
NEXT
MATCH (account:Account)<-[:Owns]-(owner:Person)
RETURN account.id, owner.name, num_incoming
```

---

## Cypher 대응 문법 짝짓기

| GQL 표준 | 하는 일 | Cypher 대응 | 대응의 어긋남 |
|---|---|---|---|
| `LET nm = p.name` | 열 추가 (비차단) | `WITH p, p.name AS nm` | `WITH`는 **차단형**. 살릴 변수를 전부 다시 나열해야 하고, 빠뜨리면 그 뒤에서 스코프 밖이 된다 |
| `FILTER p.age > 30` | 표 단위 행 필터 (독립 문) | `WITH p WHERE p.age > 30` 또는 `MATCH ... WHERE ...` | Cypher는 필터를 절에 **얹어서** 쓴다. `WHERE`는 홀로 못 서고 `MATCH`/`WITH`에 붙어야 한다 |
| `... RETURN n NEXT RETURN n` | 표 전체를 다음 구간에 전달 | `... WITH n ...` (파이프라인) | `WITH`는 투영과 필터와 전달을 한 절에 겹쳐 놓는다. `NEXT`는 «구간 경계»만 담당해서 역할이 하나다 |

같은 질의를 두 언어로 나란히 쓰면 이렇게 된다.

```gql
-- GQL: 문 하나가 역할 하나
MATCH (p:Person)
FILTER p.age > 30
LET nm = p.name
RETURN nm
```

```cypher
// Cypher: WITH 하나가 전달 + 투영 + 필터를 겸한다
MATCH (p:Person)
WITH p, p.name AS nm WHERE p.age > 30
RETURN nm
```

Cypher 쪽에서 `WITH p, p.name AS nm`의 `p`를 빼면 뒤에서 `p`를 못 쓴다 — 이게 «차단형»의 대가다.
GQL은 `LET`으로 열만 얹고 흐름은 그대로 두는 쪽을 택했다.

## 엔진 지원 현황 (2026년 8월 확인)

| 엔진 | LET | NEXT | FILTER | 비고 |
|---|---|---|---|---|
| Kuzu 0.11.3 | 미지원 | 미지원 | 미지원 | 문법이 openCypher(`oC_*` 규칙) 기반. `WITH`로 우회 |
| Neo4j (Cypher 25 계열) | 미지원 | **지원** | 미지원 | GQL 필수 기능 대부분과 선택 기능 상당수에 맞춤. `NEXT`는 순차 질의로 문서화됨 |
| Google Spanner Graph / BigQuery GQL | 지원 | 지원 | 지원 | GQL 질의문으로 문서화 — 위 예시 문법의 출처 |
| Microsoft Fabric graph (GQL) | 지원 | 파이프라인 | 지원 | `LET`/`FILTER`를 GQL 문법으로 문서화 |

즉 «표준 전용 절»이라는 표현은 «아무 데서도 안 돈다»가 아니라, **예제가 쓰는 임베디드 엔진(Kuzu)에서 안 돈다**는 뜻이다.
클라우드 쪽 신규 구현은 GQL 문법을 앞세워 나오고 있고, 기존 Cypher 엔진은 `NEXT`처럼 겹치는 부분부터 흡수하고 있다.

## 이 카드가 실제로 말하려는 것

예제 말미의 결론이 카드의 뼈대다.

> GQL은 2024년에 국제 표준이 됐다. 그런데 이 엔진은 GQL 전용 절을 아직 안 받는다.
> «표준이 나왔다»와 «표준대로 돌아간다» 사이에 몇 년이 있다.
> SQL도 같은 길을 걸었다. SQL-92가 나오고도 방언이 10년 넘게 남았다.

그래서 표준의 효과는 «지금 코드가 바뀐다»가 아니라 «방향이 정해진다»다. 대비책은 셋이다.

- 질의문을 코드에 흩뿌리지 말고 한곳에 모은다
- 엔진 고유 함수는 별도 파일로 격리한다
- 「이 질의가 어떤 질문에 답하는가」를 주석으로 남긴다 (다시 쓸 때 필요하다)

## 헷갈리기 쉬운 곳

- **`WHERE`는 답이 아니다.** `WHERE`는 GQL과 Cypher **공통** 계열로 분류되어 있고 예제에서 성공한다. 표준 전용은 독립 문인 `FILTER` 쪽이다.
- **`WITH`도 답이 아니다.** `WITH`는 반대 방향, 즉 «Cypher 방언» 계열이다. GQL 표준에는 `WITH` 절이 없다.
- **가변 길이 경로 `*1..2`도 답이 아니다.** 이건 «Cypher 방언»으로 분류돼 있고 Kuzu에서 성공한다.
- **셋 다 실행 실패가 아니라 파싱 실패다.** 「기능이 없어서 결과가 틀린다」가 아니라 「단어를 모른다」에서 끝난다.

## 근거 (웹 확인, 2026-08)

- [ISO/IEC 39075:2024 — Information technology, Database languages, GQL](https://www.iso.org/standard/76120.html) — 표준 본문 서지. 1987년 SQL 이후 ISO가 낸 첫 데이터베이스 질의 언어 표준
- [GQL query statements — Spanner (Google Cloud)](https://docs.cloud.google.com/spanner/docs/reference/standard-sql/graph-query-statements) — `LET`/`FILTER`/`NEXT`의 구문·의미론과 예시 질의문. `FILTER`가 «앞 문이 끝난 뒤» 평가된다는 서술의 출처
- [GQL language guide — Microsoft Fabric docs](https://github.com/MicrosoftDocs/fabric-docs/blob/main/docs/graph/gql-language-guide.md) — `LET`의 «행마다 식 평가 + 열 추가», 같은 `LET` 안 변수 상호 참조 불가, `FILTER`의 널 처리
- [Sequential queries (NEXT) — Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/queries/composed-queries/sequential-queries/) — `NEXT`가 결과 표를 통째로 다음 구간에 넘기는 선형 합성이라는 설명
- [GQL conformance — Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/) — Cypher가 GQL 필수 기능 대부분과 선택 기능 상당수를 수용했다는 서술
- [GQL vs. Cypher: What the New ISO Standard Brings to the Table — NebulaGraph](https://nebula-graph.io/posts/gql-vs.-cypher-what-the-new-iso-standard-brings-to-the-table) — `LET`이 비차단이고 `WITH`는 차단형이라는 대비
- [Kuzu Cypher manual](https://docs.kuzudb.com/cypher/) — Kuzu가 openCypher 기반임을 밝힌 문서
- 직접 재현: Kuzu 0.11.3 (Python 바인딩)으로 위 세 질의 실행 → 전부 `Parser exception`, `WITH` 우회 질의는 2행 성공
