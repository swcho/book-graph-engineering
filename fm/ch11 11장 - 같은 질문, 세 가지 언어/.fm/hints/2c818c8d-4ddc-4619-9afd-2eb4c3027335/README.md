# SPARQL에서 「홉 상한」을 걸어야 할 때

**질문** SPARQL에서 홉 상한을 걸어야 할 때 쓸 수 있는 대안은 무엇인가?

**답** 질의 타임아웃, 결과 개수 제한(`LIMIT`), 아니면 깊이를 명시적으로 펼쳐 쓰는 방법이다.

---

## 1. 왜 대안이 필요한가

11장 예제 2(`code/ex2_path_queries.py`)가 세 언어의 가변 길이 경로 표기를 나란히 놓고 끝맺는 문장이 이 카드의 출처입니다.

```
표기를 나란히 놓으면 이렇다.
  Cypher : -[:ParentOf*1..3]->     상한을 «반드시» 쓸 수 있다
  SPARQL : ex:parentOf+            상한 표기가 없다
  SQL    : WITH RECURSIVE ... 20줄  (3장 참조)

SPARQL 의 경로 표현에는 «최대 몇 홉»을 적는 표준 문법이 없다.
그래서 9장에서 본 «상한을 걸어라»를 SPARQL 에서는 다른 방식으로 해야 한다.
질의 타임아웃, 결과 개수 제한, 아니면 깊이를 명시적으로 펼쳐 쓰기.
```

SPARQL 1.1의 [속성 경로](https://www.w3.org/TR/sparql11-query/#propertypaths) 연산자는 이게 전부입니다.

| 표기 | 뜻 | 상한을 적을 수 있나 |
|---|---|---|
| `ex:p` | 정확히 1홉 | 고정 길이 |
| `ex:p/ex:p` | 정확히 2홉 (연결) | 고정 길이 |
| `ex:p?` | 0 또는 1홉 | 상한 1 |
| `ex:p+` | 1홉 이상, **무한** | ✗ |
| `ex:p*` | 0홉 이상, **무한** | ✗ |
| `ex:p{1,3}` | — | **표준에 없음** |

중괄호 형태(`{n}`, `{n,m}`, `{n,}`, `{,m}`)는 SPARQL 1.1 초안에는 있었지만 **최종 권고안에서 삭제**됐습니다. 이유가 재미있는데, 「경로를 셀 것인가」 문제 때문입니다. 워킹그룹은 평가 비용 문제를 피하려고 `*`, `+`, `?`를 **비계수(non-counting)** 의미론으로 바꿨습니다. 즉 `ex:p+`는 중복을 남기지 않고 「도달 가능한 노드 집합」만 돌려줍니다. 이 결정과 `{n,m}`(길이별로 경로를 세야 함)이 양립하지 않아서 후자가 빠졌습니다.

> **엔진 확장 주의** Apache Jena ARQ는 `elt{n,m}`을 **ARQ 확장**으로 지원합니다(`Syntax.syntaxARQ`가 필요). 표준 SPARQL 파서로 도는 HTTP 엔드포인트에서는 보통 안 먹습니다. 다른 엔진에도 비슷한 확장이 있을 수 있으니 문서를 확인하되, 쓰는 순간 이식성이 사라진다는 걸 감수해야 합니다. 11장 예제가 쓰는 **rdflib**은 표준만 구현하므로 `{1,3}`은 파싱 에러입니다.

이 장의 데이터로 확인해 보면 이렇습니다. `seed.py`의 지배구조는 `가온테크 → 가온소프트 → 가온연구소`.

```sparql
# Cypher의 -[:ParentOf*1..3]-> 에 대응하려고 했는데, 실제로는 상한이 없다
PREFIX ex: <http://example.org/>
SELECT ?p ?c WHERE {
    ?a ex:parentOf+ ?b .
    ?a ex:name ?p .
    ?b ex:name ?c
} ORDER BY ?p ?c
```

이 질의는 3단계든 30단계든 다 따라갑니다. 예제 데이터는 3개 노드라 괜찮지만, 실제 지배구조 그래프나 조직도, 부품 BOM에 이걸 그대로 쓰면 9장에서 본 폭발이 그대로 재현됩니다.

---

## 2. 대안 ①: 질의 타임아웃

「몇 홉까지」가 아니라 「몇 밀리초까지」로 바꿔 막는 방법입니다. **표준 SPARQL 문법이 아니라 엔드포인트 기능**이라, 엔진마다 걸는 자리와 단위가 다릅니다.

### 2.1 HTTP 파라미터로 (Virtuoso, GraphDB, Blazegraph 계열)

```bash
# Virtuoso: &timeout=<밀리초>. 1000 미만이면 무시된다
curl -G https://example.org/sparql \
  --data-urlencode 'query=PREFIX ex: <http://example.org/>
     SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }' \
  --data-urlencode 'timeout=5000' \
  -H 'Accept: application/sparql-results+json'
```

### 2.2 설정 파일로 (Apache Jena Fuseki)

```turtle
# fuseki 설정: 서버 전체 또는 데이터셋/엔드포인트 단위
:service rdf:type fuseki:Service ;
    ja:context [ ja:cxtName "arq:queryTimeout" ; ja:cxtValue "10000,60000" ] ;
    ...
```

`"10000,60000"`은 「첫 결과까지 10초, 전체 60초」라는 뜻입니다(단위 밀리초). 첫 결과가 빨리 나오는 질의는 통과시키고, 전체가 오래 끄는 질의만 자르겠다는 설계입니다.

### 2.3 질의문 안에 힌트로 (Amazon Neptune)

여기서는 질의문 자체에 넣을 수 있는데, 이것도 표준이 아니라 벤더 확장입니다.

```sparql
PREFIX hint: <http://aws.amazon.com/neptune/vocab/v01/QueryHints#>
PREFIX ex:   <http://example.org/>
SELECT ?p ?c WHERE {
    hint:Query hint:queryTimeout 5000 .        # 밀리초. DB 파라미터 값보다 작아야 한다
    ?a ex:parentOf+ ?b .
    ?a ex:name ?p .
    ?b ex:name ?c
}
```

### 2.4 클라이언트에서 (rdflib 같은 인메모리 엔진)

11장 예제가 쓰는 rdflib에는 질의 타임아웃 옵션이 없습니다. 밖에서 감싸야 합니다.

```python
import signal
from rdflib import Graph
from seed import TTL

Q = """PREFIX ex: <http://example.org/>
SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }"""

class QueryTimeout(Exception):
    pass

def _alarm(signum, frame):
    raise QueryTimeout

g = Graph().parse(data=TTL, format="turtle")
signal.signal(signal.SIGALRM, _alarm)
signal.setitimer(signal.ITIMER_REAL, 2.0)      # 2초
try:
    rows = [tuple(str(x) for x in r) for r in g.query(Q)]
except QueryTimeout:
    rows = None                                 # 부분 결과도 «없다». 전부 버린다
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
```

### 의미론과 부작용

- **홉 상한이 아니다.** 5초를 걸어도 4.9초에 200만 홉을 돌았다면 그 200만 홉은 이미 돈 겁니다. 자원 소모를 막는 게 아니라 **소모 시간의 상한**만 정합니다.
- **결정적이지 않다.** 같은 질의, 같은 데이터인데 서버 부하·캐시 상태에 따라 어제는 성공하고 오늘은 실패합니다. 테스트에서 통과한 질의가 프로덕션에서 죽습니다. 재현이 어려운 장애의 전형적인 원인입니다.
- **부분 결과가 조용히 돌아올 수 있다.** Virtuoso의 「anytime query」가 대표적입니다. 타임아웃이 걸리면 에러가 아니라 **불완전한 결과를 200 OK로** 돌려주고, 그 사실은 `X-SQL-State: S1TAT` 같은 HTTP 헤더에만 적힙니다. 헤더를 안 보는 클라이언트는 「자회사가 12개」라는 틀린 답을 그대로 화면에 띄웁니다. 이게 세 대안 중 제일 위험한 부작용입니다.
- **집계와 상성이 나쁘다.** `COUNT`, `ORDER BY`, `MIN`/`MAX`는 전체를 다 봐야 값이 정해집니다. 부분 결과 위에서 계산한 `COUNT`는 그냥 틀린 수입니다.

---

## 3. 대안 ②: 결과 개수 제한 (`LIMIT`)

이건 표준 문법입니다. 「몇 홉」이 아니라 「몇 행」으로 바꿔 막습니다.

```sparql
PREFIX ex: <http://example.org/>
SELECT ?p ?c WHERE {
    ?a ex:parentOf+ ?b .
    ?a ex:name ?p .
    ?b ex:name ?c
}
LIMIT 100
```

경로 탐색 자체를 가두고 싶으면 하위 질의로 감싸서 범위를 좁힙니다.

```sparql
PREFIX ex: <http://example.org/>
SELECT ?p ?c WHERE {
    ?a ex:name "가온테크" .
    {
        SELECT ?a ?b WHERE { ?a ex:parentOf+ ?b }   # 여기서 먼저 잘라 낸다
        LIMIT 100
    }
    ?a ex:name ?p .
    ?b ex:name ?c
}
```

### 의미론과 부작용

- **홉 상한이 아니다.** `LIMIT 100`은 「내가 받을 행의 최대치」입니다. 엔진이 100행을 만든 뒤 멈춰 줄지, 200만 행을 다 만든 뒤 100행만 잘라 줄지는 **구현에 달렸습니다.** 스트리밍 실행기라면 조기 종료가 되지만, 해시 조인이나 정렬이 중간에 끼면 전량 계산이 그대로 일어납니다.
- **`ORDER BY`를 붙이면 절약이 사라진다.** 정렬은 전체 결과를 알아야 하는 연산입니다. `ORDER BY ?p LIMIT 100`은 「200만 행 다 만들고 정렬해서 100행만 준다」는 뜻이 될 수 있습니다. 11장이 이식 대비로 `ORDER BY`를 강제하라고 한 것과 여기서 정면으로 부딪칩니다. **재현성(ORDER BY)과 절약(LIMIT)은 자동으로 같이 오지 않습니다.**
- **`ORDER BY` 없는 `LIMIT`은 「아무 100행」이다.** SPARQL 해답 시퀀스의 순서는 `ORDER BY`가 없으면 정의되지 않습니다. 어느 100행이 올지 보장이 없고, 엔진 버전만 올려도 달라집니다.
- **결과가 잘렸는지 알 방법이 없다.** 100행이 돌아왔을 때 「정확히 100개였다」와 「200만 개 중 100개였다」가 구별되지 않습니다. 관용적인 회피법은 `LIMIT 101`을 걸고 101행이 오면 「더 있음」으로 표시하는 것입니다.

```sparql
# 「잘렸는지」를 알아내는 관용구: 원하는 수 + 1
SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }
LIMIT 101
```

- **깊이와 개수는 다른 축이다.** 넓고 얕은 그래프에서는 2홉만으로 `LIMIT`이 다 차 버려서 3홉 결과는 아예 못 보고, 좁고 깊은 그래프에서는 30홉을 다 돌아도 `LIMIT`에 안 걸립니다. 홉을 막고 싶었는데 막히는 게 홉이 아닙니다.

---

## 4. 대안 ③: 깊이를 명시적으로 펼쳐 쓰기

세 대안 중 **유일하게 진짜 홉 상한**인 방법입니다. `*1..3`을 표기로 못 쓰니, 1홉·2홉·3홉을 손으로 다 적습니다.

### 4.1 교대(`|`)와 연결(`/`)로 (짧게 쓰는 방식)

```sparql
# Cypher 의 -[:ParentOf*1..3]-> 와 «같은 도달 집합»
PREFIX ex: <http://example.org/>
SELECT DISTINCT ?p ?c WHERE {
    ?a ex:parentOf|ex:parentOf/ex:parentOf|ex:parentOf/ex:parentOf/ex:parentOf ?b .
    ?a ex:name ?p .
    ?b ex:name ?c
} ORDER BY ?p ?c
```

`|`(교대)는 `/`(연결)보다 결합 우선순위가 낮으므로 위 경로는 `p | (p/p) | (p/p/p)`로 읽힙니다. 괄호로 명시하면 읽기 좋습니다.

```sparql
?a (ex:parentOf|ex:parentOf/ex:parentOf|ex:parentOf/ex:parentOf/ex:parentOf) ?b .
```

### 4.2 `UNION`으로 (깊이를 값으로 꺼내는 방식)

몇 홉짜리 관계였는지 알아야 할 때가 훨씬 많습니다. 그때는 `UNION` + `BIND`.

```sparql
PREFIX ex: <http://example.org/>
SELECT DISTINCT ?p ?c ?depth WHERE {
    {
        ?a ex:parentOf ?b .
        BIND(1 AS ?depth)
    } UNION {
        ?a ex:parentOf/ex:parentOf ?b .
        BIND(2 AS ?depth)
    } UNION {
        ?a ex:parentOf/ex:parentOf/ex:parentOf ?b .
        BIND(3 AS ?depth)
    }
    ?a ex:name ?p .
    ?b ex:name ?c
} ORDER BY ?p ?depth ?c
```

`seed.py` 데이터에서 이 질의는 다음을 돌려줍니다.

| ?p | ?c | ?depth |
|---|---|---|
| 가온소프트 | 가온연구소 | 1 |
| 가온테크 | 가온소프트 | 1 |
| 가온테크 | 가온연구소 | 2 |

`ex:parentOf+`와 도달 집합은 같지만, 이쪽은 **4홉이 생겨도 질의문을 안 고치는 한 절대 안 따라갑니다.** 그게 상한입니다.

### 4.3 rdflib에서 자동 생성

깊이를 늘리면 질의문이 금방 지저분해지니, 문자열로 만드는 게 실무적입니다.

```python
def bounded_path(pred: str, max_hops: int) -> str:
    """ex:parentOf, 3 -> 'ex:parentOf|ex:parentOf/ex:parentOf|ex:parentOf/.../ex:parentOf'"""
    return "|".join("/".join([pred] * n) for n in range(1, max_hops + 1))

Q = f"""PREFIX ex: <http://example.org/>
SELECT DISTINCT ?p ?c WHERE {{
    ?a {bounded_path("ex:parentOf", 3)} ?b .
    ?a ex:name ?p .
    ?b ex:name ?c
}} ORDER BY ?p ?c"""
```

### 의미론과 부작용

- **의미론이 바뀐다 — 중복.** 이게 제일 자주 물리는 함정입니다. `ex:p+`는 **비계수**라 `(?a, ?b)` 쌍을 한 번만 냅니다. 반면 `ex:p/ex:p`는 그냥 조인이라 **경로 수만큼 행이 나옵니다.** A에서 B로 가는 2홉 경로가 세 갈래면 3행입니다. 게다가 다이아몬드 구조에서는 같은 쌍이 깊이 2와 3에서 각각 잡힙니다. 그래서 위 예제들에 `DISTINCT`가 붙어 있습니다. **`DISTINCT`를 빼먹으면 「자회사 수」가 부풀려집니다.**
- **순환이 있으면 결과가 달라진다.** `ex:p+`는 순환에서도 안전하게 끝나고 자기 자신을 (진짜 순환일 때만) 한 번 냅니다. 펼쳐 쓴 고정 길이 경로는 순환을 지나가며 `?a = ?b`인 행과 중복을 만들어 냅니다. 필요하면 `FILTER(?a != ?b)`를 명시적으로 넣어야 합니다.
- **`*`의 0홉 의미와 다르다.** `ex:p*`는 0홉을 포함하는데, 그 결과 「그래프 안의 모든 항」이 자기 자신과 짝지어집니다(전혀 관계없는 리터럴까지). 펼쳐 쓰기에는 0홉이 없으므로 이 함정이 아예 없습니다 — 여기서는 오히려 장점입니다.
- **질의문이 길어지고, 깊이가 코드에 박힌다.** 상한 5는 5갈래, 8은 8갈래입니다. 상한을 바꾸려면 질의문을 고쳐야 하고, 파라미터화하려면 문자열 조립이 필요합니다. 파서·최적화기 관점에서도 갈래가 많은 교대는 계획이 나빠질 수 있습니다.
- **최적화기가 도와줄 수도 있다.** 반대 방향의 이야기도 있습니다. 고정 길이 경로는 평범한 조인이라 엔진의 통계·조인 순서 최적화를 그대로 받습니다. `p+`의 도달성 계산은 최적화기가 손대기 어려운 블랙박스인 경우가 많습니다. 펼쳐 쓴 질의가 **더 빠른 경우도 실제로 있습니다.**

---

## 5. 세 대안을 한눈에

| | 진짜 홉 상한인가 | 표준인가 | 결정적인가 | 제일 큰 부작용 |
|---|---|---|---|---|
| **타임아웃** | ✗ (시간 상한, 중단) | ✗ 엔진별 | ✗ 부하에 따라 변함 | 부분 결과가 조용히 성공으로 돌아올 수 있음 |
| **`LIMIT`** | ✗ (행 상한, 근사) | ✓ | `ORDER BY` 있어야 ✓ | 잘렸는지 알 수 없음, `ORDER BY`가 절약을 무효화 |
| **펼쳐 쓰기** | **✓** | ✓ | ✓ | 중복 발생(`DISTINCT` 필수), 질의문 길어짐 |

핵심 정리 한 줄. **타임아웃과 `LIMIT`은 「상한」이 아니라 「중단」과 「근사」입니다.** 셋 중 「최대 3홉」이라는 의도를 그대로 표현하는 건 펼쳐 쓰기 하나뿐입니다.

---

## 6. 실무에서는 어떻게 쓰나

셋 중 하나를 고르는 문제가 아닙니다. **역할이 다르므로 겹쳐 씁니다.**

1. **의도는 펼쳐 쓰기로 표현한다.** 도메인이 「최대 3단 자회사」라면 질의문이 그걸 말해야 합니다. `DISTINCT`를 잊지 마세요.
2. **`LIMIT`은 화면·API 보호용으로 덧붙인다.** 상한을 걸었어도 폭이 넓으면 결과가 많습니다. `LIMIT n+1`로 「더 있음」을 감지하고 사용자에게 알립니다.
3. **타임아웃은 엔드포인트 차원의 최후 방어선으로 둔다.** 질의별로 거는 게 아니라 서버 설정으로 걸어서, 누가 무슨 질의를 던져도 엔드포인트가 죽지 않게 합니다.
4. **부분 결과를 반드시 구별한다.** Virtuoso 계열이면 응답 헤더(`X-SQL-State`)를 확인하고, 잘린 결과를 완전한 결과처럼 집계·저장하지 않습니다.
5. **11장의 이식 대비 조언을 적용한다.** 이 세 방법은 다 엔진 의존적이거나 문법이 지저분해집니다. 질의문을 한곳에 모으고, 엔진 고유 부분(타임아웃 힌트, `{n,m}` 확장)은 별도 파일로 격리하고, **「이 질의는 최대 3홉까지만 본다. 도메인 규칙이 3단이라서」를 주석으로 남기세요.** 나중에 Cypher나 GQL로 옮길 때 `*1..3`으로 한 줄로 줄일 수 있는 근거가 그 주석입니다.

---

## 7. 자주 하는 오해

- **「`LIMIT`을 걸었으니 안전하다」** → 아닙니다. 엔진이 전량 계산 후 자를 수 있고, `ORDER BY`가 있으면 거의 확실히 그렇습니다.
- **「타임아웃이 걸리면 에러가 난다」** → 엔진에 따라 아닙니다. 200 OK + 불완전한 결과가 돌아오는 구현이 있습니다.
- **「`ex:p+`를 펼쳐 쓴 것과 결과가 같다」** → 도달 집합은 같아도 **중복 개수가 다릅니다.** `p+`는 비계수, `p/p`는 조인입니다.
- **「`{1,3}`이 우리 엔진에서 되니까 표준이다」** → 아닙니다. SPARQL 1.1 최종안에서 삭제된 문법이고, 벤더 확장(예: Jena ARQ)입니다.
- **「SPARQL이 이 점에서 열등하다」** → 설계 선택입니다. `*`/`+`를 비계수로 만들어 평가 비용을 낮추는 대신 길이 지정을 포기했습니다. 그 대가가 「상한을 손으로 펼쳐야 한다」입니다. 11장의 말대로, **표준의 이런 구멍이 실무를 정합니다.**

---

## 출처

- [SPARQL 1.1 Query Language — Property Paths](https://www.w3.org/TR/sparql11-query/#propertypaths) (W3C 권고안)
- [Feature:PropertyPaths — SPARQL Working Group](https://www.w3.org/2009/sparql/wiki/Feature_PropertyPaths.html) (`{n,m}` 삭제와 비계수 의미론 결정 경과)
- [Apache Jena — ARQ Property Paths](https://jena.apache.org/documentation/query/property_paths.html) (`{n,m}`은 ARQ 확장)
- [Apache Jena — Fuseki: Configuring Fuseki](https://jena.apache.org/documentation/fuseki2/fuseki-configuration.html) (`arq:queryTimeout`)
- [Virtuoso — Anytime Queries](https://docs.openlinksw.com/virtuoso/anytimequeries/) (`&timeout=`, 부분 결과와 `S1TAT`)
- [Amazon Neptune — The queryTimeout SPARQL query hint](https://docs.aws.amazon.com/neptune/latest/userguide/sparql-query-hints-queryTimeout.html)
- 책 11장 예제 `code/ex2_path_queries.py` (Kuzu 0.11.3, rdflib 7.5.0 / 확인 시점 2026년 8월)
