# Kuzu와 Neo4j 5.x의 큰 차이 — 스키마를 미리 못 박느냐

> **Q.** Kuzu와 Neo4j 5.x의 큰 차이는 무엇인가?
>
> **A.** Kuzu는 `CREATE NODE TABLE`/`CREATE REL TABLE`로 스키마를 미리 못 박아야 하고, Neo4j는 라벨을 쓰면 그 자리에서 생긴다. 스키마 강제 여부는 12장에서 다시 다룬다.

둘 다 프로퍼티 그래프이고, 둘 다 Cypher 계열 문장을 씁니다. 그래서 "문법이 조금 다르다" 정도로 넘기기 쉽지만, 실제로 갈리는 것은 문법이 아니라 **틀린 데이터가 언제 튕겨 나오는가**입니다. Kuzu는 적재 시점에 튕기고, Neo4j는 대체로 튕기지 않습니다. 이 한 줄이 저장 레이아웃, 질의 계획, 그리고 밤 12시에 무엇을 디버깅하게 되는지까지 결정합니다.

---

## 1. 코드로 보는 차이

5장 예제 `code/ex3_cypher_vs_sparql.py`가 이 차이를 주석까지 붙여 그대로 보여 줍니다. 같은 질문("해지했다가 그 뒤에 다시 계약한 고객은?")을 Cypher와 SPARQL로 푸는 예제인데, Cypher 쪽을 서버 없이 돌리려고 임베디드 엔진 **Kuzu 0.11.3**을 씁니다.

```python
CYPHER_SCHEMA = [
    "CREATE NODE TABLE Company(name STRING, grade STRING, PRIMARY KEY(name))",
    "CREATE NODE TABLE Contract(id STRING, startedOn DATE, endedOn DATE, PRIMARY KEY(id))",
    "CREATE REL TABLE Signed(FROM Company TO Contract, at DATE)",
    "CREATE REL TABLE Terminated(FROM Company TO Contract, at DATE)",
    # Neo4j 5.x 에는 이 스키마 선언이 없다. 라벨을 쓰면 그 자리에서 생긴다.
    # 스키마를 미리 못 박느냐가 두 엔진의 큰 차이다. 12장에서 다시 본다.
]
```

그리고 데이터를 넣는 문장은 Neo4j에서도 거의 그대로 돕니다.

```python
CYPHER_DATA = [
    "CREATE (:Company {name:'가온테크', grade:'A'})",
    ...
    "MATCH (a:Company {name:'가온테크'}), (b:Contract {id:'C-2025-118'}) "
    "CREATE (a)-[:Signed {at: date('2025-06-02')}]->(b)",
]
```

즉 **`CYPHER_DATA`는 두 엔진이 공유하고, `CYPHER_SCHEMA` 네 줄만 Kuzu에만 필요합니다.** Neo4j에 이 네 줄을 넣으면 문법 오류입니다(`CREATE NODE TABLE`이라는 구문 자체가 없음). Kuzu에서 이 네 줄을 빼면 `CYPHER_DATA` 첫 줄부터 실패합니다 — `Company`라는 테이블이 없으니까요.

실행 순서도 강제됩니다. `CREATE REL TABLE Signed(FROM Company TO Contract, ...)`는 `Company`와 `Contract` 노드 테이블이 **이미 존재해야** 만들어집니다. 그래서 예제도 `CYPHER_SCHEMA + CYPHER_DATA` 순서로 리스트를 이어 붙여 실행합니다.

```python
for stmt in CYPHER_SCHEMA + CYPHER_DATA:
    conn.execute(stmt)
```

---

## 2. Kuzu의 DDL이 실제로 못 박는 네 가지

`CREATE NODE TABLE` / `CREATE REL TABLE` 한 줄은 생각보다 많은 것을 확정합니다.

| 못 박는 것 | 예제에서 | 어기면 |
|---|---|---|
| **테이블(라벨)의 존재** | `Company`, `Contract`, `Signed`, `Terminated` 넷뿐 | 선언 안 한 라벨을 쓰면 바인더 오류 |
| **속성 이름과 타입** | `grade STRING`, `at DATE`, `startedOn DATE` | 없는 속성 이름 → 오류. 타입 안 맞는 값 → 변환 오류 |
| **기본키** | `PRIMARY KEY(name)`, `PRIMARY KEY(id)` | 중복 키 삽입 실패. 조회용 해시 인덱스의 근거이기도 함 |
| **엣지의 양 끝 타입** | `Signed(FROM Company TO Contract)` | `Person -[:Signed]-> Contract`나 방향이 뒤집힌 엣지는 거부 |

마지막 줄이 특히 Neo4j와 크게 다릅니다. Neo4j에서 `(:Contract)-[:SIGNED]->(:Company)`처럼 방향을 뒤집어 넣어도 아무 일이 없습니다. Kuzu에서는 그 조합이 선언된 `FROM ... TO ...` 짝에 없으면 들어가지 않습니다. (여러 짝이 필요하면 `CREATE REL TABLE R(FROM A TO B, FROM C TO B, ...)`처럼 짝을 나열합니다. 옛 `CREATE REL TABLE GROUP` 문법이 하던 역할을 흡수했습니다.)

한 가지 더, 예제 데이터를 잘 보면 재미있는 비대칭이 있습니다.

```python
"CREATE (:Contract {id:'M-2021-077', endedOn: date('2024-03-11')})",   # startedOn 없음
"CREATE (:Contract {id:'C-2025-118', startedOn: date('2025-06-02')})", # endedOn 없음
```

**선언된 컬럼을 비워 두는 것은 됩니다**(NULL). **선언 안 된 컬럼을 새로 얹는 것은 안 됩니다.** 즉 Kuzu의 강제는 "모든 값을 채워라"가 아니라 "허용된 칸 밖으로 나가지 말라"입니다. 이 구분은 컬럼 저장 설계에서 곧바로 따라 나옵니다(§4).

스키마를 바꿔야 하면 `ALTER TABLE ... ADD/DROP/RENAME`으로 마이그레이션합니다. 명시적인 절차가 하나 더 생기는 대가입니다.

---

## 3. Neo4j 5.x — 라벨은 쓰면 생긴다, 그리고 스키마는 나중에 덧붙인다

Neo4j는 공식적으로 **schema-optional**입니다. 라벨과 관계 타입, 속성 키는 사전 정의 대상이 아니고, `CREATE (:Company {grade:'A'})`를 실행하면 그 순간 `Company` 라벨과 `grade` 속성 키가 카탈로그에 등록됩니다. 별도의 DDL이 없습니다.

대신 필요할 때 **제약과 인덱스를 덧붙여** 스키마의 일부를 되찾습니다.

| 도구 | 하는 일 | 에디션 |
|---|---|---|
| 속성 유일성 제약 (property uniqueness) | 특정 라벨의 속성 조합이 유일함을 보장 | 전 에디션 |
| 속성 존재 제약 (property existence) | 특정 라벨에 그 속성이 반드시 있음 | Enterprise |
| 속성 타입 제약 (property type) | 특정 속성의 타입 고정 | Enterprise |
| 키 제약 (key constraint) | 존재 + 유일 동시 보장 | Enterprise |
| 인덱스 | 조회 성능 (스키마 강제 아님) | 전 에디션 |

여기서 실무적으로 중요한 점 두 개.

1. **Kuzu의 DDL과 Neo4j 제약은 커버리지가 다릅니다.** Neo4j 제약은 "이 라벨을 가진 노드"에 대해서만 걸립니다. `Company` 라벨에 제약을 걸어도, 오타로 만들어진 `Compnay` 라벨 노드에는 아무 제약이 없습니다. **제약은 라벨 오타를 막지 못합니다** — 오타 라벨은 제약이 걸려 있지 않은 새 라벨이니까요. Kuzu는 라벨 자체가 화이트리스트라 이 문제가 구조적으로 발생하지 않습니다.
2. **엣지 양 끝 타입을 강제하는 제약이 없습니다.** `Signed` 관계가 `Company → Contract`만 되게 만드는 선언적 수단이 Neo4j 5.x에는 없습니다(GraphQL 라이브러리나 애플리케이션 레이어에서 막아야 합니다). Kuzu는 `CREATE REL TABLE`의 `FROM ... TO ...`가 그걸 그냥 합니다.

---

## 4. 왜 Kuzu는 스키마를 요구할 수밖에 없나 — 임베디드·컬럼 저장·벡터화의 맞물림

"엄격한 게 좋은 설계라서" 스키마를 요구하는 게 아닙니다. Kuzu가 고른 세 가지 설계 선택이 **스키마 없이는 성립하지 않습니다.**

### (a) 컬럼 저장 — 컬럼 하나에 물리 타입이 하나여야 한다

Kuzu는 노드 속성을 **노드 그룹(node group)** 단위로 쪼개서 컬럼별로 디스크에 씁니다. `Contract` 테이블의 `startedOn DATE` 컬럼은 고정 폭 값이 줄줄이 붙은 배열 + NULL 비트맵으로 저장됩니다. 여기서 두 가지가 따라 나옵니다.

- **타입 선언이 필수입니다.** 컬럼을 만들려면 값 하나가 몇 바이트인지, 압축을 무엇으로 걸지가 쓰기 전에 결정돼야 합니다. `DATE`인지 `STRING`인지 모르는 컬럼은 물리적으로 배치할 수 없습니다.
- **NULL은 싸고, 새 속성은 비쌉니다.** 그래서 §2에서 본 비대칭이 나옵니다. `startedOn`을 비워 두는 것은 비트맵에 0을 하나 찍는 일이라 공짜에 가깝지만, 선언 안 된 속성을 얹으려면 컬럼 파일을 새로 만드는 스키마 변경(= `ALTER TABLE`)이어야 합니다.
- 반대로 Neo4j는 속성을 **타입 태그가 붙은 레코드의 연결 리스트**로 노드마다 따로 들고 있습니다. 노드마다 속성 집합이 달라도 상관없는 대신, 스무 개 속성 중 두 개만 필요한 질의에서도 그 노드의 속성 체인을 따라가야 합니다. Kuzu는 컬럼 두 개만 읽습니다. **스키마 강제는 그 "컬럼 두 개만"을 가능하게 하는 값입니다.**

### (b) 벡터화 실행 — 타입 판정을 바인딩 시점에 끝내야 한다

Kuzu는 값을 한 개씩이 아니라 벡터(수천 개 묶음) 단위로 처리하는 벡터화 실행기를 씁니다. `WHERE t.at < s.at`을 도는 루프가 빠른 이유는, 그 루프가 "DATE와 DATE를 비교하는 전용 커널"로 **컴파일 시점에 이미 확정**돼 있기 때문입니다.

스키마가 없으면 이 루프 안에서 값마다 태그를 읽고 "이번엔 뭐랑 뭘 비교하지?"를 분기해야 합니다. 벡터화의 이득이 그 분기에서 대부분 사라집니다. 그래서 Kuzu의 바인더는 질의를 계획하기 **전에** 카탈로그를 보고 `t.at`이 존재하는지, 타입이 무엇인지 확정합니다. 이게 §5의 "질의 시점에 오타가 오류로 잡히는" 이유입니다.

### (c) CSR 인접 구조와 질의 계획 — `FROM ... TO ...`가 필요한 이유

Kuzu는 관계를 CSR(compressed sparse row) 형태의 인접 구조로 저장합니다. "이 노드의 이웃 전부"가 포인터 추적이 아니라 **연속 구간 스캔**이 되는 배치입니다. 그러려면 노드가 조밀한 내부 오프셋 공간에 놓여야 하고, 그 오프셋 공간은 **노드 테이블 단위**로 정의됩니다.

`CREATE REL TABLE Signed(FROM Company TO Contract, at DATE)`는 그래서 단순한 무결성 규칙이 아니라 **저장 구조의 주소 지정 방식 선언**입니다. `Signed`의 CSR은 "Company 오프셋 → Contract 오프셋들"을 담는 구조로 만들어집니다. 양 끝 테이블을 모른 채로는 이 배열을 배치할 방법이 없습니다.

질의 계획 쪽으로도 이득이 옵니다.

- `MATCH (c:Company)-[t:Terminated]->(:Contract)`를 계획할 때, 스캔 대상 테이블이 **정적으로** 정해집니다. "이 노드가 정말 Company인가"를 실행 중에 라벨 필터로 확인하는 단계가 아예 없습니다.
- 카탈로그가 테이블별 카디널리티와 컬럼 통계를 갖고 있으니, 예제 질의처럼 조인이 두 개 이상 얽힐 때 조인 순서를 고를 근거가 생깁니다. 스키마 없는 엔진은 "라벨별 노드 수" 수준의 거친 추정에 머물기 쉽습니다.

### (d) 임베디드라는 조건이 이 셋을 한 방향으로 밀어붙인다

Kuzu는 서버가 아니라 **프로세스 안에 들어가는 라이브러리**입니다(그래서 예제가 `pip install kuzu` 한 줄로 Cypher를 돌립니다). 임베디드 분석 엔진의 목표는 "DuckDB가 SQL에서 하는 일을 그래프에서 하기"에 가깝습니다 — 한 프로세스 안에서 큰 스캔과 다중 조인을 CPU 한계까지 밀어붙이기. 이 목표에서는 컬럼 저장 + 벡터화 + 정적 계획이 사실상 한 묶음이고, 그 묶음의 입장료가 DDL입니다.

Neo4j의 목표는 다르고, 따라서 대가도 다릅니다. 서버로 떠서 여러 팀이 계속 모델을 바꿔 가며 붙는 상황, OLTP성 짧은 트랜잭션과 이웃 탐색이 섞이는 상황에서는 "라벨을 쓰면 생긴다"가 개발 속도로 곧바로 돌아옵니다. **표현력의 우열이 아니라 최적화하려는 것이 다른 겁니다.** 5장이 반복하는 "모델은 표현력이 아니라 상황으로 고른다"가 엔진 층에서도 같은 모양으로 나옵니다.

---

## 5. 실수가 어느 단계에서 잡히는가

같은 실수를 두 엔진에 넣으면 발각 시점이 이렇게 갈립니다.

| 실수 | Kuzu | Neo4j 5.x |
|---|---|---|
| 라벨 오타 — `CREATE (:Compnay {...})` | **적재 시점 오류.** 그런 테이블 없음 | **조용히 성공.** `Compnay` 라벨이 새로 생김 |
| 라벨 오타 — `MATCH (c:Compnay)` | **질의 바인딩 시점 오류** | 결과 0행 + 경고 알림(`UnknownLabelWarning`). 드라이버가 안 찍으면 안 보임 |
| 속성 이름 오타 — `RETURN c.gradee` | **질의 바인딩 시점 오류.** 없는 컬럼 | **`null` 반환.** 오류 아님 |
| 속성 오타로 쓰기 — `SET c.gradee = 'A'` | **오류** | **조용히 성공.** 새 속성 키 등록 |
| 타입 불일치 — `grade`에 숫자 | **적재 시점 변환 오류** | **저장됨.** 같은 속성에 STRING과 INTEGER가 섞임 |
| 엣지 방향 뒤집힘 — `(:Contract)-[:Signed]->(:Company)` | **적재 시점 오류.** `FROM/TO` 짝 위반 | **조용히 성공** |
| 엣지 양 끝 타입 오류 — `(:Person)-[:Signed]->(:Contract)` | **적재 시점 오류** | **조용히 성공** |
| 중복 기본키 | **오류** (PK) | 유일성 제약을 미리 걸어 뒀다면 오류, 안 걸었으면 **중복 노드 생성** |
| 필수 속성 누락 | 허용(NULL) — 이건 Kuzu도 안 막음 | 존재 제약(Enterprise)을 걸어 뒀다면 오류, 아니면 허용 |

읽는 방식은 이렇습니다.

- **Kuzu에서 실패는 시끄럽고 이릅니다.** `conn.execute(stmt)`가 예외를 던지고, 스택 트레이스가 문제의 문장을 가리킵니다. 대가는 유연성입니다. 형태가 들쭉날쭉한 외부 데이터를 일단 부어 놓고 나중에 정리하는 작업이 불편합니다. 스키마를 먼저 알아야 하고, 알게 될 때마다 마이그레이션해야 합니다.
- **Neo4j에서 실패는 조용하고 늦습니다.** 적재는 다 성공했고, 오류 로그도 깨끗합니다. 문제는 나중에 **"결과가 0행"** 또는 **"숫자가 이상함"** 으로 나타납니다. 그때 원인은 두 달 전에 들어간 데이터에 있고, 그래프 어딘가에 오타 라벨을 가진 노드 8만 개가 조용히 앉아 있습니다.
- 그리고 이건 Kuzu도 안 막아 준다는 점을 놓치지 마세요. **DDL은 값의 존재나 의미를 검증하지 않습니다.** `grade`가 `'A'`/`'B'`/`'C'` 중 하나여야 한다거나, 계약 시작일이 종료일보다 앞서야 한다는 것 같은 도메인 규칙은 두 엔진 모두 애플리케이션 몫입니다. 스키마 강제는 **구조**를 잡아 주고, 값의 옳음은 잡아 주지 않습니다.

---

## 6. 오타 라벨 함정을 조금 더 자세히

Neo4j에서 가장 자주 사람을 물어뜯는 지점이라 따로 씁니다. 핵심은 **읽을 때와 쓸 때의 비대칭**입니다.

```cypher
// (1) 읽기 — 경고는 나온다
MATCH (c:Compnay) RETURN count(c)
// → 0
// → Neo.ClientNotification.Statement.UnknownLabelWarning
//   "The provided label is not in the database."
```

`MATCH`에서 데이터베이스에 없는 라벨을 쓰면 Neo4j는 알림을 붙여 줍니다. 문제는 (a) **오류가 아니라 알림**이라서 결과는 정상적으로 0행이고, (b) 대부분의 드라이버·ORM·BI 도구가 이 알림을 사용자에게 보여 주지 않고, (c) 애초에 이런 알림은 스크립트 로그에 묻힌다는 겁니다.

```cypher
// (2) 쓰기 — 경고조차 없다
CREATE (:Compnay {name:'가온테크', grade:'A'})
// → 성공. 이제 Compnay 라벨이 "데이터베이스에 있는 라벨"이 되었다.
```

여기서 두 번 무너집니다.

1. 오타 노드가 만들어집니다.
2. **그 순간부터 (1)의 경고도 사라집니다.** `Compnay`는 이제 실재하는 라벨이니까요. 유일한 자동 방어선이 첫 오타로 스스로 꺼집니다.

증상은 이렇게 나타납니다. `MATCH (c:Company)-[:Signed]->(:Contract) RETURN count(*)`가 어제보다 줄어 있습니다. 오류는 없습니다. 파이프라인 한 곳이 `Compnay`로 쓰고 있을 뿐입니다. 관계 타입도 똑같습니다 — `[:SIGNED]`와 `[:Signed]`는 **다른 관계 타입**이고, Neo4j는 둘 다 만들어 줍니다. 이 두 파이프라인이 만든 그래프는 서로를 못 봅니다.

실무 방어책:

- **주기적으로 카탈로그를 눈으로 봅니다.** `CALL db.labels()`, `CALL db.relationshipTypes()`, `CALL db.propertyKeys()`. 오타는 목록에서 튀어 보입니다. 라벨 목록에 `Company`와 `Compnay`가 같이 있는데 후자의 노드가 12개면, 그게 답입니다.
- **라벨/타입/속성 키를 코드에 리터럴로 흘리지 않습니다.** 상수, enum, 또는 코드 생성으로 한 군데 모읍니다. 문자열이 코드 열 곳에 흩어져 있으면 오타는 시간 문제입니다. (5장 제목이 "문자열이 아니라 사물"인 게 여기서도 한 번 더 걸립니다. 라벨을 문자열로 다루면 라벨도 문자열의 함정을 그대로 물려받습니다.)
- **적재 후 검증 질의를 CI에 넣습니다.** 예상 라벨 목록과 실제 목록을 비교하고, 예상 밖 라벨이 있으면 실패시킵니다. 즉 **Kuzu가 DDL로 공짜로 하는 일을 손으로 만들어 붙이는 셈**입니다.
- 걸 수 있는 제약(유일성, 그리고 Enterprise면 존재·타입·키)은 **적재 전에** 걸어 둡니다. 나중에 걸면 이미 위반한 데이터 때문에 생성 자체가 실패해서, 데이터를 먼저 청소해야 합니다.
- 프로토타입에서 운영으로 넘어가는 시점을 스키마를 확정하는 관문으로 씁니다. "라벨을 쓰면 생긴다"는 탐색기에는 선물이고 운영에는 부채입니다.

---

## 7. GQL 표준에서 보면 둘 다 정상 시민이다

한쪽이 표준을 어기는 게 아니라는 점이 중요합니다. **ISO/IEC 39075:2024 (GQL)** 은 그래프의 내용이 제약 없이 열려 있을 수도 있고, 관리자가 정의한 **그래프 타입(graph type)** 으로 규정될 수도 있다고 명시합니다. 그래프 타입이 붙어 내용이 그 안으로 닫힌 그래프를 *closed*(고정 스키마) 그래프라 부르고, 그렇지 않은 쪽이 *open* 그래프입니다. 고정 스키마 그래프는 그래프 타입에 선언된 노드 타입·엣지 타입만 담을 수 있습니다.

이 틀에 얹어 보면 배치가 깔끔해집니다.

- **Kuzu ≈ closed / 고정 스키마.** `CREATE NODE TABLE`/`CREATE REL TABLE`이 그래프 타입 선언 역할을 합니다.
- **Neo4j 5.x ≈ open.** 제약과 인덱스로 부분적인 규정을 얹을 수 있습니다.

그래서 이건 "표준을 따르는 쪽 vs 안 따르는 쪽"이 아니라 **표준이 이름을 붙여 둔 스펙트럼의 양 끝**입니다. 참고로 RDF 쪽도 같은 스펙트럼을 갖고 있습니다 — 트리플 자체는 open이고, SHACL/ShEx로 나중에 형태를 규정합니다. 검증을 저장 시점에 강제하느냐 나중에 얹느냐는 모델을 가로지르는 축입니다.

---

## 8. 그래서 무엇을 고를 것인가

| 상황 | 유리한 쪽 |
|---|---|
| 형태를 아직 모르는 데이터를 탐색 중 | Neo4j (open) |
| 모델이 매주 바뀌는 프로토타입 | Neo4j (open) |
| 여러 팀이 같은 그래프에 계속 쓰기 | Kuzu 쪽 강제, 또는 Neo4j + 제약/CI 검증 |
| 배치 분석, 큰 스캔과 다중 조인 | Kuzu (컬럼 저장 + 벡터화) |
| 서버 없이 노트북·CI·파이프라인 안에서 | Kuzu (임베디드) |
| 운영 시스템의 데이터 품질이 걸린 곳 | 스키마 강제 있는 쪽 |

흔한 실전 조합은 둘 중 하나를 고르는 게 아닙니다. **탐색은 스키마 없는 쪽에서 하고, 형태가 굳으면 스키마로 못 박아 운영으로 넘깁니다.** Neo4j만 쓰더라도 그 "못 박기"는 필요합니다 — 제약을 걸고, 라벨 상수를 코드 한 군데 모으고, 카탈로그 검증을 CI에 넣는 것이 Kuzu의 DDL 네 줄에 해당하는 일입니다.

그리고 5장이 반복해서 권하는 방법이 이 층에서도 그대로 통합니다. **고르기 전에 질의 다섯 개를 두 쪽으로 써 보는 반나절이 4개월을 아낍니다.** 예제 `ex3_cypher_vs_sparql.py`가 실제로 하는 일이 그겁니다.

스키마 강제 여부가 다시 정면으로 다뤄지는 것은 **12장**입니다.

---

## 9. 짧게 확인하기

- Neo4j 5.x에 `CREATE NODE TABLE`이 있나? → **없습니다.** 문법 오류입니다.
- Kuzu에서 `CREATE REL TABLE Signed(FROM Company TO Contract, at DATE)`를 노드 테이블보다 먼저 실행할 수 있나? → **없습니다.** 양 끝 테이블이 먼저 있어야 합니다.
- Kuzu에서 선언된 속성을 비워 두는 건? → **됩니다**(NULL). 선언 안 된 속성을 얹는 건 **안 됩니다.**
- Neo4j에서 유일성 제약이 라벨 오타를 막아 주나? → **아니요.** 오타 라벨은 제약이 안 걸린 새 라벨입니다.
- Kuzu가 스키마를 요구하는 근본 이유? → 컬럼 저장의 물리 타입, 벡터화 커널의 컴파일 시점 타입 확정, CSR 인접 구조의 노드 테이블 오프셋 공간. 셋 다 선언 없이는 배치가 안 됩니다.

---

## 출처

- [Kuzu — Create table (DDL)](https://docs.kuzudb.com/cypher/data-definition/create-table/)
- [Kuzu 저장소](https://github.com/kuzudb/kuzu) · [Kuzu 0.11.0 릴리스 노트](https://github.com/kuzudb/kuzu/releases/tag/v0.11.0)
- [KÙZU Graph Database Management System (CIDR 2023)](https://www.cidrdb.org/cidr2023/papers/p48-jin.pdf) — 컬럼 저장, CSR, 벡터화 실행과 morsel 기반 병렬성
- [Neo4j — Defining a schema (schema-optional)](https://neo4j.com/docs/getting-started/cypher/schema/)
- [Neo4j Cypher Manual — Constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/) · [Create constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/)
- [Neo4j — List of notification codes](https://neo4j.com/docs/status-codes/current/notifications/all-notifications/) — `UnknownLabelWarning`
- [ISO/IEC 39075:2024 — Database languages GQL](https://www.iso.org/standard/76120.html) · [JTC1 해설: What is the database language GQL?](https://jtc1info.org/wp-content/uploads/2024/04/2024-Article-39075-Database-Language-GQL.docx.pdf) — open/closed graph type
- 5장 예제: `content/ch05/code/ex3_cypher_vs_sparql.py` (Kuzu 0.11.3, rdflib 7.5.0 기준, 확인 시점 2026년 8월)

> 오류 메시지 문구와 Enterprise 전용 여부는 버전에 따라 달라질 수 있으니, 실제 동작은 쓰는 버전에서 한 번 확인하시길 권합니다.
