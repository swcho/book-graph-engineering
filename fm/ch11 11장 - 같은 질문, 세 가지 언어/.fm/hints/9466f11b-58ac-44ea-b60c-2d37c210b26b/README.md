# SQL이 걸었던 표준화 경로는 GQL에 어떤 시사를 주는가?

> **답**: SQL-92가 나오고도 방언이 10년 넘게 남았다. 지금 어느 엔진을 쓰든 3년 뒤 GQL로 옮길 준비를 해 두는 게 낫다.

11장 예제 3(`ex3_gql_dialects.py`)이 말로가 아니라 결과로 보여 주는 게 이겁니다. Kuzu 0.11.3에 ISO GQL 표준 절(`LET`, `NEXT`, `FILTER`)을 그대로 넣으면 **실패**합니다. 반면 Cypher 방언(`WITH`, `-[:Knows*1..2]->`)은 잘 돕니다. 표준이 2024년에 나왔는데 2026년 엔진이 아직 안 받는다는 뜻입니다.

이게 처음 있는 일이 아니라는 게 이 카드의 핵심입니다. SQL이 똑같은 길을 먼저 걸었어요.

---

## 1. SQL 표준화 연표

| 연도 | 판 | 무엇이 들어갔나 |
|---|---|---|
| 1986 | **SQL-86** (ANSI X3.135) | ANSI가 SQL을 처음 표준화. DDL/DML/DCL 코어 |
| 1987 | ISO 채택 | ISO 국제 표준이 됨 (ISO 9075:1987) |
| 1989 | **SQL-89** | SQL-86의 상위집합. `PRIMARY KEY`, `FOREIGN KEY`, `DEFAULT`, `CHECK` 등 무결성 제약 |
| 1992 | **SQL-92** (SQL2) | 대규모 개정. `JOIN` 명시 문법, `CAST`, 스칼라 부질의, 문자열/날짜 함수 등. ANSI/ISO/IEC 9075:1992 |
| 1999 | **SQL:1999** (SQL3) | 재귀 질의(`WITH RECURSIVE`), 트리거, 정규식, 배열, 절차형 제어문 |
| 2003 / 2008 / 2011 / 2016 / 2023 | SQL:2003 … | 윈도 함수, `OFFSET … FETCH`, 시간 데이터, JSON, 그리고 **SQL/PGQ**(9075-16:2023) |

여기서 볼 대목은 **SQL-92가 준수 수준을 셋으로 쪼갰다**는 점입니다. Entry SQL / Intermediate SQL / Full SQL. 벤더가 "부분 준수"를 선언할 수 있게 만든 장치인데, 실제로 Full SQL-92를 달성한 상용 엔진은 사실상 없었습니다. NIST가 만든 검증 테스트 스위트 FIPS 127-2도 Entry Level 400여 개 테스트가 실질적인 기준선이었고, Oracle이 문서에서 자랑한 것도 "FIPS PUB 127-2 Entry SQL 완전 준수"였습니다. 표준이 처음부터 **부분 준수를 합법화한 구조**였다는 뜻입니다.

---

## 2. "표준 제정 ≠ 즉시 수렴": 구체적 사례

### 2-1. 조인 문법 — 1992년 표준, 2001년 구현 (9년)

SQL-92가 `LEFT OUTER JOIN` 같은 명시적 조인 문법을 정의했습니다. Oracle은 버전 6부터 자기만의 `(+)` 연산자를 쓰고 있었고, **ANSI SQL-92/99 조인 문법을 지원한 건 Oracle 9i(2001년)부터**입니다.

```sql
-- Oracle 고유 방언 (v6 ~ )
SELECT c.name, o.id FROM company c, contract o
 WHERE c.name = o.company_name(+);

-- SQL-92 표준 (Oracle 9i, 2001부터)
SELECT c.name, o.id FROM company c
  LEFT OUTER JOIN contract o ON c.name = o.company_name;
```

표준이 나온 지 9년. 그리고 그 9년 동안 쓰인 `(+)` 코드는 그 뒤로도 한참 레거시로 남았습니다. "10년 넘게 남았다"는 답의 근거가 바로 이 종류의 지연입니다.

### 2-2. 무결성 제약 `CHECK` — 1989년 표준, 2019년 구현 (30년)

`CHECK` 제약은 SQL-89에 들어간 기능입니다. MySQL은 오랫동안 `CHECK` 구문을 **파싱만 하고 무시**했습니다. 실제로 강제하기 시작한 건 **MySQL 8.0.16(2019년 4월)**부터입니다. 표준 문법을 문법 오류 없이 받아들이면서 의미는 다르게 동작하는 — 이식성 관점에서 가장 나쁜 형태의 방언이었습니다.

### 2-3. 페이징 — 지금도 방언이 살아 있음

| 엔진 | 문법 |
|---|---|
| MySQL / PostgreSQL / SQLite / MariaDB | `LIMIT n OFFSET m` |
| SQL Server (T-SQL) / Sybase ASE | `SELECT TOP (n) …` (오프셋 없음) |
| Oracle (전통) | `WHERE ROWNUM <= n` (`ORDER BY`보다 **먼저** 적용되는 함정) |
| 표준 (SQL:2008) | `ORDER BY … OFFSET n ROWS FETCH NEXT m ROWS ONLY` |

표준 `OFFSET … FETCH`는 SQL:2008에 들어갔고 SQL Server는 2012부터, Oracle은 12c(`FETCH FIRST n ROWS ONLY`)부터 받았습니다. 그런데 지금도 실무 코드베이스에서 가장 많이 보이는 건 여전히 `LIMIT`입니다. 표준이 이겼는데 관행이 안 바뀐 사례.

### 2-4. 문자열 결합 — 표준 연산자가 있는데도 셋으로 갈림

```sql
'가온' || '테크'        -- ANSI 표준. PostgreSQL, Oracle, SQLite, DB2
'가온' +  '테크'        -- SQL Server (T-SQL)
CONCAT('가온','테크')   -- MySQL (기본 설정에서 || 는 논리 OR)
```

`||`가 표준인데 T-SQL은 `+`를, MySQL은 `CONCAT()`을 씁니다. 게다가 MySQL에서 `||`는 기본 설정에서 논리 OR로 해석되니, 같은 문자열이 **에러도 없이 다른 뜻**이 됩니다.

### 2-5. 날짜 함수 — 표준 이름은 있지만 아무도 그것만 쓰지 않음

| 뜻 | 표준 | Oracle | SQL Server | MySQL | PostgreSQL |
|---|---|---|---|---|---|
| 현재 시각 | `CURRENT_TIMESTAMP` | `SYSDATE` | `GETDATE()` | `NOW()` | `now()` |
| 날짜 더하기 | `d + INTERVAL '1' MONTH` | `ADD_MONTHS(d,1)` | `DATEADD(month,1,d)` | `DATE_ADD(d, INTERVAL 1 MONTH)` | `d + interval '1 month'` |

`CURRENT_TIMESTAMP`는 SQL-92에 들어간 표준이지만, 실무 코드는 30여 년이 지난 지금도 엔진별 이름으로 가득합니다.

### 2-6. 식별자 인용 — 따옴표 하나로 이식이 깨짐

```sql
SELECT "고객" FROM "company";   -- ANSI 표준: 큰따옴표가 식별자
SELECT `고객` FROM `company`;   -- MySQL/MariaDB: 백틱 (표준 아님)
SELECT [고객] FROM [company];   -- SQL Server: 대괄호
```

MySQL은 기본 설정에서 큰따옴표를 **문자열 리터럴**로 봅니다(`ANSI_QUOTES` 모드를 켜야 표준 동작). 백틱은 ANSI 표준이 아니어서 PostgreSQL/SQL Server로 옮기면 전부 깨집니다.

### 2-7. 재귀 질의 — 1999년 표준, MySQL은 2017~2018년 (18~19년)

`WITH RECURSIVE`는 SQL:1999입니다. MySQL이 재귀 CTE를 지원한 건 8.0.1(2017년 4월, 이후 8.0 GA)부터. 11장 예제 2에서 "SQL은 재귀 CTE 스무 줄"이라고 한 그 문법조차, 표준화 후 18년간 세계에서 가장 많이 쓰이는 오픈소스 RDBMS에서는 아예 쓸 수 없었습니다.

---

## 3. 그래서 GQL에 주는 시사

GQL(**ISO/IEC 39075:2024**)은 2024년 4월에 발표됐고, **1987년 SQL 이후 ISO가 처음 내놓은 새 데이터베이스 질의 언어 표준**입니다. SQL과 같은 위원회(ISO/IEC JTC 1/SC 32 WG3)가 만들었고, 2019년부터 공식 작업이 진행됐습니다.

패턴을 그대로 겹쳐 보면 이렇게 읽힙니다.

| SQL이 겪은 일 | GQL에서 예상되는 대응물 |
|---|---|
| SQL-92의 Entry/Intermediate/Full 준수 수준 | GQL의 mandatory / optional feature 구분 → 벤더별 부분 준수 |
| Oracle `(+)` → 9년 뒤 `LEFT JOIN` | 엔진별 경로 표기(Cypher `*1..3`, SPARQL `+`) → 언제 GQL 표기로 수렴할지 미정 |
| MySQL `CHECK` 파싱만 하고 무시 | 표준 절을 문법만 받고 의미를 달리 구현하는 엔진이 나올 위험 |
| 표준 `OFFSET…FETCH`가 있어도 `LIMIT`이 살아남음 | Cypher 관용구가 GQL 표준 문법보다 오래 살아남을 가능성 |

실제 관측 데이터도 양방향입니다. 한쪽에서는 Kuzu 0.11.3이 `LET`/`NEXT`/`FILTER`를 여전히 거부하고(예제 3), SQL/PGQ(ISO/IEC 9075-16:2023)는 프로덕션 채택 사례를 찾기 어렵습니다(예제 4). 다른 한쪽에서는 Neo4j가 Cypher 25에 GQL 문법(중괄호 질의, `WHEN`/`ELSE` 조건 분기, 중간 필터 `FILTER` 절)을 넣고 GQL 준수 함수 별칭을 추가하며, 2026.02부터 배포 설정의 기본 질의 언어를 `CYPHER_25`로 바꿨습니다. 즉 **수렴은 시작됐지만, 엔진마다 속도가 다르고 몇 년이 걸린다**는 SQL의 그림과 정확히 같습니다.

> 표준의 효과는 "지금 코드가 바뀐다"가 아니라 **"방향이 정해진다"**입니다. — 11장 요약

---

## 4. 실무 준비 방침 (3년 뒤 이식을 싸게 만드는 4가지)

예제 3의 결론과 11장 요약이 제시하는 것.

1. **질의문을 한곳에 모은다.** 애플리케이션 코드에 문자열로 흩뿌리지 말고 질의 저장소(파일/모듈)로 분리. 방언 교체는 "한 디렉터리를 다시 쓰는 일"이 되어야 하고, "전 코드베이스를 grep하는 일"이 되면 안 됩니다.
2. **엔진 고유 함수를 격리한다.** 위 2-4·2-5의 SQL 사례가 정확히 이 문제입니다. `SYSDATE`/`GETDATE()`류에 해당하는 그래프 엔진 고유 함수를 별도 파일에 몰아 두면, 이식 시 교체 지점이 눈에 보입니다.
3. **`ORDER BY`를 강제한다.** 표준이 순서를 보장하지 않는 자리(Oracle `ROWNUM`이 `ORDER BY` 이전에 적용되던 함정이 대표적)에서, 엔진을 바꿨을 때 결과 순서가 조용히 달라지는 사고를 막습니다. 예제 1·2가 모든 질의에 `ORDER BY`를 붙인 이유입니다.
4. **"이 질의가 어떤 질문에 답하는가"를 주석으로 남긴다.** 이식은 결국 **다시 쓰는 일**입니다. 문법을 기계적으로 번역할 수 없는 자리(예: SPARQL에는 홉 상한 표기가 없음)에서는 의도를 알아야 재작성이 가능합니다.

여기에 하나 더 붙일 수 있습니다: **확인 시점을 항상 기록**하세요. 11장이 "확인 시점 2026년 8월, Kuzu 0.11.3"을 반복하는 건 방언 지형이 매년 변하기 때문입니다. 오늘 실패한 `FILTER` 절이 내년에는 성공할 수 있고, 그때 이 판단은 다시 해야 합니다.

---

## 1차 출처

- [ISO/IEC 39075:2024 — Database languages GQL](https://www.iso.org/standard/76120.html)
- [ISO/IEC 9075-16:2023 — SQL/PGQ (Property Graph Queries)](https://www.iso.org/standard/79473.html)
- [GQL:2024 is out — Peter Eisentraut (2024-04-17)](http://peter.eisentraut.org/blog/2024/04/17/gql-2024-is-out)
- [ISO/IEC 39075 Database Language GQL — JTC1 소개 문서 (PDF)](https://jtc1info.org/wp-content/uploads/2024/04/2024-Article-39075-Database-Language-GQL.docx.pdf)
- [GQL Standards (gqlstandards.org)](https://www.gqlstandards.org/)
- [SQL-92 — Wikipedia (연표·준수 수준)](https://en.wikipedia.org/wiki/SQL-92)
- [SQL:1999 — Wikipedia (재귀 질의 도입)](https://en.wikipedia.org/wiki/SQL:1999)
- [SQL-92 Levels: Entry, Intermediate, Full versus Core SQL:1999 onwards — modern-sql.com](https://modern-sql.com/standard/levels)
- [Oracle and Standard SQL — FIPS PUB 127-2 Entry SQL 준수 선언](https://docs.oracle.com/cd/A87860_01/doc/server.817/a85397/ap_stand.htm)
- [ANSI ISO SQL Support In Oracle 9i — ORACLE-BASE](https://oracle-base.com/articles/9i/ansi-iso-sql-support)
- [Outerjoins in Oracle — Oracle Optimizer 블로그 (`(+)` vs ANSI)](https://blogs.oracle.com/optimizer/outerjoins-in-oracle)
- [MySQL 8.0.16 Introducing CHECK constraint — MySQL 공식 블로그](https://dev.mysql.com/blog-archive/mysql-8-0-16-introducing-check-constraint/)
- [Changes in MySQL 8.0.16 (2019-04-25) — 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-16.html)
- [MySQL 8.0 Reference Manual — WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.0/en/with.html)
- [+ (String concatenation) (Transact-SQL) — Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-concatenation-transact-sql)
- [The LIMIT .. OFFSET clause of the SELECT statement — jOOQ 매뉴얼 (엔진별 방언 정리)](https://www.jooq.org/doc/latest/manual/sql-building/sql-statements/select-statement/limit-clause/)
- [TOP and FETCH for T-SQL — AWS SQL Server → Aurora PostgreSQL 마이그레이션 플레이북](https://docs.aws.amazon.com/dms/latest/sql-server-to-aurora-postgresql-migration-playbook/chap-sql-server-aurora-pg.tsql.topfetch.html)
- [GQL conformance — Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/)
- [GQL is here: Your Cypher queries in a GQL world — Neo4j 블로그](https://neo4j.com/blog/cypher-and-gql/cypher-gql-world/)
- [Changes in Neo4j 2025-2026 series — Operations Manual (`db.query.default_language=CYPHER_25`)](https://neo4j.com/docs/operations-manual/current/changes-2025-2026/)
- [SPARQL 1.1 Property Paths — W3C (홉 상한 표기 부재)](https://www.w3.org/TR/sparql11-query/#propertypaths)
