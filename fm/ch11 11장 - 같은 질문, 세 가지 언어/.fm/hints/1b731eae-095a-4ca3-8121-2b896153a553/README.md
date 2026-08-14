# 세 언어의 문법 모양을 한 줄로 대비하면

## 정답 한 줄

| 언어 | 한 줄 표기 | 비유 | 패러다임 |
|---|---|---|---|
| Cypher | `(c)-[:Signed]->(n)` | **그림** — 화이트보드에 그린 것과 같은 모양 | 선언형 |
| SPARQL | `?c ex:signed ?n .` | **문장** — 사실을 한 줄씩 늘어놓는다 | 선언형 |
| Gremlin | `.out('signed')` | **걸음** — 어디로 갈지 순서대로 지시한다 | 명령형에 가깝다 |

앞의 둘은 **무엇을 원하는지**만 적고 방법은 엔진이 정합니다. Gremlin은 **순회 순서를 내가** 정합니다.
그래서 Gremlin은 세밀한 제어가 되고, 대신 최적화기가 도와줄 여지가 적습니다.

이 대비는 11.1절 「그림, 문장, 걸음」의 핵심이고, 예제 `ex1_three_languages.py`가 실행 결과로 확인해 줍니다.
셋 다 **같은 답**을 냅니다. 다른 건 답이 아니라 **문장 모양**, 더 정확히는 **그래프를 생각하는 방식**입니다.

---

## 1. Cypher — ASCII-art 패턴

Cypher는 그래프를 **그려서** 씁니다. 키보드로 그릴 수 있는 문자를 그대로 도형으로 씁니다.

```
(c:Company)-[:Signed]->(n:Contract)
 └───┬───┘  └───┬───┘   └───┬────┘
   노드        관계          노드
```

문법 요소를 하나씩 분해하면:

| 요소 | 표기 | 뜻 |
|---|---|---|
| **노드 = 소괄호** | `(c)` | 동그라미. 원래 그림에서 노드가 동그라미였으니까 |
| 노드 변수 | `(c)` 의 `c` | 뒤에서 다시 참조할 이름. 안 쓰면 `()` 로 익명 가능 |
| 노드 라벨 | `(c:Company)` | 콜론 뒤가 종류. `(c:Company:Client)` 처럼 여러 개도 가능 |
| 노드 속성 | `(c:Company {name:'가온테크'})` | 중괄호 안에 인라인 필터 |
| **관계 = 대괄호** | `-[:Signed]-` | 선 중간에 끼워 넣은 상자. 대괄호 안이 관계 정보 |
| 관계 타입 | `[:Signed]` | 콜론 뒤가 관계 종류. `[:Signed|Renewed]` 로 OR |
| 관계 변수·속성 | `[r:Signed {since:2025}]` | 관계도 속성을 가진다 (속성 그래프의 특징) |
| **방향 = 화살표** | `->` / `<-` / `-` | `(a)-[:X]->(b)` 정방향, `(a)<-[:X]-(b)` 역방향, `(a)-[:X]-(b)` 방향 무시 |
| 가변 길이 | `-[:ParentOf*1..3]->` | 별표 뒤에 `최소..최대`. **상한을 쓸 수 있는 게 Cypher의 강점** |

읽는 법: **왼쪽에서 오른쪽으로, 화살표가 가리키는 대로.**
`(c)-[:Signed]->(n)` 은 "회사 c가 계약 n을 체결했다"입니다. 화살표를 뒤집으면 주체가 바뀝니다.

패턴을 콤마로 여러 개 이어 붙이면 **같은 변수 이름이 조인 키**가 됩니다. 이게 Cypher가 조인을 표현하는 방식입니다.

```cypher
MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
```
두 번째 줄의 `(c)`는 첫 줄의 `c`와 같은 노드입니다. 라벨을 다시 안 써도 됩니다.

---

## 2. SPARQL — triple pattern

SPARQL은 그래프를 **사실의 목록**으로 봅니다. RDF의 세계관이 그렇습니다. 모든 것이 `주어 술어 목적어` 세 토막입니다.

```
?c        ex:signed        ?n        .
└─┬─┘     └───┬───┘      └─┬─┘      ┴
주어       술어          목적어    마침표
(subject) (predicate)   (object)  (트리플 끝)
```

문법 요소를 하나씩:

| 요소 | 표기 | 뜻 |
|---|---|---|
| **변수 = 물음표** | `?c`, `?고객` | 물음표(또는 `$`)로 시작. "여기 들어갈 값을 찾아라" |
| **접두사 선언** | `PREFIX ex: <http://example.org/>` | IRI를 줄여 쓰기 위한 선언. 질의문 맨 앞에 |
| 접두사 이름 | `ex:signed` | `<http://example.org/signed>` 의 축약형. **콜론이 필수** |
| **술어 = 관계** | `ex:signed` | Cypher의 `[:Signed]` 자리. 변수 아닌 IRI로 쓴다 |
| **마침표** | `.` | 트리플 하나의 끝. 문장 부호 그대로의 뜻 |
| 세미콜론 | `;` | **주어를 이어 쓴다**. `?c ex:name ?n ; ex:signed ?s .` |
| 콤마 | `,` | 주어+술어를 이어 쓴다. `?c ex:signed ?a, ?b .` |
| WHERE 블록 | `SELECT ?x WHERE { ... }` | 중괄호 안에 트리플 패턴을 늘어놓는다 |
| 속성 경로 | `ex:parentOf+`, `ex:a/ex:b`, `^ex:signed` | `+` 1회 이상, `*` 0회 이상, `/` 연결, `^` 역방향 |
| FILTER | `FILTER(?end < ?start)` | 값 비교는 트리플로 안 되니까 별도 절로 |

핵심: **방향 화살표가 없습니다.** 방향은 "주어→목적어" 순서 자체에 있습니다.
역방향이 필요하면 순서를 뒤집거나 `^ex:signed` (inverse path)를 씁니다.

그리고 SPARQL에는 **라벨 개념이 없어서** 종류도 트리플로 씁니다. `?c a ex:Company .` — 여기서 `a`는 `rdf:type`의 축약형입니다. Cypher의 `(c:Company)` 한 조각이 SPARQL에서는 트리플 한 줄이 됩니다.

또한 **속성도 트리플입니다.** Cypher는 `c.name`으로 노드 안을 들여다보지만, SPARQL은 `?c ex:name ?고객 .` 로 관계와 똑같이 씁니다. RDF에서는 속성과 관계의 구분이 없습니다.

> **경로 표현의 구멍**: SPARQL 표준에는 `*1..3` 같은 **상한 표기가 없습니다** (11.2절). `+` 와 `*` 만 있어서 "최대 3홉"을 표준 문법으로 못 씁니다. 타임아웃, 결과 개수 제한, 깊이를 명시적으로 펼쳐 쓰기로 대신해야 합니다.

---

## 3. Gremlin — traversal step chaining

Gremlin은 그래프를 **걸어 다니는 것**으로 봅니다. 질의문이 아니라 **이동 지시서**입니다.
문법 모양이 SQL/Cypher 계열과 근본적으로 다릅니다. 점(`.`)으로 이어 붙인 **메서드 체인**입니다.

```
g  .V()  .hasLabel('Company')  .out('signed')  .values('id')
│   │        │                    │               │
│  전부     라벨로               signed 간선을    속성 값을
│  노드     걸러라               따라 나가라      꺼내라
시작점
```

주요 스텝:

| 스텝 | 뜻 | Cypher 대응 |
|---|---|---|
| `g.V()` / `g.E()` | 모든 노드 / 간선에서 출발 | `MATCH (n)` / `MATCH ()-[r]-()` |
| `.hasLabel('Company')` | 라벨 필터 | `(c:Company)` |
| `.has('name','가온테크')` | 속성 필터 | `{name:'가온테크'}` |
| **`.out('signed')`** | 나가는 간선을 따라 **상대 노드**로 | `-[:Signed]->(n)` |
| **`.in('signed')`** | 들어오는 간선을 따라 상대 노드로 | `<-[:Signed]-` |
| `.both('signed')` | 방향 무시 | `-[:Signed]-` |
| `.outE()` / `.inE()` / `.bothE()` | 노드가 아니라 **간선**으로 이동 | `[r:Signed]` 를 변수로 잡기 |
| `.outV()` / `.inV()` / `.otherV()` | 간선에서 다시 노드로 | — |
| `.as('c')` / `.select('c')` | 지금 위치에 이름표를 붙이고 나중에 돌아오기 | 변수 재사용 `(c)` |
| `.where(...)`, `.filter(...)` | 조건 | `WHERE` |
| `.values('name')` | 속성 값 꺼내기 | `RETURN c.name` |
| `.dedup()`, `.order()`, `.limit(10)` | 중복 제거, 정렬, 개수 제한 | `DISTINCT`, `ORDER BY`, `LIMIT` |
| `.repeat(out('parentOf')).times(3)` | 반복 = 가변 길이 경로 | `-[:ParentOf*1..3]->` |

핵심: **`.out()` 은 화살표 하나를 한 걸음으로 소비합니다.** 화살표를 그리는 게 아니라, 화살표를 밟고 지나갑니다.
그리고 `.out()` 이 **간선이 아니라 도착 노드**를 반환한다는 점이 중요합니다. 간선 자체를 보려면 `.outE()` 를 써야 합니다.

체인의 순서가 **곧 실행 순서**입니다. 이게 명령형에 가깝다는 뜻입니다. Cypher/SPARQL은 옵티마이저가 순서를 바꿀 수 있지만, Gremlin은 내가 쓴 순서를 대체로 그대로 갑니다. 그래서 "작은 쪽에서 시작하라"(ex5의 교훈)를 **내가 직접** 지켜야 합니다.

---

## 4. 같은 질문, 세 언어로 나란히

질문: **해지했다가 그 뒤에 다시 계약한 고객은?**
(해지 계약의 `endedOn` 보다 신규 계약의 `startedOn` 이 뒤인 회사)

### Cypher (예제 `ex1_three_languages.py` 실제 코드)

```cypher
MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
WHERE o.endedOn < n.startedOn
RETURN c.name AS 고객
ORDER BY 고객
```

읽기: 두 개의 그림을 그리고, 같은 `c`를 공유시키고, 두 날짜를 비교합니다. 5줄.

### SPARQL (예제 `ex1_three_languages.py` 실제 코드)

```sparql
PREFIX ex: <http://example.org/>
SELECT ?고객 WHERE {
    ?c ex:name ?고객 ; ex:terminated ?o ; ex:signed ?n .
    ?o ex:endedOn   ?end .
    ?n ex:startedOn ?start .
    FILTER(?end < ?start)
} ORDER BY ?고객
```

읽기: 사실을 다섯 줄 늘어놓습니다. `;` 로 주어 `?c` 를 세 번 이어 썼습니다 (펼치면 트리플 3개).
속성 접근이 `c.name` 이 아니라 `?c ex:name ?고객` 이라는 점, 날짜를 비교하려면 먼저 `?end`, `?start` 라는 **변수로 꺼내 와야** 한다는 점이 Cypher와의 차이입니다.

### Gremlin

```groovy
g.V().hasLabel('Company').as('c').
  out('terminated').values('endedOn').as('end').
  select('c').
  out('signed').values('startedOn').as('start').
  where('start', gt('end')).
  select('c').values('name').
  dedup().order()
```

읽기: 회사에 서서 이름표(`as('c')`)를 붙이고 → 해지 계약으로 한 걸음 나가 날짜를 집고 → **원래 자리로 돌아와서**(`select('c')`) → 신규 계약으로 한 걸음 나가 날짜를 집고 → 비교하고 → 다시 회사로 돌아와 이름을 꺼냅니다.
"돌아온다"는 동작이 명시적으로 나타나는 게 걸음의 특징입니다. Cypher는 `(c)` 를 두 번 쓰면 끝인 자리입니다.

> 책 예제에서 Gremlin 부분은 엔진(TinkerPop 서버)이 필요해서, `ex1_three_languages.py` 의 `gremlin_style()` 함수가 파이썬으로 **걸음을 흉내** 냅니다. 주석에 `.hasLabel('Company').out('terminated')`, `.in().out('signed')`, `.where(...)` 를 대응시켜 놨습니다. 문법이 아니라 **사고 방식**이 다르다는 걸 보여 주려는 의도입니다.

### 참고: 같은 뜻의 SQL/PGQ (`ex4_sql_pgq.py`)

```sql
SELECT * FROM GRAPH_TABLE (biz
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
        (c)-[IS Signed]->(n IS Contract)
  WHERE o.ended_on < n.started_on
  COLUMNS (c.name AS 고객)
);
```

SQL/PGQ는 Cypher의 ASCII-art를 거의 그대로 가져오면서 `:` 를 `IS` 키워드로 바꿨습니다. 그림 표기가 사실상의 승자였다는 신호입니다. GQL(ISO/IEC 39075:2024)도 같은 계열입니다.

---

## 5. 세 표기를 한눈에 매핑

| 개념 | Cypher | SPARQL | Gremlin |
|---|---|---|---|
| 노드 | `(c)` | `?c` | 순회의 현재 위치 |
| 라벨/종류 | `(c:Company)` | `?c a ex:Company .` | `.hasLabel('Company')` |
| 관계 | `-[:Signed]->` | `ex:signed` (술어) | `.out('signed')` |
| 정방향 | `->` | 주어→목적어 순서 | `.out()` |
| 역방향 | `<-` | `^ex:signed` 또는 순서 뒤집기 | `.in()` |
| 속성 읽기 | `c.name` | `?c ex:name ?n .` | `.values('name')` |
| 속성 필터 | `{name:'가온'}` / `WHERE` | `FILTER(...)` | `.has('name','가온')` |
| 변수 재사용 | 같은 이름 `(c)` | 같은 변수 `?c` | `.as('c')` + `.select('c')` |
| 가변 길이 (상한 O) | `-[:X*1..3]->` | **표준 문법 없음** | `.repeat(out('x')).times(3)` |
| 가변 길이 (무제한) | `-[:X*]->` | `ex:x+` / `ex:x*` | `.repeat(out('x')).until(...)` |
| 문장 끝 | 절 단위 개행 | `.` (마침표) | `.` (체인 연결) |

> 헷갈리기 쉬운 지점: **점(`.`)의 의미가 세 언어에서 다 다릅니다.**
> Cypher의 `.` 은 속성 접근(`c.name`), SPARQL의 `.` 은 트리플 종료, Gremlin의 `.` 은 스텝 연결입니다.

---

## 6. 왜 이 대비를 외워 둘 만한가

- **면접·설계 회의에서 즉시 쓰입니다.** "Cypher와 SPARQL 중 뭐가 좋냐"는 질문은 취향 문제가 아니라 **그래프를 그림으로 볼지 사실 목록으로 볼지**의 문제입니다. 그림/문장/걸음 세 단어로 답의 축을 잡을 수 있습니다.
- **문법이 아니라 패러다임이 갈립니다.** 앞의 둘은 선언형이라 옵티마이저에 맡기고, Gremlin은 명령형이라 내가 순서를 책임집니다. 선언형의 대가는 "느릴 때 왜 느린지 알려면 실행 계획을 읽어야 한다"입니다(`ex5_read_plan.py`).
- **차이가 가장 크게 벌어지는 건 경로 표현**입니다(11.2절). 한 줄 대비는 시작점이고, 진짜 이식 비용은 가변 길이 경로와 엔진 고유 함수에서 나옵니다.
- **표준이 나왔다 ≠ 표준대로 돈다.** GQL은 2024년 국제 표준인데도 `LET`, `NEXT`, `FILTER` 같은 GQL 전용 절은 엔진들이 아직 안 받습니다(`ex3_gql_dialects.py`가 실패를 결과로 보여 줍니다). 그래서 질의문을 한곳에 모으고, `ORDER BY`를 강제하고, 엔진 고유 함수를 격리하고, 각 질의가 답하는 질문을 주석으로 남기라는 조언이 나옵니다.

---

## 1차 출처

- [Cypher Manual — Patterns](https://neo4j.com/docs/cypher-manual/current/) *(사실상 표준)*
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) — [Property Paths](https://www.w3.org/TR/sparql11-query/#propertypaths) *(표준)*
- [Apache TinkerPop Reference — Traversal Steps](https://tinkerpop.apache.org/docs/current/reference/) *(사실상 표준)*
- [ISO/IEC 39075:2024 (GQL)](https://www.iso.org/standard/76120.html) · [ISO/IEC 9075-16:2023 (SQL/PGQ)](https://www.iso.org/standard/79473.html) *(표준)*
- 확인 시점 2026년 8월 / Kuzu 0.11.3, rdflib 7.5.0
