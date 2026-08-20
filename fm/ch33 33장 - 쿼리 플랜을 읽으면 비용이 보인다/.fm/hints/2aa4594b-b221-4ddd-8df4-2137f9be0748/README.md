# Kuzu EXPLAIN을 아래에서 위로 읽는 이유

**질문** — Kuzu에서 EXPLAIN 결과를 아래에서 위로 읽는 이유는 무엇인가?

**답** — 그것이 실행 순서이기 때문이다. 예제는 연산자를 뽑아 역순으로 이어 붙여 실행 흐름을 보여 준다.

---

## 1. 한 문장으로

플랜은 **트리**다. 트리에서 **리프가 데이터 접근**이고 **루트가 최종 결과**인데, 화면에 그릴 때는 **루트를 위에 놓는** 관례를 쓴다. 그래서 "위가 마지막, 아래가 처음"이 되고, 실행 순서대로 읽으려면 아래에서 위로 올라가야 한다.

즉 두 가지가 겹쳐서 생기는 일이다.

| | 방향 |
|---|---|
| 데이터 흐름 (의미) | 리프 → 루트 |
| 화면 렌더링 (표기) | 루트가 위, 리프가 아래 |
| 따라서 읽는 순서 | **아래 → 위** |

## 2. 연산자 트리의 구조

관계형이든 그래프든 실행 계획은 연산자(operator)들의 트리로 표현된다.

- **리프(leaf)** — 테이블/인덱스에서 실제로 데이터를 꺼내 오는 연산자. Kuzu의 `SCAN_NODE_TABLE`, `SCAN_REL_TABLE`, Neo4j의 `NodeIndexSeek`/`AllNodesScan`, PostgreSQL의 `Seq Scan`/`Index Scan`. 자식이 없다. 여기서만 디스크 히트가 난다.
- **내부 노드** — 자식이 낸 튜플을 받아서 가공한다. `FILTER`, `PROJECTION`, `HASH_JOIN_BUILD`/`HASH_JOIN_PROBE`, `AGGREGATE`, `CROSS_PRODUCT`.
- **루트(root)** — 사용자에게 나갈 최종 결과를 만드는 연산자. Kuzu는 `RESULT_COLLECTOR`, Neo4j는 `ProduceResults`.

리프는 자식이 없으니 **아무것도 기다릴 게 없다**. 그래서 제일 먼저 돈다. 루트는 자기 밑의 모든 것이 끝나야 결과를 낼 수 있다. 그래서 제일 마지막이다. 실행 순서가 트리 구조에 이미 박혀 있는 것이다.

## 3. 볼케이노/풀 모델과 데이터 흐름

고전적인 실행 엔진은 **볼케이노(Volcano) 반복자 모델**이다. 모든 연산자가 `open()` / `next()` / `close()` 인터페이스를 갖고, 부모가 자식의 `next()`를 호출해서 튜플을 하나씩 끌어온다(pull).

여기서 방향이 두 개로 갈린다는 점이 헷갈리기 쉽다.

```
제어 흐름(호출):  루트 → 리프   (부모가 자식의 next()를 부른다)
데이터 흐름(튜플): 리프 → 루트   (튜플은 아래에서 위로 올라간다)
```

플랜을 읽을 때 우리가 따라가는 건 **데이터 흐름**이다. "8,000명을 훑어서 → 마포만 남기고 → 조인해서 → 세었다"는 이야기가 곧 리프→루트 순서다. 그래서 아래에서 위로 읽는다.

Kuzu는 순수 볼케이노 풀 모델이 아니라 **푸시 기반(push-based) 파이프라인** 실행을 쓴다. 소스 연산자가 모설(morsel) 단위로 데이터를 읽어 위로 밀어 올리고, 파이프라인 끝의 싱크(예: `HASH_JOIN_BUILD`, `AGGREGATE`)가 중간 결과를 모은다. 제어 흐름의 방향은 풀 모델과 반대지만, **데이터가 리프에서 루트로 간다는 사실은 똑같다**. 그러니 읽는 규칙도 그대로다.

## 4. 실제 EXPLAIN 출력 (asset 예제 C를 그대로 실행한 것)

`ex1_read_plan.py`의 쿼리 C —

```cypher
MATCH (p:Person {city:'마포'})-[:Member]->(t:Team)
WHERE t.name = '팀7' RETURN count(p)
```

Kuzu 0.11.3의 `EXPLAIN` 출력은 상자 그림 트리다. 폭이 넓어 반복 필드(`NumOutputTuples`, `ExecutionTime`)를 줄이고 뼈대만 옮기면 이렇게 생겼다.

```
┌───────────────────────────────┐
│     RESULT_COLLECTOR[13]      │   ← 루트. 최종 결과. 제일 마지막
│   Expressions: COUNT(p._ID)   │
└───────────────┬───────────────┘
┌───────────────┴───────────────┐
│        PROJECTION[12]         │
└───────────────┬───────────────┘
┌───────────────┴───────────────┐
│      AGGREGATE_SCAN[11]       │
└───────────────┬───────────────┘
┌───────────────┴───────────────┐
│    AGGREGATE_FINALIZE[10]     │
└───────────────┬───────────────┘
┌───────────────┴───────────────┐
│         AGGREGATE[9]          │
└───────────────┬───────────────┘
┌───────────────┴───────────────┐
│         PROJECTION[8]         │
└───────────────┬───────────────┘
┌───────────────┴───────────────┐
│      HASH_JOIN_PROBE[7]       │──────────────────┐
│          Keys: t._ID          │                  │
└───────────────┬───────────────┘                  │
┌───────────────┴───────────────┐  ┌───────────────┴───────────────┐
│       SCAN_REL_TABLE[2]       │  │      HASH_JOIN_BUILD[6]       │
│        Tables: Member         │  │          Keys: t._ID          │
│    Direction: (p)-[]->(t)     │  └───────────────┬───────────────┘
└───────────────┬───────────────┘  ┌───────────────┴───────────────┐
┌───────────────┴───────────────┐  │         PROJECTION[5]         │
│           FILTER[1]           │  └───────────────┬───────────────┘
│        EQUALS(p.city)         │  ┌───────────────┴───────────────┐
└───────────────┬───────────────┘  │           FILTER[4]           │
┌───────────────┴───────────────┐  │        EQUALS(t.name)         │
│      SCAN_NODE_TABLE[0]       │  └───────────────┬───────────────┘
│        Tables: Person         │  ┌───────────────┴───────────────┐
│           Alias: p            │  │      SCAN_NODE_TABLE[3]       │
│      Properties: p.city       │  │         Tables: Team          │
└───────────────────────────────┘  │           Alias: t            │
        ↑ 리프. 제일 먼저          │      Properties: t.name       │
                                   └───────────────────────────────┘
                                            ↑ 리프. 제일 먼저
```

읽어 보면 이야기가 된다.

1. `SCAN_NODE_TABLE[3]` — Team을 훑는다 → `FILTER[4]` `t.name = '팀7'`
2. `SCAN_NODE_TABLE[0]` — Person을 훑는다 → `FILTER[1]` `p.city = '마포'`
3. `HASH_JOIN_BUILD[6]` — 걸러진 팀으로 해시 테이블을 만든다
4. `SCAN_REL_TABLE[2]` — 마포 사람들의 `Member` 엣지를 따라간다
5. `HASH_JOIN_PROBE[7]` — 엣지의 반대편 `t._ID`로 해시 테이블을 찔러 본다
6. `AGGREGATE[9]` → `RESULT_COLLECTOR[13]` — 세고, 내보낸다

### 덤으로 얻는 증거: 대괄호 안의 번호

연산자 이름 뒤 `[숫자]`는 연산자 ID다. 위 플랜에서 **리프가 0과 3, 루트가 13**이다. 번호가 **아래에서 위로 커진다**. 플래너가 트리를 리프부터 물리 연산자로 매핑하며 번호를 붙이기 때문이다. "아래가 먼저"라는 규칙을 눈으로 확인할 수 있는 자리다.

## 5. 예제가 실행 흐름을 보여 주는 방법 — 역순 이어 붙이기

`ex1_read_plan.py`는 상자 그림이 너무 넓어서, 연산자 이름만 정규식으로 뽑고 **뒤집어서** 화살표로 잇는다.

```python
r = c.execute("EXPLAIN " + QUERIES[name])
text = ""
while r.has_next():
    text += str(r.get_next()[0])
ops = re.findall(r"([A-Z_]{4,})\[\d+\]", text)
# 아래에서 위로 읽는 것이 실행 순서다
print(f"[{name}]")
print("    " + "  →  ".join(reversed(ops)))
```

핵심이 `reversed(ops)` 한 곳에 들어 있다. `re.findall`은 출력 텍스트를 **위에서 아래로** 훑으므로 `ops`는 루트→리프 순서로 담긴다. 그걸 뒤집으면 리프→루트, 즉 실행 순서가 된다. 정규식 `([A-Z_]{4,})\[\d+\]`가 노리는 것이 바로 위에서 본 `SCAN_NODE_TABLE[0]` 같은 표기다.

실제로 돌리면 세 쿼리가 이렇게 나온다(Kuzu 0.11.3, 사람 8,000명·팀 80개).

```
[B. 팀에서 시작]
    SCAN_NODE_TABLE → FILTER → SCAN_NODE_TABLE → SCAN_REL_TABLE → FILTER
    → SCAN_NODE_TABLE → SEMI_MASKER → PROJECTION → RESULT_COLLECTOR
    → HASH_JOIN_BUILD → TABLE_FUNCTION_CALL → HASH_JOIN_PROBE → PROJECTION
    → AGGREGATE → AGGREGATE_FINALIZE → AGGREGATE_SCAN → PROJECTION → RESULT_COLLECTOR

[C. 사람에서 시작]
    SCAN_NODE_TABLE → FILTER → SCAN_NODE_TABLE → PROJECTION → FILTER
    → HASH_JOIN_BUILD → SCAN_REL_TABLE → HASH_JOIN_PROBE → PROJECTION
    → AGGREGATE → AGGREGATE_FINALIZE → AGGREGATE_SCAN → PROJECTION → RESULT_COLLECTOR

[A. 두 끝을 따로 찾음]
    SCAN_NODE_TABLE → FILTER → SCAN_NODE_TABLE → RESULT_COLLECTOR → FILTER
    → CROSS_PRODUCT → SCAN_NODE_TABLE → TABLE_FUNCTION_CALL → SCAN_NODE_TABLE
    → SEMI_MASKER → SCAN_REL_TABLE → FLATTEN → RESULT_COLLECTOR
    → HASH_JOIN_BUILD → FLATTEN → HASH_JOIN_PROBE → FILTER → PROJECTION
    → AGGREGATE → AGGREGATE_FINALIZE → AGGREGATE_SCAN → PROJECTION → RESULT_COLLECTOR
```

이렇게 한 줄로 펴 놓으면 33.1절이 말하는 세 가지를 바로 볼 수 있다.

1. **`CROSS_PRODUCT`가 있나** — A에만 있다. 사람 8,000 × 팀 80을 만들고 거기서 거른다. A가 B·C보다 3.4배 느린 이유가 이 한 단어다.
2. **`SCAN`이 무엇을 훑나** — `SCAN_NODE_TABLE`의 `Tables:`/`Properties:` 줄을 본다.
3. **`FILTER`가 `SCAN` 앞인가 뒤인가** — 실행 순서 기준으로 뒤면 "다 훑고 나서 버리는" 것이다. C에서는 `SCAN_NODE_TABLE[0] → FILTER[1]`로 스캔 직후에 붙어 있어 위로 올라가는 튜플이 일찍 줄어든다.

세 가지 전부 **아래에서 위로 읽어야** 판단이 선다. 위에서 아래로 읽으면 "결과를 모으고, 세고, 조인했다"는 역순 서술이 되어 무엇이 무엇을 먹였는지가 안 보인다.

## 6. 주의 — 트리를 한 줄로 펴는 건 근사다

예제의 `reversed(ops)`는 **읽기 쉬우라고 하는 단순화**지 정확한 실행 타임라인은 아니다.

- 플랜은 트리라 가지가 둘 이상이면(해시 조인의 build 쪽 / probe 쪽) 진짜 순서는 하나로 정해지지 않는다. Kuzu는 파이프라인 단위로 병렬 실행하기도 한다.
- 상자 그림에서 형제 연산자는 **같은 줄에 좌우로** 놓이는데, 텍스트를 훑으면 좌→우로 읽히므로 두 가지가 섞인다. 실제로 C의 결과에서 `PROJECTION[5]`(Team 쪽)가 `FILTER[1]`(Person 쪽)보다 앞에 나온다.
- 중간에 `RESULT_COLLECTOR`가 또 보이면 그건 최종 출력이 아니라 서브플랜의 싱크다(A의 `EXISTS { ... }` 서브쿼리).

정확히 보고 싶으면 상자 그림 원문과 `[번호]`를 보면 된다. 한 줄 요약은 "무슨 연산자가 있고 대충 어떤 순서로 도는가"를 빠르게 훑는 용도다.

## 7. 다른 엔진의 표기와 비교

**아래에서 위로 읽는다는 규칙 자체는 거의 모든 엔진이 같다.** 다른 건 그리는 방법이다.

| 엔진 | 표기 | 루트 | 리프 |
|---|---|---|---|
| **Kuzu** | 유니코드 상자 트리 (`┌─┴─┐`), 연산자마다 `NumOutputTuples`·`ExecutionTime` 칸 | `RESULT_COLLECTOR` (맨 위) | `SCAN_NODE_TABLE` / `SCAN_REL_TABLE` (맨 아래) |
| **Neo4j** | ASCII 표. 한 행이 한 연산자, `Details`·`Estimated Rows`·`DB Hits` 열 | `ProduceResults` (첫 행) | `NodeIndexSeek`, `AllNodesScan` 등 (마지막 행) |
| **PostgreSQL** | 들여쓰기 목록 (`->` 접두사). 더 깊이 들여쓴 것이 자식 | 맨 윗줄 (`Aggregate`, `Limit` 등) | 가장 깊이 들여쓴 `Seq Scan`/`Index Scan` |

Neo4j 문서도 같은 말을 한다 — 플랜은 아래에서 위로 읽어야 하고, 리프 연산자에서 시작해 한 단계씩 올라가 루트 `ProduceResults`에 도달하며, 리프가 낸 행이 부모로 파이프된다.

작은 차이들:

- **Neo4j**는 브라우저에서 같은 플랜을 그래픽 트리로도 그리는데, 이때도 루트가 위다. `EXPLAIN`은 추정치만, `PROFILE`은 실측 행 수·DB 히트를 준다. Kuzu는 `EXPLAIN`에도 `NumOutputTuples`·`ExecutionTime` 칸이 있지만 `EXPLAIN`만 돌리면 0으로 찍힌다(실제 실행을 안 하므로). 위 출력에서 전부 `0`인 이유다.
- **PostgreSQL**은 상자나 표 대신 들여쓰기를 쓴다. "아래에서 위"라기보다 "**안쪽에서 바깥쪽으로**"가 더 정확한 표현이고, 결과적으로 같은 규칙이다.
- 연산자 어휘도 다르다. Kuzu의 `CROSS_PRODUCT`에 대응하는 것이 Neo4j의 `CartesianProduct`, PostgreSQL의 `Nested Loop`(조인 조건 없는 경우)다. 이름은 달라도 **플랜에서 제일 먼저 찾을 단어**라는 점은 같다.

## 8. 정리

- 플랜은 트리고, 리프가 데이터 접근, 루트가 최종 결과다. 실행은 리프에서 시작해 루트에서 끝난다.
- 트리를 그릴 때 루트를 위에 놓는 관례 때문에 **실행 순서가 화면에서 거꾸로** 보인다. 그래서 아래에서 위로 읽는다.
- 볼케이노 풀 모델이든 Kuzu의 푸시 기반 파이프라인이든, 제어 흐름 방향과 무관하게 **데이터는 리프→루트**로 흐른다.
- `ex1_read_plan.py`는 `re.findall`로 연산자 이름을 뽑고 `reversed(ops)`로 뒤집어, 이 규칙을 한 줄짜리 실행 흐름으로 보여 준다.
- 이렇게 펴 놓아야 33.1절의 세 가지 — `CROSS_PRODUCT` 유무, `SCAN`이 훑는 대상, `FILTER`의 위치 — 를 순서대로 판단할 수 있다.
- Neo4j·PostgreSQL도 읽는 방향은 같다. 다른 건 상자/표/들여쓰기라는 표기와 연산자 이름뿐이다.

## 참고

- [Understanding query plans — Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/)
- [Planning and tuning (EXPLAIN / PROFILE) — Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/)
- [Kùzu: A Graph DBMS for Predefined Joins (CIDR 2023)](https://www.cidrdb.org/cidr2023/papers/p48-jin.pdf) — 파이프라인·푸시 기반 실행 모델
- [Kuzu — Execution (Database internals)](https://docs.kuzudb.com/developer-guide/database-internal/execution/)
- [Reading EXPLAIN plans — Apache DataFusion](https://datafusion.apache.org/user-guide/explain-usage.html) — 다른 엔진에서도 같은 "아래에서 위로" 규칙
- [Reading PostgreSQL EXPLAIN output](https://medium.com/@philmcc/reading-postgresql-explain-and-explain-analyze-output-1b927ad6a192)
