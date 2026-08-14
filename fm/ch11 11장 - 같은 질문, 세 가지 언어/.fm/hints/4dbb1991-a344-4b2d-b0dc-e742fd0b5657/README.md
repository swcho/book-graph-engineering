# SQL/PGQ에서 그래프 패턴 질의는 어떻게 쓰는가?

## 한 줄 답

```sql
SELECT * FROM GRAPH_TABLE (graph
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract)
  ...
  COLUMNS (...)
);
```

`FROM` 절에 **`GRAPH_TABLE(...)`** 연산자를 놓고, 그 안에 그래프 이름 → `MATCH` 패턴 → (선택) `WHERE` → `COLUMNS`를 차례로 쓴다. 밖은 평범한 SQL, 안은 그래프 패턴이다.

---

## 왜 이 모양인가

SQL/PGQ의 설계 목표는 **"테이블을 옮기지 않고 그래프로 보기"**다. 11장 요약이 그대로 그 말을 한다.

> SQL/PGQ는 데이터를 옮기지 않고 그래프 시각만 얹습니다. 매력적인데 구현이 아직 덜 퍼졌고, 조인 폭발은 그대로 남습니다.

그래서 문법도 **SQL 안에 그래프를 끼워 넣는** 형태가 되어야 했다. `GRAPH_TABLE`은 그 이음새다. 들어갈 때는 관계형 세계에서 그래프 세계로, 나올 때는 그래프 세계에서 관계형 세계로 넘어간다.

```
관계형 SQL  ──[ GRAPH_TABLE( ]──▶  그래프 패턴 매칭
                                   (MATCH / WHERE)
                                          │
                                     COLUMNS(...)
관계형 SQL  ◀──[ ) ]──────────────  관계형 행 집합
```

Oracle 문서는 이 성격을 이렇게 못 박는다.

> GRAPH_TABLE is a new operator in the FROM clause which executes the graph query (pattern) against a given graph and returns matches **in tabular form** for further processing with regular SQL.
> — [Property Graphs in Oracle Database 23ai: The SQL/PGQ Standard](https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard)

`FROM` 절의 연산자라는 게 핵심이다. 결과가 테이블이므로 바깥에서 `WHERE`, `ORDER BY`, `GROUP BY`, 다른 테이블과의 `JOIN`을 그냥 얹을 수 있다.

---

## 절 단위 분해

### 0. 전제 — `CREATE PROPERTY GRAPH` (질의가 아니라 선언)

`GRAPH_TABLE`이 참조할 그래프 이름은 미리 선언해 둔다. 예제 `code/ex4_sql_pgq.py`의 선언부다.

```sql
-- SQL/PGQ 표준 문법 (ISO/IEC 9075-16:2023)
CREATE PROPERTY GRAPH biz
  VERTEX TABLES (
    company KEY (name) LABEL Company PROPERTIES (name, grade),
    contract KEY (id)  LABEL Contract PROPERTIES (id, started_on, ended_on)
  )
  EDGE TABLES (
    signed     SOURCE KEY (company_name) REFERENCES company (name)
               DESTINATION KEY (contract_id) REFERENCES contract (id)
               LABEL Signed,
    terminated SOURCE KEY (company_name) REFERENCES company (name)
               DESTINATION KEY (contract_id) REFERENCES contract (id)
               LABEL Terminated
  );
```

읽는 법:

| 조각 | 뜻 |
|---|---|
| `VERTEX TABLES (...)` | 어느 테이블의 행이 **노드**인가 |
| `KEY (name)` | 노드 신원(identity)을 만드는 열 |
| `LABEL Company` | 그 노드에 붙는 라벨. 패턴에서 `IS Company`로 부를 이름 |
| `PROPERTIES (name, grade)` | 그래프 속성으로 노출할 열 (`PROPERTIES ALL COLUMNS`도 가능) |
| `EDGE TABLES (...)` | 어느 테이블의 행이 **간선**인가 |
| `SOURCE KEY (...) REFERENCES ...` | 간선의 출발 노드를 어느 노드 테이블의 어느 키로 찾는가 |
| `DESTINATION KEY (...) REFERENCES ...` | 도착 노드 쪽 같은 것 |

이 선언은 **데이터를 복사하지 않는다.** `company`, `contract`, `signed`, `terminated` 테이블은 그대로 남고, 그 위에 "노드/간선"이라는 해석만 덧씌운다. DuckPGQ 문서 표현으로는 "a layer on top of existing tables"다 ([Property Graph — DuckPGQ](https://duckpgq.org/documentation/property_graph/)).

### 1. 그래프 이름 — `GRAPH_TABLE (biz ...`

`GRAPH_TABLE`의 첫 토큰은 대상 그래프 이름이다. 쉼표가 없다는 점을 놓치기 쉽다. `GRAPH_TABLE (biz MATCH ...)` — `biz` 뒤에 바로 `MATCH`가 붙는다.

### 2. `MATCH` — 패턴, 그리고 `IS <label>` 표기

```sql
MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
      (c)-[IS Signed]->(n IS Contract)
```

- 노드는 소괄호 `()`, 간선은 대괄호 `[]`, 방향은 `->` / `<-` / `-` (무방향). Cypher에서 온 "그림 문법(ASCII art)"이다.
- **라벨은 `IS` 키워드로 붙인다.** `(c IS Company)`는 "변수 `c`는 라벨 `Company`를 갖는 노드"라는 뜻이다. Cypher의 `(c:Company)`와 같은 자리인데 표기가 다르다. Oracle 문서가 명시한다: *"Label Notation: Uses `IS` keyword (e.g., `p1 is person`), not colon syntax"* ([ORACLE-BASE](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23)).
- 변수 이름은 생략할 수 있다. `-[IS Terminated]->`처럼 간선을 나중에 참조하지 않으면 이름을 안 붙인다. 반대로 `(c)`처럼 **이미 바인딩된 변수를 라벨 없이 재사용**해서 두 패턴을 같은 노드로 묶는다. 위 예제에서 두 줄이 쉼표로 이어져 있고 둘 다 `c`를 쓰므로, "같은 회사가 하나를 해지하고 다른 하나를 체결"이라는 조건이 성립한다.
- 쉼표로 여러 경로 패턴을 나열하면 교집합(모두 만족)이다. Cypher와 같다.

> 참고: `IS`가 표준 표기지만, 구현체가 콜론 표기를 함께 받아 주기도 한다. DuckPGQ는 콜론 표기를 쓴다 — `MATCH (a:Person)-[k:Knows]->(b:Person)` ([SQL/PGQ — DuckPGQ](https://duckpgq.org/documentation/sql_pgq/)). 즉 **표기의 이식성 자체가 아직 흔들린다.** 11장이 반복하는 "표준이 나왔다 ≠ 표준대로 돌아간다"의 한 사례다.

### 3. `WHERE` — 패턴에 붙는 술어

```sql
WHERE o.ended_on < n.started_on
```

바인딩된 변수의 속성에 걸는 조건이다. 여기서 `o.ended_on`은 `contract` 테이블의 `ended_on` 열인데, `CREATE PROPERTY GRAPH`의 `PROPERTIES (...)`에 올려 뒀기 때문에 그래프 속성으로 보인다.

두 가지를 구분해 두자.

| 위치 | 형태 | 성격 |
|---|---|---|
| `GRAPH_TABLE` **안**의 `WHERE` | `MATCH ... WHERE o.ended_on < n.started_on` | 그래프 패턴 매칭 중 필터. 매칭 자체를 줄인다 |
| 노드/간선 패턴 **내부**의 `WHERE` | `(o IS Contract WHERE o.ended_on < DATE '2025-01-01')` | 요소 패턴에 인라인으로 붙는 필터 |
| `GRAPH_TABLE` **밖**의 `WHERE` | `SELECT * FROM GRAPH_TABLE (...) WHERE 고객 LIKE '가온%'` | 이미 관계형 행이 된 결과에 대한 평범한 SQL 필터 |

인라인 형태는 PostgreSQL SQL/PGQ 패치 소개 글의 예제에서 볼 수 있다.

```sql
SELECT customer_name FROM GRAPH_TABLE (myshop
  MATCH (c IS customer)-[IS has_placed]->(o IS "order"
         WHERE o.ordered_when = current_date)
  COLUMNS (c.name AS customer_name));
```
— [SQL Property Graph Queries (SQL/PGQ): Bringing Graph Queries to PostgreSQL](https://pgweekly.github.io/en/2026/07/sql-property-graph-queries-pgq.html)

그리고 Oracle 문서는 `GRAPH_TABLE` 안의 `WHERE`/`COLUMNS`가 특수 언어가 아니라는 점을 강조한다.

> WHERE and COLUMNS clauses inside GRAPH_TABLE use the **same operators, functions and predicates** as are available elsewhere in SQL.

### 4. `COLUMNS(...)` — 그래프 결과를 관계형 행으로 되돌리는 문

```sql
COLUMNS (c.name AS 고객)
```

**이 절이 없으면 `GRAPH_TABLE`은 테이블이 될 수 없다.** `MATCH`가 만들어 낸 것은 변수 바인딩의 집합(binding table)이다. `c`는 노드, `o`와 `n`도 노드다. 노드는 SQL의 값 타입이 아니다. `COLUMNS`는 "그 바인딩에서 어떤 **스칼라 표현식**을 뽑아 어떤 열 이름으로 내보낼지"를 지정해서, 그래프 세계의 결과를 SQL이 다룰 수 있는 행으로 투영(projection)한다.

- Oracle 문서: *"COLUMNS clause **defines the columns available in the select list**"*, *"COLUMNS clause specifies what to return from the query"*.
- DuckPGQ 문서: *"Returns selected attributes as **relational output**"*.

그래서 `SELECT * FROM GRAPH_TABLE (...)`의 `*`가 가리키는 것은 원본 테이블의 열 전체가 아니라 **`COLUMNS`에 나열한 열들**이다. 위 예제에서 `SELECT *`는 곧 `SELECT 고객`이다.

`COLUMNS`에 올릴 수 있는 것:

| 종류 | 예 |
|---|---|
| 속성 접근 | `c.name AS 고객`, `o.ended_on` |
| SQL 표현식 | `n.started_on - o.ended_on AS 공백일수` |
| 요소 신원 함수 | `VERTEX_ID(c)`, `EDGE_ID(e)` (Oracle: 그래프 시각화용 JSON 식별자) |
| 경로 함수 | `path_length(p)`, `vertices(p)`, `edges(p)`, `element_id(p)` (DuckPGQ) |
| 전체 속성 | 23ai 이후 정점/간선의 모든 속성을 한 번에 선택하는 지원이 추가됨 |

역할을 한 줄로: **`MATCH`는 그래프를 걷고, `COLUMNS`는 걸어서 얻은 것을 표로 접는다.**

### 5. 정렬은 밖에서

`GRAPH_TABLE` 결과가 관계형 테이블이니 정렬은 바깥 SQL이 한다.

```sql
SELECT * FROM GRAPH_TABLE (biz MATCH ... COLUMNS (c.name AS 고객))
 ORDER BY 고객;
```

11장이 이식 대비 수칙으로 "`ORDER BY`를 강제하라"고 한 것과 그대로 맞물린다. 그래프 패턴 매칭은 순서를 보장하지 않는다.

---

## 예제의 실제 질의 (`code/ex4_sql_pgq.py`)

```sql
SELECT * FROM GRAPH_TABLE (biz
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
        (c)-[IS Signed]->(n IS Contract)
  WHERE o.ended_on < n.started_on
  COLUMNS (c.name AS 고객)
);
```

묻는 질문은 **"계약을 해지했다가 나중에 새 계약을 체결한 회사"**다.

`seed.py` 데이터로 손으로 풀어 보면:

| 회사 | Terminated → 계약 | `ended_on` | Signed → 계약 | `started_on` | `ended_on < started_on` |
|---|---|---|---|---|---|
| 가온테크 | M-2021-077 | 2024-03-11 | C-2025-118 | 2025-06-02 | ✅ |
| 라온에너지 | M-2020-031 | 2024-08-05 | (없음) | — | 패턴 불성립 |
| 나루소프트 | (없음) | — | C-2025-004 | 2025-01-20 | 패턴 불성립 |
| 다올물산 | (없음) | — | C-2026-010 | 2026-02-01 | 패턴 불성립 |

→ 답은 `['가온테크']`.

예제는 SQL/PGQ 문법을 **출력만** 하고, 실제 채점은 같은 뜻의 평범한 SQL로 한다.

```sql
SELECT DISTINCT c.name AS 고객
  FROM company c
  JOIN terminated t ON t.company_name = c.name
  JOIN contract  o ON o.id = t.contract_id
  JOIN signed    s ON s.company_name = c.name
  JOIN contract  n ON n.id = s.contract_id
 WHERE o.ended_on < n.started_on
 ORDER BY 고객
```

**조인 5개가 화살표 2개로 줄었다.** 이게 `GRAPH_TABLE`이 사는 값이다. 그런데 아래도 같이 봐야 한다 — 예제 주석이 직접 말한다.

> 옮기지 않아도 된다는 게 공짜라는 뜻은 아니다. 조인 폭발은 그대로 남는다(3장). 저장 위치가 아니라 «따라가는 값»이 문제였으니까.

문법이 짧아졌다고 실행이 싸진 건 아니다. 엔진은 결국 저 조인을 수행한다 (PostgreSQL 패치도 "maps graphs onto the relational model through **query rewriting**"이라고 설명한다).

---

## 같은 질문, Cypher 표기와 나란히

`code/ex1_three_languages.py`의 Cypher는 문자 그대로 이렇다.

```cypher
MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
WHERE o.endedOn < n.startedOn
RETURN c.name AS 고객
ORDER BY 고객
```

절 대 절로 놓으면:

| 역할 | Cypher | SQL/PGQ |
|---|---|---|
| 대상 그래프 지정 | 접속한 DB가 곧 그래프 (문법 없음) | `GRAPH_TABLE (biz ...)` — 이름을 명시 |
| 그래프 정의 | `CREATE NODE TABLE` / `CREATE REL TABLE` 등 **데이터를 넣는다** | `CREATE PROPERTY GRAPH` — 기존 테이블 위에 **뷰만 얹는다** |
| 패턴 | `MATCH (c:Company)-[:Terminated]->(o:Contract)` | `MATCH (c IS Company)-[IS Terminated]->(o IS Contract)` |
| 라벨 표기 | 콜론 `:Company` | **`IS Company`** |
| 필터 | `WHERE o.endedOn < n.startedOn` | `WHERE o.ended_on < n.started_on` (GRAPH_TABLE 안) |
| 결과 투영 | `RETURN c.name AS 고객` | **`COLUMNS (c.name AS 고객)`** |
| 정렬 | `ORDER BY 고객` (같은 질의 안) | `ORDER BY 고객` (**GRAPH_TABLE 밖**, 평범한 SQL) |
| 결과 타입 | 노드·관계·경로도 그대로 반환 가능 | `COLUMNS`를 통과한 **스칼라 열만** |

핵심 차이 세 개만 기억하면 된다.

1. **`:` → `IS`**
2. **`RETURN` → `COLUMNS(...)`** (그리고 이건 질의의 끝이 아니라 `GRAPH_TABLE`의 끝이다)
3. **`GRAPH_TABLE`은 `FROM` 절 안에 산다.** 밖은 여전히 SQL이므로 `ORDER BY`, 집계, 다른 테이블과의 조인이 자연스럽게 붙는다. Cypher는 그래프 질의가 곧 전체 질의고, SQL/PGQ는 그래프 질의가 **SQL 질의의 한 테이블**이다.

세 번째가 SQL/PGQ의 진짜 매력이다. "해지 후 재체결한 회사"를 뽑아서 곧바로 회계 테이블과 조인하고 월별로 집계하는 일이, 두 시스템을 왕복하지 않고 한 질의로 끝난다. 3장의 "두 벌 운영" 비용을 안 내는 것 — 예제 주석의 표현대로다.

---

## 자주 틀리는 곳

| 실수 | 왜 틀렸나 |
|---|---|
| `MATCH (c:Company)`로 쓴다 | 표준 표기는 `IS`. 엔진에 따라 콜론을 받아 주기도 하지만 이식성이 없다 |
| `COLUMNS`를 빼먹는다 | 그래프 바인딩은 SQL 값이 아니다. `COLUMNS` 없으면 테이블이 만들어지지 않는다 |
| `COLUMNS (c)`처럼 노드 자체를 넣는다 | 스칼라 표현식이어야 한다. 신원이 필요하면 `VERTEX_ID(c)` |
| `GRAPH_TABLE (biz, MATCH ...)`처럼 쉼표를 넣는다 | 그래프 이름과 `MATCH` 사이에 구분자가 없다 |
| `ORDER BY`를 `GRAPH_TABLE` 안에 쓴다 | 정렬은 관계형 행이 된 뒤, 바깥 SQL에서 한다 |
| `SELECT *`가 원본 테이블 전체 열이라고 생각한다 | `COLUMNS`에 나열한 열이 전부다 |
| 문법이 짧아졌으니 빨라졌다고 본다 | 엔진은 질의 재작성으로 결국 같은 조인을 수행한다. 조인 폭발은 남는다 |

---

## 확인 시점과 구현 현황 (2026년 8월 기준)

표준은 **[표준]** [ISO/IEC 9075-16:2023 — Database languages SQL — Part 16: Property Graph Queries (SQL/PGQ)](https://www.iso.org/standard/79473.html)다. 2023년 6월 발행이고, 2026년에 [Technical Corrigendum 1](https://www.iso.org/standard/93698.html)이 나왔다.

| 엔진 | 상태 |
|---|---|
| Oracle Database 23ai / 26ai | `GRAPH_TABLE` 구현. `IS` 라벨 표기, `SOURCE`/`DESTINATION` 술어, `COLUMNS`에서 전체 속성 선택 등 확장 |
| DuckDB (DuckPGQ 확장) | 커뮤니티 확장으로 `CREATE PROPERTY GRAPH` + `GRAPH_TABLE` 제공. 단 **라벨은 콜론 표기** |
| PostgreSQL | 패치가 아직 커밋되지 않음. 2026-01 시점 v20260113 패치가 118개 파일 약 14,800줄 규모 |

예제 파일이 `sqlite3`로 돌면서 SQL/PGQ 문법은 출력만 하는 이유가 여기 있다.

> SQL/PGQ(ISO/IEC 9075-16:2023)를 실제로 구현한 엔진이 아직 널리 퍼지지 않아서, 여기서는 «표준 문법»을 보여 주고 같은 뜻의 평범한 SQL을 돌려서 답을 맞춰 본다.

> 다만 2026년 8월 기준으로, 이 문법을 프로덕션에서 쓰는 팀을 저는 못 봤다. 구현이 덜 퍼졌다. 그래서 이 예제는 «돌아가는 코드»가 아니라 «앞으로 이렇게 될 가능성»을 보여 주는 것이다. 확인 시점을 꼭 같이 읽어 달라.

---

## 암기용 골격

```sql
SELECT <열>
  FROM GRAPH_TABLE ( <그래프이름>
         MATCH   <패턴, IS 라벨>
         WHERE   <술어>
         COLUMNS ( <표현식> AS <별칭> )
       )
 ORDER BY <열>;          -- 정렬은 밖에서
```

읽는 순서: **어느 그래프에서(그래프 이름) → 어떤 모양을 찾아(MATCH) → 어떤 조건만 남기고(WHERE) → 어떤 열로 내보낼지(COLUMNS)**, 그리고 그 결과는 그냥 테이블.

---

## 출처

- [ISO/IEC 9075-16:2023 — SQL Part 16: Property Graph Queries (SQL/PGQ)](https://www.iso.org/standard/79473.html)
- [ISO/IEC 9075-16:2023/Cor 1:2026 — Technical Corrigendum 1](https://www.iso.org/standard/93698.html)
- [Property Graphs in Oracle Database 23ai: The SQL/PGQ Standard (Oracle Blog)](https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard)
- [SQL Property Graphs and SQL/PGQ in Oracle Database 23ai/26ai (ORACLE-BASE)](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23)
- [Key Property Graph Features in Oracle Database Release 23ai (Oracle Docs)](https://docs.oracle.com/en/database/oracle/property-graph/24.4/spgdg/key-property-graph-features-oracle-database-release-23ai.html)
- [SQL/PGQ — DuckPGQ Documentation](https://duckpgq.org/documentation/sql_pgq/)
- [Property Graph — DuckPGQ Documentation](https://duckpgq.org/documentation/property_graph/)
- [DuckPGQ: Bringing SQL/PGQ to DuckDB (VLDB 2023, PDF)](https://www.vldb.org/pvldb/vol16/p4034-wolde.pdf)
- [SQL Property Graph Queries (SQL/PGQ): Bringing Graph Queries to PostgreSQL (Postgres Weekly, 2026-07)](https://pgweekly.github.io/en/2026/07/sql-property-graph-queries-pgq.html)
- [Graph Pattern Matching in GQL and SQL/PGQ (arXiv:2112.06217)](https://arxiv.org/abs/2112.06217)
- 11장 예제: `code/ex4_sql_pgq.py`, `code/ex1_three_languages.py`, `code/seed.py`
