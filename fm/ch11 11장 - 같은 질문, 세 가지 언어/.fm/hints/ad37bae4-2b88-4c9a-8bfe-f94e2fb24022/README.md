# SQL/PGQ의 실무 채택 상황 (2026년 8월 기준)

> **Q.** 2026년 8월 기준 SQL/PGQ의 실무 채택 상황은 어떤가?
>
> **A.** 저자는 프로덕션에서 이 문법을 쓰는 팀을 보지 못했다. 구현이 덜 퍼져서 예제는 '앞으로 이렇게 될 가능성'을 보여 준다.

조사 시점: **2026년 8월**. 아래 표와 판단은 이 시점의 문서·커밋·릴리스 노트를 확인한 결과다. 그래프 진영은 6개월 단위로 상황이 바뀌므로 **확인 시점을 반드시 같이 읽어야 한다**.

---

## 1. SQL/PGQ가 무엇이고 왜 매력적인가

SQL/PGQ는 **ISO/IEC 9075-16:2023**, 즉 SQL:2023 표준의 16번째 파트다. 핵심 아이디어는 하나다.

> **테이블을 옮기지 않는다. 그래프로 보는 시각만 얹는다.**

11장 `ex4_sql_pgq.py`의 문법이 그 그림 그대로다.

```sql
-- 1) 기존 테이블 위에 '그래프 뷰'를 선언한다 (데이터 복사 없음)
CREATE PROPERTY GRAPH biz
  VERTEX TABLES (
    company  KEY (name) LABEL Company  PROPERTIES (name, grade),
    contract KEY (id)   LABEL Contract PROPERTIES (id, started_on, ended_on)
  )
  EDGE TABLES (
    signed     SOURCE KEY (company_name) REFERENCES company (name)
               DESTINATION KEY (contract_id) REFERENCES contract (id)
               LABEL Signed,
    terminated SOURCE KEY (company_name) REFERENCES company (name)
               DESTINATION KEY (contract_id) REFERENCES contract (id)
               LABEL Terminated
  );

-- 2) GRAPH_TABLE 안에서 Cypher처럼 패턴을 쓴다
SELECT * FROM GRAPH_TABLE (biz
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
        (c)-[IS Signed]->(n IS Contract)
  WHERE o.ended_on < n.started_on
  COLUMNS (c.name AS 고객)
);
```

3장에서 본 「두 벌 운영」(RDB + 그래프 DB를 나란히 두고 동기화하는 비용)을 안 내도 된다는 게 SQL/PGQ의 값어치다. **그래서 매력적이다.** 문제는 매력이 아니라 구현이다.

---

## 2. 엔진별 SQL/PGQ 구현 현황 (2026-08 확인)

| 엔진 / 제품 | 문법 계열 | 상태 (2026-08) | 프로덕션 의존 가능? | 확인한 근거 |
|---|---|---|---|---|
| **Oracle AI Database 26ai** (이전 23ai) | SQL/PGQ (`CREATE PROPERTY GRAPH` + `GRAPH_TABLE`) | 가장 성숙. 23ai에서 최초 상용 지원, 26ai에서 확장(JSON 컬렉션을 그래프 소스로 사용 가능). 그래프는 메타데이터로만 저장되고 데이터는 materialize되지 않음 — 표준의 의도 그대로 | **가능** (단 Oracle 라이선스에 종속) | [Oracle 26ai 릴리스 노트](https://docs.oracle.com/en/database/oracle/oracle-database/26/rnrdm/property-graph-restrictions.html), [Oracle 블로그: 23ai의 SQL/PGQ](https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard), [ORACLE-BASE 정리](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23) |
| **PostgreSQL 19** | SQL/PGQ | 2026-03-16 Peter Eisentraut가 master에 커밋(약 118파일 / +14,800줄). `GRAPH_TABLE`, `CREATE/ALTER/DROP PROPERTY GRAPH`, `\dG`, `pg_get_propgraphdef()` 포함. **가변 길이 경로 `{*}`(quantified path pattern) 미구현**, 최단 경로·사이클 검출 등 그래프 알고리즘 없음. 내부적으로는 관계형 질의로 rewrite (뷰에 가까움) | **아직 아님** — 19가 정식 릴리스되기 전이고, 이 장에서 제일 중요한 가변 길이 경로가 빠져 있다 | [PG 커밋 메시지](https://www.postgresql.org/message-id/E1w247I-0000Tk-2Y@gemulon.postgresql.org), [depesz: Waiting for PostgreSQL 19 – SQL/PGQ](https://www.depesz.com/2026/07/31/waiting-for-postgresql-19-sql-property-graph-queries-sql-pgq/), [Postgres Weekly 해설](https://pgweekly.github.io/en/2026/07/sql-property-graph-queries-pgq.html) |
| **DuckDB + DuckPGQ 확장** | SQL/PGQ | CWI 연구 프로젝트. 패턴 매칭 + 병렬 경로 탐색 구현. **커뮤니티 확장**이며 최신 DuckDB 1.5.x에는 아직 안 올라옴 — 쓰려면 DuckDB **v1.4.4**로 내려가야 한다. 공식 문서에 "ongoing research project ... some features may still be under development" 경고 | **아님** (연구용/PoC용) | [duckpgq 커뮤니티 확장 페이지](https://duckdb.org/community_extensions/extensions/duckpgq), [DuckPGQ 공식 문서](https://duckpgq.org/documentation/sql_pgq/), [DuckDB Graph Queries 가이드](https://duckdb.org/docs/current/guides/sql_features/graph_queries), [VLDB 논문](https://www.vldb.org/pvldb/vol16/p4034-wolde.pdf) |
| **Google BigQuery Graph** | GQL 우선 + SQL/PGQ 호환 | 기존 BigQuery 데이터를 그래프 스키마로 매핑해 **데이터 이동 없이** SQL 또는 GQL로 질의. ISO GQL 표준과 ISO SQL/PGQ 표준 양쪽 호환을 문서에 명시 | **부분적으로 가능** — 단 문법의 중심은 GQL이다 | [BigQuery Graph 소개](https://docs.cloud.google.com/bigquery/docs/graph-overview), [Google 블로그: 통합 그래프 솔루션](https://cloud.google.com/blog/products/data-analytics/the-unified-graph-solution-with-spanner-graph-and-bigquery-graph) |
| **Google Spanner Graph** | **GQL 진영** (ISO/IEC 39075:2024) | ISO GQL 지원. SQL 안에 GQL을 섞어 쓰는 형태(`GRAPH ... MATCH ...`). BigQuery Graph와 스키마·질의 언어를 공유 | **가능** — 단 이건 SQL/PGQ가 아니라 GQL이다 | [Spanner GQL 개요](https://docs.cloud.google.com/spanner/docs/reference/standard-sql/graph-intro), [GQL within SQL](https://docs.cloud.google.com/spanner/docs/reference/standard-sql/graph-sql-queries), [Spanner Graph와 ISO 표준](https://docs.cloud.google.com/spanner/docs/graph/iso-standards) |
| **SQL Server / Azure SQL** | **독자 문법 (표준 아님)** | `CREATE TABLE ... AS NODE` / `AS EDGE`, `WHERE MATCH(A-(E)->B)`. `$node_id`, `$from_id`, `$to_id` 자동 컬럼. SQL/PGQ의 `GRAPH_TABLE`도 `CREATE PROPERTY GRAPH`도 **아니다**. 2017부터 있었지만 표준 쪽으로 수렴할 계획이 공개된 바 없음 | 기능 자체는 성숙하나 **이식성이 0** | [SQL Graph 개요](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-overview?view=sql-server-ver17), [MATCH (SQL Graph)](https://learn.microsoft.com/en-us/sql/t-sql/queries/match-sql-graph?view=sql-server-ver17) |
| **Neo4j / Kuzu / Memgraph 등 Cypher 계열** | Cypher(사실상 표준), GQL로 점진 수렴 | SQL/PGQ와는 무관한 축. 11장 `ex3`이 보여 주듯 **GQL 전용 절(`LET`, `NEXT`, `FILTER`)조차 아직 안 받는다** | 해당 없음 | [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/), 11장 `ex3_gql_dialects.py` 실행 결과 |

### 학술 서베이의 요약

2025~2026년의 그래프 DB 서베이 논문들도 같은 결론이다. **"SQL/PGQ에 완전히 부합하는(fully compliant) 시스템은 많지 않다"**. Oracle 23ai가 최초의 상용 지원이고, PostgreSQL·DuckDB·Spanner Graph는 **부분 커버리지**다.

- [Survey: On the Landscape of Graph Databases (arXiv 2505.24758)](https://arxiv.org/pdf/2505.24758)
- [Towards Cross-Model Efficiency in SQL/PGQ (arXiv 2505.07595)](https://arxiv.org/pdf/2505.07595)
- [Algorithm Support for Graph Databases, Done Right (arXiv 2601.06705)](https://arxiv.org/pdf/2601.06705)

---

## 3. 그래서 이 상태를 뭐라고 부르는가: 「표준은 있는데 구현이 없다」

정리하면 세 층이 서로 어긋나 있다.

```
표준 존재       ████████████████████  ISO/IEC 9075-16:2023 (3년 전에 확정)
구현 존재       ████████░░░░░░░░░░░░  Oracle 1곳 성숙 + PG19/DuckPGQ 부분
프로덕션 채택   █░░░░░░░░░░░░░░░░░░░  저자가 실물을 못 봄
```

카드의 답이 말하는 건 정확히 셋째 줄이다. **"구현이 없다"가 아니라 "구현이 덜 퍼졌다"**, 그리고 그 결과 **프로덕션 사례가 안 보인다**.

왜 이런 간격이 생기나. 11장 `ex3`의 결론이 그 답이다.

> SQL도 같은 길을 걸었다. SQL-92가 나오고도 방언이 10년 넘게 남았다.

표준 제정 → 구현 → 배포 → 팀이 프로덕션에 올림. 이 파이프라인의 각 칸이 몇 년씩 걸린다. SQL/PGQ는 지금 2~3번째 칸에 있다. GQL(ISO/IEC 39075:2024)은 그보다 한 칸 더 뒤다.

---

## 4. 실무 선택에 주는 함의

### 하지 말 것

- **SQL/PGQ 문법에 프로덕션 코드를 의존시키지 말 것.** Oracle을 이미 쓰고 있고 앞으로도 Oracle에 남을 확신이 있는 경우가 유일한 예외다. 그 외에는 "지금 이 문법으로 작성하면 나중에 다른 엔진으로 그대로 옮겨진다"는 기대가 성립하지 않는다.
- **PostgreSQL 19의 SQL/PGQ를 기다리며 아키텍처를 미루지 말 것.** 커밋은 됐지만 이 장에서 제일 중요한 **가변 길이 경로(`{*}`)가 없다**. 즉 11장 `ex2`가 비교한 `-[:ParentOf*1..3]->` 같은 질의를 PG19의 SQL/PGQ로는 아직 쓸 수 없다. 그러면 결국 3장의 재귀 CTE 스무 줄로 되돌아온다.
- **DuckPGQ를 프로덕션 경로에 놓지 말 것.** 최신 DuckDB에서 안 돌아서 버전을 내려야 하는 확장은 그 자체로 운영 부채다. 분석·PoC·벤치마크용으로는 훌륭하다.
- **"SQL/PGQ가 표준이니까 그래프 DB는 필요 없다"고 결론 내리지 말 것.** 그리고 반대 방향의 착각도 조심할 것 — SQL/PGQ는 **저장 위치**를 바꾸지 않으므로 **조인 폭발도 그대로 남는다**(3장). 문제는 데이터가 어디 있느냐가 아니라 「따라가는 값」이었다.

### 지금 할 것: 이식 대비만

11장 `ex3`의 마지막 세 줄이 그대로 실무 지침이다.

1. **질의문을 한곳에 모은다.** 코드 전체에 Cypher 문자열을 흩뿌려 놓으면 나중에 GQL/PGQ로 옮길 때 grep으로 찾아야 한다. 질의 모듈 하나에 모아 두면 파일 하나만 다시 쓴다.
2. **`ORDER BY`를 강제한다.** 엔진을 바꿨을 때 결과 순서가 달라지면 회귀 테스트가 전부 깨진다. 순서를 명시해 두면 엔진 교체가 "같은 결과가 나오는지"만 확인하는 작업이 된다.
3. **엔진 고유 함수는 별도 파일로 격리한다.** 표준에 없는 함수(Kuzu 고유, Neo4j APOC 등)를 한 파일에 몰아 두면 이식 시 교체 범위가 그 파일로 한정된다.
4. **각 질의가 답하는 질문을 주석으로 남긴다.** 다른 언어로 다시 쓸 때 필요한 건 원본 문법이 아니라 **의도**다. `ex1`이 같은 질문을 세 언어로 쓸 수 있었던 이유도 「해지했다가 그 뒤에 다시 계약한 고객은?」이라는 문장이 먼저 있었기 때문이다.

### 판단 기준 요약

| 상황 | 2026-08 기준 권고 |
|---|---|
| Oracle 26ai를 이미 운영 중 | SQL/PGQ 실제 사용 검토 가능. 유일하게 성숙한 선택지 |
| PostgreSQL 중심 | 지금은 재귀 CTE 또는 별도 그래프 엔진. PG19는 관찰 대상 |
| Google Cloud 중심 | Spanner Graph / BigQuery Graph의 **GQL**을 보는 게 맞다 (SQL/PGQ가 아니다) |
| SQL Server 중심 | 독자 문법을 쓰되 **이식 불가**임을 문서화해 둘 것 |
| 그래프 워크로드가 본업 | Cypher 계열 전용 엔진. 단 GQL 수렴을 전제로 위 4가지 대비 |

---

## 5. 한 줄 정리

**표준이 나왔다 ≠ 표준대로 돌아간다.** SQL/PGQ는 2023년에 확정됐고 2026년 8월에도 상용 성숙 구현은 Oracle 하나다. 그래서 11장의 `ex4`는 「돌아가는 코드」가 아니라 **「앞으로 이렇게 될 가능성」**의 스케치이고, 그 예제 안에서 실제로 실행되는 건 같은 뜻의 평범한 SQL이다. 지금 우리가 할 수 있는 건 프로덕션 의존이 아니라 **이식 대비**다.

---

## 확인한 출처

**표준 원문**
- [ISO/IEC 9075-16:2023 (SQL/PGQ)](https://www.iso.org/standard/79473.html)
- [ISO/IEC 39075:2024 (GQL)](https://www.iso.org/standard/76120.html)

**Oracle**
- [Property Graph Features That Work With Oracle AI Database 26ai](https://docs.oracle.com/en/database/oracle/oracle-database/26/rnrdm/property-graph-restrictions.html)
- [Property Graphs in Oracle Database 23ai: The SQL/PGQ Standard (Oracle 블로그)](https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard)
- [SQL Property Graphs and SQL/PGQ in Oracle Database 23ai/26ai (ORACLE-BASE)](https://oracle-base.com/articles/23/sql-property-graphs-and-sql-pgq-23)

**PostgreSQL**
- [pgsql commit: SQL Property Graph Queries (SQL/PGQ)](https://www.postgresql.org/message-id/E1w247I-0000Tk-2Y@gemulon.postgresql.org)
- [Waiting for PostgreSQL 19 – SQL Property Graph Queries (depesz, 2026-07-31)](https://www.depesz.com/2026/07/31/waiting-for-postgresql-19-sql-property-graph-queries-sql-pgq/)
- [SQL Property Graph Queries (SQL/PGQ): Bringing Graph Queries to PostgreSQL (Postgres Weekly, 2026-07)](https://pgweekly.github.io/en/2026/07/sql-property-graph-queries-pgq.html)

**DuckDB / DuckPGQ**
- [duckpgq – DuckDB Community Extensions](https://duckdb.org/community_extensions/extensions/duckpgq)
- [Graph Queries – DuckDB 공식 가이드](https://duckdb.org/docs/current/guides/sql_features/graph_queries)
- [DuckPGQ 프로젝트 문서 — SQL/PGQ](https://duckpgq.org/documentation/sql_pgq/)
- [cwida/duckpgq-extension (GitHub)](https://github.com/cwida/duckpgq-extension)
- [DuckPGQ: Bringing SQL/PGQ to DuckDB (VLDB)](https://www.vldb.org/pvldb/vol16/p4034-wolde.pdf)
- [The State of DuckPGQ (LDBC TUC 17th)](https://ldbcouncil.org/docs/tuc17th/duckpgq.pdf)

**Google Cloud (GQL 진영)**
- [Introduction to BigQuery Graph](https://docs.cloud.google.com/bigquery/docs/graph-overview)
- [The unified graph solution with Spanner Graph and BigQuery Graph](https://cloud.google.com/blog/products/data-analytics/the-unified-graph-solution-with-spanner-graph-and-bigquery-graph)
- [Spanner GQL overview](https://docs.cloud.google.com/spanner/docs/reference/standard-sql/graph-intro)
- [GQL within SQL (Spanner)](https://docs.cloud.google.com/spanner/docs/reference/standard-sql/graph-sql-queries)
- [Spanner Graph and ISO standards](https://docs.cloud.google.com/spanner/docs/graph/iso-standards)

**SQL Server (독자 문법)**
- [Graph Processing – SQL Server and Azure SQL Database](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-overview?view=sql-server-ver17)
- [MATCH (SQL Graph)](https://learn.microsoft.com/en-us/sql/t-sql/queries/match-sql-graph?view=sql-server-ver17)

**서베이 / 연구**
- [Survey: On the Landscape of Graph Databases (arXiv 2505.24758)](https://arxiv.org/pdf/2505.24758)
- [Towards Cross-Model Efficiency in SQL/PGQ (arXiv 2505.07595)](https://arxiv.org/pdf/2505.07595)
- [Algorithm Support for Graph Databases, Done Right (arXiv 2601.06705)](https://arxiv.org/pdf/2601.06705)
- [GQL Standards](https://www.gqlstandards.org/)
