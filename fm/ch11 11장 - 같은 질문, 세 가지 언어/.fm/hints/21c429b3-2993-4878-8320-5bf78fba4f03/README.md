# SQL/PGQ의 가치와 한계

**질문** — SQL/PGQ의 가치와 한계는 각각 무엇인가?

**답** — 데이터를 옮기지 않고 그래프 시각만 얹는 것이 가치이고, 구현이 아직 덜 퍼졌으며 조인 폭발은 그대로 남는 것이 한계다.

---

## 한 줄로 외울 것

> **가치 = 이사 안 함(no data movement) / 한계 = 아직 안 깔림(implementation) + 여전히 안 빨라짐(join explosion)**

한계가 두 개라는 걸 놓치기 쉽습니다. 하나는 **시간이 지나면 풀리는 한계**(구현 보급), 다른 하나는 **시간이 지나도 안 풀리는 한계**(조인 폭발)입니다. 이 구분이 이 카드의 핵심입니다.

---

## 1. SQL/PGQ가 뭔가

**SQL/PGQ = SQL Property Graph Queries**, SQL:2023의 **Part 16**입니다.

| 항목 | 내용 |
|---|---|
| 정식 표준 번호 | ISO/IEC 9075-16:2023 (2023년 6월 공표, 269쪽) |
| 위치 | SQL 표준의 한 파트 — 즉 **별도 언어가 아니라 SQL의 확장** |
| 형제 표준 | GQL(ISO/IEC 39075:2024) — 이건 **독립된 그래프 질의 언어** |
| 정정판 | ISO/IEC 9075-16:2023/Cor 1:2026 (기술 정정 1) |

**GQL과 헷갈리지 마세요.** 11장은 둘을 나란히 다루는데 역할이 다릅니다.

- **GQL**: 그래프 DB를 위한 **독립 표준 언어**. Cypher의 후계자 격. 그래프 저장소가 따로 있다고 전제.
- **SQL/PGQ**: **관계형 DB 안에서** 테이블에 그래프 뷰를 얹는 문법. 저장소는 그대로 RDB.

---

## 2. 가치 — 「데이터를 옮기지 않는다」

### 문법이 그 가치를 그대로 보여 준다

`ex4_sql_pgq.py`의 표준 문법 부분입니다.

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

SELECT * FROM GRAPH_TABLE (biz
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
        (c)-[IS Signed]->(n IS Contract)
  WHERE o.ended_on < n.started_on
  COLUMNS (c.name AS 고객)
);
```

읽는 법:

- `CREATE PROPERTY GRAPH` — **데이터를 만드는 게 아니라 메타데이터를 만듭니다.** 새 테이블도, 복사본도 안 생깁니다. 「이 테이블은 정점으로 봐라, 이 테이블은 간선으로 봐라」는 **선언**입니다. 관계형 뷰(VIEW)와 성격이 같습니다.
- `VERTEX TABLES` — 행 = 정점. `KEY`는 정점 식별자, `LABEL`은 그래프 라벨, `PROPERTIES`는 어느 컬럼을 속성으로 노출할지.
- `EDGE TABLES` — 행 = 간선. `SOURCE`/`DESTINATION`이 **외래 키를 간선의 양 끝으로 재해석**합니다. 여기가 결정적입니다. 이미 있던 FK가 그대로 간선이 됩니다.
- `GRAPH_TABLE(...)` — 그래프 패턴 매칭의 결과를 **테이블로 되돌려 주는 함수**. 그래서 바깥은 그냥 `SELECT * FROM ...`입니다. 조인·`ORDER BY`·서브쿼리 등 기존 SQL과 자연스럽게 섞입니다.
- `MATCH (c)-[IS Terminated]->(o)` — Cypher와 거의 같은 화살표 패턴. 라벨 지정만 `:` 대신 `IS`를 씁니다.

### 무엇을 절약하는가 — 「두 벌 운영」의 비용

같은 질문을 평범한 SQL로 쓰면 이렇습니다.

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

의미는 같습니다. 그런데 「해지한 뒤에 다시 계약한 고객」이라는 **의도**는 4단 조인에 묻혀 버립니다. SQL/PGQ의 `MATCH` 두 줄은 그 의도를 그림으로 보여 줍니다.

여기서 진짜 가치는 가독성 그 위입니다. SQL/PGQ가 없으면 그래프 질의를 쓰기 위해 보통 이 길을 갑니다.

1. 그래프 DB를 따로 세운다
2. RDB → 그래프 DB로 ETL 파이프라인을 만든다
3. **두 벌의 데이터를 동기화한다** ← 여기가 지옥
4. 스키마가 바뀌면 양쪽을 같이 고친다
5. 정합성 사고가 나면 「어느 쪽이 진실인가」를 따진다

3장에서 말한 **「두 벌 운영」의 비용**이 이겁니다. SQL/PGQ는 이 다섯 단계를 전부 안 내도 됩니다. 원본 테이블 하나만 유지하고, 그 위에 **보는 시각(view)** 만 얹으니까요. 진실의 원천이 하나로 남습니다.

책의 표현을 그대로:

> SQL/PGQ 의 값어치는 «데이터를 옮기지 않아도 된다»는 데 있다.
> 테이블은 그대로 두고 그래프로 보는 시각만 얹는다.
> 3장에서 본 «두 벌 운영»의 비용을 안 내도 된다는 뜻이다.

---

## 3. 한계 (1) — 구현이 아직 덜 퍼졌다

표준이 2023년에 나왔지만, 2026년 8월 기준으로 **아무 DB에나 쓸 수 있는 문법이 아닙니다.** 그래서 `ex4_sql_pgq.py`는 특이한 구조를 가집니다.

- 표준 문법(`PGQ`)은 **문자열로 출력만 하고 실행하지 않습니다.**
- 실제로 돌리는 건 같은 뜻의 `PLAIN_SQL`(sqlite3)입니다.
- 답이 맞는지는 평범한 SQL로 확인하고, 「앞으로 이렇게 쓰게 될 모양」만 보여 줍니다.

책의 확인 시점 문장:

> 다만 2026년 8월 기준으로, 이 문법을 프로덕션에서 쓰는 팀을 저는 못 봤다.
> 구현이 덜 퍼졌다. 그래서 이 예제는 «돌아가는 코드»가 아니라
> «앞으로 이렇게 될 가능성»을 보여 주는 것이다.

### 엔진별 현황 (참고, 2026년 8월경)

| 엔진 | 상태 | 메모 |
|---|---|---|
| Oracle Database 23ai | 상용 구현 있음 | 표준화를 주도했고 첫 상용 SQL/PGQ 구현으로 알려짐 |
| DuckDB (DuckPGQ) | 커뮤니티 확장 | 코어가 아니라 별도 익스텐션. 활발히 개발 중 |
| PostgreSQL | 패치/부분 구현 | 표준의 **부분집합**. 코어 기본 기능 아님 |
| Google Spanner Graph | SQL/PGQ가 아니라 **GQL** 쪽 | 구글·마이크로소프트는 GQL에 베팅 |

정리하면 **「아무도 안 쓴다」가 아니라 「어디서나 쓸 수는 없다」** 입니다. 특정 벤더에 붙으면 오늘도 쓸 수 있지만, 그건 이식성을 잃는 선택입니다. GQL과 SQL/PGQ로 업계가 두 갈래로 갈린 것도 보급을 늦추는 요인입니다.

이건 11장의 다른 카드와 짝을 이룹니다. GQL도 2024년에 표준이 됐지만 `ex3_gql_dialects.py`에서 `LET`·`NEXT`·`FILTER`는 Kuzu에서 실패합니다. **「표준이 나왔다」와 「표준대로 돌아간다」 사이에 몇 년이 있다** — SQL/PGQ도 같은 자리에 있습니다. SQL-92가 나온 뒤에도 방언이 10년 넘게 남았던 것처럼요.

**이 한계는 시간이 풀어 줍니다.** 3년 뒤엔 다른 답이 나올 문항입니다. 그래서 확인 시점을 꼭 같이 읽으라고 책이 강조합니다.

---

## 4. 한계 (2) — 조인 폭발은 그대로 남는다

이게 더 중요한 한계이고, **시간이 풀어 주지 않는 한계**입니다.

> 그리고 옮기지 않아도 된다는 게 공짜라는 뜻은 아니다.
> 조인 폭발은 그대로 남는다(3장). 저장 위치가 아니라 «따라가는 값»이 문제였으니까.

### 왜 안 풀리는가

`GRAPH_TABLE`은 **문법 설탕에 가깝습니다.** `MATCH (c)-[IS Terminated]->(o), (c)-[IS Signed]->(n)`은 결국 옵티마이저가 조인으로 풀어냅니다. 아까 본 4단 조인이 그대로 남는 거죠.

- 홉이 하나 늘면 조인이 하나 늘고, 중간 결과가 곱셈으로 커집니다.
- 3홉·4홉·가변 길이 경로로 가면 중간 결과 폭발이 그대로 터집니다.
- 문법이 짧아진 것과 실행이 빨라진 것은 **아무 관계가 없습니다.**

### 3장의 논지를 다시 확인

3장의 결론은 **「그래프 DB가 빠른 이유는 데이터를 그래프 파일에 넣었기 때문이 아니라, 이웃을 포인터로 따라가기 때문」** 이었습니다. 즉 문제는 **저장 위치**가 아니라 **따라가는 값**(index-free adjacency 대 매번 인덱스 조회/조인)입니다.

SQL/PGQ는 **저장 위치를 안 바꾸는 대신, 따라가는 방식도 안 바꿉니다.** 그래서 이사 비용은 아끼지만 순회 성능은 못 얻습니다. 가치와 한계가 **같은 뿌리에서 나옵니다** — 이 대칭을 이해하면 카드를 통째로 외울 필요가 없습니다.

물론 엔진이 `GRAPH_TABLE` 전용 순회 연산자나 전용 인접 인덱스를 넣으면 개선될 수 있고, 실제로 그런 연구(cross-model efficiency 등)가 진행 중입니다. 다만 **표준 문법을 쓴다는 사실만으로 성능이 따라오지는 않는다**는 게 요점입니다.

---

## 5. 시험 대비 정리

| 축 | 내용 | 성격 |
|---|---|---|
| 가치 | 데이터를 옮기지 않고 테이블 위에 그래프 시각만 얹음 → 두 벌 운영 비용 없음, 진실의 원천 하나 | 구조적 장점 |
| 한계 A | 구현이 아직 덜 퍼졌다 (특정 벤더 한정, GQL과 진영 분리) | **시간이 풀어 줌** |
| 한계 B | 조인 폭발은 그대로 남는다 (저장 위치가 아니라 따라가는 값이 문제) | **시간이 안 풀어 줌** |

### 자주 틀리는 지점

- ❌ 「SQL/PGQ를 쓰면 그래프 DB처럼 빨라진다」 → 아닙니다. 빨라지는 건 **작성·이해**이고, 실행은 조인 그대로입니다.
- ❌ 「SQL/PGQ와 GQL은 같은 것」 → 아닙니다. SQL/PGQ는 SQL의 Part 16(9075-16:2023), GQL은 독립 표준(39075:2024).
- ❌ 「`CREATE PROPERTY GRAPH`가 그래프를 만든다」 → 메타데이터만 만듭니다. 데이터 복사가 없습니다.
- ✅ 한계를 **두 개** 대답해야 합니다. 하나만 쓰면 반만 맞습니다.

---

## 1차 출처

- [ISO/IEC 9075-16:2023 (SQL/PGQ)](https://www.iso.org/standard/79473.html)
- [ISO/IEC 9075-16:2023/Cor 1:2026 (기술 정정 1)](https://www.iso.org/standard/93698.html)
- [ISO/IEC 39075:2024 (GQL)](https://www.iso.org/standard/76120.html) — 비교용
- [Property Graphs in Oracle Database 23ai: The SQL/PGQ Standard](https://blogs.oracle.com/database/property-graphs-in-oracle-database-23ai-the-sql-pgq-standard)
- [DuckPGQ — SQL/PGQ for DuckDB](https://duckpgq.org/documentation/sql_pgq/)
- [Spanner Graph and ISO standards](https://docs.cloud.google.com/spanner/docs/graph/iso-standards)
- 이 장 예제: `content/ch11/code/ex4_sql_pgq.py`, `content/ch11/code/ex3_gql_dialects.py`
