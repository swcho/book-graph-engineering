# SQL/PGQ에서 그래프를 선언하는 문법

## 질문

SQL/PGQ에서 그래프를 선언하는 문법은 무엇인가?

## 답

`CREATE PROPERTY GRAPH`로 VERTEX TABLES와 EDGE TABLES를 지정한다. 엣지 테이블에는 SOURCE KEY와 DESTINATION KEY로 참조를 적는다.

---

## 한 문장으로

이미 있는 관계형 테이블에 **「어느 테이블이 노드고, 어느 테이블이 엣지고, 엣지의 양 끝은 어느 컬럼으로 이어지는가」**를 선언하는 DDL이다. 데이터는 한 줄도 옮기지 않는다.

## 11장 예제의 실제 DDL

`content/ch11/code/ex4_sql_pgq.py`가 그대로 담고 있는 문장입니다.

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

이 그래프가 얹히는 밑바닥 테이블은 평범한 4개짜리 스키마입니다. 그래프 선언 전과 후에 이 테이블들은 **아무것도 달라지지 않습니다.**

```sql
CREATE TABLE company    (name TEXT PRIMARY KEY, grade TEXT);
CREATE TABLE contract   (id TEXT PRIMARY KEY, started_on TEXT, ended_on TEXT);
CREATE TABLE signed     (company_name TEXT, contract_id TEXT);
CREATE TABLE terminated (company_name TEXT, contract_id TEXT);
```

## 절 단위로 분해

### 1. `CREATE PROPERTY GRAPH <이름>`

그래프의 이름을 짓는 머리 부분입니다. 여기서 지은 이름(`biz`)이 나중에 질의할 때 `GRAPH_TABLE(biz ...)`로 다시 등장합니다. 구현체에 따라 `CREATE OR REPLACE PROPERTY GRAPH`, `IF NOT EXISTS`를 받습니다.

### 2. `VERTEX TABLES ( ... )` — 노드가 될 테이블

각 항목의 뼈대는 `테이블명 KEY(...) LABEL ... PROPERTIES (...)`입니다.

| 절 | 뜻 | 예제에서 |
|---|---|---|
| 테이블명 | 이 테이블의 **한 행이 노드 하나**가 된다 | `company`, `contract` |
| `KEY (...)` | 노드의 신원(identity). 행을 유일하게 가리키는 컬럼 | `KEY (name)`, `KEY (id)` |
| `LABEL ...` | 그래프 세계에서 부를 이름. 질의문의 `(c IS Company)`가 이걸 가리킨다 | `LABEL Company` |
| `PROPERTIES (...)` | 노드 속성으로 노출할 컬럼 목록 | `PROPERTIES (name, grade)` |

핵심 감각은 **행 하나 = 노드 하나**입니다. `company`에 4행이 있으면 `Company` 라벨 노드가 4개 생긴 것처럼 보입니다.

`KEY`는 생략하면 테이블의 기본키를 쓰는 게 일반적이고, `PROPERTIES`도 생략형이 있습니다. 실제 구현체들이 지원하는 변형은 이렇습니다.

- `PROPERTIES ARE ALL COLUMNS` / Oracle 표기 `PROPERTIES ALL COLUMNS` — 전 컬럼을 속성으로
- `PROPERTIES ARE ALL COLUMNS EXCEPT (...)` — 전 컬럼에서 일부만 빼고
- `NO PROPERTIES` — 속성 없이 위치(topology)만
- 컬럼에 표현식·별칭을 붙이는 것도 됩니다 (Oracle은 `json_value(people.json_data, '$.universe') AS universe` 같은 것까지 허용)

### 3. `EDGE TABLES ( ... )` — 엣지가 될 테이블

여기가 SQL/PGQ의 심장입니다. 노드 선언에 없던 두 절이 추가됩니다.

```
테이블명
  SOURCE KEY      (내_컬럼) REFERENCES 시작노드테이블 (그쪽_컬럼)
  DESTINATION KEY (내_컬럼) REFERENCES 끝노드테이블   (그쪽_컬럼)
  LABEL ...
  PROPERTIES (...)
```

| 절 | 뜻 |
|---|---|
| `SOURCE KEY (c) REFERENCES T (k)` | 이 엣지의 **꼬리**. 내 컬럼 `c`의 값이 `T` 테이블의 `k` 값과 같은 노드에서 출발한다 |
| `DESTINATION KEY (c) REFERENCES T (k)` | 이 엣지의 **머리**. 같은 방식으로 도착 노드를 찾는다 |

예제를 그대로 읽으면 이렇습니다.

```sql
signed SOURCE KEY (company_name) REFERENCES company (name)
       DESTINATION KEY (contract_id) REFERENCES contract (id)
       LABEL Signed
```

「`signed` 테이블의 한 행은 `Signed` 라벨 엣지 하나다. 그 행의 `company_name` 값과 `name`이 같은 `company` 노드에서 출발해, `contract_id` 값과 `id`가 같은 `contract` 노드로 향한다.」

즉 **외래키 관계를 화살표로 다시 읽는 선언**입니다. 원래 조인 조건이었던 `t.company_name = c.name`이 여기서는 `-[IS Terminated]->`라는 화살표로 승격됩니다.

`SOURCE`/`DESTINATION` 이라는 이름 때문에 엣지에 방향이 반드시 생긴다는 점도 기억해 두면 좋습니다. 무방향으로 쓰고 싶으면 질의 쪽에서 방향 없는 패턴(`-[...]-`)을 쓰거나, 양방향 행을 넣어야 합니다.

### 4. 선언과 질의는 별개

`CREATE PROPERTY GRAPH`는 **선언(DDL)까지**입니다. 실제로 걸어 다니는 건 `GRAPH_TABLE`이 담당합니다.

```sql
SELECT * FROM GRAPH_TABLE (biz
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
        (c)-[IS Signed]->(n IS Contract)
  WHERE o.ended_on < n.started_on
  COLUMNS (c.name AS 고객)
);
```

여기서 `IS Company`, `IS Terminated`가 DDL의 `LABEL`을 가리키고, `COLUMNS(...)`가 그래프 패턴 매칭 결과를 다시 **평범한 관계형 행**으로 되돌려 놓습니다. 그래서 `GRAPH_TABLE(...)`은 `FROM` 절에서 테이블처럼 쓸 수 있고, 바깥에 `JOIN`이나 `GROUP BY`를 그대로 붙일 수 있습니다.

## 왜 중요한가 — 「데이터 복제가 없다」

이 카드에서 진짜로 외워야 할 건 문법 철자가 아니라 이 성질입니다.

Oracle 문서 해설은 이 점을 딱 잘라 말합니다. **"There is no data materialized by the SQL property graph, it is just metadata. All the actual data comes from the referenced objects."** ([ORACLE-BASE](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23))

그래서 이런 것들이 따라옵니다.

- **적재 없음.** ETL로 그래프 DB에 붓는 단계가 사라집니다. `CREATE PROPERTY GRAPH`는 카탈로그에 정의를 하나 추가할 뿐입니다.
- **동기화 없음.** 원본 테이블에 `INSERT`가 들어오면 그래프 시각에서도 그 즉시 보입니다. 별도 복제본이 없으니 뒤처질 것도 없습니다.
- **두 벌 운영 비용이 없음.** 3장에서 나온 「관계형 한 벌 + 그래프 한 벌」의 이중 운영 부담을 안 냅니다.
- **뷰(view)와 같은 계층.** SQL 뷰가 테이블에 「다른 모양」을 얹듯, 프로퍼티 그래프는 테이블에 「그래프라는 시각」을 얹습니다.

### 공짜는 아니다 — 예제가 굳이 붙여 놓은 경고

`ex4_sql_pgq.py`의 마지막 출력이 이 카드의 반대쪽 절반입니다.

> 옮기지 않아도 된다는 게 공짜라는 뜻은 아니다. **조인 폭발은 그대로 남는다**(3장). 저장 위치가 아니라 «따라가는 값»이 문제였으니까.

문법이 예뻐진 것과 실행이 빨라진 것은 다른 얘기입니다. 밑에서 도는 건 여전히 그 테이블들에 대한 조인이고, 홉이 깊어질 때 터지던 조인은 문법을 바꿔도 그대로 터집니다. SQL/PGQ가 없애는 건 **표현의 고통**(재귀 CTE 스무 줄)과 **운영의 고통**(두 벌 운영)이고, **실행의 고통**은 남습니다.

그리고 예제 자체가 sqlite3로 「같은 뜻의 평범한 SQL」을 돌려서 답을 맞춰 보는 구조인 이유도 여기 있습니다. 확인 시점 2026년 8월 기준으로 이 문법을 프로덕션에서 쓰는 팀을 저자는 보지 못했다고 적어 두었습니다. 예제는 **돌아가는 코드가 아니라 앞으로 이렇게 될 가능성**을 보여 주는 것입니다.

## 실제 구현체 확인 (근거)

문법이 종이 위에만 있는 게 아니라는 걸 확인해 봤습니다.

### 표준 자체

- **ISO/IEC 9075-16:2023** — *Information technology — Database languages SQL — Part 16: Property Graph Queries (SQL/PGQ)*. 2023년 6월 발행, 269쪽. SQL:2023의 완전히 새로운 Part 16입니다. ([ISO](https://www.iso.org/standard/79473.html))
- 2026년 8월에 **Technical Corrigendum 1** (ISO/IEC 9075-16:2023/Cor 1:2026)이 나왔습니다. 표준 문서 자체도 아직 다듬어지는 중이라는 신호입니다. ([ISO](https://www.iso.org/standard/93698.html))
- 그래프 질의 언어 GQL(**ISO/IEC 39075:2024**)과는 다른 표준입니다. GQL은 그래프 네이티브 DB를 위한 독립 언어, SQL/PGQ는 관계형 SQL 안에 붙인 그래프 절입니다. SQL/PGQ의 패턴 매칭 문법과 GQL의 패턴 매칭 문법은 의도적으로 같은 뿌리를 공유합니다.

### Oracle Database 23ai / 26ai

절 구조가 11장 예제와 정확히 일치합니다. ([Oracle CREATE PROPERTY GRAPH 문서](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-property-graph.html), [ORACLE-BASE](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23))

```sql
CREATE PROPERTY GRAPH bank_graph
VERTEX TABLES (
  BANK_ACCOUNTS KEY (ID) PROPERTIES (ID, Name, Balance)
)
EDGE TABLES (
  BANK_TRANSFERS KEY (TXN_ID)
    SOURCE KEY (src_acct_id) REFERENCES BANK_ACCOUNTS(ID)
    DESTINATION KEY (dst_acct_id) REFERENCES BANK_ACCOUNTS(ID)
    PROPERTIES (src_acct_id, dst_acct_id, amount)
)
```

```sql
CREATE PROPERTY GRAPH connections_pg
  VERTEX TABLES (
    people KEY (person_id) LABEL person PROPERTIES ALL COLUMNS
  )
  EDGE TABLES (
    connections KEY (connection_id)
      SOURCE KEY (person_id_1) REFERENCES people (person_id)
      DESTINATION KEY (person_id_2) REFERENCES people (person_id)
      LABEL connection PROPERTIES ALL COLUMNS
  );
```

**여기서 눈에 띄는 차이 하나**: Oracle 예제들은 엣지 테이블에도 `KEY (TXN_ID)`, `KEY (connection_id)`처럼 **엣지 자신의 키**를 적습니다. 11장 예제의 `signed`/`terminated`에는 이 절이 없고, 밑바닥 테이블에도 기본키 컬럼이 없습니다. 엣지의 신원을 정할 수 없으면 실제 엔진에서는 거부될 수 있는 부분입니다. 표준 문법을 보여 주려고 최소 형태로 줄인 예제이니, 실제 Oracle에 옮길 때는 `signed`/`terminated`에 대리키를 하나 두고 `KEY (...)`를 채워야 한다고 생각하면 됩니다.

### DuckPGQ (DuckDB 커뮤니티 확장)

DuckDB는 `duckpgq` 확장으로 SQL:2023의 SQL/PGQ 문법을 구현합니다. 공개된 문법 정의가 절 구조를 그대로 보여 줍니다. ([DuckPGQ Property Graph](https://duckpgq.org/documentation/property_graph/), [DuckPGQ SQL/PGQ](https://duckpgq.org/documentation/sql_pgq/), [DuckDB Graph Queries 가이드](https://duckdb.org/docs/lts/guides/sql_features/graph_queries))

```
CREATE [ OR REPLACE ] PROPERTY GRAPH [ IF NOT EXISTS ] <name>
VERTEX TABLES ( <vertex_table> [, <vertex_table> ] )
[ EDGE TABLES ( <edge_table> [, <edge_table> ] ) ];

<vertex_table> ::= <table_name> [ AS <alias> ]
    [ PROPERTIES (<columns>)
    | PROPERTIES ARE ALL COLUMNS [ EXCEPT (<columns>) ]
    | NO PROPERTIES ]
    [ LABEL <label> ]

<edge_table> ::= <table_name>
    SOURCE KEY (<column>) REFERENCES <vertex_table> (<column>)
    DESTINATION KEY (<column>) REFERENCES <vertex_table> (<column>)
    [ LABEL <label> ] [ PROPERTIES (...) ]
```

실제 예:

```sql
CREATE PROPERTY GRAPH snb
VERTEX TABLES ( Person )
EDGE TABLES (
  Person_knows_person
    SOURCE KEY ( person1id ) REFERENCES Person ( id )
    DESTINATION KEY ( person2id ) REFERENCES Person ( id )
    LABEL Knows
);

FROM GRAPH_TABLE(snb
  MATCH (a:Person WHERE a.firstName = 'Jan')-[k:Knows]->(b:Person)
  COLUMNS (b.firstName)
);
```

- `VERTEX TABLES`는 **최소 하나** 있어야 유효한 프로퍼티 그래프가 됩니다. `EDGE TABLES`는 생략 가능(문법상 대괄호).
- 노드/엣지 테이블은 **기본키–외래키 관계**를 전제로 나뉩니다. 즉 이미 정규화된 관계형 스키마가 있으면 대체로 그대로 얹을 수 있습니다.
- 라벨 표기가 `IS Company`(표준·Oracle) 대신 `:Person`(Cypher 풍)으로도 받아들여집니다 — **표준이 있어도 방언은 남습니다**(11장 ex3의 주제와 같은 이야기).
- DuckPGQ의 프로퍼티 그래프는 초기엔 커넥션 수명 동안만 살아 있는 transient였고, `v0.1.0`(DuckDB `v1.1.3`)부터 영속화됩니다. 어느 쪽이든 **원본 테이블 위의 정의**일 뿐입니다.

### PostgreSQL

코어에는 없지만 SQL/PGQ를 붙이려는 작업이 진행되어 왔습니다. ([CYBERTEC](https://www.cybertec-postgresql.com/en/handling-graphs-with-sql-pgq-in-postgresql/), [EDB](https://www.enterprisedb.com/blog/representing-graphs-postgresql-sqlpgq))

## 외우는 방법

절 이름을 문장으로 이어 읽으면 그대로 문법이 됩니다.

> **그래프를 만든다**(`CREATE PROPERTY GRAPH biz`).
> **노드는 이 테이블들**이고(`VERTEX TABLES`), 각자 **신원은 이 컬럼**(`KEY`), **이름은 이거**(`LABEL`), **속성은 이 컬럼들**(`PROPERTIES`).
> **엣지는 이 테이블들**이고(`EDGE TABLES`), **여기서 출발해서**(`SOURCE KEY ... REFERENCES ...`) **저기로 간다**(`DESTINATION KEY ... REFERENCES ...`).

헷갈리기 쉬운 지점 세 개:

1. `SOURCE`/`DESTINATION`은 **엣지 테이블에만** 붙습니다. 노드 테이블에는 나올 수 없습니다.
2. `REFERENCES` 뒤는 **노드 테이블과 그 키 컬럼**입니다. 엣지 테이블을 가리키지 않습니다.
3. `KEY (...)`는 노드 테이블에서는 「노드의 신원」이고, 엣지 테이블에서는 「엣지의 신원」입니다. `SOURCE KEY`/`DESTINATION KEY`와는 다른 역할입니다.

## 관련 카드로 이어지는 자리

- **3장** — 재귀 CTE와 조인 폭발. SQL/PGQ가 문법으로 없애 주는 것과 못 없애는 것의 경계.
- **9장** — 「상한을 걸어라」. SQL/PGQ의 가변 길이 경로 표기에도 같은 규율이 필요합니다.
- **11장 ex3** — GQL 표준 절(`LET`, `NEXT`, `FILTER`)이 실제 엔진에서 실패하는 걸 세어 보는 예제. SQL/PGQ에도 같은 「표준과 구현의 시차」가 있습니다.

## 출처

- [ISO/IEC 9075-16:2023 — Database languages SQL — Part 16: Property Graph Queries (SQL/PGQ)](https://www.iso.org/standard/79473.html)
- [ISO/IEC 9075-16:2023/Cor 1:2026 — Technical Corrigendum 1](https://www.iso.org/standard/93698.html)
- [Oracle — CREATE PROPERTY GRAPH (SQL Language Reference)](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-property-graph.html)
- [ORACLE-BASE — SQL Property Graphs and SQL/PGQ in Oracle Database 23ai/26ai](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23)
- [Oracle Blogs — Property Graphs in Oracle Database 23ai: The SQL/PGQ Standard](https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard)
- [Oracle Blogs — Announcing the General Availability of the SQL:2023 Standard](https://blogs.oracle.com/sql/general-availability-of-the-sql2023-standard)
- [DuckPGQ — Property Graph](https://duckpgq.org/documentation/property_graph/)
- [DuckPGQ — SQL/PGQ](https://duckpgq.org/documentation/sql_pgq/)
- [DuckDB — Graph Queries 가이드](https://duckdb.org/docs/lts/guides/sql_features/graph_queries)
- [CYBERTEC — Handling graphs with SQL/PGQ in PostgreSQL](https://www.cybertec-postgresql.com/en/handling-graphs-with-sql-pgq-in-postgresql/)
- [EDB — Representing graphs in PostgreSQL with SQL/PGQ](https://www.enterprisedb.com/blog/representing-graphs-postgresql-sqlpgq)
