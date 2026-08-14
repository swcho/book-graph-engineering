# 질의 언어 이식을 대비하는 네 가지 방법

**질문**: 질의 언어 이식을 대비하는 네 가지 방법은 무엇인가?

**답**: 질의문을 한곳에 모으고, `ORDER BY`를 강제하고, 엔진 고유 함수를 격리하고, 각 질의가 답하는 질문을 주석으로 남긴다.

---

## 0. 왜 이걸 미리 해 둬야 하나

11장의 결론은 「표준이 나왔다」와 「표준대로 돌아간다」 사이에 몇 년이 있다는 것입니다.

- GQL은 2024년에 국제 표준(ISO/IEC 39075:2024)이 됐습니다.
- 그런데 `ex3_gql_dialects.py`를 실제로 돌려 보면, GQL **표준 전용 절**(`LET`, `NEXT`, `FILTER`)은 엔진이 아직 안 받습니다. 정작 `WITH`(Cypher 방언)와 `-[:Knows*1..2]->`(Cypher 방언)는 잘 돕니다.
- SQL도 같은 길을 걸었습니다. SQL-92가 나오고도 방언이 10년 넘게 남았죠.

```python
# ex3_gql_dialects.py 의 CASES — 표준이 곧 이식성이 아니라는 증거
("GQL 표준: LET 절",    "GQL 표준",   "MATCH (p:Person) LET nm = p.name RETURN nm"),
("GQL 표준: NEXT 절",   "GQL 표준",   "MATCH (p:Person) RETURN p.name AS n NEXT RETURN n"),
("GQL 표준: FILTER 절", "GQL 표준",   "MATCH (p:Person) FILTER p.age > 30 RETURN p.name"),
("Cypher 방언: WITH 절", "Cypher 방언", "MATCH (p:Person) WITH p WHERE p.age > 30 RETURN p.name"),
```

즉 **지금 표준 문법으로 쓸 수는 없고, 3년 뒤에 옮길 준비만 해 둘 수 있습니다.** 그 준비가 아래 네 가지입니다.
네 가지 모두 「지금 성능을 올려 주는 일」이 아니라 「나중에 옮길 때 드는 비용을 미리 깎아 두는 일」이라는 점이 공통점입니다.

| 방법 | 막아 주는 사고 | 이식할 때 얻는 것 |
|---|---|---|
| 질의문을 한곳에 모은다 | 고쳐야 할 질의를 못 찾음 | 바꿀 파일이 유한하고 세어짐 |
| `ORDER BY`를 강제한다 | 엔진 바꾸니 순서가 달라져 결과 비교 실패 | 두 엔진 결과를 그냥 `==`로 비교 가능 |
| 엔진 고유 함수를 격리한다 | 이식 불가 지점이 코드 전체에 번짐 | 이식 불가 지점이 한 파일로 모임 |
| 답하는 질문을 주석으로 남긴다 | 문법은 옮겼는데 의도를 몰라 재작성 불가 | 다른 언어로 「다시 쓸」 수 있음 |

---

## 1. 질의문을 코드에 흩뿌리지 말고 한곳에 모은다

### 왜

이식 작업의 첫 단계는 「고칠 질의가 몇 개인지 세는 것」입니다. 질의문이 서비스 로직 사이에 f-string으로 박혀 있으면 이 개수를 셀 수 없습니다. `grep MATCH`로는 문자열 연결로 조립된 질의를 절대 못 잡습니다.

### 나쁜 예 — 흩뿌린 질의

```python
# services/churn.py
def find_resigned(conn, grade):
    q = "MATCH (c:Company {grade:'" + grade + "'})-[:Terminated]->(o:Contract), "
    q += "(c)-[:Signed]->(n:Contract) WHERE o.endedOn < n.startedOn RETURN c.name"
    return [r[0] for r in _rows(conn.execute(q))]

# reports/monthly.py — 거의 같은 질의가 또 있다. 문장이 조금 달라서 grep 으로 짝을 못 맞춘다.
def monthly(conn):
    return conn.execute("MATCH (c:Company)-[:Signed]->(n) RETURN c.name, n.id")
```

### 좋은 예 — 질의 카탈로그

11장 예제가 실제로 이 모양입니다. `ex1_three_languages.py`는 질의를 모듈 상단 상수로 뽑아 두고, 함수는 그걸 실행만 합니다.

```python
# ex1_three_languages.py — 질의는 상수, 코드는 실행자
CYPHER = """
MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
WHERE o.endedOn < n.startedOn
RETURN c.name AS 고객
ORDER BY 고객
"""

SPARQL = """
PREFIX ex: <http://example.org/>
SELECT ?고객 WHERE {
    ?c ex:name ?고객 ; ex:terminated ?o ; ex:signed ?n .
    ?o ex:endedOn   ?end .
    ?n ex:startedOn ?start .
    FILTER(?end < ?start)
} ORDER BY ?고객
"""
```

한 걸음 더 나가면 `ex2_path_queries.py`처럼 **같은 질문에 대한 언어별 문장을 한 자리에 나란히** 둡니다. 이러면 이식 진행률이 딕셔너리 크기로 보입니다.

```python
# ex2_path_queries.py — 질문 이름 → (Cypher, SPARQL) 짝
QUERIES = {
    "직접 자회사만": (
        "MATCH (a:Co)-[:ParentOf]->(b:Co) RETURN a.name, b.name ORDER BY a.name, b.name",
        """PREFIX ex: <http://example.org/>
           SELECT ?p ?c WHERE { ?a ex:parentOf ?b . ?a ex:name ?p . ?b ex:name ?c }
           ORDER BY ?p ?c"""),
    "1~3단계 아래 전부": (
        "MATCH (a:Co)-[:ParentOf*1..3]->(b:Co) RETURN a.name, b.name ORDER BY a.name, b.name",
        """PREFIX ex: <http://example.org/>
           SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }
           ORDER BY ?p ?c"""),
}
```

실무 배치는 이 정도면 충분합니다.

```
queries/
  churn.cypher          # 파일 하나 = 질문 하나
  subsidiaries.cypher
  churn.sparql          # 이식 대상 언어가 늘면 확장자만 늘어난다
  registry.py           # 이름 → 파일 매핑 + 파라미터 바인딩
```

부수 효과 하나. 질의문을 문자열 조립에서 떼어내면 **파라미터 바인딩**을 쓸 수밖에 없어져서 주입(injection)도 같이 막힙니다. 위 예제들이 `f"CREATE (:Company {{name:'{name}'}})"`처럼 조립하는 건 시연용 시드 데이터라 그런 것이고, 프로덕션에서 따라 할 모양은 아닙니다.

---

## 2. `ORDER BY`를 강제한다

### 왜 — `ORDER BY` 없는 결과 순서는 엔진마다 다르다

이게 네 가지 중 유일하게 **당장 버그를 만드는** 항목입니다.

정렬을 명시하지 않으면 결과 순서는 명세가 보장하지 않는 **구현 세부사항**입니다.

- SPARQL 1.1은 해(solution)의 나열을 순서 없는 **집합**으로 정의합니다. `ORDER BY`가 없으면 어떤 순서로 줘도 명세 준수입니다.
- SQL도 같습니다. `ORDER BY` 없는 `SELECT`의 행 순서는 정의되지 않습니다.
- Cypher/Gremlin도 마찬가지입니다. 순서는 실행 계획이 정합니다.

그리고 순서는 **엔진을 바꾸지 않아도** 바뀝니다.

- 실행 계획이 바뀔 때: `ex5_read_plan.py`의 두 질의처럼, 옵티마이저가 `City`부터 스캔하느냐 `Person`부터 스캔하느냐에 따라 출력 순서가 달라집니다.
- 병렬 실행/파티션 순서가 바뀔 때.
- 색인이 추가·삭제될 때(색인 스캔은 색인 순, 전체 스캔은 저장 순).
- 데이터가 늘어 계획이 뒤집힐 때. 그래서 **개발 장비에서는 통과하고 프로덕션에서만 깨집니다.**

이식 상황에서는 더 직접적입니다. 두 엔진의 답이 같은지 확인하려면 순서가 같아야 합니다. `ex1`의 마지막 검증이 정확히 이걸 합니다.

```python
# ex1_three_languages.py — 세 언어의 답을 그냥 == 로 비교한다
same = cypher_rows == sparql_rows == gremlin_rows
print(f"\n셋이 같은가: {'예' if same else '아니오'}")
```

`==`가 성립하는 이유는 세 경로 전부 순서를 못 박아 뒀기 때문입니다.

```python
CYPHER = "... RETURN c.name AS 고객 ORDER BY 고객"        # 엔진이 정렬
SPARQL = "... } ORDER BY ?고객"                          # 엔진이 정렬
def gremlin_style():
    ...
    return sorted(set(out))                              # 손으로 정렬 (엔진이 없으니)
```

`ORDER BY`가 하나라도 빠지면 이 비교는 **간헐적으로** 실패합니다. 재현이 안 되는 종류의 실패라 원인 찾기가 제일 나쁩니다.

### 나쁜 예 → 좋은 예

```python
# 나쁜 예 — 「어차피 삽입 순서로 나오던데」
q = "MATCH (a:Co)-[:ParentOf]->(b:Co) RETURN a.name, b.name"
assert run(q)[0] == ("가온테크", "가온소프트")   # 계획이 바뀌는 날 깨진다

# 좋은 예 — 순서를 질의가 책임진다
q = "MATCH (a:Co)-[:ParentOf]->(b:Co) RETURN a.name, b.name ORDER BY a.name, b.name"
```

### 강제하는 법 (「권장」이 아니라 「강제」)

`ex2`의 모든 질의에 `ORDER BY`가 붙어 있는 건 우연이 아닙니다. 규칙으로 만들어야 지켜집니다.

```python
# tests/test_query_catalog.py — 카탈로그 전체를 훑는 린트 테스트
import re, pathlib

def test_every_query_is_ordered():
    for path in pathlib.Path("queries").glob("*.cypher"):
        sql = path.read_text()
        assert re.search(r"\bORDER BY\b", sql, re.I), f"{path}: ORDER BY 없음"

def test_limit_needs_order():
    # LIMIT + ORDER BY 없음 = 「아무 N개」. 거의 항상 버그다.
    for path in pathlib.Path("queries").glob("*"):
        sql = path.read_text()
        if re.search(r"\bLIMIT\b", sql, re.I):
            assert re.search(r"\bORDER BY\b", sql, re.I), f"{path}: LIMIT 인데 정렬 없음"
```

`LIMIT`은 특히 위험합니다. `ORDER BY` 없는 `LIMIT 10`은 「상위 10개」가 아니라 「아무 10개」이고, 그 「아무」가 엔진마다 다릅니다.

**주의할 대가 두 개.** (1) 정렬은 비용입니다. 큰 결과에 전면 정렬을 붙이면 느려지므로, 정렬 키에 색인을 두거나 `LIMIT`과 함께 써서 상위 N개 정렬로 끝나게 하세요. (2) 정렬 결과 자체도 완전히 이식되지는 않습니다 — 문자열 콜레이션(한글·대소문자 정렬 규칙)과 `NULL`의 위치(`NULLS FIRST/LAST`)는 엔진마다 다릅니다. 그래도 「정렬 안 함」보다는 「정렬하고 콜레이션 차이만 남기기」가 압도적으로 낫습니다.

---

## 3. 엔진 고유 함수는 별도 파일로 격리한다

### 왜

이식 비용은 「이식 불가한 코드의 양」이 아니라 「이식 불가한 코드가 퍼진 범위」에 비례합니다. 엔진 고유 기능이 200군데에 흩어져 있으면 200군데를 검토해야 하고, 어댑터 한 파일에 모여 있으면 그 파일만 다시 쓰면 됩니다.

11장이 보여 준 실제 격차들이 전부 여기 해당합니다.

| 기능 | Cypher | SPARQL | SQL |
|---|---|---|---|
| 가변 길이 경로 상한 | `-[:ParentOf*1..3]->` | **표준 문법 없음** (`ex:parentOf+`만) | `WITH RECURSIVE` 20줄 |
| 중간 결과 파이프 | `WITH` (방언) | 하위 `SELECT` | 파생 테이블 |
| GQL 표준 절 | `LET`/`NEXT`/`FILTER` 미지원 | 해당 없음 | 해당 없음 |

`ex2`의 결론이 이 표의 첫 줄을 콕 짚습니다.

```
  Cypher : -[:ParentOf*1..3]->     상한을 «반드시» 쓸 수 있다
  SPARQL : ex:parentOf+            상한 표기가 없다
  SQL    : WITH RECURSIVE ... 20줄  (3장 참조)
```

SPARQL에는 「최대 몇 홉」을 적는 표준 문법이 없으니, 9장에서 배운 「상한을 걸어라」를 질의 타임아웃·결과 개수 제한·깊이를 손으로 펼쳐 쓰기로 대신해야 합니다. **같은 의도인데 구현 수단이 엔진마다 다른 자리** — 정확히 격리해야 할 지점입니다.

### 나쁜 예 — 고유 기능이 로직에 섞임

```python
# services/org.py — Kuzu 전용 문법과 Kuzu 전용 함수가 서비스 코드에 노출됨
def descendants(conn, root, depth=3):
    q = f"""
    MATCH (a:Co {{name:'{root}'}})-[:ParentOf*1..{depth}]->(b:Co)
    RETURN b.name, list_element(...)      # 엔진 고유 함수
    """
```

### 좋은 예 — 포트/어댑터

```python
# graph/port.py — 「무엇을 원하는가」만 정의. 질의 언어가 여기 등장하지 않는다.
from typing import Protocol

class GraphPort(Protocol):
    def descendants(self, root: str, max_depth: int) -> list[str]:
        """root 아래 max_depth 단계까지의 자회사 이름을 정렬해서 돌려준다."""
```

```python
# graph/adapter_cypher.py — 이 파일만 Cypher 를 안다
class CypherAdapter:
    Q = ("MATCH (a:Co {name:$root})-[:ParentOf*1..%d]->(b:Co) "
         "RETURN DISTINCT b.name AS name ORDER BY name")

    def descendants(self, root, max_depth):
        # 상한이 문법에 있다 → 그대로 표현
        return [r[0] for r in self._rows(self.Q % max_depth, {"root": root})]
```

```python
# graph/adapter_sparql.py — 이 파일만 SPARQL 을 안다
class SparqlAdapter:
    # 상한 표기가 표준에 없다 → 깊이를 «명시적으로 펼쳐서» 흉내 낸다
    HOP = "?a (ex:parentOf){%d} ?b ."   # 엔진이 {n} 을 지원할 때만. 아니면 UNION 으로 전개

    def descendants(self, root, max_depth):
        blocks = " UNION ".join(
            "{ ?a %s ?b . ?b ex:name ?name }" % (" / ".join(["ex:parentOf"] * d))
            for d in range(1, max_depth + 1))
        q = (f"PREFIX ex: <http://example.org/>\n"
             f"SELECT DISTINCT ?name WHERE {{ ?a ex:name '{root}' . {blocks} }}\n"
             f"ORDER BY ?name")           # 여기도 ORDER BY 강제 (규칙 2)
        return [str(r[0]) for r in self._g.query(q)]
```

효과는 두 가지입니다.

1. **이식 범위가 유한해집니다.** GQL로 옮길 때 `adapter_gql.py`를 새로 쓰면 되고, 서비스 코드는 한 줄도 안 건드립니다.
2. **같은 테스트를 두 어댑터에 그대로 돌릴 수 있습니다.** 이게 이식이 끝났다는 증거가 됩니다.

```python
import pytest

@pytest.mark.parametrize("adapter", [CypherAdapter(), SparqlAdapter()])
def test_descendants_agree(adapter):
    # ORDER BY 를 강제해 뒀으므로 리스트 == 로 비교된다 (규칙 2 가 규칙 3 을 받쳐 준다)
    assert adapter.descendants("가온테크", 3) == ["가온소프트", "가온연구소"]
```

격리해야 할 것 체크리스트: 경로 상한 표기 / 전문검색·유사도 함수 / 날짜·시간 함수 / 문자열 함수 / 집계·`GROUP BY` 방식 / 페이지네이션(`SKIP`·`LIMIT`·`OFFSET`) / 프로시저 호출(`CALL db.*`, APOC 등) / 타임아웃 지정 / `EXPLAIN` 출력 파싱.

---

## 4. 「이 질의가 어떤 질문에 답하는가」를 주석으로 남긴다

### 왜 — 이식은 번역이 아니라 재작성이다

이게 넷 중 제일 값싸고, 제일 자주 빠집니다.

핵심은 이겁니다. **문장을 기계적으로 옮기는 건 대개 불가능합니다.** `ex2`가 그 증거입니다. Cypher의 `*1..3`을 SPARQL로 「번역」할 방법이 없습니다. 대신 「3단계 아래까지의 자회사를 알고 싶다」는 **질문**을 알면 SPARQL로 **다시 쓸** 수 있습니다.

의도를 모르면 이식하는 사람은 판단할 수가 없습니다.

- `*1..3`의 `3`은 **의미 있는 조직 깊이**였나, 아니면 폭주를 막는 **안전 상한**이었나? 앞이면 SPARQL에서도 반드시 3을 재현해야 하고, 뒤면 타임아웃으로 대체해도 됩니다. 문장만 보면 구별할 수 없습니다.
- `DISTINCT`는 중복 제거가 요구사항이었나, 조인 폭발을 덮으려고 붙인 반창고였나?
- `LIMIT 100`은 화면 페이지 크기였나, 성능 방어선이었나?

### 좋은 예 — 질의 헤더 규격

```python
CYPHER_CHURN = """
-- 질문: 계약을 해지했다가 «그 뒤에» 다시 계약한 고객은 누구인가?
-- 쓰는 곳: 월간 이탈-복귀 리포트, CS 재접촉 대상 추출
-- 판정 기준: 해지 계약의 endedOn < 신규 계약의 startedOn (같은 날은 제외)
-- 순서: 고객명 오름차순 — 리포트 재현성과 엔진 간 결과 비교를 위해 «필수». 지우지 말 것.
-- 엔진 의존: 없음. (Cypher/GQL 공통 문법만 사용)
-- 확인: Kuzu 0.11.3, 2026-08
MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
WHERE o.endedOn < n.startedOn
RETURN c.name AS 고객
ORDER BY 고객
"""

CYPHER_DESCENDANTS = """
-- 질문: 이 회사 아래 자회사 «전부»는? (손자회사까지)
-- 상한 3 의 의미: 안전 상한이다. 우리 조직은 실제로 2단계까지만 있다(9장 폭주 방지).
--   → 이식할 때 3 을 그대로 옮기지 않아도 된다. 타임아웃/결과 제한으로 대체해도 의도는 지켜진다.
-- 엔진 의존: -[:ParentOf*1..3]-> 는 Cypher 방언. SPARQL 에는 상한 표기가 없다.
MATCH (a:Co {name:$root})-[:ParentOf*1..3]->(b:Co)
RETURN DISTINCT b.name AS name
ORDER BY name
"""
```

`ex1`·`ex2`의 docstring 첫 줄이 정확히 이 역할을 합니다. 「예제 2 — 가변 길이 경로. 세 언어의 표기가 제일 크게 갈리는 자리.」 무엇을 하는지가 아니라 **왜 이 질의가 존재하는지**를 적어 뒀습니다.

또 하나. 주석에 **확인 시점**을 남기세요. 11장 예제 전부가 「확인 시점: Kuzu 0.11.3, rdflib 7.5.0」을 달고 있습니다. 방언은 엔진 버전과 함께 움직이므로, 3년 뒤 이식하는 사람에게는 「어느 버전에서 이게 됐다」가 문법 자체보다 중요할 수 있습니다.

---

## 5. 함께 기억할 경계

이 네 가지가 **해결하지 않는** 것도 같이 알아 두면 카드가 완성됩니다.

- **성능은 안 옮겨집니다.** 문법을 옮겨도 실행 계획은 새 엔진이 새로 정합니다. `ex5_read_plan.py`가 보여 준 「작은 쪽부터 스캔」 같은 판단은 엔진마다 다릅니다. 이식 후에는 계획을 다시 읽어야 합니다.
- **저장 위치를 바꿔도 조인 폭발은 남습니다.** SQL/PGQ가 데이터를 옮기지 않고 그래프 시각만 얹어 주지만, `ex4`의 결론대로 「조인 폭발은 그대로 남는다(3장). 저장 위치가 아니라 «따라가는 값»이 문제였으니까」입니다.
- **모델링 차이는 어댑터로 못 가립니다.** Cypher(속성 그래프)와 SPARQL(RDF 트리플)은 데이터 모델 자체가 달라서, `seed.py`가 같은 사실을 `COMPANIES`/`CONTRACTS` 테이블과 `TTL` 트리플 두 벌로 따로 적어 둡니다. 질의 계층 격리는 질의만 격리합니다.

## 6. 30초 복습

1. **모은다** — 질의문 한곳에. 세지 못하면 옮기지 못한다.
2. **정렬한다** — `ORDER BY` 강제. 없으면 순서가 엔진·계획·데이터량마다 달라져 결과 비교가 간헐 실패한다.
3. **격리한다** — 엔진 고유 함수·문법은 어댑터 한 파일로. 이식 범위를 유한하게 만든다.
4. **적어 둔다** — 이 질의가 답하는 질문을 주석으로. 이식은 번역이 아니라 재작성이므로 의도가 필요하다.

## 참고 출처

- [ISO/IEC 39075:2024 (GQL)](https://www.iso.org/standard/76120.html)
- [ISO/IEC 9075-16:2023 (SQL/PGQ)](https://www.iso.org/standard/79473.html)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) — 해 나열의 순서 미보장, `ORDER BY`
- [SPARQL 1.1 property paths](https://www.w3.org/TR/sparql11-query/#propertypaths) — 상한 표기가 없다
- [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Apache TinkerPop (Gremlin)](https://tinkerpop.apache.org/docs/current/reference/)
- [GQL Standards](https://www.gqlstandards.org/)
