# ISO GQL과 SQL/PGQ — 단계 3(명세 초안)과 지켜볼 신호

## 질문과 답

**질문**: ISO GQL과 SQL/PGQ는 어느 단계이며 무엇을 지켜봐야 하는가?

**답**: 명세 초안 단계(3)다. GQL은 엔진들이 실제로 구현하는지, SQL/PGQ는 DuckDB와 상용 DB의 지원 범위를 봐야 한다.

---

## 1. 이 답이 나온 곳 — 35장 「표준은 어디까지 왔나」

35장의 `ex2_standard_watch.py`는 이 책이 붙인 상태 라벨([표준] / [업계 표준] / [실험])을
**성숙도 단계**로 다시 재는 표입니다. 단계는 다섯 칸입니다.

| 단계 | 이름 | 뜻 |
|---|---|---|
| 0 | 아이디어 | 논문·블로그에만 있음 |
| 1 | 구현이 여럿 | 각자 만들어 쓰는데 서로 안 맞음 |
| 2 | 명세 초안 | 문서가 나왔지만 아직 흔들림 |
| 3 | 공식 명세 | 표준 기구가 확정한 문서가 있음 |
| 4 | 널리 채택 | 문서도 있고 구현도 널려 있음 |

> **주의**: 예제 코드의 `STAGES` 리스트는 0부터 세고,
> 카드의 「단계(3)」는 `ITEMS` 배열에 적힌 정수 `3`을 그대로 말합니다.
> 즉 `STAGES[3]`이므로 리스트 표기상 네 번째 칸입니다.
> 카드 답의 "명세 초안 단계(3)"는 **표에 적힌 숫자 3**을 가리키는 것으로 읽으면 됩니다.
> 요점은 라벨이 아니라 **「문서는 확정됐는데 구현이 아직 안 따라왔다」**는 상태입니다.

해당 두 줄:

```python
("ISO GQL",                    3, "표준",
 "엔진들이 실제로 구현하는지"),
("SQL/PGQ",                    3, "표준",
 "DuckDB · 상용 DB 의 지원 범위"),
```

같은 [표준] 라벨을 붙였지만 RDF·OWL·SHACL이나 SPARQL 1.1은 단계 4(널리 채택)인데,
GQL과 SQL/PGQ만 단계 3입니다. **차이는 「구현이 얼마나 깔렸나」 한 가지**입니다.

---

## 2. ISO GQL이란 무엇인가

### 2.1 정체

- 정식 번호: **ISO/IEC 39075:2024** — *Information technology — Database languages — GQL*
- 제정: **2024년 4월**
- 담당: ISO/IEC JTC1 SC32 WG3 (SQL을 만든 바로 그 위원회)
- 의미: **ISO가 1987년 SQL 이후 처음으로 새로 만든 데이터베이스 질의 언어 표준**입니다.
  37년 만에 두 번째 언어가 나온 것이므로, 이 자체가 사건입니다.

GQL은 **속성 그래프(property graph)** 를 일급 시민으로 다룹니다.
노드와 엣지에 라벨과 속성이 붙는 모델이고, 저장·질의·수정(DDL/DML/DQL)을 모두 정의합니다.
SPARQL이 RDF(트리플)를 다루는 것과 대비되는, "트랙 1의 다른 쪽 절반"입니다.

### 2.2 Cypher / openCypher와의 관계

이 부분이 실무에서 가장 자주 헷갈립니다. 계보로 보면 이렇습니다.

```
Cypher (2011, Neo4j 사유 언어)
   │
   ├─ openCypher (2015, Neo4j가 명세를 공개 — 「사실상 표준」)
   │     └─ Memgraph, RedisGraph/FalkorDB, AWS Neptune,
   │        Apache AGE, Kuzu 등이 각자 방언으로 구현
   │
   └─ GQL (2024, ISO/IEC 39075 — 「공식 표준」)
         Cypher를 주된 입력으로 삼되, PGQL(Oracle),
         GSQL(TigerGraph), G-CORE 등의 아이디어도 흡수
```

핵심 관계 세 가지:

1. **GQL은 Cypher의 후계가 아니라 Cypher를 "포함하려는" 표준**입니다.
   `MATCH ... RETURN` 같은 골격은 Cypher에서 왔지만, GQL에는 Cypher에 없던
   그래프 카탈로그·세션·트랜잭션·타입 시스템 규정이 추가됐습니다.
2. **openCypher 프로젝트는 스스로 "GQL로 가는 길"이 되겠다고 선언**했습니다.
   openCypher 명세에 GQL 기능을 점진적으로 흡수해서, 시간이 지나면
   openCypher 구현체가 자연히 GQL 준수에 가까워지게 하는 전략입니다.
3. **그래서 당장은 Cypher와 GQL이 공존**합니다. 기존 Cypher 코드를 버려야 하는 게 아니고,
   벤더들이 "GQL 준수 모드", 준수 범위 문서, 방언 사용을 짚어 주는 린터 같은 것을
   붙이는 방식으로 서서히 옮겨 갑니다.

이래서 35장 표에서 「Cypher 방언」은 단계 **1**(구현이 여럿)이고,
지켜볼 신호가 **"GQL로 수렴하는지, 갈라지는지"** 입니다.
GQL(단계 3)과 Cypher 방언(단계 1)이 한 표에 따로 올라간 이유가 여기 있습니다.

### 2.3 2026년 8월 시점 구현 상황

- **Neo4j**: Cypher를 "GQL 준수(GQL conformant) 질의 언어"로 표현하고,
  매뉴얼에 GQL 준수 항목별 표를 따로 유지합니다. 다만 "준수"의 범위는 항목별로 갈립니다.
- **Microsoft Fabric**: graph 기능에서 GQL을 ISO/IEC 39075 기준으로 지원한다고 문서화했습니다.
- **TigerGraph**: 고유 언어 GSQL을 유지하면서 openCypher와 GQL 패턴 매칭을 함께 지원하는 방향.
- **SAP HANA, Memgraph** 등도 GQL 준수 작업을 진행 중입니다.
- 업계 관측으로는 대부분의 속성 그래프 DB가 **2026년 말까지 GQL 1.0을 지원**하는 흐름입니다.

즉 명세는 2년 넘게 확정되어 있는데, **"어느 엔진이 GQL의 어디까지를 진짜로 구현했나"** 는
여전히 벤더 문서를 하나하나 열어 봐야 아는 상태입니다. 그게 단계 3의 정확한 모습입니다.

---

## 3. SQL/PGQ란 무엇인가

### 3.1 정체

- 정식 번호: **ISO/IEC 9075-16:2023** — SQL 표준의 **Part 16**,
  *SQL — Part 16: Property Graph Queries*
- 제정: **2023년 6월 (SQL:2023의 일부)**
- 한 줄 요약: **기존 SQL 엔진 안에서, 기존 관계형 테이블 위에 그래프 질의를 얹는 방법**입니다.

GQL이 "그래프 DB를 위한 새 언어"라면, SQL/PGQ는 "SQL DB가 그래프처럼 보이게 하는 문법"입니다.
목적이 다르므로 둘은 경쟁이라기보다 **역할 분담**입니다.
(같은 위원회가 만들었기 때문에 패턴 매칭 문법은 의도적으로 겹칩니다.)

### 3.2 기존 SQL 엔진 안에서 그래프 질의를 어떻게 다루나

핵심 장치가 두 개입니다.

**(1) `CREATE PROPERTY GRAPH` — 메타데이터만 만드는 뷰**

기존 테이블 중 무엇이 노드고 무엇이 엣지인지 선언합니다.
**데이터를 복제하거나 새 저장 엔진을 쓰지 않습니다.** 그래프는 순수하게 메타데이터,
즉 관계형 테이블 위에 씌운 "그래프 모양의 뷰"입니다.

```sql
CREATE PROPERTY GRAPH social_graph
  VERTEX TABLES (
    persons KEY (id) LABEL person PROPERTIES (id, name)
  )
  EDGE TABLES (
    friendships KEY (id)
      SOURCE KEY (src_id) REFERENCES persons (id)
      DESTINATION KEY (dst_id) REFERENCES persons (id)
      LABEL knows
  );
```

**(2) `GRAPH_TABLE(...)` — FROM 절에서 쓰는 테이블 함수**

그래프 패턴을 매칭해서 그 결과를 **다시 평범한 행 집합(relation)** 으로 돌려줍니다.
그래서 그 뒤에 일반 SQL의 JOIN, GROUP BY, 윈도 함수를 그대로 이어 붙일 수 있습니다.

```sql
SELECT *
FROM GRAPH_TABLE (social_graph
       MATCH (a IS person)-[e IS knows]->(b IS person)
       WHERE a.name = 'Alice'
       COLUMNS (a.name AS from_name, b.name AS to_name)
     ) AS t;
```

이 설계의 의미가 큽니다.
데이터를 그래프 DB로 **옮기지 않고도** 그래프 질의를 쓸 수 있고,
그래프 질의 결과가 SQL의 세계로 되돌아오니 기존 BI·리포팅 도구와도 그대로 붙습니다.
27장의 「그래프 전환점」(사실 몇 개부터 그래프가 싼가) 계산이
SQL/PGQ 때문에 흔들릴 수 있다는 게 바로 이 지점입니다.

### 3.3 2026년 8월 시점 구현 상황

| 구현 | 상태 | 메모 |
|---|---|---|
| **Oracle Database 23ai / 26ai** | 상용 최초 | SQL 프로퍼티 그래프 + `GRAPH_TABLE`. Oracle이 표준화를 주도했고 첫 상용 구현을 냈습니다. Autonomous Database에도 제공됩니다. |
| **DuckDB (DuckPGQ 확장)** | 커뮤니티 확장 | `INSTALL duckpgq FROM community; LOAD duckpgq;`. CIDR 2023 / VLDB 논문에서 시작한 연구 프로토타입이 커뮤니티 확장으로 승격. 경계 있는/없는 경로 탐색, 도달 가능성, 최단·최소비용 경로 지원. **아직 활발한 개발 중이라 일부 기능이 미완**입니다. |
| **PostgreSQL 19** | 코어에 진입 | 2026년 3월 16일 Peter Eisentraut가 SQL/PGQ 패치를 커밋(공저 Ashutosh Bapat, 약 118파일·14,800줄). 2026년 6월 4일 **Beta 1**에 포함. `GRAPH_TABLE`, `CREATE/ALTER/DROP PROPERTY GRAPH`, 새 시스템 카탈로그, psql `\dG`, `pg_get_propgraphdef()`. **새 저장 엔진이나 확장 없이** 기존 테이블 위의 뷰로 동작. 정식 릴리스는 2026년 말 예정. |
| 그 밖의 상용 DB | 미지원 또는 미공개 | SQL Server·MySQL 등은 SQL/PGQ 지원 발표가 없습니다. |

한 문장으로: **표준은 2023년에 확정, 상용 첫 구현은 Oracle, 오픈소스는 DuckDB가 확장으로,
Postgres가 방금 코어에 들어왔지만 아직 GA가 아님.** 정확히 "명세는 있는데 구현이 아직"입니다.

---

## 4. 왜 "명세는 있는데 구현이 아직"이 단계 3인가

35장의 단계 척도는 **문서와 구현을 따로 셉니다.** 이게 이 표의 핵심 설계입니다.

| | 명세 문서 | 구현 배포 | 단계 |
|---|---|---|---|
| RDF·OWL·SHACL | 확정 (W3C) | 도구가 널림 | 4 |
| SPARQL 1.1 | 확정 (W3C) | 엔진마다 지원 | 4 |
| **ISO GQL** | **확정 (2024)** | **벤더별로 부분 구현, 진행 중** | **3** |
| **SQL/PGQ** | **확정 (2023)** | **Oracle·DuckDB·PG19 beta 정도** | **3** |
| Cypher 방언 | 없음(사실상 표준) | 구현은 여럿 | 1 |
| MCP | 초안이 자주 바뀜 | 구현 많음 | 2 |

단계 4로 못 올라가는 이유가 명확합니다.

1. **이식성이 아직 없습니다.** 표준의 목적은 "A 엔진에서 쓴 질의가 B 엔진에서도 돌아가는 것"인데,
   지금 GQL 질의를 Neo4j에서 Fabric으로, SQL/PGQ 질의를 Oracle에서 DuckDB로
   그대로 옮기면 대체로 안 돌아갑니다. 표준 문서가 있다는 것과
   표준이 **작동한다**는 것은 다릅니다.
2. **"준수"의 범위가 벤더 정의입니다.** GQL은 준수 수준이 항목별로 갈리는 구조라,
   "GQL 지원"이라는 마케팅 문구만 보고 판단하면 안 됩니다.
3. **핵심 구현이 아직 GA가 아닙니다.** DuckPGQ는 커뮤니티 확장이고 미완 기능이 있으며,
   PostgreSQL의 SQL/PGQ는 2026년 8월 현재 beta입니다.
4. **그래서 도입 결정에 대칭적으로 위험합니다.**
   "표준이니까 안전하다"고 도입하면 특정 벤더에 묶이고,
   "아직 구현이 없다"고 미루면 3년 뒤에 뒤처집니다.

이래서 35장은 단계와 함께 **「지켜볼 신호」** 를 반드시 적습니다.
반증 조건 없는 문장은 주장이 아니라 의견이라는 게 이 장 전체의 논지고,
표준 성숙도 판단에도 같은 규칙을 적용한 것입니다.
"나중에 널리 쓰일 수도 있다"는 의견이지만,
"엔진 셋 이상이 GQL 준수 표를 공개하면 단계 4로 올린다"는 검증 가능한 주장입니다.

---

## 5. 지켜볼 신호 — 구체적으로 무엇을 확인하나

### 5.1 ISO GQL: "엔진들이 실제로 구현하는지"

확인할 것을 순서대로:

1. **벤더의 GQL 준수 문서 자체가 존재하는가.**
   Neo4j Cypher 매뉴얼의 `appendix/gql-conformance` 페이지처럼,
   항목별 준수 여부를 표로 공개하는지 봅니다.
   준수 표가 **없이** "GQL 지원"만 말하는 벤더는 아직 단계 1로 보는 게 안전합니다.
2. **릴리스 노트에 GQL 관련 항목이 몇 분기 연속 등장하는가.**
   한 번 발표하고 조용해지면 마케팅, 분기마다 조금씩 늘면 진짜 구현입니다.
3. **"GQL 모드" 같은 스위치가 생기는가.**
   방언과 표준을 나눠 실행하는 옵션이 붙는 것은 이식성을 실제로 신경 쓰기 시작한 신호입니다.
4. **엔진 두 개 이상에서 같은 GQL 질의가 돌아가는가.**
   이게 최종 판정 기준입니다. 표준의 가치는 이식성이고,
   이식이 확인되는 순간 단계 4입니다.
5. **openCypher 명세에 GQL 기능이 실제로 편입되는가.**
   openCypher가 GQL 쪽으로 수렴하면 Cypher 방언(단계 1) 문제도 같이 풀립니다.
   갈라지면 파편화가 굳어집니다.

**참고 링크**
- ISO/IEC 39075:2024 — https://www.iso.org/standard/76120.html
- GQL 표준 커뮤니티 — https://www.gqlstandards.org/
- Neo4j GQL 준수 표 — https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/
- openCypher — https://opencypher.org/

### 5.2 SQL/PGQ: "DuckDB · 상용 DB의 지원 범위"

1. **DuckPGQ 확장이 커뮤니티 확장에서 코어 쪽으로 올라가는가.**
   그리고 "일부 기능 미완" 문구가 릴리스마다 줄어드는가.
   DuckDB는 로컬에서 5분 만에 확인 가능하니 실측 비용이 거의 없습니다.
   ```sql
   INSTALL duckpgq FROM community;
   LOAD duckpgq;
   ```
2. **PostgreSQL 19이 SQL/PGQ를 안고 정식 GA로 나가는가.**
   이게 2026년의 가장 큰 변수입니다. Postgres 코어에 들어가면
   "그래프 질의를 위해 별도 DB를 도입한다"는 전제 자체가 흔들립니다.
   릴리스 노트와 `Documentation: 19: Property Graphs` 문서를 봅니다.
3. **상용 DB 릴리스 노트에서 `GRAPH_TABLE`을 검색.**
   Oracle은 이미 있습니다. SQL Server, MySQL, Snowflake, BigQuery 등에서
   이 키워드가 등장하기 시작하면 확산 국면입니다.
4. **지원 "범위"를 항목 단위로 봅니다.**
   `GRAPH_TABLE`만 되는지, 경계 없는 경로(`*`)와 최단 경로까지 되는지,
   DDL(`CREATE PROPERTY GRAPH`)이 있는지, 성능이 실용적인지는 전부 다른 얘기입니다.
   "SQL/PGQ 지원"이라는 한 줄로는 판단할 수 없습니다.

**참고 링크**
- DuckDB 그래프 질의 가이드 — https://duckdb.org/docs/lts/guides/sql_features/graph_queries
- DuckPGQ — https://duckpgq.org/documentation/sql_pgq/
- DuckDB 커뮤니티 확장 — https://duckdb.org/community_extensions/extensions/duckpgq
- PostgreSQL 19 Property Graphs — https://www.postgresql.org/docs/19/ddl-property-graphs.html
- Oracle 23ai SQL/PGQ — https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard

---

## 6. 이 카드가 35장의 큰 그림에서 갖는 위치

35장 표의 요점은 **"[표준]과 [실험] 사이가 비어 있다"** 는 것입니다.
[표준] 다섯은 전부 W3C·ISO의 트랙 1(지식 그래프) 것이고,
[실험] 넷은 전부 트랙 2(에이전트) 것이며 평균 단계가 0.5입니다.
두 트랙의 성숙도가 **20년쯤** 차이 납니다.
그래서 3부는 "이렇게 하면 된다"로 쓸 수 있었고,
4부는 "저는 이렇게 하는데 확신은 없습니다"로 쓸 수밖에 없었습니다.

GQL과 SQL/PGQ는 그 표에서 **트랙 1 안의 유일한 "움직이는" 항목**입니다.
RDF·SPARQL·PROV-O는 안정(단계 4)이라 앞으로 큰 변화가 없을 것이고,
GQL·SQL/PGQ만 3에서 4로 올라갈 여지가 남아 있습니다.
그리고 이 항목들은 확인 비용이 거의 없습니다.
링크 하나 열면 5분이고, 그 5분이 **"지금 이걸 도입해도 되나"** 의 답을 줍니다.

35장이 반복하는 태도가 그대로 적용됩니다.
"3년 뒤에 바뀔 수도 있다"가 아니라,
**"엔진 둘이 같은 질의를 돌리면 / Postgres가 GA를 내면 단계를 올린다"**
라고 적어 두는 것. 그게 반증 가능한 형태의 표준 관측입니다.

---

## 7. 한 줄 정리

| 항목 | 명세 | 단계 | 지켜볼 신호 | 2026-08 현재 |
|---|---|---|---|---|
| ISO GQL | ISO/IEC 39075:2024 | 3 | 엔진들이 실제로 구현하는지 | Neo4j·Fabric·TigerGraph 등 부분 구현, 준수 범위는 벤더별 |
| SQL/PGQ | ISO/IEC 9075-16:2023 (SQL:2023 Part 16) | 3 | DuckDB·상용 DB의 지원 범위 | Oracle 23ai 상용 최초, DuckPGQ 커뮤니티 확장, PostgreSQL 19 beta |
