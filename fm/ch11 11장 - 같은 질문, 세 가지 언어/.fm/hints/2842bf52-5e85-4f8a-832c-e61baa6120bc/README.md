# Cypher 방언으로 분류된 문법: 가변 길이 경로와 WITH

**질문** Cypher 방언으로 분류된 문법은 무엇인가?

**답** 가변 길이 경로 `-[:Knows*1..2]->`와 `WITH` 절이다. GQL 표준(ISO/IEC 39075:2024)에는 없지만 Cypher 계열 엔진이 지원한다.

---

## 1. 어디서 나온 분류인가

11장 예제 `code/ex3_gql_dialects.py`는 질의문마다 **문법 계열** 라벨을 붙여 놓고, 같은 엔진(Kuzu 0.11.3)에 그대로 던져서 되는지 안 되는지를 세어 봅니다. 그 라벨이 셋입니다.

| 계열 | 예제의 질의문 |
|---|---|
| `GQL/Cypher 공통` | `MATCH (p:Person) RETURN p.name ORDER BY p.name` / `... WHERE p.age > 30 ...` |
| **`Cypher 방언`** | `MATCH (a:Person)-[:Knows*1..2]->(b:Person) RETURN a.name, b.name` |
| **`Cypher 방언`** | `MATCH (p:Person) WITH p WHERE p.age > 30 RETURN p.name` |
| `GQL 표준` | `LET nm = p.name` / `... AS n NEXT RETURN n` / `FILTER p.age > 30` |

즉 「Cypher 방언」은 **엔진에서는 잘 도는데 ISO GQL 표준 문법이 아닌 것**을 가리키는 자리입니다. 반대편의 「GQL 표준」은 **표준에는 있는데 이 엔진이 아직 못 받는 것**이고요. 이 둘이 동시에 존재한다는 게 11.3절의 요지입니다 — "표준이 나왔다"와 "표준대로 돌아간다" 사이에 몇 년이 있다.

### 실제로 돌려 본 결과 (Kuzu 0.11.3, 2026-08 확인)

예제와 같은 스키마에 GQL 표준 표기까지 추가해서 직접 확인한 결과입니다.

| 문법 | 계열 | Kuzu 0.11.3 |
|---|---|---|
| `-[:Knows*1..2]->` | Cypher 방언 | 성공 (3행) |
| `WITH p WHERE ...` | Cypher 방언 | 성공 (2행) |
| `-[:Knows]->{1,2}` (GQL 정량 경로) | GQL 표준 | 실패 — `Parser exception: Invalid input <...-[:Knows]->{>` |
| `(()-[:Knows]->()){1,2}` (GQL 정량 경로 패턴) | GQL 표준 | 실패 — `Parser exception` |
| `LET nm = p.name` | GQL 표준 | 실패 — `Parser exception` |
| `FILTER p.age > 30` | GQL 표준 | 실패 — `Parser exception` |
| `... NEXT RETURN n` | GQL 표준 | 실패 — `Parser exception` |

방언 쪽은 100% 성공, 표준 쪽은 100% 실패. 카드의 답이 그대로 재현됩니다.

---

## 2. 대응표: 가변 길이 경로 → GQL 정량 경로 패턴

Neo4j 공식 문서가 이 점을 명시적으로 적어 놨습니다.

> Prior to the introduction of the syntax for quantified path patterns and quantified relationships, the only way in Cypher to match paths of variable length was with a variable-length relationship. **This syntax is still available, but it is not GQL conformant.**
> — [Cypher Manual, Patterns → Syntax and semantics → Variable-length relationships](https://neo4j.com/docs/cypher-manual/current/patterns/reference/variable-length-paths/#variable-length-relationships)

GQL 표준이 채택한 표기는 **정량 경로 패턴(quantified path pattern, QPP)** 과 그 축약형인 **정량 관계(quantified relationship)** 이고, 수량자를 `*m..n` 대신 `{m,n}`으로 관계 패턴 **뒤에** 붙입니다.

### 수량자 대응표

| Cypher 방언 (가변 길이 관계) | 뜻 | GQL 정량 관계 | GQL 정량 경로 패턴 |
|---|---|---|---|
| `-[:Knows*1..2]->` | 1~2홉 | `-[:Knows]->{1,2}` | `(()-[:Knows]->()){1,2}` |
| `-[*]->` | 1홉 이상 | `-[]->+` | `(()-[]->())+` |
| `-[*n]->` | 정확히 n홉 | `-[]->{n}` | `(()-[]->()){n}` |
| `-[*m..]->` | m홉 이상 | `-[]->{m,}` | `(()-[]->()){m,}` |
| `-[*0..]->` | 0홉 이상 | `-[]->*` | `(()-[]->())*` |
| `-[*..n]->` | **1~n홉** | `-[]->{1,n}` | `(()-[]->()){1,n}` |
| `-[*0..n]->` | 0~n홉 | `-[]->{,n}` | `(()-[]->()){,n}` |

(출처: 같은 문서의 Variable-length relationships → Rules 표)

### 기계적 치환이 아니다 — 함정 넷

문서가 "동등하지만 다음 네 가지가 다르다"고 못 박아 둔 지점입니다.

1. **수량자의 위치와 표기가 다르다.** `-[:Knows*1..2]->` 는 대괄호 **안**, `-[:Knows]->{1,2}` 는 화살표 **뒤**.
2. **별표(`*`)의 의미가 다르다.** 가변 길이 관계의 `*` 는 하한이 1(`{1,}`, 즉 `+`)인데, 정량 경로 패턴의 `*` 는 Kleene star로 하한이 0(`{0,}`)입니다. `-[*]->` 를 `-[]->*` 로 바꾸면 **0홉 경로가 새로 섞여 들어옵니다.** 같은 이유로 `-[*..n]->` 는 `{,n}` 이 아니라 `{1,n}` 입니다.
3. **타입 표현식의 표현력이 다르다.** 가변 길이 관계에서는 논리합 `|` 만 쓸 수 있습니다(`&`, `!` 불가).
4. **`WHERE` 를 쓸 수 없다.** 가변 길이 관계 안에는 `WHERE` 가 허용되지 않지만, 정량 경로 패턴 안에서는 홉 단위 술어를 걸 수 있습니다. 즉 이식이 손실이 아니라 **표현력 상승**인 방향입니다.

추가로, 수량자가 붙은 패턴 안에서 선언된 변수는 **그룹 변수(group variable)** 가 되어 바깥에서는 리스트로 보입니다. `{1}` 을 붙인 정량 경로 패턴이 고정 길이 패턴과 같지 않은 이유가 이것입니다.

한 가지 더, GQL 계열은 **경로 모드/매치 모드**(`TRAIL`, `ACYCLIC`, `DIFFERENT RELATIONSHIPS`, `REPEATABLE ELEMENTS`)를 명시적으로 씁니다. 엔진마다 가변 길이 관계의 기본 모드가 달라서(Neo4j는 관계 유일성 기준, Kuzu는 재귀 관계 기본이 `WALK`이고 `TRAIL`/`ACYCLIC`을 별도 지정) **표기만 옮기면 결과 행 수가 바뀔 수 있습니다.** 9장에서 다룬 "상한을 걸어라"와 같은 층의 문제입니다.

---

## 3. 대응표: WITH → LET / FILTER / GROUP BY / NEXT

`WITH` 는 GQL 표준에 없는 절입니다. 없는 이유는 `WITH` 가 한 절에서 **너무 많은 일**을 하기 때문이고, GQL은 그 일들을 별개 문장으로 쪼개 놨습니다.

| `WITH` 가 하던 일 | GQL 표준 표기 |
|---|---|
| 새 변수 바인딩 (`WITH p.name AS nm`) | **`LET nm = p.name`** |
| 중간 결과 필터 (`WITH p WHERE p.age > 30`) | **`FILTER p.age > 30`** (독립 문장) |
| 변수 스코프 자르기 / 질의 조각 잇기 | **`NEXT`** (선형 질의 합성) |
| 집계와 그룹핑 (`WITH c, count(*) AS n`) | **`RETURN` / `GROUP BY`** |
| 정렬·페이징 (`WITH ... ORDER BY ... LIMIT`) | `ORDER BY`, `OFFSET`, `LIMIT` (독립 문장) |
| 중복 제거 (`WITH DISTINCT`) | `RETURN DISTINCT` 등 — `LET` 으로는 못 함 |

Microsoft Fabric의 GQL 언어 가이드가 표준 문장 목록을 그대로 나열해 두었는데, `MATCH` · `LET` · `FILTER` · `ORDER BY` · `OFFSET`/`LIMIT` · `RETURN` 이고 **`WITH` 는 없습니다.** 예시도 `Match → Let → Filter → Order → Limit → Return` 파이프라인으로 적혀 있습니다.

### `WITH` 와 `LET` 은 1:1이 아니다 — 여기가 이식의 핵심

Neo4j 문서의 `LET` 설명이 차이를 정확히 짚습니다.

> `LET` binds expressions to variables. ... **Unlike `WITH`, `LET` does not drop variables from the scope of subsequent clauses. Nor can it be used for aggregations or in combination with `DISTINCT`; it can only be used to bind new variables.**
> — [Cypher Manual, LET](https://neo4j.com/docs/cypher-manual/current/clauses/let/)

정리하면,

- `WITH` 는 **차단형(blocking)** 입니다. 이후에 쓸 변수를 전부 다시 나열해야 하고, 빼먹으면 스코프에서 사라집니다.
- `LET` 은 **비차단형** 입니다. 기존 컬럼을 건드리지 않고 새 컬럼만 덧붙입니다.
- 그래서 `WITH` 를 **스코프 자르기 목적**으로 쓰던 코드는 `LET` 으로 옮길 수 없습니다. 그건 `NEXT` 나 `RETURN` 의 일입니다.

---

## 4. 그래서 이식할 때 무엇을 고쳐야 하나

체크리스트 형태로.

1. **`*m..n` 을 `{m,n}` 으로.** 대괄호 안에서 화살표 뒤로 옮깁니다. 상·하한이 둘 다 적힌 형태(`*1..2`)는 안전한 기계적 치환입니다.
2. **하한이 생략된 표기를 전수 검사.** `*`, `*..n`, `*0..` 는 별표 의미가 달라지는 자리입니다. `*` → `+`, `*..n` → `{1,n}`. `*` → `*` 로 바꾸면 조용히 0홉이 늘어납니다.
3. **관계 타입 표현식 점검.** `|` 만 쓰고 있었는지 확인. 옮긴 뒤에는 `&`, `!` 도 쓸 수 있게 됩니다.
4. **행 수를 반드시 비교.** 경로 모드/매치 모드 기본값 차이 때문에 같은 뜻으로 옮겼는데 행 수가 달라질 수 있습니다. 이식 전후 결과를 `ORDER BY` 강제 후 diff 하세요(11장 요약의 "`ORDER BY` 를 강제하라"가 이걸 위한 것입니다).
5. **`WITH` 를 용도별로 분해.** 한 `WITH` 를 통째로 한 절로 못 옮깁니다. 「바인딩」은 `LET`, 「필터」는 `FILTER`, 「스코프 자르기·조각 잇기」는 `NEXT`, 「집계」는 `RETURN`/`GROUP BY` 로 쪼갭니다.
6. **`WITH` 로 스코프를 좁혀 성능을 얻던 곳을 표시.** `LET` 은 컬럼을 줄여 주지 않으므로 그 최적화가 사라집니다. `NEXT` 로 옮겨야 합니다.
7. **GQL에 대응이 없는 것은 격리.** `MERGE`, `LOAD CSV`, `COLLECT`/`COUNT`/`EXISTS` 서브질의, `shortestPath()`/`allShortestPaths()`(이것도 비준수), `CALL { ... } IN TRANSACTIONS` 는 GQL 대안이 아직 없습니다. 11.3절이 말한 "엔진 고유 함수는 별도 파일로 격리한다"의 실제 대상 목록입니다.

---

## 5. 2026년 8월의 현황 — 방언이 남는 방향이 아니라 좁혀지는 방향

카드의 "GQL 표준에는 없지만 Cypher 계열 엔진이 지원한다"는 문장은 지금도 맞지만, **역방향도 이미 움직이고 있습니다.**

| 문법 | GQL 표준 | Kuzu 0.11.3 (직접 확인) | Neo4j Cypher 25 |
|---|---|---|---|
| `-[:Knows*1..2]->` | 없음 (비준수) | 지원 | 지원 (계속 유지, 비준수 명시) |
| `-[:Knows]->{1,2}` | 표준 | 미지원 | 지원 |
| `WITH` | 없음 | 지원 | 지원 |
| `LET` | 표준 | 미지원 | 지원 (2025.06 도입) |
| `FILTER` | 표준 | 미지원 | 지원 (2025.06 도입) |
| `NEXT` | 표준 | 미지원 | 지원 (2025.06 도입) |
| `GROUP BY` | 표준 | — | 지원 (2026.07 도입) |
| `FOR ... IN` (`UNWIND` 대체) | 표준 | 미지원 | 지원 (2026.04 도입) |

Neo4j는 GQL 준수 문법을 **추가**하면서 방언 문법을 **폐기하지 않고 병존**시키는 길을 골랐습니다(문서에 "still available, but not GQL conformant"라고 적어 두는 방식). 그래서 예제 `ex3` 의 결과는 **엔진 선택의 함수**입니다 — Kuzu에서는 GQL 전용 절이 전부 실패하지만, Neo4j 2025.06 이상에서는 `LET`/`FILTER`/`NEXT` 가 통과합니다. 카드를 외울 때 "어떤 엔진에서 실패했는가"를 같이 기억해 두는 게 정확합니다.

---

## 6. 근거 (1차 출처)

| 주장 | 출처 |
|---|---|
| 가변 길이 관계는 GQL 비준수, 정량 경로 패턴이 표준 표기 | [Cypher Manual — Patterns → Syntax and semantics → Variable-length relationships](https://neo4j.com/docs/cypher-manual/current/patterns/reference/variable-length-paths/#variable-length-relationships) |
| 같은 문장이 튜토리얼 페이지에도 반복 | [Cypher Manual — Variable-length paths](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-paths/) / [Basic queries](https://neo4j.com/docs/cypher-manual/current/queries/basic/) |
| 수량자 대응표(`*m..n` ↔ `{m,n}`), 별표 의미 차이, `WHERE` 불허, 타입 표현식 제약 | 위 Variable-length relationships → Rules |
| `LET` 은 `WITH` 와 달리 스코프를 떨어뜨리지 않고, 집계·`DISTINCT` 불가 | [Cypher Manual — LET](https://neo4j.com/docs/cypher-manual/current/clauses/let/) |
| `NEXT` 는 `WITH` 대신 질의를 선형 합성하는 데 쓸 수 있다 | [Cypher Manual — Sequential queries (NEXT)](https://neo4j.com/docs/cypher-manual/current/queries/composed-queries/sequential-queries/) |
| Cypher의 GQL 준수 범위 / 비준수 목록 (`MERGE`, `LOAD CSV`, 서브질의 등) | [Cypher Manual — Appendix: GQL conformance](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/) (Additional Cypher features 하위 페이지 포함) |
| GQL 표준 문장 목록에 `WITH` 가 없고 `MATCH`/`LET`/`FILTER`/`ORDER BY`/`LIMIT`/`RETURN` 파이프라인이다 · 상한 있는 정량 패턴 `-[:knows]->{1,3}` | [GQL Language Guide for graph in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/graph/gql-language-guide) |
| 표준 자체 | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| Kuzu 0.11.3 지원/미지원 | 본 힌트 작성 시 로컬 실행으로 직접 확인 (2026-08) |

주의: Neo4j 문서 페이지는 `current` 채널이라 시간이 지나면 내용이 바뀝니다. 위 확인 시점은 Cypher Manual 상 **Neo4j 2026.06 / 최종 갱신 2026년 6월 1일** 판입니다.
